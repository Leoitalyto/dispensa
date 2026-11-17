# -*- coding: utf-8 -*-
"""🎂 Compleanni (dentro Utilità): una scheda-badge per ogni persona.
- L'icona di apertura è il badge nella lingua dell'app (compleanni_img.py).
- Il segno zodiacale si sceglie dalla data di nascita; il nome del segno è scritto dal programma nella lingua.
- Cornice neon a due linee, nel colore del segno. Foto facoltativa.
- Se la persona non c'è più: al posto del segno compaiono le mani con la candela, con la fiamma che vibra come viva.
I dati stanno in d["compleanni"] (lista di schede con id). Caricato da app_dispensa.py dopo utilita.py (serve solo per _ut_chiama)."""
import base64
import calendar
import datetime as _cp_dt
import html as _cp_html
import io
import os as _cp_os
import re as _cp_re
import uuid as _cp_uuid

import streamlit as st

# (chiave, mese e giorno di INIZIO, colore neon)
CP_SEGNI = [
    ("capricorno", (12, 22), "#e0ae4a"), ("acquario", (1, 20), "#34c1ff"), ("pesci", (2, 19), "#2de3d0"),
    ("ariete", (3, 21), "#f5c542"), ("toro", (4, 20), "#4aa8ff"), ("gemelli", (5, 21), "#ff5a5a"),
    ("cancro", (6, 21), "#a883ff"), ("leone", (7, 23), "#ff9a2e"), ("vergine", (8, 23), "#ff7cc8"),
    ("bilancia", (9, 23), "#3ddc84"), ("scorpione", (10, 23), "#ff3d3d"), ("sagittario", (11, 22), "#b862ff"),
]
CP_COLORE_MEMORIA = "#ffb347"
CP_NOMI_SEGNI = {
    "it": ["Ariete", "Toro", "Gemelli", "Cancro", "Leone", "Vergine", "Bilancia", "Scorpione", "Sagittario", "Capricorno", "Acquario", "Pesci"],
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    "fr": ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge", "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"],
    "ar": ["الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء", "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت"],
    "de": ["Widder", "Stier", "Zwillinge", "Krebs", "Löwe", "Jungfrau", "Waage", "Skorpion", "Schütze", "Steinbock", "Wassermann", "Fische"],
    "ro": ["Berbec", "Taur", "Gemeni", "Rac", "Leu", "Fecioară", "Balanță", "Scorpion", "Săgetător", "Capricorn", "Vărsător", "Pești"],
    "pt": ["Áries", "Touro", "Gémeos", "Caranguejo", "Leão", "Virgem", "Balança", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"],
    "es": ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"],
}
CP_ORDINE_SEGNI = ["ariete", "toro", "gemelli", "cancro", "leone", "vergine", "bilancia", "scorpione", "sagittario", "capricorno", "acquario", "pesci"]
CP_MESI = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "ro": ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
}
CP_PREGHIERA = {
    "it": "L'eterno riposo dona a loro, o Signore, e splenda ad essi la luce perpetua. Riposino in pace. Amen.",
    "en": "Eternal rest grant unto them, O Lord, and let perpetual light shine upon them. May they rest in peace. Amen.",
    "fr": "Donne-leur, Seigneur, le repos éternel, et que brille sur eux la lumière sans déclin. Qu'ils reposent en paix. Amen.",
    "ar": "أعطهم يا رب الراحة الأبدية، ولينر لهم النور الدائم. ليرقدوا بسلام. آمين.",
    "de": "Herr, gib ihnen die ewige Ruhe, und das ewige Licht leuchte ihnen. Lass sie ruhen in Frieden. Amen.",
    "ro": "Odihna veșnică dă-le lor, Doamne, și lumina cea fără de sfârșit să le lucească lor. Să se odihnească în pace. Amin.",
    "pt": "Dai-lhes, Senhor, o descanso eterno, e brilhe para eles a luz perpétua. Descansem em paz. Amém.",
    "es": "Dales, Señor, el descanso eterno, y brille para ellos la luz perpetua. Descansen en paz. Amén.",
}
CP_RELAZIONI = ["", "Famiglia", "Amico/a", "Collega", "Vicino/a", "Conoscente", "Altro"]


def _cp_lg():
    lg = st.session_state.get("lang", "it")
    return lg if lg in CP_NOMI_SEGNI else "it"


def _cp_t(frase, **v):
    f = globals().get("t")
    return f(frase, **v) if callable(f) else (frase.format(**v) if v else frase)


def cp_segno(data):
    """Chiave del segno per una data (date)."""
    md = (data.month, data.day)
    scelto = "capricorno"
    for chiave, inizio, _c in sorted(CP_SEGNI, key=lambda x: x[1]):
        if md >= inizio:
            scelto = chiave
    if md < (1, 20):
        scelto = "capricorno"
    return scelto


def cp_colore(chiave):
    for k, _i, c in CP_SEGNI:
        if k == chiave:
            return c
    return "#4aa8ff"


def cp_nome_segno(chiave):
    return CP_NOMI_SEGNI[_cp_lg()][CP_ORDINE_SEGNI.index(chiave)]


def cp_data(testo):
    try:
        return _cp_dt.date.fromisoformat(str(testo)[:10])
    except Exception:
        return None


def cp_prossimo(nascita, oggi):
    """Prossimo compleanno (date). Il 29 febbraio negli anni non bisestili si festeggia il 28."""
    for anno in (oggi.year, oggi.year + 1):
        m, g = nascita.month, nascita.day
        if m == 2 and g == 29 and not calendar.isleap(anno):
            g = 28
        cand = _cp_dt.date(anno, m, g)
        if cand >= oggi:
            return cand
    return oggi


def cp_data_scritta(data, con_anno=True):
    m = CP_MESI[_cp_lg()][data.month - 1]
    return f"{data.day} {m}" + (f" {data.year}" if con_anno else "")


def cp_nuovo_id():
    return _cp_uuid.uuid4().hex[:12]


def cp_img_apri(dati):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    im.thumbnail((1000, 1000), Image.LANCZOS)
    return im


def cp_img_ritaglio(im, zoom, px, py, lato=480):
    """Il quadrato che finisce nel cerchio: zoom (1 = tutta la parte corta), px/py = posizione 0..100 sul resto della foto."""
    from PIL import Image
    w, h = im.size
    sq = min(w, h) / float(zoom)
    sx = int(round(px / 100.0 * (w - sq)))
    sy = int(round(py / 100.0 * (h - sq)))
    sqi = int(round(sq))
    base = Image.new("RGB", (max(sqi, 1), max(sqi, 1)), (15, 23, 42))
    base.paste(im.crop((max(sx, 0), max(sy, 0), min(sx + sqi, w), min(sy + sqi, h))), (max(-sx, 0), max(-sy, 0)))
    return base.resize((lato, lato), Image.LANCZOS)


def cp_img_uri(im, qualita=82):
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=qualita, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def cp_img_bytes(im, qualita=78):
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=qualita, method=6)
    return buf.getvalue()


