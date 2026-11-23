# =====================================================================================================================
# 🎛️ DOMOTICA (dentro Casa) — richiesta del 22 novembre 2026 («Centrale domotica intelligente», con le app che Leonardo usa già:
# Termostato BTicino (Smarther), Smart Life + Tuya (climatizzatore Argo Milo, lampadine della cucina), Google Home).
#
# COME FUNZIONA (niente comandi finti):
#  - L'app gira su Streamlit (nel cloud): NON può cercare gli apparecchi nel Wi-Fi o nel Bluetooth di casa. Parla con i CLOUD UFFICIALI
#    dei produttori, con le chiavi gratuite che Leonardo crea una volta:
#      · Tuya / Smart Life  → Tuya Cloud API (secrets [tuya]: access_id, access_secret, region)       — dm_tuya_*
#      · BTicino Smarther   → Legrand Smarther API v2.0 (secrets [smarther]: subscription_key, client_id, client_secret,
#                             redirect_uri; accesso OAuth una volta, token cifrato in domotica/<uid>_smarther.json) — dm_sm_*
#      · tutte le altre app (Google Home, Alexa…) → pulsante «▶ Apri nell'app» (il comando si dà lì)
#  - I comandi mostrati sono SOLO quelli che il cloud dichiara per quell'apparecchio (funzioni Tuya / modi Smarther).
#    Ogni comando risponde «✅ fatto» o con l'errore del produttore.
#  - Dati: d["casa"]["domotica"] nel file personale = {stanze, dispositivi, scenari, registro}. Gli STATI (acceso, temperatura…)
#    non si salvano: si leggono dal cloud quando apri la scheda.
#  - Prove: VM_DM_FINTO = JSON con apparecchi finti (solo per le prove automatiche: mai in produzione).
# =====================================================================================================================
import hashlib as _dm_hl
import hmac as _dm_hmac
import json as _dm_json
import os as _dm_os
import time as _dm_time
import uuid as _dm_uuid
import html as _dm_h
import urllib.parse as _dm_up
import requests as _dm_req

DM_STANZE_BASE = ["Soggiorno", "Cucina", "Camera da letto", "Bagno", "Ingresso", "Corridoio", "Garage", "Giardino"]
DM_ICONE_STANZA = {"Soggiorno": "🛋️", "Cucina": "🍳", "Camera da letto": "🛏️", "Bagno": "🛁", "Ingresso": "🚪", "Corridoio": "🚶", "Garage": "🚗", "Giardino": "🌳"}
DM_CATEGORIE = {"luce": "💡 Illuminazione", "presa": "🔌 Prese smart", "interruttore": "🎚️ Interruttori e relè", "clima": "❄️ Climatizzatori",
                "termostato": "🌡️ Termostati e riscaldamento", "tapparella": "🪟 Tapparelle e tende", "telecamera": "📹 Telecamere",
                "sensore": "📟 Sensori", "sicurezza": "🛡️ Sicurezza, allarmi e serrature", "elettrodomestico": "🧺 Elettrodomestici",
                "multimedia": "📺 TV, audio e assistenti vocali", "irrigazione": "🌱 Irrigazione", "altro": "📦 Altro"}
# categorie Tuya → nostre (https://developer.tuya.com → «Standard instruction set»)
DM_TUYA_CAT = {"dj": "luce", "dd": "luce", "xdd": "luce", "fwd": "luce", "dc": "luce", "tgq": "luce", "tgkg": "interruttore", "kg": "interruttore",
               "cz": "presa", "pc": "presa", "kt": "clima", "ktkzq": "clima", "wk": "termostato", "qn": "termostato", "rs": "termostato",
               "cl": "tapparella", "clkg": "tapparella", "sp": "telecamera", "pir": "sensore", "wsdcg": "sensore", "mcs": "sensore",
               "ywbj": "sicurezza", "rqbj": "sicurezza", "sj": "sicurezza", "ms": "sicurezza", "mal": "sicurezza", "sgbj": "sicurezza",
               "xyj": "elettrodomestico", "cs": "elettrodomestico", "kj": "elettrodomestico", "sd": "elettrodomestico", "fs": "elettrodomestico",
               "ggq": "irrigazione", "sfkzq": "irrigazione", "wf_sp": "telecamera"}
DM_SENSIBILI = {"sicurezza"}                                             # serrature, allarmi: comando solo con conferma
# app già sul telefono: pacchetto Android (si aprono con un tocco; se mancano, si apre il Play Store)
DM_APP = {"smartlife": ("Smart Life", "com.tuya.smartlife"), "tuya": ("Tuya Smart", "com.tuya.smart"),
          "bticino": ("BTicino Termostato", "it.bticino.thermostat"), "googlehome": ("Google Home", "com.google.android.apps.chromecast.app"),
          "alexa": ("Amazon Alexa", "com.amazon.dee.app"), "smartthings": ("SmartThings", "com.samsung.android.oneconnect"),
          "hue": ("Philips Hue", "com.philips.lighting.hue2"), "shelly": ("Shelly Smart Control", "cloud.shelly.smartcontrol"),
          "homeassistant": ("Home Assistant", "io.homeassistant.companion.android"), "altra": ("Altra app", "")}
DM_TUYA_URL = {"eu": "https://openapi.tuyaeu.com", "weu": "https://openapi-weaz.tuyaeu.com", "us": "https://openapi.tuyaus.com",
               "eus": "https://openapi-ueaz.tuyaus.com", "cn": "https://openapi.tuyacn.com", "in": "https://openapi.tuyain.com"}
DM_SM_API = "https://api.developer.legrand.com/smarther/v2.0"
DM_SM_AUTH = "https://partners-login.eliotbylegrand.com/authorize"
DM_SM_TOKEN = "https://partners-login.eliotbylegrand.com/token"
DM_ENUM_IT = {"cold": "❄️ Freddo", "hot": "🔥 Caldo", "heat": "🔥 Caldo", "wind": "🌀 Solo ventola", "fan": "🌀 Solo ventola", "wet": "💧 Deumidifica",
              "dehumidification": "💧 Deumidifica", "auto": "🅰️ Automatico", "sleep": "🌙 Notte", "eco": "🌿 Eco", "low": "Bassa", "mid": "Media",
              "middle": "Media", "high": "Alta", "strong": "Massima", "white": "⚪ Bianco", "colour": "🌈 Colore", "scene": "🎬 Scena", "music": "🎵 Musica",
              "open": "⬆️ Apri", "close": "⬇️ Chiudi", "stop": "⏹️ Ferma", "manual": "✋ Manuale", "smart": "🧠 Smart", "holiday": "🏖️ Vacanza"}
DM_CODICI_IT = {"switch_led": "Accesa", "switch": "Acceso", "switch_1": "Acceso", "switch_2": "Uscita 2", "bright_value_v2": "Luminosità",
                "bright_value": "Luminosità", "temp_value_v2": "Tonalità del bianco", "temp_value": "Tonalità del bianco", "work_mode": "Modalità",
                "colour_data_v2": "Colore", "colour_data": "Colore", "temp_set": "Temperatura voluta", "mode": "Modalità", "windspeed": "Ventola",
                "fan_speed_enum": "Ventola", "temp_current": "Temperatura della stanza", "humidity_current": "Umidità", "control": "Comando",
                "percent_control": "Apertura (%)", "cur_power": "Potenza (W)", "cur_voltage": "Tensione (V)", "cur_current": "Corrente (mA)",
                "add_ele": "Energia", "countdown_1": "Spegnimento a tempo", "light": "Luce", "sleep": "Notte", "eco": "Eco", "lock": "Blocco tasti",
                "child_lock": "Blocco bambini", "anion": "Ionizzatore", "swing": "Oscillazione", "temp_unit_convert": "Unità di misura"}


# ---------------------------------------------------------------------------------------------------------------------
# 1. DATI
# ---------------------------------------------------------------------------------------------------------------------
def dm_vuoto():
    return {"stanze": [], "dispositivi": [], "scenari": [], "registro": []}


def dm_migra(d):
    c = d.setdefault("casa", {})
    dm = c.setdefault("domotica", dm_vuoto())
    for k, v in dm_vuoto().items():
        dm.setdefault(k, v if not isinstance(v, list) else [])
    return dm


def _dm_id():
    return _dm_uuid.uuid4().hex[:10]


def _dm_ora():
    try:
        return adesso().isoformat(timespec="seconds")
    except Exception:
        return _dm_time.strftime("%Y-%m-%dT%H:%M:%S")


def dm_stanze(dm, casa_id=""):
    """Le stanze della casa: quelle predefinite più quelle aggiunte (ognuna con id «b:Nome» se predefinita)."""
    proprie = [s for s in dm.get("stanze") or [] if (s.get("casa_id") or "") == (casa_id or "")]
    nascoste = {s["nome"] for s in proprie if s.get("nascosta")}
    base = [{"id": "b:" + n, "nome": n, "icona": DM_ICONE_STANZA.get(n, "🏠"), "casa_id": casa_id} for n in DM_STANZE_BASE if n not in nascoste]
    return base + [s for s in proprie if not s.get("nascosta")]


def dm_nome_stanza(dm, sid, casa_id=""):
    s = next((x for x in dm_stanze(dm, casa_id) if x["id"] == sid), None)
    return f"{s.get('icona', '🏠')} {s['nome']}" if s else "❔ Stanza da scegliere"


def dm_registra(dm, testo):
    dm.setdefault("registro", []).append({"il": _dm_ora(), "chi": (st.session_state.get("sess") or {}).get("nome", ""), "testo": str(testo)[:300]})
    dm["registro"] = dm["registro"][-300:]


def dm_aggiungi_dispositivo(dm, x):
    """Aggiunge senza doppioni: stesso collegamento (piattaforma + id del cloud) = stesso apparecchio (si aggiorna)."""
    if x.get("piattaforma") in ("tuya", "smarther") and x.get("ext_id"):
        gia = next((y for y in dm["dispositivi"] if y.get("piattaforma") == x["piattaforma"] and y.get("ext_id") == x["ext_id"]), None)
        if gia:
            for k in ("marca", "modello", "categoria_cloud"):
                if x.get(k) and not gia.get(k):
                    gia[k] = x[k]
            return gia, False
    r = {"id": _dm_id(), "casa_id": "", "stanza_id": "", "nome": "", "categoria": "altro", "marca": "", "modello": "", "piattaforma": "app",
         "ext_id": "", "app": "", "foto": "", "installato_il": "", "note": "", "creato_il": _dm_ora()}
    r.update({k: v for k, v in x.items() if v is not None})
    dm["dispositivi"].append(r)
    return r, True


def _dm_leggi():
    try:
        d = carica_dati(crea_archivio(), percorso_mio())
    except Exception:
        d = {}
    d = dict(d or {})
    d["casa"] = dict(d.get("casa") or {})
    d["casa"]["domotica"] = dict(d["casa"].get("domotica") or dm_vuoto())
    return dm_migra(d)


def _dm_salva(fn, msg):
    salva_file(percorso_mio(), lambda d: fn(dm_migra(d)), "Domotica: " + msg)


# ---------------------------------------------------------------------------------------------------------------------
# 2. SEGRETI (solo nei Secrets di Streamlit, mai nei dati)
# ---------------------------------------------------------------------------------------------------------------------
def _dm_secret(gruppo):
    try:
        g = st.secrets.get(gruppo)
        return dict(g) if g else {}
    except Exception:
        return {}


def dm_finto():
    try:
        return _dm_json.loads(_dm_os.environ.get("VM_DM_FINTO") or "") or None
    except Exception:
        return None


