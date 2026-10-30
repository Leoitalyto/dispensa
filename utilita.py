# -*- coding: utf-8 -*-
"""Pagina «Utilità»: una raccolta di pulsanti (animati) che avviano un'app o un sito.
Sotto ogni pulsante c'è il nome dell'app (la targa): toccandolo si apre il «bugiardino», cioè la spiegazione di cosa fa.
In cima alla pagina c'è sempre il pulsante «Informazioni» (guida, da info_sezioni.py).

PER AGGIUNGERE UN'ALTRA UTILITÀ: aggiungi un elemento alla lista UTILITA qui sotto (id, nome, link, immagini e bugiardino)
e carica le due immagini (pulsante e targa) nella cartella principale del repository.
Caricato da app_dispensa.py. Se mancano le immagini, la pagina funziona lo stesso con pulsanti di testo."""
import base64
import html
import os

import streamlit as st

UTILITA = [
    {
        "id": "velocity",
        "nome": "Velocity Music",
        "link": "https://velocitymusic.uk/",
        "play": "play.webp",
        "play_tondo": True,
        "targa": "velocity.webp",
        "bugiardino": """**Velocity Music** è un lettore e gestore musicale che consente di accedere gratuitamente all'intera libreria di YouTube tramite un'interfaccia moderna, intuitiva e completamente personalizzabile. Tra i suoi punti di forza spiccano l'assenza totale di pubblicità e la mancanza di costi o abbonamenti.

Il progetto è ancora in fase di sviluppo, ma è già utilizzabile gratuitamente da chiunque. Inoltre, è possibile accedervi come ospiti, senza la necessità di creare un account o effettuare alcuna registrazione.

**Principali vantaggi**
- Accesso gratuito alla libreria musicale di YouTube
- Nessuna pubblicità
- Nessun abbonamento richiesto
- Interfaccia semplice, completa e personalizzabile
- Accesso immediato anche senza registrazione
- Progetto in continua evoluzione e aggiornamento""",
    },
    {
        "id": "wimbi",
        "nome": "Wimbi",
        "link": "https://wimbi.app/it/",
        "play": "wimbi_papero.webp",
        "play_tondo": False,
        "targa": "wimbi.webp",
        "bugiardino": """#### Cerca, tocca, ascolta.
Scrivi una canzone o un artista, tocca un risultato e parte. Il tutorial è tutto qui.
- Cerca per canzone o artista
- Un tocco e si parte
- Niente registrazione, niente attese

#### Playlist per tutti i gusti.
Palestra, concentrazione, viaggi lunghi, domenica mattina, quella canzone in loop: crea una playlist per ogni umore e tienile tutte sul tuo dispositivo.
- Creane quante vuoi
- Riordina i brani come preferisci
- Importa playlist da altre app musicali
- Salvate sul tuo dispositivo
- Sincronizzazione su tutti i tuoi dispositivi *(in arrivo)*

#### La musica non si ferma.
Blocca lo schermo, apri un'altra app, metti il telefono in tasca. Wimbi continua a suonare.
- Suona a schermo spento
- Controlli sulla schermata di blocco
- Va d'accordo con chiamate e altre app

#### Sempre qualcosa di nuovo da indossare.
Wimbi ha tantissimi temi e ne aggiungiamo sempre di nuovi. Scegli quello che si adatta al tuo umore, o lascia che i colori seguano la copertina.
- Tanti temi tra cui scegliere
- Nuovi temi aggiunti di continuo
- Colori che seguono la copertina

#### 17 lingue
Wimbi segue la lingua del tuo telefono e puoi cambiarla quando vuoi nelle Impostazioni.
English (Inglese) · Italiano · Español (Spagnolo) · Français (Francese) · Deutsch (Tedesco) · Português, Portugal (Portoghese) · Português, Brasil (Portoghese del Brasile) · Русский (Russo) · Türkçe (Turco) · हिन्दी (Hindi) · Bahasa Indonesia (Indonesiano) · 日本語 (Giapponese) · 한국어 (Coreano) · ไทย (Thailandese) · Tiếng Việt (Vietnamita) · 简体中文 (Cinese semplificato) · 繁體中文 (Cinese tradizionale)

#### Nessun account richiesto. E resterà così.
Puoi usare Wimbi senza account, oggi e in futuro. La tua libreria resta sul tuo dispositivo.
- Nessuna registrazione per iniziare
- Playlist salvate sul tuo dispositivo
- Usare Wimbi senza account sarà sempre possibile

#### Schermo spento. Musica accesa.
Wimbi è fatta per non darti fastidio, mentre cammini, lavori o guidi.
- Controlli da schermata di blocco e widget
- Riprende dopo chiamate e interruzioni
- Cambi brano fluidi""",
    },
]


