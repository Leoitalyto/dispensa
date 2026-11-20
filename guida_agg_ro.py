# -*- coding: utf-8 -*-
"""Instrucțiuni actualizate la 20.11.2026 — ROMÂNĂ (vezi guida_aggiornamento.py)."""

ga_traduci("ro", {
    "x_campanello": ("🔔 Clopoțelul: alertele acestei secțiuni", """În fiecare secțiune, sub butoanele colorate, este **🔔 Alertele acestei secțiuni**. Atinge-l: o fereastră îți spune **cum sunt setate alertele** și **ce urmează să expire**.

De acolo poți schimba:
- **Primește alertele acestei secțiuni**: comutatorul le pornește sau le oprește.
- **Cu câte zile înainte**: alege zilele (0 = în aceeași zi).
- **Aleg eu ora**: bifează, alege ora și apasă **Enter** pe tastatură. Fără oră aleasă, alertele vin dimineața.
- **Unde primesc alertele**: „ca celelalte secțiuni” sau alege între **Telegram, Email, WhatsApp, SMS**.
- **Calendar**: pornește „Vezi aceste alerte și în calendar” și apasă **Descarcă calendarul**; deschide fișierul, Android propune **Google Calendar**. Dacă o dată se schimbă, descarcă și deschide din nou (se actualizează, nu se dublează).
- **Ca înainte** pune totul la loc.

Apasă **💾 Salvează**. **Mai întâi** scrie-ți contactele (Telegram, email, WhatsApp, SMS) în **Sănătate → Alege cum primești alertele**: fără contact acel canal nu pornește. Alertele le trimite un program automat: uneori cu câteva minute întârziere; un mesaj ratat este recuperat în 3 ore, o singură dată.""",
                     "clopoțel alerte zile oră canale telegram email whatsapp sms sunet calendar google calendar"),
    "x_riuso_archivio": ("🗂️ Refolosirea unui fișier deja în arhivă", """Dacă ai deja un fișier sau o fotografie în arhivă **nu trebuie să le refaci**:
- **Sănătate** (vizite, rețete, documente, vaccinuri): sub „fă sau alege un fișier” este **🗂️ Sau atașează din arhivă**. Scrie pentru a căuta, alege fișierul și salvează: se folosește același fișier, fără copie.
- **Casă, Muncă (fluturași de salariu), Mașină, Animale**: în caseta unde încarci un fișier deschide **🗂️ Sau alege un fișier deja în arhivă**, alege-l și apasă **📥 Folosește acest fișier**: este citit ca și cum tocmai l-ai încărcat.
- **Cămară** (fotografia produsului): **🗂️ Alege din arhivă** arată fotografiile deja folosite, și ale produselor terminate.""",
                         "arhivă refolosire fișier fotografie deja salvat alege din arhivă atașează fără a reface"),
    "x_numeri_utili": ("📞 Numere utile și 📅 Programări", """În fiecare secțiune (în afară de Cămară), sub clopoțel, sunt două butoane.

**📞 Numere utile** este agenda ta cu cei de care ai nevoie în acea secțiune: **nume, meserie, domeniu, telefon de birou și mobil, program, site, email, adresă**.
- Dacă e o lucrare, bifează **„Există o ofertă”**: stare, sumă, **data de început și de sfârșit** și **PDF-ul sau fotografia ofertei**.
- În **„Documente primite”** pune PDF-uri, fotografii, facturi, contracte.
- Cu **„Deschide oferta, fișierele și plățile”** notezi **avansuri, rate și sold** și vezi cât ai plătit și cât mai rămâne.
- Există și **Note** și butoane pentru apel, WhatsApp, email, hartă sau site.

**Ale cui sunt?** În **Sănătate, Documentele mele și Casă**, unde alegi o persoană, numerele și programările sunt **separate pe persoană**.

**📅 Programări**: **nume, funcție, dată, oră, telefon, motiv și note**. Sus vezi **următoarele**, după dată; cele trecute sau făcute sunt jos. Cu **„Pune în calendarul telefonului”** programarea intră în calendar cu o amintire.""",
                       "numere utile agendă programări ofertă plăți avans sold contacte calendar"),
    "x_conti_casa": ("💶 Ținerea conturilor", """În **Casă** atinge **💶 Ținerea conturilor**. Adaugă câte poziții vrei: **conturi curente** (cu banca), **Postepay**, **libretele poștale**, **BOT, BTP**, fonduri, acțiuni, bonuri poștale, numerar. Vezi **totalul** sus și jos, **subtotalurile** pe tip și un câmp **Note**. Pentru titlurile de stat poți nota scadența. **Fiecare persoană are conturile ei**: dacă în Casă ai ales, de exemplu, mama ta, butonul devine **„Conturile lui/ei …”**. Conturile unei persoane nu se amestecă cu ale celorlalți.""",
                     "conturi bani bancă cont curent postepay economii obligațiuni btp bot total subtotal persoană"),
    "x_badante": ("👵 Îngrijitoare (doar administrator)", """În **Casă**, doar pentru administrator, este **👵 Îngrijitoare**.
- Setează **tariful** (de obicei 20 € pentru 2 ore), zilele în care vine și din ce zi se numără.
- **Fiecare zi contează singură ca „a venit”** (2 ore, tariful obișnuit), din ziua primei predări de bani: atinge **❌ Nu a venit** doar dacă nu a venit; dacă a stat mai multe sau mai puține ore folosește **„Altă zi sau altă sumă”**.
- Cu **„I-am dat bani mamei mele”** notezi cât și când.
- Aplicația calculează cât a rămas și **până când ajung banii**.
- **🔔 Alertele îngrijitoarei** te anunță **cu 3 zile înainte** și **în ultima zi** (zilele se pot schimba).
- Există și **contactele îngrijitoarei** și **note**.""",
                  "îngrijitoare badante ore tarif a venit bani mama alerte"),
    "x_interruttori": ("💡 Selectoare tip comutator", """În toată aplicația selectoarele tip pastilă (pentru a alege persoana, casa, vehiculul…) funcționează ca niște **comutatoare**: cel **activ este albastru neon și pulsează**, celelalte par **stinse**.""",
                       "comutator selector pastilă activ neon"),
    "x_ia": ("🤖 Inteligență artificială: documente, scris de mână, martori de bord, limbi", """Cu **cheile** serviciilor de inteligență artificială (gratuite: Groq, Google Gemini, OpenRouter, NVIDIA, Cloudflare, Cohere, Hugging Face, SambaNova cu credit de probă; **DeepSeek** cu plată, opțional) aplicația:
- **citește și clasifică documentele medicale** (ce document este, domeniul medical, investigația, datele, medicul, unitatea, concluziile). Dacă este **scris de mână**, îl citesc **mai multe servicii** și un „arbitru” compară citirile: vezi **cine l-a citit**, **limitele** și **ce trebuie verificat** pe foaie. Nimic nu se salvează fără confirmarea ta;
- **recunoaște martorii de bord ai mașinii**, comparând mai multe citiri când fotografia e nesigură;
- **traduce paginile** în limba aleasă (prima dată când se deschide o pagină; apoi rămâne salvat pentru toți);
- face ca **asistentul** să răspundă în limba aleasă.
Dacă un serviciu e epuizat sau lent, aplicația trece singură la următorul.

**DeepSeek este cu plată**: îl folosesc doar **administratorul** și persoanele alese de el (Utilități → 🤖 → DeepSeek → **🔒 Cine îl poate folosi**). Pe același rând se vede **💰 creditul rămas**. Traducerile automate nu folosesc niciodată servicii cu plată.

Cheile le pune administratorul în **Utilități → 🤖 Inteligență artificială**, cu ghidul pas cu pas; **🔄 Verifică din nou cheile** și **proba** fiecărui serviciu spun dacă funcționează. Atenție: cu cheile gratuite Google textele pot fi folosite pentru a le îmbunătăți modelele.""",
             "inteligență artificială ia chei gemini groq openrouter nvidia cloudflare cohere hugging face sambanova deepseek credit cine poate folosi scris de mână martori traducere"),
    "x_compleanni": ("🎂 Zile de naștere: fișele persoanelor", """În **Utilități → 🎂 Zile de naștere** atinge **insigna „La mulți ani”** pentru a deschide lista (atinge-o din nou pentru a o închide).

- **➕ Adaugă o persoană**: nume și data nașterii (dacă nu știi anul bifează **„Nu știu anul”**). Restul e opțional: **fotografie, locul nașterii, nume de familie, poreclă, mobil, telefon, WhatsApp, Telegram, email, adresă, site, idei de cadouri, note**. La **„Cine este pentru tine”**, dacă alegi **Altul**, poți scrie tu cuvântul potrivit.
- **Fotografia**: atinge „Alege fotografia”; **ciupește cu două degete** pentru mărire și **trage** pentru a o muta până când fața e în oval. Mai târziu o poți **🔄 Recentra**.
- Fiecare persoană are **fișa cu ramă neon** în culoarea **zodiei** sale, aleasă după dată. **Semnele se mișcă** (Berbecul dă cu capul cu ochi de foc, Peștii înoată încet, Racul merge lateral…).
- Sub fișă sunt butoane pentru **apel, WhatsApp, Telegram, email, site**. Lista e în ordinea **următoarei zile de naștere** („🎉 Azi!” dacă e azi).
- Dacă **persoana nu mai este**, bifează **🕯️ Această persoană nu mai este**: apare o **lumânare aprinsă**, fișa trece la **In memoriam** și găsești **⚰️ Unde se odihnește** (tipul înmormântării, cimitirul, poziția, concesiunea, candela, telefonul și programul cimitirului, fotografii ale pietrei funerare), **rugăciunea odihnei veșnice**, **✍️ un gând** și **🎙️ un mesaj vocal**.
- **Butonul verde ⏻** din fișă deschide **📖 Jurnalul amintirilor** (vezi fișa lui).
- ✏️ **Modifică** schimbă datele (ce nu atingi rămâne la fel); 🗑️ **Șterge** trimite fișa la Coș.""",
                     "zile de naștere zi de naștere zodie fișă persoană fotografie contacte whatsapp telegram decedat lumânare memorie înmormântare jurnal"),
    "x_diario": ("📖 Jurnalul amintirilor (fotografii, texte, muzică)", """În fișa fiecărei persoane din **🎂 Zile de naștere**, jos în dreapta, este **butonul verde ⏻**. Atinge-l: **fișa dispare și se deschide jurnalul**, cu fotografiile stivuite ca paginile unei cărți.

- **Răsfoire**: **◀ Înapoi** și **Înainte ▶** sus. **Butonul roșu ⏻**, între ele, închide jurnalul și fișa revine.
- **Derulare automată**: fotografiile trec singure la fiecare **7 secunde**; în **⏱️ Derulare automată** alegi secundele sau o oprești. Fiecare fotografie **intră și iese cu un efect mereu diferit**.
- **Adăugare fotografii**: **➕ Adaugă alte fotografii** (câte vrei, fără limită). Pentru fiecare vezi o **previzualizare**: **ciupești** cu două degete pentru mărire și **tragi** pentru mutare; poți scrie **texte colorate** (culoare, font, mărime, poziție) și pune **pictograme** (inimi, flori, lumânări…). Apoi **💾 Salvează pagina**. Fotografiile devin mai ușoare singure, fără pierdere de calitate.
- **Schimbări ulterioare**: cu **✏️ Texte și pictograme** scoți sau schimbi textele și pictogramele oricând; **↩️ Anulează ultima modificare** pune la loc (fotografia originală nu e atinsă niciodată). În **🗂️ Gestionează paginile** muți o pagină **⬆️ ⬇️**, **🔄 schimbi fotografia** sau o **🗑️ ștergi**.
- **Muzică**: în **🎵 Muzica jurnalului** alege un fișier **MP3** (se salvează singur). Pornește când atingi butonul verde; jos **bara de volum** (atinge sau trage) și ▶/🔊 pentru pauză. Pentru a o schimba, alege alt fișier.""",
                 "jurnalul amintirilor jurnal fotografii pagini buton verde roșu derulare muzică mp3 volum texte pictograme efecte gestionează pagini zile de naștere"),
    "f_ia_documenti": ("🤖 Recitirea și reclasificarea documentelor cu IA", """În **Sănătate → Documente medicale** deschide **🤖 Reclasifică documentele cu IA**.

1. Vezi **„De verificat: X din Y”**: IA citește **doar documentele încă neverificate** (bifează „Recitește și pe cele deja verificate” pentru a le reciti pe toate).
2. Atinge **🔍 Probă: citește și clasifică**. Apare o **casetă mereu deschisă** care se actualizează singură: la ce document a ajuns, de câte secunde, ce serviciu întreabă, câte a citit, cât mai durează. Punctele **●●●○** care se mișcă arată că lucrează.
3. **Poți folosi alte aplicații sau stinge ecranul**: citirea continuă singură. Fiecare document este salvat imediat ce e citit, nimic nu se pierde.
4. Un document blocat este **sărit după circa 2 minute** („prea lent, sărit”) și reîncercat data viitoare. **⏹ Oprește citirea** le păstrează pe cele deja citite.
5. **🟡 Propunerile IA de confirmat** apar în aceeași casetă, câte una pe document: lasă bifat ce e corect și atinge **✅ Aplică**; **✖ Nu aplica** lasă totul cum e. Ce ai corectat de mână nu e atins.

Și **🔄 Recitește documentele deja arhivate** (fără IA) arată **„De recitit: X din Y”** și nu le mai propune pe cele deja făcute.""",
                       "reclasifică documente ia inteligență artificială recitește citire în curs propuneri aplică verificate fundal alte aplicații oprește"),
    "f_numeri_doc": ("🔢 Nr. documentelor medicale (pentru medic)", """Fiecare document medical are un **număr**: **Nr. 1 este cel mai recent**, apoi în jos până la cel mai vechi. Îl vezi într-un **pătrat verde** pe fiecare fișă și în coloana **N°** a **rezumatului PDF** de la Sănătate.

**La ce folosește:** dai rezumatul medicului; el îți spune „adu-mi 4, 12 și 17”. Scrie numărul (de exemplu **12**) în caseta **🔍 Caută** a Documentelor medicale și apare **doar acel document**.

**Atenție:** când adaugi un document nou, el devine Nr. 1 și celelalte **coboară cu unul**. Dacă între timp ai adăugat documente, **creează din nou rezumatul PDF**. În PDF datele nu mai sunt rupte pe două rânduri.""",
                     "număr documente nr medic rezumat pdf caută număr ordine cel mai recent adu-mi"),
    "f_gruppo": ("🩸 Grupa sanguină și certificatul", """În fișa persoanei din **Sănătate**: dacă lipsește grupa sanguină, atinge **🩸 Introdu grupa sanguină**, alege-o și salvează. O poți schimba oricând cu **Modifică**.

Dedesubt poți **atașa certificatul grupei sanguine** (PDF sau fotografie): alege fișierul și se salvează singur. Îl vezi, îl descarci sau îl scoți oricând.""",
                 "grupă sanguină sânge certificat atașează pdf fotografie fișă persoană"),
    "f_wiki": ("📖 „Ce este?”: explicație simplă din Wikipedia", """În **Sănătate → Documente medicale** și în **Sănătate → Medicamente** este meniul **📖 Ce este? Explicație simplă (Wikipedia)**.

Scrie numele unei **investigații, boli sau al unui medicament** (de exemplu *ecografie Doppler*, *duloxetină*): dacă sunt mai multe articole alege-l pe cel corect și citește **două rânduri de explicație**, în limba aplicației, cu butonul pentru pagina completă.

Este o **informație generală**, gratuită: **nu este un sfat medical**. Pentru situația ta întreabă mereu medicul sau farmacistul.""",
               "ce este explicație wikipedia investigație boală medicament înțeles cuvânt raport"),
    "x_meteo": ("🌦️ Alerte meteo utile", """Alerte **doar când e nevoie**, în partea de sus a secțiunilor:
- **Sănătate**: **căldură puternică** (bea des, nu ieși între 11 și 17, atenție la vârstnici și copii) și **frig intens**;
- **Mașină**: **îngheț** (gheață pe parbriz și pe drumuri), **ploaie puternică**, **rafale de vânt**;
- **Animale**: **căldură** (plimbări devreme sau seara, asfalt fierbinte, apă proaspătă, niciodată în mașină) și **frig**.

**Pentru a le porni:** **Utilități → 🌦️ Alerte meteo** → scrie orașul tău → alege-l pe cel corect → **💾 Folosește acest oraș**. Acolo vezi și temperaturile zilelor următoare și poți **opri** alertele. Fiecare își alege orașul.

Prognozele sunt de la **Open-Meteo**: gratuit, fără chei sau înregistrare, pentru uz necomercial.""",
                "meteo alerte căldură frig îngheț ploaie vânt oraș prognoză open-meteo"),
    "x_voci_libere": ("✍️ Un nume ales de tine în listele cu „Altul”", """În listele derulante care au opțiunea **Altul** (tipuri de documente, camere, specii de animale, înmormântări, rolurile medicilor, categorii de condominiu, moduri de plată, „Cine este pentru tine”, documente INPS…):
1. alege **Altul**;
2. apare **✍️ Nu e în listă? Scrie numele dorit**: scrie numele exact (de exemplu **Ecocert**);
3. salvează ca de obicei: se salvează **numele tău**, nu „Altul”.

În fișele cu butonul de confirmare jos caseta e mereu acolo, sub listă, și contează doar dacă ai ales „Altul”. **Numele rămâne în listă**: data viitoare îl găsești deja, înainte de „Altul”.""",
                      "altul nume ales listă derulantă scrie nume opțiune proprie ecocert nu e în listă"),
    "x_lingua": ("🌐 Limba aplicației", """**Intri în limba pe care o vezi pe pagina de autentificare.** Dacă vrei altă limbă, alege-o din meniul **🌐 Lingua / Language** înainte de a atinge **Intră**: rămâne salvată.

Telefonul ține minte **ultima limbă folosită**: data viitoare pagina de autentificare se deschide deja în acea limbă. În aplicație limba se schimbă din meniul **☰** din stânga sus.

Toate paginile sunt în limba aleasă: frazele noi se traduc singure prima dată când se deschide o pagină (cam un minut), apoi rămân salvate pentru toți. Și **asistentul** răspunde în limba aleasă.""",
                 "limbă italiană engleză spaniolă franceză germană română arabă portugheză schimbă limba autentificare traducere"),
}, {
    "nv_diario": ("Jurnalul amintirilor", "Utilități → 🎂 Zile de naștere → butonul verde ⏻ din fișă: fotografii, texte, pictograme, muzică"),
    "nv_ia": ("Documente citite de IA", "Sănătate → Documente medicale → 🤖 Reclasifică: merge și dacă folosești alte aplicații"),
    "nv_numeri": ("Nr. documentelor", "Sănătate → Documente medicale: Nr. 1 este cel mai recent; caută după număr"),
    "nv_meteo": ("Alerte meteo", "Utilități → 🌦️ Alerte meteo: alege-ți orașul"),
    "nv_wiki": ("Ce este?", "Sănătate → Documente medicale și Medicamente: explicație simplă din Wikipedia"),
    "nv_altro": ("Nume alese", "În listele cu „Altul”: scrie numele dorit"),
})


