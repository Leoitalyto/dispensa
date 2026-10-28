# -*- coding: utf-8 -*-
"""CODICE A BARRE DEI MEDICINALI.
Dalla Farmacia, in «Aggiungi medicinale», si inquadra la scatola e l'app legge:
  • il DataMatrix GS1 (il quadratino che dal 2025 c'è su tutte le scatole dei farmaci con ricetta): scadenza, lotto e codice prodotto
  • il bollino (Code 39 / Code 32 «Farmadati») o le barre EAN: il codice AIC o EAN
poi riconosce il medicinale:
  1) se c'è già in casa (tra i medicinali della famiglia, per codice AIC o GTIN): ricopia nome, principio attivo, dosaggio e forma;
  2) altrimenti prova con l'elenco ufficiale AIFA (se risponde);
  3) altrimenti compila quello che sa (scadenza, lotto, codice) e il nome si scrive una volta sola: dalla volta dopo lo riconosce.
La scadenza e il lotto letti dalla scatola riempiono il modulo, che resta sempre modificabile.
Caricato da app_dispensa.py dopo farmacia.py e invio.py."""
import io
import re
import calendar
from datetime import date

import numpy as np
import streamlit as st

_BASE32 = "0123456789BCDFGHJKLMNPQRSTUVWXYZ"          # l'alfabeto del Code 32 italiano (senza vocali)
_AI_FISSI = {"00": 18, "01": 14, "02": 14, "11": 6, "12": 6, "13": 6, "15": 6, "16": 6, "17": 6, "20": 2, "31": 6, "32": 6}
_AI_VARIABILI = ("10", "21", "22", "30", "37", "240", "241", "242", "250", "251", "253", "254", "400", "710", "711", "712", "713", "714", "715", "91", "92", "93", "94", "95", "96", "97", "98", "99")
URL_AIFA_CONFEZIONI = "https://drive.aifa.gov.it/farmaci/confezioni_fornitura.csv"
URL_AIFA_PRINCIPI = "https://drive.aifa.gov.it/farmaci/PA_confezioni.csv"

_FORME_SIGLE = [("compresse", ("cpr", "compress", "cp ")), ("capsule", ("cps", "cap ", "capsul", "caps")), ("bustine", ("bust", "polv")),
                ("gocce", ("gtt", "gocce")), ("sciroppo", ("sciropp", "sir ", "sosp", "os sol")), ("fiale", ("fiala", "fiale", "fl ", "f.")),
                ("crema / pomata", ("crema", "pomata", "gel", "unguento")), ("spray", ("spray", "nebul", "aerosol")),
                ("cerotti", ("cerott",)), ("supposte", ("supp", "supposta")), ("collirio", ("collir", "coll ", "gtt oft"))]


# ---------------------------------------------------------------------------------------------------------------------
# Lettura dei codici da una foto
# ---------------------------------------------------------------------------------------------------------------------
def sm_leggi_codici(dati):
    """Tutti i codici trovati in una foto: lista di (formato, testo). None se manca la libreria di lettura."""
    try:
        import zxingcpp
    except Exception:
        return None
    from PIL import Image, ImageOps
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("L")
    except Exception:
        return []
    trovati, visti = [], set()
    for lato in (1600, 2400, 1000):                           # più misure: un DataMatrix piccolo si legge meglio ingrandito
        im = img.copy()
        im.thumbnail((lato, lato))
        for rot in (0, 90, 270):
            arr = np.array(im.rotate(rot, expand=True)) if rot else np.array(im)
            try:
                letti = zxingcpp.read_barcodes(arr)
            except Exception:
                continue
            for r in letti:
                chiave = (str(r.format), r.text)
                if chiave not in visti and r.text:
                    visti.add(chiave)
                    trovati.append((str(r.format), r.text))
        if trovati:
            break
    return trovati


# ---------------------------------------------------------------------------------------------------------------------
# Interpretazione
# ---------------------------------------------------------------------------------------------------------------------
def sm_gs1(testo):
    """Un testo GS1 (con le parentesi «(01)…(17)…» oppure senza, con il carattere di separazione tra i campi) in un dizionario {AI: valore}."""
    t = (testo or "").replace("<GS>", "\x1d").replace("␝", "\x1d")
    t = re.sub(r"^\](d2|C1|e0|Q3)", "", t)
    campi = {}
    if re.match(r"\(\d{2,4}\)", t):
        for ai, v in re.findall(r"\((\d{2,4})\)([^(]*)", t):
            campi[ai] = v.replace("\x1d", "").strip()
        return campi
    i = 0
    while i < len(t):
        if t[i] == "\x1d":
            i += 1
            continue
        for lung in (2, 3, 4):
            ai = t[i:i + lung]
            if ai in _AI_FISSI:
                campi[ai] = t[i + lung:i + lung + _AI_FISSI[ai]]
                i += lung + _AI_FISSI[ai]
                break
            if ai in _AI_VARIABILI:
                fine = t.find("\x1d", i + lung)
                fine = len(t) if fine < 0 else fine
                campi[ai] = t[i + lung:fine][:30 if len(ai) == 3 else 20]
                i = fine
                break
        else:
            break                                            # campo sconosciuto: mi fermo
    return campi


