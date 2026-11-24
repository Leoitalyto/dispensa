# =====================================================================================================================
# SPESA SMART · PESO E LITRI MANCANTI — richiesta del 22 novembre 2026: «ho inserito questo elemento ma se non appare il costo al kilo
# o litro non sarà mai possibile avere una lista della spesa davvero ottimizzata».
# Un prodotto senza formato (tipico dello scontrino: «SELEX FETTE BI») ha solo il prezzo a pezzo. Qui:
#  - avviso «⚖️ N prodotti senza peso o litri» in Dove costa meno, Riepilogo e Archivio prodotti;
#  - sotto ogni scheda senza peso: proposte automatiche (dal nome, es. «500g»; da Open Food Facts cercando nome e marca, gratis e
#    senza chiave) con un tocco, oppure peso/litri scritti a mano;
#  - salvando, ss_completa_formato ricalcola il prezzo al kg/litro di TUTTI i prezzi già inseriti di quel prodotto.
# =====================================================================================================================
import requests as _sf_req

_SF_URL = ("https://world.openfoodfacts.org/cgi/search.pl", "https://it.openfoodfacts.org/cgi/search.pl")


@st.cache_data(ttl=86400, show_spinner=False)
def sf_cerca_off(testo):
    """[(nome, marca, quantità «300 g», ean, (conf, valore, unità))] da Open Food Facts; [] se non trova o non risponde."""
    parole = [w for w in _ss_re.split(r"[^\wàèéìòù]+", str(testo or "").lower()) if len(w) >= 3]
    if not parole:
        return []
    out, visti = [], set()
    for url in _SF_URL:
        try:
            r = _sf_req.get(url, params={"search_terms": " ".join(parole[:6]), "search_simple": 1, "action": "process", "json": 1, "page_size": 12,
                                         "fields": "product_name,product_name_it,brands,quantity,code"},
                            headers={"User-Agent": "VitaMemo/5.3 (app di famiglia)"}, timeout=8)
            prodotti = (r.json() or {}).get("products") or []
        except Exception:
            continue
        for x in prodotti:
            q = str(x.get("quantity") or "").strip()
            conf, val, uni = ss_formato_da_testo(q)
            if not val:
                continue
            nome = (x.get("product_name_it") or x.get("product_name") or "").strip()
            chiave = (nome.lower(), q.lower())
            if not nome or chiave in visti:
                continue
            visti.add(chiave)
            out.append((nome, str(x.get("brands") or "").split(",")[0].strip(), q, str(x.get("code") or ""), (conf, val, uni)))
        if out:
            break
    pw = set(parole)                                                    # prima quelli che hanno più parole in comune con il nome
    out.sort(key=lambda t: -len(pw & set(_ss_re.split(r"[^\wàèéìòù]+", (t[0] + " " + t[1]).lower()))))
    return out[:6]


def _sf_unita_ok(u):
    u = str(u or "").lower()
    return {"gr": "g", "lt": "l", "pezzi": "pz", "pezzo": "pz", "hg": "g"}.get(u, u)


def _sf_salva(p, val, uni, conf=None, nome=None, marca=None):
    uni_ok = _sf_unita_ok(uni)
    if str(uni).lower() == "hg":
        val = float(val) * 100
    esito = {}
    _ss_salva(lambda s_: esito.__setitem__("n", ss_completa_formato(s_, p["id"], val, uni_ok, conf, nome, marca)), "peso/litri del prodotto")
    st.session_state["ss_msg"] = (f"✅ Salvato: {str(val).rstrip('0').rstrip('.') if isinstance(val, float) else val} {uni_ok}. "
                                  f"Ora vedi il prezzo al kg/litro" + (f" (ricalcolati {esito.get('n', 0)} prezzi già inseriti)." if esito.get("n") else "."))
    st.rerun()


