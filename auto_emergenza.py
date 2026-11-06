# -*- coding: utf-8 -*-
"""AUTO · EMERGENZA — contenuti che funzionano SENZA internet e senza intelligenza artificiale esterna.

• Spie del cruscotto: catalogo per colore e urgenza (cercabile), con il pericolo scritto per primo quando serve.
• Procedure per auto elettriche e ibride: batteria 12V scarica, cavo di ricarica bloccato, modalità tartaruga, fumo/fuoco/allagamento. Regola fissa: MAI toccare o tagliare i cavi arancioni (alta tensione).
• Altre emergenze: batteria 12V scarica su auto termica, cosa dire al soccorso.
• Sinistro: guida passo passo e testo pronto per l'assicuratore (si compila in auto.py).
Sono indicazioni GENERALI: per il tuo modello vale sempre il manuale d'uso. In caso di pericolo: 112."""
import html as _h_ae

import streamlit as st

# colore: rosso (fermati), giallo (officina a breve), verde/blu (informazione)
_AE_SPIE = [
    # ---------------- ROSSE ----------------
    {"nome": "Pressione olio motore", "colore": "rosso", "icona": "🛢️", "tipo": "termico", "urgenza": "EMERGENZA: arresto immediato",
     "significato": "La pressione dell'olio è troppo bassa o il livello è quasi a zero: il motore non è più lubrificato e si può rovinare in pochi minuti.",
     "azioni": ["Accosta subito in un punto sicuro e SPEGNI il motore.", "Aspetta qualche minuto, poi controlla il livello dell'olio con l'astina.", "Se manca olio, rabbocca con quello indicato dal manuale; se la spia resta accesa NON ripartire: chiama il carro attrezzi."],
     "cause": ["Livello olio troppo basso", "Pompa dell'olio o sensore guasti", "Perdita d'olio", "Filtro intasato"]},
    {"nome": "Temperatura del liquido di raffreddamento (surriscaldamento)", "colore": "rosso", "icona": "🌡️", "tipo": "termico", "urgenza": "EMERGENZA: arresto immediato",
     "significato": "Il motore è troppo caldo: continuare può bruciare la guarnizione della testata o fondere il motore.",
     "azioni": ["Accosta, spegni il motore e lascia il cofano chiuso finché non si è raffreddato (almeno 30 minuti).", "NON aprire il tappo del radiatore a motore caldo: il liquido è in pressione e può ustionare.", "A motore freddo controlla il livello del liquido; se è basso rabbocca. Se si ripresenta, vai in officina col carro attrezzi."],
     "cause": ["Liquido di raffreddamento basso (perdita)", "Termostato o ventola guasti", "Pompa dell'acqua", "Radiatore intasato"]},
    {"nome": "Impianto frenante / freno a mano / liquido freni", "colore": "rosso", "icona": "🛑", "tipo": "tutti", "urgenza": "EMERGENZA: i freni potrebbero non funzionare",
     "significato": "Può significare freno a mano inserito, livello del liquido freni basso o un guasto all'impianto frenante.",
     "azioni": ["Controlla prima che il freno a mano sia completamente abbassato.", "Se la spia resta accesa o il pedale è «molle» o va a fondo: accosta con cautela, spegni e NON ripartire.", "Chiama il soccorso stradale: guidare con i freni difettosi è pericolosissimo."],
     "cause": ["Freno a mano inserito", "Liquido freni sotto il minimo (pastiglie consumate o perdita)", "Guasto al servofreno o al circuito"]},
    {"nome": "Batteria / carica (alternatore)", "colore": "rosso", "icona": "🔋", "tipo": "tutti", "urgenza": "Urgente: l'auto potrebbe fermarsi tra poco",
     "significato": "La batteria a 12 V non si sta ricaricando: l'auto funziona finché la batteria si scarica (da pochi minuti a mezz'ora).",
     "azioni": ["Spegni tutto ciò che consuma (clima, radio, sedili riscaldati, luci non necessarie).", "Raggiungi in sicurezza un'officina o un posto sicuro senza spegnere il motore.", "Se si spegne tutto, chiama il soccorso."],
     "cause": ["Alternatore o cinghia dei servizi guasti", "Batteria 12V esaurita o con morsetti allentati", "Problema al DC-DC (su ibride/elettriche)"]},
    {"nome": "Airbag / sistema di ritenuta", "colore": "rosso", "icona": "🎈", "tipo": "tutti", "urgenza": "Sicurezza: da controllare subito",
     "significato": "Il sistema airbag/pretensionatori ha un'anomalia: in caso di urto potrebbe non attivarsi.",
     "azioni": ["Puoi arrivare in officina, ma fai controllare l'impianto prima possibile.", "Non intervenire da solo sui cablaggi giallo/arancio dell'airbag."],
     "cause": ["Sensore o connettore di un airbag", "Sedile con connettore scollegato", "Centralina airbag"]},
    {"nome": "Cintura non allacciata", "colore": "rosso", "icona": "🪢", "tipo": "tutti", "urgenza": "Sicurezza: allaccia la cintura",
     "significato": "Una cintura non è allacciata (o c'è un oggetto pesante sul sedile).", "azioni": ["Allaccia le cinture prima di partire.", "Se la spia resta accesa con le cinture allacciate: fai controllare il sensore."], "cause": ["Cintura non agganciata", "Sensore di presenza o fibbia"]},
    {"nome": "Servosterzo / sterzo", "colore": "rosso", "icona": "🎛️", "tipo": "tutti", "urgenza": "EMERGENZA: lo sterzo diventerà molto pesante",
     "significato": "L'assistenza allo sterzo non funziona: lo sterzo diventa duro, soprattutto a bassa velocità.",
     "azioni": ["Tieni saldo il volante, riduci la velocità e accosta appena puoi.", "Spegni e riaccendi: se non si spegne la spia, chiama il soccorso."], "cause": ["Guasto al servosterzo elettrico", "Livello olio idraulico", "Batteria debole"]},
    {"nome": "Porta, cofano o portellone aperti", "colore": "rosso", "icona": "🚪", "tipo": "tutti", "urgenza": "Attenzione: chiudi prima di partire",
     "significato": "Una porta, il cofano o il bagagliaio non è ben chiuso.", "azioni": ["Fermati in sicurezza e chiudi bene.", "Se la spia resta accesa a tutto chiuso: sensore/serratura da controllare."], "cause": ["Chiusura incompleta", "Sensore della serratura"]},
    {"nome": "Sistema ad alta tensione (HV) · guasto grave", "colore": "rosso", "icona": "⚡", "tipo": "hv", "urgenza": "EMERGENZA: arresto immediato",
     "significato": "Anomalia grave al sistema di trazione ad alta tensione (batteria di trazione, inverter, isolamento). Può esserci rischio elettrico.",
     "azioni": ["Accosta appena puoi, inserisci il freno di stazionamento e SPEGNI il veicolo.", "Non toccare i cavi arancioni e non aprire coperchi dell'alta tensione.", "Se senti odore acre, vedi fumo o senti rumori anomali: scendi, allontanati di 15-20 metri e chiama il 112.", "Chiama il soccorso stradale e dì che è un veicolo elettrico/ibrido: va caricato su carro attrezzi (a ruote sollevate)."],
     "cause": ["Guasto di isolamento", "Errore del modulo batteria", "Contattori HV", "Urto o sollecitazione al pacco batteria"]},
    {"nome": "Temperatura batteria di trazione troppo alta", "colore": "rosso", "icona": "🌡️", "tipo": "hv", "urgenza": "EMERGENZA: fermarsi e lasciar raffreddare",
     "significato": "La batteria di trazione è troppo calda: l'auto limita la potenza e può spegnersi per sicurezza.",
     "azioni": ["Fermati all'ombra, spegni il veicolo e NON ricaricare finché non si raffredda.", "Se compare fumo o odore anomalo: allontanati di 15-20 metri e chiama il 112."], "cause": ["Ricariche rapide ripetute col caldo", "Guasto al raffreddamento", "Uso intenso in salita"]},
    # ---------------- GIALLE ----------------
    {"nome": "Controllo motore (Check engine / MIL)", "colore": "giallo", "icona": "⚙️", "tipo": "termico", "urgenza": "Avviso: officina a breve",
     "significato": "La centralina ha rilevato un'anomalia nel motore o nelle emissioni. Se la spia LAMPEGGIA: stai danneggiando il catalizzatore, riduci subito il carico e vai in officina.",
     "azioni": ["Se è fissa: puoi proseguire con prudenza e fissare un controllo entro pochi giorni.", "Se lampeggia o il motore «strappa»: riduci la velocità, evita accelerazioni e vai subito in officina.", "Controlla che il tappo del serbatoio sia ben chiuso."],
     "cause": ["Sonda lambda o sensore difettoso", "Candele/bobine", "Catalizzatore", "Perdite di aria o iniezione"]},
    {"nome": "Filtro antiparticolato (DPF/FAP)", "colore": "giallo", "icona": "🏭", "tipo": "termico", "urgenza": "Avviso: rigenerazione o officina",
     "significato": "Il filtro dei fumi (diesel) si sta intasando: serve una rigenerazione.",
     "azioni": ["Percorri 15-20 minuti a velocità sostenuta (extraurbana/autostrada) senza spegnere il motore.", "Se la spia resta accesa o si aggiunge «controllo motore»: officina."], "cause": ["Troppi percorsi brevi", "Sensore di pressione", "Additivo esaurito"]},
    {"nome": "Pressione pneumatici (TPMS)", "colore": "giallo", "icona": "🛞", "tipo": "tutti", "urgenza": "Avviso: controlla le gomme",
     "significato": "Uno o più pneumatici hanno la pressione troppo bassa (o c'è un guasto del sensore).",
     "azioni": ["Fermati in un punto sicuro e guarda le gomme.", "Gonfia alla pressione indicata sull'etichetta nel montante della porta o nel manuale.", "Se sgonfia di nuovo c'è una foratura: gomma di scorta, kit riparazione o carro attrezzi. Dopo, azzera il sistema come da manuale."],
     "cause": ["Pressione bassa per freddo", "Foratura", "Sensore"]},
    {"nome": "ABS", "colore": "giallo", "icona": "🅰️", "tipo": "tutti", "urgenza": "Avviso: officina a breve",
     "significato": "L'ABS non funziona: i freni normali funzionano ma le ruote possono bloccarsi in frenata brusca.", "azioni": ["Guida con più distanza di sicurezza e frena con anticipo.", "Fai controllare il sensore ruota o la centralina."], "cause": ["Sensore ruota sporco o guasto", "Centralina ABS", "Fusibile"]},
    {"nome": "ESP / controllo di trazione", "colore": "giallo", "icona": "🚗", "tipo": "tutti", "urgenza": "Informazione o avviso",
     "significato": "Se LAMPEGGIA: il sistema sta intervenendo (asfalto scivoloso). Se è FISSA: sistema disattivato o guasto.", "azioni": ["Se lampeggia, riduci la velocità.", "Se è fissa, riaccendi il sistema col pulsante; altrimenti officina."], "cause": ["Sistema spento dal pulsante", "Sensore sterzo o ruote"]},
    {"nome": "Riserva carburante", "colore": "giallo", "icona": "⛽", "tipo": "termico", "urgenza": "Avviso: fai rifornimento",
     "significato": "Il serbatoio è in riserva.", "azioni": ["Fai rifornimento appena puoi (di solito restano 40-80 km).", "Evita di svuotare il serbatoio: può danneggiare la pompa."], "cause": ["Livello carburante basso"]},
    {"nome": "Candelette (diesel)", "colore": "giallo", "icona": "🌀", "tipo": "termico", "urgenza": "Informazione",
     "significato": "Preriscaldamento del diesel. Se resta accesa a motore avviato: anomalia.", "azioni": ["Attendi che si spenga prima di avviare.", "Se resta accesa o lampeggia: officina."], "cause": ["Preriscaldo normale", "Candelette o centralina"]},
    {"nome": "Usura pastiglie dei freni", "colore": "giallo", "icona": "🛞", "tipo": "tutti", "urgenza": "Avviso: sostituire a breve", "significato": "Le pastiglie sono consumate.", "azioni": ["Prenota la sostituzione entro pochi giorni.", "Se senti stridere o il pedale cambia: officina subito."], "cause": ["Usura normale"]},
    {"nome": "AdBlue / additivo", "colore": "giallo", "icona": "💧", "tipo": "termico", "urgenza": "Avviso: rabbocca entro i km indicati",
     "significato": "Il serbatoio AdBlue sta finendo: a zero l'auto può NON ripartire dopo lo spegnimento.", "azioni": ["Rabbocca l'AdBlue (in stazione o con tanica) appena puoi."], "cause": ["Livello AdBlue basso", "Sensore o riscaldatore"]},
    {"nome": "Manutenzione / tagliando (chiave inglese)", "colore": "giallo", "icona": "🔧", "tipo": "tutti", "urgenza": "Informazione", "significato": "Scadenza del tagliando o di un controllo periodico.", "azioni": ["Prenota il tagliando.", "Dopo l'intervento l'officina azzera l'indicatore."], "cause": ["Chilometri o mesi dal tagliando"]},
    {"nome": "Lampadina esterna guasta", "colore": "giallo", "icona": "💡", "tipo": "tutti", "urgenza": "Avviso: sostituisci appena puoi", "significato": "Una luce esterna non funziona.", "azioni": ["Controlla fari, stop e frecce e sostituisci la lampadina: è anche una sanzione."], "cause": ["Lampadina bruciata", "Fusibile"]},
    {"nome": "Sistema ibrido / elettrico · avviso", "colore": "giallo", "icona": "🔌", "tipo": "hv", "urgenza": "Avviso: officina a breve",
     "significato": "Anomalia non grave al sistema ibrido o di trazione: l'auto può ridurre le prestazioni.", "azioni": ["Puoi arrivare in officina con prudenza.", "Se la spia diventa ROSSA: fermati e spegni."], "cause": ["Sensori", "Batteria HV sbilanciata", "Software"]},
    {"nome": "Potenza ridotta (modalità tartaruga)", "colore": "giallo", "icona": "🐢", "tipo": "hv", "urgenza": "Avviso: raggiungi un luogo sicuro",
     "significato": "L'auto limita la potenza per proteggere batteria o motore (carica molto bassa, troppo caldo/freddo, guasto).", "azioni": ["Vedi la procedura «Modalità tartaruga» nella sezione Emergenza EV."], "cause": ["Carica troppo bassa", "Temperatura batteria", "Guasto"]},
    {"nome": "Batteria di trazione quasi scarica", "colore": "giallo", "icona": "🪫", "tipo": "hv", "urgenza": "Avviso: cerca una colonnina", "significato": "La carica è molto bassa.", "azioni": ["Spegni clima e consumi, guida dolcemente e cerca la colonnina più vicina."], "cause": ["Carica residua bassa"]},
    # ---------------- VERDI / BLU ----------------
    {"nome": "Luci anabbaglianti / di posizione", "colore": "verde", "icona": "💡", "tipo": "tutti", "urgenza": "Informazione", "significato": "Le luci sono accese.", "azioni": ["Nessuna."], "cause": []},
    {"nome": "Frecce", "colore": "verde", "icona": "↔️", "tipo": "tutti", "urgenza": "Informazione", "significato": "Una freccia è accesa. Se lampeggia veloce, una lampadina è bruciata.", "azioni": ["Se lampeggia veloce, sostituisci la lampadina."], "cause": []},
    {"nome": "Cruise control / limitatore", "colore": "verde", "icona": "🛣️", "tipo": "tutti", "urgenza": "Informazione", "significato": "Il controllo di velocità è attivo.", "azioni": ["Nessuna."], "cause": []},
    {"nome": "Start & Stop attivo", "colore": "verde", "icona": "⏸️", "tipo": "termico", "urgenza": "Informazione", "significato": "Il motore si è spento da fermo per risparmiare carburante.", "azioni": ["Nessuna."], "cause": []},
    {"nome": "READY (pronto alla marcia)", "colore": "verde", "icona": "🟢", "tipo": "hv", "urgenza": "Informazione", "significato": "Veicolo elettrico/ibrido acceso e pronto: si muove in silenzio.", "azioni": ["Attenzione ai pedoni: l'auto è molto silenziosa."], "cause": []},
    {"nome": "Ricarica in corso", "colore": "verde", "icona": "🔌", "tipo": "hv", "urgenza": "Informazione", "significato": "La batteria è in ricarica.", "azioni": ["Nessuna."], "cause": []},
    {"nome": "Luci abbaglianti", "colore": "blu", "icona": "🔵", "tipo": "tutti", "urgenza": "Informazione", "significato": "Gli abbaglianti sono accesi.", "azioni": ["Spegnili se incroci altri veicoli."], "cause": []},
    {"nome": "Temperatura bassa / ghiaccio", "colore": "blu", "icona": "❄️", "tipo": "tutti", "urgenza": "Informazione", "significato": "Motore freddo o rischio ghiaccio (sotto 3 °C).", "azioni": ["Guida con prudenza, il fondo può essere ghiacciato."], "cause": []},
]
_AE_ORDINE = {"rosso": 0, "giallo": 1, "verde": 2, "blu": 3}
_AE_COL = {"rosso": ("🔴", "#b71c1c", "#ffebee"), "giallo": ("🟡", "#e65100", "#fff8e1"), "verde": ("🟢", "#1b5e20", "#e8f5e9"), "blu": ("🔵", "#0d47a1", "#e3f2fd")}

