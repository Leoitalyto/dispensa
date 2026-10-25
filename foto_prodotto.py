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
from PIL import Image, ImageOps


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


def scontorna_e_addrizza(dati, lato=560):
    """Da una foto (bytes) a una immagine WebP trasparente, ritagliata sul prodotto e addrizzata. Ritorna 'data:image/webp;base64,...'."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    img.thumbnail((900, 900))
    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    # la ricerca del prodotto si fa su una copia piccola (veloce), poi la maschera si porta alla misura piena
    scala = 360.0 / max(h, w) if max(h, w) > 360 else 1.0
    piccola = cv2.resize(bgr, (max(1, int(w * scala)), max(1, int(h * scala))), interpolation=cv2.INTER_AREA)
    mp = _maschera_prodotto(piccola)
    if mp is None:
        rgba = np.dstack([cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), np.full((h, w), 255, np.uint8)])
        mask = None
    else:
        mask = cv2.resize(mp, (w, h), interpolation=cv2.INTER_LINEAR)
        mask = cv2.GaussianBlur(mask, (0, 0), 1.6)                           # bordo morbido, senza scalini
        mask = np.clip((mask.astype(np.float32) - 110) * 255 / 90, 0, 255).astype(np.uint8)
        rgba = np.dstack([cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), mask])
    if mask is not None:
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
    out.thumbnail((lato, lato))
    buf = io.BytesIO()
    out.save(buf, "WEBP", quality=82, method=6)
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
            mem[chiave] = foto_a_data_uri(dati, 560)         # se qualcosa va storto resta la foto normale
    return mem[chiave]


def foto_ampia_html(src):
    return f"<div class='foto-ampia'><img src='{html.escape(src, quote=True)}' alt=''></div>"


def campo_foto(chiave, attuale=""):
    """Mostra il punto unico per la foto. Ritorna la nuova foto pronta (data URI) oppure '' se non ne e' stata scelta una.
    I campi con chiave che inizia per 'fotocam_' aprono subito la fotocamera POSTERIORE (lo fa fotocamera.py)."""
    galleria = st.toggle("🖼️ " + t("Scelgo una foto dalla galleria invece di scattare"), key=f"{chiave}_gal")
    if galleria:
        file = st.file_uploader(t("Carica una foto dalla galleria"), type=["jpg", "jpeg", "png", "webp"], key=f"fotogal_{chiave}")
    else:
        file = st.file_uploader("📷 " + t("Scatta la foto del prodotto"), type=["jpg", "jpeg", "png", "webp"], key=f"fotocam_{chiave}")
        st.caption(t("Si apre la fotocamera posteriore. Il prodotto viene ritagliato e raddrizzato da solo."))
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
.foto-ampia{height:260px;border-radius:24px;padding:10px;background:linear-gradient(180deg,#ffffff,#edf7f1);
 box-shadow:inset 0 0 0 1px rgba(0,0,0,.04),0 8px 18px rgba(0,0,0,.08);margin:6px 0}
.foto-ampia img{width:100%;height:100%;object-fit:contain}
[class*="st-key-fotocam_"] section,[class*="st-key-fotogal_"] section{border-radius:24px;border:2px dashed #14b8a6;background:rgba(255,255,255,.75);padding:20px}
/* due tasti affiancati ma separati: Elimina e Modifica (anche su telefono) */
[class*="st-key-azioni_"] [data-testid="stHorizontalBlock"]{flex-direction:row !important;flex-wrap:nowrap !important;gap:10px !important}
[class*="st-key-azioni_"] [data-testid="stColumn"],[class*="st-key-azioni_"] [data-testid="column"]{min-width:0 !important;width:auto !important;flex:1 1 0 !important}
[class*="st-key-azioni_"] button{padding-left:6px;padding-right:6px}
[class*="st-key-modif_"] button{width:100%;min-height:52px;border-radius:999px !important;background:rgba(255,255,255,.78) !important;color:#0f766e !important;
 border:2px solid rgba(13,148,136,.35) !important;font-weight:800 !important;box-shadow:0 8px 18px rgba(0,60,50,.1)}
[class*="st-key-modif_"] button p{font-weight:800 !important;color:#0f766e !important}
[class*="st-key-modif_"] button:hover{background:#ccfbf1 !important}
[class*="st-key-modif_"] button:disabled{opacity:.5}
</style>""")
