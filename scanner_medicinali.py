# -*- coding: utf-8 -*-
"""CODICE A BARRE DEI MEDICINALI.
Da Salute, in «Aggiungi medicinale», si inquadra la scatola e l'app legge:
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
        f = formato.lower().replace(" ", "").replace("_", "").replace("-", "")
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
# Il testo stampato sulla scatola: «SCAD. 03/2028», «LOT AB1234» (per le scatole senza DataMatrix)
# ---------------------------------------------------------------------------------------------------------------------
_RE_PAROLA_SCAD = r"(?:SCAD(?:ENZA)?\.?|EXP(?:IRY)?\.?(?:\s*DATE)?|USE\s*BY|DA\s*USARE\s*ENTRO|VALIDO\s*FINO\s*AL?|BEST\s*BEFORE)"
_RE_DATA = r"(?:(\d{1,2})\s*[./\-]\s*)?(\d{1,2})\s*[./\-]\s*(\d{4}|\d{2})\b"
_RE_DATA_ISO = r"(\d{4})\s*[./\-]\s*(\d{1,2})(?:\s*[./\-]\s*(\d{1,2}))?"


def _cifre(t):
    """Sistema gli errori tipici di lettura nelle cifre (O→0, I/l→1, S→5, B→8) dentro un pezzo di testo di una data."""
    return (t or "").translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1", "S": "5", "B": "8"}))


def _data_da_pezzi(g1, m, a, anno_minimo=2000):
    """(giorno o None, mese, anno) → data. Senza giorno vale l'ultimo giorno del mese (come sulle scatole)."""
    try:
        mese, anno = int(m), int(a)
        anno = anno + 2000 if anno < 100 else anno
        if not (1 <= mese <= 12 and anno_minimo <= anno <= 2060):
            return None
        giorno = int(g1) if g1 else calendar.monthrange(anno, mese)[1]
        return date(anno, mese, min(giorno, calendar.monthrange(anno, mese)[1]))
    except (ValueError, TypeError):
        return None


def sm_analizza_testo(testo, oggi=None):
    """Dal testo letto dalla scatola: {'scadenza': ISO o '', 'lotto': ''}. Cerca dopo «SCAD./EXP./USE BY…»; senza parola chiave prende
    la data più lontana tra quelle plausibili (le altre sono di solito la produzione)."""
    oggi = oggi or date.today()
    righe = [re.sub(r"[ \t]+", " ", r).strip() for r in (testo or "").replace("\r", "\n").split("\n")]
    t = "\n".join(righe)
    scadenza = None
    for m in re.finditer(_RE_PAROLA_SCAD + r"\s*[:.\-]?\s*([0-9OoIl|SB]{1,2}\s*[./\-]\s*)?([0-9OoIl|SB]{1,2}\s*[./\-]\s*[0-9OoIl|SB]{2,4})", t, re.I):
        pezzo = _cifre(((m.group(1) or "") + m.group(2)))
        d = re.search(_RE_DATA, pezzo)
        if d:
            cand = _data_da_pezzi(d.group(1), d.group(2), d.group(3), oggi.year - 3)
            if cand and (scadenza is None or cand > scadenza):
                scadenza = cand
    if scadenza is None:
        m = re.search(_RE_PAROLA_SCAD + r"\s*[:.\-]?\s*" + _RE_DATA_ISO, t, re.I)
        if m:
            scadenza = _data_da_pezzi(m.group(3), m.group(2), m.group(1), oggi.year - 3)
    if scadenza is None:                                      # nessuna parola chiave: la data più lontana ma plausibile
        candidate = []
        for d in re.finditer(_RE_DATA, t):
            if d.group(1) is None and len(d.group(3)) == 4:      # MM/AAAA
                cand = _data_da_pezzi(None, d.group(2), d.group(3), oggi.year - 1)
                if cand and cand <= date(oggi.year + 10, 12, 31):
                    candidate.append(cand)
        if candidate:
            scadenza = max(candidate)
    lotto = ""
    m = re.search(r"\b(?:LOT(?:TO)?|BATCH|L)\b\.?\s*[:.\-]?\s*([A-Z0-9]{3,14})\b", t, re.I)
    if m and re.search(r"\d", m.group(1)):
        lotto = m.group(1).upper()
    return {"scadenza": scadenza.isoformat() if scadenza else "", "lotto": lotto}


