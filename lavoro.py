# -*- coding: utf-8 -*-
"""LAVORO — una sezione nuova, fuori da Casa, con il suo bottone fra quelli delle pagine.

Dentro, per ora:
  💶 Buste paga   carichi la busta (PDF, foto o scansione: i modi sono gli stessi di Casa), l'app legge mese, lordo, netto e trattenute e te li propone: controlli e confermi.
                  Si possono anche inserire a mano (anche solo una voce). Per anno, mese per mese in ordine cronologico. Ogni busta si apre, si scarica, si corregge, si invia.
  📊 Anno per anno   grafici e tabelle: per ogni anno il netto ricevuto, il lordo, le trattenute totali (con 13ª, 14ª e voci a mano), confrontati con gli anni prima.
  Tutto si esporta (HTML e PDF) e si invia come il resto dell'app.
I dati restano dov'erano (documenti di tipo «Busta paga»): le buste già inserite si vedono qui. Le prossime voci del Lavoro si aggiungono in seguito.
Caricato da app_dispensa.py dopo casa.py, salute_plus.py e pagine_nav.py."""
import html as _h
from datetime import date

import streamlit as st

_LV_MESI = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
_LV_CSS = """<style>
.lv-hero{display:flex;align-items:center;gap:16px;background:linear-gradient(135deg,#78909c 0%,#455a64 55%,#263238 100%);color:#fff;padding:18px 22px;border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.18)}
.lv-hero .ico{font-size:3rem;line-height:1}
.lv-hero h1{margin:0;font-size:1.7rem;color:#fff}.lv-hero p{margin:2px 0 0;font-size:.95rem;opacity:.95}
.lv-card{background:rgba(255,255,255,.88);border-radius:16px;padding:10px 14px;margin:8px 0;color:#1b2b2b}
</style>"""

# ---------------------------------------------------------------------------------------------------------------------
# registrazione della sezione: bottoni, permessi, ordine
# ---------------------------------------------------------------------------------------------------------------------
try:
    if "SEZIONI_NAV" in globals() and "lavoro" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(SEZIONI_NAV.index("casa") + 1 if "casa" in SEZIONI_NAV else len(SEZIONI_NAV), "lavoro")
    if "NOMI_NAV" in globals():
        NOMI_NAV["lavoro"] = "Lavoro"
    if "SV_SEZIONI" in globals():
        SV_SEZIONI["lavoro"] = "💼 Lavoro"
    if "_SV_DA_SEZIONE_HOME" in globals():
        _SV_DA_SEZIONE_HOME["lavoro"] = "lavoro"
except Exception:
    pass


# ---------------------------------------------------------------------------------------------------------------------
# i dati: le buste paga, anno per anno
# ---------------------------------------------------------------------------------------------------------------------
def _lv_num(v):
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def lv_serie(docs):
    """[{id, anno, mese, mensilita, netto, lordo, trattenute, extra, stimato}] per ogni busta paga con il mese, dal più vecchio. Il terzo valore si ricava dagli altri due se manca."""
    out = []
    for d in docs:
        comp = str(d.get("competenza") or "")
        if d.get("tipo") != "Busta paga" or not (len(comp) == 7 and comp[4] == "-" and comp[:4].isdigit() and comp[5:].isdigit() and 1 <= int(comp[5:]) <= 12):
            continue
        n, l, t = _lv_num(d.get("netto")), _lv_num(d.get("lordo")), _lv_num(d.get("trattenute"))
        stimato = False
        if l is None and n is not None and t is not None:
            l, stimato = n + t, True
        elif t is None and l is not None and n is not None and n <= l:
            t, stimato = l - n, True
        elif n is None and l is not None and t is not None and t <= l:
            n, stimato = l - t, True
        extra = 0.0
        for v in (d.get("voci") or []):
            try:
                extra += float((v or {}).get("importo") or 0)
            except (ValueError, TypeError, AttributeError):
                pass
        if n is None and l is None and not extra:
            continue
        out.append({"id": d.get("id"), "anno": int(comp[:4]), "mese": int(comp[5:]), "mensilita": d.get("mensilita") or "Mensile", "netto": n or 0.0, "lordo": l, "trattenute": t,
                    "extra": round(extra, 2), "stimato": stimato})
    return sorted(out, key=lambda x: (x["anno"], x["mese"], x["mensilita"]))


