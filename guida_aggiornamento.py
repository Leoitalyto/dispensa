# -*- coding: utf-8 -*-
"""AGGIORNAMENTO DELLE ISTRUZIONI E DELL'ASSISTENTE (20 novembre 2026), in italiano; le traduzioni sono in guida_agg_xx.py (en, es, fr, de, ro, ar, pt).

RICHIESTA (Leonardo): «aggiorna le spiegazioni dell'app e l'assistente in tutte le lingue».
• Nuove schede: Diario dei ricordi, lettura e riclassifica dei documenti con l'IA, N° dei documenti sanitari, gruppo sanguigno e certificato,
  «📖 Cos'è?» (Wikipedia), avvisi meteo, nomi a scelta negli elenchi con «Altro», lingua all'accesso.
• Aggiornate: 🤖 Intelligenza artificiale (servizi, DeepSeek riservato, lettura in sottofondo), Compleanni (il diario ha la sua scheda).
• «Cosa c'è di nuovo» dell'assistente: le novità di questi giorni (con le traduzioni).
• Versione delle istruzioni: 5.2 del 20/11/2026 (in tutte le lingue).
L'assistente (scritto e vocale), la ricerca e il pulsante Informazioni leggono tutti questa stessa base (_GUIDE), quindi rispondono anche sulle novità.
Caricato dopo guida_completa.py."""

GA_VERSIONE, GA_DATA, GA_DATA_IT = "5.6", "2026-11-27", "27/11/2026"

