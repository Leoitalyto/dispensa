# -*- coding: utf-8 -*-
"""ARCHIVIO di bugiardini, foto e documenti (nuova sezione, dopo «I miei documenti»).
Raccoglie in un unico elenco ordinato TUTTI i file che sono stati caricati in Salute:
  • bugiardini (fogli illustrativi) dei medicinali      • foto delle confezioni (anche quelle dell'archivio foto)
  • foto e PDF dei documenti personali                  • foto e PDF delle prescrizioni (ricette)
  • referti e documenti delle visite                    • pagine del documento vaccinale
Ogni file è classificato per categoria e tipologia (immagine o PDF), collegato alla persona e alla voce a cui appartiene
(per esempio «Medicinale: Tachipirina»), e si può cercare per nome, filtrare per persona, categoria, tipologia e data,
riaprire senza ricaricarlo, scaricare, inviare e salvare tutto in una copia di sicurezza (ZIP).
I file restano salvati in modo permanente nell'archivio privato dell'app (con la cronologia di GitHub).
Caricato da app_dispensa.py dopo navigazione.py."""
import base64
import csv
import html
import io
import re
import zipfile
from datetime import date

import streamlit as st

AR_CATEGORIE = ["Bugiardino", "Foto confezione", "Documento personale", "Prescrizione", "Visita ed esami", "Vaccinazioni"]
AR_ICONE = {"Bugiardino": "📖", "Foto confezione": "📷", "Documento personale": "🪪", "Prescrizione": "📝", "Visita ed esami": "🩺", "Vaccinazioni": "💉"}
_AR_PASSO = 10


def _ar_mime(rif):
    mime = rif.get("mime") or ""
    if mime:
        return mime
    return "application/pdf" if str(rif.get("nome", "")).lower().endswith(".pdf") else "image/webp"


def ar_voci(f, nomi_profili):
    """Tutti i file di Salute come elenco di dizionari: id, nome, mime, categoria, collegato, pid, persona, data (ISO o vuota)."""
    voci, visti = [], set()

    def aggiungi(rif, categoria, collegato, pid, data=None):
        if not rif or not rif.get("id") or rif["id"] in visti:
            return
        visti.add(rif["id"])
        voci.append({"id": rif["id"], "nome": rif.get("nome") or "file", "mime": _ar_mime(rif), "categoria": categoria, "collegato": collegato,
                     "pid": pid, "persona": nomi_profili.get(pid, ""), "data": data or ""})
    for m in f.get("medicinali", []):
        pid, nome = m.get("profilo", "p0"), m.get("nome", "")
        aggiungi(m.get("foto_grande"), "Foto confezione", f"Medicinale: {nome}", pid, m.get("acquisto"))
        for a in m.get("foglio", []):
            aggiungi(a, "Bugiardino", f"Medicinale: {nome}", pid, m.get("acquisto"))
    for x in f.get("documenti", []):
        for a in x.get("allegati", []):
            aggiungi(a, "Documento personale", f"Documento: {x.get('tipo', '')}", x.get("profilo", "p0"), x.get("rilascio"))
    for x in f.get("prescrizioni", []):
        for a in x.get("allegati", []):
            aggiungi(a, "Prescrizione", f"Prescrizione: {x.get('tipo', '')}" + (f" ({x['prescritto'][:30]})" if x.get("prescritto") else ""),
                     x.get("profilo", "p0"), x.get("data"))
    for x in f.get("visite", []):
        for a in x.get("allegati", []):
            aggiungi(a, "Visita ed esami", f"Visita: {x.get('categoria', '')}", x.get("profilo", "p0"), x.get("data"))
    for pid, pagine in (f.get("vaccini_doc") or {}).items():
        for a in pagine:
            aggiungi(a, "Vaccinazioni", "Documento vaccinale", pid)
    for e in f.get("archivio_foto", []):                     # le foto già usate (quelle ancora collegate a un medicinale sono già nell'elenco)
        aggiungi(e.get("grande"), "Foto confezione", f"Foto: {e.get('nome', '')}", "", e.get("data"))
    return voci


def _ar_data_it(iso):
    return "/".join(reversed(iso.split("-"))) if iso else "senza data"


def ar_filtra(voci, testo="", persona="", categoria="", tipologia="", dal=None, al=None, ordine="Più recenti"):
    """Cerca per nome (anche nel collegamento e nella persona) e filtra per persona, categoria, tipologia e data."""
    parole = [p for p in re.split(r"\s+", (testo or "").lower().strip()) if p]
    risultato = []
    for v in voci:
        pagliaio = f"{v['nome']} {v['collegato']} {v['persona']} {v['categoria']}".lower()
        if any(p not in pagliaio for p in parole):
            continue
        if persona and v["pid"] != persona:
            continue
        if categoria and v["categoria"] != categoria:
            continue
        pdf = v["mime"] == "application/pdf"
        if tipologia == "Immagini" and pdf:
            continue
        if tipologia == "PDF" and not pdf:
            continue
        if (dal or al) and not v["data"]:
            continue
        if dal and v["data"] < dal.isoformat():
            continue
        if al and v["data"] > al.isoformat():
            continue
        risultato.append(v)
    if ordine == "Per nome":
        risultato.sort(key=lambda v: v["nome"].lower())
    elif ordine == "Per categoria":
        risultato.sort(key=lambda v: (AR_CATEGORIE.index(v["categoria"]), v["nome"].lower()))
    else:
        risultato.sort(key=lambda v: v["data"] or "0000-00-00", reverse=True)
    return risultato


