# -*- coding: utf-8 -*-
"""ANIMALI · DOCUMENTI — lettura, riconoscimento, classificazione e archivio dei documenti veterinari.

Riusa i sistemi già presenti: il caricamento (pulsante arancione, fotocamera, galleria: casa.py), la lettura del testo con OCR (ca_estrai_testo: PDF con testo, PDF scansionati, foto),
l'archivio dei file (documenti/<utente>/<id>.json, lo stesso di Salute), l'invio (invio.py: inv_voce, inv_canali: telefono, email, WhatsApp, Telegram).
Cosa fa con un documento (referti, certificati, prescrizioni, fatture, libretti sanitari, passaporti, cartelle cliniche…):
  1 lo legge · 2 ne riconosce il tipo (con i motivi) · 3 estrae date, scadenze, microchip, vaccini, importi, veterinario e clinica · 4 propone a quale animale appartiene
  (se non è sicuro CHIEDE) · 5 mostra tutto da controllare e correggere · 6 archivia l'ORIGINALE identico e rende ricercabile il testo · 7 segnala ciò che manca o è illeggibile
  · 8 propone promemoria per le scadenze.
Caricato dopo animali.py."""
import io
import re
import zipfile
from datetime import date

import streamlit as st

AN_TIPI_DOC = {
    "Certificato di vaccinazione": True, "Libretto sanitario / Passaporto": True, "Certificato": True, "Referto / Esame": True, "Prescrizione / Ricetta": True,
    "Cartella clinica / Dimissione": True, "Intervento chirurgico": True, "Fattura / Ricevuta": False, "Microchip / Anagrafe": False, "Pedigree / Origine": False,
    "Assicurazione": False, "Fotografia": False, "Altro": False,
}
AN_EMOJI_DOC = {"Certificato di vaccinazione": "💉", "Libretto sanitario / Passaporto": "📘", "Certificato": "📜", "Referto / Esame": "🔬", "Prescrizione / Ricetta": "📝",
                "Cartella clinica / Dimissione": "🏥", "Intervento chirurgico": "🔪", "Fattura / Ricevuta": "🧾", "Microchip / Anagrafe": "🔖", "Pedigree / Origine": "🏅",
                "Assicurazione": "🛡️", "Fotografia": "📷", "Altro": "📄"}
_AN_REGOLE = {
    "Certificato di vaccinazione": [(r"certificato (di )?vaccinazion", 6), (r"vaccinazione antirabbic", 5), (r"vaccin", 2), (r"\blotto\b", 1), (r"richiamo", 1), (r"rabbia|antirabbic", 2),
                                    (r"trivalente|tetravalente|esavalente|nobivac|eurican|vanguard|feligen|purevax|versiguard", 3), (r"parvovirosi|cimurro|leptospirosi|calicivirosi|panleucopenia", 2)],
    "Libretto sanitario / Passaporto": [(r"passaporto", 6), (r"pet passport|passeport|animal health", 5), (r"libretto sanitario", 6), (r"passaporto europeo", 3), (r"\btitolare\b", 1)],
    "Certificato": [(r"\bcertificat", 4), (r"buona salute", 4), (r"idoneit", 3), (r"si certifica|certifico", 4), (r"viaggio|espatrio|trasferimento", 1)],
    "Referto / Esame": [(r"referto", 5), (r"\besito\b", 2), (r"emocromo|ematochimic|biochimic|urinocolt|coprologic|esame delle urine|esame delle feci", 4),
                        (r"ecograf|radiograf|\brx\b|\btac\b|risonanza|elettrocardiogram|\becg\b", 4), (r"\bvalori\b", 1), (r"analisi", 2), (r"laborator", 2),
                        (r"valori di riferimento|range|intervallo di riferimento", 2), (r"citolog|istolog", 4), (r"snap test|test rapido|leishmania|filaria|felv|\bfiv\b", 2)],
    "Prescrizione / Ricetta": [(r"prescrizione", 5), (r"ricetta", 4), (r"posologia", 4), (r"\brp[:.\s]", 3), (r"somministrare|somministrazione", 2), (r"compresse|\bcpr\b|fiale|gocce|sciroppo", 1),
                               (r"ricetta elettronica|ricetta (medico )?veterinaria", 3)],
    "Cartella clinica / Dimissione": [(r"dimission", 5), (r"ricovero", 4), (r"degenza", 4), (r"cartella clinica", 5), (r"anamnesi", 3), (r"lettera di", 1)],
    "Intervento chirurgico": [(r"intervento chirurgic", 5), (r"anestesi", 3), (r"sterilizzazione|castrazione|ovarioisterectomia|ovariectomia|orchiectomia", 5), (r"chirurg", 3), (r"sutur", 2)],
    "Fattura / Ricevuta": [(r"fattura", 5), (r"ricevuta", 4), (r"scontrino", 3), (r"\btotale\b", 2), (r"\biva\b|i\.v\.a", 2), (r"imponibile", 3), (r"partita iva|p\.iva", 2), (r"pagament|pagato", 1)],
    "Microchip / Anagrafe": [(r"anagrafe", 4), (r"\bmicrochip", 2), (r"transponder", 4), (r"iscrizione (all )?anagrafe", 5), (r"tatuaggio", 2)],
    "Pedigree / Origine": [(r"pedigree", 6), (r"\benci\b", 3), (r"libro genealogico", 5), (r"allevament", 2), (r"cucciolata", 2)],
    "Assicurazione": [(r"polizza", 5), (r"assicurazione", 3), (r"massimale", 3), (r"franchigia", 3)],
}
_AN_MESI = {"gennaio": 1, "gen": 1, "febbraio": 2, "feb": 2, "marzo": 3, "mar": 3, "aprile": 4, "apr": 4, "maggio": 5, "mag": 5, "giugno": 6, "giu": 6, "luglio": 7, "lug": 7,
            "agosto": 8, "ago": 8, "settembre": 9, "set": 9, "sett": 9, "ottobre": 10, "ott": 10, "novembre": 11, "nov": 11, "dicembre": 12, "dic": 12}
