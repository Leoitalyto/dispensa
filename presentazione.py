# -*- coding: utf-8 -*-
"""📘 PRESENTAZIONE COMPLETA DI VITAMEMO — si apre dal pulsante rosso «Clicca per informazioni» (in ogni pagina e in Home), in 8 lingue.
Contiene anche i due capitoli nuovi del giro del robottino (Spesa Smart e Scadenziario). Le traduzioni sono in presentazione_lingue.py.
Caricato da app_dispensa.py dopo guida_agg_*.py (prefisso pr_)."""
import streamlit as st

PR_VERSIONE = "5.3"
PR_IT = [
    ("🌍 Cos'è VitaMemo",
     "VitaMemo tiene **in ordine la vita di tutta la famiglia in una sola app**: la spesa e la dispensa, la salute, i documenti, la casa, il lavoro, l'auto, "
     "gli animali, le scadenze, i compleanni. Funziona **dal telefono**, è in **8 lingue** e ti avvisa da sola quando qualcosa sta per scadere. "
     "Non serve essere esperti: ogni pagina ha il pulsante rosso **«Clicca per informazioni»** e il **robottino** che spiega a voce."),
    ("🏠 La Home e i pulsanti",
     "Dalla **Home** entri in ogni parte con un tocco: **Dispensa, Salute, I miei documenti, Archivio, Casa, Lavoro, Auto, Animali, Chat, Utilità**, e sotto "
     "**🛒 Spesa Smart** e **🗓️ Scadenziario**. Un pulsante che **pulsa con un numero** ti dice dove c'è qualcosa da guardare. Dentro ogni sezione, in alto, "
     "i pulsanti colorati ti portano subito nelle altre; il pulsante **🌐 VitaMemo · Home** ti riporta all'inizio."),
    ("🥫 Dispensa (Scorte)",
     "I prodotti di casa con **foto e codice a barre** (nome, marca, ingredienti e allergeni arrivano da soli), **scadenze a colori**, posto (frigo, freezer, "
     "dispensa), **allergie** di ognuno. Quando un prodotto **finisce** va da solo nella **lista della spesa**. C'è anche la **dispensa di famiglia** condivisa, "
     "con chi può modificare o solo guardare e lo storico di chi ha fatto cosa."),
    ("🛒 Spesa Smart",
     "Salvi i **prezzi** dei negozi in **3 tocchi** (anche col codice a barre) e l'app calcola il prezzo **al kg, al litro o al pezzo**. Ti dice **dove costa meno**, "
     "quali **offerte** convengono davvero (mai un prezzo vecchio o un'offerta finita), prepara la **spesa ottimizzata** (un negozio, due o tre, la più economica) "
     "e legge gli **scontrini** con l'intelligenza artificiale. Le **liste della spesa** si possono **condividere con persone scelte**."),
    ("🩺 Salute",
     "Una cartella per **ogni persona della famiglia**: medicinali con scadenze e scorte, **terapie con gli orari**, ricette, visite, vaccini, esami e **documenti "
     "sanitari letti dall'IA** (numerati, il N° 1 è il più recente), controlli periodici, esenzioni, **dati per l'emergenza** e la **scheda per il medico in PDF**. "
     "Con **📖 Cos'è?** ti spiega in parole semplici una parola difficile."),
    ("📁 I miei documenti e 🗂️ Archivio",
     "Carta d'identità, patente, passaporto, tessera sanitaria con **avviso prima della scadenza**: fai la foto e i dati si scrivono da soli, controllati "
     "(codice fiscale, numeri, date). L'**Archivio** raccoglie tutti i file dell'app; con **🔎 Cerca in tutti i documenti** trovi un documento anche da quello "
     "che c'è scritto dentro."),
    ("🏡 Casa",
     "Più case (anche quella della mamma, con la sua **amministrazione** e il condominio), **bollette** con avviso prima di pagarle, **manuali, garanzie e "
     "manutenzioni** degli apparecchi, posta in arrivo, **conti della casa**, la **badante** con i conti automatici. Il **📞 Numeri utili** ha anche il "
     "**biglietto da visita fotografato**."),
    ("💼 Lavoro",
     "**Buste paga** lette da sole, Certificazione Unica, documenti INPS (anche ECOCERT), **controllo delle ore** con i **giorni di festa** e il patrono della "
     "tua città, per capire se ti pagano il giusto."),
    ("🚗 Auto e 🐾 Animali",
     "**Auto**: bollo, assicurazione, revisione, tagliando, gomme, patente e multe, consumi e spese, spie del cruscotto e aiuto in caso di guasto o incidente. "
     "**Animali**: libretto, vaccini e richiami, visite, terapie, microchip e il **report per il veterinario**."),
    ("🗓️ Scadenziario",
     "Il **centro di controllo** di tutte le scadenze: raccoglie **da solo** quelle di ogni sezione (senza doppioni: se cambi una data nella sezione cambia anche "
     "qui), più **le tue scadenze personali** con ricorrenze. Vedi a colpo d'occhio **scadute, oggi, 7 e 30 giorni**; con **✅ Fatto** e **⏰ Rinvia** le gestisci "
     "in un tocco. Puoi seguire anche le scadenze delle **persone che segui** (es. la mamma)."),
    ("🔔 Avvisi anche ad app chiusa",
     "Gli avvisi arrivano su **Telegram, email, WhatsApp o SMS**: scadenze, medicine da prendere, bollette, controlli, compleanni, raccolta differenziata, "
     "badante e il **riepilogo del mattino**. Ogni attività dello Scadenziario può avere **i suoi avvisi** (giorni, ore o minuti prima). Con **📅 Calendario "
     "del telefono** gli allarmi suonano anche senza internet."),
    ("🤖 Intelligenza artificiale",
     "L'IA **legge i documenti e le foto** (referti, bollette, carte d'identità, scontrini, biglietti da visita), propone **tipo, date, importi e di chi è** il "
     "documento e **dove va** (la mamma, la sua casa, la sua salute). **Niente cambia senza la tua conferma**, e se la correggi **impara**. La foto viene "
     "raddrizzata da sola e, se è mossa o buia, l'app te lo dice."),
    ("👨‍👩‍👧 Famiglia e persone",
     "Ogni persona ha la sua **password** e vede solo le sue cose. L'amministratore aggiunge persone, sceglie cosa possono vedere e condividere. "
     "Ci sono la **💬 Chat** con l'amministratore, i **profili familiari** (in Salute, Casa e Scadenziario) e lo **📦 scambio dati** con un'altra persona."),
    ("🧰 Utilità",
     "**Compleanni** con il **diario dei ricordi**, **avvisi meteo**, strumenti per i **PDF**, impostazioni dell'aspetto (testi più grandi, lato della freccia), "
     "le chiavi dell'intelligenza artificiale, il **controllo tecnico**, la **radio** di sottofondo e tanto altro."),
    ("🌐 Lingue, guida e robottino",
     "L'app è in **italiano, inglese, spagnolo, francese, tedesco, portoghese, rumeno e arabo**: la lingua si sceglie all'ingresso e il telefono la ricorda. "
     "Il **robottino** in basso a destra fa il **giro completo** dell'app a voce e risponde alle domande (anche col microfono); il pulsante rosso apre la "
     "**guida** di ogni pagina con la ricerca."),
    ("🔒 Sicurezza e privacy",
     "Password mai salvate in chiaro, **accesso ricordato** senza la password nel link, «📵 esci da tutti i telefoni», **cestino** per recuperare quello che "
     "elimini per sbaglio, **storico** delle modifiche. Nessuna pubblicità, nessun abbonamento: i tuoi dati restano tuoi."),
    ("💡 Come iniziare",
     "1. Scegli la lingua ed entra. 2. In **Utilità → 🔔 Avvisi** scegli dove ricevere i messaggi. 3. Aggiungi le **persone** che segui in **Salute**. "
     "4. Fotografa i primi **documenti** e qualche **prodotto**. 5. Apri lo **🗓️ Scadenziario** e accendi il **riepilogo del mattino**. "
     "Per ogni dubbio: pulsante rosso o robottino."),
]
PR_UI_IT = {"bottone": "📘 Presentazione completa di VitaMemo", "titolo": "📘 VitaMemo: tutto quello che puoi fare", "torna": "← Torna alla guida",
            "intro": "Una panoramica completa dell'app, sezione per sezione. Tocca un titolo per aprirlo.", "apri_tutto": "Apri tutto"}
