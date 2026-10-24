# -*- coding: utf-8 -*-
"""Aggiunte: ingredienti tradotti nella lingua scelta, allergeni riconosciuti in piu' lingue,
avviso lampeggiante (sirena) con l'indicazione di a chi e' controindicato ogni allergene."""
import unicodedata

# ---------------------------------------------------------------------
# Allergeni: riconosco anche i nomi scritti in altre lingue (es. "es:frutos-secos")
# ---------------------------------------------------------------------
_SINONIMI = {
    "glutine": "glutine|gluten",
    "latte": "latte|leche|lait|milch|milk",
    "uova": "uova|huevos|huevo|oeufs|oeuf|eier|eggs|egg",
    "frutta a guscio": "frutta a guscio|frutos secos|frutos de cascara|fruits a coque|fruit a coque|schalenfruchte|nuts|tree nuts|noix|nueces|noci",
    "arachidi": "arachidi|cacahuetes|cacahuete|arachides|erdnusse|peanuts|mani",
    "soia": "soia|soja|soy|soya|soybeans",
    "pesce": "pesce|pescado|poisson|fisch|fish",
    "crostacei": "crostacei|crustaceos|crustaces|krebstiere|crustaceans",
    "molluschi": "molluschi|moluscos|mollusques|weichtiere|molluscs|mollusks",
    "sedano": "sedano|apio|celeri|sellerie|celery",
    "senape": "senape|mostaza|moutarde|senf|mustard",
    "sesamo": "sesamo|sesame|sesam|sesame seeds",
    "solfiti": "solfiti|sulfitos|sulfites|sulfite|sulphites|anidride solforosa e solfiti|dioxido de azufre y sulfitos",
    "lupini": "lupini|altramuces|lupin|lupinen",
}
SINONIMI_ALLERGENI = {p: it for it, parole in _SINONIMI.items() for p in parole.split("|")}


