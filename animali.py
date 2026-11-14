# -*- coding: utf-8 -*-
"""ANIMALI — una sezione nuova, tra Auto e Chat: la cartella di ogni animale di casa.

Per ogni animale: scheda (foto, galleria, microchip, proprietario), salute (vaccinazioni e antiparassitari, visite, terapie, esami, interventi e ricoveri,
patologie, allergie), documenti (letti e classificati da soli: vedi animali_doc.py), peso e alimentazione, habitat, diario, spese, contatti dei veterinari, agenda.
Ogni diagnosi, terapia o visita porta con sé CHI l'ha scritta: «Veterinario» (registrata da lui o presa da un suo documento) oppure «Proprietario» (annotazione mia).
Tre moduli collegati: animali_doc.py (documenti), animali_report.py (report PDF), animali_scambio.py (esporta tutto / importa).
Dati: nel file personale, sotto d["animali"] = {"lista": [...], "vaccini": [...], "visite": [...], "terapie": [...], "esami": [...], "interventi": [...], "patologie": [...],
"allergie": [...], "peso": [...], "diario": [...], "spese": [...], "contatti": [...], "agenda": [...], "documenti": [...], "import": [...]}; ogni voce ha "id" e "animale".
I file (foto, PDF) stanno dove stanno tutti gli altri: documenti/<utente>/<id>.json (lo stesso archivio di Salute e Auto), mai modificati.
Caricato da app_dispensa.py dopo auto_archivio.py e PRIMA di chat_famiglia.py (così il bottone sta tra Auto e Chat)."""
import base64
import hashlib
import html as _h_an
import io
import re
import uuid
from datetime import date, datetime

import streamlit as st

AN_VERSIONE_DATI = 1
AN_MAX_FILE = 8 * 1024 * 1024
AN_SPECIE = ["Cane", "Gatto", "Coniglio", "Uccello / Pappagallo", "Pesce", "Camaleonte / Rettile", "Criceto / Roditore", "Furetto", "Cavallo", "Tartaruga", "Altro"]
AN_EMOJI = {"Cane": "🐶", "Gatto": "🐱", "Coniglio": "🐰", "Uccello / Pappagallo": "🦜", "Pesce": "🐟", "Camaleonte / Rettile": "🦎", "Criceto / Roditore": "🐹",
            "Furetto": "🦦", "Cavallo": "🐴", "Tartaruga": "🐢", "Altro": "🐾"}
AN_FONTI = {"veterinario": "👨‍⚕️ Veterinario", "proprietario": "✍️ Proprietario"}
AN_FONTI_LUNGHE = {"veterinario": "👨‍⚕️ Registrata dal veterinario (o presa da un suo documento)", "proprietario": "✍️ Annotazione mia (non del veterinario)"}
AN_TIPI_PREVENZIONE = ["Vaccino", "Antiparassitario", "Vermifugo", "Altra prevenzione"]
AN_TIPI_INTERVENTO = ["Intervento chirurgico", "Ricovero", "Sterilizzazione / castrazione", "Pronto soccorso", "Altro"]
AN_RUOLI_CONTATTO = ["Veterinario", "Clinica / ambulatorio", "Pronto soccorso veterinario", "Specialista", "Toelettatore", "Pensione / pet sitter", "Allevatore", "Assicurazione", "Altro"]
AN_TIPI_AGENDA = ["Visita", "Vaccino / richiamo", "Antiparassitario", "Terapia", "Controllo", "Altro"]
AN_ORDINE_CATEGORIE = ["lista", "vaccini", "visite", "terapie", "esami", "interventi", "patologie", "allergie", "peso", "diario", "spese", "contatti", "agenda", "documenti"]

