# -*- coding: utf-8 -*-
"""📖 Diario dei ricordi (Compleanni): sotto la scheda di OGNI persona c'è un bottone verde rotondo. Toccandolo si apre un diario con le foto ricordo:
ogni pagina è larga come la scheda, ha i bordi stondati e una cornice neon; sopra la foto si possono mettere testi colorati e icone (emoji),
scegliendo colore, grandezza, carattere e posizione. Ogni pagina ha il bottone rosso per chiudere il diario.
Dati: p["ricordi"] = [{id, foto, did, els:[{id, k:"t"|"i", t, c, s, x, y, f}]}] dentro la scheda; le foto in documenti/<uid>/ (cp_file_*). Prefisso: dr_"""
import html as _dr_html
import io as _dr_io
import uuid as _dr_uuid

import streamlit as st

DR_FONT = {"Classico": "Georgia,'Times New Roman',serif", "Corsivo": "'Brush Script MT','Segoe Script','Snell Roundhand','Apple Chancery',cursive",
           "Stampatello": "Impact,'Arial Black','Segoe UI',sans-serif", "Macchina da scrivere": "'Courier New',monospace"}
DR_ICONE = ["❤️", "🌹", "🕯️", "🕊️", "⭐", "🎂", "🎁", "🙏", "✝️", "☀️", "🌙", "🌸", "🌻", "🍀", "👼", "💐", "😊", "😢", "🥂", "🎈", "🏠", "✈️", "📷", "🎶"]
DR_COLORI = ["#ffffff", "#ffe066", "#ff8fab", "#ff5c5c", "#7dd3fc", "#86efac", "#c4b5fd", "#ffb74d", "#000000"]


def dr_pagine(p):
    return [x for x in (p.get("ricordi") or []) if isinstance(x, dict)]


def dr_files(p):
    r = [x.get("foto") for x in dr_pagine(p) if x.get("foto")]
    if isinstance(p.get("musica"), dict) and p["musica"].get("id"):
        r.append(p["musica"])
    return r


def _dr_colore(p):
    try:
        if p.get("scomparso"):
            return CP_COLORE_MEMORIA
        d = cp_data(p.get("nascita"))
        return cp_colore(cp_segno(d)) if d else "#20e6ff"
    except Exception:
        return "#20e6ff"


def _dr_nome(p):
    return "Il diario di " + " ".join(x for x in (str(p.get("nome") or "").strip(), str(p.get("cognome") or "").strip()) if x)


def _dr_salva_persona(pid, fn, msg):
    def _m(d):
        for x in d.get("compleanni", []):
            if x.get("id") == pid:
                fn(x)
                return
    _cp_salva(_m, msg)


def _dr_comprimi(dati):
    """Foto più leggera possibile senza perdere qualità visibile: lato lungo 1280 px (bastano per lo schermo del telefono anche nitido),
    WEBP; provo qualità alta e scendo solo se serve per stare sotto circa 170 KB (mai sotto 74). Ritorna (byte, rapporto larghezza/altezza)."""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(_dr_io.BytesIO(dati)))
    if im.mode not in ("RGB",):
        im = im.convert("RGB")
    im.thumbnail((1280, 1280), Image.LANCZOS)
    ar = max(0.75, min(1.33, im.width / float(max(1, im.height))))
    migliore = None
    for q in (86, 82, 78, 74):
        b = _dr_io.BytesIO()
        im.save(b, "WEBP", quality=q, method=6)                   # senza metadati (EXIF, GPS): pesa meno
        migliore = b.getvalue()
        if len(migliore) <= 170_000:
            break
    return migliore, round(ar, 3)


def dr_el_html(e):
    t = _dr_html.escape(str(e.get("t") or "")).replace("\n", "<br>")
    if not t:
        return ""
    s = float(e.get("s") or 28)
    fam = DR_FONT.get(e.get("f"), DR_FONT["Classico"]) if e.get("k") == "t" else "inherit"
    return (f"<span class='dr-el' style=\"left:{float(e.get('x', 50)):.1f}%;top:{float(e.get('y', 50)):.1f}%;color:{_dr_html.escape(str(e.get('c') or '#fff'), quote=True)};"
            f"font-size:{s / 4:.2f}cqw;font-family:{fam}\">{t}</span>")


def _dr_tr(z, px, py):
    mx = (z - 1) * 50.0
    return f"translate({(50 - px) / 50 * mx:.2f}%,{(50 - py) / 50 * mx:.2f}%) scale({z:.3f})"


def _dr_foto_bytes(rif):
    """La foto si legge dall'archivio una volta sola per sessione (lo scorrimento automatico non deve richiamarla ogni volta)."""
    ch = "dr_img_" + str(rif.get("id"))
    if ch not in st.session_state:
        st.session_state[ch] = cp_file_leggi(rif)
    return st.session_state.get(ch)


def dr_pagina_html(pg, els, col, extra=None, dati=None, mod=None, musica=False, auto=None, pila=False, effetto=0):
    """La pagina: foto grande come la scheda, bordi stondati, testi e icone sopra. mod=(etichetta, z, px, py): la foto si inquadra con le dita."""
    if dati is None and pg.get("foto"):
        dati = _dr_foto_bytes(pg["foto"])
    try:
        z, px, py = float(pg.get("z") or 1), float(pg.get("px", 50)), float(pg.get("py", 50))
    except Exception:
        z, px, py = 1.0, 50.0, 50.0
    attr = ""
    if mod:
        lab, z, px, py = mod
        attr = f" data-mod='1' data-lab='{_dr_html.escape(lab, quote=True)}'"
    z = max(1.0, min(4.0, float(z)))
    attr += f" data-z='{z:.2f}' data-px='{float(px):.0f}' data-py='{float(py):.0f}'"
    if not dati:
        img = "<div class='dr-vuota'>La foto non c'è più</div>"
    else:
        import base64 as _b64
        mime = (pg.get("foto") or {}).get("mime") or "image/webp"
        img = f"<img class='dr-img' style='transform:{_dr_tr(z, float(px), float(py))}' src='data:{mime};base64,{_b64.b64encode(dati).decode()}' alt=''>"
    sopra = "".join(dr_el_html(e) for e in list(els) + ([extra] if extra else []))
    did = str(pg.get("did") or "").strip()
    ar = float(pg.get("ar") or 1.2)
    vbar = ""
    if musica or auto:
        vbar = ("<div class='dr-vbar'>" + ("<span class='dr-pp'>⏸</span>" if auto else "")
                + ("<span class='dr-mus'>▶</span><div class='dr-vol'><i></i></div>" if musica else "<div class='dr-fill'></div>") + "</div>")
        if auto:
            vbar += f"<div class='dr-prog'><i style='animation-duration:{float(auto['dur']):.1f}s'></i></div>"
    at = f" data-id='{_dr_html.escape(str(pg.get('id') or ''), quote=True)}' data-dur='{float(auto['dur']):.1f}' data-auto='1'" if auto else ""
    return (f"<div class='dr-pag{' dr-pila' if pila else ''}{f' dr-in-{effetto}' if effetto else ''}' style='--c:{col}'{at}><div class='dr-foto' style='aspect-ratio:{ar:.3f}'{attr}><div class='dr-zi'>{img}{sopra}</div></div>"
            + (f"<div class='dr-did'>{_dr_html.escape(did)}</div>" if did else "") + vbar + "</div>")


