# Carica l'app (parte1.py, parte2.py, aggiunte.py, categorie.py, interattivi.py, hero_foto.py, stile.py, spesa.py, elimina.py, stile2.py, posto.py, account.py, foto_prodotto.py, modifica.py, bugiardino.py, guida.py, lingue*.py, parte3.py, parte4.py, avvisi.py, voce.py, fotocamera.py, farmacia.py, info_sezioni.py, utilita.py, assistente.py, guida_xx.py) come se fosse un unico file.
import glob
import os

_cartella = os.path.dirname(os.path.abspath(__file__))

# Le SCHEDE (tab) ricordano quella scelta: dopo un'azione o un ridisegno non si torna alla prima.
import inspect as _inspect_tab
import streamlit as _st_tab
if not getattr(_st_tab.tabs, "_ricorda", False):
    _tabs_originale = _st_tab.tabs
    try:
        _par_tab = _inspect_tab.signature(_tabs_originale).parameters
        _tabs_ok = "key" in _par_tab and "on_change" in _par_tab
    except Exception:
        _tabs_ok = False

    def _tabs_con_memoria(tabs, *a, **kw):
        if not _tabs_ok or "key" in kw or a:
            return _tabs_originale(tabs, *a, **kw)
        try:
            nome_file = os.path.basename(_sys_cc._getframe(1).f_code.co_filename)
        except Exception:
            nome_file = ""
        if nome_file in ("invio.py", "info_sezioni.py"):                  # finestre di invio e guide: restano come sono
            return _tabs_originale(tabs, **kw)
        vistE = _st_tab.session_state.setdefault("_tabs_viste", {})
        base = "tabm_" + _hashlib_cc.md5("|".join(str(t) for t in tabs).encode("utf-8")).hexdigest()[:10]
        try:                                                                       # dopo «Salva in dispensa» si torna alla scheda Dispensa (la prima delle schede principali)
            if _st_tab.session_state.get("_vai_tab_dispensa") and any("Aggiungi" in str(t) for t in tabs) and len(tabs) >= 5:
                _st_tab.session_state.pop("_vai_tab_dispensa", None)
                _st_tab.session_state[base] = tabs[0]
        except Exception:
            pass
        giro = _st_tab.session_state.get("_tabs_giro", 0)
        n = vistE.get(base)
        n = (n[1] + 1) if (n and n[0] == giro) else 0
        vistE[base] = (giro, n)
        try:
            return _tabs_originale(tabs, key=base + (f"_{n}" if n else ""), on_change="rerun", **kw)
        except Exception:
            return _tabs_originale(tabs, **kw)
    _tabs_con_memoria._ricorda = True
    _tabs_con_memoria._attiva = bool(_tabs_ok)                     # lo legge il «Controllo tecnico»: dopo il primo ridisegno questo codice non si riesegue
    _tabs_con_memoria._originale = _tabs_originale
    _st_tab.tabs = _tabs_con_memoria
import streamlit as _st_giro
_st_giro.session_state["_tabs_giro"] = _st_giro.session_state.get("_tabs_giro", 0) + 1     # ogni ridisegno è un «giro»: serve a dare chiavi stabili alle schede

