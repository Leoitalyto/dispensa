# -*- coding: utf-8 -*-
"""LETTORE DELLO SCRITTO (anche a mano) — vale per TUTTA l'app, anche per le sezioni future.
Sotto ogni foto o pagina di documento che l'app mostra compare da solo il pulsante «🔍 Leggi lo scritto»: nessun modulo deve ricordarsi di aggiungerlo.
Cosa fa: manda QUELLA pagina all'intelligenza artificiale attiva nell'app (la stessa della diagnosi delle spie: Claude, Gemini, OpenAI oppure OpenRouter anche gratuito)
e restituisce la trascrizione fedele, riga per riga:
 · testo normale  = letto con sicurezza;
 · ARANCIONE      = lettura non del tutto sicura (la più probabile);
 · ROSSO          = impossibile da riconoscere;
 · in fondo: nota rossa (cosa non si è potuto leggere), nota arancione (i punti incerti) e «Lettura per logica» (ipotesi ragionate dal contesto, in seconda battuta).
Il testo letto si può scaricare o copiare. La lettura resta salvata (nei dati privati della persona): la volta dopo si riapre subito, senza rileggere.
Il programma OCR dell'app (Tesseract) NON sa leggere la calligrafia: per questo serve l'IA. Senza una chiave il pulsante spiega come attivarla (c'è anche la strada gratuita).
Per NON mostrare il pulsante sotto una certa immagine: st.image(..., _lettore=False).
Caricato da app_dispensa.py dopo immagini_sicure.py e auto_diagnosi.py. Nomi con prefisso «le_»."""
import io
import re
import html as _le_html
import hashlib
import threading
from datetime import datetime

import streamlit as st

_LE_LOC = threading.local()
LE_MIN_BYTE = 15000                      # sotto questa misura è un'icona o una miniatura: niente pulsante
LE_MAX_PAGINE_PDF = 12

_LE_SISTEMA = """Sei un trascrittore professionista di documenti, esperto di calligrafia difficile (referti e ricette mediche, moduli compilati a mano, appunti, lettere, ricevute, timbri, anche in corsivo o in stampatello frettoloso).
Ti viene data l'IMMAGINE di una pagina. Devi leggerla con la massima attenzione e restituire una trascrizione FEDELE.

REGOLE DI TRASCRIZIONE
- Trascrivi TUTTO quello che c'è scritto, stampato e a mano, nell'ordine di lettura, andando a capo come nel documento. Per le tabelle: una riga per ogni riga, con « | » tra le colonne.
- NON riassumere, NON correggere, NON completare, NON inventare. Scrivi quello che c'è, non quello che ti aspetti.
- Ingrandisci mentalmente ogni parola scritta a mano: confronta le lettere con altre uguali nella stessa pagina (stessa mano) prima di decidere.
- Parola o tratto letto ma NON del tutto sicuro: scrivilo tra doppie quadre con il punto di domanda, così: [[?parola più probabile]].
- Parola o tratto IMPOSSIBILE da riconoscere: scrivi [[X]] (uno per ogni parola o tratto illeggibile). Mai tirare a indovinare qui.
- Nomi di medicinali, dosi, numeri, date, codici e cognomi: se anche una sola lettera o cifra è dubbia, vanno marcati come incerti [[?...]]. Non «aggiustare» mai una dose.
- Le abbreviazioni restano come sono scritte nel TESTO (le spieghi dopo, nella lettura per logica).
- Timbri, firme e sigle: indicali tra parentesi tonde, per esempio (timbro: ...), (firma illeggibile).

FORMATO DELLA RISPOSTA — esattamente queste sezioni, con queste intestazioni, in italiano:
### TIPO
Una riga: che documento sembra (per esempio: referto di visita ginecologica, ricetta, bolletta, lettera…).
### TESTO
La trascrizione fedele, con i segni [[?...]] e [[X]].
### NON RICONOSCIUTO
Elenco puntato («- ») dei punti impossibili da leggere: dove sono (riga o zona) e perché (grafia, macchia, taglio, timbro sopra…). Se non ce ne sono scrivi: Nessuno.
### INCERTO
Elenco puntato («- ») dei punti non del tutto sicuri: «come l'ho letto» → eventuale altra lettura possibile. Se non ce ne sono scrivi: Nessuno.
### LETTURA PER LOGICA
Solo in seconda battuta e dichiarandolo come IPOTESI: per i punti incerti o illeggibili proponi la lettura più sensata ragionando sul contesto (tipo di documento, frasi vicine, abbreviazioni d'uso: per esempio «EO» = esame obiettivo, «PA» = pressione arteriosa, «tp» = terapia). Per ogni ipotesi di' in due parole su cosa si basa. Sciogli qui anche le abbreviazioni. Se non c'è niente da aggiungere scrivi: Nessuna.

Non aggiungere altro: niente premesse, niente consigli medici, niente conclusioni tue."""
_LE_RICHIESTA = "Leggi questa pagina e trascrivila seguendo le regole e il formato indicati."