def lv_riepilogo_anni(punti):
    """Per ogni anno: netto ricevuto (con 13ª, 14ª e voci a mano), lordo, trattenute, quanto pesano le trattenute sul lordo, e le differenze con l'anno prima (anche «a parità di mesi»)."""
    anni = sorted({p["anno"] for p in punti})
    out = []
    for a in anni:
        pa = [p for p in punti if p["anno"] == a]
        mens = [p for p in pa if p["mensilita"] in ("Mensile", "Altra")]
        mesi = sorted({p["mese"] for p in mens})
        netto = round(sum(p["netto"] + p["extra"] for p in pa), 2)
        lordo = round(sum(p["lordo"] for p in pa if p["lordo"] is not None), 2)
        tratt = round(sum(p["trattenute"] for p in pa if p["trattenute"] is not None), 2)
        r = {"anno": a, "n": len(pa), "mesi": mesi, "netto": netto, "lordo": lordo, "trattenute": tratt,
             "t13": round(sum(p["netto"] for p in pa if p["mensilita"] == "13ª mensilità"), 2), "t14": round(sum(p["netto"] for p in pa if p["mensilita"] == "14ª mensilità"), 2),
             "extra": round(sum(p["extra"] for p in pa), 2), "perc_tratt": round(tratt / lordo * 100, 1) if lordo else None,
             "media": round(sum(p["netto"] for p in mens) / len(mesi), 2) if mesi else None, "var": {}, "pari": {}}
        prec = out[-1] if out and out[-1]["anno"] == a - 1 else None
        if prec:
            for k in ("netto", "lordo", "trattenute"):
                if prec[k]:
                    r["var"][k] = (round(r[k] - prec[k], 2), round((r[k] - prec[k]) / prec[k] * 100, 1))
            if prec["media"] and r["media"]:
                r["var"]["media"] = (round(r["media"] - prec["media"], 2), round((r["media"] - prec["media"]) / prec["media"] * 100, 1))
            if mesi and len(mesi) < 12:                                          # anno non finito: si confronta con gli STESSI mesi dell'anno prima
                for k in ("netto", "lordo", "trattenute"):
                    ora = sum((p[k] or 0) for p in mens if p["mese"] in mesi)
                    pr = sum((p[k] or 0) for p in punti if p["anno"] == a - 1 and p["mensilita"] in ("Mensile", "Altra") and p["mese"] in mesi)
                    if pr:
                        r["pari"][k] = (round(ora - pr, 2), round((ora - pr) / pr * 100, 1))
        out.append(r)
    return out


def _lv_eur(v):
    return ("€ " + ca_importo_fmt(round(v, 2))) if v is not None else "—"


def lv_html_riepilogo(docs, titolo="Buste paga"):
    """Il riepilogo anno per anno e mese per mese, in HTML (da stampare, salvare come PDF o inviare)."""
    e = _h.escape
    punti = lv_serie(docs)
    anni = lv_riepilogo_anni(punti)
    righe_anni = "".join(
        f"<tr><td><b>{r['anno']}</b></td><td>{_lv_eur(r['netto'])}</td><td>{_lv_eur(r['lordo']) if r['lordo'] else '—'}</td><td>{_lv_eur(r['trattenute']) if r['trattenute'] else '—'}</td>"
        f"<td>{(str(r['perc_tratt']).replace('.', ',') + '%') if r['perc_tratt'] is not None else '—'}</td><td>{r['n']}</td></tr>" for r in reversed(anni))
    var_txt = ""
    for r in reversed(anni):
        if r["var"] or r["pari"]:
            parti = []
            for k, nome in (("netto", "netto"), ("lordo", "lordo"), ("trattenute", "trattenute")):
                x = (r["pari"] or r["var"]).get(k)
                if x:
                    parti.append(f"{nome} {_ca_fmt_var(x[0], x[1])}")
            var_txt += f"<p><b>{r['anno']}</b> rispetto al {r['anno'] - 1}" + (" (a parità di mesi)" if r["pari"] else "") + ": " + e("; ".join(parti)) + "</p>"
    mesi_righe = ""
    for p in punti:
        mesi_righe += (f"<tr><td>{_LV_MESI[p['mese'] - 1]} {p['anno']}</td><td>{e(p['mensilita'])}</td><td>{_lv_eur(p['lordo']) if p['lordo'] is not None else '—'}</td>"
                       f"<td>{_lv_eur(p['trattenute']) if p['trattenute'] is not None else '—'}</td><td>{_lv_eur(p['netto'])}</td><td>{_lv_eur(p['extra']) if p['extra'] else ''}</td></tr>")
    stile = ("body{font-family:Arial,sans-serif;font-size:10.5pt;color:#111}h1{font-size:16pt}h2{font-size:12pt;border-bottom:1px solid #888;margin-top:14pt}"
             "table{border-collapse:collapse;width:100%}td,th{border:1px solid #999;padding:3px 5px;text-align:right}td:first-child,th:first-child{text-align:left}.nota{font-size:8.5pt;color:#444;margin-top:12pt}")
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><title>{e(titolo)}</title><style>{stile}</style></head><body>"
            f"<h1>{e(titolo)}</h1><h2>Anno per anno</h2><table><tr><th>Anno</th><th>Netto ricevuto</th><th>Lordo</th><th>Trattenute</th><th>Trattenute/lordo</th><th>Buste</th></tr>{righe_anni}</table>{var_txt}"
            f"<h2>Mese per mese</h2><table><tr><th>Mese</th><th>Tipo</th><th>Lordo</th><th>Trattenute</th><th>Netto</th><th>Voci a mano</th></tr>{mesi_righe}</table>"
            "<p class='nota'>Creato dall'app «La nostra dispensa» con i dati inseriti o letti dalle buste paga: controllali sugli originali. Il netto dell'anno comprende 13ª, 14ª e voci aggiunte a mano.</p></body></html>")


