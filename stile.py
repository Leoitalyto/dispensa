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
 radial-gradient(900px 520px at 0% 0%,rgba(255,252,225,.95),transparent 62%),
 radial-gradient(800px 560px at 100% 100%,rgba(110,190,215,.55),transparent 60%),
 linear-gradient(180deg,#f7f5e6 0%,#e0f1d8 26%,#c3e5d1 55%,#97cdc8 82%,#80b9cb 100%) !important;
 background-attachment:fixed !important}
.stMarkdown,.stButton,label,input,textarea{font-family:inherit}

/* ---------- intestazione ---------- */
.hero{display:flex;align-items:center;gap:16px;position:relative;overflow:hidden;border-radius:32px !important;padding:22px !important;
 background:linear-gradient(135deg,#0f9d78 0%,#14b8a6 48%,#38bdf8 100%) !important;border:1px solid rgba(255,255,255,.6) !important;
 box-shadow:0 20px 44px rgba(0,100,90,.3),inset 0 1px 0 rgba(255,255,255,.6) !important}
.hero::after{content:"";position:absolute;inset:0;background:__VASI__ right bottom/auto 92% no-repeat;opacity:.85;pointer-events:none}
.hero>*{position:relative;z-index:1}
.hero-ico{flex:none;width:68px;height:68px;border-radius:22px;display:flex;align-items:center;justify-content:center;font-size:2rem;
 background:rgba(255,255,255,.24);border:1px solid rgba(255,255,255,.6);backdrop-filter:blur(8px);box-shadow:0 8px 20px rgba(0,60,50,.25)}
.hero h1{margin:0 !important;font-size:1.75rem !important;font-weight:900 !important;line-height:1.1;letter-spacing:-.02em}
.hero p{margin:6px 0 0 !important;font-weight:700;opacity:.96}

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

/* ---------- navigazione a pillola ---------- */
[role="tablist"]{gap:4px !important;background:rgba(255,255,255,.78);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
 border-radius:999px;padding:6px !important;border:1px solid rgba(255,255,255,.95);
 box-shadow:0 14px 30px rgba(0,80,70,.2),inset 0 1px 0 rgba(255,255,255,.95);position:sticky;top:3.4rem;z-index:60}
[role="tab"]{border-radius:999px !important;padding:8px 14px !important;height:auto !important;background:transparent;transition:all .15s;
 border-bottom:0 !important}
[role="tab"] p{font-weight:800 !important;font-size:.92rem}
[role="tab"][aria-selected="true"]{background:linear-gradient(135deg,#10b981,#0d9488) !important;border-radius:999px !important;
 box-shadow:0 8px 18px rgba(13,148,136,.45),inset 0 1px 0 rgba(255,255,255,.4)}
[role="tab"][aria-selected="true"] p,[role="tab"][aria-selected="true"]{color:#fff !important}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"],.react-aria-SelectionIndicator{display:none !important}

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
.scheda .nome{font-size:1.25rem !important;font-weight:900 !important;letter-spacing:-.01em}
.scheda .marca{font-weight:700;opacity:.6 !important}
.scheda .quantita{display:inline-flex;align-items:center;gap:6px;width:fit-content;background:#fff;border:1px solid rgba(0,0,0,.1);
 border-radius:999px;padding:5px 13px;font-weight:800;box-shadow:0 3px 8px rgba(0,0,0,.05)}
.scadenza{padding:7px 16px !important;font-weight:800 !important;font-size:.92rem !important;
 background:linear-gradient(180deg,color-mix(in srgb,var(--c) 80%,#fff),var(--c)) !important;
 box-shadow:0 8px 18px color-mix(in srgb,var(--c) 45%,transparent),inset 0 1px 0 rgba(255,255,255,.45)}
.scheda .data{display:inline-block;width:fit-content;background:rgba(0,0,0,.05);border-radius:12px;padding:3px 10px;font-weight:700;opacity:1 !important}

/* ---------- avviso "Prodotti da controllare" ---------- */
[data-testid="stDialog"] [role="dialog"]{border-radius:32px !important;border:1px solid rgba(255,255,255,.95);
 background:linear-gradient(180deg,rgba(255,255,255,.9),rgba(230,246,237,.94)) !important;backdrop-filter:blur(20px);
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
</style>""".replace("__GRANA__", _GRANA).replace("__VASI__", _VASI))

if lingua() in LINGUE_DA_DESTRA or lingua() == "ar":
    CSS = CSS.replace("</style>", """
.avviso{padding:16px 32px 16px 18px !important;border-left:1px solid rgba(255,255,255,.9) !important;border-right:1px solid rgba(255,255,255,.9) !important}
.kpi-ico{right:auto;left:14px}
.avviso::before{left:auto;right:13px}
.hero::after{background-position:left bottom}
</style>""")
