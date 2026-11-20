# -*- coding: utf-8 -*-
"""🤖 INTELLIGENZA ARTIFICIALE CON CHIAVI GRATUITE (e DeepSeek, se c'è la sua chiave) — un solo punto per tutta l'app.

• FORNITORI (tutti con lo stesso «linguaggio» compatibile OpenAI): DeepSeek, Google Gemini, Mistral, Groq, OpenRouter (modelli :free), NVIDIA NIM, Cloudflare Workers AI, Cohere.
  Le chiavi stanno SOLO nei Secrets di Streamlit (DEEPSEEK_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, NVIDIA_API_KEY,
  CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID, COHERE_API_KEY). Senza nessuna chiave l'app funziona come prima (lettura locale).
• I nomi dei modelli cambiano spesso: l'app chiede a ogni servizio l'elenco dei modelli e sceglie da sola quello giusto (si può forzare con IA_MODELLO_<SERVIZIO>).
  Se un servizio risponde «troppe richieste» o «chiave sbagliata», per un po' si passa al successivo.
• DOCUMENTI SANITARI (il_leggi_sanitario): il primo servizio disponibile (DeepSeek, poi Gemini, Mistral, Groq…) legge la foto o il PDF e li CLASSIFICA con regole precise.
  Se il documento è SCRITTO A MANO o la lettura è incerta, lo fanno leggere anche altri 1–2 servizi; poi un «arbitro» confronta le letture e scrive UNA descrizione coerente con il tema
  medico, dichiarando i LIMITI della lettura e cosa VERIFICARE. Niente si salva senza la conferma della persona.
• il_consenso_immagine: lo stesso metodo (più letture + arbitro) per altre foto, per esempio le spie dell'auto.
• il_testo: una domanda di solo testo al primo servizio libero (serve anche per le traduzioni).
Prefisso: il_"""
import base64 as _il_b64
import hashlib as _il_hl
import html as _il_html
import io as _il_io
import json as _il_json
import os as _il_os
import re as _il_re
import threading as _il_thr
import time as _il_time

import requests as _il_req
import streamlit as st

IL_FORNITORI = {
    "deepseek": {"nome": "DeepSeek", "base": "https://api.deepseek.com/v1", "secret": ["DEEPSEEK_API_KEY"], "vista": ["deepseek-v4-flash-vision-exp"],
                 "testo": ["deepseek-chat", "deepseek-v4-flash"], "link": "https://platform.deepseek.com/api_keys",
                 "costo": "a pagamento: ricarica minima di pochi dollari, ogni documento costa meno di un centesimo", "dati": "server in Cina; i dati non servono ad addestrare (secondo le condizioni)"},
    "gemini": {"nome": "Google Gemini", "base": "https://generativelanguage.googleapis.com/v1beta/openai", "secret": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
               "vista_re": r"^gemini-(\d+(?:\.\d+)?)-flash(?:-latest)?$", "vista": ["gemini-flash-latest", "gemini-flash-lite-latest"], "testo": ["gemini-flash-latest", "gemini-flash-lite-latest"],
               "link": "https://aistudio.google.com/apikey", "costo": "gratis, con un tetto di richieste al minuto e al giorno",
               "dati": "con la chiave gratuita Google può usare i testi per migliorare i modelli"},
    "mistral": {"nome": "Mistral", "base": "https://api.mistral.ai/v1", "secret": ["MISTRAL_API_KEY"], "vista_cap": True, "pref_testo": [r"mistral-small-latest", r"mistral-medium-latest", r"mistral-large-latest"],
                "vista": ["mistral-medium-latest", "mistral-small-latest", "pixtral-large-latest"], "testo": ["mistral-small-latest", "mistral-medium-latest"],
                "link": "https://console.mistral.ai/api-keys", "costo": "ATTENZIONE: da novembre 2026 con il piano gratuito («Free») le chiavi non funzionano, serve un piano a pagamento (facoltativo)",
                "dati": "nel piano gratuito i dati possono servire ad addestrare i modelli"},
    "groq": {"nome": "Groq", "base": "https://api.groq.com/openai/v1", "secret": ["GROQ_API_KEY"],
             "pref_vista": [r"llama-4-scout", r"llama-4-maverick", r"qwen.*(vl|vision|3\.\d+-\d+b)", r"vision"], "pref_testo": [r"gpt-oss-120b", r"llama-4-maverick", r"llama-3\.3-70b", r"kimi-k2", r"qwen3", r"gpt-oss-20b", r"llama-3\.1-8b"],
             "vista": ["qwen/qwen3.8-27b", "meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-maverick-17b-128e-instruct"],
             "testo": ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"], "link": "https://console.groq.com/keys",
             "costo": "gratis, con tetti al minuto e al giorno", "dati": "i dati non servono ad addestrare (secondo le condizioni)"},
    "openrouter": {"nome": "OpenRouter (modelli :free)", "base": "https://openrouter.ai/api/v1", "secret": ["OPENROUTER_API_KEY"], "vista_openrouter": True,
                   "vista": ["openrouter/free"], "testo": ["deepseek/deepseek-chat-v3.1:free", "openrouter/free"], "link": "https://openrouter.ai/keys",
                   "costo": "gratis con i modelli «:free» (circa 50 richieste al giorno)", "dati": "dipende dal modello gratuito: alcuni possono usare i dati"},
    "nvidia": {"nome": "NVIDIA NIM", "base": "https://integrate.api.nvidia.com/v1", "secret": ["NVIDIA_API_KEY"],
               "pref_vista": [r"gemma-4-31b", r"nemotron.*omni", r"gemma-3-12b", r"llama-4-maverick", r"muse", r"vl", r"vision"], "pref_testo": [r"mistral-large", r"kimi-k\d", r"gemma-4-31b", r"nemotron-3\.5-lightning", r"minimax", r"llama-3\.3-70b", r"gpt-oss-120b"],
               "vista": ["meta/llama-4-maverick-17b-128e-instruct", "meta/llama-3.2-90b-vision-instruct", "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"],
               "testo": ["meta/llama-3.3-70b-instruct", "deepseek-ai/deepseek-v3.1"], "link": "https://build.nvidia.com/settings/api-keys",
               "costo": "gratis per prove (circa 40 richieste al minuto), serve il numero di telefono", "dati": "servizio per sviluppatori"},
    "cloudflare": {"nome": "Cloudflare Workers AI", "base": "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1", "secret": ["CLOUDFLARE_API_TOKEN"], "secret2": "CLOUDFLARE_ACCOUNT_ID",
                   "vista": ["@cf/meta/llama-4-scout-17b-16e-instruct", "@cf/meta/llama-3.2-11b-vision-instruct"], "testo": ["@cf/meta/llama-3.3-70b-instruct-fp8-fast"],
                   "link": "https://dash.cloudflare.com/profile/api-tokens", "costo": "gratis fino a 10.000 «neuroni» al giorno", "dati": "i dati non servono ad addestrare"},
    "cohere": {"nome": "Cohere", "base": "https://api.cohere.ai/compatibility/v1", "secret": ["COHERE_API_KEY"], "vista": ["command-a-vision-07-2025"], "testo": ["command-a-03-2025"],
               "link": "https://dashboard.cohere.com/api-keys", "costo": "chiave di prova gratuita: 1.000 richieste al mese, solo uso personale", "dati": "chiave di prova"},
    "sambanova": {"nome": "SambaNova Cloud", "base": "https://api.sambanova.ai/v1", "secret": ["SAMBANOVA_API_KEY"],
                  "pref_vista": [r"llama-4-maverick", r"vision", r"-vl"], "pref_testo": [r"deepseek-v3", r"llama-3\.3-70b", r"gpt-oss-120b", r"qwen3-32b", r"llama-4-maverick"],
                  "vista": ["Llama-4-Maverick-17B-128E-Instruct"], "testo": ["DeepSeek-V3.1", "Meta-Llama-3.3-70B-Instruct", "gpt-oss-120b"],
                  "link": "https://cloud.sambanova.ai/apis", "costo": "credito di prova gratuito (circa 5 dollari, vale circa 3 mesi), poi a pagamento: si ferma da solo quando finisce",
                  "dati": "servizio per sviluppatori"},
    "huggingface": {"nome": "Hugging Face", "base": "https://router.huggingface.co/v1", "secret": ["HF_TOKEN", "HUGGINGFACE_API_KEY"],
                    "pref_vista": [r"qwen.*vl", r"gemma-3-27b", r"llama-4", r"vision"], "pref_testo": [r"llama-3\.3-70b", r"qwen3", r"gpt-oss-120b", r"gemma-3-27b"],
                    "vista": ["Qwen/Qwen2.5-VL-7B-Instruct", "google/gemma-3-27b-it"], "testo": ["meta-llama/Llama-3.3-70B-Instruct", "openai/gpt-oss-120b"],
                    "link": "https://huggingface.co/settings/tokens", "costo": "gratis con un piccolo credito mensile (finisce in fretta): serve come riserva",
                    "dati": "le richieste passano a fornitori diversi secondo il modello"},
}
IL_ORDINE_VISTA = ["deepseek", "gemini", "mistral", "groq", "openrouter", "nvidia", "cloudflare", "cohere", "sambanova", "huggingface"]       # documenti e manoscritti: DeepSeek primo, poi i migliori
IL_ORDINE_TESTO = ["groq", "gemini", "mistral", "deepseek", "cloudflare", "nvidia", "openrouter", "cohere", "sambanova", "huggingface"]       # solo testo (arbitro, traduzioni): i più veloci prima


# ---------------------------------------------------------------------------------------------------------------------
# chiavi, pause dopo gli errori, scelta del modello
# ---------------------------------------------------------------------------------------------------------------------
def _il_secret(nome):
    if "_ad_secret" in globals():
        return _ad_secret(nome)
    try:
        return str(st.secrets.get(nome, "") or "").strip()
    except Exception:
        return ""


def il_chiave(prov):
    cfg = IL_FORNITORI[prov]
    k = next((v for v in (_il_secret(s) for s in cfg["secret"]) if v), "")
    if not k:
        return ""
    if cfg.get("secret2") and not _il_secret(cfg["secret2"]):
        return ""
    return k


def il_base(prov):
    cfg = IL_FORNITORI[prov]
    return cfg["base"].replace("{account}", _il_secret(cfg.get("secret2", "")) if cfg.get("secret2") else "")


@st.cache_resource
def _il_stato_globale():
    return {"pausa": {}, "modello": {}, "usi": {}}, _il_thr.Lock()


_IL_STATO, _IL_BLOCCO = _il_stato_globale()


def _il_in_pausa(prov):
    with _IL_BLOCCO:
        p = _IL_STATO["pausa"].get(prov)
    return bool(p and p[0] > _il_time.time() and p[1] == _il_hl.sha1(il_chiave(prov).encode()).hexdigest()[:8])


def _il_metti_pausa(prov, secondi, motivo):
    with _IL_BLOCCO:
        _IL_STATO["pausa"][prov] = (_il_time.time() + secondi, _il_hl.sha1(il_chiave(prov).encode()).hexdigest()[:8], motivo)


_IL_TL = _il_thr.local()                 # per il lavoro in sottofondo: scadenza del documento, servizio in uso, permessi di chi l'ha avviato


