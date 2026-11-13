# -*- coding: utf-8 -*-
"""SALUTE PLUS — la cartella della salute di ogni persona, più completa.

Si aggancia alla sezione Salute SENZA toccare quello che già funziona (medicinali, terapie, visite, vaccini, dottore, scheda sanitaria):
  1. Tessera sanitaria e fascicolo: per le tre voci (fascicolo sanitario elettronico, vaccinazioni, spese detraibili) c'è ora anche il TASTO PER CARICARE
     il documento già scaricato (PDF o foto), vederlo, scaricarlo, inviarlo e toglierlo (con conferma in una finestra).
  2. Sotto i tre riquadri della persona compaiono quattro pulsanti colorati:
        👩‍⚕️ Medici e riferimenti   (pediatra, specialisti, dentista… oltre al medico di base che c'era già)
        🆘 Dati per l'emergenza     (impianti come pacemaker o bypass, anticoagulanti, allergie, contatti di emergenza…)
        📄 Scheda per il medico     (una scheda esportabile e inviabile che racconta la persona: allergie, impianti, interventi, storia clinica…)
        👶 Percorso del bambino     (crescita, tappe, alimentazione, malattie, dentini…) — compare per le persone segnate come bambini
  3. La «Scheda per il medico» si compone da sola con tutto ciò che c'è nell'app e si aggiorna ogni volta che la apri. È scritta SENZA intelligenza artificiale
     (nessun dato esce dall'app). Facoltativo: con il consenso di quella persona, e solo se nei Secrets c'è la chiave dell'assistente, un servizio di
     intelligenza artificiale può scrivere una sintesi più scorrevole usando i fatti clinici SENZA nome, codice fiscale, telefono e indirizzo.
Tutto si può modificare, esportare (HTML e PDF) e inviare come il resto dell'app. Le informazioni sono quelle inserite dall'utente: non sono certificate da un medico.
Caricato da app_dispensa.py dopo farmacia.py e pagine_nav.py."""
import base64
import hashlib
import html as _h
import io
import json
import re
import uuid
from datetime import date, datetime, timedelta

import streamlit as st

_SP_MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
_SP_RUOLI_MEDICO = ["Pediatra", "Medico di base", "Specialista", "Dentista", "Ginecologo/a", "Fisioterapista", "Psicologo/a", "Guardia medica", "Altro"]
_SP_DISPOSITIVI = ["Pacemaker", "Defibrillatore impiantabile", "Bypass coronarico", "Stent coronarico", "Protesi valvolare cardiaca", "Protesi d'anca o ginocchio",
                   "Altre protesi o placche ortopediche", "Derivazione (shunt)", "Microinfusore di insulina o sensore", "Impianto cocleare o protesi acustica",
                   "Stomia", "Catetere o porta venosa", "Spirale o impianto contraccettivo"]
_SP_TERAPIE_CRITICHE = ["Anticoagulanti (es. warfarin, apixaban)", "Antiaggreganti (es. aspirina, clopidogrel)", "Insulina", "Cortisone assunto da tempo",
                        "Immunosoppressori", "Chemioterapia o radioterapia in corso", "Ossigenoterapia", "Dialisi"]
_SP_CONDIZIONI = ["Gravidanza", "Allattamento", "Donatore di organi", "Direttive anticipate di trattamento (DAT) fatte", "Invalidità riconosciuta", "Usa occhiali o lenti",
                  "Protesi dentaria", "Fumatore", "Non può ricevere trasfusioni"]
_SP_ALLERGIE_ALTRE = ["Lattice", "Mezzi di contrasto", "Anestetici", "Punture di insetti", "Nichel", "Polvere o pollini"]
_SP_TAPPE = ["Primo sorriso", "Sostiene il capo", "Si gira da solo", "Sta seduto senza appoggio", "Gattona", "Si alza in piedi", "Primi passi", "Prime parole",
             "Prime frasi", "Smette il pannolino", "Dorme tutta la notte", "Va al nido o all'asilo", "Va a scuola"]
_SP_EVENTI_DENTI = ["Primo dentino", "Nuovo dentino", "Caduta di un dentino", "Visita dal dentista", "Otturazione", "Apparecchio", "Altro"]

_SP_CSS = """<style>
.st-key-sp_azioni[data-testid='stVerticalBlock'],.st-key-sp_azioni [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:8px 0 12px}
.st-key-sp_azioni button{width:100% !important;min-height:56px !important;border-radius:18px !important;color:#fff !important;border:2px solid rgba(255,255,255,.55) !important;
 box-shadow:0 4px 0 rgba(0,0,0,.25) !important;padding:6px 8px !important}
.st-key-sp_azioni button p{color:#fff !important;font-weight:900 !important;font-size:.95rem !important;line-height:1.12 !important;text-shadow:0 1px 3px rgba(0,0,0,.5);margin:0}
.st-key-sp_a_medici button{background:linear-gradient(135deg,#26a69a,#00695c) !important}
.st-key-sp_a_critici button{background:linear-gradient(135deg,#ef5350,#b71c1c) !important}
.st-key-sp_a_scheda button{background:linear-gradient(135deg,#42a5f5,#0d47a1) !important}
.st-key-sp_a_bambino button{background:linear-gradient(135deg,#ffa726,#d84315) !important}
.st-key-sp_a_docsan button{background:linear-gradient(135deg,#7e57c2,#4527a0) !important}
.st-key-sp_a_param button{background:linear-gradient(135deg,#26c6da,#00838f) !important}
.st-key-sp_a_controlli button{background:linear-gradient(135deg,#ec407a,#ad1457) !important}
.st-key-sp_a_esenzioni button{background:linear-gradient(135deg,#8d6e63,#4e342e) !important}
.st-key-sp_a_scorte button{background:linear-gradient(135deg,#66bb6a,#1b5e20) !important}
.st-key-sp_a_tutto button{background:linear-gradient(135deg,#78909c,#37474f) !important}
.st-key-sp_azioni > div:nth-child(odd):last-child,.st-key-sp_azioni [data-testid='stVerticalBlock'] > div:nth-child(odd):last-child{grid-column:1 / -1}
.sp-card{background:rgba(255,255,255,.88);border-radius:16px;padding:10px 14px;margin:8px 0;color:#1b2b2b}
.sp-alert{background:#ffebee;border:2px solid #c62828;border-radius:16px;padding:10px 14px;margin:8px 0;color:#7f0000;font-weight:700}
</style>"""


# ---------------------------------------------------------------------------------------------------------------------
# utilità
# ---------------------------------------------------------------------------------------------------------------------
def _sp_oggi():
    return oggi() if "oggi" in globals() else date.today()


def _sp_data_it(iso):
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%d/%m/%Y") if iso else ""
    except ValueError:
        return str(iso or "")


def _sp_profilo(f, pid):
    return next((p for p in _fa_profili(f) if p["id"] == pid), {})


def _sp_salva_profilo(pid, fn, msg):
    def _m(f):
        for p in f["profili"]:
            if p["id"] == pid:
                fn(p)
    _fa_salva(_m, msg)


def _sp_eta(nascita, rif=None):
    """(anni, mesi) oppure None."""
    try:
        n = date.fromisoformat(str(nascita)[:10])
    except (ValueError, TypeError):
        return None
    r = rif or _sp_oggi()
    mesi = (r.year - n.year) * 12 + (r.month - n.month) - (1 if r.day < n.day else 0)
    return max(mesi, 0) // 12, max(mesi, 0) % 12


def _sp_e_bambino(p):
    sp = p.get("sp") or {}
    if sp.get("bambino") is not None:
        return bool(sp.get("bambino"))
    e = _sp_eta(sp.get("nascita"))
    return bool(e and e[0] < 14)


def _sp_righe(testo):
    return [x.strip(" -•\t") for x in str(testo or "").splitlines() if x.strip(" -•\t")]


def _sp_e(x):
    return _h.escape(str(x or ""))


def _sp_num(v):
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _sp_fmt_num(v):
    n = _sp_num(v)
    return "" if n is None else (f"{n:g}".replace(".", ","))


def _sp_dati_file(ref):
    try:
        d = carica_dati(crea_archivio(), _fa_percorso_doc(ref["id"]))
        return base64.b64decode(d["b64"]) if d.get("b64") else b""
    except Exception:
        return b""


def _sp_mostra(ref):
    dati = _sp_dati_file(ref)
    if not dati:
        st.error("Non trovo questo file.")
        return
    mime = ref.get("mime") or "application/octet-stream"
    if "_ca_anteprima" in globals():
        _ca_anteprima(ref.get("nome"), mime, dati)
    elif mime.startswith("image/"):
        st.image(dati, width="stretch")
    st.download_button("⬇ Scarica", dati, file_name=ref.get("nome") or "documento", mime=mime, key=f"sp_dl_{ref['id']}", width="stretch")


# ---------------------------------------------------------------------------------------------------------------------
# 1) TESSERA SANITARIA E FASCICOLO: ora con i documenti scaricati
# ---------------------------------------------------------------------------------------------------------------------
def _sp_dialogo_togli_file(pid, chiave, ref):
    def _finestra():
        st.warning(f"Togliere questo documento?\n\n**{_sp_e(ref.get('nome'))}**")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"sp_ftogli_si_{ref['id']}", type="primary", width="stretch"):
            def _fn(p):
                fv = dict(p.get("file_voce") or {})
                fv[chiave] = [r for r in fv.get(chiave, []) if r.get("id") != ref["id"]]
                p["file_voce"] = fv
            _sp_salva_profilo(pid, _fn, "Salute: documento tolto")
            _fa_cancella_files([ref["id"]])
            st.session_state["fa_msg"] = "🗑️ Documento tolto."
            st.rerun()
        if s2.button("No, tienilo", key=f"sp_ftogli_no_{ref['id']}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina il documento")(_finestra)()


def _sp_file_voce(pid, chiave, titolo):
    """Sotto ciascuna delle tre voci: carica il documento già scaricato, vedilo, scaricalo, invialo."""
    f = _fa_dati()
    p = _sp_profilo(f, pid)
    refs = list((p.get("file_voce") or {}).get(chiave, []))
    giro = st.session_state.get(f"sp_giro_{chiave}_{pid}", 0)
    with st.expander(f"📎 Il documento scaricato ({len(refs)})", expanded=bool(refs)):
        if not refs:
            st.caption("Hai già scaricato questo documento dal sito (PDF) o ne hai una foto? Caricalo qui: poi lo vedi, lo scarichi e lo invii quando serve.")
        vedi = st.session_state.setdefault("sp_vedi", [])
        for r in refs:
            st.markdown(f"<div class='sp-card'><b>📄 {_sp_e(r.get('nome'))}</b></div>", unsafe_allow_html=True)
            b1, b2 = st.columns(2, gap="small")
            aperto = r["id"] in vedi
            if b1.button("🙈 Chiudi" if aperto else "👁️ Vedi / scarica", key=f"sp_v_{r['id']}", width="stretch"):
                vedi.remove(r["id"]) if aperto else vedi.append(r["id"])
                st.rerun()
            if b2.button("🗑️ Elimina", key=f"sp_t_{r['id']}", width="stretch"):
                _sp_dialogo_togli_file(pid, chiave, r)
            if aperto:
                _sp_mostra(r)
        nuovi = st.file_uploader("Carica il documento (PDF o foto)", type=TIPI_FILE, accept_multiple_files=True, key=f"sp_up_{chiave}_{pid}_{giro}")
        if nuovi and st.button("💾 Salva il documento", key=f"sp_salva_{chiave}_{pid}", type="primary", width="stretch"):
            try:
                nuovi_refs = _fa_salva_files(nuovi, esistenti=refs)
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare: {ex}")
            else:
                def _fn(pr, nr=nuovi_refs):
                    fv = dict(pr.get("file_voce") or {})
                    fv[chiave] = list(fv.get(chiave, [])) + nr
                    pr["file_voce"] = fv
                _sp_salva_profilo(pid, _fn, "Salute: documento allegato")
                st.session_state[f"sp_giro_{chiave}_{pid}"] = giro + 1
                st.session_state["fa_msg"] = "✅ Documento salvato." if nuovi_refs else "ℹ️ Era già salvato: non l'ho duplicato."
                st.rerun()
        if refs:
            _fa_inv_voce(f"sp_voce_{chiave}_{pid}", "📤 Invia questi documenti", f"{titolo} di {p.get('nome', '')}", [], refs)


def _sp_modulo_tessera(pid):
    """Come la pagina «Tessera sanitaria e fascicolo» di prima, con in più i documenti caricabili sotto ogni voce."""
    _fa_ctx("farmacia:tessera")
    f = _fa_dati()
    profilo = _sp_profilo(f, pid) or _fa_profili(f)[0]
    link = profilo.get("link_sanitari") or {}
    if st.button("← Torna a Salute", key="fa_ts_indietro"):
        st.session_state.pop("fa_modulo_tessera", None)
        st.rerun()
    st.subheader(f"🪪 Tessera sanitaria e fascicolo · {profilo.get('nome', '')}")
    st.markdown("### 🪪 La mia tessera sanitaria")
    doc, allegati = _fa_tessera_del_profilo(f, pid)
    if allegati:
        if st.button("👁️ Mostra fronte e retro della tessera", type="primary", key="fa_ts_mostra", width="stretch"):
            _fa_dialogo_tessera(pid)
    else:
        if doc:
            st.warning("📌 Hai inserito il documento «Tessera sanitaria» ma senza foto. Aprilo in I miei documenti, tocca Modifica e aggiungi la foto del **fronte** e del **retro**.")
        else:
            st.warning("📌 Non hai ancora inserito la tessera sanitaria. Vai in **I miei documenti**, tocca **➕ Aggiungi un documento**, scegli **Tessera sanitaria** e fai la foto del fronte e del retro.")
        if st.button("📁 Vai a I miei documenti", key="fa_ts_vai_doc", width="stretch"):
            st.session_state.pop("fa_modulo_tessera", None)
            st.session_state["fa_profilo"] = pid
            st.session_state["sezione_home"] = "documenti"
            st.rerun()
    if allegati:
        _fa_tessera_invio(f, pid, allegati)
    st.markdown("### 🔗 I miei collegamenti e i miei documenti")
    st.caption("Per ogni voce: il **link** della pagina (da salvare una volta) e, sotto, il **documento già scaricato** (PDF o foto) da caricare, vedere, scaricare e inviare.")
    with st.expander("❓ Come copio il link di una pagina?"):
        st.markdown("1. Apri la pagina nel browser (per esempio dal sito della tua Regione).\n2. Tocca la **barra dell'indirizzo** in alto: il testo si seleziona tutto.\n"
                    "3. Tocca **Copia**.\n4. Torna qui, tocca il campo e scegli **Incolla**.\n5. Tocca **💾 Salva**.")
    campi = (("fse", "📂 Il mio fascicolo sanitario elettronico", "🔗 Apri il mio fascicolo sanitario", "Fascicolo sanitario elettronico"),
             ("vaccini", "💉 Le mie vaccinazioni online", "🔗 Apri le mie vaccinazioni", "Vaccinazioni"),
             ("spese", "🧾 Le mie spese sanitarie detraibili", "🔗 Apri le mie spese sanitarie", "Spese sanitarie detraibili"))
    for chiave, titolo, pulsante, nome_doc in campi:
        url = (link.get(chiave) or "").strip()
        k_mod = f"fa_ts_mod_{chiave}_{pid}"
        st.markdown(f"**{titolo}**")
        if url and not st.session_state.get(k_mod):
            c1, c2 = st.columns([3, 1.4], gap="small")
            c1.link_button(pulsante, url, type="primary", width="stretch")
            if c2.button("✏️ Modifica", key=f"fa_ts_btnmod_{chiave}_{pid}", width="stretch"):
                st.session_state[k_mod] = True
                st.rerun()
            _fa_inv_voce(f"sp_lnk_{chiave}_{pid}", "📤 Invia il link", f"{nome_doc} di {profilo.get('nome', '')}", [("Collegamento", url)], [])
        else:
            with st.form(f"fa_ts_form_{chiave}_{pid}"):
                nuovo = st.text_input(titolo, value=url, placeholder="incolla qui il link, per esempio https://…", label_visibility="collapsed")
                b1, b2 = st.columns(2)
                salva_b = b1.form_submit_button("💾 Salva il link", type="primary", width="stretch")
                togli_b = b2.form_submit_button("🗑️ Elimina il link" if url else "Annulla", width="stretch")
            if salva_b:
                valido = _fa_url_valido(nuovo)
                if valido is None:
                    st.error("Il link non sembra corretto: copialo per intero dalla barra dell'indirizzo (di solito comincia con https://).")
                elif not valido:
                    st.error("Il campo è vuoto: incolla il link e tocca Salva.")
                else:
                    try:
                        _fa_salva_link(pid, chiave, valido)
                    except Exception as ex:
                        st.error(f"Non sono riuscito a salvare: {ex}")
                    else:
                        st.session_state.pop(k_mod, None)
                        st.session_state["fa_msg"] = "✅ Collegamento salvato."
                        st.rerun()
            elif togli_b:
                if url:
                    try:
                        _fa_salva_link(pid, chiave, "")
                    except Exception as ex:
                        st.error(f"Non sono riuscito a toglierlo: {ex}")
                    else:
                        st.session_state["fa_msg"] = "🗑️ Collegamento tolto."
                st.session_state.pop(k_mod, None)
                st.rerun()
        _sp_file_voce(pid, chiave, nome_doc)
        st.divider()


# ---------------------------------------------------------------------------------------------------------------------
# la riga dei pulsanti sotto i tre riquadri, e le pagine nuove
# ---------------------------------------------------------------------------------------------------------------------
def sp_riga_azioni(pid):
    f = _fa_dati()
    p = _sp_profilo(f, pid)
    st.markdown(_SP_CSS, unsafe_allow_html=True)
    with st.container(key="sp_azioni"):
        a = st.button("👩‍⚕️ Medici e riferimenti", key="sp_a_medici", width="stretch")
        b = st.button("🆘 Dati per l'emergenza", key="sp_a_critici", width="stretch")
        c = st.button("📄 Scheda per il medico", key="sp_a_scheda", width="stretch")
        d = st.button("👶 Percorso del bambino", key="sp_a_bambino", width="stretch") if _sp_e_bambino(p) else False
        e = st.button("🗂️ Documenti sanitari", key="sp_a_docsan", width="stretch")
        g = st.button("📈 Parametri e valori", key="sp_a_param", width="stretch")
        n_c = len(sp_controlli_scadenti(p))
        h = st.button("⏰ Controlli periodici" + (f" · {n_c} da fare" if n_c else ""), key="sp_a_controlli", width="stretch")
        n_e = len(sp_esenzioni_scadenti(p)) if "sp_esenzioni_scadenti" in globals() else 0
        i_ = st.button("🪪 Invalidità ed esenzioni" + (f" · {n_e} in scadenza" if n_e else ""), key="sp_a_esenzioni", width="stretch")
        try:
            n_s = scorta_n_esaurimento(f, pid) if "scorta_n_esaurimento" in globals() else 0
        except Exception:
            n_s = 0
        s_ = st.button("💊 Scorte e rinnovo ricette" + (f" · {n_s} in esaurimento" if n_s else ""), key="sp_a_scorte", width="stretch") if "scorta_pagina" in globals() else False
        j_ = st.button("📋 Tutti i dati e documenti", key="sp_a_tutto", width="stretch")
    for premuto, vista in ((a, "medici"), (b, "critici"), (c, "scheda"), (d, "bambino"), (e, "docsan"), (g, "parametri"), (h, "controlli"), (i_, "esenzioni"), (s_, "scorte"), (j_, "tutto")):
        if premuto:
            st.session_state["sp_modulo"] = {"vista": vista, "pid": pid}
            st.rerun()


def _sp_intestazione(titolo, pid):
    f = _fa_dati()
    p = _sp_profilo(f, pid)
    st.markdown(_SP_CSS, unsafe_allow_html=True)
    if st.button("← Torna a Salute", key="sp_indietro"):
        st.session_state.pop("sp_modulo", None)
        st.rerun()
    st.subheader(f"{titolo} · {p.get('nome', '')}")
    return f, p


def _sp_dispatch(m):
    vista, pid = m.get("vista"), m.get("pid")
    {"medici": sp_modulo_medici, "critici": sp_modulo_critici, "scheda": sp_modulo_scheda, "bambino": sp_modulo_bambino, "docsan": sp_modulo_docsan, "parametri": sp_modulo_parametri, "controlli": sp_modulo_controlli, "esenzioni": globals().get("sp_modulo_esenzioni"), "scorte": globals().get("scorta_pagina"), "tutto": globals().get("stt_pagina")}.get(vista, lambda _p: None)(pid)


