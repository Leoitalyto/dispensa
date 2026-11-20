# -*- coding: utf-8 -*-
"""🛒 SPESA SMART — confronto prezzi, offerte, liste ottimizzate e scontrini, DENTRO la Dispensa.

La Dispensa diventa il contenitore di due cose: 📦 Scorte (la dispensa di prima, intatta) e 🛒 Spesa Smart (questa).

DATI («tabelle» con identificativi unici, nel file personale, chiave d["spesa_smart"]; migrazione sicura e reversibile:
si aggiunge solo questa chiave, niente di quello che c'era viene toccato; togliendo la chiave si torna esattamente a prima)
  prodotti     {id, nome, categoria, marca, variante, ean, formato_valore, formato_unita, confezioni, quantita_rif, immagine, alias[], creato_il}
  negozi       {id, nome, catena, citta, indirizzo, creato_il}                       (più punti vendita della stessa catena)
  rilevazioni  {id, prodotto_id → prodotti, negozio_id → negozi, prezzo, prezzo_promo, confezioni, formato_valore, formato_unita,
                prezzo_unitario, unita_base, data, promo_dal, promo_al, tessera, note, fonte (manuale|scontrino|acquisto|open prices), da_verificare}
  acquisti     {id, prodotto_id, negozio_id, quantita, prezzo_pagato, data, scontrino_id → scontrini, rilevazione_id → rilevazioni}
  scontrini    {id, negozio_id, data, totale, righe, creato_il}
  liste        {id, nome, creata_il, proprietario, stato (aperta|chiusa)}            (liste PRIVATE; la lista della Dispensa resta quella condivisa)
  liste_righe  {id, lista_id → liste, prodotto_id → prodotti, quantita, priorita, stato (da comprare|preso)}
Regole: un EAN = un solo prodotto; stesso nome+marca+variante+formato = stesso prodotto (si riusa, non si duplica);
un prodotto o un negozio usato da prezzi/acquisti/liste non si cancella (si UNISCE a un altro: i riferimenti si spostano).

ARCHIVIO PRODOTTI UNICO con la Dispensa: i prodotti della Dispensa (articoli) e della sua lista della spesa compaiono da soli
nell'archivio (stessa chiave della Dispensa: codice a barre, altrimenti il nome); la scheda di Spesa Smart si crea solo quando serve
(primo prezzo), con gli stessi dati. La lista della spesa principale È la lista della Dispensa (condivisa con la famiglia).

VALIDITÀ DEI PREZZI (mai un prezzo vecchio o una promozione finita mostrati come validi):
  promozione in corso (dal ≤ oggi ≤ al)  → valida fino al giorno «al»
  prezzo normale ≤ 30 giorni             → attivo
  31–90 giorni o segnato «da verificare» → 🟠 da verificare (mostrato a parte, mai come «il più basso»)
  oltre 90 giorni / promozione finita     → scaduto (solo nello storico)
Caricato da app_dispensa.py dopo lettore_unico.py."""
import html as _ss_h
import itertools as _ss_it
import re as _ss_re
import unicodedata as _ss_ud
import uuid as _ss_uuid
from datetime import date as _ss_date, datetime as _ss_dt, timedelta as _ss_td

import streamlit as st

SS_VERSIONE = 1
SS_FRESCO = 30                    # giorni: un prezzo normale è «attivo»
SS_VECCHIO = 90                   # giorni: oltre, è scaduto
SS_SOGLIA_EURO = 1.50             # risparmio minimo per consigliare un negozio in più…
SS_SOGLIA_PCT = 4.0               # …e in percentuale sul totale
SS_TABELLE = ("prodotti", "negozi", "rilevazioni", "acquisti", "scontrini", "liste", "liste_righe")
SS_CATEGORIE = ["Frutta e verdura", "Carne e pesce", "Latte, latticini e uova", "Pane e forno", "Pasta, riso e cereali", "Scatolame e conserve", "Surgelati",
                "Bevande", "Colazione e dolci", "Condimenti e spezie", "Snack", "Igiene e cura persona", "Pulizia casa", "Neonati", "Animali", "Altro"]
SS_UNITA = {"g": ("kg", 0.001), "gr": ("kg", 0.001), "hg": ("kg", 0.1), "kg": ("kg", 1.0), "mg": ("kg", 0.000001),
            "ml": ("l", 0.001), "cl": ("l", 0.01), "dl": ("l", 0.1), "l": ("l", 1.0), "lt": ("l", 1.0),
            "pz": ("pz", 1.0), "pezzi": ("pz", 1.0), "pezzo": ("pz", 1.0), "rotoli": ("pz", 1.0), "capsule": ("pz", 1.0), "lavaggi": ("lavaggio", 1.0), "m": ("m", 1.0)}
SS_UNITA_SCELTA = ["g", "kg", "ml", "cl", "l", "pz", "lavaggi", "m"]
SS_NOME_BASE = {"kg": "€/kg", "l": "€/litro", "pz": "€/pezzo", "lavaggio": "€/lavaggio", "m": "€/metro"}
SS_FONTI = ("manuale", "scontrino", "acquisto", "open prices")


# =====================================================================================================================
# 1. PICCOLE UTILITÀ
# =====================================================================================================================
def ss_id():
    return _ss_uuid.uuid4().hex[:10]


def ss_ora():
    return _ss_dt.now().isoformat(timespec="seconds")


def ss_oggi():
    try:
        return oggi()
    except Exception:
        return _ss_date.today()


def ss_norm(x):
    t = _ss_ud.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(_ss_re.sub(r"[^a-z0-9]+", " ", t).split())


def ss_parole(x):
    stop = {"con", "per", "gusto", "alla", "allo", "alle", "del", "della", "di", "da", "in", "il", "la", "le", "lo", "gli", "e", "x", "pz", "conf", "gr", "g", "kg", "ml", "l", "cl"}
    return {w for w in ss_norm(x).split() if len(w) > 1 and w not in stop and not w.isdigit()}


def ss_euro(v):
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    except Exception:
        return "—"


def ss_num(v, default=None):
    try:
        if v is None or v == "":
            return default
        x = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
        return x if x == x else default                                  # NaN → default
    except Exception:
        return default


def ss_data(iso):
    try:
        return _ss_date.fromisoformat(str(iso)[:10])
    except Exception:
        return None


def ss_data_it(iso):
    d = ss_data(iso) if not isinstance(iso, _ss_date) else iso
    return d.strftime("%d/%m/%Y") if d else ""


def _ss_esc(x):
    return _ss_h.escape(str(x or ""))


# =====================================================================================================================
# 2. MIGRAZIONE E ACCESSO ALLE TABELLE
# =====================================================================================================================
def ss_migra(d):
    """Crea (o completa) d["spesa_smart"] senza toccare nient'altro. Idempotente: si può chiamare quante volte si vuole."""
    ss = d.get("spesa_smart")
    if not isinstance(ss, dict):
        ss = d["spesa_smart"] = {}
    for t_ in SS_TABELLE:
        if not isinstance(ss.get(t_), list):
            ss[t_] = []
    if not isinstance(ss.get("impostazioni"), dict):
        ss["impostazioni"] = {}
    ss["versione"] = max(int(ss.get("versione") or 0), SS_VERSIONE)
    return ss


def ss_vuoto():
    return ss_migra({})


def ss_trova(ss, tabella, id_):
    return next((x for x in ss.get(tabella) or [] if isinstance(x, dict) and x.get("id") == id_), None)


# =====================================================================================================================
# 3. UNITÀ DI MISURA E PREZZO UNITARIO
# =====================================================================================================================
def ss_formato_da_testo(testo):
    """«6 x 1,5 l» → (6, 1.5, 'l'); «500 g» → (1, 500, 'g'); «12 rotoli» → (1, 12, 'rotoli')."""
    t = str(testo or "").lower().replace(",", ".")
    m = _ss_re.search(r"(?:(\d+)\s*[x×]\s*)?(\d+(?:\.\d+)?)\s*(kg|gr|g|hg|mg|ml|cl|dl|lt|l|pz|pezzi|pezzo|rotoli|capsule|lavaggi|m)\b", t)
    if not m:
        return None, None, None
    return (int(m.group(1)) if m.group(1) else 1), float(m.group(2)), m.group(3)


def ss_quantita_base(confezioni, valore, unita):
    """(quantità nell'unità base, unità base): 6 × 1,5 l → (9.0, 'l'); 500 g → (0.5, 'kg'); senza formato → (confezioni, 'pz')."""
    u = str(unita or "").strip().lower()
    n = ss_num(confezioni, 1) or 1
    v = ss_num(valore)
    if u in SS_UNITA and v and v > 0:
        base, f = SS_UNITA[u]
        return n * v * f, base
    return n, "pz"


def ss_prezzo_unitario(prezzo, confezioni, valore, unita):
    """(prezzo per unità base, unità base). None se il prezzo manca."""
    p = ss_num(prezzo)
    if p is None or p <= 0:
        return None, None
    q, base = ss_quantita_base(confezioni, valore, unita)
    if not q or q <= 0:
        return None, None
    return round(p / q, 4), base


def ss_fmt_unitario(pu, base):
    if pu is None:
        return ""
    return ss_euro(pu).replace(" €", "") + " " + SS_NOME_BASE.get(base, "€/" + str(base))


def ss_fmt_formato(x):
    v, u, n = ss_num(x.get("formato_valore")), x.get("formato_unita") or "", int(ss_num(x.get("confezioni"), 1) or 1)
    if not v:
        return (f"{n} pz" if n > 1 else "")
    vv = (f"{v:g}").replace(".", ",")
    return (f"{n} × " if n > 1 else "") + f"{vv} {u}"


# =====================================================================================================================
# 4. PRODOTTI: archivio unico con la Dispensa, niente doppioni
# =====================================================================================================================
def ss_chiave_disp(r):
    """La stessa chiave della Dispensa (spesa.py): codice a barre, altrimenti il nome in minuscolo."""
    return ((r.get("barcode") or r.get("ean") or "").strip() or (r.get("nome") or "").strip().lower())


def ss_firma(p):
    return "|".join((ss_norm(p.get("nome")), ss_norm(p.get("marca")), ss_norm(p.get("variante")), ss_fmt_formato(p)))


def ss_cerca_doppione(ss, p, escludi=None):
    """Il prodotto già esistente che sarebbe un doppione di p (stesso EAN, oppure stesso nome+marca+variante+formato)."""
    ean = str(p.get("ean") or "").strip()
    for x in ss["prodotti"]:
        if x.get("id") == escludi:
            continue
        if ean and str(x.get("ean") or "").strip() == ean:
            return x
    f = ss_firma(p)
    if not ss_norm(p.get("nome")):
        return None
    for x in ss["prodotti"]:
        if x.get("id") != escludi and ss_firma(x) == f:
            return x
    return None


def ss_valida_prodotto(p):
    """Elenco dei problemi (vuoto se va bene)."""
    err = []
    if not ss_norm(p.get("nome")):
        err.append("Scrivi il nome del prodotto.")
    ean = str(p.get("ean") or "").strip()
    if ean and not (ean.isdigit() and len(ean) in (8, 12, 13, 14)):
        err.append("Il codice a barre deve avere 8, 12, 13 o 14 cifre.")
    v = ss_num(p.get("formato_valore"))
    if p.get("formato_valore") not in (None, "") and (v is None or v <= 0):
        err.append("Il formato deve essere un numero maggiore di zero.")
    if p.get("formato_unita") and str(p["formato_unita"]).lower() not in SS_UNITA:
        err.append("Unità di misura non riconosciuta.")
    return err


def ss_aggiungi_prodotto(ss, p):
    """(prodotto, nuovo?): se esiste già lo stesso prodotto lo riusa (e completa i campi vuoti), altrimenti lo crea."""
    p = {k: v for k, v in p.items() if not str(k).startswith("_")}
    for k in ("nome", "marca", "variante", "categoria", "ean", "immagine", "formato_unita"):
        if isinstance(p.get(k), str):
            p[k] = p[k].strip()
    esiste = ss_cerca_doppione(ss, p)
    if esiste:
        for k, v in p.items():
            if v not in (None, "", []) and esiste.get(k) in (None, "", []):
                esiste[k] = v
        return esiste, False
    p.setdefault("confezioni", 1)
    p.setdefault("alias", [])
    p["id"] = ss_id()
    p["creato_il"] = ss_ora()
    ss["prodotti"].append(p)
    return p, True


def ss_da_dispensa(r):
    """Scheda di prodotto dai dati di un articolo della Dispensa o di una riga della sua lista della spesa."""
    return {"nome": r.get("nome", ""), "marca": r.get("marca", ""), "ean": r.get("barcode", "") or "", "categoria": r.get("categoria", "") or "",
            "formato_valore": r.get("formato_valore"), "formato_unita": ("l" if r.get("formato_unita") == "L" else r.get("formato_unita")) or "",
            "confezioni": 1, "immagine": r.get("immagine", "") if str(r.get("immagine", "")).startswith("http") else ""}


def ss_catalogo(ss, d_disp=None):
    """Tutti i prodotti: quelli di Spesa Smart + quelli della Dispensa e della sua lista che non hanno ancora una scheda (id «v:…»)."""
    out = list(ss["prodotti"])
    gia = {str(x.get("ean")).strip() for x in out if x.get("ean")} | {ss_norm(x.get("nome")) for x in out}
    for r in ((d_disp or {}).get("articoli") or []) + ((d_disp or {}).get("spesa") or []):
        if not isinstance(r, dict) or not (r.get("nome") or r.get("barcode")):
            continue
        ean, nn = str(r.get("barcode") or "").strip(), ss_norm(r.get("nome"))
        if (ean and ean in gia) or (not ean and nn in gia) or (ean and not nn):
            continue
        v = ss_da_dispensa(r)
        v["id"] = "v:" + (ean or nn)
        v["_virtuale"] = True
        out.append(v)
        gia.add(ean) if ean else gia.add(nn)
        gia.add(nn)
    return out


def ss_materializza(ss, p):
    """Un prodotto «virtuale» (della Dispensa) diventa una scheda vera. Ritorna il prodotto vero."""
    if not str(p.get("id", "")).startswith("v:"):
        return p
    q, _n = ss_aggiungi_prodotto(ss, {k: v for k, v in p.items() if k not in ("id", "_virtuale")})
    return q


def ss_prodotto_per_riga_disp(ss, r):
    """Il prodotto di Spesa Smart che corrisponde a un articolo/riga della Dispensa (None se non c'è)."""
    ean, nn = str(r.get("barcode") or r.get("ean") or "").strip(), ss_norm(r.get("nome"))
    if ean:
        x = next((p for p in ss["prodotti"] if str(p.get("ean") or "").strip() == ean), None)
        if x:
            return x
    cand = [p for p in ss["prodotti"] if ss_norm(p.get("nome")) == nn and nn]
    if len(cand) > 1 and r.get("marca"):
        cand = [p for p in cand if ss_norm(p.get("marca")) == ss_norm(r.get("marca"))] or cand
    return cand[0] if cand else None


def ss_trova_prodotto_da_testo(ss, testo, minimo=0.6):
    """Per lo scontrino: (prodotto, punteggio) del prodotto più simile alla descrizione (anche gli «alias» imparati)."""
    base = ss_parole(testo)
    if not base:
        return None, 0
    meglio, pm = None, 0.0
    for p in ss["prodotti"]:
        for nome in [p.get("nome", "") + " " + p.get("marca", "") + " " + p.get("variante", "")] + list(p.get("alias") or []):
            if ss_norm(nome) == ss_norm(testo):
                return p, 1.0
            w = ss_parole(nome)
            if not w:
                continue
            pt = len(base & w) / max(len(base), len(w))
            if pt > pm:
                meglio, pm = p, pt
    return (meglio, pm) if pm >= minimo else (None, pm)


def ss_riferimenti(ss, tabella, id_):
    campo = {"prodotti": "prodotto_id", "negozi": "negozio_id"}[tabella]
    return sum(1 for t_ in ("rilevazioni", "acquisti", "liste_righe", "scontrini") for x in ss[t_] if x.get(campo) == id_)


def ss_unisci(ss, tabella, tieni_id, togli_id):
    """Unisce due doppioni: tutti i riferimenti passano a «tieni», «togli» sparisce (i suoi nomi restano come alias)."""
    if tieni_id == togli_id:
        return False
    tieni, togli = ss_trova(ss, tabella, tieni_id), ss_trova(ss, tabella, togli_id)
    if not tieni or not togli:
        return False
    campo = {"prodotti": "prodotto_id", "negozi": "negozio_id"}[tabella]
    for t_ in ("rilevazioni", "acquisti", "liste_righe", "scontrini"):
        for x in ss[t_]:
            if x.get(campo) == togli_id:
                x[campo] = tieni_id
    if tabella == "prodotti":
        al = list(tieni.get("alias") or [])
        for n in [togli.get("nome", "")] + list(togli.get("alias") or []):
            if n and n not in al and ss_norm(n) != ss_norm(tieni.get("nome")):
                al.append(n)
        tieni["alias"] = al
        for k, v in togli.items():
            if v not in (None, "", []) and tieni.get(k) in (None, "", []):
                tieni[k] = v
    ss[tabella] = [x for x in ss[tabella] if x.get("id") != togli_id]
    return True


