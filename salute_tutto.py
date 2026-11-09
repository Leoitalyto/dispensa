# -*- coding: utf-8 -*-
"""SALUTE · «📋 Tutti i dati e documenti» di una persona.

PROBLEMA (segnalato da Leonardo, 9 novembre, profilo di sua madre): «Esporta i dati di questo profilo» portava fuori solo i dati vecchi (medicinali, terapie, prescrizioni,
visite, vaccinazioni, documenti) e NON i documenti sanitari già classificati, i parametri, i controlli, le esenzioni, i medici, i dati per l'emergenza. In un'urgenza serve poter
VEDERE tutto quello che c'è (almeno i titoli di referti ed esami) e poi, secondo quello che chiede il medico, scaricare, stampare o inviare solo quello che serve.

COSA FA (per ogni profilo, di chiunque):
• l'ELENCO COMPLETO di tutto ciò che l'app sa di quella persona, per gruppi: documenti sanitari (per tipo e data), prescrizioni, visite, vaccinazioni, terapie, medicinali, documenti
  personali, invalidità ed esenzioni, fascicolo e tessera, parametri, controlli, medici, dati per l'emergenza; ogni voce con titolo, data, dettagli e 📎 se ha file;
• ricerca per parola, scelta dei gruppi, «solo con file», «Seleziona tutto» e «Deseleziona tutto»;
• 📄 l'ELENCO da stampare o mostrare (PDF e pagina web), con tutte le voci che vedi;
• ⬇ lo ZIP con i FILE delle voci scelte (cartella per gruppo, nomi con la data) e l'indice dentro;
• 📤 INVIA le voci scelte con i modi già previsti (email, WhatsApp, Telegram…, tramite il modulo dell'invio: se un canale non può mandare il file, lo dice e propone il download).
Si apre dal pulsante «📋 Tutti i dati e documenti» sotto il profilo e da «📦 Esporta i dati di questo profilo». Anche l'esportazione tecnica (JSON) ora comprende tutto.
Non legge né modifica nulla: raccoglie e basta."""
import hashlib
import html as _stt_html
import io
import json as _stt_json
import re
import zipfile
from datetime import datetime

import streamlit as st

_STT_GRUPPI = [("docsan", "🗂️", "Documenti sanitari (referti, esami, ricette…)"), ("prescrizioni", "📝", "Prescrizioni"), ("visite", "🩺", "Visite"), ("vaccinazioni", "💉", "Vaccinazioni"),
               ("esenzioni", "🪪", "Invalidità ed esenzioni"), ("fascicolo", "📎", "Fascicolo sanitario e tessera (file scaricati)"), ("documenti", "📄", "Documenti personali"),
               ("medicinali", "💊", "Medicinali"), ("terapie", "📅", "Terapie"), ("parametri", "📈", "Parametri e valori"), ("controlli", "⏰", "Controlli periodici"),
               ("medici", "👩‍⚕️", "Medici e riferimenti"), ("emergenza", "🆘", "Dati per l'emergenza")]
_STT_NOME = {k: (i, n) for k, i, n in _STT_GRUPPI}


def _stt_files(obj):
    """Tutti i file allegati (foto, PDF) dentro una voce: riferimenti del tipo {id, nome, mime}."""
    out, visti = [], set()

    def _g(o):
        if isinstance(o, dict):
            if isinstance(o.get("id"), str) and (o.get("mime") or (o.get("nome") and o.get("sha"))) and o["id"] not in visti:
                visti.add(o["id"])
                out.append({"id": o["id"], "nome": o.get("nome") or o["id"], "mime": o.get("mime") or ""})
            for v in o.values():
                _g(v)
        elif isinstance(o, list):
            for v in o:
                _g(v)
    _g(obj)
    return out


def _stt_t(x, *chiavi, default=""):
    for k in chiavi:
        v = x.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return default


def _stt_dett(*parti):
    return " · ".join(str(p).strip() for p in parti if p and str(p).strip())


def _stt_data(iso):
    try:
        return data_it(iso) if iso else ""
    except Exception:
        return str(iso or "")


