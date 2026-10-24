

# =====================================================================
# PARTE 4 - PAGINA
# =====================================================================
st.set_page_config(page_title=t("La nostra dispensa"), page_icon="🥫", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

archivio = crea_archivio()
data_oggi = oggi()
configurato = bool(password_admin())
HERO = (f"<div class='hero'><h1>🥫 {t('La nostra dispensa')}</h1>"
        f"<p>{t('Scorte, scadenze e allergeni sempre sotto controllo')}</p></div>")


def leggi_utenti():
    try:
        return carica_dati(archivio, "utenti.json").get("utenti", [])
    except Exception as e:
        st.error(t("Non riesco a leggere i dati: {e}", e=e))
        st.stop()


def esci():
    for k in ("sess", "percorso", "k_provato", "pw_mostrata"):
        st.session_state.pop(k, None)
    st.query_params.clear()


def entra(accesso, ricorda_pw=None):
    st.session_state["sess"] = accesso
    st.session_state["percorso"] = f"dispense/{accesso['uid']}.json"
    if ricorda_pw:
        st.query_params["k"] = ricorda_pw          # il link dell'app ricorda l'accesso su questo telefono
    utenti = leggi_utenti() if accesso["uid"] != "prova" else []
    registra_accesso(accesso["uid"], utenti)
    # lingua: quella salvata dalla persona, altrimenti quella scelta da chi gestisce, altrimenti quella attuale
    try:
        salvata = carica_dati(archivio, st.session_state["percorso"]).get("lingua")
    except Exception:
        salvata = None
    iniziale = next((u.get("lingua") for u in utenti if u["id"] == accesso["uid"]), None)
    if (salvata or iniziale) in LINGUE:
        st.session_state["lang"] = salvata or iniziale


def selettore_lingua(posizione):
    """Menu per cambiare lingua. Dopo l'accesso la scelta resta salvata per quella persona."""
    codici = list(LINGUE)
    attuale = lingua() if lingua() in LINGUE else "it"
    scelta = st.selectbox("🌐 Lingua / Language", codici, index=codici.index(attuale),
                          format_func=lambda c: LINGUE[c], key="sel_lingua_" + posizione)
    if scelta != attuale:
        st.session_state["lang"] = scelta
        if st.session_state.get("sess") and st.session_state["sess"].get("uid") != "prova":
            try:
                salva(lambda d: d.__setitem__("lingua", scelta), "Lingua")
            except Exception:
                pass
        st.rerun()


# ---------------------------------------------------------------------
# ACCESSO
# ---------------------------------------------------------------------
sess = st.session_state.get("sess")
if sess and sess.get("uid") != "prova" and not sessione_valida(sess, leggi_utenti()):
    esci()
    sess = None
    st.session_state["avviso_login"] = "La tua password non è più valida. Chiedi una nuova password a chi gestisce la dispensa."

if not sess:
    st.markdown(HERO, unsafe_allow_html=True)
    if not configurato:
        st.warning("Prima configurazione: manca la password dell'amministratore.")
        st.markdown("In Streamlit apri **Settings → Secrets** e scrivi (con la tua password):\n"
                    "```\nadmin_password = \"scegli-una-password-lunga\"\n\n[github]\n"
                    "token = \"il_tuo_token\"\nrepo = \"TuoNome/dispensa-dati\"\n```\n"
                    "Per ora puoi solo provare l'app: i dati NON vengono conservati.")
        if st.button("Prova l'app senza salvare i dati"):
            st.session_state["sess"] = {"uid": "prova", "nome": "Prova", "admin": True, "h": ""}
            st.session_state["percorso"] = "dispense/prova.json"
            st.rerun()
        st.stop()
    if st.session_state.get("avviso_login"):
        st.warning(t(st.session_state.pop("avviso_login")))
    # accesso automatico dal link salvato su questo telefono
    k = st.query_params.get("k")
    if k and not st.session_state.get("k_provato"):
        st.session_state["k_provato"] = True
        if not troppi_tentativi():
            accesso = cerca_accesso(k, leggi_utenti())
            if accesso:
                entra(accesso)
                st.rerun()
            registro_errori().append(time.time())
        st.query_params.clear()
        st.warning(t("L'accesso salvato non è più valido: scrivi la tua password."))
    selettore_lingua("accesso")
    st.caption(t("Tieni sotto controllo scorte, scadenze e allergeni: fotografa il codice a barre e l'app compila i dati del prodotto."))
    with st.form("accesso"):
        pw = st.text_input(t("La tua password personale"), type="password")
        ricorda = st.checkbox(t("Ricordami su questo telefono"), value=True)
        invio = st.form_submit_button(t("Entra"), type="primary")
    if invio:
        if troppi_tentativi():
            st.error(t("Troppi tentativi sbagliati. Aspetta un minuto e riprova."))
        else:
            accesso = cerca_accesso(pw, leggi_utenti())
            if accesso:
                entra(accesso, pw if ricorda else None)
                st.rerun()
            registro_errori().append(time.time())
            time.sleep(1)
            st.error(t("Password non corretta."))
    st.caption(t("Non hai una password? Chiedila a chi gestisce la dispensa."))
    st.stop()

# ---------------------------------------------------------------------
# DISPENSA DELLA PERSONA CHE HA FATTO L'ACCESSO
# ---------------------------------------------------------------------
utente = sess["nome"]
e_admin = bool(sess.get("admin"))
try:
    dati = carica_dati(archivio, st.session_state["percorso"])
except Exception as e:
    st.error(t("Non riesco a leggere i dati: {e}", e=e))
    st.stop()
articoli = dati.get("articoli", [])

with st.sidebar:
    st.header("👤 " + (t("Amministratore") if e_admin and utente == "Amministratore" else utente))
    if e_admin:
        st.caption(t("Amministratore"))
    if st.button(t("Esci")):
        esci()
        st.rerun()
    if st.button("❓ " + t("Come si usa")):
        st.session_state["riapri_intro"] = True
        st.rerun()
    selettore_lingua("barra")
    st.header("🌾 " + t("Allergie"))
    mie = st.multiselect(t("Segnala i prodotti che contengono:"), ELENCO_ALLERGENI, key="mie_allergie",
                         default=[a for a in dati.get("allergie", []) if a in ELENCO_ALLERGENI],
                         format_func=t_all)
    if sorted(mie) != sorted(dati.get("allergie", [])):
        try:
            salva(lambda d: d.__setitem__("allergie", list(mie)), "Allergie")
        except Exception:
            pass
    solo_sicuri = st.checkbox(t("Mostra solo prodotti sicuri per me"), value=False,
                              help=t("Nasconde i prodotti con questi allergeni e quelli senza informazioni sugli allergeni."))
    st.divider()
    if archivio.permanente:
        st.success("💾 " + t("Dati salvati su GitHub"))
    else:
        st.warning("⚠️ " + t("Modalità prova: i dati si cancellano quando l'app si riavvia. Collega GitHub (vedi scheda Info)."))
    if st.button("🔄 " + t("Aggiorna")):
        carica_dati.clear()
        st.rerun()

# --- intestazione e avvisi ---
st.markdown(HERO, unsafe_allow_html=True)

# --- breve introduzione (la prima volta, oppure quando si preme "Come si usa") ---
if st.session_state.get("riapri_intro") or not (dati.get("intro_vista") or st.session_state.get("intro_chiusa")):
    with st.container(border=True):
        st.markdown(t("""**Benvenuto nella tua dispensa!**
1. ➕ **Aggiungi** i prodotti: fotografa il codice a barre (o il QR) e l'app compila nome, ingredienti e allergeni.
2. 📅 Scrivi **quante unità hai** e la **scadenza**.
3. 🟠🔴 L'app ti **avvisa** quando un prodotto scade entro 2 mesi (arancione) o entro 1 mese (rosso).
4. 🌾 Nel menu a sinistra scegli le tue **allergie**: i prodotti a rischio vengono segnalati.
5. 🔍 Apri i **Dettagli** di un prodotto per vedere i valori nutrizionali e cercare prezzi e recensioni online.

La dispensa è solo tua: nessun altro vede i tuoi prodotti."""))
        if st.button(t("Ho capito, iniziamo"), type="primary", key="chiudi_intro"):
            st.session_state["intro_chiusa"] = True
            st.session_state.pop("riapri_intro", None)
            if sess.get("uid") != "prova":
                try:
                    salva(lambda d: d.__setitem__("intro_vista", True), "Intro")
                except Exception:
                    pass
            st.rerun()

con_stato = [(r, *stato_scadenza(r.get("scadenza"), data_oggi)) for r in articoli]
scaduti = sorted([r for r, s, g in con_stato if s == "scaduto"], key=lambda r: r["scadenza"])
rossi = sorted([r for r, s, g in con_stato if s == "rosso"], key=lambda r: r["scadenza"])
arancioni = sorted([r for r, s, g in con_stato if s == "arancione"], key=lambda r: r["scadenza"])

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("Prodotti"), len(articoli))
c2.metric("🟠 " + t("Entro 2 mesi"), len(arancioni))
c3.metric("🔴 " + t("Entro 1 mese"), len(rossi))
c4.metric("⚫ " + t("Scaduti"), len(scaduti))

