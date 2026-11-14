# -*- coding: utf-8 -*-
"""Le lingue del GIRO COMPLETO del robottino (assistente_giro.py): inglese, spagnolo, francese, tedesco, romeno, arabo, portoghese.
AG_TR[lingua][id capitolo] = (titolo, testo, dove si trova, parole per la ricerca).   AG_UI[lingua] = le scritte del pannello.
Il portoghese non è una lingua dell'app: qui ci sono TUTTE le scritte del robottino in portoghese (a_*, i_*), così il robottino parla e
risponde in portoghese anche se l'app resta in italiano. Caricato dopo assistente_giro.py; se manca, il giro resta in italiano."""

try:
    AG_TR
except NameError:
    AG_TR, AG_UI = {}, {}

# =====================================================================================================================
AG_TR["en"] = {
    "g_benvenuto": ("Welcome! I am your assistant",
        "Hello! I am the little robot of the app «La nostra dispensa» (Our pantry). I will now give you the complete tour: I explain every part of the app, one at a time, in simple words. "
        "If the voice is on I go ahead by myself: tap Pause to stop me, Next or Back to move, Chapters to jump wherever you want. "
        "You can ask me a question at any time, by writing it or with the microphone. With the globe button you change my language.",
        "", "welcome start complete tour robot assistant language pause next chapters"),
    "g_entrare": ("Entering the app",
        "Every member of the family has their own password. When you enter you only see your own things: your products, your medicines, your documents. "
        "Nobody else sees them, apart from what you choose to share. On the first screen you can choose the language of the app. "
        "At the top left there is an arrow with two tips: it opens the side menu, where you find your allergies, the language and other settings.",
        "First screen: type the password and tap Enter («Entra»).", "enter password language side menu arrow allergies access login"),
    "g_home": ("The Home and the section buttons",
        "At the top of every page there is a row of coloured buttons: Pantry («Dispensa»), Health («Salute»), My documents, Archive, Home («Casa»), Work («Lavoro»), Car («Auto»), Chat and Tools («Utilità»). "
        "Slide the row with your finger to see the last ones. Tap a button and you enter that part of the app. "
        "If a bell with a number appears on a button, there is something to look at there: a close deadline or a new message. "
        "Under the buttons you always find the red button «Clicca per informazioni» (Tap for information) with the guide.",
        "The row of coloured buttons at the top of every page.", "home buttons sections bar bell number alerts colours navigate"),
    "g_dispensa": ("The Pantry: products and expiry dates",
        "The Pantry is the list of what you have at home to eat and drink. Tap Add, take a photo of the product or type the barcode, and the app fills in the name. "
        "Then write how many pieces you have and the expiry date. The colours tell you when to act: green all fine, orange expires within two months, red within one month, dark already expired. "
        "There are three parts: Adults, Babies and Pets, so you know at once who each product is for.",
        "Green button 🏠 Dispensa → at the bottom the tabs Pantry, Add, Manage, Shopping.", "pantry products expiry add photo barcode colours green orange red babies pets"),
    "g_dispensa2": ("Allergies, shopping list and statistics",
        "In the side menu choose your allergies: the products dangerous for you show a siren, so you recognise them at once. "
        "When a product is finished, tap «I used it up» and it goes by itself into the Shopping list, which you can take to the supermarket. "
        "With Manage you change quantities and expiry dates of many products together. The Statistics show you how much you threw away, to waste less. "
        "There is also the Family pantry, for the things in common.",
        "🏠 Dispensa → tabs Shopping («Spesa») and Manage («Gestisci»); allergies in the side menu (arrow at the top left).", "allergies allergens siren shopping list used up manage statistics waste family"),
    "g_salute": ("Health: the people and the medicines",
        "In Health you keep the health of the whole family. First choose the person: you, your mother, the children. Each one has a profile with blood group and drug allergies. "
        "Then add the medicines with their expiry date: you can photograph the box. For each medicine you can read the leaflet in simple words. "
        "The app counts the stock: when a medicine is about to run out it tells you and prepares the prescription request for your doctor.",
        "Red button 🩺 Salute → choose the person at the top → tab Medicines («Medicinali»).", "health person profile mother medicines drugs expiry leaflet stock prescription doctor blood group"),
    "g_terapie": ("Therapies and reminders",
        "A therapy is a medicine to take regularly: every day at a certain time, or now and then, for example one vial every fifteen days. "
        "The app reminds you when to take it: with a message on Telegram, by email or on WhatsApp. "
        "You can also download the alarms to the phone's Calendar: so the alarm rings at the right time, even without opening the app. "
        "For each therapy write medicine, dose, time and how long it lasts.",
        "🩺 Salute → tab Therapies («Terapie») → ➕ New therapy; alarms in «📅 Allarmi sul Calendario del telefono».", "therapy therapies reminder alert time dose telegram email whatsapp calendar alarm every day intervals"),
    "g_visite": ("Visits, vaccines, doctor and health card",
        "In Health you also note visits and tests, with date and time: you can photograph the booking sheet and the app reads the date by itself. "
        "After the visit you keep the report. There are the vaccines with their boosters, your doctor's card and the health card, with the links to the online health record. "
        "With one tap you prepare a complete summary of a person, to show to the doctor or to send by email.",
        "🩺 Salute → tabs Visits («Visite») and Vaccines («Vaccini»); blue health-card badge next to the doctor.", "visits tests report booking vaccines boosters doctor health card record summary"),
    "g_documenti": ("My documents",
        "Here you keep your personal documents: identity card, driving licence, passport, health card, residence permit. "
        "Take a photo of the document: the app removes the background, straightens it and tries to read the type, the number and the expiry date. You can always correct by hand. "
        "Six months and three months before the expiry the app warns you, so you renew in time. The documents are yours only: nobody else sees them.",
        "Blue button 📁 I miei documenti → «Aggiungi un documento» (Add a document).", "documents identity card licence passport photo expiry renewal alert privacy"),
    "g_archivio": ("The Archive: all the files in one place",
        "The Archive gathers all the files you saved in the app: photos of documents, leaflets, reports, manuals, bills. "
        "You search them by typing a word, filter them by type or by person, open them, download them or send them by email and WhatsApp. "
        "If a detail is wrong you correct it, and you can replace the file with a better one. It is like a big tidy binder, always in your pocket.",
        "Purple button 🗂️ Archivio → search box at the top.", "archive files search filter open download send correct binder"),
    "g_casa": ("Home: appliances, manuals and warranties",
        "In Home you keep the appliances of the house: washing machine, fridge, boiler, television. For each one you save the manual, the warranty, the receipt and the bills. "
        "If the appliance has a problem, you search a word inside the manual, for example the error code or «filter cleaning»: the app shows you the right pages with the words highlighted. "
        "If you want, it explains them in simple words. You can also send documents from your email or from the suppliers' apps.",
        "Orange button 🏡 Casa → tabs Beni (items) and Documenti → on the document «🔎 Cerca nel manuale».", "home items appliances manual warranty bill receipt search in the manual error explain"),
    "g_casa2": ("Maintenance and Administration of the home",
        "In Home you also record maintenance, such as the boiler service, and the app reminds you of the next one. "
        "In the Administration tab you keep the condominium expenses and the instalments with the payment dates, the contacts of plumber, electrician and administrator, "
        "and the calendar of waste sorting with the bulky-waste collection. You can send the whole Administration to another user with a password-protected file.",
        "🏡 Casa → tabs Manutenzioni and Amministrazione.", "maintenance boiler administration condominium expenses instalments payments contacts plumber electrician waste sorting bulky exchange"),
    "g_lavoro": ("Work: payslips and documents",
        "In Work you upload your payslips, even by photographing them: the app reads the figures and puts them in order. "
        "Year by year you see the charts and the comparison between the months. You keep the yearly tax certificate (CU) and the INPS documents. "
        "There is also the address book of the union, the CAF and the patronato, with phone and opening hours, so you find them at once when needed.",
        "Grey button 💼 Lavoro → tabs Buste paga, Anno per anno, CU, INPS, Sindacato.", "work payslip salary charts year tax certificate cu inps union caf patronato"),
    "g_auto": ("Car: the garage and the deadlines",
        "In Car there is your garage: every vehicle has its card. You can photograph the registration document and the app reads plate, make and model. "
        "It reminds you of road tax, insurance and inspection before they expire. You record maintenance, refuelling and expenses, so you know how much the car costs you. "
        "There are also the driving licence with the points and the fines, and the trips with the mileage refunds.",
        "Light-blue button 🚗 Auto → the garage → tap a vehicle → Scadenze, Manutenzione, Rifornimenti.", "car vehicle garage plate registration road tax insurance inspection maintenance refuelling expenses licence fines trips"),
    "g_auto2": ("Car: warning lights, diagnostics and emergency",
        "If a warning light comes on on the dashboard, photograph it: the app tells you what it means and whether you can keep driving. "
        "In Diagnostics you find the error codes and, with a small device to plug into the car, the engine data too. "
        "In Emergency you have the useful numbers, the roadside assistance and the accident form, with the steps to follow calmly if you have an accident.",
        "🚗 Auto → Diagnostica → «📷 Fotografa una spia»; 🚗 Auto → Emergenza.", "warning light dashboard diagnostics error codes obd emergency roadside assistance accident form"),
    "g_chat": ("The family Chat",
        "With the Chat you write to the members of the family without leaving the app, for free. At the top choose who to talk to: Everyone («Tutti»), that is the family group, or one person only, in private. "
        "Choose who to keep in view as a button; the other people stay in the menu «Altre persone» (Other people). "
        "Your messages are on the right in green, the others' on the left in white. A red dot with a number tells you how many new messages you have.",
        "Button 💬 Chat at the top → choose the person → write at the bottom → 📨 Invia (Send).", "chat messages family write everyone private people in view other people new messages"),
    "g_utilita": ("The Tools",
        "In Tools there are the service instruments. The Bin, where deleted things stay for thirty days. The Appearance of the app, to have larger texts. "
        "Data exchange, to send your data to another person or receive them. Free up space, to remove useless files from the phone. "
        "And the useful apps, such as Wimbi and Velocity Music, with their leaflet explaining what they do.",
        "Purple button 🧰 Utilità, the last one in the row at the top.", "tools bin appearance large text data exchange free space wimbi velocity useful apps"),
    "g_avvisi": ("How the alerts arrive",
        "The app warns you before deadlines and at therapy time. The alerts arrive on Telegram, by email, on WhatsApp or as an alarm on the phone's Calendar: you choose which. "
        "Telegram and email are free and safe; you just set them up once. Inside Health there is the button to send a test message, so you check that everything works. "
        "In the app, the bell with the number on the top buttons shows you the things to see.",
        "🩺 Salute → drop-down «🔔 Avvisi» → choose the channels and tap «Messaggio di prova» (test message).", "alerts notifications reminders telegram email whatsapp calendar bell test message set up"),
    "g_cestino": ("I made a mistake: the Bin",
        "Don't be afraid of making mistakes. When you delete something, the Undo button appears for a few seconds at the top of the page: tap it and everything goes back as before. "
        "If you notice later, open the Bin in Tools: deleted things stay there for thirty days and with Restore they go back to their place. "
        "Only you can decide to delete them forever.",
        "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina (Restore).", "mistake error deleted by mistake undo bin restore recover thirty days"),
    "g_aiuto": ("Help always at hand",
        "If you don't remember how to do something, you have three helps. The red button «Clicca per informazioni» at the top, with the guide of every page and a search box. "
        "Me, the little robot: tap me and I explain the page you are on, or write or tell me a question with the microphone. "
        "And What's new, where I tell you what is new. You can make my voice slower or faster, change language, or switch me off: you switch me on again from the red button.",
        "The little robot at the bottom right; the red button at the top of every page.", "help guide information question microphone voice slow fast news switch off assistant"),
    "g_fine": ("End of the tour",
        "The tour is over, well done! Now you know all the parts of the app. You don't have to remember everything: whenever you need, tap me and ask me. "
        "Start with the things you use most, for example the Pantry or the family's medicines, and discover the rest calmly. Enjoy!",
        "", "end tour finished thanks start again"),
}
AG_UI["en"] = {
    "a_giro": "🧭 Complete tour of the app", "a_giro_dlg": "🧭 Give me the complete tour of the app (the robot tells it aloud)",
    "a_capitoli": "📑 Chapters", "a_pausa": "⏸ Pause", "a_riprendi": "▶ Resume", "a_dove": "Where it is:",
    "a_lingua": "🌐 Language", "a_lingua_t": "Which language do you want me to speak?", "a_lingua_x": "Choose below. The app language does not change: my voice, the tour and the answers do.",
    "a_lingua_ok": "Perfect, from now on I speak English.", "a_cap_t": "The chapters of the tour", "a_cap_x": "Tap a chapter to go straight there.",
    "a_primo_t": "Hello! It is the first time you open me", "a_primo_x": "Would you like the complete tour of the app? It takes a few minutes and you can stop me whenever you want. Tap the yellow button below, or «Give me the tour».",
    "a_primo_btn": "🧭 Give me the tour", "a_fine_t": "End of the tour", "a_fine_x": "Done! If you need anything else, ask me.",
    "a_vel": "🐢 Voice speed", "a_vel_0": "slow", "a_vel_1": "normal", "a_vel_2": "fast", "a_vel_prova": "This is my voice at the new speed.",
    "a_trov_t": "I can't find instructions about this", "a_trov_x": "I don't want to suggest a procedure that might not work: maybe this feature does not exist in the app, or I use different words from yours. Try other words (even just one: photo, expiry, password) or choose a topic below.",
}