DR_CSS = """<style>
.cp-card{padding-bottom:70px !important}
[class*="st-key-dr_apri_"]{margin-top:-94px;position:relative;z-index:2;gap:0 !important;display:flex;flex-direction:column;align-items:flex-end;padding-right:22px;height:54px}
[class*="st-key-dr_chiudi_"]{display:flex;flex-direction:column;align-items:center}
[class*="st-key-dr_apri_"] [data-testid="stButton"],[class*="st-key-dr_chiudi_"] [data-testid="stButton"]{width:auto !important;display:flex;justify-content:center}
[class*="st-key-dr_apri_"] button,[class*="st-key-dr_chiudi_"] button{width:54px !important;height:54px !important;min-height:0 !important;padding:0 !important;border-radius:50% !important;position:relative;
 border:3px solid #c9ced6 !important;transition:transform .12s,box-shadow .15s,filter .15s;font-size:0 !important;overflow:visible}
[class*="st-key-dr_apri_"] button p,[class*="st-key-dr_chiudi_"] button p{display:none !important}
[class*="st-key-dr_apri_"] button::before,[class*="st-key-dr_chiudi_"] button::before{content:"";position:absolute;left:50%;top:50%;width:62%;height:62%;transform:translate(-50%,-50%);
 background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 12v36' stroke='white' stroke-width='9' stroke-linecap='round' fill='none'/%3E%3Cpath d='M29 27a36 36 0 1 0 42 0' stroke='white' stroke-width='9' stroke-linecap='round' fill='none'/%3E%3C/svg%3E") center/contain no-repeat;
 filter:drop-shadow(0 0 3px #fff) drop-shadow(0 0 6px rgba(255,255,255,.85))}
[class*="st-key-dr_apri_"] button::after,[class*="st-key-dr_chiudi_"] button::after{content:"";position:absolute;left:14%;top:7%;width:72%;height:42%;border-radius:50%;background:linear-gradient(rgba(255,255,255,.55),rgba(255,255,255,0));pointer-events:none}
[class*="st-key-dr_apri_"] button{background:radial-gradient(circle at 50% 38%,#8bea3d 0,#4cbb17 55%,#2f8f0c 100%) !important;
 box-shadow:0 3px 6px rgba(0,0,0,.45),0 0 8px rgba(110,220,50,.45),inset 0 -5px 8px rgba(0,70,0,.35) !important}
[class*="st-key-dr_chiudi_"] button{background:radial-gradient(circle at 50% 38%,#ff6a6a 0,#e01f26 55%,#a80f16 100%) !important;
 box-shadow:0 3px 6px rgba(0,0,0,.45),0 0 8px rgba(255,70,70,.45),inset 0 -5px 8px rgba(90,0,0,.4) !important}
[class*="st-key-dr_apri_"] button:hover,[class*="st-key-dr_apri_"] button:focus,[class*="st-key-dr_apri_"] button:active{filter:brightness(1.18) saturate(1.2);
 box-shadow:0 0 12px #b6ff6a,0 0 28px #7dff2a,0 0 48px rgba(125,255,42,.8),inset 0 -3px 6px rgba(0,70,0,.2) !important;transform:scale(1.06)}
[class*="st-key-dr_chiudi_"] button:hover,[class*="st-key-dr_chiudi_"] button:focus,[class*="st-key-dr_chiudi_"] button:active{filter:brightness(1.18) saturate(1.2);
 box-shadow:0 0 12px #ff9a9a,0 0 28px #ff3b3b,0 0 48px rgba(255,59,59,.8),inset 0 -3px 6px rgba(90,0,0,.2) !important;transform:scale(1.06)}
[class*="st-key-dr_apri_"] button:active,[class*="st-key-dr_chiudi_"] button:active{transform:scale(.96)}
.dr-leg{text-align:center;font-size:.78rem;font-weight:700;margin:6px 0 0;color:#cfe}
[class*="st-key-dr_apri_"] .dr-leg{position:absolute;right:84px;bottom:18px;margin:0;text-align:right;white-space:nowrap}
.dr-pag{margin:10px 2px;padding:8px;border-radius:24px;border:2px solid var(--c);background:#0b1120;box-shadow:0 0 8px var(--c),0 0 20px var(--c);
 transform-origin:center}
.dr-foto{position:relative;container-type:inline-size;border-radius:18px;overflow:hidden;background:#05080f;line-height:0;touch-action:pan-y;-webkit-user-select:none;user-select:none}
.dr-foto[data-mod],.dr-foto.dr-zoom{touch-action:none}
.dr-foto[data-mod]{outline:2px dashed rgba(255,255,255,.55);outline-offset:-6px;cursor:grab}
.dr-zi{position:absolute;left:0;top:0;right:0;bottom:0;transform-origin:center}
.dr-img{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;transform-origin:center;pointer-events:none;-webkit-user-drag:none}
.dr-vbar{display:flex;align-items:center;gap:8px;padding:9px 4px 0 2px}
.dr-mus{min-width:26px;text-align:center;color:#fff;font-size:16px;line-height:1;cursor:pointer;text-shadow:0 0 6px var(--c)}
.dr-vol{flex:1;height:22px;position:relative;touch-action:none;cursor:pointer;--v:70%}
.dr-vol::before{content:"";position:absolute;left:0;right:0;top:9px;height:4px;border-radius:2px;background:rgba(255,255,255,.22)}
.dr-vol i{position:absolute;left:0;top:9px;height:4px;width:var(--v);border-radius:2px;background:var(--c);box-shadow:0 0 6px var(--c)}
.dr-vol i::after{content:"";position:absolute;right:-7px;top:-5px;width:14px;height:14px;border-radius:50%;background:#fff;box-shadow:0 0 8px var(--c)}
[class*="st-key-nascosti_drg_"],[class*="st-key-nascosti_drjs_"],[class*="st-key-nascosti_dra_"]{display:none !important}
.dr-pp{min-width:26px;text-align:center;color:#fff;font-size:16px;line-height:1;cursor:pointer;text-shadow:0 0 6px var(--c)}
.dr-fill{flex:1}
.dr-prog{height:3px;margin:6px 4px 0;border-radius:2px;background:rgba(255,255,255,.16);overflow:hidden}
.dr-prog i{display:block;height:100%;width:0;background:var(--c);box-shadow:0 0 6px var(--c);animation:dr-prog linear forwards}
.dr-pila{margin-bottom:22px;box-shadow:0 5px 0 -1px #0b1120,0 6px 0 0 var(--c),0 11px 0 -1px #0b1120,0 12px 0 0 var(--c),0 0 8px var(--c),0 0 20px var(--c)}
.dr-diario-t{text-align:center;font-weight:800;font-size:1.05rem;margin:14px 0 2px;color:#fff;text-shadow:0 0 8px var(--c)}
.dr-pausa .dr-prog i{animation-play-state:paused}
@keyframes dr-prog{from{width:0}to{width:100%}}
[class*="st-key-dr_musica_"]{position:absolute;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none}
.dr-vuota{padding:40px 10px;text-align:center;color:#9ab;line-height:1.3}
.dr-el{position:absolute;transform:translate(-50%,-50%);text-align:center;line-height:1.15;white-space:nowrap;font-weight:700;
 text-shadow:0 0 3px rgba(0,0,0,.95),0 1px 4px rgba(0,0,0,.95),0 0 10px rgba(0,0,0,.6)}
.dr-did{padding:8px 6px 2px;text-align:center;font-style:italic;color:#e9eefb;font-size:.92rem;line-height:1.35}
.dr-num{text-align:center;font-size:.8rem;opacity:.8;margin:2px 0}
@keyframes dr-in-1{from{transform:translateX(60%) rotate(6deg);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-1{from{transform:none;filter:none;opacity:1}to{transform:translateX(-70%) rotate(-8deg);opacity:0}}
.dr-pag.dr-in-1{animation:dr-in-1 .65s ease-out both}
.dr-pag.dr-out-1{animation:dr-out-1 .45s ease-in forwards}
@keyframes dr-in-2{from{transform:translateX(-60%) rotate(-6deg);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-2{from{transform:none;filter:none;opacity:1}to{transform:translateX(70%) rotate(8deg);opacity:0}}
.dr-pag.dr-in-2{animation:dr-in-2 .65s ease-out both}
.dr-pag.dr-out-2{animation:dr-out-2 .45s ease-in forwards}
@keyframes dr-in-3{from{transform:scale(.55);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-3{from{transform:none;filter:none;opacity:1}to{transform:scale(.5);opacity:0}}
.dr-pag.dr-in-3{animation:dr-in-3 .65s ease-out both}
.dr-pag.dr-out-3{animation:dr-out-3 .45s ease-in forwards}
@keyframes dr-in-4{from{transform:perspective(900px) rotateY(-75deg);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-4{from{transform:none;filter:none;opacity:1}to{transform:perspective(900px) rotateY(75deg);opacity:0}}
.dr-pag.dr-in-4{animation:dr-in-4 .65s ease-out both}
.dr-pag.dr-out-4{animation:dr-out-4 .45s ease-in forwards}
@keyframes dr-in-5{from{transform:translateY(-45%);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-5{from{transform:none;filter:none;opacity:1}to{transform:translateY(45%);opacity:0}}
.dr-pag.dr-in-5{animation:dr-in-5 .65s ease-out both}
.dr-pag.dr-out-5{animation:dr-out-5 .45s ease-in forwards}
@keyframes dr-in-6{from{transform:rotate(-25deg) scale(.5);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-6{from{transform:none;filter:none;opacity:1}to{transform:rotate(25deg) scale(.4);opacity:0}}
.dr-pag.dr-in-6{animation:dr-in-6 .65s ease-out both}
.dr-pag.dr-out-6{animation:dr-out-6 .45s ease-in forwards}
@keyframes dr-in-7{from{transform:scale(1.1);filter:blur(14px);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-7{from{transform:none;filter:none;opacity:1}to{transform:scale(1.12);filter:blur(14px);opacity:0}}
.dr-pag.dr-in-7{animation:dr-in-7 .65s ease-out both}
.dr-pag.dr-out-7{animation:dr-out-7 .45s ease-in forwards}
@keyframes dr-in-8{from{transform:perspective(900px) rotateX(70deg);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes dr-out-8{from{transform:none;filter:none;opacity:1}to{transform:perspective(900px) rotateX(-70deg);opacity:0}}
.dr-pag.dr-in-8{animation:dr-in-8 .65s ease-out both}
.dr-pag.dr-out-8{animation:dr-out-8 .45s ease-in forwards}
@media (prefers-reduced-motion:reduce){.dr-pag{animation:none !important}}
</style>"""


