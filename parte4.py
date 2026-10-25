

# ---------------------------------------------------------------------
# AGGIUNGI
# ---------------------------------------------------------------------
with tab_aggiungi:
    n = st.session_state.setdefault("n_form", 0)
    K = lambda nome: f"{nome}_{n}"
    st.session_state.setdefault(K("per_chi"), st.session_state.get("ultimo_per_chi", "adulti"))
    per_chi_sel = st.radio("👪 " + t("Per chi è il prodotto?"), list(CATEGORIE), format_func=nome_cat,
                           horizontal=True, key=K("per_chi"))
    st.subheader("1️⃣ " + t("Foto del prodotto"))
    st.session_state[K("foto_pronta")] = campo_foto(K("fotoprod"))      # unico punto per la foto: scontornata e addrizzata, finisce nella home
    st.subheader("2️⃣ " + t("Codice a barre (scrivilo a mano, facoltativo)"))
    codice = st.text_input(t("Codice a barre (i numeri sotto le barre)"), key=K("codice"),
                           placeholder=t("es. 8076809513388")).strip()

    # ricerca: prima nella dispensa, poi su Open Food Facts
    if codice and ean_valido(codice) and st.session_state.get(K("cercato")) != (codice, per_chi_sel):
        st.session_state[K("cercato")] = (codice, per_chi_sel)
        gia = [a for a in articoli if a.get("barcode") == codice]
        info = None
        if gia:
            info, origine = dict(gia[-1]), "dispensa"
        else:
            with st.spinner(t("Cerco il prodotto su Open Food Facts...")):
                grezzo = cerca_prodotto(codice, per_chi_sel)
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
            st.session_state[K("info")] = dict({k: v for k, v in info.items() if k != "quantita"}, barcode=codice, per_chi=per_chi_sel)
            avviso_inserimento(st.session_state[K("info")], per_chi_sel, allergie_di(per_chi_sel), K("avviso_mostrato") + codice)
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
            mostra_scheda(scheda, allergie_di(per_chi_sel))

    st.subheader("3️⃣ " + t("Dati del prodotto"))
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
    st.session_state.setdefault(K("posto"), st.session_state.get("ultimo_posto", "dispensa"))
    posto = st.selectbox(t("Dove lo metti?"), list(POSTI), format_func=nome_posto_scelta, key=K("posto"))
    posto_altro = st.text_input(t("Scrivi dove lo metti"), key=K("posto_altro")) if posto == "altro" else ""
    piu_scad = st.checkbox("🗓️ " + t("Ho confezioni con scadenze diverse"), key=K("piu_scad"))
    b1, b2, b3 = st.columns(3)
    quant = b1.number_input(t("Quante unità hai? *"), min_value=0.0, step=1.0, key=K("quant"),
                            help=t("Quanti pacchi, bottiglie, barattoli..."), disabled=piu_scad)
    fval = b2.number_input(t("Contenuto di ogni unità"), min_value=0.0, step=10.0, key=K("fval"),
                           help=t("Es. 500 (se è un pacco da 500 g). Lascia 0 se non serve."))
    funita = b3.selectbox(t("Unità del contenuto"), UNITA_CONTENUTO, key=K("funita"))
    d1, d2 = st.columns([2, 1])
    senza_scad = d2.checkbox(t("Senza scadenza"), key=K("senza_scad"), disabled=piu_scad)
    scad = d1.date_input(t("Scadenza"), key=K("scad"), format="DD/MM/YYYY", disabled=senza_scad or piu_scad)
    lotti = []
    if piu_scad:
        st.caption(t("Scrivi per ogni scadenza quante confezioni scadono in quella data."))
        n_lotti = int(st.number_input(t("Quante scadenze diverse hai?"), min_value=2, max_value=10, value=2, step=1, key=K("n_lotti")))
        for i in range(n_lotti):
            l1, l2 = st.columns([1, 2])
            q_i = l1.number_input(f"{t('Unità')} ({i + 1})", min_value=0.0, step=1.0, value=1.0, key=K(f"lq_{i}"))
            d_i = l2.date_input(f"{t('Scadenza')} ({i + 1})", value=aggiungi_mesi(data_oggi, 3 + 3 * i), format="DD/MM/YYYY", key=K(f"ld_{i}"))
            lotti.append((q_i, d_i))

    with st.expander(("🌾 " + t("Allergeni e ingredienti")) if per_chi_sel != "animali" else ("🥣 " + t("Composizione"))):
        if per_chi_sel != "animali":
            allergeni = st.multiselect(t("Contiene"), ELENCO_ALLERGENI, key=K("allergeni"), format_func=t_all)
            tracce = st.multiselect(t("Può contenere tracce di"), ELENCO_ALLERGENI, key=K("tracce"), format_func=t_all)
            senza_glutine = st.checkbox(t("Etichettato senza glutine"), key=K("senza_glutine"))
            noti = st.checkbox(t("Ho controllato l'etichetta: gli allergeni indicati sono completi"), key=K("noti"))
        else:
            allergeni, tracce, senza_glutine, noti = [], [], False, False
        ingredienti = st.text_area(t("Ingredienti"), key=K("ingredienti"), height=90)
    note = st.text_input(t("Note (facoltative)"), key=K("note"), placeholder=t("es. aperto, aprire dopo il 10"))

    if st.button("💾 " + t("Salva in dispensa"), type="primary", width="stretch"):
        if not nome.strip():
            st.error(t("Scrivi il nome del prodotto."))
        elif not piu_scad and quant <= 0:
            st.error(t("Indica quante unità hai (almeno 1)."))
        elif piu_scad and not any(q > 0 for q, _ in lotti):
            st.error(t("Indica almeno una scadenza con almeno 1 unità."))
        else:
            immagine = st.session_state.get(K("foto_pronta")) or st.session_state.get(K("immagine"), "")
            base = {
                "barcode": codice if ean_valido(codice) else "",
                "nome": nome.strip(), "marca": marca.strip(),
                "formato_valore": float(fval) if fval else None, "formato_unita": funita if fval else None,
                "immagine": immagine, "allergeni": allergeni, "tracce": tracce,
                "senza_glutine": bool(senza_glutine), "allergeni_noti": bool(noti or allergeni),
                "ingredienti": ingredienti.strip(), "note": note.strip(),
                "categoria": categoria.strip(), "extra": st.session_state.get(K("extra"), {}), "per_chi": per_chi_sel,
                "posto": posto, "posto_altro": posto_altro.strip() if posto == "altro" else "",
                "aggiunto_da": utente.strip(), "aggiunto_il": datetime.now().isoformat(timespec="seconds"),
            }
            if piu_scad:                      # una riga per ogni scadenza (se due righe hanno la stessa data, le unisco)
                per_data = {}
                for q, d_ in lotti:
                    if q > 0:
                        per_data[d_.isoformat()] = per_data.get(d_.isoformat(), 0.0) + float(q)
                parti = sorted(per_data.items(), key=lambda x: x[0])
                parti = [(q, d_) for d_, q in parti]
            else:
                parti = [(float(quant), None if senza_scad else scad.isoformat())]
            nuove = [dict(base, id=uuid.uuid4().hex[:10], quantita=q, scadenza=d_) for q, d_ in parti]
            try:
                salva(lambda d: (d.setdefault("articoli", []).extend(nuove), togli_da_spesa(d, nuove)), f"Aggiunto {base['nome']}")
                st.session_state["messaggio"] = "✅ " + (t("{nome} aggiunto alla dispensa.", nome=base["nome"]) if len(nuove) == 1
                                                         else t("{nome}: aggiunte {n} scadenze.", nome=base["nome"], n=len(nuove)))
                st.session_state["n_form"] = n + 1
                st.session_state["ultimo_per_chi"] = per_chi_sel
                st.session_state["ultimo_posto"] = posto
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
            "id": r["id"], "🗑️": False, "Prodotto": r.get("nome", ""), "Per chi": nome_cat(categoria_di(r)), "Posto": nome_posto_scelta(posto_di(r)), "Unità": float(r.get("quantita") or 0),
            "Contenuto": r.get("formato_valore") or 0.0, "Misura": r.get("formato_unita") or "g",
            "Scadenza": date.fromisoformat(r["scadenza"]) if r.get("scadenza") else None,
            "Note": r.get("note", ""),
        } for r in sorted(articoli, key=lambda r: r.get("scadenza") or "9999")]).set_index("id")
        modificata = st.data_editor(
            df, hide_index=True, width="stretch", key="editor",
            column_config={
                "🗑️": st.column_config.CheckboxColumn("🗑️", width="small"),
                "Prodotto": st.column_config.TextColumn(t("Prodotto")),
                "Per chi": st.column_config.SelectboxColumn(t("Per chi"), options=[nome_cat(c) for c in CATEGORIE]),
                "Posto": st.column_config.SelectboxColumn(t("Posto"), options=[nome_posto_scelta(k) for k in POSTI]),
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
        st.caption(t("Al primo accesso la persona può scegliere una password sua."))
        if sess["uid"] == "prova":
            st.info(t("Modalità prova: gli utenti non vengono conservati."))

        def _link_app():
            """Indirizzo pubblico dell'app (lo stesso per tutti): scheme + dominio della pagina aperta."""
            from urllib.parse import urlsplit
            try:
                u = urlsplit(str(st.context.url))
                if u.scheme and u.netloc:
                    return f"{u.scheme}://{u.netloc}"
            except Exception:
                pass
            try:
                h = st.context.headers
                host = h.get("X-Forwarded-Host") or h.get("Host")
                if host:
                    proto = h.get("X-Forwarded-Proto") or ("http" if host.startswith(("localhost", "127.")) else "https")
                    return f"{proto}://{host}"
            except Exception:
                pass
            return ""

        link_pubblico = _link_app()
        if not link_pubblico:
            link_pubblico = st.text_input("🔗 " + t("Incolla qui il link della tua app"), key="link_app_manuale").strip()
        if link_pubblico:
            st.markdown("**🔗 " + t("Link da mandare") + "**")
            st.code(link_pubblico, language=None)
            st.caption(t("È sempre lo stesso per tutte le persone: cambia solo la password. Chi apre il link scrive la sua password e tocca Entra."))
        nuova = st.session_state.get("pw_mostrata")
        if nuova:
            st.success(t("Password per {nome}: copiala e mandala alla persona (per esempio su WhatsApp). Non verrà mostrata più.",
                         nome=nuova["nome"]))
            st.code(nuova["password"], language=None)
            if link_pubblico:
                st.markdown("**📨 " + t("Messaggio pronto da copiare e mandare") + "**")
                st.code(t("Ciao {nome}! Ecco l'app Dispensa: {link}\nApri il link, scrivi questa password e tocca Entra:\n{password}\nAl primo accesso potrai scegliere una password tua.",
                          nome=nuova["nome"], link=link_pubblico, password=nuova["password"]), language=None)
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
                         "lingua": lingua_nuovo, "deve_cambiare": True}
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
                if u.get("deve_cambiare"):
                    st.caption("🔑 " + t("Non ha ancora scelto una sua password."))
                b1, b2, b3 = st.columns(3)
                if b1.button("🔑 " + t("Nuova password"), key=f"np_{u['id']}"):
                    pw = genera_password({x.get("hash") for x in elenco})

                    def cambia(d, uid=u["id"], h=hash_password(pw)):
                        for x in d.get("utenti", []):
                            if x["id"] == uid:
                                x["hash"] = h
                                x["attivo"] = True
                                x["deve_cambiare"] = True
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
# MESSAGGI / SUGGERIMENTI
# ---------------------------------------------------------------------
with tab_spesa:
    scheda_spesa()

with tab_messaggi:
    scheda_messaggi()

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
    st.markdown(t("**Pulsanti degli allergeni:** i prodotti che possono dare allergie hanno un pulsante giallo con il nome dell'allergene (per esempio Glutine). Toccalo: si apre una schermata con la composizione e gli ingredienti del prodotto. Lo stesso avviso compare subito quando inserisci un prodotto."))
    st.markdown(t("""**La tua dispensa è solo tua:** ogni persona ha la sua password e vede solo i propri prodotti. Con "Esci" chiudi l'accesso su questo telefono."""))
    st.markdown(t("""**Cercare online:** nella scheda Dispensa, sotto i prodotti, scegli "Dettagli prodotto": trovi valori nutrizionali, ingredienti e collegamenti per cercare prezzi, offerte e recensioni su Google, Amazon e Open Prices."""))
    st.markdown(t("""**Adulti, neonati, animali:** quando aggiungi un prodotto scegli per chi è. Nella scheda Dispensa trovi tre sezioni separate; le allergie del neonato si impostano nel menu a sinistra. Per neonati e animali i dati arrivano anche da Open Products Facts e Open Pet Food Facts, che hanno meno prodotti."""))
    st.markdown(t("""**Suggerimenti e richieste:** nella scheda Suggerimenti puoi scrivere all'amministratore un'idea, una richiesta di novità o un problema. Se risponde, vedi la risposta nella stessa scheda."""))
    st.markdown(t("""**La tua password:** puoi cambiarla quando vuoi dal menu a sinistra, alla voce Cambia password."""))
    st.markdown(t("Dati dei prodotti: Open Food Facts (licenza ODbL)."))
    if e_admin:
        st.markdown(t("**Per l'amministratore: impostazioni (Streamlit → Settings → Secrets)**"))
        st.code('admin_password = "scegli-una-password-lunga"\n\n[github]\ntoken = "il_tuo_token"\n'
                'repo = "TuoNome/dispensa-dati"', language=None)

# >>> FINE DEL FILE: se vedi questa riga, il codice è completo <<<
