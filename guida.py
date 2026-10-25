# -*- coding: utf-8 -*-
"""Guida completa dell'app ("bugiardino"): colori, simboli, pulsanti e come si fa ogni cosa.
Si apre dal pulsante Info di ogni prodotto e sta anche nella scheda Info. Caricato da app_dispensa.py dopo bugiardino.py."""


def _g(sample, testo):
    """Una riga della guida: il simbolo com'e' nell'app + la spiegazione."""
    return f"<div class='g-riga'><div class='g-ex'>{sample}</div><div class='g-testo'>{testo}</div></div>"


def _g_pill(stato, simbolo, testo):
    return f"<span class='g-pill' style='background:{COLORI[stato]}'><i class='g-ico'>{simbolo}</i>{html.escape(testo)}</span>"


def _g_btn(classe, testo):
    return f"<span class='g-btn {classe}'>{testo}</span>"


def _g_testo(righe):
    st.markdown("".join(righe), unsafe_allow_html=True)


def mostra_guida():
    """Il contenuto della guida (usato nella finestra Info e nella scheda Info)."""
    nomi = ["🚀 " + t("Primi passi"), "🎨 " + t("Colori e simboli"), "🔘 " + t("Pulsanti"), "➕ " + t("Aggiungere"),
            "📸 " + t("La foto"), "🛒 " + t("Spesa e consumo"), "👤 " + t("Account e allergie"), "🛟 " + t("Se qualcosa non va")]
    admin = bool(globals().get("e_admin"))
    if admin:
        nomi.append("🛠️ " + t("Per l'amministratore"))
    schede = st.tabs(nomi)

    with schede[0]:
        st.markdown(t("""**Che cos'è:** la tua dispensa in tasca. Tieni traccia di quello che hai in casa, di quando scade e di cosa contiene (allergeni, ingredienti), e l'app ti avvisa prima che qualcosa vada a male.

**In 5 passi:**
1. **➕ Aggiungi** un prodotto: fotografalo, scrivi il codice a barre (i numeri sotto le barre) e l'app compila il resto.
2. **📅 Scrivi** quante unità hai e la scadenza.
3. **🔔 Aspetta gli avvisi:** arancione se scade entro 2 mesi, rosso entro 1 mese, scuro se è già scaduto.
4. **🌾 Segnala le tue allergie** nel menu a sinistra (la freccia **»** in alto a sinistra lo apre).
5. **🛒 Quando un prodotto finisce** va da solo nella lista della spesa.

La dispensa è **solo tua**: ogni persona ha la sua password e nessuno vede i prodotti degli altri.

**Le tre sezioni della pagina Dispensa:** 🧑 *Adulti*, 👶 *Neonati* (0-2 anni) e 🐾 *Animali*. Scegli per chi è il prodotto quando lo aggiungi."""))
        st.markdown("**" + t("Le schede in basso") + "**")
        _g_testo([
            _g("<b>🏠</b>", t("<b>Dispensa</b>: i tuoi prodotti, i contatori e gli avvisi.")),
            _g("<b>➕</b>", t("<b>Aggiungi</b>: inserisci un nuovo prodotto.")),
            _g("<b>✏️</b>", t("<b>Gestisci</b>: cambia in un colpo solo quantità, scadenze e note di tanti prodotti.")),
            _g("<b>🛒</b>", t("<b>Spesa</b>: la lista di quello che devi comprare.")),
            _g("<b>✉️ / 💬</b>", t("<b>Messaggi / Suggerimenti</b>: scrivi un'idea o un problema all'amministratore.")),
            _g("<b>ⓘ</b>", t("<b>Info</b>: questa guida.")),
        ])

    with schede[1]:
        st.markdown("**" + t("La scadenza") + "**")
        _g_testo([
            _g(_g_pill("ok", "✓", t("Scade tra 120 giorni")), t("Verde: manca più di 2 mesi. Tutto tranquillo.")),
            _g(_g_pill("arancione", "!", t("Scade tra 40 giorni")), t("Arancione: scade entro 2 mesi. Conviene usarlo.")),
            _g(_g_pill("rosso", "!", t("Scade tra 9 giorni")), t("Rosso: scade entro 1 mese. Usalo presto.")),
            _g(_g_pill("scaduto", "✕", t("Scaduto da 3 giorni")), t("Scuro: è già scaduto. Controllalo o buttalo.")),
            _g(_g_pill("nessuna", "–", t("Senza scadenza")), t("Grigio: non hai indicato una scadenza.")),
        ])
        st.markdown("**" + t("I contatori in cima") + "**")
        st.markdown(t("**Prodotti** (tutti), **Entro 2 mesi**, **Entro 1 mese** e **Scaduti**: ti dicono a colpo d'occhio quanti prodotti sono in ogni situazione."))
        st.markdown("**" + t("Gli avvisi") + "**")
        st.markdown(t("""Sotto i contatori compaiono le liste ⚫ *Scaduti: da buttare o controllare*, 🔴 *Scadono entro 1 mese* e 🟠 *Scadono entro 2 mesi*. All'apertura l'app può anche suonare: un *din-don* per gli adulti, un suono dedicato per neonati e per animali."""))
        st.markdown("**" + t("Allergeni e simboli sulla scheda") + "**")
        _g_testo([
            _g("<span class='allerg-btn'>Glutine</span>", t("<b>Giallo</b>: il prodotto contiene questo allergene. Toccalo per leggere la composizione.")),
            _g("<span class='allerg-btn traccia'>" + t("Tracce di latte") + "</span>", t("<b>Arancione</b>: può contenere tracce di questo allergene.")),
            _g("<span class='allerg-btn mio'>⚠️ " + t("Contiene") + " Glutine</span>", t("<b>Rosso lampeggiante</b>: contiene un allergene che hai segnalato tu. Attenzione!")),
            _g("<span class='badge'>❔ " + t("Allergeni non verificati") + "</span>", t("Non ci sono informazioni sugli allergeni: leggi l'etichetta.")),
            _g("<div class='allerg-riga'><span class='badge bene'>🌾 " + t("Senza glutine") + "</span></div>", t("Il prodotto è dichiarato senza glutine.")),
            _g("<span class='allerg-btn veg'>" + t("Vegano") + "</span><span class='allerg-btn vegt'>" + t("Vegetariano") + "</span>",
               t("Compaiono solo se il prodotto è classificato così (dalla lista degli ingredienti: controlla sempre l'etichetta).")),
            _g("<span class='allerg-btn ingr'>ingredienti</span>", t("Apre il <b>bugiardino del prodotto</b>: ingredienti, allergeni, valori nutrizionali e altre informazioni.")),
        ])
        st.caption(t("Per chiudere una finestra aperta toccando un'etichetta usa il cerchio ✕ in basso."))

    with schede[2]:
        st.markdown("**" + t("Sotto ogni prodotto") + "**")
        _g_testo([
            _g(_g_btn("el", "🗑️ " + t("Elimina")), t("Apre la finestra per togliere il prodotto dalla dispensa.")),
            _g(_g_btn("in", "ⓘ " + t("Info")), t("Apre questa guida.")),
            _g(_g_btn("mo", "✏️ " + t("Modifica")), t("Cambia qualsiasi dato: foto, nome, marca, per chi è, dove lo tieni, codice a barre, quantità, contenuto, scadenza, note, allergeni e ingredienti.")),
        ])
        st.caption(t("Nome, foto e allergeni valgono per tutte le scadenze dello stesso prodotto; quantità, scadenza e note solo per la voce che stai modificando."))
        st.markdown("**" + t("Per trovare i prodotti") + "**")
        st.markdown(t("""- 🔎 **Cerca**: scrivi parte del nome o della marca.
- **Mostra**: *Tutti*, *Solo in scadenza (2 mesi)*, *Solo rossi (1 mese)* o *Scaduti*.
- **Vista**: *Schede* (grandi, con foto) oppure *Tabella* (tante righe in poco spazio: spunti le righe e poi **Elimina le righe spuntate** o **Modifica la riga spuntata**).
- 🔍 **Dettagli prodotto** (in fondo alla pagina): valori nutrizionali, ingredienti, prezzi segnalati e collegamenti per cercare online. Qui trovi anche **➖ Ne ho consumato uno** e **➕ Ne ho aggiunto uno**."""))
        st.markdown("**" + t("Nella scheda Gestisci") + "**")
        st.markdown(t("""Una tabella con tutti i prodotti: cambi quantità, scadenza e note direttamente nelle celle, spunti **🗑️** per eliminare e poi tocchi **💾 Salva modifiche**. Se metti **0 unità** il prodotto è finito e va nella lista della spesa. In fondo puoi scaricare l'elenco (CSV)."""))

    with schede[3]:
        st.markdown(t("""**Aggiungere un prodotto, passo per passo** (scheda ➕ Aggiungi):

1. **📸 Foto del prodotto**: tocca *Scatta la foto* (si apre la fotocamera posteriore) oppure *Carica dal telefono*.
2. **Codice a barre**: scrivilo a mano (i numeri sotto le barre, di solito 13). L'app cerca il prodotto e compila nome, marca, contenuto, ingredienti e allergeni.
3. **Dati del prodotto**: controlla il nome, scegli *per chi è* (adulti, neonati, animali) e *dove lo metti* (dispensa, frigo...).
4. **Quante unità hai** e **scadenza**. Se lo stesso prodotto ha scadenze diverse, aggiungilo più volte: l'app le tiene separate.
5. **Note** (facoltative) e allergeni: se il prodotto non è stato trovato puoi indicarli a mano.
6. Tocca il pulsante per **salvare**.

Non hai il codice o il prodotto non c'è? Va bene lo stesso: bastano **nome, unità e scadenza**."""))
        st.info("🎤 " + t("In molti campi di testo c'è un'icona microfono: toccala, parla e il testo compare. Il browser ti chiede il permesso di usare il microfono."))

    with schede[4]:
        st.markdown(t("""**La foto in home** è ritagliata e raddrizzata dall'app: toglie lo sfondo e mette in bolla le scritte.

**Per un buon risultato:** appoggia il prodotto su un piano liscio e di un solo colore, con buona luce, tenendo il telefono fermo e il prodotto al centro. Evita tovaglie a disegni attaccate al prodotto.

**Se vuoi sistemarla a mano** (come l'editor foto del telefono):
- 🎚️ **Righello**: trascinalo a destra o a sinistra per ruotare. Servono per i ritocchi anche i tasti **−0,5°** e **+0,5°**.
- ✂️ **Cornice**: trascina gli angoli e i lati per tagliare; spostala dall'interno.
- 💾 **Salva posizione e ritaglio**: tocca quando vedi la sistemazione migliore. Solo allora l'anteprima sotto cambia.
- ↺ **Ripristina**: torna alla foto di partenza.

Dopo aver ruotato la cornice torna intera: prima raddrizza, poi ritaglia."""))

    with schede[5]:
        st.markdown(t("""**🛒 Lista della spesa**
- I prodotti **finiti** (0 unità) ci finiscono da soli. Quando li aggiungi di nuovo in dispensa escono dalla lista.
- Puoi aggiungere a mano quello che devi comprare con *Aggiungi alla lista*.
- Spunta **Preso** quando l'hai comprato, poi **Togli quelli presi** per ripulire.

**➖ / ➕ Consumo:** in *Dettagli prodotto* tocca **Ne ho consumato uno** per scalare un'unità (se era l'ultima finisce nella spesa) o **Ne ho aggiunto uno** per aumentarla."""))

    with schede[6]:
        st.markdown(t("""**Il menu a sinistra** (apri con **»**):
- **Esci**: chiude l'accesso su questo telefono.
- **❓ Come si usa**: rivedi la presentazione iniziale.
- **🔑 Cambia password**: la scegli tu quando vuoi.
- **Lingua**: italiano, inglese, spagnolo, francese, tedesco, rumeno, arabo.
- **🌾 Allergie**: indica gli allergeni da evitare; i prodotti che li contengono si accendono di rosso.
- **👶 Allergie del neonato**: lista separata, usata per la sezione Neonati.
- **Mostra solo prodotti sicuri per me**: nasconde i prodotti con i tuoi allergeni e quelli senza informazioni.
- **🔄 Aggiorna**: ricarica i dati.

**💾 Dati salvati su GitHub** vuol dire che i tuoi prodotti restano anche se l'app si riavvia. Con la scritta **Modalità prova** i dati si cancellano al riavvio."""))
        st.warning(t("Allergeni e ingredienti arrivano da Open Food Facts, un database compilato dagli utenti: possono essere incompleti o non aggiornati. Fa fede sempre l'etichetta sulla confezione."))

    with schede[7]:
        st.markdown(t("""**Non vedo i miei prodotti o sono vecchi** → tocca **🔄 Aggiorna** nel menu a sinistra.

**Il codice a barre non trova il prodotto** → compila a mano nome, unità e scadenza: funziona lo stesso.

**La foto non viene scontornata bene** → rifai la foto su un piano liscio e chiaro, oppure usa il righello e la cornice per sistemarla e tocca *Salva posizione e ritaglio*.

**La fotocamera non si apre** → controlla che il browser abbia il permesso di usare la fotocamera; in alternativa usa *Carica dal telefono*.

**Gli ingredienti sono in un'altra lingua** → l'app li traduce da sola; se il servizio di traduzione non risponde restano nella lingua originale.

**Ho sbagliato qualcosa** → tocca **Modifica** sul prodotto e correggi.

**Altro** → scrivi nella scheda **Suggerimenti**: la legge l'amministratore."""))

    if admin:
        with schede[8]:
            st.markdown(t("""**Dare l'app a una persona:**
1. Vai nella scheda **👥 Utenti**, scrivi il nome e scegli la lingua, poi **Crea utente e genera password**.
2. Copia il **messaggio pronto** (contiene link e password) e mandalo, per esempio su WhatsApp. La password si vede **una sola volta**.
3. Il **link è sempre lo stesso per tutti**: cambia solo la password.
4. Tocca **Fatto, ho mandato tutto: crea un altro utente** per prepararti al prossimo.

**Per ogni utente:** *Nuova password* (se l'ha persa), *Blocca / Riattiva*, e puoi vedere l'ultimo accesso. Non vedi le dispense degli altri.

**✉️ Messaggi:** i suggerimenti degli utenti arrivano qui con il numero dei nuovi messaggi tra parentesi; puoi rispondere.

La password dell'amministratore si cambia in *Streamlit → Settings → Secrets* (`admin_password`)."""))


