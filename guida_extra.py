# -*- coding: utf-8 -*-
"""ISTRUZIONI AGGIUNTIVE (gruppo C del progetto di ottimizzazione).

L'UNICA base delle istruzioni è `_GUIDE` / `_ID_GUIDA` / `_META_GUIDA` (info_sezioni.py): è letta dal pulsante INFORMAZIONI, dalla ricerca e dall'assistente (scritto e vocale). Qui si AGGIUNGONO le schede che mancavano (nessuna scheda esistente è toccata):
• Auto: garage, Carta di Circolazione e revisioni, Diagnostica veicoli, fotografare una spia (limite giornaliero e chiave propria), spie condivise e proposte, patente e multe, viaggi e rimborsi, Cestino, problemi comuni;
• Archivio: una guida completa (prima non aveva né guida né pulsante Informazioni);
• Cestino («eliminare e ripristinare») in Dispensa, Salute, Documenti, Casa, Lavoro, Auto, Utilità;
• Utilità: Aspetto dell'app, Scambia dati, Libera spazio, il mio nome, il Cestino; Dispensa e Salute: la barra in basso che si scorre;
• i titoli delle finestre Informazioni di Casa, Lavoro, Auto e Archivio (prima comparivano nomi tecnici come «sez_casa»);
• per OGNI sezione la scheda «📌 Versione di queste istruzioni» e GUIDA_VERSIONI (versione, data, moduli descritti): chi modifica un modulo deve riguardare la scheda e alzare la versione (lo strumento di controllo `prova_guide.py` segnala le sezioni i cui moduli sono cambiati dopo l'ultima conferma);
• le novità («Cosa c'è di nuovo» dell'assistente).
Le istruzioni sono SOLO in italiano (le traduzioni si aggiornano a lavoro finito, su richiesta).
Caricato dopo tutti i moduli che aggiungono schede alla guida."""

GUIDA_VERSIONE = "2.5"
GUIDA_DATA = "2026-11-08"
GUIDA_VERSIONI = {
    "dispensa": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["assistente.py", "assistente_extra.py", "accessibilita.py", "parte3.py", "parte4.py", "elimina.py", "dispensa_famiglia.py", "statistiche.py", "spesa.py", "cestino.py", "stile.py"]},
    "farmacia": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["farmacia.py", "salute_plus.py", "salute_esenzioni.py", "salute_catalogo.py", "famiglia.py", "invio.py", "cestino.py"]},
    "documenti": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["farmacia.py", "cestino.py"]},
    "archivio": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["archivio.py", "immagini_sicure.py", "cestino.py"]},
    "casa": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["casa.py", "assistente_extra.py", "cestino.py"]},
    "lavoro": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["lavoro.py", "casa.py", "cestino.py"]},
    "auto": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["assistente_extra.py", "auto.py", "auto_pagine.py", "auto_diagnosi.py", "auto_base.py", "auto_proposte.py", "auto_archivio.py", "auto_soccorso.py", "auto_emergenza.py", "libretto.py",
                                                                         "diagnostica.py", "diagnostica_dtc.py", "diagnostica_ble.py", "diagnostica_spie.py", "cestino.py"]},
    "utilita": {"versione": GUIDA_VERSIONE, "data": GUIDA_DATA, "moduli": ["assistente.py", "assistente_extra.py", "utilita.py", "libera_spazio.py", "scambio.py", "nomi_utenti.py", "musica.py", "cestino.py", "accessibilita.py"]},
}


def _gx_aggiungi(sez, cid, titolo, corpo, chiavi, meta=None):
    """Aggiunge una scheda alla base unica (salta se esiste già). `chiavi` = parole con cui la si cerca (e l'assistente la trova)."""
    ids = _ID_GUIDA.setdefault(sez, [])
    lista = _GUIDE.setdefault(sez, [])
    if cid in ids:
        return
    ids.append(cid)
    lista.append((titolo, corpo.strip(), chiavi))
    if meta:
        _META_GUIDA[cid] = meta


