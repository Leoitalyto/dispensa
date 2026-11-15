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
from contextlib import contextmanager

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


@contextmanager
def ut_riquadro(chiave, icona, titolo, a_cosa, colore):
    """Un riquadro colorato con il nome e una riga che dice a cosa serve: dentro ci va il suo contenuto."""
    st.markdown(f"<style>.st-key-utq_{chiave}{{border:2px solid {colore} !important;border-radius:20px !important;"
                f"background:{colore}1c !important;margin-bottom:14px}}"
                f".utq-testa-{chiave}{{background:{colore};color:#fff;border-radius:14px;padding:10px 14px;margin:0 0 8px;line-height:1.25}}"
                f".utq-testa-{chiave} b{{font-size:1.12rem;display:block}}.utq-testa-{chiave} span{{font-size:.85rem;opacity:.95}}</style>",
                unsafe_allow_html=True)
    with st.container(border=True, key=f"utq_{chiave}"):
        st.markdown(f"<div class='utq-testa-{chiave}'><b>{icona} {html.escape(titolo)}</b><span>{html.escape(a_cosa)}</span></div>",
                    unsafe_allow_html=True)
        yield


def ut_gruppo(icona, titolo, a_cosa, colore):
    """La striscia che separa i due gruppi: strumenti DELL'app e strumenti FUORI dall'app."""
    st.markdown(f"<div style='border-left:8px solid {colore};padding:6px 12px;margin:18px 0 10px;border-radius:6px;background:{colore}22'>"
                f"<div style='font-size:1.15rem;font-weight:800'>{icona} {html.escape(titolo)}</div>"
                f"<div style='font-size:.85rem;opacity:.85'>{html.escape(a_cosa)}</div></div>", unsafe_allow_html=True)


def _ut_chiama(nome):
    """Disegna un pezzo della pagina, se c'è; un errore in un pezzo non rompe gli altri."""
    f = globals().get(nome)
    if not callable(f):
        return
    try:
        f()
    except Exception as ex:
        st.warning(f"Questa parte non è disponibile ({type(ex).__name__}).")


def _ut_admin():
    return bool((st.session_state.get("sess") or {}).get("admin"))


def schermata_utilita():
    """La pagina Utilità (si apre dalla Home con la terza icona). Due gruppi: 🔧 per far funzionare l'app · 🌐 strumenti fuori dall'app."""
    st.markdown(
        "<style>@keyframes ut-batte{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.3))}"
        "50%{transform:scale(1.06);filter:drop-shadow(0 0 16px rgba(0,200,215,.95))}}"
        ".ut-hero{background:linear-gradient(135deg,#00838f 0%,#00acc1 55%,#4dd0e1 100%);color:#fff;padding:20px 24px;"
        "border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.15)}"
        ".ut-hero h1{margin:0;font-size:1.8rem;color:#fff;padding:0}.ut-hero p{margin:4px 0 0;opacity:.92}</style>",
        unsafe_allow_html=True)
    nav_barra("utilita")                                 # ← Archivio
    st.markdown("<div class='ut-hero'><h1>🧰 Utilità</h1><p>Scegli il riquadro colorato: strumenti per l'app o da usare fuori dall'app</p></div>",
                unsafe_allow_html=True)
    if "pulsante_info" in globals():                      # il pulsante Informazioni sta sempre in alto
        pulsante_info("utilita")

    ut_gruppo("🔧", "Per far funzionare l'app", "Copie di sicurezza, cose eliminate, scambio dati, aspetto e telefono", "#1565c0")
    with ut_riquadro("sicurezza", "🛟", "Sicurezza dei tuoi dati", "Copia di riserva, ripristino, spazio · cestino delle cose eliminate", "#2e7d32"):
        _ut_chiama("bk_blocco_utilita")
        _ut_chiama("cs_blocco_utilita")
    with ut_riquadro("scambio", "📦", "Scambio con altre persone", "Mandare i tuoi dati a un altro utente di VitaMemo o riceverli", "#ef6c00"):
        _ut_chiama("sc_blocco_utilita")
    with ut_riquadro("aspetto", "⚙️", "Aspetto e telefono", "Testi più grandi, radio, freccia «torna su», libera spazio sul telefono", "#0277bd"):
        _ut_chiama("pn_blocco_utilita")
    if _ut_admin():
        with ut_riquadro("tecnico", "🩺", "Controllo tecnico", "Solo per l'amministratore: l'app funziona bene?", "#546e7a"):
            _ut_chiama("ct_blocco_utilita")

    ut_gruppo("🌐", "Strumenti da usare fuori dall'app", "Si aprono in una nuova scheda del browser: l'app non manda loro i tuoi dati", "#8e24aa")
    with ut_riquadro("musica", "🎵", "Utilità musicali", "Ascolta musica gratis, senza pubblicità e senza registrarti", "#7b1fa2"):
        for u in UTILITA:
            _ut_blocco(u)
    with ut_riquadro("pdf", "📄", "Utilità PDF", "Crea, unisci, comprimi, converti, modifica e firma i PDF con i servizi più usati", "#c62828"):
        _ut_chiama("upd_pannello")
