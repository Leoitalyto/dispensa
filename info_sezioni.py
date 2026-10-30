# -*- coding: utf-8 -*-
"""Pulsante «Informazioni» (immagine info.webp) per Dispensa, Farmacia e Documenti.
Toccandolo si apre una guida con caselle a discesa (una per argomento) e un campo di ricerca:
si scrive una domanda e l'app mostra le spiegazioni più adatte.
Caricato da app_dispensa.py insieme a farmacia.py. Se manca info.webp il pulsante resta, ma senza immagine."""
import base64
import html
import os
import re
import unicodedata

import streamlit as st

_NOMI_SEZIONI = {"dispensa": "🏠 Dispensa", "farmacia": "🏥 Farmacia", "documenti": "📁 I miei documenti",
                  "utilita": "🧰 Utilità"}

# ---------------------------------------------------------------------
# I TESTI DELLE GUIDE: (titolo, spiegazione, parole utili per la ricerca)
# ---------------------------------------------------------------------
# Nome (ed eventuale link) del bot Telegram dell'app: scrivi qui il link vero, per esempio "https://t.me/NomeDelTuoBot"
_BOT_NOME = "Dispensa Leo"
_BOT_LINK = "https://t.me/dispensa_leo_bot"

_BOT_RIGA = (f"**{_BOT_NOME}**" if not _BOT_LINK else f"**{_BOT_NOME}** (tocca [questo link]({_BOT_LINK}))")

_TESTO_TELEGRAM = f"""**Cosa serve:** l'app Telegram sul telefono e due minuti di tempo. Telegram è gratuito.

1. **Installa Telegram** dal Play Store (Android) o dall'App Store (iPhone) e crea il tuo account: ti chiede il numero di cellulare.
2. **Apri il bot dell'app.** Dentro Telegram tocca la lente 🔍 in alto e cerca {_BOT_RIGA}.
3. Tocca **Avvia** (oppure scrivi `/start`). **Questo passaggio è importante:** se non lo fai, il bot non può scriverti.
4. **Scopri il tuo numero (Chat ID).** Cerca il bot **@userinfobot**, aprilo e tocca **Avvia**: ti risponde con il tuo **Id**, un numero (per esempio `123456789`). Tienilo premuto per copiarlo. È un bot gratuito che ti dice solo quel numero.
5. **Torna in questa pagina.** Apri **🔔 Scegli come ricevere gli avvisi**, spunta **📱 Telegram**, incolla il numero nel campo **Chat ID** (solo numeri) e tocca **Salva**.
6. **Fatto.** Gli avvisi arrivano da quel bot, a partire dal prossimo invio automatico (di solito la mattina dopo).

**Se non arriva nulla:** controlla di aver toccato *Avvia* nel bot (passo 3) e che il numero sia giusto, senza spazi né lettere."""

_TESTO_EMAIL = """**Per l'email è semplicissimo: basta il tuo indirizzo.** Non servono password né altre impostazioni.

1. Apri **🔔 Scegli come ricevere gli avvisi**.
2. Spunta **✉️ Email**.
3. Scrivi il **tuo indirizzo email** nel campo (per esempio `nome@gmail.com`) e controlla che sia giusto.
4. Tocca **Salva**.

I messaggi partono dall'indirizzo email dell'app. **La prima volta guarda anche in Spam o Promozioni** e, se lo trovi lì, segnalo come «Non è spam»: da quel momento arriverà nella posta normale."""

