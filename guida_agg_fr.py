# -*- coding: utf-8 -*-
"""Instructions mises à jour le 20/11/2026 — FRANÇAIS (voir guida_aggiornamento.py)."""

ga_traduci("fr", {
    "x_campanello": ("🔔 La clochette : alertes de cette section", """Dans chaque section, sous les boutons colorés, il y a **🔔 Alertes de cette section**. Touchez-la : une fenêtre indique **comment les alertes sont réglées** et **ce qui arrive à échéance**.

Vous pouvez y changer :
- **Recevoir les alertes de cette section** : l'interrupteur les active ou les désactive.
- **Combien de jours avant** : choisissez les jours (0 = le jour même).
- **Je choisis l'heure** : cochez, choisissez l'heure et appuyez sur **Entrée**. Sans heure choisie, les alertes arrivent le matin.
- **Où recevoir les alertes** : « comme les autres sections » ou choisissez parmi **Telegram, Email, WhatsApp, SMS**.
- **Calendrier** : activez « Voir aussi ces alertes dans le calendrier » et appuyez sur **Télécharger le calendrier** ; ouvrez le fichier, Android propose **Google Agenda**. Si une date change, téléchargez et ouvrez-le à nouveau (mis à jour, pas dupliqué).
- **Revenir comme avant** remet tout comme c'était.

Appuyez sur **💾 Enregistrer**. **D'abord**, écrivez vos coordonnées (Telegram, email, WhatsApp, SMS) dans **Santé → Choisir comment recevoir les alertes** : sans coordonnée ce canal ne part pas. Les alertes sont envoyées par un programme automatique : parfois avec quelques minutes de retard ; un message manqué est récupéré dans les 3 heures, une seule fois.""",
                     "clochette alertes jours heure canaux telegram email whatsapp sms son calendrier google agenda"),
    "x_riuso_archivio": ("🗂️ Réutiliser un fichier déjà dans l'archive", """Si vous avez déjà un fichier ou une photo dans l'archive, **pas besoin de les refaire** :
- **Santé** (visites, ordonnances, documents, vaccins) : sous « prendre ou choisir un fichier » il y a **🗂️ Ou joindre depuis l'archive**. Écrivez pour chercher, choisissez le fichier et enregistrez : le même fichier est utilisé, sans copie.
- **Maison, Travail (fiches de paie), Voiture, Animaux** : dans le cadre où vous chargez un fichier, ouvrez **🗂️ Ou choisir un fichier déjà dans l'archive**, choisissez-le et appuyez sur **📥 Utiliser ce fichier** : il est lu comme si vous veniez de le charger.
- **Garde-manger** (photo du produit) : **🗂️ Choisir dans l'archive** montre les photos déjà utilisées, même de produits terminés.""",
                         "archive réutiliser fichier photo déjà enregistré choisir dans l'archive joindre sans refaire"),
    "x_numeri_utili": ("📞 Numéros utiles et 📅 Rendez-vous", """Dans chaque section (sauf le Garde-manger), sous la clochette, il y a deux boutons.

**📞 Numéros utiles** est votre carnet d'adresses de ceux qui servent dans cette section : **nom, métier, domaine, téléphone du bureau et portable, horaires, site, email, adresse**.
- S'il y a des travaux, cochez **« Il y a un devis »** : état, montant, **dates de début et de fin** et le **PDF ou la photo du devis**.
- Dans **« Documents reçus »** mettez PDF, photos, factures, contrats.
- Avec **« Ouvrir devis, fichiers et paiements »** vous notez **acomptes, échéances et solde** et voyez ce qui est payé et ce qui reste.
- Il y a aussi des **Notes** et des boutons pour appeler, WhatsApp, email, ouvrir la carte ou le site.

**À qui sont-ils ?** Dans **Santé, Mes documents et Maison**, où l'on choisit une personne, numéros et rendez-vous sont **séparés par personne**.

**📅 Rendez-vous** : **nom, fonction, date, heure, téléphone, motif et notes**. En haut les **prochains**, par date ; les passés ou faits sont regroupés en bas. Avec **« Mettre dans le calendrier du téléphone »** le rendez-vous entre dans le calendrier avec un rappel.""",
                       "numéros utiles carnet rendez-vous devis paiements acompte solde contacts calendrier"),
    "x_conti_casa": ("💶 Tenir les comptes", """Dans **Maison** touchez **💶 Tenir les comptes**. Ajoutez autant de lignes que vous voulez : **comptes courants** (avec la banque), **Postepay**, **livrets postaux**, **BOT, BTP**, fonds, actions, bons postaux, espèces. Vous voyez le **total** en haut et en bas, les **sous-totaux** par type et un champ **Notes**. Pour les titres d'État vous pouvez noter l'échéance. **Chaque personne a ses comptes** : si dans Maison vous avez choisi, par exemple, votre mère, le bouton devient **« Comptes de … »**. Les comptes d'une personne ne se mélangent pas avec ceux des autres.""",
                     "comptes argent banque compte courant postepay épargne obligations btp bot total sous-total personne"),
    "x_badante": ("👵 Aide à domicile (administrateur seulement)", """Dans **Maison**, pour l'administrateur seulement, il y a **👵 Aide à domicile**.
- Réglez le **tarif** (en général 20 € pour 2 heures), les jours où elle vient et à partir de quel jour compter.
- Chaque jour touchez **✅ Venue** ou **❌ Pas venue** ; si le montant change utilisez **« Un autre jour ou un autre montant »**.
- Avec **« J'ai donné de l'argent à ma mère »** vous notez combien et quand.
- L'app calcule ce qui reste et **jusqu'à quand l'argent suffit**.
- **🔔 Alertes de l'aide à domicile** vous prévient **3 jours avant** et **le dernier jour** (jours modifiables).
- Il y a aussi les **contacts de l'aide** et des **notes**.""",
                  "aide à domicile badante heures tarif venue argent mère alertes"),
    "x_interruttori": ("💡 Sélecteurs interrupteurs", """Dans toute l'app les sélecteurs en pilule (pour choisir une personne, une maison, un véhicule…) fonctionnent comme des **interrupteurs** : celui qui est **actif est bleu néon et pulse**, les autres semblent **éteints**.""",
                       "interrupteur sélecteur pilule actif néon"),
    "x_ia": ("🤖 Intelligence artificielle : documents, écriture manuscrite, voyants, langues", """Avec les **clés** des services d'intelligence artificielle (gratuits : Groq, Google Gemini, OpenRouter, NVIDIA, Cloudflare, Cohere, Hugging Face, SambaNova avec crédit d'essai ; **DeepSeek** payant, facultatif) l'app :
- **lit et classe les documents médicaux** (quel document, domaine médical, examen, dates, médecin, établissement, conclusions). S'il est **manuscrit**, **plusieurs services** le lisent et un « arbitre » compare les lectures : vous voyez **qui l'a lu**, les **limites** et **ce qu'il faut vérifier** sur la feuille. Rien n'est enregistré sans votre confirmation ;
- **reconnaît les voyants de la voiture**, en comparant plusieurs lectures quand la photo est douteuse ;
- **traduit les pages** dans la langue choisie (la première fois qu'une page s'ouvre ; ensuite c'est enregistré pour tous) ;
- fait répondre **l'assistant** dans la langue choisie.
Si un service est épuisé ou lent, l'app passe toute seule au suivant.

**DeepSeek est payant** : seuls **l'administrateur** et les personnes qu'il choisit l'utilisent (Utilitaires → 🤖 → DeepSeek → **🔒 Qui peut l'utiliser**). La même ligne montre le **💰 crédit restant**. Les traductions automatiques n'utilisent jamais les services payants.

L'administrateur met les clés dans **Utilitaires → 🤖 Intelligence artificielle**, avec le guide pas à pas ; **🔄 Revérifier les clés** et le **test** de chaque service disent s'il fonctionne. Attention : avec les clés gratuites de Google les textes peuvent servir à améliorer leurs modèles.""",
             "intelligence artificielle ia clés gemini groq openrouter nvidia cloudflare cohere hugging face sambanova deepseek crédit qui peut l'utiliser manuscrit voyants traduction"),
    "x_compleanni": ("🎂 Anniversaires : les fiches des personnes", """Dans **Utilitaires → 🎂 Anniversaires** touchez le **badge « Joyeux anniversaire »** pour ouvrir la liste (touchez-le à nouveau pour la fermer).

- **➕ Ajouter une personne** : nom et date de naissance (si vous ne connaissez pas l'année cochez **« Je ne connais pas l'année »**). Le reste est facultatif : **photo, lieu de naissance, nom de famille, surnom, portable, téléphone, WhatsApp, Telegram, email, adresse, site, idées cadeaux, notes**. Dans **« Qui est-ce pour toi »**, si vous choisissez **Autre**, vous pouvez écrire vous-même le mot juste.
- **La photo** : touchez « Choisir la photo » ; **pincez à deux doigts** pour agrandir et **faites glisser** pour la déplacer jusqu'à ce que le visage soit dans l'ovale. Plus tard vous pouvez la **🔄 Recentrer**.
- Chaque personne a sa **fiche au cadre néon** de la couleur de son **signe du zodiaque**, choisi d'après la date. **Les signes bougent** (le Bélier donne un coup de tête avec des yeux de feu, les Poissons nagent lentement, le Cancer marche de côté…).
- Sous la fiche il y a des boutons pour **appeler, WhatsApp, Telegram, email, site**. La liste suit le **prochain anniversaire** (« 🎉 Aujourd'hui ! » si c'est aujourd'hui).
- Si **la personne n'est plus là**, cochez **🕯️ Cette personne n'est plus là** : une **bougie allumée** apparaît, la fiche passe dans **En mémoire** et vous trouvez **⚰️ Où elle repose** (type de sépulture, cimetière, emplacement, concession, lampe votive, téléphone et horaires du cimetière, photos de la pierre tombale), la **prière du repos éternel**, **✍️ une pensée** et **🎙️ un message vocal**.
- Le **bouton vert ⏻** dans la fiche ouvre le **📖 Journal des souvenirs** (voir sa fiche).
- ✏️ **Modifier** change les données (ce que vous ne touchez pas reste comme avant) ; 🗑️ **Supprimer** envoie la fiche à la Corbeille.""",
                     "anniversaires anniversaire signe zodiaque fiche personne photo contacts whatsapp telegram décédé bougie mémoire sépulture journal"),
    "x_diario": ("📖 Le Journal des souvenirs (photos, textes, musique)", """Dans la fiche de chaque personne des **🎂 Anniversaires**, en bas à droite, il y a le **bouton vert ⏻**. Touchez-le : **la fiche disparaît et le journal s'ouvre**, avec les photos empilées comme les pages d'un livre.

- **Tourner les pages** : **◀ Précédent** et **Suivant ▶** en haut. Le **bouton rouge ⏻**, entre les deux, ferme le journal et la fiche revient.
- **Défilement automatique** : les photos passent seules toutes les **7 secondes** ; dans **⏱️ Défilement automatique** choisissez les secondes ou arrêtez-le. Chaque photo **entre et sort avec un effet toujours différent**.
- **Ajouter des photos** : **➕ Ajouter d'autres photos** (autant que vous voulez, pas de limite). Pour chaque photo vous voyez un **aperçu** : **pincez** à deux doigts pour agrandir et **faites glisser** pour déplacer ; vous pouvez écrire des **textes colorés** (couleur, police, taille, position) et placer des **icônes** (cœurs, fleurs, bougies…). Puis **💾 Enregistrer la page**. Les photos sont allégées automatiquement sans perte de qualité.
- **Changer plus tard** : avec **✏️ Textes et icônes** vous enlevez ou changez textes et icônes quand vous voulez ; **↩️ Annuler la dernière modification** remet comme avant (la photo d'origine n'est jamais touchée). Dans **🗂️ Gérer les pages** vous déplacez une page **⬆️ ⬇️**, **🔄 changez la photo** ou la **🗑️ supprimez**.
- **Musique** : dans **🎵 Musique du journal** choisissez un fichier **MP3** (il s'enregistre tout seul). Elle démarre quand vous touchez le bouton vert ; en bas la **barre du volume** (toucher ou faire glisser) et ▶/🔊 pour la pause. Pour la changer, choisissez un autre fichier.""",
                 "journal des souvenirs journal photos pages bouton vert rouge défilement musique mp3 volume textes icônes effets gérer les pages anniversaires"),
    "f_ia_documenti": ("🤖 Faire relire et reclasser les documents par l'IA", """Dans **Santé → Documents médicaux** ouvrez **🤖 Reclasser les documents avec l'IA**.

1. Vous voyez **« À contrôler : X sur Y »** : l'IA lit **seulement les documents pas encore contrôlés** (cochez « Relire aussi ceux déjà contrôlés » pour tout relire).
2. Touchez **🔍 Essai : lire et classer**. Un **cadre toujours ouvert** apparaît et se met à jour tout seul : document atteint, depuis combien de secondes, quel service est interrogé, combien sont lus, combien de temps il reste. Les points **●●●○** qui bougent indiquent qu'elle travaille.
3. **Vous pouvez utiliser d'autres apps ou éteindre l'écran** : la lecture continue toute seule. Chaque document est enregistré dès qu'il est lu, rien ne se perd.
4. Un document bloqué est **sauté après environ 2 minutes** (« trop lent, sauté ») et réessayé la fois suivante. **⏹ Arrêter la lecture** garde ceux déjà lus.
5. Les **🟡 Propositions de l'IA à confirmer** apparaissent dans le même cadre, une par document : laissez coché ce qui est juste et touchez **✅ Appliquer** ; **✖ Ne pas appliquer** laisse tout tel quel. Ce que vous avez corrigé à la main n'est jamais touché.

**🔄 Relire les documents déjà archivés** (lecture sans IA) montre aussi **« À relire : X sur Y »** et ne repropose pas ceux déjà faits.""",
                       "reclasser documents ia intelligence artificielle relire lecture en cours propositions appliquer contrôlés arrière-plan autres apps arrêter"),
    "f_numeri_doc": ("🔢 Le N° des documents médicaux (pour le médecin)", """Chaque document médical a un **numéro** : le **N° 1 est le plus récent**, puis en descendant jusqu'au plus ancien. Vous le voyez dans un **cadre vert** sur chaque fiche et dans la colonne **N°** du **récapitulatif PDF** de la Santé.

**À quoi ça sert :** donnez le récapitulatif au médecin ; il vous dit « apportez-moi le 4, le 12 et le 17 ». Écrivez le numéro (par exemple **12**) dans la case **🔍 Rechercher** des Documents médicaux et **seul ce document** apparaît.

**Attention :** quand vous ajoutez un nouveau document, il devient le N° 1 et les autres **descendent d'un rang**. Si entre-temps vous avez ajouté des documents, **refaites le récapitulatif PDF**. Dans le PDF les dates ne sont plus coupées sur deux lignes.""",
                     "numéro documents n° médecin récapitulatif pdf rechercher numéro ordre plus récent apportez-moi"),
    "f_gruppo": ("🩸 Groupe sanguin et certificat", """Dans la fiche de la personne en **Santé** : si le groupe sanguin manque, touchez **🩸 Saisir le groupe sanguin**, choisissez-le et enregistrez. Vous pouvez le changer quand vous voulez avec **Modifier**.

En dessous vous pouvez **joindre le certificat du groupe sanguin** (PDF ou photo) : choisissez le fichier, il s'enregistre tout seul. Vous le voyez, le téléchargez ou l'enlevez quand vous voulez.""",
                 "groupe sanguin sang certificat joindre pdf photo fiche personne"),
    "f_wiki": ("📖 « Qu'est-ce que c'est ? » : explication simple de Wikipédia", """Dans **Santé → Documents médicaux** et dans **Santé → Médicaments** il y a le menu **📖 Qu'est-ce que c'est ? Explication simple (Wikipédia)**.

Écrivez le nom d'un **examen, d'une maladie ou d'un médicament** (par exemple *écho-doppler*, *duloxétine*) : s'il y a plusieurs articles choisissez le bon et lisez **deux lignes d'explication**, dans la langue de l'app, avec le bouton pour ouvrir la page complète.

C'est une **information générale**, gratuite : **ce n'est pas un avis médical**. Pour votre situation demandez toujours au médecin ou au pharmacien.""",
               "qu'est-ce que c'est explication wikipédia examen maladie médicament signification mot compte rendu"),
    "x_meteo": ("🌦️ Alertes météo utiles", """Des alertes **seulement quand il le faut**, en haut des sections :
- **Santé** : **forte chaleur** (boire souvent, ne pas sortir de 11 h à 17 h, attention aux personnes âgées et aux enfants) et **froid intense** ;
- **Voiture** : **gel** (glace sur le pare-brise et les routes), **fortes pluies**, **rafales de vent** ;
- **Animaux** : **chaleur** (promenades tôt ou le soir, asphalte brûlant, eau fraîche, jamais dans la voiture) et **froid**.

**Pour les activer :** **Utilitaires → 🌦️ Alertes météo** → écrivez votre ville → choisissez la bonne → **💾 Utiliser cette ville**. Vous y voyez aussi les températures des prochains jours et vous pouvez **désactiver** les alertes. Chacun choisit sa ville.

Les prévisions viennent d'**Open-Meteo** : gratuit, sans clé ni inscription, pour un usage non commercial.""",
                "météo alertes chaleur froid gel pluie vent ville prévisions open-meteo"),
    "x_voci_libere": ("✍️ Un nom de votre choix dans les listes avec « Autre »", """Dans les listes déroulantes qui ont l'option **Autre** (types de document, pièces, espèces d'animaux, sépultures, rôles des médecins, catégories de copropriété, modes de paiement, « Qui est-ce pour toi », documents INPS…) :
1. choisissez **Autre** ;
2. **✍️ Pas dans la liste ? Écrivez le nom que vous voulez** apparaît : écrivez le nom exact (par exemple **Ecocert**) ;
3. enregistrez comme d'habitude : **votre nom** est enregistré, pas « Autre ».

Dans les fiches avec le bouton de confirmation en bas, la case est toujours là, sous la liste, et ne compte que si vous avez choisi « Autre ». **Le nom reste dans la liste** : la prochaine fois vous le retrouvez, avant « Autre ».""",
                      "autre nom au choix liste déroulante écrire nom option personnalisée ecocert pas dans la liste"),
    "x_lingua": ("🌐 La langue de l'app", """**On entre dans la langue que l'on voit sur la page de connexion.** Si vous voulez une autre langue, choisissez-la dans le menu **🌐 Lingua / Language** avant de toucher **Entrer** : elle reste enregistrée.

Le téléphone se souvient de la **dernière langue utilisée** : la fois suivante la page de connexion s'ouvre déjà dans cette langue. Dans l'app la langue se change depuis le menu **☰** en haut à gauche.

Toutes les pages sont dans la langue choisie : les phrases nouvelles se traduisent toutes seules la première fois qu'une page s'ouvre (environ une minute), puis restent enregistrées pour tous. **L'assistant** répond aussi dans la langue choisie.""",
                 "langue italien anglais espagnol français allemand roumain arabe portugais changer de langue connexion traduction"),
}, {
    "nv_diario": ("Journal des souvenirs", "Utilitaires → 🎂 Anniversaires → bouton vert ⏻ dans la fiche : photos, textes, icônes, musique"),
    "nv_ia": ("Documents lus par l'IA", "Santé → Documents médicaux → 🤖 Reclasser : fonctionne même si vous utilisez d'autres apps"),
    "nv_numeri": ("N° des documents", "Santé → Documents médicaux : le N° 1 est le plus récent ; recherche par numéro"),
    "nv_meteo": ("Alertes météo", "Utilitaires → 🌦️ Alertes météo : choisissez votre ville"),
    "nv_wiki": ("Qu'est-ce que c'est ?", "Santé → Documents médicaux et Médicaments : explication simple de Wikipédia"),
    "nv_altro": ("Noms au choix", "Dans les listes avec « Autre » : écrivez le nom que vous voulez"),
})
