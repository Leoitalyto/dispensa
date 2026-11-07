# -*- coding: utf-8 -*-
"""DIAGNOSTICA · CODICI DI ERRORE (DTC) — «Leggi codici errore».

• Database LOCALE: dtc_obdex.json.gz = OBDex (https://github.com/foerbsnavi/OBDex), 9.533 codici GENERICI SAE J2012 (P0, P2, P3, U0, U3, B0, C0). Dati CC0 (pubblico dominio, nessun obbligo di citazione; lo cito comunque), codice MIT.
  Funziona senza internet esterno e senza IA. Testi in inglese: per i codici più comuni (circa 200) ho scritto io spiegazioni in ITALIANO SEMPLICE (DTC_IT); per gli altri c'è «Traduci con l'IA» (facoltativa), con memoria condivisa fra gli utenti.
• Codici specifici del COSTRUTTORE (P1xxx, B1xxx, C1xxx, U1xxx…): nessun database gratuito completo (sono dati proprietari). L'app lo dice chiaramente: si può chiedere all'IA (con marca e modello) oppure usare le note condivise degli altri utenti. Mai presentati come certi.
• Mezzi pesanti (SAE J1939): si possono scrivere SPN e FMI. Spiego il modo di guasto (FMI, che è standard); il nome dello SPN dipende dalla norma (a pagamento) e dal costruttore: si cerca nel manuale o si annota nella base condivisa.
• I codici si leggono con un qualsiasi lettore (anche un'app gratuita) e si scrivono o incollano qui; oppure con il dongle Bluetooth (diagnostica_ble.py). Il programma NON cancella mai i codici.
• Ogni lettura si può salvare nello storico del veicolo (collezione «letture»).
Caricato dopo diagnostica_spie.py."""
import gzip
import json
import os
import re
import uuid
from datetime import datetime

import streamlit as st

DTC_PERCORSO_NOTE = "conoscenza/dtc.json"
_DTC_RE = re.compile(r"(?<![A-Za-z0-9])([PBCUpbcu][0-3][0-9A-Fa-f]{3})(?![A-Za-z0-9])")
_J1939_RE = re.compile(r"SPN\s*[:=]?\s*(\d{1,6})(?:\s*[,;/:\-]\s*|\s+FMI\s*[:=]?\s*|\s+)(?:FMI\s*[:=]?\s*)?(\d{1,2})(?!\d)", re.I)

DTC_SISTEMA = {"P": "Motore e trasmissione", "B": "Carrozzeria e comfort (airbag, clima, porte)", "C": "Telaio (freni, sterzo, sospensioni)", "U": "Comunicazione fra le centraline"}
_CAT_IT = {"p": "Motore e trasmissione", "b": "Carrozzeria e comfort (airbag, clima, porte)", "c": "Telaio (freni, sterzo, sospensioni)", "n": "Comunicazione fra le centraline"}
_PROB = {"h": "molto probabile", "m": "probabile", "l": "meno probabile", "": ""}
_DIFF = {"f": "facile (anche da soli, con attenzione)", "m": "media", "d": "difficile", "o": "solo in officina", "": ""}

DTC_GRAVITA = {
    "rosso": ("🔴", "Fermati in sicurezza e spegni il motore. Non proseguire finché non è stato controllato."),
    "giallo": ("🟡", "Fai controllare a breve. Se la guida è normale puoi raggiungere l'officina con prudenza, senza sforzare il mezzo; se noti anomalie (strappi, fumo, rumori, altre spie) fermati in sicurezza."),
    "verde": ("🟢", "Poco urgente: fai controllare alla prima occasione."),
    "": ("⚪", "Gravità non classificata: se non sei sicuro, fai controllare in officina prima di fare molta strada."),
}

# ---------------------------------------------------------------------------------------------------------------------
# spiegazioni in ITALIANO SEMPLICE per i codici più comuni
# ---------------------------------------------------------------------------------------------------------------------
DTC_IT = {}


def _d(codici, titolo, sig, controlli, g="giallo"):
    for c in ([codici] if isinstance(codici, str) else codici):
        DTC_IT[c] = {"t": titolo, "s": sig, "c": controlli, "g": g}


