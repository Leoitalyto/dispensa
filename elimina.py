# -*- coding: utf-8 -*-
"""Cestino su ogni prodotto: si apre una finestra che mostra tutte le voci dello stesso prodotto
(con scadenze diverse) e si sceglie quali eliminare. Caricato da app_dispensa.py dopo spesa.py."""


def apri_elimina(ids):
    """Apre la finestra per eliminare. 'ids' sono le voci gia' spuntate; si vedono anche le altre voci dello stesso prodotto."""
    ids = list(ids)
    giro = st.session_state["elimina_giro"] = st.session_state.get("elimina_giro", 0) + 1

    def _finestra():
        tutti = carica_dati(crea_archivio(), st.session_state["percorso"]).get("articoli", [])
        chiavi = {_chiave_prodotto(r) for r in tutti if r["id"] in ids}
        if not chiavi:
            st.info(t("Non c'è ancora nulla da gestire."))
            return
        gruppi = {}
        for r in sorted(tutti, key=lambda x: x.get("scadenza") or "9999-12-31"):
            if _chiave_prodotto(r) in chiavi:
                gruppi.setdefault(_chiave_prodotto(r), []).append(r)
        scelte = []
        for righe in gruppi.values():
            st.markdown(f"**{icona_cat(categoria_di(righe[0]))} {righe[0].get('nome', '')}**"
                        + (f" · {righe[0]['marca']}" if righe[0].get("marca") else ""))
            if len(righe) > 1:
                st.caption(t("Questo prodotto ha {n} voci con scadenze diverse: scegli quali eliminare.", n=len(righe)))
            for r in righe:
                stato, giorni = stato_scadenza(r.get("scadenza"), oggi())
                pezzi = [ICONE[stato]] + ([data_it(r["scadenza"])] if r.get("scadenza") else []) \
                    + [descrivi([r]), testo_giorni(stato, giorni)]
                if st.checkbox(" · ".join(pezzi), value=r["id"] in ids, key=f"el_{giro}_{r['id']}"):
                    scelte.append(r["id"])
        nella_spesa = st.checkbox("🛒 " + t("Metti nella lista della spesa"), key=f"el_spesa_{giro}")
        motivo = None
        if scelte and "MOTIVI_ELIMINA" in globals():
            _scaduto_sel = any(stato_scadenza(r.get("scadenza"), oggi())[0] == "scaduto" for r in tutti if r["id"] in scelte)
            motivo = st.radio("Perché lo elimini? (serve per le statistiche)", MOTIVI_ELIMINA, index=0 if _scaduto_sel else 1, key=f"el_motivo_{giro}_{int(_scaduto_sel)}")
        if not scelte:
            st.caption(t("Spunta almeno una voce da eliminare."))
        c1, c2 = st.columns(2)
        if c1.button("🗑️ " + t("Elimina le voci scelte"), type="primary", disabled=not scelte,
                     key=f"el_ok_{giro}", width="stretch"):
            def _togli(d):
                tolte = [r for r in d.get("articoli", []) if r["id"] in scelte]
                d["articoli"] = [r for r in d.get("articoli", []) if r["id"] not in scelte]
                _tipo_ev = tipo_da_motivo(motivo) if motivo and "tipo_da_motivo" in globals() else None
                if _tipo_ev:                                           # per le statistiche
                    for r in tolte:
                        registra_evento(d, _tipo_ev, r, motivo=motivo)
                if nella_spesa:
                    for r in tolte:
                        if not any(_chiave_prodotto(x) == _chiave_prodotto(r) for x in d["articoli"]):
                            aggiungi_a_spesa(d, r)
            try:
                salva(_togli, "Eliminato dalla dispensa")
                st.session_state["messaggio"] = "🗑️ " + t("Eliminato dalla dispensa.")
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))
        if c2.button(t("Annulla"), key=f"el_no_{giro}", width="stretch"):
            st.rerun()

    st.dialog("🗑️ " + t("Elimina dalla dispensa"))(_finestra)()


CSS = CSS.replace("</style>", """
[class*="st-key-cest_"]{margin-top:0}
[class*="st-key-cest_"] button{width:100%;min-height:52px;border-radius:999px !important;background:rgba(255,255,255,.78) !important;color:#c62828 !important;
 border:2px solid rgba(220,38,38,.28) !important;font-weight:800 !important;box-shadow:0 8px 18px rgba(0,60,50,.1)}
[class*="st-key-cest_"] button p{font-weight:800 !important;color:#c62828 !important}
[class*="st-key-cest_"] button:hover{background:#fee2e2 !important}
[class*="st-key-cest_"] button:disabled{opacity:.5}
</style>""")