GA_SCHEDE = {
    "x_ia": ("🤖 Intelligenza artificiale: documenti, scritte a mano, spie, lingue",
             """Con le **chiavi** dei servizi di intelligenza artificiale (gratuiti: Groq, Google Gemini, OpenRouter, NVIDIA, Cloudflare, Cohere, Hugging Face, SambaNova con credito di prova; **DeepSeek** a pagamento, facoltativo) l'app:
- **legge e classifica i documenti sanitari** (che documento è, area medica, esame, date, medico, struttura, conclusioni). Se è **scritto a mano** lo leggono **più servizi** e un «arbitro» confronta le letture: vedi **chi l'ha letto**, i **limiti** e **cosa verificare** sul foglio. Niente si salva senza la tua conferma;
- **riconosce le spie dell'auto**, confrontando più letture quando la foto è incerta;
- **traduce le pagine** nella lingua scelta (la prima volta che una pagina si apre; poi resta salvato per tutti);
- fa rispondere **l'assistente** nella lingua scelta.
Se un servizio è esaurito o lento, l'app passa da sola al successivo.

**DeepSeek è a pagamento**: lo usa **solo l'amministratore** e le persone che lui sceglie (Utilità → 🤖 → DeepSeek → **🔒 Chi può usarlo**). Nella stessa riga si vede il **💰 credito rimasto**. Le traduzioni automatiche non usano mai i servizi a pagamento.

Le chiavi le mette l'amministratore in **Utilità → 🤖 Intelligenza artificiale**, con la guida passo passo; **🔄 Ricontrolla le chiavi** e la **prova** di ogni servizio dicono se funziona. Attenzione: con le chiavi gratuite di Google i testi possono essere usati per migliorare i loro modelli.""",
             "intelligenza artificiale ia chiavi gemini groq openrouter nvidia cloudflare cohere hugging face sambanova deepseek credito chi può usarlo manoscritto spie traduzione"),
    "x_compleanni": ("🎂 Compleanni: le schede delle persone",
                     """In **Utilità → 🎂 Compleanni** tocca il **badge «Buon compleanno»** per aprire l'elenco (toccalo di nuovo per chiuderlo).

- **➕ Aggiungi una persona**: nome e data di nascita (se non sai l'anno spunta **«Non conosco l'anno»**). Il resto è facoltativo: **foto, luogo di nascita, cognome, soprannome, cellulare, telefono, WhatsApp, Telegram, email, indirizzo, sito, idee regalo, note**. In **«Chi è per te»**, se scegli **Altro**, puoi scrivere tu la parola giusta.
- **La foto**: tocca «Scegli la foto»; **pizzica con due dita** per ingrandire e **trascina** per spostarla finché il viso sta nell'ovale. Più avanti puoi **🔄 Ricentrare** la foto.
- Ogni persona ha la sua **scheda con cornice neon** del colore del suo **segno zodiacale**, scelto dalla data. **I segni si muovono** (l'Ariete dà una testata con gli occhi infuocati, i Pesci nuotano lenti, il Cancro cammina di lato…).
- Sotto la scheda ci sono i tasti per **chiamare, WhatsApp, Telegram, email, sito**. L'elenco è in ordine di **prossimo compleanno** («🎉 Oggi!» se è oggi).
- Se **la persona non c'è più**, spunta **🕯️ Questa persona non c'è più**: compare una **candela accesa**, la scheda va in **In memoria** e trovi **⚰️ Dove riposa** (tipo di sepoltura, cimitero, posizione, concessione, lampada votiva, telefono e orari del cimitero, foto della lapide), la **preghiera dell'eterno riposo**, **✍️ un pensiero** e **🎙️ un messaggio vocale**.
- Il **bottone verde ⏻** dentro la scheda apre il **📖 Diario dei ricordi** (vedi la sua scheda).
- ✏️ **Modifica** cambia i dati (quello che non tocchi resta com'era); 🗑️ **Elimina** manda la scheda nel Cestino.""",
                     "compleanni compleanno segno zodiacale scheda persona foto contatti whatsapp telegram scomparso candela memoria sepoltura diario"),
    "x_diario": ("📖 Il Diario dei ricordi (foto, testi, musica)",
                 """Dentro la scheda di ogni persona dei **🎂 Compleanni**, in basso a destra, c'è il **bottone verde ⏻**. Toccalo: **la scheda sparisce e si apre il diario**, con le foto impilate come pagine di un libro.

- **Girare le pagine**: **◀ Indietro** e **Avanti ▶** in alto. Il **bottone rosso ⏻**, fra i due, chiude il diario e la scheda torna.
- **Scorrimento automatico**: le foto passano da sole ogni **7 secondi**; in **⏱️ Scorrimento automatico** scegli i secondi o lo spegni. Ogni foto **entra ed esce con un effetto sempre diverso**.
- **Aggiungere foto**: **➕ Aggiungi altre foto** (quante vuoi, non c'è un limite). Per ogni foto vedi l'**anteprima**: **pizzichi** con due dita per ingrandire e **trascini** per spostare; puoi scrivere **testi colorati** (colore, carattere, grandezza, posizione) e mettere **icone** (cuori, fiori, candele…). Poi **💾 Salva la pagina**. Le foto vengono alleggerite da sole senza perdere qualità.
- **Cambiare dopo**: con **✏️ Testi e icone** togli o cambi testi e icone quando vuoi; **↩️ Annulla l'ultima modifica** rimette com'era (la foto originale non si tocca mai). In **🗂️ Gestisci le pagine** sposti una pagina **⬆️ ⬇️**, **🔄 cambi la foto** o la **🗑️ elimini**.
- **Musica**: in **🎵 Musica del diario** scegli un file **MP3** (si salva da solo). Parte quando tocchi il bottone verde; in basso la **barretta del volume** (tocca o trascina) e ▶/🔊 per la pausa. Per cambiarla, scegli un altro file.""",
                 "diario dei ricordi diario foto pagine bottone verde rosso scorrimento musica mp3 volume testi icone effetti gestisci pagine compleanni"),
    "f_ia_documenti": ("🤖 Far rileggere e riclassificare i documenti dall'IA",
                       """In **Salute → Documenti sanitari** apri **🤖 Riclassifica i documenti con l'IA**.

1. Vedi **«Da controllare: X di Y»**: l'IA legge **solo i documenti non ancora controllati** (spunta «Rileggi anche quelli già controllati» per rileggerli tutti).
2. Tocca **🔍 Prova: leggi e classifica**. Compare un **riquadro sempre aperto** che si aggiorna da solo: documento a cui è arrivata, da quanti secondi, a quale servizio sta chiedendo, quanti ha letto, quanto manca. I pallini **●●●○** che si muovono dicono che sta lavorando.
3. **Puoi usare altre app o spegnere lo schermo**: la lettura continua da sola. Ogni documento è salvato appena letto, quindi niente si perde.
4. Un documento che resta bloccato viene **saltato dopo circa 2 minuti** («troppo lento, saltato») e si riprova la volta dopo. **⏹ Ferma la lettura** tiene quelli già letti.
5. Le **🟡 Proposte dell'IA da confermare** compaiono nello stesso riquadro, una per documento: lascia spuntato quello che va bene e tocca **✅ Applica**; **✖ Non applicare** lascia tutto com'è. Quello che hai corretto tu a mano non si tocca.

Anche **🔄 Rileggi i documenti già archiviati** (lettura senza IA) mostra **«Da rileggere: X di Y»** e non ripropone quelli già fatti.""",
                       "riclassifica documenti ia intelligenza artificiale rileggi lettura in corso proposte applica controllati sottofondo altre app ferma"),
    "f_numeri_doc": ("🔢 Il N° dei documenti sanitari (per il medico)",
                     """Ogni documento sanitario ha un **numero**: il **N° 1 è il più recente**, poi a scendere fino al più vecchio. Lo vedi in un **riquadro verde** su ogni scheda e nella colonna **N°** del **riepilogo PDF** della Salute.

**A cosa serve:** dai il riepilogo al medico; lui ti dice «portami il 4, il 12 e il 17». Tu scrivi il numero (per esempio **12**) nella casella **🔍 Cerca** dei Documenti sanitari e compare **solo quel documento**.

**Attenzione:** quando aggiungi un documento nuovo, diventa il N° 1 e gli altri **scalano di uno**. Se nel frattempo hai aggiunto documenti, **crea di nuovo il riepilogo PDF**. Nel PDF le date non vanno più a capo.""",
                     "numero documenti n° medico riepilogo pdf cerca numero ordine più recente portami"),
    "f_gruppo": ("🩸 Gruppo sanguigno e certificato",
                 """Nella scheda della persona in **Salute**: se il gruppo sanguigno non c'è, tocca **🩸 Inserisci il gruppo sanguigno**, sceglilo e salva. Puoi cambiarlo quando vuoi da **Modifica**.

Sotto puoi **allegare il certificato del gruppo sanguigno** (PDF o foto): scegli il file e si salva da solo. Lo vedi, lo scarichi o lo togli quando vuoi.""",
                 "gruppo sanguigno sangue certificato allegare pdf foto scheda persona"),
    "f_wiki": ("📖 «Cos'è?»: spiegazione semplice da Wikipedia",
               """In **Salute → Documenti sanitari** e in **Salute → Medicinali** c'è la tendina **📖 Cos'è? Spiegazione semplice (Wikipedia)**.

Scrivi il nome di un **esame, una malattia o un farmaco** (per esempio *ecocolordoppler*, *duloxetina*): se ci sono più voci scegli quella giusta e leggi **due righe di spiegazione**, nella lingua dell'app, con il tasto per aprire la pagina completa.

È un'**informazione generale**, gratuita: **non è un parere medico**. Per la tua situazione chiedi sempre al medico o al farmacista.""",
               "cos'è spiegazione wikipedia esame malattia farmaco significato parola referto"),
    "x_meteo": ("🌦️ Avvisi meteo utili",
                """Avvisi **solo quando servono**, in cima alle sezioni:
- **Salute**: **caldo forte** (bere spesso, niente uscite dalle 11 alle 17, attenzione ad anziani e bambini) e **freddo intenso**;
- **Auto**: **gelo** (ghiaccio su parabrezza e strade), **pioggia forte**, **raffiche di vento**;
- **Animali**: **caldo** (passeggiate presto o la sera, asfalto che scotta, acqua fresca, mai in auto) e **freddo**.

**Per attivarli:** **Utilità → 🌦️ Avvisi meteo** → scrivi la tua città → scegli quella giusta → **💾 Usa questa città**. Lì vedi anche le temperature dei prossimi giorni e puoi **spegnere** gli avvisi. Ognuno sceglie la sua città.

Le previsioni sono di **Open-Meteo**: gratuito, senza chiavi e senza registrazione, per uso non commerciale.""",
                "meteo avvisi caldo freddo gelo pioggia vento città previsioni open-meteo"),
    "x_voci_libere": ("✍️ Un nome a tua scelta negli elenchi con «Altro»",
                      """Negli elenchi a tendina che hanno la voce **Altro** (tipi di documento, stanze, specie degli animali, sepolture, ruoli dei medici, categorie del condominio, modi di pagamento, «Chi è per te», documenti INPS…):
1. scegli **Altro**;
2. compare **✍️ Non è nell'elenco? Scrivi il nome che vuoi**: scrivi il nome esatto (per esempio **Ecocert**);
3. salva come al solito: viene salvato **il tuo nome**, non «Altro».

Nelle schede con il bottone di conferma in fondo la casella c'è sempre, sotto l'elenco, e vale solo se hai scelto «Altro». **Il nome resta nell'elenco**: la volta dopo lo trovi già lì, prima di «Altro».""",
                      "altro nome a scelta elenco tendina scrivere nome voce personalizzata ecocert non è nell'elenco"),
    "x_lingua": ("🌐 La lingua dell'app",
                 """**Si entra nella lingua che vedi nella pagina di accesso.** Se vuoi un'altra lingua, sceglila dal menu **🌐 Lingua / Language** prima di toccare **Entra**: resta salvata.

Il telefono ricorda l'**ultima lingua usata**: la volta dopo la pagina di accesso si apre già in quella lingua. Dentro l'app la lingua si cambia dal menu **☰** in alto a sinistra.

Tutte le pagine sono nella lingua scelta: le frasi nuove si traducono da sole la prima volta che una pagina si apre (ci vuole circa un minuto), poi restano salvate per tutti. Anche **l'assistente** risponde nella lingua scelta.""",
                 "lingua language inglese spagnolo francese tedesco rumeno arabo portoghese italiano cambiare lingua accesso traduzione"),
    "x_badante": ("👵 Badante (solo amministratore)",
                  """In **Casa**, solo per l'amministratore, c'è **👵 Badante**.
- Imposta la **tariffa** (di solito 20 € per 2 ore) e i giorni in cui viene.
- **Ogni giorno conta da solo come «venuta»** (2 ore, la tariffa di sempre), a partire dal giorno della prima consegna di soldi (si cambia in «⚙️ Impostazioni»): tocca **❌ Non è venuta** solo se non è venuta; se è rimasta più o meno ore usa **«Un altro giorno o un altro importo»** (con **↩️ Torna normale** annulli).
- Con **«Ho dato dei soldi a mia madre»** segni quanto hai consegnato e quando.
- L'app calcola quanto resta e **fino a quando bastano i soldi**.
- Il tasto **🔔 Avvisi della badante** ti avvisa **3 giorni prima** e **l'ultimo giorno** (puoi cambiare i giorni).
- Ci sono anche **contatti della badante** e **note**.""",
                  "badante ore tariffa venuta non è venuta soldi madre avvisi conti automatico"),
    "x_lettore": ("🤖 Rileggi e ricataloga i documenti con l'IA (tutte le sezioni)",
                  """In fondo a **I miei documenti**, **Casa** (scheda 📚 Documenti), **Lavoro**, **Auto** e **Animali** c'è **🤖 Rileggi e ricataloga con l'IA** (in Salute c'è «🤖 Riclassifica i documenti con l'IA»).

**Come legge:** in **due tempi**: prima capisce **che documento è**, poi legge i dati con la **scheda giusta per quel tipo** (per la carta d'identità: numero, emissione, scadenza; per la bolletta: periodo, importo, scadenza, POD/PDR…). Poi **controlla** i dati: codice fiscale, numero della carta d'identità o del passaporto, targa, telaio, IBAN, date (la scadenza dopo il rilascio, mai la data di nascita al posto di un'altra). Un dato che non passa i controlli resta **🟠 da verificare** e non viene proposto.

1. Apri la tendina: vedi **«Da controllare: X di Y»**. Tocca **🔍 Leggi e cataloga**.
2. Compare il **riquadro dal vivo**: puoi usare altre app, la lettura continua; ogni documento è salvato appena letto.
3. Le **🟡 Proposte da confermare** mostrano cosa cambierebbe: lascia spuntato quello che va bene e tocca **✅ Applica**; **✖ Non applicare** lascia tutto com'è.

Anche i documenti **nuovi** (foto della carta d'identità, bollette, polizze, documenti del veterinario) si leggono con lo stesso metodo.""",
                  "rileggi ricataloga documenti ia intelligenza artificiale controlli codice fiscale numero date proposte applica casa auto animali lavoro documenti"),
    "x_smistamento": ("👥 Di chi è il documento e dove va (la mamma, la sua casa, la sua salute)",
                      """Quando l'IA legge un documento capisce anche **a chi è intestato** (destinatario della lettera, intestatario della bolletta, paziente del referto) e **in quale sezione va**.

**Prima, una volta sola:** in **🤖 Rileggi e ricataloga con l'IA** (I miei documenti o Casa) o in **🤖 Riclassifica** (Salute) tocca **👥 Di chi sono i documenti: persone e case**:
- per ogni persona scrivi **nome e cognome come sono scritti sui documenti** (es. per «Mamma»: Maria Teresa Ianniciello) e, se lo sai, il **codice fiscale**;
- per ogni casa scegli **di chi è** (es. «Casa di mamma» → Mamma). Tocca **💾 Salva**.

**Poi l'app propone da sola:**
- 🏠 **In quale casa**: la lettera dell'amministratore intestata alla mamma va nella **casa della mamma** (con la sua amministrazione);
- 👤 **Di chi è**: la carta d'identità della mamma va fra i **documenti della mamma**; il referto della mamma va nei **suoi documenti sanitari**;
- 📦 **Va spostato in**: un referto finito in Casa o in I miei documenti va in **Salute** della persona giusta; un documento d'identità finito in Casa va in **I miei documenti**.

I documenti **nuovi** si leggono **da soli** appena li carichi (in sottofondo): quando riapri la sezione trovi la proposta. Niente si sposta senza **✅ Applica**. Lo stesso vale per i tuoi documenti.""",
                      "di chi è intestatario destinatario mamma madre persona casa amministrazione salute spostare sezione giusta codice fiscale nome cognome documenti proposta"),
    "x_biglietto": ("📇 Biglietto da visita nei Numeri utili",
                    """In **Casa, Salute, Lavoro, Auto e Animali → 📞 Numeri utili → ➕ Aggiungi** c'è **📇 Fotografa un biglietto da visita**.
1. Scatta la foto (anche fronte e retro) e tocca **🔎 Leggi il biglietto**.
2. L'IA scrive da sola **nome o ditta, persona di riferimento, mestiere, telefono, cellulare, email, sito, indirizzo, orari** (la partita IVA va nelle note). **Controlla** e correggi se serve.
3. Se avete già usato le sue prestazioni spunta **✅ Abbiamo già usato le sue prestazioni** e scrivi **quando** e **cosa ha fatto** (e com'è andata). C'è anche il campo **📝 Note**.
4. Tocca **✅ Salva**.

Nella scheda trovi i tasti per contattarlo subito: **📞 Chiama, 💬 WhatsApp, ✉️ Email, ✈️ Telegram, 💬 SMS** (il +39 si aggiunge da solo).""",
                    "biglietto da visita foto numeri utili contatti telefono whatsapp email telegram sms già usato lavori fatti quando note artigiano"),
    "x_ricerca_doc": ("🔎 Cercare in tutti i documenti (anche dentro)",
                      """In fondo a **I miei documenti**, **Casa**, **Lavoro**, **Auto**, **Animali** e in **Salute → 🤖 Riclassifica** c'è **🔎 Cerca in tutti i documenti (anche dentro)**.
Scrivi una o più parole (es. «enel luglio», «revisione», «colesterolo», un numero): cerco in **tutte le sezioni** nei titoli, nei tipi, nei numeri, in chi ha emesso il documento e anche nel **riassunto** e nelle **parole chiave** che l'IA scrive quando legge il documento.
Per ogni risultato vedi la sezione, il titolo e il riassunto; con **👁️ Vedi il file** lo apri o lo scarichi.""",
                      "cercare ricerca documenti dentro riassunto parole chiave tutte le sezioni trovare file"),
    "x_correggi_ia": ("✏️ Correggere l'IA (e lei impara)",
                      """Quando l'IA propone dei cambiamenti (🟡 Proposte da confermare), sotto ogni documento c'è **✏️ Correggi prima di applicare (l'IA impara)**.
Scrivi il valore giusto (per esempio il numero esatto della carta d'identità) e tocca **✅ Applica**: si salva il tuo valore e l'app **se lo ricorda**: nelle letture dopo l'IA riceve le tue correzioni e non ripete lo stesso errore.
Se il **tipo** proposto è sbagliato spunta «non propormelo più per documenti così».""",
                      "correggere ia sbaglia impara correzioni ricorda proposte applica tipo sbagliato"),
    "x_foto_ia": ("📸 Foto migliori per la lettura",
                  """Quando fotografi un documento, l'app **raddrizza e ritaglia il foglio** e lo rende più leggibile prima di darlo all'IA.
Se la foto è **mossa**, **buia**, con un **riflesso** o **troppo piccola** te lo dice subito, con il consiglio per rifarla: tieni fermo il telefono, tocca lo schermo sul foglio per mettere a fuoco, cerca la luce, niente flash sul foglio lucido.""",
                  "foto mossa buia riflesso sfocata rifare raddrizzare ritagliare documento lettura"),
    "x_segnalati": ("📌 Documenti forse nella sezione sbagliata",
                    """Quando l'IA legge un documento capisce anche **in quale sezione dovrebbe stare**.
- Se è un documento **dell'auto** finito in Casa o in I miei documenti, propone di spostarlo nel **veicolo giusto** (quello con la targa scritta sul documento, o l'unico che hai).
- Se dovrebbe stare in **Animali** o **Lavoro**, lo segnala nel riquadro **📌 Forse nella sezione sbagliata**: aprilo da lì e caricalo nella sezione giusta, oppure tocca **Va bene qui**.""",
                    "sezione sbagliata spostare auto veicolo targa animali lavoro segnalati"),
    "x_liste_condivise": ("👥 Liste della spesa condivise con persone scelte",
                          """In **🛒 Spesa Smart → 📝 Lista della spesa** tocca **👥 Nuova lista condivisa con persone scelte**: scrivi il nome e scegli con chi condividerla.
La vedono e la modificano **solo** quelle persone e tu. Si **aggiorna da sola ogni 10 secondi**; se aggiungi un prodotto che c'è già si somma la quantità (niente doppioni); quando uno spunta «Preso» gli altri vedono **✅ chi l'ha preso**, così nessuno lo compra due volte.
Chi ha creato la lista può cambiare le persone o chiuderla in **⚙️ Lista condivisa**. Le **liste private** (🔒) restano solo tue.""",
                          "lista spesa condivisa persone scelte famiglia preso da doppioni aggiornamento privata"),
    "l_festivita": ("📅 Giorni di festa nel Controllo ore",
                    """In **Lavoro → 🧮 Controllo ore**, dopo aver caricato il foglio delle ore e la busta paga, c'è **📅 Giorni di festa**.

L'app conosce da sola le **feste nazionali** (anche **Pasquetta**, che cambia ogni anno) e la **festa del patrono** della tua città, che scegli una volta in **⛪ Festa del patrono e feste dell'anno** (per Torino: San Giovanni, 24 giugno) e poi tocchi **💾 Ricorda il patrono**.
- **Avviso rosso**: hai lavorato in un giorno di festa che nel foglio **non è segnato festivo**. Vedi i giorni, le ore e una stima di quanto potresti perdere (il festivo si paga 65%, lo straordinario normale 20%). Segna «festivo» nel foglio e ricarica, oppure chiedi all'ufficio paghe.
- **Avviso giallo**: un giorno è segnato festivo ma non è una festa né domenica: controlla (potrebbe valere una regola del tuo contratto).

Le feste vengono da **Nager.Date** (gratuito, senza chiave); se non risponde le calcola l'app.""",
                    "festivi festa giorni di festa pasquetta patrono san giovanni controllo ore busta paga festivo 65% straordinario"),
}
GA_DOVE = {"x_diario": ("utilita",), "f_ia_documenti": ("farmacia",), "f_numeri_doc": ("farmacia", "documenti"), "f_gruppo": ("farmacia",), "f_wiki": ("farmacia",),
           "x_meteo": ("farmacia", "auto", "utilita"), "x_voci_libere": ("utilita", "casa", "farmacia", "lavoro", "auto"), "x_lingua": ("utilita", "dispensa"), "l_festivita": ("lavoro",), "x_lettore": ("documenti", "casa", "lavoro", "auto", "utilita"),
           "x_smistamento": ("documenti", "casa", "farmacia", "utilita"),
           "x_ricerca_doc": ("documenti", "casa", "farmacia", "lavoro", "auto", "utilita"), "x_correggi_ia": ("documenti", "casa", "lavoro", "auto", "utilita"),
           "x_foto_ia": ("documenti", "casa", "farmacia", "auto", "utilita"), "x_segnalati": ("documenti", "casa", "utilita"), "x_liste_condivise": ("spesa_smart", "dispensa"), "x_biglietto": ("casa", "farmacia", "lavoro", "auto", "animali", "utilita")}

