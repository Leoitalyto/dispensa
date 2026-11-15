# -*- coding: utf-8 -*-
"""Una riga sola di pulsanti-icona (👁️ Vedi · ✏️ Modifica · 📤 Invia · 🗑️ Elimina · 🏷️ Categoria) sotto la scheda di un documento: sul telefono restano affiancati,
ognuno nel suo riquadro, senza andare a capo. Caricato da app_dispensa.py. Nomi con prefisso «ra_» per non scontrarsi con gli altri moduli."""
import streamlit as st

_ra_css_fatto = False


def ra_css():
    st.markdown("""<style>
div[class*="st-key-vmriga_"]{flex-wrap:nowrap !important;gap:6px !important;width:100% !important;margin:2px 0 6px !important}
div[class*="st-key-vmriga_"] > div{flex:1 1 0 !important;min-width:0 !important;width:auto !important}
div[class*="st-key-vmriga_"] [data-testid="stElementContainer"]{width:100% !important}
div[class*="st-key-vmriga_"] button{width:100% !important;min-width:0 !important;min-height:58px !important;padding:4px 1px !important;border-radius:14px !important}
div[class*="st-key-vmriga_"] button p{font-size:11px !important;line-height:1.2 !important;text-align:center !important;margin:0 !important;white-space:normal !important;word-break:break-word}
div[class*="st-key-vmriga_"] button div[data-testid="stMarkdownContainer"]{width:100%}
div[class*="st-key-vmriga_"] button p::first-line{font-size:18px !important;line-height:1.5 !important}
div[class*="st-key-vmduo_"]{flex-wrap:nowrap !important;gap:8px !important;width:100% !important}
div[class*="st-key-vmduo_"] > div{flex:1 1 0 !important;min-width:0 !important;width:auto !important}
div[class*="st-key-vmduo_"] [data-testid="stElementContainer"]{width:100% !important}
div[class*="st-key-vmduo_"] button{width:100% !important;min-width:0 !important}
</style>""", unsafe_allow_html=True)


def ra_riga(chiave, voci):
    """voci: [(id, icona, parola, aiuto, disattivo, on_click, args)] (gli ultimi tre sono facoltativi). Ritorna {id: True se toccato}."""
    ra_css()
    out = {}
    with st.container(horizontal=True, gap="small", key=f"vmriga_{chiave}"):
        for v in voci:
            vid, ico, par, aiuto = v[0], v[1], v[2], v[3]
            dis = v[4] if len(v) > 4 else False
            cb = v[5] if len(v) > 5 else None
            args = v[6] if len(v) > 6 else None
            kw = {"on_click": cb, "args": args} if cb else {}
            out[vid] = st.button(f"{ico}  \n{par}", key=f"vmra_{chiave}_{vid}", help=aiuto, disabled=bool(dis), use_container_width=True, **kw)
    return out


def ra_pannello_invio(chiave, titolo, coppie, allegati):
    """Il pannello dei canali (WhatsApp, email…) di «Invia», sotto la riga: si vede subito quando tocchi 📤."""
    if st.session_state.get(f"inv_aperto_{chiave}") and "inv_canali" in globals():
        try:
            inv_canali(chiave, titolo, _fa_inv_testo(titolo, coppie), list(_fa_inv_allegati(allegati)), oggetto=titolo)
        except Exception as e:
            st.error(f"Non riesco ad aprire l'invio ({type(e).__name__}). Chiudi e riprova; se capita ancora, scrivimelo.")
