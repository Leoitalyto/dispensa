# -*- coding: utf-8 -*-
"""Frasi del bugiardino (en, es, fr, de, ro, ar). Caricato con gli altri lingue*.py."""

_CHIAVI = ["Bugiardino del prodotto", "Altre informazioni", "Classificazione automatica dagli ingredienti: controlla sempre l’etichetta."]

_FRASI = {
    "en": ["Product leaflet", "Other information", "Automatic classification from the ingredients: always check the label."],
    "es": ["Prospecto del producto", "Otra información", "Clasificación automática según los ingredientes: comprueba siempre la etiqueta."],
    "fr": ["Notice du produit", "Autres informations", "Classification automatique d'après les ingrédients : vérifiez toujours l'étiquette."],
    "de": ["Produktinformation", "Weitere Informationen", "Automatische Einstufung anhand der Zutaten: Prüfe immer das Etikett."],
    "ro": ["Prospectul produsului", "Alte informații", "Clasificare automată după ingrediente: verifică întotdeauna eticheta."],
    "ar": ["نشرة المنتج", "معلومات أخرى", "تصنيف تلقائي حسب المكونات: تحقق دائمًا من الملصق."],
}
for _lg, _liste in _FRASI.items():
    assert len(_liste) == len(_CHIAVI), _lg
    TRADUZIONI.setdefault(_lg, {}).update(dict(zip(_CHIAVI, _liste)))