GA_NOVITA = [
    ("nv_diario", "📖", "Diario dei ricordi", "Utilità → 🎂 Compleanni → bottone verde ⏻ nella scheda: foto, testi, icone, musica"),
    ("nv_ia", "🤖", "Documenti letti dall'IA", "Salute → Documenti sanitari → 🤖 Riclassifica: lavora anche se usi altre app"),
    ("nv_numeri", "🔢", "N° dei documenti", "Salute → Documenti sanitari: il N° 1 è il più recente; cerca per numero"),
    ("nv_meteo", "🌦️", "Avvisi meteo", "Utilità → 🌦️ Avvisi meteo: scegli la tua città"),
    ("nv_wiki", "📖", "Cos'è?", "Salute → Documenti sanitari e Medicinali: spiegazione semplice da Wikipedia"),
    ("nv_altro", "✍️", "Nomi a scelta", "Negli elenchi con «Altro»: scrivi il nome che vuoi"),
    ("nv_smista", "👥", "Di chi è il documento", "L'IA mette i documenti della mamma nelle sue cose: casa, salute, documenti"),
    ("nv_biglietto", "📇", "Biglietto da visita", "Numeri utili → ➕ Aggiungi → 📇 Fotografa un biglietto da visita"),
    ("nv_cerca_doc", "🔎", "Cerca in tutti i documenti", "In fondo a ogni sezione: cerca anche dentro i documenti, nel riassunto dell'IA"),
    ("nv_scadenziario", "🗓️", "Scadenziario", "Pulsante lampone prima di Utilità: tutte le scadenze insieme, con avvisi"),
    ("nv_presentazione", "📘", "Presentazione dell'app", "Pulsante rosso «Clicca per informazioni» → 📘 Presentazione completa"),
    ("nv_spesa_smart", "🛒", "Spesa Smart", "Dispensa → 🛒 Spesa Smart: dove costa meno, offerte, spesa ottimizzata, scontrini"),
]
GA_NOV_K = {}