_AE_HV = ("**⚠️ REGOLA FISSA — alta tensione (HV).** I cavi e i componenti **arancioni** sono ad alta tensione (400-800 V): possono uccidere. **Non toccarli, non tagliarli, non aprire coperchi.** "
          "Non confondere la rete a **12 V** (cavi rossi e neri, come su ogni auto) con la rete ad **alta tensione**. Il «sezionatore d'emergenza» serve **solo ai Vigili del Fuoco e ai tecnici formati**.")

_AE_PROCEDURE = {
    "🔋 Batteria 12V scarica (elettrica/ibrida)": {
        "intro": "Anche se la batteria di trazione è piena, **se la 12 V è scarica l'auto non si accende**: la 12 V alimenta serrature, display, freno di stazionamento e i contattori dell'alta tensione.",
        "passi": ["Apri l'auto con la **chiave meccanica** nascosta nel telecomando (di solito c'è un piccolo sblocco sul telecomando).",
                  "Cerca nel manuale il **punto di avviamento d'emergenza a 12 V** (sotto il cofano o sotto una copertura: spesso ci sono morsetti dedicati). **Mai collegare nulla ai componenti arancioni.**",
                  "Usa un **booster 12 V** o un'altra auto a 12 V. Collega **prima il + (rosso)** al morsetto positivo indicato, poi il **– (nero)** al punto di massa indicato dal costruttore.",
                  "Attendi 2-5 minuti, poi **premi il freno e il pulsante di avvio** fino a vedere **READY**.",
                  "Scollega in **ordine inverso** (prima il nero, poi il rosso) e **lascia l'auto in READY**: la 12 V si ricarica dalla batteria di trazione.",
                  "Fai **controllare la batteria 12 V** in officina entro pochi giorni: se è vecchia va sostituita.",
                  "Se non parte: **carro attrezzi con ruote motrici sollevate**. Mai trainare con le ruote motrici a terra senza l'ok del manuale."]},
    "🔌 Cavo di ricarica bloccato": {
        "intro": "Il connettore resta bloccato per sicurezza fino al termine della sessione o allo sblocco dell'auto.",
        "passi": ["**Termina la ricarica** dall'app, dalla colonnina o dal display dell'auto.",
                  "**Sblocca l'auto** con il telecomando o la chiave: molti modelli sbloccano anche il cavo.",
                  "Attendi qualche secondo e **tira il connettore con calma**, senza forzare.",
                  "Se non si libera: cerca nel manuale lo **sblocco d'emergenza** (di solito un tirante o una cordicella nel bagagliaio, dietro un pannello, o un comando dal display).",
                  "**Non usare utensili né forzare**: puoi rompere il connettore.",
                  "Se persiste: chiama l'**assistenza** del costruttore o il **gestore della colonnina**."]},
    "🐢 Modalità tartaruga / potenza ridotta": {
        "intro": "L'auto limita la potenza per proteggere batteria e motore. Cause comuni: **carica molto bassa**, **batteria troppo calda o troppo fredda**, **surriscaldamento**, guasto.",
        "passi": ["**Mantieni la calma**, accendi le **4 frecce** e porta l'auto in un punto sicuro con la potenza che hai.", "Evita accelerazioni brusche; **spegni clima e riscaldamento** per risparmiare energia.",
                  "Se la carica è bassa: **vai alla colonnina più vicina** o chiama il soccorso.", "Se è un problema di temperatura: **fermati all'ombra e lascia raffreddare** (poi riprova).",
                  "Se compare una spia **rossa** (HV, temperatura batteria) o **fumo/odore**: **fermati, spegni, scendi e allontanati**.", "Se la potenza non torna: officina specializzata."]},
    "🔥 Fumo, fuoco o allagamento": {
        "intro": "**La priorità è la vita delle persone, non l'auto.**",
        "passi": ["**Accosta**, inserisci il freno di stazionamento, **spegni** il veicolo e accendi le **4 frecce**.", "**Fai scendere tutti** subito, anche con le cinture da sganciare, e **allontanatevi di almeno 15-20 metri** (meglio dietro il guardrail), controvento.",
                  "Chiama il **112 / 115** e dì chiaramente: **«veicolo ELETTRICO (o ibrido)»**, dove sei e se ci sono feriti.", "**Non aprire cofano o portellone** se c'è fumo; **non toccare i cavi arancioni**; non tentare di spegnere la batteria con estintori piccoli.",
                  "Una batteria danneggiata può **riaccendersi anche ore dopo**: lascia il lavoro ai Vigili del Fuoco, ai quali serve il **sezionatore d'emergenza** (indicato nella «guida di soccorso» del modello).",
                  "**Allagamento:** non entrare in acqua alta; se sei dentro, esci subito. **Non ricaricare mai** un veicolo elettrico dopo un allagamento: va controllato da un tecnico."]},
    "🔋 Batteria al litio (monopattino / e-bike)": {
        "intro": "Le batterie al litio dei monopattini e delle biciclette elettriche, se si danneggiano o si surriscaldano, possono **fumare o incendiarsi all'improvviso**. Non sono alta tensione come quelle delle auto, ma il fuoco è pericoloso.",
        "passi": ["Se la batteria **scalda troppo, gonfia, puzza o fuma**: **smetti di usarla** e **stacca il caricatore** subito, se non c'è pericolo a toccarlo.", "Mettila **all'aperto**, lontano da case, auto e materiali infiammabili, **mai sotto una scala o in un corridoio**.",
                  "Se c'è fumo o fiamma: **allontanati**, non respirare i fumi e chiama il **115 (Vigili del Fuoco)** o il **112**. Non cercare di salvare il mezzo.", "**Non ricaricare mai** una batteria che ha preso un urto forte, è caduta in acqua o è deformata.",
                  "Ricarica **sotto controllo**, con il caricatore originale, non di notte e non su un letto o un divano. Dopo un incendio o un urto, falla controllare da un tecnico prima di riusarla."]},
    "🔋 Batteria 12V scarica (auto termica)": {
        "intro": "Valido per benzina e diesel (per le elettriche/ibride vedi la procedura dedicata).",
        "passi": ["Servono cavi di avviamento e un'auto con batteria 12 V (o un booster). Spegni entrambe le auto.", "Collega il **+ rosso** al + della batteria scarica, poi al + di quella buona.", "Collega il **– nero** al – della batteria buona e l'altro capo a una **parte metallica nuda del motore** della tua auto (non al polo –).",
                  "Avvia l'auto buona, aspetta 2-3 minuti, poi avvia la tua.", "Scollega **in ordine inverso**. Lascia il motore acceso per 20-30 minuti. Se si ripete: batteria da sostituire."]},
}