def sm_data_gs1(yymmdd):
    """AAMMGG → data. Il giorno 00 vuol dire «ultimo giorno del mese»."""
    if not re.fullmatch(r"\d{6}", yymmdd or ""):
        return None
    aa, mm, gg = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:])
    if not 1 <= mm <= 12:
        return None
    anno = 2000 + aa
    if gg == 0:
        gg = calendar.monthrange(anno, mm)[1]
    try:
        return date(anno, mm, gg)
    except ValueError:
        return None


def sm_code32_a_aic(testo):
    """Il Code 32 («codice Farmadati in base 32») della scatola in codice AIC di 9 cifre. None se non è un Code 32."""
    t = re.sub(r"^A", "", (testo or "").strip().upper())
    if len(t) != 8 or any(c not in _BASE32 for c in t):
        return None
    valore = 0
    for c in t:
        valore = valore * 32 + _BASE32.index(c)
    return f"{valore:09d}" if valore < 10 ** 9 else None


def sm_interpreta(codici):
    """Dai codici letti: {'aic', 'gtin', 'ean', 'scadenza' (ISO), 'lotto', 'seriale', 'letti'}. I campi non trovati restano vuoti."""
    r = {"aic": "", "gtin": "", "ean": "", "scadenza": "", "lotto": "", "seriale": "", "letti": []}
    for formato, testo in codici or []:
        r["letti"].append(f"{formato}: {testo[:60]}")
        f = formato.lower().replace(" ", "")
        if "datamatrix" in f or "gs1" in f or testo.startswith("(01)") or re.match(r"^01\d{14}", testo):
            campi = sm_gs1(testo)
            if campi.get("01"):
                r["gtin"] = campi["01"]
            d = sm_data_gs1(campi.get("17", ""))
            if d:
                r["scadenza"] = d.isoformat()
            r["lotto"] = campi.get("10", r["lotto"])
            r["seriale"] = campi.get("21", r["seriale"])
            for ai in ("714", "712", "711", "710", "240", "241"):
                v = (campi.get(ai) or "").upper()
                m = re.fullmatch(r"A?(\d{9})", v)
                if m and not r["aic"]:
                    r["aic"] = m.group(1)
        elif "code39" in f or "code32" in f or "code128" in f:
            t = testo.strip().upper()
            m = re.fullmatch(r"A?(\d{9})", t)
            if m:
                r["aic"] = r["aic"] or m.group(1)
            else:
                aic = sm_code32_a_aic(t)
                if aic:
                    r["aic"] = r["aic"] or aic
        elif "ean" in f or "upc" in f:
            if re.fullmatch(r"\d{8,13}", testo.strip()) and not r["ean"]:
                r["ean"] = testo.strip()
    return r


# ---------------------------------------------------------------------------------------------------------------------
# Riconoscere il medicinale
# ---------------------------------------------------------------------------------------------------------------------
def sm_trova_in_memoria(elenco, info):
    """Tra i medicinali già conosciuti (lista di dizionari con eventuali 'aic', 'gtin', 'ean'): quello con lo stesso codice."""
    for m in elenco:
        if info.get("aic") and m.get("aic") == info["aic"]:
            return m
        if info.get("gtin") and m.get("gtin") == info["gtin"]:
            return m
        if info.get("ean") and m.get("ean") == info["ean"]:
            return m
    return None


def _forma_da_testo(testo):
    t = " " + (testo or "").lower() + " "
    for forma, sigle in _FORME_SIGLE:
        if any(s in t for s in sigle):
            return forma
    return ""


def _dosaggio_da_testo(testo):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|g|ml|ui|%)\b", testo or "", re.I)
    return f"{m.group(1).replace('.', ',')} {m.group(2).lower()}" if m else ""