def _lv_pdf(html_str):
    return sp_pdf_da_html(html_str) if "sp_pdf_da_html" in globals() else None


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def lv_esporta(docs, etichetta, chiave):
    """I tasti per scaricare (HTML e PDF) e inviare il riepilogo."""
    punti = lv_serie(docs)
    if not punti:
        return
    html_str = lv_html_riepilogo(docs)
    nome_file = f"buste_paga_{date.today().isoformat()}"
    st.download_button("📄 Scarica il riepilogo (da stampare o salvare come PDF)", html_str.encode("utf-8"), file_name=nome_file + ".html", mime="text/html", width="stretch", key=f"lv_dl_html_{chiave}")
    pdf = _lv_pdf(html_str)
    if pdf:
        st.download_button("📕 Scarica il PDF", pdf, file_name=nome_file + ".pdf", mime="application/pdf", width="stretch", key=f"lv_dl_pdf_{chiave}")
    if "inv_voce" in globals():
        anni = lv_riepilogo_anni(punti)
        testo = "Buste paga – riepilogo\n" + "\n".join(f"• {r['anno']}: netto {_lv_eur(r['netto'])}" + (f", lordo {_lv_eur(r['lordo'])}" if r["lordo"] else "") + (f", trattenute {_lv_eur(r['trattenute'])}" if r["trattenute"] else "") for r in reversed(anni))
        inv_voce(f"lv_invia_{chiave}", etichetta, "Buste paga: riepilogo", testo, lambda: ([(nome_file + ".pdf", "application/pdf", pdf)] if pdf else [(nome_file + ".html", "text/html", html_str.encode("utf-8"))]))


def lv_archivio_buste(c):
    docs = [d for d in c.get("documenti", []) if d.get("tipo") == "Busta paga"]
    st.markdown(f"#### 📚 Le tue buste paga ({len(docs)})")
    if not docs:
        st.info("Ancora nessuna busta paga. Caricane una qui sopra, oppure inseriscila a mano.")
        return
    def chiave(d):
        return (str(d.get("competenza") or d.get("data_doc") or "")[:7], {"Mensile": 0, "Altra": 1, "13ª mensilità": 2, "14ª mensilità": 3}.get(d.get("mensilita"), 0))
    per_anno = {}
    for d in docs:
        per_anno.setdefault(chiave(d)[0][:4] or "senza data", []).append(d)
    for anno in sorted(per_anno, reverse=True):
        lista = sorted(per_anno[anno], key=chiave)
        tot = sum(float(x.get("netto") or 0) + sum(float((v or {}).get("importo") or 0) for v in (x.get("voci") or [])) for x in lista)
        with st.expander(f"📅 {anno} · {len(lista)} buste" + (f" · netto ricevuto {_lv_eur(tot)}" if tot else ""), expanded=(anno == max(per_anno))):
            for d in lista:
                _ca_riga_documento(d, {}, "lv", docs)
    lv_esporta(docs, "📤 Invia il riepilogo delle buste paga", "archivio")


