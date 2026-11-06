# -*- coding: utf-8 -*-
"""INVALIDITÀ ED ESENZIONI — dentro Salute, per ogni persona.

Si registra ogni documento di invalidità o di esenzione: verbale di invalidità civile, Legge 104, indennità di accompagnamento, esenzione ticket (per patologia, per invalidità, per reddito/età/
disoccupazione, per gravidanza), contrassegno disabili, agevolazioni auto… Per ognuno: tipo, motivo o patologia, CODICE dell'esenzione, PERCENTUALE di invalidità, ente, numero del verbale,
data di rilascio, VALIDITÀ (dal… fino al…, oppure «permanente»), prossima REVISIONE, note e il FILE originale (PDF o foto).
Si carica con il pulsante arancione: lo leggo io, propongo i dati e archivio SOLO dopo la tua conferma. Le scadenze e le revisioni entrano negli avvisi (Home che lampeggia, Salute, promemoria).
Per ogni voce: 👁️ Vedi / scarica · ✏️ Correggi · 📤 Invia · 🗑️ Elimina. Dati in profilo['esenzioni'] (persona per persona). Caricato dopo salute_plus.py."""
import hashlib
import html as _h_se
import re
import uuid
from datetime import date, datetime, timedelta

import streamlit as st

SE_TIPI = ["Invalidità civile", "Legge 104 (handicap)", "Indennità di accompagnamento", "Cecità o sordità", "Esenzione ticket per patologia (cronica o rara)", "Esenzione ticket per invalidità",
           "Esenzione ticket per reddito, età o disoccupazione", "Esenzione per gravidanza o prevenzione", "Contrassegno disabili (parcheggio)", "Agevolazioni auto (bollo, IVA)", "Altro"]
SE_ICONE = {"Invalidità civile": "♿", "Legge 104 (handicap)": "🪪", "Indennità di accompagnamento": "🤝", "Cecità o sordità": "🦯", "Esenzione ticket per patologia (cronica o rara)": "🏥",
            "Esenzione ticket per invalidità": "📋", "Esenzione ticket per reddito, età o disoccupazione": "💶", "Esenzione per gravidanza o prevenzione": "🤰", "Contrassegno disabili (parcheggio)": "🅿️",
            "Agevolazioni auto (bollo, IVA)": "🚗", "Altro": "📄"}
_SE_PAROLE = {
    "Invalidità civile": [("invalidità civile", 6), ("invalidita civile", 6), ("verbale di invalidità", 6), ("percentuale di invalidità", 5), ("commissione medica", 3), ("invalidità", 3), ("inps", 1)],
    "Legge 104 (handicap)": [("legge 104", 7), ("l. 104", 6), ("104/92", 7), ("handicap", 5), ("art. 3 comma 3", 6), ("situazione di gravità", 5), ("art. 3", 2)],
    "Indennità di accompagnamento": [("indennità di accompagnamento", 8), ("accompagnamento", 4), ("assegno di accompagnamento", 6)],
    "Cecità o sordità": [("cieco", 5), ("cecità", 6), ("ipovedente", 5), ("sordo", 5), ("sordità", 6), ("sordomut", 6)],
    "Esenzione ticket per patologia (cronica o rara)": [("patologia cronica", 7), ("malattia cronica", 7), ("malattia rara", 7), ("patologia rara", 7), ("esenzione per patologia", 7), ("esenzione ticket", 3), ("codice esenzione", 3), ("patologia", 2)],
    "Esenzione ticket per invalidità": [("esenzione per invalidità", 7), ("esente per invalidità", 7), ("esenzione ticket", 2), ("invalido", 2)],
    "Esenzione ticket per reddito, età o disoccupazione": [("esenzione per reddito", 7), ("reddito", 3), ("disoccupat", 5), ("età", 1), ("codice e01", 7), ("codice e02", 7), ("codice e03", 7), ("codice e04", 7), ("e01", 3), ("e02", 3), ("e03", 3), ("e04", 3)],
    "Esenzione per gravidanza o prevenzione": [("gravidanza", 6), ("maternità", 4), ("prevenzione", 3), ("screening", 3), ("codice m", 3)],
    "Contrassegno disabili (parcheggio)": [("contrassegno", 6), ("parcheggio", 3), ("disabili", 4), ("cude", 6)],
    "Agevolazioni auto (bollo, IVA)": [("bollo", 4), ("iva agevolata", 6), ("agevolazioni auto", 6), ("veicolo", 2)],
}
_RE_COD_ESENZ = re.compile(r"(?i)(?:codice(?:\s+di)?\s+esenzione|cod\.?\s*esenzione|esenzione\s+(?:codice|cod\.?))\s*[:\-]?\s*([A-Z]{0,3}\d{2,3}[A-Z]?(?:\.\d{2,3})?)")
_RE_COD_ESENZ2 = re.compile(r"(?i)\besen(?:zione|te)\b[^\n]{0,40}?\b(\d{3}|[A-Z]\d{2}|R[A-Z]{1,2}\d{0,3})\b")


