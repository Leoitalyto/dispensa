# -*- coding: utf-8 -*-
"""CAMBIARE IL NOME DELLE PERSONE.

• L'amministratore: nella scheda «Utenti», su ogni persona, c'è «✏️ Cambia nome».
• Ogni persona (non l'amministratore): in Utilità → «⚙️ Aspetto dell'app» c'è «✏️ Il mio nome».
Le persone sono collegate alla dispensa condivisa (e a tutto il resto) da un CODICE interno, non dal nome: cambiando il nome non si rompe niente.
Il nome nuovo compare anche nell'app dell'altra persona (alla prima pagina che apre, entro pochi secondi, senza rientrare), e nel suo profilo principale di Salute.
Le voci già scritte nel registro delle modifiche della dispensa condivisa restano con il nome di allora (è lo storico).
Caricato da app_dispensa.py dopo pagine_nav.py."""
import streamlit as st


def nu_valida(nuovo, elenco, uid):
    """(ok, messaggio) per un nome nuovo."""
    n = (nuovo or "").strip()
    if not n:
        return False, "Il nome non può essere vuoto."
    if len(n) > 40:
        return False, "Il nome è troppo lungo (massimo 40 caratteri)."
    if any(x.get("id") != uid and (x.get("nome") or "").strip().lower() == n.lower() for x in elenco):
        return False, "C'è già una persona con questo nome: scegline un altro."
    adm = ""
    try:
        adm = str(st.secrets.get("admin_nome", "") or "")
    except Exception:
        adm = ""
    if adm and adm.strip().lower() == n.lower():
        return False, "Questo nome è già usato: scegline un altro."
    return True, n


def nu_cambia(uid, vecchio, nuovo):
    """Scrive il nome nuovo nell'elenco delle persone e nel profilo principale (p0) della sua Salute, se aveva ancora il nome di prima."""
    def _utenti(d):
        for x in d.get("utenti", []):
            if x.get("id") == uid:
                x["nome"] = nuovo
    salva_file("utenti.json", _utenti, f"Nome: {vecchio} → {nuovo}")

    def _p0(d):
        for p in (d.get("farmacia") or {}).get("profili", []):
            if p.get("id") == "p0" and (p.get("nome") or "").strip() == (vecchio or "").strip():
                p["nome"] = nuovo
    try:
        salva_file(f"dispense/{uid}.json", _p0, f"Nome del profilo principale: {nuovo}")
    except Exception:
        pass                                                         # se non ha ancora dati suoi, niente da aggiornare
    try:
        carica_dati.clear()
    except Exception:
        pass


def nu_ui_admin(u, elenco):
    """Su ogni persona della scheda «Utenti»: ✏️ Cambia nome."""
    if st.session_state.get("nu_msg"):
        st.success(st.session_state.pop("nu_msg"))
    with st.popover("✏️ Cambia nome"):
        st.caption("La persona **resta collegata** alla dispensa condivisa e a tutte le sue cose: cambia solo il nome che si vede. Lo vedrà cambiato anche nella sua app.")
        nuovo = st.text_input("Nuovo nome", value=u.get("nome", ""), key=f"nu_n_{u['id']}")
        if st.button("💾 Salva il nome", key=f"nu_b_{u['id']}", type="primary", width="stretch"):
            ok, msg = nu_valida(nuovo, elenco, u["id"])
            if not ok:
                st.error(msg)
            elif msg == (u.get("nome") or "").strip():
                st.info("È già questo il nome.")
            else:
                try:
                    nu_cambia(u["id"], u.get("nome", ""), msg)
                except Exception as ex:
                    st.error(f"Non sono riuscito a salvare: {ex}")
                else:
                    st.session_state["nu_msg"] = f"✅ «{u.get('nome', '')}» ora si chiama «{msg}». Resta collegata alla dispensa condivisa."
                    st.rerun()


def nu_ui_proprio():
    """In «⚙️ Aspetto dell'app»: ✏️ Il mio nome."""
    sess = st.session_state.get("sess") or {}
    if st.session_state.get("nu_msg"):
        st.success(st.session_state.pop("nu_msg"))
    if sess.get("admin"):
        st.caption("✏️ Il nome dell'amministratore si cambia dalle impostazioni segrete dell'app (parola **admin_nome**).")
        return
    if not sess.get("uid") or sess.get("uid") == "prova":
        return
    st.markdown("**✏️ Il mio nome**")
    nuovo = st.text_input("Come vuoi che ti chiami l'app", value=sess.get("nome", ""), key="nu_mio", label_visibility="collapsed")
    if st.button("💾 Salva il mio nome", key="nu_mio_b", width="stretch"):
        try:
            elenco = carica_dati(crea_archivio(), "utenti.json").get("utenti", [])
        except Exception:
            elenco = []
        ok, msg = nu_valida(nuovo, elenco, sess["uid"])
        if not ok:
            st.error(msg)
        elif msg == (sess.get("nome") or "").strip():
            st.info("È già questo il tuo nome.")
        else:
            try:
                nu_cambia(sess["uid"], sess.get("nome", ""), msg)
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare: {ex}")
            else:
                sess["nome"] = msg
                st.session_state["sess"] = sess
                st.session_state["nu_msg"] = f"✅ Ora ti chiami «{msg}»."
                st.rerun()
    st.divider()


def nu_aggiorna_sessione():
    """Se l'amministratore ha cambiato il mio nome, lo vedo subito (senza rientrare)."""
    sess = st.session_state.get("sess")
    if not sess or sess.get("admin") or sess.get("uid") in (None, "prova"):
        return
    try:
        u = next((x for x in carica_dati(crea_archivio(), "utenti.json").get("utenti", []) if x.get("id") == sess["uid"]), None)
    except Exception:
        return
    if u and u.get("nome") and u["nome"] != sess.get("nome"):
        sess["nome"] = u["nome"]
        st.session_state["sess"] = sess
