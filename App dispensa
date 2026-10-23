# -*- coding: utf-8 -*-
"""La nostra dispensa - app Streamlit per tenere traccia di scorte e scadenze."""
import base64
import calendar
import html
import io
import json
import os
import re
import tempfile
import time
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image, ImageOps

try:
    import cv2
    _DETECTOR = cv2.barcode.BarcodeDetector()
except Exception:          # senza OpenCV il codice si scrive a mano
    cv2 = None
    _DETECTOR = None

# =====================================================================
# PARTE 1 - COSTANTI E FUNZIONI DI SUPPORTO
# =====================================================================
ALLERGENI_OFF = {            # nome inglese di Open Food Facts -> italiano
    "gluten": "glutine", "milk": "latte", "eggs": "uova", "nuts": "frutta a guscio",
    "peanuts": "arachidi", "soybeans": "soia", "fish": "pesce", "crustaceans": "crostacei",
    "molluscs": "molluschi", "celery": "sedano", "mustard": "senape",
    "sesame-seeds": "sesamo", "sulphur-dioxide-and-sulphites": "solfiti", "lupin": "lupini",
}
ELENCO_ALLERGENI = sorted(set(ALLERGENI_OFF.values()))
UNITA_CONTENUTO = ["pz", "g", "kg", "ml", "cl", "L"]
FATTORE = {"g": ("peso", 1), "kg": ("peso", 1000), "ml": ("volume", 1),
           "cl": ("volume", 10), "L": ("volume", 1000)}
COLORI = {"ok": "#2e7d32", "arancione": "#ef6c00", "rosso": "#d32f2f",
          "scaduto": "#4e342e", "nessuna": "#9e9e9e"}
ICONE = {"ok": "🟢", "arancione": "🟠", "rosso": "🔴", "scaduto": "⚫", "nessuna": "⚪"}


def oggi():
    try:
        return datetime.now(ZoneInfo("Europe/Rome")).date()
    except Exception:
        return date.today()


def aggiungi_mesi(d, n):
    m = d.month - 1 + n
    anno, mese = d.year + m // 12, m % 12 + 1
    return date(anno, mese, min(d.day, calendar.monthrange(anno, mese)[1]))


def stato_scadenza(scad_iso, data_oggi):
    """Ritorna (stato, giorni): scaduto / rosso (entro 1 mese) / arancione (entro 2 mesi) / ok / nessuna."""
    if not scad_iso:
        return "nessuna", None
    try:
        d = date.fromisoformat(scad_iso)
    except ValueError:
        return "nessuna", None
    giorni = (d - data_oggi).days
    if giorni < 0:
        return "scaduto", giorni
    if d <= aggiungi_mesi(data_oggi, 1):
        return "rosso", giorni
    if d <= aggiungi_mesi(data_oggi, 2):
        return "arancione", giorni
    return "ok", giorni


def testo_giorni(stato, giorni):
    if giorni is None:
        return "Senza scadenza"
    if stato == "scaduto":
        return "Scaduto ieri" if giorni == -1 else f"Scaduto da {abs(giorni)} giorni"
    if giorni == 0:
        return "Scade oggi"
    if giorni == 1:
        return "Scade domani"
    return f"Scade tra {giorni} giorni"


def fmt_num(x):
    return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def fmt_peso(g):
    return f"{fmt_num(g / 1000)} kg" if g >= 1000 else f"{fmt_num(g)} g"


def fmt_vol(ml):
    return f"{fmt_num(ml / 1000)} L" if ml >= 1000 else f"{fmt_num(ml)} ml"


def totali(righe):
    """Somma unita', peso (g), volume (ml) e pezzi di un gruppo di prodotti."""
    unita = peso = vol = pezzi = 0.0
    for r in righe:
        q = float(r.get("quantita") or 0)
        unita += q
        u, v = r.get("formato_unita"), r.get("formato_valore")
        if u in FATTORE and v:
            tipo, f = FATTORE[u]
            if tipo == "peso":
                peso += q * float(v) * f
            else:
                vol += q * float(v) * f
        elif u == "pz" and v:
            pezzi += q * float(v)
    return unita, peso, vol, pezzi


def descrivi(righe):
    """Es.: '3 unità · 1,5 kg · 2 L'"""
    unita, peso, vol, pezzi = totali(righe)
    parti = [f"{fmt_num(unita)} {'unità'}"]
    if peso:
        parti.append(fmt_peso(peso))
    if vol:
        parti.append(fmt_vol(vol))
    if pezzi:
        parti.append(f"{fmt_num(pezzi)} pz")
    return " · ".join(parti)


