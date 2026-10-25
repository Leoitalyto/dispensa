# -*- coding: utf-8 -*-
"""Lista della spesa: i prodotti finiti ci finiscono da soli, e il tasto 'Ne ho consumato uno'.
Questo file viene caricato da app_dispensa.py prima di parte3.py."""


def _chiave_prodotto(r):
    return ((r.get("barcode") or "").strip() or (r.get("nome") or "").strip().lower())


def aggiungi_a_spesa(d, r):
    """Mette un prodotto nella lista della spesa (una sola volta). Ritorna True se l'ha aggiunto."""
    lista = d.setdefault("spesa", [])
    chiave = _chiave_prodotto(r)
    if not chiave or any(_chiave_prodotto(x) == chiave and not x.get("preso") for x in lista):
        return False
    lista.append({"id": uuid.uuid4().hex[:10], "nome": r.get("nome", ""), "marca": r.get("marca", ""),
                  "barcode": r.get("barcode", ""), "per_chi": r.get("per_chi", "adulti"), "preso": False,
                  "aggiunto_il": datetime.now().isoformat(timespec="seconds")})
    return True


def togli_da_spesa(d, prodotti):
    """Quando un prodotto torna in dispensa esce dalla lista della spesa."""
    chiavi = {_chiave_prodotto(r) for r in prodotti}
    d["spesa"] = [x for x in d.get("spesa", []) if _chiave_prodotto(x) not in chiavi]


def consuma_uno(d, id_riga):
    """Toglie un'unita' al prodotto. Se finisce, lo toglie dalla dispensa e lo mette nella lista della spesa."""
    articoli = d.get("articoli", [])
    riga = next((r for r in articoli if r.get("id") == id_riga), None)
    if riga is None:
        return {"stato": "assente"}
    resto = float(riga.get("quantita") or 0) - 1
    if resto > 0:
        riga["quantita"] = resto
        return {"stato": "resta", "nome": riga.get("nome", ""), "n": resto}
    d["articoli"] = [r for r in articoli if r.get("id") != id_riga]
    if any(_chiave_prodotto(r) == _chiave_prodotto(riga) for r in d["articoli"]):
        return {"stato": "altre", "nome": riga.get("nome", "")}      # ne restano con un'altra scadenza
    aggiungi_a_spesa(d, riga)
    return {"stato": "finito", "nome": riga.get("nome", "")}


def aggiungi_uno(d, id_riga):
    """Aggiunge un'unita' al prodotto."""
    riga = next((r for r in d.get("articoli", []) if r.get("id") == id_riga), None)
    if riga is None:
        return {"stato": "assente"}
    riga["quantita"] = float(riga.get("quantita") or 0) + 1
    return {"stato": "aggiunto", "nome": riga.get("nome", ""), "n": riga["quantita"]}


# i prodotti messi a 0 unita' nella tabella 'Gestisci' finiscono anch'essi nella lista della spesa
_applica_modifiche_senza_spesa = applica_modifiche


def applica_modifiche(d, modificata):
    finiti = []
    for r in d.get("articoli", []):
        if r["id"] in modificata.index:
            m = modificata.loc[r["id"]]
            if not bool(m["🗑️"]) and float(m["Unità"]) <= 0:
                finiti.append(dict(r))
    _applica_modifiche_senza_spesa(d, modificata)
    for r in finiti:
        if not any(_chiave_prodotto(x) == _chiave_prodotto(r) for x in d.get("articoli", [])):
            aggiungi_a_spesa(d, r)


_FRAMMENTO = hasattr(st, "fragment")


def _ricarica():
    """Aggiorna solo la scheda Spesa (senza tornare alla prima scheda)."""
    if _FRAMMENTO:
        st.rerun(scope="fragment")
    st.rerun()