def se_tipo_da_testo(testo):
    t = " " + re.sub(r"\s+", " ", (testo or "").lower()) + " "
    punti = {tipo: sum(peso * min(t.count(par), 3) for par, peso in parole) for tipo, parole in _SE_PAROLE.items()}
    tipo, p = max(punti.items(), key=lambda kv: kv[1])
    if p < 4:
        return "Altro", p
    # un verbale di invalidità che parla anche di legge 104 resta «invalidità civile» se questa pesa di più; altrimenti vince il punteggio
    return tipo, p


def se_leggi(testo, f=None, nome_file="", oggi_=None):
    """Legge un documento di invalidità o di esenzione. Ritorna {campo: {'valore','affidabilita','fonte'}}. Niente è definitivo: si conferma sempre. Se un dato non c'è, resta vuoto."""
    oggi_ = oggi_ or _sp_oggi()
    t = testo or ""
    campi = {}
    try:
        base = sp_leggi_doc(t, f, nome_file, oggi_) if "sp_leggi_doc" in globals() else {}
    except Exception:
        base = {}
    for k in ("paziente", "cf", "profilo", "struttura", "medico"):                 # chi è, a quale profilo appartiene, dove è stato rilasciato
        if k in base:
            campi[k] = base[k]

    def metti(k, v, aff, fonte="testo"):
        if v:
            campi[k] = {"valore": v, "affidabilita": aff, "fonte": fonte}
    tipo, punti = se_tipo_da_testo(t)
    metti("tipo", tipo, "alta" if punti >= 12 else "media" if punti >= 7 else "bassa")
    cm = _RE_COD_ESENZ.search(t) or _RE_COD_ESENZ2.search(t)
    if cm:
        metti("codice", cm.group(1).upper(), "alta" if _RE_COD_ESENZ.search(t) else "media")
    pm = re.search(r"(?i)invalidit[àa][^\n%]{0,50}?(\d{2,3})\s*%", t) or re.search(r"(?i)(\d{2,3})\s*%[^\n]{0,40}invalidit", t) or re.search(r"(?i)percentuale[^\n\d]{0,25}(\d{2,3})", t)
    if pm and 1 <= int(pm.group(1)) <= 100:
        metti("percentuale", pm.group(1), "alta" if "%" in pm.group(0) else "media")
    em = re.search(r"(?i)\b(I\.?N\.?P\.?S\.?|INAIL|A\.?S\.?L\.?\s*[A-Z0-9 ]{0,18}|AUSL[^\n]{0,20}|ASST[^\n]{0,20}|Azienda Sanitaria[^\n]{0,36}|Commissione medica[^\n]{0,36})", t)
    if em:
        metti("ente", re.sub(r"\s+", " ", em.group(1)).strip(" -–,:."), "media")
    elif "struttura" in campi:
        metti("ente", campi["struttura"]["valore"], "bassa")
    vm = re.search(r"(?i)(?:verbale|protocollo|prot\.)\s*(?:n[°.º]?|numero)?\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9/\-\.]{3,24})", t)
    if vm:
        metti("protocollo", vm.group(1).strip(".-"), "media")
    mot = re.search(r"(?i)(?:patologia|malattia|diagnosi|motivo)\s*[:\-]\s*([^\n]{4,90})", t)
    if mot:
        metti("titolo", re.sub(r"\s+", " ", mot.group(1)).strip(" .:-"), "bassa", "copiato dal documento")
    # le date: rilascio / validità dal-fino al / revisione
    date_t = _sp_date_nel_testo(t, oggi_)
    ril = [d_ for d_, ctx in date_t if re.search(r"verbale.{0,25}\bdel\b|protocollo.{0,25}\bdel\b|verbale del|data verbale|rilasciat|emess|data rilascio|accertament|visita del|data del", ctx) and d_ <= oggi_]
    dal = [d_ for d_, ctx in date_t if re.search(r"valid[oa] dal|decorrenza|con decorrenza|a decorrere|\bdal\b", ctx)]
    fino = [d_ for d_, ctx in date_t if re.search(r"valid[oa] (?:fino al|sino al|al)|scadenza|scade|fino al|sino al|entro il|validità al|\bal\b", ctx) and not re.search(r"nat[oa]|nascita", ctx)]
    rev = [d_ for d_, ctx in date_t if re.search(r"revision|rivedibil|rivalutazion|riesame|rinnovo", ctx)]
    if ril:
        metti("data_rilascio", min(ril).isoformat(), "media")
    if dal:
        metti("valida_dal", min(dal).isoformat(), "media")
    if fino:
        metti("valida_fino", max(fino).isoformat(), "media", "scritta nel documento")
    if rev:
        metti("revisione", max(rev).isoformat(), "media", "scritta nel documento")
    if re.search(r"(?i)carattere permanente|non rivedibile|a tempo indeterminato|validit[àa] permanente|\bpermanente\b|definitiv", t):
        metti("permanente", "1", "media", "scritto nel documento")
    return campi