# I CALENDARI di tutta l'app vanno indietro di 100 anni e avanti di 150 (di solito Streamlit ne permette solo 10 per parte, e molti punti avevano limiti propri).
import datetime as _dt_cal
if not getattr(_st_tab.date_input, "_calendario_ampio", False):
    from streamlit.delta_generator import DeltaGenerator as _DG_cal

    def _date_ampie(firma, args, kw):
        """Allarga min_value e max_value: oggi-100 anni … oggi+150 anni (e comunque le date già scelte e i limiti più larghi già impostati)."""
        try:
            b = firma.bind_partial(*args, **kw)
        except TypeError:
            return args, kw
        ar = b.arguments
        oggi_c = _dt_cal.date.today()

        def sposta(anni):
            try:
                return oggi_c.replace(year=oggi_c.year + anni)
            except ValueError:
                return oggi_c.replace(year=oggi_c.year + anni, day=28)
        lo, hi = sposta(-100), sposta(150)
        v = ar.get("value")
        scelte = []
        for x in (v if isinstance(v, (list, tuple)) else [v]):
            if isinstance(x, _dt_cal.datetime):
                x = x.date()
            if isinstance(x, _dt_cal.date):
                scelte.append(x)
        mn, mx = ar.get("min_value"), ar.get("max_value")
        mn = mn.date() if isinstance(mn, _dt_cal.datetime) else mn
        mx = mx.date() if isinstance(mx, _dt_cal.datetime) else mx
        ar["min_value"] = min([lo] + [x for x in scelte if x < lo] + ([mn] if isinstance(mn, _dt_cal.date) and mn < lo else []))
        ar["max_value"] = max([hi] + [x for x in scelte if x > hi] + ([mx] if isinstance(mx, _dt_cal.date) and mx > hi else []))
        return b.args, b.kwargs
    try:
        _firma_dg = _inspect_tab.signature(_DG_cal.date_input)
        _dg_originale = _DG_cal.date_input

        def _dg_date_input(self, *a, **kw):
            a2, k2 = _date_ampie(_firma_dg, (self,) + a, kw)
            return _dg_originale(*a2, **k2)
        _firma_st = _inspect_tab.signature(_st_tab.date_input)
        _st_originale = _st_tab.date_input

        def _st_date_input(*a, **kw):
            a2, k2 = _date_ampie(_firma_st, a, kw)
            return _st_originale(*a2, **k2)
        _dg_date_input._calendario_ampio = True
        _st_date_input._calendario_ampio = True
        _DG_cal.date_input = _dg_date_input
        _st_tab.date_input = _st_date_input
        _col_originale = _st_tab.column_config.DateColumn                      # anche i calendari dentro le tabelle modificabili

        def _colonna_data(*a, **kw):
            oggi_c = _dt_cal.date.today()
            kw["min_value"] = min([oggi_c.replace(year=oggi_c.year - 100, day=min(oggi_c.day, 28))] + ([kw["min_value"]] if isinstance(kw.get("min_value"), _dt_cal.date) else []))
            kw["max_value"] = max([oggi_c.replace(year=oggi_c.year + 150, day=min(oggi_c.day, 28))] + ([kw["max_value"]] if isinstance(kw.get("max_value"), _dt_cal.date) else []))
            return _col_originale(*a, **kw)
        _st_tab.column_config.DateColumn = _colonna_data
    except Exception:
        pass

# Le «linguette» (riquadri che si aprono e si chiudono) restano SEMPRE chiuse all'apertura della pagina: si aprono solo se le tocchi tu.
import streamlit as _st_chiuse
if not getattr(_st_chiuse.expander, "_sempre_chiusa", False):
    _expander_originale = _st_chiuse.expander

    def _expander_sempre_chiusa(label, expanded=False, _aperta=False, **kw):
        return _expander_originale(label, expanded=bool(_aperta), **kw)          # «_aperta=True» solo se chi la disegna lo chiede (es. dopo che hai toccato un pulsante dentro la tendina)
    _expander_sempre_chiusa._sempre_chiusa = True
    _st_chiuse.expander = _expander_sempre_chiusa