DR_JS = r"""<script>
(function(){
if(window.__drOK)return;window.__drOK=1;
var vol=0.7;
try{var s0=parseFloat(localStorage.getItem('dr_vol'));if(!isNaN(s0))vol=Math.max(0,Math.min(1,s0));}catch(e){}
function au(){return document.querySelector('[class*="st-key-dr_musica_"] audio');}
function ui(){
 var a=au();
 document.querySelectorAll('.dr-vol').forEach(function(el){el.style.setProperty('--v',(vol*100)+'%');});
 var t=(a&&!a.paused)?(vol===0?'🔇':'🔊'):'▶';
 document.querySelectorAll('.dr-mus').forEach(function(b){if(b.textContent!==t)b.textContent=t;});
 if(a&&Math.abs(a.volume-vol)>0.001)a.volume=vol;
}
document.addEventListener('play',function(e){if(e.target&&e.target.tagName==='AUDIO'){e.target.volume=vol;setTimeout(ui,60);}},true);
document.addEventListener('pause',function(){setTimeout(ui,60);},true);
new MutationObserver(function(){clearTimeout(window.__drT);window.__drT=setTimeout(ui,60);}).observe(document.body,{childList:true,subtree:true});
function setVol(el,x){var r=el.getBoundingClientRect();vol=Math.max(0,Math.min(1,(x-r.left)/Math.max(1,r.width)));
 try{localStorage.setItem('dr_vol',String(vol));}catch(e){}ui();}
function scrivi(lab,v){var el=document.querySelector('input[aria-label="'+lab+'"]');if(!el||el.value===v)return;
 var set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;set.call(el,v);
 el.dispatchEvent(new Event('input',{bubbles:true}));
 el.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
 el.dispatchEvent(new FocusEvent('focusout',{bubbles:true}));}
function S(el){
 var sig=el.dataset.z+'|'+el.dataset.px+'|'+el.dataset.py;
 if(el._s&&el._s.sig===sig)return el._s;
 var z=parseFloat(el.dataset.z)||1,px=parseFloat(el.dataset.px),py=parseFloat(el.dataset.py);
 if(isNaN(px))px=50;if(isNaN(py))py=50;
 var r=el.getBoundingClientRect(),mx=(z-1)*50,mod=!!el.dataset.mod;
 el._s={sig:sig,mod:mod,z:mod?z:1,tx:mod?(50-px)/50*mx/100*r.width:0,ty:mod?(50-py)/50*mx/100*r.height:0,ptr:{},last:0,t:null};
 return el._s;}
function apply(f){
 var s=S(f),r=f.getBoundingClientRect(),lx=(s.z-1)/2*r.width,ly=(s.z-1)/2*r.height;
 s.tx=Math.max(-lx,Math.min(lx,s.tx));s.ty=Math.max(-ly,Math.min(ly,s.ty));
 var t=f.querySelector(s.mod?'.dr-img':'.dr-zi');
 if(t)t.style.transform='translate('+(s.tx/r.width*100)+'%,'+(s.ty/r.height*100)+'%) scale('+s.z+')';
 if(!s.mod)f.classList.toggle('dr-zoom',s.z>1.001);}
function pianifica(f){var s=S(f);clearTimeout(s.t);s.t=setTimeout(function(){
 var r=f.getBoundingClientRect(),mx=(s.z-1)*50,tx=s.tx/r.width*100,ty=s.ty/r.height*100;
 var px=mx>0.01?50-tx/mx*50:50,py=mx>0.01?50-ty/mx*50:50;
 px=Math.max(0,Math.min(100,px));py=Math.max(0,Math.min(100,py));
 scrivi(f.dataset.lab,s.z.toFixed(2)+'|'+Math.round(px)+'|'+Math.round(py));},350);}
var pausa=false,idv=null,t0=0,tp=0,inUscita=false;
function esci(cb){var pg=document.querySelector('.dr-pag');
 if(inUscita)return;
 if(!pg||(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)){cb();return;}
 inUscita=true;var n=1+Math.floor(Math.random()*8);pg.className=pg.className.replace(/dr-in-\d/g,'')+' dr-out-'+n;
 setTimeout(function(){inUscita=false;cb();},460);}
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[class*="st-key-dr_navp"] button');
 if(!b||b.disabled)return;if(b._go){b._go=false;return;}
 e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();esci(function(){b._go=true;b.click();});},true);
function setPausa(v){pausa=v;document.body.classList.toggle('dr-pausa',v);if(v)tp=Date.now();else t0+=Date.now()-tp;
 document.querySelectorAll('.dr-pp').forEach(function(b){b.textContent=v?'\u25B6':'\u23F8';});}
setInterval(function(){
 var pg=document.querySelector('.dr-pag[data-auto]');
 if(!pg){idv=null;return;}
 document.querySelectorAll('.dr-pp').forEach(function(b){var t=pausa?'\u25B6':'\u23F8';if(b.textContent!==t)b.textContent=t;});
 if(pg.dataset.id!==idv){idv=pg.dataset.id;t0=Date.now();if(pausa)tp=Date.now();return;}
 if(pausa||document.querySelector('.dr-foto.dr-zoom'))return;
 var dur=(parseFloat(pg.dataset.dur)||7)*1000;
 if(Date.now()-t0>=dur){var b=document.querySelector('[class*="st-key-nascosti_dra_"] button');if(b){t0=Date.now();esci(function(){b.click();});}}
},400);
var vdrag=null;
document.addEventListener('pointerdown',function(e){
 var tg=e.target;if(!tg||!tg.closest)return;
 var v=tg.closest('.dr-vol');if(v){vdrag=v;setVol(v,e.clientX);e.preventDefault();return;}
 var pp=tg.closest('.dr-pp');if(pp){setPausa(!pausa);return;}
 var m=tg.closest('.dr-mus');if(m){var a=au();if(a){if(a.paused){a.volume=vol;a.play().catch(function(){});}else a.pause();setTimeout(ui,100);}return;}
 var f=tg.closest('.dr-foto');if(!f)return;
 var s=S(f),r=f.getBoundingClientRect();
 s.ptr[e.pointerId]={x:e.clientX-r.left-r.width/2,y:e.clientY-r.top-r.height/2};
 try{f.setPointerCapture(e.pointerId);}catch(x){}
 if(!s.mod){var n=Date.now();if(n-s.last<320&&Object.keys(s.ptr).length===1){s.z=1;s.tx=0;s.ty=0;apply(f);}s.last=n;}
},true);
document.addEventListener('pointermove',function(e){
 if(vdrag){setVol(vdrag,e.clientX);return;}
 var tg=e.target;var f=tg&&tg.closest?tg.closest('.dr-foto'):null;
 if(!f||!f._s||!f._s.ptr[e.pointerId])return;
 var s=f._s,r=f.getBoundingClientRect(),nx=e.clientX-r.left-r.width/2,ny=e.clientY-r.top-r.height/2,ids=Object.keys(s.ptr);
 if(ids.length>=2){
  var a=s.ptr[ids[0]],b=s.ptr[ids[1]],d0=Math.hypot(a.x-b.x,a.y-b.y),m0x=(a.x+b.x)/2,m0y=(a.y+b.y)/2;
  s.ptr[e.pointerId]={x:nx,y:ny};a=s.ptr[ids[0]];b=s.ptr[ids[1]];
  var d1=Math.hypot(a.x-b.x,a.y-b.y),m1x=(a.x+b.x)/2,m1y=(a.y+b.y)/2;
  if(d0>6){var nz=Math.max(1,Math.min(4,s.z*d1/d0)),k=nz/s.z;s.tx=m1x-k*(m0x-s.tx);s.ty=m1y-k*(m0y-s.ty);s.z=nz;}
 }else{
  var o=s.ptr[e.pointerId];s.ptr[e.pointerId]={x:nx,y:ny};
  if(!s.mod&&s.z<=1.001)return;
  s.tx+=nx-o.x;s.ty+=ny-o.y;}
 apply(f);if(s.mod)pianifica(f);
},true);
function fine(e){
 vdrag=null;var tg=e.target;var f=tg&&tg.closest?tg.closest('.dr-foto'):null;
 if(f&&f._s){delete f._s.ptr[e.pointerId];if(f._s.mod)pianifica(f);}}
document.addEventListener('pointerup',fine,true);
document.addEventListener('pointercancel',fine,true);
document.addEventListener('wheel',function(e){
 var f=e.target&&e.target.closest?e.target.closest('.dr-foto[data-mod]'):null;if(!f)return;
 e.preventDefault();var s=S(f);var nz=Math.max(1,Math.min(4,s.z*(e.deltaY<0?1.1:0.91))),k=nz/s.z;s.tx*=k;s.ty*=k;s.z=nz;apply(f);pianifica(f);},{passive:false});
ui();
})();
</script>"""


