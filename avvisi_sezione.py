# 🔔 Il campanellino di ogni sezione: si vedono gli avvisi di quella sezione, come sono impostati, e da lì si cambiano
# (giorni di preavviso, ora, canali, suono, calendario). Le scelte stanno in d["avvisi_sezioni"][sezione] e le legge
# anche promemoria.py (il programma su GitHub che manda email, Telegram, WhatsApp e SMS). Prefisso: avs_
import datetime as _avs_dt

# cosa si può regolare, sezione per sezione (onesto: dove l'invio non c'è, il pannello lo dice)
_AVS_CAPACITA = {
    "dispensa": {"giorni": True, "ora": True, "canali": True, "suono": True, "invio": True},
    "salute": {"giorni": True, "ora": True, "canali": True, "suono": False, "invio": True},
    "casa": {"giorni": True, "ora": True, "canali": True, "suono": False, "invio": True},
    "documenti": {"giorni": True, "ora": True, "canali": True, "suono": False, "invio": True},
    "auto": {"giorni": True, "ora": True, "canali": True, "suono": False, "invio": True},
    "compleanni": {"giorni": True, "ora": True, "canali": True, "suono": False, "invio": True},
    "badante": {"giorni": True, "ora": True, "canali": True, "suono": False, "invio": True},
}
_AVS_GIORNI_PRED = {"dispensa": (60, 30, 14, 7, 1, 0), "salute": (60, 30, 14, 7, 1, 0), "casa": (30, 14, 7, 1, 0),
                    "auto": (90, 30, 15, 3, 0), "documenti": (180, 90), "compleanni": (7, 1, 0), "badante": (3, 0)}
_AVS_GIORNI_SCELTA = (90, 60, 45, 30, 21, 14, 10, 7, 5, 3, 2, 1, 0)
_AVS_GIORNI_LUNGHI = (365, 270, 180, 120, 90, 60, 30, 14, 7, 3, 1, 0)
_AVS_SUONI = {"auto": "🔄 Automatico (come adesso: dipende da adulti, bimbi o animali)", "classico": "🔔 Din-don (classico)",
              "bimbi": "👶 Voci dei bimbi", "animali": "🐾 Animali (gatto, cane, leone)", "nessuno": "🔇 Nessun suono"}
_AVS_CANALI = (("telegram", "📱 Telegram", "telegram_chat_id"), ("email", "✉️ Email", "avviso_email"),
               ("whatsapp", "🟢 WhatsApp", "avviso_whatsapp"), ("sms", "💬 SMS", "avviso_sms"))


def avs_cfg(d, sez):
    c = (d.get("avvisi_sezioni") or {}).get(sez) if isinstance(d.get("avvisi_sezioni"), dict) else None
    return dict(c) if isinstance(c, dict) else {}


def avs_canali_generali(d):
    c = d.get("avvisi_canali")
    if c is None:
        c = ["telegram"] if d.get("telegram_chat_id") else []
    return [x for x in c if x in ("telegram", "email", "sms", "whatsapp")]


def avs_riepilogo(d, sez):
    """Una riga che dice come è impostata la sezione adesso."""
    cap = _AVS_CAPACITA.get(sez, {})
    c = avs_cfg(d, sez)
    if not cap.get("invio"):
        return "Gli avvisi di questa sezione si vedono dentro l'app (e nel calendario, se lo scarichi)."
    if c.get("attivo") is False:
        return "🔕 Avvisi spenti per questa sezione."
    giorni = c.get("giorni") if isinstance(c.get("giorni"), list) and c.get("giorni") else list(_AVS_GIORNI_PRED.get(sez, ()))
    canali = c.get("canali") if isinstance(c.get("canali"), list) else avs_canali_generali(d)
    nomi = {k: n for k, n, _ in _AVS_CANALI}
    parti = []
    if cap.get("giorni") and giorni:
        parti.append("preavviso: " + ", ".join(("oggi" if g == 0 else f"{g} g") for g in sorted(giorni, reverse=True)))
    parti.append("ora: " + (c.get("ora") or "al mattino (circa le 7)"))
    parti.append("canali: " + (", ".join(nomi[x] for x in canali) if canali else "nessuno (solo nell'app)"))
    if cap.get("suono"):
        parti.append("suono: " + _AVS_SUONI.get(c.get("suono") or "auto", _AVS_SUONI["auto"]).split(" ", 1)[1].split(" (")[0])
    return " · ".join(parti)


