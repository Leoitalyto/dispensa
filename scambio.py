# -*- coding: utf-8 -*-
"""SCAMBIO DATI — un file da dare a un altro utente, che lo carica nella sua app.

Da Utilità → «📦 Scambia i dati con un altro utente» (e dal pulsante in fondo a ogni sezione):
  ESPORTA   scegli cosa mettere nel file: 🥫 Dispensa · 🩺 Salute (con I miei documenti e Archivio, che sono la stessa cartella) · 🏡 Casa · 💼 Lavoro.
            Il file (.dispensa) contiene i dati e, se vuoi, anche gli allegati originali (PDF, foto). Si può proteggere con una PASSWORD (consigliato: dentro ci sono dati personali e sanitari).
  IMPORTA   l'altro utente sceglie il file (con il pulsante arancione, che sul telefono funziona sempre), vede cosa contiene, spunta cosa vuole e lo AGGIUNGE alle sue cose:
            niente viene sostituito né cancellato; ogni voce prende un nuovo identificativo (nessun conflitto con le sue) e gli allegati vengono salvati di nuovo.
Formato: «DSP1» + («N» senza password | «P» con password) + dati compressi (zlib; con password: cifrati con Fernet, chiave da PBKDF2-SHA256).
Caricato da app_dispensa.py dopo lavoro.py."""
import base64
import json
import re
import secrets
import uuid
import zlib
from datetime import date, datetime

import streamlit as st

_SC_MAGIA = b"DSP1"
SC_SEZIONI = {
    "dispensa": ("🥫 Dispensa", "i tuoi prodotti e le scadenze"),
    "salute": ("🩺 Salute, 📁 I miei documenti, 🗂️ Archivio", "le persone, medicinali, terapie, visite, ricette, vaccini, i documenti personali e i loro file"),
    "casa": ("🏡 Casa", "beni, documenti, manutenzioni e riferimenti della casa"),
    "lavoro": ("💼 Lavoro", "buste paga, Certificazioni Uniche, documenti INPS, sindacato/CAF e link INPS"),
}


# ---------------------------------------------------------------------------------------------------------------------
# il pacchetto: cosa c'è dentro e come si cifra
# ---------------------------------------------------------------------------------------------------------------------
def _sc_lavoro_tipi():
    return globals().get("_CA_TIPI_LAVORO") or ("Busta paga", "Certificazione Unica (CU)", "Documento INPS")


def sc_estrai(d, sezione):
    """La parte dei dati dell'utente che appartiene a una sezione (copie, senza toccare l'originale)."""
    import copy
    if sezione == "dispensa":
        return {"articoli": copy.deepcopy(d.get("articoli") or [])}
    if sezione == "salute":
        return copy.deepcopy(d.get("farmacia") or {})
    c = d.get("casa") or {}
    tipi = _sc_lavoro_tipi()
    if sezione == "casa":
        docs = [x for x in c.get("documenti", []) if x.get("tipo") not in tipi]
        return copy.deepcopy({"beni": c.get("beni", []), "manutenzioni": c.get("manutenzioni", []), "documenti": docs, "contatti_casa": c.get("contatti_casa", [])})
    if sezione == "lavoro":
        docs = [x for x in c.get("documenti", []) if x.get("tipo") in tipi]
        out = {"documenti": docs, "contatti_lavoro": c.get("contatti_lavoro", []), "lavori": c.get("lavori", [])}
        if c.get("inps_link"):
            out["inps_link"] = c["inps_link"]
        return copy.deepcopy(out)
    return {}


def _sc_e_file(x):
    return isinstance(x, dict) and x.get("id") and ("mime" in x or "sha256" in x or re.search(r"\.[A-Za-z0-9]{2,5}$", str(x.get("nome") or "")))


def sc_ids_file(dati):
    """Gli identificativi dei file allegati (PDF, foto…) citati nei dati."""
    trovati = []

    def giu(x):
        if isinstance(x, dict):
            if _sc_e_file(x) and x["id"] not in trovati:
                trovati.append(x["id"])
            for v in x.values():
                giu(v)
        elif isinstance(x, list):
            for v in x:
                giu(v)
    giu(dati)
    return trovati


def sc_conta(dati):
    """Quante voci per elenco (per mostrare «5 medicinali, 3 documenti…»)."""
    out = {}
    for k, v in (dati or {}).items():
        if isinstance(v, list) and v:
            out[k] = len(v)
    return out


