# -*- coding: utf-8 -*-
"""Frasi della lista della spesa e del tasto 'Ne ho consumato uno' (en, es, fr, de, ro, ar).
Il nome inizia con 'lingue_' e viene dopo lingue9.py, quindi non viene sovrascritto."""

_CHIAVI = [
    "Spesa",
    "Lista della spesa",
    "I prodotti finiti (0 unità) arrivano qui da soli. Quando li aggiungi di nuovo in dispensa escono dalla lista.",
    "Cosa devi comprare?",
    "Aggiungi alla lista",
    "Scrivi cosa devi comprare.",
    "È già nella lista.",
    "La lista della spesa è vuota.",
    "Preso",
    "Togli quelli presi",
    "Ne ho consumato uno",
    "Ne ho consumato uno: restano {n} unità.",
    "{nome} è finito: l'ho messo nella lista della spesa.",
    "{nome}: questa scadenza è finita, ma hai ancora altre unità in dispensa.",
]

_FRASI = {
    "en": ["Shopping", "Shopping list",
           "Finished products (0 units) appear here automatically. When you add them to the pantry again they leave the list.",
           "What do you need to buy?", "Add to list", "Write what you need to buy.", "It's already on the list.",
           "The shopping list is empty.", "Bought", "Remove the bought ones", "I used one",
           "I used one: {n} units left.", "{nome} is finished: I put it on the shopping list.",
           "{nome}: this expiry date is used up, but you still have other units in the pantry."],
    "es": ["Compra", "Lista de la compra",
           "Los productos terminados (0 unidades) llegan aquí solos. Cuando los añades de nuevo a la despensa salen de la lista.",
           "¿Qué tienes que comprar?", "Añadir a la lista", "Escribe qué tienes que comprar.", "Ya está en la lista.",
           "La lista de la compra está vacía.", "Comprado", "Quitar los comprados", "He consumido uno",
           "He consumido uno: quedan {n} unidades.", "{nome} se ha terminado: lo he puesto en la lista de la compra.",
           "{nome}: esta caducidad se ha agotado, pero aún tienes otras unidades en la despensa."],
    "fr": ["Courses", "Liste de courses",
           "Les produits terminés (0 unité) arrivent ici automatiquement. Quand vous les ajoutez de nouveau au garde-manger, ils quittent la liste.",
           "Que devez-vous acheter ?", "Ajouter à la liste", "Écrivez ce que vous devez acheter.", "Il est déjà dans la liste.",
           "La liste de courses est vide.", "Acheté", "Retirer les produits achetés", "J'en ai consommé un",
           "J'en ai consommé un : il reste {n} unités.", "{nome} est terminé : je l'ai mis dans la liste de courses.",
           "{nome} : cette date limite est épuisée, mais il vous reste d'autres unités dans le garde-manger."],
    "de": ["Einkauf", "Einkaufsliste",
           "Aufgebrauchte Produkte (0 Einheiten) erscheinen hier automatisch. Wenn du sie wieder in die Vorratskammer legst, verschwinden sie aus der Liste.",
           "Was musst du kaufen?", "Zur Liste hinzufügen", "Schreibe, was du kaufen musst.", "Es steht schon auf der Liste.",
           "Die Einkaufsliste ist leer.", "Gekauft", "Gekaufte entfernen", "Ich habe eins verbraucht",
           "Ich habe eins verbraucht: Es bleiben {n} Einheiten.", "{nome} ist aufgebraucht: Ich habe es auf die Einkaufsliste gesetzt.",
           "{nome}: Dieses Ablaufdatum ist aufgebraucht, aber du hast noch weitere Einheiten in der Vorratskammer."],
    "ro": ["Cumpărături", "Lista de cumpărături",
           "Produsele terminate (0 unități) apar aici automat. Când le adaugi din nou în cămară, ies din listă.",
           "Ce trebuie să cumperi?", "Adaugă în listă", "Scrie ce trebuie să cumperi.", "Este deja în listă.",
           "Lista de cumpărături este goală.", "Cumpărat", "Elimină produsele cumpărate", "Am consumat unul",
           "Am consumat unul: au rămas {n} unități.", "{nome} s-a terminat: l-am pus în lista de cumpărături.",
           "{nome}: această dată de expirare s-a terminat, dar mai ai alte unități în cămară."],
    "ar": ["التسوق", "قائمة التسوق",
           "تظهر هنا المنتجات المنتهية (0 وحدات) تلقائيًا. وعند إضافتها مجددًا إلى المخزن تخرج من القائمة.",
           "ماذا تريد أن تشتري؟", "أضف إلى القائمة", "اكتب ما تريد شراءه.", "موجود بالفعل في القائمة.",
           "قائمة التسوق فارغة.", "تم الشراء", "احذف ما تم شراؤه", "استهلكتُ واحدة",
           "استهلكتُ واحدة: بقيت {n} وحدات.", "انتهى {nome}: وضعته في قائمة التسوق.",
           "{nome}: انتهت هذه الدفعة، لكن لا تزال لديك وحدات أخرى في المخزن."],
}
for _lg, _liste in _FRASI.items():
    assert len(_liste) == len(_CHIAVI), _lg
    TRADUZIONI.setdefault(_lg, {}).update(dict(zip(_CHIAVI, _liste)))