_GUIDE = {
    "dispensa": [
        ("🤖 L'assistente digitale (il robottino)",
         """È il **robottino giallo e blu** in basso a destra, con la faccia rotonda. **Toccalo** e si apre il suo pannello.

Che cosa sa fare:
- **📖 Spiegami questa pagina**: ti racconta a voce a cosa serve la pagina in cui sei.
- **🧭 Giro guidato**: ti spiega tutta l'app passo per passo (Avanti e Indietro).
- **🆕 Cosa c'è di nuovo**: ti dice le novità e dove trovarle.
- **🎤 Fai una domanda**: tocca, parla (per esempio «come aggiungo una foto al documento?») e ti risponde con la guida. Funziona su Chrome per Android.
- Puoi anche **scrivere** la domanda nella casella.

**Voce:** usa la voce del telefono. Se non vuoi sentirlo, tocca **🔊 Voce: attiva** per spegnerla.

**Per disattivarlo:** tocca **⛔ Disattiva assistente** nel suo pannello. Per riattivarlo apri il pulsante rosso **Clicca per informazioni** e tocca **✅ Attiva** nel riquadro dell'assistente. La scelta resta salvata sul telefono.""",
         "assistente robot robottino voce parla microfono ascolta domanda giro guidato novità disattivare attivare spegnere aiuto assistente digitale"),
        ("🚀 A cosa serve e come si comincia",
         """**A cosa serve:** tiene l'elenco di quello che hai in casa, di quando scade e di cosa contiene. Ti avvisa prima che qualcosa vada a male.

**Per cominciare, 5 passi:**
1. Tocca la scheda **➕ Aggiungi** in basso.
2. Fotografa il prodotto (o saltalo).
3. Scrivi il nome, quante unità hai e la **scadenza**.
4. Tocca il pulsante per salvare.
5. Torna alla scheda **🏠 Dispensa**: il prodotto è lì, con il colore della scadenza.

La dispensa è **solo tua**: ogni persona ha la sua password e nessuno vede i prodotti degli altri.""",
         "iniziare cominciare primi passi cos'è a cosa serve come funziona introduzione uso"),
        ("➕ Come aggiungere un prodotto",
         """1. Tocca **➕ Aggiungi** (scheda in basso).
2. In alto c'è il punto della **foto**: tocca **📷 Scatta la foto** (si apre la fotocamera posteriore) oppure **📁 Carica dal telefono**.
3. Scrivi il **nome** e la **marca**.
4. Scrivi il **codice a barre** a mano (sono i numeri sotto le barre): l'app compila da sola ingredienti, valori e allergeni, se il prodotto è conosciuto.
5. Scrivi **quante unità**, quanto **pesa** o quanti **litri**.
6. Scegli la **data di scadenza**.
7. In **«Dove lo metti?»** scegli: Dispensa, Frigo, Freezer, Cantina, Negozio, Magazzino o Altro. La **Categoria** invece è un testo libero.
8. Scegli **per chi è**: adulti, neonati (0-2 anni) o animali.
9. Salva.

Se non hai nessuna informazione basta il **nome, le unità e la scadenza**.""",
         "aggiungere inserire nuovo prodotto codice a barre qr compilare scheda dove lo metti frigo freezer cantina categoria quantità unità peso litri scrivere"),
        ("📸 La foto del prodotto: scatto, righello e ritaglio",
         """1. Tocca **📷 Scatta la foto** o **📁 Carica dal telefono**.
2. L'app toglie lo **sfondo** e **raddrizza** da sola il prodotto.
3. Sotto compare l'**editor**: trascina il **righello** per girare la foto e trascina la **cornice** per tagliare i bordi.
4. Quando è perfetta tocca **💾 Salva posizione e ritaglio**.
5. Poi salva il prodotto.

Se l'editor non funziona, apri **🛠️ Controlli di riserva**: ci sono cursori per girare e tagliare.""",
         "foto fotografare scattare scatto fotocamera ruotare girare raddrizzare ritagliare tagliare sfondo scontornare righello cornice immagine"),
        ("🎨 I colori e gli avvisi di scadenza",
         """- 🟢 **Verde**: manca più di 2 mesi. Tutto tranquillo.
- 🟠 **Arancione**: scade entro 2 mesi. Conviene usarlo.
- 🔴 **Rosso**: scade entro 1 mese. Usalo presto.
- ⚫ **Scuro**: è già scaduto.

In alto vedi i **contatori** colorati e gli avvisi con quante unità, quanti grammi o litri stanno per scadere.

Ogni sezione ha il suo **suono**: adulti i suoni di sempre; neonati un suono per la bimba (2 mesi), uno per il bimbo (1 mese) e entrambi se scaduto; animali il gatto (2 mesi), il cane (1 mese) e il leone se scaduto.

Se hai attivato **Telegram** o l'**email**, l'avviso arriva anche lì.""",
         "colori scadenza avvisi verde arancione rosso scaduto contatori suono suoni sirena notifica avviso quando scade"),
        ("🌾 Allergeni, ingredienti, vegano e senza glutine",
         """1. Apri il **menu a sinistra** (la freccia **»** in alto a sinistra) e scegli le **tue allergie**.
2. I prodotti con un allergene hanno un **pulsante giallo** con il suo nome (per esempio *Glutine*): toccalo e si apre la **composizione**, con le parole pericolose evidenziate.
3. Se l'allergene è **pericoloso per te** compare la **sirena lampeggiante**, con scritto a chi è controindicato.
4. Su ogni scheda c'è il tasto **Ingredienti**: apre tutto il testo da leggere, nella tua lingua.
5. I tasti **Vegano** e **Vegetariano** compaiono solo se il prodotto è davvero così. Il tasto **Senza glutine** è bordato d'oro.""",
         "allergeni allergia glutine ingredienti vegano vegetariano senza glutine composizione intolleranza sirena pericoloso"),
        ("🔘 I pulsanti di ogni prodotto: Elimina, Info, Modifica",
         """In **Schede**, sotto ogni prodotto ci sono tre tasti:
- **Elimina**: toglie il prodotto. Se hai lo stesso prodotto con più scadenze, ti chiede **quale voce** eliminare.
- **Info**: apre la guida completa con tutti i simboli.
- **Modifica**: cambia qualsiasi dato (nome, scadenza, foto, quantità…).

In **Tabella** si spunta la casella 🗑️ della riga e poi si tocca **Elimina le righe spuntate** oppure **Modifica la riga spuntata** (per modificare spunta una riga sola).""",
         "elimina cancellare cestino modifica modificare cambiare correggere info tabella schede vista"),
        ("🧭 Le icone Farmacia, I miei documenti e Utilità",
         """Nella Home, accanto ai comandi di ricerca, trovi **tre icone che pulsano**:
- **🏥 Farmacia**: medicinali, terapie, visite, tessera sanitaria.
- **📁 I miei documenti**: carta d'identità, patente, tessera sanitaria con le scadenze.
- **🧰 Utilità**: app e siti utili, come Velocity Music.

Toccane una per aprirla; per tornare tocca **← Torna alla dispensa**. In ogni pagina, in alto, c'è il pulsante rosso **Clicca per informazioni** con la guida.""",
         "icone farmacia documenti utilità home pagine navigare menu dove trovo"),
        ("🔎 Cercare e filtrare i prodotti",
         """In cima alla Dispensa ci sono tre comandi:
1. **🔎 Cerca**: scrivi il nome o la marca.
2. **Mostra**: scegli *Tutti*, *Solo in scadenza (2 mesi)*, *Solo rossi (1 mese)* oppure *Scaduti*.
3. **Vista**: *Schede* (con foto grandi) o *Tabella* (elenco compatto).""",
         "cercare ricerca trovare filtro filtrare mostra vista schede tabella elenco"),
        ("🛒 Lista della spesa e volantini",
         """- Quando un prodotto **finisce** va da solo nella scheda **🛒 Spesa**.
- Nella scheda Spesa puoi toccare **Ne ho consumato uno** per scalare un'unità.
- Sulla scheda del prodotto, a destra della quantità, c'è il collegamento ai **volantini** di supermercati, ipermercati e discount: scegli il **Paese** (parte da quello della tua lingua) e scrivi la **città**, guarda le offerte e tocca il pulsante per mettere il prodotto nella **lista della spesa**, con il nome del negozio.""",
         "spesa lista della spesa comprare volantini offerte supermercato consumato finito città negozio"),
        ("✏️ Gestisci tanti prodotti in una volta",
         """La scheda **✏️ Gestisci** serve per cambiare in un colpo solo **quantità, scadenze e note** di tanti prodotti, senza aprirli uno per uno.""",
         "gestisci modificare molti più prodotti insieme quantità scadenze note"),
        ("👤 Password, lingua e messaggi",
         """- **Password:** ti viene data da chi gestisce l'app. Al primo accesso puoi cambiarla. È solo tua.
- **Lingua:** nel menu a sinistra c'è **🌐 Lingua / Language**.
- **Messaggi e suggerimenti:** per un'idea, un problema o una richiesta usa la scheda **✉️ Messaggi / 💬 Suggerimenti**: la legge l'amministratore.""",
         "password account accesso lingua language messaggi suggerimenti amministratore problema richiesta cambiare password"),
        ("🛟 Se qualcosa non va",
         """1. **Ricarica la pagina** del browser.
2. La foto non compare? Usa **🛠️ Controlli di riserva** oppure scegli un'altra foto.
3. Il microfono per dettare funziona su **Chrome per Android**: tocca una volta per accendere, una volta per spegnere.
4. Se il problema resta, scrivilo nella scheda **Messaggi**: aiuta l'amministratore a sistemarlo.""",
         "problema errore non funziona aiuto bloccato foto non compare microfono dettatura"),
    ],

    "farmacia": [
        ("🚀 A cosa serve la Farmacia",
         """Qui tieni in ordine i **medicinali di casa** e le **scadenze**, le **terapie**, le **visite**, i **vaccini**, il tuo **dottore** e la tua **scheda sanitaria**.

L'app ti **ricorda** e organizza quello che inserisci tu. **Non dà consigli medici** e non cambia le terapie: per dosi e cure segui sempre il medico o il farmacista.""",
         "farmacia cos'è a cosa serve medicinali iniziare introduzione"),
        ("👤 I profili della famiglia e il gruppo sanguigno",
         """Ogni persona ha un **profilo** (fino a 12): mamma, papà, figli…
1. In alto scegli il profilo da **👤 Profilo**.
2. Per aggiungerne uno apri **👥 Gestisci profili**, scrivi il nome e tocca **Aggiungi profilo**.
3. Nello stesso punto puoi cambiare il nome e scegliere il **🩸 gruppo sanguigno**: compare come una **goccia** colorata accanto al profilo.
4. Per cancellare un profilo spunta la conferma e tocca **Elimina profilo** (si cancellano anche tutti i suoi dati).""",
         "profilo profili famiglia persona gruppo sanguigno goccia nome aggiungere cancellare"),
        ("💊 Come aggiungere un medicinale",
         """1. Tocca **➕ Aggiungi medicinale**.
2. In alto la **foto della confezione**: **📷 Scatta la foto** o **📁 Carica dal telefono**; poi raddrizza col righello e taglia con la cornice, e tocca **💾 Salva posizione e ritaglio**.
3. Scrivi **nome**, **principio attivo**, **dosaggio**, **forma** (compresse, sciroppo…) e **quantità**.
4. Scegli la **scadenza** e **per chi è**.
5. Tocca **Salva**.

Puoi riusare una foto già salvata dall'**archivio delle foto**. Al medicinale puoi allegare il **foglio illustrativo** (PDF, foto o link).

Per vedere tutto di un medicinale **tocca la sua scheda**: si apre il dettaglio con il **foglio illustrativo (bugiardino)**, la foto grande, le terapie collegate e i pulsanti **✏️ Modifica** e **🗑️ Elimina**.

Per risparmiare tempo tocca **🎥 Scansiona in diretta** e inquadra il quadratino (DataMatrix) o le barre sulla scatola: l'app riempie scadenza, lotto e codice. Se il telefono non lo permette, scatta una foto: leggo anche la scadenza scritta sulla scatola. Se il medicinale è già in casa ricopia anche nome e dosaggio; se è nuovo scrivi il nome una volta sola e dalla prossima volta lo riconosce.""",
         "medicinale medicinali farmaco aggiungere confezione foto scadenza principio attivo dosaggio foglio illustrativo bugiardino archivio"),
        ("🎨 Scadenze e allergie ai farmaci",
         """- 🟠 **Arancione**: scade entro 2 mesi. 🔴 **Rosso**: entro 1 mese. ⚫ **Scaduto**: da buttare in modo corretto.
- Nella scheda del profilo puoi scrivere le **allergie ai farmaci**: se un medicinale contiene quel principio attivo compare un **avviso rosso**.""",
         "scadenza colori allergia allergie farmaci avviso rosso arancione scaduto"),
        ("📅 Le terapie e il calendario",
         """1. Apri la scheda **📅 Terapie**.
2. Aggiungi una terapia: **medicinale**, **giorni**, **orari** e quantità.
3. All'ora stabilita tocca **Presa** per segnare l'assunzione: resta nello **storico**.
4. Una terapia può essere **attiva**, **sospesa** o **terminata**. Le terapie di prova si possono **eliminare**.
5. Il **calendario** mostra la settimana e il mese.
6. Il **Report per il medico** (periodo a scelta) si stampa o si apre in Excel.""",
         "terapia terapie calendario assunzione presa orari report medico storico pillola dose"),
        ("📝 Le prescrizioni (ricette)",
         """1. Apri la scheda **📝 Prescrizioni** e tocca **➕ Aggiungi prescrizione**.
2. Scrivi la **data**, il **tipo** (farmaci, esami, visita…), il **medico**, cosa è stato **prescritto**, il **codice della ricetta** e fino a quando è **valida**.
3. Allega la **foto della ricetta** oppure il PDF.
4. Toccando una prescrizione si apre il **dettaglio**: vedi la foto, tocchi **✅ Segna come usata**, **✏️ Modifica** o **🗑️ Elimina**.
5. Le prescrizioni in scadenza compaiono tra le cose da controllare, anche nel **Controllo famiglia**.""",
         "prescrizione prescrizioni ricetta ricette medico impegnativa codice nre validità scadenza usata ritirata"),
        ("🩺 Visite, esami e referti",
         """1. Apri la scheda **🩺 Visite** e tocca per aggiungere.
2. Scrivi **data**, **tipo di visita o esame**, **medico**, **motivo** e le **indicazioni per i controlli**.
3. Se c'è, scrivi la data del **prossimo appuntamento**.
4. Allega i **referti**: foto o PDF.""",
         "visita visite esame referto referti analisi appuntamento specialista allegare"),
        ("💉 Vaccini e documento vaccinale",
         """Nella scheda **💉 Vaccini** registri le vaccinazioni di ogni profilo e alleghi il **documento vaccinale** (foto o PDF).""",
         "vaccino vaccini vaccinazione documento vaccinale libretto"),
        ("🩸 La scheda sanitaria e «Il mio dottore»",
         """- Tocca il riquadro del **gruppo sanguigno** per aprire la **scheda sanitaria**: patologie, allergie ai farmaci, interventi, storia clinica e vaccinazioni.
- Accanto trovi **Il mio dottore**: scegli dottore o dottoressa, poi scrivi nome, indirizzo, telefono, email, gli **orari** (una riga per giorno: dalle, alle, note), il **sostituto** e le note.""",
         "scheda sanitaria dottore medico di base patologie interventi storia clinica orari telefono email sostituto"),
        ("🪪 Tessera sanitaria e fascicolo sanitario",
         """In alto, accanto alla dottoressa, c'è il badge azzurro **Tessera sanitaria · Fascicolo sanitario** (pulsa piano per farsi notare). Toccalo.

**La tessera**
1. Tocca **👁️ Mostra fronte e retro della tessera**: la vedi in grande.
2. La tessera si prende da **I miei documenti**. Se non l'hai ancora inserita compare un avviso con il pulsante **📁 Vai a I miei documenti**: scegli **Tessera sanitaria** e fai la foto di fronte e retro. L'avviso sparisce da solo appena l'hai inserita.

**I collegamenti online** (uno per il fascicolo sanitario elettronico, uno per le vaccinazioni, uno per le spese sanitarie detraibili)
1. Apri la pagina nel browser e **copia l'indirizzo** dalla barra in alto.
2. Torna qui, **incollalo** nella casella giusta.
3. Tocca **💾 Salva**.
4. Da quel momento compare un pulsante **🔗**: toccandolo si apre direttamente la pagina.
5. Per cambiare il link tocca **✏️ Modifica**; per toglierlo tocca **🗑️ Togli il link**.

I collegamenti sono separati per ogni profilo della famiglia.""",
         "tessera sanitaria fascicolo sanitario elettronico fse link collegamento indirizzo vaccinazioni online spese sanitarie detraibili fronte retro badge azzurro 730 detrazioni"),
        ("🔎 Trova una farmacia aperta",
         """Tocca il pulsante grande **🔎 Trova una farmacia aperta** in alto: scegli il **Paese** (parte da quello della tua lingua) e scrivi **qualunque città o codice postale**. L'app cerca le farmacie aperte vicino a quel posto. Oppure tocca **📍 Usa la mia posizione (GPS)**: il telefono ti chiede il permesso e l'app cerca intorno a dove sei (la posizione non viene salvata).""",
         "farmacia aperta trovare cercare vicino turno notte"),
        ("🔔 Avvisi su Telegram, email e SMS",
         """Gli avvisi ti ricordano le scadenze (a 60, 30, 14 e 7 giorni, 1 giorno e il giorno stesso) e, se vuoi, l'ora delle terapie. Scegli **uno o più canali**.

### 📱 Telegram, passo per passo
""" + _TESTO_TELEGRAM + """

### ✉️ Email
""" + _TESTO_EMAIL + """

### 💬 SMS
Sono a pagamento e di solito non sono attivi: chiedi all'amministratore.

Facoltativo: spunta **«Nei messaggi non scrivere i nomi dei medicinali»** se vuoi più privacy.

Il capo famiglia, nello stesso modulo, può attivare anche il riepilogo della famiglia ogni mattina e l'avviso se una persona non registra una dose entro 90 minuti. Le prescrizioni in scadenza avvisano a 14, 7, 3 e 1 giorno e il giorno stesso.""",
         "avvisi notifiche telegram chat id bot avvia start userinfobot email sms promemoria messaggio ricevere attivare numero id gmail spam posta"),
        ("🧾 Report completo e dati",
         """In **🧾 I miei dati personali e report completo** scrivi nome e cognome e scarichi un **report da stampare** con tutto quello che hai inserito. Il file **JSON** contiene gli stessi dati per una copia di sicurezza.
Contiene dati sanitari: non condividerlo con chi non deve vederlo.""",
         "report completo stampare esportare scaricare dati personali copia pdf json"),
        ("📤 Esportare e inviare (PDF, email, WhatsApp…)",
         """1. In alto nella Farmacia apri **📤 Esporta e invia**. Scegli **di chi** e **cosa** (medicinali, terapie, prescrizioni, visite, vaccini, documenti, scheda sanitaria, dispensa, lista della spesa).
2. Scegli il **formato** (PDF, Excel o file da stampare) e tocca **📦 Prepara i file**.
3. Poi scegli come inviarli: **📤 Telefono** (si apre Condividi: WhatsApp, Gmail, Telegram, Drive…), **✉️ Email** (direttamente dall'app), **💬 WhatsApp** (riepilogo scritto), **✈️ Telegram** (nella tua chat con il bot), **📱 SMS** o **📋 Copia**.
4. Ogni documento, medicinale, prescrizione e visita ha anche il suo tasto **📤 Invia**, con le sue foto.
5. Il capo famiglia può inviare i dati di tutta la famiglia dal **Controllo famiglia**.

Solo per chi gestisce l'app: per mandare email e Telegram direttamente dall'app, in Streamlit apri Manage app, poi Settings, poi Secrets, e aggiungi EMAIL_USER, EMAIL_PASSWORD e TELEGRAM_TOKEN (gli stessi valori degli avvisi). Contiene dati sanitari: controlla bene a chi invii.""",
         "invio inviare mandare condividere whatsapp email posta telegram sms pdf excel stampare esportare condividi allegato file"),
    ],

    "utilita": [
        ("🧰 A cosa serve la pagina Utilità",
         """Raccoglie **app e siti utili** in un solo posto. Ognuno ha un grande **pulsante che pulsa**: toccalo e si avvia.

Sotto il pulsante c'è il **nome** dell'app: toccandolo si apre il **bugiardino**, cioè una spiegazione semplice di cosa fa e dei suoi vantaggi.

Per ora ci sono **Velocity Music** (il play azzurro) e **Wimbi** (il papero con le cuffie); altre utilità si aggiungeranno qui.""",
         "utilità utilita pagina app pulsanti avviare raccolta siti cos'è a cosa serve"),
        ("▶️ Come avviare un'app",
         """1. Dalla Home tocca l'icona **🧰 Utilità** (accanto a Farmacia e I miei documenti).
2. Tocca il **grande pulsante** con il simbolo ▶️: l'app si apre in una nuova scheda del browser.
3. Per tornare qui, chiudi quella scheda o torna indietro.""",
         "avviare aprire avvio play pulsante app link velocity music musica"),
        ("📖 Come leggere il bugiardino",
         """1. Sotto il pulsante c'è la **targa con il nome** dell'app.
2. **Toccala**: si apre una finestra con la spiegazione (cos'è, vantaggi, indirizzo).
3. Dentro c'è anche il pulsante **🎵 Avvia** per aprire l'app.
4. Per chiudere la finestra tocca la **X** in alto.""",
         "bugiardino spiegazione targa nome leggere descrizione vantaggi informazioni"),
        ("🦆 Wimbi",
         """Wimbi è un'app musicale: **scrivi una canzone o un artista, tocchi un risultato e parte**. Non serve registrarsi, le playlist restano sul tuo dispositivo, la musica **continua a suonare a schermo spento** e l'app è disponibile in **17 lingue**.

Tocca il **papero con le cuffie** per avviarla, oppure la scritta verde **Wimbi** per leggere il bugiardino completo.
Indirizzo: https://wimbi.app/it/""",
         "wimbi papero cuffie musica canzoni artista playlist schermo spento lingue senza account"),
        ("🎵 Velocity Music",
         """È un lettore e gestore musicale che permette di ascoltare **gratuitamente** la libreria di YouTube, **senza pubblicità** e **senza abbonamenti**. Si può usare **come ospite**, senza creare un account. Il progetto è ancora in sviluppo ma già utilizzabile.

Indirizzo: https://velocitymusic.uk/""",
         "velocity music musica youtube gratis pubblicità lettore canzoni ascoltare radio"),
    ],

    "documenti": [
        ("🚀 A cosa serve «I miei documenti»",
         """Qui tieni i **documenti personali** (carta d'identità, patente, passaporto, tessera sanitaria, permessi, assicurazioni…) con le **foto fronte e retro** e le **scadenze**.

L'app ti avvisa **6 mesi prima** (primo avviso, arancione) e **3 mesi prima** (secondo avviso, rosso e più intenso), così hai tempo per rinnovarli.""",
         "documenti cos'è a cosa serve carta d'identità patente passaporto tessera iniziare introduzione"),
        ("➕ Come aggiungere un documento",
         """1. Scegli di chi è il documento da **👤 Documenti di**.
2. Tocca **➕ Aggiungi un documento**.
3. Scegli il **tipo** dall'elenco. Se non c'è, scrivilo nella casella **«Non lo trovi?»**.
4. Scrivi **numero**, **rilasciato da**, **data di rilascio** e **data di scadenza**. Se non scade mai, spunta **«Questo documento non scade»**.
5. Fai la **foto di fronte e retro** (vedi la guida sotto).
6. Tocca **💾 Salva il documento**.""",
         "aggiungere inserire nuovo documento tipo numero rilasciato scadenza non scade salvare"),
        ("📷 Foto del fronte e del retro (con sfondo tolto e raddrizzata)",
         """Ci sono **due blocchi uguali: 📄 Fronte e 📄 Retro**. Per ciascuno:
1. Tocca **📷 Scatta la foto** (fotocamera posteriore) **oppure** **📁 Carica dal telefono** se hai già la foto.
2. L'app toglie lo **sfondo** e **raddrizza** il documento da sola.
3. Sotto compare l'**editor**: trascina il **righello** per girare e la **cornice** per tagliare.
4. Quando è perfetta tocca **💾 Salva posizione e ritaglio**.
5. Se il documento è stato tagliato male spunta **«Tieni anche lo sfondo»**: l'immagine resta intera e la sistemi solo a mano.
6. Se hai sbagliato foto tocca **🗑️ Togli questa foto**.
7. Alla fine tocca **💾 Salva il documento**: le foto vengono salvate insieme ai dati.

Per un **PDF** o altre pagine usa il campo **«Altri file»** sotto il modulo.""",
         "foto fotografare scattare fronte retro caricare upload scontornare sfondo raddrizzare ruotare ritagliare righello cornice immagine documento"),
        ("🎨 I colori e gli avvisi di scadenza",
         """- 🟢 **Verde**: scade tra più di 6 mesi.
- 🟠 **Arancione, primo avviso**: scade entro 6 mesi.
- 🔴 **Rosso, secondo avviso**: scade entro 3 mesi. Compare un riquadro d'allarme.
- ⚫ **Scaduto**: da rinnovare subito.

In alto vedi i contatori. Se hai attivato **Telegram** o l'**email** (si fa nella Farmacia, in **Scegli come ricevere gli avvisi**), gli avvisi arrivano anche lì.""",
         "colori scadenza avvisi arancione rosso scaduto sei mesi tre mesi rinnovare allarme telegram email"),
        ("🔎 Cercare e filtrare i documenti",
         """Sopra l'elenco c'è il campo **Cerca**: scrivi il tipo, il numero, l'ente o una nota. Accanto scegli una **categoria** per vedere solo quelli.""",
         "cercare ricerca trovare filtro categoria elenco"),
        ("✏️ Modificare, aprire ed eliminare",
         """- **Aprire un documento:** tocca la sua **scheda colorata**: si apre il dettaglio con tutti i dati.
- **Vedere fronte e retro:** nel dettaglio tocca **👁️ Mostra fronte e retro**: le vedi grandi e puoi **scaricarle**.
- **Modificare:** nel dettaglio tocca **✏️ Modifica**, cambia i dati o aggiungi altre foto, poi salva.
- **Togliere una foto sola:** in Modifica, nella lista **Già allegato**, tocca 🗑️ accanto al file.
- **Eliminare il documento:** nel dettaglio tocca **🗑️ Elimina** e conferma.""",
         "modificare modifica eliminare cancellare aprire allegato scaricare togliere foto"),
        ("⚙️ I tipi di documento",
         """In fondo alla pagina apri **⚙️ Gestisci i tipi di documento**: puoi **aggiungere** i tuoi tipi, **toglierli** o **nascondere** quelli che non usi.""",
         "tipi tipo categorie nuovo tipo nascondere catalogo"),
        ("🔒 Privacy",
         """I documenti contengono dati personali: **non condividere** schermate o file con chi non deve vederli. Ogni persona vede solo i propri.""",
         "privacy sicurezza dati personali condividere"),
    ],
}

