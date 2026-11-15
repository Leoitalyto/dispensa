# -*- coding: utf-8 -*-
"""«📄 Utilità PDF» (pagina Utilità): elenchi a cascata per creare, unire, comprimere, convertire, modificare e firmare un PDF
con i servizi più usati e conosciuti (iLovePDF, PDF24, Smallpdf, Sejda, Adobe, PDFgear, Xodo, Stirling-PDF…).
Sono SOLO collegamenti a servizi esterni: l'app non manda loro nulla e non usa nessuna chiave.
PER AGGIUNGERE UN SERVIZIO: aggiungi una voce a UPD_SERVIZI; per aggiungere un compito, una voce a UPD_COMPITI. Prefisso: upd_ / UPD_."""
import streamlit as st

# id: nome, indirizzo, dove si usa, costo e limiti (sempre «indicativi»), come si lavora con i tuoi file, punto forte
UPD_SERVIZI = {
    "ilovepdf": {
        "nome": "iLovePDF", "link": "https://www.ilovepdf.com/it", "dove": "Sito (Chrome) · app Android",
        "costo": "Gratis con limiti (dimensione dei file e numero di lavori). Il piano Premium costa circa 5–9 € al mese.",
        "forte": "Il più usato e conosciuto, tutto in italiano: unisci, dividi, comprimi, converti, ruota, proteggi, firma, modifica, OCR.",
        "privacy": "I file passano da un server esterno e vengono cancellati dopo un po'.",
    },
    "pdf24": {
        "nome": "PDF24 Tools", "link": "https://tools.pdf24.org/it/", "dove": "Sito (Chrome) · programma per Windows",
        "costo": "Gratis, senza registrazione e senza abbonamento.",
        "forte": "Tantissimi strumenti gratuiti in italiano; sul computer Windows c'è anche la versione che lavora senza internet.",
        "privacy": "Online i file passano da un server (cancellati dopo poco); la versione per Windows lavora sul tuo computer.",
    },
    "smallpdf": {
        "nome": "Smallpdf", "link": "https://smallpdf.com/it", "dove": "Sito (Chrome) · app",
        "costo": "Gratis solo per pochi lavori al giorno (circa 2) e file piccoli; poi abbonamento da circa 9–15 € al mese.",
        "forte": "Molto semplice e bello da usare: comprimi, converti, modifica, firma. Adatto se devi fare poche cose.",
        "privacy": "I file passano da un server esterno e vengono cancellati dopo un po'.",
    },
    "sejda": {
        "nome": "Sejda PDF", "link": "https://www.sejda.com/it/", "dove": "Sito (Chrome) · programma per computer",
        "costo": "Gratis con limiti (pochi lavori all'ora, file fino a circa 50 MB e 200 pagine); a pagamento per toglierli.",
        "forte": "Il migliore tra i gratuiti per modificare il testo dentro un PDF e per compilare moduli.",
        "privacy": "I file passano da un server esterno e vengono cancellati dopo qualche ora.",
    },
    "adobe": {
        "nome": "Adobe Acrobat (online) e Acrobat Reader", "link": "https://www.adobe.com/it/acrobat/online.html",
        "dove": "Sito (Chrome) · app Android «Adobe Acrobat Reader»",
        "costo": "L'app Reader è gratis per leggere, commentare, compilare e firmare. Online alcune azioni sono gratis con limiti (serve entrare con un account, anche Google); il resto è a pagamento.",
        "forte": "È lo standard dei PDF: la compilazione dei moduli e la firma con il dito funzionano benissimo.",
        "privacy": "Online i file passano da Adobe; nell'app lavori sul telefono.",
    },
    "pdfgear": {
        "nome": "PDFgear", "link": "https://www.pdfgear.com/", "dove": "Sito · app per Android, iPhone, Windows e Mac",
        "costo": "Gratuito, senza abbonamento né filigrane (controlla sul sito: i piani possono cambiare).",
        "forte": "Un'alternativa gratuita completa ad Acrobat: modifica testo e immagini, converte, firma.",
        "privacy": "Nell'app e nel programma i file restano sul tuo dispositivo.",
    },
    "xodo": {
        "nome": "Xodo PDF", "link": "https://xodo.com/it", "dove": "App Android · sito",
        "costo": "App gratuita per leggere, sottolineare, scrivere sopra, compilare e firmare; le funzioni avanzate sono a pagamento.",
        "forte": "Leggero e veloce sul telefono, ottimo per annotare e firmare un modulo.",
        "privacy": "Nell'app i file restano sul telefono.",
    },
    "stirling": {
        "nome": "Stirling-PDF", "link": "https://stirlingpdf.com/", "dove": "Sito · si può installare sul proprio server (per esperti)",
        "costo": "Open source e gratuito; esiste anche una versione a pagamento per le aziende.",
        "forte": "Il più «aperto» e trasparente: il codice è pubblico e, installato da te, i file non escono mai.",
        "privacy": "Installato sul tuo server i file restano tuoi; sul sito ufficiale passano da un server.",
    },
    "drive": {
        "nome": "Google Drive: Scansiona", "link": "https://play.google.com/store/apps/details?id=com.google.android.apps.docs",
        "dove": "App Android «Google Drive» (già sul telefono)",
        "costo": "Gratis (15 GB condivisi con il tuo account Google).",
        "forte": "Nell'app Drive tocca ➕ → «Scansiona»: fotografa le pagine e ottieni subito un PDF. In Documenti Google: File → Scarica → PDF.",
        "privacy": "Il file viene salvato nel tuo Google Drive.",
    },
    "adobescan": {
        "nome": "Adobe Scan", "link": "https://play.google.com/store/apps/details?id=com.adobe.scan.android",
        "dove": "App Android",
        "costo": "Gratis per scansionare e creare PDF con testo leggibile; alcune funzioni sono a pagamento.",
        "forte": "Raddrizza e pulisce le foto dei fogli e le trasforma in PDF con il testo selezionabile.",
        "privacy": "Il file viene salvato anche nel tuo account Adobe.",
    },
}