def dm_tuya_conf():
    s = _dm_secret("tuya")
    if s.get("access_id") and s.get("access_secret"):
        return {"id": str(s["access_id"]).strip(), "secret": str(s["access_secret"]).strip(), "base": DM_TUYA_URL.get(str(s.get("region") or "eu").lower(), DM_TUYA_URL["eu"])}
    return None


def dm_sm_conf():
    s = _dm_secret("smarther")
    if all(s.get(k) for k in ("subscription_key", "client_id", "client_secret", "redirect_uri")):
        return {k: str(s[k]).strip() for k in ("subscription_key", "client_id", "client_secret", "redirect_uri")}
    return None


class DmErrore(Exception):
    """Errore del cloud spiegato in italiano."""


# ---------------------------------------------------------------------------------------------------------------------
# 3. TUYA / SMART LIFE (cloud ufficiale: firma HMAC-SHA256, https://developer.tuya.com/en/docs/iot/new-singnature)
# ---------------------------------------------------------------------------------------------------------------------
_DM_SHA_VUOTO = _dm_hl.sha256(b"").hexdigest()


def dm_tuya_firma(client_id, secret, metodo, percorso, corpo="", token="", t="", nonce=""):
    """La firma Tuya: HMAC-SHA256(client_id + token + t + nonce + stringToSign) in maiuscolo.
    stringToSign = METODO \\n sha256(corpo) \\n (intestazioni firmate: nessuna) \\n percorso con la query ordinata."""
    if "?" in percorso:
        base, q = percorso.split("?", 1)
        coppie = sorted(_dm_up.parse_qsl(q, keep_blank_values=True))
        percorso = base + "?" + "&".join(f"{k}={v}" for k, v in coppie)
    sts = "\n".join([metodo.upper(), _dm_hl.sha256((corpo or "").encode("utf-8")).hexdigest(), "", percorso])
    msg = client_id + (token or "") + str(t) + (nonce or "") + sts
    return _dm_hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), _dm_hl.sha256).hexdigest().upper()


def _dm_tuya_token(conf, forza=False):
    cache = st.session_state.setdefault("_dm_tuya_tok", {})
    if not forza and cache.get("tok") and cache.get("scade", 0) > _dm_time.time() + 60:
        return cache["tok"]
    t = str(int(_dm_time.time() * 1000))
    perc = "/v1.0/token?grant_type=1"
    firma = dm_tuya_firma(conf["id"], conf["secret"], "GET", perc, "", "", t)
    r = _dm_req.get(conf["base"] + perc, headers={"client_id": conf["id"], "sign": firma, "t": t, "sign_method": "HMAC-SHA256"}, timeout=12)
    j = r.json()
    if not j.get("success"):
        raise DmErrore(_dm_tuya_err(j))
    res = j.get("result") or {}
    cache.update(tok=res.get("access_token"), scade=_dm_time.time() + int(res.get("expire_time") or 3600))
    return cache["tok"]


def _dm_tuya_err(j):
    cod, msg = j.get("code"), j.get("msg") or ""
    spiegati = {1004: "la firma non è giusta: controlla «access_secret» nei Secrets", 1010: "il permesso è scaduto: riprovo", 1011: "il permesso non è valido",
                1106: "permesso negato: in Tuya, nel progetto, apri «Service API» e attiva «IoT Core»", 28841002: "l'abbonamento di prova Tuya è scaduto: rinnovalo (Cloud → IoT Core → Extend)",
                2017: "l'apparecchio non risponde (è spento o senza Wi-Fi?)", 2008: "comando non supportato da questo apparecchio",
                1109: "parametro sbagliato", 28841105: "nessun account dell'app collegato al progetto Tuya (Devices → Link App Account)"}
    return f"Tuya: {spiegati.get(cod, msg or 'errore')} (codice {cod})"


def dm_tuya(metodo, percorso, corpo=None):
    """Una richiesta al cloud Tuya (con il permesso rinnovato da solo). Ritorna «result»."""
    conf = dm_tuya_conf()
    if not conf:
        raise DmErrore("Tuya non è ancora collegato (mancano le chiavi nei Secrets).")
    testo = _dm_json.dumps(corpo, separators=(",", ":")) if corpo is not None else ""
    for tentativo in range(2):
        tok = _dm_tuya_token(conf, forza=bool(tentativo))
        t = str(int(_dm_time.time() * 1000))
        firma = dm_tuya_firma(conf["id"], conf["secret"], metodo, percorso, testo, tok, t)
        h = {"client_id": conf["id"], "access_token": tok, "sign": firma, "t": t, "sign_method": "HMAC-SHA256", "Content-Type": "application/json"}
        r = _dm_req.request(metodo, conf["base"] + percorso, headers=h, data=testo or None, timeout=15)
        j = r.json()
        if j.get("success"):
            return j.get("result")
        if j.get("code") in (1010, 1011) and not tentativo:
            continue
        raise DmErrore(_dm_tuya_err(j))
    raise DmErrore("Tuya non risponde.")


def _dm_tuya_due(metodo, percorso, corpo=None):
    """Prima /v1.0/devices/…, poi /v1.0/iot-03/devices/… (alcuni progetti Tuya hanno solo l'una o l'altra)."""
    try:
        return dm_tuya(metodo, percorso, corpo)
    except DmErrore as e:
        if "codice 1106" in str(e) or "codice 1108" in str(e) or "codice 2009" in str(e):
            return dm_tuya(metodo, percorso.replace("/v1.0/devices/", "/v1.0/iot-03/devices/"), corpo)
        raise


def dm_tuya_dispositivi():
    """Gli apparecchi di tutti gli account dell'app (Smart Life / Tuya) collegati al progetto."""
    f = dm_finto()
    if f is not None:
        return f.get("tuya", [])
    out, chiave = [], ""
    for _ in range(10):
        res = dm_tuya("GET", "/v1.0/iot-01/associated-users/devices?size=100" + (f"&last_row_key={chiave}" if chiave else ""))
        devs = (res or {}).get("devices") or []
        out += devs
        chiave = (res or {}).get("last_row_key") or ""
        if not (res or {}).get("has_more") or not chiave:
            break
    return [{"ext_id": x.get("id"), "nome": x.get("name") or x.get("product_name") or "Apparecchio", "modello": x.get("model") or x.get("product_name") or "",
             "categoria_cloud": x.get("category") or "", "online": bool(x.get("online")), "app_cloud": "Smart Life / Tuya"} for x in out if x.get("id")]


def dm_tuya_funzioni(dev_id):
    f = dm_finto()
    if f is not None:
        return f.get("funzioni", {}).get(dev_id, [])
    res = _dm_tuya_due("GET", f"/v1.0/devices/{dev_id}/functions") or {}
    out = []
    for fn in res.get("functions") or []:
        try:
            val = _dm_json.loads(fn.get("values") or "{}")
        except Exception:
            val = {}
        out.append({"code": fn.get("code"), "type": fn.get("type"), "values": val, "name": fn.get("name") or ""})
    return out


def dm_tuya_stato(dev_id):
    f = dm_finto()
    if f is not None:
        return f.get("stato", {}).get(dev_id, {})
    return {x.get("code"): x.get("value") for x in (_dm_tuya_due("GET", f"/v1.0/devices/{dev_id}/status") or [])}


def dm_tuya_comando(dev_id, codice, valore):
    f = dm_finto()
    if f is not None:
        f.setdefault("comandi", []).append([dev_id, codice, valore])
        _dm_os.environ["VM_DM_FINTO"] = _dm_json.dumps(f)
        f.get("stato", {}).setdefault(dev_id, {})[codice] = valore
        _dm_os.environ["VM_DM_FINTO"] = _dm_json.dumps(f)
        return True
    return bool(_dm_tuya_due("POST", f"/v1.0/devices/{dev_id}/commands", {"commands": [{"code": codice, "value": valore}]}))


# ---------------------------------------------------------------------------------------------------------------------
# 4. BTICINO SMARTHER (Legrand, API v2.0 con OAuth; il permesso si rinnova da solo con il «refresh token» cifrato)
# ---------------------------------------------------------------------------------------------------------------------
def _dm_sm_chiave(conf):
    import base64 as _b64
    from cryptography.fernet import Fernet
    return Fernet(_b64.urlsafe_b64encode(_dm_hl.sha256(("vitamemo-domotica|" + conf["client_secret"]).encode()).digest()))


def _dm_sm_file(uid=None):
    uid = uid or (st.session_state.get("sess") or {}).get("uid") or "admin"
    return f"domotica/{uid}_smarther.json"


def _dm_sm_leggi_tok(conf, uid=None):
    try:
        raw = crea_archivio().leggi(_dm_sm_file(uid)) or {}
        if not raw.get("cifrato"):
            return {}
        return _dm_json.loads(_dm_sm_chiave(conf).decrypt(raw["cifrato"].encode()).decode())
    except Exception:
        return {}


def _dm_sm_scrivi_tok(conf, tok, uid=None):
    cif = _dm_sm_chiave(conf).encrypt(_dm_json.dumps(tok).encode()).decode()

    def _f(d):
        d.clear()
        d.update({"cifrato": cif, "aggiornato_il": _dm_ora()})
    salva_file(_dm_sm_file(uid), _f, "Domotica: collegamento termostato")


def dm_sm_collegato():
    if dm_finto() is not None:
        return bool(dm_finto().get("smarther"))
    conf = dm_sm_conf()
    return bool(conf and _dm_sm_leggi_tok(conf).get("refresh_token"))


def dm_sm_url_accesso():
    """L'indirizzo della pagina di accesso BTicino; lo «state» (usa e getta, 15 minuti) dice a chi salvare il collegamento."""
    conf = dm_sm_conf()
    stato = "vmdm" + _dm_uuid.uuid4().hex
    uid = (st.session_state.get("sess") or {}).get("uid") or "admin"

    def _f(d):
        p = {k: v for k, v in (d.get("attesa") or {}).items() if v.get("scade", 0) > _dm_time.time()}
        p[stato] = {"uid": uid, "scade": _dm_time.time() + 900, "k": st.query_params.get("k") or ""}
        d["attesa"] = p
    salva_file("domotica/accessi_in_attesa.json", _f, "Domotica: accesso BTicino in corso")
    return DM_SM_AUTH + "?" + _dm_up.urlencode({"client_id": conf["client_id"], "response_type": "code", "redirect_uri": conf["redirect_uri"], "state": stato})


def _dm_sm_token_da(conf, dati):
    r = _dm_req.post(DM_SM_TOKEN, data=dict(dati, client_id=conf["client_id"], client_secret=conf["client_secret"]), timeout=15)
    try:
        j = r.json()
    except Exception:
        j = {}
    if r.status_code >= 400 or not j.get("access_token"):
        raise DmErrore(f"BTicino: accesso non riuscito ({r.status_code} {str(j.get('error_description') or j.get('error') or r.text)[:120]})")
    return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token") or dati.get("refresh_token"),
            "scade": _dm_time.time() + int(j.get("expires_in") or 3600)}


