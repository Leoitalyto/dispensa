# -*- coding: utf-8 -*-
"""Grafica moderna (vetro, carte fluttuanti, contatori, navigazione a pillola).
Cambia solo l'aspetto: i testi restano identici. Caricato da app_dispensa.py dopo interattivi.py."""


def kpi_html(prodotti, arancioni, rossi, scaduti):
    """I quattro contatori in cima alla pagina, come carte colorate."""
    def carta(classe, etichetta, numero, icona=""):
        return (f"<div class='kpi {classe}'><div class='kpi-et'>{html.escape(etichetta)}</div>"
                f"<div class='kpi-n'>{numero}</div><span class='kpi-ico'>{icona}</span></div>")
    return ("<div class='kpi-griglia'>"
            + carta("kpi-ok", t("Prodotti"), prodotti, "🍃")
            + carta("kpi-arancio", t("Entro 2 mesi"), arancioni)
            + carta("kpi-rosso", t("Entro 1 mese"), rossi)
            + carta("kpi-scuro", t("Scaduti"), scaduti, "!")
            + "</div>")


def intestazione_sezione(titolo, n, classe):
    """Titolo di una sezione dell'avviso con il numero in un cerchio colorato."""
    return (f"<div class='sez-avv'><span>{html.escape(titolo)} ({n})</span><b class='{classe}'>{n}</b></div>")


_SIMBOLO_STATO = {"scaduto": "✕", "rosso": "!", "arancione": "!", "ok": "✓", "nessuna": "–"}


def scheda_html(r, data_oggi, mie):
    """Scheda prodotto: foto in cornice, nome grande, quantita', pillola di scadenza con icona, data e allergeni sulla stessa riga."""
    stato, giorni = stato_scadenza(r.get("scadenza"), data_oggi)
    marca = f"<div class='marca'>{html.escape(r['marca'])}</div>" if r.get("marca") else ""
    data = f"<span class='data'>{data_it(r['scadenza'])}</span>" if r.get("scadenza") else ""
    nota = f"<div class='nota'>📝 {html.escape(r['note'])}</div>" if r.get("note") else ""
    return (f"<div class='scheda' style='--c:{COLORI[stato]}'><div class='foto'>{foto_html(r)}</div>"
            f"<div class='corpo'><div class='nome'>{html.escape(r.get('nome', ''))}</div>{marca}"
            f"<div class='quantita'>📦 {html.escape(descrivi([r]))}</div>"
            f"<span class='scadenza'><i class='st-ico'>{_SIMBOLO_STATO.get(stato, '·')}</i>{testo_giorni(stato, giorni)}</span>"
            f"<div class='riga-data'>{data}{badge_allergeni(r, mie)}</div>{nota}</div></div>")