def _avs_data(x):
    try:
        return _avs_dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def avs_eventi(sez, d, oggi_):
    """Gli appuntamenti con data di una sezione, per il calendario: [{uid, titolo, data}]."""
    ev = []

    def aggiungi(chiave, titolo, data):
        if data and data >= oggi_ - _avs_dt.timedelta(days=1):
            ev.append({"uid": f"avs-{sez}-{chiave}", "titolo": titolo, "data": data})
    f = d.get("farmacia") or {}
    if sez == "dispensa":
        for a in d.get("articoli", []):
            aggiungi(a.get("id") or a.get("nome"), f"🥫 Scade: {a.get('nome', 'Prodotto')}", _avs_data(a.get("scadenza")))
    elif sez in ("salute", "documenti"):
        if sez == "salute":
            for m in f.get("medicinali", []):
                aggiungi("m" + str(m.get("id") or m.get("nome")), f"💊 Scade: {m.get('nome', 'Medicinale')}", _avs_data(m.get("scadenza")))
            for x in f.get("prescrizioni", []):
                if x.get("stato") != "Usata":
                    aggiungi("p" + str(x.get("id") or x.get("tipo")), f"📝 Ricetta valida fino a oggi ({x.get('tipo', '')})", _avs_data(x.get("valida_fino")))
            for x in f.get("visite", []):
                aggiungi("v" + str(x.get("id") or x.get("categoria")), f"📅 {x.get('categoria', 'Visita')}", _avs_data(x.get("prossimo")) or _avs_data(x.get("data")))
            for x in f.get("vaccinazioni", []):
                aggiungi("r" + str(x.get("id") or x.get("nome")), f"💉 Richiamo {x.get('nome', '')}", _avs_data(x.get("richiamo")))
        for x in f.get("documenti", []):
            if not x.get("senza_scadenza"):
                aggiungi("d" + str(x.get("id") or x.get("tipo")), f"📄 Scade: {x.get('tipo', 'Documento')}", _avs_data(x.get("scadenza")))
    elif sez == "badante" and "bdt_calcolo" in globals() and (d.get("badante") or {}).get("inizio"):
        r_ = bdt_calcolo(d["badante"], oggi_)
        if r_["fine"] is not None:
            aggiungi("fine", "👵 Finiscono i soldi della badante", r_["fine"])
    elif sez == "compleanni":
        for x in d.get("compleanni", []):
            nasc = _avs_data(x.get("nascita"))
            if nasc and not x.get("scomparso"):
                for anno in (oggi_.year, oggi_.year + 1):
                    try:
                        prossimo = nasc.replace(year=anno)
                    except ValueError:                           # 29 febbraio
                        prossimo = nasc.replace(year=anno, day=28)
                    if prossimo >= oggi_:
                        aggiungi(str(x.get("id") or x.get("nome")), f"🎂 Compleanno di {(str(x.get('nome', '')) + ' ' + str(x.get('cognome', ''))).strip()}", prossimo)
                        break
    elif sez == "auto" and "au_scadenze_avviso" in globals():
        for k, (g, txt) in enumerate(au_scadenze_avviso(d.get("auto") or {}, oggi_, 120)):
            if g is not None and g >= 0:
                aggiungi(f"a{k}-{g}", txt, oggi_ + _avs_dt.timedelta(days=g))
    elif sez == "casa" and "ca_scadenze" in globals():
        c = d.get("casa") or {}
        for k in ("beni", "documenti", "manutenzioni"):
            c.setdefault(k, [])
        sc = ca_scadenze(c, oggi_, 120)
        for k, (nome, g) in enumerate(sc.get("garanzie", [])):
            aggiungi(f"g{k}-{g}", f"🛠️ Garanzia {nome}", oggi_ + _avs_dt.timedelta(days=g))
        for k, (nome, voce, g) in enumerate(sc.get("manutenzioni", [])):
            aggiungi(f"m{k}-{g}", f"🔧 {nome} · {voce}", oggi_ + _avs_dt.timedelta(days=g))
        for k, (nome, g, _imp) in enumerate(sc.get("spese", [])):
            aggiungi(f"s{k}-{g}", f"🏢 {nome}", oggi_ + _avs_dt.timedelta(days=g))
        for k, (nome, g, _imp) in enumerate(sc.get("bollette", [])):
            aggiungi(f"b{k}-{g}", f"💶 {nome}", oggi_ + _avs_dt.timedelta(days=g))
    return ev


def avs_ics(sez, d, oggi_, nome):
    """Il file calendario (.ics) della sezione, con gli allarmi ai giorni e all'ora scelti qui."""
    c = avs_cfg(d, sez)
    giorni = [g for g in (c.get("giorni") or _AVS_GIORNI_PRED.get(sez) or (7, 1, 0)) if g <= 60][:5] or [1, 0]
    ora = c.get("ora") or "09:00"
    ev = avs_eventi(sez, d, oggi_)
    for e in ev:
        e["allarmi_orari"] = [(g, ora) for g in sorted(set(giorni), reverse=True)]
    return amm_ics(ev, nome) if ev else b"", len(ev)