def _cartella_ut():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return "."


@st.cache_resource(show_spinner=False)
def _ut_uri_cache(nome, data_file):
    try:
        with open(os.path.join(_cartella_ut(), nome), "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode()
    except OSError:
        return ""


def _ut_uri(nome):
    try:
        data = os.path.getmtime(os.path.join(_cartella_ut(), nome))
    except OSError:
        data = 0
    return _ut_uri_cache(nome, data)


@st.dialog("📖 Bugiardino", width="large")
def _dialogo_bugiardino(idu):
    u = next((x for x in UTILITA if x["id"] == idu), None)
    if not u:
        return
    targa = _ut_uri(u["targa"])
    if targa:
        st.markdown(f"<div style='text-align:center;margin-bottom:8px'><img src='{targa}' alt='{html.escape(u['nome'])}' "
                    "style='width:min(320px,80%);height:auto'></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"### {u['nome']}")
    st.markdown(u["bugiardino"])
    st.markdown(f"🔗 Indirizzo: {u['link']}")
    st.link_button("🎵 Avvia " + u["nome"], u["link"], type="primary")


def _ut_blocco(u):
    k = u["id"]
    play = _ut_uri(u["play"])
    targa = _ut_uri(u["targa"])
    css = "<style>"
    if play:
        css += (f".st-key-ut_play_{k} [data-testid='stLinkButton']{{display:flex;justify-content:center}}"
                f".st-key-ut_play_{k} a{{background:url('{play}') center/contain no-repeat !important;border:0 !important;"
                "box-shadow:none !important;color:transparent !important;width:min(190px,52vw) !important;height:auto !important;"
                "aspect-ratio:1/1;min-height:0 !important;padding:0 !important;" + ('border-radius:50% !important;' if u.get("play_tondo", True) else "border-radius:0 !important;") +
                "animation:ut-batte 2s ease-in-out infinite}"
                f".st-key-ut_play_{k} a:active{{transform:scale(.93);animation:none}}"
                f".st-key-ut_play_{k} a p{{font-size:0 !important}}")
    if targa:
        css += (f".st-key-ut_nome_{k} [data-testid='stButton']{{display:flex;justify-content:center}}"
                f".st-key-ut_nome_{k} button{{background:url('{targa}') center/contain no-repeat !important;border:0 !important;"
                "box-shadow:none !important;color:transparent !important;width:min(340px,86vw) !important;height:auto !important;"
                "aspect-ratio:760/233;min-height:0 !important;padding:0 !important;border-radius:0 !important}"
                f".st-key-ut_nome_{k} button p{{font-size:0 !important}}")
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)
    with st.container(key=f"ut_play_{k}"):
        st.link_button("▶️ Avvia " + u["nome"], u["link"], help="Tocca per avviare " + u["nome"])
    st.markdown("<div style='text-align:center;font-size:.8rem;opacity:.75;margin:0 0 6px'>👆 Tocca il pulsante per avviare</div>",
                unsafe_allow_html=True)
    with st.container(key=f"ut_nome_{k}"):
        premuto = st.button(u["nome"], key=f"ut_nome_btn_{k}", help="Tocca per leggere di cosa si tratta")
    st.markdown("<div style='text-align:center;font-size:.8rem;opacity:.75;margin:0 0 18px'>👆 Tocca il nome per leggere il bugiardino</div>",
                unsafe_allow_html=True)
    if premuto:
        _dialogo_bugiardino(k)


def schermata_utilita():
    """La pagina Utilità (si apre dalla Home con la terza icona, accanto a Salute e I miei documenti)."""
    st.markdown(
        "<style>@keyframes ut-batte{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.3))}"
        "50%{transform:scale(1.06);filter:drop-shadow(0 0 16px rgba(0,200,215,.95))}}"
        ".ut-hero{background:linear-gradient(135deg,#00838f 0%,#00acc1 55%,#4dd0e1 100%);color:#fff;padding:20px 24px;"
        "border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.15)}"
        ".ut-hero h1{margin:0;font-size:1.8rem;color:#fff;padding:0}.ut-hero p{margin:4px 0 0;opacity:.92}</style>",
        unsafe_allow_html=True)
    nav_barra("utilita")                                 # ← Archivio
    st.markdown("<div class='ut-hero'><h1>🧰 Utilità</h1><p>Tocca il pulsante per avviare · tocca il nome per sapere cos'è</p></div>",
                unsafe_allow_html=True)
    if "pulsante_info" in globals():                      # il pulsante Informazioni sta sempre in alto
        pulsante_info("utilita")
    for u in UTILITA:
        _ut_blocco(u)
