# -*- coding: utf-8 -*-
"""SALUTE · 📸 VISITE DA UN DOCUMENTO (promemoria di prenotazione del CUP, impegnativa di visita o esame).

Nella scheda Visite compare «📸 Aggiungi una visita da un documento»: si carica la foto (o il PDF) del PROMEMORIA DI PRENOTAZIONE e l'app lo legge (stesso OCR e stesso caricamento di Documenti)
e apre la finestra «Visita o esame» GIÀ COMPILATA: data e ora dell'appuntamento, specialità e tipo di prestazione (dal catalogo), che visita o esame, struttura e indirizzo, e nelle note:
numero di prenotazione, impegnativa, esenzione o ticket, COSA PORTARE e il numero per disdire. La persona si sceglie da sola dal codice fiscale o dal nome (se il documento è di un altro
profilo, la visita va nel suo). Il documento originale resta allegato alla visita. Tu controlli e correggi tutto prima di salvare: l'app propone, non decide.

COME SI INTEGRA: la finestra «Visita o esame» è quella di sempre (`_fa_dialogo_visita`, con un parametro in più per i dati già compilati); il caricamento è quello di Documenti
(`_ca_pannello_caricamento`); nessun dato nuovo: la visita ha gli stessi campi di sempre."""
import hashlib
import re
from datetime import date, datetime, timedelta

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# LETTURA (senza Streamlit: si prova da sola)
# ---------------------------------------------------------------------------------------------------------------------
_VP_DATA = r"(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4})"
_VP_PICCOLE = {"di", "da", "del", "della", "dei", "delle", "degli", "dello", "e", "in", "a", "per", "con", "su", "al", "alla", "ai", "agli", "alle", "il", "la", "lo", "le", "i", "gli", "un", "una"}
_VP_SIGLE = {"ASL", "CUP", "ICS", "ECG", "RMN", "TAC", "ASST", "AO", "ASO", "CAP", "ECO"}


def _vp_data(s):
    m = re.search(_VP_DATA, str(s or ""))
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def vp_titolo(s):
    """«PRESIDIO MAJOR DI TORINO - TORINO» → «Presidio Major di Torino – Torino». Se il testo non è tutto maiuscolo resta com'è."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    lettere = [c for c in s if c.isalpha()]
    if not lettere or sum(c.isupper() for c in lettere) / len(lettere) < 0.7:
        return s
    parole = []
    for i, w in enumerate(s.split(" ")):
        core = re.sub(r"[^A-Za-zÀ-ÿ']", "", w)
        if any(c.isdigit() for c in w) or w in {"-", "–"}:
            parole.append(w.replace(" - ", " – "))
        elif core.upper() in _VP_SIGLE:
            parole.append(w)
        elif i > 0 and core.lower() in _VP_PICCOLE:
            parole.append(w.lower())
        else:
            parole.append(w[:1].upper() + w[1:].lower())
    return " ".join(parole).replace(" - ", " – ")


def vp_frase(s):
    """«ECOCOLORDOPPLER DEGLI ARTI INFERIORI. A RIPOSO» → «Ecocolordoppler degli arti inferiori. A riposo» (le sigle restano maiuscole)."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if not s:
        return s
    parole = [w if re.sub(r"[^A-Za-z]", "", w).upper() in _VP_SIGLE else w.lower() for w in s.split(" ")]
    t = " ".join(parole).replace(" - ", " – ")
    t = re.sub(r"([.!?]\s+)([a-zà-ÿ])", lambda m: m.group(1) + m.group(2).upper(), t)
    return t[:1].upper() + t[1:]


def _vp_sezione(t, inizio, fine):
    """Il testo tra due intestazioni (maiuscole o minuscole), da `inizio` escluso a `fine` escluso."""
    mi = re.search(inizio, t, re.I)
    if not mi:
        return ""
    resto = t[mi.end():]
    mf = re.search(fine, resto, re.I) if fine else None
    return resto[:mf.start()] if mf else resto


