# -*- coding: utf-8 -*-
"""INTESTAZIONI DELLE SEZIONI — le icone grandi non stanno più nella prima schermata (Home): stanno nell'intestazione interna di ogni sezione.

• Home: la fila delle icone illustrate (Salute, I miei documenti, Utilità, Casa) non c'è più. Alle sezioni si va dai bottoni colorati in alto, che lampeggiano quando c'è qualcosa da guardare.
• Dentro la sezione: l'icona illustrata sta a SINISTRA nel riquadro colorato dell'intestazione, con il titolo e il sottotitolo a destra (Salute, I miei documenti, Utilità; Casa la aveva già).
  Lavoro, Auto e Archivio hanno la loro icona grande nel riquadro.
• Le icone sono rimpicciolite (200 px) e tenute in memoria: la pagina pesa meno di prima.
Caricato per ultimo da app_dispensa.py."""
import base64
import io
import os

import streamlit as st

_IH = {"salute": ("fa-hero", "salute.webp", "#e53935"), "documenti": ("doc-hero", "documenti.webp", "#039be5"), "utilita": ("ut-hero", "utilita.webp", "#00acc1")}


@st.cache_resource
def _ih_cache(percorso, mtime, lato):
    try:
        from PIL import Image
        im = Image.open(percorso).convert("RGBA")
        im.thumbnail((lato, lato))
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=88, method=6)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def ih_uri(nome, lato=200):
    """L'icona (rimpicciolita) come indirizzo «data:», oppure '' se il file manca."""
    cartella = globals().get("_cartella") or "."
    percorso = os.path.join(cartella, nome)
    try:
        return _ih_cache(percorso, os.path.getmtime(percorso), lato)
    except OSError:
        return ""


def ih_ha_icona(sezione):
    return bool(ih_uri(_IH[sezione][1])) if sezione in _IH else False


def ih_css(sezione):
    """Lo stile che mette l'icona a sinistra nell'intestazione (titolo e sottotitolo a destra)."""
    if sezione not in _IH:
        return ""
    classe, nome, _col = _IH[sezione]
    uri = ih_uri(nome)
    if not uri:
        return ""
    return (f"<style>.{classe}{{display:grid !important;grid-template-columns:auto 1fr !important;column-gap:16px !important;align-items:center !important}}"
            f".{classe}::before{{content:'';grid-row:1 / span 2;width:92px;height:92px;background:url({uri}) center/contain no-repeat;filter:drop-shadow(0 4px 6px rgba(0,0,0,.35))}}"
            f".{classe}>h1{{grid-column:2;grid-row:1;align-self:end}}.{classe}>p{{grid-column:2;grid-row:2;align-self:start}}"
            f"@media (max-width:420px){{.{classe}::before{{width:76px;height:76px}}}}</style>")


def ih_sezione_corrente():
    """Quale intestazione disegna la pagina aperta (None se non è una di queste tre)."""
    sh = st.session_state.get("sezione_home")
    if sh in ("documenti", "utilita"):
        return sh
    if sh in (None, "", "salute"):
        return "salute"
    return None


# ---- la Home non mostra più la fila delle icone illustrate
def icona_farmacia():                                          # noqa: F811
    return None


# ---- dentro la sezione: lo stile dell'icona nell'intestazione
if "schermata_farmacia" in globals() and "_ih_schermata_prima" not in globals():
    _ih_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                  # noqa: F811
        try:
            css = ih_css(ih_sezione_corrente())
            if css:
                st.markdown(css, unsafe_allow_html=True)
        except Exception:
            pass
        return _ih_schermata_prima()
