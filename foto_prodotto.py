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
        if lung < 0.06 * max(rw, rh):                                    # lati cortissimi (angoli arrotondati): li ignoro
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


_URL_MODELLO = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
_PERCORSO_MODELLO = "/tmp/u2netp.onnx"


@st.cache_resource(show_spinner=False)
def _sessione_modello():
    """Piccolo modello AI (4,6 MB) che riconosce il prodotto in primo piano. None se non e' disponibile."""
    try:
        import os
        import onnxruntime as ort
        import requests
        if not os.path.exists(_PERCORSO_MODELLO) or os.path.getsize(_PERCORSO_MODELLO) < 4_000_000:
            r = requests.get(_URL_MODELLO, timeout=60)
            r.raise_for_status()
            with open(_PERCORSO_MODELLO + ".tmp", "wb") as f:
                f.write(r.content)
            os.replace(_PERCORSO_MODELLO + ".tmp", _PERCORSO_MODELLO)
        return ort.InferenceSession(_PERCORSO_MODELLO, providers=["CPUExecutionProvider"])
    except Exception:
        return None


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
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    vicino = cv2.dilate(pieno, k)                                          # bordo morbido ma solo accanto al prodotto
    morbido = (np.clip((y - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8)
    alfa = np.where(pieno > 0, 255, np.minimum(morbido, vicino)).astype(np.uint8)
    return cv2.GaussianBlur(alfa, (0, 0), 0.9)


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
        ang = _angolo_da_raddrizzare((mask > 127).astype(np.uint8) * 255)
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
def _foto_lavorata(dati):
    """Scontorna e addrizza una sola volta per ogni foto (la scelta resta in memoria durante la sessione)."""
    mem = st.session_state.setdefault("_foto_lavorate", {})
    chiave = hash(dati)
    if chiave not in mem:
        if len(mem) >= 4:
            mem.pop(next(iter(mem)))
        try:
            mem[chiave] = scontorna_e_addrizza(dati)
        except Exception:
            mem[chiave] = foto_a_data_uri(dati, 720)         # se qualcosa va storto resta la foto normale
    return mem[chiave]


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
            nuova = _foto_lavorata(file.getvalue())
        st.markdown(foto_ampia_html(nuova), unsafe_allow_html=True)
        st.caption("✅ " + t("Foto pronta: sfondo tolto e prodotto raddrizzato."))
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
</style>""".replace("__CARICA__", t("Carica dal telefono")))