# Punti in cui la Farmacia si aggancia alla Home (parte3.py). Ogni riga viene cercata UNA sola volta:
# se non la trova, la dispensa funziona lo stesso e la Farmacia semplicemente non compare.
_AGGANCI = {
    "utilita.py": [
        ('<h1>🧰 Utilità</h1>',
         '<h1>" + ("" if "ih_ha_icona" in globals() and ih_ha_icona("utilita") else "🧰 ") + "Utilità</h1>'),
    ],
    "parte2.py": [
        ('@st.cache_data(ttl=15, show_spinner=False)\ndef carica_dati(_archivio, nome):', '@st.cache_data(ttl=60, show_spinner=False)\ndef carica_dati(_archivio, nome):'),
    ],
    "farmacia.py": [
        # Terapie a intervalli (salute_terapie_intervalli.py): il giorno in cui va presa e come si scrive «ogni 15 giorni»
        ('        if t_.get("profilo", "p0") != pid or d.weekday() not in t_.get("giorni", []):',
         '        if t_.get("profilo", "p0") != pid or not (terapia_e_giorno(t_, d) if "terapia_e_giorno" in globals() else d.weekday() in t_.get("giorni", [])):'),
        ('        giorni = ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []))\n        periodo = f"dal {data_it(t_[\'inizio\'])}"',
         '        giorni = ter_giorni_testo(t_) if "ter_giorni_testo" in globals() else ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []))\n        periodo = f"dal {data_it(t_[\'inizio\'])}"'),
        ('                                    ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", [])),\n                                    ", ".join(t_.get("orari", [])),',
         '                                    (ter_giorni_testo(t_) if "ter_giorni_testo" in globals() else ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []))),\n                                    ", ".join(t_.get("orari", [])),'),
        ('            gg = ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []) if 0 <= g < len(GIORNI_SETT)) or "tutti i giorni"',
         '            gg = (ter_giorni_testo(t_, "tutti i giorni") if "ter_giorni_testo" in globals() else ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []) if 0 <= g < len(GIORNI_SETT)) or "tutti i giorni")'),
        ('", ".join(GIORNI_SETT[g] for g in t_.get("giorni", [])), ", ".join(t_.get("orari", [])),',
         '(ter_giorni_testo(t_) if "ter_giorni_testo" in globals() else ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []))), ", ".join(t_.get("orari", [])),'),
        ('<h1>🩺 Salute</h1><p>Medicinali, terapie, visite e vaccini della tua famiglia</p>',
         '<h1>" + ("" if "ih_ha_icona" in globals() and ih_ha_icona("salute") else "🩺 ") + "Salute</h1><p>Medicinali, terapie, visite e vaccini della tua famiglia</p>'),
        ('<h1>📁 I miei documenti</h1>',
         '<h1>" + ("" if "ih_ha_icona" in globals() and ih_ha_icona("documenti") else "📁 ") + "I miei documenti</h1>'),
        ('    with st.expander(f"👥 Gestisci profili ({len(profili)}/{MAX_PROFILI})"):\n        with st.form("fa_nuovo_profilo", clear_on_submit=True):\n',
         '    with st.expander(f"👥 Gestisci profili ({len(profili)}/{MAX_PROFILI})"):\n        if "sp_rinomina_profili" in globals():\n            sp_rinomina_profili(profili, f)\n        with st.form("fa_nuovo_profilo", clear_on_submit=True):\n'),
        # Avvisi: canale WhatsApp (gratuito, a scelta) e avvisi di Casa nel modulo «Scegli come ricevere gli avvisi»
        ('    chat, mail, sms = str(d.get("telegram_chat_id") or ""), str(d.get("avviso_email") or ""), str(d.get("avviso_sms") or "")\n',
         '    chat, mail, sms = str(d.get("telegram_chat_id") or ""), str(d.get("avviso_email") or ""), str(d.get("avviso_sms") or "")\n    wa_num, wa_key = str(d.get("avviso_whatsapp") or ""), str(d.get("avviso_whatsapp_chiave") or "")\n'),
        ('    if "sms" in canali and sms:\n        attivi.append(f"💬 SMS {html.escape(sms)}")\n',
         '    if "sms" in canali and sms:\n        attivi.append(f"💬 SMS {html.escape(sms)}")\n    if "whatsapp" in canali and wa_num:\n        attivi.append(f"🟢 WhatsApp {html.escape(wa_num)}")\n    if attivi and d.get("avvisi_casa"):\n        attivi.append("🏡 Avvisi di Casa (garanzie e manutenzioni) attivi")\n'),
        ('            v_sm = st.text_input("Numero di cellulare", value=sms, placeholder="es. 333 1234567")\n',
         '            v_sm = st.text_input("Numero di cellulare", value=sms, placeholder="es. 333 1234567")\n            c_wa = st.checkbox("🟢 WhatsApp (gratuito, con CallMeBot)", value="whatsapp" in canali)\n            v_wa = st.text_input("Numero di WhatsApp", value=wa_num, placeholder="es. 333 1234567 oppure +39 333 1234567")\n            k_wa = st.text_input("Chiave personale di CallMeBot", value=wa_key, placeholder="la ricevi da CallMeBot su WhatsApp")\n            st.caption("Come avere la chiave: apri https://www.callmebot.com/blog/free-api-whatsapp-messages/ , salva il contatto che indica, scrivigli su WhatsApp «I allow callmebot to send me messages» e ti risponde con la tua chiave. Se non arriva entro 2 minuti riprova dopo 24 ore. È un servizio esterno gratuito e non ufficiale: per gli avvisi importanti tieni anche Telegram o l\'email.")\n'),
        ('            ok = st.form_submit_button("Salva")\n        st.caption("Gli avvisi arrivano quando mancano',
         '            casa_av = st.checkbox("🏡 Avvisami anche di Casa: bollette da pagare, garanzie e manutenzioni", value=bool(d.get("avvisi_casa")))\n            ok = st.form_submit_button("Salva")\n        st.caption("Gli avvisi arrivano quando mancano'),
        ('    if ok:\n        v_tg, v_ml, v_sm = v_tg.strip(), v_ml.strip(), re.sub(r"[\\s.\\-]", "", v_sm)\n',
         '    if ok:\n        v_tg, v_ml, v_sm = v_tg.strip(), v_ml.strip(), re.sub(r"[\\s.\\-]", "", v_sm)\n        v_wa, k_wa = re.sub(r"[\\s.\\-()]", "", v_wa), k_wa.strip()\n        if v_wa.startswith("00"):\n            v_wa = "+" + v_wa[2:]\n        if v_wa and re.fullmatch(r"3\\d{8,9}", v_wa):                 # cellulare italiano scritto senza prefisso\n            v_wa = "+39" + v_wa\n'),
        ('        elif (c_tg and not v_tg) or (c_ml and not v_ml) or (c_sm and not v_sm):\n',
         '        elif v_wa and not re.fullmatch(r"\\+\\d{8,15}", v_wa):\n            errore = "Il numero di WhatsApp deve avere il prefisso, per esempio +39 333 1234567."\n        elif (c_tg and not v_tg) or (c_ml and not v_ml) or (c_sm and not v_sm) or (c_wa and not (v_wa and k_wa)):\n'),
        ('        scelti = [n for n, c in (("telegram", c_tg), ("email", c_ml), ("sms", c_sm)) if c]\n',
         '        scelti = [n for n, c in (("telegram", c_tg), ("email", c_ml), ("sms", c_sm), ("whatsapp", c_wa)) if c]\n'),
        ('                     "telegram_privacy": bool(privacy), "avvisi_dosi": bool(dosi)}\n',
         '                     "telegram_privacy": bool(privacy), "avvisi_dosi": bool(dosi),\n                     "avviso_whatsapp": v_wa, "avviso_whatsapp_chiave": k_wa, "avvisi_casa": bool(casa_av)}\n'),
        # Home: gli stili dell'icona «Casa» e le misure delle quattro icone si aggiungono allo stile già scritto (casa_css è in casa.py)
        ('    css += "</style>"\n    st.markdown(css, unsafe_allow_html=True)\n    with st.container(key="azioni_icone"):\n',
         '    css += (casa_css() if "casa_css" in globals() else "")\n    css += "</style>"\n    st.markdown(css, unsafe_allow_html=True)\n    with st.container(key="azioni_icone"):\n'),
        # Home: l'icona «Casa» sulla stessa riga delle altre, tra «I miei documenti» e «Utilità» (casa_pulsante è in casa.py)
        ('        c1, c2, c3 = st.columns(3, gap="small")\n        premuto_u = False\n        with c3:\n            if uri_u:\n',
         '        c1, c2, c3, c4 = st.columns(4, gap="small")\n        premuto_u = False\n        premuto_c = False\n'
         '        with c3:\n            if "casa_pulsante" in globals():\n                premuto_c = casa_pulsante()\n'
         '        with c4:\n            if uri_u:\n'),
        ('    if premuto_u:\n',
         '    if premuto_c:\n        st.session_state["sezione_home"] = "casa"\n        st.session_state["farmacia_aperta"] = True\n        st.rerun()\n    if premuto_u:\n'),
    ],
    "parte3.py": [
        # banner della Dispensa: l'armadietto con la scritta al posto dell'immagine dei vasetti (se manca dispensa.webp resta il banner di prima)
        ("\n\ndef leggi_utenti():", "\nHERO = (ih_hero_dispensa() if \"ih_hero_dispensa\" in globals() else None) or HERO\n\n\ndef leggi_utenti():"),
        # tabella: colonna «Acquisto»
        ('                t("Scadenza"): data_it(r.get("scadenza")), t("Stato"): f"{ICONE[s]} {testo_giorni(s, g)}",\n',
         '                t("Scadenza"): data_it(r.get("scadenza")), "Acquisto": data_it(r.get("acquisto")), t("Stato"): f"{ICONE[s]} {testo_giorni(s, g)}",\n'),
        # scheda «Statistiche» (statistiche.py), prima di Info
        ('+ [":material/shopping_cart: " + t("Spesa"), _nome_messaggi, ":material/info: " + t("Info")])',
         '+ [":material/shopping_cart: " + t("Spesa"), _nome_messaggi, ":material/bar_chart: " + t("Statistiche")] + ([":material/history: " + t("Storico")] if ("fd_attivo" in globals() and fd_attivo()) else []) + [":material/info: " + t("Info")])'),
        ("tab_spesa = _schede[-3]\ntab_messaggi = _schede[-2]\ntab_info = _schede[-1]\n",
         "_k = 1 if (\"fd_attivo\" in globals() and fd_attivo()) else 0\n"
         "tab_spesa = _schede[-4 - _k]\ntab_messaggi = _schede[-3 - _k]\ntab_statistiche = _schede[-2 - _k]\ntab_info = _schede[-1]\n"
         "with tab_statistiche:\n    if \"schermata_statistiche\" in globals():\n        schermata_statistiche()\n"
         "if _k:\n    with _schede[-2]:\n        fd_scheda_storico()\n"),
        # dispensa di famiglia (dispensa_famiglia.py): sceglie il file prima di leggere i dati e mostra il selettore sotto il titolo
        ("utente = sess[\"nome\"]\ne_admin = bool(sess.get(\"admin\"))\n",
         "if \"fd_prepara\" in globals():\n    fd_prepara()\nutente = sess[\"nome\"]\ne_admin = bool(sess.get(\"admin\"))\n"),

        ("f1, f2, f3 = st.columns([3, 2, 2])",
         "f1, f2, f3, f4 = st.columns([3, 2, 2, 1])"),
        ('_viste = {"schede": "Schede", "tabella": "Tabella"}',
         'with f4:\n        icona_farmacia()\n    _viste = {"schede": "Schede", "tabella": "Tabella"}'),
        ("# --- intestazione e avvisi ---",
         'if st.session_state.get("farmacia_aperta"):\n    schermata_farmacia()\n    st.stop()\n'
         "# --- intestazione e avvisi ---"),
        # pulsante «Schermo intero» sotto la tabella dei prodotti (tabella_intera.py)
        ('            if len(_spunte) > 1:\n                st.caption(t("Spunta una sola riga da modificare."))\n',
         '            if len(_spunte) > 1:\n                st.caption(t("Spunta una sola riga da modificare."))\n'
         '            if "tf_pulsante" in globals():\n                tf_pulsante(gruppo, sezione)\n'),
        # pulsante «Informazioni» (guida a tendina) sotto l'intestazione della dispensa
        ("# --- intestazione e avvisi ---\nst.markdown(HERO, unsafe_allow_html=True)\n",
         "# --- intestazione e avvisi ---\nst.markdown(HERO, unsafe_allow_html=True)\n"
         'if "nav_pagine" in globals():\n    nav_pagine("dispensa")\n'
         'if "pn_riepilogo" in globals():\n    pn_riepilogo()\n'
         'if "pensiero_scheda" in globals():\n    pensiero_scheda()\n'
         'if "pulsante_info" in globals():\n    pulsante_info("dispensa")\n'
         'if "fd_selettore" in globals():\n    fd_selettore()\n'),
    ],
    "parte4.py": [
        ('            with st.container(border=True):\n                attivo = u.get("attivo", True)\n                ultimo = u.get("ultimo_accesso")\n',
         '            _att_u, _ult_u = u.get("attivo", True), u.get("ultimo_accesso")\n'
         '            _etich_u = f"{\'✅\' if _att_u else \'⛔\'} {u[\'nome\']} · ultimo accesso: " + (nu_ultimo_accesso(_ult_u) if "nu_ultimo_accesso" in globals() else (_ult_u.replace("T", " ") if _ult_u else "mai"))\n'
         '            with st.expander(_etich_u):\n                attivo = u.get("attivo", True)\n                ultimo = u.get("ultimo_accesso")\n'),
        ('                b1, b2, b3 = st.columns(3)\n                if b1.button("🔑 " + t("Nuova password"), key=f"np_{u[\'id\']}"):\n',
         '                if "nu_ui_admin" in globals():\n                    nu_ui_admin(u, elenco)\n                b1, b2, b3 = st.columns(3)\n                if b1.button("🔑 " + t("Nuova password"), key=f"np_{u[\'id\']}"):\n'),
        # data di acquisto nel modulo «Aggiungi»
        ('    note = st.text_input(t("Note (facoltative)"), key=K("note"), placeholder=t("es. aperto, aprire dopo il 10"))\n',
         '    note = st.text_input(t("Note (facoltative)"), key=K("note"), placeholder=t("es. aperto, aprire dopo il 10"))\n'
         '    acquisto = st.date_input(t("Data di acquisto (facoltativa)"), value=None, key=K("acquisto"), format="DD/MM/YYYY")\n'),
        ('                "aggiunto_da": utente.strip(), "aggiunto_il": datetime.now().isoformat(timespec="seconds"),\n',
         '                "aggiunto_da": utente.strip(), "aggiunto_il": datetime.now().isoformat(timespec="seconds"),\n'
         '                "acquisto": acquisto.isoformat() if acquisto else None,\n'),
        # scheda Utenti: l'interruttore «Parte della famiglia» e la spiegazione
        ('        st.caption(t("Al primo accesso la persona può scegliere una password sua."))\n',
         '        st.caption(t("Al primo accesso la persona può scegliere una password sua."))\n'
         '        st.caption("👨‍👩‍👧 " + t("Con «Parte della famiglia» vedi la Farmacia di quella persona nel Controllo famiglia: lei lo vede scritto nella sua Farmacia."))\n'),
        ('                if u.get("deve_cambiare"):\n                    st.caption("🔑 " + t("Non ha ancora scelto una sua password."))\n',
         '                if u.get("deve_cambiare"):\n                    st.caption("🔑 " + t("Non ha ancora scelto una sua password."))\n'
         '                _in_fam = st.toggle("👨‍👩‍👧 " + t("Parte della famiglia"), value=bool(u.get("famiglia")), key=f"fam_{u[\'id\']}")\n'
         '                if _in_fam != bool(u.get("famiglia")):\n'
         '                    def _imposta_fam(d, uid=u["id"], val=_in_fam):\n'
         '                        for x in d.get("utenti", []):\n'
         '                            if x["id"] == uid:\n'
         '                                x["famiglia"] = val\n'
         '                    try:\n'
         '                        salva_file("utenti.json", _imposta_fam, f"Famiglia: {u[\'nome\']}")\n'
         '                        st.rerun()\n'
         '                    except Exception as e:\n'
         '                        st.error(t("Non sono riuscito a salvare: {e}", e=e))\n'
         '                if _in_fam and "fd_selettore_ruolo" in globals():\n'
         '                    fd_selettore_ruolo(u)\n'
         '                if "sv_selettore" in globals():\n'
         '                    sv_selettore(u)\n'),
    ],
}


