# -*- coding: utf-8 -*-
"""Ricerca delle FARMACIE APERTE e dei VOLANTINI per Paese.
L'app parte dal Paese della lingua scelta (italiano → Italia, Torino; spagnolo → Spagna, Barcellona; inglese → Regno Unito,
Londra; francese → Francia, Parigi; tedesco → Germania, Berlino; rumeno → Romania, Bucarest; arabo → Egitto, Il Cairo) ma
si può cambiare Paese e scrivere qualunque città o codice postale di quel Paese.
PER AGGIUNGERE UN PAESE: aggiungi una voce a PAESI qui sotto (nome, nome inglese, codice, fuso orario, città di partenza,
parole per la ricerca su Google, siti dei volantini, catene di negozi).
Caricato da app_dispensa.py dopo info_sezioni.py; usato da farmacia.py e volantini.py."""
import re

import streamlit as st

PAESE_LINGUA = {"it": "IT", "en": "GB", "es": "ES", "fr": "FR", "de": "DE", "ro": "RO", "ar": "EG"}

PAESI = {
    "IT": {"farmacia": "farmacia", "bandiera": "🇮🇹", "nome": "Italia", "q": "Italy", "cc": "it", "tz": "Europe/Rome", "citta": "Torino", "cap": r"\d{5}",
           "turno": "farmacie di turno", "offerta": "offerta volantino", "tutti": "volantini supermercati",
           "siti": [("DoveConviene", "doveconviene.it"), ("PromoQui", "promoqui.it"), ("Volantinofacile", "volantinofacile.it"),
                    ("Tiendeo", "tiendeo.it")],
           "catene": None},
    "ES": {"farmacia": "farmacia", "bandiera": "🇪🇸", "nome": "España", "q": "Spain", "cc": "es", "tz": "Europe/Madrid", "citta": "Barcelona", "cap": r"\d{5}",
           "turno": "farmacias de guardia", "offerta": "oferta folleto", "tutti": "folletos supermercados",
           "siti": [("Tiendeo", "tiendeo.es"), ("Ofertia", "ofertia.com")],
           "catene": {"Supermercato": ["Mercadona", "Dia", "Eroski", "Consum", "Caprabo", "BonPreu", "Condis", "Ahorramás", "Supercor"],
                      "Ipermercato": ["Carrefour", "Alcampo", "Hipercor", "E.Leclerc"],
                      "Discount": ["Lidl", "Aldi", "Dia Maxi"]}},
    "GB": {"farmacia": "pharmacy", "bandiera": "🇬🇧", "nome": "United Kingdom", "q": "United Kingdom", "cc": "gb", "tz": "Europe/London", "citta": "London",
           "cap": r"[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}",
           "turno": "late night pharmacy open now", "offerta": "offer leaflet", "tutti": "supermarket leaflets",
           "siti": [("Tiendeo", "tiendeo.co.uk"), ("MySupermarket", "mysupermarket.co.uk")],
           "catene": {"Supermercato": ["Tesco", "Sainsbury's", "Asda", "Morrisons", "Waitrose", "Co-op", "M&S Food", "Iceland"],
                      "Ipermercato": ["Tesco Extra", "Asda Superstore", "Sainsbury's Superstore"],
                      "Discount": ["Aldi", "Lidl", "Farmfoods", "B&M"]}},
    "FR": {"farmacia": "pharmacie", "bandiera": "🇫🇷", "nome": "France", "q": "France", "cc": "fr", "tz": "Europe/Paris", "citta": "Paris", "cap": r"\d{5}",
           "turno": "pharmacie de garde", "offerta": "promo prospectus", "tutti": "catalogues supermarchés",
           "siti": [("Tiendeo", "tiendeo.fr"), ("Bonial", "bonial.fr"), ("PromoCatalogues", "promocatalogues.com")],
           "catene": {"Supermercato": ["Carrefour Market", "Intermarché", "Monoprix", "Casino", "Franprix", "Super U", "Match"],
                      "Ipermercato": ["Carrefour", "E.Leclerc", "Auchan", "Hyper U", "Cora", "Géant Casino"],
                      "Discount": ["Lidl", "Aldi", "Netto", "Leader Price"]}},
    "DE": {"farmacia": "Apotheke", "bandiera": "🇩🇪", "nome": "Deutschland", "q": "Germany", "cc": "de", "tz": "Europe/Berlin", "citta": "Berlin", "cap": r"\d{5}",
           "turno": "Notdienst Apotheke", "offerta": "Angebot Prospekt", "tutti": "Supermarkt Prospekte",
           "siti": [("Kaufda", "kaufda.de"), ("Marktjagd", "marktjagd.de"), ("Tiendeo", "tiendeo.de")],
           "catene": {"Supermercato": ["Edeka", "Rewe", "Tegut", "Nahkauf"],
                      "Ipermercato": ["Kaufland", "Real", "Globus", "Marktkauf"],
                      "Discount": ["Aldi", "Lidl", "Penny", "Netto"]}},
    "RO": {"farmacia": "farmacie", "bandiera": "🇷🇴", "nome": "România", "q": "Romania", "cc": "ro", "tz": "Europe/Bucharest", "citta": "București", "cap": r"\d{6}",
           "turno": "farmacie de gardă non-stop", "offerta": "ofertă catalog", "tutti": "cataloage supermarketuri",
           "siti": [("Tiendeo", "tiendeo.ro")],
           "catene": {"Supermercato": ["Mega Image", "Profi", "Carrefour Market", "Annabella"],
                      "Ipermercato": ["Kaufland", "Carrefour", "Auchan", "Selgros", "Cora"],
                      "Discount": ["Lidl", "Penny", "Aldi"]}},
    "EG": {"farmacia": "صيدلية", "bandiera": "🇪🇬", "nome": "مصر", "q": "Egypt", "cc": "eg", "tz": "Africa/Cairo", "citta": "القاهرة", "cap": None,
           "turno": "صيدلية مناوبة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Spinneys", "Metro", "Seoudi", "Fathalla"], "Ipermercato": ["Carrefour", "Hyperone", "Lulu"],
                      "Discount": ["Kazyon", "Oscar"]}},
    "MA": {"farmacia": "صيدلية", "bandiera": "🇲🇦", "nome": "المغرب", "q": "Morocco", "cc": "ma", "tz": "Africa/Casablanca", "citta": "الدار البيضاء", "cap": None,
           "turno": "صيدلية الحراسة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Marjane", "Carrefour Market", "Acima"], "Ipermercato": ["Marjane", "Carrefour", "Aswak Assalam"],
                      "Discount": ["Label'Vie"]}},
    "SA": {"farmacia": "صيدلية", "bandiera": "🇸🇦", "nome": "السعودية", "q": "Saudi Arabia", "cc": "sa", "tz": "Asia/Riyadh", "citta": "الرياض", "cap": None,
           "turno": "صيدلية 24 ساعة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Panda", "Othaim", "Tamimi", "Danube"], "Ipermercato": ["Hyper Panda", "Lulu", "Carrefour"],
                      "Discount": ["Al Raya", "Bin Dawood"]}},
    "AE": {"farmacia": "صيدلية", "bandiera": "🇦🇪", "nome": "الإمارات", "q": "United Arab Emirates", "cc": "ae", "tz": "Asia/Dubai", "citta": "دبي", "cap": None,
           "turno": "صيدلية 24 ساعة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Spinneys", "Waitrose", "Choithrams", "Union Coop"], "Ipermercato": ["Carrefour", "Lulu", "Géant"],
                      "Discount": ["Al Maya", "Nesto"]}},
}