def lv_tab_buste(c):
    n = st.session_state.get("ca_giro", 0)
    st.markdown("#### ➕ Carica una busta paga")
    st.caption("Carica il **PDF**, una **foto** o una **scansione** della busta paga: leggo mese, **lordo**, **netto** e **trattenute** e te li propongo. **Controlli, correggi e confermi tu.** Il file resta com'è.")
    up = _ca_pannello_caricamento(n)
    _ca_flusso_documento(c, [], n, up, None, None, lavoro=True)
    if "_ca_busta_a_mano" in globals():
        _ca_busta_a_mano()
    _ca_correzione(c, [])
    lv_archivio_buste(c)


def _lv_grafici_dati(punti):
    try:
        import pandas as pd
    except Exception:
        return None
    return pd


def lv_tab_grafici(c):
    punti = lv_serie([d for d in c.get("documenti", []) if d.get("tipo") == "Busta paga"])
    if len(punti) < 2:
        st.info("Per i grafici servono almeno due buste paga con il mese. Caricane altre (o inseriscile a mano) e compaiono qui.")
        return
    pd = _lv_grafici_dati(punti)
    if pd is None:
        st.warning("I grafici non sono disponibili su questo dispositivo.")
        return
    anni = lv_riepilogo_anni(punti)
    st.markdown("**💶 Anno per anno: netto ricevuto, lordo e trattenute**")
    df = pd.DataFrame({"Netto ricevuto": [r["netto"] for r in anni], "Lordo": [r["lordo"] or 0 for r in anni], "Trattenute": [r["trattenute"] or 0 for r in anni]}, index=[str(r["anno"]) for r in anni])
    st.bar_chart(df, stack=False, height=280)
    st.caption("Il **netto** comprende 13ª, 14ª e le voci aggiunte a mano. Per le buste in cui manca un valore lo ricavo dagli altri due (lordo − trattenute = netto).")
    perc = [(str(r["anno"]), r["perc_tratt"]) for r in anni if r["perc_tratt"] is not None]
    if len(perc) >= 2:
        st.markdown("**📉 Quanto pesano le trattenute sul lordo (%)**")
        st.line_chart(pd.DataFrame({"Trattenute sul lordo (%)": [v for _, v in perc]}, index=[a for a, _ in perc]), height=200)
    st.markdown("**📅 Il netto mese per mese, un colore per anno**")
    mesi_df = pd.DataFrame({str(a): [round(sum(p["netto"] + p["extra"] for p in punti if p["anno"] == a and p["mese"] == m), 2) for m in range(1, 13)] for a in sorted({p["anno"] for p in punti})}, index=_LV_MESI)
    st.bar_chart(mesi_df, stack=False, height=260)
    with st.expander("🔍 Il confronto con gli anni prima", expanded=True):
        for r in reversed(anni):
            parziale = 0 < len(r["mesi"]) < 12
            st.markdown(f"**{r['anno']}** · netto ricevuto **{_lv_eur(r['netto'])}**" + (f" · lordo {_lv_eur(r['lordo'])}" if r["lordo"] else "") + (f" · trattenute {_lv_eur(r['trattenute'])}" if r["trattenute"] else "")
                        + (f" · pesano il {str(r['perc_tratt']).replace('.', ',')}% del lordo" if r["perc_tratt"] is not None else "")
                        + (f" (mesi: {', '.join(_LV_MESI[m - 1] for m in r['mesi'])})" if parziale else ""))
            st.caption(f"{r['n']} buste" + (f" · media mensile del netto {_lv_eur(r['media'])}" if r["media"] else "") + (f" · 13ª {_lv_eur(r['t13'])}" if r["t13"] else "") + (f" · 14ª {_lv_eur(r['t14'])}" if r["t14"] else "")
                       + (f" · voci a mano {_lv_eur(r['extra'])}" if r["extra"] else ""))
            conf = r["pari"] if r["pari"] else r["var"]
            if conf:
                st.markdown(f"&nbsp;&nbsp;↳ rispetto al {r['anno'] - 1}" + (" **a parità di mesi**" if r["pari"] else "") + ": " + " · ".join(f"{nome} {_ca_fmt_var(conf[k][0], conf[k][1])}" for k, nome in (("netto", "netto"), ("lordo", "lordo"), ("trattenute", "trattenute")) if k in conf))
                if r["pari"]:
                    st.caption(f"Il {r['anno']} non è ancora finito: il confronto giusto è con gli stessi mesi del {r['anno'] - 1}.")
                if "media" in r["var"]:
                    st.markdown(f"&nbsp;&nbsp;↳ **media mensile** del netto: {_ca_fmt_var(r['var']['media'][0], r['var']['media'][1])}")
    lv_esporta([d for d in c.get("documenti", []) if d.get("tipo") == "Busta paga"], "📤 Invia il riepilogo anno per anno", "grafici")


