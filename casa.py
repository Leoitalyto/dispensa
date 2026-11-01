# -*- coding: utf-8 -*-
"""SEZIONE «CASA»: i beni della casa, i loro manuali e documenti, le manutenzioni.

È una sezione NUOVA e autonoma: non modifica nessuna funzione esistente. Si aggancia alla Home e alla navigazione "avvolgendo" due funzioni già presenti
(icona_farmacia della Home e schermata_farmacia, che smista le sezioni) e per tutto il resto usa quello che c'è già: salvataggio dei dati, archivio dei file,
sistema di invio (email, WhatsApp, Telegram…), lettura del testo dalle foto (OCR) e la guida con l'assistente. I dati stanno nel file personale, sotto la chiave «casa».

DATI («casa»):
  beni          {id, nome, categoria, sottocategoria, marca, modello, seriale, stanza, acquisto, garanzia_fino, note, creato_il}
  documenti     {id, bene_id, tipo, titolo, categoria, sottocategoria, marca, modello, seriale, data_doc, lingua, link, note,
                 file          il documento ORIGINALE, identico byte per byte (id, nome, mime, sha256, dimensione, originale=True)
                 riconosciuto  i dati letti dal documento, congelati com'erano (con affidabilità e fonte di ogni dato)
                 classificazione  la proposta automatica (tipo, categoria, sottocategoria, bene)
                 conferma      chi l'ha confermata, quando, e cosa ha corretto rispetto alla proposta}
  manutenzioni  {id, bene_id, data, tipo, descrizione, ditta, costo, prossima, documento_id, note}
Quattro livelli separati, come richiesto: documento originale · dati riconosciuti · classificazione · conferma dell'utente. Un errore del riconoscimento
automatico non tocca mai l'originale e non si salva niente senza la conferma di chi usa l'app.
Caricato da app_dispensa.py dopo navigazione.py e trasferimento.py."""
import base64
import hashlib
import io
import html as _html_ca
import json
import re
import urllib.parse
import uuid
from datetime import date, datetime

import streamlit as st

CA_TIPI = ["Manuale d'uso", "Manuale di installazione", "Manuale di manutenzione", "Scheda tecnica", "Certificato di garanzia", "Libretto di impianto",
           "Dichiarazione di conformità", "Istruzioni di montaggio", "Fattura o scontrino", "Documentazione di un intervento",
           "Bolletta o fattura", "Contratto", "Polizza assicurativa", "Ricevuta di pagamento", "Lettera o comunicazione", "Altro"]
_CA_TIPI_MANUALI = {"Manuale d'uso", "Manuale di installazione", "Manuale di manutenzione", "Scheda tecnica", "Certificato di garanzia", "Libretto di impianto", "Dichiarazione di conformità", "Istruzioni di montaggio"}
CA_LINGUE = {"it": "Italiano", "en": "Inglese", "de": "Tedesco", "fr": "Francese", "es": "Spagnolo", "": "Non so"}
CA_STANZE = ["Cucina", "Soggiorno", "Camera da letto", "Bagno", "Ingresso", "Studio", "Lavanderia", "Garage", "Cantina", "Giardino", "Terrazzo", "Tutta la casa", "Altro"]
CA_TIPI_MANUTENZIONE = ["Controllo", "Manutenzione ordinaria", "Manutenzione straordinaria", "Riparazione", "Pulizia o sostituzione filtri", "Altro"]
_CA_MIME = {"application/pdf", "image/jpeg", "image/png", "image/webp", "text/plain"}
_CA_MAX_BYTE = 8 * 1024 * 1024
CA_CATEGORIE = {
    "Riscaldamento e acqua calda": ["Caldaia", "Scaldabagno", "Stufa o camino", "Pompa di calore", "Termostato e cronotermostato", "Radiatori e termosifoni"],
    "Climatizzazione": ["Condizionatore", "Deumidificatore", "Purificatore d'aria", "Ventilatore"],
    "Elettrodomestici": ["Frigorifero", "Congelatore", "Lavatrice", "Asciugatrice", "Lavastoviglie", "Forno", "Piano cottura", "Microonde", "Cappa", "Altro elettrodomestico"],
    "TV e elettronica": ["Televisore", "Decoder e lettore", "Impianto audio", "Computer e stampante", "Rete e modem", "Altro dispositivo"],
    "Sicurezza e allarmi": ["Allarme e antifurto", "Videocitofono e telecamere", "Rilevatore di fumo o gas", "Serratura e cancello"],
    "Impianti elettrici e idraulici": ["Impianto elettrico", "Impianto idraulico", "Fotovoltaico", "Pompa e autoclave"],
    "Attrezzature e utensili": ["Utensile elettrico", "Giardinaggio", "Pulizia e aspirazione", "Altra attrezzatura"],
    "Altro": ["Altro"],
}

# parole che fanno riconoscere (categoria, sottocategoria)
_CA_PAROLE = [
    ("Riscaldamento e acqua calda", "Caldaia", ["caldaia", "boiler", "generatore di calore", "condensazione", "boilers", "heating boiler", "kessel", "chaudiere", "caldera"]),
    ("Riscaldamento e acqua calda", "Scaldabagno", ["scaldabagno", "scaldacqua", "water heater", "warmwasserspeicher"]),
    ("Riscaldamento e acqua calda", "Stufa o camino", ["stufa", "camino", "pellet", "inserto"]),
    ("Riscaldamento e acqua calda", "Pompa di calore", ["pompa di calore", "heat pump", "waermepumpe"]),
    ("Riscaldamento e acqua calda", "Termostato e cronotermostato", ["cronotermostato", "termostato", "thermostat"]),
    ("Climatizzazione", "Condizionatore", ["condizionatore", "climatizzatore", "split", "air conditioner", "klimaanlage", "climatiseur", "aire acondicionado"]),
    ("Climatizzazione", "Deumidificatore", ["deumidificatore", "dehumidifier"]),
    ("Climatizzazione", "Purificatore d'aria", ["purificatore", "air purifier"]),
    ("Elettrodomestici", "Frigorifero", ["frigorifero", "frigo", "refrigerator", "fridge", "kuehlschrank", "refrigerateur", "frigorifico", "combinato"]),
    ("Elettrodomestici", "Congelatore", ["congelatore", "freezer", "gefrierschrank"]),
    ("Elettrodomestici", "Lavatrice", ["lavatrice", "washing machine", "waschmaschine", "lave-linge", "lavadora"]),
    ("Elettrodomestici", "Asciugatrice", ["asciugatrice", "tumble dryer", "dryer", "trockner"]),
    ("Elettrodomestici", "Lavastoviglie", ["lavastoviglie", "dishwasher", "geschirrspueler", "lave-vaisselle", "lavavajillas"]),
    ("Elettrodomestici", "Forno", ["forno", "oven", "backofen", "four "]),
    ("Elettrodomestici", "Piano cottura", ["piano cottura", "piano di cottura", "cooktop", "hob", "kochfeld"]),
    ("Elettrodomestici", "Microonde", ["microonde", "microwave", "mikrowelle"]),
    ("Elettrodomestici", "Cappa", ["cappa aspirante", "cappa", "range hood", "dunstabzugshaube"]),
    ("TV e elettronica", "Televisore", ["televisore", "televisione", "smart tv", "led tv", "oled", "qled", "television", "fernseher", "telefunken"]),
    ("TV e elettronica", "Impianto audio", ["soundbar", "altoparlante", "speaker", "impianto audio", "casse"]),
    ("TV e elettronica", "Computer e stampante", ["stampante", "printer", "notebook", "laptop", "computer", "tablet"]),
    ("TV e elettronica", "Rete e modem", ["router", "modem", "ripetitore wifi", "access point"]),
    ("TV e elettronica", "Decoder e lettore", ["decoder", "lettore dvd", "blu-ray", "set-top"]),
    ("Sicurezza e allarmi", "Allarme e antifurto", ["antifurto", "allarme", "centralina", "sirena", "alarm system"]),
    ("Sicurezza e allarmi", "Videocitofono e telecamere", ["videocitofono", "citofono", "telecamera", "videosorveglianza", "camera ip"]),
    ("Sicurezza e allarmi", "Rilevatore di fumo o gas", ["rilevatore di fumo", "rilevatore di gas", "smoke detector", "co detector"]),
    ("Sicurezza e allarmi", "Serratura e cancello", ["serratura", "cancello", "automazione cancello", "porta blindata"]),
    ("Impianti elettrici e idraulici", "Fotovoltaico", ["fotovoltaico", "inverter", "pannelli solari", "photovoltaic"]),
    ("Impianti elettrici e idraulici", "Impianto elettrico", ["quadro elettrico", "interruttore differenziale", "salvavita", "impianto elettrico", "contatore elettrico"]),
    ("Impianti elettrici e idraulici", "Impianto idraulico", ["impianto idraulico", "rubinetto", "miscelatore", "scarico", "addolcitore"]),
    ("Impianti elettrici e idraulici", "Pompa e autoclave", ["autoclave", "pompa sommersa", "elettropompa"]),
    ("Attrezzature e utensili", "Utensile elettrico", ["trapano", "avvitatore", "smerigliatrice", "sega", "levigatrice", "power tool"]),
    ("Attrezzature e utensili", "Giardinaggio", ["tagliaerba", "decespugliatore", "tosaerba", "soffiatore", "motosega", "lawn mower"]),
    ("Attrezzature e utensili", "Pulizia e aspirazione", ["aspirapolvere", "idropulitrice", "scopa elettrica", "vacuum cleaner", "robot aspirapolvere", "staubsauger"]),
]
_CA_MARCHE = ["Bosch", "Siemens", "Whirlpool", "Samsung", "LG", "Beko", "Candy", "Hoover", "Ariston", "Indesit", "Hotpoint", "Electrolux", "AEG", "Zanussi", "Miele", "Smeg",
              "Haier", "Hisense", "Panasonic", "Philips", "Sony", "Sharp", "Toshiba", "Telefunken", "TCL", "Xiaomi", "Apple", "Daikin", "Mitsubishi", "Fujitsu", "Midea", "Hitachi",
              "Vaillant", "Baxi", "Immergas", "Beretta", "Riello", "Viessmann", "Junkers", "Ferroli", "Bertelli", "Saunier Duval", "Tecnogas", "Chaffoteaux", "Lg Electronics",
              "De'Longhi", "Delonghi", "Dyson", "Rowenta", "Bialetti", "Kenwood", "Bticino", "Vimar", "Gewiss", "Hager", "Abb", "Legrand", "Ajax", "Urmet", "Comelit", "Fermax",
              "Makita", "Black+Decker", "Black & Decker", "Stihl", "Husqvarna", "Karcher", "Kärcher", "Einhell", "Bosch Professional", "Brother", "Epson", "Canon", "Hp", "Tp-Link", "Netgear",
              "Fritz", "Teka", "Franke", "Foster", "Rex", "Electrolux Rex", "Ignis", "Liebherr", "Gorenje", "Bauknecht", "Neff", "Gaggenau", "Grundig", "Brandt", "Fagor"]
_CA_STOPWORD = {
    "it": {"il", "lo", "la", "gli", "le", "di", "del", "della", "dei", "che", "per", "con", "non", "una", "uno", "sono", "questo", "questa", "prima", "dopo", "utilizzo", "istruzioni", "apparecchio", "uso", "della"},
    "en": {"the", "and", "of", "to", "is", "in", "for", "with", "this", "that", "are", "not", "before", "use", "instructions", "appliance", "you", "your", "please", "warning"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "mit", "fuer", "für", "bedienungsanleitung", "gerät", "geraet", "vor", "sie", "bitte", "sicherheitshinweise"},
    "fr": {"le", "la", "les", "et", "de", "des", "du", "pour", "avec", "pas", "est", "avant", "utilisation", "appareil", "vous", "notice", "veuillez"},
    "es": {"el", "los", "las", "y", "de", "del", "para", "con", "no", "es", "antes", "uso", "aparato", "usted", "instrucciones", "manual"},
}
_CA_TIPI_PAROLE = [
    ("Manuale di installazione", ["manuale di installazione", "istruzioni per l'installazione", "istruzioni di installazione", "installation manual", "installation instructions", "montageanleitung", "notice d'installation", "manual de instalacion", "installatore"]),
    ("Manuale di manutenzione", ["manuale di manutenzione", "manutenzione ordinaria", "maintenance manual", "wartungsanleitung", "servicing", "libretto di manutenzione"]),
    ("Libretto di impianto", ["libretto di impianto", "libretto d'impianto", "rapporto di controllo", "rapporto di efficienza energetica", "libretto di centrale"]),
    ("Certificato di garanzia", ["certificato di garanzia", "condizioni di garanzia", "garanzia convenzionale", "warranty card", "warranty certificate", "garantie", "garantia"]),
    ("Dichiarazione di conformità", ["dichiarazione di conformit", "declaration of conformity", "konformitaetserklaerung", "dichiarazione ce", "marcatura ce"]),
    ("Istruzioni di montaggio", ["istruzioni di montaggio", "istruzioni per il montaggio", "assembly instructions", "assembly guide", "montaggio"]),
    ("Scheda tecnica", ["scheda tecnica", "datasheet", "data sheet", "technical data", "dati tecnici", "caratteristiche tecniche", "technische daten", "fiche technique", "etichetta energetica"]),
    ("Fattura o scontrino", ["fattura", "scontrino", "ricevuta fiscale", "invoice", "receipt", "rechnung", "documento commerciale"]),
    ("Documentazione di un intervento", ["rapporto di intervento", "foglio di intervento", "intervento tecnico", "service report", "verbale di intervento"]),
    ("Manuale d'uso", ["manuale d'uso", "manuale di istruzioni", "istruzioni per l'uso", "libretto di istruzioni", "user manual", "owner's manual", "operating instructions", "instruction manual",
                       "bedienungsanleitung", "gebrauchsanweisung", "mode d'emploi", "notice d'utilisation", "manual de usuario", "manual de instrucciones", "istruzioni d'uso", "manuale utente"]),
]
_CA_MESI_NOMI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
                 "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}


def _ca_sha(b):
    return hashlib.sha256(b).hexdigest()


def _ca_norm(t):
    import unicodedata
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.category(c).startswith("M"))


# ---------------------------------------------------------------------------------------------------------------------
# Lettura del testo
# ---------------------------------------------------------------------------------------------------------------------
def _ca_ocr_pdf(dati, max_pagine=3):
    """Per i PDF che sono solo immagini (scansioni): trasforma le prime pagine in immagini e le legge con l'OCR, come una foto. Ritorna il testo (vuoto se non riesce)."""
    if not ("_doc_ocr_lingue" in globals() and "_doc_tesseract" in globals() and _doc_ocr_lingue()):
        return ""
    try:
        try:
            import pymupdf as _mu
        except Exception:
            import fitz as _mu
        from PIL import Image
        doc = _mu.open(stream=dati, filetype="pdf")
        parti = []
        for i in range(min(max_pagine, doc.page_count)):
            pix = doc[i].get_pixmap(dpi=170, alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            im.thumbnail((2400, 2400))
            parti.append(_doc_tesseract(im, "6"))
            if i == 0:                                                       # la prima pagina (copertina, dati dell'apparecchio) si legge con due metodi
                parti.append(_doc_tesseract(im, "11"))
        doc.close()
        return "\n".join(parti)
    except Exception:
        return ""


def ca_estrai_testo(nome, mime, dati, max_pagine=8, max_car=24000):
    """(testo, info). Dai PDF con testo si legge il testo; dalle foto e dalle scansioni, se c'è, con l'OCR. info = {pagine, titolo, data_meta, scansione, metodo}."""
    info = {"pagine": None, "titolo": "", "data_meta": None, "scansione": False, "metodo": ""}
    if mime == "text/plain":                                                  # il testo di un messaggio di posta (senza allegati)
        try:
            testo = (dati or b"").decode("utf-8")
        except UnicodeDecodeError:
            testo = (dati or b"").decode("latin-1", "replace")
        info["metodo"], info["testo_p1"] = "testo del messaggio", testo[:6000]
        return testo[:max_car], info
    if mime == "application/pdf":
        try:                                                                  # 1) PyMuPDF, se c'è: tiene meglio in ordine righe, colonne e tabelle
            try:
                import pymupdf as _mu
            except Exception:
                import fitz as _mu
            doc = _mu.open(stream=dati, filetype="pdf")
            info["pagine"] = doc.page_count
            try:
                meta = doc.metadata or {}
                info["titolo"] = str(meta.get("title") or "").strip()
                m = re.match(r"D:(\d{4})(\d{2})(\d{2})", str(meta.get("creationDate") or ""))
                if m:
                    info["data_meta"] = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                pass
            parti = []
            for i in range(min(max_pagine, doc.page_count)):
                try:
                    parti.append(doc[i].get_text("text", sort=True) or "")
                except Exception:
                    parti.append("")
            doc.close()
            testo = "\n".join(parti)[:max_car]
            if len(re.sub(r"\s+", "", testo)) >= 40:
                info["metodo"], info["testo_p1"] = "testo del PDF", (parti[0] if parti else "")[:6000]
                return testo, info
        except Exception:
            pass
        try:                                                                  # 2) pypdf
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(dati))
            info["pagine"] = len(r.pages)
            try:
                meta = r.metadata or {}
                info["titolo"] = str(meta.get("/Title") or "").strip()
                m = re.match(r"D:(\d{4})(\d{2})(\d{2})", str(meta.get("/CreationDate") or ""))
                if m:
                    info["data_meta"] = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                pass
            parti = []
            for pag in list(r.pages)[:max_pagine]:
                try:
                    parti.append(pag.extract_text() or "")
                except Exception:
                    continue
            testo = "\n".join(parti)[:max_car]
            info["metodo"], info["testo_p1"] = "testo del PDF", (parti[0] if parti else "")[:6000]
            if len(re.sub(r"\s+", "", testo)) < 40:
                ocr = _ca_ocr_pdf(dati)                                      # PDF senza testo = scansione: si prova a leggerlo come una foto
                if len(re.sub(r"\s+", "", ocr)) >= 40:
                    info["metodo"], info["ocr_pdf"] = "lettura del PDF scansionato (OCR)", True
                    return ocr[:max_car], info
                info["scansione"] = True
                return "", info
            return testo, info
        except Exception:
            ocr = _ca_ocr_pdf(dati)
            if len(re.sub(r"\s+", "", ocr)) >= 40:
                info["metodo"], info["ocr_pdf"] = "lettura del PDF scansionato (OCR)", True
                return ocr[:max_car], info
            info["scansione"] = True
            return "", info
    if "_doc_ocr_lingue" in globals() and "_doc_tesseract" in globals() and _doc_ocr_lingue():
        try:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
            im.thumbnail((2400, 2400))
            testi = [_doc_tesseract(im, "6"), _doc_tesseract(im, "11")]
            info["metodo"] = "lettura della foto (OCR)"
            return "\n".join(testi)[:max_car], info
        except Exception:
            return "", info
    return "", info


# ---------------------------------------------------------------------------------------------------------------------
# Riconoscimento dei dati
# ---------------------------------------------------------------------------------------------------------------------
def ca_lingua(testo):
    parole = re.findall(r"[a-zà-ÿ']+", (testo or "").lower())
    if len(parole) < 12:
        return "", "bassa"
    punti = {l: sum(1 for p in parole if p in sw) for l, sw in _CA_STOPWORD.items()}
    ordine = sorted(punti.items(), key=lambda x: -x[1])
    (l1, p1), (_, p2) = ordine[0], ordine[1]
    if p1 < 3:
        return "", "bassa"
    return l1, ("alta" if p1 >= 2 * max(p2, 1) and p1 >= 6 else "media")


def ca_tipo(testo, nome_file=""):
    t = _ca_norm((nome_file or "") + "\n" + (testo or "")[:6000])
    migliore, punti_m = "", 0
    for tipo, parole in _CA_TIPI_PAROLE:
        punti = sum(t.count(_ca_norm(p)) for p in parole)
        if tipo == "Fattura o scontrino":
            punti = max(0, punti - 1)                                         # una sola parola «fattura» non basta: nei manuali compare per ricordare di conservarla
        if punti > punti_m or (punti == punti_m and punti and tipo.startswith("Manuale")):
            migliore, punti_m = tipo, punti
    if migliore:
        return migliore, ("alta" if punti_m >= 3 else "media")
    return "", "bassa"


