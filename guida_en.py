# -*- coding: utf-8 -*-
"""Guida, giro guidato, novità e testi dell'assistente in INGLESE. Caricato da app_dispensa.py dopo info_sezioni.py.
Per le schermate Farmacia / I miei documenti / Utilità i nomi dei pulsanti restano come si vedono sullo schermo (in italiano)."""
GUIDA_TR["en"] = {
    "d_assistente": ("🤖 The digital assistant (the little robot)",
        """It is the **little yellow and blue robot** at the bottom right, with a round face. **Tap it** and its panel opens.

What it can do:
- **📖 Explain this page**: it tells you out loud what the page you are on is for.
- **🧭 Guided tour**: it explains the whole app step by step (Next and Back).
- **🆕 What's new**: it tells you the news and where to find it.
- **🎤 Ask a question**: tap, speak (for example «how do I add a photo to the document?») and it answers using the guide. Works on Chrome for Android.
- You can also **type** your question in the box.

**Voice:** it uses your phone's voice. If you don't want to hear it, tap **🔊 Voice: on** to turn it off.

**To turn it off:** tap **⛔ Turn off assistant** in its panel. To turn it back on, open the red button **Tap for information** and tap **✅ Turn on** in the assistant box. The choice is saved on your phone.""",
        "assistant robot voice speak microphone listen question tour news disable enable turn off help"),
    "d_inizio": ("🚀 What it is for and how to start",
        """**What it is for:** it keeps the list of what you have at home, when it expires and what it contains. It warns you before something goes bad.

**To start, 5 steps:**
1. Tap the **➕ Add** tab at the bottom.
2. Take a photo of the product (or skip it).
3. Write the name, how many units you have and the **expiry date**.
4. Tap the button to save.
5. Go back to the **🏠 Pantry** tab: the product is there, with the colour of its expiry.

The pantry is **yours only**: each person has their own password and nobody sees the products of others.""",
        "start begin first steps what is it what for how it works introduction use"),
    "d_aggiungere": ("➕ How to add a product",
        """1. Tap **➕ Add** (tab at the bottom).
2. At the top there is the **photo** area: tap **📷 Take the photo** (the rear camera opens) or **📁 Upload from phone**.
3. Write the **name** and the **brand**.
4. Write the **barcode** by hand (the numbers under the bars): the app fills in ingredients, values and allergens by itself, if the product is known.
5. Write **how many units**, the **weight** or how many **litres**.
6. Choose the **expiry date**.
7. In **«Where do you put it?»** choose: Pantry, Fridge, Freezer, Cellar, Shop, Storeroom or Other. The **Category** is free text.
8. Choose **who it is for**: adults, babies (0-2 years) or animals.
9. Save.

If you have no information at all, the **name, units and expiry** are enough.""",
        "add insert new product barcode qr fill where fridge freezer cellar category quantity units weight litres write"),
    "d_foto": ("📸 The product photo: shot, ruler and crop",
        """1. Tap **📷 Take the photo** or **📁 Upload from phone**.
2. The app removes the **background** and **straightens** the product by itself.
3. The **editor** appears below: drag the **ruler** to rotate the photo and drag the **frame** to crop the edges.
4. When it is perfect tap **💾 Save position and crop**.
5. Then save the product.

If the editor does not work, open **🛠️ Backup controls**: there are sliders to rotate and crop.""",
        "photo picture take shot camera rotate straighten crop cut background cutout ruler frame image"),
    "d_colori": ("🎨 Colours and expiry alerts",
        """- 🟢 **Green**: more than 2 months left. All fine.
- 🟠 **Orange**: expires within 2 months. Better use it.
- 🔴 **Red**: expires within 1 month. Use it soon.
- ⚫ **Dark**: already expired.

At the top you see the coloured **counters** and the alerts with how many units, grams or litres are about to expire.

Each section has its own **sound**: adults the usual sounds; babies one sound for the girl (2 months), one for the boy (1 month) and both if expired; animals the cat (2 months), the dog (1 month) and the lion if expired.

If you turned on **Telegram** or **email**, the alert arrives there too.""",
        "colours colors expiry alerts green orange red expired counters sound sounds siren notification when expires"),
    "d_allergeni": ("🌾 Allergens, ingredients, vegan and gluten-free",
        """1. Open the **left menu** (the **»** arrow at the top left) and choose **your allergies**.
2. Products with an allergen have a **yellow button** with its name (for example *Gluten*): tap it and the **composition** opens, with the dangerous words highlighted.
3. If the allergen is **dangerous for you** the **flashing siren** appears, saying who it is not suitable for.
4. Every card has the **Ingredients** button: it opens the whole text to read, in your language.
5. The **Vegan** and **Vegetarian** buttons only appear if the product really is. The **Gluten-free** button has a gold border.""",
        "allergens allergy gluten ingredients vegan vegetarian gluten free composition intolerance siren dangerous"),
    "d_pulsanti": ("🔘 The buttons of each product: Delete, Info, Edit",
        """In **Cards**, under each product there are three buttons:
- **Delete**: removes the product. If you have the same product with several expiry dates, it asks **which entry** to delete.
- **Info**: opens the full guide with all the symbols.
- **Edit**: changes any detail (name, expiry, photo, quantity…).

In **Table** you tick the 🗑️ box of the row and then tap **Delete ticked rows** or **Edit the ticked row** (to edit, tick one row only).""",
        "delete remove bin trash edit change correct info table cards view"),
    "d_icone": ("🧭 The Pharmacy, My documents and Utilities icons",
        """In the Home, next to the search controls, there are **three pulsing icons**:
- **🏥 Pharmacy**: medicines, therapies, visits, health card.
- **📁 My documents**: ID card, driving licence, health card with their expiry dates.
- **🧰 Utilities**: useful apps and sites, like Velocity Music.

Tap one to open it; to come back tap **← Back to pantry**. On every page, at the top, there is the red button **Tap for information** with the guide.""",
        "icons pharmacy documents utilities home pages navigate menu where do I find"),
    "d_cercare": ("🔎 Searching and filtering products",
        """At the top of the Pantry there are three controls:
1. **🔎 Search**: write the name or the brand.
2. **Show**: choose *All*, *Only expiring (2 months)*, *Only red (1 month)* or *Expired*.
3. **View**: *Cards* (with big photos) or *Table* (compact list).""",
        "search find filter show view cards table list"),
    "d_spesa": ("🛒 Shopping list and flyers",
        """- When a product **runs out** it goes by itself to the **🛒 Shopping** tab.
- In the Shopping tab you can tap **I used one** to subtract a unit.
- On the product card, to the right of the quantity, there is the link to the **flyers** of supermarkets, hypermarkets and discount stores: choose the **country** (it starts from the one of your language) and write the **city**, look at the offers and tap the button to put the product in the **shopping list**, with the shop name.""",
        "shopping list buy flyers offers supermarket used finished city shop"),
    "d_gestisci": ("✏️ Manage many products at once",
        """The **✏️ Manage** tab is for changing **quantity, expiry dates and notes** of many products in one go, without opening them one by one.""",
        "manage edit many more products together quantity expiry notes"),
    "d_account": ("👤 Password, language and messages",
        """- **Password:** it is given to you by whoever manages the app. At first access you can change it. It is only yours.
- **Language:** in the left menu there is **🌐 Language**.
- **Messages and suggestions:** for an idea, a problem or a request use the **✉️ Messages / 💬 Suggestions** tab: the administrator reads it.""",
        "password account login language messages suggestions administrator problem request change"),
    "d_aiuto": ("🛟 If something goes wrong",
        """1. **Reload the page** of the browser.
2. The photo does not appear? Use **🛠️ Backup controls** or choose another photo.
3. The microphone for dictation works on **Chrome for Android**: tap once to turn it on, once to turn it off.
4. If the problem remains, write it in the **Messages** tab: it helps the administrator fix it.""",
        "problem error not working help stuck photo missing microphone dictation"),

    "f_cosa": ("🚀 What the Pharmacy is for",
        """Here you keep in order the **medicines at home** and their **expiry dates**, the **therapies**, the **visits**, the **vaccines**, your **doctor** and your **health record**.

The app **reminds you** and organises what you enter. It **does not give medical advice** and does not change therapies: for doses and treatments always follow your doctor or pharmacist.""",
        "pharmacy what is it what for medicines start introduction"),
    "f_profili": ("👤 Family profiles and blood group",
        """Each person has a **profile** (up to 12): mum, dad, children…
1. At the top choose the profile from **👤 Profilo**.
2. To add one open **👥 Gestisci profili**, write the name and tap **Aggiungi profilo**.
3. In the same place you can change the name and choose the **🩸 blood group**: it appears as a coloured **drop** next to the profile.
4. To delete a profile tick the confirmation and tap **Elimina profilo** (all its data is deleted too).""",
        "profile profiles family person blood group drop name add delete"),
    "f_medicinale": ("💊 How to add a medicine",
        """1. Tap **➕ Aggiungi medicinale**.
2. At the top the **photo of the box**: **📷 Scatta la foto** or **📁 Carica dal telefono**; then straighten with the ruler, crop with the frame and tap **💾 Salva posizione e ritaglio**.
3. Write **name**, **active ingredient**, **dosage**, **form** (tablets, syrup…) and **quantity**.
4. Choose the **expiry** and **who it is for**.
5. Tap **Salva**.

You can reuse a photo already saved from the **photo archive**. You can attach the **leaflet** to the medicine (PDF, photo or link).""",
        "medicine medicines drug add box photo expiry active ingredient dosage leaflet archive"),
    "f_scadenze": ("🎨 Expiry and drug allergies",
        """- 🟠 **Orange**: expires within 2 months. 🔴 **Red**: within 1 month. ⚫ **Expired**: dispose of it correctly.
- In the profile card you can write the **drug allergies**: if a medicine contains that active ingredient a **red warning** appears.""",
        "expiry colours allergy allergies drugs red warning orange expired"),
    "f_terapie": ("📅 Therapies and calendar",
        """1. Open the **📅 Terapie** tab.
2. Add a therapy: **medicine**, **days**, **times** and quantity.
3. At the set time tap **Presa** (taken) to record it: it stays in the **history**.
4. A therapy can be **active**, **suspended** or **finished**. Test therapies can be **deleted**.
5. The **calendar** shows the week and the month.
6. The **Report for the doctor** (period of your choice) can be printed or opened in Excel.""",
        "therapy therapies calendar intake taken times report doctor history pill dose"),
    "f_visite": ("🩺 Visits, tests and reports",
        """1. Open the **🩺 Visite** tab and tap to add.
2. Write the **date**, **type of visit or test**, **doctor**, **reason** and the **instructions for check-ups**.
3. If there is one, write the date of the **next appointment**.
4. Attach the **reports**: photo or PDF.""",
        "visit visits exam test report analysis appointment specialist attach"),
    "f_vaccini": ("💉 Vaccines and vaccination record",
        """In the **💉 Vaccini** tab you record the vaccinations of each profile and attach the **vaccination record** (photo or PDF).""",
        "vaccine vaccines vaccination record booklet"),
    "f_scheda": ("🩸 The health record and «My doctor»",
        """- Tap the **blood group** box to open the **health record**: conditions, drug allergies, operations, medical history and vaccinations.
- Next to it you find **Il mio dottore** (My doctor): choose doctor (male or female), then write name, address, phone, email, the **hours** (one row per day: from, to, notes), the **substitute** and notes.""",
        "health record doctor family doctor conditions operations history hours phone email substitute"),
    "f_tessera": ("🪪 Health card and health file",
        """At the top, next to the doctor, there is the light-blue badge **Tessera sanitaria · Fascicolo sanitario** (it pulses gently to be noticed). Tap it.

**The card**
1. Tap **👁️ Mostra fronte e retro della tessera**: you see it big.
2. The card is taken from **I miei documenti**. If you have not entered it yet a warning appears with the button **📁 Vai a I miei documenti**: choose **Tessera sanitaria** and take the photo of front and back. The warning disappears by itself as soon as you have entered it.

**The online links** (one for the electronic health file, one for vaccinations, one for deductible medical expenses)
1. Open the page in the browser and **copy the address** from the bar at the top.
2. Come back here and **paste it** in the right box.
3. Tap **💾 Salva**.
4. From then on a **🔗** button appears: tapping it opens the page directly.
5. To change the link tap **✏️ Modifica**; to remove it tap **🗑️ Togli il link**.

The links are separate for each family profile.""",
        "health card tessera sanitaria electronic health file fse link address vaccinations online deductible medical expenses front back badge"),
    "f_aperta": ("🔎 Find an open pharmacy",
        """Tap the big button at the top (**Find an open pharmacy**): choose the **country** (it starts from the one of your language) and write **any city or postcode**. The app looks for pharmacies open near that place.""",
        "pharmacy open find search nearby night"),
    "f_avvisi": ("🔔 Alerts on Telegram, email and SMS",
        """Alerts remind you of expiry dates (at 60, 30, 14 and 7 days, 1 day and the day itself) and, if you want, of the time of your therapies. Choose **one or more channels**.

### 📱 Telegram, step by step
**What you need:** the Telegram app on your phone and two minutes. Telegram is free.

1. **Install Telegram** from the Play Store (Android) or App Store (iPhone) and create your account: it asks for your mobile number.
2. **Open the app's bot.** Inside Telegram tap the magnifier 🔍 at the top and search for **Dispensa Leo**.
3. Tap **Start** (or write `/start`). **This step is important:** if you skip it, the bot cannot write to you.
4. **Find your number (Chat ID).** Search for the bot **@userinfobot**, open it and tap **Start**: it replies with your **Id**, a number (for example `123456789`). Hold it pressed to copy it. It is a free bot that only tells you that number.
5. **Come back to this page.** Open **🔔 Scegli come ricevere gli avvisi**, tick **📱 Telegram**, paste the number in the **Chat ID** field (numbers only) and tap **Salva**.
6. **Done.** Alerts come from that bot, starting from the next automatic send (usually the next morning).

**If nothing arrives:** check that you tapped *Start* in the bot (step 3) and that the number is right, with no spaces or letters.

### ✉️ Email
**Email is very simple: your address is enough.** No password or other settings.

1. Open **🔔 Scegli come ricevere gli avvisi**.
2. Tick **✉️ Email**.
3. Write **your email address** in the field (for example `name@gmail.com`) and check it is right.
4. Tap **Salva**.

Messages are sent from the app's email address. **The first time also look in Spam or Promotions** and, if you find it there, mark it as «Not spam»: from then on it will arrive in the normal inbox.

### 💬 SMS
They are paid and usually not active: ask the administrator.

Optional: tick **«Nei messaggi non scrivere i nomi dei medicinali»** (do not write medicine names in messages) if you want more privacy.""",
        "alerts notifications telegram chat id bot start userinfobot email sms reminder message receive activate number gmail spam mail"),
    "f_report": ("🧾 Full report and data",
        """In **🧾 I miei dati personali e report completo** write your name and surname and download a **report to print** with everything you entered. The **JSON** file contains the same data as a backup copy.
It contains health data: do not share it with those who should not see it.""",
        "report full print export download personal data copy pdf json"),

    "u_cosa": ("🧰 What the Utilities page is for",
        """It gathers **useful apps and sites** in one place. Each has a big **pulsing button**: tap it and it starts.

Under the button there is the app's **name**: tapping it opens the **leaflet**, a simple explanation of what it does and its advantages.

For now there are **Velocity Music** (the light-blue play) and **Wimbi** (the duck with headphones); other utilities will be added here.""",
        "utilities page apps buttons start collection sites what is it what for"),
    "u_avviare": ("▶️ How to start an app",
        """1. From the Home tap the **🧰 Utilità** icon (next to Farmacia and I miei documenti).
2. Tap the **big button** with the ▶️ symbol: the app opens in a new browser tab.
3. To come back here, close that tab or go back.""",
        "start open launch play button app link velocity music"),
    "u_bugiardino": ("📖 How to read the leaflet",
        """1. Under the button there is the **plate with the name** of the app.
2. **Tap it**: a window opens with the explanation (what it is, advantages, address).
3. Inside there is also the **🎵 Avvia** button to open the app.
4. To close the window tap the **X** at the top.""",
        "leaflet explanation plate name read description advantages information"),
    "u_wimbi": ("🦆 Wimbi",
        """Wimbi is a music app: **type a song or an artist, tap a result and it plays**. No sign-up needed, playlists stay on your device, the music **keeps playing with the screen off** and the app is available in **17 languages**.

Tap the **duck with headphones** to start it, or the green **Wimbi** writing to read the full leaflet.
Address: https://wimbi.app/it/""",
        "wimbi duck headphones music songs artist playlist screen off languages without account"),
    "u_velocity": ("🎵 Velocity Music",
        """It is a music player and manager that lets you listen **for free** to the YouTube library, **without ads** and **without subscriptions**. It can be used **as a guest**, without creating an account. The project is still in development but already usable.

Address: https://velocitymusic.uk/""",
        "velocity music youtube free ads player songs listen radio"),

    "x_cosa": ("🚀 What «My documents» is for",
        """Here you keep your **personal documents** (ID card, driving licence, passport, health card, permits, insurance…) with **front and back photos** and **expiry dates**.

The app warns you **6 months before** (first alert, orange) and **3 months before** (second alert, red and stronger), so you have time to renew them.""",
        "documents what is it what for id card licence passport health card start introduction"),
    "x_aggiungere": ("➕ How to add a document",
        """1. Choose whose document it is from **👤 Documenti di**.
2. Tap **➕ Aggiungi un documento**.
3. Choose the **type** from the list. If it is not there, write it in the box **«Non lo trovi?»**.
4. Write **number**, **issued by**, **issue date** and **expiry date**. If it never expires, tick **«Questo documento non scade»**.
5. Take the **photo of front and back** (see the guide below).
6. Tap **💾 Salva il documento**.""",
        "add insert new document type number issued expiry never expires save"),
    "x_foto": ("📷 Front and back photo (background removed and straightened)",
        """There are **two identical blocks: 📄 Fronte (Front) and 📄 Retro (Back)**. For each one:
1. Tap **📷 Scatta la foto** (rear camera) **or** **📁 Carica dal telefono** if you already have the photo.
2. The app removes the **background** and **straightens** the document by itself.
3. The **editor** appears below: drag the **ruler** to rotate and the **frame** to crop.
4. When it is perfect tap **💾 Salva posizione e ritaglio**.
5. If the document was cropped badly tick **«Tieni anche lo sfondo»**: the image stays whole and you adjust it by hand only.
6. If you took the wrong photo tap **🗑️ Togli questa foto**.
7. At the end tap **💾 Salva il documento**: the photos are saved together with the data.

For a **PDF** or other pages use the **«Altri file»** field under the form.""",
        "photo take front back upload cutout background straighten rotate crop ruler frame image document"),
    "x_colori": ("🎨 Colours and expiry alerts",
        """- 🟢 **Green**: expires in more than 6 months.
- 🟠 **Orange, first alert**: expires within 6 months.
- 🔴 **Red, second alert**: expires within 3 months. An alarm box appears.
- ⚫ **Expired**: renew right away.

At the top you see the counters. If you turned on **Telegram** or **email** (done in the Pharmacy, in **Scegli come ricevere gli avvisi**), alerts arrive there too.""",
        "colours colors expiry alerts orange red expired six months three months renew alarm telegram email"),
    "x_cercare": ("🔎 Searching and filtering documents",
        """Above the list there is the **Search** field: write the type, the number, the issuer or a note. Next to it choose a **category** to see only those.""",
        "search find filter category list"),
    "x_modificare": ("✏️ Editing, opening and deleting",
        """- **Open a photo:** tap the file name under the document: you see it big and can **download** it.
- **Edit:** tap **Modifica**, change the data or add more photos, then save.
- **Remove a single photo:** in Edit, in the **Già allegato** list, tap 🗑️ next to the file.
- **Delete the document:** tap **Elimina** and confirm.""",
        "edit change delete remove open attachment download photo"),
    "x_tipi": ("⚙️ Document types",
        """At the bottom of the page open **⚙️ Gestisci i tipi di documento**: you can **add** your own types, **remove** them or **hide** those you don't use.""",
        "types type categories new type hide catalogue"),
    "x_privacy": ("🔒 Privacy",
        """Documents contain personal data: **do not share** screenshots or files with those who should not see them. Each person sees only their own.""",
        "privacy security personal data share"),

    "tour1": ("Welcome!", "Hello, I am your assistant. I will give you a quick tour of the app. With the Next and Back buttons you go at your own pace, and you can stop me whenever you like."),
    "tour2": ("The Pantry", "In the Pantry you keep the list of what you have at home. Tap Add, photograph the product, write the name and the expiry date. The colours tell you when to act: green is fine, orange within two months, red within one month."),
    "tour3": ("Allergens and ingredients", "If you choose your allergies in the left menu, products dangerous for you are recognised at once and a siren appears. On every card the Ingredients button shows the composition."),
    "tour4": ("The Pharmacy", "With the first icon you enter the Pharmacy: medicines with expiry, therapies with reminders on Telegram or email, visits, vaccines and a profile for each family member."),
    "tour5": ("Health card", "In the Pharmacy, next to the doctor, there is the light-blue health card badge: it shows front and back and lets you save the links to the health file, vaccinations and deductible expenses."),
    "tour6": ("My documents", "With the second icon you enter My documents. Take a photo of the document: the app removes the background, straightens it and tries to read type, number and expiry. You can always correct the fields. It warns you six and three months before expiry."),
    "tour7": ("The Utilities", "With the third icon you enter the Utilities: useful apps such as Velocity Music and Wimbi. Tap the button to start them and the name to read the leaflet."),
    "tour8": ("Help always at hand", "At the top of every page there is the red button Tap for information, with the guide and the search. And I am here: tap me whenever you want, even with the microphone. If you don't need me, turn me off from the panel, and turn me on again from the red button. Enjoy!"),

    "nov1": ("Digital assistant", "The round little robot at the bottom right: tap it and it explains the app out loud, even with the microphone"),
    "nov2": ("New utility: Wimbi", "Home → Utilities → the duck with headphones; tap the green writing for the leaflet"),
    "nov3": ("New «Utilities» page", "Home → third light-blue icon «Utilità», next to Farmacia and I miei documenti"),
    "nov4": ("Guide on every page", "Red button «Tap for information» at the top, with explanations and search"),
    "nov5": ("Health card and health file", "Pharmacy → light-blue badge next to the doctor"),
    "nov6": ("Documents: photo and automatic reading", "My documents → «Aggiungi un documento»"),
}

