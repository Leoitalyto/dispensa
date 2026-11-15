# -*- coding: utf-8 -*-
"""LETTORE DELLO SCRITTO (anche a mano) — vale per TUTTA l'app, anche per le sezioni future.
Sotto ogni foto o pagina di documento che l'app mostra compare da solo il pulsante «🔍 Leggi lo scritto»: nessun modulo deve ricordarsi di aggiungerlo.
Cosa fa: manda QUELLA pagina all'intelligenza artificiale attiva nell'app (la stessa della diagnosi delle spie: Claude, Gemini, OpenAI oppure OpenRouter anche gratuito)
e restituisce la trascrizione fedele, riga per riga:
 · testo normale  = letto con sicurezza;
 · ARANCIONE      = lettura non del tutto sicura (la più probabile);
 · ROSSO          = impossibile da riconoscere;
 · in fondo: nota rossa (cosa non si è potuto leggere), nota arancione (i punti incerti) e «Lettura per logica» (ipotesi ragionate dal contesto, in seconda battuta).
Il testo letto si può scaricare o copiare. La lettura resta salvata (nei dati privati della persona): la volta dopo si riapre subito, senza rileggere.
Il programma OCR dell'app (Tesseract) NON sa leggere la calligrafia: per questo serve l'IA. Senza una chiave il pulsante spiega come attivarla (c'è anche la strada gratuita).
Per NON mostrare il pulsante sotto una certa immagine: st.image(..., _lettore=False).
Caricato da app_dispensa.py dopo immagini_sicure.py e auto_diagnosi.py. Nomi con prefisso «le_»."""
import io
import re
import html as _le_html
import hashlib
import threading
from datetime import datetime

import streamlit as st

_LE_LOC = threading.local()
LE_MIN_BYTE = 15000                      # sotto questa misura è un'icona o una miniatura: niente pulsante
LE_MAX_PAGINE_PDF = 12

_LE_SISTEMA = """Sei un trascrittore professionista di documenti, esperto di calligrafia difficile (referti e ricette mediche, moduli compilati a mano, appunti, lettere, ricevute, timbri, anche in corsivo o in stampatello frettoloso).
Ti viene data l'IMMAGINE di una pagina. Devi leggerla con la massima attenzione e restituire una trascrizione FEDELE.

REGOLE DI TRASCRIZIONE
- Trascrivi TUTTO quello che c'è scritto, stampato e a mano, nell'ordine di lettura, andando a capo come nel documento. Per le tabelle: una riga per ogni riga, con « | » tra le colonne.
- NON riassumere, NON correggere, NON completare, NON inventare. Scrivi quello che c'è, non quello che ti aspetti.
- Ingrandisci mentalmente ogni parola scritta a mano: confronta le lettere con altre uguali nella stessa pagina (stessa mano) prima di decidere.
- Parola o tratto letto ma NON del tutto sicuro: scrivilo tra doppie quadre con il punto di domanda, così: [[?parola più probabile]].
- Parola o tratto IMPOSSIBILE da riconoscere: scrivi [[X]] (uno per ogni parola o tratto illeggibile). Mai tirare a indovinare qui.
- Nomi di medicinali, dosi, numeri, date, codici e cognomi: se anche una sola lettera o cifra è dubbia, vanno marcati come incerti [[?...]]. Non «aggiustare» mai una dose.
- Le abbreviazioni restano come sono scritte nel TESTO (le spieghi dopo, nella lettura per logica).
- Timbri, firme e sigle: indicali tra parentesi tonde, per esempio (timbro: ...), (firma illeggibile).

FORMATO DELLA RISPOSTA — esattamente queste sezioni, con queste intestazioni, in italiano:
### TIPO
Una riga: che documento sembra (per esempio: referto di visita ginecologica, ricetta, bolletta, lettera…).
### TESTO
La trascrizione fedele, con i segni [[?...]] e [[X]].
### NON RICONOSCIUTO
Elenco puntato («- ») dei punti impossibili da leggere: dove sono (riga o zona) e perché (grafia, macchia, taglio, timbro sopra…). Se non ce ne sono scrivi: Nessuno.
### INCERTO
Elenco puntato («- ») dei punti non del tutto sicuri: «come l'ho letto» → eventuale altra lettura possibile. Se non ce ne sono scrivi: Nessuno.
### LETTURA PER LOGICA
Solo in seconda battuta e dichiarandolo come IPOTESI: per i punti incerti o illeggibili proponi la lettura più sensata ragionando sul contesto (tipo di documento, frasi vicine, abbreviazioni d'uso: per esempio «EO» = esame obiettivo, «PA» = pressione arteriosa, «tp» = terapia). Per ogni ipotesi di' in due parole su cosa si basa. Sciogli qui anche le abbreviazioni. Se non c'è niente da aggiungere scrivi: Nessuna.

Non aggiungere altro: niente premesse, niente consigli medici, niente conclusioni tue."""
_LE_RICHIESTA = "Leggi questa pagina e trascrivila seguendo le regole e il formato indicati."