# =====================================================================================================================
AG_TR["es"] = {
    "g_benvenuto": ("¡Bienvenido! Soy tu asistente",
        "¡Hola! Soy el robotito de la app «La nostra dispensa» (Nuestra despensa). Ahora te hago el recorrido completo: te explico todas las partes de la app, una por una, con palabras sencillas. "
        "Si la voz está encendida sigo yo solo: toca Pausa para pararme, Adelante o Atrás para moverte, Capítulos para saltar adonde quieras. "
        "Puedes hacerme una pregunta cuando quieras, escribiéndola o con el micrófono. Con el botón del mundo cambias mi idioma.",
        "", "bienvenido inicio recorrido completo robot asistente idioma pausa adelante capítulos"),
    "g_entrare": ("Entrar en la app",
        "Cada persona de la familia tiene su contraseña. Cuando entras ves solo tus cosas: tus productos, tus medicinas, tus documentos. "
        "Nadie más los ve, salvo lo que decidas compartir. En la primera pantalla puedes elegir el idioma de la app. "
        "Arriba a la izquierda hay una flecha con dos puntas: abre el menú lateral, donde encuentras tus alergias, el idioma y otros ajustes.",
        "Primera pantalla: escribe la contraseña y toca Entrar («Entra»).", "entrar contraseña idioma menú lateral flecha alergias acceso"),
    "g_home": ("La página inicial y los botones de las secciones",
        "Arriba, en cada página, hay una fila de botones de colores: Despensa («Dispensa»), Salud («Salute»), Mis documentos, Archivo, Casa, Trabajo («Lavoro»), Coche («Auto»), Chat y Utilidades («Utilità»). "
        "Desliza la fila con el dedo para ver los últimos. Tocas un botón y entras en esa parte de la app. "
        "Si en un botón aparece una campanita con un número, allí hay algo que mirar: un vencimiento cercano o un mensaje nuevo. "
        "Debajo de los botones encuentras siempre el botón rojo «Clicca per informazioni» (Toca para información) con la guía.",
        "La fila de botones de colores arriba, en cada página.", "inicio botones secciones barra campana número avisos colores navegar"),
    "g_dispensa": ("La Despensa: productos y caducidades",
        "La Despensa es la lista de lo que tienes en casa para comer y beber. Toca Añadir, haz la foto del producto o escribe el código de barras, y la app rellena el nombre. "
        "Luego escribe cuántas unidades tienes y la fecha de caducidad. Los colores te dicen cuándo actuar: verde todo bien, naranja caduca en dos meses, rojo en un mes, oscuro ya caducado. "
        "Hay tres partes: Adultos, Bebés y Animales, para saber enseguida para quién es cada producto.",
        "Botón verde 🏠 Dispensa → abajo las pestañas Despensa, Añadir, Gestionar, Compra.", "despensa productos caducidad añadir foto código de barras colores verde naranja rojo bebés animales"),
    "g_dispensa2": ("Alergias, lista de la compra y estadísticas",
        "En el menú lateral elige tus alergias: los productos peligrosos para ti muestran una sirena, así los reconoces enseguida. "
        "Cuando un producto se acaba, toca «Lo he consumido» y va solo a la Lista de la compra, que puedes llevar al supermercado. "
        "Con Gestionar cambias cantidades y caducidades de muchos productos a la vez. Las Estadísticas te muestran cuánto has tirado, para desperdiciar menos. "
        "También está la Despensa de familia, para las cosas en común.",
        "🏠 Dispensa → pestañas Compra («Spesa») y Gestionar («Gestisci»); alergias en el menú lateral (flecha arriba a la izquierda).", "alergias alérgenos sirena lista compra consumido gestionar estadísticas desperdicio familia"),
    "g_salute": ("Salud: las personas y las medicinas",
        "En Salud llevas la salud de toda la familia. Primero elige la persona: tú, mamá, los hijos. Cada uno tiene su perfil con grupo sanguíneo y alergias a medicamentos. "
        "Luego añade las medicinas con su caducidad: puedes fotografiar la caja. De cada medicina puedes leer el prospecto con palabras sencillas. "
        "La app cuenta las existencias: cuando una medicina está por acabarse te lo dice y te prepara la solicitud de receta para la doctora.",
        "Botón rojo 🩺 Salute → elige la persona arriba → pestaña Medicinas («Medicinali»).", "salud persona perfil mamá medicinas fármacos caducidad prospecto existencias receta doctora grupo sanguíneo"),
    "g_terapie": ("Tratamientos y recordatorios",
        "Un tratamiento es una medicina que se toma con regularidad: todos los días a cierta hora, o de vez en cuando, por ejemplo una ampolla cada quince días. "
        "La app te recuerda cuándo tomarla: con un mensaje en Telegram, por correo o en WhatsApp. "
        "También puedes descargar las alarmas en el Calendario del teléfono: así suena la alarma a la hora justa, incluso sin abrir la app. "
        "Para cada tratamiento escribe medicina, dosis, hora y cuánto dura.",
        "🩺 Salute → pestaña Tratamientos («Terapie») → ➕ Nuevo tratamiento; alarmas en «📅 Allarmi sul Calendario del telefono».", "tratamiento terapia recordatorio aviso hora dosis telegram correo whatsapp calendario alarma cada día intervalos"),
    "g_visite": ("Citas, vacunas, médico y tarjeta sanitaria",
        "En Salud apuntas también las citas y las pruebas, con fecha y hora: puedes fotografiar la hoja de la cita y la app lee la fecha sola. "
        "Después de la cita guardas el informe. Están las vacunas con sus refuerzos, la ficha de tu médico y la tarjeta sanitaria, con los enlaces al historial sanitario. "
        "Con un toque preparas un resumen completo de una persona, para enseñar al médico o enviar por correo.",
        "🩺 Salute → pestañas Citas («Visite») y Vacunas («Vaccini»); distintivo azul de la tarjeta sanitaria junto a la doctora.", "citas pruebas informe reserva vacunas refuerzos médico tarjeta sanitaria historial resumen"),
    "g_documenti": ("Mis documentos",
        "Aquí guardas los documentos personales: documento de identidad, carné de conducir, pasaporte, tarjeta sanitaria, permiso de residencia. "
        "Haz la foto al documento: la app quita el fondo, lo endereza e intenta leer el tipo, el número y la caducidad. Siempre puedes corregir a mano. "
        "Seis meses y tres meses antes de la caducidad la app te avisa, así renuevas a tiempo. Los documentos son solo tuyos: nadie más los ve.",
        "Botón azul 📁 I miei documenti → «Aggiungi un documento» (Añadir un documento).", "documentos identidad carné pasaporte foto caducidad renovar aviso privacidad"),
    "g_archivio": ("El Archivo: todos los archivos en un sitio",
        "El Archivo reúne todos los archivos que has guardado en la app: fotos de documentos, prospectos, informes, manuales, facturas. "
        "Los buscas escribiendo una palabra, los filtras por tipo o por persona, los abres, los descargas o los envías por correo y WhatsApp. "
        "Si un dato está mal lo corriges, y puedes sustituir el archivo por uno mejor. Es como una gran carpeta ordenada, siempre en el bolsillo.",
        "Botón morado 🗂️ Archivio → casilla de búsqueda arriba.", "archivo archivos buscar filtrar abrir descargar enviar corregir carpeta"),
    "g_casa": ("Casa: aparatos, manuales y garantías",
        "En Casa llevas los aparatos de la casa: lavadora, frigorífico, caldera, televisor. De cada uno guardas el manual, la garantía, el tique y las facturas. "
        "Si el aparato da un problema, buscas una palabra dentro del manual, por ejemplo el código del error o «limpieza del filtro»: la app te muestra las páginas correctas con las palabras resaltadas. "
        "Si quieres, te las explica con palabras sencillas. También puedes mandar documentos desde el correo o desde las apps de los proveedores.",
        "Botón naranja 🏡 Casa → pestañas Beni (bienes) y Documenti → en el documento «🔎 Cerca nel manuale».", "casa bienes aparatos electrodomésticos manual garantía factura tique buscar en el manual error explícame"),
    "g_casa2": ("Mantenimientos y Administración de la casa",
        "En Casa registras también los mantenimientos, como la revisión de la caldera, y la app te recuerda el siguiente. "
        "En la pestaña Administración llevas los gastos de comunidad y las cuotas con las fechas de pago, los contactos del fontanero, el electricista y el administrador, "
        "y el calendario de la recogida selectiva con la retirada de enseres. Puedes mandar toda la Administración a otro usuario con un archivo protegido con contraseña.",
        "🏡 Casa → pestañas Manutenzioni y Amministrazione.", "mantenimiento caldera administración comunidad gastos cuotas pagos contactos fontanero electricista recogida selectiva enseres intercambio"),
    "g_lavoro": ("Trabajo: nóminas y documentos",
        "En Trabajo cargas las nóminas, incluso fotografiándolas: la app lee las cifras y las pone en orden. "
        "Año por año ves los gráficos y la comparación entre los meses. Guardas el certificado anual de retenciones (CU) y los documentos del INPS. "
        "También está la agenda del sindicato, del CAF y del patronato, con teléfono y horarios, así los encuentras enseguida cuando hacen falta.",
        "Botón gris 💼 Lavoro → pestañas Buste paga, Anno per anno, CU, INPS, Sindacato.", "trabajo nómina sueldo gráficos año certificado cu inps sindicato caf patronato"),
    "g_auto": ("Coche: el garaje y los vencimientos",
        "En Coche está tu garaje: cada vehículo tiene su ficha. Puedes fotografiar el permiso de circulación y la app lee matrícula, marca y modelo. "
        "Te recuerda el impuesto, el seguro y la inspección antes de que venzan. Registras mantenimientos, repostajes y gastos, así sabes cuánto te cuesta el coche. "
        "También están el carné con los puntos y las multas, y los viajes con los reembolsos por kilómetro.",
        "Botón celeste 🚗 Auto → el garaje → toca un vehículo → Scadenze, Manutenzione, Rifornimenti.", "coche vehículo garaje matrícula permiso circulación impuesto seguro inspección itv mantenimiento repostaje gastos carné multas viajes"),
    "g_auto2": ("Coche: testigos, diagnóstico y emergencia",
        "Si en el salpicadero se enciende un testigo, fotografíalo: la app te dice qué significa y si puedes seguir conduciendo. "
        "En Diagnóstico encuentras los códigos de error y, con un pequeño aparato que se conecta al coche, también los datos del motor. "
        "En Emergencia tienes los números útiles, la asistencia en carretera y el parte de accidente, con los pasos a seguir con calma si tienes un accidente.",
        "🚗 Auto → Diagnostica → «📷 Fotografa una spia»; 🚗 Auto → Emergenza.", "testigo salpicadero diagnóstico códigos error obd emergencia asistencia carretera accidente parte"),
    "g_chat": ("El Chat de la familia",
        "Con el Chat escribes a las personas de la familia sin salir de la app, gratis. Arriba eliges con quién hablar: Todos («Tutti»), es decir el grupo de la familia, o una sola persona, en privado. "
        "Eliges a quién tener a la vista como botón; las demás personas están en el menú «Altre persone» (Otras personas). "
        "Tus mensajes están a la derecha en verde, los de los demás a la izquierda en blanco. Un punto rojo con el número te dice cuántos mensajes nuevos tienes.",
        "Botón 💬 Chat arriba → elige la persona → escribe abajo → 📨 Invia (Enviar).", "chat mensajes familia escribir todos privado personas a la vista otras personas mensajes nuevos"),
    "g_utilita": ("Las Utilidades",
        "En Utilidades están las herramientas de servicio. La Papelera, donde las cosas eliminadas se quedan treinta días. El Aspecto de la app, para tener textos más grandes. "
        "El Intercambio de datos, para mandar tus datos a otra persona o recibirlos. Liberar espacio, para quitar los archivos inútiles del teléfono. "
        "Y las apps útiles, como Wimbi y Velocity Music, con su prospecto que explica qué hacen.",
        "Botón morado 🧰 Utilità, el último de la fila de arriba.", "utilidades papelera aspecto textos grandes intercambio datos liberar espacio wimbi velocity apps útiles"),
    "g_avvisi": ("Cómo llegan los avisos",
        "La app te avisa antes de los vencimientos y a la hora de los tratamientos. Los avisos llegan por Telegram, por correo, por WhatsApp o como alarma en el Calendario del teléfono: eliges tú cuáles. "
        "Telegram y el correo son gratuitos y seguros; basta configurarlos una vez. Dentro de Salud está el botón para mandar un mensaje de prueba, así compruebas que todo funciona. "
        "En la app, la campanita con el número en los botones de arriba te muestra las cosas por ver.",
        "🩺 Salute → desplegable «🔔 Avvisi» → elige los canales y toca «Messaggio di prova» (mensaje de prueba).", "avisos notificaciones recordatorios telegram correo whatsapp calendario campana mensaje de prueba configurar"),
    "g_cestino": ("Me he equivocado: la Papelera",
        "No tengas miedo de equivocarte. Cuando eliminas algo, arriba de la página aparece unos segundos el botón Deshacer: tócalo y todo vuelve a como estaba. "
        "Si te das cuenta después, abre la Papelera en Utilidades: las cosas eliminadas se quedan allí treinta días y con Restaurar vuelven a su sitio. "
        "Solo tú puedes decidir eliminarlas para siempre.",
        "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina (Restaurar).", "equivocado error eliminado por error deshacer papelera restaurar recuperar treinta días"),
    "g_aiuto": ("Ayuda siempre a mano",
        "Si no recuerdas cómo se hace algo, tienes tres ayudas. El botón rojo «Clicca per informazioni» arriba, con la guía de cada página y una casilla para buscar. "
        "Yo, el robotito: tócame y te explico la página en la que estás, o escríbeme o dime una pregunta con el micrófono. "
        "Y las Novedades, donde te cuento qué hay de nuevo. Puedes hacer mi voz más lenta o más rápida, cambiar de idioma o apagarme: me vuelves a encender desde el botón rojo.",
        "El robotito abajo a la derecha; el botón rojo arriba en cada página.", "ayuda guía información pregunta micrófono voz lenta rápida novedades apagar asistente"),
    "g_fine": ("Fin del recorrido",
        "¡El recorrido ha terminado, muy bien! Ahora conoces todas las partes de la app. No tienes que recordarlo todo: cada vez que lo necesites, tócame y pregúntame. "
        "Empieza por las cosas que más usas, por ejemplo la Despensa o las medicinas de la familia, y descubre el resto con calma. ¡Buen trabajo!",
        "", "fin recorrido terminado gracias empezar de nuevo"),
}
AG_UI["es"] = {
    "a_giro": "🧭 Recorrido completo de la app", "a_giro_dlg": "🧭 Hazme el recorrido completo de la app (el robotito lo cuenta en voz alta)",
    "a_capitoli": "📑 Capítulos", "a_pausa": "⏸ Pausa", "a_riprendi": "▶ Continuar", "a_dove": "Dónde está:",
    "a_lingua": "🌐 Idioma", "a_lingua_t": "¿En qué idioma quieres que hable?", "a_lingua_x": "Elige aquí abajo. El idioma de la app no cambia: cambian mi voz, el recorrido y las respuestas.",
    "a_lingua_ok": "Perfecto, desde ahora hablo español.", "a_cap_t": "Los capítulos del recorrido", "a_cap_x": "Toca un capítulo para ir directamente allí.",
    "a_primo_t": "¡Hola! Es la primera vez que me abres", "a_primo_x": "¿Quieres que te haga el recorrido completo de la app? Dura pocos minutos y puedes pararme cuando quieras. Toca el botón amarillo aquí abajo, o «Hazme el recorrido».",
    "a_primo_btn": "🧭 Hazme el recorrido", "a_fine_t": "Fin del recorrido", "a_fine_x": "¡Listo! Si necesitas algo más, pregúntame.",
    "a_vel": "🐢 Velocidad de la voz", "a_vel_0": "lenta", "a_vel_1": "normal", "a_vel_2": "rápida", "a_vel_prova": "Esta es mi voz con la nueva velocidad.",
    "a_trov_t": "No encuentro instrucciones sobre esto", "a_trov_x": "No quiero indicarte un procedimiento que podría no funcionar: quizá esta función no existe en la app, o uso palabras distintas de las tuyas. Prueba con otras palabras (incluso una sola: foto, caducidad, contraseña) o elige un tema aquí abajo.",
}