def _dr_chiudi(pid, k, legenda=True):
    with st.container(key=f"dr_chiudi_{pid}_{k}"):
        if st.button("⏻", key=f"dr_x_{pid}_{k}", help="Chiudi il diario"):
            st.session_state.update({"dr_aperto": None, "dr_mod": None, "dr_pend": None})
            st.rerun()
    if legenda:
        st.markdown("<div class='dr-leg'>Chiudi il diario</div>", unsafe_allow_html=True)


def _dr_gesto(k, z0, px0, py0):
    """Inquadratura: le dita (script) scrivono in un campo nascosto; i cursori sono la riserva. Ritorna (z, px, py)."""
    with st.container(key="nascosti_drg_" + k):
        jv = st.text_input("drg" + k, key=k + "_jv", label_visibility="collapsed")
    st.session_state.setdefault(k + "_z", float(z0))
    st.session_state.setdefault(k + "_px", int(px0))
    st.session_state.setdefault(k + "_py", int(py0))
    if jv and jv != st.session_state.get(k + "_jlast"):
        try:
            zz, pp, qq = jv.split("|")
            st.session_state[k + "_z"] = max(1.0, min(4.0, round(float(zz), 2)))
            st.session_state[k + "_px"] = max(0, min(100, int(float(pp))))
            st.session_state[k + "_py"] = max(0, min(100, int(float(qq))))
            st.session_state[k + "_jlast"] = jv
        except Exception:
            pass
    return k


