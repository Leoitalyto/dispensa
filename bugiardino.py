# -*- coding: utf-8 -*-
"""1) Ingredienti sempre nella lingua scelta (si riconosce la lingua del testo e, se e' diversa, si traduce).
2) Tre tasti sulla scheda del prodotto: 'Ingredienti' (rosso, sempre) che apre tutto il bugiardino da leggere;
   'Vegano' e 'Vegetariano' (verdi) solo se il prodotto e' classificato cosi'.
Caricato da app_dispensa.py dopo modifica.py."""


# ---------------------------------------------------------------------
# Traduzione con riconoscimento della lingua
# ---------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def _traduci_rileva(testo, a):
    """Ritorna (testo tradotto, lingua riconosciuta). Se il servizio non risponde solleva un errore (non resta in cache)."""
    pezzi, rilevata = [], ""
    for pezzo in _spezza(testo, 1200):
        r = requests.get("https://translate.googleapis.com/translate_a/single", timeout=8, headers=UA,
                         params={"client": "gtx", "sl": "auto", "tl": a, "dt": "t", "q": pezzo})
        r.raise_for_status()
        j = r.json()
        pezzi.append("".join(x[0] for x in j[0] if x and x[0]))
        if not rilevata and len(j) > 2 and isinstance(j[2], str):
            rilevata = j[2].lower().split("-")[0]
    if not pezzi:
        raise RuntimeError("traduzione")
    return " ".join(pezzi), rilevata


def ingredienti_in_lingua(testo):
    """Il testo tradotto nella lingua dell'utente, oppure None se e' gia' nella sua lingua (o se non si riesce a tradurre)."""
    testo = (testo or "").strip()
    a = lingua()
    if not testo:
        return None
    fallite = st.session_state.setdefault("_trad_fallite", set())
    k = (hash(testo), a)
    if k in fallite:
        return None
    try:
        tradotto, rilevata = _traduci_rileva(testo, a)
    except Exception:
        fallite.add(k)
        return None
    if rilevata == a or not tradotto.strip():
        return None
    return tradotto


def _con_ingredienti_tradotti(r):
    nuovo = ingredienti_in_lingua(r.get("ingredienti"))
    if nuovo is None:
        return r
    r2 = dict(r)
    r2["ingredienti"] = nuovo
    extra = dict(r.get("extra") or {})
    extra["ingredienti_tradotti"] = True
    r2["extra"] = extra
    return r2


# gli ingredienti letti da Open Food Facts vengono salvati gia' tradotti
_interpreta_prima_bug = interpreta_prodotto


def interpreta_prodotto(p, lang="it"):
    info = _interpreta_prima_bug(p, lang)
    try:
        info = _con_ingredienti_tradotti(info)
    except Exception:
        pass
    return info


# la composizione e il pannello dei dettagli mostrano sempre gli ingredienti tradotti
_composizione_prima_bug = composizione_html


def composizione_html(r, mie, evidenzia=None):
    return _composizione_prima_bug(_con_ingredienti_tradotti(r), mie, evidenzia)


_mostra_scheda_prima_bug = mostra_scheda


def mostra_scheda(p, mie, mostra_link=True):
    return _mostra_scheda_prima_bug(_con_ingredienti_tradotti(p), mie, mostra_link)


# ---------------------------------------------------------------------
# Il bugiardino: tutto sul prodotto da leggere
# ---------------------------------------------------------------------
_VOCI_NUTRIENTI = [("energia_kcal", "Energia (kcal)"), ("grassi", "Grassi (g)"), ("saturi", "di cui saturi (g)"),
                   ("carboidrati", "Carboidrati (g)"), ("zuccheri", "di cui zuccheri (g)"), ("fibre", "Fibre (g)"),
                   ("proteine", "Proteine (g)"), ("sale", "Sale (g)")]