_LE_CSS = """<style>
div[class*="st-key-le_b_"]{margin:-4px 0 4px !important}
div[class*="st-key-le_b_"] button{min-height:0 !important;padding:.3rem .9rem !important;border-radius:999px !important;border:1px solid rgba(120,170,255,.55) !important;background:rgba(40,80,160,.18) !important}
div[class*="st-key-le_b_"] button p{font-size:.86rem !important;font-weight:700 !important}
.le-box{border-radius:14px;padding:12px 14px;margin:6px 0;line-height:1.55;font-size:.98rem;word-break:break-word}
.le-testo{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18)}
.le-inc{color:#ffb020;font-weight:700;border-bottom:2px dotted #ffb020}
.le-no{color:#ff5a5a;font-weight:800;background:rgba(255,60,60,.14);border-radius:5px;padding:0 4px}
.le-rosso{background:rgba(255,60,60,.12);border:1px solid rgba(255,90,90,.75);color:#ff8f8f}
.le-arancio{background:rgba(255,170,30,.12);border:1px solid rgba(255,176,32,.75);color:#ffc45e}
.le-logica{background:rgba(70,150,255,.12);border:1px solid rgba(110,170,255,.75);color:#a9cbff}
.le-box b.le-t{display:block;margin-bottom:4px}
.le-leg{font-size:.84rem;opacity:.92;margin:2px 0 6px}
</style>"""

_LE_ERRORI = {
    "chiave": "La chiave dell'intelligenza artificiale non è valida o è scaduta: va controllata in Auto → Diagnosi spie → «Scegli l'intelligenza artificiale».",
    "limite": "Il servizio di intelligenza artificiale in questo momento è occupato (troppe richieste). Riprova tra un minuto.",
    "rete": "Non sono riuscito a raggiungere il servizio di intelligenza artificiale. Controlla la connessione e riprova.",
    "rifiuto": "Il servizio non ha voluto leggere questa immagine. Prova con una foto più nitida o con un altro servizio.",
    "modello": "Il modello scelto non legge le immagini (o non esiste più): scegline un altro in Auto → Diagnosi spie → «Scegli l'intelligenza artificiale».",
    "pagamento": "Il modello scelto è a pagamento e non c'è credito: scegli un modello gratuito oppure ricarica.",
    "formato": "La risposta è arrivata in una forma che non capisco. Tocca «🔄 Rileggi».",
    "limite_app": "Per oggi le letture offerte dall'app sono finite: riprova domani, oppure usa una tua chiave (anche gratuita).",
    "vuoto": "La lettura è tornata vuota: forse la foto è troppo scura o mossa. Riprova con una foto più nitida.",
    "immagine": "Non riesco ad aprire questa immagine per leggerla.",
}


# ---------------------------------------------------------------------------------------------------------------------
# immagine → JPEG nitido per la lettura
# ---------------------------------------------------------------------------------------------------------------------
def le_jpeg(dati, lato=2000):
    """La pagina in JPEG, al massimo «lato» pixel sul lato lungo (abbastanza per la calligrafia, leggera da inviare). None se non è un'immagine."""
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(dati))
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            sfondo = Image.new("RGB", im.size, (255, 255, 255))
            sfondo.paste(im, mask=im.split()[-1])
            im = sfondo
        else:
            im = im.convert("RGB")
        im.thumbnail((lato, lato))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88, optimize=True)
        return buf.getvalue()
    except Exception:
        return None


