# -*- coding: utf-8 -*-
"""Frasi della scheda Utenti per «Parte della famiglia» (en, es, fr, de, ro, ar). Caricato con gli altri lingue*.py."""

_CHIAVI = [
    "Parte della famiglia",
    "Con «Parte della famiglia» vedi la Farmacia di quella persona nel Controllo famiglia: lei lo vede scritto nella sua Farmacia.",
]

_FRASI = {
    "en": ['Part of the family', 'With “Part of the family” you see that person’s Pharmacy in Family control: they see it written in their own Pharmacy.'],
    "es": ['Parte de la familia', 'Con «Parte de la familia» ves la Farmacia de esa persona en el Control familiar: ella lo ve escrito en su Farmacia.'],
    "fr": ['Membre de la famille', 'Avec « Membre de la famille » tu vois la Pharmacie de cette personne dans le Contrôle famille : elle le voit écrit dans sa Pharmacie.'],
    "de": ['Teil der Familie', 'Mit „Teil der Familie“ siehst du die Apotheke dieser Person in der Familienkontrolle: sie sieht das in ihrer Apotheke angezeigt.'],
    "ro": ['Face parte din familie', 'Cu „Face parte din familie” vezi Farmacia acelei persoane în Controlul familiei: ea vede acest lucru scris în Farmacia ei.'],
    "ar": ['من العائلة', 'عند تفعيل «من العائلة» ترى صيدلية هذا الشخص في مراقبة العائلة: وهو يرى ذلك مكتوباً في صيدليته.'],
}
for _lg, _liste in _FRASI.items():
    assert len(_liste) == len(_CHIAVI), _lg
    TRADUZIONI.setdefault(_lg, {}).update(dict(zip(_CHIAVI, _liste)))
