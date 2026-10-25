# -*- coding: utf-8 -*-
"""Offerte dei volantini: archivio condiviso (offerte.json), ricerca, importazione dei PDF e inserimento a mano.
Solo italiano. Caricato da app_dispensa.py dopo volantini.py."""

from datetime import timedelta

FILE_OFFERTE = "offerte.json"
_STOP = {"con", "per", "gusti", "vari", "varie", "tipi", "formati", "formato", "della", "dello", "delle", "degli", "una", "uno",
         "nei", "sul", "alla", "non", "dei", "del", "gli", "the", "esempio", "circa", "confezione", "pezzi", "pezzo", "naturale"}


def _norm(txt):
    s = unicodedata.normalize("NFKD", txt or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _tokens(txt):
    return [w for w in _norm(txt).split() if len(w) > 2 and w not in _STOP and not w.isdigit()]


def carica_offerte():
    return carica_dati(crea_archivio(), FILE_OFFERTE)


def salva_offerte(fn, messaggio):
    salva_file(FILE_OFFERTE, fn, messaggio)


def _d(iso):
    try:
        return date.fromisoformat(iso) if iso else None
    except Exception:
        return None


def _citta_ok(o, citta):
    if not citta or citta == "Tutte":
        return True
    elenco = [c.strip().lower() for c in (o.get("citta") or "").split(",") if c.strip()]
    return (not elenco) or citta.strip().lower() in elenco


def _valida_oggi(o, oggi):
    dal, al = _d(o.get("dal")), _d(o.get("al"))
    return not ((al and al < oggi) or (dal and dal > oggi))


def _sconto(o):
    if o.get("prezzo_prima") and o.get("prezzo") and o["prezzo_prima"] > o["prezzo"]:
        return round(100 * (1 - o["prezzo"] / o["prezzo_prima"]))
    return 0


def _eur(v):
    return f"{float(v):.2f}".replace(".", ",") + " €" if v else ""


def trova_corrispondenze(r, offerte, minimo=0.5):
    """Le offerte che sembrano proprio il prodotto della scheda (confronto sulle parole di nome e marca)."""
    nome_t, marca_t = set(_tokens(r.get("nome", ""))), set(_tokens(r.get("marca", "")))
    base = nome_t | marca_t
    if not base:
        return []
    ris = []
    for o in offerte:
        ot = set(_tokens(o.get("nome", "") + " " + o.get("dettaglio", "")))
        comuni = base & ot
        if not comuni or not ot:
            continue
        p = len(comuni) / min(len(base), len(ot)) + (0.25 if marca_t & ot else 0)
        if p >= minimo and (len(comuni) >= 2 or len(base) <= 2 or (marca_t & ot)):
            ris.append((p, o))
    ris.sort(key=lambda x: (-x[0], x[1].get("prezzo", 0)))
    return [o for _, o in ris]


def trova_simili(r, offerte, quante=6):
    """Offerte dello stesso tipo di prodotto (o con una parola in comune), dalle piu' convenienti."""
    cat = indovina_categoria((r.get("nome", "") + " " + r.get("categoria", "")))
    base = set(_tokens(r.get("nome", "")))
    ris = [o for o in offerte if (cat != "Altro" and o.get("categoria") == cat) or (base & set(_tokens(o.get("nome", ""))))]
    ris.sort(key=lambda o: o.get("prezzo", 0))
    return ris[:quante]


def _citta_default():
    try:
        return carica_dati(crea_archivio(), st.session_state["percorso"]).get("citta_volantini", "")
    except Exception:
        return ""


def _periodo(o):
    d1, d2 = _d(o.get("dal")), _d(o.get("al"))
    if d1 and d2:
        return f"{d1:%d/%m}–{d2:%d/%m}"
    return f"fino al {d2:%d/%m}" if d2 else ""


def _riga_offerta(o):
    pezzi = [o.get("negozio", ""), o.get("citta", "")]
    if o.get("al"):
        d = _d(o["al"])
        pezzi.append("fino al " + (d.strftime("%d/%m") if d else o["al"]))
    return f"**{o.get('nome', '')}** {o.get('formato', '')} · **{_eur(o.get('prezzo'))}** · " + " · ".join(p for p in pezzi if p)


def aggiungi_offerte_alla_spesa(offerte_scelte, citta_pref=""):
    """Mette le offerte nella lista della spesa con negozio, citta' e prezzo."""
    esiti = {"nuove": 0, "gia": 0}

    def _fn(d):
        for o in offerte_scelte:
            citta = (o.get("citta") or citta_pref or "").split(",")[0].strip()
            r = {"nome": o.get("nome", ""), "marca": "", "barcode": "", "per_chi": "adulti"}
            ok = _aggiungi_offerta(d, r, o.get("negozio", ""), o.get("tipo", ""), citta, o.get("prezzo"), _d(o.get("al")))
            esiti["nuove" if ok else "gia"] += 1
    salva(_fn, "Spesa: offerte dai volantini")
    return esiti


# ---------------------------------------------------------------------
# la scheda "Offerte"
# ---------------------------------------------------------------------
def _scheda_cerca():
    oggi = date.today()
    dati_o = carica_offerte()
    tutte = list(dati_o.get("offerte", []))
    if not tutte:
        st.info("Non ci sono ancora offerte. Importa un volantino (scheda **📥 Importa**) o aggiungi un'offerta a mano.")
        return
    citta_note = sorted({c.strip() for o in tutte for c in (o.get("citta") or "").split(",") if c.strip()})
    pref = _citta_default()
    opzioni = ["Tutte"] + citta_note
    c1, c2 = st.columns(2)
    citta = c1.selectbox("📍 Città", opzioni, index=opzioni.index(pref) if pref in opzioni else 0, key="off_citta")
    testo = c2.text_input("🔎 Cerca", placeholder="prodotto, marca o tipo (es. pasta, birra)", key="off_testo").strip()
    f1, f2 = st.columns(2)
    negozi = sorted({o.get("negozio", "") for o in tutte if o.get("negozio")})
    cats = sorted({o.get("categoria", "Altro") for o in tutte})
    neg_sel = f1.multiselect("🏪 Negozio", negozi, key="off_neg")
    cat_sel = f2.multiselect("🧺 Tipo di prodotto", cats, key="off_cat")
    g1, g2 = st.columns(2)
    solo_iniziate = g1.checkbox("Solo quelle già iniziate", value=False, key="off_iniziate")
    mostra_scadute = g2.checkbox("Mostra anche le scadute", value=False, key="off_scadute")
    ordine = st.selectbox("Ordina per", ["Prezzo più basso", "Sconto maggiore", "Scadenza più vicina", "Negozio"], key="off_ord")

    chiavi = _tokens(testo)
    ris = []
    for o in tutte:
        if not _citta_ok(o, citta):
            continue
        al_o, dal_o = _d(o.get("al")), _d(o.get("dal"))
        if not mostra_scadute and al_o and al_o < oggi:
            continue
        if solo_iniziate and dal_o and dal_o > oggi:
            continue
        if neg_sel and o.get("negozio") not in neg_sel:
            continue
        if cat_sel and o.get("categoria", "Altro") not in cat_sel:
            continue
        if chiavi:
            pagliaio = _norm(" ".join([o.get("nome", ""), o.get("dettaglio", ""), o.get("categoria", ""), o.get("negozio", "")]))
            if not all(k in pagliaio for k in chiavi):
                continue
        ris.append(o)
    if ordine == "Sconto maggiore":
        ris.sort(key=lambda o: -_sconto(o))
    elif ordine == "Scadenza più vicina":
        ris.sort(key=lambda o: o.get("al") or "9999")
    elif ordine == "Negozio":
        ris.sort(key=lambda o: (o.get("negozio", ""), o.get("prezzo", 0)))
    else:
        ris.sort(key=lambda o: o.get("prezzo", 0))
    st.caption(f"{len(ris)} offerte" + (" (mostro le prime 150)" if len(ris) > 150 else ""))
    if not ris:
        st.info("Nessuna offerta con questi filtri. Prova a togliere un filtro o a cercare una parola più corta.")
        return
    ris = ris[:150]
    df = pd.DataFrame([{"id": o["id"], "🛒": False, "Prodotto": (o.get("nome", "") + (" · " + o["formato"] if o.get("formato") else "")),
                        "Prezzo": _eur(o.get("prezzo")), "Prima": _eur(o.get("prezzo_prima")), "Sconto": (f"-{_sconto(o)}%" if _sconto(o) else ""),
                        "Negozio": o.get("negozio", ""), "Città": o.get("citta", ""),
                        "Valida": _periodo(o)} for o in ris]).set_index("id")
    mod = st.data_editor(df, hide_index=True, width="stretch", key=f"off_tab_{len(ris)}_{citta}_{testo}_{ordine}",
                         disabled=[c for c in df.columns if c != "🛒"],
                         column_config={"🛒": st.column_config.CheckboxColumn("🛒", width="small", help="Spunta per aggiungere alla lista della spesa")})
    scelte = [o for o in ris if bool(mod.loc[o["id"], "🛒"])]
    if st.button(f"🛒 Aggiungi alla lista della spesa ({len(scelte)})", type="primary", disabled=not scelte, key="off_aggiungi", width="stretch"):
        try:
            e = aggiungi_offerte_alla_spesa(scelte, "" if citta == "Tutte" else citta)
            msg = f"🛒 {e['nuove']} prodotti messi nella lista della spesa" + (f" ({e['gia']} c'erano già)" if e["gia"] else "") + "."
            st.session_state["messaggio"] = msg
            st.rerun()
        except Exception as ex:
            st.error(t("Non sono riuscito a salvare: {e}", e=ex))

    # offerte sui prodotti che hai in lista
    try:
        lista = [x for x in carica_dati(crea_archivio(), st.session_state["percorso"]).get("spesa", []) if not x.get("preso") and not x.get("negozio")]
        validi = [o for o in tutte if _citta_ok(o, citta) and _valida_oggi(o, oggi)]
        trovati = [(x, trova_corrispondenze(x, validi)[:1]) for x in lista]
        trovati = [(x, m[0]) for x, m in trovati if m]
        if trovati:
            st.markdown("**🔔 In offerta tra i prodotti della tua lista**")
            for x, o in trovati[:8]:
                st.markdown(f"- {x.get('nome', '')} → " + _riga_offerta(o))
    except Exception:
        pass


def _leggi_e_mostra_import():
    """Mostra il risultato della lettura del PDF da controllare e salvare."""
    ris = st.session_state.get("imp_ris")
    if not ris:
        return
    giro = st.session_state.get("imp_giro", 0)
    for a in ris.get("avvisi", []):
        st.warning(a)
    st.success(f"Ho letto {ris['pagine']} pagine e trovato {len(ris['offerte'])} prodotti con prezzo. **Controllali prima di salvare**: "
               "i volantini sono impaginati in tanti modi e qualche nome o prezzo può essere sbagliato.")
    chain_tutte = [x for lst in CATENE.values() for x in lst]
    det = ris.get("negozio") or ""
    elenco = chain_tutte + ["Altro (scrivo il nome)"]
    c1, c2 = st.columns(2)
    scelta = c1.selectbox("🏪 Negozio", elenco, index=elenco.index(det) if det in elenco else 0, key=f"imp_neg_{giro}")
    negozio = c1.text_input("Nome del negozio", key=f"imp_neg_altro_{giro}").strip() if scelta.startswith("Altro") else scelta
    tipo_def = ris.get("tipo") or next((k for k, v in CATENE.items() if negozio in v), "Supermercato")
    tipi = list(CATENE)
    tipo = c2.selectbox("Tipo", tipi, index=tipi.index(tipo_def) if tipo_def in tipi else 0, key=f"imp_tipo_{giro}")
    citta = st.text_input("📍 Città o zona dove vale (più città: separale con la virgola)", value=_citta_default(), key=f"imp_citta_{giro}").strip()
    d1, d2 = st.columns(2)
    dal = d1.date_input("Valido dal", value=_d(ris.get("dal")) or date.today(), format="DD/MM/YYYY", key=f"imp_dal_{giro}")
    al = d2.date_input("Valido fino al", value=_d(ris.get("al")) or date.today() + timedelta(days=7), format="DD/MM/YYYY", key=f"imp_al_{giro}")
    cats = [c for c, _ in _CATEGORIE] + ["Altro"]
    df = pd.DataFrame([{"Includi": True, "Prodotto": o["nome"], "Formato": o.get("formato", ""), "Categoria": o.get("categoria", "Altro"),
                        "Prezzo": float(o["prezzo"]), "Prima": float(o["prezzo_prima"]) if o.get("prezzo_prima") else 0.0,
                        "Dettaglio": o.get("dettaglio", "")} for o in ris["offerte"]])
    mod = st.data_editor(df, hide_index=True, width="stretch", num_rows="dynamic", key=f"imp_tab_{giro}",
                         column_config={"Includi": st.column_config.CheckboxColumn("✔", width="small", default=True),
                                        "Categoria": st.column_config.SelectboxColumn("Tipo", options=cats, default="Altro"),
                                        "Prezzo": st.column_config.NumberColumn("Prezzo €", min_value=0.0, step=0.01, format="%.2f"),
                                        "Prima": st.column_config.NumberColumn("Prima €", min_value=0.0, step=0.01, format="%.2f")})
    buone = [r for _, r in mod.iterrows() if r.get("Includi") is not False and str(r.get("Prodotto") or "").strip() and (r.get("Prezzo") or 0) > 0]
    b1, b2 = st.columns(2)
    if b1.button(f"💾 Salva {len(buone)} offerte", type="primary", key=f"imp_salva_{giro}", width="stretch", disabled=not buone):
        if not negozio:
            st.error("Scrivi il nome del negozio.")
        elif not citta:
            st.error("Scrivi la città o la zona dove vale il volantino.")
        elif al < dal:
            st.error("La data di fine è prima di quella di inizio.")
        else:
            lista = [{"nome": str(r["Prodotto"]).strip(), "formato": str(r.get("Formato") or "").strip(), "categoria": r.get("Categoria") or "Altro",
                      "prezzo": float(r["Prezzo"]), "prezzo_prima": float(r["Prima"]) if (r.get("Prima") or 0) > 0 else None,
                      "dettaglio": str(r.get("Dettaglio") or "")} for r in buone]
            esito = {}
            try:
                salva_offerte(lambda d: esito.update(n=registra_volantino(d, lista, negozio, tipo, citta, dal.isoformat(), al.isoformat(),
                                                                         ris.get("fonte", ""), globals().get("utente", ""))), f"Volantino {negozio} {citta}")
                salva(lambda d: d.__setitem__("citta_volantini", citta.split(",")[0].strip()), "Città volantini")
                st.session_state.pop("imp_ris", None)
                st.session_state["imp_giro"] = giro + 1
                st.session_state["messaggio"] = f"✅ Salvate {esito.get('n', 0)} offerte di {negozio} ({citta})."
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))
    if b2.button("Annulla", key=f"imp_annulla_{giro}", width="stretch"):
        st.session_state.pop("imp_ris", None)
        st.session_state["imp_giro"] = giro + 1
        st.rerun()