# ---------------------------------------------------------------------------------------------------------------------
# 2) MEDICI E RIFERIMENTI (pediatra compreso)
# ---------------------------------------------------------------------------------------------------------------------
def _sp_dialogo_togli_medico(pid, mid, nome):
    def _finestra():
        st.warning(f"Togliere dalla rubrica **{_sp_e(nome)}**?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"sp_mtogli_si_{mid}", type="primary", width="stretch"):
            _sp_salva_profilo(pid, lambda p: p.__setitem__("medici", [m for m in p.get("medici", []) if m.get("id") != mid]), "Salute: medico tolto")
            st.session_state["fa_msg"] = "🗑️ Tolto dalla rubrica."
            st.rerun()
        if s2.button("No, tienilo", key=f"sp_mtogli_no_{mid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina dalla rubrica")(_finestra)()


def _sp_form_medico(pid, m=None):
    m = m or {}
    with st.form(f"sp_form_medico_{m.get('id', 'nuovo')}", border=False):
        ruolo = st.selectbox("Chi è", _SP_RUOLI_MEDICO, index=_SP_RUOLI_MEDICO.index(m.get("ruolo")) if m.get("ruolo") in _SP_RUOLI_MEDICO else 0)
        spec = st.text_input("Specialità (se è uno specialista)", value=m.get("spec", ""), placeholder="es. cardiologo, oculista")
        nome = st.text_input("Nome e cognome", value=m.get("nome", ""))
        struttura = st.text_input("Studio, ambulatorio o ospedale", value=m.get("struttura", ""))
        c1, c2 = st.columns(2)
        tel = c1.text_input("Telefono", value=m.get("telefono", ""))
        email = c2.text_input("Email", value=m.get("email", ""))
        ind = st.text_input("Indirizzo", value=m.get("indirizzo", ""))
        orari = st.text_area("Orari di ricevimento", value=m.get("orari", ""), height=80, placeholder="es. lun-ven 9-12; mar e gio anche 15-18")
        sost = st.text_input("Sostituto (se c'è)", value=m.get("sostituto", ""))
        note = st.text_input("Note", value=m.get("note", ""))
        ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
    if ok:
        if not (nome.strip() or struttura.strip()):
            st.error("Scrivi almeno il nome o lo studio.")
            return
        nuovo = {"id": m.get("id") or uuid.uuid4().hex[:8], "ruolo": ruolo, "spec": spec.strip(), "nome": nome.strip(), "struttura": struttura.strip(), "telefono": tel.strip(),
                 "email": email.strip(), "indirizzo": ind.strip(), "orari": orari.strip(), "sostituto": sost.strip(), "note": note.strip()}

        def _fn(p):
            lista = [x for x in p.get("medici", []) if x.get("id") != nuovo["id"]]
            p["medici"] = lista + [nuovo]
        _sp_salva_profilo(pid, _fn, "Salute: medico")
        st.session_state.pop("sp_med_mod", None)
        st.session_state["fa_msg"] = "✅ Salvato."
        st.rerun()


def sp_modulo_medici(pid):
    f, p = _sp_intestazione("👩‍⚕️ Medici e riferimenti", pid)
    dott = p.get("dottore") or {}
    st.markdown("**Il medico di base** (la sua scheda completa, con orari e sostituto, è quella di prima)")
    resumo = " · ".join(x for x in (dott.get("nome"), dott.get("telefono")) if x)
    st.markdown(f"<div class='sp-card'>{_sp_e(resumo) or '<i>non ancora inserito</i>'}</div>", unsafe_allow_html=True)
    if st.button("🩺 Apri la scheda del medico di base", key="sp_apri_dottore", width="stretch"):
        st.session_state.pop("sp_modulo", None)
        st.session_state["fa_modulo_dottore"] = {"pid": pid}
        st.rerun()
    st.divider()
    st.markdown("**Pediatra, specialisti e altri riferimenti**")
    if _sp_e_bambino(p) and not any(x.get("ruolo") == "Pediatra" for x in p.get("medici", [])):
        st.info("👶 Questo profilo è un bambino: aggiungi qui il **pediatra**.")
    lista = p.get("medici", [])
    for m in sorted(lista, key=lambda x: (_SP_RUOLI_MEDICO.index(x["ruolo"]) if x.get("ruolo") in _SP_RUOLI_MEDICO else 99, x.get("nome", ""))):
        icona = "👶🩺" if m.get("ruolo") == "Pediatra" else "👩‍⚕️"
        titolo = f"{icona} {m.get('ruolo', '')}" + (f" · {m['spec']}" if m.get("spec") else "") + f" — {m.get('nome') or m.get('struttura', '')}"
        righe = "<br>".join(x for x in (_sp_e(m.get("struttura")), "📞 " + _sp_e(m.get("telefono")) if m.get("telefono") else "", "✉️ " + _sp_e(m.get("email")) if m.get("email") else "",
                                        "📍 " + _sp_e(m.get("indirizzo")) if m.get("indirizzo") else "", "🕒 " + _sp_e(m.get("orari")).replace("\n", "; ") if m.get("orari") else "",
                                        "Sostituto: " + _sp_e(m.get("sostituto")) if m.get("sostituto") else "", _sp_e(m.get("note"))) if x)
        st.markdown(f"<div class='sp-card'><b>{_sp_e(titolo)}</b><br>{righe}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="small")
        if m.get("telefono"):
            c1.link_button("📞 Chiama", "tel:" + _fa_tel(m["telefono"]), width="stretch")
        if m.get("email"):
            c2.link_button("✉️ Scrivi", "mailto:" + m["email"], width="stretch")
        if c3.button("✏️ Modifica", key=f"sp_med_e_{m['id']}", width="stretch"):
            st.session_state["sp_med_mod"] = m["id"]
            st.rerun()
        d1, d2 = st.columns(2, gap="small")
        if d1.button("🗑️ Elimina", key=f"sp_med_t_{m['id']}", width="stretch"):
            _sp_dialogo_togli_medico(pid, m["id"], m.get("nome") or m.get("struttura") or "questo riferimento")
        with d2:
            _fa_inv_voce(f"sp_med_{m['id']}", "📤 Invia", f"{m.get('ruolo', '')} di {p.get('nome', '')}",
                         [("Nome", m.get("nome")), ("Studio", m.get("struttura")), ("Telefono", m.get("telefono")), ("Email", m.get("email")), ("Indirizzo", m.get("indirizzo")), ("Orari", m.get("orari"))], [])
        if st.session_state.get("sp_med_mod") == m["id"]:
            _sp_form_medico(pid, m)
    with st.expander("➕ Aggiungi un riferimento (pediatra, specialista, dentista…)", expanded=not lista):
        _sp_form_medico(pid)


# ---------------------------------------------------------------------------------------------------------------------
# 3) DATI PER L'EMERGENZA
# ---------------------------------------------------------------------------------------------------------------------
def sp_modulo_critici(pid):
    f, p = _sp_intestazione("🆘 Dati per l'emergenza", pid)
    sp = dict(p.get("sp") or {})
    st.caption("Sono le cose che un medico deve sapere subito, anche se non conosce la persona. Compila quello che sai: tutto è facoltativo e modificabile.")
    san_allergie = (f.get("allergie") or {}).get(pid, [])
    st.markdown(f"💊 **Allergie ai farmaci** (si modificano nella **Scheda sanitaria**): {_sp_e(', '.join(san_allergie)) or '— nessuna dichiarata —'}")
    with st.form("sp_form_critici", border=False):
        c1, c2 = st.columns(2)
        nascita = c1.date_input("Data di nascita", value=(date.fromisoformat(sp["nascita"]) if sp.get("nascita") else None), min_value=date(1900, 1, 1), max_value=_sp_oggi(), format="DD/MM/YYYY")
        sesso = c2.selectbox("Sesso", ["", "Femmina", "Maschio", "Altro"], index=["", "Femmina", "Maschio", "Altro"].index(sp.get("sesso", "")) if sp.get("sesso", "") in ["", "Femmina", "Maschio", "Altro"] else 0,
                             format_func=lambda x: "— non indicato —" if not x else x)
        c3, c4 = st.columns(2)
        altezza = c3.text_input("Altezza (cm)", value=sp.get("altezza", ""), placeholder="es. 172")
        peso = c4.text_input("Peso (kg)", value=sp.get("peso", ""), placeholder="es. 68")
        bambino = st.checkbox("👶 È un bambino o una bambina (apre il «Percorso del bambino»)", value=_sp_e_bambino(p))
        dispositivi = st.multiselect("❤️ Impianti, protesi e dispositivi che porta", _SP_DISPOSITIVI, default=[x for x in sp.get("dispositivi", []) if x in _SP_DISPOSITIVI])
        disp_altro = st.text_input("Altri impianti o dispositivi (con l'anno, se lo sai)", value=sp.get("dispositivi_altro", ""), placeholder="es. bypass triplo nel 2019")
        terapie = st.multiselect("💊 Terapie importanti in corso", _SP_TERAPIE_CRITICHE, default=[x for x in sp.get("terapie_critiche", []) if x in _SP_TERAPIE_CRITICHE])
        nessuna = st.checkbox("Nessuna allergia nota", value=bool(sp.get("nessuna_allergia")))
        all_alt = st.multiselect("🌾 Altre allergie", _SP_ALLERGIE_ALTRE, default=[x for x in sp.get("allergie_altre", []) if x in _SP_ALLERGIE_ALTRE])
        all_cibi = st.text_input("Allergie o intolleranze alimentari", value=sp.get("allergie_cibi", ""), placeholder="es. arachidi, lattosio, glutine (celiachia)")
        cond = st.multiselect("📌 Condizioni particolari", _SP_CONDIZIONI, default=[x for x in sp.get("condizioni", []) if x in _SP_CONDIZIONI])
        st.markdown("**📞 Chi chiamare in caso di emergenza**")
        contatti = list(sp.get("contatti") or [])
        contatti = (contatti + [{}, {}])[:2]
        nuovi_c = []
        for i, ct in enumerate(contatti):
            k1, k2, k3 = st.columns([2, 1.4, 1.6])
            n_ = k1.text_input(f"Nome {i + 1}", value=ct.get("nome", ""), key=f"sp_c_n{i}")
            r_ = k2.text_input(f"Chi è {i + 1}", value=ct.get("parentela", ""), key=f"sp_c_r{i}", placeholder="es. marito")
            t_ = k3.text_input(f"Telefono {i + 1}", value=ct.get("telefono", ""), key=f"sp_c_t{i}")
            nuovi_c.append({"nome": n_.strip(), "parentela": r_.strip(), "telefono": t_.strip()})
        note = st.text_area("Altre cose importanti da sapere", value=sp.get("note", ""), height=90, placeholder="es. soffre di crisi epilettiche; non parla italiano; pesa poco…")
        ok = st.form_submit_button("💾 Salva i dati per l'emergenza", type="primary", width="stretch")
    if ok:
        sp.update({"nascita": nascita.isoformat() if nascita else "", "sesso": sesso, "altezza": altezza.strip(), "peso": peso.strip(), "bambino": bool(bambino), "dispositivi": dispositivi,
                   "dispositivi_altro": disp_altro.strip(), "terapie_critiche": terapie, "nessuna_allergia": bool(nessuna), "allergie_altre": all_alt, "allergie_cibi": all_cibi.strip(),
                   "condizioni": cond, "contatti": [c for c in nuovi_c if c["nome"] or c["telefono"]], "note": note.strip()})
        _sp_salva_profilo(pid, lambda pr: pr.__setitem__("sp", sp), "Salute: dati per l'emergenza")
        st.session_state["fa_msg"] = "✅ Dati salvati."
        st.rerun()
    st.markdown("---")
    if st.button("📄 Vedi la scheda per il medico", key="sp_vai_scheda", type="primary", width="stretch"):
        st.session_state["sp_modulo"] = {"vista": "scheda", "pid": pid}
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 4) LA SCHEDA PER IL MEDICO: si compone da sola, si aggiorna da sola
# ---------------------------------------------------------------------------------------------------------------------
def sp_raccogli(f, pid, oggi_=None):
    """Tutto ciò che l'app sa di una persona, ordinato per la scheda. Funzione pura: lavora sul dizionario della Salute."""
    oggi_ = oggi_ or _sp_oggi()
    p = next((x for x in (f.get("profili") or [{"id": "p0", "nome": ""}]) if x["id"] == pid), {"id": pid, "nome": ""})
    sp, san, dott = p.get("sp") or {}, p.get("sanitario") or {}, p.get("dottore") or {}
    eta = _sp_eta(sp.get("nascita"), oggi_)
    vacc = sorted([v for v in f.get("vaccinazioni", []) if v.get("profilo", "p0") == pid], key=lambda v: v.get("data", ""), reverse=True)
    vis = sorted([v for v in f.get("visite", []) if v.get("profilo", "p0") == pid], key=lambda v: v.get("data", ""), reverse=True)
    ter = [t for t in f.get("terapie", []) if t.get("profilo", "p0") == pid and t.get("stato", "attiva") == "attiva"]
    medici = []
    if dott.get("nome") or dott.get("telefono"):
        medici.append({"ruolo": "Medico di base", "nome": dott.get("nome", ""), "telefono": dott.get("telefono", ""), "email": dott.get("email", ""), "struttura": ""})
    medici += [dict(m) for m in p.get("medici", [])]
    try:
        terapie = [{"nome": _fa_nome_med(f, t.get("med"), t.get("nome_med", "")), "quantita": t.get("quantita", ""), "orari": ", ".join(t.get("orari", []))} for t in ter]
    except Exception:
        terapie = []
    return {"id": pid, "nome": p.get("nome", ""), "nascita": sp.get("nascita", ""), "eta": eta, "sesso": sp.get("sesso", ""), "gruppo": p.get("gruppo") or "", "altezza": sp.get("altezza", ""),
            "peso": sp.get("peso", ""), "bambino": _sp_e_bambino(p), "allergie_farmaci": list((f.get("allergie") or {}).get(pid, [])), "nessuna_allergia": bool(sp.get("nessuna_allergia")),
            "allergie_altre": list(sp.get("allergie_altre", [])), "allergie_cibi": sp.get("allergie_cibi", ""), "dispositivi": list(sp.get("dispositivi", [])) + ([sp["dispositivi_altro"]] if sp.get("dispositivi_altro") else []),
            "terapie_critiche": list(sp.get("terapie_critiche", [])), "condizioni": list(sp.get("condizioni", [])), "contatti": list(sp.get("contatti", [])), "note": sp.get("note", ""),
            "patologie": _sp_righe(san.get("patologie")), "interventi": _sp_righe(san.get("interventi")), "storia": san.get("storia", ""), "famiglia": san.get("famiglia", ""), "altro": san.get("altro", ""),
            "terapie": terapie, "vaccini": [{"nome": v.get("nome", ""), "data": v.get("data", ""), "dose": v.get("dose", ""), "richiamo": v.get("richiamo", "")} for v in vacc],
            "visite": [{"data": v.get("data", ""), "categoria": v.get("categoria", ""), "medico": v.get("medico", "")} for v in vis[:8]], "medici": medici,
            "bambino_dati": p.get("bambino") or {}, "oggi": oggi_.isoformat(),
            "parametri": [{"nome": n, "unita": u, "data": d_, "valore": v_} for n, u, d_, v_ in sp_ultimi_parametri(p)],
            "docsan": [{"tipo": x.get("tipo", ""), "data": x.get("data", ""), "titolo": x.get("titolo", ""), "struttura": x.get("struttura", "")} for x in sorted(p.get("docsan", []), key=lambda x: x.get("data", ""), reverse=True)[:12]]}


def sp_avvisi(d):
    """Le righe «da sapere subito» in cima alla scheda."""
    out = []
    all_ = list(d["allergie_farmaci"]) + list(d["allergie_altre"]) + ([d["allergie_cibi"]] if d["allergie_cibi"] else [])
    if all_:
        out.append("⚠️ ALLERGIE: " + ", ".join(all_))
    if d["dispositivi"]:
        out.append("❤️ IMPIANTI E DISPOSITIVI: " + ", ".join(d["dispositivi"]))
    if d["terapie_critiche"]:
        out.append("💊 TERAPIE IMPORTANTI: " + ", ".join(d["terapie_critiche"]))
    cond = [c for c in d["condizioni"] if c in ("Gravidanza", "Allattamento", "Non può ricevere trasfusioni")]
    if cond:
        out.append("📌 " + ", ".join(cond).upper())
    return out


def sp_mancanti(d):
    """Cosa manca per rendere la scheda davvero utile a un medico che non conosce la persona."""
    m = []
    if not d["nascita"]:
        m.append(("Data di nascita", "critici"))
    if not d["gruppo"]:
        m.append(("Gruppo sanguigno", "scheda_sanitaria"))
    if not (d["allergie_farmaci"] or d["allergie_altre"] or d["allergie_cibi"] or d["nessuna_allergia"]):
        m.append(("Allergie: scrivile oppure spunta «Nessuna allergia nota»", "critici"))
    if not d["contatti"]:
        m.append(("Contatto di emergenza", "critici"))
    if not any(x.get("ruolo") == "Medico di base" for x in d["medici"]) and not (d["bambino"] and any(x.get("ruolo") == "Pediatra" for x in d["medici"])):
        m.append(("Il medico di base" + (" o il pediatra" if d["bambino"] else ""), "medici"))
    if not (d["patologie"] or d["interventi"] or d["storia"]):
        m.append(("Patologie, interventi o storia clinica (anche solo «nessuno»)", "scheda_sanitaria"))
    if d["bambino"] and not d["vaccini"]:
        m.append(("Vaccinazioni del bambino", "vaccini"))
    return m


def _sp_sesso_txt(d):
    return {"Femmina": ("donna", "nata"), "Maschio": ("uomo", "nato")}.get(d["sesso"], ("persona", "nata/o"))


def sp_racconto(d):
    """La sintesi scritta, SENZA intelligenza artificiale: solo i fatti inseriti, mai supposizioni."""
    sesso, nato = _sp_sesso_txt(d)
    if d["eta"] is not None:
        a, m = d["eta"]
        eta_txt = (f"{a} anni" if a >= 2 else f"{a * 12 + m} mesi")
        if d["bambino"] and 0 <= a < 2:
            sesso = "bambina" if d["sesso"] == "Femmina" else "bambino" if d["sesso"] == "Maschio" else "bambino/a"
        intro = f"{d['nome']} è {'una' if sesso in ('donna', 'persona', 'bambina') else 'un'} {sesso} di {eta_txt} ({nato} il {_sp_data_it(d['nascita'])})."
    else:
        intro = f"{d['nome']}: età non indicata."
    frasi = [intro]
    if d["gruppo"]:
        frasi.append(f"Gruppo sanguigno {d['gruppo']}.")
    mis = [x for x in ((f"altezza {d['altezza']} cm" if d["altezza"] else ""), (f"peso {d['peso']} kg" if d["peso"] else "")) if x]
    if mis:
        frasi.append("Misure riferite: " + ", ".join(mis) + ".")
    all_ = list(d["allergie_farmaci"]) + list(d["allergie_altre"]) + ([d["allergie_cibi"]] if d["allergie_cibi"] else [])
    frasi.append(("Allergie o intolleranze dichiarate: " + ", ".join(all_) + ".") if all_ else ("Nessuna allergia nota (dichiarato)." if d["nessuna_allergia"] else "Allergie: non indicate."))
    if d["dispositivi"]:
        frasi.append("Porta: " + ", ".join(d["dispositivi"]) + ".")
    if d["terapie_critiche"]:
        frasi.append("Terapie importanti: " + ", ".join(d["terapie_critiche"]) + ".")
    if d["patologie"]:
        frasi.append("Patologie: " + "; ".join(d["patologie"]) + ".")
    if d["interventi"]:
        frasi.append("Interventi subiti: " + "; ".join(d["interventi"]) + ".")
    if d["storia"]:
        frasi.append("Storia clinica di rilievo: " + re.sub(r"\s+", " ", d["storia"]).strip() + (" " if not d["storia"].strip().endswith(".") else ""))
    if d["terapie"]:
        frasi.append("Terapie in corso: " + "; ".join(f"{t['nome']} ({t['quantita']})" if t["quantita"] else t["nome"] for t in d["terapie"]) + ".")
    if d["condizioni"]:
        frasi.append("Altre condizioni: " + ", ".join(d["condizioni"]) + ".")
    if d["famiglia"]:
        frasi.append("Familiarità: " + re.sub(r"\s+", " ", d["famiglia"]).strip() + ".")
    if d["visite"]:
        v = d["visite"][0]
        frasi.append(f"Ultima visita registrata: {v['categoria'] or 'visita'} del {_sp_data_it(v['data'])}" + (f" ({v['medico']})" if v["medico"] else "") + ".")
    if d["bambino"] and d["bambino_dati"].get("misure"):
        ms = sorted(d["bambino_dati"]["misure"], key=lambda x: x.get("data", ""))[-1]
        frasi.append("Ultime misure registrate (" + _sp_data_it(ms.get("data")) + "): " + ", ".join(x for x in ((f"peso {_sp_fmt_num(ms.get('peso'))} kg" if ms.get("peso") else ""),
                     (f"altezza {_sp_fmt_num(ms.get('altezza'))} cm" if ms.get("altezza") else ""), (f"circonferenza cranica {_sp_fmt_num(ms.get('cranio'))} cm" if ms.get("cranio") else "")) if x) + ".")
    return " ".join(x.strip() for x in frasi if x.strip())


_SP_STILE = ("body{font-family:Arial,sans-serif;margin:0;color:#111;font-size:11pt}h1{font-size:17pt;margin:0 0 4pt}h2{font-size:12pt;margin:12pt 0 3pt;border-bottom:1px solid #888}"
             ".al{border:2px solid #b71c1c;background:#ffebee;padding:6pt 9pt;margin:6pt 0;font-weight:bold;color:#7f0000}.box{background:#f1f1f1;padding:6pt 9pt}"
             ".nota{font-size:8.5pt;color:#444;margin-top:14pt}li{margin:1pt 0}")


def sp_html_scheda(d, racconto, racconto_ai=None):
    """La scheda per il medico, in HTML (da stampare, salvare come PDF o inviare)."""
    e = _sp_e
    def lis(xs, vuoto="<i>non indicato</i>"):
        return ("<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>") if xs else f"<p>{vuoto}</p>"
    avv = sp_avvisi(d)
    eta = f"{d['eta'][0]} anni" if d["eta"] is not None and d["eta"][0] >= 2 else (f"{d['eta'][0] * 12 + d['eta'][1]} mesi" if d["eta"] is not None else "")
    anag = " · ".join(x for x in (d["nome"], eta, ("nato/a il " + _sp_data_it(d["nascita"])) if d["nascita"] else "", d["sesso"], ("gruppo " + d["gruppo"]) if d["gruppo"] else "") if x)
    medici = lis([f"{m.get('ruolo', '')}: {m.get('nome', '')}" + (f" – {m['struttura']}" if m.get("struttura") else "") + (f" – tel. {m['telefono']}" if m.get("telefono") else "") + (f" – {m['email']}" if m.get("email") else "")
                  for m in d["medici"]])
    contatti = lis([f"{c.get('nome', '')} ({c.get('parentela', '')}) – tel. {c.get('telefono', '')}" for c in d["contatti"]])
    vacc = lis([f"{v['nome']} – {_sp_data_it(v['data'])}" + (f" ({v['dose']})" if v["dose"] else "") + (f" – richiamo {_sp_data_it(v['richiamo'])}" if v["richiamo"] else "") for v in d["vaccini"]], "<i>nessuna registrata</i>")
    visite = lis([f"{_sp_data_it(v['data'])} – {v['categoria']}" + (f" ({v['medico']})" if v["medico"] else "") for v in d["visite"]], "<i>nessuna registrata</i>")
    terapie = lis([f"{t['nome']} – {t['quantita']}" + (f" – {t['orari']}" if t["orari"] else "") for t in d["terapie"]], "<i>nessuna</i>")
    ai = (f"<h2>Sintesi redatta con l'aiuto di un'intelligenza artificiale (da verificare)</h2><p>{e(racconto_ai['testo']).replace(chr(10), '<br>')}</p>") if racconto_ai and racconto_ai.get("testo") else ""
    baby = ""
    if d["bambino"] and d["bambino_dati"]:
        baby = "<h2>Percorso del bambino</h2>" + sp_html_bambino_corpo(d["bambino_dati"], d["sesso"], d["nascita"])
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Scheda per il medico – {e(d['nome'])}</title>"
            f"<style>{_SP_STILE}</style></head><body><h1>Scheda sanitaria per il medico</h1><div class='box'><b>{e(anag)}</b><br>Aggiornata il {_sp_data_it(d['oggi'])}</div>"
            + "".join(f"<div class='al'>{e(a)}</div>" for a in avv)
            + f"<h2>Racconto in breve</h2><p>{e(racconto)}</p>{ai}"
            f"<h2>Chi chiamare in caso di emergenza</h2>{contatti}<h2>Medici e riferimenti</h2>{medici}"
            f"<h2>Patologie</h2>{lis(d['patologie'])}<h2>Interventi subiti</h2>{lis(d['interventi'])}"
            f"<h2>Storia clinica di rilievo</h2><p>{e(d['storia']).replace(chr(10), '<br>') or '<i>non indicata</i>'}</p>"
            + (f"<h2>Familiarità</h2><p>{e(d['famiglia']).replace(chr(10), '<br>')}</p>" if d["famiglia"] else "")
            + f"<h2>Terapie in corso</h2>{terapie}<h2>Vaccinazioni</h2>{vacc}<h2>Ultime visite</h2>{visite}"
            + (("<h2>Ultimi valori registrati</h2>" + lis([f"{x['nome']}: {x['valore']} {x['unita']} ({_sp_data_it(x['data'])})" for x in d["parametri"]])) if d.get("parametri") else "")
            + (("<h2>Referti e documenti archiviati (ultimi)</h2>" + lis([f"{_sp_data_it(x['data'])} – {x['titolo']}" for x in d["docsan"]])) if d.get("docsan") else "")
            + (f"<h2>Altre informazioni</h2><p>{e(d['note'] + ' ' + d['altro']).strip()}</p>" if (d["note"] or d["altro"]) else "")
            + baby
            + "<p class='nota'>Documento creato dall'app «La nostra dispensa» con le informazioni inserite dall'utente: non è certificato da un medico e non sostituisce la documentazione clinica. "
              "Verificare i dati con l'interessato o con i documenti originali.</p></body></html>")


def sp_testo_scheda(d, racconto):
    avv = sp_avvisi(d)
    righe = [f"SCHEDA PER IL MEDICO – {d['nome']}", f"Aggiornata il {_sp_data_it(d['oggi'])}", ""] + avv + ([""] if avv else []) + [racconto, ""]
    if d["contatti"]:
        righe += ["Emergenza: " + "; ".join(f"{c.get('nome', '')} ({c.get('parentela', '')}) {c.get('telefono', '')}" for c in d["contatti"])]
    return "\n".join(righe)


def sp_pdf_da_html(html_str):
    """HTML → PDF con la libreria che c'è già (PyMuPDF). Ritorna i byte, o None se non riesce."""
    try:
        import pymupdf as fz
    except Exception:
        try:
            import fitz as fz
        except Exception:
            return None
    try:
        story = fz.Story(html=html_str, user_css="body{font-family:sans-serif}")
        buf = io.BytesIO()
        writer = fz.DocumentWriter(buf)
        mediabox = fz.paper_rect("a4")
        where = mediabox + (36, 36, -36, -36)
        piu = True
        while piu:
            dev = writer.begin_page(mediabox)
            piu, _ = story.place(where)
            story.draw(dev)
            writer.end_page()
        writer.close()
        return buf.getvalue()
    except Exception:
        return None


