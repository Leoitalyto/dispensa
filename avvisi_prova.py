# -*- coding: utf-8 -*-
"""SALUTE · «📨 Mandami un messaggio di prova» (dentro «🔔 Scegli come ricevere gli avvisi»).

PROBLEMA: dopo aver scelto un canale (Telegram, email, WhatsApp…) la persona non sapeva se aveva fatto giusto: gli avvisi veri partono al prossimo controllo automatico (di solito la
mattina dopo), e se qualcosa era sbagliato (Chat ID, bot non avviato, chiave di WhatsApp…) lo scopriva dopo giorni, o mai.

COME FUNZIONA
• La persona tocca «📨 Mandami un messaggio di prova»: l'app scrive nei suoi dati una richiesta {id, quando} (`avviso_prova`).
• Il programma automatico in GitHub (promemoria.py, ogni mezz'ora di giorno e ogni mattina) la vede, manda il messaggio su OGNI canale che la persona ha scelto e SALVATO, e scrive
  l'esito in `prove_avvisi/<persona>.json`: per ogni canale «ok», «errore: …» o «saltato: …».
• Qui l'app mostra «⏳ in attesa» finché l'esito non c'è, poi ✅ o ❌ per canale con spiegazioni in parole semplici su cosa fare (bot non avviato, numero sbagliato, chiave errata,
  servizio non attivato dall'amministratore…). «🔄 Controlla se è arrivato» rilegge l'esito.
• Si può rifare la richiesta dopo 10 minuti (o appena arriva l'esito)."""
import os
import uuid

import streamlit as st

_AV_NOMI = {"telegram": "📱 Telegram", "email": "✉️ Email", "sms": "💬 SMS", "whatsapp": "🟢 WhatsApp"}
_AV_CAMPO = {"telegram": "telegram_chat_id", "email": "avviso_email", "sms": "avviso_sms", "whatsapp": "avviso_whatsapp"}
_AV_ATTESA_MIN = 10


def av_uid():
    return os.path.splitext(os.path.basename(st.session_state.get("percorso") or "dispense/admin.json"))[0]


def av_canali_salvati(d):
    """I canali scelti E con il campo compilato (come li vede il programma automatico)."""
    canali = d.get("avvisi_canali")
    if canali is None:
        canali = ["telegram"] if d.get("telegram_chat_id") else []
    return [c for c in canali if c in _AV_CAMPO and str(d.get(_AV_CAMPO[c]) or "").strip()]


def av_leggi_esito(uid, forza=False):
    nome = f"prove_avvisi/{uid}.json"
    try:
        arch = crea_archivio()
        if forza:
            if hasattr(arch, "_mem_togli"):
                arch._mem_togli(nome)
            carica_dati.clear()
        return carica_dati(arch, nome) or {}
    except Exception:
        return {}


def _av_ora(iso):
    try:
        dt = datetime.fromisoformat(str(iso))
        return dt.strftime("%d/%m alle %H:%M")
    except Exception:
        return ""


def av_spiega_esito(canale, esito, admin="chi gestisce l'app"):
    """(icona, frase in parole semplici) per l'esito di un canale."""
    nome = _AV_NOMI.get(canale, canale)
    e = str(esito or "")
    el = e.lower()
    if e == "ok":
        consigli = {"telegram": "guarda Telegram.", "email": "guarda la posta (anche **Spam** o **Promozioni**).",
                    "whatsapp": "guarda WhatsApp: a volte arriva con qualche minuto di ritardo.", "sms": "guarda i messaggi."}
        return "✅", f"**{nome}**: inviato. {consigli.get(canale, '')}".strip()
    if canale == "telegram":
        if "403" in e:
            return "❌", f"**{nome}**: il bot non può scriverti. Apri il bot in Telegram e tocca **Avvia** (passo 3 della guida), poi rifai la prova."
        if "400" in e:
            return "❌", f"**{nome}**: il numero (**Chat ID**) non sembra giusto. Controlla di averlo copiato da **@userinfobot**, senza spazi né lettere."
        if "token" in el:
            return "⚠️", f"**{nome}**: il servizio non è ancora stato attivato dall'amministratore. Avvisa **{admin}**."
    if canale == "email":
        if "recipients" in el or "refused" in el:
            return "❌", f"**{nome}**: l'indirizzo è stato rifiutato. Controlla di averlo scritto giusto."
        if "auth" in el or "email_user" in el or "email_password" in el:
            return "⚠️", f"**{nome}**: il servizio email dell'app non è attivo. Avvisa **{admin}**."
    if canale == "whatsapp":
        if "manca" in el:
            return "⚠️", f"**{nome}**: manca il numero o la chiave. Compilali nella tendina e tocca **Salva**."
        if "callmebot" in el:
            frase = e.split("«", 1)[1].rsplit("»", 1)[0] if "«" in e else ""
            return "❌", f"**{nome}**: il servizio dice «{frase or e}». Controlla il **numero** (con +39) e la **chiave** di CallMeBot (scheda «Come attivo WhatsApp»)."
    if canale == "sms" and ("twilio" in el or e.startswith("saltato")):
        return "⚠️", f"**{nome}**: gli SMS non sono attivi (sono a pagamento). Avvisa **{admin}**."
    if e.startswith("saltato"):
        return "⚠️", f"**{nome}**: non è partito ({e.replace('saltato: ', '')}). Controlla i dati e tocca **Salva**."
    return "❌", f"**{nome}**: non è partito ({e}). Riprova fra poco; se si ripete avvisa **{admin}**."