_AN_VACCINI = [("Rabbia", r"rabbia|antirabbic"), ("Parvovirosi", r"parvovir|\bcpv\b"), ("Cimurro", r"cimurro|\bcdv\b"), ("Epatite infettiva (adenovirus)", r"epatite|adenovir|\bcav\b"),
               ("Leptospirosi", r"leptospir"), ("Parainfluenza", r"parainfluenz|\bcpiv\b"), ("Tosse dei canili (Bordetella)", r"bordetella|tosse dei canili"), ("Leishmaniosi", r"leishman"),
               ("Rinotracheite (herpesvirus felino)", r"rinotracheite|herpesvirus|\bfhv\b"), ("Calicivirosi", r"calicivir|\bfcv\b"), ("Panleucopenia", r"panleucopen|\bfpv\b"),
               ("Leucemia felina (FeLV)", r"leucemia felina|\bfelv\b"), ("Clamidiosi", r"clamid"), ("Mixomatosi", r"mixomat"), ("Malattia emorragica virale (RHD)", r"\brhd\b|emorragica virale"),
               ("Polivalente / trivalente / tetravalente", r"polivalente|trivalente|tetravalente|esavalente|dhppi|dhpp")]
_AN_PREVENZIONE = [("Antiparassitario", r"antiparassitari|frontline|advantage|nexgard|bravecto|simparica|seresto|spot[- ]on|collare antiparass"), ("Vermifugo", r"vermifug|drontal|milbemax|antielmintic")]


def _an_estrai(nome, mime, dati):
    """(testo, info, errore): il testo del documento, con gli stessi metodi di Casa (PDF con testo, PDF scansionato, foto con OCR)."""
    try:
        if "ca_estrai_testo" in globals():
            testo, info = ca_estrai_testo(nome, mime, dati)
            return testo or "", info or {}, ""
        if mime == "application/pdf":
            try:
                import pymupdf as _mu
            except Exception:
                import fitz as _mu
            doc = _mu.open(stream=dati, filetype="pdf")
            return "\n".join(p.get_text("text") for p in doc), {"pagine": doc.page_count, "metodo": "testo del PDF"}, ""
    except Exception as ex:
        return "", {}, f"{type(ex).__name__}"
    return "", {}, ""


def an_trova_date(testo):
    """[(date, ruolo, vicino)] — tutte le date del testo, ognuna col ruolo letto dalle parole prima: scadenza, richiamo, controllo, data."""
    t = an_norm(testo)
    trovate = []

    def _agg(g, m, a, pos):
        try:
            a = int(a)
            if a < 100:
                a += 2000 if a < 70 else 1900
            d_ = date(a, int(m), int(g))
        except (ValueError, TypeError):
            return
        if not (1990 <= d_.year <= 2100):
            return
        prima = t[max(0, pos - 48):pos]
        if re.search(r"scadenz|scade|valid\w* fino|validit|fino al|entro il", prima):
            ruolo = "scadenza"
        elif re.search(r"richiamo|prossim\w* (vaccin|somministr|dose)|revaccin|booster|rinnovo", prima):
            ruolo = "richiamo"
        elif re.search(r"controllo|prossima visita|ricontroll|rivalutazion|appuntament|tornare", prima):
            ruolo = "controllo"
        else:
            ruolo = "data"
        trovate.append((d_, ruolo, pos))
    for m in re.finditer(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4}|\d{2})\b", t):
        _agg(m.group(1), m.group(2), m.group(3), m.start())
    for m in re.finditer(r"\b(\d{1,2})\s+(" + "|".join(sorted(_AN_MESI, key=len, reverse=True)) + r")\.?\s+(\d{4})\b", t):
        _agg(m.group(1), _AN_MESI[m.group(2)], m.group(3), m.start())
    for m in re.finditer(r"\b(20\d{2})-(\d{2})-(\d{2})\b", t):
        _agg(m.group(3), m.group(2), m.group(1), m.start())
    visti, out = set(), []
    for d_, ruolo, pos in sorted(trovate, key=lambda z: z[2]):
        if (d_, ruolo) in visti:
            continue
        visti.add((d_, ruolo))
        out.append((d_, ruolo, pos))
    return out


def an_classifica(testo, nome_file=""):
    """(tipo, sicuro, motivi, punteggi) — il tipo di documento più probabile e le parole che hanno deciso."""
    t = an_norm(testo)
    n = an_norm(nome_file)
    punti, motivi = {}, {}
    for tipo, regole in _AN_REGOLE.items():
        s, parole = 0, []
        for pat, peso in regole:
            m = re.search(pat, t)
            if m:
                s += peso
                parole.append(m.group(0).strip())
            if re.search(pat, n):
                s += 3
                parole.append("nome del file: " + re.search(pat, n).group(0))
        punti[tipo] = s
        motivi[tipo] = parole[:4]
    ordine = sorted(punti.items(), key=lambda z: -z[1])
    tipo, s = ordine[0]
    if s < 3:
        return "Altro", False, [], punti
    secondo = ordine[1][1] if len(ordine) > 1 else 0
    sicuro = s >= 5 and s - secondo >= 2
    return tipo, sicuro, motivi[tipo], punti