def _scheda_importa():
    st.markdown("Carica il **PDF del volantino** (lo scarichi dal sito o dall'app del supermercato) oppure incolla il **link**. "
                "L'app legge prodotti e prezzi e te li fa controllare prima di salvarli per tutti.")
    giro = st.session_state.get("imp_giro", 0)
    modo = st.radio("Da dove?", ["📄 Carico il PDF", "🔗 Incollo il link"], horizontal=True, key=f"imp_modo_{giro}", label_visibility="collapsed")
    dati_pdf, fonte = None, ""
    if modo.startswith("📄"):
        f = st.file_uploader("Volantino in PDF", type=["pdf"], key=f"imp_file_{giro}")
        if f is not None:
            dati_pdf, fonte = f.getvalue(), f.name
    else:
        url = st.text_input("Link del volantino (PDF, oppure la pagina che lo contiene)", key=f"imp_url_{giro}", placeholder="https://…").strip()
        fonte = url
    if st.button("🔎 Leggi il volantino", type="primary", key=f"imp_leggi_{giro}", width="stretch",
                 disabled=(dati_pdf is None and not fonte)):
        try:
            with st.spinner("Sto leggendo il volantino…"):
                if dati_pdf is None:
                    dati_pdf, fonte = leggi_fonte(fonte)
                ris = estrai_volantino(dati_pdf)
            ris["fonte"] = fonte
            st.session_state["imp_ris"] = ris
        except Exception as e:
            st.session_state.pop("imp_ris", None)
            st.error(f"Non riesco a leggere questo volantino: {e}")
    _leggi_e_mostra_import()