# =====================================================================================================================
AG_TR["fr"] = {
    "g_benvenuto": ("Bienvenue ! Je suis ton assistant",
        "Bonjour ! Je suis le petit robot de l'appli « La nostra dispensa » (Notre garde-manger). Je te fais maintenant la visite complète : je t'explique toutes les parties de l'appli, une à la fois, avec des mots simples. "
        "Si la voix est allumée, j'avance tout seul : touche Pause pour m'arrêter, Suivant ou Retour pour te déplacer, Chapitres pour sauter où tu veux. "
        "Tu peux me poser une question quand tu veux, en l'écrivant ou avec le micro. Avec le bouton du globe, tu changes ma langue.",
        "", "bienvenue début visite complète robot assistant langue pause suivant chapitres"),
    "g_entrare": ("Entrer dans l'appli",
        "Chaque personne de la famille a son mot de passe. Quand tu entres, tu vois seulement tes affaires : tes produits, tes médicaments, tes documents. "
        "Personne d'autre ne les voit, sauf ce que tu choisis de partager. Sur le premier écran, tu peux choisir la langue de l'appli. "
        "En haut à gauche il y a une flèche à deux pointes : elle ouvre le menu latéral, où tu trouves tes allergies, la langue et d'autres réglages.",
        "Premier écran : écris le mot de passe et touche Entrer (« Entra »).", "entrer mot de passe langue menu latéral flèche allergies accès connexion"),
    "g_home": ("L'accueil et les boutons des sections",
        "En haut de chaque page, il y a une rangée de boutons colorés : Garde-manger (« Dispensa »), Santé (« Salute »), Mes documents, Archives, Maison (« Casa »), Travail (« Lavoro »), Voiture (« Auto »), Chat et Outils (« Utilità »). "
        "Fais glisser la rangée avec le doigt pour voir les derniers. Tu touches un bouton et tu entres dans cette partie de l'appli. "
        "Si une cloche avec un nombre apparaît sur un bouton, il y a quelque chose à regarder là : une échéance proche ou un nouveau message. "
        "Sous les boutons, tu trouves toujours le bouton rouge « Clicca per informazioni » (Touche pour les informations) avec le guide.",
        "La rangée de boutons colorés en haut de chaque page.", "accueil boutons sections barre cloche nombre alertes couleurs naviguer"),
    "g_dispensa": ("Le Garde-manger : produits et dates de péremption",
        "Le Garde-manger est la liste de ce que tu as à la maison à manger et à boire. Touche Ajouter, prends la photo du produit ou écris le code-barres, et l'appli remplit le nom. "
        "Puis écris combien de pièces tu as et la date de péremption. Les couleurs te disent quand agir : vert tout va bien, orange périme dans deux mois, rouge dans un mois, foncé déjà périmé. "
        "Il y a trois parties : Adultes, Bébés et Animaux, pour savoir tout de suite à qui est chaque produit.",
        "Bouton vert 🏠 Dispensa → en bas les onglets Garde-manger, Ajouter, Gérer, Courses.", "garde-manger produits péremption ajouter photo code-barres couleurs vert orange rouge bébés animaux"),
    "g_dispensa2": ("Allergies, liste de courses et statistiques",
        "Dans le menu latéral, choisis tes allergies : les produits dangereux pour toi montrent une sirène, ainsi tu les reconnais tout de suite. "
        "Quand un produit est fini, touche « Je l'ai consommé » et il va tout seul dans la Liste de courses, que tu peux emporter au supermarché. "
        "Avec Gérer, tu changes quantités et dates de beaucoup de produits ensemble. Les Statistiques te montrent combien tu as jeté, pour moins gaspiller. "
        "Il y a aussi le Garde-manger de famille, pour les choses en commun.",
        "🏠 Dispensa → onglets Courses (« Spesa ») et Gérer (« Gestisci ») ; allergies dans le menu latéral (flèche en haut à gauche).", "allergies allergènes sirène liste courses consommé gérer statistiques gaspillage famille"),
    "g_salute": ("Santé : les personnes et les médicaments",
        "Dans Santé, tu suis la santé de toute la famille. D'abord choisis la personne : toi, maman, les enfants. Chacun a son profil avec groupe sanguin et allergies aux médicaments. "
        "Puis ajoute les médicaments avec leur date de péremption : tu peux photographier la boîte. Pour chaque médicament, tu peux lire la notice en mots simples. "
        "L'appli compte les stocks : quand un médicament va manquer, elle te le dit et te prépare la demande d'ordonnance pour le médecin.",
        "Bouton rouge 🩺 Salute → choisis la personne en haut → onglet Médicaments (« Medicinali »).", "santé personne profil maman médicaments péremption notice stock ordonnance médecin groupe sanguin"),
    "g_terapie": ("Traitements et rappels",
        "Un traitement est un médicament à prendre régulièrement : tous les jours à une certaine heure, ou de temps en temps, par exemple une ampoule tous les quinze jours. "
        "L'appli te rappelle quand le prendre : avec un message sur Telegram, par e-mail ou sur WhatsApp. "
        "Tu peux aussi télécharger les alarmes dans le Calendrier du téléphone : ainsi l'alarme sonne à la bonne heure, même sans ouvrir l'appli. "
        "Pour chaque traitement, écris médicament, dose, horaire et durée.",
        "🩺 Salute → onglet Traitements (« Terapie ») → ➕ Nouveau traitement ; alarmes dans « 📅 Allarmi sul Calendario del telefono ».", "traitement rappel alerte horaire dose telegram e-mail whatsapp calendrier alarme chaque jour intervalles"),
    "g_visite": ("Rendez-vous, vaccins, médecin et carte de santé",
        "Dans Santé, tu notes aussi les rendez-vous et les examens, avec date et heure : tu peux photographier la feuille de réservation et l'appli lit la date toute seule. "
        "Après le rendez-vous, tu gardes le compte rendu. Il y a les vaccins avec les rappels, la fiche de ton médecin et la carte de santé, avec les liens vers le dossier médical. "
        "D'une touche, tu prépares un résumé complet d'une personne, à montrer au médecin ou à envoyer par e-mail.",
        "🩺 Salute → onglets Rendez-vous (« Visite ») et Vaccins (« Vaccini ») ; badge bleu de la carte de santé à côté du médecin.", "rendez-vous examens compte rendu réservation vaccins rappels médecin carte de santé dossier résumé"),
    "g_documenti": ("Mes documents",
        "Ici tu gardes les documents personnels : carte d'identité, permis de conduire, passeport, carte de santé, titre de séjour. "
        "Prends la photo du document : l'appli enlève le fond, le redresse et essaie de lire le type, le numéro et la date d'expiration. Tu peux toujours corriger à la main. "
        "Six mois et trois mois avant l'expiration, l'appli te prévient, pour renouveler à temps. Les documents sont à toi seul : personne d'autre ne les voit.",
        "Bouton bleu 📁 I miei documenti → « Aggiungi un documento » (Ajouter un document).", "documents carte identité permis passeport photo expiration renouvellement alerte confidentialité"),
    "g_archivio": ("Les Archives : tous les fichiers au même endroit",
        "Les Archives rassemblent tous les fichiers enregistrés dans l'appli : photos de documents, notices, comptes rendus, manuels, factures. "
        "Tu les cherches en écrivant un mot, tu les filtres par type ou par personne, tu les ouvres, les télécharges ou les envoies par e-mail et WhatsApp. "
        "Si une donnée est fausse, tu la corriges, et tu peux remplacer le fichier par un meilleur. C'est comme un grand classeur bien rangé, toujours dans la poche.",
        "Bouton violet 🗂️ Archivio → case de recherche en haut.", "archives fichiers chercher filtrer ouvrir télécharger envoyer corriger classeur"),
    "g_casa": ("Maison : appareils, manuels et garanties",
        "Dans Maison, tu gardes les appareils de la maison : lave-linge, frigo, chaudière, télévision. Pour chacun, tu enregistres le manuel, la garantie, le ticket et les factures. "
        "Si l'appareil a un problème, tu cherches un mot dans le manuel, par exemple le code d'erreur ou « nettoyage du filtre » : l'appli te montre les bonnes pages avec les mots surlignés. "
        "Si tu veux, elle te les explique en mots simples. Tu peux aussi envoyer des documents depuis le courrier ou les applis des fournisseurs.",
        "Bouton orange 🏡 Casa → onglets Beni (biens) et Documenti → sur le document « 🔎 Cerca nel manuale ».", "maison biens appareils électroménager manuel garantie facture ticket chercher dans le manuel erreur explique-moi"),
    "g_casa2": ("Entretien et Administration de la maison",
        "Dans Maison, tu enregistres aussi les entretiens, comme la révision de la chaudière, et l'appli te rappelle le prochain. "
        "Dans l'onglet Administration, tu suis les charges de copropriété et les échéances avec les dates de paiement, les contacts du plombier, de l'électricien et du syndic, "
        "et le calendrier du tri des déchets avec le ramassage des encombrants. Tu peux envoyer toute l'Administration à un autre utilisateur avec un fichier protégé par mot de passe.",
        "🏡 Casa → onglets Manutenzioni et Amministrazione.", "entretien chaudière administration copropriété charges échéances paiements contacts plombier électricien tri déchets encombrants échange"),
    "g_lavoro": ("Travail : fiches de paie et documents",
        "Dans Travail, tu charges les fiches de paie, même en les photographiant : l'appli lit les chiffres et les met en ordre. "
        "Année par année, tu vois les graphiques et la comparaison entre les mois. Tu gardes l'attestation fiscale annuelle (CU) et les documents de l'INPS. "
        "Il y a aussi le carnet d'adresses du syndicat, du CAF et du patronato, avec téléphone et horaires, pour les trouver tout de suite quand il faut.",
        "Bouton gris 💼 Lavoro → onglets Buste paga, Anno per anno, CU, INPS, Sindacato.", "travail fiche de paie salaire graphiques année attestation cu inps syndicat caf patronato"),
    "g_auto": ("Voiture : le garage et les échéances",
        "Dans Voiture, il y a ton garage : chaque véhicule a sa fiche. Tu peux photographier la carte grise et l'appli lit plaque, marque et modèle. "
        "Elle te rappelle la taxe, l'assurance et le contrôle technique avant leur échéance. Tu enregistres les entretiens, les pleins et les dépenses, pour savoir combien te coûte la voiture. "
        "Il y a aussi le permis avec les points et les amendes, et les trajets avec les remboursements kilométriques.",
        "Bouton bleu clair 🚗 Auto → le garage → touche un véhicule → Scadenze, Manutenzione, Rifornimenti.", "voiture véhicule garage plaque carte grise taxe assurance contrôle technique entretien plein dépenses permis amendes trajets"),
    "g_auto2": ("Voiture : voyants, diagnostic et urgence",
        "Si un voyant s'allume sur le tableau de bord, photographie-le : l'appli te dit ce qu'il signifie et si tu peux continuer à rouler. "
        "Dans Diagnostic, tu trouves les codes d'erreur et, avec un petit appareil à brancher sur la voiture, aussi les données du moteur. "
        "Dans Urgence, tu as les numéros utiles, le dépannage et le constat d'accident, avec les étapes à suivre calmement en cas d'accident.",
        "🚗 Auto → Diagnostica → « 📷 Fotografa una spia » ; 🚗 Auto → Emergenza.", "voyant tableau de bord diagnostic codes erreur obd urgence dépannage accident constat"),
    "g_chat": ("Le Chat de la famille",
        "Avec le Chat, tu écris aux personnes de la famille sans quitter l'appli, gratuitement. En haut, choisis avec qui parler : Tous (« Tutti »), c'est-à-dire le groupe de la famille, ou une seule personne, en privé. "
        "Choisis qui garder en vue comme bouton ; les autres personnes restent dans le menu « Altre persone » (Autres personnes). "
        "Tes messages sont à droite en vert, ceux des autres à gauche en blanc. Un point rouge avec le nombre te dit combien de nouveaux messages tu as.",
        "Bouton 💬 Chat en haut → choisis la personne → écris en bas → 📨 Invia (Envoyer).", "chat messages famille écrire tous privé personnes en vue autres personnes nouveaux messages"),
    "g_utilita": ("Les Outils",
        "Dans Outils, il y a les instruments de service. La Corbeille, où les choses supprimées restent trente jours. L'Apparence de l'appli, pour avoir des textes plus grands. "
        "L'Échange de données, pour envoyer tes données à une autre personne ou les recevoir. Libérer de l'espace, pour enlever les fichiers inutiles du téléphone. "
        "Et les applis utiles, comme Wimbi et Velocity Music, avec leur notice qui explique ce qu'elles font.",
        "Bouton violet 🧰 Utilità, le dernier de la rangée en haut.", "outils corbeille apparence textes grands échange données libérer espace wimbi velocity applis utiles"),
    "g_avvisi": ("Comment arrivent les alertes",
        "L'appli te prévient avant les échéances et à l'heure des traitements. Les alertes arrivent sur Telegram, par e-mail, sur WhatsApp ou comme alarme dans le Calendrier du téléphone : tu choisis lesquelles. "
        "Telegram et l'e-mail sont gratuits et sûrs ; il suffit de les régler une fois. Dans Santé, il y a le bouton pour envoyer un message d'essai, pour vérifier que tout fonctionne. "
        "Dans l'appli, la cloche avec le nombre sur les boutons du haut te montre les choses à voir.",
        "🩺 Salute → menu « 🔔 Avvisi » → choisis les canaux et touche « Messaggio di prova » (message d'essai).", "alertes notifications rappels telegram e-mail whatsapp calendrier cloche message d'essai régler"),
    "g_cestino": ("Je me suis trompé : la Corbeille",
        "N'aie pas peur de te tromper. Quand tu supprimes quelque chose, le bouton Annuler apparaît quelques secondes en haut de la page : touche-le et tout revient comme avant. "
        "Si tu t'en aperçois plus tard, ouvre la Corbeille dans Outils : les choses supprimées y restent trente jours et avec Restaurer elles reviennent à leur place. "
        "Toi seul peux décider de les supprimer pour toujours.",
        "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina (Restaurer).", "trompé erreur supprimé par erreur annuler corbeille restaurer récupérer trente jours"),
    "g_aiuto": ("De l'aide toujours à portée de main",
        "Si tu ne te souviens plus comment faire quelque chose, tu as trois aides. Le bouton rouge « Clicca per informazioni » en haut, avec le guide de chaque page et une case pour chercher. "
        "Moi, le petit robot : touche-moi et je t'explique la page où tu es, ou écris-moi ou dis-moi une question avec le micro. "
        "Et les Nouveautés, où je te raconte ce qu'il y a de nouveau. Tu peux rendre ma voix plus lente ou plus rapide, changer de langue, ou m'éteindre : tu me rallumes depuis le bouton rouge.",
        "Le petit robot en bas à droite ; le bouton rouge en haut de chaque page.", "aide guide informations question micro voix lente rapide nouveautés éteindre assistant"),
    "g_fine": ("Fin de la visite",
        "La visite est finie, bravo ! Maintenant tu connais toutes les parties de l'appli. Tu n'as pas à tout retenir : chaque fois que tu en as besoin, touche-moi et demande-moi. "
        "Commence par les choses que tu utilises le plus, par exemple le Garde-manger ou les médicaments de la famille, et découvre le reste tranquillement. Bon travail !",
        "", "fin visite terminée merci recommencer"),
}
AG_UI["fr"] = {
    "a_giro": "🧭 Visite complète de l'appli", "a_giro_dlg": "🧭 Fais-moi la visite complète de l'appli (le petit robot la raconte à voix haute)",
    "a_capitoli": "📑 Chapitres", "a_pausa": "⏸ Pause", "a_riprendi": "▶ Reprendre", "a_dove": "Où ça se trouve :",
    "a_lingua": "🌐 Langue", "a_lingua_t": "Dans quelle langue veux-tu que je parle ?", "a_lingua_x": "Choisis ci-dessous. La langue de l'appli ne change pas : ma voix, la visite et les réponses changent.",
    "a_lingua_ok": "Parfait, à partir de maintenant je parle français.", "a_cap_t": "Les chapitres de la visite", "a_cap_x": "Touche un chapitre pour y aller directement.",
    "a_primo_t": "Bonjour ! C'est la première fois que tu m'ouvres", "a_primo_x": "Veux-tu que je te fasse la visite complète de l'appli ? Elle dure quelques minutes et tu peux m'arrêter quand tu veux. Touche le bouton jaune ci-dessous, ou « Fais-moi la visite ».",
    "a_primo_btn": "🧭 Fais-moi la visite", "a_fine_t": "Fin de la visite", "a_fine_x": "Voilà ! S'il te faut autre chose, demande-moi.",
    "a_vel": "🐢 Vitesse de la voix", "a_vel_0": "lente", "a_vel_1": "normale", "a_vel_2": "rapide", "a_vel_prova": "Voici ma voix à la nouvelle vitesse.",
    "a_trov_t": "Je ne trouve pas d'instructions là-dessus", "a_trov_x": "Je ne veux pas t'indiquer une procédure qui pourrait ne pas marcher : peut-être que cette fonction n'existe pas dans l'appli, ou j'utilise d'autres mots que les tiens. Essaie avec d'autres mots (même un seul : photo, échéance, mot de passe) ou choisis un sujet ci-dessous.",
}