def sf_widget_formato(ss, p, k, compatto=True):
    """Le proposte e i campi per aggiungere peso o litri a un prodotto."""
    if not p or not p.get("id"):
        return
    box = st.expander("⚖️ Manca il peso o i litri: aggiungilo per vedere il prezzo al kg/litro", expanded=False) if compatto else st.container(border=True)
    with box:
        if not compatto:
            st.markdown(f"**{_ss_esc(p.get('nome'))}**" + (f" · {_ss_esc(p.get('marca'))}" if p.get("marca") else ""))
        conf_n, val_n, uni_n = ss_formato_da_testo(p.get("nome"))
        if val_n:                                                       # il peso è già scritto nel nome (es. «Fette 500g»)
            if st.button(f"✅ Usa {val_n:g} {uni_n} (scritto nel nome)", key=k + "_nome", type="primary", width="stretch"):
                _sf_salva(p, val_n, uni_n, conf_n if conf_n and conf_n > 1 else None)
        cerca_k = k + "_off"
        testo_ric = " ".join(x for x in (p.get("marca"), p.get("nome")) if x)
        if st.button("🔎 Cerca il peso giusto su Open Food Facts (gratis)", key=k + "_cerca", width="stretch"):
            st.session_state[cerca_k] = True
        if st.session_state.get(cerca_k):
            with st.spinner("Cerco il prodotto…"):
                trovati = sf_cerca_off(testo_ric)
            if not trovati:
                st.info("Non l'ho trovato (il nome dello scontrino è spesso abbreviato). Scrivi il peso qui sotto: lo trovi sulla confezione.")
            else:
                corto = any(len(w) <= 3 for w in str(p.get("nome") or "").split()[1:])     # nome tagliato dallo scontrino, es. «fette bi»
                usa_nome = st.checkbox("Metti anche il nome completo trovato", value=corto, key=k + "_usanome")
                st.caption("Tocca quello giusto (controlla il peso sulla tua confezione):")
                for i, (nome, marca, q, ean, (cf, vl, un)) in enumerate(trovati):
                    if st.button(f"✅ {q} · {nome}" + (f" · {marca}" if marca else ""), key=f"{k}_r{i}", width="stretch"):
                        _sf_salva(p, vl, un, cf if cf and cf > 1 else None, nome if usa_nome else None, marca if usa_nome and not p.get("marca") else None)
        st.caption("…oppure scrivilo tu (è sulla confezione, vicino al codice a barre):")
        c1, c2, c3 = st.columns([2, 2, 2], gap="small")
        val = c1.number_input("Peso o volume", min_value=0.0, value=None, step=1.0, format="%g", key=k + "_v", placeholder="es. 300")
        uni = c2.selectbox("Unità", SS_UNITA_SCELTA, key=k + "_u")
        conf = c3.number_input("Pezzi", min_value=1, value=int(ss_num(p.get("confezioni"), 1) or 1), step=1, key=k + "_c")
        if st.button("💾 Salva peso/litri", key=k + "_ok", width="stretch"):
            if not val:
                st.warning("Scrivi il numero (es. 300 per 300 g).")
            else:
                _sf_salva(p, val, uni, conf)


def sf_senza_peso(ss):
    """I prodotti con almeno un prezzo ma senza peso/litri."""
    con_prezzo = {r.get("prodotto_id") for r in ss.get("rilevazioni") or []}
    return [p for p in ss.get("prodotti") or [] if p.get("id") in con_prezzo and ss_senza_formato(p)]


def sf_banner_senza_peso(ss, k, con_elenco=True):
    sp = sf_senza_peso(ss)
    if not sp:
        return
    msg = (f"⚖️ **{len(sp)} prodott{'o' if len(sp) == 1 else 'i'} senza peso o litri** ("
           + ", ".join(_ss_esc(p.get("nome") or "?") for p in sp[:4]) + ("…" if len(sp) > 4 else "")
           + "): per loro vedo solo il prezzo **a pezzo**, non quello al kg o al litro, e non posso confrontare confezioni diverse.")
    if not con_elenco:
        st.warning(msg + " Apri **⚖️ Manca il peso** sotto la scheda.")
        return
    st.warning(msg)
    with st.expander(f"⚖️ Completa il peso o i litri ({len(sp)})"):
        for p in sp[:40]:
            sf_widget_formato(ss, p, f"sfb_{k}_{p['id']}", compatto=False)


if "_ss_v_dash" in globals() and "_sf_dash_prima" not in globals():
    _sf_dash_prima = _ss_v_dash

    def _ss_v_dash(ss, disp):                                            # noqa: F811
        try:
            sf_banner_senza_peso(ss, "dash")
        except Exception:
            pass
        return _sf_dash_prima(ss, disp)

