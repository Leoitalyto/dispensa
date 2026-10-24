# -*- coding: utf-8 -*-
"""Frasi dei pulsanti allergeni interattivi e dell'avviso all'inserimento (en, es, fr, de, ro, ar).
Il nome inizia con 'lingue_' e viene dopo lingue9.py nell'ordine di caricamento, cosi' non viene sovrascritto."""

_K_COMP = "Composizione del prodotto"
_K_MANCA = "Ingredienti non disponibili: controlla l'etichetta sulla confezione."
_K_ATT = "Attenzione: questo prodotto può dare allergie"
_K_CHIUDI = "Tocca ✕ per chiudere"
_K_CAPITO = "Ho capito"
_K_FEDE = "Fa fede sempre l'etichetta sulla confezione."
_K_PULSANTI = ("**Pulsanti degli allergeni:** i prodotti che possono dare allergie hanno un pulsante giallo con il nome "
               "dell'allergene (per esempio Glutine). Toccalo: si apre una schermata con la composizione e gli ingredienti "
               "del prodotto. Lo stesso avviso compare subito quando inserisci un prodotto.")

_NUOVE = {
    "en": {
        _K_COMP: "Product composition",
        _K_MANCA: "Ingredients not available: check the label on the package.",
        _K_ATT: "Warning: this product may cause allergies",
        _K_CHIUDI: "Tap ✕ to close",
        _K_CAPITO: "Got it",
        _K_FEDE: "The label on the package always prevails.",
        _K_PULSANTI: "**Allergen buttons:** products that may cause allergies have a yellow button with the allergen's name "
                     "(for example Gluten). Tap it: a screen opens with the product's composition and ingredients. "
                     "The same warning appears right away when you add a product.",
    },
    "es": {
        _K_COMP: "Composición del producto",
        _K_MANCA: "Ingredientes no disponibles: revisa la etiqueta del envase.",
        _K_ATT: "Atención: este producto puede provocar alergias",
        _K_CHIUDI: "Toca ✕ para cerrar",
        _K_CAPITO: "Entendido",
        _K_FEDE: "Manda siempre la etiqueta del envase.",
        _K_PULSANTI: "**Botones de alérgenos:** los productos que pueden provocar alergias tienen un botón amarillo con el "
                     "nombre del alérgeno (por ejemplo Gluten). Púlsalo: se abre una pantalla con la composición y los "
                     "ingredientes del producto. El mismo aviso aparece en cuanto añades un producto.",
    },
    "fr": {
        _K_COMP: "Composition du produit",
        _K_MANCA: "Ingrédients non disponibles : vérifiez l'étiquette sur l'emballage.",
        _K_ATT: "Attention : ce produit peut provoquer des allergies",
        _K_CHIUDI: "Touchez ✕ pour fermer",
        _K_CAPITO: "Compris",
        _K_FEDE: "L'étiquette sur l'emballage fait toujours foi.",
        _K_PULSANTI: "**Boutons d'allergènes :** les produits pouvant provoquer des allergies ont un bouton jaune avec le nom "
                     "de l'allergène (par exemple Gluten). Touchez-le : un écran s'ouvre avec la composition et les "
                     "ingrédients du produit. Le même avertissement s'affiche dès que vous ajoutez un produit.",
    },
    "de": {
        _K_COMP: "Zusammensetzung des Produkts",
        _K_MANCA: "Zutaten nicht verfügbar: Prüfe das Etikett auf der Verpackung.",
        _K_ATT: "Achtung: Dieses Produkt kann Allergien auslösen",
        _K_CHIUDI: "Tippe auf ✕ zum Schließen",
        _K_CAPITO: "Verstanden",
        _K_FEDE: "Maßgeblich ist immer das Etikett auf der Verpackung.",
        _K_PULSANTI: "**Allergen-Schaltflächen:** Produkte, die Allergien auslösen können, haben eine gelbe Schaltfläche mit "
                     "dem Namen des Allergens (zum Beispiel Gluten). Tippe darauf: Es öffnet sich ein Bildschirm mit der "
                     "Zusammensetzung und den Zutaten des Produkts. Dieselbe Warnung erscheint sofort, wenn du ein Produkt "
                     "hinzufügst.",
    },
    "ro": {
        _K_COMP: "Compoziția produsului",
        _K_MANCA: "Ingrediente indisponibile: verifică eticheta de pe ambalaj.",
        _K_ATT: "Atenție: acest produs poate provoca alergii",
        _K_CHIUDI: "Atinge ✕ pentru a închide",
        _K_CAPITO: "Am înțeles",
        _K_FEDE: "Eticheta de pe ambalaj este întotdeauna cea corectă.",
        _K_PULSANTI: "**Butoanele alergenilor:** produsele care pot provoca alergii au un buton galben cu numele alergenului "
                     "(de exemplu Gluten). Atinge-l: se deschide un ecran cu compoziția și ingredientele produsului. "
                     "Același avertisment apare imediat când adaugi un produs.",
    },
    "ar": {
        _K_COMP: "تركيبة المنتج",
        _K_MANCA: "المكوّنات غير متوفرة: تحقق من الملصق الموجود على العبوة.",
        _K_ATT: "تنبيه: قد يسبب هذا المنتج الحساسية",
        _K_CHIUDI: "المس ✕ للإغلاق",
        _K_CAPITO: "فهمت",
        _K_FEDE: "الملصق الموجود على العبوة هو المرجع دائمًا.",
        _K_PULSANTI: "**أزرار مسببات الحساسية:** المنتجات التي قد تسبب الحساسية لها زر أصفر عليه اسم المادة المسببة "
                     "للحساسية (مثل الغلوتين). المسه: تُفتح شاشة تعرض تركيبة المنتج ومكوّناته. يظهر التنبيه نفسه "
                     "فور إضافة منتج.",
    },
}
for _lg, _frasi in _NUOVE.items():
    TRADUZIONI.setdefault(_lg, {}).update(_frasi)