# ---------------------------------------------------------------------------------------------------------------------
# registrazione della sezione: DOPO Auto, PRIMA di Chat e Utilità
# ---------------------------------------------------------------------------------------------------------------------
try:
    if "SEZIONI_NAV" in globals() and "animali" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(SEZIONI_NAV.index("auto") + 1 if "auto" in SEZIONI_NAV else (SEZIONI_NAV.index("utilita") if "utilita" in SEZIONI_NAV else len(SEZIONI_NAV)), "animali")
    if "NOMI_NAV" in globals():
        NOMI_NAV["animali"] = "Animali"
    if "SV_SEZIONI" in globals() and "animali" not in SV_SEZIONI:
        _vecchie_an = list(SV_SEZIONI.items())
        SV_SEZIONI.clear()
        _messa_an = False
        for k_, v_ in _vecchie_an:
            if k_ in ("chat", "utilita") and not _messa_an:
                SV_SEZIONI["animali"] = "🐾 Animali"
                _messa_an = True
            SV_SEZIONI[k_] = v_
        SV_SEZIONI.setdefault("animali", "🐾 Animali")
    if "_SV_DA_SEZIONE_HOME" in globals():
        _SV_DA_SEZIONE_HOME["animali"] = "animali"
    if "_PN_VOCI" in globals() and not any(v_[0] == "animali" for v_ in _PN_VOCI):
        _i_an = next((i_ for i_, v_ in enumerate(_PN_VOCI) if v_[0] == "auto"), len(_PN_VOCI) - 1) + 1
        _PN_VOCI.insert(_i_an, ("animali", "🐾 Animali", "#e8b43c", "#8a5a00"))
except Exception:
    pass

_AN_CSS = """<style>
.an-hero{display:flex;align-items:center;gap:16px;background:linear-gradient(135deg,#3a2a08 0%,#8a5a00 52%,#d9a62e 100%);color:#fff;padding:16px 20px;border-radius:24px;margin:6px 0 12px;box-shadow:0 6px 18px rgba(80,50,0,.4)}
.an-hero .ico-img{width:132px;max-width:40%;height:auto;flex:0 0 auto;filter:drop-shadow(0 0 7px rgba(255,255,255,.5)) drop-shadow(0 4px 6px rgba(0,0,0,.4))}
.an-hero .ico{font-size:3rem;line-height:1}.an-hero h1{margin:0;font-size:1.6rem;color:#fff}.an-hero p{margin:2px 0 0;font-size:.95rem;opacity:.95}
.an-card{background:rgba(255,255,255,.9);border-radius:16px;padding:10px 14px;margin:8px 0;color:#2b2111;border-left:6px solid #c58b1a;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.an-card .t{font-weight:800;font-size:1.02rem}.an-card .s{font-size:.9rem;opacity:.85}
.an-card.vet{border-left-color:#2e7d32}.an-card.prop{border-left-color:#78909c}.an-card.scad{border-left-color:#d84315}
.an-badge{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.78rem;font-weight:800;margin-right:4px;color:#fff}
.an-badge.vet{background:#2e7d32}.an-badge.prop{background:#607d8b}.an-badge.ok{background:#2e7d32}.an-badge.att{background:#ef6c00}.an-badge.no{background:#c62828}
.an-badge.tipo{background:#6d4c41}
.an-foto{width:100%;max-height:300px;object-fit:cover;border-radius:18px;margin:4px 0 8px;box-shadow:0 3px 10px rgba(0,0,0,.25)}
.an-mini{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:12px}
.an-riga{display:flex;gap:8px;font-size:.93rem;padding:3px 0;border-bottom:1px dashed rgba(0,0,0,.12)}.an-riga b{min-width:42%;flex:0 0 42%}
.st-key-an_top[data-testid='stVerticalBlock'],.st-key-an_top [data-testid='stVerticalBlock'],[class*='st-key-an_tools_'][data-testid='stVerticalBlock'],[class*='st-key-an_tools_'] [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:8px !important;margin:4px 0 10px}
.st-key-an_top button,[class*='st-key-an_tools_'] button{width:100% !important;min-height:56px !important;border-radius:16px !important;font-weight:900 !important;color:#fff !important;border:2px solid rgba(255,255,255,.5) !important;
 background:linear-gradient(135deg,#e8b43c 0%,#8a5a00 100%) !important;box-shadow:0 4px 0 rgba(0,0,0,.25) !important}
.st-key-an_top button p,[class*='st-key-an_tools_'] button p{color:#fff !important;font-weight:900 !important;text-shadow:0 1px 3px rgba(0,0,0,.5);margin:0;line-height:1.15}
.st-key-an_top button[kind='primary'],[class*='st-key-an_tools_'] button[kind='primary']{background:linear-gradient(135deg,#43a047 0%,#1b5e20 100%) !important}
@media (prefers-reduced-motion:no-preference){.an-pulsa{animation:anpulsa 1.6s ease-in-out infinite}}@keyframes anpulsa{50%{opacity:.55}}
</style>"""

