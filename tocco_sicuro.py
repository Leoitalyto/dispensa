# -*- coding: utf-8 -*-
"""👆 Tocco sicuro (tutta l'app): sul telefono, con la tastiera aperta, il primo tocco su «Salva» spesso si perde (la tastiera si chiude, lo schermo si sposta e il tocco cade a vuoto).
Questo piccolo script nella pagina: 1) se tocchi un bottone mentre scrivi in un campo, chiude la tastiera, aspetta che il testo sia registrato e poi preme il bottone da solo (un tocco basta);
2) appena tocchi un bottone di SALVATAGGIO (Salva, 💾, Conferma, Invia, Registra) lo mostra «occupato» per un attimo, così non lo tocchi due volte. Prefisso: ts_"""
import json as _ts_json

import streamlit as st

TS_JS = r"""
(function(){
if(window.__tsOK)return;window.__tsOK=1;
var css=document.createElement('style');
css.textContent='@keyframes ts-p{0%{opacity:.55}50%{opacity:.95}100%{opacity:.55}}button.ts-occ{animation:ts-p .7s ease-in-out infinite;pointer-events:none !important;filter:brightness(1.15)}';
document.head.appendChild(css);
var st=null;
function bottone(t){return t&&t.closest?t.closest('button'):null;}
function campo(){var a=document.activeElement;return a&&(a.tagName==='INPUT'||a.tagName==='TEXTAREA');}
function occupa(b){var tx=(b.textContent||'');
 if(/salva|\uD83D\uDCBE|conferma|invia|registra/i.test(tx)){b.classList.add('ts-occ');setTimeout(function(){b.classList.remove('ts-occ');},2600);}}
document.addEventListener('touchstart',function(e){var b=bottone(e.target);
 if(!b||b.disabled||!e.touches||e.touches.length!==1||b.closest('[data-testid="stNumberInput"],[data-testid="stDateInput"],[data-testid="stTimeInput"],[data-baseweb="popover"]')){st=null;return;}
 st={b:b,x:e.touches[0].clientX,y:e.touches[0].clientY,campo:campo(),moved:false};},{passive:true,capture:true});
document.addEventListener('touchmove',function(e){if(st&&e.touches&&e.touches[0]&&(Math.abs(e.touches[0].clientX-st.x)>12||Math.abs(e.touches[0].clientY-st.y)>12))st.moved=true;},{passive:true,capture:true});
document.addEventListener('touchend',function(e){var s=st;st=null;
 if(!s||s.moved||!s.campo||!e.cancelable)return;
 e.preventDefault();                                   // niente tocco "storto": faccio io i passi nell'ordine giusto
 try{document.activeElement.blur();}catch(x){}
 setTimeout(function(){if(document.body.contains(s.b)&&!s.b.disabled){occupa(s.b);s.b.click();}},180);},{passive:false,capture:true});
document.addEventListener('click',function(e){var b=bottone(e.target);if(b&&!b.disabled&&!b.classList.contains('ts-occ'))occupa(b);},true);
})();
(function(){
// CAMBIO DI PAGINA PULITO: mentre la pagina nuova si disegna, la pagina vecchia (sbiadita, «stale») resta sotto e scivola giù a pezzi: sembra che la schermata «coli».
// Quando si tocca un bottone che cambia pagina, i pezzi vecchi spariscono subito; la pagina nuova compare dall'alto, pulita. Tornano normali appena la pagina è pronta.
// Il bottone PayPal: le sue copie vecchie non si vedono mai (prima, per un attimo, comparivano una sotto l'altra).
if(window.__tsNav)return;window.__tsNav=1;
var css=document.createElement('style');
css.textContent='body.vm-cambio [data-testid="stElementContainer"][data-stale="true"]{display:none !important}'
 +'[data-testid="stElementContainer"][data-stale="true"]:has([class*="st-key-dn_badge"]),[class*="st-key-dn_badge"] [data-stale="true"]{display:none !important}'
 +'[data-testid="stElementContainer"]{transition:none !important}';
document.head.appendChild(css);
function fine(){document.body.classList.remove('vm-cambio');}
function pagina(b){return !!(b.closest&&b.closest('[class*="st-key-vmh_"],[class*="st-key-navp_"],[class*="st-key-navpa_"],[class*="st-key-vm_torna"],[class*="st-key-nav_pagine"],[class*="st-key-sezh_"],[class*="st-key-lv_hub"],[class*="st-key-an_b_"]'));}
document.addEventListener('click',function(e){var b=e.target&&e.target.closest?e.target.closest('button'):null;
 if(!b||!pagina(b))return;
 document.body.classList.add('vm-cambio');
 var app=document.querySelector('[data-test-script-state]'),visto=false,t0=Date.now();
 var iv=setInterval(function(){var s=app?app.getAttribute('data-test-script-state'):'';
  if(s==='running')visto=true;
  if((visto&&s!=='running')||Date.now()-t0>9000){clearInterval(iv);setTimeout(fine,120);}},80);},true);
})();
"""


def ts_installa():
    """Si chiama a ogni pagina: lo script si installa una volta sola (e una sola volta per ridisegnata)."""
    giro = st.session_state.get("_vm_run")
    if giro is not None and st.session_state.get("_ts_fatto") == giro:
        return
    st.session_state["_ts_fatto"] = giro
    try:
        cod = ("<!doctype html><html><body><script>(function(){try{var P=window.parent;if(P.__tsOK)return;var s=P.document.createElement('script');s.textContent="
               + _ts_json.dumps(TS_JS).replace("</", "<\\/") + ";P.document.head.appendChild(s);}catch(e){}})();</script></body></html>")
        with st.container(key="nascosti_ts_js"):
            if "_mostra_editor" in globals():
                _mostra_editor(cod, 1)
            elif hasattr(st, "iframe"):
                st.iframe(cod, height=1)
            else:
                import streamlit.components.v1 as _c
                _c.html(cod, height=1)
        st.markdown("<style>[class*='st-key-nascosti_ts_js']{display:none !important}</style>", unsafe_allow_html=True)
    except Exception:
        pass


try:
    ts_installa()                    # anche nella Home e nella pagina di accesso (prima solo nelle sezioni)
except Exception:
    pass
