# -*- coding: utf-8 -*-
"""AUTO · DIAGNOSI VISIVA DELLE SPIE — fotografi il cruscotto e l'intelligenza artificiale riconosce la spia (di QUALSIASI mezzo: auto, moto, camion/TIR, autobus, furgoni, camper, mezzi agricoli).

Come funziona:
• La foto si fa col pulsante arancione («📷 Scatta foto» o «🖼️ Dalla galleria»), oppure col visore live (se il telefono lo permette).
• SE nei Secrets di Streamlit c'è ANTHROPIC_API_KEY (la stessa chiave dell'assistente intelligente), la foto viene mandata a un modello Claude con capacità di vedere le immagini, che
  risponde con: nome della spia, colore, urgenza, significato, azioni e cause. Interruttore: DIAGNOSI_AI = "no". Modello: DIAGNOSI_MODELLO (predefinito claude-sonnet-5-5).
  Tetti: DIAGNOSI_MAX_GIORNO (predefinito 40 per tutta l'app) e 15 ogni ora per sessione. Costa più di una domanda di testo: conviene fissare un limite di spesa nella console Anthropic.
• SENZA chiave (o se qualcosa non va) la foto si vede e si confronta col catalogo delle spie, che resta sempre disponibile.
• La SICUREZZA viene prima di tutto e non dipende dall'IA: se qualcosa è rosso, l'avviso di pericolo compare per primo con il 112 e il soccorso a un tocco.
• La foto viene mandata al servizio SOLO quando la scatti o la carichi tu; non ci sono dati personali (niente nome, targa o volti: inquadra solo il cruscotto).
• L'IA può sbagliare: il risultato è un aiuto, non una diagnosi da officina. Il manuale del veicolo vale sempre.
Caricato dopo auto_pagine.py."""
import base64
import hashlib
import html as _h_ap
import io
import json
import re
import time
import urllib.parse
import uuid
from datetime import date, datetime

import streamlit as st

AD_MODELLO = "claude-sonnet-5-5"
AD_URL = "https://api.anthropic.com/v1/messages"
AD_MAX_ORA = 15
AD_MEZZI = ["Il veicolo scelto", "Auto", "Moto", "Ciclomotore / scooter", "Monopattino elettrico", "Bicicletta elettrica (e-bike)", "Camion / TIR", "Autobus / pullman", "Furgone o veicolo commerciale", "Camper", "Mezzo agricolo o da lavoro", "Altro mezzo"]
AD_SOCCORSO_PREDEFINITO = "803116"

_AD_REGOLE = """Sei un esperto di diagnostica dei veicoli (auto, moto, camion e TIR, autobus, furgoni, camper, mezzi agricoli; termici, ibridi ed elettrici) e di soccorso stradale. Ti viene mostrata la FOTO di un cruscotto con una o più spie accese.
Il tuo compito: riconoscere le spie visibili e spiegarle a una persona non esperta, in italiano semplice, con frasi brevi.

REGOLE
- SICUREZZA PRIMA DI TUTTO. Se una spia indica pericolo grave (pressione olio, freni, surriscaldamento, sterzo, airbag, aria dell'impianto frenante nei mezzi pesanti, guasto ad alta tensione, batteria di trazione), mettila come PRIMA e indica chiaramente se accostare subito e spegnere.
- Colore: «rosso» = arresto immediato/emergenza; «giallo» (giallo o arancio) = avviso, officina a breve; «verde», «blu» o «bianco» = informazione o funzione attiva.
- NON INVENTARE. Se la foto è sfocata, troppo scura, riflette, o non si vedono spie, rispondi riconosciuta=false e spiega cosa fare per rifare la foto (più vicino, più luce, spia accesa, evitare i riflessi). Se non sei sicuro di una spia, dillo (confidenza «bassa») e dai le ipotesi più probabili.
- Il codice del simbolo (ISO 2575 / ISO 7000) indicalo SOLO se ne sei certo; altrimenti lascia la stringa vuota.
- Tieni conto del tipo di mezzo: nei camion e negli autobus esistono spie specifiche (EBS/ABS del rimorchio, retarder, pressione aria dei freni, SCR/AdBlue, DPF, tachigrafo, sospensioni pneumatiche, cambio automatizzato…); nelle moto ci sono spie diverse dalle auto.
- Veicoli elettrici e ibridi: NON suggerire mai di toccare o tagliare i cavi arancioni ad alta tensione; distingui la rete a 12 V dall'alta tensione.
- Azioni: passi brevi e numerati, il primo è sempre il più importante per la sicurezza. Niente consigli pericolosi (non aprire il tappo del radiatore a motore caldo, non lavorare su impianti ad alta tensione).
- Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo e senza ``` , con questa forma:
{"riconosciuta": true|false, "confidenza": "alta"|"media"|"bassa", "spie": [{"nome": "", "colore": "rosso"|"giallo"|"verde"|"blu"|"bianco", "urgenza": "critica"|"alta"|"media"|"informazione", "simbolo_iso": "", "aspetto": "", "significato": "", "azioni": ["", ""], "cause": ["", ""]}], "avviso_sicurezza": "", "note": ""}
- «aspetto»: come è fatto il simbolo, in poche parole (es. «triangolo giallo con punto esclamativo», «oliatore rosso con goccia»).
- «avviso_sicurezza»: una frase di pericolo se serve fermarsi (altrimenti stringa vuota). «note»: consigli per rifare la foto o osservazioni (breve). Massimo 6 spie."""

_AD_CHAT = """Sei un esperto di diagnostica dei veicoli e di soccorso stradale. Rispondi in italiano semplice, con frasi brevi e passi numerati, a domande su una spia del cruscotto già analizzata. Priorità alla sicurezza: se c'è pericolo dillo per primo.
Non dare istruzioni su impianti ad alta tensione (cavi arancioni) né su interventi che richiedono un'officina. Se non sei sicuro, dillo. Massimo circa 150 parole. Solo testo semplice e **grassetto**."""