def _dtc_costruisci():
    """Riempie DTC_IT. È dentro una funzione perché tutti i moduli condividono lo stesso spazio dei nomi: le variabili dei cicli non devono sovrascrivere quelle dell'app."""
    # mancate accensioni, bobine, iniettori, candelette
    _d("P0300", "Mancate accensioni in più cilindri (casuali)", "Il motore salta alcune accensioni, in cilindri diversi: senti strappi o vibrazioni. Se la spia motore LAMPEGGIA è grave: fermati, perché il catalizzatore si può rovinare.",
       ["Candele e bobine", "Perdite d'aria (tubi, guarnizioni)", "Qualità del carburante", "Iniettori"])
    for n in range(1, 13):
        _d(f"P03{n:02d}", f"Mancate accensioni nel cilindro {n}", f"Il cilindro {n} salta delle accensioni: vibrazioni e strappi. Se la spia motore lampeggia fermati: il catalizzatore si può rovinare.",
           [f"Candela e bobina del cilindro {n} (si prova a scambiarle con un altro cilindro)", f"Iniettore del cilindro {n}", "Compressione (valvole, fasce)"])
    for n in range(1, 13):
        _d(f"P03{50 + n:02d}" if n <= 9 else f"P03{60 + n - 10:02d}", f"Bobina d'accensione, cilindro {n}: circuito", f"Il circuito della bobina del cilindro {n} non risponde: il cilindro può non accendersi.",
           ["Connettore e cablaggio della bobina", "Bobina difettosa", "Candela"])
    for n in range(1, 13):
        _d(f"P02{n:02d}", f"Iniettore del cilindro {n}: circuito", f"Il circuito dell'iniettore del cilindro {n} è guasto: il cilindro può funzionare male o non funzionare.", ["Connettore", "Iniettore", "Cablaggio e centralina"])
    for n in range(1, 7):
        _d(f"P067{n}", f"Candeletta cilindro {n}: circuito", f"La candeletta del cilindro {n} non funziona: il motore diesel può partire male a freddo.", ["Candeletta", "Connettore", "Relè e centralina delle candelette"])
    # sonde lambda
    for (b, s, base) in ((1, 1, 130), (1, 2, 136), (1, 3, 142), (2, 1, 150), (2, 2, 156), (2, 3, 162)):
        guasti = ["circuito non funzionante", "tensione bassa (segnale troppo povero)", "tensione alta (segnale troppo ricco)", "risposta lenta", "nessuna attività", "riscaldatore guasto"]
        for i, gu in enumerate(guasti):
            c = f"P0{base + i:03d}"
            pos = "a monte del catalizzatore" if s == 1 else ("a valle del catalizzatore" if s == 2 else "terza")
            _d(c, f"Sonda lambda bancata {b} sensore {s} ({pos}): {gu}", "La sonda che misura l'ossigeno nei gas di scarico non lavora bene: il motore può consumare di più e inquinare, e la spia motore resta accesa.",
               ["Fusibile e riscaldatore della sonda" if i == 5 else "Connettore e cablaggio della sonda", "Sonda vecchia o sporca", "Perdite nello scarico vicino alla sonda"], "giallo")
    # sensori e miscela
    _d("P0016", "Distribuzione sfasata (albero motore e albero a camme)", "I due alberi non sono in fase: può dipendere da catena o cinghia di distribuzione allungata o da un sensore. Se ignorato il motore si può danneggiare.", ["Livello e stato dell'olio", "Sensori dell'albero motore e delle camme", "Catena o cinghia di distribuzione"])
    _d("P0087", "Pressione del carburante nel rail troppo bassa", "Il motore non riceve abbastanza carburante a pressione: può perdere potenza o spegnersi.", ["Filtro del carburante", "Livello carburante", "Pompa e regolatore di pressione"])
    _d("P0088", "Pressione del carburante nel rail troppo alta", "La pressione nel circuito del carburante è troppo alta: può andare in modalità di emergenza.", ["Regolatore di pressione", "Sensore di pressione del rail", "Valvola di sfogo"])
    _d(["P0100", "P0101", "P0102", "P0103", "P0104"], "Debimetro (misuratore dell'aria) non regolare", "Il sensore che misura l'aria aspirata dà valori sbagliati: il motore può andare a scatti, consumare di più o perdere potenza.", ["Filtro e tubi dell'aria", "Connettore e sensore (pulizia con prodotto adatto)", "Perdite d'aria dopo il debimetro"])
    _d(["P0105", "P0106", "P0107", "P0108", "P0109"], "Sensore di pressione del collettore (MAP) non regolare", "Il sensore che misura la pressione dell'aria in ingresso dà valori sbagliati.", ["Tubo del vuoto e sensore", "Connettore", "Perdite d'aria"])
    _d(["P0110", "P0111", "P0112", "P0113", "P0114"], "Sensore temperatura aria aspirata non regolare", "Il sensore della temperatura dell'aria in ingresso dà valori sbagliati: di solito la guida resta normale.", ["Connettore", "Sensore"], "verde")
    _d(["P0115", "P0116", "P0117", "P0118", "P0119"], "Sensore temperatura del liquido di raffreddamento non regolare", "Se il sensore sbaglia, la ventola può non partire e il motore può scaldare troppo: controlla l'indicatore di temperatura.", ["Connettore", "Sensore", "Livello del liquido", "Termostato e ventola"])
    _d(["P0120", "P0121", "P0122", "P0123", "P0124"], "Sensore della farfalla o del pedale (A) non regolare", "Il sistema dell'acceleratore ha un'anomalia: il motore può avere meno potenza (modalità di emergenza).", ["Connettore e cablaggio", "Sensore del pedale o corpo farfallato", "Pulizia della farfalla"])
    _d("P0125", "Motore troppo lento a scaldarsi per la gestione della miscela", "Il motore non raggiunge subito la temperatura giusta: di solito dipende dal termostato.", ["Termostato", "Sensore di temperatura"], "verde")
    _d("P0128", "Termostato: temperatura sotto il valore normale", "Il motore sembra restare freddo: di solito il termostato rimane aperto. Consumi un po' più alti.", ["Termostato", "Sensore di temperatura"], "verde")
    _d(["P0171", "P0174"], "Miscela troppo magra (poca benzina o troppa aria)", "Il motore riceve troppa aria rispetto al carburante: può andare a scatti o al minimo irregolare.", ["Perdite d'aria (tubi, guarnizioni, vuoto)", "Debimetro sporco", "Pressione del carburante", "Sonda lambda"])
    _d(["P0172", "P0175"], "Miscela troppo ricca (troppo carburante)", "Il motore riceve troppo carburante rispetto all'aria: consumi alti e fumo nero.", ["Iniettori che gocciolano", "Debimetro", "Sonda lambda", "Filtro dell'aria"])
    _d(["P0190", "P0191", "P0192", "P0193", "P0194"], "Sensore pressione carburante del rail non regolare", "Il sensore che misura la pressione del carburante dà valori sbagliati.", ["Connettore", "Sensore", "Pompa"])
    _d("P0217", "Motore surriscaldato", "Il motore è troppo caldo. Se l'indicatore di temperatura è alto: FERMATI subito, spegni e lascia raffreddare. Non aprire il tappo a caldo.", ["Livello del liquido", "Ventola e termostato", "Pompa dell'acqua", "Radiatore"], "rosso")
    _d("P0234", "Pressione del turbo troppo alta", "Il turbo spinge più del previsto: la potenza viene limitata per proteggere il motore.", ["Valvola wastegate / geometria variabile", "Sensore di pressione", "Tubi del turbo"])
    _d(["P0235", "P0236", "P0237", "P0238"], "Sensore pressione del turbo non regolare", "Il sensore della pressione del turbo dà valori sbagliati.", ["Connettore e sensore", "Tubi dell'aria"])
    _d("P0299", "Pressione del turbo troppo bassa", "Il turbo spinge meno del previsto: poca potenza, a volte fumo.", ["Tubi e fascette dell'aria", "Turbocompressore", "Valvola wastegate", "Intercooler con perdite"])
    _d(["P0325", "P0326", "P0327", "P0328", "P0329", "P0330", "P0331", "P0332", "P0333", "P0334"], "Sensore di detonazione (battito in testa)", "Il sensore che «sente» i battiti anomali del motore non funziona o segnala detonazioni: usa benzina di qualità e fai controllare.", ["Connettore e cablaggio", "Sensore", "Carburante di scarsa qualità"])
    _d(["P0335", "P0336", "P0337", "P0338", "P0339"], "Sensore albero motore non regolare", "Il sensore che dice alla centralina il regime del motore ha un problema: il motore può spegnersi o non partire.", ["Connettore e cablaggio", "Sensore", "Anello fonico"])
    _d(["P0340", "P0341", "P0342", "P0343", "P0344"], "Sensore albero a camme non regolare", "Il sensore delle camme dà un segnale sbagliato: avviamento difficile o motore in modalità di emergenza.", ["Connettore e cablaggio", "Sensore", "Distribuzione"])
    _d("P0380", "Circuito candelette (A)", "Il circuito delle candelette ha un guasto: il diesel può partire male a freddo.", ["Relè e fusibile", "Candelette", "Cablaggio"])
    _d("P0381", "Spia delle candelette: circuito", "La spia delle candelette non funziona correttamente.", ["Lampadina del quadro", "Cablaggio"], "verde")
    _d(["P0400", "P0401", "P0402", "P0403", "P0404", "P0405", "P0406", "P0407", "P0408", "P0409"], "Valvola EGR (ricircolo dei gas) non regolare", "La valvola che rimanda parte dei gas di scarico al motore è sporca, bloccata o ha un sensore errato: il motore può andare a scatti, consumare di più e inquinare.", ["Valvola EGR sporca o bloccata (nei diesel: fuliggine)", "Tubi e sensori", "Collettore intasato"])
    _d("P0411", "Sistema aria secondaria: flusso errato", "Il sistema che immette aria nello scarico per ridurre le emissioni non funziona bene.", ["Pompa dell'aria", "Valvole", "Tubi"], "verde")
    _d("P0420", "Catalizzatore: efficienza sotto la soglia (bancata 1)", "Il catalizzatore (o le sonde lambda) non pulisce abbastanza i gas di scarico. Spesso la guida resta normale, ma si può fallire la revisione.", ["Sonde lambda a monte e a valle", "Perdite nello scarico", "Catalizzatore invecchiato", "Mancate accensioni"])
    _d("P0430", "Catalizzatore: efficienza sotto la soglia (bancata 2)", "Come P0420 ma sull'altra fila di cilindri.", ["Sonde lambda", "Perdite nello scarico", "Catalizzatore invecchiato"])
    for c, t in (("P0440", "Sistema vapori di carburante (EVAP): guasto"), ("P0441", "EVAP: flusso di spurgo errato"), ("P0442", "EVAP: piccola perdita"), ("P0443", "Valvola di spurgo EVAP: circuito"), ("P0446", "Ventilazione EVAP: circuito"),
                 ("P0455", "EVAP: perdita grande (controlla il tappo)"), ("P0456", "EVAP: perdita molto piccola"), ("P0457", "EVAP: tappo del serbatoio non chiuso o perdita")):
        _d(c, t, "Il sistema che trattiene i vapori di benzina ha una perdita o una valvola che non funziona. Non è pericoloso per la marcia, ma la spia resta accesa.",
           ["Chiudi bene il tappo del serbatoio e guarda se la spia si spegne dopo qualche giorno", "Guarnizione del tappo", "Tubi e valvola EVAP"], "verde")
    _d(["P0480", "P0481"], "Ventola di raffreddamento: circuito", "La ventola del radiatore non si comanda bene: in coda o in estate il motore può scaldare.", ["Fusibile e relè", "Motore della ventola", "Cablaggio"])
    _d("P0500", "Sensore velocità del veicolo", "Il segnale di velocità manca: possono non funzionare tachimetro, cruise control e ABS.", ["Sensore e connettore", "Anello fonico", "Cablaggio"])
    _d(["P0505", "P0506", "P0507", "P0508", "P0509"], "Regolazione del minimo non regolare", "Il minimo del motore è irregolare, troppo basso o troppo alto.", ["Farfalla sporca", "Perdite d'aria", "Valvola del minimo"])
    _d(["P0520", "P0521", "P0522", "P0523"], "Sensore pressione olio: segnale non regolare", "Il sensore (o il suo circuito) dà valori sbagliati. Se la SPIA dell'olio è accesa, fermati: potrebbe mancare olio vero.", ["Livello olio (controlla subito)", "Sensore e connettore", "Cablaggio"])
    _d("P0524", "Pressione olio motore troppo bassa", "L'olio non ha la pressione giusta: il motore si può rovinare in pochi minuti. Non proseguire.", ["Livello olio", "Pompa dell'olio", "Sensore", "Perdite"], "rosso")
    _d("P0562", "Tensione del sistema troppo bassa", "La tensione di bordo è bassa: batteria debole o alternatore che non carica.", ["Batteria", "Alternatore", "Cavi e masse"])
    _d("P0563", "Tensione del sistema troppo alta", "La tensione di bordo è troppo alta: il regolatore dell'alternatore potrebbe essere guasto.", ["Alternatore e regolatore", "Batteria"])
    _d(["P0571", "P0572", "P0573"], "Interruttore del freno (luci stop): circuito", "L'interruttore sul pedale del freno non dà il segnale giusto: le luci stop potrebbero non accendersi. Controlla subito che le luci stop funzionino.", ["Interruttore sul pedale del freno", "Fusibile e lampade delle luci stop", "Cablaggio"])
    _d(["P0600", "P0601", "P0602", "P0603", "P0604", "P0605", "P0606"], "Centralina del motore: comunicazione o memoria", "La centralina ha un problema interno o di comunicazione.", ["Alimentazione e masse", "Connettori", "Aggiornamento software", "Centralina"])
    _d(["P0620", "P0621", "P0622"], "Alternatore: circuito di controllo", "Il comando dell'alternatore ha un guasto: la batteria può non caricarsi.", ["Cablaggio", "Alternatore", "Batteria"])
    _d("P0627", "Pompa carburante: circuito di controllo", "Il comando della pompa del carburante ha un problema: il motore può spegnersi o non partire.", ["Relè e fusibile della pompa", "Pompa", "Cablaggio"])
    _d(["P0641", "P0651"], "Tensione di alimentazione dei sensori fuori limite", "L'alimentazione a 5 volt dei sensori non è corretta: più sensori possono dare errori insieme.", ["Cablaggio e masse", "Un sensore in corto", "Centralina"])
    _d("P0700", "Sistema di controllo del cambio: guasto", "La centralina del cambio ha registrato un guasto. Questo codice dice solo «guarda i codici del cambio»: serve una lettura dedicata.", ["Leggere i codici dalla centralina del cambio", "Livello e stato dell'olio del cambio"])
    _d(["P0715", "P0716", "P0717"], "Sensore velocità d'ingresso del cambio", "Il cambio non legge la velocità in ingresso: cambi marcia a scatti o in emergenza.", ["Sensore e connettore", "Olio del cambio"])
    _d(["P0720", "P0721", "P0722", "P0723"], "Sensore velocità d'uscita del cambio", "Il cambio non legge la velocità in uscita: cambi marcia a scatti e tachimetro errato.", ["Sensore e connettore", "Olio del cambio"])
    _d("P0730", "Rapporto delle marce errato", "Il cambio non inserisce la marcia come richiesto: scivolamenti o strappi.", ["Livello e stato dell'olio del cambio", "Elettrovalvole", "Frizioni interne"])
    _d(["P0740", "P0741", "P0742", "P0743", "P0744"], "Convertitore di coppia / frizione di blocco", "Il blocco del convertitore non funziona bene: vibrazioni o consumi alti.", ["Olio del cambio", "Elettrovalvola", "Convertitore"])
    _d(["P0750", "P0755", "P0760", "P0765", "P0770"], "Elettrovalvola del cambio", "Un'elettrovalvola del cambio automatico non funziona: marce mancanti o cambi bruschi.", ["Olio del cambio", "Connettore e cablaggio", "Elettrovalvola"])
    # filtro antiparticolato, SCR
    _d("P2002", "Filtro antiparticolato: efficienza sotto la soglia", "Il filtro dei fumi dei diesel è pieno o danneggiato.", ["Rigenerazione (guida a velocità costante)", "Sensore di pressione differenziale", "Filtro"])
    _d(["P2452", "P2453", "P2454", "P2455"], "Sensore pressione differenziale del filtro antiparticolato", "Il sensore che misura quanto è pieno il filtro dà valori sbagliati.", ["Tubicini del sensore", "Sensore", "Connettore"])
    _d("P2458", "Rigenerazione del filtro antiparticolato troppo lunga", "La pulizia del filtro non si completa.", ["Percorsi più lunghi a velocità costante", "Sensori di temperatura", "Iniettore del post-iniezione"])
    _d("P2463", "Troppa fuliggine nel filtro antiparticolato", "Il filtro è molto pieno: rischia di intasarsi.", ["Rigenerazione forzata in officina", "Iniettori", "Valvola EGR"])
    _d("P20EE", "Catalizzatore SCR (AdBlue): efficienza sotto la soglia", "Il sistema AdBlue non riduce abbastanza gli ossidi di azoto. Può partire un conto alla rovescia dopo il quale l'auto non riparte.", ["Qualità e livello dell'AdBlue", "Iniettore e pompa dell'AdBlue", "Sensori NOx", "Catalizzatore SCR"])
    # comunicazione
    _d("U0001", "Comunicazione CAN ad alta velocità: guasto", "La rete interna che fa parlare le centraline ha un problema: più spie possono accendersi insieme.", ["Cablaggio e connettori della rete CAN", "Una centralina difettosa", "Batteria debole"])
    _d("U0100", "Comunicazione persa con la centralina motore", "Le altre centraline non riescono a parlare con quella del motore: può non partire o andare in emergenza.", ["Alimentazione e masse della centralina motore", "Rete CAN", "Batteria"])
    _d("U0101", "Comunicazione persa con la centralina del cambio", "Le centraline non parlano con quella del cambio.", ["Rete CAN", "Alimentazione del cambio", "Centralina cambio"])
    _d("U0121", "Comunicazione persa con la centralina ABS", "Le centraline non parlano con quella dell'ABS/ESP: ABS ed ESP possono non funzionare.", ["Rete CAN", "Alimentazione dell'ABS", "Centralina ABS"])
    _d("U0140", "Comunicazione persa con la centralina della carrozzeria (BCM)", "Luci, chiusura e altre funzioni di comfort possono funzionare male.", ["Alimentazione e masse", "Rete CAN", "BCM"])
    _d("U0155", "Comunicazione persa con il quadro strumenti", "Il cruscotto non riceve i dati: spie e indicatori possono essere sbagliati.", ["Cablaggio del quadro", "Rete CAN", "Quadro strumenti"])
    # telaio
    for c, ruota in (("C0035", "anteriore sinistra"), ("C0040", "anteriore destra"), ("C0045", "posteriore sinistra"), ("C0050", "posteriore destra")):
        _d(c, f"Sensore velocità ruota {ruota}", "Un sensore delle ruote non dà il segnale: ABS ed ESP possono non funzionare. La frenata normale resta, ma senza aiuto antibloccaggio e con distanze maggiori.", ["Sensore e cavo", "Anello fonico sporco o danneggiato", "Cuscinetto della ruota"])
    _d("C0110", "Pompa dell'ABS: motorino", "Il motorino della pompa dell'ABS ha un problema: ABS ed ESP possono non funzionare.", ["Fusibile e relè", "Pompa/gruppo ABS"])
    _d("C0265", "Relè dell'ABS (centralina frenata)", "Il relè della centralina dell'ABS non funziona: ABS ed ESP fuori servizio.", ["Fusibile e relè", "Centralina ABS"])
    _d("B0001", "Airbag guidatore: circuito di attivazione", "L'airbag del volante potrebbe non aprirsi in caso di urto. È un problema di sicurezza: non toccare connettori e cavi dell'airbag.", ["Solo in officina: connettore sotto il volante, spirale (clockspring), airbag"], "giallo")