try:
    if "_GUIDE" in globals() and "_ID_GUIDA" in globals():
        _ids = _ID_GUIDA.setdefault("spesa_smart", [])
        if "ss_peso" not in _ids:
            _ids.append("ss_peso")
            _GUIDE.setdefault("spesa_smart", []).append((
                "⚖️ Peso e litri: il prezzo al kg",
                "Il prezzo **al kg o al litro** serve per confrontare confezioni e marche diverse. Se un prodotto non ha il peso (succede con lo **scontrino**, "
                "dove il nome è abbreviato), vedi solo il prezzo **a pezzo** e compare l'avviso **⚖️ prodotti senza peso o litri**.\n"
                "Sotto la scheda apri **⚖️ Manca il peso o i litri**: se il peso è scritto nel nome basta un tocco; altrimenti **🔎 Cerca il peso giusto su "
                "Open Food Facts** (gratis) e tocca quello giusto (puoi mettere anche il nome completo), oppure scrivilo tu (es. 300 g) e **💾 Salva**.\n"
                "Tutti i prezzi già inseriti di quel prodotto vengono **ricalcolati** al kg o al litro.\n"
                "Nota: per lo **stesso** prodotto in negozi diversi la Lista ottimizzata funziona anche a pezzo; il prezzo al kg serve per confrontare formati e marche diverse.",
                "peso litri prezzo al kg al litro formato manca scontrino open food facts confronto confezioni"))
except Exception:
    pass