PR_TR = {}                # lingua → [(titolo, testo)] nello stesso ordine di PR_IT   (presentazione_lingue.py)
PR_UI = {}                # lingua → {chiave: testo}


def pr_lingua():
    try:
        return lingua()
    except Exception:
        return "it"


def pr_testi(lg=None):
    lg = lg or pr_lingua()
    tr = PR_TR.get(lg) if lg != "it" else None
    if tr and len(tr) == len(PR_IT):
        return tr
    return PR_IT


def pr_u(k, lg=None):
    lg = lg or pr_lingua()
    return (PR_UI.get(lg) or {}).get(k) or PR_UI_IT[k]


def pr_pagina(sezione):
    """La presentazione (dentro la finestra della guida)."""
    lg = pr_lingua()
    if lg == "ar":
        st.markdown("<style>[data-testid='stDialog'] [data-testid='stVerticalBlock']{direction:rtl;text-align:right}</style>", unsafe_allow_html=True)
    if st.button(pr_u("torna"), key=f"pr_torna_{sezione}", width="stretch"):
        st.session_state["pr_aperta"] = False
        st.rerun(scope="fragment")
    st.markdown(f"### {pr_u('titolo')}")
    st.caption(pr_u("intro") + f" · v{PR_VERSIONE}")
    tutto = st.toggle(pr_u("apri_tutto"), key=f"pr_tutto_{sezione}")
    for i, (t, x) in enumerate(pr_testi(lg)):
        if tutto:                                                   # tutto aperto: testo continuo, da leggere scorrendo
            st.markdown(f"#### {t}")
            st.markdown(x)
        else:
            with st.expander(t, expanded=i == 0):
                st.markdown(x)