def vp_leggi_prenotazione(testo):
    """Legge un promemoria di prenotazione (CUP/ASL). → dict; `riconosciuto` è vero solo se il documento sembra davvero una prenotazione. NON decide: propone."""
    t = str(testo or "")
    r = {"riconosciuto": False, "paziente": "", "cf": "", "nascita": None, "prenotazione": None, "impegnativa": None, "convenzione": "", "importo": None, "struttura": "", "reparto": "",
         "appuntamenti": [], "prestazione": "", "portare": [], "disdetta_tel": "", "disdetta_giorni": None, "stampato": None}
    if not t.strip():
        return r
    r["riconosciuto"] = bool(re.search(r"promemoria\s+di\s+prenotazione|quando\s+presentarsi|richiesta\s+di\s+prenotazione|prenotazione\s+cup", t, re.I))
    righe = [x.strip(" |") for x in t.splitlines() if x.strip(" |")]
    # chi è: il codice fiscale, la data di nascita e il nome (le maiuscole in fondo alla riga prima di «Nata a»)
    m = re.search(r"\bC\.?F\.?\s*[:.]?\s*([A-Z0-9]{16})\b", t)
    if m:
        r["cf"] = m.group(1).upper()
    for i, riga in enumerate(righe):
        mn = re.search(r"Nat[oa]\s+a\s+(.+?),?\s+il\s+" + _VP_DATA, riga, re.I)
        if mn:
            r["nascita"] = _vp_data(riga[mn.start():])
            for prec in (righe[i - 1] if i else "", riga[:mn.start()]):
                mm = re.search(r"((?:[A-ZÀ-Ý']{2,}\s+){1,3}[A-ZÀ-Ý']{2,})\s*$", prec.strip())
                if mm and mm.group(1).split()[0] not in {"REGIONE", "SERVIZIO", "SANITARIO", "PIEMONTE"}:
                    r["paziente"] = mm.group(1).strip()
                    break
            break
    m = re.search(r"\bN\.?\s*(\d{9,})\s+del\s+" + _VP_DATA + r"(?:\s+(\d{1,2}:\d{2}))?", t)
    if m:
        r["prenotazione"] = {"numero": m.group(1), "data": _vp_data(m.group(0)), "ora": m.group(5) or ""}
    m = re.search(r"IMPEGNATIVA[:\s]*([0-9A-Z]{10,})\s+del\s+" + _VP_DATA, t)
    if m:
        r["impegnativa"] = {"numero": m.group(1), "data": _vp_data(m.group(0))}
    m = re.search(r"CONVENZIONE[:\s]*(.+?)(?=\s+NUMERO|\s*$)", t, re.M)
    if m:
        r["convenzione"] = vp_frase(m.group(1).strip(" :-"))
    m = re.search(r"Importo\s+da\s+pagare[^\d\n]{0,6}(\d+[.,]\d{2})", t, re.I)                      # il simbolo € è spesso letto male (E, ·, C): non lo si pretende
    if m:
        r["importo"] = float(m.group(1).replace(",", "."))
    m = re.search(r"stampa[:\s]*" + _VP_DATA, t, re.I)
    if m:
        r["stampato"] = _vp_data(m.group(0))
    # dove
    dove = _vp_sezione(t, r"DOVE\s+PRESENTARSI[^\n]*", r"QUANDO\s+PRESENTARSI")
    for riga in dove.splitlines():
        m = re.search(r"((?:PRESIDIO|OSPEDALE|POLIAMBULATORIO|CLINICA|AMBULATORIO|AZIENDA|ISTITUTO|CENTRO|ASL)\b.+)$", riga.strip(" |"))
        if m and not r["struttura"]:
            r["struttura"] = vp_titolo(re.sub(r"\s+", " ", m.group(1)).strip(" -"))
    m = re.search(r"#\d+\s*-\s*[A-Z]{2}\s*-\s*([^\n]+)", dove)
    if m:
        r["reparto"] = vp_titolo(m.group(1).strip(" |"))
    # quando e cosa
    quando = _vp_sezione(t, r"QUANDO\s+PRESENTARSI[^\n]*", r"COSA\s+PORTARE")
    plano = re.sub(r"\s+", " ", quando.replace("|", " "))
    app = []
    for m in re.finditer(_VP_DATA + r"\s*(\d{1,2}):(\d{2})", plano):
        d = _vp_data(m.group(0))
        if d:
            app.append((d, f"{int(m.group(4)):02d}:{m.group(5)}"))
    r["data_ricostruita"] = False
    if not app and plano:                                                                    # l'OCR spesso spezza «Giovedì 03/12/2026 15:00» in pezzi su righe diverse: si rimettono insieme
        mp = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/(?!\s*\d{3})", plano) or re.search(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{0,2})\b", plano)
        mo = re.findall(r"\b(\d{1,2}):(\d{2})\b", plano)
        if mp and mo:
            base = (r["prenotazione"] or {}).get("data") or r["stampato"] or date.today()
            my = re.search(r"\b(20\d{2})\b", plano)
            anno = int(my.group(1)) if my else base.year
            try:
                d = date(anno, int(mp.group(2)), int(mp.group(1)))
                if not my and d < base:
                    d = date(anno + 1, int(mp.group(2)), int(mp.group(1)))
                app = [(d, f"{int(mo[-1][0]):02d}:{mo[-1][1]}")]
                r["data_ricostruita"] = True
            except ValueError:
                pass
    r["appuntamenti"] = app
    if plano:
        s = re.sub(_VP_DATA + r"\s*(\d{1,2}:\d{2})?", " ", plano)
        s = re.sub(r"\b\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{0,4}\b", " ", s)
        s = re.sub(r"\b\d{1,2}:\d{2}\b", " ", s)
        s = re.sub(r"\b(lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica|lunedi|martedi|mercoledi|giovedi|venerdi)\b", " ", s, flags=re.I)
        s = re.sub(r"\bQ\.?\s*t[àa]'?\s*\d+", " ", s, flags=re.I)
        s = re.sub(r"\b\d{6,}\b", " ", s)
        s = re.sub(r"\b\d{2}\.\d{2}(?:\.\d+)?[A-Z]?\b", " ", s)
        def _buona(w):
            core = re.sub(r"[^A-Za-zÀ-ÿ]", "", w)
            if re.search(r"[0-9]", w) or w in {"-", "–"} or core.lower() in {"tà", "ta", "qtà", "qta"}:
                return False
            return len(core) >= 2
        parole = []
        for w in s.split():
            core = re.sub(r"[^A-Za-zÀ-ÿ]", "", w)
            if len(core) == 1:                                                                # una lettera sola è quasi sempre rumore dell'OCR: si tiene solo in «… venoso. A riposo»
                if core in {"A", "a"} and parole and parole[-1].endswith("."):
                    parole.append(w)
            elif _buona(w):
                parole.append(w)
        r["prestazione"] = vp_frase(" ".join(parole).strip(" .,-")) if parole else ""
    portare = _vp_sezione(t, r"COSA\s+PORTARE[^\n]*", r"\bNOTE\b|INFORMAZIONI\s+PER")
    portare = re.sub(r"\s+", " ", portare.replace("|", " ")).strip()
    if portare:
        pezzi = [p.strip(" ,;") for p in re.split(r"(?=TESSERA\s+SANITARIA|REFERTI|IMPEGNATIVA|DOCUMENTO\s+D|CARTA\s+D|RICETTA|CODICE\s+FISCALE|ESENZIONE)", portare) if p.strip(" ,;")]
        r["portare"] = [vp_frase(p) for p in pezzi]
    m = re.search(r"contattare[^.\n]*?\bn\.?\s*(\d[\d ]{6,14}\d)", t, re.I)
    if m:
        r["disdetta_tel"] = re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"entro\s+(\d+)\s+giorni\s+lavorativi", t, re.I)
    if m:
        r["disdetta_giorni"] = int(m.group(1))
    if not r["riconosciuto"] and r["appuntamenti"] and r["struttura"]:
        r["riconosciuto"] = True
    return r