def ca_categoria(testo, nome_file=""):
    """(categoria, sottocategoria, affidabilità). Dà più peso al nome del file e all'inizio del documento."""
    inizio = _ca_norm((nome_file or "") + " " + (testo or "")[:1500])
    tutto = _ca_norm(testo or "")
    miglior, punti_m = None, 0
    for cat, sotto, parole in _CA_PAROLE:
        p = 0
        for w in parole:
            wn = _ca_norm(w)
            p += 4 * inizio.count(wn) + min(tutto.count(wn), 12)
        if p > punti_m:
            miglior, punti_m = (cat, sotto), p
    if miglior and punti_m >= 3:
        return miglior[0], miglior[1], ("alta" if punti_m >= 12 else "media")
    return "", "", "bassa"


def ca_marca(testo, nome_file=""):
    """(marca, affidabilità): la marca più citata all'inizio del documento (o nel nome del file); poi quella dopo «prodotto da / fabbricante»."""
    inizio = (nome_file or "") + " " + (testo or "")[:2500]
    migliore, punti_m = "", 0
    for marca in _CA_MARCHE:
        n = len(re.findall(r"(?<![A-Za-z])" + re.escape(marca) + r"(?![A-Za-z])", inizio, re.I)) * 3 + len(re.findall(r"(?<![A-Za-z])" + re.escape(marca) + r"(?![A-Za-z])", testo or "", re.I))
        if n > punti_m:
            migliore, punti_m = marca, n
    if migliore:
        migliore = {"Lg Electronics": "LG", "Delonghi": "De'Longhi", "Hp": "HP", "Abb": "ABB", "Aeg": "AEG", "Tcl": "TCL"}.get(migliore, migliore)
        return migliore, ("alta" if punti_m >= 4 else "media")
    m = re.search(r"(?:prodotto da|fabbricante|fabbricato da|costruttore|manufacturer|produced by|made by|distribuito da|hersteller)\s*[:.]?\s*([A-Z][A-Za-z0-9&.\- ]{2,30})", testo or "")
    if m:
        return m.group(1).strip().split("\n")[0].strip(" .-"), "bassa"
    return "", "bassa"


_RE_MODELLO = re.compile(r"(?<![A-Za-z])(?:mod(?:ello|el|\.)|model(?:l)?|tipo|type|art(?:icolo|\.)|cod(?:ice)?\.?|ref(?:erence|\.)?|modell)\s*(?:n(?:umber|\.)?|no\.?|nr\.?|:)?\s*[:.#]?\s*"
                         r"([A-Z0-9][A-Z0-9\-/.]{0,24}(?:[ ][A-Z0-9][A-Z0-9\-/.]{1,14})?)", re.I)
_RE_SERIALE = re.compile(r"(?<![A-Za-z])(?:s/?n\b|serial(?:\s*(?:number|no\.?|nr\.?))?|n(?:umero|\.|°)?\s*(?:di\s*)?serie|matricola|seriennummer|n[º°]\s*de\s*serie|num[ée]ro de s[ée]rie)\s*[:.#]?\s*([A-Z0-9][A-Z0-9\-]{5,24})", re.I)


def _cerca_tutti(modello, testo):
    """Tutte le corrispondenze, anche vicine: se una non va bene si riparte da un carattere dopo (così non si «mangia» la successiva)."""
    pos = 0
    while True:
        m = modello.search(testo, pos)
        if not m:
            return
        yield m
        pos = m.start() + 1


def ca_modello(testo, marca=""):
    """(modello, affidabilità): dalle etichette «Modello / Model / Tipo…»; altrimenti il codice scritto accanto alla marca."""
    t = testo or ""
    for m in _cerca_tutti(_RE_MODELLO, t):
        pezzi = m.group(1).strip(".-/").split()
        if len(pezzi) == 2 and not re.search(r"\d", pezzi[1]):
            pezzi = pezzi[:1]
        v = " ".join(pezzi)
        if re.search(r"\d", v) and len(v) >= 4 and not re.fullmatch(r"\d{4}", v) and v.lower() not in ("1234", "000000"):
            return v.upper(), "alta"
    if marca:
        m = re.search(re.escape(marca) + r"\s+([A-Z][A-Z0-9\-/]{3,20})", t)
        if m and re.search(r"\d", m.group(1)):
            return m.group(1).upper(), "media"
    return "", "bassa"


def ca_seriale(testo):
    for m in _cerca_tutti(_RE_SERIALE, testo or ""):
        v = m.group(1).strip(".-")
        if re.search(r"\d", v):
            return v.upper(), "alta"
    return "", "bassa"


def ca_data(testo, data_meta=None, anni_validi=(1990, 2100)):
    """(data, fonte, affidabilità). Cerca date vicine a parole come «data / edizione / revisione»; poi una data qualsiasi; poi i metadati del PDF."""
    t = testo or ""
    def costruisci(g, m, a):
        try:
            a = int(a); a = a + 2000 if a < 100 else a
            if not (anni_validi[0] <= a <= anni_validi[1]):
                return None
            return date(a, int(m), int(g) if g else 1)
        except (ValueError, TypeError):
            return None
    chiave = r"(?:data|date|datum|edizione|edition|rev(?:isione|\.)?|revision|versione|version|aggiornamento|stand|fecha|publicado)"
    for m in re.finditer(chiave + r"\s*[:.]?\s*(?:(\d{1,2})[./\-])?(\d{1,2})[./\-](\d{4}|\d{2})\b", t, re.I):
        d = costruisci(m.group(1), m.group(2), m.group(3))
        if d:
            return d, "testo", "media"
    for m in re.finditer(chiave + r"\s*[:.]?\s*(\d{1,2})?\s*(" + "|".join(_CA_MESI_NOMI) + r")\s+(\d{4})", t, re.I):
        d = costruisci(m.group(1), _CA_MESI_NOMI[m.group(2).lower()], m.group(3))
        if d:
            return d, "testo", "media"
    for m in re.finditer(r"(?:ed(?:izione|ition|\.)|rev\.?)\s*[:.]?\s*(?:\d+\s*[-/ ])?(20\d{2}|19\d{2})\b", t, re.I):
        d = costruisci(None, 1, m.group(1))
        if d:
            return d, "testo", "bassa"
    for m in re.finditer(r"\b(\d{1,2})[./\-](\d{1,2})[./\-](20\d{2}|19\d{2})\b", t):
        d = costruisci(m.group(1), m.group(2), m.group(3))
        if d:
            return d, "testo", "bassa"
    if data_meta:
        return data_meta, "dati del file", "bassa"
    return None, "", "bassa"


# ---------------------------------------------------------------------------------------------------------------------
# BOLLETTE, FATTURE E DOCUMENTI DI CASA (non solo manuali): chi li ha emessi, di cosa parlano, quanto, quando, per quale periodo
# ---------------------------------------------------------------------------------------------------------------------
CA_ARGOMENTI = ["Luce", "Gas", "Luce e Gas", "Acqua", "Telefono e Internet", "Rifiuti (TARI)", "Condominio", "Assicurazioni", "Tasse e imposte",
                "Contratti, affitto e mutuo", "Interventi e riparazioni", "Acquisti e garanzie", "Manuali e istruzioni", "Altro"]
_CA_ICONE_ARG = {"Luce": "💡", "Gas": "🔥", "Luce e Gas": "💡🔥", "Acqua": "💧", "Telefono e Internet": "📞", "Rifiuti (TARI)": "🗑️", "Condominio": "🏢", "Assicurazioni": "🛡️",
                 "Tasse e imposte": "🏛️", "Contratti, affitto e mutuo": "📝", "Interventi e riparazioni": "🛠️", "Acquisti e garanzie": "🧾", "Manuali e istruzioni": "📚", "Altro": "📁"}
_CA_ARG_APPARECCHIO = {"Manuali e istruzioni", "Acquisti e garanzie"}
_CA_TIPI_UTENZA = ["Bolletta o fattura", "Contratto", "Polizza assicurativa", "Ricevuta di pagamento", "Lettera o comunicazione"]

# parole che fanno capire l'argomento: (parola, peso)
_CA_PAROLE_ARG = {
    "Luce": [("energia elettrica", 3), ("kwh", 3), (" pod ", 4), ("potenza impegnata", 3), ("potenza disponibile", 2), ("bolletta luce", 4), ("fattura luce", 4), ("fornitura di energia elettrica", 4),
             ("servizio elettrico", 2), ("mercato libero dell'energia elettrica", 3), ("energia attiva", 2), ("trasporto dell'energia elettrica", 3)],
    "Gas": [("gas naturale", 3), ("smc", 3), (" pdr ", 4), ("bolletta gas", 4), ("fattura gas", 4), ("gas metano", 3), ("fornitura di gas", 4), ("potere calorifico", 3), ("metri cubi", 1), ("coefficiente c", 2)],
    "Acqua": [("servizio idrico", 4), ("acquedotto", 3), ("fognatura", 3), ("depurazione", 3), ("acqua potabile", 3), ("consumo di acqua", 3), ("bolletta acqua", 4), ("fattura acqua", 4), ("idrico integrato", 4)],
    "Telefono e Internet": [("linea fissa", 3), ("fibra", 2), ("adsl", 3), ("ftth", 3), ("internet", 2), ("giga", 2), ("traffico", 2), ("numero di telefono", 3), ("telefonia", 3), ("chiamate", 2), ("canone mensile", 1), ("sim ", 1), ("offerta mobile", 2)],
    "Rifiuti (TARI)": [("tari", 5), ("tassa rifiuti", 5), ("tariffa rifiuti", 5), ("rifiuti", 3), ("igiene urbana", 4), ("raccolta differenziata", 2)],
    "Condominio": [("condominio", 4), ("condominiale", 4), ("amministratore di condominio", 4), ("millesimi", 4), ("quota condominiale", 4), ("rendiconto condominiale", 4)],
    "Assicurazioni": [("polizza", 4), ("assicurazione", 3), ("premio", 2), ("massimale", 3), ("contraente", 3), ("assicurato", 3), ("rc auto", 3), ("rca", 2)],
    "Tasse e imposte": [("imu", 5), ("tasi", 5), ("f24", 4), ("agenzia delle entrate", 3), ("imposta", 2), ("tributo", 2), ("bollo auto", 3), ("canone rai", 4), ("cartella esattoriale", 5), ("agenzia delle entrate-riscossione", 5)],
    "Contratti, affitto e mutuo": [("contratto di locazione", 5), ("canone di locazione", 4), ("affitto", 3), ("locatore", 3), ("conduttore", 3), ("mutuo", 4), ("rata del mutuo", 4), ("piano di ammortamento", 4)],
    "Interventi e riparazioni": [("intervento", 2), ("riparazione", 3), ("sostituzione", 2), ("manodopera", 3), ("assistenza tecnica", 3), ("idraulico", 3), ("elettricista", 3), ("manutenzione", 2), ("tecnico", 1), ("ricambi", 2)],
    "Acquisti e garanzie": [("scontrino", 4), ("ricevuta fiscale", 3), ("documento commerciale", 4), ("garanzia", 1), ("acquisto", 1)],
}
# parole che dicono «questa è una bolletta / fattura / avviso di pagamento»: (parola, peso); le «forti» da sole fanno quasi una fattura
_CA_PAROLE_FATTURA = [("fattura", 2), ("bolletta", 2), ("totale da pagare", 3), ("importo da pagare", 3), ("importo dovuto", 3), ("totale fattura", 3), ("totale bolletta", 3), ("totale documento", 3),
                      ("periodo di fatturazione", 3), ("codice cliente", 2), ("numero cliente", 2), ("imponibile", 3), ("iva", 1), ("avviso di pagamento", 3), ("bollettino", 2), ("pagopa", 2),
                      ("scadenza", 1), ("modalita di pagamento", 2), ("addebito", 1), ("partita iva", 1), ("codice fiscale", 1), ("importo", 1), ("rata", 1), ("premio", 1), ("canone", 1)]
_CA_FATTURA_FORTI = ("totale da pagare", "importo da pagare", "importo dovuto", "totale fattura", "totale bolletta", "totale documento", "periodo di fatturazione", "imponibile",
                     "avviso di pagamento", "fattura n", "bolletta n", "numero fattura", "n. fattura", "rata", "premio", "canone di locazione")

# gli enti (aziende, comuni, assicurazioni…) che compaiono più spesso: (nome da mostrare, [pezzi di testo senza accenti])
_CA_ENTI = [
    ("Enel Energia", ["enel energia"]), ("Servizio Elettrico Nazionale", ["servizio elettrico nazionale"]), ("Plenitude (Eni)", ["plenitude", "eni gas e luce", "eni gas e luce"]),
    ("A2A Energia", ["a2a energia", "a2a"]), ("Edison Energia", ["edison energia", "edison"]), ("Hera Comm", ["hera comm", "gruppo hera"]), ("Iren Mercato", ["iren mercato"]),
    ("Acea Energia", ["acea energia"]), ("E.ON Energia", ["e.on energia", "eon energia", "e.on "]), ("Sorgenia", ["sorgenia"]), ("Illumia", ["illumia"]), ("Engie", ["engie"]),
    ("Axpo", ["axpo"]), ("Dolomiti Energia", ["dolomiti energia"]), ("Alperia", ["alperia"]), ("Estra", ["estra energie", "estra "]), ("AGSM AIM", ["agsm aim", "agsm"]),
    ("Green Network", ["green network"]), ("Wekiwi", ["wekiwi"]), ("Octopus Energy", ["octopus energy"]), ("Pulsee", ["pulsee"]), ("Enel", ["enel "]),
    ("SMAT (Torino)", ["smat", "societa metropolitana acque torino"]), ("Acea Ato 2", ["acea ato"]), ("Acquedotto Pugliese", ["acquedotto pugliese"]), ("Publiacqua", ["publiacqua"]),
    ("Veritas", ["veritas"]), ("MM (Milano)", ["metropolitana milanese"]), ("Gaia", ["gaia s.p.a", "gaia spa"]), ("CAP Holding", ["cap holding"]), ("Abbanoa", ["abbanoa"]),
    ("TIM", ["telecom italia", "tim s.p.a", " tim "]), ("Vodafone", ["vodafone"]), ("WindTre", ["windtre", "wind tre"]), ("Iliad", ["iliad"]), ("Fastweb", ["fastweb"]),
    ("Tiscali", ["tiscali"]), ("PosteMobile", ["postemobile", "poste mobile"]), ("Sky Italia", ["sky italia"]), ("Linkem", ["linkem"]), ("EOLO", ["eolo "]),
    ("AMIAT (Torino)", ["amiat"]), ("Iren Ambiente", ["iren ambiente"]), ("AMA (Roma)", ["azienda municipale ambiente"]),
    ("Generali", ["generali italia", "assicurazioni generali"]), ("UnipolSai", ["unipolsai", "unipol sai"]), ("Allianz", ["allianz"]), ("AXA", ["axa assicurazioni", "axa italia"]),
    ("Reale Mutua", ["reale mutua"]), ("Zurich", ["zurich"]), ("Cattolica Assicurazioni", ["cattolica assicurazioni"]), ("Vittoria Assicurazioni", ["vittoria assicurazioni"]),
    ("Poste Assicura", ["poste assicura"]), ("Linear", ["linear assicurazioni"]), ("Genertel", ["genertel"]), ("Direct Line", ["direct line"]),
    ("Agenzia delle Entrate", ["agenzia delle entrate"]),
]
# frasi che dicono con certezza «questa è la prova di un pagamento»…
_CA_RE_RICEVUTA_FORTE = (r"ricevuta di pagamento|quietanza|esito (?:del )?pagamento|pagamento (?:effettuato|eseguito|riuscito|completato|andato a buon fine)|ricevuta (?:pagopa|telematica|di versamento|del bonifico)|"
                         r"contabile|bonifico (?:eseguito|disposto|istantaneo)|attestazione di pagamento|conferma (?:di|del) pagamento|ordine di bonifico|payment receipt|transazione (?:eseguita|completata)")
# …e frasi che compaiono anche DENTRO una bolletta («metodo di pagamento: addebito diretto»): valgono solo per un testo breve (uno screenshot) senza i segni di una bolletta
_CA_RE_RICEVUTA_DEBOLE = r"pagat[oa] in data|pagat[oa] il|addebito diretto|addebito effettuato|addebitato il|pagamento ricevuto|pagamento registrato|saldat[oa]|regolarmente pagat|bolletta pagata|fattura pagata"
_CA_RE_SEGNI_BOLLETTA = (r"totale da pagare|importo da pagare|periodo di fatturazione|periodo di riferimento|importo dovuto|dovrai pagare|da pagare entro|imponibile|potenza impegnata|kwh|smc|\bpod\b|\bpdr\b|"
                         r"scadenza|data fattura|numero fattura|consumo fatturato")
_CA_FORMA_LEGALE = r"(?:S\.?\s?p\.?\s?A\.?|S\.?\s?r\.?\s?l\.?|S\.?\s?c\.?\s?a\.?\s?r\.?\s?l\.?|S\.?\s?n\.?\s?c\.?|S\.?\s?a\.?\s?s\.?|Soc(?:ieta|ietà)?\.?\s+Coop(?:erativa)?\.?)"
_CA_MESI_ABB = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
_CA_RE_DATA = r"(\d{1,2})\s*[./\-]\s*(\d{1,2})\s*[./\-]\s*(\d{4}|\d{2})\b|(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)\.?\s+(\d{4})\b"
_CA_RE_IMPORTO = r"(?:€|eur(?:o)?\.?)?\s*(\d{1,3}(?:\.\d{3})+,\d{2}|\d{1,6},\d{2})(?!\d)"


def _ca_data_da_match(m):
    """Da un risultato di _CA_RE_DATA a un oggetto data (oppure None)."""
    try:
        if m.group(1):
            g, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        else:
            g, a = int(m.group(4)), int(m.group(6))
            n = m.group(5).lower()
            mo = _CA_MESI_NOMI.get(n) or _CA_MESI_ABB.get(n[:3])
        a = a + 2000 if a < 100 else a
        if not (2000 <= a <= 2100):
            return None
        return date(a, mo, g)
    except (ValueError, TypeError):
        return None


def _ca_etichetta(et):
    return re.escape(et).replace(r"\ ", r"\s+")


def _ca_dopo(testo, etichette, regex_valore, finestra=90):
    """Il primo valore che compare DOPO una delle etichette (nell'ordine dato, dalla più sicura alla meno sicura). Ritorna (match, etichetta) o (None, '')."""
    for et in etichette:
        for m in re.finditer(_ca_etichetta(et), testo, re.I):
            v = re.search(regex_valore, testo[m.end(): m.end() + finestra], re.I)
            if v:
                return v, et
    return None, ""


def _ca_importo_str(s):
    """«1.234,56» → «1234.56»."""
    return s.replace(".", "").replace(",", ".")


def ca_importo_fmt(valore):
    """«1234.56» → «1.234,56»."""
    try:
        x = float(str(valore).replace(",", "."))
    except (ValueError, TypeError):
        return str(valore or "")
    s = f"{x:,.2f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def ca_leggi_ente(testo, testo_p1="", nome_file=""):
    """(ente, affidabilità, fonte): chi ha emesso il documento."""
    p1 = _ca_norm(" " + (testo_p1 or (testo or "")[:3500]) + " ")
    tutto = _ca_norm(" " + (testo or "") + " ")
    migliore, punti_m = "", 0
    for nome, pezzi in _CA_ENTI:
        punti = 0
        for z in pezzi:
            zn = _ca_norm(z)
            punti += 3 * p1.count(zn) + tutto.count(zn)
            if zn.strip() and p1[:500].find(zn) >= 0:
                punti += 8                                                  # in cima alla prima pagina: è quasi sempre l'intestazione
        if punti > punti_m:
            migliore, punti_m = nome, punti
    if migliore and punti_m >= 3:
        return migliore, ("alta" if punti_m >= 8 else "media"), "testo"
    prime = [r.strip() for r in (testo_p1 or testo or "").splitlines()[:45] if r.strip()]
    for riga in prime:                                                      # ragione sociale: «A2A Energia S.p.A.», «Rossi Impianti S.r.l.»…
        m = re.search(r"([A-Z][\w&.'’\-]*(?:\s+[A-Za-zÀ-ÿ&.'’\-]+){0,5}?)\s*,?\s+(" + _CA_FORMA_LEGALE + r")(?![\w])", riga)
        if m and len(m.group(1)) >= 3:
            return re.sub(r"\s+", " ", m.group(1) + " " + m.group(2)).strip(" -–,"), "media", "testo"
    for riga in prime:
        m = re.search(r"\bComune\s+di\s+([A-ZÀ-Ý][\wà-ÿ'’\-]+(?:\s+[A-ZÀ-Ý][\wà-ÿ'’\-]+){0,2})", riga)
        if m:
            return "Comune di " + m.group(1), "media", "testo"
    stem = re.sub(r"[\d_\-\.]+", " ", nome_file or "").strip()
    stem = re.sub(r"\b(fattura|bolletta|scansione|documento|allegato|copia|pdf|img|scan|ricevuta|pagamento|quietanza|bonifico|contabile|esito|senza|riferimenti|foto|immagine|whatsapp|image|screenshot|download|manuale|scontrino)\b", "", stem, flags=re.I).strip()
    if len(stem) >= 3:
        return stem[:40].title(), "bassa", "nome del file"
    return "", "bassa", ""