def stt_inventario(f, pid):
    """Tutto ciò che c'è di una persona, come elenco di voci {id, gruppo, titolo, data, dett, files, solo_info}."""
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {"id": pid, "nome": ""})
    voci = []

    def agg(gruppo, vid, titolo, data="", dett="", obj=None, info=False):
        files = _stt_files(obj) if obj is not None and not info else []
        voci.append({"id": f"{gruppo}:{vid}", "gruppo": gruppo, "titolo": titolo or "(senza titolo)", "data": data or "", "dett": dett or "", "files": files, "solo_info": info and not files})
    mio = lambda x: x.get("profilo", "p0") == pid
    for i, x in enumerate(p.get("docsan", []) or []):
        t = x.get("titolo") or (sp_titolo_doc(x) if "sp_titolo_doc" in globals() else "") or _stt_t(x, "esame", "tipo")
        agg("docsan", x.get("id", i), t, x.get("data") or x.get("data_referto"), _stt_dett(x.get("tipo"), x.get("specialita"), x.get("medico"), x.get("struttura")), x)
    for i, x in enumerate(f.get("prescrizioni", []) or []):
        if mio(x):
            agg("prescrizioni", x.get("id", i), _stt_t(x, "titolo", "nome", "medicinale", "descrizione", default="Prescrizione"), x.get("data"), _stt_dett(x.get("medico"), x.get("note")), x)
    for i, x in enumerate(f.get("visite", []) or []):
        if mio(x):
            agg("visite", x.get("id", i), _stt_dett(_stt_t(x, "categoria", "specialita", "nome", default="Visita"), x.get("prestazione")), x.get("data"), _stt_dett(x.get("medico"), x.get("struttura"), x.get("esito")), x)
    for i, x in enumerate(f.get("vaccinazioni", []) or []):
        if mio(x):
            agg("vaccinazioni", x.get("id", i), _stt_t(x, "nome", default="Vaccinazione"), x.get("data"), _stt_dett(x.get("dose"), ("richiamo " + _stt_data(x["richiamo"])) if x.get("richiamo") else ""), x)
    for i, x in enumerate(p.get("esenzioni", []) or []):
        agg("esenzioni", x.get("id", i), _stt_t(x, "titolo", "tipo", "nome", default="Invalidità o esenzione"), x.get("rilascio") or x.get("data"), _stt_dett(x.get("tipo"), x.get("codice"), ("fino al " + _stt_data(x["fino_al"])) if x.get("fino_al") else ""), x)
    for k, nome in (("fse", "Fascicolo sanitario elettronico"), ("vaccini", "Vaccinazioni online"), ("spese", "Spese sanitarie detraibili")):
        fl = _stt_files((p.get("file_voce") or {}).get(k))
        if fl:
            agg("fascicolo", k, nome, "", "documento scaricato", (p.get("file_voce") or {}).get(k))
    for i, x in enumerate(f.get("documenti", []) or []):
        if mio(x):
            agg("documenti", x.get("id", i), _stt_t(x, "nome", "titolo", "tipo", default="Documento"), x.get("scadenza"), _stt_dett(x.get("tipo"), x.get("numero")), x)
    for i, x in enumerate(f.get("medicinali", []) or []):
        if mio(x):
            agg("medicinali", x.get("id", i), _stt_t(x, "nome", default="Medicinale"), x.get("scadenza"), _stt_dett(x.get("marca"), x.get("principio")), x)
    for i, x in enumerate(f.get("terapie", []) or []):
        if mio(x):
            agg("terapie", x.get("id", i), _stt_t(x, "nome_med", "nome", default="Terapia"), "", _stt_dett(", ".join(x.get("orari", []) or []), x.get("stato")), x, info=True)
    try:
        for n, u, d_, v_ in sp_ultimi_parametri(p, 1):
            agg("parametri", n, f"{n}: {v_} {u}".strip(), d_, "ultimo valore registrato", None, info=True)
    except Exception:
        pass
    for i, x in enumerate(p.get("controlli", []) or []):
        agg("controlli", x.get("id", i), _stt_t(x, "nome", default="Controllo"), x.get("ultimo"), ("prossimo: " + _stt_data(x["prossimo"])) if x.get("prossimo") else "", None, info=True)
    dott = p.get("dottore") or {}
    if dott.get("nome") or dott.get("telefono"):
        agg("medici", "base", "Medico di base: " + (dott.get("nome") or ""), "", _stt_dett(dott.get("telefono"), dott.get("email")), None, info=True)
    for i, x in enumerate(p.get("medici", []) or []):
        agg("medici", x.get("id", i), _stt_dett(x.get("ruolo"), x.get("nome")), "", _stt_dett(x.get("telefono"), x.get("struttura")), None, info=True)
    sp = p.get("sp") or {}
    righe = []
    all_ = list((f.get("allergie") or {}).get(pid, [])) + list(sp.get("allergie_altre", []) or [])
    if all_:
        righe.append("Allergie: " + ", ".join(all_))
    for k, et in (("dispositivi", "Impianti e dispositivi"), ("terapie_critiche", "Terapie importanti"), ("condizioni", "Condizioni")):
        if sp.get(k):
            righe.append(et + ": " + ", ".join(sp[k]))
    if p.get("gruppo"):
        righe.append("Gruppo sanguigno: " + str(p["gruppo"]))
    if righe or sp.get("nascita"):
        agg("emergenza", "dati", "Dati per l'emergenza", sp.get("nascita"), " · ".join(righe), None, info=True)
    return voci


