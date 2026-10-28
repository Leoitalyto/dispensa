# -*- coding: utf-8 -*-
"""Guida, giro guidato, novità e testi dell'assistente in RUMENO. Caricato da app_dispensa.py dopo info_sezioni.py.
Per le schermate Farmacia / I miei documenti / Utilità i nomi dei pulsanti restano come si vedono sullo schermo (in italiano)."""
GUIDA_TR["ro"] = {
    "d_assistente": ("🤖 Asistentul digital (robotul mic)",
        """Este **robotul mic galben și albastru** din dreapta jos, cu fața rotundă. **Atinge-l** și se deschide panoul lui.

Ce știe să facă:
- **📖 Explică-mi această pagină**: îți spune cu voce tare la ce servește pagina în care ești.
- **🧭 Tur ghidat**: îți explică toată aplicația pas cu pas (Înainte și Înapoi).
- **🆕 Ce e nou**: îți spune noutățile și unde le găsești.
- **🎤 Pune o întrebare**: atinge, vorbește (de exemplu „cum adaug o fotografie la document?”) și îți răspunde cu ghidul. Funcționează pe Chrome pentru Android.
- Poți și să **scrii** întrebarea în casetă.

**Voce:** folosește vocea telefonului. Dacă nu vrei să-l auzi, atinge **🔊 Voce: activă** ca s-o oprești.

**Ca să-l dezactivezi:** atinge **⛔ Dezactivează asistentul** în panoul lui. Ca să-l reactivezi deschide butonul roșu **Atinge pentru informații** și atinge **✅ Activează** în caseta asistentului. Alegerea rămâne salvată pe telefon.""",
        "asistent robot voce vorbeste microfon asculta intrebare tur noutati dezactiveaza activeaza opreste ajutor"),
    "d_inizio": ("🚀 La ce folosește și cum se începe",
        """**La ce folosește:** ține lista cu ce ai în casă, când expiră și ce conține. Te avertizează înainte să se strice ceva.

**Ca să începi, 5 pași:**
1. Atinge fila **➕ Adaugă** de jos.
2. Fotografiază produsul (sau sari peste).
3. Scrie numele, câte bucăți ai și **data de expirare**.
4. Atinge butonul de salvare.
5. Întoarce-te la fila **🏠 Cămara**: produsul e acolo, cu culoarea expirării.

Cămara este **doar a ta**: fiecare persoană are parola ei și nimeni nu vede produsele celorlalți.""",
        "incepe inceput primii pasi ce este la ce foloseste cum functioneaza introducere utilizare"),
    "d_aggiungere": ("➕ Cum adaugi un produs",
        """1. Atinge **➕ Adaugă** (fila de jos).
2. Sus este zona **fotografiei**: atinge **📷 Fă fotografia** (se deschide camera din spate) sau **📁 Încarcă din telefon**.
3. Scrie **numele** și **marca**.
4. Scrie **codul de bare** de mână (sunt cifrele de sub bare): aplicația completează singură ingredientele, valorile și alergenii, dacă produsul este cunoscut.
5. Scrie **câte bucăți**, cât **cântărește** sau câți **litri**.
6. Alege **data de expirare**.
7. La **„Unde îl pui?”** alege: Cămară, Frigider, Congelator, Pivniță, Magazin, Depozit sau Altceva. **Categoria** este text liber.
8. Alege **pentru cine este**: adulți, bebeluși (0-2 ani) sau animale.
9. Salvează.

Dacă nu ai nicio informație, ajung **numele, bucățile și expirarea**.""",
        "adauga introdu nou produs cod de bare qr completeaza unde frigider congelator pivnita categorie cantitate bucati greutate litri scrie"),
    "d_foto": ("📸 Fotografia produsului: poză, riglă și decupare",
        """1. Atinge **📷 Fă fotografia** sau **📁 Încarcă din telefon**.
2. Aplicația scoate **fundalul** și **îndreaptă** singură produsul.
3. Dedesubt apare **editorul**: trage **rigla** ca să rotești poza și trage **cadrul** ca să tai marginile.
4. Când e perfectă atinge **💾 Salvează poziția și decuparea**.
5. Apoi salvează produsul.

Dacă editorul nu merge, deschide **🛠️ Comenzi de rezervă**: sunt cursoare pentru rotire și decupare.""",
        "foto fotografie poza fa camera roteste indreapta decupeaza taie fundal contur rigla cadru imagine"),
    "d_colori": ("🎨 Culorile și avertizările de expirare",
        """- 🟢 **Verde**: mai sunt peste 2 luni. Totul e liniștit.
- 🟠 **Portocaliu**: expiră în mai puțin de 2 luni. Merită să-l folosești.
- 🔴 **Roșu**: expiră în mai puțin de 1 lună. Folosește-l curând.
- ⚫ **Închis**: a expirat deja.

Sus vezi **contoarele** colorate și avertizările cu câte bucăți, grame sau litri sunt pe cale să expire.

Fiecare secțiune are **sunetul** ei: adulții sunetele obișnuite; bebelușii un sunet pentru fetiță (2 luni), unul pentru băiețel (1 lună) și ambele dacă a expirat; animalele pisica (2 luni), câinele (1 lună) și leul dacă a expirat.

Dacă ai activat **Telegram** sau **e-mailul**, avertizarea ajunge și acolo.""",
        "culori expirare avertizari verde portocaliu rosu expirat contoare sunet sunete sirena notificare cand expira"),
    "d_allergeni": ("🌾 Alergeni, ingrediente, vegan și fără gluten",
        """1. Deschide **meniul din stânga** (săgeata **»** din stânga sus) și alege **alergiile tale**.
2. Produsele cu un alergen au un **buton galben** cu numele lui (de exemplu *Gluten*): atinge-l și se deschide **compoziția**, cu cuvintele periculoase evidențiate.
3. Dacă alergenul este **periculos pentru tine** apare **sirena care clipește**, cu scris cui îi este contraindicat.
4. Pe fiecare fișă este butonul **Ingrediente**: deschide tot textul de citit, în limba ta.
5. Butoanele **Vegan** și **Vegetarian** apar doar dacă produsul chiar este. Butonul **Fără gluten** are marginea aurie.""",
        "alergeni alergie gluten ingrediente vegan vegetarian fara gluten compozitie intoleranta sirena periculos"),
    "d_pulsanti": ("🔘 Butoanele fiecărui produs: Șterge, Info, Modifică",
        """În **Fișe**, sub fiecare produs sunt trei butoane:
- **Șterge**: scoate produsul. Dacă ai același produs cu mai multe expirări, te întreabă **care intrare** să o șteargă.
- **Info**: deschide ghidul complet cu toate simbolurile.
- **Modifică**: schimbă orice dată (nume, expirare, fotografie, cantitate…).

În **Tabel** se bifează căsuța 🗑️ a rândului și apoi se atinge **Șterge rândurile bifate** sau **Modifică rândul bifat** (pentru modificare bifează un singur rând).""",
        "sterge elimina cos modifica schimba corecteaza info tabel fise vizualizare"),
    "d_icone": ("🧭 Pictogramele Farmacie, Documentele mele și Utilitare",
        """Pe Pagina principală, lângă comenzile de căutare, sunt **trei pictograme care pulsează**:
- **🏥 Farmacie**: medicamente, tratamente, vizite, cardul de sănătate.
- **📁 Documentele mele**: buletin, permis, card de sănătate cu termenele.
- **🧰 Utilitare**: aplicații și site-uri utile, ca Velocity Music.

Atinge una ca s-o deschizi; ca să te întorci atinge **← Înapoi la cămară**. Pe fiecare pagină, sus, este butonul roșu **Atinge pentru informații** cu ghidul.""",
        "pictograme farmacie documente utilitare pagina principala pagini navigheaza meniu unde gasesc"),
    "d_cercare": ("🔎 Căutarea și filtrarea produselor",
        """Sus în Cămară sunt trei comenzi:
1. **🔎 Caută**: scrie numele sau marca.
2. **Arată**: alege *Toate*, *Doar cele care expiră curând (2 luni)*, *Doar roșii (1 lună)* sau *Expirate*.
3. **Vizualizare**: *Fișe* (cu poze mari) sau *Tabel* (listă compactă).""",
        "cauta cautare gaseste filtru filtreaza arata vizualizare fise tabel lista"),
    "d_spesa": ("🛒 Lista de cumpărături și pliante",
        """- Când un produs **se termină** merge singur în fila **🛒 Cumpărături**.
- În fila Cumpărături poți atinge **Am consumat unul** ca să scazi o bucată.
- Pe fișa produsului, în dreapta cantității, este legătura către **pliantele** supermarketurilor, hipermarketurilor și discounterilor: alege **țara** (pornește de la cea a limbii tale) și scrie **orașul**, uită-te la oferte și atinge butonul ca să pui produsul în **lista de cumpărături**, cu numele magazinului.""",
        "cumparaturi lista de cumparaturi cumpara pliante oferte supermarket consumat terminat oras magazin"),
    "d_gestisci": ("✏️ Gestionezi mai multe produse deodată",
        """Fila **✏️ Gestionează** servește ca să schimbi dintr-o dată **cantitatea, expirările și notele** mai multor produse, fără să le deschizi pe rând.""",
        "gestioneaza modifica mai multe produse impreuna cantitate expirari note"),
    "d_account": ("👤 Parolă, limbă și mesaje",
        """- **Parola:** ți-o dă cine administrează aplicația. La prima intrare o poți schimba. Este doar a ta.
- **Limba:** în meniul din stânga este **🌐 Limbă / Language**.
- **Mesaje și sugestii:** pentru o idee, o problemă sau o cerere folosește fila **✉️ Mesaje / 💬 Sugestii**: o citește administratorul.""",
        "parola cont acces limba language mesaje sugestii administrator problema cerere schimba"),
    "d_aiuto": ("🛟 Dacă ceva nu merge",
        """1. **Reîncarcă pagina** din browser.
2. Fotografia nu apare? Folosește **🛠️ Comenzi de rezervă** sau alege altă fotografie.
3. Microfonul pentru dictare funcționează pe **Chrome pentru Android**: atinge o dată ca să-l pornești, o dată ca să-l oprești.
4. Dacă problema rămâne, scrie-o în fila **Mesaje**: îl ajută pe administrator s-o rezolve.""",
        "problema eroare nu merge ajutor blocat fotografia nu apare microfon dictare"),

    "f_cosa": ("🚀 La ce folosește Farmacia",
        """Aici ții în ordine **medicamentele din casă** și **termenele de expirare**, **tratamentele**, **vizitele**, **vaccinurile**, **medicul** tău și **fișa ta medicală**.

Aplicația îți **amintește** și organizează ce introduci tu. **Nu dă sfaturi medicale** și nu schimbă tratamentele: pentru doze și tratamente urmează mereu medicul sau farmacistul.""",
        "farmacie ce este la ce foloseste medicamente incepe introducere"),
    "f_profili": ("👤 Profilurile familiei și grupa de sânge",
        """Fiecare persoană are un **profil** (până la 12): mama, tata, copiii…
1. Sus alege profilul din **👤 Profilo**.
2. Ca să adaugi unul deschide **👥 Gestisci profili**, scrie numele și atinge **Aggiungi profilo**.
3. În același loc poți schimba numele și alege **🩸 grupa de sânge**: apare ca o **picătură** colorată lângă profil.
4. Ca să ștergi un profil bifează confirmarea și atinge **Elimina profilo** (se șterg și toate datele lui).""",
        "profil profiluri familie persoana grupa de sange picatura nume adauga sterge"),
    "f_medicinale": ("💊 Cum adaugi un medicament",
        """1. Atinge **➕ Aggiungi medicinale**.
2. Sus **fotografia cutiei**: **📷 Scatta la foto** sau **📁 Carica dal telefono**; apoi îndreaptă cu rigla, taie cu cadrul și atinge **💾 Salva posizione e ritaglio**.
3. Scrie **nume**, **substanță activă**, **doză**, **formă** (comprimate, sirop…) și **cantitate**.
4. Alege **expirarea** și **pentru cine este**.
5. Atinge **Salva**.

Poți refolosi o fotografie deja salvată din **arhiva de fotografii**. La medicament poți atașa **prospectul** (PDF, fotografie sau link).

Ca să vezi tot despre un medicament, **atinge fișa lui**: se deschide detaliul cu **prospectul**, fotografia mare, terapiile legate și butoanele **✏️ Modifica** și **🗑️ Elimina**.

Ca să economisești timp atinge **📷 Inquadra la scatola** (Scanează cutia): aplicația citește pătrățelul (DataMatrix) sau liniile și completează data de expirare, lotul și codul. Dacă medicamentul e deja în casă copiază și numele și doza; dacă e nou, scrie numele o singură dată și data viitoare îl recunoaște.""",
        "medicament medicamente adauga cutie foto expirare substanta activa doza prospect arhiva"),
    "f_scadenze": ("🎨 Expirări și alergii la medicamente",
        """- 🟠 **Portocaliu**: expiră în mai puțin de 2 luni. 🔴 **Roșu**: în mai puțin de 1 lună. ⚫ **Expirat**: de aruncat corect.
- În fișa profilului poți scrie **alergiile la medicamente**: dacă un medicament conține acea substanță activă apare un **avertisment roșu**.""",
        "expirare culori alergie alergii medicamente avertisment rosu portocaliu expirat"),
    "f_terapie": ("📅 Tratamentele și calendarul",
        """1. Deschide fila **📅 Terapie**.
2. Adaugă un tratament: **medicament**, **zile**, **ore** și cantitate.
3. La ora stabilită atinge **Presa** (luat) ca să notezi administrarea: rămâne în **istoric**.
4. Un tratament poate fi **activ**, **suspendat** sau **terminat**. Tratamentele de probă se pot **șterge**.
5. **Calendarul** arată săptămâna și luna.
6. **Raportul pentru medic** (perioadă la alegere) se tipărește sau se deschide în Excel.""",
        "tratament tratamente terapie calendar administrare luat ore raport medic istoric pastila doza"),
    "f_prescrizioni": ('📝 Rețete',
        """1. Deschide fila **📝 Prescrizioni** și atinge **➕ Aggiungi prescrizione**.
2. Scrie **data**, **tipul** (medicamente, analize, consult…), **medicul**, ce a fost **prescris**, **codul rețetei** și până când este **valabilă**.
3. Atașează **fotografia rețetei** sau PDF-ul.
4. Atingând o rețetă se deschide **detaliul**: vezi fotografia, atingi **✅ Segna come usata** (Marchează ca folosită), **✏️ Modifica** sau **🗑️ Elimina**.
5. Rețetele care expiră curând apar printre lucrurile de verificat, și în **Controlul familiei**.""",
        'reteta retete prescriptie medic cod valabilitate expirare folosita'),
    "f_invio": ('📤 Exportă și trimite (PDF, email, WhatsApp…)',
        """1. Sus în Farmacie deschide **📤 Esporta e invia** (Exportă și trimite). Alege **a cui** și **ce** (medicamente, terapii, rețete, vizite, vaccinuri, documente, fișă sanitară, cămară, listă de cumpărături).
2. Alege **formatul** (PDF, Excel sau fișier de tipărit) și atinge **📦 Prepara i file** (Pregătește fișierele).
3. Apoi alege cum le trimiți: **📤 Telefono** (se deschide Partajare: WhatsApp, Gmail, Telegram, Drive…), **✉️ Email** (direct din aplicație), **💬 WhatsApp** (rezumat scris), **✈️ Telegram** (în chatul tău cu botul), **📱 SMS** sau **📋 Copia** (Copiază).
4. Fiecare document, medicament, rețetă și vizită are și butonul său **📤 Invia** (Trimite), cu fotografiile lui.
5. Capul familiei poate trimite datele întregii familii din **Controlul familiei**.

Doar pentru cine administrează aplicația: ca să trimiți email și Telegram direct din aplicație, în Streamlit deschide Manage app, apoi Settings, apoi Secrets, și adaugă EMAIL_USER, EMAIL_PASSWORD și TELEGRAM_TOKEN (aceleași valori ca la notificări). Conține date sanitare: verifică bine cui le trimiți.""",
        'trimite partajare whatsapp email posta telegram sms pdf excel tiparire export atasament fisier'),
    "f_visite": ("🩺 Vizite, analize și rezultate",
        """1. Deschide fila **🩺 Visite** și atinge ca să adaugi.
2. Scrie **data**, **tipul vizitei sau analizei**, **medicul**, **motivul** și **indicațiile pentru controale**.
3. Dacă există, scrie data **următoarei programări**.
4. Atașează **rezultatele**: fotografie sau PDF.""",
        "vizita vizite analize rezultate programare specialist ataseaza"),
    "f_vaccini": ("💉 Vaccinuri și carnetul de vaccinare",
        """În fila **💉 Vaccini** înregistrezi vaccinările fiecărui profil și atașezi **carnetul de vaccinare** (fotografie sau PDF).""",
        "vaccin vaccinuri vaccinare carnet"),
    "f_scheda": ("🩸 Fișa medicală și «Il mio dottore»",
        """- Atinge chenarul **grupei de sânge** ca să deschizi **fișa medicală**: afecțiuni, alergii la medicamente, intervenții, istoric medical și vaccinări.
- Alături găsești **Il mio dottore** (Medicul meu): alege medic sau doctoriță, apoi scrie nume, adresă, telefon, e-mail, **programul** (un rând pe zi: de la, până la, note), **înlocuitorul** și notele.""",
        "fisa medicala medic medic de familie afectiuni interventii istoric program telefon email inlocuitor"),
    "f_tessera": ("🪪 Cardul de sănătate și dosarul medical",
        """Sus, lângă doctoriță, este insigna albastru deschis **Tessera sanitaria · Fascicolo sanitario** (pulsează încet ca să fie observată). Atinge-o.

**Cardul**
1. Atinge **👁️ Mostra fronte e retro della tessera**: îl vezi mare.
2. Cardul se ia din **I miei documenti**. Dacă nu l-ai introdus încă apare un avertisment cu butonul **📁 Vai a I miei documenti**: alege **Tessera sanitaria** și fă fotografia din față și din spate. Avertismentul dispare singur de îndată ce l-ai introdus.

**Legăturile online** (una pentru dosarul medical electronic, una pentru vaccinări, una pentru cheltuielile medicale deductibile)
1. Deschide pagina în browser și **copiază adresa** din bara de sus.
2. Întoarce-te aici și **lipește-o** în caseta potrivită.
3. Atinge **💾 Salva**.
4. De atunci apare un buton **🔗**: atingându-l se deschide direct pagina.
5. Ca să schimbi linkul atinge **✏️ Modifica**; ca să-l scoți atinge **🗑️ Togli il link**.

Legăturile sunt separate pentru fiecare profil al familiei.""",
        "card de sanatate tessera sanitaria dosar medical electronic fse link adresa vaccinari online cheltuieli medicale deductibile fata spate insigna"),
    "f_aperta": ("🔎 Găsește o farmacie deschisă",
        """Atinge butonul mare de sus (**Găsește o farmacie deschisă**): alege **țara** (pornește de la cea a limbii tale) și scrie **orice oraș sau cod poștal**. Aplicația caută farmaciile deschise lângă acel loc. Sau atinge **📍 Folosește locația mea (GPS)**: telefonul cere permisiunea și aplicația caută în jurul tău (locația nu se salvează).""",
        "farmacie deschisa gaseste cauta aproape garda noapte"),
    "f_avvisi": ("🔔 Notificări pe Telegram, e-mail și SMS",
        """Notificările îți amintesc expirările (la 60, 30, 14 și 7 zile, 1 zi și chiar în ziua respectivă) și, dacă vrei, ora tratamentelor. Alege **unul sau mai multe canale**.

### 📱 Telegram, pas cu pas
**Ce îți trebuie:** aplicația Telegram pe telefon și două minute. Telegram este gratuit.

1. **Instalează Telegram** din Play Store (Android) sau App Store (iPhone) și creează-ți contul: îți cere numărul de mobil.
2. **Deschide botul aplicației.** În Telegram atinge lupa 🔍 de sus și caută **Dispensa Leo**.
3. Atinge **Start** (sau scrie `/start`). **Acest pas este important:** dacă nu-l faci, botul nu îți poate scrie.
4. **Află-ți numărul (Chat ID).** Caută botul **@userinfobot**, deschide-l și atinge **Start**: îți răspunde cu **Id**-ul tău, un număr (de exemplu `123456789`). Ține apăsat ca să-l copiezi. Este un bot gratuit care îți spune doar acel număr.
5. **Întoarce-te pe această pagină.** Deschide **🔔 Scegli come ricevere gli avvisi**, bifează **📱 Telegram**, lipește numărul în câmpul **Chat ID** (doar cifre) și atinge **Salva**.
6. **Gata.** Notificările vin de la acel bot, începând cu următoarea trimitere automată (de obicei a doua zi dimineața).

**Dacă nu vine nimic:** verifică dacă ai atins *Start* în bot (pasul 3) și dacă numărul este corect, fără spații sau litere.

### ✉️ E-mail
**Pentru e-mail e foarte simplu: îți ajunge adresa.** Nu trebuie parolă sau alte setări.

1. Deschide **🔔 Scegli come ricevere gli avvisi**.
2. Bifează **✉️ Email**.
3. Scrie **adresa ta de e-mail** în câmp (de exemplu `nume@gmail.com`) și verifică dacă e corectă.
4. Atinge **Salva**.

Mesajele pleacă de la adresa de e-mail a aplicației. **Prima dată uită-te și în Spam sau Promoții** și, dacă îl găsești acolo, marchează-l „Nu este spam”: de atunci va ajunge în căsuța normală.

### 💬 SMS
Sunt cu plată și de obicei nu sunt active: întreabă administratorul.

Opțional: bifează **„Nei messaggi non scrivere i nomi dei medicinali”** (în mesaje să nu se scrie numele medicamentelor) dacă vrei mai multă confidențialitate.

Capul familiei, în același formular, poate activa și rezumatul zilnic al familiei și alerta când o persoană nu înregistrează o doză în 90 de minute. Rețetele care expiră curând trimit alerte cu 14, 7, 3 și 1 zile înainte și chiar în ziua respectivă.""",
        "notificari avertizari telegram chat id bot start userinfobot email sms memento mesaj primi activeaza numar gmail spam"),
    "f_report": ("🧾 Raport complet și date",
        """În **🧾 I miei dati personali e report completo** scrii nume și prenume și descarci un **raport de tipărit** cu tot ce ai introdus. Fișierul **JSON** conține aceleași date pentru o copie de siguranță.
Conține date medicale: nu-l da celor care nu trebuie să-l vadă.""",
        "raport complet tipareste exporta descarca date personale copie pdf json"),

    "u_cosa": ("🧰 La ce folosește pagina Utilitare",
        """Adună **aplicații și site-uri utile** într-un singur loc. Fiecare are un **buton mare care pulsează**: atinge-l și pornește.

Sub buton este **numele** aplicației: atingându-l se deschide **prospectul**, o explicație simplă a ce face și a avantajelor ei.

Deocamdată sunt **Velocity Music** (play-ul albastru deschis) și **Wimbi** (rața cu căști); aici se vor adăuga și alte utilitare.""",
        "utilitare pagina aplicatii butoane porneste colectie site-uri ce este la ce foloseste"),
    "u_avviare": ("▶️ Cum pornești o aplicație",
        """1. Din Pagina principală atinge pictograma **🧰 Utilità** (lângă Farmacia și I miei documenti).
2. Atinge **butonul mare** cu simbolul ▶️: aplicația se deschide într-o filă nouă a browserului.
3. Ca să te întorci aici, închide acea filă sau mergi înapoi.""",
        "porneste deschide lanseaza play buton aplicatie link velocity music muzica"),
    "u_bugiardino": ("📖 Cum citești prospectul",
        """1. Sub buton este **plăcuța cu numele** aplicației.
2. **Atinge-o**: se deschide o fereastră cu explicația (ce este, avantaje, adresă).
3. Înăuntru este și butonul **🎵 Avvia** ca să deschizi aplicația.
4. Ca să închizi fereastra atinge **X**-ul de sus.""",
        "prospect explicatie placuta nume citeste descriere avantaje informatii"),
    "u_wimbi": ("🦆 Wimbi",
        """Wimbi este o aplicație de muzică: **scrii o melodie sau un artist, atingi un rezultat și pornește**. Nu trebuie înregistrare, playlisturile rămân pe dispozitivul tău, muzica **continuă să cânte cu ecranul stins** și aplicația este disponibilă în **17 limbi**.

Atinge **rața cu căști** ca s-o pornești sau scrisul verde **Wimbi** ca să citești prospectul complet.
Adresa: https://wimbi.app/it/""",
        "wimbi rata casti muzica melodii artist playlist ecran stins limbi fara cont"),
    "u_velocity": ("🎵 Velocity Music",
        """Este un player și manager de muzică care îți permite să asculți **gratuit** biblioteca YouTube, **fără reclame** și **fără abonamente**. Poate fi folosit **ca invitat**, fără să creezi un cont. Proiectul este încă în dezvoltare, dar deja utilizabil.

Adresa: https://velocitymusic.uk/""",
        "velocity music youtube gratuit reclame player melodii asculta radio"),

    "x_cosa": ("🚀 La ce servesc «Documentele mele»",
        """Aici ții **documentele personale** (buletin, permis, pașaport, card de sănătate, permise, asigurări…) cu **fotografiile din față și din spate** și **termenele de expirare**.

Aplicația te avertizează **cu 6 luni înainte** (prima avertizare, portocalie) și **cu 3 luni înainte** (a doua avertizare, roșie și mai intensă), ca să ai timp să le reînnoiești.""",
        "documente ce este la ce foloseste buletin permis pasaport card de sanatate incepe introducere"),
    "x_aggiungere": ("➕ Cum adaugi un document",
        """1. Alege al cui este documentul din **👤 Documenti di**.
2. Atinge **➕ Aggiungi un documento**.
3. Alege **tipul** din listă. Dacă nu e acolo, scrie-l în caseta **„Non lo trovi?”**.
4. Scrie **numărul**, **eliberat de**, **data eliberării** și **data expirării**. Dacă nu expiră niciodată, bifează **„Questo documento non scade”**.
5. Fă **fotografia din față și din spate** (vezi ghidul de mai jos).
6. Atinge **💾 Salva il documento**.""",
        "adauga introdu nou document tip numar eliberat expirare nu expira salveaza"),
    "x_foto": ("📷 Fotografia din față și din spate (fundal scos și îndreptată)",
        """Sunt **două blocuri la fel: 📄 Fronte (Față) și 📄 Retro (Spate)**. Pentru fiecare:
1. Atinge **📷 Scatta la foto** (camera din spate) **sau** **📁 Carica dal telefono** dacă ai deja fotografia.
2. Aplicația scoate **fundalul** și **îndreaptă** singură documentul.
3. Dedesubt apare **editorul**: trage **rigla** ca să rotești și **cadrul** ca să tai.
4. Când e perfectă atinge **💾 Salva posizione e ritaglio**.
5. Dacă documentul a fost decupat prost bifează **„Tieni anche lo sfondo”**: imaginea rămâne întreagă și o aranjezi doar de mână.
6. Dacă ai greșit fotografia atinge **🗑️ Togli questa foto**.
7. La sfârșit atinge **💾 Salva il documento**: fotografiile se salvează împreună cu datele.

Pentru un **PDF** sau alte pagini folosește câmpul **„Altri file”** de sub formular.""",
        "foto fotografie fata spate incarca decupeaza fundal indreapta roteste rigla cadru imagine document"),
    "x_colori": ("🎨 Culorile și avertizările de expirare",
        """- 🟢 **Verde**: expiră peste mai mult de 6 luni.
- 🟠 **Portocaliu, prima avertizare**: expiră în mai puțin de 6 luni.
- 🔴 **Roșu, a doua avertizare**: expiră în mai puțin de 3 luni. Apare un chenar de alarmă.
- ⚫ **Expirat**: de reînnoit imediat.

Sus vezi contoarele. Dacă ai activat **Telegram** sau **e-mailul** (se face în Farmacie, la **Scegli come ricevere gli avvisi**), avertizările ajung și acolo.""",
        "culori expirare avertizari portocaliu rosu expirat sase luni trei luni reinnoieste alarma telegram email"),
    "x_cercare": ("🔎 Căutarea și filtrarea documentelor",
        """Deasupra listei este câmpul **Caută**: scrie tipul, numărul, instituția sau o notă. Alături alege o **categorie** ca să le vezi doar pe acelea.""",
        "cauta cautare gaseste filtru categorie lista"),
    "x_modificare": ("✏️ Modifici, deschizi și ștergi",
        """- **Deschide un document:** atinge **fișa lui colorată**: se deschide detaliul cu toate datele.
- **Vezi fața și spatele:** în detaliu atinge **👁️ Mostra fronte e retro** (Arată fața și spatele): le vezi mari și le poți **descărca**.
- **Modifică:** în detaliu atinge **✏️ Modifica**, schimbă datele sau adaugă alte fotografii, apoi salvează.
- **Scoate o singură fotografie:** în Modifica, în lista **Già allegato**, atinge 🗑️ lângă fișier.
- **Șterge documentul:** în detaliu atinge **🗑️ Elimina** și confirmă.""",
        "modifica schimba sterge elimina deschide atasament descarca scoate foto"),
    "x_tipi": ("⚙️ Tipurile de documente",
        """La sfârșitul paginii deschide **⚙️ Gestisci i tipi di documento**: poți **adăuga** tipurile tale, le poți **scoate** sau **ascunde** pe cele pe care nu le folosești.""",
        "tipuri tip categorii tip nou ascunde catalog"),
    "x_privacy": ("🔒 Confidențialitate",
        """Documentele conțin date personale: **nu trimite** capturi de ecran sau fișiere celor care nu trebuie să le vadă. Fiecare persoană vede doar ale ei.""",
        "confidentialitate securitate date personale trimite"),

    "tour1": ("Bun venit!", "Salut, sunt asistentul tău. Îți fac un tur rapid al aplicației. Cu butoanele Înainte și Înapoi mergi în ritmul tău și mă poți opri oricând."),
    "tour2": ("Cămara", "În Cămară ții lista a ce ai în casă. Atinge Adaugă, fotografiază produsul, scrie numele și expirarea. Culorile îți spun când să acționezi: verde liniștit, portocaliu sub două luni, roșu sub o lună."),
    "tour3": ("Alergeni și ingrediente", "Dacă alegi alergiile tale din meniul din stânga, produsele periculoase pentru tine se recunosc imediat și apare o sirenă. Pe fiecare fișă butonul Ingrediente arată compoziția."),
    "tour4": ("Farmacia", "Cu prima pictogramă intri în Farmacie: medicamente cu expirare, tratamente cu memento pe Telegram sau e-mail, vizite, vaccinuri și un profil pentru fiecare membru al familiei."),
    "tour5": ("Cardul de sănătate", "În Farmacie, lângă doctoriță, este insigna albastru deschis a cardului de sănătate: arată fața și spatele și te lasă să salvezi legăturile către dosarul medical, vaccinări și cheltuieli deductibile."),
    "tour6": ("Documentele mele", "Cu a doua pictogramă intri în Documentele mele. Fotografiază documentul: aplicația scoate fundalul, îl îndreaptă și încearcă să citească tipul, numărul și expirarea. Poți corecta oricând câmpurile. Te avertizează cu șase și cu trei luni înainte de expirare."),
    "tour7": ("Utilitarele", "Cu a treia pictogramă intri în Utilitare: aplicații utile ca Velocity Music și Wimbi. Atinge butonul ca să le pornești și numele ca să citești prospectul."),
    "tour8": ("Ajutor mereu la îndemână", "Sus, pe fiecare pagină, este butonul roșu Atinge pentru informații, cu ghidul și căutarea. Iar eu sunt aici: atinge-mă oricând, chiar și cu microfonul. Dacă nu-ți sunt de folos, mă dezactivezi din panou și mă reactivezi din butonul roșu. Spor la treabă!"),

    "nov1": ("Asistent digital", "Robotul mic și rotund din dreapta jos: atinge-l și îți explică aplicația cu voce tare, chiar și cu microfonul"),
    "nov2": ("Utilitar nou: Wimbi", "Pagina principală → Utilitare → rața cu căști; atinge scrisul verde pentru prospect"),
    "nov3": ("Pagină nouă „Utilitare”", "Pagina principală → a treia pictogramă albastru deschis „Utilità”, lângă Farmacia și I miei documenti"),
    "nov4": ("Ghid pe fiecare pagină", "Butonul roșu „Atinge pentru informații” sus, cu explicații și căutare"),
    "nov5": ("Card de sănătate și dosar medical", "Farmacie → insigna albastru deschis de lângă doctoriță"),
    "nov6": ("Documente: fotografie și citire automată", "Documentele mele → „Aggiungi un documento”"),
}