def ca_leggi_argomento(testo, nome_file=""):
    """(argomento, punti, punti_luce, punti_gas): di che cosa parla la bolletta o il documento."""
    t = " " + _ca_norm((nome_file or "") + " " + (testo or "")) + " "
    punti = {}
    for arg, parole in _CA_PAROLE_ARG.items():
        p = 0
        for parola, peso in parole:
            p += peso * min(t.count(_ca_norm(parola)), 6)
        punti[arg] = p
    if punti["Luce"] >= 6 and punti["Gas"] >= 6 and min(punti["Luce"], punti["Gas"]) * 2 >= max(punti["Luce"], punti["Gas"]):
        return "Luce e Gas", punti["Luce"] + punti["Gas"], punti["Luce"], punti["Gas"]
    arg = max(punti, key=lambda k: punti[k])
    if punti[arg] < 4:
        return "", 0, punti["Luce"], punti["Gas"]
    return arg, punti[arg], punti["Luce"], punti["Gas"]


def ca_leggi_utenza(testo, testo_p1="", nome_file=""):
    """Legge una bolletta, una fattura, un avviso di pagamento, una polizza…
    Ritorna {'e_utenza': bool, 'campi': {nome: {'valore', 'affidabilita', 'fonte'}}}. NON salva niente."""
    t = testo or ""
    tn = " " + _ca_norm(t) + " "
    punti_f = sum(peso * min(tn.count(_ca_norm(p)), 4) for p, peso in _CA_PAROLE_FATTURA)
    forti = sum(1 for p in _CA_FATTURA_FORTI if _ca_norm(p) in tn)
    arg, punti_a, p_luce, p_gas = ca_leggi_argomento(t, nome_file)
    ha_importo = bool(re.search(_CA_RE_IMPORTO, t))                           # (il simbolo € non si pretende: la lettura ottica lo sbaglia spesso)
    ha_scadenza = bool(re.search(r"scadenza|scade|entro il|da pagare", tn))
    e_ricevuta = ha_importo and ((bool(re.search(_CA_RE_RICEVUTA_FORTE, tn)) and not re.search(r"totale da pagare|importo da pagare|periodo di fatturazione|importo dovuto|dovrai pagare|imponibile", tn))
                                 or (bool(re.search(_CA_RE_RICEVUTA_DEBOLE, tn)) and len(t) < 700 and not re.search(_CA_RE_SEGNI_BOLLETTA, tn)))
    e_utenza = bool(t) and (arg not in _CA_ARG_APPARECCHIO) and ((punti_f >= 7 and forti >= 1) or (arg and punti_a >= 8 and ha_importo and ha_scadenza) or e_ricevuta)
    if not e_utenza:
        return {"e_utenza": False, "campi": {}}
    campi = {}

    def metti(k, valore, aff, fonte="testo"):
        if valore:
            campi[k] = {"valore": valore, "affidabilita": aff, "fonte": fonte}
    p1 = testo_p1 or t[:5000]
    # --- tipo di documento
    if "polizza" in tn and arg == "Assicurazioni":
        tipo = "Polizza assicurativa"
    elif e_ricevuta:
        tipo = "Ricevuta di pagamento"
    elif re.search(r"contratto di (?:fornitura|locazione|somministrazione)|condizioni generali di contratto", tn) and "fattura" not in tn and "bolletta" not in tn:
        tipo = "Contratto"
    else:
        tipo = "Bolletta o fattura"
    metti("tipo", tipo, "alta" if forti >= 2 else "media")
    metti("argomento", arg or "Altro", ("alta" if punti_a >= 12 else "media") if arg else "bassa")
    ente, aff_e, fonte_e = ca_leggi_ente(t, p1, nome_file)
    if arg == "Condominio":
        mc = re.search(r"\b(Condominio\s+[A-Za-zÀ-ÿ0-9][^\n]{3,50})", p1 + "\n" + t)
        if mc:
            ente, aff_e, fonte_e = re.sub(r"\s+", " ", mc.group(1)).strip(" -–,."), "media", "testo"
    metti("ente", ente, aff_e, fonte_e)
    # --- importo (dal più sicuro al più generico)
    et_imp = ["totale da pagare", "importo da pagare", "questo mese dovrai pagare", "dovrai pagare", "importo da versare", "saldo da pagare", "totale dovuto", "importo dovuto", "totale bolletta", "totale fattura", "totale documento", "totale importo", "importo totale",
              "totale complessivo", "totale del documento", "da pagare", "premio totale", "premio da pagare", "importo rata", "totale"]
    if tipo == "Ricevuta di pagamento":
        et_imp = ["importo pagato", "importo versato", "totale pagato", "importo del pagamento", "importo addebitato", "importo bonifico", "importo", "totale"]
    v, et = _ca_dopo(t, et_imp, _CA_RE_IMPORTO, 110)
    if not v:                                                               # alcuni documenti mettono l'importo PRIMA dell'etichetta
        for et in ("totale da pagare", "importo da pagare", "importo dovuto", "totale bolletta", "totale fattura", "totale documento", "importo pagato", "importo versato"):
            m = re.search(_CA_RE_IMPORTO + r"\s*(?:€|eur(?:o)?)?\s*\n?\s*" + _ca_etichetta(et), t, re.I)
            if m:
                v = m
                break
    if v:
        metti("importo", _ca_importo_str(v.group(1)), "alta" if et != "totale" else "media")
    elif tipo == "Ricevuta di pagamento":                                       # screenshot senza etichette: se nel testo c'è UN solo importo, è quello
        importi = sorted({_ca_importo_str(x) for x in re.findall(_CA_RE_IMPORTO, t)})
        if len(importi) == 1:
            metti("importo", importi[0], "media")
    # --- numero del documento: dopo l'etichetta, il primo «pezzo» con cifre che non sia una data («Numero fattura elettronica valida ai fini fiscali: KE-26-D92452D9-006»)
    def _numero_dopo(rx, finestra, min_cifre):
        for m in re.finditer(rx, t, re.I):
            for tok in re.findall(r"[A-Z0-9][A-Z0-9/\-\.]{1,24}", t[m.end(): m.end() + finestra], re.I):
                tok = tok.rstrip(".-/")
                if len(re.findall(r"\d", tok)) >= min_cifre and not re.fullmatch(r"\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}", tok) and not re.fullmatch(r"(?:19|20)\d{2}", tok):
                    return tok
        return ""
    numero = (_numero_dopo(r"(?:numero|n\s*[.°º]|nr\.?)\s*(?:della\s*)?(?:fattura|bolletta|documento|avviso)", 95, 2)
              or _numero_dopo(r"(?:fattura|bolletta|documento|avviso)\s*(?:elettronica\s*)?(?:n\s*[.°º]?|nr\.?|numero)", 70, 1)
              or _numero_dopo(r"(?:fattura|bolletta)\s*[:\-]?\s*(?=[A-Z0-9/\-]*\d)", 30, 4))
    if numero:
        metti("numero_doc", numero, "alta")
    # --- data di emissione (per una ricevuta: la data del PAGAMENTO)
    emessa = None
    if tipo == "Ricevuta di pagamento":
        v, _ = _ca_dopo(t, ["pagato in data", "pagata in data", "data pagamento", "data del pagamento", "data operazione", "data esecuzione", "data di esecuzione", "data valuta", "eseguito il", "pagato il", "pagata il", "addebitato il", "data addebito", "ricevuto il", "effettuato il", "data"], _CA_RE_DATA, 50)
        emessa = _ca_data_da_match(v) if v else None
        if emessa:
            metti("data_doc", emessa.isoformat(), "alta")
    m = re.search(r"(?:fattura|bolletta|documento)[^\n]{0,70}?\bdel\s+(" + _CA_RE_DATA + ")", t, re.I) if tipo != "Ricevuta di pagamento" else None
    if m:
        mm = re.search(_CA_RE_DATA, m.group(1))
        emessa = _ca_data_da_match(mm) if mm else None
    if not emessa and tipo != "Ricevuta di pagamento":
        v, _ = _ca_dopo(t, ["data emissione", "data di emissione", "emessa il", "emesso il", "data fattura", "data bolletta", "data documento", "emissione", "data"], _CA_RE_DATA, 40)
        emessa = _ca_data_da_match(v) if v else None
    if emessa and tipo != "Ricevuta di pagamento":
        metti("data_doc", emessa.isoformat(), "alta")
    # --- scadenza di pagamento
    v, _ = _ca_dopo(t, ["data scadenza", "scadenza pagamento", "scade il", "da pagare entro il", "da pagare entro", "pagare entro il", "pagabile entro il", "scadenza", "entro il"], _CA_RE_DATA, 50)
    sc = _ca_data_da_match(v) if (v and tipo != "Ricevuta di pagamento") else None
    if sc and (not emessa or sc >= emessa):
        metti("scadenza_doc", sc.isoformat(), "alta")
    # --- periodo
    m = re.search(r"(?:periodo(?:\s+di)?\s*(?:fatturazione|consumo|competenza|riferimento)?|competenza|relativ[ao]\s+al\s+periodo)[^\d]{0,45}(?P<d1>" + _CA_RE_DATA + r")\s*(?:-|–|a|al|fino\s+al)\s*(?P<d2>" + _CA_RE_DATA + ")", p1 + "\n" + t, re.I)
    if not m:
        m = re.search(r"\bdal\s+(?P<d1>" + _CA_RE_DATA + r")\s+al\s+(?P<d2>" + _CA_RE_DATA + ")", p1 + "\n" + t, re.I)
    if m:
        a1, a2 = re.search(_CA_RE_DATA, m.group("d1")), re.search(_CA_RE_DATA, m.group("d2"))
        d1 = _ca_data_da_match(a1) if a1 else None
        d2 = _ca_data_da_match(a2) if a2 else None
        if d1 and d2 and d1 <= d2:
            metti("periodo_da", d1.isoformat(), "alta")
            metti("periodo_a", d2.isoformat(), "alta")
    # --- codici
    m = re.search(r"\bIT\s?\d{3}\s?E\s?\d{8}\b", t)
    if m:
        pdr, _ = _ca_dopo(t, ["pdr", "punto di riconsegna"], r"\b(\d{14})\b", 40)
        metti("codice_fornitura", re.sub(r"\s", "", m.group(0)) + (" · PDR " + pdr.group(1) if pdr else ""), "alta")
    else:
        v, _ = _ca_dopo(t, ["pdr", "punto di riconsegna"], r"\b(\d{14})\b", 40)
        if v:
            metti("codice_fornitura", v.group(1), "alta")
        else:
            v, _ = _ca_dopo(t, ["numero di telefono", "numero linea", "linea fissa", "numero telefonico"], r"(\+?\d[\d\s/]{7,14}\d)", 40)
            if v:
                metti("codice_fornitura", re.sub(r"\s+", " ", v.group(1)).strip(), "media")
            else:
                v, _ = _ca_dopo(t, ["codice utenza", "id fornitura", "codice fornitura", "matricola contatore", "numero polizza", "n. polizza", "polizza n"], r"([A-Z0-9][A-Z0-9\-/\.]{4,20})", 40)
                if v and re.search(r"\d", v.group(1)):
                    metti("codice_fornitura", v.group(1).rstrip(".-/"), "media")
    v, _ = _ca_dopo(t, ["codice cliente", "numero cliente", "cod. cliente", "codice contratto", "numero contratto", "contratto n", "codice anagrafica", "n. cliente"], r"([A-Z0-9][A-Z0-9\-/]{4,19})", 45)
    if v and re.search(r"\d", v.group(1)):
        metti("codice_cliente", v.group(1).rstrip("-/"), "alta")
    lingua, aff = ca_lingua(t)
    metti("lingua", lingua, aff)
    return {"e_utenza": True, "campi": campi}


_CA_NEGOZI = ["MediaWorld", "Unieuro", "Euronics", "Expert", "Trony", "Leroy Merlin", "Brico", "Bricocenter", "Ikea", "Amazon", "ePRICE", "Conforama", "Mondo Convenienza",
              "Esselunga", "Coop", "Conad", "Carrefour", "Lidl", "Decathlon", "Castorama", "OBI", "Brico io", "Auchan"]


def ca_leggi_negozio(testo, testo_p1=""):
    """Il negozio che ha emesso uno scontrino o una fattura di acquisto."""
    p1 = _ca_norm(" " + (testo_p1 or testo or "")[:1500] + " ")
    for n in _CA_NEGOZI:
        if " " + _ca_norm(n) in p1 or _ca_norm(n) + " " in p1:
            return n
    for riga in [r.strip() for r in (testo_p1 or testo or "").splitlines()[:6] if r.strip()]:
        if 3 <= len(riga) <= 40 and not re.search(r"\d{3,}|totale|scontrino|fattura|ricevuta|documento", riga, re.I) and re.search(r"[A-Za-zÀ-ÿ]{3}", riga):
            return riga.title() if riga.isupper() else riga
    return ""


def ca_titolo_auto(d):
    """Il titolo che si scrive da solo, se non ne viene dato uno: «Luce · Enel Energia · Fattura n. 123 del 12/03/2026 · € 87,35»."""
    arg, ente = d.get("argomento") or "", d.get("ente") or ""
    if arg and arg not in _CA_ARG_APPARECCHIO and (ente or d.get("importo") or d.get("numero_doc")):
        parti = [arg, ente]
        tipo = {"Rifiuti (TARI)": "Avviso di pagamento", "Tasse e imposte": "Avviso di pagamento", "Condominio": "Rata condominiale"}.get(arg) or \
               {"Bolletta o fattura": "Fattura", "Polizza assicurativa": "Polizza", "Ricevuta di pagamento": "Ricevuta"}.get(d.get("tipo"), d.get("tipo") or "Documento")
        corpo = tipo + (f" n. {d['numero_doc']}" if d.get("numero_doc") else "") + (f" del {_ca_data_it(d['data_doc'])}" if d.get("data_doc") else "")
        parti.append(corpo)
        if d.get("importo"):
            parti.append("€ " + ca_importo_fmt(d["importo"]))
        return " · ".join(p for p in parti if p)[:140]
    return " ".join(x for x in (d.get("tipo"), d.get("marca"), d.get("modello")) if x)


_CA_TIPI_PAGABILI = {"Bolletta o fattura", "Polizza assicurativa"}


def ca_ricevute_di(docs, bid):
    """Le ricevute di pagamento collegate a una bolletta, dalla più vecchia alla più recente."""
    return sorted([x for x in docs if x.get("collegato_a") == bid], key=lambda x: (_ca_ordine(x), x.get("creato_il", "")))


def ca_stato_pagamento(d, docs, oggi_):
    """('pagata', data) · ('da_pagare', giorni) · ('scaduta', giorni) · None (se non è una bolletta o non ha scadenza)."""
    if d.get("tipo") not in _CA_TIPI_PAGABILI:
        return None
    r = ca_ricevute_di(docs, d.get("id"))
    if r:
        return "pagata", (r[-1].get("data_doc") or d.get("pagata_il") or "")
    if d.get("pagata_il"):
        return "pagata", d["pagata_il"]
    sc = _data(d.get("scadenza_doc"))
    if not sc:
        return None
    g = (sc - oggi_).days
    return ("scaduta", -g) if g < 0 else ("da_pagare", g)


def ca_candidate_bollette(docs, campi, escludi_id=None):
    """Le bollette ancora NON pagate che potrebbero essere quelle di una ricevuta o di uno screenshot di pagamento, dalla più probabile: [{id, punti, esatto, motivi}]."""
    v = lambda k: (campi.get(k) or {}).get("valore", "") if isinstance(campi.get(k), dict) else (campi.get(k) or "")
    num, ente = _ca_norm(v("numero_doc")), _ca_norm(v("ente"))
    try:
        imp = float(v("importo")) if v("importo") else None
    except ValueError:
        imp = None
    out = []
    for b in docs:
        if b.get("tipo") not in _CA_TIPI_PAGABILI or b.get("id") == escludi_id or ca_ricevute_di(docs, b.get("id")) or b.get("pagata_il"):
            continue
        p, motivi, esatto = 0, [], False
        if num and _ca_norm(b.get("numero_doc")) == num:
            p += 6; motivi.append("stesso numero di fattura")
        try:
            if imp is not None and b.get("importo") and abs(float(b["importo"]) - imp) < 0.005:
                p += 4; esatto = True; motivi.append("stesso importo")
        except ValueError:
            pass
        eb = _ca_norm(b.get("ente"))
        if ente and eb and ente == eb:
            p += 3; motivi.append("stessa azienda")
        elif ente and eb and (ente in eb or eb in ente):
            p += 2; motivi.append("azienda simile")
        out.append({"id": b["id"], "punti": p, "esatto": esatto or bool(num and _ca_norm(b.get("numero_doc")) == num), "motivi": motivi, "ordine": _ca_ordine(b)})
    try:
        pag = date.fromisoformat(v("data_doc"))
    except (ValueError, TypeError):
        pag = None
    if pag:
        for x in out:
            b = next((y for y in docs if y.get("id") == x["id"]), {})
            rif = _data(b.get("scadenza_doc")) or _data(b.get("data_doc"))
            x["vicino"] = -abs((pag - rif).days) if rif else -9999
    out.sort(key=lambda x: (x["esatto"], x["punti"], x.get("vicino", 0), x["ordine"]), reverse=True)
    return out


def ca_proponi_bolletta(docs, campi, escludi_id=None):
    """La bolletta a cui sembra riferirsi una ricevuta: (id, motivi) oppure (None, []). Una sola bolletta con lo stesso importo basta."""
    cand = ca_candidate_bollette(docs, campi, escludi_id)
    if not cand:
        return None, []
    m = cand[0]
    esatte = [x for x in cand if x["esatto"]]
    if m["punti"] >= 6 or (m["esatto"] and len(esatte) == 1):
        return m["id"], m["motivi"]
    return None, []


def _ca_etichetta_bolletta(b):
    return " · ".join(x for x in (b.get("ente") or "Senza ente", ("n. " + b["numero_doc"]) if b.get("numero_doc") else "", ("€ " + ca_importo_fmt(b["importo"])) if b.get("importo") else "",
                                  _ca_data_it(b.get("data_doc")) if b.get("data_doc") else "") if x)


def _ca_argomento_di(d):
    """L'argomento di un documento, anche vecchio (archiviato prima che esistesse questo campo)."""
    a = d.get("argomento")
    if a in CA_ARGOMENTI:
        return a
    return "Acquisti e garanzie" if d.get("tipo") == "Fattura o scontrino" else ("Manuali e istruzioni" if d.get("tipo") in _CA_TIPI_MANUALI else "Altro")


def _ca_ente_di(d):
    return (d.get("ente") or d.get("marca") or "").strip() or "Senza indicazione"


def _ca_ordine(d):
    """Per ordinare: la data del documento (o, se manca, quella di archiviazione)."""
    return (d.get("data_doc") or str(d.get("creato_il") or "")[:10] or "0000-00-00")


