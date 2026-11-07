# -*- coding: utf-8 -*-
"""LETTORE DELLA CARTA DI CIRCOLAZIONE (formato europeo, Mod. MC 820 D e simili) — nuovo, molto più preciso del vecchio.

PERCHÉ LEGGEVA MALE: il libretto ha uno sfondo con un disegno antifalsificazione (linee sottili chiare) e il testo è battuto a macchina. Leggere tutta la pagina in un colpo mescolava le colonne e il disegno confondeva le lettere.
COME FA ORA:
 1. Toglie lo sfondo: il testo è molto più scuro del disegno, quindi si tiene solo ciò che è sotto una soglia di nero (poi si ripete con soglie diverse).
 2. Legge OGNI RIQUADRO (i 4 riquadri della pagina) e anche le due metà, così le colonne non si mescolano.
 3. Per ogni dato raccoglie le letture di tutte le prove e SCEGLIE PER VOTO. La targa compare in tutti e 4 i riquadri: sono 4 letture per ogni prova. Targa e telaio si correggono carattere per carattere e con le regole vere (targa = 2 lettere, 3 cifre, 2 lettere; telaio = 17 caratteri senza I, O, Q).
 4. La marca si corregge con l'elenco delle marche (CREVROGET → CHEVROLET).
 5. Dal retro legge i TIMBRI DELLE REVISIONI (data, scadenza, chilometri).
 6. (facoltativo) Se un'IA è attiva, rilegge le pagine e confronta: dove OCR e IA sono d'accordo il dato è «sicuro».
Ogni dato ha un'affidabilità (alta / media / bassa): i dati letti vanno SEMPRE controllati prima di salvare.
Caricato dopo auto_pagine.py."""
import base64
import difflib
import os
import io
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date

try:
    import cv2
    import numpy as np
except Exception:                                                        # senza OpenCV il vecchio lettore resta in uso
    cv2 = None
    np = None

_MARCHE_LB = ["ABARTH", "ALFA ROMEO", "ALPINE", "ASTON MARTIN", "AUDI", "AUSTIN", "BENTLEY", "BMW", "BYD", "CADILLAC", "CHEVROLET", "CHRYSLER", "CITROEN", "CUPRA", "DACIA", "DAEWOO", "DAIHATSU", "DODGE", "DR", "DS", "EVO",
              "FERRARI", "FIAT", "FORD", "GALLOPER", "HONDA", "HUMMER", "HYUNDAI", "INFINITI", "INNOCENTI", "ISUZU", "IVECO", "JAGUAR", "JEEP", "KIA", "LADA", "LAMBORGHINI", "LANCIA", "LAND ROVER", "LEXUS", "LOTUS", "MAHINDRA",
              "MASERATI", "MAZDA", "MERCEDES", "MERCEDES-BENZ", "MG", "MINI", "MITSUBISHI", "NISSAN", "OPEL", "PEUGEOT", "PIAGGIO", "PORSCHE", "RENAULT", "ROVER", "SAAB", "SEAT", "SKODA", "SMART", "SSANGYONG", "SUBARU", "SUZUKI",
              "TESLA", "TOYOTA", "VOLKSWAGEN", "VOLVO", "YAMAHA", "KAWASAKI", "KTM", "DUCATI", "APRILIA", "MOTO GUZZI", "TRIUMPH", "HARLEY-DAVIDSON", "BETA", "SCANIA", "MAN", "DAF", "RENAULT TRUCKS", "NEW HOLLAND", "FENDT",
              "CASE", "JOHN DEERE", "LANDINI", "MASSEY FERGUSON", "KUBOTA", "DEUTZ", "CLAAS", "PORSCHE", "SANTANA", "TATA", "GREAT WALL", "MAXUS", "LEVC", "POLESTAR", "LYNK", "XPENG", "NIO"]
_LETTERE_TARGA = set("ABCDEFGHJKLMNPRSTVWXYZ")                         # nelle targhe italiane non ci sono I, O, Q, U
_EURO_REG = {"692/2008": "Euro 5", "566/2011": "Euro 5", "459/2012": "Euro 6", "630/2012": "Euro 6", "143/2013": "Euro 6", "519/2013": "Euro 6", "2016/427": "Euro 6", "2016/646": "Euro 6", "2017/1151": "Euro 6", "2017/1154": "Euro 6",
             "715/2007": "Euro 4", "595/2009": "Euro VI", "582/2011": "Euro VI"}


# ---------------------------------------------------------------------------------------------------------------------
# immagini e OCR
# ---------------------------------------------------------------------------------------------------------------------
def lb_disponibile():
    return cv2 is not None and bool(shutil.which("tesseract"))


def _lingue():
    try:
        if "_doc_ocr_lingue" in globals():
            return _doc_ocr_lingue() or "eng"
    except Exception:
        pass
    try:
        r = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=15)
        return "ita+eng" if "ita" in r.stdout else "eng"
    except Exception:
        return "eng"


def lb_immagini(nome, mime, dati, dpi=300, max_pagine=4):
    """Le pagine come immagini OpenCV (BGR): da PDF (PyMuPDF) o da una foto."""
    if cv2 is None:
        return []
    out = []
    try:
        if str(mime).endswith("pdf") or str(nome).lower().endswith(".pdf"):
            import fitz
            doc = fitz.open(stream=dati, filetype="pdf")
            for p in list(doc)[:max_pagine]:
                pix = p.get_pixmap(dpi=dpi)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                out.append(cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_GRAY2BGR))
        else:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
            if max(im.size) > 3600:
                im.thumbnail((3600, 3600))
            out.append(cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR))
    except Exception:
        return []
    return out