_AE_CAI = [
    ("1. Sicurezza", ["Fermati, accendi le 4 frecce, indossa il giubbotto retroriflettente e metti il triangolo (10 m in città, 50 m fuori; 100 m in autostrada).", "Se ci sono feriti o pericolo chiama il **112**. Non spostare i feriti.", "Se ci sono veicoli elettrici/ibridi danneggiati o fumo: allontanati di 15-20 m."]),
    ("2. Cosa raccogliere sul posto", ["Data, ora e **luogo preciso** (via, numero civico, km).", "**Targhe** e marche dei veicoli coinvolti; compagnia e numero di polizza dell'altra parte.", "Nome, indirizzo e telefono dei conducenti e dei **testimoni**.", "**Foto**: danni, posizione dei veicoli, targhe, segnaletica e condizioni della strada."]),
    ("3. Il modulo CAI (CID)", ["Compila il modulo blu/rosso (uno per veicolo): **non firmare** se non sei d'accordo; segna solo i fatti.", "Se firmate entrambi la **versione concordata** vale per l'assicurazione. Se non siete d'accordo: scrivi la tua versione e fai foto."]),
    ("4. Dopo", ["Invia la denuncia alla tua compagnia **entro 3 giorni**.", "Conserva foto, modulo, preventivi e fatture delle riparazioni."]),
]


