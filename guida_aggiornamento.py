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

GA_VERSIONE, GA_DATA, GA_DATA_IT = "5.2", "2026-11-20", "20/11/2026"

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
    "l_festivita": ("📅 Giorni di festa nel Controllo ore",
                    """In **Lavoro → 🧮 Controllo ore**, dopo aver caricato il foglio delle ore e la busta paga, c'è **📅 Giorni di festa**.

L'app conosce da sola le **feste nazionali** (anche **Pasquetta**, che cambia ogni anno) e la **festa del patrono** della tua città, che scegli una volta in **⛪ Festa del patrono e feste dell'anno** (per Torino: San Giovanni, 24 giugno) e poi tocchi **💾 Ricorda il patrono**.
- **Avviso rosso**: hai lavorato in un giorno di festa che nel foglio **non è segnato festivo**. Vedi i giorni, le ore e una stima di quanto potresti perdere (il festivo si paga 65%, lo straordinario normale 20%). Segna «festivo» nel foglio e ricarica, oppure chiedi all'ufficio paghe.
- **Avviso giallo**: un giorno è segnato festivo ma non è una festa né domenica: controlla (potrebbe valere una regola del tuo contratto).

Le feste vengono da **Nager.Date** (gratuito, senza chiave); se non risponde le calcola l'app.""",
                    "festivi festa giorni di festa pasquetta patrono san giovanni controllo ore busta paga festivo 65% straordinario"),
}
GA_DOVE = {"x_diario": ("utilita",), "f_ia_documenti": ("farmacia",), "f_numeri_doc": ("farmacia", "documenti"), "f_gruppo": ("farmacia",), "f_wiki": ("farmacia",),
           "x_meteo": ("farmacia", "auto", "utilita"), "x_voci_libere": ("utilita", "casa", "farmacia", "lavoro", "auto"), "x_lingua": ("utilita", "dispensa"), "l_festivita": ("lavoro",), "x_lettore": ("documenti", "casa", "lavoro", "auto", "utilita")}

GA_NOVITA = [
    ("nv_diario", "📖", "Diario dei ricordi", "Utilità → 🎂 Compleanni → bottone verde ⏻ nella scheda: foto, testi, icone, musica"),
    ("nv_ia", "🤖", "Documenti letti dall'IA", "Salute → Documenti sanitari → 🤖 Riclassifica: lavora anche se usi altre app"),
    ("nv_numeri", "🔢", "N° dei documenti", "Salute → Documenti sanitari: il N° 1 è il più recente; cerca per numero"),
    ("nv_meteo", "🌦️", "Avvisi meteo", "Utilità → 🌦️ Avvisi meteo: scegli la tua città"),
    ("nv_wiki", "📖", "Cos'è?", "Salute → Documenti sanitari e Medicinali: spiegazione semplice da Wikipedia"),
    ("nv_altro", "✍️", "Nomi a scelta", "Negli elenchi con «Altro»: scrivi il nome che vuoi"),
]
GA_NOV_K = {}


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
