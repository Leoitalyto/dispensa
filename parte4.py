

# ---------------------------------------------------------------------
# AGGIUNGI
# ---------------------------------------------------------------------
with tab_aggiungi:
    n = st.session_state.setdefault("n_form", 0)
    K = lambda nome: f"{nome}_{n}"
    st.subheader("1️⃣ " + t("Leggi il codice a barre (facoltativo)"))
    usa_camera = st.toggle("📷 " + t("Usa la fotocamera del telefono"), key=K("usa_camera"))
    foto_codice = st.camera_input(t("Inquadra il codice a barre e scatta"), key=K("camera")) if usa_camera else None
    foto_file = st.file_uploader(t("…oppure carica una foto del codice"), type=["jpg", "jpeg", "png"], key=K("file_codice"))
    for sorgente in (foto_codice, foto_file):
        if sorgente is not None:
            dati_img = sorgente.getvalue()
            impronta = hash(dati_img)
            if st.session_state.get(K("ultima_foto")) != impronta:
                st.session_state[K("ultima_foto")] = impronta
                letto = leggi_foto(dati_img)
                if letto.get("ean"):
                    st.session_state[K("codice")] = letto["ean"]
                    st.session_state[K("cercato")] = None       # forza la ricerca
                    if letto.get("scadenza"):                    # i QR GS1 possono contenere la scadenza
                        st.session_state[K("scad")] = date.fromisoformat(letto["scadenza"])
                        st.session_state[K("senza_scad")] = False
                        st.session_state[K("scad_letta")] = letto["scadenza"]
                    if letto.get("lotto"):
                        st.session_state[K("note")] = t("lotto") + " " + letto["lotto"]
                    st.session_state[K("qr")] = letto if letto.get("link") else None
                elif letto.get("testo"):
                    st.session_state[K("qr")] = letto
                else:
                    st.session_state[K("codice_non_letto")] = True
    if st.session_state.pop(K("codice_non_letto"), False):
        st.warning(t("Non riesco a leggere il codice dalla foto. Riprova più vicino e con più luce, oppure scrivi i numeri qui sotto."))
    qr = st.session_state.get(K("qr"))
    if qr:
        st.info(t("QR letto: {testo}", testo=qr.get("link") or qr["testo"][:200]))
        if qr.get("link"):
            st.link_button(t("Apri il link del QR"), qr["link"])
        if not qr.get("ean"):
            st.warning(t("Il QR non contiene un codice a barre del prodotto: scrivi il codice o il nome."))
    if st.session_state.get(K("scad_letta")):
        st.success("📅 " + t("Ho letto anche la scadenza dal codice: controllala."))
    codice = st.text_input(t("Codice a barre (i numeri sotto le barre)"), key=K("codice"),
                           placeholder=t("es. 8076809513388")).strip()

    # ricerca: prima nella dispensa, poi su Open Food Facts
    if codice and ean_valido(codice) and st.session_state.get(K("cercato")) != codice:
        st.session_state[K("cercato")] = codice
        gia = [a for a in articoli if a.get("barcode") == codice]
        info = None
        if gia:
            info, origine = dict(gia[-1]), "dispensa"
        else:
            with st.spinner(t("Cerco il prodotto su Open Food Facts...")):
                grezzo = cerca_open_food_facts(codice)
            info = interpreta_prodotto(grezzo, lingua()) if grezzo and "errore" not in grezzo else grezzo
            origine = "off"
        st.session_state[K("origine")] = origine if info and "errore" not in info else ("errore" if info else "nontrovato")
        if info and "errore" not in info:
            st.session_state[K("nome")] = info.get("nome", "")
            st.session_state[K("marca")] = info.get("marca", "")
            if info.get("formato_valore"):
                st.session_state[K("fval")] = float(info["formato_valore"])
                st.session_state[K("funita")] = info.get("formato_unita") or "pz"
            st.session_state[K("allergeni")] = [a for a in (info.get("allergeni") or [])]
            st.session_state[K("tracce")] = [a for a in (info.get("tracce") or [])]
            st.session_state[K("senza_glutine")] = bool(info.get("senza_glutine"))
            st.session_state[K("ingredienti")] = info.get("ingredienti", "")
            st.session_state[K("immagine")] = info.get("immagine", "")
            st.session_state[K("noti")] = bool(info.get("allergeni_noti"))
            st.session_state[K("categoria")] = info.get("categoria", "")
            st.session_state[K("extra")] = info.get("extra", {})
            st.session_state[K("info")] = dict({k: v for k, v in info.items() if k != "quantita"}, barcode=codice)
    elif codice and not ean_valido(codice):
        st.error(t("Il codice non sembra corretto (di solito ha 13 numeri). Controlla le cifre."))

    origine = st.session_state.get(K("origine"))
    if origine == "dispensa":
        st.success("✅ " + t("Prodotto già presente in dispensa: ho copiato nome, foto e allergeni."))
    elif origine == "off":
        st.success("✅ " + t("Prodotto trovato su Open Food Facts. Controlla i dati e completa quantità e scadenza."))
    elif origine == "nontrovato":
        st.info(t("Prodotto non trovato nel database: compila i dati a mano (e aggiungi una foto)."))
    elif origine == "errore":
        st.warning(t("Non riesco a contattare Open Food Facts adesso. Compila a mano o riprova."))

    scheda = st.session_state.get(K("info"))
    if scheda and origine in ("off", "dispensa"):
        with st.expander("📋 " + t("Informazioni trovate sul prodotto"), expanded=True):
            mostra_scheda(scheda, mie)

    st.subheader("2️⃣ " + t("Dati del prodotto"))
    for chiave, valore in (("nome", ""), ("marca", ""), ("quant", 1.0), ("fval", 0.0), ("funita", "g"),
                           ("allergeni", []), ("tracce", []), ("senza_glutine", False), ("ingredienti", ""),
                           ("note", ""), ("senza_scad", False), ("noti", False), ("immagine", ""),
                           ("categoria", ""), ("extra", {})):
        st.session_state.setdefault(K(chiave), valore)
    st.session_state.setdefault(K("scad"), aggiungi_mesi(data_oggi, 6))

    a1, a2 = st.columns(2)
    nome = a1.text_input(t("Nome del prodotto *"), key=K("nome"))
    marca = a2.text_input(t("Marca"), key=K("marca"))
    categoria = st.text_input(t("Categoria"), key=K("categoria"))
    b1, b2, b3 = st.columns(3)
    quant = b1.number_input(t("Quante unità hai? *"), min_value=0.0, step=1.0, key=K("quant"),
                            help=t("Quanti pacchi, bottiglie, barattoli..."))
    fval = b2.number_input(t("Contenuto di ogni unità"), min_value=0.0, step=10.0, key=K("fval"),
                           help=t("Es. 500 (se è un pacco da 500 g). Lascia 0 se non serve."))
    funita = b3.selectbox(t("Unità del contenuto"), UNITA_CONTENUTO, key=K("funita"))
    d1, d2 = st.columns([2, 1])
    senza_scad = d2.checkbox(t("Senza scadenza"), key=K("senza_scad"))
    scad = d1.date_input(t("Scadenza"), key=K("scad"), format="DD/MM/YYYY", disabled=senza_scad)

    with st.expander("🌾 " + t("Allergeni e ingredienti")):
        allergeni = st.multiselect(t("Contiene"), ELENCO_ALLERGENI, key=K("allergeni"), format_func=t_all)
        tracce = st.multiselect(t("Può contenere tracce di"), ELENCO_ALLERGENI, key=K("tracce"), format_func=t_all)
        senza_glutine = st.checkbox(t("Etichettato senza glutine"), key=K("senza_glutine"))
        noti = st.checkbox(t("Ho controllato l'etichetta: gli allergeni indicati sono completi"), key=K("noti"))
        ingredienti = st.text_area(t("Ingredienti"), key=K("ingredienti"), height=90)
    with st.expander("📷 " + t("Foto del prodotto")):
        if st.session_state.get(K("immagine")):
            st.image(src_sicuro(st.session_state[K("immagine")]), width=140)
        foto_prod = st.file_uploader(t("Carica o scatta una foto (sostituisce quella attuale)"),
                                     type=["jpg", "jpeg", "png"], key=K("foto_prod"))
    note = st.text_input(t("Note (facoltative)"), key=K("note"), placeholder=t("es. aperto, aprire dopo il 10"))

    if st.button("💾 " + t("Salva in dispensa"), type="primary", width="stretch"):
        if not nome.strip():
            st.error(t("Scrivi il nome del prodotto."))
        elif quant <= 0:
            st.error(t("Indica quante unità hai (almeno 1)."))
        else:
            immagine = foto_a_data_uri(foto_prod.getvalue()) if foto_prod is not None else st.session_state.get(K("immagine"), "")
            riga = {
                "id": uuid.uuid4().hex[:10], "barcode": codice if ean_valido(codice) else "",
                "nome": nome.strip(), "marca": marca.strip(), "quantita": float(quant),
                "formato_valore": float(fval) if fval else None, "formato_unita": funita if fval else None,
                "scadenza": None if senza_scad else scad.isoformat(),
                "immagine": immagine, "allergeni": allergeni, "tracce": tracce,
                "senza_glutine": bool(senza_glutine), "allergeni_noti": bool(noti or allergeni),
                "ingredienti": ingredienti.strip(), "note": note.strip(),
                "categoria": categoria.strip(), "extra": st.session_state.get(K("extra"), {}),
                "aggiunto_da": utente.strip(), "aggiunto_il": datetime.now().isoformat(timespec="seconds"),
            }
            try:
                salva(lambda d: d.setdefault("articoli", []).append(riga), f"Aggiunto {riga['nome']}")
                st.session_state["messaggio"] = "✅ " + t("{nome} aggiunto alla dispensa.", nome=riga["nome"])
                st.session_state["n_form"] = n + 1
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))

