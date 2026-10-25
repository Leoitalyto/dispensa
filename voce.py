# -*- coding: utf-8 -*-
"""Dettatura vocale: un'icona microfono dentro i campi di testo adatti. Si tocca, si parla, il testo compare nel campo
(poi si puo' correggere a mano). Usa il riconoscimento vocale del browser (Chrome su Android); dove non c'e', i pulsanti non compaiono.
Va caricato per ultimo da app_dispensa.py."""
import json

_LINGUE_VOCE = {"it": "it-IT", "en": "en-GB", "es": "es-ES", "fr": "fr-FR", "de": "de-DE", "ro": "ro-RO", "ar": "ar-SA"}

# etichetta del campo -> come si inserisce il testo detto ("sostituisci" = al posto del testo, "aggiungi" = dopo quello gia' scritto)
_CAMPI_VOCE = [
    ("Nome del prodotto *", "sostituisci", "nome"), ("Marca", "sostituisci", "nome"), ("Categoria", "sostituisci", "nome"),
    ("Note (facoltative)", "aggiungi", "testo"), ("Ingredienti", "aggiungi", "testo"),
    ("Codice a barre (i numeri sotto le barre)", "sostituisci", "cifre"),
    ("Il tuo messaggio", "aggiungi", "testo"), ("Risposta", "aggiungi", "testo"),
    ("Nome della persona", "sostituisci", "nome"), ("Cosa devi comprare?", "sostituisci", "nome"),
]