_dtc_costruisci()


# ---------------------------------------------------------------------------------------------------------------------
# i componenti in italiano (i più frequenti)
# ---------------------------------------------------------------------------------------------------------------------
DTC_COMP = {
    "wiring_harness": "cablaggio", "engine_control_module": "centralina motore", "sensor_wiring": "cablaggio del sensore", "ecm": "centralina motore", "bms": "gestione batteria (BMS)", "hybrid_control_module": "centralina ibrido",
    "transmission_control_module": "centralina cambio", "tcm": "centralina cambio", "vehicle_bus_wiring": "cablaggio della rete interna", "on_board_charger": "caricatore di bordo", "can_bus_wiring": "cablaggio rete CAN", "oxygen_sensor_wiring": "cablaggio sonda lambda",
    "fuel_injector": "iniettore", "injector_wiring": "cablaggio iniettore", "transmission_valve_body": "gruppo valvole del cambio", "srs_control_module": "centralina airbag", "crankshaft_position_sensor": "sensore albero motore", "actuator_wiring": "cablaggio attuatore",
    "afcm": "centralina pompa carburante", "body_control_module": "centralina carrozzeria (BCM)", "control_module": "centralina", "engine_oil": "olio motore", "can_bus": "rete CAN", "abs_control_module": "centralina ABS", "nox_sensor": "sensore NOx",
    "ignition_wiring": "cablaggio accensione", "dcdc_converter": "convertitore DC/DC", "glow_plug_control_module": "centralina candelette", "transmission_clutches": "frizioni del cambio", "inverter": "inverter", "squib_circuit": "circuito di innesco airbag",
    "glow_plug": "candeletta", "valve_body": "gruppo valvole", "transmission_fluid": "olio del cambio", "ac_compressor_module": "compressore clima", "high_pressure_fuel_pump": "pompa carburante alta pressione", "catalytic_converter": "catalizzatore",
    "shift_solenoid": "elettrovalvola del cambio", "mass_air_flow_sensor": "debimetro", "hvac_control_module": "centralina clima", "fuel_injectors": "iniettori", "fuel_pressure_regulator": "regolatore pressione carburante", "instrument_cluster": "quadro strumenti",
    "intake_manifold": "collettore di aspirazione", "module_connector": "connettore della centralina", "srs_wiring": "cablaggio airbag", "ignition_coil": "bobina d'accensione", "electronic_range_selector": "selettore del cambio elettronico",
    "oxygen_sensor_heater": "riscaldatore sonda lambda", "throttle_position_sensor": "sensore farfalla", "exhaust_gas_temperature_sensor": "sensore temperatura gas di scarico", "oxygen_sensor_downstream": "sonda lambda a valle", "egr_valve": "valvola EGR",
    "reductant_pump": "pompa AdBlue", "oil_control_valve": "valvola controllo olio", "hv_battery": "batteria alta tensione", "brake_control_module": "centralina freni", "communication_bus": "rete di comunicazione", "battery": "batteria", "injection_pump": "pompa di iniezione",
    "ignition_module": "modulo d'accensione", "fuel_rail": "rail del carburante", "oxygen_sensor_bank1_sensor1": "sonda lambda bancata 1 sensore 1", "accelerator_pedal_position_sensor": "sensore del pedale", "alternator": "alternatore",
    "exhaust_system": "impianto di scarico", "oxygen_sensor_bank2_sensor1": "sonda lambda bancata 2 sensore 1", "throttle_body": "corpo farfallato", "manifold_absolute_pressure_sensor": "sensore pressione collettore (MAP)", "reductant_injection_valve": "iniettore AdBlue",
    "oxygen_sensor_upstream": "sonda lambda a monte", "nox_sensor_wiring": "cablaggio sensore NOx", "solenoid": "elettrovalvola", "barometric_pressure_sensor": "sensore pressione atmosferica", "oxygen_sensor_bank1_sensor2": "sonda lambda bancata 1 sensore 2",
    "oxygen_sensor_bank2_sensor2": "sonda lambda bancata 2 sensore 2", "electronic_throttle_body": "farfalla elettronica", "knock_sensor_wiring": "cablaggio sensore detonazione", "turbocharger": "turbocompressore", "clockspring": "spirale del volante (clockspring)",
    "steering_angle_sensor": "sensore angolo di sterzo", "fuse": "fusibile", "tone_ring": "anello fonico", "engine_coolant_temperature_sensor": "sensore temperatura liquido", "cooling_system": "impianto di raffreddamento", "evap_purge_valve": "valvola di spurgo EVAP",
    "abs_hydraulic_unit": "gruppo idraulico ABS", "brake_system_control_module": "centralina impianto frenante", "scr_catalyst": "catalizzatore SCR", "fuel_pump": "pompa carburante", "epb_control_module": "centralina freno di stazionamento",
    "reductant_level_sensor": "sensore livello AdBlue", "oxygen_sensor": "sonda lambda", "charge_port": "presa di ricarica", "glow_plug_wiring": "cablaggio candelette",
}


