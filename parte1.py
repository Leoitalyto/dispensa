# -*- coding: utf-8 -*-
"""La nostra dispensa - app Streamlit per tenere traccia di scorte e scadenze."""
import base64
import calendar
import hashlib
import hmac
import html
import io
import json
import os
import random
import re
import tempfile
import time
import urllib.parse
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

# ---------- lingue ----------
LINGUE = {"it": "Italiano", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch"}
LINGUE_DA_DESTRA = set()          # lingue scritte da destra a sinistra (per ora nessuna)
TRADUZIONI = {"it": {"unità (singolare)": "unità"}}   # i file lingue1.py, lingue2.py... aggiungono le altre


def lingua():
    return st.session_state.get("lang", "it")


def t(frase, **valori):
    """Traduce una frase italiana nella lingua scelta (se manca la traduzione resta in italiano)."""
    risultato = TRADUZIONI.get(lingua(), {}).get(frase)
    if risultato is None:
        risultato = TRADUZIONI["it"].get(frase, frase)
    return risultato.format(**valori) if valori else risultato


def t_all(nome):
    """Nome di un allergene nella lingua scelta (nei dati resta sempre in italiano)."""
    return TRADUZIONI.get(lingua(), {}).get("allergene:" + nome, nome)


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
        return t("Senza scadenza")
    if stato == "scaduto":
        return t("Scaduto ieri") if giorni == -1 else t("Scaduto da {n} giorni", n=abs(giorni))
    if giorni == 0:
        return t("Scade oggi")
    if giorni == 1:
        return t("Scade domani")
    return t("Scade tra {n} giorni", n=giorni)


def fmt_num(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s if lingua() == "en" else s.replace(".", ",")


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
    parola = t("unità (singolare)") if unita == 1 else t("unità")
    parti = [f"{fmt_num(unita)} {parola}"]
    if peso:
        parti.append(fmt_peso(peso))
    if vol:
        parti.append(fmt_vol(vol))
    if pezzi:
        parti.append(f"{fmt_num(pezzi)} {t('pz')}")
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


# ---------- QR code ----------
def data_gs1(aammgg):
    """Data GS1 (AAMMGG) -> 'AAAA-MM-GG'. Il giorno 00 significa 'fine del mese'."""
    try:
        anno, mese, giorno = 2000 + int(aammgg[:2]), int(aammgg[2:4]), int(aammgg[4:6])
        if giorno == 0:
            giorno = calendar.monthrange(anno, mese)[1]
        return date(anno, mese, giorno).isoformat()
    except (ValueError, IndexError):
        return None


def ean_da_gtin(gtin):
    """Da un GTIN (8, 12, 13 o 14 cifre) ricava il codice EAN valido, oppure None."""
    g = re.sub(r"\D", "", gtin or "")
    for c in (g, g[1:] if g.startswith("0") else "", g[2:] if g.startswith("00") else ""):
        if c and ean_valido(c):
            return c
    return None


def leggi_qr(testo):
    """Interpreta il contenuto di un QR: link GS1 (con codice, lotto e scadenza), un link qualsiasi o solo testo."""
    ris = {"testo": (testo or "").strip(), "ean": None, "scadenza": None, "lotto": None, "link": None}
    s = ris["testo"]
    if not s:
        return ris
    if s.lower().startswith(("http://", "https://")):
        ris["link"] = s
    m = re.search(r"/01/(\d{8,14})", s) or re.search(r"\(01\)(\d{8,14})", s) or re.match(r"^01(\d{14})", s)
    if m:
        ris["ean"] = ean_da_gtin(m.group(1))
    m = re.search(r"/17/(\d{6})", s) or re.search(r"\(17\)(\d{6})", s) or re.match(r"^01\d{14}17(\d{6})", s)
    if m:
        ris["scadenza"] = data_gs1(m.group(1))
    m = re.search(r"/10/([^/?#]+)", s) or re.search(r"\(10\)([^(\s]+)", s)
    if m:
        ris["lotto"] = urllib.parse.unquote(m.group(1))[:30]
    if not ris["ean"]:
        for numero in re.findall(r"\d{8,14}", s):
            e = ean_da_gtin(numero)
            if e:
                ris["ean"] = e
                break
    return ris


def leggi_qr_da_foto(dati_immagine):
    """Cerca un QR in una foto e ne restituisce il testo."""
    if cv2 is None:
        return None
    img = cv2.imdecode(np.frombuffer(dati_immagine, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    rilevatore = cv2.QRCodeDetector()
    h, w = img.shape[:2]
    for lato in (1000, 700, 480, 1400):
        s = lato / max(h, w)
        ridotta = cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))),
                             interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        try:
            testo, _, _ = rilevatore.detectAndDecode(ridotta)
        except Exception:
            continue
        if testo:
            return testo
    return None


def leggi_foto(dati_immagine):
    """Legge un codice a barre o un QR da una foto. Ritorna un dizionario (vuoto se non legge nulla)."""
    ean = leggi_codice_da_foto(dati_immagine)
    if ean:
        return {"ean": ean}
    testo = leggi_qr_da_foto(dati_immagine)
    return leggi_qr(testo) if testo else {}


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


def _grado(v):
    v = str(v or "").lower()
    return v if v in ("a", "b", "c", "d", "e") else ""


def _stato(analisi, si, no):
    return "si" if si in analisi else "no" if no in analisi else "?"


def interpreta_prodotto(p, lang="it"):
    """Trasforma i dati di Open Food Facts nei campi dell'app (nome e ingredienti nella lingua scelta, se esistono)."""
    valore, unita = parse_quantita(p.get("quantity"))
    etichette = p.get("labels_tags") or []
    nome = p.get("product_name_" + lang) or p.get("product_name_it") or p.get("product_name") or ""
    ingredienti = p.get("ingredients_text_" + lang) or p.get("ingredients_text_it") or p.get("ingredients_text") or ""
    n = p.get("nutriments") or {}

    def num(chiave):
        v = n.get(chiave)
        return round(float(v), 2) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
    nutrienti = {"energia_kcal": num("energy-kcal_100g"), "grassi": num("fat_100g"), "saturi": num("saturated-fat_100g"),
                 "carboidrati": num("carbohydrates_100g"), "zuccheri": num("sugars_100g"),
                 "fibre": num("fiber_100g"), "proteine": num("proteins_100g"), "sale": num("salt_100g")}
    nutrienti = {k: v for k, v in nutrienti.items() if v is not None}
    try:
        nova = int(p.get("nova_group"))
    except (TypeError, ValueError):
        nova = None
    analisi = p.get("ingredients_analysis_tags") or []
    categorie = ", ".join(c.strip() for c in (p.get("categories") or "").split(",")[:3] if c.strip())
    return {
        "nome": nome.strip(),
        "marca": (p.get("brands") or "").split(",")[0].strip(),
        "formato_valore": valore, "formato_unita": unita,
        "immagine": p.get("image_front_small_url") or p.get("image_front_url") or "",
        "allergeni": tag_in_italiano(p.get("allergens_tags")),
        "tracce": tag_in_italiano(p.get("traces_tags")),
        "senza_glutine": "en:no-gluten" in etichette or "en:gluten-free" in etichette,
        "ingredienti": ingredienti.strip(),
        "allergeni_noti": "allergens_tags" in p,
        "categoria": categorie,
        "extra": {
            "nutriscore": _grado(p.get("nutriscore_grade")), "ecoscore": _grado(p.get("ecoscore_grade")),
            "nova": nova if nova in (1, 2, 3, 4) else None, "nutrienti": nutrienti,
            "paesi": (p.get("countries") or "")[:80], "origine": (p.get("origins") or "")[:80],
            "vegano": _stato(analisi, "en:vegan", "en:non-vegan"),
            "vegetariano": _stato(analisi, "en:vegetarian", "en:non-vegetarian"),
            "olio_palma": _stato(analisi, "en:palm-oil", "en:palm-oil-free"),
            "additivi": p.get("additives_n") if isinstance(p.get("additives_n"), int) else None,
        },
    }


UA = {"User-Agent": "DispensaFamiglia/1.0 (app Streamlit)"}
CAMPI_OFF = ("product_name,product_name_it,product_name_en,product_name_es,product_name_fr,product_name_de,"
             "brands,quantity,image_front_small_url,image_front_url,allergens_tags,traces_tags,"
             "ingredients_text,ingredients_text_it,ingredients_text_en,ingredients_text_es,ingredients_text_fr,"
             "ingredients_text_de,labels_tags,nutriscore_grade,nova_group,ecoscore_grade,nutriments,categories,"
             "countries,origins,ingredients_analysis_tags,additives_n")


@st.cache_data(ttl=3600, show_spinner=False)
def cerca_open_food_facts(codice):
    """None = non trovato; {'errore': ...} = problema di rete; altrimenti il prodotto come lo da' Open Food Facts."""
    try:
        r = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{codice}.json",
                         params={"fields": CAMPI_OFF}, timeout=10, headers=UA)
    except requests.RequestException:
        return {"errore": "rete"}
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        return {"errore": f"http {r.status_code}"}
    j = r.json()
    if j.get("status") != 1 or not j.get("product"):
        return None
    return j["product"]