# ---- «Tutto deve poter essere modificabile» (22 novembre 2026): prezzo, offerta, negozio, data, note e il prodotto (nome, marca, peso/litri)
def sf_modifica_prezzo(ss, r, k):
    """Modifica completa di un prezzo già inserito e del suo prodotto, con il prezzo al kg/litro calcolato mentre scrivi."""
    p = ss_trova(ss, "prodotti", r.get("prodotto_id")) or {}
    st.markdown("**📦 Prodotto**")
    c1, c2 = st.columns([3, 2], gap="small")
    nome = c1.text_input("Nome", value=p.get("nome", ""), key=k + "_nome")
    marca = c2.text_input("Marca", value=p.get("marca", ""), key=k + "_marca")
    c3, c4, c5 = st.columns(3, gap="small")
    fv = c3.number_input("Peso o volume", min_value=0.0, value=ss_num(p.get("formato_valore")), step=1.0, format="%g", key=k + "_fv", placeholder="es. 300")
    fu0 = _sf_unita_ok(p.get("formato_unita") or "g")
    fu = c4.selectbox("Unità", SS_UNITA_SCELTA, index=SS_UNITA_SCELTA.index(fu0) if fu0 in SS_UNITA_SCELTA else 0, key=k + "_fu")
    conf = c5.number_input("Pezzi", min_value=1, value=int(ss_num(p.get("confezioni"), 1) or 1), step=1, key=k + "_conf")
    st.markdown("**💶 Prezzo**")
    c6, c7 = st.columns(2, gap="small")
    prezzo = c6.number_input("Prezzo (€)", min_value=0.0, value=ss_num(r.get("prezzo")), step=0.01, format="%.2f", key=k + "_pr")
    promo = c7.number_input("In offerta (€)", min_value=0.0, value=ss_num(r.get("prezzo_promo")), step=0.01, format="%.2f", key=k + "_pp", placeholder="se c'è")
    neg_ids = [n["id"] for n in ss["negozi"]]
    _nomi_neg = {i: ss_nome_negozio(ss_trova(ss, "negozi", i)) for i in neg_ids}
    neg = st.selectbox("🏪 Negozio", neg_ids, index=neg_ids.index(r["negozio_id"]) if r.get("negozio_id") in neg_ids else (0 if neg_ids else None),
                       format_func=lambda i: _nomi_neg.get(i, i), key=k + "_neg", accept_new_options=True,
                       placeholder="Scegli o scrivi il negozio")
    st.caption("🏪 Per cambiare negozio tocca il riquadro: scegli dall'elenco oppure **scrivi il nome di un negozio nuovo** e tocca la riga **«Add: …»** (in inglese vuol dire «Aggiungi»).")
    neg_nuovo = {}
    if neg and neg not in neg_ids:                                   # negozio scritto a mano: lo creo (o lo riconosco se c'è già)
        cn1, cn2 = st.columns(2, gap="small")
        neg_nuovo = {"nome": str(neg).strip(), "citta": cn1.text_input("Città (facoltativa)", key=k + "_negc", placeholder="es. Torino"),
                     "indirizzo": cn2.text_input("Indirizzo (facoltativo)", key=k + "_negi", placeholder="es. Via Roma 1")}
        st.caption(f"➕ «{neg_nuovo['nome']}» sarà aggiunto ai tuoi negozi quando salvi.")
    c8, c9, c10 = st.columns(3, gap="small")
    data_r = c8.date_input("Data del prezzo", value=ss_data(r.get("data")) or ss_oggi(), max_value=ss_oggi(), format="DD/MM/YYYY", key=k + "_d")
    pdal = c9.date_input("Offerta dal", value=ss_data(r.get("promo_dal")), format="DD/MM/YYYY", key=k + "_pdal")
    pal = c10.date_input("Offerta fino al", value=ss_data(r.get("promo_al")), format="DD/MM/YYYY", key=k + "_pal")
    tess = st.checkbox("Serve la tessera fedeltà", value=bool(r.get("tessera")), key=k + "_t")
    note = st.text_input("Note", value=r.get("note", ""), key=k + "_note")
    # il prezzo al kg/litro, calcolato subito
    proprio = ss_num(r.get("formato_valore")) and (ss_num(r.get("formato_valore")), r.get("formato_unita")) != (ss_num(p.get("formato_valore")), p.get("formato_unita"))
    fv_r, fu_r = (r.get("formato_valore"), r.get("formato_unita")) if proprio else (fv, fu)
    pu, base = ss_prezzo_unitario(promo or prezzo, conf, fv_r, fu_r if fv_r else "")
    if pu:
        st.markdown(f"<div class='ss-card'><span class='u'>= {ss_fmt_unitario(pu, base)}</span>"
                    + ("" if fv_r else " <small>(scrivi il peso o i litri per il prezzo al kg/litro)</small>") + "</div>", unsafe_allow_html=True)
    if st.button("💾 Salva le modifiche", key=k + "_ok", type="primary", width="stretch"):
        esito = {}

        def _m(s_):
            pr = ss_trova(s_, "prodotti", r.get("prodotto_id"))
            if pr is not None:
                prima = {x: pr.get(x) for x in ("formato_valore", "formato_unita", "confezioni")}
                if nome.strip():
                    pr["nome"] = nome.strip()
                pr["marca"] = marca.strip()
                pr["formato_valore"], pr["formato_unita"], pr["confezioni"] = (fv or None), (fu if fv else ""), int(conf)
                ss_cambia_formato_prodotto(s_, pr["id"], prima)
            neg_id = neg if neg in neg_ids else None
            if neg_nuovo.get("nome"):
                n_ = ss_trova_negozio_da_testo(s_, neg_nuovo["nome"], neg_nuovo.get("citta", ""), neg_nuovo.get("indirizzo", ""))
                if n_ is None:
                    n_, _x = ss_aggiungi_negozio(s_, {"nome": neg_nuovo["nome"], "catena": neg_nuovo["nome"], "citta": neg_nuovo.get("citta", "").strip(),
                                                      "indirizzo": neg_nuovo.get("indirizzo", "").strip()})
                neg_id = n_["id"]
            esito["err"] = ss_modifica_rilevazione(s_, r["id"], {"prezzo": prezzo, "prezzo_promo": promo, "negozio_id": neg_id or r.get("negozio_id"),
                                                                 "data": data_r.isoformat() if data_r else r.get("data"),
                                                                 "promo_dal": pdal.isoformat() if pdal else "", "promo_al": pal.isoformat() if pal else "",
                                                                 "tessera": tess, "note": note})
        _ss_salva(_m, "prezzo modificato")
        if esito.get("err"):
            for e in esito["err"]:
                st.warning(e)
        else:
            st.session_state["ss_msg"] = "✅ Modificato: prezzo al kg/litro ricalcolato."
            for _kk in [x for x in list(st.session_state) if str(x).startswith(k + "_")]:     # la prossima volta riparte dai dati salvati
                st.session_state.pop(_kk, None)
            st.rerun()