AN_CATEGORIE = {
    "vaccini": {"titolo": "💉 Vaccinazioni e prevenzione", "singolare": "vaccinazione o trattamento", "fonte": True, "data": "data", "scad": "richiamo",
                "campi": [("tipo", "Tipo", ("s", AN_TIPI_PREVENZIONE)), ("nome", "Nome (vaccino o prodotto)", "t"), ("data", "Data", "d"), ("richiamo", "Prossimo richiamo", "d"),
                          ("lotto", "Lotto", "t"), ("vet", "Veterinario o clinica", "t"), ("note", "Note", "a")], "titolo_campo": "nome", "obbl": ("nome",)},
    "visite": {"titolo": "🩺 Visite veterinarie", "singolare": "visita", "fonte": True, "data": "data", "scad": "prossimo",
               "campi": [("data", "Data", "d"), ("motivo", "Motivo della visita", "t"), ("vet", "Veterinario", "t"), ("clinica", "Clinica o ambulatorio", "t"),
                         ("diagnosi", "Diagnosi", "a"), ("indicazioni", "Cure e indicazioni date", "a"), ("costo", "Costo (€)", "n"), ("prossimo", "Prossimo controllo", "d"), ("note", "Note", "a")],
               "titolo_campo": "motivo", "obbl": ("data",)},
    "terapie": {"titolo": "💊 Farmaci e terapie", "singolare": "terapia", "fonte": True, "data": "dal", "scad": "al",
                "campi": [("farmaco", "Farmaco o trattamento", "t"), ("dose", "Dose", "t"), ("frequenza", "Quante volte", "t"), ("dal", "Dal", "d"), ("al", "Fino al (vuoto = in corso)", "d"),
                          ("motivo", "Per quale problema", "t"), ("note", "Note", "a")], "titolo_campo": "farmaco", "obbl": ("farmaco",)},
    "esami": {"titolo": "🔬 Esami e referti", "singolare": "esame", "fonte": True, "data": "data", "scad": None,
              "campi": [("data", "Data", "d"), ("tipo", "Tipo di esame", "t"), ("esito", "Risultato / esito", "a"), ("vet", "Veterinario o laboratorio", "t"), ("note", "Note", "a")],
              "titolo_campo": "tipo", "obbl": ("tipo",)},
    "interventi": {"titolo": "🏥 Interventi e ricoveri", "singolare": "intervento o ricovero", "fonte": True, "data": "data", "scad": None,
                   "campi": [("tipo", "Che cosa", ("s", AN_TIPI_INTERVENTO)), ("data", "Data", "d"), ("fine", "Fine ricovero / dimissione", "d"), ("descrizione", "Descrizione", "a"),
                             ("clinica", "Clinica", "t"), ("note", "Note", "a")], "titolo_campo": "descrizione", "obbl": ("data",)},
    "patologie": {"titolo": "🩻 Patologie conosciute", "singolare": "patologia", "fonte": True, "data": "dal", "scad": None,
                  "campi": [("nome", "Patologia", "t"), ("dal", "Dal", "d"), ("stato", "Stato", ("s", ["In corso", "Sotto controllo", "Risolta"])), ("note", "Note", "a")],
                  "titolo_campo": "nome", "obbl": ("nome",)},
    "allergie": {"titolo": "⚠️ Allergie e intolleranze", "singolare": "allergia o intolleranza", "fonte": True, "data": None, "scad": None,
                 "campi": [("sostanza", "A che cosa (cibo, farmaco, pulci…)", "t"), ("reazione", "Che reazione ha", "t"), ("note", "Note", "a")], "titolo_campo": "sostanza", "obbl": ("sostanza",)},
    "peso": {"titolo": "⚖️ Peso", "singolare": "peso", "fonte": False, "data": "data", "scad": None,
             "campi": [("data", "Data", "d"), ("kg", "Peso (kg)", "n"), ("note", "Note", "t")], "titolo_campo": "kg", "obbl": ("kg",)},
    "diario": {"titolo": "📔 Diario", "singolare": "nota del diario", "fonte": False, "data": "data", "scad": None,
               "campi": [("data", "Data", "d"), ("testo", "Che cosa è successo", "a")], "titolo_campo": "testo", "obbl": ("testo",)},
    "spese": {"titolo": "💶 Spese", "singolare": "spesa", "fonte": False, "data": "data", "scad": None,
              "campi": [("data", "Data", "d"), ("voce", "Per che cosa", "t"), ("importo", "Importo (€)", "n"), ("note", "Note", "t")], "titolo_campo": "voce", "obbl": ("voce",)},
    "contatti": {"titolo": "📇 Veterinari e contatti", "singolare": "contatto", "fonte": False, "data": None, "scad": None,
                 "campi": [("nome", "Nome", "t"), ("ruolo", "Chi è", ("s", AN_RUOLI_CONTATTO)), ("tel", "Telefono", "t"), ("email", "Email", "t"), ("indirizzo", "Indirizzo", "t"), ("note", "Note", "a")],
                 "titolo_campo": "nome", "obbl": ("nome",)},
    "agenda": {"titolo": "📅 Agenda e promemoria", "singolare": "appuntamento", "fonte": False, "data": "data", "scad": "data",
               "campi": [("data", "Data", "d"), ("ora", "Ora (facoltativa)", "t"), ("titolo", "Che cosa", "t"), ("tipo", "Tipo", ("s", AN_TIPI_AGENDA)), ("note", "Note", "a")],
               "titolo_campo": "titolo", "obbl": ("titolo", "data")},
}


