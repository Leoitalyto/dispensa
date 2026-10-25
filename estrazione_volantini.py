# -*- coding: utf-8 -*-
"""Lettura dei volantini PDF: trova prodotto + prezzo usando la POSIZIONE delle parole sulla pagina
(nei PDF dei volantini i nomi e i prezzi sono spesso in blocchi separati, quindi il testo "in fila" non basta).
Modulo senza Streamlit: lo usa l'app e puo' essere usato anche da uno script automatico.
I risultati sono SEMPRE da controllare prima di salvarli: i volantini sono impaginati in mille modi."""
import io
import re
from datetime import date

CATENE_NOTE = {
    "Coop": "Supermercato", "Conad": "Supermercato", "Carrefour": "Supermercato", "Esselunga": "Supermercato", "Pam": "Supermercato",
    "Despar": "Supermercato", "Eurospar": "Supermercato", "Famila": "Supermercato", "Iperal": "Supermercato", "Tigros": "Supermercato",
    "Simply": "Supermercato", "Sigma": "Supermercato", "Crai": "Supermercato", "Gros Cido": "Supermercato", "DOK": "Supermercato",
    "Ipercoop": "Ipermercato", "Interspar": "Ipermercato", "Bennet": "Ipermercato", "Il Gigante": "Ipermercato", "Panorama": "Ipermercato",
    "Lidl": "Discount", "Eurospin": "Discount", "MD": "Discount", "Aldi": "Discount", "Penny": "Discount", "Todis": "Discount",
    "Tuodì": "Discount", "Dpiù": "Discount", "In's": "Discount",
}
_MESI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
         "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}
_RE_PREZZO = re.compile(r"^(\d{1,3}[.,]\d{2})€?$")
_ESCLUDI = ("prezzi validi", "non tutte le referenze", "scopri le offerte", "volantino", "www.", "orari", "telefono", "servizio filo",
            "disegni, fotografie", "salvo esaurimento", "scarica", "inquadra", "seguici", "punto vendita", "depliant", "provincia di",
            "ogni giorno il meglio", "carta fedelt", "offerta valida", "valida dal", "validi dal", "tutti i diritti", "p.iva")
_PAROLE_RUMORE = {"conviene", "sconto", "%", "vale", "bollino", "bollini", "coppia", "da", "non", "perdere", "la", "novità", "novita",
                  "sottocosto", "solo", "con", "carta", "app", "esclusivo", "prezzo", "speciale", "confezione", "offerta"}
_CATEGORIE = [
    ("Pasta e riso", ("pasta", "spaghetti", "penne", "fusilli", "riso", "gnocchi", "tortellini", "ravioli", "farfalle", "maccheroni")),
    ("Latticini e uova", ("latte", "yogurt", "burro", "mozzarella", "formaggio", "formaggini", "parmigiano", "grana", "gorgonzola", "ricotta", "panna", "uova", "stracchino", "brie")),
    ("Carne e salumi", ("pollo", "manzo", "vitello", "suino", "maiale", "macinato", "salsiccia", "prosciutto", "salame", "salumi", "bresaola", "pancetta", "wurstel", "tacchino", "fettine", "scaloppe", "lonza", "mortadella", "speck")),
    ("Pesce", ("tonno", "salmone", "pesce", "merluzzo", "gamberi", "sgombri", "acciughe", "trance", "orata", "branzino")),
    ("Frutta e verdura", ("mele", "pere", "arance", "banane", "clementine", "limoni", "kiwi", "uva", "insalata", "pomodori", "patate", "carote", "finocchi", "zucchine", "cipolle", "frutta", "verdura", "taccole", "friarielli")),
    ("Pane e dolci", ("pane", "pan ", "biscotti", "merenda", "merendine", "crackers", "fette biscottate", "cioccolato", "torta", "brioss", "nutella", "snack", "focaccia", "gelato", "dolce", "kinder")),
    ("Bevande", ("acqua", "birra", "vino", "spumante", "prosecco", "succo", "aranciata", "cola", "tè", "the ", "energade", "limoncello", "amaro", "liquore", "bibita", "gassosa")),
    ("Caffè e colazione", ("caffè", "caffe", "cialde", "capsule", "cereali", "marmellata", "miele", "cappuccino")),
    ("Dispensa", ("olio", "aceto", "passata", "pelati", "sugo", "farina", "zucchero", "sale", "legumi", "fagioli", "ceci", "lenticchie", "scatolame", "polpa", "conserva", "pesto", "maionese", "ketchup")),
    ("Surgelati", ("surgelat", "findus", "orogel", "bastoncini")),
    ("Casa e pulizia", ("detersivo", "ammorbidente", "lavastoviglie", "lavatrice", "pavimenti", "sgrassatore", "carta igienica", "scottex", "tovaglioli", "spugne", "candeggina", "pulitore", "sacchetti")),
    ("Igiene e cura persona", ("shampoo", "balsamo", "bagnodoccia", "dentifricio", "deodorante", "assorbenti", "sapone", "salviettine", "pannolini", "rasoi", "crema")),
    ("Animali", ("cane", "gatto", "crocchette", "lettiera", "croccantini")),
]