@st.cache_data(ttl=3600, show_spinner=False)
def cerca_prezzi(codice):
    """Ultimi prezzi segnalati dalla community su Open Prices (lista vuota se non ce ne sono)."""
    try:
        r = requests.get("https://prices.openfoodfacts.org/api/v1/prices",
                         params={"product_code": codice, "order_by": "-date", "size": 5}, timeout=8, headers=UA)
        if r.status_code != 200:
            return []
        risultato = []
        for voce in (r.json().get("items") or [])[:5]:
            if voce.get("price") is None:
                continue
            luogo = voce.get("location") or {}
            negozio = ", ".join(x for x in (luogo.get("osm_name"), luogo.get("osm_address_city")) if x)
            risultato.append({"prezzo": float(voce["price"]), "valuta": voce.get("currency") or "EUR",
                              "data": str(voce.get("date") or "")[:10], "negozio": negozio})
        return risultato
    except Exception:
        return []


def link_online(nome, marca, codice, immagine):
    """Collegamenti per cercare il prodotto online: prezzi, offerte, recensioni, foto con Google Lens."""
    ricerca = " ".join(x for x in (marca, nome) if x) or (codice or "")
    q = urllib.parse.quote_plus(ricerca)
    qc = urllib.parse.quote_plus(codice or ricerca)
    tld = {"it": "it", "en": "co.uk", "es": "es", "fr": "fr", "de": "de"}.get(lingua(), "com")
    righe = [("🔎 " + t("Cerca su Google"), f"https://www.google.com/search?q={qc}"),
             ("🛒 " + t("Prezzi su Google Shopping"), f"https://www.google.com/search?tbm=shop&q={q}"),
             ("📦 " + t("Cerca su Amazon"), f"https://www.amazon.{tld}/s?k={q}"),
             ("⭐ " + t("Leggi le recensioni"), "https://www.google.com/search?q=" + urllib.parse.quote_plus(ricerca + " " + t("recensioni")))]
    if immagine and immagine.startswith("http"):
        righe.append(("📷 " + t("Cerca la foto con Google Lens"), "https://lens.google.com/uploadbyurl?url=" + urllib.parse.quote_plus(immagine)))
    if codice:
        righe.append(("💶 " + t("Prezzi su Open Prices"), f"https://prices.openfoodfacts.org/products/{codice}"))
        righe.append(("🥗 " + t("Scheda su Open Food Facts"), f"https://world.openfoodfacts.org/product/{codice}"))
    return righe


# ---------- immagini ----------
def foto_a_data_uri(dati, lato=220):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    img.thumbnail((lato, lato))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def src_sicuro(src):
    return src if src.startswith(("https://", "http://", "data:image/")) else ""


# >>> FINE PARTE 1 di 4: adesso incolla la PARTE 2 qui sotto <<<