def vp_ocr_raddrizzata(dati):
    """Rilegge la foto dopo averla RADDRIZZATA: le foto dei fogli sono quasi sempre un po' inclinate e l'OCR sbaglia i numeri e spezza le righe. → testo ('' se non serve o non si può)."""
    try:
        import io
        import cv2
        import numpy as np
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("L")
        a = np.array(im)
        h, w = a.shape
        b = cv2.adaptiveThreshold(cv2.GaussianBlur(a, (3, 3), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)
        piccola = cv2.resize(b, None, fx=0.35, fy=0.35, interpolation=cv2.INTER_AREA)

        def punteggio(ang):
            M = cv2.getRotationMatrix2D((piccola.shape[1] / 2, piccola.shape[0] / 2), ang, 1.0)
            rr = cv2.warpAffine(piccola, M, (piccola.shape[1], piccola.shape[0]), flags=cv2.INTER_NEAREST)
            return float(np.var(np.diff(rr.sum(axis=1).astype(float))))
        miglior = max((x / 4 for x in range(-24, 25)), key=punteggio)                       # da -6° a +6°: l'inclinazione con le righe più nette
        if abs(miglior) < 0.2:
            return ""                                                                      # già dritta
        M = cv2.getRotationMatrix2D((w / 2, h / 2), miglior, 1.0)
        dritta = Image.fromarray(cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=255))
        dritta.thumbnail((2400, 2400))
        return _doc_tesseract(dritta, "6") if "_doc_tesseract" in globals() else __import__("pytesseract").image_to_string(dritta, lang="ita", config="--psm 6")
    except Exception:
        return ""