_SC_NOMI = {"articoli": "prodotti", "profili": "persone", "medicinali": "medicinali", "terapie": "terapie", "visite": "visite", "prescrizioni": "ricette", "vaccinazioni": "vaccinazioni",
            "documenti": "documenti", "archivio_foto": "foto", "beni": "beni", "manutenzioni": "interventi", "contatti_casa": "riferimenti", "contatti_lavoro": "contatti", "lavori": "lavori"}


def sc_riassunto(dati):
    c = sc_conta(dati)
    return ", ".join(f"{n} {_SC_NOMI.get(k, k)}" for k, n in c.items()) or "niente"


def _sc_chiave(password, sale):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sale, iterations=200_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def sc_impacchetta(pacchetto, password=""):
    """Da dizionario a byte del file .dispensa."""
    grezzo = zlib.compress(json.dumps(pacchetto, ensure_ascii=False).encode("utf-8"), 6)
    if not password:
        return _SC_MAGIA + b"N" + grezzo
    from cryptography.fernet import Fernet
    sale = secrets.token_bytes(16)
    return _SC_MAGIA + b"P" + sale + Fernet(_sc_chiave(password, sale)).encrypt(grezzo)


class ScambioErrore(Exception):
    pass


def sc_apri(dati, password=""):
    """Dai byte del file al dizionario. Solleva ScambioErrore con un messaggio chiaro."""
    if not dati or not dati.startswith(_SC_MAGIA) or len(dati) < 6:
        raise ScambioErrore("Questo non sembra un file di scambio della dispensa (deve finire con .dispensa).")
    modo, corpo = dati[4:5], dati[5:]
    try:
        if modo == b"P":
            if not password:
                raise ScambioErrore("Il file è protetto: scrivi la password.")
            from cryptography.fernet import Fernet, InvalidToken
            try:
                corpo = Fernet(_sc_chiave(password, corpo[:16])).decrypt(corpo[16:])
            except InvalidToken:
                raise ScambioErrore("La password non è quella giusta (o il file è danneggiato).")
        elif modo != b"N":
            raise ScambioErrore("Versione del file non riconosciuta.")
        pacchetto = json.loads(zlib.decompress(corpo).decode("utf-8"))
    except ScambioErrore:
        raise
    except Exception:
        raise ScambioErrore("Non riesco a leggere il file: potrebbe essere incompleto o danneggiato. Fattelo mandare di nuovo.")
    if pacchetto.get("formato") != "dispensa-scambio":
        raise ScambioErrore("Il file non è di questo tipo.")
    return pacchetto


def sc_prepara(d, sezioni, con_file, leggi_file):
    """Costruisce il pacchetto. leggi_file(id) → {nome, mime, b64} oppure None."""
    dati = {s: sc_estrai(d, s) for s in sezioni}
    file_ = {}
    mancanti = 0
    if con_file:
        for s in sezioni:
            for i in sc_ids_file(dati[s]):
                if i in file_:
                    continue
                f = leggi_file(i)
                if f and f.get("b64"):
                    file_[i] = {"nome": f.get("nome", ""), "mime": f.get("mime", ""), "b64": f["b64"]}
                else:
                    mancanti += 1
    return {"formato": "dispensa-scambio", "versione": 1, "creato": datetime.now().strftime("%Y-%m-%d %H:%M"), "sezioni": list(sezioni), "dati": dati, "file": file_, "senza_file": not con_file, "file_mancanti": mancanti}


# ---------------------------------------------------------------------------------------------------------------------
# l'importazione: nuovi identificativi, nessun conflitto
# ---------------------------------------------------------------------------------------------------------------------
def _sc_e_id(x):
    return isinstance(x, str) and bool(re.fullmatch(r"[0-9a-f]{6,16}|p\d{1,2}", x))


def _sc_nuovo_id(vecchio):
    return "p" + uuid.uuid4().hex[:6] if re.fullmatch(r"p\d{1,2}", str(vecchio)) else uuid.uuid4().hex[:10]


def sc_rimappa(parti, ids_file):
    """Dà un identificativo nuovo a OGNI voce che ne ha uno e lo sostituisce ovunque (campi e chiavi): i collegamenti restano giusti. Ritorna (parti nuove, mappa vecchio→nuovo)."""
    mappa = {}

    def raccogli(x):
        if isinstance(x, dict):
            if _sc_e_id(x.get("id")) and x["id"] not in mappa:
                mappa[x["id"]] = _sc_nuovo_id(x["id"])
            for v in x.values():
                raccogli(v)
        elif isinstance(x, list):
            for v in x:
                raccogli(v)
    raccogli(parti)
    for i in ids_file:
        if _sc_e_id(i):
            mappa.setdefault(i, uuid.uuid4().hex[:12])

    def cambia(x):
        if isinstance(x, dict):
            return {(mappa.get(k, k) if isinstance(k, str) else k): cambia(v) for k, v in x.items()}
        if isinstance(x, list):
            return [cambia(v) for v in x]
        if isinstance(x, str) and x in mappa:
            return mappa[x]
        return x
    return cambia(parti), mappa