def ss_elimina(ss, tabella, id_):
    """Cancella solo se non è usato (altrimenti si unisce). True se cancellato."""
    if tabella in ("prodotti", "negozi") and ss_riferimenti(ss, tabella, id_):
        return False
    n = len(ss[tabella])
    ss[tabella] = [x for x in ss[tabella] if x.get("id") != id_]
    if tabella == "liste":
        ss["liste_righe"] = [x for x in ss["liste_righe"] if x.get("lista_id") != id_]
    return len(ss[tabella]) < n


# =====================================================================================================================
# 5. NEGOZI
# =====================================================================================================================
def ss_nome_negozio(n):
    if not n:
        return "?"
    pezzi = [n.get("nome") or n.get("catena") or "Negozio"]
    if n.get("citta"):
        pezzi.append(n["citta"])
    if n.get("indirizzo"):
        pezzi.append(n["indirizzo"])
    return " · ".join(pezzi)


def ss_aggiungi_negozio(ss, n):
    n = {k: (v.strip() if isinstance(v, str) else v) for k, v in n.items()}
    if not ss_norm(n.get("nome")):
        raise ValueError("Scrivi il nome del negozio.")
    firma = (ss_norm(n.get("nome")), ss_norm(n.get("citta")), ss_norm(n.get("indirizzo")))
    for x in ss["negozi"]:
        if (ss_norm(x.get("nome")), ss_norm(x.get("citta")), ss_norm(x.get("indirizzo"))) == firma:
            return x, False
    n.setdefault("catena", n.get("nome"))
    n["id"], n["creato_il"] = ss_id(), ss_ora()
    ss["negozi"].append(n)
    return n, True


def ss_trova_negozio_da_testo(ss, nome, citta="", indirizzo=""):
    nn = ss_norm(nome)
    if not nn:
        return None
    cand = [x for x in ss["negozi"] if ss_norm(x.get("nome")) == nn or (ss_norm(x.get("catena")) and ss_norm(x.get("catena")) in nn) or (nn in ss_norm(x.get("nome")))]
    if citta:
        cand = [x for x in cand if not x.get("citta") or ss_norm(x.get("citta")) == ss_norm(citta)] or cand
    if indirizzo and len(cand) > 1:
        cand = [x for x in cand if ss_parole(indirizzo) & ss_parole(x.get("indirizzo"))] or cand
    return cand[0] if cand else None


# =====================================================================================================================
# 6. RILEVAZIONI DI PREZZO E VALIDITÀ
# =====================================================================================================================
def ss_valida_rilevazione(r, oggi_=None):
    oggi_ = oggi_ or ss_oggi()
    err = []
    p, pp = ss_num(r.get("prezzo")), ss_num(r.get("prezzo_promo"))
    if (p is None or p <= 0) and (pp is None or pp <= 0):
        err.append("Scrivi il prezzo.")
    if p is not None and p > 5000:
        err.append("Il prezzo sembra troppo alto: controlla la virgola.")
    if p and pp and pp >= p:
        err.append("Il prezzo in offerta deve essere più basso del prezzo normale.")
    if not r.get("prodotto_id"):
        err.append("Scegli il prodotto.")
    if not r.get("negozio_id"):
        err.append("Scegli il negozio.")
    d1, d2, dr = ss_data(r.get("promo_dal")), ss_data(r.get("promo_al")), ss_data(r.get("data"))
    if d1 and d2 and d2 < d1:
        err.append("La fine dell'offerta è prima dell'inizio.")
    if dr and dr > oggi_ + _ss_td(days=1):
        err.append("La data della rilevazione è nel futuro.")
    return err


def ss_nuova_rilevazione(ss, prodotto_id, negozio_id, prezzo=None, prezzo_promo=None, confezioni=None, formato_valore=None, formato_unita=None, data=None,
                         promo_dal=None, promo_al=None, tessera=False, note="", fonte="manuale", oggi_=None):
    """Crea la rilevazione con il prezzo unitario già calcolato. Ritorna (rilevazione, errori)."""
    prod = ss_trova(ss, "prodotti", prodotto_id) or {}
    conf = ss_num(confezioni, None) or ss_num(prod.get("confezioni"), 1) or 1
    fv = ss_num(formato_valore, None) if formato_valore not in (None, "") else ss_num(prod.get("formato_valore"))
    fu = (formato_unita or prod.get("formato_unita") or "").strip()
    r = {"id": ss_id(), "prodotto_id": prodotto_id, "negozio_id": negozio_id, "prezzo": ss_num(prezzo), "prezzo_promo": ss_num(prezzo_promo),
         "confezioni": conf, "formato_valore": fv, "formato_unita": fu, "data": str(data or (oggi_ or ss_oggi()).isoformat())[:10],
         "promo_dal": str(promo_dal)[:10] if promo_dal else "", "promo_al": str(promo_al)[:10] if promo_al else "", "tessera": bool(tessera),
         "note": str(note or "").strip(), "fonte": fonte if fonte in SS_FONTI else "manuale", "da_verificare": False, "creato_il": ss_ora()}
    err = ss_valida_rilevazione(r, oggi_)
    if err:
        return None, err
    pu, base = ss_prezzo_unitario(r["prezzo_promo"] or r["prezzo"], conf, fv, fu)
    r["prezzo_unitario"], r["unita_base"] = pu, base
    if r["prezzo"]:
        r["prezzo_unitario_pieno"] = ss_prezzo_unitario(r["prezzo"], conf, fv, fu)[0]
    ss["rilevazioni"].append(r)
    return r, []


def ss_stato(r, oggi_=None):
    """(stato, prezzo effettivo oggi, è un'offerta in corso?)  stato: attiva | da verificare | scaduta | futura."""
    oggi_ = oggi_ or ss_oggi()
    p, pp = ss_num(r.get("prezzo")), ss_num(r.get("prezzo_promo"))
    d = ss_data(r.get("data")) or oggi_
    d1, d2 = ss_data(r.get("promo_dal")), ss_data(r.get("promo_al"))
    promo_ok = bool(pp) and (not d1 or d1 <= oggi_) and (not d2 or d2 >= oggi_)
    if pp and not d2 and promo_ok:                                       # offerta senza data di fine: vale come un prezzo normale (scade col tempo)
        promo_ok = (oggi_ - d).days <= SS_FRESCO
    if promo_ok:
        return ("da verificare" if r.get("da_verificare") else "attiva"), pp, True
    prezzo_ora = p                                                       # offerta finita o non ancora iniziata: vale solo il prezzo normale (se c'è)
    if not prezzo_ora:
        return "scaduta", None, False
    eta = (oggi_ - d).days
    if eta > SS_VECCHIO:
        return "scaduta", prezzo_ora, False
    if r.get("da_verificare") or eta > SS_FRESCO:
        return "da verificare", prezzo_ora, False
    return "attiva", prezzo_ora, False


def ss_unitario_oggi(r, prezzo):
    return ss_prezzo_unitario(prezzo, r.get("confezioni"), r.get("formato_valore"), r.get("formato_unita"))


def ss_prezzi_correnti(ss, prodotto_id, oggi_=None, anche_da_verificare=False):
    """Per ogni negozio l'ULTIMA rilevazione valida del prodotto: [{negozio_id, rilevazione, stato, prezzo, unitario, base, offerta}] dal più conveniente."""
    oggi_ = oggi_ or ss_oggi()
    per_neg = {}
    for r in ss["rilevazioni"]:
        if r.get("prodotto_id") != prodotto_id:
            continue
        stato, prezzo, offerta = ss_stato(r, oggi_)
        if stato == "scaduta" or prezzo is None or (stato == "da verificare" and not anche_da_verificare):
            continue
        chiave = (r.get("data") or "", 1 if offerta else 0, r.get("creato_il") or "")
        att = per_neg.get(r.get("negozio_id"))
        if att is None or chiave > att["_k"]:
            pu, base = ss_unitario_oggi(r, prezzo)
            per_neg[r.get("negozio_id")] = {"_k": chiave, "negozio_id": r.get("negozio_id"), "rilevazione": r, "stato": stato, "prezzo": prezzo,
                                            "unitario": pu, "base": base, "offerta": offerta}
    righe = list(per_neg.values())
    basi = {x["base"] for x in righe}
    confrontabili = len(basi) <= 1
    righe.sort(key=lambda x: (x["unitario"] if confrontabili and x["unitario"] is not None else x["prezzo"]))
    for x in righe:
        x.pop("_k", None)
        x["confrontabile"] = confrontabili
    return righe


def ss_storico(ss, prodotto_id):
    return sorted((r for r in ss["rilevazioni"] if r.get("prodotto_id") == prodotto_id), key=lambda r: (r.get("data") or "", r.get("creato_il") or ""))


def ss_mediana(valori):
    v = sorted(x for x in valori if x is not None)
    if not v:
        return None
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


# =====================================================================================================================
# 7. DOVE COSTA MENO
# =====================================================================================================================
def ss_dove_costa_meno(ss, oggi_=None, ordine="prezzo crescente", filtro=""):
    """Una riga per prodotto con almeno un prezzo valido oggi."""
    oggi_ = oggi_ or ss_oggi()
    out = []
    f = ss_parole(filtro)
    for p in ss["prodotti"]:
        if f and not (f & ss_parole(p.get("nome", "") + " " + p.get("marca", "") + " " + p.get("categoria", ""))):
            continue
        cor = ss_prezzi_correnti(ss, p["id"], oggi_)
        if not cor:
            continue
        migl, peggio = cor[0], cor[-1]
        val = (lambda x: x["unitario"] if x["confrontabile"] and x["unitario"] is not None else x["prezzo"])
        risp = (1 - val(migl) / val(peggio)) * 100 if len(cor) > 1 and val(peggio) else 0.0
        ultima = max((x["rilevazione"].get("data") or "") for x in cor)
        out.append({"prodotto": p, "migliore": migl, "classifica": cor, "risparmio_pct": round(risp, 1), "ultima": ultima})
    if ordine == "prezzo decrescente":
        out.sort(key=lambda x: -(x["migliore"]["prezzo"] or 0))
    elif ordine == "percentuale di risparmio":
        out.sort(key=lambda x: -x["risparmio_pct"])
    elif ordine == "data dell'ultima rilevazione":
        out.sort(key=lambda x: x["ultima"], reverse=True)
    else:
        out.sort(key=lambda x: x["migliore"]["prezzo"] or 0)
    return out


# =====================================================================================================================
# 8. OFFERTE INTERESSANTI E SUGGERIMENTI
# =====================================================================================================================
def ss_offerte_interessanti(ss, oggi_=None, prodotti_ids=None):
    """Prezzi validi OGGI davvero convenienti: offerta in corso con sconto, o almeno 10% sotto il solito prezzo (mediana dello storico).
    Punteggio = risparmio % × freschezza (1 entro 7 giorni, 0,8 entro 14, 0,6 entro 30)."""
    oggi_ = oggi_ or ss_oggi()
    out = []
    for p in ss["prodotti"]:
        if prodotti_ids is not None and p["id"] not in prodotti_ids:
            continue
        storico = ss_storico(ss, p["id"])
        if not storico:
            continue
        cor = ss_prezzi_correnti(ss, p["id"], oggi_)
        if not cor:
            continue
        basi = {r.get("unita_base") for r in storico}
        solito = ss_mediana([(r.get("prezzo_unitario_pieno") or r.get("prezzo_unitario")) if len(basi) == 1 else r.get("prezzo") for r in storico])
        for c in cor:
            r = c["rilevazione"]
            v = c["unitario"] if len(basi) == 1 else c["prezzo"]
            sconto_promo = (1 - c["prezzo"] / r["prezzo"]) * 100 if c["offerta"] and r.get("prezzo") else 0.0
            sotto = (1 - v / solito) * 100 if solito and v else 0.0
            risp = max(sconto_promo, sotto)
            if risp < (5 if c["offerta"] else 10):
                continue
            eta = (oggi_ - (ss_data(r.get("data")) or oggi_)).days
            fres = 1.0 if eta <= 7 else 0.8 if eta <= 14 else 0.6
            out.append({"prodotto": p, "corrente": c, "risparmio_pct": round(risp, 1), "punteggio": round(risp * fres, 1), "eta": eta,
                        "fine": r.get("promo_al") if c["offerta"] else ""})
    out.sort(key=lambda x: -x["punteggio"])
    return out


def ss_suggerimenti(ss, d_disp=None, oggi_=None):
    """{frequenti, in_esaurimento, convenienti, aumenti, pagati_di_piu}."""
    oggi_ = oggi_ or ss_oggi()
    s = {"frequenti": [], "in_esaurimento": [], "convenienti": [], "aumenti": [], "pagati_di_piu": []}
    da = (oggi_ - _ss_td(days=90)).isoformat()
    cont = {}
    for a in ss["acquisti"]:
        if (a.get("data") or "") >= da:
            cont[a.get("prodotto_id")] = cont.get(a.get("prodotto_id"), 0) + 1
    for pid, n in sorted(cont.items(), key=lambda x: -x[1]):
        p = ss_trova(ss, "prodotti", pid)
        if p and n >= 3:
            s["frequenti"].append((p, n))
    if d_disp:
        visti = set()
        for r in (d_disp.get("spesa") or []):
            if not r.get("preso") and ss_chiave_disp(r) not in visti:
                visti.add(ss_chiave_disp(r))
                s["in_esaurimento"].append(r.get("nome", ""))
        for a in (d_disp.get("articoli") or []):
            if 0 < (ss_num(a.get("quantita"), 0) or 0) <= 1 and ss_chiave_disp(a) not in visti:
                visti.add(ss_chiave_disp(a))
                s["in_esaurimento"].append(a.get("nome", "") + " (ne resta 1)")
    s["convenienti"] = ss_offerte_interessanti(ss, oggi_)[:8]
    for p in ss["prodotti"]:
        acq = sorted((a for a in ss["acquisti"] if a.get("prodotto_id") == p["id"] and ss_num(a.get("prezzo_pagato"))),
                     key=lambda a: (a.get("data") or "", a.get("creato_il") or ""))
        if len(acq) >= 2:
            u = lambda a: (ss_num(a["prezzo_pagato"]) / max(ss_num(a.get("quantita"), 1) or 1, 0.001))
            ult, prima = u(acq[-1]), u(acq[-2])
            if prima and abs(ult - prima) / prima >= 0.05:
                s["aumenti"].append((p, prima, ult))
            minimo = min(u(a) for a in acq[:-1])
            if minimo and ult > minimo * 1.10:
                s["pagati_di_piu"].append((p, minimo, ult))
    return s


# =====================================================================================================================
# 9. LISTA OTTIMIZZATA: tre scenari
# =====================================================================================================================
def ss_ottimizza(ss, righe, oggi_=None, costo_negozio=0.0, max_negozi=3):
    """righe = [{prodotto_id, quantita, nome}]. Ritorna {A, B, C, mancano, consiglio, completo} con per ogni scenario:
    {negozi:[id], assegna:[{riga, negozio_id, prezzo, totale}], totale, spostamenti, n_negozi, coperti, scoperti}."""
    oggi_ = oggi_ or ss_oggi()
    prezzi = {}
    for rg in righe:
        pid = rg.get("prodotto_id")
        if pid and pid not in prezzi:
            prezzi[pid] = {c["negozio_id"]: c["prezzo"] for c in ss_prezzi_correnti(ss, pid, oggi_)}
    mancano = [rg for rg in righe if not prezzi.get(rg.get("prodotto_id"))]
    con_prezzo = [rg for rg in righe if prezzi.get(rg.get("prodotto_id"))]
    negozi = sorted({n for v in prezzi.values() for n in v})
    costo = max(ss_num(costo_negozio, 0) or 0, 0.0)

    def _scenario(insieme):
        assegna, scoperti = [], []
        for rg in con_prezzo:
            opz = [(prezzi[rg["prodotto_id"]][n], n) for n in insieme if n in prezzi[rg["prodotto_id"]]]
            if not opz:
                scoperti.append(rg)
                continue
            pr, n = min(opz)
            q = ss_num(rg.get("quantita"), 1) or 1
            assegna.append({"riga": rg, "negozio_id": n, "prezzo": pr, "totale": round(pr * q, 2)})
        usati = sorted({a["negozio_id"] for a in assegna})
        spesa = round(sum(a["totale"] for a in assegna), 2)
        spost = round(costo * max(len(usati) - 1, 0), 2)
        return {"negozi": usati, "assegna": assegna, "spesa": spesa, "spostamenti": spost, "totale": round(spesa + spost, 2),
                "n_negozi": len(usati), "coperti": len(assegna), "scoperti": scoperti}

    if not negozi:
        vuoto = {"negozi": [], "assegna": [], "spesa": 0.0, "spostamenti": 0.0, "totale": 0.0, "n_negozi": 0, "coperti": 0, "scoperti": []}
        return {"A": vuoto, "B": None, "C": vuoto, "mancano": mancano, "consiglio": "A", "completo": not righe, "negozi": []}
    # A: un solo negozio (prima chi ha più prodotti, poi il totale più basso)
    sing = [_scenario([n]) for n in negozi]
    A = min(sing, key=lambda s: (-s["coperti"], s["totale"]))
    # C: ogni prodotto dove costa meno (tutti i negozi necessari)
    C = _scenario(negozi)
    # B: la migliore combinazione di 2..max_negozi negozi che copre almeno quanto A
    B = None
    for k in range(2, min(max_negozi, len(negozi)) + 1):
        for comb in _ss_it.combinations(negozi, k):
            s = _scenario(list(comb))
            if s["n_negozi"] < 2 or s["coperti"] < A["coperti"]:
                continue
            if B is None or (-s["coperti"], s["totale"]) < (-B["coperti"], B["totale"]):
                B = s
    for s in (A, B, C):
        if s:
            s["scoperti_tot"] = len(s["scoperti"]) + len(mancano)

    def _vale(s, rif):                                                    # vale la pena girare più negozi?
        if not s or s["n_negozi"] <= rif["n_negozi"]:
            return False
        if s["coperti"] > rif["coperti"]:
            return True
        risp = rif["totale"] - s["totale"]
        return risp >= SS_SOGLIA_EURO and (rif["totale"] and risp / rif["totale"] * 100 >= SS_SOGLIA_PCT)
    consiglio = "A"
    if _vale(B, A):
        consiglio = "B"
    if _vale(C, A if consiglio == "A" else B):
        consiglio = "C"
    if C and B and C["negozi"] == B["negozi"]:
        consiglio = "B" if consiglio == "C" else consiglio
    return {"A": A, "B": B, "C": C, "mancano": mancano, "consiglio": consiglio, "completo": not mancano and not any(s and s["scoperti"] for s in (A,)),
            "negozi": negozi}