# ---------------------------------------------------------------------------------------------------------------------
# I testi (nella lingua scelta). Chi manca in una lingua si vede in italiano.
# ---------------------------------------------------------------------------------------------------------------------
RP_TR = {
    "it": {
        "f_btn": "🔎 Trova una farmacia aperta", "f_titolo": "Trova una farmacia aperta", "paese": "🌍 Paese",
        "dove": "Città, comune o codice postale (CAP)", "dove_ph": "es. {citta}", "cerca": "Cerca",
        "err_vuoto": "Scrivi il nome di una città o un codice postale.",
        "err_non_trovo": "Non trovo questo posto in {paese}. Controlla come l'hai scritto oppure cambia Paese.",
        "err_rete": "Non riesco a collegarmi al servizio delle mappe in questo momento. Riprova tra poco.",
        "scrivi": "Scrivi la città o il codice postale e tocca Cerca.", "solo_aperte": "Mostra solo quelle che risultano aperte adesso",
        "vicino": "Ricerca vicino a: {luogo} · alle {ora} del {data}",
        "nessuna": "Non ho trovato farmacie vicino a questo posto. Prova con un altro codice postale o con il nome del comune.",
        "nessuna_aperta": "Nessuna farmacia risulta aperta adesso secondo gli orari disponibili. Controlla anche quelle con orari non verificabili e quelle di turno.",
        "aperta": "Risulta aperta adesso", "chiusa": "Risulta chiusa adesso", "ignoto": "Orari non verificabili: chiama prima",
        "oggi": "oggi {orari}", "chiusa_oggi": "chiusa oggi", "portami": "🧭 Portami lì", "chiama": "📞 Chiama",
        "turno_btn": "🌙 Cerca le farmacie di turno (notte e festivi)",
        "osm": "ℹ️ Posizioni e orari arrivano da OpenStreetMap, una mappa aperta aggiornata da volontari: possono essere incompleti o non aggiornati. Nei giorni festivi e di notte gli orari normali non valgono. L'app non può sapere quali farmacie sono di turno: usa il pulsante qui sopra o telefona per esserne sicuro.",
        "v_titolo": "🏷️ Offerte nei volantini", "v_citta": "📍 Città", "v_cerca_h": "**1️⃣ Cerca nei volantini**",
        "v_cap": "Non esiste un archivio pubblico dei volantini da controllare in automatico: questi pulsanti aprono la ricerca nei siti dei volantini del tuo Paese, già compilata con prodotto e città.",
        "v_scrivi_citta": "Scrivi la città per cercare le offerte della tua zona.",
        "v_cerca_btn": "🔎 Cerca nei volantini di {citta}", "v_tutti": "🛒 Tutti i volantini dei supermercati a {citta}",
        "v_tipo_Supermercato": "Supermercato", "v_tipo_Ipermercato": "Ipermercato", "v_tipo_Discount": "Discount",
    },
    "en": {
        "f_btn": "🔎 Find an open pharmacy", "f_titolo": "Find an open pharmacy", "paese": "🌍 Country",
        "dove": "City, town or postcode", "dove_ph": "e.g. {citta}", "cerca": "Search",
        "err_vuoto": "Write the name of a city or a postcode.",
        "err_non_trovo": "I cannot find this place in {paese}. Check how you wrote it or change the country.",
        "err_rete": "I cannot connect to the map service right now. Try again in a moment.",
        "scrivi": "Write the city or postcode and tap Search.", "solo_aperte": "Show only those that appear open now",
        "vicino": "Search near: {luogo} · at {ora} on {data}",
        "nessuna": "I did not find pharmacies near this place. Try another postcode or the name of the town.",
        "nessuna_aperta": "No pharmacy appears open now according to the available hours. Also check those with unverifiable hours and the on-duty ones.",
        "aperta": "Appears open now", "chiusa": "Appears closed now", "ignoto": "Hours cannot be verified: call first",
        "oggi": "today {orari}", "chiusa_oggi": "closed today", "portami": "🧭 Take me there", "chiama": "📞 Call",
        "turno_btn": "🌙 Look for on-duty pharmacies (night and holidays)",
        "osm": "ℹ️ Locations and hours come from OpenStreetMap, an open map updated by volunteers: they may be incomplete or out of date. On holidays and at night the normal hours do not apply. The app cannot know which pharmacies are on duty: use the button above or phone to be sure.",
        "v_titolo": "🏷️ Offers in the leaflets", "v_citta": "📍 City", "v_cerca_h": "**1️⃣ Search the leaflets**",
        "v_cap": "There is no public leaflet archive to check automatically: these buttons open the search on the leaflet sites of your country, already filled in with product and city.",
        "v_scrivi_citta": "Write the city to look for offers in your area.",
        "v_cerca_btn": "🔎 Search the leaflets of {citta}", "v_tutti": "🛒 All supermarket leaflets in {citta}",
        "v_tipo_Supermercato": "Supermarket", "v_tipo_Ipermercato": "Hypermarket", "v_tipo_Discount": "Discount store",
    },
    "es": {
        "f_btn": "🔎 Encuentra una farmacia abierta", "f_titolo": "Encuentra una farmacia abierta", "paese": "🌍 País",
        "dove": "Ciudad, municipio o código postal", "dove_ph": "p. ej. {citta}", "cerca": "Buscar",
        "err_vuoto": "Escribe el nombre de una ciudad o un código postal.",
        "err_non_trovo": "No encuentro este lugar en {paese}. Comprueba cómo lo has escrito o cambia de país.",
        "err_rete": "No consigo conectar con el servicio de mapas ahora mismo. Inténtalo de nuevo en un momento.",
        "scrivi": "Escribe la ciudad o el código postal y toca Buscar.", "solo_aperte": "Mostrar solo las que figuran abiertas ahora",
        "vicino": "Búsqueda cerca de: {luogo} · a las {ora} del {data}",
        "nessuna": "No he encontrado farmacias cerca de este lugar. Prueba con otro código postal o con el nombre del municipio.",
        "nessuna_aperta": "Ninguna farmacia figura abierta ahora según los horarios disponibles. Mira también las de horario no verificable y las de guardia.",
        "aperta": "Figura abierta ahora", "chiusa": "Figura cerrada ahora", "ignoto": "Horario no verificable: llama antes",
        "oggi": "hoy {orari}", "chiusa_oggi": "cerrada hoy", "portami": "🧭 Llévame allí", "chiama": "📞 Llamar",
        "turno_btn": "🌙 Buscar farmacias de guardia (noche y festivos)",
        "osm": "ℹ️ Las ubicaciones y los horarios vienen de OpenStreetMap, un mapa abierto actualizado por voluntarios: pueden estar incompletos o desactualizados. En festivos y de noche no valen los horarios normales. La app no puede saber qué farmacias están de guardia: usa el botón de arriba o llama para estar seguro.",
        "v_titolo": "🏷️ Ofertas en los folletos", "v_citta": "📍 Ciudad", "v_cerca_h": "**1️⃣ Busca en los folletos**",
        "v_cap": "No existe un archivo público de folletos que se pueda consultar automáticamente: estos botones abren la búsqueda en los sitios de folletos de tu país, ya rellenada con producto y ciudad.",
        "v_scrivi_citta": "Escribe la ciudad para buscar las ofertas de tu zona.",
        "v_cerca_btn": "🔎 Buscar en los folletos de {citta}", "v_tutti": "🛒 Todos los folletos de supermercados en {citta}",
        "v_tipo_Supermercato": "Supermercado", "v_tipo_Ipermercato": "Hipermercado", "v_tipo_Discount": "Tienda de descuento",
    },
    "fr": {
        "f_btn": "🔎 Trouver une pharmacie ouverte", "f_titolo": "Trouver une pharmacie ouverte", "paese": "🌍 Pays",
        "dove": "Ville, commune ou code postal", "dove_ph": "ex. {citta}", "cerca": "Chercher",
        "err_vuoto": "Écris le nom d'une ville ou un code postal.",
        "err_non_trovo": "Je ne trouve pas ce lieu en {paese}. Vérifie comment tu l'as écrit ou change de pays.",
        "err_rete": "Je n'arrive pas à me connecter au service de cartes pour le moment. Réessaie dans un instant.",
        "scrivi": "Écris la ville ou le code postal et touche Chercher.", "solo_aperte": "Afficher seulement celles qui semblent ouvertes maintenant",
        "vicino": "Recherche près de : {luogo} · à {ora} le {data}",
        "nessuna": "Je n'ai pas trouvé de pharmacies près de ce lieu. Essaie avec un autre code postal ou le nom de la commune.",
        "nessuna_aperta": "Aucune pharmacie ne semble ouverte maintenant d'après les horaires disponibles. Regarde aussi celles aux horaires non vérifiables et celles de garde.",
        "aperta": "Semble ouverte maintenant", "chiusa": "Semble fermée maintenant", "ignoto": "Horaires non vérifiables : appelle avant",
        "oggi": "aujourd'hui {orari}", "chiusa_oggi": "fermée aujourd'hui", "portami": "🧭 Emmène-moi là-bas", "chiama": "📞 Appeler",
        "turno_btn": "🌙 Chercher les pharmacies de garde (nuit et jours fériés)",
        "osm": "ℹ️ Les positions et les horaires viennent d'OpenStreetMap, une carte ouverte mise à jour par des bénévoles : ils peuvent être incomplets ou périmés. Les jours fériés et la nuit les horaires normaux ne valent pas. L'appli ne peut pas savoir quelles pharmacies sont de garde : utilise le bouton ci-dessus ou téléphone pour être sûr.",
        "v_titolo": "🏷️ Offres dans les prospectus", "v_citta": "📍 Ville", "v_cerca_h": "**1️⃣ Cherche dans les prospectus**",
        "v_cap": "Il n'existe pas d'archive publique de prospectus à consulter automatiquement : ces boutons ouvrent la recherche sur les sites de prospectus de ton pays, déjà remplie avec produit et ville.",
        "v_scrivi_citta": "Écris la ville pour chercher les offres de ta zone.",
        "v_cerca_btn": "🔎 Chercher dans les prospectus de {citta}", "v_tutti": "🛒 Tous les prospectus des supermarchés à {citta}",
        "v_tipo_Supermercato": "Supermarché", "v_tipo_Ipermercato": "Hypermarché", "v_tipo_Discount": "Discount",
    },
    "de": {
        "f_btn": "🔎 Geöffnete Apotheke finden", "f_titolo": "Geöffnete Apotheke finden", "paese": "🌍 Land",
        "dove": "Stadt, Gemeinde oder Postleitzahl", "dove_ph": "z. B. {citta}", "cerca": "Suchen",
        "err_vuoto": "Schreibe den Namen einer Stadt oder eine Postleitzahl.",
        "err_non_trovo": "Ich finde diesen Ort in {paese} nicht. Prüfe die Schreibweise oder wechsle das Land.",
        "err_rete": "Ich kann mich gerade nicht mit dem Kartendienst verbinden. Versuche es gleich noch einmal.",
        "scrivi": "Schreibe die Stadt oder die Postleitzahl und tippe auf Suchen.", "solo_aperte": "Nur die anzeigen, die jetzt geöffnet scheinen",
        "vicino": "Suche in der Nähe von: {luogo} · um {ora} am {data}",
        "nessuna": "Ich habe in der Nähe dieses Ortes keine Apotheken gefunden. Versuche eine andere Postleitzahl oder den Namen der Gemeinde.",
        "nessuna_aperta": "Nach den verfügbaren Zeiten scheint jetzt keine Apotheke geöffnet. Sieh auch bei denen mit nicht überprüfbaren Zeiten und bei den Notdienst-Apotheken nach.",
        "aperta": "Scheint jetzt geöffnet", "chiusa": "Scheint jetzt geschlossen", "ignoto": "Zeiten nicht überprüfbar: vorher anrufen",
        "oggi": "heute {orari}", "chiusa_oggi": "heute geschlossen", "portami": "🧭 Bring mich hin", "chiama": "📞 Anrufen",
        "turno_btn": "🌙 Notdienst-Apotheken suchen (Nacht und Feiertage)",
        "osm": "ℹ️ Standorte und Zeiten stammen von OpenStreetMap, einer offenen Karte, die von Freiwilligen gepflegt wird: sie können unvollständig oder veraltet sein. An Feiertagen und nachts gelten die normalen Zeiten nicht. Die App kann nicht wissen, welche Apotheken Notdienst haben: nutze den Knopf oben oder ruf an, um sicher zu sein.",
        "v_titolo": "🏷️ Angebote in den Prospekten", "v_citta": "📍 Stadt", "v_cerca_h": "**1️⃣ In den Prospekten suchen**",
        "v_cap": "Es gibt kein öffentliches Prospekt-Archiv, das automatisch geprüft werden kann: diese Knöpfe öffnen die Suche auf den Prospekt-Seiten deines Landes, schon mit Produkt und Stadt ausgefüllt.",
        "v_scrivi_citta": "Schreibe die Stadt, um die Angebote deiner Gegend zu suchen.",
        "v_cerca_btn": "🔎 In den Prospekten von {citta} suchen", "v_tutti": "🛒 Alle Supermarkt-Prospekte in {citta}",
        "v_tipo_Supermercato": "Supermarkt", "v_tipo_Ipermercato": "Hypermarkt", "v_tipo_Discount": "Discounter",
    },
    "ro": {
        "f_btn": "🔎 Găsește o farmacie deschisă", "f_titolo": "Găsește o farmacie deschisă", "paese": "🌍 Țara",
        "dove": "Oraș, localitate sau cod poștal", "dove_ph": "ex. {citta}", "cerca": "Caută",
        "err_vuoto": "Scrie numele unui oraș sau un cod poștal.",
        "err_non_trovo": "Nu găsesc acest loc în {paese}. Verifică cum l-ai scris sau schimbă țara.",
        "err_rete": "Nu mă pot conecta acum la serviciul de hărți. Încearcă din nou peste puțin.",
        "scrivi": "Scrie orașul sau codul poștal și atinge Caută.", "solo_aperte": "Arată doar cele care par deschise acum",
        "vicino": "Căutare lângă: {luogo} · la {ora} pe {data}",
        "nessuna": "Nu am găsit farmacii lângă acest loc. Încearcă un alt cod poștal sau numele localității.",
        "nessuna_aperta": "Nicio farmacie nu pare deschisă acum după programul disponibil. Verifică și pe cele cu program neverificabil și pe cele de gardă.",
        "aperta": "Pare deschisă acum", "chiusa": "Pare închisă acum", "ignoto": "Program neverificabil: sună înainte",
        "oggi": "azi {orari}", "chiusa_oggi": "închisă azi", "portami": "🧭 Du-mă acolo", "chiama": "📞 Sună",
        "turno_btn": "🌙 Caută farmaciile de gardă (noaptea și sărbători)",
        "osm": "ℹ️ Pozițiile și programul vin de la OpenStreetMap, o hartă deschisă actualizată de voluntari: pot fi incomplete sau neactualizate. În zilele de sărbătoare și noaptea programul obișnuit nu se aplică. Aplicația nu poate ști care farmacii sunt de gardă: folosește butonul de mai sus sau sună ca să fii sigur.",
        "v_titolo": "🏷️ Oferte în cataloage", "v_citta": "📍 Oraș", "v_cerca_h": "**1️⃣ Caută în cataloage**",
        "v_cap": "Nu există o arhivă publică de cataloage care să poată fi verificată automat: aceste butoane deschid căutarea pe site-urile de cataloage din țara ta, deja completată cu produs și oraș.",
        "v_scrivi_citta": "Scrie orașul ca să cauți ofertele din zona ta.",
        "v_cerca_btn": "🔎 Caută în cataloagele din {citta}", "v_tutti": "🛒 Toate cataloagele supermarketurilor din {citta}",
        "v_tipo_Supermercato": "Supermarket", "v_tipo_Ipermercato": "Hipermarket", "v_tipo_Discount": "Discount",
    },
    "ar": {
        "f_btn": "🔎 ابحث عن صيدلية مفتوحة", "f_titolo": "ابحث عن صيدلية مفتوحة", "paese": "🌍 البلد",
        "dove": "المدينة أو البلدة أو الرمز البريدي", "dove_ph": "مثال: {citta}", "cerca": "بحث",
        "err_vuoto": "اكتب اسم مدينة أو رمزاً بريدياً.",
        "err_non_trovo": "لا أجد هذا المكان في {paese}. تحقق من طريقة كتابته أو غيّر البلد.",
        "err_rete": "لا أستطيع الاتصال بخدمة الخرائط الآن. حاول مرة أخرى بعد قليل.",
        "scrivi": "اكتب المدينة أو الرمز البريدي والمس بحث.", "solo_aperte": "إظهار التي تبدو مفتوحة الآن فقط",
        "vicino": "البحث بالقرب من: {luogo} · الساعة {ora} بتاريخ {data}",
        "nessuna": "لم أجد صيدليات بالقرب من هذا المكان. جرّب رمزاً بريدياً آخر أو اسم البلدة.",
        "nessuna_aperta": "لا تبدو أي صيدلية مفتوحة الآن حسب المواعيد المتاحة. تحقق أيضاً من التي مواعيدها غير مؤكدة ومن المناوبة.",
        "aperta": "تبدو مفتوحة الآن", "chiusa": "تبدو مغلقة الآن", "ignoto": "المواعيد غير مؤكدة: اتصل قبل الذهاب",
        "oggi": "اليوم {orari}", "chiusa_oggi": "مغلقة اليوم", "portami": "🧭 خذني إلى هناك", "chiama": "📞 اتصال",
        "turno_btn": "🌙 ابحث عن الصيدليات المناوبة (ليلاً والعطل)",
        "osm": "ℹ️ المواقع والمواعيد تأتي من OpenStreetMap، وهي خريطة مفتوحة يحدّثها متطوعون: قد تكون ناقصة أو قديمة. في العطل وفي الليل لا تنطبق المواعيد العادية. لا يستطيع التطبيق معرفة أي الصيدليات مناوبة: استخدم الزر أعلاه أو اتصل للتأكد.",
        "v_titolo": "🏷️ العروض في النشرات", "v_citta": "📍 المدينة", "v_cerca_h": "**1️⃣ ابحث في النشرات**",
        "v_cap": "لا يوجد أرشيف عام للنشرات يمكن فحصه تلقائياً: تفتح هذه الأزرار البحث في مواقع النشرات في بلدك، مملوءاً بالمنتج والمدينة.",
        "v_scrivi_citta": "اكتب المدينة للبحث عن عروض منطقتك.",
        "v_cerca_btn": "🔎 ابحث في نشرات {citta}", "v_tutti": "🛒 كل نشرات السوبرماركت في {citta}",
        "v_tipo_Supermercato": "سوبرماركت", "v_tipo_Ipermercato": "هايبرماركت", "v_tipo_Discount": "متجر خصومات",
    },
}

