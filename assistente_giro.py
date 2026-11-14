# -*- coding: utf-8 -*-
"""GIRO COMPLETO DELL'APP con il robottino: animato, parlante, in 8 lingue, con domande e risposte.

Che cosa aggiunge all'assistente che già esiste (assistente.py + assistente_extra.py), senza rifare niente:
 1. 🧭 GIRO COMPLETO: 21 capitoli che spiegano TUTTA l'app (Home, Dispensa, Salute, Documenti, Archivio, Casa, Lavoro, Auto, Chat,
    Utilità, avvisi, Cestino, aiuto). Il robottino parla con la voce del telefono (gratis, nessuna chiave), evidenzia la frase che sta
    dicendo e, se la voce è accesa, passa da solo al capitolo dopo (⏸ Pausa per fermarlo). Pulsanti grandi: Indietro, Pausa, Avanti,
    Fine, 📑 Capitoli (per saltare dove si vuole). Ogni capitolo dice anche DOVE si trova la cosa (📍).
 2. 🌐 LINGUA DEL ROBOTTINO: italiano, inglese, spagnolo, francese, tedesco, romeno, arabo e PORTOGHESE. Si cambia dal pannello del
    robottino con il pulsante 🌐 e resta salvata sul telefono. La lingua dell'app non cambia: cambiano la voce, il giro, i pulsanti del
    robottino e le risposte alle domande.
 3. ❓ DOMANDE: i capitoli del giro entrano nella ricerca dell'assistente (scritta e a voce). Così risponde su Casa, Auto, Lavoro, Chat,
    Archivio… in tutte le 8 lingue (nella lingua dell'app, oltre ai capitoli, usa anche la guida completa come prima).
 4. 🧭 Un pulsante «Fammi il giro completo» in cima alla finestra «📖 Guida e informazioni» (pulsante rosso in alto) e, la prima volta
    che si apre il robottino, l'invito a fare il giro.
I testi italiani stanno qui (AG_CAPITOLI); le altre lingue in assistente_giro_lingue.py (AG_TR, AG_UI). Caricato dopo guida_ar.py.
Se qualcosa manca (per esempio il file delle lingue), il giro funziona in italiano e l'app non cambia."""
import json

import streamlit as st

AG_VERSIONE = "2"