# =====================================================================================================================
# 10. ACQUISTI, SCONTRINI E DISPENSA
# =====================================================================================================================
def ss_registra_acquisto(ss, prodotto_id, negozio_id, quantita, prezzo_pagato, data=None, scontrino_id="", con_rilevazione=True, prezzo_unitario=None, sconto=0.0,
                         oggi_=None):
    """Acquisto + (di solito) la rilevazione del prezzo (fonte «acquisto»/«scontrino»). Ritorna l'acquisto."""
    q = ss_num(quantita, 1) or 1
    pp = ss_num(prezzo_pagato)
    if pp is None or pp < 0:
        raise ValueError("prezzo pagato mancante")
    a = {"id": ss_id(), "prodotto_id": prodotto_id, "negozio_id": negozio_id, "quantita": q, "prezzo_pagato": round(pp, 2),
         "data": str(data or (oggi_ or ss_oggi()).isoformat())[:10], "scontrino_id": scontrino_id or "", "rilevazione_id": "", "creato_il": ss_ora()}
    if con_rilevazione and pp > 0:
        pu = ss_num(prezzo_unitario) or round(pp / q, 2)
        sc = ss_num(sconto, 0) or 0
        pieno = round(pu + sc / q, 2) if sc > 0 else pu
        r, err = ss_nuova_rilevazione(ss, prodotto_id, negozio_id, prezzo=pieno, prezzo_promo=(pu if sc > 0 and pu < pieno else None), data=a["data"],
                                      promo_dal=(a["data"] if sc > 0 else None), promo_al=(a["data"] if sc > 0 else None),
                                      fonte=("scontrino" if scontrino_id else "acquisto"), oggi_=oggi_)
        if r:
            a["rilevazione_id"] = r["id"]
    ss["acquisti"].append(a)
    return a


def ss_articolo_da_prodotto(p, quantita, scadenza=None, posto="dispensa", utente=""):
    """Il nuovo articolo della Dispensa (stessi campi di spesa.py)."""
    fu = p.get("formato_unita") or None
    return {"id": ss_id(), "barcode": p.get("ean", "") or "", "nome": p.get("nome", ""), "marca": p.get("marca", ""),
            "formato_valore": ss_num(p.get("formato_valore")), "formato_unita": ("L" if fu == "l" else fu), "immagine": p.get("immagine", "") or "",
            "allergeni": [], "tracce": [], "senza_glutine": False, "allergeni_noti": False, "ingredienti": "", "note": "", "categoria": p.get("categoria", "") or "",
            "extra": {}, "per_chi": "adulti", "posto": posto or "dispensa", "posto_altro": "", "aggiunto_da": utente, "aggiunto_il": ss_ora(),
            "acquisto": ss_oggi().isoformat(), "quantita": float(ss_num(quantita, 1) or 1), "scadenza": scadenza or None, "da_spesa_smart": True}


def ss_metti_in_dispensa(d_disp, voci, utente=""):
    """voci = [{prodotto, quantita, scadenza, posto}] → articoli nuovi; i prodotti tornati in dispensa escono dalla lista della spesa. Ritorna quanti."""
    n = 0
    for v in voci:
        q = ss_num(v.get("quantita"), 0) or 0
        if q <= 0:
            continue
        a = ss_articolo_da_prodotto(v["prodotto"], q, v.get("scadenza"), v.get("posto"), utente)
        d_disp.setdefault("articoli", []).append(a)
        n += 1
        ch = ss_chiave_disp(a)
        nn = ss_norm(a.get("nome"))
        d_disp["spesa"] = [x for x in d_disp.get("spesa", []) if not (not x.get("preso") and (ss_chiave_disp(x) == ch or ss_norm(x.get("nome")) == nn))]
    return n


# =====================================================================================================================
# 11. ESAURITI CON OFFERTA (il badge sul pulsante) — calcolato ogni volta dallo stato: niente notifiche doppie
# =====================================================================================================================
def ss_esauriti_con_offerta(ss, d_disp, oggi_=None, offerte_volantini=None):
    """[(nome, testo)] una volta per prodotto: le righe da comprare della lista della Dispensa che hanno un'offerta valida oggi
    (prezzo di Spesa Smart conveniente oppure offerta dei volantini ancora valida)."""
    oggi_ = oggi_ or ss_oggi()
    out, visti = [], set()
    righe = [r for r in (d_disp or {}).get("spesa", []) if isinstance(r, dict) and not r.get("preso")]
    for r in righe:
        ch = ss_chiave_disp(r)
        if not ch or ch in visti:
            continue
        p = ss_prodotto_per_riga_disp(ss, r)
        testo = ""
        if p:
            off = ss_offerte_interessanti(ss, oggi_, {p["id"]})
            if off:
                o = off[0]
                n = ss_trova(ss, "negozi", o["corrente"]["negozio_id"])
                testo = f"{ss_euro(o['corrente']['prezzo'])} da {ss_nome_negozio(n)} (−{o['risparmio_pct']:.0f}%)"
        if not testo and offerte_volantini and "trova_corrispondenze" in globals():
            try:
                valide = [o for o in offerte_volantini if (not o.get("al") or (ss_data(o.get("al")) or oggi_) >= oggi_) and (not o.get("dal") or (ss_data(o.get("dal")) or oggi_) <= oggi_)]
                m = trova_corrispondenze(r, valide)
                if m:
                    testo = f"{ss_euro(m[0].get('prezzo'))} da {m[0].get('negozio', '')} (volantino" + (f", fino al {ss_data_it(m[0].get('al'))}" if m[0].get("al") else "") + ")"
            except Exception:
                testo = ""
        if testo:
            visti.add(ch)
            out.append((r.get("nome", ""), testo))
    return out


# =====================================================================================================================
# 11-bis. LISTE CONDIVISE CON PERSONE SCELTE (file comune famiglia/liste_spesa.json)
#   {liste: [{id, nome, proprietario, persone[uid], creata_il, stato, righe: [{id, nome, marca, ean, formato_valore, formato_unita,
#             quantita, priorita, stato, aggiunto_da, preso_da, preso_il}]}]}
#   Le vede e le modifica SOLO chi le ha create e le persone scelte; le liste private restano nel file personale.
# =====================================================================================================================
SS_LC = "famiglia/liste_spesa.json"


def ss_lc_mie(dati, uid):
    return [l for l in (dati or {}).get("liste") or [] if isinstance(l, dict) and l.get("stato") != "chiusa"
            and (l.get("proprietario") == uid or uid in (l.get("persone") or []))]


def ss_lc_puo(lista, uid):
    return bool(lista) and (lista.get("proprietario") == uid or uid in (lista.get("persone") or []))


def ss_lc_nuova(dati, nome, proprietario, persone):
    nome = str(nome or "").strip()
    if not nome:
        raise ValueError("Scrivi il nome della lista.")
    l = {"id": ss_id(), "nome": nome, "proprietario": proprietario, "persone": [p for p in dict.fromkeys(persone or []) if p and p != proprietario],
         "creata_il": ss_ora(), "stato": "aperta", "righe": []}
    dati.setdefault("liste", []).append(l)
    dati["versione"] = int(dati.get("versione") or 0) + 1
    return l


def ss_lc_aggiungi(lista, p, quantita, chi):
    """Aggiunge il prodotto; se c'è già da comprare (stesso codice o stesso nome e marca) somma la quantità: niente doppioni. Ritorna (riga, nuova?)."""
    ean, nn, mm = str(p.get("ean") or p.get("barcode") or "").strip(), ss_norm(p.get("nome")), ss_norm(p.get("marca"))
    q = ss_num(quantita, 1) or 1
    for r in lista.setdefault("righe", []):
        if r.get("stato") == "preso":
            continue
        if (ean and str(r.get("ean") or "") == ean) or (ss_norm(r.get("nome")) == nn and (not mm or not r.get("marca") or ss_norm(r.get("marca")) == mm)):
            r["quantita"] = (ss_num(r.get("quantita"), 1) or 1) + q
            return r, False
    r = {"id": ss_id(), "nome": p.get("nome", ""), "marca": p.get("marca", ""), "ean": ean, "formato_valore": p.get("formato_valore"),
         "formato_unita": p.get("formato_unita") or "", "quantita": q, "priorita": "Normale", "stato": "da comprare", "aggiunto_da": chi, "preso_da": "", "preso_il": ""}
    lista["righe"].append(r)
    return r, True


def ss_lc_applica(lista, cambi, chi):
    """cambi = {riga_id: {preso?, quantita?, priorita?, togli?}} — solo quello che QUESTA persona ha cambiato (le modifiche degli altri restano)."""
    nuove = []
    for r in lista.get("righe") or []:
        c = cambi.get(r.get("id"))
        if c:
            if c.get("togli"):
                continue
            if "preso" in c:
                if c["preso"] and r.get("stato") != "preso":
                    r.update(stato="preso", preso_da=chi, preso_il=ss_ora())
                elif not c["preso"] and r.get("stato") == "preso":
                    r.update(stato="da comprare", preso_da="", preso_il="")
            if "quantita" in c:
                r["quantita"] = max(ss_num(c["quantita"], 1) or 1, 1)
            if "priorita" in c and c["priorita"] in ("Alta", "Normale", "Bassa"):
                r["priorita"] = c["priorita"]
        nuove.append(r)
    lista["righe"] = nuove


# =====================================================================================================================
# 12. LETTURA DELLO SCONTRINO (IA con la foto; si conferma SEMPRE prima di salvare)
# =====================================================================================================================
SS_ISTR_SCONTRINO = ("Leggi lo SCONTRINO italiano nella foto e rispondi SOLO con JSON: "
                     '{"negozio": "nome del negozio/insegna", "citta": "", "indirizzo": "", "data": "AAAA-MM-GG", "totale": numero, '
                     '"righe": [{"descrizione": "come scritta", "quantita": numero, "prezzo_unitario": numero, "prezzo_totale": numero, "sconto": numero}]}. '
                     "Una riga per prodotto. Gli sconti scritti sotto un prodotto (SCONTO, -0,50, OFFERTA) vanno nel campo «sconto» di quel prodotto come numero positivo, "
                     "non come riga a parte. Righe come SUBTOTALE, TOTALE, CONTANTE, RESTO, IVA, PAGAMENTO, BUONI, PUNTI non sono prodotti. "
                     "Se c'è «2 x 1,20» la quantità è 2 e il prezzo unitario 1,20. Usa il punto per i decimali. Non inventare: se un valore non si legge lascia null.")


def ss_leggi_scontrino(files):
    """{negozio, citta, indirizzo, data, totale, righe:[…], fonte} oppure {} se non si legge."""
    import json as _j
    import os as _o
    if _o.environ.get("VM_SS_SCONTRINO_FINTO"):
        r = _j.loads(_o.environ["VM_SS_SCONTRINO_FINTO"])
        r["fonte"] = "groq"
        return r
    if "il_disponibili" not in globals() or not il_disponibili(IL_ORDINE_VISTA):
        return {}
    imgs = []
    for f in files[:3]:
        try:
            imgs += il_immagini(f.name, f.type or "", f.getvalue(), max_pagine=2, lato=2000)
        except Exception:
            pass
    if not imgs:
        return {}
    for prov in il_disponibili(IL_ORDINE_VISTA):
        r, _err = il_chiama(prov, SS_ISTR_SCONTRINO, "Ecco lo scontrino.", imgs[:4], max_tokens=4000)
        j = il_json(r)
        if isinstance(j, dict) and isinstance(j.get("righe"), list) and j["righe"]:
            j["fonte"] = prov
            return j
    return {}


def ss_pulisci_scontrino(letto):
    """Righe pulite: tolte quelle che non sono prodotti; numeri controllati; segnate quelle incerte."""
    no = ("totale", "subtotale", "contante", "resto", "iva", "pagamento", "bancomat", "carta", "buono", "punti", "arrotond", "sconto totale", "di cui")
    out = []
    for r in letto.get("righe") or []:
        if not isinstance(r, dict):
            continue
        desc = str(r.get("descrizione") or "").strip()
        if not desc or any(desc.lower().startswith(x) for x in no):
            continue
        q = ss_num(r.get("quantita"), 1) or 1
        pu, pt, sc = ss_num(r.get("prezzo_unitario")), ss_num(r.get("prezzo_totale")), abs(ss_num(r.get("sconto"), 0) or 0)
        if pt is None and pu is not None:
            pt = round(pu * q, 2)
        if pu is None and pt is not None:
            pu = round(pt / q, 2)
        incerta = pt is None or pt <= 0 or pt > 500 or (pu and abs(pu * q - pt) > 0.05 and not sc)
        out.append({"descrizione": desc, "quantita": q, "prezzo_unitario": pu, "prezzo_totale": pt, "sconto": sc, "incerta": bool(incerta)})
    return out


# =====================================================================================================================
# 13. INTERFACCIA
# =====================================================================================================================
SS_COLORI = ("#00e6a8", "#00574b")
_SS_VISTE = [("dash", "🏠 Riepilogo"), ("ins", "⚡ Inserisci un prezzo"), ("dcm", "🏆 Dove costa meno"), ("lista", "📝 Lista della spesa"),
             ("ott", "🧮 Lista ottimizzata"), ("off", "🔥 Offerte interessanti"), ("scon", "🧾 Scontrino"), ("sto", "📈 Storico prezzi"),
             ("prod", "📦 Archivio prodotti"), ("neg", "🏪 Archivio negozi")]