# compito: (titolo, a cosa serve, [id dei servizi in ordine di consiglio], come si chiama il comando dentro il servizio, cosa c'è già nell'app)
UPD_COMPITI = [
    ("📷 Trasformare foto o fogli in un PDF", "Hai le foto di una o più pagine e vuoi un solo file PDF.",
     ["drive", "adobescan", "ilovepdf", "pdf24"], "Cerca «JPG in PDF» (o «Immagini in PDF»).",
     "Nell'app: «📤 Esporta» → «📄 In un solo PDF» mette le foto di un documento in un solo PDF, senza uscire."),
    ("📝 Creare un PDF da Word, Excel o testo", "Hai un documento scritto e lo vuoi in PDF.",
     ["drive", "ilovepdf", "pdf24", "smallpdf"], "Cerca «Word in PDF» (o «Excel in PDF»). Con Documenti Google basta File → Scarica → PDF.", ""),
    ("📎 Unire più PDF in uno solo", "Hai più file PDF e ne vuoi uno solo, nell'ordine che scegli.",
     ["pdf24", "ilovepdf", "sejda", "smallpdf"], "Cerca «Unisci PDF».",
     "Nell'app: «📤 Esporta» → «📄 In un solo PDF» unisce già i file di un documento."),
    ("✂️ Dividere un PDF o togliere pagine", "Ti serve solo qualche pagina, oppure vuoi eliminare quelle inutili.",
     ["ilovepdf", "pdf24", "sejda"], "Cerca «Dividi PDF» oppure «Rimuovi pagine» / «Estrai pagine».", ""),
    ("🗜️ Rimpicciolire un PDF (per email e WhatsApp)", "Il file è troppo pesante da inviare.",
     ["ilovepdf", "smallpdf", "pdf24"], "Cerca «Comprimi PDF» e scegli la compressione consigliata.",
     "Nell'app: puoi mandare anche «solo il testo» (senza file) o un «🗜️ ZIP»."),
    ("🔄 Convertire un PDF in Word, Excel o JPG (e viceversa)", "Vuoi cambiare il formato del file.",
     ["ilovepdf", "smallpdf", "pdf24"], "Cerca «PDF in Word» / «PDF in JPG».", ""),
    ("✏️ Modificare il testo o le immagini di un PDF", "Correggere una scritta, aggiungere testo, cancellare o spostare qualcosa.",
     ["sejda", "pdfgear", "adobe", "xodo"], "Cerca «Modifica PDF».", ""),
    ("🖊️ Compilare un modulo e firmare", "Scrivere sopra un modulo e mettere la firma con il dito.",
     ["adobe", "xodo", "smallpdf", "sejda"], "Nell'app Adobe Reader tocca la matita blu → «Compila e firma».", ""),
    ("🔒 Mettere o togliere la password", "Proteggere un PDF, oppure aprirne uno di cui conosci la password.",
     ["ilovepdf", "pdf24", "sejda"], "Cerca «Proteggi PDF» o «Sblocca PDF».",
     "Per i dati più riservati usa lo «Scambio dati» dell'app, che si protegge con una password."),
    ("🔃 Ruotare o riordinare le pagine", "Una pagina è storta o le pagine sono nell'ordine sbagliato.",
     ["ilovepdf", "pdf24", "sejda"], "Cerca «Ruota PDF» oppure «Organizza PDF».", ""),
    ("🔍 Rendere leggibile il testo di una scansione (OCR)", "Vuoi poter cercare e copiare le parole di un PDF fatto da foto.",
     ["ilovepdf", "pdf24", "adobescan"], "Cerca «OCR PDF».",
     "Nell'app: sotto ogni immagine c'è «🔍 Leggi lo scritto», che legge anche la scrittura a mano."),
]


