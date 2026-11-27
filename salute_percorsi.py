"""🗂️ PERCORSI DI CURA (Salute) — una cartella unica per una cura lunga (dentista, fisioterapia, ortodonzia…):
preventivo, appuntamenti, piano dei pagamenti (rate), pagamenti fatti con le ricevute, documenti e un diario, tutto insieme.

Dati: d["farmacia"]["percorsi"] = [{
    id, profilo, titolo, tipo, stato ("In corso" | "Concluso" | "Sospeso"), creato_il, note,
    struttura {nome, indirizzo, telefoni[], email, medico, partita_iva},
    preventivo {numero, data, totale, righe[{descrizione, dente, importo}], note},
    appuntamenti [{id, data, ora, cosa, note, fatto, esito}],
    rate [{id, scadenza, importo, nota}],                     piano dei pagamenti (vuoto = pagamento libero)
    pagamenti [{id, data, importo, metodo, riferimento, nota, fattura, allegati[]}],
    documenti [{id, titolo, categoria, data, allegati[]}],
    diario [{id, data, testo}] }]
Gli AVVISI (WhatsApp, Telegram, email, anche ad app chiusa) li dà lo Scadenziario: appuntamenti non ancora fatti (categoria «visite»)
e rate non ancora coperte dai pagamenti (categoria «pagamenti») — vedi _sz_f_salute in scadenziario_core.py.
Le rate si considerano pagate in ordine di scadenza: il totale pagato copre prima la rata più vecchia (non serve collegare ogni bonifico alla sua rata).
"""
import base64 as _pc_b64
import html as _pc_html
import re as _pc_re
import uuid as _pc_uuid
from datetime import date as _pc_date, timedelta as _pc_td

PC_TIPI = ["🦷 Dentista", "🏃 Fisioterapia", "👁️ Oculistica", "🦴 Ortopedia", "🩺 Specialistica", "🏥 Intervento / ricovero", "📋 Altro"]
PC_STATI = ["In corso", "Sospeso", "Concluso"]
PC_METODI = ["Bonifico", "Carta / Bancomat", "Contanti", "Finanziamento", "Assegno", "Altro"]
PC_CAT_DOC = ["Preventivo", "Promemoria appuntamento", "Fattura", "Ricevuta di pagamento", "Consenso informato", "Radiografia / esame",
              "Piano di cura", "Contratto di finanziamento", "Altro"]
_PC_MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
_PC_GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


# =====================================================================================================================
# LOGICA (senza Streamlit: si prova da sola)
# =====================================================================================================================
def pc_id():
    return _pc_uuid.uuid4().hex[:10]


def pc_d(x):
    try:
        return _pc_date.fromisoformat(str(x)[:10]) if x else None
    except Exception:
        return None


def pc_num(x):
    """«7.500,00» → 7500.0 · «1000» → 1000.0 · 12.5 → 12.5 · vuoto/non valido → None."""
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace("€", "").replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") == 1 and len(s.split(".")[1]) == 3:
        s = s.replace(".", "")                                     # «7.500» = settemilacinquecento
    try:
        return float(s)
    except ValueError:
        return None


def pc_euro(x):
    n = pc_num(x) or 0.0
    s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def pc_data_it(x):
    d = pc_d(x)
    return d.strftime("%d/%m/%Y") if d else ""


def pc_data_lunga(x):
    d = pc_d(x)
    return f"{_PC_GIORNI[d.weekday()]} {d.day} {_PC_MESI[d.month - 1]} {d.year}" if d else ""


def pc_nuovo(titolo, profilo, oggi_=None):
    return {"id": pc_id(), "profilo": profilo or "p0", "titolo": (titolo or "Percorso di cura").strip(), "tipo": PC_TIPI[0], "stato": "In corso",
            "creato_il": (oggi_ or _pc_date.today()).isoformat(), "note": "",
            "struttura": {"nome": "", "indirizzo": "", "telefoni": [], "email": "", "medico": "", "partita_iva": ""},
            "preventivo": {"numero": "", "data": "", "totale": None, "righe": [], "note": ""},
            "appuntamenti": [], "rate": [], "pagamenti": [], "documenti": [], "diario": []}


def pc_aggiungi_mesi(d, n):
    import calendar
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))


def pc_genera_rate(totale, n_rate, prima, ogni_mesi=1, acconto=0.0, data_acconto=None):
    """Il piano: (acconto) + n rate uguali ogni «ogni_mesi» mesi dalla «prima» scadenza. L'ultima rata assorbe gli arrotondamenti."""
    tot = round(pc_num(totale) or 0.0, 2)
    acc = round(pc_num(acconto) or 0.0, 2)
    out = []
    if acc > 0:
        out.append({"id": pc_id(), "scadenza": (pc_d(data_acconto) or pc_d(prima) or _pc_date.today()).isoformat(), "importo": acc, "nota": "Acconto"})
    n = max(1, int(n_rate or 1))
    resto = round(tot - acc, 2)
    if resto <= 0:
        return out
    base = round(resto / n, 2)
    p = pc_d(prima) or _pc_date.today()
    for i in range(n):
        imp = base if i < n - 1 else round(resto - base * (n - 1), 2)
        out.append({"id": pc_id(), "scadenza": pc_aggiungi_mesi(p, i * max(1, int(ogni_mesi or 1))).isoformat(), "importo": imp, "nota": f"Rata {i + 1} di {n}"})
    return out


def pc_stato_rate(p, oggi_):
    """Ogni rata con quanto è coperto dai pagamenti (in ordine di scadenza) → [{…rata, coperto, residuo, stato: pagata|parziale|scaduta|da pagare}]."""
    pagato = round(sum(pc_num(x.get("importo")) or 0 for x in p.get("pagamenti") or []), 2)
    out = []
    for r in sorted(p.get("rate") or [], key=lambda r: (r.get("scadenza") or "9999", r.get("id", ""))):
        imp = round(pc_num(r.get("importo")) or 0, 2)
        cop = round(min(imp, max(0.0, pagato)), 2)
        pagato = round(pagato - cop, 2)
        res = round(imp - cop, 2)
        sc = pc_d(r.get("scadenza"))
        stato = "pagata" if res <= 0.005 else ("scaduta" if sc and sc < oggi_ else "parziale" if cop > 0 else "da pagare")
        out.append(dict(r, coperto=cop, residuo=max(0.0, res), stato=stato))
    return out


def pc_totali(p, oggi_):
    """I numeri della cartella: totale (preventivo o somma delle rate), pagato, da pagare, rate scadute, prossima rata, prossimo appuntamento."""
    pagato = round(sum(pc_num(x.get("importo")) or 0 for x in p.get("pagamenti") or []), 2)
    tot_prev = pc_num((p.get("preventivo") or {}).get("totale"))
    tot_rate = round(sum(pc_num(r.get("importo")) or 0 for r in p.get("rate") or []), 2)
    totale = tot_prev if tot_prev else tot_rate
    rate = pc_stato_rate(p, oggi_)
    future = [a for a in p.get("appuntamenti") or [] if not a.get("fatto") and pc_d(a.get("data")) and pc_d(a.get("data")) >= oggi_]
    future.sort(key=lambda a: (a.get("data"), a.get("ora") or ""))
    aperte = [r for r in rate if r["stato"] != "pagata"]
    return {"totale": round(totale or 0, 2), "pagato": pagato, "residuo": round(max(0.0, (totale or 0) - pagato), 2),
            "percentuale": (min(100, round(pagato / totale * 100)) if totale else 0), "rate": rate,
            "scadute": [r for r in rate if r["stato"] == "scaduta"], "prossima_rata": (aperte[0] if aperte else None),
            "prossimo_app": (future[0] if future else None), "n_app_futuri": len(future),
            "differenza_piano": (round(tot_rate - tot_prev, 2) if tot_prev and tot_rate and abs(tot_rate - tot_prev) > 0.01 else 0.0)}


def pc_data_app(giorno, mese, anno=None, giorno_settimana="", oggi_=None):
    """Data di un appuntamento scritto senza anno («18/01»): la prima data non passata (da una settimana fa in poi); se il cartellino dice
    anche il giorno della settimana (la riga «Lunedì»), sceglie l'anno in cui cade proprio di quel giorno."""
    oggi_ = oggi_ or _pc_date.today()
    try:
        g, m = int(giorno), int(mese)
    except (TypeError, ValueError):
        return None
    if anno:
        try:
            a = int(anno)
            a = a + 2000 if a < 100 else a
            return _pc_date(a, m, g)
        except (TypeError, ValueError):
            return None
    gs = str(giorno_settimana or "").strip().lower()[:3]
    idx = next((i for i, n in enumerate(_PC_GIORNI) if gs and n.startswith(gs)), None)
    candidati = []
    for a in range(oggi_.year - 1, oggi_.year + 4):
        try:
            d = _pc_date(a, m, g)
        except ValueError:
            continue
        if d >= oggi_ - _pc_td(days=7):
            candidati.append(d)
    if idx is not None:
        giusti = [d for d in candidati if d.weekday() == idx]
        if giusti:
            return giusti[0]
    return candidati[0] if candidati else None


def pc_ora(x):
    m = _pc_re.search(r"(\d{1,2})\s*[:.,h]\s*(\d{2})", str(x or ""))
    if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    m = _pc_re.fullmatch(r"\s*(\d{1,2})\s*", str(x or ""))
    return f"{int(m.group(1)):02d}:00" if m and int(m.group(1)) < 24 else ""


_PC_IMPORTO = r"\d{1,3}(?:\.\d{3})*,\d{2}"