# ---------------------------------------------------------------------------------------------------------------------
# 23/11/2026 — RICHIESTA (Leonardo): «aggiorna l'assistente e le informazioni in tutte le lingue».
# Nuove: Moduli da compilare e catalogo (Lavoro, SOLO amministratore: sono personali), Appuntamenti in ogni sezione e tutti in Utilità,
# Cartelle di cura (Salute) e collegamento dei documenti con l'IA; riscritta la Domotica (termostato: boost, «fino a», orari della settimana).
# Traduzioni in guida_agg_traduzioni_2311.py (anche le schede rimaste solo in italiano: Utilità, CQC, patente, Portale, Controllo ore,
# Stipendio previsto, Peso e litri, e le novità 7–14).
# ---------------------------------------------------------------------------------------------------------------------
GA_SOLO_ADMIN = {"l_moduli", "l_moduli_catalogo", "l_controllo", "l_stipendio", "l_festivita"}   # personali: le vede (e l'assistente le usa) solo l'amministratore

GA_SCHEDE.update({
    "l_moduli": ("📝 Moduli da compilare (solo per te)",
                 """In **💼 Lavoro → 📝 Moduli da compilare** compili dal telefono i moduli di carta del lavoro: l'app **scrive sul foglio originale**, come con la penna. **È una cosa personale**: la vede solo l'amministratore.
1. Tocca il modulo: **🏖️ Richiesta di permesso – ferie** oppure **👕 Scheda ordini abbigliamento**.
2. Rispondi alle domande: nome, cantiere e data di oggi sono già scritti.
   - **Permesso**: scegli cosa chiedi (ferie, permesso retribuito… o **Altro**) e **quali giorni**: «A decorrere dal… fino al…». Per **giorni non di fila** tocca **➕ Aggiungi un altro giorno**: sotto vedi cosa verrà scritto e il **totale dei giorni**.
   - **Abbigliamento**: appalto, mese, luogo di consegna; poi aggiungi **una riga alla volta** (articolo, quantità, taglia). Il nome è il tuo e **le taglie vengono ricordate**.
3. Apri **👁️ Guarda l'anteprima**, poi tocca **✍️ Firma e salva** (la firma si mette **solo** con questo tasto) oppure **💾 Salva senza firma**.
4. Nel riquadro verde tocca **📤 Manda il PDF**: si apre «Condividi» con il PDF già allegato, scegli **WhatsApp** e poi il tuo responsabile. Poi tocca **✅ Fatto: l'ho mandato**. Ci sono anche **⬇️ PDF**, **⬇️ Foto (JPG)** e **📨 Altri modi** (email, Telegram…).

**✍️ La tua firma**: la carichi una volta (foto della firma su un foglio bianco): l'app toglie il bianco e tiene solo l'inchiostro. **⚙️ A chi li mandi**: nome e cellulare del responsabile e il tuo cantiere.
I giorni di permesso entrano da soli negli **📅 Appuntamenti** di Lavoro (e nel riepilogo di Utilità).""",
                 "moduli modulo compilare permesso ferie richiesta giorni non consecutivi firma responsabile whatsapp abbigliamento vestiario taglia pdf"),
    "l_moduli_catalogo": ("🗂️ Il catalogo dei moduli inviati",
                          """Ogni modulo compilato resta nel **🗂️ Catalogo dei moduli** (in fondo a **📝 Moduli da compilare**), diviso **per mese**.
- **Filtri**: **Tipo** (permessi, abbigliamento), **Stato** (📤 Inviati, ⏳ Da inviare), **Anno** e **🔎 Cerca** (per esempio «ferie», «polo», il nome del responsabile).
- Quando segni l'invio, l'app salva la **copia esatta del PDF inviato**, con data e ora: la trovi in **📎 Copie inviate** e resta così anche se poi modifichi il modulo o cambi la firma.
- Se modifichi un modulo già mandato compare **«✏️ modificato dopo l'invio: da rimandare»**.
- Su ogni modulo: **👁️ Apri**, **✏️ Modifica**, **📄 Duplica** (comodo per l'ordine del mese dopo) e **🗑️ Elimina**.
- **📊 Giorni chiesti nell'anno**: quanti giorni di ferie, permessi… (un giorno conta una volta sola).
- **🗜️ ZIP**: scarichi in un solo file tutte le copie inviate dell'elenco che stai guardando.""",
                          "catalogo moduli inviati copia esatta pdf stato da inviare rimandare filtro anno cerca giorni chiesti zip duplica"),
    "x_appuntamenti": ("📅 Appuntamenti: in ogni sezione e tutti insieme in Utilità",
                       """**In ogni sezione** il bottone **📅 Appuntamenti** mostra quelli di quella sezione: Salute in Salute, Auto in Auto, Lavoro in Lavoro… Sotto, in **🔗 Dalle altre schede**, compaiono anche quelli scritti altrove per la stessa persona (in Salute: visite, controlli, cartelle di cura come il dentista). Il numero sul bottone li conta tutti.

**In 🧰 Utilità → 📅 Appuntamenti** ci sono **tutti** gli appuntamenti dell'app: per ognuno vedi da quale sezione viene, di chi è e la priorità.
- **Tipologia**: Tutte, Salute, Auto, Lavoro… (con quanti sono).
- **Ordina per**: **📅 Data** (Oggi, Domani, Nei prossimi 7 giorni, Entro un mese, Più avanti) oppure **⭐ Priorità** (prima le alte).
- **➕ Aggiungi un appuntamento**: scegli prima **«Di che tipo è?»** (e, per Salute, **per chi**): l'appuntamento va **nella sua sezione**. In Utilità resta solo quello di tipo «Altro».
- **Priorità**: **⚙️ Automatica** (alta se è un pagamento o è scaduto, media entro 30 giorni, bassa se è più lontano), oppure 🔴 Alta, 🟡 Media, 🟢 Bassa. Per quelli delle altre schede c'è **⭐ Cambia priorità**. Vale anche nello Scadenziario.
- Da lì segni **✅ Fatto**, **✏️ Modifichi** o elimini; **↗️ Apri la scheda** porta dove l'appuntamento è scritto. In fondo, **🗂️ Passati o fatti**.""",
                       "appuntamenti tutti riepilogo utilità sezione tipologia priorità alta media bassa automatica data ordina dalle altre schede dentista visite"),
    "f_percorsi": ("🗂️ Cartelle di cura (dentista, cicli di cure)",
                   """Per un **lavoro lungo dal dentista**, un ciclo di fisioterapia o un intervento: tutto **in una cartella sola**.
1. In **Salute** scegli la persona (per esempio la mamma). In alto trovi **🗂️ Cartelle di cura** → **➕ Nuova cartella**.
2. Carica il **cartellino dell'appuntamento** e il **preventivo** (foto o PDF) e tocca **🔎 Leggi i documenti e compila**: l'app legge studio, telefoni, medico, date, orari e righe del preventivo. Controlli e tocchi **💾 Crea la cartella**.

Dentro la cartella:
- **Appuntamenti**: data e ora, cosa si fa; dopo la seduta segni **fatto**, l'**esito** e il **prossimo appuntamento**;
- **Pagamenti**: bonifici e contanti, con la **ricevuta** (l'app legge importo e data), il **piano delle rate** e **quanto resta da pagare**;
- **Documenti**, **Preventivo** e **Diario**.
In alto ci sono **📞 Chiama**, **📍 Mappa** e **✉️ Email** dello studio e il file **.ics** per il calendario.
Appuntamenti e rate entrano nello **🗓️ Scadenziario** con gli avvisi (WhatsApp, email, Telegram) e negli **📅 Appuntamenti** della persona. Lo studio entra **da solo nei 📞 Numeri utili** della persona (una volta sola: se lo elimini non torna). Le cartelle concluse stanno sotto, in **Concluse**.""",
                   "cartella di cura percorso dentista preventivo rate bonifico ricevuta pagamenti appuntamenti studio cure fisioterapia intervento mamma"),
    "f_percorsi_ia": ("🤖 Collegare i documenti a una cartella di cura (con l'IA)",
                      """Dentro una cartella di cura, **🔗 Da collegare (N)** mostra i documenti **già nell'app** (documenti sanitari, visite, prescrizioni della **stessa persona**) che sembrano di quella cartella, con il **motivo** (stesso studio, stessa data, stesso telefono…).
Tocca **🤖 Controlla che sia di questa cartella**: l'IA confronta con cura **partita IVA, codice fiscale, telefono, nome dello studio, paziente e importi** e risponde **✅ collima**, **❌ non collima** o **⚠️ incerto**, spiegando perché.
Anche i documenti caricati **dopo** vengono proposti. **Niente si collega senza la tua conferma**; quelli che scarti non vengono riproposti.""",
                      "collegare documenti cartella di cura ia controlla collima partita iva codice fiscale paziente importo da collegare"),
    "x_domotica": ("🎛️ Domotica: comandare la casa (anche il termostato)",
                   """In **🏠 Casa → 🎛️ Domotica** trovi gli apparecchi di casa divisi **per stanza** o **per tipo**.
- **☁️ si comanda da qui**: apparecchi collegati al cloud del produttore (Tuya / Smart Life: climatizzatori, lampadine, prese…; BTicino: termostato). Tocca **🎮 Apri → Controlli**: compaiono SOLO i comandi che l'apparecchio ha davvero; ogni comando risponde ✅ o con l'errore.
- **📱 con la sua app** (Google Home, Alexa, SmartThings…): il pulsante **▶ Apri** apre l'app giusta.
- **🔎 Cerca adesso** chiede ai cloud collegati gli apparecchi nuovi: scegli la stanza e confermi (niente doppioni).
- **🎬 Scenari**: «Esco di casa», «Buonanotte»… più comandi con un tocco.
- **🔗 Collegamenti**: lo stato dei collegamenti Tuya e BTicino. Le chiavi stanno solo nei Secrets di Streamlit.

**🌡️ Il termostato (BTicino)**: **🎯 Temperatura a mano** (anche **«fino a»** un orario), **🚀 Boost** di 30, 60 o 90 minuti (e **⏹ Ferma boost**), **🅰️ Programma automatico**, **❄️ Antigelo**, **⏻ Spegni**.
**📅 Orari della settimana**: per ogni giorno scrivi **le fasce** (dalle… alle…) con la temperatura; ci sono **modelli pronti**, **«copia su»** altri giorni, e scegli cosa fare **fuori dalle fasce** (programma del termostato o temperatura ridotta). Vedi la **stima del risparmio**. Un **orologio automatico** controlla ogni mezz'ora, **anche ad app chiusa**, e manda al termostato la fascia giusta: quando è attivo compare **«🤖 Orologio automatico attivo»**.
Per sicurezza serrature e allarmi chiedono una conferma prima di ogni comando.""",
                   "domotica casa apparecchi stanza comandi luce lampadina climatizzatore termostato boost orari fasce settimana risparmio antigelo tuya smart life bticino google home scenari"),
})
GA_SCHEDE["x_orologio"] = ("⏰ Orologio automatico e 📅 giorni speciali del riscaldamento",
    """Gli **📅 Orari della settimana** del termostato funzionano anche **ad app chiusa** grazie all'**⏰ Orologio automatico**: una sveglia gratuita (sul sito cron-job.org) che ogni mezz'ora, dalle 5:00 alle 23:30, manda al termostato la fascia giusta.
**Dove:** Casa → 🎛️ Domotica → termostato → **📅 Orari della settimana**, in fondo: riquadro **⏰ Orologio automatico** (nel titolo vedi se è acceso o in pausa).
- **▶️ Accendi**: resta acceso finché non lo fermi. **⏸️ Metti in pausa**: si ferma. **📅 Accendi solo per oggi**: si spegne da solo stanotte. **🔧 Orario consigliato**: ogni mezz'ora dalle 5 alle 23:30.
- **Perché si mette in pausa:** ogni sveglia consuma 1 minuto dei circa **2.000 minuti gratuiti al mese** di GitHub (gli stessi di promemoria e posta). Acceso tutto il mese sono circa 1.150 minuti: va bene, ma se non usi gli orari conviene tenerlo in pausa. Se si superano i 2.000 minuti non paghi niente, ma le automazioni si fermano fino al mese dopo.
- **Funziona anche in pausa:** 🎯 temperatura a mano (anche «fino a» un orario), 🚀 Boost, ⏻ Spegni, ❄️ Antigelo, il programma del termostato e l'app BTicino; e gli orari vengono applicati quando apri VitaMemo.

**📅 Solo per un giorno** (sopra «Fuori dalle fasce»): scegli una data, tocca **➕ Aggiungi** e scrivi le fasce di quel giorno (ferie, sei a casa, ospiti…). Valgono **solo quel giorno**, al posto di quelle della settimana, **anche se gli orari della settimana sono spenti**; senza fasce, quel giorno niente riscaldamento in più. Poi **💾 Salva gli orari** e, quel giorno, **📅 Accendi solo per oggi** nell'orologio. Il giorno dopo si cancellano da sole.
Per comandare l'orologio da qui serve una volta sola la chiave gratuita di cron-job.org nei Secrets (`[cronjob] api_key`); senza, il riquadro spiega come farlo a mano.""",
    "orologio automatico cron job cron-job.org pausa accendi solo per oggi minuti github actions riscaldamento orari giorno speciale eccezione ferie fasce termostato")
