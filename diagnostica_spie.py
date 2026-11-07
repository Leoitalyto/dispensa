# -*- coding: utf-8 -*-
"""DIAGNOSTICA · ARCHIVIO DELLE SPIE IN 14 CATEGORIE.

• Non sostituisce il catalogo esistente (auto_emergenza.py): lo ARRICCHISCE. Alle 32 spie già presenti dà una categoria e ne aggiunge altre (auto, moto, elettrici, camion, autobus, mezzi agricoli).
• Le 14 categorie: Motore · Olio e lubrificazione · Temperatura e raffreddamento · Freni · Batteria e alternatore · Pneumatici · Airbag e sicurezza · ABS ed ESP · Filtri e antinquinamento · AdBlue e sistema SCR · Illuminazione · Cambio e trasmissione · Sistemi elettronici · Assistenza alla guida.
• Si cerca per nome, simbolo (come è fatto), categoria, descrizione e colore. Si può aggiornare nel tempo: aggiungere una voce a mano in questo file, oppure con la base condivisa (auto_base.py), che cresce con l'uso.
• Il catalogo è dentro il programma: si consulta senza IA e senza servizi esterni.
Caricato dopo auto_base.py."""
import html as _h_aa

import streamlit as st

AA_CATEGORIE = ["🔧 Motore", "🛢️ Olio e lubrificazione", "🌡️ Temperatura e raffreddamento", "🛑 Freni", "🔋 Batteria e alternatore", "🛞 Pneumatici", "🛡️ Airbag e sicurezza", "⚙️ ABS ed ESP",
                "🌫️ Filtri e antinquinamento", "💧 AdBlue e sistema SCR", "💡 Illuminazione", "🕹️ Cambio e trasmissione", "🖥️ Sistemi elettronici", "🚦 Assistenza alla guida"]
_C = {c.split(" ", 1)[1]: c for c in AA_CATEGORIE}                       # «Motore» → «🔧 Motore»

# categoria delle spie già presenti nel catalogo (per nome)
_AA_ESISTENTI = {
    "Pressione olio motore": "Olio e lubrificazione", "Temperatura del liquido di raffreddamento (surriscaldamento)": "Temperatura e raffreddamento", "Impianto frenante / freno a mano / liquido freni": "Freni",
    "Batteria / carica (alternatore)": "Batteria e alternatore", "Airbag / sistema di ritenuta": "Airbag e sicurezza", "Cintura non allacciata": "Airbag e sicurezza", "Servosterzo / sterzo": "Sistemi elettronici",
    "Porta, cofano o portellone aperti": "Sistemi elettronici", "Sistema ad alta tensione (HV) · guasto grave": "Sistemi elettronici", "Temperatura batteria di trazione troppo alta": "Temperatura e raffreddamento",
    "Controllo motore (Check engine / MIL)": "Motore", "Filtro antiparticolato (DPF/FAP)": "Filtri e antinquinamento", "Pressione pneumatici (TPMS)": "Pneumatici", "ABS": "ABS ed ESP", "ESP / controllo di trazione": "ABS ed ESP",
    "Riserva carburante": "Motore", "Candelette (diesel)": "Motore", "Usura pastiglie dei freni": "Freni", "AdBlue / additivo": "AdBlue e sistema SCR", "Manutenzione / tagliando (chiave inglese)": "Sistemi elettronici",
    "Lampadina esterna guasta": "Illuminazione", "Sistema ibrido / elettrico · avviso": "Sistemi elettronici", "Potenza ridotta (modalità tartaruga)": "Motore", "Batteria di trazione quasi scarica": "Batteria e alternatore",
    "Luci anabbaglianti / di posizione": "Illuminazione", "Frecce": "Illuminazione", "Cruise control / limitatore": "Assistenza alla guida", "Start & Stop attivo": "Motore", "READY (pronto alla marcia)": "Sistemi elettronici",
    "Ricarica in corso": "Batteria e alternatore", "Luci abbaglianti": "Illuminazione", "Temperatura bassa / ghiaccio": "Temperatura e raffreddamento",
}

_G, _R, _V, _B = "giallo", "rosso", "verde", "blu"
_URG = {"emerg": "EMERGENZA: arresto immediato", "fren": "EMERGENZA: i freni potrebbero non funzionare", "caldo": "EMERGENZA: fermarsi e lasciar raffreddare", "urg": "Urgente: riduci la velocità e fermati appena possibile",
        "off": "Avviso: officina a breve", "info": "Informazione", "sicur": "Sicurezza: da controllare subito", "poss": "Avviso: sostituisci appena puoi"}


def _s(cat, nome, colore, icona, urg, significato, azioni, cause, aspetto, tipo="tutti", solo=""):
    return {"categoria": cat, "nome": nome, "colore": colore, "icona": icona, "tipo": tipo, "urgenza": _URG.get(urg, urg), "significato": significato, "azioni": azioni, "cause": cause, "aspetto": aspetto, "solo": solo}