# Codici stabili delle voci (nell'ordine di _GUIDE): servono per collegare le traduzioni. Chi aggiunge una voce italiana
# aggiunge qui il suo codice (e la traduzione nei file guida_xx.py; se manca, in quella lingua si vede l'italiano).
_ID_GUIDA = {
    "dispensa": "d_assistente d_inizio d_aggiungere d_foto d_colori d_allergeni d_pulsanti d_icone d_cercare d_spesa d_gestisci d_account d_aiuto".split(),
    "farmacia": "f_cosa f_profili f_medicinale f_scadenze f_terapie f_prescrizioni f_visite f_vaccini f_scheda f_tessera f_aperta f_avvisi f_report f_invio".split(),
    "utilita": "u_cosa u_avviare u_bugiardino u_wimbi u_velocity".split(),
    "documenti": "x_cosa x_aggiungere x_foto x_colori x_cercare x_modificare x_tipi x_privacy".split(),
}

GUIDA_TR = {}      # lingua -> {codice: (titolo, spiegazione, parole utili alla ricerca)}  (riempito da guida_xx.py)
UI_TR = {}         # lingua -> {chiave: testo}                                              (riempito da guida_xx.py)

UI_IT = {
    "dlg_titolo": "📖 Guida e informazioni",
    "dlg_hint": "Tocca un argomento per aprirlo. Oppure scrivi qui sotto cosa vuoi sapere.",
    "dlg_cerca_label": "🔎 Cosa vuoi sapere?",
    "dlg_cerca_ph": "es. come faccio la foto al retro del documento",
    "dlg_trovato": "**Ecco cosa ho trovato:**",
    "dlg_nulla": "Non ho trovato una risposta con queste parole. Prova a scriverlo in modo diverso (per esempio una sola parola: "
                 "*foto*, *scadenza*, *password*) oppure scrivi un suggerimento nella scheda Messaggi.",
    "dlg_tutti": "Tutti gli argomenti",
    "dlg_nota_it": "ℹ️ Le schermate di questa sezione per ora sono in italiano: i nomi dei pulsanti sono scritti come li vedi sullo schermo.",
    "dlg_asst": "**🤖 Assistente digitale** (il robottino che parla e ti aiuta)",
    "dlg_on": "✅ Attiva", "dlg_off": "⛔ Disattiva",
    "info_help": "Tocca per leggere come si usa questa sezione", "info_fallback": "ℹ️ Informazioni e guida",
    "sez_dispensa": "🏠 Dispensa", "sez_farmacia": "🏥 Farmacia", "sez_documenti": "📁 I miei documenti", "sez_utilita": "🧰 Utilità",
    # --- assistente digitale
    "a_aria": "Assistente digitale", "a_rileggi": "📖 Spiegami questa pagina", "a_giro": "🧭 Giro guidato dell'app",
    "a_novita": "🆕 Cosa c'è di nuovo", "a_mic": "🎤 Fai una domanda", "a_indietro": "◀ Indietro", "a_avanti": "Avanti ▶", "a_fine": "Fine",
    "a_ph": "Scrivi qui la tua domanda…", "a_chiedi": "Chiedi", "a_voce_on": "🔊 Voce: attiva", "a_voce_off": "🔇 Voce: spenta",
    "a_silenzio": "⏹ Silenzio", "a_off": "⛔ Disattiva assistente", "a_ascolto_btn": "⏹ Sto ascoltando…",
    "a_ascolto_t": "Ti ascolto", "a_ascolto_x": "Parla ora: per esempio «come aggiungo una foto al documento?»",
    "a_mic_t": "Microfono", "a_mic_no": "Su questo telefono non riesco ad ascoltarti: scrivi la domanda qui sotto.",
    "a_mic_perm": "Consenti l'uso del microfono al browser per parlare con me.",
    "a_mic_err": "Non riesco a usare la voce ora: scrivi la domanda qui sotto.",
    "a_nulla_t": "Non ho sentito niente", "a_nulla_x": "Riprova: tocca il microfono e parla.",
    "a_dimmi_t": "Dimmi pure", "a_dimmi_x": "Scrivi o dì cosa vuoi sapere.",
    "a_off_t": "Vuoi che mi disattivi?",
    "a_off_x": "Tocca il pulsante «⛔ Disattiva assistente» qui sotto. Mi riattivi dal pulsante rosso «Clicca per informazioni».",
    "a_trov_t": "Non ho trovato la risposta",
    "a_trov_x": "Prova con altre parole (per esempio una sola: foto, scadenza, password) oppure scegli un argomento qui sotto.",
    "a_nov_none_t": "Novità", "a_nov_none_x": "Per ora non ci sono novità recenti. Ti avviso io quando ne arrivano!",
    "a_nov_voce": "Ecco le novità.", "a_nov_trovi": "La trovi così:", "a_nov_t": "Cosa c'è di nuovo",
    "a_fine_t": "Fine del giro", "a_fine_x": "Ecco fatto! Se ti serve altro, chiedimi.",
    "a_toast_off": "Assistente disattivato. Lo riattivi da «Clicca per informazioni».", "a_toast_on": "Assistente attivo: tocca il robottino.",
    "a_vedi": "Tocca un argomento qui sotto per saperne di più.",
    # parole che l'assistente riconosce nelle domande (separate da spazio)
    "i_silenzio": "silenzio zitto basta smetti", "i_off": "disattiv spegn", "i_ass": "assistent robot",
    "i_novita": "novit nuovo nuove aggiornament", "i_giro": "giro tutorial guida inizia", "i_saluto": "ciao salve buongiorno buonasera aiuto",
}
LINGUE_BCP47 = {"it": "it-IT", "en": "en-GB", "es": "es-ES", "fr": "fr-FR", "de": "de-DE", "ro": "ro-RO", "ar": "ar-SA"}

