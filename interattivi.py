# -*- coding: utf-8 -*-
"""Pulsanti degli allergeni interattivi (si apre la composizione del prodotto), avviso subito
all'inserimento e grafica moderna con sfondo colorato.
Questo file viene caricato da app_dispensa.py dopo categorie.py e prima di account.py."""


# ---------- testo sicuro dentro l'HTML (niente effetti strani del markdown) ----------
def _md_sicuro(testo):
    s = html.escape(str(testo or ""))
    for c, e in (("*", "&#42;"), ("_", "&#95;"), ("`", "&#96;"), ("[", "&#91;"), ("]", "&#93;"),
                 ("\\", "&#92;"), ("~", "&#126;")):
        s = s.replace(c, e)
    return s.replace("\r", "").replace("\n", "<br>")


def _maiuscola(s):
    return s[:1].upper() + s[1:]


# ---------- la schermata con la composizione del prodotto ----------
def composizione_html(r, mie, evidenzia=None):
    """Nome, allergeni (con a chi sono controindicati) e ingredienti del prodotto."""
    marca = f"<div class='comp-marca'>{_md_sicuro(r['marca'])}</div>" if r.get("marca") else ""
    voci = []
    for a, traccia in ([(x, False) for x in (r.get("allergeni") or [])]
                       + [(x, True) for x in (r.get("tracce") or []) if x not in (r.get("allergeni") or [])]):
        nome = _maiuscola(((t("tracce di") + " ") if traccia else "") + t_all(a))
        classe = ("sel " if a == evidenzia else "") + ("mio " if a in mie else "") + ("traccia" if traccia else "")
        contro = t_contro(a) if "t_contro" in globals() else ""
        contro = f"<span class='comp-contro'>{html.escape(t('controindicato per:'))} {html.escape(contro)}</span>" if contro else ""
        voci.append(f"<li class='{classe.strip()}'><b>{html.escape(nome)}</b>{contro}</li>")
    allergeni = (f"<div class='comp-sez'>⚠️ {t('Allergeni')}</div><ul class='comp-lista'>{''.join(voci)}</ul>"
                 if voci else "")
    ingr = (r.get("ingredienti") or "").strip()
    manca = t("Ingredienti non disponibili: controlla l'etichetta sulla confezione.")
    testo_ingr = _md_sicuro(ingr) if ingr else f"<i>{html.escape(manca)}</i>"
    auto = t("Traduzione automatica: può contenere errori. Fa fede l'etichetta.")
    tradotto = f"<div class='nota'>{html.escape(auto)}</div>" if (r.get("extra") or {}).get("ingredienti_tradotti") else ""
    fede = t("Fa fede sempre l'etichetta sulla confezione.")
    return ("<div class='comp'>"
            f"<div class='comp-titolo'>🥣 {html.escape(t('Composizione del prodotto'))}</div>"
            f"<div class='comp-nome'>{_md_sicuro(r.get('nome', ''))}</div>{marca}"
            f"{allergeni}"
            f"<div class='comp-sez'>🧾 {html.escape(t('Ingredienti'))}</div><div class='comp-ingr'>{testo_ingr}</div>"
            f"{tradotto}<div class='nota'>{html.escape(fede)}</div>"
            "</div>")


def _pulsante(r, mie, a, traccia):
    """Un pulsante giallo con il nome dell'allergene: toccandolo si apre la composizione."""
    mio = a in mie
    nome = t_all(a)
    if traccia:
        etichetta = t("tracce di") + " " + nome
    else:
        etichetta = (("⚠️ " + t("Contiene") + " ") if mio else "") + nome
    classe = "allerg-btn" + (" traccia" if traccia else "") + (" mio" if mio else "")
    pannello = ("<div class='allerg-pannello'>" + composizione_html(r, mie, a)
                + f"<div class='allerg-chiudi'>{html.escape(t('Tocca ✕ per chiudere'))}</div></div>")
    return (f"<details class='allerg'><summary class='{classe}'>{html.escape(_maiuscola(etichetta))}</summary>"
            f"{pannello}</details>")