def ca_riconosci(nome, mime, dati, testo=None, info=None):
    """Legge un documento e propone i dati. Ritorna {'testo_ok', 'info', 'campi': {nome: {'valore', 'affidabilita', 'fonte'}}, 'testo_inizio'}. NON salva niente."""
    if testo is None:
        testo, info = ca_estrai_testo(nome, mime, dati)
    info = info or {}
    stem = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", nome or "").replace("_", " ").replace("-", " ")
    campi = {}

    ocr = "OCR" in str(info.get("metodo") or "")

    def metti(k, valore, aff, fonte):
        if valore:
            if ocr and fonte != "nome del file":                             # la lettura ottica sbaglia più facilmente (lettere e numeri scambiati): un gradino di sicurezza in meno
                aff = {"alta": "media", "media": "bassa"}.get(aff, aff)
            campi[k] = {"valore": valore, "affidabilita": aff, "fonte": fonte}
    tipo, aff = ca_tipo(testo, stem)
    metti("tipo", tipo, aff, "testo" if testo else "nome del file")
    cat, sotto, aff = ca_categoria(testo, stem)
    metti("categoria", cat, aff, "testo" if testo else "nome del file")
    metti("sottocategoria", sotto, aff, "testo" if testo else "nome del file")
    marca, aff = ca_marca(testo, stem)
    metti("marca", marca, aff, "testo" if marca and marca.lower() in (testo or "").lower() else "nome del file")
    modello, aff = ca_modello(testo, marca)
    metti("modello", modello, aff, "testo")
    seriale, aff = ca_seriale(testo)
    metti("seriale", seriale, aff, "testo")
    d, fonte, aff = ca_data(testo, info.get("data_meta"))
    metti("data_doc", d.isoformat() if d else "", aff, fonte)
    lingua, aff = ca_lingua(testo)
    metti("lingua", lingua, aff, "testo")
    sotto_v = campi.get("sottocategoria", {}).get("valore", "")
    nome_prop = " ".join(x for x in (sotto_v if sotto_v and sotto_v != "Altro" else "", marca, modello) if x).strip()
    metti("nome_apparecchio", nome_prop or stem[:60], "media" if nome_prop else "bassa", "testo" if nome_prop else "nome del file")
    # --- è una bolletta, una fattura, un avviso di pagamento, una polizza? Allora NON è un apparecchio: si leggono ente, importo, numero, date, periodo e codici
    ut = ca_leggi_utenza(testo, info.get("testo_p1") or "", stem) if testo else {"e_utenza": False, "campi": {}}
    if ut["e_utenza"]:
        campi = {}
        for k, v in ut["campi"].items():
            metti(k, v["valore"], v["affidabilita"], v["fonte"])
        if "data_doc" not in campi:
            dd, fonte_d, aff_d = ca_data(testo, info.get("data_meta"))
            metti("data_doc", dd.isoformat() if dd else "", aff_d, fonte_d)
    else:
        tipo_v = (campi.get("tipo") or {}).get("valore", "")
        metti("argomento", "Acquisti e garanzie" if tipo_v == "Fattura o scontrino" else "Manuali e istruzioni", "media" if tipo_v else "bassa", "testo")
        if tipo_v == "Fattura o scontrino":
            negozio = ca_leggi_negozio(testo, info.get("testo_p1") or "")
            if negozio:
                metti("ente", negozio, "media", "testo")
            else:
                metti("ente", marca, "bassa", "nome del file")
            imp, _ = _ca_dopo(testo, ["totale complessivo", "totale da pagare", "importo pagato", "totale euro", "totale"], _CA_RE_IMPORTO, 60)
            if imp:
                metti("importo", _ca_importo_str(imp.group(1)), "media", "testo")
        else:
            metti("ente", marca, "media" if marca else "bassa", "testo" if marca and marca.lower() in (testo or "").lower() else "nome del file")
            if testo and len(testo) < 700 and not tipo_v:
                importi = sorted({_ca_importo_str(x) for x in re.findall(_CA_RE_IMPORTO, testo)})
                if len(importi) == 1:
                    metti("importo", importi[0], "bassa", "testo")
    return {"testo_ok": bool(testo), "info": {k: (v.isoformat() if isinstance(v, date) else v) for k, v in info.items()}, "campi": campi, "testo_inizio": (testo or "")[:400]}


def ca_proponi_bene(beni, campi):
    """Il bene dell'inventario che sembra quello del documento: (bene_id, punteggio, motivi) oppure (None, 0, [])."""
    v = lambda k: (campi.get(k) or {}).get("valore", "") if isinstance(campi.get(k), dict) else (campi.get(k) or "")
    modello, seriale, marca, sotto, cat = _ca_norm(v("modello")), _ca_norm(v("seriale")), _ca_norm(v("marca")), _ca_norm(v("sottocategoria")), _ca_norm(v("categoria"))
    migliore, punti_m, motivi_m = None, 0, []
    for b in beni:
        p, motivi = 0, []
        if seriale and _ca_norm(b.get("seriale")) == seriale:
            p += 6; motivi.append("stesso numero di serie")
        if modello and _ca_norm(b.get("modello")) == modello:
            p += 5; motivi.append("stesso modello")
        if marca and _ca_norm(b.get("marca")) == marca:
            p += 2; motivi.append("stessa marca")
            if sotto and _ca_norm(b.get("sottocategoria")) == sotto:
                p += 2; motivi.append("stesso tipo di apparecchio")
        elif sotto and _ca_norm(b.get("sottocategoria")) == sotto and cat and _ca_norm(b.get("categoria")) == cat:
            p += 1
        if p > punti_m:
            migliore, punti_m, motivi_m = b.get("id"), p, motivi
    return (migliore, punti_m, motivi_m) if punti_m >= 4 else (None, 0, [])


def ca_ai_classifica(testo, base=None):
    """Facoltativo: se nei Secrets c'è la chiave dell'assistente intelligente, chiede al modello di migliorare la lettura. Ritorna un dizionario o None."""
    if not (testo or "").strip() or "ai_attivo" not in globals() or not ai_attivo():
        return None
    import json
    import requests
    try:
        r = requests.post(AI_URL, timeout=(5, 40), headers={"x-api-key": _ai_chiave(), "anthropic-version": "2023-06-01", "content-type": "application/json"},
                          json={"model": AI_MODELLO, "max_tokens": 500,
                                "system": "Leggi l'inizio di un manuale o documento tecnico di una casa e rispondi SOLO con un oggetto JSON con le chiavi: tipo, categoria, sottocategoria, "
                                          "marca, modello, seriale, lingua (it/en/de/fr/es), data_doc (AAAA-MM-GG o vuoto). Se non sei sicuro di un dato lascialo vuoto: non inventare.",
                                "messages": [{"role": "user", "content": (testo or "")[:3500]}]})
        if r.status_code != 200:
            return None
        t = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
        m = re.search(r"\{.*\}", t, re.S)
        j = json.loads(m.group(0)) if m else None
        return {k: str(v).strip() for k, v in j.items() if isinstance(v, (str, int)) and str(v).strip()} if isinstance(j, dict) else None
    except Exception:
        return None


# ---------------------------------------------------------------------------------------------------------------------
# Dati (funzioni pure: lavorano su un dizionario «casa»)
# ---------------------------------------------------------------------------------------------------------------------
_CAMPI_BENE = ("nome", "categoria", "sottocategoria", "marca", "modello", "seriale", "stanza", "acquisto", "garanzia_fino", "note")
_CAMPI_DOC = ("tipo", "titolo", "argomento", "ente", "importo", "numero_doc", "scadenza_doc", "periodo_da", "periodo_a", "codice_cliente", "codice_fornitura",
              "categoria", "sottocategoria", "marca", "modello", "seriale", "data_doc", "lingua", "bene_id", "collegato_a", "pagata_il", "link", "note")
_CAMPI_CONTROLLATI = ("tipo", "argomento", "ente", "importo", "numero_doc", "scadenza_doc", "periodo_da", "periodo_a", "codice_cliente", "codice_fornitura",
                      "categoria", "sottocategoria", "marca", "modello", "seriale", "data_doc", "lingua")


def ca_vuoto():
    return {"beni": [], "documenti": [], "manutenzioni": []}


def _ca_pulisci(valori, campi):
    return {k: (str(valori.get(k) or "").strip() if not isinstance(valori.get(k), date) else valori[k].isoformat()) for k in campi}


def ca_nuovo_bene(c, valori, ora):
    b = _ca_pulisci(valori, _CAMPI_BENE)
    b["nome"] = b["nome"] or "Bene senza nome"
    b.update({"id": uuid.uuid4().hex[:10], "creato_il": ora})
    c.setdefault("beni", []).append(b)
    return b


def ca_aggiorna_bene(c, bid, valori):
    b = next((x for x in c.get("beni", []) if x.get("id") == bid), None)
    if b is None:
        return None
    b.update({k: v for k, v in _ca_pulisci(valori, _CAMPI_BENE).items() if k != "nome" or v})
    return b


def ca_elimina_bene(c, bid, con_documenti=False):
    """Toglie un bene. I suoi documenti restano (non collegati) oppure vanno via con lui. Ritorna gli id dei file da cancellare dall'archivio."""
    file_da_togliere = []
    docs = c.get("documenti", [])
    if con_documenti:
        file_da_togliere = [x["file"]["id"] for x in docs if x.get("bene_id") == bid and x.get("file")]
        c["documenti"] = [x for x in docs if x.get("bene_id") != bid]
    else:
        for x in docs:
            if x.get("bene_id") == bid:
                x["bene_id"] = ""
    c["beni"] = [x for x in c.get("beni", []) if x.get("id") != bid]
    c["manutenzioni"] = [m for m in c.get("manutenzioni", []) if m.get("bene_id") != bid]
    return file_da_togliere


def _ca_eredita_dalla_bolletta(c, fin):
    """Una ricevuta collegata a una bolletta prende da lei argomento ed ente (se non li ha), così sta nello stesso posto."""
    b = next((x for x in c.get("documenti", []) if x.get("id") == fin.get("collegato_a")), None) if fin.get("collegato_a") else None
    if b:
        if fin.get("argomento") in ("", "Altro", None):
            fin["argomento"] = b.get("argomento") or fin.get("argomento", "")
        if not fin.get("ente"):
            fin["ente"] = b.get("ente") or ""
        if not fin.get("importo") and b.get("importo"):
            fin["importo"] = b["importo"]


def _ca_modificati(campi_prop, fin, presenti=None):
    """I campi che chi usa l'app ha cambiato rispetto a ciò che aveva letto il programma (un campo lasciato vuoto o «Altro» non conta come correzione; un campo non indicato non conta)."""
    def uguale(k):
        a, b = str(campi_prop.get(k) or ""), str(fin.get(k) or "")
        return a == b or (not a and b in ("", "Altro"))
    return [k for k in _CAMPI_CONTROLLATI if (presenti is None or k in presenti) and not uguale(k)]


def ca_aggiungi_documento(c, file_ref, riconosciuto, proposta, finale, utente, ora):
    """Archivia un documento con i QUATTRO livelli separati: file originale · dati riconosciuti · classificazione proposta · conferma di chi usa l'app."""
    campi_prop = {k: (v.get("valore") if isinstance(v, dict) else v) for k, v in ((riconosciuto or {}).get("campi") or {}).items()}
    fin = _ca_pulisci(finale, _CAMPI_DOC)
    _ca_eredita_dalla_bolletta(c, fin)
    modificati = _ca_modificati(campi_prop, fin, set(finale))
    doc = dict(fin)
    doc.update({
        "id": uuid.uuid4().hex[:10], "creato_il": ora,
        "file": dict(file_ref, originale=not file_ref.get("ridotta")),
        "riconosciuto": riconosciuto or {},
        "classificazione": dict(proposta or {}),
        "conferma": {"stato": "confermato", "da": utente, "il": ora, "modificati": modificati, "bene_proposto": (proposta or {}).get("bene_id") or ""},
    })
    doc["titolo"] = doc["titolo"] or ca_titolo_auto(doc) or (file_ref.get("nome") or "Documento")
    c.setdefault("documenti", []).append(doc)
    return doc


def ca_correggi_documento(c, did, finale, utente, ora):
    """Corregge i dati di un documento già archiviato: l'originale, i dati riconosciuti e la proposta automatica restano com'erano; si aggiorna solo la conferma."""
    d = next((x for x in c.get("documenti", []) if x.get("id") == did), None)
    if d is None:
        return None
    fin = _ca_pulisci(finale, _CAMPI_DOC)
    campi_prop = {k: (v.get("valore") if isinstance(v, dict) else v) for k, v in ((d.get("riconosciuto") or {}).get("campi") or {}).items()}
    _ca_eredita_dalla_bolletta(c, fin)
    if fin.get("titolo") in ("", ca_titolo_auto(d), d.get("file", {}).get("nome", "")):          # il titolo era quello automatico: si riscrive con i dati corretti
        fin["titolo"] = ""
    d.update({k: fin[k] for k in _CAMPI_DOC if k in fin})
    d["titolo"] = d["titolo"] or ca_titolo_auto(d) or (d.get("file") or {}).get("nome", "Documento")
    conf = d.setdefault("conferma", {})
    conf.update({"stato": "confermato", "da": utente, "il": ora, "modificati": _ca_modificati(campi_prop, d, set(finale))})
    conf["correzioni"] = int(conf.get("correzioni", 0) or 0) + 1
    return d


def ca_elimina_documento(c, did):
    d = next((x for x in c.get("documenti", []) if x.get("id") == did), None)
    if d is None:
        return None
    c["documenti"] = [x for x in c["documenti"] if x.get("id") != did]
    for m in c.get("manutenzioni", []):
        if m.get("documento_id") == did:
            m["documento_id"] = ""
    return (d.get("file") or {}).get("id")


def ca_aggiungi_manutenzione(c, valori):
    campi = ("bene_id", "data", "tipo", "descrizione", "ditta", "costo", "prossima", "documento_id", "note")
    m = _ca_pulisci(valori, campi)
    m["id"] = uuid.uuid4().hex[:10]
    c.setdefault("manutenzioni", []).append(m)
    return m


def _data(v):
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def ca_stato_garanzia(bene, oggi_):
    """('nessuna' | 'ok' | 'presto' entro 60 giorni | 'scaduta', giorni)."""
    d = _data(bene.get("garanzia_fino"))
    if not d:
        return "nessuna", None
    g = (d - oggi_).days
    return ("scaduta" if g < 0 else "presto" if g <= 60 else "ok"), g


def ca_scadenze(c, oggi_, giorni=60):
    """Garanzie e manutenzioni in arrivo o scadute: {'garanzie': [(bene, giorni)], 'manutenzioni': [(bene_nome, voce, giorni)]}."""
    nomi = {b["id"]: b.get("nome", "") for b in c.get("beni", [])}
    garanzie, manut = [], []
    for b in c.get("beni", []):
        stato, g = ca_stato_garanzia(b, oggi_)
        if stato == "presto":
            garanzie.append((b.get("nome", ""), g))
    ultime = {}
    for m in sorted(c.get("manutenzioni", []), key=lambda x: x.get("data") or ""):
        ultime[(m.get("bene_id"), m.get("tipo"))] = m
    for m in ultime.values():
        d = _data(m.get("prossima"))
        if d and (d - oggi_).days <= giorni and m.get("bene_id") in nomi:
            manut.append((nomi[m["bene_id"]], m.get("descrizione") or m.get("tipo") or "Manutenzione", (d - oggi_).days))
    docs = c.get("documenti", [])
    bollette = []                                                                    # bollette da pagare tra 10 giorni o già scadute (fino a 90 giorni fa) senza ricevuta
    for d in docs:
        sp = ca_stato_pagamento(d, docs, oggi_)
        if sp and sp[0] == "da_pagare" and sp[1] <= 10:
            bollette.append((f"{_ca_argomento_di(d)} · {_ca_ente_di(d)}", sp[1], d.get("importo")))
        elif sp and sp[0] == "scaduta" and sp[1] <= 90:
            bollette.append((f"{_ca_argomento_di(d)} · {_ca_ente_di(d)}", -sp[1], d.get("importo")))
    return {"garanzie": sorted(garanzie, key=lambda x: x[1]), "manutenzioni": sorted(manut, key=lambda x: x[2]), "bollette": sorted(bollette, key=lambda x: x[1])}


# ---------------------------------------------------------------------------------------------------------------------
# Salvataggio e lettura (sul file personale, chiave «casa»)
# ---------------------------------------------------------------------------------------------------------------------
def _ca_dati():
    try:
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
    except Exception:
        return ca_vuoto()
    c = dict(d.get("casa") or {})
    for k in ("beni", "documenti", "manutenzioni"):
        c.setdefault(k, [])
    return c


def _ca_salva(fn, messaggio):
    def _m(d):
        c = d.setdefault("casa", {})
        for k in ("beni", "documenti", "manutenzioni"):
            c.setdefault(k, [])
        fn(c)
    salva(_m, messaggio)


def _ca_scrivi_file(nid, nome, mime, dati):
    """Il file ORIGINALE, identico byte per byte, nello stesso archivio dei documenti di Salute."""
    corpo = {"nome": nome, "mime": mime, "b64": base64.b64encode(dati).decode()}
    salva_file(_fa_percorso_doc(nid), lambda d, c=corpo: d.update(c), "Casa: documento archiviato")


def _ca_leggi_file(rif):
    """[(nome, mime, byte)] del documento originale."""
    return _fa_inv_allegati([rif]) if "_fa_inv_allegati" in globals() else []


def _ca_ora():
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------------------------------------------------
# Schermate
# ---------------------------------------------------------------------------------------------------------------------
_CA_AFF = {"alta": "🟢", "media": "🟡", "bassa": "🟠"}
_CA_CSS = """<style>
.ca-hero{background:linear-gradient(135deg,#7a5c00 0%,#d4a017 45%,#4aa3df 100%);color:#fff;padding:18px 22px;border-radius:24px;margin:6px 0 12px;
box-shadow:0 10px 30px rgba(0,0,0,.15);display:flex;align-items:center;gap:14px}
.ca-hero img{width:64px;height:64px;object-fit:contain;filter:drop-shadow(0 3px 5px rgba(0,0,0,.3))}
.ca-hero h1{margin:0;font-size:1.8rem;color:#fff;padding:0}.ca-hero p{margin:4px 0 0;opacity:.95}
.ca-card{background:#ffffffcc;border:1px solid #e3d9b8;border-radius:18px;padding:12px 14px;margin:6px 0}
.ca-card b{font-size:1.02rem}.ca-chip{display:inline-block;border-radius:999px;padding:2px 10px;font-size:.78rem;font-weight:700;margin:2px 4px 2px 0}
.ca-ok{background:#e8f5e9;color:#1b5e20}.ca-presto{background:#fff3e0;color:#bf360c}.ca-scaduta{background:#eceff1;color:#263238}.ca-neutro{background:#e3f2fd;color:#0d47a1}
</style>"""


def _ca_chip(testo, classe="ca-neutro"):
    return f"<span class='ca-chip {classe}'>{testo}</span>"


def _ca_testo(v):
    import html as _h
    return _h.escape(str(v or ""))


def _ca_data_it(iso):
    d = _data(iso)
    return d.strftime("%d/%m/%Y") if d else ""


def _ca_form_bene(chiave, b=None):
    """Il modulo di un bene (nuovo o da modificare). Ritorna (inviato, valori)."""
    b = b or {}
    with st.form(chiave, border=False):
        nome = st.text_input("Nome del bene *", value=b.get("nome", ""), placeholder="es. Caldaia del bagno, Lavatrice, TV del soggiorno")
        cats = list(CA_CATEGORIE)
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Categoria", cats, index=cats.index(b["categoria"]) if b.get("categoria") in cats else 0)
        sotto_opz = CA_CATEGORIE[cat]
        sotto = c2.text_input("Che apparecchio è", value=b.get("sottocategoria", ""), placeholder="es. " + sotto_opz[0], help="Per esempio: " + ", ".join(sotto_opz[:4]))
        c3, c4 = st.columns(2)
        marca = c3.text_input("Marca", value=b.get("marca", ""))
        modello = c4.text_input("Modello", value=b.get("modello", ""))
        seriale = st.text_input("Numero di serie (se c'è)", value=b.get("seriale", ""))
        stanza = st.selectbox("Dove si trova", [""] + CA_STANZE, index=(CA_STANZE.index(b["stanza"]) + 1) if b.get("stanza") in CA_STANZE else 0, format_func=lambda x: x or "—")
        c5, c6 = st.columns(2)
        acq = c5.date_input("Data di acquisto", value=_data(b.get("acquisto")), format="DD/MM/YYYY")
        gar = c6.date_input("Garanzia fino al", value=_data(b.get("garanzia_fino")), format="DD/MM/YYYY")
        note = st.text_input("Note (facoltative)", value=b.get("note", ""))
        ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
    return ok, {"nome": nome, "categoria": cat, "sottocategoria": sotto, "marca": marca, "modello": modello, "seriale": seriale, "stanza": stanza,
                "acquisto": acq, "garanzia_fino": gar, "note": note}


def _ca_importo_da_testo(x):
    """«€ 1.234,56» o «87.35» → «1234.56» (se non è un numero, si tiene com'è scritto)."""
    x = str(x or "").replace("€", "").replace("EUR", "").replace("eur", "").strip().replace(" ", "")
    if not x:
        return ""
    if "," in x:
        x = x.replace(".", "").replace(",", ".")
    try:
        return f"{float(x):.2f}"
    except ValueError:
        return x


