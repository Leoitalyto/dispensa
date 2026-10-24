

# =====================================================================
# PARTE 4 - PAGINA
# =====================================================================
st.set_page_config(page_title="La nostra dispensa", page_icon="🥫", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

archivio = crea_archivio()
data_oggi = oggi()
configurato = bool(password_admin())
HERO = ("<div class='hero'><h1>🥫 La nostra dispensa</h1>"
        "<p>Scorte, scadenze e allergeni sempre sotto controllo</p></div>")


def leggi_utenti():
    try:
        return carica_dati(archivio, "utenti.json").get("utenti", [])
    except Exception as e:
        st.error(f"Non riesco a leggere i dati: {e}")
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
    registra_accesso(accesso["uid"], leggi_utenti() if accesso["uid"] != "prova" else [])


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
        st.warning(st.session_state.pop("avviso_login"))
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
        st.warning("L'accesso salvato non è più valido: scrivi la tua password.")
    with st.form("accesso"):
        pw = st.text_input("La tua password personale", type="password")
        ricorda = st.checkbox("Ricordami su questo telefono", value=True)
        invio = st.form_submit_button("Entra", type="primary")
    if invio:
        if troppi_tentativi():
            st.error("Troppi tentativi sbagliati. Aspetta un minuto e riprova.")
        else:
            accesso = cerca_accesso(pw, leggi_utenti())
            if accesso:
                entra(accesso, pw if ricorda else None)
                st.rerun()
            registro_errori().append(time.time())
            time.sleep(1)
            st.error("Password non corretta.")
    st.caption("Non hai una password? Chiedila a chi gestisce la dispensa.")
    st.stop()

# ---------------------------------------------------------------------
# DISPENSA DELLA PERSONA CHE HA FATTO L'ACCESSO
# ---------------------------------------------------------------------
utente = sess["nome"]
e_admin = bool(sess.get("admin"))
try:
    dati = carica_dati(archivio, st.session_state["percorso"])
except Exception as e:
    st.error(f"Non riesco a leggere i dati: {e}")
    st.stop()
articoli = dati.get("articoli", [])

with st.sidebar:
    st.header(f"👤 {utente}")
    if e_admin:
        st.caption("Amministratore")
    if st.button("Esci"):
        esci()
        st.rerun()
    st.header("🌾 Allergie")
    mie = st.multiselect("Segnala i prodotti che contengono:", ELENCO_ALLERGENI, key="mie_allergie",
                         default=[a for a in dati.get("allergie", []) if a in ELENCO_ALLERGENI])
    if sorted(mie) != sorted(dati.get("allergie", [])):
        try:
            salva(lambda d: d.__setitem__("allergie", list(mie)), "Allergie")
        except Exception:
            pass
    solo_sicuri = st.checkbox("Mostra solo prodotti sicuri per me", value=False,
                              help="Nasconde i prodotti con questi allergeni e quelli senza informazioni sugli allergeni.")
    st.divider()
    if archivio.permanente:
        st.success("💾 Dati salvati su GitHub")
    else:
        st.warning("⚠️ Modalità prova: i dati si cancellano quando l'app si riavvia. "
                   "Collega GitHub (vedi scheda Info).")
    if st.button("🔄 Aggiorna"):
        carica_dati.clear()
        st.rerun()

# --- intestazione e avvisi ---
st.markdown(HERO, unsafe_allow_html=True)

con_stato = [(r, *stato_scadenza(r.get("scadenza"), data_oggi)) for r in articoli]
scaduti = sorted([r for r, s, g in con_stato if s == "scaduto"], key=lambda r: r["scadenza"])
rossi = sorted([r for r, s, g in con_stato if s == "rosso"], key=lambda r: r["scadenza"])
arancioni = sorted([r for r, s, g in con_stato if s == "arancione"], key=lambda r: r["scadenza"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Prodotti", len(articoli))
c2.metric("🟠 Entro 2 mesi", len(arancioni))
c3.metric("🔴 Entro 1 mese", len(rossi))
c4.metric("⚫ Scaduti", len(scaduti))

if scaduti:
    st.markdown(avviso_html("⚫ Scaduti: da buttare o controllare", "scaduto", scaduti, data_oggi), unsafe_allow_html=True)
if rossi:
    st.markdown(avviso_html("🔴 Scadono entro 1 mese", "rosso", rossi, data_oggi), unsafe_allow_html=True)
if arancioni:
    st.markdown(avviso_html("🟠 Scadono entro 2 mesi", "arancione", arancioni, data_oggi), unsafe_allow_html=True)

if st.session_state.get("messaggio"):
    st.success(st.session_state.pop("messaggio"))

_nomi_schede = ["🏠 Dispensa", "➕ Aggiungi", "✏️ Gestisci"] + (["👥 Utenti"] if e_admin else []) + ["ℹ️ Info"]
_schede = st.tabs(_nomi_schede)
tab_dispensa, tab_aggiungi, tab_gestisci = _schede[0], _schede[1], _schede[2]
tab_utenti = _schede[3] if e_admin else None
tab_info = _schede[-1]

# ---------------------------------------------------------------------
# DISPENSA
# ---------------------------------------------------------------------
with tab_dispensa:
    f1, f2, f3 = st.columns([3, 2, 2])
    cerca = f1.text_input("🔎 Cerca", placeholder="nome o marca", label_visibility="collapsed")
    filtro = f2.selectbox("Mostra", ["Tutti", "Solo in scadenza (2 mesi)", "Solo rossi (1 mese)", "Scaduti"],
                          label_visibility="collapsed")
    vista = f3.radio("Vista", ["Schede", "Tabella"], horizontal=True, label_visibility="collapsed")

    visibili = []
    for r, stato, giorni in con_stato:
        if cerca and cerca.lower() not in (r.get("nome", "") + " " + r.get("marca", "")).lower():
            continue
        if filtro == "Solo in scadenza (2 mesi)" and stato not in ("arancione", "rosso", "scaduto"):
            continue
        if filtro == "Solo rossi (1 mese)" and stato not in ("rosso", "scaduto"):
            continue
        if filtro == "Scaduti" and stato != "scaduto":
            continue
        if solo_sicuri and mie:
            if any(a in mie for a in (r.get("allergeni") or [])) or not (r.get("allergeni_noti") or r.get("allergeni")):
                continue
        visibili.append((r, stato, giorni))
    visibili.sort(key=lambda x: (x[0].get("scadenza") or "9999-12-31"))

    if not articoli:
        st.info("La dispensa è vuota. Vai nella scheda ➕ Aggiungi per inserire il primo prodotto.")
    elif not visibili:
        st.info("Nessun prodotto corrisponde ai filtri.")
    elif vista == "Schede":
        st.markdown("<div class='griglia'>" + "".join(scheda_html(r, data_oggi, mie) for r, _, _ in visibili) + "</div>",
                    unsafe_allow_html=True)
    else:
        tab = pd.DataFrame([{
            "Foto": src_sicuro(r.get("immagine") or "") or None,
            "Prodotto": r.get("nome", ""), "Marca": r.get("marca", ""),
            "Quantità": descrivi([r]),
            "Scadenza": data_it(r.get("scadenza")), "Stato": f"{ICONE[s]} {testo_giorni(s, g)}",
            "Allergeni": ", ".join(r.get("allergeni") or []) or ("—" if r.get("allergeni_noti") else "non verificati"),
            "_stato": s,
        } for r, s, g in visibili])
        sfondi = {"rosso": "background-color:#ffcdd2", "arancione": "background-color:#ffe0b2",
                  "scaduto": "background-color:#d7ccc8", "ok": "", "nessuna": ""}
        stile = tab.style.apply(lambda riga: [sfondi[riga["_stato"]]] * len(riga), axis=1)
        st.dataframe(stile, hide_index=True, height=min(700, 60 + 72 * len(tab)),
                     column_config={"Foto": st.column_config.ImageColumn("Foto", width="small"),
                                    "_stato": None})

# >>> FINE PARTE 3 di 4: adesso incolla la PARTE 4 qui sotto <<<