def player_html(wav):
    """Lettore audio moderno (play, tempo, barra con sfumatura, volume) per l'avviso iniziale."""
    b64 = base64.b64encode(wav).decode()
    return """<style>
html{color-scheme:light;background:transparent}body{margin:0;padding:4px 6px 18px;background:transparent;font-family:Inter,system-ui,sans-serif}
.p{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.92);border-radius:999px;padding:9px 18px 9px 9px;
 border:1px solid #fff;box-shadow:0 8px 22px rgba(0,60,50,.16)}
#b{width:50px;height:50px;border-radius:50%;border:0;background:#fff;box-shadow:0 5px 14px rgba(0,0,0,.2);display:flex;
 align-items:center;justify-content:center;cursor:pointer;flex:none;padding:0}
#t{font-size:13px;font-weight:700;color:#475569;min-width:78px;white-space:nowrap}
#r{flex:1;min-width:0;-webkit-appearance:none;appearance:none;height:8px;border-radius:8px;outline:none;margin:0;
 background:linear-gradient(90deg,#86efac,#fde047 0%,#e5e7eb 0%)}
#r::-webkit-slider-thumb{-webkit-appearance:none;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.35)}
#r::-moz-range-thumb{width:22px;height:22px;border:0;border-radius:50%;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.35)}
#v{background:none;border:0;cursor:pointer;padding:0;flex:none;display:flex}
</style>
<div class="p"><button id="b" aria-label="play"><svg id="i" width="22" height="22" viewBox="0 0 24 24" fill="#111"><path d="M7 4.5v15l12-7.5z"/></svg></button>
<span id="t">0:00 / 0:00</span><input id="r" type="range" min="0" max="1000" value="0">
<button id="v" aria-label="volume"><svg width="26" height="26" viewBox="0 0 24 24" fill="#111"><path d="M4 9v6h4l5 4V5L8 9z"/><path d="M16 8.5a5 5 0 0 1 0 7" stroke="#111" stroke-width="2" fill="none" stroke-linecap="round"/></svg></button></div>
<audio id="a" preload="auto" src="data:audio/wav;base64,__B64__"></audio>
<script>
var a=document.getElementById('a'),b=document.getElementById('b'),r=document.getElementById('r'),t=document.getElementById('t'),
i=document.getElementById('i'),v=document.getElementById('v');
var PLAY='M7 4.5v15l12-7.5z',PAUSE='M6 4h4v16H6zM14 4h4v16h-4z';
function f(x){x=Math.floor(x||0);return Math.floor(x/60)+':'+('0'+(x%60)).slice(-2);}
function draw(){var d=a.duration||0,p=d?a.currentTime/d*100:0;r.value=p*10;
 r.style.background='linear-gradient(90deg,#86efac,#fde047 '+p+'%,#e5e7eb '+p+'%)';t.textContent=f(a.currentTime)+' / '+f(d);}
a.addEventListener('timeupdate',draw);a.addEventListener('loadedmetadata',draw);
a.addEventListener('play',function(){i.innerHTML='<path d="'+PAUSE+'"/>';});
a.addEventListener('pause',function(){i.innerHTML='<path d="'+PLAY+'"/>';});
a.addEventListener('ended',function(){i.innerHTML='<path d="'+PLAY+'"/>';});
b.onclick=function(){if(a.paused){if(a.ended)a.currentTime=0;a.play();}else{a.pause();}};
r.oninput=function(){if(a.duration){a.currentTime=r.value/1000*a.duration;}draw();};
v.onclick=function(){a.muted=!a.muted;v.style.opacity=a.muted?.35:1;};
var q=a.play();if(q&&q.catch){q.catch(function(){});}
</script>""".replace("__B64__", b64)


_VASI = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='150' viewBox='0 0 300 150'>"
         "<g stroke='%23ffffff' stroke-opacity='.65' stroke-width='2' fill='%23ffffff' fill-opacity='.22'>"
         "<rect x='60' y='62' width='62' height='80' rx='12'/><rect x='128' y='34' width='70' height='108' rx='14'/>"
         "<rect x='204' y='70' width='60' height='72' rx='12'/></g>"
         "<g fill='%23ffffff' fill-opacity='.5'><rect x='66' y='50' width='50' height='14' rx='5'/>"
         "<rect x='136' y='20' width='54' height='16' rx='6'/><rect x='210' y='58' width='48' height='14' rx='5'/>"
         "<rect x='72' y='86' width='38' height='30' rx='6'/><rect x='140' y='70' width='46' height='40' rx='7'/>"
         "<rect x='214' y='92' width='38' height='28' rx='6'/></g>"
         "<g fill='%23bbf7d0' fill-opacity='.7'><path d='M30 20 C58 30 60 66 34 80 C8 64 6 34 30 20Z'/>"
         "<path d='M276 14 C296 28 292 58 270 66 C252 48 256 24 276 14Z'/></g></svg>\")")