def dtc_comp_it(idc):
    if idc in DTC_COMP:
        return DTC_COMP[idc]
    m = re.fullmatch(r"fuel_injector_cylinder_(\d+)", idc)
    return f"iniettore cilindro {m.group(1)}" if m else ""


# ---------------------------------------------------------------------------------------------------------------------
# il database locale
# ---------------------------------------------------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _dtc_carica(percorso, mtime):
    with gzip.open(percorso, "rt", encoding="utf-8") as f:
        righe = json.load(f)
    return {r[0]: r for r in righe}


def dtc_db():
    """{codice: riga} oppure {} se il file non c'è (l'app lo dice)."""
    cartella = globals().get("_cartella") or "."
    p = os.path.join(cartella, "dtc_obdex.json.gz")
    try:
        return _dtc_carica(p, os.path.getmtime(p))
    except Exception:
        return {}


def dtc_estrai(testo):
    """I codici scritti o incollati (P0420, p0420, P0420-00…), senza doppioni e in ordine; più gli SPN/FMI dei mezzi pesanti."""
    visti, ris = set(), []
    for m in _DTC_RE.finditer(str(testo or "")):
        c = m.group(1).upper()
        if c not in visti:
            visti.add(c)
            ris.append({"codice": c, "tipo": "obd"})
    for m in _J1939_RE.finditer(str(testo or "")):
        c = f"SPN {int(m.group(1))} FMI {int(m.group(2))}"
        if c not in visti and 0 <= int(m.group(2)) <= 31:
            visti.add(c)
            ris.append({"codice": c, "tipo": "j1939", "spn": int(m.group(1)), "fmi": int(m.group(2))})
    return ris


