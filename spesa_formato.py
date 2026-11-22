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
    neg = st.selectbox("🏪 Negozio", neg_ids, index=neg_ids.index(r["negozio_id"]) if r.get("negozio_id") in neg_ids else 0,
                       format_func=lambda i: ss_nome_negozio(ss_trova(ss, "negozi", i)), key=k + "_neg") if neg_ids else None
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
            esito["err"] = ss_modifica_rilevazione(s_, r["id"], {"prezzo": prezzo, "prezzo_promo": promo, "negozio_id": neg or r.get("negozio_id"),
                                                                 "data": data_r.isoformat() if data_r else r.get("data"),
                                                                 "promo_dal": pdal.isoformat() if pdal else "", "promo_al": pal.isoformat() if pal else "",
                                                                 "tessera": tess, "note": note})
        _ss_salva(_m, "prezzo modificato")
        if esito.get("err"):
            for e in esito["err"]:
                st.warning(e)
        else:
            st.session_state["ss_msg"] = "✅ Modificato: prezzo al kg/litro ricalcolato."
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