def apri_guida():
    """Il pulsante Info: apre la guida completa in una finestra."""
    st.dialog("📖 " + t("Guida completa dell'app"), width="large")(mostra_guida)()


CSS = CSS.replace("</style>", """
.g-riga{display:flex;gap:12px;align-items:center;margin:9px 0;flex-wrap:wrap}
.g-ex{flex:0 0 auto;max-width:100%;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.g-testo{flex:1 1 200px;font-weight:600;line-height:1.35}
.g-pill{display:inline-flex;align-items:center;gap:8px;padding:6px 16px 6px 7px;border-radius:999px;color:#fff;font-weight:800;box-shadow:0 5px 12px rgba(0,0,0,.18)}
.g-ico{width:26px;height:26px;border-radius:50%;border:2px solid #fff;display:inline-flex;align-items:center;justify-content:center;font-style:normal;font-size:.85rem}
.g-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 20px;border-radius:999px;font-weight:800;background:rgba(255,255,255,.85);border:2px solid}
.g-btn.el{color:#b91c1c;border-color:rgba(185,28,28,.35)}.g-btn.in{color:#1d4ed8;border-color:rgba(37,99,235,.4)}.g-btn.mo{color:#0f766e;border-color:rgba(13,148,136,.4)}
[class*="st-key-info_"] button{width:100%;min-height:52px;border-radius:999px !important;background:rgba(255,255,255,.78) !important;color:#1d4ed8 !important;
 border:2px solid rgba(37,99,235,.35) !important;font-weight:800 !important;box-shadow:0 8px 18px rgba(0,40,100,.1)}
[class*="st-key-info_"] button p{font-weight:800 !important;color:#1d4ed8 !important}
[class*="st-key-info_"] button:hover{background:#dbeafe !important}
</style>""")
