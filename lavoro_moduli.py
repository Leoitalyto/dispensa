# -*- coding: utf-8 -*-
"""Lavoro → «📝 Moduli da compilare»: i moduli di carta (scansioni PDF) compilati a domande, firmati e inviati.

Come funziona: il modulo vuoto è una FOTO del foglio. L'app non lo «riempie» come un modulo online: scrive sopra il foglio,
nei punti giusti (le coordinate sono in LM_MODELLI), come si farebbe con la penna, e se lo chiedi mette la firma.
Il risultato è un PDF identico all'originale, compilato.

Dove stanno le cose (niente di personale nel codice, che è pubblico):
  · i moduli vuoti: nel repository PRIVATO dei dati, file «modelli_lavoro/<id>.json» ({nome, mime, b64}: foto JPEG a 150 dpi);
  · la firma: tra i documenti privati di chi la carica (documenti/<uid>/firma_lavoro.json), PNG trasparente;
  · i moduli compilati: d["casa"]["moduli_lavoro"]["compilati"] (solo i dati scritti: il PDF si rifà ogni volta, sempre uguale).
Prefisso: lm_ / LM_."""
import base64 as _lm_b64
import datetime as _lm_dt
import io as _lm_io
import re as _lm_re
import uuid as _lm_uuid

import streamlit as st

LM_INCHIOSTRO = (0.06, 0.12, 0.45)                      # blu penna
LM_MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
LM_PERMESSI = ["Permesso retribuito", "Permesso non retribuito", "Permesso ex festività", "Ferie", "Permesso Studio", "Permesso esame", "Permessi L. 104"]
LM_ARTICOLI = ["Pantaloni", "Pantaloni alta visibilità", "Giubbotto", "Giacca impermeabile", "Felpa", "Polo", "T-shirt", "Camicia",
               "Gilet alta visibilità", "Scarpe antinfortunistiche", "Stivali", "Guanti", "Cappello"]
LM_TAGLIE = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"] + [str(n) for n in range(36, 50)]

# Le coordinate sono in punti PDF (A4 = 595 × 842), misurate sulle scansioni: y = la riga su cui si scrive.
LM_MODELLI = {
    "frassati_permessi": {
        "titolo": "Richiesta di permesso – ferie", "icona": "🏖️", "file": "modelli_lavoro/frassati_permessi.json", "pagina": (595, 842),
        "testi": {"nome": (180, 169, 505, 12), "cantiere": (190, 215, 505, 12), "altro": (148, 507, 505, 11), "periodo": (160, 561, 388, 11)},
        "caselle": {LM_PERMESSI[i]: (374.5, y) for i, y in enumerate((317, 343, 370.5, 397, 424, 451, 477.5))},
        "firma": (192, 584, 392, 634),                      # x0, y0, x1, y1 (la riga è a y1)
        "data": {"g": (108, 719), "m": (137, 719), "a": (166, 719)},
    },
    "frassati_vestiario": {
        "titolo": "Scheda ordini abbigliamento", "icona": "👕", "file": "modelli_lavoro/frassati_vestiario.json", "pagina": (595, 842),
        "testi": {"appalto": (92, 158, 560, 11), "mese": (124, 187, 400, 11), "data_ordine": (422, 187, 560, 11),
                  "luogo": (152, 216, 560, 11), "riferimento": (95, 251, 560, 10)},
        "tabella": {"y0": 285.0, "y1": 730.0, "righe": 23, "colonne": [("nome", 24, 136), ("articolo", 136, 268), ("qta", 268, 302), ("taglia", 302, 396), ("altro", 396, 564)]},
        "note": (28, 753, 562, 806),
        "firma": (420, 770, 560, 805),                      # facoltativa: in basso a destra, nel riquadro delle Note
    },
}