def ae_spie(v=None):
    """Catalogo delle spie, cercabile e filtrabile per colore."""
    st.markdown("<div style='background:#fff3e0;border-left:6px solid #e65100;padding:8px 12px;border-radius:10px;margin:6px 0'>🚦 <b>Come si leggono:</b> 🔴 rosso = <b>fermati subito</b> · 🟡 giallo/arancio = <b>avviso, officina a breve</b> · 🟢🔵 verde/blu = <b>informazione</b>. Per il tuo modello vale il manuale.</div>", unsafe_allow_html=True)
    ev = bool(v) and str(v.get("alimentazione", "")).startswith(("Elettrica", "Ibrida"))
    c1, c2 = st.columns([3, 2])
    cerca = c1.text_input("🔍 Cerca una spia", key="ae_cerca", placeholder="olio, freni, motore, batteria…", label_visibility="collapsed")
    colore = c2.selectbox("Colore", ["Tutti i colori", "🔴 Rosse", "🟡 Gialle", "🟢 Verdi e 🔵 blu"], key="ae_colore", label_visibility="collapsed")
    q = (cerca or "").strip().lower()
    elenco = []
    for s in _AE_SPIE:
        if s["tipo"] == "hv" and v and not ev:
            continue
        if s["tipo"] == "termico" and v and str(v.get("alimentazione", "")).startswith("Elettrica"):
            continue
        if colore.startswith("🔴") and s["colore"] != "rosso" or colore.startswith("🟡") and s["colore"] != "giallo" or colore.startswith("🟢") and s["colore"] not in ("verde", "blu"):
            continue
        if q and q not in (s["nome"] + " " + s["significato"] + " " + " ".join(s["cause"])).lower():
            continue
        elenco.append(s)
    if not elenco:
        st.info("Nessuna spia corrisponde. Se la spia non c'è in elenco, cercala nel manuale del tuo veicolo.")
    for s in sorted(elenco, key=lambda x: _AE_ORDINE[x["colore"]]):
        ic, col, bg = _AE_COL[s["colore"]]
        with st.expander(f"{ic} {s['icona']} {s['nome']}"):
            if s["colore"] == "rosso":
                st.markdown(f"<div style='background:{bg};border:2px solid {col};border-radius:12px;padding:10px 12px;color:{col};font-weight:900'>⚠️ PERICOLO — {_h_ae.escape(s['urgenza'])}. Accosta subito in sicurezza e spegni il veicolo.</div>", unsafe_allow_html=True)
            st.markdown(f"**Colore:** {s['colore'].capitalize()}  \n**Urgenza:** {s['urgenza']}  \n**Significato:** {s['significato']}")
            st.markdown("**Cosa fare subito**\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(s["azioni"], 1)))
            if s["cause"]:
                st.markdown("**Possibili cause:** " + ", ".join(s["cause"]) + ".")
    st.caption("Non ho una fotocamera «intelligente» che riconosce la spia da una foto: cerca per nome o filtra per colore. Se hai dubbi e la spia è rossa: fermati.")


def ae_procedure(v=None):
    st.error("🆘 In caso di pericolo per le persone chiama subito il **112**.")
    st.markdown(_AE_HV)
    for titolo, p in _AE_PROCEDURE.items():
        with st.expander(titolo):
            st.markdown(p["intro"])
            st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(p["passi"], 1)))
    st.caption("Indicazioni generali valide per la maggior parte dei modelli: per il tuo veicolo vale la **guida di soccorso del costruttore** e il manuale.")


def ae_cai_guida():
    for titolo, righe in _AE_CAI:
        with st.expander(titolo):
            st.markdown("\n".join(f"- {r}" for r in righe))