def le_pagina_pdf(dati, indice, dpi=170):
    """Una pagina di un PDF come immagine nitida (PNG). None se non si riesce."""
    try:
        try:
            import pymupdf as _mu
        except Exception:
            import fitz as _mu
        doc = _mu.open(stream=dati, filetype="pdf")
        try:
            return doc[indice].get_pixmap(dpi=dpi, alpha=False).tobytes("png")
        finally:
            doc.close()
    except Exception:
        return None


# ---------------------------------------------------------------------------------------------------------------------
# la lettura
# ---------------------------------------------------------------------------------------------------------------------
def le_attivo():
    return "ad_attivo" in globals() and ad_attivo()


def le_servizio():
    try:
        return (AD_PROVIDER.get(ad_provider_scelto()) or {}).get("nome", "il servizio di intelligenza artificiale")
    except Exception:
        return "il servizio di intelligenza artificiale"


def le_leggi(jpeg):
    """Chiede la trascrizione. Ritorna (testo grezzo, None) oppure (None, errore)."""
    if not le_attivo():
        return None, "assente"
    prov = ad_provider_scelto()
    cfg = ad_cfg(prov)
    if cfg["fonte"] == "app" and not ad_puo():
        return None, (ad_errore_stop() if "ad_errore_stop" in globals() else "limite_app")
    st.session_state.pop("_ad_dettaglio", None)
    testo, err = _ad_invia(prov, cfg, _LE_SISTEMA, [("u", _LE_RICHIESTA)], [jpeg], 4000, False, {"temperature": 0.1})
    if err:
        return None, err
    if not (testo or "").strip():
        return None, "vuoto"
    return testo, None


def le_sezioni(grezzo):
    """Divide la risposta nelle sue parti. Se le intestazioni mancano, tutto finisce nel testo (non si perde niente)."""
    out = {"tipo": "", "testo": "", "no": "", "incerto": "", "logica": ""}
    pezzi = re.split(r"(?m)^\s*#{2,4}\s*(.+?)\s*$", grezzo or "")
    if len(pezzi) < 3:
        out["testo"] = (grezzo or "").strip()
        return out
    if pezzi[0].strip():
        out["testo"] = pezzi[0].strip()
    for i in range(1, len(pezzi) - 1, 2):
        nome, corpo = pezzi[i].upper(), pezzi[i + 1].strip()
        if "LOGICA" in nome:
            out["logica"] = corpo
        elif "NON RICONOSC" in nome or "ILLEGGIB" in nome:
            out["no"] = corpo
        elif "INCERT" in nome:
            out["incerto"] = corpo
        elif "TIPO" in nome:
            out["tipo"] = corpo.split("\n")[0].strip()
        elif "TESTO" in nome or "TRASCRIZ" in nome:
            out["testo"] = (out["testo"] + "\n" + corpo).strip()
        else:
            out["testo"] = (out["testo"] + "\n" + corpo).strip()
    return out


def _le_vuota(t):
    return not (t or "").strip() or re.fullmatch(r"[-•*\s]*(nessun[oa]?|niente|n/?a)\.?", (t or "").strip(), re.I) is not None


def le_conta(testo):
    return len(re.findall(r"\[\[\?", testo or "")), len(re.findall(r"\[\[\s*[Xx✗]\s*\]\]", testo or ""))