def sm_interpreta_riga_aifa(intestazioni, riga):
    """Da una riga dell'elenco AIFA (intestazioni + valori) a {'nome', 'marca', 'forma', 'dosaggio', 'confezione'}. Le intestazioni non sono
    note con certezza: si cercano per parole (denominazione, confezione, forma, titolare)."""
    campi = {h.strip().upper(): (v or "").strip() for h, v in zip(intestazioni, riga)}

    def prendi(*parole, escludi=()):
        for h, v in campi.items():
            if v and any(p in h for p in parole) and not any(e in h for e in escludi):
                return v
        return ""
    denominazione = prendi("DENOMINAZ", "NOME_MEDICINALE", "NOME", "SPECIALIT", "MEDICINALE", escludi=("TITOLARE", "AZIENDA", "DITTA"))
    confezione = prendi("CONFEZION", "DESCRIZ", escludi=("CODICE", "STATO", "FORMA"))
    forma = prendi("FORMA")
    azienda = prendi("TITOLARE", "AZIENDA", "DITTA")
    nome = denominazione
    if not nome and confezione:
        nome = confezione.split("*")[0]
    elif "*" in nome:
        nome = nome.split("*")[0]
    testo_forma = " ".join(x for x in (forma, confezione, denominazione) if x)
    return {"nome": nome.strip().title() if nome.isupper() else nome.strip(), "marca": azienda.title() if azienda.isupper() else azienda,
            "forma": _forma_da_testo(testo_forma), "dosaggio": _dosaggio_da_testo(testo_forma), "confezione": confezione}