# =====================================================================================================================
AG_TR["de"] = {
    "g_benvenuto": ("Willkommen! Ich bin dein Assistent",
        "Hallo! Ich bin der kleine Roboter der App «La nostra dispensa» (Unsere Vorratskammer). Jetzt mache ich mit dir den kompletten Rundgang: Ich erkläre dir alle Teile der App, einen nach dem anderen, mit einfachen Worten. "
        "Wenn die Stimme an ist, gehe ich von allein weiter: Tippe auf Pause, um mich anzuhalten, auf Weiter oder Zurück, um dich zu bewegen, auf Kapitel, um dorthin zu springen, wo du willst. "
        "Du kannst mir jederzeit eine Frage stellen, schriftlich oder mit dem Mikrofon. Mit der Weltkugel-Taste wechselst du meine Sprache.",
        "", "willkommen start kompletter rundgang roboter assistent sprache pause weiter kapitel"),
    "g_entrare": ("In die App kommen",
        "Jede Person der Familie hat ihr eigenes Passwort. Wenn du hineingehst, siehst du nur deine Sachen: deine Produkte, deine Medikamente, deine Dokumente. "
        "Niemand sonst sieht sie, außer dem, was du teilen möchtest. Auf dem ersten Bildschirm kannst du die Sprache der App wählen. "
        "Oben links ist ein Pfeil mit zwei Spitzen: Er öffnet das Seitenmenü, wo du deine Allergien, die Sprache und andere Einstellungen findest.",
        "Erster Bildschirm: Passwort eingeben und auf Eintreten («Entra») tippen.", "eintreten passwort sprache seitenmenü pfeil allergien zugang anmelden"),
    "g_home": ("Die Startseite und die Tasten der Bereiche",
        "Oben auf jeder Seite gibt es eine Reihe bunter Tasten: Vorratskammer («Dispensa»), Gesundheit («Salute»), Meine Dokumente, Archiv, Haus («Casa»), Arbeit («Lavoro»), Auto, Chat und Werkzeuge («Utilità»). "
        "Schiebe die Reihe mit dem Finger, um die letzten zu sehen. Du tippst auf eine Taste und kommst in diesen Teil der App. "
        "Wenn auf einer Taste eine Glocke mit einer Zahl erscheint, gibt es dort etwas anzusehen: eine nahe Frist oder eine neue Nachricht. "
        "Unter den Tasten findest du immer die rote Taste «Clicca per informazioni» (Für Informationen tippen) mit der Anleitung.",
        "Die Reihe bunter Tasten oben auf jeder Seite.", "startseite tasten bereiche leiste glocke zahl hinweise farben navigieren"),
    "g_dispensa": ("Die Vorratskammer: Produkte und Haltbarkeit",
        "Die Vorratskammer ist die Liste von dem, was du zu Hause zu essen und zu trinken hast. Tippe auf Hinzufügen, fotografiere das Produkt oder tippe den Strichcode ein, und die App füllt den Namen aus. "
        "Dann schreibst du, wie viele Stück du hast, und das Haltbarkeitsdatum. Die Farben sagen dir, wann du handeln musst: Grün alles gut, Orange läuft in zwei Monaten ab, Rot in einem Monat, Dunkel schon abgelaufen. "
        "Es gibt drei Teile: Erwachsene, Babys und Tiere, damit du sofort weißt, für wen jedes Produkt ist.",
        "Grüne Taste 🏠 Dispensa → unten die Reiter Vorratskammer, Hinzufügen, Verwalten, Einkauf.", "vorratskammer produkte haltbarkeit hinzufügen foto strichcode farben grün orange rot babys tiere"),
    "g_dispensa2": ("Allergien, Einkaufsliste und Statistiken",
        "Im Seitenmenü wählst du deine Allergien: Die für dich gefährlichen Produkte zeigen eine Sirene, so erkennst du sie sofort. "
        "Wenn ein Produkt aufgebraucht ist, tippe auf «Aufgebraucht» und es wandert von allein in die Einkaufsliste, die du in den Supermarkt mitnehmen kannst. "
        "Mit Verwalten änderst du Mengen und Daten vieler Produkte auf einmal. Die Statistiken zeigen dir, wie viel du weggeworfen hast, um weniger zu verschwenden. "
        "Es gibt auch die Familien-Vorratskammer für die gemeinsamen Sachen.",
        "🏠 Dispensa → Reiter Einkauf («Spesa») und Verwalten («Gestisci»); Allergien im Seitenmenü (Pfeil oben links).", "allergien allergene sirene einkaufsliste aufgebraucht verwalten statistiken verschwendung familie"),
    "g_salute": ("Gesundheit: die Personen und die Medikamente",
        "In Gesundheit kümmerst du dich um die Gesundheit der ganzen Familie. Wähle zuerst die Person: du, Mama, die Kinder. Jede hat ihr Profil mit Blutgruppe und Medikamentenallergien. "
        "Dann fügst du die Medikamente mit Haltbarkeitsdatum hinzu: Du kannst die Packung fotografieren. Zu jedem Medikament kannst du den Beipackzettel in einfachen Worten lesen. "
        "Die App zählt die Vorräte: Wenn ein Medikament zur Neige geht, sagt sie es dir und bereitet die Rezeptanfrage für die Ärztin vor.",
        "Rote Taste 🩺 Salute → oben die Person wählen → Reiter Medikamente («Medicinali»).", "gesundheit person profil mama medikamente haltbarkeit beipackzettel vorrat rezept ärztin blutgruppe"),
    "g_terapie": ("Therapien und Erinnerungen",
        "Eine Therapie ist ein Medikament, das regelmäßig genommen wird: jeden Tag zu einer bestimmten Uhrzeit oder ab und zu, zum Beispiel eine Ampulle alle fünfzehn Tage. "
        "Die App erinnert dich, wann du es nehmen musst: mit einer Nachricht auf Telegram, per E-Mail oder auf WhatsApp. "
        "Du kannst die Alarme auch in den Kalender des Telefons laden: So klingelt der Wecker zur richtigen Zeit, auch ohne die App zu öffnen. "
        "Für jede Therapie schreibst du Medikament, Dosis, Uhrzeit und Dauer.",
        "🩺 Salute → Reiter Therapien («Terapie») → ➕ Neue Therapie; Alarme in «📅 Allarmi sul Calendario del telefono».", "therapie erinnerung hinweis uhrzeit dosis telegram e-mail whatsapp kalender wecker alarm jeden tag intervalle"),
    "g_visite": ("Termine, Impfungen, Arzt und Gesundheitskarte",
        "In Gesundheit trägst du auch Termine und Untersuchungen ein, mit Datum und Uhrzeit: Du kannst den Terminzettel fotografieren und die App liest das Datum von allein. "
        "Nach dem Termin bewahrst du den Befund auf. Es gibt die Impfungen mit Auffrischungen, die Karte deines Arztes und die Gesundheitskarte mit den Links zur elektronischen Patientenakte. "
        "Mit einem Tipp bereitest du eine vollständige Zusammenfassung einer Person vor, um sie dem Arzt zu zeigen oder per E-Mail zu schicken.",
        "🩺 Salute → Reiter Termine («Visite») und Impfungen («Vaccini»); blaues Abzeichen der Gesundheitskarte neben der Ärztin.", "termine untersuchungen befund buchung impfungen auffrischung arzt gesundheitskarte akte zusammenfassung"),
    "g_documenti": ("Meine Dokumente",
        "Hier bewahrst du die persönlichen Dokumente auf: Personalausweis, Führerschein, Reisepass, Gesundheitskarte, Aufenthaltstitel. "
        "Fotografiere das Dokument: Die App entfernt den Hintergrund, richtet es gerade und versucht, Art, Nummer und Ablaufdatum zu lesen. Du kannst immer von Hand korrigieren. "
        "Sechs Monate und drei Monate vor dem Ablauf warnt dich die App, damit du rechtzeitig verlängerst. Die Dokumente gehören nur dir: Niemand sonst sieht sie.",
        "Blaue Taste 📁 I miei documenti → «Aggiungi un documento» (Dokument hinzufügen).", "dokumente personalausweis führerschein reisepass foto ablauf verlängerung hinweis datenschutz"),
    "g_archivio": ("Das Archiv: alle Dateien an einem Ort",
        "Das Archiv sammelt alle Dateien, die du in der App gespeichert hast: Fotos von Dokumenten, Beipackzettel, Befunde, Anleitungen, Rechnungen. "
        "Du suchst sie, indem du ein Wort schreibst, filterst sie nach Art oder Person, öffnest sie, lädst sie herunter oder schickst sie per E-Mail und WhatsApp. "
        "Wenn eine Angabe falsch ist, korrigierst du sie, und du kannst die Datei durch eine bessere ersetzen. Es ist wie ein großer, ordentlicher Ordner, immer in der Tasche.",
        "Violette Taste 🗂️ Archivio → Suchfeld oben.", "archiv dateien suchen filtern öffnen herunterladen senden korrigieren ordner"),
    "g_casa": ("Haus: Geräte, Anleitungen und Garantien",
        "In Haus verwaltest du die Geräte des Hauses: Waschmaschine, Kühlschrank, Heizung, Fernseher. Zu jedem speicherst du die Anleitung, die Garantie, den Kassenbon und die Rechnungen. "
        "Wenn das Gerät ein Problem macht, suchst du ein Wort in der Anleitung, zum Beispiel den Fehlercode oder «Filterreinigung»: Die App zeigt dir die richtigen Seiten mit den markierten Wörtern. "
        "Wenn du willst, erklärt sie sie dir in einfachen Worten. Du kannst Dokumente auch aus der E-Mail oder aus den Apps der Anbieter schicken.",
        "Orange Taste 🏡 Casa → Reiter Beni (Güter) und Documenti → auf dem Dokument «🔎 Cerca nel manuale».", "haus güter geräte haushaltsgeräte anleitung garantie rechnung kassenbon in der anleitung suchen fehler erklär mir"),
    "g_casa2": ("Wartung und Verwaltung des Hauses",
        "In Haus trägst du auch die Wartungen ein, wie die Heizungswartung, und die App erinnert dich an die nächste. "
        "Im Reiter Verwaltung führst du die Hausgeldkosten und die Raten mit den Zahlungsterminen, die Kontakte von Klempner, Elektriker und Hausverwalter "
        "und den Kalender der Mülltrennung mit der Sperrmüllabholung. Du kannst die ganze Verwaltung einem anderen Nutzer mit einer passwortgeschützten Datei schicken.",
        "🏡 Casa → Reiter Manutenzioni und Amministrazione.", "wartung heizung verwaltung hausgeld kosten raten zahlungen kontakte klempner elektriker mülltrennung sperrmüll austausch"),
    "g_lavoro": ("Arbeit: Lohnzettel und Dokumente",
        "In Arbeit lädst du die Lohnzettel hoch, auch indem du sie fotografierst: Die App liest die Zahlen und ordnet sie. "
        "Jahr für Jahr siehst du die Diagramme und den Vergleich zwischen den Monaten. Du bewahrst die jährliche Steuerbescheinigung (CU) und die Dokumente der INPS auf. "
        "Es gibt auch das Adressbuch der Gewerkschaft, des CAF und des Patronato, mit Telefon und Öffnungszeiten, damit du sie sofort findest, wenn sie gebraucht werden.",
        "Graue Taste 💼 Lavoro → Reiter Buste paga, Anno per anno, CU, INPS, Sindacato.", "arbeit lohnzettel gehalt diagramme jahr bescheinigung cu inps gewerkschaft caf patronato"),
    "g_auto": ("Auto: die Garage und die Fristen",
        "In Auto ist deine Garage: Jedes Fahrzeug hat seine Karte. Du kannst den Fahrzeugschein fotografieren und die App liest Kennzeichen, Marke und Modell. "
        "Sie erinnert dich an Kfz-Steuer, Versicherung und Hauptuntersuchung, bevor sie ablaufen. Du trägst Wartungen, Tankfüllungen und Ausgaben ein, so weißt du, was dich das Auto kostet. "
        "Es gibt auch den Führerschein mit den Punkten und den Strafzetteln, und die Fahrten mit den Kilometererstattungen.",
        "Hellblaue Taste 🚗 Auto → die Garage → auf ein Fahrzeug tippen → Scadenze, Manutenzione, Rifornimenti.", "auto fahrzeug garage kennzeichen fahrzeugschein steuer versicherung hauptuntersuchung wartung tanken ausgaben führerschein strafzettel fahrten"),
    "g_auto2": ("Auto: Kontrollleuchten, Diagnose und Notfall",
        "Wenn am Armaturenbrett eine Kontrollleuchte angeht, fotografiere sie: Die App sagt dir, was sie bedeutet und ob du weiterfahren kannst. "
        "In Diagnose findest du die Fehlercodes und, mit einem kleinen Gerät zum Anschließen ans Auto, auch die Motordaten. "
        "In Notfall hast du die nützlichen Nummern, die Pannenhilfe und den Unfallbericht, mit den Schritten, die du bei einem Unfall in Ruhe befolgen kannst.",
        "🚗 Auto → Diagnostica → «📷 Fotografa una spia»; 🚗 Auto → Emergenza.", "kontrollleuchte armaturenbrett diagnose fehlercodes obd notfall pannenhilfe unfall unfallbericht"),
    "g_chat": ("Der Familien-Chat",
        "Mit dem Chat schreibst du den Personen der Familie, ohne die App zu verlassen, kostenlos. Oben wählst du, mit wem du sprichst: Alle («Tutti»), also die Familiengruppe, oder nur eine Person, privat. "
        "Wähle, wen du als Taste im Blick behalten willst; die anderen Personen bleiben im Menü «Altre persone» (Andere Personen). "
        "Deine Nachrichten stehen rechts in Grün, die der anderen links in Weiß. Ein roter Punkt mit der Zahl sagt dir, wie viele neue Nachrichten du hast.",
        "Taste 💬 Chat oben → Person wählen → unten schreiben → 📨 Invia (Senden).", "chat nachrichten familie schreiben alle privat personen im blick andere personen neue nachrichten"),
    "g_utilita": ("Die Werkzeuge",
        "In Werkzeuge sind die Hilfsmittel. Der Papierkorb, in dem gelöschte Sachen dreißig Tage bleiben. Das Aussehen der App, für größere Texte. "
        "Der Datenaustausch, um deine Daten an eine andere Person zu schicken oder zu empfangen. Speicher freigeben, um unnütze Dateien vom Telefon zu entfernen. "
        "Und die nützlichen Apps, wie Wimbi und Velocity Music, mit ihrem Beipackzettel, der erklärt, was sie tun.",
        "Violette Taste 🧰 Utilità, die letzte der Reihe oben.", "werkzeuge papierkorb aussehen große texte datenaustausch speicher freigeben wimbi velocity nützliche apps"),
    "g_avvisi": ("Wie die Hinweise ankommen",
        "Die App warnt dich vor Fristen und zur Therapiezeit. Die Hinweise kommen auf Telegram, per E-Mail, auf WhatsApp oder als Alarm im Kalender des Telefons: Du wählst, welche. "
        "Telegram und E-Mail sind kostenlos und sicher; du richtest sie nur einmal ein. In Gesundheit gibt es die Taste für eine Testnachricht, so prüfst du, ob alles funktioniert. "
        "In der App zeigt dir die Glocke mit der Zahl auf den oberen Tasten die Dinge, die du ansehen solltest.",
        "🩺 Salute → Aufklappmenü «🔔 Avvisi» → Kanäle wählen und auf «Messaggio di prova» (Testnachricht) tippen.", "hinweise benachrichtigungen erinnerungen telegram e-mail whatsapp kalender glocke testnachricht einrichten"),
    "g_cestino": ("Ich habe einen Fehler gemacht: der Papierkorb",
        "Hab keine Angst, Fehler zu machen. Wenn du etwas löschst, erscheint oben auf der Seite für ein paar Sekunden die Taste Rückgängig: Tippe darauf und alles ist wie vorher. "
        "Wenn du es später merkst, öffne den Papierkorb in Werkzeuge: Gelöschte Sachen bleiben dort dreißig Tage und mit Wiederherstellen kommen sie an ihren Platz zurück. "
        "Nur du kannst entscheiden, sie für immer zu löschen.",
        "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina (Wiederherstellen).", "fehler versehentlich gelöscht rückgängig papierkorb wiederherstellen zurückholen dreißig tage"),
    "g_aiuto": ("Hilfe immer griffbereit",
        "Wenn du nicht mehr weißt, wie etwas geht, hast du drei Hilfen. Die rote Taste «Clicca per informazioni» oben, mit der Anleitung jeder Seite und einem Suchfeld. "
        "Mich, den kleinen Roboter: Tippe mich an und ich erkläre dir die Seite, auf der du bist, oder schreib mir oder sag mir eine Frage mit dem Mikrofon. "
        "Und die Neuigkeiten, wo ich dir erzähle, was neu ist. Du kannst meine Stimme langsamer oder schneller machen, die Sprache wechseln oder mich ausschalten: Du schaltest mich über die rote Taste wieder ein.",
        "Der kleine Roboter unten rechts; die rote Taste oben auf jeder Seite.", "hilfe anleitung informationen frage mikrofon stimme langsam schnell neuigkeiten ausschalten assistent"),
    "g_fine": ("Ende des Rundgangs",
        "Der Rundgang ist zu Ende, gut gemacht! Jetzt kennst du alle Teile der App. Du musst dir nicht alles merken: Wann immer du es brauchst, tippe mich an und frag mich. "
        "Fang mit den Dingen an, die du am meisten benutzt, zum Beispiel die Vorratskammer oder die Medikamente der Familie, und entdecke den Rest in Ruhe. Viel Erfolg!",
        "", "ende rundgang fertig danke neu beginnen"),
}
AG_UI["de"] = {
    "a_giro": "🧭 Kompletter Rundgang durch die App", "a_giro_dlg": "🧭 Mach mit mir den kompletten Rundgang durch die App (der Roboter erzählt ihn laut)",
    "a_capitoli": "📑 Kapitel", "a_pausa": "⏸ Pause", "a_riprendi": "▶ Weiter", "a_dove": "Wo es ist:",
    "a_lingua": "🌐 Sprache", "a_lingua_t": "In welcher Sprache soll ich sprechen?", "a_lingua_x": "Wähle unten. Die Sprache der App ändert sich nicht: Meine Stimme, der Rundgang und die Antworten ändern sich.",
    "a_lingua_ok": "Perfekt, ab jetzt spreche ich Deutsch.", "a_cap_t": "Die Kapitel des Rundgangs", "a_cap_x": "Tippe auf ein Kapitel, um direkt dorthin zu gehen.",
    "a_primo_t": "Hallo! Du öffnest mich zum ersten Mal", "a_primo_x": "Möchtest du den kompletten Rundgang durch die App? Er dauert ein paar Minuten und du kannst mich jederzeit anhalten. Tippe unten auf die gelbe Taste oder auf «Mach den Rundgang».",
    "a_primo_btn": "🧭 Mach den Rundgang", "a_fine_t": "Ende des Rundgangs", "a_fine_x": "Fertig! Wenn du noch etwas brauchst, frag mich.",
    "a_vel": "🐢 Sprechgeschwindigkeit", "a_vel_0": "langsam", "a_vel_1": "normal", "a_vel_2": "schnell", "a_vel_prova": "Das ist meine Stimme mit der neuen Geschwindigkeit.",
    "a_trov_t": "Dazu finde ich keine Anleitung", "a_trov_x": "Ich möchte dir keinen Ablauf nennen, der vielleicht nicht funktioniert: Vielleicht gibt es diese Funktion in der App nicht, oder ich benutze andere Wörter als du. Versuche es mit anderen Wörtern (auch nur einem: Foto, Ablauf, Passwort) oder wähle unten ein Thema.",
}