def schermata_lavoro():
    """La pagina «Lavoro»."""
    if "nav_barra" in globals():
        nav_barra("lavoro")
    if "_CA_CSS" in globals():
        st.markdown(_CA_CSS, unsafe_allow_html=True)
    st.markdown(_LV_CSS, unsafe_allow_html=True)
    st.markdown("<div class='lv-hero'><div class='ico'>💼</div><div><h1>Lavoro</h1><p>Le buste paga, anno per anno: netto, lordo e trattenute a confronto</p></div></div>", unsafe_allow_html=True)
    if st.session_state.get("messaggio"):
        st.success(st.session_state.pop("messaggio"))
    if "pulsante_info" in globals():
        try:
            pulsante_info("lavoro")
        except Exception:
            pass
    try:
        c = _ca_dati()
    except Exception as ex:
        st.error(f"Non riesco a leggere i dati ({type(ex).__name__}). Riprova fra poco.")
        return
    t1, t2 = st.tabs(["💶 Buste paga", "📊 Anno per anno"])
    with t1:
        lv_tab_buste(c)
    with t2:
        lv_tab_grafici(c)


# ---- lo smistamento: «lavoro» va alla sua pagina (con il controllo dei permessi di «Sezioni visibili»), il resto come prima
if "schermata_farmacia" in globals() and "_lv_schermata_prima" not in globals():
    _lv_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "lavoro":
            if "sv_nascoste" in globals() and "lavoro" in sv_nascoste():
                return sv_blocca("lavoro")
            return schermata_lavoro()
        return _lv_schermata_prima()


# ---- la guida «Informazioni» della sezione
if "_NOMI_SEZIONI" in globals():
    _NOMI_SEZIONI.setdefault("lavoro", "💼 Lavoro")
    _GUIDE.setdefault("lavoro", [
        ("💼 Cos'è la sezione Lavoro",
         """Qui sta tutto ciò che riguarda il tuo lavoro. Per ora: le **buste paga**.
Ha due schede: **💶 Buste paga** (carichi, leggi, correggi, invii) e **📊 Anno per anno** (grafici e confronti).
Si apre dal bottone **💼 Lavoro** in alto, accanto agli altri.""", "lavoro buste paga stipendio netto lordo trattenute"),
        ("💶 Caricare una busta paga",
         """1. Apri **💼 Lavoro** e resta sulla scheda **💶 Buste paga**.
2. Tocca **📎 Scegli il PDF o il file** (oppure **📷 Scatta foto** o **🖼️ Dalla galleria**). Puoi anche scegliere **più buste insieme**.
3. L'app legge il **mese**, il **lordo**, il **netto** e le **trattenute** e te li propone: **controlla e correggi** quello che serve, poi tocca **✅ Conferma e archivia**.
4. Se non riesce a leggere un valore, lo scrivi tu. Puoi aggiungere anche **voci a mano** (premio, straordinari, arretrati): contano nei totali.
Se la stessa busta (stesso mese) sembra già archiviata, ti avviso prima.
Per inserirla **a mano**, senza file, apri **✍️ Inserisci a mano una busta paga o una voce**.""", "carica busta paga pdf foto leggi netto lordo trattenute voci 13esima 14esima"),
        ("📊 Anno per anno: grafici e confronto",
         """Apri la scheda **📊 Anno per anno**. Vedi, per ogni anno, il **netto ricevuto** (con 13ª, 14ª e voci a mano), il **lordo** e le **trattenute totali**, e quanto pesano le trattenute sul lordo.
Sotto, **il confronto con gli anni prima**, in euro e in percentuale. Per l'anno non ancora finito il confronto è **«a parità di mesi»**, con gli stessi mesi dell'anno prima.
Puoi **scaricare** il riepilogo (HTML o PDF) e **inviarlo** per email, WhatsApp o Telegram.""", "grafico anno confronto netto lordo trattenute percentuale riepilogo esporta"),
    ])
    _ID_GUIDA.setdefault("lavoro", ["l_cosa", "l_carica", "l_anni"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("lavoro", "l_cosa")