def avs_guida_testo(sez):
    cap = _AVS_CAPACITA.get(sez, {})
    righe = ["**Come ricevere gli avvisi:**"]
    if cap.get("invio"):
        righe += ["1. Vai in **🩺 Salute → 🔔 Scegli come ricevere gli avvisi** e scrivi i tuoi recapiti (Telegram, email, WhatsApp, SMS), una volta sola.",
                  "2. Qui sopra spunta i canali che vuoi per questa sezione, oppure lascia «come le altre sezioni».",
                  "3. Gli avvisi li manda un programma automatico: controlla ogni mezz'ora, quindi l'ora scelta può slittare di qualche minuto.",
                  "4. Per provare, in Salute premi **📨 Mandami un messaggio di prova**."]
    else:
        righe += ["Per questa sezione gli avvisi si vedono qui nell'app (campanellino con il numero) e sulla Home.",
                  "Per averli anche sul telefono, scarica il calendario qui sotto."]
    righe += ["", "**Google Calendar:** premi «Scarica il calendario», poi apri il file: Android propone **Calendario Google**. "
              "Oppure da calendar.google.com → ⚙️ Impostazioni → Importa ed esporta → Importa. Gli appuntamenti si aggiornano se lo importi di nuovo "
              "(non si duplicano). Non è un collegamento automatico: se cambi una data, scarica e importa ancora."]
    return "\n".join(righe)