def dm_sm_ritorno():
    """La persona torna dalla pagina BTicino (?code=…&state=vmdm…): si salva il collegamento, anche se non ha ancora fatto l'accesso a VitaMemo."""
    code, stato = st.query_params.get("code"), st.query_params.get("state") or ""
    conf = dm_sm_conf()
    esito = st.session_state.get("_dm_sm_esito")
    if esito is None:
        try:
            attesa = (crea_archivio().leggi("domotica/accessi_in_attesa.json") or {}).get("attesa") or {}
            voce = attesa.get(stato)
            if not conf or not voce or voce.get("scade", 0) < _dm_time.time():
                raise DmErrore("il collegamento è scaduto o non è partito da VitaMemo: riprova da Casa → Domotica")
            try:
                tok = _dm_sm_token_da(conf, {"grant_type": "authorization_code", "code": code, "redirect_uri": conf["redirect_uri"]})
            except DmErrore:
                tok = _dm_sm_token_da(conf, {"grant_type": "authorization_code", "code": code})
            _dm_sm_scrivi_tok(conf, tok, voce["uid"])
            esito = {"ok": True, "k": voce.get("k") or ""}
        except Exception as e:
            esito = {"ok": False, "msg": str(e)}
        st.session_state["_dm_sm_esito"] = esito
    if esito.get("ok"):
        st.success("✅ Termostato BTicino collegato a VitaMemo. Ora lo trovi in 🏠 Casa → 🎛️ Domotica.")
    else:
        st.error("❌ Non sono riuscito a collegare il termostato: " + esito.get("msg", ""))
    if st.button("Torna a VitaMemo", type="primary", key="dm_sm_torna"):
        k = (st.session_state.pop("_dm_sm_esito", None) or {}).get("k")
        st.session_state.pop("_dm_sm_tok", None)
        st.query_params.clear()
        if k:
            st.query_params["k"] = k                                    # si rientra senza riscrivere la password (accesso ricordato)
        st.rerun()
    st.stop()


def _dm_sm_access(conf):
    cache = st.session_state.setdefault("_dm_sm_tok", {})
    if cache.get("access_token") and cache.get("scade", 0) > _dm_time.time() + 60:
        return cache["access_token"]
    vecchio = _dm_sm_leggi_tok(conf)
    if not vecchio.get("refresh_token"):
        raise DmErrore("il termostato non è ancora collegato: tocca «🔗 Collega il termostato BTicino»")
    nuovo = _dm_sm_token_da(conf, {"grant_type": "refresh_token", "refresh_token": vecchio["refresh_token"]})
    if nuovo.get("refresh_token") != vecchio.get("refresh_token"):
        _dm_sm_scrivi_tok(conf, {"refresh_token": nuovo["refresh_token"]})
    cache.clear()
    cache.update(nuovo)
    return nuovo["access_token"]


def dm_sm(metodo, percorso, corpo=None):
    conf = dm_sm_conf()
    if not conf:
        raise DmErrore("BTicino non è ancora configurato (mancano le chiavi nei Secrets).")
    h = {"Ocp-Apim-Subscription-Key": conf["subscription_key"], "Authorization": "Bearer " + _dm_sm_access(conf), "Content-Type": "application/json"}
    r = _dm_req.request(metodo, DM_SM_API + percorso, headers=h, data=_dm_json.dumps(corpo) if corpo is not None else None, timeout=15)
    if r.status_code in (200, 201, 204):
        try:
            return r.json() if r.text.strip() else {}
        except Exception:
            return {}
    try:
        dett = str((r.json() or {}).get("message") or (r.json() or {}).get("error_description") or r.text)[:160]
    except Exception:
        dett = (r.text or "")[:160]
    if r.status_code == 401 and "subscription key" in dett.lower():
        raise DmErrore("BTicino: la «subscription_key» nei Secrets non è giusta o l'abbonamento Starter Kit non è attivo (401). Ricopia la Primary key da Legrand → Subscription keys")
    spieg = {401: "accesso negato: nell'app «Termostato» attiva Account → Accesso di terze parti, poi in VitaMemo «🔄 Ricollega il termostato» (Casa → Domotica → Collegamenti)", 403: "la chiave «subscription_key» non è giusta o l'abbonamento non è attivo",
             404: "termostato non trovato", 408: "il termostato non risponde (Wi-Fi?)", 429: "troppe richieste: aspetta un minuto", 469: "il termostato è offline"}
    raise DmErrore(f"BTicino: {spieg.get(r.status_code, 'errore')} ({r.status_code})" + (f" — risposta: {dett}" if dett else ""))


def _dm_jwt_info(tok):
    """Chi è il proprietario del permesso (senza mostrare il permesso): email/nome e scadenza dal token."""
    try:
        import base64 as _b64
        corpo = tok.split(".")[1]
        corpo += "=" * (-len(corpo) % 4)
        j = _dm_json.loads(_b64.urlsafe_b64decode(corpo))
        mail = j.get("email") or (j.get("emails") or [None])[0] or j.get("upn") or j.get("name") or j.get("sub")
        return {"account": mail, "scope": j.get("scp") or j.get("scope"), "aud": j.get("aud")}
    except Exception:
        return {}


def dm_sm_diagnosi():
    """Prova passo per passo il collegamento BTicino e dice dove si ferma (senza mostrare chiavi)."""
    out = []
    conf = dm_sm_conf()
    if not conf:
        return [("❌", "Chiavi [smarther] nei Secrets", "mancano o sono incomplete")]
    out.append(("✅", "Chiavi [smarther] nei Secrets", f"subscription_key di {len(conf['subscription_key'])} caratteri, redirect {conf['redirect_uri']}"))
    vecchio = _dm_sm_leggi_tok(conf)
    if not vecchio.get("refresh_token"):
        return out + [("❌", "Accesso BTicino", "non ancora fatto: tocca «Collega il termostato»")]
    out.append(("✅", "Accesso BTicino salvato", "c'è"))
    st.session_state.pop("_dm_sm_tok", None)
    try:
        acc = _dm_sm_access(conf)
        info = _dm_jwt_info(acc)
        out.append(("✅", "Permesso rinnovato", f"account: {info.get('account') or '?'} · permessi: {info.get('scope') or '?'}"))
    except Exception as e:
        return out + [("❌", "Permesso rinnovato", str(e))]
    h = {"Ocp-Apim-Subscription-Key": conf["subscription_key"], "Authorization": "Bearer " + acc}
    piante = []
    try:
        r = _dm_req.get(DM_SM_API + "/plants", headers=h, timeout=15)
        out.append(("✅" if r.status_code in (200, 204) else "❌", "Elenco impianti (/plants)", f"HTTP {r.status_code} · {(r.text or '')[:200]}"))
        piante = ((r.json() or {}).get("plants") or []) if r.status_code == 200 else []
    except Exception as e:
        out.append(("❌", "Elenco impianti (/plants)", str(e)))
    for pl in piante[:2]:
        for nome, perc in (("Termostati dell'impianto (topology)", f"/plants/{pl['id']}/topology"),
                           ("Termostati dell'impianto (modules)", f"/chronothermostat/thermoregulation/addressLocation/plants/{pl['id']}/modules")):
            try:
                r = _dm_req.get(DM_SM_API + perc, headers=h, timeout=15)
                out.append(("✅" if r.status_code == 200 else "❌", nome, f"HTTP {r.status_code} · {(r.text or '')[:300]}"))
            except Exception as e:
                out.append(("❌", nome, str(e)))
    try:
        trovati = dm_sm_dispositivi()
        out.append(("✅" if trovati else "❌", "Termostati trovati da VitaMemo", ", ".join(t["nome"] for t in trovati) or "nessuno"))
    except Exception as e:
        out.append(("❌", "Termostati trovati da VitaMemo", str(e)))
    return out


def dm_sm_dispositivi():
    """Impianti (/plants) → per ognuno la topologia (/plants/{id}/topology → plant.modules): un termostato per modulo."""
    f = dm_finto()
    if f is not None:
        return f.get("smarther", [])
    out = []
    for pl in (dm_sm("GET", "/plants") or {}).get("plants") or []:
        try:
            topo = dm_sm("GET", f"/plants/{pl['id']}/topology") or {}
        except DmErrore:
            topo = {}
        mods = ((topo.get("plant") or {}).get("modules")) or topo.get("modules") or []
        if not mods:
            try:
                alt = dm_sm("GET", f"/chronothermostat/thermoregulation/addressLocation/plants/{pl['id']}/modules") or {}
                mods = alt.get("modules") or alt.get("chronothermostats") or ((alt.get("plant") or {}).get("modules")) or []
            except DmErrore:
                mods = []
        for m in mods:
            if m.get("device") and "chrono" not in str(m.get("device")).lower():
                continue
            out.append({"ext_id": f"{pl['id']}|{m.get('id')}", "nome": m.get("name") or pl.get("name") or "Termostato", "modello": "Smarther",
                        "categoria_cloud": "termostato", "online": True, "app_cloud": "BTicino Termostato"})
    return out


def dm_sm_stato(ext_id):
    f = dm_finto()
    if f is not None:
        return f.get("stato_sm", {}).get(ext_id, {})
    pl, mod = ext_id.split("|", 1)
    j = dm_sm("GET", f"/chronothermostat/thermoregulation/addressLocation/plants/{pl}/modules/parameter/id/value/{mod}") or {}
    c = (j.get("chronothermostats") or [{}])[0]

    def _mis(x):
        try:
            return float(((x or {}).get("measures") or [{}])[0].get("value"))
        except Exception:
            return None
    try:
        sp = float((c.get("setPoint") or {}).get("value"))
    except Exception:
        sp = None
    return {"temperatura": _mis(c.get("thermometer")), "umidita": _mis(c.get("hygrometer")), "voluta": sp, "modo": str(c.get("mode") or "").lower(),
            "funzione": str(c.get("function") or "heating").lower(), "programma": ((c.get("programs") or [{}])[0] or {}).get("number"),
            "acceso": str(c.get("loadState") or "").upper() == "ACTIVE", "fino": _dm_sm_fine(c.get("activationTime"))}


def _dm_sm_fine(at):
    """«2026-11-23T10:00:00/2026-11-23T11:30:00» → «11:30» (o «24/11 11:30» se non è oggi)."""
    try:
        import datetime as _dt
        fine = str(at or "").split("/")[1][:16]
        d = _dt.datetime.strptime(fine, "%Y-%m-%dT%H:%M")
        try:
            oggi = adesso().date()
        except Exception:
            oggi = _dt.date.today()
        return d.strftime("%H:%M") if d.date() == oggi else d.strftime("%d/%m %H:%M")
    except Exception:
        return ""


def dm_sm_programmi(ext_id):
    """Programmi settimanali salvati nel termostato: [(numero, nome)]. Se Legrand non risponde: lista vuota."""
    f = dm_finto()
    if f is not None:
        return [tuple(p) for p in f.get("programmi_sm", {}).get(ext_id, [])]
    pl, mod = ext_id.split("|", 1)
    try:
        j = dm_sm("GET", f"/chronothermostat/thermoregulation/addressLocation/plants/{pl}/modules/parameter/id/value/{mod}/programlist") or {}
    except Exception:
        return []
    progs = ((j.get("chronothermostats") or [{}])[0] or {}).get("programs") or j.get("programs") or []
    out = []
    for p_ in progs:
        try:
            out.append((int(p_.get("number")), str(p_.get("name") or f"Programma {p_.get('number')}")))
        except Exception:
            pass
    return out


