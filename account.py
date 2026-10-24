# -*- coding: utf-8 -*-
"""Cambio password (al primo accesso e quando si vuole) e messaggi/suggerimenti per l'amministratore."""

LUNGHEZZA_MIN_PW = 8


# ---------------------------------------------------------------------
# PASSWORD
# ---------------------------------------------------------------------
def controlla_nuova_password(nuova, conferma, utenti, uid):
    """Ritorna il testo dell'errore, oppure None se la nuova password va bene."""
    n = normalizza_password(nuova)
    if len(n) < LUNGHEZZA_MIN_PW:
        return t("La password deve avere almeno {n} caratteri.", n=LUNGHEZZA_MIN_PW)
    if (n.isdigit() or n.isalpha()) and len(n) < 16:
        return t("Usa lettere e numeri insieme (oppure una frase di almeno 16 caratteri).")
    if normalizza_password(conferma) != n:
        return t("Le due password non coincidono.")
    if troppi_tentativi():
        return t("Troppi tentativi sbagliati. Aspetta un minuto e riprova.")
    h = hash_password(nuova)
    if hmac.compare_digest(h, st.session_state.get("sess", {}).get("h", "")):
        return t("Scegli una password diversa da quella attuale.")
    pa = password_admin()
    occupata = (pa and hmac.compare_digest(h, hash_password(pa))) or any(
        u["id"] != uid and hmac.compare_digest(u.get("hash", ""), h) for u in utenti)
    if occupata:
        registro_errori().append(time.time())        # conta come tentativo, per non poter "indovinare" le password altrui
        return t("Questa password non è utilizzabile: scegline un'altra.")
    return None


def salva_nuova_password(uid, nuova):
    h = hash_password(nuova)

    def aggiorna(d):
        for x in d.get("utenti", []):
            if x["id"] == uid:
                x["hash"] = h
                x["deve_cambiare"] = False
                x["pw_cambiata"] = adesso().isoformat(timespec="minutes")
    salva_file("utenti.json", aggiorna, "Password cambiata")
    st.session_state["sess"] = dict(st.session_state["sess"], h=h)
    if st.query_params.get("k"):                       # l'accesso ricordato su questo telefono segue la nuova password
        st.query_params["k"] = nuova


def modulo_cambio_password(forzata=False):
    sfx = "forz" if forzata else "menu"
    with st.form("cambio_password_" + sfx, clear_on_submit=True):
        st.caption(t("Almeno {n} caratteri, con lettere e numeri insieme (oppure una frase di almeno 16 caratteri).",
                     n=LUNGHEZZA_MIN_PW))
        nuova = st.text_input(t("Nuova password"), type="password")
        conferma = st.text_input(t("Ripeti la nuova password"), type="password")
        invio = st.form_submit_button("💾 " + t("Salva la mia password"), type="primary")
    if invio:
        errore = controlla_nuova_password(nuova, conferma, leggi_utenti(), sess["uid"])
        if errore:
            st.error(errore)
        else:
            try:
                salva_nuova_password(sess["uid"], nuova)
                st.session_state["messaggio"] = "✅ " + t("Password cambiata. Da ora usa quella nuova per entrare.")
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))


def schermata_primo_accesso():
    selettore_lingua("primo")
    st.subheader("👋 " + t("Ciao {nome}!", nome=utente))
    st.write(t("Per sicurezza scegli una password tua: quella che ti ha mandato l'amministratore funziona finché non la cambi."))
    modulo_cambio_password(forzata=True)
    if st.button(t("Più tardi"), key="pw_piu_tardi_btn"):
        st.session_state["pw_piu_tardi"] = True
        st.rerun()


# ---------------------------------------------------------------------
# MESSAGGI E SUGGERIMENTI
# ---------------------------------------------------------------------
TIPI_MESSAGGIO = {"suggerimento": ("💡", "Suggerimento"), "integrazione": ("🧩", "Richiesta di integrazione"),
                  "problema": ("🐞", "Segnalazione di un problema")}


def carica_messaggi():
    try:
        return carica_dati(crea_archivio(), "messaggi.json").get("messaggi", [])
    except Exception:
        return []


