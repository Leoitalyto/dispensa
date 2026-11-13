# -*- coding: utf-8 -*-
"""ASSISTENTE · gruppo D del progetto di ottimizzazione. Solo AGGIUNTE all'assistente che già esiste (assistente.py): niente è rifatto.

1) CONTESTO DELLA SCHERMATA. «📖 Spiegami questa pagina» e le domande brevi («come lo modifico?») funzionavano solo in Dispensa, Salute, Documenti e Utilità. Ora l'assistente sa anche in quale punto di Casa, Lavoro, Auto (garage, scadenze, diagnostica, fotografare una spia, proposte…) e Archivio ti trovi. Il contesto è «sezione:sottosezione» e si ricava da cosa è aperto, senza leggere dati personali.
2) VOCE: velocità regolabile (🐢 lenta · normale · veloce). Il pulsante sta nel pannello dell'assistente accanto a «Voce»; la scelta resta salvata sul telefono (localStorage `asst_rate`).
3) DOMANDE SENZA RISPOSTA: l'assistente non inventa. Se non trova una procedura lo dice con onestà («non voglio indicarti una procedura che potrebbe non funzionare») e suggerisce come proseguire.
4) 📚 CERCA NEI MIEI MANUALI E DOCUMENTI: una finestra (sotto il pulsante «Informazioni» di Dispensa, Casa, Auto, Utilità) che cerca nei manuali, nelle garanzie e nei documenti dei beni di Casa e nei documenti dei veicoli dell'UTENTE (mai di altre persone). Non carica tutto l'archivio: sceglie al massimo 3 documenti in base a titolo, marca, modello e bene, ne legge il testo UNA volta (tenuto in memoria un'ora), lo divide in passaggi e mostra i 3 più pertinenti con documento, pagina e posizione. Il passaggio si può far leggere ad alta voce. Non spiega e non riassume con l'intelligenza artificiale (servirebbe inviare il manuale a un servizio esterno): mostra le parole del manuale. Se non trova niente, lo dice senza inventare.
Nessun dato lascia l'app. Solo italiano. Caricato dopo assistente.py e guida_extra.py."""
import hashlib
import json
import math
import re
import unicodedata

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# 1) contesto
# ---------------------------------------------------------------------------------------------------------------------
_AE_CTX = {
    "casa": "c_cosa", "casa:amministrazione": "c_amministrazione", "casa:documenti": "c_manuali", "casa:manutenzioni": "c_manutenzioni", "casa:riferimenti": "c_riferimenti",
    "lavoro": "l_cosa", "lavoro:buste": "l_carica", "lavoro:anni": "l_anni", "lavoro:cu": "l_cu", "lavoro:inps": "l_inps", "lavoro:contatti": "l_rubrica",
    "auto": "au_garage", "auto:scheda": "au_aggiungi", "auto:scadenze": "au_scadenze", "auto:manutenzione": "au_manut", "auto:rifornimenti": "au_manut",
    "auto:ricambi": "au_manut", "auto:emergenza": "au_emerg", "auto:patente": "au_patente", "auto:viaggi": "au_viaggi", "auto:diagnostica": "au_diag",
    "auto:foto": "au_foto_spia", "auto:archivio": "au_proposte", "auto:codici": "au_diag", "auto:dispositivo": "au_diag", "auto:storico": "au_diag", "auto:assistente": "au_diag",
    "archivio": "ar_cosa", "archivio:tabella": "ar_cercare",
}
_AE_AUTO_SEZ = [("scheda", "scheda"), ("scadenze", "scadenze"), ("manutenzione", "manutenzione"), ("rifornimenti", "rifornimenti"), ("ricambi", "ricambi"), ("emergenza", "emergenza"), ("patente", "patente"), ("diagnostica", "diagnostica")]
_AE_LV = [("buste", "buste"), ("anno", "anni"), ("certificazione", "cu"), ("inps", "inps"), ("sindacato", "contatti")]


def ae_contesto(contesto):
    """Da «auto», «lavoro», «archivio» a «auto:diagnostica»… secondo cosa è aperto adesso (solo le scelte fatte nell'interfaccia)."""
    try:
        ss = st.session_state
        if contesto == "auto" and ss.get("au_vista") == "sezione":
            et = str(ss.get("au_sezione") or "").lower()
            if "diagnostica" in et:
                vd = str(ss.get("dg_vista") or "")
                return "auto:" + (vd if vd in ("foto", "archivio", "dispositivo", "codici", "storico", "assistente") else "diagnostica")
            for chiave, nome in _AE_AUTO_SEZ:
                if chiave in et:
                    return "auto:" + nome
        if contesto == "lavoro":
            et = str(ss.get("lv_sezione") or "").lower()
            for chiave, nome in _AE_LV:
                if chiave in et:
                    return "lavoro:" + nome
        if contesto == "archivio" and str(ss.get("ar_vista") or "").lower().startswith("tabella"):
            return "archivio:tabella"
    except Exception:
        pass
    return contesto


try:
    _CTX_GUIDA.update(_AE_CTX)
    _TAB_CTX["casa"] = ["amministrazione", "casa", "documenti", "manutenzioni", "riferimenti"]          # l'ordine delle schede in basso nella pagina Casa: Amministrazione, Beni, Documenti, Manutenzioni, Riferimenti
except NameError:
    pass

if "_ae_assistente_prima" not in globals() and "assistente" in globals():
    _ae_assistente_prima = assistente


def assistente(contesto):
    try:
        contesto = ae_contesto(contesto)
    except Exception:
        pass
    return _ae_assistente_prima(contesto)


# ---------------------------------------------------------------------------------------------------------------------
# 2) voce: velocità regolabile  (si modifica il testo dello script dell'assistente; se un punto non si trova, resta com'era)
# ---------------------------------------------------------------------------------------------------------------------
AE_VOCE_OK = False