def _dr_cursori(k):
    with st.expander("🎚️ Se il pizzico non funziona: usa i cursori"):
        z = st.slider("🔍 Ingrandisci", 1.0, 4.0, step=0.05, key=k + "_z")
        px = st.slider("↔️ Sposta a sinistra / a destra", 0, 100, key=k + "_px")
        py = st.slider("↕️ Sposta in alto / in basso", 0, 100, key=k + "_py")
    return z, px, py


def _dr_pulisci(prefisso):
    for s_ in [s for s in st.session_state if str(s).startswith(prefisso)]:
        st.session_state.pop(s_, None)


def _dr_nuove(p, pid):
    """Sceglie le foto: ognuna passa dall'anteprima (inquadratura) prima di diventare una pagina."""
    tipi = ["jpg", "jpeg", "png", "webp"]
    up = (ar_uploader("📷 Scegli le foto ricordo", type=tipi, accept_multiple_files=True, key=f"dr_up_{pid}")
          if "ar_uploader" in globals() else st.file_uploader("📷 Scegli le foto ricordo", type=tipi, accept_multiple_files=True, key=f"dr_up_{pid}"))
    if up and st.button(f"👀 Vedi l'anteprima di {len(up)} foto", type="primary", key=f"dr_addp_{pid}", width="stretch"):
        coda = []
        try:
            with st.spinner("Preparo le foto…"):
                for f in up:
                    b, ar = _dr_comprimi(f.getvalue())
                    coda.append({"i": _dr_uuid.uuid4().hex[:8], "b": b, "ar": ar})
        except Exception as e:
            st.error(f"Non riesco a leggere una foto ({type(e).__name__}). Riprova con un'altra.")
            return
        st.session_state["dr_pend"] = coda
        st.session_state.pop(f"dr_up_{pid}", None)
        st.rerun()