def an_abbina_animale(testo, animali, microchip_doc=None):
    """(id, sicuro, motivi): a quale animale sembra appartenere il documento. Il microchip è una prova; il nome, un indizio. In dubbio: id vuoto o non sicuro."""
    t = an_norm(testo)
    punti = {}
    motivi = {}
    chip_doc = an_solo_cifre(microchip_doc) if microchip_doc else ""
    cifre_testo = re.findall(r"\d{15}", re.sub(r"(?<=\d)[ .\-](?=\d)", "", t))
    for x in animali:
        s, m = 0, []
        chip = an_solo_cifre(x.get("microchip"))
        if len(chip) == 15 and (chip in cifre_testo or chip == chip_doc):
            s += 10
            m.append(f"c'è il suo microchip ({chip})")
        nome = an_norm(x.get("nome")).strip()
        if len(nome) >= 3 and re.search(r"\b" + re.escape(nome) + r"\b", t):
            s += 4
            m.append(f"c'è il nome «{x.get('nome')}»")
        razza = an_norm(x.get("razza")).strip()
        if len(razza) >= 4 and razza in t:
            s += 1
            m.append(f"c'è la razza «{x.get('razza')}»")
        punti[x["id"]] = s
        motivi[x["id"]] = m
    if not punti:
        return "", False, []
    ordine = sorted(punti.items(), key=lambda z: -z[1])
    aid, s = ordine[0]
    secondo = ordine[1][1] if len(ordine) > 1 else 0
    if s >= 10 or (s >= 4 and s - secondo >= 4):
        return aid, True, motivi[aid]
    if s >= 1 and s > secondo:
        return aid, False, motivi[aid]
    return "", False, []


def an_leggi_documento(nome, mime, dati, animali):
    """Legge un documento e ritorna la proposta da far controllare (vedi il modulo)."""
    testo, info, errore = _an_estrai(nome, mime, dati)
    testo = testo or ""
    nt = an_norm(testo)
    soli_testo = re.sub(r"\s+", "", testo)
    lettere = sum(c.isalpha() for c in soli_testo)
    qualita = (lettere / len(soli_testo)) if soli_testo else 0.0
    es_foto = str(mime).startswith("image/")
    mancanti, note = [], []
    if es_foto and len(soli_testo) < 25:
        tipo, sicuro, motivi = "Fotografia", False, ["la foto non contiene testo leggibile"]
        mancanti.append("Non ho potuto leggere testo nella foto: se è un documento, scegli tu il tipo; se è una foto dell'animale, va bene così.")
    else:
        tipo, sicuro, motivi, _p = an_classifica(testo, nome)
        if len(soli_testo) < 40:
            mancanti.append("Il testo del documento è quasi vuoto o illeggibile: controlla i dati a mano.")
        elif qualita < 0.55:
            mancanti.append("Il testo è poco leggibile (lettura imprecisa): controlla bene date e numeri.")
    # --- le date
    date_t = an_trova_date(testo)
    oggi_ = _an_oggi()
    data_doc = next((d_ for d_, r, _p in date_t if r == "data" and d_ <= oggi_), None) or next((d_ for d_, r, _p in date_t if d_ <= oggi_ and r == "data"), None)
    if data_doc is None:
        passate = [d_ for d_, r, _p in date_t if d_ <= oggi_]
        data_doc = min(passate) if passate else None
    scadenza = next((d_ for d_, r, _p in date_t if r == "scadenza"), None)
    richiamo = next((d_ for d_, r, _p in date_t if r == "richiamo"), None)
    controllo = next((d_ for d_, r, _p in date_t if r == "controllo"), None)
    if scadenza is None and richiamo is not None and tipo in ("Certificato di vaccinazione", "Libretto sanitario / Passaporto"):
        scadenza = richiamo
    if data_doc is None and tipo != "Fotografia":
        mancanti.append("Non trovo la data del documento.")
    if tipo == "Certificato di vaccinazione" and richiamo is None and scadenza is None:
        mancanti.append("Non trovo la data del prossimo richiamo.")
    # --- i campi
    campi = {}
    m = re.search(r"(?<!\d)(\d{3}[ .\-]?\d{3}[ .\-]?\d{3}[ .\-]?\d{3}[ .\-]?\d{3})(?!\d)", testo)
    if m:
        campi["microchip"] = an_solo_cifre(m.group(1))
    m = re.search(r"\b(?i:dott\.?(?:ssa)?|dr\.?(?:ssa)?|dottor(?:e|essa)?)\s+([A-ZÀ-Ý][\w'’\-]+(?:\s+[A-ZÀ-Ý][\w'’\-]+){0,2})", testo)
    if m:
        campi["veterinario"] = m.group(1).strip()
    m = re.search(r"((?:clinica|ambulatorio|ospedale|studio|centro)\s+(?:veterinari[oa]|zoo\w*)[^\n]{0,50})", testo, re.I)
    if m:
        campi["clinica"] = re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"totale[^\d\n]{0,25}(?:€|eur\w*)?\s*(\d{1,6}(?:[.,]\d{2}))", nt)
    if m:
        campi["importo"] = m.group(1).replace(",", ".")
    for chiave, pats in (("terapia", (r"(?:posologia|rp[:.]|somministrare)[:\s]*", r"prescrizione\s*:\s*")),
                         ("esito", (r"conclusion\w*[:\s]*", r"esito\s*:\s*", r"commento\s*:\s*", r"referto\s*:\s*")), ("diagnosi", (r"diagnosi\s*:\s*",))):
        lung = 60 if chiave == "diagnosi" else 200
        for pat in pats:
            mm = re.search(pat + r"([^\n]{3," + str(lung) + r"}(?:\n[^\n]{3,120}){0,2})" if chiave != "diagnosi" else pat + r"([^\n]{3,200})", testo, re.I)
            if mm:
                campi[chiave] = re.sub(r"[ \t]+", " ", mm.group(1)).strip()[:300]
                break
    vacc = []
    for nome_v, pat in _AN_VACCINI:
        if re.search(pat, nt):
            vacc.append({"nome": nome_v, "tipo": "Vaccino"})
    for nome_v, pat in _AN_PREVENZIONE:
        if re.search(pat, nt):
            vacc.append({"nome": nome_v, "tipo": nome_v})
    if tipo != "Certificato di vaccinazione" and tipo != "Libretto sanitario / Passaporto":
        vacc = [v for v in vacc if v["tipo"] != "Vaccino"] if not re.search(r"vaccin", nt) else vacc
    # --- l'animale
    aid, a_sicuro, a_motivi = an_abbina_animale(testo, animali, campi.get("microchip"))
    if not aid:
        mancanti.append("Non so a quale animale appartiene: sceglilo tu.")
    elif not a_sicuro:
        mancanti.append("Non sono sicuro dell'animale: controlla che sia quello giusto.")
    # --- promemoria
    promemoria = []
    for d_, ruolo, _p in date_t:
        if d_ > oggi_ or (ruolo in ("scadenza", "richiamo", "controllo") and (oggi_ - d_).days <= 60):
            if ruolo in ("scadenza", "richiamo", "controllo") or d_ > oggi_:
                promemoria.append({"data": d_.isoformat(), "tipo": {"scadenza": "Controllo", "richiamo": "Vaccino / richiamo", "controllo": "Visita"}.get(ruolo, "Altro"),
                                   "titolo": {"scadenza": "Scadenza", "richiamo": "Richiamo", "controllo": "Controllo veterinario"}.get(ruolo, "Appuntamento") + f" — {tipo}"})
    visti, uniche = set(), []
    for p in promemoria:
        if (p["data"], p["titolo"]) not in visti:
            visti.add((p["data"], p["titolo"]))
            uniche.append(p)
    titolo_meta = str((info or {}).get("titolo") or "").strip()
    return {"tipo": tipo, "tipo_sicuro": sicuro, "motivi": motivi, "data": data_doc.isoformat() if data_doc else "", "scadenza": scadenza.isoformat() if scadenza else "",
            "richiamo": richiamo.isoformat() if richiamo else "", "controllo": controllo.isoformat() if controllo else "", "campi": campi, "vaccini": vacc,
            "animale": aid, "animale_sicuro": a_sicuro, "animale_motivi": a_motivi, "mancanti": mancanti, "promemoria": uniche[:6], "testo": testo[:9000],
            "metodo": (info or {}).get("metodo") or ("lettura non riuscita" if errore else ""), "pagine": (info or {}).get("pagine"), "titolo_file": titolo_meta,
            "qualita": round(qualita, 2), "errore": errore, "date_trovate": [(d_.isoformat(), r) for d_, r, _p in date_t][:12]}