def _ca_anteprima(nome, mime, dati):
    """Fa vedere il documento nella pagina: la foto intera, oppure le prime pagine del PDF."""
    if (mime or "").startswith("image/"):
        st.image(dati, width="stretch")
        return
    if mime == "text/plain":
        st.text((dati or b"").decode("utf-8", "replace")[:5000])
        return
    try:
        try:
            import pymupdf as _mu
        except Exception:
            import fitz as _mu
        doc = _mu.open(stream=dati, filetype="pdf")
        n = doc.page_count
        for i in range(min(3, n)):
            st.image(doc[i].get_pixmap(dpi=100, alpha=False).tobytes("png"), caption=f"Pagina {i + 1} di {n}", width="stretch")
        if n > 3:
            st.caption(f"Ti mostro le prime 3 pagine su {n}: per il resto usa «Apri / scarica».")
        doc.close()
    except Exception:
        st.info("Qui l'anteprima non è disponibile: usa «⬇ Apri / scarica» per vedere il documento.")


def _ca_riga_documento(d, beni_nomi, pre="", docs=None):
    """Un documento in elenco: dati, apri/scarica, anteprima, invia, correggi, elimina. Se è una bolletta, ci sono dentro anche le sue ricevute di pagamento."""
    f = d.get("file") or {}
    k = f"{pre}{d['id']}"
    stato_p = ca_stato_pagamento(d, docs, oggi()) if docs is not None else None
    chip_p = ""
    if stato_p:
        quando = {"pagata": lambda v: "✅ Pagata" + (f" il {_ca_data_it(v)}" if v else ""),
                  "da_pagare": lambda g: "⏳ Da pagare " + ("oggi" if g == 0 else f"entro {g} giorni"),
                  "scaduta": lambda g: f"⚠️ Scaduta da {g} giorni: non risulta pagata"}[stato_p[0]](stato_p[1])
        chip_p = _ca_chip(quando, {"pagata": "ca-ok", "da_pagare": "ca-presto", "scaduta": "ca-scaduta"}[stato_p[0]])
    righe = []
    if d.get("importo"):
        righe.append("💶 <b>€ " + ca_importo_fmt(d["importo"]) + "</b>")
    if d.get("numero_doc"):
        righe.append("n. " + _ca_testo(d["numero_doc"]))
    if d.get("data_doc"):
        righe.append("del " + _ca_data_it(d["data_doc"]))
    if d.get("periodo_da") and d.get("periodo_a"):
        righe.append("periodo " + _ca_data_it(d["periodo_da"]) + " → " + _ca_data_it(d["periodo_a"]))
    if d.get("scadenza_doc"):
        righe.append("scadenza " + _ca_data_it(d["scadenza_doc"]))
    app = " · ".join(x for x in (_ca_testo(d.get("marca")), _ca_testo(d.get("modello")), ("S/N " + _ca_testo(d.get("seriale"))) if d.get("seriale") else "") if x)
    cod = " · ".join(x for x in (("cliente " + _ca_testo(d.get("codice_cliente"))) if d.get("codice_cliente") else "", ("fornitura " + _ca_testo(d.get("codice_fornitura"))) if d.get("codice_fornitura") else "") if x)
    st.markdown(f"<div class='ca-card'><b>📄 {_ca_testo(d.get('titolo'))}</b><br>"
                + _ca_chip(_ca_testo(d.get("tipo") or "Documento")) + chip_p
                + (_ca_chip("🏠 " + _ca_testo(beni_nomi.get(d.get("bene_id"), "")), "ca-ok") if beni_nomi.get(d.get("bene_id")) else "")
                + ("<br><span style='font-size:.9rem'>" + " · ".join(righe) + "</span>" if righe else "")
                + ("<br><span style='font-size:.85rem'>" + app + "</span>" if app else "")
                + ("<br><span style='font-size:.8rem;opacity:.85'>" + cod + "</span>" if cod else "")
                + (("<br><span style='font-size:.8rem;opacity:.85'>" + CA_LINGUE.get(d.get("lingua"), "") + "</span>") if d.get("lingua") and CA_LINGUE.get(d.get("lingua")) else "")
                + "</div>", unsafe_allow_html=True)
    caricato = _ca_leggi_file(f) if f.get("id") else []
    vedi = st.session_state.setdefault("ca_vedi", [])
    aperto = d["id"] in vedi
    b1, b2 = st.columns(2, gap="small")
    if caricato:
        nome, mime, dati = caricato[0]
        b1.download_button("⬇ Apri / scarica", dati, file_name=nome, mime=mime, key=f"ca_dl_{k}", width="stretch")
        if b2.button("🙈 Chiudi l'anteprima" if aperto else "👁️ Vedi qui", key=f"ca_pv_{k}", width="stretch"):
            if aperto:
                vedi.remove(d["id"])
            else:
                vedi.append(d["id"])
            st.rerun()
    elif d.get("link"):
        b1.link_button("🔗 Apri il link", d["link"], width="stretch")
    else:
        b1.caption("⚠️ Il file non è più disponibile.")
    b3, b4 = st.columns(2, gap="small")
    if b3.button("✏️ Correggi", key=f"ca_cor_{k}", width="stretch"):
        st.session_state["ca_correggi"] = d["id"]
        st.rerun()
    if b4.button("🗑️ Elimina", key=f"ca_del_{k}", width="stretch"):
        st.session_state["ca_elimina_doc"] = d["id"]
        st.rerun()
    if caricato and aperto:
        _ca_anteprima(*caricato[0])
    if stato_p and stato_p[0] != "pagata" and not d.get("pagata_il"):                           # bolletta pagata senza file di ricevuta
        if st.button("✅ Segna come pagata (oggi)", key=f"ca_pag_{k}", width="stretch"):
            _ca_salva(lambda cc: next((x.update({"pagata_il": date.today().isoformat()}) for x in cc.get("documenti", []) if x.get("id") == d["id"]), None), "Casa: bolletta segnata come pagata")
            st.rerun()
    elif d.get("pagata_il") and not ca_ricevute_di(docs or [], d["id"]):
        if st.button("↩️ Togli «pagata»", key=f"ca_npag_{k}", width="stretch"):
            _ca_salva(lambda cc: next((x.pop("pagata_il", None) for x in cc.get("documenti", []) if x.get("id") == d["id"]), None), "Casa: tolto «pagata»")
            st.rerun()
    if docs is not None:
        for r in ca_ricevute_di(docs, d["id"]):
            with st.container(border=True):
                st.markdown("🧾 **Ricevuta di pagamento**" + (f" · {_ca_data_it(r['data_doc'])}" if r.get("data_doc") else "") + (f" · € {ca_importo_fmt(r['importo'])}" if r.get("importo") else ""))
                _ca_riga_documento(r, beni_nomi, k + "r", None)
    if "_fa_inv_voce" in globals() and caricato:
        _fa_inv_voce(f"casa_{k}", "📤 Invia questo documento (email, WhatsApp…)", f"📄 {d.get('titolo', 'Documento')}",
                     [("Tipo", d.get("tipo")), ("Emesso da", d.get("ente")), ("Importo", ("€ " + ca_importo_fmt(d["importo"])) if d.get("importo") else ""), ("Numero", d.get("numero_doc")),
                      ("Scadenza", _ca_data_it(d.get("scadenza_doc")) if d.get("scadenza_doc") else ""), ("Marca", d.get("marca")), ("Modello", d.get("modello")), ("Numero di serie", d.get("seriale"))], [f])
    conf = d.get("conferma") or {}
    if conf:
        st.caption(f"Confermato da {conf.get('da', '')} il {_ca_data_it(conf.get('il'))}" + (f" · corretti: {', '.join(conf['modificati'])}" if conf.get("modificati") else " · nessuna correzione"))


def _ca_form_documento(chiave, d, beni, riconosciuto=None, proposta_bene=None, motivi=None, bollette=None, proposta_bolletta=None, motivi_bolletta=None):
    """Il modulo «Controlla e conferma» (anche per correggere). Ritorna (inviato, valori)."""
    campi = (riconosciuto or {}).get("campi") or {}
    val = lambda k: (d or {}).get(k) if d else (campi.get(k) or {}).get("valore", "")
    def aff(k):
        c = campi.get(k) or {}
        return f" {_CA_AFF.get(c.get('affidabilita'), '')}" if c and not d else ""
    arg_v = val("argomento") if val("argomento") in CA_ARGOMENTI else (_ca_argomento_di(d) if d else "Altro")
    e_app = arg_v in _CA_ARG_APPARECCHIO
    with st.form(chiave, border=False):
        argomento = st.selectbox("Argomento: dove lo ritroverai" + aff("argomento"), CA_ARGOMENTI, index=CA_ARGOMENTI.index(arg_v), format_func=lambda a: f"{_CA_ICONE_ARG.get(a, '')} {a}")
        tipo_v = val("tipo") if val("tipo") in CA_TIPI else ("Manuale d'uso" if e_app else "Bolletta o fattura")
        tipo = st.selectbox("Che documento è" + aff("tipo"), CA_TIPI, index=CA_TIPI.index(tipo_v))
        ente = st.text_input("Chi lo ha emesso (azienda, ente, negozio o marca)" + aff("ente"), value=val("ente") or "", help="Con questo nome i documenti si raggruppano: tutte le bollette di «Enel Energia» stanno insieme.")
        c3, c4 = st.columns(2)
        data_doc = c3.date_input("Data del documento" + aff("data_doc"), value=_data(val("data_doc")), format="DD/MM/YYYY")
        lingue = list(CA_LINGUE)
        lingua = c4.selectbox("Lingua" + aff("lingua"), lingue, index=lingue.index(val("lingua")) if val("lingua") in lingue else lingue.index(""), format_func=lambda x: CA_LINGUE[x])
        with st.expander("🧾 Dati della bolletta o della fattura", expanded=not e_app):
            c5, c6 = st.columns(2)
            numero_doc = c5.text_input("Numero del documento" + aff("numero_doc"), value=val("numero_doc") or "")
            importo = c6.text_input("Importo totale in € (es. 87,35)" + aff("importo"), value=ca_importo_fmt(val("importo")) if val("importo") else "")
            c7, c8 = st.columns(2)
            periodo_da = c7.date_input("Periodo: dal" + aff("periodo_da"), value=_data(val("periodo_da")), format="DD/MM/YYYY")
            periodo_a = c8.date_input("Periodo: al" + aff("periodo_a"), value=_data(val("periodo_a")), format="DD/MM/YYYY")
            scadenza_doc = st.date_input("Scadenza del pagamento" + aff("scadenza_doc"), value=_data(val("scadenza_doc")), format="DD/MM/YYYY")
            codice_cliente = st.text_input("Codice cliente o contratto" + aff("codice_cliente"), value=val("codice_cliente") or "")
            codice_fornitura = st.text_input("Codice della fornitura (POD luce, PDR gas, telefono, polizza…)" + aff("codice_fornitura"), value=val("codice_fornitura") or "")
        with st.expander("🔧 Dati dell'apparecchio (per manuali, garanzie e acquisti)", expanded=e_app):
            cats = list(CA_CATEGORIE)
            cat = st.selectbox("Categoria" + aff("categoria"), cats, index=cats.index(val("categoria")) if val("categoria") in cats else len(cats) - 1)
            sotto = st.text_input("Che apparecchio è" + aff("sottocategoria"), value=val("sottocategoria") or "")
            c1, c2 = st.columns(2)
            marca = c1.text_input("Marca" + aff("marca"), value=val("marca") or "")
            modello = c2.text_input("Modello" + aff("modello"), value=val("modello") or "")
            seriale = st.text_input("Numero di serie" + aff("seriale"), value=val("seriale") or "")
        e_ricevuta = tipo == "Ricevuta di pagamento" or val("tipo") == "Ricevuta di pagamento"
        with st.expander("💶 Pagamento: collega la ricevuta alla sua bolletta", expanded=bool(e_ricevuta or (d or {}).get("collegato_a"))):
            bol = [b for b in (bollette or []) if b.get("tipo") in _CA_TIPI_PAGABILI and b.get("id") != (d or {}).get("id")]
            opz_b = [""] + [b["id"] for b in bol]
            att_b = (d or {}).get("collegato_a") if d else (proposta_bolletta or "")
            nomi_b = {b["id"]: _ca_etichetta_bolletta(b) for b in bol}
            collegato_a = st.selectbox("Questa è la ricevuta di pagamento della bolletta…" + (f" ({', '.join(motivi_bolletta)})" if motivi_bolletta and not d and proposta_bolletta else ""), opz_b,
                                       index=opz_b.index(att_b) if att_b in opz_b else 0, format_func=lambda x: "— nessuna: non è una ricevuta, o la bolletta non c'è ancora —" if not x else nomi_b.get(x, x),
                                       help="Così la ricevuta sta dentro la bolletta e questa risulta «pagata».")
            pagata_il = st.date_input("Oppure: questa bolletta è già stata pagata il (senza ricevuta)", value=_data((d or {}).get("pagata_il")), format="DD/MM/YYYY")
        opz = ["__nuovo__", ""] + [b["id"] for b in beni]
        nomi = {b["id"]: f"{b.get('nome', '')} ({b.get('marca', '')} {b.get('modello', '')})".replace("( )", "").strip() for b in beni}
        corrente = (d or {}).get("bene_id") if d else (proposta_bene or ("__nuovo__" if (e_app and (val("marca") or val("modello"))) else ""))
        etic = {"__nuovo__": "➕ Crea un nuovo bene con questi dati", "": "— Non collegare a nessun bene —"}
        bene = st.selectbox("Collega a un bene dell'inventario (facoltativo)" + (f" ({', '.join(motivi)})" if motivi and not d and proposta_bene else ""), opz, index=opz.index(corrente) if corrente in opz else 1,
                            format_func=lambda x: etic.get(x) or nomi.get(x, x), help="Le bollette di solito non vanno collegate a un bene: restano nel loro argomento.")
        titolo = st.text_input("Titolo", value=(d or {}).get("titolo", "") if d else "", placeholder="se lo lasci vuoto lo scrivo io (argomento, ente, numero, data, importo)")
        link = st.text_input("Link al documento online (facoltativo)", value=(d or {}).get("link", "") if d else "")
        note = st.text_input("Note (facoltative)", value=(d or {}).get("note", "") if d else "")
        ok = st.form_submit_button("✅ Conferma e archivia" if not d else "💾 Salva le correzioni", type="primary", width="stretch")
    return ok, {"argomento": argomento, "tipo": tipo, "ente": ente, "data_doc": data_doc, "lingua": lingua, "numero_doc": numero_doc, "importo": _ca_importo_da_testo(importo), "periodo_da": periodo_da,
                "periodo_a": periodo_a, "scadenza_doc": scadenza_doc, "codice_cliente": codice_cliente, "codice_fornitura": codice_fornitura, "categoria": cat, "sottocategoria": sotto,
                "marca": marca, "modello": modello, "seriale": seriale, "bene_id": bene, "collegato_a": collegato_a, "pagata_il": pagata_il, "titolo": titolo, "link": link, "note": note}


def _ca_mime(nome, tipo, dati):
    """Che file è davvero, guardando com'è fatto dentro (non fidandosi del telefono, che a volte dichiara un tipo vuoto o sbagliato) e poi dall'estensione."""
    testa = (dati or b"")[:1024]
    if b"%PDF" in testa:
        return "application/pdf"
    if testa.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if testa.startswith(b"\x89PNG"):
        return "image/png"
    if testa[:4] == b"RIFF" and testa[8:12] == b"WEBP":
        return "image/webp"
    est = str(nome or "").lower().rsplit(".", 1)[-1]
    if est == "txt" and not testa.startswith((b"%PDF", b"\xff\xd8", b"\x89PNG")):
        return "text/plain"
    return {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(est, tipo or "application/octet-stream")


_CA_JS_PDF = r"""
(function () {
  var w = window, doc = w.document;
  if (w.__caPdfAttivo2) return;
  w.__caPdfAttivo2 = true;
  var T = w.__caTempi || {lettura: 12000, primoAck: 20000, ack: 30000, upl: 40000};
  var CHUNK = 3 * 200 * 1024, MAX = __MAX__, ultimo = null, occupato = false, consegnati = {}, log = [];
  var AIUTO = ' METODO SICURO: apri il PDF, fai uno screenshot di una pagina (o fotografalo) e usa «🖼️ Dalla galleria». Oppure caricalo su Google Drive, condividilo con «chiunque abbia il link» e incolla il link in «🔗 …oppure prendi il manuale da un link».';
  function riga(t) {
    try {
      log.push(new Date().toLocaleTimeString() + '  ' + t);
      var el = doc.querySelector('[data-ca-log]');
      if (el) el.textContent = log.slice(-14).join('\n');
    } catch (e) {}
  }
  function stato(testo, errore) {
    var el = doc.querySelector('[data-ca-stato]');
    if (el) { el.textContent = testo; el.style.color = errore ? '#b71c1c' : '#0f766e'; }
    riga(testo);
  }
  function campo() { return doc.querySelector('input[aria-label="ca-pdf-trasf"]'); }
  function ack() { var e = doc.querySelector('[data-ca-ack]'); return e ? e.getAttribute('data-ca-ack') : ''; }
  function pausa(ms) { return new Promise(function (r) { w.setTimeout(r, ms); }); }
  function conTempo(p, ms, nome) {
    return new Promise(function (ok, ko) {
      var t = w.setTimeout(function () { ko(new Error(nome + ': nessuna risposta dal telefono dopo ' + Math.round(ms / 1000) + ' secondi')); }, ms);
      p.then(function (v) { w.clearTimeout(t); ok(v); }, function (e) { w.clearTimeout(t); ko(e); });
    });
  }
  function leggiFR(file) {
    return new Promise(function (ok, ko) {
      var r = new w.FileReader();
      r.onload = function () { ok(r.result); };
      r.onerror = function () { ko(r.error || new Error('lettura non riuscita')); };
      r.readAsArrayBuffer(file);
    });
  }
  async function leggiTutto(file) {
    var errori = [], metodi = [
      ['FileReader', function () { return leggiFR(file); }],
      ['arrayBuffer', function () { return file.arrayBuffer(); }],
      ['fetch', function () { return w.fetch(w.URL.createObjectURL(file)).then(function (r) { return r.arrayBuffer(); }); }]
    ];
    for (var m = 0; m < metodi.length; m++) {
      try {
        riga('lettura con ' + metodi[m][0] + '…');
        var buf = await conTempo(Promise.resolve().then(metodi[m][1]), T.lettura, metodi[m][0]);
        if (buf && buf.byteLength > 0) return buf;
        errori.push(metodi[m][0] + ': file vuoto');
      } catch (e) { errori.push(String(e && e.message ? e.message : e)); }
    }
    throw new Error(errori.join(' · '));
  }
  function scrivi(valore) {
    var inp = campo();
    if (!inp) return false;
    var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
    try { inp.focus(); } catch (e) {}
    setter.call(inp, valore);
    inp.dispatchEvent(new w.Event('input', {bubbles: true}));
    ['keydown', 'keypress', 'keyup'].forEach(function (t) {
      inp.dispatchEvent(new w.KeyboardEvent(t, {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
    });
    try { inp.blur(); } catch (e) {}
    inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
    return true;
  }
  function b64(buf, da, a) {
    var u = new Uint8Array(buf, da, a - da), s = '', passo = 0x8000;
    for (var i = 0; i < u.length; i += passo) s += String.fromCharCode.apply(null, u.subarray(i, Math.min(i + passo, u.length)));
    return w.btoa(s);
  }
  async function attendiAck(voluto, id, ms) {
    var t0 = Date.now();
    while (Date.now() - t0 < ms) {
      await pausa(300);
      var a = ack();
      if (a === voluto || a === id + ':fine') return true;
    }
    return false;
  }
  /* CANALE 1: il file passa a pezzi dal collegamento della pagina */
  async function canale1(buf, file) {
    var n = Math.max(1, Math.ceil(buf.byteLength / CHUNK)), id = Date.now().toString(36), nome = encodeURIComponent(file.name || 'documento');
    for (var i = 0; i < n; i++) {
      var parte = b64(buf, i * CHUNK, Math.min(buf.byteLength, (i + 1) * CHUNK)), voluto = id + ':' + i, riuscito = false, tentativi = i === 0 ? 2 : 3;
      for (var tent = 0; tent < tentativi && !riuscito; tent++) {
        stato('② Invio all\'app, pezzo ' + (i + 1) + ' di ' + n + (tent ? ' (nuovo tentativo)' : '') + '…');
        if (!scrivi(id + '|' + i + '|' + n + '|' + nome + '|' + parte)) { riga('punto di invio non trovato nella pagina'); return false; }
        riuscito = await attendiAck(voluto, id, i === 0 ? T.primoAck : T.ack);
      }
      if (!riuscito) { riga('nessuna conferma dall\'app per il pezzo ' + (i + 1)); return false; }
    }
    return true;
  }
  /* CANALE 2: il file viene consegnato al normale campo di caricamento di Streamlit (lo stesso sistema della fotocamera) */
  async function canale2(file) {
    var dest = doc.querySelector('[class*="st-key-fotopdf_cadoc"] input[type="file"]'), a0 = ack();
    if (!dest) { riga('campo di caricamento di riserva non trovato'); return false; }
    try {
      var dt = new w.DataTransfer(); dt.items.add(file); dest.files = dt.files;
      dest.dispatchEvent(new w.Event('change', {bubbles: true}));
    } catch (e) { riga('consegna al campo non riuscita: ' + (e && e.message ? e.message : e)); return false; }
    stato('③ Provo l\'altro canale di invio…');
    var t0 = Date.now();
    while (Date.now() - t0 < T.upl) {
      await pausa(300);
      var a = ack();
      if (a.indexOf('upl:') === 0 && a !== a0) return true;
    }
    return false;
  }
  async function manda(file) {
    if (occupato) return;
    occupato = true;
    try {
      var kb = Math.max(1, Math.round(file.size / 1024));
      riga('SCELTO: «' + (file.name || '?') + '» · ' + file.size + ' byte · tipo «' + (file.type || 'vuoto') + '»');
      if (file.size === 0) { stato('❌ Il telefono dice che il file è VUOTO (0 KB): di solito è un file ancora «in nuvola» o non scaricato del tutto.' + AIUTO, true); return; }
      if (file.size > MAX) { stato('❌ Il file è troppo grande (massimo 8 MB). Per i manuali più grandi usa il link al sito del produttore.', true); return; }
      stato('① Leggo il file «' + (file.name || 'documento') + '» (' + kb + ' KB)…');
      var buf;
      try { buf = await leggiTutto(file); }
      catch (e) { stato('❌ Il telefono non lascia leggere questo file al browser (' + e.message + ').' + AIUTO, true); return; }
      riga('letto: ' + buf.byteLength + ' byte');
      if (await canale1(buf, file)) { stato('✅ File ricevuto: ' + (file.name || 'documento')); return; }
      if (await canale2(file)) { stato('✅ File ricevuto: ' + (file.name || 'documento')); return; }
      stato('❌ Ho letto il file (' + kb + ' KB) ma non riesco a farlo arrivare all\'app, né dal primo né dal secondo canale.' + AIUTO, true);
    } catch (e) {
      stato('❌ Errore imprevisto: ' + (e && e.message ? e.message : e) + '.' + AIUTO, true);
    } finally { occupato = false; }
  }
  function consegna(inp) {
    var f = inp && inp.files && inp.files[0];
    if (!f) return;
    var chiave = f.name + '|' + f.size + '|' + f.lastModified;
    if (consegnati[chiave]) return;
    consegnati[chiave] = true;
    manda(f);
  }
  doc.addEventListener('click', function (e) {
    var b = e.target && e.target.closest ? e.target.closest('[data-ca-pdf]') : null;
    if (!b) return;
    e.preventDefault(); e.stopPropagation();
    consegnati = {};
    var inp = doc.createElement('input');
    inp.type = 'file';
    inp.style.display = 'none';                                  /* nessun filtro: il telefono mostra TUTTI i file */
    inp.addEventListener('change', function () { consegna(inp); });
    inp.addEventListener('input', function () { consegna(inp); });
    doc.body.appendChild(inp);                                   /* resta nella pagina: se il telefono la sospende durante la scelta, il file si recupera */
    ultimo = inp;
    stato('Scegli il file dal telefono…');
    inp.click();
  }, true);
  function ricontrolla() { if (ultimo) w.setTimeout(function () { consegna(ultimo); }, 700); }
  doc.addEventListener('visibilitychange', function () { if (!doc.hidden) ricontrolla(); });
  w.addEventListener('focus', ricontrolla);
  w.addEventListener('pageshow', ricontrolla);
})();
""".replace("__MAX__", str(8 * 1024 * 1024))


def _ca_avvia_trasferimento():
    """Mette nella pagina il programma che porta il file dal telefono all'app (stesso sistema usato per la fotocamera)."""
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_CA_JS_PDF) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_ca
            _comp_ca.html(pagina, height=0)
    except Exception:
        pass


