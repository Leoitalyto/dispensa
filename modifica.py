# -*- coding: utf-8 -*-
"""Tasto 'Modifica' su ogni prodotto: si apre una finestra dove si cambia qualsiasi dato (foto, nome, marca, quantita',
scadenza, posto, allergeni, note...). Nome, foto e allergeni valgono per tutte le scadenze dello stesso prodotto;
quantita', scadenza e note solo per la voce scelta. Caricato da app_dispensa.py dopo foto_prodotto.py."""


def apri_modifica(rid):
    giro = st.session_state["modifica_giro"] = st.session_state.get("modifica_giro", 0) + 1

    def _finestra():
        tutti = carica_dati(crea_archivio(), st.session_state["percorso"]).get("articoli", [])
        r = next((x for x in tutti if x["id"] == rid), None)
        if r is None:
            st.info(t("Prodotto non trovato."))
            return
        chiave_vecchia = _chiave_prodotto(r)
        altre = sum(1 for x in tutti if _chiave_prodotto(x) == chiave_vecchia)
        K = lambda nome: f"mod_{giro}_{nome}_{rid}"
        if altre > 1:
            st.caption(t("Nome, foto e allergeni valgono per tutte le scadenze di questo prodotto; quantità, scadenza e note solo per questa voce."))

        nuova_foto = campo_foto(K("foto"), r.get("immagine") or "")
        togli_foto = st.checkbox(t("Togli la foto"), key=K("togli")) if (r.get("immagine") and not nuova_foto) else False

        m1, m2 = st.columns(2)
        nome = m1.text_input(t("Nome del prodotto *"), value=r.get("nome", ""), key=K("nome"))
        marca = m2.text_input(t("Marca"), value=r.get("marca", ""), key=K("marca"))
        categoria = st.text_input(t("Categoria"), value=r.get("categoria", ""), key=K("categoria"))
        sezioni = list(CATEGORIE)
        per_chi = st.radio("👪 " + t("Per chi è il prodotto?"), sezioni, format_func=nome_cat, horizontal=True,
                           index=sezioni.index(categoria_di(r)) if categoria_di(r) in sezioni else 0, key=K("per_chi"))
        posti = list(POSTI)
        posto = st.selectbox(t("Dove lo metti?"), posti, format_func=nome_posto_scelta,
                             index=posti.index(posto_di(r)), key=K("posto"))
        posto_altro = st.text_input(t("Scrivi dove lo metti"), value=r.get("posto_altro", ""), key=K("posto_altro")) if posto == "altro" else ""
        codice = st.text_input(t("Codice a barre (i numeri sotto le barre)"), value=r.get("barcode", ""), key=K("codice")).strip()

        q1, q2, q3 = st.columns(3)
        quant = q1.number_input(t("Quante unità hai? *"), min_value=0.0, step=1.0, value=float(r.get("quantita") or 0), key=K("quant"))
        fval = q2.number_input(t("Contenuto di ogni unità"), min_value=0.0, step=10.0, value=float(r.get("formato_valore") or 0), key=K("fval"))
        unita_att = r.get("formato_unita") if r.get("formato_unita") in UNITA_CONTENUTO else "g"
        funita = q3.selectbox(t("Unità del contenuto"), UNITA_CONTENUTO, index=UNITA_CONTENUTO.index(unita_att), key=K("funita"))
        s1, s2 = st.columns([2, 1])
        senza_scad = s2.checkbox(t("Senza scadenza"), value=not r.get("scadenza"), key=K("senza"))
        try:
            scad_att = date.fromisoformat(r["scadenza"]) if r.get("scadenza") else aggiungi_mesi(oggi(), 6)
        except Exception:
            scad_att = aggiungi_mesi(oggi(), 6)
        scad = s1.date_input(t("Scadenza"), value=scad_att, format="DD/MM/YYYY", disabled=senza_scad, key=K("scad"))
        note = st.text_input(t("Note (facoltative)"), value=r.get("note", ""), key=K("note"))

        with st.expander((("🌾 " + t("Allergeni e ingredienti")) if per_chi != "animali" else ("🥣 " + t("Composizione")))):
            if per_chi != "animali":
                allergeni = st.multiselect(t("Contiene"), ELENCO_ALLERGENI, default=[a for a in (r.get("allergeni") or []) if a in ELENCO_ALLERGENI],
                                           format_func=t_all, key=K("allergeni"))
                tracce = st.multiselect(t("Può contenere tracce di"), ELENCO_ALLERGENI, default=[a for a in (r.get("tracce") or []) if a in ELENCO_ALLERGENI],
                                        format_func=t_all, key=K("tracce"))
                senza_glutine = st.checkbox(t("Etichettato senza glutine"), value=bool(r.get("senza_glutine")), key=K("senza_glutine"))
            else:
                allergeni, tracce, senza_glutine = [], [], False
            ingredienti = st.text_area(t("Ingredienti"), value=r.get("ingredienti", ""), height=90, key=K("ingredienti"))

        c1, c2 = st.columns(2)
        if c1.button("💾 " + t("Salva le modifiche"), type="primary", key=K("ok"), width="stretch"):
            if not nome.strip():
                st.error(t("Scrivi il nome del prodotto."))
            elif quant <= 0:
                st.error(t("Indica quante unità hai (almeno 1)."))
            elif codice and not ean_valido(codice):
                st.error(t("Il codice non sembra corretto (di solito ha 13 numeri). Controlla le cifre."))
            else:
                comuni = {"nome": nome.strip(), "marca": marca.strip(), "categoria": categoria.strip(), "per_chi": per_chi,
                          "posto": posto, "posto_altro": posto_altro.strip() if posto == "altro" else "", "barcode": codice,
                          "formato_valore": float(fval) if fval else None, "formato_unita": funita if fval else None,
                          "allergeni": allergeni, "tracce": tracce, "senza_glutine": bool(senza_glutine),
                          "ingredienti": ingredienti.strip()}
                if nuova_foto:
                    comuni["immagine"] = nuova_foto
                elif togli_foto:
                    comuni["immagine"] = ""
                singoli = {"quantita": float(quant), "scadenza": None if senza_scad else scad.isoformat(), "note": note.strip()}

                def _applica(d):
                    for x in d.get("articoli", []):
                        if _chiave_prodotto(x) == chiave_vecchia:
                            x.update(comuni)
                            x["allergeni_noti"] = bool(x.get("allergeni_noti") or allergeni)
                            if x["id"] == rid:
                                x.update(singoli)
                try:
                    salva(_applica, f"Modificato {comuni['nome']}")
                    st.session_state["messaggio"] = "✅ " + t("Modifiche salvate.")
                    st.rerun()
                except Exception as e:
                    st.error(t("Non sono riuscito a salvare: {e}", e=e))
        if c2.button(t("Annulla"), key=K("no"), width="stretch"):
            st.rerun()

    st.dialog("✏️ " + t("Modifica prodotto"))(_finestra)()
