# -*- coding: utf-8 -*-
"""Tabella dei prodotti a SCHERMO INTERO.
Sotto la tabella della Dispensa c'è il pulsante «⛶ Schermo intero»: toccandolo il browser va a schermo intero, il telefono si mette
in orizzontale (se lo permette) e si apre la tabella grande, che si scorre con il dito. Per uscire: X, oppure indietro del telefono.
La tabella a schermo intero serve a guardare; per eliminare o modificare si usa la tabella normale.
Il pulsante è agganciato in parte3.py da app_dispensa.py. Caricato da app_dispensa.py prima di parte3.py."""
import base64
import html
import io
import json

import streamlit as st
from PIL import Image

_JS_TAB_INTERA = r"""
(function () {
  var w = window, d = w.document;
  try {
    if (w.__tabIntAttivo) return;
    w.__tabIntAttivo = true;
    var visto = false;
    function entra() {
      try {
        var el = d.documentElement;
        var p = el.requestFullscreen ? el.requestFullscreen() : (el.webkitRequestFullscreen ? el.webkitRequestFullscreen() : null);
        var gira = function () { try { w.screen.orientation.lock('landscape').catch(function () {}); } catch (e) {} };
        if (p && p.then) p.then(gira).catch(function () {}); else gira();
      } catch (e) {}
    }
    function esci() {
      try { if (w.screen.orientation && w.screen.orientation.unlock) w.screen.orientation.unlock(); } catch (e) {}
      try { if (d.fullscreenElement && d.exitFullscreen) d.exitFullscreen(); } catch (e) {}
    }
    // il clic su «Schermo intero» passa a Streamlit come sempre; qui si chiede solo lo schermo intero (serve un tocco dell'utente)
    d.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[class*="st-key-tabfull_"] button') : null;
      if (b) { visto = false; entra(); }
    }, true);
    // quando la tabella si chiude (X), si esce anche dallo schermo intero
    new w.MutationObserver(function () {
      var aperta = !!d.querySelector('.tf-marker');
      if (aperta) visto = true;
      else if (visto) { visto = false; esci(); }
    }).observe(d.body, {childList: true, subtree: true});
    d.addEventListener('fullscreenchange', function () { if (!d.fullscreenElement) { try { w.screen.orientation.unlock(); } catch (e) {} } });
  } catch (err) { /* se qualcosa non va, la tabella si apre lo stesso, a larghezza piena */ }
})();
"""

_CSS_TAB_INTERA = """<style>
div[data-testid="stDialog"] div[role="dialog"]{width:100vw !important;max-width:100vw !important;height:100vh !important;height:100dvh !important;
 max-height:100dvh !important;margin:0 !important;border-radius:0 !important}
.tf-scroll{overflow:auto;height:calc(100vh - 150px);height:calc(100dvh - 150px);-webkit-overflow-scrolling:touch;border-radius:14px;
 box-shadow:inset 0 0 0 1px rgba(0,0,0,.08)}
table.tf{border-collapse:collapse;width:100%;min-width:680px;font-size:15px}
table.tf th{position:sticky;top:0;z-index:2;background:#0f766e;color:#fff;padding:10px 8px;text-align:left;white-space:nowrap}
table.tf td{padding:6px 8px;border-bottom:1px solid rgba(0,0,0,.1);vertical-align:middle}
table.tf img{width:56px;height:56px;object-fit:contain;border-radius:8px;background:#fff;display:block}
@media (orientation:landscape){.tf-scroll{height:calc(100vh - 110px);height:calc(100dvh - 110px)}}
</style>"""

_SFONDI = {"rosso": "#ffcdd2", "arancione": "#ffe0b2", "scaduto": "#d7ccc8", "ok": "", "nessuna": ""}


@st.cache_data(show_spinner=False, max_entries=400)
def _tf_miniatura(src):
    """Una foto piccola (96 px) per la tabella grande: così si carica in fretta anche con tanti prodotti."""
    if not src or not str(src).startswith("data:image"):
        return src
    try:
        im = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1]))).convert("RGBA")
        im.thumbnail((96, 96))
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=72)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return src


def _tf_inietta_js():
    """Inserisce nella pagina lo script dello schermo intero (una volta sola per sessione)."""
    if st.session_state.get("_tf_js"):
        return
    st.session_state["_tf_js"] = True
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\\\"stApp\\\"],.stApp,[data-testid=\\\"stAppViewContainer\\\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_JS_TAB_INTERA) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_tf
            _comp_tf.html(pagina, height=0)
    except Exception:
        pass


def tf_pulsante(gruppo, sezione):
    """Il pulsante «Schermo intero» sotto la tabella (e, se premuto, la tabella a schermo intero)."""
    _tf_inietta_js()
    etichetta = rp_t("tab_intero") if "rp_t" in globals() else "⛶ Schermo intero (anche ruotando il telefono)"
    if st.button(etichetta, key="tabfull_" + sezione, width="stretch"):
        tabella_schermo_intero(gruppo, sezione)


def tabella_schermo_intero(gruppo, sezione):
    """Apre la tabella dei prodotti di una sezione a tutto schermo. gruppo = lista di (prodotto, stato, giorni)."""
    def _corpo():
        st.markdown(_CSS_TAB_INTERA, unsafe_allow_html=True)
        st.markdown("<div class='tf-marker'></div>", unsafe_allow_html=True)
        st.caption(rp_t("tab_hint") if "rp_t" in globals() else "Ruota il telefono in orizzontale per vedere meglio. Per uscire tocca la X o torna indietro.")
        e = html.escape
        intest = [t("Foto"), t("Prodotto"), t("Marca"), t("Quantità"), t("Scadenza"), t("Stato"), t("Allergeni")]
        righe = []
        for r, s, g in gruppo:
            foto = _tf_miniatura(src_sicuro(r.get("immagine") or "") or _FOTO_VUOTA)
            allerg = ", ".join(t_all(a) for a in (r.get("allergeni") or [])) or ("—" if r.get("allergeni_noti") else t("non verificati"))
            sfondo = f" style='background:{_SFONDI.get(s, '')}'" if _SFONDI.get(s) else ""
            righe.append(f"<tr{sfondo}><td><img src='{e(str(foto), quote=True)}' alt=''></td><td><b>{e(r.get('nome', ''))}</b></td>"
                         f"<td>{e(r.get('marca', ''))}</td><td>{e(str(descrivi([r])))}</td><td>{e(str(data_it(r.get('scadenza'))))}</td>"
                         f"<td>{e(ICONE[s])} {e(str(testo_giorni(s, g)))}</td><td>{e(allerg)}</td></tr>")
        testa = "".join(f"<th>{e(str(x))}</th>" for x in intest)
        st.markdown(f"<div class='tf-scroll'><table class='tf'><thead><tr>{testa}</tr></thead><tbody>{''.join(righe)}</tbody></table></div>",
                    unsafe_allow_html=True)
    st.dialog(rp_t("tab_titolo") if "rp_t" in globals() else "Tabella a schermo intero", width="large")(_corpo)()