# ---------------------------------------------------------------------
# GESTISCI
# ---------------------------------------------------------------------
with tab_gestisci:
    st.subheader(t("Modifica quantità, scadenze e note"))
    st.caption(t("Cambia i valori nella tabella, spunta 🗑️ per eliminare, poi premi Salva modifiche."))
    if not articoli:
        st.info(t("Non c'è ancora nulla da gestire."))
    else:
        df = pd.DataFrame([{
            "id": r["id"], "🗑️": False, "Prodotto": r.get("nome", ""), "Unità": float(r.get("quantita") or 0),
            "Contenuto": r.get("formato_valore") or 0.0, "Misura": r.get("formato_unita") or "g",
            "Scadenza": date.fromisoformat(r["scadenza"]) if r.get("scadenza") else None,
            "Note": r.get("note", ""),
        } for r in sorted(articoli, key=lambda r: r.get("scadenza") or "9999")]).set_index("id")
        modificata = st.data_editor(
            df, hide_index=True, width="stretch", key="editor",
            column_config={
                "🗑️": st.column_config.CheckboxColumn("🗑️", width="small"),
                "Prodotto": st.column_config.TextColumn(t("Prodotto")),
                "Unità": st.column_config.NumberColumn(t("Unità"), min_value=0.0, step=1.0),
                "Contenuto": st.column_config.NumberColumn(t("Contenuto"), min_value=0.0),
                "Misura": st.column_config.SelectboxColumn(t("Misura"), options=UNITA_CONTENUTO),
                "Scadenza": st.column_config.DateColumn(t("Scadenza"), format="DD/MM/YYYY"),
                "Note": st.column_config.TextColumn(t("Note")),
            })
        if st.button("💾 " + t("Salva modifiche"), type="primary"):
            try:
                salva(lambda d: applica_modifiche(d, modificata), "Modifiche alla dispensa")
                st.session_state["messaggio"] = "✅ " + t("Modifiche salvate.")
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))
        st.caption(t("Se metti 0 unità il prodotto viene tolto dalla dispensa (finito)."))
        elenco = pd.DataFrame([{k: (", ".join(v) if isinstance(v, list) else v)
                                for k, v in r.items() if k != "immagine"} for r in articoli])
        st.download_button("⬇️ " + t("Scarica l'elenco (CSV)"), elenco.to_csv(index=False).encode("utf-8"),
                           "dispensa.csv", "text/csv")