# ---------------------------------------------------------------------------------------------------------------------
# I CAPITOLI DEL GIRO (italiano). id, sezione, titolo, testo (letto e mostrato), dove si trova (📍), parole per la ricerca
# ---------------------------------------------------------------------------------------------------------------------
AG_CAPITOLI = [
    {"id": "g_benvenuto", "s": "app", "t": "Benvenuto! Sono il tuo assistente",
     "x": "Ciao! Sono il robottino dell'app «La nostra dispensa». Adesso ti faccio il giro completo: ti spiego tutte le parti dell'app, una alla volta, con parole semplici. "
          "Se la voce è accesa vado avanti da solo: tocca Pausa per fermarmi, Avanti o Indietro per muoverti, Capitoli per saltare dove vuoi. "
          "Puoi farmi una domanda quando vuoi, scrivendola o con il microfono. Con il pulsante con il mondo cambi la mia lingua.",
     "d": "", "k": "benvenuto inizio giro completo robottino assistente lingua pausa avanti capitoli"},
    {"id": "g_entrare", "s": "app", "t": "Entrare nell'app",
     "x": "Ogni persona della famiglia ha la sua password. Quando entri vedi solo le tue cose: i tuoi prodotti, i tuoi medicinali, i tuoi documenti. "
          "Nessun altro li vede, a parte le cose che scegli di condividere. All'ingresso puoi scegliere la lingua dell'app. "
          "In alto a sinistra c'è una freccia con due punte: apre il menu laterale, dove trovi le tue allergie, la lingua e altre impostazioni.",
     "d": "Prima schermata: scrivi la password e tocca Entra.", "k": "entrare password lingua menu laterale freccia allergie accesso login"},
    {"id": "g_home", "s": "app", "t": "La Home e i pulsanti delle sezioni",
     "x": "In alto, in ogni pagina, c'è una fila di pulsanti colorati: Dispensa, Salute, I miei documenti, Archivio, Casa, Lavoro, Auto, Chat e Utilità. "
          "Scorri la fila con il dito per vedere gli ultimi. Tocchi un pulsante ed entri in quella parte dell'app. "
          "Se su un pulsante compare una campanella con un numero, lì c'è qualcosa da guardare: una scadenza vicina o un messaggio nuovo. "
          "Sotto ai pulsanti trovi sempre il pulsante rosso «Clicca per informazioni» con la guida.",
     "d": "La fila di pulsanti colorati in alto, in ogni pagina.", "k": "home pulsanti sezioni barra campanella numero avvisi colori navigare"},
    {"id": "g_dispensa", "s": "dispensa", "t": "La Dispensa: prodotti e scadenze",
     "x": "La Dispensa è l'elenco di quello che hai in casa da mangiare e da bere. Tocca Aggiungi, fai la foto del prodotto o scrivi il codice a barre, "
          "e l'app compila il nome. Poi scrivi quanti pezzi hai e la scadenza. I colori ti dicono quando agire: verde tutto bene, arancione scade entro due mesi, "
          "rosso entro un mese, scuro è già scaduto. Ci sono tre parti: Adulti, Neonati e Animali, per sapere subito per chi è ogni prodotto.",
     "d": "Pulsante verde 🏠 Dispensa → in basso le schede Dispensa, Aggiungi, Gestisci, Spesa.", "k": "dispensa prodotti scadenza aggiungere foto codice a barre colori verde arancione rosso neonati animali"},
    {"id": "g_dispensa2", "s": "dispensa", "t": "Allergie, lista della spesa e statistiche",
     "x": "Nel menu laterale scegli le tue allergie: i prodotti pericolosi per te mostrano una sirena, così li riconosci subito. "
          "Quando un prodotto finisce, tocca «L'ho consumato» e va da solo nella Lista della spesa, che puoi portare al supermercato. "
          "Con Gestisci cambi quantità e scadenze di tanti prodotti insieme. Le Statistiche ti mostrano quanto hai buttato via, per sprecare meno. "
          "C'è anche la Dispensa di famiglia, per le cose in comune.",
     "d": "🏠 Dispensa → schede Spesa e Gestisci; allergie nel menu laterale (freccia in alto a sinistra).", "k": "allergie allergeni sirena lista spesa consumato gestisci statistiche sprechi famiglia"},
    {"id": "g_salute", "s": "farmacia", "t": "Salute: le persone e i medicinali",
     "x": "In Salute tieni la salute di tutta la famiglia. Prima scegli la persona: tu, la mamma, i figli. Ognuno ha il suo profilo con gruppo sanguigno e allergie ai farmaci. "
          "Poi aggiungi i medicinali con la scadenza: puoi fotografare la scatola. Per ogni medicinale puoi leggere il bugiardino con parole semplici. "
          "L'app conta le scorte: quando una medicina sta per finire te lo dice e ti prepara la richiesta della ricetta per la dottoressa.",
     "d": "Pulsante rosso 🩺 Salute → scegli la persona in alto → scheda Medicinali.", "k": "salute persona profilo mamma medicinali farmaci scadenza bugiardino scorte ricetta dottoressa gruppo sanguigno"},
    {"id": "g_terapie", "s": "farmacia", "t": "Terapie e promemoria",
     "x": "Una terapia è una medicina da prendere con regolarità: tutti i giorni a una certa ora, oppure ogni tanto, per esempio una fiala ogni quindici giorni. "
          "L'app ti ricorda quando prenderla: con un messaggio su Telegram, per email o su WhatsApp. "
          "Puoi anche scaricare gli allarmi sul Calendario del telefono: così suona la sveglia all'ora giusta, anche senza aprire l'app. "
          "Per ogni terapia scrivi medicina, dose, orario e quanto dura.",
     "d": "🩺 Salute → scheda Terapie → ➕ Nuova terapia; allarmi in «📅 Allarmi sul Calendario del telefono».", "k": "terapia terapie promemoria avviso orario dose telegram email whatsapp calendario sveglia allarme ogni giorno intervalli"},
    {"id": "g_visite", "s": "farmacia", "t": "Visite, vaccini, dottore e tessera sanitaria",
     "x": "In Salute segni anche le visite e gli esami, con data e ora: puoi fotografare il foglio della prenotazione e l'app legge la data da sola. "
          "Dopo la visita conservi il referto. Ci sono i vaccini con i richiami, la scheda del tuo dottore e la tessera sanitaria, con i collegamenti al fascicolo sanitario. "
          "Con un tocco prepari un riepilogo completo di una persona, da mostrare al medico o da mandare per email.",
     "d": "🩺 Salute → schede Visite e Vaccini; badge azzurro della tessera sanitaria accanto alla dottoressa.", "k": "visite esami referto prenotazione vaccini richiami dottore medico tessera sanitaria fascicolo report riepilogo"},
    {"id": "g_documenti", "s": "documenti", "t": "I miei documenti",
     "x": "Qui conservi i documenti personali: carta d'identità, patente, passaporto, tessera sanitaria, permesso di soggiorno. "
          "Fai la foto al documento: l'app toglie lo sfondo, lo raddrizza e prova a leggere il tipo, il numero e la scadenza. Puoi sempre correggere a mano. "
          "Sei mesi e tre mesi prima della scadenza l'app ti avvisa, così rinnovi in tempo. I documenti sono solo tuoi: nessun altro li vede.",
     "d": "Pulsante azzurro 📁 I miei documenti → «Aggiungi un documento».", "k": "documenti carta identità patente passaporto foto scadenza rinnovo avviso privacy"},
    {"id": "g_archivio", "s": "archivio", "t": "L'Archivio: tutti i file in un posto",
     "x": "L'Archivio raccoglie tutti i file che hai salvato nell'app: foto di documenti, bugiardini, referti, manuali, bollette. "
          "Li cerchi scrivendo una parola, li filtri per tipo o per persona, li apri, li scarichi o li mandi per email e WhatsApp. "
          "Se un dato è sbagliato lo correggi, e puoi sostituire il file con uno migliore. È come un grande raccoglitore ordinato, sempre in tasca.",
     "d": "Pulsante viola 🗂️ Archivio → casella di ricerca in alto.", "k": "archivio file cercare filtrare aprire scaricare inviare correggere raccoglitore"},
    {"id": "g_casa", "s": "casa", "t": "Casa: beni, manuali e garanzie",
     "x": "In Casa tieni gli apparecchi di casa: lavatrice, frigorifero, caldaia, televisore. Per ognuno salvi il manuale, la garanzia, lo scontrino e le bollette. "
          "Se l'apparecchio dà un problema, cerchi una parola dentro il manuale, per esempio il codice dell'errore o «pulizia del filtro»: l'app ti mostra le pagine giuste con le parole evidenziate. "
          "Se vuoi, te le spiega in parole semplici. Puoi mandare i documenti anche dalla posta o dalle app dei fornitori.",
     "d": "Pulsante arancione 🏡 Casa → schede Beni e Documenti → sul documento «🔎 Cerca nel manuale».", "k": "casa beni apparecchi elettrodomestici manuale garanzia bolletta scontrino cercare nel manuale errore spiegami"},
    {"id": "g_casa2", "s": "casa", "t": "Manutenzioni e Amministrazione della casa",
     "x": "In Casa registri anche le manutenzioni, come la revisione della caldaia, e l'app ti ricorda la prossima. "
          "Nella scheda Amministrazione tieni le spese condominiali e le rate con le date di pagamento, i contatti di idraulico, elettricista e amministratore, "
          "e il calendario della raccolta differenziata con il ritiro degli ingombranti. Puoi mandare tutta l'Amministrazione a un altro utente con un file protetto da password.",
     "d": "🏡 Casa → schede Manutenzioni e Amministrazione.", "k": "manutenzione caldaia amministrazione condominio spese rate pagamenti contatti idraulico elettricista raccolta differenziata ingombranti scambio"},
    {"id": "g_lavoro", "s": "lavoro", "t": "Lavoro: buste paga e documenti",
     "x": "In Lavoro carichi le buste paga, anche fotografandole: l'app legge le cifre e le mette in ordine. "
          "Anno per anno vedi i grafici e il confronto tra i mesi. Conservi la Certificazione Unica e i documenti dell'INPS. "
          "C'è anche la rubrica del sindacato, del CAF e del patronato, con telefono e orari, così li trovi subito quando servono.",
     "d": "Pulsante grigio 💼 Lavoro → schede Buste paga, Anno per anno, CU, INPS, Sindacato.", "k": "lavoro busta paga stipendio grafici anno certificazione unica cu inps sindacato caf patronato"},
    {"id": "g_auto", "s": "auto", "t": "Auto: il garage e le scadenze",
     "x": "In Auto c'è il tuo garage: ogni veicolo ha la sua scheda. Puoi fotografare la carta di circolazione e l'app legge targa, marca e modello. "
          "Ti ricorda bollo, assicurazione e revisione prima che scadano. Registri le manutenzioni, i rifornimenti e le spese, così sai quanto ti costa l'auto. "
          "Ci sono anche la patente con i punti e le multe, e i viaggi con i rimborsi chilometrici.",
     "d": "Pulsante azzurro 🚗 Auto → il garage → tocca un veicolo → Scadenze, Manutenzione, Rifornimenti.", "k": "auto veicolo garage targa libretto carta circolazione bollo assicurazione revisione manutenzione rifornimento spese patente multe viaggi"},
    {"id": "g_auto2", "s": "auto", "t": "Auto: spie, diagnostica ed emergenza",
     "x": "Se sul cruscotto si accende una spia, fotografala: l'app ti dice cosa significa e se puoi continuare a guidare. "
          "Nella Diagnostica trovi i codici di errore e, con un piccolo apparecchio da collegare all'auto, anche i dati del motore. "
          "In Emergenza hai i numeri utili, il soccorso stradale e il modulo per il sinistro, con i passi da seguire con calma se hai un incidente.",
     "d": "🚗 Auto → Diagnostica → «📷 Fotografa una spia»; 🚗 Auto → Emergenza.", "k": "spia cruscotto diagnostica codici errore obd emergenza soccorso stradale incidente sinistro constatazione"},
    {"id": "g_chat", "s": "chat", "t": "La Chat della famiglia",
     "x": "Con la Chat scrivi alle persone della famiglia senza uscire dall'app, gratis. In alto scegli con chi parlare: Tutti, cioè il gruppo di famiglia, oppure una persona sola, in privato. "
          "Scegli chi tenere in vista come pulsante; le altre persone stanno nel menu «Altre persone». "
          "I tuoi messaggi sono a destra in verde, quelli degli altri a sinistra in bianco. Un pallino rosso con il numero ti dice quanti messaggi nuovi hai.",
     "d": "Pulsante 💬 Chat in alto → scegli la persona → scrivi in basso → 📨 Invia.", "k": "chat messaggi famiglia scrivere tutti privata persone in vista altre persone nuovi messaggi"},
    {"id": "g_utilita", "s": "utilita", "t": "Le Utilità",
     "x": "Nelle Utilità ci sono gli strumenti di servizio. Il Cestino, dove restano trenta giorni le cose eliminate. L'Aspetto dell'app, per avere testi più grandi. "
          "Lo Scambio dati, per mandare i tuoi dati a un'altra persona o riceverli. Libera spazio, per togliere i file inutili dal telefono. "
          "E le app utili, come Wimbi e Velocity Music, con il loro bugiardino che spiega cosa fanno.",
     "d": "Pulsante viola 🧰 Utilità, l'ultimo della fila in alto.", "k": "utilità cestino aspetto testi grandi scambio dati libera spazio wimbi velocity app utili"},
    {"id": "g_avvisi", "s": "farmacia", "t": "Come arrivano gli avvisi",
     "x": "L'app ti avvisa prima delle scadenze e all'ora delle terapie. Gli avvisi arrivano su Telegram, per email, su WhatsApp o come allarme sul Calendario del telefono: scegli tu quali. "
          "Telegram ed email sono gratuiti e sicuri; basta impostarli una volta. Dentro Salute c'è il pulsante per mandare un messaggio di prova, così controlli che tutto funzioni. "
          "Nell'app, la campanella con il numero sui pulsanti in alto ti mostra le cose da vedere.",
     "d": "🩺 Salute → tendina «🔔 Avvisi» → scegli i canali e tocca «Messaggio di prova».", "k": "avvisi notifiche promemoria telegram email whatsapp calendario campanella messaggio di prova impostare"},
    {"id": "g_cestino", "s": "utilita", "t": "Ho sbagliato: il Cestino",
     "x": "Non avere paura di sbagliare. Quando elimini qualcosa, in cima alla pagina compare per qualche secondo il pulsante Annulla: toccalo e torna tutto come prima. "
          "Se te ne accorgi dopo, apri il Cestino nelle Utilità: le cose eliminate restano lì trenta giorni e con Ripristina tornano al loro posto. "
          "Solo tu puoi decidere di eliminarle per sempre.",
     "d": "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina.", "k": "sbagliato errore eliminato per sbaglio annulla cestino ripristina recuperare trenta giorni"},
    {"id": "g_aiuto", "s": "app", "t": "Aiuto sempre a portata di mano",
     "x": "Se non ricordi come si fa una cosa, hai tre aiuti. Il pulsante rosso «Clicca per informazioni» in alto, con la guida di ogni pagina e una casella per cercare. "
          "Io, il robottino: toccami e ti spiego la pagina in cui sei, oppure scrivimi o dimmi una domanda con il microfono. "
          "E le Novità, dove ti racconto cosa c'è di nuovo. Puoi rendere la mia voce più lenta o più veloce, cambiare lingua, o spegnermi: mi riaccendi dal pulsante rosso.",
     "d": "Il robottino in basso a destra; il pulsante rosso in alto in ogni pagina.", "k": "aiuto guida informazioni domanda microfono voce lenta veloce novità spegnere assistente"},
    {"id": "g_fine", "s": "app", "t": "Fine del giro",
     "x": "Il giro è finito, bravo! Ora conosci tutte le parti dell'app. Non devi ricordare tutto: ogni volta che ti serve, toccami e chiedimi. "
          "Comincia dalle cose che usi di più, per esempio la Dispensa o le medicine della famiglia, e scopri il resto con calma. Buon lavoro!",
     "d": "", "k": "fine giro finito grazie ricomincia"},
]