def upd_scheda(sid, chiave, posizione=None):
    """Una riga con il servizio: nome, costo, dove si usa e il pulsante per aprirlo."""
    s = UPD_SERVIZI.get(sid)
    if not s:
        return
    with st.container(border=True):
        pre = f"{posizione}. " if posizione else ""
        st.markdown(f"**{pre}{s['nome']}**  \n💶 {s['costo']}  \n📍 {s['dove']}")
        st.link_button("🌐 Apri " + s["nome"].split(" (")[0], s["link"], width="stretch", key=f"upd_l_{chiave}_{sid}")


def upd_pannello():
    st.caption("Sono **collegamenti a servizi esterni**: si aprono in una nuova scheda. L'app non manda loro nulla. "
               "Prezzi e limiti cambiano: controllali sempre sul sito prima di pagare.")
    st.warning("🔒 **Documenti riservati** (sanitari, identità, contratti): preferisci le app che lavorano sul telefono "
               "(Adobe Acrobat Reader, Xodo, PDFgear) e non usare i siti. Se usi un sito, cancella il file quando hai finito.")
    voci = [c[0] for c in UPD_COMPITI]
    scelta = st.selectbox("1️⃣ Cosa vuoi fare con il PDF?", voci, index=None, placeholder="Tocca qui e scegli…", key="upd_compito")
    if scelta:
        c = next(x for x in UPD_COMPITI if x[0] == scelta)
        st.markdown(f"**{c[0]}**  \n{c[1]}")
        st.markdown("**I servizi, dal più consigliato:**")
        for i, sid in enumerate(c[2], 1):
            upd_scheda(sid, "c", i)
        if c[3]:
            st.info("👉 Dentro il servizio: " + c[3])
        if c[4]:
            st.success("🏠 " + c[4])
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    nomi = {sid: s["nome"] for sid, s in UPD_SERVIZI.items()}
    sv = st.selectbox("2️⃣ Oppure scegli un servizio per conoscerlo", list(nomi), index=None, format_func=lambda x: nomi[x],
                      placeholder="Tocca qui e scegli…", key="upd_servizio")
    if sv:
        s = UPD_SERVIZI[sv]
        with st.container(border=True):
            st.markdown(f"### {s['nome']}")
            st.markdown(f"⭐ **Punto forte:** {s['forte']}  \n💶 **Costo e limiti:** {s['costo']}  \n"
                        f"📍 **Dove si usa:** {s['dove']}  \n🔒 **Privacy:** {s['privacy']}")
            st.link_button("🌐 Apri " + s["nome"].split(" (")[0], s["link"], width="stretch", type="primary", key=f"upd_l_s_{sv}")