GA_NOVITA.append(("nv_orologio", "⏰", "Orologio del riscaldamento dall'app", "Termostato → 📅 Orari → ⏰ Orologio automatico: accendi, pausa, solo per oggi; e 📅 Solo per un giorno"))
GA_SCHEDE["x_parcheggio"] = ("🅿️ Dove ho parcheggiato",
    """In **Home**, accanto a **🛒 Spesa Smart**, c'è **🅿️ Parcheggio**.
1. Appena parcheggi toccalo e poi tocca **📍 Salva qui (GPS)**: il telefono trova dove sei (la prima volta tocca **Consenti**) e salva da solo, con l'indirizzo. Oppure **scrivi tu** il posto.
2. Se vuoi, in **➕ Foto, note, veicolo, scadenza della sosta**: una **foto** (il piano, la colonna), le **note** (es. «Piano -1, colonna B14»), **quale auto** e la **scadenza della sosta** (strisce blu): poi **📲 Avviso nel calendario** suona 10 minuti prima.
3. Quando torni, il bottone diventa **🅿️ Dov'è l'auto**: tocca **🧭 Portami all'auto** (Google Maps a piedi), **🗺️ Mappa** o **📤 Manda** la posizione su WhatsApp.
4. Ripresa l'auto, tocca **✅ Ho ripreso l'auto**: il parcheggio va nei **🕘 Parcheggi precedenti**. La posizione compare anche in **Auto**, nella scheda del veicolo.""",
    "parcheggio parcheggiato dove auto macchina gps posizione sosta strisce blu disco orario portami mappa piano colonna")
