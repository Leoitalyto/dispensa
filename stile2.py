# -*- coding: utf-8 -*-
"""Grafica 'vetro menta' (passo 1): banner compatto con i tre vasetti e quattro contatori sempre in fila.
Va caricato dopo stile.py. Serve il file vasetti.webp nella stessa cartella dell'app (se manca, il banner resta senza foto)."""


def _immagine_vasetti():
    try:
        with open(os.path.join(_cartella, "vasetti.webp"), "rb") as f:
            return "data:image/webp;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return ""


_VASETTI = _immagine_vasetti()

_ICO_FOGLIA = ("<svg width='13' height='13' viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='2.2' stroke-linecap='round'>"
               "<path d='M5 19C5 10 10 5 20 4c0 10-5 15-14 15z'/><path d='M5 19l8-8'/></svg>")
_ICO_AVVISO = ("<svg width='13' height='13' viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='2.4' stroke-linecap='round' "
               "stroke-linejoin='round'><path d='M12 3 2 20h20z'/><path d='M12 10v4'/><path d='M12 17h.01'/></svg>")


def kpi_html(prodotti, arancioni, rossi, scaduti):
    """I quattro contatori in cima alla pagina: carte piccole, sempre affiancate, con icone disegnate."""
    def carta(classe, etichetta, numero, icona=""):
        return (f"<div class='kpi {classe}'><div class='kpi-et'>{html.escape(etichetta)}</div>"
                f"<div class='kpi-n'>{numero}</div><span class='kpi-ico'>{icona}</span></div>")
    return ("<div class='kpi-griglia'>"
            + carta("kpi-ok", t("Prodotti"), prodotti, _ICO_FOGLIA)
            + carta("kpi-arancio", t("Entro 2 mesi"), arancioni)
            + carta("kpi-rosso", t("Entro 1 mese"), rossi)
            + carta("kpi-scuro", t("Scaduti"), scaduti, _ICO_AVVISO)
            + "</div>")


_CSS_VETRO_1 = """
/* ===== grafica vetro menta - passo 1: banner e contatori ===== */
.hero,.hero *,.kpi,.kpi *{box-sizing:border-box}
.hero{position:relative !important;overflow:visible !important;display:flex !important;flex-direction:row !important;align-items:center !important;
 justify-content:flex-start !important;gap:10px !important;min-height:112px !important;height:112px;padding:0 0 0 12px !important;border-radius:28px !important;
 background:linear-gradient(100deg,#0D7253 0%,#2A9C80 50%,#61C0B2 100%) !important;border:1px solid rgba(255,255,255,.4) !important;
 box-shadow:0 12px 32px rgba(16,41,63,.18) !important;margin:6px 0 12px !important}
.hero::before{content:"";position:absolute;left:30%;top:-12px;width:160px;height:80px;border-radius:50%;background:rgba(255,255,255,.22);
 filter:blur(26px);pointer-events:none}
.hero::after{content:"";position:absolute;right:-4px;top:-8px;width:150px;height:102px;opacity:1 !important;pointer-events:none;
 background:__VASETTI_URL__ no-repeat right top/contain}
.hero-ico{flex:none;width:48px !important;height:48px !important;border-radius:50%;background:rgba(255,255,255,.22) !important;
 border:1px solid rgba(255,255,255,.45) !important;box-shadow:none !important;font-size:1rem}
.hero-ico svg{width:26px;height:26px}
.hero-testi{max-width:200px !important;display:flex;flex-direction:column;gap:4px}
.hero h1{margin:0 !important;font-size:17px !important;line-height:1.1 !important;font-weight:800 !important;letter-spacing:-.3px;white-space:nowrap;color:#fff;padding:0 !important}
.hero p{margin:0 !important;font-size:11px !important;line-height:1.35 !important;font-weight:500 !important;opacity:.95;max-width:150px;color:#fff}

.kpi-griglia{display:grid !important;grid-template-columns:repeat(4,minmax(0,1fr)) !important;gap:8px !important;margin:0 0 12px !important}
.kpi{border-radius:22px !important;padding:9px 7px 9px 9px !important;min-height:72px !important;height:72px;border:1px solid rgba(255,255,255,.8) !important;
 box-shadow:0 12px 32px rgba(16,41,63,.12) !important;overflow:visible}
.kpi-et{font-size:10px !important;font-weight:600 !important;letter-spacing:-.2px;white-space:nowrap;color:#10293F}
.kpi-n{font-size:28px !important;font-weight:800 !important;line-height:1.05 !important;margin-top:0 !important;letter-spacing:0}
.kpi-ico{right:8px !important;bottom:8px !important;width:24px !important;height:24px !important;font-size:0 !important}
.kpi-ok{background:#E5F1E6 !important}.kpi-ok .kpi-n{color:#1E5A45}
.kpi-ok .kpi-ico{background:linear-gradient(135deg,#5CC78A,#2E9E63) !important;box-shadow:0 3px 8px rgba(46,158,99,.35) !important}
.kpi-arancio{background:#FDEBD7 !important}.kpi-arancio .kpi-et{color:#7A4A1A}.kpi-arancio .kpi-n{color:#E8811E}
.kpi-arancio .kpi-ico{background:radial-gradient(circle at 35% 30%,#FFD9A0,#F29B3A) !important;border:1px solid rgba(232,129,30,.5);box-shadow:none !important}
.kpi-rosso{background:#FAE5E2 !important}.kpi-rosso .kpi-et{color:#8A2E2E}.kpi-rosso .kpi-n{color:#D93636}
.kpi-rosso .kpi-ico{background:radial-gradient(circle at 35% 30%,#FFB3B5,#E8545A) !important;border:1px solid rgba(217,54,54,.45);box-shadow:none !important}
.kpi-scuro{background:#10293F !important;border-color:rgba(255,255,255,.15) !important;box-shadow:0 12px 32px rgba(16,41,63,.22) !important}
.kpi-scuro .kpi-et,.kpi-scuro .kpi-n{color:#fff}
.kpi-scuro .kpi-ico{background:#E47678 !important;box-shadow:none !important}
@media (max-width:480px){.hero h1{font-size:17px !important}.hero-ico{width:48px !important;height:48px !important}.hero::after{opacity:1 !important;background-size:contain !important}}
</style>"""

CSS = CSS.replace("</style>", _CSS_VETRO_1.replace("__VASETTI_URL__", ('url("' + _VASETTI + '")') if _VASETTI else "none"))

if lingua() in LINGUE_DA_DESTRA or lingua() == "ar":
    CSS = CSS.replace("</style>", """
.hero{padding:0 12px 0 0 !important}
.hero::after{right:auto;left:-4px;background-position:left top;transform:scaleX(-1)}
.kpi{padding:9px 9px 9px 7px !important}.kpi-ico{right:auto !important;left:8px !important}
</style>""")