# --- facoltativo: sintesi scritta da un'intelligenza artificiale (con il consenso, senza dati che identificano la persona)
def sp_dati_anonimi(d):
    """I fatti clinici, SENZA nome, codice fiscale, telefoni, email, indirizzi, nomi dei medici e dei contatti."""
    rid = {"sesso": d["sesso"], "eta": (f"{d['eta'][0]} anni e {d['eta'][1]} mesi" if d["eta"] else ""), "gruppo_sanguigno": d["gruppo"], "altezza_cm": d["altezza"], "peso_kg": d["peso"],
           "allergie_farmaci": d["allergie_farmaci"], "allergie_altre": d["allergie_altre"], "allergie_cibi": d["allergie_cibi"], "nessuna_allergia_nota": d["nessuna_allergia"],
           "impianti_dispositivi": d["dispositivi"], "terapie_importanti": d["terapie_critiche"], "condizioni": d["condizioni"], "patologie": d["patologie"], "interventi": d["interventi"],
           "storia_clinica": d["storia"], "familiarita": d["famiglia"], "terapie_in_corso": [t["nome"] + " " + t["quantita"] for t in d["terapie"]],
           "vaccinazioni": [v["nome"] + " " + (v["data"][:4] if v["data"] else "") for v in d["vaccini"]], "altre_note": (d["note"] + " " + d["altro"]).strip()}
    testo = json.dumps(rid, ensure_ascii=False)
    testo = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", testo)
    testo = re.sub(r"(?<!\d)(\+?\d[\d\s/.-]{7,}\d)(?!\d)", "[numero]", testo)
    testo = re.sub(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", "[codice]", testo, flags=re.I)
    testo = re.sub(r"\b(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{14,34}\b", "[codice]", testo)           # qualsiasi sequenza lunga di lettere e cifre: codice fiscale, IBAN, tessera…
    if d["nome"]:
        for parte in d["nome"].split():
            if len(parte) > 2:
                testo = re.sub(re.escape(parte), "[nome]", testo, flags=re.I)
    return testo


_SP_AI_ISTRUZIONI = ("Sei un assistente che prepara per un medico che NON conosce il paziente una breve sintesi clinica, a partire SOLO dai fatti forniti in JSON, riferiti dall'utente. "
                     "Non fare diagnosi, non suggerire terapie o dosi, non aggiungere nessuna informazione che non sia nei dati, non dedurre malattie dai farmaci. Se un dato manca, scrivi «non indicato». "
                     "Scrivi in italiano, tono professionale e chiaro. Struttura: 1) «Sintesi» (4-7 righe) 2) «Punti di attenzione» (elenco breve: allergie, impianti, terapie importanti, condizioni) "
                     "3) «Cosa chiedere o verificare» (dati mancanti o da confermare con documenti originali). Massimo 250 parole. Niente titoli markdown, solo testo semplice.")


def sp_ai_sintesi(d):
    """Ritorna il testo oppure None (chiave assente, errore di rete…). Non fa mai fallire l'app."""
    if "ai_attivo" not in globals() or not ai_attivo():
        return None
    try:
        import requests
        r = requests.post(AI_URL, timeout=(5, 50), headers={"x-api-key": _ai_chiave(), "anthropic-version": "2023-06-01", "content-type": "application/json"},
                          json={"model": AI_MODELLO, "max_tokens": 700, "system": _SP_AI_ISTRUZIONI, "messages": [{"role": "user", "content": sp_dati_anonimi(d)[:6000]}]})
        if r.status_code != 200:
            return None
        t = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text").strip()
        return t or None
    except Exception:
        return None


def sp_impronta(d):
    base = {k: v for k, v in d.items() if k not in ("oggi",)}
    return hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def sp_modulo_scheda(pid):
    f, p = _sp_intestazione("📄 Scheda per il medico", pid)
    d = sp_raccogli(f, pid)
    racconto = sp_racconto(d)
    sp = p.get("sp") or {}
    ai_salvato = sp.get("racconto_ai") or {}
    ai_ok = bool(ai_salvato.get("testo"))
    for a in sp_avvisi(d):
        st.markdown(f"<div class='sp-alert'>{_sp_e(a)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sp-card'><b>Racconto in breve</b><br>{_sp_e(racconto)}</div>", unsafe_allow_html=True)
    if ai_ok:
        aggiornato = ai_salvato.get("hash") == sp_impronta(d)
        st.markdown(f"<div class='sp-card'><b>🤖 Sintesi con intelligenza artificiale</b> · del {_sp_data_it(ai_salvato.get('il'))}"
                    + ("" if aggiornato else " · <span style='color:#b71c1c'>i dati sono cambiati dopo: aggiornala</span>") + f"<br>{_sp_e(ai_salvato['testo']).replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
    mancanti = sp_mancanti(d)
    if mancanti:
        with st.expander(f"📝 Per rendere la scheda più utile ({len(mancanti)} cose)", expanded=True):
            for testo, dove in mancanti:
                st.markdown(f"- {testo}")
            c1, c2 = st.columns(2, gap="small")
            if c1.button("🆘 Compila i dati per l'emergenza", key="sp_vai_critici", width="stretch"):
                st.session_state["sp_modulo"] = {"vista": "critici", "pid": pid}
                st.rerun()
            if c2.button("📋 Apri la scheda sanitaria", key="sp_vai_san", width="stretch"):
                st.session_state.pop("sp_modulo", None)
                st.session_state["fa_modulo_sanitario"] = {"pid": pid}
                st.rerun()
    # ---- esportare e inviare
    html_str = sp_html_scheda(d, racconto, ai_salvato if ai_ok else None)
    nome_file = f"scheda_medico_{re.sub(r'[^A-Za-z0-9]+', '_', d['nome']) or 'persona'}_{d['oggi']}"
    st.download_button("📄 Scarica la scheda (da stampare o salvare come PDF)", html_str.encode("utf-8"), file_name=nome_file + ".html", mime="text/html", width="stretch")
    pdf = sp_pdf_da_html(html_str)
    if pdf:
        st.download_button("📕 Scarica il PDF", pdf, file_name=nome_file + ".pdf", mime="application/pdf", width="stretch")
    if "inv_voce" in globals():
        inv_voce(f"sp_scheda_{pid}", "📤 Invia la scheda (email, WhatsApp, Telegram…)", f"Scheda per il medico di {d['nome']}", sp_testo_scheda(d, racconto),
                 lambda: ([(nome_file + ".pdf", "application/pdf", pdf)] if pdf else [(nome_file + ".html", "text/html", html_str.encode("utf-8"))]))
    st.caption("Contiene dati sanitari: condividila solo con chi deve vederla. Le informazioni sono quelle inserite da te e non sono certificate da un medico.")
    # ---- facoltativo: intelligenza artificiale
    with st.expander("🤖 Sintesi più scorrevole con l'intelligenza artificiale (facoltativa)"):
        if "ai_attivo" not in globals() or not ai_attivo():
            st.info("Non è attiva: nei Secrets dell'app manca la chiave dell'assistente intelligente. La scheda funziona benissimo anche senza: è scritta dall'app, senza mandare dati fuori.")
        else:
            st.markdown("L'intelligenza artificiale riscrive i fatti già presenti in modo più scorrevole e segnala cosa manca. **Non fa diagnosi e non aggiunge niente.** "
                        "Se la usi, vengono inviati a un servizio esterno (Anthropic) **solo i dati clinici, senza nome, codice fiscale, telefoni, email e indirizzi**.")
            consenso = st.checkbox("Sì, per questa persona consento l'invio dei dati clinici (senza i dati che la identificano)", value=bool(sp.get("ai_consenso")), key=f"sp_ai_cons_{pid}")
            if consenso != bool(sp.get("ai_consenso")):
                _sp_salva_profilo(pid, lambda pr, c=consenso: pr.__setitem__("sp", dict(pr.get("sp") or {}, ai_consenso=bool(c))), "Salute: consenso alla sintesi")
                st.rerun()
            if consenso and st.button("🔄 Scrivi o aggiorna la sintesi", key=f"sp_ai_go_{pid}", type="primary", width="stretch"):
                with st.spinner("Preparo la sintesi…"):
                    testo = sp_ai_sintesi(d)
                if testo:
                    _sp_salva_profilo(pid, lambda pr, t=testo, h=sp_impronta(d): pr.__setitem__("sp", dict(pr.get("sp") or {}, racconto_ai={"testo": t, "il": _sp_oggi().isoformat(), "hash": h})), "Salute: sintesi")
                    st.rerun()
                else:
                    st.warning("Non sono riuscito a preparare la sintesi adesso (rete o limiti). La scheda qui sopra resta valida: riprova più tardi.")
            if ai_ok and st.button("🗑️ Elimina la sintesi salvata", key=f"sp_ai_via_{pid}", width="stretch"):
                _sp_salva_profilo(pid, lambda pr: pr.__setitem__("sp", {k: v for k, v in (pr.get("sp") or {}).items() if k != "racconto_ai"}), "Salute: sintesi tolta")
                st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 5) PERCORSO DEL BAMBINO
# ---------------------------------------------------------------------------------------------------------------------
def sp_html_bambino_corpo(b, sesso="", nascita=""):
    e = _sp_e
    def tab(titolo, righe, intest):
        if not righe:
            return ""
        return (f"<h3>{titolo}</h3><table border='1' cellpadding='3' cellspacing='0' style='border-collapse:collapse;width:100%'><tr>" + "".join(f"<th>{e(x)}</th>" for x in intest) + "</tr>"
                + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in righe) + "</table>")
    ms = sorted(b.get("misure", []), key=lambda x: x.get("data", ""))
    con_perc = bool(sesso in ("Femmina", "Maschio") and nascita and "sp_perc_testo" in globals())
    return (tab("Crescita", [[_sp_data_it(m.get("data")), _sp_fmt_num(m.get("peso")), _sp_fmt_num(m.get("altezza")), _sp_fmt_num(m.get("cranio")), m.get("nota", "")]
                             + ([sp_perc_testo(sesso, nascita, m.get("data"), m).replace("percentile ", "")] if con_perc else []) for m in ms],
                ["Data", "Peso kg", "Altezza cm", "Cranio cm", "Note"] + (["Percentili OMS"] if con_perc else []))
            + tab("Tappe", [[_sp_data_it(t.get("data")), t.get("tappa", ""), t.get("nota", "")] for t in sorted(b.get("tappe", []), key=lambda x: x.get("data", ""))], ["Quando", "Tappa", "Note"])
            + tab("Alimentazione", [[_sp_data_it(t.get("data")), t.get("cosa", ""), t.get("reazione", ""), t.get("nota", "")] for t in sorted(b.get("alimentazione", []), key=lambda x: x.get("data", ""))], ["Dal", "Cosa", "Reazioni", "Note"])
            + tab("Malattie e febbri", [[_sp_data_it(t.get("data")), t.get("cosa", ""), _sp_fmt_num(t.get("febbre")), t.get("terapia", ""), t.get("nota", "")] for t in sorted(b.get("malattie", []), key=lambda x: x.get("data", ""))],
                  ["Data", "Cosa", "Febbre °C", "Cure", "Note"])
            + tab("Denti", [[_sp_data_it(t.get("data")), t.get("cosa", ""), t.get("nota", "")] for t in sorted(b.get("denti", []), key=lambda x: x.get("data", ""))], ["Data", "Evento", "Note"])
            + tab("Ricoveri e interventi", [[_sp_data_it(t.get("data")), t.get("cosa", ""), t.get("dove", ""), t.get("nota", "")] for t in sorted(b.get("ricoveri", []), key=lambda x: x.get("data", ""))], ["Data", "Motivo", "Dove", "Note"])
            + (f"<h3>Note</h3><p>{e(b.get('note', ''))}</p>" if b.get("note") else ""))


_SP_SEZIONI_BAMBINO = {
    "misure": [("data", "Data", "date"), ("peso", "Peso (kg)", "num"), ("altezza", "Altezza o lunghezza (cm)", "num"), ("cranio", "Circonferenza cranica (cm)", "num"), ("nota", "Note", "text")],
    "tappe": [("tappa", "Tappa", "tappa"), ("data", "Quando", "date"), ("nota", "Note", "text")],
    "alimentazione": [("data", "Dal", "date"), ("cosa", "Cosa (latte materno o artificiale, pappa, nuovo alimento…)", "text"), ("reazione", "Reazioni o allergie", "text"), ("nota", "Note", "text")],
    "malattie": [("data", "Data", "date"), ("cosa", "Malattia o problema", "text"), ("febbre", "Febbre massima (°C)", "num"), ("terapia", "Cure fatte", "text"), ("nota", "Note", "text")],
    "denti": [("data", "Data", "date"), ("cosa", "Cosa è successo", "denti"), ("nota", "Note", "text")],
    "ricoveri": [("data", "Data", "date"), ("cosa", "Motivo", "text"), ("dove", "Dove", "text"), ("nota", "Note", "text")],
}


def _sp_riassunto_voce(sez, v, p=None):
    if sez == "misure":
        base = " · ".join(x for x in ((f"⚖️ {_sp_fmt_num(v.get('peso'))} kg" if v.get("peso") else ""), (f"📏 {_sp_fmt_num(v.get('altezza'))} cm" if v.get("altezza") else ""),
                                      (f"🧠 cranio {_sp_fmt_num(v.get('cranio'))} cm" if v.get("cranio") else "")) if x) or "—"
        if p is not None and (p.get("sp") or {}).get("nascita"):
            perc = sp_perc_testo((p.get("sp") or {}).get("sesso", ""), (p.get("sp") or {})["nascita"], v.get("data"), v)
            if perc:
                base += f" · 📊 {perc}"
        return base
    if sez == "tappe":
        return v.get("tappa", "")
    if sez == "malattie":
        return v.get("cosa", "") + (f" · febbre {_sp_fmt_num(v.get('febbre'))}°" if v.get("febbre") else "")
    return v.get("cosa", "")


def _sp_dialogo_togli_voce(pid, sez, vid, testo):
    def _finestra():
        st.warning(f"Togliere questa voce?\n\n**{_sp_e(testo)}**")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglila", key=f"sp_vt_si_{vid}", type="primary", width="stretch"):
            def _fn(p):
                b = dict(p.get("bambino") or {})
                b[sez] = [x for x in b.get(sez, []) if x.get("id") != vid]
                p["bambino"] = b
            _sp_salva_profilo(pid, _fn, "Salute: percorso del bambino")
            st.rerun()
        if s2.button("No, tienila", key=f"sp_vt_no_{vid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina la voce")(_finestra)()


def _sp_form_voce(pid, sez, v=None):
    v = v or {}
    with st.form(f"sp_form_{sez}_{v.get('id', 'nuovo')}", border=False):
        val = {}
        for chiave, etichetta, tipo in _SP_SEZIONI_BAMBINO[sez]:
            if tipo == "date":
                try:
                    pre = date.fromisoformat(v["data"]) if v.get("data") else _sp_oggi()
                except ValueError:
                    pre = _sp_oggi()
                val[chiave] = st.date_input(etichetta, value=pre, min_value=date(1990, 1, 1), max_value=_sp_oggi(), format="DD/MM/YYYY").isoformat()
            elif tipo == "num":
                val[chiave] = st.text_input(etichetta, value=_sp_fmt_num(v.get(chiave)) if v.get(chiave) else "")
            elif tipo == "tappa":
                scelta = st.selectbox(etichetta, _SP_TAPPE + ["Altra (la scrivo io)"], index=(_SP_TAPPE.index(v["tappa"]) if v.get("tappa") in _SP_TAPPE else (len(_SP_TAPPE) if v.get("tappa") else 0)))
                altra = st.text_input("Se «Altra», scrivila", value=v.get("tappa", "") if v.get("tappa") not in _SP_TAPPE else "")
                val[chiave] = altra.strip() if scelta.startswith("Altra") else scelta
            elif tipo == "denti":
                scelta = st.selectbox(etichetta, _SP_EVENTI_DENTI, index=(_SP_EVENTI_DENTI.index(v["cosa"]) if v.get("cosa") in _SP_EVENTI_DENTI else 0))
                val[chiave] = scelta
            else:
                val[chiave] = st.text_input(etichetta, value=v.get(chiave, "")).strip()
        ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
    if ok:
        if sez == "misure" and not any(_sp_num(val.get(k)) is not None for k in ("peso", "altezza", "cranio")):
            st.error("Scrivi almeno il peso, l'altezza o la circonferenza cranica.")
            return
        if sez == "tappe" and not val.get("tappa"):
            st.error("Scegli o scrivi la tappa.")
            return
        for k in ("peso", "altezza", "cranio", "febbre"):
            if k in val:
                n = _sp_num(val[k])
                val[k] = "" if n is None else f"{n:g}"
        val["id"] = v.get("id") or uuid.uuid4().hex[:8]

        def _fn(p):
            b = dict(p.get("bambino") or {})
            b[sez] = [x for x in b.get(sez, []) if x.get("id") != val["id"]] + [val]
            p["bambino"] = b
        _sp_salva_profilo(pid, _fn, "Salute: percorso del bambino")
        st.session_state.pop(f"sp_bmod_{sez}", None)
        st.session_state["fa_msg"] = "✅ Salvato."
        st.rerun()