# =====================================================================================================================
AG_TR["ro"] = {
    "g_benvenuto": ("Bine ai venit! Sunt asistentul tău",
        "Salut! Sunt robotul aplicației «La nostra dispensa» (Cămara noastră). Acum îți fac turul complet: îți explic toate părțile aplicației, una câte una, cu cuvinte simple. "
        "Dacă vocea este pornită merg mai departe singur: apasă Pauză ca să mă oprești, Înainte sau Înapoi ca să te miști, Capitole ca să sari unde vrei. "
        "Poți să-mi pui o întrebare oricând, scriind-o sau cu microfonul. Cu butonul cu globul îmi schimbi limba.",
        "", "bine ai venit început tur complet robot asistent limbă pauză înainte capitole"),
    "g_entrare": ("Intrarea în aplicație",
        "Fiecare persoană din familie are parola ei. Când intri vezi doar lucrurile tale: produsele tale, medicamentele tale, documentele tale. "
        "Nimeni altcineva nu le vede, în afară de ce alegi să împarți. Pe primul ecran poți alege limba aplicației. "
        "Sus în stânga este o săgeată cu două vârfuri: deschide meniul lateral, unde găsești alergiile tale, limba și alte setări.",
        "Primul ecran: scrie parola și apasă Intră («Entra»).", "intrare parolă limbă meniu lateral săgeată alergii acces autentificare"),
    "g_home": ("Pagina principală și butoanele secțiunilor",
        "Sus, pe fiecare pagină, este un rând de butoane colorate: Cămară («Dispensa»), Sănătate («Salute»), Documentele mele, Arhivă, Casă («Casa»), Muncă («Lavoro»), Mașină («Auto»), Chat și Utilități («Utilità»). "
        "Glisează rândul cu degetul ca să le vezi pe ultimele. Apeși un buton și intri în acea parte a aplicației. "
        "Dacă pe un buton apare un clopoțel cu un număr, acolo este ceva de văzut: un termen apropiat sau un mesaj nou. "
        "Sub butoane găsești mereu butonul roșu «Clicca per informazioni» (Apasă pentru informații) cu ghidul.",
        "Rândul de butoane colorate de sus, pe fiecare pagină.", "pagina principală butoane secțiuni bară clopoțel număr alerte culori navigare"),
    "g_dispensa": ("Cămara: produse și termene de valabilitate",
        "Cămara este lista cu ce ai acasă de mâncat și de băut. Apasă Adaugă, fă poza produsului sau scrie codul de bare, iar aplicația completează numele. "
        "Apoi scrie câte bucăți ai și data de expirare. Culorile îți spun când să acționezi: verde totul bine, portocaliu expiră în două luni, roșu într-o lună, închis deja expirat. "
        "Sunt trei părți: Adulți, Bebeluși și Animale, ca să știi imediat pentru cine este fiecare produs.",
        "Butonul verde 🏠 Dispensa → jos filele Cămară, Adaugă, Gestionează, Cumpărături.", "cămară produse expirare adaugă poză cod de bare culori verde portocaliu roșu bebeluși animale"),
    "g_dispensa2": ("Alergii, lista de cumpărături și statistici",
        "În meniul lateral alege alergiile tale: produsele periculoase pentru tine arată o sirenă, așa le recunoști imediat. "
        "Când un produs se termină, apasă «L-am consumat» și merge singur în Lista de cumpărături, pe care o poți lua la supermarket. "
        "Cu Gestionează schimbi cantitățile și termenele multor produse deodată. Statisticile îți arată cât ai aruncat, ca să risipești mai puțin. "
        "Există și Cămara familiei, pentru lucrurile în comun.",
        "🏠 Dispensa → filele Cumpărături («Spesa») și Gestionează («Gestisci»); alergiile în meniul lateral (săgeata din stânga sus).", "alergii alergeni sirenă listă cumpărături consumat gestionează statistici risipă familie"),
    "g_salute": ("Sănătate: persoanele și medicamentele",
        "În Sănătate ții sănătatea întregii familii. Mai întâi alege persoana: tu, mama, copiii. Fiecare are profilul său cu grupa sanguină și alergiile la medicamente. "
        "Apoi adaugă medicamentele cu data de expirare: poți fotografia cutia. Pentru fiecare medicament poți citi prospectul în cuvinte simple. "
        "Aplicația numără stocurile: când un medicament e pe terminate îți spune și îți pregătește cererea de rețetă pentru doctoriță.",
        "Butonul roșu 🩺 Salute → alege persoana sus → fila Medicamente («Medicinali»).", "sănătate persoană profil mama medicamente expirare prospect stoc rețetă doctoriță grupa sanguină"),
    "g_terapie": ("Tratamente și memento-uri",
        "Un tratament este un medicament de luat regulat: în fiecare zi la o anumită oră, sau din când în când, de exemplu o fiolă la cincisprezece zile. "
        "Aplicația îți amintește când să-l iei: cu un mesaj pe Telegram, prin e-mail sau pe WhatsApp. "
        "Poți descărca alarmele și în Calendarul telefonului: așa sună alarma la ora potrivită, chiar fără să deschizi aplicația. "
        "Pentru fiecare tratament scrie medicamentul, doza, ora și cât durează.",
        "🩺 Salute → fila Tratamente («Terapie») → ➕ Tratament nou; alarmele în «📅 Allarmi sul Calendario del telefono».", "tratament terapie memento alertă oră doză telegram e-mail whatsapp calendar alarmă zilnic intervale"),
    "g_visite": ("Consultații, vaccinuri, doctor și card de sănătate",
        "În Sănătate notezi și consultațiile și analizele, cu data și ora: poți fotografia foaia de programare și aplicația citește data singură. "
        "După consultație păstrezi rezultatul. Sunt vaccinurile cu rapelurile, fișa doctorului tău și cardul de sănătate, cu linkurile către dosarul medical. "
        "Cu o atingere pregătești un rezumat complet al unei persoane, de arătat medicului sau de trimis prin e-mail.",
        "🩺 Salute → filele Consultații («Visite») și Vaccinuri («Vaccini»); ecusonul albastru al cardului de sănătate lângă doctoriță.", "consultații analize rezultat programare vaccinuri rapel doctor card de sănătate dosar rezumat"),
    "g_documenti": ("Documentele mele",
        "Aici păstrezi documentele personale: cartea de identitate, permisul de conducere, pașaportul, cardul de sănătate, permisul de ședere. "
        "Fă poza documentului: aplicația scoate fundalul, îl îndreaptă și încearcă să citească tipul, numărul și data expirării. Poți corecta oricând de mână. "
        "Cu șase luni și cu trei luni înainte de expirare aplicația te anunță, ca să reînnoiești la timp. Documentele sunt doar ale tale: nimeni altcineva nu le vede.",
        "Butonul albastru 📁 I miei documenti → «Aggiungi un documento» (Adaugă un document).", "documente carte identitate permis pașaport poză expirare reînnoire alertă confidențialitate"),
    "g_archivio": ("Arhiva: toate fișierele într-un loc",
        "Arhiva adună toate fișierele salvate în aplicație: poze de documente, prospecte, rezultate, manuale, facturi. "
        "Le cauți scriind un cuvânt, le filtrezi după tip sau persoană, le deschizi, le descarci sau le trimiți prin e-mail și WhatsApp. "
        "Dacă o informație e greșită o corectezi, și poți înlocui fișierul cu unul mai bun. E ca un biblioraft mare și ordonat, mereu în buzunar.",
        "Butonul violet 🗂️ Archivio → căsuța de căutare de sus.", "arhivă fișiere caută filtrează deschide descarcă trimite corectează biblioraft"),
    "g_casa": ("Casă: aparate, manuale și garanții",
        "În Casă ții aparatele din casă: mașina de spălat, frigiderul, centrala, televizorul. Pentru fiecare salvezi manualul, garanția, bonul și facturile. "
        "Dacă aparatul are o problemă, cauți un cuvânt în manual, de exemplu codul erorii sau «curățarea filtrului»: aplicația îți arată paginile potrivite cu cuvintele evidențiate. "
        "Dacă vrei, ți le explică în cuvinte simple. Poți trimite documente și din e-mail sau din aplicațiile furnizorilor.",
        "Butonul portocaliu 🏡 Casa → filele Beni (bunuri) și Documenti → pe document «🔎 Cerca nel manuale».", "casă bunuri aparate electrocasnice manual garanție factură bon caută în manual eroare explică-mi"),
    "g_casa2": ("Întreținere și Administrarea casei",
        "În Casă înregistrezi și lucrările de întreținere, cum ar fi revizia centralei, iar aplicația îți amintește următoarea. "
        "În fila Administrare ții cheltuielile de bloc și ratele cu datele de plată, contactele instalatorului, electricianului și administratorului, "
        "și calendarul colectării selective cu ridicarea deșeurilor voluminoase. Poți trimite toată Administrarea altui utilizator cu un fișier protejat cu parolă.",
        "🏡 Casa → filele Manutenzioni și Amministrazione.", "întreținere centrală administrare bloc cheltuieli rate plăți contacte instalator electrician colectare selectivă voluminoase schimb"),
    "g_lavoro": ("Muncă: fluturași de salariu și documente",
        "În Muncă încarci fluturașii de salariu, chiar fotografiindu-i: aplicația citește cifrele și le pune în ordine. "
        "An de an vezi graficele și comparația între luni. Păstrezi certificatul fiscal anual (CU) și documentele de la INPS. "
        "Există și agenda sindicatului, a CAF-ului și a patronatului, cu telefon și program, ca să le găsești imediat când e nevoie.",
        "Butonul gri 💼 Lavoro → filele Buste paga, Anno per anno, CU, INPS, Sindacato.", "muncă fluturaș salariu grafice an certificat cu inps sindicat caf patronat"),
    "g_auto": ("Mașină: garajul și termenele",
        "În Mașină este garajul tău: fiecare vehicul are fișa lui. Poți fotografia certificatul de înmatriculare și aplicația citește numărul, marca și modelul. "
        "Îți amintește taxa, asigurarea și inspecția tehnică înainte să expire. Înregistrezi întreținerea, alimentările și cheltuielile, așa știi cât te costă mașina. "
        "Există și permisul cu punctele și amenzile, și călătoriile cu decontările pe kilometru.",
        "Butonul bleu 🚗 Auto → garajul → apasă un vehicul → Scadenze, Manutenzione, Rifornimenti.", "mașină vehicul garaj număr talon taxă asigurare itp întreținere alimentare cheltuieli permis amenzi călătorii"),
    "g_auto2": ("Mașină: martori, diagnoză și urgență",
        "Dacă pe bord se aprinde un martor, fotografiază-l: aplicația îți spune ce înseamnă și dacă poți continua să conduci. "
        "În Diagnoză găsești codurile de eroare și, cu un mic aparat de conectat la mașină, și datele motorului. "
        "În Urgență ai numerele utile, asistența rutieră și formularul de accident, cu pașii de urmat cu calm dacă ai un accident.",
        "🚗 Auto → Diagnostica → «📷 Fotografa una spia»; 🚗 Auto → Emergenza.", "martor bord diagnoză coduri eroare obd urgență asistență rutieră accident constatare"),
    "g_chat": ("Chatul familiei",
        "Cu Chatul scrii persoanelor din familie fără să ieși din aplicație, gratuit. Sus alegi cu cine vorbești: Toți («Tutti»), adică grupul familiei, sau o singură persoană, în privat. "
        "Alegi pe cine să ții la vedere ca buton; celelalte persoane stau în meniul «Altre persone» (Alte persoane). "
        "Mesajele tale sunt în dreapta, verzi, ale celorlalți în stânga, albe. Un punct roșu cu număr îți spune câte mesaje noi ai.",
        "Butonul 💬 Chat de sus → alege persoana → scrie jos → 📨 Invia (Trimite).", "chat mesaje familie scrie toți privat persoane la vedere alte persoane mesaje noi"),
    "g_utilita": ("Utilitățile",
        "În Utilități sunt instrumentele de serviciu. Coșul, unde lucrurile șterse rămân treizeci de zile. Aspectul aplicației, pentru texte mai mari. "
        "Schimbul de date, ca să trimiți datele tale altei persoane sau să le primești. Eliberează spațiu, ca să scoți fișierele inutile din telefon. "
        "Și aplicațiile utile, cum ar fi Wimbi și Velocity Music, cu prospectul lor care explică ce fac.",
        "Butonul violet 🧰 Utilità, ultimul din rândul de sus.", "utilități coș aspect texte mari schimb date eliberează spațiu wimbi velocity aplicații utile"),
    "g_avvisi": ("Cum sosesc alertele",
        "Aplicația te anunță înainte de termene și la ora tratamentelor. Alertele sosesc pe Telegram, prin e-mail, pe WhatsApp sau ca alarmă în Calendarul telefonului: alegi tu care. "
        "Telegram și e-mailul sunt gratuite și sigure; le setezi o singură dată. În Sănătate este butonul pentru un mesaj de probă, ca să verifici că totul funcționează. "
        "În aplicație, clopoțelul cu număr de pe butoanele de sus îți arată lucrurile de văzut.",
        "🩺 Salute → lista «🔔 Avvisi» → alege canalele și apasă «Messaggio di prova» (mesaj de probă).", "alerte notificări memento telegram e-mail whatsapp calendar clopoțel mesaj de probă setare"),
    "g_cestino": ("Am greșit: Coșul",
        "Nu-ți fie teamă să greșești. Când ștergi ceva, sus pe pagină apare câteva secunde butonul Anulează: apasă-l și totul revine ca înainte. "
        "Dacă îți dai seama mai târziu, deschide Coșul din Utilități: lucrurile șterse rămân acolo treizeci de zile și cu Restaurează revin la locul lor. "
        "Doar tu poți decide să le ștergi pentru totdeauna.",
        "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina (Restaurează).", "greșit eroare șters din greșeală anulează coș restaurează recuperează treizeci de zile"),
    "g_aiuto": ("Ajutor mereu la îndemână",
        "Dacă nu-ți amintești cum se face ceva, ai trei ajutoare. Butonul roșu «Clicca per informazioni» de sus, cu ghidul fiecărei pagini și o căsuță de căutare. "
        "Eu, robotul: atinge-mă și îți explic pagina în care ești, sau scrie-mi ori spune-mi o întrebare cu microfonul. "
        "Și Noutățile, unde îți povestesc ce e nou. Poți face vocea mea mai lentă sau mai rapidă, poți schimba limba sau mă poți opri: mă repornești din butonul roșu.",
        "Robotul din dreapta jos; butonul roșu de sus de pe fiecare pagină.", "ajutor ghid informații întrebare microfon voce lentă rapidă noutăți oprire asistent"),
    "g_fine": ("Sfârșitul turului",
        "Turul s-a terminat, bravo! Acum cunoști toate părțile aplicației. Nu trebuie să ții minte tot: ori de câte ori ai nevoie, atinge-mă și întreabă-mă. "
        "Începe cu lucrurile pe care le folosești cel mai mult, de exemplu Cămara sau medicamentele familiei, și descoperă restul pe îndelete. Spor la treabă!",
        "", "sfârșit tur terminat mulțumesc reîncepe"),
}
AG_UI["ro"] = {
    "a_giro": "🧭 Turul complet al aplicației", "a_giro_dlg": "🧭 Fă-mi turul complet al aplicației (robotul îl povestește cu voce tare)",
    "a_capitoli": "📑 Capitole", "a_pausa": "⏸ Pauză", "a_riprendi": "▶ Continuă", "a_dove": "Unde se află:",
    "a_lingua": "🌐 Limba", "a_lingua_t": "În ce limbă vrei să vorbesc?", "a_lingua_x": "Alege mai jos. Limba aplicației nu se schimbă: se schimbă vocea mea, turul și răspunsurile.",
    "a_lingua_ok": "Perfect, de acum vorbesc română.", "a_cap_t": "Capitolele turului", "a_cap_x": "Apasă un capitol ca să mergi direct acolo.",
    "a_primo_t": "Salut! E prima dată când mă deschizi", "a_primo_x": "Vrei să-ți fac turul complet al aplicației? Durează câteva minute și mă poți opri oricând. Apasă butonul galben de mai jos, sau «Fă-mi turul».",
    "a_primo_btn": "🧭 Fă-mi turul", "a_fine_t": "Sfârșitul turului", "a_fine_x": "Gata! Dacă mai ai nevoie de ceva, întreabă-mă.",
    "a_vel": "🐢 Viteza vocii", "a_vel_0": "lentă", "a_vel_1": "normală", "a_vel_2": "rapidă", "a_vel_prova": "Aceasta este vocea mea cu noua viteză.",
    "a_trov_t": "Nu găsesc instrucțiuni despre asta", "a_trov_x": "Nu vreau să-ți indic o procedură care s-ar putea să nu funcționeze: poate funcția nu există în aplicație, sau folosesc alte cuvinte decât tine. Încearcă alte cuvinte (chiar și unul singur: poză, expirare, parolă) sau alege un subiect mai jos.",
}