UI_TR["ro"] = {
    "dlg_titolo": "📖 Ghid și informații",
    "dlg_hint": "Atinge un subiect ca să-l deschizi. Sau scrie mai jos ce vrei să afli.",
    "dlg_cerca_label": "🔎 Ce vrei să afli?",
    "dlg_cerca_ph": "ex. cum fac fotografia pe spatele documentului",
    "dlg_trovato": "**Iată ce am găsit:**",
    "dlg_nulla": "Nu am găsit un răspuns cu aceste cuvinte. Încearcă să scrii altfel (de exemplu un singur cuvânt: *foto*, *expirare*, *parolă*) sau scrie o sugestie în fila Mesaje.",
    "dlg_tutti": "Toate subiectele",
    "dlg_nota_it": "ℹ️ Ecranele acestei secțiuni sunt deocamdată în italiană: numele butoanelor sunt scrise cum le vezi pe ecran.",
    "dlg_asst": "**🤖 Asistent digital** (robotul mic care vorbește și te ajută)",
    "dlg_on": "✅ Activează", "dlg_off": "⛔ Dezactivează",
    "info_help": "Atinge ca să citești cum se folosește această secțiune", "info_fallback": "ℹ️ Informații și ghid",
    "sez_dispensa": "🏠 Cămara", "sez_farmacia": "🏥 Farmacia", "sez_documenti": "📁 Documentele mele", "sez_utilita": "🧰 Utilitare",
    "a_aria": "Asistent digital", "a_rileggi": "📖 Explică-mi această pagină", "a_giro": "🧭 Tur ghidat al aplicației",
    "a_novita": "🆕 Ce e nou", "a_mic": "🎤 Pune o întrebare", "a_indietro": "◀ Înapoi", "a_avanti": "Înainte ▶", "a_fine": "Gata",
    "a_ph": "Scrie aici întrebarea ta…", "a_chiedi": "Întreabă", "a_voce_on": "🔊 Voce: activă", "a_voce_off": "🔇 Voce: oprită",
    "a_silenzio": "⏹ Liniște", "a_off": "⛔ Dezactivează asistentul", "a_ascolto_btn": "⏹ Ascult…",
    "a_ascolto_t": "Te ascult", "a_ascolto_x": "Vorbește acum: de exemplu „cum adaug o fotografie la document?”",
    "a_mic_t": "Microfon", "a_mic_no": "Pe acest telefon nu pot să te ascult: scrie întrebarea mai jos.",
    "a_mic_perm": "Permite browserului să folosească microfonul ca să vorbești cu mine.",
    "a_mic_err": "Acum nu pot folosi vocea: scrie întrebarea mai jos.",
    "a_nulla_t": "Nu am auzit nimic", "a_nulla_x": "Încearcă din nou: atinge microfonul și vorbește.",
    "a_dimmi_t": "Spune-mi", "a_dimmi_x": "Scrie sau spune ce vrei să afli.",
    "a_off_t": "Vrei să mă dezactivez?",
    "a_off_x": "Atinge butonul „⛔ Dezactivează asistentul” de mai jos. Mă reactivezi din butonul roșu „Atinge pentru informații”.",
    "a_trov_t": "Nu am găsit răspunsul",
    "a_trov_x": "Încearcă cu alte cuvinte (de exemplu doar unul: foto, expirare, parolă) sau alege un subiect mai jos.",
    "a_nov_none_t": "Noutăți", "a_nov_none_x": "Deocamdată nu sunt noutăți recente. Te anunț eu când apar!",
    "a_nov_voce": "Iată noutățile.", "a_nov_trovi": "O găsești așa:", "a_nov_t": "Ce e nou",
    "a_fine_t": "Sfârșitul turului", "a_fine_x": "Gata! Dacă ai nevoie de altceva, întreabă-mă.",
    "a_toast_off": "Asistent dezactivat. Îl reactivezi din „Atinge pentru informații”.", "a_toast_on": "Asistent activ: atinge robotul mic.",
    "a_vedi": "Atinge un subiect mai jos ca să afli mai multe.",
    "i_silenzio": "liniste taci stop destul opreste", "i_off": "dezactiv opreste inchide", "i_ass": "asistent robot",
    "i_novita": "noutat nou noua actualiz", "i_giro": "tur tutorial ghid inceput", "i_saluto": "salut buna ziua buna seara ajutor",
}