import hashlib as _hashlib_cc
import sys as _sys_cc
import types as _types_cc
_MEMORIA_CODICE = _sys_cc.modules.get("_dispensa_codice_compilato")
if _MEMORIA_CODICE is None:                                             # sopravvive ai ridisegni della pagina: si compila una volta sola per ogni versione del file
    _MEMORIA_CODICE = _sys_cc.modules["_dispensa_codice_compilato"] = _types_cc.ModuleType("_dispensa_codice_compilato")
    _MEMORIA_CODICE.codice = {}


# CARICAMENTO PROGRESSIVO DELLE SCHEDE: solo la scheda aperta viene disegnata (le altre restano vuote finché non le tocchi). Prima ogni ridisegno
# costruiva e mandava al telefono anche tutte le schede nascoste (nella Dispensa circa 1300 elementi su 2200). Vale solo per le schede che non
# si passano variabili fra loro (controllato con l'analisi del codice); la scheda principale (Dispensa, Medicinali) è sempre disegnata.
# Si spegne con CARICAMENTO_PROGRESSIVO = "no" nei Secrets. Se la scheda non sa dire se è aperta (`.open` manca), resta tutto com'era.
# NON pigre (di proposito): «Aggiungi», «Gestisci» e «Utenti» hanno moduli con testo scritto a metà: se la scheda non viene disegnata, Streamlit dimentica
# quello che hai scritto e passando a un'altra scheda e tornando lo perderesti (provato). Restano sempre disegnate.
_TABS_PIGRE = {"parte4.py": {"tab_spesa", "tab_messaggi", "tab_info", "tab_statistiche"},
               "farmacia.py": {"tab_ter", "tab_pre", "tab_vis", "tab_vac"}}