_VP_VOCABOLARIO = {"degli", "delle", "dei", "del", "della", "dello", "arti", "inferiori", "superiori", "inferiore", "superiore", "venoso", "arterioso", "venosa", "arteriosa", "riposo", "digiuno", "sforzo",
                   "visita", "controllo", "esame", "ecografia", "ecocolordoppler", "doppler", "ecodoppler", "ecg", "elettrocardiogramma", "addome", "completo", "tiroide", "mammella", "mammografia", "radiografia",
                   "torace", "cuore", "cardiologica", "specialistica", "prima", "ginecologica", "oculistica", "ortopedica", "dermatologica", "neurologica", "analisi", "sangue", "urine", "tac", "risonanza",
                   "magnetica", "con", "senza", "mezzo", "contrasto", "bilaterale", "destra", "sinistra", "ginocchio", "spalla", "anca", "colonna", "lombare", "cervicale", "polmonare", "spirometria"}


def _vp_punteggio_frase(f):
    """Quante parole «vere» (note) ci sono in una frase letta: serve a scegliere fra due letture dell'OCR."""
    return sum(1 for w in re.findall(r"[A-Za-zÀ-ÿ]+", str(f or "").lower()) if w in _VP_VOCABOLARIO)


def vp_unisci(principale, altra):
    """Due letture dello stesso documento: si tiene la prima e si completa con la seconda quello che manca. La prestazione si sceglie fra le due con più parole."""
    r = dict(principale)
    for k, v in altra.items():
        if k in ("riconosciuto",):
            r[k] = principale[k] or v
        elif k == "prestazione":
            sp_, sa_ = _vp_punteggio_frase(principale[k]), _vp_punteggio_frase(v)
            r[k] = v if (sa_, -len(v.split())) > (sp_, -len(principale[k].split())) else principale[k]
        elif k == "data_ricostruita":
            continue
        elif not r.get(k):
            r[k] = v
    r["data_ricostruita"] = principale.get("data_ricostruita", False) if principale.get("appuntamenti") else altra.get("data_ricostruita", False)
    return r


def vp_leggi_documento(testo, dati=None, mime=""):
    """La lettura completa: il testo già estratto dall'app e, per le foto, anche la foto raddrizzata. → dict come vp_leggi_prenotazione."""
    r1 = vp_leggi_prenotazione(testo)
    if dati and str(mime).startswith("image/"):
        t2 = vp_ocr_raddrizzata(dati)
        if t2:
            r2 = vp_leggi_prenotazione(t2)
            if r2["riconosciuto"] or r1["riconosciuto"]:
                return vp_unisci(r2, r1)
    return r1