# ---------------------------------------------------------------------
# INFO
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# UTENTI (solo amministratore)
# ---------------------------------------------------------------------
if tab_utenti is not None:
    with tab_utenti:
        st.subheader(t("Utenti e password"))
        st.caption(t("Ogni persona ha la sua password e la sua dispensa separata. Tu non vedi le dispense degli altri."))
        if sess["uid"] == "prova":
            st.info(t("Modalità prova: gli utenti non vengono conservati."))
        nuova = st.session_state.get("pw_mostrata")
        if nuova:
            st.success(t("Password per {nome}: copiala e mandala alla persona (per esempio su WhatsApp). Non verrà mostrata più.",
                         nome=nuova["nome"]))
            st.code(nuova["password"], language=None)
            if st.button(t("Ho copiato la password")):
                st.session_state.pop("pw_mostrata", None)
                st.rerun()
        with st.form("nuovo_utente", clear_on_submit=True):
            nome_nuovo = st.text_input(t("Nome della persona"))
            lingua_nuovo = st.selectbox(t("Lingua della persona"), list(LINGUE), index=list(LINGUE).index(lingua()),
                                        format_func=lambda c: LINGUE[c])
            crea = st.form_submit_button("➕ " + t("Crea utente e genera password"))
        if crea:
            if not nome_nuovo.strip():
                st.error(t("Scrivi il nome della persona."))
            else:
                pw = genera_password({u.get("hash") for u in leggi_utenti()})
                nuovo = {"id": uuid.uuid4().hex[:8], "nome": nome_nuovo.strip(), "hash": hash_password(pw),
                         "attivo": True, "creato": adesso().isoformat(timespec="minutes"), "ultimo_accesso": None,
                         "lingua": lingua_nuovo}
                try:
                    salva_file("utenti.json", lambda d: d.setdefault("utenti", []).append(nuovo),
                               f"Nuovo utente {nuovo['nome']}")
                    st.session_state["pw_mostrata"] = {"nome": nuovo["nome"], "password": pw}
                    st.rerun()
                except Exception as e:
                    st.error(t("Non sono riuscito a salvare: {e}", e=e))
        st.divider()
        elenco = leggi_utenti()
        if not elenco:
            st.info(t("Non hai ancora creato nessun utente."))
        for u in elenco:
            with st.container(border=True):
                attivo = u.get("attivo", True)
                ultimo = u.get("ultimo_accesso")
                st.markdown(f"**{u['nome']}** · " + ("✅ " + t("Attivo") if attivo else "⛔ " + t("Bloccato")))
                st.caption(t("Ultimo accesso:") + " " + (ultimo.replace("T", " ") if ultimo else t("mai")))
                b1, b2, b3 = st.columns(3)
                if b1.button("🔑 " + t("Nuova password"), key=f"np_{u['id']}"):
                    pw = genera_password({x.get("hash") for x in elenco})

                    def cambia(d, uid=u["id"], h=hash_password(pw)):
                        for x in d.get("utenti", []):
                            if x["id"] == uid:
                                x["hash"] = h
                                x["attivo"] = True
                    try:
                        salva_file("utenti.json", cambia, f"Nuova password per {u['nome']}")
                        st.session_state["pw_mostrata"] = {"nome": u["nome"], "password": pw}
                        st.rerun()
                    except Exception as e:
                        st.error(t("Non sono riuscito a salvare: {e}", e=e))
                if b2.button("⛔ " + t("Blocca") if attivo else "✅ " + t("Riattiva"), key=f"bl_{u['id']}"):
                    def blocca(d, uid=u["id"], val=not attivo):
                        for x in d.get("utenti", []):
                            if x["id"] == uid:
                                x["attivo"] = val
                    try:
                        salva_file("utenti.json", blocca, f"{'Riattivato' if not attivo else 'Bloccato'} {u['nome']}")
                        st.rerun()
                    except Exception as e:
                        st.error(t("Non sono riuscito a salvare: {e}", e=e))
                with b3.popover("🗑️ " + t("Elimina")):
                    st.write(t("Elimina {nome} e la sua dispensa. Non si può annullare.", nome=u["nome"]))
                    if st.button(t("Sì, elimina"), key=f"el_{u['id']}"):
                        try:
                            salva_file("utenti.json",
                                       lambda d, uid=u["id"]: d.__setitem__("utenti", [x for x in d.get("utenti", []) if x["id"] != uid]),
                                       f"Eliminato {u['nome']}")
                            archivio.elimina(f"dispense/{u['id']}.json", f"Eliminata dispensa di {u['nome']}")
                            carica_dati.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(t("Non sono riuscito a eliminare: {e}", e=e))