def _tab_aperta(_t):
    try:
        _a = getattr(_t, "open", True)
        return True if _a is None else bool(_a)
    except Exception:
        return True


def _pigre_attivo():
    try:
        import streamlit as _st_pg
        return str(_st_pg.secrets.get("CARICAMENTO_PROGRESSIVO", "si")).strip().lower() not in ("no", "off", "0", "spento")
    except Exception:
        return True


def _compila_con_schede_pigre(_testo, _percorso, _nomi):
    import ast as _ast
    _albero = _ast.parse(_testo, _percorso)

    class _Pigra(_ast.NodeTransformer):
        def visit_With(self, n):
            self.generic_visit(n)
            if len(n.items) == 1 and n.items[0].optional_vars is None and isinstance(n.items[0].context_expr, _ast.Name) and n.items[0].context_expr.id in _nomi and n.body:
                _guardia = _ast.If(test=_ast.Call(func=_ast.Name(id="_tab_aperta", ctx=_ast.Load()), args=[_ast.Name(id=n.items[0].context_expr.id, ctx=_ast.Load())], keywords=[]), body=n.body, orelse=[])
                n.body = [_ast.copy_location(_guardia, n.body[0])]
            return n
    _albero = _Pigra().visit(_albero)
    _ast.fix_missing_locations(_albero)
    return compile(_albero, _percorso, "exec")