def _scheda_manuale():
    giro = st.session_state.setdefault("off_man_giro", 0)
    K = lambda n: f"offman_{giro}_{n}"
    prod = st.text_input("Prodotto *", key=K("p"), placeholder="es. Pasta Barilla spaghetti").strip()
    c1, c2 = st.columns(2)
    formato = c1.text_input("Formato", key=K("f"), placeholder="es. 500 g").strip()
    categoria = c2.selectbox("Tipo di prodotto", [c for c, _ in _CATEGORIE] + ["Altro"], index=len(_CATEGORIE), key=K("c"))
    c3, c4 = st.columns(2)
    prezzo = c3.number_input("💶 Prezzo in offerta *", min_value=0.0, step=0.05, format="%.2f", key=K("pz"))
    prima = c4.number_input("Prezzo prima (facoltativo)", min_value=0.0, step=0.05, format="%.2f", key=K("pr"))
    tipo = st.radio("Dove", list(CATENE), horizontal=True, key=K("t"), format_func=lambda x: ICONE_TIPO[x] + " " + x)
    scelta = st.selectbox("Nome del negozio", CATENE[tipo] + ["Altro (scrivo il nome)"], key=K("n"))
    negozio = st.text_input("Scrivi il nome del negozio", key=K("na")).strip() if scelta.startswith("Altro") else scelta
    citta = st.text_input("📍 Città", value=_citta_default(), key=K("ci")).strip()
    d1, d2 = st.columns(2)
    dal = d1.date_input("Valido dal", value=date.today(), format="DD/MM/YYYY", key=K("d1"))
    al = d2.date_input("Valido fino al", value=date.today() + timedelta(days=7), format="DD/MM/YYYY", key=K("d2"))
    if st.button("💾 Salva l'offerta", type="primary", key=K("ok"), width="stretch"):
        if not prod or prezzo <= 0 or not negozio or not citta:
            st.error("Servono prodotto, prezzo, negozio e città.")
        elif al < dal:
            st.error("La data di fine è prima di quella di inizio.")
        else:
            def _aggiungi(d):
                registra_offerta_manuale(d, {"nome": prod, "formato": formato, "categoria": categoria, "prezzo": prezzo, "prezzo_prima": prima or None},
                                         negozio, tipo, citta, dal.isoformat(), al.isoformat(), globals().get("utente", ""), oggi=date.today())
            try:
                salva_offerte(_aggiungi, f"Offerta {prod}")
                salva(lambda d: d.__setitem__("citta_volantini", citta.split(",")[0].strip()), "Città volantini")
                st.session_state["off_man_giro"] = giro + 1
                st.session_state["messaggio"] = f"✅ Offerta salvata: {prod} a {_eur(prezzo)} ({negozio}, {citta})."
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))