# ---------------------------------------------------------------------------------------------------------------------
# i fornitori di intelligenza artificiale: quello dell'app (a pagamento, del proprietario) e quelli che sceglie chi usa l'app
# ---------------------------------------------------------------------------------------------------------------------
AD_PROVIDER = {
    "anthropic": {"nome": "Claude (Anthropic)", "secret": "ANTHROPIC_API_KEY", "modello": AD_MODELLO, "chiave_link": "https://console.anthropic.com/", "gratis": "a pagamento (si paga a consumo)"},
    "gemini": {"nome": "Google Gemini", "secret": "GEMINI_API_KEY", "modello": "gemini-2.0-flash", "chiave_link": "https://aistudio.google.com/apikey", "gratis": "ha una fascia gratuita con limiti (la chiave è gratuita)"},
    "openai": {"nome": "ChatGPT (OpenAI)", "secret": "OPENAI_API_KEY", "modello": "gpt-4o-mini", "url": "https://api.openai.com/v1/chat/completions", "chiave_link": "https://platform.openai.com/api-keys", "gratis": "a pagamento (si paga a consumo)"},
    "openrouter": {"nome": "OpenRouter (anche modelli gratuiti)", "secret": "OPENROUTER_API_KEY", "modello": "google/gemma-4-31b-it:free", "url": "https://openrouter.ai/api/v1/chat/completions", "chiave_link": "https://openrouter.ai/keys",
                   "gratis": "gratuita solo con i modelli che finiscono con «:free» (limiti: 20 richieste al minuto e 50 al giorno); gli altri modelli si pagano con i crediti"},
    "altra": {"nome": "Un'altra IA (compatibile con OpenAI)", "secret": "ALTRA_IA_KEY", "modello": "", "url": "", "chiave_link": "", "gratis": "dipende dal servizio"},
}
AD_ORDINE = ["anthropic", "gemini", "openai", "openrouter", "altra"]


def _ad_secret(nome):
    try:
        return str(st.secrets.get(nome, "") or "").strip()
    except Exception:
        return ""


def _ad_chiave():
    """La chiave di Claude messa dall'amministratore (la stessa dell'assistente intelligente)."""
    return _ad_secret("ANTHROPIC_API_KEY")


def ad_cfg(prov):
    """{key, fonte ('app' = messa dall'amministratore, 'mia' = scritta da chi usa l'app in questa sessione), modello, url}. La chiave 'mia' resta SOLO nella sessione: non viene salvata."""
    d = AD_PROVIDER.get(prov) or AD_PROVIDER["anthropic"]
    key, fonte = _ad_secret(d["secret"]), "app"
    if not key:
        key, fonte = str(st.session_state.get(f"ad_k_{prov}", "") or "").strip(), "mia"
    mod = str(st.session_state.get(f"ad_m_{prov}", "") or "").strip() or _ad_secret("DIAGNOSI_MODELLO" if prov == "anthropic" else f"DIAGNOSI_MODELLO_{prov.upper()}") or d.get("modello", "")
    url = str(st.session_state.get(f"ad_u_{prov}", "") or "").strip() or _ad_secret(f"DIAGNOSI_URL_{prov.upper()}") or d.get("url", "")
    return {"key": key, "fonte": fonte if key else "", "modello": mod, "url": url}


def ad_provider_scelto():
    """Quale fornitore si usa: quello scelto da chi usa l'app, altrimenti il primo con una chiave dell'amministratore, altrimenti Claude."""
    sc = st.session_state.get("ad_prov")
    if sc in AD_PROVIDER:
        return sc
    for k in AD_ORDINE:
        if _ad_secret(AD_PROVIDER[k]["secret"]):
            return k
    return "anthropic"


def ad_attivo():
    """True se il fornitore scelto ha una chiave (dell'amministratore o di chi usa l'app) e non è spento da DIAGNOSI_AI."""
    try:
        spento = str(st.secrets.get("DIAGNOSI_AI", "")).strip().lower() in ("no", "off", "0", "false", "spento")
    except Exception:
        spento = False
    if spento:
        return False
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    return bool(cfg["key"]) and (prov != "altra" or bool(cfg["url"] and cfg["modello"]))


@st.cache_resource
def _ad_contatori():
    return {}


def _ad_limite_giorno():
    try:
        return int(st.secrets.get("DIAGNOSI_MAX_GIORNO", 40))
    except Exception:
        return 40


def ad_puo(adesso=None):
    """True se i limiti (all'ora per sessione, al giorno per l'app) non sono superati; in tal caso conta l'analisi. Valgono solo per le chiavi dell'amministratore: chi usa la PROPRIA chiave ha i suoi limiti."""
    adesso = adesso or time.time()
    orari = [t for t in st.session_state.get("_ad_orari", []) if adesso - t < 3600]
    if len(orari) >= AD_MAX_ORA:
        st.session_state["_ad_orari"] = orari
        return False
    oggi_ = date.today().isoformat()
    c = _ad_contatori()
    if c.get(oggi_, 0) >= _ad_limite_giorno():
        return False
    for k in [k for k in c if k != oggi_]:
        c.pop(k, None)
    c[oggi_] = c.get(oggi_, 0) + 1
    orari.append(adesso)
    st.session_state["_ad_orari"] = orari
    return True


def _ad_modello():
    return ad_cfg("anthropic")["modello"] or AD_MODELLO


# ---------------------------------------------------------------------------------------------------------------------
# la foto e la richiesta al modello
# ---------------------------------------------------------------------------------------------------------------------
def ad_comprimi(dati):
    """La foto in JPEG, al massimo 1568 px per lato (più leggera e sufficiente). Ritorna (bytes, media_type) o (None, None)."""
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(dati))
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((1568, 1568))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=85, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return None, None


def _ad_parse(testo):
    """Estrae l'oggetto JSON dalla risposta (anche se il modello ha aggiunto del testo o i backtick)."""
    t = (testo or "").strip()
    t = re.sub(r"^```(?:json)?|```$", "", t.strip(), flags=re.M).strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        d = json.loads(t[i:j + 1])
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    spie = []
    for s in (d.get("spie") or [])[:6]:
        if not isinstance(s, dict) or not str(s.get("nome") or "").strip():
            continue
        col = str(s.get("colore") or "").lower().strip()
        col = {"arancio": "giallo", "arancione": "giallo", "ambra": "giallo", "bianca": "bianco", "rossa": "rosso", "gialla": "giallo"}.get(col, col)
        urg = str(s.get("urgenza") or "").lower().strip()
        spie.append({"nome": str(s["nome"]).strip()[:140], "colore": col if col in ("rosso", "giallo", "verde", "blu", "bianco") else "giallo",
                     "urgenza": urg if urg in ("critica", "alta", "media", "informazione") else ("critica" if col == "rosso" else "media"),
                     "simbolo_iso": str(s.get("simbolo_iso") or "").strip()[:40], "aspetto": str(s.get("aspetto") or "").strip()[:120], "significato": str(s.get("significato") or "").strip()[:500],
                     "azioni": [str(x).strip()[:300] for x in (s.get("azioni") or []) if str(x).strip()][:8], "cause": [str(x).strip()[:160] for x in (s.get("cause") or []) if str(x).strip()][:8]})
    return {"riconosciuta": bool(d.get("riconosciuta")) and bool(spie), "confidenza": str(d.get("confidenza") or "bassa").lower(), "spie": spie,
            "avviso_sicurezza": str(d.get("avviso_sicurezza") or "").strip()[:400], "note": str(d.get("note") or "").strip()[:500]}