# nomi delle lingue del robottino (nella loro lingua) e codici per la voce del telefono
AG_LINGUE = [("it", "Italiano", "it-IT"), ("en", "English", "en-GB"), ("es", "Español", "es-ES"), ("fr", "Français", "fr-FR"),
             ("de", "Deutsch", "de-DE"), ("ro", "Română", "ro-RO"), ("ar", "العربية", "ar-SA"), ("pt", "Português", "pt-PT")]
AG_RTL = {"ar"}

# le scritte nuove del pannello (italiano); le altre lingue in assistente_giro_lingue.py
AG_UI_IT = {
    "a_giro": "🧭 Giro completo dell'app", "a_giro_dlg": "🧭 Fammi il giro completo dell'app (il robottino lo racconta a voce)",
    "a_capitoli": "📑 Capitoli", "a_pausa": "⏸ Pausa", "a_riprendi": "▶ Riprendi", "a_dove": "Dove si trova:",
    "a_lingua": "🌐 Lingua", "a_lingua_t": "In che lingua vuoi che parli?", "a_lingua_x": "Scegli qui sotto. La lingua dell'app non cambia: cambiano la mia voce, il giro e le risposte.",
    "a_lingua_ok": "Perfetto, da adesso parlo italiano.", "a_cap_t": "I capitoli del giro", "a_cap_x": "Tocca un capitolo per andare direttamente lì.",
    "a_primo_t": "Ciao! È la prima volta che mi apri", "a_primo_x": "Vuoi che ti faccia il giro completo dell'app? Dura pochi minuti e puoi fermarmi quando vuoi. Tocca il pulsante giallo qui sotto, oppure «Fammi il giro».",
    "a_primo_btn": "🧭 Fammi il giro", "a_fine_t": "Fine del giro", "a_fine_x": "Ecco fatto! Se ti serve altro, chiedimi.",
    "a_auto_on": "▶ Vado avanti da solo", "a_auto_off": "⏸ Fermo a ogni capitolo",
}

# ---------------------------------------------------------------------------------------------------------------------
# traduzioni: riempite da assistente_giro_lingue.py  (AG_TR[lingua][id] = (titolo, testo, dove, parole); AG_UI[lingua] = scritte)
# ---------------------------------------------------------------------------------------------------------------------
AG_TR = {}
AG_UI = {}
AG_STOP = {"pt": "o a os as um uma uns umas de do da dos das em no na nos nas para por com e ou que quem como onde quando qual quais "
                 "me te se nos vos não é são tenho tens tem posso podes fazer faço devo quero queria se este esta isso meu minha teu tua app mais também".split()}


def ag_capitoli(lingua):
    """I capitoli del giro nella lingua chiesta (se manca una traduzione, quel capitolo resta in italiano)."""
    tr = AG_TR.get(lingua, {}) if lingua != "it" else {}
    out = []
    for c in AG_CAPITOLI:
        x = tr.get(c["id"])
        if x:
            out.append({"id": c["id"], "s": c["s"], "t": x[0], "x": x[1], "d": x[2] if len(x) > 2 else "", "k": (x[3] if len(x) > 3 else "") + " " + c["k"]})
        else:
            out.append(dict(c))
    return out


def ag_ui(lingua):
    """Tutte le scritte del pannello (a_*, i_*) nella lingua chiesta: prima quelle del giro, poi quelle della guida, poi l'italiano."""
    base = {k: v for k, v in UI_IT.items() if k.startswith(("a_", "i_"))} if "UI_IT" in globals() else {}
    base.update(AG_UI_IT)
    if lingua != "it":
        tr = UI_TR.get(lingua, {}) if "UI_TR" in globals() else {}
        base.update({k: v for k, v in tr.items() if k.startswith(("a_", "i_"))})
        base.update(AG_UI.get(lingua, {}))
    return base


def ag_config_lingue():
    """La configurazione di tutte le lingue del robottino (mandata al browser una volta per sessione)."""
    out = {}
    for cod, nome, bcp in AG_LINGUE:
        stop = AG_STOP.get(cod)
        if stop is None and "_STOP_LANG" in globals():
            stop = _STOP_LANG.get(cod, _STOP_LANG.get("it", []))
        out[cod] = {"nome": nome, "lang": bcp, "rtl": cod in AG_RTL, "ui": ag_ui(cod), "tour": ag_capitoli(cod), "stop": list(stop or [])}
    return out


