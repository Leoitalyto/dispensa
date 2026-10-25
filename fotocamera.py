# -*- coding: utf-8 -*-
"""Tasto 'Scatta foto' che apre subito la fotocamera POSTERIORE (non quella dei selfie).
Il tasto ha un suo campo nascosto con capture="environment"; la foto scattata viene passata al campo di caricamento
dell'app, accanto al tasto 'Carica dal telefono'. Va caricato per ultimo da app_dispensa.py."""
import json

_JS_FOTO = r"""
(function () {
  var w = window, doc = w.document;
  /* 1) la fotocamera interna (riserva) parte dal lato posteriore */
  try {
    var md = w.navigator.mediaDevices;
    if (md && md.getUserMedia && !w.__gumPatched) {
      w.__gumPatched = true;
      var orig = md.getUserMedia.bind(md);
      md.getUserMedia = function (c) {
        try {
          if (c && c.video) {
            if (c.video === true) c.video = {};
            if (typeof c.video === 'object') { delete c.video.deviceId; c.video.facingMode = {ideal: 'environment'}; }
          }
        } catch (e) {}
        return orig(c);
      };
    }
  } catch (e) {}
  /* 1b) pulsante 'Volantini' sulle schede: manda l'id del prodotto al campo nascosto di Streamlit */
  try {
    if (!w.__volAttivo) {
      w.__volAttivo = true;
      doc.addEventListener('click', function (e) {
        var el = e.target && e.target.closest ? e.target.closest('[data-vol]') : null;
        if (!el) return;
        var inp = doc.querySelector('input[aria-label="volantini-trigger"]');
        if (!inp) return;
        e.preventDefault(); e.stopPropagation();
        var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, el.getAttribute('data-vol') + '|' + Date.now());
        inp.dispatchEvent(new w.Event('input', {bubbles: true}));
        inp.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
        inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
      }, true);
    }
  } catch (e) {}
  /* 2) tasti 'Scatta' e 'Carica dal telefono': aprono la fotocamera vera (lato posteriore) o la galleria del telefono
        e passano la foto al campo nascosto di Streamlit */
  try {
    if (w.__scattaAttivo) return;
    w.__scattaAttivo = true;
    doc.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('button') : null;
      if (!b) return;
      var c = b.closest('[class*="st-key-scatta_"],[class*="st-key-galleria_"]');
      if (!c) return;
      var cls = c.className || '';
      var m = cls.match(/st-key-(scatta|galleria)_(\S+)/);
      if (!m) return;
      var camera = (m[1] === 'scatta'), chiave = m[2];
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
      var inp = doc.createElement('input');
      inp.type = 'file'; inp.accept = 'image/*'; inp.style.display = 'none';
      if (camera) inp.setAttribute('capture', 'environment');
      inp.addEventListener('change', function () {
        var f = inp.files && inp.files[0];
        if (f) {
          var dest = doc.querySelector('[class~="st-key-' + (camera ? 'fotocam_' : 'fotogal_') + chiave + '"] input[type="file"]');
          if (dest) {
            var dt = new w.DataTransfer(); dt.items.add(f); dest.files = dt.files;
            dest.dispatchEvent(new w.Event('change', {bubbles: true}));
          }
        }
        if (inp.parentNode) inp.parentNode.removeChild(inp);
      });
      doc.body.appendChild(inp);
      inp.click();
    }, true);
  } catch (e) {}
})();
"""


def _avvia_fotocamera_posteriore():
    codice = _JS_FOTO.replace("__TESTO__", json.dumps(t("Scatta foto"), ensure_ascii=False))
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
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
            import streamlit.components.v1 as _comp_foto
            _comp_foto.html(pagina, height=0)
    except Exception:
        pass


_avvia_fotocamera_posteriore()
