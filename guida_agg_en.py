# -*- coding: utf-8 -*-
"""Instructions updated on 20/11/2026 — ENGLISH (see guida_aggiornamento.py)."""

ga_traduci("en", {
    "x_campanello": ("🔔 The bell: alerts of this section", """In every section, under the coloured buttons, there is **🔔 Alerts of this section**. Tap it: a window tells you **how the alerts are set** and **what is about to expire**.

From there you can change:
- **Receive the alerts of this section**: the switch turns them on or off.
- **How many days before**: choose the days (0 = the same day).
- **I choose the time**: tick it and choose the time, then press **Enter** on the keyboard. Without a chosen time, alerts arrive in the morning.
- **Where to receive the alerts**: «like the other sections» or choose among **Telegram, Email, WhatsApp, SMS**.
- **Calendar**: turn on «See these alerts in the calendar too» and press **Download the calendar**; open the file and Android offers **Google Calendar**. If a date changes, download and open it again (events are updated, not duplicated).
- **Back as before** restores everything.

Press **💾 Save** to keep your choices. **First** write your contacts (Telegram, email, WhatsApp, SMS) in **Salute → Choose how to receive alerts**: without a contact that channel does not start. Alerts are sent by an automatic program: sometimes a few minutes late; a missed message is recovered within 3 hours, only once.""",
                     "bell alerts days time channels telegram email whatsapp sms sound calendar google calendar"),
    "x_riuso_archivio": ("🗂️ Reusing a file already in the archive", """If you already have a file or a photo in the archive **you do not need to redo it**:
- **Salute** (visits, prescriptions, documents, vaccines): under «take or choose a file» there is **🗂️ Or attach from the archive**. Type to search, choose the file and save: the same file is used, without copying it.
- **Casa, Work (payslips), Car, Animals**: in the box where you upload a file open **🗂️ Or choose a file already in the archive**, choose it and press **📥 Use this file**: it is read as if you had just uploaded it.
- **Pantry** (product photo): **🗂️ Choose from the archive** shows the photos already used, also of finished products.""",
                         "archive reuse file photo already saved choose from archive attach without redoing"),
    "x_numeri_utili": ("📞 Useful numbers and 📅 Appointments", """In every section (except the Pantry), under the bell, there are two buttons.

**📞 Useful numbers** is your address book of who is needed in that section: **name, job, field, office phone and mobile, hours, website, email, address**.
- If there is a job, tick **«There is a quote»**: status, amount, **start and end dates** and the **PDF or photo of the quote**.
- In **«Documents received»** put PDFs, photos, invoices, contracts.
- With **«Open quote, files and payments»** you record **deposits, instalments and balance** and see how much is paid and how much is left.
- There is also a **Notes** field, and buttons to call, WhatsApp, email, open the map or the website.

**Whose are they?** In **Salute, My documents and Casa**, where you choose a person, numbers and appointments are **separate for each person**.

**📅 Appointments**: **name, role, date, time, phone, reason and notes**. At the top you see the **next ones**, in date order; past or done ones are grouped below. With **«Put in the phone calendar»** the appointment goes into the calendar with a reminder.""",
                       "useful numbers address book appointments quote payments deposit balance contacts calendar"),
    "x_conti_casa": ("💶 Keeping the accounts", """In **Casa** tap **💶 Keeping the accounts**. Add as many items as you want: **current accounts** (with the bank), **Postepay**, **postal savings books**, **BOT, BTP**, funds, shares, postal bonds, cash. You see the **total** at the top and at the bottom, the **subtotals** by type and a **Notes** field. For government bonds you can also note the maturity date. **Each person has their own accounts**: if in Casa you chose, for example, your mother, the button becomes **«Accounts of …»**. The accounts of one person never mix with the others'.""",
                     "accounts money bank current account postepay savings bonds btp bot total subtotal person"),
    "x_badante": ("👵 Carer (administrator only)", """In **Casa**, for the administrator only, there is **👵 Carer**.
- Set the **rate** (usually €20 for 2 hours), the days she comes and from which day to count.
- **Every day counts by itself as «came»** (2 hours, the usual rate), from the day of the first money handed over: tap **❌ Did not come** only if she did not come; if she stayed more or fewer hours use **«Another day or another amount»**.
- With **«I gave money to my mother»** you record how much you handed over and when.
- The app calculates what is left and **until when the money lasts**.
- **🔔 Carer alerts** warns you **3 days before** and **on the last day** (you can change the days).
- There are also the **carer's contacts** and **notes**.""",
                  "carer caregiver badante hours rate came money mother alerts"),
    "x_interruttori": ("💡 Switch selectors", """Throughout the app the pill selectors (to choose a person, a house, a vehicle…) work like **switches**: the **active one is neon blue and pulses**, the others look **switched off**.""",
                       "switch selector pill active neon"),
    "x_ia": ("🤖 Artificial intelligence: documents, handwriting, warning lights, languages", """With the **keys** of the artificial intelligence services (free: Groq, Google Gemini, OpenRouter, NVIDIA, Cloudflare, Cohere, Hugging Face, SambaNova with trial credit; **DeepSeek** paid, optional) the app:
- **reads and classifies health documents** (what document it is, medical area, test, dates, doctor, facility, conclusions). If it is **handwritten**, **several services** read it and an «arbiter» compares the readings: you see **who read it**, the **limits** and **what to check** on the paper. Nothing is saved without your confirmation;
- **recognises car warning lights**, comparing several readings when the photo is uncertain;
- **translates the pages** into the chosen language (the first time a page opens; then it stays saved for everyone);
- makes **the assistant** answer in the chosen language.
If a service is exhausted or slow, the app moves on to the next one by itself.

**DeepSeek is paid**: only **the administrator** and the people he chooses can use it (Utilities → 🤖 → DeepSeek → **🔒 Who can use it**). The same row shows the **💰 remaining credit**. Automatic translations never use paid services.

The administrator enters the keys in **Utilities → 🤖 Artificial intelligence**, with the step-by-step guide; **🔄 Check the keys again** and the **test** of each service tell you if it works. Note: with Google's free keys texts may be used to improve their models.""",
             "artificial intelligence ai keys gemini groq openrouter nvidia cloudflare cohere hugging face sambanova deepseek credit who can use handwriting warning lights translation"),
    "x_compleanni": ("🎂 Birthdays: the people's cards", """In **Utilities → 🎂 Birthdays** tap the **«Happy birthday» badge** to open the list (tap it again to close it).

- **➕ Add a person**: name and date of birth (if you do not know the year tick **«I don't know the year»**). The rest is optional: **photo, place of birth, surname, nickname, mobile, phone, WhatsApp, Telegram, email, address, website, gift ideas, notes**. In **«Who is this person to you»**, if you choose **Other**, you can write the right word yourself.
- **The photo**: tap «Choose the photo»; **pinch with two fingers** to zoom and **drag** to move it until the face is inside the oval. Later you can **🔄 Recentre** it.
- Each person has a **card with a neon frame** in the colour of their **zodiac sign**, chosen from the date. **The signs move** (Aries headbutts with fiery eyes, Pisces swim slowly, Cancer walks sideways…).
- Under the card there are buttons to **call, WhatsApp, Telegram, email, website**. The list is in order of **next birthday** («🎉 Today!» if it is today).
- If **the person has passed away**, tick **🕯️ This person is no longer with us**: a **lit candle** appears, the card goes into **In memory** and you find **⚰️ Where they rest** (type of burial, cemetery, position, concession, votive lamp, cemetery phone and hours, photos of the headstone), the **eternal rest prayer**, **✍️ a thought** and **🎙️ a voice message**.
- The **green ⏻ button** inside the card opens the **📖 Diary of memories** (see its card).
- ✏️ **Edit** changes the data (what you do not touch stays as it was); 🗑️ **Delete** sends the card to the Bin.""",
                     "birthdays birthday zodiac sign card person photo contacts whatsapp telegram passed away candle memory burial diary"),
    "x_diario": ("📖 The Diary of memories (photos, texts, music)", """Inside the card of each person in **🎂 Birthdays**, bottom right, there is the **green ⏻ button**. Tap it: **the card disappears and the diary opens**, with the photos stacked like the pages of a book.

- **Turning pages**: **◀ Back** and **Next ▶** at the top. The **red ⏻ button**, between the two, closes the diary and the card comes back.
- **Automatic scrolling**: the photos change by themselves every **7 seconds**; in **⏱️ Automatic scrolling** choose the seconds or turn it off. Each photo **comes in and goes out with a different effect**.
- **Adding photos**: **➕ Add more photos** (as many as you want, there is no limit). For each photo you see a **preview**: **pinch** with two fingers to zoom and **drag** to move; you can write **coloured texts** (colour, font, size, position) and place **icons** (hearts, flowers, candles…). Then **💾 Save the page**. Photos are made lighter automatically without losing quality.
- **Changing later**: with **✏️ Texts and icons** you remove or change texts and icons whenever you want; **↩️ Undo the last change** puts things back (the original photo is never touched). In **🗂️ Manage pages** you move a page **⬆️ ⬇️**, **🔄 change the photo** or **🗑️ delete** it.
- **Music**: in **🎵 Diary music** choose an **MP3** file (it saves by itself). It starts when you tap the green button; at the bottom the **volume bar** (tap or drag) and ▶/🔊 to pause. To change it, choose another file.""",
                 "diary of memories diary photos pages green button red scrolling music mp3 volume texts icons effects manage pages birthdays"),
    "f_ia_documenti": ("🤖 Having documents re-read and reclassified by AI", """In **Salute → Health documents** open **🤖 Reclassify documents with AI**.

1. You see **«To check: X of Y»**: the AI reads **only the documents not yet checked** (tick «Re-read also those already checked» to re-read them all).
2. Tap **🔍 Test: read and classify**. A **box that is always open** appears and updates by itself: which document it has reached, for how many seconds, which service it is asking, how many it has read, how long is left. The moving dots **●●●○** mean it is working.
3. **You can use other apps or turn off the screen**: reading goes on by itself. Each document is saved as soon as it is read, so nothing is lost.
4. A document that stays stuck is **skipped after about 2 minutes** («too slow, skipped») and tried again next time. **⏹ Stop reading** keeps those already read.
5. The **🟡 AI proposals to confirm** appear in the same box, one per document: leave ticked what is right and tap **✅ Apply**; **✖ Do not apply** leaves everything as it is. What you corrected by hand is never touched.

**🔄 Re-read the documents already archived** (reading without AI) also shows **«To re-read: X of Y»** and does not propose again those already done.""",
                       "reclassify documents ai artificial intelligence re-read reading in progress proposals apply checked background other apps stop"),
    "f_numeri_doc": ("🔢 The No. of the health documents (for the doctor)", """Each health document has a **number**: **No. 1 is the most recent**, then down to the oldest. You see it in a **green box** on each card and in the **No.** column of the Salute **PDF summary**.

**What it is for:** give the summary to the doctor; he tells you «bring me 4, 12 and 17». Write the number (for example **12**) in the **🔍 Search** box of the Health documents and **only that document** appears.

**Note:** when you add a new document it becomes No. 1 and the others **move down by one**. If you have added documents in the meantime, **create the PDF summary again**. In the PDF dates no longer wrap onto two lines.""",
                     "number documents no doctor summary pdf search number order most recent bring me"),
    "f_gruppo": ("🩸 Blood group and certificate", """In the person's card in **Salute**: if the blood group is missing, tap **🩸 Enter the blood group**, choose it and save. You can change it at any time with **Edit**.

Below you can **attach the blood group certificate** (PDF or photo): choose the file and it saves by itself. You can view it, download it or remove it whenever you want.""",
                 "blood group blood type certificate attach pdf photo person card"),
    "f_wiki": ("📖 «What is it?»: simple explanation from Wikipedia", """In **Salute → Health documents** and in **Salute → Medicines** there is the drop-down **📖 What is it? Simple explanation (Wikipedia)**.

Write the name of a **test, an illness or a medicine** (for example *colour doppler ultrasound*, *duloxetine*): if there are several entries choose the right one and read **two lines of explanation**, in the app's language, with the button to open the full page.

It is **general information**, free: **it is not medical advice**. For your situation always ask your doctor or pharmacist.""",
               "what is it explanation wikipedia test illness medicine meaning word report"),
    "x_meteo": ("🌦️ Useful weather alerts", """Alerts **only when they are needed**, at the top of the sections:
- **Salute**: **strong heat** (drink often, do not go out from 11 to 17, take care of elderly people and children) and **intense cold**;
- **Car**: **frost** (ice on windscreen and roads), **heavy rain**, **wind gusts**;
- **Animals**: **heat** (walks early or in the evening, scorching asphalt, fresh water, never in the car) and **cold**.

**To turn them on:** **Utilities → 🌦️ Weather alerts** → write your town → choose the right one → **💾 Use this town**. There you also see the temperatures of the next days and you can **turn off** the alerts. Everyone chooses their own town.

Forecasts come from **Open-Meteo**: free, without keys or registration, for non-commercial use.""",
                "weather alerts heat cold frost rain wind town forecast open-meteo"),
    "x_voci_libere": ("✍️ A name of your choice in the lists with «Other»", """In the drop-down lists that have the item **Other** (document types, rooms, animal species, burials, doctors' roles, condominium categories, payment methods, «Who is this person to you», INPS documents…):
1. choose **Other**;
2. **✍️ Not in the list? Write the name you want** appears: write the exact name (for example **Ecocert**);
3. save as usual: **your name** is saved, not «Other».

In the cards with the confirm button at the bottom the box is always there, under the list, and counts only if you chose «Other». **The name stays in the list**: next time you find it there, before «Other».""",
                      "other name of your choice list drop-down write name custom item ecocert not in the list"),
    "x_lingua": ("🌐 The language of the app", """**You enter in the language you see on the login page.** If you want another language, choose it from the **🌐 Lingua / Language** menu before tapping **Enter**: it stays saved.

The phone remembers the **last language used**: next time the login page already opens in that language. Inside the app the language is changed from the **☰** menu at the top left.

All pages are in the chosen language: new sentences translate by themselves the first time a page opens (it takes about a minute), then they stay saved for everyone. **The assistant** also answers in the chosen language.""",
                 "language italian english spanish french german romanian arabic portuguese change language login translation"),
}, {
    "nv_diario": ("Diary of memories", "Utilities → 🎂 Birthdays → green ⏻ button in the card: photos, texts, icons, music"),
    "nv_ia": ("Documents read by AI", "Salute → Health documents → 🤖 Reclassify: it works even if you use other apps"),
    "nv_numeri": ("No. of the documents", "Salute → Health documents: No. 1 is the most recent; search by number"),
    "nv_meteo": ("Weather alerts", "Utilities → 🌦️ Weather alerts: choose your town"),
    "nv_wiki": ("What is it?", "Salute → Health documents and Medicines: simple explanation from Wikipedia"),
    "nv_altro": ("Names of your choice", "In the lists with «Other»: write the name you want"),
})