# --- ricerca con il GPS del telefono ---
RP_TR["it"].update({'gps_btn': '📍 Usa la mia posizione (GPS)', 'gps_hint': 'Il telefono ti chiederà il permesso di usare la posizione. Non viene salvata. Oppure scrivi la città qui sotto.', 'gps_err_perm': 'Non ho il permesso di usare la posizione. Consentila nelle impostazioni del browser per questo sito, oppure scrivi la città.', 'gps_err_non_disp': 'Non riesco a trovare la posizione adesso. Accendi il GPS oppure scrivi la città.', 'gps_err_tempo': "La posizione ci mette troppo. Riprova all'aperto oppure scrivi la città.", 'gps_err_no': 'Questo telefono o browser non permette di usare la posizione. Scrivi la città.', 'gps_luogo': 'la tua posizione (±{acc} m)'})
RP_TR["en"].update({'gps_btn': '📍 Use my location (GPS)', 'gps_hint': 'The phone will ask permission to use your location. It is not saved. Or write the city below.', 'gps_err_perm': 'I do not have permission to use the location. Allow it in the browser settings for this site, or write the city.', 'gps_err_non_disp': 'I cannot find the location right now. Turn on GPS or write the city.', 'gps_err_tempo': 'The location is taking too long. Try again outdoors or write the city.', 'gps_err_no': 'This phone or browser does not allow using the location. Write the city.', 'gps_luogo': 'your location (±{acc} m)'})
RP_TR["es"].update({'gps_btn': '📍 Usar mi ubicación (GPS)', 'gps_hint': 'El teléfono te pedirá permiso para usar la ubicación. No se guarda. O escribe la ciudad abajo.', 'gps_err_perm': 'No tengo permiso para usar la ubicación. Permítela en los ajustes del navegador para este sitio, o escribe la ciudad.', 'gps_err_non_disp': 'No consigo encontrar la ubicación ahora. Enciende el GPS o escribe la ciudad.', 'gps_err_tempo': 'La ubicación tarda demasiado. Inténtalo al aire libre o escribe la ciudad.', 'gps_err_no': 'Este teléfono o navegador no permite usar la ubicación. Escribe la ciudad.', 'gps_luogo': 'tu ubicación (±{acc} m)'})
RP_TR["fr"].update({'gps_btn': '📍 Utiliser ma position (GPS)', 'gps_hint': "Le téléphone te demandera l'autorisation d'utiliser la position. Elle n'est pas enregistrée. Ou écris la ville ci-dessous.", 'gps_err_perm': "Je n'ai pas l'autorisation d'utiliser la position. Autorise-la dans les réglages du navigateur pour ce site, ou écris la ville.", 'gps_err_non_disp': "Je n'arrive pas à trouver la position pour le moment. Allume le GPS ou écris la ville.", 'gps_err_tempo': 'La position met trop de temps. Réessaie en extérieur ou écris la ville.', 'gps_err_no': "Ce téléphone ou navigateur ne permet pas d'utiliser la position. Écris la ville.", 'gps_luogo': 'ta position (±{acc} m)'})
RP_TR["de"].update({'gps_btn': '📍 Meinen Standort nutzen (GPS)', 'gps_hint': 'Das Handy fragt nach der Erlaubnis, den Standort zu nutzen. Er wird nicht gespeichert. Oder schreibe unten die Stadt.', 'gps_err_perm': 'Ich habe keine Erlaubnis, den Standort zu nutzen. Erlaube ihn in den Browser-Einstellungen für diese Seite oder schreibe die Stadt.', 'gps_err_non_disp': 'Ich finde den Standort gerade nicht. Schalte das GPS ein oder schreibe die Stadt.', 'gps_err_tempo': 'Der Standort braucht zu lange. Versuche es im Freien oder schreibe die Stadt.', 'gps_err_no': 'Dieses Handy oder dieser Browser erlaubt keine Standortnutzung. Schreibe die Stadt.', 'gps_luogo': 'dein Standort (±{acc} m)'})
RP_TR["ro"].update({'gps_btn': '📍 Folosește locația mea (GPS)', 'gps_hint': 'Telefonul îți va cere permisiunea de a folosi locația. Nu se salvează. Sau scrie orașul mai jos.', 'gps_err_perm': 'Nu am permisiunea de a folosi locația. Permite-o în setările browserului pentru acest site sau scrie orașul.', 'gps_err_non_disp': 'Nu pot găsi locația acum. Pornește GPS-ul sau scrie orașul.', 'gps_err_tempo': 'Locația durează prea mult. Încearcă afară sau scrie orașul.', 'gps_err_no': 'Acest telefon sau browser nu permite folosirea locației. Scrie orașul.', 'gps_luogo': 'locația ta (±{acc} m)'})
RP_TR["ar"].update({'gps_btn': '📍 استخدم موقعي (GPS)', 'gps_hint': 'سيطلب منك الهاتف الإذن باستخدام الموقع. لا يتم حفظه. أو اكتب المدينة في الأسفل.', 'gps_err_perm': 'ليس لدي إذن باستخدام الموقع. اسمح به في إعدادات المتصفح لهذا الموقع أو اكتب المدينة.', 'gps_err_non_disp': 'لا أستطيع إيجاد الموقع الآن. شغّل GPS أو اكتب المدينة.', 'gps_err_tempo': 'الموقع يستغرق وقتاً طويلاً. حاول في الهواء الطلق أو اكتب المدينة.', 'gps_err_no': 'هذا الهاتف أو المتصفح لا يسمح باستخدام الموقع. اكتب المدينة.', 'gps_luogo': 'موقعك (±{acc} م)'})