def _tesseract(img, psm=6, tsv=False):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        nome = f.name
    try:
        cv2.imwrite(nome, img)
        r = subprocess.run(["tesseract", nome, "stdout", "-l", _lingue(), "--psm", str(psm), "-c", "preserve_interword_spaces=1"] + (["tsv"] if tsv else []), capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, OMP_THREAD_LIMIT="1"))         # un solo thread per processo: 3 volte più veloce, e si possono lanciare più processi insieme
        return r.stdout or ""
    except Exception:
        return ""
    finally:
        try:
            os.remove(nome)
        except Exception:
            pass


def _binaria(g, soglia):
    """Solo il testo: ciò che è più scuro della soglia (il disegno antifalsificazione è molto più chiaro)."""
    g = cv2.GaussianBlur(g, (3, 3), 0)
    return np.where(g < soglia, 0, 255).astype(np.uint8)


def _soglie(g):
    """Le soglie da provare: fisse (scansioni) e adattate alla luminosità della foto."""
    carta = float(np.percentile(g, 75))                                   # il «bianco» della carta
    rel = lambda k: int(max(80, min(190, carta * k)))
    return sorted({130, 150, rel(0.55), rel(0.65)})[:4]


_RIQUADRI = {"alto-sx": (0.02, 0.02, 0.53, 0.52), "alto-dx": (0.47, 0.02, 0.99, 0.52), "basso-sx": (0.02, 0.48, 0.53, 0.99), "basso-dx": (0.47, 0.48, 0.99, 0.99)}


def _conta_etichette(testo):
    return len(re.findall(r"\(\s*[A-Z]\s*(?:\.\s*\d)*\s*\)", testo.upper())) + (3 if "CIRCOLAZIONE" in testo.upper() else 0)


def _orienta_fronte(img):
    """Ruota la pagina finché si leggono le etichette «(A) (B) (C.2.1)…»: ritorna (immagine, quante etichette)."""
    migliore, punti = img, -1
    for rot in (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_180):
        r = img if rot is None else cv2.rotate(img, rot)
        g = cv2.cvtColor(r, cv2.COLOR_BGR2GRAY)
        s = 1100.0 / g.shape[1]
        p = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        n = _conta_etichette(_tesseract(_binaria(p, 150), 6))
        if n > punti:
            migliore, punti = r, n
        if n >= 8:                                                        # già dritta
            break
    return migliore, punti


def _ocr_passata(g, soglie):
    h, w = g.shape
    lavori = []
    for soglia in soglie:
        b = _binaria(g, soglia)
        for _nome, (x0, y0, x1, y1) in _RIQUADRI.items():
            lavori.append((b[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)], 6))
    with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as ex:
        return [t for t in ex.map(lambda a: _tesseract(*a), lavori) if t.strip()]


def _basta(campi):
    """La lettura è già buona? (targa e telaio sicuri e almeno 12 dati)"""
    return len(campi) >= 12 and (campi.get("targa") or {}).get("affidabilita") == "alta" and (campi.get("telaio") or {}).get("affidabilita") == "alta"


