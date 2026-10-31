# Carica l'app (parte1.py, parte2.py, aggiunte.py, categorie.py, interattivi.py, hero_foto.py, stile.py, spesa.py, elimina.py, stile2.py, posto.py, account.py, foto_prodotto.py, modifica.py, bugiardino.py, guida.py, lingue*.py, parte3.py, parte4.py, avvisi.py, voce.py, fotocamera.py, farmacia.py, info_sezioni.py, utilita.py, assistente.py, guida_xx.py) come se fosse un unico file.
import glob
import os

_cartella = os.path.dirname(os.path.abspath(__file__))

# Punti in cui la Farmacia si aggancia alla Home (parte3.py). Ogni riga viene cercata UNA sola volta:
# se non la trova, la dispensa funziona lo stesso e la Farmacia semplicemente non compare.
_AGGANCI = {
    "farmacia.py": [
        # Home: l'icona «Casa» sulla stessa riga delle altre, tra «I miei documenti» e «Utilità» (casa_pulsante è in casa.py)
        ('        c1, c2, c3 = st.columns(3, gap="small")\n        premuto_u = False\n        with c3:\n            if uri_u:\n',
         '        c1, c2, c3, c4 = st.columns(4, gap="small")\n        premuto_u = False\n        premuto_c = False\n'
         '        with c3:\n            if "casa_pulsante" in globals():\n                premuto_c = casa_pulsante()\n'
         '        with c4:\n            if uri_u:\n'),
        ('    if premuto_u:\n',
         '    if premuto_c:\n        st.session_state["sezione_home"] = "casa"\n        st.session_state["farmacia_aperta"] = True\n        st.rerun()\n    if premuto_u:\n'),
    ],
    "parte3.py": [
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
         'if "pulsante_info" in globals():\n    pulsante_info("dispensa")\n'
         'if "fd_selettore" in globals():\n    fd_selettore()\n'),
    ],
    "parte4.py": [
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
         '                    fd_selettore_ruolo(u)\n'),
    ],
}


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
    exec(compile(_testo, percorso, "exec"), globals())


for _nome in ("parte1.py", "parte2.py", "aggiunte.py", "categorie.py", "interattivi.py", "hero_foto.py", "stile.py", "spesa.py", "statistiche.py", "elimina.py", "stile2.py", "posto.py", "account.py", "dispensa_famiglia.py", "foto_prodotto.py", "modifica.py", "bugiardino.py", "guida.py", "volantini.py", "farmacia.py", "info_sezioni.py", "ricerca_paesi.py", "tabella_intera.py", "famiglia.py", "invio.py", "scanner_medicinali.py", "navigazione.py", "archivio.py", "trasferimento.py", "assistente_ai.py", "utilita.py", "assistente.py", "casa.py",
              "guida_en.py", "guida_es.py", "guida_fr.py", "guida_de.py", "guida_ro.py", "guida_ar.py"):
    _carica(os.path.join(_cartella, _nome))
for _percorso in sorted(glob.glob(os.path.join(_cartella, "lingue*.py"))):
    _carica(_percorso)
try:
    for _nome in ("parte3.py", "parte4.py", "avvisi.py", "voce.py", "fotocamera.py", "volantini_fine.py"):
        _carica(os.path.join(_cartella, _nome))
finally:
    if "fd_ripristina" in globals():
        fd_ripristina()                                   # a fine pagina il percorso torna sempre quello personale
