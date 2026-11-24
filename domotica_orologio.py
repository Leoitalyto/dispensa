# -*- coding: utf-8 -*-
"""⏰ L'OROLOGIO AUTOMATICO del riscaldamento, comandato da VitaMemo (richiesta del 24/11/2026: «inserisci nel pannello la funzione
per attivare e disattivare il cron job e una breve spiegazione, così non torno sempre qui per le domande»).

L'orologio è un «cronjob» su cron-job.org (gratuito) che ogni mezz'ora fa partire su GitHub il programma domotica_orari.py.
Ogni partenza consuma 1 minuto dei circa 2.000 gratuiti al mese di GitHub Actions: per questo lo si accende solo quando serve.
Da qui, con la chiave gratuita delle API di cron-job.org (Streamlit Secrets: [cronjob] api_key = "…"), si può:
  · vedere se è acceso o in pausa e con quale orario;
  · ▶️ accenderlo, ⏸️ metterlo in pausa, 📅 accenderlo solo fino a fine giornata (si spegne da solo: «expiresAt»);
  · 🔧 rimettere l'orario consigliato (ogni mezz'ora dalle 5:00 alle 23:30, ora italiana).
API: https://api.cron-job.org (Authorization: Bearer <chiave>), limite 100 richieste al giorno → lo stato si tiene in memoria 10 minuti.
Senza chiave: spiegazione e passi da fare a mano su console.cron-job.org. Prefisso: orl_ / ORL_."""
import datetime as _orl_dt
import json as _orl_json
import urllib.error as _orl_ue
import urllib.request as _orl_ur

import streamlit as st

ORL_API = "https://api.cron-job.org"
ORL_ORE = list(range(5, 24))                     # dalle 5:00 alle 23:30
ORL_MINUTI = [0, 30]
ORL_MINUTI_GITHUB = 2000                         # circa (12 $ di credito gratuito al mese)
ORL_ALTRI_AL_MESE = 180                          # promemoria e posta, più o meno


class OrlErrore(Exception):
    pass


# =====================================================================================================================
# logica (senza Streamlit)
# =====================================================================================================================
def orl_avvii_al_giorno(schedule):
    """Quante volte parte in un giorno con quell'orario (ore × minuti; -1 = tutti)."""
    s = schedule or {}
    ore = s.get("hours") or [-1]
    minuti = s.get("minutes") or [-1]
    n_ore = 24 if -1 in ore else len(set(ore))
    n_min = 60 if -1 in minuti else len(set(minuti))
    return n_ore * n_min


def orl_descrivi_orario(schedule):
    s = schedule or {}
    ore = sorted(set(s.get("hours") or [-1]))
    minuti = sorted(set(s.get("minutes") or [-1]))
    if minuti == [-1]:
        q = "ogni minuto"
    elif len(minuti) == 1:
        q = f"ogni ora al minuto {minuti[0]:02d}"
    elif len(minuti) >= 2 and all((minuti[i + 1] - minuti[i]) == (minuti[1] - minuti[0]) for i in range(len(minuti) - 1)) and minuti[0] == 0 and 60 % (minuti[1] - minuti[0]) == 0:
        q = f"ogni {minuti[1] - minuti[0]} minuti"
    else:
        q = "ai minuti " + ", ".join(f"{m:02d}" for m in minuti)
    if ore == [-1]:
        quando = "giorno e notte"
    elif ore == list(range(ore[0], ore[-1] + 1)):
        quando = f"dalle {ore[0]}:00 alle {ore[-1]}:{max(m for m in minuti if m >= 0) if minuti != [-1] else 59:02d}"
    else:
        quando = "alle ore " + ", ".join(str(h) for h in ore)
    return f"{q}, {quando}"


