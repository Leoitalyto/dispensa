# -*- coding: utf-8 -*-
"""Dove si trova il prodotto: Dispensa, Frigo, Freezer, Cantina, Negozio, Magazzino, Altro.
Caricato da app_dispensa.py dopo stile2.py e prima di parte3.py e parte4.py."""

POSTI = {"dispensa": "🏠", "frigo": "❄️", "freezer": "🧊", "cantina": "📦", "negozio": "🏪", "magazzino": "🏭", "altro": "➕"}
_NOMI_POSTI = {"dispensa": "Dispensa", "frigo": "Frigo", "freezer": "Freezer", "cantina": "Cantina",
               "negozio": "Negozio", "magazzino": "Magazzino", "altro": "Altro"}


def nome_posto_scelta(chiave):
    """Icona + nome del posto, come compare nella casella a discesa (nella lingua dell'utente)."""
    chiave = chiave if chiave in POSTI else "dispensa"
    return f"{POSTI[chiave]} {t(_NOMI_POSTI[chiave])}"


def posto_di(r):
    """Il posto di un prodotto (quelli vecchi, senza posto, sono in dispensa)."""
    p = r.get("posto") or "dispensa"
    return p if p in POSTI else "dispensa"


def etichetta_posto(r):
    """Cosa scrivere sulla scheda: per 'Altro' il nome scelto dall'utente."""
    p = posto_di(r)
    if p == "altro" and (r.get("posto_altro") or "").strip():
        return "📍 " + r["posto_altro"].strip()
    return nome_posto_scelta(p)


# la scheda del prodotto mostra dove si trova
_scheda_html_senza_posto = scheda_html


def scheda_html(r, data_oggi, mie):
    h = _scheda_html_senza_posto(r, data_oggi, mie)
    chip = f"<div class='posto-chip'>{html.escape(etichetta_posto(r))}</div>"
    return h.replace("<span class='scadenza'>", chip + "<span class='scadenza'>", 1)


# la tabella 'Gestisci' puo' cambiare il posto di un prodotto
_applica_modifiche_senza_posto = applica_modifiche


def applica_modifiche(d, modificata):
    _applica_modifiche_senza_posto(d, modificata)
    if "Posto" not in modificata.columns:
        return
    inverso = {nome_posto_scelta(k): k for k in POSTI}
    for r in d.get("articoli", []):
        if r.get("id") in modificata.index:
            nuovo = inverso.get(modificata.loc[r["id"], "Posto"])
            if nuovo and nuovo != posto_di(r):
                r["posto"] = nuovo
                if nuovo != "altro":
                    r["posto_altro"] = ""


CSS = CSS.replace("</style>", """
.posto-chip{display:inline-flex;align-items:center;gap:5px;width:fit-content;max-width:100%;background:#E3F3EF;border:1px solid rgba(13,140,121,.28);
 border-radius:999px;padding:3px 11px;font-weight:700;font-size:.8rem;color:#0B5F52;margin:2px 6px 2px 0}
</style>""")
