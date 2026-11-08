# -*- coding: utf-8 -*-
"""PENSIERO DEL GIORNO — una frase al giorno, tra i bottoni delle pagine e il grande tasto rosso delle informazioni, nella Home.

Filosofi, scrittori, poeti, scienziati, artisti, grandi della storia e qualche battuta di film. Ogni giorno ne compare una diversa (uguale per tutti in quella data);
passano tutte, in un ordine mescolato, prima che una si ripeta. Nella raccolta ci sono solo frasi di cui l'autore è documentato (le tante frasi «attribuite» a Einstein, Gandhi,
Twain e altri senza una fonte non ci sono). Le frasi in altre lingue sono traduzioni (le versioni italiane più note). Per aggiungerne: nuove righe in _PENSIERI.
Il tasto «Un altro» mostra la frase successiva; «Invia» la manda come il resto dell'app."""
import html as _h
from datetime import date

import streamlit as st

# (frase, autore, ambito)
_PENSIERI = [
    # --- il mondo antico
    ("Io so di non sapere.", "Socrate", "Filosofia"),
    ("Una vita senza ricerca non vale la pena di essere vissuta.", "Socrate", "Filosofia"),
    ("Conosci te stesso.", "Iscrizione del tempio di Apollo a Delfi", "Saggezza antica"),
    ("Nulla di troppo.", "Iscrizione del tempio di Apollo a Delfi", "Saggezza antica"),
    ("L'inizio è la parte più importante del lavoro.", "Platone", "Filosofia"),
    ("La prima e la più bella delle vittorie è vincere se stessi.", "Platone", "Filosofia"),
    ("L'uomo è per natura un animale sociale e politico.", "Aristotele", "Filosofia"),
    ("Tutti gli uomini per natura desiderano sapere.", "Aristotele", "Filosofia"),
    ("Una rondine non fa primavera.", "Aristotele", "Filosofia"),
    ("Non ci si bagna mai due volte nello stesso fiume.", "Eraclito", "Filosofia"),
    ("Il carattere di un uomo è il suo destino.", "Eraclito", "Filosofia"),
    ("Non si è mai troppo giovani né troppo vecchi per occuparsi della salute dell'anima.", "Epicuro", "Filosofia"),
    ("Non è che abbiamo poco tempo: è che ne perdiamo molto.", "Seneca", "Filosofia"),
    ("Mentre si rimanda, la vita passa.", "Seneca", "Filosofia"),
    ("Non sono le cose in sé a turbare gli uomini, ma le opinioni che hanno delle cose.", "Epitteto", "Filosofia"),
    ("L'anima si tinge del colore dei suoi pensieri.", "Marco Aurelio", "Filosofia"),
    ("Ciò che non giova all'alveare non giova nemmeno all'ape.", "Marco Aurelio", "Filosofia"),
    ("Se hai un giardino e una biblioteca, non ti mancherà nulla.", "Cicerone", "Filosofia"),
    ("La storia è maestra di vita.", "Cicerone", "Storia"),
    ("Sono un uomo: niente di ciò che è umano ritengo estraneo a me.", "Terenzio", "Teatro"),
    ("Una mente sana in un corpo sano.", "Giovenale", "Poesia"),
    ("Cogli il giorno, confidando il meno possibile nel domani.", "Orazio", "Poesia"),
    ("La goccia scava la pietra non con la forza, ma cadendo spesso.", "Ovidio", "Poesia"),
    ("Forse un giorno ci piacerà ricordare anche questo.", "Virgilio", "Poesia"),
    ("Dove fanno il deserto, lo chiamano pace.", "Tacito", "Storia"),
    ("Non esiste libro così cattivo da non avere in sé qualcosa di buono.", "Plinio il Vecchio", "Letteratura"),
    ("La mente non è un vaso da riempire, ma un fuoco da accendere.", "Plutarco", "Filosofia"),
    ("Che cos'è dunque il tempo? Se nessuno me lo chiede, lo so; se voglio spiegarlo a chi me lo chiede, non lo so.", "Sant'Agostino", "Filosofia"),
    ("Imparare senza riflettere è fatica sprecata; riflettere senza imparare è pericoloso.", "Confucio", "Saggezza d'Oriente"),
    ("Un viaggio di mille miglia comincia con il primo passo.", "Lao Tzu", "Saggezza d'Oriente"),
    ("L'odio non cessa mai con l'odio, ma con l'amore: questa è una legge eterna.", "Dhammapada", "Saggezza d'Oriente"),
    ("Navigare è necessario, vivere non è necessario.", "Pompeo (riferito da Plutarco)", "Storia"),
    # --- Medioevo e Rinascimento
    ("Fatti non foste a viver come bruti, ma per seguir virtute e canoscenza.", "Dante Alighieri", "Poesia"),
    ("Amor, ch'a nullo amato amar perdona.", "Dante Alighieri", "Poesia"),
    ("Non ragioniam di lor, ma guarda e passa.", "Dante Alighieri", "Poesia"),
    ("Umana cosa è aver compassione degli afflitti.", "Giovanni Boccaccio", "Letteratura"),
    ("L'esperienza non falla mai: falliscono soltanto i nostri giudizi.", "Leonardo da Vinci", "Arte e scienza"),
    ("Come una giornata bene spesa dà lieto dormire, così una vita bene usata dà lieto morire.", "Leonardo da Vinci", "Arte e scienza"),
    ("Chi non punisce il male, comanda che si faccia.", "Leonardo da Vinci", "Arte e scienza"),
    ("Gli uomini giudicano più con gli occhi che con le mani.", "Niccolò Machiavelli", "Politica"),
    ("Chi legge molto e cammina molto, vede molto e sa molto.", "Miguel de Cervantes", "Letteratura"),
    ("Che so io?", "Michel de Montaigne", "Filosofia"),
    ("Sapere è potere.", "Francis Bacon", "Filosofia"),
    ("Il grandissimo libro della natura è scritto in lingua matematica.", "Galileo Galilei", "Scienza"),
    ("Datemi un punto d'appoggio e solleverò il mondo.", "Archimede", "Scienza"),
    ("Essere o non essere: questo è il dilemma.", "William Shakespeare", "Teatro"),
    ("Siamo fatti della stessa sostanza dei sogni.", "William Shakespeare", "Teatro"),
    ("C'è del metodo in questa follia.", "William Shakespeare", "Teatro"),
    # --- Seicento e Settecento
    ("Penso, dunque sono.", "René Descartes", "Filosofia"),
    ("Il cuore ha le sue ragioni, che la ragione non conosce.", "Blaise Pascal", "Filosofia"),
    ("Tutta l'infelicità degli uomini viene da una sola cosa: non saper stare tranquilli in una stanza.", "Blaise Pascal", "Filosofia"),
    ("L'uomo non è che una canna, la più fragile della natura; ma è una canna che pensa.", "Blaise Pascal", "Filosofia"),
    ("Non ridere, non lamentarsi, non detestare, ma comprendere.", "Baruch Spinoza", "Filosofia"),
    ("Se ho visto più lontano, è perché stavo sulle spalle di giganti.", "Isaac Newton", "Scienza"),
    ("Il dubbio non è una condizione piacevole, ma la certezza è assurda.", "Voltaire", "Filosofia"),
    ("L'uomo è nato libero, e ovunque è in catene.", "Jean-Jacques Rousseau", "Filosofia"),
    ("La ragione è, e deve essere, schiava delle passioni.", "David Hume", "Filosofia"),
    ("Sapere aude: abbi il coraggio di servirti della tua propria intelligenza.", "Immanuel Kant", "Filosofia"),
    ("Due cose riempiono l'animo di ammirazione: il cielo stellato sopra di me e la legge morale dentro di me.", "Immanuel Kant", "Filosofia"),
    ("Il pensare è più interessante del sapere, ma meno interessante del guardare.", "Johann Wolfgang Goethe", "Letteratura"),
    ("Non basta sapere, bisogna anche applicare; non basta volere, bisogna anche fare.", "Johann Wolfgang Goethe", "Letteratura"),
    # --- Ottocento
    ("Il vero è l'intero.", "Georg W. F. Hegel", "Filosofia"),
    ("La vita può essere compresa solo all'indietro, ma va vissuta in avanti.", "Søren Kierkegaard", "Filosofia"),
    ("Il talento colpisce un bersaglio che nessun altro riesce a colpire; il genio ne colpisce uno che nessun altro riesce a vedere.", "Arthur Schopenhauer", "Filosofia"),
    ("Ciò che non mi uccide mi rende più forte.", "Friedrich Nietzsche", "Filosofia"),
    ("Chi ha un perché abbastanza forte può sopportare quasi ogni come.", "Friedrich Nietzsche", "Filosofia"),
    ("Bisogna avere ancora il caos dentro di sé per partorire una stella danzante.", "Friedrich Nietzsche", "Filosofia"),
    ("A egregie cose il forte animo accendono l'urne dei forti.", "Ugo Foscolo", "Poesia"),
    ("E il naufragar m'è dolce in questo mare.", "Giacomo Leopardi", "Poesia"),
    ("Il buon senso c'era; ma se ne stava nascosto, per paura del senso comune.", "Alessandro Manzoni", "Letteratura"),
    ("Era il migliore dei tempi, era il peggiore dei tempi.", "Charles Dickens", "Letteratura"),
    ("Chiamatemi Ismaele.", "Herman Melville", "Letteratura"),
    ("La maggior parte degli uomini conduce una vita di tranquilla disperazione.", "Henry David Thoreau", "Letteratura"),
    ("Nulla di grande è mai stato realizzato senza entusiasmo.", "Ralph Waldo Emerson", "Filosofia"),
    ("La speranza è quella cosa piumata che si posa sull'anima.", "Emily Dickinson", "Poesia"),
    ("Non c'è nulla al mondo di più potente di un'idea il cui momento è arrivato.", "Victor Hugo", "Letteratura"),
    ("La bellezza salverà il mondo.", "Fëdor Dostoevskij", "Letteratura"),
    ("Il segreto dell'esistenza umana non sta soltanto nel vivere, ma nel sapere per che cosa si vive.", "Fëdor Dostoevskij", "Letteratura"),
    ("Tutte le famiglie felici si somigliano; ogni famiglia infelice lo è a modo suo.", "Lev Tolstoj", "Letteratura"),
    ("La brevità è sorella del talento.", "Anton Čechov", "Letteratura"),
    ("Nei campi dell'osservazione il caso favorisce solo le menti preparate.", "Louis Pasteur", "Scienza"),
    ("L'esperienza è il nome che ognuno dà ai propri errori.", "Oscar Wilde", "Letteratura"),
    ("Non c'è cammino: il cammino si fa camminando.", "Antonio Machado", "Poesia"),
    ("Sventurata la terra che ha bisogno di eroi.", "Bertolt Brecht", "Teatro"),
    # --- Novecento: filosofia, letteratura, poesia
    ("Il vero viaggio di scoperta non consiste nel cercare nuove terre, ma nell'avere nuovi occhi.", "Marcel Proust", "Letteratura"),
    ("Un libro dev'essere l'ascia che spezza il mare di ghiaccio dentro di noi.", "Franz Kafka", "Letteratura"),
    ("Una donna, se vuole scrivere, deve avere del denaro e una stanza tutta per sé.", "Virginia Woolf", "Letteratura"),
    ("Non tutti quelli che vagano si sono perduti.", "J. R. R. Tolkien", "Letteratura"),
    ("Un uomo può essere distrutto, ma non sconfitto.", "Ernest Hemingway", "Letteratura"),
    ("Chi controlla il passato controlla il futuro; chi controlla il presente controlla il passato.", "George Orwell", "Letteratura"),
    ("La libertà è poter dire che due più due fa quattro.", "George Orwell", "Letteratura"),
    ("L'essenziale è invisibile agli occhi.", "Antoine de Saint-Exupéry", "Letteratura"),
    ("Sei responsabile per sempre di ciò che hai addomesticato.", "Antoine de Saint-Exupéry", "Letteratura"),
    ("Ho sempre immaginato che il Paradiso sarebbe una specie di biblioteca.", "Jorge Luis Borges", "Letteratura"),
    ("Dopo il silenzio, ciò che più si avvicina all'esprimere l'inesprimibile è la musica.", "Aldous Huxley", "Letteratura"),
    ("Bisogna vivere le domande.", "Rainer Maria Rilke", "Poesia"),
    ("Abbiate pazienza verso tutto ciò che è irrisolto nel vostro cuore, e cercate di amare le domande stesse.", "Rainer Maria Rilke", "Poesia"),
    ("I vostri figli non sono i vostri figli: sono i figli e le figlie della sete che la vita ha di se stessa.", "Kahlil Gibran", "Poesia"),
    ("Ogni bambino che nasce ci porta il messaggio che Dio non è ancora stanco degli uomini.", "Rabindranath Tagore", "Poesia"),
    ("I limiti del mio linguaggio significano i limiti del mio mondo.", "Ludwig Wittgenstein", "Filosofia"),
    ("Il problema dell'umanità è che gli stupidi sono sicurissimi di tutto e gli intelligenti pieni di dubbi.", "Bertrand Russell", "Filosofia"),
    ("Il nostro sapere può essere soltanto finito, mentre la nostra ignoranza deve essere necessariamente infinita.", "Karl Popper", "Filosofia"),
    ("L'esistenza precede l'essenza.", "Jean-Paul Sartre", "Filosofia"),
    ("Bisogna immaginare Sisifo felice.", "Albert Camus", "Filosofia"),
    ("Nel mezzo dell'inverno ho scoperto in me un'invincibile estate.", "Albert Camus", "Filosofia"),
    ("Non si nasce donna: lo si diventa.", "Simone de Beauvoir", "Filosofia"),
    ("Un classico è un libro che non ha mai finito di dire quel che ha da dire.", "Italo Calvino", "Letteratura"),
    ("Se comprendere è impossibile, conoscere è necessario.", "Primo Levi", "Letteratura"),
    ("Chi non legge, a settant'anni avrà vissuto una sola vita: la propria. Chi legge avrà vissuto cinquemila anni.", "Umberto Eco", "Letteratura"),
    ("Non ricordiamo giorni, ricordiamo momenti.", "Cesare Pavese", "Letteratura"),
    ("L'uomo mortale non ha che questo d'immortale: il ricordo che porta e il ricordo che lascia.", "Cesare Pavese", "Letteratura"),
    ("M'illumino d'immenso.", "Giuseppe Ungaretti", "Poesia"),
    ("Si sta come d'autunno sugli alberi le foglie.", "Giuseppe Ungaretti", "Poesia"),
    ("Spesso il male di vivere ho incontrato.", "Eugenio Montale", "Poesia"),
    ("Codesto solo oggi possiamo dirti: ciò che non siamo, ciò che non vogliamo.", "Eugenio Montale", "Poesia"),
    ("Ognuno sta solo sul cuor della terra, trafitto da un raggio di sole: ed è subito sera.", "Salvatore Quasimodo", "Poesia"),
    ("I poeti lavorano di notte, quando il tempo non urge su di loro.", "Alda Merini", "Poesia"),
    ("I care: mi importa, mi sta a cuore.", "Don Lorenzo Milani", "Educazione"),
    ("Aiutami a fare da solo.", "Maria Montessori", "Educazione"),
    ("Istruitevi, perché avremo bisogno di tutta la vostra intelligenza.", "Antonio Gramsci", "Politica"),
    ("La libertà è come l'aria: ci si accorge di quanto vale quando comincia a mancare.", "Piero Calamandrei", "Politica"),
    ("I giovani non hanno bisogno di sermoni: hanno bisogno di esempi di onestà, di coerenza e di altruismo.", "Sandro Pertini", "Politica"),
    ("Gli uomini passano, le idee restano.", "Giovanni Falcone", "Impegno civile"),
    ("È bello morire per ciò in cui si crede; chi ha paura muore ogni giorno, chi non ha paura muore una volta sola.", "Paolo Borsellino", "Impegno civile"),
    ("La mafia sarà vinta da un esercito di maestri elementari.", "Gesualdo Bufalino", "Impegno civile"),
    # --- scienza e conoscenza
    ("L'immaginazione è più importante della conoscenza.", "Albert Einstein", "Scienza"),
    ("La cosa più incomprensibile dell'universo è che sia comprensibile.", "Albert Einstein", "Scienza"),
    ("L'importante è non smettere mai di domandarsi.", "Albert Einstein", "Scienza"),
    ("Un uomo che osa sprecare un'ora di tempo non ha scoperto il valore della vita.", "Charles Darwin", "Scienza"),
    ("La prima regola è non ingannare te stesso: e tu sei la persona più facile da ingannare.", "Richard Feynman", "Scienza"),
    ("Siamo fatti della stessa materia delle stelle.", "Carl Sagan", "Scienza"),
    ("Ricordati di guardare le stelle e non i tuoi piedi.", "Stephen Hawking", "Scienza"),
    ("Il corpo faccia ciò che vuole: io non sono il corpo, io sono la mente.", "Rita Levi-Montalcini", "Scienza"),
    ("Siate affamati, siate folli.", "Steve Jobs (discorso a Stanford, 2005)", "Innovazione"),
    # --- grandi della storia
    ("Ho un sogno: che i miei quattro figli piccoli vivranno un giorno in una nazione dove non saranno giudicati per il colore della pelle, ma per il contenuto del loro carattere.", "Martin Luther King", "Storia"),
    ("L'istruzione è l'arma più potente che puoi usare per cambiare il mondo.", "Nelson Mandela", "Storia"),
    ("Sembra sempre impossibile, finché non viene fatto.", "Nelson Mandela", "Storia"),
    ("La mia vita è il mio messaggio.", "Mohandas Gandhi", "Storia"),
    ("Non chiederti che cosa il tuo paese può fare per te: chiediti che cosa puoi fare tu per il tuo paese.", "John F. Kennedy", "Storia"),
    ("L'unica cosa di cui dobbiamo avere paura è la paura stessa.", "Franklin D. Roosevelt", "Storia"),
    ("Non ho altro da offrire che sangue, fatica, lacrime e sudore.", "Winston Churchill", "Storia"),
    # --- proverbi e saggezza popolare
    ("Chi va piano va sano e va lontano.", "Proverbio", "Saggezza popolare"),
    ("Il mattino ha l'oro in bocca.", "Proverbio", "Saggezza popolare"),
    ("Non c'è rosa senza spine.", "Proverbio", "Saggezza popolare"),
    ("Dopo la pioggia viene il sereno.", "Proverbio", "Saggezza popolare"),
    ("L'abitudine è una seconda natura.", "Proverbio", "Saggezza popolare"),
    ("Chi cerca trova.", "Proverbio", "Saggezza popolare"),
    # --- il cinema
    ("Carpe diem. Cogliete l'attimo, ragazzi.", "L'attimo fuggente (1989)", "Cinema"),
    ("La vita è come una scatola di cioccolatini: non sai mai quello che ti capita.", "Forrest Gump (1994)", "Cinema"),
    ("Dopotutto, domani è un altro giorno.", "Via col vento (1939)", "Cinema"),
    ("Non c'è posto come casa.", "Il mago di Oz (1939)", "Cinema"),
    ("La speranza è una cosa buona, forse la migliore, e le cose buone non muoiono mai.", "Le ali della libertà (1994)", "Cinema"),
    ("Ciò che facciamo in vita riecheggia nell'eternità.", "Il gladiatore (2000)", "Cinema"),
    ("Anche la più piccola persona può cambiare il corso del futuro.", "Il Signore degli Anelli (2001)", "Cinema"),
    ("La poesia non è di chi la scrive, ma di chi gli serve.", "Il postino (1994)", "Cinema"),
    ("Qualunque cosa farai, amala.", "Nuovo Cinema Paradiso (1988)", "Cinema"),
    ("Houston, abbiamo un problema.", "Apollo 13 (1995)", "Cinema"),
    ("Buongiorno, principessa!", "La vita è bella (1997)", "Cinema"),
    # --- altre voci
    ("Sempre caro mi fu quest'ermo colle.", "Giacomo Leopardi", "Poesia"),
    ("Pace non trovo, et non ò da far guerra.", "Francesco Petrarca", "Poesia"),
    ("Le donne, i cavalier, l'arme, gli amori, le cortesie, l'audaci imprese io canto.", "Ludovico Ariosto", "Poesia"),
    ("Il coraggio, uno, se non ce l'ha, non se lo può dare.", "Alessandro Manzoni", "Letteratura"),
    ("Adelante, Pedro, con juicio, si puedes.", "Alessandro Manzoni", "Letteratura"),
    ("Le bugie hanno le gambe corte.", "Carlo Collodi", "Letteratura"),
    ("Se vogliamo che tutto rimanga com'è, bisogna che tutto cambi.", "Giuseppe Tomasi di Lampedusa", "Letteratura"),
    ("La vita non è né brutta né bella, ma è originale!", "Italo Svevo", "Letteratura"),
    ("Gli esami non finiscono mai.", "Eduardo De Filippo", "Teatro"),
    ("Ha da passà 'a nuttata.", "Eduardo De Filippo", "Teatro"),
    ("Memento audere semper: ricordati di osare sempre.", "Gabriele D'Annunzio", "Letteratura"),
    ("Resisto a tutto, tranne alle tentazioni.", "Oscar Wilde", "Letteratura"),
    ("Il mondo non perirà per mancanza di meraviglie, ma per mancanza di meraviglia.", "G. K. Chesterton", "Letteratura"),
    ("Il riso è il sole che scaccia l'inverno dal volto umano.", "Victor Hugo", "Letteratura"),
    ("Sii regolare e ordinato nella tua vita, come un borghese, per poter essere violento e originale nelle tue opere.", "Gustave Flaubert", "Letteratura"),
    ("Bisogna essere assolutamente moderni.", "Arthur Rimbaud", "Poesia"),
    ("Senza la musica la vita sarebbe un errore.", "Friedrich Nietzsche", "Filosofia"),
    ("Dove si bruciano i libri, si finisce per bruciare anche gli uomini.", "Heinrich Heine", "Letteratura"),
    ("Chi guarda fuori sogna, chi guarda dentro si sveglia.", "Carl Gustav Jung", "Filosofia"),
    ("Se il naso di Cleopatra fosse stato più corto, tutta la faccia della terra sarebbe cambiata.", "Blaise Pascal", "Filosofia"),
    ("Chi soffre impara.", "Eschilo", "Teatro"),
    ("Il segreto della felicità è la libertà, il segreto della libertà è il coraggio.", "Tucidide (discorso di Pericle)", "Storia"),
    ("Non pretendere che gli eventi accadano come vuoi: desidera che accadano come accadono, e la tua vita scorrerà serena.", "Epitteto", "Filosofia"),
    ("Il destino guida chi acconsente, trascina chi si oppone.", "Seneca", "Filosofia"),
    ("Non c'è vento favorevole per chi non sa dove andare.", "Seneca", "Filosofia"),
    ("O tempora, o mores!", "Cicerone", "Storia"),
    ("Il dado è tratto.", "Giulio Cesare (riferito da Svetonio)", "Storia"),
    ("La concordia fa crescere le piccole cose, la discordia manda in rovina le più grandi.", "Sallustio", "Storia"),
    ("La musica è la stenografia del sentimento.", "Lev Tolstoj", "Letteratura"),
    ("Se senti una voce dentro di te che dice «non puoi dipingere», allora dipingi, e quella voce sarà messa a tacere.", "Vincent van Gogh", "Arte e scienza"),
    ("Piedi, perché li voglio, se ho ali per volare?", "Frida Kahlo", "Arte e scienza"),
    ("Il problema degli stereotipi non è che siano falsi, ma che sono incompleti.", "Chimamanda Ngozi Adichie", "Letteratura"),
    ("Un bambino, un insegnante, un libro e una penna possono cambiare il mondo.", "Malala Yousafzai", "Educazione"),
    ("È il tempo che hai perduto per la tua rosa che ha fatto la tua rosa così importante.", "Antoine de Saint-Exupéry", "Letteratura"),
    ("Seconda stella a destra, e poi dritto fino al mattino.", "James M. Barrie, Peter Pan", "Letteratura"),
    ("Se non sai dove vuoi andare, non importa quale strada prendi.", "Lewis Carroll, Alice nel Paese delle Meraviglie", "Letteratura"),
    ("Il tempo è denaro.", "Benjamin Franklin", "Storia"),
    ("Si può trovare la felicità anche nei momenti più bui, se solo uno si ricorda di accendere la luce.", "Harry Potter e il prigioniero di Azkaban (2004)", "Cinema"),
    ("Un grande potere comporta una grande responsabilità.", "Spider-Man (2002)", "Cinema"),
    ("Roma non è stata costruita in un giorno.", "Proverbio", "Saggezza popolare"),
    ("Tra il dire e il fare c'è di mezzo il mare.", "Proverbio", "Saggezza popolare"),
    ("Aiutati, che il ciel t'aiuta.", "Proverbio", "Saggezza popolare"),
    ("L'unione fa la forza.", "Proverbio", "Saggezza popolare"),
    ("Meglio un uovo oggi che una gallina domani.", "Proverbio", "Saggezza popolare"),
    # --- seconda raccolta
    ("Tutto scorre.", "Eraclito", "Filosofia"),
    ("La virtù sta nel mezzo.", "Aristotele", "Filosofia"),
    ("Il meravigliarsi è il tratto distintivo del filosofo.", "Platone", "Filosofia"),
    ("La morte non è nulla per noi.", "Epicuro", "Filosofia"),
    ("Se vuoi essere amato, ama.", "Seneca", "Filosofia"),
    ("Non è povero chi ha poco, ma chi desidera molto.", "Seneca", "Filosofia"),
    ("L'ostacolo sulla via diventa la via.", "Marco Aurelio", "Filosofia"),
    ("La vita dei morti sta nella memoria dei vivi.", "Cicerone", "Storia"),
    ("Viviamo, mia Lesbia, e amiamo.", "Catullo", "Poesia"),
    ("Ricordati di conservare l'animo sereno nelle avversità.", "Orazio", "Poesia"),
    ("Il tempo divora ogni cosa.", "Ovidio", "Poesia"),
    ("Nulla nasce dal nulla.", "Lucrezio", "Filosofia"),
    ("Poca favilla gran fiamma seconda.", "Dante Alighieri", "Poesia"),
    ("E quindi uscimmo a riveder le stelle.", "Dante Alighieri", "Poesia"),
    ("L'amor che move il sole e l'altre stelle.", "Dante Alighieri", "Poesia"),
    ("Quant'è bella giovinezza, che si fugge tuttavia! Chi vuol esser lieto, sia: di doman non c'è certezza.", "Lorenzo de' Medici", "Poesia"),
    ("Amai trite parole che non uno osava.", "Umberto Saba", "Poesia"),
    ("Ostinato rigore.", "Leonardo da Vinci", "Arte e scienza"),
    ("Il moto è causa d'ogni vita.", "Leonardo da Vinci", "Arte e scienza"),
    ("La situazione politica in Italia è grave, ma non è seria.", "Ennio Flaiano", "Letteratura"),
    ("Conoscere per deliberare.", "Luigi Einaudi", "Politica"),
    ("La più grande cosa del mondo è sapere essere di se stessi.", "Michel de Montaigne", "Filosofia"),
    ("Il buon senso è la cosa meglio distribuita del mondo.", "René Descartes", "Filosofia"),
    ("Il migliore dei mondi possibili.", "Gottfried W. Leibniz", "Filosofia"),
    ("La vita oscilla come un pendolo tra il dolore e la noia.", "Arthur Schopenhauer", "Filosofia"),
    ("L'angoscia è la vertigine della libertà.", "Søren Kierkegaard", "Filosofia"),
    ("Diventa ciò che sei.", "Friedrich Nietzsche", "Filosofia"),
    ("Meglio essere un Socrate insoddisfatto che un porco soddisfatto.", "John Stuart Mill", "Filosofia"),
    ("I filosofi hanno soltanto interpretato il mondo; si tratta di cambiarlo.", "Karl Marx", "Filosofia"),
    ("Ai fatti stessi!", "Edmund Husserl", "Filosofia"),
    ("Il più profondo principio della natura umana è il desiderio di essere apprezzato.", "William James", "Filosofia"),
    ("La filosofia occidentale è una serie di note a margine a Platone.", "Alfred N. Whitehead", "Filosofia"),
    ("Tre passioni, semplici ma irresistibilmente forti, hanno governato la mia vita: il desiderio d'amore, la ricerca della conoscenza e una insopportabile pietà per le sofferenze dell'umanità.", "Bertrand Russell", "Filosofia"),
    ("L'uomo è l'unica creatura che rifiuta di essere ciò che è.", "Albert Camus", "Filosofia"),
    ("L'attenzione è la forma più rara e più pura della generosità.", "Simone Weil", "Filosofia"),
    ("È verità universalmente riconosciuta che uno scapolo in possesso di un'ingente fortuna debba aver bisogno di una moglie.", "Jane Austen", "Letteratura"),
    ("Non sono un uccello, e nessuna rete mi imprigiona: sono un essere umano libero, con una volontà indipendente.", "Charlotte Brontë, Jane Eyre", "Letteratura"),
    ("Io accuso.", "Émile Zola", "Letteratura"),
    ("Attendere e sperare.", "Alexandre Dumas, Il conte di Montecristo", "Letteratura"),
    ("Il sapere si può comunicare, la saggezza no.", "Hermann Hesse, Siddharta", "Letteratura"),
    ("Due anime, ahimè, abitano nel mio petto.", "Johann Wolfgang Goethe, Faust", "Letteratura"),
    ("Aprile è il più crudele dei mesi.", "T. S. Eliot", "Poesia"),
    ("Così continuiamo a remare, barche controcorrente, risospinti senza posa nel passato.", "F. Scott Fitzgerald, Il grande Gatsby", "Letteratura"),
    ("Tutto ciò che vediamo o immaginiamo non è che un sogno entro un sogno.", "Edgar Allan Poe", "Poesia"),
    ("Contengo moltitudini.", "Walt Whitman", "Poesia"),
    ("Due strade divergevano in un bosco, e io… io presi quella meno battuta: e ciò ha fatto tutta la differenza.", "Robert Frost", "Poesia"),
    ("Confesso che ho vissuto.", "Pablo Neruda", "Letteratura"),
    ("Tutto vale la pena se l'anima non è piccola.", "Fernando Pessoa", "Poesia"),
    ("Se puoi guardare, vedi. Se puoi vedere, osserva.", "José Saramago, Saggio sulla cecità", "Letteratura"),
    ("Ho provato. Ho fallito. Non importa. Riprova. Fallisci ancora. Fallisci meglio.", "Samuel Beckett", "Letteratura"),
    ("Coloro che non credono nella magia non la troveranno mai.", "Roald Dahl", "Letteratura"),
    ("Nulla è troppo bello per essere vero, se è in accordo con le leggi della natura.", "Michael Faraday", "Scienza"),
    ("Dubitare di tutto o credere a tutto sono due soluzioni ugualmente comode, che ci dispensano entrambe dal riflettere.", "Henri Poincaré", "Scienza"),
    ("Dobbiamo sapere, e sapremo.", "David Hilbert", "Scienza"),
    ("Possiamo vedere solo poco davanti a noi, ma vediamo molto di ciò che c'è da fare.", "Alan Turing", "Scienza"),
    ("La scienza è più di un corpo di conoscenze: è un modo di pensare.", "Carl Sagan", "Scienza"),
    ("L'oscurità non può scacciare l'oscurità: solo la luce può farlo. L'odio non può scacciare l'odio: solo l'amore può farlo.", "Martin Luther King", "Storia"),
    ("Un governo del popolo, dal popolo, per il popolo.", "Abraham Lincoln", "Storia"),
    ("Libera Chiesa in libero Stato.", "Camillo Benso, conte di Cavour", "Storia"),
    ("Obbedisco.", "Giuseppe Garibaldi", "Storia"),
    ("Qui si fa l'Italia o si muore.", "Giuseppe Garibaldi", "Storia"),
    ("Pensiero e azione.", "Giuseppe Mazzini", "Storia"),
    ("Fatta l'Italia, bisogna fare gli italiani.", "Massimo d'Azeglio", "Storia"),
    ("Il colore è un mezzo per esercitare un'influenza diretta sull'anima.", "Wassily Kandinsky", "Arte e scienza"),
    ("Torniamo all'antico e sarà un progresso.", "Giuseppe Verdi", "Arte e scienza"),
    ("Chi dorme non piglia pesci.", "Proverbio", "Saggezza popolare"),
    ("Non è tutto oro quel che luccica.", "Proverbio", "Saggezza popolare"),
    ("Chi trova un amico trova un tesoro.", "Proverbio", "Saggezza popolare"),
    ("Il tempo è galantuomo.", "Proverbio", "Saggezza popolare"),
    ("La fretta è cattiva consigliera.", "Proverbio", "Saggezza popolare"),
    ("Chi semina vento raccoglie tempesta.", "Proverbio", "Saggezza popolare"),
    ("Tutte le strade portano a Roma.", "Proverbio", "Saggezza popolare"),
    ("Gli faremo un'offerta che non potrà rifiutare.", "Il padrino (1972)", "Cinema"),
    ("Si può fare!", "Frankenstein Junior (1974)", "Cinema"),
    ("Dove andiamo, non c'è bisogno di strade.", "Ritorno al futuro (1985)", "Cinema"),
    ("Verso l'infinito e oltre!", "Toy Story (1995)", "Cinema"),
    ("Continua a nuotare.", "Alla ricerca di Nemo (2003)", "Cinema"),
    ("La vita trova sempre la sua strada.", "Jurassic Park (1993)", "Cinema"),
    ("Com'è umano lei!", "Fantozzi (1975)", "Cinema"),
    ("E.T. telefono casa.", "E.T. l'extra-terrestre (1982)", "Cinema"),
    ("Sono il re del mondo!", "Titanic (1997)", "Cinema"),
]