AA_NUOVE = [
    # ---------------- MOTORE
    _s("Motore", "Controllo motore LAMPEGGIANTE", _G, "🔧", "urg", "Il motore ha mancate accensioni gravi: il carburante non bruciato può rovinare in fretta il catalizzatore (costoso) e il motore. È più seria della spia fissa.",
       ["Scarica l'acceleratore, evita sforzi e salite e non andare veloce.", "Fermati appena puoi in un posto sicuro e spegni il motore.", "Non continuare il viaggio a lungo: chiama l'assistenza o vai piano e dritto in officina."],
       ["Candele o bobine d'accensione", "Iniettori", "Troppa o troppo poca aria/carburante", "Sensori del motore"], "motore giallo/arancio che lampeggia"),
    _s("Motore", "EPC · controllo elettronico della potenza (VW, Audi, Skoda, Seat)", _G, "🔧", "off", "Il sistema che gestisce l'acceleratore e la potenza ha trovato un guasto. Il motore può dare meno potenza o spegnersi.",
       ["Se la spia è fissa e l'auto va, guida con prudenza fino all'officina.", "Se si accende insieme a un cambio di comportamento (strappi, poca potenza) fermati appena puoi.", "Non insistere con l'acceleratore: fai leggere i codici in officina."],
       ["Pedale o corpo farfallato", "Sensore del pedale del freno", "Centralina motore", "Cablaggi"], "scritta EPC in un cerchio o a fianco di un ingranaggio"),
    _s("Motore", "Immobilizer / antifurto: il motore non parte", _G, "🔑", "off", "L'auto non riconosce la chiave (il chip dentro la chiave) e blocca l'avviamento per sicurezza.",
       ["Prova con l'altra chiave e togli altre chiavi o portachiavi accanto a quella usata.", "Sostituisci la batteria della chiave, se la tua auto la prevede.", "Se non parte, chiama l'assistenza: serve un tecnico per la chiave."],
       ["Batteria della chiave scarica", "Chip della chiave rotto", "Antenna del lettore", "Batteria dell'auto debole"], "auto con lucchetto o chiave dentro un'auto"),
    _s("Motore", "Start & Stop non disponibile / guasto", _G, "🔧", "info", "Il sistema che spegne il motore al semaforo non funziona o è temporaneamente fuori uso. Si può guidare normalmente.",
       ["Controlla se il motore è ancora freddo o la batteria è debole: spesso torna da solo.", "Se resta accesa, fai controllare la batteria in officina."],
       ["Batteria 12V debole o vecchia", "Sensore della batteria", "Temperatura troppo bassa o alta", "Cintura o porta aperta"], "A cerchiata con la parola OFF o barrata"),
    _s("Motore", "Acqua nel filtro del gasolio", _G, "💧", "Avviso: scarica l'acqua appena possibile", "C'è acqua nel prefiltro del gasolio: se arriva agli iniettori li rovina (costosissimi). Comune su diesel, camion e trattori.",
       ["Fermati e spegni il motore, non insistere con gli avviamenti.", "Se sei capace, scarica l'acqua con la vite di spurgo sotto il filtro; altrimenti vai in officina.", "Cambia fornitore di gasolio se succede spesso e svuota la condensa dal serbatoio."],
       ["Gasolio contaminato", "Condensa nel serbatoio", "Filtro pieno d'acqua"], "filtro con una goccia o la scritta H2O", tipo="termico"),
    _s("Motore", "Catalizzatore troppo caldo", _G, "🔥", "urg", "Il catalizzatore sta superando la temperatura sicura (di solito per mancate accensioni): può fondersi o dare fuoco all'erba secca sotto l'auto.",
       ["Riduci subito la velocità ed evita acceleratori forti.", "Non parcheggiare sull'erba secca. Fermati appena puoi e fai controllare l'auto.", "Se senti odore di bruciato o vedi fumo, spegni e allontanati."],
       ["Mancate accensioni", "Miscela troppo ricca", "Catalizzatore danneggiato"], "scarico/catalizzatore con le fiamme", tipo="termico"),
    _s("Motore", "Tappo del serbatoio non chiuso", _G, "⛽", "info", "Il tappo del carburante non è chiuso bene, e il sistema antievaporazione può dare errore.",
       ["Fermati, togli il tappo e richiudilo con più scatti.", "Se la spia resta, può servire un tappo nuovo (guarnizione)."], ["Tappo allentato", "Guarnizione vecchia"], "pompa di benzina con tappo", tipo="termico"),
    _s("Motore", "Folle (N) inserita", _V, "🟢", "info", "Il cambio è in folle. Su moto e auto con la spia, è un'informazione.", ["Nessuna azione: la spia si spegne quando inserisci una marcia."], [], "lettera N verde"),
    _s("Motore", "Cavalletto laterale abbassato (moto)", _G, "🏍️", "sicur", "Il cavalletto è giù: in molte moto impedisce di partire, e se parti con il cavalletto abbassato può farti cadere in curva.",
       ["Fermati e alza il cavalletto prima di partire.", "Se la spia resta con il cavalletto alzato, il sensore è guasto: fai controllare."], ["Cavalletto abbassato", "Sensore del cavalletto guasto o sporco"], "moto con una freccia verso il basso o il cavalletto", solo="moto"),
    # ---------------- OLIO
    _s("Olio e lubrificazione", "Livello olio motore basso", _G, "🛢️", "Avviso: rabbocca entro i km indicati", "Nel motore c'è poco olio. Finché non scende troppo non si rovina, ma non va ignorata: senza olio il motore si danneggia.",
       ["Ferma l'auto in piano, spegni e aspetta 5-10 minuti.", "Controlla con l'astina e rabbocca con l'olio indicato nel manuale, a piccole dosi.", "Se il livello scende spesso, c'è una perdita o il motore consuma olio: vai in officina."],
       ["Consumo normale di olio", "Perdite", "Cambio olio in ritardo"], "oliatore con una riga ondulata sotto", tipo="termico"),
    _s("Olio e lubrificazione", "Olio degradato / qualità dell'olio", _G, "🛢️", "poss", "Il sensore dice che l'olio è invecchiato o diluito (per esempio dal gasolio): perde la capacità di proteggere.",
       ["Programma il cambio olio e filtro al più presto.", "Se fai spesso brevi percorsi o rigenerazioni del filtro, chiedi un cambio olio più ravvicinato."], ["Olio vecchio", "Diluizione con carburante", "Percorsi brevi"], "oliatore con simboli di scintille", tipo="termico"),
    _s("Olio e lubrificazione", "Temperatura olio troppo alta", _R, "🛢️", "caldo", "L'olio è troppo caldo e non lubrifica bene: il motore rischia di rovinarsi.", ["Riduci il carico, fermati in un posto sicuro e lascia il motore al minimo qualche minuto, poi spegni.", "Controlla il livello olio e il radiatore.", "Non ripartire finché la temperatura non scende; chiama l'assistenza se si ripete."],
       ["Carico eccessivo o salite lunghe", "Livello olio basso", "Radiatore dell'olio sporco", "Termostato guasto"], "oliatore con un termometro"),
    _s("Olio e lubrificazione", "Filtro idraulico intasato (macchine operatrici, trattori)", _G, "🚜", "off", "Il filtro dell'olio idraulico è sporco: la macchina può muoversi male e le pompe consumarsi.",
       ["Termina il lavoro in corso con cautela, spegni e fai sostituire il filtro (e se serve l'olio).", "Non lavorare con la spia accesa a olio freddo: a volte si spegne a caldo, ma non va ignorata."], ["Filtro da cambiare", "Olio freddo", "Sporcizia nel circuito"], "filtro con frecce", solo="agricoli e macchine operatrici"),
    # ---------------- TEMPERATURA
    _s("Temperatura e raffreddamento", "Livello liquido di raffreddamento basso", _G, "🌡️", "Avviso: rabbocca prima di partire", "Nel circuito di raffreddamento manca liquido: se continua a calare il motore si surriscalda.",
       ["Ferma e spegni. NON aprire il tappo a motore caldo: può spruzzare liquido bollente.", "A motore freddo rabbocca con il liquido giusto (vedi manuale). Cerca macchie sotto l'auto.", "Se manca spesso, c'è una perdita: vai in officina."],
       ["Perdita (tubi, radiatore, pompa)", "Guarnizione della testata", "Tappo del radiatore"], "termometro dentro onde con una riga di livello"),
    # ---------------- FRENI
    _s("Freni", "Freno di stazionamento elettrico guasto", _G, "🅿️", "off", "Il freno a mano elettrico non funziona bene: potresti non riuscire a bloccarlo o a sbloccarlo.",
       ["Parcheggia in piano, inserisci la marcia (o P) e metti dei cunei se sei in pendenza.", "Non lasciare l'auto in discesa affidandoti solo al freno elettrico.", "Fai controllare il sistema in officina."], ["Motorino del freno", "Cablaggio o fusibile", "Batteria debole", "Software"], "P in un cerchio con un punto esclamativo"),
    _s("Freni", "Autohold / mantenimento frenata attivo", _V, "🅿️", "info", "Il sistema tiene l'auto ferma al semaforo senza tenere il piede sul freno. È una funzione attiva.", ["Nessuna azione. Si disattiva da solo quando acceleri."], [], "A in un cerchio verde (AUTO HOLD)"),
    _s("Freni", "Pressione aria dell'impianto frenante bassa (mezzi pesanti)", _R, "🛑", "fren", "Nei camion e negli autobus i freni usano l'aria compressa. Se la pressione è bassa, i freni possono non funzionare o bloccare le ruote.",
       ["Accosta subito in sicurezza e blocca il mezzo (freno di stazionamento).", "Non ripartire finché la pressione non è risalita (la spia si spegne e la lancetta entra nel settore verde).", "Se non risale, chiama il soccorso: c'è una perdita o il compressore non funziona."],
       ["Perdita d'aria", "Compressore guasto o cinghia", "Essiccatore o valvole", "Condensa o gelo"], "cerchio rosso con una P e freccette", solo="camion e autobus"),
    _s("Freni", "EBS / ABS del rimorchio guasto (mezzi pesanti)", _G, "🛑", "off", "Il sistema elettronico dei freni del camion o del rimorchio ha un guasto: la frenata potrebbe essere meno stabile.",
       ["Guida con distanze di sicurezza maggiori e velocità ridotta.", "Controlla il collegamento elettrico e pneumatico del rimorchio.", "Fai controllare l'impianto prima di un nuovo viaggio."], ["Spina o cavo del rimorchio", "Sensori ruota", "Centralina EBS"], "ABS con una R o un rimorchio", solo="camion e autobus"),
    _s("Freni", "Rallentatore (retarder) surriscaldato (mezzi pesanti)", _G, "🛑", "off", "Il freno rallentatore sta lavorando troppo ed è troppo caldo.", ["Passa alla marcia più bassa e usa di più i freni di servizio a intervalli.", "Evita discese lunghe a velocità alta: usa anche il freno motore."], ["Discesa lunga", "Liquido di raffreddamento basso", "Troppo carico"], "scritta RET", solo="camion e autobus"),
    # ---------------- BATTERIA
    _s("Batteria e alternatore", "Batteria 12V debole (auto ibride ed elettriche)", _G, "🔋", "off", "Anche le auto elettriche hanno una piccola batteria da 12V che le fa «svegliare». Se è debole l'auto può non avviarsi, anche con la batteria grande carica.",
       ["Misura la tensione a veicolo spento (circa 12,4-12,8 V è sano; sotto 12,0 V è scarica).", "Ricaricala o falla sostituire; usa il soccorso se l'auto non si accende.", "Non staccare cavi arancioni dell'alta tensione: tocca solo la parte a 12V."], ["Batteria 12V vecchia", "Luci lasciate accese", "Carica del convertitore (DC/DC) non riuscita"], "batteria con 12V", tipo="hv"),
    _s("Batteria e alternatore", "Batteria della chiave scarica", _G, "🔑", "info", "La pila del telecomando o della chiave elettronica è quasi scarica.", ["Sostituisci la pila (di solito CR2032) appena puoi.", "Se l'auto non riconosce la chiave, avvicinala al punto indicato nel manuale (spesso vicino al pulsante di avviamento)."], ["Pila scarica"], "chiave con segnale"),
    # ---------------- PNEUMATICI
    _s("Pneumatici", "Sistema pressione pneumatici guasto (TPMS)", _G, "🛞", "off", "La spia lampeggia per circa un minuto e poi resta fissa: il controllo della pressione non funziona (non è detto che una gomma sia sgonfia).",
       ["Controlla comunque la pressione di tutte le gomme con il manometro.", "Fai controllare i sensori (pile dei sensori o dopo il cambio gomme)."], ["Sensore scarico o rotto", "Ruota nuova non registrata", "Interferenze"], "ferro di cavallo con punto esclamativo che lampeggia"),
    # ---------------- AIRBAG
    _s("Airbag e sicurezza", "Airbag passeggero disattivato (OFF)", _V, "🛡️", "info", "L'airbag davanti al passeggero è spento (di solito per un seggiolino contro marcia). La spia lo conferma.",
       ["Controlla che sia spento solo se c'è un seggiolino rivolto indietro sul sedile davanti.", "Riattivalo quando il sedile è occupato da un adulto."], ["Interruttore manuale", "Sensore di occupazione sedile"], "passeggero con un airbag barrato e OFF"),
    # ---------------- ABS / ESP
    _s("ABS ed ESP", "ESP / controllo di trazione disattivato (OFF)", _G, "⚙️", "info", "Il controllo di stabilità è spento: l'auto non ti aiuta più in caso di slittamento. Va bene solo in casi particolari (neve alta, fango).",
       ["Riattivalo premendo il pulsante ESP OFF appena puoi.", "Se la spia compare da sola, c'è un guasto: vedi la spia ESP."], ["Pulsante premuto", "Guasto del sistema"], "auto che slitta con la scritta OFF"),
    _s("ABS ed ESP", "Controllo discesa (HDC) attivo", _V, "⛰️", "info", "L'auto mantiene da sola una velocità bassa in discesa frenando le ruote.", ["Nessuna azione: puoi tenere il piede lontano dai pedali."], [], "auto su una pendenza", tipo="tutti"),
    # ---------------- FILTRI / ANTINQUINAMENTO
    _s("Filtri e antinquinamento", "Filtro antiparticolato benzina (GPF) intasato", _G, "🌫️", "off", "Il filtro dei fumi dei motori a benzina moderni è pieno di fuliggine e deve rigenerarsi.", ["Percorri qualche chilometro a velocità costante e a regime medio-alto per farlo bruciare.", "Se la spia resta, vai in officina."], ["Percorsi brevi", "Miscela non perfetta"], "filtro con puntini", tipo="termico"),
    _s("Filtri e antinquinamento", "Sistema antinquinamento / emissioni", _G, "🌫️", "off", "Un componente che riduce i gas di scarico (catalizzatore, sonda lambda, EGR) non funziona bene. L'auto va, ma inquina più del consentito.",
       ["Fai leggere i codici di errore (vedi «Leggi codici errore»).", "Non rimandare troppo: può portare a danni al catalizzatore e a bocciare la revisione."], ["Sonda lambda", "Catalizzatore", "Valvola EGR", "Perdite nello scarico"], "motore con nuvoletta", tipo="termico"),
    _s("Filtri e antinquinamento", "Rigenerazione del filtro in corso (mezzi pesanti)", _G, "🌫️", "info", "Il camion sta bruciando la fuliggine del filtro: può servire tempo e temperatura alta allo scarico.",
       ["Se puoi, prosegui il viaggio senza spegnere finché la spia si spegne.", "Non fermarti in un posto con erba secca o materiali infiammabili: lo scarico è molto caldo.", "Se la spia non si spegne e si accende quella del motore, vai in officina."], ["Fuliggine accumulata", "Percorsi urbani"], "filtro con fiamma", solo="camion, autobus e mezzi agricoli"),
    _s("Filtri e antinquinamento", "Filtro aria intasato (camion, trattori, macchine operatrici)", _G, "🌫️", "off", "Il filtro dell'aria è sporco: il motore respira male, consuma di più e rende meno.", ["Pulisci o sostituisci il filtro appena possibile (in ambienti molto polverosi più spesso).", "Controlla che le prese d'aria non siano coperte."], ["Polvere o fieno", "Filtro vecchio"], "filtro con una freccia di aria", solo="camion, trattori e macchine operatrici"),
    # ---------------- ADBLUE
    _s("AdBlue e sistema SCR", "AdBlue: guasto al sistema o qualità non buona", _G, "💧", "urg", "Il sistema che usa AdBlue per pulire i fumi dei diesel non funziona. Per legge, dopo un certo numero di km l'auto può non riavviarsi.",
       ["Controlla il livello di AdBlue e rabbocca se serve, con prodotto di qualità (norma ISO 22241).", "Se compare un conto alla rovescia di km, vai in officina prima che finisca.", "Non rimandare: a conto finito, dopo lo spegnimento il motore può non ripartire."], ["Liquido sbagliato o vecchio", "Riscaldatore, pompa o iniettore", "Sensore NOx", "Congelamento"], "serbatoio AdBlue con un punto esclamativo", tipo="termico"),
    _s("AdBlue e sistema SCR", "Sensore NOx guasto", _G, "💧", "off", "Il sensore che misura gli ossidi di azoto allo scarico (serve al sistema AdBlue) non risponde.", ["Fai leggere i codici in officina: spesso è un sensore da sostituire.", "Non ignorare: può far scattare il conto alla rovescia dell'AdBlue."], ["Sensore usurato", "Cablaggio", "Scarico con perdite"], "NOx sopra un'impronta", tipo="termico"),
    # ---------------- ILLUMINAZIONE
    _s("Illuminazione", "Fari antinebbia anteriori accesi", _V, "💡", "info", "I fari antinebbia davanti sono accesi.", ["Spegnili quando la visibilità torna buona: possono abbagliare e vanno usati solo con nebbia, neve o pioggia forte."], [], "faro verde con linee oblique"),
    _s("Illuminazione", "Fendinebbia posteriore acceso", _G, "💡", "info", "La luce rossa antinebbia dietro è accesa.", ["Spegnila appena la nebbia finisce: abbaglia chi ti segue (e va usata solo con visibilità sotto i 50 metri)."], [], "luce con linee e freccia (ambra)"),
    _s("Illuminazione", "Abbaglianti automatici attivi", _V, "💡", "info", "L'auto accende e spegne gli abbaglianti da sola. È una funzione attiva.", ["Nessuna azione: puoi disattivarla dal pulsante delle luci se non ti piace."], [], "faro con A (AUTO)"),
    _s("Illuminazione", "Fari adattivi o direzionali guasti", _G, "💡", "off", "I fari che girano seguendo la curva non funzionano bene.", ["Guida con prudenza di notte e fai controllare il sistema.", "Controlla che i fari non siano rotti o appannati."], ["Motorino del faro", "Sensore dello sterzo", "Livello fari"], "faro con una freccia curva", tipo="tutti"),
    # ---------------- CAMBIO
    _s("Cambio e trasmissione", "Temperatura olio del cambio troppo alta", _R, "🕹️", "caldo", "L'olio del cambio automatico è troppo caldo: la trasmissione si può rovinare.", ["Accosta in sicurezza, metti in P o folle e lascia il motore al minimo per qualche minuto, poi spegni.", "Non ripartire se la spia resta accesa: chiama il soccorso.", "Evita di trainare molto in salita o di guidare a lungo in colonna."],
       ["Traino o salite lunghe", "Olio poco o vecchio", "Radiatore del cambio", "Guasto interno"], "ingranaggio con un termometro"),
    _s("Cambio e trasmissione", "Cambio automatico o robotizzato: guasto", _G, "🕹️", "off", "Il cambio ha un'anomalia. Può funzionare solo con alcune marce (modalità di emergenza).", ["Guida piano, senza strappi, fino all'officina.", "Se si accende con strattoni forti o rumori, fermati e chiama l'assistenza."], ["Olio cambio", "Elettrovalvole", "Sensori", "Frizione"], "ingranaggio con punto esclamativo"),
    _s("Cambio e trasmissione", "Frizione surriscaldata o usurata", _G, "🕹️", "off", "La frizione si sta scaldando troppo (salite, manovre lunghe, partenze in pendenza).", ["Fermati qualche minuto e lascia raffreddare.", "Non tenere l'auto ferma in salita con la frizione: usa i freni.", "Se si ripete, fai controllare la frizione."], ["Partenze in salita", "Frizione consumata", "Traino"], "frizione con un termometro"),
    _s("Cambio e trasmissione", "Trazione integrale / differenziale guasto", _G, "🕹️", "off", "Il sistema che porta la forza a tutte le ruote ha un guasto.", ["Evita fondo difficile (neve, fango) finché non è controllato.", "Fai leggere i codici in officina."], ["Giunto, differenziale", "Sensori", "Olio"], "4x4 con punto esclamativo"),
    _s("Cambio e trasmissione", "Presa di forza (PTO) inserita (trattori, camion)", _V, "🚜", "info", "La presa di forza è collegata: gira un albero per attrezzi o pompe.", ["Disinseriscila prima di scendere e prima di spostare il mezzo.", "Non indossare abiti larghi vicino all'albero in rotazione."], [], "albero di trasmissione con PTO", solo="trattori e camion"),
    _s("Cambio e trasmissione", "Blocco del differenziale inserito", _V, "🚜", "info", "Le ruote sono collegate per avere più trazione su fondo difficile.", ["Disinseriscilo su fondo normale e in curva stretta: stressa la trasmissione."], [], "differenziale con un lucchetto", solo="trattori e camion"),
    _s("Cambio e trasmissione", "Modalità di guida (Eco, Sport, Neve)", _B, "🕹️", "info", "Hai scelto un modo di guida che cambia risposta di motore e cambio.", ["Nessuna azione. Torna in normale se non serve."], [], "scritta ECO, SPORT o fiocco di neve"),
    # ---------------- SISTEMI ELETTRONICI
    _s("Sistemi elettronici", "Avviso generico (triangolo con punto esclamativo)", _G, "⚠️", "off", "L'auto vuole dirti qualcosa: guarda il messaggio sul display del cruscotto. Può essere piccolo (porta, pressione) o più importante.",
       ["Leggi con attenzione il messaggio scritto.", "Se non c'è un messaggio o parla di freni, sterzo o motore, fermati in sicurezza.", "Cerca poi la spia indicata nell'archivio."], ["Qualunque anomalia segnalata sul display"], "triangolo giallo con punto esclamativo"),
    _s("Sistemi elettronici", "Chiave non rilevata (accesso senza chiave)", _G, "🔑", "info", "L'auto non trova la chiave elettronica: potrebbe non partire.", ["Porta la chiave vicino al lettore indicato nel manuale.", "Cambia la pila della chiave e allontana telefoni o altre chiavi."], ["Pila scarica", "Interferenze"], "chiave con punto interrogativo o X"),
    _s("Sistemi elettronici", "Liquido lavavetri basso", _G, "💧", "info", "Il serbatoio del lavacristalli sta finendo.", ["Rabbocca con acqua e liquido lavavetri (in inverno con antigelo)."], ["Serbatoio vuoto"], "parabrezza con spruzzi"),
    _s("Sistemi elettronici", "Sospensioni pneumatiche guaste (camion, autobus)", _G, "🚚", "off", "Le sospensioni ad aria non mantengono l'altezza giusta: il mezzo può inclinarsi o sbattere.", ["Controlla la pressione dell'aria e le perdite.", "Guida piano e fai controllare prima del carico pesante."], ["Perdita d'aria", "Soffietto rotto", "Sensore di altezza"], "mezzo con soffietto e un'onda", solo="camion e autobus"),
    _s("Sistemi elettronici", "Tachigrafo guasto o taratura scaduta (mezzi pesanti)", _G, "⏱️", "off", "Il tachigrafo, che registra guida e riposo, non funziona o ha la taratura scaduta: si rischiano sanzioni.", ["Fai controllare e tarare il tachigrafo in un centro autorizzato.", "Annota a mano i tempi finché non è riparato, come previsto dalla norma."], ["Taratura scaduta", "Sensori", "Alimentazione"], "disco con una freccia (cronotachigrafo)", solo="camion e autobus"),
    _s("Sistemi elettronici", "eCall / SOS guasto", _G, "🆘", "info", "Il sistema di chiamata automatica di emergenza non funziona. In caso di incidente potrebbe non chiamare i soccorsi.", ["In caso di bisogno chiama tu il 112.", "Fai controllare il modulo in officina."], ["Modulo di chiamata", "Batteria di riserva", "Antenna"], "SOS con triangolo"),
    _s("Sistemi elettronici", "Cavo di ricarica collegato (auto elettriche)", _V, "🔌", "info", "Il cavo è inserito: l'auto non si muove per sicurezza finché non lo togli.", ["Scollega il cavo prima di partire."], [], "spina con auto", tipo="hv"),
    _s("Sistemi elettronici", "Guasto al sistema di ricarica (auto elettriche)", _G, "🔌", "off", "La ricarica non parte o si ferma: può essere il cavo, la colonnina o un problema dell'auto.", ["Prova con un'altra colonnina o un altro cavo.", "Se succede sempre, fai controllare il caricatore di bordo in officina."], ["Colonnina o cavo", "Presa dell'auto", "Caricatore di bordo"], "spina con punto esclamativo", tipo="hv"),
    # ---------------- ASSISTENZA ALLA GUIDA
    _s("Assistenza alla guida", "Mantenimento della corsia attivo / guasto", _V, "🚦", "info", "Il sistema ti riporta dolcemente nella corsia se esci senza freccia. Se diventa gialla o c'è un messaggio, non è disponibile.", ["Tieni sempre le mani sul volante: è un aiuto, non guida al posto tuo.", "Se è guasto, pulisci la telecamera sul parabrezza e fai controllare."], ["Telecamera sporca o coperta", "Linee non visibili", "Guasto"], "auto tra due linee"),
    _s("Assistenza alla guida", "Cruise control adattivo (ACC) attivo / radar non disponibile", _V, "🚦", "info", "L'auto mantiene la velocità e la distanza dal veicolo davanti. Se compare un avviso giallo, il radar è sporco, coperto o guasto.", ["Pulisci il radar sul paraurti davanti (neve, fango, adesivi).", "Quando non è disponibile guida tu: distanza e velocità sono tua responsabilità."], ["Radar sporco o coperto", "Pioggia o nebbia forti", "Guasto"], "auto con onde davanti"),
    _s("Assistenza alla guida", "Frenata automatica d'emergenza (AEB) non disponibile", _G, "🚦", "off", "Il sistema che frena da solo per evitare un urto è spento o non funziona: devi frenare tu.", ["Aumenta la distanza di sicurezza.", "Pulisci la telecamera/radar e fai controllare se resta."], ["Sensore sporco", "Disattivata", "Guasto"], "auto con onde e un'esclamazione"),
    _s("Assistenza alla guida", "Sensori di parcheggio guasti", _G, "🚦", "info", "I sensori che suonano quando ti avvicini a un ostacolo non funzionano.", ["Manovra con più attenzione e usa gli specchi.", "Pulisci i sensori sul paraurti e fai controllare."], ["Sensore sporco o danneggiato", "Fusibile"], "auto con onde e P"),
    _s("Assistenza alla guida", "Angolo cieco (BSM) non disponibile", _G, "🚦", "info", "L'avviso per le auto che non vedi nello specchio non funziona.", ["Guarda sempre a mano nello specchio e fuori dal finestrino prima di cambiare corsia.", "Pulisci il paraurti dietro e fai controllare il sistema."], ["Sensori sporchi", "Guasto"], "auto con due triangoli"),
]

