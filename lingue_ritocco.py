# -*- coding: utf-8 -*-
"""Frasi del ritocco manuale della foto (en, es, fr, de, ro, ar). Caricato con gli altri lingue*.py."""

_CHIAVI = ["Raddrizza e taglia a mano", "Gira (gradi): positivo = senso antiorario", "Taglia sopra (%)", "Taglia sotto (%)",
           "Taglia a sinistra (%)", "Taglia a destra (%)",
           "Ripristina", "Trascina il righello per raddrizzare · trascina la cornice per tagliare · poi tocca Salva", "Controlli di riserva",
           "Salva posizione e ritaglio", "Salvato", "Modifiche non ancora salvate"]

_FRASI = {
    "en": ["Straighten and crop by hand", "Rotate (degrees): positive = counter-clockwise", "Crop top (%)", "Crop bottom (%)", "Crop left (%)", "Crop right (%)", "Reset", "Drag the ruler to straighten · drag the frame to crop · then tap Save", "Backup controls", "Save position and crop", "Saved", "Changes not saved yet"],
    "es": ["Enderezar y recortar a mano", "Girar (grados): positivo = sentido antihorario", "Recortar arriba (%)", "Recortar abajo (%)", "Recortar a la izquierda (%)", "Recortar a la derecha (%)", "Restablecer", "Arrastra la regla para enderezar · arrastra el marco para recortar · luego toca Guardar", "Controles de reserva", "Guardar posición y recorte", "Guardado", "Cambios sin guardar"],
    "fr": ["Redresser et rogner à la main", "Pivoter (degrés) : positif = sens antihoraire", "Rogner en haut (%)", "Rogner en bas (%)", "Rogner à gauche (%)", "Rogner à droite (%)", "Réinitialiser", "Faites glisser la règle pour redresser · faites glisser le cadre pour rogner · puis touchez Enregistrer", "Commandes de secours", "Enregistrer la position et le recadrage", "Enregistré", "Modifications non enregistrées"],
    "de": ["Von Hand begradigen und zuschneiden", "Drehen (Grad): positiv = gegen den Uhrzeigersinn", "Oben zuschneiden (%)", "Unten zuschneiden (%)", "Links zuschneiden (%)", "Rechts zuschneiden (%)", "Zurücksetzen", "Lineal ziehen zum Begradigen · Rahmen ziehen zum Zuschneiden · dann Speichern tippen", "Reserve-Regler", "Position und Zuschnitt speichern", "Gespeichert", "Änderungen noch nicht gespeichert"],
    "ro": ["Îndreaptă și taie manual", "Rotește (grade): pozitiv = în sens antiorar", "Taie sus (%)", "Taie jos (%)", "Taie stânga (%)", "Taie dreapta (%)", "Resetează", "Trage rigla pentru a îndrepta · trage cadrul pentru a tăia · apoi atinge Salvează", "Comenzi de rezervă", "Salvează poziția și decuparea", "Salvat", "Modificări nesalvate încă"],
    "ar": ["تعديل وقص يدوي", "تدوير (درجات): موجب = عكس عقارب الساعة", "قص من الأعلى (%)", "قص من الأسفل (%)", "قص من اليسار (%)", "قص من اليمين (%)", "إعادة ضبط", "اسحب المسطرة للتعديل · اسحب الإطار للقص · ثم اضغط حفظ", "عناصر تحكم احتياطية", "حفظ الموضع والقص", "تم الحفظ", "التعديلات غير محفوظة بعد"],
}
for _lg, _liste in _FRASI.items():
    assert len(_liste) == len(_CHIAVI), _lg
    TRADUZIONI.setdefault(_lg, {}).update(dict(zip(_CHIAVI, _liste)))