# ---------------------------------------------------------------------------------------------------------------------
# piccoli aiuti
# ---------------------------------------------------------------------------------------------------------------------
def _an_oggi():
    try:
        return oggi()
    except Exception:
        return date.today()


def _an_adesso():
    try:
        return adesso().isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")


def an_nuovo_id():
    return uuid.uuid4().hex[:12]


def _an_e(x):
    return _h_an.escape(str(x if x is not None else ""))


def an_data_it(iso):
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return ""


def an_data(iso):
    try:
        return date.fromisoformat(str(iso)[:10]) if iso else None
    except (ValueError, TypeError):
        return None


def an_norm(t):
    import unicodedata
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if not unicodedata.category(c).startswith("M"))


def an_solo_cifre(s):
    return re.sub(r"\D", "", str(s or ""))


def an_sha(b):
    return hashlib.sha256(b).hexdigest()


def an_mime_da_nome(nome, dati=b""):
    n = str(nome or "").lower()
    if dati[:4] == b"%PDF" or n.endswith(".pdf"):
        return "application/pdf"
    if dati[:3] == b"\xff\xd8\xff" or n.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if dati[:8] == b"\x89PNG\r\n\x1a\n" or n.endswith(".png"):
        return "image/png"
    if dati[:4] == b"RIFF" and dati[8:12] == b"WEBP" or n.endswith(".webp"):
        return "image/webp"
    if n.endswith((".heic", ".heif")):
        return "image/heic"
    return "application/octet-stream"


# ---------------------------------------------------------------------------------------------------------------------
# i dati
# ---------------------------------------------------------------------------------------------------------------------
def an_dati():
    """Tutti i dati Animali dell'utente (copia da leggere, non da modificare)."""
    try:
        return carica_dati(crea_archivio(), st.session_state["percorso"]).get("animali") or {}
    except Exception:
        return {}


def an_salva(fn, messaggio="Animali"):
    """Salva con una modifica: fn(a) riceve il dizionario d['animali'] (già completo di tutte le liste)."""
    def _m(d):
        a = d.setdefault("animali", {})
        for k in AN_ORDINE_CATEGORIE:
            if not isinstance(a.get(k), list):
                a[k] = []
        if not isinstance(a.get("import"), list):
            a["import"] = []
        a.setdefault("versione", AN_VERSIONE_DATI)
        fn(a)
    salva(_m, messaggio)


def an_animali(a=None):
    a = a if a is not None else an_dati()
    return [x for x in (a.get("lista") or []) if isinstance(x, dict) and x.get("id")]


def an_trova(a, aid):
    return next((x for x in an_animali(a) if x["id"] == aid), None)


def an_nome(a, aid):
    x = an_trova(a, aid)
    return (x or {}).get("nome") or "—"


def an_voci(a, cat, aid=None):
    """Le voci di una categoria (di un animale, o tutte)."""
    v = [x for x in (a.get(cat) or []) if isinstance(x, dict)]
    if aid:
        v = [x for x in v if x.get("animale") == aid]
    return v


def an_ordina(voci, chiave="data", recenti_prima=True):
    return sorted(voci, key=lambda x: (str(x.get(chiave) or ""), str(x.get("agg") or x.get("creato") or "")), reverse=recenti_prima)


def an_etichetta_animale(x):
    return f"{AN_EMOJI.get(x.get('specie'), '🐾')} {x.get('nome') or 'Senza nome'}"


def an_ultimo_aggiornamento(a, aid):
    """La data (ISO) dell'ultima modifica ai dati dell'animale (schede, voci e documenti)."""
    best = ""
    x = an_trova(a, aid) or {}
    best = max(best, str(x.get("agg") or x.get("creato") or ""))
    for cat in AN_ORDINE_CATEGORIE[1:]:
        for r in an_voci(a, cat, aid):
            best = max(best, str(r.get("agg") or r.get("creato") or ""))
    return best[:10]