def _senza_accenti(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tag_in_italiano(tags):
    risultato = []
    for tag in tags or []:
        grezzo = tag.split(":", 1)[-1].lower()
        it = (ALLERGENI_OFF.get(grezzo) or SINONIMI_ALLERGENI.get(_senza_accenti(grezzo).replace("-", " "))
              or grezzo.replace("-", " "))
        if it not in risultato:
            risultato.append(it)
    return risultato


# ---------------------------------------------------------------------
# Traduzione automatica (servizi gratuiti: prima MyMemory, poi Google come riserva)
# ---------------------------------------------------------------------
def _spezza(testo, massimo=300):
    pezzi, corrente = [], ""
    for parte in re.split(r"(?<=[,.;:])\s+", testo):
        while len(parte) > massimo:                       # frase senza punteggiatura: taglio sugli spazi
            taglio = parte.rfind(" ", 0, massimo) or massimo
            if taglio <= 0:
                taglio = massimo
            if corrente:
                pezzi.append(corrente)
                corrente = ""
            pezzi.append(parte[:taglio].strip())
            parte = parte[taglio:].strip()
        if corrente and len(corrente) + len(parte) + 1 > massimo:
            pezzi.append(corrente)
            corrente = parte
        else:
            corrente = (corrente + " " + parte).strip()
    if corrente:
        pezzi.append(corrente)
    return [p for p in pezzi if p]


def _traduci_mymemory(testo, a, da):
    r = requests.get("https://api.mymemory.translated.net/get", timeout=10, headers=UA,
                     params={"q": testo, "langpair": f"{'Autodetect' if da == 'auto' else da}|{a}"})
    r.raise_for_status()
    j = r.json()
    risultato = (j.get("responseData") or {}).get("translatedText") or ""
    if not risultato or "MYMEMORY WARNING" in risultato.upper() or str(j.get("responseStatus")) != "200":
        raise RuntimeError("mymemory")
    return risultato


def _traduci_google(testo, a, da):
    r = requests.get("https://translate.googleapis.com/translate_a/single", timeout=10, headers=UA,
                     params={"client": "gtx", "sl": da, "tl": a, "dt": "t", "q": testo})
    r.raise_for_status()
    risultato = "".join(x[0] for x in r.json()[0] if x and x[0])
    if not risultato:
        raise RuntimeError("google")
    return risultato


@st.cache_data(ttl=86400, show_spinner=False)
def _traduci_con_cache(testo, a, da):
    """Se nessun servizio risponde solleva un errore (cosi' il risultato negativo non resta in cache)."""
    tradotti = []
    for pezzo in _spezza(testo):
        for servizio in (_traduci_mymemory, _traduci_google):
            try:
                tradotti.append(servizio(pezzo, a, da))
                break
            except Exception:
                continue
        else:
            raise RuntimeError("traduzione non riuscita")
    return " ".join(tradotti)


def traduci_testo(testo, a, da="auto"):
    """Testo tradotto in lingua 'a', oppure None se non e' possibile (si resta con l'originale)."""
    testo = (testo or "").strip()
    if not testo or a == da:
        return None
    try:
        return _traduci_con_cache(testo, a, da)
    except Exception:
        return None


def _codice_lingua(c):
    c = (c or "").lower()
    return c if re.fullmatch(r"[a-z]{2}", c) and c != "xx" else "auto"


CAMPI_OFF = CAMPI_OFF + ",lang"
_interpreta_base = interpreta_prodotto


def interpreta_prodotto(p, lang="it"):
    """Come prima, ma gli ingredienti (e categoria e paesi) vengono tradotti nella lingua scelta."""
    info = _interpreta_base(p, lang)
    extra = info["extra"]
    testo = (p.get("ingredients_text_" + lang) or "").strip()
    origine = lang
    if not testo:
        testo, origine = (p.get("ingredients_text") or "").strip(), _codice_lingua(p.get("lang"))
        if not testo:
            for altra in ("en", "it", "fr", "es", "de"):
                if (p.get("ingredients_text_" + altra) or "").strip():
                    testo, origine = p["ingredients_text_" + altra].strip(), altra
                    break
    if testo and origine != lang:
        tradotto = traduci_testo(testo, lang, origine)
        if tradotto:
            testo = tradotto
            extra["ingredienti_tradotti"] = True
    info["ingredienti"] = testo
    if lang != "en":                       # categorie e paesi arrivano di solito in inglese
        if info.get("categoria"):
            info["categoria"] = traduci_testo(info["categoria"], lang, "auto") or info["categoria"]
        for chiave in ("paesi", "origine"):
            if extra.get(chiave):
                extra[chiave] = traduci_testo(extra[chiave], lang, "en") or extra[chiave]
    return info


# ---------------------------------------------------------------------
# Allergeni: a chi sono controindicati + avviso lampeggiante
# ---------------------------------------------------------------------
CONTROINDICATO = {   # in italiano; le altre lingue sono nei file lingue*.py ("controindicato:<allergene>")
    "glutine": "celiaci e persone allergiche o sensibili al glutine",
    "latte": "allergici alle proteine del latte (gli intolleranti al lattosio possono avere disturbi)",
    "uova": "allergici alle uova",
    "frutta a guscio": "allergici alla frutta a guscio (noci, nocciole, mandorle, pistacchi...)",
    "arachidi": "allergici alle arachidi",
    "soia": "allergici alla soia",
    "pesce": "allergici al pesce",
    "crostacei": "allergici ai crostacei (gamberi, granchi, aragoste...)",
    "molluschi": "allergici ai molluschi (cozze, vongole, calamari...)",
    "sedano": "allergici al sedano",
    "senape": "allergici alla senape",
    "sesamo": "allergici al sesamo",
    "solfiti": "persone sensibili ai solfiti, in particolare chi soffre di asma",
    "lupini": "allergici ai lupini (possibile reazione anche in chi è allergico alle arachidi)",
}


def t_contro(nome):
    return TRADUZIONI.get(lingua(), {}).get("controindicato:" + nome, CONTROINDICATO.get(nome, ""))


def _riga_allergene(prefisso, a):
    return (f"<li>{html.escape(prefisso)} <b>{html.escape(t_all(a)).upper()}</b> — "
            f"{html.escape(t('controindicato per:'))} {html.escape(t_contro(a))}</li>")


def avviso_allergie_html(r, mie, completo=True):
    """Riquadro rosso lampeggiante per gli allergeni della persona; riquadro arancione per gli altri allergeni presenti."""
    allergeni = [a for a in (r.get("allergeni") or []) if a in CONTROINDICATO]
    tracce = [a for a in (r.get("tracce") or []) if a in CONTROINDICATO and a not in allergeni]
    miei = ([_riga_allergene(t("Contiene"), a) for a in allergeni if a in mie]
            + [_riga_allergene(t("Può contenere tracce di"), a) for a in tracce if a in mie])
    pezzi = []
    if miei:
        pezzi.append("<div class='allarme'><span class='sirena'>🚨</span> <b>"
                     + html.escape(t("ATTENZIONE: allergene che ti riguarda")) + "</b><ul>" + "".join(miei) + "</ul></div>")
    if completo:
        altri = ([_riga_allergene(t("Contiene"), a) for a in allergeni if a not in mie]
                 + [_riga_allergene(t("Può contenere tracce di"), a) for a in tracce if a not in mie])
        if altri or miei:
            corpo = ""
            if altri:
                corpo = ("<div class='allergeni-box'>⚠️ <b>" + html.escape(t("Allergeni presenti nel prodotto"))
                         + "</b><ul>" + "".join(altri) + "</ul></div>")
            pezzi.append(corpo + "<div class='nota'>" + html.escape(
                t("Informazione generale, non è un parere medico: per la tua situazione chiedi al medico.")) + "</div>")
    return "".join(pezzi)


CSS = CSS.replace("</style>", """
@keyframes sirena{0%,100%{box-shadow:0 0 0 0 rgba(211,47,47,.7)}50%{box-shadow:0 0 16px 6px rgba(211,47,47,.5)}}
@keyframes lampeggia{0%,49%{opacity:1}50%,100%{opacity:.2}}
.allarme{border:3px solid #d32f2f;background:#ffebee;color:#7f0000;border-radius:16px;padding:10px 14px;margin:8px 0;
 animation:sirena 1.4s ease-in-out infinite}
.allarme ul{margin:6px 0 0 0;padding-left:20px}
.allarme .sirena{display:inline-block;font-size:1.5rem;vertical-align:middle;animation:lampeggia 1.2s linear infinite}
.allergeni-box{border-left:8px solid #ef6c00;background:#fff3e0;color:#6a3100;border-radius:12px;padding:10px 14px;margin:8px 0}
.allergeni-box ul{margin:6px 0 0 0;padding-left:20px}
.scheda .allarme{font-size:.8rem;padding:8px 10px;margin:6px 0 0 0}
.scheda.allarme-card{border-top-color:#d32f2f}
@media (prefers-reduced-motion:reduce){.allarme,.allarme .sirena{animation:none}}
</style>""")


def scheda_html(r, data_oggi, mie):
    stato, giorni = stato_scadenza(r.get("scadenza"), data_oggi)
    colore = COLORI[stato]
    marca = f"<div class='marca'>{html.escape(r['marca'])}</div>" if r.get("marca") else ""
    data = f"<div class='data'>{data_it(r['scadenza'])}</div>" if r.get("scadenza") else ""
    nota = f"<div class='nota'>📝 {html.escape(r['note'])}</div>" if r.get("note") else ""
    allarme = avviso_allergie_html(r, mie, completo=False)
    classe = "scheda allarme-card" if allarme else "scheda"
    return (f"<div class='{classe}' style='--c:{colore}'><div class='foto'>{foto_html(r)}</div>"
            f"<div class='corpo'><div class='nome'>{html.escape(r.get('nome', ''))}</div>{marca}"
            f"<div class='quantita'>📦 {html.escape(descrivi([r]))}</div>"
            f"<span class='scadenza'>{ICONE[stato]} {testo_giorni(stato, giorni)}</span>{data}"
            f"<div>{badge_allergeni(r, mie)}</div>{allarme}{nota}</div></div>")


def mostra_scheda(p, mie, mostra_link=True):
    """Pannello con le informazioni di un prodotto: allergeni, valori nutrizionali, ingredienti, prezzi e collegamenti."""
    extra = p.get("extra") or {}
    c1, c2 = st.columns([1, 3])
    src = src_sicuro(p.get("immagine") or "")
    if src:
        c1.image(src, width=110)
    c2.markdown(f"**{p.get('nome', '')}**" + (f" · {p['marca']}" if p.get("marca") else ""))
    c2.caption(descrivi([p]) if p.get("quantita") else "")
    gradi = badge_grado("Nutri-Score", extra.get("nutriscore")) + badge_grado("Eco-Score", extra.get("ecoscore"))
    if extra.get("nova"):
        gradi += f"<span class='badge'>NOVA {extra['nova']}</span>"
    st.markdown(gradi + badge_allergeni(p, mie), unsafe_allow_html=True)
    st.markdown(avviso_allergie_html(p, mie), unsafe_allow_html=True)
    if not mie and (p.get("allergeni") or p.get("tracce")):
        st.caption(t("Per ricevere l'avviso lampeggiante, scegli le tue allergie nel menu a sinistra (tocca la freccia » in alto)."))

    n = extra.get("nutrienti") or {}
    if n:
        voci = [("energia_kcal", "Energia (kcal)"), ("grassi", "Grassi (g)"), ("saturi", "di cui saturi (g)"),
                ("carboidrati", "Carboidrati (g)"), ("zuccheri", "di cui zuccheri (g)"), ("fibre", "Fibre (g)"),
                ("proteine", "Proteine (g)"), ("sale", "Sale (g)")]
        st.dataframe(pd.DataFrame([{t("Valori nutrizionali"): t(nome), t("Per 100 g"): fmt_num(n[k])}
                                   for k, nome in voci if k in n]), hide_index=True)
    else:
        st.caption(t("Nessun dato nutrizionale disponibile."))

    righe = []
    categoria = p.get("categoria") or ""
    if categoria:
        righe.append(f"**{t('Categoria')}:** {categoria}")
    if any(extra.get(k, "?") != "?" for k in ("vegano", "vegetariano", "olio_palma")):
        righe.append(f"**{t('Vegano')}:** {sino(extra.get('vegano'))} · **{t('Vegetariano')}:** "
                     f"{sino(extra.get('vegetariano'))} · **{t('Olio di palma')}:** {sino(extra.get('olio_palma'))}")
    if extra.get("origine"):
        righe.append(f"**{t('Provenienza')}:** {extra['origine']}")
    if extra.get("paesi"):
        righe.append(f"**{t('Venduto in')}:** {extra['paesi']}")
    if extra.get("additivi") is not None:
        righe.append(f"**{t('Additivi')}:** {extra['additivi']}")
    if p.get("ingredienti"):
        righe.append(f"**{t('Ingredienti')}:** {p['ingredienti']}")
    if righe:
        st.markdown("\n\n".join(righe))
    if extra.get("ingredienti_tradotti") and p.get("ingredienti"):
        st.caption("🌐 " + t("Traduzione automatica: può contenere errori. Fa fede l'etichetta."))

    if mostra_link:
        if p.get("barcode"):
            prezzi = cerca_prezzi(p["barcode"])
            if prezzi:
                st.markdown(f"**💶 {t('Prezzi segnalati dalla community (Open Prices)')}**")
                for z in prezzi:
                    importo = f"{z['prezzo']:.2f}" if lingua() == "en" else f"{z['prezzo']:.2f}".replace(".", ",")
                    st.write(f"{importo} {z['valuta']} · {z['negozio'] or '—'} · {z['data']}")
            else:
                st.caption(t("Nessun prezzo segnalato."))
        st.markdown(f"**🔗 {t('Cerca online')}**")
        colonne = st.columns(2)
        for i, (etichetta, url) in enumerate(link_online(p.get("nome", ""), p.get("marca", ""), p.get("barcode", ""),
                                                           p.get("immagine", ""))):
            colonne[i % 2].link_button(etichetta, url, width="stretch")
        st.caption(t("I collegamenti aprono siti esterni: prezzi e recensioni non sono verificati da questa app."))