_STOP_LANG = {
    "it": "il lo la i gli le un uno una di a da in con su per tra fra e o ma che chi cui come dove quando cosa quale quali mi ti si ci vi non "
          "del dello della dei degli delle al allo alla ai agli alle dal dallo dalla dai dagli dalle nel nello nella nei negli nelle sul sullo "
          "sulla sui sugli sulle è sono ho hai ha posso puoi fare faccio fa devo voglio vorrei se questo questa quello quella mio mia miei mie "
          "tuo tua app dell all anche più poi può possibile modo vuole".split(),
    "en": "the a an of to in on for and or is are how do does i can my me what where when with from this that it be you your app".split(),
    "es": "el la los las un una unos unas de del al a en con por para y o que como donde cuando cual mi mis tu tus se es son puedo "
          "puedes quiero hacer lo le app".split(),
    "fr": "le la les un une des de du au aux en et ou que qui comment ou quand quel quelle mon ma mes ton ta tes je peux puis veux "
          "faire est sont dans sur pour avec app".split(),
    "de": "der die das ein eine einen dem den des und oder wie wo wann was welche mein meine dein deine ich kann kannst will "
          "machen ist sind in auf fur mit von zu app".split(),
    "ro": "un o niste de la in pe cu si sau ca cum unde cand ce care meu mea tau mele pot poti vreau fac este sunt din pentru app".split(),
    "ar": "في من على إلى عن مع هل ما كيف أين متى هذا هذه أن أنا أريد يمكن لي".split(),
}