def _ca_trasf_ricevi():
    """Raccoglie i pezzi del file mandati dalla pagina. Quando sono tutti, il file diventa il documento da leggere. Ritorna (conferma per la pagina, errore)."""
    v = st.session_state.get("ca_trasf_in") or ""
    if v and v != st.session_state.get("ca_trasf_visto"):
        st.session_state["ca_trasf_visto"] = v
        try:
            pid, i, n, nome_u, dati_b64 = v.split("|", 4)
            i, n = int(i), int(n)
            if not (0 <= i < n <= 40) or not re.fullmatch(r"[A-Za-z0-9]{1,16}", pid):
                raise ValueError("pacchetto non valido")
            raccolta = st.session_state.setdefault("ca_trasf_parti", {})
            if raccolta.get("id") != pid:
                raccolta.clear()
                raccolta.update({"id": pid, "parti": {}})
            raccolta["parti"][i] = dati_b64
            st.session_state["ca_trasf_ack"], st.session_state["ca_trasf_err"] = f"{pid}:{i}", ""
            if all(k in raccolta["parti"] for k in range(n)):
                dati = b"".join(base64.b64decode(raccolta["parti"][k]) for k in range(n))                  # ogni pezzo si decodifica da solo: va bene qualsiasi misura
                nome = urllib.parse.unquote(nome_u)[:120] or "documento"
                st.session_state["ca_bozza_in"] = {"nome": nome, "mime": _ca_mime(nome, "", dati), "dati": dati, "link": ""}
                st.session_state.pop("ca_bozza", None)
                st.session_state["ca_trasf_ack"] = f"{pid}:fine"
                raccolta.clear()
        except Exception as e:
            st.session_state["ca_trasf_err"] = f"Il trasferimento non è andato a buon fine ({e}). Riprova."
    return st.session_state.get("ca_trasf_ack", ""), st.session_state.get("ca_trasf_err", "")