def an_titolo_automatico(tipo, nome_animale, data_iso, campi=None):
    base = tipo + (f" — {nome_animale}" if nome_animale else "")
    return base + (f" ({an_data_it(data_iso)})" if data_iso else "")


# ---------------------------------------------------------------------------------------------------------------------
# archiviare: il file originale + la scheda del documento + le voci collegate
# ---------------------------------------------------------------------------------------------------------------------
def an_archivia_documento(nome, mime, dati, prop, scelte):
    """Salva l'originale identico e crea la scheda del documento e le voci scelte. prop = proposta (poi corretta dall'utente). Ritorna (id_documento, esito)."""
    aid = scelte["animale"]
    a0 = an_dati()
    esistenti = [r for d_ in an_voci(a0, "documenti", aid) for r in (d_.get("allegati") or [])]
    rif = an_salva_originale(nome, dati, esistenti=esistenti, mime=mime)
    if rif.get("doppione"):
        return None, "Questo file è già archiviato per questo animale (identico): non l'ho salvato due volte."
    rif = {k: v for k, v in rif.items() if k != "doppione"}
    did = an_nuovo_id()
    fonte_doc = "veterinario" if AN_TIPI_DOC.get(scelte["tipo"]) else "proprietario"
    fonte = scelte.get("fonte") or fonte_doc

    def _m(a):
        ora = _an_adesso()
        doc = {"id": did, "animale": aid, "tipo": scelte["tipo"], "titolo": scelte["titolo"], "data": scelte.get("data") or "", "scadenza": scelte.get("scadenza") or "",
               "allegati": [rif], "campi": {k: v for k, v in (scelte.get("campi") or {}).items() if v not in (None, "")}, "testo": prop.get("testo", "")[:9000],
               "mancanti": list(prop.get("mancanti") or []), "classificazione": "automatica" if scelte["tipo"] == prop.get("tipo") else "corretta dall'utente",
               "tipo_proposto": prop.get("tipo"), "metodo_lettura": prop.get("metodo") or "", "fonte": fonte, "creato": ora, "agg": ora, "origine": {"tipo": "caricato qui"}}
        a["documenti"].append(doc)
        for v in scelte.get("vaccini") or []:
            a["vaccini"].append({"id": an_nuovo_id(), "animale": aid, "tipo": v.get("tipo") or "Vaccino", "nome": v["nome"], "data": scelte.get("data") or "",
                                 "richiamo": scelte.get("richiamo") or "", "lotto": "", "vet": (scelte.get("campi") or {}).get("veterinario", ""), "note": "", "fonte": "veterinario",
                                 "doc": did, "creato": ora, "agg": ora, "origine": {"tipo": "da documento", "doc": did}})
        for cat in scelte.get("crea") or []:
            base = {"id": an_nuovo_id(), "animale": aid, "doc": did, "creato": ora, "agg": ora, "origine": {"tipo": "da documento", "doc": did}}
            c = scelte.get("campi") or {}
            if cat == "esami":
                a["esami"].append(dict(base, data=scelte.get("data") or "", tipo=scelte["tipo"], esito=c.get("esito", ""), vet=c.get("veterinario", ""), note="", fonte="veterinario"))
            elif cat == "visite":
                a["visite"].append(dict(base, data=scelte.get("data") or "", motivo=scelte["tipo"], vet=c.get("veterinario", ""), clinica=c.get("clinica", ""), diagnosi=c.get("diagnosi", ""),
                                        indicazioni=c.get("terapia", ""), costo=c.get("importo", ""), prossimo=scelte.get("controllo") or "", note="", fonte="veterinario"))
            elif cat == "interventi":
                a["interventi"].append(dict(base, tipo="Intervento chirurgico", data=scelte.get("data") or "", fine="", descrizione=c.get("diagnosi") or c.get("esito") or scelte["titolo"],
                                            clinica=c.get("clinica", ""), note="", fonte="veterinario"))
            elif cat == "spese":
                a["spese"].append(dict(base, data=scelte.get("data") or "", voce=scelte["titolo"], importo=c.get("importo", ""), note=""))
        for p in scelte.get("promemoria") or []:
            a["agenda"].append({"id": an_nuovo_id(), "animale": aid, "data": p["data"], "ora": "", "titolo": p["titolo"], "tipo": p.get("tipo") or "Altro", "note": "Proposto dalla lettura del documento",
                                "doc": did, "fatto": False, "creato": ora, "agg": ora, "origine": {"tipo": "da documento", "doc": did}})
        x = an_trova(a, aid)
        if x is not None:
            c = scelte.get("campi") or {}
            if c.get("microchip") and not x.get("microchip") and scelte.get("microchip_alla_scheda"):
                x["microchip"] = c["microchip"]
            x["agg"] = ora
    try:
        an_salva(_m, "Animali: documento")
    except Exception:
        an_cancella_file([rif["id"]])
        raise
    return did, ""


