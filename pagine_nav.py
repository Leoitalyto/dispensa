# -*- coding: utf-8 -*-
"""NAVIGAZIONE CHIARA E FRECCIA «TORNA SU».

1) nav_pagine(corrente): sei bottoni grandi, con la scritta dentro ben leggibile e un colore intenso per ogni pagina
   (Dispensa verde, Salute rosso, I miei documenti azzurro, Archivio indaco, Casa arancione, Utilità viola).
   Compare sotto il titolo della Dispensa e in cima a ogni sezione (al posto delle vecchie frecce ← →).
   La pagina in cui ti trovi ha un bordo bianco e un pallino. Le sezioni nascoste a una persona («Sezioni visibili») non compaiono.
2) pn_freccia_su(): una piccola freccia tonda, trasparente, che compare solo quando si scorre in basso e riporta in cima con un tocco.
   Sta a DESTRA (predefinito) o a SINISTRA, a scelta, sopra l'assistente e i pulsanti in basso, per non coprire le scritte.
   La scelta si fa in Utilità → «⚙️ Aspetto dell'app» e si ricorda per ogni persona.
Caricato da app_dispensa.py dopo sezioni.py."""
import json

import streamlit as st

_PN_VOCI = [
    ("dispensa", "🏠 Dispensa", "#2ec4a6", "#00695c"),
    ("salute", "🩺 Salute", "#ff6f60", "#b71c1c"),
    ("documenti", "📁 I miei documenti", "#42b0ff", "#01579b"),
    ("archivio", "🗂️ Archivio", "#7986cb", "#283593"),
    ("casa", "🏡 Casa", "#ffb74d", "#d84315"),
    ("lavoro", "💼 Lavoro", "#90a4ae", "#37474f"),
    ("utilita", "🧰 Utilità", "#c46bdc", "#4a148c"),
]


def _pn_css(corrente):
    r = ["<style>"
         ".st-key-nav_pagine[data-testid='stVerticalBlock'],.st-key-nav_pagine [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:6px 0 12px}"
         ".st-key-nav_pagine button{width:100% !important;min-height:58px !important;border-radius:18px !important;color:#fff !important;font-weight:900 !important;"
         "border:2px solid rgba(255,255,255,.55) !important;box-shadow:0 4px 0 rgba(0,0,0,.25) !important;padding:6px 8px !important}"
         ".st-key-nav_pagine button p{color:#fff !important;font-weight:900 !important;font-size:1.04rem !important;line-height:1.15 !important;text-shadow:0 1px 3px rgba(0,0,0,.55);margin:0}"
         ".st-key-nav_pagine button:active{transform:translateY(2px);box-shadow:0 2px 0 rgba(0,0,0,.25) !important}"]
    for sez, _, c1, c2 in _PN_VOCI:
        r.append(f".st-key-navp_{sez} button,.st-key-navpa_{sez} button{{background:linear-gradient(135deg,{c1} 0%,{c2} 100%) !important}}")
        r.append(f".st-key-navpa_{sez} button{{outline:3px solid #fff !important;outline-offset:-5px;box-shadow:0 0 0 3px {c2},0 5px 0 rgba(0,0,0,.3) !important}}")
    r.append("@media (max-width:340px){.st-key-nav_pagine[data-testid='stVerticalBlock'],.st-key-nav_pagine [data-testid='stVerticalBlock']{grid-template-columns:1fr}}</style>")
    return "".join(r)


def nav_pagine(corrente):
    """I bottoni colorati per passare da una pagina all'altra."""
    nasc = sv_nascoste() if "sv_nascoste" in globals() else set()
    st.markdown(_pn_css(corrente), unsafe_allow_html=True)
    with st.container(key="nav_pagine"):
        for sez, etichetta, _c1, _c2 in _PN_VOCI:
            if sez != "dispensa" and ("SEZIONI_NAV" in globals() and sez not in SEZIONI_NAV):
                continue
            if sez in nasc:
                continue
            attiva = sez == corrente
            st.button(("● " if attiva else "") + etichetta, key=("navpa_" if attiva else "navp_") + sez, width="stretch",
                      on_click=(None if attiva else nav_vai), args=(None if attiva else (sez,)))
    pn_freccia_su()