def pc_leggi_testo(testo, oggi_=None):
    """Lettura SENZA intelligenza artificiale (dal testo estratto o dall'OCR): struttura, telefoni, email, P.IVA, preventivo (numero, data, totale,
    righe), appuntamenti con data e ora. Prende solo quello che trova scritto chiaramente."""
    oggi_ = oggi_ or _pc_date.today()
    t = str(testo or "")
    righe = [r.strip() for r in t.splitlines() if r.strip()]
    low = t.lower()
    tipo = ("preventivo" if "preventivo" in low else "appuntamento" if "appuntament" in low else "fattura" if "fattura" in low
            else "ricevuta" if _pc_re.search(r"bonifico|\bcro\b|\btrn\b", low) else "altro")
    tel = []
    for m in _pc_re.finditer(r"(?<!\d)(?:\+39[\s.]?)?((?:0\d{1,3}|3\d{2})[\s./-]?\d{3,4}[\s./-]?\d{3,4})(?!\d)", t):
        cifre = _pc_re.sub(r"\D", "", m.group(1))
        if 8 <= len(cifre) <= 11 and not any(_pc_re.sub(r"\D", "", x) == cifre for x in tel) and not _pc_re.search(r"iva\W*$", t[max(0, m.start() - 8):m.start()].lower()):
            tel.append(m.group(1).strip())
    piva = _pc_re.search(r"P\.?\s?IVA\W*(\d{11})", t, _pc_re.I)
    tel = [x for x in tel if not (piva and _pc_re.sub(r"\D", "", x) in piva.group(1))]
    email = _pc_re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t)
    via = _pc_re.search(r"\b(?:Via|Viale|V\.le|Corso|C\.so|Piazza|P\.zza|Largo|Strada)\s+[A-Za-zÀ-ÿ' .]+,?\s*\d+[A-Za-z]?(?:\s*[,-]\s*\d{5}\s+[A-Za-zÀ-ÿ ]+(?:\s*\([A-Z]{2}\))?)?", t)
    cand_nomi = [r for r in righe if _pc_re.search(r"centro|studio|dental|odontoiatr|poliambulator|clinica|fisioterap|medico", r, _pc_re.I)
                 and not _pc_re.search(r"dir\.?\s*san|dott|via|tel|e-?mail", r, _pc_re.I)]
    nome = next((r for r in cand_nomi if _pc_parole(r)), cand_nomi[0] if cand_nomi else "")       # il nome «vero» (Steda Dental), non «Centro medico odontoiatrico»
    medico = _pc_re.search(r"(?:Dott\.?(?:ssa)?|Dr\.?(?:ssa)?)\s+[A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+){1,2}", t)
    prev_m = _pc_re.search(r"preventivo\s*(?:n[°.]?\s*)?([A-Za-z0-9/-]+)\s+del\s+(\d{1,2})/(\d{1,2})/(\d{2,4})", t, _pc_re.I)
    totali = _pc_re.findall(r"totale[^\d\n]{0,40}(" + _PC_IMPORTO + ")", t, _pc_re.I)
    righe_prev = []
    for r in righe:
        if _pc_re.search(r"totale|importo\s*$|p\.\s*u\.", r, _pc_re.I):
            continue
        imp = _pc_re.findall(_PC_IMPORTO, r)
        if imp and _pc_re.search(r"[A-Za-zÀ-ÿ]{4,}", r):
            desc = _pc_re.split(_PC_IMPORTO, r)[0].strip(" -:·")
            dente = _pc_re.search(r"(?<![\d,.])(\d{2}(?:\s*-\s*\d{2})?)(?![\d,.])", r[len(desc):])
            desc = _pc_re.sub(r"(\s+\S{1,2})+$", "", desc).strip(" -:·,")                          # «Impianto osteointegrato È» → senza la sporcizia dell'OCR
            dn = dente.group(1).replace(" ", "") if dente else ""
            chiave = (dn, pc_num(imp[-1]), desc.lower()[:12])
            if desc and chiave not in {(r["dente"], r["importo"], r["descrizione"].lower()[:12]) for r in righe_prev}:
                righe_prev.append({"descrizione": desc[:120], "dente": dn, "importo": pc_num(imp[-1])})
    app = []
    if tipo == "appuntamento" or "appuntament" in low:
        for m in _pc_re.finditer(r"(?<![\d/])(\d{1,2})\s*/\s*(\d{1,2})(?:\s*/\s*(\d{2,4}))?(?![\d/])", t):
            if prev_m and m.start() >= prev_m.start() and m.end() <= prev_m.end():
                continue
            dopo = t[m.end():m.end() + 25]
            prima_riga = t[max(0, t.rfind("\n", 0, m.start())):m.start()].lower()
            d = pc_data_app(m.group(1), m.group(2), m.group(3), next((g for g in _PC_GIORNI if g[:3] in prima_riga), ""), oggi_)
            if d:
                app.append({"data": d.isoformat(), "ora": pc_ora(_pc_re.search(r"\d{1,2}\s*[:.]\s*\d{2}", dopo).group(0)) if _pc_re.search(r"\d{1,2}\s*[:.]\s*\d{2}", dopo) else "",
                            "cosa": "", "note": ""})
    prev = {}
    if prev_m:
        d = pc_data_app(prev_m.group(2), prev_m.group(3), prev_m.group(4), "", oggi_)
        prev = {"numero": prev_m.group(1), "data": d.isoformat() if d else ""}
    if totali:
        prev["totale"] = pc_num(totali[-1])
    if righe_prev and tipo == "preventivo":
        prev["righe"] = righe_prev
    cf = _pc_re.search(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", t.upper())
    return {"codice_fiscale": cf.group(0) if cf else "", "paziente": "", "tipo": tipo, "struttura": {"nome": nome[:80], "indirizzo": via.group(0).strip() if via else "", "telefoni": tel[:4],
                                         "email": email.group(0) if email else "", "medico": medico.group(0) if medico else "", "partita_iva": piva.group(1) if piva else ""},
            "preventivo": prev, "appuntamenti": app, "pagamento": {}, "titolo": "", "fonte": "testo"}


def pc_da_ia(j, oggi_=None):
    """La risposta JSON dell'IA → lo stesso formato di pc_leggi_testo (con le date sistemate e gli importi in numero)."""
    oggi_ = oggi_ or _pc_date.today()
    if not isinstance(j, dict):
        return None
    s = j.get("struttura") if isinstance(j.get("struttura"), dict) else {}
    tel = s.get("telefoni") or []
    tel = [str(x).strip() for x in (tel if isinstance(tel, list) else [tel]) if str(x).strip()]
    pv = j.get("preventivo") if isinstance(j.get("preventivo"), dict) else {}
    righe = []
    for r in pv.get("righe") or []:
        if isinstance(r, dict) and str(r.get("descrizione") or "").strip():
            righe.append({"descrizione": str(r["descrizione"]).strip()[:120], "dente": str(r.get("dente") or "").strip()[:20], "importo": pc_num(r.get("importo"))})
    prev = {k: v for k, v in {"numero": str(pv.get("numero") or "").strip(), "data": (pc_d(pv.get("data")) or "") and pc_d(pv.get("data")).isoformat(),
                              "totale": pc_num(pv.get("totale")), "righe": righe, "note": str(pv.get("note") or "").strip()}.items() if v}
    app = []
    for a in j.get("appuntamenti") or []:
        if not isinstance(a, dict):
            continue
        d = pc_d(a.get("data")) or pc_data_app(a.get("giorno"), a.get("mese"), a.get("anno"), a.get("giorno_settimana"), oggi_)
        if d:
            app.append({"data": d.isoformat(), "ora": pc_ora(a.get("ora")), "cosa": str(a.get("cosa") or "").strip()[:120], "note": ""})
    pg = j.get("pagamento") if isinstance(j.get("pagamento"), dict) else {}
    pag = {k: v for k, v in {"data": (pc_d(pg.get("data")) or "") and pc_d(pg.get("data")).isoformat(), "importo": pc_num(pg.get("importo")),
                             "metodo": str(pg.get("metodo") or "").strip(), "riferimento": str(pg.get("riferimento") or "").strip()}.items() if v}
    tipo = str(j.get("tipo") or "altro").lower()
    return {"tipo": tipo if tipo in ("preventivo", "appuntamento", "fattura", "ricevuta") else "altro",
            "struttura": {"nome": str(s.get("nome") or "").strip()[:80], "indirizzo": str(s.get("indirizzo") or "").strip()[:160], "telefoni": tel[:4],
                          "email": str(s.get("email") or "").strip(), "medico": str(s.get("medico") or "").strip()[:80], "partita_iva": str(s.get("partita_iva") or "").strip()},
            "preventivo": prev, "appuntamenti": app, "pagamento": pag, "titolo": str(j.get("titolo_cura") or "").strip()[:80], "fonte": "ia",
            "paziente": str(j.get("paziente") or "").strip()[:80], "codice_fiscale": _pc_re.sub(r"\s", "", str(j.get("codice_fiscale") or "")).upper()[:16]}


def pc_unisci(letture):
    """Più documenti letti (preventivo + cartellino + …) → una proposta sola: i dati della struttura dal primo che li ha, il preventivo dal
    preventivo, tutti gli appuntamenti (senza doppioni)."""
    out = {"struttura": {"nome": "", "indirizzo": "", "telefoni": [], "email": "", "medico": "", "partita_iva": ""}, "preventivo": {}, "appuntamenti": [],
           "pagamenti": [], "titolo": ""}
    for l in [x for x in letture if x]:
        for k, v in (l.get("struttura") or {}).items():
            if k == "telefoni":
                for tnum in v or []:
                    if _pc_re.sub(r"\D", "", tnum) not in [_pc_re.sub(r"\D", "", x) for x in out["struttura"]["telefoni"]]:
                        out["struttura"]["telefoni"].append(tnum)
            elif v and not out["struttura"].get(k):
                out["struttura"][k] = v
        pv = l.get("preventivo") or {}
        for k, v in pv.items():
            if v and not out["preventivo"].get(k):
                out["preventivo"][k] = v
        for a in l.get("appuntamenti") or []:
            if not any(a["data"] == b["data"] and (a.get("ora") or "") == (b.get("ora") or "") for b in out["appuntamenti"]):
                out["appuntamenti"].append(a)
        if l.get("pagamento", {}).get("importo"):
            out["pagamenti"].append(l["pagamento"])
        if l.get("titolo") and not out["titolo"]:
            out["titolo"] = l["titolo"]
        for k in ("paziente", "codice_fiscale"):
            if l.get(k) and not out.get(k):
                out[k] = l[k]
    out["appuntamenti"].sort(key=lambda a: (a["data"], a.get("ora") or ""))
    return out


def pc_titolo_proposto(prop, tipo=""):
    if prop.get("titolo"):
        return prop["titolo"]
    righe = (prop.get("preventivo") or {}).get("righe") or []
    testo = " ".join(r.get("descrizione", "") for r in righe).lower()
    if "impiant" in testo or "toronto" in testo or "protesi" in testo:
        base = "Impianti e protesi dentale"
    elif "orto" in testo or "apparecch" in testo:
        base = "Ortodonzia"
    elif righe:
        base = righe[0]["descrizione"][:50]
    else:
        base = (tipo or "Percorso di cura").split(" ", 1)[-1]
    nome = (prop.get("struttura") or {}).get("nome") or ""
    nome = _pc_re.sub(r"(?i)\b(centro medico|odontoiatrico|snc|s\.n\.c\.|srl|s\.r\.l\.)\b", "", nome).strip(" -·,")
    return f"{base} — {nome.title()}" if nome else base


def pc_timeline(p):
    """Tutto in ordine di data (dal più recente): appuntamenti, pagamenti, documenti, note del diario, preventivo."""
    ev = []
    pv = p.get("preventivo") or {}
    if pv.get("data") or pv.get("totale"):
        ev.append((pv.get("data") or p.get("creato_il") or "", "🦷", f"Preventivo {pv.get('numero') or ''} · {pc_euro(pv.get('totale'))}".replace("  ", " ")))
    for a in p.get("appuntamenti") or []:
        ev.append((a.get("data") or "", "✅" if a.get("fatto") else "📅",
                   f"Appuntamento {a.get('ora') or ''} {('· ' + a['cosa']) if a.get('cosa') else ''}{(' — ' + a['esito']) if a.get('esito') else ''}".replace("  ", " ")))
    for x in p.get("pagamenti") or []:
        ev.append((x.get("data") or "", "💶", f"Pagato {pc_euro(x.get('importo'))} ({x.get('metodo') or ''}){' · fattura ✔' if x.get('fattura') else ''}"))
    for x in p.get("documenti") or []:
        ev.append((x.get("data") or "", "📄", f"{x.get('categoria') or 'Documento'}: {x.get('titolo') or ''}"))
    for x in p.get("diario") or []:
        ev.append((x.get("data") or "", "📝", str(x.get("testo") or "")))
    return sorted(ev, key=lambda e: e[0] or "", reverse=True)


def pc_riepilogo_testo(p, persona, oggi_):
    t = pc_totali(p, oggi_)
    s = p.get("struttura") or {}
    r = [f"🗂️ {p.get('titolo')}", f"👤 {persona}" if persona else "", f"🏥 {s.get('nome')}" if s.get("nome") else "",
         f"📍 {s.get('indirizzo')}" if s.get("indirizzo") else "", ("📞 " + " · ".join(s.get("telefoni") or [])) if s.get("telefoni") else "",
         f"💶 Totale {pc_euro(t['totale'])} · pagato {pc_euro(t['pagato'])} · da pagare {pc_euro(t['residuo'])}"]
    if t["prossimo_app"]:
        a = t["prossimo_app"]
        r.append(f"📅 Prossimo appuntamento: {pc_data_lunga(a['data'])}{' alle ' + a['ora'] if a.get('ora') else ''}")
    if t["prossima_rata"]:
        x = t["prossima_rata"]
        r.append(f"⏳ Prossima rata: {pc_euro(x['residuo'])} entro il {pc_data_it(x['scadenza'])}")
    if t["scadute"]:
        r.append(f"⚠️ Rate scadute: {len(t['scadute'])} ({pc_euro(sum(x['residuo'] for x in t['scadute']))})")
    app = sorted(p.get("appuntamenti") or [], key=lambda a: (a.get("data") or "", a.get("ora") or ""))
    if app:
        r.append("\nAppuntamenti:")
        r += [f"  {'✅' if a.get('fatto') else '•'} {pc_data_it(a.get('data'))} {a.get('ora') or ''} {a.get('cosa') or ''}".rstrip() for a in app]
    if p.get("pagamenti"):
        r.append("\nPagamenti fatti:")
        r += [f"  • {pc_data_it(x.get('data'))} {pc_euro(x.get('importo'))} {x.get('metodo') or ''}".rstrip()
              for x in sorted(p["pagamenti"], key=lambda x: x.get("data") or "")]
    return "\n".join(x for x in r if x)


def pc_detraibile_anno(p, anno):
    """Quanto è stato pagato nell'anno (per la dichiarazione dei redditi: spese sanitarie) e quanto di questo ha già la fattura."""
    tot = fatt = 0.0
    for x in p.get("pagamenti") or []:
        d = pc_d(x.get("data"))
        if d and d.year == anno:
            tot += pc_num(x.get("importo")) or 0
            if x.get("fattura"):
                fatt += pc_num(x.get("importo")) or 0
    return round(tot, 2), round(fatt, 2)


def pc_allegati(p):
    """Tutti i file della cartella (riferimenti {id, nome, mime}) senza doppioni."""
    out, visti = [], set()
    for grp in ("documenti", "pagamenti"):
        for x in p.get(grp) or []:
            for a in x.get("allegati") or []:
                if a.get("id") and a["id"] not in visti:
                    visti.add(a["id"])
                    out.append(a)
    for a in p.get("appuntamenti") or []:
        for r in a.get("allegati") or []:
            if r.get("id") and r["id"] not in visti:
                visti.add(r["id"])
                out.append(r)
    return out


# =====================================================================================================================
# LETTURA DEI DOCUMENTI (IA se c'è, sempre anche senza)
# =====================================================================================================================
PC_ISTRUZIONI_IA = """Leggi documenti di studi medici e dentistici italiani: preventivi, cartellini degli appuntamenti (anche scritti a mano), fatture, ricevute di bonifico.
Rispondi SOLO con un oggetto JSON con questa forma:
{"tipo": "preventivo|appuntamento|fattura|ricevuta|altro",
 "struttura": {"nome": "", "indirizzo": "", "telefoni": [], "email": "", "medico": "direttore sanitario o medico, se scritto", "partita_iva": ""},
 "paziente": "", "codice_fiscale": "",
 "titolo_cura": "nome breve della cura in italiano semplice (es. «Impianti e protesi arcata inferiore»), vuoto se non è un preventivo",
 "preventivo": {"numero": "", "data": "AAAA-MM-GG", "totale": 0, "righe": [{"descrizione": "", "dente": "", "importo": 0}], "note": "condizioni di pagamento o finanziamento scritte"},
 "appuntamenti": [{"giorno": 0, "mese": 0, "anno": null, "giorno_settimana": "", "ora": "HH:MM", "cosa": ""}],
 "pagamento": {"data": "AAAA-MM-GG", "importo": 0, "metodo": "", "riferimento": "CRO/TRN o numero fattura"}}
REGOLE: non inventare nulla; quello che non c'è resta vuoto. Importi in numero con il punto per i decimali (7.500,00 € → 7500.00).
Nei cartellini con una tabella dei giorni, il giorno della settimana è quello della RIGA dove è scritta a mano la data; se l'anno non è scritto metti anno null.
Un'ora scritta «10.00», «10:00» o «10» va resa «10:00»."""


def pc_leggi_documento(nome, mime, dati, oggi_=None):
    """→ (lettura, come): prima l'IA (se ci sono i servizi), poi la lettura del testo che completa quello che manca."""
    oggi_ = oggi_ or _pc_date.today()
    ia = None
    come = []
    try:
        if "il_disponibili" in globals() and il_disponibili(IL_ORDINE_VISTA):
            imm = il_immagini(nome, mime, dati)
            if imm:
                es = il_consenso_immagine(PC_ISTRUZIONI_IA, f"Documento: {nome}. Leggilo e compila il JSON.", imm, quante=2,
                                          incerta=lambda d: not d.get("appuntamenti") and not (d.get("preventivo") or {}).get("totale"))
                ia = pc_da_ia(es.get("risultato"), oggi_)
                if ia:
                    come.append("IA: " + " + ".join(IL_FORNITORI.get(p, {}).get("nome", p) for p in es.get("fonti") or []))
    except Exception as e:
        come.append(f"IA non disponibile ({type(e).__name__})")
    loc = None
    try:
        testo = ""
        if "ca_estrai_testo" in globals():
            testo, _info = ca_estrai_testo(nome, mime, dati)
        if str(mime).startswith("image/") and "vp_ocr_raddrizzata" in globals():
            testo = (testo or "") + "\n" + (vp_ocr_raddrizzata(dati) or "")
        if testo.strip():
            loc = pc_leggi_testo(testo, oggi_)
            come.append("testo del documento")
    except Exception:
        pass
    if ia and loc:
        unito = pc_unisci([ia, loc])
        return dict(ia, struttura=unito["struttura"], preventivo=dict(loc.get("preventivo") or {}, **(ia.get("preventivo") or {})),
                    appuntamenti=ia["appuntamenti"] or loc["appuntamenti"]), " · ".join(come)
    return (ia or loc or {"tipo": "altro", "struttura": {}, "preventivo": {}, "appuntamenti": [], "pagamento": {}, "titolo": ""}), " · ".join(come) or "nessuna lettura"


# =====================================================================================================================
# INTERFACCIA
# =====================================================================================================================
_PC_CSS = """<style>
.pc-card{border:1px solid rgba(120,220,255,.35);border-radius:16px;padding:12px 14px;margin:6px 0 8px;background:linear-gradient(135deg,rgba(30,60,110,.55),rgba(20,30,60,.55));box-shadow:0 0 14px rgba(80,200,255,.15)}
.pc-card h4{margin:0 0 4px;font-size:1.05rem}
.pc-card small{opacity:.85}
.pc-bar{height:10px;border-radius:6px;background:rgba(255,255,255,.15);overflow:hidden;margin:6px 0 2px}
.pc-bar i{display:block;height:100%;background:linear-gradient(90deg,#2ee6a6,#2bb6ff)}
.pc-kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:6px 0 10px}
.pc-k{border-radius:12px;padding:8px 10px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12)}
.pc-k span{display:block;font-size:.72rem;font-weight:700;opacity:.8}.pc-k b{font-size:1.15rem}
.pc-k.rosso{border-color:#ff5a6e;box-shadow:0 0 10px rgba(255,90,110,.35)}.pc-k.verde{border-color:#2ee6a6}
.pc-riga{border-left:3px solid #2bb6ff;padding:4px 10px;margin:4px 0;border-radius:6px;background:rgba(255,255,255,.04)}
.pc-riga.fatto{border-color:#2ee6a6;opacity:.85}.pc-riga.scaduta{border-color:#ff5a6e}.pc-riga.pagata{border-color:#2ee6a6;opacity:.8}
</style>"""


def _pc_e(x):
    return _pc_html.escape(str(x or ""))


def _pc_percorsi(f, pid=None):
    return [p for p in f.get("percorsi") or [] if pid is None or p.get("profilo", "p0") == pid]


def _pc_get(pc_id_):
    return next((p for p in _fa_dati().get("percorsi") or [] if p.get("id") == pc_id_), None)


def _pc_modifica(pc_id_, fn, msg):
    def _f(f):
        for p in f.setdefault("percorsi", []):
            if p.get("id") == pc_id_:
                fn(p)
                break
    _fa_salva(_f, "Salute · percorso di cura: " + msg)


def _pc_tel_link(t):
    num = _pc_re.sub(r"[^\d+]", "", t)
    if num and not num.startswith("+"):
        num = "+39" + num
    return f"<a href='tel:{num}'>📞 {_pc_e(t)}</a>"


def pc_sezione(f, pid, nomi, oggi_):
    """Il riquadro in Salute (sopra le schede): elenco dei percorsi della persona scelta, oppure il percorso aperto."""
    st.markdown(_PC_CSS, unsafe_allow_html=True)
    aperto = st.session_state.get("pc_aperto")
    tutti = _pc_percorsi(f, pid)
    if aperto and any(p["id"] == aperto for p in tutti):
        _pc_dettaglio(next(p for p in tutti if p["id"] == aperto), nomi.get(pid, ""), oggi_)
        return
    attivi = [p for p in tutti if p.get("stato") != "Concluso"]
    chiusi = [p for p in tutti if p.get("stato") == "Concluso"]
    def _nuovo(tipo="secondary"):
        if st.button("➕ Nuovo percorso di cura", key=f"pc_nuovo_{pid}", type=tipo, width="stretch"):
            st.session_state.pop("pc_bozza", None)
            _pc_dialogo_nuovo(pid, nomi.get(pid, ""), oggi_)
    if attivi:                                     # le cure in corso sempre in vista, in cima a Salute
        st.markdown(f"#### 🗂️ Percorsi di cura di {_pc_e(nomi.get(pid, ''))}")
        for p in attivi:
            _pc_card(p, oggi_)
        if chiusi:
            with st.expander(f"📦 Percorsi conclusi ({len(chiusi)})"):
                for p in chiusi:
                    _pc_card(p, oggi_)
        _nuovo()
        return
    with st.expander(f"🗂️ Percorsi di cura di {nomi.get(pid, '')}" + (f" ({len(chiusi)} conclusi)" if chiusi else "")):
        st.caption("Una cartella per ogni cura lunga (dentista, fisioterapia, ortodonzia…): preventivo, appuntamenti con gli avvisi, rate e "
                   "pagamenti con le ricevute, documenti e note. Tutto in un posto solo.")
        for p in chiusi:
            _pc_card(p, oggi_)
        _nuovo("primary")


def _pc_card(p, oggi_):
    t = pc_totali(p, oggi_)
    s = p.get("struttura") or {}
    app = t["prossimo_app"]
    righe = [f"<h4>{_pc_e(p.get('tipo', '').split(' ')[0])} {_pc_e(p.get('titolo'))}</h4>"]
    if s.get("nome"):
        righe.append(f"<small>🏥 {_pc_e(s['nome'])}</small><br>")
    if app:
        righe.append(f"<small>📅 Prossimo appuntamento: <b>{_pc_e(pc_data_lunga(app['data']))}</b>{' alle ' + _pc_e(app['ora']) if app.get('ora') else ''}</small><br>")
    if t["totale"]:
        righe.append(f"<div class='pc-bar'><i style='width:{t['percentuale']}%'></i></div><small>💶 Pagato {pc_euro(t['pagato'])} su {pc_euro(t['totale'])} "
                     f"· da pagare <b>{pc_euro(t['residuo'])}</b></small>")
    if t["scadute"]:
        righe.append(f"<br><small style='color:#ff8a98'>⚠️ {len(t['scadute'])} rata/e scaduta/e: {pc_euro(sum(x['residuo'] for x in t['scadute']))}</small>")
    if p.get("stato") != "In corso":
        righe.append(f"<br><small>Stato: {_pc_e(p.get('stato'))}</small>")
    try:
        n_c = len(pc_candidati(_fa_dati(), p))
    except Exception:
        n_c = 0
    if n_c:
        righe.append(f"<br><small style='color:#ffd36e'>🔗 {n_c} documento/i già nell'app sembra/no di questa cartella: aprila per controllarli</small>")
    st.markdown("<div class='pc-card'>" + "".join(righe) + "</div>", unsafe_allow_html=True)
    if st.button("📂 Apri la cartella", key=f"pc_apri_{p['id']}", width="stretch"):
        st.session_state["pc_aperto"] = p["id"]
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------- nuovo percorso
def _pc_tabella_righe(righe):
    import pandas as pd
    return pd.DataFrame([{"Descrizione": r.get("descrizione", ""), "Dente": r.get("dente", ""), "Importo €": pc_num(r.get("importo"))} for r in righe]
                        or [{"Descrizione": "", "Dente": "", "Importo €": None}])


def _pc_tabella_app(app):
    import pandas as pd
    return pd.DataFrame([{"Data": pc_d(a.get("data")), "Ora": a.get("ora", ""), "Per cosa": a.get("cosa", "")} for a in app]
                        or [{"Data": None, "Ora": "", "Per cosa": ""}])


def _pc_dialogo_nuovo(pid, persona, oggi_):
    def _corpo():
        st.caption(f"Per **{persona}**. Carica i documenti che hai (preventivo, cartellino dell'appuntamento, foto o PDF): l'app li legge e "
                   "compila da sola. Controlla e correggi, poi salva. Puoi anche compilare tutto a mano.")
        files = ar_uploader("📎 Preventivo, appuntamento, altri documenti (foto o PDF)", type=TIPI_FILE, accept_multiple_files=True, key="pc_nuovo_files")
        bozza = st.session_state.get("pc_bozza") or {}
        if files and st.button("🔎 Leggi i documenti e compila", key="pc_leggi", width="stretch"):
            letture, cats, come = [], [], []
            with st.spinner("Leggo i documenti… (con l'IA può volerci un minuto)"):
                for u in files:
                    try:
                        dati = u.getvalue()
                        mime = getattr(u, "type", "") or ("application/pdf" if u.name.lower().endswith(".pdf") else "image/jpeg")
                        l, c = pc_leggi_documento(u.name, mime, dati, oggi_)
                    except Exception as e:
                        l, c = None, f"errore {type(e).__name__}"
                    letture.append(l)
                    cats.append({"preventivo": "Preventivo", "appuntamento": "Promemoria appuntamento", "fattura": "Fattura",
                                 "ricevuta": "Ricevuta di pagamento"}.get((l or {}).get("tipo"), "Altro"))
                    come.append(f"{u.name}: {c}")
            prop = pc_unisci(letture)
            prop["categorie"] = cats
            prop["come"] = come
            prop["giro"] = bozza.get("giro", 0) + 1
            st.session_state["pc_bozza"] = bozza = prop
        if bozza.get("come"):
            st.info("📖 Letto: " + " · ".join(bozza["come"]) + "\n\nControlla i dati qui sotto prima di salvare.")
        g = bozza.get("giro", 0)
        s = bozza.get("struttura") or {}
        pv = bozza.get("preventivo") or {}
        tipo = st.selectbox("Tipo di cura", PC_TIPI, key=f"pc_n_tipo_{g}")
        titolo = st.text_input("Nome della cartella", value=pc_titolo_proposto(bozza, tipo) if bozza else "", key=f"pc_n_tit_{g}",
                               placeholder="es. Impianti dentali — Steda Dental")
        st.markdown("**🏥 Studio / struttura**")
        nome_s = st.text_input("Nome", value=s.get("nome", ""), key=f"pc_n_sn_{g}")
        ind = st.text_input("Indirizzo", value=s.get("indirizzo", ""), key=f"pc_n_si_{g}")
        c1, c2 = st.columns(2, gap="small")
        tel = c1.text_input("Telefoni (separati da virgola)", value=", ".join(s.get("telefoni") or []), key=f"pc_n_st_{g}")
        mail = c2.text_input("Email", value=s.get("email", ""), key=f"pc_n_se_{g}")
        medico = st.text_input("Medico / dentista", value=s.get("medico", ""), key=f"pc_n_sm_{g}")
        st.markdown("**🦷 Preventivo**")
        c1, c2, c3 = st.columns(3, gap="small")
        num = c1.text_input("Numero", value=str(pv.get("numero") or ""), key=f"pc_n_pn_{g}")
        dprev = c2.date_input("Data", value=pc_d(pv.get("data")), format="DD/MM/YYYY", key=f"pc_n_pd_{g}")
        tot = c3.number_input("Totale €", min_value=0.0, value=float(pc_num(pv.get("totale")) or 0.0), step=50.0, format="%.2f", key=f"pc_n_pt_{g}")
        righe = st.data_editor(_pc_tabella_righe(pv.get("righe") or []), num_rows="dynamic", width="stretch", hide_index=True, key=f"pc_n_pr_{g}",
                               column_config={"Importo €": st.column_config.NumberColumn(format="%.2f €", min_value=0.0)})
        st.markdown("**📅 Appuntamenti**")
        app = st.data_editor(_pc_tabella_app(bozza.get("appuntamenti") or []), num_rows="dynamic", width="stretch", hide_index=True, key=f"pc_n_ap_{g}",
                             column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY"), "Ora": st.column_config.TextColumn(help="es. 10:00")})
        for a in bozza.get("appuntamenti") or []:
            st.caption(f"📅 Letto: **{pc_data_lunga(a['data'])}**{' alle ' + a['ora'] if a.get('ora') else ''} (se l'anno non era scritto l'ho dedotto: controllalo).")
        st.markdown("**💶 Come pagherete**")
        modo = st.radio("Pagamento", ["Ancora da decidere", "Un'unica volta", "A rate"], horizontal=True, key=f"pc_n_mod_{g}", label_visibility="collapsed")
        rate = []
        if modo == "Un'unica volta" and tot:
            dun = st.date_input("Entro il", value=oggi_ + _pc_td(days=30), format="DD/MM/YYYY", key=f"pc_n_un_{g}")
            rate = [{"id": pc_id(), "scadenza": dun.isoformat(), "importo": round(tot, 2), "nota": "Saldo"}]
        elif modo == "A rate" and tot:
            c1, c2 = st.columns(2, gap="small")
            acc = c1.number_input("Acconto €", min_value=0.0, max_value=float(tot), value=0.0, step=50.0, format="%.2f", key=f"pc_n_acc_{g}")
            n = c2.number_input("Numero di rate", min_value=1, max_value=120, value=12, key=f"pc_n_nr_{g}")
            c1, c2 = st.columns(2, gap="small")
            prima = c1.date_input("Prima rata il", value=pc_aggiungi_mesi(oggi_, 1), format="DD/MM/YYYY", key=f"pc_n_pr1_{g}")
            ogni = c2.selectbox("Ogni", [1, 2, 3, 6], format_func=lambda m: "mese" if m == 1 else f"{m} mesi", key=f"pc_n_ogni_{g}")
            rate = pc_genera_rate(tot, n, prima, ogni, acc, oggi_)
            if rate:
                st.caption(f"{len(rate)} scadenze: " + ", ".join(f"{pc_data_it(r['scadenza'])} {pc_euro(r['importo'])}" for r in rate[:4]) + (" …" if len(rate) > 4 else "")
                           + " — le potrai cambiare una per una.")
        st.caption("🔔 Gli avvisi degli appuntamenti e delle rate arrivano dallo Scadenziario (WhatsApp, Telegram, email) come gli altri.")
        if st.button("💾 Crea la cartella", type="primary", key="pc_n_salva", width="stretch", disabled=not titolo.strip()):
            p = pc_nuovo(titolo, pid, oggi_)
            p["tipo"] = tipo
            p["struttura"] = {"nome": nome_s.strip(), "indirizzo": ind.strip(), "telefoni": [x.strip() for x in tel.split(",") if x.strip()],
                              "email": mail.strip(), "medico": medico.strip(), "partita_iva": s.get("partita_iva", "")}
            rr = []
            for _i, r in righe.iterrows():
                if str(r.get("Descrizione") or "").strip():
                    rr.append({"descrizione": str(r["Descrizione"]).strip(), "dente": str(r.get("Dente") or "").strip(), "importo": pc_num(r.get("Importo €"))})
            p["preventivo"] = {"numero": num.strip(), "data": dprev.isoformat() if dprev else "", "totale": round(tot, 2) if tot else None, "righe": rr, "note": pv.get("note", "")}
            for _i, r in app.iterrows():
                dd = r.get("Data")
                try:
                    dd = dd.date() if hasattr(dd, "date") else dd
                    dd = pc_d(dd.isoformat()) if dd else None
                except Exception:
                    dd = None
                if dd:
                    p["appuntamenti"].append({"id": pc_id(), "data": dd.isoformat(), "ora": pc_ora(r.get("Ora")), "cosa": str(r.get("Per cosa") or "").strip(),
                                              "note": "", "fatto": False, "esito": ""})
            p["rate"] = rate
            p["paziente"] = {"nome": bozza.get("paziente", ""), "codice_fiscale": bozza.get("codice_fiscale", "")}
            for x in bozza.get("pagamenti") or []:
                if x.get("importo"):
                    p["pagamenti"].append({"id": pc_id(), "data": x.get("data") or oggi_.isoformat(), "importo": x["importo"], "metodo": x.get("metodo") or "Bonifico",
                                           "riferimento": x.get("riferimento", ""), "nota": "", "fattura": False, "allegati": []})
            try:
                refs = _fa_salva_files(files) if files else []
            except Exception as e:
                st.error(f"Non sono riuscito a salvare i file: {e}")
                return
            cats = bozza.get("categorie") or []
            for i, r in enumerate(refs):
                cat = cats[i] if i < len(cats) else "Altro"
                p["documenti"].append({"id": pc_id(), "titolo": r.get("nome", "documento"), "categoria": cat,
                                       "data": (p["preventivo"]["data"] if cat == "Preventivo" and p["preventivo"]["data"] else oggi_.isoformat()), "allegati": [r]})
            p["diario"].append({"id": pc_id(), "data": oggi_.isoformat(), "testo": "Cartella creata" + (f" con {len(refs)} documenti" if refs else "")})
            _fa_salva(lambda f: f.setdefault("percorsi", []).append(p), "Salute: nuovo percorso di cura")
            st.session_state.pop("pc_bozza", None)
            st.session_state["pc_aperto"] = p["id"]
            st.session_state["fa_msg"] = f"✅ Cartella «{p['titolo']}» creata."
            st.rerun()
    st.dialog("🗂️ Nuovo percorso di cura", width="large")(_corpo)()


# ---------------------------------------------------------------------------------------------------------------- la cartella aperta
def _pc_dettaglio(p, persona, oggi_):
    t = pc_totali(p, oggi_)
    s = p.get("struttura") or {}
    c1, c2 = st.columns([3, 2], gap="small")
    if c1.button("← Tutti i percorsi", key="pc_chiudi", width="stretch"):
        st.session_state.pop("pc_aperto", None)
        st.rerun()
    if c2.button("✏️ Modifica dati", key="pc_mod_testa", width="stretch"):
        _pc_dialogo_testa(p)
    contatti = []
    if s.get("indirizzo"):
        contatti.append(f"<a href='https://www.google.com/maps/search/?api=1&query={_pc_html.escape(s['indirizzo'], quote=True)}' target='_blank'>📍 {_pc_e(s['indirizzo'])}</a>")
    contatti += [_pc_tel_link(x) for x in s.get("telefoni") or []]
    if s.get("email"):
        contatti.append(f"<a href='mailto:{_pc_e(s['email'])}'>✉️ {_pc_e(s['email'])}</a>")
    st.markdown(f"<div class='pc-card'><h4>{_pc_e(p.get('tipo', '').split(' ')[0])} {_pc_e(p.get('titolo'))}</h4>"
                f"<small>👤 {_pc_e(persona)} · {_pc_e(p.get('stato'))}{(' · 🏥 ' + _pc_e(s['nome'])) if s.get('nome') else ''}"
                f"{(' · 👨‍⚕️ ' + _pc_e(s['medico'])) if s.get('medico') else ''}</small><br><small>{' · '.join(contatti)}</small></div>", unsafe_allow_html=True)
    app = t["prossimo_app"]
    pr = t["prossima_rata"]
    st.markdown("<div class='pc-kpi'>"
                f"<div class='pc-k'><span>Totale</span><b>{pc_euro(t['totale'])}</b></div>"
                f"<div class='pc-k verde'><span>Pagato</span><b>{pc_euro(t['pagato'])}</b></div>"
                f"<div class='pc-k{' rosso' if t['scadute'] else ''}'><span>Da pagare</span><b>{pc_euro(t['residuo'])}</b></div>"
                f"<div class='pc-k'><span>Prossimo appuntamento</span><b>{_pc_e(pc_data_it(app['data']) + (' ' + app['ora'] if app.get('ora') else '')) if app else '—'}</b></div>"
                f"<div class='pc-k{' rosso' if pr and pr['stato'] == 'scaduta' else ''}'><span>Prossima rata</span>"
                f"<b>{(pc_euro(pr['residuo']) + ' · ' + pc_data_it(pr['scadenza'])) if pr else '—'}</b></div></div>", unsafe_allow_html=True)
    if t["totale"]:
        st.markdown(f"<div class='pc-bar'><i style='width:{t['percentuale']}%'></i></div><small>{t['percentuale']}% pagato</small>", unsafe_allow_html=True)
    if t["scadute"]:
        st.error(f"⚠️ {len(t['scadute'])} rata/e scaduta/e da pagare: {pc_euro(sum(x['residuo'] for x in t['scadute']))}")
    if t["differenza_piano"]:
        st.warning(f"Le rate sommano {pc_euro(t['differenza_piano'] + t['totale'])}, il preventivo {pc_euro(t['totale'])}: controlla il piano dei pagamenti.")
    try:
        cand = pc_candidati(_fa_dati(), p)
    except Exception:
        cand = []
    voci = ["📅 Appuntamenti", "💶 Pagamenti", "📄 Documenti", "🦷 Preventivo", "🕑 Diario"] + ([f"🔗 Da collegare ({len(cand)})"] if cand else [])
    if st.session_state.get(f"pc_vista_{p['id']}") not in voci:
        st.session_state[f"pc_vista_{p['id']}"] = voci[0]
    if cand:
        st.info(f"🔗 Ho trovato {len(cand)} documento/i già nell'app che sembra/no di questa cura: guarda in «🔗 Da collegare».")
    vista = st.radio("Sezione", voci, horizontal=True, key=f"pc_vista_{p['id']}", label_visibility="collapsed")
    if vista.startswith("🔗"):
        _pc_vista_collegare(p, cand, persona, oggi_)
        vista = ""
    if vista.startswith("📅"):
        _pc_vista_appuntamenti(p, oggi_)
    elif vista.startswith("💶"):
        _pc_vista_pagamenti(p, t, oggi_)
    elif vista.startswith("📄"):
        _pc_vista_documenti(p, persona, oggi_)
    elif vista.startswith("🦷"):
        _pc_vista_preventivo(p)
    elif vista.startswith("🕑"):
        _pc_vista_diario(p, oggi_)
    st.divider()
    allegati = pc_allegati(p)
    _fa_inv_voce(f"pc_inv_{p['id']}", f"📤 Invia il riepilogo ({len(allegati)} file)", f"{p.get('titolo')} — {persona}",
                 [("Riepilogo", pc_riepilogo_testo(p, persona, oggi_))], allegati)
    st.download_button("⬇ Scarica il riepilogo (testo)", pc_riepilogo_testo(p, persona, oggi_).encode("utf-8"), file_name=f"riepilogo_{p['id']}.txt",
                       mime="text/plain", key=f"pc_dl_{p['id']}", width="stretch")


def _pc_dialogo_testa(p):
    def _corpo():
        s = p.get("struttura") or {}
        tit = st.text_input("Nome della cartella", value=p.get("titolo", ""), key="pc_t_tit")
        tipo = st.selectbox("Tipo di cura", PC_TIPI, index=PC_TIPI.index(p["tipo"]) if p.get("tipo") in PC_TIPI else 0, key="pc_t_tipo")
        stato = st.radio("Stato", PC_STATI, index=PC_STATI.index(p.get("stato")) if p.get("stato") in PC_STATI else 0, horizontal=True, key="pc_t_stato")
        nome_s = st.text_input("Studio / struttura", value=s.get("nome", ""), key="pc_t_sn")
        ind = st.text_input("Indirizzo", value=s.get("indirizzo", ""), key="pc_t_si")
        tel = st.text_input("Telefoni (separati da virgola)", value=", ".join(s.get("telefoni") or []), key="pc_t_st")
        mail = st.text_input("Email", value=s.get("email", ""), key="pc_t_se")
        med = st.text_input("Medico / dentista", value=s.get("medico", ""), key="pc_t_sm")
        note = st.text_area("Note", value=p.get("note", ""), key="pc_t_note")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", type="primary", key="pc_t_ok", width="stretch"):
            def _fn(x):
                x.update(titolo=tit.strip() or x["titolo"], tipo=tipo, stato=stato, note=note)
                x["struttura"] = dict(x.get("struttura") or {}, nome=nome_s.strip(), indirizzo=ind.strip(), email=mail.strip(), medico=med.strip(),
                                      telefoni=[y.strip() for y in tel.split(",") if y.strip()])
            _pc_modifica(p["id"], _fn, "dati")
            st.rerun()
        if c2.button("Annulla", key="pc_t_no", width="stretch"):
            st.rerun()
        with st.expander("🗑️ Elimina tutta la cartella"):
            st.warning("Si cancellano appuntamenti, pagamenti, note e i file allegati che non sono usati altrove. Non si può annullare.")
            if st.checkbox("Sì, voglio eliminarla", key="pc_t_conf") and st.button("🗑️ Elimina definitivamente", key="pc_t_del", width="stretch"):
                ids = {a["id"] for a in pc_allegati(p)}
                ids -= {r.get("id") for x in p.get("documenti") or [] if str(x.get("da") or "").startswith(("docsan:", "visita:", "presc:")) or x.get("collegato")
                        for r in x.get("allegati") or [] if isinstance(r, dict)}       # i file COLLEGATI da Salute non si toccano mai: restano nei loro documenti
                _fa_salva(lambda f: f.__setitem__("percorsi", [x for x in f.get("percorsi") or [] if x.get("id") != p["id"]]), "Salute: percorso eliminato")
                try:
                    usati = set(_ar_riuso_riferimenti(_fa_dati())) if "_ar_riuso_riferimenti" in globals() else ids
                    _fa_cancella_files(sorted(ids - usati))
                except Exception:
                    pass
                st.session_state.pop("pc_aperto", None)
                st.session_state["fa_msg"] = "🗑️ Cartella eliminata."
                st.rerun()
    st.dialog("✏️ Dati della cartella")(_corpo)()


# ---------------------------------------------------------------------------------------------------------------- appuntamenti
def _pc_vista_appuntamenti(p, oggi_):
    app = sorted(p.get("appuntamenti") or [], key=lambda a: (a.get("data") or "", a.get("ora") or ""))
    futuri = [a for a in app if not a.get("fatto") and (pc_d(a.get("data")) or oggi_) >= oggi_]
    passati = [a for a in app if a not in futuri]
    if st.button("➕ Aggiungi un appuntamento", key=f"pc_app_add_{p['id']}", type="primary", width="stretch"):
        _pc_dialogo_app(p, None, oggi_)
    if not app:
        st.caption("Nessun appuntamento. Aggiungilo qui: lo Scadenziario ti avvisa il giorno prima e un'ora prima.")
    for a in futuri + list(reversed(passati)):
        cls = "fatto" if a.get("fatto") else ("scaduta" if (pc_d(a.get("data")) or oggi_) < oggi_ else "")
        st.markdown(f"<div class='pc-riga {cls}'>{'✅' if a.get('fatto') else '📅'} <b>{_pc_e(pc_data_lunga(a.get('data')))}</b>"
                    f"{' alle ' + _pc_e(a['ora']) if a.get('ora') else ''}{(' · ' + _pc_e(a['cosa'])) if a.get('cosa') else ''}"
                    f"{('<br><small>' + _pc_e(a['esito'] or a.get('note')) + '</small>') if (a.get('esito') or a.get('note')) else ''}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        if not a.get("fatto") and c1.button("✅ Fatto", key=f"pc_app_ok_{a['id']}", width="stretch"):
            _pc_dialogo_app(p, a, oggi_, fatto=True)
        if c2.button("✏️ Modifica", key=f"pc_app_mod_{a['id']}", width="stretch"):
            _pc_dialogo_app(p, a, oggi_)
    if futuri:
        st.download_button("📆 Metti gli appuntamenti nel calendario del telefono (.ics)", _pc_ics(p, futuri).encode("utf-8"), file_name="appuntamenti.ics",
                           mime="text/calendar", key=f"pc_ics_{p['id']}", width="stretch")
    st.caption("🔔 Avvisi automatici (WhatsApp, Telegram, email) dallo Scadenziario: si regolano in 📅 Scadenziario → «Visite e appuntamenti».")


def _pc_ics(p, app):
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VitaMemo//Percorsi di cura//IT"]
    luogo = ((p.get("struttura") or {}).get("nome") or "") + ((" - " + p["struttura"]["indirizzo"]) if (p.get("struttura") or {}).get("indirizzo") else "")
    for a in app:
        d = pc_d(a.get("data"))
        if not d:
            continue
        ora = a.get("ora") or ""
        righe += ["BEGIN:VEVENT", f"UID:pc-{p['id']}-{a['id']}@vitamemo", f"SUMMARY:{p.get('titolo')}{(' - ' + a['cosa']) if a.get('cosa') else ''}"]
        if ora:
            hh, mm = ora.split(":")
            righe += [f"DTSTART;TZID=Europe/Rome:{d.strftime('%Y%m%d')}T{hh}{mm}00", "DURATION:PT1H"]
        else:
            righe += [f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}"]
        if luogo:
            righe.append("LOCATION:" + luogo.replace(",", "\\,"))
        righe += ["BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", "DESCRIPTION:Appuntamento domani", "END:VALARM",
                  "BEGIN:VALARM", "TRIGGER:-PT1H", "ACTION:DISPLAY", "DESCRIPTION:Appuntamento tra un'ora", "END:VALARM", "END:VEVENT"]
    righe.append("END:VCALENDAR")
    return "\r\n".join(righe)


def _pc_dialogo_app(p, a, oggi_, fatto=False):
    nuovo = a is None
    a = dict(a or {"id": pc_id(), "data": "", "ora": "", "cosa": "", "note": "", "fatto": False, "esito": ""})

    def _corpo():
        k = a["id"]
        d = st.date_input("Giorno", value=pc_d(a.get("data")) or oggi_, format="DD/MM/YYYY", key=f"pc_a_d_{k}")
        st.caption(pc_data_lunga(d.isoformat()))
        ora = st.text_input("Ora (es. 10:00)", value=a.get("ora", ""), key=f"pc_a_o_{k}")
        cosa = st.text_input("Per cosa (facoltativo)", value=a.get("cosa", ""), key=f"pc_a_c_{k}", placeholder="es. estrazioni, impronte, prova protesi…")
        note = st.text_input("Note", value=a.get("note", ""), key=f"pc_a_n_{k}")
        fatto_ = st.checkbox("✅ Appuntamento già fatto", value=fatto or bool(a.get("fatto")), key=f"pc_a_f_{k}")
        esito = st.text_area("Com'è andata / cosa hanno fatto", value=a.get("esito", ""), key=f"pc_a_e_{k}") if fatto_ else a.get("esito", "")
        pross = st.date_input("📅 Prossimo appuntamento fissato (se c'è)", value=None, format="DD/MM/YYYY", key=f"pc_a_p_{k}") if fatto_ else None
        pross_ora = st.text_input("Ora del prossimo", key=f"pc_a_po_{k}") if pross else ""
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", type="primary", key=f"pc_a_ok_{k}", width="stretch"):
            nuovo_a = dict(a, data=d.isoformat(), ora=pc_ora(ora), cosa=cosa.strip(), note=note.strip(), fatto=fatto_, esito=(esito or "").strip())

            def _fn(x):
                lst = [y for y in x.setdefault("appuntamenti", []) if y.get("id") != a["id"]]
                lst.append(nuovo_a)
                if pross:
                    lst.append({"id": pc_id(), "data": pross.isoformat(), "ora": pc_ora(pross_ora), "cosa": "", "note": "", "fatto": False, "esito": ""})
                x["appuntamenti"] = lst
                if fatto_ and not a.get("fatto"):
                    x.setdefault("diario", []).append({"id": pc_id(), "data": d.isoformat(), "testo": "Appuntamento fatto" + (f": {esito.strip()}" if esito else "")})
            _pc_modifica(p["id"], _fn, "appuntamento")
            st.rerun()
        if not nuovo and c2.button("🗑️ Elimina", key=f"pc_a_del_{k}", width="stretch"):
            _pc_modifica(p["id"], lambda x: x.__setitem__("appuntamenti", [y for y in x.get("appuntamenti") or [] if y.get("id") != a["id"]]), "appuntamento tolto")
            st.rerun()
    st.dialog("📅 Appuntamento")(_corpo)()


# ---------------------------------------------------------------------------------------------------------------- pagamenti
def _pc_vista_pagamenti(p, t, oggi_):
    c1, c2 = st.columns(2, gap="small")
    if c1.button("➕ Registra un pagamento", key=f"pc_pag_add_{p['id']}", type="primary", width="stretch"):
        _pc_dialogo_pag(p, None, oggi_, t)
    if c2.button("🗓️ Piano delle rate", key=f"pc_rate_{p['id']}", width="stretch"):
        _pc_dialogo_rate(p, oggi_)
    if t["rate"]:
        st.markdown("**🗓️ Rate** (i pagamenti coprono prima le rate più vecchie)")
        icone = {"pagata": "✅", "parziale": "🟡", "scaduta": "🔴", "da pagare": "⏳"}
        for r in t["rate"]:
            extra = f" · pagati {pc_euro(r['coperto'])}, mancano {pc_euro(r['residuo'])}" if r["stato"] == "parziale" or (r["stato"] == "scaduta" and r["coperto"]) else ""
            st.markdown(f"<div class='pc-riga {r['stato'].replace(' ', '')}'>{icone[r['stato']]} {_pc_e(pc_data_it(r.get('scadenza')))} · <b>{pc_euro(r.get('importo'))}</b>"
                        f" {_pc_e(r.get('nota') or '')}{extra}</div>", unsafe_allow_html=True)
    pag = sorted(p.get("pagamenti") or [], key=lambda x: x.get("data") or "", reverse=True)
    st.markdown(f"**💶 Pagamenti fatti ({len(pag)})**")
    if not pag:
        st.caption("Nessun pagamento registrato. Registra ogni bonifico o rata pagata e allega la ricevuta: così hai tutto pronto anche per la dichiarazione dei redditi.")
    for x in pag:
        n_all = len(x.get("allegati") or [])
        st.markdown(f"<div class='pc-riga pagata'>💶 <b>{pc_euro(x.get('importo'))}</b> · {_pc_e(pc_data_it(x.get('data')))} · {_pc_e(x.get('metodo'))}"
                    f"{(' · ' + _pc_e(x['riferimento'])) if x.get('riferimento') else ''}{' · 🧾 fattura' if x.get('fattura') else ''}"
                    f"{' · 📎 ' + str(n_all) if n_all else ''}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        vedi = st.session_state.setdefault("pc_vedi", [])
        if n_all and c1.button("🙈 Chiudi" if x["id"] in vedi else "👁️ Ricevuta", key=f"pc_pag_v_{x['id']}", width="stretch"):
            vedi.remove(x["id"]) if x["id"] in vedi else vedi.append(x["id"])
            st.rerun()
        if c2.button("✏️ Modifica", key=f"pc_pag_m_{x['id']}", width="stretch"):
            _pc_dialogo_pag(p, x, oggi_, t)
        if x["id"] in vedi:
            for r in x.get("allegati") or []:
                _sp_mostra(r)
    anno = oggi_.year
    tot, fatt = pc_detraibile_anno(p, anno)
    if tot:
        st.info(f"🧾 Pagato nel {anno}: **{pc_euro(tot)}** (con fattura: {pc_euro(fatt)}). Le spese mediche e dentistiche sono detraibili nella dichiarazione dei redditi "
                "se pagate con mezzi tracciabili (bonifico, carta) e con la fattura intestata alla persona: tieni qui fatture e ricevute.")


def _pc_dialogo_pag(p, x, oggi_, t):
    nuovo = x is None
    pr = t.get("prossima_rata")
    x = dict(x or {"id": pc_id(), "data": oggi_.isoformat(), "importo": (pr or {}).get("residuo"), "metodo": "Bonifico", "riferimento": "", "nota": "",
                   "fattura": False, "allegati": []})

    def _corpo():
        k = x["id"]
        c1, c2 = st.columns(2, gap="small")
        d = c1.date_input("Data del pagamento", value=pc_d(x.get("data")) or oggi_, format="DD/MM/YYYY", key=f"pc_p_d_{k}")
        imp = c2.number_input("Importo €", min_value=0.0, value=float(pc_num(x.get("importo")) or 0.0), step=10.0, format="%.2f", key=f"pc_p_i_{k}")
        metodo = st.selectbox("Come", PC_METODI, index=PC_METODI.index(x["metodo"]) if x.get("metodo") in PC_METODI else 0, key=f"pc_p_m_{k}")
        rif = st.text_input("Riferimento (CRO/TRN del bonifico, n. fattura…)", value=x.get("riferimento", ""), key=f"pc_p_r_{k}")
        nota = st.text_input("Nota", value=x.get("nota", ""), key=f"pc_p_n_{k}")
        fatt = st.checkbox("🧾 Ho ricevuto la fattura", value=bool(x.get("fattura")), key=f"pc_p_f_{k}")
        if x.get("allegati"):
            st.caption("📎 Già allegati: " + ", ".join(a.get("nome", "file") for a in x["allegati"]))
        nuovi = ar_uploader("📎 Ricevuta del bonifico / fattura (foto o PDF)", type=TIPI_FILE, accept_multiple_files=True, key=f"pc_p_up_{k}")
        if nuovi and st.button("🔎 Leggi la ricevuta e compila", key=f"pc_p_leggi_{k}", width="stretch"):
            u = nuovi[0]
            mime = getattr(u, "type", "") or ("application/pdf" if u.name.lower().endswith(".pdf") else "image/jpeg")
            with st.spinner("Leggo…"):
                l, _c = pc_leggi_documento(u.name, mime, u.getvalue(), oggi_)
            pg = (l or {}).get("pagamento") or {}
            if pg:
                if pg.get("data"):
                    st.session_state[f"pc_p_d_{k}"] = pc_d(pg["data"])
                if pg.get("importo"):
                    st.session_state[f"pc_p_i_{k}"] = float(pg["importo"])
                if pg.get("riferimento"):
                    st.session_state[f"pc_p_r_{k}"] = pg["riferimento"]
                st.rerun(scope="fragment")
            else:
                st.info("Non ho trovato importo e data nella ricevuta: scrivili tu.")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", type="primary", key=f"pc_p_ok_{k}", width="stretch", disabled=not imp):
            try:
                refs = _fa_salva_files(nuovi, esistenti=x.get("allegati")) if nuovi else []
            except Exception as e:
                st.error(f"Non sono riuscito a salvare il file: {e}")
                return
            nx = dict(x, data=d.isoformat(), importo=round(imp, 2), metodo=metodo, riferimento=rif.strip(), nota=nota.strip(), fattura=fatt,
                      allegati=list(x.get("allegati") or []) + refs)

            def _fn(pp):
                pp["pagamenti"] = [y for y in pp.get("pagamenti") or [] if y.get("id") != x["id"]] + [nx]
                if nuovo:
                    pp.setdefault("diario", []).append({"id": pc_id(), "data": d.isoformat(), "testo": f"Pagati {pc_euro(imp)} ({metodo})"})
            _pc_modifica(p["id"], _fn, "pagamento")
            st.rerun()
        if not nuovo and c2.button("🗑️ Elimina", key=f"pc_p_del_{k}", width="stretch"):
            _pc_modifica(p["id"], lambda pp: pp.__setitem__("pagamenti", [y for y in pp.get("pagamenti") or [] if y.get("id") != x["id"]]), "pagamento tolto")
            st.rerun()
    st.dialog("💶 Pagamento")(_corpo)()


def _pc_dialogo_rate(p, oggi_):
    def _corpo():
        import pandas as pd
        tot = pc_num((p.get("preventivo") or {}).get("totale")) or 0.0
        st.caption("Le scadenze delle rate: lo Scadenziario avvisa 7, 3 e 1 giorno prima e il giorno stesso, finché i pagamenti non le coprono.")
        with st.expander("⚙️ Crea il piano automaticamente", expanded=not p.get("rate")):
            c1, c2 = st.columns(2, gap="small")
            totale = c1.number_input("Totale €", min_value=0.0, value=float(tot), step=50.0, format="%.2f", key="pc_r_tot")
            acc = c2.number_input("Acconto €", min_value=0.0, value=0.0, step=50.0, format="%.2f", key="pc_r_acc")
            c1, c2, c3 = st.columns(3, gap="small")
            n = c1.number_input("Rate", min_value=1, max_value=120, value=12, key="pc_r_n")
            prima = c2.date_input("Prima rata", value=pc_aggiungi_mesi(oggi_, 1), format="DD/MM/YYYY", key="pc_r_pr")
            ogni = c3.selectbox("Ogni", [1, 2, 3, 6], format_func=lambda m: "mese" if m == 1 else f"{m} mesi", key="pc_r_ogni")
            if st.button("⚙️ Crea il piano (sostituisce quello qui sotto)", key="pc_r_gen", width="stretch"):
                st.session_state["pc_r_bozza"] = pc_genera_rate(totale, n, prima, ogni, acc, oggi_)
                st.session_state["pc_r_giro"] = st.session_state.get("pc_r_giro", 0) + 1
                st.rerun(scope="fragment")
        bozza = st.session_state.get("pc_r_bozza", p.get("rate") or [])
        df = pd.DataFrame([{"Scadenza": pc_d(r.get("scadenza")), "Importo €": pc_num(r.get("importo")), "Nota": r.get("nota", "")} for r in bozza]
                          or [{"Scadenza": None, "Importo €": None, "Nota": ""}])
        ed = st.data_editor(df, num_rows="dynamic", hide_index=True, width="stretch", key=f"pc_r_ed_{st.session_state.get('pc_r_giro', 0)}",
                            column_config={"Scadenza": st.column_config.DateColumn(format="DD/MM/YYYY"), "Importo €": st.column_config.NumberColumn(format="%.2f €")})
        somma = sum(pc_num(v) or 0 for v in ed["Importo €"].tolist())
        st.caption(f"Somma delle rate: **{pc_euro(somma)}**" + (f" · preventivo {pc_euro(tot)}" if tot else ""))
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva il piano", type="primary", key="pc_r_ok", width="stretch"):
            nuove = []
            for _i, r in ed.iterrows():
                dd = r.get("Scadenza")
                try:
                    dd = dd.date() if hasattr(dd, "date") else dd
                except Exception:
                    dd = None
                if dd and pc_num(r.get("Importo €")):
                    nuove.append({"id": pc_id(), "scadenza": pc_d(dd.isoformat()).isoformat(), "importo": round(pc_num(r["Importo €"]), 2), "nota": str(r.get("Nota") or "")})
            _pc_modifica(p["id"], lambda pp: pp.__setitem__("rate", nuove), "piano delle rate")
            st.session_state.pop("pc_r_bozza", None)
            st.rerun()
        if c2.button("Annulla", key="pc_r_no", width="stretch"):
            st.session_state.pop("pc_r_bozza", None)
            st.rerun()
    st.dialog("🗓️ Piano delle rate", width="large")(_corpo)()


# ---------------------------------------------------------------------------------------------------------------- documenti, preventivo, diario
def _pc_vista_documenti(p, persona, oggi_):
    docs = sorted(p.get("documenti") or [], key=lambda x: x.get("data") or "", reverse=True)
    with st.expander("➕ Aggiungi documenti", expanded=not docs):
        cat = st.selectbox("Che cos'è", PC_CAT_DOC, key=f"pc_d_cat_{p['id']}")
        tit = st.text_input("Titolo (facoltativo)", key=f"pc_d_tit_{p['id']}", placeholder="es. Fattura acconto, Radiografia panoramica…")
        dd = st.date_input("Data", value=oggi_, format="DD/MM/YYYY", key=f"pc_d_data_{p['id']}")
        giro = st.session_state.get(f"pc_d_giro_{p['id']}", 0)
        up = ar_uploader("Foto o PDF", type=TIPI_FILE, accept_multiple_files=True, key=f"pc_d_up_{p['id']}_{giro}")
        if up and st.button("💾 Salva i documenti", type="primary", key=f"pc_d_ok_{p['id']}", width="stretch"):
            try:
                refs = _fa_salva_files(up)
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
                refs = []
            if refs:
                nuovi = [{"id": pc_id(), "titolo": tit.strip() or r.get("nome", "documento"), "categoria": cat, "data": dd.isoformat(), "allegati": [r], "da_verificare": True}
                         for r in refs]
                _pc_modifica(p["id"], lambda pp: pp.setdefault("documenti", []).extend(nuovi), "documenti")
                st.session_state[f"pc_d_giro_{p['id']}"] = giro + 1
                st.rerun()
    if not docs:
        st.caption("Nessun documento: preventivo, fatture, ricevute, radiografie, consensi… stanno tutti qui.")
    vedi = st.session_state.setdefault("pc_vedi", [])
    for x in docs:
        _cl = x.get("classificazione") or {}
        _coll = ("<br><small>🔗 dai Documenti sanitari" + (": " + _pc_e(" · ".join(str(_cl[k]) for k in ("tipo", "specialita", "esame") if _cl.get(k))) if _cl else "")
                 + " — resta anche lì; «Togli» lo toglie solo da questo percorso</small>") if str(x.get("da") or "").startswith("docsan:") else ""
        st.markdown(f"<div class='pc-riga'>📄 <b>{_pc_e(x.get('categoria'))}</b> · {_pc_e(x.get('titolo'))} · <small>{_pc_e(pc_data_it(x.get('data')))}</small>{_coll}</div>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        if c1.button("🙈 Chiudi" if x["id"] in vedi else "👁️ Vedi / scarica", key=f"pc_doc_v_{x['id']}", width="stretch"):
            vedi.remove(x["id"]) if x["id"] in vedi else vedi.append(x["id"])
            st.rerun()
        if c2.button("🗑️ Togli", key=f"pc_doc_t_{x['id']}", width="stretch"):
            _pc_modifica(p["id"], lambda pp: pp.__setitem__("documenti", [y for y in pp.get("documenti") or [] if y.get("id") != x["id"]]), "documento tolto")
            st.rerun()
        if x.get("da_verificare"):
            ver = st.session_state.setdefault("pc_verifiche", {})
            vv = ver.get("doc:" + x["id"])
            if vv:
                _pc_mostra_verifica(vv)
            elif st.button("🤖 Controlla che sia di questa cartella", key=f"pc_doc_ver_{x['id']}", width="stretch"):
                with st.spinner("Leggo il documento e lo confronto con la cartella…"):
                    ver["doc:" + x["id"]] = _pc_verifica(p, x.get("allegati") or [], persona, oggi_)
                if ver["doc:" + x["id"]]["verdetto"] == "si":
                    _pc_modifica(p["id"], lambda pp, i=x["id"]: [d.update(da_verificare=False, verificato="si") for d in pp.get("documenti") or [] if d.get("id") == i], "documento verificato")
                st.rerun()
        if x["id"] in vedi:
            for r in x.get("allegati") or []:
                _sp_mostra(r)


def _pc_vista_preventivo(p):
    pv = p.get("preventivo") or {}
    if not (pv.get("righe") or pv.get("totale")):
        st.caption("Nessun preventivo inserito: aggiungilo con «✏️ Modifica dati» oppure caricalo in 📄 Documenti.")
    st.markdown(f"**Preventivo {_pc_e(pv.get('numero') or '')}** {('del ' + _pc_e(pc_data_it(pv.get('data')))) if pv.get('data') else ''}")
    for r in pv.get("righe") or []:
        st.markdown(f"<div class='pc-riga'>{_pc_e(r.get('descrizione'))}{(' · dente ' + _pc_e(r['dente'])) if r.get('dente') else ''} · <b>{pc_euro(r.get('importo'))}</b></div>",
                    unsafe_allow_html=True)
    if pv.get("totale"):
        st.markdown(f"**Totale: {pc_euro(pv['totale'])}**")
    if pv.get("note"):
        st.caption(pv["note"])
    if st.button("✏️ Modifica il preventivo", key=f"pc_pv_mod_{p['id']}", width="stretch"):
        _pc_dialogo_preventivo(p)


def _pc_dialogo_preventivo(p):
    def _corpo():
        pv = p.get("preventivo") or {}
        c1, c2, c3 = st.columns(3, gap="small")
        num = c1.text_input("Numero", value=str(pv.get("numero") or ""), key="pc_pv_n")
        d = c2.date_input("Data", value=pc_d(pv.get("data")), format="DD/MM/YYYY", key="pc_pv_d")
        tot = c3.number_input("Totale €", min_value=0.0, value=float(pc_num(pv.get("totale")) or 0.0), step=50.0, format="%.2f", key="pc_pv_t")
        ed = st.data_editor(_pc_tabella_righe(pv.get("righe") or []), num_rows="dynamic", hide_index=True, width="stretch", key="pc_pv_ed",
                            column_config={"Importo €": st.column_config.NumberColumn(format="%.2f €")})
        note = st.text_area("Condizioni / note", value=pv.get("note", ""), key="pc_pv_note")
        if st.button("💾 Salva", type="primary", key="pc_pv_ok", width="stretch"):
            rr = [{"descrizione": str(r["Descrizione"]).strip(), "dente": str(r.get("Dente") or "").strip(), "importo": pc_num(r.get("Importo €"))}
                  for _i, r in ed.iterrows() if str(r.get("Descrizione") or "").strip()]
            _pc_modifica(p["id"], lambda pp: pp.__setitem__("preventivo", {"numero": num.strip(), "data": d.isoformat() if d else "", "totale": round(tot, 2) if tot else None,
                                                                          "righe": rr, "note": note.strip()}), "preventivo")
            st.rerun()
    st.dialog("🦷 Preventivo", width="large")(_corpo)()


def _pc_vista_diario(p, oggi_):
    testo = st.text_area("📝 Scrivi una nota (cosa ha detto il dentista, come sta, cosa portare…)", key=f"pc_di_t_{p['id']}")
    if testo.strip() and st.button("💾 Aggiungi la nota", key=f"pc_di_ok_{p['id']}", width="stretch"):
        _pc_modifica(p["id"], lambda pp: pp.setdefault("diario", []).append({"id": pc_id(), "data": oggi_.isoformat(), "testo": testo.strip()}), "nota")
        st.session_state.pop(f"pc_di_t_{p['id']}", None)
        st.rerun()
    for data_, icona, txt in pc_timeline(p):
        st.markdown(f"<div class='pc-riga'>{icona} <small>{_pc_e(pc_data_it(data_))}</small> · {_pc_e(txt)}</div>", unsafe_allow_html=True)



# =====================================================================================================================
# DOCUMENTI GIÀ NELL'APP (o aggiunti dopo) CHE APPARTENGONO ALLA CARTELLA: ricerca precisa + verifica con l'IA
# =====================================================================================================================
_PC_PAROLE_VUOTE = {"centro", "medico", "medica", "studio", "odontoiatrico", "odontoiatrica", "dentistico", "dentale", "dental", "clinica", "poliambulatorio",
                    "dott", "dottssa", "dottor", "dottoressa", "snc", "srl", "spa", "sas", "della", "dello", "delle", "degli", "associato", "associati",
                    "torino", "milano", "roma", "napoli", "via", "corso", "piazza", "salute", "sanitario", "sanitaria", "direttore", "dir", "san"}


def _pc_parole(x):
    return {w for w in _pc_re.findall(r"[a-zà-ü]{4,}", str(x or "").lower()) if w not in _PC_PAROLE_VUOTE}


def _pc_cifre(x):
    return _pc_re.sub(r"\D", "", str(x or ""))


def pc_impronta(p):
    """Le «impronte» della cartella con cui riconoscere un documento: parole del nome dello studio, cognome del medico, P.IVA, telefoni, email,
    importi (preventivo, rate, pagamenti), finestra di date, persona."""
    s = p.get("struttura") or {}
    pv = p.get("preventivo") or {}
    importi = {round(v, 2) for v in [pc_num(pv.get("totale"))] + [pc_num(r.get("importo")) for r in (pv.get("righe") or []) + (p.get("rate") or []) + (p.get("pagamenti") or [])] if v}
    inizio = pc_d(pv.get("data")) or pc_d(p.get("creato_il")) or _pc_date.today()
    return {"parole": _pc_parole(s.get("nome")), "medico": _pc_parole(s.get("medico")), "piva": _pc_cifre(s.get("partita_iva")),
            "telefoni": {_pc_cifre(t)[-9:] for t in s.get("telefoni") or [] if len(_pc_cifre(t)) >= 8}, "email": str(s.get("email") or "").lower().strip(),
            "importi": importi, "dal": inizio - _pc_td(days=60), "dentista": "dent" in str(p.get("tipo", "")).lower(),
            "cf": str((p.get("paziente") or {}).get("codice_fiscale") or "").upper()}


def pc_punteggio(imp, testo, data=None, importo=None, specialita=""):
    """Quanto un documento (descritto da un testo: titolo, struttura, medico, riconosciuto…) somiglia alla cartella → (punti, motivi)."""
    punti, motivi = 0, []
    t = str(testo or "").lower()
    cifre = _pc_cifre(t)
    if imp["piva"] and len(imp["piva"]) == 11 and imp["piva"] in cifre:
        punti += 60
        motivi.append("stessa partita IVA dello studio")
    comuni = imp["parole"] & _pc_parole(t)
    if comuni:
        punti += 40
        motivi.append("stesso studio (" + ", ".join(sorted(comuni)) + ")")
    med = imp["medico"] & _pc_parole(t)
    if med:
        punti += 25
        motivi.append("stesso medico (" + ", ".join(sorted(med)) + ")")
    if any(x and x in cifre for x in imp["telefoni"]):
        punti += 30
        motivi.append("stesso numero di telefono")
    if imp["email"] and imp["email"] in t:
        punti += 30
        motivi.append("stessa email")
    if imp["cf"] and imp["cf"].lower() in t:
        punti += 20
        motivi.append("stesso codice fiscale del paziente")
    if importo and round(pc_num(importo) or 0, 2) in imp["importi"]:
        punti += 25
        motivi.append(f"importo {pc_euro(importo)} uguale a quello della cartella")
    if imp["dentista"] and _pc_re.search(r"odont|dent|ortodon|implant|igiene orale|parodont|ortopan|panoramic|endoral|bitewing", t + " " + str(specialita).lower()):
        punti += 10
        motivi.append("è un documento odontoiatrico")
    d = pc_d(data)
    if d and d < imp["dal"]:
        punti -= 30
        motivi.append(f"⚠️ è del {pc_data_it(d.isoformat())}, prima dell'inizio della cura")
    return punti, motivi


def pc_candidati(f, p):
    """I documenti di Salute della stessa persona (documenti sanitari, visite, prescrizioni, archivio) che sembrano di questa cartella e non ci sono già.
    → [{chiave, titolo, data, refs, motivi, punti, livello: alta|media, fonte, tipo}] dal più probabile."""
    imp = pc_impronta(p)
    gia = {a["id"] for a in pc_allegati(p)}
    scartati = set(p.get("scartati") or [])
    pid = p.get("profilo", "p0")
    out = []

    def valuta(chiave, titolo, data, refs, testo, fonte, importo=None, specialita="", tipo=""):
        refs = [r for r in refs if r and r.get("id") and r["id"] not in gia]
        if not refs or chiave in scartati:
            return
        punti, motivi = pc_punteggio(imp, testo, data, importo, specialita)
        if punti >= 35 and any(not m.startswith("è un documento") for m in motivi if not m.startswith("⚠️")):
            out.append({"chiave": chiave, "titolo": titolo, "data": data or "", "refs": refs, "motivi": motivi, "punti": punti,
                        "livello": "alta" if punti >= 60 else "media", "fonte": fonte, "tipo": tipo})
    prof = next((x for x in f.get("profili") or [] if x.get("id") == pid), {})
    for x in prof.get("docsan") or []:
        ric = x.get("riconosciuto") or {}
        testo = " ".join(str(v) for v in [x.get("titolo"), x.get("tipo"), x.get("struttura"), x.get("medico"), x.get("conclusioni"), x.get("note"),
                                          (x.get("file") or {}).get("nome")] + [str(v) for v in ric.values()])
        valuta(f"docsan:{x.get('id')}", x.get("titolo") or x.get("tipo") or "Documento sanitario", x.get("data"), [x.get("file")] + list(x.get("allegati") or []),
               testo, "Documenti sanitari", ric.get("importo") or x.get("importo"), x.get("specialita") or "", x.get("tipo") or "")
    for x in f.get("visite") or []:
        if x.get("profilo", "p0") != pid:
            continue
        testo = " ".join(str(x.get(k) or "") for k in ("categoria", "medico", "motivo", "struttura", "note", "controlli"))
        valuta(f"visita:{x.get('id')}", f"Visita: {x.get('categoria') or ''} {x.get('medico') or ''}".strip(), x.get("data"), list(x.get("allegati") or []),
               testo + " " + " ".join(a.get("nome", "") for a in x.get("allegati") or []), "Visite", None, x.get("categoria") or "", "Visita")
    for x in f.get("prescrizioni") or []:
        if x.get("profilo", "p0") != pid:
            continue
        testo = " ".join(str(x.get(k) or "") for k in ("tipo", "medico", "prescritto", "farmaco", "descrizione", "note"))
        valuta(f"presc:{x.get('id')}", f"Prescrizione {x.get('tipo') or ''}", x.get("data"), list(x.get("allegati") or []), testo, "Prescrizioni", None, "", "Prescrizione")
    return sorted(out, key=lambda c: -c["punti"])


def pc_confronta(p, lettura, persona):
    """Confronto PRECISO fra quello che l'IA ha letto nel documento e la cartella → (verdetto: si|no|incerto, controlli[(ok: True/False/None, frase)])."""
    s = p.get("struttura") or {}
    ls = (lettura or {}).get("struttura") or {}
    ctrl = []
    piva_c, piva_d = _pc_cifre(s.get("partita_iva")), _pc_cifre(ls.get("partita_iva"))
    if piva_c and piva_d:
        ctrl.append((piva_c == piva_d, f"Partita IVA: documento {piva_d} · cartella {piva_c}"))
    pn = _pc_parole(s.get("nome")) & _pc_parole(ls.get("nome"))
    if s.get("nome") and ls.get("nome"):
        ctrl.append((bool(pn), f"Studio: «{ls.get('nome')}» · cartella «{s.get('nome')}»"))
    tc = {_pc_cifre(t)[-9:] for t in s.get("telefoni") or [] if len(_pc_cifre(t)) >= 8}
    td = {_pc_cifre(t)[-9:] for t in ls.get("telefoni") or [] if len(_pc_cifre(t)) >= 8}
    if tc and td:
        ctrl.append((bool(tc & td), "Telefono dello studio " + ("uguale" if tc & td else "diverso")))
    cf_c = str((p.get("paziente") or {}).get("codice_fiscale") or "").upper()
    cf_d = str((lettura or {}).get("codice_fiscale") or "").upper()
    if cf_c and cf_d:
        ctrl.append((cf_c == cf_d, f"Codice fiscale del paziente: {'uguale' if cf_c == cf_d else 'DIVERSO (' + cf_d + ')'}"))
    paz = (lettura or {}).get("paziente") or ""
    if paz and persona:
        uguali = _pc_parole(paz) & _pc_parole(persona)
        ctrl.append((bool(uguali) if len(_pc_parole(persona)) else None, f"Paziente sul documento: «{paz}» · cartella di {persona}"))
    imp = pc_impronta(p)
    valori = [x for x in [((lettura or {}).get("pagamento") or {}).get("importo"), ((lettura or {}).get("preventivo") or {}).get("totale")] if x]
    if valori and imp["importi"]:
        ok = any(round(pc_num(v) or 0, 2) in imp["importi"] for v in valori)
        ctrl.append((ok if ok else None, "Importo " + ", ".join(pc_euro(v) for v in valori) + (" presente nella cartella" if ok else " non ancora nella cartella (potrebbe essere un pagamento nuovo)")))
    no = [c for c in ctrl if c[0] is False]
    si = [c for c in ctrl if c[0] is True]
    forte_no = any(c[0] is False and (c[1].startswith("Partita IVA") or c[1].startswith("Codice fiscale")) for c in ctrl)
    forte_si = any(c[0] is True and (c[1].startswith("Partita IVA") or c[1].startswith("Telefono") or c[1].startswith("Codice fiscale")) for c in ctrl)
    if forte_no or (no and not si):
        return "no", ctrl
    if (forte_si or len(si) >= 2) and not no:
        return "si", ctrl
    return "incerto", ctrl


def _pc_mime_ref(r):
    m = r.get("mime") or ""
    n = str(r.get("nome") or "").lower()
    return m or ("application/pdf" if n.endswith(".pdf") else "image/jpeg")


def _pc_verifica(p, refs, persona, oggi_):
    """Legge (IA + testo) il primo file e lo confronta con la cartella. → dict salvato in sessione."""
    for r in refs:
        dati = _sp_dati_file(r) if "_sp_dati_file" in globals() else b""
        if not dati:
            continue
        lettura, come = pc_leggi_documento(r.get("nome", "documento"), _pc_mime_ref(r), dati, oggi_)
        verdetto, ctrl = pc_confronta(p, lettura, persona)
        return {"verdetto": verdetto, "controlli": ctrl, "come": come, "lettura": lettura}
    return {"verdetto": "incerto", "controlli": [(None, "Non riesco ad aprire il file.")], "come": "", "lettura": {}}


def _pc_cat_da_lettura(lettura, tipo=""):
    t = (lettura or {}).get("tipo") or ""
    return {"preventivo": "Preventivo", "appuntamento": "Promemoria appuntamento", "fattura": "Fattura", "ricevuta": "Ricevuta di pagamento"}.get(t) or \
        ("Radiografia / esame" if _pc_re.search(r"radiogr|ortopan|tac|esame|referto", str(tipo).lower()) else "Altro")


def _pc_mostra_verifica(v):
    icona = {"si": "✅ Corrisponde a questa cartella", "no": "❌ NON corrisponde: è di un altro studio o di un'altra persona", "incerto": "❓ Non sono sicuro: controlla tu"}
    (st.success if v["verdetto"] == "si" else st.error if v["verdetto"] == "no" else st.warning)(icona[v["verdetto"]] + (f" · letto con {v['come']}" if v.get("come") else ""))
    for ok, frase in v["controlli"]:
        st.markdown(f"- {'✅' if ok is True else '❌' if ok is False else '➖'} {_pc_e(frase)}")


def _pc_vista_collegare(p, cand, persona, oggi_):
    st.caption("Ho cercato tra i documenti di Salute di questa persona (documenti sanitari, visite, prescrizioni) quelli che sembrano di questa cura: "
               "stesso studio, medico, partita IVA, telefono, importi e date. Con **🤖 Verifica** l'IA legge il file e lo confronta punto per punto. "
               "Niente viene spostato senza la tua conferma; il documento resta anche dov'era.")
    ver = st.session_state.setdefault("pc_verifiche", {})
    if len(cand) > 1 and st.button(f"🤖 Verifica tutti ({min(len(cand), 8)})", key=f"pc_ver_tutti_{p['id']}", width="stretch"):
        with st.spinner("Leggo e confronto i documenti… (può volerci qualche minuto)"):
            for c in cand[:8]:
                if c["chiave"] not in ver:
                    ver[c["chiave"]] = _pc_verifica(p, c["refs"], persona, oggi_)
        st.rerun()
    for c in cand:
        st.markdown(f"<div class='pc-riga'>{'🟢' if c['livello'] == 'alta' else '🟡'} <b>{_pc_e(c['titolo'])}</b> · <small>{_pc_e(pc_data_it(c['data']))} · {_pc_e(c['fonte'])}</small>"
                    f"<br><small>{_pc_e(' · '.join(c['motivi']))}</small></div>", unsafe_allow_html=True)
        v = ver.get(c["chiave"])
        if v:
            _pc_mostra_verifica(v)
        c1, c2, c3 = st.columns(3, gap="small")
        if not v and c1.button("🤖 Verifica", key=f"pc_ver_{c['chiave']}", width="stretch"):
            with st.spinner("Leggo il documento e lo confronto con la cartella…"):
                ver[c["chiave"]] = _pc_verifica(p, c["refs"], persona, oggi_)
            st.rerun()
        aggiungi = c2.button("➕ Aggiungi", key=f"pc_agg_{c['chiave']}", width="stretch", type="primary" if (v or {}).get("verdetto") == "si" else "secondary",
                             disabled=(v or {}).get("verdetto") == "no")
        if c3.button("✖️ Non c'entra", key=f"pc_sca_{c['chiave']}", width="stretch"):
            _pc_modifica(p["id"], lambda pp: pp.__setitem__("scartati", list(set(pp.get("scartati") or []) | {c["chiave"]})), "documento escluso")
            st.rerun()
        pag = ((v or {}).get("lettura") or {}).get("pagamento") or {}
        reg = False
        if pag.get("importo") and (v or {}).get("verdetto") != "no":
            reg = st.checkbox(f"💶 Registra anche il pagamento di {pc_euro(pag['importo'])}" + (f" del {pc_data_it(pag.get('data'))}" if pag.get("data") else ""),
                              value=round(pc_num(pag["importo"]) or 0, 2) not in {round(pc_num(x.get("importo")) or 0, 2) for x in p.get("pagamenti") or []},
                              key=f"pc_regpag_{c['chiave']}")
        if aggiungi:
            lett = (v or {}).get("lettura") or {}
            cat = _pc_cat_da_lettura(lett, c.get("tipo"))

            def _fn(pp, c=c, cat=cat, reg=reg, pag=pag):
                pp.setdefault("documenti", []).append({"id": pc_id(), "titolo": c["titolo"], "categoria": cat, "data": c["data"] or oggi_.isoformat(), "allegati": c["refs"],
                                                       "da": c["chiave"], "verificato": (v or {}).get("verdetto", "")})
                if reg:
                    pp.setdefault("pagamenti", []).append({"id": pc_id(), "data": pag.get("data") or c["data"] or oggi_.isoformat(), "importo": round(pc_num(pag["importo"]), 2),
                                                           "metodo": pag.get("metodo") if pag.get("metodo") in PC_METODI else "Bonifico", "riferimento": pag.get("riferimento", ""),
                                                           "nota": "dal documento collegato", "fattura": cat == "Fattura", "allegati": c["refs"]})
                pp.setdefault("diario", []).append({"id": pc_id(), "data": oggi_.isoformat(), "testo": f"Collegato «{c['titolo']}» ({c['fonte']})"})
            _pc_modifica(p["id"], _fn, "documento collegato")
            ver.pop(c["chiave"], None)
            st.session_state["fa_msg"] = f"✅ «{c['titolo']}» aggiunto alla cartella."
            st.rerun()


# =====================================================================================================================
# COLLEGAMENTI: archivio dei file di Salute e «↗️ Apri» dallo Scadenziario
# =====================================================================================================================
if "ar_voci" in globals() and not globals().get("_pc_ar_fatto"):
    _pc_ar_voci_orig = ar_voci
    if "Percorsi di cura" not in AR_CATEGORIE:
        AR_CATEGORIE.append("Percorsi di cura")

    def ar_voci(f, nomi_profili):                                                                      # noqa: F811
        voci = _pc_ar_voci_orig(f, nomi_profili)
        visti = {v["id"] for v in voci}
        for p in f.get("percorsi") or []:
            for a in pc_allegati(p):
                if a["id"] not in visti:
                    visti.add(a["id"])
                    voci.append({"id": a["id"], "nome": a.get("nome") or "file", "mime": _ar_mime(a) if "_ar_mime" in globals() else a.get("mime", ""),
                                 "categoria": "Percorsi di cura", "collegato": f"Percorso: {p.get('titolo', '')}", "pid": p.get("profilo", "p0"),
                                 "persona": nomi_profili.get(p.get("profilo", "p0"), ""), "data": p.get("creato_il") or "", "originale": bool(a.get("originale"))})
        return voci
    _pc_ar_fatto = True

if "_sz_apri_origine" in globals() and not globals().get("_pc_sz_fatto"):
    _pc_sz_apri_orig = _sz_apri_origine

    def _sz_apri_origine(v):                                                                           # noqa: F811
        nav = v.get("nav") or {}
        if nav.get("percorso"):
            st.session_state["pc_aperto"] = nav["percorso"]
            if nav.get("profilo"):
                st.session_state["fa_profilo"] = nav["profilo"]
        return _pc_sz_apri_orig(v)
    _pc_sz_fatto = True