_LE_CSS = """<style>
div[class*="st-key-le_b_"]{margin:-4px 0 4px !important}
div[class*="st-key-le_b_"] button{min-height:0 !important;padding:.3rem .9rem !important;border-radius:999px !important;border:1px solid rgba(120,170,255,.55) !important;background:rgba(40,80,160,.18) !important}
div[class*="st-key-le_b_"] button p{font-size:.86rem !important;font-weight:700 !important}
.le-box{border-radius:14px;padding:12px 14px;margin:6px 0;line-height:1.55;font-size:.98rem;word-break:break-word}
.le-testo{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18)}
.le-inc{color:#ffb020;font-weight:700;border-bottom:2px dotted #ffb020}
.le-ok{color:#5fe08a;font-weight:700;border-bottom:2px solid #5fe08a}
.le-no{color:#ff5a5a;font-weight:800;background:rgba(255,60,60,.14);border-radius:5px;padding:0 4px}
.le-rosso{background:rgba(255,60,60,.12);border:1px solid rgba(255,90,90,.75);color:#ff8f8f}
.le-arancio{background:rgba(255,170,30,.12);border:1px solid rgba(255,176,32,.75);color:#ffc45e}
.le-logica{background:rgba(70,150,255,.12);border:1px solid rgba(110,170,255,.75);color:#a9cbff}
.le-box b.le-t{display:block;margin-bottom:4px}
.le-leg{font-size:.84rem;opacity:.92;margin:2px 0 6px}
</style>"""

_LE_ERRORI = {
    "chiave": "La chiave dell'intelligenza artificiale non è valida o è scaduta: va controllata in Auto → Diagnosi spie → «Scegli l'intelligenza artificiale».",
    "limite": "Il servizio di intelligenza artificiale in questo momento è occupato (troppe richieste). Riprova tra un minuto.",
    "rete": "Non sono riuscito a raggiungere il servizio di intelligenza artificiale. Controlla la connessione e riprova.",
    "rifiuto": "Il servizio non ha voluto leggere questa immagine. Prova con una foto più nitida o con un altro servizio.",
    "modello": "Il modello scelto non legge le immagini (o non esiste più): scegline un altro in Auto → Diagnosi spie → «Scegli l'intelligenza artificiale».",
    "pagamento": "Il modello scelto è a pagamento e non c'è credito: scegli un modello gratuito oppure ricarica.",
    "formato": "La risposta è arrivata in una forma che non capisco. Tocca «🔄 Rileggi».",
    "limite_app": "Per oggi le letture offerte dall'app sono finite: riprova domani, oppure usa una tua chiave (anche gratuita).",
    "vuoto": "La lettura è tornata vuota: forse la foto è troppo scura o mossa. Riprova con una foto più nitida.",
    "immagine": "Non riesco ad aprire questa immagine per leggerla.",
}


# ---------------------------------------------------------------------------------------------------------------------
# immagine → JPEG nitido per la lettura
# ---------------------------------------------------------------------------------------------------------------------
def le_jpeg(dati, lato=2000):
    """La pagina in JPEG, al massimo «lato» pixel sul lato lungo (abbastanza per la calligrafia, leggera da inviare). None se non è un'immagine."""
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(dati))
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            sfondo = Image.new("RGB", im.size, (255, 255, 255))
            sfondo.paste(im, mask=im.split()[-1])
            im = sfondo
        else:
            im = im.convert("RGB")
        im.thumbnail((lato, lato))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88, optimize=True)
        return buf.getvalue()
    except Exception:
        return None


def le_pagina_pdf(dati, indice, dpi=170):
    """Una pagina di un PDF come immagine nitida (PNG). None se non si riesce."""
    try:
        try:
            import pymupdf as _mu
        except Exception:
            import fitz as _mu
        doc = _mu.open(stream=dati, filetype="pdf")
        try:
            return doc[indice].get_pixmap(dpi=dpi, alpha=False).tobytes("png")
        finally:
            doc.close()
    except Exception:
        return None


# ---------------------------------------------------------------------------------------------------------------------
# la lettura
# ---------------------------------------------------------------------------------------------------------------------
def le_attivo():
    return "ad_attivo" in globals() and ad_attivo()


def le_servizio():
    try:
        return (AD_PROVIDER.get(ad_provider_scelto()) or {}).get("nome", "il servizio di intelligenza artificiale")
    except Exception:
        return "il servizio di intelligenza artificiale"


def le_richiesta(suggerimenti="", parole=None, zona=None):
    """Il testo che accompagna l'immagine: la richiesta, più (se ci sono) la fascia, le informazioni date dalla persona e le parole già corrette."""
    r = _LE_RICHIESTA
    if zona:
        r += (f"\nATTENZIONE: questa immagine è la FASCIA {zona[0]} di {zona[1]} della pagina (contando dall'alto), ingrandita. Trascrivi solo le righe intere: "
              "ignora una riga tagliata a metà dal bordo in alto o in basso (è intera nella fascia vicina).")
    sug = re.sub(r"\s+", " ", str(suggerimenti or "")).strip()[:300]
    if sug:
        r += ("\nINFORMAZIONI DATE DALLA PERSONA su questa pagina (usale solo come contesto per capire la grafia e le abbreviazioni; NON copiarle nel testo e non darle per certe): " + sug)
    voci = [v for v in (parole or []) if v.get("da") and v.get("a")][-40:]
    if voci:
        r += ("\nPAROLE GIÀ CORRETTE DALLA PERSONA in letture precedenti (se ritrovi lo stesso tratto di penna, è probabile la stessa lettura; non forzarla se il tratto è diverso): "
              + "; ".join(f"«{v['da']}» va letto «{v['a']}»" + (f" (grafia: {v['grafia']})" if v.get("grafia") else "") for v in voci))
    return r


def le_leggi(jpeg, suggerimenti="", parole=None, zona=None, temperatura=0.1):
    """Chiede la trascrizione. Ritorna (testo grezzo, None) oppure (None, errore)."""
    if not le_attivo():
        return None, "assente"
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if cfg["fonte"] == "app" and not ad_puo():
        return None, (ad_errore_stop() if "ad_errore_stop" in globals() else "limite_app")
    st.session_state.pop("_ad_dettaglio", None)
    testo, err = _ad_invia(prov, cfg, _LE_SISTEMA, [("u", le_richiesta(suggerimenti, parole, zona))], [jpeg], 4000, False, {"temperature": temperatura})
    if err:
        return None, err
    if not (testo or "").strip():
        return None, "vuoto"
    return testo, None