GA_NOVITA.append(("nv_parcheggio", "🅿️", "Dove ho parcheggiato", "Home → 🅿️ Parcheggio, accanto a Spesa Smart: un tocco e il GPS salva il posto"))
GA_DOVE.update({"x_orologio": ("casa",), "x_parcheggio": ("dispensa", "auto", "utilita"), "l_moduli": ("lavoro",), "l_moduli_catalogo": ("lavoro",),
                "x_appuntamenti": ("farmacia", "documenti", "casa", "lavoro", "auto", "animali", "utilita"),
                "f_percorsi": ("farmacia",), "f_percorsi_ia": ("farmacia",)})
GA_SCHEDE["d_prezzi"] = ("💶 Prezzi in Dispensa e 🛒 «quando finisce»",
    """**Dove:** Dispensa → **🔍 Dettagli prodotto** → scegli il prodotto: sotto la scheda ci sono tre cose nuove.
- **🛒 Metti nella lista della spesa**: scegli **quanti** e tocca. Se è già in lista aggiorna la quantità.
- **💶 Prezzo, peso e prezzo al kg**: scrivi **prezzo pagato**, **confezioni**, **peso o contenuto** (g, kg, ml, l) e **negozio**: l'app calcola da sola **€/kg** o **€/litro**. Per frutta, verdura e carne attiva **⚖️ Venduto a peso** (€/kg × grammi). Se era in offerta spunta **🏷️ Era in offerta**. Il prezzo va in **🛒 Spesa Smart** (niente doppioni): sulla scheda vedi l'ultimo prezzo, **🏷️ In offerta da…** o **💡 Costa meno da…** e gli ultimi prezzi.
- **⚙️ Quando finisce**: ❓ **Chiedimi** (normale), 🛒 **Mettilo sempre in lista**, 🏷️ **Solo se è in offerta**, 🚫 **Mai**. E la **📦 scorta minima**: quando ne restano così pochi, è come se fosse finito.
**Un prodotto finito NON va più in lista da solo**: compare **«❓ È finito: cosa faccio?»** con 4 scelte: **🛒 Mettilo nella lista**, **⏰ Più avanti** (1 settimana, 2 settimane, 1 mese o una data; quel giorno te lo richiedo o lo metto in lista da solo), **💭 Solo se conviene** (ti avviso 🔔 quando è in offerta), **🚫 Non lo ricompro**. Se non scegli, resta in **Spesa → ❓ Finiti, da decidere**. Se lo rimetti in lista 3 volte di fila, l'app ti propone **«mettilo sempre in lista»**.
**Nella scheda 🛒 Spesa**, sopra la lista: **❓ Finiti, da decidere** · **🏷️ Da ricomprare se conviene** (con 🔥 quando sono in offerta) · **⏰ Più avanti**. In **📦 Metti in dispensa i prodotti presi** puoi scrivere anche **quanto hai pagato e dove**: i prezzi vanno in Spesa Smart.""",
    "prezzo prezzi peso kg chilo litro euro al kg costo pagato negozio offerta conviene dove costa meno lista della spesa finito finiti ricomprare riacquistare più avanti scorta minima regola quando finisce non lo ricompro")