def _ad_invia(prov, cfg, system, turni, jpeg, max_tokens, json_out=False):
    """Una richiesta a UN fornitore. turni = [("u"|"a", testo), ...]; la foto va col primo turno dell'utente. Ritorna (testo, None) oppure (None, errore) con errore in: chiave, limite, rete, rifiuto, formato."""
    import requests
    img = base64.b64encode(jpeg).decode() if jpeg else ""
    try:
        if prov == "anthropic":
            msgs = []
            for i, (ruolo, testo) in enumerate(turni):
                if i == 0 and img:
                    msgs.append({"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img}}, {"type": "text", "text": testo}]})
                else:
                    msgs.append({"role": "user" if ruolo == "u" else "assistant", "content": testo})
            r = requests.post(AD_URL, timeout=(8, 60), headers={"x-api-key": cfg["key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
                              json={"model": cfg["modello"] or AD_MODELLO, "max_tokens": max_tokens, "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}], "messages": msgs})
        elif prov == "gemini":
            cont = []
            for i, (ruolo, testo) in enumerate(turni):
                parti = ([{"inline_data": {"mime_type": "image/jpeg", "data": img}}] if (i == 0 and img) else []) + [{"text": testo}]
                cont.append({"role": "user" if ruolo == "u" else "model", "parts": parti})
            corpo = {"systemInstruction": {"parts": [{"text": system}]}, "contents": cont, "generationConfig": {"maxOutputTokens": max_tokens}}
            if json_out:
                corpo["generationConfig"]["responseMimeType"] = "application/json"
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['modello']}:generateContent", timeout=(8, 60), headers={"x-goog-api-key": cfg["key"], "content-type": "application/json"}, json=corpo)
        else:                                                           # OpenAI, OpenRouter e ogni servizio compatibile
            msgs = [{"role": "system", "content": system}]
            for i, (ruolo, testo) in enumerate(turni):
                if i == 0 and img:
                    msgs.append({"role": "user", "content": [{"type": "text", "text": testo}, {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + img}}]})
                else:
                    msgs.append({"role": "user" if ruolo == "u" else "assistant", "content": testo})
            corpo_oa = {"max_tokens": max_tokens, "messages": msgs}
            elenco_m = [m_.strip() for m_ in str(cfg["modello"]).split(",") if m_.strip()]
            if prov == "openrouter" and len(elenco_m) > 1:
                corpo_oa["models"] = elenco_m[:3]                              # OpenRouter prova i modelli in ordine: i gratuiti cambiano spesso
            else:
                corpo_oa["model"] = elenco_m[0] if elenco_m else cfg["modello"]
            r = requests.post(cfg["url"], timeout=(8, 60), headers={"Authorization": "Bearer " + cfg["key"], "content-type": "application/json"}, json=corpo_oa)
        if r.status_code in (401, 403):
            return None, "chiave"
        if r.status_code == 400 and prov == "gemini" and "API key" in str(r.text if hasattr(r, "text") else r.json())[:400]:
            return None, "chiave"
        if r.status_code == 429:
            return None, "limite"
        if r.status_code == 402:
            return None, "pagamento"                                               # modello a pagamento e nessun credito
        if r.status_code in (400, 404) and prov != "gemini":
            return None, "modello"                                                 # il modello non esiste più o non legge le immagini
        if r.status_code != 200:
            return None, "rete"
        dati = r.json()
        if prov == "anthropic":
            if dati.get("stop_reason") == "refusal":
                return None, "rifiuto"
            return "".join(b.get("text", "") for b in dati.get("content", []) if b.get("type") == "text"), None
        if prov == "gemini":
            cand = (dati.get("candidates") or [{}])[0]
            if cand.get("finishReason") in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT"):
                return None, "rifiuto"
            return "".join(p_.get("text", "") for p_ in ((cand.get("content") or {}).get("parts") or [])), None
        ch = (dati.get("choices") or [{}])[0]
        msg = (ch.get("message") or {}).get("content")
        if isinstance(msg, list):
            msg = "".join(x.get("text", "") for x in msg if isinstance(x, dict))
        return (msg or ""), None
    except Exception:
        return None, "rete"


def ad_analizza(jpeg, mezzo):
    """Manda la foto al fornitore scelto. Ritorna il risultato (dict) oppure {'errore': motivo}."""
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if not cfg["key"] or (prov == "altra" and not (cfg["url"] and cfg["modello"])):
        return {"errore": "chiave"}
    if cfg["fonte"] == "app" and not ad_puo():
        return {"errore": "limite"}
    testo, err = _ad_invia(prov, cfg, _AD_REGOLE, [("u", f"Mezzo: {mezzo}. Riconosci le spie accese in questa foto del cruscotto.")], jpeg, 1500, json_out=True)
    if err:
        return {"errore": err}
    ris = _ad_parse(testo)
    return ris if ris is not None else {"errore": "formato", "testo": (testo or "")[:1500]}


_AD_REGOLE_TESTO = _AD_REGOLE.replace("Ti viene mostrata la FOTO di un cruscotto con una o più spie accese.", "Ti viene descritta A PAROLE una spia del cruscotto o un guasto del mezzo (non c'è la foto).")


def ad_analizza_testo(domanda, mezzo):
    """Come ad_analizza, ma da una descrizione scritta (spia o guasto), senza foto. Ritorna il risultato (dict) oppure {'errore': motivo}."""
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if not cfg["key"] or (prov == "altra" and not (cfg["url"] and cfg["modello"])):
        return {"errore": "chiave"}
    if cfg["fonte"] == "app" and not ad_puo():
        return {"errore": "limite"}
    testo, err = _ad_invia(prov, cfg, _AD_REGOLE_TESTO, [("u", f"Mezzo: {mezzo}. Problema descritto a parole: {str(domanda)[:400]}")], None, 1500, json_out=True)
    if err:
        return {"errore": err}
    ris = _ad_parse(testo)
    return ris if ris is not None else {"errore": "formato", "testo": (testo or "")[:1500]}


def ad_chiedi(storia, jpeg, mezzo, riassunto):
    """Una domanda di approfondimento sulla foto già analizzata. Ritorna il testo o None."""
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if not cfg["key"] or (cfg["fonte"] == "app" and not ad_puo()):
        return None
    turni = [("u", f"Mezzo: {mezzo}. Analisi già fatta: {riassunto}\n\nDomanda: {storia[0][1]}")] + [(r_, t_) for r_, t_ in storia[1:]]
    testo, err = _ad_invia(prov, cfg, _AD_CHAT, turni, jpeg, 700)
    return (testo or "").strip()[:2500] or None if not err else None


# ---------------------------------------------------------------------------------------------------------------------
# collegamento al catalogo verificato
# ---------------------------------------------------------------------------------------------------------------------
_AD_STOP = {"di", "del", "della", "dei", "delle", "e", "ed", "il", "la", "lo", "le", "un", "una", "in", "a", "al", "per", "con", "da", "su", "spia", "sistema", "avviso", "guasto"}


def _ad_token(t):
    return {w for w in re.findall(r"[a-zà-ù0-9]{3,}", (t or "").lower()) if w not in _AD_STOP}


def ad_abbina_catalogo(nome):
    """La voce del catalogo (verificato) più simile al nome che ha dato l'IA, oppure None."""
    if "_AE_SPIE" not in globals():
        return None
    a = _ad_token(nome)
    migliore, punti = None, 0.0
    for s in _AE_SPIE:
        b = _ad_token(s["nome"])
        if not a or not b:
            continue
        com = a & b
        sc = len(com) / max(1, min(len(a), len(b)))
        if com and sc > punti:
            migliore, punti = s, sc
    return migliore if punti >= 0.5 else None


# ---------------------------------------------------------------------------------------------------------------------
# testo del report
# ---------------------------------------------------------------------------------------------------------------------
def ad_testo_report(ris, mezzo, data_=None):
    righe = [f"DIAGNOSI SPIE DEL CRUSCOTTO — {data_ or datetime.now().strftime('%d/%m/%Y %H:%M')}", f"Mezzo: {mezzo}", ""]
    if ris.get("avviso_sicurezza"):
        righe += ["⚠️ " + ris["avviso_sicurezza"], ""]
    for s in ris.get("spie", []):
        righe += [f"SPIA: {s['nome']}", f"Colore: {s['colore']} · Urgenza: {s['urgenza']}"]
        if s.get("simbolo_iso"):
            righe.append(f"Simbolo: {s['simbolo_iso']} (da verificare)")
        if s.get("significato"):
            righe.append(f"Significato: {s['significato']}")
        if s.get("azioni"):
            righe += ["Cosa fare:"] + [f"{i}. {a}" for i, a in enumerate(s["azioni"], 1)]
        if s.get("cause"):
            righe.append("Possibili cause: " + ", ".join(s["cause"]))
        righe.append("")
    righe.append(f"Affidabilità dell'analisi: {ris.get('confidenza', 'bassa')}. Diagnosi automatica con intelligenza artificiale: può sbagliare; vale il manuale del veicolo.")
    return "\n".join(righe)


# ---------------------------------------------------------------------------------------------------------------------
# la schermata
# ---------------------------------------------------------------------------------------------------------------------
_AD_CSS = """<style>
.ad-cornice{border:3px dashed #00acc1;border-radius:22px;padding:18px 10px;text-align:center;background:linear-gradient(135deg,rgba(0,172,193,.12),rgba(255,255,255,.7));margin:6px 0 10px}
.ad-cornice .ico{font-size:2.6rem;line-height:1}.ad-cornice b{display:block;font-size:1.05rem;margin-top:4px;color:#004d5a}
.ad-pericolo{background:#b71c1c;color:#fff;border-radius:16px;padding:12px 14px;margin:8px 0;font-weight:900;font-size:1.05rem;box-shadow:0 0 0 3px #ffcdd2}
.ad-spia{border-radius:16px;padding:10px 14px;margin:8px 0;color:#1b2b2b;background:rgba(255,255,255,.92)}
.ad-spia.r{border-left:8px solid #c62828}.ad-spia.g{border-left:8px solid #f9a825}.ad-spia.v{border-left:8px solid #2e7d32}.ad-spia.b{border-left:8px solid #1565c0}
</style>"""
_AD_CSS2 = """<style>.ad-share{border-radius:14px;padding:13px 10px;text-align:center;font-weight:900;font-size:1.02rem;color:#fff;cursor:pointer;user-select:none;background:linear-gradient(135deg,#42a5f5,#0d47a1);box-shadow:0 5px 0 rgba(10,40,100,.35);-webkit-tap-highlight-color:transparent;margin:6px 0}.ad-share:active{transform:scale(.98)}</style>"""

_AD_JS = r"""
(function () {
  var w = window, doc = document;
  if (w.__adShare) return;
  w.__adShare = true;
  function avvisa(t, errore) {
    var el = doc.querySelector('[data-ad-msg]');
    if (el) { el.textContent = t; el.style.display = 'block'; el.style.color = errore ? '#b71c1c' : '#0f766e'; }
  }
  function inFile(b64) {
    var bin = atob(b64), n = bin.length, u = new Uint8Array(n);
    for (var i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
    return new File([u], 'spia-cruscotto.jpg', {type: 'image/jpeg'});
  }
  function copia(t) { try { return navigator.clipboard.writeText(t); } catch (e) { return Promise.resolve(); } }
  function condividi() {
    var d = w.__adFoto;
    if (!d || !d.b64) { avvisa('Prima scegli la foto.', true); return; }
    var f = inFile(d.b64);
    if (navigator.canShare && navigator.canShare({files: [f]}) && navigator.share) {
      navigator.share({files: [f], text: d.testo, title: 'Spia del cruscotto'}).then(function () {
        avvisa('Fatto: nella tua app di IA vedi la foto e le istruzioni. Se non vedi le istruzioni, incollale (le ho copiate).');
      }).catch(function (e) { avvisa(e && e.name === 'AbortError' ? 'Annullato.' : 'Non sono riuscito a condividere la foto: usa i bottoni qui sotto.', !(e && e.name === 'AbortError')); });
      copia(d.testo);
      return;
    }
    copia(d.testo).then(function () {
      avvisa('Questo telefono non può mandare la foto da qui. Ho copiato le istruzioni: apri la tua IA con i bottoni qui sotto, incolla le istruzioni e allega la foto.', true);
    });
  }
  doc.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('[data-ad-azione]') : null;
    if (!b) return;
    ev.preventDefault();
    if (b.getAttribute('data-ad-azione') === 'condividi') condividi();
  }, true);
})();
"""
_AD_APP_IA = [("ChatGPT", "https://chatgpt.com/"), ("Gemini", "https://gemini.google.com/app"), ("Claude", "https://claude.ai/new"), ("Copilot", "https://copilot.microsoft.com/"), ("Perplexity", "https://www.perplexity.ai/"), ("Grok", "https://grok.com/")]
_AD_COLORE = {"rosso": ("r", "🔴"), "giallo": ("g", "🟡"), "verde": ("v", "🟢"), "blu": ("b", "🔵"), "bianco": ("b", "⚪")}


def ad_prompt_libero(mezzo, domanda=None):
    """Le istruzioni da dare a una qualunque app di IA insieme alla foto (testo semplice, non JSON). Con «domanda» il problema è descritto a parole, senza foto."""
    cosa = f"In allegato c'è la FOTO del cruscotto di questo mezzo: {mezzo}. " if not domanda else f"Il mezzo è questo: {mezzo}. Descrivo il problema a parole: «{str(domanda)[:400]}». "
    return (f"Sei un esperto di diagnostica dei veicoli (auto, moto, camion e TIR, autobus, monopattini, mezzi agricoli) e di soccorso stradale. {cosa}"
            "Riconosci le spie accese e rispondi in italiano semplice, con frasi brevi. Per ogni spia scrivi: nome della spia; colore (rosso = fermati subito, giallo o arancio = avviso, officina a breve, verde o blu = informazione); urgenza; cosa significa; "
            "cosa fare subito, in passi numerati; possibili cause. Se una spia indica pericolo (pressione olio, freni, surriscaldamento, sterzo, aria dell'impianto frenante nei mezzi pesanti, alta tensione) scrivilo PER PRIMO in grassetto e dimmi se devo accostare e spegnere subito. "
            "Non inventare: se la foto non è chiara dimmelo e spiegami come rifarla. Nei veicoli elettrici non consigliarmi mai di toccare i cavi arancioni. Alla fine ricordami che sei un aiuto e che vale il manuale del mezzo.")


def _ad_inietta_foto(jpeg, prompt, sha):
    """Manda al browser la foto e le istruzioni (una volta per foto), così il tasto «Manda alla mia IA» può condividerle."""
    codice = "window.__adFoto={b64:" + json.dumps(base64.b64encode(jpeg).decode()) + ",testo:" + json.dumps(prompt) + "};"
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_AD_JS + codice) + ";P.document.head.appendChild(s);s.parentNode.removeChild(s);})();</script>")
    if "pn_inietta_una_volta" in globals():
        pn_inietta_una_volta("adfoto", sha, pagina)
    else:
        try:
            st.html(pagina, unsafe_allow_javascript=True)
        except Exception:
            pass


def _ad_scelta_ia():
    """Quale intelligenza artificiale usare: quella dell'app (se c'è) oppure una a scelta, con la chiave di chi usa l'app (tenuta solo nella sessione)."""
    prov = ad_provider_scelto()
    etichette = {k: AD_PROVIDER[k]["nome"] + (" ✅" if _ad_secret(AD_PROVIDER[k]["secret"]) else "") for k in AD_ORDINE}
    st.markdown("#### 🤖 Quale intelligenza artificiale uso?")
    scelta = st.selectbox("Intelligenza artificiale", AD_ORDINE, index=AD_ORDINE.index(prov), format_func=lambda k: etichette[k], key="ad_prov", label_visibility="collapsed") if "ad_prov" not in st.session_state \
        else st.selectbox("Intelligenza artificiale", AD_ORDINE, format_func=lambda k: etichette[k], key="ad_prov", label_visibility="collapsed")
    cfg = ad_cfg(scelta)
    d = AD_PROVIDER[scelta]
    if cfg["fonte"] == "app" and cfg["key"]:
        st.caption("✅ Uso la chiave messa dall'amministratore dell'app: il costo è suo, con i tetti giornalieri.")
    else:
        st.text_input(f"La tua chiave di {d['nome']}", type="password", key=f"ad_k_{scelta}", placeholder="incollala qui")
        st.caption(f"La chiave resta **solo in questa sessione**: non viene salvata e va solo a {d['nome']}. Costo: {d['gratis']}.")
        if scelta == "openrouter":
            st.caption("🆓 Per restare **gratis** usa solo modelli con «:free» nel nome e che leggano le immagini. Se un giorno non risponde più, quel modello gratuito è stato tolto: cambia il nome. Puoi scriverne più di uno separati da virgola (il secondo è di riserva).")
        if d.get("chiave_link"):
            st.link_button(f"🔑 Ottieni una chiave di {d['nome'].split(' (')[0]}", d["chiave_link"], width="stretch")
    if scelta == "altra":
        st.text_input("Indirizzo del servizio (come https://…/v1/chat/completions)", key="ad_u_altra", placeholder="https://…")
        st.text_input("Nome del modello (che sa leggere le immagini)", key="ad_m_altra", placeholder="es. pixtral-12b")
    else:
        st.text_input("Modello (puoi cambiarlo)", key=f"ad_m_{scelta}", placeholder=d.get("modello", ""))
    st.caption("I servizi gratuiti possono usare le foto per migliorarsi: **non inquadrare persone, targhe o documenti**, solo il cruscotto.")
    return scelta


def _ad_condividi_ia(jpeg, mezzo, sha):
    """Senza chiavi e senza pagare: la foto e le istruzioni vanno alla TUA app di IA (ChatGPT, Gemini, Claude, Copilot…) col menu «Condividi» del telefono."""
    prompt = ad_prompt_libero(mezzo)
    st.markdown("#### 🆓 Usa la tua app di intelligenza artificiale (senza pagare)")
    st.caption("Se hai già ChatGPT, Gemini, Claude, Copilot o un'altra IA sul telefono, puoi farle leggere la foto da lì: ti preparo foto e istruzioni.")
    _ad_inietta_foto(jpeg, prompt, sha)
    st.markdown(_AD_CSS2 + "<div class='ad-share' role='button' tabindex='0' data-ad-azione='condividi'>📤 Manda foto e istruzioni alla mia IA</div><div data-ad-msg style='display:none;margin:4px 0;font-weight:700;font-size:13.5px'></div>", unsafe_allow_html=True)
    cols = st.columns(3, gap="small")
    for i, (nome, url) in enumerate(_AD_APP_IA):
        cols[i % 3].link_button(nome, url, width="stretch")
    st.caption("Se il tasto qui sopra non apre la condivisione, apri la tua IA con uno di questi bottoni, **incolla le istruzioni** (qui sotto) e **allega la foto**.")
    st.code(prompt, language=None)


def _ad_numero_soccorso(v):
    return re.sub(r"[^\d+]", "", str((v or {}).get("soccorso_tel") or AD_SOCCORSO_PREDEFINITO))


def _ad_manuale_url(v, mezzo, nome):
    q = " ".join(x for x in ((v or {}).get("marca"), (v or {}).get("modello"), (v or {}).get("anno")) if x) if mezzo.startswith("Il veicolo") else mezzo
    return "https://www.google.com/search?q=" + urllib.parse.quote_plus(f"{q} spia {nome} significato manuale uso")


def _ad_riceve():
    """Il pulsante arancione (e, a scelta, il visore live): ritorna (nome, dati) quando arriva una foto."""
    arr = None
    if "_ca_pannello_caricamento" in globals():
        up = _ca_pannello_caricamento(st.session_state.get("ca_giro", 0), multi=False)
        if up is not None:
            arr = (up.name, up.getvalue())
        b = st.session_state.pop("ca_bozza_in", None)
        if b and b.get("dati"):
            arr = (b.get("nome") or "foto", b["dati"])
    return arr


def _ad_risultato(ris, v, mezzo, sha, jpeg):
    spie = ris.get("spie", [])
    rosse = [s for s in spie if s["colore"] == "rosso" or s["urgenza"] == "critica"]
    st.markdown("#### 🚨 Risultato della diagnosi")
    if rosse:
        st.markdown(f"<div class='ad-pericolo'>🔴 PERICOLO CRITICO — ARRESTO IMMEDIATO<br><small style='font-weight:700'>{_h_ap.escape(ris.get('avviso_sicurezza') or 'Accosta subito in un punto sicuro e spegni il veicolo. Non ripartire finché non hai capito il problema.')}</small></div>", unsafe_allow_html=True)
        st.error("Se senti odore acre, vedi fumo o c'è rischio per le persone: scendi, allontanati e chiama il **112**.")
    elif ris.get("avviso_sicurezza"):
        st.warning("⚠️ " + ris["avviso_sicurezza"])
    for s in spie:
        cl, ic = _AD_COLORE.get(s["colore"], ("g", "🟡"))
        righe = f"<b>{ic} Spia: {_h_ap.escape(s['nome'])}</b><br><small><b>Colore:</b> {s['colore'].capitalize()} · <b>Urgenza:</b> {'⚠️ ' if s['urgenza'] in ('critica', 'alta') else ''}{s['urgenza'].capitalize()}</small>"
        if s.get("simbolo_iso"):
            righe += f"<br><small><b>Codice simbolo:</b> {_h_ap.escape(s['simbolo_iso'])} <i>(indicato dall'IA: da verificare)</i></small>"
        if s.get("significato"):
            righe += f"<br><small><b>Significato:</b> {_h_ap.escape(s['significato'])}</small>"
        st.markdown(f"<div class='ad-spia {cl}'>{righe}</div>", unsafe_allow_html=True)
        if s.get("azioni"):
            st.markdown("**📋 Azione suggerita:**\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(s["azioni"], 1)))
        if s.get("cause"):
            st.caption("Possibili cause: " + ", ".join(s["cause"]) + ".")
        cat = ad_abbina_catalogo(s["nome"])
        if cat:
            with st.expander(f"✅ Nel catalogo verificato: {cat['icona']} {cat['nome']}"):
                st.markdown(f"**Urgenza:** {cat['urgenza']}  \n**Significato:** {cat['significato']}")
                st.markdown("**Cosa fare subito**\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(cat["azioni"], 1)))
        if "bd_mostra_abbinamento" in globals():
            try:
                bd_mostra_abbinamento(s["nome"], s["colore"], hashlib.md5(f"{sha}{s['nome']}".encode("utf-8")).hexdigest()[:8])
            except Exception:
                pass
        st.link_button("📖 Cerca nel manuale", _ad_manuale_url(v, mezzo, s["nome"]), width="stretch")
    conf = ris.get("confidenza", "bassa")
    st.caption(f"Affidabilità dell'analisi: **{conf}**. L'IA può sbagliare: se la spia è **ROSSA** fermati comunque, e per il tuo mezzo vale il manuale.")
    if ris.get("note"):
        st.info("💡 " + ris["note"])


def _ad_azioni(ris, v, mezzo, sha, jpeg, vid):
    c1, c2 = st.columns(2, gap="small")
    tel = _ad_numero_soccorso(v)
    c1.link_button("🚨 Chiama il soccorso stradale", "tel:" + tel, width="stretch")
    c2.link_button("🆘 Chiama il 112", "tel:112", width="stretch")
    ass = (((v or {}).get("scadenze") or {}).get("assicurazione") or {}).get("telefono")
    if ass:
        st.link_button("📞 Assistenza della mia assicurazione", "tel:" + re.sub(r"[^\d+]", "", ass), width="stretch")
    with st.expander("⚙️ Numero del soccorso stradale"):
        with st.form(f"ad_tel_{vid or 'x'}", border=False):
            n = st.text_input("Numero da chiamare con un tocco", value=(v or {}).get("soccorso_tel") or "803.116", key=f"ad_telv_{vid or 'x'}")
            if st.form_submit_button("💾 Salva", width="stretch") and vid:
                _au_mod(vid, lambda x, n=n.strip(): x.__setitem__("soccorso_tel", n), "Auto: numero soccorso")
                st.rerun()
        st.caption("Predefinito: ACI Soccorso Stradale (803.116). Controlla che sia il numero giusto per te (assicurazione, costruttore, flotta).")
    b1, b2 = st.columns(2, gap="small")
    salvata = st.session_state.get("ad_salvate", {}).get(sha)
    if vid and not salvata and b1.button("💾 Salva nel veicolo", key=f"ad_salva_{sha[:6]}", width="stretch"):
        try:
            rif = (_fa_salva_files([_SpUp(f"spia_{date.today().isoformat()}.jpg", jpeg)]) or [{}])[0]
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare la foto: {ex}")
            rif = None
        if rif is not None:
            voce = {"id": uuid.uuid4().hex[:10], "data": date.today().isoformat(), "mezzo": mezzo, "spie": ris.get("spie", []), "confidenza": ris.get("confidenza", ""), "sintesi": ad_testo_report(ris, mezzo), "files": [rif]}
            _au_mod(vid, lambda x, voce=voce: x.setdefault("diagnosi", []).append(voce), "Auto: diagnosi spie")
            st.session_state.setdefault("ad_salvate", {})[sha] = voce
            if "ls_segna_archiviato" in globals():
                ls_segna_archiviato()
            st.session_state["messaggio"] = "✅ Diagnosi salvata nel veicolo."
            st.rerun()
    elif salvata:
        b1.success("✅ Salvata")
    with b2:
        titolo = "Diagnosi spie: " + ", ".join(s["nome"] for s in ris.get("spie", [])[:2])
        _fa_inv_voce(f"ad_{sha[:8]}", "📤 Condividi il report", titolo, [("Report", ad_testo_report(ris, mezzo))], list(salvata["files"]) if salvata else [])
    if not salvata and vid:
        st.caption("Salva nel veicolo per allegare anche la foto quando condividi.")


def _ad_chat(ris, mezzo, sha, jpeg):
    st.markdown("#### 💬 Chiedi all'assistente")
    chiave = f"ad_chat_{sha}"
    storia = st.session_state.setdefault(chiave, [])
    for ruolo, testo in storia:
        st.markdown(("🧑 **Tu:** " if ruolo == "u" else "🤖 **Assistente:** ") + testo)
    if not ad_attivo():
        st.caption("La chat con l'assistente si accende con la chiave dell'intelligenza artificiale.")
        return
    if len([1 for r, _t in storia if r == "u"]) >= 6:
        st.caption("Hai fatto 6 domande su questa foto: per altre, scatta una nuova foto.")
        return
    with st.form(f"ad_chatf_{sha[:8]}_{len(storia)}", border=False):
        dom = st.text_input("Una domanda su questa spia", key=f"ad_chatq_{sha[:8]}_{len(storia)}", placeholder="es. Posso arrivare fino a casa? Quanto costa di solito?", max_chars=400)
        if st.form_submit_button("📨 Chiedi", width="stretch") and dom.strip():
            storia.append(("u", dom.strip()))
            with st.spinner("Sto pensando…"):
                r = ad_chiedi(storia, jpeg, mezzo, ad_testo_report(ris, mezzo))
            storia.append(("a", r or "Non riesco a rispondere adesso (rete o limite raggiunto). Riprova fra poco."))
            st.rerun()


def _ad_storico(v):
    voci = sorted(v.get("diagnosi", []), key=lambda x: x.get("data", ""), reverse=True)
    if not voci:
        return
    st.markdown("#### 🗂️ Diagnosi salvate")
    vedi = st.session_state.setdefault("au_vedi", [])
    for d_ in voci:
        titolo = f"Diagnosi del {_au_it(d_.get('data'))}: " + ", ".join(s["nome"] for s in d_.get("spie", [])[:2])
        st.markdown(f"<div class='au-card'><b class='t'>🔍 {_h_ap.escape(titolo)}</b><br><small>{_h_ap.escape(d_.get('mezzo', ''))} · affidabilità {_h_ap.escape(d_.get('confidenza', ''))}</small></div>", unsafe_allow_html=True)
        _au_f_allegati(v["id"], "diagnosi", d_)
        b1, b2 = st.columns(2, gap="small")
        with b1:
            _fa_inv_voce(f"adv_{d_['id']}", "📤 Invia", titolo, [("Report", d_.get("sintesi", ""))], list(d_.get("files") or []))
        if b2.button("🗑️ Elimina", key=f"ad_del_{d_['id']}", width="stretch"):
            _au_dialogo_togli(v["id"], "diagnosi", d_["id"], titolo)


def ad_pagina(v):
    """La schermata «Diagnosi visiva spie»."""
    vid = (v or {}).get("id")
    st.markdown(_AD_CSS, unsafe_allow_html=True)
    top1, top2 = st.columns([1, 3], gap="small")
    if top1.button("← Chiudi", key="ad_chiudi", width="stretch"):
        if vid:
            st.session_state[f"au_em_{vid}"] = "🚦 Spie del cruscotto"
        st.session_state.pop("ad_libera", None)
        st.rerun()
    top2.markdown("### 🔍 Diagnosi visiva delle spie")
    opz = list(AD_MEZZI)
    nome_v = _au_nome(v) if v else ""
    if not v:
        opz = opz[1:]
    mezzo_sel = st.selectbox("Di che mezzo è la spia", opz, format_func=lambda x: f"Il mio veicolo: {nome_v}" if x == "Il veicolo scelto" else x, key="ad_mezzo")
    desc_mezzo = (f"{_au_nome(v)} ({v.get('alimentazione', '')}, {v.get('anno', '')})".replace(", )", ")").replace(" ()", "") if mezzo_sel == "Il veicolo scelto" else mezzo_sel)
    if "bd_scope" in globals():
        _bd_form_modello()                                                  # facoltativo: marca, modello e anno scritti a mano
        scope_ad = bd_scope(v)
        st.session_state["ad_scope"] = scope_ad
        if (st.session_state.get("mz_marca") or st.session_state.get("mz_modello")):
            desc_mezzo = bd_scope_desc(scope_ad, v)
        if bd_attiva():
            bd_checkbox_contribuisci()
    else:
        scope_ad = {}
    # ---- il «visore»: cornice, fotocamera e galleria
    st.markdown("<div class='ad-cornice'><div class='ico'>🔴</div><b>Inquadra la spia accesa</b><small>Cruscotto acceso, spia ben visibile, foto nitida e senza riflessi. Per fare luce usa la torcia del telefono.</small></div>", unsafe_allow_html=True)
    arr = _ad_riceve()
    with st.expander("🎥 Visore live (se il tuo telefono lo permette)"):
        try:
            cam = st.camera_input("Inquadra la spia", key="ad_cam", label_visibility="collapsed")
        except Exception:
            cam = None
        if cam is not None:
            arr = (getattr(cam, "name", "foto.jpg") or "foto.jpg", cam.getvalue())
    if arr:
        jpeg, _mt = ad_comprimi(arr[1])
        if jpeg is None:
            st.error("Non riesco a leggere questa foto: scegli un'immagine (JPG o PNG).")
        else:
            sha = hashlib.sha256(jpeg).hexdigest()
            if st.session_state.get("ad_sha") != sha:
                st.session_state["ad_sha"] = sha
                st.session_state["ad_foto"] = jpeg
                st.session_state["ad_mezzo_usato"] = desc_mezzo
                st.session_state.pop("ad_ris", None)
    jpeg = st.session_state.get("ad_foto")
    sha = st.session_state.get("ad_sha")
    if not jpeg:
        st.caption("Scatta una foto con **📷 Scatta foto** o scegli **🖼️ Dalla galleria**. " + ("" if ad_attivo() else "Senza l'intelligenza artificiale attiva puoi usare la tua app di IA, una tua chiave gratuita, oppure il catalogo delle spie."))
        _ad_storico(v) if v else None
        return
    st.image(jpeg, width="stretch", caption="La tua foto")
    if st.button("🗑️ Togli questa foto", key="ad_togli", width="stretch"):
        for k in ("ad_foto", "ad_sha", "ad_ris"):
            st.session_state.pop(k, None)
        st.session_state["ca_giro"] = st.session_state.get("ca_giro", 0) + 1
        st.rerun()
    mezzo = st.session_state.get("ad_mezzo_usato") or desc_mezzo
    scelta_ia = _ad_scelta_ia()
    cfg_ia = ad_cfg(scelta_ia)
    firma = (scelta_ia, hashlib.sha256((cfg_ia["key"] or "").encode()).hexdigest()[:10], cfg_ia["modello"], cfg_ia["url"])
    if st.session_state.get("ad_firma") != firma:                      # se cambia l'IA, la chiave o il modello si rifà l'analisi
        st.session_state["ad_firma"] = firma
        st.session_state.pop("ad_ris", None)
    # ---- l'analisi
    if ad_attivo():
        if "ad_ris" not in st.session_state:
            st.info("🔒 La foto del cruscotto viene mandata al servizio di intelligenza artificiale per riconoscere la spia. Non inquadrare persone, targhe o documenti.")
            with st.spinner("Riconosco la spia… (qualche secondo)"):
                st.session_state["ad_ris"] = ad_analizza(jpeg, mezzo)
        ris = st.session_state["ad_ris"]
        err = ris.get("errore")
        if err:
            msg = {"chiave": "La chiave dell'intelligenza artificiale non è valida o è scaduta.", "limite": "Hai raggiunto il limite di analisi (per ora o per oggi). Riprova più tardi.",
                   "rete": "Non riesco a collegarmi al servizio adesso. Riprova fra poco.", "rifiuto": "Il servizio non ha potuto analizzare questa foto.", "formato": "La risposta non era leggibile. Riprova con una foto più nitida.",
                   "pagamento": "Questo modello è a pagamento e non ci sono crediti: scegli un modello che finisce con «:free».", "modello": "Questo modello non esiste più o non legge le immagini: cambia il nome del modello (scegline uno gratuito che accetti le immagini)."}.get(err, "Qualcosa non ha funzionato.")
            st.warning(msg + " Intanto confronta la foto con il catalogo qui sotto.")
            if st.button("🔄 Riprova", key="ad_riprova", width="stretch"):
                st.session_state.pop("ad_ris", None)
                st.rerun()
            ae_spie(v)
        elif not ris.get("riconosciuta"):
            st.warning("Non sono riuscito a riconoscere una spia in questa foto." + (" " + ris["note"] if ris.get("note") else " Riprova da più vicino, con più luce e la spia accesa."))
            ae_spie(v)
        else:
            _ad_risultato(ris, v, mezzo, sha, jpeg)
            if "bd_registra_risultato" in globals() and bd_attiva() and st.session_state.get("bd_contrib", True) and not st.session_state.get(f"ad_reg_{sha}"):
                st.session_state[f"ad_reg_{sha}"] = True                    # una volta per foto: le spie riconosciute entrano nella base condivisa (solo testo)
                nuove, agg = bd_registra_risultato(ris, scope_ad, "IA (" + AD_PROVIDER[ad_provider_scelto()]["nome"].split(" (")[0] + ")")
                st.session_state[f"ad_reg_msg_{sha}"] = f"📚 Aggiunta alla base condivisa: {nuove} nuove, {agg} già presenti (solo testo, senza la foto)." if (nuove or agg) else ""
            if st.session_state.get(f"ad_reg_msg_{sha}"):
                st.caption(st.session_state[f"ad_reg_msg_{sha}"])
            _ad_azioni(ris, v, mezzo, sha, jpeg, vid)
            _ad_chat(ris, mezzo, sha, jpeg)
    else:
        st.info("🤖 L'**intelligenza artificiale non è attiva**: la foto non può essere riconosciuta da sola. **Senza pagare** puoi: (1) mandare foto e istruzioni alla **tua app di IA** (qui sotto); (2) incollare qui sopra **una tua chiave gratuita** (per esempio di Gemini); oppure (3) confrontare la foto col **catalogo** (filtra per colore o cerca per nome).")
        c1, c2 = st.columns(2, gap="small")
        c1.link_button("🚨 Chiama il soccorso stradale", "tel:" + _ad_numero_soccorso(v), width="stretch")
        c2.link_button("🆘 Chiama il 112", "tel:112", width="stretch")
        _ad_condividi_ia(jpeg, mezzo, sha)
        ae_spie(v)
    if ad_attivo():
        _ad_condividi_ia(jpeg, mezzo, sha)
    if v:
        _ad_storico(v)