# ---------------------------------------------------------------------------------------------------------------------
# pulizia della pagina prima della lettura: raddrizzata, via ombre e ingiallimento, più contrasto, più nitida
# ---------------------------------------------------------------------------------------------------------------------
def _le_cv():
    try:
        import cv2
        import numpy as np
        return cv2, np
    except Exception:
        return None, None


def _le_angolo(grigio, cv2, np):
    """Di quanti gradi è storta la pagina (fra -6 e +6): l'angolo che rende le righe di scrittura più «a strisce». 0 se non è chiaro."""
    try:
        h, w = grigio.shape[:2]
        s = 600.0 / max(h, w)
        g = cv2.resize(grigio, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else grigio
        bn = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        hh, ww = bn.shape[:2]

        def punteggio(ang):
            m = cv2.getRotationMatrix2D((ww / 2, hh / 2), ang, 1.0)
            r = cv2.warpAffine(bn, m, (ww, hh), flags=cv2.INTER_NEAREST, borderValue=0)
            return float(np.var(r.sum(axis=1).astype("float64")))
        base = punteggio(0.0)
        meglio, ang_m = base, 0.0
        for k in range(-12, 13):
            ang = k * 0.5
            if ang == 0:
                continue
            p_ = punteggio(ang)
            if p_ > meglio:
                meglio, ang_m = p_, ang
        return ang_m if (abs(ang_m) >= 1.0 and meglio > base * 1.08) else 0.0
    except Exception:
        return 0.0


def le_pulisci(dati, lato=2200):
    """La pagina ripulita (JPEG). Se la pulizia non riesce ritorna la pagina così com'è; None se non è un'immagine."""
    base = le_jpeg(dati, lato)
    cv2, np = _le_cv()
    if not base or cv2 is None:
        return base
    try:
        img = cv2.imdecode(np.frombuffer(base, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return base
        h, w = img.shape[:2]
        ang = _le_angolo(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2, np)
        if ang:
            m = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
            img = cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        k = max(31, (min(h, w) // 10) | 1)
        sfondo = cv2.GaussianBlur(cv2.dilate(img, np.ones((9, 9), np.uint8)), (k, k), 0)        # la carta senza l'inchiostro: ombre e ingiallimento
        img = cv2.divide(img, sfondo, scale=255)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_, a_, b_ = cv2.split(lab)
        l_ = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l_)
        img = cv2.cvtColor(cv2.merge((l_, a_, b_)), cv2.COLOR_LAB2BGR)
        sfoc = cv2.GaussianBlur(img, (0, 0), 1.2)
        img = cv2.addWeighted(img, 1.5, sfoc, -0.5, 0)                                             # più nitida
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return buf.tobytes() if ok else base
    except Exception:
        return base


def le_zone(jpeg, lato=2000):
    """Divide la pagina in 2 o 3 fasce orizzontali ingrandite (con un po' di sovrapposizione, così nessuna riga resta tagliata in tutte e due)."""
    cv2, np = _le_cv()
    if cv2 is None:
        return [jpeg]
    try:
        img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        n = 3 if h >= w * 1.15 else 2
        passo = h / n
        sovr = int(h * 0.06)
        out = []
        for i in range(n):
            y0, y1 = max(0, int(i * passo) - sovr), min(h, int((i + 1) * passo) + sovr)
            pezzo = img[y0:y1]
            s = min(2.2, lato / max(pezzo.shape[:2]))
            if s > 1.05:
                pezzo = cv2.resize(pezzo, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
            ok, buf = cv2.imencode(".jpg", pezzo, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ok:
                out.append(buf.tobytes())
        return out or [jpeg]
    except Exception:
        return [jpeg]


def le_grezzo(sez):
    """Ricompone la risposta nelle sue sezioni (stesso formato che dà l'intelligenza artificiale)."""
    return ("### TIPO\n" + (sez.get("tipo") or "") + "\n### TESTO\n" + (sez.get("testo") or "") + "\n### NON RICONOSCIUTO\n" + (sez.get("no") or "Nessuno")
            + "\n### INCERTO\n" + (sez.get("incerto") or "Nessuno") + "\n### LETTURA PER LOGICA\n" + (sez.get("logica") or "Nessuna"))


def _le_norma(t):
    return re.sub(r"[^0-9a-zàèéìòù]+", "", str(t or "").lower())


def le_unisci_zone(grezzi):
    """Mette insieme le letture delle fasce, togliendo le righe ripetute dove le fasce si sovrappongono."""
    import difflib
    nomi = {2: ["Parte alta", "Parte bassa"], 3: ["Parte alta", "Parte centrale", "Parte bassa"]}.get(len(grezzi), [f"Parte {i + 1}" for i in range(len(grezzi))])
    tot = {"tipo": "", "testo": "", "no": "", "incerto": "", "logica": ""}
    righe_tot = []
    for nome, g in zip(nomi, grezzi):
        if g is None:
            righe_tot.append(f"[[X]] ({nome.lower()} della pagina: lettura non riuscita)")
            tot["no"] += f"\n- {nome}: la lettura di questa fascia non è riuscita (riprova)."
            continue
        sz = le_sezioni(g)
        tot["tipo"] = tot["tipo"] or sz["tipo"]
        righe = [r for r in sz["testo"].split("\n")]
        coda = [_le_norma(r) for r in righe_tot[-4:] if _le_norma(r)]
        while righe and coda and _le_norma(righe[0]) and any(difflib.SequenceMatcher(None, _le_norma(righe[0]), c).ratio() > 0.82 for c in coda):
            righe.pop(0)                                         # riga già letta nella fascia sopra
        righe_tot += righe
        for k in ("no", "incerto", "logica"):
            if not _le_vuota(sz[k]):
                tot[k] += f"\n{nome}:\n{sz[k]}"
    tot["testo"] = "\n".join(righe_tot).strip()
    for k in ("no", "incerto", "logica"):
        tot[k] = tot[k].strip()
    return le_grezzo(tot)


def le_confronta(g1, g2):
    """Due letture della stessa pagina: dove NON coincidono la parola diventa «incerta» (arancione) e la differenza va nella nota. Ritorna (grezzo, quante differenze)."""
    import difflib
    s1, s2 = le_sezioni(g1), le_sezioni(g2)
    spezza = lambda t: re.findall(r"\[\[.*?\]\]|\n|[^\s\[]+|\[", t or "", flags=re.S)
    t1, t2 = spezza(s1["testo"]), spezza(s2["testo"])
    n1, n2 = [("\n" if x == "\n" else _le_norma(x)) for x in t1], [("\n" if x == "\n" else _le_norma(x)) for x in t2]
    out, diff = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, n1, n2, autojunk=False).get_opcodes():
        pezzo = t1[i1:i2]
        if op == "equal":
            out += pezzo
            continue
        va = " ".join(x for x in pezzo if x != "\n" and _le_norma(x))
        vb = " ".join(x for x in t2[j1:j2] if x != "\n" and _le_norma(x))
        if op == "insert":
            if vb:
                diff.append(f"- una delle due letture ha in più: «{vb}»")
            continue
        for x in pezzo:
            out.append(x if (x == "\n" or not _le_norma(x) or x.startswith("[[")) else f"[[?{x}]]")
        if va or vb:
            diff.append(f"- «{va or '…'}» ↔ nell'altra lettura: «{vb or '(manca)'}»")
    testo = re.sub(r" ?\n ?", "\n", " ".join(out))
    pul = lambda t: re.sub(r"\[\[\?\s*(.*?)\]\]", r"\1", t).replace("[[X]]", "▮")
    s1["testo"] = testo
    if diff:
        s1["incerto"] = ("" if _le_vuota(s1["incerto"]) else s1["incerto"] + "\n") + "Punti in cui le DUE letture non coincidono:\n" + "\n".join(pul(d) for d in diff[:40])
    if not _le_vuota(s2["logica"]) and _le_norma(s2["logica"]) != _le_norma(s1["logica"]):
        s1["logica"] = ("" if _le_vuota(s1["logica"]) else s1["logica"] + "\n") + "Dalla seconda lettura: " + s2["logica"]
    return le_grezzo(s1), len(diff)


def le_sezioni(grezzo):
    """Divide la risposta nelle sue parti. Se le intestazioni mancano, tutto finisce nel testo (non si perde niente)."""
    out = {"tipo": "", "testo": "", "no": "", "incerto": "", "logica": ""}
    pezzi = re.split(r"(?m)^\s*#{2,4}\s*(.+?)\s*$", grezzo or "")
    if len(pezzi) < 3:
        out["testo"] = (grezzo or "").strip()
        return out
    if pezzi[0].strip():
        out["testo"] = pezzi[0].strip()
    for i in range(1, len(pezzi) - 1, 2):
        nome, corpo = pezzi[i].upper(), pezzi[i + 1].strip()
        if "LOGICA" in nome:
            out["logica"] = corpo
        elif "NON RICONOSC" in nome or "ILLEGGIB" in nome:
            out["no"] = corpo
        elif "INCERT" in nome:
            out["incerto"] = corpo
        elif "TIPO" in nome:
            out["tipo"] = corpo.split("\n")[0].strip()
        elif "TESTO" in nome or "TRASCRIZ" in nome:
            out["testo"] = (out["testo"] + "\n" + corpo).strip()
        else:
            out["testo"] = (out["testo"] + "\n" + corpo).strip()
    return out


def _le_vuota(t):
    return not (t or "").strip() or re.fullmatch(r"[-•*\s]*(nessun[oa]?|niente|n/?a)\.?", (t or "").strip(), re.I) is not None


def le_conta(testo):
    return len(re.findall(r"\[\[\?", testo or "")), len(re.findall(r"\[\[\s*[Xx✗]\s*\]\]", testo or ""))


def le_html(testo):
    """Il testo con i colori: arancione = incerto, rosso = illeggibile."""
    t = _le_html.escape(testo or "")
    t = re.sub(r"\[\[\s*[Xx✗]\s*\]\]", "<span class='le-no'>▮ illeggibile</span>", t)
    t = re.sub(r"\[\[\?\s*(.*?)\]\]", lambda m: f"<span class='le-inc'>{m.group(1).strip() or '?'}</span>", t, flags=re.S)
    t = re.sub(r"⟦ok:(.*?)⟧", lambda m: f"<span class='le-ok'>{m.group(1)}</span>", t, flags=re.S)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def le_applica(testo, correzioni):
    """Mette nel testo le correzioni fatte dalla persona (diventano verdi)."""
    t = testo or ""
    for c in correzioni or []:
        da, a_ = str(c.get("da") or "").strip(), str(c.get("a") or "").strip()
        if not da or not a_:
            continue
        segno = r"\[\[\?\s*" + re.escape(da) + r"\s*\]\]"
        if re.search(segno, t):                              # era una parola incerta: cambio solo quella (non le altre uguali, lette con sicurezza)
            t = re.sub(segno, lambda m: f"⟦ok:{a_}⟧", t)
        else:
            t = re.sub(r"(?<![\w⟦:])" + re.escape(da) + r"(?![\w⟧])", lambda m: f"⟦ok:{a_}⟧", t)
    return t


def le_testo_semplice(sez):
    """Il testo da scaricare o copiare (senza colori: «(?)» = incerto, «[illeggibile]» = non riconosciuto)."""
    def pulisci(t):
        t = re.sub(r"\[\[\s*[Xx✗]\s*\]\]", "[illeggibile]", t or "")
        t = re.sub(r"⟦ok:(.*?)⟧", r"\1", t, flags=re.S)
        return re.sub(r"\[\[\?\s*(.*?)\]\]", lambda m: f"{m.group(1).strip()}(?)", t, flags=re.S)
    parti = []
    if sez.get("tipo"):
        parti.append("TIPO DI DOCUMENTO: " + sez["tipo"])
    parti.append("TESTO LETTO\n" + pulisci(sez.get("testo")))
    if not _le_vuota(sez.get("no")):
        parti.append("NON RICONOSCIUTO\n" + pulisci(sez["no"]))
    if not _le_vuota(sez.get("incerto")):
        parti.append("NON DEL TUTTO SICURO\n" + pulisci(sez["incerto"]))
    if not _le_vuota(sez.get("logica")):
        parti.append("LETTURA PER LOGICA (ipotesi, da verificare)\n" + pulisci(sez["logica"]))
    parti.append("Legenda: (?) = lettura non sicura · [illeggibile] = non riconosciuto.\nLettura automatica: può contenere errori. Per dosi, medicinali e diagnosi vale solo il documento originale e la parola del medico.")
    return "\n\n".join(parti)


# ---------------------------------------------------------------------------------------------------------------------
# la lettura salvata (nei dati privati della persona)
# ---------------------------------------------------------------------------------------------------------------------
def _le_percorso(ident):
    uid = (st.session_state.get("sess") or {}).get("uid", "prova")
    return f"documenti/{uid}/lettura_{ident}.json"


def le_salvata(ident):
    k = "le_ris_" + ident
    if k in st.session_state:
        return st.session_state[k]
    ris = None
    try:
        d = carica_dati(crea_archivio(), _le_percorso(ident))
        if isinstance(d, dict) and d.get("grezzo"):
            ris = {k: d[k] for k in ("grezzo", "il", "servizio", "modo", "suggerimenti", "nota", "grafia", "correzioni") if k in d}
    except Exception:
        ris = None
    st.session_state[k] = ris
    return ris


def le_salva(ident, ris):
    st.session_state["le_ris_" + ident] = ris
    try:
        salva_file(_le_percorso(ident), lambda d, r=ris: (d.clear(), d.update(r)), "Lettura dello scritto salvata")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------------------------------------------------
# il pulsante e il pannello
# ---------------------------------------------------------------------------------------------------------------------
def _le_alterna(chiave):
    st.session_state[chiave] = not st.session_state.get(chiave, False)


def _le_in_finestra():
    try:
        return bool(co_contesto()["finestra"]) if "co_contesto" in globals() else False
    except Exception:
        return False


def _le_in_modulo():
    try:
        from streamlit.elements.lib.form_utils import current_form_id
        return bool(current_form_id(st._main._active_dg))
    except Exception:
        return False


def _le_gia_visto(chiave):
    """Lo stesso pulsante non va disegnato due volte nella stessa ridisegnata (stessa foto mostrata due volte)."""
    ss = st.session_state
    run = (ss.get("_vm_run", 0), ss.get("_co_dlg") if chiave.startswith("le_b_d") else None)
    if ss.get("_le_run") != run:
        ss["_le_run"] = run
        ss["_le_visti"] = []
    if chiave in ss["_le_visti"]:
        if chiave.startswith("le_b_d"):                 # dentro una finestra la pagina si ridisegna da sola: si riparte
            ss["_le_visti"] = [chiave]
            return False
        return True
    ss["_le_visti"] = ss["_le_visti"] + [chiave]
    return False


def le_pulsante(ident, sorgente, etichetta="🔍 Leggi lo scritto"):
    """Il pulsante sotto un'immagine. ident = impronta della pagina; sorgente = i byte dell'immagine oppure una funzione che li restituisce."""
    if _le_in_modulo():
        return                                             # dentro un modulo di Streamlit i pulsanti normali non sono permessi
    ident = re.sub(r"[^A-Za-z0-9_]", "", str(ident))[:40]
    chiave = f"le_b_{'d' if _le_in_finestra() else 'm'}{ident}"
    if _le_gia_visto(chiave):
        return
    k_ap = "le_ap_" + ident
    aperto = bool(st.session_state.get(k_ap))
    _LE_LOC.dentro = True
    try:
        st.markdown(_LE_CSS, unsafe_allow_html=True)
        st.button(("🙈 Chiudi la lettura" if aperto else etichetta), key=chiave, on_click=_le_alterna, args=(k_ap,),
                  help="Legge lo scritto di questa pagina, anche a mano, e ti restituisce il testo: in arancione ciò che non è sicuro, in rosso ciò che non si riconosce.")
        if aperto:
            le_pannello(ident, sorgente)
    finally:
        _LE_LOC.dentro = False


def _le_mostra_errore(err):
    if err in ("limite_utente",) and "ad_mostra_errore" in globals():
        ad_mostra_errore(err)
        return
    st.warning("⚠️ " + _LE_ERRORI.get(err, "Non sono riuscito a leggere. Riprova tra poco."))
    dett = st.session_state.get("_ad_dettaglio")
    if dett and (st.session_state.get("sess") or {}).get("admin"):
        st.caption("Dettaglio tecnico (lo vedi solo tu): " + str(dett)[:400])
    if err in ("chiave", "modello", "pagamento", "limite_app") and "ad_guida_propria_chiave" in globals():
        with st.expander("🔑 Usa una tua chiave (c'è anche la strada gratuita)"):
            ad_guida_propria_chiave()
            if "ad_campo_chiave_propria" in globals():
                ad_campo_chiave_propria()


# ---------------------------------------------------------------------------------------------------------------------
# le parole corrette dalla persona: restano e aiutano le letture successive
# ---------------------------------------------------------------------------------------------------------------------
def _le_percorso_parole():
    uid = (st.session_state.get("sess") or {}).get("uid", "prova")
    return f"documenti/{uid}/lettore_parole.json"


def le_parole():
    if "le_parole_mem" in st.session_state:
        return st.session_state["le_parole_mem"]
    voci = []
    try:
        d = carica_dati(crea_archivio(), _le_percorso_parole())
        voci = [v for v in (d.get("voci") or []) if isinstance(v, dict)] if isinstance(d, dict) else []
    except Exception:
        voci = []
    st.session_state["le_parole_mem"] = voci
    return voci


def le_parola_ricorda(da, a_, grafia=""):
    voci = [v for v in le_parole() if not (_le_norma(v.get("da")) == _le_norma(da) and _le_norma(v.get("grafia")) == _le_norma(grafia))]
    voci.append({"da": da, "a": a_, "grafia": grafia})
    voci = voci[-200:]
    st.session_state["le_parole_mem"] = voci
    try:
        salva_file(_le_percorso_parole(), lambda d, v=voci: d.__setitem__("voci", v), "Lettore: parola corretta")
    except Exception:
        pass


def le_incerte(testo):
    viste = []
    for m in re.findall(r"\[\[\?\s*(.*?)\]\]", testo or "", flags=re.S):
        m = m.strip()
        if m and m not in viste:
            viste.append(m)
    return viste


_LE_ALTRA = "✍️ Un'altra parola…"


def _le_cb_correggi(ident):
    """Salva la correzione scritta nei campi (chiamata dal pulsante, PRIMA che la pagina si ridisegni: così si vede subito in verde)."""
    ss = st.session_state
    ris = ss.get("le_ris_" + ident)
    if not ris:
        return
    scelta = ss.get(f"le_c_sc_{ident}")
    da = (ss.get(f"le_c_da_{ident}") or "").strip() if (scelta in (None, _LE_ALTRA)) else str(scelta).strip()
    a_ = (ss.get(f"le_c_a_{ident}") or "").strip()
    grafia = (ss.get(f"le_c_gr_{ident}") or "").strip()[:60]
    if not da or not a_ or da == a_:
        ss[f"le_c_msg_{ident}"] = "⚠️ Scrivi sia la parola com'è stata letta sia com'è giusta."
        return
    ris = dict(ris)
    ris["correzioni"] = [c for c in (ris.get("correzioni") or []) if c.get("da") != da] + [{"da": da, "a": a_}]
    if grafia:
        ris["grafia"] = grafia
    le_salva(ident, ris)
    le_parola_ricorda(da, a_, grafia)
    for k in (f"le_c_da_{ident}", f"le_c_a_{ident}", f"le_c_sc_{ident}"):
        ss.pop(k, None)
    ss[f"le_c_msg_{ident}"] = f"✅ Corretto: «{da}» → «{a_}». Me lo ricordo anche per le prossime letture."


def _le_cb_togli_correzione(ident):
    ss = st.session_state
    ris = ss.get("le_ris_" + ident)
    if ris and ris.get("correzioni"):
        ris = dict(ris)
        tolta = ris["correzioni"][-1]
        ris["correzioni"] = ris["correzioni"][:-1]
        le_salva(ident, ris)
        ss[f"le_c_msg_{ident}"] = f"↩️ Tolta la correzione «{tolta.get('da')}» → «{tolta.get('a')}»."


def _le_correzioni_ui(ident, ris, testo):
    corr = ris.get("correzioni") or []
    with st.expander(f"✏️ Correggi una parola letta male" + (f" · {len(corr)} corrette" if corr else "")):
        st.caption("Scegli (o scrivi) la parola com'è stata letta e scrivi com'è giusta: nel testo diventa **verde** e l'app la ricorda per le prossime letture della stessa grafia.")
        msg = st.session_state.pop(f"le_c_msg_{ident}", None)
        if msg:
            (st.warning if msg.startswith("⚠️") else st.success)(msg)
        incerte = le_incerte(testo)
        scelta = st.selectbox("Parola da correggere", incerte + [_LE_ALTRA], key=f"le_c_sc_{ident}") if incerte else _LE_ALTRA
        if scelta == _LE_ALTRA:
            st.text_input("Com'è stata letta (copiala dal testo qui sopra)", key=f"le_c_da_{ident}", max_chars=80)
        st.text_input("Com'è giusta", key=f"le_c_a_{ident}", max_chars=80)
        st.text_input("Di chi è la grafia (facoltativo)", key=f"le_c_gr_{ident}", value=ris.get("grafia", ""), max_chars=60, placeholder="es. Dott. Nannetti")
        st.button("✅ Correggi", key=f"le_c_ok_{ident}", type="primary", on_click=_le_cb_correggi, args=(ident,))
        if corr:
            st.caption("Corrette finora: " + " · ".join(f"«{c.get('da')}» → «{c.get('a')}»" for c in corr[-12:]))
            st.button("↩️ Annulla l'ultima correzione", key=f"le_c_no_{ident}", on_click=_le_cb_togli_correzione, args=(ident,))


_LE_MODI = {"normale": "Normale · 1 lettura",
            "zone": "A zone ingrandite · per le pagine fitte (2-3 letture)",
            "doppia": "Doppia a confronto · segna dove le due letture non coincidono (2 letture)"}
_LE_MODI_NOTA = {"zone": "lettura a zone ingrandite", "doppia": "doppia lettura a confronto"}


def le_mostra_risultato(ident, ris):
    sez = le_sezioni(ris.get("grezzo", ""))
    corr = ris.get("correzioni") or []
    sez["testo"] = le_applica(sez["testo"], corr)
    n_inc, n_no = le_conta(sez["testo"])
    quando = ""
    try:
        quando = datetime.fromisoformat(ris.get("il", "")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    st.markdown(f"**📖 Testo letto**" + (f" · {_le_html.escape(sez['tipo'])}" if sez["tipo"] else ""))
    st.markdown("<div class='le-leg'>Testo normale = letto con sicurezza · <span class='le-inc'>arancione</span> = non del tutto sicuro"
                + (f" ({n_inc})" if n_inc else "") + " · <span class='le-no'>▮ illeggibile</span> = non riconosciuto" + (f" ({n_no})" if n_no else "")
                + (" · <span class='le-ok'>verde</span> = corretto da te" if corr else "") + "</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='le-box le-testo'>{le_html(sez['testo']) or '—'}</div>", unsafe_allow_html=True)
    if not _le_vuota(sez["no"]):
        st.markdown(f"<div class='le-box le-rosso'><b class='le-t'>🔴 Impossibile da riconoscere</b>{le_html(sez['no'])}</div>", unsafe_allow_html=True)
    if not _le_vuota(sez["incerto"]):
        st.markdown(f"<div class='le-box le-arancio'><b class='le-t'>🟠 Non del tutto sicuro</b>{le_html(sez['incerto'])}</div>", unsafe_allow_html=True)
    if not _le_vuota(sez["logica"]):
        st.markdown(f"<div class='le-box le-logica'><b class='le-t'>💡 Lettura per logica (ipotesi, in seconda battuta)</b>{le_html(sez['logica'])}</div>", unsafe_allow_html=True)
    _le_correzioni_ui(ident, ris, sez["testo"])
    semplice = le_testo_semplice(sez)
    st.download_button("⬇ Scarica il testo letto", semplice.encode("utf-8"), file_name=f"testo_letto_{ident[:8]}.txt", mime="text/plain", key=f"le_dl_{ident}", width="stretch")
    with st.expander("📋 Copia il testo (tocca l'icona in alto a destra del riquadro)"):
        st.code(semplice, language=None, wrap_lines=True)
    st.caption("Lettura automatica" + (f" del {quando}" if quando else "") + (f" · {ris.get('servizio')}" if ris.get("servizio") else "")
               + (f" · {_LE_MODI_NOTA[ris['modo']]}" if ris.get("modo") in _LE_MODI_NOTA else "")
               + ": può contenere errori. Per dosi, medicinali e diagnosi vale solo il documento originale e la parola del medico.")


def le_esegui(dati, modo, suggerimenti):
    """Fa la lettura nel modo scelto. Ritorna (grezzo, errore, nota). Se una parte riesce e un'altra no, tiene quella riuscita e lo dice nella nota."""
    pulita = le_pulisci(dati)
    if not pulita:
        return None, "immagine", ""
    parole = le_parole()
    if modo == "zone":
        fasce = le_zone(pulita)
        grezzi, primo_err = [], None
        for i, fz in enumerate(fasce):
            g, e = le_leggi(fz, suggerimenti, parole, zona=(i + 1, len(fasce)) if len(fasce) > 1 else None)
            grezzi.append(g)
            primo_err = primo_err or e
            if e in ("chiave", "pagamento", "limite_utente", "limite_app", "assente") and not any(grezzi):
                return None, e, ""
        if not any(grezzi):
            return None, primo_err or "rete", ""
        return le_unisci_zone(grezzi), None, ("" if all(grezzi) else "⚠️ Una fascia della pagina non è stata letta: nel testo è segnata in rosso. Puoi rifare la lettura.")
    g1, e1 = le_leggi(pulita, suggerimenti, parole)
    if e1:
        return None, e1, ""
    if modo == "doppia":
        g2, e2 = le_leggi(le_jpeg(dati) or pulita, suggerimenti, parole, temperatura=0.4)        # seconda lettura sulla pagina originale: due «sguardi» diversi
        if e2:
            return g1, None, "⚠️ La seconda lettura non è riuscita: ti mostro la prima (senza il confronto)."
        unito, n = le_confronta(g1, g2)
        return unito, None, (f"Le due letture non coincidono in {n} punt{'o' if n == 1 else 'i'}: li trovi in arancione." if n else "Le due letture coincidono in tutto il testo.")
    return g1, None, ""


def _le_cb_vai(ident):
    st.session_state.pop(f"le_errore_{ident}", None)
    st.session_state["le_consenso"] = True
    st.session_state[f"le_fai_{ident}"] = True


def _le_avvio(ident, gia_letta):
    """I campi prima della lettura: suggerimenti, tipo di lettura e il pulsante che la fa partire (la lettura NON parte mai da sola: non si consumano letture per sbaglio)."""
    if not st.session_state.get("le_consenso"):
        st.info(f"Per leggerla, **questa pagina viene inviata a {le_servizio()}** (un servizio esterno di intelligenza artificiale). Il file nell'app resta com'è.")
    st.text_input("💡 Cosa sai già di questa pagina? (facoltativo: aiuta molto)", key=f"le_sug_{ident}", max_chars=300,
                  placeholder="es. referto ginecologico del 2005, dott. Nannetti",
                  help="Tipo di documento, medico o ente, anno, argomento, parole che conosci già. Serve a capire meglio grafia e abbreviazioni.")
    st.radio("Tipo di lettura", list(_LE_MODI), format_func=lambda k: _LE_MODI[k], key=f"le_modo_{ident}")
    n_par = len(st.session_state.get("le_parole_mem") or [])
    st.caption("Prima di leggerla, la pagina viene ripulita da sola: raddrizzata, senza ombre né ingiallimento, più contrasto."
               + (f" Ricordo già {n_par} parol{'a' if n_par == 1 else 'e'} corrett{'a' if n_par == 1 else 'e'} da te." if n_par else ""))
    st.button("🔄 Rileggi adesso" if gia_letta else "🔍 Leggi adesso", key=f"le_go_{ident}", type="primary", on_click=_le_cb_vai, args=(ident,))


def le_pannello(ident, sorgente):
    ss = st.session_state
    if ss.pop(f"le_fai_{ident}", False) and le_attivo():          # è stato toccato «Leggi adesso»: la lettura si fa PRIMA di disegnare il resto
        modo = ss.get(f"le_modo_{ident}") if ss.get(f"le_modo_{ident}") in _LE_MODI else "normale"
        sug = str(ss.get(f"le_sug_{ident}") or "")
        with st.spinner({"zone": "Leggo la pagina a zone ingrandite… (fino a 2-3 minuti)", "doppia": "Leggo la pagina due volte e confronto… (fino a 2 minuti)"}.get(modo, "Sto leggendo con attenzione, parola per parola… (può volerci fino a un minuto)")):
            try:
                dati = sorgente() if callable(sorgente) else sorgente
            except Exception:
                dati = None
            grezzo, err, nota = le_esegui(dati, modo, sug) if dati else (None, "immagine", "")
        if err:
            ss[f"le_errore_{ident}"] = err                       # resta a schermo finché non si riprova (la pagina può ridisegnarsi subito dopo)
        else:
            ss.pop(f"le_errore_{ident}", None)
            vecchia = ss.get("le_ris_" + ident) or {}
            nuovo = {"grezzo": grezzo, "il": datetime.now().isoformat(timespec="seconds"), "servizio": le_servizio(), "modo": modo, "suggerimenti": sug, "nota": nota,
                     "correzioni": list(vecchia.get("correzioni") or []), "grafia": vecchia.get("grafia", "")}       # le correzioni già fatte valgono anche sulla nuova lettura
            if not le_salva(ident, nuovo):
                ss[f"le_nonsalvata_{ident}"] = True
    if ss.get(f"le_errore_{ident}"):
        _le_mostra_errore(ss[f"le_errore_{ident}"])
    if ss.get(f"le_nonsalvata_{ident}"):
        st.caption("Non sono riuscito a salvare la lettura: la vedi adesso, ma la prossima volta andrà rifatta.")
    ris = le_salvata(ident)
    if ris:
        if ris.get("nota"):
            (st.warning if str(ris["nota"]).startswith("⚠️") else st.info)(ris["nota"])
        le_mostra_risultato(ident, ris)
    if not le_attivo():
        if not ris:
            st.info("Per leggere la calligrafia serve l'**intelligenza artificiale**, che ora non è attiva. Il lettore di testo dell'app (gratuito, sempre acceso) riconosce solo lo stampato, non lo scritto a mano.")
            if "ad_guida_propria_chiave" in globals():
                with st.expander("🔑 Come attivarla (c'è anche la strada gratuita)", **({"_aperta": True} if getattr(st.expander, "_sempre_chiusa", False) else {"expanded": True})):
                    ad_guida_propria_chiave()
                    if "ad_campo_chiave_propria" in globals():
                        ad_campo_chiave_propria()
        return
    if ris:
        with st.expander("🔄 Rileggi (con suggerimenti o con una lettura più approfondita)"):
            _le_avvio(ident, True)
    else:
        _le_avvio(ident, False)


def le_pulsanti_pdf(dati, mostrate=3):
    """Per un PDF: il pulsante per le pagine che l'anteprima NON mostra (dalla quarta in poi)."""
    try:
        try:
            import pymupdf as _mu
        except Exception:
            import fitz as _mu
        doc = _mu.open(stream=dati, filetype="pdf")
        n = doc.page_count
        doc.close()
    except Exception:
        return
    base = hashlib.md5(dati).hexdigest()[:16]
    for i in range(mostrate, min(n, LE_MAX_PAGINE_PDF)):
        le_pulsante(f"{base}p{i + 1}", (lambda i=i: le_pagina_pdf(dati, i)), etichetta=f"🔍 Leggi lo scritto di pagina {i + 1}")


# ---------------------------------------------------------------------------------------------------------------------
# aggancio automatico: sotto ogni immagine grande mostrata con st.image(...)
# ---------------------------------------------------------------------------------------------------------------------
def _le_byte(x):
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    if isinstance(x, io.BytesIO):
        return x.getvalue()
    return None


if not getattr(st.image, "_lettore", False):
    _le_image_originale = st.image

    def _le_image(*a, **kw):
        voglio = kw.pop("_lettore", True)
        esito = _le_image_originale(*a, **kw)
        if not voglio or getattr(_LE_LOC, "dentro", False):
            return esito
        try:
            dati = _le_byte(a[0] if a else kw.get("image"))
            larg = kw.get("width")
            piccola = isinstance(larg, int) and not isinstance(larg, bool) and larg < 200
            if dati and len(dati) >= LE_MIN_BYTE and not piccola:
                getattr(st, "_le_pulsante", le_pulsante)(hashlib.md5(dati).hexdigest()[:20], dati)
        except Exception:
            pass
        return esito
    _le_image._lettore = True
    _le_image._sicura = True
    st.image = _le_image

st._le_pulsante = le_pulsante                      # sempre la versione più recente (il codice dell'app si ricarica a ogni ridisegnata)