# ---------------------------------------------------------------------------------------------------------------------
# scadenze
# ---------------------------------------------------------------------------------------------------------------------
def _se_data(x):
    try:
        return date.fromisoformat(x) if x else None
    except (TypeError, ValueError):
        return None


def se_scadenza(e):
    """La data che conta per gli avvisi: la fine della validità (se non è permanente) oppure la prossima revisione."""
    perm = bool(e.get("permanente"))
    fino = _se_data(e.get("valida_fino")) if not perm else None
    rev = _se_data(e.get("revisione"))
    cand = [d_ for d_ in (fino, rev) if d_]
    return min(cand) if cand else None


def se_stato(e, oggi_=None):
    """(stato, giorni): 'scaduta', 'in_scadenza' (entro 60 giorni), 'valida', 'permanente', 'senza_data'."""
    oggi_ = oggi_ or _sp_oggi()
    s = se_scadenza(e)
    if not s:
        return ("permanente" if e.get("permanente") else "senza_data"), None
    g = (s - oggi_).days
    return ("scaduta" if g < 0 else "in_scadenza" if g <= 60 else "valida"), g


def sp_esenzioni_scadenti(p, oggi_=None, entro=60):
    """[(giorni, esenzione)] già scadute (da meno di un anno) o in scadenza entro N giorni, ordinate."""
    oggi_ = oggi_ or _sp_oggi()
    out = []
    for e in p.get("esenzioni", []) or []:
        if e.get("avvisa") is False:
            continue
        stato, g = se_stato(e, oggi_)
        if g is not None and -365 <= g <= entro:
            out.append((g, e))
    return sorted(out, key=lambda x: x[0])