def _ae_patch_voce():
    global _JS_ASSISTENTE, AE_VOCE_OK
    js = _JS_ASSISTENTE
    if "velocita()" in js:
        AE_VOCE_OK = True
        return
    Q = '"'                                                                                          # le virgolette dentro lo script dell'assistente sono normali
    coppie = [
        ("u.rate = 1; u.pitch = 1.05;", "u.rate = velocita(); u.pitch = 1.05;"),
        ("data-az=" + Q + "silenzio" + Q + " data-ui=" + Q + "a_silenzio" + Q + "></button>",
         "data-az=" + Q + "vel" + Q + "></button>' +\n      '<button class=" + Q + "asst-b grigio" + Q + " data-az=" + Q + "silenzio" + Q + " data-ui=" + Q + "a_silenzio" + Q + "></button>"),
        ("btnVoce = pan.querySelector('[data-az=" + Q + "voce" + Q + "]');", "btnVoce = pan.querySelector('[data-az=" + Q + "voce" + Q + "]'), btnVel = pan.querySelector('[data-az=" + Q + "vel" + Q + "]');"),
        ("if (!SS) { btnVoce.style.display = 'none';", "if (!SS) { btnVel.style.display = 'none'; btnVoce.style.display = 'none';"),
        ("function aggiornaVoceBtn() { btnVoce.textContent = voceOn ? T('a_voce_on') : T('a_voce_off'); }",
         "function velocita() { var v = parseFloat(leggi('asst_rate', '1')); return (v >= 0.5 && v <= 2) ? v : 1; }\n"
         "  function aggiornaVoceBtn() { btnVoce.textContent = voceOn ? T('a_voce_on') : T('a_voce_off'); var v = velocita(); btnVel.textContent = T('a_vel') + ': ' + T(v < 0.9 ? 'a_vel_0' : (v > 1.1 ? 'a_vel_2' : 'a_vel_1')); }"),
        ("else if (az === 'voce') {", "else if (az === 'vel') { var v0 = velocita(), n0 = v0 < 0.9 ? 1 : (v0 > 1.1 ? 0.8 : 1.25); scrivi('asst_rate', String(n0)); aggiornaVoceBtn(); if (SS) parla(T('a_vel_prova')); }\n    else if (az === 'voce') {"),
    ]
    for a, b in coppie:
        if js.count(a) != 1:
            return                                                                                  # un punto non si trova: l'assistente resta com'era (nessun danno)
    for a, b in coppie:
        js = js.replace(a, b)
    _JS_ASSISTENTE = js
    AE_VOCE_OK = True


AE_RICERCA_OK = False


def _ae_patch_ricerca():
    """Una domanda senza senso non deve «trovare» una scheda a caso: con 3 o più parole che contano, una sola parola in comune con una scheda non basta (a meno che l'azione, per esempio «eliminare», non coincida)."""
    global _JS_ASSISTENTE, AE_RICERCA_OK
    js = _JS_ASSISTENTE
    if "forte = true" in js:
        AE_RICERCA_OK = True
        return
    coppie = [
        ("var pt = 0, tr = 0, bonus = 0, ex = false;", "var pt = 0, tr = 0, bonus = 0, ex = false, forte = false;"),
        ("if (combacia(x, e.t)) { pt += 3; tr++; } else if (combacia(x, e.k)) { pt += 2; tr++; }", "if (combacia(x, e.t)) { pt += 3; tr++; forte = true; } else if (combacia(x, e.k)) { pt += 2; tr++; forte = true; }"),
        ("if (pt + bonus > 0) ris.push(", "if (pt + bonus > 0 && (bonus > 0 || tr >= 2 || q.length <= 2)) ris.push("),
    ]
    if any(js.count(a_) != 1 for a_, _b in coppie):
        return                                                                                  # un punto non si trova: resta com'era
    for a_, b_ in coppie:
        js = js.replace(a_, b_)
    _JS_ASSISTENTE = js
    AE_RICERCA_OK = True


try:
    UI_IT.update({"a_vel": "🐢 Velocità della voce", "a_vel_0": "lenta", "a_vel_1": "normale", "a_vel_2": "veloce", "a_vel_prova": "Questa è la mia voce con la nuova velocità.",
                  # 3) niente procedure inventate
                  "a_trov_t": "Non trovo istruzioni su questo",
                  "a_trov_x": "Non voglio indicarti una procedura che potrebbe non funzionare: forse questa funzione non esiste nell'app, oppure uso parole diverse dalle tue. Prova con altre parole (anche una sola: foto, scadenza, password) o scegli un argomento qui sotto. Se riguarda un tuo apparecchio, apri «📚 Cerca nei miei manuali e documenti»."})
    _ae_patch_voce()
    _ae_patch_ricerca()
    _extra_stop = ("faccio", "fare", "fai", "fatto", "posso", "puoi", "devo", "voglio", "vorrei", "quanto", "quanti", "quanta", "quante", "quale", "quali", "qual")      # parole comuni che non dicono di che cosa si parla
    _it_stop = _STOP_LANG.get("it", ())
    _STOP_LANG["it"] = (_it_stop | set(_extra_stop)) if isinstance(_it_stop, (set, frozenset)) else (type(_it_stop)(list(_it_stop) + [x for x in _extra_stop if x not in _it_stop]) if isinstance(_it_stop, (list, tuple)) else _it_stop)
except NameError:
    pass