_AA_FATTO = [False]


def aa_prepara():
    """Dà una categoria alle spie già presenti e aggiunge le nuove (una volta per ridisegno del programma)."""
    if "_AE_SPIE" not in globals():
        return
    for s in _AE_SPIE:
        if not s.get("categoria"):
            s["categoria"] = _AA_ESISTENTI.get(s["nome"], "Sistemi elettronici")
            s.setdefault("aspetto", "")
            s.setdefault("solo", "")
    nomi = {s["nome"] for s in _AE_SPIE}
    for n in AA_NUOVE:
        if n["nome"] not in nomi:
            _AE_SPIE.append(dict(n))
    _AA_FATTO[0] = True


def aa_categoria_etichetta(s):
    return _C.get(s.get("categoria", ""), "🖥️ Sistemi elettronici")


def aa_cerca(q="", categoria="", colore="", mezzo="", ev=None, voci=None):
    """Le spie del catalogo che corrispondono: per nome, simbolo (aspetto), categoria, descrizione e cause."""
    aa_prepara()
    voci = voci if voci is not None else _AE_SPIE
    parole = [p for p in (q or "").lower().split() if p]
    ris = []
    for s in voci:
        if categoria and s.get("categoria") != categoria.split(" ", 1)[-1]:
            continue
        if colore and s["colore"] not in colore:
            continue
        if s["tipo"] == "hv" and ev is False:
            continue
        if s["tipo"] == "termico" and ev is True:
            continue
        if mezzo == "pesanti" and s.get("solo") and "camion" not in s["solo"] and "autobus" not in s["solo"] and "trattori" not in s["solo"] and "agricoli" not in s["solo"]:
            continue
        testo = " ".join([s["nome"], s["significato"], " ".join(s["cause"]), s.get("aspetto", ""), s.get("categoria", ""), s.get("solo", "")]).lower()
        if parole and not all(p in testo for p in parole):
            continue
        ris.append(s)
    return ris