def _se_testo_stato(e, oggi_=None):
    stato, g = se_stato(e, oggi_)
    s = se_scadenza(e)
    txt = _sp_data_it(s.isoformat()) if s else ""
    return {"scaduta": f"🔴 SCADUTA da {abs(g or 0)} giorni · {txt}", "in_scadenza": f"🟠 Scade tra {g} giorni · {txt}" if g else f"🟠 Scade oggi · {txt}", "valida": f"🟢 Valida fino al {txt} ({g} giorni)",
            "permanente": "🟢 Permanente (non scade)", "senza_data": "⚪ Nessuna scadenza indicata"}[stato]


def se_titolo(e):
    return " · ".join(x for x in (e.get("tipo", "Esenzione"), ("codice " + e["codice"]) if e.get("codice") else "", (e.get("percentuale") + "%") if e.get("percentuale") else "", e.get("titolo", "")) if x)


# ---------------------------------------------------------------------------------------------------------------------
# modulo di conferma / correzione
# ---------------------------------------------------------------------------------------------------------------------
def _se_form(chiave, f, pid, v=None, riconosciuto=None, con_profilo=True):
    v = v or {}
    riconosciuto = riconosciuto or {}

    def val(k, d=""):
        return v.get(k) or (riconosciuto.get(k) or {}).get("valore", d)

    def aff(k):
        a = (riconosciuto.get(k) or {}).get("affidabilita")
        return {"alta": " 🟢", "media": " 🟡", "bassa": " 🟠"}.get(a, "")

    def data_iso(k):
        return _se_data(val(k))
    profili = _fa_profili(f)
    with st.form(chiave, border=False):
        if con_profilo:
            prop = (riconosciuto.get("profilo") or {}).get("valore")
            pids = [p["id"] for p in profili]
            att = prop if prop in pids else pid
            profilo = st.selectbox("👤 Di chi è" + (aff("profilo") if prop else ""), pids, index=pids.index(att) if att in pids else 0, format_func=lambda i: next(p["nome"] for p in profili if p["id"] == i))
        else:
            profilo = pid
        t_att = val("tipo") if val("tipo") in SE_TIPI else "Altro"
        tipo = st.selectbox("📂 Che documento è" + aff("tipo"), SE_TIPI, index=SE_TIPI.index(t_att), format_func=lambda x: f"{SE_ICONE.get(x, '')} {x}")
        titolo = st.text_input("Motivo o patologia (facoltativo)" + aff("titolo"), value=val("titolo"), placeholder="es. Diabete mellito, Invalidità per ipoacusia")
        c1, c2 = st.columns(2)
        codice = c1.text_input("Codice dell'esenzione" + aff("codice"), value=val("codice"), placeholder="es. 013, C02, E01")
        perc = c2.text_input("Percentuale di invalidità" + aff("percentuale"), value=val("percentuale"), placeholder="es. 75")
        c3, c4 = st.columns(2)
        ente = c3.text_input("Ente che l'ha rilasciato" + aff("ente"), value=val("ente"), placeholder="es. INPS, ASL TO1")
        prot = c4.text_input("Numero del verbale o protocollo" + aff("protocollo"), value=val("protocollo"))
        rilascio = st.date_input("Data del verbale o del rilascio" + aff("data_rilascio"), value=data_iso("data_rilascio"), format="DD/MM/YYYY")
        perm = st.checkbox("♾️ È permanente (non scade)" + aff("permanente"), value=bool(val("permanente")))
        c5, c6 = st.columns(2)
        dal = c5.date_input("Valida dal" + aff("valida_dal"), value=data_iso("valida_dal"), format="DD/MM/YYYY")
        fino = c6.date_input("Valida fino al" + aff("valida_fino"), value=data_iso("valida_fino"), format="DD/MM/YYYY", help="Se è permanente lascia vuoto e spunta «È permanente».")
        rev = st.date_input("Prossima revisione o rinnovo" + aff("revisione"), value=data_iso("revisione"), format="DD/MM/YYYY", help="La data in cui va rivisto o rinnovato: ti avviso prima.")
        avvisa = st.checkbox("🔔 Avvisami prima della scadenza o della revisione", value=v.get("avvisa", True))
        note = st.text_area("Note (cosa dà diritto, a chi rivolgersi, numeri utili…)", value=v.get("note", ""), height=90)
        ok = st.form_submit_button("✅ Conferma e archivia" if not v.get("id") else "💾 Salva le correzioni", type="primary", width="stretch")
    return ok, {"profilo": profilo, "tipo": tipo, "titolo": titolo.strip(), "codice": codice.strip().upper(), "percentuale": re.sub(r"[^\d]", "", perc)[:3], "ente": ente.strip(), "protocollo": prot.strip(),
                "data_rilascio": rilascio.isoformat() if rilascio else "", "permanente": bool(perm), "valida_dal": dal.isoformat() if dal else "", "valida_fino": fino.isoformat() if fino else "",
                "revisione": rev.isoformat() if rev else "", "avvisa": bool(avvisa), "note": note.strip()}