def dm_sm_imposta(ext_id, modo, voluta=None, minuti=None, programma=None, funzione=None, fino=None):
    """modo: automatic (programma), manual (temperatura, per sempre o per N minuti), boost (30/60/90 min), off, protection (antigelo).
    Il corpo è lo stesso dell'integrazione per Home Assistant (bticino_x8000): funzione attuale, setPoint in «°C», programma attuale."""
    f = dm_finto()
    if f is not None:
        f.setdefault("comandi", []).append([ext_id, modo, voluta, minuti, fino.strftime("%Y-%m-%dT%H:%M") if fino else None])
        _dm_os.environ["VM_DM_FINTO"] = _dm_json.dumps(f)
        return True
    import datetime as _dt
    pl, mod = ext_id.split("|", 1)
    try:
        ora_st = dm_sm_stato(ext_id)
    except Exception:
        ora_st = {}
    funz = (funzione or ora_st.get("funzione") or "heating").lower()
    prog = int(programma or ora_st.get("programma") or 1)
    try:
        adesso_ = adesso().replace(microsecond=0, tzinfo=None)
    except Exception:
        adesso_ = _dt.datetime.now().replace(microsecond=0)
    fmt = "%Y-%m-%dT%H:%M:%S"
    corpo = {"function": funz, "mode": modo}
    if modo == "manual":
        corpo["setPoint"] = {"value": f"{float(voluta if voluta is not None else (ora_st.get('voluta') or 20)):.1f}", "unit": "°C"}
        if fino is not None:
            corpo["activationTime"] = adesso_.strftime(fmt) + "/" + fino.replace(second=0, microsecond=0, tzinfo=None).strftime(fmt)
        elif minuti:
            corpo["activationTime"] = adesso_.strftime(fmt) + "/" + (adesso_ + _dt.timedelta(minutes=int(minuti))).strftime(fmt)
        else:
            corpo["programs"] = [{"number": prog}]
    elif modo == "automatic":
        corpo["programs"] = [{"number": prog}]
        if ora_st.get("voluta") is not None:
            corpo["setPoint"] = {"value": f"{float(ora_st['voluta']):.1f}", "unit": "°C"}
    elif modo == "boost":
        m_ = int(minuti or 30)
        corpo["activationTime"] = adesso_.strftime(fmt) + "/" + (adesso_ + _dt.timedelta(minutes=m_)).strftime(fmt)
        corpo["setPoint"] = {"value": "7" if funz == "cooling" else "40", "unit": "°C"}
    dm_sm("POST", f"/chronothermostat/thermoregulation/addressLocation/plants/{pl}/modules/parameter/id/value/{mod}", corpo)
    return True


# ---------------------------------------------------------------------------------------------------------------------
# 5. APRIRE LE APP DEL TELEFONO
# ---------------------------------------------------------------------------------------------------------------------
def dm_link_app(chiave):
    nome, pkg = DM_APP.get(chiave, ("", ""))
    if not pkg:
        return ""
    store = "https://play.google.com/store/apps/details?id=" + pkg
    return ("intent:#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;package=" + pkg
            + ";S.browser_fallback_url=" + _dm_up.quote(store, safe="") + ";end")


def dm_pulsante_app(chiave, k):
    url = dm_link_app(chiave)
    if url:
        nome = DM_APP[chiave][0]
        st.markdown(f"<a class='dm-app' href='{_dm_h.escape(url)}' target='_self'>▶ Apri «{_dm_h.escape(nome)}»</a>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------------------------------------------------
# 6. INTERFACCIA
# ---------------------------------------------------------------------------------------------------------------------
_DM_CSS = """<style>
.dm-kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:6px 0 10px}.dm-k{border-radius:14px;padding:8px;text-align:center;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15)}
.dm-k b{display:block;font-size:1.5rem}.dm-k span{font-size:.78rem;opacity:.85}
.dm-card{border-radius:16px;padding:10px 12px;margin:6px 0;background:rgba(255,255,255,.95);color:#10243a;border-left:6px solid #2f7de1}
.dm-card .t{font-weight:900;font-size:1.03rem}.dm-card .m{font-size:.84rem;color:#3c5269}.dm-on{color:#0a8f4a;font-weight:800}.dm-off{color:#b3261e;font-weight:800}
.dm-stanza{border-radius:16px;padding:10px;margin:4px 0;background:linear-gradient(135deg,#123a63,#1d5fa0);color:#fff}
.dm-stanza b{font-size:1.05rem}.dm-stanza .ic{font-size:1.3rem;letter-spacing:2px}
a.dm-app{display:block;text-align:center;padding:10px;border-radius:14px;background:#1d5fa0;color:#fff !important;font-weight:800;text-decoration:none;margin:4px 0}
.dm-big{font-size:2.6rem;font-weight:900;line-height:1}
</style>"""


def _dm_icona(x):
    return DM_CATEGORIE.get(x.get("categoria") or "altro", "📦").split(" ")[0]


def _dm_esito(fn, testo_ok):
    """Esegue un comando vero e dice com'è andata (✅ o l'errore del produttore)."""
    try:
        fn()
        st.toast("✅ " + testo_ok)
        return True
    except DmErrore as e:
        st.error("❌ " + str(e))
    except Exception as e:
        st.error(f"❌ Il comando non è arrivato ({type(e).__name__}: {str(e)[:120]}).")
    return False


def _dm_valore_leggibile(fn, v):
    if fn.get("type") == "Integer" and isinstance(v, (int, float)):
        sc = int((fn.get("values") or {}).get("scale") or 0)
        u = (fn.get("values") or {}).get("unit") or ""
        return f"{v / (10 ** sc):g} {u}".strip()
    if isinstance(v, bool):
        return "sì" if v else "no"
    return DM_ENUM_IT.get(str(v), str(v))


def _dm_controlli_tuya(x, k):
    """Solo i comandi che il cloud dichiara per QUESTO apparecchio (funzioni Tuya), con il valore di adesso."""
    try:
        funz = dm_tuya_funzioni(x["ext_id"])
        stato = dm_tuya_stato(x["ext_id"])
    except Exception as e:
        st.error("❌ Non riesco a leggere l'apparecchio: " + str(e))
        return
    if not funz:
        st.info("Il produttore non dà comandi per questo apparecchio tramite il cloud: usa «Apri nell'app».")
    sensibile = x.get("categoria") in DM_SENSIBILI
    if sensibile:
        ok = st.checkbox("🔐 Confermo: voglio comandare un dispositivo di sicurezza", key=k + "_conf")
        if not ok:
            st.caption("Per sicurezza i comandi di serrature e allarmi si sbloccano solo con la conferma qui sopra.")
            return
    for fn in funz:
        cod, tipo, val = fn["code"], fn["type"], fn.get("values") or {}
        nome = DM_CODICI_IT.get(cod, fn.get("name") or cod)
        attuale = stato.get(cod)
        kk = f"{k}_{cod}"
        if tipo == "Boolean":
            c1, c2 = st.columns([3, 2], gap="small")
            c1.markdown(f"**{nome}**: " + ("<span class='dm-on'>ACCESO</span>" if attuale else "<span class='dm-off'>SPENTO</span>" if attuale is not None else "?"),
                        unsafe_allow_html=True)
            if c2.button("Spegni" if attuale else "Accendi", key=kk, type="primary", width="stretch"):
                if _dm_esito(lambda: dm_tuya_comando(x["ext_id"], cod, not bool(attuale)), f"{x.get('nome')}: {nome.lower()} {'spento' if attuale else 'acceso'}"):
                    _dm_log(f"{x.get('nome')}: {nome} → {'no' if attuale else 'sì'}")
                    _dm_rr()
        elif tipo == "Integer":
            sc = int(val.get("scale") or 0)
            mn, mx, passo = val.get("min", 0), val.get("max", 100), val.get("step", 1) or 1
            div = 10 ** sc
            ora = (attuale if isinstance(attuale, (int, float)) else mn) / div
            nuovo = st.slider(f"{nome} ({val.get('unit') or ''})".replace(" ()", ""), float(mn) / div, float(mx) / div, float(min(max(ora, mn / div), mx / div)),
                              float(passo) / div, key=kk)
            if abs(nuovo - ora) > 1e-9 and st.button(f"✅ Imposta {nome.lower()} a {nuovo:g}", key=kk + "_ok", width="stretch"):
                v = int(round(nuovo * div))
                if _dm_esito(lambda: dm_tuya_comando(x["ext_id"], cod, v), f"{nome}: {nuovo:g}"):
                    _dm_log(f"{x.get('nome')}: {nome} → {nuovo:g}")
                    _dm_rr()
        elif tipo == "Enum":
            scelte = list(val.get("range") or [])
            if not scelte:
                continue
            i = scelte.index(attuale) if attuale in scelte else 0
            nuovo = st.selectbox(nome, scelte, index=i, format_func=lambda v: DM_ENUM_IT.get(str(v), str(v)), key=kk)
            if nuovo != attuale and st.button(f"✅ Imposta {nome.lower()}: {DM_ENUM_IT.get(str(nuovo), nuovo)}", key=kk + "_ok", width="stretch"):
                if _dm_esito(lambda: dm_tuya_comando(x["ext_id"], cod, nuovo), f"{nome}: {DM_ENUM_IT.get(str(nuovo), nuovo)}"):
                    _dm_log(f"{x.get('nome')}: {nome} → {nuovo}")
                    _dm_rr()
        elif tipo == "Json" and cod.startswith("colour_data"):
            v2 = cod.endswith("v2")
            colore = st.color_picker(nome, "#ffd27f", key=kk)
            if st.button("✅ Usa questo colore", key=kk + "_ok", width="stretch"):
                import colorsys
                r_, g_, b_ = (int(colore[i:i + 2], 16) / 255 for i in (1, 3, 5))
                h_, s_, v_ = colorsys.rgb_to_hsv(r_, g_, b_)
                dato = {"h": int(h_ * 360), "s": int(s_ * (1000 if v2 else 255)), "v": int(max(v_, .1) * (1000 if v2 else 255))}
                if _dm_esito(lambda: dm_tuya_comando(x["ext_id"], cod, dato), f"{x.get('nome')}: colore cambiato"):
                    _dm_log(f"{x.get('nome')}: colore {colore}")
                    _dm_rr()
    letti = [(c, v) for c, v in stato.items() if c not in {fn["code"] for fn in funz}]
    if letti:
        st.caption("📟 Letture: " + " · ".join(f"{DM_CODICI_IT.get(c, c)}: {_dm_valore_leggibile({'type': 'Integer' if isinstance(v, (int, float)) and not isinstance(v, bool) else '', 'values': {}}, v)}"
                                             for c, v in letti[:10]))


def _dm_controlli_smarther(x, k):
    try:
        s = dm_sm_stato(x["ext_id"])
    except Exception as e:
        st.error("❌ Non riesco a leggere il termostato: " + str(e))
        return
    t, u, v = s.get("temperatura"), s.get("umidita"), s.get("voluta")
    st.markdown(f"<div class='dm-card'><div class='m'>In casa adesso</div><div class='dm-big'>{(f'{t:.1f}°' if t is not None else '—').replace('.', ',')}</div>"
                f"<div class='m'>💧 Umidità {f'{u:.0f}%' if u is not None else '—'} · 🎯 voluta {(f'{v:.1f}°' if v is not None else '—').replace('.', ',')}"
                f" · modo: <b>{ {'automatic': 'automatico', 'manual': 'manuale', 'boost': 'boost', 'off': 'spento', 'protection': 'antigelo'}.get(s.get('modo'), s.get('modo') or '?') }</b>"
                f"{' · 🔥 caldaia accesa' if s.get('acceso') else ''}</div></div>", unsafe_allow_html=True)
    if s.get("fino") and s.get("modo") in ("manual", "boost"):
        st.caption(f"⏱️ {'Boost' if s.get('modo') == 'boost' else 'Manuale'} fino alle {s['fino']}, poi torna al programma automatico.")
    modo = st.radio("Cosa vuoi fare?", ["🎯 Temperatura a mano", "🚀 Boost", "🅰️ Programma automatico", "❄️ Antigelo", "⏻ Spegni"], horizontal=True, key=k + "_modo")
    if modo.startswith("🎯"):
        _dm_manuale_smarther(x, k, v)
    elif modo.startswith("🅰️"):
        progs = dm_sm_programmi(x["ext_id"])
        attuale = s.get("programma")
        if progs:
            nums = [n for n, _ in progs]
            prog = st.radio("Quale programma settimanale", nums, index=nums.index(attuale) if attuale in nums else 0,
                            format_func=lambda n: next(f"{nome_} (n. {n})" for n_, nome_ in progs if n_ == n) + (" · in uso" if n == attuale else ""), key=k + "_p")
        else:
            prog = st.number_input("Numero del programma (come nell'app Termostato)", 0, 10, int(attuale or 1), key=k + "_p")
        st.caption("📅 Gli orari di ogni giorno (a che ora accendere e a quanti gradi) sono scritti dentro il programma. "
                   "Legrand permette alle altre app solo di sceglierlo, non di cambiarne gli orari: quelli si modificano nell'app Termostato.")
        dm_pulsante_app("bticino", k + "_app")
        if st.button("✅ Usa questo programma", key=k + "_ok2", type="primary", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "automatic", programma=prog), "Termostato in automatico"):
                _dm_log(f"{x.get('nome')}: automatico (programma {prog})"); _dm_rr()
    elif modo.startswith("🚀"):
        st.caption("Il boost accende il riscaldamento al massimo per il tempo scelto, poi torna da solo al programma automatico (come il tasto ▶ dell'app Termostato).")
        mi = st.radio("Per", [30, 60, 90], format_func=lambda m: f"{m} minuti", horizontal=True, key=k + "_b")
        if st.button(f"🚀 Avvia il boost per {mi} minuti", key=k + "_ok3", type="primary", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "boost", minuti=mi), f"Boost per {mi} minuti"):
                _dm_log(f"{x.get('nome')}: boost {mi} min"); _dm_rr()
        if s.get("modo") == "boost" and st.button("⏹ Ferma il boost (torna in automatico)", key=k + "_stopb", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "automatic", programma=s.get("programma")), "Boost fermato"):
                _dm_log(f"{x.get('nome')}: boost fermato"); _dm_rr()
    elif modo.startswith("❄️"):
        if st.button("✅ Metti in antigelo", key=k + "_ok4", type="primary", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "protection"), "Termostato in antigelo"):
                _dm_log(f"{x.get('nome')}: antigelo"); _dm_rr()
    else:
        if st.button("✅ Spegni il riscaldamento", key=k + "_ok5", type="primary", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "off"), "Termostato spento"):
                _dm_log(f"{x.get('nome')}: spento"); _dm_rr()