def an_terapia_attiva(t, oggi_=None):
    oggi_ = oggi_ or _an_oggi()
    al, dal = an_data(t.get("al")), an_data(t.get("dal"))
    if dal and dal > oggi_:
        return False
    return al is None or al >= oggi_


# ---------------------------------------------------------------------------------------------------------------------
# i file (foto e documenti): lo stesso archivio di Salute, SENZA modificare l'originale
# ---------------------------------------------------------------------------------------------------------------------
def an_percorso_file(fid):
    return _fa_percorso_doc(fid)


def an_salva_originale(nome, dati, esistenti=None, mime=None):
    """Salva il file così com'è (nessuna riduzione, nessuna conversione) e ritorna il riferimento {id, nome, mime, sha, originale}.
    Se un file identico è già fra gli «esistenti», ritorna quello (con 'doppione': True) senza salvare di nuovo."""
    if not dati:
        raise ValueError("Il file è vuoto.")
    if len(dati) > AN_MAX_FILE:
        raise ValueError(f"«{nome}» è troppo grande ({len(dati) // 1024 // 1024} MB): il massimo è 8 MB. Riducilo o dividilo in due.")
    mime = mime or an_mime_da_nome(nome, dati)
    sha = an_sha(dati)
    for e in (esistenti or []):
        if e.get("sha") == sha and e.get("id"):
            return dict(e, doppione=True)
    fid = an_nuovo_id()
    corpo = {"nome": str(nome)[:160] or "file", "mime": mime, "b64": base64.b64encode(dati).decode()}
    salva_file(an_percorso_file(fid), lambda d, c=corpo: d.update(c), "Animali: file")
    return {"id": fid, "nome": corpo["nome"], "mime": mime, "sha": sha, "originale": True}


def an_leggi_file(rif):
    """I byte di un file (o None se non si trova)."""
    try:
        d = carica_dati(crea_archivio(), an_percorso_file(rif["id"]))
        return base64.b64decode(d["b64"]) if d and d.get("b64") else None
    except Exception:
        return None


def an_cancella_file(ids):
    for fid in ids:
        try:
            crea_archivio().elimina(an_percorso_file(fid), "Animali: file eliminato")
        except Exception:
            pass
    try:
        carica_dati.clear()
    except Exception:
        pass


def an_uri_foto(rif, lato=520):
    """La foto come indirizzo «data:» ridotto (solo per mostrarla), oppure ''."""
    if not rif or not rif.get("id"):
        return ""
    cache = st.session_state.setdefault("an_cache_foto", {})
    k = (rif["id"], lato)
    if k in cache:
        return cache[k]
    dati = an_leggi_file(rif)
    uri = ""
    if dati and str(rif.get("mime") or "").startswith("image/"):
        try:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
            im.thumbnail((lato, lato))
            b = io.BytesIO()
            im.save(b, "JPEG", quality=80)
            uri = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
        except Exception:
            uri = ""
    if len(cache) > 60:
        cache.clear()
    cache[k] = uri
    return uri


# ---------------------------------------------------------------------------------------------------------------------
# finestre: scheda animale, voce generica, eliminazione
# ---------------------------------------------------------------------------------------------------------------------
def _an_campo(k, etichetta, tipo, valore, chiave):
    if tipo == "t":
        return st.text_input(etichetta, value=str(valore or ""), key=chiave).strip()
    if tipo == "a":
        return st.text_area(etichetta, value=str(valore or ""), key=chiave, height=90).strip()
    if tipo == "n":
        try:
            v0 = float(str(valore).replace(",", ".")) if valore not in (None, "") else None
        except (ValueError, TypeError):
            v0 = None
        r = st.number_input(etichetta, min_value=0.0, max_value=100000.0, value=v0, step=0.1, format="%.2f", key=chiave)
        return r if r is not None else ""
    if tipo == "d":
        r = st.date_input(etichetta, value=an_data(valore), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=chiave)
        return r.isoformat() if r else ""
    if isinstance(tipo, tuple) and tipo[0] == "s":
        opz = list(tipo[1])
        if valore and valore not in opz:
            opz.append(valore)
        return st.selectbox(etichetta, opz, index=opz.index(valore) if valore in opz else 0, key=chiave)
    return valore