def _dr_pannello_el(kp, els, sel_key, salva_el, togli_el, undo_key=None, ripristina=None):
    """Testi colorati e icone da mettere sopra la foto (colore, carattere, grandezza, posizione). Ritorna (elemento in anteprima o None, id)."""
    sel = st.session_state.get(sel_key)
    cur = next((e for e in els if e["id"] == sel), None)
    st.markdown("**✍️ Testi colorati e 😊 icone sopra la foto**")
    tipo = st.pills("Cosa aggiungo", ["✍️ Testo", "😊 Icona"], default=("😊 Icona" if cur and cur.get("k") == "i" else "✍️ Testo"), key=kp + "_tipo", label_visibility="collapsed") or "✍️ Testo"
    kk = kp + "_" + (sel or "n")
    testo_t = tipo.startswith("✍")
    if testo_t:
        testo = st.text_area("Scrivi il testo", value=(cur or {}).get("t", "") if cur and cur.get("k") == "t" else "", key=kk + "_t", height=80)
        fnt = st.selectbox("Carattere", list(DR_FONT), index=list(DR_FONT).index(cur["f"]) if cur and cur.get("f") in DR_FONT else 0, key=kk + "_f")
        colore = st.color_picker("Colore", value=(cur or {}).get("c", "#ffffff") if cur and cur.get("k") == "t" else "#ffffff", key=kk + "_c")
    else:
        sc = st.pills("Scegli un'icona", DR_ICONE, key=kk + "_ic", label_visibility="collapsed")
        testo = st.text_input("Oppure scrivi un'icona (emoji)", value=sc or ((cur or {}).get("t", "") if cur and cur.get("k") == "i" else ""), key=kk + "_ic2" + (sc or ""))
        fnt, colore = "Classico", "#ffffff"
    gr = st.slider("Grandezza", 12, 80 if testo_t else 140, int((cur or {}).get("s", 28 if testo_t else 40)), key=kk + "_s")
    x = st.slider("Posizione: sinistra ↔ destra", 0, 100, int((cur or {}).get("x", 50)), key=kk + "_x")
    y = st.slider("Posizione: alto ↕ basso", 0, 100, int((cur or {}).get("y", 50)), key=kk + "_y")
    nuovo = {"id": sel if cur else _dr_uuid.uuid4().hex[:8], "k": "t" if testo_t else "i", "t": testo, "c": colore, "s": gr, "x": x, "y": y, "f": fnt}
    b1, b2 = st.columns(2, gap="small")
    def _ricorda():                                          # prima di ogni cambio, si ricorda com'era: tutto si può rimettere a posto
        if undo_key:
            st.session_state[undo_key] = (st.session_state.get(undo_key) or [])[-19:] + [[dict(e) for e in els]]
    if b1.button("💾 " + ("Salva le modifiche" if cur else "Metti sulla foto"), key=kk + "_ok", type="primary", width="stretch", disabled=not testo.strip()):
        _ricorda()
        salva_el(nuovo)
        st.session_state[sel_key] = None
        _dr_pulisci(kp + "_")
        st.rerun()
    if cur and b2.button("Nuovo elemento", key=kk + "_nuovo", width="stretch"):
        st.session_state[sel_key] = None
        st.rerun()
    if els:
        st.markdown("**Già sulla foto**")
        for e in els:
            r1, r2, r3 = st.columns([3, 1, 1], gap="small")
            r1.markdown(("✍️ " if e.get("k") == "t" else "") + _dr_html.escape(str(e.get("t", ""))[:28]))
            if r2.button("✏️", key=f"{kp}_ed_{e['id']}", help="Modifica", width="stretch"):
                st.session_state[sel_key] = e["id"]
                st.rerun()
            if r3.button("🗑️", key=f"{kp}_del_{e['id']}", help="Togli", width="stretch"):
                _ricorda()
                togli_el(e["id"])
                st.rerun()
    pila = st.session_state.get(undo_key) if undo_key else None
    if pila and ripristina:
        st.caption("Niente è definitivo: puoi sempre rimettere le cose come prima.")
        if st.button(f"↩️ Annulla l'ultima modifica ({len(pila)})", key=kp + "_undo", width="stretch"):
            prima = pila[-1]
            st.session_state[undo_key] = pila[:-1]
            ripristina(prima)
            st.session_state[sel_key] = None
            _dr_pulisci(kp + "_")
            st.rerun()
    return (nuovo if testo.strip() else None), nuovo["id"]


def _dr_pend(p, pid, col):
    coda = st.session_state.get("dr_pend") or []
    it = coda[0]
    k = "dr_pn_" + it["i"]
    kls = k + "_els"
    els = st.session_state.setdefault(kls, [])
    st.markdown(f"<div class='dr-num'>👀 Anteprima · foto 1 di {len(coda)}</div>", unsafe_allow_html=True)
    ph = st.container()
    _dr_gesto(k, 1.0, 50, 50)
    st.caption("👆 Pizzica con due dita sulla foto per ingrandire, trascina per spostare. Così la vedrai nel diario.")
    z, px, py = _dr_cursori(k)
    did = st.text_input("Didascalia sotto la foto (facoltativa)", key=k + "_did")
    dur = st.number_input("⏱️ Secondi su questa foto (0 = come nel diario)", 0, 120, 0, key=k + "_dur")

    def _salva_el(n):
        st.session_state[kls] = [e for e in st.session_state[kls] if e["id"] != n["id"]] + [n]

    def _togli_el(eid):
        st.session_state[kls] = [e for e in st.session_state[kls] if e["id"] != eid]
    def _ripr(prima):
        st.session_state[kls] = prima
    nuovo, eid = _dr_pannello_el(k + "p", els, k + "_sel", _salva_el, _togli_el, k + "_undo", _ripr)
    ph.markdown(dr_pagina_html({"ar": it["ar"], "did": did}, [e for e in els if e["id"] != eid], col, nuovo, dati=it["b"], mod=("drg" + k, z, px, py)), unsafe_allow_html=True)
    b1, b2 = st.columns(2, gap="small")
    if b1.button("💾 Salva la pagina", type="primary", key=k + "_ok", width="stretch"):
        try:
            rif = cp_file_salva(it["b"], "ricordo.webp", "image/webp")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare ({type(e).__name__}). Riprova.")
            return
        pagina = {"id": _dr_uuid.uuid4().hex[:10], "foto": rif, "did": did.strip(), "els": list(els), "z": round(float(z), 2), "px": int(px), "py": int(py), "ar": it["ar"], "dur": int(dur)}
        _dr_salva_persona(pid, lambda x: x.setdefault("ricordi", []).append(pagina), "Diario ricordi: nuova pagina")
        st.session_state["dr_pend"] = coda[1:] or None
        st.session_state["dr_pag"] = len(dr_pagine(p))
        _dr_pulisci(k)
        st.rerun()
    if b2.button("Salta questa foto", key=k + "_no", width="stretch"):
        st.session_state["dr_pend"] = coda[1:] or None
        _dr_pulisci(k)
        st.rerun()


