# -*- coding: utf-8 -*-
"""Tre sezioni per i prodotti: adulti, neonati (0-2 anni), animali.
Nomi, ricerca nel database giusto per ogni sezione, tabella 'Gestisci'."""

CATEGORIE = {"adulti": ("🧑", "Adulti"), "neonati": ("👶", "Neonati (0-2 anni)"), "animali": ("🐾", "Animali")}


def categoria_di(r):
    """Sezione di un prodotto (i prodotti salvati prima di questa novita' sono 'adulti')."""
    c = (r or {}).get("per_chi")
    return c if c in CATEGORIE else "adulti"


def icona_cat(c):
    return CATEGORIE.get(c, CATEGORIE["adulti"])[0]


def nome_cat(c):
    icona, nome = CATEGORIE.get(c, CATEGORIE["adulti"])
    return f"{icona} {t(nome)}"


# ---------- ricerca del prodotto nel database giusto ----------
BASI_DATI = {
    "adulti": ["world.openfoodfacts.org"],
    "neonati": ["world.openfoodfacts.org", "world.openproductsfacts.org"],       # latte in polvere, pappe, pannolini...
    "animali": ["world.openpetfoodfacts.org", "world.openfoodfacts.org"],
}


@st.cache_data(ttl=3600, show_spinner=False)
def _cerca_in(base, codice):
    """None = non trovato; {'errore': ...} = problema di rete; altrimenti il prodotto."""
    try:
        r = requests.get(f"https://{base}/api/v2/product/{codice}.json",
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


def cerca_prodotto(codice, sezione="adulti"):
    """Cerca il codice nei database della sezione (nell'ordine); None se non c'e' da nessuna parte."""
    errore = None
    for base in BASI_DATI.get(sezione, BASI_DATI["adulti"]):
        r = _cerca_in(base, codice)
        if r and "errore" not in r:
            return r
        if r:
            errore = r
    return errore


# ---------- adattamenti per le sezioni ----------
_badge_base = badge_allergeni


def badge_allergeni(r, mie):
    """Per gli animali gli allergeni 'umani' non servono: niente etichette."""
    return "" if categoria_di(r) == "animali" else _badge_base(r, mie)


_mostra_scheda_base = mostra_scheda


def mostra_scheda(p, mie, mostra_link=True):
    if categoria_di(p) == "animali":
        mie = ["*"]                      # nessun suggerimento sulle allergie delle persone
    _mostra_scheda_base(p, mie, mostra_link)


def applica_modifiche(d, modificata):
    """Applica alla dispensa le modifiche fatte nella tabella 'Gestisci' (compresa la sezione)."""
    inverso = {nome_cat(c): c for c in CATEGORIE}
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
        if "Per chi" in modificata.columns and m["Per chi"] in inverso:
            r["per_chi"] = inverso[m["Per chi"]]
        if r["quantita"] > 0:
            nuovi.append(r)           # 0 unita' = finito: lo tolgo dalla dispensa
    d["articoli"] = nuovi