def _ar_carica(v):
    """Il contenuto di un file (byte), oppure None se non si trova."""
    try:
        d = carica_dati(crea_archivio(), _fa_percorso_doc(v["id"]))
        return base64.b64decode(d["b64"]) if d.get("b64") else None
    except Exception:
        return None


def ar_zip(voci, progresso=None):
    """Una copia di sicurezza: tutti i file in un ZIP, in cartelle per categoria e persona, con un indice (CSV). Ritorna (byte dello ZIP, file non trovati)."""
    buf, mancanti = io.BytesIO(), []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        indice = io.StringIO()
        w = csv.writer(indice, delimiter=";")
        w.writerow(["File", "Categoria", "Persona", "Collegato a", "Data", "Tipo"])
        usati = set()
        for n, v in enumerate(voci):
            dati = _ar_carica(v)
            if dati is None:
                mancanti.append(v["nome"])
            else:
                cartella = f"{v['categoria']}/{(v['persona'] or 'senza persona').replace('/', '-')}"
                nome = re.sub(r'[\\/:*?"<>|]+', "_", v["nome"])
                percorso, k = f"{cartella}/{nome}", 2
                while percorso in usati:
                    base, _, est = nome.rpartition(".")
                    percorso = f"{cartella}/{(base or nome)}_{k}{('.' + est) if base else ''}"
                    k += 1
                usati.add(percorso)
                z.writestr(percorso, dati)
                w.writerow([percorso, v["categoria"], v["persona"], v["collegato"], _ar_data_it(v["data"]), v["mime"]])
            if progresso:
                progresso((n + 1) / max(1, len(voci)))
        z.writestr("indice.csv", ("\ufeff" + indice.getvalue()).encode("utf-8"))
    return buf.getvalue(), mancanti


def _ar_alterna(chiave):
    st.session_state[chiave] = not st.session_state.get(chiave, False)


def archivio_pulsante(dove):
    """Il pulsante che porta all'Archivio (si mette in Salute e in I miei documenti)."""
    st.button("🗂️ Archivio: bugiardini, foto e documenti", key=f"ar_apri_{dove}", width="stretch", on_click=nav_vai, args=("archivio",))


def _ar_scheda(v):
    e = html.escape
    pdf = v["mime"] == "application/pdf"
    righe = [f"{AR_ICONE.get(v['categoria'], '📎')} <b>{e(v['nome'])}</b>",
             f"🏷️ {e(v['categoria'])} · {'📄 PDF' if pdf else '🖼️ immagine'}",
             f"🔗 {e(v['collegato'])}" + (f" · 👤 {e(v['persona'])}" if v["persona"] else ""),
             f"📅 {_ar_data_it(v['data'])}"]
    return "<div style='line-height:1.5;font-size:.92rem'>" + "<br>".join(righe) + "</div>"