@st.dialog("🐾 Scheda dell'animale")
def _an_dialogo_animale(aid):
    a = an_dati()
    x = an_trova(a, aid) or {}
    k = f"an_da_{aid or 'nuovo'}_"
    nome = st.text_input("Nome *", value=x.get("nome", ""), key=k + "nome").strip()
    specie = st.selectbox("Specie", AN_SPECIE, index=AN_SPECIE.index(x["specie"]) if x.get("specie") in AN_SPECIE else 0, key=k + "specie")
    razza = st.text_input("Razza", value=x.get("razza", ""), key=k + "razza").strip()
    c1, c2 = st.columns(2)
    sesso = c1.selectbox("Sesso", ["", "Maschio", "Femmina"], index=["", "Maschio", "Femmina"].index(x.get("sesso", "")) if x.get("sesso", "") in ("", "Maschio", "Femmina") else 0, key=k + "sesso")
    sterilizzato = c2.checkbox("Sterilizzato / castrato", value=bool(x.get("sterilizzato")), key=k + "ster")
    nascita = st.date_input("Data di nascita (anche approssimata)", value=an_data(x.get("nascita")), min_value=date(1990, 1, 1), max_value=_an_oggi(), format="DD/MM/YYYY", key=k + "nascita")
    colore = st.text_input("Colore / segni particolari", value=x.get("colore", ""), key=k + "colore").strip()
    microchip = st.text_input("Microchip (15 cifre)", value=x.get("microchip", ""), key=k + "chip").strip()
    tatuaggio = st.text_input("Altri identificativi (tatuaggio, anello, anagrafe…)", value=x.get("tatuaggio", ""), key=k + "tat").strip()
    passaporto = st.text_input("Numero del passaporto o libretto", value=x.get("passaporto", ""), key=k + "pass").strip()
    pedigree = st.text_input("Pedigree / iscrizione (facoltativo)", value=x.get("pedigree", ""), key=k + "ped").strip()
    st.markdown("**Proprietario**")
    p = x.get("proprietario") or {}
    pn = st.text_input("Nome e cognome", value=p.get("nome", ""), key=k + "pn").strip()
    pt = st.text_input("Telefono", value=p.get("tel", ""), key=k + "pt").strip()
    pe = st.text_input("Email", value=p.get("email", ""), key=k + "pe").strip()
    pa = st.text_input("Indirizzo", value=p.get("indirizzo", ""), key=k + "pa").strip()
    note = st.text_area("Annotazioni importanti", value=x.get("note", ""), key=k + "note", height=90).strip()
    errore = ""
    if microchip and len(an_solo_cifre(microchip)) not in (0, 15):
        errore = "Il microchip ha di solito 15 cifre: controlla (puoi salvare lo stesso)."
    if errore:
        st.caption("⚠️ " + errore)
    if st.button("✅ Salva", type="primary", key=k + "ok", width="stretch"):
        if not nome:
            st.error("Scrivi il nome dell'animale.")
            return
        nuovo_id = aid or an_nuovo_id()

        def _m(a):
            rec = an_trova(a, nuovo_id)
            if rec is None:
                rec = {"id": nuovo_id, "creato": _an_adesso(), "origine": {"tipo": "creato qui"}}
                a["lista"].append(rec)
            rec.update({"nome": nome, "specie": specie, "razza": razza, "sesso": sesso, "sterilizzato": sterilizzato, "nascita": nascita.isoformat() if nascita else "",
                        "colore": colore, "microchip": microchip, "tatuaggio": tatuaggio, "passaporto": passaporto, "pedigree": pedigree,
                        "proprietario": {"nome": pn, "tel": pt, "email": pe, "indirizzo": pa}, "note": note, "agg": _an_adesso()})
        an_salva(_m, "Animali: scheda")
        st.session_state["an_sel"] = nuovo_id
        st.session_state["messaggio"] = f"✅ Scheda di {nome} salvata."
        st.rerun()