def sc_unisci(d, sezione, parte):
    """Aggiunge la parte importata ai dati dell'utente (senza togliere né cambiare niente di suo)."""
    if sezione == "dispensa":
        d.setdefault("articoli", []).extend(parte.get("articoli") or [])
    elif sezione == "salute":
        f = d.setdefault("farmacia", {})
        if not f.get("profili"):                                                 # chi non ha ancora persone ha il profilo «suo»: lo si tiene prima di aggiungere le altre
            f["profili"] = [{"id": "p0", "nome": (st.session_state.get("sess") or {}).get("nome", "Io")}]
        for k, v in parte.items():
            if isinstance(v, list):
                f.setdefault(k, []).extend(v)
            elif isinstance(v, dict):
                f.setdefault(k, {}).update({kk: vv for kk, vv in v.items() if kk not in f.get(k, {})})
            elif k not in f:
                f[k] = v
    else:
        c = d.setdefault("casa", {})
        for k in ("beni", "documenti", "manutenzioni"):
            c.setdefault(k, [])
        for k, v in parte.items():
            if isinstance(v, list):
                c.setdefault(k, []).extend(v)
            elif k not in c or not c[k]:
                c[k] = v


def sc_importa(d, pacchetto, sezioni, scrivi_file):
    """Importa le sezioni scelte in d (modifica d). scrivi_file(nuovo_id, nome, mime, b64) salva gli allegati. Ritorna un riepilogo {sezione: testo} e il numero di file salvati."""
    dati = pacchetto.get("dati") or {}
    file_ = pacchetto.get("file") or {}
    scelte = {s: dati[s] for s in sezioni if s in dati}
    ids_f = [i for s in scelte.values() for i in sc_ids_file(s)]
    nuove, mappa = sc_rimappa(scelte, ids_f)
    riepilogo = {}
    for s, parte in nuove.items():
        sc_unisci(d, s, parte)
        riepilogo[s] = sc_riassunto(parte)
    salvati = 0
    for vecchio, f in file_.items():
        if vecchio in mappa:
            scrivi_file(mappa[vecchio], f.get("nome", ""), f.get("mime", ""), f.get("b64", ""))
            salvati += 1
    return riepilogo, salvati


# ---------------------------------------------------------------------------------------------------------------------
# la pagina: Utilità → «📦 Scambia i dati con un altro utente»
# ---------------------------------------------------------------------------------------------------------------------
def _sc_dati():
    return carica_dati(crea_archivio(), st.session_state["percorso"])


def _sc_leggi_file(i):
    try:
        f = carica_dati(crea_archivio(), _fa_percorso_doc(i))
        return f if f and f.get("b64") else None
    except Exception:
        return None


def _sc_scrivi_file(nid, nome, mime, b64):
    corpo = {"nome": nome, "mime": mime, "b64": b64}
    salva_file(_fa_percorso_doc(nid), lambda d, c=corpo: d.update(c), "Scambio: allegato importato")