def _il_scaduto():
    sc = getattr(_IL_TL, "scadenza", None)
    return bool(sc and _il_time.time() >= sc)


def _il_tempo(t):
    """Attesa massima per una richiesta: mai oltre la scadenza del documento."""
    sc = getattr(_IL_TL, "scadenza", None)
    return t if not sc else max(5, min(t, sc - _il_time.time()))


def _il_segna(prov, modello):
    lav = getattr(_IL_TL, "lavoro", None)
    if lav is not None and getattr(_IL_TL, "doc_i", lav.get("i")) == lav.get("i"):     # un documento già abbandonato non scrive più
        lav["servizio"] = f"{IL_FORNITORI.get(prov, {}).get('nome', prov)} · {modello.split('/')[-1]}"
        lav["segnale"] = _il_time.time()


IL_RISERVATI = ("deepseek",)          # servizi A PAGAMENTO: li usa solo chi l'amministratore ha scelto (l'amministratore sempre)
IL_PERMESSI_FILE = "ia_permessi.json"


def il_permessi():
    """{prov: [uid, …]} — chi può usare i servizi a pagamento."""
    try:
        d = carica_dati(crea_archivio(), IL_PERMESSI_FILE) or {}
        return {k: [str(x) for x in (v or [])] for k, v in (d.get("riservati") or {}).items()}
    except Exception:
        return {}


def _il_permesso(prov):
    """Vero se la persona che sta usando l'app può usare questo servizio. Fuori da una sessione (lavori in sottofondo) i servizi a pagamento non si usano mai."""
    if prov not in IL_RISERVATI:
        return True
    perm = getattr(_IL_TL, "permessi", None)
    if perm is not None:
        return prov in perm
    try:
        s_ = st.session_state.get("sess") or {}
    except Exception:
        return False
    if not s_.get("uid"):
        return False
    if s_.get("admin"):
        return True
    return str(s_["uid"]) in il_permessi().get(prov, [])


def il_disponibili(ordine=None):
    """I servizi con la chiave, non in pausa e permessi a chi sta usando l'app, nell'ordine voluto."""
    if _il_os.environ.get("VM_IL_PROVA_LENTA"):
        return ["groq"]
    return [p for p in (ordine or IL_ORDINE_VISTA) if p in IL_FORNITORI and il_chiave(p) and not _il_in_pausa(p) and _il_permesso(p)]


@st.cache_data(ttl=600, show_spinner=False)
def _il_credito_deepseek(_impronta):
    """Credito rimasto su DeepSeek, es. «9.87 USD»; "" se non risponde."""
    try:
        r = _il_req.get("https://api.deepseek.com/user/balance", headers={"Authorization": "Bearer " + il_chiave("deepseek")}, timeout=10)
        info = (r.json().get("balance_infos") or [{}])[0]
        return f"{float(info.get('total_balance', 0)):.2f} {info.get('currency', 'USD')}" if r.status_code == 200 else ""
    except Exception:
        return ""


def _il_ui_permessi(prov):
    """Riquadro dell'amministratore: chi può usare il servizio a pagamento."""
    try:
        utenti = [(str(u["id"]), str(u["nome"])) for u in leggi_utenti() if u.get("attivo", True) and u.get("id") and u.get("nome")]
    except Exception:
        utenti = []
    nomi = dict(utenti)
    attuali = [u for u in il_permessi().get(prov, []) if u in nomi]
    st.markdown("**🔒 Chi può usarlo** (è a pagamento: tu sempre, gli altri solo se li scegli qui)")
    scelti = st.multiselect("Persone che possono usarlo", [u for u, _ in utenti], default=attuali,
                            format_func=lambda u: nomi.get(u, u), key=f"il_perm_{prov}", placeholder="Solo io")
    if sorted(scelti) != sorted(attuali):
        if st.button("💾 Salva chi può usarlo", key=f"il_perm_salva_{prov}", width="stretch", type="primary"):
            def _fn(d):
                d.setdefault("riservati", {})[prov] = list(scelti)
                return d
            salva_file(IL_PERMESSI_FILE, _fn, "Permessi IA")
            st.success("Salvato ✅")
            st.rerun()
    st.caption("Per tutti gli altri l'app usa solo i servizi gratuiti. Le traduzioni automatiche non usano mai i servizi a pagamento.")


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _il_elenco_modelli(prov, _impronta_chiave):
    """[{id, vista}] dal servizio; [] se non risponde."""
    try:
        r = _il_req.get(il_base(prov) + "/models", headers={"Authorization": f"Bearer {il_chiave(prov)}"}, timeout=12)
        if r.status_code != 200:
            return []
        dati = r.json()
        lista = dati.get("data") if isinstance(dati, dict) else dati
        out = []
        for m in lista or []:
            mid = str(m.get("id") or m.get("name") or "").replace("models/", "")
            if mid:
                cap = m.get("capabilities") or {}
                out.append({"id": mid, "vista": bool(cap.get("vision")) if isinstance(cap, dict) else False})
        return out
    except Exception:
        return []


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _il_openrouter_vista_gratis():
    try:
        r = _il_req.get("https://openrouter.ai/api/v1/models", timeout=10)
        out = []
        for m in r.json().get("data", []):
            prezzi = m.get("pricing") or {}
            gratis = all(str(prezzi.get(k, "0")) in ("0", "0.0", "0.00") for k in ("prompt", "completion"))
            if gratis and "image" in ((m.get("architecture") or {}).get("input_modalities") or []) and not str(m.get("id", "")).startswith("openrouter/"):
                out.append(m["id"])
        return out[:6]
    except Exception:
        return []


def il_modelli(prov, vista=True):
    """I modelli da provare, in ordine (il primo è quello buono; se dice «non esiste» si passa al successivo)."""
    cfg = IL_FORNITORI[prov]
    forzato = _il_secret(f"IA_MODELLO_{prov.upper()}" + ("" if vista else "_TESTO"))
    if forzato:
        return [forzato]
    base = list(cfg["vista"] if vista else cfg["testo"])
    elenco = _il_elenco_modelli(prov, _il_hl.sha1(il_chiave(prov).encode()).hexdigest()[:8])
    ids = [m["id"] for m in elenco]
    scelti = []
    if cfg.get("vista_re") and ids:
        cand = []
        for i in ids:
            m = _il_re.match(cfg["vista_re"], i)
            if m:
                try:
                    cand.append((float(m.group(1)), "latest" not in i, i))
                except ValueError:
                    pass
        scelti += [i for _v, _l, i in sorted(cand, reverse=True)][:2]
    if vista and cfg.get("vista_cap") and elenco:
        pref = [m["id"] for m in elenco if m["vista"] and _il_re.search(r"medium|small|large|pixtral", m["id"]) and "latest" in m["id"]]
        scelti += pref[:2]
    if vista and cfg.get("vista_openrouter"):
        scelti += _il_openrouter_vista_gratis()[:3]
    if ids:
        scelti += [m for m in base if m in ids]
        for rx in cfg.get("pref_vista" if vista else "pref_testo") or []:          # dall'elenco VERO del servizio (i nomi cambiano spesso)
            scelti += [i for i in ids if _il_re.search(rx, i, _il_re.I) and not _il_re.search(r"guard|whisper|tts|embed|orpheus|prompt", i, _il_re.I)][:1]
        if not any(m in ids for m in scelti):                                     # nessun nome conosciuto: scelgo io dall'elenco un modello per parlare
            no = r"embed|guard|safety|retriev|detector|calibration|starcoder|coder|reward|tts|whisper|rerank|pii|parse|ocr-|clip|diffusion|image-gen|video|audio"
            si = r"vl|vision|omni|gemma|llama-4|muse|pixtral" if vista else r"instruct|-it|chat|flash|pro|large|lightning|ultra|kimi|mistral|gemma|llama|qwen|minimax"
            scelti += [i for i in ids if _il_re.search(si, i, _il_re.I) and not _il_re.search(no, i, _il_re.I)][:3]
        scelti = [m for m in scelti if m in ids] + [m for m in scelti if m not in ids]   # prima quelli che esistono davvero
    scelti += base
    visti, out = set(), []
    for m in scelti:
        if m and m not in visti:
            visti.add(m)
            out.append(m)
    with _IL_BLOCCO:
        buono = _IL_STATO["modello"].get((prov, vista))
    if buono:
        if buono in out:
            out.remove(buono)
        out.insert(0, buono)                                              # quello che ha funzionato (o che il servizio ha suggerito) per primo
    return out[:5]