_JS_VOCE = r"""
(function () {
  var w = (window.parent && window.parent !== window) ? window.parent : window;
  var CONFIG = __CONFIG__;
  w.__vocaleConfig = CONFIG;
  if (w.__vocaleAttivo) { if (w.__vocaleScansiona) w.__vocaleScansiona(); return; }
  var SR = w.SpeechRecognition || w.webkitSpeechRecognition;
  if (!SR) return;
  w.__vocaleAttivo = true;
  var doc = w.document;
  var stile = doc.createElement('style');
  stile.textContent = '.vc-mic{position:absolute;right:8px;top:50%;transform:translateY(-50%);width:34px;height:34px;border-radius:50%;border:0;' +
    'background:linear-gradient(135deg,#1CAA70,#169A88);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;z-index:5;' +
    'box-shadow:0 3px 8px rgba(22,154,136,.4)}.vc-mic.vc-area{top:10px;transform:none}' +
    '.vc-mic.vc-on{background:#E5484D;animation:vcp 1s infinite}@keyframes vcp{0%{box-shadow:0 0 0 0 rgba(229,72,77,.6)}100%{box-shadow:0 0 0 12px rgba(229,72,77,0)}}' +
    '.vc-msg{font-size:12px;font-weight:600;margin:2px 0 0 4px;color:#B3261E}.vc-msg.vc-ok{color:#0B7A69}';
  doc.head.appendChild(stile);
  var ICONA = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0M12 18v3"></path></svg>';
  var CIFRE = {zero: '0', uno: '1', una: '1', due: '2', tre: '3', quattro: '4', cinque: '5', sei: '6', sette: '7', otto: '8', nove: '9',
               one: '1', two: '2', three: '3', four: '4', five: '5', six: '6', seven: '7', eight: '8', nine: '9'};
  var attivo = null;

  function norm(s) {
    return (s || '').toLowerCase().replace(/[*:\u2026]/g, '').replace(/[^\p{L}\p{N} ]/gu, ' ').replace(/\s+/g, ' ').trim();
  }
  function testo(chiave) { return (CONFIG.testi && CONFIG.testi[chiave]) || ''; }

  function imposta(el, valore) {
    var proto = el.tagName === 'TEXTAREA' ? w.HTMLTextAreaElement.prototype : w.HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, valore);
    el.dispatchEvent(new w.Event('input', {bubbles: true}));
    el.dispatchEvent(new w.Event('change', {bubbles: true}));
    el.dispatchEvent(new w.FocusEvent('blur'));
    el.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
  }

  function pulisci(s, c) {
    s = (s || '').trim();
    if (c.tipo === 'cifre') {
      return s.toLowerCase().split(/[\s,.-]+/).map(function (p) { return CIFRE[p] !== undefined ? CIFRE[p] : p; }).join('').replace(/[^0-9]/g, '');
    }
    if (c.modo === 'sostituisci') { s = s.replace(/[.!?,;:\u061F\u060C]+$/, ''); return s.charAt(0).toUpperCase() + s.slice(1); }
    return s;
  }

  function messaggio(cont, chiave, ok) {
    var vecchio = cont.parentElement && cont.parentElement.querySelector('.vc-msg');
    if (vecchio) vecchio.remove();
    var m = doc.createElement('div');
    m.className = 'vc-msg' + (ok ? ' vc-ok' : '');
    m.textContent = testo(chiave);
    cont.insertAdjacentElement('afterend', m);
    w.setTimeout(function () { if (m.parentElement) m.remove(); }, 4000);
  }

  function ascolta(el, c, b, cont) {
    if (attivo) {
      var stessa = attivo.el === el;
      try { attivo.rec.stop(); } catch (e) {}
      attivo = null;
      if (stessa) return;
    }
    var rec = new SR();
    rec.lang = CONFIG.lang || 'it-IT';
    rec.interimResults = false;
    rec.continuous = false;
    rec.maxAlternatives = 1;
    var detto = '';
    attivo = {rec: rec, el: el};
    b.classList.add('vc-on');
    messaggio(cont, 'ascolto', true);
    rec.onresult = function (e) {
      for (var i = e.resultIndex; i < e.results.length; i++) { if (e.results[i].isFinal) detto += e.results[i][0].transcript + ' '; }
    };
    rec.onerror = function (e) {
      var perm = (e.error === 'not-allowed' || e.error === 'service-not-allowed');
      messaggio(cont, perm ? 'permesso' : (e.error === 'no-speech' ? 'nulla' : 'errore'), false);
    };
    rec.onend = function () {
      b.classList.remove('vc-on');
      attivo = null;
      var vm = cont.parentElement && cont.parentElement.querySelector('.vc-msg.vc-ok');
      if (vm) vm.remove();
      var nuovo = pulisci(detto, c);
      if (!nuovo) return;
      if (c.modo === 'aggiungi' && el.value && el.value.trim()) nuovo = el.value.replace(/\s+$/, '') + ' ' + nuovo;
      imposta(el, nuovo);
    };
    try { rec.start(); } catch (err) { b.classList.remove('vc-on'); attivo = null; }
  }

  function aggiungi(el, c) {
    var cont = el.closest('[data-baseweb="input"],[data-baseweb="textarea"]') || el.parentElement;
    if (!cont) return;
    el.dataset.vcFatto = '1';
    cont.style.position = 'relative';
    el.style.paddingRight = '48px';
    var b = doc.createElement('button');
    b.type = 'button';
    b.className = 'vc-mic' + (el.tagName === 'TEXTAREA' ? ' vc-area' : '');
    b.innerHTML = ICONA;
    b.setAttribute('aria-label', testo('detta'));
    b.title = testo('detta');
    b.addEventListener('click', function (ev) { ev.preventDefault(); ev.stopPropagation(); ascolta(el, c, b, cont); });
    cont.appendChild(b);
  }

  function scansiona() {
    var campi = (w.__vocaleConfig && w.__vocaleConfig.campi) || [];
    doc.querySelectorAll('input[type=text], input:not([type]), textarea').forEach(function (el) {
      if (el.dataset.vcFatto) return;
      var nome = norm(el.getAttribute('aria-label'));
      if (!nome) return;
      for (var i = 0; i < campi.length; i++) {
        if (norm(campi[i].etichetta) === nome) { aggiungi(el, campi[i]); break; }
      }
    });
  }
  w.__vocaleScansiona = scansiona;
  var attesa = null;
  new w.MutationObserver(function () {
    if (attesa) return;
    attesa = w.setTimeout(function () { attesa = null; scansiona(); }, 250);
  }).observe(doc.body, {childList: true, subtree: true});
  scansiona();
})();
"""


def _avvia_voce():
    config = {
        "lang": _LINGUE_VOCE.get(lingua(), "it-IT"),
        "campi": [{"etichetta": t(e), "modo": m, "tipo": tp} for e, m, tp in _CAMPI_VOCE]
                 + [{"etichetta": "🔎 " + t("Cerca"), "modo": "sostituisci", "tipo": "nome"}],
        "testi": {"detta": t("Detta con la voce"), "ascolto": t("Sto ascoltando… parla ora"),
                  "permesso": t("Consenti l'uso del microfono al browser per dettare."),
                  "nulla": t("Non ho sentito niente: riprova."), "errore": t("Non riesco a usare la voce su questo telefono.")},
    }
    codice = _JS_VOCE.replace("__CONFIG__", json.dumps(config, ensure_ascii=False))
    pagina = ("<script>(function(){var P=(window.parent&&window.parent!==window)?window.parent:window;"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(codice) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        try:
            import streamlit.components.v1 as _comp_voce
            _comp_voce.html(pagina, height=0)
        except Exception:
            pass


_avvia_voce()