def le_html(testo):
    """Il testo con i colori: arancione = incerto, rosso = illeggibile."""
    t = _le_html.escape(testo or "")
    t = re.sub(r"\[\[\s*[Xx✗]\s*\]\]", "<span class='le-no'>▮ illeggibile</span>", t)
    t = re.sub(r"\[\[\?\s*(.*?)\]\]", lambda m: f"<span class='le-inc'>{m.group(1).strip() or '?'}</span>", t, flags=re.S)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def le_testo_semplice(sez):
    """Il testo da scaricare o copiare (senza colori: «(?)» = incerto, «[illeggibile]» = non riconosciuto)."""
    def pulisci(t):
        t = re.sub(r"\[\[\s*[Xx✗]\s*\]\]", "[illeggibile]", t or "")
        return re.sub(r"\[\[\?\s*(.*?)\]\]", lambda m: f"{m.group(1).strip()}(?)", t, flags=re.S)
    parti = []
    if sez.get("tipo"):
        parti.append("TIPO DI DOCUMENTO: " + sez["tipo"])
    parti.append("TESTO LETTO\n" + pulisci(sez.get("testo")))
    if not _le_vuota(sez.get("no")):
        parti.append("NON RICONOSCIUTO\n" + pulisci(sez["no"]))
    if not _le_vuota(sez.get("incerto")):
        parti.append("NON DEL TUTTO SICURO\n" + pulisci(sez["incerto"]))
    if not _le_vuota(sez.get("logica")):
        parti.append("LETTURA PER LOGICA (ipotesi, da verificare)\n" + pulisci(sez["logica"]))
    parti.append("Legenda: (?) = lettura non sicura · [illeggibile] = non riconosciuto.\nLettura automatica: può contenere errori. Per dosi, medicinali e diagnosi vale solo il documento originale e la parola del medico.")
    return "\n\n".join(parti)


# ---------------------------------------------------------------------------------------------------------------------
# la lettura salvata (nei dati privati della persona)
# ---------------------------------------------------------------------------------------------------------------------
def _le_percorso(ident):
    uid = (st.session_state.get("sess") or {}).get("uid", "prova")
    return f"documenti/{uid}/lettura_{ident}.json"


def le_salvata(ident):
    k = "le_ris_" + ident
    if k in st.session_state:
        return st.session_state[k]
    ris = None
    try:
        d = carica_dati(crea_archivio(), _le_percorso(ident))
        if isinstance(d, dict) and d.get("grezzo"):
            ris = {"grezzo": d["grezzo"], "il": d.get("il", ""), "servizio": d.get("servizio", "")}
    except Exception:
        ris = None
    st.session_state[k] = ris
    return ris


def le_salva(ident, ris):
    st.session_state["le_ris_" + ident] = ris
    try:
        salva_file(_le_percorso(ident), lambda d, r=ris: d.update(r), "Lettura dello scritto salvata")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------------------------------------------------
# il pulsante e il pannello
# ---------------------------------------------------------------------------------------------------------------------
def _le_alterna(chiave):
    st.session_state[chiave] = not st.session_state.get(chiave, False)


def _le_in_finestra():
    try:
        return bool(co_contesto()["finestra"]) if "co_contesto" in globals() else False
    except Exception:
        return False


def _le_in_modulo():
    try:
        from streamlit.elements.lib.form_utils import current_form_id
        return bool(current_form_id(st._main._active_dg))
    except Exception:
        return False


def _le_gia_visto(chiave):
    """Lo stesso pulsante non va disegnato due volte nella stessa ridisegnata (stessa foto mostrata due volte)."""
    ss = st.session_state
    run = (ss.get("_vm_run", 0), ss.get("_co_dlg") if chiave.startswith("le_b_d") else None)
    if ss.get("_le_run") != run:
        ss["_le_run"] = run
        ss["_le_visti"] = []
    if chiave in ss["_le_visti"]:
        if chiave.startswith("le_b_d"):                 # dentro una finestra la pagina si ridisegna da sola: si riparte
            ss["_le_visti"] = [chiave]
            return False
        return True
    ss["_le_visti"] = ss["_le_visti"] + [chiave]
    return False


def le_pulsante(ident, sorgente, etichetta="🔍 Leggi lo scritto"):
    """Il pulsante sotto un'immagine. ident = impronta della pagina; sorgente = i byte dell'immagine oppure una funzione che li restituisce."""
    if _le_in_modulo():
        return                                             # dentro un modulo di Streamlit i pulsanti normali non sono permessi
    ident = re.sub(r"[^A-Za-z0-9_]", "", str(ident))[:40]
    chiave = f"le_b_{'d' if _le_in_finestra() else 'm'}{ident}"
    if _le_gia_visto(chiave):
        return
    k_ap = "le_ap_" + ident
    aperto = bool(st.session_state.get(k_ap))
    _LE_LOC.dentro = True
    try:
        st.markdown(_LE_CSS, unsafe_allow_html=True)
        st.button(("🙈 Chiudi la lettura" if aperto else etichetta), key=chiave, on_click=_le_alterna, args=(k_ap,),
                  help="Legge lo scritto di questa pagina, anche a mano, e ti restituisce il testo: in arancione ciò che non è sicuro, in rosso ciò che non si riconosce.")
        if aperto:
            le_pannello(ident, sorgente)
    finally:
        _LE_LOC.dentro = False