def _extra_bugiardino(r):
    extra = r.get("extra") or {}
    pezzi = []
    n = extra.get("nutrienti") or {}
    if n:
        righe = "".join(f"<tr><td>{html.escape(t(nome))}</td><td>{html.escape(fmt_num(n[k]))}</td></tr>"
                        for k, nome in _VOCI_NUTRIENTI if k in n)
        pezzi.append(f"<div class='comp-sez'>📊 {html.escape(t('Valori nutrizionali'))} · {html.escape(t('Per 100 g'))}</div>"
                     f"<table class='bug-tab'>{righe}</table>")
    gradi = []
    if extra.get("nutriscore"):
        gradi.append(f"Nutri-Score {str(extra['nutriscore']).upper()}")
    if extra.get("ecoscore"):
        gradi.append(f"Eco-Score {str(extra['ecoscore']).upper()}")
    if extra.get("nova"):
        gradi.append(f"NOVA {extra['nova']}")
    righe = []
    if gradi:
        righe.append(" · ".join(gradi))
    if r.get("categoria"):
        righe.append(f"<b>{html.escape(t('Categoria'))}:</b> {_md_sicuro(r['categoria'])}")
    if any(extra.get(k, "?") != "?" for k in ("vegano", "vegetariano", "olio_palma")):
        righe.append(f"<b>{html.escape(t('Vegano'))}:</b> {html.escape(sino(extra.get('vegano')))} · "
                     f"<b>{html.escape(t('Vegetariano'))}:</b> {html.escape(sino(extra.get('vegetariano')))} · "
                     f"<b>{html.escape(t('Olio di palma'))}:</b> {html.escape(sino(extra.get('olio_palma')))}")
    if extra.get("origine"):
        righe.append(f"<b>{html.escape(t('Provenienza'))}:</b> {_md_sicuro(extra['origine'])}")
    if extra.get("additivi") is not None:
        righe.append(f"<b>{html.escape(t('Additivi'))}:</b> {html.escape(str(extra['additivi']))}")
    if r.get("note"):
        righe.append(f"📝 {_md_sicuro(r['note'])}")
    if righe:
        pezzi.append(f"<div class='comp-sez'>ℹ️ {html.escape(t('Altre informazioni'))}</div>"
                     "<div class='comp-ingr'>" + "<br>".join(righe) + "</div>")
        if extra.get("vegano") == "si" or extra.get("vegetariano") == "si":
            pezzi.append(f"<div class='nota'>{html.escape(t('Classificazione automatica dagli ingredienti: controlla sempre l’etichetta.'))}</div>")
    return "".join(pezzi)


def bugiardino_html(r, mie):
    h = composizione_html(r, mie)
    h = h.replace(html.escape(t("Composizione del prodotto")), html.escape(t("Bugiardino del prodotto")), 1)
    extra = _extra_bugiardino(r)
    punto = h.find("<div class='nota'>")
    return h[:punto] + extra + h[punto:] if punto >= 0 else h + extra


def _tasto_bugiardino(r, mie, classe, etichetta):
    pannello = ("<div class='allerg-pannello'>" + bugiardino_html(r, mie)
                + f"<div class='allerg-chiudi'>{html.escape(t('Tocca ✕ per chiudere'))}</div></div>")
    return (f"<details class='allerg tasto-bug'><summary class='allerg-btn {classe}'>{html.escape(etichetta)}</summary>"
            f"{pannello}</details>")


_scheda_html_prima_bug = scheda_html


def scheda_html(r, data_oggi, mie):
    h = _scheda_html_prima_bug(r, data_oggi, mie)
    extra = r.get("extra") or {}
    veg = ""
    if extra.get("vegano") == "si":
        veg += _tasto_bugiardino(r, mie, "veg", t("Vegano"))
    if extra.get("vegetariano") == "si":
        veg += _tasto_bugiardino(r, mie, "vegt", t("Vegetariano"))
    if veg:
        h = re.sub(r"(<div class='quantita'>.*?</div>)", lambda m: f"<div class='riga-qv'>{m.group(1)}{veg}</div>", h, count=1, flags=re.S)
    ingr = f"<span class='ingr-posto'>{_tasto_bugiardino(r, mie, 'ingr', t('Ingredienti'))}</span>"
    return h.replace("<div class='riga-data'>", "<div class='riga-data'>" + ingr, 1)


CSS = CSS.replace("</style>", """
.riga-qv{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}
.riga-data .ingr-posto{order:99;margin-left:auto}
.allerg-btn.ingr,.allerg-btn.veg,.allerg-btn.vegt{color:#fff;text-shadow:0 1px 0 rgba(0,0,0,.45)}
.allerg-btn.ingr::after,.allerg-btn.veg::after,.allerg-btn.vegt::after{content:""}
.allerg-btn.ingr{background:linear-gradient(#ff8a80,#e53935 50%,#b71c1c);border-color:#4a0000;
 box-shadow:0 3px 0 #6d0000,0 6px 10px rgba(0,0,0,.25),inset 0 2px 2px rgba(255,255,255,.5);text-transform:lowercase}
.allerg-btn.veg{background:linear-gradient(#d4fc79,#7ed321 50%,#4a9d0a);border-color:#1b3d00;
 box-shadow:0 3px 0 #2f6a00,0 6px 10px rgba(0,0,0,.25),inset 0 2px 2px rgba(255,255,255,.6)}
.allerg-btn.vegt{background:linear-gradient(#b7cf6a,#6f8f1f 50%,#44601a);border-color:#1b2a00;
 box-shadow:0 3px 0 #2c4010,0 6px 10px rgba(0,0,0,.25),inset 0 2px 2px rgba(255,255,255,.4)}
details.tasto-bug[open]>.allerg-pannello{border-top-color:#2e7d32}
.tasto-bug .comp-ingr mark.ev{background:linear-gradient(transparent 30%,#ffe066 30%)}
.bug-tab{width:100%;border-collapse:collapse;font-weight:700;margin:2px 0 6px}
.bug-tab td{padding:5px 8px;border-bottom:1px solid #e3efe7}
.bug-tab td:last-child{text-align:right;white-space:nowrap}
</style>""")