# ---------------------------------------------------------------------------------------------------------------------
# la chiamata (compatibile OpenAI)
# ---------------------------------------------------------------------------------------------------------------------
def il_chiama(prov, istruzioni, testo, immagini=(), max_tokens=2500, timeout=120, modelli_max=5):
    """(risposta, errore). immagini = elenco di JPEG (byte). errore: 'chiave', 'limite', 'modello', 'rete', 'servizio', ''."""
    key = il_chiave(prov)
    if not key:
        return "", "chiave"
    contenuto = [{"type": "text", "text": testo}] + [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + _il_b64.b64encode(im).decode()}} for im in immagini]
    messaggi = [{"role": "system", "content": istruzioni}, {"role": "user", "content": contenuto if immagini else testo}]
    ultimo = "modello"
    if prov == "gemini":                                                     # Gemini: il suo collegamento «nativo» (più affidabile del compatibile OpenAI)
        return _il_gemini(key, istruzioni, testo, immagini, max_tokens, timeout, modelli_max)
    for modello in il_modelli(prov, vista=bool(immagini))[:modelli_max]:
        if _il_scaduto():
            return "", "tempo"
        _il_segna(prov, modello)
        timeout = _il_tempo(timeout)
        corpo = {"model": modello, "messages": messaggi, "temperature": 0.1, "max_tokens": max(max_tokens, 400)}
        if prov == "gemini" or (prov == "groq" and "gpt-oss" in modello):
            corpo["reasoning_effort"] = "low"                                # i modelli «che pensano» rispondono subito
        try:
            r = _il_req.post(il_base(prov) + "/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                                                          "HTTP-Referer": "https://vitamemo.streamlit.app", "X-Title": "VitaMemo"},
                             json=corpo, timeout=timeout)
        except Exception:
            ultimo = "rete"
            continue
        if r.status_code == 200:
            try:
                j = r.json()
                risposta = (((j.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
                if isinstance(risposta, list):
                    risposta = "".join(x.get("text", "") for x in risposta if isinstance(x, dict))
            except Exception:
                ultimo = "servizio"
                continue
            if not risposta.strip():
                with _IL_BLOCCO:
                    _IL_STATO.setdefault("errori", {})[prov] = f"{modello}: risposta vuota"
            if risposta.strip():
                with _IL_BLOCCO:
                    _IL_STATO["modello"][(prov, bool(immagini))] = modello
                    oggi = _il_time.strftime("%Y-%m-%d")
                    _IL_STATO["usi"][(prov, oggi)] = _IL_STATO["usi"].get((prov, oggi), 0) + 1
                return risposta, ""
            ultimo = "servizio"
            continue
        if r.status_code in (401, 403):
            _il_metti_pausa(prov, 6 * 3600, "chiave non valida")
            return "", "chiave"
        if r.status_code == 429:
            _il_metti_pausa(prov, 20 * 60, "troppe richieste")
            return "", "limite"
        if r.status_code in (402,):
            _il_metti_pausa(prov, 6 * 3600, "credito finito")
            return "", "limite"
        ultimo = "modello" if r.status_code in (400, 404, 422) else "servizio"
        try:
            dett = f"{modello}: {r.status_code} {r.text[:220]}"
        except Exception:
            dett = f"{modello}: {r.status_code}"
        with _IL_BLOCCO:
            _IL_STATO.setdefault("errori", {})[prov] = dett
        if r.status_code == 400 and corpo.get("reasoning_effort"):          # il modello non accetta «reasoning_effort»: riprovo senza
            corpo.pop("reasoning_effort", None)
            try:
                r2 = _il_req.post(il_base(prov) + "/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=corpo, timeout=timeout)
                if r2.status_code == 200:
                    risposta = (((r2.json().get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
                    if str(risposta).strip():
                        with _IL_BLOCCO:
                            _IL_STATO["modello"][(prov, bool(immagini))] = modello
                        return str(risposta), ""
            except Exception:
                pass
    return "", ultimo


def _il_gemini(key, istruzioni, testo, immagini, max_tokens, timeout, modelli_max):
    if getattr(_il_gemini, "_dentro", False):
        return _il_gemini_una(key, istruzioni, testo, immagini, max_tokens, timeout, modelli_max)
    _il_gemini._dentro = True
    try:
        return _il_gemini_una(key, istruzioni, testo, immagini, max_tokens, timeout, modelli_max)
    finally:
        _il_gemini._dentro = False


def _il_gemini_una(key, istruzioni, testo, immagini, max_tokens, timeout, modelli_max):
    """Google Gemini con l'API generateContent. Pensiero ridotto al minimo (prima i modelli «pensavano» e non rispondevano in tempo)."""
    parti = [{"text": testo}] + [{"inline_data": {"mime_type": "image/jpeg", "data": _il_b64.b64encode(im).decode()}} for im in immagini]
    ultimo = "modello"
    for modello in il_modelli("gemini", vista=bool(immagini))[:modelli_max]:
        if _il_scaduto():
            return "", "tempo"
        _il_segna("gemini", modello)
        timeout = _il_tempo(timeout)
        pensiero = {"thinkingBudget": 0} if _il_re.search(r"2\.5-flash|flash-latest|flash-lite", modello) else {"thinkingLevel": "low"} if _il_re.search(r"gemini-3", modello) else None
        corpo = {"systemInstruction": {"parts": [{"text": istruzioni}]}, "contents": [{"role": "user", "parts": parti}],
                 "generationConfig": {"temperature": 0.1, "maxOutputTokens": max(max_tokens, 400)}}
        for tentativo in (0, 1):
            if pensiero and tentativo == 0:
                corpo["generationConfig"]["thinkingConfig"] = pensiero
            else:
                corpo["generationConfig"].pop("thinkingConfig", None)
            try:
                r = _il_req.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modello}:generateContent",
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=corpo, timeout=timeout)
            except Exception as e_:
                ultimo = "rete"
                with _IL_BLOCCO:
                    _IL_STATO.setdefault("errori", {})["gemini"] = f"{modello}: {type(e_).__name__} (nessuna risposta in {timeout} s)"
                break
            if r.status_code == 200:
                try:
                    cand = (r.json().get("candidates") or [{}])[0]
                    risposta = "".join(p.get("text", "") for p in ((cand.get("content") or {}).get("parts") or []) if not p.get("thought"))
                except Exception:
                    risposta = ""
                if risposta.strip():
                    with _IL_BLOCCO:
                        _IL_STATO["modello"][("gemini", bool(immagini))] = modello
                        oggi = _il_time.strftime("%Y-%m-%d")
                        _IL_STATO["usi"][("gemini", oggi)] = _IL_STATO["usi"].get(("gemini", oggi), 0) + 1
                    return risposta, ""
                with _IL_BLOCCO:
                    _IL_STATO.setdefault("errori", {})["gemini"] = f"{modello}: risposta vuota ({str(cand.get('finishReason', ''))})"
                ultimo = "servizio"
                break
            try:
                dett = f"{modello}: {r.status_code} {r.text[:220]}"
            except Exception:
                dett = f"{modello}: {r.status_code}"
            with _IL_BLOCCO:
                _IL_STATO.setdefault("errori", {})["gemini"] = dett
            if r.status_code in (401, 403):
                _il_metti_pausa("gemini", 6 * 3600, "chiave non valida")
                return "", "chiave"
            if r.status_code == 429:
                if _il_re.search(r"limit:\s*0|free_tier|FreeTier|free tier", getattr(r, "text", "") or "", _il_re.I):
                    ultimo = "limite"                                     # questo modello non è nel piano gratuito: provo il prossimo
                    break
                _il_metti_pausa("gemini", 20 * 60, "troppe richieste")
                return "", "limite"
            if r.status_code == 400 and tentativo == 0 and pensiero:
                continue                                                  # non accetta il «pensiero ridotto»: riprovo senza
            _sugg = [x for x in _il_re.findall(r"models/(gemini-[\w.\-]*\w)", r.text or "") if x != modello] if r.status_code == 404 else []
            m_sugg = _il_re.match(r"(.+)", _sugg[-1]) if _sugg else None          # il modello che Google consiglia (l'ultimo nominato)
            if m_sugg and m_sugg.group(1) != modello:                       # Google dice quale modello usare al suo posto: lo uso subito
                with _IL_BLOCCO:
                    _IL_STATO["modello"][("gemini", bool(immagini))] = m_sugg.group(1)
                return _il_gemini_una(key, istruzioni, testo, immagini, max_tokens, timeout, 1) if modelli_max > 1 else ("", "modello")
            ultimo = "modello" if r.status_code in (400, 404) else "servizio"
            break
    return "", ultimo


def il_json(testo):
    """Il primo oggetto JSON dentro la risposta (anche se c'è testo intorno o ```json)."""
    if not testo:
        return None
    t = _il_re.sub(r"```(?:json)?", "", testo)
    i = t.find("{")
    while i != -1:
        livello = 0
        for j in range(i, len(t)):
            if t[j] == "{":
                livello += 1
            elif t[j] == "}":
                livello -= 1
                if livello == 0:
                    try:
                        return _il_json.loads(t[i:j + 1])
                    except Exception:
                        break
        i = t.find("{", i + 1)
    return None


def il_testo(istruzioni, testo, max_tokens=2000, ordine=None):
    """Una domanda di solo testo al primo servizio libero. (risposta, servizio) oppure ('', '')."""
    for prov in il_disponibili(ordine or IL_ORDINE_TESTO):
        r, err = il_chiama(prov, istruzioni, testo, max_tokens=max_tokens, timeout=60)
        if r:
            return r, prov
    return "", ""


def _il_quad(cnt, cv2, np):
    peri = cv2.arcLength(cnt, True)
    ap = cv2.approxPolyDP(cnt, 0.02 * peri, True)
    return ap.reshape(4, 2).astype("float32") if len(ap) == 4 and cv2.isContourConvex(ap) else None


def il_migliora_foto(im):
    """FOTO MIGLIORI per la lettura: se si vede il foglio intero lo raddrizza e lo ritaglia (prospettiva), poi aumenta un po' il contrasto
    in modo uniforme (CLAHE). Se qualcosa non torna restituisce la foto com'era: non peggiora mai."""
    try:
        import cv2
        import numpy as np
        from PIL import Image
        a = np.array(im)
        h, w = a.shape[:2]
        if min(h, w) < 300:
            return im
        s_ = 900.0 / max(h, w)
        pic = cv2.resize(a, (int(w * s_), int(h * s_)), interpolation=cv2.INTER_AREA) if s_ < 1 else a.copy()
        g = cv2.GaussianBlur(cv2.cvtColor(pic, cv2.COLOR_RGB2GRAY), (5, 5), 0)
        bordi = cv2.dilate(cv2.Canny(g, 50, 150), np.ones((3, 3), np.uint8), iterations=2)
        cnts, _h = cv2.findContours(bordi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        area_tot = pic.shape[0] * pic.shape[1]
        quad = None
        for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
            if cv2.contourArea(c) < 0.25 * area_tot:
                break
            quad = _il_quad(c, cv2, np)
            if quad is not None:
                break
        if quad is not None and cv2.contourArea(quad) < 0.93 * area_tot:  # il foglio non riempie già tutta la foto: lo ritaglio
            quad = quad / (s_ if s_ < 1 else 1.0)
            somma, diff = quad.sum(1), np.diff(quad, axis=1).ravel()
            tl, br, tr, bl = quad[np.argmin(somma)], quad[np.argmax(somma)], quad[np.argmin(diff)], quad[np.argmax(diff)]
            W = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
            H = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
            if W > 200 and H > 200 and 0.2 < W / H < 5:
                M = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl], dtype="float32"), np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], dtype="float32"))
                a = cv2.warpPerspective(a, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        lab = cv2.cvtColor(a, cv2.COLOR_RGB2LAB)
        l_, a_, b_ = cv2.split(lab)
        l_ = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l_)
        return Image.fromarray(cv2.cvtColor(cv2.merge((l_, a_, b_)), cv2.COLOR_LAB2RGB))
    except Exception:
        return im


def il_avvisi_foto(dati, mime="", nome=""):
    """Controlla la foto PRIMA di leggerla: mossa/sfocata, troppo buia, troppo chiara (riflesso), troppo piccola. Ritorna i consigli (vuoto se va bene)."""
    if (mime or "").endswith("pdf") or str(nome).lower().endswith(".pdf"):
        return []
    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(_il_io.BytesIO(dati))).convert("L")
        a = np.array(im)
        h, w = a.shape[:2]
        avvisi = []
        if max(h, w) < 700:
            avvisi.append("📏 La foto è piccola: avvicinati al foglio o usa la qualità massima della fotocamera.")
        s_ = 1000.0 / max(h, w)
        g = cv2.resize(a, (max(1, int(w * s_)), max(1, int(h * s_)))) if s_ < 1 else a
        nitidezza = cv2.Laplacian(g, cv2.CV_64F).var()
        media = float(g.mean())
        chiari = float((g >= 254).mean())
        if nitidezza < 60:
            avvisi.append("🌫️ La foto sembra mossa o sfocata: tieni fermo il telefono, tocca lo schermo sul foglio per mettere a fuoco e rifalla.")
        if media < 70:
            avvisi.append("🌑 La foto è buia: accendi la luce o avvicinati a una finestra.")
        if chiari > 0.15:
            avvisi.append("☀️ C'è un riflesso o troppa luce: inclina un po' il foglio o spegni il flash.")
        return avvisi
    except Exception:
        return []