def _le_mostra_errore(err):
    if err in ("limite_utente",) and "ad_mostra_errore" in globals():
        ad_mostra_errore(err)
        return
    st.warning("⚠️ " + _LE_ERRORI.get(err, "Non sono riuscito a leggere. Riprova tra poco."))
    dett = st.session_state.get("_ad_dettaglio")
    if dett and (st.session_state.get("sess") or {}).get("admin"):
        st.caption("Dettaglio tecnico (lo vedi solo tu): " + str(dett)[:400])
    if err in ("chiave", "modello", "pagamento", "limite_app") and "ad_guida_propria_chiave" in globals():
        with st.expander("🔑 Usa una tua chiave (c'è anche la strada gratuita)"):
            ad_guida_propria_chiave()
            if "ad_campo_chiave_propria" in globals():
                ad_campo_chiave_propria()


def le_mostra_risultato(ident, ris):
    sez = le_sezioni(ris.get("grezzo", ""))
    n_inc, n_no = le_conta(sez["testo"])
    quando = ""
    try:
        quando = datetime.fromisoformat(ris.get("il", "")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    st.markdown(f"**📖 Testo letto**" + (f" · {_le_html.escape(sez['tipo'])}" if sez["tipo"] else ""))
    st.markdown("<div class='le-leg'>Testo normale = letto con sicurezza · <span class='le-inc'>arancione</span> = non del tutto sicuro"
                + (f" ({n_inc})" if n_inc else "") + " · <span class='le-no'>▮ illeggibile</span> = non riconosciuto" + (f" ({n_no})" if n_no else "") + "</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='le-box le-testo'>{le_html(sez['testo']) or '—'}</div>", unsafe_allow_html=True)
    if not _le_vuota(sez["no"]):
        st.markdown(f"<div class='le-box le-rosso'><b class='le-t'>🔴 Impossibile da riconoscere</b>{le_html(sez['no'])}</div>", unsafe_allow_html=True)
    if not _le_vuota(sez["incerto"]):
        st.markdown(f"<div class='le-box le-arancio'><b class='le-t'>🟠 Non del tutto sicuro</b>{le_html(sez['incerto'])}</div>", unsafe_allow_html=True)
    if not _le_vuota(sez["logica"]):
        st.markdown(f"<div class='le-box le-logica'><b class='le-t'>💡 Lettura per logica (ipotesi, in seconda battuta)</b>{le_html(sez['logica'])}</div>", unsafe_allow_html=True)
    semplice = le_testo_semplice(sez)
    st.download_button("⬇ Scarica il testo letto", semplice.encode("utf-8"), file_name=f"testo_letto_{ident[:8]}.txt", mime="text/plain", key=f"le_dl_{ident}", width="stretch")
    with st.expander("📋 Copia il testo (tocca l'icona in alto a destra del riquadro)"):
        st.code(semplice, language=None, wrap_lines=True)
    st.caption("Lettura automatica" + (f" del {quando}" if quando else "") + (f" · {ris.get('servizio')}" if ris.get("servizio") else "")
               + ": può contenere errori. Per dosi, medicinali e diagnosi vale solo il documento originale e la parola del medico.")


def le_pannello(ident, sorgente):
    ris = le_salvata(ident)
    rileggi = False
    if ris:
        le_mostra_risultato(ident, ris)
        rileggi = st.button("🔄 Rileggi da capo", key=f"le_ri_{ident}", help="Fa una nuova lettura di questa pagina (per esempio dopo aver scelto un altro servizio di intelligenza artificiale).")
        if not rileggi:
            return
    if not le_attivo():
        st.info("Per leggere la calligrafia serve l'**intelligenza artificiale**, che ora non è attiva. Il lettore di testo dell'app (gratuito, sempre acceso) riconosce solo lo stampato, non lo scritto a mano.")
        if "ad_guida_propria_chiave" in globals():
            with st.expander("🔑 Come attivarla (c'è anche la strada gratuita)", **({"_aperta": True} if getattr(st.expander, "_sempre_chiusa", False) else {"expanded": True})):
                ad_guida_propria_chiave()
                if "ad_campo_chiave_propria" in globals():
                    ad_campo_chiave_propria()
        return
    k_err = "le_err_" + ident
    if st.session_state.get(k_err) and not rileggi:                      # l'ultima lettura non è riuscita: NON riparte da sola a ogni tocco (consumerebbe le letture)
        _le_mostra_errore(st.session_state[k_err])
        st.button("🔄 Riprova", key=f"le_rp_{ident}", on_click=lambda: st.session_state.pop(k_err, None))
        return
    parti = bool(rileggi or st.session_state.get("le_consenso"))
    if not parti:
        st.info(f"Per leggerla, **questa pagina viene inviata a {le_servizio()}** (un servizio esterno di intelligenza artificiale). Il file nell'app resta com'è. "
                "Te lo chiedo solo la prima volta.")
        if st.button("✅ Va bene, leggi", key=f"le_ok_{ident}", type="primary"):
            st.session_state["le_consenso"] = True
            parti = True
    if not parti:
        return
    with st.spinner("Sto leggendo con attenzione, parola per parola… (può volerci fino a un minuto)"):
        try:
            dati = sorgente() if callable(sorgente) else sorgente
        except Exception:
            dati = None
        jpeg = le_jpeg(dati) if dati else None
        if not jpeg:
            grezzo, err = None, "immagine"
        else:
            grezzo, err = le_leggi(jpeg)
    if err:
        st.session_state[k_err] = err
        _le_mostra_errore(err)
        st.button("🔄 Riprova", key=f"le_rp_{ident}", on_click=lambda: st.session_state.pop(k_err, None))
        return
    st.session_state.pop(k_err, None)
    ris = {"grezzo": grezzo, "il": datetime.now().isoformat(timespec="seconds"), "servizio": le_servizio()}
    salvata = le_salva(ident, ris)
    le_mostra_risultato(ident, ris)
    if not salvata:
        st.caption("Non sono riuscito a salvare la lettura: la vedi adesso, ma la prossima volta andrà rifatta.")


def le_pulsanti_pdf(dati, mostrate=3):
    """Per un PDF: il pulsante per le pagine che l'anteprima NON mostra (dalla quarta in poi)."""
    try:
        try:
            import pymupdf as _mu
        except Exception:
            import fitz as _mu
        doc = _mu.open(stream=dati, filetype="pdf")
        n = doc.page_count
        doc.close()
    except Exception:
        return
    base = hashlib.md5(dati).hexdigest()[:16]
    for i in range(mostrate, min(n, LE_MAX_PAGINE_PDF)):
        le_pulsante(f"{base}p{i + 1}", (lambda i=i: le_pagina_pdf(dati, i)), etichetta=f"🔍 Leggi lo scritto di pagina {i + 1}")


# ---------------------------------------------------------------------------------------------------------------------
# aggancio automatico: sotto ogni immagine grande mostrata con st.image(...)
# ---------------------------------------------------------------------------------------------------------------------
def _le_byte(x):
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    if isinstance(x, io.BytesIO):
        return x.getvalue()
    return None


if not getattr(st.image, "_lettore", False):
    _le_image_originale = st.image

    def _le_image(*a, **kw):
        voglio = kw.pop("_lettore", True)
        esito = _le_image_originale(*a, **kw)
        if not voglio or getattr(_LE_LOC, "dentro", False):
            return esito
        try:
            dati = _le_byte(a[0] if a else kw.get("image"))
            larg = kw.get("width")
            piccola = isinstance(larg, int) and not isinstance(larg, bool) and larg < 200
            if dati and len(dati) >= LE_MIN_BYTE and not piccola:
                getattr(st, "_le_pulsante", le_pulsante)(hashlib.md5(dati).hexdigest()[:20], dati)
        except Exception:
            pass
        return esito
    _le_image._lettore = True
    _le_image._sicura = True
    st.image = _le_image

st._le_pulsante = le_pulsante                      # sempre la versione più recente (il codice dell'app si ricarica a ogni ridisegnata)
