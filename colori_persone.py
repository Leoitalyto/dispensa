# -*- coding: utf-8 -*-
"""COLORI DELLE PERSONE · ogni persona della famiglia ha il SUO colore neon in tutta l'app.

Il primo profilo (tu) è BLU elettrico, il secondo FUCSIA, poi verde e arancio (gli stessi colori degli avvisi al neon di Casa).
Dove si vede: le pillole «👤 Nome» per scegliere di chi sono la casa, gli appuntamenti, i numeri…; i pulsanti con «👤 Nome»;
le scelte «👤 Nome» dei pulsanti tondi; i titoli con «👤 Nome»; i menu a tendina che mostrano il nome di una persona (Salute).
La persona SCELTA si illumina col suo colore pieno; le altre hanno solo il bordo e il nome del loro colore.
Come: un piccolo script (iniettato una volta, e di nuovo solo se cambiano i nomi dei profili) riconosce il nome nel testo
e mette sull'elemento data-vmp="0|1|2|3"; il colore lo dà il CSS qui sotto. Nessun dato cambia."""
import json as _cp_json

import streamlit as st

_CP_COLORI = (("#1e90ff", "#8fd0ff", "0,14,48"), ("#ff1fd2", "#ff9bef", "48,0,40"), ("#39ff14", "#b6ff9e", "6,36,0"), ("#ff8c00", "#ffc680", "48,24,0"))


def _cp_css():
    H = "html body "
    out = []
    for i, (col, chiaro, bg) in enumerate(_CP_COLORI):
        a = f'[data-vmp="{i}"]' * 3                                            # ripetuto: vince sulle regole del tema (più specifiche)
        on = ",".join(H + f"button{a}{x}" for x in ('[aria-checked="true"]', '[data-selected="true"]', '[aria-selected="true"]', '[data-testid$="Active"]'))
        on_in = ",".join(H + f"button{a}{x} {t}" for x in ('[aria-checked="true"]', '[data-selected="true"]', '[aria-selected="true"]', '[data-testid$="Active"]') for t in ("p", "span", "div"))
        out.append(f"{H}button{a}{{border:2px solid {col} !important;color:{chiaro} !important;background:rgba({bg},.55) !important;box-shadow:none !important}}")
        out.append(f"{H}button{a} p,{H}button{a} span,{H}button{a} div{{color:{chiaro} !important}}")
        out.append(f"{on}{{background:rgba({bg},.95) !important;color:#fff !important;border:2px solid {col} !important;"
                   f"text-shadow:0 0 6px {chiaro},0 0 12px {col};box-shadow:0 0 6px {col},0 0 16px {col},inset 0 0 6px {col} !important}}")
        out.append(f"{on_in}{{color:#fff !important}}")
        out.append(",".join(H + t + a + x for t in ("label", "h1", "h2", "h3", "h4", "h5", "h6") for x in ("", " p")) + f"{{color:{col} !important;text-shadow:0 0 8px {col}}}")
        out.append(f"{H}div{a}[data-vmsel]{{border:2px solid {col} !important;box-shadow:0 0 6px {col},0 0 14px {col} !important;border-radius:10px}}")
    return "\n".join(out)


CP_CSS = "\n/* ===== colori delle persone (blu elettrico, fucsia…) ===== */\n" + _cp_css() + "\n"

_CP_JS = r"""(function(){var w=window,d=w.document;
if(!d.getElementById('vm-pers-css')){var st_=d.createElement('style');st_.id='vm-pers-css';st_.textContent=w.__vmPersCss||'';d.head.appendChild(st_);}
w.__vmPersScan=function(){var N=(w.__vmPersone||[]).map(function(n,i){return [String(n||'').trim(),i];}).filter(function(x){return x[0];});
 N.sort(function(a,b){return b[0].length-a[0].length;});
 function trova(t,soloNome){t=(t||'').replace(/\s+/g,' ').trim();if(!t)return -1;
  for(var k=0;k<N.length;k++){var n=N[k][0];
   if(soloNome){if(t===n||t.indexOf(n+' ·')===0||t.indexOf(n+' (')===0)return N[k][1];continue;}
   var p=t.indexOf('👤 '+n);if(p<0)continue;var dopo=t.charAt(p+3+n.length);
   if(!dopo||!/[A-Za-zÀ-ÿ]/.test(dopo))return N[k][1];}
  return -1;}
 function metti(el,i,sel){if(i<0){if(el.hasAttribute('data-vmp'))el.removeAttribute('data-vmp');return;}
  i=String(i%4);if(el.getAttribute('data-vmp')!==i)el.setAttribute('data-vmp',i);if(sel)el.setAttribute('data-vmsel','1');}
 var l=d.querySelectorAll('button,label,h1,h2,h3,h4,h5,h6');
 for(var j=0;j<l.length;j++){var e=l[j];if(e.closest&&e.closest('[class*="st-key-neon"]'))continue;
  var t=(e.innerText||'').slice(0,160);if(e.__vmpT===t)continue;e.__vmpT=t;metti(e,trova(t,false),false);}
 var s=d.querySelectorAll('[data-baseweb="select"]>div');
 for(var j=0;j<s.length;j++){var e=s[j];var t=(e.innerText||'').slice(0,120);if(e.__vmpT===t)continue;e.__vmpT=t;
  var i=trova(t,true);if(i<0)i=trova(t,false);metti(e,i,true);}};
if(!w.__vmPersOss){w.__vmPersOss=1;
 new MutationObserver(function(){w.clearTimeout(w.__vmPersT);w.__vmPersT=w.setTimeout(w.__vmPersScan,120);}).observe(d.body,{childList:true,subtree:true,characterData:true});}
})();"""

if "CSS" in globals():
    CSS = CSS.replace("</style>", CP_CSS + "\n</style>")


def cp_nomi():
    try:
        return [n for _i, n in cpf_profili()]
    except Exception:
        return []


def cp_inietta():
    """Manda allo script i nomi dei profili (solo la prima volta e quando cambiano) e lo fa ripassare sulla pagina."""
    try:
        nomi = cp_nomi()
        firma = _cp_json.dumps(nomi, ensure_ascii=False)
        if len(nomi) < 2 or st.session_state.get("_inj_cp") == firma or "_inietta" not in globals():
            return
        st.session_state["_inj_cp"] = firma
        _inietta("window.__vmPersone=" + firma + ";window.__vmPersCss=" + _cp_json.dumps(CP_CSS) + ";" + _CP_JS + "for(var _i=0;_i<4;_i++)window.setTimeout(function(){document.querySelectorAll('[data-vmp],button,label').forEach(function(e){e.__vmpT=null;});window.__vmPersScan();},_i*400);")
    except Exception:
        pass


if "_cp_nav_prima" not in globals() and "nav_pagine" in globals():
    _cp_nav_prima = nav_pagine


def nav_pagine(corrente):
    r = _cp_nav_prima(corrente)
    cp_inietta()
    return r
