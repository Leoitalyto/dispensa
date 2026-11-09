# -*- coding: utf-8 -*-
"""UTILITÀ · «🩺 Controllo tecnico dell'app» (solo amministratore).

Serve a vedere in un colpo d'occhio se tutto ciò che l'app usa è a posto, soprattutto DOPO un aggiornamento di Streamlit o di una libreria:
• la versione di Streamlit in uso e se è FISSATA nel file requirements.txt (se non lo è, un aggiornamento automatico potrebbe cambiare qualcosa senza che tu lo sappia);
• le funzioni di Streamlit che l'app usa (la nuova «st.iframe», i comandi in JavaScript di «st.html», le schede con memoria, le finestre…): se una manca, dice cosa smette di funzionare;
• i programmi per leggere documenti e foto (riconoscimento del testo, PDF, immagini);
• l'archivio dei dati (GitHub o locale) e la memoria veloce;
• le parti dell'app che NON si sono caricate (l'app continua a funzionare, ma quella parte no).
Non modifica niente: legge e basta."""
import inspect
import os

import streamlit as st

_CT_ICONE = {"ok": "🟢", "attenzione": "🟡", "errore": "🔴"}


def _ct_firma(funzione):
    try:
        return set(inspect.signature(funzione).parameters)
    except Exception:
        return set()


def ct_controlli(percorso_requirements=None):
    """[(esito, voce, dettaglio)]: esito è «ok», «attenzione» o «errore»."""
    out = []
    ver = getattr(st, "__version__", "?")
    # la versione di Streamlit e se è fissata
    try:
        pr = percorso_requirements or os.path.join(globals().get("_cartella", "."), "requirements.txt")
        righe = [r.strip() for r in open(pr, encoding="utf-8").read().splitlines() if r.strip().lower().startswith("streamlit")]
        if any("==" in r for r in righe):
            out.append(("ok", "Versione di Streamlit", f"in uso la {ver}; è fissata nel file requirements.txt ({righe[0]}): non cambia da sola."))
        else:
            out.append(("attenzione", "Versione di Streamlit", f"in uso la {ver}, ma NON è fissata nel file requirements.txt: dopo una reinstallazione potrebbe arrivare una versione più nuova e cambiare qualcosa. Consigliato scrivere «streamlit=={ver}»."))
    except Exception:
        out.append(("attenzione", "Versione di Streamlit", f"in uso la {ver}; non riesco a leggere il file requirements.txt."))
    # le funzioni che l'app usa
    if hasattr(st, "iframe"):
        out.append(("ok", "Funzione nuova «st.iframe»", "c'è: pulsante arancione, voce, fotocamera, scanner, radio… usano questa."))
    else:
        out.append(("attenzione", "Funzione nuova «st.iframe»", "manca in questa versione di Streamlit: l'app usa la funzione vecchia (può smettere di funzionare in futuro)."))
    if "unsafe_allow_javascript" in _ct_firma(st.html):
        out.append(("ok", "Comandi JavaScript in «st.html»", "disponibili."))
    else:
        out.append(("attenzione", "Comandi JavaScript in «st.html»", "non disponibili: alcune funzioni usano l'altra strada (st.iframe)."))
    try:
        sch = _ct_firma(globals().get("_tabs_originale") or st.tabs)                  # la funzione VERA di Streamlit (st.tabs è sostituita dall'app con una versione che ricorda la scheda)
        out.append(("ok" if "on_change" in sch else "attenzione", "Schede che ricordano dove eri", "disponibili." if "on_change" in sch else "non disponibili: dopo ogni azione si torna alla prima scheda."))
    except Exception:
        pass
    for nome, voce in (("dialog", "Finestre sopra la pagina"), ("fragment", "Aggiornamenti parziali"), ("pills", "Scelte a pillole"), ("toggle", "Interruttori"), ("popover", "Riquadri a comparsa")):
        out.append(("ok" if hasattr(st, nome) else "errore", voce, "disponibili." if hasattr(st, nome) else f"manca «st.{nome}»: parte dell'app non funzionerà."))
    # programmi di lettura
    try:
        lingue = _doc_ocr_lingue() if "_doc_ocr_lingue" in globals() else ""
        out.append(("ok" if lingue else "errore", "Lettura del testo nelle foto (Tesseract)", f"lingue: {lingue}." if lingue else "non trovato: foto e PDF scansionati non si leggono (serve «tesseract-ocr» nel file packages.txt)."))
    except Exception as ex:
        out.append(("errore", "Lettura del testo nelle foto (Tesseract)", f"errore: {type(ex).__name__}"))
    for modulo, voce in (("pymupdf", "Lettura dei PDF (PyMuPDF)"), ("pypdf", "Lettura dei PDF (pypdf)"), ("PIL", "Immagini (Pillow)"), ("cv2", "Immagini (OpenCV)"), ("cryptography", "Cifratura dei file")):
        try:
            __import__(modulo)
            out.append(("ok", voce, "c'è."))
        except Exception:
            out.append(("attenzione" if modulo in ("pypdf", "cv2") else "errore", voce, "NON c'è: parte delle funzioni non va."))
    # archivio dei dati
    try:
        arch = crea_archivio()
        tipo = type(arch).__name__
        try:
            ve = str(st.secrets.get("ARCHIVIO_VELOCE", "si")).strip().lower() not in ("no", "off", "0", "spento")
        except Exception:
            ve = True
        out.append(("ok", "Archivio dei dati", f"{'GitHub (privato)' if tipo == 'ArchivioGitHub' else 'cartella locale (prova)'}; memoria veloce {'accesa' if ve else 'spenta'}."))
    except Exception as ex:
        out.append(("errore", "Archivio dei dati", f"errore: {type(ex).__name__}: {str(ex)[:80]}"))
    # le parti che non si sono caricate
    falliti = st.session_state.get("_moduli_falliti") or []
    if falliti:
        out.append(("errore", "Parti dell'app non caricate", "; ".join(f"{n} ({e})" for n, e in falliti[:6])))
    else:
        out.append(("ok", "Parti dell'app", "tutte caricate."))
    return out


def ct_pannello():
    c = ct_controlli()
    n_att = sum(1 for e, _v, _d in c if e == "attenzione")
    n_err = sum(1 for e, _v, _d in c if e == "errore")
    if n_err:
        st.error(f"🔴 {n_err} cose da sistemare" + (f" e {n_att} da guardare" if n_att else "") + ".")
    elif n_att:
        st.warning(f"🟡 Tutto funziona, {n_att} cose da guardare.")
    else:
        st.success("🟢 Tutto a posto.")
    for esito, voce, dettaglio in c:
        st.markdown(f"{_CT_ICONE[esito]} **{voce}** — {dettaglio}")
    st.caption("Dopo ogni aggiornamento dell'app o di Streamlit guarda qui: se compare un 🔴 o un 🟡 nuovo, dimmelo e lo sistemo.")


if "_ct_utilita_prima" not in globals() and "schermata_utilita" in globals():
    _ct_utilita_prima = schermata_utilita


def schermata_utilita():                                                   # noqa: F811
    r = _ct_utilita_prima()
    try:
        if bool((st.session_state.get("sess") or {}).get("admin")):
            with st.expander("🩺 Controllo tecnico dell'app (solo amministratore)"):
                ct_pannello()
    except Exception:
        pass
    return r
