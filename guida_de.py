# -*- coding: utf-8 -*-
"""Guida, giro guidato, novità e testi dell'assistente in TEDESCO. Caricato da app_dispensa.py dopo info_sezioni.py.
Per le schermate Farmacia / I miei documenti / Utilità i nomi dei pulsanti restano come si vedono sullo schermo (in italiano)."""
GUIDA_TR["de"] = {
    "d_assistente": ("🤖 Der digitale Assistent (der kleine Roboter)",
        """Es ist der **kleine gelb-blaue Roboter** unten rechts mit dem runden Gesicht. **Tippe ihn an** und sein Fenster öffnet sich.

Was er kann:
- **📖 Erkläre mir diese Seite**: er sagt dir laut, wofür die Seite da ist, auf der du bist.
- **🧭 Geführte Tour**: er erklärt dir die ganze App Schritt für Schritt (Weiter und Zurück).
- **🆕 Was ist neu**: er nennt dir die Neuigkeiten und wo du sie findest.
- **🎤 Stelle eine Frage**: tippen, sprechen (zum Beispiel „Wie füge ich dem Dokument ein Foto hinzu?“) und er antwortet mit der Anleitung. Funktioniert mit Chrome für Android.
- Du kannst die Frage auch **schreiben**.

**Stimme:** er benutzt die Stimme deines Handys. Wenn du ihn nicht hören willst, tippe **🔊 Stimme: an**, um sie auszuschalten.

**Zum Ausschalten:** tippe **⛔ Assistent ausschalten** in seinem Fenster. Zum Wiedereinschalten öffne den roten Knopf **Tippe für Infos** und tippe **✅ Einschalten** im Kasten des Assistenten. Die Wahl bleibt auf dem Handy gespeichert.""",
        "assistent roboter stimme spricht mikrofon hort frage tour neuigkeiten ausschalten einschalten hilfe"),
    "d_inizio": ("🚀 Wofür sie da ist und wie man anfängt",
        """**Wofür sie da ist:** sie führt die Liste dessen, was du zu Hause hast, wann es abläuft und was es enthält. Sie warnt dich, bevor etwas verdirbt.

**Zum Anfangen, 5 Schritte:**
1. Tippe unten auf den Reiter **➕ Hinzufügen**.
2. Fotografiere das Produkt (oder überspringe es).
3. Schreibe den Namen, wie viele Stück du hast und das **Ablaufdatum**.
4. Tippe auf den Knopf zum Speichern.
5. Geh zurück zum Reiter **🏠 Vorratsschrank**: das Produkt ist da, mit der Farbe des Ablaufdatums.

Der Vorratsschrank gehört **nur dir**: jede Person hat ihr Passwort und niemand sieht die Produkte der anderen.""",
        "anfangen beginnen erste schritte was ist wofur wie funktioniert einfuhrung benutzung"),
    "d_aggiungere": ("➕ Wie man ein Produkt hinzufügt",
        """1. Tippe auf **➕ Hinzufügen** (Reiter unten).
2. Oben ist der **Foto**-Bereich: tippe **📷 Foto aufnehmen** (die Rückkamera öffnet sich) oder **📁 Vom Handy hochladen**.
3. Schreibe **Name** und **Marke**.
4. Schreibe den **Barcode** von Hand (die Zahlen unter den Strichen): die App füllt Zutaten, Werte und Allergene selbst aus, wenn das Produkt bekannt ist.
5. Schreibe **wie viele Stück**, das **Gewicht** oder wie viele **Liter**.
6. Wähle das **Ablaufdatum**.
7. Bei **„Wohin legst du es?“** wähle: Vorratsschrank, Kühlschrank, Gefrierschrank, Keller, Geschäft, Lager oder Sonstiges. Die **Kategorie** ist freier Text.
8. Wähle **für wen es ist**: Erwachsene, Babys (0-2 Jahre) oder Tiere.
9. Speichern.

Wenn du keine Informationen hast, genügen **Name, Stückzahl und Ablaufdatum**.""",
        "hinzufugen eingeben neu produkt barcode qr ausfullen wohin kuhlschrank gefrierschrank keller kategorie menge stuck gewicht liter schreiben"),
    "d_foto": ("📸 Das Produktfoto: Aufnahme, Lineal und Zuschnitt",
        """1. Tippe auf **📷 Foto aufnehmen** oder **📁 Vom Handy hochladen**.
2. Die App entfernt den **Hintergrund** und **richtet** das Produkt selbst **gerade**.
3. Darunter erscheint der **Editor**: ziehe das **Lineal**, um das Foto zu drehen, und den **Rahmen**, um die Ränder zuzuschneiden.
4. Wenn es perfekt ist, tippe auf **💾 Position und Zuschnitt speichern**.
5. Dann speichere das Produkt.

Wenn der Editor nicht funktioniert, öffne **🛠️ Ersatzregler**: dort gibt es Schieberegler zum Drehen und Zuschneiden.""",
        "foto fotografieren aufnehmen kamera drehen gerade richten zuschneiden schneiden hintergrund freistellen lineal rahmen bild"),
    "d_colori": ("🎨 Die Farben und die Ablaufwarnungen",
        """- 🟢 **Grün**: noch mehr als 2 Monate. Alles ruhig.
- 🟠 **Orange**: läuft in weniger als 2 Monaten ab. Besser verbrauchen.
- 🔴 **Rot**: läuft in weniger als 1 Monat ab. Bald verbrauchen.
- ⚫ **Dunkel**: schon abgelaufen.

Oben siehst du die farbigen **Zähler** und die Hinweise, wie viele Stück, Gramm oder Liter bald ablaufen.

Jeder Bereich hat seinen **Ton**: Erwachsene die üblichen Töne; Babys ein Ton für das Mädchen (2 Monate), einer für den Jungen (1 Monat) und beide bei abgelaufen; Tiere die Katze (2 Monate), der Hund (1 Monat) und der Löwe bei abgelaufen.

Wenn du **Telegram** oder **E-Mail** aktiviert hast, kommt die Warnung auch dort an.""",
        "farben ablauf warnungen grun orange rot abgelaufen zahler ton tone sirene benachrichtigung hinweis wann lauft ab"),
    "d_allergeni": ("🌾 Allergene, Zutaten, vegan und glutenfrei",
        """1. Öffne das **Menü links** (der Pfeil **»** oben links) und wähle **deine Allergien**.
2. Produkte mit einem Allergen haben einen **gelben Knopf** mit seinem Namen (zum Beispiel *Gluten*): tippe darauf und die **Zusammensetzung** öffnet sich, mit den gefährlichen Wörtern hervorgehoben.
3. Wenn das Allergen **für dich gefährlich** ist, erscheint die **blinkende Sirene**, mit der Angabe, für wen es ungeeignet ist.
4. Auf jeder Karte gibt es den Knopf **Zutaten**: er öffnet den ganzen Text zum Lesen, in deiner Sprache.
5. Die Knöpfe **Vegan** und **Vegetarisch** erscheinen nur, wenn das Produkt es wirklich ist. Der Knopf **Glutenfrei** hat einen goldenen Rand.""",
        "allergene allergie gluten zutaten vegan vegetarisch glutenfrei zusammensetzung unvertraglichkeit sirene gefahrlich"),
    "d_pulsanti": ("🔘 Die Knöpfe jedes Produkts: Löschen, Info, Bearbeiten",
        """In **Karten** gibt es unter jedem Produkt drei Knöpfe:
- **Löschen**: entfernt das Produkt. Wenn du dasselbe Produkt mit mehreren Ablaufdaten hast, fragt es, **welchen Eintrag** es löschen soll.
- **Info**: öffnet die komplette Anleitung mit allen Symbolen.
- **Bearbeiten**: ändert jede Angabe (Name, Ablaufdatum, Foto, Menge…).

In der **Tabelle** hakst du das Kästchen 🗑️ der Zeile an und tippst dann auf **Angehakte Zeilen löschen** oder **Angehakte Zeile bearbeiten** (zum Bearbeiten nur eine Zeile anhaken).""",
        "loschen entfernen papierkorb bearbeiten andern korrigieren info tabelle karten ansicht"),
    "d_icone": ("🧭 Die Symbole Apotheke, Meine Dokumente und Extras",
        """Auf der Startseite findest du neben den Suchfeldern **drei pulsierende Symbole**:
- **🏥 Apotheke**: Medikamente, Therapien, Besuche, Gesundheitskarte.
- **📁 Meine Dokumente**: Personalausweis, Führerschein, Gesundheitskarte mit den Ablaufdaten.
- **🧰 Extras**: nützliche Apps und Seiten, wie Velocity Music.

Tippe eines an, um es zu öffnen; zum Zurückgehen tippe **← Zurück zum Vorratsschrank**. Auf jeder Seite ist oben der rote Knopf **Tippe für Infos** mit der Anleitung.""",
        "symbole apotheke dokumente extras startseite seiten navigieren menu wo finde"),
    "d_cercare": ("🔎 Produkte suchen und filtern",
        """Oben im Vorratsschrank gibt es drei Bedienelemente:
1. **🔎 Suchen**: schreibe Name oder Marke.
2. **Anzeigen**: wähle *Alle*, *Nur bald ablaufend (2 Monate)*, *Nur rote (1 Monat)* oder *Abgelaufen*.
3. **Ansicht**: *Karten* (mit großen Fotos) oder *Tabelle* (kompakte Liste).""",
        "suchen suche finden filter filtern anzeigen ansicht karten tabelle liste"),
    "d_spesa": ("🛒 Einkaufsliste und Prospekte",
        """- Wenn ein Produkt **aufgebraucht** ist, kommt es von allein in den Reiter **🛒 Einkauf**.
- Im Reiter Einkauf kannst du **Ich habe eins verbraucht** antippen, um ein Stück abzuziehen.
- Auf der Produktkarte, rechts von der Menge, ist der Link zu den **Prospekten** von Supermärkten, Hypermärkten und Discountern: wähle das **Land** (es beginnt mit dem deiner Sprache) und schreibe die **Stadt**, sieh dir die Angebote an und tippe auf den Knopf, um das Produkt auf die **Einkaufsliste** zu setzen, mit dem Namen des Geschäfts.""",
        "einkauf einkaufsliste kaufen prospekte angebote supermarkt verbraucht aufgebraucht stadt geschaft"),
    "d_gestisci": ("✏️ Viele Produkte auf einmal verwalten",
        """Der Reiter **✏️ Verwalten** dient dazu, **Menge, Ablaufdaten und Notizen** vieler Produkte auf einmal zu ändern, ohne sie einzeln zu öffnen.""",
        "verwalten bearbeiten viele mehrere produkte zusammen menge ablaufdaten notizen"),
    "d_account": ("👤 Passwort, Sprache und Nachrichten",
        """- **Passwort:** du bekommst es von der Person, die die App verwaltet. Beim ersten Zugang kannst du es ändern. Es gehört nur dir.
- **Sprache:** im Menü links gibt es **🌐 Sprache / Language**.
- **Nachrichten und Vorschläge:** für eine Idee, ein Problem oder eine Bitte nutze den Reiter **✉️ Nachrichten / 💬 Vorschläge**: der Administrator liest sie.""",
        "passwort konto zugang sprache language nachrichten vorschlage administrator problem bitte andern"),
    "d_aiuto": ("🛟 Wenn etwas nicht klappt",
        """1. **Lade die Seite neu** im Browser.
2. Das Foto erscheint nicht? Nutze **🛠️ Ersatzregler** oder wähle ein anderes Foto.
3. Das Mikrofon zum Diktieren funktioniert mit **Chrome für Android**: einmal tippen zum Einschalten, einmal zum Ausschalten.
4. Wenn das Problem bleibt, schreibe es in den Reiter **Nachrichten**: das hilft dem Administrator, es zu beheben.""",
        "problem fehler funktioniert nicht hilfe blockiert foto erscheint nicht mikrofon diktat"),

    "f_cosa": ("🚀 Wofür die Apotheke da ist",
        """Hier hältst du die **Medikamente zu Hause** und ihre **Ablaufdaten**, die **Therapien**, die **Arztbesuche**, die **Impfungen**, deinen **Arzt** und dein **Gesundheitsblatt** in Ordnung.

Die App **erinnert dich** und ordnet, was du einträgst. Sie **gibt keine medizinischen Ratschläge** und ändert keine Therapien: für Dosen und Behandlungen folge immer deinem Arzt oder Apotheker.""",
        "apotheke was ist wofur medikamente anfangen einfuhrung"),
    "f_profili": ("👤 Die Familienprofile und die Blutgruppe",
        """Jede Person hat ein **Profil** (bis zu 12): Mama, Papa, Kinder…
1. Oben wähle das Profil bei **👤 Profilo**.
2. Um eines hinzuzufügen öffne **👥 Gestisci profili**, schreibe den Namen und tippe **Aggiungi profilo**.
3. An derselben Stelle kannst du den Namen ändern und die **🩸 Blutgruppe** wählen: sie erscheint als farbiger **Tropfen** neben dem Profil.
4. Um ein Profil zu löschen, hake die Bestätigung an und tippe **Elimina profilo** (alle seine Daten werden mit gelöscht).""",
        "profil profile familie person blutgruppe tropfen name hinzufugen loschen"),
    "f_medicinale": ("💊 Wie man ein Medikament hinzufügt",
        """1. Tippe auf **➕ Aggiungi medicinale**.
2. Oben das **Foto der Packung**: **📷 Scatta la foto** oder **📁 Carica dal telefono**; dann mit dem Lineal gerade richten, mit dem Rahmen zuschneiden und **💾 Salva posizione e ritaglio** tippen.
3. Schreibe **Name**, **Wirkstoff**, **Dosierung**, **Form** (Tabletten, Saft…) und **Menge**.
4. Wähle das **Ablaufdatum** und **für wen es ist**.
5. Tippe auf **Salva**.

Du kannst ein bereits gespeichertes Foto aus dem **Fotoarchiv** wiederverwenden. Dem Medikament kannst du den **Beipackzettel** anhängen (PDF, Foto oder Link).

Um alles zu einem Medikament zu sehen, **tippe auf seine Karte**: das Detail öffnet sich mit dem **Beipackzettel**, dem großen Foto, den verknüpften Therapien und den Knöpfen **✏️ Modifica** und **🗑️ Elimina**.""",
        "medikament medikamente arznei hinzufugen packung foto ablaufdatum wirkstoff dosierung beipackzettel archiv"),
    "f_scadenze": ("🎨 Ablaufdaten und Medikamentenallergien",
        """- 🟠 **Orange**: läuft in weniger als 2 Monaten ab. 🔴 **Rot**: in weniger als 1 Monat. ⚫ **Abgelaufen**: richtig entsorgen.
- Auf der Profilkarte kannst du die **Medikamentenallergien** eintragen: wenn ein Medikament diesen Wirkstoff enthält, erscheint eine **rote Warnung**.""",
        "ablaufdatum farben allergie allergien medikamente warnung rot orange abgelaufen"),
    "f_terapie": ("📅 Die Therapien und der Kalender",
        """1. Öffne den Reiter **📅 Terapie**.
2. Füge eine Therapie hinzu: **Medikament**, **Tage**, **Uhrzeiten** und Menge.
3. Zur festgelegten Zeit tippe auf **Presa** (genommen), um die Einnahme zu vermerken: sie bleibt in der **Chronik**.
4. Eine Therapie kann **aktiv**, **pausiert** oder **beendet** sein. Testtherapien kann man **löschen**.
5. Der **Kalender** zeigt Woche und Monat.
6. Der **Bericht für den Arzt** (Zeitraum nach Wahl) lässt sich drucken oder in Excel öffnen.""",
        "therapie therapien kalender einnahme genommen uhrzeiten bericht arzt chronik tablette dosis"),
    "f_prescrizioni": ('📝 Rezepte',
        """1. Öffne den Reiter **📝 Prescrizioni** und tippe auf **➕ Aggiungi prescrizione**.
2. Schreibe das **Datum**, die **Art** (Medikamente, Untersuchungen, Besuch…), den **Arzt**, was **verschrieben** wurde, den **Rezeptcode** und bis wann es **gültig** ist.
3. Füge das **Foto des Rezepts** oder die PDF hinzu.
4. Tippt man auf ein Rezept, öffnet sich das **Detail**: du siehst das Foto, tippst auf **✅ Segna come usata** (Als verwendet markieren), **✏️ Modifica** oder **🗑️ Elimina**.
5. Bald ablaufende Rezepte erscheinen bei den Dingen zum Prüfen, auch in der **Familienkontrolle**.""",
        'rezept rezepte verschreibung arzt code gueltigkeit ablauf verwendet'),
    "f_visite": ("🩺 Arztbesuche, Untersuchungen und Befunde",
        """1. Öffne den Reiter **🩺 Visite** und tippe zum Hinzufügen.
2. Schreibe **Datum**, **Art des Besuchs oder der Untersuchung**, **Arzt**, **Grund** und die **Hinweise für Kontrollen**.
3. Falls vorhanden, schreibe das Datum des **nächsten Termins**.
4. Hänge die **Befunde** an: Foto oder PDF.""",
        "besuch arztbesuch untersuchung befund analyse termin facharzt anhangen"),
    "f_vaccini": ("💉 Impfungen und Impfpass",
        """Im Reiter **💉 Vaccini** trägst du die Impfungen jedes Profils ein und hängst den **Impfpass** an (Foto oder PDF).""",
        "impfung impfungen impfpass impfausweis"),
    "f_scheda": ("🩸 Das Gesundheitsblatt und „Il mio dottore“",
        """- Tippe auf das Feld der **Blutgruppe**, um das **Gesundheitsblatt** zu öffnen: Erkrankungen, Medikamentenallergien, Operationen, Krankengeschichte und Impfungen.
- Daneben findest du **Il mio dottore** (Mein Arzt): wähle Arzt oder Ärztin, dann schreibe Name, Adresse, Telefon, E-Mail, die **Sprechzeiten** (eine Zeile pro Tag: von, bis, Notizen), die **Vertretung** und Notizen.""",
        "gesundheitsblatt arzt hausarzt erkrankungen operationen krankengeschichte sprechzeiten telefon email vertretung"),
    "f_tessera": ("🪪 Gesundheitskarte und Gesundheitsakte",
        """Oben, neben der Ärztin, ist das hellblaue Abzeichen **Tessera sanitaria · Fascicolo sanitario** (es pulsiert sanft, damit man es bemerkt). Tippe darauf.

**Die Karte**
1. Tippe auf **👁️ Mostra fronte e retro della tessera**: du siehst sie groß.
2. Die Karte kommt aus **I miei documenti**. Wenn du sie noch nicht eingetragen hast, erscheint ein Hinweis mit dem Knopf **📁 Vai a I miei documenti**: wähle **Tessera sanitaria** und mache das Foto von Vorder- und Rückseite. Der Hinweis verschwindet von selbst, sobald du sie eingetragen hast.

**Die Online-Links** (einer für die elektronische Gesundheitsakte, einer für Impfungen, einer für absetzbare Gesundheitskosten)
1. Öffne die Seite im Browser und **kopiere die Adresse** aus der Leiste oben.
2. Komm hierher zurück und **füge sie** in das richtige Feld **ein**.
3. Tippe auf **💾 Salva**.
4. Ab dann erscheint ein Knopf **🔗**: beim Antippen öffnet sich die Seite direkt.
5. Um den Link zu ändern tippe **✏️ Modifica**; um ihn zu entfernen tippe **🗑️ Togli il link**.

Die Links sind für jedes Familienprofil getrennt.""",
        "gesundheitskarte tessera sanitaria gesundheitsakte elektronisch fse link adresse impfungen online absetzbar gesundheitskosten vorderseite ruckseite abzeichen"),
    "f_aperta": ("🔎 Eine geöffnete Apotheke finden",
        """Tippe oben auf den großen Knopf (**Geöffnete Apotheke finden**): wähle das **Land** (es beginnt mit dem deiner Sprache) und schreibe **eine beliebige Stadt oder Postleitzahl**. Die App sucht geöffnete Apotheken in der Nähe dieses Ortes. Oder tippe auf **📍 Meinen Standort nutzen (GPS)**: das Handy fragt nach der Erlaubnis und die App sucht rund um deinen Standort (er wird nicht gespeichert).""",
        "apotheke geoffnet finden suchen nahe notdienst nacht"),
    "f_avvisi": ("🔔 Benachrichtigungen per Telegram, E-Mail und SMS",
        """Die Benachrichtigungen erinnern dich an die Ablaufdaten (bei 60, 30, 14 und 7 Tagen, 1 Tag und am Tag selbst) und, wenn du willst, an die Uhrzeit der Therapien. Wähle **einen oder mehrere Kanäle**.

### 📱 Telegram, Schritt für Schritt
**Was du brauchst:** die Telegram-App auf dem Handy und zwei Minuten. Telegram ist kostenlos.

1. **Installiere Telegram** aus dem Play Store (Android) oder App Store (iPhone) und erstelle dein Konto: es fragt nach deiner Handynummer.
2. **Öffne den Bot der App.** Tippe in Telegram oben auf die Lupe 🔍 und suche **Dispensa Leo**.
3. Tippe auf **Start** (oder schreibe `/start`). **Dieser Schritt ist wichtig:** ohne ihn kann der Bot dir nicht schreiben.
4. **Finde deine Nummer (Chat ID).** Suche den Bot **@userinfobot**, öffne ihn und tippe auf **Start**: er antwortet mit deiner **Id**, einer Zahl (zum Beispiel `123456789`). Halte sie gedrückt, um sie zu kopieren. Es ist ein kostenloser Bot, der dir nur diese Zahl sagt.
5. **Komm auf diese Seite zurück.** Öffne **🔔 Scegli come ricevere gli avvisi**, hake **📱 Telegram** an, füge die Zahl in das Feld **Chat ID** ein (nur Ziffern) und tippe auf **Salva**.
6. **Fertig.** Die Benachrichtigungen kommen von diesem Bot, ab dem nächsten automatischen Versand (meist am nächsten Morgen).

**Wenn nichts ankommt:** prüfe, ob du im Bot auf *Start* getippt hast (Schritt 3) und ob die Zahl stimmt, ohne Leerzeichen oder Buchstaben.

### ✉️ E-Mail
**Für die E-Mail ist es ganz einfach: deine Adresse genügt.** Kein Passwort und keine anderen Einstellungen.

1. Öffne **🔔 Scegli come ricevere gli avvisi**.
2. Hake **✉️ Email** an.
3. Schreibe **deine E-Mail-Adresse** in das Feld (zum Beispiel `name@gmail.com`) und prüfe, ob sie stimmt.
4. Tippe auf **Salva**.

Die Nachrichten kommen von der E-Mail-Adresse der App. **Schau beim ersten Mal auch in Spam oder Werbung** und, wenn du sie dort findest, markiere sie als „Kein Spam“: ab dann kommt sie in den normalen Posteingang.

### 💬 SMS
Sie kosten Geld und sind meist nicht aktiv: frag den Administrator.

Optional: hake **„Nei messaggi non scrivere i nomi dei medicinali“** (in Nachrichten keine Medikamentennamen schreiben) an, wenn du mehr Privatsphäre willst.""",
        "benachrichtigungen warnungen telegram chat id bot start userinfobot email sms erinnerung nachricht erhalten aktivieren nummer gmail spam"),
    "f_report": ("🧾 Vollständiger Bericht und Daten",
        """In **🧾 I miei dati personali e report completo** schreibst du Vor- und Nachname und lädst einen **Bericht zum Ausdrucken** mit allem herunter, was du eingetragen hast. Die **JSON**-Datei enthält dieselben Daten als Sicherungskopie.
Sie enthält Gesundheitsdaten: gib sie nicht an Personen weiter, die sie nicht sehen sollen.""",
        "bericht vollstandig drucken exportieren herunterladen personliche daten kopie pdf json"),

    "u_cosa": ("🧰 Wofür die Seite Extras da ist",
        """Sie sammelt **nützliche Apps und Seiten** an einem Ort. Jede hat einen großen **pulsierenden Knopf**: tippe darauf und sie startet.

Unter dem Knopf steht der **Name** der App: beim Antippen öffnet sich der **Beipackzettel**, eine einfache Erklärung, was sie kann und welche Vorteile sie hat.

Im Moment gibt es **Velocity Music** (das hellblaue Play) und **Wimbi** (die Ente mit Kopfhörern); weitere Extras kommen hier dazu.""",
        "extras seite apps knopfe starten sammlung seiten was ist wofur"),
    "u_avviare": ("▶️ Wie man eine App startet",
        """1. Tippe auf der Startseite auf das Symbol **🧰 Utilità** (neben Farmacia und I miei documenti).
2. Tippe auf den **großen Knopf** mit dem Symbol ▶️: die App öffnet sich in einem neuen Browser-Tab.
3. Um hierher zurückzukehren, schließe diesen Tab oder geh zurück.""",
        "starten offnen play knopf app link velocity music musik"),
    "u_bugiardino": ("📖 Wie man den Beipackzettel liest",
        """1. Unter dem Knopf ist das **Schild mit dem Namen** der App.
2. **Tippe es an**: ein Fenster öffnet sich mit der Erklärung (was es ist, Vorteile, Adresse).
3. Darin gibt es auch den Knopf **🎵 Avvia**, um die App zu öffnen.
4. Zum Schließen des Fensters tippe oben auf das **X**.""",
        "beipackzettel erklarung schild name lesen beschreibung vorteile information"),
    "u_wimbi": ("🦆 Wimbi",
        """Wimbi ist eine Musik-App: **du schreibst ein Lied oder einen Künstler, tippst auf ein Ergebnis und es spielt**. Keine Anmeldung nötig, Playlists bleiben auf deinem Gerät, die Musik **spielt bei ausgeschaltetem Bildschirm weiter** und die App gibt es in **17 Sprachen**.

Tippe auf die **Ente mit Kopfhörern**, um sie zu starten, oder auf die grüne Schrift **Wimbi**, um den ganzen Beipackzettel zu lesen.
Adresse: https://wimbi.app/it/""",
        "wimbi ente kopfhorer musik lieder kunstler playlist bildschirm aus sprachen ohne konto"),
    "u_velocity": ("🎵 Velocity Music",
        """Es ist ein Musikplayer und -manager, mit dem du die YouTube-Bibliothek **kostenlos**, **ohne Werbung** und **ohne Abo** hören kannst. Man kann ihn **als Gast** nutzen, ohne ein Konto zu erstellen. Das Projekt ist noch in Entwicklung, aber schon nutzbar.

Adresse: https://velocitymusic.uk/""",
        "velocity music youtube kostenlos werbung player lieder horen radio"),

    "x_cosa": ("🚀 Wofür „Meine Dokumente“ da sind",
        """Hier bewahrst du deine **persönlichen Dokumente** (Personalausweis, Führerschein, Reisepass, Gesundheitskarte, Genehmigungen, Versicherungen…) mit den **Fotos von Vorder- und Rückseite** und den **Ablaufdaten** auf.

Die App warnt dich **6 Monate vorher** (erste Warnung, orange) und **3 Monate vorher** (zweite Warnung, rot und intensiver), damit du Zeit zum Erneuern hast.""",
        "dokumente was ist wofur personalausweis fuhrerschein reisepass gesundheitskarte anfangen einfuhrung"),
    "x_aggiungere": ("➕ Wie man ein Dokument hinzufügt",
        """1. Wähle bei **👤 Documenti di**, wem das Dokument gehört.
2. Tippe auf **➕ Aggiungi un documento**.
3. Wähle den **Typ** aus der Liste. Wenn er fehlt, schreibe ihn in das Feld **„Non lo trovi?“**.
4. Schreibe **Nummer**, **ausgestellt von**, **Ausstellungsdatum** und **Ablaufdatum**. Wenn es nie abläuft, hake **„Questo documento non scade“** an.
5. Mache das **Foto von Vorder- und Rückseite** (siehe Anleitung unten).
6. Tippe auf **💾 Salva il documento**.""",
        "hinzufugen eingeben neu dokument typ nummer ausgestellt ablaufdatum lauft nicht ab speichern"),
    "x_foto": ("📷 Foto von Vorder- und Rückseite (Hintergrund entfernt und gerade gerichtet)",
        """Es gibt **zwei gleiche Blöcke: 📄 Fronte (Vorderseite) und 📄 Retro (Rückseite)**. Für jeden:
1. Tippe auf **📷 Scatta la foto** (Rückkamera) **oder** **📁 Carica dal telefono**, wenn du das Foto schon hast.
2. Die App entfernt den **Hintergrund** und **richtet** das Dokument selbst **gerade**.
3. Darunter erscheint der **Editor**: ziehe das **Lineal** zum Drehen und den **Rahmen** zum Zuschneiden.
4. Wenn es perfekt ist, tippe auf **💾 Salva posizione e ritaglio**.
5. Wenn das Dokument schlecht ausgeschnitten wurde, hake **„Tieni anche lo sfondo“** an: das Bild bleibt ganz und du passt es nur von Hand an.
6. Wenn du das falsche Foto gemacht hast, tippe **🗑️ Togli questa foto**.
7. Am Ende tippe **💾 Salva il documento**: die Fotos werden zusammen mit den Daten gespeichert.

Für ein **PDF** oder weitere Seiten nutze das Feld **„Altri file“** unter dem Formular.""",
        "foto aufnehmen vorderseite ruckseite hochladen zuschneiden hintergrund gerade drehen lineal rahmen bild dokument"),
    "x_colori": ("🎨 Die Farben und die Ablaufwarnungen",
        """- 🟢 **Grün**: läuft in mehr als 6 Monaten ab.
- 🟠 **Orange, erste Warnung**: läuft in weniger als 6 Monaten ab.
- 🔴 **Rot, zweite Warnung**: läuft in weniger als 3 Monaten ab. Ein Alarmkasten erscheint.
- ⚫ **Abgelaufen**: sofort erneuern.

Oben siehst du die Zähler. Wenn du **Telegram** oder **E-Mail** aktiviert hast (das geht in der Apotheke, bei **Scegli come ricevere gli avvisi**), kommen die Warnungen auch dort an.""",
        "farben ablauf warnungen orange rot abgelaufen sechs monate drei monate erneuern alarm telegram email"),
    "x_cercare": ("🔎 Dokumente suchen und filtern",
        """Über der Liste ist das Feld **Suchen**: schreibe den Typ, die Nummer, die Behörde oder eine Notiz. Daneben wähle eine **Kategorie**, um nur diese zu sehen.""",
        "suchen suche finden filter kategorie liste"),
    "x_modificare": ("✏️ Bearbeiten, öffnen und löschen",
        """- **Ein Dokument öffnen:** tippe auf seine **farbige Karte**: das Detail öffnet sich mit allen Daten.
- **Vorder- und Rückseite ansehen:** im Detail tippe auf **👁️ Mostra fronte e retro** (Vorder- und Rückseite zeigen): du siehst sie groß und kannst sie **herunterladen**.
- **Bearbeiten:** im Detail tippe auf **✏️ Modifica**, ändere die Daten oder füge weitere Fotos hinzu, dann speichere.
- **Nur ein Foto entfernen:** in Modifica, in der Liste **Già allegato**, tippe auf 🗑️ neben der Datei.
- **Das Dokument löschen:** im Detail tippe auf **🗑️ Elimina** und bestätige.""",
        "bearbeiten andern loschen entfernen offnen anhang herunterladen foto"),
    "x_tipi": ("⚙️ Die Dokumenttypen",
        """Unten auf der Seite öffne **⚙️ Gestisci i tipi di documento**: du kannst eigene Typen **hinzufügen**, **entfernen** oder die nicht genutzten **ausblenden**.""",
        "typen typ kategorien neuer typ ausblenden katalog"),
    "x_privacy": ("🔒 Datenschutz",
        """Dokumente enthalten persönliche Daten: **teile keine** Screenshots oder Dateien mit Personen, die sie nicht sehen sollen. Jede Person sieht nur ihre eigenen.""",
        "datenschutz sicherheit personliche daten teilen"),

    "tour1": ("Willkommen!", "Hallo, ich bin dein Assistent. Ich zeige dir kurz die App. Mit den Knöpfen Weiter und Zurück gehst du in deinem Tempo, und du kannst mich jederzeit stoppen."),
    "tour2": ("Der Vorratsschrank", "Im Vorratsschrank führst du die Liste dessen, was du zu Hause hast. Tippe auf Hinzufügen, fotografiere das Produkt, schreibe Name und Ablaufdatum. Die Farben sagen dir, wann du handeln musst: grün ruhig, orange unter zwei Monaten, rot unter einem Monat."),
    "tour3": ("Allergene und Zutaten", "Wenn du im Menü links deine Allergien wählst, erkennst du gefährliche Produkte sofort und eine Sirene erscheint. Auf jeder Karte zeigt der Knopf Zutaten die Zusammensetzung."),
    "tour4": ("Die Apotheke", "Mit dem ersten Symbol kommst du in die Apotheke: Medikamente mit Ablaufdatum, Therapien mit Erinnerungen per Telegram oder E-Mail, Arztbesuche, Impfungen und ein Profil für jedes Familienmitglied."),
    "tour5": ("Gesundheitskarte", "In der Apotheke, neben der Ärztin, ist das hellblaue Abzeichen der Gesundheitskarte: es zeigt Vorder- und Rückseite und lässt dich die Links zur Gesundheitsakte, zu Impfungen und zu absetzbaren Kosten speichern."),
    "tour6": ("Meine Dokumente", "Mit dem zweiten Symbol kommst du zu Meine Dokumente. Fotografiere das Dokument: die App entfernt den Hintergrund, richtet es gerade und versucht, Typ, Nummer und Ablauf zu lesen. Du kannst die Felder immer korrigieren. Sie warnt dich sechs und drei Monate vor dem Ablauf."),
    "tour7": ("Die Extras", "Mit dem dritten Symbol kommst du zu den Extras: nützliche Apps wie Velocity Music und Wimbi. Tippe auf den Knopf, um sie zu starten, und auf den Namen, um den Beipackzettel zu lesen."),
    "tour8": ("Hilfe immer griffbereit", "Oben auf jeder Seite ist der rote Knopf Tippe für Infos, mit Anleitung und Suche. Und ich bin hier: tippe mich an, wann du willst, auch mit dem Mikrofon. Wenn du mich nicht brauchst, schaltest du mich im Fenster aus und über den roten Knopf wieder ein. Viel Erfolg!"),

    "nov1": ("Digitaler Assistent", "Der runde kleine Roboter unten rechts: tippe ihn an und er erklärt dir die App laut, auch mit dem Mikrofon"),
    "nov2": ("Neues Extra: Wimbi", "Startseite → Extras → die Ente mit Kopfhörern; tippe auf die grüne Schrift für den Beipackzettel"),
    "nov3": ("Neue Seite „Extras“", "Startseite → drittes hellblaues Symbol „Utilità“, neben Farmacia und I miei documenti"),
    "nov4": ("Anleitung auf jeder Seite", "Roter Knopf „Tippe für Infos“ oben, mit Erklärungen und Suche"),
    "nov5": ("Gesundheitskarte und Gesundheitsakte", "Apotheke → hellblaues Abzeichen neben der Ärztin"),
    "nov6": ("Dokumente: Foto und automatisches Lesen", "Meine Dokumente → „Aggiungi un documento“"),
}

