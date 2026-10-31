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
import re
import uuid
from datetime import date, datetime

import streamlit as st

CA_TIPI = ["Manuale d'uso", "Manuale di installazione", "Manuale di manutenzione", "Scheda tecnica", "Certificato di garanzia", "Libretto di impianto",
           "Dichiarazione di conformità", "Istruzioni di montaggio", "Fattura o scontrino", "Documentazione di un intervento", "Altro"]
CA_LINGUE = {"it": "Italiano", "en": "Inglese", "de": "Tedesco", "fr": "Francese", "es": "Spagnolo", "": "Non so"}
CA_STANZE = ["Cucina", "Soggiorno", "Camera da letto", "Bagno", "Ingresso", "Studio", "Lavanderia", "Garage", "Cantina", "Giardino", "Terrazzo", "Tutta la casa", "Altro"]
CA_TIPI_MANUTENZIONE = ["Controllo", "Manutenzione ordinaria", "Manutenzione straordinaria", "Riparazione", "Pulizia o sostituzione filtri", "Altro"]
_CA_MIME = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
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
def ca_estrai_testo(nome, mime, dati, max_pagine=8, max_car=24000):
    """(testo, info). Dai PDF con testo si legge il testo; dalle foto e dalle scansioni, se c'è, con l'OCR. info = {pagine, titolo, data_meta, scansione, metodo}."""
    info = {"pagine": None, "titolo": "", "data_meta": None, "scansione": False, "metodo": ""}
    if mime == "application/pdf":
        try:
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
            info["metodo"] = "testo del PDF"
            if len(re.sub(r"\s+", "", testo)) < 40:
                info["scansione"] = True
                return "", info
            return testo, info
        except Exception:
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
        if punti > punti_m:
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


def ca_riconosci(nome, mime, dati, testo=None, info=None):
    """Legge un documento e propone i dati. Ritorna {'testo_ok', 'info', 'campi': {nome: {'valore', 'affidabilita', 'fonte'}}, 'testo_inizio'}. NON salva niente."""
    if testo is None:
        testo, info = ca_estrai_testo(nome, mime, dati)
    info = info or {}
    stem = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", nome or "").replace("_", " ").replace("-", " ")
    campi = {}

    def metti(k, valore, aff, fonte):
        if valore:
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
_CAMPI_DOC = ("tipo", "titolo", "categoria", "sottocategoria", "marca", "modello", "seriale", "data_doc", "lingua", "bene_id", "link", "note")
_CAMPI_CONTROLLATI = ("tipo", "categoria", "sottocategoria", "marca", "modello", "seriale", "data_doc", "lingua")


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


def ca_aggiungi_documento(c, file_ref, riconosciuto, proposta, finale, utente, ora):
    """Archivia un documento con i QUATTRO livelli separati: file originale · dati riconosciuti · classificazione proposta · conferma di chi usa l'app."""
    campi_prop = {k: (v.get("valore") if isinstance(v, dict) else v) for k, v in ((riconosciuto or {}).get("campi") or {}).items()}
    fin = _ca_pulisci(finale, _CAMPI_DOC)
    modificati = [k for k in _CAMPI_CONTROLLATI if str(campi_prop.get(k) or "") != fin.get(k, "")]
    doc = dict(fin)
    doc.update({
        "id": uuid.uuid4().hex[:10], "creato_il": ora,
        "file": dict(file_ref, originale=True),
        "riconosciuto": riconosciuto or {},
        "classificazione": dict(proposta or {}),
        "conferma": {"stato": "confermato", "da": utente, "il": ora, "modificati": modificati, "bene_proposto": (proposta or {}).get("bene_id") or ""},
    })
    doc["titolo"] = doc["titolo"] or " ".join(x for x in (doc["tipo"], doc["marca"], doc["modello"]) if x) or (file_ref.get("nome") or "Documento")
    c.setdefault("documenti", []).append(doc)
    return doc


def ca_correggi_documento(c, did, finale, utente, ora):
    """Corregge i dati di un documento già archiviato: l'originale, i dati riconosciuti e la proposta automatica restano com'erano; si aggiorna solo la conferma."""
    d = next((x for x in c.get("documenti", []) if x.get("id") == did), None)
    if d is None:
        return None
    fin = _ca_pulisci(finale, _CAMPI_DOC)
    campi_prop = {k: (v.get("valore") if isinstance(v, dict) else v) for k, v in ((d.get("riconosciuto") or {}).get("campi") or {}).items()}
    d.update({k: fin[k] for k in _CAMPI_DOC if k in fin})
    d["titolo"] = d["titolo"] or " ".join(x for x in (d["tipo"], d["marca"], d["modello"]) if x) or (d.get("file") or {}).get("nome", "Documento")
    conf = d.setdefault("conferma", {})
    conf.update({"stato": "confermato", "da": utente, "il": ora, "modificati": [k for k in _CAMPI_CONTROLLATI if str(campi_prop.get(k) or "") != d.get(k, "")]})
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
    return {"garanzie": sorted(garanzie, key=lambda x: x[1]), "manutenzioni": sorted(manut, key=lambda x: x[2])}


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