# ---------------------------------------------------------------------------------------------------------------------
# la schermata dei documenti
# ---------------------------------------------------------------------------------------------------------------------
def _an_ricevi_documento():
    n = f"andoc{st.session_state.get('an_giro', 0)}"
    return _an_riceve_file(n)


def _an_form_bozza(a, x, bz):
    """Il controllo prima di archiviare: tutto ciò che ho letto, da correggere."""
    prop = bz["prop"]
    animali = an_animali(a)
    k = f"an_bz_{bz['sha'][:10]}_"
    st.markdown("<div class='an-card'><b class='t'>🔎 Ho letto il documento: controlla e conferma</b><div class='s'>Il file originale resta com'è. Quello che trovi qui sotto è solo una proposta: puoi correggere tutto.</div></div>", unsafe_allow_html=True)
    mime = bz["mime"]
    if mime.startswith("image/"):
        st.image(bz["dati"], width="stretch")
    else:
        st.caption(f"📄 {bz['nome']} · {len(bz['dati']) // 1024} KB" + (f" · {prop['pagine']} pagine" if prop.get("pagine") else ""))
    st.caption(f"Lettura: {prop.get('metodo') or 'non riuscita'}" + (f" · qualità del testo {int(prop.get('qualita', 0) * 100)}%" if prop.get("testo") else ""))
    for mc in prop.get("mancanti") or []:
        st.warning("⚠️ " + mc)
    tipi = list(AN_TIPI_DOC)
    st.markdown(("✅ **Tipo riconosciuto**" if prop["tipo_sicuro"] else "❓ **Tipo da controllare**") + (" — " + ", ".join(prop["motivi"]) if prop.get("motivi") else ""))
    tipo = st.selectbox("Tipo di documento", tipi, index=tipi.index(prop["tipo"]), key=k + "tipo")
    st.markdown(("✅ **Animale riconosciuto**" if prop["animale_sicuro"] else "❓ **Dimmi tu a quale animale appartiene**") + (" — " + ", ".join(prop["animale_motivi"]) if prop.get("animale_motivi") else ""))
    opz = {an_etichetta_animale(z): z["id"] for z in animali}
    nomi = list(opz)
    if prop["animale_sicuro"] or (len(animali) == 1):
        ind = list(opz.values()).index(prop["animale"]) if prop["animale"] in opz.values() else (list(opz.values()).index(x["id"]) if x else 0)
        scelta = st.selectbox("Animale", nomi, index=ind, key=k + "animale")
    else:
        pre = ["— scegli l'animale —"] + nomi
        ind = pre.index(next(n for n, i in opz.items() if i == prop["animale"])) if prop["animale"] in opz.values() else 0
        scelta = st.selectbox("Animale", pre, index=ind, key=k + "animale")
    aid = opz.get(scelta, "")
    nome_an = an_nome(a, aid) if aid else ""
    titolo = st.text_input("Titolo", value=prop.get("titolo_file") or an_titolo_automatico(tipo, nome_an, prop["data"]), key=k + f"titolo_{tipo}_{aid}").strip()
    data = st.date_input("Data del documento", value=an_data(prop["data"]), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=k + "data")
    scad = st.date_input("Scadenza o prossimo richiamo (se c'è)", value=an_data(prop["scadenza"] or prop["richiamo"]), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=k + "scad")
    c = prop["campi"]
    campi = {"veterinario": st.text_input("Veterinario", value=c.get("veterinario", ""), key=k + "vet").strip(), "clinica": st.text_input("Clinica o ambulatorio", value=c.get("clinica", ""), key=k + "cli").strip(),
             "microchip": st.text_input("Microchip trovato", value=c.get("microchip", ""), key=k + "chip").strip(), "importo": st.text_input("Importo (€)", value=c.get("importo", ""), key=k + "imp").strip(),
             "diagnosi": st.text_input("Diagnosi scritta nel documento", value=c.get("diagnosi", ""), key=k + "dia").strip(),
             "esito": st.text_area("Esito / conclusioni (copiate dal documento)", value=c.get("esito", ""), key=k + "esi", height=80).strip(),
             "terapia": st.text_area("Terapia o indicazioni scritte nel documento", value=c.get("terapia", ""), key=k + "ter", height=80).strip()}
    chip_scheda = False
    if campi["microchip"] and aid and not (an_trova(a, aid) or {}).get("microchip"):
        chip_scheda = st.checkbox("Scrivi questo microchip nella scheda dell'animale (ora è vuoto)", key=k + "chipscheda")
    fonti = list(AN_FONTI_LUNGHE)
    fonte = st.radio("Le informazioni di questo documento sono…", fonti, index=0 if AN_TIPI_DOC.get(tipo) else 1, format_func=lambda z: AN_FONTI_LUNGHE[z], key=k + f"fonte_{tipo}")
    vacc_scelti = []
    if prop["vaccini"]:
        st.markdown("**💉 Vaccini e trattamenti trovati** — spunta quelli da registrare nelle vaccinazioni")
        for i, v in enumerate(prop["vaccini"]):
            if st.checkbox(f"{v['nome']}" + (f" ({v['tipo']})" if v["tipo"] != "Vaccino" else ""), value=bool(data and aid), key=k + f"v{i}"):
                vacc_scelti.append(v)
    crea = []
    if aid and data:
        opzioni_crea = {"Referto / Esame": ("esami", "🔬 Registra anche come esame"), "Cartella clinica / Dimissione": ("visite", "🩺 Registra anche come visita"),
                        "Intervento chirurgico": ("interventi", "🏥 Registra anche come intervento"), "Fattura / Ricevuta": ("spese", "💶 Registra anche come spesa")}
        if tipo in opzioni_crea and (tipo != "Fattura / Ricevuta" or campi["importo"]):
            cat, et = opzioni_crea[tipo]
            if st.checkbox(et, value=False, key=k + "crea"):
                crea.append(cat)
    prom_scelti = []
    if prop["promemoria"]:
        st.markdown("**🔔 Promemoria proposti** — spunta quelli da mettere nell'agenda")
        for i, p in enumerate(prop["promemoria"]):
            if st.checkbox(f"{an_data_it(p['data'])} · {p['titolo']}", value=bool(aid), key=k + f"p{i}"):
                prom_scelti.append(p)
    if prop.get("testo"):
        with st.expander("📜 Testo letto dal documento (serve per cercarlo)"):
            st.text(prop["testo"][:3000])
    c1, c2 = st.columns(2, gap="small")
    if c1.button("✅ Conferma e archivia", type="primary", key=k + "ok", width="stretch"):
        if not aid:
            st.error("Scegli prima a quale animale appartiene il documento.")
            return
        if not titolo:
            st.error("Scrivi un titolo.")
            return
        scelte = {"animale": aid, "tipo": tipo, "titolo": titolo, "data": data.isoformat() if data else "", "scadenza": scad.isoformat() if scad else "",
                  "richiamo": scad.isoformat() if scad else "", "controllo": prop.get("controllo") or "", "campi": campi, "fonte": fonte, "vaccini": vacc_scelti, "crea": crea,
                  "promemoria": prom_scelti, "microchip_alla_scheda": chip_scheda}
        try:
            with st.spinner("Archivio il documento…"):
                did, errore = an_archivia_documento(bz["nome"], bz["mime"], bz["dati"], prop, scelte)
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare: {ex}")
            return
        if errore:
            st.warning(errore)
            return
        st.session_state.pop("an_bozza", None)
        st.session_state["an_giro"] = st.session_state.get("an_giro", 0) + 1
        st.session_state["an_sel"] = aid
        st.session_state["messaggio"] = f"✅ Documento archiviato in «{tipo}» per {an_nome(an_dati(), aid)}, con il file originale identico."
        st.rerun()
    if c2.button("✖ Scarta", key=k + "no", width="stretch"):
        st.session_state.pop("an_bozza", None)
        st.session_state["an_giro"] = st.session_state.get("an_giro", 0) + 1
        st.rerun()


