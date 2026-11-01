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
from datetime import date, datetime

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
    st.dialog("🗑️ Togli il documento")(_finestra)()


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
            if b2.button("🗑️ Togli", key=f"sp_t_{r['id']}", width="stretch"):
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
        else:
            with st.form(f"fa_ts_form_{chiave}_{pid}"):
                nuovo = st.text_input(titolo, value=url, placeholder="incolla qui il link, per esempio https://…", label_visibility="collapsed")
                b1, b2 = st.columns(2)
                salva_b = b1.form_submit_button("💾 Salva il link", type="primary", width="stretch")
                togli_b = b2.form_submit_button("🗑️ Togli il link" if url else "Annulla", width="stretch")
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
    for premuto, vista in ((a, "medici"), (b, "critici"), (c, "scheda"), (d, "bambino")):
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
    {"medici": sp_modulo_medici, "critici": sp_modulo_critici, "scheda": sp_modulo_scheda, "bambino": sp_modulo_bambino}.get(vista, lambda _p: None)(pid)


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
    st.dialog("🗑️ Togli dalla rubrica")(_finestra)()


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
        if d1.button("🗑️ Togli", key=f"sp_med_t_{m['id']}", width="stretch"):
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
            "bambino_dati": p.get("bambino") or {}, "oggi": oggi_.isoformat()}


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
        baby = "<h2>Percorso del bambino</h2>" + sp_html_bambino_corpo(d["bambino_dati"])
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Scheda per il medico – {e(d['nome'])}</title>"
            f"<style>{_SP_STILE}</style></head><body><h1>Scheda sanitaria per il medico</h1><div class='box'><b>{e(anag)}</b><br>Aggiornata il {_sp_data_it(d['oggi'])}</div>"
            + "".join(f"<div class='al'>{e(a)}</div>" for a in avv)
            + f"<h2>Racconto in breve</h2><p>{e(racconto)}</p>{ai}"
            f"<h2>Chi chiamare in caso di emergenza</h2>{contatti}<h2>Medici e riferimenti</h2>{medici}"
            f"<h2>Patologie</h2>{lis(d['patologie'])}<h2>Interventi subiti</h2>{lis(d['interventi'])}"
            f"<h2>Storia clinica di rilievo</h2><p>{e(d['storia']).replace(chr(10), '<br>') or '<i>non indicata</i>'}</p>"
            + (f"<h2>Familiarità</h2><p>{e(d['famiglia']).replace(chr(10), '<br>')}</p>" if d["famiglia"] else "")
            + f"<h2>Terapie in corso</h2>{terapie}<h2>Vaccinazioni</h2>{vacc}<h2>Ultime visite</h2>{visite}"
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
            if ai_ok and st.button("🗑️ Togli la sintesi salvata", key=f"sp_ai_via_{pid}", width="stretch"):
                _sp_salva_profilo(pid, lambda pr: pr.__setitem__("sp", {k: v for k, v in (pr.get("sp") or {}).items() if k != "racconto_ai"}), "Salute: sintesi tolta")
                st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 5) PERCORSO DEL BAMBINO
# ---------------------------------------------------------------------------------------------------------------------
def sp_html_bambino_corpo(b):
    e = _sp_e
    def tab(titolo, righe, intest):
        if not righe:
            return ""
        return (f"<h3>{titolo}</h3><table border='1' cellpadding='3' cellspacing='0' style='border-collapse:collapse;width:100%'><tr>" + "".join(f"<th>{e(x)}</th>" for x in intest) + "</tr>"
                + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in righe) + "</table>")
    ms = sorted(b.get("misure", []), key=lambda x: x.get("data", ""))
    return (tab("Crescita", [[_sp_data_it(m.get("data")), _sp_fmt_num(m.get("peso")), _sp_fmt_num(m.get("altezza")), _sp_fmt_num(m.get("cranio")), m.get("nota", "")] for m in ms],
                ["Data", "Peso kg", "Altezza cm", "Cranio cm", "Note"])
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


def _sp_riassunto_voce(sez, v):
    if sez == "misure":
        return " · ".join(x for x in ((f"⚖️ {_sp_fmt_num(v.get('peso'))} kg" if v.get("peso") else ""), (f"📏 {_sp_fmt_num(v.get('altezza'))} cm" if v.get("altezza") else ""),
                                      (f"🧠 cranio {_sp_fmt_num(v.get('cranio'))} cm" if v.get("cranio") else "")) if x) or "—"
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
    st.dialog("🗑️ Togli la voce")(_finestra)()


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
        testo = f"{_sp_data_it(v.get('data'))} · {_sp_riassunto_voce(sez, v)}"
        st.markdown(f"<div class='sp-card'>{_sp_e(testo)}" + (f"<br><small>{_sp_e(v.get('nota'))}</small>" if v.get("nota") else "") + "</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        if c1.button("✏️ Modifica", key=f"sp_b_e_{v['id']}", width="stretch"):
            st.session_state[f"sp_bmod_{sez}"] = v["id"]
            st.rerun()
        if c2.button("🗑️ Togli", key=f"sp_b_t_{v['id']}", width="stretch"):
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
        for campo, unita in (("peso", "peso (kg)"), ("altezza", "altezza (cm)"), ("cranio", "circonferenza cranica (cm)")):
            svg = sp_svg_crescita(misure, campo, unita)
            if svg:
                st.markdown(svg, unsafe_allow_html=True)
        if len([m for m in misure if m.get("data")]) < 2:
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
    corpo = sp_html_bambino_corpo(p.get("bambino") or {})
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