# ---- il pulsante in cima alla finestra «Clicca per informazioni»
try:
    _pr_corpo_prima = getattr(_dialogo_info, "__wrapped__", None)
except NameError:
    _pr_corpo_prima = None

if _pr_corpo_prima is not None and "_pr_fatto" not in globals():
    _pr_fatto = True
    _pr_titolo_dlg = UI_IT.get("dlg_titolo", "📖 Guida e informazioni") if "UI_IT" in globals() else "📖 Guida e informazioni"

    def _pr_corpo(sezione):
        if st.session_state.get("pr_aperta"):
            pr_pagina(sezione)
            return
        st.markdown("<style>.st-key-pr_apri button{min-height:56px !important;border-radius:18px !important;background:linear-gradient(135deg,#0b1f4a,#1565c0 60%,#42a5f5) !important;"
                    "border:2px solid #90caf9 !important;box-shadow:0 0 14px rgba(66,165,245,.6) !important}.st-key-pr_apri button p{color:#fff !important;font-weight:900 !important;"
                    "font-size:1.05rem !important}</style>", unsafe_allow_html=True)
        with st.container(key="pr_apri"):
            if st.button(pr_u("bottone"), key=f"pr_apri_{sezione}", width="stretch"):
                st.session_state["pr_aperta"] = True
                st.rerun(scope="fragment")
        _pr_corpo_prima(sezione)

    _pr_dialoghi = {}

    def _dialogo_info(sezione):                                     # noqa: F811 — il titolo della finestra nella lingua scelta
        try:
            tit = _u("dlg_titolo") or _pr_titolo_dlg
        except Exception:
            tit = _pr_titolo_dlg
        if tit not in _pr_dialoghi:
            _pr_dialoghi[tit] = st.dialog(tit, width="large")(_pr_corpo)
        return _pr_dialoghi[tit](sezione)

    _dialogo_info.__wrapped__ = _pr_corpo

    if "pulsante_info" in globals() and "_pr_pulsante_prima" not in globals():
        _pr_pulsante_prima = pulsante_info

        def pulsante_info(sezione):                                  # noqa: F811 — la finestra si apre sempre dalla guida, non dalla presentazione
            if st.session_state.get(f"ginfo_btn_{sezione}"):          # tocco sul pulsante rosso: si riapre sempre dalla guida
                st.session_state["pr_aperta"] = False
            return _pr_pulsante_prima(sezione)