ga_traduci('ro', {"l_festivita": ('📅 Zile de sărbătoare în Controlul orelor', 'În **Muncă → 🧮 Controlul orelor**, după ce încarci foaia orelor și fluturașul de salariu, este **📅 Zile de sărbătoare**.\n\nAplicația cunoaște singură **sărbătorile naționale** (și **Lunea Paștelui**, care se schimbă în fiecare an) și **sărbătoarea patronului** orașului tău, pe care o alegi o dată în **⛪ Sărbătoarea patronului și sărbătorile anului** (pentru Torino: Sfântul Ioan, 24 iunie), apoi atingi **💾 Ține minte patronul**.\n- **Avertisment roșu**: ai lucrat într-o zi de sărbătoare care în foaie **nu este marcată ca sărbătoare**. Vezi zilele, orele și o estimare a cât ai putea pierde (sărbătoarea se plătește 65%, orele suplimentare normale 20%). Marchează „sărbătoare” în foaie și reîncarcă, sau întreabă biroul de salarizare.\n- **Avertisment galben**: o zi este marcată ca sărbătoare, dar nu este nici sărbătoare, nici duminică: verifică (poate exista o regulă a contractului tău).\n\nSărbătorile vin de la **Nager.Date** (gratuit, fără cheie); dacă nu răspunde, le calculează aplicația.', 'sărbători zi de sărbătoare lunea paștelui patron controlul orelor fluturaș ore suplimentare')}, {})