def _lingua_guida():
    """La lingua scelta all'ingresso (it, en, es, fr, de, ro, ar)."""
    try:
        return lingua()
    except Exception:
        return "it"


def _u(chiave):
    """Un testo dell'interfaccia della guida / dell'assistente nella lingua scelta (se manca la traduzione, in italiano)."""
    return UI_TR.get(_lingua_guida(), {}).get(chiave) or UI_IT.get(chiave, chiave)


def voci_guida(sezione):
    """Le voci della guida di una sezione nella lingua scelta: lista di dict {id, sez, titolo, corpo, chiavi}."""
    lg = _lingua_guida()
    tr = GUIDA_TR.get(lg, {}) if lg != "it" else {}
    out = []
    for codice, (titolo, corpo, chiavi) in zip(_ID_GUIDA.get(sezione, []), _GUIDE.get(sezione, [])):
        x = tr.get(codice)
        out.append({"id": codice, "sez": sezione, "titolo": x[0] if x else titolo, "corpo": x[1] if x else corpo,
                    "chiavi": ((x[2] + " " + chiavi) if x and len(x) > 2 else chiavi)})
    return out


def tutte_voci():
    return [v for sez in _GUIDE for v in voci_guida(sez)]


def _norm(testo):
    testo = unicodedata.normalize("NFD", str(testo).lower())
    testo = "".join(c for c in testo if not unicodedata.category(c).startswith("M"))
    return re.sub(r"[\W_]+", " ", testo)