# ---------------------------------------------------------------------------------------------------------------------
# lo script del robottino, versione 2 (tutto quello di prima + giro completo, lingue, pausa, capitoli, frase evidenziata)
# ---------------------------------------------------------------------------------------------------------------------
_AG_JS = r"""
(function () {
  var w = window, doc = w.document;
  var CFG = __CONFIG__;
  try {
  if (w.__assistente && w.__assistente.versione === CFG.versione) { w.__assistente.aggiorna(CFG); return; }
  if (w.__assistente && w.__assistente.rimuovi) { try { w.__assistente.rimuovi(); } catch (e) {} }
  var D = CFG, SS = w.speechSynthesis, SR = w.SpeechRecognition || w.webkitSpeechRecognition;
  function leggi(k, def) { try { var v = w.localStorage.getItem(k); return v === null ? def : v; } catch (e) { return def; } }
  function scrivi(k, v) { try { w.localStorage.setItem(k, v); } catch (e) {} }
  function T(k) { return (D.ui && D.ui[k]) || ''; }
  var attivo = leggi('asst_attivo', '1') === '1', voceOn = leggi('asst_voce', '1') === '1', autoOn = leggi('asst_auto', '1') === '1';
  var ultimoCmd = (D.cmd && D.cmd.id) || '';
  var tourIdx = -1, riconoscimento = null, aperto = false, ctxCorrente = D.ctx, inPausa = false, timerAuto = null, serie = 0;
  var lingua = D.applang || 'it';
  (function () { var s = leggi('asst_lingua', ''); if (s && D.lingue && D.lingue[s]) lingua = s; })();
  function applicaLingua() {
    var L = D.lingue && D.lingue[lingua]; if (!L) return;
    D.lang = L.lang; D.rtl = L.rtl; D.ui = L.ui; D.tour = L.tour; D.stop = L.stop; stopSet = null; indice = null;
  }

  /* ---------- aspetto ---------- */
  var st = doc.createElement('style'); st.id = 'asst-css';
  st.textContent =
    '@keyframes asstAnello{0%{box-shadow:0 0 0 0 rgba(25,80,180,.55)}70%{box-shadow:0 0 0 14px rgba(25,80,180,0)}100%{box-shadow:0 0 0 0 rgba(25,80,180,0)}}' +
    '@keyframes asstFluttua{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}' +
    '@keyframes asstParla{0%,100%{transform:scale(1) rotate(-1.5deg)}50%{transform:scale(1.06) rotate(1.5deg)}}' +
    '@keyframes asstSaluta{0%,100%{transform:rotate(0)}25%{transform:rotate(-8deg) translateY(-4px)}75%{transform:rotate(8deg) translateY(-4px)}}' +
    '@keyframes asstAscolta{0%{box-shadow:0 0 0 0 rgba(229,72,77,.7)}100%{box-shadow:0 0 0 18px rgba(229,72,77,0)}}' +
    '@keyframes asstFrase{0%{background:#fff3b0}100%{background:#ffe066}}' +
    '#asst-btn{position:fixed;right:12px;bottom:108px;width:62px;height:62px;border-radius:50%;border:0;padding:0;background:transparent;' +
      'z-index:99998;cursor:pointer;animation:asstAnello 2.4s infinite;box-shadow:0 6px 14px rgba(0,0,0,.28)}' +
    '#asst-btn img{width:100%;height:100%;display:block;border-radius:50%}#asst-btn:active{transform:scale(.93)}' +
    '#asst-pan{position:fixed;left:8px;right:8px;bottom:8px;max-width:560px;margin:0 auto;z-index:100000;background:#fff;color:#14302b;' +
      'border-radius:26px;border:3px solid #ffd600;box-shadow:0 14px 40px rgba(0,0,0,.4);max-height:86vh;overflow:auto;' +
      'font-family:inherit;padding:12px 12px 10px;display:none}' +
    '#asst-pan *{box-sizing:border-box}' +
    '.asst-top{display:flex;gap:10px;align-items:flex-start}' +
    '.asst-robot{flex:0 0 92px}.asst-robot img{width:92px;height:auto;display:block;animation:asstFluttua 3s ease-in-out infinite}' +
    '.asst-robot.parla img{animation:asstParla .6s ease-in-out infinite;filter:drop-shadow(0 0 10px rgba(255,214,0,.9))}' +
    '.asst-robot.saluta img{animation:asstSaluta 1.1s ease-in-out 2}' +
    '.asst-robot.ascolta img{filter:drop-shadow(0 0 10px rgba(229,72,77,.9))}' +
    '.asst-bolla{flex:1;min-width:0;background:#eef6ff;border:2px solid #1950b4;border-radius:18px 18px 18px 4px;padding:9px 12px;' +
      'max-height:36vh;overflow:auto;font-size:14.5px;line-height:1.4}' +
    '#asst-pan[dir=rtl] .asst-bolla{border-radius:18px 18px 4px 18px}' +
    '.asst-titolo{font-weight:900;color:#1950b4;margin-bottom:3px;font-size:15px}.asst-testo b{font-weight:800}' +
    '.asst-testo .asst-fr{border-radius:6px;padding:1px 2px;transition:background .3s}.asst-testo .asst-fr.ora{background:#ffe066;animation:asstFrase .6s;font-weight:700}' +
    '.asst-testo .asst-dove{display:block;margin-top:8px;padding:6px 8px;border-radius:10px;background:#fff8d6;border:1px dashed #d4a500;font-size:13.5px}' +
    '.asst-x{flex:0 0 auto;width:34px;height:34px;border-radius:50%;border:0;background:#e9eef2;font-size:16px;cursor:pointer;color:#14302b}' +
    '.asst-azioni{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0 6px}' +
    '#asst-pan button.asst-b{border:0;border-radius:14px;padding:11px 8px;font-size:13.5px;font-weight:800;cursor:pointer;color:#fff;' +
      'background:linear-gradient(135deg,#1950b4,#2f80ed)}' +
    '#asst-pan button.asst-b.giallo{background:linear-gradient(135deg,#f5b800,#ffd600);color:#3a2d00}' +
    '#asst-pan button.asst-b.verde{background:linear-gradient(135deg,#0f9d74,#26a69a)}' +
    '#asst-pan button.asst-b.rosso{background:linear-gradient(135deg,#c62828,#ef5350)}' +
    '#asst-pan button.asst-b.grigio{background:#e9eef2;color:#14302b}' +
    '#asst-pan button.asst-b.ascolta{background:#e5484d;animation:asstAscolta 1s infinite}' +
    '.asst-tour{display:none;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:6px 0}' +
    '.asst-tour .asst-prog{grid-column:1/4;display:flex;align-items:center;gap:8px;font-weight:800;font-size:13px;color:#1950b4}' +
    '.asst-tour .asst-barra{flex:1;height:8px;border-radius:99px;background:#e3eaf2;overflow:hidden}.asst-tour .asst-barra i{display:block;height:100%;background:linear-gradient(90deg,#f5b800,#ffd600);width:0;transition:width .4s}' +
    '.asst-chiedi{display:flex;gap:6px;margin:6px 0}' +
    '.asst-chiedi input{flex:1;min-width:0;border:2px solid #b9c8d8;border-radius:14px;padding:10px 12px;font-size:14.5px;background:#fff;color:#14302b}' +
    '.asst-sugg{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}' +
    '.asst-sugg button{border:2px solid #1950b4;background:#fff;color:#1950b4;border-radius:999px;padding:6px 11px;font-size:12.5px;font-weight:700;cursor:pointer}' +
    '.asst-sugg button.asst-grande{width:100%;font-size:15px;padding:12px;background:linear-gradient(135deg,#f5b800,#ffd600);color:#3a2d00;border-color:#f5b800}' +
    '.asst-sugg button.asst-lg.ora{background:#1950b4;color:#fff}' +
    '.asst-pie{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.asst-pie button{flex:1 1 auto}' +
    '#asst-toast{position:fixed;left:50%;transform:translateX(-50%);bottom:120px;max-width:90vw;background:#14302b;color:#fff;padding:10px 16px;' +
      'border-radius:16px;font-size:13.5px;z-index:100001;display:none;text-align:center}';
  doc.head.appendChild(st);

  var btn = doc.createElement('button'); btn.id = 'asst-btn';
  btn.innerHTML = D.img.testa ? '<img alt="" src="' + D.img.testa + '">' : '<span style="font-size:34px">🤖</span>';
  var pan = doc.createElement('div'); pan.id = 'asst-pan'; pan.setAttribute('role', 'dialog');
  pan.innerHTML =
    '<div class="asst-top"><div class="asst-robot">' + (D.img.intero ? '<img alt="" src="' + D.img.intero + '">' : '<span style="font-size:60px">🤖</span>') + '</div>' +
    '<div class="asst-bolla"><div class="asst-titolo"></div><div class="asst-testo"></div></div>' +
    '<button class="asst-x" aria-label="X">✕</button></div>' +
    '<div class="asst-azioni">' +
      '<button class="asst-b" data-az="pagina" data-ui="a_rileggi"></button>' +
      '<button class="asst-b giallo" data-az="giro" data-ui="a_giro"></button>' +
      '<button class="asst-b verde" data-az="novita" data-ui="a_novita"></button>' +
      '<button class="asst-b rosso" data-az="mic" data-ui="a_mic"></button></div>' +
    '<div class="asst-tour"><div class="asst-prog"><span class="asst-num"></span><div class="asst-barra"><i></i></div><button class="asst-b grigio" data-az="capitoli" data-ui="a_capitoli" style="padding:7px 9px;font-size:12.5px"></button></div>' +
      '<button class="asst-b grigio" data-az="indietro" data-ui="a_indietro"></button>' +
      '<button class="asst-b giallo" data-az="pausa"></button>' +
      '<button class="asst-b" data-az="avanti" data-ui="a_avanti"></button>' +
      '<button class="asst-b grigio" data-az="fine" data-ui="a_fine" style="grid-column:1/4;padding:8px"></button></div>' +
    '<div class="asst-chiedi"><input type="text"><button class="asst-b" data-az="chiedi" data-ui="a_chiedi"></button></div>' +
    '<div class="asst-sugg"></div>' +
    '<div class="asst-pie"><button class="asst-b grigio" data-az="voce"></button>' +
      '<button class="asst-b grigio" data-az="vel"></button>' +
      '<button class="asst-b grigio" data-az="lingua"></button>' +
      '<button class="asst-b grigio" data-az="silenzio" data-ui="a_silenzio"></button>' +
      '<button class="asst-b grigio" data-az="off" data-ui="a_off"></button></div>';
  var toast = doc.createElement('div'); toast.id = 'asst-toast';
  doc.body.appendChild(btn); doc.body.appendChild(pan); doc.body.appendChild(toast);
  function $(s) { return pan.querySelector(s); }
  var elTitolo = $('.asst-titolo'), elTesto = $('.asst-testo'), elRobot = $('.asst-robot'), elTour = $('.asst-tour'),
      elSugg = $('.asst-sugg'), elInput = $('.asst-chiedi input'), btnMic = pan.querySelector('[data-az="mic"]'),
      btnVoce = pan.querySelector('[data-az="voce"]'), btnVel = pan.querySelector('[data-az="vel"]'), btnLingua = pan.querySelector('[data-az="lingua"]'),
      btnPausa = pan.querySelector('[data-az="pausa"]'), elNum = $('.asst-num'), elBarra = $('.asst-barra i');
  if (!SR) btnMic.style.display = 'none';
  if (!SS) { btnVel.style.display = 'none'; btnVoce.style.display = 'none'; pan.querySelector('[data-az="silenzio"]').style.display = 'none'; }
  function velocita() { var v = parseFloat(leggi('asst_rate', '1')); return (v >= 0.5 && v <= 2) ? v : 1; }
  function aggiornaVoceBtn() {
    btnVoce.textContent = voceOn ? T('a_voce_on') : T('a_voce_off');
    var v = velocita(); btnVel.textContent = T('a_vel') + ': ' + T(v < 0.9 ? 'a_vel_0' : (v > 1.1 ? 'a_vel_2' : 'a_vel_1'));
    var L = D.lingue && D.lingue[lingua]; btnLingua.textContent = T('a_lingua') + ': ' + (L ? L.nome : lingua);
    btnPausa.textContent = inPausa ? T('a_riprendi') : T('a_pausa');
  }
  function applicaUI() {
    [].forEach.call(pan.querySelectorAll('[data-ui]'), function (b) { b.textContent = T(b.getAttribute('data-ui')); });
    elInput.placeholder = T('a_ph'); btn.setAttribute('aria-label', T('a_aria')); pan.setAttribute('aria-label', T('a_aria'));
    pan.setAttribute('dir', D.rtl ? 'rtl' : 'ltr'); toast.setAttribute('dir', D.rtl ? 'rtl' : 'ltr'); aggiornaVoceBtn();
  }

  /* ---------- testi e voce ---------- */
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function mdHtml(s) {
    return esc(s).replace(/^#{1,6}\s*/gm, '').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`([^`]*)`/g, '$1')
      .replace(/^\s*[-•]\s+/gm, '• ').replace(/\n/g, '<br>');
  }
  var RX_EMOJI = /[\u{1F000}-\u{1FAFF}\u{2190}-\u{21FF}\u{2300}-\u{23FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}]/gu;
  function perVoce(s) {
    return String(s).replace(/\*\*/g, '').replace(/`/g, '').replace(/^#{1,6}\s*/gm, '').replace(RX_EMOJI, '')
      .replace(/https?:\/\/\S+/g, '').replace(/[«»]/g, '').replace(/^\s*[-•]\s+/gm, '').replace(/\n+/g, '. ').replace(/\s+/g, ' ').replace(/\.\s*\./g, '.').trim();
  }
  function scegliVoce() {
    var pre = (D.lang || 'it-IT').slice(0, 2).toLowerCase(), rx = new RegExp('^' + pre, 'i');
    var vs = (SS && SS.getVoices && SS.getVoices()) || [], ok = vs.filter(function (v) { return rx.test(v.lang); });
    var esatta = ok.filter(function (v) { return String(v.lang).replace('_', '-').toLowerCase() === String(D.lang).toLowerCase(); });
    return esatta.filter(function (v) { return /google|natural|neural|premium/i.test(v.name); })[0] || ok.filter(function (v) { return /google|natural|neural|premium/i.test(v.name); })[0] || esatta[0] || ok[0] || null;
  }
  function spezza(testo) {
    var frasi = testo.split(/(?<=[.!?;:،؛؟])\s+/), out = [], cur = '';
    frasi.forEach(function (f) {
      if ((cur + ' ' + f).length > 190 && cur) { out.push(cur); cur = f; } else { cur = cur ? cur + ' ' + f : f; }
    });
    if (cur) out.push(cur);
    return out;
  }
  function ferma() { serie++; if (timerAuto) { w.clearTimeout(timerAuto); timerAuto = null; } try { if (SS) SS.cancel(); } catch (e) {} elRobot.classList.remove('parla'); evidenzia(-1); }
  function evidenzia(i) { var sp = elTesto.querySelectorAll('.asst-fr'); for (var k = 0; k < sp.length; k++) sp[k].classList.toggle('ora', k === i); if (i >= 0 && sp[i] && sp[i].scrollIntoView) { try { sp[i].scrollIntoView({block: 'nearest', behavior: 'smooth'}); } catch (e) {} } }
  function parla(testo, alFine, pezziDati) {
    ferma();
    var mia = serie;
    if (!SS || !voceOn) { if (alFine) w.setTimeout(function () { if (mia === serie) alFine(); }, 0); return; }
    var pezzi = pezziDati || spezza(perVoce(testo)), i = 0, voce = scegliVoce();
    if (!pezzi.length) return;
    function dici() {
      if (mia !== serie) return;
      if (i >= pezzi.length) { elRobot.classList.remove('parla'); evidenzia(-1); if (alFine) alFine(); return; }
      var idx = i, u = new w.SpeechSynthesisUtterance(pezzi[i++]); u.lang = D.lang || 'it-IT'; u.rate = velocita(); u.pitch = 1.05;
      if (voce) u.voice = voce;
      u.onstart = function () { if (mia === serie && pezziDati) evidenzia(idx); };
      u.onend = dici; u.onerror = function () { if (mia !== serie) return; elRobot.classList.remove('parla'); evidenzia(-1); if (alFine) alFine(); };
      elRobot.classList.add('parla'); if (pezziDati) evidenzia(idx); SS.speak(u);
    }
    dici();
  }
  function mostra(titolo, testo, voceTesto, parlare, alFine) {
    elTitolo.textContent = titolo || ''; elTesto.innerHTML = mdHtml(testo); $('.asst-bolla').scrollTop = 0;
    if (parlare === false) return;
    parla((titolo ? titolo + (/[.!?:؟]$/.test(titolo) ? ' ' : '. ') : '') + (voceTesto || testo), alFine);
  }
  function avviso(m) { toast.textContent = m; toast.style.display = 'block'; w.setTimeout(function () { toast.style.display = 'none'; }, 5200); }

  /* ---------- ricerca nella guida e nei capitoli del giro (nella lingua del robottino) ---------- */
  function norm(s) { return String(s).toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/[^\p{L}\p{N}]+/gu, ' '); }
  function stem(p) { return p.length > 4 ? p.replace(/[aeiou]+$/, '') : p; }
  var stopSet = null;
  function parole(s) {
    if (!stopSet) { stopSet = {}; (D.stop || []).forEach(function (x) { stopSet[norm(x).trim()] = 1; }); }
    var min = /^ar/i.test(D.lang || '') ? 2 : 3, o = {};
    var ar = /^ar/i.test(D.lang || '');
    norm(s).split(' ').forEach(function (p) { if (p.length >= min && !stopSet[p]) o[stem(ar && p.length > 4 ? p.replace(/^(وال|بال|كال|لل|ال)/, '') : p)] = 1; });
    return Object.keys(o);
  }
  function combacia(q, ins) { for (var i = 0; i < ins.length; i++) { var x = ins[i]; if (x.indexOf(q) === 0 || (x.length >= 4 && q.indexOf(x) === 0)) return true; } return false; }
  var indice = null;
  function vociGiro() { return (D.tour || []).map(function (c, i) { return {id: 'giro:' + i, s: c.s, t: c.t, b: c.x + (c.d ? '\n\n📍 ' + T('a_dove') + ' ' + c.d : ''), k: c.k || '', a: null, o: null, giro: i}; }); }
  function vociTutte() { var g = vociGiro(); return (lingua === (D.applang || 'it')) ? (D.guida || []).concat(g) : g; }   /* in un'altra lingua rispondo con i capitoli, che sono tradotti */
  function costruisci() { indice = vociTutte().map(function (g) { return {g: g, t: parole(g.t), k: parole(g.k), b: parole(g.b)}; }); }
  var memoria = {az: null, og: null};
  function rileva(testo) {
    var n = ' ' + norm(testo).trim() + ' ', I = D.intenti || {az: {}, og: {}}, r = {az: null, og: null};
    ['az', 'og'].forEach(function (tipo) {
      var best = 1e9;
      Object.keys(I[tipo] || {}).forEach(function (k) {
        I[tipo][k].forEach(function (p) {
          var esatta = p.charAt(0) === '=', q = norm(esatta ? p.slice(1) : p).trim(), pos = q ? n.indexOf(' ' + q + (esatta ? ' ' : '')) : -1;
          if (pos >= 0 && pos < best) { best = pos; r[tipo] = k; }
        });
      });
    });
    var rec = (I.az && I.az.recupera) || [];
    if (rec.some(function (p) { var esatta = p.charAt(0) === '=', q = norm(esatta ? p.slice(1) : p).trim(); return q && n.indexOf(' ' + q + (esatta ? ' ' : '')) >= 0; })) r.az = 'recupera';
    return r;
  }
  function cerca(domanda, intento) {
    if (!indice) costruisci();
    var q = parole(domanda); if (!q.length) return [];
    var az = intento && intento.az, og = intento && intento.og, ris = [], esatte = 0;
    indice.forEach(function (e) {
      var pt = 0, tr = 0, bonus = 0, ex = false, forte = false;
      q.forEach(function (x) {
        if (combacia(x, e.t)) { pt += 3; tr++; forte = true; } else if (combacia(x, e.k)) { pt += 2; tr++; forte = true; } else if (combacia(x, e.b)) { pt += 1; tr++; }
      });
      var a = e.g.a, o = e.g.o;
      if (az && a) bonus += (a === az) ? 6 : -8;
      if (og && o) bonus += (o === og) ? 6 : -4;
      if (az && og && a === az && o === og) { bonus += 12; ex = true; }
      if (ex) esatte++;
      if (pt + bonus > 0 && (bonus > 0 || tr >= 2 || q.length <= 2)) ris.push({p: pt + tr + bonus + (e.g.s === D.sezione ? 1 : 0), g: e.g, ex: ex});
    });
    ris.sort(function (a, b) { return b.p - a.p; });
    if (!ris.length) return [];
    if (esatte) return [ris[0].g];
    var top = ris[0].p; return ris.filter(function (r) { return r.p * 2 >= top; }).slice(0, 4).map(function (r) { return r.g; });
  }
  function argomento(g, parlare, prefisso) {
    modoGiro(false); tourIdx = -1;
    var testo = (prefisso || '') + g.b;
    var corto = perVoce(testo); if (corto.length > 900) corto = corto.slice(0, 900).replace(/[^.!?؟]*$/, '') || corto.slice(0, 900);
    mostra(g.t, testo, corto, parlare);
  }
  function chipsTesto(lista) {
    elSugg.innerHTML = '';
    lista.forEach(function (x) {
      var b = doc.createElement('button'); b.textContent = x[0]; b.addEventListener('click', function () { elInput.value = x[1]; chiedi(x[1]); }); elSugg.appendChild(b);
    });
  }
  function chips(lista) {
    elSugg.innerHTML = '';
    lista.forEach(function (g) {
      var b = doc.createElement('button'); b.textContent = g.t;
      b.addEventListener('click', function () { if (g.giro !== undefined) tourVai(g.giro); else { argomento(g); chips([]); } }); elSugg.appendChild(b);
    });
  }
  function voceGuida(id) { var l = vociTutte(); for (var i = 0; i < l.length; i++) if (l[i].id === id) return l[i]; return null; }
  function argomentiSezione(escludi) { return vociTutte().filter(function (g) { return g.s === D.sezione && g.id !== escludi; }).slice(0, 8); }

  /* ---------- la pagina in cui sei ---------- */
  function ctxAttuale() {
    var base = D.ctx || D.sezione; if (base.indexOf(':') >= 0) return base;
    var lista = D.tabs && D.tabs[D.sezione]; if (!lista) return base;
    var attesi = D.sezione === 'dispensa' ? [6, 7] : [lista.length];
    var liste = doc.querySelectorAll('[data-baseweb="tab-list"]');
    for (var k = 0; k < liste.length; k++) {
      var tabs = liste[k].querySelectorAll('[role="tab"]'), n = tabs.length;
      if (attesi.indexOf(n) < 0) continue;
      var idx = -1; for (var i = 0; i < n; i++) if (tabs[i].getAttribute('aria-selected') === 'true') idx = i;
      if (idx <= 0) return base;
      var nomi = lista.slice(); if (D.sezione === 'dispensa' && n === 6) nomi.splice(3, 1);
      return nomi[idx] ? D.sezione + ':' + nomi[idx] : base;
    }
    return base;
  }
  function capitoloSezione(sez) { var t = D.tour || []; for (var i = 0; i < t.length; i++) if (t[i].s === sez) return i; return -1; }
  function guidaCtx() {
    var c = ctxAttuale(), id = D.ctxmap[c] || D.ctxmap[D.sezione] || D.ctxmap.dispensa;
    if (lingua !== (D.applang || 'it')) { var i = capitoloSezione(D.sezione); if (i >= 0) return vociGiro()[i]; }     /* in un'altra lingua: il capitolo tradotto della sezione */
    return voceGuida(id) || (capitoloSezione(D.sezione) >= 0 ? vociGiro()[capitoloSezione(D.sezione)] : null);
  }
  function paginaCorrente(parlare) {
    var g = guidaCtx(); if (!g) return;
    modoGiro(false); tourIdx = -1;
    var corto = perVoce(g.b); if (corto.length > 900) corto = corto.slice(0, 900).replace(/[^.!?؟]*$/, '') || corto.slice(0, 900);
    mostra(g.t, g.b + '\n\n' + T('a_vedi'), corto, parlare);
    chips(argomentiSezione(g.id));
  }
  function novita() {
    modoGiro(false); tourIdx = -1; chips([]);
    if (!D.novita.length) { mostra(T('a_nov_none_t'), T('a_nov_none_x')); return; }
    var testo = D.novita.map(function (n) { return '**' + n.i + ' ' + n.t + '**\n📍 ' + n.d; }).join('\n\n');
    var voceT = T('a_nov_voce') + ' ' + D.novita.map(function (n) { return n.t + '. ' + T('a_nov_trovi') + ' ' + n.d + '.'; }).join(' ');
    mostra(T('a_nov_t'), testo, voceT);
  }

  /* ---------- il giro completo: capitoli, pausa, avanti da solo, frase evidenziata ---------- */
  function modoGiro(on) { elTour.style.display = on ? 'grid' : 'none'; $('.asst-azioni').style.display = on ? 'none' : 'grid'; }   /* durante il giro i 4 pulsanti grandi si nascondono: più spazio al testo */
  function tourVai(i) {
    ferma(); inPausa = false; chips([]); elInput.value = '';
    tourIdx = Math.max(0, Math.min(D.tour.length - 1, i));
    modoGiro(true); elNum.textContent = (tourIdx + 1) + ' / ' + D.tour.length; elBarra.style.width = Math.round((tourIdx + 1) * 100 / D.tour.length) + '%';
    aggiornaVoceBtn();
    var c = D.tour[tourIdx], pezzi = spezza(perVoce(c.x));
    var html = pezzi.map(function (p) { return '<span class="asst-fr">' + esc(p) + '</span>'; }).join(' ');
    if (c.d) html += '<span class="asst-dove">📍 <b>' + esc(T('a_dove')) + '</b> ' + esc(c.d) + '</span>';
    elTitolo.textContent = c.t; elTesto.innerHTML = html; $('.asst-bolla').scrollTop = 0;
    if (tourIdx === 0) { elRobot.classList.add('saluta'); w.setTimeout(function () { elRobot.classList.remove('saluta'); }, 2400); }
    var daDire = [c.t].concat(pezzi); if (c.d) daDire.push(T('a_dove') + ' ' + perVoce(c.d));
    var evid = [-1].concat(pezzi.map(function (_p, k) { return k; })); if (c.d) evid.push(-1);
    /* le frasi evidenziate seguono la voce: il titolo e il «dove» non sono evidenziati */
    var mia = serie + 1;
    parlaPezzi(daDire, evid, function (ok) {
      if (!ok || mia !== serie || tourIdx < 0) return;
      if (voceOn && autoOn && SS) { timerAuto = w.setTimeout(function () { timerAuto = null; if (tourIdx >= D.tour.length - 1) tourFine(); else tourVai(tourIdx + 1); }, 1400); }
    });
  }
  function parlaPezzi(pezzi, evid, alFine) {
    ferma(); var mia = serie, guasto = false;
    if (!SS || !voceOn) { if (alFine) w.setTimeout(function () { if (mia === serie) alFine(false); }, 0); return; }
    var i = 0, voce = scegliVoce();
    function dici() {
      if (mia !== serie) return;
      if (i >= pezzi.length) { elRobot.classList.remove('parla'); evidenzia(-1); if (alFine) alFine(!guasto); return; }
      var idx = i, u = new w.SpeechSynthesisUtterance(pezzi[i++]); u.lang = D.lang || 'it-IT'; u.rate = velocita(); u.pitch = 1.05;
      if (voce) u.voice = voce;
      u.onstart = function () { if (mia === serie) evidenzia(evid[idx]); };
      u.onend = dici; u.onerror = function (e) { if (mia !== serie) return; if (e && (e.error === 'interrupted' || e.error === 'canceled')) return; guasto = true; dici(); };   /* la voce non va: finisco di mostrare, ma non vado avanti da solo */
      elRobot.classList.add('parla'); evidenzia(evid[idx]); SS.speak(u);
    }
    dici();
  }
  function tourPausa() {
    if (tourIdx < 0) return;
    if (!inPausa) { inPausa = true; ferma(); } else { inPausa = false; tourVai(tourIdx); }
    aggiornaVoceBtn();
  }
  function tourCapitoli() {
    elSugg.innerHTML = '';
    (D.tour || []).forEach(function (c, i) {
      var b = doc.createElement('button'); b.textContent = (i + 1) + '. ' + c.t; b.className = 'asst-lg' + (i === tourIdx ? ' ora' : '');
      b.addEventListener('click', function () { tourVai(i); }); elSugg.appendChild(b);
    });
    try { elSugg.scrollIntoView({block: 'nearest', behavior: 'smooth'}); } catch (e) {}
  }
  function tourFine() { modoGiro(false); tourIdx = -1; inPausa = false; ferma(); mostra(T('a_fine_t'), T('a_fine_x')); chips(argomentiSezione()); }
  function scegliLingua() {
    ferma(); modoGiro(false); tourIdx = -1;
    mostra(T('a_lingua_t'), T('a_lingua_x'));
    elSugg.innerHTML = '';
    Object.keys(D.lingue || {}).forEach(function (cod) {
      var b = doc.createElement('button'); b.textContent = D.lingue[cod].nome; b.className = 'asst-lg' + (cod === lingua ? ' ora' : '');
      b.addEventListener('click', function () { cambiaLingua(cod); }); elSugg.appendChild(b);
    });
  }
  function cambiaLingua(cod) {
    if (!D.lingue || !D.lingue[cod]) return;
    lingua = cod; scrivi('asst_lingua', cod); applicaLingua(); applicaUI(); chips([]);
    mostra(D.lingue[cod].nome, T('a_lingua_ok'), null, true, function () {});
    chipsTesto([[T('a_giro'), '__giro__']]);
  }
  function ascolta() {
    if (!SR) { mostra(T('a_mic_t'), T('a_mic_no')); return; }
    if (riconoscimento) { try { riconoscimento.stop(); } catch (e) {} return; }
    ferma();
    var r = new SR(); riconoscimento = r; r.lang = D.lang || 'it-IT'; r.interimResults = false; r.maxAlternatives = 1;
    btnMic.classList.add('ascolta'); elRobot.classList.add('ascolta'); btnMic.textContent = T('a_ascolto_btn');
    mostra(T('a_ascolto_t'), T('a_ascolto_x'), ' ', false);
    var detto = false;
    function fine() { riconoscimento = null; btnMic.classList.remove('ascolta'); elRobot.classList.remove('ascolta'); btnMic.textContent = T('a_mic'); }
    r.onresult = function (e) { detto = true; var t = e.results[0][0].transcript; fine(); elInput.value = t; chiedi(t); };
    r.onerror = function (e) {
      fine(); detto = true;
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') mostra(T('a_mic_t'), T('a_mic_perm'), ' ', false);
      else if (e.error === 'no-speech') mostra(T('a_nulla_t'), T('a_nulla_x'), ' ', false);
      else mostra(T('a_mic_t'), T('a_mic_err'), ' ', false);
    };
    r.onend = function () { if (!detto) { fine(); mostra(T('a_nulla_t'), T('a_nulla_x'), ' ', false); } else { fine(); } };
    try { r.start(); } catch (e) { fine(); }
  }
  function haParola(n, lista) { return String(lista || '').split(' ').some(function (x) { x = norm(x).trim(); return x && n.indexOf(x) >= 0; }); }
  /* ---------- intelligenza artificiale (facoltativa, solo quando app e robottino sono in italiano) ---------- */
  var storia = [], inAttesa = null;
  function ricorda(q, r) { storia.push({r: 'u', t: q}, {r: 'a', t: String(r || '').slice(0, 700)}); if (storia.length > 12) storia = storia.slice(-12); }
  function mandaAlModello(inp, valore) {
    var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, valore);
    inp.dispatchEvent(new w.Event('input', {bubbles: true}));
    inp.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
    inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
  }
  function chiedi(testo) {
    testo = (testo || '').trim();
    if (testo === '__giro__') { elInput.value = ''; tourVai(0); return; }
    var A = D.ai, n0 = ' ' + norm(testo) + ' ';
    var speciale = !testo || (haParola(n0, T('i_off')) && haParola(n0, T('i_ass'))) || haParola(n0, T('i_silenzio')) || haParola(n0, T('i_novita')) || haParola(n0, T('i_giro')) ||
      (n0.trim().split(' ').length <= 3 && haParola(n0, T('i_saluto')));
    var inp = A && A.attivo && /^it/i.test(D.lang || 'it') && lingua === (D.applang || 'it') && !speciale ? doc.querySelector('input[aria-label="asst-llm-q"]') : null;
    if (!inp) { chiediLocale(testo); ricorda(testo, elTitolo.textContent + '. ' + elTesto.textContent); return; }
    var it = rileva(testo); if (it.az) memoria.az = it.az; if (it.og) memoria.og = it.og;
    var id = String(Date.now()) + String(Math.floor(Math.random() * 1000));
    if (inAttesa) w.clearTimeout(inAttesa.t);
    inAttesa = {id: id, testo: testo, t: w.setTimeout(function () {
      if (inAttesa && inAttesa.id === id) { var q = inAttesa.testo; inAttesa = null; chiediLocale(q); ricorda(q, elTitolo.textContent + '. ' + elTesto.textContent); }
    }, A.timeout || 35000)};
    mostra('💭 ' + (A.pensando || ''), A.attendi || '', ' ', false);
    chips([]);
    mandaAlModello(inp, JSON.stringify({id: id, q: testo.slice(0, 500), h: storia.slice(-6)}));
  }
  function rispostaModello(r) {
    if (!inAttesa || !r || r.id !== inAttesa.id) return;
    w.clearTimeout(inAttesa.t);
    var q = inAttesa.testo; inAttesa = null;
    if (r.ok && r.testo) {
      mostra('💬 ' + ((D.ai && D.ai.titolo) || ''), r.testo, perVoce(r.testo).slice(0, 700));
      ricorda(q, r.testo);
      chips(argomentiSezione());
    } else { chiediLocale(q); ricorda(q, elTitolo.textContent + '. ' + elTesto.textContent); }
  }
  function chiediLocale(testo) {
    testo = (testo || '').trim(); if (!testo) { mostra(T('a_dimmi_t'), T('a_dimmi_x'), ' ', false); return; }
    var n = norm(testo);
    if (haParola(n, T('i_off')) && haParola(n, T('i_ass'))) { mostra(T('a_off_t'), T('a_off_x')); chips([]); return; }
    if (haParola(n, T('i_silenzio'))) { ferma(); return; }
    if (haParola(n, T('i_novita'))) { novita(); return; }
    if (haParola(n, T('i_giro'))) { tourVai(0); return; }
    if (n.trim().split(' ').length <= 3 && haParola(n, T('i_saluto'))) { paginaCorrente(true); return; }
    var italiano = /^it/i.test(D.lang || 'it') && lingua === (D.applang || 'it'), it = italiano ? rileva(testo) : {az: null, og: null};
    var og = it.og || ((it.az && memoria.og) ? memoria.og : null), az = it.az;
    var verbi = {elimina: 'eliminare', aggiungi: 'aggiungere', modifica: 'modificare', vedi: 'vedere', condividi: 'inviare', esporta: 'esportare', recupera: 'recuperare'};
    var nomi = {medicinale: 'un medicinale', terapia: 'una terapia', prescrizione: 'una prescrizione', visita: 'una visita o un esame',
                vaccino: 'una vaccinazione', documento: 'un documento', profilo: 'una persona', foto: 'una foto', bugiardino: 'il bugiardino'};
    if (italiano && az && !og && !/(foglio|sbaglio|whatsapp|email|mail|telegram|sms|pdf|excel)/.test(n)) {
      mostra('Su cosa?', 'Certo, ti aiuto a ' + (verbi[az] || 'farlo') + '. Dimmi **su cosa**: scegli qui sotto.');
      chipsTesto(['medicinale', 'terapia', 'prescrizione', 'visita', 'vaccino', 'documento'].map(function (o) { return [nomi[o].replace(/^(un|una|il) /, ''), (verbi[az] || '') + ' ' + o]; }));
      memoria.az = az; return;
    }
    if (italiano && og && !az && n.trim().split(' ').length <= 3 && nomi[og]) {
      mostra('Cosa vuoi fare?', 'Vuoi **aggiungere**, **modificare**, **eliminare** o **inviare** ' + nomi[og] + '? Scegli qui sotto, oppure scrivimelo.');
      chipsTesto([['Aggiungere', 'aggiungere ' + og], ['Modificare', 'modificare ' + og], ['Eliminare', 'eliminare ' + og], ['Inviare', 'inviare ' + og]]);
      memoria.og = og; return;
    }
    var ris = cerca(testo, italiano ? {az: az, og: og} : null);
    if (!ris.length) { mostra(T('a_trov_t'), T('a_trov_x')); chips(argomentiSezione()); return; }
    var guaio = italiano && /(non riesco|non funziona|errore|problema|aiuto|non trovo|non capisco|sbagli)/.test(n);
    var prefisso = guaio ? 'Mi dispiace per il disagio, vediamo subito insieme.\n\n' : '';
    if (az) memoria.az = az;
    if (og) memoria.og = og;
    argomento(ris[0], undefined, prefisso); chips(ris.slice(1));
  }
  function apri() {
    if (!attivo) return; aperto = true; pan.style.display = 'block'; btn.style.display = 'none';
    ctxCorrente = ctxAttuale();
    if (leggi('asst_primo', '') !== '1') {                      /* la prima volta: l'invito al giro completo */
      scrivi('asst_primo', '1'); modoGiro(false); tourIdx = -1;
      mostra(T('a_primo_t'), T('a_primo_x'));
      elSugg.innerHTML = ''; var b = doc.createElement('button'); b.textContent = T('a_primo_btn'); b.className = 'asst-grande';
      b.addEventListener('click', function () { tourVai(0); }); elSugg.appendChild(b);
      return;
    }
    paginaCorrente(true);
  }
  function chiudi() { aperto = false; pan.style.display = 'none'; ferma(); tourIdx = -1; modoGiro(false); if (riconoscimento) { try { riconoscimento.abort(); } catch (e) {} } if (attivo) btn.style.display = 'block'; }
  function imposta(on) {
    attivo = on; scrivi('asst_attivo', on ? '1' : '0');
    if (!on) { chiudi(); btn.style.display = 'none'; avviso(T('a_toast_off')); }
    else { btn.style.display = aperto ? 'none' : 'block'; avviso(T('a_toast_on')); }
  }
  function giroCompleto() { if (!attivo) imposta(true); aperto = true; pan.style.display = 'block'; btn.style.display = 'none'; scrivi('asst_primo', '1'); tourVai(0); }
  function controllaCtx() {
    var c = ctxAttuale(); if (c === ctxCorrente) return; ctxCorrente = c;
    if (aperto && tourIdx < 0) paginaCorrente(false);
  }

  btn.addEventListener('click', apri);
  pan.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('button') : null; if (!b) return;
    if (b.classList.contains('asst-x')) { chiudi(); return; }
    var az = b.getAttribute('data-az'); if (!az) return;
    if (az === 'pagina') paginaCorrente(true); else if (az === 'giro') tourVai(0); else if (az === 'novita') novita(); else if (az === 'mic') ascolta();
    else if (az === 'avanti') { if (tourIdx >= D.tour.length - 1) tourFine(); else tourVai(tourIdx + 1); }
    else if (az === 'indietro') tourVai(tourIdx - 1); else if (az === 'fine') tourFine(); else if (az === 'pausa') tourPausa(); else if (az === 'capitoli') tourCapitoli();
    else if (az === 'chiedi') chiedi(elInput.value);
    else if (az === 'vel') { var v0 = velocita(), n0 = v0 < 0.9 ? 1 : (v0 > 1.1 ? 0.8 : 1.25); scrivi('asst_rate', String(n0)); aggiornaVoceBtn(); if (SS) parla(T('a_vel_prova')); }
    else if (az === 'voce') { voceOn = !voceOn; scrivi('asst_voce', voceOn ? '1' : '0'); if (!voceOn) ferma(); aggiornaVoceBtn(); }
    else if (az === 'lingua') scegliLingua();
    else if (az === 'silenzio') ferma(); else if (az === 'off') imposta(false);
  });
  elInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); chiedi(elInput.value); } });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && aperto) chiudi(); });
  doc.addEventListener('click', function (e) { if (e.target && e.target.closest && e.target.closest('[role="tab"]')) w.setTimeout(controllaCtx, 350); }, true);
  var osservatore = null;
  try {
    var attesa = null;
    osservatore = new w.MutationObserver(function () { if (attesa) return; attesa = w.setTimeout(function () { attesa = null; controllaCtx(); }, 400); });
    osservatore.observe(doc.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['aria-selected']});
  } catch (e) {}
  if (SS && SS.addEventListener) { try { SS.addEventListener('voiceschanged', function () {}); } catch (e) {} }
  applicaLingua(); applicaUI();
  btn.style.display = attivo ? 'block' : 'none';
  if (D.cmd && D.cmd.az === 'giro') w.setTimeout(giroCompleto, 300);

  w.__assistente = {
    versione: D.versione,
    aggiorna: function (c) {
      var cambiaUI = false;
      ['ui', 'tour', 'lang', 'rtl', 'ctxmap', 'tabs', 'img', 'lingue', 'applang'].forEach(function (k) { if (c[k] !== undefined) { D[k] = c[k]; cambiaUI = true; } });
      if (c.stop) { D.stop = c.stop; stopSet = null; indice = null; }
      if (c.guida) { D.guida = c.guida; indice = null; }
      if (c.novita) D.novita = c.novita;
      if (c.ai !== undefined) D.ai = c.ai;
      if (c.sezione) D.sezione = c.sezione;
      if (c.ctx) D.ctx = c.ctx;
      if (c.lingue || c.applang) { if (!D.lingue[lingua]) lingua = D.applang || 'it'; applicaLingua(); }
      if (cambiaUI) applicaUI();
      if (c.cmd && c.cmd.id && c.cmd.id !== ultimoCmd) { ultimoCmd = c.cmd.id; if (c.cmd.az === 'on') imposta(true); else if (c.cmd.az === 'off') imposta(false); else if (c.cmd.az === 'giro') giroCompleto(); }
      ctxCorrente = ctxAttuale();
      if (aperto && tourIdx < 0) paginaCorrente(false);
    },
    llm: rispostaModello,
    apri: apri, chiudi: chiudi, giro: giroCompleto, lingua: cambiaLingua,
    rimuovi: function () { ferma(); try { if (osservatore) osservatore.disconnect(); } catch (e) {} [btn, pan, toast, st].forEach(function (x) { try { x.parentNode.removeChild(x); } catch (e) {} }); }
  };
  } catch (err) { /* se qualcosa non va, l'app funziona come prima, senza assistente */ }
})();
"""