# --- errori dei servizi delle mappe e alternativa con Google Maps ---
RP_TR["it"].update({'err_geo': 'Il servizio che trova le città non risponde in questo momento.', 'err_farm': 'Il servizio che elenca le farmacie è sovraccarico e non risponde. Riprova tra qualche secondo.', 'fallback_btn': '🗺️ Apri Google Maps e cerca le farmacie qui', 'dettaglio': 'Dettaglio tecnico: {d}', 'riprova': 'Tocca Cerca per riprovare, oppure usa Google Maps.'})
RP_TR["en"].update({'err_geo': 'The service that finds cities is not responding right now.', 'err_farm': 'The service that lists pharmacies is overloaded and not responding. Try again in a few seconds.', 'fallback_btn': '🗺️ Open Google Maps and look for pharmacies here', 'dettaglio': 'Technical detail: {d}', 'riprova': 'Tap Search to try again, or use Google Maps.'})
RP_TR["es"].update({'err_geo': 'El servicio que encuentra las ciudades no responde en este momento.', 'err_farm': 'El servicio que lista las farmacias está sobrecargado y no responde. Inténtalo de nuevo en unos segundos.', 'fallback_btn': '🗺️ Abrir Google Maps y buscar farmacias aquí', 'dettaglio': 'Detalle técnico: {d}', 'riprova': 'Toca Buscar para intentarlo de nuevo, o usa Google Maps.'})
RP_TR["fr"].update({'err_geo': 'Le service qui trouve les villes ne répond pas pour le moment.', 'err_farm': 'Le service qui liste les pharmacies est surchargé et ne répond pas. Réessaie dans quelques secondes.', 'fallback_btn': '🗺️ Ouvrir Google Maps et chercher les pharmacies ici', 'dettaglio': 'Détail technique : {d}', 'riprova': 'Touche Chercher pour réessayer, ou utilise Google Maps.'})
RP_TR["de"].update({'err_geo': 'Der Dienst, der Städte findet, antwortet gerade nicht.', 'err_farm': 'Der Dienst, der Apotheken auflistet, ist überlastet und antwortet nicht. Versuche es in ein paar Sekunden noch einmal.', 'fallback_btn': '🗺️ Google Maps öffnen und hier nach Apotheken suchen', 'dettaglio': 'Technisches Detail: {d}', 'riprova': 'Tippe auf Suchen, um es erneut zu versuchen, oder nutze Google Maps.'})
RP_TR["ro"].update({'err_geo': 'Serviciul care găsește orașele nu răspunde acum.', 'err_farm': 'Serviciul care listează farmaciile este suprasolicitat și nu răspunde. Încearcă din nou peste câteva secunde.', 'fallback_btn': '🗺️ Deschide Google Maps și caută farmacii aici', 'dettaglio': 'Detaliu tehnic: {d}', 'riprova': 'Atinge Caută ca să încerci din nou sau folosește Google Maps.'})
RP_TR["ar"].update({'err_geo': 'الخدمة التي تجد المدن لا تستجيب الآن.', 'err_farm': 'الخدمة التي تعرض الصيدليات مثقلة ولا تستجيب. حاول مرة أخرى بعد ثوانٍ.', 'fallback_btn': '🗺️ افتح خرائط Google وابحث عن الصيدليات هنا', 'dettaglio': 'تفصيل تقني: {d}', 'riprova': 'المس بحث للمحاولة مرة أخرى أو استخدم خرائط Google.'})