def _se_archivia(pid, rif, val, riconosciuto, utente):
    """Salva la voce nella cartella della persona scelta (con il file originale, se c'è)."""
    e = dict(val)
    e.pop("profilo", None)
    e.update({"id": uuid.uuid4().hex[:10], "file": rif or {}, "creato_il": datetime.now().isoformat(timespec="seconds"), "riconosciuto": {k: v_.get("valore") for k, v_ in (riconosciuto or {}).items()},
              "conferma": {"da": utente, "il": datetime.now().isoformat(timespec="seconds")}})

    def _fn(p):
        p["esenzioni"] = list(p.get("esenzioni", [])) + [e]
    _sp_salva_profilo(pid, _fn, "Salute: invalidità o esenzione archiviata")
    return e


def _se_dialogo_togli(pid, eid, titolo):
    def _finestra():
        st.warning(f"Eliminare questa voce?\n\n**{_h_se.escape(titolo)}**")
        st.caption("Il file originale, se c'è, verrà cancellato.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=f"se_del_si_{eid}", type="primary", width="stretch"):
            ids = []

            def _fn(p):
                for e in p.get("esenzioni", []):
                    if e.get("id") == eid and (e.get("file") or {}).get("id"):
                        ids.append(e["file"]["id"])
                p["esenzioni"] = [e for e in p.get("esenzioni", []) if e.get("id") != eid]
            _sp_salva_profilo(pid, _fn, "Salute: invalidità o esenzione eliminata")
            if ids:
                _fa_cancella_files(ids)
            st.session_state["fa_msg"] = "🗑️ Eliminata."
            st.rerun()
        if s2.button("No, tienila", key=f"se_del_no_{eid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina")(_finestra)()


# ---------------------------------------------------------------------------------------------------------------------
# flusso: file → lettura → finestra di conferma → archivio
# ---------------------------------------------------------------------------------------------------------------------
def _se_chiudi(coda):
    if coda:
        coda.pop(0)
    st.session_state["ca_giro"] = st.session_state.get("ca_giro", 0) + 1
    st.session_state.pop("se_fin", None)


def _se_corpo(f, p, pid, utente, coda):
    c = coda[0]
    st.markdown(f"#### 📖 {_sp_e(c['nome'])}" + (f" (ne restano {len(coda) - 1} dopo questo)" if len(coda) > 1 else ""))
    if c.get("manuale"):
        riconosciuto, letto = {}, False
        st.info("Compili tu i dati: nessun file allegato (potrai aggiungerlo poi correggendo la voce con un nuovo caricamento).")
    else:
        mime = _ca_mime(c["nome"], "", c["dati"]) if "_ca_mime" in globals() else ("application/pdf" if c["nome"].lower().endswith(".pdf") else "image/jpeg")
        if mime.startswith("image/"):
            st.image(c["dati"], width=260)
        chiave_lettura = f"se_lett_{c['sha']}"
        if chiave_lettura not in st.session_state:
            with st.spinner("Leggo il documento…"):
                try:
                    testo, info = ca_estrai_testo(c["nome"], mime, c["dati"]) if "ca_estrai_testo" in globals() else ("", {})
                except Exception:
                    testo, info = "", {}
                st.session_state[chiave_lettura] = (se_leggi(testo, f, c["nome"]) if testo.strip() else {}, bool(testo.strip()))
        riconosciuto, letto = st.session_state[chiave_lettura]
        if letto:
            st.success("Ho letto il documento. I pallini: 🟢 sicuro, 🟡 abbastanza, 🟠 poco. **Controlla e correggi** quello che serve: i dati che non ho trovato restano vuoti.")
        else:
            st.info("Non sono riuscito a leggere il testo (foto sfocata o scansione): compila tu i dati qui sotto.")
        gia = [e for pr in _fa_profili(f) for e in pr.get("esenzioni", []) if (e.get("file") or {}).get("sha") == c["sha"] or (e.get("file") or {}).get("sha256") == c["sha"]]
        if gia and not st.session_state.get(f"se_dup_{c['sha']}"):
            st.warning("⚠️ **Questo stesso file è già archiviato** tra le invalidità ed esenzioni.")
            q1, q2 = st.columns(2, gap="small")
            if q1.button("📥 Archivia lo stesso", key="se_dup_si", width="stretch"):
                st.session_state[f"se_dup_{c['sha']}"] = True
                st.rerun()
            if q2.button("✖ Non archiviare", key="se_dup_no", width="stretch"):
                _se_chiudi(coda)
                st.rerun()
            return
    ok, val = _se_form("se_form_" + c["sha"][:10], f, pid, riconosciuto=riconosciuto)
    b2 = st.columns(1)[0]
    if b2.button("✖ Scarta questo", key="se_scarta", width="stretch"):
        _se_chiudi(coda)
        st.rerun()
    if ok:
        try:
            rif = {}
            if not c.get("manuale"):
                rifs = _fa_salva_files([_SpUp(c["nome"], c["dati"])])
                rif = rifs[0] if rifs else {"id": "", "nome": c["nome"], "mime": mime, "sha": c["sha"]}
            dest = val["profilo"]
            _se_archivia(dest, rif, val, riconosciuto, utente)
            _se_chiudi(coda)
            nome_dest = next((x["nome"] for x in _fa_profili(f) if x["id"] == dest), "")
            st.session_state["fa_msg"] = f"✅ Archiviato nella cartella di {nome_dest}."
            st.rerun()
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare: {ex}")


def _se_finestra(f, p, pid, utente, coda):
    chiave = coda[0]["sha"]

    def _apri():
        def _fin():
            _se_corpo(f, p, pid, utente, coda)
        try:
            st.dialog("🪪 Invalidità o esenzione: controlla e conferma", width="large")(_fin)()
        except TypeError:
            st.dialog("🪪 Invalidità o esenzione: controlla e conferma")(_fin)()
    if st.session_state.get("se_fin") != chiave:
        st.session_state["se_fin"] = chiave
        _apri()
    else:
        st.info(f"📖 C'è un documento aperto: «{_sp_e(coda[0]['nome'])}». Se hai chiuso la finestra, riaprila.")
        r1, r2 = st.columns(2, gap="small")
        if r1.button("📖 Riapri", key="se_riapri", type="primary", width="stretch"):
            _apri()
        if r2.button("✖ Scarta", key="se_scarta_f", width="stretch"):
            _se_chiudi(coda)
            st.rerun()


def se_da_docsan(pid, item):
    """Dai Documenti sanitari: un file che sembra un'invalidità o un'esenzione passa qui."""
    coda = st.session_state.setdefault("se_coda", [])
    if not any(c["sha"] == item["sha"] for c in coda):
        coda.insert(0, {"nome": item["nome"], "dati": item["dati"], "sha": item["sha"]})
    st.session_state["sp_modulo"] = {"vista": "esenzioni", "pid": pid}


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def _se_riga(e, pid, f, p, vedi):
    stato, g = se_stato(e)
    righe_dati = [("Codice", e.get("codice")), ("Invalidità", (e["percentuale"] + "%") if e.get("percentuale") else ""), ("Ente", e.get("ente")), ("Verbale", e.get("protocollo")),
                  ("Rilasciato il", _sp_data_it(e.get("data_rilascio"))), ("Valida dal", _sp_data_it(e.get("valida_dal"))),
                  ("Valida fino al", "permanente" if e.get("permanente") else _sp_data_it(e.get("valida_fino"))), ("Revisione", _sp_data_it(e.get("revisione")))]
    dati = " · ".join(f"{k}: {v}" for k, v in righe_dati if v)
    col = {"scaduta": "#b71c1c", "in_scadenza": "#e65100", "valida": "#00897b", "permanente": "#00897b", "senza_data": "#757575"}[stato]
    st.markdown(f"<div class='sp-card' style='border-left:6px solid {col}'><b>{SE_ICONE.get(e.get('tipo'), '📄')} {_sp_e(se_titolo(e))}</b><br><small>{_sp_e(dati)}</small><br><b style='color:{col}'>{_sp_e(_se_testo_stato(e))}</b>"
                + (f"<br><small>📝 {_sp_e(e.get('note'))}</small>" if e.get("note") else "") + "</div>", unsafe_allow_html=True)
    ref = e.get("file") or {}
    c1, c2 = st.columns(2, gap="small")
    if ref.get("id"):
        aperto = ref["id"] in vedi
        if c1.button("🙈 Chiudi" if aperto else "👁️ Vedi / scarica", key=f"se_v_{e['id']}", width="stretch"):
            vedi.remove(ref["id"]) if aperto else vedi.append(ref["id"])
            st.rerun()
    else:
        c1.caption("Nessun file allegato")
    if c2.button("✏️ Correggi", key=f"se_c_{e['id']}", width="stretch"):
        st.session_state["se_cor"] = None if st.session_state.get("se_cor") == e["id"] else e["id"]
        st.rerun()
    if ref.get("id") and ref["id"] in vedi:
        _sp_mostra(ref)
    d1, d2 = st.columns(2, gap="small")
    with d1:
        _fa_inv_voce(f"se_{e['id']}", "📤 Invia", f"{se_titolo(e)} – {p.get('nome', '')}", [("Tipo", e.get("tipo")), ("Codice", e.get("codice")), ("Percentuale", (e.get("percentuale") + "%") if e.get("percentuale") else ""),
                     ("Ente", e.get("ente")), ("Verbale", e.get("protocollo")), ("Valida fino al", "permanente" if e.get("permanente") else _sp_data_it(e.get("valida_fino"))), ("Revisione", _sp_data_it(e.get("revisione"))),
                     ("Note", e.get("note"))], [ref] if ref.get("id") else [])
    if d2.button("🗑️ Elimina", key=f"se_d_{e['id']}", width="stretch"):
        _se_dialogo_togli(pid, e["id"], se_titolo(e))
    if st.session_state.get("se_cor") == e["id"]:
        ok, val = _se_form("se_cor_" + e["id"], f, pid, v=e, con_profilo=False)
        if ok:
            def _fn(pr, eid=e["id"], nv=val):
                for x in pr.get("esenzioni", []):
                    if x.get("id") == eid:
                        x.update({k: v_ for k, v_ in nv.items() if k != "profilo"})
            _sp_salva_profilo(pid, _fn, "Salute: invalidità o esenzione corretta")
            st.session_state.pop("se_cor", None)
            st.session_state["fa_msg"] = "✅ Corretto."
            st.rerun()


def sp_modulo_esenzioni(pid):
    f, p = _sp_intestazione("🪪 Invalidità ed esenzioni", pid)
    utente = (st.session_state.get("sess") or {}).get("nome", "")
    st.caption("Qui tieni i documenti di **invalidità** e di **esenzione**: verbale di invalidità civile, Legge 104, indennità di accompagnamento, esenzione ticket (per patologia, invalidità, reddito, età, gravidanza), "
               "contrassegno disabili… Carica il documento (PDF o foto): lo leggo e ti propongo **tipo, codice dell'esenzione, percentuale, ente, validità e revisione**. **Archivio solo dopo la tua conferma.**")
    coda = st.session_state.setdefault("se_coda", [])
    n_giro = st.session_state.get("ca_giro", 0)
    arrivi = []
    if "_ca_pannello_caricamento" in globals():
        up = _ca_pannello_caricamento(n_giro, multi=False)
        if up is not None:
            arrivi.append((up.name, up.getvalue()))
        b = st.session_state.pop("ca_bozza_in", None)
        if b and b.get("dati"):
            arrivi.append((b.get("nome") or "documento", b["dati"]))
    for nome, dati in arrivi:
        sha = hashlib.sha256(dati).hexdigest()
        if not any(c_["sha"] == sha for c_ in coda):
            coda.append({"nome": nome, "dati": dati, "sha": sha})
    if st.button("✍️ Aggiungi a mano (senza file)", key="se_manuale", width="stretch") and not any(c_.get("manuale") for c_ in coda):
        coda.insert(0, {"nome": "Nuova voce a mano", "dati": b"", "sha": "manuale" + uuid.uuid4().hex[:8], "manuale": True})
        st.session_state.pop("se_fin", None)
        st.rerun()
    if coda:
        _se_finestra(f, p, pid, utente, coda)
    voci = list(p.get("esenzioni", []))
    st.divider()
    st.markdown(f"#### 🪪 Le voci di {p.get('nome', '')} ({len(voci)})")
    if not voci:
        st.info("Ancora nessuna invalidità o esenzione registrata.")
        return
    stati = [se_stato(e)[0] for e in voci]
    st.markdown(f"🟢 **{sum(1 for x in stati if x in ('valida', 'permanente', 'senza_data'))}** valide · 🟠 **{sum(1 for x in stati if x == 'in_scadenza')}** in scadenza (entro 60 giorni) · 🔴 **{sum(1 for x in stati if x == 'scaduta')}** scadute")
    cerca = st.text_input("🔍 Cerca", key=f"se_cerca_{pid}", placeholder="codice, patologia, ente…", label_visibility="collapsed")
    q = " ".join(_sp_norm_nome(cerca))
    vedi = st.session_state.setdefault("sp_vedi", [])
    gruppi = {}
    for e in voci:
        pagliaio = " ".join(_sp_norm_nome(" ".join(str(e.get(k) or "") for k in ("tipo", "titolo", "codice", "ente", "protocollo", "note", "percentuale"))))
        if q and not all(w in pagliaio for w in q.split()):
            continue
        gruppi.setdefault(e.get("tipo", "Altro"), []).append(e)
    if not gruppi:
        st.warning("Nessuna voce corrisponde.")
        return
    for tipo in [t for t in SE_TIPI if t in gruppi] + [t for t in gruppi if t not in SE_TIPI]:
        with st.expander(f"{SE_ICONE.get(tipo, '📄')} {tipo} · {len(gruppi[tipo])}"):
            for e in sorted(gruppi[tipo], key=lambda x: (se_scadenza(x) or date(2999, 1, 1))):
                _se_riga(e, pid, f, p, vedi)