def _sc_dialogo_importa(pacchetto, sezioni, con_file_n):
    def _finestra():
        st.warning(f"Aggiungo alle tue cose: **{', '.join(SC_SEZIONI[s][0] for s in sezioni)}**. Non cancello e non cambio niente di quello che hai già.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("✅ Sì, importa", key="sc_imp_si", type="primary", width="stretch"):
            esito = {}

            def _fn(d):
                esito["riep"], esito["file"] = sc_importa(d, pacchetto, sezioni, _sc_scrivi_file)
            try:
                with st.spinner("Importo… (può volerci un po' se ci sono tanti allegati)"):
                    salva(_fn, "Scambio: dati importati da un altro utente")
                st.session_state["sc_msg"] = "✅ Importato: " + "; ".join(f"{SC_SEZIONI[s][0].split(',')[0]}: {t}" for s, t in esito["riep"].items()) + f" · {esito['file']} allegati."
                for k in ("sc_pacchetto", "sc_file"):
                    st.session_state.pop(k, None)
            except Exception as ex:
                st.session_state["sc_err"] = f"Non sono riuscito a importare: {ex}"
            st.rerun()
        if s2.button("No", key="sc_imp_no", width="stretch"):
            st.rerun()
    st.dialog("📥 Importa nella tua app")(_finestra)()


def sc_pannello(preselezionata=None):
    """Esporta / Importa. Due schede in una."""
    pre = st.session_state.pop("sc_pre", None) or preselezionata
    if st.session_state.get("sc_msg"):
        st.success(st.session_state.pop("sc_msg"))
    if st.session_state.get("sc_err"):
        st.error(st.session_state.pop("sc_err"))
    scelta = st.radio("Cosa vuoi fare", ["📤 Esporta le mie cose", "📥 Importa da un altro utente"], horizontal=True, key="sc_modo", label_visibility="collapsed",
                      index=0)
    d = _sc_dati()
    if scelta.startswith("📤"):
        st.caption("Scegli **cosa mettere nel file**. Lo dai a un altro utente (per WhatsApp, email…) e lui lo carica nella sua app: le tue cose si **aggiungono** alle sue, senza cancellare niente.")
        sez = st.multiselect("Cosa esporto", list(SC_SEZIONI), default=[pre] if pre in SC_SEZIONI else [], key="sc_sez", format_func=lambda s: SC_SEZIONI[s][0])
        for s in sez:
            st.caption(f"• {SC_SEZIONI[s][0]}: {sc_riassunto(sc_estrai(d, s))}")
        con_file = st.checkbox("Includi anche gli allegati originali (PDF, foto)", value=True, key="sc_con_file", help="Senza allegati il file è molto più leggero, ma l'altro utente vedrà solo i dati.")
        pw = st.text_input("Password per proteggere il file (consigliato)", type="password", key="sc_pw_e", help="Nel file ci sono dati personali e sanitari. Con la password solo chi la conosce lo può aprire. Comunicala a voce, non nello stesso messaggio.")
        if not sez:
            st.info("Scegli almeno una sezione.")
            return
        if st.button("📦 Prepara il file", key="sc_prepara", type="primary", width="stretch"):
            with st.spinner("Preparo il file…"):
                pac = sc_prepara(d, sez, con_file, _sc_leggi_file)
                pac["da"] = (st.session_state.get("sess") or {}).get("nome", "")
                st.session_state["sc_pronto"] = (sc_impacchetta(pac, pw), len(pac["file"]), pac["file_mancanti"], bool(pw))
        pronto = st.session_state.get("sc_pronto")
        if pronto:
            dati, n_file, manc, cifrato = pronto
            st.success(f"✅ File pronto: {len(dati) // 1024} KB · {n_file} allegati" + (" · 🔒 protetto con password" if cifrato else " · ⚠️ senza password"))
            if manc:
                st.warning(f"{manc} allegati non si trovano più nell'archivio e non sono nel file.")
            if len(dati) > 20 * 1024 * 1024:
                st.warning("Il file è grande (oltre 20 MB): per mandarlo conviene Google Drive, oppure esportare una sezione alla volta o senza allegati.")
            nome_f = f"dispensa_{re.sub(r'[^A-Za-z0-9]+', '_', (st.session_state.get('sess') or {}).get('nome', 'utente'))}_{date.today().isoformat()}.dispensa"
            st.download_button("⬇ Scarica il file da dare all'altro utente", dati, file_name=nome_f, mime="application/octet-stream", key="sc_dl", width="stretch")
        return
    # ---- importa
    st.caption("Chi ti ha dato il file **.dispensa**: scegli qui il file, scrivi la password se c'è, guarda cosa contiene e **aggiungi** quello che vuoi alle tue cose. Non cancello e non cambio niente di quello che hai già.")
    if "_ca_avvia_trasferimento" in globals() and "_ca_trasf_ricevi" in globals():
        st.markdown(_CA_CSS_FOTO, unsafe_allow_html=True)
        _ca_avvia_trasferimento()
        ack_t, err_t = _ca_trasf_ricevi()
        with st.container(key="ca_ricezione"):
            st.text_input("ca-pdf-trasf", key="ca_trasf_in", label_visibility="collapsed")
        st.markdown("<div class='ca-pdf-btn' role='button' tabindex='0' data-ca-pdf='1'>📎 Scegli il file .dispensa</div>"
                    f"<div class='ca-pdf-stato' data-ca-stato='1'>{'⚠️ ' + err_t if err_t else ('✅ File ricevuto.' if (ack_t.endswith(':fine')) else 'Tocca il pulsante arancione e scegli il file.')}</div>"
                    f"<span data-ca-ack='{ack_t}' style='display:none'></span><pre data-ca-log='1' style='display:none'></pre>", unsafe_allow_html=True)
    b = st.session_state.get("ca_bozza_in")
    if b and str(b.get("nome", "")).lower().endswith(".dispensa"):             # il file arrivato dal pulsante arancione: si prende e non resta tra i documenti
        st.session_state["sc_file"] = {"nome": b["nome"], "dati": b["dati"]}
        st.session_state.pop("ca_bozza_in", None)
        st.session_state.pop("sc_pacchetto", None)
    elif b:
        st.warning(f"Il file «{b.get('nome', '')}» non è un file di scambio (.dispensa): lo ignoro.")
        st.session_state.pop("ca_bozza_in", None)
    alt = st.file_uploader("…oppure scegli il file da qui", key="sc_up", help="Se il pulsante arancione non funziona.")
    if alt is not None and alt.name.lower().endswith(".dispensa") and (st.session_state.get("sc_file") or {}).get("nome") != alt.name:
        st.session_state["sc_file"] = {"nome": alt.name, "dati": alt.getvalue()}
        st.session_state.pop("sc_pacchetto", None)
    f = st.session_state.get("sc_file")
    if not f:
        return
    st.markdown(f"📄 **{f['nome']}** ({len(f['dati']) // 1024} KB)")
    pw = st.text_input("Password del file (se c'è)", type="password", key="sc_pw")
    if st.button("🔍 Guarda cosa contiene", key="sc_guarda", width="stretch"):
        try:
            st.session_state["sc_pacchetto"] = sc_apri(f["dati"], pw)
        except ScambioErrore as ex:
            st.session_state.pop("sc_pacchetto", None)
            st.error(str(ex))
    pac = st.session_state.get("sc_pacchetto")
    if not pac:
        return
    st.success(f"✅ File aperto · creato il {pac.get('creato', '?')}" + (f" da **{pac['da']}**" if pac.get("da") else "") + f" · {len(pac.get('file') or {})} allegati")
    if pac.get("senza_file"):
        st.info("Questo file non contiene gli allegati originali: importerai solo i dati.")
    dispo = [s for s in SC_SEZIONI if s in (pac.get("dati") or {})]
    scelte = st.multiselect("Cosa importo", dispo, default=dispo, key="sc_scelte", format_func=lambda s: f"{SC_SEZIONI[s][0]}: {sc_riassunto(pac['dati'][s])}")
    troppe = False
    if "salute" in scelte:
        ora = len((d.get("farmacia") or {}).get("profili") or [{}])
        nuove_p = len((pac["dati"]["salute"] or {}).get("profili") or [])
        massimo = globals().get("MAX_PROFILI", 12)
        if ora + nuove_p > massimo:
            troppe = True
            st.error(f"Con queste persone arriveresti a {ora + nuove_p} profili: il massimo è {massimo}. Togli qualche profilo che non ti serve (Salute → 👥 Gestisci profili) oppure non importare la Salute.")
    if scelte and st.button("📥 Importa quello che ho scelto", key="sc_importa", type="primary", width="stretch", disabled=troppe):
        _sc_dialogo_importa(pac, scelte, len(pac.get("file") or {}))


def sc_pulsante(sezione):
    """Il piccolo pulsante in fondo a ogni sezione: porta allo scambio con quella sezione già scelta."""
    if st.button("📦 Esporta o importa questa sezione (scambio con un altro utente)", key=f"sc_btn_{sezione}", width="stretch"):
        st.session_state["sc_pre"] = {"documenti": "salute", "archivio": "salute", "salute": "salute"}.get(sezione, sezione)
        st.session_state["sc_apri"] = True
        nav_vai("utilita")
        st.rerun()


# ---- aggancio: Utilità ha il riquadro; ogni sezione ha il pulsante in fondo
if "schermata_utilita" in globals() and "_sc_utilita_prima" not in globals():
    _sc_utilita_prima = schermata_utilita

    def schermata_utilita():                                         # noqa: F811
        _sc_utilita_prima()
        try:
            st.markdown("<div id='sc-scambio'></div>", unsafe_allow_html=True)
            if st.session_state.pop("sc_apri", False):                       # arrivi dal pulsante di una sezione: il riquadro è già aperto
                st.subheader("📦 Scambia i dati con un altro utente")
                sc_pannello()
            else:
                with st.expander("📦 Scambia i dati con un altro utente (esporta e importa)"):
                    sc_pannello()
        except Exception as ex:
            st.warning(f"Lo scambio dati non è disponibile ({type(ex).__name__}).")

if "schermata_farmacia" in globals() and "_sc_farmacia_prima" not in globals():
    _sc_farmacia_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        r = _sc_farmacia_prima()
        sez = st.session_state.get("sezione_home") or "salute"
        if sez in ("salute", "documenti", "archivio", "casa", "lavoro"):
            try:
                st.divider()
                sc_pulsante(sez)
            except Exception:
                pass
        return r