def _dr_musica_ui(p, pid):
    m = p.get("musica") if isinstance(p.get("musica"), dict) else None
    with st.expander("🎵 Musica del diario" + (" (c'è)" if m else "")):
        if m:
            st.caption("🎶 " + str(m.get("nome") or "musica") + " — parte quando tocchi il bottone verde.")
            if st.button("🗑️ Togli la musica", key=f"dr_mtogli_{pid}", width="stretch"):
                _dr_salva_persona(pid, lambda x: x.pop("musica", None), "Diario ricordi: tolta la musica")
                cp_file_cancella([m])
                st.session_state.pop("dr_mus_" + str(m.get("id")), None)
                st.rerun()
        f = st.file_uploader("Scegli un file MP3" if not m else "Cambia la musica (file MP3)", type=["mp3", "m4a", "ogg", "wav"], key=f"dr_mp3_{pid}")
        if f is not None and st.button("💾 Salva la musica", type="primary", key=f"dr_msalva_{pid}", width="stretch"):
            dati = f.getvalue()
            nome = getattr(f, "name", "musica.mp3")
            mime = {"mp3": "audio/mpeg", "m4a": "audio/mp4", "ogg": "audio/ogg", "wav": "audio/wav"}.get(nome.rsplit(".", 1)[-1].lower(), "audio/mpeg")
            if len(dati) > 3_500_000:                                  # file pesante: lo rendo più leggero (se c'è ffmpeg)
                try:
                    import shutil
                    import subprocess
                    import tempfile
                    if shutil.which("ffmpeg"):
                        with tempfile.TemporaryDirectory() as tmp:
                            a, b = tmp + "/in." + nome.rsplit(".", 1)[-1], tmp + "/out.mp3"
                            open(a, "wb").write(dati)
                            subprocess.run(["ffmpeg", "-y", "-i", a, "-vn", "-ac", "2", "-b:a", "96k", b], capture_output=True, timeout=120)
                            d2 = open(b, "rb").read()
                            if d2:
                                dati, mime, nome = d2, "audio/mpeg", nome.rsplit(".", 1)[0] + ".mp3"
                except Exception:
                    pass
            if len(dati) > 8_000_000:
                st.error("Il file è troppo pesante (massimo circa 8 MB). Scegli un MP3 più corto o più leggero.")
                return
            try:
                rif = cp_file_salva(dati, nome, mime)
            except Exception as e:
                st.error(f"Non sono riuscito a salvare la musica ({type(e).__name__}). Riprova.")
                return
            vecchia = m
            _dr_salva_persona(pid, lambda x: x.__setitem__("musica", rif), "Diario ricordi: musica")
            if vecchia:
                cp_file_cancella([vecchia])
            st.session_state.pop(f"dr_mp3_{pid}", None)
            st.toast("🎵 Musica salvata")
            st.rerun()