ga_traduci('ro', {"x_lettore": ('🤖 Recitirea și recatalogarea documentelor cu IA (toate secțiunile)', 'Jos în **Documentele mele**, **Casă** (fila 📚 Documente), **Muncă**, **Mașină** și **Animale** este **🤖 Recitește și recatalogează cu IA** (la Sănătate: „🤖 Reclasifică documentele cu IA”).\n\n**Cum citește:** în **doi pași**: întâi înțelege **ce document este**, apoi citește datele cu **fișa potrivită pentru acel tip** (buletin: număr, emitere, expirare; factură: perioadă, sumă, scadență, POD/PDR…). Apoi **verifică** datele: cod fiscal, numărul buletinului sau al pașaportului, număr de înmatriculare, serie de șasiu, IBAN, date (expirarea după emitere, niciodată data nașterii în locul alteia). O valoare care nu trece verificările rămâne **🟠 de verificat** și nu este propusă.\n\n1. Deschide meniul: vezi **„De verificat: X din Y”**. Atinge **🔍 Citește și catalogează**.\n2. Apare **caseta în direct**: poți folosi alte aplicații, citirea continuă; fiecare document e salvat imediat ce e citit.\n3. **🟡 Propunerile de confirmat** arată ce s-ar schimba: lasă bifat ce e corect și atinge **✅ Aplică**; **✖ Nu aplica** lasă totul cum e.\n\nȘi documentele **noi** (fotografia buletinului, facturi, polițe, documente de la veterinar) sunt citite la fel.', 'recitește recatalogează documente ia verificări cod fiscal număr date propuneri aplică')}, {})