def data_it(iso):
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%Y")
    except Exception:
        return ""


# ---------- codici a barre ----------
def ean_valido(c):
    if not c.isdigit() or len(c) not in (8, 12, 13):
        return False
    cifre = [int(x) for x in c]
    controllo = cifre.pop()
    somma = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(cifre)))
    return (10 - somma % 10) % 10 == controllo


def leggi_codice_da_foto(dati_immagine):
    """Cerca un codice a barre in una foto (prova varie dimensioni, margini e rotazioni)."""
    if _DETECTOR is None:
        return None
    img = cv2.imdecode(np.frombuffer(dati_immagine, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    for margine in (0, 0.2):
        base = img
        if margine:
            p = int(max(img.shape[:2]) * margine)
            base = cv2.copyMakeBorder(img, p, p, p, p, cv2.BORDER_CONSTANT, value=(200, 200, 200))
        h, w = base.shape[:2]
        for lato in (1000, 700, 480, 1400):
            s = lato / max(h, w)
            ridotta = cv2.resize(base, (max(1, int(w * s)), max(1, int(h * s))),
                                 interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
            for rot in (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE):
                prova = ridotta if rot is None else cv2.rotate(ridotta, rot)
                try:
                    r = _DETECTOR.detectAndDecodeWithType(prova)
                except Exception:
                    continue
                infos = r[1] if len(r) >= 2 else []
                for codice in (infos if infos is not None else []):
                    if codice and ean_valido(codice):
                        return codice
    return None


# ---------- Open Food Facts ----------
def parse_quantita(testo):
    """'400 g' -> (400, 'g'); '6 x 33 cl' -> (198, 'cl'); '1,5 l' -> (1.5, 'L')"""
    if not testo:
        return None, None
    m = re.search(r"(?:(\d+)\s*[x×]\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g|ml|cl|l)\b", testo.lower())
    if not m:
        return None, None
    molt = int(m.group(1)) if m.group(1) else 1
    valore = float(m.group(2).replace(",", ".")) * molt
    unita = "L" if m.group(3) == "l" else m.group(3)
    return valore, unita


def tag_in_italiano(tags):
    risultato = []
    for t in tags or []:
        nome = t.split(":", 1)[-1]
        it = ALLERGENI_OFF.get(nome, nome.replace("-", " "))
        if it not in risultato:
            risultato.append(it)
    return risultato


def interpreta_prodotto(p):
    valore, unita = parse_quantita(p.get("quantity"))
    etichette = p.get("labels_tags") or []
    return {
        "nome": (p.get("product_name_it") or p.get("product_name") or "").strip(),
        "marca": (p.get("brands") or "").split(",")[0].strip(),
        "formato_valore": valore, "formato_unita": unita,
        "immagine": p.get("image_front_small_url") or p.get("image_front_url") or "",
        "allergeni": tag_in_italiano(p.get("allergens_tags")),
        "tracce": tag_in_italiano(p.get("traces_tags")),
        "senza_glutine": "en:no-gluten" in etichette or "en:gluten-free" in etichette,
        "ingredienti": (p.get("ingredients_text_it") or p.get("ingredients_text") or "").strip(),
        "allergeni_noti": "allergens_tags" in p,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def cerca_open_food_facts(codice):
    """None = non trovato; {'errore': ...} = problema di rete; altrimenti i dati del prodotto."""
    campi = ("product_name,product_name_it,brands,quantity,image_front_small_url,image_front_url,"
             "allergens_tags,traces_tags,ingredients_text,ingredients_text_it,labels_tags")
    try:
        r = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{codice}.json",
                         params={"fields": campi}, timeout=10,
                         headers={"User-Agent": "DispensaFamiglia/1.0 (app Streamlit)"})
    except requests.RequestException:
        return {"errore": "rete"}
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        return {"errore": f"http {r.status_code}"}
    j = r.json()
    if j.get("status") != 1 or not j.get("product"):
        return None
    return interpreta_prodotto(j["product"])


# ---------- immagini ----------
def foto_a_data_uri(dati, lato=220):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    img.thumbnail((lato, lato))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def src_sicuro(src):
    return src if src.startswith(("https://", "http://", "data:image/")) else ""


# =====================================================================
# PARTE 2 - ARCHIVIO DEI DATI (locale per le prove, GitHub per averli sempre)
# =====================================================================
class Conflitto(Exception):
    pass


class ArchivioLocale:
    """File JSON accanto all'app. ATTENZIONE: su Streamlit Cloud si cancella quando l'app si riavvia."""
    permanente = False

    def __init__(self, percorso):
        self.percorso = percorso

    def leggi(self):
        try:
            with open(self.percorso, encoding="utf-8") as f:
                return json.load(f), None
        except (FileNotFoundError, json.JSONDecodeError):
            return {"articoli": []}, None

    def modifica(self, fn, messaggio=""):
        dati, _ = self.leggi()
        fn(dati)
        cartella = os.path.dirname(os.path.abspath(self.percorso))
        with tempfile.NamedTemporaryFile("w", delete=False, dir=cartella, encoding="utf-8") as tmp:
            json.dump(dati, tmp, ensure_ascii=False)
        os.replace(tmp.name, self.percorso)
        return dati


class ArchivioGitHub:
    """Salva il file JSON in un repository GitHub (i dati restano per sempre)."""
    permanente = True

    def __init__(self, token, repo, percorso="dispensa.json", ramo=None, http=requests):
        self.repo, self.percorso, self.ramo, self.http = repo, percorso, ramo, http
        self.intest = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                       "X-GitHub-Api-Version": "2022-11-28"}

    def _url(self):
        return f"https://api.github.com/repos/{self.repo}/contents/{self.percorso}"

    def leggi(self):
        par = {"ref": self.ramo} if self.ramo else None
        r = self.http.get(self._url(), headers=self.intest, params=par, timeout=20)
        if r.status_code == 404:
            return {"articoli": []}, None
        r.raise_for_status()
        j = r.json()
        if j.get("content"):
            grezzo = base64.b64decode(j["content"])
        else:                                   # file grande: lo leggo come "blob"
            b = self.http.get(f"https://api.github.com/repos/{self.repo}/git/blobs/{j['sha']}",
                              headers=self.intest, timeout=30)
            b.raise_for_status()
            grezzo = base64.b64decode(b.json()["content"])
        try:
            return json.loads(grezzo.decode("utf-8")), j["sha"]
        except json.JSONDecodeError:
            return {"articoli": []}, j["sha"]

    def _scrivi(self, dati, sha, messaggio):
        corpo = {"message": messaggio or "Aggiornamento dispensa",
                 "content": base64.b64encode(json.dumps(dati, ensure_ascii=False).encode("utf-8")).decode()}
        if sha:
            corpo["sha"] = sha
        if self.ramo:
            corpo["branch"] = self.ramo
        r = self.http.put(self._url(), headers=self.intest, json=corpo, timeout=30)
        if r.status_code in (409, 422):
            raise Conflitto()
        r.raise_for_status()

    def modifica(self, fn, messaggio=""):
        for tentativo in range(4):
            dati, sha = self.leggi()
            fn(dati)
            try:
                self._scrivi(dati, sha, messaggio)
                return dati
            except Conflitto:                    # qualcun altro ha salvato nel frattempo: riprovo
                time.sleep(0.5 * (tentativo + 1))
        raise RuntimeError("Non riesco a salvare: troppe modifiche contemporanee. Riprova.")


def segreto(nome, default=None):
    try:
        return st.secrets[nome]
    except Exception:
        return default


@st.cache_resource
def crea_archivio():
    g = segreto("github")
    if g and g.get("token") and g.get("repo"):
        return ArchivioGitHub(g["token"], g["repo"], g.get("path", "dispensa.json"), g.get("branch"))
    return ArchivioLocale(os.environ.get("DISPENSA_FILE", "dispensa_locale.json"))


@st.cache_data(ttl=20, show_spinner=False)
def carica_dati(_archivio):
    dati, _ = _archivio.leggi()
    return dati


def salva(fn, messaggio):
    archivio = crea_archivio()
    archivio.modifica(fn, messaggio)
    carica_dati.clear()


def applica_modifiche(d, modificata):
    """Applica alla dispensa le modifiche fatte nella tabella 'Gestisci'."""
    nuovi = []
    for r in d.get("articoli", []):
        if r["id"] not in modificata.index:
            nuovi.append(r)
            continue
        m = modificata.loc[r["id"]]
        if bool(m["🗑️"]):
            continue
        r["nome"] = str(m["Prodotto"]).strip() or r.get("nome", "")
        r["quantita"] = float(m["Unità"])
        r["formato_valore"] = float(m["Contenuto"]) if m["Contenuto"] else None
        r["formato_unita"] = m["Misura"] if m["Contenuto"] else None
        r["scadenza"] = pd.to_datetime(m["Scadenza"]).date().isoformat() if pd.notna(m["Scadenza"]) else None
        r["note"] = "" if pd.isna(m["Note"]) else str(m["Note"])
        if r["quantita"] > 0:
            nuovi.append(r)           # 0 unità = finito: lo tolgo dalla dispensa
    d["articoli"] = nuovi


# =====================================================================
# PARTE 3 - GRAFICA (HTML e colori)
# =====================================================================
CSS = """
<style>
.hero{background:linear-gradient(135deg,#1b5e20 0%,#00897b 55%,#0288d1 100%);color:#fff;padding:22px 26px;
 border-radius:22px;margin-bottom:14px;box-shadow:0 10px 30px rgba(0,0,0,.15)}
.hero h1{margin:0;font-size:1.9rem;color:#fff;padding:0}
.hero p{margin:4px 0 0;opacity:.92}
.avviso{border-radius:16px;padding:14px 18px;margin:10px 0;border-left:8px solid;box-shadow:0 4px 14px rgba(0,0,0,.08)}
.avviso h3{margin:0 0 4px 0;font-size:1.08rem;padding:0}
.avviso .tot{font-weight:700;margin-bottom:4px}
.avviso ul{margin:6px 0 0 0;padding-left:20px}
.avviso.rosso{background:#ffebee;border-color:#d32f2f;color:#7f0000}
.avviso.arancione{background:#fff3e0;border-color:#ef6c00;color:#6a3100}
.avviso.scaduto{background:#efebe9;border-color:#4e342e;color:#2b1b17}
.griglia{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:16px;margin-top:8px}
.scheda{background:var(--secondary-background-color,#fff);color:var(--text-color,#222);border-radius:20px;
 overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,.12);border-top:8px solid var(--c);display:flex;flex-direction:column}
.scheda .foto{height:150px;display:flex;align-items:center;justify-content:center;background:#fff;font-size:64px}
.scheda .foto img{max-height:140px;max-width:92%;object-fit:contain}
.scheda .corpo{padding:12px 14px 16px 14px;display:flex;flex-direction:column;gap:6px}
.scheda .nome{font-weight:700;font-size:1.05rem;line-height:1.2}
.scheda .marca{opacity:.65;font-size:.85rem;margin-top:-4px}
.scheda .quantita{font-size:.95rem}
.scadenza{display:inline-block;color:#fff;background:var(--c);border-radius:999px;padding:4px 12px;font-size:.85rem;font-weight:600;width:fit-content}
.data{font-size:.8rem;opacity:.7}
.badge{display:inline-block;border-radius:999px;padding:2px 9px;font-size:.75rem;margin:2px 3px 0 0;
 background:rgba(128,128,128,.18)}
.badge.pericolo{background:#d32f2f;color:#fff;font-weight:700}
.badge.attenzione{background:#fbc02d;color:#3b2d00;font-weight:700}
.badge.bene{background:#2e7d32;color:#fff}
.nota{opacity:.7;font-size:.8rem}
</style>
"""


def foto_html(r):
    src = src_sicuro(r.get("immagine") or "")
    return f"<img src='{html.escape(src, quote=True)}' alt=''>" if src else "🥫"


def badge_allergeni(r, mie):
    pezzi = []
    allergeni, tracce = r.get("allergeni") or [], r.get("tracce") or []
    if not r.get("allergeni_noti") and not allergeni:
        pezzi.append("<span class='badge'>❔ Allergeni non verificati</span>")
    for a in allergeni:
        classe = "pericolo" if a in mie else ""
        icona = "⚠️ Contiene " if a in mie else ""
        pezzi.append(f"<span class='badge {classe}'>{icona}{html.escape(a)}</span>")
    for a in tracce:
        classe = "attenzione" if a in mie else ""
        pezzi.append(f"<span class='badge {classe}'>tracce di {html.escape(a)}</span>")
    if r.get("senza_glutine"):
        pezzi.append("<span class='badge bene'>🌾 Senza glutine</span>")
    return "".join(pezzi)


def scheda_html(r, data_oggi, mie):
    stato, giorni = stato_scadenza(r.get("scadenza"), data_oggi)
    colore = COLORI[stato]
    marca = f"<div class='marca'>{html.escape(r['marca'])}</div>" if r.get("marca") else ""
    data = f"<div class='data'>{data_it(r['scadenza'])}</div>" if r.get("scadenza") else ""
    nota = f"<div class='nota'>📝 {html.escape(r['note'])}</div>" if r.get("note") else ""
    return (f"<div class='scheda' style='--c:{colore}'><div class='foto'>{foto_html(r)}</div>"
            f"<div class='corpo'><div class='nome'>{html.escape(r.get('nome', ''))}</div>{marca}"
            f"<div class='quantita'>📦 {html.escape(descrivi([r]))}</div>"
            f"<span class='scadenza'>{ICONE[stato]} {testo_giorni(stato, giorni)}</span>{data}"
            f"<div>{badge_allergeni(r, mie)}</div>{nota}</div></div>")


def avviso_html(titolo, classe, righe, data_oggi):
    voci = "".join(
        f"<li><b>{html.escape(r.get('nome', ''))}</b>: {html.escape(descrivi([r]))} "
        f"· scade il {data_it(r['scadenza'])} ({testo_giorni(*stato_scadenza(r['scadenza'], data_oggi)).lower()})</li>"
        for r in righe)
    return (f"<div class='avviso {classe}'><h3>{titolo}</h3>"
            f"<div class='tot'>In totale: {html.escape(descrivi(righe))}</div><ul>{voci}</ul></div>")


# =====================================================================
# PARTE 4 - PAGINA
# =====================================================================
st.set_page_config(page_title="La nostra dispensa", page_icon="🥫", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# --- accesso con codice famiglia (facoltativo) ---
pin = segreto("pin")
if pin and st.session_state.get("pin_ok") != True:
    st.markdown("<div class='hero'><h1>🥫 La nostra dispensa</h1><p>Inserisci il codice di famiglia</p></div>",
                unsafe_allow_html=True)
    inserito = st.text_input("Codice di famiglia", type="password")
    if inserito and inserito == str(pin):
        st.session_state["pin_ok"] = True
        st.rerun()
    elif inserito:
        st.error("Codice non corretto.")
    st.stop()

archivio = crea_archivio()
try:
    dati = carica_dati(archivio)
except Exception as e:
    st.error(f"Non riesco a leggere i dati: {e}")
    st.stop()
articoli = dati.get("articoli", [])
data_oggi = oggi()

# --- barra laterale ---
with st.sidebar:
    st.header("👤 Chi sei?")
    utente = st.text_input("Il tuo nome", key="utente", placeholder="es. Leo")
    st.header("🌾 Allergie")
    mie = st.multiselect("Segnala i prodotti che contengono:", ELENCO_ALLERGENI, key="mie_allergie")
    solo_sicuri = st.checkbox("Mostra solo prodotti sicuri per me", value=False,
                              help="Nasconde i prodotti con questi allergeni e quelli senza informazioni sugli allergeni.")
    st.divider()
    if archivio.permanente:
        st.success("💾 Dati salvati su GitHub")
    else:
        st.warning("⚠️ Modalità prova: i dati si cancellano quando l'app si riavvia. "
                   "Collega GitHub (vedi scheda Info).")
    if st.button("🔄 Aggiorna"):
        carica_dati.clear()
        st.rerun()

# --- intestazione e avvisi ---
st.markdown("<div class='hero'><h1>🥫 La nostra dispensa</h1>"
            "<p>Scorte, scadenze e allergeni sempre sotto controllo</p></div>", unsafe_allow_html=True)

con_stato = [(r, *stato_scadenza(r.get("scadenza"), data_oggi)) for r in articoli]
scaduti = sorted([r for r, s, g in con_stato if s == "scaduto"], key=lambda r: r["scadenza"])
rossi = sorted([r for r, s, g in con_stato if s == "rosso"], key=lambda r: r["scadenza"])
arancioni = sorted([r for r, s, g in con_stato if s == "arancione"], key=lambda r: r["scadenza"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Prodotti", len(articoli))
c2.metric("🟠 Entro 2 mesi", len(arancioni))
c3.metric("🔴 Entro 1 mese", len(rossi))
c4.metric("⚫ Scaduti", len(scaduti))

if scaduti:
    st.markdown(avviso_html("⚫ Scaduti: da buttare o controllare", "scaduto", scaduti, data_oggi), unsafe_allow_html=True)
if rossi:
    st.markdown(avviso_html("🔴 Scadono entro 1 mese", "rosso", rossi, data_oggi), unsafe_allow_html=True)
if arancioni:
    st.markdown(avviso_html("🟠 Scadono entro 2 mesi", "arancione", arancioni, data_oggi), unsafe_allow_html=True)

if st.session_state.get("messaggio"):
    st.success(st.session_state.pop("messaggio"))

tab_dispensa, tab_aggiungi, tab_gestisci, tab_info = st.tabs(
    ["🏠 Dispensa", "➕ Aggiungi", "✏️ Gestisci", "ℹ️ Info"])

# ---------------------------------------------------------------------
# DISPENSA
# ---------------------------------------------------------------------
with tab_dispensa:
    f1, f2, f3 = st.columns([3, 2, 2])
    cerca = f1.text_input("🔎 Cerca", placeholder="nome o marca", label_visibility="collapsed")
    filtro = f2.selectbox("Mostra", ["Tutti", "Solo in scadenza (2 mesi)", "Solo rossi (1 mese)", "Scaduti"],
                          label_visibility="collapsed")
    vista = f3.radio("Vista", ["Schede", "Tabella"], horizontal=True, label_visibility="collapsed")

    visibili = []
    for r, stato, giorni in con_stato:
        if cerca and cerca.lower() not in (r.get("nome", "") + " " + r.get("marca", "")).lower():
            continue
        if filtro == "Solo in scadenza (2 mesi)" and stato not in ("arancione", "rosso", "scaduto"):
            continue
        if filtro == "Solo rossi (1 mese)" and stato not in ("rosso", "scaduto"):
            continue
        if filtro == "Scaduti" and stato != "scaduto":
            continue
        if solo_sicuri and mie:
            if any(a in mie for a in (r.get("allergeni") or [])) or not (r.get("allergeni_noti") or r.get("allergeni")):
                continue
        visibili.append((r, stato, giorni))
    visibili.sort(key=lambda x: (x[0].get("scadenza") or "9999-12-31"))

    if not articoli:
        st.info("La dispensa è vuota. Vai nella scheda ➕ Aggiungi per inserire il primo prodotto.")
    elif not visibili:
        st.info("Nessun prodotto corrisponde ai filtri.")
    elif vista == "Schede":
        st.markdown("<div class='griglia'>" + "".join(scheda_html(r, data_oggi, mie) for r, _, _ in visibili) + "</div>",
                    unsafe_allow_html=True)
    else:
        tab = pd.DataFrame([{
            "Foto": src_sicuro(r.get("immagine") or "") or None,
            "Prodotto": r.get("nome", ""), "Marca": r.get("marca", ""),
            "Quantità": descrivi([r]),
            "Scadenza": data_it(r.get("scadenza")), "Stato": f"{ICONE[s]} {testo_giorni(s, g)}",
            "Allergeni": ", ".join(r.get("allergeni") or []) or ("—" if r.get("allergeni_noti") else "non verificati"),
            "_stato": s,
        } for r, s, g in visibili])
        sfondi = {"rosso": "background-color:#ffcdd2", "arancione": "background-color:#ffe0b2",
                  "scaduto": "background-color:#d7ccc8", "ok": "", "nessuna": ""}
        stile = tab.style.apply(lambda riga: [sfondi[riga["_stato"]]] * len(riga), axis=1)
        st.dataframe(stile, hide_index=True, height=min(700, 60 + 72 * len(tab)),
                     column_config={"Foto": st.column_config.ImageColumn("Foto", width="small"),
                                    "_stato": None})

# ---------------------------------------------------------------------
# AGGIUNGI
# ---------------------------------------------------------------------
with tab_aggiungi:
    n = st.session_state.setdefault("n_form", 0)
    K = lambda nome: f"{nome}_{n}"
    st.subheader("1️⃣ Leggi il codice a barre (facoltativo)")
    usa_camera = st.toggle("📷 Usa la fotocamera del telefono", key=K("usa_camera"))
    foto_codice = st.camera_input("Inquadra il codice a barre e scatta", key=K("camera")) if usa_camera else None
    foto_file = st.file_uploader("…oppure carica una foto del codice", type=["jpg", "jpeg", "png"], key=K("file_codice"))
    for sorgente in (foto_codice, foto_file):
        if sorgente is not None:
            dati_img = sorgente.getvalue()
            impronta = hash(dati_img)
            if st.session_state.get(K("ultima_foto")) != impronta:
                st.session_state[K("ultima_foto")] = impronta
                trovato = leggi_codice_da_foto(dati_img)
                if trovato:
                    st.session_state[K("codice")] = trovato
                    st.session_state[K("cercato")] = None       # forza la ricerca
                else:
                    st.session_state[K("codice_non_letto")] = True
    if st.session_state.pop(K("codice_non_letto"), False):
        st.warning("Non riesco a leggere il codice dalla foto. Riprova più vicino e con più luce, "
                   "oppure scrivi i numeri qui sotto.")
    codice = st.text_input("Codice a barre (i numeri sotto le barre)", key=K("codice"),
                           placeholder="es. 8076809513388").strip()

    # ricerca: prima nella dispensa, poi su Open Food Facts
    if codice and ean_valido(codice) and st.session_state.get(K("cercato")) != codice:
        st.session_state[K("cercato")] = codice
        gia = [a for a in articoli if a.get("barcode") == codice]
        info = None
        if gia:
            info, origine = dict(gia[-1]), "dispensa"
        else:
            with st.spinner("Cerco il prodotto su Open Food Facts..."):
                info = cerca_open_food_facts(codice)
            origine = "off"
        st.session_state[K("origine")] = origine if info and "errore" not in info else ("errore" if info else "nontrovato")
        if info and "errore" not in info:
            st.session_state[K("nome")] = info.get("nome", "")
            st.session_state[K("marca")] = info.get("marca", "")
            if info.get("formato_valore"):
                st.session_state[K("fval")] = float(info["formato_valore"])
                st.session_state[K("funita")] = info.get("formato_unita") or "pz"
            st.session_state[K("allergeni")] = [a for a in (info.get("allergeni") or [])]
            st.session_state[K("tracce")] = [a for a in (info.get("tracce") or [])]
            st.session_state[K("senza_glutine")] = bool(info.get("senza_glutine"))
            st.session_state[K("ingredienti")] = info.get("ingredienti", "")
            st.session_state[K("immagine")] = info.get("immagine", "")
            st.session_state[K("noti")] = bool(info.get("allergeni_noti"))
    elif codice and not ean_valido(codice):
        st.error("Il codice non sembra corretto (di solito ha 13 numeri). Controlla le cifre.")

    origine = st.session_state.get(K("origine"))
    if origine == "dispensa":
        st.success("✅ Prodotto già presente in dispensa: ho copiato nome, foto e allergeni.")
    elif origine == "off":
        st.success("✅ Prodotto trovato su Open Food Facts. Controlla i dati e completa quantità e scadenza.")
    elif origine == "nontrovato":
        st.info("Prodotto non trovato nel database: compila i dati a mano (e aggiungi una foto).")
    elif origine == "errore":
        st.warning("Non riesco a contattare Open Food Facts adesso. Compila a mano o riprova.")

    st.subheader("2️⃣ Dati del prodotto")
    for chiave, valore in (("nome", ""), ("marca", ""), ("quant", 1.0), ("fval", 0.0), ("funita", "g"),
                           ("allergeni", []), ("tracce", []), ("senza_glutine", False), ("ingredienti", ""),
                           ("note", ""), ("senza_scad", False), ("noti", False), ("immagine", "")):
        st.session_state.setdefault(K(chiave), valore)
    st.session_state.setdefault(K("scad"), aggiungi_mesi(data_oggi, 6))

    a1, a2 = st.columns(2)
    nome = a1.text_input("Nome del prodotto *", key=K("nome"))
    marca = a2.text_input("Marca", key=K("marca"))
    b1, b2, b3 = st.columns(3)
    quant = b1.number_input("Quante unità hai? *", min_value=0.0, step=1.0, key=K("quant"),
                            help="Quanti pacchi, bottiglie, barattoli...")
    fval = b2.number_input("Contenuto di ogni unità", min_value=0.0, step=10.0, key=K("fval"),
                           help="Es. 500 (se è un pacco da 500 g). Lascia 0 se non serve.")
    funita = b3.selectbox("Unità del contenuto", UNITA_CONTENUTO, key=K("funita"))
    d1, d2 = st.columns([2, 1])
    senza_scad = d2.checkbox("Senza scadenza", key=K("senza_scad"))
    scad = d1.date_input("Scadenza", key=K("scad"), format="DD/MM/YYYY", disabled=senza_scad)

    with st.expander("🌾 Allergeni e ingredienti"):
        allergeni = st.multiselect("Contiene", ELENCO_ALLERGENI, key=K("allergeni"))
        tracce = st.multiselect("Può contenere tracce di", ELENCO_ALLERGENI, key=K("tracce"))
        senza_glutine = st.checkbox("Etichettato senza glutine", key=K("senza_glutine"))
        noti = st.checkbox("Ho controllato l'etichetta: gli allergeni indicati sono completi", key=K("noti"))
        ingredienti = st.text_area("Ingredienti", key=K("ingredienti"), height=90)
    with st.expander("📷 Foto del prodotto"):
        if st.session_state.get(K("immagine")):
            st.image(src_sicuro(st.session_state[K("immagine")]), width=140)
        foto_prod = st.file_uploader("Carica o scatta una foto (sostituisce quella attuale)",
                                     type=["jpg", "jpeg", "png"], key=K("foto_prod"))
    note = st.text_input("Note (facoltative)", key=K("note"), placeholder="es. aperto, aprire dopo il 10")

    if st.button("💾 Salva in dispensa", type="primary", width="stretch"):
        if not nome.strip():
            st.error("Scrivi il nome del prodotto.")
        elif quant <= 0:
            st.error("Indica quante unità hai (almeno 1).")
        else:
            immagine = foto_a_data_uri(foto_prod.getvalue()) if foto_prod is not None else st.session_state.get(K("immagine"), "")
            riga = {
                "id": uuid.uuid4().hex[:10], "barcode": codice if ean_valido(codice) else "",
                "nome": nome.strip(), "marca": marca.strip(), "quantita": float(quant),
                "formato_valore": float(fval) if fval else None, "formato_unita": funita if fval else None,
                "scadenza": None if senza_scad else scad.isoformat(),
                "immagine": immagine, "allergeni": allergeni, "tracce": tracce,
                "senza_glutine": bool(senza_glutine), "allergeni_noti": bool(noti or allergeni),
                "ingredienti": ingredienti.strip(), "note": note.strip(),
                "aggiunto_da": utente.strip(), "aggiunto_il": datetime.now().isoformat(timespec="seconds"),
            }
            try:
                salva(lambda d: d.setdefault("articoli", []).append(riga), f"Aggiunto {riga['nome']}")
                st.session_state["messaggio"] = f"✅ {riga['nome']} aggiunto alla dispensa."
                st.session_state["n_form"] = n + 1
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")

# ---------------------------------------------------------------------
# GESTISCI
# ---------------------------------------------------------------------
with tab_gestisci:
    st.subheader("Modifica quantità, scadenze e note")
    st.caption("Cambia i valori nella tabella, spunta 🗑️ per eliminare, poi premi Salva modifiche.")
    if not articoli:
        st.info("Non c'è ancora nulla da gestire.")
    else:
        df = pd.DataFrame([{
            "id": r["id"], "🗑️": False, "Prodotto": r.get("nome", ""), "Unità": float(r.get("quantita") or 0),
            "Contenuto": r.get("formato_valore") or 0.0, "Misura": r.get("formato_unita") or "g",
            "Scadenza": date.fromisoformat(r["scadenza"]) if r.get("scadenza") else None,
            "Note": r.get("note", ""),
        } for r in sorted(articoli, key=lambda r: r.get("scadenza") or "9999")]).set_index("id")
        modificata = st.data_editor(
            df, hide_index=True, width="stretch", key="editor",
            column_config={
                "🗑️": st.column_config.CheckboxColumn("🗑️", width="small"),
                "Unità": st.column_config.NumberColumn("Unità", min_value=0.0, step=1.0),
                "Contenuto": st.column_config.NumberColumn("Contenuto", min_value=0.0),
                "Misura": st.column_config.SelectboxColumn("Misura", options=UNITA_CONTENUTO),
                "Scadenza": st.column_config.DateColumn("Scadenza", format="DD/MM/YYYY"),
            })
        if st.button("💾 Salva modifiche", type="primary"):
            try:
                salva(lambda d: applica_modifiche(d, modificata), "Modifiche alla dispensa")
                st.session_state["messaggio"] = "✅ Modifiche salvate."
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
        st.caption("Se metti 0 unità il prodotto viene tolto dalla dispensa (finito).")
        elenco = pd.DataFrame([{k: (", ".join(v) if isinstance(v, list) else v)
                                for k, v in r.items() if k != "immagine"} for r in articoli])
        st.download_button("⬇️ Scarica l'elenco (CSV)", elenco.to_csv(index=False).encode("utf-8"),
                           "dispensa.csv", "text/csv")

# ---------------------------------------------------------------------
# INFO
# ---------------------------------------------------------------------
with tab_info:
    st.markdown("""
**Come funzionano i colori**
- 🟢 verde: più di 2 mesi alla scadenza
- 🟠 arancione: la scadenza è entro 2 mesi
- 🔴 rosso: la scadenza è entro 1 mese
- ⚫ scuro: già scaduto

**Allergeni: leggi sempre l'etichetta.** I dati dei prodotti arrivano da *Open Food Facts*, un database
compilato dagli utenti: possono essere incompleti o non aggiornati. L'app ti aiuta, ma non sostituisce
la lettura dell'etichetta sulla confezione, soprattutto in caso di allergia o celiachia.

**Come aggiungere un prodotto:** scheda ➕ Aggiungi, fotografa il codice a barre (o scrivi i numeri),
controlla i dati, scrivi quante unità hai e la scadenza.

**Dati permanenti:** per non perdere i dati quando l'app si riavvia, vanno collegati a GitHub
(in Streamlit: Settings → Secrets).
```
[github]
token = "il_tuo_token"
repo = "TuoNome/dispensa-dati"
```
Facoltativo, per proteggere l'app con un codice: `pin = "1234"`.

Dati dei prodotti: Open Food Facts (licenza ODbL).
""")