@st.dialog("🐾 Voce")
def _an_dialogo_voce(cat, rid, aid):
    sp = AN_CATEGORIE[cat]
    a = an_dati()
    r = next((x for x in an_voci(a, cat) if x.get("id") == rid), {}) if rid else {}
    k = f"an_v_{cat}_{rid or 'nuova'}_"
    st.markdown(f"**{sp['titolo']}** · {_an_e(an_nome(a, aid)) if aid else 'per tutti'}")
    valori = {}
    for campo, etichetta, tipo in sp["campi"]:
        v0 = r.get(campo)
        if v0 in (None, "") and tipo == "d" and campo == sp.get("data") and not rid:
            v0 = _an_oggi().isoformat()
        valori[campo] = _an_campo(campo, etichetta, tipo, v0, k + campo)
    fonte = "proprietario"
    if sp["fonte"]:
        scelte = list(AN_FONTI_LUNGHE)
        fonte = st.radio("Chi l'ha scritto?", scelte, index=scelte.index(r.get("fonte", "proprietario")) if r.get("fonte") in scelte else 1,
                         format_func=lambda z: AN_FONTI_LUNGHE[z], key=k + "fonte")
        st.caption("Nel report PDF le diagnosi e le prescrizioni del veterinario sono tenute separate dalle mie annotazioni.")
    if cat == "contatti":
        st.caption("Il contatto vale per tutti gli animali.")
    if st.button("✅ Salva", type="primary", key=k + "ok", width="stretch"):
        mancanti = [e for c_, e, _t in sp["campi"] if c_ in sp["obbl"] and (valori.get(c_) in (None, ""))]
        if mancanti:
            st.error("Manca: " + ", ".join(mancanti))
            return
        nid = rid or an_nuovo_id()

        def _m(a):
            lista = a[cat]
            rec = next((x for x in lista if x.get("id") == nid), None)
            if rec is None:
                rec = {"id": nid, "animale": aid if cat != "contatti" else "", "creato": _an_adesso(), "origine": {"tipo": "creata qui"}}
                lista.append(rec)
            for c_, v_ in valori.items():
                rec[c_] = v_
            if sp["fonte"]:
                rec["fonte"] = fonte
            rec["agg"] = _an_adesso()
        an_salva(_m, f"Animali: {cat}")
        st.session_state["messaggio"] = "✅ Salvato."
        st.rerun()


@st.dialog("🗑️ Eliminare?")
def _an_dialogo_elimina(cat, rid, descrizione):
    st.warning(f"Stai per eliminare: **{_an_e(descrizione)}**. Non si può annullare.")
    n_doc = 0
    if cat == "documenti":
        st.caption("Viene tolto anche il file originale da questa scheda.")
    c1, c2 = st.columns(2)
    if c1.button("🗑️ Sì, elimina", type="primary", key=f"an_el_si_{cat}_{rid}", width="stretch"):
        ids_file = []

        def _m(a):
            nonlocal ids_file
            for x in list(a.get(cat) or []):
                if x.get("id") == rid:
                    if cat == "documenti":
                        ids_file = [r_["id"] for r_ in (x.get("allegati") or []) if r_.get("id")]
                    elif cat == "lista":
                        pass
                    a[cat].remove(x)
            if cat == "lista":                                                    # eliminare un animale toglie anche tutto ciò che è suo (dopo conferma esplicita)
                for k_ in AN_ORDINE_CATEGORIE[1:]:
                    for x in list(a.get(k_) or []):
                        if x.get("animale") == rid:
                            if k_ == "documenti":
                                ids_file.extend(r_["id"] for r_ in (x.get("allegati") or []) if r_.get("id"))
                            a[k_].remove(x)
        an_salva(_m, f"Animali: {cat} eliminato")
        if ids_file:
            an_cancella_file(ids_file)
        if cat == "lista":
            st.session_state.pop("an_sel", None)
        st.session_state["messaggio"] = "🗑️ Eliminato."
        st.rerun()
    if c2.button("Annulla", key=f"an_el_no_{cat}_{rid}", width="stretch"):
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# disegnare le voci
# ---------------------------------------------------------------------------------------------------------------------
def an_badge_fonte(r):
    f = r.get("fonte")
    if f == "veterinario":
        return "<span class='an-badge vet'>👨‍⚕️ Veterinario</span>"
    if f == "proprietario":
        return "<span class='an-badge prop'>✍️ Proprietario</span>"
    return ""