GA_NOVITA.append(("nv_dprezzi", "💶", "Prezzi in Dispensa e «quando finisce»", "Dispensa → Dettagli prodotto: 💶 prezzo e €/kg, 🛒 in lista; se finisce l'app ti chiede cosa fare"))
GA_SCHEDE["x_non_indietro"] = ("🧭 L'app non torna più indietro da sola",
    """**Cosa è cambiato (27/11/2026):**
- Dopo un'azione (Salva, Metti in lista, Applica…) resti **nella stessa scheda e nella stessa voce**: anche se sopra compare o sparisce un messaggio, o cambia un numero tra parentesi (per esempio «Messaggi (3)» → «(4)»).
- Le **pillole** (per esempio le categorie dell'Archivio) ricordano la scelta anche quando apri un documento o un'altra voce e poi torni.
- Se il telefono **«stacca» l'app** (fotocamera, scelta di un file, WhatsApp, schermo spento) e la pagina riparte entro 20 minuti, torni **nella sezione, nella voce e nella scheda** in cui eri, non una pagina indietro.
**Negozio nuovo più semplice:** in Spesa Smart, in Modifica prezzo e in Dispensa, sotto i negozi che hai c'è sempre la riga **«✍️ …oppure scrivi un negozio nuovo»**: scrivi il nome e basta. Città e indirizzo solo se servono, in **«➕ Città e indirizzo»**. Il negozio nuovo diventa il primo dell'elenco. Quando metti in dispensa i prodotti presi, il negozio si sceglie **una volta sola** per tutta la spesa.""",
    "indietro torna indietro pagina precedente scheda prima scheda si chiude perdo il punto ricomincia riparte negozio nuovo aggiungere negozio scrivere negozio città indirizzo")