def aa_pagina(v=None):
    """Archivio delle spie: categorie, ricerca per nome / simbolo / descrizione, colore. Funziona senza IA e senza internet esterno."""
    aa_prepara()
    ev = None if not v else str(v.get("alimentazione", "")).startswith("Elettrica")        # None = nessun veicolo scelto: si vedono tutte
    st.markdown("<div style='background:#fff3e0;border-left:6px solid #e65100;padding:8px 12px;border-radius:10px;margin:6px 0'>🚦 <b>Come si leggono:</b> 🔴 rosso = <b>fermati subito</b> · 🟡 giallo/arancio = <b>avviso, officina a breve</b> · 🟢🔵 verde/blu = <b>informazione</b>. Il colore da solo non basta: conta anche il simbolo e il tuo veicolo.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2], gap="small")
    q = c1.text_input("🔍 Cerca per nome, simbolo o descrizione", key="aa_q", placeholder="olio, freni, triangolo, goccia, AdBlue…", label_visibility="collapsed")
    col_s = c2.selectbox("Colore", ["Tutti i colori", "🔴 Rosse", "🟡 Gialle", "🟢 Verdi e 🔵 blu"], key="aa_col", label_visibility="collapsed")
    cat = st.selectbox("Categoria", ["Tutte le categorie"] + AA_CATEGORIE, key="aa_cat", label_visibility="collapsed")
    mezzo_s = st.selectbox("Mezzo", ["Tutti i mezzi", "Camion, autobus e mezzi agricoli"], key="aa_mezzo", label_visibility="collapsed")
    colore = {"🔴 Rosse": ("rosso",), "🟡 Gialle": ("giallo",), "🟢 Verdi e 🔵 blu": ("verde", "blu")}.get(col_s, ())
    elenco = aa_cerca(q, "" if cat.startswith("Tutte") else cat, colore, "pesanti" if mezzo_s.startswith("Camion") else "", ev)
    st.caption(f"{len(elenco)} spie su {len(_AE_SPIE)} nel catalogo (dentro il programma: nessun servizio esterno).")
    if not elenco:
        st.info("Nessuna spia corrisponde qui. Prova un'altra parola, oppure cerca nella **base condivisa** qui sotto: contiene anche le spie trovate dagli altri.")
    for s in sorted(elenco, key=lambda x: (_AE_ORDINE[x["colore"]], x.get("categoria", ""), x["nome"])):
        ic, col, bg = _AE_COL[s["colore"]]
        with st.expander(f"{ic} {s['icona']} {s['nome']}"):
            if s["colore"] == "rosso":
                st.markdown(f"<div style='background:{bg};border:2px solid {col};border-radius:12px;padding:10px 12px;color:{col};font-weight:900'>⚠️ PERICOLO — {_h_aa.escape(s['urgenza'])}. Non continuare a guidare se non puoi escludere un rischio.</div>", unsafe_allow_html=True)
            st.markdown(f"**Categoria:** {aa_categoria_etichetta(s)}  \n**Colore:** {s['colore'].capitalize()} · **Urgenza:** {s['urgenza']}"
                        + (f"  \n**Come è fatto il simbolo:** {s['aspetto']}" if s.get("aspetto") else "") + (f"  \n**Per:** {s['solo']}" if s.get("solo") else ""))
            st.markdown("**Significato:** " + s["significato"])
            st.markdown("**Cosa fare subito**\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(s["azioni"], 1)))
            if s["cause"]:
                st.markdown("**Possibili cause:** " + ", ".join(s["cause"]) + ".")
    st.caption("Per il tuo veicolo vale sempre il manuale. Se la spia è rossa o hai dubbi sulla sicurezza: fermati in un posto sicuro.")


aa_prepara()