def stt_nome_file(titolo, data, n, mime_o_nome):
    base = re.sub(r"[^\w\- ]+", "", str(titolo or "documento"), flags=re.U).strip().replace(" ", "_")[:50] or "documento"
    ext = ""
    m = re.search(r"\.([A-Za-z0-9]{2,5})$", str(mime_o_nome or ""))
    if m:
        ext = "." + m.group(1).lower()
    elif "pdf" in str(mime_o_nome or ""):
        ext = ".pdf"
    elif "jpeg" in str(mime_o_nome or "") or "jpg" in str(mime_o_nome or ""):
        ext = ".jpg"
    elif "png" in str(mime_o_nome or ""):
        ext = ".png"
    pref = (str(data)[:10] + "_") if data else ""
    return f"{pref}{base}{'_' + str(n) if n else ''}{ext}"


def stt_html_elenco(nome, voci):
    """La pagina dell'elenco (si stampa o si salva in PDF)."""
    e = _stt_html.escape
    oggi_ = datetime.now().strftime("%d/%m/%Y")
    h = [f"<html><head><meta charset='utf-8'><title>Elenco di {e(nome)}</title></head><body style='font-family:sans-serif;font-size:11pt'>",
         f"<h1 style='font-size:17pt'>Elenco dei documenti e dei dati di {e(nome)}</h1><p>Preparato il {oggi_} dall'app «La nostra dispensa». Contiene dati personali: da dare solo a chi deve vederli.</p>"]
    for k, ico, titolo in _STT_GRUPPI:
        vv = [v for v in voci if v["gruppo"] == k]
        if not vv:
            continue
        h.append(f"<h2 style='font-size:13pt;margin-top:14px'>{e(titolo)} ({len(vv)})</h2><table border='1' cellspacing='0' cellpadding='4' style='border-collapse:collapse;width:100%;font-size:10pt'>")
        h.append("<tr style='background:#e8f0f0'><th align='left'>Titolo</th><th align='left'>Data</th><th align='left'>Dettagli</th><th>File</th></tr>")
        for v in sorted(vv, key=lambda z: z["data"] or "", reverse=True):
            h.append(f"<tr><td>{e(v['titolo'])}</td><td>{e(_stt_data(v['data']))}</td><td>{e(v['dett'])}</td><td align='center'>{'📎 ' + str(len(v['files'])) if v['files'] else '—'}</td></tr>")
        h.append("</table>")
    h.append("</body></html>")
    return "".join(h)