def _dr_editor(p, pid, pg, col):
    k = f"dr_e_{pg['id']}"
    kf = f"dr_f_{pg['id']}"                                  # inquadratura (non si cancella quando salvi un testo)
    els = list(pg.get("els") or [])
    ph = st.container()                                     # anteprima in alto, sopra i campi
    _dr_gesto(kf, pg.get("z") or 1.0, pg.get("px", 50), pg.get("py", 50))
    st.caption("👆 Pizzica con due dita sulla foto per ingrandire, trascina per spostare.")
    z, px, py = _dr_cursori(kf)
    did = st.text_input("Didascalia sotto la foto (facoltativa)", value=pg.get("did", ""), key=k + "_did")
    dur = st.number_input("⏱️ Secondi su questa foto (0 = come nel diario)", 0, 120, int(pg.get("dur") or 0), key=k + "_dur")
    cadr = {"z": round(float(z), 2), "px": int(px), "py": int(py), "dur": int(dur)}

    def _salva_el(n, pgid=pg["id"]):
        def _fn(x_):
            for q in x_.get("ricordi", []):
                if q.get("id") == pgid:
                    q["els"] = [e for e in q.get("els", []) if e.get("id") != n["id"]] + [n]
                    q["did"] = did
                    q.update(cadr)
        _dr_salva_persona(pid, _fn, "Diario ricordi: testo/icona")

    def _togli_el(eid, pgid=pg["id"]):
        _dr_salva_persona(pid, lambda x_: [q.update(els=[z_ for z_ in q.get("els", []) if z_.get("id") != eid]) for q in x_.get("ricordi", []) if q.get("id") == pgid], "Diario ricordi: tolto")
    def _ripr(prima, pgid=pg["id"]):
        _dr_salva_persona(pid, lambda x_: [q.update(els=prima) for q in x_.get("ricordi", []) if q.get("id") == pgid], "Diario ricordi: annullato")
    nuovo, eid = _dr_pannello_el(k + "p", els, "dr_el", _salva_el, _togli_el, "dr_undo_" + pg["id"], _ripr)
    ph.markdown(dr_pagina_html({**pg, "did": did}, [e for e in els if e["id"] != eid], col, nuovo, mod=("drg" + kf, z, px, py)), unsafe_allow_html=True)
    st.markdown("**Cambia la foto**")
    nf = st.file_uploader("Nuova foto per questa pagina", type=["jpg", "jpeg", "png", "webp"], key=k + "_nf")
    c1, c2 = st.columns(2, gap="small")
    if c1.button("✅ Fatto", key=k + "_fatto", width="stretch"):
        def _fn2(x_, pgid=pg["id"]):
            for q in x_.get("ricordi", []):
                if q.get("id") == pgid:
                    q["did"] = did
                    q.update(cadr)
        _dr_salva_persona(pid, _fn2, "Diario ricordi: didascalia")
        if nf is not None:
            try:
                b_, ar_ = _dr_comprimi(nf.getvalue())
                rif = cp_file_salva(b_, "ricordo.webp", "image/webp")
                vecchia = pg.get("foto")
                _dr_salva_persona(pid, lambda x_, pgid=pg["id"], r=rif, a=ar_: [q.update(foto=r, ar=a, z=1.0, px=50, py=50) for q in x_.get("ricordi", []) if q.get("id") == pgid], "Diario ricordi: nuova foto")
                cp_file_cancella([vecchia])
            except Exception as e_:
                st.error(f"Non sono riuscito a cambiare la foto ({type(e_).__name__}).")
                return
        st.session_state.update({"dr_mod": None, "dr_el": None})
        _dr_pulisci(kf)
        st.rerun()
    if c2.button("🗑️ Elimina pagina", key=k + "_elim", width="stretch"):
        st.session_state["dr_conf"] = pg["id"]
        st.rerun()
    if st.session_state.get("dr_conf") == pg["id"]:
        st.warning("Eliminare questa pagina con la sua foto?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=k + "_si", type="primary", width="stretch"):
            _dr_salva_persona(pid, lambda x_, pgid=pg["id"]: x_.__setitem__("ricordi", [q for q in x_.get("ricordi", []) if q.get("id") != pgid]), "Diario ricordi: pagina eliminata")
            cp_file_cancella([pg.get("foto")])
            st.session_state.update({"dr_conf": None, "dr_mod": None, "dr_el": None, "dr_pag": max(0, int(st.session_state.get("dr_pag", 0)) - 1)})
            st.rerun()
        if s2.button("No", key=k + "_no", width="stretch"):
            st.session_state["dr_conf"] = None
            st.rerun()


def _dr_scorrimento_ui(p, pid):
    with st.expander("⏱️ Scorrimento automatico (ogni " + str(int(p.get("durata") or 7)) + " secondi)" if p.get("auto", True) else "⏱️ Scorrimento automatico (spento)"):
        at = st.toggle("Le foto scorrono da sole", value=bool(p.get("auto", True)), key=f"dr_at_{pid}")
        du = st.number_input("Quanti secondi resta ogni foto", 2, 120, int(p.get("durata") or 7), key=f"dr_du_{pid}")
        if st.button("💾 Salva", key=f"dr_ds_{pid}", type="primary", width="stretch"):
            _dr_salva_persona(pid, lambda x: x.update(auto=bool(at), durata=int(du)), "Diario ricordi: scorrimento")
            st.toast("✅ Salvato")
            st.rerun()


def _dr_diario(p, pid, col):
    if st.session_state.get("dr_pend"):
        _dr_pend(p, pid, col)
        return
    pagine = dr_pagine(p)
    if not pagine:
        st.info("Il diario è vuoto. Scegli una o più foto: ognuna sarà una pagina.")
        _dr_nuove(p, pid)
        _dr_musica_ui(p, pid)
        _dr_chiudi(pid, "v")
        return
    i = max(0, min(int(st.session_state.get("dr_pag", 0)), len(pagine) - 1))
    st.session_state["dr_pag"] = i
    pg = pagine[i]
    st.markdown(f"<div class='dr-diario-t' style='--c:{col}'>📖 {_dr_html.escape(_dr_nome(p))}</div><div class='dr-num'>Pagina {i + 1} di {len(pagine)}</div>", unsafe_allow_html=True)
    if st.session_state.get("dr_mod") == pg["id"]:
        _dr_editor(p, pid, pg, col)
        return
    auto = {"dur": float(pg.get("dur") or p.get("durata") or 7)} if (len(pagine) > 1 and p.get("auto", True)) else None
    n1, nm, n2 = st.columns([5, 3, 5], gap="small", vertical_alignment="center")   # in alto: Indietro · bottone rosso · Avanti
    with n1.container(key=f"dr_navp_{pid}"):
        if st.button("◀ Indietro", key=f"dr_prev_{pid}", width="stretch", disabled=i == 0):
            st.session_state["dr_pag"] = i - 1
            st.rerun()
    with nm:
        _dr_chiudi(pid, "p", legenda=False)                    # il rosso: chiude il diario e torna la scheda
    with n2.container(key=f"dr_navp2_{pid}"):
        if st.button("Avanti ▶", key=f"dr_next_{pid}", width="stretch", disabled=i >= len(pagine) - 1):
            st.session_state["dr_pag"] = i + 1
            st.rerun()
    import random as _rnd
    ult = st.session_state.get("dr_fx", 0)
    fx = _rnd.choice([n for n in range(1, 9) if n != ult])         # ogni foto entra con un effetto diverso dall'ultimo
    st.session_state["dr_fx"] = fx
    st.markdown(dr_pagina_html(pg, pg.get("els") or [], col, musica=bool(p.get("musica")), auto=auto, pila=len(pagine) > 1, effetto=fx), unsafe_allow_html=True)
    if auto:
        with st.container(key=f"nascosti_dra_{pid}"):             # lo scorrimento automatico tocca questo bottone: vai alla pagina dopo (dall'ultima, torna alla prima)
            if st.button("auto", key=f"dr_aut_{pid}"):
                st.session_state["dr_pag"] = (i + 1) % len(pagine)
                st.rerun()
    if st.button("✏️ Inquadra, testi e icone", key=f"dr_mod_{pid}", width="stretch"):
        st.session_state["dr_mod"] = pg["id"]
        st.session_state["dr_el"] = None
        st.rerun()
    with st.expander("➕ Aggiungi altre foto al diario"):
        _dr_nuove(p, pid)
    _dr_scorrimento_ui(p, pid)
    _dr_musica_ui(p, pid)


def _dr_installa_js():
    import json as _j
    corpo = DR_JS.strip()
    corpo = corpo[len("<script>"):-len("</script>")]
    cod = ("<!doctype html><html><body><script>(function(){try{var P=window.parent;if(P.__drOK)return;var s=P.document.createElement('script');s.textContent="
           + _j.dumps(corpo).replace("</", "<\\/") + ";P.document.head.appendChild(s);}catch(e){}})();</script></body></html>")
    if "_mostra_editor" in globals():
        _mostra_editor(cod, 1)
    elif hasattr(st, "iframe"):
        st.iframe(cod, height=1)
    else:
        import streamlit.components.v1 as _c
        _c.html(cod, height=1)


def _dr_base(pid):
    st.markdown(DR_CSS, unsafe_allow_html=True)
    with st.container(key="nascosti_drjs_" + pid):             # installa lo script (gesti, volume) nella pagina dell'app
        _dr_installa_js()


def dr_bottone(p):
    """Il bottone verde DENTRO la scheda (subito dopo la scheda, tirato su dentro la cornice)."""
    pid = p["id"]
    _dr_base(pid)
    n = len(dr_pagine(p))
    aperto = st.session_state.get("dr_aperto") == pid
    with st.container(key=f"dr_apri_{pid}"):
        if st.button("⏻", key=f"dr_o_{pid}", help="Apri il diario dei ricordi" if not aperto else "Chiudi il diario"):
            if aperto:
                st.session_state.update({"dr_aperto": None, "dr_pend": None})
            else:
                st.session_state.update({"dr_aperto": pid, "dr_pag": 0, "dr_mod": None, "dr_pend": None})
            st.rerun()
        st.markdown(f"<div class='dr-leg'>📖 Diario dei ricordi{f' ({n})' if n else ''}</div>", unsafe_allow_html=True)


def _dr_musica_player(p):
    m = p.get("musica") if isinstance(p.get("musica"), dict) else None
    if not m or not m.get("id"):
        return
    chiave = "dr_mus_" + str(m["id"])
    if chiave not in st.session_state:
        st.session_state[chiave] = cp_file_leggi(m)
    dati = st.session_state.get(chiave)
    if dati:
        with st.container(key=f"dr_musica_{p['id']}"):          # parte da sola quando tocchi il bottone verde
            st.audio(dati, format=m.get("mime") or "audio/mpeg", loop=True, autoplay=True)
    else:
        st.session_state.pop(chiave, None)
        st.warning("🎵 Non trovo più il file della musica. Apri «🎵 Musica del diario» in fondo e caricalo di nuovo.")


def dr_blocco(p):
    """Se aperto, il diario sotto la scheda (con la musica, se c'è)."""
    if st.session_state.get("dr_aperto") == p["id"]:
        _dr_base(p["id"])
        _dr_musica_player(p)
        _dr_diario(p, p["id"], _dr_colore(p))