def _corpo_spesa():
    """Contenuto della scheda 'Spesa' (legge sempre i dati aggiornati)."""
    lista = list(carica_dati(crea_archivio(), st.session_state["percorso"]).get("spesa", []))
    st.subheader("🛒 " + t("Lista della spesa"))
    st.caption(t("I prodotti finiti (0 unità) arrivano qui da soli. Quando li aggiungi di nuovo in dispensa escono dalla lista."))
    giro = st.session_state.setdefault("spesa_giro", 0)
    c1, c2 = st.columns([3, 2])
    nuovo = c1.text_input(t("Cosa devi comprare?"), key=f"spesa_nuovo_{giro}", label_visibility="collapsed",
                          placeholder=t("Cosa devi comprare?"))
    if c2.button("➕ " + t("Aggiungi alla lista"), key=f"spesa_aggiungi_{giro}", width="stretch"):
        nome = nuovo.strip()
        if not nome:
            st.warning(t("Scrivi cosa devi comprare."))
        elif any((x.get("nome") or "").strip().lower() == nome.lower() and not x.get("preso") for x in lista):
            st.info(t("È già nella lista."))
        else:
            try:
                salva(lambda d: aggiungi_a_spesa(d, {"nome": nome}), "Spesa: " + nome)
                st.session_state["spesa_giro"] = giro + 1
                _ricarica()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))
    if not lista:
        st.info(t("La lista della spesa è vuota."))
        return
    negozi = sorted({(x.get("negozio") or "").strip() for x in lista if (x.get("negozio") or "").strip()})
    filtro_neg = "Tutti"
    if negozi:
        filtro_neg = st.selectbox("🏪 Mostra", ["Tutti"] + negozi + ["Senza negozio"], key="spesa_filtro_negozio")
    lista.sort(key=lambda x: (bool(x.get("preso")), (x.get("negozio") or "~").lower(), x.get("aggiunto_il", "")))
    if filtro_neg == "Senza negozio":
        lista = [x for x in lista if not (x.get("negozio") or "").strip()]
    elif filtro_neg != "Tutti":
        lista = [x for x in lista if (x.get("negozio") or "").strip() == filtro_neg]
    if not lista:
        st.info(t("La lista della spesa è vuota."))
        return
    df = pd.DataFrame([{"id": x["id"], "Preso": bool(x.get("preso")),
                        "Prodotto": x.get("nome", "") + (f" · {x['marca']}" if x.get("marca") else ""),
                        "Dove": (_dove(x) if "_dove" in globals() else ""),
                        "🗑️": False} for x in lista]).set_index("id")
    modificata = st.data_editor(df, hide_index=True, width="stretch", key=f"editor_spesa_{len(lista)}_{giro}_{filtro_neg}",
                                disabled=["Prodotto", "Dove"],
                                column_config={"Preso": st.column_config.CheckboxColumn(t("Preso"), width="small"),
                                               "Prodotto": st.column_config.TextColumn(t("Prodotto")),
                                               "Dove": st.column_config.TextColumn("🏪 Dove"),
                                               "🗑️": st.column_config.CheckboxColumn("🗑️", width="small")})

    def _applica(d):
        nuova = []
        for x in d.get("spesa", []):
            if x["id"] in modificata.index:
                m = modificata.loc[x["id"]]
                if bool(m["🗑️"]):
                    continue
                x["preso"] = bool(m["Preso"])
            nuova.append(x)
        d["spesa"] = nuova

    b1, b2 = st.columns(2)
    if b1.button("💾 " + t("Salva modifiche"), type="primary", key="spesa_salva", width="stretch"):
        try:
            salva(_applica, "Lista della spesa")
            _ricarica()
        except Exception as e:
            st.error(t("Non sono riuscito a salvare: {e}", e=e))
    if b2.button("🧹 " + t("Togli quelli presi"), key="spesa_pulisci", width="stretch"):
        try:
            def _pulisci(d):
                _applica(d)
                d["spesa"] = [x for x in d.get("spesa", []) if not x.get("preso")]
            salva(_pulisci, "Spesa: tolti i presi")
            _ricarica()
        except Exception as e:
            st.error(t("Non sono riuscito a salvare: {e}", e=e))


scheda_spesa = st.fragment(_corpo_spesa) if _FRAMMENTO else _corpo_spesa