def _ca_riga_documento(d, beni_nomi, pre=""):
    """Un documento in elenco: dati, apri/scarica, invia, correggi, elimina."""
    f = d.get("file") or {}
    st.markdown(f"<div class='ca-card'><b>📄 {_ca_testo(d.get('titolo'))}</b><br>"
                + _ca_chip(_ca_testo(d.get("tipo") or "Documento")) + (_ca_chip("🏠 " + _ca_testo(beni_nomi.get(d.get("bene_id"), "")), "ca-ok") if beni_nomi.get(d.get("bene_id")) else _ca_chip("non collegato", "ca-scaduta"))
                + "<br><span style='font-size:.85rem'>" + " · ".join(x for x in (_ca_testo(d.get("marca")), _ca_testo(d.get("modello")), ("S/N " + _ca_testo(d.get("seriale"))) if d.get("seriale") else "",
                                                                                   _ca_data_it(d.get("data_doc")), CA_LINGUE.get(d.get("lingua"), "")) if x) + "</span></div>", unsafe_allow_html=True)
    k = f"{pre}{d['id']}"
    b1, b2, b3 = st.columns(3, gap="small")
    caricato = _ca_leggi_file(f) if f.get("id") else []
    if caricato:
        nome, mime, dati = caricato[0]
        b1.download_button("⬇ Apri / scarica", dati, file_name=nome, mime=mime, key=f"ca_dl_{k}", width="stretch")
    elif d.get("link"):
        b1.link_button("🔗 Apri il link", d["link"], width="stretch")
    if b2.button("✏️ Correggi", key=f"ca_cor_{k}", width="stretch"):
        st.session_state["ca_correggi"] = d["id"]
        st.rerun()
    if b3.button("🗑️ Elimina", key=f"ca_del_{k}", width="stretch"):
        st.session_state["ca_elimina_doc"] = d["id"]
        st.rerun()
    if caricato and caricato[0][1].startswith("image/"):
        st.image(caricato[0][2], width="stretch")
    if "_fa_inv_voce" in globals() and caricato:
        _fa_inv_voce(f"casa_{k}", "📤 Invia questo documento (email, WhatsApp…)", f"📄 {d.get('titolo', 'Documento')}",
                     [("Tipo", d.get("tipo")), ("Marca", d.get("marca")), ("Modello", d.get("modello")), ("Numero di serie", d.get("seriale"))], [f])
    conf = d.get("conferma") or {}
    if conf:
        st.caption(f"Confermato da {conf.get('da', '')} il {_ca_data_it(conf.get('il'))}" + (f" · corretti: {', '.join(conf['modificati'])}" if conf.get("modificati") else " · nessuna correzione"))