DTC_FMI = {0: "Valore valido ma molto sopra il normale (livello molto alto)", 1: "Valore valido ma molto sotto il normale (livello molto basso)", 2: "Dati intermittenti, irregolari o errati", 3: "Tensione troppo alta o corto circuito verso positivo",
           4: "Tensione troppo bassa o corto circuito verso massa", 5: "Corrente troppo bassa o circuito aperto (filo interrotto)", 6: "Corrente troppo alta o corto circuito verso massa", 7: "Il componente meccanico non risponde o è fuori regolazione",
           8: "Frequenza o durata dell'impulso anomala", 9: "Frequenza di aggiornamento dei dati anomala", 10: "Variazione troppo rapida del valore", 11: "Causa di guasto non identificata", 12: "Componente o centralina guasti",
           13: "Valore fuori taratura", 14: "Istruzioni speciali del costruttore", 15: "Valore sopra il normale (livello poco alto)", 16: "Valore sopra il normale (livello moderatamente alto)", 17: "Valore sotto il normale (livello poco basso)",
           18: "Valore sotto il normale (livello moderatamente basso)", 19: "Errore nei dati ricevuti dalla rete", 20: "Deriva del dato verso l'alto", 21: "Deriva del dato verso il basso", 31: "Condizione presente / non disponibile"}