# 20/11 sera: di chi è il documento · biglietto da visita
ga_traduci('ro', {'x_smistamento': ('👥 Al cui e documentul și unde merge (mama, casa ei, sănătatea ei)', "Când IA citește un document înțelege și **cui îi este adresat** (destinatarul scrisorii, titularul facturii, pacientul din raport) și **în ce secțiune merge**.\n\n**Mai întâi, o singură dată:** în **🤖 Rileggi e ricataloga con l'IA** (Documentele mele sau Casa) sau în **🤖 Riclassifica** (Sănătate) atinge **👥 Di chi sono i documenti: persone e case** (Ale cui sunt documentele: persoane și case):\n- pentru fiecare persoană scrie **numele și prenumele cum apar pe documente** (ex. pentru «Mama»: Maria Teresa Ianniciello) și, dacă îl știi, **codul fiscal**;\n- pentru fiecare casă alege **a cui este** (ex. «Casa mamei» → Mama). Atinge **💾 Salva** (Salvează).\n\n**Apoi aplicația propune singură:**\n- 🏠 **În ce casă**: scrisoarea administratorului adresată mamei merge în **casa mamei** (cu administrația ei);\n- 👤 **Al cui e**: buletinul mamei merge la **documentele mamei**; raportul medical al mamei merge la **documentele ei de sănătate**;\n- 📦 **De mutat în**: un raport medical pus în Casa sau în Documentele mele merge în **Sănătatea** persoanei potrivite; un act de identitate pus în Casa merge în **Documentele mele**.\n\nDocumentele **noi** se citesc **singure** imediat ce le încarci (în fundal): când redeschizi secțiunea găsești propunerea. Nimic nu se mută fără **✅ Applica** (Aplică). La fel și pentru documentele tale.", 'al cui titular destinatar mama persoană casă administrație sănătate muta secțiunea potrivită cod fiscal nume prenume documente propunere'), 'x_biglietto': ('📇 Carte de vizită în Numere utile', 'În **Casa, Sănătate, Muncă, Mașină și Animale → 📞 Numeri utili → ➕ Aggiungi** (Numere utile → Adaugă) există **📇 Fotografa un biglietto da visita** (Fotografiază o carte de vizită).\n1. Fă poza (și față și verso) și atinge **🔎 Leggi il biglietto** (Citește cartea).\n2. IA completează singură **nume sau firmă, persoană de contact, meserie, telefon, mobil, email, site, adresă, program** (codul de TVA merge în note). **Verifică** și corectează dacă e nevoie.\n3. Dacă ați folosit deja serviciile lui bifează **✅ Abbiamo già usato le sue prestazioni** (Am folosit deja serviciile lui) și scrie **când** și **ce a făcut** (și cum a fost). Există și câmpul **📝 Note**.\n4. Atinge **✅ Salva** (Salvează).\n\nPe fișă găsești butoanele ca să-l contactezi imediat: **📞 Sună, 💬 WhatsApp, ✉️ Email, ✈️ Telegram, 💬 SMS** (+39 se adaugă singur).', 'carte de vizită poză numere utile contacte telefon whatsapp email telegram sms folosit deja lucrări făcute când note meșter')}, {'nv_smista': ('Al cui e documentul', 'IA pune documentele mamei la lucrurile ei: casă, sănătate, documente'), 'nv_biglietto': ('Carte de vizită', 'Numere utile → ➕ Adaugă → 📇 Fotografiază o carte de vizită')})