def _ocr_fronte(img):
    """I testi letti dal fronte: ogni riquadro, con 2 soglie; se la lettura non è ancora sicura si aggiungono altre 2 soglie. Ritorna (testi, campi)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sog = _soglie(g)
    prime = [x for x in (150, sog[-1] if sog else 140) if x][:2]
    testi = _ocr_passata(g, sorted(set(prime)))
    campi = lb_campi_fronte(testi)
    if not _basta(campi):
        altre = [x for x in sog + [130, 170] if x not in prime][:2]
        testi += _ocr_passata(g, altre)
        campi = lb_campi_fronte(testi)
    return testi, campi


def _ocr_retro(img):
    """Il retro: i timbri delle revisioni sono in una colonna ruotata. Prova la metà destra ruotata nei due versi e sceglie la migliore."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    miglior, n_max = [], -1
    for nome, rot in (("orario", cv2.ROTATE_90_CLOCKWISE), ("antiorario", cv2.ROTATE_90_COUNTERCLOCKWISE), ("nessuna", None)):
        for (x0, y0, x1, y1) in ((0.5, 0.0, 1.0, 0.55), (0.0, 0.0, 1.0, 0.55)):
            pz = g[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
            if rot is not None:
                pz = cv2.rotate(pz, rot)
            testi = []
            for soglia in (130, 150):
                testi.append(_tesseract(_binaria(pz, soglia), 6))
            n = sum(t.upper().count("REVISIONE") + t.upper().count("SCADENZA") for t in testi)
            if n > n_max:
                miglior, n_max = testi, n
        if n_max >= 6:
            break
    return miglior


# ---------------------------------------------------------------------------------------------------------------------
# correzioni e validatori
# ---------------------------------------------------------------------------------------------------------------------
def _fix_targa(s):
    s = re.sub(r"[^A-Z0-9]", "", str(s).upper())
    if len(s) != 7:
        return None
    a_cifra = {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "G": "6", "B": "8", "T": "7"}
    a_lettera = {"0": "D", "1": "I", "5": "S", "8": "B", "6": "G", "2": "Z"}
    r = "".join((a_lettera.get(c, c) if i in (0, 1, 5, 6) else a_cifra.get(c, c)) for i, c in enumerate(s))
    return r if re.fullmatch(r"[A-Z]{2}\d{3}[A-Z]{2}", r) else None


def _targa_valida(t):
    return bool(t) and all(c in _LETTERE_TARGA for c in (t[0], t[1], t[5], t[6]))


def _fix_vin(s):
    s = re.sub(r"[^A-Z0-9]", "", str(s).upper()).replace("O", "0").replace("Q", "0").replace("I", "1")
    return s if len(s) == 17 else None


def _voto_carattere(cands):
    """Fra stringhe della stessa lunghezza: per ogni posizione vale il carattere più frequente. Ritorna (stringa, quante letture concordano del tutto)."""
    if not cands:
        return "", 0
    lung = Counter(len(c) for c in cands).most_common(1)[0][0]
    c2 = [c for c in cands if len(c) == lung]
    ris = "".join(Counter(c[i] for c in c2).most_common(1)[0][0] for i in range(lung))
    return ris, sum(1 for c in c2 if c == ris)


def _num(s):
    s = str(s).replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _data_it(g, m, a, oggi=None):
    try:
        d = date(int(a), int(m), int(g))
    except ValueError:
        return None
    oggi = oggi or date.today()
    return d if date(1950, 1, 1) <= d <= date(oggi.year + 12, 12, 31) else None


def _marca(parola):
    p = re.sub(r"[^A-Z \-]", "", str(parola).upper()).strip()
    if not p:
        return ""
    if p in _MARCHE_LB:
        return p
    ris = difflib.get_close_matches(p, _MARCHE_LB, n=1, cutoff=0.7)
    if ris:
        return ris[0]
    prima = p.split(" ")[0]
    ris = difflib.get_close_matches(prima, _MARCHE_LB, n=1, cutoff=0.74)
    return ris[0] if ris else ""


def _alim(testo):
    t = str(testo).upper()
    for chiavi, v in ((("ELETTR",), "Elettrica (BEV)"), (("IBRID",), "Ibrida (HEV)"), (("GASOL", "DIESEL", "GASOLIO"), "Diesel"), (("BENZ",), "Benzina"), (("GPL",), "GPL"), (("METAN", "CNG"), "Metano")):
        if any(t.startswith(k) or k in t[:8] for k in chiavi):
            return v
    return ""


# ---------------------------------------------------------------------------------------------------------------------
# lettura dei campi dai testi (tutte le prove insieme)
# ---------------------------------------------------------------------------------------------------------------------
def _etichetta(sigla):
    """Un'etichetta del libretto come «(P.1)»: tollera spazi e punti letti male."""
    return r"\(\s*" + r"\s*\.?\s*".join(re.escape(x) for x in sigla.replace(".", " ").split()) + r"\s*\)"


def _raccogli(testi, regex, gruppo=1, flags=re.I | re.M):
    out = []
    for t in testi:
        for m in re.finditer(regex, t, flags):
            out.append(m.group(gruppo).strip())
    return out


def _piu_votato(cands, minimo=1):
    c = Counter(x for x in cands if x)
    if not c:
        return "", 0, 0
    v, n = c.most_common(1)[0]
    return v, n, len(cands)


def _aff(n, tot, forte=False):
    """Affidabilità dal numero di letture concordi: alta = molte letture uguali (o validatore forte e almeno 2)."""
    if n >= 3 or (forte and n >= 2):
        return "alta"
    if n >= 2 or forte:
        return "media"
    return "bassa"


def lb_campi_fronte(testi):
    """I dati del fronte, scelti per voto fra tutte le letture."""
    T = [re.sub(r"[ \t]+", " ", t) for t in testi]
    campi = {}

    def metti(k, v, aff):
        if v not in (None, ""):
            campi[k] = {"valore": str(v), "affidabilita": aff}
    # targa: «(A) EN061MH» (ripetuta nei 4 riquadri) e ogni parola che ha la forma di una targa
    cand = [_fix_targa(x) for x in _raccogli(T, r"\(\s*A\s*\)\s*([A-Z0-9]{6,8})\b")] + [_fix_targa(x) for x in _raccogli(T, r"\b([A-Z]{2}\s?\d{3}\s?[A-Z]{2})\b")]
    cand = [c for c in cand if c]
    grezzi = [re.sub(r"[^A-Z0-9]", "", x.upper()) for x in _raccogli(T, r"\(\s*A\s*\)\s*([A-Z0-9]{7})\b")]
    carat, _n = _voto_carattere([_fix_targa(x) or x for x in grezzi if len(x) == 7])
    if _fix_targa(carat):
        cand += [_fix_targa(carat)] * 2
    v, n, tot = _piu_votato([c for c in cand if _targa_valida(c)] or cand)
    metti("targa", v, _aff(n, tot, forte=_targa_valida(v) and n >= 2))
    # telaio: «(E) KL1MF4819BC638346»
    vin = []
    for x in _raccogli(T, r"\(\s*[E8B]\s*\)\s*([A-Z0-9 ]{15,22})"):
        for taglia in (x.replace(" ", ""), x.split(" ")[0]):
            f = _fix_vin(taglia[:17]) if len(taglia) >= 17 else None
            if f:
                vin.append(f)
                break
    vin += [f for f in (_fix_vin(x) for x in _raccogli(T, r"\b([A-Z0-9]{17})\b")) if f]
    v, n = _voto_carattere(vin)
    metti("telaio", v, _aff(n, len(vin), forte=bool(v) and n >= 2))
    # date: (B) prima immatricolazione, (I) data dell'immatricolazione cui si riferisce la carta
    for k, etic in (("immatricolazione", r"\(\s*B\s*\)"), ("immatricolazione_attuale", r"\(\s*[I1lJ|]\s*\)")):
        ds = []
        for g_, m_, a_ in re.findall(etic + r"\s*[:\-]?\s*(\d{1,2})\s*[.\-/, ]\s*(\d{1,2})\s*[.\-/, ]\s*(\d{4})", "\n".join(T)):
            d = _data_it(g_, m_, a_)
            if d:
                ds.append(d.isoformat())
        v, n, tot = _piu_votato(ds)
        metti(k, v, _aff(n, tot))
    if "immatricolazione" in campi:
        campi["anno"] = {"valore": campi["immatricolazione"]["valore"][:4], "affidabilita": campi["immatricolazione"]["affidabilita"]}
    # marca, modello, tipo
    marche = [_marca(x) for x in _raccogli(T, r"\(\s*D\s*\.?\s*1\s*\)\s*([A-Za-z][A-Za-z \-]{2,22})")]
    v, n, tot = _piu_votato(marche)
    metti("marca", v, _aff(n, tot, forte=bool(v)))
    mod = []
    for x in _raccogli(T, r"\(\s*D\s*\.?\s*3\s*\)\s*([A-Za-z0-9][^\n]{1,30})"):
        x = re.sub(r"\s{2,}.*$", "", x)
        x = re.sub(r"[^A-Za-z0-9 \-\./]", "", x).strip().upper()
        if 2 <= len(x) <= 24:
            mod.append(x)
    v, n, tot = _piu_votato(mod)
    metti("modello", v, _aff(n, tot))
    # motore e masse
    v, n, tot = _piu_votato([str(int(_num(x))) for x in _raccogli(T, r"\(\s*P\s*\.?\s*1\s*\)\s*(\d{3,4}(?:[.,]\d{1,2})?)") if _num(x) and 40 <= _num(x) <= 9999])
    metti("cilindrata", v, _aff(n, tot))
    v, n, tot = _piu_votato([str(int(round(_num(x)))) for x in _raccogli(T, r"\(\s*P\s*\.?\s*2\s*\)\s*(\d{1,3}(?:[.,]\d{1,2})?)") if _num(x) and 1 <= _num(x) <= 999])
    metti("kw", v, _aff(n, tot))
    if "kw" in campi:
        metti("cv", int(round(float(campi["kw"]["valore"]) * 1.35962)), "media")
    v, n, tot = _piu_votato([_alim(x) for x in _raccogli(T, r"\(\s*P\s*\.?\s*3\s*\)\s*([A-Za-z]{3,12})")])
    metti("alimentazione", v, _aff(n, tot, forte=bool(v)))
    motori = []
    for x in _raccogli(T, r"\(\s*P\s*\.?\s*5\s*\)\s*([A-Z0-9]{3,12})\b"):
        x = x.upper()
        if re.search(r"\d", x):
            motori.append(x[0] + x[1:].replace("O", "0").replace("I", "1"))         # nei codici motore la O è quasi sempre uno zero
    v, n, tot = _piu_votato(motori)
    metti("codice_motore", v, _aff(n, tot))
    v, n, tot = _piu_votato([str(int(_num(x))) for x in _raccogli(T, r"\(\s*F\s*\.?\s*2\s*\)\s*(\d{3,5})\b") if _num(x)])
    metti("massa_kg", v, _aff(n, tot))
    v, n, tot = _piu_votato(_raccogli(T, r"\(\s*S\s*\.?\s*1\s*\)\s*(\d{1,2})\b"))
    metti("posti", v, _aff(n, tot))
    v, n, tot = _piu_votato(_raccogli(T, r"\(\s*L\s*\)\s*(\d)\b"))
    metti("assi", v, _aff(n, tot))
    v, n, tot = _piu_votato([str(int(round(_num(x)))) for x in _raccogli(T, r"\(\s*V\s*\.?\s*7\s*\)\s*(\d{2,3}(?:[.,]\d)?)") if _num(x)])
    metti("co2", v, _aff(n, tot))
    # categoria, uso, carrozzeria, omologazione
    cat = []
    for x in _raccogli(T, r"\(\s*[J37]\s*\)\s*([MNOL]\s?[1-4IlL][A-Za-z]?)\b"):
        x = re.sub(r"\s", "", x).upper()
        x = x[0] + x[1:].replace("I", "1").replace("L", "1")
        cat.append(x[:3] if x[2:3] == "G" else x[:2])
    v, n, tot = _piu_votato(cat)
    metti("categoria", v, _aff(n, tot))
    uso = []
    for a_, b_ in re.findall(r"\(\s*[J7]\s*\.?\s*1\s*\)\s*([A-Z][^\n]{6,70})(?:\n[^A-Za-z(\n]{0,4}([A-Z][A-Z \-\.']{4,40}))?", "\n".join(T)):
        u = re.sub(r"\s+", " ", (a_ + " " + b_)).strip(" -.,;:|‘'").upper()
        if len(u) > 8:
            uso.append(u)
    v, n, tot = _piu_votato(uso)
    metti("uso", v, _aff(n, tot))
    v, n, tot = _piu_votato([re.sub(r"\s+", " ", x).strip().upper() for x in _raccogli(T, r"\(\s*[J73I1]\s*\.{1,2}\s*2\s*\)\s*([A-Z]{1,3}(?:\s*\([A-Za-z ]{3,20}\))?)")])
    metti("carrozzeria", v, _aff(n, tot))
    omo = [x.replace(" ", "") for x in _raccogli(T, r"\(\s*K\s*\)\s*\(?\s*([A-Z0-9][A-Za-z0-9*/\-]{5,26})")]
    v, n, tot = _piu_votato([x.replace("B", "E", 1) if x.startswith("OB") else x for x in omo if len(x) >= 8])
    ce = [("e" + x[1:]) for x in re.findall(r"\b([A-Za-z@€©]\d{1,2}\*\d{4}/\d{2,3}\*\d{3,5}\*\d{2})\b", "\n".join(T))]
    ve, ne, _t = _piu_votato(ce)
    metti("omologazione", (v + (f" ({ve})" if ve else "")) if v else ve, _aff(max(n, ne), tot))
    # euro: «EURO 5A» oppure i regolamenti in (V.9)
    eu = [("Euro " + x.upper()) for x in _raccogli(T, r"\bEURO\s*([0-9]{1}[A-Z]?|VI)\b")]
    for a_, b_ in re.findall(r"(\d{3,4}/\d{4})\s*\*\s*(\d{2,4}/\d{4})", "\n".join(T)):
        if b_ in _EURO_REG:
            eu.append(_EURO_REG[b_])
    v, n, tot = _piu_votato(eu)
    metti("classe_euro", v, _aff(n, tot))
    # riquadro 3: annotazioni
    v, n, tot = _piu_votato([re.sub(r"\s+", " ", x).strip(" .:;").upper() for x in _raccogli(T, r"COSTRUTTORE\s*:?\s*([A-Z0-9][A-Z0-9 .&\-]{3,38})")])
    metti("costruttore", v, _aff(n, tot))
    for k, parola in (("lunghezza_m", "LUNGHEZZA"), ("larghezza_m", "LARGHEZZA")):
        v, n, tot = _piu_votato([f"{_num(x):.3f}".rstrip("0").rstrip(".") for x in _raccogli(T, parola + r"\s*(\d[,.]\d{2,3})") if _num(x) and 0.5 < _num(x) < 25])
        metti(k, v, _aff(n, tot))
    v, n, tot = _piu_votato([re.sub(r"[^A-Z ]", "", x.upper()).strip() for x in _raccogli(T, r"TIPO\s+CAMBIO\s*:?\s*([A-Za-z ]{5,20})")])
    metti("cambio", v.title() if v else "", _aff(n, tot))
    cons = {}
    for k, pat in (("urbano", r"\bURBANO\s*(\d{1,2}[,.]\d{1,2})"), ("extraurbano", r"EXTRAURBANO\s*(\d{1,2}[,.]\d{1,2})"), ("combinato", r"COMBINATO\s*(\d{1,2}[,.]\d{1,2})")):
        v, n, tot = _piu_votato([f"{_num(x):g}" for x in _raccogli(T, pat) if _num(x) and 0.5 < _num(x) < 40])
        if v:
            cons[k] = (v, _aff(n, tot))
    if cons:
        metti("consumo", " · ".join(f"{k} {v[0]}" for k, v in cons.items()) + " l/100 km", min((v[1] for v in cons.values()), key=["bassa", "media", "alta"].index))
    gomme = Counter()
    for x in _raccogli(T, r"\b(\d{3}\s?/\s?\d{2}\s*R\s?\d{2}\s*\d{2,3}[A-Z])\b"):
        m_ = re.match(r"(\d{3})\s?/\s?(\d{2})\s*R\s?(\d{2})\s*(\d{2,3}[A-Z])", x.upper())
        gomme[f"{m_.group(1)}/{m_.group(2)} R{m_.group(3)} {m_.group(4)}"] += 1                 # es. «155/80 R13 79T»
    gomme = [g_ for g_, n_ in gomme.most_common(8) if n_ >= 1]
    metti("pneumatici_omologati", ", ".join(gomme), "media" if gomme else "")
    n_c = [re.sub(r"\s", "", x) for x in _raccogli(T, r"CIRCOLAZIONE\s+([A-Z]{2}\s?\d{6,8})\b")]
    v, n, tot = _piu_votato(n_c)
    metti("numero_carta", (v[:2] + " " + v[2:]) if v else "", _aff(n, tot))
    cogn = _piu_votato([x.upper() for x in _raccogli(T, _etichetta("C.2.1") + r"\s*([A-Za-z' ]{2,30})")])
    nome = _piu_votato([x.upper() for x in _raccogli(T, _etichetta("C.2.2") + r"\s*([A-Za-z' ]{2,30})")])
    if cogn[0] and nome[0]:
        metti("intestatario", f"{cogn[0].strip()} {nome[0].strip()}".title(), "bassa" if min(cogn[1], nome[1]) < 2 else "media")
    return campi


def lb_revisioni(testi):
    """Le revisioni dai timbri sul retro: [{data, scadenza, km, esito, affidabilita}], dalla più recente."""
    t = "\n".join(re.sub(r"[ \t]+", " ", x) for x in testi)
    ris = {}
    for m in re.finditer(r"REVISIONE\s*DEL\s*(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4})", t, re.I):
        d = _data_it(m.group(1), m.group(2), m.group(3))
        if not d:
            continue
        resto = t[m.end():m.end() + 420]
        # il blocco finisce dove inizia un'altra «REVISIONE DEL»
        fine = re.search(r"REVISIONE\s*DEL", resto, re.I)
        blocco = resto[:fine.start()] if fine else resto
        sc = re.search(r"SCADENZA\s*[:\-]?\s*(\d{1,2})\s*[/.]\s*(\d{4})", blocco, re.I)
        km = re.search(r"\bK\s?M\s*[:.]?\s*(\d{4,6})\b", blocco, re.I)
        esito = "Regolare" if re.search(r"REGOLARE", blocco, re.I) else ("Da ripetere" if re.search(r"RIPETERE", blocco, re.I) else ("Sospeso" if re.search(r"SOSPES", blocco, re.I) else ""))
        scad = ""
        if sc:
            mm, aa = int(sc.group(1)), int(sc.group(2))
            if 1 <= mm <= 12 and d.year <= aa <= d.year + 6:
                scad = f"{aa}-{mm:02d}"
        voce = {"data": d.isoformat(), "scadenza": scad, "km": km.group(1) if km else "", "esito": esito}
        # coerente: la scadenza è dopo la revisione (di solito 2 anni, 4 la prima volta)
        ok_scad = bool(scad) and 12 <= (int(scad[:4]) - d.year) * 12 + int(scad[5:]) - d.month <= 50
        voce["affidabilita"] = "media" if (ok_scad and esito) else "bassa"
        ris[voce["data"]] = max(ris.get(voce["data"], voce), voce, key=lambda x: (x["affidabilita"] == "media", bool(x["scadenza"]), bool(x["km"])))
    return sorted(ris.values(), key=lambda x: x["data"], reverse=True)


def _parole_tsv(img, soglia=150):
    """Le parole del testo con la posizione: [(testo, x, y, larghezza, altezza)]."""
    b = _binaria(img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), soglia)
    righe = _tesseract(b, 11, tsv=True).split("\n")
    out = []
    for r in righe[1:]:
        c = r.split("\t")
        if len(c) >= 12 and c[11].strip():
            try:
                out.append((c[11].strip(), int(c[6]), int(c[7]), int(c[8]), int(c[9])))
            except ValueError:
                pass
    return out