def an_zip_documenti(docs):
    """Un file ZIP con gli originali dei documenti (nomi unici) e un indice."""
    buf = io.BytesIO()
    usati = set()
    righe = ["Documenti veterinari — originali identici ai file caricati\n"]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for d_ in docs:
            for r in d_.get("allegati") or []:
                dati = an_leggi_file(r)
                if not dati:
                    continue
                nome = re.sub(r"[\\/:*?\"<>|]+", "_", r.get("nome") or "file")
                base, _, est = nome.rpartition(".")
                cand, n = nome, 1
                while cand in usati:
                    n += 1
                    cand = f"{base or nome} ({n})" + (f".{est}" if base else "")
                usati.add(cand)
                z.writestr(cand, dati)
                righe.append(f"{cand}\t{d_.get('tipo', '')}\t{d_.get('titolo', '')}\t{an_data_it(d_.get('data'))}")
        z.writestr("INDICE.txt", "\n".join(righe))
    return buf.getvalue()


def an_allegati_invio(docs):
    """[(nome, mime, byte)] degli originali, per gli strumenti di invio."""
    out = []
    for d_ in docs:
        for r in d_.get("allegati") or []:
            dati = an_leggi_file(r)
            if dati:
                out.append((r.get("nome") or "file", r.get("mime") or an_mime_da_nome(r.get("nome"), dati), dati))
    return out


