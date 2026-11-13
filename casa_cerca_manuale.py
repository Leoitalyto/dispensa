# -*- coding: utf-8 -*-
"""CASA · CERCA DENTRO IL MANUALE: scrivi una parola («errore E4», «pulizia filtro», «garanzia») e ti dico in QUALI PAGINE del manuale se ne parla, con la frase e la pagina da vedere.

PRIMA: dei manuali l'app leggeva solo le prime pagine (per riconoscere marca e modello) e non si poteva cercare dentro. ORA:
• PDF con testo: si cerca in TUTTE le pagine all'istante, senza servizi esterni e senza costi.
• Manuale scansionato o fotografato (pagine che sono immagini): la lettura OCR (Tesseract, gratuito, già nell'app) si fa a BLOCCHI di 10 pagine con il pulsante «📖 Leggi le prossime pagine»
  (ogni blocco richiede circa un minuto); quello che è già letto resta in memoria finché l'app non viene riavviata, quindi la volta dopo la ricerca è subito pronta.
• La ricerca ignora maiuscole e accenti; con più parole cerca le pagine che le contengono TUTTE (quelle con più occorrenze per prime). Al massimo 10 pagine, con la frase evidenziata.
• «👁️ Vedi la pagina N» mostra la pagina del manuale per intero.
Nessun dato lascia l'app e non si scrive niente nell'archivio: il testo letto vive solo in memoria. Compare in ogni documento di tipo manuale (Casa → Manuali, e dentro ai Beni)."""
import re as _cm_re
import unicodedata as _cm_ud

import streamlit as st

_CM_MAX_PAGINE = 600                  # oltre questo numero di pagine il manuale si cerca solo nelle prime 600
_CM_BLOCCO = 10                       # pagine lette con l'OCR a ogni tocco del pulsante
_CM_MIN_TESTO = 25                    # una pagina con meno caratteri di questi è considerata «immagine» (da leggere con l'OCR)


def cm_norma(t):
    """Minuscolo, senza accenti, spazi semplici: per confrontare la ricerca con il testo."""
    t = _cm_ud.normalize("NFD", str(t or "").lower())
    t = "".join(c for c in t if _cm_ud.category(c) != "Mn")
    return _cm_re.sub(r"\s+", " ", t).strip()


def cm_parole(domanda):
    """Le parole da cercare (almeno 2 lettere o numeri, senza doppioni)."""
    viste, out = set(), []
    for p in _cm_re.findall(r"[a-z0-9]+", cm_norma(domanda)):
        if len(p) >= 2 and p not in viste:
            viste.add(p)
            out.append(p)
    return out[:8]


def cm_cerca(pagine, domanda, quante=10):
    """pagine: {numero: testo}. Ritorna [(numero, punti, frase)] delle pagine che contengono TUTTE le parole, le più ricche per prime."""
    parole = cm_parole(domanda)
    if not parole:
        return []
    ris = []
    for n, testo in pagine.items():
        if not testo:
            continue
        nt = cm_norma(testo)
        if not all(p in nt for p in parole):
            continue
        punti = sum(nt.count(p) for p in parole)
        piano = _cm_re.sub(r"\s+", " ", str(testo)).strip()
        centro = max(0, cm_norma_conserva(piano).find(parole[0]))               # stessa lunghezza del testo originale: la posizione vale anche per le frasi con accenti
        a, b = max(0, centro - 90), min(len(piano), centro + 150)
        frase = ("…" if a > 0 else "") + piano[a:b] + ("…" if b < len(piano) else "")
        ris.append((n, punti, frase))
    ris.sort(key=lambda r: (-r[1], r[0]))
    return ris[:quante]


def cm_norma_conserva(t):
    """Come cm_norma ma mantiene la stessa lunghezza del testo (sostituisce le lettere accentate con quelle semplici): serve a trovare la posizione nel testo originale."""
    out = []
    for c in str(t):
        d = _cm_ud.normalize("NFD", c.lower())
        d = "".join(x for x in d if _cm_ud.category(x) != "Mn")
        out.append(d[0] if d else c)
    return "".join(out)