def indovina_categoria(nome):
    n = (nome or "").lower() + " "
    for cat, chiavi in _CATEGORIE:
        if any(k in n for k in chiavi):
            return cat
    return "Altro"


def _num(txt):
    return float(txt.replace(",", "."))


def _estrai_date(testo):
    """Cerca 'dal 8 al 21 gennaio 2026' e simili. Ritorna (dal, al) come date oppure (None, None)."""
    t = (testo or "").lower().replace("’", "'")
    anno_default = None
    m = re.search(r"\b(20\d{2})\b", t)
    if m:
        anno_default = int(m.group(1))
    mesi = "|".join(_MESI)
    m = re.search(rf"dal(?:l')?\s*(\d{{1,2}})\s*({mesi})?\s*al(?:l')?\s*(\d{{1,2}})\s*({mesi})(?:\s*(20\d{{2}}))?", t)
    try:
        if m:
            g1, m1, g2, m2, a = m.groups()
            anno = int(a) if a else anno_default or date.today().year
            mese2 = _MESI[m2]
            mese1 = _MESI[m1] if m1 else mese2
            anno1 = anno - 1 if mese1 > mese2 else anno
            return date(anno1, mese1, int(g1)), date(anno, mese2, int(g2))
        m = re.search(r"dal(?:l')?\s*(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?\s*al(?:l')?\s*(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?", t)
        if m:
            g1, mm1, a1, g2, mm2, a2 = m.groups()
            anno2 = int(a2) + (2000 if a2 and int(a2) < 100 else 0) if a2 else anno_default or date.today().year
            anno1 = (int(a1) + (2000 if int(a1) < 100 else 0)) if a1 else (anno2 - 1 if int(mm1) > int(mm2) else anno2)
            return date(anno1, int(mm1), int(g1)), date(anno2, int(mm2), int(g2))
    except (ValueError, KeyError):
        pass
    return None, None


def _indovina_negozio(testo):
    t = (testo or "")
    migliore, punti = "", 0
    for nome in CATENE_NOTE:
        n = len(re.findall(r"\b" + re.escape(nome) + r"\b", t, flags=re.I))
        if n > punti:
            migliore, punti = nome, n
    return migliore


