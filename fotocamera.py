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
    var MSG = __MSG__;
    var ultimo = null;                                  // l'ultimo campo scelto: {inp, camera, chiave}
    function avviso(testo, ms) {
      var el = doc.getElementById('foto-avviso');
      if (!el) {
        el = doc.createElement('div'); el.id = 'foto-avviso';
        el.style.cssText = 'position:fixed;left:50%;top:78px;transform:translateX(-50%);max-width:92vw;background:#14302b;color:#fff;padding:10px 16px;' +
          'border-radius:16px;font:600 14px/1.3 sans-serif;z-index:100002;text-align:center;box-shadow:0 8px 24px rgba(0,0,0,.35)';
        doc.body.appendChild(el);
      }
      el.textContent = testo; el.style.display = 'block';
      w.clearTimeout(el.__t); el.__t = w.setTimeout(function () { el.style.display = 'none'; }, ms || 5000);
    }
    // la foto del telefono pesa parecchi MB: la riduco prima di caricarla (molto piu' veloce e affidabile)
    function riduci(f, cb) {
      if (!w.createImageBitmap || f.size < 600000) { cb(f); return; }
      var fatto = false;
      function una(g) { if (!fatto) { fatto = true; cb(g); } }
      w.setTimeout(function () { una(f); }, 8000);       // se la riduzione si blocca, carico l'originale
      w.createImageBitmap(f, {imageOrientation: 'from-image'}).then(function (bm) {
        var s = Math.min(1, 1800 / Math.max(bm.width, bm.height));
        var c = doc.createElement('canvas'); c.width = Math.max(1, Math.round(bm.width * s)); c.height = Math.max(1, Math.round(bm.height * s));
        c.getContext('2d').drawImage(bm, 0, 0, c.width, c.height);
        c.toBlob(function (b) {
          if (!b) { una(f); return; }
          una(new w.File([b], ((f.name || 'foto').replace(/\.\w+$/, '')) + '.jpg', {type: 'image/jpeg', lastModified: Date.now()}));
        }, 'image/jpeg', 0.9);
      }).catch(function () { una(f); });
    }
    function consegna(inp) {
      var f = inp && inp.files && inp.files[0];
      if (!f || inp.__fatto === f) return;
      inp.__fatto = f;
      avviso(MSG.carico, 7000);
      riduci(f, function (g) {
        var dest = doc.querySelector('[class~="st-key-' + (inp.__camera ? 'fotocam_' : 'fotogal_') + inp.__chiave + '"] input[type="file"]');
        if (!dest) { avviso(MSG.nonarrivata, 9000); return; }
        try {
          var dt = new w.DataTransfer(); dt.items.add(g); dest.files = dt.files;
          dest.dispatchEvent(new w.Event('change', {bubbles: true}));
        } catch (err) { avviso(MSG.nonarrivata, 9000); }
      });
    }
    function ricontrolla() { if (ultimo) w.setTimeout(function () { consegna(ultimo.inp); }, 700); }
    // dopo lo scatto il telefono torna al browser: se l'evento di cambio e' andato perso, la foto si recupera da qui
    doc.addEventListener('visibilitychange', function () { if (!doc.hidden) ricontrolla(); });
    w.addEventListener('focus', ricontrolla);
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
      if (ultimo && ultimo.inp && ultimo.inp.parentNode) ultimo.inp.parentNode.removeChild(ultimo.inp);
      var inp = doc.createElement('input');
      inp.type = 'file'; inp.accept = 'image/*'; inp.style.display = 'none';
      if (camera) inp.setAttribute('capture', 'environment');
      inp.__camera = camera; inp.__chiave = chiave;
      inp.addEventListener('change', function () { consegna(inp); });
      inp.addEventListener('input', function () { consegna(inp); });
      doc.body.appendChild(inp);                        // resta nella pagina: se il telefono la ricarica, la foto si recupera
      ultimo = {inp: inp};
      inp.click();
    }, true);
  } catch (e) {}
})();
"""


def _avvia_fotocamera_posteriore():
    msg = {"carico": (_fp("foto_carico") if "_fp" in globals() else "⏳ Sto caricando la foto…"),
           "nonarrivata": (_fp("foto_non_arrivata") if "_fp" in globals() else "⚠️ La foto non è arrivata. Riprova oppure usa «Carica dal telefono».")}
    codice = _JS_FOTO.replace("__TESTO__", json.dumps(t("Scatta foto"), ensure_ascii=False)).replace("__MSG__", json.dumps(msg, ensure_ascii=False))
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