@st.dialog("✏️ Modifica il prezzo e il prodotto", width="large")
def sf_dialogo_modifica(rid):
    """Finestra sopra la pagina (resta aperta mentre scrivi): tutti i campi del prezzo e del prodotto."""
    ss, _disp = _ss_leggi()
    r = ss_trova(ss, "rilevazioni", rid)
    if not r:
        st.warning("Questo prezzo non c'è più.")
        return
    sf_modifica_prezzo(ss, r, "dlg_" + rid)
    if st.button("🗑️ Elimina questo prezzo", key="dlg_del_" + rid, width="stretch"):
        _ss_salva(lambda s_: ss_elimina(s_, "rilevazioni", rid), "prezzo eliminato")
        st.session_state["ss_msg"] = "🗑️ Prezzo eliminato."
        st.rerun()


# ---- «Si può anche aggiungere la foto del prodotto?» (22 novembre 2026)
def _sf_img_ok(u):
    u = str(u or "")
    return u.startswith("http") or u.startswith("data:image/")


@st.dialog("📷 Foto del prodotto", width="large")
def sf_dialogo_foto(pid):
    """Scatta, carica dal telefono o scegli dall'archivio: sfondo tolto e raddrizzata come nella Dispensa."""
    ss, disp = _ss_leggi()
    p = ss_trova(ss, "prodotti", pid)
    if not p:
        p = next((x for x in ss_catalogo(ss, disp) if x.get("id") == pid), None)
    if not p:
        st.warning("Prodotto non trovato.")
        return
    st.markdown(f"**{_ss_esc(p.get('nome'))}**" + (f" · {_ss_esc(p.get('marca'))}" if p.get("marca") else ""))
    uri = ""
    try:
        uri = campo_foto("ssfoto_" + pid, p.get("immagine") or "", archivio=True)
    except Exception:
        st.caption("La foto con ritocco non è disponibile adesso: usa il campo qui sotto.")
    with st.expander("📎 Se la foto non compare, usa questo campo"):
        alt = st.file_uploader("Scatta o scegli la foto", type=["jpg", "jpeg", "png", "webp"], key="ssfoto_alt_" + pid)
        if alt is not None and not uri:
            try:
                from PIL import Image as _Im
                import io as _io, base64 as _b64
                im = _Im.open(_io.BytesIO(alt.getvalue())).convert("RGB")
                im.thumbnail((640, 640))
                buf = _io.BytesIO()
                im.save(buf, "WEBP", quality=80)
                uri = "data:image/webp;base64," + _b64.b64encode(buf.getvalue()).decode()
                st.image(uri, width=200)
            except Exception as ex:
                st.warning(f"Non riesco a leggere questa foto ({type(ex).__name__}).")
    c1, c2 = st.columns(2, gap="small")
    if c1.button("💾 Salva la foto", key="ssfoto_ok_" + pid, type="primary", width="stretch", disabled=not uri):
        def _m(s_):
            pr = ss_trova(s_, "prodotti", pid) or (ss_materializza(s_, dict(p)) if "ss_materializza" in globals() else None)
            if pr is not None:
                pr["immagine"] = uri
        _ss_salva(_m, "foto del prodotto")
        st.session_state["ss_msg"] = "📷 Foto salvata."
        st.rerun()
    if p.get("immagine") and c2.button("🗑️ Togli la foto", key="ssfoto_del_" + pid, width="stretch"):
        _ss_salva(lambda s_: (ss_trova(s_, "prodotti", pid) or {}).pop("immagine", None), "foto tolta")
        st.session_state["ss_msg"] = "🗑️ Foto tolta."
        st.rerun()