def sm_ocr_scatola(dati):
    """Legge il testo della scatola con Tesseract (se c'è) e ne ricava scadenza e lotto. {} se non si capisce niente o manca Tesseract."""
    if "_doc_ocr_lingue" not in globals() or not _doc_ocr_lingue():
        return {}
    import time
    import cv2
    from PIL import Image, ImageOps
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    except Exception:
        return {}
    img.thumbnail((2200, 2200))
    grigio = np.array(img.convert("L"))
    soglia = cv2.adaptiveThreshold(cv2.medianBlur(grigio, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 12)
    varianti = [(img, "11"), (Image.fromarray(soglia), "11"), (Image.fromarray(soglia), "6"), (Image.fromarray(grigio), "6")]
    inizio, testi, migliore = time.time(), [], {}
    for immagine, psm in varianti:
        if testi and time.time() - inizio > 40:
            break
        try:
            testi.append(_doc_tesseract(immagine, psm))
        except Exception:
            continue
        migliore = sm_analizza_testo("\n".join(testi))
        if migliore.get("scadenza") and migliore.get("lotto"):
            break
    return {k: v for k, v in migliore.items() if v}


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


def sm_cerca_ean(ean):
    """Cerca un codice EAN (integratori, prodotti erboristici, dispositivi...) negli elenchi pubblici già usati dalla dispensa (Open Food Facts e Open Products
    Facts). Ritorna {'nome', 'marca', 'categoria', 'fonte'} oppure None."""
    if "cerca_prodotto" not in globals() or not ean:
        return None
    try:
        p = cerca_prodotto(ean, "neonati")                      # «neonati» cerca anche in Open Products Facts (prodotti non alimentari)
    except Exception:
        return None
    if not p or "errore" in p:
        return None
    nome = p.get("product_name_it") or p.get("product_name") or p.get("product_name_en") or ""
    marca = (p.get("brands") or "").split(",")[0].strip()
    if not nome and not marca:
        return None
    testo = " ".join(str(p.get(k) or "") for k in ("categories", "labels_tags", "product_name")).lower()
    categoria = ""
    if any(x in testo for x in ("supplement", "integrator", "vitamin", "dietary", "complemen")):
        categoria = "Integratore"
    elif any(x in testo for x in ("herbal", "erbor", "tisan", "infus", "tintura")):
        categoria = "Prodotto erboristico"
    return {"nome": nome.strip(), "marca": marca, "categoria": categoria, "quantita_testo": str(p.get("quantity") or "")}


def sm_data_it(iso):
    return "/".join(reversed(iso.split("-"))) if iso else ""


# ---------------------------------------------------------------------------------------------------------------------
# Scansione in diretta con la fotocamera (BarcodeDetector del browser: Chrome su Android): niente foto da caricare
# ---------------------------------------------------------------------------------------------------------------------
_JS_SCAN = r"""
(function () {
  var w = window, d = w.document;
  try {
    if (w.__scanDirAttivo) return;
    w.__scanDirAttivo = true;
    var MSG = __MSG__;
    function invia(chiave, valore) {
      var inp = d.querySelector('input[aria-label="scan-diretta-' + chiave + '"]');
      if (!inp) return;
      var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
      setter.call(inp, valore);
      inp.dispatchEvent(new w.Event('input', {bubbles: true}));
      inp.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
      inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
    }
    function chiudi(ov) {
      try { var v = ov.querySelector('video'); if (v && v.srcObject) v.srcObject.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
      if (ov.parentNode) ov.parentNode.removeChild(ov);
    }
    function avvia(chiave) {
      var ov = d.createElement('div'); ov.id = 'scan-diretta';
      ov.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;background:#000;z-index:100003;display:flex;flex-direction:column';
      ov.innerHTML = '<video playsinline muted style="flex:1;width:100%;min-height:0;object-fit:cover"></video>' +
        '<div style="position:absolute;left:12%;right:12%;top:30%;height:34%;border:3px solid #3ddc97;border-radius:18px;box-shadow:0 0 0 2000px rgba(0,0,0,.35)"></div>' +
        '<div id="scan-stato" style="position:absolute;left:0;right:0;top:14px;text-align:center;color:#fff;font:600 16px/1.3 sans-serif;padding:0 70px;text-shadow:0 1px 4px #000"></div>' +
        '<button id="scan-chiudi" style="position:absolute;right:12px;top:10px;width:48px;height:48px;border-radius:24px;border:0;background:#fff;font:700 22px sans-serif">✖</button>' +
        '<div style="position:absolute;left:0;right:0;bottom:22px;text-align:center;color:#fff;font:600 14px sans-serif;text-shadow:0 1px 4px #000;padding:0 20px">' + MSG.consiglio + '</div>';
      d.body.appendChild(ov);
      var stato = ov.querySelector('#scan-stato'), video = ov.querySelector('video'), fermo = false;
      stato.textContent = MSG.cerco;
      ov.querySelector('#scan-chiudi').onclick = function () { fermo = true; chiudi(ov); };
      w.navigator.mediaDevices.getUserMedia({video: {facingMode: {ideal: 'environment'}, width: {ideal: 1920}, height: {ideal: 1080}}, audio: false}).then(function (stream) {
        video.srcObject = stream;
        try { var tr = stream.getVideoTracks()[0]; tr.applyConstraints({advanced: [{focusMode: 'continuous'}]}).catch(function () {}); } catch (e) {}
        var pr = video.play(); if (pr && pr.catch) pr.catch(function () {});
        w.BarcodeDetector.getSupportedFormats().then(function (sup) {
          var voluti = ['data_matrix', 'code_39', 'code_128', 'ean_13', 'ean_8', 'upc_a', 'qr_code'];
          var formati = voluti.filter(function (f) { return sup.indexOf(f) >= 0; });
          var det = new w.BarcodeDetector({formats: formati.length ? formati : undefined});
          var trovati = {}, primo = 0;
          (function giro() {
            if (fermo) return;
            det.detect(video).then(function (res) {
              (res || []).forEach(function (r) { if (r.rawValue) { trovati[r.format + '|' + r.rawValue] = [r.format, r.rawValue]; } });
              var chiavi = Object.keys(trovati);
              if (chiavi.length && !primo) { primo = Date.now(); stato.textContent = MSG.letto; }
              var haDM = chiavi.some(function (k) { return k.indexOf('data_matrix') === 0; });
              var haAltro = chiavi.some(function (k) { return k.indexOf('data_matrix') !== 0; });
              if (chiavi.length && ((haDM && haAltro) || Date.now() - primo > 2500)) {
                fermo = true; chiudi(ov);
                try { if (w.navigator.vibrate) w.navigator.vibrate(90); } catch (e) {}
                invia(chiave, JSON.stringify(chiavi.map(function (k) { return trovati[k]; })) + '|' + Date.now());
                return;
              }
              w.setTimeout(giro, 160);
            }).catch(function () { w.setTimeout(giro, 400); });
          })();
        });
      }).catch(function (err) { fermo = true; chiudi(ov); invia(chiave, 'errore|' + ((err && err.name) || 'camera') + '|' + Date.now()); });
    }
    d.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[class*="st-key-scandiretta_"] button') : null;
      if (!b) return;
      var c = b.closest('[class*="st-key-scandiretta_"]');
      var m = (c.className || '').match(/st-key-scandiretta_(\S+)/);
      if (!m) return;
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
      if (!w.BarcodeDetector || !w.navigator.mediaDevices || !w.navigator.mediaDevices.getUserMedia) { invia(m[1], 'errore|nonsupp|' + Date.now()); return; }
      avvia(m[1]);
    }, true);
  } catch (err) { /* resta la scelta di scattare una foto */ }
})();
"""

_MSG_SCAN = {"cerco": "Inquadra il codice…", "letto": "Letto! Tengo ancora un attimo…",
             "consiglio": "Avvicinati al quadratino (DataMatrix) o alle barre, con buona luce. Se hai due codici, inquadrali uno dopo l'altro."}


def _sm_pagina_js(codice):
    import json as _json
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\\\"stApp\\\"],.stApp,[data-testid=\\\"stAppViewContainer\\\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + _json.dumps(codice) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_sm
            _comp_sm.html(pagina, height=0)
    except Exception:
        pass


def sm_inietta_scansione():
    if st.session_state.get("_sm_js"):
        return
    st.session_state["_sm_js"] = True
    import json as _json
    _sm_pagina_js(_JS_SCAN.replace("__MSG__", _json.dumps(_MSG_SCAN, ensure_ascii=False)))


def sm_leggi_risposta_live(valore):
    """Il testo mandato dal browser dopo la scansione in diretta: lista di (formato, testo) oppure ('errore', motivo)."""
    import json as _json
    corpo = str(valore or "").rpartition("|")[0] or str(valore or "")
    if corpo.startswith("errore|"):
        return "errore", corpo.split("|", 1)[1]
    try:
        return "ok", [(str(f), str(t)) for f, t in _json.loads(corpo)]
    except Exception:
        return "errore", "risposta non valida"


# ---------------------------------------------------------------------------------------------------------------------
# Il pezzo di schermata
# ---------------------------------------------------------------------------------------------------------------------
def sm_prepara(codici, dati_foto, conosciuti):
    """Dai codici letti (e, se c'è la foto, dal testo stampato) al dizionario da ricopiare nel modulo. Aggiunge '_errore' se non si capisce niente."""
    info = sm_interpreta(codici or [])
    pref = {"scadenza": info["scadenza"], "lotto": info["lotto"], "aic": info["aic"], "gtin": info["gtin"], "ean": info["ean"],
            "_letti": info["letti"], "_origine": "", "_da_testo": False}
    if dati_foto and (not pref["scadenza"] or not pref["lotto"]):          # scatola senza DataMatrix: provo a leggere la data scritta
        try:
            ocr = sm_ocr_scatola(dati_foto)
        except Exception:
            ocr = {}
        if ocr.get("scadenza") and not pref["scadenza"]:
            pref["scadenza"], pref["_da_testo"] = ocr["scadenza"], True
        if ocr.get("lotto") and not pref["lotto"]:
            pref["lotto"] = ocr["lotto"]
    if not any(pref[k] for k in ("scadenza", "lotto", "aic", "gtin", "ean")):
        return {"_errore": "non vedo né un codice né una data di scadenza"}
    noto = sm_trova_in_memoria(conosciuti, info)
    if noto:
        pref.update({k: noto.get(k, "") for k in ("nome", "marca", "principio", "dosaggio", "forma", "categoria")})
        pref["_origine"] = "casa"
    elif info["aic"]:
        with st.spinner("Cerco il medicinale nell'elenco AIFA…"):
            try:
                aifa = sm_cerca_aifa(info["aic"])
            except Exception:
                aifa = None
        if aifa:
            pref.update({k: aifa.get(k, "") for k in ("nome", "marca", "principio", "dosaggio", "forma")})
            pref["_origine"], pref["categoria"] = "aifa", "Farmaco"
    if not pref["_origine"] and (info["ean"] or info["gtin"]):
        with st.spinner("Cerco il prodotto negli elenchi pubblici…"):
            trovato = sm_cerca_ean(info["ean"] or info["gtin"].lstrip("0"))
        if trovato:
            pref.update({k: trovato.get(k, "") for k in ("nome", "marca", "categoria")})
            pref["_origine"] = "ean"
    return pref


def sm_blocco(elenco_conosciuti, chiave="scanmed"):
    """«Inquadra la scatola»: scansione in diretta, oppure foto (scattata o scelta). Ritorna i dati da ricopiare nel modulo (dizionario, può essere vuoto).
    elenco_conosciuti = medicinali già conosciuti dalla famiglia (dizionari con nome, principio, dosaggio, forma, aic, gtin)."""
    sm_inietta_scansione()
    with st.container(key="scandiretta_" + chiave):
        st.button("🎥 Scansiona in diretta", key=f"scandiretta_btn_{chiave}", type="primary", width="stretch")
    with st.container(key="nascosti_live_" + chiave):
        valore_live = st.text_input(f"scan-diretta-{chiave}", key=f"{chiave}_live", label_visibility="collapsed")
    with st.container(key="azioni_foto_" + chiave):
        c_cam, c_gal = st.columns(2, gap="small")
        premuto_cam = c_cam.button("📷 Scatta una foto", key=f"scatta_{chiave}", width="stretch")
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
    st.caption("Tocca **Scansiona in diretta** e inquadra il **quadratino** (DataMatrix) o le **barre**, da vicino e con buona luce. "
               "Se il telefono non la permette, scatta una foto: leggo anche la scadenza scritta sulla scatola.")

    # --- scansione in diretta
    if valore_live and valore_live != st.session_state.get(f"{chiave}_live_visto"):
        st.session_state[f"{chiave}_live_visto"] = valore_live
        esito, dati = sm_leggi_risposta_live(valore_live)
        if esito == "errore":
            motivo = {"nonsupp": "questo browser non permette la scansione in diretta: scatta una foto", "NotAllowedError": "non hai dato il permesso alla fotocamera",
                      "NotFoundError": "non trovo la fotocamera", "NotReadableError": "la fotocamera è usata da un'altra app"}.get(dati, dati)
            st.session_state["sm_prefill"] = {"_errore": motivo}
        else:
            st.session_state["sm_prefill"] = sm_prepara(dati, None, elenco_conosciuti)

    # --- foto (scattata o scelta)
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
    if file is not None:
        ident_f = getattr(file, "file_id", None) or f"{file.name}{file.size}"
        if st.session_state.get("sm_elaborata") != ident_f:           # ogni foto si legge una volta sola
            st.session_state["sm_elaborata"] = ident_f
            dati = file.getvalue()
            with st.spinner("Leggo il codice e la scadenza…"):
                codici = sm_leggi_codici(dati)
                if codici is None:
                    codici = []
                st.session_state["sm_prefill"] = sm_prepara(codici, dati, elenco_conosciuti)

    risultato = st.session_state.get("sm_prefill") or {}
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
                righe.append(f"scadenza {sm_data_it(risultato['scadenza'])}" + (" (letta dal testo: controllala)" if risultato.get("_da_testo") else ""))
            if risultato.get("lotto"):
                righe.append(f"lotto {risultato['lotto']}")
            st.success("📦 Letto dalla scatola: " + " · ".join(righe))
            if risultato.get("_origine") == "casa":
                st.info(f"✅ Lo conosco: **{risultato.get('nome', '')}** è già in casa. Ho ricopiato nome, principio attivo, dosaggio e forma.")
            elif risultato.get("_origine") == "aifa":
                st.info(f"✅ Trovato nell'elenco AIFA: **{risultato.get('nome', '')}**. Controlla che sia giusto prima di salvare.")
            elif risultato.get("_origine") == "ean":
                st.info(f"✅ Trovato in un elenco pubblico (Open Food Facts): **{risultato.get('nome', '')}**"
                        + (f", categoria «{risultato['categoria']}»" if risultato.get("categoria") else "") + ". Controlla che sia giusto prima di salvare.")
            else:
                st.info("Non conosco ancora questo medicinale: scrivi il nome una volta, dalla prossima volta lo riconosco da solo.")
        if st.button("✖ Togli la scansione", key=f"{chiave}_togli"):
            st.session_state.pop("sm_prefill", None)        # la foto resta nel campo nascosto: non va riletta
            st.rerun()
    return {k: v for k, v in risultato.items() if not k.startswith("_") and v}
