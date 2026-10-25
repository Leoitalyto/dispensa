# -*- coding: utf-8 -*-
"""Riceve il tocco sul pulsante 🏷️ Volantini di una scheda (lo manda fotocamera.py) e apre la finestra. Va caricato per ultimo."""

with st.container(key="nascosti_vol"):
    _vol_valore = st.text_input("volantini-trigger", key="vol_trigger", label_visibility="collapsed")
if _vol_valore and _vol_valore != st.session_state.get("vol_gestito"):
    st.session_state["vol_gestito"] = _vol_valore
    apri_volantini(_vol_valore.split("|")[0])