# =====================================================================================================================
AG_TR["ar"] = {
    "g_benvenuto": ("أهلاً بك! أنا مساعدك",
        "مرحباً! أنا الروبوت الصغير لتطبيق «La nostra dispensa» (مخزننا). سأقوم الآن بالجولة الكاملة معك: أشرح لك كل أجزاء التطبيق، واحداً تلو الآخر، بكلمات بسيطة. "
        "إذا كان الصوت مفعّلاً أتابع وحدي: اضغط إيقاف مؤقت لإيقافي، التالي أو السابق للتنقل، الفصول للقفز إلى حيث تريد. "
        "يمكنك أن تسألني في أي وقت، كتابةً أو بالميكروفون. بزر الكرة الأرضية تغيّر لغتي.",
        "", "أهلا بداية جولة كاملة روبوت مساعد لغة إيقاف التالي فصول"),
    "g_entrare": ("الدخول إلى التطبيق",
        "لكل فرد من العائلة كلمة مرور خاصة به. عندما تدخل ترى أشياءك فقط: منتجاتك وأدويتك ومستنداتك. "
        "لا يراها أحد غيرك، باستثناء ما تختار مشاركته. في الشاشة الأولى يمكنك اختيار لغة التطبيق. "
        "في الأعلى على اليسار يوجد سهم برأسين: يفتح القائمة الجانبية، حيث تجد حساسياتك واللغة وإعدادات أخرى.",
        "الشاشة الأولى: اكتب كلمة المرور واضغط دخول («Entra»).", "دخول كلمة مرور لغة قائمة جانبية سهم حساسية وصول تسجيل"),
    "g_home": ("الصفحة الرئيسية وأزرار الأقسام",
        "في أعلى كل صفحة يوجد صف من الأزرار الملوّنة: المخزن («Dispensa»)، الصحة («Salute»)، مستنداتي، الأرشيف، المنزل («Casa»)، العمل («Lavoro»)، السيارة («Auto»)، الدردشة والأدوات («Utilità»). "
        "مرّر الصف بإصبعك لرؤية الأزرار الأخيرة. تضغط على زر فتدخل ذلك الجزء من التطبيق. "
        "إذا ظهر على زر جرس مع رقم، فهناك شيء يجب النظر إليه: موعد قريب أو رسالة جديدة. "
        "تحت الأزرار تجد دائماً الزر الأحمر «Clicca per informazioni» (اضغط للمعلومات) مع الدليل.",
        "صف الأزرار الملوّنة في أعلى كل صفحة.", "رئيسية أزرار أقسام شريط جرس رقم تنبيهات ألوان تنقل"),
    "g_dispensa": ("المخزن: المنتجات وتواريخ الانتهاء",
        "المخزن هو قائمة ما لديك في البيت من طعام وشراب. اضغط إضافة، صوّر المنتج أو اكتب الباركود، فيملأ التطبيق الاسم. "
        "ثم اكتب كم قطعة لديك وتاريخ الانتهاء. الألوان تخبرك متى تتصرف: الأخضر كل شيء بخير، البرتقالي ينتهي خلال شهرين، الأحمر خلال شهر، الداكن انتهى بالفعل. "
        "هناك ثلاثة أقسام: الكبار والرضّع والحيوانات، لتعرف فوراً لمن كل منتج.",
        "الزر الأخضر 🏠 Dispensa ← في الأسفل التبويبات المخزن، إضافة، إدارة، التسوّق.", "مخزن منتجات انتهاء إضافة صورة باركود ألوان أخضر برتقالي أحمر رضع حيوانات"),
    "g_dispensa2": ("الحساسية وقائمة التسوّق والإحصائيات",
        "في القائمة الجانبية اختر حساسياتك: المنتجات الخطرة عليك تُظهر صفارة إنذار، فتتعرف عليها فوراً. "
        "عندما ينتهي منتج، اضغط «استهلكته» فينتقل وحده إلى قائمة التسوّق التي يمكنك أخذها إلى السوبرماركت. "
        "بواسطة إدارة تغيّر الكميات وتواريخ الانتهاء لمنتجات كثيرة معاً. تُظهر لك الإحصائيات كم رميت، لتهدر أقل. "
        "يوجد أيضاً مخزن العائلة للأشياء المشتركة.",
        "🏠 Dispensa ← تبويبا التسوّق («Spesa») والإدارة («Gestisci»)؛ الحساسية في القائمة الجانبية (السهم أعلى اليسار).", "حساسية مسببات صفارة قائمة تسوق استهلكت إدارة إحصائيات هدر عائلة"),
    "g_salute": ("الصحة: الأشخاص والأدوية",
        "في الصحة تتابع صحة العائلة كلها. اختر أولاً الشخص: أنت، الأم، الأطفال. لكل واحد ملفه الشخصي مع فصيلة الدم وحساسية الأدوية. "
        "ثم أضف الأدوية مع تاريخ الانتهاء: يمكنك تصوير العلبة. لكل دواء يمكنك قراءة النشرة بكلمات بسيطة. "
        "يحسب التطبيق المخزون: عندما يوشك دواء على النفاد يخبرك ويجهّز لك طلب الوصفة للطبيبة.",
        "الزر الأحمر 🩺 Salute ← اختر الشخص في الأعلى ← تبويب الأدوية («Medicinali»).", "صحة شخص ملف أم أدوية انتهاء نشرة مخزون وصفة طبيبة فصيلة دم"),
    "g_terapie": ("العلاجات والتذكيرات",
        "العلاج هو دواء يؤخذ بانتظام: كل يوم في ساعة معينة، أو بين حين وآخر، مثلاً أمبولة كل خمسة عشر يوماً. "
        "يذكّرك التطبيق بموعد تناوله: برسالة على تيليغرام أو بالبريد الإلكتروني أو على واتساب. "
        "يمكنك أيضاً تنزيل المنبّهات إلى تقويم الهاتف: فيرنّ المنبّه في الوقت الصحيح، حتى دون فتح التطبيق. "
        "لكل علاج اكتب الدواء والجرعة والوقت ومدته.",
        "🩺 Salute ← تبويب العلاجات («Terapie») ← ➕ علاج جديد؛ المنبّهات في «📅 Allarmi sul Calendario del telefono».", "علاج تذكير تنبيه وقت جرعة تيليغرام بريد واتساب تقويم منبه كل يوم فترات"),
    "g_visite": ("المواعيد واللقاحات والطبيب والبطاقة الصحية",
        "في الصحة تسجّل أيضاً المواعيد والفحوصات، بالتاريخ والساعة: يمكنك تصوير ورقة الحجز فيقرأ التطبيق التاريخ وحده. "
        "بعد الموعد تحتفظ بالتقرير. هناك اللقاحات مع الجرعات المعزّزة، وبطاقة طبيبك، والبطاقة الصحية مع الروابط إلى الملف الصحي. "
        "بلمسة واحدة تجهّز ملخصاً كاملاً عن شخص، لعرضه على الطبيب أو إرساله بالبريد الإلكتروني.",
        "🩺 Salute ← تبويبا المواعيد («Visite») واللقاحات («Vaccini»)؛ شارة البطاقة الصحية الزرقاء بجانب الطبيبة.", "مواعيد فحوصات تقرير حجز لقاحات معززة طبيب بطاقة صحية ملف ملخص"),
    "g_documenti": ("مستنداتي",
        "هنا تحتفظ بالمستندات الشخصية: بطاقة الهوية، رخصة القيادة، جواز السفر، البطاقة الصحية، تصريح الإقامة. "
        "صوّر المستند: يزيل التطبيق الخلفية ويقوّمه ويحاول قراءة النوع والرقم وتاريخ الانتهاء. يمكنك دائماً التصحيح يدوياً. "
        "قبل الانتهاء بستة أشهر وبثلاثة أشهر ينبّهك التطبيق لتجدّد في الوقت المناسب. المستندات لك وحدك: لا يراها أحد غيرك.",
        "الزر الأزرق 📁 I miei documenti ← «Aggiungi un documento» (إضافة مستند).", "مستندات هوية رخصة جواز صورة انتهاء تجديد تنبيه خصوصية"),
    "g_archivio": ("الأرشيف: كل الملفات في مكان واحد",
        "يجمع الأرشيف كل الملفات التي حفظتها في التطبيق: صور المستندات والنشرات والتقارير والأدلة والفواتير. "
        "تبحث عنها بكتابة كلمة، تصفّيها حسب النوع أو الشخص، تفتحها أو تنزّلها أو ترسلها بالبريد الإلكتروني وواتساب. "
        "إذا كانت معلومة خاطئة تصحّحها، ويمكنك استبدال الملف بآخر أفضل. إنه كمصنّف كبير مرتّب، دائماً في جيبك.",
        "الزر البنفسجي 🗂️ Archivio ← خانة البحث في الأعلى.", "أرشيف ملفات بحث تصفية فتح تنزيل إرسال تصحيح مصنف"),
    "g_casa": ("المنزل: الأجهزة والأدلة والضمانات",
        "في المنزل تتابع أجهزة البيت: الغسالة والثلاجة والسخّان والتلفاز. لكل جهاز تحفظ الدليل والضمان والإيصال والفواتير. "
        "إذا حدثت مشكلة في الجهاز، تبحث عن كلمة داخل الدليل، مثلاً رمز الخطأ أو «تنظيف الفلتر»: يعرض لك التطبيق الصفحات الصحيحة مع تمييز الكلمات. "
        "إذا أردت، يشرحها لك بكلمات بسيطة. يمكنك أيضاً إرسال المستندات من البريد أو من تطبيقات المزوّدين.",
        "الزر البرتقالي 🏡 Casa ← تبويبا Beni (الممتلكات) وDocumenti ← على المستند «🔎 Cerca nel manuale».", "منزل ممتلكات أجهزة كهربائية دليل ضمان فاتورة إيصال بحث في الدليل خطأ اشرح لي"),
    "g_casa2": ("الصيانة وإدارة المنزل",
        "في المنزل تسجّل أيضاً أعمال الصيانة، مثل فحص السخّان، ويذكّرك التطبيق بالموعد التالي. "
        "في تبويب الإدارة تتابع مصاريف العمارة والأقساط مع تواريخ الدفع، وجهات اتصال السبّاك والكهربائي والمدير، "
        "وتقويم فرز النفايات مع جمع النفايات الكبيرة. يمكنك إرسال الإدارة كلها لمستخدم آخر بملف محمي بكلمة مرور.",
        "🏡 Casa ← تبويبا Manutenzioni وAmministrazione.", "صيانة سخان إدارة عمارة مصاريف أقساط دفع جهات اتصال سباك كهربائي فرز نفايات كبيرة تبادل"),
    "g_lavoro": ("العمل: كشوف الرواتب والمستندات",
        "في العمل تحمّل كشوف الرواتب، حتى بتصويرها: يقرأ التطبيق الأرقام ويرتّبها. "
        "سنة بعد سنة ترى الرسوم البيانية والمقارنة بين الأشهر. تحتفظ بالشهادة الضريبية السنوية (CU) ومستندات INPS. "
        "يوجد أيضاً دفتر عناوين النقابة وCAF وPatronato، مع الهاتف وساعات العمل، لتجدهم فوراً عند الحاجة.",
        "الزر الرمادي 💼 Lavoro ← التبويبات Buste paga وAnno per anno وCU وINPS وSindacato.", "عمل كشف راتب رسوم بيانية سنة شهادة cu inps نقابة caf patronato"),
    "g_auto": ("السيارة: المرآب والمواعيد",
        "في السيارة يوجد مرآبك: لكل مركبة بطاقتها. يمكنك تصوير رخصة السير فيقرأ التطبيق اللوحة والماركة والطراز. "
        "يذكّرك بالضريبة والتأمين والفحص الفني قبل انتهائها. تسجّل الصيانة والتزوّد بالوقود والمصاريف، فتعرف كم تكلّفك السيارة. "
        "توجد أيضاً رخصة القيادة مع النقاط والمخالفات، والرحلات مع تعويضات الكيلومترات.",
        "الزر السماوي 🚗 Auto ← المرآب ← اضغط مركبة ← Scadenze وManutenzione وRifornimenti.", "سيارة مركبة مرآب لوحة رخصة سير ضريبة تأمين فحص فني صيانة وقود مصاريف رخصة قيادة مخالفات رحلات"),
    "g_auto2": ("السيارة: لمبات التحذير والتشخيص والطوارئ",
        "إذا أضاءت لمبة تحذير في لوحة القيادة، صوّرها: يخبرك التطبيق بمعناها وهل يمكنك متابعة القيادة. "
        "في التشخيص تجد رموز الأعطال، ومع جهاز صغير يوصَل بالسيارة، بيانات المحرك أيضاً. "
        "في الطوارئ لديك الأرقام المفيدة والمساعدة على الطريق ونموذج الحادث، مع الخطوات التي تتبعها بهدوء إذا تعرّضت لحادث.",
        "🚗 Auto ← Diagnostica ← «📷 Fotografa una spia»؛ 🚗 Auto ← Emergenza.", "لمبة تحذير لوحة قيادة تشخيص رموز أعطال obd طوارئ مساعدة طريق حادث نموذج"),
    "g_chat": ("دردشة العائلة",
        "بالدردشة تكتب لأفراد العائلة دون الخروج من التطبيق، مجاناً. في الأعلى تختار مع من تتحدث: الجميع («Tutti»)، أي مجموعة العائلة، أو شخص واحد فقط، على انفراد. "
        "تختار من تبقيه ظاهراً كزر؛ الأشخاص الآخرون يبقون في قائمة «Altre persone» (أشخاص آخرون). "
        "رسائلك على اليمين باللون الأخضر، ورسائل الآخرين على اليسار باللون الأبيض. نقطة حمراء مع رقم تخبرك كم رسالة جديدة لديك.",
        "الزر 💬 Chat في الأعلى ← اختر الشخص ← اكتب في الأسفل ← 📨 Invia (إرسال).", "دردشة رسائل عائلة كتابة الجميع خاص أشخاص ظاهرون أشخاص آخرون رسائل جديدة"),
    "g_utilita": ("الأدوات",
        "في الأدوات توجد أدوات الخدمة. سلة المهملات، حيث تبقى الأشياء المحذوفة ثلاثين يوماً. مظهر التطبيق، لنصوص أكبر. "
        "تبادل البيانات، لإرسال بياناتك لشخص آخر أو استقبالها. تحرير المساحة، لإزالة الملفات غير المفيدة من الهاتف. "
        "والتطبيقات المفيدة، مثل Wimbi وVelocity Music، مع نشرتها التي تشرح ما تفعله.",
        "الزر البنفسجي 🧰 Utilità، الأخير في الصف العلوي.", "أدوات سلة مظهر نصوص كبيرة تبادل بيانات تحرير مساحة wimbi velocity تطبيقات مفيدة"),
    "g_avvisi": ("كيف تصل التنبيهات",
        "ينبّهك التطبيق قبل المواعيد وفي وقت العلاجات. تصل التنبيهات على تيليغرام أو بالبريد الإلكتروني أو على واتساب أو كمنبّه في تقويم الهاتف: أنت تختار أيّها. "
        "تيليغرام والبريد الإلكتروني مجانيان وآمنان؛ يكفي إعدادهما مرة واحدة. داخل الصحة يوجد زر لإرسال رسالة تجريبية، لتتأكد أن كل شيء يعمل. "
        "في التطبيق، يُظهر لك الجرس مع الرقم على الأزرار العلوية الأشياء التي يجب رؤيتها.",
        "🩺 Salute ← القائمة المنسدلة «🔔 Avvisi» ← اختر القنوات واضغط «Messaggio di prova» (رسالة تجريبية).", "تنبيهات إشعارات تذكيرات تيليغرام بريد واتساب تقويم جرس رسالة تجريبية إعداد"),
    "g_cestino": ("أخطأت: سلة المهملات",
        "لا تخف من الخطأ. عندما تحذف شيئاً، يظهر لبضع ثوانٍ في أعلى الصفحة زر التراجع: اضغطه فيعود كل شيء كما كان. "
        "إذا انتبهت لاحقاً، افتح سلة المهملات في الأدوات: تبقى الأشياء المحذوفة هناك ثلاثين يوماً وبزر الاستعادة تعود إلى مكانها. "
        "أنت وحدك تقرر حذفها نهائياً.",
        "🧰 Utilità ← 🗑️ Cestino ← ↩️ Ripristina (استعادة).", "خطأ حذف بالخطأ تراجع سلة استعادة استرجاع ثلاثون يوما"),
    "g_aiuto": ("المساعدة دائماً في متناول اليد",
        "إذا لم تتذكر كيف تفعل شيئاً، لديك ثلاث مساعدات. الزر الأحمر «Clicca per informazioni» في الأعلى، مع دليل كل صفحة وخانة للبحث. "
        "أنا، الروبوت الصغير: المسني فأشرح لك الصفحة التي أنت فيها، أو اكتب لي أو قل لي سؤالاً بالميكروفون. "
        "والجديد، حيث أخبرك بما هو جديد. يمكنك جعل صوتي أبطأ أو أسرع، أو تغيير اللغة، أو إطفائي: تعيد تشغيلي من الزر الأحمر.",
        "الروبوت الصغير في الأسفل على اليمين؛ الزر الأحمر في أعلى كل صفحة.", "مساعدة دليل معلومات سؤال ميكروفون صوت بطيء سريع جديد إطفاء مساعد"),
    "g_fine": ("نهاية الجولة",
        "انتهت الجولة، أحسنت! الآن تعرف كل أجزاء التطبيق. لست مضطراً لتذكّر كل شيء: كلما احتجت، المسني واسألني. "
        "ابدأ بالأشياء التي تستخدمها أكثر، مثلاً المخزن أو أدوية العائلة، واكتشف الباقي بهدوء. بالتوفيق!",
        "", "نهاية جولة انتهت شكرا إعادة"),
}
AG_UI["ar"] = {
    "a_giro": "🧭 الجولة الكاملة في التطبيق", "a_giro_dlg": "🧭 خذني في الجولة الكاملة في التطبيق (يرويها الروبوت بصوت عالٍ)",
    "a_capitoli": "📑 الفصول", "a_pausa": "⏸ إيقاف مؤقت", "a_riprendi": "▶ متابعة", "a_dove": "أين يوجد:",
    "a_lingua": "🌐 اللغة", "a_lingua_t": "بأي لغة تريدني أن أتحدث؟", "a_lingua_x": "اختر في الأسفل. لغة التطبيق لا تتغير: يتغير صوتي والجولة والإجابات.",
    "a_lingua_ok": "ممتاز، من الآن أتحدث العربية.", "a_cap_t": "فصول الجولة", "a_cap_x": "اضغط فصلاً للانتقال إليه مباشرة.",
    "a_primo_t": "مرحباً! هذه أول مرة تفتحني", "a_primo_x": "هل تريد الجولة الكاملة في التطبيق؟ تستغرق بضع دقائق ويمكنك إيقافي متى شئت. اضغط الزر الأصفر في الأسفل، أو «خذني في الجولة».",
    "a_primo_btn": "🧭 خذني في الجولة", "a_fine_t": "نهاية الجولة", "a_fine_x": "تم! إذا احتجت شيئاً آخر، اسألني.",
    "a_vel": "🐢 سرعة الصوت", "a_vel_0": "بطيئة", "a_vel_1": "عادية", "a_vel_2": "سريعة", "a_vel_prova": "هذا صوتي بالسرعة الجديدة.",
    "a_trov_t": "لا أجد تعليمات عن هذا", "a_trov_x": "لا أريد أن أدلّك على إجراء قد لا يعمل: ربما هذه الوظيفة غير موجودة في التطبيق، أو أستخدم كلمات مختلفة عن كلماتك. جرّب كلمات أخرى (حتى كلمة واحدة: صورة، انتهاء، كلمة مرور) أو اختر موضوعاً في الأسفل.",
}

