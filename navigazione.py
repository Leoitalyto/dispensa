# -*- coding: utf-8 -*-
"""NAVIGAZIONE tra le sezioni e pulizia dell'interfaccia.
Le sezioni dell'app, nell'ordine: Dispensa → Salute → I miei documenti → Utilità.
Ogni sezione ha in alto, nello stesso posto, due pulsanti: «← precedente» e «successiva →».
In più c'è un piccolo controllo che nasconde la linguetta nera «Manage app» di Streamlit, che copre i pulsanti in basso a destra.
(La linguetta la vede solo chi ha fatto l'accesso a Streamlit come proprietario dell'app: gli altri utenti non l'hanno mai.)
Caricato da app_dispensa.py prima di farmacia.py."""
import json

import streamlit as st

SEZIONI_NAV = ["dispensa", "salute", "documenti", "utilita"]
NOMI_NAV = {"dispensa": "Dispensa", "salute": "Salute", "documenti": "I miei documenti", "utilita": "Utilità"}
_STATI_DA_CHIUDERE = ("fa_modulo_med", "fa_modulo_foglio", "fa_modulo_dottore", "fa_modulo_sanitario", "fa_modulo_tessera", "doc_modulo",
                      "fa_famiglia", "fa_apri_presc")

_JS_PULIZIA = r"""
(function () {
  var w = window, d = w.document;
  try {
    if (w.__navPulizia) return;
    w.__navPulizia = true;
    var giri = 0;
    function nascondi() {
      var els = d.querySelectorAll('a, button, div, span');
      for (var i = 0; i < els.length; i++) {
        var el = els[i];
        if (el.children.length > 4) continue;
        var t = (el.textContent || '').replace(/\s+/g, ' ').trim();
        if (t !== 'Manage app') continue;
        var x = el;                                           // risalgo fino all'elemento fisso in basso (la linguetta intera)
        for (var k = 0; k < 8 && x && x !== d.body; k++) {
          var pos = '';
          try { pos = w.getComputedStyle(x).position; } catch (e) {}
          if (pos === 'fixed' || pos === 'sticky') break;
          x = x.parentElement;
        }
        if (x && x !== d.body) { x.style.setProperty('display', 'none', 'important'); w.__navNascosta = (w.__navNascosta || 0) + 1; }
        else { el.style.setProperty('display', 'none', 'important'); }
      }
    }
    nascondi();
    var attesa = null;
    new w.MutationObserver(function () {
      if (attesa) return;
      attesa = w.setTimeout(function () { attesa = null; if (giri++ < 400) nascondi(); }, 700);
    }).observe(d.body, {childList: true, subtree: true});
  } catch (err) { /* se non si può, resta com'è */ }
})();
"""


def _nav_pagina_js(codice):
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\\\"stApp\\\"],.stApp,[data-testid=\\\"stAppViewContainer\\\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(codice) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_nav
            _comp_nav.html(pagina, height=0)
    except Exception:
        pass


def nav_pulisci_interfaccia():
    """Nasconde la linguetta «Manage app» (una volta per sessione)."""
    if st.session_state.get("_nav_js"):
        return
    st.session_state["_nav_js"] = True
    _nav_pagina_js(_JS_PULIZIA)


def nav_vai(sezione):
    """Porta alla sezione indicata (lo stesso effetto delle icone della Home). Si usa come on_click di un pulsante."""
    for k in _STATI_DA_CHIUDERE:
        st.session_state.pop(k, None)
    if sezione == "dispensa":
        st.session_state.pop("sezione_home", None)
        st.session_state["farmacia_aperta"] = False
    elif sezione == "salute":
        st.session_state.pop("sezione_home", None)
        st.session_state["farmacia_aperta"] = True
    else:
        st.session_state["sezione_home"] = sezione
        st.session_state["farmacia_aperta"] = True


def nav_barra(sezione):
    """I due pulsanti in alto: sezione precedente a sinistra, successiva a destra (solo se ci sono)."""
    nav_pulisci_interfaccia()
    i = SEZIONI_NAV.index(sezione)
    prec = SEZIONI_NAV[i - 1] if i > 0 else None
    succ = SEZIONI_NAV[i + 1] if i < len(SEZIONI_NAV) - 1 else None
    c1, c2 = st.columns(2, gap="small")
    if prec:
        c1.button(f"← {NOMI_NAV[prec]}", key=f"nav_prec_{sezione}", width="stretch", on_click=nav_vai, args=(prec,))
    if succ:
        c2.button(f"{NOMI_NAV[succ]} →", key=f"nav_succ_{sezione}", width="stretch", on_click=nav_vai, args=(succ,))