def dtc_info(codice):
    """Tutto ciò che si sa di un codice OBD: {'stato': 'generico'|'costruttore'|'sconosciuto', 'it': curato o None, 'db': riga o None}."""
    c = str(codice).upper()
    db = dtc_db()
    r = db.get(c)
    it = DTC_IT.get(c)
    if r or it:
        return {"stato": "generico", "it": it, "db": r}
    # specifico del costruttore: P1xxx, B1xxx/B2xxx, C1xxx/C2xxx, U1xxx/U2xxx e le serie 3 riservate
    if len(c) == 5 and (c[1] in "123"):
        return {"stato": "costruttore", "it": None, "db": None}
    return {"stato": "sconosciuto", "it": None, "db": None}


def dtc_riepilogo(info):
    """(gravità, titolo in italiano se noto)."""
    if info["it"]:
        return info["it"]["g"], info["it"]["t"]
    r = info["db"]
    if r:
        return "", r[2]
    return "", ""


# ---------------------------------------------------------------------------------------------------------------------
# memoria condivisa: traduzioni e note dell'IA (solo testo)
# ---------------------------------------------------------------------------------------------------------------------
def dtc_note_leggi():
    try:
        d = carica_dati(crea_archivio(), DTC_PERCORSO_NOTE)
    except Exception:
        return {}
    return d or {}


def dtc_note_salva(chiave, valore):
    def _m(d):
        d.setdefault("ia", {})[chiave] = valore
    try:
        salva_file(DTC_PERCORSO_NOTE, _m, f"Codici: {chiave}")
        return True
    except Exception:
        return False


_SYS_TRAD = ("Sei un meccanico che spiega in italiano molto semplice, senza termini tecnici non spiegati. Ti do la scheda in inglese di un codice di errore OBD-II. "
             "Rispondi SOLO con un oggetto JSON (nessun testo fuori, nessun markdown): "
             '{"titolo": "...", "significato": "frase semplice di 1-2 righe", "cause": ["...", "..."], "controlli": ["...", "..."], "sintomi": ["..."]}. '
             "Non inventare: traduci e semplifica solo ciò che c'è nella scheda. Mai presentare un'ipotesi come una certezza.")
_SYS_COSTR = ("Sei un meccanico che spiega in italiano molto semplice, senza termini tecnici non spiegati. Ti do un codice di errore SPECIFICO DEL COSTRUTTORE e il mezzo. Questi codici cambiano da marca a marca: se non sei sicuro, dillo. "
              'Rispondi SOLO con JSON: {"titolo": "...", "significato": "...", "cause": ["..."], "controlli": ["..."], "certezza": "alta|media|bassa"}. Se non conosci il codice per quella marca usa certezza «bassa» e scrivilo nel significato. Non inventare.')


