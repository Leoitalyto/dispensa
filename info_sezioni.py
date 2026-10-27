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

_NOMI_SEZIONI = {"dispensa": "🏠 Dispensa", "farmacia": "🏥 Farmacia", "documenti": "📁 I miei documenti"}

# ---------------------------------------------------------------------
# I TESTI DELLE GUIDE: (titolo, spiegazione, parole utili per la ricerca)
# ---------------------------------------------------------------------
# Nome (ed eventuale link) del bot Telegram dell'app: scrivi qui il link vero, per esempio "https://t.me/NomeDelTuoBot"
_BOT_NOME = "Dispensa Leo"
_BOT_LINK = ""

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
        ("🔎 Cercare e filtrare i prodotti",
         """In cima alla Dispensa ci sono tre comandi:
1. **🔎 Cerca**: scrivi il nome o la marca.
2. **Mostra**: scegli *Tutti*, *Solo in scadenza (2 mesi)*, *Solo rossi (1 mese)* oppure *Scaduti*.
3. **Vista**: *Schede* (con foto grandi) o *Tabella* (elenco compatto).""",
         "cercare ricerca trovare filtro filtrare mostra vista schede tabella elenco"),
        ("🛒 Lista della spesa e volantini",
         """- Quando un prodotto **finisce** va da solo nella scheda **🛒 Spesa**.
- Nella scheda Spesa puoi toccare **Ne ho consumato uno** per scalare un'unità.
- Sulla scheda del prodotto, a destra della quantità, c'è il collegamento ai **volantini** di supermercati, ipermercati e discount: scegli la **città**, guarda le offerte e tocca il pulsante per mettere il prodotto nella **lista della spesa**, con il nome del negozio.""",
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

Puoi riusare una foto già salvata dall'**archivio delle foto**. Al medicinale puoi allegare il **foglio illustrativo** (PDF, foto o link).""",
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
        ("🔎 Trova una farmacia aperta",
         """Tocca il pulsante grande **🔎 Trova una farmacia aperta** in alto: l'app cerca le farmacie aperte vicino a te.""",
         "farmacia aperta trovare cercare vicino turno notte"),
        ("🔔 Avvisi su Telegram, email e SMS",
         """Gli avvisi ti ricordano le scadenze (a 60, 30, 14 e 7 giorni, 1 giorno e il giorno stesso) e, se vuoi, l'ora delle terapie. Scegli **uno o più canali**.

### 📱 Telegram, passo per passo
""" + _TESTO_TELEGRAM + """

### ✉️ Email
""" + _TESTO_EMAIL + """

### 💬 SMS
Sono a pagamento e di solito non sono attivi: chiedi all'amministratore.

Facoltativo: spunta **«Nei messaggi non scrivere i nomi dei medicinali»** se vuoi più privacy.""",
         "avvisi notifiche telegram chat id bot avvia start userinfobot email sms promemoria messaggio ricevere attivare numero id gmail spam posta"),
        ("🧾 Report completo e dati",
         """In **🧾 I miei dati personali e report completo** scrivi nome e cognome e scarichi un **report da stampare** con tutto quello che hai inserito. Il file **JSON** contiene gli stessi dati per una copia di sicurezza.
Contiene dati sanitari: non condividerlo con chi non deve vederlo.""",
         "report completo stampare esportare scaricare dati personali copia pdf json"),
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
         """- **Aprire una foto:** tocca il nome del file sotto il documento: la vedi grande e puoi **scaricarla**.
- **Modificare:** tocca **Modifica**, cambia i dati o aggiungi altre foto, poi salva.
- **Togliere una foto sola:** in Modifica, nella lista **Già allegato**, tocca 🗑️ accanto al file.
- **Eliminare il documento:** tocca **Elimina** e conferma.""",
         "modificare modifica eliminare cancellare aprire allegato scaricare togliere foto"),
        ("⚙️ I tipi di documento",
         """In fondo alla pagina apri **⚙️ Gestisci i tipi di documento**: puoi **aggiungere** i tuoi tipi, **toglierli** o **nascondere** quelli che non usi.""",
         "tipi tipo categorie nuovo tipo nascondere catalogo"),
        ("🔒 Privacy",
         """I documenti contengono dati personali: **non condividere** schermate o file con chi non deve vederli. Ogni persona vede solo i propri.""",
         "privacy sicurezza dati personali condividere"),
    ],
}