def badge_allergeni(r, mie):
    """Etichette degli allergeni: ogni allergene e' un pulsante interattivo. Per gli animali niente etichette."""
    if categoria_di(r) == "animali":
        return ""
    pezzi = []
    allergeni, tracce = r.get("allergeni") or [], r.get("tracce") or []
    if not r.get("allergeni_noti") and not allergeni:
        pezzi.append(f"<span class='badge'>❔ {t('Allergeni non verificati')}</span>")
    for a in allergeni:
        pezzi.append(_pulsante(r, mie, a, False))
    for a in tracce:
        if a not in allergeni:
            pezzi.append(_pulsante(r, mie, a, True))
    if r.get("senza_glutine"):
        pezzi.append(f"<span class='badge bene'>🌾 {t('Senza glutine')}</span>")
    return "<div class='allerg-riga'>" + "".join(pezzi) + "</div>" if pezzi else ""


# ---------- avviso subito all'inserimento del prodotto ----------
def avviso_inserimento(info, per_chi, mie, chiave):
    """Dopo la lettura del codice: si apre una schermata con allergeni e composizione (una volta per prodotto)."""
    if per_chi == "animali":
        return
    if not ((info.get("allergeni") or []) or (info.get("tracce") or [])):
        return
    if st.session_state.get(chiave):
        return
    st.session_state[chiave] = True

    def _schermata():
        src = src_sicuro(info.get("immagine") or "")
        if src:
            st.image(src, width=110)
        st.markdown(composizione_html(info, mie), unsafe_allow_html=True)
        if st.button(t("Ho capito"), type="primary", width="stretch", key="chiudi_avviso_" + chiave):
            st.rerun()

    st.dialog("⚠️ " + t("Attenzione: questo prodotto può dare allergie"))(_schermata)()


# ---------- grafica: sfondo colorato, testi in grassetto, stile moderno e giovanile ----------
_GRANA = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
          "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/>"
          "<feColorMatrix values='0 0 0 0 .15  0 0 0 0 .45  0 0 0 0 .25  0 0 0 .28 0'/></filter>"
          "<rect width='100%' height='100%' filter='url(%23n)'/></svg>\")")