def _data_ora(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return ""


def _minuti_fa(iso):
    try:
        return (adesso() - datetime.fromisoformat(iso)).total_seconds() / 60
    except Exception:
        return 10 ** 6


def _etichetta_tipo(k):
    icona, nome = TIPI_MESSAGGIO.get(k, TIPI_MESSAGGIO["suggerimento"])
    return f"{icona} {t(nome)}"


def _aggiorna_messaggio(mid, fn):
    def agg(d):
        for m in d.get("messaggi", []):
            if m["id"] == mid:
                fn(m)
    salva_file("messaggi.json", agg, "Messaggio aggiornato")


def _messaggi_utente():
    st.subheader("💬 " + t("Scrivi all'amministratore"))
    st.caption(t("Hai un'idea o ti serve qualcosa in più? Scrivilo qui: lo leggerà l'amministratore."))
    miei = [m for m in carica_messaggi() if m.get("uid") == sess["uid"]]
    with st.form("nuovo_messaggio", clear_on_submit=True):
        tipo = st.radio(t("Di cosa si tratta?"), list(TIPI_MESSAGGIO), format_func=_etichetta_tipo)
        testo = st.text_area(t("Il tuo messaggio"), max_chars=1000, height=140)
        invia = st.form_submit_button("📨 " + t("Invia"), type="primary")
    if invia:
        if not testo.strip():
            st.error(t("Scrivi il messaggio."))
        elif sum(1 for m in miei if _minuti_fa(m.get("data")) < 60) >= 3:
            st.error(t("Hai già mandato 3 messaggi nell'ultima ora: riprova più tardi."))
        else:
            nuovo = {"id": uuid.uuid4().hex[:10], "uid": sess["uid"], "nome": utente, "tipo": tipo,
                     "testo": testo.strip()[:1000], "data": adesso().isoformat(timespec="minutes"),
                     "letto": False, "risposta": "", "data_risposta": None}
            try:
                salva_file("messaggi.json", lambda d: d.setdefault("messaggi", []).append(nuovo), "Nuovo messaggio")
                st.session_state["messaggio"] = "✅ " + t("Messaggio inviato all'amministratore.")
                st.rerun()
            except Exception as e:
                st.error(t("Non sono riuscito a salvare: {e}", e=e))
    if miei:
        st.divider()
        st.markdown("**" + t("I tuoi messaggi") + "**")
    for m in reversed(miei):
        with st.container(border=True):
            st.caption(f"{_etichetta_tipo(m.get('tipo'))} · {_data_ora(m.get('data'))}")
            st.write(m.get("testo", ""))
            if m.get("risposta"):
                st.success("✅ " + t("Risposta dell'amministratore:") + " " + m["risposta"])
            elif m.get("letto"):
                st.caption("👀 " + t("Letto dall'amministratore"))
            else:
                st.caption("⏳ " + t("In attesa"))


def _messaggi_admin():
    messaggi = carica_messaggi()
    nuovi = sum(1 for m in messaggi if not m.get("letto"))
    st.subheader("📬 " + t("Messaggi ricevuti"))
    st.caption(t("{n} nuovi", n=nuovi))
    if not messaggi:
        st.info(t("Nessun messaggio ricevuto."))
    for m in reversed(messaggi):
        with st.container(border=True):
            nuovo = not m.get("letto")
            st.markdown(("🆕 " if nuovo else "") + f"**{m.get('nome', '')}** · {_etichetta_tipo(m.get('tipo'))} · {_data_ora(m.get('data'))}")
            st.write(m.get("testo", ""))
            if m.get("risposta"):
                st.success("✅ " + t("Risposta dell'amministratore:") + " " + m["risposta"])
            risposta = st.text_area(t("Risposta"), key=f"ris_{m['id']}", height=80, max_chars=1000)
            b1, b2, b3 = st.columns(3)
            if b1.button("✉️ " + t("Rispondi"), key=f"rsp_{m['id']}"):
                if risposta.strip():
                    def rispondi(x, testo=risposta.strip()[:1000]):
                        x["risposta"] = testo
                        x["letto"] = True
                        x["data_risposta"] = adesso().isoformat(timespec="minutes")
                    try:
                        _aggiorna_messaggio(m["id"], rispondi)
                        st.rerun()
                    except Exception as e:
                        st.error(t("Non sono riuscito a salvare: {e}", e=e))
                else:
                    st.warning(t("Scrivi la risposta."))
            if nuovo and b2.button("👀 " + t("Segna come letto"), key=f"let_{m['id']}"):
                try:
                    _aggiorna_messaggio(m["id"], lambda x: x.__setitem__("letto", True))
                    st.rerun()
                except Exception as e:
                    st.error(t("Non sono riuscito a salvare: {e}", e=e))
            with b3.popover("🗑️ " + t("Elimina")):
                st.write(t("Eliminare questo messaggio? Non si può annullare."))
                if st.button(t("Sì, elimina"), key=f"del_{m['id']}"):
                    try:
                        salva_file("messaggi.json",
                                   lambda d, mid=m["id"]: d.__setitem__("messaggi", [x for x in d.get("messaggi", []) if x["id"] != mid]),
                                   "Messaggio eliminato")
                        st.rerun()
                    except Exception as e:
                        st.error(t("Non sono riuscito a eliminare: {e}", e=e))


def scheda_messaggi():
    if e_admin:
        _messaggi_admin()
    else:
        _messaggi_utente()