def _carica(percorso):
    with open(percorso, encoding="utf-8") as _f:
        _testo = _f.read()
    _punti = _AGGANCI.get(os.path.basename(percorso))
    if _punti:
        _testo = _testo.replace("\r\n", "\n")
        for _cerca, _sostituisci in _punti:
            if _testo.count(_cerca) == 1:
                _testo = _testo.replace(_cerca, _sostituisci)
            else:
                import streamlit as _st
                _st.sidebar.caption("⚠️ Farmacia: punto di aggancio non trovato in " + os.path.basename(percorso))
    _nomi_pigri = _TABS_PIGRE.get(os.path.basename(percorso)) if _pigre_attivo() else None
    _chiave = (percorso, _hashlib_cc.md5(_testo.encode("utf-8")).hexdigest(), bool(_nomi_pigri))
    _codice = _MEMORIA_CODICE.codice.get(_chiave)
    if _codice is None:
        _codice = _compila_con_schede_pigre(_testo, percorso, _nomi_pigri) if _nomi_pigri else compile(_testo, percorso, "exec")
        for _vecchia in [k for k in _MEMORIA_CODICE.codice if k[0] == percorso]:                  # di ogni file si tiene solo l'ultima versione
            del _MEMORIA_CODICE.codice[_vecchia]
        _MEMORIA_CODICE.codice[_chiave] = _codice
    exec(_codice, globals())