def cm_evidenzia(frase, domanda):
    """Le parole cercate in grassetto (la frase non contiene mai codice: si scrive con markdown semplice)."""
    base = cm_norma_conserva(frase)
    spans = []
    for p in cm_parole(domanda):
        for m in _cm_re.finditer(_cm_re.escape(p), base):
            spans.append((m.start(), m.end()))
    spans.sort()
    unite = []
    for s, e in spans:
        if unite and s <= unite[-1][1]:
            unite[-1] = (unite[-1][0], max(unite[-1][1], e))
        else:
            unite.append((s, e))
    out, pos = [], 0
    for s, e in unite:
        out.append(frase[pos:s].replace("*", "").replace("_", " "))
        out.append("**" + frase[s:e].replace("*", "").replace("_", " ") + "**")
        pos = e
    out.append(frase[pos:].replace("*", "").replace("_", " "))
    return "".join(out)


def _cm_apri_pdf(dati):
    try:
        import pymupdf as _mu
    except Exception:
        import fitz as _mu
    return _mu.open(stream=dati, filetype="pdf")


@st.cache_resource(show_spinner=False)
def _cm_memoria():
    """Il testo già letto dei manuali (OCR compreso), per tutta la vita dell'app: {chiave: {pagina: testo}}."""
    return {}


def _cm_chiave(d, dati):
    return f"{d.get('id', '')}:{len(dati or b'')}"


def cm_leggi_testo(mem, dati, mime):
    """Legge il testo che si può leggere SUBITO (PDF con testo). Ritorna (n_pagine, [numeri delle pagine senza testo]). Lo scrive in mem['testo']."""
    if (mime or "").startswith("image/"):
        mem.setdefault("testo", {})
        return 1, ([1] if 1 not in mem["testo"] else [])
    if "pagine" in mem:
        return mem["pagine"], list(mem.get("senza_testo", []))
    doc = _cm_apri_pdf(dati)
    try:
        tot = doc.page_count
        mem["testo"], mem["pagine"] = {}, tot
        mem["troncato"] = tot > _CM_MAX_PAGINE
        senza = []
        for i in range(min(tot, _CM_MAX_PAGINE)):
            t = doc[i].get_text("text", sort=True) or ""
            if len(_cm_re.sub(r"\s+", "", t)) >= _CM_MIN_TESTO:
                mem["testo"][i + 1] = t
            else:
                senza.append(i + 1)
        mem["senza_testo"] = senza
        return tot, senza
    finally:
        doc.close()