def stt_testo_elenco(nome, voci):
    r = [f"ELENCO DEI DOCUMENTI E DEI DATI DI {nome.upper()}", f"Preparato il {datetime.now().strftime('%d/%m/%Y')}", ""]
    for k, ico, titolo in _STT_GRUPPI:
        vv = [v for v in voci if v["gruppo"] == k]
        if vv:
            r.append(f"{titolo.upper()} ({len(vv)})")
            for v in sorted(vv, key=lambda z: z["data"] or "", reverse=True):
                r.append(f"- {v['titolo']}" + (f" · {_stt_data(v['data'])}" if v["data"] else "") + (f" · {v['dett']}" if v["dett"] else "") + (f" · {len(v['files'])} file" if v["files"] else ""))
            r.append("")
    return "\n".join(r)


def stt_zip(nome, voci, carica):
    """ZIP con l'indice e i file delle voci. `carica(refs)` → [(nome, mime, bytes)]. Ritorna (bytes, n_file, saltati)."""
    buf = io.BytesIO()
    usati, n_file, saltati, totale = set(), 0, [], 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("INDICE.html", stt_html_elenco(nome, voci))
        z.writestr("INDICE.txt", stt_testo_elenco(nome, voci))
        for v in voci:
            cartella = re.sub(r"[^\w\- ]+", "", _STT_NOME.get(v["gruppo"], ("", v["gruppo"]))[1], flags=re.U).strip().replace(" ", "_")[:40] or v["gruppo"]
            for i, rif in enumerate(v["files"], 1):
                try:
                    car = carica([rif])
                except Exception:
                    car = []
                if not car:
                    saltati.append(v["titolo"])
                    continue
                nm, mime, dati = car[0]
                if totale + len(dati) > 120 * 1024 * 1024:
                    saltati.append(v["titolo"] + " (troppo grande per lo ZIP)")
                    continue
                n = stt_nome_file(v["titolo"], v["data"], i if len(v["files"]) > 1 else 0, nm or mime)
                base, k = f"{cartella}/{n}", 1
                while base in usati:
                    k += 1
                    base = f"{cartella}/{k}_{n}"
                usati.add(base)
                z.writestr(base, dati)
                totale += len(dati)
                n_file += 1
    return buf.getvalue(), n_file, saltati


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def _stt_seleziona(chiavi, valore):
    for k in chiavi:
        st.session_state["stt_s_" + k] = valore