def _righe_csv(url, timeout=(10, 90)):
    """Le righe di un grande file CSV, lette a pezzi senza scaricarlo tutto."""
    import requests
    with requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": "DispensaFamiglia/1.0 (https://github.com/Leoitalyto/dispensa)"}) as r:
        r.raise_for_status()
        for riga in r.iter_lines():
            if riga:
                try:
                    yield riga.decode("utf-8")
                except UnicodeDecodeError:
                    yield riga.decode("latin-1")


@st.cache_data(ttl=7 * 86400, show_spinner=False, max_entries=300)
def sm_cerca_aifa(aic):
    """Cerca un codice AIC nell'elenco ufficiale AIFA (se risponde). Ritorna {'nome', 'marca', 'forma', 'dosaggio', 'principio'} oppure None."""
    aic = re.sub(r"\D", "", aic or "").zfill(9)
    risultato, intest, col = None, None, None
    for riga in _righe_csv(URL_AIFA_CONFEZIONI):
        campi = riga.split(";")
        if intest is None:
            intest = [c.strip().strip('"') for c in campi]
            col = next((i for i, h in enumerate(intest) if h.upper() in ("CODICE_AIC", "AIC", "COD_AIC") or "AIC" in h.upper()), None)
            if col is None:
                return None                                    # il file non ha la colonna che cerco
            continue
        if col < len(campi) and campi[col].strip().strip('"').zfill(9) == aic:
            risultato = sm_interpreta_riga_aifa(intest, [c.strip().strip('"') for c in campi])
            break
    if not risultato:
        return None
    principi, dosaggi = [], []
    try:
        for riga in _righe_csv(URL_AIFA_PRINCIPI):
            campi = riga.split(";")
            if campi and campi[0].strip().zfill(9) == aic and len(campi) >= 2:
                if campi[1].strip() not in ("N.D.", "") and campi[1].strip() not in principi:
                    principi.append(campi[1].strip())
                if len(campi) >= 4 and campi[2].strip() and campi[3].strip() not in ("N.D.",) and not dosaggi:
                    dosaggi.append(f"{campi[2].strip().replace('.', ',')} {campi[3].strip()}".strip())
            elif principi and campi and campi[0].strip().zfill(9) > aic:
                break                                          # l'elenco è in ordine di codice: oltre, non c'è più
    except Exception:
        pass
    risultato["principio"] = " / ".join(p.title() for p in principi)
    if not risultato.get("dosaggio") and dosaggi:
        risultato["dosaggio"] = dosaggi[0]
    return risultato


def sm_data_it(iso):
    return "/".join(reversed(iso.split("-"))) if iso else ""


# ---------------------------------------------------------------------------------------------------------------------
# Il pezzo di schermata
# ---------------------------------------------------------------------------------------------------------------------
def sm_blocco(elenco_conosciuti, chiave="scanmed"):
    """«📷 Inquadra la scatola»: legge i codici da una foto e ritorna i dati da ricopiare nel modulo (dizionario, può essere vuoto).
    elenco_conosciuti = medicinali già conosciuti dalla famiglia (dizionari con nome, principio, dosaggio, forma, aic, gtin)."""
    with st.container(key="azioni_foto_" + chiave):
        c_cam, c_gal = st.columns(2, gap="small")
        premuto_cam = c_cam.button("📷 Inquadra la scatola", key=f"scatta_{chiave}", width="stretch")
        premuto_gal = c_gal.button("📁 Scegli una foto", key=f"galleria_{chiave}", width="stretch")
    with st.container(key="nascosti_" + chiave):
        f_cam = st.file_uploader("camera", type=["jpg", "jpeg", "png", "webp"], key=f"fotocam_{chiave}")
        f_gal = st.file_uploader("galleria", type=["jpg", "jpeg", "png", "webp"], key=f"fotogal_{chiave}")
    if premuto_cam:
        st.session_state[f"{chiave}_fall_cam"] = True
    if premuto_gal:
        st.session_state[f"{chiave}_fall_gal"] = True
    fall_cam = st.camera_input("Inquadra la scatola", key=f"camfall_{chiave}") if st.session_state.get(f"{chiave}_fall_cam") else None
    fall_gal = st.file_uploader("Scegli una foto", type=["jpg", "jpeg", "png", "webp"], key=f"galfall_{chiave}") if st.session_state.get(f"{chiave}_fall_gal") else None
    st.caption("Inquadra il **quadratino** (DataMatrix) o le **barre** sulla scatola, da vicino e con buona luce: leggo scadenza, lotto e codice.")

    viste = st.session_state.setdefault(f"{chiave}_viste", {})
    ultima = st.session_state.get(f"{chiave}_ultima")
    candidati = {"cam": f_cam, "gal": f_gal, "fcam": fall_cam, "fgal": fall_gal}
    for nome, f in candidati.items():
        if f is None:
            viste.pop(nome, None)
            continue
        ident = getattr(f, "file_id", None) or f"{f.name}{f.size}"
        if viste.get(nome) != ident:
            viste[nome] = ident
            ultima = nome
    st.session_state[f"{chiave}_ultima"] = ultima
    file = candidati.get(ultima) or next((f for f in candidati.values() if f is not None), None)

    risultato = st.session_state.get("sm_prefill") or {}
    if file is not None:
        ident_f = getattr(file, "file_id", None) or f"{file.name}{file.size}"
        if st.session_state.get("sm_elaborata") != ident_f:           # ogni foto si legge una volta sola
            st.session_state["sm_elaborata"] = ident_f
            with st.spinner("Leggo il codice…"):
                codici = sm_leggi_codici(file.getvalue())
            if codici is None:
                st.session_state["sm_prefill"] = {"_errore": "manca la libreria di lettura (riga «zxing-cpp» in requirements.txt)"}
            elif not codici:
                st.session_state["sm_prefill"] = {"_errore": "non vedo nessun codice nella foto"}
            else:
                info = sm_interpreta(codici)
                pref = {"scadenza": info["scadenza"], "lotto": info["lotto"], "aic": info["aic"], "gtin": info["gtin"], "ean": info["ean"],
                        "_letti": info["letti"], "_origine": ""}
                noto = sm_trova_in_memoria(elenco_conosciuti, info)
                if noto:
                    pref.update({k: noto.get(k, "") for k in ("nome", "marca", "principio", "dosaggio", "forma")})
                    pref["_origine"] = "casa"
                elif info["aic"]:
                    with st.spinner("Cerco il medicinale nell'elenco AIFA…"):
                        try:
                            aifa = sm_cerca_aifa(info["aic"])
                        except Exception:
                            aifa = None
                    if aifa:
                        pref.update({k: aifa.get(k, "") for k in ("nome", "marca", "principio", "dosaggio", "forma")})
                        pref["_origine"] = "aifa"
                st.session_state["sm_prefill"] = pref
            risultato = st.session_state["sm_prefill"]

    if risultato:
        if risultato.get("_errore"):
            st.warning(f"⚠️ Non ci sono riuscito: {risultato['_errore']}. Riprova più vicino e con più luce, oppure compila a mano.")
        else:
            righe = []
            if risultato.get("aic"):
                righe.append(f"AIC {risultato['aic']}")
            if risultato.get("gtin"):
                righe.append(f"codice prodotto {risultato['gtin']}")
            if risultato.get("ean") and not risultato.get("aic"):
                righe.append(f"EAN {risultato['ean']}")
            if risultato.get("scadenza"):
                righe.append(f"scadenza {sm_data_it(risultato['scadenza'])}")
            if risultato.get("lotto"):
                righe.append(f"lotto {risultato['lotto']}")
            st.success("📦 Letto dalla scatola: " + " · ".join(righe) if righe else "📦 Codice letto.")
            if risultato.get("_origine") == "casa":
                st.info(f"✅ Lo conosco: **{risultato.get('nome', '')}** è già in casa. Ho ricopiato nome, principio attivo, dosaggio e forma.")
            elif risultato.get("_origine") == "aifa":
                st.info(f"✅ Trovato nell'elenco AIFA: **{risultato.get('nome', '')}**. Controlla che sia giusto prima di salvare.")
            else:
                st.info("Non conosco ancora questo medicinale: scrivi il nome una volta, dalla prossima volta lo riconosco da solo.")
        if st.button("✖ Togli la scansione", key=f"{chiave}_togli"):
            st.session_state.pop("sm_prefill", None)        # la foto resta nel campo nascosto: non va riletta
            st.rerun()
    return {k: v for k, v in risultato.items() if not k.startswith("_") and v}