# =====================================================================================================================
AG_TR["pt"] = {
    "g_benvenuto": ("Bem-vindo! Sou o teu assistente",
        "Olá! Sou o robô da aplicação «La nostra dispensa» (A nossa despensa). Agora faço-te a visita completa: explico-te todas as partes da aplicação, uma de cada vez, com palavras simples. "
        "Se a voz estiver ligada, avanço sozinho: toca em Pausa para me parares, Seguinte ou Anterior para te moveres, Capítulos para saltares para onde quiseres. "
        "Podes fazer-me uma pergunta quando quiseres, escrevendo-a ou com o microfone. Com o botão do globo mudas a minha língua.",
        "", "bem-vindo início visita completa robô assistente língua pausa seguinte capítulos"),
    "g_entrare": ("Entrar na aplicação",
        "Cada pessoa da família tem a sua palavra-passe. Quando entras vês só as tuas coisas: os teus produtos, os teus medicamentos, os teus documentos. "
        "Mais ninguém os vê, a não ser o que decidires partilhar. No primeiro ecrã podes escolher a língua da aplicação. "
        "Em cima à esquerda há uma seta com duas pontas: abre o menu lateral, onde encontras as tuas alergias, a língua e outras definições.",
        "Primeiro ecrã: escreve a palavra-passe e toca em Entrar («Entra»).", "entrar palavra-passe senha língua menu lateral seta alergias acesso"),
    "g_home": ("A página inicial e os botões das secções",
        "Em cima, em cada página, há uma fila de botões coloridos: Despensa («Dispensa»), Saúde («Salute»), Os meus documentos, Arquivo, Casa, Trabalho («Lavoro»), Carro («Auto»), Chat e Utilidades («Utilità»). "
        "Desliza a fila com o dedo para veres os últimos. Tocas num botão e entras nessa parte da aplicação. "
        "Se num botão aparecer um sino com um número, ali há algo para ver: um prazo próximo ou uma mensagem nova. "
        "Debaixo dos botões encontras sempre o botão vermelho «Clicca per informazioni» (Toca para informações) com o guia.",
        "A fila de botões coloridos em cima, em cada página.", "início botões secções barra sino número avisos cores navegar"),
    "g_dispensa": ("A Despensa: produtos e validades",
        "A Despensa é a lista do que tens em casa para comer e beber. Toca em Adicionar, tira a foto do produto ou escreve o código de barras, e a aplicação preenche o nome. "
        "Depois escreve quantas unidades tens e a data de validade. As cores dizem-te quando agir: verde tudo bem, laranja expira dentro de dois meses, vermelho dentro de um mês, escuro já expirou. "
        "Há três partes: Adultos, Bebés e Animais, para saberes logo para quem é cada produto.",
        "Botão verde 🏠 Dispensa → em baixo os separadores Despensa, Adicionar, Gerir, Compras.", "despensa produtos validade adicionar foto código de barras cores verde laranja vermelho bebés animais"),
    "g_dispensa2": ("Alergias, lista de compras e estatísticas",
        "No menu lateral escolhe as tuas alergias: os produtos perigosos para ti mostram uma sirene, assim reconhece-los logo. "
        "Quando um produto acaba, toca em «Consumi-o» e vai sozinho para a Lista de compras, que podes levar ao supermercado. "
        "Com Gerir mudas quantidades e validades de muitos produtos de uma vez. As Estatísticas mostram-te quanto deitaste fora, para desperdiçares menos. "
        "Há também a Despensa da família, para as coisas em comum.",
        "🏠 Dispensa → separadores Compras («Spesa») e Gerir («Gestisci»); alergias no menu lateral (seta em cima à esquerda).", "alergias alergénios sirene lista compras consumido gerir estatísticas desperdício família"),
    "g_salute": ("Saúde: as pessoas e os medicamentos",
        "Na Saúde cuidas da saúde de toda a família. Primeiro escolhe a pessoa: tu, a mãe, os filhos. Cada um tem o seu perfil com grupo sanguíneo e alergias a medicamentos. "
        "Depois adiciona os medicamentos com a validade: podes fotografar a caixa. Para cada medicamento podes ler o folheto com palavras simples. "
        "A aplicação conta o stock: quando um medicamento está a acabar avisa-te e prepara o pedido de receita para a médica.",
        "Botão vermelho 🩺 Salute → escolhe a pessoa em cima → separador Medicamentos («Medicinali»).", "saúde pessoa perfil mãe medicamentos validade folheto stock receita médica grupo sanguíneo"),
    "g_terapie": ("Tratamentos e lembretes",
        "Um tratamento é um medicamento para tomar com regularidade: todos os dias a certa hora, ou de vez em quando, por exemplo uma ampola a cada quinze dias. "
        "A aplicação lembra-te de quando o tomar: com uma mensagem no Telegram, por e-mail ou no WhatsApp. "
        "Também podes descarregar os alarmes para o Calendário do telemóvel: assim o alarme toca à hora certa, mesmo sem abrir a aplicação. "
        "Para cada tratamento escreve medicamento, dose, hora e quanto dura.",
        "🩺 Salute → separador Tratamentos («Terapie») → ➕ Novo tratamento; alarmes em «📅 Allarmi sul Calendario del telefono».", "tratamento terapia lembrete aviso hora dose telegram e-mail whatsapp calendário alarme todos os dias intervalos"),
    "g_visite": ("Consultas, vacinas, médico e cartão de saúde",
        "Na Saúde anotas também as consultas e os exames, com data e hora: podes fotografar a folha da marcação e a aplicação lê a data sozinha. "
        "Depois da consulta guardas o relatório. Há as vacinas com os reforços, a ficha do teu médico e o cartão de saúde, com as ligações ao processo clínico. "
        "Com um toque preparas um resumo completo de uma pessoa, para mostrar ao médico ou enviar por e-mail.",
        "🩺 Salute → separadores Consultas («Visite») e Vacinas («Vaccini»); crachá azul do cartão de saúde ao lado da médica.", "consultas exames relatório marcação vacinas reforços médico cartão de saúde processo resumo"),
    "g_documenti": ("Os meus documentos",
        "Aqui guardas os documentos pessoais: cartão de cidadão, carta de condução, passaporte, cartão de saúde, autorização de residência. "
        "Tira a foto ao documento: a aplicação retira o fundo, endireita-o e tenta ler o tipo, o número e a validade. Podes sempre corrigir à mão. "
        "Seis meses e três meses antes da validade a aplicação avisa-te, para renovares a tempo. Os documentos são só teus: mais ninguém os vê.",
        "Botão azul 📁 I miei documenti → «Aggiungi un documento» (Adicionar um documento).", "documentos cartão cidadão carta condução passaporte foto validade renovação aviso privacidade"),
    "g_archivio": ("O Arquivo: todos os ficheiros num só lugar",
        "O Arquivo reúne todos os ficheiros que guardaste na aplicação: fotos de documentos, folhetos, relatórios, manuais, faturas. "
        "Procura-los escrevendo uma palavra, filtra-los por tipo ou por pessoa, abre-los, descarrega-los ou envia-los por e-mail e WhatsApp. "
        "Se um dado estiver errado corrige-lo, e podes substituir o ficheiro por um melhor. É como um grande dossiê arrumado, sempre no bolso.",
        "Botão roxo 🗂️ Archivio → caixa de pesquisa em cima.", "arquivo ficheiros procurar filtrar abrir descarregar enviar corrigir dossiê"),
    "g_casa": ("Casa: aparelhos, manuais e garantias",
        "Na Casa guardas os aparelhos da casa: máquina de lavar, frigorífico, caldeira, televisão. Para cada um guardas o manual, a garantia, o talão e as faturas. "
        "Se o aparelho der um problema, procuras uma palavra dentro do manual, por exemplo o código do erro ou «limpeza do filtro»: a aplicação mostra-te as páginas certas com as palavras realçadas. "
        "Se quiseres, explica-tas com palavras simples. Também podes enviar documentos do e-mail ou das aplicações dos fornecedores.",
        "Botão laranja 🏡 Casa → separadores Beni (bens) e Documenti → no documento «🔎 Cerca nel manuale».", "casa bens aparelhos eletrodomésticos manual garantia fatura talão procurar no manual erro explica-me"),
    "g_casa2": ("Manutenções e Administração da casa",
        "Na Casa registas também as manutenções, como a revisão da caldeira, e a aplicação lembra-te da próxima. "
        "No separador Administração guardas as despesas do condomínio e as prestações com as datas de pagamento, os contactos do canalizador, do eletricista e do administrador, "
        "e o calendário da reciclagem com a recolha de monos. Podes enviar toda a Administração a outro utilizador com um ficheiro protegido por palavra-passe.",
        "🏡 Casa → separadores Manutenzioni e Amministrazione.", "manutenção caldeira administração condomínio despesas prestações pagamentos contactos canalizador eletricista reciclagem monos troca"),
    "g_lavoro": ("Trabalho: recibos de vencimento e documentos",
        "No Trabalho carregas os recibos de vencimento, mesmo fotografando-os: a aplicação lê os números e põe-nos em ordem. "
        "Ano a ano vês os gráficos e a comparação entre os meses. Guardas a declaração fiscal anual (CU) e os documentos do INPS. "
        "Há também a agenda do sindicato, do CAF e do patronato, com telefone e horários, para os encontrares logo quando forem precisos.",
        "Botão cinzento 💼 Lavoro → separadores Buste paga, Anno per anno, CU, INPS, Sindacato.", "trabalho recibo vencimento salário gráficos ano declaração cu inps sindicato caf patronato"),
    "g_auto": ("Carro: a garagem e os prazos",
        "No Carro está a tua garagem: cada veículo tem a sua ficha. Podes fotografar o documento único e a aplicação lê matrícula, marca e modelo. "
        "Lembra-te do imposto, do seguro e da inspeção antes de expirarem. Registas manutenções, abastecimentos e despesas, assim sabes quanto te custa o carro. "
        "Há também a carta de condução com os pontos e as multas, e as viagens com os reembolsos por quilómetro.",
        "Botão azul-claro 🚗 Auto → a garagem → toca num veículo → Scadenze, Manutenzione, Rifornimenti.", "carro veículo garagem matrícula livrete imposto seguro inspeção manutenção abastecimento despesas carta multas viagens"),
    "g_auto2": ("Carro: luzes de aviso, diagnóstico e emergência",
        "Se no painel se acender uma luz de aviso, fotografa-a: a aplicação diz-te o que significa e se podes continuar a conduzir. "
        "No Diagnóstico encontras os códigos de erro e, com um pequeno aparelho para ligar ao carro, também os dados do motor. "
        "Na Emergência tens os números úteis, a assistência em viagem e a declaração de acidente, com os passos a seguir com calma se tiveres um acidente.",
        "🚗 Auto → Diagnostica → «📷 Fotografa una spia»; 🚗 Auto → Emergenza.", "luz aviso painel diagnóstico códigos erro obd emergência assistência viagem acidente declaração"),
    "g_chat": ("O Chat da família",
        "Com o Chat escreves às pessoas da família sem sair da aplicação, grátis. Em cima escolhes com quem falar: Todos («Tutti»), ou seja o grupo da família, ou uma só pessoa, em privado. "
        "Escolhes quem manter à vista como botão; as outras pessoas ficam no menu «Altre persone» (Outras pessoas). "
        "As tuas mensagens estão à direita a verde, as dos outros à esquerda a branco. Um ponto vermelho com o número diz-te quantas mensagens novas tens.",
        "Botão 💬 Chat em cima → escolhe a pessoa → escreve em baixo → 📨 Invia (Enviar).", "chat mensagens família escrever todos privado pessoas à vista outras pessoas mensagens novas"),
    "g_utilita": ("As Utilidades",
        "Nas Utilidades estão as ferramentas de serviço. A Reciclagem, onde as coisas eliminadas ficam trinta dias. O Aspeto da aplicação, para teres textos maiores. "
        "A Troca de dados, para enviares os teus dados a outra pessoa ou recebê-los. Libertar espaço, para tirares os ficheiros inúteis do telemóvel. "
        "E as aplicações úteis, como o Wimbi e o Velocity Music, com o seu folheto que explica o que fazem.",
        "Botão roxo 🧰 Utilità, o último da fila de cima.", "utilidades reciclagem lixo aspeto textos grandes troca dados libertar espaço wimbi velocity aplicações úteis"),
    "g_avvisi": ("Como chegam os avisos",
        "A aplicação avisa-te antes dos prazos e à hora dos tratamentos. Os avisos chegam no Telegram, por e-mail, no WhatsApp ou como alarme no Calendário do telemóvel: escolhes tu quais. "
        "O Telegram e o e-mail são gratuitos e seguros; basta configurá-los uma vez. Dentro da Saúde há o botão para enviar uma mensagem de teste, assim confirmas que tudo funciona. "
        "Na aplicação, o sino com o número nos botões de cima mostra-te as coisas para ver.",
        "🩺 Salute → lista «🔔 Avvisi» → escolhe os canais e toca em «Messaggio di prova» (mensagem de teste).", "avisos notificações lembretes telegram e-mail whatsapp calendário sino mensagem de teste configurar"),
    "g_cestino": ("Enganei-me: a Reciclagem",
        "Não tenhas medo de te enganar. Quando eliminas algo, no cimo da página aparece durante alguns segundos o botão Anular: toca-lhe e tudo volta a ser como antes. "
        "Se reparares mais tarde, abre a Reciclagem nas Utilidades: as coisas eliminadas ficam lá trinta dias e com Repor voltam ao seu lugar. "
        "Só tu podes decidir eliminá-las para sempre.",
        "🧰 Utilità → 🗑️ Cestino → ↩️ Ripristina (Repor).", "enganei erro eliminado por engano anular reciclagem lixo repor recuperar trinta dias"),
    "g_aiuto": ("Ajuda sempre à mão",
        "Se não te lembrares de como se faz uma coisa, tens três ajudas. O botão vermelho «Clicca per informazioni» em cima, com o guia de cada página e uma caixa para pesquisar. "
        "Eu, o robô: toca-me e explico-te a página em que estás, ou escreve-me ou diz-me uma pergunta com o microfone. "
        "E as Novidades, onde te conto o que há de novo. Podes tornar a minha voz mais lenta ou mais rápida, mudar de língua ou desligar-me: voltas a ligar-me no botão vermelho.",
        "O robô em baixo à direita; o botão vermelho em cima em cada página.", "ajuda guia informações pergunta microfone voz lenta rápida novidades desligar assistente"),
    "g_fine": ("Fim da visita",
        "A visita terminou, muito bem! Agora conheces todas as partes da aplicação. Não tens de te lembrar de tudo: sempre que precisares, toca-me e pergunta-me. "
        "Começa pelas coisas que mais usas, por exemplo a Despensa ou os medicamentos da família, e descobre o resto com calma. Bom trabalho!",
        "", "fim visita terminada obrigado recomeçar"),
}
# il portoghese NON è una lingua dell'app: il robottino ha bisogno di tutte le sue scritte
AG_UI["pt"] = {
    "a_aria": "Assistente digital", "a_rileggi": "📖 Explica-me esta página", "a_giro": "🧭 Visita completa da aplicação",
    "a_giro_dlg": "🧭 Faz-me a visita completa da aplicação (o robô conta-a em voz alta)",
    "a_novita": "🆕 O que há de novo", "a_mic": "🎤 Faz uma pergunta", "a_indietro": "◀ Anterior", "a_avanti": "Seguinte ▶", "a_fine": "Fim",
    "a_ph": "Escreve aqui a tua pergunta…", "a_chiedi": "Perguntar", "a_voce_on": "🔊 Voz: ligada", "a_voce_off": "🔇 Voz: desligada",
    "a_silenzio": "⏹ Silêncio", "a_off": "⛔ Desligar assistente", "a_ascolto_btn": "⏹ Estou a ouvir…",
    "a_ascolto_t": "Estou a ouvir-te", "a_ascolto_x": "Fala agora: por exemplo «como adiciono uma foto ao documento?»",
    "a_mic_t": "Microfone", "a_mic_no": "Neste telemóvel não consigo ouvir-te: escreve a pergunta aqui em baixo.",
    "a_mic_perm": "Permite ao navegador usar o microfone para falares comigo.",
    "a_mic_err": "Agora não consigo usar a voz: escreve a pergunta aqui em baixo.",
    "a_nulla_t": "Não ouvi nada", "a_nulla_x": "Tenta outra vez: toca no microfone e fala.",
    "a_dimmi_t": "Diz-me", "a_dimmi_x": "Escreve ou diz o que queres saber.",
    "a_off_t": "Queres que me desligue?",
    "a_off_x": "Toca no botão «⛔ Desligar assistente» aqui em baixo. Voltas a ligar-me no botão vermelho «Clicca per informazioni».",
    "a_trov_t": "Não encontro instruções sobre isto",
    "a_trov_x": "Não quero indicar-te um procedimento que pode não funcionar: talvez esta função não exista na aplicação, ou eu use palavras diferentes das tuas. Tenta outras palavras (mesmo uma só: foto, validade, palavra-passe) ou escolhe um tema aqui em baixo.",
    "a_nov_none_t": "Novidades", "a_nov_none_x": "Por agora não há novidades recentes. Eu aviso-te quando chegarem!",
    "a_nov_voce": "Aqui estão as novidades.", "a_nov_trovi": "Encontra-la assim:", "a_nov_t": "O que há de novo",
    "a_fine_t": "Fim da visita", "a_fine_x": "Pronto! Se precisares de mais alguma coisa, pergunta-me.",
    "a_toast_off": "Assistente desligado. Voltas a ligá-lo em «Clicca per informazioni».", "a_toast_on": "Assistente ativo: toca no robô.",
    "a_vedi": "Toca num tema aqui em baixo para saberes mais.",
    "a_vel": "🐢 Velocidade da voz", "a_vel_0": "lenta", "a_vel_1": "normal", "a_vel_2": "rápida", "a_vel_prova": "Esta é a minha voz com a nova velocidade.",
    "a_capitoli": "📑 Capítulos", "a_pausa": "⏸ Pausa", "a_riprendi": "▶ Continuar", "a_dove": "Onde está:",
    "a_lingua": "🌐 Língua", "a_lingua_t": "Em que língua queres que fale?", "a_lingua_x": "Escolhe aqui em baixo. A língua da aplicação não muda: mudam a minha voz, a visita e as respostas.",
    "a_lingua_ok": "Perfeito, a partir de agora falo português.", "a_cap_t": "Os capítulos da visita", "a_cap_x": "Toca num capítulo para ires diretamente para lá.",
    "a_primo_t": "Olá! É a primeira vez que me abres", "a_primo_x": "Queres que te faça a visita completa da aplicação? Dura poucos minutos e podes parar-me quando quiseres. Toca no botão amarelo aqui em baixo, ou em «Faz-me a visita».",
    "a_primo_btn": "🧭 Faz-me a visita",
    "i_silenzio": "silêncio silencio cala basta para", "i_off": "desliga desativa apaga", "i_ass": "assistente robô robo",
    "i_novita": "novidade novidades novo novos atualizaç", "i_giro": "visita tutorial guia começa comeca", "i_saluto": "olá ola bom dia boa tarde boa noite ajuda",
}

# ---------------------------------------------------------------------------------------------------------------------
# le scritte nuove entrano anche nella guida (UI_TR), così «_u()» le trova nella lingua dell'app (per il pulsante nella finestra Info)
# ---------------------------------------------------------------------------------------------------------------------
try:
    for _ag_lg, _ag_d in AG_UI.items():
        UI_TR.setdefault(_ag_lg, {}).update(_ag_d)
except NameError:
    pass