_SS_CSS = """<style>
.ss-hero{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,#02130f 0%,#00574b 55%,#00e6a8 140%);color:#fff;padding:16px 18px;border-radius:22px;
 margin:6px 0 10px;border:2px solid rgba(0,230,168,.7);box-shadow:0 0 18px rgba(0,230,168,.35)}
.ss-hero .ico{font-size:2.6rem;line-height:1}.ss-hero h1{margin:0;font-size:1.55rem;color:#fff}.ss-hero p{margin:2px 0 0;font-size:.92rem;opacity:.95}
.st-key-ss_hub[data-testid='stVerticalBlock'],.st-key-ss_hub [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:6px 0 12px}
.st-key-ss_hub button{width:100% !important;min-height:56px !important;border-radius:18px !important;color:#fff !important;background:linear-gradient(135deg,#0b2a24,#00574b) !important;
 border:2px solid rgba(0,230,168,.65) !important;box-shadow:0 0 10px rgba(0,230,168,.25),0 4px 0 rgba(0,0,0,.25) !important}
.st-key-ss_hub button p{color:#fff !important;font-weight:900 !important;font-size:.95rem !important;line-height:1.12 !important;margin:0}
.st-key-ss_hub [class*='st-key-ss_hon_'] button{background:linear-gradient(135deg,#00e6a8,#00574b) !important;outline:3px solid #fff !important;outline-offset:-5px}
.ss-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:6px 0 10px}
.ss-tile{background:rgba(10,30,26,.92);border:1px solid rgba(0,230,168,.45);border-radius:16px;padding:10px 12px;color:#e8fff8}
.ss-tile b{display:block;font-size:1.45rem;color:#00e6a8;line-height:1.1}.ss-tile span{font-size:.82rem;opacity:.9}
.ss-card{background:rgba(255,255,255,.95);color:#0d2621;border-radius:16px;padding:10px 12px;margin:8px 0;border-left:6px solid #00a37a;overflow-wrap:anywhere}
.ss-card .t{font-weight:900;font-size:1.02rem}.ss-card .m{font-size:.85rem;color:#35514a}.ss-card .big{font-size:1.35rem;font-weight:900;color:#00704f}
.ss-card .u{font-size:.85rem;color:#00704f;font-weight:700}.ss-card img{float:right;width:54px;height:54px;object-fit:contain;margin-left:8px;border-radius:8px;background:#fff}
.ss-card ol{margin:4px 0 0 18px;padding:0;font-size:.88rem}.ss-card li{margin:1px 0}
.ss-promo{display:inline-block;background:#ff3d71;color:#fff;font-weight:900;border-radius:10px;padding:1px 8px;font-size:.8rem;margin-left:4px}
.ss-ver{display:inline-block;background:#ffb300;color:#3a2600;font-weight:800;border-radius:10px;padding:1px 8px;font-size:.78rem}
.ss-scen{border-radius:18px;padding:12px 14px;margin:10px 0;background:rgba(10,30,26,.94);color:#e8fff8;border:2px solid rgba(0,230,168,.35)}
.ss-scen.ok{border-color:#00e6a8;box-shadow:0 0 16px rgba(0,230,168,.45)}.ss-scen h4{margin:0 0 4px;color:#fff}.ss-scen .tot{font-size:1.4rem;font-weight:900;color:#00e6a8}
.ss-scen .neg{margin-top:6px;font-weight:800;color:#b9fbe7}.ss-scen .r{margin-left:10px;font-size:.9rem}
.st-key-ss_switch[data-testid='stHorizontalBlock'],.st-key-ss_switch [data-testid='stHorizontalBlock']{gap:8px !important}
.st-key-ss_switch button{min-height:48px !important;border-radius:999px !important;font-weight:900 !important}
[class*='st-key-ss_sw_scorte'] button{background:linear-gradient(135deg,#2ec4a6,#00695c) !important;color:#fff !important;border:2px solid rgba(255,255,255,.5) !important}
[class*='st-key-ss_sw_smart'] button{background:linear-gradient(135deg,#00e6a8,#00574b) !important;color:#fff !important;border:2px solid rgba(0,230,168,.9) !important;box-shadow:0 0 12px rgba(0,230,168,.55) !important}
[class*='st-key-ss_sw_'] button p{color:#fff !important;font-weight:900 !important}
[class*='_on'][class*='st-key-ss_sw_'] button{outline:3px solid #fff !important;outline-offset:-5px}
.st-key-vm_ss button{width:100% !important;min-height:54px !important;border-radius:999px !important;background:linear-gradient(135deg,#02130f,#00574b 60%,#00e6a8) !important;
 border:2px solid #00e6a8 !important;box-shadow:0 0 14px rgba(0,230,168,.6) !important}
.st-key-vm_ss{max-width:460px;margin:0 auto 6px}.st-key-vm_ss button p{color:#fff !important;font-weight:900 !important;font-size:1.05rem !important}
</style>"""


def _ss_utente():
    return str((st.session_state.get("sess") or {}).get("nome") or "")


def _ss_leggi():
    """(ss, dati della dispensa aperta). ss è una COPIA: si modifica solo dentro _ss_salva."""
    import copy as _c
    try:
        d = carica_dati(crea_archivio(), percorso_mio())
    except Exception:
        d = {}
    ss = ss_migra(_c.deepcopy({"spesa_smart": d.get("spesa_smart") or {}}))
    try:
        disp = carica_dati(crea_archivio(), st.session_state.get("percorso") or percorso_mio())
    except Exception:
        disp = {}
    return ss, disp


def _ss_salva(fn, msg):
    """fn(ss) dentro il file personale (sempre con la migrazione prima)."""
    salva_file(percorso_mio(), lambda d: fn(ss_migra(d)), "Spesa Smart: " + msg)


def _ss_salva_disp(fn, msg):
    salva(fn, "Spesa Smart → Dispensa: " + msg)


def _ss_vai(v):
    st.session_state["ss_vista"] = v


def _ss_etich_prodotto(p):
    pezzi = [p.get("nome") or "?"]
    if p.get("marca"):
        pezzi.append(p["marca"])
    if p.get("variante"):
        pezzi.append(p["variante"])
    f = ss_fmt_formato(p)
    if f:
        pezzi.append(f)
    return " · ".join(pezzi) + ("  (dalla Dispensa)" if p.get("_virtuale") else "")


def ss_switch(corrente):
    """📦 Scorte | 🛒 Spesa Smart: le due parti della Dispensa."""
    st.markdown(_SS_CSS, unsafe_allow_html=True)
    avv = st.session_state.pop("ss_avviso", None)
    if avv:
        st.info(avv + " Lo trovi in 🛒 Spesa Smart → 🔥 Offerte interessanti.")
    with st.container(key="ss_switch", horizontal=True):
        with st.container(key="ss_sw_scorte" + ("_on" if corrente == "dispensa" else "")):
            st.button(("● " if corrente == "dispensa" else "") + "📦 Scorte", key="ss_vai_scorte", width="stretch",
                      on_click=(None if corrente == "dispensa" else nav_vai), args=(None if corrente == "dispensa" else ("dispensa",)))
        with st.container(key="ss_sw_smart" + ("_on" if corrente == "spesa_smart" else "")):
            st.button(("● " if corrente == "spesa_smart" else "") + "🛒 Spesa Smart", key="ss_vai_smart", width="stretch",
                      on_click=(None if corrente == "spesa_smart" else nav_vai), args=(None if corrente == "spesa_smart" else ("spesa_smart",)))


def schermata_spesa_smart():
    st.markdown(_SS_CSS, unsafe_allow_html=True)
    if "nav_pagine" in globals():
        nav_pagine("spesa_smart")
    st.markdown("<div class='ss-hero'><div class='ico'>🛒</div><div><h1>Spesa Smart</h1>"
                "<p>Dove costa meno, offerte, liste ottimizzate e scontrini: insieme alla tua Dispensa.</p></div></div>", unsafe_allow_html=True)
    if "pulsante_info" in globals():
        try:
            pulsante_info("spesa_smart")
        except Exception:
            pass
    vista = st.session_state.get("ss_vista", "dash")
    with st.container(key="ss_hub"):
        for k, nome in _SS_VISTE:
            st.button(nome, key=("ss_hon_" if k == vista else "ss_h_") + k, width="stretch", on_click=_ss_vai, args=(k,))
    msg = st.session_state.pop("ss_msg", None)
    if msg:
        st.success(msg)
    try:
        ss, disp = _ss_leggi()
        {"dash": _ss_v_dash, "ins": _ss_v_inserisci, "dcm": _ss_v_dcm, "lista": _ss_v_lista, "ott": _ss_v_ottimizzata, "off": _ss_v_offerte,
         "scon": _ss_v_scontrino, "sto": _ss_v_storico, "prod": _ss_v_prodotti, "neg": _ss_v_negozi}.get(vista, _ss_v_dash)(ss, disp)
    except Exception as e:
        st.error(f"Qualcosa non è andato in Spesa Smart: {type(e).__name__}: {e}. I tuoi dati non sono stati toccati.")
    _ss_in_dispensa_proposta()


# ---------------------------------------------------------------------------------------------------------------------
# 13.1 Riepilogo (dashboard)
# ---------------------------------------------------------------------------------------------------------------------
def _ss_offerte_volantini():
    try:
        return (carica_offerte() or {}).get("offerte") or [] if "carica_offerte" in globals() else []
    except Exception:
        return []


def _ss_v_dash(ss, disp):
    oggi_ = ss_oggi()
    validi = sum(1 for p in ss["prodotti"] for _c in ss_prezzi_correnti(ss, p["id"], oggi_))
    off = ss_offerte_interessanti(ss, oggi_)
    esau = ss_esauriti_con_offerta(ss, disp, oggi_, _ss_offerte_volantini())
    da_comprare = [x for x in disp.get("spesa", []) if not x.get("preso")]
    st.markdown("<div class='ss-tiles'>" + "".join(f"<div class='ss-tile'><b>{n}</b><span>{_ss_esc(t)}</span></div>" for n, t in [
        (len(da_comprare), "da comprare (lista della Dispensa)"), (len(esau), "finiti con un'offerta"), (len(off), "offerte interessanti"),
        (validi, "prezzi validi oggi"), (len(ss_catalogo(ss, disp)), "prodotti in archivio"), (len(ss["negozi"]), "negozi")]) + "</div>", unsafe_allow_html=True)
    if esau:
        st.markdown("**🔔 Finiti in dispensa e oggi in offerta**")
        for nome, testo in esau[:8]:
            st.markdown(f"- **{_ss_esc(nome)}**: {_ss_esc(testo)}")
    if not ss["rilevazioni"]:
        st.info("**Come si comincia:** tocca **⚡ Inserisci un prezzo** quando sei al supermercato (o fotografa uno **🧾 Scontrino**). "
                "Con qualche prezzo di due o tre negozi l'app ti dice **dove costa meno** e prepara la **spesa ottimizzata**.")
        return
    s = ss_suggerimenti(ss, disp, oggi_)
    if s["pagati_di_piu"]:
        st.markdown("**📈 Pagati più del solito**")
        for p, minimo, ult in s["pagati_di_piu"][:5]:
            st.markdown(f"- {_ss_esc(p.get('nome'))}: l'ultima volta {ss_euro(ult)} (prima anche {ss_euro(minimo)})")
    elif s["aumenti"]:
        st.markdown("**↕️ Prezzi cambiati dall'ultimo acquisto**")
        for p, prima, ult in s["aumenti"][:5]:
            st.markdown(f"- {_ss_esc(p.get('nome'))}: {ss_euro(prima)} → {ss_euro(ult)}")
    if s["frequenti"]:
        st.markdown("**🔁 Compri spesso** (ultimi 3 mesi): " + ", ".join(f"{_ss_esc(p.get('nome'))} ({n})" for p, n in s["frequenti"][:6]))
    if s["in_esaurimento"]:
        st.markdown("**🥫 Stanno finendo:** " + ", ".join(_ss_esc(x) for x in s["in_esaurimento"][:10]))


# ---------------------------------------------------------------------------------------------------------------------
# 13.2 Inserimento rapido del prezzo
# ---------------------------------------------------------------------------------------------------------------------
def _ss_campi_prodotto(k, pre=None):
    """I campi di un prodotto nuovo (dentro la stessa schermata). Ritorna il dizionario."""
    pre = pre or {}
    c1, c2 = st.columns([3, 2], gap="small")
    nome = c1.text_input("Nome del prodotto *", value=pre.get("nome", ""), key=k + "_nome", placeholder="es. Spaghetti n.5")
    marca = c2.text_input("Marca", value=pre.get("marca", ""), key=k + "_marca", placeholder="es. Barilla")
    c3, c4 = st.columns([3, 2], gap="small")
    variante = c3.text_input("Variante", value=pre.get("variante", ""), key=k + "_var", placeholder="es. integrale, senza lattosio")
    cats = SS_CATEGORIE
    categoria = c4.selectbox("Categoria", cats, index=cats.index(pre["categoria"]) if pre.get("categoria") in cats else len(cats) - 1, key=k + "_cat")
    c5, c6, c7 = st.columns([2, 2, 2], gap="small")
    fv = c5.number_input("Formato", min_value=0.0, value=ss_num(pre.get("formato_valore")), step=1.0, format="%g", key=k + "_fv", placeholder="es. 500")
    unita = SS_UNITA_SCELTA
    fu0 = str(pre.get("formato_unita") or "g").lower()
    fu = c6.selectbox("Unità", unita, index=unita.index(fu0) if fu0 in unita else 0, key=k + "_fu")
    conf = c7.number_input("Pezzi nella confezione", min_value=1, value=int(ss_num(pre.get("confezioni"), 1) or 1), step=1, key=k + "_conf")
    ean = st.text_input("Codice a barre (EAN)", value=pre.get("ean", ""), key=k + "_ean", placeholder="facoltativo")
    return {"nome": nome, "marca": marca, "variante": variante, "categoria": categoria, "formato_valore": fv or None, "formato_unita": fu if fv else "",
            "confezioni": int(conf), "ean": ean.strip(), "immagine": pre.get("immagine", "")}


def _ss_codice_a_barre(k):
    """📷 Leggi il codice a barre (foto) → EAN in session_state[k]."""
    with st.expander("📷 Leggi il codice a barre"):
        foto = st.camera_input("Inquadra il codice a barre", key=k + "_cam") if st.checkbox("Usa la fotocamera", key=k + "_usa_cam") else None
        file_ = st.file_uploader("…oppure scegli una foto", type=["jpg", "jpeg", "png", "webp"], key=k + "_up")
        img = foto or file_
        if img is not None:
            dati = img.getvalue()
            firma = hash(dati[:2000])
            if st.session_state.get(k + "_firma") != firma:
                st.session_state[k + "_firma"] = firma
                ean = ""
                try:
                    ean = (leggi_foto(dati) or {}).get("ean", "") if "leggi_foto" in globals() else ""
                except Exception:
                    ean = ""
                if ean:
                    st.session_state[k] = ean
                    st.session_state.pop(k + "_off", None)
                else:
                    st.warning("Non trovo il codice a barre nella foto: avvicinati, con più luce, e tieni il codice dritto.")
        ean_m = st.text_input("…oppure scrivi le cifre", key=k + "_man", placeholder="8076800195057")
        if ean_m.strip().isdigit() and len(ean_m.strip()) in (8, 12, 13, 14) and st.session_state.get(k) != ean_m.strip():
            st.session_state[k] = ean_m.strip()
            st.session_state.pop(k + "_off", None)
    return st.session_state.get(k, "")


def _ss_dati_off(ean, k):
    """Nome, marca e formato da Open Food Facts (gratuito, senza chiave), una volta sola per codice."""
    if not ean:
        return {}
    if k + "_off" not in st.session_state:
        pre = {}
        try:
            if "cerca_prodotto" in globals():
                raw = cerca_prodotto(ean)
                if raw and "errore" not in raw:
                    x = interpreta_prodotto(raw)
                    pre = {"nome": x.get("nome", ""), "marca": x.get("marca", ""), "formato_valore": x.get("formato_valore"),
                           "formato_unita": ("l" if x.get("formato_unita") == "L" else x.get("formato_unita") or ""), "immagine": x.get("immagine", "")}
        except Exception:
            pre = {}
        pre["ean"] = ean
        st.session_state[k + "_off"] = pre
    return st.session_state[k + "_off"]


def _ss_scelta_negozio(ss, k, etichetta="🏪 Negozio"):
    """Ritorna (negozio_id esistente | None, dati del negozio nuovo | None)."""
    ultimo = ss["impostazioni"].get("ultimo_negozio")
    ids = [n["id"] for n in sorted(ss["negozi"], key=lambda n: (n["id"] != ultimo, ss_norm(n.get("nome"))))]
    nomi = {n["id"]: ss_nome_negozio(n) for n in ss["negozi"]}
    if ids:
        scelta = st.pills(etichetta, ids + ["__nuovo__"], default=(ultimo if ultimo in ids else None), key=k + "_neg",
                          format_func=lambda i: "➕ Nuovo negozio" if i == "__nuovo__" else nomi.get(i, "?"))
    else:
        st.markdown(f"**{etichetta}**")
        scelta = "__nuovo__"
    if scelta == "__nuovo__":
        c1, c2 = st.columns(2, gap="small")
        nome = c1.text_input("Nome del negozio *", key=k + "_nn", placeholder="es. Esselunga")
        citta = c2.text_input("Città", key=k + "_nc", placeholder="es. Torino")
        ind = st.text_input("Indirizzo (per distinguere i punti vendita)", key=k + "_ni", placeholder="es. Corso Traiano 3")
        return None, {"nome": nome, "citta": citta, "indirizzo": ind, "catena": nome}
    return scelta, None