def _dtc_json(testo):
    if not testo:
        return None
    m = re.search(r"\{.*\}", testo, re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except Exception:
        return None
    return d if isinstance(d, dict) and d.get("titolo") else None


def dtc_ia(codice, info, mezzo=""):
    """Traduce (codice generico) o spiega (codice del costruttore) con l'IA scelta. Ritorna (dizionario, errore)."""
    if "ad_provider_scelto" not in globals() or not ad_attivo():
        return None, "assente"
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if cfg["fonte"] == "app" and not ad_puo():
        return None, "limite"
    if info["stato"] == "generico" and info["db"]:
        r = info["db"]
        scheda = f"Codice {codice}. Titolo: {r[2]}. Descrizione: {r[3]} Cause: " + "; ".join(c[0] for c in r[4]) + ". Sintomi: " + "; ".join(r[5])
        sys_, turno = _SYS_TRAD, scheda
    else:
        sys_, turno = _SYS_COSTR, f"Mezzo: {mezzo or 'non specificato'}. Codice: {codice}."
    testo, err = _ad_invia(prov, cfg, sys_, [("u", turno)], None, 900)
    if err:
        return None, err
    d = _dtc_json(testo)
    if not d:
        return None, "formato"
    d["fonte"] = "IA (" + AD_PROVIDER[prov]["nome"].split(" (")[0] + ")"
    d["data"] = datetime.now().strftime("%Y-%m-%d")
    return d, None


def dtc_prompt_libero(codice, info, mezzo=""):
    """Le istruzioni da incollare in una qualunque app di IA (senza chiavi): per tradurre/spiegare un codice."""
    if info["stato"] == "generico" and info["db"]:
        r = info["db"]
        return (f"Spiegami in italiano molto semplice questo codice di errore OBD-II, senza termini tecnici non spiegati. Mezzo: {mezzo or 'non specificato'}. Codice {codice}: {r[2]}. {r[3]} "
                f"Dimmi: cosa significa, possibili cause, cosa controllare e se posso continuare a guidare. Non presentare ipotesi come certezze.")
    return (f"Spiegami in italiano molto semplice il codice di errore {codice} per questo mezzo: {mezzo or 'non specificato'}. È un codice specifico del costruttore: se non lo conosci per questa marca dillo chiaramente. "
            f"Dimmi cosa significa, possibili cause, cosa controllare e se posso continuare a guidare. Non presentare ipotesi come certezze.")


# ---------------------------------------------------------------------------------------------------------------------
# la schermata
# ---------------------------------------------------------------------------------------------------------------------
def _dtc_carta(c, v, mezzo, chiave):
    codice = c["codice"]
    if c["tipo"] == "j1939":
        with st.expander(f"🚚 {codice} · {DTC_FMI.get(c['fmi'], 'modo di guasto')[:60]}"):
            st.markdown(f"**Modo di guasto (FMI {c['fmi']}):** {DTC_FMI.get(c['fmi'], 'non previsto')}")
            st.markdown(f"**SPN {c['spn']}:** il nome del componente per questo numero dipende dalla norma J1939 (a pagamento) e dal costruttore: cercalo nel **manuale d'officina** o nella scheda del costruttore. "
                        "Se lo trovi, puoi annotarlo nella base condivisa (Archivio spie).")
            st.caption("Il collegamento diretto J1939 da telefono non è supportato: qui si leggono i codici che ti ha dato un lettore o il cruscotto.")
        return
    info = dtc_info(codice)
    g, titolo = dtc_riepilogo(info)
    note = dtc_note_leggi().get("ia", {})
    ia = note.get(codice) or (note.get(f"{codice}|{(v or {}).get('marca', '').lower()}") if v else None)
    if not titolo and ia:
        titolo = ia.get("titolo", "")
    ic = DTC_GRAVITA.get(g, DTC_GRAVITA[""])[0]
    etichetta = {"generico": "", "costruttore": " · specifico del costruttore", "sconosciuto": " · non riconosciuto"}[info["stato"]]
    with st.expander(f"{ic} {codice} · {titolo or 'senza descrizione gratuita'}{etichetta}"):
        _ic, testo_g = DTC_GRAVITA.get(g, DTC_GRAVITA[""])
        if g == "rosso":
            st.markdown(f"<div style='background:#ffebee;border:2px solid #b71c1c;border-radius:12px;padding:10px 12px;color:#b71c1c;font-weight:900'>⚠️ PERICOLO — {testo_g}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"**{ic} Gravità:** {testo_g}")
        if codice[0] in "BC" and g != "rosso":
            st.caption("Codice che riguarda airbag, freni o sterzo: per la sicurezza non rimandare il controllo, e non toccare i cavi dell'airbag.")
        st.caption(f"Sistema: {DTC_SISTEMA.get(codice[0], '')}")
        if info["stato"] == "sconosciuto":
            st.warning("Non riconosco questo codice: controlla di averlo scritto bene (una lettera P, B, C o U e quattro cifre).")
        elif info["stato"] == "costruttore":
            st.warning("È un codice **specifico del costruttore**: non esiste un database gratuito completo e il significato cambia da marca a marca. Non lo presento come certo.")
        if info["it"]:
            i = info["it"]
            st.markdown("**Cosa significa:** " + i["s"])
            st.markdown("**Cosa controllare:** " + "; ".join(i["c"]) + ".")
        if info["db"]:
            r = info["db"]
            if not info["it"]:
                st.markdown(f"**Titolo (inglese):** {r[2]}")
            st.markdown("**📖 Dettagli dal database (in inglese)**")
            if r[3]:
                st.markdown("**Descrizione:** " + r[3])
            if r[4]:
                st.markdown("**Possibili cause:**\n" + "\n".join(f"- {x[0]}" + (f" _({_PROB.get(x[1], '')})_" if x[1] else "") for x in r[4]))
            if r[5]:
                st.markdown("**Sintomi:**\n" + "\n".join(f"- {x}" for x in r[5]))
            comp = [dtc_comp_it(x) for x in r[6]]
            comp = [x for x in comp if x]
            if comp:
                st.markdown("**Componenti coinvolti:** " + ", ".join(comp) + ".")
            extra = []
            if r[9]:
                extra.append("accende la spia motore")
            if r[10]:
                extra.append("può limitare la potenza (modalità di emergenza)")
            if r[7]:
                extra.append("riparazione: " + _DIFF[r[7]])
            if extra:
                st.caption("Per questo codice: " + " · ".join(extra) + ".")
            if r[11]:
                st.caption("Codici collegati: " + ", ".join(r[11]) + ".")
            st.caption("Fonte: OBDex (dati CC0, https://github.com/foerbsnavi/OBDex) · testi in inglese.")
        # IA: traduzione o spiegazione, con memoria condivisa
        if ia:
            st.markdown(f"**🇮🇹 Spiegazione dell'IA** _(non verificata: può contenere errori)_  \n**{ia.get('titolo', '')}** — {ia.get('significato', '')}")
            if ia.get("cause"):
                st.markdown("Possibili cause: " + ", ".join(ia["cause"]) + ".")
            if ia.get("controlli"):
                st.markdown("Cosa controllare: " + ", ".join(ia["controlli"]) + ".")
            st.caption(f"Fonte: {ia.get('fonte', 'IA')} · {ia.get('data', '')}" + (f" · certezza dichiarata: {ia['certezza']}" if ia.get("certezza") else ""))
        elif info["stato"] != "sconosciuto" and not info["it"]:
            if "ad_attivo" in globals() and ad_attivo():
                if st.button("🇮🇹 Spiega in italiano con l'IA" if info["stato"] == "generico" else "🤖 Chiedi all'IA (con marca e modello)", key=f"dtc_ia_{chiave}_{codice}", width="stretch"):
                    with st.spinner("Chiedo all'IA…"):
                        d, err = dtc_ia(codice, info, mezzo)
                    if d:
                        dtc_note_salva(codice if info["stato"] == "generico" else f"{codice}|{(v or {}).get('marca', '').lower()}", d)
                        st.rerun()
                    st.warning({"limite": "Limite di analisi raggiunto: riprova più tardi.", "chiave": "La chiave dell'IA non è valida.", "pagamento": "Questo modello è a pagamento: scegline uno «:free».",
                                "modello": "Questo modello non esiste più o non legge il testo: cambia modello."}.get(err, "L'IA non ha risposto. Riprova fra poco."))
            else:
                st.caption("Per l'italiano senza pagare: copia queste istruzioni nella tua app di IA (ChatGPT, Gemini, Claude…).")
                st.code(dtc_prompt_libero(codice, info, mezzo), language=None)
        if st.button("🤖 Chiedi all'assistente su questo codice", key=f"dtc_ass_{chiave}_{codice}", width="stretch"):
            st.session_state["dg_ass_codici"] = codice
            st.session_state["dg_vista"] = "assistente"
            st.rerun()


def dtc_pannello(v=None):
    """La schermata «Leggi codici errore»."""
    st.markdown("#### 🔢 Leggi codici errore")
    st.caption("Hai letto i codici con un lettore (anche un'app gratuita sul telefono, o l'officina)? **Scrivili o incollali qui**: te li spiego in italiano semplice, con la gravità e cosa controllare. "
               "Non serve nessun dispositivo e non serve l'IA.")
    db = dtc_db()
    if not db:
        st.warning("Il database dei codici (dtc_obdex.json.gz) non è nell'app: carica il file insieme agli altri. Intanto ti spiego i circa 200 codici più comuni scritti in italiano.")
    c1, c2 = st.columns(2, gap="small")
    origine = c1.selectbox("Dove li hai letti", ["Memorizzati", "In attesa", "Permanenti", "Non so"], key="dg_cod_orig")
    km = c2.text_input("Chilometri (facoltativo)", key="dg_cod_km", placeholder=str((v or {}).get("km_attuali", "") or "es. 125000"))
    testo = st.text_area("Codici (separati da spazio, virgola o a capo)", key="dg_cod_testo", height=90, placeholder="es. P0420, P0171\noppure, per camion: SPN 3226 FMI 4")
    sintomi = st.text_input("Cosa noti? (facoltativo)", key="dg_cod_sint", placeholder="es. strappi in accelerazione, poca potenza, fumo…")
    st.button("🔍 Spiega i codici", key="dg_cod_vai", type="primary", width="stretch")
    elenco = dtc_estrai(testo)
    mezzo = ""
    if "bd_scope" in globals():
        mezzo = bd_scope_desc(bd_scope(v), v)
    if not elenco:
        st.info("Scrivi un codice per iniziare (per esempio **P0420**). Le lettere sono P (motore e cambio), B (carrozzeria), C (telaio), U (comunicazione).")
    else:
        st.session_state["dg_ultimi_codici"] = [c["codice"] for c in elenco]
        st.markdown(f"**{len(elenco)} {'codice' if len(elenco) == 1 else 'codici'}** · letti: {origine.lower()}")
        for c in elenco:
            _dtc_carta(c, v, mezzo, "lettura")
        if v:
            if st.button("💾 Salva questa lettura nello storico del veicolo", key="dg_cod_salva", width="stretch"):
                voce = {"id": uuid.uuid4().hex[:8], "data": datetime.now().strftime("%Y-%m-%d %H:%M"), "fonte": "Codici inseriti a mano", "origine": origine, "km": km.strip(),
                        "codici": [{"codice": c["codice"], "titolo": (dtc_riepilogo(dtc_info(c["codice"]))[1] if c["tipo"] == "obd" else DTC_FMI.get(c.get("fmi"), ""))} for c in elenco],
                        "sintomi": sintomi.strip(), "stato": "Aperto", "intervento": "", "note": "", "files": []}
                _au_mod(v["id"], lambda x, vv=voce: x.setdefault("letture", []).append(vv), "Diagnostica: lettura codici")
                st.session_state["messaggio"] = "✅ Lettura salvata nello storico."
                st.rerun()
        else:
            st.caption("Per salvare la lettura nello storico scegli prima un veicolo.")
    st.divider()
    st.markdown("**🔎 Cerca un codice per parola** (inglese o italiano)")
    q = st.text_input("Cerca", key="dg_cod_cerca", placeholder="es. catalizzatore, oxygen, misfire, turbo…", label_visibility="collapsed").strip().lower()
    if q and db:
        trovati = []
        for codice, r in db.items():
            it = DTC_IT.get(codice)
            testo_r = (r[2] + " " + (it["t"] if it else "")).lower()
            if q in testo_r:
                trovati.append(codice)
        for codice, it in DTC_IT.items():
            if codice not in db and q in it["t"].lower():
                trovati.append(codice)
        st.caption(f"{len(trovati)} codici corrispondono" + (" (mostro i primi 15)" if len(trovati) > 15 else "") + ".")
        for codice in trovati[:15]:
            _dtc_carta({"codice": codice, "tipo": "obd"}, v, mezzo, "cerca")
    st.caption(f"Database locale: {len(db)} codici generici (OBDex, dati CC0). I codici specifici del costruttore non hanno un database gratuito completo: li spiego solo con l'IA o con le note condivise, e lo dico sempre.")
