# -*- coding: utf-8 -*-
"""Guida, giro guidato, novità e testi dell'assistente in FRANCESE. Caricato da app_dispensa.py dopo info_sezioni.py.
Per le schermate Farmacia / I miei documenti / Utilità i nomi dei pulsanti restano come si vedono sullo schermo (in italiano)."""
GUIDA_TR["fr"] = {
    "d_assistente": ("🤖 L'assistant numérique (le petit robot)",
        """C'est le **petit robot jaune et bleu** en bas à droite, avec le visage rond. **Touche-le** et son panneau s'ouvre.

Ce qu'il sait faire :
- **📖 Explique-moi cette page** : il te dit à voix haute à quoi sert la page où tu es.
- **🧭 Visite guidée** : il t'explique toute l'appli pas à pas (Suivant et Retour).
- **🆕 Quoi de neuf** : il te dit les nouveautés et où les trouver.
- **🎤 Pose une question** : touche, parle (par exemple « comment ajouter une photo au document ? ») et il te répond avec le guide. Fonctionne sur Chrome pour Android.
- Tu peux aussi **écrire** la question dans la case.

**Voix :** il utilise la voix du téléphone. Si tu ne veux pas l'entendre, touche **🔊 Voix : activée** pour la couper.

**Pour le désactiver :** touche **⛔ Désactiver l'assistant** dans son panneau. Pour le réactiver ouvre le bouton rouge **Touche pour les infos** et touche **✅ Activer** dans l'encadré de l'assistant. Le choix reste enregistré sur le téléphone.""",
        "assistant robot voix parle micro ecoute question visite nouveautes desactiver activer eteindre aide"),
    "d_inizio": ("🚀 À quoi ça sert et comment commencer",
        """**À quoi ça sert :** elle garde la liste de ce que tu as à la maison, de la date de péremption et de ce que ça contient. Elle te prévient avant que quelque chose s'abîme.

**Pour commencer, 5 étapes :**
1. Touche l'onglet **➕ Ajouter** en bas.
2. Photographie le produit (ou saute cette étape).
3. Écris le nom, combien d'unités tu as et la **date de péremption**.
4. Touche le bouton pour enregistrer.
5. Reviens à l'onglet **🏠 Garde-manger** : le produit est là, avec la couleur de la péremption.

Le garde-manger est **à toi seul** : chaque personne a son mot de passe et personne ne voit les produits des autres.""",
        "commencer debuter premieres etapes qu'est-ce a quoi ca sert fonctionnement introduction utilisation"),
    "d_aggiungere": ("➕ Comment ajouter un produit",
        """1. Touche **➕ Ajouter** (onglet en bas).
2. En haut se trouve la zone de la **photo** : touche **📷 Prendre la photo** (l'appareil photo arrière s'ouvre) ou **📁 Importer depuis le téléphone**.
3. Écris le **nom** et la **marque**.
4. Écris le **code-barres** à la main (ce sont les chiffres sous les barres) : l'appli remplit toute seule ingrédients, valeurs et allergènes, si le produit est connu.
5. Écris **combien d'unités**, le **poids** ou combien de **litres**.
6. Choisis la **date de péremption**.
7. Dans **« Où le ranges-tu ? »** choisis : Garde-manger, Frigo, Congélateur, Cave, Magasin, Réserve ou Autre. La **Catégorie** est un texte libre.
8. Choisis **pour qui c'est** : adultes, bébés (0-2 ans) ou animaux.
9. Enregistre.

Si tu n'as aucune information, le **nom, les unités et la péremption** suffisent.""",
        "ajouter inserer nouveau produit code barres qr remplir ou frigo congelateur cave categorie quantite unites poids litres ecrire"),
    "d_foto": ("📸 La photo du produit : prise, règle et recadrage",
        """1. Touche **📷 Prendre la photo** ou **📁 Importer depuis le téléphone**.
2. L'appli enlève le **fond** et **redresse** toute seule le produit.
3. En dessous apparaît l'**éditeur** : glisse la **règle** pour tourner la photo et glisse le **cadre** pour recadrer les bords.
4. Quand elle est parfaite touche **💾 Enregistrer position et recadrage**.
5. Puis enregistre le produit.

Si l'éditeur ne fonctionne pas, ouvre **🛠️ Commandes de secours** : il y a des curseurs pour tourner et recadrer.""",
        "photo photographier prendre appareil tourner pivoter redresser recadrer couper fond detourer regle cadre image"),
    "d_colori": ("🎨 Les couleurs et les alertes de péremption",
        """- 🟢 **Vert** : il reste plus de 2 mois. Tout va bien.
- 🟠 **Orange** : périme dans moins de 2 mois. Mieux vaut l'utiliser.
- 🔴 **Rouge** : périme dans moins de 1 mois. Utilise-le vite.
- ⚫ **Sombre** : déjà périmé.

En haut tu vois les **compteurs** colorés et les alertes avec combien d'unités, de grammes ou de litres vont bientôt périmer.

Chaque section a son **son** : adultes les sons habituels ; bébés un son pour la fille (2 mois), un pour le garçon (1 mois) et les deux si périmé ; animaux le chat (2 mois), le chien (1 mois) et le lion si périmé.

Si tu as activé **Telegram** ou l'**e-mail**, l'alerte arrive aussi là.""",
        "couleurs peremption alertes vert orange rouge perime compteurs son sons sirene notification alerte quand perime"),
    "d_allergeni": ("🌾 Allergènes, ingrédients, végan et sans gluten",
        """1. Ouvre le **menu de gauche** (la flèche **»** en haut à gauche) et choisis **tes allergies**.
2. Les produits avec un allergène ont un **bouton jaune** avec son nom (par exemple *Gluten*) : touche-le et la **composition** s'ouvre, avec les mots dangereux surlignés.
3. Si l'allergène est **dangereux pour toi** la **sirène clignotante** apparaît, avec écrit à qui il est contre-indiqué.
4. Sur chaque fiche il y a le bouton **Ingrédients** : il ouvre tout le texte à lire, dans ta langue.
5. Les boutons **Végan** et **Végétarien** n'apparaissent que si le produit l'est vraiment. Le bouton **Sans gluten** a un bord doré.""",
        "allergenes allergie gluten ingredients vegan vegetarien sans gluten composition intolerance sirene dangereux"),
    "d_pulsanti": ("🔘 Les boutons de chaque produit : Supprimer, Info, Modifier",
        """Dans **Fiches**, sous chaque produit il y a trois boutons :
- **Supprimer** : retire le produit. Si tu as le même produit avec plusieurs péremptions, il demande **quelle ligne** supprimer.
- **Info** : ouvre le guide complet avec tous les symboles.
- **Modifier** : change n'importe quelle donnée (nom, péremption, photo, quantité…).

Dans **Tableau** on coche la case 🗑️ de la ligne puis on touche **Supprimer les lignes cochées** ou **Modifier la ligne cochée** (pour modifier, coche une seule ligne).""",
        "supprimer effacer corbeille modifier changer corriger info tableau fiches vue"),
    "d_icone": ("🧭 Les icônes Pharmacie, Mes documents et Utilitaires",
        """Sur l'Accueil, à côté des commandes de recherche, il y a **trois icônes qui pulsent** :
- **🏥 Pharmacie** : médicaments, traitements, visites, carte vitale.
- **📁 Mes documents** : carte d'identité, permis, carte vitale avec les échéances.
- **🧰 Utilitaires** : applis et sites utiles, comme Velocity Music.

Touches-en une pour l'ouvrir ; pour revenir touche **← Retour au garde-manger**. Sur chaque page, en haut, il y a le bouton rouge **Touche pour les infos** avec le guide.""",
        "icones pharmacie documents utilitaires accueil pages naviguer menu ou trouver"),
    "d_cercare": ("🔎 Chercher et filtrer les produits",
        """En haut du Garde-manger il y a trois commandes :
1. **🔎 Chercher** : écris le nom ou la marque.
2. **Afficher** : choisis *Tous*, *Seulement bientôt périmés (2 mois)*, *Seulement rouges (1 mois)* ou *Périmés*.
3. **Vue** : *Fiches* (avec grandes photos) ou *Tableau* (liste compacte).""",
        "chercher recherche trouver filtre filtrer afficher vue fiches tableau liste"),
    "d_spesa": ("🛒 Liste de courses et prospectus",
        """- Quand un produit **est fini** il va tout seul dans l'onglet **🛒 Courses**.
- Dans l'onglet Courses tu peux toucher **J'en ai consommé un** pour retirer une unité.
- Sur la fiche du produit, à droite de la quantité, il y a le lien vers les **prospectus** des supermarchés, hypermarchés et discounts : choisis le **pays** (celui de ta langue au départ) et écris la **ville**, regarde les offres et touche le bouton pour mettre le produit dans la **liste de courses**, avec le nom du magasin.""",
        "courses liste de courses acheter prospectus offres supermarche consomme fini ville magasin"),
    "d_gestisci": ("✏️ Gérer beaucoup de produits d'un coup",
        """L'onglet **✏️ Gérer** sert à changer d'un seul coup **quantité, péremptions et notes** de beaucoup de produits, sans les ouvrir un par un.""",
        "gerer modifier beaucoup plusieurs produits ensemble quantite peremptions notes"),
    "d_account": ("👤 Mot de passe, langue et messages",
        """- **Mot de passe :** il t'est donné par la personne qui gère l'appli. À la première connexion tu peux le changer. Il est à toi seul.
- **Langue :** dans le menu de gauche il y a **🌐 Langue / Language**.
- **Messages et suggestions :** pour une idée, un problème ou une demande utilise l'onglet **✉️ Messages / 💬 Suggestions** : l'administrateur le lit.""",
        "mot de passe compte connexion langue language messages suggestions administrateur probleme demande changer"),
    "d_aiuto": ("🛟 Si quelque chose ne va pas",
        """1. **Recharge la page** du navigateur.
2. La photo n'apparaît pas ? Utilise **🛠️ Commandes de secours** ou choisis une autre photo.
3. Le micro pour dicter fonctionne sur **Chrome pour Android** : touche une fois pour l'allumer, une fois pour l'éteindre.
4. Si le problème reste, écris-le dans l'onglet **Messages** : ça aide l'administrateur à le régler.""",
        "probleme erreur ne marche pas aide bloque photo n'apparait pas micro dictee"),

    "f_cosa": ("🚀 À quoi sert la Pharmacie",
        """Ici tu ranges les **médicaments de la maison** et leurs **péremptions**, les **traitements**, les **visites**, les **vaccins**, ton **médecin** et ta **fiche santé**.

L'appli te **rappelle** et organise ce que tu saisis. Elle **ne donne pas de conseils médicaux** et ne change pas les traitements : pour les doses et les soins suis toujours ton médecin ou ton pharmacien.""",
        "pharmacie qu'est-ce a quoi ca sert medicaments commencer introduction"),
    "f_profili": ("👤 Les profils de la famille et le groupe sanguin",
        """Chaque personne a un **profil** (jusqu'à 12) : maman, papa, enfants…
1. En haut choisis le profil dans **👤 Profilo**.
2. Pour en ajouter un ouvre **👥 Gestisci profili**, écris le nom et touche **Aggiungi profilo**.
3. Au même endroit tu peux changer le nom et choisir le **🩸 groupe sanguin** : il apparaît comme une **goutte** colorée à côté du profil.
4. Pour supprimer un profil coche la confirmation et touche **Elimina profilo** (toutes ses données sont supprimées aussi).""",
        "profil profils famille personne groupe sanguin goutte nom ajouter supprimer"),
    "f_medicinale": ("💊 Comment ajouter un médicament",
        """1. Touche **➕ Aggiungi medicinale**.
2. En haut la **photo de la boîte** : **📷 Scatta la foto** ou **📁 Carica dal telefono** ; puis redresse avec la règle, recadre avec le cadre et touche **💾 Salva posizione e ritaglio**.
3. Écris **nom**, **principe actif**, **dosage**, **forme** (comprimés, sirop…) et **quantité**.
4. Choisis la **péremption** et **pour qui c'est**.
5. Touche **Salva**.

Tu peux réutiliser une photo déjà enregistrée depuis l'**archive des photos**. Tu peux joindre au médicament la **notice** (PDF, photo ou lien).

Pour tout voir d'un médicament, **touche sa fiche** : le détail s'ouvre avec la **notice**, la grande photo, les traitements liés et les boutons **✏️ Modifica** et **🗑️ Elimina**.

Pour gagner du temps touche **🎥 Scansiona in diretta** (Scanner en direct) et vise le petit carré (DataMatrix) ou les barres de la boîte : l'appli remplit péremption, lot et code. Si le téléphone ne le permet pas, prends une photo : je lis aussi la date de péremption écrite sur la boîte. Si le médicament est déjà à la maison elle copie aussi nom et dosage ; s'il est nouveau, écris le nom une seule fois et la prochaine fois elle le reconnaît.""",
        "medicament medicaments ajouter boite photo peremption principe actif dosage notice archive"),
    "f_scadenze": ("🎨 Péremptions et allergies aux médicaments",
        """- 🟠 **Orange** : périme dans moins de 2 mois. 🔴 **Rouge** : dans moins de 1 mois. ⚫ **Périmé** : à jeter correctement.
- Dans la fiche du profil tu peux écrire les **allergies aux médicaments** : si un médicament contient ce principe actif, un **avertissement rouge** apparaît.""",
        "peremption couleurs allergie allergies medicaments avertissement rouge orange perime"),
    "f_terapie": ("📅 Les traitements et le calendrier",
        """1. Ouvre l'onglet **📅 Terapie**.
2. Ajoute un traitement : **médicament**, **jours**, **heures** et quantité.
3. À l'heure prévue touche **Presa** (pris) pour noter la prise : elle reste dans l'**historique**.
4. Un traitement peut être **actif**, **suspendu** ou **terminé**. Les traitements d'essai peuvent être **supprimés**.
5. Le **calendrier** montre la semaine et le mois.
6. Le **Rapport pour le médecin** (période au choix) s'imprime ou s'ouvre dans Excel.""",
        "traitement traitements calendrier prise heures rapport medecin historique pilule dose"),
    "f_prescrizioni": ('📝 Ordonnances',
        """1. Ouvre l'onglet **📝 Prescrizioni** et touche **➕ Aggiungi prescrizione**.
2. Écris la **date**, le **type** (médicaments, examens, consultation…), le **médecin**, ce qui a été **prescrit**, le **code de l'ordonnance** et jusqu'à quand elle est **valable**.
3. Joins la **photo de l'ordonnance** ou le PDF.
4. En touchant une ordonnance, le **détail** s'ouvre : tu vois la photo, tu touches **✅ Segna come usata** (Marquer comme utilisée), **✏️ Modifica** ou **🗑️ Elimina**.
5. Les ordonnances bientôt périmées apparaissent parmi les choses à vérifier, aussi dans le **Contrôle famille**.""",
        'ordonnance ordonnances prescription medecin code validite expiration utilisee'),
    "f_invio": ('📤 Exporter et envoyer (PDF, email, WhatsApp…)',
        """1. En haut de la Pharmacie ouvre **📤 Esporta e invia** (Exporter et envoyer). Choisis **de qui** et **quoi** (médicaments, traitements, ordonnances, visites, vaccins, documents, fiche santé, garde-manger, liste de courses).
2. Choisis le **format** (PDF, Excel ou fichier à imprimer) et touche **📦 Prepara i file** (Préparer les fichiers).
3. Puis choisis comment les envoyer : **📤 Telefono** (la fenêtre Partager s'ouvre : WhatsApp, Gmail, Telegram, Drive…), **✉️ Email** (directement depuis l'appli), **💬 WhatsApp** (résumé écrit), **✈️ Telegram** (dans ta discussion avec le bot), **📱 SMS** ou **📋 Copia** (Copier).
4. Chaque document, médicament, ordonnance et visite a aussi son bouton **📤 Invia** (Envoyer), avec ses photos.
5. Le chef de famille peut envoyer les données de toute la famille depuis le **Contrôle famille**.

Seulement pour qui gère l'appli : pour envoyer email et Telegram directement depuis l'appli, dans Streamlit ouvre Manage app, puis Settings, puis Secrets, et ajoute EMAIL_USER, EMAIL_PASSWORD et TELEGRAM_TOKEN (les mêmes valeurs que pour les rappels). Il contient des données de santé : vérifie bien à qui tu l'envoies.""",
        'envoyer partager whatsapp email courrier telegram sms pdf excel imprimer exporter piece jointe fichier'),
    "f_visite": ("🩺 Visites, examens et comptes rendus",
        """1. Ouvre l'onglet **🩺 Visite** et touche pour ajouter.
2. Écris **date**, **type de visite ou d'examen**, **médecin**, **motif** et les **consignes pour les contrôles**.
3. S'il y en a un, écris la date du **prochain rendez-vous**.
4. Joins les **comptes rendus** : photo ou PDF.""",
        "visite visites examen compte rendu analyse rendez-vous specialiste joindre"),
    "f_vaccini": ("💉 Vaccins et carnet de vaccination",
        """Dans l'onglet **💉 Vaccini** tu enregistres les vaccinations de chaque profil et tu joins le **carnet de vaccination** (photo ou PDF).""",
        "vaccin vaccins vaccination carnet"),
    "f_scheda": ("🩸 La fiche santé et « Il mio dottore »",
        """- Touche l'encadré du **groupe sanguin** pour ouvrir la **fiche santé** : pathologies, allergies aux médicaments, interventions, antécédents et vaccinations.
- À côté tu trouves **Il mio dottore** (Mon médecin) : choisis médecin homme ou femme, puis écris nom, adresse, téléphone, e-mail, les **horaires** (une ligne par jour : de, à, notes), le **remplaçant** et les notes.""",
        "fiche sante medecin medecin traitant pathologies interventions antecedents horaires telephone email remplacant"),
    "f_tessera": ("🪪 Carte santé et dossier santé",
        """En haut, à côté de la médecin, il y a le badge bleu clair **Tessera sanitaria · Fascicolo sanitario** (il pulse doucement pour se faire remarquer). Touche-le.

**La carte**
1. Touche **👁️ Mostra fronte e retro della tessera** : tu la vois en grand.
2. La carte est prise dans **I miei documenti**. Si tu ne l'as pas encore saisie, un avertissement apparaît avec le bouton **📁 Vai a I miei documenti** : choisis **Tessera sanitaria** et prends la photo recto-verso. L'avertissement disparaît tout seul dès que tu l'as saisie.

**Les liens en ligne** (un pour le dossier santé électronique, un pour les vaccinations, un pour les frais de santé déductibles)
1. Ouvre la page dans le navigateur et **copie l'adresse** de la barre du haut.
2. Reviens ici et **colle-la** dans la bonne case.
3. Touche **💾 Salva**.
4. À partir de là un bouton **🔗** apparaît : en le touchant la page s'ouvre directement.
5. Pour changer le lien touche **✏️ Modifica** ; pour le retirer touche **🗑️ Togli il link**.

Les liens sont séparés pour chaque profil de la famille.""",
        "carte sante tessera sanitaria dossier sante electronique fse lien adresse vaccinations en ligne frais deductibles recto verso badge"),
    "f_aperta": ("🔎 Trouver une pharmacie ouverte",
        """Touche le grand bouton en haut (**Trouver une pharmacie ouverte**) : choisis le **pays** (celui de ta langue au départ) et écris **n'importe quelle ville ou code postal**. L'appli cherche les pharmacies ouvertes près de ce lieu. Ou touche **📍 Utiliser ma position (GPS)** : le téléphone demande l'autorisation et l'appli cherche autour de toi (la position n'est pas enregistrée).""",
        "pharmacie ouverte trouver chercher proche garde nuit"),
    "f_avvisi": ("🔔 Alertes sur Telegram, e-mail et SMS",
        """Les alertes te rappellent les péremptions (à 60, 30, 14 et 7 jours, 1 jour et le jour même) et, si tu veux, l'heure des traitements. Choisis **un ou plusieurs canaux**.

### 📱 Telegram, pas à pas
**Ce qu'il faut :** l'appli Telegram sur le téléphone et deux minutes. Telegram est gratuit.

1. **Installe Telegram** depuis le Play Store (Android) ou l'App Store (iPhone) et crée ton compte : il demande ton numéro de portable.
2. **Ouvre le bot de l'appli.** Dans Telegram touche la loupe 🔍 en haut et cherche **Dispensa Leo**.
3. Touche **Démarrer** (ou écris `/start`). **Cette étape est importante :** si tu ne la fais pas, le bot ne peut pas t'écrire.
4. **Trouve ton numéro (Chat ID).** Cherche le bot **@userinfobot**, ouvre-le et touche **Démarrer** : il te répond avec ton **Id**, un nombre (par exemple `123456789`). Garde le doigt appuyé pour le copier. C'est un bot gratuit qui te donne seulement ce nombre.
5. **Reviens sur cette page.** Ouvre **🔔 Scegli come ricevere gli avvisi**, coche **📱 Telegram**, colle le nombre dans le champ **Chat ID** (chiffres seulement) et touche **Salva**.
6. **C'est fait.** Les alertes arrivent de ce bot, à partir du prochain envoi automatique (en général le lendemain matin).

**Si rien n'arrive :** vérifie d'avoir touché *Démarrer* dans le bot (étape 3) et que le nombre est juste, sans espaces ni lettres.

### ✉️ E-mail
**Pour l'e-mail c'est très simple : ton adresse suffit.** Pas de mot de passe ni d'autres réglages.

1. Ouvre **🔔 Scegli come ricevere gli avvisi**.
2. Coche **✉️ Email**.
3. Écris **ton adresse e-mail** dans le champ (par exemple `nom@gmail.com`) et vérifie qu'elle est juste.
4. Touche **Salva**.

Les messages partent de l'adresse e-mail de l'appli. **La première fois regarde aussi dans Spam ou Promotions** et, si tu le trouves là, marque-le comme « Pas un spam » : à partir de là il arrivera dans la boîte normale.

### 💬 SMS
Ils sont payants et en général pas actifs : demande à l'administrateur.

Facultatif : coche **« Nei messaggi non scrivere i nomi dei medicinali »** (ne pas écrire les noms des médicaments dans les messages) si tu veux plus de confidentialité.

Le chef de famille, dans le même formulaire, peut aussi activer le résumé quotidien de la famille et l'alerte quand une personne n'enregistre pas une prise dans les 90 minutes. Les ordonnances bientôt périmées envoient des alertes à 14, 7, 3 et 1 jours et le jour même.""",
        "alertes notifications telegram chat id bot demarrer start userinfobot email sms rappel message recevoir activer numero gmail spam"),
    "f_report": ("🧾 Rapport complet et données",
        """Dans **🧾 I miei dati personali e report completo** écris nom et prénom et télécharge un **rapport à imprimer** avec tout ce que tu as saisi. Le fichier **JSON** contient les mêmes données pour une copie de sauvegarde.
Il contient des données de santé : ne le partage pas avec ceux qui ne doivent pas le voir.""",
        "rapport complet imprimer exporter telecharger donnees personnelles copie pdf json"),

    "u_cosa": ("🧰 À quoi sert la page Utilitaires",
        """Elle rassemble des **applis et sites utiles** au même endroit. Chacun a un grand **bouton qui pulse** : touche-le et il démarre.

Sous le bouton il y a le **nom** de l'appli : en le touchant s'ouvre la **notice**, une explication simple de ce qu'elle fait et de ses avantages.

Pour l'instant il y a **Velocity Music** (le play bleu clair) et **Wimbi** (le canard avec casque) ; d'autres utilitaires s'ajouteront ici.""",
        "utilitaires page applis boutons demarrer collection sites qu'est-ce a quoi ca sert"),
    "u_avviare": ("▶️ Comment démarrer une appli",
        """1. Depuis l'Accueil touche l'icône **🧰 Utilità** (à côté de Farmacia et I miei documenti).
2. Touche le **grand bouton** avec le symbole ▶️ : l'appli s'ouvre dans un nouvel onglet du navigateur.
3. Pour revenir ici, ferme cet onglet ou reviens en arrière.""",
        "demarrer ouvrir lancer play bouton appli lien velocity music musique"),
    "u_bugiardino": ("📖 Comment lire la notice",
        """1. Sous le bouton il y a la **plaque avec le nom** de l'appli.
2. **Touche-la** : une fenêtre s'ouvre avec l'explication (ce que c'est, avantages, adresse).
3. À l'intérieur il y a aussi le bouton **🎵 Avvia** pour ouvrir l'appli.
4. Pour fermer la fenêtre touche la **X** en haut.""",
        "notice explication plaque nom lire description avantages informations"),
    "u_wimbi": ("🦆 Wimbi",
        """Wimbi est une appli de musique : **tu écris une chanson ou un artiste, tu touches un résultat et ça joue**. Pas besoin de s'inscrire, les playlists restent sur ton appareil, la musique **continue à jouer écran éteint** et l'appli est disponible en **17 langues**.

Touche le **canard avec casque** pour la démarrer, ou l'écriture verte **Wimbi** pour lire la notice complète.
Adresse : https://wimbi.app/it/""",
        "wimbi canard casque musique chansons artiste playlist ecran eteint langues sans compte"),
    "u_velocity": ("🎵 Velocity Music",
        """C'est un lecteur et gestionnaire de musique qui permet d'écouter **gratuitement** la bibliothèque YouTube, **sans publicité** et **sans abonnement**. On peut l'utiliser **en invité**, sans créer de compte. Le projet est encore en développement mais déjà utilisable.

Adresse : https://velocitymusic.uk/""",
        "velocity music youtube gratuit publicite lecteur chansons ecouter radio"),

    "x_cosa": ("🚀 À quoi servent « Mes documents »",
        """Ici tu ranges tes **documents personnels** (carte d'identité, permis, passeport, carte vitale, titres de séjour, assurances…) avec les **photos recto et verso** et les **échéances**.

L'appli te prévient **6 mois avant** (première alerte, orange) et **3 mois avant** (deuxième alerte, rouge et plus intense), pour que tu aies le temps de les renouveler.""",
        "documents qu'est-ce a quoi ca sert carte identite permis passeport carte vitale commencer introduction"),
    "x_aggiungere": ("➕ Comment ajouter un document",
        """1. Choisis à qui est le document dans **👤 Documenti di**.
2. Touche **➕ Aggiungi un documento**.
3. Choisis le **type** dans la liste. S'il n'y est pas, écris-le dans la case **« Non lo trovi? »**.
4. Écris **numéro**, **délivré par**, **date de délivrance** et **date d'expiration**. S'il n'expire jamais, coche **« Questo documento non scade »**.
5. Fais la **photo recto et verso** (voir le guide ci-dessous).
6. Touche **💾 Salva il documento**.""",
        "ajouter inserer nouveau document type numero delivre expiration n'expire pas enregistrer"),
    "x_foto": ("📷 Photo recto et verso (fond enlevé et redressée)",
        """Il y a **deux blocs identiques : 📄 Fronte (Recto) et 📄 Retro (Verso)**. Pour chacun :
1. Touche **📷 Scatta la foto** (appareil arrière) **ou** **📁 Carica dal telefono** si tu as déjà la photo.
2. L'appli enlève le **fond** et **redresse** le document toute seule.
3. En dessous apparaît l'**éditeur** : glisse la **règle** pour tourner et le **cadre** pour recadrer.
4. Quand elle est parfaite touche **💾 Salva posizione e ritaglio**.
5. Si le document a été mal découpé coche **« Tieni anche lo sfondo »** : l'image reste entière et tu l'ajustes seulement à la main.
6. Si tu t'es trompé de photo touche **🗑️ Togli questa foto**.
7. À la fin touche **💾 Salva il documento** : les photos sont enregistrées avec les données.

Pour un **PDF** ou d'autres pages utilise le champ **« Altri file »** sous le formulaire.""",
        "photo prendre recto verso importer recadrer fond redresser tourner regle cadre image document"),
    "x_colori": ("🎨 Les couleurs et les alertes de péremption",
        """- 🟢 **Vert** : expire dans plus de 6 mois.
- 🟠 **Orange, première alerte** : expire dans moins de 6 mois.
- 🔴 **Rouge, deuxième alerte** : expire dans moins de 3 mois. Un encadré d'alarme apparaît.
- ⚫ **Expiré** : à renouveler tout de suite.

En haut tu vois les compteurs. Si tu as activé **Telegram** ou l'**e-mail** (cela se fait dans la Pharmacie, dans **Scegli come ricevere gli avvisi**), les alertes arrivent aussi là.""",
        "couleurs peremption alertes orange rouge expire six mois trois mois renouveler alarme telegram email"),
    "x_cercare": ("🔎 Chercher et filtrer les documents",
        """Au-dessus de la liste il y a le champ **Chercher** : écris le type, le numéro, l'organisme ou une note. À côté choisis une **catégorie** pour voir seulement ceux-là.""",
        "chercher recherche trouver filtre categorie liste"),
    "x_modificare": ("✏️ Modifier, ouvrir et supprimer",
        """- **Ouvrir un document :** touche sa **fiche colorée** : le détail s'ouvre avec toutes les données.
- **Voir recto et verso :** dans le détail touche **👁️ Mostra fronte e retro** (Afficher recto et verso) : tu les vois en grand et tu peux les **télécharger**.
- **Modifier :** dans le détail touche **✏️ Modifica**, change les données ou ajoute d'autres photos, puis enregistre.
- **Retirer une seule photo :** dans Modifica, dans la liste **Già allegato**, touche 🗑️ à côté du fichier.
- **Supprimer le document :** dans le détail touche **🗑️ Elimina** et confirme.""",
        "modifier changer supprimer effacer ouvrir piece jointe telecharger retirer photo"),
    "x_tipi": ("⚙️ Les types de document",
        """En bas de la page ouvre **⚙️ Gestisci i tipi di documento** : tu peux **ajouter** tes types, les **retirer** ou **masquer** ceux que tu n'utilises pas.""",
        "types type categories nouveau type masquer catalogue"),
    "x_privacy": ("🔒 Confidentialité",
        """Les documents contiennent des données personnelles : **ne partage pas** de captures ou de fichiers avec ceux qui ne doivent pas les voir. Chaque personne ne voit que les siens.""",
        "confidentialite securite donnees personnelles partager"),

    "tour1": ("Bienvenue !", "Bonjour, je suis ton assistant. Je te fais une visite rapide de l'appli. Avec les boutons Suivant et Retour tu avances à ton rythme, et tu peux m'arrêter quand tu veux."),
    "tour2": ("Le Garde-manger", "Dans le Garde-manger tu gardes la liste de ce que tu as à la maison. Touche Ajouter, photographie le produit, écris le nom et la péremption. Les couleurs te disent quand agir : vert tranquille, orange sous deux mois, rouge sous un mois."),
    "tour3": ("Allergènes et ingrédients", "Si tu choisis tes allergies dans le menu de gauche, les produits dangereux pour toi se reconnaissent tout de suite et une sirène apparaît. Sur chaque fiche le bouton Ingrédients montre la composition."),
    "tour4": ("La Pharmacie", "Avec la première icône tu entres dans la Pharmacie : médicaments avec péremption, traitements avec rappels sur Telegram ou e-mail, visites, vaccins et un profil pour chaque membre de la famille."),
    "tour5": ("Carte santé", "Dans la Pharmacie, à côté de la médecin, il y a le badge bleu clair de la carte santé : il montre recto et verso et te laisse enregistrer les liens vers le dossier santé, les vaccinations et les frais déductibles."),
    "tour6": ("Mes documents", "Avec la deuxième icône tu entres dans Mes documents. Prends le document en photo : l'appli enlève le fond, le redresse et essaie de lire type, numéro et échéance. Tu peux toujours corriger les champs. Elle te prévient six et trois mois avant l'échéance."),
    "tour7": ("Les Utilitaires", "Avec la troisième icône tu entres dans les Utilitaires : des applis utiles comme Velocity Music et Wimbi. Touche le bouton pour les démarrer et le nom pour lire la notice."),
    "tour8": ("Une aide toujours à portée de main", "En haut de chaque page il y a le bouton rouge Touche pour les infos, avec le guide et la recherche. Et moi je suis là : touche-moi quand tu veux, même avec le micro. Si je ne te sers pas, tu me désactives depuis le panneau, et tu me réactives depuis le bouton rouge. Bon travail !"),

    "nov1": ("Assistant numérique", "Le petit robot rond en bas à droite : touche-le et il t'explique l'appli à voix haute, même avec le micro"),
    "nov2": ("Nouvel utilitaire : Wimbi", "Accueil → Utilitaires → le canard avec casque ; touche l'écriture verte pour la notice"),
    "nov3": ("Nouvelle page « Utilitaires »", "Accueil → troisième icône bleu clair « Utilità », à côté de Farmacia et I miei documenti"),
    "nov4": ("Un guide sur chaque page", "Bouton rouge « Touche pour les infos » en haut, avec explications et recherche"),
    "nov5": ("Carte santé et dossier santé", "Pharmacie → badge bleu clair à côté de la médecin"),
    "nov6": ("Documents : photo et lecture automatique", "Mes documents → « Aggiungi un documento »"),
}