def _ss_v_inserisci(ss, disp):
    giro = st.session_state.setdefault("ss_ins_giro", 0)
    k = f"ssi{giro}"
    st.markdown("#### ⚡ Inserisci un prezzo")
    st.caption("Tre tocchi se prodotto e negozio ci sono già: **scegli il prodotto**, **scrivi il prezzo**, **💾 Salva** (il negozio resta quello dell'ultima volta).")
    ean = _ss_codice_a_barre(k + "_ean")
    cat = ss_catalogo(ss, disp)
    uso = {}
    for r in ss["rilevazioni"]:
        uso[r.get("prodotto_id")] = max(uso.get(r.get("prodotto_id"), ""), r.get("data") or "")
    cat.sort(key=lambda p: (uso.get(p["id"], "") == "", "" if not uso.get(p["id"]) else "~" + str(9999 - int(uso[p["id"]][:4] or 0)) + uso[p["id"]][4:],
                            ss_norm(p.get("nome"))))
    cat.sort(key=lambda p: uso.get(p["id"], ""), reverse=True)
    per_id = {p["id"]: p for p in cat}
    pre_id = None
    if ean:
        pre_id = next((p["id"] for p in cat if str(p.get("ean") or "").strip() == ean), None)
        if pre_id:
            st.success("Trovato: " + _ss_etich_prodotto(per_id[pre_id]))
        else:
            st.info(f"Il codice {ean} non è ancora nell'archivio: compila il prodotto nuovo qui sotto (ho cercato nome e formato su Open Food Facts).")
    opz = ["__nuovo__"] + list(per_id)
    idx = opz.index(pre_id) if pre_id else (0 if ean else None)
    scelta = st.selectbox("🔎 Prodotto (scrivi per cercare)", opz, index=idx, key=k + "_prod", placeholder="Scrivi il nome…",
                          format_func=lambda i: "➕ Nuovo prodotto" if i == "__nuovo__" else _ss_etich_prodotto(per_id[i]))
    nuovo_p = None
    if scelta == "__nuovo__":
        with st.container(border=True):
            nuovo_p = _ss_campi_prodotto(k + "_np", _ss_dati_off(ean, k + "_ean") if ean else {})
            for e in ss_valida_prodotto(nuovo_p) if nuovo_p.get("nome") else []:
                st.warning(e)
            dop = ss_cerca_doppione(ss, nuovo_p) if nuovo_p.get("nome") else None
            if dop:
                st.info("Esiste già: **" + _ss_esc(_ss_etich_prodotto(dop)) + "** — salvo il prezzo su quello (niente doppioni).")
    neg_id, neg_nuovo = _ss_scelta_negozio(ss, k)
    prezzo = st.number_input("💶 Prezzo (€)", min_value=0.0, max_value=5000.0, value=None, step=0.01, format="%.2f", key=k + "_prezzo", placeholder="es. 1,29")
    prod_rif = per_id.get(scelta) if scelta and scelta != "__nuovo__" else (nuovo_p or {})
    with st.expander("🏷️ Offerta, formato, tessera, data e note"):
        c1, c2 = st.columns(2, gap="small")
        promo = c1.number_input("Prezzo in offerta (€)", min_value=0.0, value=None, step=0.01, format="%.2f", key=k + "_promo", placeholder="se c'è")
        tessera = c2.checkbox("Serve la tessera fedeltà", key=k + "_tess")
        c3, c4 = st.columns(2, gap="small")
        pdal = c3.date_input("Offerta dal", value=None, format="DD/MM/YYYY", key=k + "_pdal")
        pal = c4.date_input("Offerta fino al", value=None, format="DD/MM/YYYY", key=k + "_pal")
        st.caption("Solo se QUESTA confezione è diversa dal solito (" + (ss_fmt_formato(prod_rif) or "formato non indicato") + "):")
        c5, c6, c7 = st.columns(3, gap="small")
        fv_x = c5.number_input("Formato", min_value=0.0, value=None, step=1.0, format="%g", key=k + "_fv", placeholder="uguale")
        fu_x = c6.selectbox("Unità", SS_UNITA_SCELTA, key=k + "_fu")
        conf_x = c7.number_input("Pezzi", min_value=1, value=None, step=1, key=k + "_conf", placeholder="uguale")
        data_r = st.date_input("Data del prezzo", value=ss_oggi(), max_value=ss_oggi(), format="DD/MM/YYYY", key=k + "_data")
        note = st.text_input("Note", key=k + "_note", placeholder="es. solo nel volantino, 3x2…")
    fv = fv_x or ss_num(prod_rif.get("formato_valore"))
    fu = fu_x if fv_x else str(prod_rif.get("formato_unita") or "")
    conf = int(conf_x or ss_num(prod_rif.get("confezioni"), 1) or 1)
    pu, base = ss_prezzo_unitario(promo or prezzo, conf, fv, fu if fv else "")
    if pu:
        st.markdown(f"<div class='ss-card'><span class='u'>= {ss_fmt_unitario(pu, base)}</span>"
                    + (f" <span class='ss-promo'>offerta</span>" if promo else "") + "</div>", unsafe_allow_html=True)
    comprato = st.checkbox("🧾 L'ho comprato adesso (registra anche l'acquisto)", key=k + "_comp")
    quanti = st.number_input("Quanti ne hai presi", min_value=1, value=1, step=1, key=k + "_q") if comprato else 1
    if st.button("💾 Salva il prezzo", type="primary", width="stretch", key=k + "_ok"):
        errori = []
        if not scelta:
            errori.append("Scegli il prodotto (o «➕ Nuovo prodotto»).")
        if scelta == "__nuovo__":
            errori += ss_valida_prodotto(nuovo_p or {})
        if not neg_id and not (neg_nuovo or {}).get("nome", "").strip():
            errori.append("Scegli il negozio o scrivi il nome di quello nuovo.")
        if not (prezzo or promo):
            errori.append("Scrivi il prezzo.")
        if errori:
            for e in errori:
                st.warning(e)
            return
        esito = {}

        def _fn(ss_):
            if scelta == "__nuovo__":
                p, _n = ss_aggiungi_prodotto(ss_, nuovo_p)
            else:
                p = ss_trova(ss_, "prodotti", scelta) or ss_materializza(ss_, dict(per_id[scelta]))
            n = ss_trova(ss_, "negozi", neg_id) if neg_id else ss_aggiungi_negozio(ss_, neg_nuovo)[0]
            r, err = ss_nuova_rilevazione(ss_, p["id"], n["id"], prezzo=prezzo, prezzo_promo=promo, confezioni=conf_x or None, formato_valore=fv_x or None,
                                          formato_unita=fu_x if fv_x else "", data=data_r, promo_dal=pdal, promo_al=pal, tessera=tessera, note=note)
            if err:
                esito["err"] = err
                raise ValueError("; ".join(err))
            if comprato:
                ss_registra_acquisto(ss_, p["id"], n["id"], quanti, round((promo or prezzo) * quanti, 2), data=data_r, con_rilevazione=False)
            ss_["impostazioni"]["ultimo_negozio"] = n["id"]
            esito.update(p=dict(p), n=ss_nome_negozio(n), r=r)
        try:
            _ss_salva(_fn, "prezzo")
        except Exception as e:
            st.error("Non salvato: " + ("; ".join(esito.get("err") or []) or str(e)))
            return
        st.session_state["ss_msg"] = f"✅ Salvato: {esito['p'].get('nome')} a {ss_euro(promo or prezzo)} da {esito['n']}" + (
            f" ({ss_fmt_unitario(esito['r'].get('prezzo_unitario'), esito['r'].get('unita_base'))})" if esito["r"].get("prezzo_unitario") else "")
        if comprato:
            st.session_state["ss_in_disp"] = [{"prodotto": esito["p"], "quantita": quanti}]
        st.session_state["ss_ins_giro"] = giro + 1
        st.rerun()


def _ss_in_dispensa_proposta():
    """Dopo un acquisto: «📦 Aggiorno le scorte della Dispensa?» (si conferma; si può cambiare quantità e scadenza)."""
    voci = st.session_state.get("ss_in_disp")
    if not voci:
        return
    with st.container(border=True):
        st.markdown("**📦 Hai comprato: aggiorno le scorte della Dispensa?**")
        scelte = []
        for i, v in enumerate(voci):
            p = v["prodotto"]
            st.markdown(f"**{_ss_esc(_ss_etich_prodotto(p))}**")
            c1, c2 = st.columns([1, 2], gap="small")
            q = c1.number_input("Unità", min_value=0, value=int(ss_num(v.get("quantita"), 1) or 1), step=1, key=f"ssd_q{i}")
            senza = c2.checkbox("Senza scadenza", key=f"ssd_ns{i}")
            sc = None if senza else c2.date_input("Scadenza", value=None, format="DD/MM/YYYY", key=f"ssd_sc{i}")
            scelte.append({"prodotto": p, "quantita": q, "scadenza": sc.isoformat() if sc else None, "posto": st.session_state.get("ultimo_posto", "dispensa")})
        b1, b2 = st.columns(2, gap="small")
        if b1.button("📦 Sì, aggiungi alla Dispensa", type="primary", width="stretch", key="ssd_ok"):
            esito = {}
            _ss_salva_disp(lambda d: esito.__setitem__("n", ss_metti_in_dispensa(d, scelte, _ss_utente())), "acquisto in dispensa")
            st.session_state.pop("ss_in_disp", None)
            st.session_state["ss_msg"] = f"📦 Scorte aggiornate: {esito.get('n', 0)} prodotti in Dispensa (e tolti dalla lista della spesa)."
            st.rerun()
        if b2.button("No, grazie", width="stretch", key="ssd_no"):
            st.session_state.pop("ss_in_disp", None)
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 13.3 Dove costa meno
# ---------------------------------------------------------------------------------------------------------------------
def _ss_card_dcm(ss, x):
    p, m = x["prodotto"], x["migliore"]
    n = ss_trova(ss, "negozi", m["negozio_id"])
    img = f"<img src='{_ss_esc(p['immagine'])}' alt=''>" if str(p.get("immagine", "")).startswith("http") else ""
    r = m["rilevazione"]
    promo = (f"<span class='ss-promo'>OFFERTA" + (f" fino al {ss_data_it(r.get('promo_al'))}" if r.get("promo_al") else "") + "</span>") if m["offerta"] else ""
    tess = " 💳 con tessera" if r.get("tessera") else ""
    righe = ""
    for c in x["classifica"][1:6]:
        nn = ss_trova(ss, "negozi", c["negozio_id"])
        righe += (f"<li>{_ss_esc(ss_nome_negozio(nn))}: <b>{ss_euro(c['prezzo'])}</b>" + (f" · {ss_fmt_unitario(c['unitario'], c['base'])}" if c["unitario"] else "")
                  + (" <span class='ss-promo'>offerta</span>" if c["offerta"] else "") + f" <small>({ss_data_it(c['rilevazione'].get('data'))})</small></li>")
    avviso = "" if m["confrontabile"] else "<div class='m'>⚠️ Confezioni misurate in unità diverse (es. litri e kg): confronto solo sul prezzo della confezione.</div>"
    return (f"<div class='ss-card'>{img}<div class='t'>{_ss_esc(p.get('nome'))}</div><div class='m'>{_ss_esc(' · '.join(x_ for x_ in (p.get('marca'), ss_fmt_formato(p)) if x_))}</div>"
            f"<div class='big'>{ss_euro(m['prezzo'])} {promo}</div><div class='u'>{ss_fmt_unitario(m['unitario'], m['base'])}</div>"
            f"<div class='m'>🏪 <b>{_ss_esc(ss_nome_negozio(n))}</b>{tess} · rilevato il {ss_data_it(r.get('data'))}"
            + (f" · risparmi fino al {x['risparmio_pct']:.0f}%" if x["risparmio_pct"] >= 1 else "") + f"</div>{avviso}"
            + (f"<ol start='2'>{righe}</ol>" if righe else "") + "</div>")


def _ss_v_dcm(ss, disp):
    st.markdown("#### 🏆 Dove costa meno")
    c1, c2 = st.columns([3, 2], gap="small")
    filtro = c1.text_input("🔎 Cerca", key="ss_dcm_f", placeholder="nome, marca o categoria")
    ordine = c2.selectbox("Ordina per", ["prezzo crescente", "prezzo decrescente", "percentuale di risparmio", "data dell'ultima rilevazione"], key="ss_dcm_o")
    righe = ss_dove_costa_meno(ss, ss_oggi(), ordine, filtro)
    if not righe:
        st.info("Nessun prezzo valido oggi" + (" per questa ricerca" if filtro else "") + ". I prezzi più vecchi di 30 giorni e le offerte finite non valgono: aggiungine con **⚡ Inserisci un prezzo**.")
    for x in righe[:60]:
        st.markdown(_ss_card_dcm(ss, x), unsafe_allow_html=True)
    da_ver = [(p, c) for p in ss["prodotti"] for c in ss_prezzi_correnti(ss, p["id"], ss_oggi(), anche_da_verificare=True) if c["stato"] == "da verificare"]
    if da_ver:
        with st.expander(f"🟠 Prezzi da verificare ({len(da_ver)}): più vecchi di 30 giorni, NON usati nei confronti"):
            for p, c in da_ver[:40]:
                n = ss_trova(ss, "negozi", c["negozio_id"])
                st.markdown(f"- {_ss_esc(p.get('nome'))}: {ss_euro(c['prezzo'])} da {_ss_esc(ss_nome_negozio(n))} ({ss_data_it(c['rilevazione'].get('data'))})")
    con_ean = [p for p in ss["prodotti"] if p.get("ean")]
    if con_ean and "cerca_prezzi" in globals():
        with st.expander("🌍 Prezzi segnalati dalla comunità (Open Prices, gratuito)"):
            st.caption("Prezzi inseriti da altre persone su Open Prices (Open Food Facts). Sono **da verificare** e non entrano nei tuoi confronti.")
            pid = st.selectbox("Prodotto con codice a barre", [p["id"] for p in con_ean], format_func=lambda i: _ss_etich_prodotto(ss_trova(ss, "prodotti", i)), key="ss_op_p")
            if st.button("🔎 Cerca su Open Prices", key="ss_op_ok", width="stretch"):
                pr = cerca_prezzi(ss_trova(ss, "prodotti", pid)["ean"])
                if not pr:
                    st.info("Nessun prezzo segnalato per questo codice.")
                for x in pr:
                    st.markdown(f"- {ss_euro(x['prezzo'])} · {_ss_esc(x.get('negozio') or '?')} · {ss_data_it(x.get('data'))} 🟠")


# ---------------------------------------------------------------------------------------------------------------------
# 13.4 Storico prezzi
# ---------------------------------------------------------------------------------------------------------------------
def _ss_v_storico(ss, disp):
    st.markdown("#### 📈 Storico prezzi")
    con = [p for p in ss["prodotti"] if any(r.get("prodotto_id") == p["id"] for r in ss["rilevazioni"])]
    if not con:
        st.info("Ancora nessun prezzo salvato.")
        return
    pid = st.selectbox("Prodotto", [p["id"] for p in con], format_func=lambda i: _ss_etich_prodotto(ss_trova(ss, "prodotti", i)), key="ss_sto_p")
    sto = ss_storico(ss, pid)
    import pandas as _pd
    basi = {r.get("unita_base") for r in sto}
    unit = len(basi) == 1
    righe = []
    for r in sto:
        n = ss_trova(ss, "negozi", r.get("negozio_id"))
        eff = ss_num(r.get("prezzo_promo")) or ss_num(r.get("prezzo"))
        righe.append({"data": r.get("data"), "negozio": ss_nome_negozio(n).split(" · ")[0] + (" · " + n.get("citta") if n and n.get("citta") else ""),
                      "valore": (r.get("prezzo_unitario") if unit else eff)})
    df = _pd.DataFrame(righe)
    if not df.empty:
        df["data"] = _pd.to_datetime(df["data"], errors="coerce")
        tab = df.pivot_table(index="data", columns="negozio", values="valore", aggfunc="min").sort_index()
        st.caption("Andamento " + (SS_NOME_BASE.get(next(iter(basi)), "€") if unit else "€ a confezione (formati diversi)") + " per negozio")
        st.line_chart(tab, height=260)
    oggi_ = ss_oggi()
    for r in reversed(sto[-40:]):
        n = ss_trova(ss, "negozi", r.get("negozio_id"))
        stato, prezzo, off = ss_stato(r, oggi_)
        bollino = {"attiva": "🟢", "da verificare": "🟠", "scaduta": "⚪"}.get(stato, "⚪")
        c1, c2 = st.columns([5, 1], gap="small")
        c1.markdown(f"{bollino} **{ss_data_it(r.get('data'))}** · {_ss_esc(ss_nome_negozio(n))} · {ss_euro(r.get('prezzo'))}"
                    + (f" → offerta {ss_euro(r.get('prezzo_promo'))}" if r.get("prezzo_promo") else "")
                    + (f" · {ss_fmt_unitario(r.get('prezzo_unitario'), r.get('unita_base'))}" if r.get("prezzo_unitario") else "")
                    + f" · _{r.get('fonte')}_ · {stato}")
        with c2.popover("⋯"):
            if st.button("🟠 Da verificare" if not r.get("da_verificare") else "🟢 È giusto", key="ss_ver_" + r["id"], width="stretch"):
                _ss_salva(lambda s_, i=r["id"]: ss_trova(s_, "rilevazioni", i).__setitem__("da_verificare", not ss_trova(s_, "rilevazioni", i).get("da_verificare")), "verifica prezzo")
                st.rerun()
            if st.button("🗑️ Elimina questo prezzo", key="ss_del_" + r["id"], width="stretch"):
                _ss_salva(lambda s_, i=r["id"]: ss_elimina(s_, "rilevazioni", i), "prezzo eliminato")
                st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 13.5 Lista della spesa (quella della Dispensa, condivisa) + liste private
# ---------------------------------------------------------------------------------------------------------------------
_SS_LISTA_DISP = "__dispensa__"
_SS_PRIORITA = ["Alta", "Normale", "Bassa"]


def _ss_uid():
    return str((st.session_state.get("sess") or {}).get("uid") or "")


def _ss_lc_leggi():
    """Il file delle liste condivise, sempre fresco (non dalla memoria di 60 secondi)."""
    try:
        a_ = crea_archivio()
        return (a_.leggi_grezzo(SS_LC) if hasattr(a_, "leggi_grezzo") else a_.leggi(SS_LC)) or {}
    except Exception:
        return {}


def _ss_persone():
    """[(uid, nome)] delle persone dell'app (tranne me)."""
    try:
        tutte = [("admin", fd_nome_di("admin") if "fd_nome_di" in globals() else "Amministratore")] + [(u["id"], u["nome"]) for u in leggi_utenti() if u.get("attivo", True)]
    except Exception:
        tutte = []
    return [(i, n) for i, n in tutte if i != _ss_uid()]