_STOP = set("""il lo la i gli le un uno una di a da in con su per tra fra e o ma che chi cui come dove quando cosa quale quali mi ti si ci
vi non del dello della dei degli delle al allo alla ai agli alle dal dallo dalla dai dagli dalle nel nello nella nei negli nelle sul sullo
sulla sui sugli sulle è sono ho hai ha posso puoi fare faccio fa devo voglio vorrei se questo questa quello quella mio mia miei mie tuo tua
app dell all dal sul nell anche più poi può possibile modo vuole voglio""".split())


def _norm(testo):
    testo = unicodedata.normalize("NFD", str(testo).lower())
    testo = "".join(c for c in testo if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", testo)


def _stem(parola):
    return re.sub(r"[aeiou]+$", "", parola) if len(parola) > 4 else parola


def _parole(testo):
    return {_stem(p) for p in _norm(testo).split() if len(p) >= 3 and p not in _STOP}


def _combacia(q, insieme):
    return any(w.startswith(q) or (len(w) >= 4 and q.startswith(w)) for w in insieme)


_INDICE = {}


def _indice():
    if not _INDICE:
        for sezione, voci in _GUIDE.items():
            for i, (titolo, corpo, chiavi) in enumerate(voci):
                _INDICE[(sezione, i)] = (_parole(titolo), _parole(chiavi), _parole(corpo))
    return _INDICE


def cerca_nella_guida(domanda, massimo=4, preferita=None):
    """Le voci della guida più adatte alla domanda: lista di (sezione, indice, titolo, spiegazione).
    Le voci della sezione in cui ci si trova (preferita) passano davanti a parità di risultato."""
    stems = [q for q in _parole(domanda) if q]
    if not stems:
        return []
    punteggi = []
    for (sezione, i), (p_tit, p_chi, p_cor) in _indice().items():
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
            punteggi.append((punti + trovate + (1 if sezione == preferita else 0), sezione, i))
    punteggi.sort(key=lambda x: (-x[0], x[1], x[2]))
    if not punteggi:
        return []
    migliore = punteggi[0][0]
    risultati = []
    for punti, sezione, i in punteggi[:massimo]:
        if punti * 2 < migliore:
            continue
        titolo, corpo, _ = _GUIDE[sezione][i]
        risultati.append((sezione, i, titolo, corpo))
    return risultati


def guida_avvisi():
    """Spiegazione passo per passo di Telegram ed email, da mostrare dentro «Scegli come ricevere gli avvisi»."""
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


@st.dialog("📖 Guida e informazioni", width="large")
def _dialogo_info(sezione):
    st.markdown(f"### {_NOMI_SEZIONI.get(sezione, sezione)}")
    st.caption("Tocca un argomento per aprirlo. Oppure scrivi qui sotto cosa vuoi sapere.")
    domanda = st.text_input("🔎 Cosa vuoi sapere?", key=f"guida_cerca_{sezione}",
                            placeholder="es. come faccio la foto al retro del documento",
                            label_visibility="collapsed")
    if domanda.strip():
        risultati = cerca_nella_guida(domanda, preferita=sezione)
        if not risultati:
            st.warning("Non ho trovato una risposta con queste parole. Prova a scriverlo in modo diverso "
                       "(per esempio una sola parola: *foto*, *scadenza*, *password*) oppure scrivi un suggerimento "
                       "nella scheda Messaggi.")
        else:
            st.markdown("**Ecco cosa ho trovato:**")
            for sez, _i, titolo, corpo in risultati:
                with st.container(border=True):
                    nome_sez = _NOMI_SEZIONI.get(sez, sez)
                    st.markdown(f"**{titolo}**  \n<span style='opacity:.7'>{html.escape(nome_sez)}</span>",
                                unsafe_allow_html=True)
                    st.markdown(corpo)
        st.divider()
    st.markdown(f"**Tutti gli argomenti · {_NOMI_SEZIONI.get(sezione, sezione)}**")
    for titolo, corpo, _chiavi in _GUIDE.get(sezione, []):
        with st.expander(titolo):
            st.markdown(corpo)


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


def pulsante_info(sezione):
    """Mostra il pulsante con l'immagine «Informazioni»; toccandolo si apre la guida di quella sezione."""
    uri = _info_uri()
    chiave = f"ginfo_{sezione}"
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
        premuto = st.button("Informazioni" if uri else "ℹ️ Informazioni e guida", key=f"ginfo_btn_{sezione}",
                            help="Tocca per leggere come si usa questa sezione", width="stretch")
    if premuto:
        _dialogo_info(sezione)