def cp_file_salva(dati, nome, mime):
    """Mette un file (foto originale, messaggio vocale) nell'archivio dei documenti: nella scheda resta solo il riferimento."""
    fid = _cp_uuid.uuid4().hex[:12]
    corpo = {"nome": nome, "mime": mime, "b64": base64.b64encode(dati).decode()}
    salva_file(_fa_percorso_doc(fid), lambda d, c=corpo: d.update(c), "Compleanni: file")
    return {"id": fid, "nome": nome, "mime": mime}


def cp_file_leggi(rif):
    try:
        d = carica_dati(crea_archivio(), _fa_percorso_doc(rif["id"]))
        return base64.b64decode(d["b64"]) if d and d.get("b64") else None
    except Exception:
        return None


def cp_file_cancella(rifs):
    ids = [r.get("id") for r in rifs if isinstance(r, dict) and r.get("id")]
    if ids:
        try:
            _fa_cancella_files(ids)
        except Exception:
            pass


def cp_audio_comprimi(dati, nome="voce.wav"):
    """Rende il messaggio vocale piccolo (voce, ~24 kbps). Ritorna (byte, mime, nome) oppure None se non si riesce."""
    import shutil
    import subprocess
    import tempfile
    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as tmp:
            src = tmp + "/in." + (nome.rsplit(".", 1)[-1][:5] if "." in nome else "wav")
            open(src, "wb").write(dati)
            for est, mime, args in (("ogg", "audio/ogg", ["-c:a", "libopus", "-b:a", "24k"]), ("mp3", "audio/mpeg", ["-c:a", "libmp3lame", "-b:a", "48k"])):
                out = f"{tmp}/out.{est}"
                try:
                    r = subprocess.run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "24000", *args, out], capture_output=True, timeout=120)
                    if r.returncode == 0 and _cp_os.path.getsize(out) > 0:
                        return open(out, "rb").read(), mime, f"messaggio.{est}"
                except Exception:
                    pass
    try:                                                    # senza ffmpeg: WAV a 16 kHz mono (più piccolo)
        import wave
        import numpy as np
        with wave.open(io.BytesIO(dati)) as w:
            ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            if sw != 2 or n / float(sr) > 150:
                raise ValueError("non adatto")
            x = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, ch).mean(axis=1)
        nuovo = np.interp(np.linspace(0, len(x) - 1, int(len(x) * 16000.0 / sr)), np.arange(len(x)), x).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as o:
            o.setnchannels(1)
            o.setsampwidth(2)
            o.setframerate(16000)
            o.writeframes(nuovo.tobytes())
        return buf.getvalue(), "audio/wav", "messaggio.wav"
    except Exception:
        pass
    if len(dati) <= 3_500_000:
        est = nome.rsplit(".", 1)[-1].lower() if "." in nome else "wav"
        return dati, {"mp3": "audio/mpeg", "m4a": "audio/mp4", "ogg": "audio/ogg", "wav": "audio/wav"}.get(est, "audio/mpeg"), nome
    return None