def _avs_corpo(sez, etichetta):
    d = carica_dati(crea_archivio(), st.session_state["percorso"])
    cap = _AVS_CAPACITA.get(sez, {})
    c = avs_cfg(d, sez)
    k = f"avs_{sez}_"
    st.caption("Ecco come sono impostati ora gli avvisi di questa sezione:")
    st.info(avs_riepilogo(d, sez))
    voci = pn_scadenze().get(sez, []) if "pn_scadenze" in globals() else []
    if voci:
        st.markdown("**Adesso c'è da guardare:**")
        for v in voci[:12]:
            st.markdown("• " + v)
        if len(voci) > 12:
            st.caption(f"… e altri {len(voci) - 12}.")
    else:
        st.success("Per ora non c'è niente in scadenza.")
    nuovo = dict(c)
    if cap.get("invio"):
        nuovo["attivo"] = st.toggle("Ricevi gli avvisi di questa sezione", value=c.get("attivo", True) is not False, key=k + "attivo")
        if nuovo["attivo"]:
            if cap.get("giorni"):
                pred = list(_AVS_GIORNI_PRED.get(sez, (7, 1, 0)))
                att = c.get("giorni") if isinstance(c.get("giorni"), list) and c.get("giorni") else pred
                opz = sorted(set(_AVS_GIORNI_LUNGHI if sez == "documenti" else _AVS_GIORNI_SCELTA) | set(att), reverse=True)
                sc = st.multiselect("Quanti giorni prima avvisarmi (0 = il giorno stesso)", opz, default=sorted(set(att), reverse=True), key=k + "giorni",
                                    format_func=lambda g: "Il giorno stesso" if g == 0 else f"{g} giorni prima")
                if sorted(sc, reverse=True) in (sorted(pred, reverse=True), []):
                    nuovo.pop("giorni", None)                      # come i giorni di sempre: non si salva niente
                else:
                    nuovo["giorni"] = sorted(sc, reverse=True)
            if sez == "casa":
                st.caption("Questi giorni valgono per garanzie, manutenzioni e bollette. Le rate dell'amministrazione hanno i loro giorni, scelti nella rata.")
            elif sez == "auto":
                st.caption("Valgono per bollo, assicurazione, revisione, patente e simili. Le multe da pagare hanno giorni propri (15, 5, 3, 0).")
            elif sez == "badante":
                st.caption("Ti avviso 3 giorni prima e l'ultimo giorno in cui i soldi bastano. Si calcola da soldi consegnati, tariffa e giorni di lavoro.")
            elif sez == "compleanni":
                st.caption("Di solito 7 giorni prima, il giorno prima e il giorno stesso. Le persone segnate «non c'è più» non vengono avvisate.")
            elif sez == "documenti":
                st.caption("Di solito 180 giorni (6 mesi) e 90 giorni (3 mesi) prima della scadenza; poi ogni lunedì se è scaduto.")
            if cap.get("ora"):
                usa_ora = st.checkbox("Scelgo io l'ora degli avvisi", value=bool(c.get("ora")), key=k + "usaora")
                if usa_ora:
                    try:
                        h, m = (c.get("ora") or "08:00").split(":")
                        v0 = _avs_dt.time(int(h), int(m))
                    except Exception:
                        v0 = _avs_dt.time(8, 0)
                    t_ = st.time_input("A che ora?", value=v0, step=1800, key=k + "ora")
                    nuovo["ora"] = t_.strftime("%H:%M")
                else:
                    nuovo.pop("ora", None)
                    st.caption("Senza ora scelta, gli avvisi arrivano al mattino.")
            if cap.get("canali"):
                modo = st.radio("Dove ricevere gli avvisi", ["Come le altre sezioni", "Scelgo io per questa sezione"], index=1 if isinstance(c.get("canali"), list) else 0,
                                key=k + "modo")
                if modo.startswith("Scelgo"):
                    base = c.get("canali") if isinstance(c.get("canali"), list) else avs_canali_generali(d)
                    scelti = []
                    for cod, nome, campo in _AVS_CANALI:
                        ha = bool(str(d.get(campo) or "").strip())
                        if st.checkbox(nome + ("" if ha else " — manca il recapito"), value=cod in base, key=k + "c_" + cod):
                            scelti.append(cod)
                    if any(not str(d.get(dict((a, f) for a, _n, f in _AVS_CANALI)[x]) or "").strip() for x in scelti):
                        st.warning("Per i canali senza recapito scrivilo in 🩺 Salute → Scegli come ricevere gli avvisi: finché manca, quel canale non parte.")
                    if not scelti:
                        st.caption("Nessun canale spuntato: gli avvisi li vedi solo nell'app.")
                    nuovo["canali"] = scelti
                else:
                    nuovo.pop("canali", None)
            if cap.get("suono"):
                chiavi = list(_AVS_SUONI)
                s0 = c.get("suono") if c.get("suono") in _AVS_SUONI else "auto"
                nuovo["suono"] = st.selectbox("Suono nell'app (quando si apre «Prodotti da controllare»)", chiavi, index=chiavi.index(s0),
                                              format_func=lambda x: _AVS_SUONI[x], key=k + "suono")
            elif cap.get("invio"):
                st.caption("🔊 Il suono dell'avviso c'è nella Dispensa; qui il telefono usa il suono delle notifiche di Telegram, WhatsApp, email o SMS.")
    nuovo["calendario"] = st.toggle("Vedi questi avvisi anche nel calendario (Google Calendar)", value=bool(c.get("calendario")), key=k + "cal")
    if nuovo["calendario"]:
        try:
            dati_ics, n_ev = avs_ics(sez, d, oggi(), f"VitaMemo – {etichetta}")
        except Exception:
            dati_ics, n_ev = b"", 0
        if n_ev:
            st.download_button(f"📅 Scarica il calendario ({n_ev} appuntamenti)", dati_ics, file_name=f"avvisi_{sez}.ics", mime="text/calendar",
                               key=k + "ics", width="stretch")
        else:
            st.caption("Per ora non ci sono appuntamenti con una data da mettere nel calendario.")
    with st.expander("ℹ️ Come ricevere gli avvisi"):
        st.markdown(avs_guida_testo(sez))
    a, b = st.columns(2)
    if a.button("💾 Salva", type="primary", key=k + "salva", width="stretch"):
        try:
            pulito = {x: y for x, y in nuovo.items() if y is not None}
            salva(lambda dd: dd.setdefault("avvisi_sezioni", {}).__setitem__(sez, pulito), "Avvisi della sezione")
            st.session_state["avs_ok"] = "Salvato ✅"
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.rerun()
    if b.button("↩️ Torna come prima", key=k + "reset", width="stretch"):
        salva(lambda dd: (dd.get("avvisi_sezioni") or {}).pop(sez, None), "Avvisi della sezione")
        st.session_state["avs_ok"] = "Rimessi come prima ✅"
        st.rerun()


def avs_apri(sez, etichetta):
    st.dialog("🔔 " + etichetta, width="large")(lambda: _avs_corpo(sez, etichetta))()


def avs_bottone(corrente):
    """Il campanellino sotto i bottoni delle sezioni."""
    etichetta = next((e for s, e, _a, _b in _PN_VOCI if s == corrente), None)
    if not etichetta:
        return
    n = len(pn_scadenze().get(corrente, []))
    msg = st.session_state.pop("avs_ok", None)
    if msg:
        st.toast(msg)
    with st.container(key="avs_barra"):
        if st.button(f"🔔 Avvisi di questa sezione" + (f" ({n})" if n else ""), key="avs_apri_" + corrente, width="stretch"):
            avs_apri(corrente, etichetta)