UI_TR["en"] = {
    "dlg_titolo": "📖 Guide and information",
    "dlg_hint": "Tap a topic to open it. Or write below what you want to know.",
    "dlg_cerca_label": "🔎 What do you want to know?",
    "dlg_cerca_ph": "e.g. how do I take a photo of the back of the document",
    "dlg_trovato": "**Here is what I found:**",
    "dlg_nulla": "I did not find an answer with these words. Try writing it differently (for example just one word: *photo*, *expiry*, *password*) or write a suggestion in the Messages tab.",
    "dlg_tutti": "All topics",
    "dlg_nota_it": "ℹ️ The screens of this section are for now in Italian: button names are written as you see them on the screen.",
    "dlg_asst": "**🤖 Digital assistant** (the little robot that talks and helps you)",
    "dlg_on": "✅ Turn on", "dlg_off": "⛔ Turn off",
    "info_help": "Tap to read how to use this section", "info_fallback": "ℹ️ Information and guide",
    "sez_dispensa": "🏠 Pantry", "sez_farmacia": "🏥 Pharmacy", "sez_documenti": "📁 My documents", "sez_utilita": "🧰 Utilities",
    "a_aria": "Digital assistant", "a_rileggi": "📖 Explain this page", "a_giro": "🧭 Guided tour of the app",
    "a_novita": "🆕 What's new", "a_mic": "🎤 Ask a question", "a_indietro": "◀ Back", "a_avanti": "Next ▶", "a_fine": "End",
    "a_ph": "Write your question here…", "a_chiedi": "Ask", "a_voce_on": "🔊 Voice: on", "a_voce_off": "🔇 Voice: off",
    "a_silenzio": "⏹ Silence", "a_off": "⛔ Turn off assistant", "a_ascolto_btn": "⏹ Listening…",
    "a_ascolto_t": "I'm listening", "a_ascolto_x": "Speak now: for example «how do I add a photo to the document?»",
    "a_mic_t": "Microphone", "a_mic_no": "On this phone I cannot listen to you: write the question below.",
    "a_mic_perm": "Allow the browser to use the microphone so you can talk to me.",
    "a_mic_err": "I cannot use the voice now: write the question below.",
    "a_nulla_t": "I heard nothing", "a_nulla_x": "Try again: tap the microphone and speak.",
    "a_dimmi_t": "Go ahead", "a_dimmi_x": "Write or say what you want to know.",
    "a_off_t": "Do you want me to turn off?",
    "a_off_x": "Tap the «⛔ Turn off assistant» button below. You can turn me on again from the red button «Tap for information».",
    "a_trov_t": "I did not find the answer",
    "a_trov_x": "Try other words (for example just one: photo, expiry, password) or choose a topic below.",
    "a_nov_none_t": "News", "a_nov_none_x": "There is no recent news for now. I will tell you when there is!",
    "a_nov_voce": "Here is the news.", "a_nov_trovi": "You find it like this:", "a_nov_t": "What's new",
    "a_fine_t": "End of the tour", "a_fine_x": "That's it! If you need anything else, ask me.",
    "a_toast_off": "Assistant turned off. You can turn it on again from «Tap for information».", "a_toast_on": "Assistant on: tap the little robot.",
    "a_vedi": "Tap a topic below to learn more.",
    "i_silenzio": "silence quiet stop shut enough", "i_off": "disable turn off deactivate switch off", "i_ass": "assistant robot",
    "i_novita": "news new update updates what's new", "i_giro": "tour tutorial walkthrough start guide", "i_saluto": "hello hi hey help good morning good evening",
}