def an_testo_riepilogo_doc(a, docs):
    righe = ["Documenti veterinari"]
    for d_ in docs:
        righe.append(f"• {d_.get('titolo', '')} ({d_.get('tipo', '')}, {an_nome(a, d_.get('animale'))}" + (f", {an_data_it(d_['data'])}" if d_.get("data") else "") + ")")
    return "\n".join(righe)


@st.dialog("✏️ Correggi il documento")
def _an_dialogo_correggi(did):
    a = an_dati()
    d_ = next((z for z in an_voci(a, "documenti") if z.get("id") == did), None)
    if not d_:
        st.error("Documento non trovato.")
        return
    k = f"an_cd_{did}_"
    tipi = list(AN_TIPI_DOC)
    if d_.get("tipo") not in tipi:
        tipi.append(d_.get("tipo"))
    tipo = st.selectbox("Tipo di documento", tipi, index=tipi.index(d_.get("tipo")) if d_.get("tipo") in tipi else 0, key=k + "tipo")
    animali = an_animali(a)
    opz = {an_etichetta_animale(z): z["id"] for z in animali}
    nomi = list(opz)
    ind = list(opz.values()).index(d_.get("animale")) if d_.get("animale") in opz.values() else 0
    sc = st.selectbox("Animale", nomi, index=ind, key=k + "an")
    titolo = st.text_input("Titolo", value=d_.get("titolo", ""), key=k + "tit").strip()
    data = st.date_input("Data", value=an_data(d_.get("data")), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=k + "data")
    scad = st.date_input("Scadenza", value=an_data(d_.get("scadenza")), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=k + "scad")
    campi = dict(d_.get("campi") or {})
    for kk, et in (("veterinario", "Veterinario"), ("clinica", "Clinica"), ("importo", "Importo"), ("diagnosi", "Diagnosi"), ("esito", "Esito"), ("terapia", "Terapia")):
        campi[kk] = st.text_input(et, value=campi.get(kk, ""), key=k + kk).strip()
    fonti = list(AN_FONTI_LUNGHE)
    fonte = st.radio("Le informazioni sono…", fonti, index=fonti.index(d_.get("fonte")) if d_.get("fonte") in fonti else 1, format_func=lambda z: AN_FONTI_LUNGHE[z], key=k + "fonte")
    if st.button("✅ Salva la correzione", type="primary", key=k + "ok", width="stretch"):
        def _m(a2):
            r = next((z for z in a2["documenti"] if z.get("id") == did), None)
            if r is not None:
                if tipo != r.get("tipo"):
                    r["classificazione"] = "corretta dall'utente"
                r.update({"tipo": tipo, "animale": opz[sc], "titolo": titolo or r.get("titolo"), "data": data.isoformat() if data else "", "scadenza": scad.isoformat() if scad else "",
                          "campi": {kk: vv for kk, vv in campi.items() if vv}, "fonte": fonte, "agg": _an_adesso()})
                r["mancanti"] = [mm for mm in (r.get("mancanti") or []) if "animale" not in mm.lower()] if opz[sc] else r.get("mancanti")
        an_salva(_m, "Animali: documento corretto")
        st.session_state["messaggio"] = "✅ Correzione salvata (il file originale non è stato toccato)."
        st.rerun()
    if st.button("🔄 Rileggi il documento e proponimi i dati", key=k + "rileggi", width="stretch"):
        rif = (d_.get("allegati") or [{}])[0]
        dati = an_leggi_file(rif) if rif.get("id") else None
        if not dati:
            st.error("Non trovo il file originale.")
            return
        with st.spinner("Rileggo…"):
            prop = an_leggi_documento(rif.get("nome") or "", rif.get("mime") or "", dati, animali)
        st.info(f"Proposta della lettura: **{prop['tipo']}**" + (f" · data {an_data_it(prop['data'])}" if prop["data"] else "") + (f" · scadenza {an_data_it(prop['scadenza'])}" if prop["scadenza"] else "")
                + ". Se ti sembra giusto, scegli tu i valori qui sopra: la classificazione di prima non è stata cambiata.")