# ---------------------------------------------------------------------------------------------------------------------
# 4) cercare nei manuali e nei documenti dell'utente
# ---------------------------------------------------------------------------------------------------------------------
_MR_STOP = set("il lo la le gli un una uno di da del dello della dei degli delle in con su per tra fra che chi cosa come dove quando perche non mi ti si ci vi ho ha hai sono e ed o ma se piu poco molto questo questa questi queste quello quella al allo alla ai agli alle nel nello nella nei negli nelle sul sullo sulla sui sugli sulle puo posso devo fare fatto faccio vuole voglio vorrei anche solo gia ancora quanto quale quali".split())
_MR_TIPI_LAVORO = {"Busta paga", "Certificazione Unica (CU)", "Documento INPS"}
# i tipi VERI di Casa (CA_TIPI) che sono manuali o istruzioni; gli altri documenti (bollette, contratti…) si cercano solo se il nome o il bene c'entrano con la domanda
_MR_TIPI_MANUALE = ("Manuale d'uso", "Manuale di installazione", "Manuale di manutenzione", "Scheda tecnica", "Certificato di garanzia", "Libretto di impianto", "Dichiarazione di conformità", "Istruzioni di montaggio")
MR_MAX_DOC = 5              # al massimo 5 documenti letti per ricerca: prima quelli che c'entrano per nome o bene (fino a 3), poi i manuali
MR_MAX_DOC_TUTTI = 12
MR_MAX_BYTE = 25 * 1024 * 1024
MR_MAX_PAGINE = 150
MR_OCR_PAGINE = 10                # pagine di una scansione lette con il riconoscimento del testo ad ogni ricerca (per documento); si possono chiedere altre pagine con un pulsante
MR_OCR_PASSO = 12