# =====================================================================================================================
# logica (senza Streamlit): firma, PDF, testi
# =====================================================================================================================
def lm_pulisci_firma(dati):
    """Dalla foto della firma (su carta bianca) → PNG trasparente con il solo inchiostro, ritagliato. Restituisce (png, larghezza, altezza)."""
    import numpy as np
    from PIL import Image, ImageFilter, ImageOps
    im = ImageOps.exif_transpose(Image.open(_lm_io.BytesIO(dati))).convert("L")
    if max(im.size) > 1800:
        im.thumbnail((1800, 1800))
    g = np.asarray(im, dtype=np.float32)
    fondo = np.asarray(im.filter(ImageFilter.GaussianBlur(radius=max(15, min(im.size) // 12))), dtype=np.float32)
    fondo = np.maximum(fondo, g)                                # il foglio, con le sue ombre
    ink = np.clip(1.0 - g / np.maximum(fondo, 1.0), 0, 1)        # 0 = carta, 1 = inchiostro pieno
    soglia = max(0.08, float(np.percentile(ink, 60)) * 2.5)
    alfa = np.clip((ink - soglia) / max(0.25, 1 - soglia) * 2.6, 0, 1)
    ys, xs = np.where(alfa > 0.15)
    if len(xs) < 50:
        raise ValueError("Non vedo la firma: fotografala su un foglio bianco, ben illuminata, riempiendo la foto.")
    m = 12
    x0, x1, y0, y1 = max(0, xs.min() - m), min(alfa.shape[1], xs.max() + m), max(0, ys.min() - m), min(alfa.shape[0], ys.max() + m)
    alfa = alfa[y0:y1, x0:x1]
    rgba = np.zeros(alfa.shape + (4,), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 18, 22, 60          # inchiostro scuro (nero-blu)
    rgba[..., 3] = (alfa * 255).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    if out.width > 1000:
        out = out.resize((1000, int(out.height * 1000 / out.width)), Image.LANCZOS)
    b = _lm_io.BytesIO()
    out.save(b, "PNG", optimize=True)
    return b.getvalue(), out.width, out.height


def _lm_latino(s):
    """Il carattere del PDF (Helvetica) conosce solo le lettere «latine»: trattini lunghi, virgolette curve ed emoji si sostituiscono."""
    s = str(s or "").strip()
    for a, b in (("–", "-"), ("—", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("…", "..."), ("€", "EUR")):
        s = s.replace(a, b)
    return s.encode("latin-1", "ignore").decode("latin-1")


def _lm_scrivi(pg, x, y, x_max, testo, dim, minimo=6.5):
    """Scrive su una riga, rimpicciolendo il carattere se il testo è troppo lungo per lo spazio."""
    import pymupdf as fitz
    testo = _lm_latino(testo)
    if not testo:
        return
    lungh = lambda s, f: fitz.get_text_length(s, fontname="helv", fontsize=f)
    f = dim
    while f > minimo and lungh(testo, f) > (x_max - x):
        f -= 0.5
    while testo and lungh(testo, f) > (x_max - x):
        testo = testo[:-1]
    pg.insert_text((x, y), testo, fontname="helv", fontsize=f, color=LM_INCHIOSTRO)


def _lm_firma(pg, box, firma_png):
    """La firma dentro il riquadro (x0, y0, x1, y1), appoggiata sulla riga e un po' sopra, senza deformarla."""
    import pymupdf as fitz
    from PIL import Image
    x0, y0, x1, y1 = box
    im = Image.open(_lm_io.BytesIO(firma_png))
    w, h = im.size
    alt = (y1 - y0) * 1.25                                      # può scendere un po' sotto la riga, come una firma vera
    larg = alt * w / h
    if larg > (x1 - x0):
        larg = x1 - x0
        alt = larg * h / w
    yb = y1 + alt * 0.18
    pg.insert_image(fitz.Rect(x0, yb - alt, x0 + larg, yb), stream=firma_png, keep_proportion=True, overlay=True)


def _lm_fmt(dd):
    return dd.strftime("%d/%m/%Y") if dd else ""


def lm_data(s):
    try:
        return _lm_dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def lm_genera_pdf(modello, sfondo_jpg, valori, firma_png=None):
    """Il PDF compilato (byte). valori = i dati del modulo; firma_png = None per non firmare."""
    import pymupdf as fitz
    M = LM_MODELLI[modello]
    W, H = M["pagina"]
    doc = fitz.open()
    v = valori or {}

    def _pagina():
        pg = doc.new_page(width=W, height=H)
        pg.insert_image(fitz.Rect(0, 0, W, H), stream=sfondo_jpg, keep_proportion=False)
        return pg

    if modello == "frassati_permessi":
        pg = _pagina()
        t = M["testi"]
        for k in ("nome", "cantiere"):
            x, y, xm, f = t[k]
            _lm_scrivi(pg, x, y, xm, v.get(k), f)
        tipo = v.get("tipo")
        if tipo in M["caselle"]:
            cx, cy = M["caselle"][tipo]
            pg.draw_line((cx - 6, cy - 6), (cx + 6, cy + 6), color=LM_INCHIOSTRO, width=2)
            pg.draw_line((cx - 6, cy + 6), (cx + 6, cy - 6), color=LM_INCHIOSTRO, width=2)
        elif tipo == "Altro":
            x, y, xm, f = t["altro"]
            _lm_scrivi(pg, x, y, xm, v.get("altro"), f)
        dal, al = lm_data(v.get("dal")), lm_data(v.get("al"))
        if dal:
            x, y, xm, f = t["periodo"]
            _lm_scrivi(pg, x, y, xm, _lm_fmt(dal) + (f"  fino al  {_lm_fmt(al)}" if al else ""), f)
        dm = lm_data(v.get("data_modulo"))
        if dm:
            for k, s in (("g", f"{dm.day:02d}"), ("m", f"{dm.month:02d}"), ("a", str(dm.year))):
                x, y = M["data"][k]
                _lm_scrivi(pg, x, y, x + 60, s, 11)
        if firma_png:
            _lm_firma(pg, M["firma"], firma_png)
    else:
        righe = [r for r in (v.get("righe") or []) if any(str(r.get(c) or "").strip() for c, *_ in M["tabella"]["colonne"])]
        T = M["tabella"]
        h = (T["y1"] - T["y0"]) / T["righe"]
        blocchi = [righe[i:i + T["righe"]] for i in range(0, len(righe), T["righe"])] or [[]]
        dm = lm_data(v.get("data_ordine"))
        for nb, blocco in enumerate(blocchi):
            pg = _pagina()
            for k in ("appalto", "mese", "luogo", "riferimento"):
                x, y, xm, f = M["testi"][k]
                _lm_scrivi(pg, x, y, xm, v.get(k), f)
            x, y, xm, f = M["testi"]["data_ordine"]
            _lm_scrivi(pg, x, y, xm, _lm_fmt(dm) + (f"   (foglio {nb + 1}/{len(blocchi)})" if len(blocchi) > 1 else ""), f)
            for i, r in enumerate(blocco):
                yb = T["y0"] + h * (i + 1) - 5.5
                for c, xa, xb in T["colonne"]:
                    t_ = _lm_latino(r.get(c))
                    if c in ("qta", "taglia") and t_:                  # numeri e taglie al centro della casella
                        xa = max(xa, (xa + xb) / 2 - fitz.get_text_length(t_, fontname="helv", fontsize=9.5) / 2 - 3)
                    _lm_scrivi(pg, xa + 3, yb, xb - 3, t_, 9.5, minimo=5.5)
            if v.get("note"):
                x0, y0, x1, y1 = M["note"]
                larg_testo = (x1 - x0) if not (firma_png and v.get("firma_in_fondo")) else (M["firma"][0] - 8 - x0)
                pg.insert_textbox(fitz.Rect(x0, y0 + 2, x0 + larg_testo, y1), _lm_latino(v["note"]), fontname="helv", fontsize=9.5, color=LM_INCHIOSTRO)
            if firma_png and v.get("firma_in_fondo"):
                _lm_firma(pg, M["firma"], firma_png)
    out = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return out


def lm_immagine(pdf, dpi=110, pagina=0, fmt="png"):
    """Una pagina del PDF come immagine (anteprima o foto da mandare)."""
    import pymupdf as fitz
    doc = fitz.open(stream=pdf, filetype="pdf")
    pix = doc[min(pagina, len(doc) - 1)].get_pixmap(dpi=dpi)
    out = pix.tobytes("jpeg" if fmt == "jpg" else "png")
    doc.close()
    return out


def lm_pagine(pdf):
    import pymupdf as fitz
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return len(doc)


def lm_titolo(rec):
    """Il nome del modulo compilato (anche per il file)."""
    v = rec.get("valori") or {}
    if rec.get("modello") == "frassati_permessi":
        dal, al = lm_data(v.get("dal")), lm_data(v.get("al"))
        tipo = v.get("altro") if v.get("tipo") == "Altro" else v.get("tipo")
        per = (f" dal {_lm_fmt(dal)}" if dal else "") + (f" al {_lm_fmt(al)}" if al and al != dal else "")
        return f"{tipo or 'Permesso'}{per}"
    n = len([r for r in v.get("righe") or [] if r.get("articolo") or r.get("nome")])
    return f"Ordine abbigliamento {v.get('mese') or ''}".strip() + (f" · {n} {'riga' if n == 1 else 'righe'}" if n else "")


def lm_nome_file(rec, est="pdf"):
    base = _lm_re.sub(r"[^\w\-]+", "_", lm_titolo(rec)).strip("_")[:60] or "modulo"
    return f"{base}.{est}"


def lm_messaggio(rec, destinatario=""):
    """Il testo che accompagna il modulo su WhatsApp/email."""
    v = rec.get("valori") or {}
    saluto = f"Ciao {destinatario.split()[0]}," if destinatario.strip() else "Ciao,"
    if rec.get("modello") == "frassati_permessi":
        return f"{saluto} ti mando la richiesta: {lm_titolo(rec)}. Grazie, {v.get('nome') or ''}".strip()
    return f"{saluto} ti mando la scheda ordini abbigliamento ({v.get('mese') or ''}). Grazie, {v.get('riferimento') or v.get('firmatario') or ''}".strip()


def lm_controlla(modello, v):
    """Gli errori in italiano (lista vuota = si può fare)."""
    err = []
    if modello == "frassati_permessi":
        if not str(v.get("nome") or "").strip():
            err.append("Scrivi il tuo nome e cognome.")
        if not v.get("tipo"):
            err.append("Scegli cosa chiedi (ferie, permesso…).")
        if v.get("tipo") == "Altro" and not str(v.get("altro") or "").strip():
            err.append("Hai scelto «Altro»: scrivi che cosa.")
        dal, al = lm_data(v.get("dal")), lm_data(v.get("al"))
        if not dal:
            err.append("Scegli da quando («A decorrere dal»).")
        if dal and al and al < dal:
            err.append("«Fino al» è prima di «dal»: controlla le date.")
    else:
        if not [r for r in v.get("righe") or [] if r.get("articolo")]:
            err.append("Aggiungi almeno una riga (chi, che articolo, quanti).")
    return err


def lm_impara(mem, rec):
    """Ricorda colleghi, articoli e taglie (per proporli la volta dopo)."""
    mem = mem if isinstance(mem, dict) else {}
    v = rec.get("valori") or {}
    for r in v.get("righe") or []:
        n, a, t = str(r.get("nome") or "").strip(), str(r.get("articolo") or "").strip(), str(r.get("taglia") or "").strip()
        if n:
            col = mem.setdefault("colleghi", {}).setdefault(n, {})
            if a and t:
                col[a] = t
        if a and a not in mem.setdefault("articoli", []) and a not in LM_ARTICOLI:
            mem["articoli"].append(a)
    return mem


def lm_taglia_proposta(mem, nome, articolo):
    col = ((mem or {}).get("colleghi") or {}).get(str(nome or "").strip()) or {}
    if articolo in col:
        return col[articolo]
    scarpe = _lm_re.search(r"scarp|stival", str(articolo or ""), _lm_re.I)
    for a, t in col.items():                                     # stessa taglia di un altro capo dello stesso tipo
        if bool(_lm_re.search(r"scarp|stival", a, _lm_re.I)) == bool(scarpe):
            return t
    return ""


def lm_appuntamento(rec):
    """La voce per gli appuntamenti di Lavoro (solo per i permessi): {nome, data, …}."""
    v = rec.get("valori") or {}
    dal, al = lm_data(v.get("dal")), lm_data(v.get("al"))
    if rec.get("modello") != "frassati_permessi" or not dal:
        return None
    tipo = v.get("altro") if v.get("tipo") == "Altro" else v.get("tipo")
    return {"id": "lm_" + rec["id"], "nome": tipo or "Permesso", "funzione": "Richiesta di permesso – ferie", "telefono": "", "data": dal.isoformat(), "ora": "",
            "luogo": "", "motivo": (f"dal {_lm_fmt(dal)} al {_lm_fmt(al)}" if al and al != dal else f"il {_lm_fmt(dal)}"), "note": "Dal modulo compilato in Lavoro → Moduli.",
            "fatto": False, "priorita": "", "da_modulo": rec["id"]}


# =====================================================================================================================
# Streamlit
# =====================================================================================================================
_LM_CSS = """<style>
.lm-card{border:1px solid rgba(120,190,255,.45);border-radius:14px;padding:10px 12px;margin:6px 0;background:rgba(74,163,255,.06)}
.lm-card b{font-size:1rem}.lm-card .lm-s{font-size:.85rem;opacity:.85;margin-top:2px}
.lm-firma{background:#fff;border-radius:12px;padding:8px;text-align:center}.lm-firma img{max-width:100%;max-height:110px}
div[class*='st-key-lm_fabio']{border:2px solid #25D366 !important;border-radius:16px !important;background:rgba(37,211,102,.08) !important;padding:10px 12px !important}
</style>"""


def _lm_dati(c):
    m = c.get("moduli_lavoro")
    m = dict(m) if isinstance(m, dict) else {}
    m.setdefault("impostazioni", {})
    m.setdefault("compilati", [])
    m.setdefault("memoria", {})
    return m


def _lm_salva(fn, msg):
    def _f(c):
        m = c.setdefault("moduli_lavoro", {})
        m.setdefault("impostazioni", {})
        m.setdefault("compilati", [])
        m.setdefault("memoria", {})
        fn(m)
    _ca_salva(_f, "Lavoro → Moduli: " + msg)


@st.cache_data(ttl=3600, show_spinner=False)
def _lm_sfondo_cache(percorso):
    d = carica_dati(crea_archivio(), percorso)
    return _lm_b64.b64decode(d["b64"]) if d and d.get("b64") else None


def lm_sfondo(modello):
    try:
        return _lm_sfondo_cache(LM_MODELLI[modello]["file"])
    except Exception:
        return None


def _lm_uid():
    return (st.session_state.get("sess") or {}).get("uid") or "anonimo"


def _lm_firma_percorso():
    return f"documenti/{_lm_uid()}/firma_lavoro.json"


def lm_firma():
    """La firma salvata (PNG) o None."""
    try:
        d = carica_dati(crea_archivio(), _lm_firma_percorso())
        return _lm_b64.b64decode(d["b64"]) if d and d.get("b64") else None
    except Exception:
        return None


def _lm_nome_mio():
    s = st.session_state.get("sess") or {}
    n = str(s.get("nome") or "").strip()
    return "" if n.lower() in ("amministratore", "admin") else n


def _lm_sezione_firma():
    firma = lm_firma()
    with st.container(border=True, key="lm_firma_box"):
        st.markdown("**✍️ La tua firma**")
        if firma and not st.session_state.get("lm_firma_cambia"):
            st.markdown(f"<div class='lm-firma'><img alt='firma' src='data:image/png;base64,{_lm_b64.b64encode(firma).decode()}'></div>", unsafe_allow_html=True)
            st.caption("Si mette sul modulo SOLO quando tocchi «✍️ Firma e salva». È salvata tra i tuoi dati privati.")
            c1, c2 = st.columns(2, gap="small")
            if c1.button("🔄 Cambia firma", key="lm_firma_cambia_b", width="stretch"):
                st.session_state["lm_firma_cambia"] = True
                st.rerun()
            if c2.button("🗑️ Togli firma", key="lm_firma_togli", width="stretch"):
                try:
                    crea_archivio().elimina(_lm_firma_percorso(), "Lavoro → Moduli: firma tolta")
                except Exception:
                    salva_file(_lm_firma_percorso(), lambda d: d.clear(), "Lavoro → Moduli: firma tolta")
                carica_dati.clear()
                st.rerun()
            return
        st.caption("Firma su un **foglio bianco** con una penna scura, fai una foto da vicino (o scegli la foto che hai già): "
                   "l'app toglie il bianco e tiene solo l'inchiostro.")
        up = st.file_uploader("Foto della firma", type=["jpg", "jpeg", "png", "webp", "heic"], key="lm_firma_up")
        if up is not None:
            try:
                png, w, h = lm_pulisci_firma(up.getvalue())
            except Exception as ex:
                st.error(str(ex) if isinstance(ex, ValueError) else f"Non riesco a leggere la foto ({type(ex).__name__}): prova con un'altra.")
                return
            st.markdown(f"<div class='lm-firma'><img alt='firma' src='data:image/png;base64,{_lm_b64.b64encode(png).decode()}'></div>", unsafe_allow_html=True)
            st.caption("Ecco come apparirà. Se si vedono macchie o ombre, rifai la foto con più luce.")
            if st.button("💾 Usa questa firma", key="lm_firma_ok", type="primary", width="stretch"):
                corpo = {"nome": "firma.png", "mime": "image/png", "b64": _lm_b64.b64encode(png).decode(), "aggiornata": _lm_dt.datetime.now().isoformat(timespec="seconds")}
                salva_file(_lm_firma_percorso(), lambda d, c=corpo: (d.clear(), d.update(c)), "Lavoro → Moduli: firma")
                st.session_state.pop("lm_firma_cambia", None)
                st.toast("✅ Firma salvata")
                st.rerun()
        if firma and st.button("Annulla", key="lm_firma_annulla", width="stretch"):
            st.session_state.pop("lm_firma_cambia", None)
            st.rerun()


def _lm_impostazioni(m):
    imp = m["impostazioni"]
    resp = imp.get("responsabile") or {}
    with st.expander("⚙️ A chi li mandi e dati che si ripetono" + ("" if resp.get("cell") else " · manca il numero del responsabile")):
        with st.form("lm_imp"):
            nome = st.text_input("Il tuo nome e cognome (come va scritto sul modulo)", value=imp.get("nome") or _lm_nome_mio(), key="lm_i_nome")
            cant = st.text_input("Cantiere / Settore", value=imp.get("cantiere", ""), key="lm_i_cant")
            st.markdown("**💬 Responsabile (a cui li mandi di solito)**")
            rn = st.text_input("Nome", value=resp.get("nome") or "Fabio Di Maggio", key="lm_i_rn")
            rc = st.text_input("Cellulare WhatsApp (con prefisso, es. 39 333 1234567)", value=resp.get("cell", ""), key="lm_i_rc")
            st.markdown("**✉️ Altri, solo se serve (facoltativo)**")
            ae = st.text_input("Email (es. della segreteria)", value=imp.get("email_altri", ""), key="lm_i_ae", placeholder="segreteriab@coopfrassati.com")
            if st.form_submit_button("💾 Salva", type="primary", width="stretch"):
                def _fn(mm):
                    mm["impostazioni"].update({"nome": nome.strip(), "cantiere": cant.strip(), "email_altri": ae.strip(),
                                               "responsabile": {"nome": rn.strip(), "cell": "".join(ch for ch in rc if ch.isdigit())}})
                _lm_salva(_fn, "impostazioni")
                st.toast("✅ Salvato")
                st.rerun()


def _lm_nuovo_valori(modello, m):
    imp, oggi_ = m["impostazioni"], _lm_dt.date.today()
    if modello == "frassati_permessi":
        return {"nome": imp.get("nome") or _lm_nome_mio(), "cantiere": imp.get("cantiere", ""), "tipo": "Ferie", "altro": "",
                "dal": (oggi_ + _lm_dt.timedelta(days=7)).isoformat(), "al": (oggi_ + _lm_dt.timedelta(days=7)).isoformat(), "data_modulo": oggi_.isoformat()}
    ultimo = next((r for r in reversed(m["compilati"]) if r.get("modello") == modello), None)
    vv = (ultimo or {}).get("valori") or {}
    prossimo = (oggi_.replace(day=1) + _lm_dt.timedelta(days=32))
    return {"appalto": vv.get("appalto", ""), "mese": f"{LM_MESI[prossimo.month - 1]} {prossimo.year}", "data_ordine": oggi_.isoformat(),
            "luogo": vv.get("luogo", ""), "riferimento": vv.get("riferimento") or imp.get("nome") or _lm_nome_mio(), "righe": [], "note": "", "firma_in_fondo": False}


def _lm_form_permessi(v, k):
    st.markdown("**1 · Chi**")
    v["nome"] = st.text_input("Il/la sottoscritto/a", value=v.get("nome", ""), key=k + "nome")
    v["cantiere"] = st.text_input("del Cantiere / Settore", value=v.get("cantiere", ""), key=k + "cant")
    st.markdown("**2 · Cosa chiedi**")
    opz = LM_PERMESSI + ["Altro"]
    v["tipo"] = st.radio("chiede di poter usufruire di", opz, index=opz.index(v["tipo"]) if v.get("tipo") in opz else 3, key=k + "tipo", label_visibility="collapsed")
    if v["tipo"] == "Altro":
        v["altro"] = st.text_input("Altro: che cosa", value=v.get("altro", ""), key=k + "altro")
    st.markdown("**3 · Quando**")
    c1, c2 = st.columns(2, gap="small")
    dal = c1.date_input("A decorrere dal", value=lm_data(v.get("dal")) or _lm_dt.date.today(), format="DD/MM/YYYY", key=k + "dal")
    al = c2.date_input("fino al", value=max(lm_data(v.get("al")) or dal, dal), min_value=dal, format="DD/MM/YYYY", key=k + "al")
    v["dal"], v["al"] = dal.isoformat(), al.isoformat()
    giorni = (al - dal).days + 1
    st.caption(f"🗓️ {giorni} {'giorno' if giorni == 1 else 'giorni'} di calendario.")
    st.markdown("**4 · Data del modulo**")
    v["data_modulo"] = st.date_input("Torino, il", value=lm_data(v.get("data_modulo")) or _lm_dt.date.today(), format="DD/MM/YYYY", key=k + "dm").isoformat()
    st.caption("«Visto dal Responsabile di Settore» resta vuoto: lo firma lui.")


def _lm_form_vestiario(v, k, mem):
    st.markdown("**1 · Dati dell'ordine**")
    v["appalto"] = st.text_input("Appalto", value=v.get("appalto", ""), key=k + "app")
    c1, c2 = st.columns(2, gap="small")
    v["mese"] = c1.text_input("Ordine mese", value=v.get("mese", ""), key=k + "mese")
    v["data_ordine"] = c2.date_input("Data ordine", value=lm_data(v.get("data_ordine")) or _lm_dt.date.today(), format="DD/MM/YYYY", key=k + "do").isoformat()
    v["luogo"] = st.text_input("Luogo consegna", value=v.get("luogo", ""), key=k + "luogo")
    v["riferimento"] = st.text_input("Riferimento", value=v.get("riferimento", ""), key=k + "rif")
    st.markdown(f"**2 · Abbigliamento** ({len(v.get('righe') or [])} {'riga' if len(v.get('righe') or []) == 1 else 'righe'})")
    righe = v.setdefault("righe", [])
    for i, r in enumerate(righe):
        a, b = st.columns([5, 1], gap="small")
        a.markdown(f"<div class='lm-card' style='margin:2px 0;padding:6px 10px'><b>{sc_esc(r.get('nome') or '—')}</b> · {sc_esc(r.get('articolo') or '')}"
                   f" · <b>{sc_esc(r.get('qta') or '')}</b> pz · taglia <b>{sc_esc(r.get('taglia') or '—')}</b>"
                   + (f" · {sc_esc(r['altro'])}" if r.get("altro") else "") + "</div>", unsafe_allow_html=True)
        if b.button("🗑️", key=f"{k}del{i}", width="stretch"):
            righe.pop(i)
            st.rerun()
    with st.container(border=True, key=k + "riga"):
        st.markdown("➕ **Aggiungi una riga**")
        colleghi = list(((mem or {}).get("colleghi") or {}).keys())
        mio = v.get("riferimento") or ""
        nomi = ([mio] if mio else []) + [n for n in colleghi if n != mio]
        nome = st.selectbox("Nome e cognome", nomi, index=0 if nomi else None, accept_new_options=True, key=k + "rn",
                            placeholder="Scrivi o scegli", help="Scrivi un nome nuovo e premi Invio: la prossima volta lo trovi nell'elenco.")
        arts = LM_ARTICOLI + [a for a in ((mem or {}).get("articoli") or []) if a not in LM_ARTICOLI]
        art = st.selectbox("Articolo", arts, index=None, accept_new_options=True, key=k + "ra", placeholder="Scrivi o scegli")
        c1, c2 = st.columns([1, 2], gap="small")
        qta = c1.number_input("Q.tà", min_value=1, max_value=99, value=1, step=1, key=k + "rq")
        prop = lm_taglia_proposta(mem, nome, art)
        tg_opz = ([prop] if prop and prop not in LM_TAGLIE else []) + LM_TAGLIE
        tg = c2.selectbox("Taglia / Numero", tg_opz, index=tg_opz.index(prop) if prop in tg_opz else None, accept_new_options=True, key=k + "rt",
                          placeholder="Scegli", help="Se la persona l'ha già ordinata, la taglia è proposta da sola.")
        altro = st.text_input("Altro (facoltativo: colore, note…)", key=k + "rx")
        if st.button("➕ Aggiungi alla lista", key=k + "radd", type="primary", width="stretch"):
            if not art:
                st.error("Scegli o scrivi l'articolo.")
            elif len(righe) >= 69:
                st.error("Al massimo 69 righe (3 fogli).")
            else:
                righe.append({"nome": (nome or "").strip(), "articolo": art.strip(), "qta": str(int(qta)), "taglia": (tg or "").strip(), "altro": altro.strip()})
                for x in ("rn", "ra", "rq", "rt", "rx"):
                    st.session_state.pop(k + x, None)
                st.rerun()
        if len(righe) > 23:
            st.caption(f"Le righe sono più di 23: il modulo sarà su {(len(righe) - 1) // 23 + 1} fogli.")
    st.markdown("**3 · Note**")
    v["note"] = st.text_area("Note (facoltative)", value=v.get("note", ""), key=k + "note", height=80)
    v["firma_in_fondo"] = st.checkbox("✍️ Metti la mia firma in basso (questo modulo non ha la riga della firma)", value=bool(v.get("firma_in_fondo")), key=k + "ff")


def _lm_editor(m):
    """La compilazione guidata (nuovo o modifica). Lo stato del lavoro in corso sta in session_state["lm_bozza"]."""
    bz = st.session_state.get("lm_bozza")
    if not bz:
        return False
    modello = bz["modello"]
    M = LM_MODELLI[modello]
    k = f"lm_e_{bz['id']}_"
    with st.container(border=True, key="lm_editor"):
        st.markdown(f"### {M['icona']} {M['titolo']}" + (" · ✏️ modifica" if bz.get("esistente") else ""))
        v = bz["valori"]
        if modello == "frassati_permessi":
            _lm_form_permessi(v, k)
        else:
            _lm_form_vestiario(v, k, m.get("memoria"))
        firma = lm_firma()
        serve_firma = modello == "frassati_permessi" or v.get("firma_in_fondo")
        if serve_firma and not firma:
            st.warning("Non hai ancora caricato la firma: puoi salvare senza e firmarlo dopo (in alto, «✍️ La tua firma»).")
        with st.expander("👁️ Guarda l'anteprima prima di salvare"):
            sf = lm_sfondo(modello)
            if sf:
                pdf = lm_genera_pdf(modello, sf, v, firma if (firma and serve_firma) else None)
                st.image(lm_immagine(pdf, dpi=100), width="stretch")
                st.caption("Anteprima con la firma (se c'è)." if serve_firma and firma else "")
        err = lm_controlla(modello, v)
        c1, c2 = st.columns(2, gap="small")
        etich_ok = "✍️ Firma e salva" if (serve_firma and firma) else "💾 Salva"
        ok = c1.button(etich_ok, key=k + "ok", type="primary", width="stretch")
        senza = (serve_firma and firma) and c2.button("💾 Salva senza firma", key=k + "nofirma", width="stretch")
        annulla = st.button("Annulla", key=k + "no", width="stretch")
        if ok or senza:
            if err:
                for e_ in err:
                    st.error(e_)
                return True
            rec = {"id": bz["id"], "modello": modello, "valori": v, "firmato": bool(ok and serve_firma and firma),
                   "creato_il": bz.get("creato_il") or _lm_dt.datetime.now().isoformat(timespec="seconds"),
                   "aggiornato_il": _lm_dt.datetime.now().isoformat(timespec="seconds"), "invii": bz.get("invii") or []}
            if modello == "frassati_permessi":
                rec["valori"]["firma_in_fondo"] = False

            def _fn(mm, rec=rec):
                lst = mm["compilati"]
                for i, x in enumerate(lst):
                    if x.get("id") == rec["id"]:
                        lst[i] = rec
                        break
                else:
                    lst.append(rec)
                if modello == "frassati_permessi":
                    mm["impostazioni"]["nome"] = v.get("nome", "").strip() or mm["impostazioni"].get("nome", "")
                    mm["impostazioni"]["cantiere"] = v.get("cantiere", "").strip()
                mm["memoria"] = lm_impara(mm.get("memoria"), rec)
            _lm_salva(_fn, lm_titolo(rec))
            ap = lm_appuntamento(rec)                            # le ferie vanno anche negli appuntamenti di Lavoro
            if ap and "_apn_salva" in globals():
                try:
                    _apn_salva("lavoro", ap)
                except Exception:
                    pass
            st.session_state.pop("lm_bozza", None)
            st.session_state["lm_aperto"] = rec["id"]
            st.toast("✅ Modulo salvato" + (" e firmato" if rec["firmato"] else ""))
            st.rerun()
        if annulla:
            st.session_state.pop("lm_bozza", None)
            st.rerun()
    return True


def lm_pdf_di(rec):
    sf = lm_sfondo(rec.get("modello"))
    if not sf:
        return None
    firma = lm_firma() if rec.get("firmato") else None
    return lm_genera_pdf(rec["modello"], sf, rec.get("valori") or {}, firma)


def _lm_segna_invio(rec_id, a, come):
    def _fn(mm):
        for x in mm["compilati"]:
            if x.get("id") == rec_id:
                x.setdefault("invii", []).append({"a": a, "come": come, "il": _lm_dt.datetime.now().isoformat(timespec="seconds")})
    _lm_salva(_fn, "inviato a " + a)


def _lm_invio(rec, m, pdf):
    """Invio: prima Fabio (WhatsApp), poi gli altri modi."""
    imp = m["impostazioni"]
    resp = imp.get("responsabile") or {}
    rn = resp.get("nome") or "il responsabile"
    nome_pdf = lm_nome_file(rec)
    jpg = lm_immagine(pdf, dpi=150, fmt="jpg")
    msg = lm_messaggio(rec, rn)
    chiave = "lm_" + rec["id"]
    with st.container(key=f"lm_fabio_{rec['id']}"):
        st.markdown(f"**💬 Manda a {sc_esc(rn)} su WhatsApp** · consigliato")
        inv_registra_condivisione(chiave, lm_titolo(rec), msg, [(nome_pdf, "application/pdf", pdf)])
        with st.container(key=f"invio_share_{chiave}"):
            st.button(f"📤 Manda il PDF a {rn.split()[0] if rn else 'lui'}", key=f"lm_share_{rec['id']}", type="primary", width="stretch")
        st.markdown("<div class='inv-diag' style='font-size:.82rem;margin:2px 0 6px'></div>", unsafe_allow_html=True)
        st.caption(f"Si apre «Condividi» con il PDF già allegato: tocca **WhatsApp** e poi **{rn}** (di solito è tra i primi in alto).")
        if resp.get("cell"):
            st.link_button(f"💬 Apri la chat di {rn.split()[0]} (solo il messaggio)", inv_link_whatsapp(resp["cell"], msg), width="stretch")
            st.caption("Utile se «Condividi» non si apre: scarica il PDF qui sotto e allegalo nella chat con la graffetta 📎.")
        else:
            st.caption("Per aprire direttamente la sua chat, scrivi il suo numero in «⚙️ A chi li mandi».")
        if st.button(f"✅ Fatto: l'ho mandato a {rn.split()[0] if rn else 'lui'}", key=f"lm_segna_{rec['id']}", width="stretch"):
            _lm_segna_invio(rec["id"], rn, "WhatsApp")
            st.toast("✅ Segnato come inviato")
            st.rerun()
    c1, c2 = st.columns(2, gap="small")
    c1.download_button("⬇️ PDF", pdf, file_name=nome_pdf, mime="application/pdf", key=f"lm_dl_{rec['id']}", width="stretch")
    c2.download_button("⬇️ Foto (JPG)", jpg, file_name=lm_nome_file(rec, "jpg"), mime="image/jpeg", key=f"lm_dlj_{rec['id']}", width="stretch")
    with st.expander("📨 Altri modi (email, Telegram, altre persone…)"):
        if imp.get("email_altri"):
            st.caption(f"✉️ Email salvata: {imp['email_altri']}")
        inv_canali(f"lm_altri_{rec['id']}", lm_titolo(rec), msg, [(nome_pdf, "application/pdf", pdf)], oggetto=lm_titolo(rec), forma_fissa=True)


def _lm_card(rec, m):
    M = LM_MODELLI.get(rec.get("modello")) or {"icona": "📝", "titolo": "Modulo"}
    quando = (lm_data(rec.get("aggiornato_il")) or lm_data(rec.get("creato_il")))
    invii = rec.get("invii") or []
    stato = ("✍️ firmato" if rec.get("firmato") else "senza firma") + (" · " + "; ".join(f"📤 a {x['a']} il {_lm_fmt(lm_data(x['il']))}" for x in invii[-2:]) if invii else " · non ancora inviato")
    aperto = st.session_state.get("lm_aperto") == rec["id"]
    st.markdown(f"<div class='lm-card'><b>{M['icona']} {sc_esc(lm_titolo(rec))}</b><div class='lm-s'>{sc_esc(M['titolo'])} · {_lm_fmt(quando)}<br>{sc_esc(stato)}</div></div>",
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    if c1.button("🙈" if aperto else "👁️ Apri", key=f"lm_ap_{rec['id']}", width="stretch", type="primary" if not aperto else "secondary"):
        st.session_state["lm_aperto"] = None if aperto else rec["id"]
        st.rerun()
    if c2.button("✏️", key=f"lm_mod_{rec['id']}", width="stretch", help="Modifica"):
        st.session_state["lm_bozza"] = {"id": rec["id"], "modello": rec["modello"], "valori": dict(rec.get("valori") or {}, righe=[dict(r) for r in (rec.get("valori") or {}).get("righe") or []]),
                                        "esistente": True, "creato_il": rec.get("creato_il"), "invii": rec.get("invii") or []}
        st.rerun()
    if c3.button("📄", key=f"lm_dup_{rec['id']}", width="stretch", help="Duplica (parte da questo)"):
        v = dict(rec.get("valori") or {}, righe=[dict(r) for r in (rec.get("valori") or {}).get("righe") or []])
        oggi_ = _lm_dt.date.today().isoformat()
        v["data_modulo" if rec["modello"] == "frassati_permessi" else "data_ordine"] = oggi_
        st.session_state["lm_bozza"] = {"id": _lm_uuid.uuid4().hex[:10], "modello": rec["modello"], "valori": v}
        st.rerun()
    if c4.button("🗑️", key=f"lm_del_{rec['id']}", width="stretch", help="Elimina"):
        st.session_state["lm_conferma_del"] = rec["id"]
        st.rerun()
    if st.session_state.get("lm_conferma_del") == rec["id"]:
        st.warning("Eliminare questo modulo compilato?")
        a, b = st.columns(2, gap="small")
        if a.button("🗑️ Sì, elimina", key=f"lm_del_si_{rec['id']}", type="primary", width="stretch"):
            _lm_salva(lambda mm: mm.__setitem__("compilati", [x for x in mm["compilati"] if x.get("id") != rec["id"]]), "eliminato")
            if "sc_salva" in globals():
                try:
                    sc_salva(lambda d: d.setdefault("appuntamenti", {}).__setitem__("lavoro", [x for x in d["appuntamenti"].get("lavoro", []) if x.get("da_modulo") != rec["id"]]),
                             "Appuntamento del modulo tolto")
                except Exception:
                    pass
            st.session_state.pop("lm_conferma_del", None)
            st.rerun()
        if b.button("No", key=f"lm_del_no_{rec['id']}", width="stretch"):
            st.session_state.pop("lm_conferma_del", None)
            st.rerun()
    if aperto:
        pdf = lm_pdf_di(rec)
        if not pdf:
            st.error("Non trovo il modulo vuoto nell'archivio: riprova fra poco.")
            return
        n = lm_pagine(pdf)
        for p in range(n):
            st.image(lm_immagine(pdf, dpi=100, pagina=p), width="stretch")
        if not rec.get("firmato") and lm_firma() and (rec["modello"] == "frassati_permessi" or (rec.get("valori") or {}).get("firma_in_fondo")):
            if st.button("✍️ Firmalo adesso", key=f"lm_firma_ora_{rec['id']}", type="primary", width="stretch"):
                def _fn(mm):
                    for x in mm["compilati"]:
                        if x.get("id") == rec["id"]:
                            x["firmato"] = True
                _lm_salva(_fn, "firmato")
                st.rerun()
        _lm_invio(rec, m, pdf)


def lm_pagina(c):
    """La pagina «📝 Moduli da compilare» dentro Lavoro."""
    st.markdown(_LM_CSS, unsafe_allow_html=True)
    m = _lm_dati(c)
    st.markdown("### 📝 Moduli da compilare")
    st.caption("Scegli il modulo, rispondi alle domande: l'app scrive sul foglio originale, mette la tua firma e lo mandi a chi serve.")
    if _lm_editor(m):
        return
    for mid, M in LM_MODELLI.items():
        if st.button(f"{M['icona']} {M['titolo']}", key=f"lm_nuovo_{mid}", type="primary", width="stretch"):
            st.session_state["lm_bozza"] = {"id": _lm_uuid.uuid4().hex[:10], "modello": mid, "valori": _lm_nuovo_valori(mid, m)}
            st.rerun()
    _lm_sezione_firma()
    _lm_impostazioni(m)
    lst = sorted(m["compilati"], key=lambda r: str(r.get("aggiornato_il") or r.get("creato_il") or ""), reverse=True)
    st.markdown(f"### 🗂️ Moduli compilati ({len(lst)})")
    if not lst:
        st.caption("Ancora nessuno: tocca uno dei moduli qui sopra.")
    for rec in lst:
        _lm_card(rec, m)