def stt_pagina(pid):
    f = _fa_dati()
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {"id": pid, "nome": ""})
    nome = p.get("nome") or "questa persona"
    st.markdown("<style>.stt-riga{font-size:1.02rem}</style>", unsafe_allow_html=True)
    if st.button("← Torna a Salute", key="stt_indietro"):
        st.session_state.pop("sp_modulo", None)
        st.rerun()
    st.subheader(f"📋 Tutti i dati e documenti · {nome}")
    st.caption("Qui vedi **tutto quello che abbiamo** di questa persona. Il **documento completo** (sopra) è il PDF di sempre. Se un medico chiede **solo certi referti o esami**, "
               "spunta le voci che servono e scarica o invia i loro file.")
    voci = stt_inventario(f, pid)
    if "inv_hub" in globals():
        st.markdown("### 📄 1 · Il documento completo")
        st.caption("È il **report di sempre** (PDF, Excel o da stampare, con tutte le voci), ora **completo**: comprende anche documenti sanitari, esenzioni, parametri, controlli, medici e dati per l'emergenza. "
                   "Scegli le sezioni, tocca **Prepara i file** e poi stampa, scarica o invia come hai sempre fatto.")
        try:
            p_ = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {"id": pid, "nome": nome})
            inv_hub(f"profilo_{pid}_pagina", [{"chiave": "io:" + pid, "nome": nome, "origine": "", "d": _inv_dati_conto(), "f": f, "pid": pid, "p": p_}], _inv_dati_conto(), "Salute – " + nome)
        except Exception as ex:
            st.error(f"Non riesco ad aprire l'esportazione ({type(ex).__name__}): riprova.")
        st.divider()
        st.markdown("### 📋 2 · Cosa abbiamo a disposizione (e i file da dare al medico)")
    if not voci:
        st.info("Per ora non c'è niente di registrato per questa persona.")
        return
    con_file = [v for v in voci if v["files"]]
    n_f = sum(len(v["files"]) for v in voci)
    st.markdown(f"**{len(voci)} {'voce' if len(voci) == 1 else 'voci'}** · 📎 **{n_f} {'file' if n_f == 1 else 'file'}** in {len(con_file)} {'voce' if len(con_file) == 1 else 'voci'}")
    q = st.text_input("Cerca (esame, medico, struttura, anno…)", key="stt_q", placeholder="es. emocromo, cardiologo, 2025", label_visibility="collapsed")
    gruppi_presenti = [(k, i, n) for k, i, n in _STT_GRUPPI if any(v["gruppo"] == k for v in voci)]
    scelta = st.multiselect("Gruppi da vedere", [n for _k, _i, n in gruppi_presenti], default=[], key="stt_gr", placeholder="Tutti i gruppi", label_visibility="collapsed")
    solo_file = st.toggle("Solo le voci con file (📎)", key="stt_sf")
    qn = (q or "").lower().strip()
    chiavi_scelte = {k for k, i, n in gruppi_presenti if n in scelta} or {k for k, _i, _n in gruppi_presenti}
    visibili = [v for v in voci if v["gruppo"] in chiavi_scelte and (not solo_file or v["files"])
                and (not qn or qn in (v["titolo"] + " " + v["dett"] + " " + v["data"] + " " + _stt_data(v["data"])).lower())]
    c1, c2 = st.columns(2, gap="small")
    c1.button("☑️ Seleziona tutto", key="stt_tutto", width="stretch", on_click=_stt_seleziona, args=([v["id"] for v in visibili], True))
    c2.button("⬜ Deseleziona tutto", key="stt_niente", width="stretch", on_click=_stt_seleziona, args=([v["id"] for v in voci], False))
    st.caption(f"Mostro {len(visibili)} voci su {len(voci)}.")
    for k, ico, titolo in _STT_GRUPPI:
        vv = [v for v in visibili if v["gruppo"] == k]
        if not vv:
            continue
        with st.expander(f"{ico} {titolo} ({len(vv)})", expanded=(len(visibili) <= 25 or bool(qn))):
            for v in sorted(vv, key=lambda z: z["data"] or "", reverse=True):
                et = f"**{v['titolo']}**" + (f" · {_stt_data(v['data'])}" if v["data"] else "") + (f" · {v['dett']}" if v["dett"] else "") + (f" · 📎 {len(v['files'])}" if v["files"] else "")
                if v["solo_info"]:
                    st.markdown("• " + et)
                else:
                    st.checkbox(et, key="stt_s_" + v["id"])
    scelte = [v for v in voci if st.session_state.get("stt_s_" + v["id"]) and not v["solo_info"]]
    n_file_sc = sum(len(v["files"]) for v in scelte)
    st.divider()
    st.markdown(f"#### Cosa vuoi fare? · ☑️ {len(scelte)} {'voce scelta' if len(scelte) == 1 else 'voci scelte'} ({n_file_sc} file)")
    st.markdown("**I file delle voci scelte** (foto e PDF veri, in uno ZIP o inviati)")
    if not scelte:
        st.caption("Spunta almeno una voce qui sopra (o tocca «Seleziona tutto»).")
    else:
        if st.button(f"⬇ Prepara lo ZIP con {n_file_sc} file", key="stt_prep_zip", width="stretch", disabled=(n_file_sc == 0)):
            with st.spinner("Preparo lo ZIP…"):
                z, nf, saltati = stt_zip(nome, scelte, _fa_inv_allegati)
            st.session_state["stt_zip"] = {"dati": z, "n": nf, "saltati": saltati}
        zz = st.session_state.get("stt_zip")
        if zz:
            st.download_button(f"⬇ Scarica lo ZIP ({zz['n']} file + indice)", zz["dati"], file_name="documenti_" + re.sub(r"\W+", "_", nome) + ".zip", mime="application/zip", key="stt_dl_zip", width="stretch")
            if zz["saltati"]:
                st.warning("Non sono riuscito a includere: " + "; ".join(zz["saltati"][:6]) + ".")
        if n_file_sc == 0:
            st.caption("Le voci scelte non hanno file allegati: compaiono solo nell'elenco.")
        elif "_fa_inv_voce" in globals():
            refs = [r for v in scelte for r in v["files"]]
            righe = [(v["titolo"], _stt_dett(_stt_data(v["data"]), v["dett"])) for v in scelte[:30]]
            _fa_inv_voce("stt_inv_" + pid, f"📤 Invia le {len(scelte)} voci scelte", f"Documenti di {nome}", righe, refs)
    st.caption("Per **un solo** documento puoi anche aprire **🗂️ Documenti sanitari** e usare **Vedi / Scarica / Invia** sulla sua scheda.")