def _mr_norm(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def mr_token(testo):
    """Le parole che contano di una frase (senza parole comuni), in forma ridotta per confrontare «filtro/filtri»."""
    out = []
    for p in re.findall(r"[a-z0-9]{3,}", _mr_norm(testo)):
        if p in _MR_STOP:
            continue
        out.append(p[:6] if len(p) > 6 else p)
    return list(dict.fromkeys(out))


def _mr_ridotte(testo):
    return [p[:6] if len(p) > 6 else p for p in re.findall(r"[a-z0-9]{3,}", _mr_norm(testo))]


def mr_documenti(d):
    """I documenti in cui cercare: SOLO quelli dell'utente (manuali, garanzie e documenti dei beni di Casa; documenti dei veicoli). [{id, titolo, dove, riferimenti[], meta, fonte}]"""
    out = []
    casa = (d or {}).get("casa") or {}
    beni = {b.get("id"): b for b in casa.get("beni", []) if isinstance(b, dict)}
    for x in casa.get("documenti", []) or []:
        if not isinstance(x, dict) or x.get("tipo") in _MR_TIPI_LAVORO:
            continue
        rif = x.get("file") if isinstance(x.get("file"), dict) else None
        if not rif or not rif.get("id"):
            continue
        tipo_x = str(x.get("tipo") or "")
        manuale = tipo_x in _MR_TIPI_MANUALE or tipo_x.startswith("Manuale") or tipo_x in ("Garanzia", "Manuale") or x.get("argomento") == "Manuali e istruzioni" or bool(x.get("bene_id"))
        bene = beni.get(x.get("bene_id")) or {}
        meta = " ".join(str(v) for v in (x.get("titolo"), x.get("tipo"), x.get("argomento"), x.get("marca"), x.get("modello"), x.get("categoria"), x.get("sottocategoria"), bene.get("nome"), bene.get("marca"), bene.get("modello")) if v)
        out.append({"id": x.get("id"), "titolo": x.get("titolo") or rif.get("nome") or "Documento", "dove": "Casa → 📚 Documenti" + (f" (bene: {bene.get('nome')})" if bene.get("nome") else ""), "riferimenti": [rif], "meta": meta, "fonte": "casa", "manuale": manuale,
                    "marchio": " ".join(str(v) for v in (x.get("marca"), x.get("modello"), bene.get("nome"), bene.get("marca"), bene.get("modello")) if v)})
    for v in ((d or {}).get("auto") or {}).get("veicoli", []) or []:
        if not isinstance(v, dict):
            continue
        nome_v = " ".join(str(z) for z in (v.get("marca"), v.get("modello"), v.get("targa")) if z)
        for x in v.get("documenti", []) or []:
            if not isinstance(x, dict):
                continue
            ris = [r for r in (x.get("files") or []) if isinstance(r, dict) and r.get("id")]
            if not ris:
                continue
            out.append({"id": x.get("id"), "titolo": (x.get("titolo") or x.get("tipo") or "Documento") + (f" · {v.get('targa')}" if v.get("targa") else ""), "dove": "Auto → " + (nome_v or "veicolo") + " → 🪪 Scheda e documenti",
                        "riferimenti": ris[:2], "meta": " ".join(str(z) for z in (x.get("titolo"), x.get("tipo"), x.get("categoria"), nome_v) if z), "fonte": "auto", "marchio": nome_v, "manuale": "manuale" in _mr_norm(x.get("titolo", "") + " " + str(x.get("tipo", "")))})
    return out


def mr_scegli(documenti, domanda, tutti=False):
    """Quali documenti leggere: prima quelli che c'entrano per titolo/marca/modello/bene; se nessuno, i manuali. Ritorna (scelti, altri_non_letti)."""
    tok = mr_token(domanda)
    punti = []
    for doc in documenti:
        m = set(_mr_ridotte(doc["meta"]))
        p = sum(1 for t in tok if t in m)
        punti.append((p, 1 if doc.get("manuale") else 0, doc))
    punti.sort(key=lambda z: (-z[0], -z[1]))
    limite = MR_MAX_DOC_TUTTI if tutti else MR_MAX_DOC
    con = [z[2] for z in punti if z[0] > 0]                                  # quelli che c'entrano per nome, marca, modello o bene
    resto = [z[2] for z in punti if z[0] == 0]
    # «dello stesso apparecchio»: il manuale della caldaia può non avere «caldaia» nel nome ma ha la stessa marca o lo stesso modello della fattura o del bene che lo hanno
    segni = set()
    for doc in con:
        segni.update(_mr_ridotte(doc.get("marchio", "")))
    segni -= set(tok)
    segni = {x for x in segni if len(x) >= 4}
    stesso = []
    for doc in resto:
        if segni & set(_mr_ridotte(doc["meta"])):
            stesso.append(dict(doc, rel=True))
    stesso_id = {(d_["id"], d_["titolo"]) for d_ in stesso}
    manuali = [d_ for d_ in resto if d_.get("manuale") and (d_["id"], d_["titolo"]) not in stesso_id]
    altri = [d_ for d_ in resto if not d_.get("manuale") and (d_["id"], d_["titolo"]) not in stesso_id]
    scelti = con[:3 if not tutti else limite]
    for doc in stesso + manuali + altri:
        if len(scelti) >= limite:
            break
        scelti.append(doc)
    return scelti, max(0, len(documenti) - len(scelti))


@st.cache_data(ttl=3600, max_entries=16, show_spinner=False)
def _mr_pagine_file(uid, fid, nome, mime, dimensione):
    """([(pagina, testo)], pagine totali, [indici delle pagine senza testo]) di un file (lo si legge UNA volta e si tiene un'ora in memoria). `uid` fa parte della chiave: la memoria è per persona."""
    try:
        file_ = _ca_leggi_file({"id": fid, "nome": nome, "mime": mime})
    except Exception:
        return [], 0, []
    if not file_:
        return [], 0, []
    nome_, mime_, dati = file_[0]
    if not dati or len(dati) > MR_MAX_BYTE:
        return [], 0, []
    pagine, totale, vuote = [], 0, []
    if mime_ == "application/pdf":
        try:
            try:
                import pymupdf as _mu
            except Exception:
                import fitz as _mu
            doc = _mu.open(stream=dati, filetype="pdf")
            totale = min(MR_MAX_PAGINE, doc.page_count)
            for i in range(totale):
                try:
                    pagina = doc[i]
                    t = _mr_testo_pagina(pagina.get_text("blocks"), float(pagina.rect.width))
                except Exception:
                    t = ""
                if t.strip():
                    pagine.append((i + 1, t[:9000]))
                if len(t.strip()) < 25:                                          # pagina che è solo un'immagine (scansione)
                    vuote.append(i)
            doc.close()
        except Exception:
            pagine, totale, vuote = [], 0, []
    if not pagine and mime_ != "application/pdf":                                              # una FOTO: lettura con OCR (una pagina sola); le scansioni in PDF si leggono a blocchi, in mr_cerca
        try:
            testo, _info = ca_estrai_testo(nome_, mime_, dati, max_pagine=3, max_car=12000)
            if (testo or "").strip():
                pagine.append((1, testo))
        except Exception:
            pass
    return pagine, totale, vuote


def _mr_pulisci(t):
    """Un paragrafo da leggere: le parole spezzate a fine riga («spe-\ngne») si riattaccano e le righe diventano una frase continua."""
    t = re.sub(r"(\w)-\s*\n\s*([a-zàèéìòùäöü])", r"\1\2", t or "")
    t = re.sub(r"\s*\n\s*", " ", t)
    return re.sub(r"[ \t]+", " ", t).strip()


def _mr_ordina_blocchi(blocchi, larghezza):
    """I blocchi di testo di una pagina nell'ordine in cui si leggono: le pagine dei manuali sono spesso su DUE colonne; tra due elementi a tutta larghezza (titoli, tabelle)
    si legge prima tutta la colonna di sinistra, poi tutta quella di destra."""
    larghi = sorted([b for b in blocchi if (b[2] - b[0]) >= 0.6 * larghezza], key=lambda b: b[1])
    stretti = [b for b in blocchi if (b[2] - b[0]) < 0.6 * larghezza]
    out, y0 = [], -1.0
    for lg in larghi + [None]:
        y1 = lg[1] if lg is not None else 1e9
        fascia = [b for b in stretti if y0 <= b[1] < y1]
        sx = sorted([b for b in fascia if (b[0] + b[2]) / 2 < larghezza / 2], key=lambda b: (round(b[1]), b[0]))
        dx = sorted([b for b in fascia if (b[0] + b[2]) / 2 >= larghezza / 2], key=lambda b: (round(b[1]), b[0]))
        out += sx + dx
        if lg is not None:
            out.append(lg)
            y0 = lg[3] - 0.01
    return out


def _mr_testo_pagina(blocchi, larghezza):
    """Il testo di una pagina: un paragrafo per blocco, nell'ordine di lettura, separati da una riga vuota."""
    veri = [b for b in blocchi if len(b) >= 5 and (len(b) < 7 or b[6] == 0) and str(b[4]).strip()]
    paragrafi = [_mr_pulisci(b[4]) for b in _mr_ordina_blocchi(veri, larghezza or 595.0)]
    return "\n\n".join(x for x in paragrafi if x)


def _mr_ocr_disponibile():
    return "_doc_ocr_lingue" in globals() and "_doc_tesseract" in globals() and bool(_doc_ocr_lingue())


def _mr_apri_pdf(dati):
    try:
        import pymupdf as _mu
    except Exception:
        import fitz as _mu
    return _mu.open(stream=dati, filetype="pdf")


@st.cache_data(ttl=3600, max_entries=60, show_spinner=False)
def _mr_ocr_blocco(uid, fid, nome, mime, dimensione, indici):
    """Legge con il riconoscimento del testo (OCR) alcune pagine di una scansione. [(numero pagina, testo)]. Lento: si tiene il risultato un'ora."""
    out = []
    try:
        from PIL import Image
        file_ = _ca_leggi_file({"id": fid, "nome": nome, "mime": mime})
        doc = _mr_apri_pdf(file_[0][2])
        for i in indici:
            if i >= doc.page_count:
                continue
            pix = doc[i].get_pixmap(dpi=160, alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            im.thumbnail((2400, 2400))
            grezzo = _doc_tesseract(im, "6") or ""
            paragrafi = [_mr_pulisci(b) for b in re.split(r"\n\s*\n", grezzo)]
            testo = "\n\n".join(x for x in paragrafi if x)
            if testo.strip():
                out.append((i + 1, testo[:9000]))
        doc.close()
    except Exception:
        pass
    return out


def _mr_passaggi(pagine, lung=900):
    out = []
    for n, t in pagine:
        blocchi = [b.strip() for b in re.split(r"\n\s*\n", t) if b.strip()] or [t.strip()]
        cur = ""
        for b in blocchi:
            b = re.sub(r"[ \t]+", " ", b)
            if len(cur) + len(b) <= lung:
                cur = (cur + "\n\n" + b).strip()
            else:
                if cur:
                    out.append((n, cur))
                while len(b) > lung:                                                           # un paragrafo lungo: si spezza alla fine di una frase, mai a metà parola
                    taglio = max(b.rfind(". ", 0, lung), b.rfind("; ", 0, lung), b.rfind(": ", 0, lung))
                    if taglio < lung // 3:
                        taglio = b.rfind(" ", 0, lung)
                    taglio = taglio if taglio > 0 else lung
                    out.append((n, b[:taglio + 1].strip()))
                    b = b[taglio + 1:].strip()
                cur = b
        if cur:
            out.append((n, cur))
    return out


def mr_cerca(d, domanda, tutti=False, massimo=3, ocr=None):
    """Cerca nei documenti dell'utente. Ritorna {"passaggi": [...], "letti": [titoli], "non_letti": n, "nessun_documento": bool, "scansioni": [...]}.
    `ocr` = {id del file: pagine di scansione in più da leggere con il riconoscimento del testo}."""
    ocr = ocr or {}
    scansioni = []
    docs = mr_documenti(d)
    if not docs:
        return {"passaggi": [], "letti": [], "non_letti": 0, "nessun_documento": True, "scansioni": []}
    tok = mr_token(domanda)
    scelti, non_letti = mr_scegli(docs, domanda, tutti)
    letti, cand, df, n_tot = [], [], {}, 0
    for doc in scelti:
        rif = doc["riferimenti"][0]
        meta_doc = set(_mr_ridotte(doc["meta"]))
        hit_doc = sum(1 for t in tok if t in meta_doc) + (1 if doc.get("rel") else 0)   # parole della domanda già nel nome del documento / del bene (o stesso apparecchio)
        pagine, totale, vuote, r_usato = [], 0, [], doc["riferimenti"][0]
        for r in doc["riferimenti"]:
            pg_, tot_, vu_ = _mr_pagine_file((st.session_state.get("sess") or {}).get("uid", ""), r.get("id"), r.get("nome", ""), r.get("mime", ""), int(r.get("dimensione") or 0))
            if pg_ or vu_:
                pagine, totale, vuote, r_usato = pg_, tot_, vu_, r
                break
        # le pagine che sono solo immagini (scansioni) si leggono con il riconoscimento del testo, poche alla volta (è lento)
        try:
            uid_ = (st.session_state.get("sess") or {}).get("uid", "")
            r0 = r_usato
            if r0.get("mime") == "application/pdf" and _mr_ocr_disponibile():
                if vuote:
                    extra = int(ocr.get(r0.get("id"), 0))
                    blocchi = [vuote[:MR_OCR_PAGINE]] + [vuote[MR_OCR_PAGINE + k * MR_OCR_PASSO:MR_OCR_PAGINE + (k + 1) * MR_OCR_PASSO] for k in range(extra // MR_OCR_PASSO)]
                    lette = 0
                    for bl in blocchi:                                           # a blocchi fissi: ogni blocco letto una volta resta in memoria e non si rilegge
                        if bl:
                            pagine = sorted(list(pagine) + _mr_ocr_blocco(uid_, r0.get("id"), r0.get("nome", ""), r0.get("mime", ""), int(r0.get("dimensione") or 0), tuple(bl)))
                            lette += len(bl)
                    scansioni.append({"titolo": doc["titolo"], "fid": r0.get("id"), "lette": lette, "vuote": len(vuote), "totale": totale})
        except Exception:
            pass
        letti.append(doc["titolo"])
        testi_pagina = {n_: t_ for n_, t_ in pagine}
        for n, testo in _mr_passaggi(pagine):
            parole = set(_mr_ridotte(testo))
            n_tot += 1
            for t in tok:
                if t in parole:
                    df[t] = df.get(t, 0) + 1
            cand.append((doc, n, testo, parole, hit_doc, testi_pagina.get(n, testo)))
    ris = []
    for doc, n, testo, parole, hit_doc, pag_intera in cand:
        trovate = [t for t in tok if t in parole]
        if not trovate:
            continue
        # con due o più parole nella domanda, nel passaggio ne servono almeno due, meno quelle che già dicono di che documento si parla (nome o bene):
        # «pressione caldaia» in un documento della caldaia basta «pressione»; in un manuale di altro (un giradischi) servono tutte e due
        servono = max(1, min(2, len(tok)) - hit_doc)
        if len(trovate) < servono:
            continue
        punteggio = sum(math.log(1 + n_tot / (1 + df.get(t, 0))) for t in trovate) * (1.0 + 0.5 * (len(trovate) - 1)) + 2.0 * hit_doc
        ris.append({"titolo": doc["titolo"], "pagina": n, "testo": testo, "dove": doc["dove"], "punteggio": round(punteggio, 2), "parole": trovate, "pagina_testo": pag_intera})
    ris.sort(key=lambda r: -r["punteggio"])
    visti, out = set(), []
    for r in ris:
        k = (r["titolo"], r["pagina"])
        if k in visti:
            continue
        visti.add(k)
        out.append(r)
        if len(out) >= massimo:
            break
    return {"passaggi": out, "letti": letti, "non_letti": non_letti, "nessun_documento": False, "scansioni": scansioni}


# ---------------------------------------------------------------------------------------------------------------------
# ✨ «Spiegami in parole semplici»: facoltativo. Usa lo STESSO collegamento gratuito delle spie (stessa chiave dell'amministratore o chiave propria
# gratuita di chi usa l'app). Manda al servizio SOLO il testo del passaggio che si tocca (niente titolo, nomi, indirizzi o altri documenti).
# Spegnibile con MANUALI_IA = "no" nei Secrets. Limite per persona: MANUALI_IA_MAX_UTENTE_GIORNO (predefinito 10) con la chiave dell'app; la chiave propria non ha limite.
# ---------------------------------------------------------------------------------------------------------------------
MR_IA_MAX_UTENTE = 10
_MR_IA_SISTEMA = """Sei un assistente che spiega, in italiano molto semplice, un passaggio di un manuale d'uso a una persona poco esperta di tecnologia.
FORMATO OBBLIGATORIO: rispondi SOLO con la spiegazione, scritta in ITALIANO, dentro i tag <spiegazione> e </spiegazione>. Fuori dai tag non scrivere niente. Non scrivere analisi, ragionamenti, passaggi di lavoro, traduzioni o parole in inglese, e non ricopiare il testo del manuale.
REGOLE: (1) usa SOLO quello che c'è scritto nel passaggio: non aggiungere numeri, valori, passaggi o avvertenze che non ci sono; (2) se il passaggio è incompleto, tagliato o confuso, dillo («Il testo è incompleto: apri la pagina intera») e spiega solo la parte chiara; (3) frasi brevi e parole comuni, al massimo 120 parole; (4) se ci sono dei passi, scrivili in un elenco numerato; (5) se si parla di gas, corrente elettrica, pressione, acqua calda o altri rischi, aggiungi una frase: «Segui le avvertenze del manuale e, se non sei sicuro, chiama un tecnico»; (6) non fare diagnosi, non dare consigli tuoi, non parlare di te."""
_MR_IA_PROMEMORIA = "\n\nScrivi ora SOLO la spiegazione in italiano tra <spiegazione> e </spiegazione>: niente ragionamenti, niente inglese, niente copia del testo."

# parole per riconoscere le righe in inglese (il ragionamento che alcuni modelli gratuiti scrivono per errore) e le tracce di lavoro
_MR_EN = set("the and is are was were to of for with this that it be must will should not from you your user passage text explain simple italian wait let but output draft refine check constraint constraints role source translate translation sentence step response answer which have has been into than then also only".split())
_MR_IT = set("il lo la gli le un una uno di del dello della dei degli delle che per con non è e sono si se da nel nella nei sul sulla alla al ai alle ma come quando puoi può devi deve fai fare prima dopo poi anche ha hanno più dove cui quindi perché ti tuo tua suo sua questo questa quello".split())
_MR_TRACCIA = re.compile(r"(analy[sz]e|source text|role:|constraints?\b|draft(ing)?\b|self[- ]?correct|wait,|let'?s\b|step \d|final (polish|check)|refin(e|ing)|output generation|thinking|reasoning|translation artifact|re-?read|check against|\bplan:|\bgoal:|request:)", re.I)


def mr_pulisci_risposta(t, sorgente=""):
    """Toglie da una risposta dell'IA tutto ciò che non è la spiegazione: ragionamenti, righe in inglese, copie del testo originale. Ritorna il testo pulito oppure None se non resta una spiegazione utilizzabile."""
    t = str(t or "").replace("\r", "")
    t = re.sub(r"<(think|thinking|reasoning)>.*?</\1>", "", t, flags=re.S | re.I)
    m = re.findall(r"<spiegazione>(.*?)(?:</spiegazione>|$)", t, flags=re.S | re.I)
    if m and m[-1].strip():
        t = m[-1]
    else:
        fin = list(re.finditer(r"(?i)(final (answer|output|response|version|text)|risposta finale|spiegazione finale|versione finale)\W{0,3}[:：]\s*", t))
        if fin and len(t[fin[-1].end():].strip()) >= 40:
            t = t[fin[-1].end():]
    src = set(re.findall(r"[a-zàèéìòù']+", str(sorgente or "").lower()))
    righe = []
    for r in t.split("\n"):
        r0 = r.strip().lstrip("*-•○■#>0123456789.) (").strip().strip("*_ ")
        if not r0:
            righe.append("")
            continue
        if _MR_TRACCIA.search(r0):
            continue
        w = re.findall(r"[a-zàèéìòù']+", r0.lower())
        en = sum(1 for x in w if x in _MR_EN)
        it = sum(1 for x in w if x in _MR_IT)
        if (en > it and en >= 2) or (en >= 3 and en >= 0.3 * len(w)):
            continue                                                                    # riga in inglese
        if len(w) >= 8 and src and sum(1 for x in w if x in src) / len(w) >= 0.8:
            continue                                                                    # riga che ricopia il testo del manuale
        righe.append(r.rstrip())
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(righe)).strip()
    w_tot = re.findall(r"[a-zàèéìòù']+", out.lower())
    if len(out) < 40 or len(w_tot) < 8 or sum(1 for x in w_tot if x in _MR_EN) > 0.15 * len(w_tot):
        return None
    return out[:1500]


_MR_IA_MSG = {"chiave": "La chiave dell'intelligenza artificiale non è valida o è scaduta.", "rete": "Non riesco a collegarmi al servizio adesso. Riprova fra poco.",
              "formato": "Il servizio gratuito ha risposto in modo confuso (anche dopo qualche tentativo). Riprova fra un minuto, oppure leggi il testo del manuale qui sopra.",
              "limite": "Il servizio gratuito è occupato o ha finito le richieste: aspetta un minuto e riprova.", "limite_app": "Hai raggiunto il tetto di spiegazioni dell'app per oggi. Riprova più tardi.",
              "pagamento": "Il modello scelto è a pagamento: nel servizio gratuito scegline uno con «:free» nel nome.", "modello": "Il modello gratuito scelto non c'è più o non funziona: riprova fra poco."}


def mr_ia_attiva():
    try:
        spento = str(st.secrets.get("MANUALI_IA", "")).strip().lower() in ("no", "off", "0", "false", "spento")
    except Exception:
        spento = False
    return (not spento) and "ad_provider_scelto" in globals() and "_ad_invia" in globals()


@st.cache_resource
def _mr_ia_conteggi():
    return {}


def _mr_ia_limite():
    try:
        v = str(st.secrets.get("MANUALI_IA_MAX_UTENTE_GIORNO", MR_IA_MAX_UTENTE)).strip().lower()
        return None if v in ("no", "-1", "illimitato") else int(v)
    except Exception:
        return MR_IA_MAX_UTENTE


def mr_ia_puo(cfg):
    """Con la chiave dell'app c'è un limite al giorno per persona (l'amministratore e chi usa la PROPRIA chiave non hanno limite). Conta l'uso."""
    if cfg.get("fonte") != "app":
        return True
    sess = st.session_state.get("sess") or {}
    if sess.get("admin"):
        return True
    lim = _mr_ia_limite()
    if lim is None:
        return True
    oggi_ = _ad_oggi() if "_ad_oggi" in globals() else date_oggi_iso()
    c = _mr_ia_conteggi()
    for k in [k for k in c if k[0] != oggi_]:
        c.pop(k, None)
    chiave = (oggi_, sess.get("uid", ""))
    if c.get(chiave, 0) >= lim:
        return False
    c[chiave] = c.get(chiave, 0) + 1
    return True


def date_oggi_iso():
    import datetime as _dt
    return _dt.date.today().isoformat()


def mr_spiega(testo):
    """(spiegazione, None) oppure (None, errore) con errore in: chiave, limite_utente, rete, limite, formato… (gli stessi messaggi delle spie).
    Se il servizio gratuito risponde in modo confuso (ragionamento in inglese, copia del testo), si pulisce; se non resta niente di buono si riprova con un altro modello (fino a 3 tentativi)."""
    try:
        prov = ad_provider_scelto()
        cfg = ad_cfg(prov)
        if not cfg.get("key") or (prov == "altra" and not (cfg.get("url") and cfg.get("modello"))):
            return None, "chiave"
        if not mr_ia_puo(cfg):
            return None, "limite_utente"
        modelli = [m_.strip() for m_ in str(cfg.get("modello", "")).split(",") if m_.strip()]
        tentativi = [cfg] + ([dict(cfg, modello=m_) for m_ in modelli[1:3]] if (prov == "openrouter" and len(modelli) > 1) else [cfg])
        utente = "Passaggio del manuale:\n\n" + str(testo)[:2500] + _MR_IA_PROMEMORIA
        ultimo = "formato"
        for c_ in tentativi[:3]:
            try:
                t, err = _ad_invia(prov, c_, _MR_IA_SISTEMA, [("u", utente)], None, 900, False, {"temperature": 0.2, "reasoning": {"exclude": True}})
            except TypeError:                                                           # una versione di _ad_invia senza i parametri in più
                t, err = _ad_invia(prov, c_, _MR_IA_SISTEMA, [("u", utente)], None, 900)
            if err:
                if err in ("chiave", "pagamento", "limite"):
                    return None, err
                ultimo = err
                continue
            pulito = mr_pulisci_risposta(t, testo)
            if pulito:
                return pulito, None
            ultimo = "formato"
        return None, ultimo
    except Exception:
        return None, "rete"


def _mr_js_voce(testo):
    """Legge ad alta voce un passaggio con la velocità scelta nel pannello dell'assistente."""
    pulito = re.sub(r"\s+", " ", re.sub(r"[*_`#]", "", testo)).strip()
    return ("(function(){var w=window,SS=w.speechSynthesis;if(!SS)return;SS.cancel();var r=1;try{r=parseFloat(w.localStorage.getItem('asst_rate')||'1')||1}catch(e){}if(r<0.5||r>2)r=1;"
            "var t=" + json.dumps(pulito, ensure_ascii=False) + ";var p=t.match(/[^.;:!?]+[.;:!?]?/g)||[t],i=0;"
            "function dici(){if(i>=p.length)return;var u=new w.SpeechSynthesisUtterance(p[i++].trim());u.lang='it-IT';u.rate=r;u.onend=dici;SS.speak(u);}dici();})();")


def _mr_dialogo(sezione):
    @st.dialog("📚 Cerca nei miei manuali e documenti", width="large")
    def _f():
        st.caption("Scrivi cosa cerchi (per esempio «spia rossa lavatrice» o «pulire il filtro caldaia»). Cerco **solo nei tuoi** manuali, garanzie e documenti di Casa e dei veicoli, e ti mostro **i passaggi che c'entrano**, non tutto il PDF.")
        q = st.text_input("Cosa cerchi", key="mr_q", placeholder="es. come sbloccare il cestello", label_visibility="collapsed")
        cerca = st.button("🔎 Cerca", key="mr_vai", width="stretch", type="primary")
        if cerca:
            st.session_state["mr_tutti"] = False                                                   # una nuova ricerca parte dai documenti più adatti
        tutti = st.session_state.get("mr_tutti", False)
        if q.strip() and (cerca or st.session_state.get("mr_ultima") == q.strip()):
            st.session_state["mr_ultima"] = q.strip()
            try:
                d = carica_dati(crea_archivio(), st.session_state["percorso"])
            except Exception:
                st.error("Non riesco a leggere i tuoi documenti ora. Riprova fra poco.")
                return
            with st.spinner("Leggo i documenti… (se un manuale è una scansione ci vuole un po': lo leggo pagina per pagina)"):
                r = mr_cerca(d, q, tutti=tutti, ocr=st.session_state.get("mr_ocr") or {})
            for sc in r.get("scansioni", []):
                if sc["lette"] < sc["vuote"]:
                    st.caption(f"📄 «{sc['titolo']}» è una **scansione** (solo immagini): ho letto {sc['lette']} pagine su {sc['vuote']} con il riconoscimento del testo.")
                    if st.button(f"🔎 Leggi altre {MR_OCR_PASSO} pagine di «{sc['titolo'][:30]}» (più lento)", key="mr_ocr_" + str(sc["fid"]), width="stretch"):
                        mo = dict(st.session_state.get("mr_ocr") or {})
                        mo[sc["fid"]] = int(mo.get(sc["fid"], 0)) + MR_OCR_PASSO
                        st.session_state["mr_ocr"] = mo
                        st.rerun(scope="fragment")
                else:
                    st.caption(f"📄 «{sc['titolo']}» è una scansione: il testo è letto con il riconoscimento ottico e può contenere qualche errore.")
            if r["nessun_documento"]:
                st.info("Non hai ancora manuali o documenti archiviati. Apri **Casa → 📚 Documenti** e carica un manuale (PDF o foto): poi potrò cercare dentro.")
                return
            if not r["passaggi"]:
                st.warning("Non ho trovato niente su «" + q.strip() + "» nei documenti che ho letto. **Non voglio inventare una risposta.**")
                st.caption("Ho letto: " + "; ".join(r["letti"]) + ".")
                if r["non_letti"] and not tutti:
                    if st.button(f"🔎 Cerca anche negli altri {r['non_letti']} documenti (più lento)", key="mr_tutti_b", width="stretch"):
                        st.session_state["mr_tutti"] = True
                        st.rerun(scope="fragment")
                st.caption("Prova con altre parole, oppure apri il documento e cercalo a mano.")
                return
            n_p = len(r["passaggi"])
            st.markdown(f"**{n_p} " + ("passaggio trovato" if n_p == 1 else "passaggi trovati") + "** (in: " + "; ".join(r["letti"]) + ")")
            for i, p in enumerate(r["passaggi"]):
                with st.container(border=True):
                    st.markdown(f"**📄 {p['titolo']}** · pagina {p['pagina']}")
                    st.caption(f"📍 Dove si trova: {p['dove']}")
                    st.markdown(p["testo"].replace("\n\n", "\n\n"))
                    if len(p.get("pagina_testo", "")) > len(p["testo"]) + 40:
                        with st.expander("📖 Leggi tutta la pagina " + str(p["pagina"])):
                            st.markdown(p["pagina_testo"])
                            if st.button("🔊 Leggi la pagina intera", key=f"mr_leggi_p_{i}", width="stretch"):
                                _inietta(_mr_js_voce(p["pagina_testo"]))
                    c1, c2 = st.columns(2, gap="small")
                    if c1.button("🔊 Leggi ad alta voce", key=f"mr_leggi_{i}", width="stretch"):
                        _inietta(_mr_js_voce(p["testo"]))
                    if c2.button("⏹ Ferma la voce", key=f"mr_ferma_{i}", width="stretch"):
                        _inietta("(function(){try{window.speechSynthesis.cancel()}catch(e){}})();")
                    if mr_ia_attiva():
                        kspieg = hashlib.md5((str(p["pagina"]) + p["testo"][:120]).encode("utf-8")).hexdigest()[:12]
                        if st.button("✨ Spiegami in parole semplici", key=f"mr_ia_{i}", width="stretch"):
                            if not ad_attivo():
                                st.info("Per le spiegazioni serve una **chiave gratuita** (di OpenRouter o di Google Gemini): segui la guida qui sotto, è facoltativo.")
                                try:
                                    ad_guida_propria_chiave()
                                    ad_campo_chiave_propria()
                                except Exception:
                                    pass
                            else:
                                with st.spinner("Preparo la spiegazione…"):
                                    sp_t, sp_e = mr_spiega(p["testo"])
                                if sp_e:
                                    ad_mostra_errore(sp_e, _MR_IA_MSG.get(sp_e, "Non sono riuscito a preparare la spiegazione. Riprova fra poco."))
                                else:
                                    mm = dict(st.session_state.get("mr_spiega") or {})
                                    mm[kspieg] = sp_t
                                    st.session_state["mr_spiega"] = mm
                        else:
                            st.caption("✨ Invia **solo questo passaggio** a un servizio di intelligenza artificiale gratuito (facoltativo).")
                        sp_vista = (st.session_state.get("mr_spiega") or {}).get(kspieg)
                        if sp_vista:
                            st.info("✨ **In parole semplici:**\n\n" + sp_vista)
                            st.caption("Spiegazione automatica: **può sbagliare**. Controlla sempre il manuale qui sopra.")
                            if st.button("🔊 Leggi la spiegazione", key=f"mr_ia_voce_{i}", width="stretch"):
                                _inietta(_mr_js_voce(sp_vista))
            st.caption("Sono le parole del manuale, non una mia spiegazione: se qualcosa non è chiaro, chiedi a una persona di fiducia. Per cambiare la velocità della voce usa il robottino: «🐢 Velocità della voce».")
    _f()


if "_ae_info_prima" not in globals() and "pulsante_info" in globals():
    _ae_info_prima = pulsante_info


def pulsante_info(sezione):
    r = _ae_info_prima(sezione)
    if sezione in ("dispensa", "casa", "auto", "utilita"):
        try:
            if st.button("📚 Cerca nei miei manuali e documenti", key=f"mr_btn_{sezione}", width="stretch"):
                _mr_dialogo(sezione)
        except Exception:
            pass
    return r