def _dm_manuale_smarther(x, k, v):
    """Come «Modalità manuale» dell'app Termostato: temperatura + «Fino a» (per sempre, per qualche ora, fino a un orario)."""
    import datetime as _dt
    nuova = st.number_input("🌡️ Imposta temperatura (°C)", min_value=3.0, max_value=40.0, value=float(v if v is not None else 20.0), step=0.5, format="%.1f", key=k + "_t")
    g_ = f"{nuova:g}".replace(".", ",")
    fino_a = st.radio("Fino a", ["♾️ Per sempre", "⏱️ Per qualche ora", "🕘 Fino a un orario"], horizontal=True, key=k + "_fa")
    durata, fino, ok = None, None, True
    if fino_a.startswith("⏱️"):
        durata = st.select_slider("Per quanto tempo", [30, 60, 90, 120, 180, 240, 360, 480, 720],
                                  value=120, format_func=lambda m: f"{m} minuti" if m < 60 else (f"{m // 60} ore" + (" e mezza" if m % 60 else "")).replace("1 ore", "1 ora"), key=k + "_dur")
    elif fino_a.startswith("🕘"):
        ora_ = adesso()
        c1, c2 = st.columns(2, gap="small")
        orario = c2.time_input("Orario", value=_dt.time((ora_.hour + 2) % 24, 0), step=_dt.timedelta(minutes=15), key=k + "_ora")
        giorno_def = ora_.date() if orario > ora_.time() else ora_.date() + _dt.timedelta(days=1)
        giorno = c1.date_input("Giorno", value=giorno_def, min_value=ora_.date(), max_value=ora_.date() + _dt.timedelta(days=60), format="DD/MM/YYYY", key=k + "_gio")
        fino = _dt.datetime.combine(giorno, orario)
        if fino <= ora_:
            st.warning("⚠️ L'orario scelto è già passato: scegli un orario più avanti o il giorno dopo.")
            ok = False
        else:
            quando = "oggi" if giorno == ora_.date() else ("domani" if giorno == ora_.date() + _dt.timedelta(days=1) else giorno.strftime("%d/%m"))
            st.caption(f"Resterà a {g_}° fino a {quando} alle {orario.strftime('%H:%M')}, poi tornerà al programma automatico.")
    if st.button(f"✅ Imposta {g_}°", key=k + "_ok1", type="primary", width="stretch", disabled=not ok):
        dove = " per sempre" if not durata and not fino else (f" fino alle {fino.strftime('%H:%M')}" if fino else f" per {durata} minuti")
        if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "manual", nuova, durata, fino=fino), f"Termostato a {g_}°{dove}"):
            _dm_log(f"{x.get('nome')}: manuale {nuova:g}°{dove}"); _dm_rr()


def _dm_rr():
    """Ridisegna solo la finestra (che resta aperta) dopo un comando."""
    try:
        st.rerun(scope="fragment")
    except Exception as e:
        if type(e).__name__ in ("RerunException", "StopException"):
            raise
        st.rerun()


def _dm_log(testo):
    try:
        _dm_salva(lambda dm: dm_registra(dm, testo), "comando")
    except Exception:
        pass


@st.dialog("🎛️ Apparecchio", width="large")
def dm_scheda(did, casa_id=""):
    dm = _dm_leggi()
    x = next((y for y in dm["dispositivi"] if y["id"] == did), None)
    if not x:
        st.warning("Apparecchio non trovato.")
        return
    st.markdown(f"### {_dm_icona(x)} {_dm_h.escape(x.get('nome') or '')}")
    st.caption(" · ".join(p for p in (dm_nome_stanza(dm, x.get("stanza_id"), casa_id), DM_CATEGORIE.get(x.get("categoria"), ""), x.get("marca"), x.get("modello")) if p))
    t1, t2, t3 = st.tabs(["🎮 Controlli", "📋 Scheda", "🕑 Storico"])
    with t1:
        if x.get("piattaforma") == "tuya":
            _dm_controlli_tuya(x, "dmc_" + did)
        elif x.get("piattaforma") == "smarther":
            _dm_controlli_smarther(x, "dms_" + did)
        else:
            st.info("Questo apparecchio non è collegato a un cloud che VitaMemo può comandare: il comando si dà nella sua app.")
        if x.get("app"):
            dm_pulsante_app(x["app"], "dma_" + did)
    with t2:
        stanze = dm_stanze(dm, casa_id)
        ids = [s["id"] for s in stanze]
        nome = st.text_input("Nome", value=x.get("nome", ""), key="dmf_n_" + did)
        stanza = st.selectbox("Stanza", ids, index=ids.index(x["stanza_id"]) if x.get("stanza_id") in ids else 0,
                              format_func=lambda i: dm_nome_stanza(dm, i, casa_id), key="dmf_s_" + did)
        cats = list(DM_CATEGORIE)
        cat = st.selectbox("Tipo", cats, index=cats.index(x.get("categoria")) if x.get("categoria") in cats else len(cats) - 1, format_func=DM_CATEGORIE.get, key="dmf_c_" + did)
        c1, c2 = st.columns(2, gap="small")
        marca = c1.text_input("Marca", value=x.get("marca", ""), key="dmf_m_" + did)
        modello = c2.text_input("Modello", value=x.get("modello", ""), key="dmf_mo_" + did)
        apps = list(DM_APP)
        app = st.selectbox("App con cui si comanda", [""] + apps, index=([""] + apps).index(x.get("app")) if x.get("app") in apps else 0,
                           format_func=lambda a: "— nessuna —" if not a else DM_APP[a][0], key="dmf_a_" + did)
        inst = st.date_input("Data di installazione", value=_dm_data(x.get("installato_il")), format="DD/MM/YYYY", key="dmf_i_" + did)
        note = st.text_area("Note (descrizione, dove si trova il manuale…)", value=x.get("note", ""), key="dmf_no_" + did)
        st.caption(f"Collegamento: {({'tuya': '☁️ Tuya / Smart Life', 'smarther': '☁️ BTicino Smarther'}).get(x.get('piattaforma'), '📱 solo app')}"
                   + (f" · id {x['ext_id']}" if x.get("ext_id") else "") + f" · inserito il {str(x.get('creato_il', ''))[:10]}")
        if st.button("💾 Salva", key="dmf_ok_" + did, type="primary", width="stretch"):
            def _m(dm_):
                y = next((z for z in dm_["dispositivi"] if z["id"] == did), None)
                if y:
                    y.update(nome=nome.strip() or y.get("nome"), stanza_id=stanza, categoria=cat, marca=marca.strip(), modello=modello.strip(), app=app,
                             installato_il=inst.isoformat() if inst else "", note=note.strip(), casa_id=casa_id)
                    dm_registra(dm_, f"{y['nome']}: scheda modificata")
            _dm_salva(_m, "apparecchio modificato")
            st.rerun()
        if st.checkbox("🗑️ Voglio eliminare questo apparecchio da VitaMemo (nell'app del produttore resta)", key="dmf_d_" + did):
            if st.button("Elimina", key="dmf_del_" + did, width="stretch"):
                def _e(dm_):
                    dm_["dispositivi"] = [z for z in dm_["dispositivi"] if z["id"] != did]
                    dm_registra(dm_, f"{x.get('nome')}: eliminato")
                _dm_salva(_e, "apparecchio eliminato")
                st.rerun()
    with t3:
        righe = [r for r in reversed(dm.get("registro") or []) if str(r.get("testo", "")).startswith((x.get("nome") or "#") + ":")][:30]
        if not righe:
            st.caption("Nessun comando ancora.")
        for r in righe:
            st.markdown(f"- {str(r['il'])[:16].replace('T', ' ')} · {_dm_h.escape(r.get('chi') or '')}: {_dm_h.escape(r['testo'])}")


def _dm_data(iso):
    try:
        import datetime as _dt
        return _dt.date.fromisoformat(str(iso)[:10]) if iso else None
    except Exception:
        return None


def _dm_cerca_nuovi(dm, casa_id):
    """Chiede ai cloud collegati la lista degli apparecchi; ritorna (nuovi, errori)."""
    trovati, errori = [], []
    for nome, attivo, fn, piatt in (("Tuya / Smart Life", dm_tuya_conf() or dm_finto() is not None, dm_tuya_dispositivi, "tuya"),
                                    ("BTicino", dm_sm_collegato(), dm_sm_dispositivi, "smarther")):
        if not attivo:
            continue
        try:
            for t in fn():
                t["piattaforma"] = piatt
                trovati.append(t)
        except Exception as e:
            errori.append(str(e) if str(e).startswith(nome.split(" ")[0]) else f"{nome}: {e}")
    noti = {(y.get("piattaforma"), y.get("ext_id")) for y in dm["dispositivi"]}
    return [t for t in trovati if (t["piattaforma"], t["ext_id"]) not in noti], trovati, errori