# ---- la scheda nella guida di Home/Utilità e la novità
try:
    if "_GUIDE" in globals() and "_ID_GUIDA" in globals():
        for _sez in ("dispensa", "utilita"):
            _ids = _ID_GUIDA.setdefault(_sez, [])
            if "x_presentazione" not in _ids:
                _ids.insert(0, "x_presentazione")
                _GUIDE.setdefault(_sez, []).insert(0, ("📘 Presentazione completa di VitaMemo",
                                                        "In cima a questa finestra c'è il pulsante blu **📘 Presentazione completa di VitaMemo**: spiega **tutta l'app**, sezione per "
                                                        "sezione (Dispensa, Spesa Smart, Salute, Documenti, Casa, Lavoro, Auto, Animali, Scadenziario, avvisi, intelligenza "
                                                        "artificiale, famiglia, Utilità, lingue, sicurezza) e **come iniziare**. È in tutte le 8 lingue.",
                                                        "presentazione completa app funzioni possibilità panoramica cosa fa vitamemo"))
except Exception:
    pass


# ---- i capitoli nuovi del giro del robottino
try:
    if "AG_CAPITOLI" in globals() and not any(c.get("id") == "g_spesa_smart" for c in AG_CAPITOLI):
        _i = next((i for i, c in enumerate(AG_CAPITOLI) if c.get("id") == "g_dispensa2"), 4) + 1
        AG_CAPITOLI.insert(_i, {"id": "g_spesa_smart", "s": "spesa_smart", "t": "Spesa Smart: dove costa meno",
                                "x": "Spesa Smart è la seconda parte della Dispensa. Salvi i prezzi dei negozi in pochi tocchi, anche con il codice a barre, e l'app ti dice dove costa meno, "
                                     "calcolando il prezzo al chilo, al litro o al pezzo. Ti mostra solo le offerte che convengono davvero, prepara la spesa ottimizzata in uno o più negozi "
                                     "e legge gli scontrini con l'intelligenza artificiale. Le liste della spesa si possono condividere con le persone che scegli.",
                                "d": "Dispensa → in alto «🛒 Spesa Smart», oppure il pulsante verde smeraldo sotto Dispensa.",
                                "k": "spesa smart prezzi negozi dove costa meno offerte scontrino lista ottimizzata confronto"})
    if "AG_CAPITOLI" in globals() and not any(c.get("id") == "g_scadenziario" for c in AG_CAPITOLI):
        _i = next((i for i, c in enumerate(AG_CAPITOLI) if c.get("id") == "g_utilita"), len(AG_CAPITOLI) - 1)
        AG_CAPITOLI.insert(_i, {"id": "g_scadenziario", "s": "scadenziario", "t": "Lo Scadenziario: tutte le scadenze insieme",
                                "x": "Lo Scadenziario raccoglie da solo le scadenze di tutte le sezioni: medicine, visite, documenti, bollette, condominio, auto, animali, appuntamenti e compleanni. "
                                     "In cima vedi quante sono scadute, quante sono per oggi, per i prossimi sette e trenta giorni. Con Fatto le segni completate, con Rinvia sposti solo l'avviso. "
                                     "Puoi aggiungere le tue scadenze personali, anche ripetute, scegliere gli avvisi e seguire anche le scadenze delle persone che segui.",
                                "d": "Il pulsante lampone «🗓️ Scadenziario», prima di Utilità.",
                                "k": "scadenziario scadenze tutte avvisi rinvia fatto personali ricorrenze riepilogo"})
except Exception:
    pass