def _ss_nome_uid(uid):
    try:
        return fd_nome_di(uid) if "fd_nome_di" in globals() else uid
    except Exception:
        return uid


def _ss_scegli_lista(ss, k):
    liste = [l for l in ss["liste"] if l.get("stato") != "chiusa"]
    comuni = ss_lc_mie(_ss_lc_leggi(), _ss_uid())
    opz = [_SS_LISTA_DISP] + ["c:" + l["id"] for l in comuni] + [l["id"] for l in liste]
    nomi = {_SS_LISTA_DISP: "🏠 Lista della Dispensa (condivisa)"} | {l["id"]: "🔒 " + (l.get("nome") or "Lista") for l in liste}
    for l in comuni:
        altri = [_ss_nome_uid(u) for u in [l.get("proprietario")] + list(l.get("persone") or []) if u != _ss_uid()]
        nomi["c:" + l["id"]] = "👥 " + (l.get("nome") or "Lista") + (" (con " + ", ".join(altri[:3]) + ("…" if len(altri) > 3 else "") + ")" if altri else "")
    nxt = st.session_state.pop(k + "_prossima", None)
    if nxt in opz:
        st.session_state[k] = nxt
    if st.session_state.get(k) not in opz:
        st.session_state.pop(k, None)
    return st.selectbox("Quale lista", opz, format_func=lambda i: nomi.get(i, "?"), key=k)


def _ss_v_lista(ss, disp):
    st.markdown("#### 📝 Lista della spesa")
    lid = _ss_scegli_lista(ss, "ss_lista_sel")
    persone = _ss_persone()
    if persone:
        with st.popover("👥 Nuova lista condivisa con persone scelte", width="stretch"):
            nome_c = st.text_input("Nome della lista", key="ss_nc_nome", placeholder="es. Spesa per la mamma")
            chi = st.multiselect("Con chi la condividi", [i for i, _n in persone], format_func=dict(persone).get, key="ss_nc_chi")
            st.caption("La vedono e la modificano **solo** queste persone e tu. Si aggiorna da sola ogni 10 secondi; quando uno spunta un prodotto, gli altri vedono «preso da…».")
            if st.button("Crea", key="ss_nc_ok", type="primary", width="stretch"):
                if not nome_c.strip() or not chi:
                    st.warning("Scrivi il nome e scegli almeno una persona.")
                else:
                    esito = {}
                    salva_file(SS_LC, lambda d: esito.__setitem__("l", ss_lc_nuova(d, nome_c, _ss_uid(), chi)), "Spesa Smart: nuova lista condivisa")
                    st.session_state["ss_lista_sel_prossima"] = "c:" + esito["l"]["id"]
                    st.rerun()
    with st.popover("➕ Nuova lista privata", width="stretch"):
        nome = st.text_input("Nome della lista", key="ss_nl_nome", placeholder="es. Spesa grande del mese")
        if st.button("Crea", key="ss_nl_ok", type="primary", width="stretch") and nome.strip():
            nid = ss_id()
            _ss_salva(lambda s_: s_["liste"].append({"id": nid, "nome": nome.strip(), "creata_il": ss_ora(), "proprietario": _ss_utente(), "stato": "aperta"}), "nuova lista")
            st.session_state["ss_lista_sel_prossima"] = nid
            st.rerun()
    cat = ss_catalogo(ss, disp)
    per_id = {p["id"]: p for p in cat}
    if lid == _SS_LISTA_DISP:
        st.caption("È **la stessa lista della Dispensa**: i prodotti finiti arrivano qui da soli e, se usi la dispensa di famiglia, la vedono e la spuntano anche gli altri "
                   "(si aggiorna da sola ogni pochi secondi; un prodotto spuntato da uno non viene comprato due volte).")
        c1, c2 = st.columns([3, 1], gap="small")
        scelti = c1.multiselect("Aggiungi dall'archivio prodotti (anche quelli della Dispensa)", list(per_id), format_func=lambda i: _ss_etich_prodotto(per_id[i]), key="ss_ld_add")
        if c2.button("➕ Aggiungi", key="ss_ld_ok", width="stretch") and scelti:
            def _fn(d):
                for i in scelti:
                    p = per_id[i]
                    aggiungi_a_spesa(d, {"nome": p.get("nome"), "marca": p.get("marca", ""), "barcode": p.get("ean", ""), "q": 1})
            _ss_salva_disp(_fn, "aggiunti alla lista")
            st.rerun()
        quasi = [a for a in disp.get("articoli", []) if 0 < (ss_num(a.get("quantita"), 0) or 0) <= 1]
        if quasi and st.button(f"📥 Importa quelli quasi finiti in Dispensa ({len(quasi)})", key="ss_ld_imp", width="stretch"):
            _ss_salva_disp(lambda d: [aggiungi_a_spesa(d, dict(a, q=1)) for a in quasi], "quasi finiti in lista")
            st.rerun()
        if "scheda_spesa" in globals():
            scheda_spesa()                                                 # la lista vera, con le sue spunte, quantità e «Metti in dispensa»
        return
    if str(lid).startswith("c:"):
        _ss_lc_vista(lid[2:], per_id)
        return
    lista = ss_trova(ss, "liste", lid)
    if not lista:
        return
    righe = [r for r in ss["liste_righe"] if r.get("lista_id") == lid]
    c1, c2, c3 = st.columns([4, 1.4, 1.6], gap="small")
    pid = c1.selectbox("Prodotto", list(per_id), index=None, format_func=lambda i: _ss_etich_prodotto(per_id[i]), key="ss_lp_p", placeholder="Scrivi per cercare…")
    q = c2.number_input("Quanti", min_value=1, value=1, step=1, key="ss_lp_q")
    if c3.button("➕ Aggiungi", key="ss_lp_ok", width="stretch") and pid:
        def _fn(s_):
            p = ss_trova(s_, "prodotti", pid) or ss_materializza(s_, dict(per_id[pid]))
            gia = next((r for r in s_["liste_righe"] if r.get("lista_id") == lid and r.get("prodotto_id") == p["id"] and r.get("stato") != "preso"), None)
            if gia:
                gia["quantita"] = (ss_num(gia.get("quantita"), 1) or 1) + q                # niente doppioni: si somma
            else:
                s_["liste_righe"].append({"id": ss_id(), "lista_id": lid, "prodotto_id": p["id"], "quantita": q, "priorita": "Normale", "stato": "da comprare"})
        _ss_salva(_fn, "riga di lista")
        st.rerun()
    da_disp = [r for r in disp.get("spesa", []) if not r.get("preso")]
    if da_disp and st.button(f"📥 Importa i finiti della Dispensa ({len(da_disp)})", key="ss_lp_imp", width="stretch"):
        def _fn(s_):
            for r in da_disp:
                p = ss_prodotto_per_riga_disp(s_, r) or ss_aggiungi_prodotto(s_, ss_da_dispensa(r))[0]
                if not any(x.get("lista_id") == lid and x.get("prodotto_id") == p["id"] and x.get("stato") != "preso" for x in s_["liste_righe"]):
                    s_["liste_righe"].append({"id": ss_id(), "lista_id": lid, "prodotto_id": p["id"], "quantita": ss_num(r.get("q"), 1) or 1, "priorita": "Normale", "stato": "da comprare"})
        _ss_salva(_fn, "finiti importati")
        st.rerun()
    if not righe:
        st.info("La lista è vuota.")
    else:
        import pandas as _pd
        df = _pd.DataFrame([{"id": r["id"], "Preso": r.get("stato") == "preso", "Prodotto": _ss_etich_prodotto(ss_trova(ss, "prodotti", r.get("prodotto_id")) or {"nome": "?"}),
                             "Quanti": float(ss_num(r.get("quantita"), 1) or 1), "Priorità": r.get("priorita") or "Normale", "🗑️": False} for r in righe]).set_index("id")
        mod = st.data_editor(df, key=f"ss_lp_ed_{lid}_{len(righe)}", width="stretch", disabled=["Prodotto"], hide_index=True,
                             column_config={"Preso": st.column_config.CheckboxColumn("Preso", width="small"), "Quanti": st.column_config.NumberColumn("Quanti", min_value=1.0, step=1.0, width="small"),
                                            "Priorità": st.column_config.SelectboxColumn("Priorità", options=_SS_PRIORITA, width="small"), "🗑️": st.column_config.CheckboxColumn("🗑️", width="small")})
        if st.button("💾 Salva la lista", key="ss_lp_salva", type="primary", width="stretch"):
            def _fn(s_):
                nuove = []
                for r in s_["liste_righe"]:
                    if r.get("lista_id") == lid and r["id"] in mod.index:
                        m = mod.loc[r["id"]]
                        if bool(m["🗑️"]):
                            continue
                        r["stato"] = "preso" if bool(m["Preso"]) else "da comprare"
                        r["quantita"] = max(ss_num(m["Quanti"], 1) or 1, 1)
                        r["priorita"] = m["Priorità"] if m["Priorità"] in _SS_PRIORITA else "Normale"
                    nuove.append(r)
                s_["liste_righe"] = nuove
            _ss_salva(_fn, "lista")
            st.rerun()
        presi = [r for r in righe if r.get("stato") == "preso"]
        if presi and st.button(f"📦 Metti in Dispensa i presi ({len(presi)})", key="ss_lp_disp", width="stretch"):
            st.session_state["ss_in_disp"] = [{"prodotto": ss_trova(ss, "prodotti", r["prodotto_id"]), "quantita": r.get("quantita")} for r in presi if ss_trova(ss, "prodotti", r["prodotto_id"])]
            st.rerun()
    with st.expander("⚙️ Lista"):
        if st.button("✅ Chiudi la lista (spesa fatta)", key="ss_lp_chiudi", width="stretch"):
            _ss_salva(lambda s_: ss_trova(s_, "liste", lid).__setitem__("stato", "chiusa"), "lista chiusa")
            st.session_state["ss_lista_sel_prossima"] = "__dispensa__"
            st.rerun()
        if st.button("🗑️ Elimina la lista", key="ss_lp_del", width="stretch"):
            _ss_salva(lambda s_: ss_elimina(s_, "liste", lid), "lista eliminata")
            st.session_state["ss_lista_sel_prossima"] = "__dispensa__"
            st.rerun()


def _ss_lc_corpo(lc_id, per_id):
    """Una lista condivisa: si ridisegna da sola ogni 10 secondi (modifiche degli altri)."""
    uid, chi = _ss_uid(), _ss_utente()
    dati = _ss_lc_leggi()
    lista = next((l for l in dati.get("liste") or [] if l.get("id") == lc_id), None)
    if not lista or not ss_lc_puo(lista, uid):
        st.warning("Questa lista non c'è più o non è condivisa con te.")
        return
    persone = [_ss_nome_uid(u) for u in [lista.get("proprietario")] + list(lista.get("persone") or [])]
    st.caption("👥 Condivisa tra: **" + ", ".join(persone) + "** · si aggiorna da sola ogni 10 secondi")
    c1, c2, c3 = st.columns([4, 1.4, 1.6], gap="small")
    pid = c1.selectbox("Prodotto", list(per_id), index=None, format_func=lambda i: _ss_etich_prodotto(per_id[i]), key="ss_lc_p_" + lc_id, placeholder="Scrivi per cercare…")
    q = c2.number_input("Quanti", min_value=1, value=1, step=1, key="ss_lc_q_" + lc_id)
    libero = st.text_input("…oppure scrivi un prodotto che non è in archivio", key="ss_lc_lib_" + lc_id, placeholder="es. pane fresco")
    if c3.button("➕ Aggiungi", key="ss_lc_ok_" + lc_id, width="stretch") and (pid or libero.strip()):
        p = per_id[pid] if pid else {"nome": libero.strip()}
        esito = {}

        def _fn(d):
            l = next((x for x in d.get("liste") or [] if x.get("id") == lc_id), None)
            if not ss_lc_puo(l, uid):
                raise PermissionError("lista non condivisa con te")
            esito["r"] = ss_lc_aggiungi(l, p, q, chi)
            d["versione"] = int(d.get("versione") or 0) + 1
        salva_file(SS_LC, _fn, "Spesa Smart: lista condivisa")
        if not esito["r"][1]:
            st.toast(f"«{p.get('nome')}» era già in lista: ho aumentato la quantità.")
        st.session_state.pop("ss_lc_lib_" + lc_id, None)
        st.rerun(scope="fragment")
    righe = lista.get("righe") or []
    if not righe:
        st.info("La lista è vuota.")
        return
    import pandas as _pd
    df = _pd.DataFrame([{"id": r["id"], "Preso": r.get("stato") == "preso", "Prodotto": " · ".join(x for x in (r.get("nome"), r.get("marca")) if x),
                         "Quanti": float(ss_num(r.get("quantita"), 1) or 1), "Priorità": r.get("priorita") or "Normale",
                         "Chi": ("✅ " + r["preso_da"]) if r.get("stato") == "preso" and r.get("preso_da") else ("➕ " + (r.get("aggiunto_da") or "")),
                         "🗑️": False} for r in righe]).set_index("id")
    ver = int(dati.get("versione") or 0)
    mod = st.data_editor(df, key=f"ss_lc_ed_{lc_id}_{ver}", width="stretch", disabled=["Prodotto", "Chi"], hide_index=True,
                         column_config={"Preso": st.column_config.CheckboxColumn("Preso", width="small"), "Quanti": st.column_config.NumberColumn("Quanti", min_value=1.0, step=1.0, width="small"),
                                        "Priorità": st.column_config.SelectboxColumn("Priorità", options=_SS_PRIORITA, width="small"), "Chi": st.column_config.TextColumn("Chi", width="small"),
                                        "🗑️": st.column_config.CheckboxColumn("🗑️", width="small")})
    cambi = {}
    for i in df.index:
        c = {}
        if bool(mod.loc[i, "Preso"]) != bool(df.loc[i, "Preso"]):
            c["preso"] = bool(mod.loc[i, "Preso"])
        if float(mod.loc[i, "Quanti"] or 1) != float(df.loc[i, "Quanti"]):
            c["quantita"] = float(mod.loc[i, "Quanti"] or 1)
        if mod.loc[i, "Priorità"] != df.loc[i, "Priorità"]:
            c["priorita"] = mod.loc[i, "Priorità"]
        if bool(mod.loc[i, "🗑️"]):
            c["togli"] = True
        if c:
            cambi[i] = c
    if st.button("💾 Salva" + ((" (1 cambio)" if len(cambi) == 1 else f" ({len(cambi)} cambi)") if cambi else ""), key="ss_lc_salva_" + lc_id, type="primary", width="stretch", disabled=not cambi):
        def _fn(d):
            l = next((x for x in d.get("liste") or [] if x.get("id") == lc_id), None)
            if not ss_lc_puo(l, uid):
                raise PermissionError("lista non condivisa con te")
            ss_lc_applica(l, cambi, chi)
            d["versione"] = int(d.get("versione") or 0) + 1
        salva_file(SS_LC, _fn, "Spesa Smart: lista condivisa")
        st.rerun(scope="fragment")
    presi = [r for r in righe if r.get("stato") == "preso" and r.get("preso_da") == chi]
    if presi and st.button(f"📦 Metti in Dispensa quelli che ho preso io ({len(presi)})", key="ss_lc_disp_" + lc_id, width="stretch"):
        st.session_state["ss_in_disp"] = [{"prodotto": {"nome": r.get("nome"), "marca": r.get("marca"), "ean": r.get("ean"), "formato_valore": r.get("formato_valore"),
                                                        "formato_unita": r.get("formato_unita")}, "quantita": r.get("quantita")} for r in presi]
        st.rerun()
    if lista.get("proprietario") == uid:
        with st.expander("⚙️ Lista condivisa"):
            persone_tutte = _ss_persone()
            nuove = st.multiselect("Con chi è condivisa", [i for i, _n in persone_tutte], default=[u for u in lista.get("persone") or [] if u in dict(persone_tutte)],
                                   format_func=dict(persone_tutte).get, key="ss_lc_chi_" + lc_id)
            if st.button("💾 Salva le persone", key="ss_lc_chi_ok_" + lc_id, width="stretch") and nuove:
                salva_file(SS_LC, lambda d: next(x for x in d["liste"] if x["id"] == lc_id).__setitem__("persone", list(nuove)), "Spesa Smart: persone della lista")
                st.rerun()
            if st.button("✅ Chiudi la lista (spesa fatta)", key="ss_lc_chiudi_" + lc_id, width="stretch"):
                salva_file(SS_LC, lambda d: next(x for x in d["liste"] if x["id"] == lc_id).__setitem__("stato", "chiusa"), "Spesa Smart: lista chiusa")
                st.session_state["ss_lista_sel_prossima"] = "__dispensa__"
                st.rerun()


def _ss_lc_vista(lc_id, per_id):
    f = st.fragment(run_every=10)(_ss_lc_corpo) if hasattr(st, "fragment") else _ss_lc_corpo
    f(lc_id, per_id)