def _dm_categoria_da(t):
    if t.get("piattaforma") == "smarther":
        return "termostato"
    return DM_TUYA_CAT.get(str(t.get("categoria_cloud") or "").lower(), "altro")


def _dm_pannello_nuovi(dm, casa_id):
    st.markdown("#### 🔎 Cerca apparecchi nei cloud collegati")
    if not (dm_tuya_conf() or dm_sm_collegato() or dm_finto() is not None):
        st.info("Nessun cloud collegato ancora: segui **🔗 Collegamenti** qui sotto. Intanto puoi aggiungere gli apparecchi a mano.")
        return
    if st.button("🔎 Cerca adesso", key="dm_cerca", type="primary", width="stretch"):
        with st.spinner("Chiedo ai cloud dei produttori…"):
            st.session_state["_dm_trovati"] = _dm_cerca_nuovi(dm, casa_id)
    ris = st.session_state.get("_dm_trovati")
    if not ris:
        return
    nuovi, tutti, errori = ris
    for e in errori:
        st.error("❌ " + e)
    st.caption(f"Trovati {len(tutti)} apparecchi · nuovi: {len(nuovi)} · offline: {sum(1 for t in tutti if not t.get('online'))}")
    if not nuovi:
        st.success("✅ Nessun apparecchio nuovo: sono già tutti in VitaMemo.")
    stanze = dm_stanze(dm, casa_id)
    ids = [s["id"] for s in stanze]
    manuali = [y for y in dm["dispositivi"] if y.get("piattaforma") == "app"]
    for i, t in enumerate(nuovi):
        with st.container(border=True):
            st.markdown(f"**{_dm_h.escape(t['nome'])}** · {_dm_h.escape(t.get('modello') or '')} · {t.get('app_cloud')}" + (" · 🟢 online" if t.get("online") else " · 🔴 offline"))
            st_ = st.selectbox("In quale stanza?", ids, index=None, placeholder="Scegli la stanza", format_func=lambda s: dm_nome_stanza(dm, s, casa_id), key=f"dmn_s_{i}")
            uguale = st.selectbox("È uno di quelli che avevi già inserito a mano?", [""] + [y["id"] for y in manuali],
                                  format_func=lambda j: "No, è nuovo" if not j else next(y["nome"] for y in manuali if y["id"] == j), key=f"dmn_u_{i}") if manuali else ""
            if st.button("✅ Conferma e aggiungi", key=f"dmn_ok_{i}", width="stretch"):
                if not st_:
                    st.warning("Scegli la stanza.")
                else:
                    def _m(dm_, t=t, st_=st_, uguale=uguale):
                        if uguale:
                            y = next((z for z in dm_["dispositivi"] if z["id"] == uguale), None)
                            if y:
                                y.update(piattaforma=t["piattaforma"], ext_id=t["ext_id"], stanza_id=st_, modello=y.get("modello") or t.get("modello", ""),
                                         categoria=y.get("categoria") if y.get("categoria") != "altro" else _dm_categoria_da(t))
                                dm_registra(dm_, f"{y['nome']}: collegato al cloud")
                                return
                        y, _n = dm_aggiungi_dispositivo(dm_, {"nome": t["nome"], "modello": t.get("modello", ""), "piattaforma": t["piattaforma"], "ext_id": t["ext_id"],
                                                             "categoria": _dm_categoria_da(t), "categoria_cloud": t.get("categoria_cloud", ""), "stanza_id": st_,
                                                             "casa_id": casa_id, "app": "smartlife" if t["piattaforma"] == "tuya" else "bticino"})
                        dm_registra(dm_, f"{y['nome']}: aggiunto")
                    _dm_salva(_m, "nuovo apparecchio dal cloud")
                    st.session_state["_dm_trovati"] = (nuovi[:i] + nuovi[i + 1:], tutti, errori)
                    st.rerun()


def _dm_aggiungi_a_mano(dm, casa_id):
    with st.expander("➕ Aggiungi un apparecchio a mano (con il pulsante per aprire la sua app)"):
        nome = st.text_input("Nome", key="dmm_n", placeholder="es. Google Home del soggiorno")
        stanze = dm_stanze(dm, casa_id)
        stanza = st.selectbox("Stanza", [s["id"] for s in stanze], format_func=lambda i: dm_nome_stanza(dm, i, casa_id), key="dmm_s")
        cat = st.selectbox("Tipo", list(DM_CATEGORIE), format_func=DM_CATEGORIE.get, key="dmm_c")
        c1, c2 = st.columns(2, gap="small")
        marca = c1.text_input("Marca", key="dmm_m")
        modello = c2.text_input("Modello", key="dmm_mo")
        app = st.selectbox("App con cui si comanda", list(DM_APP), format_func=lambda a: DM_APP[a][0], key="dmm_a")
        if st.button("💾 Aggiungi", key="dmm_ok", type="primary", width="stretch"):
            if not nome.strip():
                st.warning("Scrivi il nome.")
            else:
                _dm_salva(lambda dm_: dm_registra(dm_, dm_aggiungi_dispositivo(dm_, {"nome": nome.strip(), "stanza_id": stanza, "categoria": cat, "marca": marca.strip(),
                                                                                       "modello": modello.strip(), "app": app, "casa_id": casa_id})[0]["nome"] + ": aggiunto a mano"),
                          "apparecchio aggiunto")
                st.rerun()


def _dm_collegamenti():
    with st.expander("🔗 Collegamenti ai cloud (Tuya / Smart Life, BTicino)"):
        st.markdown("**☁️ Tuya / Smart Life** (climatizzatore, lampadine, prese…): " + ("✅ chiavi presenti" if dm_tuya_conf() else "❌ non ancora collegato"))
        if not dm_tuya_conf():
            st.caption("Servono le chiavi del progetto Tuya nei Secrets di Streamlit, sotto [tuya]: access_id, access_secret, region = \"eu\". Te le faccio creare passo passo.")
        st.markdown("**🌡️ BTicino Smarther** (termostato): " + ("✅ collegato" if dm_sm_collegato() else "🟠 chiavi presenti, manca l'accesso" if dm_sm_conf() else "❌ non ancora configurato"))
        if dm_sm_conf():
            st.caption("Prima di collegare: nell'app «Termostato» BTicino vai su **Account → Accesso di terze parti** (Third party access) e attivalo.")
            if st.button("🔗 Collega il termostato BTicino" if not dm_sm_collegato() else "🔄 Ricollega il termostato BTicino", key="dm_sm_coll",
                         type="primary", width="stretch"):
                st.session_state["_dm_sm_url"] = dm_sm_url_accesso()
            if st.session_state.get("_dm_sm_url"):
                st.link_button("➡️ Apri la pagina di accesso BTicino", st.session_state["_dm_sm_url"], width="stretch")
                st.caption("Entra con lo stesso account dell'app «Termostato» e tocca «Allow / Consenti»: tornerai qui da solo.")
        elif not dm_sm_conf():
            st.caption("Servono le chiavi Legrand nei Secrets, sotto [smarther]: subscription_key, client_id, client_secret, redirect_uri.")
        if dm_sm_conf() and st.button("🧪 Prova il collegamento BTicino (passo per passo)", key="dm_sm_diag", width="stretch"):
            with st.spinner("Provo il collegamento…"):
                for ico, cosa, dett in dm_sm_diagnosi():
                    st.markdown(f"{ico} **{cosa}** — {_dm_h.escape(str(dett))}")
        st.markdown("**🔊 Google Home, Alexa e le altre app**: si aprono con il pulsante «▶ Apri» (non danno comandi alle app esterne).")


def dm_tab(c=None, casa_id=None):
    """La scheda 🎛️ Domotica dentro Casa."""
    st.markdown(_DM_CSS, unsafe_allow_html=True)
    casa_id = casa_id if casa_id is not None else (st.session_state.get("ca_casa_sel") or "")
    if casa_id == "__vuota__":
        casa_id = ""
    dm = _dm_leggi()
    disp = [x for x in dm["dispositivi"] if (x.get("casa_id") or "") == casa_id]
    st.markdown("#### 🎛️ La centrale della casa")
    collegati = [x for x in disp if x.get("piattaforma") in ("tuya", "smarther")]
    st.markdown(f"<div class='dm-kpi'><div class='dm-k'><b>{len(disp)}</b><span>apparecchi</span></div>"
                f"<div class='dm-k'><b>{len(collegati)}</b><span>comandabili da qui</span></div>"
                f"<div class='dm-k'><b>{len(disp) - len(collegati)}</b><span>con la loro app</span></div></div>", unsafe_allow_html=True)
    vista = st.radio("Vedi", ["🎛️ Telecomando", "🗺️ Elenco per stanza", "🗂️ Per tipo", "🎬 Scenari"], horizontal=True, key="dm_vista", label_visibility="collapsed")
    if vista.startswith("🎛️"):
        _dm_telecomando(dm, casa_id, disp)
        _dm_pannello_nuovi(dm, casa_id)
        _dm_aggiungi_a_mano(dm, casa_id)
        _dm_stanze_ui(dm, casa_id)
        _dm_collegamenti()
        return
    cerca = st.text_input("🔎 Cerca", key="dm_cerca_t", placeholder="nome, marca, stanza…")
    if cerca:
        parole = cerca.lower().split()
        disp = [x for x in disp if all(p in " ".join(str(x.get(k) or "") for k in ("nome", "marca", "modello", "note")).lower() + " " + dm_nome_stanza(dm, x.get("stanza_id"), casa_id).lower()
                                       for p in parole)]
    if vista.startswith("🎬"):
        _dm_scenari(dm, casa_id, [x for x in dm["dispositivi"] if (x.get("casa_id") or "") == casa_id])
    else:
        if vista.startswith("🗺️"):
            gruppi = [(dm_nome_stanza(dm, s["id"], casa_id), [x for x in disp if x.get("stanza_id") == s["id"]]) for s in dm_stanze(dm, casa_id)]
            gruppi.append(("❔ Stanza da scegliere", [x for x in disp if x.get("stanza_id") not in {s["id"] for s in dm_stanze(dm, casa_id)}]))
        else:
            gruppi = [(DM_CATEGORIE[k], [x for x in disp if (x.get("categoria") or "altro") == k]) for k in DM_CATEGORIE]
        vuoti = True
        for titolo, xs in gruppi:
            if not xs:
                continue
            vuoti = False
            st.markdown(f"<div class='dm-stanza'><b>{_dm_h.escape(titolo)}</b> · {len(xs)} <span class='ic'>{''.join(_dm_icona(x) for x in xs[:8])}</span></div>", unsafe_allow_html=True)
            for x in xs:
                via = {"tuya": "☁️ si comanda da qui", "smarther": "☁️ si comanda da qui"}.get(x.get("piattaforma"), "📱 con la sua app")
                c1, c2 = st.columns([3, 2], gap="small")
                c1.markdown(f"<div class='dm-card'><div class='t'>{_dm_icona(x)} {_dm_h.escape(x.get('nome') or '')}</div><div class='m'>"
                            + _dm_h.escape(" · ".join(p for p in (x.get("marca"), x.get("modello")) if p)) + f"<br>{via}</div></div>", unsafe_allow_html=True)
                if c2.button("🎮 Apri", key="dm_o_" + x["id"], width="stretch", type="primary" if x.get("piattaforma") != "app" else "secondary"):
                    dm_scheda(x["id"], casa_id)
                if x.get("app") and x.get("piattaforma") == "app":
                    with c2:
                        dm_pulsante_app(x["app"], "dml_" + x["id"])
        if vuoti:
            st.info("Ancora nessun apparecchio in questa casa. Cercali nei cloud collegati o aggiungili a mano qui sotto.")
    _dm_pannello_nuovi(dm, casa_id)
    _dm_aggiungi_a_mano(dm, casa_id)
    _dm_stanze_ui(dm, casa_id)
    _dm_collegamenti()