_ICONE = {"I miei pensieri": "✍️", "Filosofia": "🏛️", "Saggezza antica": "🏺", "Storia": "📜", "Teatro": "🎭", "Poesia": "🪶", "Letteratura": "📖", "Saggezza d'Oriente": "🪷", "Arte e scienza": "🎨",
          "Politica": "⚖️", "Scienza": "🔭", "Educazione": "🎓", "Impegno civile": "🕊️", "Innovazione": "💡", "Saggezza popolare": "🌾", "Cinema": "🎬"}


def pensiero_indice(giorno, spostamento=0, n=None):
    """Quale frase tocca in un giorno: un ordine mescolato che le fa passare tutte prima di ripetere."""
    n = n or len(_PENSIERI)
    return ((giorno.toordinal() + int(spostamento)) * 7919 + 13) % n


def pensiero_miei():
    """Le frasi aggiunte da te: [{id, t, a}]."""
    try:
        return [x for x in (_ca_dati().get("pensieri_miei") or []) if isinstance(x, dict) and str(x.get("t") or "").strip()]
    except Exception:
        return []


def pensiero_tutti(miei=None):
    miei = pensiero_miei() if miei is None else miei
    return list(_PENSIERI) + [(x["t"], x.get("a") or "Una frase che ti piace", "I miei pensieri") for x in miei]