CSS = CSS.replace("</style>", """
.stApp{background:__GRANA__,
 radial-gradient(1100px 620px at 8% -8%,rgba(110,225,170,.65),transparent 62%),
 radial-gradient(900px 520px at 100% 4%,rgba(120,205,240,.55),transparent 58%),
 radial-gradient(900px 640px at 55% 112%,rgba(200,238,140,.65),transparent 62%),
 linear-gradient(180deg,#ecfbf2 0%,#dcf4e6 55%,#e7f8ee 100%) !important;background-attachment:fixed !important;color:#10261a}
[data-testid="stHeader"]{background:transparent !important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(255,255,255,.92),rgba(222,246,232,.95)) !important;
 border-right:2px solid rgba(0,137,123,.18)}
.stMarkdown p,.stMarkdown li,label p,[data-testid="stCaptionContainer"] p,[data-testid="stWidgetLabel"] p{font-weight:700 !important}
h1,h2,h3,h4{font-weight:800 !important;letter-spacing:-.01em}
button[data-baseweb="tab"] p{font-weight:800 !important}
button[data-baseweb="tab"][aria-selected="true"]{background:rgba(255,255,255,.75);border-radius:14px 14px 0 0}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{font-weight:800 !important;border-radius:999px !important;
 border:2px solid rgba(0,137,123,.45) !important;box-shadow:0 3px 0 rgba(0,100,90,.25)}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#00a98f,#0288d1) !important;color:#fff !important;border:0 !important}
[data-testid="stExpander"]{background:rgba(255,255,255,.8);border:2px solid rgba(0,137,123,.22) !important;border-radius:20px !important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:20px}
input,textarea,[data-baseweb="select"]>div{border-radius:14px !important;font-weight:700 !important}
.hero{background:linear-gradient(135deg,#00a86b 0%,#00a6a6 50%,#2f80ed 100%);border:2px solid rgba(255,255,255,.55)}
.hero h1{font-weight:900 !important}
.scheda{background:#fff !important;color:#10261a !important;box-shadow:0 8px 24px rgba(0,80,60,.16)}
.scheda .foto{background:linear-gradient(180deg,#fff,#f1fbf5)}
.scheda .nome{font-weight:800}
.scheda .marca,.scheda .quantita,.scheda .data{font-weight:700;opacity:.8}
.avviso{font-weight:700}
.allerg-riga{display:flex;flex-wrap:wrap;gap:6px 6px;margin-top:2px}
details.allerg{display:inline-block;margin:0;vertical-align:top}
details.allerg>summary{list-style:none;cursor:pointer;-webkit-tap-highlight-color:transparent;user-select:none;outline:none}
details.allerg>summary::-webkit-details-marker{display:none}
.allerg-btn{display:inline-block;padding:4px 15px 5px;border-radius:999px;font-weight:800;font-size:.95rem;line-height:1.25;color:#1b1400;
 background:linear-gradient(#fff59d 0%,#ffd91c 45%,#f9a825 100%);border:2px solid #2b2000;
 box-shadow:0 3px 0 #a87400,0 6px 10px rgba(0,0,0,.2),inset 0 2px 2px rgba(255,255,255,.9);text-shadow:0 1px 0 rgba(255,255,255,.6)}
.allerg-btn::after{content:" ⓘ";font-weight:800}
details.allerg:not([open])>summary:active{transform:translateY(2px)}
.allerg-btn.traccia{background:linear-gradient(#ffe9c7,#ffc266 55%,#fb9a1c);box-shadow:0 3px 0 #a85d00,0 6px 10px rgba(0,0,0,.2),inset 0 2px 2px rgba(255,255,255,.9)}
.allerg-btn.mio{color:#fff;background:linear-gradient(#ff8a80,#e53935 55%,#b71c1c);border-color:#4a0000;text-shadow:0 1px 0 rgba(0,0,0,.4);
 box-shadow:0 3px 0 #6d0000,0 6px 10px rgba(0,0,0,.25),inset 0 2px 2px rgba(255,255,255,.45);animation:sirena 1.4s ease-in-out infinite}
@keyframes apri{from{opacity:0;transform:translate(-50%,-46%) scale(.96)}to{opacity:1;transform:translate(-50%,-50%) scale(1)}}
details.allerg:not([open])>.allerg-pannello{display:none}
details.allerg[open]>summary::before{content:"";position:fixed;inset:0;background:rgba(9,40,25,.62);
 backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);z-index:1000000;cursor:pointer}
details.allerg[open]>summary::after{content:"✕";position:fixed;left:50%;bottom:max(18px,env(safe-area-inset-bottom));
 transform:translateX(-50%);width:54px;height:54px;line-height:50px;text-align:center;border-radius:50%;background:#fff;color:#b71c1c;
 font-size:1.6rem;font-weight:900;border:3px solid #b71c1c;box-shadow:0 6px 18px rgba(0,0,0,.35);z-index:1000003;text-shadow:none}
details.allerg[open]>.allerg-pannello{position:fixed;z-index:1000002;left:50%;top:46%;transform:translate(-50%,-50%);
 width:min(92vw,540px);max-height:70vh;overflow:auto;background:#fff;color:#10261a;border-radius:26px;
 border-top:10px solid #fbc02d;box-shadow:0 24px 60px rgba(0,0,0,.45);animation:apri .18s ease-out;text-align:start;font-weight:600}
.allerg-chiudi{text-align:center;opacity:.65;font-size:.8rem;font-weight:700;padding:0 14px 14px}
.comp{padding:16px 18px 8px 18px;color:#10261a}
.comp-titolo{font-weight:900;font-size:1.15rem}
.comp-nome{font-weight:800;font-size:1.05rem;margin-top:2px}
.comp-marca{font-weight:700;opacity:.7}
.comp-sez{font-weight:900;margin:14px 0 4px 0;padding:3px 10px;border-radius:10px;background:#e6f7ee;width:fit-content}
.comp-lista{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.comp-lista li{padding:8px 12px;border-radius:12px;background:#fff8e1;border-left:6px solid #fbc02d;font-weight:700}
.comp-lista li.traccia{background:#fff3e0;border-left-color:#fb8c00}
.comp-lista li.mio{background:#ffebee;border-left-color:#d32f2f;color:#7f0000}
.comp-lista li.sel{outline:3px solid #f9a825;box-shadow:0 4px 12px rgba(249,168,37,.45)}
.comp-contro{display:block;font-weight:600;font-size:.85rem;opacity:.85}
.comp-ingr{font-weight:700;line-height:1.45;padding:2px 4px}
@media (prefers-reduced-motion:reduce){.allerg-btn.mio,details.allerg[open]>.allerg-pannello{animation:none}}
</style>""".replace("__GRANA__", _GRANA))

if lingua() in LINGUE_DA_DESTRA or lingua() == "ar":
    CSS = CSS.replace("</style>", """
.comp-lista li{border-left:0;border-right:6px solid #fbc02d}
.comp-lista li.traccia{border-right-color:#fb8c00}
.comp-lista li.mio{border-right-color:#d32f2f}
.allerg-pannello,.comp{direction:rtl;text-align:right}
</style>""")