# ---- «I prodotti di Dove costa meno devono poter essere inseriti nella lista ottimizzata e suddivisi per supermercato o negozio a richiesta» (22/11/2026)
def sf_metti_in_lista(lid, p, quantita=1):
    """Aggiunge il prodotto alla lista scelta (Dispensa, privata o condivisa) senza doppioni. Ritorna True se nuovo, False se ha sommato/era già."""
    q = ss_num(quantita, 1) or 1
    esito = {"nuovo": True}
    if lid == _SS_LISTA_DISP:
        _ss_salva_disp(lambda d: esito.__setitem__("nuovo", aggiungi_a_spesa(d, {"nome": p.get("nome"), "marca": p.get("marca", ""), "barcode": p.get("ean", ""), "q": q})),
                       "dalla classifica alla lista")
    elif str(lid).startswith("c:"):
        uid = _ss_uid()

        def _fn(d):
            l = next((x for x in d.get("liste") or [] if x.get("id") == lid[2:]), None)
            if not ss_lc_puo(l, uid):
                raise PermissionError("lista non condivisa con te")
            esito["nuovo"] = ss_lc_aggiungi(l, p, q, uid)[1]
            d["versione"] = int(d.get("versione") or 0) + 1
        salva_file(SS_LC, _fn, "Spesa Smart: lista condivisa")
    else:
        def _fp(s_):
            pr = ss_trova(s_, "prodotti", p["id"]) or ss_materializza(s_, dict(p))
            gia = next((r for r in s_["liste_righe"] if r.get("lista_id") == lid and r.get("prodotto_id") == pr["id"] and r.get("stato") != "preso"), None)
            if gia:
                gia["quantita"] = (ss_num(gia.get("quantita"), 1) or 1) + q
                esito["nuovo"] = False
            else:
                s_["liste_righe"].append({"id": ss_id(), "lista_id": lid, "prodotto_id": pr["id"], "quantita": q, "priorita": "Normale", "stato": "da comprare"})
        _ss_salva(_fp, "dalla classifica alla lista")
    return esito["nuovo"]


def sf_dcm_barra_lista(ss, righe):
    """In cima a Dove costa meno: in quale lista mettere i prodotti, «tutti in lista» e il passaggio alla Lista ottimizzata."""
    with st.container(border=True):
        st.markdown("**📝 Metti in lista e ottimizza**")
        lid = _ss_scegli_lista(ss, "ss_dcm_lista")
        st.session_state["_sf_dcm_lid"] = lid
        c1, c2 = st.columns(2, gap="small")
        if righe and c1.button(f"➕ Tutti quelli qui sotto ({len(righe)})", key="sf_dcm_tutti", width="stretch"):
            nuovi = sum(1 for x in righe if sf_metti_in_lista(lid, x["prodotto"], 1))
            st.session_state["ss_msg"] = f"📝 {nuovi} prodotti messi in lista" + (f" ({len(righe) - nuovi} c'erano già)." if len(righe) - nuovi else ".")
            st.rerun()
        if c2.button("🧮 Vai alla lista ottimizzata", key="sf_dcm_vai", type="primary", width="stretch"):
            st.session_state["ss_ott_sel_prossima"] = lid
            _ss_vai("ott")
            st.rerun()


def sf_dcm_tasto_lista(x):
    lid = st.session_state.get("_sf_dcm_lid", _SS_LISTA_DISP)
    if st.button("➕ In lista", key="sf_dcm_l_" + x["prodotto"]["id"], width="stretch"):
        nuovo = sf_metti_in_lista(lid, x["prodotto"], 1)
        st.toast(f"📝 «{x['prodotto'].get('nome')}» " + ("è in lista." if nuovo else "era già in lista."))


def ss_dividi_nei_negozi(ss, righe, negozi_scelti, oggi_=None):
    """Divide la lista SOLO nei negozi scelti: ogni prodotto va dove costa meno fra quelli. Ritorna {per_negozio:{nid:[voce]}, totale, non_trovati:[riga], mancano:[riga]}."""
    oggi_ = oggi_ or ss_oggi()
    scelti = set(negozi_scelti or [])
    per_neg, tot, non_trovati, mancano = {}, 0.0, [], []
    for rg in righe:
        pid = rg.get("prodotto_id")
        cor = ss_prezzi_correnti(ss, pid, oggi_) if pid else []
        if not cor:
            mancano.append(rg)
            continue
        qui = [c for c in cor if c["negozio_id"] in scelti]
        if not qui:
            non_trovati.append(rg)
            continue
        c = min(qui, key=lambda c: c["prezzo"])
        q = ss_num(rg.get("quantita"), 1) or 1
        voce = {"riga": rg, "negozio_id": c["negozio_id"], "prezzo": c["prezzo"], "totale": round(c["prezzo"] * q, 2), "unitario": c.get("unitario"), "base": c.get("base"),
                "offerta": c.get("offerta")}
        per_neg.setdefault(c["negozio_id"], []).append(voce)
        tot += voce["totale"]
    return {"per_negozio": per_neg, "totale": round(tot, 2), "non_trovati": non_trovati, "mancano": mancano}