def pensiero_del_giorno(giorno=None, spostamento=0, miei=None):
    giorno = giorno or (oggi() if "oggi" in globals() else date.today())
    tutti = pensiero_tutti(miei)
    return tutti[pensiero_indice(giorno, spostamento, len(tutti))]


def pensiero_leggi_righe(testo):
    """Da un testo incollato (una frase per riga, «frase — autore») alle frasi: [(frase, autore)]. Toglie virgolette e numerazioni; scarta righe vuote o troppo lunghe."""
    import re
    out = []
    for riga in str(testo or "").splitlines():
        r = riga.strip()
        r = re.sub(r"^\s*(?:\d{1,3}[\.\)]|[-•*])\s+", "", r).strip()                         # «1. », «- », «• »
        if len(r) < 8:
            continue
        autore = ""
        m = re.match(r"^(.*\S)\s+[—–-]\s+([^—–-]{2,70})$", r) or re.match(r"^(.*\S)\s*\(([^()]{2,70})\)$", r)
        if m:
            r, autore = m.group(1).strip(), m.group(2).strip()
        r = r.strip("«»\"“”' ").strip()
        if 8 <= len(r) <= 450:
            out.append((r, autore.strip(" ,.;")))
    return out


def _pe_dialogo_togli(ids):
    def _finestra():
        st.warning(f"Togliere {len(ids)} {'frase' if len(ids) == 1 else 'frasi'} dai tuoi pensieri?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglile", key="pe_togli_si", type="primary", width="stretch"):
            _ca_salva(lambda cc: cc.__setitem__("pensieri_miei", [x for x in cc.get("pensieri_miei", []) if x.get("id") not in ids]), "Pensieri: tolti")
            st.session_state.pop("pe_togli_sel", None)
            st.rerun()
        if s2.button("No, tienile", key="pe_togli_no", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina i miei pensieri")(_finestra)()


def _pe_aggiungi_cb():
    """Al tocco del pulsante: aggiunge le frasi scritte (senza doppioni) e svuota la casella."""
    import uuid
    miei = pensiero_miei()
    anteprima = pensiero_leggi_righe(st.session_state.get("pe_nuove", ""))
    esistenti = {x["t"].strip().lower() for x in miei} | {f.strip().lower() for f, _, _ in _PENSIERI}
    nuove, saltate = [], 0
    for fr, au in anteprima:
        if fr.lower() in esistenti:
            saltate += 1
            continue
        esistenti.add(fr.lower())
        nuove.append({"id": uuid.uuid4().hex[:8], "t": fr, "a": au})
    if nuove:
        _ca_salva(lambda cc, nv=nuove: cc.__setitem__("pensieri_miei", list(cc.get("pensieri_miei", [])) + nv), "Pensieri: aggiunti")
    st.session_state["pe_nuove"] = ""
    st.session_state["pe_msg"] = f"✅ Aggiunte {len(nuove)} frasi." + (f" ({saltate} c'erano già: le ho saltate.)" if saltate else "")


def pensiero_miei_pannello():
    """«✍️ I miei pensieri»: incolli le frasi che ti piacciono (anche da Aphorism.it, frasi.net o dai libri) ed entrano nella rotazione."""
    import uuid
    miei = pensiero_miei()
    with st.expander(f"✍️ I miei pensieri ({len(miei)}) · aggiungi le frasi che ti piacciono"):
        st.caption("Incolla qui **una o più frasi, una per riga**. Per indicare l'autore scrivi **«frase — autore»** (con un trattino lungo o corto). Entrano subito nella rotazione del pensiero del giorno. "
                   "Puoi copiarle da **Aphorism.it**, **frasi.net**, da un libro o da dove vuoi.")
        testo = st.text_area("Frasi", key="pe_nuove", height=130, placeholder="La vita è ciò che accade mentre sei impegnato a fare altri progetti — John Lennon\nChi ha un perché abbastanza forte… — Nietzsche", label_visibility="collapsed")
        anteprima = pensiero_leggi_righe(testo)
        if testo.strip():
            st.caption(f"Ho riconosciuto **{len(anteprima)}** {'frase' if len(anteprima) == 1 else 'frasi'}.")
        st.button("💾 Aggiungi alla raccolta", key="pe_aggiungi", type="primary", width="stretch", disabled=not anteprima, on_click=_pe_aggiungi_cb)
        if st.session_state.get("pe_msg"):
            st.success(st.session_state.pop("pe_msg"))
        if miei:
            scelte = st.multiselect("Togli alcune delle mie frasi", [x["id"] for x in miei], key="pe_togli_sel", format_func=lambda i: next((f"{x['t'][:60]}…" if len(x['t']) > 60 else x['t']) + (f" — {x['a']}" if x.get("a") else "") for x in miei if x["id"] == i))
            if scelte and st.button("🗑️ Elimina le selezionate", key="pe_togli_btn", width="stretch"):
                _pe_dialogo_togli(set(scelte))


def pensiero_scheda(giorno=None):
    """La scheda del pensiero nella Home."""
    giorno = giorno or (oggi() if "oggi" in globals() else date.today())
    spost = st.session_state.get("pensiero_altro", 0)
    miei = pensiero_miei()
    frase, autore, ambito = pensiero_del_giorno(giorno, spost, miei)
    st.markdown(
        "<style>.pg-card{background:linear-gradient(135deg,#ede7f6 0%,#d1c4e9 55%,#b39ddb 100%);border-radius:22px;padding:14px 18px 12px;margin:10px 0 8px;color:#311b92;"
        "box-shadow:0 6px 18px rgba(49,27,146,.18);border:2px solid rgba(255,255,255,.7)}"
        ".pg-card .tit{font-size:.78rem;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:#4527a0}"
        ".pg-card .fr{font-size:1.12rem;line-height:1.42;font-style:italic;font-weight:600;margin:6px 0 6px;color:#1a0f5c}"
        ".pg-card .au{font-size:.88rem;font-weight:800;color:#4527a0}</style>"
        f"<div class='pg-card'><div class='tit'>💭 Pensiero del giorno · {_ICONE.get(ambito, '💭')} {_h.escape(ambito)}</div>"
        f"<div class='fr'>«{_h.escape(frase)}»</div><div class='au'>— {_h.escape(autore)}</div></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    if c1.button("🔁 Un altro pensiero", key="pensiero_altro_btn", width="stretch"):
        st.session_state["pensiero_altro"] = spost + 1
        st.rerun()
    if "inv_voce" in globals():
        with c2:
            inv_voce("pensiero_invia", "📤 Invia", "Pensiero del giorno", f"«{frase}»\n— {autore}", [])
    if "_ca_dati" in globals() and "_ca_salva" in globals():
        pensiero_miei_pannello()