def il_immagini(nome, mime, dati, max_pagine=3, lato=1700):
    """Le pagine del documento come JPEG (foto o PDF)."""
    out = []
    try:
        if (mime or "").endswith("pdf") or str(nome).lower().endswith(".pdf"):
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            doc = fitz.open(stream=dati, filetype="pdf")
            for i, pag in enumerate(doc):
                if i >= max_pagine:
                    break
                zoom = min(3.0, lato / max(1.0, max(pag.rect.width, pag.rect.height)))
                pix = pag.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                try:
                    out.append(pix.tobytes("jpeg", jpg_quality=85))
                except Exception:
                    from PIL import Image
                    b = _il_io.BytesIO()
                    Image.open(_il_io.BytesIO(pix.tobytes("png"))).convert("RGB").save(b, "JPEG", quality=85)
                    out.append(b.getvalue())
        else:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(_il_io.BytesIO(dati))).convert("RGB")
            im = il_migliora_foto(im)                                     # foto migliori: raddrizzata, ritagliata, più leggibile
            im.thumbnail((lato, lato))
            b = _il_io.BytesIO()
            im.save(b, "JPEG", quality=86)
            out.append(b.getvalue())
    except Exception:
        return out
    return out


# ---------------------------------------------------------------------------------------------------------------------
# più letture + arbitro (manoscritti, foto incerte)
# ---------------------------------------------------------------------------------------------------------------------
_IL_ARBITRO = """Sei un arbitro molto attento. Ricevi 2 o 3 LETTURE INDIPENDENTI della STESSA immagine, fatte da servizi diversi, in JSON con lo stesso schema.
Il tuo compito: scrivere UNA lettura finale, la più vicina alla realtà e coerente con il TEMA del documento.
REGOLE
- Per ogni campo scegli il valore su cui le letture concordano. Se discordano, scegli quello più plausibile per il contesto (termini del settore, date possibili, nomi coerenti) e metti il campo in "da_verificare" con le alternative.
- Non inventare nulla che nessuna lettura riporta. Se nessuna lettura è affidabile lascia il campo vuoto.
- Nella "trascrizione" unisci le letture: le parole incerte segnale con [?], quelle illeggibili con [illeggibile].
- "limiti": elenca i limiti della lettura (scrittura poco chiara, sigle ambigue, date incerte, parti tagliate o sfocate…), in italiano semplice.
- "da_verificare": cose dedotte per intuizione o con letture diverse, da controllare sul documento originale.
- "accordo": "alto" se le letture coincidono quasi del tutto, "medio" se differiscono in qualche dettaglio, "basso" se differiscono molto.
Rispondi SOLO con un oggetto JSON con lo stesso schema delle letture, più "limiti" (lista), "da_verificare" (lista) e "accordo"."""


def il_consenso(letture, schema_txt="", ordine_testo=None):
    """letture = [(servizio, dict)]. Ritorna (dict finale, servizio arbitro). Senza arbitro: voto campo per campo."""
    validi = [(p, d) for p, d in letture if isinstance(d, dict)]
    if not validi:
        return None, ""
    if len(validi) == 1:
        d = dict(validi[0][1])
        d.setdefault("limiti", [])
        d.setdefault("da_verificare", [])
        d.setdefault("accordo", "una sola lettura")
        return d, ""
    corpo = "\n\n".join(f"LETTURA {i + 1} ({IL_FORNITORI.get(p, {}).get('nome', p)}):\n{_il_json.dumps(d, ensure_ascii=False)[:9000]}" for i, (p, d) in enumerate(validi))
    risp, arbitro = il_testo(_IL_ARBITRO + ("\n\nSCHEMA E REGOLE DEL DOCUMENTO:\n" + schema_txt if schema_txt else ""), corpo, max_tokens=3500, ordine=ordine_testo)
    fin = il_json(risp)
    if isinstance(fin, dict):
        return fin, arbitro
    # nessun arbitro libero: voto semplice
    fin, dubbi = {}, []
    chiavi = {k for _p, d in validi for k in d}
    for k in chiavi:
        valori = [d.get(k) for _p, d in validi if d.get(k) not in (None, "", [])]
        if not valori:
            fin[k] = ""
            continue
        conta = {}
        for v in valori:
            conta[_il_json.dumps(v, ensure_ascii=False, sort_keys=True).lower()] = conta.get(_il_json.dumps(v, ensure_ascii=False, sort_keys=True).lower(), 0) + 1
        migliore = max(valori, key=lambda v: conta[_il_json.dumps(v, ensure_ascii=False, sort_keys=True).lower()])
        fin[k] = migliore
        if len(conta) > 1 and k not in ("trascrizione", "riassunto", "confidenza"):
            dubbi.append(f"{k}: " + " / ".join(str(v)[:60] for v in valori))
    fin["limiti"] = ["Le letture dei servizi non coincidono del tutto: controlla i campi indicati."] if dubbi else []
    fin["da_verificare"] = dubbi
    fin["accordo"] = "medio" if dubbi else "alto"
    return fin, ""


def il_consenso_immagine(istruzioni, testo, immagini, quante=3, sempre=False, incerta=None, schema_txt=""):
    """Legge con il primo servizio; se la lettura è incerta (incerta(dict) → True) o sempre=True, chiede anche ad altri (fino a «quante»), poi l'arbitro.
    Ritorna {"risultato", "fonti", "arbitro", "errori"}."""
    letture, errori = [], {}
    for prov in il_disponibili(IL_ORDINE_VISTA):
        sc = getattr(_IL_TL, "scadenza", None)
        if sc and letture and sc - _il_time.time() < 35:
            break                                                          # poco tempo rimasto: tengo le letture che ho e lascio lavorare l'arbitro
        if _il_scaduto():
            break
        r, err = il_chiama(prov, istruzioni, testo, immagini)
        d = il_json(r)
        if isinstance(d, dict):
            letture.append((prov, d))
        else:
            errori[prov] = err or "formato"
        if letture and len(letture) >= quante:
            break
        if len(letture) == 1 and not sempre and not (incerta and incerta(letture[0][1])):
            break
    fin, arbitro = il_consenso(letture, schema_txt)
    return {"risultato": fin, "fonti": [p for p, _d in letture], "arbitro": arbitro, "errori": errori}


# ---------------------------------------------------------------------------------------------------------------------
# DOCUMENTI SANITARI: il modulo di classificazione
# ---------------------------------------------------------------------------------------------------------------------
def _il_tipi():
    return list(globals().get("_SP_TIPI_DOC") or ["Esame di laboratorio", "Diagnostica per immagini", "Referto di visita", "Ricetta medica", "Ricovero e dimissione",
                                                   "Certificato medico", "Vaccinazione", "Piano terapeutico", "Esenzione o invalidità", "Altro"])


def il_regole_sanitarie():
    aree = list(globals().get("CAT_AREE") or [])
    prest = list(globals().get("CAT_TIPI") or ["Visita specialistica", "Esame diagnostico", "Prestazione terapeutica", "Screening", "Controllo di follow-up", "Altro"])
    return f"""Sei un esperto di documentazione sanitaria italiana (referti, ricette, analisi, lettere di dimissione, certificati), anche SCRITTA A MANO dai medici.
Leggi le immagini del documento (una o più pagine) e compila la scheda. Scrivi in italiano.

CLASSIFICAZIONE — "tipo" è UNO di questi (scegli seguendo le regole, nell'ordine):
{_il_json.dumps(_il_tipi(), ensure_ascii=False)}
1. "Diagnostica per immagini": radiografia (RX), ecografia, ecocolordoppler, TAC, risonanza (RM), mammografia, MOC/densitometria, scintigrafia, PET, OCT, angiografia, ecocardiogramma — anche se il foglio si chiama «referto».
2. "Esame di laboratorio": analisi di sangue, urine, feci, tamponi, colture, esami istologici e citologici (pap test), con valori e intervalli di riferimento.
3. "Ricetta medica": ricetta rossa o bianca, ricetta dematerializzata o il suo PROMEMORIA (NRE, codice autenticazione), prescrizione di farmaci o di esami da prenotare.
4. "Piano terapeutico": SOLO il piano terapeutico formale (AIFA o regionale) di un farmaco, con centro prescrittore, posologia e durata. NON i preventivi del dentista e NON gli schemi di colliri dopo un intervento.
5. "Ricovero e dimissione": lettera di dimissione, verbale di pronto soccorso, cartella di ricovero, verbale operatorio o descrizione di un intervento chirurgico.
6. "Certificato medico": certificati (malattia, idoneità, gruppo sanguigno, sana e robusta costituzione…).
7. "Vaccinazione": certificati o libretti vaccinali, attestati di vaccinazione.
8. "Esenzione o invalidità": esenzioni ticket, verbali di invalidità, legge 104.
9. "Referto di visita": esito di una visita (specialistica o del medico di famiglia): anamnesi, esame obiettivo, diagnosi, terapia consigliata; comprese le INDICAZIONI SCRITTE A MANO dal medico,
   gli schemi di terapia dopo una visita o un intervento, i programmi di cure proposte (per esempio intervento di cataratta, laser), i piani di cura del dentista.
10. "Altro": solo se nessuna regola sopra va bene (per esempio fatture e ricevute).
"specialita" (area medica): scegli dall'elenco {_il_json.dumps(aree, ensure_ascii=False)} (scrivi il nome ESATTO); se nessuna va bene, scrivi la specialità in italiano.
"tipo_prestazione": uno di {_il_json.dumps(prest, ensure_ascii=False)}.
"esame": il nome dell'esame o della visita principale (es. «Mammografia bilaterale», «Visita oculistica», «Emocromo»), mai il nome dell'ospedale o della Regione.
"esami_elenco": per le analisi, i nomi degli esami contenuti (es. ["Emocromo", "Glicemia"]).

DATE (formato AAAA-MM-GG, vuoto se non c'è):
- "data" = il giorno in cui è stata fatta la visita o l'esame (prelievo, esecuzione); "data_referto" = il giorno in cui è stato scritto il referto, se diverso.
- "prossimo_controllo" = SOLO se è scritta una data precisa di controllo; se è scritto «controllo tra 6 mesi» mettilo in "controllo_indicato" e lascia vuota la data.
- Per le ricette: "codice_ricetta" (NRE) e "valida_fino" se scritti.

PERSONE E LUOGHI: "paziente" (nome e cognome come scritti), "codice_fiscale" (se si legge), "medico" (solo il nome del medico, con Dott./Dott.ssa), "struttura" (ospedale, studio, laboratorio).
"conclusioni": l'esito o la diagnosi, copiati quasi alla lettera (massimo 400 caratteri), senza intestazioni di tabelle.

SCRITTO A MANO: "manoscritto": true se il testo importante è scritto a mano. Leggi con attenzione le grafie mediche, le abbreviazioni (OD occhio destro, OS occhio sinistro, cp compresse,
gtt gocce, die al giorno, bid due volte al giorno, FACO facoemulsificazione, IOL lente intraoculare…) e sciogli le abbreviazioni solo nella "trascrizione_chiara".
"trascrizione": il testo come scritto (parole incerte con [?], illeggibili con [illeggibile]). "trascrizione_chiara": lo stesso contenuto riscritto in italiano chiaro e completo.
"leggibilita": "alta" | "media" | "bassa". "confidenza": {{"tipo": 0-1, "data": 0-1, "esame": 0-1}}.
"riassunto": 2-3 frasi semplici su cosa dice il documento. "parole_incerte": elenco delle parole di cui non sei sicuro.
NON INVENTARE: se un dato non c'è o non si legge, lascia la stringa vuota.
Rispondi SOLO con un oggetto JSON con queste chiavi:
manoscritto, leggibilita, tipo, specialita, tipo_prestazione, esame, esami_elenco, data, data_referto, struttura, medico, paziente, codice_fiscale, codice_ricetta, valida_fino,
conclusioni, controllo_indicato, prossimo_controllo, trascrizione, trascrizione_chiara, riassunto, parole_incerte, confidenza"""


