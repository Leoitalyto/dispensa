# -*- coding: utf-8 -*-
"""Foto del prodotto: un solo punto (in alto nella scheda Aggiungi) dove si scatta con la fotocamera POSTERIORE.
La foto viene scontornata (sfondo tolto) e addrizzata in modo automatico, poi mostrata AMPIA nel riquadro della scheda.
Caricato da app_dispensa.py dopo account.py e prima di parte3.py."""
import base64
import html
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


def scontorna_e_addrizza(dati, lato=720):
    """Da una foto (bytes) a una immagine WebP trasparente, ritagliata sul prodotto e addrizzata. Ritorna 'data:image/webp;base64,...'."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    img.thumbnail((1200, 1200))
    rgb = np.array(img)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    mask = _maschera_ai(rgb)
    if mask is None:                                                         # riserva: metodo senza modello
        scala = 360.0 / max(h, w) if max(h, w) > 360 else 1.0
        piccola = cv2.resize(bgr, (max(1, int(w * scala)), max(1, int(h * scala))), interpolation=cv2.INTER_AREA)
        mp = _maschera_prodotto(piccola)
        if mp is not None:
            mask = cv2.resize(mp, (w, h), interpolation=cv2.INTER_LINEAR)
            mask = cv2.GaussianBlur(mask, (0, 0), 1.6)
            mask = np.clip((mask.astype(np.float32) - 110) * 255 / 90, 0, 255).astype(np.uint8)
    if mask is None:
        rgba = np.dstack([rgb, np.full((h, w), 255, np.uint8)])
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
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------
# Campo foto (uno solo, in alto) usato da "Aggiungi" e da "Modifica"
# ---------------------------------------------------------------------
_VERSIONE_FOTO = 7


def _foto_lavorata(dati):
    """Scontorna e addrizza una sola volta per ogni foto (la scelta resta in memoria durante la sessione)."""
    mem = st.session_state.setdefault("_foto_lavorate", {})
    chiave = (hash(dati), _VERSIONE_FOTO)                      # se cambia il metodo, le vecchie foto in memoria non valgono piu'
    if chiave not in mem:
        if len(mem) >= 4:
            mem.pop(next(iter(mem)))
        try:
            mem[chiave] = scontorna_e_addrizza(dati)
        except Exception:
            mem[chiave] = foto_a_data_uri(dati, 720)         # se qualcosa va storto resta la foto normale
    return mem[chiave]


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


def foto_ampia_html(src):
    return f"<div class='foto-ampia'><img src='{html.escape(src, quote=True)}' alt=''></div>"


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
    if file is not None:
        with st.spinner(t("Sto ritagliando e raddrizzando la foto…")):
            automatica = _foto_lavorata(file.getvalue())
        ident_f = f"{chiave}_{getattr(file, 'file_id', None) or file.name + str(file.size)}"
        # ritocco a mano: sotto la foto, con anteprima subito (ogni foto nuova riparte da zero)
        with st.expander("🛠️ " + t("Raddrizza e taglia a mano"), expanded=False):
            grado = st.slider("↻ " + t("Gira (gradi): positivo = senso antiorario"), -30.0, 30.0, 0.0, 0.5, key=f"rot_{ident_f}")
            c1, c2 = st.columns(2)
            sopra = c1.slider("⬆️ " + t("Taglia sopra (%)"), 0, 40, 0, key=f"ts_{ident_f}")
            sotto = c2.slider("⬇️ " + t("Taglia sotto (%)"), 0, 40, 0, key=f"tb_{ident_f}")
            sinistra = c1.slider("⬅️ " + t("Taglia a sinistra (%)"), 0, 40, 0, key=f"tl_{ident_f}")
            destra = c2.slider("➡️ " + t("Taglia a destra (%)"), 0, 40, 0, key=f"tr_{ident_f}")
        nuova = _ritocco(automatica, grado, sopra, sotto, sinistra, destra)
        st.markdown(foto_ampia_html(nuova), unsafe_allow_html=True)
        st.caption(f"✅ {t('Foto pronta: sfondo tolto e prodotto raddrizzato.')} (v{_VERSIONE_FOTO})")
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