# --- foto (controllo, elimina, tieni tutta la foto) e tabella a schermo intero ---
RP_TR["it"].update({'foto_ricevuta': '📥 Foto ricevuta: {nome} ({kb} KB)', 'foto_elimina': '🗑️ Elimina questa foto', 'foto_tolta': "Foto eliminata. Scegline o scattane un'altra con i pulsanti qui sopra.", 'foto_tieni': 'Tieni tutta la foto (non togliere lo sfondo)', 'foto_usa_comunque': '✅ Usa comunque questa foto', 'foto_problema': '⚠️ Questa foto non va bene:', 'foto_consiglio': "Eliminala e fanne un'altra: più luce, telefono fermo, prodotto ben centrato.", 'foto_p_piccola': 'è troppo piccola', 'foto_p_sfocata': 'è sfocata', 'foto_p_scura': 'è troppo scura', 'foto_p_chiara': 'è troppo chiara', 'foto_p_vuota': 'sembra vuota (non si vede il prodotto)', 'foto_scatola': 'Il prodotto riempie la foto: ho tenuto tutta la confezione. Se non va bene, spunta «Tieni tutta la foto» o usa la cornice.', 'foto_carico': '⏳ Sto caricando la foto…', 'foto_non_arrivata': '⚠️ La foto non è arrivata. Riprova oppure usa «Carica dal telefono».', 'tab_intero': '⛶ Schermo intero (anche ruotando il telefono)', 'tab_titolo': 'Tabella a schermo intero', 'tab_hint': 'Ruota il telefono in orizzontale per vedere meglio. Per uscire tocca la X o torna indietro.'})
RP_TR["en"].update({'foto_ricevuta': '📥 Photo received: {nome} ({kb} KB)', 'foto_elimina': '🗑️ Delete this photo', 'foto_tolta': 'Photo deleted. Choose or take another one with the buttons above.', 'foto_tieni': 'Keep the whole photo (do not remove the background)', 'foto_usa_comunque': '✅ Use this photo anyway', 'foto_problema': '⚠️ This photo is not good:', 'foto_consiglio': 'Delete it and take another: more light, hold the phone still, product well centred.', 'foto_p_piccola': 'it is too small', 'foto_p_sfocata': 'it is blurry', 'foto_p_scura': 'it is too dark', 'foto_p_chiara': 'it is too bright', 'foto_p_vuota': 'it looks empty (the product is not visible)', 'foto_scatola': 'The product fills the photo: I kept the whole package. If it is not right, tick «Keep the whole photo» or use the frame.', 'foto_carico': '⏳ Uploading the photo…', 'foto_non_arrivata': '⚠️ The photo did not arrive. Try again or use «Upload from phone».', 'tab_intero': '⛶ Full screen (also rotating the phone)', 'tab_titolo': 'Full-screen table', 'tab_hint': 'Turn the phone sideways to see better. To leave, tap the X or go back.'})
RP_TR["es"].update({'foto_ricevuta': '📥 Foto recibida: {nome} ({kb} KB)', 'foto_elimina': '🗑️ Eliminar esta foto', 'foto_tolta': 'Foto eliminada. Elige o haz otra con los botones de arriba.', 'foto_tieni': 'Mantener toda la foto (no quitar el fondo)', 'foto_usa_comunque': '✅ Usar esta foto de todos modos', 'foto_problema': '⚠️ Esta foto no sirve:', 'foto_consiglio': 'Elimínala y haz otra: más luz, el teléfono quieto, el producto bien centrado.', 'foto_p_piccola': 'es demasiado pequeña', 'foto_p_sfocata': 'está borrosa', 'foto_p_scura': 'es demasiado oscura', 'foto_p_chiara': 'es demasiado clara', 'foto_p_vuota': 'parece vacía (no se ve el producto)', 'foto_scatola': 'El producto llena la foto: he mantenido todo el envase. Si no está bien, marca «Mantener toda la foto» o usa el marco.', 'foto_carico': '⏳ Subiendo la foto…', 'foto_non_arrivata': '⚠️ La foto no ha llegado. Inténtalo de nuevo o usa «Subir desde el teléfono».', 'tab_intero': '⛶ Pantalla completa (también girando el teléfono)', 'tab_titolo': 'Tabla a pantalla completa', 'tab_hint': 'Gira el teléfono en horizontal para ver mejor. Para salir toca la X o vuelve atrás.'})
RP_TR["fr"].update({'foto_ricevuta': '📥 Photo reçue : {nome} ({kb} Ko)', 'foto_elimina': '🗑️ Supprimer cette photo', 'foto_tolta': 'Photo supprimée. Choisis-en ou prends-en une autre avec les boutons ci-dessus.', 'foto_tieni': 'Garder toute la photo (ne pas enlever le fond)', 'foto_usa_comunque': '✅ Utiliser quand même cette photo', 'foto_problema': '⚠️ Cette photo ne convient pas :', 'foto_consiglio': 'Supprime-la et prends-en une autre : plus de lumière, téléphone immobile, produit bien centré.', 'foto_p_piccola': 'elle est trop petite', 'foto_p_sfocata': 'elle est floue', 'foto_p_scura': 'elle est trop sombre', 'foto_p_chiara': 'elle est trop claire', 'foto_p_vuota': "elle semble vide (le produit n'est pas visible)", 'foto_scatola': "Le produit remplit la photo : j'ai gardé tout l'emballage. Si ça ne va pas, coche « Garder toute la photo » ou utilise le cadre.", 'foto_carico': '⏳ Envoi de la photo…', 'foto_non_arrivata': "⚠️ La photo n'est pas arrivée. Réessaie ou utilise « Importer depuis le téléphone ».", 'tab_intero': '⛶ Plein écran (même en tournant le téléphone)', 'tab_titolo': 'Tableau en plein écran', 'tab_hint': "Tourne le téléphone à l'horizontale pour mieux voir. Pour sortir touche la X ou reviens en arrière."})
RP_TR["de"].update({'foto_ricevuta': '📥 Foto empfangen: {nome} ({kb} KB)', 'foto_elimina': '🗑️ Dieses Foto löschen', 'foto_tolta': 'Foto gelöscht. Wähle oder mache ein anderes mit den Knöpfen oben.', 'foto_tieni': 'Ganzes Foto behalten (Hintergrund nicht entfernen)', 'foto_usa_comunque': '✅ Dieses Foto trotzdem verwenden', 'foto_problema': '⚠️ Dieses Foto ist nicht gut:', 'foto_consiglio': 'Lösche es und mache ein neues: mehr Licht, Handy ruhig halten, Produkt gut zentriert.', 'foto_p_piccola': 'es ist zu klein', 'foto_p_sfocata': 'es ist unscharf', 'foto_p_scura': 'es ist zu dunkel', 'foto_p_chiara': 'es ist zu hell', 'foto_p_vuota': 'es wirkt leer (das Produkt ist nicht zu sehen)', 'foto_scatola': 'Das Produkt füllt das Foto: ich habe die ganze Verpackung behalten. Wenn es nicht passt, hake „Ganzes Foto behalten“ an oder nutze den Rahmen.', 'foto_carico': '⏳ Foto wird hochgeladen…', 'foto_non_arrivata': '⚠️ Das Foto ist nicht angekommen. Versuche es noch einmal oder nutze „Vom Handy hochladen“.', 'tab_intero': '⛶ Vollbild (auch beim Drehen des Handys)', 'tab_titolo': 'Tabelle im Vollbild', 'tab_hint': 'Drehe das Handy quer, um besser zu sehen. Zum Verlassen tippe auf das X oder geh zurück.'})
RP_TR["ro"].update({'foto_ricevuta': '📥 Fotografie primită: {nome} ({kb} KB)', 'foto_elimina': '🗑️ Șterge această fotografie', 'foto_tolta': 'Fotografie ștearsă. Alege sau fă alta cu butoanele de mai sus.', 'foto_tieni': 'Păstrează toată fotografia (nu scoate fundalul)', 'foto_usa_comunque': '✅ Folosește totuși această fotografie', 'foto_problema': '⚠️ Această fotografie nu e bună:', 'foto_consiglio': 'Șterge-o și fă alta: mai multă lumină, telefon nemișcat, produs bine centrat.', 'foto_p_piccola': 'este prea mică', 'foto_p_sfocata': 'este neclară', 'foto_p_scura': 'este prea întunecată', 'foto_p_chiara': 'este prea luminoasă', 'foto_p_vuota': 'pare goală (produsul nu se vede)', 'foto_scatola': 'Produsul umple fotografia: am păstrat tot ambalajul. Dacă nu e bine, bifează „Păstrează toată fotografia” sau folosește cadrul.', 'foto_carico': '⏳ Se încarcă fotografia…', 'foto_non_arrivata': '⚠️ Fotografia nu a ajuns. Încearcă din nou sau folosește „Încarcă din telefon”.', 'tab_intero': '⛶ Ecran complet (și rotind telefonul)', 'tab_titolo': 'Tabel pe ecran complet', 'tab_hint': 'Rotește telefonul pe orizontală ca să vezi mai bine. Ca să ieși atinge X sau mergi înapoi.'})
RP_TR["ar"].update({'foto_ricevuta': '📥 تم استلام الصورة: {nome} ({kb} KB)', 'foto_elimina': '🗑️ احذف هذه الصورة', 'foto_tolta': 'تم حذف الصورة. اختر صورة أخرى أو التقط واحدة بالأزرار أعلاه.', 'foto_tieni': 'احتفظ بالصورة كاملة (لا تُزل الخلفية)', 'foto_usa_comunque': '✅ استخدم هذه الصورة على أي حال', 'foto_problema': '⚠️ هذه الصورة غير مناسبة:', 'foto_consiglio': 'احذفها والتقط أخرى: إضاءة أكثر، هاتف ثابت، والمنتج في الوسط.', 'foto_p_piccola': 'صغيرة جداً', 'foto_p_sfocata': 'غير واضحة', 'foto_p_scura': 'داكنة جداً', 'foto_p_chiara': 'فاتحة جداً', 'foto_p_vuota': 'تبدو فارغة (المنتج غير ظاهر)', 'foto_scatola': 'المنتج يملأ الصورة: احتفظت بالعبوة كاملة. إن لم يكن مناسباً ضع علامة على «احتفظ بالصورة كاملة» أو استخدم الإطار.', 'foto_carico': '⏳ جارٍ رفع الصورة…', 'foto_non_arrivata': '⚠️ لم تصل الصورة. حاول مرة أخرى أو استخدم «رفع من الهاتف».', 'tab_intero': '⛶ ملء الشاشة (مع تدوير الهاتف أيضاً)', 'tab_titolo': 'الجدول بملء الشاشة', 'tab_hint': 'أدر الهاتف أفقياً لترى بشكل أفضل. للخروج المس X أو ارجع.'})