def _scheda_salvati():
    dati_o = carica_offerte()
    vol = sorted(dati_o.get("volantini", []), key=lambda v: v.get("al") or "", reverse=True)
    if not vol:
        st.info("Nessun volantino salvato.")
    admin = bool(globals().get("e_admin"))
    for v in vol:
        d1, d2 = _d(v.get("dal")), _d(v.get("al"))
        periodo = (d1.strftime("%d/%m") if d1 else "?") + " – " + (d2.strftime("%d/%m/%Y") if d2 else "?")
        scaduto = d2 is not None and d2 < date.today()
        c1, c2 = st.columns([5, 2])
        c1.markdown(f"{'⚫' if scaduto else '🟢'} **{v.get('negozio', '')}** · {v.get('citta', '')} · {periodo} · {v.get('n', 0)} offerte")
        if admin or v.get("importato_da") == globals().get("utente"):
            if c2.button("🗑️ Elimina", key=f"offdel_{v['id']}", width="stretch"):
                try:
                    salva_offerte(lambda d, vid=v["id"]: (d.__setitem__("offerte", [o for o in d.get("offerte", []) if o.get("volantino") != vid]),
                                                          d.__setitem__("volantini", [x for x in d.get("volantini", []) if x.get("id") != vid])), "Volantino eliminato")
                    st.rerun()
                except Exception as e:
                    st.error(t("Non sono riuscito a salvare: {e}", e=e))
    if vol and st.button("🧹 Togli i volantini scaduti", key="off_pulisci"):
        ieri = (date.today()).isoformat()
        salva_offerte(lambda d: (d.__setitem__("offerte", [o for o in d.get("offerte", []) if not o.get("al") or o["al"] >= ieri]),
                                 d.__setitem__("volantini", [x for x in d.get("volantini", []) if not x.get("al") or x["al"] >= ieri])), "Pulizia volantini")
        st.rerun()