def orl_scadenza(job):
    """La data/ora in cui si spegne da solo (datetime) o None. expiresAt = AAAAMMGGhhmmss nel fuso del lavoro, 0 = mai."""
    v = ((job or {}).get("schedule") or {}).get("expiresAt") or 0
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    if v <= 0:
        return None
    try:
        return _orl_dt.datetime.strptime(str(v), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def orl_stato(job, adesso):
    """("acceso" | "pausa" | "scaduto" | "fino", testo)."""
    if not job:
        return "pausa", "non trovato"
    if not job.get("enabled"):
        return "pausa", "⏸️ In pausa: non consuma minuti"
    sc = orl_scadenza(job)
    if sc and sc <= adesso:
        return "scaduto", "⏸️ In pausa (era acceso solo fino al " + sc.strftime("%d/%m alle %H:%M") + ")"
    if sc:
        return "fino", "▶️ Acceso fino a " + ("stasera" if sc.date() == adesso.date() else sc.strftime("%d/%m")) + f" alle {sc:%H:%M}, poi si spegne da solo"
    return "acceso", "▶️ Acceso"


def orl_minuti_mese(job, adesso):
    stato = orl_stato(job, adesso)[0]
    giorni = orl_avvii_al_giorno((job or {}).get("schedule")) if stato in ("acceso", "fino") else 0
    return giorni * 30 + ORL_ALTRI_AL_MESE


def orl_trova(jobs):
    """Il lavoro dell'orologio: quello che chiama domotica_orari.yml (o con «riscaldamento» nel titolo)."""
    for j in jobs or []:
        if "domotica_orari" in str(j.get("url") or ""):
            return j
    for j in jobs or []:
        if "riscald" in str(j.get("title") or "").lower():
            return j
    return None


def orl_corpo(azione, adesso, fino=None):
    """Il corpo della richiesta PATCH per l'azione scelta."""
    if azione == "accendi":
        return {"job": {"enabled": True, "schedule": {"expiresAt": 0}}}
    if azione == "pausa":
        return {"job": {"enabled": False}}
    if azione == "oggi":
        f = fino or adesso.replace(hour=23, minute=59, second=0, microsecond=0)
        return {"job": {"enabled": True, "schedule": {"expiresAt": int(f.strftime("%Y%m%d%H%M%S"))}}}
    if azione == "orario":
        return {"job": {"schedule": {"timezone": "Europe/Rome", "hours": ORL_ORE, "minutes": ORL_MINUTI, "mdays": [-1], "months": [-1], "wdays": [-1]}}}
    raise ValueError(azione)


def orl_chiama(chiave, metodo, percorso, corpo=None, timeout=20, base=None):
    req = _orl_ur.Request((base or ORL_API).rstrip("/") + percorso, method=metodo, data=_orl_json.dumps(corpo).encode() if corpo is not None else None,
                         headers={"Authorization": f"Bearer {chiave}", "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with _orl_ur.urlopen(req, timeout=timeout) as r:
            testo = r.read().decode() or "{}"
            return _orl_json.loads(testo)
    except _orl_ue.HTTPError as e:
        spiega = {401: "la chiave delle API non è giusta (rifalla in Impostazioni → API su cron-job.org)",
                  403: "la chiave non può essere usata da qui: in Impostazioni → API togli il limite degli indirizzi IP",
                  404: "il lavoro non esiste più su cron-job.org",
                  429: "troppe richieste oggi (cron-job.org ne permette 100 al giorno): riprova domani o fallo a mano"}.get(e.code, f"errore {e.code}")
        raise OrlErrore(spiega) from None
    except Exception as e:
        raise OrlErrore(f"cron-job.org non risponde ({type(e).__name__}): riprova fra poco") from None


# =====================================================================================================================
# Streamlit
# =====================================================================================================================
def _orl_base():
    try:
        return str((st.secrets.get("cronjob") or {}).get("api_url") or ORL_API)     # api_url: solo per le prove
    except Exception:
        return ORL_API


def orl_chiave():
    try:
        s = st.secrets.get("cronjob") or {}
        k = s.get("api_key") if hasattr(s, "get") else None
        return str(k or st.secrets.get("CRONJOB_API_KEY") or "").strip()
    except Exception:
        return ""


@st.cache_data(ttl=600, show_spinner=False)
def _orl_jobs_cache(chiave, giro):
    return orl_chiama(chiave, "GET", "/jobs", base=_orl_base()).get("jobs") or []


def orl_lavoro(forza=False):
    chiave = orl_chiave()
    if not chiave:
        return None
    if forza:
        st.session_state["_orl_giro"] = st.session_state.get("_orl_giro", 0) + 1
    return orl_trova(_orl_jobs_cache(chiave, st.session_state.get("_orl_giro", 0)))


def orl_fai(azione, job):
    chiave = orl_chiave()
    orl_chiama(chiave, "PATCH", f"/jobs/{int(job['jobId'])}", orl_corpo(azione, _orl_adesso()), base=_orl_base())
    try:
        _dm_log({"accendi": "orologio acceso", "pausa": "orologio in pausa", "oggi": "orologio acceso solo per oggi", "orario": "orologio: orario consigliato"}[azione])
    except Exception:
        pass
    st.session_state["_orl_giro"] = st.session_state.get("_orl_giro", 0) + 1


def _orl_adesso():
    try:
        return adesso().replace(tzinfo=None)
    except Exception:
        return _orl_dt.datetime.now()


def _orl_n(n):
    return f"{int(n):,}".replace(",", ".")


def _orl_spiegazione():
    st.markdown(
        "**Cos'è.** Un «orologio» gratuito (sul sito cron-job.org) che ogni mezz'ora sveglia VitaMemo **anche quando l'app è chiusa**, "
        "così gli **📅 orari** vengono mandati al termostato all'ora giusta.\n\n"
        f"**Quanto costa.** Niente soldi, ma ogni sveglia consuma **1 minuto** dei circa **{_orl_n(ORL_MINUTI_GITHUB)} minuti gratuiti al mese** di GitHub "
        "(gli stessi che usano promemoria e posta). Ogni mezz'ora dalle 5 alle 23:30 sono circa 1.150 minuti al mese: va bene. "
        "Se un mese si superano i 2.000 minuti non paghi niente, ma **le automazioni si fermano** fino al mese dopo.\n\n"
        "**Quando serve acceso:** solo se usi gli **📅 Orari della settimana** o un **giorno speciale** e vuoi che funzionino anche ad app chiusa.\n\n"
        "**Funziona anche in pausa:** 🎯 temperatura a mano (anche «fino a» un orario), 🚀 Boost, ⏻ Spegni, ❄️ Antigelo, 🅰️ il programma del termostato "
        "e l'app BTicino. E gli orari vengono comunque applicati **quando apri VitaMemo**.")


def _orl_guida_chiave():
    st.markdown(
        "**Per comandare l'orologio da qui serve una chiave gratuita di cron-job.org** (una volta sola):\n"
        "1. Apri [console.cron-job.org → Impostazioni](https://console.cron-job.org/settings) ed entra.\n"
        "2. Cerca la parte **«API»** (o «Chiavi API») e tocca **«Crea chiave API»** (*Create API key*). **Non** mettere limiti di indirizzi IP.\n"
        "3. Copia la chiave (una lunga serie di lettere e numeri). **Non mandarla in chat.**\n"
        "4. Apri [i Secrets della tua app su Streamlit](https://share.streamlit.io/) → la tua app → **⋮ → Settings → Secrets** e aggiungi in fondo:\n"
        "```\n[cronjob]\napi_key = \"INCOLLA_QUI_LA_CHIAVE\"\n```\n"
        "5. Tocca **Save**: dopo un minuto qui compaiono i bottoni ▶️ ⏸️ 📅.\n\n"
        "**Intanto puoi farlo a mano:** [console.cron-job.org → Cronjobs](https://console.cron-job.org/jobs) → spunta il quadratino di "
        "«VitaMemo orari riscaldamento» → **Attiva** oppure **Disattiva**.")


def orl_pannello(in_uso=False, aperto=False):
    """Il riquadro «⏰ Orologio automatico» (nella pagina degli orari del termostato)."""
    ora = _orl_adesso()
    chiave = orl_chiave()
    job, errore = None, None
    if chiave:
        try:
            job = orl_lavoro()
        except OrlErrore as e:
            errore = str(e)
    stato = orl_stato(job, ora) if job else (None, "")
    breve = {"acceso": "▶️ acceso", "fino": "▶️ acceso fino a stanotte", "pausa": "⏸️ in pausa", "scaduto": "⏸️ in pausa"}
    titolo = "⏰ Orologio automatico" + (f" · {breve.get(stato[0], '')}" if job else "")
    with st.expander(titolo, expanded=aperto):
        if chiave and errore:
            st.error("❌ " + errore)
        elif chiave and not job:
            st.warning("Non trovo su cron-job.org il lavoro che chiama «domotica_orari.yml». Controlla che esista (anche in pausa) in "
                       "[Cronjobs](https://console.cron-job.org/jobs).")
        if job:
            s, testo = stato
            colore = {"acceso": "#2ecc71", "fino": "#4aa3ff", "pausa": "#9aa4b2", "scaduto": "#9aa4b2"}[s]
            minuti = orl_minuti_mese(job, ora)
            st.markdown(f"<div style='border-left:6px solid {colore};padding:8px 12px;border-radius:10px;background:rgba(255,255,255,.05)'>"
                        f"<b>{testo}</b><br><small>🕑 Orario: {orl_descrivi_orario(job.get('schedule'))} "
                        f"({orl_avvii_al_giorno(job.get('schedule'))} volte al giorno)<br>"
                        f"📊 Minuti GitHub stimati al mese: <b>{_orl_n(minuti)}</b> su circa {_orl_n(ORL_MINUTI_GITHUB)}</small></div>",
                        unsafe_allow_html=True)
            if orl_avvii_al_giorno(job.get("schedule")) > 40:
                st.warning("⚠️ Così parte troppo spesso: con il bottone **🔧 Orario consigliato** lo metti ogni mezz'ora dalle 5 alle 23:30.")
            if in_uso and s in ("pausa", "scaduto"):
                st.info("📅 Hai orari attivi: con l'orologio in pausa vengono applicati solo quando apri VitaMemo.")
            c1, c2 = st.columns(2, gap="small")
            azione = None
            if s in ("pausa", "scaduto", "fino") and c1.button("▶️ Accendi", key="orl_accendi", type="primary", width="stretch", help="Sempre acceso finché non lo metti in pausa"):
                azione = "accendi"
            if s in ("acceso", "fino") and c2.button("⏸️ Metti in pausa", key="orl_pausa", width="stretch"):
                azione = "pausa"
            if s != "fino" and st.button("📅 Accendi solo per oggi (si spegne da solo stanotte)", key="orl_oggi", width="stretch"):
                azione = "oggi"
            if orl_avvii_al_giorno(job.get("schedule")) != len(ORL_ORE) * len(ORL_MINUTI) and st.button("🔧 Orario consigliato (ogni mezz'ora, 5:00–23:30)", key="orl_orario", width="stretch"):
                azione = "orario"
            if azione:
                try:
                    with st.spinner("Lo dico a cron-job.org…"):
                        orl_fai(azione, job)
                    st.toast({"accendi": "▶️ Orologio acceso", "pausa": "⏸️ Orologio in pausa", "oggi": "📅 Orologio acceso fino a stanotte",
                              "orario": "🔧 Orario sistemato"}[azione])
                    _dm_rr() if "_dm_rr" in globals() else st.rerun()
                except OrlErrore as e:
                    st.error("❌ " + str(e))
            if st.button("🔄 Aggiorna lo stato", key="orl_aggiorna", width="stretch"):
                try:
                    orl_lavoro(forza=True)
                except OrlErrore:
                    pass
                _dm_rr() if "_dm_rr" in globals() else st.rerun()
        elif not chiave:
            _orl_guida_chiave()
        st.divider()
        _orl_spiegazione()