def _rp_lingua():
    try:
        return lingua()
    except Exception:
        return "it"


def rp_t(chiave, **valori):
    """Un testo della ricerca farmacie / volantini nella lingua scelta (se manca la traduzione, in italiano)."""
    testo = RP_TR.get(_rp_lingua(), {}).get(chiave) or RP_TR["it"].get(chiave, chiave)
    return testo.format(**valori) if valori else testo


def rp_paese():
    """Il Paese in uso: parte da quello della lingua scelta e si può cambiare (resta finché non cambia la lingua)."""
    lg = _rp_lingua()
    if st.session_state.get("_rp_lingua") != lg or st.session_state.get("rp_paese") not in PAESI:
        st.session_state["_rp_lingua"] = lg
        st.session_state["rp_paese"] = PAESE_LINGUA.get(lg, "IT")
    return st.session_state["rp_paese"]


def rp_selettore():
    """Il menu per scegliere il Paese (parte da quello della lingua). Ritorna il codice del Paese scelto."""
    rp_paese()
    return st.selectbox(rp_t("paese"), list(PAESI), format_func=lambda c: f"{PAESI[c]['bandiera']} {PAESI[c]['nome']}", key="rp_paese")


def rp_geocodifica_parametri(testo, cc):
    """I parametri da mandare a Nominatim (OpenStreetMap) per trovare il posto nel Paese scelto."""
    P = PAESI[cc]
    t_ = (testo or "").strip()
    tentativi = []
    if P["cap"] and re.fullmatch(P["cap"], t_, re.I):
        tentativi.append({"postalcode": t_, "country": P["q"]})
    tentativi.append({"q": f"{t_}, {P['q']}"})
    return [{**par, "format": "json", "limit": 1, "countrycodes": P["cc"], "accept-language": _rp_lingua()} for par in tentativi]