def vp_prefill(r, f=None, pid="p0"):
    """I dati già compilati per la finestra «Visita o esame». → (id del profilo, prefill, avvisi). La specialità e il tipo vengono dal catalogo (`cat_classifica`)."""
    area, tipo = "", ""
    try:
        c = cat_classifica(r.get("prestazione") or "")
        area, tipo = c.get("area") or "", c.get("tipo") or ""
    except Exception:
        pass
    avvisi = []
    scelto = pid
    if f is not None and "sp_proponi_profilo" in globals():
        try:
            pp, motivo = sp_proponi_profilo(f, r.get("paziente", ""), r.get("cf", ""))
        except Exception:
            pp, motivo = None, ""
        nomi = {x.get("id"): x.get("nome", "") for x in (f.get("profili") or [])}
        if pp and pp != pid:
            scelto = pp
            avvisi.append(f"Il documento è intestato a **{r.get('paziente') or 'un altro profilo'}** ({motivo}): la visita viene salvata nel profilo di **{nomi.get(pp, '')}**.")
        elif not pp and (r.get("paziente") or r.get("cf")):
            avvisi.append(f"Il documento è intestato a **{r.get('paziente') or r.get('cf')}**: non lo riconosco tra i profili, controlla che sia la persona giusta (la visita va nel profilo di **{nomi.get(pid, '')}**).")
    app = r.get("appuntamenti") or []
    d0, ora = (app[0] if app else (None, ""))
    note = []
    if r.get("prenotazione"):
        p_ = r["prenotazione"]
        note.append(f"Prenotazione CUP n. {p_['numero']}" + (f" del {p_['data'].strftime('%d/%m/%Y')}" if p_.get("data") else ""))
    if r.get("impegnativa"):
        i_ = r["impegnativa"]
        note.append(f"Impegnativa n. {i_['numero']}" + (f" del {i_['data'].strftime('%d/%m/%Y')}" if i_.get("data") else ""))
    if r.get("convenzione"):
        note.append(r["convenzione"] + (f", importo da pagare € {r['importo']:.2f}".replace(".", ",") if r.get("importo") is not None else ""))
    if r.get("reparto"):
        note.append("Reparto: " + r["reparto"])
    if r.get("portare"):
        note.append("Da portare: " + "; ".join(x[:1].lower() + x[1:] if i else x for i, x in enumerate(r["portare"])))
    if r.get("disdetta_tel"):
        note.append(f"Per disdire: {r['disdetta_tel']}" + (f", almeno {r['disdetta_giorni']} giorni lavorativi prima" if r.get("disdetta_giorni") else ""))
    if len(app) > 1:
        note.append("Altri appuntamenti nel documento: " + "; ".join(f"{d.strftime('%d/%m/%Y')} {o}" for d, o in app[1:]))
        avvisi.append(f"Nel documento ci sono **{len(app)} appuntamenti**: qui salvo il primo, gli altri sono scritti nelle note.")
    if not app:
        avvisi.append("Non sono riuscito a leggere la data e l'ora dell'appuntamento: scrivile tu.")
    elif r.get("data_ricostruita"):
        avvisi.append("Ho **ricostruito la data dell'appuntamento** da una lettura incerta: **controllala** con il documento.")
    pre = {"data": d0.isoformat() if d0 else None, "ora": ora, "categoria": area or "Altro", "tipo_prestazione": tipo, "prestazione": r.get("prestazione", ""),
           "medico": " · ".join(x for x in (r.get("struttura"),) if x), "motivo": "", "controlli": "", "prossimo": None, "note": " · ".join(note), "_avvisi": avvisi}
    return scelto, pre, avvisi


# ---------------------------------------------------------------------------------------------------------------------
# INTERFACCIA
# ---------------------------------------------------------------------------------------------------------------------
class _VpFile:
    """Il file già letto, fatto passare per «caricato» (serve a _fa_salva_files)."""
    def __init__(self, nome, dati):
        self.name, self._d = nome, dati

    def getvalue(self):
        return self._d


def _vp_chiudi(n=None):
    for k in ("vp_on", "vp_chiave", "vp_lettura", "ca_bozza_in"):
        st.session_state.pop(k, None)
    if n is not None:
        st.session_state["ca_giro"] = n + 1