def _ss_righe_lista(ss, disp, lid):
    """Le righe da comprare della lista scelta, con il prodotto collegato (o None se non c'è ancora una scheda)."""
    out = []
    if str(lid).startswith("c:"):
        l = next((x for x in _ss_lc_leggi().get("liste") or [] if x.get("id") == lid[2:]), None) or {}
        for r in l.get("righe") or []:
            if r.get("stato") == "preso":
                continue
            p = ss_prodotto_per_riga_disp(ss, {"barcode": r.get("ean"), "nome": r.get("nome"), "marca": r.get("marca")})
            out.append({"prodotto_id": p["id"] if p else None, "quantita": ss_num(r.get("quantita"), 1) or 1, "nome": r.get("nome", "")})
        return out
    if lid == _SS_LISTA_DISP:
        for r in disp.get("spesa", []):
            if r.get("preso"):
                continue
            p = ss_prodotto_per_riga_disp(ss, r)
            out.append({"prodotto_id": p["id"] if p else None, "quantita": ss_num(r.get("q"), 1) or 1, "nome": r.get("nome", "")})
    else:
        for r in ss["liste_righe"]:
            if r.get("lista_id") == lid and r.get("stato") != "preso":
                p = ss_trova(ss, "prodotti", r.get("prodotto_id"))
                out.append({"prodotto_id": r.get("prodotto_id"), "quantita": ss_num(r.get("quantita"), 1) or 1, "nome": (p or {}).get("nome", "?")})
    return out


# ---------------------------------------------------------------------------------------------------------------------
# 13.6 Lista ottimizzata: tre scenari
# ---------------------------------------------------------------------------------------------------------------------
def _ss_html_scenario(ss, lettera, titolo, s, consigliato, altri):
    if not s:
        return (f"<div class='ss-scen'><h4>{lettera}. {titolo}</h4><div>Non c'è una combinazione di più negozi che convenga "
                "(o i prezzi sono di un solo negozio).</div></div>")
    per_neg = {}
    for a in s["assegna"]:
        per_neg.setdefault(a["negozio_id"], []).append(a)
    corpo = ""
    for nid, voci in per_neg.items():
        n = ss_trova(ss, "negozi", nid)
        sub = sum(v["totale"] for v in voci)
        corpo += f"<div class='neg'>🏪 {_ss_esc(ss_nome_negozio(n))} — {ss_euro(sub)}</div>" + "".join(
            f"<div class='r'>• {_ss_esc(v['riga'].get('nome') or (ss_trova(ss, 'prodotti', v['riga']['prodotto_id']) or {}).get('nome', '?'))} × {ss_num(v['riga'].get('quantita'), 1):g}"
            f" = {ss_euro(v['totale'])}</div>" for v in voci)
    risp = "".join(f"<div>Rispetto a {l}: {('risparmi ' + ss_euro(t - s['totale'])) if t > s['totale'] else ('spendi ' + ss_euro(s['totale'] - t) + ' in più') if t < s['totale'] else 'uguale'}</div>"
                   for l, t in altri if t is not None)
    mancano = f"<div>⚠️ {s['scoperti_tot']} prodotti senza prezzo in questi negozi</div>" if s.get("scoperti_tot") else ""
    return (f"<div class='ss-scen{' ok' if consigliato else ''}'><h4>{lettera}. {titolo}{' — ✅ consigliato' if consigliato else ''}</h4>"
            f"<div class='tot'>{ss_euro(s['totale'])}</div><div>{s['n_negozi']} {'negozio' if s['n_negozi'] == 1 else 'negozi'} · spesa {ss_euro(s['spesa'])}"
            + (f" + spostamenti {ss_euro(s['spostamenti'])}" if s["spostamenti"] else "") + f"</div>{risp}{mancano}{corpo}</div>")


def _ss_v_ottimizzata(ss, disp):
    st.markdown("#### 🧮 Lista ottimizzata")
    lid = _ss_scegli_lista(ss, "ss_ott_sel")
    righe = _ss_righe_lista(ss, disp, lid)
    if not righe:
        st.info("La lista è vuota: aggiungi qualcosa in **📝 Lista della spesa**.")
        return
    costo0 = ss_num(ss["impostazioni"].get("costo_negozio"), 0.0) or 0.0
    costo = st.number_input("🚗 Quanto ti costa andare in un negozio in più (benzina, tempo)? €", min_value=0.0, value=float(costo0), step=0.5, format="%.2f", key="ss_ott_costo",
                            help="Se lo lasci a 0 conto solo i prezzi. L'app non ti manda in più negozi se il risparmio è minimo.")
    if abs(costo - costo0) > 0.001:
        _ss_salva(lambda s_: s_["impostazioni"].__setitem__("costo_negozio", costo), "costo spostamento")
    o = ss_ottimizza(ss, righe, ss_oggi(), costo)
    if o["mancano"]:
        st.warning("⚠️ **Confronto incompleto**: per " + str(len(o["mancano"])) + " prodotti non c'è un prezzo valido oggi ("
                   + ", ".join(_ss_esc(r.get("nome") or "?") for r in o["mancano"][:8]) + ("…" if len(o["mancano"]) > 8 else "")
                   + "). I totali qui sotto non li contano.")
    if not o["negozi"]:
        st.info("Non ci sono prezzi validi per questi prodotti: inseriscine qualcuno con **⚡ Inserisci un prezzo**.")
        return
    A, B, C = o["A"], o["B"], o["C"]
    tot = {"A": A["totale"] if A else None, "B": B["totale"] if B else None, "C": C["totale"] if C else None}
    if o["consiglio"] == "A" and (B or (C and C["n_negozi"] > 1)):
        st.info("💡 Girare più negozi farebbe risparmiare poco (meno di " + ss_euro(SS_SOGLIA_EURO) + f" o del {SS_SOGLIA_PCT:g}%): ti consiglio un solo negozio.")
    st.markdown(_ss_html_scenario(ss, "A", "Tutto in un solo negozio", A, o["consiglio"] == "A", [("B", tot["B"]), ("C", tot["C"])]), unsafe_allow_html=True)
    st.markdown(_ss_html_scenario(ss, "B", "Diviso tra due o tre negozi", B, o["consiglio"] == "B", [("A", tot["A"]), ("C", tot["C"])]), unsafe_allow_html=True)
    st.markdown(_ss_html_scenario(ss, "C", "La combinazione più economica", C, o["consiglio"] == "C", [("A", tot["A"]), ("B", tot["B"])]), unsafe_allow_html=True)
    st.caption("Uso solo prezzi validi oggi (offerte in corso e prezzi degli ultimi 30 giorni). Le offerte con tessera sono segnate in **🏆 Dove costa meno**.")


# ---------------------------------------------------------------------------------------------------------------------
# 13.7 Offerte interessanti
# ---------------------------------------------------------------------------------------------------------------------
def _ss_v_offerte(ss, disp):
    st.markdown("#### 🔥 Offerte interessanti")
    st.caption("Solo prezzi validi **oggi**, dalla più conveniente (conta anche quanto è recente il prezzo). Un'offerta conta se è almeno il 5% sotto il prezzo pieno, "
               "un prezzo normale se è almeno il 10% sotto il solito.")
    esau = ss_esauriti_con_offerta(ss, disp, ss_oggi(), _ss_offerte_volantini())
    if esau:
        st.markdown("**🔔 Ti servono (finiti in Dispensa) e sono in offerta:**")
        for nome, testo in esau:
            st.markdown(f"- **{_ss_esc(nome)}**: {_ss_esc(testo)}")
    off = ss_offerte_interessanti(ss, ss_oggi())
    if not off and not esau:
        st.info("Nessuna offerta interessante tra i prezzi che hai salvato. Le offerte dei **volantini** sono in Dispensa → 🛒 Offerte.")
    for i, o in enumerate(off[:40]):
        p, c = o["prodotto"], o["corrente"]
        n = ss_trova(ss, "negozi", c["negozio_id"])
        c1, c2 = st.columns([5, 2], gap="small")
        c1.markdown(f"<div class='ss-card'><div class='t'>{_ss_esc(_ss_etich_prodotto(p))}</div><div class='big'>{ss_euro(c['prezzo'])} <span class='ss-promo'>−{o['risparmio_pct']:.0f}%</span></div>"
                    f"<div class='m'>🏪 {_ss_esc(ss_nome_negozio(n))}" + (f" · fino al {ss_data_it(o['fine'])}" if o["fine"] else "") + (" · 💳 tessera" if c["rilevazione"].get("tessera") else "")
                    + f" · rilevato {('oggi' if o['eta'] == 0 else str(o['eta']) + ' giorni fa')}</div></div>", unsafe_allow_html=True)
        if c2.button("➕ In lista", key=f"ss_off_l{i}", width="stretch"):
            _ss_salva_disp(lambda d, p=p: aggiungi_a_spesa(d, {"nome": p.get("nome"), "marca": p.get("marca", ""), "barcode": p.get("ean", ""), "q": 1}), "offerta in lista")
            st.session_state["ss_msg"] = f"➕ {p.get('nome')} è nella lista della spesa."
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 13.8 Scontrino
# ---------------------------------------------------------------------------------------------------------------------
_SS_NON = "— non salvare —"
_SS_NUOVO = "➕ Nuovo prodotto (con questo nome)"


def _ss_v_scontrino(ss, disp):
    st.markdown("#### 🧾 Scontrino")
    st.caption("Fotografa lo scontrino: leggo negozio, data, prodotti, quantità, prezzi e sconti. **Niente viene salvato finché non confermi**; "
               "le righe incerte restano **senza spunta**.")
    giro = st.session_state.setdefault("ss_sc_giro", 0)
    files = st.file_uploader("Foto o PDF dello scontrino (anche più foto se è lungo)", type=["jpg", "jpeg", "png", "webp", "heic", "pdf"], accept_multiple_files=True, key=f"ss_sc_f{giro}")
    for f_ in files or []:
        if "il_mostra_avvisi_foto" in globals():
            il_mostra_avvisi_foto(f_)
    if files and st.button("🔎 Leggi lo scontrino", type="primary", width="stretch", key=f"ss_sc_leggi{giro}"):
        with st.spinner("🤖 Leggo lo scontrino…"):
            letto = ss_leggi_scontrino(files)
        if not letto:
            st.warning("Non sono riuscito a leggerlo (serve una chiave di intelligenza artificiale in Utilità → 🤖, oppure la foto è poco chiara: più luce, scontrino dritto).")
        else:
            st.session_state["ss_scontrino"] = letto
            st.rerun()
    letto = st.session_state.get("ss_scontrino")
    if not letto:
        return
    righe = ss_pulisci_scontrino(letto)
    st.success(f"Letto con {il_nomi_fonti([letto.get('fonte')]) if 'il_nomi_fonti' in globals() else letto.get('fonte', 'IA')}: {len(righe)} prodotti. Controlla e conferma.")
    neg0 = ss_trova_negozio_da_testo(ss, letto.get("negozio"), letto.get("citta", ""), letto.get("indirizzo", ""))
    ids = [n["id"] for n in ss["negozi"]]
    opz = ids + ["__nuovo__"]
    nomi = {n["id"]: ss_nome_negozio(n) for n in ss["negozi"]}
    neg = st.selectbox("🏪 Negozio", opz, index=opz.index(neg0["id"]) if neg0 else len(opz) - 1, key=f"ss_sc_neg{giro}",
                       format_func=lambda i: ("➕ Nuovo: " + (letto.get("negozio") or "negozio")) if i == "__nuovo__" else nomi[i])
    nn = {}
    if neg == "__nuovo__":
        c1, c2 = st.columns(2, gap="small")
        nn = {"nome": c1.text_input("Nome", value=letto.get("negozio") or "", key=f"ss_sc_nn{giro}"), "citta": c2.text_input("Città", value=letto.get("citta") or "", key=f"ss_sc_nc{giro}"),
              "indirizzo": st.text_input("Indirizzo", value=letto.get("indirizzo") or "", key=f"ss_sc_ni{giro}")}
    data_s = st.date_input("📅 Data", value=ss_data(letto.get("data")) or ss_oggi(), max_value=ss_oggi(), format="DD/MM/YYYY", key=f"ss_sc_d{giro}")
    etich = {}
    for p in ss["prodotti"]:
        e = _ss_etich_prodotto(p)
        while e in etich:
            e += " ·"
        etich[e] = p["id"]
    opzioni = [_SS_NON, _SS_NUOVO] + sorted(etich)
    import pandas as _pd
    tab = []
    for r in righe:
        p, punt = ss_trova_prodotto_da_testo(ss, r["descrizione"])
        lab = next((e for e, i in etich.items() if p and i == p["id"]), None)
        sicura = bool(lab) and not r["incerta"]
        tab.append({"Salva": sicura, "Sullo scontrino": r["descrizione"], "Prodotto": lab or (_SS_NUOVO if not r["incerta"] else _SS_NON), "Quanti": r["quantita"],
                    "Prezzo cad.": r["prezzo_unitario"], "Totale": r["prezzo_totale"], "Sconto": r["sconto"] or 0.0, "": "✅" if sicura else "❓"})
    df = _pd.DataFrame(tab)
    st.caption("❓ = da controllare (prodotto non riconosciuto o prezzo strano): scegli il prodotto giusto, «➕ Nuovo» o lascialo senza spunta.")
    mod = st.data_editor(df, key=f"ss_sc_ed{giro}", hide_index=True, width="stretch", disabled=["Sullo scontrino", ""],
                         column_config={"Salva": st.column_config.CheckboxColumn("Salva", width="small"), "Prodotto": st.column_config.SelectboxColumn("Prodotto", options=opzioni, width="medium"),
                                        "Quanti": st.column_config.NumberColumn("Quanti", min_value=0.001, step=1.0, width="small"),
                                        "Prezzo cad.": st.column_config.NumberColumn("€ cad.", min_value=0.0, step=0.01, format="%.2f", width="small"),
                                        "Totale": st.column_config.NumberColumn("€ totale", min_value=0.0, step=0.01, format="%.2f", width="small"),
                                        "Sconto": st.column_config.NumberColumn("Sconto €", min_value=0.0, step=0.01, format="%.2f", width="small")})
    sel = mod[mod["Salva"] == True]  # noqa: E712
    tot_letto = ss_num(letto.get("totale"))
    somma = round(float(_pd.to_numeric(mod["Totale"], errors="coerce").fillna(0).sum()), 2)
    st.caption(f"Somma delle righe: **{ss_euro(somma)}**" + (f" · totale sullo scontrino: **{ss_euro(tot_letto)}**" + (" ✅" if abs(somma - tot_letto) < 0.06 else " ⚠️ non torna: controlla")
                                                             if tot_letto else ""))
    in_disp = st.checkbox("📦 Dopo, proponimi di mettere questi prodotti in Dispensa", value=True, key=f"ss_sc_disp{giro}")
    b1, b2 = st.columns(2, gap="small")
    if b1.button(f"✅ Conferma e salva ({len(sel)} righe)", type="primary", width="stretch", key=f"ss_sc_ok{giro}", disabled=sel.empty):
        errori = [f"«{r['Sullo scontrino']}»: manca il prezzo" for _i, r in sel.iterrows() if ss_num(r["Totale"]) is None and ss_num(r["Prezzo cad."]) is None]
        errori += [f"«{r['Sullo scontrino']}»: scegli il prodotto" for _i, r in sel.iterrows() if r["Prodotto"] == _SS_NON]
        if neg == "__nuovo__" and not (nn.get("nome") or "").strip():
            errori.append("Scrivi il nome del negozio.")
        if errori:
            for e in errori:
                st.warning(e)
            return
        esito = {"prodotti": []}

        def _fn(s_):
            n = ss_trova(s_, "negozi", neg) if neg != "__nuovo__" else ss_aggiungi_negozio(s_, nn)[0]
            sid = ss_id()
            s_["scontrini"].append({"id": sid, "negozio_id": n["id"], "data": data_s.isoformat(), "totale": tot_letto, "righe": len(sel), "creato_il": ss_ora(),
                                    "fonte": letto.get("fonte", "")})
            for _i, r in sel.iterrows():
                if r["Prodotto"] == _SS_NUOVO:
                    p, _x = ss_aggiungi_prodotto(s_, {"nome": str(r["Sullo scontrino"]).strip().capitalize()})
                else:
                    p = ss_trova(s_, "prodotti", etich.get(r["Prodotto"]))
                    if not p:
                        continue
                desc = str(r["Sullo scontrino"]).strip()
                if ss_norm(desc) != ss_norm(p.get("nome")) and desc not in (p.get("alias") or []):
                    p.setdefault("alias", []).append(desc)                    # la prossima volta lo riconosco da solo
                q = ss_num(r["Quanti"], 1) or 1
                totale = ss_num(r["Totale"]) if ss_num(r["Totale"]) is not None else round((ss_num(r["Prezzo cad."], 0) or 0) * q, 2)
                pu = ss_num(r["Prezzo cad."]) or round(totale / q, 2)
                ss_registra_acquisto(s_, p["id"], n["id"], q, totale, data=data_s.isoformat(), scontrino_id=sid, prezzo_unitario=pu, sconto=ss_num(r["Sconto"], 0))
                esito["prodotti"].append({"prodotto": dict(p), "quantita": q})
            s_["impostazioni"]["ultimo_negozio"] = n["id"]
        try:
            _ss_salva(_fn, "scontrino")
        except Exception as e:
            st.error(f"Non salvato: {e}")
            return
        st.session_state.pop("ss_scontrino", None)
        st.session_state["ss_sc_giro"] = giro + 1
        st.session_state["ss_msg"] = f"🧾 Scontrino salvato: {len(esito['prodotti'])} acquisti e prezzi."
        if in_disp and esito["prodotti"]:
            st.session_state["ss_in_disp"] = esito["prodotti"]
        st.rerun()
    if b2.button("✖ Annulla", width="stretch", key=f"ss_sc_no{giro}"):
        st.session_state.pop("ss_scontrino", None)
        st.session_state["ss_sc_giro"] = giro + 1
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# 13.9 Archivio prodotti e negozi
# ---------------------------------------------------------------------------------------------------------------------
def _ss_v_prodotti(ss, disp):
    st.markdown("#### 📦 Archivio prodotti")
    st.caption("È **un solo archivio con la Dispensa**: i prodotti che hai in Dispensa o in lista compaiono da soli (segnati «dalla Dispensa»); la scheda si crea al primo prezzo.")
    cat = ss_catalogo(ss, disp)
    f = st.text_input("🔎 Cerca", key="ss_pr_f", placeholder="nome, marca, codice a barre")
    if f:
        fp = ss_parole(f)
        cat = [p for p in cat if fp & ss_parole(" ".join(str(p.get(k) or "") for k in ("nome", "marca", "variante", "categoria"))) or f.strip() == str(p.get("ean") or "")]
    with st.popover("➕ Nuovo prodotto", width="stretch"):
        nuovo = _ss_campi_prodotto("ss_pr_new")
        if st.button("💾 Salva", key="ss_pr_new_ok", type="primary", width="stretch"):
            err = ss_valida_prodotto(nuovo)
            if err:
                for e in err:
                    st.warning(e)
            else:
                esito = {}
                _ss_salva(lambda s_: esito.__setitem__("x", ss_aggiungi_prodotto(s_, nuovo)), "nuovo prodotto")
                st.session_state["ss_msg"] = ("✅ Prodotto creato." if esito["x"][1] else "ℹ️ Esisteva già: ho completato la sua scheda (niente doppioni).")
                st.rerun()
    st.caption(f"{len(cat)} prodotti")
    for p in sorted(cat, key=lambda p: ss_norm(p.get("nome")))[:150]:
        n_pr = sum(1 for r in ss["rilevazioni"] if r.get("prodotto_id") == p["id"])
        c1, c2 = st.columns([5, 1], gap="small")
        c1.markdown(f"**{_ss_esc(p.get('nome'))}** " + _ss_esc(" · ".join(x for x in (p.get("marca"), p.get("variante"), ss_fmt_formato(p), p.get("categoria")) if x))
                    + (f" · `{p['ean']}`" if p.get("ean") else "") + (f" · {n_pr} prezzi" if n_pr else "") + (" · _dalla Dispensa_" if p.get("_virtuale") else ""))
        if p.get("_virtuale"):
            continue
        with c2.popover("✏️"):
            m = _ss_campi_prodotto("ss_pr_" + p["id"], p)
            if st.button("💾 Salva", key="ss_pr_ok_" + p["id"], type="primary", width="stretch"):
                err = ss_valida_prodotto(m)
                dop = ss_cerca_doppione(ss, m, escludi=p["id"])
                if err or dop:
                    for e in err + ([f"Esiste già uguale: {_ss_etich_prodotto(dop)} — usa «Unisci»."] if dop else []):
                        st.warning(e)
                else:
                    _ss_salva(lambda s_, i=p["id"]: ss_trova(s_, "prodotti", i).update({k: v for k, v in m.items() if k != "immagine" or v}), "prodotto modificato")
                    st.rerun()
            altri = [x["id"] for x in ss["prodotti"] if x["id"] != p["id"]]
            if altri:
                dove = st.selectbox("🔗 È un doppione di…", altri, index=None, format_func=lambda i: _ss_etich_prodotto(ss_trova(ss, "prodotti", i)), key="ss_pr_u_" + p["id"])
                if dove and st.button("Unisci (prezzi e acquisti passano all'altro)", key="ss_pr_uok_" + p["id"], width="stretch"):
                    _ss_salva(lambda s_, a=dove, b=p["id"]: ss_unisci(s_, "prodotti", a, b), "prodotti uniti")
                    st.rerun()
            if ss_riferimenti(ss, "prodotti", p["id"]):
                st.caption("Ha prezzi o acquisti: non si elimina (puoi unirlo a un altro).")
            elif st.button("🗑️ Elimina", key="ss_pr_del_" + p["id"], width="stretch"):
                _ss_salva(lambda s_, i=p["id"]: ss_elimina(s_, "prodotti", i), "prodotto eliminato")
                st.rerun()