def an_lista_documenti(a, aid, chiave="doc", tutti_animali=False):
    """L'elenco dei documenti con ricerca, filtri, apertura dell'originale, correzione, invio, esportazione multipla."""
    docs = an_voci(a, "documenti", None if tutti_animali else aid)
    if not docs:
        st.caption("Nessun documento archiviato.")
        return
    q = st.text_input("🔎 Cerca nei documenti (titolo, parole lette, veterinario…)", key=f"an_dq_{chiave}_{aid}").strip()
    tipi = sorted({d_.get("tipo") or "Altro" for d_ in docs})
    ft = st.multiselect("Tipo", tipi, key=f"an_dt_{chiave}_{aid}")
    if q:
        nq = an_norm(q)
        docs = [d_ for d_ in docs if nq in an_testo_voce("documenti", d_)]
    if ft:
        docs = [d_ for d_ in docs if (d_.get("tipo") or "Altro") in ft]
    docs = an_ordina(docs, "data")
    st.caption(f"{len(docs)} documenti")
    scelti = []
    for d_ in docs[:60]:
        did = d_["id"]
        mancanti = bool(d_.get("mancanti"))
        c0, c1 = st.columns([1, 6], gap="small")
        if c0.checkbox("sel", key=f"an_ds_{chiave}_{did}", label_visibility="collapsed"):
            scelti.append(d_)
        det = " · ".join(z for z in (an_data_it(d_.get("data")), an_nome(a, d_.get("animale")) if tutti_animali else "", ("scade " + an_data_it(d_["scadenza"])) if d_.get("scadenza") else "") if z)
        extra = "<span class='an-badge att'>da completare</span>" if mancanti else ""
        c1.markdown(f"<div class='an-card {'vet' if d_.get('fonte') == 'veterinario' else 'prop'}'><div class='t'>{AN_EMOJI_DOC.get(d_.get('tipo'), '📄')} {_an_e(d_.get('titolo'))}</div>"
                    f"<div><span class='an-badge tipo'>{_an_e(d_.get('tipo'))}</span>{an_badge_fonte(d_)}{extra}</div><div class='s'>{_an_e(det)}</div></div>", unsafe_allow_html=True)
        kapri = f"an_apri_{chiave}_{did}"
        if st.button("🙈 Chiudi" if st.session_state.get(kapri) else "👁️ Apri, scarica, invia", key=f"an_dap_{chiave}_{did}", width="stretch",
                     on_click=lambda k=kapri: st.session_state.__setitem__(k, not st.session_state.get(k))):
            pass
        if st.session_state.get(kapri):
            for r in d_.get("allegati") or []:
                dati = an_leggi_file(r)
                if not dati:
                    st.error("Il file originale non si trova più.")
                    continue
                if str(r.get("mime", "")).startswith("image/"):
                    st.image(dati, width="stretch")
                st.download_button(f"⬇ Scarica l'originale ({r.get('nome', 'file')})", dati, file_name=r.get("nome") or "file", mime=r.get("mime") or "application/octet-stream",
                                   key=f"an_dl_{chiave}_{did}_{r.get('id')}", width="stretch")
            for mm in d_.get("mancanti") or []:
                st.warning("⚠️ " + mm)
            cmp_ = d_.get("campi") or {}
            if cmp_:
                st.markdown("<div class='an-card'>" + "".join(f"<div class='an-riga'><b>{_an_e(k.capitalize())}</b><span>{_an_e(v)}</span></div>" for k, v in cmp_.items()) + "</div>", unsafe_allow_html=True)
            st.caption(f"Classificazione: {d_.get('classificazione', '')}" + (f" (proposto: {d_['tipo_proposto']})" if d_.get("tipo_proposto") and d_["tipo_proposto"] != d_.get("tipo") else ""))
            e1, e2 = st.columns(2, gap="small")
            if e1.button("✏️ Correggi", key=f"an_dco_{chiave}_{did}", width="stretch"):
                _an_dialogo_correggi(did)
            if e2.button("🗑️ Elimina", key=f"an_dde_{chiave}_{did}", width="stretch"):
                _an_dialogo_elimina("documenti", did, d_.get("titolo") or "documento")
            if "inv_voce" in globals():
                inv_voce(f"andoc_{chiave}_{did}", "📤 Invia questo documento", d_.get("titolo") or "Documento veterinario", an_testo_riepilogo_doc(a, [d_]), lambda d2=d_: an_allegati_invio([d2]))
    if len(docs) > 60:
        st.caption("Ce ne sono altri: usa la ricerca.")
    if scelti:
        st.markdown(f"<div class='an-card'><b class='t'>{len(scelti)} documenti scelti</b></div>", unsafe_allow_html=True)
        z = an_zip_documenti(scelti)
        st.download_button(f"📦 Scarica i {len(scelti)} originali in un file ZIP", z, file_name="documenti_animali.zip", mime="application/zip", key=f"an_zip_{chiave}_{aid}", width="stretch")
        if "inv_voce" in globals():
            inv_voce(f"andocm_{chiave}_{aid}", f"📤 Invia i {len(scelti)} documenti scelti", "Documenti veterinari", an_testo_riepilogo_doc(a, scelti), lambda s=scelti: an_allegati_invio(s))


def an_tab_documenti(a, x):
    st.markdown("#### 📂 Documenti")
    st.caption("Carica un referto, un certificato, una prescrizione, una fattura, il libretto o il passaporto: PDF, foto o scansione. Lo leggo, lo riconosco e ti dico dove lo metto.")
    if st.session_state.pop("an_doc_carica", False):
        st.session_state["an_doc_aperto"] = True
    if st.button("🙈 Chiudi il caricamento" if st.session_state.get("an_doc_aperto") else "📎 Carica un documento", key="an_doc_btn", type="primary", width="stretch",
                 on_click=lambda: st.session_state.__setitem__("an_doc_aperto", not st.session_state.get("an_doc_aperto"))):
        pass
    bz = st.session_state.get("an_bozza")
    if st.session_state.get("an_doc_aperto") and not bz:
        arr = _an_ricevi_documento()
        if arr:
            nome, dati = arr
            mime = an_mime_da_nome(nome, dati)
            if mime == "application/octet-stream" or mime == "image/heic":
                st.error("Questo tipo di file non lo so leggere: manda un PDF o una foto (JPG, PNG, WebP).")
            elif len(dati) > AN_MAX_FILE:
                st.error(f"Il file è troppo grande ({len(dati) // 1024 // 1024} MB): il massimo è 8 MB.")
            else:
                with st.spinner("Leggo il documento… (le foto possono richiedere qualche secondo)"):
                    prop = an_leggi_documento(nome, mime, dati, an_animali(a))
                st.session_state["an_bozza"] = {"nome": nome, "mime": mime, "dati": dati, "sha": an_sha(dati), "prop": prop}
                st.rerun()
    if bz:
        _an_form_bozza(a, x, bz)
        return
    tutti = st.checkbox("Mostra i documenti di tutti gli animali", key="an_doc_tutti") if len(an_animali(a)) > 1 else False
    an_lista_documenti(a, x["id"], chiave="doc", tutti_animali=tutti)