def _righe(parole):
    """Raggruppa le parole in righe (stessa altezza)."""
    parole = sorted(parole, key=lambda w: (w["top"], w["x0"]))
    righe = []
    for w in parole:
        for r in righe:
            if abs(r["top"] - w["top"]) <= max(2.0, 0.45 * r["size"]) and w["x0"] >= r["x0"] - 2:
                r["parole"].append(w)
                r["top"] = min(r["top"], w["top"])
                r["bottom"] = max(r["bottom"], w["bottom"])
                r["x1"] = max(r["x1"], w["x1"])
                r["size"] = max(r["size"], w.get("size", 8))
                break
        else:
            righe.append({"parole": [w], "top": w["top"], "bottom": w["bottom"], "x0": w["x0"], "x1": w["x1"], "size": w.get("size", 8)})
    # una riga che attraversa piu' colonne va spezzata dove c'e' un grande vuoto tra le parole
    spezzate = []
    for r in righe:
        r["parole"].sort(key=lambda w: w["x0"])
        gruppo = [r["parole"][0]]
        for w in r["parole"][1:]:
            if w["x0"] - gruppo[-1]["x1"] > max(16.0, 1.6 * r["size"]):
                spezzate.append(gruppo)
                gruppo = [w]
            else:
                gruppo.append(w)
        spezzate.append(gruppo)
    risultato = []
    for g in spezzate:
        risultato.append({"parole": g, "top": min(w["top"] for w in g), "bottom": max(w["bottom"] for w in g),
                          "x0": g[0]["x0"], "x1": max(w["x1"] for w in g), "size": max(w.get("size", 8) for w in g),
                          "testo": " ".join(w["text"] for w in g).strip()})
    return risultato


def _blocchi(righe):
    """Unisce le righe vicine e sovrapposte in orizzontale in blocchi di testo (un prodotto = un blocco)."""
    blocchi = []
    for r in sorted(righe, key=lambda r: (r["top"], r["x0"])):
        alt = max(6.0, r["bottom"] - r["top"])
        for b in blocchi:
            gap = r["top"] - b["bottom"]
            sovrapp = min(r["x1"], b["x1"]) - max(r["x0"], b["x0"])
            if -2 <= gap <= 1.1 * alt and (sovrapp > 0.2 * min(r["x1"] - r["x0"], b["x1"] - b["x0"]) or abs(r["x0"] - b["x0"]) < 25):
                b["righe"].append(r)
                b["bottom"] = max(b["bottom"], r["bottom"])
                b["x0"], b["x1"] = min(b["x0"], r["x0"]), max(b["x1"], r["x1"])
                break
        else:
            blocchi.append({"righe": [r], "top": r["top"], "bottom": r["bottom"], "x0": r["x0"], "x1": r["x1"]})
    return blocchi


def _maiuscole(txt):
    lettere = [c for c in txt if c.isalpha()]
    return (sum(1 for c in lettere if c.isupper()) / len(lettere)) if lettere else 0.0


def _prezzi_pagina(parole):
    """Trova i prezzi della pagina e dice quali sono 'al kg / al lt / all'etto' (da scartare)."""
    ordinate = sorted(parole, key=lambda w: (round(w["top"] / 3), w["x0"]))
    prezzi = []
    for i, w in enumerate(ordinate):
        m = _RE_PREZZO.match(w["text"].replace(" ", ""))
        if not m:
            continue
        stessa = [x for x in ordinate if abs(x["top"] - w["top"]) <= 3 and x is not w]
        dopo = " ".join(x["text"] for x in sorted(stessa, key=lambda x: x["x0"]) if x["x0"] > w["x0"])[:25].lower().replace("’", "'")
        prima = " ".join(x["text"] for x in sorted(stessa, key=lambda x: x["x0"]) if x["x1"] <= w["x0"] + 1)[-14:].lower()
        unit = bool(re.match(r"^€?\s*\(?(al|all'|/)\s*(kg|lt|l|etto|hg|100)", dopo)) or bool(re.search(r"\(\s*al\s*(kg|lt|l)\s*$", prima)) \
            or bool(re.search(r"\bal\s*(kg|lt|l)\s*$", prima))
        prezzi.append({"valore": _num(m.group(1)), "x": (w["x0"] + w["x1"]) / 2, "top": w["top"], "bottom": w["bottom"],
                       "size": w.get("size", 8), "unit": unit, "usato": False})
    return prezzi