def _ss_v_negozi(ss, disp):
    st.markdown("#### 🏪 Archivio negozi")
    with st.popover("➕ Nuovo negozio", width="stretch"):
        c1, c2 = st.columns(2, gap="small")
        n = {"nome": c1.text_input("Nome *", key="ss_ng_n", placeholder="es. Lidl"), "catena": c2.text_input("Catena / insegna", key="ss_ng_c", placeholder="es. Lidl"),
             "citta": c1.text_input("Città", key="ss_ng_ci"), "indirizzo": c2.text_input("Indirizzo", key="ss_ng_i")}
        if st.button("💾 Salva", key="ss_ng_ok", type="primary", width="stretch"):
            if not n["nome"].strip():
                st.warning("Scrivi il nome.")
            else:
                esito = {}
                n["catena"] = n["catena"].strip() or n["nome"].strip()
                _ss_salva(lambda s_: esito.__setitem__("x", ss_aggiungi_negozio(s_, n)), "nuovo negozio")
                st.session_state["ss_msg"] = "✅ Negozio aggiunto." if esito["x"][1] else "ℹ️ C'era già (stesso nome, città e indirizzo)."
                st.rerun()
    if not ss["negozi"]:
        st.info("Nessun negozio: si aggiungono anche mentre inserisci un prezzo.")
    per_catena = {}
    for x in ss["negozi"]:
        per_catena.setdefault(x.get("catena") or x.get("nome") or "?", []).append(x)
    for catena, punti in sorted(per_catena.items(), key=lambda kv: ss_norm(kv[0])):
        st.markdown(f"**{_ss_esc(catena)}**" + (f" · {len(punti)} punti vendita" if len(punti) > 1 else ""))
        for x in punti:
            n_pr = sum(1 for r in ss["rilevazioni"] if r.get("negozio_id") == x["id"])
            c1, c2 = st.columns([5, 1], gap="small")
            c1.markdown(f"🏪 {_ss_esc(ss_nome_negozio(x))}" + (f" · {n_pr} prezzi" if n_pr else ""))
            with c2.popover("✏️"):
                m = {"nome": st.text_input("Nome", value=x.get("nome", ""), key="ss_ng_n_" + x["id"]), "catena": st.text_input("Catena", value=x.get("catena", ""), key="ss_ng_c_" + x["id"]),
                     "citta": st.text_input("Città", value=x.get("citta", ""), key="ss_ng_ci_" + x["id"]), "indirizzo": st.text_input("Indirizzo", value=x.get("indirizzo", ""), key="ss_ng_i_" + x["id"])}
                if st.button("💾 Salva", key="ss_ng_ok_" + x["id"], type="primary", width="stretch") and m["nome"].strip():
                    _ss_salva(lambda s_, i=x["id"]: ss_trova(s_, "negozi", i).update({k: v.strip() for k, v in m.items()}), "negozio modificato")
                    st.rerun()
                altri = [y["id"] for y in ss["negozi"] if y["id"] != x["id"]]
                if altri:
                    dove = st.selectbox("🔗 È un doppione di…", altri, index=None, format_func=lambda i: ss_nome_negozio(ss_trova(ss, "negozi", i)), key="ss_ng_u_" + x["id"])
                    if dove and st.button("Unisci", key="ss_ng_uok_" + x["id"], width="stretch"):
                        _ss_salva(lambda s_, a=dove, b=x["id"]: ss_unisci(s_, "negozi", a, b), "negozi uniti")
                        st.rerun()
                if ss_riferimenti(ss, "negozi", x["id"]):
                    st.caption("Ha prezzi o acquisti: non si elimina (puoi unirlo a un altro).")
                elif st.button("🗑️ Elimina", key="ss_ng_del_" + x["id"], width="stretch"):
                    _ss_salva(lambda s_, i=x["id"]: ss_elimina(s_, "negozi", i), "negozio eliminato")
                    st.rerun()


# =====================================================================================================================
# 14. AGGANCI: pulsante sotto Dispensa, smistamento, badge, Home, guida
# =====================================================================================================================
try:
    if "SEZIONI_NAV" in globals() and "spesa_smart" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(SEZIONI_NAV.index("dispensa") + 1 if "dispensa" in SEZIONI_NAV else 1, "spesa_smart")
    if "NOMI_NAV" in globals():
        NOMI_NAV["spesa_smart"] = "Spesa Smart"
    if "_PN_VOCI" in globals() and not any(v_[0] == "spesa_smart" for v_ in _PN_VOCI):
        _i_ss = next((i_ for i_, v_ in enumerate(_PN_VOCI) if v_[0] == "salute"), 1) + 1     # griglia a 2 colonne: subito SOTTO Dispensa
        _PN_VOCI.insert(_i_ss, ("spesa_smart", "🛒 Spesa Smart", SS_COLORI[0], SS_COLORI[1]))
    if "SC_ESCLUSE" in globals() and "spesa_smart" not in SC_ESCLUSE:
        SC_ESCLUSE = tuple(SC_ESCLUSE) + ("spesa_smart",)
    if "_SEZ_VALIDE" in globals():
        _SEZ_VALIDE.add("spesa_smart")
except Exception:
    pass

if "schermata_farmacia" in globals() and "_ss_schermata_prima" not in globals():
    _ss_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "spesa_smart":
            return schermata_spesa_smart()
        return _ss_schermata_prima()

if "nav_pagine" in globals() and "_ss_nav_prima" not in globals():
    _ss_nav_prima = nav_pagine

    def nav_pagine(corrente):                                        # noqa: F811
        r = _ss_nav_prima(corrente)
        if corrente in ("dispensa", "spesa_smart"):
            try:
                ss_switch(corrente)                                    # 📦 Scorte | 🛒 Spesa Smart
            except Exception:
                pass
        if corrente != "spesa_smart":
            st.markdown("<style>.st-key-navp_spesa_smart button{border-color:rgba(0,230,168,.95) !important;box-shadow:0 0 12px rgba(0,230,168,.6),0 4px 0 rgba(0,0,0,.25) !important}</style>",
                        unsafe_allow_html=True)
        return r

if "consuma_uno" in globals() and "_ss_consuma_prima" not in globals():
    _ss_consuma_prima = consuma_uno

    def consuma_uno(d, id_riga):                                     # noqa: F811 — finito in Dispensa → in lista (come prima) + avviso se oggi è in offerta
        esito = _ss_consuma_prima(d, id_riga)
        try:
            if esito.get("stato") == "finito":
                ss, _disp = _ss_leggi()
                riga = {"nome": esito.get("nome", ""), "preso": False}
                riga.update(next((x for x in d.get("spesa", []) if ss_norm(x.get("nome")) == ss_norm(esito.get("nome"))), {}))
                v = ss_esauriti_con_offerta(ss, {"spesa": [riga]}, ss_oggi(), _ss_offerte_volantini())
                if v:
                    st.session_state["ss_avviso"] = f"🔥 {v[0][0]} è finito ed è in offerta: {v[0][1]}."
        except Exception:
            pass
        return esito


if "pn_scadenze" in globals() and "_ss_scad_prima" not in globals():
    _ss_scad_prima = pn_scadenze

    def pn_scadenze():                                               # noqa: F811
        out = _ss_scad_prima()
        try:
            ss, disp = _ss_leggi()
            v = ss_esauriti_con_offerta(ss, disp, ss_oggi(), _ss_offerte_volantini())
            if v:
                out["spesa_smart"] = [f"🛒 {n}: {t}" for n, t in v]
        except Exception:
            pass
        return out

if "_vm_riepilogo" in globals() and "_ss_riep_prima" not in globals():
    _ss_riep_prima = _vm_riepilogo

    def _vm_riepilogo(sc):                                           # noqa: F811 — in Home, sotto i pulsanti: 🛒 Spesa Smart (con il numero delle offerte utili)
        try:
            st.markdown(_SS_CSS, unsafe_allow_html=True)
            n = len(sc.get("spesa_smart") or pn_scadenze().get("spesa_smart") or [])
            st.button("🛒 Spesa Smart" + (f" · 🔔 {n} in offerta" if n else ""), key="vm_ss", on_click=vm_apri, args=("spesa_smart",))
        except Exception:
            pass
        return _ss_riep_prima({k: v for k, v in sc.items() if k != "spesa_smart"})

if "_NOMI_SEZIONI" in globals():
    _NOMI_SEZIONI.setdefault("spesa_smart", "🛒 Spesa Smart")
    if "_ID_GUIDA" in globals():
        _ID_GUIDA.setdefault("spesa_smart", ["ss_cosa", "ss_prezzo", "ss_dcm", "ss_ott", "ss_scontrino", "ss_badge"])
    if "UI_IT" in globals():
        UI_IT.setdefault("sez_spesa_smart", "🛒 Spesa Smart")
    _GUIDE.setdefault("spesa_smart", [
        ("🛒 Cos'è Spesa Smart",
         """È la seconda parte della **Dispensa**: in alto scegli **📦 Scorte** (la dispensa di sempre) o **🛒 Spesa Smart**.
Qui salvi i **prezzi** dei negozi dove fai la spesa e l'app ti dice **dove costa meno**, quali **offerte** valgono davvero, prepara la **spesa ottimizzata** e legge gli **scontrini**.
L'archivio dei prodotti è **lo stesso della Dispensa** e la lista della spesa principale è **la lista della Dispensa** (condivisa con la famiglia).""",
         "spesa smart prezzi negozi confronto offerte lista ottimizzata scontrino dispensa"),
        ("⚡ Inserire un prezzo (3 tocchi)",
         """1. **⚡ Inserisci un prezzo** → scegli il **prodotto** (scrivi per cercare; oppure **📷 Leggi il codice a barre**; oppure **➕ Nuovo prodotto**).
2. Il **negozio** resta quello dell'ultima volta (toccane un altro o **➕ Nuovo negozio**).
3. Scrivi il **prezzo** e tocca **💾 Salva**. L'app calcola da sola il prezzo **al kg, al litro o al pezzo**.
In **🏷️ Offerta, formato…** metti il prezzo in offerta con le date, se serve la tessera, un formato diverso, le note. Con **🧾 L'ho comprato adesso** registri anche l'acquisto e l'app ti propone di **aggiornare le scorte**.""",
         "inserire prezzo codice a barre negozio offerta tessera formato al kg al litro acquisto"),
        ("🏆 Dove costa meno e 🔥 Offerte",
         """**🏆 Dove costa meno**: per ogni prodotto il prezzo più basso **valido oggi**, il negozio, il prezzo al kg/litro/pezzo, la classifica degli altri negozi e la data. Ordina per prezzo, risparmio o data.
Un prezzo vale **30 giorni**; dopo diventa **🟠 da verificare** (non entra nei confronti) e dopo 90 giorni scade. Un'offerta finita **non** viene mai mostrata come valida.
**🔥 Offerte interessanti**: solo quelle davvero convenienti (sotto il prezzo pieno o sotto il solito), prima le più recenti. In cima quelle dei prodotti **finiti in Dispensa**.""",
         "dove costa meno classifica negozi prezzo unitario offerte valide scadute da verificare"),
        ("🧮 Spesa ottimizzata",
         """Scegli la lista: l'app prepara tre proposte: **A** tutto in un solo negozio, **B** diviso tra due o tre negozi, **C** la combinazione più economica. Per ognuna: cosa comprare e dove, totale, risparmio e numero di negozi.
Se vuoi, scrivi quanto ti costa andare in un negozio in più: **se il risparmio è piccolo** l'app ti consiglia un solo negozio. Se mancano prezzi lo dice chiaramente.""",
         "lista ottimizzata scenari un negozio più negozi risparmio costo spostamento"),
        ("🧾 Scontrino",
         """Fotografa lo scontrino e tocca **🔎 Leggi lo scontrino**: l'intelligenza artificiale legge negozio, data, prodotti, quantità, prezzi e sconti.
Controlla la tabella: le righe sicure hanno ✅, quelle incerte ❓ e **restano senza spunta**. Per ogni riga scegli il prodotto giusto o **➕ Nuovo**. Tocca **✅ Conferma e salva**: diventano acquisti e prezzi, e l'app impara il nome scritto sullo scontrino.
Poi ti propone di **mettere i prodotti in Dispensa**.""",
         "scontrino foto leggere prodotti prezzi sconti conferma acquisti dispensa"),
        ("🔔 Il numero sul pulsante",
         """Il pulsante **🛒 Spesa Smart** si illumina con un numero quando dei prodotti **finiti in Dispensa** (nella lista della spesa) sono **in offerta oggi** (tra i tuoi prezzi o nei volantini). Il conto si rifà da solo e ogni prodotto conta una volta sola.""",
         "badge numero pulsante offerte prodotti finiti"),
    ])