def sf_testo_per_negozio(ss, div):
    righe = ["🛒 Lista della spesa divisa per negozio"]
    for nid, voci in div["per_negozio"].items():
        n = ss_trova(ss, "negozi", nid)
        righe.append(f"\n🏪 {ss_nome_negozio(n)} — {ss_euro(sum(v['totale'] for v in voci))}")
        for v in voci:
            nome = v["riga"].get("nome") or (ss_trova(ss, "prodotti", v["riga"].get("prodotto_id")) or {}).get("nome", "?")
            righe.append(f"☐ {nome} × {ss_num(v['riga'].get('quantita'), 1):g} = {ss_euro(v['totale'])}")
    if div["non_trovati"] or div["mancano"]:
        righe.append("\n❓ Senza prezzo in questi negozi: " + ", ".join(r.get("nome") or "?" for r in div["non_trovati"] + div["mancano"]))
    righe.append(f"\nTotale: {ss_euro(div['totale'])}")
    return "\n".join(righe)


def sf_ottimizzata_a_scelta(ss, righe):
    """La divisione per negozio a richiesta: scegli tu uno o più negozi, ogni prodotto va dove costa meno fra quelli."""
    con_prezzo = {c["negozio_id"] for rg in righe if rg.get("prodotto_id") for c in ss_prezzi_correnti(ss, rg["prodotto_id"], ss_oggi())}
    ids = [n["id"] for n in ss["negozi"] if n["id"] in con_prezzo] or [n["id"] for n in ss["negozi"]]
    if not ids:
        st.info("Non ci sono ancora negozi con prezzi.")
        return
    scelti = st.multiselect("🏪 In quali negozi vuoi andare?", ids, default=ids[:min(len(ids), 2)], format_func=lambda i: ss_nome_negozio(ss_trova(ss, "negozi", i)),
                            key="sf_ott_neg", help="Ne scegli uno solo = tutta la spesa lì. Più di uno = ogni prodotto va dove costa meno fra quelli scelti.")
    if not scelti:
        st.info("Scegli almeno un negozio.")
        return
    div = ss_dividi_nei_negozi(ss, righe, scelti)
    st.markdown(f"<div class='ss-scen ok'><h4>🏪 La tua spesa divisa per negozio</h4><div class='tot'>{ss_euro(div['totale'])}</div>"
                f"<div>{len(div['per_negozio'])} {'negozio' if len(div['per_negozio']) == 1 else 'negozi'}</div></div>", unsafe_allow_html=True)
    for nid, voci in div["per_negozio"].items():
        n = ss_trova(ss, "negozi", nid)
        with st.container(border=True):
            st.markdown(f"**🏪 {_ss_esc(ss_nome_negozio(n))}** — **{ss_euro(sum(v['totale'] for v in voci))}**")
            for v in voci:
                nome = v["riga"].get("nome") or (ss_trova(ss, "prodotti", v["riga"].get("prodotto_id")) or {}).get("nome", "?")
                st.markdown(f"• {_ss_esc(nome)} × {ss_num(v['riga'].get('quantita'), 1):g} = **{ss_euro(v['totale'])}**"
                            + (f" · {ss_fmt_unitario(v['unitario'], v['base'])}" if v.get("unitario") and v.get("base") != "pz" else "")
                            + (" 🔥 offerta" if v.get("offerta") else ""))
    if div["non_trovati"]:
        st.warning("❓ Non ho il prezzo **in questi negozi** per: " + ", ".join(_ss_esc(r.get("nome") or "?") for r in div["non_trovati"])
                   + ". Aggiungi un altro negozio o inserisci il prezzo.")
    if div["mancano"]:
        st.caption("Senza nessun prezzo valido oggi: " + ", ".join(_ss_esc(r.get("nome") or "?") for r in div["mancano"]))
    testo = sf_testo_per_negozio(ss, div)
    import urllib.parse as _up
    st.link_button("📤 Manda la lista divisa per negozio su WhatsApp", "https://wa.me/?text=" + _up.quote(testo), width="stretch")
    with st.expander("📋 Testo da copiare"):
        st.code(testo, language=None)