def _ca_form_documento(chiave, d, beni, riconosciuto=None, proposta_bene=None, motivi=None):
    """Il modulo «Controlla e conferma» (anche per correggere). Ritorna (inviato, valori)."""
    campi = (riconosciuto or {}).get("campi") or {}
    val = lambda k: (d or {}).get(k) if d else (campi.get(k) or {}).get("valore", "")
    def aff(k):
        c = campi.get(k) or {}
        return f" {_CA_AFF.get(c.get('affidabilita'), '')}" if c and not d else ""
    with st.form(chiave, border=False):
        tipo_v = val("tipo") if val("tipo") in CA_TIPI else "Manuale d'uso"
        tipo = st.selectbox("Che documento è" + aff("tipo"), CA_TIPI, index=CA_TIPI.index(tipo_v))
        cats = list(CA_CATEGORIE)
        cat = st.selectbox("Categoria" + aff("categoria"), cats, index=cats.index(val("categoria")) if val("categoria") in cats else len(cats) - 1)
        sotto = st.text_input("Che apparecchio è" + aff("sottocategoria"), value=val("sottocategoria") or "")
        c1, c2 = st.columns(2)
        marca = c1.text_input("Marca" + aff("marca"), value=val("marca") or "")
        modello = c2.text_input("Modello" + aff("modello"), value=val("modello") or "")
        seriale = st.text_input("Numero di serie" + aff("seriale"), value=val("seriale") or "")
        c3, c4 = st.columns(2)
        data_doc = c3.date_input("Data del documento" + aff("data_doc"), value=_data(val("data_doc")), format="DD/MM/YYYY")
        lingue = list(CA_LINGUE)
        lingua = c4.selectbox("Lingua" + aff("lingua"), lingue, index=lingue.index(val("lingua")) if val("lingua") in lingue else lingue.index(""), format_func=lambda x: CA_LINGUE[x])
        opz = ["__nuovo__", ""] + [b["id"] for b in beni]
        nomi = {b["id"]: f"{b.get('nome', '')} ({b.get('marca', '')} {b.get('modello', '')})".replace("( )", "").strip() for b in beni}
        corrente = (d or {}).get("bene_id") if d else (proposta_bene or "__nuovo__")
        etic = {"__nuovo__": "➕ Crea un nuovo bene con questi dati", "": "— Non collegare a nessun bene —"}
        bene = st.selectbox("Collega a questo bene" + (f" ({', '.join(motivi)})" if motivi and not d and proposta_bene else ""), opz, index=opz.index(corrente) if corrente in opz else 1,
                            format_func=lambda x: etic.get(x) or nomi.get(x, x))
        titolo = st.text_input("Titolo", value=(d or {}).get("titolo", "") if d else "", placeholder="se lo lasci vuoto lo scrivo io")
        link = st.text_input("Link al manuale online (facoltativo)", value=(d or {}).get("link", "") if d else "")
        note = st.text_input("Note (facoltative)", value=(d or {}).get("note", "") if d else "")
        ok = st.form_submit_button("✅ Conferma e archivia" if not d else "💾 Salva le correzioni", type="primary", width="stretch")
    return ok, {"tipo": tipo, "categoria": cat, "sottocategoria": sotto, "marca": marca, "modello": modello, "seriale": seriale, "data_doc": data_doc, "lingua": lingua,
                "bene_id": bene, "titolo": titolo, "link": link, "note": note}


