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


# >>> FINE PARTE 1 di 4: adesso incolla la PARTE 2 qui sotto <<<