# ---------------------------------------------------------------------------------------------------------------------
# la freccia «torna su»
# ---------------------------------------------------------------------------------------------------------------------
_PN_JS = r"""
(function () {
  var w = window, doc = w.document, lato = __LATO__;
  var vecchia = doc.getElementById('pn-su');
  if (vecchia) { vecchia.setAttribute('data-lato', lato); vecchia.style[lato === 'sinistra' ? 'left' : 'right'] = '8px'; vecchia.style[lato === 'sinistra' ? 'right' : 'left'] = 'auto'; return; }
  var b = doc.createElement('button');
  b.id = 'pn-su'; b.type = 'button'; b.setAttribute('aria-label', 'Torna in cima'); b.setAttribute('data-lato', lato); b.textContent = '▲';
  b.style.cssText = 'position:fixed;bottom:250px;width:34px;height:34px;border-radius:50%;border:1px solid rgba(255,255,255,.7);background:rgba(0,105,92,.55);color:#fff;font-size:15px;line-height:30px;opacity:.55;'
    + 'padding:0;z-index:99990;display:none;box-shadow:0 2px 6px rgba(0,0,0,.2);cursor:pointer;-webkit-tap-highlight-color:transparent;transition:opacity .15s';
  b.addEventListener('touchstart', function () { b.style.opacity = '1'; }, {passive: true});
  b.style[lato === 'sinistra' ? 'left' : 'right'] = '8px';
  doc.body.appendChild(b);
  function contenitori() {
    var c = [doc.querySelector('[data-testid="stMain"]'), doc.querySelector('section.main'), doc.querySelector('[data-testid="stAppViewContainer"]'), doc.scrollingElement, doc.documentElement, doc.body];
    return c.filter(function (x) { return !!x; });
  }
  function posizione() {
    var m = 0, c = contenitori();
    for (var i = 0; i < c.length; i++) { m = Math.max(m, c[i].scrollTop || 0); }
    return Math.max(m, w.pageYOffset || 0);
  }
  function aggiorna() { b.style.display = posizione() > 500 ? 'block' : 'none'; }
  doc.addEventListener('scroll', aggiorna, true);
  w.addEventListener('scroll', aggiorna, true);
  w.setInterval(aggiorna, 700);
  b.addEventListener('click', function (e) {
    e.preventDefault(); e.stopPropagation();
    var c = contenitori();
    for (var i = 0; i < c.length; i++) { try { c[i].scrollTo({top: 0, behavior: 'smooth'}); } catch (x) { c[i].scrollTop = 0; } }
    try { w.scrollTo({top: 0, behavior: 'smooth'}); } catch (x) { w.scrollTo(0, 0); }
  });
})();
"""


def pn_lato():
    """«destra» (predefinito) o «sinistra»: la scelta della persona, ricordata nei suoi dati."""
    if "pn_lato" not in st.session_state:
        lato = "destra"
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"]) or {}
            lato = (d.get("impostazioni") or {}).get("freccia", "destra")
        except Exception:
            pass
        st.session_state["pn_lato"] = lato if lato in ("destra", "sinistra") else "destra"
    return st.session_state["pn_lato"]


def pn_freccia_su():
    """Mette (o aggiorna) la freccia «torna su» nella pagina."""
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_PN_JS.replace("__LATO__", json.dumps(pn_lato()))) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_pn
            _comp_pn.html(pagina, height=0)
    except Exception:
        pass


def pn_impostazioni():
    """Il riquadro «⚙️ Aspetto dell'app» (in Utilità): da che parte sta la freccia «torna su»."""
    with st.expander("⚙️ Aspetto dell'app: freccia «torna su»"):
        scelta = st.radio("La freccia che riporta in cima sta a…", ["destra", "sinistra"], index=0 if pn_lato() == "destra" else 1, horizontal=True, key="pn_lato_scelta",
                          format_func=lambda x: "➡️ destra (predefinito)" if x == "destra" else "⬅️ sinistra")
        st.caption("Compare in basso solo quando scorri una pagina lunga, e con un tocco ti riporta all'inizio. Sta sopra i pulsanti in basso, per non coprire le scritte.")
        if scelta != pn_lato():
            st.session_state["pn_lato"] = scelta
            try:
                def _fn(d, v=scelta):
                    d.setdefault("impostazioni", {})["freccia"] = v
                salva(_fn, "Aspetto: lato della freccia")
            except Exception as e:
                st.warning(f"Non sono riuscito a ricordare la scelta: {e}")
            st.rerun()


# ---- aggancio: le vecchie frecce ← → diventano i bottoni colorati; l'impostazione compare in Utilità
if "nav_barra" in globals() and "_pn_nav_prima" not in globals():
    _pn_nav_prima = nav_barra

    def nav_barra(sezione):                                          # noqa: F811
        try:
            return nav_pagine(sezione)
        except Exception:
            return _pn_nav_prima(sezione)

if "schermata_utilita" in globals() and "_pn_utilita_prima" not in globals():
    _pn_utilita_prima = schermata_utilita

    def schermata_utilita():                                         # noqa: F811
        _pn_utilita_prima()
        try:
            pn_impostazioni()
        except Exception:
            pass