def rp_ora_locale(cc, tz=None):
    """Data e ora adesso nel fuso orario del Paese scelto, o in quello indicato dal telefono (serve a capire se una farmacia è aperta)."""
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo
    for nome in (tz, PAESI.get(cc, {}).get("tz")):
        try:
            if nome:
                return _dt.now(ZoneInfo(nome))
        except Exception:
            continue
    return _dt.now()


def rp_leggi_gps(valore):
    """Dal testo mandato dal browser («lat|lon|precisione|fuso|ora» oppure «errore|codice|ora») ricava ('ok', lat, lon, precisione, fuso)
    oppure ('errore', codice)."""
    parti = str(valore or "").split("|")
    if parti[0] == "errore":
        return ("errore", parti[1] if len(parti) > 1 else "")
    try:
        lat, lon = float(parti[0]), float(parti[1])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError
        acc = int(float(parti[2])) if len(parti) > 2 and parti[2] else 0
        return ("ok", lat, lon, acc, parti[3] if len(parti) > 3 else "")
    except Exception:
        return ("errore", "")


def rp_testo_errore_gps(codice):
    return rp_t({"1": "gps_err_perm", "2": "gps_err_non_disp", "3": "gps_err_tempo", "nogps": "gps_err_no"}.get(str(codice), "gps_err_non_disp"))