def estrai_pagina(pagina):
    parole = pagina.extract_words(extra_attrs=["size"], keep_blank_chars=False, use_text_flow=False)
    if not parole:
        return [], ""
    righe = _righe(parole)
    prezzi = _prezzi_pagina(parole)
    blocchi = []
    for b in _blocchi(righe):
        testi = [r["testo"] for r in b["righe"]]
        prima = testi[0]
        tutto = " ".join(testi)
        low = tutto.lower().replace("’", "'")
        if any(x in low for x in _ESCLUDI) or re.search(r"\b(iva|p\.iva)\b", low):
            continue
        if _RE_PREZZO.search(prima) or _maiuscole(prima) < 0.6 or len(prima) < 3:
            continue
        # tolgo parole di rumore (CONVIENE, SCONTO, VALE BOLLINO...) dalle righe del nome
        pulite = []
        for r in b["righe"]:
            parole_r = [w["text"] for w in r["parole"] if w["text"].lower().strip(",.") not in _PAROLE_RUMORE
                        and not _RE_PREZZO.match(w["text"]) and w["text"] != "€"]
            riga = " ".join(parole_r).strip()
            if riga and not re.fullmatch(r"[\d\s%.,-]+", riga):          # via le righe fatte solo di numeri (es. "50")
                pulite.append(riga)
        if not pulite or _maiuscole(pulite[0]) < 0.6:
            continue
        b["nome_righe"] = pulite
        blocchi.append(b)
    # associo a ogni blocco il prezzo (non "al kg") piu' vicino, sotto o accanto
    coppie = []
    for bi, b in enumerate(blocchi):
        for pi, p in enumerate(prezzi):
            if p["unit"]:
                continue
            dy = p["top"] - b["bottom"]
            if dy < -25 or dy > 260:
                continue
            dx = 0 if b["x0"] - 50 <= p["x"] <= b["x1"] + 90 else min(abs(p["x"] - b["x0"]), abs(p["x"] - b["x1"]))
            if dx > 90:
                continue
            coppie.append((max(dy, 0) + 0.7 * dx + (8 if dy < 0 else 0), bi, pi))
    coppie.sort()
    risultati, usati_b = [], set()
    for _, bi, pi in coppie:
        if bi in usati_b or prezzi[pi]["usato"]:
            continue
        p = prezzi[pi]
        # altri prezzi vicini (prezzo prima dello sconto, prezzo all'etto...) fanno parte dello stesso gruppo
        gruppo = [p]
        for pj, q in enumerate(prezzi):
            if pj != pi and not q["unit"] and not q["usato"] and abs(q["x"] - p["x"]) < 95 and abs(q["top"] - p["top"]) < 60:
                gruppo.append(q)
        finale = max(gruppo, key=lambda q: (round(q["size"]), -q["top"]))
        prima = max((q["valore"] for q in gruppo if q["valore"] > finale["valore"] * 1.02), default=None)
        for q in gruppo:
            q["usato"] = True
        usati_b.add(bi)
        b = blocchi[bi]
        righe_nome = b["nome_righe"]
        nome = " ".join(r for r in righe_nome if _maiuscole(r) >= 0.6)
        dettaglio = " ".join(r for r in righe_nome if _maiuscole(r) < 0.6)
        formato = ""
        mf = re.search(r"(\d+\s*[x×]\s*\d+(?:[.,]\d+)?\s*(?:g|kg|ml|cl|lt|l)\b|\d+(?:[.,]\d+)?\s*(?:g|kg|ml|cl|lt|l|pezzi|pz|lavaggi)\b)", " ".join(righe_nome), re.I)
        if mf:
            formato = mf.group(1).strip()
        risultati.append({"nome": nome.title().replace("D.O.P.", "D.O.P.").strip(), "dettaglio": dettaglio.strip(" ,"), "formato": formato,
                          "prezzo": finale["valore"], "prezzo_prima": prima, "pos": (round(b["top"]), round(b["x0"]))})
    risultati.sort(key=lambda r: (r["pos"][0] // 120, r["pos"][1]))
    testo = " ".join(w["text"] for w in parole)
    return risultati, testo


def estrai_volantino(dati_pdf, massimo_pagine=60):
    """Legge un volantino PDF. Ritorna un dizionario: offerte (da controllare), date, negozio probabile, pagine, avvisi."""
    import pdfplumber
    offerte, testo_tot, avvisi = [], [], []
    with pdfplumber.open(io.BytesIO(dati_pdf)) as pdf:
        pagine = pdf.pages[:massimo_pagine]
        if len(pdf.pages) > massimo_pagine:
            avvisi.append(f"Ho letto solo le prime {massimo_pagine} pagine.")
        for n, pag in enumerate(pagine, 1):
            try:
                ris, testo = estrai_pagina(pag)
            except Exception as e:                       # una pagina strana non deve bloccare tutto
                avvisi.append(f"Pagina {n}: non riesco a leggerla ({type(e).__name__}).")
                continue
            for r in ris:
                r["pagina"] = n
            offerte.extend(ris)
            testo_tot.append(testo)
    testo_unico = " ".join(testo_tot)
    dal, al = _estrai_date(testo_unico)
    negozio = _indovina_negozio(testo_unico)
    for o in offerte:
        o["categoria"] = indovina_categoria(o["nome"] + " " + o.get("dettaglio", ""))
    # tolgo i doppioni identici (stesso nome e prezzo)
    visti, uniche = set(), []
    for o in offerte:
        k = (o["nome"].lower(), o["prezzo"])
        if k not in visti:
            visti.add(k)
            uniche.append(o)
    if not uniche:
        avvisi.append("Non ho trovato prodotti con prezzo: se il PDF è una foto (scansione) il testo non si legge. Puoi inserire le offerte a mano.")
    return {"offerte": uniche, "dal": dal.isoformat() if dal else None, "al": al.isoformat() if al else None, "negozio": negozio,
            "tipo": CATENE_NOTE.get(negozio, ""), "pagine": len(pagine), "avvisi": avvisi}


# ---------------------------------------------------------------------
# Scaricare i volantini e registrarli nell'archivio (usato dall'app e dallo script settimanale)
# ---------------------------------------------------------------------
import uuid as _uuid
from datetime import datetime as _dt, timedelta as _td
from urllib.parse import urljoin as _urljoin

_UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36",
       "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.5"}


def scarica_bytes(url, massimo=25_000_000, http=None):
    """Scarica un file (PDF o pagina). Ritorna i byte. Errore se e' troppo grande o la richiesta fallisce."""
    import requests
    http = http or requests
    r = http.get(url, headers=_UA, timeout=45, stream=True)
    r.raise_for_status()
    dati = bytearray()
    for pezzo in r.iter_content(65536):
        dati.extend(pezzo)
        if len(dati) > massimo:
            raise ValueError("Il file è troppo grande (oltre 25 MB).")
    return bytes(dati)


def trova_link_pdf(testo_html, url_base):
    """Cerca i link a PDF in una pagina. Mette prima quelli che sembrano volantini."""
    trovati = []
    for m in re.finditer(r"""(?:href|src|data-href|data-url)\s*=\s*["']([^"']+?\.pdf[^"']*)["']""", testo_html, flags=re.I):
        link = _urljoin(url_base, m.group(1).replace("&amp;", "&"))
        if link not in trovati:
            trovati.append(link)
    chiavi = ("volantin", "flyer", "offert", "promo", "leaflet")
    trovati.sort(key=lambda l: (0 if any(k in l.lower() for k in chiavi) else 1))
    return trovati


def leggi_fonte(url, http=None):
    """Da un indirizzo (PDF diretto o pagina che contiene il PDF) ai byte del PDF. Ritorna (byte, indirizzo_pdf)."""
    dati = scarica_bytes(url, http=http)
    if dati[:5] == b"%PDF-":
        return dati, url
    testo = dati.decode("utf-8", errors="ignore")
    link = trova_link_pdf(testo, url)
    if not link:
        raise ValueError("Nella pagina non ho trovato nessun PDF: serve il link diretto al volantino.")
    for l in link[:4]:
        try:
            pdf = scarica_bytes(l, http=http)
        except Exception:
            continue
        if pdf[:5] == b"%PDF-":
            return pdf, l
    raise ValueError("Ho trovato dei link ma nessuno era un PDF leggibile.")


def registra_volantino(dati, offerte, negozio, tipo, citta, dal, al, fonte="", utente="", oggi=None):
    """Mette un volantino e le sue offerte nel dizionario 'dati' (il contenuto di offerte.json). Sostituisce lo stesso volantino
    gia' presente (stesso negozio, citta' e date) e toglie le offerte scadute da piu' di 30 giorni. Ritorna quante offerte ha salvato."""
    oggi = oggi or date.today()
    limite = (oggi - _td(days=30)).isoformat()
    if al and al < limite:
        raise ValueError(f"Il volantino è scaduto il {al[8:10]}/{al[5:7]}/{al[:4]} (da più di 30 giorni): non lo salvo.")
    chiave = f"{negozio}|{citta}|{dal}|{al}".lower()
    dati["offerte"] = [o for o in dati.get("offerte", []) if o.get("chiave") != chiave]
    dati["volantini"] = [v for v in dati.get("volantini", []) if v.get("chiave") != chiave]
    vid = _uuid.uuid4().hex[:8]
    adesso = _dt.now().isoformat(timespec="seconds")
    n = 0
    for o in offerte:
        try:
            prezzo = float(o["prezzo"])
        except (KeyError, TypeError, ValueError):
            continue
        nome = (o.get("nome") or "").strip()
        if not nome or prezzo <= 0:
            continue
        prima = o.get("prezzo_prima")
        dati["offerte"].append({"id": _uuid.uuid4().hex[:10], "chiave": chiave, "volantino": vid, "nome": nome,
                                "dettaglio": (o.get("dettaglio") or "").strip(), "formato": (o.get("formato") or "").strip(),
                                "categoria": o.get("categoria") or "Altro", "prezzo": round(prezzo, 2),
                                "prezzo_prima": round(float(prima), 2) if prima else None, "negozio": negozio, "tipo": tipo,
                                "citta": citta, "dal": dal, "al": al, "fonte": fonte})
        n += 1
    dati["volantini"].append({"id": vid, "chiave": chiave, "negozio": negozio, "tipo": tipo, "citta": citta, "dal": dal, "al": al,
                              "n": n, "fonte": fonte, "importato_il": adesso, "importato_da": utente})
    dati["offerte"] = [o for o in dati["offerte"] if not o.get("al") or o["al"] >= limite]
    dati["volantini"] = [v for v in dati["volantini"] if not v.get("al") or v["al"] >= limite]
    return n


def registra_offerta_manuale(dati, o, negozio, tipo, citta, dal, al, utente="", oggi=None):
    """Aggiunge UNA offerta scritta a mano, senza toccare i volantini gia' importati."""
    oggi = oggi or date.today()
    dati.setdefault("offerte", []).append({
        "id": _uuid.uuid4().hex[:10], "chiave": "manuale|" + _uuid.uuid4().hex[:6], "volantino": "manuale", "nome": o["nome"].strip(),
        "dettaglio": "", "formato": (o.get("formato") or "").strip(), "categoria": o.get("categoria") or "Altro",
        "prezzo": round(float(o["prezzo"]), 2), "prezzo_prima": round(float(o["prezzo_prima"]), 2) if o.get("prezzo_prima") else None,
        "negozio": negozio, "tipo": tipo, "citta": citta, "dal": dal, "al": al, "fonte": "a mano", "inserita_da": utente})
    limite = (oggi - _td(days=30)).isoformat()
    dati["offerte"] = [x for x in dati["offerte"] if not x.get("al") or x["al"] >= limite]