GA_SCHEDE["x_velocita_doc"] = ("⚡ Documenti letti più in fretta",
    """**Cosa è cambiato (27/11/2026), con la stessa qualità di prima:**
- **Caricare un documento in Salute**: la lettura del testo e l'intelligenza artificiale lavorano **insieme** (prima una dopo l'altra).
- **Documenti scritti a mano o difficili**: le letture dei vari servizi si chiedono **tutte insieme**; poi il confronto finale, come prima.
- **Negli altri documenti** (Casa, Auto, Animali, ricatalogazione): se l'app sa già che tipo di documento è, la scheda su misura parte subito, insieme al riconoscimento del tipo; se il tipo era diverso, la rifà con quello giusto.
- **Scansioni e PDF senza testo**: le pagine si leggono insieme. Lo stesso file non si rilegge due volte (la seconda volta è immediato).
- **🔄 Rileggi i documenti già archiviati** (Salute): i file si scaricano e si leggono **4 alla volta**: molto più veloce, stesse proposte.
- **Riclassificazione in sottofondo**: mentre l'IA legge un documento, il file del successivo si scarica già; e i salvataggi avvengono in coda, senza far aspettare la lettura.""",
    "veloce lento lentezza velocità rileggi documenti archiviati riclassifica ricatalogare lettura documenti caricare documento OCR scansione intelligenza artificiale aspettare")
GA_DOVE.update({"x_non_indietro": ("utilita", "dispensa", "spesa_smart"), "x_velocita_doc": ("farmacia", "documenti", "casa", "utilita")})
GA_NOVITA.append(("nv_nonindietro", "🧭", "Non si torna più indietro da soli", "Dopo un'azione resti nella stessa scheda e voce; se il telefono stacca l'app, torni dove eri. Negozio nuovo: scrivi il nome e basta"))
GA_NOVITA.append(("nv_velocita", "⚡", "Documenti letti più in fretta", "Salute, Rileggi, riclassificazione e caricamenti: letture insieme e file preparati in anticipo, stessa qualità"))
GA_DOVE.update({"d_prezzi": ("dispensa",)})
GA_NOVITA += [
    ("nv_appuntamenti", "📅", "Tutti gli appuntamenti", "Utilità → 📅 Appuntamenti: per tipologia, per data o per priorità"),
    ("nv_percorsi", "🗂️", "Cartelle di cura", "Salute → 🗂️ Cartelle di cura: appuntamenti, pagamenti e documenti insieme"),
    ("nv_termostato", "🌡️", "Termostato: boost e orari", "Casa → 🎛️ Domotica → termostato: 🚀 Boost e 📅 Orari della settimana"),
]


def _ga_admin():
    try:
        return bool((st.session_state.get("sess") or {}).get("admin"))
    except Exception:
        return False


if "voci_guida" in globals() and "_ga_voci_guida_prima" not in globals():
    _ga_voci_guida_prima = voci_guida

    def voci_guida(sezione):                                                 # noqa: F811 — le schede personali solo per l'amministratore
        voci = _ga_voci_guida_prima(sezione)
        return voci if _ga_admin() else [v for v in voci if v.get("id") not in GA_SOLO_ADMIN]


def _ga_applica():
    # schede nuove o riscritte
    for cid, (titolo, corpo, chiavi) in GA_SCHEDE.items():
        dove = GA_DOVE.get(cid)
        if dove is None:                                                     # scheda già esistente: la riscrivo dove c'è
            for sez, ids in _ID_GUIDA.items():
                if cid in ids:
                    i = ids.index(cid)
                    lista = _GUIDE.get(sez) or []
                    if i < len(lista):
                        lista[i] = (titolo, corpo.strip(), chiavi)
            continue
        for sez in dove:
            ids = _ID_GUIDA.setdefault(sez, [])
            lista = _GUIDE.setdefault(sez, [])
            if cid in ids:
                i = ids.index(cid)
                if i < len(lista):
                    lista[i] = (titolo, corpo.strip(), chiavi)
            else:
                ids.append(cid)
                lista.append((titolo, corpo.strip(), chiavi))
    # versione delle istruzioni
    try:
        for info in (GUIDA_VERSIONI or {}).values():
            info["versione"], info["data"] = GA_VERSIONE, GA_DATA
        for sez, ids in _ID_GUIDA.items():
            for i, cid in enumerate(ids):
                if cid.startswith("ver_") and i < len(_GUIDE.get(sez) or []):
                    t_, c_, k_ = _GUIDE[sez][i]
                    _GUIDE[sez][i] = (t_, c_.replace("versione 5.1", "versione " + GA_VERSIONE).replace("13/11/2026", GA_DATA_IT), k_)
        for lg, d in GUIDA_TR.items():
            for cid, v in list(d.items()):
                if cid.startswith("ver_") and isinstance(v, tuple) and len(v) >= 2:
                    d[cid] = (v[0], v[1].replace("5.1", GA_VERSIONE).replace("13/11/2026", GA_DATA_IT)) + tuple(v[2:])
    except Exception:
        pass
    # le novità dell'assistente
    gia = {n[2] for n in _NOVITA}
    for cod, ic, tit, dove in GA_NOVITA:
        if tit not in gia:
            _NOVITA.append((GA_DATA, ic, tit, dove))
        GA_NOV_K[cod] = next(k for k, n in enumerate(_NOVITA, start=1) if n[2] == tit)


def ga_traduci(lg, schede, novita):
    """Usata da guida_agg_xx.py: schede {cid: (titolo, testo, parole)} e novità {codice: (titolo, dove)}."""
    d = GUIDA_TR.setdefault(lg, {})
    d.update(schede)
    if "x_numeri_utili" in schede:                                           # la stessa scheda vale in tutte le sezioni
        for sez in ("casa", "salute", "documenti", "archivio", "lavoro", "auto", "animali", "utilita"):
            d["x_numeri_utili_" + sez] = schede["x_numeri_utili"]
    for cod, (t_, dove) in novita.items():
        if cod in GA_NOV_K:
            d[f"nov{GA_NOV_K[cod]}"] = (t_, dove)


try:
    _ga_applica()
except Exception:
    pass