# Il tasto «Usa la mia posizione» è un normale pulsante di Streamlit: il browser (JavaScript) ne intercetta il tocco, chiede la posizione
# al telefono e la scrive nel campo nascosto «gps-posizione», così l'app la riceve. La posizione non viene salvata.
RP_JS_GPS = r"""
(function () {
  var w = window, doc = w.document;
  try {
    if (w.__gpsAttivo) return;
    w.__gpsAttivo = true;
    doc.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[class*="st-key-gps_btn"] button, button[class*="st-key-gps_btn"]') : null;
      if (!b) return;
      var inp = doc.querySelector('input[aria-label="gps-posizione"]');
      if (!inp) return;
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
      function invia(v) {
        var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, v);
        inp.dispatchEvent(new w.Event('input', {bubbles: true}));
        inp.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
        inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
      }
      if (!w.navigator.geolocation) { invia('errore|nogps|' + Date.now()); return; }
      w.navigator.geolocation.getCurrentPosition(function (p) {
        var tz = ''; try { tz = w.Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (x) {}
        invia(p.coords.latitude + '|' + p.coords.longitude + '|' + Math.round(p.coords.accuracy || 0) + '|' + tz + '|' + Date.now());
      }, function (err) { invia('errore|' + (err && err.code ? err.code : 2) + '|' + Date.now()); },
      {enableHighAccuracy: true, timeout: 20000, maximumAge: 60000});
    }, true);
  } catch (err) { /* se qualcosa non va, resta la ricerca scrivendo la città */ }
})();
"""


def rp_inietta_gps():
    """Inserisce nella pagina il piccolo script del GPS (una volta sola per sessione; lo stesso metodo di voce.py e fotocamera.py)."""
    if st.session_state.get("_rp_gps_js"):
        return
    st.session_state["_rp_gps_js"] = True
    import json as _json
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + _json.dumps(RP_JS_GPS) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_gps
            _comp_gps.html(pagina, height=0)
    except Exception:
        pass


def rp_link_turno(cc, dove):
    from urllib.parse import quote_plus
    return "https://www.google.com/search?q=" + quote_plus(f"{PAESI[cc]['turno']} {dove}")


def rp_link_mappe(cc, dove="", lat=None, lon=None):
    """Un link a Google Maps con la ricerca delle farmacie: funziona anche quando i servizi delle mappe dell'app non rispondono."""
    from urllib.parse import quote_plus
    parola = PAESI.get(cc, PAESI["IT"])["farmacia"]
    if lat is not None and lon is not None:
        return f"https://www.google.com/maps/search/{quote_plus(parola)}/@{lat},{lon},15z"
    return "https://www.google.com/maps/search/" + quote_plus(f"{parola} {dove}".strip())