# ---------------------------------------------------------------------------------------------------------------------
# 6-bis. IL TELECOMANDO (richiesta del 23 novembre 2026): un tasto per stanza; toccandolo si apre la stanza con i suoi apparecchi
#        e i comandi rapidi (acceso/spento, temperatura ±); «🎮 Tutti i comandi» apre la scheda completa.
# ---------------------------------------------------------------------------------------------------------------------
_DM_CSS_TELE = """<style>
.st-key-dm_tele [data-testid='stHorizontalBlock']{gap:10px !important}
.st-key-dm_tele button{min-height:96px !important;border-radius:22px !important;background:linear-gradient(145deg,#12355c,#1f6fb8) !important;
 border:2px solid #6fb3ff !important;box-shadow:0 0 14px rgba(80,160,255,.35) !important;white-space:pre-line !important}
.st-key-dm_tele button p{color:#fff !important;font-weight:900 !important;font-size:1.05rem !important;line-height:1.25 !important;white-space:pre-line !important}
.st-key-dm_tele button:disabled{opacity:.45 !important}
.dm-rc{border-radius:18px;padding:10px 12px;margin:8px 0 4px;background:rgba(255,255,255,.96);color:#10243a;border-left:6px solid #2f7de1}
.dm-rc .t{font-weight:900;font-size:1.05rem}.dm-rc .s{font-size:.9rem;color:#3c5269}.dm-rc .big{font-size:2rem;font-weight:900;line-height:1.05}
</style>"""
_DM_INTERRUTTORI = ("switch_led", "switch", "switch_1")


@st.cache_data(ttl=3600, show_spinner=False)
def _dm_funzioni_cache(dev_id, _finto_firma=""):
    return dm_tuya_funzioni(dev_id)


def _dm_rapido_tuya(x, k):
    """Comandi rapidi Tuya: interruttore principale e, se c'è, temperatura voluta − / +."""
    try:
        funz = _dm_funzioni_cache(x["ext_id"], str(bool(dm_finto())))
        stato = dm_tuya_stato(x["ext_id"])
    except Exception as e:
        st.caption("❌ " + str(e)[:160])
        return
    codici = {f["code"]: f for f in funz}
    inter = next((c for c in _DM_INTERRUTTORI if c in codici), None)
    acceso = stato.get(inter) if inter else None
    righe = []
    if inter:
        righe.append("🟢 ACCESO" if acceso else "⚫ SPENTO")
    if "temp_current" in stato:
        sc = int(((codici.get("temp_current") or {}).get("values") or {}).get("scale") or 0)
        righe.append(f"🌡️ {stato['temp_current'] / (10 ** sc):g}°")
    if "temp_set" in stato:
        sc = int((codici.get("temp_set") or {}).get("values", {}).get("scale") or 0)
        righe.append(f"🎯 {stato['temp_set'] / (10 ** sc):g}°")
    if "mode" in stato:
        righe.append(DM_ENUM_IT.get(str(stato["mode"]), str(stato["mode"])))
    if righe:
        st.caption(" · ".join(righe))
    if x.get("categoria") in DM_SENSIBILI:
        st.caption("🔐 Dispositivo di sicurezza: comandalo da «🎮 Tutti i comandi» (chiede conferma).")
        return
    cols = st.columns(3 if "temp_set" in codici else 1, gap="small")
    if inter and cols[0].button("⏻ Spegni" if acceso else "⏻ Accendi", key=k + "_on", type="primary", width="stretch"):
        if _dm_esito(lambda: dm_tuya_comando(x["ext_id"], inter, not bool(acceso)), f"{x.get('nome')}: {'spento' if acceso else 'acceso'}"):
            _dm_log(f"{x.get('nome')}: {DM_CODICI_IT.get(inter, inter)} → {'no' if acceso else 'sì'}")
            st.rerun()
    if "temp_set" in codici and isinstance(stato.get("temp_set"), (int, float)):
        v = codici["temp_set"].get("values") or {}
        passo = int(v.get("step") or 1)
        for i_, (et, d) in enumerate((("➖", -passo), ("➕", passo)), start=1):
            nuovo = max(int(v.get("min", stato["temp_set"])), min(int(v.get("max", stato["temp_set"])), int(stato["temp_set"]) + d))
            if cols[i_].button(et, key=f"{k}_t{i_}", width="stretch", disabled=nuovo == stato["temp_set"]):
                if _dm_esito(lambda n=nuovo: dm_tuya_comando(x["ext_id"], "temp_set", n), f"{x.get('nome')}: temperatura voluta cambiata"):
                    _dm_log(f"{x.get('nome')}: Temperatura voluta → {nuovo}")
                    st.rerun()


def _dm_rapido_smarther(x, k):
    """Comandi rapidi del termostato: temperatura di casa, voluta, − / + mezzo grado, automatico."""
    try:
        s_ = dm_sm_stato(x["ext_id"])
    except Exception as e:
        st.caption("❌ " + str(e)[:160])
        return
    t, v = s_.get("temperatura"), s_.get("voluta")
    modi = {"automatic": "🅰️ automatico", "manual": "✋ manuale", "boost": "🚀 boost", "off": "⏻ spento", "protection": "❄️ antigelo"}
    st.markdown(f"<div class='dm-rc'><span class='big'>{(f'{t:.1f}°' if t is not None else '—').replace('.', ',')}</span> "
                f"<span class='s'>in casa · 🎯 voluta {(f'{v:.1f}°' if v is not None else '—').replace('.', ',')}"
                f" · {modi.get(s_.get('modo'), s_.get('modo') or '')}{(' fino alle ' + s_['fino']) if s_.get('fino') and s_.get('modo') in ('manual', 'boost') else ''}"
                f"{' · 🔥 acceso' if s_.get('acceso') else ''}"
                f"{(' · 💧 ' + format(s_['umidita'], '.0f') + '%') if s_.get('umidita') is not None else ''}</span></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    base = v if v is not None else 20.0
    for col, et, d in ((c1, "➖ 0,5°", -0.5), (c2, "➕ 0,5°", 0.5)):
        if col.button(et, key=f"{k}_{d}", width="stretch"):
            n = max(5.0, min(30.0, base + d))
            if _dm_esito(lambda n=n: dm_sm_imposta(x["ext_id"], "manual", n), f"Termostato a {n:g}°".replace(".", ",")):
                _dm_log(f"{x.get('nome')}: manuale {n:g}°")
                st.rerun()
    if c3.button("🅰️ Auto", key=k + "_auto", width="stretch", disabled=s_.get("modo") == "automatic"):
        if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "automatic", programma=s_.get("programma")), "Termostato in automatico"):
            _dm_log(f"{x.get('nome')}: automatico")
            st.rerun()
    st.caption("🚀 Boost: riscaldamento al massimo, poi torna da solo in automatico")
    b1, b2, b3 = st.columns(3, gap="small")
    for col, mi in ((b1, 30), (b2, 60), (b3, 90)):
        if col.button(f"🚀 {mi}′", key=f"{k}_b{mi}", width="stretch"):
            if _dm_esito(lambda mi=mi: dm_sm_imposta(x["ext_id"], "boost", minuti=mi), f"{x.get('nome')}: boost per {mi} minuti"):
                _dm_log(f"{x.get('nome')}: boost {mi} min")
                st.rerun()
    if s_.get("modo") == "boost":
        if st.button("⏹ Ferma il boost", key=k + "_stopb", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "automatic", programma=s_.get("programma")), "Boost fermato"):
                _dm_log(f"{x.get('nome')}: boost fermato")
                st.rerun()
    elif s_.get("modo") != "off":
        if st.button("⏻ Spegni", key=k + "_off", width="stretch"):
            if _dm_esito(lambda: dm_sm_imposta(x["ext_id"], "off"), f"{x.get('nome')}: spento"):
                _dm_log(f"{x.get('nome')}: spento")
                st.rerun()
    st.caption("🕘 Temperatura fino a un orario e programmi: tocca «🎮 Tutti i comandi e la scheda».")


def _dm_telecomando(dm, casa_id, disp):
    st.markdown(_DM_CSS_TELE, unsafe_allow_html=True)
    stanze = dm_stanze(dm, casa_id)
    ids_st = {s_["id"] for s_ in stanze}
    aperta = st.session_state.get("dm_stanza_aperta")
    senza = [x for x in disp if x.get("stanza_id") not in ids_st]
    if aperta and aperta not in ids_st | {"__senza__"}:
        aperta = None
    if not aperta:
        st.caption("Tocca una stanza per aprirla e comandare i suoi apparecchi.")
        tasti = [(s_["id"], s_.get("icona", "🏠"), s_["nome"], [x for x in disp if x.get("stanza_id") == s_["id"]]) for s_ in stanze]
        if senza:
            tasti.append(("__senza__", "❔", "Da sistemare", senza))
        with st.container(key="dm_tele"):
            for i in range(0, len(tasti), 2):
                cols = st.columns(2, gap="small")
                for col, (sid, ico, nome, xs) in zip(cols, tasti[i:i + 2]):
                    sotto = (f"{len(xs)} apparecch{'io' if len(xs) == 1 else 'i'} " + "".join(_dm_icona(x) for x in xs[:4])) if xs else "vuota"
                    if col.button(f"{ico} {nome}\n{sotto}", key="dm_st_" + sid.replace(":", "_"), width="stretch"):
                        st.session_state["dm_stanza_aperta"] = sid
                        st.rerun()
        return
    nome = "❔ Da sistemare" if aperta == "__senza__" else dm_nome_stanza(dm, aperta, casa_id)
    if st.button("← Tutte le stanze", key="dm_st_back", width="stretch"):
        st.session_state.pop("dm_stanza_aperta", None)
        st.rerun()
    st.markdown(f"### {_dm_h.escape(nome)}")
    xs = senza if aperta == "__senza__" else [x for x in disp if x.get("stanza_id") == aperta]
    if not xs:
        st.info("Nessun apparecchio in questa stanza. Spostane uno qui sotto, oppure cercali nei cloud o aggiungili a mano.")
    for x in xs:
        with st.container(border=True):
            st.markdown(f"**{_dm_icona(x)} {_dm_h.escape(x.get('nome') or '')}**" + (f" · {_dm_h.escape(x.get('marca') or '')}" if x.get("marca") else ""))
            if x.get("piattaforma") == "tuya":
                _dm_rapido_tuya(x, "dmr_" + x["id"])
            elif x.get("piattaforma") == "smarther":
                _dm_rapido_smarther(x, "dmr_" + x["id"])
            elif x.get("app"):
                dm_pulsante_app(x["app"], "dmra_" + x["id"])
            if st.button("🎮 Tutti i comandi e la scheda", key="dm_full_" + x["id"], width="stretch"):
                dm_scheda(x["id"], casa_id)
    altri = [x for x in disp if x.get("stanza_id") != aperta]
    if altri and aperta != "__senza__":
        with st.expander(f"➕ Metti un apparecchio in {nome}"):
            scelto = st.selectbox("Quale apparecchio", [x["id"] for x in altri], index=None, placeholder="Scegli…",
                                  format_func=lambda i: next(f"{_dm_icona(x)} {x.get('nome')} ({dm_nome_stanza(dm, x.get('stanza_id'), casa_id)})" for x in altri if x["id"] == i),
                                  key="dm_sposta_" + aperta)
            if scelto and st.button("✅ Spostalo qui", key="dm_sposta_ok_" + aperta, width="stretch"):
                def _m(dm_, i=scelto, sid=aperta):
                    y = next((z for z in dm_["dispositivi"] if z["id"] == i), None)
                    if y:
                        y["stanza_id"] = sid
                        dm_registra(dm_, f"{y['nome']}: spostato in {nome}")
                _dm_salva(_m, "apparecchio spostato")
                st.rerun()


