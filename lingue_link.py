# -*- coding: utf-8 -*-
"""Frasi del link da mandare agli utenti (en, es, fr, de, ro, ar). Caricato con gli altri lingue*.py."""

_CHIAVI = [
    "Link da mandare",
    "È sempre lo stesso per tutte le persone: cambia solo la password. Chi apre il link scrive la sua password e tocca Entra.",
    "Incolla qui il link della tua app",
    "Messaggio pronto da copiare e mandare",
    "Ciao {nome}! Ecco l'app Dispensa: {link}\nApri il link, scrivi questa password e tocca Entra:\n{password}\nAl primo accesso potrai scegliere una password tua.",
]

_FRASI = {
    "en": ["Link to send", "It is always the same for everyone: only the password changes. Whoever opens the link types their password and taps Enter.",
           "Paste the link to your app here", "Ready-made message to copy and send",
           "Hi {nome}! Here is the Pantry app: {link}\nOpen the link, type this password and tap Enter:\n{password}\nOn first access you can choose your own password."],
    "es": ["Enlace para enviar", "Es siempre el mismo para todos: solo cambia la contraseña. Quien abre el enlace escribe su contraseña y toca Entrar.",
           "Pega aquí el enlace de tu app", "Mensaje listo para copiar y enviar",
           "¡Hola {nome}! Aquí tienes la app Despensa: {link}\nAbre el enlace, escribe esta contraseña y toca Entrar:\n{password}\nEn el primer acceso podrás elegir tu propia contraseña."],
    "fr": ["Lien à envoyer", "C'est toujours le même pour tout le monde : seul le mot de passe change. Celui qui ouvre le lien saisit son mot de passe et touche Entrer.",
           "Collez ici le lien de votre application", "Message prêt à copier et envoyer",
           "Bonjour {nome} ! Voici l'application Garde-manger : {link}\nOuvrez le lien, saisissez ce mot de passe et touchez Entrer :\n{password}\nÀ la première connexion, vous pourrez choisir votre propre mot de passe."],
    "de": ["Link zum Senden", "Er ist für alle immer derselbe: nur das Passwort ändert sich. Wer den Link öffnet, gibt sein Passwort ein und tippt auf Weiter.",
           "Füge hier den Link deiner App ein", "Fertige Nachricht zum Kopieren und Senden",
           "Hallo {nome}! Hier ist die Vorrats-App: {link}\nÖffne den Link, gib dieses Passwort ein und tippe auf Weiter:\n{password}\nBeim ersten Zugang kannst du ein eigenes Passwort wählen."],
    "ro": ["Link de trimis", "Este mereu același pentru toți: se schimbă doar parola. Cine deschide linkul scrie parola lui și atinge Intră.",
           "Lipește aici linkul aplicației tale", "Mesaj gata de copiat și trimis",
           "Salut {nome}! Iată aplicația Cămara: {link}\nDeschide linkul, scrie această parolă și atinge Intră:\n{password}\nLa prima accesare îți poți alege propria parolă."],
    "ar": ["الرابط المراد إرساله", "هو نفسه دائمًا للجميع: تتغير كلمة المرور فقط. من يفتح الرابط يكتب كلمة مروره ويضغط دخول.",
           "الصق هنا رابط تطبيقك", "رسالة جاهزة للنسخ والإرسال",
           "مرحبًا {nome}! هذا هو تطبيق المؤونة: {link}\nافتح الرابط، اكتب كلمة المرور هذه واضغط دخول:\n{password}\nعند أول دخول يمكنك اختيار كلمة مرور خاصة بك."],
}
for _lg, _liste in _FRASI.items():
    assert len(_liste) == len(_CHIAVI), _lg
    TRADUZIONI.setdefault(_lg, {}).update(dict(zip(_CHIAVI, _liste)))