def _fix_data_rev(g, m, a, scad):
    """La data di una revisione letta dal timbro: corregge le cifre più confuse (15 letto 35, mese 11 letto 41) aiutandosi con la scadenza (di norma 2 anni dopo, 4 la prima volta, stesso mese)."""
    def cifre_possibili(n, massimo):
        s_ = f"{n:02d}"
        out = [n] if 1 <= n <= massimo else []
        for c in "123":
            x = int(c + s_[1])
            if 1 <= x <= massimo and x not in out:
                out.append(x)
        return out
    ms = cifre_possibili(m, 12)
    if scad:
        sm, sa = int(scad[5:]), int(scad[:4])
        ms = [sm] + [x for x in ms if x != sm] if (not ms or sm in ms or abs((ms[0] if ms else sm) - sm) <= 1) else ms
        if ms and ms[0] == sm and a not in (sa - 2, sa - 4, sa - 3, sa - 1):
            a = sa - 2 if abs(a - (sa - 2)) <= abs(a - (sa - 4)) else sa - 4
    for mm in ms or [m]:
        for gg in cifre_possibili(g, 31) or [g]:
            d = _data_it(gg, mm, a)
            if d:
                return d
    return None


def _parse_scheda(testo):
    """Una scheda del timbro (le sue parole, riga per riga) → dizionario oppure None."""
    t = re.sub(r"[ \t]+", " ", testo)
    sc = re.search(r"SCADENZA\W{0,3}(\d{1,2})\s*[/.]\s*(\d{4})", t, re.I)
    scad = ""
    if sc and 1 <= int(sc.group(1)) <= 12:
        scad = f"{int(sc.group(2))}-{int(sc.group(1)):02d}"
    dm = re.search(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4})(?!\d)", t)
    d = _fix_data_rev(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)), scad) if dm else None
    km = re.search(r"\bK\s?M\W{0,3}(\d{4,6})\b", t, re.I)
    if not d and not km and not scad:
        return None
    esito = "Regolare" if re.search(r"REGOLAR", t, re.I) else ("Da ripetere" if re.search(r"RIPETER", t, re.I) else ("Sospeso" if re.search(r"SOSPES", t, re.I) else ""))
    if d and scad and not (12 <= (int(scad[:4]) - d.year) * 12 + int(scad[5:]) - d.month <= 50):
        scad = ""
    return {"data": d.isoformat() if d else "", "scadenza": scad, "km": km.group(1) if km else "", "esito": esito}


