# -*- coding: utf-8 -*-
"""Foto del prodotto: un solo punto (in alto nella scheda Aggiungi) dove si scatta con la fotocamera POSTERIORE.
La foto viene scontornata (sfondo tolto) e addrizzata in modo automatico, poi mostrata AMPIA nel riquadro della scheda.
Caricato da app_dispensa.py dopo account.py e prima di parte3.py."""
import base64
import hashlib
import html
import json
import io

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageFilter, ImageOps


def _maschera_prodotto(bgr):
    """Trova il prodotto (GrabCut partendo da un rettangolo centrale). Ritorna una maschera 0/255 o None."""
    h, w = bgr.shape[:2]
    m = int(min(h, w) * 0.04)
    rett = (m, m, w - 2 * m, h - 2 * m)
    mask = np.zeros((h, w), np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(bgr, mask, rett, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    except Exception:
        return None
    m01 = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # pulizia: tolgo i puntini, chiudo i buchi, tengo solo la macchia piu' grande
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60) | 1,) * 2)
    m01 = cv2.morphologyEx(m01, cv2.MORPH_OPEN, k)
    m01 = cv2.morphologyEx(m01, cv2.MORPH_CLOSE, k)
    n, etich, stat, _ = cv2.connectedComponentsWithStats(m01)
    if n <= 1:
        return None
    grande = 1 + int(np.argmax(stat[1:, cv2.CC_STAT_AREA]))
    m01 = np.where(etich == grande, 255, 0).astype(np.uint8)
    # riempio i buchi interni
    cont, _ = cv2.findContours(m01, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cont:
        return None
    pieno = np.zeros_like(m01)
    cv2.drawContours(pieno, cont, -1, 255, cv2.FILLED)
    area = pieno.mean() / 255.0
    if area < 0.08 or area > 0.96:          # non ha trovato un prodotto sensato: meglio non rovinare la foto
        return None
    return pieno


def _angolo_da_raddrizzare(maschera):
    """Di quanto girare il prodotto per metterlo dritto. Si guardano i lati del contorno: la loro direzione media
    (modulo 90 gradi) dice quanto e' storto. Solo inclinazioni lievi: oggetti volutamente girati o irregolari restano come sono."""
    cont, _ = cv2.findContours(maschera, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cont:
        return 0.0
    c = max(cont, key=cv2.contourArea)
    (cx, cy), (rw, rh), _ = cv2.minAreaRect(c)
    if rw < 1 or rh < 1 or cv2.contourArea(c) / (rw * rh) < 0.62:      # forma irregolare (es. sacchetto): non giro
        return 0.0
    poli = cv2.approxPolyDP(c, 0.012 * cv2.arcLength(c, True), True)[:, 0, :].astype(np.float64)
    if len(poli) < 3:
        return 0.0
    vx = vy = 0.0
    for i in range(len(poli)):
        d = poli[(i + 1) % len(poli)] - poli[i]
        lung = float(np.hypot(*d))
        if lung < 0.18 * max(rw, rh):                                    # lati corti (angoli arrotondati, smussi): li ignoro
            continue
        teta = np.arctan2(d[1], d[0])
        vx += lung * np.cos(4 * teta)                                    # periodo di 90 gradi: i lati opposti e quelli ortogonali contano uguale
        vy += lung * np.sin(4 * teta)
    if vx == 0 and vy == 0:
        return 0.0
    ang = np.degrees(np.arctan2(vy, vx) / 4.0)                           # tra -45 e +45
    if abs(ang) < 1.5 or abs(ang) > 35:
        return 0.0
    return float(ang)


def _angolo_dal_testo(rgb, mask):
    """Inclinazione delle scritte piccole (le righe di testo, non i grandi loghi). Ritorna (angolo da applicare, affidabilita').
    Si isolano i tratti sottili, si scartano le lettere enormi dei loghi, si prova a girare e si sceglie l'angolo in cui
    le righe diventano orizzontali. Affidabilita' = quanto il risultato e' piu' netto che senza girare (1 = nessuna)."""
    h, w = mask.shape
    sc = 800.0 / max(h, w) if max(h, w) > 800 else 1.0
    g = cv2.cvtColor(cv2.resize(rgb, (max(1, int(w * sc)), max(1, int(h * sc))), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    mk = cv2.resize((mask > 127).astype(np.uint8) * 255, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_NEAREST)
    mk = cv2.erode(mk, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, g.shape[1] // 14) | 1,) * 2))   # via il bordo del prodotto
    if mk.mean() < 8:
        return 0.0, 1.0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(5, g.shape[1] // 80) | 1,) * 2)
    tratti = cv2.add(cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, k), cv2.morphologyEx(g, cv2.MORPH_TOPHAT, k))
    _, bn = cv2.threshold(tratti, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bn = cv2.bitwise_and(bn, mk)
    n, etich, stat, _ = cv2.connectedComponentsWithStats(bn)
    gh, gw = g.shape
    buone = np.zeros_like(bn)
    for i in range(1, n):
        x, y, ww, hh, area = stat[i]
        if hh <= 0.045 * gh and ww <= 0.25 * gw and area >= 6:              # solo lettere piccole
            buone[etich == i] = 255
    if (buone > 0).sum() < 300:
        return 0.0, 1.0
    lato = int(np.hypot(gh, gw)) + 2

    def punteggio(a):
        M = cv2.getRotationMatrix2D((gw / 2.0, gh / 2.0), a, 1.0)
        M[0, 2] += (lato - gw) / 2.0
        M[1, 2] += (lato - gh) / 2.0
        r = cv2.warpAffine(buone, M, (lato, lato), flags=cv2.INTER_LINEAR, borderValue=0)
        return float(np.var(r.astype(np.float32).sum(axis=1)))

    base = punteggio(0.0)
    if base <= 0:
        return 0.0, 1.0
    migliore, miglior_ang = base, 0.0
    for a in np.arange(-30.0, 30.01, 0.5):
        p = punteggio(a)
        if p > migliore:
            migliore, miglior_ang = p, float(a)
    for a in np.arange(miglior_ang - 0.5, miglior_ang + 0.51, 0.1):         # rifinitura
        p = punteggio(a)
        if p > migliore:
            migliore, miglior_ang = p, float(a)
    return miglior_ang, migliore / base


def _affina_bordo(rgb, alfa):
    """Fa aderire il bordo ai contorni veri della foto: GrabCut lavora solo in una fascia stretta attorno alla maschera AI."""
    try:
        h, w = alfa.shape
        sc = 560.0 / max(h, w) if max(h, w) > 560 else 1.0
        piccola = cv2.resize(rgb, (max(1, int(w * sc)), max(1, int(h * sc))), interpolation=cv2.INTER_AREA)
        b = (cv2.resize(alfa, (piccola.shape[1], piccola.shape[0]), interpolation=cv2.INTER_AREA) > 127).astype(np.uint8)
        fascia = max(3, int(0.022 * max(piccola.shape[:2])))
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * fascia + 1,) * 2)
        gc = np.full(b.shape, cv2.GC_PR_BGD, np.uint8)
        gc[b > 0] = cv2.GC_PR_FGD
        gc[cv2.erode(b, k) > 0] = cv2.GC_FGD
        gc[cv2.dilate(b, k) == 0] = cv2.GC_BGD
        bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(cv2.cvtColor(piccola, cv2.COLOR_RGB2BGR), gc, None, bg, fg, 4, cv2.GC_INIT_WITH_MASK)
        nuovo = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        n, etich, stat, _ = cv2.connectedComponentsWithStats(nuovo)
        if n <= 1:
            return alfa
        nuovo = np.where(etich == 1 + int(np.argmax(stat[1:, cv2.CC_STAT_AREA])), 255, 0).astype(np.uint8)
        cont, _ = cv2.findContours(nuovo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        pieno = np.zeros_like(nuovo)
        cv2.drawContours(pieno, cont, -1, 255, cv2.FILLED)
        rapporto = pieno.sum() / max(1.0, float(b.sum()) * 255.0)
        if rapporto < 0.9 or rapporto > 1.08:                              # ha esagerato: tengo la maschera AI
            return alfa
        pieno = cv2.morphologyEx(pieno, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        pieno = cv2.resize(pieno, (w, h), interpolation=cv2.INTER_LINEAR)
        return cv2.GaussianBlur(pieno, (0, 0), 1.1)
    except Exception:
        return alfa


def _ruota_piccola(img, ang, interp, bordo=0):
    h, w = img.shape[:2]
    diag = int(np.hypot(h, w)) + 4
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), ang, 1.0)
    M[0, 2] += (diag - w) / 2.0
    M[1, 2] += (diag - h) / 2.0
    return cv2.warpAffine(img, M, (diag, diag), flags=interp, borderValue=bordo)


def _angolo_totale(rgb, mask):
    """Si stima l'angolo, si gira una copia piccola e si misura di nuovo: fino a 3 volte, cosi' l'errore residuo sparisce."""
    h, w = mask.shape
    sc = 700.0 / max(h, w) if max(h, w) > 700 else 1.0
    r = cv2.resize(rgb, (max(1, int(w * sc)), max(1, int(h * sc))), interpolation=cv2.INTER_AREA)
    m = cv2.resize(mask, (r.shape[1], r.shape[0]), interpolation=cv2.INTER_AREA)
    totale = 0.0
    for _ in range(3):
        a = _angolo_scelto(r, m)
        if not a or abs(totale + a) > 60:
            break
        totale += a
        r = _ruota_piccola(r, a, cv2.INTER_LINEAR)
        m = _ruota_piccola(m, a, cv2.INTER_LINEAR)
        ys, xs = np.where(m > 40)
        if len(xs):
            r, m = r[ys.min():ys.max() + 1, xs.min():xs.max() + 1], m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return totale


def _angolo_scelto(rgb, mask):
    """Prima le scritte (sono quello che l'utente legge): se sono chiare, comandano loro. Altrimenti, per scatole e lattine, i lati dritti."""
    binaria = (mask > 127).astype(np.uint8) * 255
    cont, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cont:
        return 0.0
    c = max(cont, key=cv2.contourArea)
    (_, _), (rw, rh), _ = cv2.minAreaRect(c)
    rettangolare = rw > 1 and rh > 1 and cv2.contourArea(c) / (rw * rh) >= 0.9
    ang_testo, fiducia = _angolo_dal_testo(rgb, mask)
    if abs(ang_testo) < 0.7:
        ang_testo = 0.0
    if ang_testo and fiducia >= 1.25 and abs(ang_testo) <= 30:
        return ang_testo
    ang_lati = _angolo_da_raddrizzare(binaria)
    if rettangolare and ang_lati:
        return ang_lati
    if ang_testo and fiducia >= 1.08 and abs(ang_testo) <= 30:
        return ang_testo
    return ang_lati


_MODELLI = [("https://github.com/danielgatis/rembg/releases/download/v0.0.0/silueta.onnx", "/tmp/silueta.onnx", 40_000_000),
            ("https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx", "/tmp/u2netp.onnx", 4_000_000)]


@st.cache_resource(show_spinner=False)
def _sessione_modello():
    """Modello AI che riconosce il prodotto in primo piano (prima 'silueta', piu' preciso; se non si scarica, il piu' leggero). None se non disponibile."""
    try:
        import os
        import onnxruntime as ort
        import requests
    except Exception:
        return None
    for url, percorso, minimo in _MODELLI:
        try:
            if not os.path.exists(percorso) or os.path.getsize(percorso) < minimo:
                r = requests.get(url, timeout=90)
                r.raise_for_status()
                with open(percorso + ".tmp", "wb") as f:
                    f.write(r.content)
                os.replace(percorso + ".tmp", percorso)
            return ort.InferenceSession(percorso, providers=["CPUExecutionProvider"])
        except Exception:
            continue
    return None


def _toglie_code(pieno):
    """Toglie le 'code' che sporgono dal prodotto (un lembo di tovaglia, un'ombra lunga): si apre la forma con un cerchio grande
    e si riporta indietro solo un po' di bordo, cosi' gli angoli restano. Se la forma e' sottile non si tocca niente."""
    ys, xs = np.where(pieno > 0)
    if len(xs) == 0:
        return pieno
    bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    sc = 400.0 / max(pieno.shape) if max(pieno.shape) > 400 else 1.0
    p = cv2.resize(pieno, (max(1, int(pieno.shape[1] * sc)), max(1, int(pieno.shape[0] * sc))), interpolation=cv2.INTER_AREA)
    p = (p > 127).astype(np.uint8) * 255
    lato = min(bw, bh) * sc
    r = int(0.14 * lato)
    if r < 3:
        return pieno
    aperto = cv2.morphologyEx(p, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2))
    if aperto.sum() < 0.65 * p.sum():                                        # forma sottile o strana: non toccare
        return pieno
    n, etich, stat, _ = cv2.connectedComponentsWithStats(aperto)
    if n <= 1:
        return pieno
    aperto = np.where(etich == 1 + int(np.argmax(stat[1:, cv2.CC_STAT_AREA])), 255, 0).astype(np.uint8)
    r2 = max(2, int(0.045 * lato))
    ripristino = cv2.dilate(aperto, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r2 + 1,) * 2))
    ripristino = cv2.resize(ripristino, (pieno.shape[1], pieno.shape[0]), interpolation=cv2.INTER_LINEAR)
    return cv2.bitwise_and(pieno, (ripristino > 127).astype(np.uint8) * 255)


def _maschera_ai(rgb):
    """Trasparenza (0-255) del prodotto con il modello AI, oppure None se non riesce / non trova un prodotto sensato."""
    sess = _sessione_modello()
    if sess is None:
        return None
    try:
        h, w = rgb.shape[:2]
        x = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        x = ((x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)).transpose(2, 0, 1)[None]
        y = sess.run(None, {sess.get_inputs()[0].name: x.astype(np.float32)})[0][0, 0]
        y = (y - y.min()) / (y.max() - y.min() + 1e-8)
        y = cv2.resize(y, (w, h), interpolation=cv2.INTER_CUBIC)
    except Exception:
        return None
    sicuro = (y > 0.5).astype(np.uint8) * 255
    n, etich, stat, _ = cv2.connectedComponentsWithStats(sicuro)
    if n <= 1:
        return None
    sicuro = np.where(etich == 1 + int(np.argmax(stat[1:, cv2.CC_STAT_AREA])), 255, 0).astype(np.uint8)
    cont, _ = cv2.findContours(sicuro, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pieno = np.zeros_like(sicuro)
    cv2.drawContours(pieno, cont, -1, 255, cv2.FILLED)                     # niente buchi dentro il prodotto
    area = pieno.mean() / 255.0
    if area < 0.05 or area > 0.97:
        return None
    pieno = _toglie_code(pieno)
    cont, _ = cv2.findContours(pieno, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cont:
        return None
    grande = max(cont, key=cv2.contourArea)
    guscio = np.zeros_like(pieno)
    cv2.drawContours(guscio, [cv2.convexHull(grande)], -1, 255, cv2.FILLED)
    if 0 < pieno.mean() / max(guscio.mean(), 1e-6) <= 1.0 and guscio.mean() / max(pieno.mean(), 1e-6) <= 1.22:
        pieno = guscio                                                       # prodotto quasi convesso: tolgo le "morsi" ai bordi
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    vicino = cv2.dilate(pieno, k)                                          # bordo morbido ma solo accanto al prodotto
    morbido = (np.clip((y - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8)
    alfa = np.where(pieno > 0, 255, np.minimum(morbido, vicino)).astype(np.uint8)
    return _affina_bordo(rgb, cv2.GaussianBlur(alfa, (0, 0), 0.9))


def _maschera_classica_grande(bgr):
    """GrabCut su una copia piccola, riportata alla misura della foto (0/255), oppure None."""
    h, w = bgr.shape[:2]
    scala = 360.0 / max(h, w) if max(h, w) > 360 else 1.0
    piccola = cv2.resize(bgr, (max(1, int(w * scala)), max(1, int(h * scala))), interpolation=cv2.INTER_AREA)
    mp = _maschera_prodotto(piccola)
    if mp is None:
        return None
    m = cv2.resize(mp, (w, h), interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), 1.6)
    return np.clip((m.astype(np.float32) - 110) * 255 / 90, 0, 255).astype(np.uint8)


def _scegli_maschera(rgb, bgr):
    """Sceglie come ritagliare. Ritorna (maschera, modo): 'ai' (sagoma precisa), 'classica', 'scatola' (il prodotto riempie la foto:
    si tiene tutto) oppure (None, 'intera') se non si capisce dov'e' il prodotto.
    Il modello AI a volte riconosce solo un dettaglio (per esempio il fungo disegnato sulla busta del risotto): se la sagoma e' piccola
    e dentro la foto c'e' un oggetto molto piu' grande che la contiene, vale l'oggetto grande."""
    ai = _maschera_ai(rgb)
    area_ai = float((ai > 127).mean()) if ai is not None else 0.0
    if ai is not None and area_ai >= 0.22:
        return ai, "ai"
    cl = _maschera_classica_grande(bgr)
    area_cl = float((cl > 127).mean()) if cl is not None else 0.0
    if cl is not None:
        contiene = 1.0 if ai is None else float(((ai > 127) & (cl > 127)).sum()) / max(1.0, float((ai > 127).sum()))
        if area_cl >= max(0.10, 1.8 * area_ai) and contiene >= 0.6:
            return (cl, "scatola") if area_cl >= 0.45 else (cl, "classica")
    if ai is not None and area_ai >= 0.08:
        return ai, "ai"
    return None, "intera"


def controlla_foto(dati):
    """Controlla se la foto e' utilizzabile. Ritorna la lista dei problemi: 'piccola', 'sfocata', 'scura', 'chiara', 'vuota' (lista vuota = va bene)."""
    problemi = []
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
        if min(img.size) < 360:
            problemi.append("piccola")
        g = img.convert("L")
        g.thumbnail((800, 800))
        a = np.array(g)
        media = float(a.mean())
        contrasto = float(np.percentile(a, 98) - np.percentile(a, 2))
        nitidezza = float(cv2.Laplacian(a, cv2.CV_64F).var())
        if contrasto < 12 and nitidezza < 5:
            problemi.append("vuota")
        elif media < 38 or (media < 60 and contrasto < 28):
            problemi.append("scura")
        elif media > 238 and contrasto < 40:
            problemi.append("chiara")
        elif nitidezza < 35:
            problemi.append("sfocata")
    except Exception:
        return []                                              # se non riesco a controllare, non blocco niente
    return problemi


def _scontorna_completa(dati, lato=720, mantieni=False):
    """Da una foto (bytes) a (immagine WebP trasparente ritagliata e addrizzata, modo). mantieni=True: tutta la foto, senza togliere lo sfondo."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    img.thumbnail((1200, 1200))
    rgb = np.array(img)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    mask, modo = (None, "intera") if mantieni else _scegli_maschera(rgb, bgr)
    if mask is None:
        rgba = np.dstack([rgb, np.full((h, w), 255, np.uint8)])
    elif modo == "scatola":
        # il prodotto riempie la foto: si ritaglia a rettangolo (con un po' di margine) e niente trasparenze, cosi' non si perde nulla
        ys, xs = np.where(mask > 127)
        m = int(0.04 * max(xs.max() - xs.min(), ys.max() - ys.min()))
        x0, x1, y0, y1 = max(0, xs.min() - m), min(w, xs.max() + m + 1), max(0, ys.min() - m), min(h, ys.max() + m + 1)
        rgba = np.dstack([rgb, np.full((h, w), 255, np.uint8)])[y0:y1, x0:x1]
    else:
        rgba = np.dstack([rgb, mask])
        ang = _angolo_totale(rgb, mask)
        if ang:
            diag = int(np.hypot(h, w)) + 4
            M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
            M[0, 2] += (diag - w) / 2
            M[1, 2] += (diag - h) / 2
            rgba = cv2.warpAffine(rgba, M, (diag, diag), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
        ys, xs = np.where(rgba[:, :, 3] > 40)
        if len(xs):
            marg = int(0.03 * max(xs.max() - xs.min(), ys.max() - ys.min()))
            y0, y1 = max(0, ys.min() - marg), min(rgba.shape[0], ys.max() + marg + 1)
            x0, x1 = max(0, xs.min() - marg), min(rgba.shape[1], xs.max() + marg + 1)
            rgba = rgba[y0:y1, x0:x1]
    out = Image.fromarray(rgba, "RGBA")
    out.thumbnail((lato, lato), Image.LANCZOS)
    nitida = out.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=3))   # un po' piu' nitida
    nitida.putalpha(out.getchannel("A"))
    out = nitida
    buf = io.BytesIO()
    out.save(buf, "WEBP", quality=86, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(), modo


def scontorna_e_addrizza(dati, lato=720):
    """Da una foto (bytes) a una immagine WebP trasparente, ritagliata sul prodotto e addrizzata. Ritorna 'data:image/webp;base64,...'."""
    return _scontorna_completa(dati, lato)[0]


# ---------------------------------------------------------------------
# Campo foto (uno solo, in alto) usato da "Aggiungi" e da "Modifica"
# ---------------------------------------------------------------------
_VERSIONE_FOTO = 10


def _foto_lavorata_modo(dati, mantieni=False):
    """Scontorna e addrizza una sola volta per ogni foto (la scelta resta in memoria durante la sessione). Ritorna (uri, modo)."""
    mem = st.session_state.setdefault("_foto_lavorate", {})
    chiave = (hash(dati), bool(mantieni), _VERSIONE_FOTO)      # se cambia il metodo, le vecchie foto in memoria non valgono piu'
    if chiave not in mem:
        if len(mem) >= 4:
            mem.pop(next(iter(mem)))
        try:
            mem[chiave] = _scontorna_completa(dati, mantieni=mantieni)
        except Exception:
            mem[chiave] = (foto_a_data_uri(dati, 720), "intera")   # se qualcosa va storto resta la foto normale
    return mem[chiave]


def _foto_lavorata(dati):
    return _foto_lavorata_modo(dati)[0]


def _ritocco(uri, grado, sopra, sotto, sinistra, destra):
    """Correzione a mano sulla foto gia' scontornata: taglia i bordi (in %) e gira di 'grado' gradi. Ritorna un nuovo data URI."""
    if not grado and not (sopra or sotto or sinistra or destra):
        return uri
    im = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("RGBA")
    w, h = im.size
    x0, x1 = int(w * sinistra / 100.0), w - int(w * destra / 100.0)
    y0, y1 = int(h * sopra / 100.0), h - int(h * sotto / 100.0)
    if x1 - x0 > 20 and y1 - y0 > 20:
        im = im.crop((x0, y0, x1, y1))
    if grado:
        im = im.rotate(grado, resample=Image.BICUBIC, expand=True)           # positivo = in senso antiorario
    a = np.array(im)
    ys, xs = np.where(a[:, :, 3] > 40)
    if len(xs):
        marg = int(0.02 * max(xs.max() - xs.min(), ys.max() - ys.min()))
        im = im.crop((max(0, xs.min() - marg), max(0, ys.min() - marg), min(im.width, xs.max() + marg + 1), min(im.height, ys.max() + marg + 1)))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=86, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


_EDITOR_JS = r'''(function () {
  var IMG_SRC = __IMG__, ETICHETTA = __LABEL__, LBL_SALVA = __L_SALVA__, LBL_SALVATO = __L_SALVATO__, LBL_NONSALVATO = __L_NONSALVATO__;
  var cv = document.getElementById('cv'), rl = document.getElementById('rl');
  var cx = cv.getContext('2d'), rx = rl.getContext('2d');
  var img = new Image(), pronto = false;
  var ang = 0, c = {x0: 0, y0: 0, x1: 1, y1: 1};
  var PX_GRADO = 13, MAXANG = 45, timer = null, ultimo = null, dpr = Math.max(1, window.devicePixelRatio || 1);

  function parentWin() {
    var w = window;
    for (var i = 0; i < 4; i++) {
      try { if (w.document.querySelector('[data-testid="stApp"],.stApp')) return w; } catch (e) {}
      if (w.parent === w) break;
      w = w.parent;
    }
    return null;
  }
  function campo() {
    var P = parentWin();
    if (!P) return null;
    return P.document.querySelector('input[aria-label="' + ETICHETTA + '"]');
  }
  function scrivi(v) {
    var P = parentWin(), el = campo();
    if (!P || !el || el.value === v) return;
    var setter = Object.getOwnPropertyDescriptor(P.HTMLInputElement.prototype, 'value').set;
    setter.call(el, v);
    el.dispatchEvent(new P.Event('input', {bubbles: true}));
    el.dispatchEvent(new P.KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
    el.dispatchEvent(new P.FocusEvent('focusout', {bubbles: true}));
  }
  function valore() {
    return ang.toFixed(2) + '|' + c.x0.toFixed(4) + '|' + c.y0.toFixed(4) + '|' + c.x1.toFixed(4) + '|' + c.y1.toFixed(4);
  }
  var stato = 'neutro';
  function aggiornaStato() {
    var b = document.getElementById('salva'), s = document.getElementById('stato');
    if (stato === 'sporco') { b.className = ''; b.innerHTML = LBL_SALVA; s.className = 'su'; s.textContent = LBL_NONSALVATO; }
    else if (stato === 'salvato') { b.className = 'ok'; b.innerHTML = '&#10004; ' + LBL_SALVATO; s.className = ''; s.textContent = ''; }
    else { b.className = ''; b.innerHTML = LBL_SALVA; s.className = ''; s.textContent = ''; }
  }
  function conferma() { stato = 'sporco'; aggiornaStato(); }
  function salva() { scrivi(valore()); stato = 'salvato'; aggiornaStato(); }
  function leggiIniziale() {
    try {
      var el = campo();
      if (el && el.value) {
        var p = el.value.split('|').map(parseFloat);
        if (p.length === 5 && p.every(function (n) { return isFinite(n); })) {
          ang = Math.max(-MAXANG, Math.min(MAXANG, p[0]));
          c = {x0: p[1], y0: p[2], x1: p[3], y1: p[4]};
        }
      }
    } catch (e) {}
  }

  function misure() {
    var a = ang * Math.PI / 180, co = Math.abs(Math.cos(a)), si = Math.abs(Math.sin(a));
    var W = img.width * co + img.height * si, H = img.width * si + img.height * co;
    var vw = cv.clientWidth, vh = cv.clientHeight, m = 14;
    var s = Math.min((vw - 2 * m) / W, (vh - 2 * m) / H);
    return {W: W, H: H, s: s, bx: (vw - W * s) / 2, by: (vh - H * s) / 2, vw: vw, vh: vh};
  }
  function disegna() {
    if (!pronto) return;
    var m = misure();
    cx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cx.clearRect(0, 0, m.vw, m.vh);
    cx.fillStyle = '#edf7f1'; cx.fillRect(0, 0, m.vw, m.vh);
    cx.save();
    cx.translate(m.bx + m.W * m.s / 2, m.by + m.H * m.s / 2);
    cx.rotate(-ang * Math.PI / 180);
    cx.drawImage(img, -img.width * m.s / 2, -img.height * m.s / 2, img.width * m.s, img.height * m.s);
    cx.restore();
    var X0 = m.bx + c.x0 * m.W * m.s, Y0 = m.by + c.y0 * m.H * m.s, X1 = m.bx + c.x1 * m.W * m.s, Y1 = m.by + c.y1 * m.H * m.s;
    cx.fillStyle = 'rgba(8,30,20,.55)';
    cx.fillRect(0, 0, m.vw, Y0); cx.fillRect(0, Y1, m.vw, m.vh - Y1);
    cx.fillRect(0, Y0, X0, Y1 - Y0); cx.fillRect(X1, Y0, m.vw - X1, Y1 - Y0);
    cx.strokeStyle = 'rgba(255,255,255,.95)'; cx.lineWidth = 1.5; cx.strokeRect(X0, Y0, X1 - X0, Y1 - Y0);
    cx.strokeStyle = 'rgba(255,255,255,.35)'; cx.lineWidth = 1;
    for (var i = 1; i < 3; i++) {
      cx.beginPath(); cx.moveTo(X0 + (X1 - X0) * i / 3, Y0); cx.lineTo(X0 + (X1 - X0) * i / 3, Y1); cx.stroke();
      cx.beginPath(); cx.moveTo(X0, Y0 + (Y1 - Y0) * i / 3); cx.lineTo(X1, Y0 + (Y1 - Y0) * i / 3); cx.stroke();
    }
    cx.strokeStyle = '#fff'; cx.lineWidth = 4; var L = 20;
    [[X0, Y0, 1, 1], [X1, Y0, -1, 1], [X0, Y1, 1, -1], [X1, Y1, -1, -1]].forEach(function (p) {
      cx.beginPath(); cx.moveTo(p[0], p[1] + p[3] * L); cx.lineTo(p[0], p[1]); cx.lineTo(p[0] + p[2] * L, p[1]); cx.stroke();
    });
    [[(X0 + X1) / 2, Y0, 1], [(X0 + X1) / 2, Y1, 1], [X0, (Y0 + Y1) / 2, 0], [X1, (Y0 + Y1) / 2, 0]].forEach(function (p) {
      cx.beginPath();
      if (p[2]) { cx.moveTo(p[0] - 14, p[1]); cx.lineTo(p[0] + 14, p[1]); } else { cx.moveTo(p[0], p[1] - 14); cx.lineTo(p[0], p[1] + 14); }
      cx.stroke();
    });
    document.getElementById('val').textContent = (ang > 0 ? '+' : '') + ang.toFixed(1) + '\u00b0';
    disegnaRighello();
  }
  function disegnaRighello() {
    var w = rl.clientWidth, h = rl.clientHeight, mid = w / 2;
    rx.setTransform(dpr, 0, 0, dpr, 0, 0);
    rx.clearRect(0, 0, w, h);
    rx.fillStyle = '#ffffff'; rx.fillRect(0, 0, w, h);
    rx.textAlign = 'center'; rx.font = '600 11px system-ui,sans-serif';
    for (var v = -MAXANG; v <= MAXANG; v += 1) {
      var x = mid + (v - ang) * PX_GRADO;
      if (x < -10 || x > w + 10) continue;
      var lungo = (v % 5 === 0);
      rx.strokeStyle = lungo ? '#0f766e' : '#8db8ae'; rx.lineWidth = lungo ? 2 : 1;
      rx.beginPath(); rx.moveTo(x, h - 8); rx.lineTo(x, h - (lungo ? 28 : 18)); rx.stroke();
      if (v % 10 === 0) { rx.fillStyle = '#35564a'; rx.fillText(String(v), x, 16); }
    }
    rx.strokeStyle = '#f59e0b'; rx.lineWidth = 3;
    rx.beginPath(); rx.moveTo(mid, 22); rx.lineTo(mid, h - 4); rx.stroke();
  }
  function ridimensiona() {
    [cv, rl].forEach(function (el) { el.width = Math.round(el.clientWidth * dpr); el.height = Math.round(el.clientHeight * dpr); });
    disegna();
  }

  // ----- cornice di ritaglio -----
  var modo = null, inizio = null;
  function pos(e) { var r = cv.getBoundingClientRect(); return {x: e.clientX - r.left, y: e.clientY - r.top}; }
  function tocco(p) {
    var m = misure(), T = 26;
    var X0 = m.bx + c.x0 * m.W * m.s, Y0 = m.by + c.y0 * m.H * m.s, X1 = m.bx + c.x1 * m.W * m.s, Y1 = m.by + c.y1 * m.H * m.s;
    var nx0 = Math.abs(p.x - X0) < T, nx1 = Math.abs(p.x - X1) < T, ny0 = Math.abs(p.y - Y0) < T, ny1 = Math.abs(p.y - Y1) < T;
    var dentroX = p.x > X0 - T && p.x < X1 + T, dentroY = p.y > Y0 - T && p.y < Y1 + T;
    var h = '';
    if (ny0 && dentroX) h += 'n'; else if (ny1 && dentroX) h += 's';
    if (nx0 && dentroY) h += 'w'; else if (nx1 && dentroY) h += 'e';
    if (h) return h;
    if (p.x > X0 && p.x < X1 && p.y > Y0 && p.y < Y1) return 'm';
    return null;
  }
  cv.addEventListener('pointerdown', function (e) {
    var p = pos(e); modo = tocco(p);
    if (!modo) return;
    inizio = {p: p, c: {x0: c.x0, y0: c.y0, x1: c.x1, y1: c.y1}};
    cv.setPointerCapture(e.pointerId); e.preventDefault();
  });
  cv.addEventListener('pointermove', function (e) {
    if (!modo) return;
    var m = misure(), p = pos(e), dx = (p.x - inizio.p.x) / (m.W * m.s), dy = (p.y - inizio.p.y) / (m.H * m.s), o = inizio.c, MIN = 0.1;
    var n = {x0: o.x0, y0: o.y0, x1: o.x1, y1: o.y1};
    if (modo === 'm') {
      var w = o.x1 - o.x0, h = o.y1 - o.y0;
      n.x0 = Math.max(0, Math.min(1 - w, o.x0 + dx)); n.x1 = n.x0 + w;
      n.y0 = Math.max(0, Math.min(1 - h, o.y0 + dy)); n.y1 = n.y0 + h;
    } else {
      if (modo.indexOf('w') >= 0) n.x0 = Math.max(0, Math.min(o.x1 - MIN, o.x0 + dx));
      if (modo.indexOf('e') >= 0) n.x1 = Math.min(1, Math.max(o.x0 + MIN, o.x1 + dx));
      if (modo.indexOf('n') >= 0) n.y0 = Math.max(0, Math.min(o.y1 - MIN, o.y0 + dy));
      if (modo.indexOf('s') >= 0) n.y1 = Math.min(1, Math.max(o.y0 + MIN, o.y1 + dy));
    }
    c = n; disegna(); e.preventDefault();
  });
  function fine(e) { if (modo) { modo = null; conferma(); } }
  cv.addEventListener('pointerup', fine); cv.addEventListener('pointercancel', fine);

  // ----- righello: si trascina per ruotare -----
  var rIn = null;
  rl.addEventListener('pointerdown', function (e) { rIn = {x: e.clientX, a: ang}; rl.setPointerCapture(e.pointerId); e.preventDefault(); });
  rl.addEventListener('pointermove', function (e) {
    if (!rIn) return;
    ang = Math.max(-MAXANG, Math.min(MAXANG, Math.round((rIn.a - (e.clientX - rIn.x) / PX_GRADO) * 10) / 10));
    c = {x0: 0, y0: 0, x1: 1, y1: 1};                 // dopo aver girato si ritaglia di nuovo
    disegna(); e.preventDefault();
  });
  function fineR() { if (rIn) { rIn = null; conferma(); } }
  rl.addEventListener('pointerup', fineR); rl.addEventListener('pointercancel', fineR);

  function passo(d) { ang = Math.max(-MAXANG, Math.min(MAXANG, Math.round((ang + d) * 10) / 10)); c = {x0: 0, y0: 0, x1: 1, y1: 1}; disegna(); conferma(); }
  document.getElementById('meno').addEventListener('click', function () { passo(-0.5); });
  document.getElementById('piu').addEventListener('click', function () { passo(0.5); });
  document.getElementById('reset').addEventListener('click', function () { ang = 0; c = {x0: 0, y0: 0, x1: 1, y1: 1}; disegna(); salva(); });
  document.getElementById('salva').addEventListener('click', salva);

  window.addEventListener('resize', ridimensiona);
  img.onload = function () { pronto = true; leggiIniziale(); ridimensiona(); aggiornaStato(); };
  img.src = IMG_SRC;
})();
'''


_EDITOR_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;background:transparent;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#10261a;-webkit-user-select:none;user-select:none}
#box{width:100%;max-width:600px;margin:0 auto}
#cv{width:100%;height:340px;display:block;border-radius:18px;touch-action:none;box-shadow:0 6px 16px rgba(0,60,50,.15)}
#rl{width:100%;height:62px;display:block;margin-top:10px;border-radius:16px;touch-action:none;box-shadow:inset 0 0 0 2px #cfe8de}
.riga{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-top:10px}
#val{min-width:84px;text-align:center;font-weight:900;font-size:1.15rem;color:#0f766e}
button{flex:1;min-height:46px;border-radius:999px;border:2px solid rgba(13,148,136,.45);background:#fff;color:#0f766e;font-weight:800;font-size:1rem;box-shadow:0 3px 0 rgba(0,100,90,.2)}
button:active{transform:translateY(2px);box-shadow:none}
#reset{flex:1.4}
#salva{width:100%;flex:none;margin-top:10px;min-height:54px;border:0;color:#fff;font-size:1.1rem;background:linear-gradient(135deg,#00a98f,#0288d1);box-shadow:0 4px 0 rgba(0,70,90,.35)}
#salva.ok{background:linear-gradient(135deg,#43a047,#1b7a2e);box-shadow:0 4px 0 rgba(10,70,20,.4)}
#stato{min-height:18px;margin-top:6px;text-align:center;font-weight:800;font-size:.85rem;color:#b45309}
.nota{margin-top:8px;text-align:center;font-size:.78rem;font-weight:700;opacity:.65}
</style></head><body><div id="box">
<canvas id="cv"></canvas>
<canvas id="rl"></canvas>
<div class="riga"><button id="meno">&minus;0,5&deg;</button><div id="val">0&deg;</div><button id="piu">+0,5&deg;</button><button id="reset">&#8634; __RIPRISTINA__</button></div>
<button id="salva">__SALVA__</button><div id="stato"></div>
<div class="nota">__NOTA__</div>
</div>
<script>__JS__</script></body></html>"""


def _editor_html(uri, etichetta):
    js = (_EDITOR_JS.replace("__IMG__", json.dumps(uri)).replace("__LABEL__", json.dumps(etichetta))
          .replace("__L_SALVA__", json.dumps("\U0001F4BE " + t("Salva posizione e ritaglio")))
          .replace("__L_SALVATO__", json.dumps(t("Salvato")))
          .replace("__L_NONSALVATO__", json.dumps(t("Modifiche non ancora salvate"))))
    return (_EDITOR_HTML.replace("__RIPRISTINA__", html.escape(t("Ripristina")).encode("ascii", "xmlcharrefreplace").decode())
            .replace("__NOTA__", html.escape(t("Trascina il righello per raddrizzare · trascina la cornice per tagliare · poi tocca Salva")).encode("ascii", "xmlcharrefreplace").decode())
            .replace("__SALVA__", html.escape("\U0001F4BE " + t("Salva posizione e ritaglio")).encode("ascii", "xmlcharrefreplace").decode())
            .replace("__JS__", js))


def _ritocco_params(uri, params):
    """Applica il ritocco deciso nell'editor: 'angolo|x0|y0|x1|y1' (angolo positivo = antiorario; ritaglio in frazioni dell'immagine girata)."""
    try:
        a, x0, y0, x1, y1 = [float(v) for v in str(params).split("|")]
    except Exception:
        return uri
    a = max(-45.0, min(45.0, a))
    x0, y0, x1, y1 = [max(0.0, min(1.0, v)) for v in (x0, y0, x1, y1)]
    if x1 - x0 < 0.05 or y1 - y0 < 0.05 or (abs(a) < 0.05 and x0 < 0.001 and y0 < 0.001 and x1 > 0.999 and y1 > 0.999):
        return uri
    im = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("RGBA")
    if abs(a) >= 0.05:
        im = im.rotate(a, resample=Image.BICUBIC, expand=True)
    w, h = im.size
    im = im.crop((int(round(x0 * w)), int(round(y0 * h)), int(round(x1 * w)), int(round(y1 * h))))
    arr = np.array(im)
    ys, xs = np.where(arr[:, :, 3] > 40)
    if len(xs):
        marg = int(0.02 * max(xs.max() - xs.min(), ys.max() - ys.min()))
        im = im.crop((max(0, xs.min() - marg), max(0, ys.min() - marg), min(im.width, xs.max() + marg + 1), min(im.height, ys.max() + marg + 1)))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=86, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def _mostra_editor(codice, altezza=650):
    if hasattr(st, "iframe"):
        st.iframe(codice, height=altezza)
    else:
        import streamlit.components.v1 as _comp_editor
        _comp_editor.html(codice, height=altezza)


def foto_ampia_html(src):
    return f"<div class='foto-ampia'><img src='{html.escape(src, quote=True)}' alt=''></div>"


_FP_IT = {
    "foto_ricevuta": "📥 Foto ricevuta: {nome} ({kb} KB)", "foto_elimina": "🗑️ Elimina questa foto",
    "foto_tolta": "Foto eliminata. Scegline o scattane un'altra con i pulsanti qui sopra.",
    "foto_tieni": "Tieni tutta la foto (non togliere lo sfondo)", "foto_usa_comunque": "✅ Usa comunque questa foto",
    "foto_problema": "⚠️ Questa foto non va bene:", "foto_consiglio": "Eliminala e fanne un'altra: più luce, telefono fermo, prodotto ben centrato.",
    "foto_p_piccola": "è troppo piccola", "foto_p_sfocata": "è sfocata", "foto_p_scura": "è troppo scura", "foto_p_chiara": "è troppo chiara",
    "foto_p_vuota": "sembra vuota (non si vede il prodotto)",
    "foto_scatola": "Il prodotto riempie la foto: ho tenuto tutta la confezione. Se non va bene, spunta «Tieni tutta la foto» o usa la cornice.",
}


def _fp(chiave, **valori):
    """Un testo del campo foto nella lingua scelta (se non c'e' la traduzione, in italiano)."""
    testo = (rp_t(chiave) if "rp_t" in globals() and chiave in RP_TR.get(lingua() if "lingua" in globals() else "it", {}) else _FP_IT[chiave])
    return testo.format(**valori) if valori else testo


def campo_foto(chiave, attuale=""):
    """Punto unico per la foto. A sinistra 'Scatta' (apre la fotocamera VERA del telefono, lato posteriore, con messa a fuoco),
    a destra 'Carica dal telefono'. I due tasti li gestisce fotocamera.py: la foto scelta finisce nei campi nascosti qui sotto.
    Se il javascript non funzionasse, i tasti mostrano i normali campi di scatto / caricamento."""
    with st.container(key="azioni_foto_" + chiave):
        c_cam, c_gal = st.columns(2, gap="small")
        premuto_cam = c_cam.button("📷 " + t("Scatta la foto"), key=f"scatta_{chiave}", width="stretch")
        premuto_gal = c_gal.button("📁 " + t("Carica dal telefono"), key=f"galleria_{chiave}", width="stretch")
    with st.container(key="nascosti_" + chiave):
        foto_cam = st.file_uploader("camera", type=["jpg", "jpeg", "png", "webp"], key=f"fotocam_{chiave}")
        foto_gal = st.file_uploader("galleria", type=["jpg", "jpeg", "png", "webp"], key=f"fotogal_{chiave}")
    if premuto_cam:
        st.session_state[f"{chiave}_fall_cam"] = True
    if premuto_gal:
        st.session_state[f"{chiave}_fall_gal"] = True
    fall_cam = st.camera_input(t("Scatta la foto del prodotto"), key=f"camfall_{chiave}") if st.session_state.get(f"{chiave}_fall_cam") else None
    fall_gal = st.file_uploader(t("Carica dal telefono"), type=["jpg", "jpeg", "png", "webp"], key=f"galfall_{chiave}") if st.session_state.get(f"{chiave}_fall_gal") else None

    # tra le possibili foto vale l'ultima arrivata
    viste = st.session_state.setdefault(f"{chiave}_viste", {})
    ultima = st.session_state.get(f"{chiave}_ultima")
    candidati = {"cam": foto_cam, "gal": foto_gal, "fcam": fall_cam, "fgal": fall_gal}
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

    nuova = ""
    ident_f = None
    if file is not None:
        ident_f = f"{chiave}_{getattr(file, 'file_id', None) or file.name + str(file.size)}"
        if st.session_state.get(f"{chiave}_scartata") == ident_f:
            st.caption(_fp("foto_tolta"))
            file = None
    if file is not None:
        st.caption(_fp("foto_ricevuta", nome=file.name, kb=file.size // 1024))
        problemi = controlla_foto(file.getvalue())
        if problemi and not st.session_state.get(f"{chiave}_ok_{ident_f}"):
            # la foto non rispetta i requisiti: si propone subito di eliminarla e rifarla
            st.warning(_fp("foto_problema") + " " + ", ".join(_fp("foto_p_" + p) for p in problemi) + ".\n\n" + _fp("foto_consiglio"))
            c_el, c_ok = st.columns(2, gap="small")
            if c_el.button(_fp("foto_elimina"), key=f"fp_elimina_{ident_f}", type="primary", width="stretch"):
                st.session_state[f"{chiave}_scartata"] = ident_f
                st.rerun()
            if c_ok.button(_fp("foto_usa_comunque"), key=f"fp_usa_{ident_f}", width="stretch"):
                st.session_state[f"{chiave}_ok_{ident_f}"] = True
                st.rerun()
            return ""
        tieni = st.checkbox(_fp("foto_tieni"), key=f"fp_tieni_{ident_f}")
        with st.spinner(t("Sto ritagliando e raddrizzando la foto…")):
            automatica, modo = _foto_lavorata_modo(file.getvalue(), tieni)
        if modo == "scatola":
            st.caption(_fp("foto_scatola"))
        # editor come quello del telefono: righello per raddrizzare e cornice per tagliare
        sigla = hashlib.md5((ident_f + str(tieni)).encode()).hexdigest()[:10]
        etichetta = f"ritocco{sigla}"
        with st.container(key="nascosti_rit_" + sigla):
            params = st.text_input(etichetta, key=f"rit_{sigla}", label_visibility="collapsed")
        _mostra_editor(_editor_html(automatica, etichetta))
        nuova = _ritocco_params(automatica, params)
        with st.expander("🛠️ " + t("Controlli di riserva"), expanded=False):
            grado = st.slider("↻ " + t("Gira (gradi): positivo = senso antiorario"), -30.0, 30.0, 0.0, 0.5, key=f"rot_{ident_f}")
            c1, c2 = st.columns(2)
            sopra = c1.slider("⬆️ " + t("Taglia sopra (%)"), 0, 40, 0, key=f"ts_{ident_f}")
            sotto = c2.slider("⬇️ " + t("Taglia sotto (%)"), 0, 40, 0, key=f"tb_{ident_f}")
            sinistra = c1.slider("⬅️ " + t("Taglia a sinistra (%)"), 0, 40, 0, key=f"tl_{ident_f}")
            destra = c2.slider("➡️ " + t("Taglia a destra (%)"), 0, 40, 0, key=f"tr_{ident_f}")
        if grado or sopra or sotto or sinistra or destra:
            nuova = _ritocco(nuova, grado, sopra, sotto, sinistra, destra)
        st.markdown(foto_ampia_html(nuova), unsafe_allow_html=True)
        st.caption(f"✅ {t('Foto pronta: sfondo tolto e prodotto raddrizzato.')} (v{_VERSIONE_FOTO})")
        if st.button(_fp("foto_elimina"), key=f"fp_elimina2_{ident_f}", width="stretch"):
            st.session_state[f"{chiave}_scartata"] = ident_f
            st.rerun()
    elif attuale and src_sicuro(attuale):
        st.markdown(foto_ampia_html(src_sicuro(attuale)), unsafe_allow_html=True)
    return nuova


CSS = CSS.replace("</style>", """
/* foto ampia: scheda in home, anteprima e modifica */
.scheda .foto{height:250px !important;padding:8px !important;overflow:hidden}
.scheda .foto img{width:100% !important;height:100% !important;max-width:100% !important;max-height:none !important;object-fit:contain !important;border-radius:0 !important}
.foto-ampia{height:380px;border-radius:24px;padding:10px;background:linear-gradient(180deg,#ffffff,#edf7f1);
 box-shadow:inset 0 0 0 1px rgba(0,0,0,.04),0 8px 18px rgba(0,0,0,.08);margin:6px 0}
.foto-ampia img{width:100%;height:100%;object-fit:contain}
[class*="st-key-fotocam_"]{display:flex !important;flex-direction:row !important;gap:10px;align-items:stretch}
[class*="st-key-fotocam_"]>div{flex:1 1 0;min-width:0}
.cam-btn{flex:1 1 0;min-width:0;min-height:100px;border:0;border-radius:24px;background:linear-gradient(135deg,#14b8a6,#06b6d4);color:#fff;
 font-weight:900;font-size:1.05rem;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;cursor:pointer;
 box-shadow:0 10px 22px rgba(6,182,212,.4);font-family:inherit}
.cam-btn span{font-size:2rem;line-height:1}
[class*="st-key-fotocam_"] [data-testid="stFileUploaderDropzoneInstructions"]{display:none !important}
[class*="st-key-fotocam_"] section{min-height:100px;display:flex;align-items:center;justify-content:center;padding:8px;border-radius:24px;
 border:2px dashed #14b8a6;background:rgba(255,255,255,.75)}
[class*="st-key-fotocam_"] section button{font-size:0 !important;border:0 !important;background:transparent !important;box-shadow:none !important}
[class*="st-key-fotocam_"] section button::after{content:"🖼️ __CARICA__";font-size:1rem;font-weight:800;color:#0f766e}
/* due tasti affiancati ma separati: Elimina e Modifica (anche su telefono) */
[class*="st-key-azioni_"] [data-testid="stHorizontalBlock"]{flex-direction:row !important;flex-wrap:nowrap !important;gap:10px !important}
[class*="st-key-azioni_"] [data-testid="stColumn"],[class*="st-key-azioni_"] [data-testid="column"]{min-width:0 !important;width:auto !important;flex:1 1 0 !important}
[class*="st-key-azioni_"] button{padding-left:6px;padding-right:6px}
[class*="st-key-modif_"] button{width:100%;min-height:52px;border-radius:999px !important;background:rgba(255,255,255,.78) !important;color:#0f766e !important;
 border:2px solid rgba(13,148,136,.35) !important;font-weight:800 !important;box-shadow:0 8px 18px rgba(0,60,50,.1)}
[class*="st-key-modif_"] button p{font-weight:800 !important;color:#0f766e !important}
[class*="st-key-modif_"] button:hover{background:#ccfbf1 !important}
[class*="st-key-modif_"] button:disabled{opacity:.5}
[class*="st-key-nascosti_"]{display:none !important}
[class*="st-key-scatta_"] button,[class*="st-key-galleria_"] button{min-height:64px;border-radius:999px !important;font-weight:800 !important;font-size:1.02rem;
 border:2px solid rgba(13,148,136,.45) !important;box-shadow:0 4px 0 rgba(0,100,90,.25)}
[class*="st-key-scatta_"] button{background:linear-gradient(135deg,#00a98f,#0288d1) !important;color:#fff !important;border:0 !important}
[class*="st-key-scatta_"] button p{color:#fff !important}
</style>""".replace("__CARICA__", t("Carica dal telefono")))