def schermata_archivio():
    nav_barra("archivio")
    st.markdown("<div style='background:linear-gradient(135deg,#4527a0 0%,#7e57c2 55%,#b39ddb 100%);color:#fff;padding:20px 24px;border-radius:24px;"
                "margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.15)'><h1 style='margin:0;font-size:1.8rem;color:#fff;padding:0'>🗂️ Archivio</h1>"
                "<p style='margin:4px 0 0;opacity:.92'>Bugiardini, foto e documenti: tutto in un posto, sempre a portata di mano</p></div>", unsafe_allow_html=True)
    f = _fa_dati()
    profili = _fa_profili(f)
    nomi = {p["id"]: p["nome"] for p in profili}
    voci = ar_voci(f, nomi)
    if not voci:
        st.info("Qui compariranno i file che carichi in Salute: i fogli illustrativi dei medicinali, le foto delle confezioni, i documenti, "
                "le ricette, i referti e le pagine del libretto vaccinale. Per ora non ce n'è nessuno.")
        return
    n_pdf = sum(1 for v in voci if v["mime"] == "application/pdf")
    st.markdown(f"**{len(voci)} file** · 🖼️ {len(voci) - n_pdf} immagini · 📄 {n_pdf} PDF")

    cerca = st.text_input("Cerca", placeholder="nome del file, del medicinale, della persona…", label_visibility="collapsed", key="ar_cerca")
    c1, c2 = st.columns(2, gap="small")
    persona = c1.selectbox("Persona", [""] + list(nomi), format_func=lambda p: "👤 Tutte le persone" if not p else f"👤 {nomi[p]}", key="ar_persona")
    conteggi = {c: sum(1 for v in voci if v["categoria"] == c) for c in AR_CATEGORIE}
    categoria = c2.selectbox("Categoria", [""] + AR_CATEGORIE, key="ar_categoria",
                             format_func=lambda c: "🏷️ Tutte le categorie" if not c else f"{AR_ICONE[c]} {c} ({conteggi[c]})")
    c3, c4 = st.columns(2, gap="small")
    tipologia = c3.selectbox("Tipologia", ["", "Immagini", "PDF"], format_func=lambda t: "📎 Tutte le tipologie" if not t else t, key="ar_tipologia")
    ordine = c4.selectbox("Ordina", ["Più recenti", "Per nome", "Per categoria"], key="ar_ordine")
    with st.expander("📅 Filtra per data"):
        d1, d2 = st.columns(2, gap="small")
        dal = d1.date_input("Dal", value=None, format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31), key="ar_dal")
        al = d2.date_input("Al", value=None, format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31), key="ar_al")
        st.caption("Vale per i file con una data (documento, ricetta, visita, acquisto). Gli altri non compaiono se scegli un periodo.")

    trovati = ar_filtra(voci, cerca, persona, categoria, tipologia, dal, al, ordine)
    firma = (cerca, persona, categoria, tipologia, str(dal), str(al), ordine)
    if st.session_state.get("ar_firma") != firma:                     # se cambiano i filtri si riparte dall'inizio
        st.session_state["ar_firma"], st.session_state["ar_mostrati"] = firma, _AR_PASSO
    mostrati = st.session_state.get("ar_mostrati", _AR_PASSO)
    if not trovati:
        st.warning("Nessun file corrisponde: prova a togliere un filtro.")
    else:
        st.caption(f"{len(trovati)} file trovati")
    for v in trovati[:mostrati]:
        with st.container(border=True, key=f"ar_box_{v['id']}"):
            st.markdown(_ar_scheda(v), unsafe_allow_html=True)
            k_ap = f"ar_ap_{v['id']}"
            aperto = st.session_state.get(k_ap, False)
            st.button("🙈 Chiudi" if aperto else "👁️ Apri", key=f"ar_btn_{v['id']}", width="stretch", on_click=_ar_alterna, args=(k_ap,))
            if aperto:
                dati = _ar_carica(v)
                if dati is None:
                    st.error("Non trovo questo file nell'archivio: potrebbe essere stato eliminato da un'altra scheda.")
                else:
                    if v["mime"].startswith("image/"):
                        st.image(dati)
                    else:
                        st.caption("PDF: scaricalo e aprilo con il visualizzatore del telefono.")
                    st.download_button("⬇ Scarica", dati, file_name=v["nome"], mime=v["mime"], key=f"ar_dl_{v['id']}", width="stretch")
            if "inv_voce" in globals():
                inv_voce(f"ar_{v['id']}", "📤 Invia", f"{AR_ICONE.get(v['categoria'], '')} {v['nome']}",
                         f"{v['categoria']} · {v['collegato']}" + (f" · {v['persona']}" if v["persona"] else ""),
                         lambda v=v: [(v["nome"], v["mime"], d)] if (d := _ar_carica(v)) is not None else [])
    if len(trovati) > mostrati:
        if st.button(f"Mostra altri {min(_AR_PASSO, len(trovati) - mostrati)} (ne mancano {len(trovati) - mostrati})", key="ar_altri", width="stretch"):
            st.session_state["ar_mostrati"] = mostrati + _AR_PASSO
            st.rerun()

    st.subheader("🛡️ Copia di sicurezza")
    st.caption("I file sono già salvati in modo permanente e con la cronologia delle versioni. Qui puoi anche scaricarne una copia: un unico file ZIP con tutti i file "
               "in cartelle per categoria e per persona, più un indice. Se hai applicato dei filtri, la copia comprende solo i file trovati.")
    if st.button(f"📦 Prepara la copia di sicurezza ({len(trovati)} file)", key="ar_prepara", width="stretch", disabled=not trovati):
        barra = st.progress(0.0, text="Preparo la copia…")
        dati_zip, mancanti = ar_zip(trovati, lambda x: barra.progress(x, text="Preparo la copia…"))
        barra.empty()
        st.session_state["ar_zip"] = (dati_zip, mancanti, len(trovati))
    pronto = st.session_state.get("ar_zip")
    if pronto:
        dati_zip, mancanti, n = pronto
        st.success(f"✅ Copia pronta: {n - len(mancanti)} file ({len(dati_zip) // 1024} KB).")
        if mancanti:
            st.warning("Non ho trovato: " + ", ".join(mancanti[:8]) + (" …" if len(mancanti) > 8 else ""))
        st.download_button("⬇ Scarica la copia (ZIP)", dati_zip, file_name=f"archivio_salute_{date.today().isoformat()}.zip", mime="application/zip",
                           key="ar_dl_zip", width="stretch")