def _stem(parola):
    return re.sub(r"[aeiou]+$", "", parola) if len(parola) > 4 else parola


def _parole_guida(testo):
    stop = set(_STOP_LANG.get(_lingua_guida(), _STOP_LANG["it"]))
    minimo = 2 if _lingua_guida() == "ar" else 3
    ar = _lingua_guida() == "ar"
    return {_stem(re.sub(r"^(وال|بال|كال|لل|ال)", "", p) if ar and len(p) > 4 else p)
            for p in _norm(testo).split() if len(p) >= minimo and p not in stop}


def _combacia(q, insieme):
    return any(w.startswith(q) or (len(w) >= 4 and q.startswith(w)) for w in insieme)


def _indice():
    """L'indice di ricerca nella lingua scelta (si ricostruisce a ogni esecuzione: la lingua può cambiare)."""
    return {(v["sez"], v["id"]): (v, _parole_guida(v["titolo"]), _parole_guida(v["chiavi"]), _parole_guida(v["corpo"])) for v in tutte_voci()}


def cerca_nella_guida(domanda, massimo=4, preferita=None):
    """Le voci della guida più adatte alla domanda: lista di (sezione, codice, titolo, spiegazione).
    Le voci della sezione in cui ci si trova (preferita) passano davanti a parità di risultato."""
    stems = [q for q in _parole_guida(domanda) if q]
    if not stems:
        return []
    indice = _indice()
    punteggi = []
    for chiave, (v, p_tit, p_chi, p_cor) in indice.items():
        punti = 0
        trovate = 0
        for q in stems:
            if _combacia(q, p_tit):
                punti += 3
            elif _combacia(q, p_chi):
                punti += 2
            elif _combacia(q, p_cor):
                punti += 1
            else:
                continue
            trovate += 1
        if punti:
            punteggi.append((punti + trovate + (1 if chiave[0] == preferita else 0), chiave))
    punteggi.sort(key=lambda x: (-x[0], x[1]))
    if not punteggi:
        return []
    migliore = punteggi[0][0]
    risultati = []
    for punti, chiave in punteggi[:massimo]:
        if punti * 2 < migliore:
            continue
        v = indice[chiave][0]
        risultati.append((v["sez"], v["id"], v["titolo"], v["corpo"]))
    return risultati