def lb_revisioni_pagina(img):
    """Il retro: i timbri sono schede separate (anche una sopra l'altra). Ruota la metà destra, trova ogni «REVISIONE» e legge SOLO le parole che stanno dentro la sua scheda; ripete con più soglie e sceglie per voto."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    rot_scelta, n_max = None, 0
    for rot in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, None):
        pz = g[0:int(0.6 * h), int(0.45 * w):]
        if rot is not None:
            pz = cv2.rotate(pz, rot)
        n = sum(1 for p_ in _parole_tsv(pz, 150) if "REVIS" in p_[0].upper())
        if n > n_max:
            rot_scelta, n_max = rot, n
        if n >= 2:
            break
    if n_max == 0:
        return []
    pz = g[0:int(0.6 * h), int(0.45 * w):]
    if rot_scelta is not None:
        pz = cv2.rotate(pz, rot_scelta)
    schede = {}                                                                # ancora (riquadro 200x200) → letture
    ancore = {}
    for soglia in (150, 170):
        for (t, x, y, pw, ph) in _parole_tsv(pz, soglia):
            if "EVISION" in t.upper() or "REVIS" in t.upper():
                ancore.setdefault((round(x / 200), round(y / 200)), (x, y))
    for soglia in (150, 170):
        parole = _parole_tsv(pz, soglia)
        for chiave, (x, y) in ancore.items():
            dentro = sorted([p_ for p_ in parole if x - 40 <= p_[1] <= x + 640 and y - 90 <= p_[2] <= y + 260], key=lambda p_: (p_[2] // 28, p_[1]))
            righe, riga, ultima = [], [], None
            for p_ in dentro:
                if ultima is not None and p_[2] // 28 != ultima:
                    righe.append(" ".join(riga))
                    riga = []
                riga.append(p_[0])
                ultima = p_[2] // 28
            if riga:
                righe.append(" ".join(riga))
            lettura = _parse_scheda("\n".join(righe))
            if lettura:
                schede.setdefault(chiave, []).append(lettura)
    H2, W2 = pz.shape
    lavori = []
    for chiave, (x, y) in list(ancore.items())[:6]:
        gia = schede.get(chiave, [])
        if gia and all(any(l_[k_] for l_ in gia) for k_ in ("data", "scadenza", "km", "esito")):      # questo timbro è già letto per intero
            continue
        x0, x1, y0, y1 = max(0, x - 50), min(W2, x + 660), max(0, y - 100), min(H2, y + 270)
        ritaglio = cv2.resize(pz[y0:y1, x0:x1], None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(ritaglio)
        for soglia in (120, 145, 170):
            lavori.append((chiave, _binaria(clahe, soglia)))
    with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as ex:
        testi = list(ex.map(lambda lv: _tesseract(lv[1], 6), lavori))
    for (chiave, _img), testo in zip(lavori, testi):
        lettura = _parse_scheda(testo)
        if lettura:
            schede.setdefault(chiave, []).append(lettura)
    ris = {}
    for letture in schede.values():
        data, nd, _t = _piu_votato([l_["data"] for l_ in letture if l_["data"]])
        if not data:
            continue
        scad, ns, _t = _piu_votato([l_["scadenza"] for l_ in letture if l_["scadenza"]])
        km, nk, _t = _piu_votato([l_["km"] for l_ in letture if l_["km"]])
        esito, _n, _t = _piu_votato([l_["esito"] for l_ in letture if l_["esito"]])
        ok = bool(scad) and bool(esito)
        ris[data] = {"data": data, "scadenza": scad, "km": km, "esito": esito, "affidabilita": "media" if (ok and nd >= 2 and (nk >= 2 or ns >= 2)) else "bassa"}
    return list(ris.values())


# ---------------------------------------------------------------------------------------------------------------------
# la lettura completa
# ---------------------------------------------------------------------------------------------------------------------
def lb_leggi(nome, mime, dati):
    """Legge un libretto (PDF o foto, una o più pagine). Ritorna {'campi': {...}, 'revisioni': [...], 'pagine': n, 'fonte': 'OCR'}; campi vuoto se non riesce."""
    if not lb_disponibile():
        return {"campi": {}, "revisioni": [], "pagine": 0, "fonte": "", "errore": "manca Tesseract o OpenCV"}
    pagine = lb_immagini(nome, mime, dati)
    retro_testi, n_fronti, campi_fronte, revisioni = [], 0, {}, []
    for img in pagine:
        dritta, n_etic = _orienta_fronte(img)
        if n_etic >= 5:
            _t, c_ = _ocr_fronte(dritta)
            for k_, v_ in c_.items():                                             # più fronti: tiene il dato più sicuro
                if k_ not in campi_fronte or ["bassa", "media", "alta"].index(v_["affidabilita"]) > ["bassa", "media", "alta"].index(campi_fronte[k_]["affidabilita"]):
                    campi_fronte[k_] = v_
            n_fronti += 1
        else:
            revisioni += lb_revisioni_pagina(img)
    campi = campi_fronte
    return {"campi": campi, "revisioni": sorted({r_["data"]: r_ for r_ in revisioni}.values(), key=lambda x: x["data"], reverse=True), "pagine": len(pagine), "fonte": "OCR", "fronti": n_fronti}


# ---------------------------------------------------------------------------------------------------------------------
# controllo con l'IA (facoltativo): rilegge le pagine e confronta
# ---------------------------------------------------------------------------------------------------------------------
_SYS_LIBRETTO = ("Sei un assistente che legge la CARTA DI CIRCOLAZIONE italiana (formato europeo, con codici fra parentesi come (A), (B), (D.1)…). Ti do le immagini delle pagine. Leggi con la massima attenzione e rispondi SOLO con un oggetto JSON, senza altro testo. "
                 'Chiavi: {"targa": "(A) due lettere, tre cifre, due lettere", "telaio": "(E) 17 caratteri, senza I O Q", "marca": "(D.1)", "modello": "(D.3)", "tipo_omologato": "(D.2)", "immatricolazione": "(B) AAAA-MM-GG", "immatricolazione_attuale": "(I) AAAA-MM-GG", '
                 '"cilindrata": "(P.1) numero in cc", "kw": "(P.2) numero", "alimentazione": "(P.3) Benzina|Diesel|GPL|Metano|Elettrica|Ibrida", "codice_motore": "(P.5)", "massa_kg": "(F.2)", "posti": "(S.1)", "assi": "(L)", "categoria": "(J)", "uso": "(J.1)", "carrozzeria": "(J.2)", '
                 '"omologazione": "(K)", "co2": "(V.7) g/km", "classe_euro": "es. Euro 5", "costruttore": "", "lunghezza_m": "", "larghezza_m": "", "cambio": "", "consumo_urbano": "", "consumo_extraurbano": "", "consumo_combinato": "", "pneumatici": ["misure omologate"], '
                 '"numero_carta": "numero del modulo, es. AB 0026561", "revisioni": [{"data": "AAAA-MM-GG", "scadenza": "AAAA-MM", "km": "numero", "esito": "Regolare|Da ripetere"}]}. '
                 "Se un dato non si legge con sicurezza, lascialo vuoto (stringa vuota): NON inventare. Le revisioni sono nei timbri sul retro: elencale tutte.")


def lb_ia(pagine_jpeg):
    """Lettura con l'IA scelta (se attiva e se c'è ancora la quota). Ritorna (dizionario | None, errore | None)."""
    if "ad_attivo" not in globals() or not ad_attivo():
        return None, "assente"
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if cfg["fonte"] == "app" and not ad_puo():
        return None, ad_errore_stop() if "ad_errore_stop" in globals() else "limite_app"
    testo, err = _ad_invia(prov, cfg, _SYS_LIBRETTO, [("u", "Leggi questa carta di circolazione.")], pagine_jpeg, 2200, json_out=True)
    if err:
        return None, err
    m = re.search(r"\{.*\}", testo or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except Exception:
        d = None
    return (d, None) if isinstance(d, dict) else (None, "formato")


def lb_jpeg_pagine(nome, mime, dati, lato=1800):
    """Le pagine ridotte (JPEG) da mandare all'IA."""
    out = []
    for img in lb_immagini(nome, mime, dati, dpi=170)[:3]:
        h, w = img.shape[:2]
        s = lato / max(h, w)
        if s < 1:
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if ok:
            out.append(buf.tobytes())
    return out