def _ca_url_diretto(url):
    """Trasforma i link di condivisione di Google Drive e Dropbox nel link che scarica davvero il file."""
    m = re.search(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)", url) or re.search(r"drive\.google\.com/(?:open|uc)\?(?:[^#]*&)?id=([A-Za-z0-9_-]+)", url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    if "dropbox.com" in url:
        url = url.replace("dl=0", "dl=1")
        if "dl=1" not in url:
            url += ("&" if "?" in url else "?") + "dl=1"
    return url


_CA_CSS_FOTO = """<style>
[class*="st-key-nascosti_cadoc"]{display:none !important}
[class*="st-key-ca_ricezione"]{position:absolute !important;left:-9999px !important;top:0 !important;width:1px !important;height:1px !important;overflow:hidden !important;opacity:0 !important}
[class*="st-key-azioni_foto_cadoc"] [data-testid="stHorizontalBlock"]{flex-direction:row !important;flex-wrap:nowrap !important;gap:10px !important}
[class*="st-key-azioni_foto_cadoc"] [data-testid="stColumn"],[class*="st-key-azioni_foto_cadoc"] [data-testid="column"]{min-width:0 !important;width:auto !important;flex:1 1 0 !important}
[class*="st-key-scatta_cadoc"] button,[class*="st-key-galleria_cadoc"] button{min-height:64px;border-radius:999px !important;font-weight:800 !important;font-size:1.02rem;
 border:2px solid rgba(13,148,136,.45) !important;box-shadow:0 4px 0 rgba(0,100,90,.25);padding-left:6px;padding-right:6px}
[class*="st-key-scatta_cadoc"] button{background:linear-gradient(135deg,#00a98f,#0288d1) !important;color:#fff !important;border:0 !important}
[class*="st-key-scatta_cadoc"] button p{color:#fff !important}
.ca-pdf-btn{display:flex;align-items:center;justify-content:center;gap:8px;min-height:72px;border-radius:999px;background:linear-gradient(135deg,#f59e0b,#ef6c00);color:#fff;
 font-weight:900;font-size:1.1rem;cursor:pointer;box-shadow:0 5px 0 rgba(150,70,0,.35);text-align:center;padding:8px 14px;user-select:none}
.ca-pdf-stato{margin:6px 2px 10px;font-weight:700;color:#0f766e;font-size:.95rem;min-height:1.3em}
</style>"""
_CA_TIPI_FOTO = ["jpg", "jpeg", "png", "webp"]


def _ca_ultimo_file(candidati, chiave):
    """Tra i campi di caricamento vale l'ULTIMO file arrivato (foto scattata, galleria, PDF…)."""
    viste = st.session_state.setdefault(f"{chiave}_viste", {})
    ultima = st.session_state.get(f"{chiave}_ultima")
    for nome, fl in candidati.items():
        if fl is None:
            viste.pop(nome, None)
            continue
        ident = getattr(fl, "file_id", None) or f"{getattr(fl, 'name', '')}{getattr(fl, 'size', '')}"
        if viste.get(nome) != ident:
            viste[nome] = ident
            ultima = nome
    st.session_state[f"{chiave}_ultima"] = ultima
    return candidati.get(ultima) or next((fl for fl in candidati.values() if fl is not None), None)


def _ca_riduci_foto(nome, dati, massimo=None):
    """Una foto più grande del limite (le fotocamere nuove arrivano a 10 MB e oltre) viene ridotta, così si può archiviare. Ritorna (nome, dati) oppure None se non riesce."""
    massimo = massimo or (_CA_MAX_BYTE - 512 * 1024)
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
        for lato in (3200, 2600, 2000, 1600):
            for q in (88, 80, 70):
                x = im.copy()
                x.thumbnail((lato, lato))
                b = io.BytesIO()
                x.save(b, "JPEG", quality=q, optimize=True)
                if b.tell() <= massimo:
                    return re.sub(r"\.[A-Za-z0-9]{2,4}$", "", nome or "foto") + ".jpg", b.getvalue()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------------------------------------------------
# POSTA IN ARRIVO: i file arrivati per email (inoltrati a «…+casa@gmail.com» o con l'etichetta «Casa») li mette nell'archivio il programma posta.py, ogni poche ore;
# qui si vedono, si leggono e si archiviano come tutti gli altri documenti.
# ---------------------------------------------------------------------------------------------------------------------
_CA_INDIRIZZO_POSTA = "leoitalyto+casa@gmail.com"


def _ca_posta_percorso():
    return f"posta/{st.session_state['sess']['uid']}.json"


def _ca_posta_leggi():
    try:
        d = carica_dati(crea_archivio(), _ca_posta_percorso()) or {}
        return [x for x in d.get("items", []) if isinstance(x, dict) and x.get("file_id")]
    except Exception:
        return []


def _ca_posta_togli(pid, cancella_file=False):
    """Toglie un elemento dalla posta in arrivo (e, se serve, cancella il file arrivato)."""
    trovato = {}

    def _fn(d):
        resto = []
        for x in d.get("items", []):
            if x.get("id") == pid:
                trovato.update(x)
            else:
                resto.append(x)
        d["items"] = resto
    salva_file(_ca_posta_percorso(), _fn, "Posta: elemento tolto")
    if cancella_file and trovato.get("file_id") and "_fa_cancella_files" in globals():
        _fa_cancella_files([trovato["file_id"]])


def _ca_posta_riquadro(c):
    """Il riquadro «📥 Posta in arrivo» in cima alla scheda Documenti."""
    items = _ca_posta_leggi()
    titolo = f"📥 Posta in arrivo: {len(items)} da archiviare" if items else "📥 Posta in arrivo (nessun file nuovo)"
    with st.expander(titolo, expanded=bool(items)):
        for it in items[:15]:
            kb = max(1, int(it.get("dimensione") or 0) // 1024)
            st.markdown(f"<div class='ca-card'><b>📎 {_ca_testo(it.get('nome') or 'file')}</b> · {kb} KB<br><span style='font-size:.85rem'>da {_ca_testo(it.get('da') or '?')}"
                        + (f" · «{_ca_testo(it.get('oggetto'))}»" if it.get("oggetto") else "") + (f" · {_ca_data_it(str(it.get('data_mail') or '')[:10])}" if it.get("data_mail") else "") + "</span></div>", unsafe_allow_html=True)
            q1, q2 = st.columns(2, gap="small")
            if q1.button("📖 Leggi e archivia", key=f"ca_po_ok_{it['id']}", width="stretch", type="primary"):
                car = _fa_inv_allegati([{"id": it["file_id"], "nome": it.get("nome"), "mime": it.get("mime")}]) if "_fa_inv_allegati" in globals() else []
                if not car:
                    st.error("Non riesco ad aprire questo file: toccalo di nuovo fra poco, oppure scartalo.")
                else:
                    nome_, mime_, dati_ = car[0]
                    st.session_state["ca_bozza_in"] = {"nome": nome_, "mime": _ca_mime(nome_, mime_, dati_), "dati": dati_, "link": "", "file_id": it["file_id"], "posta_id": it["id"]}
                    st.session_state.pop("ca_bozza", None)
                    st.rerun()
            if q2.button("🗑️ Scarta", key=f"ca_po_no_{it['id']}", width="stretch"):
                try:
                    _ca_posta_togli(it["id"], cancella_file=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Non sono riuscito: {e}")
        if len(items) > 15:
            st.caption(f"…e altri {len(items) - 15}: archivia questi per vedere i prossimi.")
        st.markdown(f"**Come ci mandi un documento dalla posta:** inoltralo (o scrivi, allegando il file) a **{_CA_INDIRIZZO_POSTA}**, oppure dalle app dei fornitori tocca **Condividi → Gmail** e usa quell'indirizzo. "
                    "Anche i messaggi con l'etichetta Gmail **«Casa»** arrivano qui. Il programma controlla la posta alcune volte al giorno.")
        st.link_button("🔄 Controlla la posta adesso", "https://github.com/Leoitalyto/dispensa-dati/actions/workflows/posta.yml", width="stretch")
        st.caption("Si apre GitHub: tocca **Run workflow** e poi **Run workflow**; dopo circa un minuto torna qui e ricarica la pagina.")


def _ca_val_da_ric(ric, **extra):
    """I dati di una lettura, nella forma del modulo (per archiviare in un tocco)."""
    v = {k: (ric["campi"].get(k) or {}).get("valore", "") for k in _CAMPI_DOC}
    v.update({"bene_id": "", "link": "", "note": "", "titolo": ""})
    v["tipo"] = v.get("tipo") or "Ricevuta di pagamento"
    v["categoria"] = v.get("categoria") or "Altro"
    v.update(extra)
    return v


def _ca_archivia(sorgente, sha, ric, bozza, val, n):
    """Archivia il documento (originale intatto + dati letti + classificazione + conferma). Ritorna il messaggio da mostrare. Se il file viene dalla posta è già nell'archivio: non si ricopia."""
    nid = sorgente.get("file_id") or uuid.uuid4().hex[:12]
    if not sorgente.get("file_id"):
        _ca_scrivi_file(nid, sorgente["nome"], sorgente["mime"], sorgente["dati"])                   # 1) l'originale, intatto
    ora, utente = _ca_ora(), (st.session_state.get("sess") or {}).get("nome", "")
    rif = {"id": nid, "nome": sorgente["nome"], "mime": sorgente["mime"], "sha256": sha, "dimensione": len(sorgente["dati"]), **({"ridotta": True} if sorgente.get("ridotta") else {})}
    proposta = {k: (ric["campi"].get(k) or {}).get("valore", "") for k in ("tipo", "categoria", "sottocategoria")}
    proposta["bene_id"] = (bozza or {}).get("bene") or ""

    def _fn(cc, val=val, ora=ora, utente=utente, rif=rif, proposta=proposta, ric=ric, sorg=sorgente):
        v = dict(val)
        if v.get("bene_id") == "__nuovo__":                                                          # nuovo bene dai dati confermati
            nb = ca_nuovo_bene(cc, {"nome": " ".join(x for x in (v["sottocategoria"], v["marca"], v["modello"]) if x) or v["titolo"] or "Nuovo bene", "categoria": v["categoria"],
                                    "sottocategoria": v["sottocategoria"], "marca": v["marca"], "modello": v["modello"], "seriale": v["seriale"]}, ora)
            v["bene_id"] = nb["id"]
        v["link"] = v.get("link") or sorg.get("link", "")
        ca_aggiungi_documento(cc, rif, ric, proposta, v, utente, ora)
    _ca_salva(_fn, "Casa: documento archiviato")
    if sorgente.get("posta_id") and "_ca_posta_togli" in globals():
        _ca_posta_togli(sorgente["posta_id"], cancella_file=False)
    st.session_state["ca_giro"] = n + 1
    for k in ("ca_bozza", "ca_bozza_in"):
        st.session_state.pop(k, None)
    return (f"✅ Documento archiviato in «{val.get('argomento') or 'Altro'}»" + (f" › «{val['ente']}»" if val.get("ente") else "")
            + (" e collegato alla sua bolletta" if val.get("collegato_a") else "") + ", con il file originale: lo ritrovi nella scheda Documenti.")


def _ca_tab_manuali(c):
    beni = c.get("beni", [])
    nomi = {b["id"]: b.get("nome", "") for b in beni}
    st.markdown("#### ➕ Archivia un documento: manuale, bolletta, fattura, polizza…")
    st.caption("Carica un **PDF**, una **foto** o una **scansione** (anche un PDF fatto con lo scanner): leggo il documento e ti propongo tipo, apparecchio, marca, modello e numero di serie, "
               "e lo collego al bene giusto. **Il file resta com'è**, e prima di archiviare controlli e confermi tu.")
    n = st.session_state.get("ca_giro", 0)
    _ca_posta_riquadro(c)
    chiave_f = f"cadoc{n}"
    if "_fa_assicura_fotocamera" in globals():                                  # la fotocamera posteriore è la stessa di Salute e della dispensa
        try:
            _fa_assicura_fotocamera()
        except Exception:
            pass
    st.markdown(_CA_CSS_FOTO, unsafe_allow_html=True)
    st.markdown("**📷 Fotografa il documento** — la copertina o la pagina con i dati dell'apparecchio")
    with st.container(key="azioni_foto_" + chiave_f):
        c_cam, c_gal = st.columns(2, gap="small")
        c_cam.button("📷 Scatta foto", key=f"scatta_{chiave_f}", width="stretch")
        c_gal.button("🖼️ Dalla galleria", key=f"galleria_{chiave_f}", width="stretch")
    with st.container(key="nascosti_" + chiave_f):
        f_cam = st.file_uploader("camera", type=_CA_TIPI_FOTO, key=f"fotocam_{chiave_f}")
        f_gal = st.file_uploader("galleria", type=_CA_TIPI_FOTO, key=f"fotogal_{chiave_f}")
        f_pdfx = st.file_uploader("canale2", key=f"fotopdf_{chiave_f}")                    # riserva del pulsante arancione: accetta qualsiasi file
    st.markdown("**📄 Oppure carica un PDF o un file già nel telefono**")
    _ca_avvia_trasferimento()
    ack_t, err_t = _ca_trasf_ricevi()
    if f_pdfx is not None:                                                                     # il file è arrivato dal canale 2: lo si dice alla pagina
        ack_t = _html_ca.escape(f"upl:{f_pdfx.name}:{f_pdfx.size}", quote=True)
    with st.container(key="ca_ricezione"):
        st.text_input("ca-pdf-trasf", key="ca_trasf_in", label_visibility="collapsed")
    st.markdown("<div class='ca-pdf-btn' role='button' tabindex='0' data-ca-pdf='1'>📎 Scegli il PDF o il file</div>"
                f"<div class='ca-pdf-stato' data-ca-stato='1'>{'⚠️ ' + err_t if err_t else ('✅ File ricevuto.' if (ack_t.endswith(':fine') or ack_t.startswith('upl:')) else 'Tocca il pulsante arancione e scegli il file: lo vedi tutto, anche se ha un nome strano.')}</div>"
                f"<span data-ca-ack='{ack_t}' style='display:none'></span>", unsafe_allow_html=True)
    st.caption("📸 **Metodo sicuro per un PDF:** aprilo, fai uno **screenshot** di una pagina (o fotografalo) e usa **«🖼️ Dalla galleria»**: la foto viene letta come il documento.")
    with st.expander("📂 Altro metodo: il campo di caricamento normale (solo PDF)"):
        up_pdf = st.file_uploader("PDF", type=["pdf"], key=f"ca_up_{n}", label_visibility="collapsed")
    with st.expander("🛟 Il PDF o la foto non si caricano? Prova da qui"):
        st.caption("Qui il telefono ti fa scegliere **qualsiasi file**, anche uno senza estensione o con un nome strano (per esempio scaricato da WhatsApp o da una mail): "
                   "controllo io dentro il file se è un PDF o una foto. Tocca il campo e scegli **Fotocamera**, **File** o **Documenti**.")
        f_soc = st.file_uploader("Scegli qualsiasi file", key=f"ca_soc_{n}", label_visibility="collapsed")
    with st.expander("🔎 Cosa ha ricevuto l'app finora (per capire dove si ferma)"):
        def _rx(fl):
            return f"ricevuto «{fl.name}» ({fl.size // 1024} KB)" if fl is not None else "niente"
        st.markdown("<pre data-ca-log='1' style='white-space:pre-wrap;font-size:.78rem;background:#eef7f5;border-radius:12px;padding:8px;margin:4px 0'>Qui compare il racconto passo passo del pulsante arancione: scegli un file e torna a guardare.</pre>", unsafe_allow_html=True)
        st.caption(f"Fotocamera: {_rx(f_cam)} · Galleria: {_rx(f_gal)} · Campo PDF: {_rx(up_pdf)} · Qualsiasi file: {_rx(f_soc)} · Canale 2 del pulsante: {_rx(f_pdfx)} · "
                   f"Pulsante arancione: {('file ricevuto' if (ack_t.endswith(':fine') or ack_t.startswith('upl:')) else ('in arrivo (pezzo ' + ack_t.split(':')[-1] + ')' if ack_t else 'niente'))}" + (f" · ⚠️ {err_t}" if err_t else ""))
    up = _ca_ultimo_file({"cam": f_cam, "gal": f_gal, "soc": f_soc, "pdf": up_pdf, "x": f_pdfx}, chiave_f)
    with st.expander("🔗 …oppure prendi il manuale da un link"):
        st.caption("Va bene anche il link di **Google Drive** o **Dropbox**. Attenzione: perché funzioni il file deve essere condiviso con «chiunque abbia il link»: dopo averlo caricato qui, **togli la condivisione**.")
        url = st.text_input("Indirizzo del PDF", key=f"ca_url_{n}", placeholder="https://…/manuale.pdf")
        if st.button("⬇ Scarica e leggi", key=f"ca_url_btn_{n}") and url.strip():
            if "_fa_scarica_pdf" in globals():
                with st.spinner("Scarico il PDF…"):
                    f, errore = _fa_scarica_pdf(_ca_url_diretto(url.strip()), "Manuale")
                if f is None:
                    st.error("Non riesco: " + str(errore))
                else:
                    st.session_state["ca_bozza_in"] = {"nome": f.name, "mime": "application/pdf", "dati": f.getvalue() if hasattr(f, "getvalue") else f.dati, "link": url.strip()}
                    st.rerun()
    sorgente = None
    if up is not None:
        _dati_up = up.getvalue()
        sorgente = {"nome": up.name, "mime": _ca_mime(up.name, up.type, _dati_up), "dati": _dati_up, "link": ""}
    elif st.session_state.get("ca_bozza_in"):
        sorgente = st.session_state["ca_bozza_in"]
    if sorgente:
        if sorgente["mime"] in _CA_MIME and sorgente["mime"].startswith("image/") and len(sorgente["dati"]) > _CA_MAX_BYTE and not sorgente.get("ridotta"):
            rid = _ca_riduci_foto(sorgente["nome"], sorgente["dati"])
            if rid:
                sorgente = dict(sorgente, nome=rid[0], mime="image/jpeg", dati=rid[1], ridotta=True)
                st.info("📷 La foto era molto grande: l'ho **ridotta** per poterla archiviare. Il testo si legge lo stesso.")
        elif sorgente["mime"] in _CA_MIME and sorgente.get("ridotta"):
            st.info("📷 La foto era molto grande: l'ho **ridotta** per poterla archiviare. Il testo si legge lo stesso.")
        if sorgente["mime"] not in _CA_MIME:
            st.error(f"Questo tipo di file non è ammesso: carica un PDF o una foto (JPG, PNG, WebP). Il file «{sorgente['nome']}» risulta di tipo «{sorgente['mime']}».")
        elif len(sorgente["dati"]) > _CA_MAX_BYTE:
            st.error("Il file è troppo grande (massimo 8 MB). Per i manuali più grandi usa il link al sito del produttore.")
        else:
            sha = _ca_sha(sorgente["dati"])
            bozza = st.session_state.get("ca_bozza")
            if not bozza or bozza.get("sha") != sha:
                with st.spinner("Leggo il documento…"):
                    testo, info = ca_estrai_testo(sorgente["nome"], sorgente["mime"], sorgente["dati"])
                    ric = ca_riconosci(sorgente["nome"], sorgente["mime"], sorgente["dati"], testo, info)
                    ai = ca_ai_classifica(testo, ric)
                    if ai:                                                              # se l'assistente intelligente è acceso, completa i dati che mancano
                        for k, v in ai.items():
                            if k in ("tipo", "categoria", "sottocategoria", "marca", "modello", "seriale", "lingua", "data_doc") and v and k not in ric["campi"]:
                                ric["campi"][k] = {"valore": v, "affidabilita": "media", "fonte": "assistente intelligente"}
                    bene_id, punti, motivi = ca_proponi_bene(beni, ric["campi"])
                    bol_id, motivi_b = ca_proponi_bolletta(c.get("documenti", []), ric["campi"]) if (ric["campi"].get("tipo") or {}).get("valore") == "Ricevuta di pagamento" else (None, [])
                bozza = {"sha": sha, "ric": ric, "bene": bene_id, "motivi": motivi, "bolletta": bol_id, "motivi_b": motivi_b}
                st.session_state["ca_bozza"] = bozza
            ric = bozza["ric"]
            if ric["info"].get("scansione"):
                st.warning("Questo PDF è una **scansione** (immagini senza testo): non riesco a leggerlo da solo. Compila tu i dati qui sotto, oppure carica una foto di una pagina con i dati.")
            elif not ric["testo_ok"]:
                st.info("Non sono riuscito a leggere testo dal file: controlla e completa tu i dati qui sotto.")
            else:
                st.success("Ho letto il documento. I pallini mostrano quanto sono sicuro: 🟢 alta, 🟡 media, 🟠 bassa. **Controlla e correggi** quello che serve.")
                if ric["info"].get("ocr_pdf"):
                    st.caption("📷 Questo PDF era una **scansione**: l'ho letto come una foto (solo le prime pagine). Lettere e numeri possono essere sbagliati, soprattutto **modello e numero di serie**: controllali.")
            if sorgente["mime"].startswith("image/"):
                st.image(sorgente["dati"], width=240)
            # ---- prova di pagamento (ricevuta, bonifico, screenshot dell'app del fornitore): si propone subito a quale bolletta collegarla
            docs_c = c.get("documenti", [])
            tipo_ric = (ric["campi"].get("tipo") or {}).get("valore", "")
            cand = ca_candidate_bollette(docs_c, ric["campi"])
            esatte = [x for x in cand if x["esatto"]]
            rapido = bool(cand) and (tipo_ric == "Ricevuta di pagamento" or (bool(esatte) and tipo_ric in ("", "Altro"))) and not st.session_state.get(f"ca_scelgo_io_{n}")
            if rapido:
                imp_r = (ric["campi"].get("importo") or {}).get("valore", "")
                dat_r = (ric["campi"].get("data_doc") or {}).get("valore", "")
                st.markdown("#### 💶 Sembra la prova di un pagamento" + (f": € {ca_importo_fmt(imp_r)}" if imp_r else "") + (f", del {_ca_data_it(dat_r)}" if dat_r else ""))
                if esatte:
                    st.success(f"Ho trovato {len(esatte)} {'bolletta' if len(esatte) == 1 else 'bollette'} non pagat{'a' if len(esatte) == 1 else 'e'} con lo stesso importo" + (": è questa?" if len(esatte) == 1 else ": quale è?"))
                else:
                    st.info("Non trovo una bolletta con questo importo. Scegli tu a quale collegarla, oppure archiviala da sola.")
                bmap = {b_["id"]: b_ for b_ in docs_c}
                ordine_o = [x["id"] for x in esatte] + [x["id"] for x in cand if not x["esatto"]][:8]
                def _et(i):
                    if i == "__nessuna__":
                        return "— Nessuna di queste: la archivio da sola —"
                    b_ = bmap[i]
                    return f"{_CA_ICONE_ARG.get(_ca_argomento_di(b_), '')} {_ca_etichetta_bolletta(b_)}" + (" ✅ stesso importo" if i in [x['id'] for x in esatte] else "")
                scelta = st.radio("A quale bolletta la collego?", ordine_o + ["__nessuna__"], format_func=_et, key=f"ca_q_scelta_{n}")
                q1, q2 = st.columns(2, gap="small")
                if q1.button("✅ Collega e archivia" if scelta != "__nessuna__" else "📥 Archivia da sola", key=f"ca_q_ok_{n}", type="primary", width="stretch"):
                    try:
                        st.session_state["messaggio"] = _ca_archivia(sorgente, sha, ric, bozza, _ca_val_da_ric(ric, collegato_a="" if scelta == "__nessuna__" else scelta), n)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Non sono riuscito a salvare: {e}")
                if q2.button("✋ Scelgo io (modulo completo)", key=f"ca_q_io_{n}", width="stretch"):
                    st.session_state[f"ca_scelgo_io_{n}"] = True
                    st.rerun()
                if st.button("✖ Scarta", key="ca_scarta_q", width="stretch"):
                    if sorgente.get("posta_id") and "_ca_posta_togli" in globals():
                        _ca_posta_togli(sorgente["posta_id"], cancella_file=True)
                    st.session_state["ca_giro"] = n + 1
                    for k in ("ca_bozza", "ca_bozza_in"):
                        st.session_state.pop(k, None)
                    st.rerun()
            else:
                ok, val = _ca_form_documento("ca_form_nuovo", None, beni, ric, bozza.get("bene"), bozza.get("motivi"), docs_c, bozza.get("bolletta"), bozza.get("motivi_b"))
                c1, c2 = st.columns(2)
                if c2.button("✖ Scarta", key="ca_scarta", width="stretch"):
                    if sorgente.get("posta_id") and "_ca_posta_togli" in globals():
                        _ca_posta_togli(sorgente["posta_id"], cancella_file=True)
                    st.session_state["ca_giro"] = n + 1
                    for k in ("ca_bozza", "ca_bozza_in"):
                        st.session_state.pop(k, None)
                    st.rerun()
                if ok:
                    try:
                        st.session_state["messaggio"] = _ca_archivia(sorgente, sha, ric, bozza, val, n)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Non sono riuscito a salvare: {e}")
    # ---- correzione e cancellazione
    cid = st.session_state.get("ca_correggi")
    if cid:
        d = next((x for x in c.get("documenti", []) if x["id"] == cid), None)
        if d:
            st.markdown(f"##### ✏️ Correggi: {_ca_testo(d.get('titolo'))}")
            if st.button("🔄 Rileggi il file e completa i dati mancanti", key=f"ca_rileggi_{cid}", width="stretch",
                         help="Rilegge il file con il lettore aggiornato e riempie SOLO i campi ancora vuoti: quello che hai già scritto o corretto non si tocca."):
                f_ = d.get("file") or {}
                car = _ca_leggi_file(f_) if f_.get("id") else []
                if not car:
                    st.warning("Il file originale non è disponibile.")
                else:
                    nome_, mime_, dati_ = car[0]
                    testo_, info_ = ca_estrai_testo(nome_, mime_, dati_)
                    ric_ = ca_riconosci(nome_, mime_, dati_, testo_, info_)
                    nuovi = {k: v["valore"] for k, v in ric_["campi"].items() if k in _CAMPI_CONTROLLATI and v.get("valore") and not d.get(k) and not (k == "argomento" and d.get(k) == "Altro")}
                    def _riempi(cc, nuovi=nuovi, cid=cid):
                        x = next((y for y in cc.get("documenti", []) if y.get("id") == cid), None)
                        if x is not None and nuovi:
                            vecchio_auto = ca_titolo_auto(x)
                            x.update(nuovi)
                            if x.get("titolo") in ("", vecchio_auto):
                                x["titolo"] = ca_titolo_auto(x) or x.get("titolo", "")
                    if nuovi:
                        _ca_salva(_riempi, "Casa: dati completati rileggendo il file")
                    st.session_state["messaggio"] = ("🔄 Ho completato: " + ", ".join(nuovi)) if nuovi else "🔄 Ho riletto il file: non c'era niente da aggiungere."
                    st.session_state.pop("ca_correggi", None)
                    st.rerun()
            ok, val = _ca_form_documento(f"ca_form_cor_{cid}", d, beni, bollette=c.get("documenti", []))
            if st.button("Annulla", key="ca_cor_annulla"):
                st.session_state.pop("ca_correggi", None)
                st.rerun()
            if ok:
                try:
                    _ca_salva(lambda cc: ca_correggi_documento(cc, cid, val, (st.session_state.get("sess") or {}).get("nome", ""), _ca_ora()), "Casa: documento corretto")
                    st.session_state.pop("ca_correggi", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Non sono riuscito a salvare: {e}")
    did = st.session_state.get("ca_elimina_doc")
    if did:
        d = next((x for x in c.get("documenti", []) if x["id"] == did), None)
        if d:
            st.warning(f"Eliminare «{d.get('titolo')}»? Il file originale verrà cancellato.")
            e1, e2 = st.columns(2)
            if e1.button("🗑️ Sì, elimina", key="ca_del_si", type="primary", width="stretch"):
                try:
                    ids = []
                    _ca_salva(lambda cc: ids.append(ca_elimina_documento(cc, did)), "Casa: documento eliminato")
                    if "_fa_cancella_files" in globals():
                        _fa_cancella_files([i for i in ids if i])
                    st.session_state.pop("ca_elimina_doc", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Non sono riuscito: {e}")
            if e2.button("No, tienilo", key="ca_del_no", width="stretch"):
                st.session_state.pop("ca_elimina_doc", None)
                st.rerun()
    # ---- l'archivio: per ARGOMENTO (Luce, Gas, Acqua…), dentro per ENTE (la compagnia, il negozio, la marca), dentro per DATA
    docs = c.get("documenti", [])
    st.divider()
    if not docs:
        st.info("Non hai ancora archiviato nessun documento. Carica qui sopra il primo: un manuale, una bolletta, una fattura, una polizza…")
        return
    st.markdown(f"#### 📚 I tuoi documenti ({len(docs)})")
    cerca = st.text_input("Cerca", key="ca_cerca", placeholder="ente, titolo, numero, marca, modello…", label_visibility="collapsed")
    presenti = [a_ for a_ in CA_ARGOMENTI if any(_ca_argomento_di(d) == a_ for d in docs)]       # (le ricevute collegate contano dentro la loro bolletta)
    f1, f2 = st.columns(2, gap="small")
    farg = f1.selectbox("Argomento", [""] + presenti, format_func=lambda x: "📂 Tutti gli argomenti" if not x else f"{_CA_ICONE_ARG.get(x, '')} {x} ({sum(1 for d in docs if _ca_argomento_di(d) == x)})", key="ca_farg")
    fbene = f2.selectbox("Bene", ["", "__nessuno__"] + [b["id"] for b in beni], format_func=lambda x: "🏠 Tutti i beni" if not x else "non collegati" if x == "__nessuno__" else nomi.get(x, x), key="ca_fbene")
    anni = sorted({(_ca_ordine(d) or "")[:4] for d in docs if (_ca_ordine(d) or "")[:4].isdigit()}, reverse=True)
    fanno = st.selectbox("Anno", [""] + anni, format_func=lambda x: "📅 Tutti gli anni" if not x else x, key="ca_fanno") if len(anni) > 1 else ""
    q = _ca_norm(cerca)
    gruppi = {}
    for d in docs:
        if farg and _ca_argomento_di(d) != farg:
            continue
        if fanno and not _ca_ordine(d).startswith(fanno):
            continue
        if fbene == "__nessuno__" and d.get("bene_id"):
            continue
        if fbene and fbene != "__nessuno__" and d.get("bene_id") != fbene:
            continue
        parenti = [d] + ca_ricevute_di(docs, d["id"])
        if q and not any(q in _ca_norm(" ".join(str(x.get(k) or "") for k in ("titolo", "ente", "marca", "modello", "seriale", "tipo", "sottocategoria", "note", "categoria", "argomento", "numero_doc", "importo", "codice_cliente", "codice_fornitura"))) for x in parenti):
            continue
        if d.get("collegato_a") and any(x.get("id") == d["collegato_a"] for x in docs):          # ricevuta collegata: si vede dentro la sua bolletta
            continue
        gruppi.setdefault(_ca_argomento_di(d), {}).setdefault(_ca_ente_di(d), []).append(d)
    if not gruppi:
        st.info("Nessun documento corrisponde alla ricerca.")
        return
    for arg in [a_ for a_ in CA_ARGOMENTI if a_ in gruppi]:
        enti = gruppi[arg]
        st.markdown(f"### {_CA_ICONE_ARG.get(arg, '')} {arg} · {sum(len(v) for v in enti.values())}")
        for ente, lista in sorted(enti.items(), key=lambda kv: max(_ca_ordine(x) for x in kv[1]), reverse=True):
            lista.sort(key=_ca_ordine, reverse=True)
            ultimo = _ca_data_it(lista[0].get("data_doc")) if lista[0].get("data_doc") else ""
            etichetta = f"🏢 {ente} · {len(lista)} document{'o' if len(lista) == 1 else 'i'}" + (f" · ultimo {ultimo}" if ultimo else "")
            with st.expander(etichetta, expanded=bool(q) or len(enti) == 1 or bool(farg)):
                chiave_tutti = f"ca_tutti_{arg}_{ente}"
                visibili = lista if st.session_state.get(chiave_tutti) else lista[:12]
                for d in visibili:
                    _ca_riga_documento(d, nomi, "m", docs)
                if len(lista) > len(visibili) and st.button(f"Mostra tutti i {len(lista)} documenti", key="b_" + chiave_tutti):
                    st.session_state[chiave_tutti] = True
                    st.rerun()


def _ca_tab_beni(c):
    oggi_ = oggi()
    beni, docs = c.get("beni", []), c.get("documenti", [])
    with st.expander("➕ Aggiungi un bene (caldaia, lavatrice, TV…)", expanded=not beni):
        ok, val = _ca_form_bene("ca_form_bene_nuovo")
        if ok:
            if not val["nome"].strip():
                st.error("Scrivi almeno il nome del bene.")
            else:
                try:
                    _ca_salva(lambda cc: ca_nuovo_bene(cc, val, _ca_ora()), "Casa: bene aggiunto")
                    st.rerun()
                except Exception as e:
                    st.error(f"Non sono riuscito a salvare: {e}")
    if not beni:
        st.info("Qui trovi l'inventario della casa: caldaia, climatizzatori, elettrodomestici, TV, allarmi. Per ognuno puoi collegare manuali, garanzia e manutenzioni.")
        return
    st.markdown(f"**{len(beni)} beni** · {len(docs)} documenti")
    cerca = st.text_input("Cerca", key="ca_cerca_beni", placeholder="nome, marca, modello, stanza…", label_visibility="collapsed")
    cats = sorted({b.get("categoria") for b in beni if b.get("categoria")})
    fcat = st.selectbox("Categoria", [""] + cats, format_func=lambda x: x or "🏷️ Tutte le categorie", key="ca_fcat")
    q = _ca_norm(cerca)
    nomi = {b["id"]: b.get("nome", "") for b in beni}
    for b in sorted(beni, key=lambda x: _ca_norm(x.get("nome"))):
        if fcat and b.get("categoria") != fcat:
            continue
        if q and q not in _ca_norm(" ".join(str(b.get(k) or "") for k in ("nome", "marca", "modello", "stanza", "sottocategoria", "seriale", "categoria"))):
            continue
        stato, g = ca_stato_garanzia(b, oggi_)
        n_doc = sum(1 for d in docs if d.get("bene_id") == b["id"])
        chip_g = {"ok": _ca_chip(f"🛡️ In garanzia fino al {_ca_data_it(b.get('garanzia_fino'))}", "ca-ok"), "presto": _ca_chip(f"⚠️ Garanzia scade tra {g} giorni", "ca-presto"),
                  "scaduta": _ca_chip("Garanzia scaduta", "ca-scaduta"), "nessuna": ""}[stato]
        st.markdown(f"<div class='ca-card'><b>🏠 {_ca_testo(b.get('nome'))}</b><br>" + _ca_chip(_ca_testo(b.get("sottocategoria") or b.get("categoria") or "Bene")) + chip_g
                    + _ca_chip(f"📄 {n_doc} document{'o' if n_doc == 1 else 'i'}") + "<br><span style='font-size:.85rem'>"
                    + " · ".join(x for x in (_ca_testo(b.get("marca")), _ca_testo(b.get("modello")), _ca_testo(b.get("stanza"))) if x) + "</span></div>", unsafe_allow_html=True)
        aperto = st.session_state.get("ca_bene_aperto") == b["id"]
        if st.button("🙈 Chiudi la scheda" if aperto else "📂 Apri la scheda", key=f"ca_apri_{b['id']}", width="stretch"):
            st.session_state["ca_bene_aperto"] = None if aperto else b["id"]
            st.session_state.pop("ca_bene_mod", None)
            st.rerun()
        if aperto:
            _ca_scheda_bene(c, b, nomi)


def _ca_scheda_bene(c, b, nomi):
    docs = [d for d in c.get("documenti", []) if d.get("bene_id") == b["id"]]
    dettagli = [("Marca", b.get("marca")), ("Modello", b.get("modello")), ("Numero di serie", b.get("seriale")), ("Dove", b.get("stanza")),
                ("Acquistato il", _ca_data_it(b.get("acquisto"))), ("Garanzia fino al", _ca_data_it(b.get("garanzia_fino"))), ("Note", b.get("note"))]
    st.markdown("<br>".join(f"**{k}:** {_ca_testo(v)}" for k, v in dettagli if v) or "_Nessun dettaglio_", unsafe_allow_html=True)
    st.markdown("**📄 Documenti collegati**")
    if docs:
        for d in docs:
            _ca_riga_documento(d, nomi, "b")
    else:
        st.caption("Nessun documento collegato: caricane uno nella scheda «Documenti» e scegli questo bene.")
    liberi = [d for d in c.get("documenti", []) if not d.get("bene_id")]
    if liberi:
        sc = st.selectbox("Collega un documento già archiviato", [""] + [d["id"] for d in liberi], key=f"ca_coll_{b['id']}",
                          format_func=lambda x: "—" if not x else next((d.get("titolo", "") for d in liberi if d["id"] == x), x))
        if sc and st.button("🔗 Collega", key=f"ca_coll_ok_{b['id']}"):
            try:
                def _l(cc, sc=sc, bid=b["id"]):
                    for d in cc["documenti"]:
                        if d["id"] == sc:
                            d["bene_id"] = bid
                _ca_salva(_l, "Casa: documento collegato")
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito: {e}")
    man = sorted([m for m in c.get("manutenzioni", []) if m.get("bene_id") == b["id"]], key=lambda x: x.get("data") or "", reverse=True)
    st.markdown("**🔧 Storico delle manutenzioni**")
    if man:
        for m in man[:12]:
            st.markdown(f"- {_ca_data_it(m.get('data'))} · {_ca_testo(m.get('tipo'))}: {_ca_testo(m.get('descrizione'))}" + (f" · {_ca_testo(m.get('ditta'))}" if m.get("ditta") else "")
                        + (f" · prossima: {_ca_data_it(m.get('prossima'))}" if m.get("prossima") else ""))
    else:
        st.caption("Nessuna manutenzione registrata: aggiungila nella scheda «Manutenzioni».")
    e1, e2 = st.columns(2, gap="small")
    if e1.button("✏️ Modifica i dati", key=f"ca_mod_{b['id']}", width="stretch"):
        st.session_state["ca_bene_mod"] = b["id"]
        st.rerun()
    if e2.button("🗑️ Elimina il bene", key=f"ca_eli_{b['id']}", width="stretch"):
        st.session_state["ca_bene_elimina"] = b["id"]
        st.rerun()
    if st.session_state.get("ca_bene_mod") == b["id"]:
        ok, val = _ca_form_bene(f"ca_form_bene_mod_{b['id']}", b)
        if ok:
            try:
                _ca_salva(lambda cc: ca_aggiorna_bene(cc, b["id"], val), "Casa: bene modificato")
                st.session_state.pop("ca_bene_mod", None)
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
    if st.session_state.get("ca_bene_elimina") == b["id"]:
        st.warning(f"Eliminare «{b.get('nome')}»? Scegli cosa fare dei suoi {len(docs)} documenti.")
        con = st.radio("I documenti collegati", ["Tienili (restano senza bene)", "Eliminali insieme al bene"], key=f"ca_eli_rad_{b['id']}")
        s1, s2 = st.columns(2)
        if s1.button("🗑️ Elimina", key=f"ca_eli_si_{b['id']}", type="primary", width="stretch"):
            try:
                ids = []
                _ca_salva(lambda cc: ids.extend(ca_elimina_bene(cc, b["id"], con.startswith("Eliminali"))), "Casa: bene eliminato")
                if ids and "_fa_cancella_files" in globals():
                    _fa_cancella_files(ids)
                st.session_state.pop("ca_bene_elimina", None)
                st.session_state.pop("ca_bene_aperto", None)
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito: {e}")
        if s2.button("No", key=f"ca_eli_no_{b['id']}", width="stretch"):
            st.session_state.pop("ca_bene_elimina", None)
            st.rerun()


def _ca_tab_manutenzioni(c):
    beni = c.get("beni", [])
    if not beni:
        st.info("Prima aggiungi un bene nella scheda «Beni»: poi qui registri le sue manutenzioni.")
        return
    nomi = {b["id"]: b.get("nome", "") for b in beni}
    docs = c.get("documenti", [])
    with st.expander("➕ Registra una manutenzione o un intervento", expanded=not c.get("manutenzioni")):
        with st.form("ca_form_manut", border=False):
            bene = st.selectbox("Su quale bene", [b["id"] for b in beni], format_func=lambda x: nomi.get(x, x))
            c1, c2 = st.columns(2)
            data_m = c1.date_input("Data", value=oggi(), format="DD/MM/YYYY")
            tipo = c2.selectbox("Tipo", CA_TIPI_MANUTENZIONE)
            descr = st.text_input("Cosa è stato fatto", placeholder="es. Controllo fumi e pulizia bruciatore")
            c3, c4 = st.columns(2)
            ditta = c3.text_input("Ditta o tecnico")
            costo = c4.text_input("Costo (facoltativo)", placeholder="es. 90")
            prossima = st.date_input("Prossimo controllo (facoltativo)", value=None, format="DD/MM/YYYY")
            doc = st.selectbox("Documento dell'intervento (facoltativo)", [""] + [d["id"] for d in docs], format_func=lambda x: "—" if not x else next((d.get("titolo", "") for d in docs if d["id"] == x), x))
            note = st.text_input("Note (facoltative)")
            ok = st.form_submit_button("💾 Registra", type="primary", width="stretch")
        if ok:
            try:
                val = {"bene_id": bene, "data": data_m, "tipo": tipo, "descrizione": descr, "ditta": ditta, "costo": costo, "prossima": prossima, "documento_id": doc, "note": note}
                _ca_salva(lambda cc: ca_aggiungi_manutenzione(cc, val), "Casa: manutenzione registrata")
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
    sc = ca_scadenze(c, oggi())
    if sc["manutenzioni"]:
        st.markdown("**⏳ In arrivo o in ritardo**")
        for nome, voce, g in sc["manutenzioni"]:
            st.markdown(f"- {'🔴 in ritardo di ' + str(-g) + ' giorni' if g < 0 else '🟠 tra ' + str(g) + ' giorni' if g > 0 else '🔴 oggi'} · **{_ca_testo(nome)}**: {_ca_testo(voce)}")
    man = sorted(c.get("manutenzioni", []), key=lambda x: x.get("data") or "", reverse=True)
    if man:
        st.markdown("**📋 Storico**")
        for m in man[:40]:
            st.markdown(f"- {_ca_data_it(m.get('data'))} · **{_ca_testo(nomi.get(m.get('bene_id'), '?'))}** · {_ca_testo(m.get('tipo'))}: {_ca_testo(m.get('descrizione'))}"
                        + (f" · {_ca_testo(m.get('ditta'))}" if m.get("ditta") else "") + (f" · {_ca_testo(m.get('costo'))} €" if m.get("costo") else ""))


def schermata_casa():
    """La pagina «Casa»."""
    if "nav_barra" in globals():
        nav_barra("casa")
    st.markdown(_CA_CSS, unsafe_allow_html=True)
    uri = _fa_file_uri("casa.webp") if "_fa_file_uri" in globals() else ""
    st.markdown(f"<div class='ca-hero'>{('<img src=' + chr(34) + uri + chr(34) + '>') if uri else ''}<div><h1>Casa</h1>"
                "<p>I beni della casa, i loro manuali e le manutenzioni, sempre a portata di mano</p></div></div>", unsafe_allow_html=True)
    if "pulsante_info" in globals():
        try:
            pulsante_info("casa")
        except Exception:
            pass
    c = _ca_dati()
    sc = ca_scadenze(c, oggi())
    for nome, g in sc["garanzie"][:3]:
        st.warning(f"🛡️ La garanzia di **{nome}** scade tra {g} giorni.")
    for nome, voce, g in sc["manutenzioni"][:3]:
        st.warning(f"🔧 **{nome}**: {voce} — " + (f"in ritardo di {-g} giorni" if g < 0 else "oggi" if g == 0 else f"tra {g} giorni"))
    for nome, g, imp in sc.get("bollette", [])[:4]:
        st.warning(f"💶 **{nome}**" + (f" (€ {ca_importo_fmt(imp)})" if imp else "") + " — " + (f"scaduta da {-g} giorni, non risulta pagata: carica la ricevuta o tocca «Segna come pagata»" if g < 0 else "da pagare oggi" if g == 0 else f"da pagare entro {g} giorni"))
    t1, t2, t3 = st.tabs(["🏠 Beni", "📚 Documenti", "🔧 Manutenzioni"])
    with t1:
        _ca_tab_beni(c)
    with t2:
        _ca_tab_manuali(c)
    with t3:
        _ca_tab_manutenzioni(c)


# ---------------------------------------------------------------------------------------------------------------------
# Aggancio all'app (senza modificare le funzioni esistenti: le «avvolge»)
# ---------------------------------------------------------------------------------------------------------------------
if "casa" not in SEZIONI_NAV:                                       # la navigazione ← → : Casa sta tra Archivio e Utilità
    SEZIONI_NAV.insert(SEZIONI_NAV.index("archivio") + 1 if "archivio" in SEZIONI_NAV else len(SEZIONI_NAV), "casa")
NOMI_NAV.setdefault("casa", "Casa")

if "_NOMI_SEZIONI" in globals():                                    # la guida della sezione (l'assistente la usa da solo)
    _NOMI_SEZIONI.setdefault("casa", "🏡 Casa")
    _GUIDE.setdefault("casa", [
        ("🏡 Cos'è la sezione Casa",
         """La sezione **Casa** raccoglie **i beni della tua casa** (caldaia, climatizzatori, elettrodomestici, TV, allarmi, impianti), **tutti i documenti di casa** (manuali, garanzie, bollette di luce, gas e acqua, fatture, polizze…) e **le manutenzioni**.
Ha tre schede in basso: **🏠 Beni**, **📚 Documenti**, **🔧 Manutenzioni**.
Si apre dall'icona della casa in Home, oppure con le frecce ← → in alto.""",
         "casa abitazione beni inventario caldaia lavatrice manuali manutenzioni sezione"),
        ("📚 Archiviare un documento (manuale, bolletta, fattura…)",
         """1. Apri **Casa** e tocca la scheda **📚 Documenti**.
2. In **Archivia un documento** carica un **PDF**, una **foto** o una **scansione** (massimo 8 MB), oppure usa **🔗 prendi il manuale da un link**.
3. Leggo il documento e capisco **di cosa parla** (Luce, Gas, Acqua, Telefono e Internet, Rifiuti, Condominio, Assicurazioni, Manuali…). Per una **bolletta o fattura** ti propongo **chi l'ha emessa, importo, numero, data, periodo, scadenza e codici** (cliente, POD, PDR…); per un **manuale** categoria, marca, modello e numero di serie. I pallini dicono quanto sono sicuro: 🟢 alta, 🟡 media, 🟠 bassa.
4. **Controlla e correggi** quello che non va. Le bollette di solito **non si collegano a un bene**; i manuali sì (o crei un nuovo bene). Poi tocca **✅ Conferma e archivia**.

**Ricevuta di pagamento:** può essere un PDF, una foto, un bonifico o anche lo **screenshot dell'app del fornitore** («Pagato in data…»). Caricala come gli altri documenti: leggo l'importo e la data e ti chiedo subito **a quale bolletta collegarla** (cerco prima quelle con lo stesso importo, di qualsiasi argomento) con un tocco su **✅ Collega e archivia**; se preferisci, **✋ Scelgo io** apre il modulo completo. Una volta collegata, la ricevuta sta **dentro la sua bolletta** e la bolletta risulta **✅ Pagata**. Se hai pagato senza ricevuta, tocca **«✅ Segna come pagata»**. Le bollette in scadenza o scadute e non pagate compaiono tra gli avvisi in cima a Casa.

**Come ritrovi i documenti:** sono ordinati per **argomento** (💡 Luce, 🔥 Gas, 💧 Acqua…); dentro ogni argomento c'è una **linguetta per ogni azienda o ente** (per esempio «Enel Energia», «SMAT», «TIM»); dentro, i documenti dal **più recente** al più vecchio. Con **⬇ Apri / scarica** apri il file originale, con **👁️ Vedi qui** lo guardi nella pagina. Puoi cercare per nome, numero o importo e filtrare per argomento e anno.

Puoi **scattare una foto** (tasto «📷 Scatta foto», che apre la fotocamera posteriore), prenderla **dalla galleria**, oppure toccare il pulsante arancione **«📎 Scegli il PDF o il file»**: il telefono ti fa scegliere qualsiasi file, anche con un nome strano. Se qualcosa non va, il riquadro **«🔎 Cosa ha ricevuto l'app finora»** dice a che punto si ferma. Un PDF si può anche prendere da un **link** (anche di Google Drive o Dropbox). Il **file originale resta com'è**, identico (una foto enorme viene ridotta, e viene segnato). Un PDF fatto con lo scanner (solo immagini) viene letto come una foto, ma solo le **prime 3 pagine**: lettere e numeri possono essere sbagliati, quindi **controlla soprattutto modello e numero di serie**. Se non riesco a leggerlo, compili tu i dati.""",
         "archiviare manuale manuali caricare pdf foto scansione riconoscimento marca modello numero di serie conferma"),
        ("🏠 Aggiungere e collegare un bene",
         """In **🏠 Beni** tocca **➕ Aggiungi un bene** e compila nome, categoria, marca, modello, numero di serie, dove si trova, data di acquisto e garanzia.
Tocca **📂 Apri la scheda** per vedere **tutti i documenti collegati** (li apri o li scarichi da lì), lo **storico delle manutenzioni** e collegare un documento già archiviato.
Puoi **modificare** o **eliminare** il bene: scegli se tenere o eliminare i suoi documenti.""",
         "bene beni inventario aggiungere collegare garanzia scheda caldaia documenti collegati"),
        ("🔧 Registrare una manutenzione",
         """In **🔧 Manutenzioni** tocca **➕ Registra una manutenzione o un intervento**: scegli il bene, la data, cosa è stato fatto, la ditta, il costo e, se vuoi, il **prossimo controllo**.
In cima alla pagina Casa compaiono gli avvisi di **garanzie** in scadenza e **manutenzioni** in arrivo o in ritardo.

**Avvisi sul telefono (a scelta):** in **Salute → 🔔 Scegli come ricevere gli avvisi** scegli i canali (**Telegram**, **email**, **SMS** o **WhatsApp**) e spunta **🏡 Avvisami anche delle garanzie e delle manutenzioni di Casa**. Le garanzie arrivano a 60, 30, 14, 7, 1 giorno e il giorno stesso; le manutenzioni a 30, 14, 7, 1 giorno e il giorno stesso, e ogni lunedì se sono in ritardo.
**WhatsApp** è gratuito ma serve la tua **chiave personale di CallMeBot**: la spiegazione è nello stesso riquadro. Gli **SMS** sono a pagamento (servizio Twilio configurato dall'amministratore).""",
         "manutenzione intervento controllo caldaia tecnico ditta prossimo controllo scadenza garanzia"),
        ("📥 Mandare documenti dalla posta o dalle app dei fornitori",
         f"""Inoltra un messaggio con un PDF o una foto (o scrivine uno, allegando il file) a **{_CA_INDIRIZZO_POSTA}**: il programma controlla la posta alcune volte al giorno e mette i file nel riquadro **📥 Posta in arrivo** della scheda Documenti. Lì tocchi **📖 Leggi e archivia** e il documento viene classificato come tutti gli altri.
Dalle **app dei fornitori** (luce, gas, telefono…) tocca **Condividi** (o «Invia») sul PDF o sullo screenshot, scegli **Gmail** e come destinatario **{_CA_INDIRIZZO_POSTA}** (salvalo in rubrica come «Casa dispensa»).
Anche i messaggi che metti nell'etichetta Gmail **«Casa»** arrivano qui. I messaggi senza allegati (per esempio «Abbiamo ricevuto il tuo pagamento…») diventano un file di testo, e si leggono lo stesso.
**🔄 Controlla la posta adesso** apre GitHub per far partire subito il controllo (tocca **Run workflow**).""",
         "posta email inoltrare gmail allegato condividere app fornitore bolletta screenshot casa dispensa"),
        ("✏️ Correggere o eliminare un documento",
         """Nell'elenco dei documenti tocca **✏️ Correggi** per cambiare argomento, azienda, importo, date, tipo, marca, modello, bene collegato e il resto: l'originale e i dati letti dal programma restano com'erano.
Tocca **🗑️ Elimina** per toglierlo (ti chiedo conferma). **📤 Invia** lo manda per email, WhatsApp o Telegram.""",
         "correggere modificare eliminare cancellare documento manuale inviare condividere"),
    ])
    _ID_GUIDA.setdefault("casa", ["c_cosa", "c_manuali", "c_beni", "c_manutenzioni", "c_posta", "c_correggi"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("casa", "c_cosa")

def casa_css():
    """Gli stili dell'icona di Casa e le misure comuni alle quattro icone della Home. Si aggiungono allo stile che icona_farmacia scrive già (un piccolo aggancio):
    così nella colonna di Casa c'è soltanto il pulsante e l'icona sta alla stessa altezza delle altre."""
    uri_c = _fa_file_uri("casa.webp") if "_fa_file_uri" in globals() else ""
    if not uri_c:
        return ""
    return ("@keyframes ca-battito{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.25))}50%{transform:scale(1.06);filter:drop-shadow(0 0 14px rgba(255,193,7,.95))}}"
            + _css_icona("casa_icona", uri_c, "1/1", "ca-battito", 2.4, 80)
            + ".st-key-azioni_icone .st-key-fa_icona button,.st-key-azioni_icone .st-key-doc_icona button,.st-key-azioni_icone .st-key-ut_icona button,"
              ".st-key-azioni_icone .st-key-casa_icona button{width:80px}"
              ".st-key-azioni_icone div[style*='width:112px']{width:80px !important;font-size:.6rem !important}")


def casa_pulsante():
    """L'icona di Casa nella riga della Home, tra «I miei documenti» e «Utilità» (la chiama un piccolo aggancio in icona_farmacia). Ritorna True se è stata toccata."""
    if not (_fa_file_uri("casa.webp") if "_fa_file_uri" in globals() else ""):
        return False
    sc = ca_scadenze(_ca_dati(), oggi())
    n_av = len(sc["garanzie"]) + len(sc["manutenzioni"]) + len(sc.get("bollette", []))
    premuto = st.button("Casa", key="casa_icona", help="Apri Casa: beni, manuali e manutenzioni")
    if n_av:
        st.markdown(f"<div style='width:80px;text-align:center;font-weight:800;font-size:.6rem;color:#e65100'>⚠️ {n_av} da controllare</div>", unsafe_allow_html=True)
    return premuto


if "schermata_farmacia" in globals() and "_casa_schermata_prima" not in globals():
    _casa_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                       # noqa: F811 — lo smistamento delle sezioni: «casa» va alla sua pagina, tutto il resto come prima
        if st.session_state.get("sezione_home") == "casa":
            return schermata_casa()
        return _casa_schermata_prima()