def guida_avvisi():
    """Spiegazione passo per passo di Telegram ed email, da mostrare dentro «Scegli come ricevere gli avvisi» (nella lingua scelta)."""
    voce = next((v for v in voci_guida("farmacia") if v["id"] == "f_avvisi"), None)
    parti = (voce["corpo"].split("\n### ") if voce else [])
    if len(parti) >= 3:
        nomi = [p.split("\n", 1)[0].strip() for p in parti[1:3]]
        t_tg, t_ml = st.tabs(nomi)
        with t_tg:
            st.markdown(parti[1].split("\n", 1)[1])
        with t_ml:
            st.markdown(parti[2].split("\n", 1)[1])
        return
    t_tg, t_ml = st.tabs(["📱 Come attivo Telegram", "✉️ Come attivo l'email"])
    with t_tg:
        st.markdown(_TESTO_TELEGRAM)
    with t_ml:
        st.markdown(_TESTO_EMAIL)


# ---------------------------------------------------------------------
# IL PULSANTE E LA FINESTRA
# ---------------------------------------------------------------------
def _cartella_info():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return "."


@st.cache_resource(show_spinner=False)
def _info_uri_cache(data_file):
    try:
        with open(os.path.join(_cartella_info(), "info.webp"), "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode()
    except OSError:
        return ""


def _info_uri():
    try:
        data = os.path.getmtime(os.path.join(_cartella_info(), "info.webp"))
    except OSError:
        data = 0
    return _info_uri_cache(data)


@st.dialog(UI_IT["dlg_titolo"], width="large")
def _dialogo_info(sezione):
    if "LINGUE_DA_DESTRA" in globals() and _lingua_guida() in LINGUE_DA_DESTRA or _lingua_guida() == "ar":
        st.markdown("<style>[data-testid='stDialog'] [data-testid='stVerticalBlock']{direction:rtl;text-align:right}</style>",
                    unsafe_allow_html=True)
    nome = _u("sez_" + sezione)
    st.markdown(f"### {nome}")
    st.caption(_u("dlg_hint"))
    if _lingua_guida() != "it" and sezione in ("farmacia", "documenti", "utilita"):
        st.info(_u("dlg_nota_it"))
    domanda = st.text_input(_u("dlg_cerca_label"), key=f"guida_cerca_{sezione}", placeholder=_u("dlg_cerca_ph"),
                            label_visibility="collapsed")
    if domanda.strip():
        risultati = cerca_nella_guida(domanda, preferita=sezione)
        if not risultati:
            st.warning(_u("dlg_nulla"))
        else:
            st.markdown(_u("dlg_trovato"))
            for sez, _i, titolo, corpo in risultati:
                with st.container(border=True):
                    st.markdown(f"**{titolo}**  \n<span style='opacity:.7'>{html.escape(_u('sez_' + sez))}</span>",
                                unsafe_allow_html=True)
                    st.markdown(corpo)
        st.divider()
    if "assistente" in globals():
        with st.container(border=True):
            st.markdown(_u("dlg_asst"))
            c_on, c_off = st.columns(2)
            if c_on.button(_u("dlg_on"), key=f"asst_on_{sezione}", width="stretch"):
                st.session_state["_asst_cmd"] = "on"
                st.rerun()
            if c_off.button(_u("dlg_off"), key=f"asst_off_{sezione}", width="stretch"):
                st.session_state["_asst_cmd"] = "off"
                st.rerun()
    st.markdown(f"**{_u('dlg_tutti')} · {nome}**")
    for v in voci_guida(sezione):
        with st.expander(v["titolo"]):
            st.markdown(v["corpo"])


# Banner «La nostra dispensa» più grande (si applica solo nella Dispensa, sopra il pulsante Informazioni)
_CSS_BANNER_GRANDE = """<style>
div.hero{height:158px !important;min-height:158px !important;padding:0 0 0 14px !important;gap:12px !important;border-radius:34px !important}
div.hero .hero-ico{width:58px !important;height:58px !important}
div.hero .hero-ico svg{width:32px !important;height:32px !important}
div.hero .hero-testi{max-width:150px !important;gap:6px !important}
div.hero h1{font-size:25px !important;line-height:1.08 !important;white-space:normal !important}
div.hero p{font-size:13px !important;line-height:1.3 !important;max-width:150px !important}
div.hero::after{width:180px !important;height:158px !important;top:-10px !important;right:-4px !important}
</style>"""


# Elenco delle novità: (data ISO, simbolo, titolo, DOVE SI TROVA). Si aggiunge una riga per ogni novità: l'assistente
# digitale le dice a voce («Cosa c'è di nuovo») solo per gli ultimi 14 giorni, poi scompaiono da sole.
_NOVITA = [
    ("2026-10-28", "🤖", "Assistente digitale", "Il robottino rotondo in basso a destra: toccalo e ti spiega l'app a voce, anche con il microfono"),
    ("2026-10-27", "🦆", "Nuova utilità: Wimbi", "Home → Utilità → il papero con le cuffie; tocca la scritta verde per il bugiardino"),
    ("2026-10-27", "🧰", "Nuova pagina «Utilità»", "Home → terza icona azzurra «Utilità», accanto a Farmacia e I miei documenti"),
    ("2026-10-27", "ℹ️", "Guida in ogni pagina", "Pulsante rosso «Clicca per informazioni» in alto, con spiegazioni e ricerca"),
    ("2026-10-27", "🪪", "Tessera sanitaria e fascicolo", "Farmacia → badge azzurro accanto alla dottoressa"),
    ("2026-10-27", "📷", "Documenti: foto e lettura automatica", "I miei documenti → «Aggiungi un documento»"),
]

def pulsante_info(sezione):
    """Mostra il pulsante con l'immagine «Informazioni»; toccandolo si apre la guida di quella sezione."""
    uri = _info_uri()
    chiave = f"ginfo_{sezione}"
    if "assistente" in globals():                       # il robottino assistente (assistente.py)
        try:
            assistente(sezione)
        except Exception:
            pass
    if sezione == "dispensa":
        st.markdown(_CSS_BANNER_GRANDE, unsafe_allow_html=True)
    if uri:
        st.markdown(
            "<style>"
            "@keyframes ginfo-batte{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.25))}"
            "50%{transform:scale(1.02);filter:drop-shadow(0 0 14px rgba(229,57,53,.85))}}"
            f".st-key-{chiave} button{{background:url('{uri}') center/100% 100% no-repeat !important;"
            "border:0 !important;box-shadow:none !important;color:transparent !important;"
            "display:block !important;width:100% !important;max-width:640px !important;margin:0 auto !important;height:auto !important;aspect-ratio:760/225;min-height:0 !important;"
            "padding:0 !important;border-radius:0 !important;cursor:pointer;animation:ginfo-batte 2.4s ease-in-out infinite}"
            f".st-key-{chiave} button:active{{transform:scale(.95);animation:none}}"
            f".st-key-{chiave} button p{{font-size:0 !important}}"
            "</style>", unsafe_allow_html=True)
    with st.container(key=chiave):
        premuto = st.button("Informazioni" if uri else _u("info_fallback"), key=f"ginfo_btn_{sezione}",
                            help=_u("info_help"), width="stretch")
    if premuto:
        _dialogo_info(sezione)