def _ca_tab_manuali(c):
    beni = c.get("beni", [])
    nomi = {b["id"]: b.get("nome", "") for b in beni}
    st.markdown("#### ➕ Archivia un manuale o un documento")
    st.caption("Carica un PDF, una foto o una scansione: leggo il documento e ti propongo tipo, apparecchio, marca, modello e numero di serie. "
               "**Il file resta com'è**, e prima di archiviare controlli e confermi tu.")
    n = st.session_state.get("ca_giro", 0)
    up = st.file_uploader("PDF, foto o scansione", type=["pdf", "jpg", "jpeg", "png", "webp"], key=f"ca_up_{n}", label_visibility="collapsed")
    with st.expander("🔗 …oppure prendi il manuale da un link"):
        url = st.text_input("Indirizzo del PDF", key=f"ca_url_{n}", placeholder="https://…/manuale.pdf")
        if st.button("⬇ Scarica e leggi", key=f"ca_url_btn_{n}") and url.strip():
            if "_fa_scarica_pdf" in globals():
                with st.spinner("Scarico il PDF…"):
                    f, errore = _fa_scarica_pdf(url.strip(), "Manuale")
                if f is None:
                    st.error("Non riesco: " + str(errore))
                else:
                    st.session_state["ca_bozza_in"] = {"nome": f.name, "mime": "application/pdf", "dati": f.getvalue() if hasattr(f, "getvalue") else f.dati, "link": url.strip()}
                    st.rerun()
    sorgente = None
    if up is not None:
        sorgente = {"nome": up.name, "mime": up.type or "application/octet-stream", "dati": up.getvalue(), "link": ""}
    elif st.session_state.get("ca_bozza_in"):
        sorgente = st.session_state["ca_bozza_in"]
    if sorgente:
        if sorgente["mime"] not in _CA_MIME:
            st.error("Questo tipo di file non è ammesso: carica un PDF o una foto (JPG, PNG, WebP).")
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
                bozza = {"sha": sha, "ric": ric, "bene": bene_id, "motivi": motivi}
                st.session_state["ca_bozza"] = bozza
            ric = bozza["ric"]
            if ric["info"].get("scansione"):
                st.warning("Questo PDF è una **scansione** (immagini senza testo): non riesco a leggerlo da solo. Compila tu i dati qui sotto, oppure carica una foto di una pagina con i dati.")
            elif not ric["testo_ok"]:
                st.info("Non sono riuscito a leggere testo dal file: controlla e completa tu i dati qui sotto.")
            else:
                st.success("Ho letto il documento. I pallini mostrano quanto sono sicuro: 🟢 alta, 🟡 media, 🟠 bassa. **Controlla e correggi** quello che serve.")
            if sorgente["mime"].startswith("image/"):
                st.image(sorgente["dati"], width=240)
            ok, val = _ca_form_documento("ca_form_nuovo", None, beni, ric, bozza.get("bene"), bozza.get("motivi"))
            c1, c2 = st.columns(2)
            if c2.button("✖ Scarta", key="ca_scarta", width="stretch"):
                st.session_state["ca_giro"] = n + 1
                st.session_state.pop("ca_bozza", None)
                st.session_state.pop("ca_bozza_in", None)
                st.rerun()
            if ok:
                try:
                    nid = uuid.uuid4().hex[:12]
                    _ca_scrivi_file(nid, sorgente["nome"], sorgente["mime"], sorgente["dati"])              # 1) l'originale, intatto
                    ora, utente = _ca_ora(), (st.session_state.get("sess") or {}).get("nome", "")
                    rif = {"id": nid, "nome": sorgente["nome"], "mime": sorgente["mime"], "sha256": sha, "dimensione": len(sorgente["dati"])}
                    proposta = {k: (ric["campi"].get(k) or {}).get("valore", "") for k in ("tipo", "categoria", "sottocategoria")}
                    proposta["bene_id"] = bozza.get("bene") or ""

                    def _fn(cc, val=val, ora=ora, utente=utente, rif=rif, proposta=proposta, ric=ric, sorg=sorgente):
                        v = dict(val)
                        if v["bene_id"] == "__nuovo__":                                                     # nuovo bene dai dati confermati
                            nb = ca_nuovo_bene(cc, {"nome": " ".join(x for x in (v["sottocategoria"], v["marca"], v["modello"]) if x) or v["titolo"] or "Nuovo bene", "categoria": v["categoria"],
                                                    "sottocategoria": v["sottocategoria"], "marca": v["marca"], "modello": v["modello"], "seriale": v["seriale"]}, ora)
                            v["bene_id"] = nb["id"]
                        v["link"] = v["link"] or sorg.get("link", "")
                        ca_aggiungi_documento(cc, rif, ric, proposta, v, utente, ora)
                    _ca_salva(_fn, "Casa: documento archiviato")
                    st.session_state["ca_giro"] = n + 1
                    st.session_state.pop("ca_bozza", None)
                    st.session_state.pop("ca_bozza_in", None)
                    st.session_state["messaggio"] = "✅ Documento archiviato, con il file originale."
                    st.rerun()
                except Exception as e:
                    st.error(f"Non sono riuscito a salvare: {e}")
    # ---- correzione e cancellazione
    cid = st.session_state.get("ca_correggi")
    if cid:
        d = next((x for x in c.get("documenti", []) if x["id"] == cid), None)
        if d:
            st.markdown(f"##### ✏️ Correggi: {_ca_testo(d.get('titolo'))}")
            ok, val = _ca_form_documento(f"ca_form_cor_{cid}", d, beni)
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
    # ---- elenco
    docs = c.get("documenti", [])
    st.divider()
    if not docs:
        st.info("Non hai ancora archiviato nessun documento. Carica qui sopra il primo manuale.")
        return
    st.markdown(f"#### 📚 I tuoi documenti ({len(docs)})")
    cerca = st.text_input("Cerca", key="ca_cerca", placeholder="nome, marca, modello, numero di serie…", label_visibility="collapsed")
    f1, f2 = st.columns(2, gap="small")
    ftipo = f1.selectbox("Tipo", [""] + CA_TIPI, format_func=lambda x: x or "📑 Tutti i tipi", key="ca_ftipo")
    fbene = f2.selectbox("Bene", ["", "__nessuno__"] + [b["id"] for b in beni], format_func=lambda x: "🏠 Tutti i beni" if not x else "non collegati" if x == "__nessuno__" else nomi.get(x, x), key="ca_fbene")
    q = _ca_norm(cerca)
    for d in sorted(docs, key=lambda x: x.get("creato_il", ""), reverse=True):
        if ftipo and d.get("tipo") != ftipo:
            continue
        if fbene == "__nessuno__" and d.get("bene_id"):
            continue
        if fbene and fbene != "__nessuno__" and d.get("bene_id") != fbene:
            continue
        if q and q not in _ca_norm(" ".join(str(d.get(k) or "") for k in ("titolo", "marca", "modello", "seriale", "tipo", "sottocategoria", "note", "categoria"))):
            continue
        _ca_riga_documento(d, nomi, "m")


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
        st.caption("Nessun documento collegato: caricane uno nella scheda «Manuali» e scegli questo bene.")
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
    t1, t2, t3 = st.tabs(["🏠 Beni", "📚 Manuali", "🔧 Manutenzioni"])
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
         """La sezione **Casa** raccoglie **i beni della tua casa** (caldaia, climatizzatori, elettrodomestici, TV, allarmi, impianti), **i loro manuali e documenti** e **le manutenzioni**.
Ha tre schede in basso: **🏠 Beni**, **📚 Manuali**, **🔧 Manutenzioni**.
Si apre dall'icona della casa in Home, oppure con le frecce ← → in alto.""",
         "casa abitazione beni inventario caldaia lavatrice manuali manutenzioni sezione"),
        ("📚 Archiviare un manuale",
         """1. Apri **Casa** e tocca la scheda **📚 Manuali**.
2. In **Archivia un manuale o un documento** carica un **PDF**, una **foto** o una **scansione** (massimo 8 MB), oppure usa **🔗 prendi il manuale da un link**.
3. Leggo il documento e ti propongo **tipo, categoria, apparecchio, marca, modello, numero di serie, data e lingua**. I pallini dicono quanto sono sicuro: 🟢 alta, 🟡 media, 🟠 bassa.
4. **Controlla e correggi** quello che non va, scegli a quale **bene** collegarlo (o crea un nuovo bene) e tocca **✅ Conferma e archivia**.

Il **file originale resta com'è**, identico. Se il PDF è una scansione senza testo, compili tu i dati.""",
         "archiviare manuale manuali caricare pdf foto scansione riconoscimento marca modello numero di serie conferma"),
        ("🏠 Aggiungere e collegare un bene",
         """In **🏠 Beni** tocca **➕ Aggiungi un bene** e compila nome, categoria, marca, modello, numero di serie, dove si trova, data di acquisto e garanzia.
Tocca **📂 Apri la scheda** per vedere **tutti i documenti collegati** (li apri o li scarichi da lì), lo **storico delle manutenzioni** e collegare un documento già archiviato.
Puoi **modificare** o **eliminare** il bene: scegli se tenere o eliminare i suoi documenti.""",
         "bene beni inventario aggiungere collegare garanzia scheda caldaia documenti collegati"),
        ("🔧 Registrare una manutenzione",
         """In **🔧 Manutenzioni** tocca **➕ Registra una manutenzione o un intervento**: scegli il bene, la data, cosa è stato fatto, la ditta, il costo e, se vuoi, il **prossimo controllo**.
In cima alla pagina Casa compaiono gli avvisi di **garanzie** in scadenza e **manutenzioni** in arrivo o in ritardo.""",
         "manutenzione intervento controllo caldaia tecnico ditta prossimo controllo scadenza garanzia"),
        ("✏️ Correggere o eliminare un documento",
         """Nell'elenco dei documenti tocca **✏️ Correggi** per cambiare tipo, categoria, marca, modello, bene collegato e il resto: l'originale e i dati letti dal programma restano com'erano.
Tocca **🗑️ Elimina** per toglierlo (ti chiedo conferma). **📤 Invia** lo manda per email, WhatsApp o Telegram.""",
         "correggere modificare eliminare cancellare documento manuale inviare condividere"),
    ])
    _ID_GUIDA.setdefault("casa", ["c_cosa", "c_manuali", "c_beni", "c_manutenzioni", "c_correggi"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("casa", "c_cosa")

def casa_pulsante():
    """L'icona di Casa nella riga della Home, tra «I miei documenti» e «Utilità» (la chiama un piccolo aggancio in icona_farmacia). Ritorna True se è stata toccata.
    Le quattro icone stanno tutte sulla stessa riga: per questo qui si rimpiccioliscono un po' (80 px) e si regola la scritta degli avvisi sotto «I miei documenti»."""
    uri_c = _fa_file_uri("casa.webp") if "_fa_file_uri" in globals() else ""
    if not uri_c:
        return False
    sc = ca_scadenze(_ca_dati(), oggi())
    n_av = len(sc["garanzie"]) + len(sc["manutenzioni"])
    st.markdown("<style>@keyframes ca-battito{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.25))}"
                "50%{transform:scale(1.06);filter:drop-shadow(0 0 14px rgba(255,193,7,.95))}}"
                + _css_icona("casa_icona", uri_c, "1/1", "ca-battito", 2.4, 80)
                + ".st-key-azioni_icone .st-key-fa_icona button,.st-key-azioni_icone .st-key-doc_icona button,.st-key-azioni_icone .st-key-ut_icona button,"
                  ".st-key-azioni_icone .st-key-casa_icona button{width:80px}"
                  ".st-key-azioni_icone div[style*='width:112px']{width:80px !important;font-size:.6rem !important}</style>", unsafe_allow_html=True)
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