CP_EDITOR_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;background:transparent;font-family:system-ui,-apple-system,sans-serif;color:#dfe8ff;-webkit-user-select:none;user-select:none}
#cp{width:min(86vw,260px);aspect-ratio:1/1;margin:8px auto 4px;border-radius:50%;border:3px solid #4aa8ff;box-shadow:0 0 16px rgba(74,168,255,.8);position:relative;overflow:hidden;background:#0f172a;touch-action:none;cursor:grab}
#im{position:absolute;left:0;top:0;transform-origin:0 0;max-width:none;pointer-events:none;-webkit-user-drag:none}
#gu{position:absolute;left:25%;top:12%;width:50%;height:66%;border:2px dashed rgba(255,255,255,.7);border-radius:50%;pointer-events:none;box-shadow:0 0 0 1px rgba(0,0,0,.35)}
#nota{text-align:center;font-size:13px;line-height:1.35;margin:4px 8px 6px;opacity:.92}
.bt{display:flex;gap:8px;justify-content:center;margin-bottom:4px}.bt button{font-size:20px;min-width:52px;height:42px;border-radius:12px;border:1px solid #4aa8ff;background:#14213d;color:#dfe8ff}
#st{text-align:center;font-size:12px;opacity:.75;min-height:16px}</style></head><body>
<div id="cp"><img id="im" alt=""><div id="gu"></div></div>
<div id="nota">__NOTA__</div>
<div class="bt"><button id="mn" type="button">&minus;</button><button id="rs" type="button">&#8634;</button><button id="pu" type="button">+</button></div>
<div id="st"></div>
<script>
(function(){
var ETICHETTA=__LABEL__, SRC=__IMG__, Z0=__Z__, PX0=__PX__, PY0=__PY__, ZMIN=0.7, ZMAX=4;
var cp=document.getElementById('cp'), im=document.getElementById('im'), st=document.getElementById('st');
var W=0,H=0,V=0,z=Z0,sx=0,sy=0,timer=null,ptr={},ultimo=null;
function parentWin(){var w=window;for(var i=0;i<4;i++){try{if(w.document.querySelector('[data-testid="stApp"],.stApp'))return w;}catch(e){}if(w.parent===w)break;w=w.parent;}return null;}
function campo(){var P=parentWin();return P?P.document.querySelector('input[aria-label="'+ETICHETTA+'"]'):null;}
function scrivi(v){var P=parentWin(),el=campo();if(!P||!el||el.value===v)return false;
 var set=Object.getOwnPropertyDescriptor(P.HTMLInputElement.prototype,'value').set;set.call(el,v);
 el.dispatchEvent(new P.Event('input',{bubbles:true}));
 el.dispatchEvent(new P.KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
 el.dispatchEvent(new P.FocusEvent('focusout',{bubbles:true}));return true;}
function sq(){return Math.min(W,H)/z;}
function lim(a,b){var lo=Math.min(0,b),hi=Math.max(0,b);return Math.max(lo,Math.min(hi,a));}
function clampPos(){var q=sq();sx=lim(sx,W-q);sy=lim(sy,H-q);}
function disegna(){var q=sq(),sc=V/q;im.style.width=(W*sc)+'px';im.style.height=(H*sc)+'px';im.style.transform='translate('+(-sx*sc)+'px,'+(-sy*sc)+'px)';}
function perc(pos,dim){var q=sq(),r=dim-q;return Math.abs(r)<0.5?50:Math.max(0,Math.min(100,pos/r*100));}
function valore(){return z.toFixed(2)+'|'+Math.round(perc(sx,W))+'|'+Math.round(perc(sy,H));}
function pianifica(){clearTimeout(timer);timer=setTimeout(function(){var v=valore();if(v===ultimo)return;ultimo=v;
 if(scrivi(v))st.textContent='\u2713 '+__OK__;else st.textContent='';},350);}
function zoomA(nz,mx,my){nz=Math.max(ZMIN,Math.min(ZMAX,nz));var q=sq(),sc=V/q,ix=sx+mx/sc,iy=sy+my/sc;z=nz;q=sq();sc=V/q;sx=ix-mx/sc;sy=iy-my/sc;clampPos();disegna();pianifica();}
function iniz(){V=cp.clientWidth;W=im.naturalWidth;H=im.naturalHeight;var q=sq();sx=PX0/100*(W-q);sy=PY0/100*(H-q);disegna();}
im.onload=iniz;im.src=SRC;window.addEventListener('resize',function(){V=cp.clientWidth;disegna();});
function pts(){return Object.keys(ptr).map(function(k){return ptr[k];});}
cp.addEventListener('pointerdown',function(e){cp.setPointerCapture(e.pointerId);var r=cp.getBoundingClientRect();ptr[e.pointerId]={x:e.clientX-r.left,y:e.clientY-r.top};cp.style.cursor='grabbing';});
cp.addEventListener('pointermove',function(e){if(!ptr[e.pointerId])return;var r=cp.getBoundingClientRect(),nx=e.clientX-r.left,ny=e.clientY-r.top,P=pts();
 if(P.length>=2){var a=P[0],b=P[1],d0=Math.hypot(a.x-b.x,a.y-b.y),mx0=(a.x+b.x)/2,my0=(a.y+b.y)/2;ptr[e.pointerId]={x:nx,y:ny};P=pts();a=P[0];b=P[1];
  var d1=Math.hypot(a.x-b.x,a.y-b.y),mx=(a.x+b.x)/2,my=(a.y+b.y)/2;if(d0>8){zoomA(z*d1/d0,mx,my);var sc=V/sq();sx-=(mx-mx0)/sc;sy-=(my-my0)/sc;clampPos();disegna();pianifica();}}
 else{var o=ptr[e.pointerId],sc2=V/sq();sx-=(nx-o.x)/sc2;sy-=(ny-o.y)/sc2;ptr[e.pointerId]={x:nx,y:ny};clampPos();disegna();pianifica();}});
function fine(e){delete ptr[e.pointerId];if(!pts().length)cp.style.cursor='grab';pianifica();}
cp.addEventListener('pointerup',fine);cp.addEventListener('pointercancel',fine);
cp.addEventListener('wheel',function(e){e.preventDefault();var r=cp.getBoundingClientRect();zoomA(z*(e.deltaY<0?1.1:0.91),e.clientX-r.left,e.clientY-r.top);},{passive:false});
document.getElementById('pu').onclick=function(){zoomA(z*1.15,V/2,V/2);};
document.getElementById('mn').onclick=function(){zoomA(z/1.15,V/2,V/2);};
document.getElementById('rs').onclick=function(){z=1;var q=sq();sx=0.5*(W-q);sy=(H>W?0.3:0.5)*(H-q);clampPos();disegna();pianifica();};
window.__cp_stato=function(){return valore();};
})();
</script></body></html>"""


def cp_editor_html(uri, etichetta, z, px, py):
    import json as _j
    return (CP_EDITOR_HTML.replace("__IMG__", _j.dumps(uri)).replace("__LABEL__", _j.dumps(etichetta))
            .replace("__Z__", str(float(z))).replace("__PX__", str(float(px))).replace("__PY__", str(float(py)))
            .replace("__NOTA__", _cp_html.escape(_cp_t("Pizzica con due dita per ingrandire · trascina per spostare: il viso va dentro l'ovale tratteggiato")))
            .replace("__OK__", _j.dumps(_cp_t("Posizione registrata"))))


def cp_rgba(hex_, a):
    h = hex_.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def cp_telegram_url(v):
    v = str(v or "").strip()
    if not v:
        return ""
    if v.lower().startswith(("http://", "https://", "t.me/")):
        return v if v.lower().startswith("http") else "https://" + v
    if v.startswith("@"):
        return "https://t.me/" + v[1:]
    cifre = _cp_re.sub(r"[^\d+]", "", v)
    if cifre and len(cifre.lstrip("+")) >= 6 and not _cp_re.search(r"[A-Za-z_]", v):
        return "https://t.me/" + (cifre if cifre.startswith("+") else "+" + cifre)
    return "https://t.me/" + v


def cp_whatsapp_url(v):
    c = cc_cifre(v) if "cc_cifre" in globals() else _cp_re.sub(r"[^\d+]", "", str(v or ""))
    c = c.lstrip("+")
    return f"https://wa.me/{c}" if len(c) >= 6 else ""


CP_CSS = """<style>
.cp-card{position:relative;margin:14px 2px 6px;padding:14px 12px 12px;border-radius:20px;color:#e9eefb;
 background:radial-gradient(120% 90% at 50% 0%,#16213a 0%,#0b1120 70%);border:2px solid var(--c);
 box-shadow:0 0 6px var(--cg),0 0 18px var(--cg),inset 0 0 12px var(--cg)}
.cp-card:before{content:"";position:absolute;inset:5px;border-radius:15px;border:1px solid var(--c);opacity:.8;pointer-events:none;
 box-shadow:0 0 6px var(--cg)}
.cp-testa{display:flex;gap:10px;align-items:center}
.cp-foto{flex:0 0 92px;width:92px;height:92px;border-radius:50%;border:2px solid var(--c);box-shadow:0 0 10px var(--cg);
 background:#0f172a center/cover no-repeat;display:flex;align-items:center;justify-content:center;font-size:1.7rem;font-weight:800;color:var(--c)}
.cp-nome{flex:1;min-width:0}.cp-nome b{display:block;font-size:1.12rem;line-height:1.2;color:#fff;word-break:break-word}
.cp-nome i{font-style:normal;font-size:.8rem;opacity:.75;display:block}
.cp-nome .cp-chip{display:inline-block;margin-top:5px;padding:2px 9px;border-radius:999px;border:1px solid var(--c);color:var(--c);font-size:.78rem;font-weight:700;background:var(--cg2);white-space:nowrap}
.cp-segno{margin:8px auto 0;text-align:center}.cp-segno img{width:150px;max-width:62%;height:auto;max-height:130px;object-fit:contain;filter:drop-shadow(0 0 8px var(--cg))}
.cp-segno span{display:block;font-size:.72rem;letter-spacing:.04em;color:var(--c);font-weight:700;margin-top:1px}
.cp-righe{margin-top:10px;display:grid;gap:3px;font-size:.88rem}
.cp-righe div{display:flex;gap:7px;line-height:1.3;word-break:break-word}.cp-righe div>span:first-child{flex:0 0 1.4em}
.cp-righe a{color:var(--c)}
.cp-sez{margin-top:8px;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--c);opacity:.85;border-top:1px dashed var(--cg);padding-top:6px}
/* la fiaccola: mani con la candela e la fiamma viva */
.cp-fiacc{position:relative;width:190px;max-width:70%;margin:8px auto 0}
.cp-fiacc img.cp-base{width:100%;display:block;filter:drop-shadow(0 0 10px rgba(255,170,60,.55))}
.cp-alone{position:absolute;left:37%;top:-4%;width:26%;aspect-ratio:1/1;border-radius:50%;pointer-events:none;
 background:radial-gradient(circle,rgba(255,200,90,.85) 0%,rgba(255,150,40,.35) 40%,rgba(255,120,20,0) 70%);mix-blend-mode:screen;animation:cp-alone 2.3s ease-in-out infinite}
.cp-fiamma{position:absolute;left:45.5%;top:13.9%;width:10.1%;height:26.2%;pointer-events:none;mix-blend-mode:screen;
 transform-origin:50% 100%;animation:cp-fiamma 1.35s ease-in-out infinite}
@keyframes cp-fiamma{0%{transform:scale(1,1) skewX(0);opacity:.95}12%{transform:scale(.93,1.07) skewX(-4deg);opacity:1}
 27%{transform:scale(1.06,.94) skewX(3deg);opacity:.85}41%{transform:scale(.96,1.1) skewX(-2deg);opacity:1}
 58%{transform:scale(1.04,.97) skewX(4deg);opacity:.9}73%{transform:scale(.95,1.06) skewX(-3deg);opacity:1}
 88%{transform:scale(1.02,.98) skewX(2deg);opacity:.88}100%{transform:scale(1,1) skewX(0);opacity:.95}}
@keyframes cp-alone{0%,100%{opacity:.55;transform:scale(.92)}20%{opacity:.95;transform:scale(1.08)}45%{opacity:.7;transform:scale(.97)}
 70%{opacity:1;transform:scale(1.12)}85%{opacity:.65;transform:scale(1)}}
[class*="st-key-cp_azioni_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.4rem !important}
[class*="st-key-cp_azioni_"] [data-testid="stColumn"]{min-width:0 !important;flex:1 1 0 !important;width:auto !important}
[class*="st-key-cp_azioni_"] a,[class*="st-key-cp_azioni_"] button{font-size:.8rem !important;padding:.25rem .3rem !important;min-height:2.3rem !important}
[class*="st-key-cp_data_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.4rem !important}
[class*="st-key-cp_data_"] [data-testid="stColumn"]{min-width:0 !important}
/* ogni segno si muove secondo il suo significato (piano, in tono con l'app) */
.cp-segno img{transform-origin:50% 60%;will-change:transform}
.cp-an-ariete img{animation:cp-ariete 4.6s ease-in-out infinite}
.cp-an-toro img{animation:cp-toro 5s ease-in-out infinite}
.cp-an-gemelli img{animation:cp-gemelli 5.2s ease-in-out infinite alternate}
.cp-an-cancro img{animation:cp-cancro 6s ease-in-out infinite}
.cp-an-leone img{animation:cp-leone 4.2s ease-in-out infinite}
.cp-an-vergine img{animation:cp-vergine 5.5s ease-in-out infinite}
.cp-an-bilancia img{transform-origin:50% 22%;animation:cp-bilancia 3.8s ease-in-out infinite alternate}
.cp-an-scorpione img{transform-origin:78% 88%;animation:cp-scorpione 4.4s ease-in-out infinite}
.cp-an-sagittario img{animation:cp-sagittario 4.8s ease-in-out infinite}
.cp-an-capricorno img{animation:cp-capricorno 6s ease-in-out infinite}
.cp-an-acquario img{animation:cp-acquario 4s ease-in-out infinite alternate}
.cp-an-pesci img{animation:cp-pesci 4.4s ease-in-out infinite alternate}
@keyframes cp-ariete{0%,62%,100%{transform:translateX(0) rotate(0)}72%{transform:translateX(-4px) rotate(-2.5deg)}82%{transform:translateX(9px) rotate(3deg) scale(1.04)}90%{transform:translateX(0) rotate(0)}}
@keyframes cp-toro{0%,55%,100%{transform:translateY(0) rotate(0)}62%{transform:translateY(4px) rotate(-1.8deg)}69%{transform:translateY(-1px)}76%{transform:translateY(4px) rotate(1.8deg)}84%{transform:translateY(0)}}
@keyframes cp-gemelli{0%{transform:translateX(-3px) rotate(-1.6deg)}100%{transform:translateX(3px) rotate(1.6deg)}}
@keyframes cp-cancro{0%,100%{transform:translateX(0) rotate(0)}12%,30%{transform:translateX(-7px) rotate(-1.5deg)}42%{transform:translateX(0)}54%,72%{transform:translateX(7px) rotate(1.5deg)}84%{transform:translateX(0)}}
@keyframes cp-leone{0%,100%{transform:scale(1);filter:drop-shadow(0 0 8px var(--cg)) brightness(1)}50%{transform:scale(1.05);filter:drop-shadow(0 0 16px var(--c)) brightness(1.14)}}
@keyframes cp-vergine{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-6px) rotate(1.2deg)}}
@keyframes cp-bilancia{0%{transform:rotate(-3.6deg)}100%{transform:rotate(3.6deg)}}
@keyframes cp-scorpione{0%,66%,100%{transform:rotate(0)}72%{transform:rotate(-5deg)}79%{transform:rotate(4deg) scale(1.02)}86%{transform:rotate(-1deg)}}
@keyframes cp-sagittario{0%,50%,100%{transform:translateX(0) scale(1)}68%{transform:translateX(-5px) scale(.97)}74%{transform:translateX(-5px) scale(.97)}80%{transform:translateX(9px) scale(1.03)}90%{transform:translateX(0) scale(1)}}
@keyframes cp-capricorno{0%,100%{transform:translate(0,0) rotate(0)}20%{transform:translate(2px,-4px) rotate(-1.5deg)}40%{transform:translate(4px,-3px) rotate(0)}60%{transform:translate(5px,-8px) rotate(-1.5deg)}80%{transform:translate(2px,-3px) rotate(0)}}
@keyframes cp-acquario{0%{transform:skewX(-2.5deg) translateY(0);filter:drop-shadow(0 0 8px var(--cg)) hue-rotate(0)}100%{transform:skewX(2.5deg) translateY(-4px);filter:drop-shadow(0 0 14px var(--c)) hue-rotate(-14deg)}}
@keyframes cp-pesci{0%{transform:translate(-5px,3px) rotate(-2.5deg)}100%{transform:translate(5px,-3px) rotate(2.5deg)}}
.cp-pregh{margin:10px 4px 0;text-align:center;font-style:italic;font-size:.86rem;line-height:1.45;color:#ffe2b0;opacity:.95}
.cp-pregh:before{content:"🕊️";display:block;font-style:normal;font-size:1.1rem;margin-bottom:2px}
.cp-pens{margin-top:10px;padding:9px 10px;border-radius:12px;border:1px solid var(--cg);background:var(--cg2);font-size:.9rem;line-height:1.45;white-space:pre-wrap;word-break:break-word}
.cp-pens b{display:block;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--c);margin-bottom:3px}
[class*="st-key-nascosti_cpv_"]{display:none !important}
.cp-anteprima{width:min(46vw,170px);aspect-ratio:1/1;margin:6px auto 4px;border-radius:50%;border:3px solid #4aa8ff;box-shadow:0 0 14px rgba(74,168,255,.7);
 background:#0f172a center/cover no-repeat;position:relative}
.cp-anteprima:after{content:"";position:absolute;left:25%;top:14%;width:50%;height:62%;border:2px dashed rgba(255,255,255,.55);border-radius:50%}
.cp-guida-foto{font-size:.84rem;line-height:1.45;padding:8px 10px;border-radius:10px;background:rgba(74,168,255,.12);border:1px solid rgba(74,168,255,.4);margin-bottom:6px}
@media (prefers-reduced-motion:reduce){.cp-segno img{animation:none !important}.cp-fiamma,.cp-alone{animation:none}}
</style>"""


def _cp_scheda_html(p, oggi):
    nascita = cp_data(p.get("nascita"))
    scomparso = bool(p.get("scomparso"))
    seg = cp_segno(nascita) if nascita else "ariete"
    col = CP_COLORE_MEMORIA if scomparso else cp_colore(seg)
    e = _cp_html.escape
    nome = (str(p.get("nome", "")) + " " + str(p.get("cognome", ""))).strip() or "—"
    senza_anno = bool(p.get("anno_ignoto"))
    chip, sotto = "", ""
    if nascita:
        pross = cp_prossimo(nascita, oggi)
        giorni = (pross - oggi).days
        eta = pross.year - nascita.year
        if giorni == 0:
            chip = _cp_t("🎉 Oggi!") if not scomparso else _cp_t("🕯️ Oggi")
        elif giorni == 1:
            chip = _cp_t("Domani")
        else:
            chip = _cp_t("tra {n} giorni", n=giorni)
        if scomparso:
            sotto = cp_data_scritta(nascita, not senza_anno) + (" · † " + cp_data_scritta(cp_data(p["data_scomparsa"])) if cp_data(p.get("data_scomparsa")) else " · †")
            if not senza_anno:
                chip += " · " + _cp_t("{n} anni", n=eta)
        else:
            sotto = cp_data_scritta(nascita, not senza_anno)
            if not senza_anno:
                chip += " · " + _cp_t("{n} anni", n=eta)
    soprannome = f"<i>«{e(str(p.get('soprannome')))}»</i>" if p.get("soprannome") else ""
    relaz = f"<i>{e(_cp_t(p['relazione']))}</i>" if p.get("relazione") else ""
    # foto o iniziale
    if p.get("foto"):
        foto = f"<div class='cp-foto' style=\"background-image:url('{e(p['foto'], quote=True)}')\"></div>"
    else:
        ini = (str(p.get("nome", "?"))[:1] + str(p.get("cognome", ""))[:1]).upper() or "?"
        foto = f"<div class='cp-foto'>{e(ini)}</div>"
    # a destra: segno oppure fiaccola
    if scomparso:
        destra = ("<div class='cp-fiacc'><img class='cp-base' alt='' src='data:image/webp;base64," + CPI_FIACCOLA + "'>"
                  "<div class='cp-alone'></div><img class='cp-fiamma' alt='' src='data:image/webp;base64," + CPI_FIAMMA + "'></div>")
    else:
        if "sa_segno_html" in globals():
            destra = sa_segno_html(seg, CPI_ZODIACO[seg], cp_nome_segno(seg))        # segni con i pezzi che si muovono (segni_animati.py)
        else:
            destra = ("<div class='cp-segno cp-an-" + seg + "'><img alt='" + e(cp_nome_segno(seg)) + "' src='data:image/webp;base64," + CPI_ZODIACO[seg] + "'>"
                      "<span>" + e(cp_nome_segno(seg)) + "</span></div>")
    if scomparso:
        if p.get("preghiera", True):
            destra += "<div class='cp-pregh'>" + e(CP_PREGHIERA[_cp_lg()]) + "</div>"
        pens = str(p.get("pensiero") or "").strip()
        if pens:
            blocco = f"<b>✍️ {e(_cp_t('Un pensiero'))}</b>{e(pens)}"
            if len(pens) > 500:
                blocco = f"<details><summary style='cursor:pointer;color:var(--c);font-weight:700'>✍️ {e(_cp_t('Leggi il pensiero'))}</summary>{e(pens)}</details>"
            destra += f"<div class='cp-pens'>{blocco}</div>"
    righe = []

    def riga(ic, testo, link=""):
        if testo:
            righe.append(f"<div><span>{ic}</span><span>" + (f"<a href='{e(link, quote=True)}' target='_blank' rel='noopener'>{e(testo)}</a>" if link else e(testo)) + "</span></div>")
    if p.get("luogo"):
        righe.append(f"<div class='cp-sez' style='grid-column:1'>{e(_cp_t('Nascita'))}</div>")
        riga("📍", _cp_t("Nato/a a {luogo}", luogo=p["luogo"]))
    contatti = []
    for ic, chiave, fn in (("📱", "cellulare", lambda v: "tel:" + _cp_re.sub(r"[^\d+]", "", v)), ("☎️", "fisso", lambda v: "tel:" + _cp_re.sub(r"[^\d+]", "", v)),
                           ("🟢", "whatsapp", cp_whatsapp_url), ("✈️", "telegram", cp_telegram_url), ("✉️", "email", lambda v: "mailto:" + v)):
        v = str(p.get(chiave) or "").strip()
        if v:
            contatti.append((ic, v, fn(v) if fn(v) != "tel:" else ""))
    if contatti:
        righe.append(f"<div class='cp-sez'>{e(_cp_t('Contatti'))}</div>")
        for ic, v, link in contatti:
            riga(ic, v, link)
    if p.get("indirizzo") or p.get("sito"):
        righe.append(f"<div class='cp-sez'>{e(_cp_t('Dove'))}</div>")
        riga("🏠", p.get("indirizzo", ""))
        if p.get("sito") and cc_url(p["sito"]):
            riga("🌐", str(p["sito"]).strip(), cc_url(p["sito"]))
    if p.get("regalo") or p.get("note"):
        righe.append(f"<div class='cp-sez'>{e(_cp_t('Da ricordare'))}</div>")
        riga("🎁", p.get("regalo", ""))
        riga("📝", p.get("note", ""))
    return (f"<div class='cp-card' style='--c:{col};--cg:{cp_rgba(col, .45)};--cg2:{cp_rgba(col, .14)}'>"
            f"<div class='cp-testa'>{foto}<div class='cp-nome'><b>{e(nome)}</b>{soprannome}{relaz}"
            f"<i>{e(sotto)}</i>" + (f"<span class='cp-chip'>{e(chip)}</span>" if chip else "") + f"</div></div>{destra}"
            f"<div class='cp-righe'>{''.join(righe)}</div></div>")


def cp_campo_data(k, etichetta, attuale=None):
    """Data a tre menu (giorno, mese, anno): sul telefono è più comoda di una data da digitare. Ritorna date oppure None."""
    st.markdown(f"<div style='font-weight:600;margin:2px 0 -4px'>{_cp_html.escape(etichetta)}</div>", unsafe_allow_html=True)
    riga = st.container(key="cp_data_" + k)
    c1, c2, c3 = riga.columns([1.05, 1.75, 1.45], gap="small")
    giorni = list(range(1, 32))
    mesi = CP_MESI[_cp_lg()]
    anni = list(range(_cp_dt.date.today().year, 1899, -1))
    g = c1.selectbox(_cp_t("Giorno"), giorni, index=giorni.index(attuale.day) if attuale else None, placeholder="—", key=k + "_g", label_visibility="collapsed")
    m = c2.selectbox(_cp_t("Mese"), list(range(1, 13)), index=attuale.month - 1 if attuale else None, placeholder=_cp_t("Mese"),
                     format_func=lambda x: mesi[x - 1], key=k + "_m", label_visibility="collapsed")
    a = c3.selectbox(_cp_t("Anno"), anni, index=anni.index(attuale.year) if attuale and attuale.year in anni else None, placeholder=_cp_t("Anno"), key=k + "_a", label_visibility="collapsed")
    if g and m and a:
        try:
            return _cp_dt.date(a, m, g)
        except ValueError:
            st.caption("⚠️ " + _cp_t("Questa data non esiste: controlla giorno e mese."))
    return None


def _cp_dati():
    return carica_dati(crea_archivio(), st.session_state["percorso"])


def _cp_salva(fn, msg):
    salva(fn, msg)


def _cp_pulsanti(p, k):
    pul = []
    n_f, n_c = str(p.get("fisso") or ""), str(p.get("cellulare") or "")
    if cc_numeri(n_f, n_c):
        pul.append(("📞 " + _cp_t("Chiama"), ("__chiama__", n_f, n_c, str(p.get("nome", "")))))
    if cp_whatsapp_url(p.get("whatsapp") or n_c):
        pul.append(("🟢 WhatsApp", cp_whatsapp_url(p.get("whatsapp") or n_c)))
    if cp_telegram_url(p.get("telegram")):
        pul.append(("✈️ Telegram", cp_telegram_url(p.get("telegram"))))
    if str(p.get("email") or "").strip():
        pul.append(("✉️ Email", "mailto:" + str(p["email"]).strip()))
    if cc_url(p.get("sito")):
        pul.append(("🌐 " + _cp_t("Sito"), cc_url(p["sito"])))
    if pul:
        with st.container(key="cp_azioni_" + k):
            cc_pulsanti(pul, "cp_pul_" + k, per_riga=3)


def _cp_modulo(pid):
    """Il modulo di una persona (pid = id oppure '' per una nuova)."""
    lista = _cp_dati().get("compleanni", [])
    p = next((x for x in lista if x.get("id") == pid), {}) if pid else {}
    k = "cpf_" + (pid or "nuovo")
    with st.container(border=True, key=k + "_box"):
        st.markdown("**" + ("✏️ " + _cp_t("Modifica") if pid else "➕ " + _cp_t("Nuova persona")) + "**")
        # 1) foto: scelta, poi si centra il viso nel cerchio con l'anteprima
        st.markdown("<div class='cp-guida-foto'><b>📷 " + _cp_html.escape(_cp_t("Come mettere la foto")) + "</b><br>"
                    + _cp_html.escape(_cp_t("1) Tocca «Scegli la foto» (galleria o fotocamera). 2) Con i cursori ingrandisci e sposta la foto finché il viso sta al centro dell'ovale tratteggiato. 3) Tocca «Salva». Puoi ricentrarla quando vuoi.")) + "</div>", unsafe_allow_html=True)
        f = st.file_uploader("📷 " + _cp_t("Scegli la foto (facoltativa)"), type=["jpg", "jpeg", "png", "webp"], key=k + "_up")
        ok_ = k + "_ob"
        if f is not None:
            ident = getattr(f, "file_id", None) or f"{f.name}{f.size}"
            if st.session_state.get(k + "_fid") != ident:
                try:
                    im0 = cp_img_apri(f.getvalue())
                    st.session_state[ok_] = im0
                    st.session_state[k + "_fid"] = ident
                    st.session_state[k + "_orig_bytes"] = True
                    st.session_state[k + "_nome_orig"] = f.name
                    st.session_state[k + "_zoom"] = 1.0
                    st.session_state[k + "_px"] = 50
                    st.session_state[k + "_py"] = 30 if im0.size[1] > im0.size[0] else 50
                    st.session_state[k + "_cur"] = st.session_state[k + "_init"] = (1.0, 50, st.session_state[k + "_py"])
                    st.session_state[k + "_jv"] = ""
                    st.session_state.pop(k + "_jlast", None)
                except Exception:
                    st.warning(_cp_t("Non riesco a leggere questa foto: provane un'altra."))
        if ok_ not in st.session_state and p.get("foto_orig") and st.button("🔄 " + _cp_t("Ricentra la foto già salvata"), key=k + "_ricentra", width="stretch"):
            dati_o = cp_file_leggi(p["foto_orig"])
            if dati_o:
                st.session_state[ok_] = cp_img_apri(dati_o)
                pos = p.get("foto_pos") or [1.0, 50, 30]
                st.session_state[k + "_zoom"], st.session_state[k + "_px"], st.session_state[k + "_py"] = round(float(pos[0]), 2), int(pos[1]), int(pos[2])
                st.session_state[k + "_cur"] = st.session_state[k + "_init"] = (round(float(pos[0]), 2), int(pos[1]), int(pos[2]))
                st.session_state[k + "_jv"] = ""
                st.session_state.pop(k + "_jlast", None)
                st.rerun()
            else:
                st.warning(_cp_t("Non trovo la foto originale: scegli di nuovo la foto."))
        foto_att = p.get("foto", "")
        foto_pos = p.get("foto_pos")
        if ok_ in st.session_state:
            im0 = st.session_state[ok_]
            et = "cpvista" + k
            with st.container(key="nascosti_cpv_" + k):                      # dove l'editor a pizzico scrive la posizione
                jv = st.text_input(et, key=k + "_jv", label_visibility="collapsed")
            if jv and jv != st.session_state.get(k + "_jlast"):
                try:
                    zz, pp, qq = jv.split("|")
                    st.session_state[k + "_zoom"], st.session_state[k + "_px"], st.session_state[k + "_py"] = round(float(zz), 2), int(float(pp)), int(float(qq))
                    st.session_state[k + "_cur"] = (st.session_state[k + "_zoom"], st.session_state[k + "_px"], st.session_state[k + "_py"])
                    st.session_state[k + "_jlast"] = jv
                except Exception:
                    pass
            vetrina = st.container(key="cp_vetrina_" + k)
            with st.expander("🎚️ " + _cp_t("Se il pizzico non funziona: usa i cursori")):
                zoom = st.slider("🔍 " + _cp_t("Ingrandisci / rimpicciolisci"), 0.7, 4.0, step=0.01, key=k + "_zoom")
                px = st.slider("↔️ " + _cp_t("Sposta a sinistra / a destra"), 0, 100, key=k + "_px")
                py = st.slider("↕️ " + _cp_t("Sposta in alto / in basso"), 0, 100, key=k + "_py")
            cur = (round(zoom, 2), px, py)
            if cur != st.session_state.get(k + "_cur"):                       # mossi i cursori: l'editor riparte da qui
                st.session_state[k + "_cur"] = cur
                st.session_state[k + "_init"] = cur
            ini = st.session_state.setdefault(k + "_init", cur)
            with vetrina:
                if "_mostra_editor" in globals():
                    _mostra_editor(cp_editor_html(cp_img_uri(im0, 85), et, *ini), 400)
            rit = cp_img_ritaglio(im0, zoom, px, py)
            foto_att = cp_img_uri(rit)
            foto_pos = [zoom, px, py]
            st.caption("👆 " + _cp_t("Quando sei contento, scorri in basso e tocca «Salva»."))
        elif foto_att:
            st.markdown(f"<div class='cp-anteprima' style=\"background-image:url('{_cp_html.escape(foto_att, quote=True)}')\"></div>", unsafe_allow_html=True)
        if foto_att and st.checkbox("🗑️ " + _cp_t("Togli la foto"), key=k + "_togli"):
            foto_att, foto_pos = "", None
        # 2) chi è
        c1, c2 = st.columns(2, gap="small")
        nome = c1.text_input(_cp_t("Nome") + " *", value=p.get("nome", ""), key=k + "_nome")
        cognome = c2.text_input(_cp_t("Cognome"), value=p.get("cognome", ""), key=k + "_cogn")
        sopr = st.text_input(_cp_t("Soprannome (facoltativo)"), value=p.get("soprannome", ""), key=k + "_sopr")
        rel_att = p.get("relazione", "")
        relazione = st.selectbox(_cp_t("Chi è per te"), CP_RELAZIONI, index=CP_RELAZIONI.index(rel_att) if rel_att in CP_RELAZIONI else 0,
                                 format_func=lambda x: _cp_t(x) if x else "—", key=k + "_rel")
        # 3) nascita
        nasc_att = cp_data(p.get("nascita"))
        nascita = cp_campo_data(k + "_nasc", "🎂 " + _cp_t("Data di nascita") + " *", nasc_att)
        anno_ignoto = st.checkbox(_cp_t("Non conosco l'anno (conta solo giorno e mese)"), value=bool(p.get("anno_ignoto")), key=k + "_anno")
        luogo = st.text_input("📍 " + _cp_t("Luogo di nascita"), value=p.get("luogo", ""), key=k + "_luogo")
        # 4) contatti
        st.markdown("<div style='margin-top:6px;font-weight:700'>" + _cp_html.escape(_cp_t("Contatti")) + "</div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2, gap="small")
        cell = c3.text_input("📱 " + _cp_t("Cellulare"), value=p.get("cellulare", ""), key=k + "_cell")
        fisso = c4.text_input("☎️ " + _cp_t("Telefono fisso"), value=p.get("fisso", ""), key=k + "_fisso")
        wa = st.text_input("🟢 WhatsApp", value=p.get("whatsapp", ""), key=k + "_wa", placeholder=_cp_t("se vuoto uso il cellulare"))
        tg = st.text_input("✈️ Telegram", value=p.get("telegram", ""), key=k + "_tg", placeholder="@nomeutente")
        email = st.text_input("✉️ Email", value=p.get("email", ""), key=k + "_mail")
        # 5) dove
        indirizzo = st.text_area("🏠 " + _cp_t("Indirizzo"), value=p.get("indirizzo", ""), key=k + "_ind", height=70)
        sito = cc_campo_sito(p.get("sito", ""), k + "_sito")
        # 6) da ricordare
        regalo = st.text_input("🎁 " + _cp_t("Idee regalo"), value=p.get("regalo", ""), key=k + "_reg")
        note = st.text_area("📝 " + _cp_t("Note"), value=p.get("note", ""), key=k + "_note", height=70)
        # 7) scomparsa
        scomp = st.checkbox("🕯️ " + _cp_t("Questa persona non c'è più"), value=bool(p.get("scomparso")), key=k + "_sc",
                            help=_cp_t("Al posto del segno zodiacale compare una candela accesa."))
        data_sc = None
        if scomp:
            data_sc = cp_campo_data(k + "_dsc", _cp_t("Data (facoltativa)"), cp_data(p.get("data_scomparsa")))
        preghiera, pensiero, voce_nuova, voce_togli = True, "", None, False
        if scomp:
            st.markdown("<div style='margin-top:8px;font-weight:700'>🕊️ " + _cp_html.escape(_cp_t("Ricordo")) + "</div>", unsafe_allow_html=True)
            preghiera = st.checkbox(_cp_t("Mostra la preghiera dell'eterno riposo"), value=p.get("preghiera", True), key=k + "_pregh")
            pensiero = st.text_area("✍️ " + _cp_t("Un pensiero personale (scrivi quanto vuoi, senza limiti)"), value=p.get("pensiero", ""), key=k + "_pens", height=220)
            st.markdown("<div style='font-weight:600;margin-top:4px'>🎙️ " + _cp_html.escape(_cp_t("Messaggio vocale")) + "</div>", unsafe_allow_html=True)
            if p.get("voce"):
                dv = cp_file_leggi(p["voce"])
                if dv:
                    st.audio(dv, format=p["voce"].get("mime", "audio/ogg"))
                    st.caption(_cp_t("Questo è il messaggio salvato. Se ne registri un altro qui sotto, lo sostituisce."))
                voce_togli = st.checkbox("🗑️ " + _cp_t("Togli il messaggio vocale"), key=k + "_vtogli")
            reg = st.audio_input("🎙️ " + _cp_t("Registra adesso (tocca il microfono, parla, poi ferma)"), key=k + "_vreg") if hasattr(st, "audio_input") else None
            fv = st.file_uploader("📁 " + _cp_t("Oppure scegli un file audio"), type=["mp3", "m4a", "ogg", "wav", "aac", "opus", "webm"], key=k + "_vup")
            voce_nuova = reg or fv
            sep_dati, sep_nuove, sep_togli = sp_campi(p, k) if "sp_campi" in globals() else (None, [], [])
        else:
            sep_dati, sep_nuove, sep_togli = None, [], []
        b1, b2 = st.columns(2, gap="small")
        if b1.button("✅ " + _cp_t("Salva"), type="primary", key=k + "_ok", width="stretch"):
            if not nome.strip():
                st.error(_cp_t("Scrivi almeno il nome."))
                return
            if not nascita:
                st.error(_cp_t("Scegli la data di nascita."))
                return
            nid = pid or cp_nuovo_id()
            rec = {"id": nid, "nome": nome.strip(), "cognome": cognome.strip(), "soprannome": sopr.strip(), "relazione": relazione,
                   "nascita": nascita.isoformat(), "anno_ignoto": bool(anno_ignoto), "luogo": luogo.strip(), "cellulare": cell.strip(),
                   "fisso": fisso.strip(), "whatsapp": wa.strip(), "telegram": tg.strip(), "email": email.strip(), "indirizzo": indirizzo.strip(),
                   "sito": (sito or "").strip(), "regalo": regalo.strip(), "note": note.strip(), "foto": foto_att, "scomparso": bool(scomp),
                   "data_scomparsa": data_sc.isoformat() if (scomp and data_sc) else "", "preghiera": bool(preghiera), "pensiero": pensiero.strip()}
            da_cancellare = []
            if scomp and sep_dati is not None:                          # dove riposa (sepolture.py)
                try:
                    with st.spinner(_cp_t("Salvo le foto…")):
                        rec["sepoltura"], _tolte = sp_salva_foto(sep_dati, sep_nuove, sep_togli)
                    da_cancellare += _tolte
                except Exception as _e:
                    st.error(f"Non sono riuscito a salvare le foto della sepoltura ({type(_e).__name__}). Riprova.")
                    return
            elif p.get("sepoltura"):
                rec["sepoltura"] = p["sepoltura"]                        # non si perde se togli la spunta
            # foto originale (serve per ricentrare dopo) e posizione
            vecchia_o = p.get("foto_orig")
            if foto_att and foto_pos:
                rec["foto_pos"] = foto_pos
                if st.session_state.get(k + "_orig_bytes"):
                    try:
                        rec["foto_orig"] = cp_file_salva(cp_img_bytes(st.session_state[ok_], 85), "foto_originale.webp", "image/webp")
                        if vecchia_o:
                            da_cancellare.append(vecchia_o)
                    except Exception:
                        st.warning(_cp_t("Non sono riuscito a tenere la foto originale: la foto nel cerchio è salvata lo stesso."))
                elif vecchia_o:
                    rec["foto_orig"] = vecchia_o
            elif vecchia_o:
                da_cancellare.append(vecchia_o)
            # messaggio vocale
            vecchia_v = p.get("voce")
            if scomp:
                if voce_nuova is not None:
                    risultato = cp_audio_comprimi(voce_nuova.getvalue(), getattr(voce_nuova, "name", "voce.wav"))
                    if not risultato:
                        st.error(_cp_t("Il messaggio vocale è troppo lungo o in un formato che non riesco a ridurre: registralo più corto."))
                        return
                    with st.spinner(_cp_t("Salvo il messaggio vocale…")):
                        rec["voce"] = cp_file_salva(*risultato)
                    if vecchia_v:
                        da_cancellare.append(vecchia_v)
                elif vecchia_v and not voce_togli:
                    rec["voce"] = vecchia_v
                elif vecchia_v:
                    da_cancellare.append(vecchia_v)
            elif vecchia_v:
                da_cancellare.append(vecchia_v)

            def _m(d):
                lst = d.setdefault("compleanni", [])
                for i, x in enumerate(lst):
                    if x.get("id") == nid:
                        lst[i] = rec
                        break
                else:
                    lst.append(rec)
            _cp_salva(_m, "Compleanni: " + rec["nome"])
            cp_file_cancella(da_cancellare)
            for s in [x for x in st.session_state if str(x).startswith(k)]:
                st.session_state.pop(s, None)
            st.session_state["cp_modulo"] = None
            st.session_state["messaggio"] = "✅ " + _cp_t("{nome} salvato/a.", nome=rec["nome"])
            st.rerun()
        if b2.button(_cp_t("Annulla"), key=k + "_no", width="stretch"):
            st.session_state["cp_modulo"] = None
            st.rerun()


def _cp_elenco():
    oggi = _cp_dt.date.today()
    lista = [x for x in _cp_dati().get("compleanni", []) if cp_data(x.get("nascita"))]
    if not lista:
        st.info("🎂 " + _cp_t("Non c'è ancora nessuno. Tocca «Aggiungi una persona»."))
        return
    cerca = st.text_input("🔍 " + _cp_t("Cerca per nome"), key="cp_cerca").strip().lower() if len(lista) > 5 else ""
    if cerca:
        lista = [x for x in lista if cerca in (str(x.get("nome", "")) + " " + str(x.get("cognome", "")) + " " + str(x.get("soprannome", ""))).lower()]
    vivi = sorted([x for x in lista if not x.get("scomparso")], key=lambda x: cp_prossimo(cp_data(x["nascita"]), oggi))
    memoria = sorted([x for x in lista if x.get("scomparso")], key=lambda x: cp_prossimo(cp_data(x["nascita"]), oggi))
    for titolo, gruppo in (("", vivi), ("🕯️ " + _cp_t("In memoria"), memoria)):
        if not gruppo:
            continue
        if titolo:
            st.markdown(f"<div style='margin:18px 0 0;font-weight:800;color:{CP_COLORE_MEMORIA}'>{_cp_html.escape(titolo)}</div>", unsafe_allow_html=True)
        for p in gruppo:
            pid = p["id"]
            st.markdown(_cp_scheda_html(p, oggi), unsafe_allow_html=True)
            if p.get("scomparso") and p.get("voce"):
                with st.expander("🎙️ " + _cp_t("Ascolta il messaggio vocale")):
                    dv = cp_file_leggi(p["voce"])
                    if dv:
                        st.audio(dv, format=p["voce"].get("mime", "audio/ogg"))
                    else:
                        st.caption(_cp_t("Non trovo il file audio."))
            if p.get("scomparso") and "sp_mostra" in globals():
                sp_mostra(p)
            _cp_pulsanti(p, pid)
            if st.session_state.get("cp_modulo") == pid:
                _cp_modulo(pid)
                continue
            c1, c2 = st.columns(2, gap="small")
            if c1.button("✏️ " + _cp_t("Modifica"), key=f"cp_mod_{pid}", width="stretch"):
                st.session_state["cp_modulo"] = pid
                st.session_state["cp_elimina"] = None
                st.rerun()
            if st.session_state.get("cp_elimina") == pid:
                st.warning(_cp_t("Eliminare {nome}? Finisce nel cestino e lo puoi recuperare.", nome=p.get("nome", "")))
                s1, s2 = st.columns(2, gap="small")
                if s1.button("🗑️ " + _cp_t("Sì, elimina"), key=f"cp_siel_{pid}", type="primary", width="stretch"):
                    _cp_salva(lambda d, _i=pid: d.__setitem__("compleanni", [x for x in d.get("compleanni", []) if x.get("id") != _i]), "Compleanni: eliminato " + str(p.get("nome", "")))
                    cp_file_cancella([p.get("foto_orig"), p.get("voce")] + (sp_files(p) if "sp_files" in globals() else []))
                    st.session_state["cp_elimina"] = None
                    st.rerun()
                if s2.button(_cp_t("No"), key=f"cp_noel_{pid}", width="stretch"):
                    st.session_state["cp_elimina"] = None
                    st.rerun()
            elif c2.button("🗑️ " + _cp_t("Elimina"), key=f"cp_el_{pid}", width="stretch"):
                st.session_state["cp_elimina"] = pid
                st.rerun()


def cp_blocco_utilita():
    """Il contenuto del riquadro «Compleanni» in Utilità: il badge nella lingua apre e chiude la sezione."""
    st.markdown(CP_CSS, unsafe_allow_html=True)
    b = CPI_BADGE.get(_cp_lg()) or CPI_BADGE["it"]
    st.markdown("<style>div.st-key-cp_apri [data-testid=stButton],div.st-key-cp_apri [data-testid=stElementContainer]{display:flex !important;justify-content:center;width:100% !important}div.st-key-cp_apri{display:flex;justify-content:center}div.st-key-cp_apri button{background:url('data:image/webp;base64," + b +
                "') center/contain no-repeat !important;border:0 !important;box-shadow:none !important;color:transparent !important;width:210px !important;"
                "max-width:70vw;aspect-ratio:410/420;height:auto !important;min-height:0 !important;padding:0 !important;border-radius:0 !important}"
                "div.st-key-cp_apri button p{font-size:0 !important}div.st-key-cp_apri button:hover{filter:drop-shadow(0 0 12px rgba(255,200,90,.9))}</style>",
                unsafe_allow_html=True)
    with st.container(key="cp_apri"):
        if st.button(_cp_t("Compleanni"), key="cp_apri_b"):
            st.session_state["cp_aperto"] = not st.session_state.get("cp_aperto")
            st.rerun()
    if not st.session_state.get("cp_aperto"):
        st.caption(_cp_t("Tocca il badge per aprire i compleanni."))
        return
    if "avs_apri" in globals() and st.button("🔔 " + _cp_t("Avvisi dei compleanni"), key="cp_campanello", width="stretch"):
        avs_apri("compleanni", "Compleanni")
    if st.button("➕ " + _cp_t("Aggiungi una persona"), key="cp_nuovo", type="primary", width="stretch"):
        st.session_state["cp_modulo"] = "__nuovo__"
        st.rerun()
    if st.session_state.get("cp_modulo") == "__nuovo__":
        _cp_modulo("")
    _cp_elenco()