def stt_dati_completi(f, pid):
    """Per l'esportazione tecnica (JSON): tutti i dati della persona, vecchi e nuovi."""
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {})
    out = {k: p.get(k) for k in ("docsan", "esenzioni", "parametri", "controlli", "medici", "sp", "sanitario", "dottore", "file_voce", "bambino") if p.get(k) not in (None, [], {})}
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Le sezioni NUOVE entrano anche nell'esportazione classica («Esporta e invia»: PDF, Excel, pagina da stampare, JSON) che usa FAM_SEZIONI (famiglia.py).
# Prima quel report si fermava a medicinali, terapie, prescrizioni, visite, vaccinazioni, documenti: sotto «Visite, esami e referti» compariva «Nessun dato inserito»
# anche se la persona aveva documenti sanitari classificati.
# ---------------------------------------------------------------------------------------------------------------------
def _stt_fd(iso):
    try:
        return _fam_d(iso) if "_fam_d" in globals() else _stt_data(iso)
    except Exception:
        return str(iso or "")


def _stt_nomi_file(x):
    n = [r["nome"] for r in _stt_files(x)]
    return ", ".join(n[:3]) + (f" (+{len(n) - 3})" if len(n) > 3 else "")


def _stt_righe_docsan(p):
    pr = p["p"]
    righe = []
    for d in sorted(pr.get("docsan", []) or [], key=lambda x: x.get("data") or x.get("data_referto") or "", reverse=True):
        titolo = d.get("titolo") or (sp_titolo_doc(d) if "sp_titolo_doc" in globals() else "") or d.get("esame", "")
        righe.append([_stt_fd(d.get("data") or d.get("data_referto")), d.get("tipo", ""), titolo, d.get("specialita", ""), d.get("medico", ""), d.get("struttura", ""),
                      (str(d.get("conclusioni", ""))[:160] + ("…" if len(str(d.get("conclusioni", ""))) > 160 else "")), _stt_nomi_file(d)])
    return righe


_STT_H_DOCSAN = ["Data", "Tipo", "Titolo", "Specialità", "Medico", "Struttura", "Conclusioni", "File"]


def _stt_righe_esenzioni(p):
    righe = []
    for x in p["p"].get("esenzioni", []) or []:
        righe.append([x.get("tipo", ""), x.get("titolo", ""), x.get("codice", ""), str(x.get("percentuale", "") or ""), x.get("ente", ""), _stt_fd(x.get("rilascio")),
                      "permanente" if x.get("permanente") else _stt_fd(x.get("fino_al")), x.get("patologia", "") or x.get("note", ""), _stt_nomi_file(x)])
    return righe


_STT_H_ESENZ = ["Tipo", "Titolo", "Codice", "Percentuale", "Ente", "Rilascio", "Valida fino al", "Patologia o note", "File"]


def _stt_righe_parametri(p):
    righe = []
    for m in sorted(p["p"].get("parametri", []) or [], key=lambda x: x.get("data", ""), reverse=True)[:300]:
        try:
            val = _sp_fmt_param(m)
        except Exception:
            val = str(m.get("valore", ""))
        righe.append([_stt_fd(m.get("data")), m.get("nome") or m.get("tipo", ""), val, m.get("unita", "") or "", m.get("note", "")])
    return righe


