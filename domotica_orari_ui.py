"""📅 Orari del riscaldamento (fasce giornaliere) nella scheda del termostato BTicino.

Il motore è in domotica_orari_core.py (identico in dispensa-dati, dove l'«orologio» domotica_orari.py lo usa ad app chiusa).
Qui: modifica delle fasce per ogni giorno, copia su altri giorni, modelli pronti, temperatura fuori dalle fasce,
stima del risparmio, stato dell'orologio automatico, e applicazione immediata quando si apre l'app.
"""
import copy as _or_copy
import uuid as _or_uuid
import datetime as _or_dt

OR_FILE_STATO = "domotica/orari_stato.json"
OR_MODO_RADIO = "📅 Orari della settimana"


def _or_uid():
    try:
        return str(percorso_mio()).split("/")[-1][:-5] or "admin"
    except Exception:
        return "admin"


def _or_repo_dati():
    try:
        return str((segreto("github") or {}).get("repo") or "Leoitalyto/dispensa-dati")
    except Exception:
        return "Leoitalyto/dispensa-dati"


def or_leggi_stato(forza=False):
    cache = st.session_state.get("_or_stato_cache")
    if not forza and cache and cache[0] > _dm_time.time() - 60:
        return cache[1]
    try:
        s = crea_archivio().leggi(OR_FILE_STATO) or {}
    except Exception:
        s = {}
    st.session_state["_or_stato_cache"] = (_dm_time.time(), s)
    return s


def dm_orari_di(x, dm=None):
    dm = dm or _dm_leggi()
    return or_normalizza((dm.get("orari") or {}).get(x["id"]))


def dm_orari_applica(x, prog=None, forza=False):
    """Fa subito quello che farebbe l'orologio automatico (una volta per passaggio). Ritorna il testo dell'esito o None."""
    prog = or_normalizza(prog if prog is not None else dm_orari_di(x))
    ob = or_obiettivo(prog, adesso())
    if not ob:
        return None
    chiave_voce = f"{_or_uid()}|{x['id']}"
    prima = (or_leggi_stato(forza=True).get("voci") or {}).get(chiave_voce) or {}
    if not forza and prima.get("chiave") == ob["chiave"] and prima.get("esito") == "ok":
        return None
    try:
        s_ = dm_sm_stato(x["ext_id"])
        if ob["tipo"] == "programma":
            if s_.get("modo") == "manual" and str(prima.get("chiave") or "")[:2] in ("F|", "R|"):
                dm_sm_imposta(x["ext_id"], "automatic", programma=s_.get("programma"))
                testo = "rimesso il programma del termostato"
            else:
                testo = "programma del termostato (niente da fare)"
        else:
            dm_sm_imposta(x["ext_id"], "manual", ob["temp"], fino=ob["fino"])
            testo = f"impostato {ob['descr']}"
        esito = "ok"
    except Exception as e:
        testo, esito = str(e)[:200], "errore"
    ora = adesso().strftime("%Y-%m-%d %H:%M")

    def _f(d):
        d.setdefault("voci", {})[chiave_voce] = {"nome": x.get("nome") or "Termostato", "chiave": ob["chiave"] if esito == "ok" else prima.get("chiave"),
                                                 "esito": esito, "quando": ora, "testo": testo, "obiettivo": ob["descr"], "controllato": ora}
        d["storia"] = ([{"quando": ora, "nome": x.get("nome") or "Termostato", "testo": "📱 dall'app: " + testo, "esito": esito}] + (d.get("storia") or []))[:40]
    try:
        salva_file(OR_FILE_STATO, _f, "Domotica: orari riscaldamento (dall'app)")
    except Exception:
        pass
    st.session_state.pop("_or_stato_cache", None)
    if esito == "ok":
        _dm_log(f"{x.get('nome')}: orari → {testo}")
    return ("✅ " if esito == "ok" else "❌ ") + testo


def _or_riga_rapida(x):
    """Nel telecomando: cosa stanno facendo gli orari, e li applica se il passaggio non è ancora stato fatto."""
    prog = dm_orari_di(x)
    if not prog.get("attivo"):
        return
    ob = or_obiettivo(prog, adesso())
    pross = or_prossimo_cambio(prog, adesso())
    st.caption(f"📅 Orari di VitaMemo: adesso {ob['descr'] if ob else '—'}" + (f" · poi {pross[1]}" if pross else ""))
    if ob and st.session_state.get(f"_or_fatto_{x['id']}") != ob["chiave"]:
        st.session_state[f"_or_fatto_{x['id']}"] = ob["chiave"]
        esito = dm_orari_applica(x, prog)
        if esito:
            st.toast(esito)