import streamlit as _st_pos
_SEZ_VALIDE = {"salute", "documenti", "archivio", "casa", "lavoro", "utilita"}
if not _st_pos.session_state.get("_pos_letta"):                       # sessione nuova (primo avvio, o la pagina è stata ripresa dopo una pausa): si torna alla sezione in cui eri
    _st_pos.session_state["_pos_letta"] = True
    try:
        _s_url = _st_pos.query_params.get("s")
        if _s_url in _SEZ_VALIDE and "farmacia_aperta" not in _st_pos.session_state:
            _st_pos.session_state["farmacia_aperta"] = True
            if _s_url != "salute":
                _st_pos.session_state["sezione_home"] = _s_url
    except Exception:
        pass

# CARICAMENTO A PROVA DI GUASTO: se una parte non essenziale dell'app non si carica (per esempio dopo un aggiornamento di Streamlit), le altre continuano a funzionare e l'amministratore
# vede un avviso nella barra laterale e in Utilità → «Controllo tecnico». Le quattro parti essenziali (parte1-4) invece, se si rompono, fermano l'app come prima.
_MODULI_FALLITI = []
_ESSENZIALI_CC = {"parte1.py", "parte2.py", "parte3.py", "parte4.py"}


def _carica_sicuro(_p):
    try:
        _carica(_p)
    except Exception as _e_cs:                                  # le interruzioni di Streamlit (stop, rerun) non sono «Exception»: passano
        if os.path.basename(_p) in _ESSENZIALI_CC:
            raise
        _MODULI_FALLITI.append((os.path.basename(_p), type(_e_cs).__name__ + ": " + str(_e_cs)[:160]))