def _il_incerta(d):
    try:
        conf = float((d.get("confidenza") or {}).get("tipo", 1))
    except Exception:
        conf = 1.0
    return bool(d.get("manoscritto")) or str(d.get("leggibilita", "")).lower() in ("media", "bassa") or conf < 0.65


def _il_data_ok(x):
    x = str(x or "").strip()
    return x if _il_re.fullmatch(r"\d{4}-\d{2}-\d{2}", x) else ""


def _il_scegli(valore, ammessi):
    """Il valore ammesso più vicino (senza maiuscole/accenti); '' se nessuno."""
    import unicodedata
    n = lambda s: unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower().strip()
    v = n(valore)
    if not v:
        return ""
    for a in ammessi:
        if n(a) == v:
            return a
    for a in ammessi:
        if v in n(a) or n(a) in v:
            return a
    return ""


def il_leggi_sanitario(nome, mime, dati, f=None):
    """Legge e classifica un documento sanitario con l'IA. Ritorna None (nessun servizio) oppure
    {"campi": {campo: {"valore","affidabilita","fonte"}}, "fonti", "arbitro", "manoscritto", "limiti", "da_verificare", "riassunto", "trascrizione", "errori"}."""
    if not il_disponibili(IL_ORDINE_VISTA):
        return None
    immagini = il_immagini(nome, mime, dati)
    if not immagini:
        return None
    regole = il_regole_sanitarie()
    esito = il_consenso_immagine(regole, f"Documento: {nome}. Leggilo e compila la scheda.", immagini, quante=3, incerta=_il_incerta, schema_txt=regole)
    d = esito["risultato"]
    if not isinstance(d, dict):
        return {"campi": {}, "fonti": [], "arbitro": "", "manoscritto": False, "limiti": [], "da_verificare": [], "riassunto": "", "trascrizione": "", "errori": esito["errori"]}
    fonti = " + ".join(IL_FORNITORI[p]["nome"] for p in esito["fonti"])
    accordo = str(d.get("accordo", "")).lower()
    try:
        conf = d.get("confidenza") or {}
    except Exception:
        conf = {}

    def aff(k):
        try:
            c = float(conf.get(k)) if isinstance(conf, dict) and conf.get(k) is not None else None
        except Exception:
            c = None
        if accordo == "basso" or str(d.get("leggibilita", "")).lower() == "bassa":
            return "bassa"
        if c is not None:
            return "alta" if c >= 0.8 else "media" if c >= 0.55 else "bassa"
        return "alta" if accordo in ("alto", "una sola lettura") and len(esito["fonti"]) >= 2 else "media"
    campi = {}

    def metti(k, v):
        if v not in (None, "", []):
            campi[k] = {"valore": v, "affidabilita": aff(k), "fonte": "IA: " + fonti}
    metti("tipo", _il_scegli(d.get("tipo"), _il_tipi()) or "Altro")
    aree = list(globals().get("CAT_AREE") or [])
    metti("specialita", _il_scegli(d.get("specialita"), aree) or str(d.get("specialita") or "").strip())
    metti("tipo_prestazione", _il_scegli(d.get("tipo_prestazione"), list(globals().get("CAT_TIPI") or [])))
    metti("esame", str(d.get("esame") or "").strip()[:120])
    el = d.get("esami_elenco")
    metti("esami_elenco", ", ".join(str(x) for x in el) if isinstance(el, list) else str(el or "").strip())
    for k in ("data", "data_referto", "prossimo_controllo", "valida_fino"):
        metti(k, _il_data_ok(d.get(k)))
    for k, k2 in (("struttura", "struttura"), ("medico", "medico"), ("conclusioni", "conclusioni"), ("controllo_indicato", "controllo_indicato"), ("codice", "codice_ricetta")):
        metti(k, str(d.get(k2) or "").strip()[:400])
    if f is not None and "sp_proponi_profilo" in globals():
        try:
            pid, motivo = sp_proponi_profilo(f, str(d.get("paziente") or ""), str(d.get("codice_fiscale") or "").upper().replace(" ", ""))
            if pid:
                campi["profilo"] = {"valore": pid, "affidabilita": "alta" if motivo == "codice fiscale" else "media", "fonte": "IA: " + motivo}
        except Exception:
            pass
    lim = d.get("limiti") or []
    ver = d.get("da_verificare") or []
    return {"campi": campi, "fonti": esito["fonti"], "arbitro": esito["arbitro"], "manoscritto": bool(d.get("manoscritto")),
            "limiti": [str(x) for x in (lim if isinstance(lim, list) else [lim]) if x], "da_verificare": [str(x) for x in (ver if isinstance(ver, list) else [ver]) if x],
            "riassunto": str(d.get("riassunto") or ""), "trascrizione": str(d.get("trascrizione_chiara") or d.get("trascrizione") or ""), "errori": esito["errori"],
            "parole_incerte": [str(x) for x in (d.get("parole_incerte") or []) if x] if isinstance(d.get("parole_incerte"), list) else []}


def il_unisci(locale, ia):
    """La lettura dell'IA ha la precedenza; quello che l'IA non ha trovato resta dalla lettura locale."""
    out = dict(locale or {})
    for k, v in ((ia or {}).get("campi") or {}).items():
        out[k] = v
    if ia:
        out["_ia"] = {"valore": {k: ia.get(k) for k in ("fonti", "arbitro", "manoscritto", "limiti", "da_verificare", "riassunto", "trascrizione", "parole_incerte")}}
    return out


def il_mostra_lettura(riconosciuto):
    """Il riquadro «chi ha letto il documento, limiti, cosa verificare»."""
    ia = ((riconosciuto or {}).get("_ia") or {}).get("valore")
    if not ia:
        return
    import html as _h
    fonti = " + ".join(IL_FORNITORI.get(p, {}).get("nome", p) for p in ia.get("fonti") or [])
    righe = [f"🤖 <b>Letto da:</b> {_h.escape(fonti)}" + (f" · <b>confronto finale:</b> {_h.escape(IL_FORNITORI.get(ia['arbitro'], {}).get('nome', ia['arbitro']))}" if ia.get("arbitro") else "")]
    if ia.get("manoscritto"):
        righe.append("✍️ <b>Documento scritto a mano</b>: l'ho fatto leggere a più servizi e ho confrontato le letture.")
    if ia.get("riassunto"):
        righe.append("📝 " + _h.escape(ia["riassunto"]))
    if ia.get("limiti"):
        righe.append("⚠️ <b>Limiti della lettura:</b> " + _h.escape("; ".join(ia["limiti"][:6])))
    if ia.get("da_verificare"):
        righe.append("🔍 <b>Da verificare sul foglio:</b> " + _h.escape("; ".join(ia["da_verificare"][:6])))
    st.markdown("<div style='border:1px solid rgba(120,200,255,.45);border-radius:14px;padding:10px 12px;margin:6px 0;background:rgba(20,60,110,.25);line-height:1.45'>"
                + "<br>".join(righe) + "</div>", unsafe_allow_html=True)
    if ia.get("trascrizione"):
        with st.expander("📄 Testo letto (trascrizione)"):
            st.text(ia["trascrizione"][:6000])


# ---------------------------------------------------------------------------------------------------------------------
# riclassificare i documenti già archiviati con l'IA
# ---------------------------------------------------------------------------------------------------------------------
_IL_CAMPI_RICLASSIFICA = ["tipo", "specialita", "tipo_prestazione", "esame", "esami_elenco", "data", "data_referto", "medico", "struttura", "conclusioni", "controllo_indicato", "prossimo_controllo"]


def il_cambiamenti(doc, campi):
    """{campo: (vecchio, nuovo)}. Non tocca i campi che la persona ha corretto a mano (diversi da quello che l'app aveva letto la prima volta)."""
    letto_prima = doc.get("riconosciuto") or {}
    c = {}
    for k in _IL_CAMPI_RICLASSIFICA:
        nuovo = (campi.get(k) or {}).get("valore")
        if nuovo in (None, ""):
            continue
        att = doc.get(k) or ""
        if att and letto_prima and k in letto_prima and str(letto_prima.get(k) or "") != str(att):
            continue                                              # l'ha scritto la persona: non si tocca
        if str(att).strip().lower() != str(nuovo).strip().lower():
            if (campi.get(k) or {}).get("affidabilita") == "bassa" and att:
                continue                                          # lettura poco sicura: non cambio un valore che c'è già
            c[k] = (att, nuovo)
    return c


def _il_fase(testo):
    lav = getattr(_IL_TL, "lavoro", None)
    if lav is not None and getattr(_IL_TL, "doc_i", lav.get("i")) == lav.get("i"):
        lav["servizio"], lav["segnale"] = testo, _il_time.time()


def _il_uno_doc(d, f, files, titolo):
    """Legge e classifica UN documento → voce delle proposte."""
    refs = files(d) if files else [d["file"]]
    if _il_os.environ.get("VM_IL_PROVA_LENTA"):                              # solo per le prove automatiche: lettura finta e lenta
        lenta = float(_il_os.environ["VM_IL_PROVA_LENTA"])
        if str(d.get("titolo", "")).startswith("BLOCCA"):
            lenta = 10 ** 6                                                  # documento che non finisce mai: deve intervenire il controllo
        t0 = _il_time.time()
        while _il_time.time() - t0 < lenta:
            _il_segna("groq", "prova-lenta")
            _il_time.sleep(0.2)
        ia_f = {"campi": {"profilo": {"valore": _il_os.environ["VM_IL_PAZIENTE"]}}} if _il_os.environ.get("VM_IL_PAZIENTE") else {"campi": {}}
        return {"id": d.get("id"), "titolo": titolo, "cambi": {"tipo": (d.get("tipo"), "Esame di laboratorio")} | _il_cambio_persona(d, f, ia_f), "ia": ia_f, "errore": ""}
    _il_fase("apro il file…")
    try:
        nome, mime, dati = _fa_inv_allegati(refs[:1])[0]
    except Exception:
        return {"id": d.get("id"), "titolo": titolo, "cambi": {}, "errore": "file non leggibile"}
    _il_fase("preparo le pagine del documento…")
    try:
        ia = il_leggi_sanitario(nome, mime, dati, f)
    except Exception as e_:
        ia = {"errore_interno": f"{type(e_).__name__}"}
    if not ia or not ia.get("campi"):
        errore = "troppo lento, saltato" if _il_scaduto() else "nessun servizio ha risposto" if ia is None else "lettura non riuscita"
        return {"id": d.get("id"), "titolo": titolo, "cambi": {}, "errore": errore, "ia": ia}
    return {"id": d.get("id"), "titolo": titolo, "cambi": il_cambiamenti(d, ia["campi"]) | _il_cambio_persona(d, f, ia), "ia": ia, "errore": ""}