# ---------------------------------------------------------------------------------------------------------------------
# collegamento all'assistente che già esiste
# ---------------------------------------------------------------------------------------------------------------------
try:
    _JS_ASSISTENTE = _AG_JS                                        # lo script nuovo al posto di quello vecchio (assistente() lo legge al momento)
    _VERSIONE_ASSISTENTE = AG_VERSIONE
    AE_VOCE_OK = True
    AE_RICERCA_OK = True
except Exception:
    pass

try:
    UI_IT.update(AG_UI_IT)
    if "LINGUE_BCP47" in globals():
        LINGUE_BCP47.setdefault("pt", "pt-PT")
    if "_STOP_LANG" in globals():
        _STOP_LANG.setdefault("pt", list(AG_STOP["pt"]))
except Exception:
    pass

if "_config_assistente" in globals() and "_ag_config_prima" not in globals():
    _ag_config_prima = _config_assistente

    def _config_assistente(contesto, completo, cmd):                # noqa: F811
        cfg = _ag_config_prima(contesto, completo, cmd)
        try:
            if completo:
                lg = _lingua_guida() if "_lingua_guida" in globals() else "it"
                cfg["versione"] = AG_VERSIONE
                cfg["applang"] = lg if any(lg == c for c, _n, _b in AG_LINGUE) else "it"
                cfg["lingue"] = ag_config_lingue()
                cfg["tour"] = ag_capitoli(cfg["applang"])
                cfg["ui"] = ag_ui(cfg["applang"])
        except Exception:
            pass
        return cfg


