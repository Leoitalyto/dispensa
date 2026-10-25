# -*- coding: utf-8 -*-
"""Tasto 'Scatta foto' che apre subito la fotocamera POSTERIORE (non quella dei selfie).
Il tasto ha un suo campo nascosto con capture="environment"; la foto scattata viene passata al campo di caricamento
dell'app, accanto al tasto 'Carica dal telefono'. Va caricato per ultimo da app_dispensa.py."""
import json

_JS_FOTO = r"""
(function () {
  var w = window, doc = w.document;
  try {
    w.__fotoTesto = __TESTO__;
    if (w.__fotoAttivo) { if (w.__fotoApplica) w.__fotoApplica(); return; }
    w.__fotoAttivo = true;
    function crea(box) {
      var btn = doc.createElement('button');
      btn.type = 'button'; btn.className = 'cam-btn';
      btn.innerHTML = '<span>📷</span>' + (w.__fotoTesto || 'Scatta foto');
      var inp = doc.createElement('input');
      inp.type = 'file'; inp.accept = 'image/*'; inp.setAttribute('capture', 'environment'); inp.style.display = 'none';
      btn.appendChild(inp);
      btn.addEventListener('click', function (e) { if (e.target !== inp) { e.preventDefault(); inp.click(); } });
      inp.addEventListener('change', function () {
        var f = inp.files && inp.files[0];
        var dest = box.querySelector('input[type="file"]:not(.cam-btn input)');
        if (!f || !dest) return;
        var dt = new w.DataTransfer(); dt.items.add(f);
        dest.files = dt.files;
        dest.dispatchEvent(new w.Event('change', {bubbles: true}));
        inp.value = '';
      });
      box.insertBefore(btn, box.firstChild);
    }
    function applica() {
      var boxes = doc.querySelectorAll('[class*="st-key-fotocam_"]');
      for (var i = 0; i < boxes.length; i++) {
        var b = boxes[i];
        if (!b.querySelector(':scope > .cam-btn')) crea(b);
        else b.querySelector(':scope > .cam-btn').firstChild.nextSibling.textContent = w.__fotoTesto || 'Scatta foto';
      }
    }
    w.__fotoApplica = applica;
    new w.MutationObserver(applica).observe(doc.body, {childList: true, subtree: true});
    applica();
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
