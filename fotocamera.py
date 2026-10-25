# -*- coding: utf-8 -*-
"""Fa aprire subito la fotocamera POSTERIORE (non quella per i selfie) nei campi foto 'fotocam_...'.
Imposta capture="environment" sul campo di caricamento; funziona su Chrome/Android e Safari/iPhone.
Va caricato per ultimo da app_dispensa.py."""

_JS_FOTO = r"""
(function () {
  var w = window, doc = w.document;
  try {
    if (w.__fotoAttivo) { if (w.__fotoApplica) w.__fotoApplica(); return; }
    w.__fotoAttivo = true;
    function applica() {
      var el = doc.querySelectorAll('[class*="st-key-fotocam_"] input[type="file"]');
      for (var i = 0; i < el.length; i++) {
        if (el[i].getAttribute('capture') !== 'environment') el[i].setAttribute('capture', 'environment');
      }
    }
    w.__fotoApplica = applica;
    new w.MutationObserver(applica).observe(doc.body, {childList: true, subtree: true});
    applica();
  } catch (e) {}
})();
"""


def _avvia_fotocamera_posteriore():
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_JS_FOTO) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_foto
            _comp_foto.html(pagina, height=0)
    except Exception:
        pass


_avvia_fotocamera_posteriore()