def _scheda_fonti():
    """Indirizzi da cui aggiornare i volantini ogni settimana (a mano con un tocco, o in automatico con lo script)."""
    dati_o = carica_offerte()
    fonti = list(dati_o.get("fonti", []))
    st.markdown("Qui metti gli **indirizzi dei volantini** che vuoi tenere aggiornati (il link al PDF, o la pagina del supermercato che contiene "
                "il link al volantino). Con **Aggiorna ora** l'app li legge tutti. Per l'aggiornamento automatico ogni settimana vedi la guida.")
    ultimo = dati_o.get("ultimo_aggiornamento")
    if ultimo:
        st.caption("Ultimo aggiornamento: " + ultimo.replace("T", " "))
    for f in fonti:
        c1, c2 = st.columns([5, 2])
        c1.markdown(f"**{f.get('negozio', '')}** · {f.get('citta', '')}  \n<small>{html.escape(f.get('url', ''))}</small>", unsafe_allow_html=True)
        if c2.button("🗑️", key=f"fontedel_{f['id']}", width="stretch"):
            salva_offerte(lambda d, fid=f["id"]: d.__setitem__("fonti", [x for x in d.get("fonti", []) if x.get("id") != fid]), "Fonte tolta")
            st.rerun()
    with st.expander("➕ Aggiungi un indirizzo", expanded=not fonti):
        scelta = st.selectbox("Negozio", [x for lst in CATENE.values() for x in lst] + ["Altro (scrivo il nome)"], key="fonte_neg")
        negozio = st.text_input("Scrivi il nome del negozio", key="fonte_neg_a").strip() if scelta.startswith("Altro") else scelta
        citta = st.text_input("📍 Città o zona", value=_citta_default(), key="fonte_citta").strip()
        url = st.text_input("Indirizzo (https://…)", key="fonte_url").strip()
        if st.button("Salva l'indirizzo", key="fonte_ok"):
            if not (negozio and citta and url.startswith("http")):
                st.error("Servono negozio, città e un indirizzo che inizia con http.")
            else:
                tipo = next((k for k, v in CATENE.items() if negozio in v), "Supermercato")
                salva_offerte(lambda d: d.setdefault("fonti", []).append({"id": uuid.uuid4().hex[:8], "negozio": negozio, "tipo": tipo, "citta": citta, "url": url}), "Fonte volantini")
                st.rerun()
    if fonti and st.button("🔄 Aggiorna ora tutti i volantini", type="primary", key="fonti_aggiorna", width="stretch"):
        esiti = []
        for f in fonti:
            try:
                with st.spinner(f"{f['negozio']}…"):
                    pdf, url_pdf = leggi_fonte(f["url"])
                    ris = estrai_volantino(pdf)
                    dal, al = ris.get("dal"), ris.get("al")
                    if not (dal and al):
                        raise ValueError("non trovo le date di validità nel volantino: importalo a mano dalla scheda 📥")
                    esito = {}
                    salva_offerte(lambda d: esito.update(n=registra_volantino(d, ris["offerte"], f["negozio"], f["tipo"], f["citta"], dal, al, url_pdf,
                                                                              "aggiornamento")), "Aggiornamento " + f["negozio"])
                esiti.append(f"✅ {f['negozio']}: {esito.get('n', 0)} offerte (controlla nella scheda Volantini salvati)")
            except Exception as e:
                esiti.append(f"⚠️ {f['negozio']}: {e}")
        salva_offerte(lambda d: d.__setitem__("ultimo_aggiornamento", datetime.now().isoformat(timespec="seconds")), "Aggiornamento volantini")
        for e_ in esiti:
            st.write(e_)
        st.caption("Le offerte importate così non sono state controllate una per una: per i prezzi importanti verifica sul volantino.")


def mostra_offerte():
    st.subheader("🏷️ Offerte dei volantini")
    st.caption("Offerte di supermercati, ipermercati e discount della tua zona, raccolte da tutti. Controlla sempre il prezzo sul volantino o in negozio.")
    schede = st.tabs(["🔎 Cerca", "📥 Importa", "✍️ A mano", "🗂️ Salvati", "🔄 Fonti"])
    with schede[0]:
        _scheda_cerca()
    with schede[1]:
        _scheda_importa()
    with schede[2]:
        _scheda_manuale()
    with schede[3]:
        _scheda_salvati()
    with schede[4]:
        _scheda_fonti()