def _il_cambio_persona(d, f, ia):
    """Il referto è di un'altra persona della famiglia (paziente o codice fiscale letti)? → {"profilo": (chi ora, chi è)}; l'id va in ia["sposta_a"]."""
    try:
        prof = (f or {}).get("profili") or []
        ora_ = next((p for p in prof if any(x.get("id") == d.get("id") for x in (p.get("docsan") or []))), None)
        nuovo = ((ia.get("campi") or {}).get("profilo") or {}).get("valore")
        dopo = next((p for p in prof if p.get("id") == nuovo), None)
        if ora_ and dopo and dopo["id"] != ora_["id"]:
            ia["sposta_a"] = dopo["id"]
            return {"profilo": (ora_.get("nome", "?"), dopo.get("nome", "?"))}
    except Exception:
        pass
    return {}


def _il_con_controllo(fn, secondi):
    """Esegue fn() in un filo a parte e non aspetta più di «secondi»: se si blocca (rete, file, servizio) si va avanti lo stesso. (finito, risultato)."""
    lav_ = getattr(_IL_TL, "lavoro", None)
    ris, tl = {}, (lav_, getattr(_IL_TL, "permessi", None), getattr(_IL_TL, "scadenza", None), (lav_ or {}).get("i"))

    def _corri():
        _IL_TL.lavoro, _IL_TL.permessi, _IL_TL.scadenza, _IL_TL.doc_i = tl
        try:
            ris["v"] = fn()
        except Exception as e_:
            ris["e"] = e_

    t_ = _il_thr.Thread(target=_corri, daemon=True)
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
        add_script_run_ctx(t_, get_script_run_ctx())
    except Exception:
        pass
    t_.start()
    t_.join(secondi)
    return (not t_.is_alive() and "v" in ris), ris.get("v")


def il_da_controllare(p, tutti=False):
    """I documenti con file che l'IA non ha ancora controllato (o tutti)."""
    files = globals().get("_stt_files")
    return [d for d in (p.get("docsan") or []) if (files(d) if files else d.get("file")) and (tutti or not (d.get("lettura_ia") or d.get("proposta_ia")))]


def _il_riassunto_ia(ia):
    ia = ia or {}
    return {"fonti": ia.get("fonti"), "manoscritto": ia.get("manoscritto"), "limiti": ia.get("limiti"), "da_verificare": ia.get("da_verificare"), "riassunto": ia.get("riassunto"),
            **({"sposta_a": ia["sposta_a"]} if ia.get("sposta_a") else {})}


def _il_salva_esito(percorso, pid, voce):
    """Subito dopo aver letto un documento: lo segno nei dati. Senza cambi → «controllato»; con cambi → «proposta da confermare». Così il conto scende
    a ogni documento e niente si perde se l'app si riavvia."""
    if voce.get("errore") or not percorso:
        return
    ora = _il_time.strftime("%Y-%m-%dT%H:%M:%S")

    def _m(d):
        for pr in (d.get("farmacia") or {}).get("profili") or []:
            if pr.get("id") != pid:
                continue
            for d_ in pr.get("docsan") or []:
                if d_.get("id") != voce["id"]:
                    continue
                if voce.get("cambi"):
                    d_["proposta_ia"] = {"cambi": {k: list(v) for k, v in voce["cambi"].items()}, "ia": _il_riassunto_ia(voce.get("ia")), "il": ora}
                else:
                    d_.pop("proposta_ia", None)
                    d_["lettura_ia"] = dict(_il_riassunto_ia(voce.get("ia")), il=ora, nessun_cambio=True)
    try:
        crea_archivio().modifica(percorso, _m, "Salute: documento controllato con l'IA")   # in sottofondo: niente «Salvo…» a schermo
    except Exception as e_:
        lav = getattr(_IL_TL, "lavoro", None)
        if lav is not None:
            lav["errore_salva"] = f"{type(e_).__name__}: {e_}"[:160]
    try:
        carica_dati.clear()
    except Exception:
        pass


def il_proposte_riclassifica(f, pid, progress=None, massimo=60, tutti=False):
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {})
    files = globals().get("_stt_files")
    docs = il_da_controllare(p, tutti)[:massimo]
    out = []
    lav = getattr(_IL_TL, "lavoro", None)
    for i, d in enumerate(docs):
        titolo = d.get("titolo") or (sp_titolo_doc(d) if "sp_titolo_doc" in globals() else d.get("tipo", "Documento"))
        if progress:
            progress(i / max(1, len(docs)), f"Leggo con l'IA {i + 1} di {len(docs)}: {titolo}"[:90])
        if lav is None:
            out.append(_il_uno_doc(d, f, files, titolo))
            continue
        if lav.get("stop"):
            break
        lav.update(i=i, n=len(docs), inizio_doc=_il_time.time(), servizio="", segnale=_il_time.time(), out=list(out), titolo=titolo)
        _IL_TL.scadenza = _il_time.time() + IL_MAX_DOC
        finito, voce = _il_con_controllo(lambda d=d, titolo=titolo: _il_uno_doc(d, f, files, titolo), IL_MAX_DOC + 15)
        out.append(voce if finito and voce else {"id": d.get("id"), "titolo": titolo, "cambi": {}, "errore": "troppo lento, saltato"})
        _il_salva_esito(lav.get("percorso"), pid, out[-1])
    _IL_TL.scadenza = None
    if lav is not None:
        lav["out"] = list(out)
    if progress:
        progress(1.0, "Fatto")
    return out


def il_applica_riclassifica(pid, proposte, scelti):
    """Applica i cambi scelti e segna come «controllati dall'IA» tutti i documenti letti bene (anche quelli senza cambi o non scelti), così non si rileggono più."""
    mappa = {x["id"]: x for x in proposte if x.get("cambi") and x["id"] in scelti}
    letti = {x["id"] for x in proposte if not x.get("errore")}
    if not mappa and not letti:
        return 0

    def _fn(f):
        for pr in f.get("profili") or []:
            if pr.get("id") != pid:
                continue
            for d_ in pr.get("docsan") or []:
                x = mappa.get(d_.get("id"))
                if not x:
                    if d_.get("id") in letti and not d_.get("lettura_ia"):
                        d_["lettura_ia"] = {"il": _il_time.strftime("%Y-%m-%dT%H:%M:%S"), "nessun_cambio": True}
                    continue
                vecchio_auto = sp_titolo_doc(d_) if "sp_titolo_doc" in globals() else ""
                titolo_auto = not d_.get("titolo") or d_.get("titolo") == vecchio_auto
                for k, (_a, b) in x["cambi"].items():
                    d_[k] = b
                    d_.setdefault("riconosciuto", {})[k] = b
                ia = x.get("ia") or {}
                d_["lettura_ia"] = {"fonti": ia.get("fonti"), "manoscritto": ia.get("manoscritto"), "limiti": ia.get("limiti"), "da_verificare": ia.get("da_verificare"),
                                    "riassunto": ia.get("riassunto"), "il": _il_time.strftime("%Y-%m-%dT%H:%M:%S")}
                if titolo_auto and "sp_titolo_doc" in globals():
                    d_["titolo"] = sp_titolo_doc(d_)
    _fa_salva(_fn, "Salute: documenti riclassificati con l'IA")
    return len(mappa)


def il_conferma_proposte(pid, scelti, tutte):
    """Proposte salvate nei dati: applica quelle scelte, le altre restano come erano; tutte diventano «controllate»."""
    scelti, tutte = set(scelti), set(tutte)

    def _fn(f):
        da_spostare = []
        for pr in f.get("profili") or []:
            if pr.get("id") != pid:
                continue
            for d_ in pr.get("docsan") or []:
                pr_ = d_.get("proposta_ia")
                if not pr_ or d_.get("id") not in tutte:
                    continue
                ora = _il_time.strftime("%Y-%m-%dT%H:%M:%S")
                if d_.get("id") in scelti:
                    vecchio_auto = sp_titolo_doc(d_) if "sp_titolo_doc" in globals() else ""
                    titolo_auto = not d_.get("titolo") or d_.get("titolo") == vecchio_auto
                    if "profilo" in (pr_.get("cambi") or {}) and (pr_.get("ia") or {}).get("sposta_a"):
                        da_spostare.append((d_, pr_["ia"]["sposta_a"]))      # va nei documenti sanitari dell'altra persona
                    for k, v in (pr_.get("cambi") or {}).items():
                        if k == "profilo":
                            continue
                        b = v[1] if isinstance(v, (list, tuple)) and len(v) == 2 else v
                        d_[k] = b
                        d_.setdefault("riconosciuto", {})[k] = b
                    if titolo_auto and "sp_titolo_doc" in globals():
                        d_["titolo"] = sp_titolo_doc(d_)
                    d_["lettura_ia"] = dict(pr_.get("ia") or {}, il=ora)
                else:
                    d_["lettura_ia"] = dict(pr_.get("ia") or {}, il=ora, rifiutata=True)
                d_.pop("proposta_ia", None)
        for d_, verso in da_spostare:
            dest = next((p for p in f.get("profili") or [] if p.get("id") == verso), None)
            orig = next((p for p in f.get("profili") or [] if p.get("id") == pid), None)
            if dest is not None and orig is not None and dest is not orig:
                orig["docsan"] = [x for x in orig.get("docsan") or [] if x is not d_]
                dest.setdefault("docsan", []).append(d_)
    _fa_salva(_fn, "Salute: proposte dell'IA confermate")
    return len(scelti)


_IL_ETICHETTE = {"profilo": "👤 Di chi è (va nei suoi documenti sanitari)", "tipo": "Tipo", "specialita": "Area medica", "tipo_prestazione": "Prestazione", "esame": "Esame o visita", "esami_elenco": "Esami contenuti", "data": "Data",
                 "data_referto": "Data del referto", "medico": "Medico", "struttura": "Struttura", "conclusioni": "Conclusioni", "controllo_indicato": "Controllo indicato",
                 "prossimo_controllo": "Prossimo controllo"}


IL_MAX_DOC = int(_il_os.environ.get("VM_IL_MAX_DOC", "110"))                        # secondi al massimo per un documento (poi passa al successivo)
@st.cache_resource
def _il_lavori_globali():
    return {}


_IL_LAVORI = _il_lavori_globali()          # i lavori restano anche se la pagina si ricarica o il telefono si riconnette


def _il_chi():
    try:
        return str((st.session_state.get("sess") or {}).get("uid") or "anonimo")
    except Exception:
        return "anonimo"