def _dm_stanze_ui(dm, casa_id):
    with st.expander("🚪 Stanze: aggiungi o nascondi"):
        nuova = st.text_input("Nuova stanza", key="dms_n", placeholder="es. Cameretta, Taverna, Balcone")
        icona = st.selectbox("Icona", ["🏠", "🧸", "🍷", "🌿", "💻", "🧺", "🎮", "🛏️", "🛋️"], key="dms_i")
        if st.button("➕ Aggiungi la stanza", key="dms_ok", width="stretch") and nuova.strip():
            _dm_salva(lambda dm_: dm_["stanze"].append({"id": _dm_id(), "nome": nuova.strip(), "icona": icona, "casa_id": casa_id}), "stanza aggiunta")
            st.rerun()
        base_vis = [s["nome"] for s in dm_stanze(dm, casa_id) if s["id"].startswith("b:")]
        nasc = st.multiselect("Stanze predefinite che non ti servono", DM_STANZE_BASE, default=[n for n in DM_STANZE_BASE if n not in base_vis], key="dms_h")
        if set(nasc) != {n for n in DM_STANZE_BASE if n not in base_vis} and st.button("💾 Salva le stanze nascoste", key="dms_hok", width="stretch"):
            def _m(dm_):
                dm_["stanze"] = [s for s in dm_["stanze"] if not (s.get("nascosta") and (s.get("casa_id") or "") == casa_id)]
                dm_["stanze"] += [{"id": "h:" + n, "nome": n, "nascosta": True, "casa_id": casa_id} for n in nasc]
            _dm_salva(_m, "stanze")
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 7. SCENARI (si avviano con un tocco; ogni azione è un comando vero, con l'esito una per una)
# ---------------------------------------------------------------------------------------------------------------------
DM_SCENARI_PRONTI = ["🚪 Esco di casa", "🌙 Buonanotte", "🏠 Rientro a casa", "🌿 Risparmio energetico"]


def dm_esegui_scenario(dm, sc):
    """Esegue le azioni una per una; ritorna [(testo, ok, errore)]."""
    out = []
    for a in sc.get("azioni") or []:
        x = next((y for y in dm["dispositivi"] if y["id"] == a.get("disp")), None)
        if not x:
            out.append(("apparecchio eliminato", False, "non c'è più"))
            continue
        try:
            if x.get("piattaforma") == "tuya":
                dm_tuya_comando(x["ext_id"], a["code"], a["value"])
            elif x.get("piattaforma") == "smarther":
                dm_sm_imposta(x["ext_id"], a["code"], a.get("value"))
            else:
                raise DmErrore("si comanda solo dalla sua app")
            out.append((f"{x.get('nome')}: {a.get('testo') or a['code']}", True, ""))
        except Exception as e:
            out.append((f"{x.get('nome')}: {a.get('testo') or a.get('code')}", False, str(e)))
    return out


def _dm_scenari(dm, casa_id, disp):
    scen = [s for s in dm.get("scenari") or [] if (s.get("casa_id") or "") == casa_id]
    comandabili = [x for x in disp if x.get("piattaforma") in ("tuya", "smarther")]
    for s in scen:
        with st.container(border=True):
            st.markdown(f"**{_dm_h.escape(s['nome'])}** · {len(s.get('azioni') or [])} azioni" + ("" if s.get("attivo", True) else " · ⏸️ disattivato"))
            st.caption(" · ".join(a.get("testo") or a.get("code") for a in s.get("azioni") or [])[:300])
            c1, c2 = st.columns(2, gap="small")
            if c1.button("▶ Avvia", key="dmsc_go_" + s["id"], type="primary", width="stretch", disabled=not s.get("attivo", True)):
                ris = dm_esegui_scenario(dm, s)
                for testo, ok, err in ris:
                    (st.success if ok else st.error)(("✅ " if ok else "❌ ") + testo + ("" if ok else f" — {err}"))
                _dm_log(f"Scenario {s['nome']}: {sum(1 for r in ris if r[1])}/{len(ris)} azioni riuscite")
            if c2.button("⏸️ Disattiva" if s.get("attivo", True) else "▶️ Riattiva", key="dmsc_on_" + s["id"], width="stretch"):
                def _t(dm_, sid=s["id"]):
                    y = next(z for z in dm_["scenari"] if z["id"] == sid)
                    y["attivo"] = not y.get("attivo", True)
                _dm_salva(_t, "scenario")
                st.rerun()
            if st.button("🗑️ Elimina lo scenario", key="dmsc_del_" + s["id"]):
                _dm_salva(lambda dm_, sid=s["id"]: dm_.__setitem__("scenari", [z for z in dm_["scenari"] if z["id"] != sid]), "scenario eliminato")
                st.rerun()
    with st.expander("➕ Crea uno scenario"):
        if not comandabili:
            st.info("Gli scenari usano gli apparecchi **comandabili da qui** (☁️): collega prima Tuya / Smart Life o il termostato BTicino.")
            return
        nome = st.selectbox("Nome", DM_SCENARI_PRONTI + ["✏️ Scrivo io"], key="dmsc_nome")
        if nome.startswith("✏️"):
            nome = st.text_input("Nome dello scenario", key="dmsc_nome_l")
        azioni = st.session_state.setdefault("_dm_sc_azioni", [])
        x_id = st.selectbox("Apparecchio", [x["id"] for x in comandabili], format_func=lambda i: next(x["nome"] for x in comandabili if x["id"] == i), key="dmsc_x")
        x = next(y for y in comandabili if y["id"] == x_id)
        if x["piattaforma"] == "smarther":
            m = st.selectbox("Cosa fa", ["off", "protection", "automatic", "manual"], format_func={"off": "⏻ Spegni", "protection": "❄️ Antigelo", "automatic": "🅰️ Automatico",
                                                                                                 "manual": "🎯 Temperatura"}.get, key="dmsc_m")
            val = st.slider("Temperatura", 5.0, 30.0, 18.0, 0.5, key="dmsc_v") if m == "manual" else None
            azione = {"disp": x_id, "code": m, "value": val, "testo": {"off": "termostato spento", "protection": "antigelo", "automatic": "automatico", "manual": f"{val:g}°" if val else ""}[m]}
        else:
            try:
                funz = [f for f in dm_tuya_funzioni(x["ext_id"]) if f["type"] in ("Boolean", "Enum", "Integer")]
            except Exception as e:
                st.error("❌ " + str(e))
                return
            if not funz:
                st.info("Questo apparecchio non ha comandi da usare negli scenari.")
                return
            fc = st.selectbox("Comando", [f["code"] for f in funz], format_func=lambda c: DM_CODICI_IT.get(c, c), key="dmsc_f")
            fn = next(f for f in funz if f["code"] == fc)
            if fn["type"] == "Boolean":
                val = st.radio("Valore", [True, False], format_func=lambda b: "Acceso" if b else "Spento", horizontal=True, key="dmsc_b")
                testo = f"{DM_CODICI_IT.get(fc, fc).lower()} {'sì' if val else 'no'}"
            elif fn["type"] == "Enum":
                val = st.selectbox("Valore", fn["values"].get("range") or [], format_func=lambda v: DM_ENUM_IT.get(str(v), str(v)), key="dmsc_e")
                testo = f"{DM_CODICI_IT.get(fc, fc).lower()}: {DM_ENUM_IT.get(str(val), val)}"
            else:
                vv, sc_ = fn["values"], int(fn["values"].get("scale") or 0)
                n = st.number_input("Valore", float(vv.get("min", 0)) / 10 ** sc_, float(vv.get("max", 100)) / 10 ** sc_, float(vv.get("min", 0)) / 10 ** sc_, key="dmsc_i")
                val, testo = int(round(n * 10 ** sc_)), f"{DM_CODICI_IT.get(fc, fc).lower()} {n:g}"
            azione = {"disp": x_id, "code": fc, "value": val, "testo": testo}
        if st.button("➕ Aggiungi questa azione", key="dmsc_add", width="stretch"):
            azioni.append(azione)
            st.rerun()
        for i, a in enumerate(azioni):
            st.markdown(f"{i + 1}. {_dm_h.escape(next((x['nome'] for x in comandabili if x['id'] == a['disp']), '?'))}: {_dm_h.escape(a['testo'])}")
        if azioni and st.button("💾 Salva lo scenario", key="dmsc_ok", type="primary", width="stretch") and nome:
            _dm_salva(lambda dm_: dm_["scenari"].append({"id": _dm_id(), "nome": nome, "azioni": list(azioni), "attivo": True, "casa_id": casa_id}), "scenario creato")
            st.session_state["_dm_sc_azioni"] = []
            st.rerun()
    st.caption("Gli scenari partono con un tocco. Quelli a orario (es. ogni sera alle 23) si fanno nell'app Smart Life / Termostato, che restano accese anche quando VitaMemo è chiusa.")


# ---------------------------------------------------------------------------------------------------------------------
# 8. AGGANCI: ritorno da BTicino, guida
# ---------------------------------------------------------------------------------------------------------------------
try:
    if str(st.query_params.get("state") or "").startswith("vmdm") and st.query_params.get("code"):
        dm_sm_ritorno()
except Exception as _e_dm:
    if type(_e_dm).__name__ in ("StopException", "RerunException"):
        raise

try:
    if "_GUIDE" in globals() and "_ID_GUIDA" in globals():
        _ids = _ID_GUIDA.setdefault("casa", [])
        if "x_domotica" not in _ids:
            _ids.append("x_domotica")
            _GUIDE.setdefault("casa", []).append((
                "🎛️ Domotica: comandare la casa",
                "In **🏠 Casa → 🎛️ Domotica** trovi gli apparecchi di casa divisi **per stanza** o **per tipo**.\n"
                "- **☁️ si comanda da qui**: apparecchi collegati al cloud del produttore (Tuya / Smart Life: climatizzatori, lampadine, prese…; BTicino: termostato). "
                "Tocca **🎮 Apri → Controlli**: compaiono SOLO i comandi che l'apparecchio ha davvero; ogni comando risponde ✅ o con l'errore.\n"
                "- **📱 con la sua app** (Google Home, Alexa…): il pulsante **▶ Apri** apre l'app giusta.\n"
                "- **🔎 Cerca adesso** chiede ai cloud collegati gli apparecchi nuovi: scegli la stanza e confermi (niente doppioni).\n"
                "- **🎬 Scenari**: «Esco di casa», «Buonanotte»… più comandi con un tocco.\n"
                "- **🔗 Collegamenti**: lo stato dei collegamenti Tuya e BTicino. Le chiavi stanno solo nei Secrets di Streamlit.\n"
                "Per sicurezza serrature e allarmi chiedono una conferma prima di ogni comando.",
                "domotica casa apparecchi stanza comandi luce lampadina climatizzatore termostato tuya smart life bticino google home scenari"))
except Exception:
    pass