def vp_pannello(f, pid):
    """Il pulsante «📸 Aggiungi una visita da un documento» in cima alla scheda Visite e, aperto, il caricamento di Documenti; letto il file si apre la finestra già compilata."""
    if not st.session_state.get("vp_on"):
        if st.button("📸 Aggiungi una visita da un documento (promemoria di prenotazione, impegnativa)", key="vp_apri", width="stretch", type="primary"):
            st.session_state["vp_on"] = True
            st.rerun()
        return
    st.markdown("##### 📸 Visita da un documento")
    st.caption("Carica la **foto o il PDF del promemoria di prenotazione** (CUP, ASL, ospedale). Lo leggo e apro la finestra **già compilata**: data e ora, specialità, struttura, cosa portare. "
               "**Controlli e correggi tu** prima di salvare. Il documento resta allegato alla visita.")
    if st.button("✖ Chiudi", key="vp_chiudi", width="stretch"):
        _vp_chiudi()
        st.rerun()
    if "_ca_pannello_caricamento" not in globals() or "ca_estrai_testo" not in globals():
        st.error("Il caricamento dei documenti non è disponibile adesso.")
        return
    n = st.session_state.get("ca_giro", 0)
    up = _ca_pannello_caricamento(n, multi=False)
    sorgente = None
    if up is not None:
        dati = up.getvalue()
        sorgente = {"nome": up.name, "mime": _ca_mime(up.name, up.type, dati), "dati": dati}
    elif st.session_state.get("ca_bozza_in"):
        sorgente = dict(st.session_state["ca_bozza_in"])
        sorgente.setdefault("mime", _ca_mime(sorgente.get("nome"), "", sorgente.get("dati")))
    if not sorgente:
        st.session_state.pop("vp_chiave", None)
        return
    if sorgente["mime"] not in _CA_MIME or len(sorgente["dati"]) > _CA_MAX_BYTE:
        st.error("Carica un PDF o una foto (JPG, PNG, WebP) di al massimo 8 MB.")
        return
    if sorgente["mime"].startswith("image/") and len(sorgente["dati"]) > 4_000_000 and "_ca_riduci_foto" in globals():
        rid = _ca_riduci_foto(sorgente["nome"], sorgente["dati"])
        if rid:
            sorgente = dict(sorgente, nome=rid[0], mime="image/jpeg", dati=rid[1])
    sha = hashlib.sha256(sorgente["dati"]).hexdigest()
    lett = st.session_state.get("vp_lettura")
    if not lett or lett.get("sha") != sha:
        with st.spinner("Leggo il documento…"):
            testo, _info = ca_estrai_testo(sorgente["nome"], sorgente["mime"], sorgente["dati"])
            lettura = vp_leggi_documento(testo or "", sorgente["dati"], sorgente["mime"])
        lett = {"sha": sha, "r": lettura, "testo_ok": bool(testo)}
        st.session_state["vp_lettura"] = lett
    r = lett["r"]
    if not r["riconosciuto"]:
        st.warning("Questo non sembra un **promemoria di prenotazione**. " + ("Non sono riuscito a leggere il testo (la foto è poco leggibile?). " if not lett["testo_ok"] else "")
                   + "Se è un referto o un esame già fatto, usa **«📎 Carica un referto…»** qui sotto; altrimenti riprova con una foto più dritta e ben illuminata, oppure compila la visita a mano.")
        if st.button("✖ Scarta il documento", key="vp_scarta", width="stretch"):
            _vp_chiudi(n)
            st.rerun()
        return
    scelto, pre, avvisi = vp_prefill(r, f, pid)
    pre["_avvisi"] = ["📖 **Ho letto il documento**: controlla i dati e correggi quello che non torna prima di salvare."] + avvisi
    pre["_allegato"] = _VpFile(sorgente["nome"], sorgente["dati"])
    pre["_dopo"] = lambda: _vp_chiudi(n)
    chiave = f"{n}:{sha}"
    if st.session_state.get("vp_chiave") != chiave:
        st.session_state["vp_chiave"] = chiave                                              # la finestra si apre da sola una volta per ogni file
        _fa_dialogo_visita(scelto, None, pre)
    else:
        st.info("📖 Documento letto. Se hai chiuso la finestra, riaprila.")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("📖 Riapri la visita", key=f"vp_riapri_{n}", type="primary", width="stretch"):
            _fa_dialogo_visita(scelto, None, pre)
        if c2.button("✖ Scarta il documento", key=f"vp_scarta2_{n}", width="stretch"):
            _vp_chiudi(n)
            st.rerun()


# la scheda Visite mostra il pulsante in cima (la scheda originale non si tocca: si «avvolge»)
if "_vp_tab_visite_prima" not in globals() and "_fa_tab_visite" in globals():
    _vp_tab_visite_prima = _fa_tab_visite


def _fa_tab_visite(f, pid, nomi, oggi_):                                                    # noqa: F811
    try:
        vp_pannello(f, pid)
    except Exception as e:                                                                  # un problema qui non deve rompere la scheda Visite
        st.warning(f"La lettura da un documento non è disponibile adesso ({type(e).__name__}).")
    return _vp_tab_visite_prima(f, pid, nomi, oggi_)