def _il_avvia_lavoro(f, pid, tutti=False):
    """Fa partire la lettura in sottofondo: continua anche se il telefono passa ad altre app o lo schermo si spegne."""
    k = (_il_chi(), pid)
    perm = {p for p in IL_FORNITORI if _il_permesso(p)}
    lav = {"percorso": st.session_state.get("percorso"), "stato": "corre", "i": 0, "n": 0, "inizio": _il_time.time(), "inizio_doc": _il_time.time(), "segnale": _il_time.time(), "servizio": "", "out": [], "stop": False}
    with _IL_BLOCCO:
        for kk in [kk for kk, v in _IL_LAVORI.items() if v.get("stato") != "corre" and _il_time.time() - v.get("fine", 0) > 6 * 3600]:
            _IL_LAVORI.pop(kk, None)                                       # pulizia dei lavori vecchi
        _IL_LAVORI[k] = lav

    def _corri():
        _IL_TL.lavoro, _IL_TL.permessi, _IL_TL.scadenza = lav, perm, None
        try:
            lav["out"] = il_proposte_riclassifica(f, pid, tutti=tutti)
            lav["stato"] = "fermato" if lav.get("stop") else "fatto"
        except Exception as e_:
            lav["stato"], lav["errore"] = "errore", f"{type(e_).__name__}: {e_}"[:200]
        finally:
            lav["fine"] = _il_time.time()
            _IL_TL.lavoro = _IL_TL.permessi = _IL_TL.scadenza = None

    t_ = _il_thr.Thread(target=_corri, daemon=True, name=f"il_riclassifica_{pid}")
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
        add_script_run_ctx(t_, get_script_run_ctx())
    except Exception:
        pass
    t_.start()


def _il_lavoro(pid):
    return _IL_LAVORI.get((_il_chi(), pid))


def _il_mostra_avanzamento(pid):
    """Riquadro che si aggiorna da solo ogni 2 secondi mentre l'IA legge."""
    @st.fragment(run_every=2)
    def _vivo():
        lav = _il_lavoro(pid)
        if not lav:
            return
        ora = _il_time.time()
        if lav["stato"] == "corre" and ora - lav.get("segnale", ora) > IL_MAX_DOC + 90:   # il lavoro non dà più segni (es. il server è ripartito)
            lav.update(stato="errore", errore="la lettura non rispondeva più", fine=ora)
        if lav["stato"] != "corre":
            st.rerun()                                                     # finito: mostro le proposte
        i, n = lav.get("i", 0), max(1, lav.get("n", 0) or 1)
        su_doc = int(ora - lav.get("inizio_doc", ora))
        totale = int(ora - lav.get("inizio", ora))
        fatti = lav.get("out") or []
        media = (totale - su_doc) / i if i else 60
        resto = max(0, int(media * (n - i) - su_doc))
        punti = "●" * (1 + totale % 4) + "○" * (3 - totale % 4)
        st.markdown(f"<div style='border:1px solid #38bdf8;border-radius:14px;padding:10px 12px;margin:6px 0'>"
                    f"<b>🤖 Lettura in corso {punti}</b><br>"
                    f"📄 Documento <b>{min(i + 1, n)} di {n}</b>" + (f": {_il_html.escape(str(lav.get('titolo', ''))[:70])}" if lav.get("titolo") else "") + "<br>"
                    f"⏱️ Su questo documento da <b>{su_doc} s</b> (al massimo {IL_MAX_DOC} s, poi passo al prossimo)<br>"
                    f"🔄 Sto chiedendo a: <b>{lav.get('servizio') or 'preparo il documento…'}</b><br>"
                    f"✅ Letti finora: <b>{len(fatti)}</b> · da cambiare: <b>{sum(1 for x in fatti if x.get('cambi'))}</b><br>"
                    f"⌛ Tempo passato: {totale // 60} min {totale % 60} s · manca circa: <b>{resto // 60} min</b></div>", unsafe_allow_html=True)
        st.progress(min(1.0, (i + min(0.95, su_doc / IL_MAX_DOC)) / n))
        st.caption("📱 Puoi usare altre app o spegnere lo schermo: la lettura continua da sola. Quando torni qui trovi il punto a cui è arrivata o le proposte pronte.")
        if st.button("⏹ Ferma la lettura (tengo quelli già letti)", key=f"il_stop_{pid}", width="stretch"):
            lav["stop"] = True
            st.toast("Mi fermo dopo il documento che sto leggendo")
    _vivo()


def _il_blocco_proposte(pid, pendenti):
    st.markdown(f"<div style='font-weight:700;font-size:1.05rem;margin:8px 0 4px'>🟡 Proposte dell'IA da confermare: {len(pendenti)}</div>", unsafe_allow_html=True)
    scelti = []
    for d in pendenti:
        pr_ = d["proposta_ia"]
        titolo = d.get("titolo") or (sp_titolo_doc(d) if "sp_titolo_doc" in globals() else d.get("tipo", "Documento"))
        st.markdown(f"**📄 {titolo}**")
        for k, v in (pr_.get("cambi") or {}).items():
            a, b = (v[0], v[1]) if isinstance(v, (list, tuple)) and len(v) == 2 else ("", v)
            st.markdown(f"<div style='font-size:.88rem;margin-left:8px'>{_IL_ETICHETTE.get(k, k)}: <s>{_il_html.escape(str(a or '—'))}</s> → <b>{_il_html.escape(str(b))}</b></div>",
                        unsafe_allow_html=True)
        ia = pr_.get("ia") or {}
        if ia.get("limiti") or ia.get("da_verificare"):
            st.caption("⚠️ " + "; ".join([str(x) for x in (ia.get("limiti") or [])[:2] + (ia.get("da_verificare") or [])[:2]]))
        if st.checkbox("Applica a questo documento", value=True, key=f"il_sc_{pid}_{d['id']}"):
            scelti.append(d["id"])
    c1, c2 = st.columns(2, gap="small")
    ids = [d["id"] for d in pendenti]
    if c1.button(f"✅ Applica ({len(scelti)})", key=f"il_app_{pid}", type="primary", width="stretch", disabled=not scelti):
        n_ = il_conferma_proposte(pid, scelti, ids)
        st.toast(f"Riclassificati {n_} documenti")
        st.rerun()
    if c2.button("✖ Non applicare", key=f"il_no_{pid}", width="stretch"):
        il_conferma_proposte(pid, [], ids)
        st.rerun()


def il_pannello_riclassifica(pid):
    """Dentro Documenti sanitari: prova e riclassificazione con l'IA.
    La lettura in corso e le proposte da confermare stanno FUORI dalla tendina, sempre in vista: così non si chiude nulla mentre l'IA lavora."""
    f = _fa_dati()
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {})
    n = len(il_da_controllare(p, True))
    if not n:
        return
    resta = len(il_da_controllare(p))
    pendenti = [d for d in (p.get("docsan") or []) if d.get("proposta_ia")]
    disp = il_disponibili(IL_ORDINE_VISTA)
    lav = _il_lavoro(pid)
    corre = bool(lav and lav["stato"] == "corre")
    if corre or pendenti:
        with st.container(border=True, key=f"il_vista_{pid}"):
            st.markdown("<div style='font-weight:700'>🤖 Riclassifica con l'IA</div>", unsafe_allow_html=True)
            if corre:
                _il_mostra_avanzamento(pid)
            if pendenti:
                _il_blocco_proposte(pid, pendenti)
    with st.expander("🤖 Riclassifica i documenti con l'IA"):
        if not disp:
            st.info("Per usare l'IA serve almeno una chiave gratuita (Gemini, Groq, Mistral…). L'amministratore la mette in **Utilità → 🤖 Intelligenza artificiale**.")
            return
        st.caption("Faccio rileggere ogni documento dall'IA (" + ", ".join(IL_FORNITORI[x]["nome"] for x in disp[:3]) + "). Se è **scritto a mano** lo leggono più servizi e confronto le "
                   "letture. **Prima ti mostro cosa cambierebbe**; cambia solo quello che lasci spuntato e tocchi **Applica**. Quello che hai corretto tu a mano non si tocca.")
        st.markdown(f"**Da controllare: {resta} di {n}**" + (f" · da confermare: {len(pendenti)} (qui sopra)" if pendenti else "") + (" · tutti controllati ✅" if not resta and not pendenti else ""))
        if corre:
            st.caption("La lettura è in corso: la vedi qui sopra.")
            return
        if lav and lav["stato"] in ("fatto", "fermato", "errore"):
            if lav["stato"] == "errore":
                st.warning("La lettura si è interrotta (" + str(lav.get("errore", "")) + "): quello già letto è salvato. Tocca di nuovo «Prova» per continuare con i rimanenti.")
            err = [x for x in (lav.get("out") or []) if x.get("errore")]
            letti = len(lav.get("out") or []) - len(err)
            st.caption(f"Ultima lettura: {letti} documenti controllati" + (f" · non letti {len(err)}: " + "; ".join(f"{x['titolo']} ({x['errore']})" for x in err[:5]) if err else "")
                       + (". Toccando «Prova» riprovo solo quelli rimasti." if err else ""))
        if "lu_ricerca_ui" in globals():
            lu_ricerca_ui("salute_" + str(pid))                            # 🔎 cerca in tutti i documenti (anche dentro)
        if "lu_ui_persone" in globals():
            lu_ui_persone()                                                 # nome e cognome sui documenti: i referti di un'altra persona vanno nella sua cartella
        tutti = st.checkbox(f"Rileggi anche quelli già controllati (tutti i {n})", key=f"il_tutti_{pid}", value=False)
        quanti = n if tutti else resta
        if st.button(f"🔍 Prova: leggi e classifica {quanti} document" + ("o" if quanti == 1 else "i"), key=f"il_prova_{pid}", width="stretch", disabled=not quanti):
            _il_avvia_lavoro(f, pid, tutti)
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# Utilità → 🤖 Intelligenza artificiale: quali chiavi ci sono e come crearle
# ---------------------------------------------------------------------------------------------------------------------
_IL_GUIDE = {
    "gemini": ["Apri il link qui sotto e accedi con il tuo account Google.", "Tocca **Create API key** (crea chiave API) e poi **Create API key in new project** (in un nuovo progetto).",
               "Tocca **Copy** (copia).", "In Streamlit: **Manage app → Settings → Secrets** e scrivi una riga: `GEMINI_API_KEY = \"la-chiave-copiata\"`, poi **Save** (salva)."],
    "groq": ["Apri il link e accedi (anche con Google).", "Tocca **Create API Key** (crea chiave), scrivi un nome qualsiasi (es. vitamemo) e tocca **Submit** (invia).",
             "Tocca **Copy** (copia): la chiave si vede una volta sola.", "Nei Secrets di Streamlit: `GROQ_API_KEY = \"la-chiave-copiata\"` e **Save**."],
    "mistral": ["Apri il link e crea l'account (serve il numero di telefono).", "Scegli il piano **Experiment** (gratuito).", "Tocca **Create new key** (crea nuova chiave) e poi **Copy**.",
                "Nei Secrets: `MISTRAL_API_KEY = \"la-chiave-copiata\"` e **Save**."],
    "openrouter": ["Apri il link e accedi (anche con Google).", "Tocca **Create Key** (crea chiave), metti un nome e lascia vuoto il «Credit limit» (limite di credito).",
                   "Copia la chiave.", "Nei Secrets: `OPENROUTER_API_KEY = \"la-chiave-copiata\"` e **Save**."],
    "nvidia": ["Apri il link e accedi o crea l'account NVIDIA (serve il numero di telefono).", "Tocca **Generate API Key** (genera chiave) e poi **Copy**.",
               "Nei Secrets: `NVIDIA_API_KEY = \"la-chiave-copiata\"` e **Save**."],
    "cloudflare": ["Crea l'account Cloudflare gratuito e apri il link.", "Tocca **Create Token** (crea token) → modello **Workers AI** → **Continue to summary** → **Create Token**, poi copialo.",
                   "Il numero dell'account (Account ID) lo trovi nella pagina principale di Cloudflare, a destra.",
                   "Nei Secrets due righe: `CLOUDFLARE_API_TOKEN = \"il-token\"` e `CLOUDFLARE_ACCOUNT_ID = \"il-numero-account\"`, poi **Save**."],
    "cohere": ["Apri il link e crea l'account.", "Nella pagina delle chiavi c'è già una **Trial key** (chiave di prova): tocca **Copy**.", "Nei Secrets: `COHERE_API_KEY = \"la-chiave\"` e **Save**."],
    "sambanova": ["Apri il link e crea l'account gratuito (anche con Google): ricevi un credito di prova.", "Tocca **Create API Key** (crea chiave), scrivi un nome e poi **Copy** (copia).",
                  "Nei Secrets: `SAMBANOVA_API_KEY = \"la-chiave\"` e **Save**. Non mettere la carta: quando il credito di prova finisce, l'app usa gli altri servizi."],
    "huggingface": ["Apri il link e crea l'account gratuito (anche con Google).", "Tocca **+ Create new token** (crea un nuovo token) e scegli **Fine-grained**.",
                    "Scrivi un nome (es. vitamemo) e spunta **Make calls to Inference Providers** (fare richieste ai fornitori di IA); in fondo tocca **Create token** e poi **Copy**.",
                    "Nei Secrets: `HF_TOKEN = \"la-chiave\"` e **Save**."],
    "deepseek": ["Apri il link e crea l'account.", "DeepSeek è a pagamento: in **Top up** (ricarica) metti pochi dollari.", "In **API keys** tocca **Create new API key**, poi copiala.",
                 "Nei Secrets: `DEEPSEEK_API_KEY = \"la-chiave\"` e **Save**."],
}