def _gx_costruisci():
    # ---- i titoli che mancavano (comparivano «sez_casa»…)
    UI_IT.update({"sez_casa": "🏡 Casa", "sez_lavoro": "💼 Lavoro", "sez_auto": "🚗 Auto", "sez_archivio": "🗂️ Archivio"})
    a = _gx_aggiungi

    # ================= il Cestino: una scheda in ogni sezione, scritta per quella sezione
    a("dispensa", "d_cestino", "🗑️ Eliminare un prodotto e recuperarlo (Cestino)",
      """**Eliminare:** tocca il prodotto → **🗑️ Elimina**, scegli le voci e conferma. Non sparisce subito: va nel **Cestino** per 30 giorni.

**Annullare subito:** in cima alla pagina compare «🗑️ … spostato nel Cestino» con il pulsante **↩️ Annulla**: toccalo e il prodotto torna al suo posto (resta visibile circa 40 secondi).

**Recuperarlo dopo:** **Home → 🧰 Utilità → 🗑️ Cestino**. Trovi l'elenco con la data di eliminazione e fra quanti giorni si cancella da solo. Tocca **↩️ Ripristina** per rimetterlo in dispensa, oppure **🗑️ Elimina per sempre** (ti chiede conferma).

**Non vanno nel Cestino** i prodotti che segni come finiti («L'ho consumato / finito») o buttati: vanno nelle statistiche.""",
      "cestino ripristina recupera recuperare eliminato eliminati eliminare cancellato per sbaglio annulla indietro prodotto dispensa", ("recupera", "prodotto"))
    a("farmacia", "f_cestino", "🗑️ Eliminare e ripristinare con il Cestino",
      """Quando elimini un medicinale, una terapia, una prescrizione, una visita, un vaccino, un documento o un intero profilo, **non sparisce subito**: va nel **Cestino** per 30 giorni (puoi cambiare i giorni in **Utilità → Cestino**).

- **Subito dopo:** in cima compare **↩️ Annulla**.
- **Più tardi:** in fondo alla pagina apri **🗑️ Cestino di questa sezione**: tocca **↩️ Ripristina** (torna al suo posto, con foto e allegati) oppure **🗑️ Elimina per sempre**.
- **Un profilo** eliminato porta con sé i suoi medicinali, visite e documenti: nel Cestino sono **un solo elemento** e si ripristinano insieme.
- Gli allegati (foto, PDF) restano al sicuro finché l'elemento è nel Cestino; si cancellano davvero quando lo elimini per sempre o scade.""",
      "cestino ripristina ripristinare recupera recuperare eliminato eliminata per sbaglio annulla profilo medicinale visita terapia documento", ("recupera", None))
    a("documenti", "x_cestino", "🗑️ Recuperare un documento eliminato (Cestino)",
      """Un documento eliminato va nel **Cestino**, con le sue foto e i suoi allegati, per 30 giorni.

1. Appena eliminato: in cima tocca **↩️ Annulla**.
2. Più tardi: in fondo a questa pagina apri **🗑️ Cestino di questa sezione** e tocca **↩️ Ripristina**.
3. Se vuoi davvero toglierlo: **🗑️ Elimina per sempre** (con conferma). Dopo 30 giorni si cancella da solo.""",
      "cestino ripristina recupera recuperare documento eliminato eliminata per sbaglio annulla patente tessera carta identità", ("recupera", "documento"))
    a("casa", "c_cestino", "🗑️ Eliminare e ripristinare (beni, documenti, manutenzioni)",
      """Beni, documenti, bollette, manutenzioni, riferimenti e case eliminati vanno nel **Cestino** per 30 giorni.

- **Subito:** **↩️ Annulla** in cima alla pagina.
- **Dopo:** in fondo alla sezione Casa apri **🗑️ Cestino di questa sezione** → **↩️ Ripristina** o **🗑️ Elimina per sempre**.
- Se elimini un **bene con i suoi documenti**, nel Cestino sono un solo elemento e tornano insieme.
- Le **bollette pagate** con la ricevuta collegata tornano con il collegamento.""",
      "cestino ripristina recupera recuperare bene documento bolletta manutenzione eliminato per sbaglio annulla casa", ("recupera", None))
    a("lavoro", "l_cestino", "🗑️ Eliminare e ripristinare (buste paga, CU, rubrica)",
      """Una busta paga, una CU, un documento INPS, un lavoro o un contatto eliminati vanno nel **Cestino** per 30 giorni.

- **Subito:** **↩️ Annulla** in cima.
- **Dopo:** in fondo alla sezione Lavoro apri **🗑️ Cestino di questa sezione** → **↩️ Ripristina** (torna con il suo file) oppure **🗑️ Elimina per sempre**.""",
      "cestino ripristina recupera recuperare busta paga cu inps contatto lavoro eliminata per sbaglio annulla", ("recupera", None))
    a("auto", "au_cestino", "🗑️ Eliminare e ripristinare nell'Auto",
      """Veicoli, documenti, interventi, rifornimenti, spese, pneumatici, patenti, multe e viaggi eliminati vanno nel **Cestino** per 30 giorni.

- **Subito:** **↩️ Annulla** in cima.
- **Dopo:** in fondo alla pagina Auto apri **🗑️ Cestino di questa sezione** → **↩️ Ripristina**.
- **Un veicolo** eliminato torna con **tutto quello che conteneva** (interventi, documenti, foto).
- Se elimini un veicolo e poi cerchi di ripristinare solo un suo intervento, ti dirà di ripristinare prima il veicolo.""",
      "cestino ripristina recupera recuperare veicolo auto intervento documento eliminato per sbaglio annulla", ("recupera", None))
    a("utilita", "u_cestino", "🗑️ Il Cestino: tutto in un posto",
      """Qui trovi **tutto quello che hai eliminato** da tutte le sezioni.

1. Apri **Home → 🧰 Utilità** e tocca **🗑️ Cestino (N)**.
2. Per ogni elemento vedi la sezione, la data e fra quanti giorni si cancella da solo.
3. **↩️ Ripristina** lo rimette al suo posto. **🗑️ Elimina per sempre** lo toglie davvero (chiede conferma).
4. **🗑️ Svuota tutto il Cestino** toglie tutto.
5. In fondo scegli **per quanti giorni tenere** gli elementi: 7, 15, 30, 60 o 90.

Il Cestino comprende **i tuoi dati personali** e, se sei l'amministratore, anche i prodotti eliminati dalla **dispensa di famiglia** (quella condivisa): li trovi in **🗑️ Cestino della dispensa di famiglia**, solo tu li vedi e li puoi ripristinare. Se condividi la tua dispensa con altre persone, anche i prodotti eliminati da loro finiscono nel tuo Cestino.""",
      "cestino svuota ripristina recupera giorni conservazione eliminati tutto elenco utilità", ("recupera", None))

    # ================= salvare un prodotto
    a("dispensa", "d_salva", "💾 Salvare un prodotto: i due pulsanti",
      """Nella scheda **Aggiungi**, dopo aver scritto il nome e quante unità hai, ci sono due modi per salvare:

- **💾 Salva in dispensa** (il pulsante verde che resta sempre in vista sopra la barra in basso): salva il prodotto e **ti riporta alla scheda Dispensa**, dove lo vedi nell'elenco.
- **➕ Salva e aggiungi un altro prodotto**: salva e **resta nella scheda Aggiungi** con il modulo vuoto, comodo quando ne inserisci tanti.

**Il tasto Invio della tastiera non salva**: serve solo a confermare quello che hai scritto in quel campo. Per salvare tocca sempre il pulsante.

Se manca qualcosa (il nome o le unità) compare **un avviso sopra i pulsanti** e un messaggio giallo in alto, e il prodotto non viene salvato finché non lo completi.""",
      "salvare aggiungere prodotto pulsante salva invio tastiera non salva torna dispensa un altro pannello non si chiude unità nome", ("aggiungi", "prodotto"))

    # ================= i colori dei comandi
    colori = ("🎨 I colori dei comandi: sempre uguali",
              """In tutta l'app i pulsanti più usati hanno **sempre lo stesso colore**, così li riconosci anche senza leggere:

- **Rosso** → **Elimina** (🗑️). Quello che elimini va nel Cestino e lo puoi recuperare.
- **Blu** → **Modifica** (✏️).
- **Verde** → **Invia** o **Condividi** (📤, ✉️, 💬).
- **Grigio** → **Indietro** (←).

I pulsanti grandi e colorati in alto (Dispensa, Salute, Casa…) servono per cambiare sezione; quelli verdi scuri con la scritta bianca sono le azioni principali, come **Salva** o **Conferma**.""",
              "colori pulsanti rosso blu verde grigio elimina modifica invia indietro riconoscere comandi")
    a("dispensa", "d_colori_cmd", *colori, meta=("vedi", None))
    a("utilita", "u_colori_cmd", *colori, meta=("vedi", None))

    # ================= tanti prodotti
    a("dispensa", "d_mostra_altri", "📃 Tanti prodotti: «Mostra altri»",
      """Per tenere l'app veloce, in ogni gruppo della Dispensa (per esempio «Scadono entro 2 mesi» o «Ancora buoni») si vedono **30 schede per volta**.

Se ce ne sono di più, sotto l'ultima trovi il pulsante **⬇ Mostra altri** (con scritto quanti prodotti aggiunge, quanti ne vedi e quanti ce ne sono). Toccalo per vederne altri 30.

Per trovare subito un prodotto senza scorrere, usa la **ricerca** in alto. Con la vista **📋 Tabella** vedi tutti i prodotti in una lista unica scorrevole.""",
      "tanti prodotti mostra altri schede lente veloce elenco lungo scorrere troppi cercare trovare", ("vedi", "prodotto"))

    # ================= l'assistente: manuali e voce
    manuali = ("📚 Cercare nei miei manuali e documenti",
               """Sotto il pulsante **Informazioni** trovi **📚 Cerca nei miei manuali e documenti**.

1. Tocca il pulsante e scrivi cosa cerchi, per esempio «pulire il filtro della lavatrice» o «pressione della caldaia».
2. Tocca **🔎 Cerca**. L'app non legge tutto l'archivio: sceglie i documenti che c'entrano (per titolo, marca, modello, bene), li legge una volta sola e ti mostra **i 3 passaggi più adatti**, con il **nome del documento, la pagina** e **dove si trova** nell'app.
3. **🔊 Leggi ad alta voce** li legge con la voce del telefono; **⏹ Ferma la voce** la ferma.

Cerca **solo nei tuoi** manuali, garanzie e documenti dei beni di Casa e nei documenti dei veicoli. Ti mostra **le parole del manuale**: non le riassume né le spiega con l'intelligenza artificiale.

**Se non trova niente** te lo dice e non inventa: prova con altre parole, oppure apri il documento. Se non hai ancora manuali, caricane uno da **Casa → 📚 Documenti**.""",
               "manuale manuali istruzioni cercare cerca nei documenti pdf pagina leggere ad alta voce apparecchio lavatrice caldaia libretto uso manutenzione")
    for sez in ("dispensa", "casa", "auto", "utilita"):
        a(sez, "m_manuali_" + sez, *manuali, meta=("vedi", "documento"))
    voce = ("🔊 La voce dell'assistente: più lenta o più veloce",
            """Apri il robottino e tocca **🐢 Velocità della voce**: a ogni tocco passa da **normale** a **veloce**, poi **lenta**, poi di nuovo normale, e ti fa sentire una frase di prova. La scelta resta **salvata sul telefono**.

Con **🔊 Voce: attiva** (o **🔇 Voce: spenta**) accendi o spegni la voce; con **⏹ Silenzio** la fermi subito. Se il microfono o la voce non funzionano sul tuo telefono, puoi sempre **scrivere** la domanda.""",
            "voce velocità lenta veloce parla piano più piano più veloce ascoltare assistente audio microfono")
    a("dispensa", "d_voce", *voce, meta=("modifica", None))
    a("utilita", "u_voce", *voce, meta=("modifica", None))

    # ================= lo storico delle modifiche
    for sez in ("farmacia", "documenti", "archivio", "casa", "lavoro", "auto", "utilita", "dispensa"):
        dove = ("Apri **Home → 🧰 Utilità** e tocca **🕘 Storico delle modifiche**." if sez in ("dispensa", "utilita") else
                "In fondo alla pagina apri **🕘 Storico delle modifiche di questa sezione** (per le operazioni di tutte le sezioni: **Utilità → 🕘 Storico delle modifiche**).")
        a(sez, "rm_" + sez, "🕘 Storico delle modifiche: cosa è stato fatto e quando",
          f"""È il **registro delle operazioni**: dice che cosa è stato **aggiunto, modificato, eliminato o ripristinato** e **quando**.

{dove}

- Ogni riga ha il nome dell'elemento, la data e l'ora e, per le modifiche, **quali campi sono cambiati** (per esempio «campi: nome, scadenza»).
- **Non contiene i dati veri** (non vedi il vecchio e il nuovo valore): serve a sapere cosa è successo, non a tornare indietro. Per tornare indietro su un'eliminazione usa il **Cestino**.
- Non è lo «storico dei contenuti» (gli elenchi di ciò che hai registrato: terapie fatte, visite passate, consumi…): quelli restano nelle loro schede.
- Restano le ultime 300 operazioni, per al massimo 180 giorni. Vale per i tuoi dati personali; la dispensa di famiglia ha il suo storico con «Annulla» per l'amministratore.""",
          "storico modifiche registro cronologia cosa ho cambiato quando chi ha modificato aggiunto eliminato log operazioni", ("vedi", None))

    # ================= la barra in basso
    barra = ("📱 La barra in basso: scorri fino all'ultima voce",
             """In basso c'è una **barra con le voci della pagina** (per esempio in Salute: Medicinali, Terapie, Prescrizioni, Visite, **Vaccini**). Su un telefono non entrano tutte: **fai scorrere la barra con il dito verso sinistra** finché non compare l'ultima.

La barra è un po' più corta di tutta la larghezza di proposito: a destra, in basso, Streamlit mette un **rettangolo rosso** e a volte un **cerchio con il profilo**, e così non coprono le voci.

Se una voce non si vede, scorri la barra **a sinistra**: è lì, solo fuori schermo.""",
             "barra in basso scorrere scorri voci vaccini ultima voce non vedo non riesco schede menu sotto")
    a("dispensa", "d_barra", *barra, meta=("vedi", None))
    a("farmacia", "f_barra", *barra, meta=("vedi", None))

    # ================= Utilità
    a("utilita", "u_aspetto", "⚙️ Aspetto dell'app: testi grandi, radio, freccia",
      """Apri **Utilità → ⚙️ Aspetto dell'app**.

- **🔤 Grandezza dei testi:** normale, grande, molto grande. Serve per leggere meglio senza stringere gli occhi.
- **🎧 Radio di sottofondo:** mostra o nasconde la linguetta della radio sul bordo sinistro.
- **Freccia «torna su»:** scegli se sta a destra o a sinistra.
- **✏️ Il mio nome:** cambia il nome con cui compari nell'app (il nome dell'amministratore si cambia dai Secrets).
- **🧹 Libera spazio:** attiva o spegne il promemoria per cancellare dal telefono i file già archiviati.""",
      "aspetto testo grande piccolo grandezza caratteri radio freccia torna su nome cambiare leggere ingrandire", ("modifica", None))
    a("utilita", "u_scambio", "📦 Scambiare i dati con un altro utente",
      """In **Utilità → 📦 Scambia i dati con un altro utente (esporta e importa)** crei un file **.dispensa** con le parti che scegli (Dispensa, Salute, Casa, Lavoro) e lo mandi a un'altra persona.

- Si può **proteggere con una password**.
- Chi lo riceve lo **importa**: le cose si **aggiungono** ai suoi dati, senza toccare quelle che ha già.
- Per importare, il file si carica con il **pulsante arancione**.""",
      "scambio scambiare trasferire dati esportare importare condividere file dispensa altro utente password", ("esporta", None))
    a("utilita", "u_libera", "🧹 Libera spazio sul telefono",
      """Quando archivi un file dal telefono (foto, PDF), l'app non può cancellarlo dal telefono da sola: lo permette soltanto il telefono.

Dopo l'archiviazione compare **🧹 Libera spazio** con nome e peso del file e il percorso per eliminarlo (Galleria o File → tieni premuto → Elimina). Su Chrome per computer c'è anche **🗑️ Elimina dal computer**.

Per non vederlo più tocca **🔕 Non ricordarmelo più** (si riattiva da Aspetto dell'app).""",
      "libera spazio cancellare telefono foto file archiviato memoria piena eliminare dal telefono", ("elimina", None))

    # ================= Archivio (nuova guida completa)
    a("archivio", "ar_cosa", "🗂️ A cosa serve l'Archivio",
      """L'Archivio raccoglie **in un posto solo tutti i file della sezione Salute**: bugiardini, foto delle confezioni, documenti personali, prescrizioni, referti e documenti vaccinali, con la persona e il medicinale o la visita a cui sono collegati.

Serve a **ritrovare un file** senza ricordare in quale scheda l'avevi messo. Non si caricano file da qui: i file si aggiungono dalle schede di Salute e compaiono da soli nell'Archivio.""",
      "archivio a cosa serve cos'è tutti i file bugiardini foto documenti dove trovo salvato", ("vedi", None))
    a("archivio", "ar_cercare", "🔎 Cercare e filtrare i file",
      """- Scrivi nella casella di ricerca il nome, il medicinale, la persona: l'elenco si restringe.
- Scegli il modo di vedere: **📇 Schede** (una scheda per file) o **📋 Tabella** (più file in una volta).
- **🔍 Altri filtri: persona, tipo di file, data, ordine** per restringere ancora, e per ordinare dal più recente.
- In fondo, **Mostra altri** carica altri file: se ne vedono pochi alla volta per tenere l'app veloce.""",
      "cercare ricerca filtrare filtri persona data ordine tipo file schede tabella dove trovo", ("vedi", None))
    a("archivio", "ar_modifica", "✏️ Correggere un dato o sostituire un file",
      """**Da qui i file non si modificano**: l'Archivio serve a ritrovarli, aprirli, scaricarli, inviarli ed eliminarli.

- **Correggere un dato** (il nome del medicinale, la data di una visita…): vai nella scheda di **Salute** a cui il file è collegato e tocca **Modifica**.
- **Sostituire un file** con uno nuovo: aggiungi il nuovo dalla scheda di Salute e poi **🗑️ Elimina** il vecchio qui (resta 30 giorni nel Cestino, nel caso ti serva ancora).""",
      "modificare correggere cambiare sostituire file archivio dato nome data", ("modifica", None))
    a("archivio", "ar_aprire", "👁️ Aprire, scaricare e inviare un file",
      """Su ogni scheda:
- **👁️ Apri** mostra l'anteprima (le foto si vedono qui; i PDF si scaricano e si aprono con il telefono). **🙈 Chiudi** la richiude.
- **⬇ Scarica** salva il file sul telefono.
- **📤 Invia** lo manda per **email, WhatsApp, Telegram** o con il **menu di condivisione del telefono**.
- **Tabella:** tocca più righe, poi **📦 Prepara lo ZIP** e **⬇ Scarica lo ZIP** per averli tutti insieme.

Se un canale non può mandare il file allegato, l'app te lo dice e ti propone di scaricarlo e inviarlo dal menu di condivisione.""",
      "aprire anteprima scaricare scarica inviare invia whatsapp email telegram zip condividere file allegato", ("condividi", None))
    a("archivio", "ar_elimina", "🗑️ Eliminare file e recuperarli",
      """- **🗑️ Elimina** su una scheda, oppure scegli più righe in **Tabella** → **🗑️ Elimina (N)**, e conferma.
- Il file esce dall'elenco e dai punti in cui era collegato (medicinale, visita…): va nel **Cestino** per 30 giorni.
- Per recuperarlo: **↩️ Annulla** subito in cima alla pagina, oppure **Utilità → 🗑️ Cestino** o il Cestino in fondo a **Salute**.""",
      "eliminare elimina cancellare file archivio cestino ripristina recupera annulla", ("elimina", None))
    a("archivio", "ar_problemi", "🛠️ Problemi comuni nell'Archivio",
      """- **«Questa immagine non si può mostrare qui»:** il file è danneggiato oppure in un formato che l'app non apre (per esempio HEIC). Tocca **⬇ Scarica** e aprilo con il telefono.
- **«Non trovo questo file nell'archivio»:** il file è stato eliminato (da un'altra scheda o da un'altra persona) o non è stato salvato bene. Cerca nel **Cestino** di Salute; se non c'è, caricalo di nuovo dalla scheda di Salute.
- **L'elenco sembra corto:** hai un filtro attivo, controlla **Altri filtri**.
- **L'app è lenta con molte foto:** apri una scheda alla volta.""",
      "problema errore immagine non si vede foto non si vede non trovo file danneggiato heic lento", ("vedi", None))

    # ================= Auto
    a("auto", "au_garage", "🏠 Il garage: la schermata iniziale",
      """Aprendo **Auto** vedi il **Garage personale**: la scheda del veicolo scelto (foto, nome, anno, targa), le **scadenze in evidenza** (le tre più urgenti), e i tasti colorati che portano alle sezioni: scheda e documenti, scadenze, manutenzione, rifornimenti e spese, ricambi e valore, emergenza, patente e multe, **diagnostica veicoli**.

- **Foto del mezzo:** tocca per aggiungerla.
- **Carica e autonomia** (per i mezzi elettrici): li scrivi tu, l'app **non è collegata all'auto**.
- **Ultima posizione salvata:** scrivi dove hai parcheggiato oppure tocca il pulsante per prendere la posizione dal GPS del telefono, poi **Salva la posizione**.
- Dalle sezioni torni indietro con **← Torna al garage**.""",
      "garage schermata iniziale auto veicolo scadenze in evidenza posizione parcheggio foto del mezzo", ("vedi", "veicolo"))
    a("auto", "au_libretto", "📄 Leggere la Carta di Circolazione (e le revisioni sul retro)",
      """In **➕ Aggiungi un mezzo** carica la **Carta di Circolazione** (PDF o foto: meglio anche il retro, con i timbri delle revisioni). L'app la legge in **circa un minuto** e ti propone i dati: targa, telaio, marca, modello, date, cilindrata, potenza, alimentazione, classe Euro, masse, posti, dimensioni, consumi, pneumatici e altro.

- Ogni dato ha un pallino che dice quanto è sicuro: 🟢 sicuro, 🟡 abbastanza, 🟠 poco sicuro. **Controlla e correggi** i dati prima di salvare.
- **🔧 Revisioni lette sul retro:** spunta quelle giuste; l'app registra l'ultima revisione, la prossima scadenza e lo storico. Le revisioni vecchie o sbiadite potrebbero non essere lette: le puoi aggiungere a mano.
- Se è attiva un'intelligenza artificiale, compare **🤖 Controlla con l'intelligenza artificiale**: rilegge le pagine e confronta (conta come una delle tue analisi gratuite del giorno).
- Meglio una **scansione** o una foto **dritta e con buona luce**: con foto inclinate o scure legge peggio.""",
      "libretto carta di circolazione leggere lettura targa telaio revisione revisioni retro timbri pallini controlla", ("aggiungi", "veicolo"))
    a("auto", "au_diag", "🩺 Diagnostica veicoli: le sei schede",
      """Dal garage tocca **🩺 Diagnostica veicoli**. Le sei schede:
1. **📷 Fotografa una spia** — fotografi il cruscotto e ti dice cosa significa la spia.
2. **📚 Consulta archivio spie** — catalogo con ricerca (nome, simbolo, colore, categoria) e la **base condivisa** delle spie trovate da tutti.
3. **🔌 Collega dispositivo diagnostico** — dongle OBD con Bluetooth a basso consumo (solo Chrome su Android; non tutti i dongle funzionano).
4. **🔢 Leggi codici errore** — scrivi o incolla un codice (P0301…) e ti dà significato, cause e controlli.
5. **🗂️ Consulta storico guasti** — foto, letture e consulenze salvate, con stato, intervento e note.
6. **🤖 Chiedi all'assistente AI** — descrivi il problema e ti dà un elenco ordinato: guasto confermato, probabile, possibile causa, controlli.

**Importante:** l'app non sostituisce un meccanico. Per le spie **rosse** ferma il mezzo in sicurezza.""",
      "diagnostica veicoli spie cruscotto guasti codici errore obd dongle bluetooth storico assistente ai", ("vedi", "veicolo"))
    a("auto", "au_foto_spia", "📷 Fotografare una spia (e il limite giornaliero)",
      """1. **Diagnostica veicoli → 📷 Fotografa una spia**.
2. In **Di che mezzo è la spia** scegli il mezzo **giusto** (per esempio *Camion / TIR*): vale la tua scelta, non il veicolo registrato. Facoltativo: marca e modello.
3. Fotografa **solo il cruscotto**, senza persone, targhe o documenti.
4. Il risultato dice colore, urgenza, significato, cosa fare e possibili cause, e il confronto con il **catalogo verificato**. Per le spie **rosse** compare prima l'avviso di PERICOLO.
5. **💾 Salva nel veicolo** per tenere foto e risultato in **🗂️ Diagnosi salvate**.

**Limite:** con la chiave dell'app hai di norma **2 analisi gratuite al giorno**. Finite, puoi usare una **tua chiave gratuita** (OpenRouter o Google Gemini: l'app ti mostra la guida passo passo) oppure aspettare il giorno dopo. Senza intelligenza artificiale restano il catalogo e la ricerca.

**Può sbagliare:** controlla sempre con il manuale del mezzo.""",
      "fotografare foto spia cruscotto limite analisi due al giorno chiave propria openrouter gemini camion tir mezzo", ("aggiungi", None))
    a("auto", "au_proposte", "📚 Spie condivise: proporre una spia (la verifica l'amministratore)",
      """La **base condivisa** contiene le spie e i guasti che aiutano tutti. **Nessuna spia entra da sola**: prima la controlla l'amministratore.

**Per proporre una spia che hai riconosciuto:**
1. Sotto il risultato tocca il pulsante grande **📤 PROPONI ALLA BASE CONDIVISA** (o, per scrivere a mano, **➕ Proponi una spia o un guasto alla base**).
2. Scegli **per quale mezzo** hai fatto la ricerca (obbligatorio), scrivi marca e modello se vuoi, e **correggi il testo** che vuoi salvare.
3. Spunta **«Ho controllato il testo e la foto»** e tocca **📤 Invia all'amministratore**.

All'amministratore arrivano **la foto, il testo, il tipo di ricerca, il mezzo e il modello**. Tu vedi lo stato in **📬 Le mie proposte** (in attesa, approvata, rifiutata con il motivo). Massimo **5 proposte al giorno**.

**Se sei l'amministratore:** **🛠️ Proposte da verificare** e **🗄️ Archivio completo (testo e foto insieme)** (voci con foto, ricerca, Conferma/Contesta, Modifica, Foto, Elimina).""",
      "proporre proposta spia base condivisa verifica amministratore approvare rifiutare archivio completo foto testo", ("aggiungi", None))
    a("auto", "au_patente", "👤 Patente e multe",
      """Da **Auto → 👤 Patente e multe** (anche senza veicoli):
- **Patente:** scadenza, visita medica, CQC e punti. L'app ti avvisa con anticipo.
- **Multe (verbali):** importo, stato (da pagare, pagata, ricorso), «pagare entro». Per ogni voce puoi allegare una foto, correggere, inviare o eliminare.""",
      "patente multa multe verbale punti cqc visita medica scadenza pagare ricorso", ("aggiungi", None))
    a("auto", "au_viaggi", "🧭 Viaggi e rimborsi",
      """In **Rifornimenti e spese → 🧭 Viaggi e rimborsi** registri i viaggi (personali o di lavoro) con i chilometri.

Se scrivi la **tariffa per chilometro** che ti spetta, l'app calcola il **rimborso** dei viaggi di lavoro, per anno e per mese, e prepara un report da inviare. Le tabelle ufficiali ACI **non** sono incluse: la tariffa la scrivi tu.""",
      "viaggi rimborso chilometrico tariffa km lavoro trasferta report", ("aggiungi", None))
    a("auto", "au_problemi", "🛠️ Problemi comuni nell'Auto",
      """- **Il libretto non viene letto bene:** usa una scansione o una foto dritta e luminosa, controlla i dati con i pallini 🟠 e correggi a mano. Le revisioni vecchie si aggiungono a mano.
- **«Hai finito le tue analisi gratuite di oggi»:** è il limite giornaliero. Segui la guida per una chiave gratuita oppure riprova domani.
- **La spia riconosciuta sembra sbagliata:** controlla di aver scelto il **mezzo giusto** e confrontala con il manuale; se è sbagliata nella base, dillo all'amministratore.
- **Il dongle Bluetooth non compare:** serve Chrome su Android e un dongle a basso consumo (BLE); molti economici non lo sono.
- **Ho eliminato qualcosa per sbaglio:** guarda il **Cestino** in fondo alla pagina.
- **Una foto non si vede:** il file potrebbe essere rovinato; la foto originale si scarica dal pulsante accanto.""",
      "problema errore libretto non letto analisi finite spia sbagliata dongle bluetooth non compare foto non si vede eliminato per sbaglio", ("vedi", None))

    # ================= una scheda «Versione» per ogni sezione
    for sez, info in GUIDA_VERSIONI.items():
        data = "/".join(reversed(info["data"].split("-")))
        a(sez, "ver_" + sez, "📌 Versione di queste istruzioni",
          f"""Queste istruzioni sono la **versione {info['versione']}** del **{data}**.

Descrivono l'app **come è oggi**. Se un pulsante o una scritta è **diverso** da come è spiegato qui, forse le istruzioni sono rimaste indietro: **scrivilo all'amministratore** così le aggiorna. L'assistente usa le stesse istruzioni, quindi risponde in base a questa versione.""",
          "versione istruzioni aggiornate aggiornamento guida non aggiornata", ("vedi", None))

    # ================= le novità («Cosa c'è di nuovo»)
    if any(n[2] == "Cestino" for n in _NOVITA):
        return
    _NOVITA.extend([
        ("2026-11-08", "🗑️", "Cestino", "Quello che elimini resta 30 giorni: «↩️ Annulla» in cima, Cestino in fondo a ogni sezione e in Utilità"),
        ("2026-11-08", "🗂️", "Archivio con guida", "Archivio → pulsante «Clicca per informazioni» con le istruzioni"),
        ("2026-11-08", "🩺", "Spie condivise e proposte", "Auto → Diagnostica veicoli → «📤 Proponi alla base condivisa»"),
        ("2026-11-08", "🕘", "Storico delle modifiche", "In fondo a ogni sezione e in Utilità: cosa è stato aggiunto, modificato o eliminato, e quando"),
        ("2026-11-08", "📚", "Cerca nei miei manuali", "Sotto il pulsante «Informazioni»: «📚 Cerca nei miei manuali e documenti»"),
        ("2026-11-08", "🐢", "Velocità della voce", "Nel pannello del robottino: «🐢 Velocità della voce» (lenta, normale, veloce)"),
        ("2026-11-08", "📱", "Barra in basso", "Scorri le voci con il dito verso sinistra fino all'ultima (per esempio Vaccini)"),
    ])


_gx_costruisci()