# ---- il pulsante «Fammi il giro completo» in cima alla finestra «📖 Guida e informazioni»
try:
    _ag_dialogo_corpo = getattr(_dialogo_info, "__wrapped__", None)
except NameError:
    _ag_dialogo_corpo = None

if _ag_dialogo_corpo is not None and "_ag_dialogo_fatto" not in globals():
    _ag_dialogo_fatto = True

    @st.dialog(UI_IT.get("dlg_titolo", "📖 Guida e informazioni"), width="large")
    def _dialogo_info(sezione):                                     # noqa: F811
        try:
            if st.button(_u("a_giro_dlg"), key=f"ag_giro_{sezione}", type="primary", width="stretch"):
                st.session_state["_asst_cmd"] = "giro"
                st.rerun()
        except Exception:
            pass
        _ag_dialogo_corpo(sezione)


# ---- la scheda nella guida (pulsante rosso «Clicca per informazioni» → Dispensa)
try:
    if "_gx_aggiungi" in globals():
        _gx_aggiungi("dispensa", "d_giro", "🧭 Il giro completo dell'app (il robottino lo racconta, in 8 lingue)",
                     """**Cos'è:** il robottino ti spiega **tutta l'app**, capitolo per capitolo (Dispensa, Salute, Documenti, Archivio, Casa, Lavoro, Auto, Chat, Utilità, avvisi, Cestino, aiuto), **a voce** e con il testo che si evidenzia mentre parla.

**Come si avvia:** tocca il robottino in basso a destra → **🧭 Giro completo dell'app**. Oppure, in questa finestra, il pulsante in alto **«Fammi il giro completo»**.

**I comandi:** se la voce è accesa il robottino **va avanti da solo**; **⏸ Pausa** lo ferma, **Avanti ▶** e **◀ Indietro** ti muovono, **📑 Capitoli** ti porta dove vuoi, **Fine** chiude. Ogni capitolo dice anche **📍 dove si trova** la cosa.

**Le lingue:** con **🌐 Lingua** scegli italiano, inglese, spagnolo, francese, tedesco, romeno, arabo o **portoghese**. Cambiano la voce, il giro e le risposte del robottino; **l'app resta nella sua lingua**. La scelta resta salvata sul telefono.

**Le domande:** scrivi o dì una domanda (🎤): il robottino risponde con la guida e con i capitoli del giro, nella lingua scelta.""",
                     "giro completo tour robottino assistente lingue portoghese inglese spagnolo francese tedesco romeno arabo voce pausa capitoli spiegazione app", ("vedi", None))
except Exception:
    pass


# ---- la novità
try:
    if not any(n[2].startswith("Giro completo") for n in _NOVITA):
        # dopo le 6 novità originali (che hanno le traduzioni nov1…nov6) e prima di quelle di guida_extra, così compare per prima tra le recenti
        _NOVITA.insert(min(6, len(_NOVITA)), ("2026-11-14", "🧭", "Giro completo dell'app in 8 lingue",
                                              "Tocca il robottino → «🧭 Giro completo dell'app»; con «🌐 Lingua» scegli italiano, inglese, spagnolo, francese, tedesco, romeno, arabo o portoghese"))
except Exception:
    pass