def _or_bozza(x, k):
    bk = k + "_orb"
    if bk not in st.session_state:
        b = _or_copy.deepcopy(dm_orari_di(x))
        for g in b["giorni"].values():
            for f in g:
                f["id"] = _or_uuid.uuid4().hex[:8]
        st.session_state[bk] = b
    return st.session_state[bk]


def _or_pulito(b):
    out = _or_copy.deepcopy(b)
    for g, fasce in out["giorni"].items():
        out["giorni"][g] = sorted(({kk: vv for kk, vv in f.items() if kk != "id"} for f in fasce), key=lambda f: f["dalle"])
    return out


def _or_stato_auto(x, attivo):
    s = or_leggi_stato()
    giro = s.get("giro")
    voce = (s.get("voci") or {}).get(f"{_or_uid()}|{x['id']}") or {}
    vecchio = True
    if giro:
        try:
            vecchio = (adesso() - _or_dt.datetime.strptime(giro, "%Y-%m-%d %H:%M")).total_seconds() > 4 * 3600
        except Exception:
            vecchio = True
    if giro and not vecchio:
        st.success(f"🤖 Orologio automatico attivo · ultimo controllo {giro[11:]} del {giro[8:10]}/{giro[5:7]}"
                   + (f" · {voce.get('testo')}" if voce.get("testo") else ""))
    elif attivo:
        st.warning("🤖 L'orologio automatico non è ancora attivo" + (f" (ultimo controllo: {giro[8:10]}/{giro[5:7]} alle {giro[11:]})" if giro else "")
                   + ": per ora gli orari vengono applicati solo quando apri VitaMemo. Per farli funzionare anche ad app chiusa segui «⚙️ Attiva l'orologio automatico» qui sotto.")
    if voce.get("esito") == "errore":
        st.error("❌ Ultimo tentativo non riuscito: " + str(voce.get("testo") or ""))
    storia = [h for h in (s.get("storia") or []) if h.get("nome") == (x.get("nome") or "Termostato")][:10]
    if storia:
        with st.expander("🕑 Cosa hanno fatto gli orari"):
            for h in storia:
                st.markdown(f"- {'✅' if h.get('esito') == 'ok' else '❌'} {h['quando'][8:10]}/{h['quando'][5:7]} {h['quando'][11:]} — {_dm_h.escape(str(h.get('testo') or ''))}")


def _or_guida_orologio():
    repo = _or_repo_dati()
    with st.expander("⚙️ Attiva l'orologio automatico (una volta sola)"):
        st.markdown(
            "Serve perché gli orari funzionino **anche quando VitaMemo è chiusa**. Tutto gratuito, senza carta di credito.\n\n"
            f"1. **Le 3 chiavi del termostato su GitHub** → [apri questa pagina](https://github.com/{repo}/settings/secrets/actions/new) e crea "
            "tre «secret» con questi nomi, copiando i valori dai Secrets di Streamlit (gruppo `[smarther]`): "
            "`SMARTHER_SUBSCRIPTION_KEY`, `SMARTHER_CLIENT_ID`, `SMARTHER_CLIENT_SECRET`.\n"
            "2. **Un permesso per far partire l'orologio** → [crea il permesso](https://github.com/settings/personal-access-tokens/new): "
            f"solo il repository `{repo.split('/')[-1]}`, permesso **Actions: Read and write**.\n"
            "3. **La sveglia ogni mezz'ora** → [cron-job.org](https://console.cron-job.org/signup) (gratuito): un «cronjob» che ogni 30 minuti chiama\n"
            f"`https://api.github.com/repos/{repo}/actions/workflows/domotica_orari.yml/dispatches` con metodo **POST**, corpo `{{\"ref\":\"main\"}}` "
            "e le intestazioni `Authorization: Bearer <il permesso del punto 2>` e `Accept: application/vnd.github+json`.\n\n"
            "Quando funziona, qui sopra compare «🤖 Orologio automatico attivo». Claude ti guida passo passo.")