# ---------------------------------------------------------------------
# INFO
# ---------------------------------------------------------------------
with tab_info:
    st.markdown(t("""**Come funzionano i colori**
- 🟢 verde: più di 2 mesi alla scadenza
- 🟠 arancione: la scadenza è entro 2 mesi
- 🔴 rosso: la scadenza è entro 1 mese
- ⚫ scuro: già scaduto"""))
    st.markdown(t("""**Allergeni: leggi sempre l'etichetta.** I dati dei prodotti arrivano da *Open Food Facts*, un database compilato dagli utenti: possono essere incompleti o non aggiornati. L'app ti aiuta, ma non sostituisce la lettura dell'etichetta sulla confezione, soprattutto in caso di allergia o celiachia."""))
    st.markdown(t("""**Come aggiungere un prodotto:** scheda ➕ Aggiungi, fotografa il codice a barre (o scrivi i numeri), controlla i dati, scrivi quante unità hai e la scadenza."""))
    st.markdown(t("""**La tua dispensa è solo tua:** ogni persona ha la sua password e vede solo i propri prodotti. Con "Esci" chiudi l'accesso su questo telefono."""))
    st.markdown(t("""**Cercare online:** nella scheda Dispensa, sotto i prodotti, scegli "Dettagli prodotto": trovi valori nutrizionali, ingredienti e collegamenti per cercare prezzi, offerte e recensioni su Google, Amazon e Open Prices."""))
    st.markdown(t("Dati dei prodotti: Open Food Facts (licenza ODbL)."))
    if e_admin:
        st.markdown(t("**Per l'amministratore: impostazioni (Streamlit → Settings → Secrets)**"))
        st.code('admin_password = "scegli-una-password-lunga"\n\n[github]\ntoken = "il_tuo_token"\n'
                'repo = "TuoNome/dispensa-dati"', language=None)

# >>> FINE DEL FILE: se vedi questa riga, il codice è completo <<<