CSS = CSS.replace("<style>", "<style>\n@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&display=swap');", 1)
CSS = CSS.replace("</style>", """
.stApp{font-family:Inter,"Source Sans",system-ui,sans-serif;
 background:__GRANA__,
 radial-gradient(900px 520px at 0% 0%,rgba(236,252,244,.95),transparent 62%),
 linear-gradient(180deg,#e3f6ed 0%,#c9ecdd 38%,#a9dbd5 70%,#8ec4d8 100%) !important;
 background-attachment:fixed !important}
[data-testid="stMainBlockContainer"]{padding-bottom:130px !important}
.stMarkdown,.stButton,label,input,textarea{font-family:inherit}

/* ---------- intestazione ---------- */
.hero{display:flex;flex-direction:column;justify-content:space-between;gap:18px;position:relative;overflow:hidden;min-height:230px;
 border-radius:34px !important;padding:22px !important;
 background:linear-gradient(90deg,#34b58f 0%,#34b58f 40%,rgba(52,181,143,.55) 58%,rgba(52,181,143,0) 78%),url(__FOTO__) right center/auto 100% no-repeat,
 linear-gradient(135deg,#2fae8a,#4cc3a2) !important;border:1px solid rgba(255,255,255,.65) !important;
 box-shadow:0 20px 44px rgba(0,100,90,.28),inset 0 1px 0 rgba(255,255,255,.6) !important}
.hero>*{position:relative;z-index:1}
.hero-ico{flex:none;width:58px;height:58px;border-radius:50%;display:flex;align-items:center;justify-content:center;
 background:rgba(255,255,255,.22);border:1.5px solid rgba(255,255,255,.7);backdrop-filter:blur(8px);box-shadow:0 8px 20px rgba(0,60,50,.2)}
.hero-testi{max-width:66%}
.hero h1{margin:0 !important;font-size:2rem !important;font-weight:900 !important;line-height:1.05;letter-spacing:-.02em;color:#fff;padding:0 !important}
.hero p{margin:8px 0 0 !important;font-weight:700;opacity:.97;font-size:.95rem;color:#fff}

/* ---------- contatori ---------- */
.kpi-griglia{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:4px 0 14px}
@media (min-width:760px){.kpi-griglia{grid-template-columns:repeat(4,1fr)}}
.kpi{position:relative;border-radius:28px;padding:14px 16px 16px;min-height:112px;overflow:hidden;border:1px solid rgba(255,255,255,.9);
 box-shadow:0 12px 26px rgba(0,60,50,.14),inset 0 1px 0 rgba(255,255,255,.9)}
.kpi-et{font-weight:800;font-size:.98rem}
.kpi-n{font-weight:900;font-size:2.7rem;line-height:1.05;margin-top:4px;letter-spacing:-.02em}
.kpi-ico{position:absolute;right:14px;bottom:14px;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;
 font-size:1.15rem;font-weight:900;color:#fff}
.kpi-ok{background:linear-gradient(160deg,#f4fcf7,#d6f1e1);color:#14532d}
.kpi-ok .kpi-ico{background:linear-gradient(135deg,#34d399,#059669);box-shadow:0 0 18px rgba(16,185,129,.6)}
.kpi-arancio{background:linear-gradient(160deg,#fff8ee,#ffe4c2);color:#b45309}
.kpi-arancio .kpi-ico{background:radial-gradient(circle at 35% 30%,#fff3d6,#fdba74 55%,#f59e0b);box-shadow:0 0 20px rgba(245,158,11,.7)}
.kpi-rosso{background:linear-gradient(160deg,#fff4f4,#ffd5d5);color:#b91c1c}
.kpi-rosso .kpi-ico{background:radial-gradient(circle at 35% 30%,#ffe0e0,#f87171 55%,#dc2626);box-shadow:0 0 20px rgba(239,68,68,.7)}
.kpi-scuro{background:linear-gradient(160deg,#1f3b63,#0e1f38);color:#fff;border-color:rgba(255,255,255,.18)}
.kpi-scuro .kpi-ico{background:linear-gradient(135deg,#f87171,#dc2626);box-shadow:0 0 18px rgba(239,68,68,.7)}

/* ---------- avvisi di scadenza ---------- */
.avviso{position:relative;border-radius:26px !important;padding:16px 18px 16px 32px !important;border-left:1px solid rgba(255,255,255,.9) !important;background:rgba(255,255,255,.72) !important;
 backdrop-filter:blur(10px);box-shadow:0 12px 28px rgba(0,60,50,.14) !important;border-top:1px solid rgba(255,255,255,.9);
 border-right:1px solid rgba(255,255,255,.9);border-bottom:1px solid rgba(255,255,255,.9)}
.avviso::before{content:"";position:absolute;left:13px;top:16px;bottom:16px;width:6px;border-radius:6px;background:var(--acc,#999)}
.avviso.rosso{--acc:linear-gradient(180deg,#f87171,#dc2626)}.avviso.arancione{--acc:linear-gradient(180deg,#fb923c,#f59e0b)}
.avviso.scaduto{--acc:linear-gradient(180deg,#6b7280,#1f2937)}
.avviso h3{font-weight:900;font-size:1.1rem}
.avviso .tot{font-weight:700;opacity:.8}
.avviso ul{list-style:none;padding:0 !important;margin:10px 0 0 0 !important;margin-inline-start:0 !important;padding-inline-start:0 !important;display:flex;flex-direction:column;gap:8px}
.avviso li{margin:0 !important;background:rgba(255,255,255,.65);border-radius:18px;padding:10px 12px;font-weight:700;box-shadow:inset 0 0 0 1px rgba(0,0,0,.04)}
.avviso.rosso{background:linear-gradient(160deg,rgba(255,244,244,.92),rgba(255,222,222,.85)) !important}
.avviso.arancione{background:linear-gradient(160deg,rgba(255,248,236,.92),rgba(255,232,203,.85)) !important}
.avviso.scaduto{background:linear-gradient(160deg,rgba(236,238,243,.92),rgba(214,219,230,.85)) !important;border-color:#374151 !important;color:#111827 !important}

/* ---------- navigazione fissa in basso ---------- */
[role="tablist"]{position:fixed !important;left:50%;bottom:max(12px,env(safe-area-inset-bottom));top:auto !important;transform:translateX(-50%);
 width:min(600px,calc(100vw - 24px));z-index:80;gap:2px !important;background:rgba(255,255,255,.86);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
 border-radius:999px;padding:6px !important;border:1px solid rgba(255,255,255,.95);overflow-x:auto;scrollbar-width:none;
 box-shadow:0 16px 36px rgba(0,80,70,.26),inset 0 1px 0 rgba(255,255,255,.95)}
[role="tablist"]::-webkit-scrollbar{display:none}
[role="tab"]{flex:1 0 auto;min-width:54px;border-radius:999px !important;padding:8px 8px !important;height:auto !important;background:transparent;
 transition:all .15s;border-bottom:0 !important}
[role="tab"] p{display:flex;flex-direction:column;align-items:center;gap:3px;margin:0 !important;font-weight:800 !important;font-size:.7rem !important;line-height:1.1}
[role="tab"] p>span[role="img"],[role="tab"] [data-testid="stIconMaterial"]{font-size:1.65rem !important;line-height:1;vertical-align:middle}
[role="tab"][aria-selected="true"]{background:linear-gradient(135deg,#10b981,#0d9488) !important;border-radius:999px !important;
 box-shadow:0 8px 18px rgba(13,148,136,.45),inset 0 1px 0 rgba(255,255,255,.4)}
[role="tab"][aria-selected="true"] p,[role="tab"][aria-selected="true"] span{color:#fff !important}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"],.react-aria-SelectionIndicator,[data-testid="stTabsScrollRight"]{display:none !important}

/* ---------- moduli e controlli ---------- */
[data-testid="stForm"],[data-testid="stExpander"]{background:rgba(255,255,255,.72) !important;backdrop-filter:blur(10px);
 border:1px solid rgba(255,255,255,.95) !important;border-radius:28px !important;box-shadow:0 12px 28px rgba(0,60,50,.12)}
[data-testid="stRadio"] [role="radiogroup"]{background:rgba(255,255,255,.72);border-radius:22px;padding:6px;gap:6px;
 border:1px solid rgba(255,255,255,.95);box-shadow:inset 0 1px 3px rgba(0,0,0,.06),0 6px 16px rgba(0,60,50,.08)}
[data-testid="stRadio"] label{border-radius:16px;padding:8px 12px !important;flex:1 1 auto;margin:0 !important;transition:all .15s}
[data-testid="stRadio"] label:has(input:checked){background:linear-gradient(135deg,rgba(16,185,129,.24),rgba(13,148,136,.3));
 box-shadow:0 6px 14px rgba(13,148,136,.25),inset 0 1px 0 rgba(255,255,255,.7)}
[data-testid="stFileUploaderDropzone"]{border:2px dashed rgba(13,148,136,.55) !important;border-radius:24px !important;background:rgba(255,255,255,.62) !important}
[data-testid="stToggle"] label span{font-weight:700}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:linear-gradient(135deg,#14b8a6,#06b6d4) !important;color:#fff !important;border:0 !important;
 box-shadow:0 10px 22px rgba(6,182,212,.4),inset 0 1px 0 rgba(255,255,255,.5) !important}
[data-testid="stSidebar"]{backdrop-filter:blur(14px)}

/* ---------- schede prodotto ---------- */
.griglia{gap:18px}
.scheda{border-top:0 !important;border-radius:32px !important;padding:12px !important;background:rgba(255,255,255,.84) !important;
 backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.95);
 box-shadow:0 16px 36px rgba(0,70,60,.17),0 0 0 4px rgba(150,230,190,.3) !important}
.scheda .foto{height:170px !important;border-radius:24px;background:linear-gradient(180deg,#ffffff,#edf7f1) !important;
 box-shadow:inset 0 0 0 1px rgba(0,0,0,.04),0 8px 18px rgba(0,0,0,.08)}
.scheda .foto img{border-radius:18px;max-height:150px !important}
.scheda .corpo{padding:12px 6px 6px !important;gap:8px !important}
.scheda .nome{font-size:1.5rem !important;line-height:1.15 !important;font-weight:900 !important;letter-spacing:-.015em}
.st-ico{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;border:2px solid #fff;
 font-style:normal;font-size:.72rem;font-weight:900;line-height:1;margin-right:4px;vertical-align:middle}
.riga-data{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.scheda .marca{font-weight:700;opacity:.6 !important}
.scheda .quantita{display:inline-flex;align-items:center;gap:6px;width:fit-content;background:#fff;border:1px solid rgba(0,0,0,.1);
 border-radius:999px;padding:5px 13px;font-weight:800;box-shadow:0 3px 8px rgba(0,0,0,.05)}
.scadenza{padding:7px 16px !important;font-weight:800 !important;font-size:.92rem !important;
 background:linear-gradient(180deg,color-mix(in srgb,var(--c) 80%,#fff),var(--c)) !important;
 box-shadow:0 8px 18px color-mix(in srgb,var(--c) 45%,transparent),inset 0 1px 0 rgba(255,255,255,.45)}
.scheda .data{display:inline-block;width:fit-content;background:none !important;padding:0 !important;font-size:1rem;font-weight:700;color:#4b5563;opacity:1 !important}

/* ---------- avviso "Prodotti da controllare" ---------- */
[data-testid="stDialog"] [role="dialog"]{border-radius:32px !important;border:1px solid rgba(255,255,255,.95);
 background:linear-gradient(180deg,#ffffff,#e4f5ec) !important;
 box-shadow:0 34px 90px rgba(0,50,40,.4)}
[data-testid="stDialog"] [role="dialog"] h2{font-weight:900;letter-spacing:-.01em}
[data-testid="stDialog"] button[aria-label="Close"]{border-radius:50%;background:rgba(255,255,255,.85);box-shadow:0 4px 12px rgba(0,0,0,.12)}
[data-testid="stDialog"] audio{width:100%;border-radius:999px;background:rgba(255,255,255,.88);box-shadow:0 10px 24px rgba(0,60,50,.14)}
[data-testid="stDialog"] [data-testid="stHorizontalBlock"]:has(.chip-info){background:rgba(255,255,255,.78);border-radius:26px;padding:10px;
 box-shadow:0 10px 24px rgba(0,60,50,.1);border:1px solid rgba(255,255,255,.95);align-items:center}
[data-testid="stDialog"] [data-testid="stHorizontalBlock"]:has(.chip-info){flex-wrap:nowrap !important;gap:12px !important}
[data-testid="stDialog"] [data-testid="stHorizontalBlock"]:has(.chip-info)>[data-testid="stColumn"]:first-child{flex:0 0 76px !important;width:76px !important;min-width:76px !important}
[data-testid="stDialog"] [data-testid="stHorizontalBlock"]:has(.chip-info)>[data-testid="stColumn"]:last-child{flex:1 1 0 !important;min-width:0 !important;width:auto !important}
[data-testid="stDialog"] .stMarkdown strong{font-weight:900;font-size:1.05rem}
[data-testid="stDialog"] .scadenza{white-space:nowrap;font-size:.85rem !important;padding:6px 14px !important}
.chip-info{background:rgba(255,255,255,.85);border-radius:16px;padding:7px 11px;font-size:.82rem;font-weight:700;box-shadow:inset 0 0 0 1px rgba(0,0,0,.05);margin:4px 0 6px}
[data-testid="stDialog"] [data-testid="stImage"] img{border-radius:18px;box-shadow:0 6px 14px rgba(0,0,0,.12)}
[data-testid="stDialog"] [data-testid="stElementContainer"]:has(+ [data-testid="stElementContainer"] button[kind="primary"]) [data-testid="stCaptionContainer"]{
 background:rgba(224,242,254,.85);border-radius:18px;padding:10px 14px;border-left:5px solid #38bdf8;font-weight:700}
[data-testid="stDialog"] .stButton>button[kind="primary"]{width:100%;border-radius:999px;padding:12px 0;font-size:1.1rem;font-weight:900}
.sez-avv{display:flex;align-items:center;justify-content:space-between;font-weight:900;font-size:1.05rem;margin:6px 2px 2px}
.sez-avv b{min-width:30px;height:30px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:.9rem;
 box-shadow:0 4px 10px rgba(0,0,0,.2)}
.sez-avv b.s-scaduti{background:#374151}.sez-avv b.s-rossi{background:linear-gradient(135deg,#f87171,#dc2626)}
.sez-avv b.s-arancio{background:linear-gradient(135deg,#fb923c,#f59e0b)}
@media (max-width:480px){.hero h1{font-size:1.45rem !important}.hero-ico{width:56px;height:56px;font-size:1.6rem}
 .hero::after{opacity:.2;background-size:auto 70%}}
</style>""".replace("__GRANA__", _GRANA).replace("__FOTO__", "\"" + HERO_FOTO + "\""))

if lingua() in LINGUE_DA_DESTRA or lingua() == "ar":
    CSS = CSS.replace("</style>", """
.avviso{padding:16px 32px 16px 18px !important;border-left:1px solid rgba(255,255,255,.9) !important;border-right:1px solid rgba(255,255,255,.9) !important}
.kpi-ico{right:auto;left:14px}
.avviso::before{left:auto;right:13px}
.hero::after{background-position:left bottom}
</style>""")