def av_prova_ui(d):
    """Il riquadro «📨 Prova se funziona»: pulsante, attesa ed esito."""
    uid = av_uid()
    admin = nome_admin() if "nome_admin" in globals() else "chi gestisce l'app"
    st.markdown("##### 📨 Prova se funziona")
    canali = av_canali_salvati(d)
    if not canali:
        st.info("Per fare la prova spunta **almeno un canale**, compila il suo campo e tocca **Salva**. Poi torna qui.")
        return
    rich = d.get("avviso_prova") if isinstance(d.get("avviso_prova"), dict) else {}
    esito = av_leggi_esito(uid)
    fatta = bool(rich.get("id")) and esito.get("id") == rich.get("id") and esito.get("stato") in ("fatto", "nessun canale")
    in_corso = bool(rich.get("id")) and esito.get("id") == rich.get("id") and esito.get("stato") == "in corso"
    attesa = bool(rich.get("id")) and not fatta
    minuti = None
    try:
        minuti = (adesso() - datetime.fromisoformat(str(rich.get("quando")))).total_seconds() / 60
    except Exception:
        pass
    st.caption("Tocca il pulsante: l'app manda un **messaggio di prova** su tutti i canali che hai spuntato e **salvato** (" + ", ".join(_AV_NOMI[c] for c in canali) + "). "
               "Non parte subito: parte al **prossimo controllo automatico**, di solito entro 30 minuti (di notte, al mattino). Poi tocca **«🔄 Controlla se è arrivato»**.")
    blocca = attesa and minuti is not None and minuti < _AV_ATTESA_MIN
    if st.button("📨 Mandami un messaggio di prova", key="av_prova_btn", width="stretch", disabled=blocca):
        nuova = {"id": uuid.uuid4().hex[:10], "quando": adesso().isoformat(timespec="minutes")}
        try:
            salva(lambda dd: dd.update({"avviso_prova": nuova}), "Avvisi: richiesta di un messaggio di prova")
        except Exception as e:
            st.error(f"Non sono riuscito a registrare la richiesta: {e}")
            return
        st.rerun()
    if blocca:
        st.caption(f"Hai già fatto la richiesta {_av_ora(rich.get('quando'))}: puoi rifarla fra {max(1, int(_AV_ATTESA_MIN - (minuti or 0)))} minuti.")
    if not rich.get("id"):
        return
    if fatta:
        if esito.get("stato") == "nessun canale":
            st.warning("Al momento della prova non risultava nessun canale attivo. Spunta un canale, tocca **Salva** e rifai la prova.")
        else:
            st.markdown(f"**Esito della prova** (richiesta {_av_ora(rich.get('quando'))}, inviata {_av_ora(esito.get('inviata'))}):")
            for c, e in (esito.get("esiti") or {}).items():
                ic, frase = av_spiega_esito(c, e, admin)
                st.markdown(f"{ic} {frase}")
            tutti_ok = all(e == "ok" for e in (esito.get("esiti") or {}).values())
            if tutti_ok:
                st.success("Tutto a posto: gli avvisi veri arriveranno così.")
    elif in_corso:
        st.info(f"⏳ La prova è **in corso** (richiesta {_av_ora(rich.get('quando'))}). Tocca **🔄 Controlla se è arrivato** fra un minuto.")
    else:
        st.info(f"⏳ Richiesta fatta {_av_ora(rich.get('quando'))}: il messaggio parte al prossimo controllo automatico (entro circa 30 minuti; di notte, al mattino). "
                "Quando è passato un po', tocca **🔄 Controlla se è arrivato**.")
    if st.button("🔄 Controlla se è arrivato", key="av_prova_ricontrolla", width="stretch"):
        av_leggi_esito(uid, forza=True)
        st.rerun()