UI_TR["fr"] = {
    "dlg_titolo": "📖 Guide et informations",
    "dlg_hint": "Touche un sujet pour l'ouvrir. Ou écris ci-dessous ce que tu veux savoir.",
    "dlg_cerca_label": "🔎 Que veux-tu savoir ?",
    "dlg_cerca_ph": "ex. comment prendre en photo le verso du document",
    "dlg_trovato": "**Voici ce que j'ai trouvé :**",
    "dlg_nulla": "Je n'ai pas trouvé de réponse avec ces mots. Essaie de l'écrire autrement (par exemple un seul mot : *photo*, *péremption*, *mot de passe*) ou écris une suggestion dans l'onglet Messages.",
    "dlg_tutti": "Tous les sujets",
    "dlg_nota_it": "ℹ️ Les écrans de cette section sont pour l'instant en italien : les noms des boutons sont écrits comme tu les vois à l'écran.",
    "dlg_asst": "**🤖 Assistant numérique** (le petit robot qui parle et t'aide)",
    "dlg_on": "✅ Activer", "dlg_off": "⛔ Désactiver",
    "info_help": "Touche pour lire comment utiliser cette section", "info_fallback": "ℹ️ Informations et guide",
    "sez_dispensa": "🏠 Garde-manger", "sez_farmacia": "🏥 Pharmacie", "sez_documenti": "📁 Mes documents", "sez_utilita": "🧰 Utilitaires",
    "a_aria": "Assistant numérique", "a_rileggi": "📖 Explique-moi cette page", "a_giro": "🧭 Visite guidée de l'appli",
    "a_novita": "🆕 Quoi de neuf", "a_mic": "🎤 Pose une question", "a_indietro": "◀ Retour", "a_avanti": "Suivant ▶", "a_fine": "Fin",
    "a_ph": "Écris ici ta question…", "a_chiedi": "Demander", "a_voce_on": "🔊 Voix : activée", "a_voce_off": "🔇 Voix : coupée",
    "a_silenzio": "⏹ Silence", "a_off": "⛔ Désactiver l'assistant", "a_ascolto_btn": "⏹ J'écoute…",
    "a_ascolto_t": "Je t'écoute", "a_ascolto_x": "Parle maintenant : par exemple « comment ajouter une photo au document ? »",
    "a_mic_t": "Micro", "a_mic_no": "Sur ce téléphone je ne peux pas t'écouter : écris la question ci-dessous.",
    "a_mic_perm": "Autorise le navigateur à utiliser le micro pour me parler.",
    "a_mic_err": "Je ne peux pas utiliser la voix maintenant : écris la question ci-dessous.",
    "a_nulla_t": "Je n'ai rien entendu", "a_nulla_x": "Réessaie : touche le micro et parle.",
    "a_dimmi_t": "Dis-moi", "a_dimmi_x": "Écris ou dis ce que tu veux savoir.",
    "a_off_t": "Veux-tu que je me désactive ?",
    "a_off_x": "Touche le bouton « ⛔ Désactiver l'assistant » ci-dessous. Tu me réactives depuis le bouton rouge « Touche pour les infos ».",
    "a_trov_t": "Je n'ai pas trouvé la réponse",
    "a_trov_x": "Essaie avec d'autres mots (par exemple un seul : photo, péremption, mot de passe) ou choisis un sujet ci-dessous.",
    "a_nov_none_t": "Nouveautés", "a_nov_none_x": "Pour l'instant il n'y a pas de nouveautés récentes. Je te préviens quand il y en aura !",
    "a_nov_voce": "Voici les nouveautés.", "a_nov_trovi": "Tu la trouves ainsi :", "a_nov_t": "Quoi de neuf",
    "a_fine_t": "Fin de la visite", "a_fine_x": "Voilà ! Si tu as besoin d'autre chose, demande-moi.",
    "a_toast_off": "Assistant désactivé. Tu le réactives depuis « Touche pour les infos ».", "a_toast_on": "Assistant activé : touche le petit robot.",
    "a_vedi": "Touche un sujet ci-dessous pour en savoir plus.",
    "i_silenzio": "silence tais stop arrete assez", "i_off": "desactiv eteins arret", "i_ass": "assistant robot",
    "i_novita": "nouveaute nouveau nouvelle neuf mise a jour", "i_giro": "visite tutoriel guide commenc", "i_saluto": "bonjour salut bonsoir coucou aide",
}