for _nome in ("parte1.py", "parte2.py", "aggiunte.py", "categorie.py", "interattivi.py", "hero_foto.py", "stile.py", "spesa.py", "statistiche.py", "elimina.py", "stile2.py", "posto.py", "account.py", "dispensa_famiglia.py", "foto_prodotto.py", "modifica.py", "bugiardino.py", "guida.py", "volantini.py", "farmacia.py", "info_sezioni.py", "ricerca_paesi.py", "tabella_intera.py", "famiglia.py", "invio.py", "scanner_medicinali.py", "navigazione.py", "archivio.py", "trasferimento.py", "assistente_ai.py", "utilita.py", "assistente.py", "casa.py", "sezioni.py", "pagine_nav.py", "nomi_utenti.py", "musica.py", "salute_catalogo.py", "salute_plus.py", "salute_esenzioni.py", "salute_scorte.py", "salute_prenotazioni.py", "salute_profilo.py", "salute_terapie_intervalli.py", "salute_tutto.py", "salute_rilettura.py", "controllo_tecnico.py", "avvisi_prova.py", "casa_amministrazione.py", "auto_emergenza.py", "auto.py", "auto_pagine.py", "auto_diagnosi.py", "auto_soccorso.py", "auto_base.py", "auto_proposte.py", "auto_archivio.py", "libretto.py", "diagnostica_spie.py", "diagnostica_dtc.py", "diagnostica_ble.py", "diagnostica.py", "lavoro.py", "scambio.py", "pensiero.py", "libera_spazio.py", "intestazioni.py", "immagini_sicure.py", "cestino.py", "guida_extra.py", "assistente_extra.py", "accessibilita.py",
              "guida_en.py", "guida_es.py", "guida_fr.py", "guida_de.py", "guida_ro.py", "guida_ar.py"):
    _carica_sicuro(os.path.join(_cartella, _nome))
for _percorso in sorted(glob.glob(os.path.join(_cartella, "lingue*.py"))):
    _carica_sicuro(_percorso)
try:
    for _nome in ("parte3.py", "parte4.py", "avvisi.py", "voce.py", "fotocamera.py", "volantini_fine.py"):
        _carica_sicuro(os.path.join(_cartella, _nome))
finally:
    if "fd_ripristina" in globals():
        fd_ripristina()                                   # a fine pagina il percorso torna sempre quello personale
_st_pos.session_state["_moduli_falliti"] = list(_MODULI_FALLITI)
if _MODULI_FALLITI and (_st_pos.session_state.get("sess") or {}).get("admin"):
    try:
        _st_pos.sidebar.warning("⚠️ " + str(len(_MODULI_FALLITI)) + " parti dell'app non si sono caricate (il resto funziona): " + ", ".join(n_ for n_, _e in _MODULI_FALLITI[:4]) + ". Vedi Utilità → Controllo tecnico.")
    except Exception:
        pass
try:                                                      # la sezione in cui sei si scrive nell'indirizzo (senza ridisegnare): serve a ritrovarla se la pagina riparte
    if "sess" in _st_pos.session_state:
        _sez_ora = "dispensa" if not _st_pos.session_state.get("farmacia_aperta") else (_st_pos.session_state.get("sezione_home") or "salute")
        if _st_pos.query_params.get("s") != _sez_ora:
            _st_pos.query_params["s"] = _sez_ora
except Exception:
    pass