def cm_ocr_blocco(mem, dati, mime, numeri):
    """Legge con l'OCR le pagine indicate e le aggiunge a mem['testo']. Ritorna quante pagine ha letto con testo."""
    if not ("_doc_ocr_lingue" in globals() and "_doc_tesseract" in globals() and _doc_ocr_lingue()):
        return -1
    from PIL import Image
    letti = 0
    if (mime or "").startswith("image/"):
        import io
        im = Image.open(io.BytesIO(dati)).convert("RGB")
        im.thumbnail((2400, 2400))
        t = _doc_tesseract(im, "6")
        mem["testo"][1] = t or ""
        return 1 if t else 0
    doc = _cm_apri_pdf(dati)
    try:
        for n in numeri:
            pix = doc[n - 1].get_pixmap(dpi=170, alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            im.thumbnail((2400, 2400))
            t = _doc_tesseract(im, "6") or ""
            mem["testo"][n] = t                                              # anche vuota: la pagina risulta «già provata»
            letti += 1 if t.strip() else 0
    finally:
        doc.close()
    return letti


def _cm_mostra_pagina(dati, mime, n):
    if (mime or "").startswith("image/"):
        st.image(dati, width="stretch")
        return
    doc = _cm_apri_pdf(dati)
    try:
        st.image(doc[n - 1].get_pixmap(dpi=110, alpha=False).tobytes("png"), caption=f"Pagina {n} di {doc.page_count}", width="stretch")
    finally:
        doc.close()


def cm_e_manuale(d):
    tipi = globals().get("_CA_TIPI_MANUALI", set())
    try:
        return d.get("tipo") in tipi or (_ca_argomento_di(d) == "Manuali e istruzioni")
    except Exception:
        return d.get("tipo") in tipi


def cm_pannello(d, k):
    """Il riquadro «🔎 Cerca dentro il manuale» di un documento."""
    f = d.get("file") or {}
    if not (cm_e_manuale(d) and f.get("id")):
        return
    chiave_ap = f"cm_ap_{k}"
    if not st.session_state.get(chiave_ap):
        if st.button("🔎 Cerca dentro il manuale", key=f"cm_b_{k}", width="stretch"):
            st.session_state[chiave_ap] = True
            st.rerun()
        return
    caricato = _ca_leggi_file(f)
    if not caricato:
        st.caption("Il file non è più disponibile: non posso cercare dentro.")
        return
    nome, mime, dati = caricato[0]
    if (mime or "") not in ("application/pdf",) and not (mime or "").startswith("image/"):
        st.caption("Si può cercare dentro i manuali in PDF o in foto.")
        return
    mem = _cm_memoria().setdefault(_cm_chiave(d, dati), {})
    with st.container(border=True):
        c1, c2 = st.columns([5, 2], gap="small")
        c1.markdown("**🔎 Cerca dentro il manuale**")
        if c2.button("✖ Chiudi", key=f"cm_x_{k}", width="stretch"):
            st.session_state[chiave_ap] = False
            st.rerun()
        try:
            with st.spinner("Leggo il manuale…"):
                tot, senza = cm_leggi_testo(mem, dati, mime)
        except Exception as e:
            st.warning(f"Non sono riuscito ad aprire il manuale ({type(e).__name__}).")
            return
        domanda = st.text_input("Cosa cerchi?", key=f"cm_q_{k}", placeholder="per esempio: errore E4, pulizia filtro, garanzia", label_visibility="collapsed")
        da_leggere = [n for n in senza if n not in mem["testo"]]
        if da_leggere:
            letti_img = len(senza) - len(da_leggere)
            st.info(f"📄 Il manuale ha **{tot} pagine**; **{len(senza)}** sono immagini (scansione o foto) e vanno lette una volta sola con il riconoscimento del testo. Già lette: **{letti_img}**.")
            if st.button(f"📖 Leggi le prossime {min(_CM_BLOCCO, len(da_leggere))} pagine (circa {max(1, min(_CM_BLOCCO, len(da_leggere)) // 4 + 1)} min)", key=f"cm_ocr_{k}", width="stretch"):
                with st.spinner("Leggo le pagine… non chiudere l'app."):
                    try:
                        r = cm_ocr_blocco(mem, dati, mime, da_leggere[:_CM_BLOCCO])
                    except Exception as e:
                        r = None
                        st.warning(f"La lettura si è interrotta ({type(e).__name__}). Riprova: le pagine già lette restano.")
                if r == -1:
                    st.warning("Il riconoscimento del testo (OCR) non è disponibile adesso su questo server.")
                else:
                    st.rerun()
        if mem.get("troncato"):
            st.caption(f"Il manuale è molto lungo: cerco solo nelle prime {_CM_MAX_PAGINE} pagine.")
        if not domanda.strip():
            st.caption("Scrivi una o più parole. Con più parole trovo le pagine che le contengono tutte.")
            return
        if not cm_parole(domanda):
            st.caption("Scrivi almeno una parola di 2 lettere.")
            return
        ris = cm_cerca(mem["testo"], domanda)
        if not ris:
            if da_leggere:
                st.warning("Non trovo niente nelle pagine già lette. Leggi le altre pagine con il pulsante qui sopra e riprova.")
            else:
                st.warning("Non trovo queste parole nel manuale. Prova con una sola parola, o con un'altra più semplice.")
            return
        st.success(f"Trovato in {len(ris)} pagin{'a' if len(ris) == 1 else 'e'}" + (" (le più ricche per prime)" if len(ris) > 1 else "") + ".")
        chiave_pag = f"cm_pag_{k}"
        for n, punti, frase in ris:
            with st.container(border=True):
                st.markdown(f"**Pagina {n}** · {punti} volt{'a' if punti == 1 else 'e'}")
                st.markdown(cm_evidenzia(frase, domanda))
                if st.button(f"👁️ Vedi la pagina {n}", key=f"cm_v_{k}_{n}", width="stretch"):
                    st.session_state[chiave_pag] = n
        if st.session_state.get(chiave_pag):
            try:
                _cm_mostra_pagina(dati, mime, st.session_state[chiave_pag])
            except Exception:
                st.info("Non riesco a mostrare questa pagina: usa «Apri / scarica».")


# la riga di un documento mostra sotto anche la ricerca (la funzione originale non si tocca: si «avvolge»)
if "_cm_riga_documento_prima" not in globals() and "_ca_riga_documento" in globals():
    _cm_riga_documento_prima = _ca_riga_documento

    def _ca_riga_documento(d, beni_nomi, pre="", docs=None):                                   # noqa: F811
        r = _cm_riga_documento_prima(d, beni_nomi, pre, docs)
        try:
            cm_pannello(d, f"{pre}{d['id']}")
        except Exception as e:                                                                  # un problema qui non deve rompere l'elenco dei documenti
            st.caption(f"La ricerca nel manuale non è disponibile adesso ({type(e).__name__}).")
        return r
