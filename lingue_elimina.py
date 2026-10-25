# -*- coding: utf-8 -*-
"""Frasi del cestino e della finestra 'Elimina dalla dispensa' (en, es, fr, de, ro, ar)."""

_CHIAVI = [
    "Elimina",
    "Elimina dalla dispensa",
    "Questo prodotto ha {n} voci con scadenze diverse: scegli quali eliminare.",
    "Metti nella lista della spesa",
    "Elimina le voci scelte",
    "Annulla",
    "Elimina le righe spuntate",
    "Eliminato dalla dispensa.",
    "Spunta almeno una voce da eliminare.",
]

_FRASI = {
    "en": ["Delete", "Remove from pantry", "This product has {n} entries with different expiry dates: choose which ones to delete.",
           "Put on the shopping list", "Delete the selected entries", "Cancel", "Delete the ticked rows",
           "Removed from the pantry.", "Tick at least one entry to delete."],
    "es": ["Eliminar", "Eliminar de la despensa", "Este producto tiene {n} entradas con caducidades distintas: elige cuáles eliminar.",
           "Poner en la lista de la compra", "Eliminar las entradas elegidas", "Cancelar", "Eliminar las filas marcadas",
           "Eliminado de la despensa.", "Marca al menos una entrada para eliminar."],
    "fr": ["Supprimer", "Retirer du garde-manger", "Ce produit a {n} entrées avec des dates limites différentes : choisissez lesquelles supprimer.",
           "Mettre dans la liste de courses", "Supprimer les entrées choisies", "Annuler", "Supprimer les lignes cochées",
           "Retiré du garde-manger.", "Cochez au moins une entrée à supprimer."],
    "de": ["Löschen", "Aus der Vorratskammer entfernen", "Dieses Produkt hat {n} Einträge mit unterschiedlichen Ablaufdaten: Wähle aus, welche gelöscht werden sollen.",
           "Auf die Einkaufsliste setzen", "Ausgewählte Einträge löschen", "Abbrechen", "Markierte Zeilen löschen",
           "Aus der Vorratskammer entfernt.", "Markiere mindestens einen Eintrag zum Löschen."],
    "ro": ["Șterge", "Elimină din cămară", "Acest produs are {n} intrări cu date de expirare diferite: alege pe care le ștergi.",
           "Pune în lista de cumpărături", "Șterge intrările alese", "Anulează", "Șterge rândurile bifate",
           "Eliminat din cămară.", "Bifează cel puțin o intrare de șters."],
    "ar": ["احذف", "احذف من المخزن", "لهذا المنتج {n} إدخالات بتواريخ انتهاء مختلفة: اختر أيها تريد حذفه.",
           "ضعه في قائمة التسوق", "احذف الإدخالات المحددة", "إلغاء", "احذف الصفوف المحددة",
           "تم الحذف من المخزن.", "حدد إدخالًا واحدًا على الأقل للحذف."],
}
for _lg, _liste in _FRASI.items():
    assert len(_liste) == len(_CHIAVI), _lg
    TRADUZIONI.setdefault(_lg, {}).update(dict(zip(_CHIAVI, _liste)))