ga_traduci('en', {"l_festivita": ('📅 Holidays in the Hours check', "In **Work → 🧮 Hours check**, after loading the hours sheet and the payslip, there is **📅 Holidays**.\n\nThe app knows the **national holidays** by itself (also **Easter Monday**, which changes every year) and the **patron saint's day** of your town, which you choose once in **⛪ Patron saint's day and holidays of the year** (for Turin: Saint John, 24 June), then tap **💾 Remember the patron saint**.\n- **Red warning**: you worked on a holiday that in the sheet is **not marked as a holiday**. You see the days, the hours and an estimate of what you might lose (holiday work is paid 65%, normal overtime 20%). Mark «holiday» in the sheet and reload, or ask the payroll office.\n- **Yellow warning**: a day is marked as a holiday but is neither a holiday nor a Sunday: check it (a rule of your contract may apply).\n\nHolidays come from **Nager.Date** (free, no key); if it does not answer, the app calculates them.", 'holidays public holiday easter monday patron saint hours check payslip overtime')}, {})


ga_traduci('en', {"x_lettore": ('🤖 Re-read and re-catalogue documents with AI (all sections)', 'At the bottom of **My documents**, **Casa** (📚 Documents tab), **Work**, **Car** and **Animals** there is **🤖 Re-read and re-catalogue with AI** (in Salute there is «🤖 Reclassify documents with AI»).\n\n**How it reads:** in **two steps**: first it understands **what document it is**, then it reads the data with the **right form for that type** (for the identity card: number, issue, expiry; for a bill: period, amount, due date, POD/PDR…). Then it **checks** the data: tax code, identity card or passport number, number plate, chassis, IBAN, dates (expiry after issue, never the date of birth instead of another date). A value that fails the checks stays **🟠 to verify** and is not proposed.\n\n1. Open the drop-down: you see **«To check: X of Y»**. Tap **🔍 Read and catalogue**.\n2. The **live box** appears: you can use other apps, reading goes on; each document is saved as soon as it is read.\n3. The **🟡 Proposals to confirm** show what would change: leave ticked what is right and tap **✅ Apply**; **✖ Do not apply** leaves everything as it is.\n\n**New** documents too (photo of the identity card, bills, policies, vet documents) are read with the same method.', 're-read re-catalogue documents ai checks tax code number dates proposals apply')}, {})