def an_riassunto_voce(cat, r):
    """(titolo, riga di dettagli) leggibili di una voce."""
    sp = AN_CATEGORIE[cat]
    if cat == "vaccini":
        t = f"{r.get('nome', '')}"
        det = [r.get("tipo") or "", an_data_it(r.get("data")), ("richiamo " + an_data_it(r["richiamo"])) if r.get("richiamo") else "", r.get("vet") or ""]
    elif cat == "visite":
        t = r.get("motivo") or "Visita"
        det = [an_data_it(r.get("data")), r.get("vet") or "", r.get("clinica") or "", ("diagnosi: " + r["diagnosi"]) if r.get("diagnosi") else "",
               ("prossimo controllo " + an_data_it(r["prossimo"])) if r.get("prossimo") else ""]
    elif cat == "terapie":
        t = r.get("farmaco") or "Terapia"
        det = [r.get("dose") or "", r.get("frequenza") or "", ("dal " + an_data_it(r["dal"])) if r.get("dal") else "", ("fino al " + an_data_it(r["al"])) if r.get("al") else "in corso",
               r.get("motivo") or ""]
    elif cat == "esami":
        t = r.get("tipo") or "Esame"
        det = [an_data_it(r.get("data")), r.get("esito") or "", r.get("vet") or ""]
    elif cat == "interventi":
        t = (r.get("tipo") or "Intervento") + (": " + r["descrizione"][:60] if r.get("descrizione") else "")
        det = [an_data_it(r.get("data")), ("fino al " + an_data_it(r["fine"])) if r.get("fine") else "", r.get("clinica") or ""]
    elif cat == "patologie":
        t = r.get("nome") or "Patologia"
        det = [r.get("stato") or "", ("dal " + an_data_it(r["dal"])) if r.get("dal") else "", r.get("note") or ""]
    elif cat == "allergie":
        t = r.get("sostanza") or "Allergia"
        det = [r.get("reazione") or "", r.get("note") or ""]
    elif cat == "peso":
        t = f"{r.get('kg', '')} kg"
        det = [an_data_it(r.get("data")), r.get("note") or ""]
    elif cat == "diario":
        t = an_data_it(r.get("data")) or "Nota"
        det = [r.get("testo") or ""]
    elif cat == "spese":
        t = r.get("voce") or "Spesa"
        det = [an_data_it(r.get("data")), (f"{float(r['importo']):.2f} €".replace(".", ",") if r.get("importo") not in (None, "") else "")]
    elif cat == "contatti":
        t = r.get("nome") or "Contatto"
        det = [r.get("ruolo") or "", r.get("tel") or "", r.get("email") or "", r.get("indirizzo") or ""]
    else:
        t = r.get("titolo") or "Appuntamento"
        det = [an_data_it(r.get("data")), r.get("ora") or "", r.get("tipo") or "", "✅ fatto" if r.get("fatto") else ""]
    return t, " · ".join(x for x in det if x)


def _an_scheda_voce(cat, r, a, modificabile=True, chiave=""):
    t, det = an_riassunto_voce(cat, r)
    cl = "vet" if r.get("fonte") == "veterinario" else "prop" if r.get("fonte") == "proprietario" else ""
    extra = ""
    if cat == "terapie" and an_terapia_attiva(r):
        extra = "<span class='an-badge att'>in corso</span>"
    if r.get("doc"):
        extra += "<span class='an-badge tipo'>📎 da documento</span>"
    st.markdown(f"<div class='an-card {cl}'><div class='t'>{_an_e(t)}</div><div>{an_badge_fonte(r)}{extra}</div><div class='s'>{_an_e(det)}</div></div>", unsafe_allow_html=True)
    if modificabile:
        c1, c2 = st.columns(2, gap="small")
        if c1.button("✏️ Correggi", key=f"an_mod_{cat}_{r['id']}{chiave}", width="stretch"):
            _an_dialogo_voce(cat, r["id"], r.get("animale", ""))
        if c2.button("🗑️ Elimina", key=f"an_del_{cat}_{r['id']}{chiave}", width="stretch"):
            _an_dialogo_elimina(cat, r["id"], t)


def an_elenco(cat, a, aid, vuoto="Ancora niente qui.", filtro=None, max_voci=None):
    """Titolo, bottone «aggiungi» e le voci di una categoria per un animale."""
    sp = AN_CATEGORIE[cat]
    st.markdown(f"#### {sp['titolo']}")
    if st.button(f"➕ Aggiungi {sp['singolare']}", key=f"an_add_{cat}_{aid}", type="primary", width="stretch"):
        _an_dialogo_voce(cat, None, aid)
    voci = an_voci(a, cat, aid if cat != "contatti" else None)
    if filtro:
        voci = [x for x in voci if filtro(x)]
    chiave_ord = sp["data"] or "creato"
    voci = an_ordina(voci, chiave_ord)
    if not voci:
        st.caption(vuoto)
    for r in voci[:max_voci]:
        _an_scheda_voce(cat, r, a)
    if max_voci and len(voci) > max_voci:
        st.caption(f"… e altre {len(voci) - max_voci}.")