_STT_H_PARAM = ["Data", "Parametro", "Valore", "Unità", "Note"]


def _stt_righe_controlli(p):
    return [[x.get("nome", ""), str(x.get("ogni_mesi", "") or ""), _stt_fd(x.get("ultimo")), _stt_fd(x.get("prossimo")), x.get("note", "")] for x in p["p"].get("controlli", []) or []]


_STT_H_CONTR = ["Controllo", "Ogni (mesi)", "Ultimo", "Prossimo", "Note"]


def _stt_righe_medici(p):
    return [[x.get("ruolo", ""), x.get("nome", ""), x.get("telefono", ""), x.get("email", ""), x.get("struttura", ""), x.get("note", "")] for x in p["p"].get("medici", []) or []]


_STT_H_MEDICI = ["Ruolo", "Nome", "Telefono", "Email", "Struttura", "Note"]


def _stt_righe_emergenza(p):
    pr, f, pid = p["p"], p["f"], p["pid"]
    sp = pr.get("sp") or {}
    r = []
    if sp.get("nascita"):
        r.append(["Data di nascita", _stt_fd(sp["nascita"])])
    for k, et in (("sesso", "Sesso"), ("altezza", "Altezza"), ("peso", "Peso")):
        if sp.get(k):
            r.append([et, str(sp[k])])
    all_ = list((f.get("allergie") or {}).get(pid, [])) + list(sp.get("allergie_altre", []) or []) + ([sp["allergie_cibi"]] if sp.get("allergie_cibi") else [])
    if all_:
        r.append(["Allergie", ", ".join(all_)])
    for k, et in (("dispositivi", "Impianti e dispositivi"), ("terapie_critiche", "Terapie importanti"), ("condizioni", "Condizioni")):
        if sp.get(k):
            r.append([et, ", ".join(sp[k])])
    for c in sp.get("contatti", []) or []:
        r.append(["Contatto di emergenza", _stt_dett(c.get("nome"), c.get("telefono"), c.get("relazione"))])
    return r


_STT_H_EMERG = ["Voce", "Valore"]


def _stt_righe_fascicolo(p):
    r = []
    for k, nome in (("fse", "Fascicolo sanitario elettronico"), ("vaccini", "Vaccinazioni online"), ("spese", "Spese sanitarie detraibili")):
        fl = (p["p"].get("file_voce") or {}).get(k)
        if _stt_files(fl):
            r.append([nome, _stt_nomi_file(fl)])
    return r


_STT_H_FASC = ["Voce", "File"]


def _stt_registra_sezioni():
    if "FAM_SEZIONI" not in globals() or "FAM_TITOLI" not in globals():
        return
    nuove = [("Documenti sanitari (referti, esami, ricette)", _STT_H_DOCSAN, _stt_righe_docsan), ("Invalidità ed esenzioni", _STT_H_ESENZ, _stt_righe_esenzioni),
             ("Parametri e valori", _STT_H_PARAM, _stt_righe_parametri), ("Controlli periodici", _STT_H_CONTR, _stt_righe_controlli),
             ("Medici e riferimenti", _STT_H_MEDICI, _stt_righe_medici), ("Dati per l'emergenza", _STT_H_EMERG, _stt_righe_emergenza), ("Fascicolo e tessera (file)", _STT_H_FASC, _stt_righe_fascicolo)]
    gia = {t_ for t_, _h, _f in FAM_SEZIONI}
    pos = next((i + 1 for i, (t_, _h, _f) in enumerate(FAM_SEZIONI) if t_ == "Visite, esami e referti"), len(FAM_SEZIONI))
    for k, n_ in enumerate([x for x in nuove if x[0] not in gia]):
        FAM_SEZIONI.insert(pos + k, n_)
    FAM_TITOLI[:] = [t_ for t_, _h, _f in FAM_SEZIONI]


try:
    _stt_registra_sezioni()
except Exception:
    pass