def _sp_editor_sezione(pid, p, sez, vuoto):
    voci = sorted((p.get("bambino") or {}).get(sez, []), key=lambda x: x.get("data", ""), reverse=True)
    if not voci:
        st.caption(vuoto)
    for v in voci:
        testo = f"{_sp_data_it(v.get('data'))} · {_sp_riassunto_voce(sez, v, p)}"
        st.markdown(f"<div class='sp-card'>{_sp_e(testo)}" + (f"<br><small>{_sp_e(v.get('nota'))}</small>" if v.get("nota") else "") + "</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        if c1.button("✏️ Modifica", key=f"sp_b_e_{v['id']}", width="stretch"):
            st.session_state[f"sp_bmod_{sez}"] = v["id"]
            st.rerun()
        if c2.button("🗑️ Elimina", key=f"sp_b_t_{v['id']}", width="stretch"):
            _sp_dialogo_togli_voce(pid, sez, v["id"], testo)
        if st.session_state.get(f"sp_bmod_{sez}") == v["id"]:
            _sp_form_voce(pid, sez, v)
    with st.expander("➕ Aggiungi", expanded=not voci):
        _sp_form_voce(pid, sez)


def sp_svg_crescita(misure, campo, unita):
    """Un piccolo grafico (SVG) del peso o dell'altezza nel tempo."""
    pts = [(m["data"], _sp_num(m.get(campo))) for m in sorted(misure, key=lambda x: x.get("data", "")) if _sp_num(m.get(campo)) is not None and m.get("data")]
    if len(pts) < 2:
        return ""
    xs = [date.fromisoformat(d_).toordinal() for d_, _ in pts]
    ys = [y for _, y in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if x1 == x0:
        x1 = x0 + 1
    if y1 == y0:
        y1 = y0 + 1
    W, H, M = 320, 150, 28
    px = lambda x: M + (x - x0) / (x1 - x0) * (W - 2 * M)
    py = lambda y: H - M - (y - y0) / (y1 - y0) * (H - 2 * M)
    linea = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
    pallini = "".join(f"<circle cx='{px(x):.1f}' cy='{py(y):.1f}' r='3' fill='#d84315'/>" for x, y in zip(xs, ys))
    return (f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' style='width:100%;max-width:420px;background:#fff;border-radius:10px'>"
            f"<polyline points='{linea}' fill='none' stroke='#d84315' stroke-width='2'/>{pallini}"
            f"<text x='4' y='12' font-size='10' fill='#444'>{unita}: da {y0:g} a {y1:g}</text>"
            f"<text x='{M}' y='{H - 6}' font-size='9' fill='#444'>{_sp_data_it(pts[0][0])}</text><text x='{W - M - 52}' y='{H - 6}' font-size='9' fill='#444'>{_sp_data_it(pts[-1][0])}</text></svg>")



# ---------------------------------------------------------------------------------------------------------------------
# CURVE DI CRESCITA OMS (da 0 a 5 anni): le tabelle ufficiali dell'Organizzazione Mondiale della Sanità sono QUI DENTRO (nessuna libreria da installare)
# ---------------------------------------------------------------------------------------------------------------------
import math as _math

_OMS_LMS = {   # tabelle OMS (L, M, S): chiave «indicatore:sesso:tipo» — m = mensili 0-60 mesi, w = settimanali 0-13 settimane. Fonte: OMS Child Growth Standards (via pygrowup, licenza BSD)
    "wfa:M:m": [[0,0.3487,3.3464,0.14602],[1,0.2297,4.4709,0.13395],[2,0.197,5.5675,0.12385],[3,0.1738,6.3762,0.11727],[4,0.1553,7.0023,0.11316],[5,0.1395,7.5105,0.1108],[6,0.1257,7.934,0.10958],[7,0.1134,8.297,0.10902],[8,0.1021,8.6151,0.10882],[9,0.0917,8.9014,0.10881],[10,0.082,9.1649,0.10891],[11,0.073,9.4122,0.10906],[12,0.0644,9.6479,0.10925],[13,0.0563,9.8749,0.10949],[14,0.0487,10.0953,0.10976],[15,0.0413,10.3108,0.11007],[16,0.0343,10.5228,0.11041],[17,0.0275,10.7319,0.11079],[18,0.0211,10.9385,0.11119],[19,0.0148,11.143,0.11164],[20,0.0087,11.3462,0.11211],[21,0.0029,11.5486,0.11261],[22,-0.0028,11.7504,0.11314],[23,-0.0083,11.9514,0.11369],[24,-0.0137,12.1515,0.11426],[25,-0.0189,12.3502,0.11485],[26,-0.024,12.5466,0.11544],[27,-0.0289,12.7401,0.11604],[28,-0.0337,12.9303,0.11664],[29,-0.0385,13.1169,0.11723],[30,-0.0431,13.3,0.11781],[31,-0.0476,13.4798,0.11839],[32,-0.052,13.6567,0.11896],[33,-0.0564,13.8309,0.11953],[34,-0.0606,14.0031,0.12008],[35,-0.0648,14.1736,0.12062],[36,-0.0689,14.3429,0.12116],[37,-0.0729,14.5113,0.12168],[38,-0.0769,14.6791,0.1222],[39,-0.0808,14.8466,0.12271],[40,-0.0846,15.014,0.12322],[41,-0.0883,15.1813,0.12373],[42,-0.092,15.3486,0.12425],[43,-0.0957,15.5158,0.12478],[44,-0.0993,15.6828,0.12531],[45,-0.1028,15.8497,0.12586],[46,-0.1063,16.0163,0.12643],[47,-0.1097,16.1827,0.127],[48,-0.1131,16.3489,0.12759],[49,-0.1165,16.515,0.12819],[50,-0.1198,16.6811,0.1288],[51,-0.123,16.8471,0.12943],[52,-0.1262,17.0132,0.13005],[53,-0.1294,17.1792,0.13069],[54,-0.1325,17.3452,0.13133],[55,-0.1356,17.5111,0.13197],[56,-0.1387,17.6768,0.13261],[57,-0.1417,17.8422,0.13325],[58,-0.1447,18.0073,0.13389],[59,-0.1477,18.1722,0.13453],[60,-0.1506,18.3366,0.13517]],
    "wfa:M:w": [[0,0.3487,3.3464,0.14602],[1,0.2776,3.4879,0.14483],[2,0.2581,3.7529,0.14142],[3,0.2442,4.0603,0.13807],[4,0.2331,4.3671,0.13497],[5,0.2237,4.659,0.13215],[6,0.2155,4.9303,0.1296],[7,0.2081,5.1817,0.12729],[8,0.2014,5.4149,0.1252],[9,0.1952,5.6319,0.1233],[10,0.1894,5.8346,0.12157],[11,0.184,6.0242,0.12001],[12,0.1789,6.2019,0.1186],[13,0.174,6.369,0.11732]],
    "wfa:F:m": [[0,0.3809,3.2322,0.14171],[1,0.1714,4.1873,0.13724],[2,0.0962,5.1282,0.13],[3,0.0402,5.8458,0.12619],[4,-0.005,6.4237,0.12402],[5,-0.043,6.8985,0.12274],[6,-0.0756,7.297,0.12204],[7,-0.1039,7.6422,0.12178],[8,-0.1288,7.9487,0.12181],[9,-0.1507,8.2254,0.12199],[10,-0.17,8.48,0.12223],[11,-0.1872,8.7192,0.12247],[12,-0.2024,8.9481,0.12268],[13,-0.2158,9.1699,0.12283],[14,-0.2278,9.387,0.12294],[15,-0.2384,9.6008,0.12299],[16,-0.2478,9.8124,0.12303],[17,-0.2562,10.0226,0.12306],[18,-0.2637,10.2315,0.12309],[19,-0.2703,10.4393,0.12315],[20,-0.2762,10.6464,0.12323],[21,-0.2815,10.8534,0.12335],[22,-0.2862,11.0608,0.1235],[23,-0.2903,11.2688,0.12369],[24,-0.2941,11.4775,0.1239],[25,-0.2975,11.6864,0.12414],[26,-0.3005,11.8947,0.12441],[27,-0.3032,12.1015,0.12472],[28,-0.3057,12.3059,0.12506],[29,-0.308,12.5073,0.12545],[30,-0.3101,12.7055,0.12587],[31,-0.312,12.9006,0.12633],[32,-0.3138,13.093,0.12683],[33,-0.3155,13.2837,0.12737],[34,-0.3171,13.4731,0.12794],[35,-0.3186,13.6618,0.12855],[36,-0.3201,13.8503,0.12919],[37,-0.3216,14.0385,0.12988],[38,-0.323,14.2265,0.13059],[39,-0.3243,14.414,0.13135],[40,-0.3257,14.601,0.13213],[41,-0.327,14.7873,0.13293],[42,-0.3283,14.9727,0.13376],[43,-0.3296,15.1573,0.1346],[44,-0.3309,15.341,0.13545],[45,-0.3322,15.524,0.1363],[46,-0.3335,15.7064,0.13716],[47,-0.3348,15.8882,0.138],[48,-0.3361,16.0697,0.13884],[49,-0.3374,16.2511,0.13968],[50,-0.3387,16.4322,0.14051],[51,-0.34,16.6133,0.14132],[52,-0.3414,16.7942,0.14213],[53,-0.3427,16.9748,0.14293],[54,-0.344,17.1551,0.14371],[55,-0.3453,17.3347,0.14448],[56,-0.3466,17.5136,0.14525],[57,-0.3479,17.6916,0.146],[58,-0.3492,17.8686,0.14675],[59,-0.3505,18.0445,0.14748],[60,-0.3518,18.2193,0.14821]],
    "wfa:F:w": [[0,0.3809,3.2322,0.14171],[1,0.2671,3.3388,0.146],[2,0.2304,3.5693,0.14339],[3,0.2024,3.8352,0.1406],[4,0.1789,4.0987,0.13805],[5,0.1582,4.3476,0.13583],[6,0.1395,4.5793,0.13392],[7,0.1224,4.795,0.13228],[8,0.1065,4.9959,0.13087],[9,0.0918,5.1842,0.12966],[10,0.0779,5.3618,0.12861],[11,0.0648,5.5295,0.1277],[12,0.0525,5.6883,0.12691],[13,0.0407,5.8393,0.12622]],
    "lhfa:M:m": [[0,1.0,49.8842,0.03795],[1,1.0,54.7244,0.03557],[2,1.0,58.4249,0.03424],[3,1.0,61.4292,0.03328],[4,1.0,63.886,0.03257],[5,1.0,65.9026,0.03204],[6,1.0,67.6236,0.03165],[7,1.0,69.1645,0.03139],[8,1.0,70.5994,0.03124],[9,1.0,71.9687,0.03117],[10,1.0,73.2812,0.03118],[11,1.0,74.5388,0.03125],[12,1.0,75.7488,0.03137],[13,1.0,76.9186,0.03154],[14,1.0,78.0497,0.03174],[15,1.0,79.1458,0.03197],[16,1.0,80.2113,0.03222],[17,1.0,81.2487,0.0325],[18,1.0,82.2587,0.03279],[19,1.0,83.2418,0.0331],[20,1.0,84.1996,0.03342],[21,1.0,85.1348,0.03376],[22,1.0,86.0477,0.0341],[23,1.0,86.941,0.03445],[24,1.0,87.1161,0.03507],[25,1.0,87.972,0.03542],[26,1.0,88.8065,0.03576],[27,1.0,89.6197,0.0361],[28,1.0,90.412,0.03642],[29,1.0,91.1828,0.03674],[30,1.0,91.9327,0.03704],[31,1.0,92.6631,0.03733],[32,1.0,93.3753,0.03761],[33,1.0,94.0711,0.03787],[34,1.0,94.7532,0.03812],[35,1.0,95.4236,0.03836],[36,1.0,96.0835,0.03858],[37,1.0,96.7337,0.03879],[38,1.0,97.3749,0.039],[39,1.0,98.0073,0.03919],[40,1.0,98.631,0.03937],[41,1.0,99.2459,0.03954],[42,1.0,99.8515,0.03971],[43,1.0,100.4485,0.03986],[44,1.0,101.0374,0.04002],[45,1.0,101.6186,0.04016],[46,1.0,102.1933,0.04031],[47,1.0,102.7625,0.04045],[48,1.0,103.3273,0.04059],[49,1.0,103.8886,0.04073],[50,1.0,104.4473,0.04086],[51,1.0,105.0041,0.041],[52,1.0,105.5596,0.04113],[53,1.0,106.1138,0.04126],[54,1.0,106.6668,0.04139],[55,1.0,107.2188,0.04152],[56,1.0,107.7697,0.04165],[57,1.0,108.3198,0.04177],[58,1.0,108.8689,0.0419],[59,1.0,109.417,0.04202],[60,1.0,109.9638,0.04214]],
    "lhfa:M:w": [[0,1.0,49.8842,0.03795],[1,1.0,51.1152,0.03723],[2,1.0,52.3461,0.03652],[3,1.0,53.3905,0.03609],[4,1.0,54.3881,0.0357],[5,1.0,55.3374,0.03534],[6,1.0,56.2357,0.03501],[7,1.0,57.0851,0.0347],[8,1.0,57.8889,0.03442],[9,1.0,58.6536,0.03416],[10,1.0,59.3872,0.03392],[11,1.0,60.0894,0.03369],[12,1.0,60.7605,0.03348],[13,1.0,61.4013,0.03329]],
    "lhfa:F:m": [[0,1.0,49.1477,0.0379],[1,1.0,53.6872,0.0364],[2,1.0,57.0673,0.03568],[3,1.0,59.8029,0.0352],[4,1.0,62.0899,0.03486],[5,1.0,64.0301,0.03463],[6,1.0,65.7311,0.03448],[7,1.0,67.2873,0.03441],[8,1.0,68.7498,0.0344],[9,1.0,70.1435,0.03444],[10,1.0,71.4818,0.03452],[11,1.0,72.771,0.03464],[12,1.0,74.015,0.03479],[13,1.0,75.2176,0.03496],[14,1.0,76.3817,0.03514],[15,1.0,77.5099,0.03534],[16,1.0,78.6055,0.03555],[17,1.0,79.671,0.03576],[18,1.0,80.7079,0.03598],[19,1.0,81.7182,0.0362],[20,1.0,82.7036,0.03643],[21,1.0,83.6654,0.03666],[22,1.0,84.604,0.03688],[23,1.0,85.5202,0.03711],[24,1.0,85.7153,0.03764],[25,1.0,86.5904,0.03786],[26,1.0,87.4462,0.03808],[27,1.0,88.283,0.0383],[28,1.0,89.1004,0.03851],[29,1.0,89.8991,0.03872],[30,1.0,90.6797,0.03893],[31,1.0,91.443,0.03913],[32,1.0,92.1906,0.03933],[33,1.0,92.9239,0.03952],[34,1.0,93.6444,0.03971],[35,1.0,94.3533,0.03989],[36,1.0,95.0515,0.04006],[37,1.0,95.7399,0.04024],[38,1.0,96.4187,0.04041],[39,1.0,97.0885,0.04057],[40,1.0,97.7493,0.04073],[41,1.0,98.4015,0.04089],[42,1.0,99.0448,0.04105],[43,1.0,99.6795,0.0412],[44,1.0,100.3058,0.04135],[45,1.0,100.9238,0.0415],[46,1.0,101.5337,0.04164],[47,1.0,102.136,0.04179],[48,1.0,102.7312,0.04193],[49,1.0,103.3197,0.04206],[50,1.0,103.9021,0.0422],[51,1.0,104.4786,0.04233],[52,1.0,105.0494,0.04246],[53,1.0,105.6148,0.04259],[54,1.0,106.1748,0.04272],[55,1.0,106.7295,0.04285],[56,1.0,107.2788,0.04298],[57,1.0,107.8227,0.0431],[58,1.0,108.3613,0.04322],[59,1.0,108.8948,0.04334],[60,1.0,109.4233,0.04347]],
    "lhfa:F:w": [[0,1.0,49.1477,0.0379],[1,1.0,50.3298,0.03742],[2,1.0,51.512,0.03694],[3,1.0,52.4695,0.03669],[4,1.0,53.3809,0.03647],[5,1.0,54.2454,0.03627],[6,1.0,55.0642,0.03609],[7,1.0,55.8406,0.03593],[8,1.0,56.5767,0.03578],[9,1.0,57.2761,0.03564],[10,1.0,57.9436,0.03552],[11,1.0,58.5816,0.0354],[12,1.0,59.1922,0.0353],[13,1.0,59.7773,0.0352]],
    "hcfa:M:m": [[0,1.0,34.4618,0.03686],[1,1.0,37.2759,0.03133],[2,1.0,39.1285,0.02997],[3,1.0,40.5135,0.02918],[4,1.0,41.6317,0.02868],[5,1.0,42.5576,0.02837],[6,1.0,43.3306,0.02817],[7,1.0,43.9803,0.02804],[8,1.0,44.53,0.02796],[9,1.0,44.9998,0.02792],[10,1.0,45.4051,0.0279],[11,1.0,45.7573,0.02789],[12,1.0,46.0661,0.02789],[13,1.0,46.3395,0.02789],[14,1.0,46.5844,0.02791],[15,1.0,46.806,0.02792],[16,1.0,47.0088,0.02795],[17,1.0,47.1962,0.02797],[18,1.0,47.3711,0.028],[19,1.0,47.5357,0.02803],[20,1.0,47.6919,0.02806],[21,1.0,47.8408,0.0281],[22,1.0,47.9833,0.02813],[23,1.0,48.1201,0.02817],[24,1.0,48.2515,0.02821],[25,1.0,48.3777,0.02825],[26,1.0,48.4989,0.0283],[27,1.0,48.6151,0.02834],[28,1.0,48.7264,0.02838],[29,1.0,48.8331,0.02842],[30,1.0,48.9351,0.02847],[31,1.0,49.0327,0.02851],[32,1.0,49.126,0.02855],[33,1.0,49.2153,0.02859],[34,1.0,49.3007,0.02863],[35,1.0,49.3826,0.02867],[36,1.0,49.4612,0.02871],[37,1.0,49.5367,0.02875],[38,1.0,49.6093,0.02878],[39,1.0,49.6791,0.02882],[40,1.0,49.7465,0.02886],[41,1.0,49.8116,0.02889],[42,1.0,49.8745,0.02893],[43,1.0,49.9354,0.02896],[44,1.0,49.9942,0.02899],[45,1.0,50.0512,0.02903],[46,1.0,50.1064,0.02906],[47,1.0,50.1598,0.02909],[48,1.0,50.2115,0.02912],[49,1.0,50.2617,0.02915],[50,1.0,50.3105,0.02918],[51,1.0,50.3578,0.02921],[52,1.0,50.4039,0.02924],[53,1.0,50.4488,0.02927],[54,1.0,50.4926,0.02929],[55,1.0,50.5354,0.02932],[56,1.0,50.5772,0.02935],[57,1.0,50.6183,0.02938],[58,1.0,50.6587,0.0294],[59,1.0,50.6984,0.02943],[60,1.0,50.7375,0.02946]],
    "hcfa:M:w": [[0,1.0,34.4618,0.03686],[1,1.0,35.1634,0.03472],[2,1.0,35.8649,0.03258],[3,1.0,36.5216,0.03197],[4,1.0,37.0926,0.03148],[5,1.0,37.601,0.03107],[6,1.0,38.0609,0.03072],[7,1.0,38.4824,0.03041],[8,1.0,38.8724,0.03014],[9,1.0,39.2368,0.0299],[10,1.0,39.5797,0.02969],[11,1.0,39.9033,0.0295],[12,1.0,40.2096,0.02933],[13,1.0,40.5008,0.02918]],
    "hcfa:F:m": [[0,1.0,33.8787,0.03496],[1,1.0,36.5463,0.0321],[2,1.0,38.2521,0.03168],[3,1.0,39.5328,0.0314],[4,1.0,40.5817,0.03119],[5,1.0,41.459,0.03102],[6,1.0,42.1995,0.03087],[7,1.0,42.829,0.03075],[8,1.0,43.3671,0.03063],[9,1.0,43.83,0.03053],[10,1.0,44.2319,0.03044],[11,1.0,44.5844,0.03035],[12,1.0,44.8965,0.03027],[13,1.0,45.1752,0.03019],[14,1.0,45.4265,0.03012],[15,1.0,45.6551,0.03006],[16,1.0,45.865,0.02999],[17,1.0,46.0598,0.02993],[18,1.0,46.2424,0.02987],[19,1.0,46.4152,0.02982],[20,1.0,46.5801,0.02977],[21,1.0,46.7384,0.02972],[22,1.0,46.8913,0.02967],[23,1.0,47.0391,0.02962],[24,1.0,47.1822,0.02957],[25,1.0,47.3204,0.02953],[26,1.0,47.4536,0.02949],[27,1.0,47.5817,0.02945],[28,1.0,47.7045,0.02941],[29,1.0,47.8219,0.02937],[30,1.0,47.934,0.02933],[31,1.0,48.041,0.02929],[32,1.0,48.1432,0.02926],[33,1.0,48.2408,0.02922],[34,1.0,48.3343,0.02919],[35,1.0,48.4239,0.02915],[36,1.0,48.5099,0.02912],[37,1.0,48.5926,0.02909],[38,1.0,48.6722,0.02906],[39,1.0,48.7489,0.02903],[40,1.0,48.8228,0.029],[41,1.0,48.8941,0.02897],[42,1.0,48.9629,0.02894],[43,1.0,49.0294,0.02891],[44,1.0,49.0937,0.02888],[45,1.0,49.156,0.02886],[46,1.0,49.2164,0.02883],[47,1.0,49.2751,0.0288],[48,1.0,49.3321,0.02878],[49,1.0,49.3877,0.02875],[50,1.0,49.4419,0.02873],[51,1.0,49.4947,0.0287],[52,1.0,49.5464,0.02868],[53,1.0,49.5969,0.02865],[54,1.0,49.6464,0.02863],[55,1.0,49.6947,0.02861],[56,1.0,49.7421,0.02859],[57,1.0,49.7885,0.02856],[58,1.0,49.8341,0.02854],[59,1.0,49.8789,0.02852],[60,1.0,49.9229,0.0285]],
    "hcfa:F:w": [[0,1.0,33.8787,0.03496],[1,1.0,34.5529,0.03374],[2,1.0,35.2272,0.03251],[3,1.0,35.843,0.03231],[4,1.0,36.3761,0.03215],[5,1.0,36.8472,0.03202],[6,1.0,37.2711,0.03191],[7,1.0,37.6584,0.03182],[8,1.0,38.0167,0.03173],[9,1.0,38.3516,0.03166],[10,1.0,38.6673,0.03158],[11,1.0,38.9661,0.03152],[12,1.0,39.2501,0.03146],[13,1.0,39.521,0.0314]],
}

_SpCalc = True                                                         # le tabelle sono nel file: sempre disponibili
_SP_Z_P = {"3°": -1.8808, "15°": -1.0364, "50°": 0.0, "85°": 1.0364, "97°": 1.8808}
_SP_CAMPI_OMS = {"peso": ("wfa", "kg", 1.0, 30.0), "altezza": ("lhfa", "cm", 40.0, 125.0), "cranio": ("hcfa", "cm", 28.0, 56.0)}


def _oms_lms(ind, sx, mesi):
    """(L, M, S) per un'età in mesi (0-60): interpolando fra le righe vicine; fino a 3 mesi si usano le tabelle a settimane."""
    if mesi <= 3:
        tab, x = _OMS_LMS[f"{ind}:{sx}:w"], min(max(mesi * 30.4374 / 7 + 1e-9, 0), 13)
    else:
        tab, x = _OMS_LMS[f"{ind}:{sx}:m"], min(max(mesi, 0), 60)
    i = int(x)
    j = min(i + 1, len(tab) - 1)
    a, b, f = tab[i], tab[j], x - i
    return tuple(a[k] + (b[k] - a[k]) * f for k in (1, 2, 3))


def _oms_z_val(ind, sx, mesi, y):
    L, M, S = _oms_lms(ind, sx, mesi)
    return _math.log(y / M) / S if abs(L) < 1e-9 else ((y / M) ** L - 1) / (S * L)


def _oms_val_da_z(ind, sx, mesi, z):
    L, M, S = _oms_lms(ind, sx, mesi)
    return M * _math.exp(S * z) if abs(L) < 1e-9 else M * (1 + L * S * z) ** (1 / L)


def sp_eta_mesi(nascita_iso, data_iso):
    try:
        return (date.fromisoformat(str(data_iso)[:10]) - date.fromisoformat(str(nascita_iso)[:10])).days / 30.4375
    except (ValueError, TypeError):
        return None


def sp_z_oms(sesso, mesi, tipo, valore):
    """Lo «z-score» OMS (quante deviazioni dalla media) di una misura; None se non si può calcolare (sesso mancante, oltre i 5 anni, valore assurdo)."""
    n = _sp_num(valore)
    if sesso not in ("Femmina", "Maschio") or mesi is None or n is None or n <= 0 or mesi < 0 or mesi > 60 or tipo not in _SP_CAMPI_OMS:
        return None
    try:
        z = _oms_z_val(_SP_CAMPI_OMS[tipo][0], "F" if sesso == "Femmina" else "M", mesi, n)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    return z if abs(z) <= 5 else None                                  # oltre 5 deviazioni la misura è quasi certamente sbagliata


def sp_percentile(z):
    return None if z is None else round(0.5 * (1 + _math.erf(z / _math.sqrt(2))) * 100)


def sp_perc_testo(sesso, nascita, data, m):
    """«percentile peso 28°, altezza 15°» per una misura registrata (stringa vuota se non calcolabile)."""
    mesi = sp_eta_mesi(nascita, data)
    out = []
    for campo, etichetta in (("peso", "peso"), ("altezza", "altezza"), ("cranio", "cranio")):
        p_ = sp_percentile(sp_z_oms(sesso, mesi, campo, m.get(campo))) if m.get(campo) else None
        if p_ is not None:
            out.append(f"{etichetta} {p_}°")
    return ("percentile " + ", ".join(out)) if out else ""


@st.cache_data(show_spinner=False)
def sp_curve_oms(sesso, campo, fino_mesi):
    """Le curve di riferimento OMS: {'3°': [(mese, valore)…], '15°': …, '50°': …, '85°': …, '97°': …} per 0..fino_mesi (massimo 60)."""
    if sesso not in ("Femmina", "Maschio") or campo not in _SP_CAMPI_OMS:
        return {}
    ind, sx = _SP_CAMPI_OMS[campo][0], "F" if sesso == "Femmina" else "M"
    return {nome: [(m, round(_oms_val_da_z(ind, sx, m, z), 2)) for m in range(0, min(int(fino_mesi), 60) + 1)] for nome, z in _SP_Z_P.items()}


def sp_svg_oms(misure, campo, sesso, nascita):
    """Il grafico con le curve di riferimento OMS (fascia 3°–97°, mediana) e i punti del bambino. '' se non si può."""
    pts = []
    for m in sorted(misure, key=lambda x: x.get("data", "")):
        mesi = sp_eta_mesi(nascita, m.get("data"))
        n = _sp_num(m.get(campo))
        if mesi is not None and 0 <= mesi <= 60 and n is not None:
            pts.append((mesi, n))
    if not pts:
        return ""
    fino = min(60, int(max(x for x, _ in pts)) + 6)
    curve = sp_curve_oms(sesso, campo, max(fino, 12))
    if not curve or not curve.get("50°"):
        return ""
    unita = _SP_CAMPI_OMS[campo][1]
    xs_max = max(m for m, _ in curve["97°"])
    ys = [v for lista in curve.values() for _, v in lista] + [y for _, y in pts]
    y0, y1 = min(ys), max(ys)
    W, H, M = 340, 190, 32
    px = lambda x: M + x / xs_max * (W - 2 * M)
    py = lambda y: H - M - (y - y0) / (y1 - y0) * (H - 2 * M)
    banda = " ".join(f"{px(m):.1f},{py(v):.1f}" for m, v in curve["97°"]) + " " + " ".join(f"{px(m):.1f},{py(v):.1f}" for m, v in reversed(curve["3°"]))
    linee = "".join(f"<polyline points='{' '.join(f'{px(m):.1f},{py(v):.1f}' for m, v in curve[k])}' fill='none' stroke='{col}' stroke-width='{sw}' {dash}/>"
                    for k, col, sw, dash in (("3°", "#7aa", 1, ""), ("15°", "#9bb", .7, "stroke-dasharray='3,3'"), ("50°", "#00796b", 1.6, "stroke-dasharray='5,3'"), ("85°", "#9bb", .7, "stroke-dasharray='3,3'"), ("97°", "#7aa", 1, "")))
    etich = "".join(f"<text x='{W - M + 2}' y='{py(curve[k][-1][1]) + 3:.1f}' font-size='8' fill='#066'>{k}</text>" for k in ("3°", "50°", "97°"))
    punti = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in pts)
    cerchi = "".join(f"<circle cx='{px(x):.1f}' cy='{py(y):.1f}' r='3.6' fill='#d84315'/>" for x, y in pts)
    asse = "".join(f"<text x='{px(m):.1f}' y='{H - 10}' font-size='8' fill='#444' text-anchor='middle'>{m}</text>" for m in range(0, int(xs_max) + 1, 6 if xs_max <= 36 else 12))
    return (f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' style='width:100%;max-width:460px;background:#fff;border-radius:10px'>"
            f"<polygon points='{banda}' fill='#cdeee6' opacity='.7'/>{linee}{etich}<polyline points='{punti}' fill='none' stroke='#d84315' stroke-width='2'/>{cerchi}{asse}"
            f"<text x='4' y='11' font-size='10' fill='#333'>{campo} ({unita}) — curve OMS, età in mesi</text></svg>")


def sp_modulo_bambino(pid):
    f, p = _sp_intestazione("👶 Percorso del bambino", pid)
    sp = p.get("sp") or {}
    eta = _sp_eta(sp.get("nascita"))
    if eta:
        st.markdown(f"**{p.get('nome', '')}** · {eta[0]} anni e {eta[1]} mesi" if eta[0] else f"**{p.get('nome', '')}** · {eta[1]} mesi")
    else:
        st.info("Per calcolare l'età scrivi la **data di nascita** in «🆘 Dati per l'emergenza».")
    st.caption("Qui si raccoglie la storia sanitaria e fisica del bambino, dalla nascita. Le **visite dal pediatra** e le **vaccinazioni** si segnano nelle schede 🩺 Visite e 💉 Vaccini di questa persona: finiscono in automatico nella scheda per il medico.")
    t1, t2, t3, t4, t5, t6 = st.tabs(["📏 Crescita", "🧩 Tappe", "🍼 Alimentazione", "🤒 Malattie", "🦷 Denti", "🏥 Ricoveri"])
    b = p.get("bambino") or {}
    with t1:
        misure = b.get("misure", [])
        sesso_b, nasc_b = sp.get("sesso", ""), sp.get("nascita", "")
        oms = bool(sesso_b in ("Femmina", "Maschio") and nasc_b and _SpCalc is not None)
        if misure and not oms:
            st.info("Per vedere le **curve di riferimento dell'OMS** (e i percentili) scrivi **data di nascita** e **sesso** in «🆘 Dati per l'emergenza»."
                    + ("" if _SpCalc is not None else " (Le curve non sono disponibili su questo dispositivo.)"))
        for campo, unita in (("peso", "peso (kg)"), ("altezza", "altezza (cm)"), ("cranio", "circonferenza cranica (cm)")):
            svg = sp_svg_oms(misure, campo, sesso_b, nasc_b) if oms else ""
            svg = svg or sp_svg_crescita(misure, campo, unita)
            if svg:
                st.markdown(svg, unsafe_allow_html=True)
        if oms and misure:
            st.caption("📊 L'area verde è la fascia tra il 3° e il 97° percentile delle curve OMS (0–5 anni); la linea tratteggiata è la mediana. Il percentile dice quanti bambini su 100 della stessa età e sesso "
                       "pesano o misurano di meno. Sono numeri statistici, non un giudizio: **li interpreta il pediatra**, che guarda anche la crescita nel tempo.")
        elif len([m for m in misure if m.get("data")]) < 2:
            st.caption("Aggiungi almeno due misure per vedere il grafico della crescita.")
        _sp_editor_sezione(pid, p, "misure", "Ancora nessuna misura. Aggiungi peso e altezza alla nascita e a ogni controllo.")
    with t2:
        _sp_editor_sezione(pid, p, "tappe", "Ancora nessuna tappa: primo sorriso, primi passi, prime parole…")
    with t3:
        _sp_editor_sezione(pid, p, "alimentazione", "Allattamento, svezzamento, alimenti introdotti e reazioni.")
    with t4:
        _sp_editor_sezione(pid, p, "malattie", "Malattie, febbri, otiti… con le cure fatte.")
    with t5:
        _sp_editor_sezione(pid, p, "denti", "Primi dentini, cadute, visite dal dentista.")
    with t6:
        _sp_editor_sezione(pid, p, "ricoveri", "Ricoveri, interventi, pronto soccorso.")
    st.markdown("---")
    note = st.text_area("📝 Note generali sul bambino", value=b.get("note", ""), height=90, key=f"sp_bnote_{pid}")
    if note.strip() != b.get("note", "").strip() and st.button("💾 Salva le note", key=f"sp_bnote_salva_{pid}", width="stretch"):
        _sp_salva_profilo(pid, lambda pr, n=note.strip(): pr.__setitem__("bambino", dict(pr.get("bambino") or {}, note=n)), "Salute: note del bambino")
        st.rerun()
    d = sp_raccogli(f, pid)
    corpo = sp_html_bambino_corpo(p.get("bambino") or {}, sp.get("sesso", ""), sp.get("nascita", ""))
    svg = "".join(sp_svg_crescita((p.get("bambino") or {}).get("misure", []), c, u) for c, u in (("peso", "peso (kg)"), ("altezza", "altezza (cm)")))
    html_str = (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><title>Percorso di {_sp_e(p.get('nome'))}</title><style>{_SP_STILE}h3{{font-size:11pt;margin:8pt 0 2pt}}</style></head>"
                f"<body><h1>Percorso sanitario e di crescita · {_sp_e(p.get('nome'))}</h1><div class='box'>Aggiornato il {_sp_data_it(d['oggi'])}</div>{svg}{corpo}"
                "<p class='nota'>Creato dall'app «La nostra dispensa» con le informazioni inserite dai genitori: non è certificato da un medico.</p></body></html>")
    nome_file = f"percorso_{re.sub(r'[^A-Za-z0-9]+', '_', p.get('nome', '')) or 'bambino'}_{d['oggi']}"
    st.download_button("📄 Scarica il libretto (da stampare o salvare come PDF)", html_str.encode("utf-8"), file_name=nome_file + ".html", mime="text/html", width="stretch")
    pdf = sp_pdf_da_html(html_str)
    if pdf:
        st.download_button("📕 Scarica il PDF", pdf, file_name=nome_file + ".pdf", mime="application/pdf", width="stretch")
    if "inv_voce" in globals():
        inv_voce(f"sp_bimbo_{pid}", "📤 Invia il libretto", f"Percorso di {p.get('nome', '')}", sp_racconto(d), lambda: ([(nome_file + ".pdf", "application/pdf", pdf)] if pdf else [(nome_file + ".html", "text/html", html_str.encode("utf-8"))]))



# ---------------------------------------------------------------------------------------------------------------------
# 6) DOCUMENTI SANITARI: li leggo io, tu confermi
# ---------------------------------------------------------------------------------------------------------------------
_SP_TIPI_DOC = ["Esame di laboratorio", "Diagnostica per immagini", "Referto di visita", "Ricetta medica", "Ricovero e dimissione", "Certificato medico", "Vaccinazione",
                "Piano terapeutico", "Esenzione o invalidità", "Altro"]
_SP_ICONE_DOC = {"Esame di laboratorio": "🧪", "Diagnostica per immagini": "🩻", "Referto di visita": "🩺", "Ricetta medica": "📝", "Ricovero e dimissione": "🏥", "Certificato medico": "📜",
                 "Vaccinazione": "💉", "Piano terapeutico": "📅", "Esenzione o invalidità": "🪪", "Altro": "📄"}
_SP_PAROLE_DOC = {
    "Esame di laboratorio": [("emocromo", 4), ("emocromocitometrico", 5), ("glicemia", 3), ("colesterolo", 3), ("creatinina", 3), ("azotemia", 3), ("transaminasi", 3), ("trigliceridi", 3), ("tsh", 3),
                             ("valori di riferimento", 4), ("intervallo di riferimento", 4), ("analisi del sangue", 5), ("esami del sangue", 5), ("laboratorio analisi", 4), ("emoglobina", 3), ("referto di laboratorio", 5),
                             ("campione", 1), ("prelievo", 2), ("urine", 2), ("piastrine", 2)],
    "Diagnostica per immagini": [("radiografia", 5), ("ecografia", 5), ("ecocolordoppler", 5), ("tomografia", 5), ("tac ", 4), ("risonanza magnetica", 5), ("risonanza", 3), ("mammografia", 5), ("mineralometria", 5),
                                 ("scintigrafia", 5), ("radiologia", 3), ("rx ", 3), ("ecocardiogramma", 5), ("elettrocardiogramma", 5), ("ecg", 3), ("moc ", 3), ("reperto", 2), ("quesito diagnostico", 4)],
    "Referto di visita": [("visita specialistica", 5), ("visita cardiologica", 5), ("visita ", 2), ("anamnesi", 4), ("esame obiettivo", 4), ("conclusioni", 3), ("diagnosi", 3), ("terapia consigliata", 4),
                          ("si consiglia", 2), ("controllo tra", 3), ("referto", 2), ("specialista", 2), ("ambulatorio", 1)],
    "Ricetta medica": [("ricetta", 5), ("nre", 4), ("prescrizione", 3), ("ricetta dematerializzata", 6), ("promemoria", 2), ("codice autenticazione", 4), ("ssn", 2), ("esenzione", 1), ("prestazioni", 2), ("prescritto", 2)],
    "Ricovero e dimissione": [("dimissione", 5), ("lettera di dimissione", 7), ("ricovero", 4), ("degenza", 4), ("decorso clinico", 5), ("reparto", 3), ("dimesso", 4), ("intervento chirurgico", 4), ("verbale di pronto soccorso", 6), ("pronto soccorso", 4)],
    "Certificato medico": [("certificato medico", 7), ("si certifica", 5), ("certifico", 5), ("idoneità", 4), ("certificato di malattia", 6), ("certificato", 3), ("inabilità", 3)],
    "Vaccinazione": [("vaccin", 4), ("certificato vaccinale", 7), ("lotto", 3), ("richiamo", 2), ("dose", 1)],
    "Piano terapeutico": [("piano terapeutico", 8), ("posologia", 2), ("durata del trattamento", 4), ("centro prescrittore", 5), ("rinnovo", 1)],
    "Esenzione o invalidità": [("esenzione ticket", 6), ("invalidità", 4), ("legge 104", 6), ("verbale di accertamento", 5), ("percentuale di invalidità", 6), ("handicap", 3), ("esenzione", 3)],
}
_SP_ESAMI = ["Emocromo", "Glicemia", "Colesterolo", "Esami del sangue", "Esame delle urine", "Radiografia", "Ecografia addominale", "Ecografia", "Ecocolordoppler", "Risonanza magnetica", "TAC", "Mammografia",
             "Mineralometria ossea (MOC)", "Elettrocardiogramma", "Ecocardiogramma", "Holter", "Visita cardiologica", "Visita ortopedica", "Visita oculistica", "Visita dermatologica", "Visita ginecologica", "Visita neurologica",
             "Visita otorinolaringoiatrica", "Visita urologica", "Visita pediatrica", "Visita fisiatrica", "Visita gastroenterologica", "Visita endocrinologica", "Visita pneumologica", "Pronto soccorso"]
_SP_MESI_NOME = {m: i + 1 for i, m in enumerate(_SP_MESI)}
_RE_DATA_SP = re.compile(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?!\d)")
_RE_DATA_TXT_SP = re.compile(r"(?<!\d)(\d{1,2})\s+(" + "|".join(_SP_MESI) + r")\s+(\d{4})(?!\d)", re.I)


def sp_tipo_da_testo(testo):
    """(tipo, punteggio) dal testo: somma delle parole tipiche. Meno di 4 punti = non so."""
    t = " " + re.sub(r"\s+", " ", (testo or "").lower()) + " "
    punti = {tipo: sum(peso * min(t.count(par), 3) for par, peso in parole) for tipo, parole in _SP_PAROLE_DOC.items()}
    tipo, p = max(punti.items(), key=lambda x: x[1])
    if p < 5:
        return "Altro", p
    if tipo == "Vaccinazione" and punti["Esame di laboratorio"] > p:
        return "Esame di laboratorio", punti["Esame di laboratorio"]
    return tipo, p


def _sp_date_nel_testo(testo, oggi_):
    """[(data, contesto)] di tutte le date trovate."""
    out = []
    for m in _RE_DATA_SP.finditer(testo):
        g, me, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = a + (2000 if a < 70 else 1900) if a < 100 else a
        try:
            out.append((date(a, me, g), testo[max(0, m.start() - 28): m.start()].lower()))
        except ValueError:
            continue
    for m in _RE_DATA_TXT_SP.finditer(testo):
        try:
            out.append((date(int(m.group(3)), _SP_MESI_NOME[m.group(2).lower()], int(m.group(1))), testo[max(0, m.start() - 28): m.start()].lower()))
        except (ValueError, KeyError):
            continue
    return out


def sp_leggi_doc(testo, f=None, nome_file="", oggi_=None):
    """Legge un documento sanitario. Ritorna {campo: {'valore', 'affidabilita', 'fonte'}}. Niente è definitivo: si conferma sempre."""
    oggi_ = oggi_ or _sp_oggi()
    t = testo or ""
    campi = {}

    def metti(k, v, aff, fonte="testo"):
        if v:
            campi[k] = {"valore": v, "affidabilita": aff, "fonte": fonte}
    tipo, punti = sp_tipo_da_testo(t)
    metti("tipo", tipo, "alta" if punti >= 12 else "media" if punti >= 7 else "bassa")
    # data del documento
    date_t = _sp_date_nel_testo(t, oggi_)
    scelte = [d_ for d_, ctx in date_t if re.search(r"referto|prelievo|esame|visita|emissione|accettazione|data\b|erogazione|prescri|dimission", ctx) and not re.search(r"nat[oa]|nascita|scadenza|valid", ctx) and d_ <= oggi_]
    if scelte:
        metti("data", max(scelte).isoformat(), "alta")
    else:
        candidate = [d_ for d_, ctx in date_t if not re.search(r"nat[oa]|nascita|scadenza|valid", ctx) and d_ <= oggi_]
        if candidate:
            metti("data", max(candidate).isoformat(), "media")
    # struttura e medico
    righe = [x.strip() for x in t.splitlines() if x.strip()]
    for r in righe[:25]:
        if re.search(r"ospedale|asl\b|a\.s\.l|azienda sanitaria|azienda ospedaliera|laboratorio|poliambulatorio|clinica|centro (?:medico|diagnostico)|ambulatorio|istituto|presidio|studio medico|policlinico|croce", r, re.I) and 4 <= len(r) <= 80:
            metti("struttura", re.sub(r"\s+", " ", r).strip(" -–,:"), "media")
            break
    mm = re.search(r"(?:medico|refertante|responsabile|specialista|dirigente medico|firmato da)[^\n]{0,25}?((?:Dott\.?(?:ssa)?|Dr\.?(?:ssa)?|Prof\.?(?:ssa)?)\s+[A-ZÀ-Ý][\wà-ÿ'’\.]+(?:\s+[A-ZÀ-Ý][\wà-ÿ'’]+){0,2})", t, re.I) \
        or re.search(r"((?:Dott\.?(?:ssa)?|Dr\.?(?:ssa)?|Prof\.?(?:ssa)?)\s+[A-ZÀ-Ý][\wà-ÿ'’\.]+(?:\s+[A-ZÀ-Ý][\wà-ÿ'’]+){0,2})", t)
    if mm:
        metti("medico", re.sub(r"\s+", " ", mm.group(1)).strip(" .,;:"), "media")
    # che esame o che visita
    tl = t.lower()
    for nome in _SP_ESAMI:
        base = nome.lower().split(" (")[0]
        if base in tl or (base.startswith("visita ") and base.replace("visita ", "visita ") in tl):
            metti("esame", nome, "media")
            break
    # chi è il paziente: nome, codice fiscale
    cfm = re.search(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", t.upper()) or re.search(r"[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]", re.sub(r"[^A-Z0-9]", "", t.upper()))
    if cfm:
        metti("cf", cfm.group(0), "alta")
    pm = re.search(r"(?i:paziente|assistito|cognome e nome|nome e cognome|intestatario|sig\.?(?:ra)?)[ \t]*[:\-]?[ \t]*([A-ZÀ-Ý][A-Za-zÀ-ÿ'’]+(?:[ \t]+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’]+){0,3})", t)
    if pm:
        parole_p = pm.group(1).split()
        while len(parole_p) > 1 and parole_p[-1].lower() in ("codice", "data", "nato", "nata", "il", "del", "residente", "luogo", "reparto", "ricovero", "tessera", "eta", "età", "sesso", "domicilio", "cf", "c.f."):
            parole_p.pop()
        metti("paziente", " ".join(parole_p), "media")
    # ricetta
    if tipo == "Ricetta medica":
        nre = re.search(r"\b(?=[0-9A-Z]*\d)(?=[0-9A-Z]*[A-Z])[0-9A-Z]{15}\b", t.upper())
        if nre:
            metti("codice", nre.group(0), "media")
        v = [d_ for d_, ctx in date_t if re.search(r"valid|scad|entro", ctx)]
        if v:
            metti("valida_fino", max(v).isoformat(), "media")
    # a chi appartiene fra i profili
    if f is not None:
        pid, motivo = sp_proponi_profilo(f, campi.get("paziente", {}).get("valore", ""), campi.get("cf", {}).get("valore", ""))
        if pid:
            metti("profilo", pid, "alta" if motivo == "codice fiscale" else "media", motivo)
    return campi


_SP_ANALITI = [("Emocromo", r"emocromo|globuli rossi|globuli bianchi|piastrine|emoglobina"), ("Glicemia", r"glicemia|glucosio"), ("Colesterolo", r"colesterolo"), ("Trigliceridi", r"trigliceridi"),
               ("Creatinina", r"creatinina"), ("Azotemia", r"azotemia|\burea\b"), ("Transaminasi (AST/ALT)", r"transaminasi|\bgot\b|\bgpt\b|\bast\b|\balt\b"), ("Gamma GT", r"gamma ?gt|gamma-glutamil"),
               ("Bilirubina", r"bilirubina"), ("Ferritina", r"ferritina"), ("Sideremia", r"sideremia"), ("Vitamina D", r"vitamina d|25-oh"), ("Vitamina B12", r"\bb12\b|cobalamina"), ("TSH", r"\btsh\b"),
               ("FT3 / FT4", r"\bft3\b|\bft4\b"), ("PSA", r"\bpsa\b"), ("Emoglobina glicata (HbA1c)", r"hba1c|emoglobina glicata"), ("VES", r"\bves\b|velocità di eritro"), ("PCR", r"\bpcr\b|proteina c reattiva"),
               ("Esame delle urine", r"esame (?:delle )?urine|urinocoltura"), ("Sodio e potassio", r"sodio|potassio|natriemia|potassiemia"), ("Acido urico", r"acido urico|uricemia"), ("Calcio", r"\bcalcio\b|calcemia"),
               ("Coagulazione (PT/INR)", r"\binr\b|\baptt\b|fibrinogeno")]
_RE_DATA_EFF = r"data (?:della |dell')?(?:visita|esame|prestazione|prelievo|esecuzione|accettazione)|eseguit[oa] il|effettuat[oa] il|visita del|esame del|prelievo del|svolt[oa] il|prestazione del"
_RE_DATA_REF = r"referto del|refertat[oa] il|data (?:del )?referto|emess[oa] il|data emissione|stampat[oa] il|data di stampa|validat[oa] il|firmat[oa] il"


def sp_aggiungi_mesi_g(d, quantita, unita):
    if unita.startswith("giorn"):
        return d + timedelta(days=quantita)
    if unita.startswith("settim"):
        return d + timedelta(weeks=quantita)
    return sp_aggiungi_mesi(d, quantita * (12 if unita.startswith("ann") else 1))


def _sp_arricchisci_lettura(campi, t, oggi_):
    """Aggiunge a una lettura: area medica, prestazione, tipo, elenco degli esami, data dell'esame distinta da quella del referto, conclusioni copiate dal documento, controllo consigliato dal medico."""
    def metti(k, v, aff, fonte="testo"):
        if v:
            campi[k] = {"valore": v, "affidabilita": aff, "fonte": fonte}
    cl = cat_classifica(t) if "cat_classifica" in globals() else {}
    if cl.get("area"):
        aff = "alta" if cl["punti"] >= 14 else "media" if cl["punti"] >= 8 else "bassa"
        metti("specialita", cl["area"], aff, "parole: " + ", ".join(cl["parole"][:4]))
        if cl.get("prestazione"):
            metti("prestazione", cl["prestazione"], aff)
            if "esame" not in campi or campi["esame"]["affidabilita"] != "alta":
                metti("esame", cl["prestazione"], aff)
        if cl.get("tipo"):
            metti("tipo_prestazione", cl["tipo"], aff)
        if cl.get("alternative"):
            campi["_alternative"] = {"valore": ", ".join(cl["alternative"]), "affidabilita": "bassa", "fonte": "testo"}
    # elenco degli esami contenuti (analisi)
    tl = t.lower()
    trovati = [nome for nome, rx in _SP_ANALITI if re.search(rx, tl)]
    if len(trovati) >= 2 or (campi.get("tipo", {}).get("valore") == "Esame di laboratorio" and trovati):
        metti("esami_elenco", ", ".join(trovati), "media")
    # le date: quella dell'esame o della visita NON è quella del referto
    date_t = _sp_date_nel_testo(t, oggi_)
    eff = [d_ for d_, ctx in date_t if re.search(_RE_DATA_EFF, ctx) and d_ <= oggi_ and not re.search(r"nat[oa]|nascita|scadenza|valid", ctx)]
    ref = [d_ for d_, ctx in date_t if re.search(_RE_DATA_REF, ctx) and d_ <= oggi_]
    if eff:
        metti("data", max(eff).isoformat(), "alta", "data dell'esame o della visita")
        if ref and max(ref) != max(eff):
            metti("data_referto", max(ref).isoformat(), "alta", "data del referto")
    elif ref:
        metti("data_referto", max(ref).isoformat(), "media", "data del referto")
        if "data" in campi:
            campi["data"]["affidabilita"] = "bassa"
            campi["data"]["fonte"] = "potrebbe essere la data del referto: controlla"
    # le conclusioni, copiate così come sono (niente riassunti inventati)
    m = re.search(r"(?is)\b(conclusioni|diagnosi|giudizio diagnostico|commento|esito)\b\s*[:\-–]?\s*(.{12,600}?)(?=\n\s*\n|\n\s*[A-ZÀ-Ý][A-ZÀ-Ý ]{5,}\s*[:\n]|$)", t)
    if m:
        testo_c = re.sub(r"\s+", " ", m.group(2)).strip(" -–:")
        if len(testo_c) >= 12:
            metti("conclusioni", testo_c[:500], "media", "copiato dal documento")
    # il controllo consigliato dal medico (solo se è scritto)
    mc = re.search(r"(?i)(controllo|rivalutazione|follow[- ]?up|rivedere|ripetere|da ripetere|rivisita)[^.\n]{0,45}?\b(tra|entro|fra|dopo)\s+(\d{1,2})\s*(giorni|giorno|settimane|settimana|mesi|mese|anni|anno)\b", t)
    if mc:
        n_, unita = int(mc.group(3)), mc.group(4).lower()
        metti("controllo_indicato", f"{mc.group(1).capitalize()} {mc.group(2)} {n_} {unita}", "media", "scritto nel documento")
        base = None
        try:
            base = date.fromisoformat(campi.get("data", {}).get("valore", "")) if campi.get("data") else None
        except ValueError:
            base = None
        if base:
            metti("prossimo_controllo", sp_aggiungi_mesi_g(base, n_, unita).isoformat(), "media", "calcolata da ciò che scrive il medico")
    return campi


_sp_leggi_doc_base = sp_leggi_doc


def sp_leggi_doc(testo, f=None, nome_file="", oggi_=None):                         # noqa: F811
    """La lettura di sempre + area medica, prestazione, date distinte, esami contenuti, conclusioni e controllo consigliato."""
    campi = _sp_leggi_doc_base(testo, f, nome_file, oggi_)
    try:
        return _sp_arricchisci_lettura(campi, testo or "", oggi_ or _sp_oggi())
    except Exception:
        return campi


def sp_titolo_doc(d):                                                              # noqa: F811
    nome = d.get("esame") or d.get("prestazione") or ""
    return " · ".join(x for x in (d.get("tipo", "Documento"), nome, d.get("struttura") if not nome else "", _sp_data_it(d.get("data"))) if x)


def _sp_norm_nome(x):
    import unicodedata
    return re.sub(r"[^a-z ]", "", unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode().lower()).split()


def sp_proponi_profilo(f, paziente, cf):
    """(id profilo, motivo) in base al codice fiscale o al nome letto; (None, '') se non lo so."""
    profili = f.get("profili") or []
    if cf:
        for p in profili:
            try:
                if _fa_cf_del_profilo(f, p["id"]) == cf:
                    return p["id"], "codice fiscale"
            except Exception:
                pass
    parole = set(_sp_norm_nome(paziente))
    if len(parole) >= 2:
        for p in profili:
            nome = set(_sp_norm_nome(p.get("nome")))
            if nome and (nome <= parole or (len(nome & parole) >= 2)):
                return p["id"], "nome"
    return None, ""


def sp_trova_doppioni_doc(profilo, tipo, data, sha, struttura=""):
    """Documenti già archiviati che sembrano lo stesso: [(doc, motivo)]."""
    out = []
    for d in profilo.get("docsan", []):
        if sha and (d.get("file") or {}).get("sha") == sha:
            out.append((d, "è lo stesso identico file"))
        elif tipo and d.get("tipo") == tipo and data and d.get("data") == data and (not struttura or not d.get("struttura") or _sp_norm_nome(d["struttura"])[:2] == _sp_norm_nome(struttura)[:2]):
            out.append((d, "stesso tipo e stessa data"))
    return out


class _SpUp:
    """Un file già letto, fatto passare per «caricato» (serve a _fa_salva_files)."""
    def __init__(self, nome, dati):
        self.name, self._d = nome, dati

    def getvalue(self):
        return self._d


def _sp_dialogo_togli_docsan(pid, did, titolo):
    def _finestra():
        st.warning(f"Eliminare questo documento?\n\n**{_sp_e(titolo)}**")
        st.caption("Il file originale verrà cancellato.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=f"sp_ds_del_si_{did}", type="primary", width="stretch"):
            ids = []

            def _fn(p):
                for d in p.get("docsan", []):
                    if d.get("id") == did and (d.get("file") or {}).get("id"):
                        ids.append(d["file"]["id"])
                p["docsan"] = [d for d in p.get("docsan", []) if d.get("id") != did]
            _sp_salva_profilo(pid, _fn, "Salute: documento sanitario eliminato")
            if ids:
                _fa_cancella_files(ids)
            st.session_state["fa_msg"] = "🗑️ Documento eliminato."
            st.rerun()
        if s2.button("No, tienilo", key=f"sp_ds_del_no_{did}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina il documento")(_finestra)()


def _sp_form_docsan(chiave, f, pid_corrente, v=None, riconosciuto=None, con_profilo=True):
    """Il modulo di conferma (nuovo documento o correzione). Ritorna (ok, valori)."""
    v = v or {}
    riconosciuto = riconosciuto or {}

    def val(k, d=""):
        return v.get(k) or (riconosciuto.get(k) or {}).get("valore", d)

    def aff(k):
        a = (riconosciuto.get(k) or {}).get("affidabilita")
        return {"alta": " 🟢", "media": " 🟡", "bassa": " 🟠"}.get(a, "")

    def data_iso(k):
        try:
            return date.fromisoformat(val(k)) if val(k) else None
        except ValueError:
            return None
    profili = _fa_profili(f)
    aree = list(CAT_AREE) if "CAT_AREE" in globals() else []
    tipi_p = list(CAT_TIPI) if "CAT_TIPI" in globals() else ["Altro"]
    with st.form(chiave, border=False):
        if con_profilo:
            prop = (riconosciuto.get("profilo") or {}).get("valore")
            pids = [p["id"] for p in profili]
            att = prop if prop in pids else pid_corrente
            profilo = st.selectbox("👤 Di chi è" + (aff("profilo") if prop else ""), pids, index=pids.index(att) if att in pids else 0, format_func=lambda i: next(p["nome"] for p in profili if p["id"] == i))
        else:
            profilo = pid_corrente
        tipo_att = val("tipo") if val("tipo") in _SP_TIPI_DOC else "Altro"
        tipo = st.selectbox("📂 Che documento è" + aff("tipo"), _SP_TIPI_DOC, index=_SP_TIPI_DOC.index(tipo_att), format_func=lambda x: f"{_SP_ICONE_DOC.get(x, '')} {x}")
        sp_att = val("specialita")
        opz_sp = [""] + aree
        spec = st.selectbox("🩺 Area medica (specialità)" + aff("specialita"), opz_sp, index=opz_sp.index(sp_att) if sp_att in opz_sp else 0,
                            format_func=lambda x: "— non so —" if not x else f"{CAT_ICONE.get(x, '')} {x}")
        spec_altra = st.text_input("Se la specialità non è nell'elenco, scrivila qui", value=sp_att if sp_att and sp_att not in opz_sp else "", placeholder="es. Medicina estetica")
        tp_att = val("tipo_prestazione")
        tipo_prest = st.selectbox("🧭 Tipo di prestazione" + aff("tipo_prestazione"), [""] + tipi_p, index=([""] + tipi_p).index(tp_att) if tp_att in tipi_p else 0, format_func=lambda x: "— non so —" if not x else x)
        esame = st.text_input("Che esame o che visita" + aff("esame"), value=val("esame"), placeholder="es. Ecocardiogramma, Visita cardiologica, Emocromo")
        elenco = st.text_input("Esami contenuti (se è un'analisi)" + aff("esami_elenco"), value=val("esami_elenco"), placeholder="es. Emocromo, Glicemia, Colesterolo")
        c1, c2 = st.columns(2)
        data = c1.date_input("Data dell'esame o della visita" + aff("data"), value=data_iso("data"), min_value=date(1950, 1, 1), max_value=_sp_oggi(), format="DD/MM/YYYY",
                             help="Quella in cui è stata fatta la prestazione (non quella in cui è stato scritto il referto).")
        data_ref = c2.date_input("Data del referto (se diversa)" + aff("data_referto"), value=data_iso("data_referto"), min_value=date(1950, 1, 1), max_value=_sp_oggi(), format="DD/MM/YYYY")
        c5, c6 = st.columns(2)
        medico = c5.text_input("Medico" + aff("medico"), value=val("medico"))
        struttura = c6.text_input("Ospedale, laboratorio o studio" + aff("struttura"), value=val("struttura"))
        c3, c4 = st.columns(2)
        codice = c3.text_input("Codice ricetta (solo ricette)", value=val("codice"))
        valida = c4.date_input("Valida fino al (solo ricette)", value=data_iso("valida_fino"), format="DD/MM/YYYY")
        conclusioni = st.text_area("Conclusioni (copiate dal documento)" + aff("conclusioni"), value=val("conclusioni"), height=90, placeholder="L'esito scritto dal medico, così com'è.")
        c7, c8 = st.columns(2)
        ctrl = c7.text_input("Controllo consigliato dal medico" + aff("controllo_indicato"), value=val("controllo_indicato"), placeholder="es. Controllo tra 6 mesi")
        pross = c8.date_input("Data del prossimo controllo" + aff("prossimo_controllo"), value=data_iso("prossimo_controllo"), format="DD/MM/YYYY",
                              help="Viene dal documento, non la decide l'app. Se la scrivi, entra negli avvisi.")
        titolo = st.text_input("Titolo (se vuoto lo scrivo io)", value=v.get("titolo", "") if v.get("titolo") and v.get("titolo") != sp_titolo_doc(v) else "")
        note = st.text_area("Note (per esempio i valori da ricordare)", value=v.get("note", ""), height=80)
        ok = st.form_submit_button("✅ Conferma e archivia" if not v.get("id") else "💾 Salva le correzioni", type="primary", width="stretch")
    return ok, {"profilo": profilo, "tipo": tipo, "specialita": (spec_altra.strip() or spec), "tipo_prestazione": tipo_prest, "esame": esame.strip(), "esami_elenco": elenco.strip(),
                "data": data.isoformat() if data else "", "data_referto": data_ref.isoformat() if data_ref else "", "medico": medico.strip(), "struttura": struttura.strip(),
                "codice": codice.strip().upper(), "valida_fino": valida.isoformat() if valida else "", "conclusioni": conclusioni.strip(), "controllo_indicato": ctrl.strip(),
                "prossimo_controllo": pross.isoformat() if pross else "", "titolo": titolo.strip(), "note": note.strip()}


def _sp_archivia_docsan(pid, rif, val, riconosciuto, utente):
    """Salva il documento nella cartella della persona scelta."""
    doc = dict(val)
    doc.pop("profilo", None)
    doc.update({"id": uuid.uuid4().hex[:10], "file": rif, "creato_il": datetime.now().isoformat(timespec="seconds"), "riconosciuto": {k: v.get("valore") for k, v in (riconosciuto or {}).items()},
                "conferma": {"da": utente, "il": datetime.now().isoformat(timespec="seconds")}})
    doc["titolo"] = doc.get("titolo") or sp_titolo_doc(doc)

    def _fn(p):
        p["docsan"] = list(p.get("docsan", [])) + [doc]
    _sp_salva_profilo(pid, _fn, "Salute: documento sanitario archiviato")
    return doc


def sp_da_posta(it):
    """Dalla «Posta in arrivo» di Casa: il file diventa un documento sanitario da leggere e confermare (si apre la pagina Documenti sanitari con quel file)."""
    car = _fa_inv_allegati([{"id": it["file_id"], "nome": it.get("nome"), "mime": it.get("mime")}]) if "_fa_inv_allegati" in globals() else []
    if not car:
        st.error("Non riesco ad aprire questo file: riprova fra poco.")
        return
    nome, mime, dati = car[0]
    coda = st.session_state.setdefault("sp_ds_coda", [])
    sha = hashlib.sha256(dati).hexdigest()
    if not any(c["sha"] == sha for c in coda):
        coda.insert(0, {"nome": nome, "dati": dati, "sha": sha, "posta_id": it["id"]})
    f = _fa_dati()
    profili = _fa_profili(f)
    pid = st.session_state.get("fa_profilo") if st.session_state.get("fa_profilo") in {x["id"] for x in profili} else profili[0]["id"]
    for k in ("fa_modulo_med", "fa_modulo_foglio", "fa_modulo_dottore", "fa_modulo_sanitario", "fa_modulo_tessera", "sezione_home", "ca_bozza_in", "ca_bozza"):
        st.session_state.pop(k, None)
    st.session_state["farmacia_aperta"] = True
    st.session_state["sp_modulo"] = {"vista": "docsan", "pid": pid}
    st.rerun()


def sp_rinomina_profili(profili, f):
    """In «👥 Gestisci profili»: per ogni profilo AGGIUNTIVO (non il tuo) un campo per cambiare il nome."""
    altri = profili[1:]
    if not altri:
        return
    st.markdown("**✏️ Cambia il nome dei profili aggiuntivi**")
    for pr in altri:
        c1, c2 = st.columns([4, 1], gap="small")
        nuovo = c1.text_input(f"Nome di «{pr['nome']}»", value=pr["nome"], key=f"sp_rin_{pr['id']}", label_visibility="collapsed")
        if c2.button("💾", key=f"sp_rin_b_{pr['id']}", width="stretch", help="Salva il nuovo nome"):
            n = nuovo.strip()
            if not n:
                st.error("Il nome non può essere vuoto.")
            elif n == pr["nome"]:
                st.info("È già questo il nome.")
            elif any(x["id"] != pr["id"] and x["nome"].strip().lower() == n.lower() for x in profili):
                st.error("C'è già un profilo con questo nome: scegline un altro.")
            else:
                def _rin(f_, pid_=pr["id"], nome_=n):
                    for x in f_.get("profili", []):
                        if x["id"] == pid_:
                            x["nome"] = nome_
                try:
                    _fa_salva(_rin, "Salute: nome del profilo")
                    st.session_state["fa_msg"] = f"✅ Ora si chiama «{n}»."
                    st.rerun()
                except Exception as ex:
                    st.error(f"Non sono riuscito a salvare: {ex}")
    st.divider()


def _sp_docsan_chiudi(coda):
    """Il documento in cima alla coda è finito (archiviato o scartato): si passa al prossimo e il campo di caricamento si svuota."""
    if coda:
        coda.pop(0)
    st.session_state["ca_giro"] = st.session_state.get("ca_giro", 0) + 1
    st.session_state.pop("sp_ds_fin", None)


def _sp_docsan_corpo(f, p, pid, utente, coda, finestra):
    """Il documento aperto: lo leggo, avviso se c'è già, propongo i dati e archivio solo dopo la tua conferma."""
    c = coda[0]
    st.markdown(f"#### 📖 {_sp_e(c['nome'])}" + (f" (ne restano {len(coda) - 1} dopo questo)" if len(coda) > 1 else ""))
    mime = _ca_mime(c["nome"], "", c["dati"]) if "_ca_mime" in globals() else ("application/pdf" if c["nome"].lower().endswith(".pdf") else "image/jpeg")
    if mime.startswith("image/"):
        st.image(c["dati"], width=260)
    chiave_lettura = f"sp_ds_lett_{c['sha']}"
    if chiave_lettura not in st.session_state:
        with st.spinner("Leggo il documento…"):
            try:
                testo, info = ca_estrai_testo(c["nome"], mime, c["dati"]) if "ca_estrai_testo" in globals() else ("", {})
            except Exception:
                testo, info = "", {}
            st.session_state[chiave_lettura] = (sp_leggi_doc(testo, f, c["nome"]) if testo.strip() else {}, bool(testo.strip()))
    riconosciuto, letto = st.session_state[chiave_lettura]
    if letto:
        st.success("Ho letto il documento. I pallini: 🟢 sicuro, 🟡 abbastanza, 🟠 poco. **Controlla e correggi** quello che serve.")
        perche = (riconosciuto.get("specialita") or {}).get("fonte") or ""
        if perche.startswith("parole:"):
            st.caption("🔎 Area medica riconosciuta da " + perche[8:] + ((" · potrebbe essere anche: " + riconosciuto["_alternative"]["valore"]) if riconosciuto.get("_alternative") else ""))
        if (riconosciuto.get("data") or {}).get("fonte", "").startswith("potrebbe"):
            st.warning("⚠️ Ho trovato solo la data del referto: **controlla la data dell'esame o della visita**.")
    else:
        st.info("Non sono riuscito a leggere il testo (foto sfocata o scansione): compila tu i dati qui sotto.")
    if letto and (riconosciuto.get("tipo") or {}).get("valore") == "Esenzione o invalidità" and "se_da_docsan" in globals():
        st.info("🪪 Questo sembra un documento di **invalidità o di esenzione**. Nella sezione **Invalidità ed esenzioni** lo registro con codice, percentuale, validità e revisione, e ti avviso prima della scadenza.")
        if st.button("🪪 Registralo lì", key="sp_ds_verso_ese", type="primary", width="stretch"):
            se_da_docsan(pid, coda[0])
            _sp_docsan_chiudi(coda)
            st.rerun()
    prop_pid = (riconosciuto.get("profilo") or {}).get("valore") or pid
    pr_dest = next((x for x in _fa_profili(f) if x["id"] == prop_pid), p)
    doppi = sp_trova_doppioni_doc(pr_dest, (riconosciuto.get("tipo") or {}).get("valore"), (riconosciuto.get("data") or {}).get("valore"), c["sha"], (riconosciuto.get("struttura") or {}).get("valore", ""))
    if doppi and not st.session_state.get(f"sp_ds_dup_{c['sha']}"):
        st.warning("⚠️ **Controlla: forse questo documento c'è già.**")
        for dd, motivo in doppi[:3]:
            st.markdown(f"<div class='sp-card'><b>📄 {_sp_e(dd.get('titolo'))}</b><br><small>{motivo}</small></div>", unsafe_allow_html=True)
        q1, q2 = st.columns(2, gap="small")
        if q1.button("📥 Archivia lo stesso", key="sp_ds_dup_si", width="stretch"):
            st.session_state[f"sp_ds_dup_{c['sha']}"] = True
            st.rerun()
        if q2.button("✖ Non archiviare", key="sp_ds_dup_no", width="stretch"):
            _sp_docsan_chiudi(coda)
            st.rerun()
        return
    ok, val = _sp_form_docsan("sp_ds_form_" + c["sha"][:10], f, pid, riconosciuto=riconosciuto)
    b1, b2 = st.columns(2, gap="small")
    if b1.button("⏭️ Salta (lo rivedo dopo)", key="sp_ds_salta", width="stretch") and len(coda) > 1:
        coda.append(coda.pop(0))
        st.session_state.pop("sp_ds_fin", None)
        st.rerun()
    if b2.button("✖ Scarta questo", key="sp_ds_scarta", width="stretch"):
        if c.get("posta_id"):
            st.session_state["fa_msg"] = "ℹ️ Il file resta nella Posta in arrivo di Casa: lo trovi lì."
        _sp_docsan_chiudi(coda)
        st.rerun()
    if ok:
        try:
            rifs = _fa_salva_files([_SpUp(c["nome"], c["dati"])])
            rif = rifs[0] if rifs else {"id": "", "nome": c["nome"], "mime": mime, "sha": c["sha"]}
            dest = val["profilo"]
            _sp_archivia_docsan(dest, rif, val, riconosciuto, utente)
            if c.get("posta_id") and "_ca_posta_togli" in globals():
                try:
                    _ca_posta_togli(c["posta_id"], cancella_file=True)                              # il file è già nella cartella sanitaria: via la copia della posta
                except Exception:
                    pass
            _sp_docsan_chiudi(coda)
            nome_dest = next((x["nome"] for x in _fa_profili(f) if x["id"] == dest), "")
            st.session_state["fa_msg"] = f"✅ Documento archiviato nella cartella di {nome_dest}."
            st.rerun()
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare: {ex}")


def _sp_docsan_finestra(f, p, pid, utente, coda):
    """Il documento aperto compare IN SOVRAIMPRESSIONE (si apre da solo una volta per file; se lo chiudi puoi riaprirlo)."""
    chiave = coda[0]["sha"]

    def _apri():
        def _fin():
            _sp_docsan_corpo(f, p, pid, utente, coda, True)
        try:
            st.dialog("📖 Documento sanitario letto: controlla e conferma", width="large")(_fin)()
        except TypeError:
            st.dialog("📖 Documento sanitario letto: controlla e conferma")(_fin)()
    if st.session_state.get("sp_ds_fin") != chiave:
        st.session_state["sp_ds_fin"] = chiave
        _apri()
    else:
        st.info(f"📖 C'è un documento aperto: «{_sp_e(coda[0]['nome'])}»" + (f" (ne restano {len(coda) - 1})" if len(coda) > 1 else "") + ". Se hai chiuso la finestra, riaprila.")
        r1, r2 = st.columns(2, gap="small")
        if r1.button("📖 Riapri il documento", key="sp_ds_riapri", type="primary", width="stretch"):
            _apri()
        if r2.button("✖ Scarta il documento", key="sp_ds_scarta_f", width="stretch"):
            _sp_docsan_chiudi(coda)
            st.rerun()


def _sp_riclassifica(pid, did, nuovi, pid_a=None):
    """Cambia categoria (tipo, specialità, prestazione) a un documento e, se serve, lo sposta nella cartella di un'altra persona."""
    pid_a = pid_a or pid

    def _fn(f_):
        doc = None
        for pr in f_.get("profili", []):
            if pr["id"] == pid:
                for d_ in pr.get("docsan", []):
                    if d_.get("id") == did:
                        doc = d_
                if pid_a != pid and doc is not None:
                    pr["docsan"] = [d_ for d_ in pr.get("docsan", []) if d_.get("id") != did]
        if doc is None:
            return
        vecchio_auto = sp_titolo_doc(doc)
        doc.update(nuovi)
        if not doc.get("titolo") or doc.get("titolo") == vecchio_auto:
            doc["titolo"] = sp_titolo_doc(doc)
        if pid_a != pid:
            for pr in f_.get("profili", []):
                if pr["id"] == pid_a:
                    pr["docsan"] = list(pr.get("docsan", [])) + [doc]
    _fa_salva(_fn, "Salute: documento sanitario riclassificato")


def _sp_scelta_categoria(chiave, d=None, con_persona=False, f=None, pid=None, solo=None):
    """I campi per scegliere la categoria: tipo di documento, area medica, tipo di prestazione (e, se serve, di chi è). Ritorna i valori scelti.
    solo = 'tipo' | 'specialita' per mostrarne uno solo (spostamento di un gruppo intero)."""
    d = d or {}
    out = {}
    if solo in (None, "tipo"):
        att = d.get("tipo") if d.get("tipo") in _SP_TIPI_DOC else "Altro"
        out["tipo"] = st.selectbox("📂 Tipo di documento", _SP_TIPI_DOC, index=_SP_TIPI_DOC.index(att), format_func=lambda x: f"{_SP_ICONE_DOC.get(x, '')} {x}", key=f"{chiave}_tipo")
    if solo in (None, "specialita"):
        opz = [""] + list(CAT_AREE)
        sp_att = d.get("specialita") or ""
        sel = st.selectbox("🩺 Area medica (specialità)", opz, index=opz.index(sp_att) if sp_att in opz else 0, format_func=lambda x: "— nessuna —" if not x else f"{CAT_ICONE.get(x, '')} {x}", key=f"{chiave}_sp")
        altra = st.text_input("Se non è nell'elenco, scrivila qui", value=sp_att if sp_att and sp_att not in opz else "", key=f"{chiave}_spa")
        out["specialita"] = altra.strip() or sel
    if solo is None:
        tp_att = d.get("tipo_prestazione") or ""
        opz_t = [""] + list(CAT_TIPI)
        out["tipo_prestazione"] = st.selectbox("🧭 Tipo di prestazione", opz_t, index=opz_t.index(tp_att) if tp_att in opz_t else 0, format_func=lambda x: "— non so —" if not x else x, key=f"{chiave}_tp")
    if con_persona and f is not None:
        profili = _fa_profili(f)
        pids = [x["id"] for x in profili]
        out["_persona"] = st.selectbox("👤 Di chi è (cartella)", pids, index=pids.index(pid) if pid in pids else 0, format_func=lambda i: next(x["nome"] for x in profili if x["id"] == i), key=f"{chiave}_pers")
    return out


def _sp_riga_docsan(d, pid, f, p, vedi):
    """Un documento: scheda con i dati, e i tasti per vederlo e scaricarlo, correggerlo, inviarlo, eliminarlo."""
    prest = d.get("prestazione") or d.get("esame") or ""
    badge = " ".join(x for x in ((f"{CAT_ICONE.get(d['specialita'], '🩺')} {d['specialita']}") if d.get("specialita") else "", d.get("tipo_prestazione") or "") if x)
    righe = " · ".join(x for x in (_sp_data_it(d.get("data")), d.get("medico", ""), d.get("struttura", ""), ("codice " + d["codice"]) if d.get("codice") else "") if x)
    extra = ""
    if d.get("data_referto") and d.get("data_referto") != d.get("data"):
        extra += f"<br><small>📄 Referto del {_sp_data_it(d['data_referto'])}</small>"
    if d.get("esami_elenco"):
        extra += f"<br><small>🧪 {_sp_e(d['esami_elenco'])}</small>"
    if d.get("conclusioni"):
        extra += f"<br><small>📝 {_sp_e(d['conclusioni'][:260])}{'…' if len(d['conclusioni']) > 260 else ''}</small>"
    if d.get("controllo_indicato") or d.get("prossimo_controllo"):
        extra += f"<br><small>🔁 {_sp_e(d.get('controllo_indicato', ''))}" + (f" · entro il {_sp_data_it(d['prossimo_controllo'])}" if d.get("prossimo_controllo") else "") + "</small>"
    st.markdown(f"<div class='sp-card'><b>{_sp_e(d.get('titolo'))}</b>" + (f"<br><small>{_sp_e(badge)}</small>" if badge else "") + f"<br><small>{_sp_e(righe)}</small>" + extra
                + (f"<br><small>{_sp_e(d.get('note'))}</small>" if d.get("note") else "") + "</div>", unsafe_allow_html=True)
    ref = d.get("file") or {}
    c1, c2 = st.columns(2, gap="small")
    if ref.get("id"):
        aperto = ref["id"] in vedi
        if c1.button("🙈 Chiudi" if aperto else "👁️ Vedi / scarica", key=f"sp_dsv_{d['id']}", width="stretch"):
            vedi.remove(ref["id"]) if aperto else vedi.append(ref["id"])
            st.rerun()
    if c2.button("✏️ Modifica", key=f"sp_dsc_{d['id']}", width="stretch"):
        st.session_state["sp_ds_cor"] = None if st.session_state.get("sp_ds_cor") == d["id"] else d["id"]
        st.rerun()
    if ref.get("id") and ref["id"] in vedi:
        _sp_mostra(ref)
    e1, e2 = st.columns(2, gap="small")
    with e1:
        _fa_inv_voce(f"sp_ds_{d['id']}", "📤 Invia", f"{d.get('titolo')} – {p.get('nome', '')}", [("Area medica", d.get("specialita")), ("Data", _sp_data_it(d.get("data"))), ("Medico", d.get("medico")), ("Struttura", d.get("struttura")),
                     ("Conclusioni", d.get("conclusioni")), ("Controllo", d.get("controllo_indicato")), ("Note", d.get("note"))], [ref] if ref.get("id") else [])
    if e2.button("🗑️ Elimina", key=f"sp_dsd_{d['id']}", width="stretch"):
        _sp_dialogo_togli_docsan(pid, d["id"], d.get("titolo"))
    aperta_cat = st.session_state.get("sp_ds_cat") == d["id"]
    if st.button("🙈 Chiudi" if aperta_cat else "🏷️ Cambia categoria (o cartella)", key=f"sp_dscat_{d['id']}", width="stretch"):
        st.session_state["sp_ds_cat"] = None if aperta_cat else d["id"]
        st.rerun()
    if aperta_cat:
        st.caption("Scegli dove deve stare questo documento. Non perdi niente: cambia solo la categoria.")
        with st.form(f"sp_ds_catf_{d['id']}", border=False):
            nuovi = _sp_scelta_categoria(f"sp_ds_cat_{d['id']}", d, con_persona=len(_fa_profili(f)) > 1, f=f, pid=pid)
            ok_c = st.form_submit_button("✅ Sposta", type="primary", width="stretch")
        if ok_c:
            dest = nuovi.pop("_persona", pid)
            _sp_riclassifica(pid, d["id"], nuovi, dest)
            st.session_state.pop("sp_ds_cat", None)
            nome_dest = next((x["nome"] for x in _fa_profili(f) if x["id"] == dest), "")
            st.session_state["fa_msg"] = "✅ Spostato" + (f" nella cartella di {nome_dest}." if dest != pid else ": nuova categoria salvata.")
            st.rerun()
    if st.session_state.get("sp_ds_cor") == d["id"]:
        ok, val = _sp_form_docsan("sp_ds_cor_" + d["id"], f, pid, v=d, con_profilo=False)
        if ok:
            def _fn(pr, did=d["id"], nv=val):
                for x in pr.get("docsan", []):
                    if x.get("id") == did:
                        vecchio_auto = sp_titolo_doc(x)
                        x.update({k: v_ for k, v_ in nv.items() if k != "profilo"})
                        if not nv.get("titolo") or nv.get("titolo") == vecchio_auto:
                            x["titolo"] = sp_titolo_doc(x)
            _sp_salva_profilo(pid, _fn, "Salute: documento sanitario corretto")
            st.session_state.pop("sp_ds_cor", None)
            st.session_state["fa_msg"] = "✅ Corretto."
            st.rerun()


def sp_modulo_docsan(pid):
    f, p = _sp_intestazione("🗂️ Documenti sanitari", pid)
    utente = (st.session_state.get("sess") or {}).get("nome", "")
    st.caption("Carica un referto, un esame, una ricetta, una lettera di dimissione, un certificato… (PDF o foto). Lo leggo io: ti propongo **di chi è**, **che documento è**, l'**area medica**, il **tipo di prestazione**, "
               "la **data dell'esame** (distinta da quella del referto), il medico, la struttura, le conclusioni e l'eventuale controllo consigliato. **Archivio solo dopo la tua conferma**; se non riesco a leggerlo, lo compili tu.")
    coda = st.session_state.setdefault("sp_ds_coda", [])
    n_giro = st.session_state.get("ca_giro", 0)
    arrivi = []
    if "_ca_pannello_caricamento" in globals():
        up = _ca_pannello_caricamento(n_giro, multi=False)
        if up is not None:
            arrivi.append((up.name, up.getvalue()))
        b = st.session_state.pop("ca_bozza_in", None)                         # il file arrivato con il pulsante arancione
        if b and b.get("dati"):
            arrivi.append((b.get("nome") or "documento", b["dati"]))
    else:
        giro = st.session_state.get("sp_ds_giro", 0)
        nuovi = st.file_uploader("📎 Scegli i documenti (puoi sceglierne più di uno)", type=TIPI_FILE, accept_multiple_files=True, key=f"sp_ds_up_{giro}")
        for up in nuovi or []:
            arrivi.append((up.name, up.getvalue()))
        if nuovi:
            st.session_state["sp_ds_giro"] = giro + 1
    for nome, dati in arrivi:
        sha = hashlib.sha256(dati).hexdigest()
        if not any(c_["sha"] == sha for c_ in coda):
            coda.append({"nome": nome, "dati": dati, "sha": sha})
    if arrivi and coda:
        st.rerun() if False else None
    if coda:
        _sp_docsan_finestra(f, p, pid, utente, coda)
    # ---- l'archivio della persona: una linguetta per tipo (o per specialità, o per anno)
    docs = list(p.get("docsan", []))
    st.divider()
    st.markdown(f"#### 📚 I documenti di {p.get('nome', '')} ({len(docs)})")
    if not docs:
        st.info("Ancora nessun documento sanitario archiviato.")
        return
    cerca = st.text_input("🔍 Cerca", key=f"sp_ds_cerca_{pid}", placeholder="esame, medico, ospedale, specialità, data…", label_visibility="collapsed")
    gruppo = st.radio("Come vuoi vederli", ["📂 Per tipo di documento", "🩺 Per specialità", "📅 Per anno"], horizontal=True, key=f"sp_ds_gr_{pid}", label_visibility="collapsed")
    q = _sp_norm_nome(cerca)
    vedi = st.session_state.setdefault("sp_vedi", [])
    def _pagliaio(d):
        return " ".join(_sp_norm_nome(" ".join(str(d.get(k) or "") for k in ("titolo", "esame", "prestazione", "specialita", "medico", "struttura", "note", "esami_elenco", "conclusioni", "tipo")))) + " " + _sp_data_it(d.get("data")) + " " + str(d.get("data") or "")
    visibili = [d for d in docs if all(x in _pagliaio(d) for x in q)] if q else docs
    if not visibili:
        st.warning("Nessun documento corrisponde.")
        return
    if gruppo.startswith("📂"):
        chiavi = lambda d: d.get("tipo", "Altro")
        etichetta = lambda k: f"{_SP_ICONE_DOC.get(k, '')} {k}"
    elif gruppo.startswith("🩺"):
        chiavi = lambda d: d.get("specialita") or "Senza specialità"
        etichetta = lambda k: f"{CAT_ICONE.get(k, '🩺')} {k}"
    else:
        chiavi = lambda d: (d.get("data") or "")[:4] or "Senza data"
        etichetta = lambda k: f"📅 {k}"
    gruppi = {}
    for d in visibili:
        gruppi.setdefault(chiavi(d), []).append(d)
    ordine = sorted(gruppi, key=lambda k: (k.startswith("Senza"), -int(k) if k.isdigit() else 0, k))
    for k in ordine:
        with st.expander(f"{etichetta(k)} · {len(gruppi[k])}"):
            if not gruppo.startswith("📅"):
                modo = "tipo" if gruppo.startswith("📂") else "specialita"
                with st.popover("🏷️ Sposta tutti i documenti di questa linguetta"):
                    st.caption(f"Sposta **tutti i {len(gruppi[k])}** documenti di «{k}» in un'altra " + ("categoria di documento." if modo == "tipo" else "area medica."))
                    nuovi_g = _sp_scelta_categoria(f"sp_ds_bulk_{hashlib.md5(f"{gruppo}|{k}".encode("utf-8")).hexdigest()[:8]}", None, solo=modo)
                    if st.button(f"✅ Sposta {"il documento" if len(gruppi[k]) == 1 else "i " + str(len(gruppi[k])) + " documenti"}", key=f"sp_ds_bulkb_{hashlib.md5(f"{gruppo}|{k}".encode("utf-8")).hexdigest()[:8]}", type="primary", width="stretch"):
                        ids = [x["id"] for x in gruppi[k]]

                        def _bulk(f_, ids=ids, nuovi=nuovi_g):
                            for pr in f_.get("profili", []):
                                if pr["id"] == pid:
                                    for d_ in pr.get("docsan", []):
                                        if d_.get("id") in ids:
                                            vecchio_auto = sp_titolo_doc(d_)
                                            d_.update(nuovi)
                                            if not d_.get("titolo") or d_.get("titolo") == vecchio_auto:
                                                d_["titolo"] = sp_titolo_doc(d_)
                        _fa_salva(_bulk, "Salute: documenti sanitari riclassificati")
                        st.session_state["fa_msg"] = f"✅ Spostati {len(ids)} documenti."
                        st.rerun()
            for d in sorted(gruppi[k], key=lambda x: x.get("data", ""), reverse=True):
                _sp_riga_docsan(d, pid, f, p, vedi)


# ---------------------------------------------------------------------------------------------------------------------
# 6-bis) VISITE ED ESAMI: le STESSE specialità dei documenti, il tipo di prestazione, lo storico per specialità
# ---------------------------------------------------------------------------------------------------------------------
def _sp_vai_docsan(pid):
    st.session_state["sp_modulo"] = {"vista": "docsan", "pid": pid}
    st.rerun()


def _sp_migra_visite_dati(f):
    """Le visite di prima passano alle specialità del catalogo (in place). Ritorna True se ha cambiato qualcosa."""
    cambiato = False
    for v in f.get("visite", []):
        nuova, tp = cat_unifica_visita(v.get("categoria"))
        if nuova != v.get("categoria"):
            v["categoria"] = nuova
            cambiato = True
        if tp and not v.get("tipo_prestazione"):
            v["tipo_prestazione"] = tp
            cambiato = True
    return cambiato


def _sp_card_visita(v, pid, nomi):
    """Una visita (la scheda di sempre, con Elimina, Modifica e Invia), ora con tipo di prestazione e prestazione."""
    e = _h.escape
    righe = f"<div class='nome'>{CAT_ICONE.get(v.get('categoria'), '🩺')} {e(v.get('categoria', ''))}</div>"
    if v.get("tipo_prestazione") or v.get("prestazione"):
        righe += "<div class='riga'>🧭 " + e(" · ".join(x for x in (v.get("tipo_prestazione"), v.get("prestazione")) if x)) + "</div>"
    righe += f"<div class='riga'>📅 {data_it(v['data'])}" + (f" · {e(v['ora'])}" if v.get("ora") else "") + "</div>"
    for icona, chiave in (("👨‍⚕️", "medico"), ("❓", "motivo"), ("🔁", "controlli"), ("📝", "note")):
        if v.get(chiave):
            righe += f"<div class='riga'>{icona} {e(v[chiave])}</div>"
    if v.get("prossimo"):
        righe += f"<span class='scad'>📅 Prossimo: {data_it(v['prossimo'])}</span>"
    with st.container(border=True):
        st.markdown(f"<div class='fa-med' style='--c:#00897b'>{righe}</div>", unsafe_allow_html=True)
        _fa_bottoni_allegati(v.get("allegati", []), "visita", v["id"])
        b1, b2, b3 = st.columns(3, gap="small")
        if b1.button("Elimina", icon=":material/delete:", key="fa_elv_" + v["id"], width="stretch"):
            _fa_dialogo_elimina_voce("visite", v["id"], f"{v.get('categoria', '')} del {data_it(v['data'])}")
        if b2.button("Modifica", icon=":material/edit:", key="fa_mov_" + v["id"], width="stretch"):
            _fa_dialogo_visita(pid, v["id"])
        if "inv_canali" in globals() and b3.button("Invia", icon=":material/send:", key="fa_inv_vis_" + v["id"], width="stretch"):
            _fa_visita_invia(v, nomi.get(pid, ""))


@st.dialog("Visita o esame")
def _fa_dialogo_visita(pid, vis_id=None, prefill=None):                            # noqa: F811
    """Aggiungere o modificare una visita o un esame: stesse specialità dei documenti + tipo di prestazione.
    `prefill`: i dati già compilati letti da un documento (salute_prenotazioni.py); `_avvisi` = frasi da mostrare in cima, `_allegato` = il documento originale da allegare, `_dopo` = da fare dopo il salvataggio."""
    f = _fa_dati()
    v = next((x for x in f.get("visite", []) if x["id"] == vis_id), {}) if vis_id else (prefill or {})
    for a_ in (v.get("_avvisi") or []):
        st.info(a_)
    area_att, tp_sugg = cat_unifica_visita(v.get("categoria"))
    extra = [x for x in (f.get("categorie_extra") or []) if x not in CAT_AREE]
    if area_att and area_att not in CAT_AREE and area_att != "Altro" and area_att not in extra:
        extra.append(area_att)
    opzioni = list(CAT_AREE) + extra + ["Altro"]
    with st.form("fa_form_vis"):
        c1, c2 = st.columns(2)
        data_v = c1.date_input("Data", value=_fa_data(v.get("data")) or oggi(), format="DD/MM/YYYY", min_value=date(1950, 1, 1), max_value=date(2100, 12, 31))
        ora_v = c2.text_input("Orario (facoltativo)", value=v.get("ora", ""), placeholder="es. 09:30")
        cat = st.selectbox("🩺 Specialità", opzioni, index=opzioni.index(area_att) if area_att in opzioni else len(opzioni) - 1, format_func=lambda x: f"{CAT_ICONE.get(x, '🩺')} {x}")
        nuova = st.text_input("Se la specialità non c'è, scrivila qui", placeholder="es. Medicina estetica")
        tp_att = v.get("tipo_prestazione") or tp_sugg
        opz_t = [""] + list(CAT_TIPI)
        tipo_p = st.selectbox("🧭 Tipo di prestazione", opz_t, index=opz_t.index(tp_att) if tp_att in opz_t else 0, format_func=lambda x: "— non so —" if not x else x)
        prest = st.text_input("Che visita o che esame (facoltativo)", value=v.get("prestazione", ""), placeholder="es. Ecocardiogramma, Visita di controllo")
        medico = st.text_input("Medico, specialista o struttura", value=v.get("medico", ""))
        motivo = st.text_input("Motivo della visita o dell'esame", value=v.get("motivo", ""))
        controlli = st.text_area("Indicazioni per i controlli successivi", value=v.get("controlli", ""))
        prossimo = st.date_input("Data del prossimo appuntamento (facoltativa)", value=_fa_data(v.get("prossimo")), format="DD/MM/YYYY", min_value=date(1950, 1, 1), max_value=date(2100, 12, 31))
        note = st.text_area("Note personali", value=v.get("note", ""))
        if v.get("allegati"):
            st.caption(f"Documenti già allegati: {len(v['allegati'])} (si aprono ed eliminano dalla scheda).")
        st.caption("📎 Per allegare un referto o un esame, dopo aver salvato usa **Carica un referto, un esame o una ricetta (lo leggo io)**: lo leggo e lo metto nella stessa specialità.")
        nuovi = st.file_uploader("Oppure allega qui: scatta una foto o scegli PDF e immagini", type=TIPI_FILE, accept_multiple_files=True)
        inviato = st.form_submit_button("Salva", type="primary")
    if inviato:
        categoria = nuova.strip() or cat
        try:
            riferimenti = _fa_salva_files(nuovi, next((x_.get("allegati") or [] for x_ in _fa_dati().get("visite", []) if x_["id"] == vis_id), [])) if nuovi else []
            if not vis_id and v.get("_allegato") is not None:                                    # il documento letto resta allegato alla visita
                riferimenti = riferimenti + _fa_salva_files([v["_allegato"]], riferimenti)
        except ValueError as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(f"Non sono riuscito a salvare i documenti: {e}")
            return
        rec = {"profilo": pid, "data": data_v.isoformat(), "ora": ora_v.strip(), "categoria": categoria, "tipo_prestazione": tipo_p, "prestazione": prest.strip(),
               "medico": medico.strip(), "motivo": motivo.strip(), "controlli": controlli.strip(), "prossimo": prossimo.isoformat() if prossimo else None, "note": note.strip()}

        def _scrivi(f):
            f.setdefault("visite", [])
            if nuova.strip() and categoria not in CAT_AREE and categoria not in (f.get("categorie_extra") or []):
                f.setdefault("categorie_extra", []).append(categoria)
            if vis_id:
                for x in f["visite"]:
                    if x["id"] == vis_id:
                        x.update(rec)
                        x["allegati"] = (x.get("allegati") or []) + riferimenti
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                rec["allegati"] = riferimenti
                f["visite"].append(rec)
        try:
            _fa_salva(_scrivi, "Salute: visita")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Visita salvata."
        if not vis_id and callable(v.get("_dopo")):
            v["_dopo"]()
        st.rerun()


def _sp_storico_specialita(f, pid, nomi, p):
    """Una linguetta per ogni specialità: dentro, in ordine di data, le visite e i documenti (referti, esami, ricette) di quella specialità."""
    visite = [v for v in f.get("visite", []) if v.get("profilo", "p0") == pid]
    docs = [d for d in p.get("docsan", [])]
    gruppi = {}
    for v in visite:
        area = cat_unifica_visita(v.get("categoria"))[0]
        if area not in CAT_AREE:                                                   # un nome scritto a mano («Cardiologo») si collega alla specialità giusta
            area = cat_area_da_nome(area) or area
        area = area or "Senza specialità"
        gruppi.setdefault(area, []).append(("visita", v.get("data", ""), v))
    for d in docs:
        gruppi.setdefault(d.get("specialita") or "Senza specialità", []).append(("doc", d.get("data", ""), d))
    if not gruppi:
        st.info("Ancora niente da mostrare: aggiungi una visita o carica un referto.")
        return
    vedi = st.session_state.setdefault("sp_vedi", [])
    ordine = sorted(gruppi, key=lambda k: (k.startswith("Senza"), k))
    for area in ordine:
        voci = sorted(gruppi[area], key=lambda x: x[1], reverse=True)
        nv, nd = sum(1 for x in voci if x[0] == "visita"), sum(1 for x in voci if x[0] == "doc")
        with st.expander(f"{CAT_ICONE.get(area, '🩺')} {area} · {nv} {'visita' if nv == 1 else 'visite'} · {nd} {'documento' if nd == 1 else 'documenti'}"):
            anno = None
            for tipo, data_, x in voci:
                if (data_ or "")[:4] != anno:
                    anno = (data_ or "")[:4]
                    st.markdown(f"**📅 {anno or 'Senza data'}**")
                if tipo == "visita":
                    _sp_card_visita(x, pid, nomi)
                else:
                    _sp_riga_docsan(x, pid, f, p, vedi)


def _fa_tab_visite(f, pid, nomi, oggi_):                                         # noqa: F811
    """La scheda Visite: stesse specialità dei documenti, tipo di prestazione, ricerca, e lo STORICO PER SPECIALITÀ."""
    if not st.session_state.get("sp_mig_vis"):                                    # una volta sola: le categorie di prima passano al catalogo (le visite non si perdono)
        st.session_state["sp_mig_vis"] = True
        try:
            if _sp_migra_visite_dati(dict(f, visite=[dict(x) for x in f.get("visite", [])])):
                _fa_salva(_sp_migra_visite_dati, "Salute: specialità delle visite unificate")
                f = _fa_dati()
        except Exception:
            pass
    if st.button("📎 Carica un referto, un esame o una ricetta (lo leggo io)", key=f"sp_vis_carica_{pid}", width="stretch"):
        _sp_vai_docsan(pid)
    vista = st.radio("Come vuoi vederle", ["📇 Le visite", "📚 Storico per specialità"], horizontal=True, key=f"sp_vis_vista_{pid}", label_visibility="collapsed")
    visite = [v for v in f.get("visite", []) if v.get("profilo", "p0") == pid]
    for v in visite:                                                              # in sicurezza anche per la sola visualizzazione
        nuova, tp = cat_unifica_visita(v.get("categoria"))
        v["categoria"] = nuova
        if tp and not v.get("tipo_prestazione"):
            v["tipo_prestazione"] = tp
    if vista.startswith("📚"):
        if st.button("➕ Aggiungi visita o esame", type="primary", key="fa_nuova_vis", width="stretch"):
            _fa_dialogo_visita(pid)
        _sp_storico_specialita(f, pid, nomi, _sp_profilo(f, pid))
        return
    prossimi = sorted([v for v in visite if v.get("prossimo") and v["prossimo"] >= oggi_.isoformat()], key=lambda v: v["prossimo"])[:5]
    if prossimi:
        st.subheader("📅 Prossimi appuntamenti")
        for v in prossimi:
            st.markdown(f"• **{data_it(v['prossimo'])}** · {_h.escape(v.get('categoria', ''))}" + (f" · {_h.escape(v['medico'])}" if v.get("medico") else ""))
    if st.button("➕ Aggiungi visita o esame", type="primary", key="fa_nuova_vis", width="stretch"):
        _fa_dialogo_visita(pid)
    c1, c2, c3 = st.columns([3, 2, 2])
    cerca = c1.text_input("Cerca", placeholder="medico, motivo, note…", label_visibility="collapsed", key="fa_cerca_vis")
    presenti = sorted({v.get("categoria", "") for v in visite if v.get("categoria")})
    cat = c2.selectbox("Specialità", ["Tutte le specialità"] + presenti, label_visibility="collapsed", key="fa_cat_vis")
    tipi_pres = sorted({v.get("tipo_prestazione", "") for v in visite if v.get("tipo_prestazione")})
    tpf = c3.selectbox("Tipo", ["Tutti i tipi"] + tipi_pres, label_visibility="collapsed", key="fa_tp_vis")
    visibili = []
    for v in sorted(visite, key=lambda v: (v.get("data", ""), v.get("ora", "")), reverse=True):
        testo = " ".join(str(v.get(k, "")) for k in ("categoria", "tipo_prestazione", "prestazione", "medico", "motivo", "note", "controlli")).lower()
        if cerca and cerca.lower() not in testo:
            continue
        if cat != "Tutte le specialità" and v.get("categoria") != cat:
            continue
        if tpf != "Tutti i tipi" and v.get("tipo_prestazione") != tpf:
            continue
        visibili.append(v)
    if not visite:
        st.info(f"Nessuna visita o esame per {nomi[pid]}. Tocca «Aggiungi visita o esame».")
    elif not visibili:
        st.info("Nessun risultato.")
    for v in visibili:
        _sp_card_visita(v, pid, nomi)


_fa_tab_prescrizioni_originale = _fa_tab_prescrizioni


def _fa_tab_prescrizioni(f, pid, nomi, oggi_):                                   # noqa: F811
    if st.button("📎 Carica una ricetta o un'impegnativa (la leggo io)", key=f"sp_pre_carica_{pid}", width="stretch"):
        _sp_vai_docsan(pid)
    return _fa_tab_prescrizioni_originale(f, pid, nomi, oggi_)


# ---------------------------------------------------------------------------------------------------------------------
# 7) PARAMETRI E VALORI NEL TEMPO (pressione, glicemia, peso, febbre, colesterolo…)
# ---------------------------------------------------------------------------------------------------------------------
_SP_PARAMETRI = {"Pressione": "mmHg", "Glicemia": "mg/dl", "Peso": "kg", "Temperatura": "°C", "Frequenza cardiaca": "battiti/min", "Saturazione": "%", "Colesterolo totale": "mg/dl",
                 "Colesterolo LDL": "mg/dl", "Colesterolo HDL": "mg/dl", "Trigliceridi": "mg/dl", "Emoglobina glicata": "mmol/mol", "Creatinina": "mg/dl", "Altro": ""}


def sp_svg_linee(serie, unita):
    """Grafico a linee (SVG) di una o due serie: [(etichetta, colore, [(data_iso, valore)])]."""
    serie = [(e_, c_, [(d_, v_) for d_, v_ in pts if v_ is not None]) for e_, c_, pts in serie]
    serie = [x for x in serie if len(x[2]) >= 2]
    if not serie:
        return ""
    tutti = [(date.fromisoformat(d_).toordinal(), v_) for _, _, pts in serie for d_, v_ in pts]
    x0, x1, y0, y1 = min(x for x, _ in tutti), max(x for x, _ in tutti), min(y for _, y in tutti), max(y for _, y in tutti)
    x1 = x1 if x1 > x0 else x0 + 1
    y1 = y1 if y1 > y0 else y0 + 1
    W, H, M = 330, 160, 30
    px = lambda x: M + (x - x0) / (x1 - x0) * (W - 2 * M)
    py = lambda y: H - M - (y - y0) / (y1 - y0) * (H - 2 * M)
    parti = []
    for i, (e_, c_, pts) in enumerate(serie):
        xy = [(px(date.fromisoformat(d_).toordinal()), py(v_)) for d_, v_ in pts]
        parti.append(f"<polyline points='{' '.join(f'{a:.1f},{b:.1f}' for a, b in xy)}' fill='none' stroke='{c_}' stroke-width='2'/>" + "".join(f"<circle cx='{a:.1f}' cy='{b:.1f}' r='3' fill='{c_}'/>" for a, b in xy)
                     + f"<text x='{M + i * 90}' y='12' font-size='10' fill='{c_}'>{_h.escape(e_)}</text>")
    d_prima, d_ultima = min(d_ for _, _, pts in serie for d_, _ in pts), max(d_ for _, _, pts in serie for d_, _ in pts)
    return (f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' style='width:100%;max-width:440px;background:#fff;border-radius:10px'>{''.join(parti)}"
            f"<text x='4' y='{H - M + 12}' font-size='9' fill='#444'>min {y0:g} · max {y1:g} {_h.escape(unita)}</text><text x='{M}' y='{H - 6}' font-size='9' fill='#444'>{_sp_data_it(d_prima)}</text>"
            f"<text x='{W - M - 52}' y='{H - 6}' font-size='9' fill='#444'>{_sp_data_it(d_ultima)}</text></svg>")


def _sp_fmt_param(m):
    if m.get("tipo") == "Pressione" and m.get("valore2"):
        return f"{_sp_fmt_num(m.get('valore'))}/{_sp_fmt_num(m.get('valore2'))}"
    return _sp_fmt_num(m.get("valore"))


def sp_ultimi_parametri(p, n=1):
    """Gli ultimi valori per tipo: [(nome, unita, data, valore)]."""
    out = []
    per_tipo = {}
    for m in sorted(p.get("parametri", []), key=lambda x: x.get("data", "")):
        per_tipo.setdefault(m.get("nome") or m.get("tipo"), []).append(m)
    for nome, lista in per_tipo.items():
        u = lista[-1].get("unita") or _SP_PARAMETRI.get(lista[-1].get("tipo"), "")
        out.append((nome, u, lista[-1].get("data", ""), _sp_fmt_param(lista[-1])))
    return out


def _sp_dialogo_togli_param(pid, mid, testo):
    def _finestra():
        st.warning(f"Togliere questo valore?\n\n**{_sp_e(testo)}**")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"sp_pt_si_{mid}", type="primary", width="stretch"):
            _sp_salva_profilo(pid, lambda pr: pr.__setitem__("parametri", [x for x in pr.get("parametri", []) if x.get("id") != mid]), "Salute: valore tolto")
            st.rerun()
        if s2.button("No, tienilo", key=f"sp_pt_no_{mid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina il valore")(_finestra)()


def _sp_form_param(pid, m=None, tipo_pre=None):
    m = m or {}
    with st.form(f"sp_form_param_{m.get('id', 'nuovo')}", border=False):
        tipi = list(_SP_PARAMETRI)
        tipo = st.selectbox("Cosa hai misurato", tipi, index=tipi.index(m.get("tipo") or tipo_pre) if (m.get("tipo") or tipo_pre) in tipi else 0)
        nome = st.text_input("Se «Altro», come si chiama", value=m.get("nome", "") if m.get("tipo") == "Altro" else "")
        c1, c2 = st.columns(2)
        try:
            d0 = date.fromisoformat(m["data"]) if m.get("data") else _sp_oggi()
        except ValueError:
            d0 = _sp_oggi()
        data = c1.date_input("Data", value=d0, min_value=date(1990, 1, 1), max_value=_sp_oggi(), format="DD/MM/YYYY")
        val = c2.text_input("Valore (per la pressione: la massima)", value=_sp_fmt_num(m.get("valore")) if m.get("valore") else "")
        val2 = st.text_input("Solo pressione: la minima", value=_sp_fmt_num(m.get("valore2")) if m.get("valore2") else "")
        unita = st.text_input("Unità (se vuoi cambiarla)", value=m.get("unita", ""), placeholder="lascia vuoto per quella solita")
        nota = st.text_input("Note (a digiuno, dopo la corsa, con la febbre…)", value=m.get("nota", ""))
        ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
    if ok:
        n1, n2 = _sp_num(val), _sp_num(val2)
        if n1 is None:
            st.error("Scrivi il valore (un numero).")
            return
        if tipo == "Altro" and not nome.strip():
            st.error("Scrivi come si chiama.")
            return
        nuovo = {"id": m.get("id") or uuid.uuid4().hex[:8], "tipo": tipo, "nome": (nome.strip() if tipo == "Altro" else tipo), "data": data.isoformat(), "valore": f"{n1:g}",
                 "valore2": (f"{n2:g}" if (tipo == "Pressione" and n2 is not None) else ""), "unita": unita.strip(), "nota": nota.strip()}
        _sp_salva_profilo(pid, lambda pr, nv=nuovo: pr.__setitem__("parametri", [x for x in pr.get("parametri", []) if x.get("id") != nv["id"]] + [nv]), "Salute: parametri")
        st.session_state.pop("sp_param_mod", None)
        st.session_state["fa_msg"] = "✅ Valore salvato."
        st.rerun()


def sp_modulo_parametri(pid):
    f, p = _sp_intestazione("📈 Parametri e valori", pid)
    st.caption("Pressione, glicemia, peso, febbre, colesterolo… con la data: vedi come cambiano nel tempo. Sono tuoi appunti: per capire se un valore va bene chiedi al medico.")
    lista = list(p.get("parametri", []))
    with st.expander("➕ Aggiungi un valore", expanded=not lista):
        _sp_form_param(pid)
    if not lista:
        st.info("Ancora nessun valore registrato.")
        return
    nomi = sorted({m.get("nome") or m.get("tipo") for m in lista})
    scelto = st.selectbox("Che valore vuoi vedere", nomi, key=f"sp_param_sel_{pid}")
    voci = sorted([m for m in lista if (m.get("nome") or m.get("tipo")) == scelto], key=lambda x: x.get("data", ""))
    unita = voci[-1].get("unita") or _SP_PARAMETRI.get(voci[-1].get("tipo"), "")
    st.markdown(f"**Ultimo valore:** {_sp_fmt_param(voci[-1])} {unita} · {_sp_data_it(voci[-1].get('data'))}")
    if voci[-1].get("tipo") == "Pressione":
        svg = sp_svg_linee([("massima", "#c62828", [(m["data"], _sp_num(m.get("valore"))) for m in voci]), ("minima", "#1565c0", [(m["data"], _sp_num(m.get("valore2"))) for m in voci])], unita)
    else:
        svg = sp_svg_linee([(scelto, "#00796b", [(m["data"], _sp_num(m.get("valore"))) for m in voci])], unita)
    if svg:
        st.markdown(svg, unsafe_allow_html=True)
    else:
        st.caption("Con almeno due valori compare il grafico.")
    for m in reversed(voci):
        testo = f"{_sp_data_it(m.get('data'))} · {_sp_fmt_param(m)} {m.get('unita') or _SP_PARAMETRI.get(m.get('tipo'), '')}" + (f" · {m['nota']}" if m.get("nota") else "")
        st.markdown(f"<div class='sp-card'>{_sp_e(testo)}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        if c1.button("✏️ Modifica", key=f"sp_pe_{m['id']}", width="stretch"):
            st.session_state["sp_param_mod"] = None if st.session_state.get("sp_param_mod") == m["id"] else m["id"]
            st.rerun()
        if c2.button("🗑️ Elimina", key=f"sp_pt_{m['id']}", width="stretch"):
            _sp_dialogo_togli_param(pid, m["id"], testo)
        if st.session_state.get("sp_param_mod") == m["id"]:
            _sp_form_param(pid, m)
    righe = "".join(f"<tr><td>{_sp_data_it(m.get('data'))}</td><td>{_sp_e(m.get('nome') or m.get('tipo'))}</td><td>{_sp_e(_sp_fmt_param(m))} {_sp_e(m.get('unita') or _SP_PARAMETRI.get(m.get('tipo'), ''))}</td><td>{_sp_e(m.get('nota'))}</td></tr>"
                    for m in sorted(lista, key=lambda x: (x.get("nome") or x.get("tipo") or "", x.get("data", ""))))
    html_str = (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><title>Parametri di {_sp_e(p.get('nome'))}</title><style>{_SP_STILE}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #999;padding:3px 5px}}</style></head>"
                f"<body><h1>Parametri e valori · {_sp_e(p.get('nome'))}</h1><div class='box'>Aggiornato il {_sp_data_it(_sp_oggi().isoformat())}</div><table><tr><th>Data</th><th>Cosa</th><th>Valore</th><th>Note</th></tr>{righe}</table>"
                "<p class='nota'>Appunti inseriti dall'utente, non certificati da un medico.</p></body></html>")
    nome_file = f"parametri_{re.sub(r'[^A-Za-z0-9]+', '_', p.get('nome', '')) or 'persona'}_{_sp_oggi().isoformat()}"
    st.download_button("📄 Scarica la tabella (da stampare o salvare come PDF)", html_str.encode("utf-8"), file_name=nome_file + ".html", mime="text/html", width="stretch")
    pdf = sp_pdf_da_html(html_str)
    if pdf:
        st.download_button("📕 Scarica il PDF", pdf, file_name=nome_file + ".pdf", mime="application/pdf", width="stretch")
    if "inv_voce" in globals():
        inv_voce(f"sp_param_{pid}", "📤 Invia i valori", f"Parametri di {p.get('nome', '')}", "\n".join(f"• {n}: {v_} {u} ({_sp_data_it(d_)})" for n, u, d_, v_ in sp_ultimi_parametri(p)),
                 lambda: ([(nome_file + ".pdf", "application/pdf", pdf)] if pdf else [(nome_file + ".html", "text/html", html_str.encode("utf-8"))]))



# ---------------------------------------------------------------------------------------------------------------------
# 8) CONTROLLI PERIODICI (dentista, vista, vaccini…) con avviso
# ---------------------------------------------------------------------------------------------------------------------
_SP_IDEE_CONTROLLI = [("Visita dal dentista e igiene orale", 6), ("Visita pediatrica o bilancio di salute (bambini)", 6), ("Controllo della vista (oculista)", 24), ("Esami del sangue di controllo", 12),
                      ("Controllo della pressione dal medico", 12), ("Vaccino antinfluenzale", 12), ("Richiamo antitetanico", 120), ("Visita cardiologica di controllo", 12),
                      ("Controllo dei nei (dermatologo)", 12), ("Controllo della glicemia", 12), ("Pap test o HPV (donne)", 36), ("Mammografia (donne, secondo l'età)", 24),
                      ("Ricerca del sangue occulto nelle feci (screening del colon)", 24), ("Controllo di un impianto o dispositivo (pacemaker, ecc.)", 12), ("Altro (lo scrivo io)", 12)]


def sp_aggiungi_mesi(d, n):
    m = d.month - 1 + int(n)
    a, me = d.year + m // 12, m % 12 + 1
    giorni = [31, 29 if (a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][me - 1]
    return date(a, me, min(d.day, giorni))


def sp_controllo_prossimo(c):
    """La data del prossimo controllo: quella scritta a mano oppure l'ultimo fatto + ogni quanti mesi. None se non si può calcolare."""
    try:
        if c.get("prossimo"):
            return date.fromisoformat(c["prossimo"])
        if c.get("ultimo") and int(c.get("ogni_mesi") or 0) > 0:
            return sp_aggiungi_mesi(date.fromisoformat(c["ultimo"]), int(c["ogni_mesi"]))
    except (ValueError, TypeError):
        pass
    return None


def sp_controlli_scadenti(p, oggi_=None, entro=30):
    """I controlli già scaduti o in scadenza entro N giorni: [(giorni, controllo)]."""
    oggi_ = oggi_ or _sp_oggi()
    out = []
    for c in p.get("controlli", []):
        pr = sp_controllo_prossimo(c)
        if pr and (pr - oggi_).days <= entro:
            out.append(((pr - oggi_).days, c))
    return sorted(out, key=lambda x: x[0])


def _sp_dialogo_togli_controllo(pid, cid, nome):
    def _finestra():
        st.warning(f"Togliere il promemoria **{_sp_e(nome)}**?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"sp_ct_si_{cid}", type="primary", width="stretch"):
            _sp_salva_profilo(pid, lambda pr: pr.__setitem__("controlli", [x for x in pr.get("controlli", []) if x.get("id") != cid]), "Salute: controllo tolto")
            st.rerun()
        if s2.button("No, tienilo", key=f"sp_ct_no_{cid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina il promemoria")(_finestra)()


def _sp_form_controllo(pid, c=None):
    c = c or {}
    nomi = [x[0] for x in _SP_IDEE_CONTROLLI]
    with st.form(f"sp_form_ctrl_{c.get('id', 'nuovo')}", border=False):
        idea = st.selectbox("Che controllo è", nomi, index=nomi.index(c["nome"]) if c.get("nome") in nomi else (len(nomi) - 1 if c.get("nome") else 0))
        libero = st.text_input("Se «Altro», scrivi quale", value=c.get("nome", "") if c.get("nome") not in nomi else "")
        ogni = st.number_input("Ogni quanti mesi", min_value=1, max_value=240, value=int(c.get("ogni_mesi") or dict(_SP_IDEE_CONTROLLI).get(idea, 12)), step=1,
                               help="Per esempio 6 = ogni sei mesi, 12 = ogni anno, 24 = ogni due anni. Chiedi al medico ogni quanto serve a te.")
        c1, c2 = st.columns(2)
        try:
            u0 = date.fromisoformat(c["ultimo"]) if c.get("ultimo") else None
        except ValueError:
            u0 = None
        ultimo = c1.date_input("L'ultima volta", value=u0, min_value=date(1990, 1, 1), max_value=_sp_oggi(), format="DD/MM/YYYY")
        try:
            p0 = date.fromisoformat(c["prossimo"]) if c.get("prossimo") else None
        except ValueError:
            p0 = None
        prossimo = c2.date_input("Oppure: la prossima data già fissata", value=p0, format="DD/MM/YYYY")
        avvisa = st.checkbox("🔔 Avvisami sul telefono quando si avvicina", value=c.get("avvisa", True))
        note = st.text_input("Note", value=c.get("note", ""))
        ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
    if ok:
        nome = libero.strip() if idea.startswith("Altro") else idea
        if not nome:
            st.error("Scrivi che controllo è.")
            return
        if not (ultimo or prossimo):
            st.error("Scrivi l'ultima volta oppure la prossima data già fissata, così so quando avvisarti.")
            return
        nuovo = {"id": c.get("id") or uuid.uuid4().hex[:8], "nome": nome, "ogni_mesi": int(ogni), "ultimo": ultimo.isoformat() if ultimo else "", "prossimo": prossimo.isoformat() if prossimo else "",
                 "avvisa": bool(avvisa), "note": note.strip()}
        _sp_salva_profilo(pid, lambda pr, nv=nuovo: pr.__setitem__("controlli", [x for x in pr.get("controlli", []) if x.get("id") != nv["id"]] + [nv]), "Salute: controllo periodico")
        st.session_state.pop("sp_ctrl_mod", None)
        st.session_state["fa_msg"] = "✅ Promemoria salvato."
        st.rerun()


def sp_modulo_controlli(pid):
    f, p = _sp_intestazione("⏰ Controlli periodici", pid)
    st.caption("Dentista, vista, vaccini, esami di controllo… scrivi l'ultima volta e ogni quanti mesi: ti dico quando tocca e ti avviso sul telefono. "
               "I tempi giusti dipendono da età, sesso e storia clinica, e da cosa offre la tua Regione: **chiedi al medico**; quelli proposti sono solo idee comuni.")
    lista = list(p.get("controlli", []))
    oggi_ = _sp_oggi()
    for c in sorted(lista, key=lambda x: (sp_controllo_prossimo(x) or date(2999, 1, 1))):
        pr = sp_controllo_prossimo(c)
        g = (pr - oggi_).days if pr else None
        stato = "⚪ senza data" if g is None else (f"🔴 in ritardo di {-g} giorni" if g < 0 else "🟠 oggi" if g == 0 else f"🟠 tra {g} giorni" if g <= 30 else f"🟢 tra {g} giorni")
        righe = " · ".join(x for x in (f"ogni {c.get('ogni_mesi')} mesi" if c.get("ogni_mesi") else "", f"ultima volta {_sp_data_it(c['ultimo'])}" if c.get("ultimo") else "",
                                      f"prossima {_sp_data_it(pr.isoformat())}" if pr else "", "🔔 avviso acceso" if c.get("avvisa", True) else "🔕 senza avviso") if x)
        st.markdown(f"<div class='sp-card'><b>{_sp_e(c.get('nome'))}</b> · {stato}<br><small>{_sp_e(righe)}</small>" + (f"<br><small>{_sp_e(c.get('note'))}</small>" if c.get("note") else "") + "</div>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3, gap="small")
        if b1.button("✅ Fatto oggi", key=f"sp_cf_{c['id']}", width="stretch"):
            _sp_salva_profilo(pid, lambda pr_, cid=c["id"]: [x.update({"ultimo": oggi_.isoformat(), "prossimo": ""}) for x in pr_.get("controlli", []) if x.get("id") == cid], "Salute: controllo fatto")
            st.session_state["fa_msg"] = "✅ Segnato come fatto oggi: calcolo la prossima data."
            st.rerun()
        if b2.button("✏️ Modifica", key=f"sp_ce_{c['id']}", width="stretch"):
            st.session_state["sp_ctrl_mod"] = None if st.session_state.get("sp_ctrl_mod") == c["id"] else c["id"]
            st.rerun()
        if b3.button("🗑️ Elimina", key=f"sp_ctt_{c['id']}", width="stretch"):
            _sp_dialogo_togli_controllo(pid, c["id"], c.get("nome", ""))
        if st.session_state.get("sp_ctrl_mod") == c["id"]:
            _sp_form_controllo(pid, c)
    with st.expander("➕ Aggiungi un controllo", expanded=not lista):
        _sp_form_controllo(pid)
    if lista:
        righe_t = []
        for c in sorted(lista, key=lambda x: (sp_controllo_prossimo(x) or date(2999, 1, 1))):
            pr = sp_controllo_prossimo(c)
            righe_t.append((c.get("nome", ""), f"ogni {c.get('ogni_mesi')} mesi" if c.get("ogni_mesi") else "", _sp_data_it(c.get("ultimo")), _sp_data_it(pr.isoformat()) if pr else "", c.get("note", "")))
        html_c = (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><title>Controlli periodici di {_sp_e(p.get('nome'))}</title><style>{_SP_STILE}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #999;padding:3px 5px}}</style></head>"
                  f"<body><h1>Controlli periodici · {_sp_e(p.get('nome'))}</h1><div class='box'>Aggiornato il {_sp_data_it(oggi_.isoformat())}</div><table><tr><th>Controllo</th><th>Frequenza</th><th>Ultima volta</th><th>Prossima</th><th>Note</th></tr>"
                  + "".join("<tr>" + "".join(f"<td>{_sp_e(x)}</td>" for x in r) + "</tr>" for r in righe_t) + "</table></body></html>")
        nome_c = f"controlli_{re.sub(r'[^A-Za-z0-9]+', '_', p.get('nome', '')) or 'persona'}_{oggi_.isoformat()}"
        st.download_button("📄 Scarica l'elenco (da stampare o salvare come PDF)", html_c.encode("utf-8"), file_name=nome_c + ".html", mime="text/html", width="stretch", key=f"sp_ctrl_dl_{pid}")
        if "inv_voce" in globals():
            inv_voce(f"sp_ctrl_inv_{pid}", "📤 Invia l'elenco dei controlli", f"Controlli periodici di {p.get('nome', '')}", "\n".join(f"• {r[0]}: prossima {r[3] or '—'} ({r[1]})" for r in righe_t), [])


# ---------------------------------------------------------------------------------------------------------------------
# agganci alla sezione Salute (senza cambiare niente di quello che c'era)
# ---------------------------------------------------------------------------------------------------------------------
if "_fa_modulo_tessera" in globals() and "_sp_tessera_prima" not in globals():
    _sp_tessera_prima = _fa_modulo_tessera

    def _fa_modulo_tessera(pid):                                    # noqa: F811
        try:
            return _sp_modulo_tessera(pid)
        except Exception as ex:
            st.warning(f"La nuova pagina non si apre ({type(ex).__name__}): ti mostro quella di prima.")
            return _sp_tessera_prima(pid)

if "_fa_riga_profilo" in globals() and "_sp_riga_prima" not in globals():
    _sp_riga_prima = _fa_riga_profilo

    def _fa_riga_profilo(profili, pid, nome, gruppo):                # noqa: F811
        _sp_riga_prima(profili, pid, nome, gruppo)
        try:
            sp_riga_azioni(pid)
        except Exception as ex:
            st.caption(f"(I pulsanti Medici, Emergenza, Scheda non si aprono: {type(ex).__name__})")

if "schermata_farmacia" in globals() and "_sp_schermata_prima" not in globals():
    _sp_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        m = st.session_state.get("sp_modulo")
        if m and not st.session_state.get("sezione_home") and not st.session_state.get("fa_famiglia"):
            if "_FA_CSS" in globals():
                st.markdown(_FA_CSS, unsafe_allow_html=True)
            if "nav_barra" in globals():
                nav_barra("salute")
            if st.session_state.get("fa_msg"):
                _msg = st.session_state.pop("fa_msg")
                (st.warning if _msg.startswith("⚠️") else st.success)(_msg)
            try:
                _sp_dispatch(m)
            except Exception as ex:
                st.error(f"Non riesco ad aprire questa pagina ({type(ex).__name__}). Torna a Salute e riprova.")
                if st.button("← Torna a Salute", key="sp_errore_indietro"):
                    st.session_state.pop("sp_modulo", None)
                    st.rerun()
            return
        return _sp_schermata_prima()

try:                                                                 # lasciando una sezione, la pagina aperta si chiude
    if "_STATI_DA_CHIUDERE" in globals() and "sp_modulo" not in _STATI_DA_CHIUDERE:
        _STATI_DA_CHIUDERE = list(_STATI_DA_CHIUDERE) + ["sp_modulo"]
except Exception:
    pass


# ---------------------------------------------------------------------------------------------------------------------
# la guida «Informazioni» della Salute: le novità (solo italiano, le altre lingue a lavoro finito)
# ---------------------------------------------------------------------------------------------------------------------
_SP_GUIDA = [
    ("s_emerg", "🆘 Dati per l'emergenza e scheda per il medico",
     """Ogni persona ha, sotto i riquadri, quattro pulsanti colorati.
**🆘 Dati per l'emergenza**: scrivi la data di nascita, gli **impianti** (pacemaker, bypass, stent, protesi), le terapie importanti (**anticoagulanti**, insulina…), le **allergie** (anche a cibi e lattice) e **chi chiamare**. Tocca **💾 Salva**.
**📄 Scheda per il medico**: l'app mette insieme tutto quello che sa della persona e lo scrive in una scheda: in alto gli **avvisi rossi** (allergie, impianti, terapie importanti), poi un racconto in breve, le patologie, gli interventi, le terapie, i vaccini, le visite, i documenti e gli ultimi valori. Si aggiorna da sola. La scarichi in **HTML o PDF** o la **invii** (email, WhatsApp, Telegram).
In fondo c'è l'elenco **📝 Per rendere la scheda più utile**: ti dice cosa manca.
Le informazioni sono quelle che inserisci tu: la scheda non è certificata da un medico. Non esce nessun dato dall'app, a meno che tu attivi la sintesi con intelligenza artificiale (facoltativa, solo con il consenso, senza nome e dati che identificano la persona).""",
     "emergenza scheda medico allergie pacemaker bypass anticoagulanti impianti protesi contatto pdf esporta racconto"),
    ("s_docsan", "🗂️ Documenti sanitari: li leggo io, tu confermi",
     """1. Apri **Salute** e tocca **🗂️ Documenti sanitari**.
2. Tocca il **pulsante arancione «📎 Scegli il PDF o il file»** (oppure **📷 Scatta foto** o **🖼️ Dalla galleria**) e scegli un referto, un esame, un'ecografia, una ricetta, una lettera di dimissione, un certificato.
3. Si apre **una finestra sopra la pagina**: ti propongo **di chi è**, **che documento è**, l'**area medica** (Cardiologia, Oculistica, Analisi di laboratorio…), il **tipo di prestazione** (visita, esame, terapia, screening, controllo), la **data dell'esame o della visita** (distinta da quella del referto), il medico, la struttura, gli **esami contenuti**, le **conclusioni copiate dal documento** e l'eventuale **controllo consigliato dal medico**. Sotto c'è scritto **perché** ho scelto quell'area. I pallini dicono quanto sono sicuro: 🟢 sicuro, 🟡 abbastanza, 🟠 poco.
4. **Controlli e correggi**, poi **✅ Conferma e archivia**. Non invento niente: se un dato non c'è nel documento, resta vuoto.
**Ritrovarli:** sotto, una **linguetta per ogni tipo di documento**, oppure **per specialità**, oppure **per anno** (scegli in alto). Tocca la linguetta: dentro vedi i documenti, con **👁️ Vedi / scarica**, **✏️ Modifica**, **📤 Invia** e **🗑️ Elimina**. C'è anche la ricerca.""",
     "documenti sanitari referto esame ecografia ricetta dimissione pulsante arancione specialita linguetta carica leggi conferma"),
    ("s_esenzioni", "🪪 Invalidità ed esenzioni",
     """In **Salute** tocca **🪪 Invalidità ed esenzioni** (in fondo ai bottoni). Qui tieni i documenti di **invalidità civile**, **Legge 104**, **indennità di accompagnamento**, **esenzioni ticket** (per patologia, per invalidità, per reddito/età/disoccupazione, per gravidanza), **contrassegno disabili**, **agevolazioni auto**.
1. Tocca il **pulsante arancione «📎 Scegli il PDF o il file»** (o scatta una foto). Lo leggo e ti propongo **tipo, codice dell'esenzione, percentuale di invalidità, ente, numero del verbale, date di validità e di revisione**. Quello che non trovo resta vuoto.
2. **Controlli e correggi**, poi **✅ Conferma e archivia**. Oppure **✍️ Aggiungi a mano** senza file.
3. Ogni tipo ha la sua **linguetta**: dentro, per ogni voce, **👁️ Vedi / scarica**, **✏️ Modifica**, **📤 Invia**, **🗑️ Elimina**. Se è **permanente** spunta «♾️ È permanente».
**Avvisi:** se una voce scade (o va rivista) entro 60 giorni, o è già scaduta, la Home lampeggia e Salute lo dice; con gli avvisi accesi ricevi anche il promemoria sui tuoi canali.""",
     "invalidita esenzione ticket legge 104 accompagnamento contrassegno disabili percentuale codice esenzione verbale scadenza revisione"),
    ("s_storico", "📚 Storico per specialità (Visite)",
     """Nella scheda **🩺 Visite** scegli **📚 Storico per specialità**: una linguetta per ogni specialità (Cardiologia, Oculistica…). Dentro trovi, **anno per anno**, le visite e i documenti di quella specialità (referti, esami, ricette): per esempio tutta la storia cardiologica in un posto solo.
In cima c'è **📎 Carica un referto, un esame o una ricetta (lo leggo io)**: ti porta ai Documenti sanitari.""", "storico specialita visite referti cardiologia anno linguetta"),
    ("s_profili", "✏️ Cambiare il nome di un profilo",
     """In **Salute → 👥 Gestisci profili** trovi **✏️ Cambia il nome dei profili aggiuntivi**: per ogni persona aggiunta c'è un campo con il suo nome. Scrivi il nuovo nome e tocca **💾**. Non puoi usare un nome già presente. Il tuo profilo non si rinomina da qui.""", "profilo nome cambiare rinominare persona gestisci profili"),
    ("s_medici", "👩‍⚕️ Medici e riferimenti (anche il pediatra)",
     """Tocca **👩‍⚕️ Medici e riferimenti**. In alto trovi il **medico di base** (la sua scheda completa è quella di prima). Sotto puoi aggiungere con **➕ Aggiungi un riferimento**: **pediatra**, specialisti, dentista, fisioterapista…, con studio, telefono, email, indirizzo, orari e sostituto.
Su ognuno: **📞 Chiama**, **✉️ Scrivi**, **✏️ Modifica**, **🗑️ Elimina**, **📤 Invia**. Per un bambino l'app ti ricorda di aggiungere il pediatra.""",
     "medici pediatra specialista dentista rubrica telefono orari riferimenti"),
    ("s_bimbo", "👶 Percorso del bambino",
     """Per un bambino, nei **🆘 Dati per l'emergenza** spunta **È un bambino o una bambina**: compare **👶 Percorso del bambino**.
Ha sei schede: **📏 Crescita** (peso e altezza con il grafico), **🧩 Tappe** (primo sorriso, primi passi, prime parole…), **🍼 Alimentazione**, **🤒 Malattie**, **🦷 Denti**, **🏥 Ricoveri**. Ogni voce si modifica e si toglie.
Le **visite dal pediatra** e i **vaccini** si segnano nelle schede 🩺 Visite e 💉 Vaccini. In fondo scarichi o invii il **libretto** (HTML o PDF).""",
     "bambino bimbo crescita peso altezza tappe pediatra libretto denti malattie febbre"),
    ("s_param", "📈 Parametri e valori",
     """Tocca **📈 Parametri e valori** e scrivi pressione (massima e minima), glicemia, peso, febbre, battiti, saturazione, colesterolo… con la **data**. Scegli quale valore guardare: vedi l'ultimo e il **grafico nel tempo**. Scarichi la tabella (HTML o PDF) o la invii.
L'app non dice se un valore va bene o no: chiedilo al medico.""",
     "parametri pressione glicemia peso febbre colesterolo grafico diario valori"),
    ("s_ctrl", "⏰ Controlli periodici",
     """Tocca **⏰ Controlli periodici** e aggiungi dentista, vista, esami del sangue, antinfluenzale… scrivendo **l'ultima volta** e **ogni quanti mesi**. Ti dico quando tocca (🟢 lontano, 🟠 vicino, 🔴 in ritardo) e, con **🔔 Avvisami**, ti avviso sul telefono: **30, 7 e 1 giorno prima**, il giorno stesso e ogni lunedì se sei in ritardo.
**✅ Fatto oggi** mette la data di oggi e calcola la prossima. I tempi giusti dipendono da te: chiedi al medico.""",
     "controlli periodici dentista vista vaccino antinfluenzale promemoria avviso scadenza"),
    ("s_tess", "🪪 Tessera, fascicolo sanitario e i documenti scaricati",
     """Tocca il riquadro **Tessera sanitaria · Fascicolo sanitario**. Sotto le tre voci (**fascicolo sanitario elettronico**, **vaccinazioni**, **spese sanitarie detraibili**) c'è il **link** da salvare e, sotto, **📎 Il documento scaricato**: carichi il PDF o la foto che hai già scaricato dal sito, poi lo **vedi**, lo **scarichi**, lo **invii** o lo **togli**.""",
     "tessera sanitaria fascicolo sanitario elettronico vaccinazioni spese detraibili documento scaricato pdf"),
]
if "_GUIDE" in globals() and "farmacia" in _GUIDE and "_ID_GUIDA" in globals() and "s_emerg" not in _ID_GUIDA.get("farmacia", []) and len(_GUIDE["farmacia"]) == len(_ID_GUIDA.get("farmacia", [])):
    _GUIDE["farmacia"] = list(_GUIDE["farmacia"]) + [(t_, c_, k_) for _i, t_, c_, k_ in _SP_GUIDA]
    _ID_GUIDA["farmacia"] = list(_ID_GUIDA["farmacia"]) + [x[0] for x in _SP_GUIDA]