def il_blocco_utilita():
    """Il riquadro dell'amministratore: stato delle chiavi, prova, guida passo passo."""
    st.caption("Più chiavi metti, più l'app è affidabile: se un servizio ha finito le richieste del giorno, passa da sola al successivo. Le chiavi non escono mai dai Secrets.")
    if st.button("🔄 Ricontrolla le chiavi", key="il_ricontrolla", width="stretch"):
        _il_elenco_modelli.clear()
        with _IL_BLOCCO:
            _IL_STATO["pausa"].clear()
            _IL_STATO["modello"].clear()
        st.rerun()
    if "ta_stato_ui" in globals():
        try:
            ta_stato_ui()
        except Exception:
            pass
    oggi = _il_time.strftime("%Y-%m-%d")
    for prov in IL_ORDINE_VISTA:
        cfg = IL_FORNITORI[prov]
        ha = bool(il_chiave(prov))
        with _IL_BLOCCO:
            pausa = _IL_STATO["pausa"].get(prov)
            usi = _IL_STATO["usi"].get((prov, oggi), 0)
        credito = _il_credito_deepseek(_il_hl.sha1(il_chiave(prov).encode()).hexdigest()[:8]) if ha and prov == "deepseek" else ""
        stato = ("🟢 chiave presente" if ha else "⚪ nessuna chiave") + (f" · 💰 credito {credito}" if credito else "") + (f" · ⏸️ in pausa ({pausa[2]})" if ha and pausa and pausa[0] > _il_time.time() else "") + (f" · usata {usi} volte oggi" if usi else "")
        with st.expander(f"{cfg['nome']} — {stato}"):
            st.markdown(f"**Costo:** {cfg['costo']}  \n**Dati:** {cfg['dati']}")
            if prov == "deepseek" and ha:
                st.link_button("💰 Vedi il credito rimasto" + (f" ({credito})" if credito else ""), "https://platform.deepseek.com/usage", width="stretch")
            if prov in IL_RISERVATI:
                _il_ui_permessi(prov)
            if ha:
                if st.button("🧪 Prova questa chiave", key=f"il_prova_{prov}", width="stretch"):
                    with st.spinner("Provo… (al massimo un minuto)"):
                        r, err = il_chiama(prov, "Rispondi solo con la parola OK.", "Scrivi OK", max_tokens=400, timeout=30, modelli_max=3)
                    if r:
                        st.success(f"Funziona ✅ (modello: {il_modelli(prov, False)[0]})")
                    else:
                        st.error({"chiave": "La chiave non è valida: ricopiala nei Secrets.", "limite": "Richieste finite per ora: riprova più tardi.",
                                  "modello": "Il servizio non ha trovato il modello: scrivimelo e lo aggiorno.", "rete": "Il servizio non risponde: riprova."}.get(err, "Non ha funzionato: riprova."))
                        with _IL_BLOCCO:
                            dett = (_IL_STATO.get("errori") or {}).get(prov)
                        if dett:
                            st.caption("Dettaglio per Claude (mandami una foto di questa riga): " + dett)
                        elenco_ = _il_elenco_modelli(prov, _il_hl.sha1(il_chiave(prov).encode()).hexdigest()[:8])
                        st.caption("Modelli che il servizio dice di avere: " + (", ".join(m["id"] for m in elenco_[:25]) or "nessun elenco ricevuto"))
            else:
                st.markdown("**Come avere la chiave (dal telefono):**")
                for i, passo in enumerate(_IL_GUIDE.get(prov, []), 1):
                    st.markdown(f"{i}. {passo}")
                st.link_button("🔑 Apri la pagina per la chiave", cfg["link"], width="stretch")


# ---------------------------------------------------------------------------------------------------------------------
# LETTURA GENERALE CON L'IA: per tutti i documenti dell'app (identità, Casa, Auto, Animali, carta di circolazione…)
# ---------------------------------------------------------------------------------------------------------------------
_IL_DATA_RE = _il_re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _il_data_iso(v):
    """«27/03/2031», «2031-03-27», «27.03.2031» → «2031-03-27»; altrimenti ''."""
    s = str(v or "").strip()
    if _IL_DATA_RE.match(s):
        return s
    m = _il_re.match(r"^(\d{1,2})[./\-\s](\d{1,2})[./\-\s](\d{2,4})$", s)
    if m:
        g, me, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = a + 2000 if a < 100 else a
        if 1 <= g <= 31 and 1 <= me <= 12:
            return f"{a:04d}-{me:02d}-{g:02d}"
    return ""


def il_leggi_campi(contesto, campi, testo="", nome=None, mime=None, dati=None, immagini=None, quante=2, sempre=False, critici=(), regole=""):
    """Legge un documento con l'IA e ritorna ({campo: valore}, [servizi]).
    campi = {chiave: descrizione}. Le chiavi che finiscono con «data», «scadenza», «rilascio», «nascita», «emissione» sono date (AAAA-MM-GG).
    Con le immagini: il primo servizio; se mancano i campi «critici» o la sicurezza è bassa (o sempre=True), altri servizi e l'arbitro.
    Senza chiavi o se nessun servizio risponde: ({}, [])."""
    try:
        if not il_disponibili(IL_ORDINE_VISTA):
            return {}, []
        imgs = list(immagini or [])
        if not imgs and dati and (str(mime or "").startswith("image/") or str(mime or "").endswith("pdf") or str(nome or "").lower().endswith(".pdf")):
            imgs = il_immagini(nome or "doc", mime or "", dati, max_pagine=3)
        schema = ", ".join(f'"{k}": "{d}"' for k, d in campi.items())
        istr = (f"Sei un assistente esperto che legge {contesto}. Leggi con la massima attenzione e rispondi SOLO con un oggetto JSON, senza altro testo, con queste chiavi: "
                f"{{{schema}, \"sicurezza\": \"numero da 0 a 1: quanto sei sicuro\", \"dubbi\": [\"cosa non si legge bene\"]}}. "
                "Le date sempre in formato AAAA-MM-GG. Non scambiare MAI la data di nascita, la data di emissione/rilascio e la data di scadenza: leggi l'etichetta scritta accanto a ogni data. "
                "Se un dato non si legge con sicurezza lascialo vuoto (stringa vuota): NON inventare. " + (regole or ""))
        utente = ("Testo letto con la lettura automatica (può contenere errori, usalo solo come aiuto):\n" + str(testo)[:6000]) if str(testo or "").strip() else "Leggi il documento nell'immagine."
        if imgs:
            def _incerta(d):
                try:
                    poco = float(d.get("sicurezza") or 0) < 0.75
                except Exception:
                    poco = True
                return poco or any(not str(d.get(k) or "").strip() for k in critici)
            esito = il_consenso_immagine(istr, utente, imgs[:3], quante=quante, sempre=sempre, incerta=_incerta, schema_txt=schema)
            d, fonti = esito.get("risultato"), esito.get("fonti") or []
        else:
            if not str(testo or "").strip():
                return {}, []
            r, prov = il_testo(istr, utente, max_tokens=1200)
            d, fonti = il_json(r), ([prov] if prov else [])
        if not isinstance(d, dict):
            return {}, fonti
        out = {}
        for k in campi:
            v = d.get(k)
            if isinstance(v, (int, float)):
                v = str(v)
            if not isinstance(v, str) or not v.strip():
                continue
            v = v.strip()
            if _il_re.search(r"(data|scadenza|rilascio|nascita|emissione|richiamo|controllo|_da|_a)$", k):
                v = _il_data_iso(v)
                if not v:
                    continue
            out[k] = v
        if d.get("dubbi"):
            out["_dubbi"] = [str(x) for x in (d.get("dubbi") or []) if x][:4]
        return out, fonti
    except Exception:
        return {}, []


def il_nomi_fonti(fonti):
    return ", ".join(IL_FORNITORI.get(p, {}).get("nome", p) for p in fonti if p)


# ---------------------------------------------------------------------------------------------------------------------
# FOTO MIGLIORI: consigli subito dopo aver scattato/scelto la foto (in tutti i caricamenti col pulsante arancione, scontrini, biglietti)
# ---------------------------------------------------------------------------------------------------------------------
def il_mostra_avvisi_foto(f):
    """Se la foto è mossa, buia o con riflessi lo dice subito (una volta per foto), con il consiglio per rifarla."""
    try:
        if f is None:
            return []
        dati = f.getvalue() if hasattr(f, "getvalue") else (f.get("dati") if isinstance(f, dict) else None)
        if not dati:
            return []
        nome = getattr(f, "name", "") or (f.get("nome") if isinstance(f, dict) else "")
        mime = getattr(f, "type", "") or (f.get("mime") if isinstance(f, dict) else "")
        firma = (nome, len(dati))
        mem = st.session_state.setdefault("_il_foto_avvisi", {})
        if firma not in mem:
            mem[firma] = il_avvisi_foto(dati, mime, nome)
            if len(mem) > 40:
                mem.pop(next(iter(mem)))
        for a in mem[firma]:
            st.warning(a + " La lettura sarà più precisa con una foto migliore (puoi anche andare avanti così).")
        return mem[firma]
    except Exception:
        return []


if "_ca_pannello_caricamento" in globals() and "_il_pannello_prima" not in globals():
    _il_pannello_prima = _ca_pannello_caricamento

    def _ca_pannello_caricamento(n, multi=True):                     # noqa: F811
        up = _il_pannello_prima(n, multi)
        if up is not None:
            il_mostra_avvisi_foto(up)
        return up