if scaduti:
    st.markdown(avviso_html("⚫ " + t("Scaduti: da buttare o controllare"), "scaduto", scaduti, data_oggi), unsafe_allow_html=True)
if rossi:
    st.markdown(avviso_html("🔴 " + t("Scadono entro 1 mese"), "rosso", rossi, data_oggi), unsafe_allow_html=True)
if arancioni:
    st.markdown(avviso_html("🟠 " + t("Scadono entro 2 mesi"), "arancione", arancioni, data_oggi), unsafe_allow_html=True)

if st.session_state.get("messaggio"):
    st.success(st.session_state.pop("messaggio"))

_nomi_schede = ["🏠 " + t("Dispensa"), "➕ " + t("Aggiungi"), "✏️ " + t("Gestisci")] + (["👥 " + t("Utenti")] if e_admin else []) + ["ℹ️ " + t("Info")]
_schede = st.tabs(_nomi_schede)
tab_dispensa, tab_aggiungi, tab_gestisci = _schede[0], _schede[1], _schede[2]
tab_utenti = _schede[3] if e_admin else None
tab_info = _schede[-1]

# ---------------------------------------------------------------------
# DISPENSA
# ---------------------------------------------------------------------
with tab_dispensa:
    f1, f2, f3 = st.columns([3, 2, 2])
    cerca = f1.text_input("🔎 " + t("Cerca"), placeholder=t("nome o marca"), label_visibility="collapsed")
    _filtri = {"tutti": "Tutti", "2mesi": "Solo in scadenza (2 mesi)", "1mese": "Solo rossi (1 mese)", "scaduti": "Scaduti"}
    filtro = f2.selectbox(t("Mostra"), list(_filtri), format_func=lambda c: t(_filtri[c]),
                          label_visibility="collapsed")
    _viste = {"schede": "Schede", "tabella": "Tabella"}
    vista = f3.radio(t("Vista"), list(_viste), format_func=lambda c: t(_viste[c]), horizontal=True,
                     label_visibility="collapsed")

    visibili = []
    for r, stato, giorni in con_stato:
        if cerca and cerca.lower() not in (r.get("nome", "") + " " + r.get("marca", "")).lower():
            continue
        if filtro == "2mesi" and stato not in ("arancione", "rosso", "scaduto"):
            continue
        if filtro == "1mese" and stato not in ("rosso", "scaduto"):
            continue
        if filtro == "scaduti" and stato != "scaduto":
            continue
        if solo_sicuri and mie:
            if any(a in mie for a in (r.get("allergeni") or [])) or not (r.get("allergeni_noti") or r.get("allergeni")):
                continue
        visibili.append((r, stato, giorni))
    visibili.sort(key=lambda x: (x[0].get("scadenza") or "9999-12-31"))

    if not articoli:
        st.info(t("La dispensa è vuota. Vai nella scheda ➕ Aggiungi per inserire il primo prodotto."))
    elif not visibili:
        st.info(t("Nessun prodotto corrisponde ai filtri."))
    elif vista == "schede":
        st.markdown("<div class='griglia'>" + "".join(scheda_html(r, data_oggi, mie) for r, _, _ in visibili) + "</div>",
                    unsafe_allow_html=True)
    else:
        tab = pd.DataFrame([{
            t("Foto"): src_sicuro(r.get("immagine") or "") or None,
            t("Prodotto"): r.get("nome", ""), t("Marca"): r.get("marca", ""),
            t("Quantità"): descrivi([r]),
            t("Scadenza"): data_it(r.get("scadenza")), t("Stato"): f"{ICONE[s]} {testo_giorni(s, g)}",
            t("Allergeni"): ", ".join(t_all(a) for a in (r.get("allergeni") or []))
                            or ("—" if r.get("allergeni_noti") else t("non verificati")),
            "_stato": s,
        } for r, s, g in visibili])
        sfondi = {"rosso": "background-color:#ffcdd2", "arancione": "background-color:#ffe0b2",
                  "scaduto": "background-color:#d7ccc8", "ok": "", "nessuna": ""}
        stile = tab.style.apply(lambda riga: [sfondi[riga["_stato"]]] * len(riga), axis=1)
        st.dataframe(stile, hide_index=True, height=min(700, 60 + 72 * len(tab)),
                     column_config={t("Foto"): st.column_config.ImageColumn(t("Foto"), width="small"),
                                    "_stato": None})

    if visibili:
        st.divider()
        _nomi = {r["id"]: r.get("nome", "") + (f" · {r['marca']}" if r.get("marca") else "") for r, _, _ in visibili}
        scelto = st.selectbox("🔍 " + t("Dettagli prodotto"), [""] + list(_nomi),
                              format_func=lambda i: _nomi.get(i, t("Scegli un prodotto")))
        if scelto:
            mostra_scheda(next(r for r in articoli if r["id"] == scelto), mie)

# >>> FINE PARTE 3 di 4: adesso incolla la PARTE 4 qui sotto <<<