UI_TR["de"] = {
    "dlg_titolo": "📖 Anleitung und Informationen",
    "dlg_hint": "Tippe ein Thema an, um es zu öffnen. Oder schreibe unten, was du wissen willst.",
    "dlg_cerca_label": "🔎 Was willst du wissen?",
    "dlg_cerca_ph": "z. B. wie fotografiere ich die Rückseite des Dokuments",
    "dlg_trovato": "**Das habe ich gefunden:**",
    "dlg_nulla": "Mit diesen Wörtern habe ich keine Antwort gefunden. Versuche es anders zu schreiben (zum Beispiel nur ein Wort: *Foto*, *Ablauf*, *Passwort*) oder schreibe einen Vorschlag im Reiter Nachrichten.",
    "dlg_tutti": "Alle Themen",
    "dlg_nota_it": "ℹ️ Die Bildschirme dieses Bereichs sind vorerst auf Italienisch: die Namen der Knöpfe sind so geschrieben, wie du sie auf dem Bildschirm siehst.",
    "dlg_asst": "**🤖 Digitaler Assistent** (der kleine Roboter, der spricht und dir hilft)",
    "dlg_on": "✅ Einschalten", "dlg_off": "⛔ Ausschalten",
    "info_help": "Tippe, um zu lesen, wie dieser Bereich funktioniert", "info_fallback": "ℹ️ Informationen und Anleitung",
    "sez_dispensa": "🏠 Vorratsschrank", "sez_farmacia": "🏥 Apotheke", "sez_documenti": "📁 Meine Dokumente", "sez_utilita": "🧰 Extras",
    "a_aria": "Digitaler Assistent", "a_rileggi": "📖 Erkläre mir diese Seite", "a_giro": "🧭 Geführte Tour durch die App",
    "a_novita": "🆕 Was ist neu", "a_mic": "🎤 Stelle eine Frage", "a_indietro": "◀ Zurück", "a_avanti": "Weiter ▶", "a_fine": "Ende",
    "a_ph": "Schreibe hier deine Frage…", "a_chiedi": "Fragen", "a_voce_on": "🔊 Stimme: an", "a_voce_off": "🔇 Stimme: aus",
    "a_silenzio": "⏹ Stille", "a_off": "⛔ Assistent ausschalten", "a_ascolto_btn": "⏹ Ich höre zu…",
    "a_ascolto_t": "Ich höre zu", "a_ascolto_x": "Sprich jetzt: zum Beispiel „Wie füge ich dem Dokument ein Foto hinzu?“",
    "a_mic_t": "Mikrofon", "a_mic_no": "Auf diesem Handy kann ich dich nicht hören: schreibe die Frage unten.",
    "a_mic_perm": "Erlaube dem Browser, das Mikrofon zu nutzen, damit du mit mir sprechen kannst.",
    "a_mic_err": "Ich kann die Stimme gerade nicht nutzen: schreibe die Frage unten.",
    "a_nulla_t": "Ich habe nichts gehört", "a_nulla_x": "Versuche es noch einmal: tippe auf das Mikrofon und sprich.",
    "a_dimmi_t": "Sag nur", "a_dimmi_x": "Schreibe oder sage, was du wissen willst.",
    "a_off_t": "Soll ich mich ausschalten?",
    "a_off_x": "Tippe unten auf den Knopf „⛔ Assistent ausschalten“. Über den roten Knopf „Tippe für Infos“ schaltest du mich wieder ein.",
    "a_trov_t": "Ich habe die Antwort nicht gefunden",
    "a_trov_x": "Versuche es mit anderen Wörtern (zum Beispiel nur eins: Foto, Ablauf, Passwort) oder wähle unten ein Thema.",
    "a_nov_none_t": "Neuigkeiten", "a_nov_none_x": "Im Moment gibt es keine neuen Neuigkeiten. Ich sage dir Bescheid, wenn welche kommen!",
    "a_nov_voce": "Hier sind die Neuigkeiten.", "a_nov_trovi": "Du findest sie so:", "a_nov_t": "Was ist neu",
    "a_fine_t": "Ende der Tour", "a_fine_x": "Das war's! Wenn du noch etwas brauchst, frag mich.",
    "a_toast_off": "Assistent ausgeschaltet. Über „Tippe für Infos“ schaltest du ihn wieder ein.", "a_toast_on": "Assistent an: tippe den kleinen Roboter an.",
    "a_vedi": "Tippe unten ein Thema an, um mehr zu erfahren.",
    "i_silenzio": "stille ruhig stopp aufhor genug", "i_off": "ausschalt deaktiv abschalt", "i_ass": "assistent roboter",
    "i_novita": "neuigkeit neu aktualis", "i_giro": "tour tutorial anleitung start rundgang", "i_saluto": "hallo hi guten morgen guten abend hilfe",
}
