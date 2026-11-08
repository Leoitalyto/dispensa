# -*- coding: utf-8 -*-
"""IMMAGINI SICURE — una foto rovinata non deve mai rompere una pagina.

PROBLEMA TROVATO (sezione Archivio): se un file allegato ha l'estensione di una foto ma non è un'immagine valida (file danneggiato o interrotto durante il caricamento, vuoto, oppure un formato che il programma non sa aprire come HEIC), `st.image()` lancia un errore («cannot identify image file») e l'INTERA pagina si ferma con una schermata rossa.
RIMEDIO UNICO PER TUTTE LE SEZIONI: `st.image` (e `contenitore.image`, `colonna.image`…) viene avvolta una sola volta: se l'immagine non si può mostrare, al suo posto compare una riga chiara («🖼️ Questa immagine non si può mostrare…») e la pagina continua a funzionare. Il pulsante «Scarica» accanto all'immagine resta disponibile.
È un'aggiunta: le immagini valide si vedono esattamente come prima."""
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

_AVVISO = ("🖼️ Questa immagine non si può mostrare qui (il file è danneggiato oppure è in un formato che il programma non sa aprire). "
           "Se c'è il pulsante «Scarica», puoi salvarla e aprirla con il telefono.")


def _is_segnale_interno(e):
    return any(x in type(e).__name__ for x in ("Rerun", "Stop", "Script"))                  # i segnali interni di Streamlit passano


if not getattr(DeltaGenerator.image, "_sicura", False):                                     # contenitori e colonne: col.image(...), with st.container(): ...
    _is_image_originale = DeltaGenerator.image

    def _is_image_sicura(self, *args, **kwargs):
        try:
            return _is_image_originale(self, *args, **kwargs)
        except Exception as e:
            if _is_segnale_interno(e):
                raise
            return self.caption(_AVVISO)
    _is_image_sicura._sicura = True
    DeltaGenerator.image = _is_image_sicura

if not getattr(st.image, "_sicura", False):                                                 # la chiamata semplice st.image(...) è una copia legata a parte: va avvolta anche lei
    _is_st_image_originale = st.image

    def _is_st_image_sicura(*args, **kwargs):
        try:
            return _is_st_image_originale(*args, **kwargs)
        except Exception as e:
            if _is_segnale_interno(e):
                raise
            return st.caption(_AVVISO)
    _is_st_image_sicura._sicura = True
    st.image = _is_st_image_sicura
