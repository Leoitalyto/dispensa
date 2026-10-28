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
    "IT": {"bandiera": "🇮🇹", "nome": "Italia", "q": "Italy", "cc": "it", "tz": "Europe/Rome", "citta": "Torino", "cap": r"\d{5}",
           "turno": "farmacie di turno", "offerta": "offerta volantino", "tutti": "volantini supermercati",
           "siti": [("DoveConviene", "doveconviene.it"), ("PromoQui", "promoqui.it"), ("Volantinofacile", "volantinofacile.it"),
                    ("Tiendeo", "tiendeo.it")],
           "catene": None},
    "ES": {"bandiera": "🇪🇸", "nome": "España", "q": "Spain", "cc": "es", "tz": "Europe/Madrid", "citta": "Barcelona", "cap": r"\d{5}",
           "turno": "farmacias de guardia", "offerta": "oferta folleto", "tutti": "folletos supermercados",
           "siti": [("Tiendeo", "tiendeo.es"), ("Ofertia", "ofertia.com")],
           "catene": {"Supermercato": ["Mercadona", "Dia", "Eroski", "Consum", "Caprabo", "BonPreu", "Condis", "Ahorramás", "Supercor"],
                      "Ipermercato": ["Carrefour", "Alcampo", "Hipercor", "E.Leclerc"],
                      "Discount": ["Lidl", "Aldi", "Dia Maxi"]}},
    "GB": {"bandiera": "🇬🇧", "nome": "United Kingdom", "q": "United Kingdom", "cc": "gb", "tz": "Europe/London", "citta": "London",
           "cap": r"[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}",
           "turno": "late night pharmacy open now", "offerta": "offer leaflet", "tutti": "supermarket leaflets",
           "siti": [("Tiendeo", "tiendeo.co.uk"), ("MySupermarket", "mysupermarket.co.uk")],
           "catene": {"Supermercato": ["Tesco", "Sainsbury's", "Asda", "Morrisons", "Waitrose", "Co-op", "M&S Food", "Iceland"],
                      "Ipermercato": ["Tesco Extra", "Asda Superstore", "Sainsbury's Superstore"],
                      "Discount": ["Aldi", "Lidl", "Farmfoods", "B&M"]}},
    "FR": {"bandiera": "🇫🇷", "nome": "France", "q": "France", "cc": "fr", "tz": "Europe/Paris", "citta": "Paris", "cap": r"\d{5}",
           "turno": "pharmacie de garde", "offerta": "promo prospectus", "tutti": "catalogues supermarchés",
           "siti": [("Tiendeo", "tiendeo.fr"), ("Bonial", "bonial.fr"), ("PromoCatalogues", "promocatalogues.com")],
           "catene": {"Supermercato": ["Carrefour Market", "Intermarché", "Monoprix", "Casino", "Franprix", "Super U", "Match"],
                      "Ipermercato": ["Carrefour", "E.Leclerc", "Auchan", "Hyper U", "Cora", "Géant Casino"],
                      "Discount": ["Lidl", "Aldi", "Netto", "Leader Price"]}},
    "DE": {"bandiera": "🇩🇪", "nome": "Deutschland", "q": "Germany", "cc": "de", "tz": "Europe/Berlin", "citta": "Berlin", "cap": r"\d{5}",
           "turno": "Notdienst Apotheke", "offerta": "Angebot Prospekt", "tutti": "Supermarkt Prospekte",
           "siti": [("Kaufda", "kaufda.de"), ("Marktjagd", "marktjagd.de"), ("Tiendeo", "tiendeo.de")],
           "catene": {"Supermercato": ["Edeka", "Rewe", "Tegut", "Nahkauf"],
                      "Ipermercato": ["Kaufland", "Real", "Globus", "Marktkauf"],
                      "Discount": ["Aldi", "Lidl", "Penny", "Netto"]}},
    "RO": {"bandiera": "🇷🇴", "nome": "România", "q": "Romania", "cc": "ro", "tz": "Europe/Bucharest", "citta": "București", "cap": r"\d{6}",
           "turno": "farmacie de gardă non-stop", "offerta": "ofertă catalog", "tutti": "cataloage supermarketuri",
           "siti": [("Tiendeo", "tiendeo.ro")],
           "catene": {"Supermercato": ["Mega Image", "Profi", "Carrefour Market", "Annabella"],
                      "Ipermercato": ["Kaufland", "Carrefour", "Auchan", "Selgros", "Cora"],
                      "Discount": ["Lidl", "Penny", "Aldi"]}},
    "EG": {"bandiera": "🇪🇬", "nome": "مصر", "q": "Egypt", "cc": "eg", "tz": "Africa/Cairo", "citta": "القاهرة", "cap": None,
           "turno": "صيدلية مناوبة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Spinneys", "Metro", "Seoudi", "Fathalla"], "Ipermercato": ["Carrefour", "Hyperone", "Lulu"],
                      "Discount": ["Kazyon", "Oscar"]}},
    "MA": {"bandiera": "🇲🇦", "nome": "المغرب", "q": "Morocco", "cc": "ma", "tz": "Africa/Casablanca", "citta": "الدار البيضاء", "cap": None,
           "turno": "صيدلية الحراسة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Marjane", "Carrefour Market", "Acima"], "Ipermercato": ["Marjane", "Carrefour", "Aswak Assalam"],
                      "Discount": ["Label'Vie"]}},
    "SA": {"bandiera": "🇸🇦", "nome": "السعودية", "q": "Saudi Arabia", "cc": "sa", "tz": "Asia/Riyadh", "citta": "الرياض", "cap": None,
           "turno": "صيدلية 24 ساعة", "offerta": "عروض", "tutti": "عروض السوبرماركت", "siti": [],
           "catene": {"Supermercato": ["Panda", "Othaim", "Tamimi", "Danube"], "Ipermercato": ["Hyper Panda", "Lulu", "Carrefour"],
                      "Discount": ["Al Raya", "Bin Dawood"]}},
    "AE": {"bandiera": "🇦🇪", "nome": "الإمارات", "q": "United Arab Emirates", "cc": "ae", "tz": "Asia/Dubai", "citta": "دبي", "cap": None,
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


def rp_ora_locale(cc):
    """Data e ora adesso nel fuso orario del Paese scelto (serve a capire se una farmacia è aperta)."""
    from datetime import datetime as _dt
    try:
        from zoneinfo import ZoneInfo
        return _dt.now(ZoneInfo(PAESI[cc]["tz"]))
    except Exception:
        return _dt.now()


def rp_link_turno(cc, dove):
    from urllib.parse import quote_plus
    return "https://www.google.com/search?q=" + quote_plus(f"{PAESI[cc]['turno']} {dove}")