def dm_orari_ui(x, k):
    """La pagina «📅 Orari della settimana» del termostato."""
    b = _or_bozza(x, k)
    st.caption("Scegli le fasce di ogni giorno: in ogni fascia VitaMemo mette il termostato alla temperatura che vuoi, "
               "e alla fine della fascia il termostato torna da solo a quella più bassa. Così scaldi solo quando serve.")
    b["attivo"] = st.toggle("📅 Usa questi orari (VitaMemo comanda il termostato)", value=bool(b.get("attivo")), key=k + "_or_on")
    _or_stato_auto(x, b["attivo"])
    with st.expander("✨ Parti da un modello pronto"):
        mod = st.radio("Modello", list(OR_MODELLI), key=k + "_or_mod")
        st.caption(" · ".join(f"{OR_GIORNI_BREVI[int(g.split('-')[0])]}–{OR_GIORNI_BREVI[int(g.split('-')[1])]}: " + ", ".join(f"{a}–{c} {t:g}°" for a, c, t in fs)
                              for g, fs in OR_MODELLI[mod].items()))
        if st.button("📥 Usa questo modello (poi puoi cambiarlo)", key=k + "_or_modok", width="stretch"):
            nuovo = or_da_modello(mod)
            for g, fs in nuovo["giorni"].items():
                b["giorni"][g] = [dict(f, id=_or_uuid.uuid4().hex[:8]) for f in fs]
            _dm_rr()
    giorno = st.radio("Giorno", list(range(7)), horizontal=True, key=k + "_or_g",
                      format_func=lambda i: OR_GIORNI_BREVI[i] + (f" · {len(b['giorni'][str(i)])}" if b["giorni"][str(i)] else ""))
    fasce = b["giorni"][str(giorno)]
    st.markdown(f"**{OR_GIORNI[giorno]}** — " + (f"{len(fasce)} fasc{'ia' if len(fasce) == 1 else 'e'}" if fasce else "nessuna fascia"))
    for i, f in enumerate(fasce):
        fid = f["id"]
        with st.container(border=True):
            c1, c2 = st.columns(2, gap="small")
            f["dalle"] = c1.selectbox("Dalle", OR_ORARI, index=OR_ORARI.index(f["dalle"]) if f["dalle"] in OR_ORARI else 12, key=f"{k}_or_d_{fid}")
            f["alle"] = c2.selectbox("Alle", OR_ORARI_FINE, index=OR_ORARI_FINE.index(f["alle"]) if f["alle"] in OR_ORARI_FINE else 16, key=f"{k}_or_a_{fid}")
            c3, c4 = st.columns([3, 1], gap="small", vertical_alignment="bottom")
            f["temp"] = c3.number_input("🌡️ Temperatura (°C)", min_value=OR_TEMP_MIN, max_value=OR_TEMP_MAX, value=float(f.get("temp") or 20.0),
                                        step=0.5, format="%.1f", key=f"{k}_or_t_{fid}")
            if c4.button("🗑️", key=f"{k}_or_x_{fid}", width="stretch", help="Togli questa fascia"):
                b["giorni"][str(giorno)] = [y for y in fasce if y["id"] != fid]
                _dm_rr()
    if st.button("➕ Aggiungi una fascia", key=k + "_or_add", width="stretch"):
        ultima = max((OR_ORARI_FINE.index(y["alle"]) for y in fasce), default=OR_ORARI.index("06:00") - 1)
        inizio = OR_ORARI[min(ultima + 1, len(OR_ORARI) - 1)] if fasce else "06:00"
        i0 = OR_ORARI.index(inizio)
        fine = OR_ORARI_FINE[min(i0 + 3, len(OR_ORARI_FINE) - 1)]
        fasce.append({"id": _or_uuid.uuid4().hex[:8], "dalle": inizio, "alle": fine, "temp": float(fasce[-1]["temp"]) if fasce else 20.0})
        _dm_rr()
    for e in or_controlla_giorno(fasce):
        st.error("⚠️ " + e)
    if fasce:
        with st.expander(f"📋 Copia gli orari di {OR_GIORNI[giorno].lower()} su altri giorni"):
            scorciatoie = {"Lun–Ven": [0, 1, 2, 3, 4], "Sab–Dom": [5, 6], "Tutti": list(range(7))}
            scelta = st.radio("Su quali giorni", list(scorciatoie) + ["Scelgo io"], horizontal=True, key=k + "_or_cs")
            dest = scorciatoie.get(scelta) or st.multiselect("Giorni", list(range(7)), format_func=lambda i: OR_GIORNI[i], key=k + "_or_cd")
            dest = [g for g in dest if g != giorno]
            if dest and st.button(f"📋 Copia su {', '.join(OR_GIORNI_BREVI[g] for g in dest)}", key=k + "_or_cok", width="stretch"):
                for g in dest:
                    b["giorni"][str(g)] = [dict(y, id=_or_uuid.uuid4().hex[:8]) for y in fasce]
                _dm_rr()
    st.markdown("**Fuori dalle fasce**")
    tipo = st.radio("Fuori dalle fasce", ["programma", "temp"], label_visibility="collapsed", key=k + "_or_ft",
                    index=0 if b["fuori"].get("tipo") != "temp" else 1,
                    format_func=lambda t: "🅰️ Il programma del termostato" if t == "programma" else "🌙 Una temperatura ridotta decisa qui")
    b["fuori"]["tipo"] = tipo
    if tipo == "temp":
        b["fuori"]["temp"] = st.number_input("🌙 Temperatura ridotta (°C)", min_value=OR_TEMP_MIN, max_value=OR_TEMP_MAX,
                                             value=float(b["fuori"].get("temp") or 16.0), step=0.5, format="%.1f", key=k + "_or_rt")
    else:
        st.caption("Fuori dalle fasce il termostato segue il suo programma (se lì c'è una temperatura molto bassa, per esempio 7°, la casa resta quasi spenta). "
                   "Se preferisci tenerla un po' più calda (per esempio 16° di notte), scegli «temperatura ridotta».")
    stima = or_stima(b)
    if stima:
        n_ = lambda v, d=1: (f"{v:.{d}f}".rstrip("0").rstrip(".") if d else f"{v:.0f}").replace(".", ",")  # noqa: E731
        txt = f"🔥 Riscaldamento alla temperatura delle fasce: **{n_(stima['ore_comfort'])} ore** a settimana su 168"
        if stima.get("risparmio") is not None:
            txt += (f". Temperatura media della settimana **{n_(stima['media'])}°** invece di {n_(stima['alta'])}° tutto il giorno: "
                    f"risparmio stimato **circa {n_(stima['risparmio'] * 100, 0)}%** di gas (regola pratica: ogni grado in meno fa consumare circa il 7% in meno; "
                    "il valore vero dipende da come è isolata la casa).")
        else:
            txt += ". Con «temperatura ridotta» qui sotto vedi anche il risparmio stimato."
        st.info(txt)
    errori = [f"{OR_GIORNI[int(g)]}: {e}" for g, fs in b["giorni"].items() for e in or_controlla_giorno(fs)]
    c1, c2 = st.columns([2, 1], gap="small")
    if c1.button("💾 Salva gli orari", key=k + "_or_salva", type="primary", width="stretch", disabled=bool(errori)):
        pulito = _or_pulito(b)
        if pulito["attivo"] and not any(pulito["giorni"].values()):
            st.error("⚠️ Aggiungi almeno una fascia prima di attivare gli orari.")
        else:
            _dm_salva(lambda dm_: dm_.setdefault("orari", {}).__setitem__(x["id"], pulito), "orari riscaldamento")
            _dm_log(f"{x.get('nome')}: orari {'attivati' if pulito['attivo'] else 'salvati (spenti)'}")
            try:
                carica_dati.clear()
            except Exception:
                pass
            esito = dm_orari_applica(x, pulito, forza=True) if pulito["attivo"] else None
            st.session_state.pop(k + "_orb", None)
            st.session_state.pop(f"_or_fatto_{x['id']}", None)
            st.toast("✅ Orari salvati" + (" · " + esito if esito else ""))
            st.rerun()                                                   # si chiude la finestra e il telecomando mostra subito gli orari
    if c2.button("↩️ Annulla", key=k + "_or_ann", width="stretch"):
        st.session_state.pop(k + "_orb", None)
        _dm_rr()
    if errori:
        st.caption("Correggi prima: " + "; ".join(errori))
    if b["attivo"]:
        pross = or_prossimo_cambio(_or_pulito(b), adesso())
        if pross:
            st.caption("⏭️ Prossimo cambio: " + pross[1])
        st.caption("✋ Se cambi la temperatura a mano (qui o nell'app Termostato), la tua scelta vale fino all'inizio della fascia successiva.")
    _or_guida_orologio()