def lb_unisci(ocr, ia):
    """Fonde OCR e IA: se concordano il dato è «alta»; se non concordano vale quello che passa i controlli (targa, telaio) altrimenti l'IA, ma con «media»."""
    campi = {k: dict(v) for k, v in (ocr.get("campi") or {}).items()}
    if not ia:
        return campi, ocr.get("revisioni") or []
    norm = lambda x: re.sub(r"[^A-Z0-9]", "", str(x or "").upper())
    mappa = {"targa": _fix_targa, "telaio": _fix_vin}

    def metti(k, v, aff):
        if v not in (None, "", []):
            campi[k] = {"valore": str(v), "affidabilita": aff}
    for k in ("targa", "telaio", "marca", "modello", "immatricolazione", "immatricolazione_attuale", "cilindrata", "kw", "alimentazione", "codice_motore", "massa_kg", "posti", "assi", "categoria", "uso", "carrozzeria", "omologazione", "co2",
              "classe_euro", "costruttore", "lunghezza_m", "larghezza_m", "cambio", "numero_carta"):
        vi = str(ia.get(k) or "").strip()
        if k in mappa:
            vi = mappa[k](vi) or ""
        if k == "marca":
            vi = _marca(vi) or vi.upper()
        if not vi:
            continue
        vo = (campi.get(k) or {}).get("valore", "")
        if vo and norm(vo) == norm(vi):
            campi[k]["affidabilita"] = "alta"
        elif vo and k in mappa and mappa[k](vo) and not mappa[k](vi):
            continue
        elif vo and k in mappa and (campi[k]["affidabilita"] == "alta"):
            continue
        else:
            metti(k, vi, "media")
    if "immatricolazione" in campi and "anno" not in campi:
        campi["anno"] = {"valore": campi["immatricolazione"]["valore"][:4], "affidabilita": campi["immatricolazione"]["affidabilita"]}
    cons = [f"{etic} {ia[k]}" for etic, k in (("urbano", "consumo_urbano"), ("extraurbano", "consumo_extraurbano"), ("combinato", "consumo_combinato")) if str(ia.get(k) or "").strip()]
    if cons and "consumo" not in campi:
        metti("consumo", " · ".join(cons) + " l/100 km", "media")
    gomme = ia.get("pneumatici")
    if isinstance(gomme, list) and gomme and "pneumatici_omologati" not in campi:
        metti("pneumatici_omologati", ", ".join(str(x) for x in gomme[:8]), "media")
    rev = list(ocr.get("revisioni") or [])
    for r in (ia.get("revisioni") or []):
        try:
            d = date.fromisoformat(str(r.get("data")))
        except ValueError:
            continue
        sc = str(r.get("scadenza") or "")[:7]
        voce = {"data": d.isoformat(), "scadenza": sc if re.fullmatch(r"\d{4}-\d{2}", sc) else "", "km": re.sub(r"\D", "", str(r.get("km") or "")), "esito": str(r.get("esito") or ""), "affidabilita": "media"}
        presente = next((x for x in rev if x["data"] == voce["data"]), None)
        if presente:
            if presente.get("scadenza") == voce["scadenza"] and presente.get("km") == voce["km"]:
                presente["affidabilita"] = "alta"
            else:
                presente.update({k: voce[k] for k in ("scadenza", "km", "esito") if voce[k]})
                presente["affidabilita"] = "media"
        else:
            rev.append(voce)
    return campi, sorted(rev, key=lambda x: x["data"], reverse=True)
