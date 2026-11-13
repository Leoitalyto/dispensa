# -*- coding: utf-8 -*-
"""CASA · 🏢 AMMINISTRAZIONE (la prima scheda di Casa, prima di Beni, Documenti, Manutenzioni e Riferimenti).

Un centro di gestione amministrativa della casa, con badge indipendenti:
• 🏢 DATI AMMINISTRAZIONE: scheda dell'amministratore (studio, telefoni, email, PEC, codice fiscale/P.IVA, IBAN…) con chiamata, email e PEC a un tocco;
• 💶 SPESE E SCADENZE: spese condominiali e amministrative a rate; le scadenze si generano da sole dal numero di rate e dalla prima data; pagamenti anche PARZIALI con storico;
  stati «da pagare / in scadenza / pagata / scaduta»; riepilogo (totale anno, pagato, da pagare, scadute); allegati presi dai Documenti di Casa (senza toccare il loro sistema di caricamento);
• 🛠️ CONTATTI E INTERVENTI, ♻️ RACCOLTA DIFFERENZIATA e 🛋️ RITIRO INGOMBRANTI: vedi più sotto.
• 📥 In Spese e scadenze si può IMPORTARE un documento (avviso di pagamento, piano rate, bollettino, ricevuta): viene letto con lo stesso sistema di Documenti e propone la spesa con le sue rate.

COME SI INTEGRA (senza toccare quello che c'è):
• i dati stanno nel file personale, sotto `casa`, in liste NUOVE (`amministratori`, `spese_amm`…) che portano la stessa etichetta `casa_id` degli altri elementi di Casa: con più abitazioni
  i dati restano separati (`ca_vista_casa`, `_ca_salva`, «Togli una casa» funzionano da soli);
• si salva con `_ca_salva` (quindi Cestino, storico delle modifiche e copie di scorta valgono come per il resto); i documenti allegati sono quelli già archiviati in Documenti;
• i pagamenti, gli stati e le ricevute seguono lo stesso modo di ragionare delle bollette di Casa; gli avvisi usano gli stessi canali già scelti dalla persona (tappa 2)."""
import calendar
import html as _amm_h
import re
import uuid
from datetime import date, datetime, timedelta

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# LOGICA (senza Streamlit: si prova da sola)
# ---------------------------------------------------------------------------------------------------------------------
AMM_PERIODI = {"Una sola volta": 0, "Ogni mese": 1, "Ogni 2 mesi": 2, "Ogni trimestre": 3, "Ogni 4 mesi": 4, "Ogni semestre": 6, "Ogni anno": 12, "Altro (scelgo io i mesi)": None}
AMM_CATEGORIE = ["Spese condominiali ordinarie", "Rata straordinaria o lavori", "Riscaldamento", "Acqua", "Pulizia scale", "Ascensore", "Assicurazione", "Fondo cassa o riserva",
                 "Conguaglio", "Imposte e tasse (IMU, TARI…)", "Altro"]
AMM_GIORNI_AVVISO = [60, 30, 15, 10, 7, 5, 3, 2, 1, 0]
AMM_GIORNI_DEFAULT = [30, 15, 7, 3, 1]
AMM_FINESTRA_IN_SCADENZA = 15                       # una rata si dice «in scadenza» da 15 giorni prima
AMM_STATI = {"pagata": ("🟢", "Pagata", "#1b5e20"), "da_pagare": ("🔵", "Da pagare", "#0d47a1"), "in_scadenza": ("🟠", "In scadenza", "#e65100"), "scaduta": ("🔴", "Scaduta", "#b71c1c")}


def amm_id():
    return uuid.uuid4().hex[:8]


def amm_importo(x):
    """«1.234,56», «1234,56», «1234.56», 1234.56 → 1234.56 (None se non è un numero)."""
    if isinstance(x, (int, float)):
        return round(float(x), 2)
    s = str(x or "").replace("€", "").replace(" ", "").strip()
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") == 1 and len(s.split(".")[1]) <= 2:
        pass                                                           # «1234.56»: punto decimale
    else:
        s = s.replace(".", "")                                         # «1.234» = mille duecento trentaquattro
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def amm_euro(x):
    s = f"{float(x or 0):,.2f}"
    return "€ " + s.replace(",", "§").replace(".", ",").replace("§", ".")


def amm_aggiungi_mesi(d, n):
    """La stessa data fra n mesi (a fine mese: 31 gennaio + 1 mese = 28 febbraio)."""
    m = d.month - 1 + n
    a, m = d.year + m // 12, m % 12 + 1
    return date(a, m, min(d.day, calendar.monthrange(a, m)[1]))


def amm_genera_scadenze(prima, n, mesi):
    """Le date di n rate: la prima e poi una ogni `mesi` mesi (partendo SEMPRE dalla prima, così i giorni a fine mese non scivolano)."""
    n = max(1, int(n or 1))
    if not mesi or n == 1:
        return [prima]
    return [amm_aggiungi_mesi(prima, mesi * k) for k in range(n)]


def amm_ripartisci(totale, n):
    """Divide un importo in n rate uguali al centesimo: la differenza va sull'ultima."""
    n = max(1, int(n or 1))
    cent = int(round(float(totale) * 100))
    base = cent // n
    rate = [base] * n
    rate[-1] += cent - base * n
    return [round(c / 100, 2) for c in rate]


def amm_pagato(rata):
    return round(sum(float(p.get("importo") or 0) for p in rata.get("pagamenti", [])), 2)


def amm_residuo(rata):
    return max(0.0, round(float(rata.get("importo") or 0) - amm_pagato(rata), 2))


def amm_stato_rata(rata, oggi_, finestra=AMM_FINESTRA_IN_SCADENZA):
    if amm_residuo(rata) <= 0.004:
        return "pagata"
    try:
        g = (date.fromisoformat(rata["scadenza"]) - oggi_).days
    except (KeyError, ValueError, TypeError):
        return "da_pagare"
    if g < 0:
        return "scaduta"
    return "in_scadenza" if g <= finestra else "da_pagare"


def amm_stato_spesa(spesa, oggi_, finestra=AMM_FINESTRA_IN_SCADENZA):
    stati = [amm_stato_rata(r, oggi_, finestra) for r in spesa.get("rate", [])]
    if not stati or all(s == "pagata" for s in stati):
        return "pagata"
    for s in ("scaduta", "in_scadenza"):
        if s in stati:
            return s
    return "da_pagare"


def amm_crea_spesa(descrizione, categoria, importo_totale, n_rate, prima_scadenza, mesi, amministratore_id="", note="", avvisi_giorni=None, rinnovo_auto=False, importi=None):
    """Una spesa con le sue rate già generate. `importi`: elenco facoltativo degli importi di ogni rata (altrimenti rate uguali)."""
    n = max(1, int(n_rate or 1))
    date_r = amm_genera_scadenze(prima_scadenza, n, mesi)
    imp = list(importi) if importi and len(importi) == n else amm_ripartisci(importo_totale, n)
    return {"id": amm_id(), "descrizione": descrizione.strip(), "categoria": categoria, "importo_totale": round(float(importo_totale), 2), "periodicita_mesi": mesi or 0,
            "rinnovo_auto": bool(rinnovo_auto), "amministratore_id": amministratore_id, "note": note.strip(), "allegati": [],
            "avvisi_giorni": sorted(set(avvisi_giorni if avvisi_giorni is not None else AMM_GIORNI_DEFAULT), reverse=True), "avvisi_attivi": True,
            "creata_il": date.today().isoformat(),
            "rate": [{"id": amm_id(), "n": k + 1, "scadenza": d.isoformat(), "importo": imp[k], "pagamenti": []} for k, d in enumerate(date_r)],
            "storico": [{"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "testo": f"Spesa creata: {n} rata/e da {amm_euro(imp[0])}"}]}


def amm_rate_ordinate(spesa):
    return sorted(spesa.get("rate", []), key=lambda r: (r.get("scadenza") or "", r.get("n") or 0))


def _amm_log(spesa, testo):
    spesa.setdefault("storico", []).append({"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "testo": testo})


def amm_aggiungi_rate_ricorrenti(spesa, oggi_, minimo=2):
    """Per le spese che si ripetono sempre (rinnovo automatico): si assicura che ci siano almeno `minimo` rate non pagate nel futuro. NON crea doppioni (stessa data)."""
    mesi = spesa.get("periodicita_mesi") or 0
    rate = amm_rate_ordinate(spesa)
    if not spesa.get("rinnovo_auto") or not mesi or not rate:
        return 0
    esistenti = {r["scadenza"] for r in rate}
    ultima = date.fromisoformat(rate[-1]["scadenza"])
    base = date.fromisoformat(rate[0]["scadenza"])
    k = round(((ultima.year - base.year) * 12 + ultima.month - base.month) / mesi)
    nuove = 0
    while sum(1 for r in spesa["rate"] if amm_residuo(r) > 0.004 and date.fromisoformat(r["scadenza"]) >= oggi_) < minimo and nuove < 24:
        k += 1
        d = amm_aggiungi_mesi(base, mesi * k)
        if d.isoformat() in esistenti:
            continue
        esistenti.add(d.isoformat())
        spesa["rate"].append({"id": amm_id(), "n": len(spesa["rate"]) + 1, "scadenza": d.isoformat(), "importo": rate[-1]["importo"], "pagamenti": []})
        nuove += 1
    if nuove:
        _amm_log(spesa, f"Aggiunte {nuove} scadenze (la spesa si ripete)")
    return nuove


def amm_registra_pagamento(spesa, rata_id, importo, data_iso, modo="", nota="", ricevuta_id=""):
    """(ok, messaggio). Un pagamento può essere anche PARZIALE; non può superare quanto resta da pagare."""
    r = next((x for x in spesa.get("rate", []) if x.get("id") == rata_id), None)
    if not r:
        return False, "Rata non trovata."
    imp = amm_importo(importo)
    if imp is None or imp <= 0:
        return False, "Scrivi un importo maggiore di zero."
    if imp > amm_residuo(r) + 0.004:
        return False, f"L'importo supera quello che resta da pagare ({amm_euro(amm_residuo(r))})."
    r.setdefault("pagamenti", []).append({"id": amm_id(), "data": data_iso, "importo": round(imp, 2), "modo": modo, "nota": nota.strip(), "ricevuta_id": ricevuta_id})
    _amm_log(spesa, f"Pagamento di {amm_euro(imp)} sulla rata {r.get('n')} ({data_iso})" + (" — rata saldata" if amm_residuo(r) <= 0.004 else f" — restano {amm_euro(amm_residuo(r))}"))
    if amm_residuo(r) <= 0.004 and spesa.get("rinnovo_auto"):
        amm_aggiungi_rate_ricorrenti(spesa, date.fromisoformat(data_iso) if data_iso else date.today())
    return True, "Pagamento registrato."


def amm_annulla_pagamento(spesa, rata_id, pag_id):
    r = next((x for x in spesa.get("rate", []) if x.get("id") == rata_id), None)
    if not r:
        return False
    p = next((x for x in r.get("pagamenti", []) if x.get("id") == pag_id), None)
    if not p:
        return False
    r["pagamenti"] = [x for x in r["pagamenti"] if x.get("id") != pag_id]
    _amm_log(spesa, f"Annullato il pagamento di {amm_euro(p.get('importo'))} del {p.get('data')} sulla rata {r.get('n')}")
    return True


def amm_modifica_rata(spesa, rata_id, scadenza_iso=None, importo=None):
    """(ok, messaggio). Si possono cambiare data e importo senza perdere i pagamenti già fatti; l'importo non può scendere sotto il già pagato."""
    r = next((x for x in spesa.get("rate", []) if x.get("id") == rata_id), None)
    if not r:
        return False, "Rata non trovata."
    if importo is not None:
        imp = amm_importo(importo)
        if imp is None or imp <= 0:
            return False, "Scrivi un importo valido."
        if imp < amm_pagato(r) - 0.004:
            return False, f"Hai già pagato {amm_euro(amm_pagato(r))}: l'importo non può essere più basso."
    if scadenza_iso:
        try:
            date.fromisoformat(scadenza_iso)
        except ValueError:
            return False, "Data non valida."
        if any(x.get("scadenza") == scadenza_iso and x.get("id") != rata_id for x in spesa["rate"]):
            return False, "C'è già un'altra rata con questa data."
    if importo is not None and abs(imp - float(r.get("importo") or 0)) > 0.004:
        _amm_log(spesa, f"Rata {r.get('n')}: importo da {amm_euro(r.get('importo'))} a {amm_euro(imp)}")
        r["importo"] = round(imp, 2)
    if scadenza_iso and scadenza_iso != r.get("scadenza"):
        _amm_log(spesa, f"Rata {r.get('n')}: scadenza dal {r.get('scadenza')} al {scadenza_iso}")
        r["scadenza"] = scadenza_iso
    spesa["importo_totale"] = round(sum(float(x.get("importo") or 0) for x in spesa["rate"]), 2)
    return True, "Rata aggiornata."


def amm_riepilogo(spese, anno, oggi_):
    """Totali dell'anno (sulle rate che scadono quell'anno) e le scadute di tutti gli anni."""
    tot = pag = 0.0
    scadute = []
    for s in spese:
        for r in s.get("rate", []):
            d = r.get("scadenza") or ""
            if d.startswith(str(anno)):
                tot += float(r.get("importo") or 0)
                pag += amm_pagato(r)
            if amm_stato_rata(r, oggi_) == "scaduta":
                scadute.append((s, r))
    return {"totale": round(tot, 2), "pagato": round(pag, 2), "da_pagare": round(tot - pag, 2), "scadute": scadute}


def amm_prossime(spese, oggi_, quante=8):
    """Le prossime rate da pagare (non pagate, non ancora scadute), dalla più vicina."""
    out = []
    for s in spese:
        for r in s.get("rate", []):
            if amm_residuo(r) > 0.004 and (r.get("scadenza") or "") >= oggi_.isoformat():
                out.append((r["scadenza"], s, r))
    return [(s, r) for _d, s, r in sorted(out, key=lambda x: x[0])[:quante]]


def amm_storico_pagamenti(spese):
    out = []
    for s in spese:
        for r in s.get("rate", []):
            for p in r.get("pagamenti", []):
                out.append((p.get("data") or "", s, r, p))
    return sorted(out, key=lambda x: x[0], reverse=True)


def amm_iban_valido(iban):
    """Controllo del codice di controllo IBAN (ISO 13616). Serve per avvisare di un errore di battitura, non per vietare."""
    s = "".join(str(iban or "").split()).upper()
    if len(s) < 15 or len(s) > 34 or not s[:2].isalpha() or not s[2:4].isdigit() or not s.isalnum():
        return False
    r = s[4:] + s[:4]
    return int("".join(str(int(ch, 36)) for ch in r)) % 97 == 1


def amm_rate_vicine(spese, oggi_, giorni=10):
    """Per gli avvisi DENTRO l'app: le rate non pagate scadute (fino a un anno) o in scadenza entro `giorni`: [(«Spesa · rata 2/4», giorni, residuo)]."""
    out = []
    for s in spese:
        rate = amm_rate_ordinate(s)
        for k, r in enumerate(rate, 1):
            if amm_residuo(r) <= 0.004:
                continue
            g = amm_giorni_a(r.get("scadenza"), oggi_)
            if g is not None and -365 <= g <= giorni:
                out.append((f"{s.get('descrizione', 'Spesa')} · rata {r.get('n') or k}/{len(rate)}", g, amm_residuo(r)))
    return sorted(out, key=lambda t: t[1])


def _ics_testo(t):
    return str(t or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _ics_riga(riga):
    """Una riga del file calendario, spezzata a 75 byte come richiede lo standard."""
    b, out = riga.encode("utf-8"), []
    while len(b) > 75:
        taglio = 75
        while taglio > 0 and (b[taglio] & 0xC0) == 0x80:
            taglio -= 1
        out.append(b[:taglio].decode("utf-8"))
        b = b" " + b[taglio:]
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)


def amm_ics(eventi, nome="Amministrazione casa"):
    """Un file calendario (.ics) con allarmi: il telefono SUONA anche con l'app e tutto il resto chiusi.
    eventi: [{uid, titolo, descrizione, data (date), allarmi: [giorni prima alle 9:00; 0 = il giorno stesso], ripeti_settimanale: 'MO'..'SU' o '', sera_prima: ora (es. 20) oppure None}]
    Gli «uid» sono stabili: importando di nuovo lo stesso file gli eventi si AGGIORNANO, non si duplicano."""
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//La nostra dispensa//Amministrazione casa//IT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_ics_testo(nome)}"]
    ora = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for e in eventi:
        d = e["data"]
        righe += ["BEGIN:VEVENT", f"UID:{e['uid']}@dispensa", f"DTSTAMP:{ora}", f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}",
                  f"SUMMARY:{_ics_testo(e['titolo'])}"]
        if e.get("descrizione"):
            righe.append(f"DESCRIPTION:{_ics_testo(e['descrizione'])}")
        if e.get("ripeti_settimanale"):
            righe.append(f"RRULE:FREQ=WEEKLY;BYDAY={e['ripeti_settimanale']}")
        for xd in e.get("escludi") or []:
            righe.append(f"EXDATE;VALUE=DATE:{xd.strftime('%Y%m%d')}")                   # un giorno in cui la ripetizione settimanale NON vale (variazione)
        righe.append("TRANSP:TRANSPARENT")
        for gp, hhmm in e.get("allarmi_orari") or []:                                     # «giorni prima, alle HH:MM»: l'evento di un'intera giornata comincia a mezzanotte
            try:
                minuti = -int(gp) * 1440 + int(hhmm.split(":")[0]) * 60 + int(hhmm.split(":")[1])
            except (ValueError, IndexError):
                continue
            righe += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_testo(e['titolo'])}", f"TRIGGER:{'-' if minuti < 0 else ''}PT{abs(minuti)}M", "END:VALARM"]
        for g in sorted(set(e.get("allarmi") or []), reverse=True):
            righe += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_testo(e['titolo'])}", ("TRIGGER:PT9H" if g == 0 else f"TRIGGER:-P{g - 1}DT15H"), "END:VALARM"]
        if e.get("sera_prima") is not None:                                           # la sera prima all'ora scelta (es. 20): «un giorno prima» meno (24 − ora) ore
            righe += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_testo(e['titolo'])}", f"TRIGGER:-PT{24 - int(e['sera_prima'])}H", "END:VALARM"]
        righe.append("END:VEVENT")
    righe.append("END:VCALENDAR")
    return ("\r\n".join(_ics_riga(r) for r in righe) + "\r\n").encode("utf-8")


def amm_eventi_rate(spese, oggi_, giorni_default=None):
    """Gli eventi del calendario per le rate non ancora pagate che non sono già scadute."""
    ev = []
    for s in spese:
        if s.get("avvisi_attivi") is False:
            continue
        rate = amm_rate_ordinate(s)
        for k, r in enumerate(rate, 1):
            if amm_residuo(r) <= 0.004 or (r.get("scadenza") or "") < oggi_.isoformat():
                continue
            ev.append({"uid": "rata-" + str(r["id"]), "titolo": f"💶 {s.get('descrizione', 'Spesa')} – rata {r.get('n') or k}/{len(rate)}: {amm_euro(amm_residuo(r))}",
                       "descrizione": f"Amministrazione casa · {s.get('categoria', '')}. Registra il pagamento nell'app La nostra dispensa → Casa → Amministrazione.",
                       "data": date.fromisoformat(r["scadenza"]), "allarmi": [int(g) for g in (s.get("avvisi_giorni") or giorni_default or AMM_GIORNI_DEFAULT)]})
    return ev


def amm_giorni_a(data_iso, oggi_):
    try:
        return (date.fromisoformat(data_iso) - oggi_).days
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------------------------------------------------
# INTERFACCIA
# ---------------------------------------------------------------------------------------------------------------------
_AMM_CSS = """<style>
.st-key-amm_hub[data-testid='stVerticalBlock'],.st-key-amm_hub [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:6px 0 12px}
.st-key-amm_hub button{width:100% !important;min-height:78px !important;border-radius:20px !important;color:#fff !important;font-weight:900 !important;border:2px solid rgba(255,255,255,.55) !important;
 box-shadow:0 4px 0 rgba(0,0,0,.25) !important;padding:8px !important}
.st-key-amm_hub button p{color:#fff !important;font-weight:900 !important;font-size:1.02rem !important;line-height:1.2 !important;text-shadow:0 1px 3px rgba(0,0,0,.55);margin:0}
.st-key-amm_b_dati button{background:linear-gradient(135deg,#0d47a1,#42a5f5) !important}
.st-key-amm_b_spese button{background:linear-gradient(135deg,#1b5e20,#66bb6a) !important}
.st-key-amm_b_contatti button{background:linear-gradient(135deg,#e65100,#ffb74d) !important}
.st-key-amm_b_raccolta button{background:linear-gradient(135deg,#4a148c,#ab47bc) !important}
.st-key-amm_b_ingombranti button{background:linear-gradient(135deg,#37474f,#90a4ae) !important}
.st-key-amm_b_ingombranti{grid-column:1 / -1}
.amm-card{background:rgba(255,255,255,.86);border-radius:18px;padding:12px 14px;margin:8px 0;border:1px solid rgba(0,0,0,.06);box-shadow:0 3px 10px rgba(0,0,0,.07)}
.amm-riep{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}
.amm-riep div{border-radius:16px;padding:10px 12px;color:#fff;font-weight:800}
.amm-riep small{display:block;font-weight:600;opacity:.92}
.amm-st{display:inline-block;border-radius:999px;padding:2px 10px;font-weight:800;font-size:.86rem;color:#fff}
.amm-barra{height:9px;border-radius:99px;background:rgba(0,0,0,.12);overflow:hidden;margin:6px 0}
.amm-barra span{display:block;height:100%;background:#2e7d32}
</style>"""


def _amm_stato_html(stato):
    ic, testo, col = AMM_STATI[stato]
    return f"<span class='amm-st' style='background:{col}'>{ic} {testo}</span>"


def _amm_oggi():
    return oggi() if "oggi" in globals() else date.today()


def _amm_lista(c, chiave):
    return [x for x in c.get(chiave, []) if isinstance(x, dict)]


def _amm_trova(c, chiave, i):
    return next((x for x in _amm_lista(c, chiave) if x.get("id") == i), None)


def _amm_salva(fn, messaggio):
    """Salva nel file personale (con l'etichetta della casa scelta, Cestino e storico come per il resto di Casa)."""
    _ca_salva(fn, messaggio)


def _amm_scadenze_vicine(c):
    oggi_ = _amm_oggi()
    spese = _amm_lista(c, "spese_amm")
    return sum(1 for s in spese for r in s.get("rate", []) if amm_stato_rata(r, oggi_) in ("scaduta", "in_scadenza") and amm_giorni_a(r.get("scadenza"), oggi_) is not None
               and amm_giorni_a(r.get("scadenza"), oggi_) <= 7)


def ca_amm_tab(c):
    """L'area Amministrazione di Casa (prima scheda): schermata dei badge e le schermate interne. `c` = i dati della casa scelta."""
    st.markdown(_AMM_CSS, unsafe_allow_html=True)
    vista = st.session_state.get("amm_vista")
    if vista:
        if st.button("← Torna ad Amministrazione", key="amm_indietro", width="stretch"):
            st.session_state["amm_vista"] = None
            st.rerun()
    if vista == "dati":
        return _amm_schermata_dati(c)
    if vista == "spese":
        return _amm_schermata_spese(c)
    if vista == "contatti" and "_amm_schermata_contatti" in globals():
        return _amm_schermata_contatti(c)
    if vista == "raccolta" and "_amm_schermata_raccolta" in globals():
        return _amm_schermata_raccolta(c)
    if vista == "ingombranti" and "_amm_schermata_ingombranti" in globals():
        return _amm_schermata_ingombranti(c)
    if vista:
        st.info("Questa schermata arriva nella prossima tappa dei lavori.")
        return
    st.subheader("🏢 Amministrazione della casa")
    st.caption("Spese condominiali e rate, dati dell'amministratore, professionisti da chiamare e raccolta differenziata: tutto in un posto, **separato per ogni casa**.")
    n = _amm_scadenze_vicine(c)
    with st.container(key="amm_hub"):
        for chiave, et in (("dati", "🏢 Dati amministrazione"), ("spese", "💶 Spese e scadenze" + (f" 🔔{n}" if n else "")), ("contatti", "🛠️ Contatti e interventi"),
                           ("raccolta", "♻️ Raccolta differenziata"), ("ingombranti", "🛋️ Ritiro ingombranti")):
            if st.button(et, key="amm_b_" + chiave, width="stretch"):
                st.session_state["amm_vista"] = chiave
                st.rerun()
    spese = _amm_lista(c, "spese_amm")
    if spese:
        r = amm_riepilogo(spese, _amm_oggi().year, _amm_oggi())
        st.markdown(f"**Quest'anno:** {amm_euro(r['totale'])} · pagato {amm_euro(r['pagato'])} · ancora da pagare **{amm_euro(r['da_pagare'])}**"
                    + (f" · 🔴 **{len(r['scadute'])} rate scadute**" if r["scadute"] else ""))


# ---------- 🏢 DATI AMMINISTRAZIONE ----------
_AMM_CAMPI_ADMIN = [("nome", "Nome"), ("cognome", "Cognome"), ("studio", "Nome dello studio di amministrazione"), ("indirizzo_studio", "Indirizzo dello studio"),
                    ("telefono", "Telefono fisso"), ("cellulare", "Cellulare"), ("email", "Email"), ("pec", "PEC"), ("cf_piva", "Codice fiscale o partita IVA"),
                    ("immobile", "Indirizzo dell'immobile amministrato"), ("condominio", "Nome del condominio"), ("banca", "Riferimenti bancari (banca, intestatario)"), ("iban", "IBAN")]


def _amm_dlg_admin(c, a=None):
    def _finestra():
        k = "amm_adm_" + (a["id"] if a else "nuovo")
        v = {}
        for chiave, et in _AMM_CAMPI_ADMIN:
            v[chiave] = st.text_input(et, value=(a or {}).get(chiave, ""), key=f"{k}_{chiave}")
        v["note"] = st.text_area("Note aggiuntive", value=(a or {}).get("note", ""), key=f"{k}_note", height=90)
        if v["iban"].strip() and not amm_iban_valido(v["iban"]):
            st.warning("L'IBAN non sembra giusto (il codice di controllo non torna): controlla di averlo scritto bene. Puoi salvare lo stesso.")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_salva", type="primary", width="stretch"):
            if not (v["nome"].strip() or v["cognome"].strip() or v["studio"].strip()):
                st.error("Scrivi almeno il nome dell'amministratore o dello studio.")
                return
            if a:
                def _fn(cc):
                    x = _amm_trova(cc, "amministratori", a["id"])
                    if x:
                        x.update({kk: vv.strip() for kk, vv in v.items()})
            else:
                def _fn(cc):
                    cc.setdefault("amministratori", []).append({"id": amm_id(), **{kk: vv.strip() for kk, vv in v.items()}})
            _amm_salva(_fn, "Amministrazione: dati dell'amministratore")
            st.rerun()
        if c2.button("Annulla", key=k + "_annulla", width="stretch"):
            st.rerun()
    st.dialog("🏢 Amministratore" if a else "➕ Nuovo amministratore")(_finestra)()


def _amm_dlg_elimina(c, chiave, i, nome, messaggio):
    def _finestra():
        st.warning(f"Eliminare **{_amm_h.escape(nome)}**? " + messaggio)
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=f"amm_el_si_{i}", type="primary", width="stretch"):
            def _fn(cc):
                cc[chiave] = [x for x in cc.get(chiave, []) if not (isinstance(x, dict) and x.get("id") == i)]
            _amm_salva(_fn, "Amministrazione: eliminato " + nome[:40])
            st.rerun()
        if s2.button("No, tienilo", key=f"amm_el_no_{i}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina")(_finestra)()


def _amm_schermata_dati(c):
    st.subheader("🏢 Dati dell'amministrazione")
    adm = _amm_lista(c, "amministratori")
    if not adm:
        st.info("Non hai ancora inserito l'amministratore. Tocca **➕ Aggiungi** per scrivere i suoi dati: poi potrai chiamarlo o scrivergli con un tocco.")
    for a in adm:
        nome = " ".join(x for x in (a.get("nome"), a.get("cognome")) if x) or a.get("studio") or "Amministratore"
        righe = [("🏢", a.get("studio")), ("📍", a.get("indirizzo_studio")), ("📞", a.get("telefono")), ("📱", a.get("cellulare")), ("✉️", a.get("email")), ("📨 PEC", a.get("pec")),
                 ("🆔", a.get("cf_piva")), ("🏘️ Condominio", a.get("condominio")), ("📌 Immobile", a.get("immobile")), ("🏦", a.get("banca"))]
        corpo = "<br>".join(f"{ic} {_amm_h.escape(v)}" for ic, v in righe if v)
        st.markdown(f"<div class='amm-card'><b style='font-size:1.1rem'>👤 {_amm_h.escape(nome)}</b><div style='margin-top:6px'>{corpo}</div>"
                    + (f"<div style='margin-top:6px'><i>{_amm_h.escape(a['note'])}</i></div>" if a.get("note") else "") + "</div>", unsafe_allow_html=True)
        if a.get("iban"):
            st.caption("IBAN (tocca l'icona a destra per copiarlo):")
            st.code(a["iban"], language=None)
            if not amm_iban_valido(a["iban"]):
                st.caption("⚠️ Il codice di controllo dell'IBAN non torna: verifica che sia scritto bene.")
        pulsanti = []
        tel = a.get("cellulare") or a.get("telefono")
        if tel:
            pulsanti.append(("📞 Chiama", "tel:" + (_lv_tel(tel) if "_lv_tel" in globals() else "".join(ch for ch in tel if ch.isdigit() or ch == "+"))))
        if a.get("email"):
            pulsanti.append(("✉️ Scrivi", "mailto:" + a["email"]))
        if a.get("pec"):
            pulsanti.append(("📨 Scrivi alla PEC", "mailto:" + a["pec"]))
        for i in range(0, len(pulsanti), 3):
            for col, (et, url) in zip(st.columns(len(pulsanti[i:i + 3]), gap="small"), pulsanti[i:i + 3]):
                col.link_button(et, url, width="stretch")
        d1, d2, d3 = st.columns(3, gap="small")
        if d1.button("✏️ Modifica", key=f"amm_adm_mod_{a['id']}", width="stretch"):
            _amm_dlg_admin(c, a)
        if d2.button("🗑️ Elimina", key=f"amm_adm_el_{a['id']}", width="stretch"):
            _amm_dlg_elimina(c, "amministratori", a["id"], nome, "Le spese collegate restano, senza il suo nome.")
        with d3:
            if "_fa_inv_voce" in globals():
                _fa_inv_voce(f"amm_adm_inv_{a['id']}", "📤 Invia", "Amministratore: " + nome,
                             [(et, a.get(k)) for k, et in _AMM_CAMPI_ADMIN if a.get(k)] + ([("Note", a.get("note"))] if a.get("note") else []), [])
    if st.button("➕ Aggiungi un amministratore", key="amm_adm_nuovo", width="stretch", type="primary" if not adm else "secondary"):
        _amm_dlg_admin(c, None)


# ---------- 💶 SPESE E SCADENZE ----------
def _amm_nome_admin(c, i):
    a = _amm_trova(c, "amministratori", i) if i else None
    return (" ".join(x for x in (a.get("nome"), a.get("cognome")) if x) or a.get("studio")) if a else ""


def _amm_dlg_spesa(c, s=None):
    def _finestra():
        k = "amm_sp_" + (s["id"] if s else "nuova")
        adm = _amm_lista(c, "amministratori")
        descr = st.text_input("Descrizione della spesa *", value=(s or {}).get("descrizione", ""), key=k + "_d", placeholder="es. Rate condominio 2026, Lavori facciata")
        cat = st.selectbox("Categoria", AMM_CATEGORIE, index=AMM_CATEGORIE.index((s or {}).get("categoria")) if (s or {}).get("categoria") in AMM_CATEGORIE else 0, key=k + "_c")
        if not s:
            tot = st.text_input("Importo totale (€) *", key=k + "_t", placeholder="es. 1.200,00")
            n = st.number_input("Numero di rate", min_value=1, max_value=60, value=1, step=1, key=k + "_n")
            prima = st.date_input("Scadenza della prima rata *", value=_amm_oggi() + timedelta(days=30), key=k + "_p", format="DD/MM/YYYY")
            per = st.selectbox("Ogni quanto scadono le rate", list(AMM_PERIODI), index=3, key=k + "_per")
            mesi = AMM_PERIODI[per]
            if mesi is None:
                mesi = int(st.number_input("Ogni quanti mesi", min_value=1, max_value=60, value=1, step=1, key=k + "_mesi"))
            rinnovo = st.checkbox("🔁 La spesa si ripete sempre (aggiungi da solo le scadenze future)", key=k + "_rin", help="Per spese fisse come l'assicurazione o le quote annuali.") if mesi else False
            imp_tot = amm_importo(tot)
            if imp_tot and n:
                anteprima = amm_ripartisci(imp_tot, int(n))
                date_r = amm_genera_scadenze(prima, int(n), mesi)
                st.caption(f"Si creano **{int(n)} rate**: " + ", ".join(f"{amm_euro(x)} il {d.strftime('%d/%m/%Y')}" for x, d in list(zip(anteprima, date_r))[:6]) + (" …" if int(n) > 6 else "")
                           + ". Potrai poi cambiare data e importo di ogni rata.")
        giorni = st.multiselect("Avvisami quanti giorni prima della scadenza", AMM_GIORNI_AVVISO, default=(s or {}).get("avvisi_giorni", st.session_state.get("amm_giorni_default", AMM_GIORNI_DEFAULT)),
                                key=k + "_g", format_func=lambda g: "il giorno stesso" if g == 0 else f"{g} giorno" if g == 1 else f"{g} giorni")
        att = st.checkbox("🔔 Avvisami per questa spesa", value=bool((s or {}).get("avvisi_attivi", True)), key=k + "_att")
        opz = [""] + [x["id"] for x in adm]
        adm_sel = st.selectbox("Amministratore", opz, index=opz.index((s or {}).get("amministratore_id", "")) if (s or {}).get("amministratore_id", "") in opz else 0,
                               key=k + "_a", format_func=lambda i: "— nessuno —" if not i else _amm_nome_admin(c, i))
        note = st.text_area("Note", value=(s or {}).get("note", ""), key=k + "_note", height=80)
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva la spesa", key=k + "_salva", type="primary", width="stretch"):
            if not descr.strip():
                st.error("Scrivi una descrizione.")
                return
            if s:
                def _fn(cc):
                    x = _amm_trova(cc, "spese_amm", s["id"])
                    if x:
                        x.update({"descrizione": descr.strip(), "categoria": cat, "avvisi_giorni": sorted(set(giorni), reverse=True), "amministratore_id": adm_sel, "note": note.strip(), "avvisi_attivi": bool(att)})
                        _amm_log(x, "Dati della spesa modificati")
                _amm_salva(_fn, "Amministrazione: spesa modificata")
            else:
                if not imp_tot or imp_tot <= 0:
                    st.error("Scrivi l'importo totale (per esempio 1.200,00).")
                    return
                nuova = amm_crea_spesa(descr, cat, imp_tot, int(n), prima, mesi, adm_sel, note, giorni, rinnovo)
                nuova["avvisi_attivi"] = bool(att)
                _amm_salva(lambda cc: cc.setdefault("spese_amm", []).append(nuova), "Amministrazione: nuova spesa " + descr.strip()[:40])
            st.rerun()
        if c2.button("Annulla", key=k + "_annulla", width="stretch"):
            st.rerun()
    st.dialog("✏️ Modifica la spesa" if s else "➕ Nuova spesa")(_finestra)()


def _amm_dlg_paga(c, s, r):
    def _finestra():
        k = f"amm_pg_{r['id']}"
        st.markdown(f"**{_amm_h.escape(s['descrizione'])}** — rata {r.get('n')} del {data_it(r['scadenza'])}")
        st.caption(f"Importo della rata {amm_euro(r['importo'])} · già pagato {amm_euro(amm_pagato(r))} · **resta da pagare {amm_euro(amm_residuo(r))}**")
        imp = st.text_input("Quanto hai pagato (€)", value=f"{amm_residuo(r):.2f}".replace(".", ","), key=k + "_i", help="Puoi scrivere anche una cifra più bassa: è un pagamento parziale.")
        dt = st.date_input("Data del pagamento", value=_amm_oggi(), key=k + "_d", format="DD/MM/YYYY")
        modo = st.selectbox("Come hai pagato", _CA_MODI_PAGAMENTO if "_CA_MODI_PAGAMENTO" in globals() else ["Bonifico", "Contanti", "Altro"], key=k + "_m")
        docs = [d for d in _amm_lista(c, "documenti") if d.get("file") or d.get("files")]
        opz = [""] + [d["id"] for d in docs]
        ric = st.selectbox("Ricevuta (facoltativa, tra i documenti archiviati)", opz, key=k + "_r", format_func=lambda i: "— nessuna —" if not i else next((d.get("titolo") or d.get("tipo") or i for d in docs if d["id"] == i), i))
        nota = st.text_input("Nota", key=k + "_n")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("✅ Registra il pagamento", key=k + "_ok", type="primary", width="stretch"):
            esito = {}

            def _fn(cc):
                x = _amm_trova(cc, "spese_amm", s["id"])
                esito["r"] = amm_registra_pagamento(x, r["id"], imp, dt.isoformat(), modo, nota, ric) if x else (False, "Spesa non trovata.")
            _amm_salva(_fn, "Amministrazione: pagamento registrato")
            if not esito.get("r", (False,))[0]:
                st.error(esito["r"][1])
                return
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("💶 Registra un pagamento")(_finestra)()


def _amm_dlg_rata(c, s, r):
    def _finestra():
        k = f"amm_rt_{r['id']}"
        st.markdown(f"**{_amm_h.escape(s['descrizione'])}** — rata {r.get('n')}")
        if r.get("pagamenti"):
            st.caption(f"Hai già pagato {amm_euro(amm_pagato(r))}: i pagamenti restano nello storico anche se cambi data o importo.")
        imp = st.text_input("Importo della rata (€)", value=f"{float(r['importo']):.2f}".replace(".", ","), key=k + "_i")
        dt = st.date_input("Scadenza", value=date.fromisoformat(r["scadenza"]), key=k + "_d", format="DD/MM/YYYY")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_ok", type="primary", width="stretch"):
            esito = {}

            def _fn(cc):
                x = _amm_trova(cc, "spese_amm", s["id"])
                esito["r"] = amm_modifica_rata(x, r["id"], dt.isoformat(), imp) if x else (False, "Spesa non trovata.")
            _amm_salva(_fn, "Amministrazione: rata modificata")
            if not esito.get("r", (False,))[0]:
                st.error(esito["r"][1])
                return
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("✏️ Modifica la rata")(_finestra)()


def _amm_dlg_allega(c, s):
    def _finestra():
        k = f"amm_al_{s['id']}"
        st.caption("Scegli tra i documenti **già archiviati** in Casa (avvisi di pagamento, bollettini, ricevute…). Per aggiungerne uno nuovo caricalo prima in **📚 Documenti**: si legge e si classifica da solo.")
        q = st.text_input("Cerca (titolo, tipo, ente, data…)", key=k + "_q")
        lavoro = globals().get("_CA_TIPI_LAVORO", ())
        docs = [d for d in _amm_lista(c, "documenti") if d.get("tipo") not in lavoro and (d.get("file") or d.get("files"))]
        qn = (_ca_norm(q) if q.strip() else "")
        vis = [d for d in docs if not qn or qn in _ca_norm(" ".join(str(d.get(x) or "") for x in ("titolo", "tipo", "ente", "data", "numero", "argomento")))][:40]
        scelti = st.multiselect("Documenti da allegare", [d["id"] for d in vis], default=[i for i in s.get("allegati", []) if i in [d["id"] for d in vis]], key=k + "_m",
                                format_func=lambda i: next(((d.get("titolo") or d.get("tipo") or i) + (f" · {data_it(d['data'])}" if d.get("data") else "") for d in docs if d["id"] == i), i))
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva gli allegati", key=k + "_ok", type="primary", width="stretch"):
            def _fn(cc):
                x = _amm_trova(cc, "spese_amm", s["id"])
                if x:
                    visibili = {d["id"] for d in vis}
                    x["allegati"] = [i for i in x.get("allegati", []) if i not in visibili] + scelti
                    _amm_log(x, f"Allegati aggiornati ({len(x['allegati'])})")
            _amm_salva(_fn, "Amministrazione: allegati della spesa")
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("📎 Allega documenti")(_finestra)()


def _amm_scheda_spesa(c, s, nomi_docs):
    oggi_ = _amm_oggi()
    stato = amm_stato_spesa(s, oggi_)
    rate = amm_rate_ordinate(s)
    pagate = sum(1 for r in rate if amm_stato_rata(r, oggi_) == "pagata")
    tot_pag = sum(amm_pagato(r) for r in rate)
    perc = int(100 * tot_pag / s["importo_totale"]) if s.get("importo_totale") else 0
    prossima = next((r for r in rate if amm_residuo(r) > 0.004), None)
    sottotit = f"{pagate}/{len(rate)} rate pagate"
    if prossima:
        g = amm_giorni_a(prossima["scadenza"], oggi_)
        sottotit += f" · prossima {data_it(prossima['scadenza'])} ({'scaduta da ' + str(-g) + ' giorni' if g is not None and g < 0 else 'oggi' if g == 0 else 'tra ' + str(g) + ' giorni'})"
    st.markdown(f"<div class='amm-card'><div style='display:flex;justify-content:space-between;gap:8px;align-items:center'><b>{_amm_h.escape(s['descrizione'])}</b>{_amm_stato_html(stato)}</div>"
                f"<div style='opacity:.8'>{_amm_h.escape(s.get('categoria', ''))} · totale <b>{amm_euro(s['importo_totale'])}</b> · pagato {amm_euro(tot_pag)}</div>"
                f"<div class='amm-barra'><span style='width:{perc}%'></span></div><div style='font-size:.92rem'>{sottotit}</div></div>", unsafe_allow_html=True)
    with st.expander(f"🔽 Rate, pagamenti e documenti di «{s['descrizione'][:28]}»"):
        if s.get("amministratore_id") and _amm_nome_admin(c, s["amministratore_id"]):
            st.caption("👤 Amministratore: " + _amm_nome_admin(c, s["amministratore_id"]))
        if s.get("note"):
            st.caption("📝 " + s["note"])
        for r in rate:
            st_r = amm_stato_rata(r, oggi_)
            parz = amm_pagato(r) > 0.004 and st_r != "pagata"
            st.markdown(f"<div class='amm-card' style='padding:8px 12px'><b>Rata {r.get('n')}</b> · {data_it(r['scadenza'])} · <b>{amm_euro(r['importo'])}</b> {_amm_stato_html(st_r)}"
                        + (f"<div>⏳ Pagato in parte: {amm_euro(amm_pagato(r))} · resta <b>{amm_euro(amm_residuo(r))}</b></div>" if parz else "")
                        + "".join(f"<div style='font-size:.88rem'>✔ {data_it(p.get('data'))} · {amm_euro(p.get('importo'))}" + (f" · {_amm_h.escape(p['modo'])}" if p.get("modo") else "")
                                  + (f" · {_amm_h.escape(p['nota'])}" if p.get("nota") else "") + "</div>" for p in r.get("pagamenti", [])) + "</div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3, gap="small")
            if st_r != "pagata" and b1.button("💶 Pagata", key=f"amm_pg_b_{r['id']}", width="stretch"):
                _amm_dlg_paga(c, s, r)
            if b2.button("✏️ Modifica", key=f"amm_rt_b_{r['id']}", width="stretch"):
                _amm_dlg_rata(c, s, r)
            if r.get("pagamenti") and b3.button("↩️ Annulla pagamento", key=f"amm_ann_b_{r['id']}", width="stretch"):
                ultimo = r["pagamenti"][-1]

                def _fn(cc, rid=r["id"], pid=ultimo["id"]):
                    x = _amm_trova(cc, "spese_amm", s["id"])
                    if x:
                        amm_annulla_pagamento(x, rid, pid)
                _amm_salva(_fn, "Amministrazione: pagamento annullato")
                st.rerun()
        if s.get("rinnovo_auto") and st.button("➕ Aggiungi le prossime scadenze", key=f"amm_ric_{s['id']}", width="stretch"):
            def _fn(cc):
                x = _amm_trova(cc, "spese_amm", s["id"])
                if x:
                    amm_aggiungi_rate_ricorrenti(x, _amm_oggi(), minimo=4)
            _amm_salva(_fn, "Amministrazione: scadenze future")
            st.rerun()
        alleg = [d for d in _amm_lista(c, "documenti") if d.get("id") in s.get("allegati", [])]
        if alleg:
            st.markdown("**📎 Documenti allegati**")
            for d in alleg:
                if "_ca_riga_documento" in globals():
                    _ca_riga_documento(d, nomi_docs, "amm" + s["id"] + "_", _amm_lista(c, "documenti"))
                    if "_ca_correzione_qui" in globals():
                        _ca_correzione_qui(c, d)
        if s.get("storico"):
            with st.expander("📜 Storico di questa spesa"):
                for e in reversed(s["storico"][-30:]):
                    st.caption(f"{e.get('quando', '')} — {e.get('testo', '')}")
    ev_s = amm_eventi_rate([s], oggi_, st.session_state.get("amm_giorni_default"))
    if ev_s:
        st.download_button("📅 Metti queste scadenze nel calendario del telefono (con allarme)", amm_ics(ev_s, s.get("descrizione", "Spesa")), file_name="scadenze_" + "".join(ch for ch in s.get("descrizione", "spesa") if ch.isalnum())[:30] + ".ics",
                           mime="text/calendar", key=f"amm_ics_{s['id']}", width="stretch")
    a1, a2, a3 = st.columns(3, gap="small")
    if a1.button("✏️ Modifica", key=f"amm_sp_mod_{s['id']}", width="stretch"):
        _amm_dlg_spesa(c, s)
    if a2.button("📎 Allega", key=f"amm_sp_al_{s['id']}", width="stretch"):
        _amm_dlg_allega(c, s)
    if a3.button("🗑️ Elimina", key=f"amm_sp_el_{s['id']}", width="stretch"):
        _amm_dlg_elimina(c, "spese_amm", s["id"], s["descrizione"], "Si perdono anche le sue rate e i pagamenti registrati (resta nel Cestino per qualche giorno).")


def _amm_schermata_spese(c):
    oggi_ = _amm_oggi()
    st.subheader("💶 Spese e scadenze")
    spese = _amm_lista(c, "spese_amm")
    anni = sorted({int(r["scadenza"][:4]) for s in spese for r in s.get("rate", []) if r.get("scadenza")} | {oggi_.year})
    anno = st.selectbox("Anno del riepilogo", anni, index=anni.index(oggi_.year), key="amm_anno")
    rp = amm_riepilogo(spese, anno, oggi_)
    st.markdown(f"<div class='amm-riep'><div style='background:#37474f'><small>Totale {anno}</small>{amm_euro(rp['totale'])}</div><div style='background:#2e7d32'><small>Già pagato</small>{amm_euro(rp['pagato'])}</div>"
                f"<div style='background:#0d47a1'><small>Ancora da pagare</small>{amm_euro(rp['da_pagare'])}</div><div style='background:#b71c1c'><small>Rate scadute</small>{len(rp['scadute'])}</div></div>",
                unsafe_allow_html=True)
    if st.button("➕ Nuova spesa", key="amm_sp_nuova", width="stretch", type="primary"):
        _amm_dlg_spesa(c, None)
    _amm_import_pannello(c)
    if not spese:
        st.info("Non hai ancora registrato spese. Tocca **➕ Nuova spesa**: scrivi l'importo e il numero di rate, e le scadenze si creano da sole.")
        return
    prossime = amm_prossime(spese, oggi_, 5)
    if rp["scadute"] or prossime:
        with st.expander(f"⏰ Prossime scadenze ({len(prossime)}) e rate scadute ({len(rp['scadute'])})"):
            for s, r in rp["scadute"]:
                st.markdown(f"🔴 **{_amm_h.escape(s['descrizione'])}** · rata {r['n']} · {data_it(r['scadenza'])} · da pagare {amm_euro(amm_residuo(r))}")
            for s, r in prossime:
                g = amm_giorni_a(r["scadenza"], oggi_)
                st.markdown(f"{AMM_STATI[amm_stato_rata(r, oggi_)][0]} **{_amm_h.escape(s['descrizione'])}** · rata {r['n']} · {data_it(r['scadenza'])} (tra {g} giorni) · {amm_euro(amm_residuo(r))}")
    f1, f2 = st.columns(2, gap="small")
    filtro = f1.selectbox("Mostra", ["Tutte", "Da pagare", "In scadenza", "Scadute", "Pagate"], key="amm_filtro")
    cerca = f2.text_input("Cerca", key="amm_cerca", placeholder="descrizione, categoria…")
    mappa = {"Da pagare": "da_pagare", "In scadenza": "in_scadenza", "Scadute": "scaduta", "Pagate": "pagata"}
    visibili = [s for s in spese if (filtro == "Tutte" or amm_stato_spesa(s, oggi_) == mappa[filtro])
                and (not cerca.strip() or cerca.strip().lower() in (s.get("descrizione", "") + " " + s.get("categoria", "")).lower())]
    ordine = {"scaduta": 0, "in_scadenza": 1, "da_pagare": 2, "pagata": 3}
    nomi = {b.get("id"): b.get("nome", "") for b in _amm_lista(c, "beni")}
    for s in sorted(visibili, key=lambda x: (ordine[amm_stato_spesa(x, oggi_)], (amm_rate_ordinate(x)[0]["scadenza"] if x.get("rate") else ""))):
        _amm_scheda_spesa(c, s, nomi)
    if spese and not visibili:
        st.info("Nessuna spesa con questi filtri.")
    storico = amm_storico_pagamenti(spese)
    if storico:
        with st.expander(f"📜 Storico dei pagamenti ({len(storico)})"):
            for d_, s, r, p in storico[:60]:
                st.markdown(f"✔ **{data_it(p.get('data'))}** · {amm_euro(p.get('importo'))} · {_amm_h.escape(s['descrizione'])} (rata {r['n']})" + (f" · {_amm_h.escape(p['modo'])}" if p.get("modo") else ""))
    with st.expander("⚙️ Avvisi: quando ricordarmi le scadenze"):
        att = st.session_state.get("amm_giorni_default", AMM_GIORNI_DEFAULT)
        nuovi = st.multiselect("Giorni prima della scadenza (valgono per le nuove spese)", AMM_GIORNI_AVVISO, default=att, key="amm_giorni_ms",
                               format_func=lambda g: "il giorno stesso" if g == 0 else f"{g} giorno" if g == 1 else f"{g} giorni")
        st.session_state["amm_giorni_default"] = nuovi or AMM_GIORNI_DEFAULT
        st.caption("Gli avvisi arrivano sui canali che hai scelto in **Salute → 🔔 Scegli come ricevere gli avvisi** (Telegram, email, WhatsApp, SMS), con la casella **«🏡 Avvisami anche di Casa»** accesa. "
                   "Ogni spesa può avere i suoi giorni e può essere spenta: si cambiano da **✏️ Modifica**. Dentro l'app le rate in scadenza o scadute compaiono in cima a Casa e fanno lampeggiare il pulsante nella Home.")
        ev = amm_eventi_rate(spese, oggi_, st.session_state.get("amm_giorni_default"))
        st.markdown("**🔔 Suono sul telefono anche con l'app chiusa**")
        st.caption("L'app da sola non può suonare: il suono è quello di Telegram, WhatsApp o dell'email. Per avere **anche un allarme del telefono**, scarica il file calendario: aprendolo, il telefono "
                   "aggiunge le scadenze al **Calendario** con gli allarmi ai giorni scelti. Se lo riscarichi dopo aver cambiato qualcosa, le scadenze si **aggiornano**, non si duplicano.")
        if ev:
            st.download_button(f"📅 Scarica il calendario delle {len(ev)} rate da pagare (.ics)", amm_ics(ev), file_name="scadenze_amministrazione.ics", mime="text/calendar", key="amm_ics_tutte", width="stretch")
        else:
            st.caption("Non ci sono rate future da mettere nel calendario.")


# ---------------------------------------------------------------------------------------------------------------------
# aggancio a Casa: la scheda «Amministrazione» (si fa in casa.py con una riga, qui non si tocca nient'altro)
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# 🛠️ CONTATTI E INTERVENTI
# Una rubrica SOLA: i professionisti sono i contatti di «📇 Riferimenti» (lista `contatti_casa`, stessi campi e stessi pulsanti). I campi in più (specializzazione, costo, preferito,
# preventivi) stanno in una lista di appoggio `contatti_extra` collegata al contatto: se un contatto si modifica da «Riferimenti» (che riscrive il contatto), i campi in più NON si perdono.
# ---------------------------------------------------------------------------------------------------------------------
AMM_CATEGORIE_PROF = ["Elettricista", "Idraulico", "Muratore", "Fabbro", "Tecnico caldaia", "Tecnico climatizzazione", "Tecnico elettrodomestici", "Antennista", "Serramentista",
                      "Imbianchino", "Impresa di pulizie", "Giardiniere", "Manutentore generico", "Altri professionisti"]
_AMM_SINONIMI = {"Tecnico caldaia": "Caldaista", "Impresa di pulizie": "Pulizie"}           # categorie della rubrica già esistenti (badge di Riferimenti)


def amm_tipo_base(categoria, tipi_esistenti):
    """(tipo, altro) da scrivere nel contatto della rubrica: se la categoria è già un badge di Riferimenti si usa quello, altrimenti «Altro» + il nome della categoria."""
    cat = (categoria or "").strip()
    if cat in tipi_esistenti:
        return cat, ""
    if _AMM_SINONIMI.get(cat) in tipi_esistenti:
        return _AMM_SINONIMI[cat], ""
    return ("Altro" if "Altro" in tipi_esistenti else (list(tipi_esistenti)[-1] if tipi_esistenti else "Altro")), cat


def amm_categoria_di(m):
    """Il nome della categoria di un contatto, come lo vede chi guarda."""
    if m.get("tipo") == "Altro" and m.get("altro"):
        return m["altro"]
    inv = {v: k for k, v in _AMM_SINONIMI.items()}
    return inv.get(m.get("tipo"), m.get("tipo") or "Altro")


def amm_extra_di(c, cid):
    return next((x for x in _amm_lista(c, "contatti_extra") if x.get("contatto_id") == cid), {})


def amm_totale_interventi(interventi, cid=None, anno=None):
    tot = 0.0
    for i in interventi:
        if cid and i.get("contatto_id") != cid:
            continue
        if anno and not str(i.get("data") or "").startswith(str(anno)):
            continue
        tot += float(i.get("costo") or 0)
    return round(tot, 2)


def _amm_tipi_rubrica():
    try:
        return _rub_tipi("casa")
    except Exception:
        return {}


def _amm_categorie(c):
    tipi = _amm_tipi_rubrica()
    visti = list(AMM_CATEGORIE_PROF)
    for t in tipi:
        if t in ("Amministratore",):
            continue
        nome = {v: k for k, v in _AMM_SINONIMI.items()}.get(t, t)
        if nome not in visti and t != "Altro":
            visti.append(nome)
    for x in (c.get("categorie_prof") or []):
        if x not in visti:
            visti.append(x)
    for m in _amm_lista(c, "contatti_casa"):
        cat = amm_categoria_di(m)
        if cat and cat not in visti and cat != "Altro":
            visti.append(cat)
    return visti


def _amm_dlg_contatto(c, m=None):
    def _finestra():
        k = "amm_ct_" + (m["id"] if m else "nuovo")
        ex = amm_extra_di(c, m["id"]) if m else {}
        cats = _amm_categorie(c)
        cat_att = amm_categoria_di(m) if m else cats[0]
        cat = st.selectbox("Categoria", cats + ["➕ Altra categoria (nuova)…"], index=cats.index(cat_att) if cat_att in cats else 0, key=k + "_cat")
        nuova_cat = st.text_input("Nome della nuova categoria", key=k + "_ncat", placeholder="es. Tecnico antifurto") if cat.startswith("➕") else ""
        ref = st.text_input("Nome e cognome", value=(m or {}).get("referente", ""), key=k + "_ref")
        nome = st.text_input("Nome dell'attività", value=(m or {}).get("nome", ""), key=k + "_nome", placeholder="es. Idraulica Bianchi snc")
        spec = st.text_input("Specializzazione", value=ex.get("specializzazione", ""), key=k + "_spec", placeholder="es. caldaie a condensazione, perdite")
        c1, c2 = st.columns(2)
        tel = c1.text_input("Telefono", value=(m or {}).get("telefono", ""), key=k + "_tel")
        cell = c2.text_input("Cellulare / WhatsApp", value=(m or {}).get("cellulare", ""), key=k + "_cell")
        email = st.text_input("Email", value=(m or {}).get("email", ""), key=k + "_email")
        ind = st.text_input("Indirizzo", value=(m or {}).get("indirizzo", ""), key=k + "_ind")
        sito = st.text_input("Sito internet", value=(m or {}).get("sito", ""), key=k + "_sito", placeholder="https://…")
        orari = st.text_area("Orari di disponibilità", value=(m or {}).get("orari", ""), key=k + "_orari", height=70, placeholder="es. lun-ven 8-18; urgenze anche di sera")
        costo = st.text_area("Costo indicativo o tariffario", value=ex.get("costo", ""), key=k + "_costo", height=70, placeholder="es. uscita € 40, € 35/ora")
        note = st.text_area("Note", value=(m or {}).get("note", ""), key=k + "_note", height=70)
        pref = st.checkbox("⭐ Preferito", value=bool(ex.get("preferito")), key=k + "_pref")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_salva", type="primary", width="stretch"):
            categoria = (nuova_cat.strip() if cat.startswith("➕") else cat)
            if not (ref.strip() or nome.strip()):
                st.error("Scrivi almeno il nome della persona o dell'attività.")
                return
            if cat.startswith("➕") and not categoria:
                st.error("Scrivi il nome della nuova categoria.")
                return
            if email.strip() and ("@" not in email or "." not in email.split("@")[-1]):
                st.error("L'email non sembra giusta (deve essere tipo nome@esempio.it).")
                return
            tipo, altro = amm_tipo_base(categoria, _amm_tipi_rubrica())
            cid = m["id"] if m else amm_id()
            base = {"tipo": tipo, "altro": altro, "nome": nome.strip(), "referente": ref.strip(), "telefono": tel.strip(), "cellulare": cell.strip(), "email": email.strip(),
                    "indirizzo": ind.strip(), "sito": sito.strip(), "orari": orari.strip(), "note": note.strip()}
            extra = {"specializzazione": spec.strip(), "costo": costo.strip(), "preferito": bool(pref)}

            def _fn(cc):
                lista = cc.setdefault("contatti_casa", [])
                x = next((y for y in lista if isinstance(y, dict) and y.get("id") == cid), None)
                if x:
                    x.update(base)                                                    # si aggiorna il contatto SENZA buttare i campi che non conosciamo
                else:
                    lista.append({"id": cid, **base})
                if categoria and categoria not in AMM_CATEGORIE_PROF and categoria not in (cc.get("categorie_prof") or []) and categoria not in _amm_tipi_rubrica():
                    cc.setdefault("categorie_prof", []).append(categoria)
                e = next((y for y in cc.setdefault("contatti_extra", []) if isinstance(y, dict) and y.get("contatto_id") == cid), None)
                if e:
                    e.update(extra)
                else:
                    cc["contatti_extra"].append({"id": amm_id(), "contatto_id": cid, "preventivi": [], **extra})
            _amm_salva(_fn, "Amministrazione: professionista " + (ref.strip() or nome.strip())[:40])
            st.rerun()
        if c2.button("Annulla", key=k + "_annulla", width="stretch"):
            st.rerun()
    st.dialog("✏️ Professionista" if m else "➕ Nuovo professionista")(_finestra)()


def _amm_dlg_intervento(c, i=None, contatto_id=""):
    def _finestra():
        k = "amm_in_" + (i["id"] if i else "nuovo")
        contatti = [m for m in _amm_lista(c, "contatti_casa")]
        opz = [m["id"] for m in contatti]
        pre = (i or {}).get("contatto_id") or contatto_id
        if not opz:
            st.info("Prima aggiungi un professionista (➕ Nuovo professionista).")
            return
        sel = st.selectbox("Chi è intervenuto", opz, index=opz.index(pre) if pre in opz else 0, key=k + "_c",
                           format_func=lambda x: next(((m.get("referente") or m.get("nome") or x) + " · " + amm_categoria_di(m) for m in contatti if m["id"] == x), x))
        dt = st.date_input("Data dell'intervento", value=date.fromisoformat((i or {}).get("data")) if (i or {}).get("data") else _amm_oggi(), key=k + "_d", format="DD/MM/YYYY")
        problema = st.text_area("Problema e lavoro eseguito", value=(i or {}).get("problema", ""), key=k + "_p", height=90, placeholder="es. perdita sotto il lavandino, sostituito il sifone")
        costo = st.text_input("Costo (€)", value=(f"{float(i['costo']):.2f}".replace(".", ",") if (i or {}).get("costo") is not None else ""), key=k + "_costo")
        beni = _amm_lista(c, "beni")
        bopz = [""] + [b["id"] for b in beni]
        bene = st.selectbox("Bene interessato (facoltativo)", bopz, index=bopz.index((i or {}).get("bene_id", "")) if (i or {}).get("bene_id", "") in bopz else 0, key=k + "_b",
                            format_func=lambda x: "— nessuno —" if not x else next((b.get("nome", x) for b in beni if b["id"] == x), x))
        docs = [d for d in _amm_lista(c, "documenti") if d.get("file") or d.get("files")]
        allegati = st.multiselect("Documenti allegati (già archiviati in Documenti)", [d["id"] for d in docs], default=[x for x in (i or {}).get("allegati", []) if x in [d["id"] for d in docs]], key=k + "_a",
                                  format_func=lambda x: next(((d.get("titolo") or d.get("tipo") or x) for d in docs if d["id"] == x), x))
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva l'intervento", key=k + "_ok", type="primary", width="stretch"):
            imp = amm_importo(costo) if costo.strip() else 0.0
            if imp is None or imp < 0:
                st.error("Il costo non è un numero valido.")
                return
            rec = {"contatto_id": sel, "data": dt.isoformat(), "problema": problema.strip(), "costo": imp, "bene_id": bene, "allegati": allegati}

            def _fn(cc):
                lista = cc.setdefault("interventi_prof", [])
                x = next((y for y in lista if isinstance(y, dict) and y.get("id") == (i or {}).get("id")), None) if i else None
                if x:
                    x.update(rec)
                else:
                    lista.append({"id": amm_id(), **rec})
            _amm_salva(_fn, "Amministrazione: intervento registrato")
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("✏️ Intervento" if i else "🔧 Registra un intervento")(_finestra)()


def _amm_dlg_preventivi(c, m):
    def _finestra():
        k = "amm_pv_" + m["id"]
        ex = amm_extra_di(c, m["id"])
        st.caption("Scegli tra i documenti **già archiviati** in Casa (preventivi, fatture, garanzie…). Per aggiungerne uno nuovo caricalo prima in **📚 Documenti**.")
        lavoro = globals().get("_CA_TIPI_LAVORO", ())
        docs = [d for d in _amm_lista(c, "documenti") if d.get("tipo") not in lavoro and (d.get("file") or d.get("files"))]
        scelti = st.multiselect("Preventivi e documenti", [d["id"] for d in docs], default=[x for x in ex.get("preventivi", []) if x in [d["id"] for d in docs]], key=k + "_m",
                                format_func=lambda x: next((((d.get("titolo") or d.get("tipo") or x) + (f" · {data_it(d['data'])}" if d.get("data") else "")) for d in docs if d["id"] == x), x))
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_ok", type="primary", width="stretch"):
            def _fn(cc):
                e = next((y for y in cc.setdefault("contatti_extra", []) if isinstance(y, dict) and y.get("contatto_id") == m["id"]), None)
                if e:
                    e["preventivi"] = scelti
                else:
                    cc["contatti_extra"].append({"id": amm_id(), "contatto_id": m["id"], "preventivi": scelti})
            _amm_salva(_fn, "Amministrazione: preventivi allegati")
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("📎 Preventivi e documenti")(_finestra)()


def _amm_dlg_togli_contatto(c, m):
    def _finestra():
        nome = m.get("referente") or m.get("nome") or "questo contatto"
        st.warning(f"Eliminare **{_amm_h.escape(nome)}** dalla rubrica? Sparisce anche da **📇 Riferimenti** (è la stessa rubrica). Gli interventi registrati restano nello storico.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=f"amm_ct_si_{m['id']}", type="primary", width="stretch"):
            def _fn(cc):
                cc["contatti_casa"] = [x for x in cc.get("contatti_casa", []) if not (isinstance(x, dict) and x.get("id") == m["id"])]
                cc["contatti_extra"] = [x for x in cc.get("contatti_extra", []) if not (isinstance(x, dict) and x.get("contatto_id") == m["id"])]
            _amm_salva(_fn, "Amministrazione: eliminato " + nome[:40])
            st.rerun()
        if s2.button("No, tienilo", key=f"amm_ct_no_{m['id']}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina il contatto")(_finestra)()


def _amm_preferito(c, m, valore):
    def _fn(cc):
        e = next((y for y in cc.setdefault("contatti_extra", []) if isinstance(y, dict) and y.get("contatto_id") == m["id"]), None)
        if e:
            e["preferito"] = valore
        else:
            cc["contatti_extra"].append({"id": amm_id(), "contatto_id": m["id"], "preferito": valore, "preventivi": []})
    _amm_salva(_fn, "Amministrazione: preferito")
    st.rerun()


def _amm_schermata_contatti(c):
    st.subheader("🛠️ Contatti e interventi")
    st.caption("I professionisti da chiamare per guasti e lavori. È la **stessa rubrica di 📇 Riferimenti**: cambiando un contatto in un posto cambia anche nell'altro.")
    contatti = _amm_lista(c, "contatti_casa")
    interventi = _amm_lista(c, "interventi_prof")
    b1, b2 = st.columns(2, gap="small")
    if b1.button("➕ Nuovo professionista", key="amm_ct_nuovo", width="stretch", type="primary"):
        _amm_dlg_contatto(c, None)
    if b2.button("🔧 Registra un intervento", key="amm_in_nuovo", width="stretch"):
        _amm_dlg_intervento(c, None)
    if not contatti:
        st.info("Non hai ancora nessun contatto. Tocca **➕ Nuovo professionista** (elettricista, idraulico, tecnico caldaia…).")
    f1, f2 = st.columns(2, gap="small")
    cats = sorted({amm_categoria_di(m) for m in contatti})
    filtro = f1.selectbox("Categoria", ["Tutte"] + cats, key="amm_ct_filtro")
    cerca = f2.text_input("Cerca", key="amm_ct_cerca", placeholder="nome, attività, categoria…")
    solo_pref = st.toggle("⭐ Solo i preferiti", key="amm_ct_pref")
    vis = []
    for m in contatti:
        ex = amm_extra_di(c, m["id"])
        testo = " ".join(str(v) for v in list(m.values()) + list(ex.values())).lower()
        if (filtro == "Tutte" or amm_categoria_di(m) == filtro) and (not cerca.strip() or cerca.strip().lower() in testo) and (not solo_pref or ex.get("preferito")):
            vis.append((m, ex))
    tel_f = _lv_tel if "_lv_tel" in globals() else (lambda t: "".join(ch for ch in str(t) if ch.isdigit() or ch == "+"))
    for m, ex in sorted(vis, key=lambda t: (not t[1].get("preferito"), amm_categoria_di(t[0]), (t[0].get("referente") or t[0].get("nome") or "").lower())):
        nome = m.get("referente") or m.get("nome") or "Contatto"
        righe = [("🏷️", amm_categoria_di(m) + (f" · {ex['specializzazione']}" if ex.get("specializzazione") else "")), ("🏢", m.get("nome") if m.get("referente") else ""), ("📞", m.get("telefono")), ("📱", m.get("cellulare")),
                 ("✉️", m.get("email")), ("📍", m.get("indirizzo")), ("🕒", (m.get("orari") or "").replace("\n", "; ")), ("💶", (ex.get("costo") or "").replace("\n", "; "))]
        corpo = "<br>".join(f"{ic} {_amm_h.escape(str(v))}" for ic, v in righe if v)
        spesa_tot = amm_totale_interventi(interventi, m["id"])
        st.markdown(f"<div class='amm-card'><b style='font-size:1.05rem'>{'⭐ ' if ex.get('preferito') else ''}{_amm_h.escape(nome)}</b><div style='margin-top:4px'>{corpo}</div>"
                    + (f"<div style='margin-top:4px'><i>{_amm_h.escape(m['note'])}</i></div>" if m.get("note") else "")
                    + (f"<div style='margin-top:4px;opacity:.8'>🔧 Interventi: {sum(1 for i in interventi if i.get('contatto_id') == m['id'])} · speso {amm_euro(spesa_tot)}</div>" if spesa_tot or any(i.get('contatto_id') == m['id'] for i in interventi) else "")
                    + "</div>", unsafe_allow_html=True)
        pulsanti = []
        if m.get("telefono") or m.get("cellulare"):
            pulsanti.append(("📞 Chiama", "tel:" + tel_f(m.get("cellulare") or m.get("telefono"))))
        if "_lv_wa" in globals() and _lv_wa(m.get("cellulare")):
            pulsanti.append(("💬 WhatsApp", "https://wa.me/" + _lv_wa(m["cellulare"])))
        if m.get("email"):
            pulsanti.append(("✉️ Scrivi", "mailto:" + m["email"]))
        if m.get("indirizzo") and "_lv_maps" in globals():
            pulsanti.append(("📍 Mappa", _lv_maps(m["indirizzo"])))
        if str(m.get("sito", "")).startswith(("http://", "https://")):
            pulsanti.append(("🌐 Sito", m["sito"]))
        for i in range(0, len(pulsanti), 3):
            for col, (et, url) in zip(st.columns(len(pulsanti[i:i + 3]), gap="small"), pulsanti[i:i + 3]):
                col.link_button(et, url, width="stretch")
        d1, d2, d3 = st.columns(3, gap="small")
        if d1.button("☆ Togli dai preferiti" if ex.get("preferito") else "⭐ Preferito", key=f"amm_ct_fav_{m['id']}", width="stretch"):
            _amm_preferito(c, m, not ex.get("preferito"))
        if d2.button("✏️ Modifica", key=f"amm_ct_mod_{m['id']}", width="stretch"):
            _amm_dlg_contatto(c, m)
        if d3.button("🗑️ Elimina", key=f"amm_ct_el_{m['id']}", width="stretch"):
            _amm_dlg_togli_contatto(c, m)
        e1, e2 = st.columns(2, gap="small")
        if e1.button("🔧 Intervento", key=f"amm_ct_int_{m['id']}", width="stretch"):
            _amm_dlg_intervento(c, None, m["id"])
        if e2.button(f"📎 Preventivi ({len([x for x in ex.get('preventivi', []) if x])})", key=f"amm_ct_pv_{m['id']}", width="stretch"):
            _amm_dlg_preventivi(c, m)
        prev = [d for d in _amm_lista(c, "documenti") if d.get("id") in ex.get("preventivi", [])]
        if prev:
            with st.expander(f"📎 Preventivi e documenti di {nome[:24]}"):
                nomi_b = {b.get("id"): b.get("nome", "") for b in _amm_lista(c, "beni")}
                for d in prev:
                    if "_ca_riga_documento" in globals():
                        _ca_riga_documento(d, nomi_b, "amct" + m["id"] + "_", _amm_lista(c, "documenti"))
                        if "_ca_correzione_qui" in globals():
                            _ca_correzione_qui(c, d)
    if contatti and not vis:
        st.info("Nessun contatto con questi filtri.")
    if interventi:
        anno = _amm_oggi().year
        with st.expander(f"📜 Interventi registrati ({len(interventi)}) · speso nel {anno}: {amm_euro(amm_totale_interventi(interventi, None, anno))}"):
            nomi_c = {m["id"]: (m.get("referente") or m.get("nome") or "") + " · " + amm_categoria_di(m) for m in contatti}
            nomi_b = {b.get("id"): b.get("nome", "") for b in _amm_lista(c, "beni")}
            for i in sorted(interventi, key=lambda x: x.get("data") or "", reverse=True):
                st.markdown(f"<div class='amm-card' style='padding:8px 12px'><b>{data_it(i.get('data'))}</b> · {_amm_h.escape(nomi_c.get(i.get('contatto_id'), 'contatto eliminato'))} · <b>{amm_euro(i.get('costo'))}</b>"
                            + (f"<div>{_amm_h.escape(i['problema'])}</div>" if i.get("problema") else "") + (f"<div style='opacity:.8'>🏠 {_amm_h.escape(nomi_b.get(i.get('bene_id'), ''))}</div>" if i.get("bene_id") else "")
                            + (f"<div style='opacity:.8'>📎 {len(i.get('allegati', []))} documento/i</div>" if i.get("allegati") else "") + "</div>", unsafe_allow_html=True)
                g1, g2 = st.columns(2, gap="small")
                if g1.button("✏️ Modifica", key=f"amm_in_mod_{i['id']}", width="stretch"):
                    _amm_dlg_intervento(c, i)
                if g2.button("🗑️ Elimina", key=f"amm_in_el_{i['id']}", width="stretch"):
                    _amm_dlg_elimina(c, "interventi_prof", i["id"], "l'intervento del " + data_it(i.get("data")), "")


# ---------------------------------------------------------------------------------------------------------------------
# ♻️ RACCOLTA DIFFERENZIATA e 🛋️ RITIRO INGOMBRANTI
# Il calendario settimanale: i 7 giorni, ogni giorno con uno o più tipi di rifiuto (senza orari). Più «programmi» (per esempio Normale ed Estate), uno attivo alla volta; variazioni per
# singole date (festivi, giorni straordinari); avvisi la sera prima, la mattina stessa e un secondo promemoria, per ogni tipo; file calendario con allarme. Gli avvisi veri li manda il
# programma automatico (promemoria.py) sugli stessi canali di sempre.
# ---------------------------------------------------------------------------------------------------------------------
AMM_GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
AMM_GIORNI_ICS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
AMM_TIPI_RIFIUTO = ["Organico", "Indifferenziato", "Carta", "Vetro", "Plastica", "Metalli"]
AMM_ICONE_RIFIUTO = {"Organico": "🟤", "Indifferenziato": "⚪", "Carta": "🟡", "Vetro": "🔵", "Plastica": "🔴", "Metalli": "🔘"}


def amm_icona_rifiuto(t):
    return AMM_ICONE_RIFIUTO.get(t, "🟣")


def amm_avvisi_raccolta_default():
    return {"sera": True, "ora_sera": "20:00", "mattina": False, "ora_mattina": "07:00", "secondo": False, "ora_secondo": "21:30", "tipi_spenti": []}


def amm_programma_nuovo(nome="Programma normale", attivo=True):
    return {"id": amm_id(), "nome": nome, "attivo": bool(attivo), "giorni": {str(g): {"tipi": [], "nota": "", "nessuna": False} for g in range(7)}, "avvisi": amm_avvisi_raccolta_default()}


def amm_programma_duplica(p, nome=None):
    import copy
    n = copy.deepcopy(p)
    n["id"], n["attivo"] = amm_id(), False
    n["nome"] = nome or ("Copia di " + p.get("nome", "programma"))
    return n


def amm_programma_attivo(programmi):
    return next((p for p in programmi if p.get("attivo")), programmi[0] if programmi else None)


def amm_piano_data(p, eccezioni, d):
    """Cosa si ritira nel giorno `d`: (tipi, nota, nessuna raccolta, «variazione» o «programma»). Una variazione per quella data vale più del programma."""
    for e in eccezioni:
        if e.get("data") == d.isoformat():
            return ([] if e.get("nessuna") else list(e.get("tipi", []))), e.get("nota", ""), bool(e.get("nessuna")), "variazione"
    g = (p or {}).get("giorni", {}).get(str(d.weekday()), {})
    nessuna = bool(g.get("nessuna"))
    return ([] if nessuna else list(g.get("tipi", []))), g.get("nota", ""), nessuna, "programma"


def amm_prossimi_giorni(p, eccezioni, da, quanti=7):
    return [(da + timedelta(days=k), *amm_piano_data(p, eccezioni, da + timedelta(days=k))) for k in range(quanti)]


def amm_eventi_raccolta(p, eccezioni, oggi_, nome_casa=""):
    """Gli eventi del calendario: uno per ogni giorno della settimana con rifiuti (si ripete ogni settimana), i giorni cambiati da una variazione sono esclusi e diventano eventi a parte."""
    av = p.get("avvisi") or amm_avvisi_raccolta_default()
    spenti = set(av.get("tipi_spenti") or [])
    orari = []
    if av.get("sera"):
        orari.append((1, av.get("ora_sera", "20:00")))
    if av.get("mattina"):
        orari.append((0, av.get("ora_mattina", "07:00")))
    if av.get("secondo"):
        orari.append((1, av.get("ora_secondo", "21:30")))
    ev = []
    for g in range(7):
        info = p.get("giorni", {}).get(str(g), {})
        tipi = [t for t in info.get("tipi", []) if t not in spenti]
        if info.get("nessuna") or not tipi:
            continue
        prima = oggi_ + timedelta(days=(g - oggi_.weekday()) % 7)
        esclusi = [date.fromisoformat(e["data"]) for e in eccezioni if e.get("data") and date.fromisoformat(e["data"]).weekday() == g and date.fromisoformat(e["data"]) >= prima]
        ev.append({"uid": f"raccolta-{p['id']}-{g}", "titolo": f"♻️ {AMM_GIORNI[g]}: " + " + ".join(tipi) + (f" ({nome_casa})" if nome_casa else ""), "descrizione": info.get("nota", ""),
                   "data": prima, "ripeti_settimanale": AMM_GIORNI_ICS[g], "escludi": esclusi, "allarmi_orari": orari})
    for e in eccezioni:
        if not e.get("data") or e["data"] < oggi_.isoformat() or e.get("nessuna") or not e.get("tipi"):
            continue
        tipi = [t for t in e["tipi"] if t not in spenti]
        if tipi:
            ev.append({"uid": f"raccolta-var-{e['id']}", "titolo": "♻️ Variazione: " + " + ".join(tipi) + (f" ({nome_casa})" if nome_casa else ""), "descrizione": e.get("nota", ""),
                       "data": date.fromisoformat(e["data"]), "allarmi_orari": orari})
    return ev


def _amm_tipi_disponibili(c):
    return AMM_TIPI_RIFIUTO + [t for t in (c.get("tipi_rifiuto") or []) if t not in AMM_TIPI_RIFIUTO]


def _amm_chip_html(t):
    return f"<span style='display:inline-block;background:rgba(255,255,255,.9);border:1px solid rgba(0,0,0,.12);border-radius:999px;padding:1px 9px;margin:2px 3px 2px 0;font-weight:700'>{amm_icona_rifiuto(t)} {_amm_h.escape(t)}</span>"


def _amm_programmi(c):
    return _amm_lista(c, "raccolta")


def _amm_dlg_giorno(c, p, g):
    def _finestra():
        k = f"amm_gg_{p['id']}_{g}"
        info = p["giorni"].get(str(g), {})
        st.markdown(f"**{AMM_GIORNI[g]}** · {_amm_h.escape(p.get('nome', ''))}")
        disp = _amm_tipi_disponibili(c)
        tipi = st.multiselect("Cosa si ritira", disp, default=[t for t in info.get("tipi", []) if t in disp], key=k + "_t", format_func=lambda t: f"{amm_icona_rifiuto(t)} {t}")
        nuovo = st.text_input("Altro tipo di rifiuto (nuovo)", key=k + "_n", placeholder="es. Sfalci, Oli, Pannolini")
        nota = st.text_input("Note", value=info.get("nota", ""), key=k + "_nota", placeholder="es. esporre entro le 6, sacco giallo")
        nessuna = st.checkbox("🚫 Nessuna raccolta in questo giorno", value=bool(info.get("nessuna")), key=k + "_nes")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva il giorno", key=k + "_ok", type="primary", width="stretch"):
            sel = list(tipi) + ([nuovo.strip()] if nuovo.strip() and nuovo.strip() not in tipi else [])

            def _fn(cc):
                x = _amm_trova(cc, "raccolta", p["id"])
                if x:
                    x["giorni"][str(g)] = {"tipi": sel, "nota": nota.strip(), "nessuna": bool(nessuna)}
                if nuovo.strip() and nuovo.strip() not in AMM_TIPI_RIFIUTO and nuovo.strip() not in (cc.get("tipi_rifiuto") or []):
                    cc.setdefault("tipi_rifiuto", []).append(nuovo.strip())
            _amm_salva(_fn, f"Raccolta: {AMM_GIORNI[g]}")
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog(f"✏️ {AMM_GIORNI[g]}")(_finestra)()


def _amm_dlg_eccezione(c, p, e=None):
    def _finestra():
        k = "amm_ec_" + (e["id"] if e else "nuova")
        dt = st.date_input("Giorno della variazione", value=date.fromisoformat(e["data"]) if e else _amm_oggi() + timedelta(days=1), key=k + "_d", format="DD/MM/YYYY")
        disp = _amm_tipi_disponibili(c)
        tipi = st.multiselect("Cosa si ritira quel giorno", disp, default=[t for t in (e or {}).get("tipi", []) if t in disp], key=k + "_t", format_func=lambda t: f"{amm_icona_rifiuto(t)} {t}")
        nessuna = st.checkbox("🚫 Quel giorno NON c'è la raccolta (festivo)", value=bool((e or {}).get("nessuna")), key=k + "_nes")
        nota = st.text_input("Note", value=(e or {}).get("nota", ""), key=k + "_nota", placeholder="es. Capodanno: spostata a sabato")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva la variazione", key=k + "_ok", type="primary", width="stretch"):
            if not nessuna and not tipi:
                st.error("Scegli cosa si ritira quel giorno, oppure spunta «Quel giorno NON c'è la raccolta».")
                return
            rec = {"data": dt.isoformat(), "tipi": [] if nessuna else tipi, "nessuna": bool(nessuna), "nota": nota.strip(), "programma_id": p["id"]}

            def _fn(cc):
                lista = cc.setdefault("raccolta_ecc", [])
                x = next((y for y in lista if isinstance(y, dict) and y.get("id") == (e or {}).get("id")), None) if e else None
                altra = next((y for y in lista if isinstance(y, dict) and y.get("data") == rec["data"] and y.get("id") != (e or {}).get("id")), None)
                if altra:
                    lista.remove(altra)                                              # una sola variazione per data: quella nuova sostituisce la vecchia
                if x:
                    x.update(rec)
                else:
                    lista.append({"id": amm_id(), **rec})
            _amm_salva(_fn, "Raccolta: variazione")
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("✏️ Variazione" if e else "➕ Variazione (festivo o straordinaria)")(_finestra)()


def _amm_dlg_programma(c, p=None):
    def _finestra():
        k = "amm_pr_" + (p["id"] if p else "nuovo")
        nome = st.text_input("Nome del programma", value=(p or {}).get("nome", ""), key=k + "_n", placeholder="es. Programma normale, Estate, Festività")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_ok", type="primary", width="stretch"):
            if not nome.strip():
                st.error("Scrivi un nome.")
                return

            def _fn(cc):
                if p:
                    x = _amm_trova(cc, "raccolta", p["id"])
                    if x:
                        x["nome"] = nome.strip()
                else:
                    cc.setdefault("raccolta", []).append(amm_programma_nuovo(nome.strip(), attivo=not any(y.get("attivo") for y in _amm_lista(c, "raccolta"))))
            _amm_salva(_fn, "Raccolta: programma")
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("✏️ Programma" if p else "➕ Nuovo programma")(_finestra)()


def _amm_schermata_raccolta(c):
    oggi_ = _amm_oggi()
    st.subheader("♻️ Raccolta differenziata")
    programmi = _amm_programmi(c)
    if not programmi:
        st.info("Costruisci il calendario della tua zona: ogni giorno della settimana puoi scegliere **uno o più tipi di rifiuto**. Poi l'app ti ricorda la sera prima.")
        if st.button("➕ Crea il calendario", key="amm_rc_crea", type="primary", width="stretch"):
            def _crea(cc):
                sel = st.session_state.get("ca_casa_sel") or ""
                if any(isinstance(x, dict) and (x.get("casa_id") or "") == sel for x in cc.get("raccolta", [])):
                    return                                                          # c'è già: un secondo tocco (o un doppio tocco) non ne crea un altro
                cc.setdefault("raccolta", []).append(amm_programma_nuovo())
            _amm_salva(_crea, "Raccolta: calendario creato")
            st.rerun()
        return
    eccez = _amm_lista(c, "raccolta_ecc")
    ids = [p["id"] for p in programmi]
    att = amm_programma_attivo(programmi)
    if len(programmi) > 1:
        sel_id = st.pills("Programma", ids, default=st.session_state.get("amm_rc_sel") if st.session_state.get("amm_rc_sel") in ids else att["id"], key="amm_rc_pill",
                          format_func=lambda i: ("✅ " if i == att["id"] else "") + next(p for p in programmi if p["id"] == i).get("nome", ""))
        sel_id = sel_id or att["id"]
        st.session_state["amm_rc_sel"] = sel_id
    else:
        sel_id = att["id"]
    p = next(x for x in programmi if x["id"] == sel_id)
    st.caption(("✅ **Programma in uso** (quello degli avvisi)" if p["id"] == att["id"] else "Questo programma **non è in uso**: gli avvisi seguono quello con ✅.") + f" · {p.get('nome', '')}")
    doppi = [x for x in programmi if x["id"] != p["id"] and x.get("nome") == p.get("nome") and x.get("giorni") == p.get("giorni")]
    if doppi:
        st.warning(f"Hai **due programmi uguali** chiamati «{p.get('nome', '')}»: uno è di troppo. Tocca il pulsante per togliere il doppione.")
        if st.button("🧹 Elimina il programma doppio", key="amm_pr_doppio", width="stretch", type="primary"):
            tolti = {x["id"] for x in doppi}

            def _fn(cc):
                cc["raccolta"] = [x for x in cc.get("raccolta", []) if not (isinstance(x, dict) and x.get("id") in tolti)]
                resto = [x for x in cc["raccolta"] if isinstance(x, dict) and (x.get("casa_id") or "") == (p.get("casa_id") or "")]
                if resto and not any(x.get("attivo") for x in resto):
                    resto[0]["attivo"] = True
                for e in cc.get("raccolta_ecc", []):
                    if isinstance(e, dict) and e.get("programma_id") in tolti:
                        e["programma_id"] = p["id"]
            _amm_salva(_fn, "Raccolta: tolto il programma doppio")
            st.rerun()
    # oggi e domani
    ap = amm_programma_attivo(programmi)
    ecc_ap = [e for e in eccez if (e.get("programma_id") or ap["id"]) == ap["id"]]
    righe = []
    for d_, et in ((oggi_, "Oggi"), (oggi_ + timedelta(days=1), "Domani")):
        tipi, nota, nessuna, orig = amm_piano_data(ap, ecc_ap, d_)
        righe.append(f"<b>{et}</b> ({AMM_GIORNI[d_.weekday()]}): " + ("🚫 nessuna raccolta" if nessuna else "".join(_amm_chip_html(t) for t in tipi) if tipi else "—")
                     + (f" <i>· {_amm_h.escape(nota)}</i>" if nota else "") + (" <b>(variazione)</b>" if orig == "variazione" else ""))
    st.markdown("<div class='amm-card' style='background:rgba(232,245,233,.92)'>" + "<br>".join(righe) + "</div>", unsafe_allow_html=True)
    # la tabella settimanale (GIORNO · TIPO DI RIFIUTO · NOTE, senza orari)
    # lo stile della tabella di riferimento di Leonardo: griglia sottile, intestazione grigio-verde, giorni abbreviati, riga di OGGI verde e in grassetto
    BORDO = "1px solid rgba(60,80,75,.28)"
    TD = f"padding:12px 8px;border-right:{BORDO};border-bottom:{BORDO};vertical-align:middle;color:#1b2b2a;font-size:1.02rem"
    tr = ""
    for g in range(7):
        info = p["giorni"].get(str(g), {})
        if info.get("nessuna"):
            celle = "🚫 nessuna raccolta"
        else:
            celle = "<br>".join(f"{amm_icona_rifiuto(t)}&nbsp;{_amm_h.escape(t)}" for t in info.get("tipi", [])) or "<span style='opacity:.45'>—</span>"
        oggi_r = g == oggi_.weekday()
        sfondo = "background:#c8e6c9;font-weight:800;" if oggi_r else "background:rgba(240,250,246,.92);"
        tr += (f"<tr style='{sfondo}'><td style='{TD};white-space:nowrap'>{AMM_GIORNI[g][:3]}</td><td style='{TD}'>{celle}</td>"
               f"<td style='{TD};font-size:.92rem;border-right:none'>{_amm_h.escape(info.get('nota', ''))}</td></tr>")
    TH = f"padding:12px 8px;text-align:left;font-weight:800;color:#1b2b2a;border-right:{BORDO};border-bottom:{BORDO};background:#e3e9e6;font-size:.98rem;white-space:nowrap"
    st.markdown(f"<div style='border-radius:16px;overflow:hidden;border:{BORDO};margin:8px 0'><table style='width:100%;border-collapse:collapse;table-layout:fixed'>"
                f"<colgroup><col style='width:22%'><col style='width:48%'><col style='width:30%'></colgroup>"
                f"<thead><tr><th style='{TH}'>Giorno</th><th style='{TH}'>Tipo di rifiuto</th><th style='{TH};border-right:none'>Note</th></tr></thead><tbody>"
                + tr + "</tbody></table></div>", unsafe_allow_html=True)
    st.caption("Tocca un giorno per scegliere cosa si ritira (anche più tipi, anche lo stesso tipo in giorni diversi).")
    for riga in (range(0, 4), range(4, 7)):
        cols = st.columns(len(riga), gap="small")
        for col, g in zip(cols, riga):
            if col.button(f"✏️ {AMM_GIORNI[g][:3]}", key=f"amm_gg_b_{p['id']}_{g}", width="stretch"):
                _amm_dlg_giorno(c, p, g)
    b1, b2, b3 = st.columns(3, gap="small")
    if b1.button("➕ Programma", key="amm_pr_nuovo", width="stretch"):
        _amm_dlg_programma(c, None)
    if b2.button("📑 Duplica", key="amm_pr_dup", width="stretch"):
        copia = amm_programma_duplica(p)
        _amm_salva(lambda cc: cc.setdefault("raccolta", []).append(copia), "Raccolta: programma duplicato")
        st.session_state["amm_rc_sel"] = copia["id"]
        st.rerun()
    if b3.button("✏️ Nome", key="amm_pr_nome", width="stretch"):
        _amm_dlg_programma(c, p)
    if p["id"] != att["id"] and st.button("✅ Usa questo programma per gli avvisi", key="amm_pr_usa", width="stretch", type="primary"):
        def _fn(cc):
            for x in cc.get("raccolta", []):
                if isinstance(x, dict) and (x.get("casa_id") or "") == (p.get("casa_id") or ""):
                    x["attivo"] = x.get("id") == p["id"]
        _amm_salva(_fn, "Raccolta: programma in uso")
        st.rerun()
    if len(programmi) > 1 and st.button("🗑️ Elimina questo programma", key="amm_pr_el", width="stretch"):
        _amm_dlg_elimina(c, "raccolta", p["id"], p.get("nome", "programma"), "Le variazioni restano.")
    # variazioni
    with st.expander(f"📅 Variazioni: festivi e giorni straordinari ({len([e for e in eccez if e.get('data', '') >= oggi_.isoformat()])})"):
        if st.button("➕ Aggiungi una variazione", key="amm_ec_nuova", width="stretch"):
            _amm_dlg_eccezione(c, p, None)
        for e in sorted(eccez, key=lambda x: x.get("data") or ""):
            futura = (e.get("data") or "") >= oggi_.isoformat()
            st.markdown(f"{'🗓️' if futura else '⌛'} **{data_it(e.get('data'))}** ({AMM_GIORNI[date.fromisoformat(e['data']).weekday()]}): " + ("🚫 nessuna raccolta" if e.get("nessuna") else "".join(_amm_chip_html(t) for t in e.get("tipi", [])))
                        + (f" · {_amm_h.escape(e['nota'])}" if e.get("nota") else ""), unsafe_allow_html=True)
            x1, x2 = st.columns(2, gap="small")
            if x1.button("✏️ Modifica", key=f"amm_ec_mod_{e['id']}", width="stretch"):
                _amm_dlg_eccezione(c, p, e)
            if x2.button("🗑️ Elimina", key=f"amm_ec_el_{e['id']}", width="stretch"):
                _amm_dlg_elimina(c, "raccolta_ecc", e["id"], "la variazione del " + data_it(e.get("data")), "")
    # avvisi
    with st.expander("🔔 Avvisi della raccolta"):
        av = {**amm_avvisi_raccolta_default(), **(p.get("avvisi") or {})}
        k = "amm_av_" + p["id"]
        sera = st.checkbox("🌙 La sera prima", value=av["sera"], key=k + "_s")
        ora_s = st.text_input("Ora (sera prima)", value=av["ora_sera"], key=k + "_os", help="Formato 20:00") if sera else av["ora_sera"]
        mat = st.checkbox("☀️ La mattina stessa", value=av["mattina"], key=k + "_m")
        ora_m = st.text_input("Ora (mattina)", value=av["ora_mattina"], key=k + "_om") if mat else av["ora_mattina"]
        sec = st.checkbox("⏰ Un secondo promemoria la sera prima", value=av["secondo"], key=k + "_2")
        ora_2 = st.text_input("Ora (secondo promemoria)", value=av["ora_secondo"], key=k + "_o2") if sec else av["ora_secondo"]
        disp = _amm_tipi_disponibili(c)
        attivi = st.multiselect("Avvisami per questi tipi di rifiuto", disp, default=[t for t in disp if t not in av.get("tipi_spenti", [])], key=k + "_ti", format_func=lambda t: f"{amm_icona_rifiuto(t)} {t}")
        if st.button("💾 Salva gli avvisi", key=k + "_ok", type="primary", width="stretch"):
            def _ora_ok(x):
                try:
                    h, m = x.strip().split(":")
                    return 0 <= int(h) <= 23 and 0 <= int(m) <= 59
                except (ValueError, AttributeError):
                    return False
            if not (_ora_ok(ora_s) and _ora_ok(ora_m) and _ora_ok(ora_2)):
                st.error("Scrivi le ore come 20:00 oppure 07:30.")
            else:
                nuovi = {"sera": sera, "ora_sera": ora_s.strip(), "mattina": mat, "ora_mattina": ora_m.strip(), "secondo": sec, "ora_secondo": ora_2.strip(), "tipi_spenti": [t for t in disp if t not in attivi]}

                def _fn(cc):
                    x = _amm_trova(cc, "raccolta", p["id"])
                    if x:
                        x["avvisi"] = nuovi
                _amm_salva(_fn, "Raccolta: avvisi")
                st.rerun()
        st.caption("I messaggi arrivano sui canali scelti in **Salute → 🔔 Scegli come ricevere gli avvisi**, con **«🏡 Avvisami anche di Casa»** acceso, **entro mezz'ora dall'ora scelta**. "
                   "L'app non può suonare da sola: il suono è quello di Telegram, WhatsApp o email. Per un **allarme del telefono** scarica il calendario qui sotto.")
        casa_nome = ""
        ev = amm_eventi_raccolta(p, [e for e in eccez if (e.get("programma_id") or p["id"]) == p["id"]], oggi_, casa_nome)
        if ev:
            st.download_button(f"📅 Metti la raccolta nel calendario del telefono ({len(ev)} eventi, con allarme)", amm_ics(ev, "Raccolta differenziata"), file_name="raccolta_differenziata.ics",
                               mime="text/calendar", key="amm_ics_raccolta", width="stretch")
        else:
            st.caption("Scegli i rifiuti dei giorni per poter scaricare il calendario.")
    # prossimi giorni
    with st.expander("🔎 Prossimi 14 giorni"):
        for d_, tipi, nota, nessuna, orig in amm_prossimi_giorni(ap, ecc_ap, oggi_, 14):
            if tipi or nessuna:
                st.markdown(f"**{AMM_GIORNI[d_.weekday()][:3]} {d_.strftime('%d/%m')}** · " + ("🚫 nessuna raccolta" if nessuna else "".join(_amm_chip_html(t) for t in tipi)) + (" **(variazione)**" if orig == "variazione" else ""), unsafe_allow_html=True)


# ---------- 🛋️ RITIRO INGOMBRANTI ----------
def _amm_dlg_ingombranti(c, m=None):
    def _finestra():
        k = "amm_ig_" + (m["id"] if m else "nuovo")
        nome = st.text_input("Servizio o azienda *", value=(m or {}).get("nome", ""), key=k + "_n", placeholder="es. AMIAT ritiro ingombranti, Comune di …")
        c1, c2 = st.columns(2)
        tel = c1.text_input("Telefono / numero verde", value=(m or {}).get("telefono", ""), key=k + "_t")
        cell = c2.text_input("Cellulare / WhatsApp", value=(m or {}).get("cellulare", ""), key=k + "_c")
        email = st.text_input("Email", value=(m or {}).get("email", ""), key=k + "_e")
        sito = st.text_input("Sito per prenotare", value=(m or {}).get("sito", ""), key=k + "_s", placeholder="https://…")
        come = st.text_area("Come si prenota", value=(m or {}).get("come", ""), key=k + "_come", height=80, placeholder="es. telefonare con 3 giorni d'anticipo; max 3 pezzi")
        orari = st.text_input("Giorni e orari del ritiro", value=(m or {}).get("orari", ""), key=k + "_o", placeholder="es. giovedì mattina")
        costo = st.text_input("Costo", value=(m or {}).get("costo", ""), key=k + "_costo", placeholder="es. gratuito 2 volte l'anno")
        note = st.text_area("Note", value=(m or {}).get("note", ""), key=k + "_note", height=70)
        pr = st.date_input("Prossimo ritiro prenotato (facoltativo)", value=date.fromisoformat(m["prossimo_ritiro"]) if (m or {}).get("prossimo_ritiro") else None, key=k + "_pr", format="DD/MM/YYYY")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_ok", type="primary", width="stretch"):
            if not nome.strip():
                st.error("Scrivi il nome del servizio.")
                return
            rec = {"nome": nome.strip(), "telefono": tel.strip(), "cellulare": cell.strip(), "email": email.strip(), "sito": sito.strip(), "come": come.strip(), "orari": orari.strip(), "costo": costo.strip(),
                   "note": note.strip(), "prossimo_ritiro": pr.isoformat() if pr else ""}

            def _fn(cc):
                lista = cc.setdefault("ingombranti", [])
                x = next((y for y in lista if isinstance(y, dict) and y.get("id") == (m or {}).get("id")), None) if m else None
                if x:
                    x.update(rec)
                else:
                    lista.append({"id": amm_id(), **rec})
            _amm_salva(_fn, "Ingombranti: " + nome.strip()[:40])
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("✏️ Ritiro ingombranti" if m else "➕ Servizio per gli ingombranti")(_finestra)()


def _amm_schermata_ingombranti(c):
    oggi_ = _amm_oggi()
    st.subheader("🛋️ Ritiro ingombranti")
    st.caption("Mobili, materassi, elettrodomestici: i servizi da chiamare per farli ritirare, come si prenota e quando passano.")
    lista = _amm_lista(c, "ingombranti")
    if st.button("➕ Aggiungi un servizio", key="amm_ig_nuovo", width="stretch", type="primary" if not lista else "secondary"):
        _amm_dlg_ingombranti(c, None)
    if not lista:
        st.info("Non hai ancora inserito nessun servizio. Tocca **➕ Aggiungi un servizio** (il Comune, l'azienda dei rifiuti, una ditta privata).")
    tel_f = _lv_tel if "_lv_tel" in globals() else (lambda t: "".join(ch for ch in str(t) if ch.isdigit() or ch == "+"))
    for m in sorted(lista, key=lambda x: x.get("nome", "").lower()):
        pr = m.get("prossimo_ritiro")
        g = amm_giorni_a(pr, oggi_) if pr else None
        righe = [("📞", m.get("telefono")), ("📱", m.get("cellulare")), ("✉️", m.get("email")), ("🕒 Ritiro", m.get("orari")), ("💶", m.get("costo"))]
        corpo = "<br>".join(f"{ic} {_amm_h.escape(v)}" for ic, v in righe if v)
        st.markdown(f"<div class='amm-card'><b style='font-size:1.05rem'>🛋️ {_amm_h.escape(m['nome'])}</b><div style='margin-top:4px'>{corpo}</div>"
                    + (f"<div style='margin-top:4px'><b>Come si prenota:</b> {_amm_h.escape(m['come'])}</div>" if m.get("come") else "")
                    + (f"<div style='margin-top:6px'>📅 <b>Prossimo ritiro prenotato: {data_it(pr)}</b> ({'oggi' if g == 0 else 'tra ' + str(g) + ' giorni' if g is not None and g > 0 else 'passato'})</div>" if pr else "")
                    + (f"<div style='margin-top:4px'><i>{_amm_h.escape(m['note'])}</i></div>" if m.get("note") else "") + "</div>", unsafe_allow_html=True)
        pulsanti = []
        if m.get("telefono") or m.get("cellulare"):
            pulsanti.append(("📞 Chiama", "tel:" + tel_f(m.get("telefono") or m.get("cellulare"))))
        if "_lv_wa" in globals() and _lv_wa(m.get("cellulare")):
            pulsanti.append(("💬 WhatsApp", "https://wa.me/" + _lv_wa(m["cellulare"])))
        if m.get("email"):
            pulsanti.append(("✉️ Scrivi", "mailto:" + m["email"]))
        if str(m.get("sito", "")).startswith(("http://", "https://")):
            pulsanti.append(("🌐 Prenota online", m["sito"]))
        for i in range(0, len(pulsanti), 3):
            for col, (et, url) in zip(st.columns(len(pulsanti[i:i + 3]), gap="small"), pulsanti[i:i + 3]):
                col.link_button(et, url, width="stretch")
        d1, d2 = st.columns(2, gap="small")
        if d1.button("✏️ Modifica", key=f"amm_ig_mod_{m['id']}", width="stretch"):
            _amm_dlg_ingombranti(c, m)
        if d2.button("🗑️ Elimina", key=f"amm_ig_el_{m['id']}", width="stretch"):
            _amm_dlg_elimina(c, "ingombranti", m["id"], m["nome"], "")


# ---------------------------------------------------------------------------------------------------------------------
# 📥 IMPORTARE UN DOCUMENTO in «Spese e scadenze»
# Si usa lo STESSO sistema di Documenti (caricamento con tutti i suoi modi, lettura, archiviazione dell'originale): qui sopra c'è solo la lettura delle RATE e la conferma che crea la spesa.
# Sempre con la conferma di chi usa l'app: l'app propone, tu controlli.
# ---------------------------------------------------------------------------------------------------------------------
_AMM_MESI_NOMI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
_AMM_RE_DATA = re.compile(r"(?<![\d/.\-])(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?![\d/])|(?<!\d)(\d{1,2})\s+(" + "|".join(_AMM_MESI_NOMI) + r")\s+(\d{4})", re.I)
_AMM_RE_IMPORTO = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d+),(\d{2})(?![\d])")
_AMM_RE_RATA = re.compile(r"(?:\b(\d{1,2})\s*[ªaº°^]?\s*rata\b|\brata\s*(?:n\.?|nr\.?|num\.?|numero)?\s*[:.]?\s*(\d{1,2})\b(?:\s*(?:/|di)\s*(\d{1,2}))?)", re.I)
_AMM_RE_RICEVUTA = re.compile(r"ricevuta di pagamento|quietanza|attestazione di pagamento|pagamento (?:eseguito|effettuato|disposto)|bonifico (?:eseguito|disposto|effettuato)|esito (?:del )?pagamento|\bCRO\b|\bTRN\b|pagato in data|ricevuta del bonifico", re.I)


def amm_parse_data(s):
    """«15/12/2026», «15-12-26», «15.12.2026», «2026-12-15», «15 dicembre 2026» → date (None se non è una data)."""
    t = str(s or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        try:
            return date.fromisoformat(t)
        except ValueError:
            return None
    m = _AMM_RE_DATA.search(t)
    return _amm_data_da_match(m) if m else None


def _amm_data_da_match(m):
    try:
        if m.group(1):
            a = int(m.group(3))
            return date(a + 2000 if a < 100 else a, int(m.group(2)), int(m.group(1)))
        return date(int(m.group(6)), _AMM_MESI_NOMI.index(m.group(5).lower()) + 1, int(m.group(4)))
    except ValueError:
        return None


def _amm_importo_da_match(m):
    return round(float(m.group(1).replace(".", "") + "." + m.group(2)), 2)


def _amm_scegli_data(finestra, oggi_):
    """La data di SCADENZA in un pezzo di testo: quella dopo la parola «scad…», altrimenti l'ultima. Solo date plausibili (da due anni fa a quattro anni avanti)."""
    ds = [(m, _amm_data_da_match(m)) for m in _AMM_RE_DATA.finditer(finestra)]
    ds = [(m, d) for m, d in ds if d and oggi_.replace(year=oggi_.year - 2) <= d <= oggi_.replace(year=oggi_.year + 4)]
    if not ds:
        return None
    for m, d in ds:
        if re.search(r"scad\w*[^\d]{0,25}$", finestra[:m.start()], re.I):
            return d
    return ds[-1][1]


def _amm_scegli_importo(finestra, dopo=0):
    """L'importo della rata: il primo importo che non segue «totale» o «saldo»."""
    for m in _AMM_RE_IMPORTO.finditer(finestra, dopo):
        if not re.search(r"(totale|saldo|residuo)\W{0,12}$", finestra[:m.start()], re.I) and _amm_importo_da_match(m) > 0:
            return _amm_importo_da_match(m)
    return None


def amm_leggi_avviso(testo, oggi_=None):
    """Legge il testo di un avviso di pagamento / piano rate / bollettino / ricevuta. NON decide niente: propone.
    → {tipo: 'avviso'|'ricevuta'|'altro', rate: [(data, importo, n)], totale, n_dichiarato, pagamento: {data, importo}, iban, descrizione, categoria, affidabilita, note[]}"""
    oggi_ = oggi_ or date.today()
    righe = [r.strip() for r in str(testo or "").splitlines() if r.strip()]
    ris = {"tipo": "altro", "rate": [], "totale": None, "n_dichiarato": None, "pagamento": None, "iban": "", "descrizione": "", "categoria": "Spese condominiali ordinarie", "affidabilita": "bassa", "note": []}
    if not righe:
        return ris
    cand = []
    for i, r in enumerate(righe):
        mr = _AMM_RE_RATA.search(r)
        tab = re.match(r"^\s*(\d{1,2})[\s.)\-]+(?:\S+\s+){0,2}?(\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*\d{2,4})", r)
        if not (mr or tab):
            continue
        finestra = r
        k_ = i + 1
        while mr and not (_AMM_RE_DATA.search(finestra) and _AMM_RE_IMPORTO.search(finestra)) and k_ < len(righe) and k_ <= i + 3 and not _AMM_RE_RATA.search(righe[k_]):
            finestra += " " + righe[k_]                                                 # il marcatore «2ª rata» e i suoi dati possono stare su più righe (fino a 3)
            k_ += 1
        d = _amm_scegli_data(finestra, oggi_)
        imp = _amm_scegli_importo(finestra, (_AMM_RE_DATA.search(finestra).end() if _AMM_RE_DATA.search(finestra) else 0))
        if imp is None:
            imp = _amm_scegli_importo(finestra)
        if not d or not imp:
            continue
        if mr:
            nr = int(mr.group(1) or mr.group(2))
            if mr.group(3):
                ris["n_dichiarato"] = int(mr.group(3))
        else:
            nr = int(tab.group(1))
        if (d, imp) not in [(x[0], x[1]) for x in cand]:
            cand.append((d, imp, nr))
    ris["rate"] = sorted(cand, key=lambda x: (x[0], x[2]))
    for r in righe:                                                                      # il totale scritto nel documento
        if re.search(r"\btotale\b", r, re.I) and not _AMM_RE_RATA.search(r):
            ims = list(_AMM_RE_IMPORTO.finditer(r))
            if ims:
                ris["totale"] = _amm_importo_da_match(ims[-1])
                break
    comp = testo.replace(" ", "").upper() if isinstance(testo, str) else ""
    mi = re.search(r"IT\d{2}[A-Z]\d{10}[A-Z0-9]{12}", comp)
    if mi and amm_iban_valido(mi.group(0)):
        ris["iban"] = mi.group(0)
    t_low = str(testo).lower()
    if _AMM_RE_RICEVUTA.search(testo) and len(ris["rate"]) <= 1:
        ris["tipo"] = "ricevuta"
        d = None
        for r in righe:
            if re.search(r"data|valuta|esecuzione|eseguit|pagat", r, re.I):
                d = _amm_scegli_data(r, oggi_)
                if d:
                    break
        imp = None
        for r in righe:
            if re.search(r"importo|totale|pagat|euro|€", r, re.I):
                imp = _amm_scegli_importo(r)
                if imp:
                    break
        ris["pagamento"] = {"data": d, "importo": imp}
        ris["affidabilita"] = "alta" if (d and imp) else "media"
    elif ris["rate"]:
        ris["tipo"] = "avviso"
        somma = round(sum(x[1] for x in ris["rate"]), 2)
        ris["affidabilita"] = "alta" if (len(ris["rate"]) >= 2 and (ris["totale"] is None or abs(somma - ris["totale"]) < 0.06)) else "media"
        if ris["totale"] is not None and abs(somma - ris["totale"]) >= 0.06:
            ris["note"].append(f"La somma delle rate che ho letto ({amm_euro(somma)}) non è uguale al totale scritto nel documento ({amm_euro(ris['totale'])}): controlla le rate.")
        if ris["n_dichiarato"] and ris["n_dichiarato"] != len(ris["rate"]):
            ris["note"].append(f"Il documento parla di {ris['n_dichiarato']} rate, io ne ho trovate {len(ris['rate'])}.")
    else:                                                                                # un bollettino con una sola scadenza e un solo importo
        d = None
        for r in righe:
            if re.search(r"scad", r, re.I):
                d = _amm_scegli_data(r, oggi_) or d
        imp = None
        for r in righe:
            if re.search(r"importo|da pagare|euro|€|totale", r, re.I):
                imp = _amm_scegli_importo(r) or imp
        if d or imp:
            ris["tipo"] = "avviso"
            ris["rate"] = [(d, imp, 1)] if (d and imp) else []
            ris["pagamento"] = {"data": d, "importo": imp} if not (d and imp) else None
            ris["affidabilita"] = "media" if (d and imp) else "bassa"
    if "straordinar" in t_low or "lavori" in t_low:
        ris["categoria"] = "Rata straordinaria o lavori"
    elif "riscaldament" in t_low:
        ris["categoria"] = "Riscaldamento"
    elif "assicuraz" in t_low or "polizza" in t_low:
        ris["categoria"] = "Assicurazione"
    elif "ascensore" in t_low:
        ris["categoria"] = "Ascensore"
    anno = (ris["rate"][0][0].year if ris["rate"] and ris["rate"][0][0] else oggi_.year)
    ris["descrizione"] = ("Lavori straordinari " if ris["categoria"] == "Rata straordinaria o lavori" else "Rate condominio ") + str(anno)
    return ris


def amm_crea_spesa_da_rate(descrizione, categoria, rate, amministratore_id="", note="", avvisi_giorni=None, rinnovo_auto=False):
    """Come amm_crea_spesa, ma con le date e gli importi di ogni rata già decisi (letti da un documento o scritti a mano). rate: [(date, importo)]."""
    rate = sorted(rate, key=lambda x: x[0])
    s = amm_crea_spesa(descrizione, categoria, sum(x[1] for x in rate), 1, rate[0][0], 0, amministratore_id, note, avvisi_giorni, rinnovo_auto)
    s["rate"] = [{"id": amm_id(), "n": k + 1, "scadenza": d.isoformat(), "importo": round(float(imp), 2), "pagamenti": []} for k, (d, imp) in enumerate(rate)]
    s["importo_totale"] = round(sum(x[1] for x in rate), 2)
    s["storico"] = [{"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "testo": f"Spesa creata da un documento: {len(rate)} rata/e"}]
    return s


def amm_trova_rata_per_ricevuta(spese, importo, data_iso=None):
    """Le rate non pagate che possono essere quelle di una ricevuta: prima quelle con lo stesso importo (la più vicina alla data del pagamento), poi quelle che resterebbero pagate in parte.
    → [(spesa, rata, esatta)]"""
    if not importo:
        return []
    rif = amm_parse_data(data_iso) if data_iso else date.today()
    rif = rif or date.today()
    esatte, parziali = [], []
    for s in spese:
        for r in amm_rate_ordinate(s):
            res = amm_residuo(r)
            if res <= 0.004:
                continue
            try:
                dist = abs((date.fromisoformat(r["scadenza"]) - rif).days)
            except (KeyError, ValueError):
                dist = 9999
            if abs(res - importo) < 0.011:
                esatte.append((dist, s, r))
            elif importo < res:
                parziali.append((dist, s, r))
    return [(s, r, True) for _d, s, r in sorted(esatte, key=lambda x: x[0])] + [(s, r, False) for _d, s, r in sorted(parziali, key=lambda x: x[0])][:6]


def _amm_import_pannello(c):
    """Il pulsante «Importa un documento» in cima a Spese e scadenze e, aperto, il caricamento di Documenti (stessi modi: foto, galleria, PDF, più file, link)."""
    if not st.session_state.get("amm_imp_on"):
        if st.button("📥 Importa un documento (avviso, rate, bollettino, ricevuta)", key="amm_imp_apri", width="stretch"):
            st.session_state["amm_imp_on"] = True
            st.rerun()
        return
    st.markdown("##### 📥 Importa un documento")
    st.caption("Carica l'**avviso di pagamento**, il **piano delle rate**, il **bollettino** o la **ricevuta** (PDF, foto o scansione). Lo leggo e ti propongo la spesa con le sue rate, "
               "oppure il pagamento da segnare. **Controlli e confermi tu.** Il file originale resta archiviato in 📚 Documenti.")
    if st.button("✖ Chiudi l'importazione", key="amm_imp_chiudi", width="stretch"):
        for k in ("amm_imp_on", "amm_imp", "amm_imp_chiave", "ca_bozza_in"):
            st.session_state.pop(k, None)
        st.rerun()
    if "_ca_pannello_caricamento" not in globals() or "ca_riconosci" not in globals():
        st.error("Il caricamento dei documenti non è disponibile adesso.")
        return
    n = st.session_state.get("ca_giro", 0)
    up = _ca_pannello_caricamento(n)
    _amm_import_flusso(c, n, up)


def _amm_import_flusso(c, n, up):
    sorgente = None
    if up is not None:
        dati_up = up.getvalue()
        sorgente = {"nome": up.name, "mime": _ca_mime(up.name, up.type, dati_up), "dati": dati_up, "link": ""}
    elif st.session_state.get("ca_bozza_in"):
        sorgente = dict(st.session_state["ca_bozza_in"])
        sorgente.setdefault("mime", _ca_mime(sorgente.get("nome"), "", sorgente.get("dati")))
    if not sorgente:
        st.session_state.pop("amm_imp_chiave", None)
        return
    if sorgente["mime"].startswith("image/") and len(sorgente["dati"]) > _CA_MAX_BYTE and not sorgente.get("ridotta"):
        rid = _ca_riduci_foto(sorgente["nome"], sorgente["dati"])
        if rid:
            sorgente = dict(sorgente, nome=rid[0], mime="image/jpeg", dati=rid[1], ridotta=True)
            st.info("📷 La foto era molto grande: l'ho **ridotta** per poterla archiviare. Il testo si legge lo stesso.")
    if sorgente["mime"] not in _CA_MIME:
        st.error(f"Questo tipo di file non è ammesso: carica un PDF o una foto (JPG, PNG, WebP). Il file «{sorgente['nome']}» risulta di tipo «{sorgente['mime']}».")
        return
    if len(sorgente["dati"]) > _CA_MAX_BYTE:
        st.error("Il file è troppo grande (massimo 8 MB).")
        return
    sha = _ca_sha(sorgente["dati"])
    stato = st.session_state.get("amm_imp")
    if not stato or stato.get("sha") != sha:
        with st.spinner("Leggo il documento…"):
            testo, info = ca_estrai_testo(sorgente["nome"], sorgente["mime"], sorgente["dati"])
            ric = ca_riconosci(sorgente["nome"], sorgente["mime"], sorgente["dati"], testo, info)
        stato = {"sha": sha, "ric": ric, "prop": amm_leggi_avviso(testo or "", _amm_oggi()), "testo_ok": bool(testo)}
        st.session_state["amm_imp"] = stato
    chiave = f"{n}:{sha}"
    if st.session_state.get("amm_imp_chiave") != chiave:
        st.session_state["amm_imp_chiave"] = chiave                                       # la finestra si apre da sola una volta per ogni file
        _amm_dlg_import(c, n, sorgente, sha, stato["ric"], stato["prop"], stato["testo_ok"])
    else:
        st.info(f"📖 C'è un documento aperto: «{_amm_h.escape(sorgente['nome'])}». Se hai chiuso la finestra, riaprila.")
        r1, r2 = st.columns(2, gap="small")
        if r1.button("📖 Riapri il pannello", key=f"amm_imp_riapri_{n}", type="primary", width="stretch"):
            _amm_dlg_import(c, n, sorgente, sha, stato["ric"], stato["prop"], stato["testo_ok"])
        if r2.button("✖ Scarta il documento", key=f"amm_imp_scarta_{n}", width="stretch"):
            for k in ("ca_bozza_in", "amm_imp", "amm_imp_chiave"):
                st.session_state.pop(k, None)
            st.session_state["ca_giro"] = n + 1
            st.rerun()


def _amm_archivia_import(c, n, sorgente, sha, ric, esatto, tipo=None, ente="", importo=None, nota=""):
    """Archivia l'originale con lo STESSO sistema di Documenti (_ca_archivia): se è già archiviato non lo ricopia. → (id del documento, messaggio)."""
    if esatto:
        return esatto.get("id"), "Il documento era già archiviato in Documenti: l'ho usato così com'è."
    nid = uuid.uuid4().hex[:12]
    _ca_scrivi_file(nid, sorgente["nome"], sorgente["mime"], sorgente["dati"])
    val = _ca_val_da_ric(ric)
    if tipo:
        val["tipo"] = tipo
        val["argomento"] = "Condominio"
    if ente:
        val["ente"] = ente
    if importo:
        val["importo"] = f"{float(importo):.2f}"
    if nota:
        val["note"] = nota
    msg = _ca_archivia(dict(sorgente, file_id=nid), sha, ric, {"sha": sha, "bene": ""}, val, n)
    doc = next((x for x in _ca_dati().get("documenti", []) if (x.get("file") or {}).get("id") == nid), None)
    return (doc or {}).get("id"), msg


def _amm_dlg_import(c, n, sorgente, sha, ric, prop, testo_ok=True):
    def _finestra():
        k = "amm_im_" + sha[:8]
        spese = _amm_lista(c, "spese_amm")
        docs = _amm_lista(c, "documenti")
        adm = _amm_lista(c, "amministratori")
        campi = ric.get("campi", {})
        st.caption(f"📄 {sorgente.get('nome')}")
        doppi = ca_trova_doppioni(docs, ric, sha) if "ca_trova_doppioni" in globals() else []
        esatto = next((d for d, _m, f in doppi if f >= 3 and (d.get("file") or {}).get("sha256") == sha), None)
        if esatto:
            st.warning(f"Questo documento è **già archiviato** in Documenti («{_amm_h.escape(esatto.get('titolo') or esatto.get('tipo') or 'documento')}»): non lo copio di nuovo, lo uso così com'è.")
        elif doppi:
            st.warning("Somiglia a un documento già archiviato: " + "; ".join(f"«{_amm_h.escape(d.get('titolo') or d.get('tipo') or 'documento')}»" for d, _m, _f in doppi[:2]) + ". Se è lo stesso, scartalo.")
        def _fmt(ch, val):
            if ch == "importo" and amm_importo(val) is not None:
                return amm_euro(amm_importo(val))
            if ch == "scadenza_doc" and amm_parse_data(val):
                return amm_parse_data(val).strftime("%d/%m/%Y")
            return str(val)
        letti = [f"**{et}:** {_amm_h.escape(_fmt(ch, (campi.get(ch) or {}).get('valore')))}" for et, ch in (("Ente", "ente"), ("Numero", "numero_doc"), ("Importo", "importo"), ("Scadenza", "scadenza_doc")) if (campi.get(ch) or {}).get("valore")]
        if prop["rate"]:
            letti.append(f"**Rate trovate:** {len(prop['rate'])}")
        st.markdown("🔎 **Ho letto:** " + (" · ".join(letti) if letti else "niente di chiaro") + (f" · affidabilità **{prop['affidabilita']}**" if prop["rate"] or prop.get("pagamento") else ""))
        if not testo_ok:
            st.warning("Non sono riuscito a leggere il testo del documento (è una foto poco leggibile?). Puoi scrivere tu i dati qui sotto: il file viene archiviato lo stesso.")
        for nota in prop["note"]:
            st.warning(nota)
        pag = prop.get("pagamento") or {}
        imp_ric = pag.get("importo") or amm_importo((campi.get("importo") or {}).get("valore"))
        opz = ["nuova"] + (["ricevuta"] if spese else []) + (["allega"] if spese else []) + ["solo"]
        etichette = {"nuova": "➕ Crea una nuova spesa con le sue rate", "ricevuta": "💶 È la ricevuta di un pagamento: segna pagata una rata", "allega": "📎 Allega il documento a una spesa già inserita",
                     "solo": "📥 Archivia soltanto, in Documenti"}
        pre = "ricevuta" if (prop["tipo"] == "ricevuta" and spese) else "nuova" if (prop["rate"] or imp_ric) else "solo"
        az = st.radio("Cosa vuoi fare?", opz, index=opz.index(pre), format_func=lambda x: etichette[x], key=k + "_az")
        ente = (campi.get("ente") or {}).get("valore") or (adm[0].get("studio") if adm else "") or ""
        da_fare = {}
        if az == "nuova":
            descr = st.text_input("Descrizione della spesa *", value=prop["descrizione"], key=k + "_d")
            cat = st.selectbox("Categoria", AMM_CATEGORIE, index=AMM_CATEGORIE.index(prop["categoria"]) if prop["categoria"] in AMM_CATEGORIE else 0, key=k + "_c")
            manuale = True if not prop["rate"] else st.checkbox("Non è giusto: le rate le scrivo io", key=k + "_man")
            rate_in = []
            if not manuale:
                st.markdown("**Le rate (puoi correggerle):**")
                for i, (d_, imp, nr) in enumerate(prop["rate"]):
                    a, b = st.columns([3, 2], gap="small")
                    rate_in.append((a.text_input(f"Rata {i + 1}: scadenza", value=d_.strftime("%d/%m/%Y"), key=f"{k}_rd{i}"), b.text_input("Importo €", value=f"{imp:.2f}".replace(".", ","), key=f"{k}_ri{i}")))
            else:
                tot = st.text_input("Importo totale (€) *", value=(f"{imp_ric:.2f}".replace(".", ",") if imp_ric else ""), key=k + "_t")
                nr_ = st.number_input("Numero di rate", min_value=1, max_value=60, value=1, step=1, key=k + "_n")
                d0 = amm_parse_data((campi.get("scadenza_doc") or {}).get("valore")) or (_amm_oggi() + timedelta(days=30))
                prima = st.date_input("Scadenza della prima rata *", value=d0, key=k + "_p", format="DD/MM/YYYY")
                per = st.selectbox("Ogni quanto scadono le rate", list(AMM_PERIODI), index=3, key=k + "_per")
                mesi = AMM_PERIODI[per] if AMM_PERIODI[per] is not None else int(st.number_input("Ogni quanti mesi", min_value=1, max_value=60, value=1, step=1, key=k + "_mesi"))
            giorni = st.multiselect("Avvisami quanti giorni prima", AMM_GIORNI_AVVISO, default=st.session_state.get("amm_giorni_default", AMM_GIORNI_DEFAULT), key=k + "_g",
                                    format_func=lambda g_: "il giorno stesso" if g_ == 0 else f"{g_} giorno" if g_ == 1 else f"{g_} giorni")
            opz_a = [""] + [x["id"] for x in adm]
            adm_sel = st.selectbox("Amministratore", opz_a, key=k + "_a", format_func=lambda i: "— nessuno —" if not i else _amm_nome_admin(c, i))
            da_fare = {"descr": descr, "cat": cat, "manuale": manuale, "rate_in": rate_in, "giorni": giorni, "adm": adm_sel}
            if manuale:
                da_fare.update({"tot": tot, "n": int(nr_), "prima": prima, "mesi": mesi})
        elif az == "ricevuta":
            imp_txt = st.text_input("Importo pagato (€)", value=(f"{imp_ric:.2f}".replace(".", ",") if imp_ric else ""), key=k + "_pi")
            d_pag = st.date_input("Data del pagamento", value=pag.get("data") or _amm_oggi(), key=k + "_pd", format="DD/MM/YYYY")
            cand = amm_trova_rata_per_ricevuta(spese, amm_importo(imp_txt), d_pag.isoformat())
            if not cand:
                st.info("Non trovo una rata da pagare con questo importo. Controlla l'importo, oppure scegli «Allega» o «Archivia soltanto».")
            else:
                if cand[0][2]:
                    st.success("Ho trovato una rata con lo **stesso importo**: è questa?")
                chiavi = [f"{s_['id']}|{r_['id']}" for s_, r_, _e in cand]
                scelta = st.radio("A quale rata la collego?", chiavi, key=k + "_ra",
                                  format_func=lambda x: next((f"{s_['descrizione']} · rata {r_['n']} · {data_it(r_['scadenza'])} · resta {amm_euro(amm_residuo(r_))}" + (" ✅ stesso importo" if e_ else " (pagamento parziale)")
                                                              for s_, r_, e_ in cand if f"{s_['id']}|{r_['id']}" == x), x))
                modo = st.selectbox("Come hai pagato", _CA_MODI_PAGAMENTO if "_CA_MODI_PAGAMENTO" in globals() else ["Bonifico", "Contanti", "Altro"], key=k + "_pm")
                da_fare = {"imp": imp_txt, "data": d_pag, "scelta": scelta, "modo": modo}
        elif az == "allega":
            sp_id = st.selectbox("A quale spesa", [x["id"] for x in spese], key=k + "_sp", format_func=lambda i: next((x["descrizione"] for x in spese if x["id"] == i), i))
            da_fare = {"spesa": sp_id}
        c1, c2 = st.columns(2, gap="small")
        if c1.button("✅ Conferma e archivia", key=k + "_ok", type="primary", width="stretch"):
            try:
                errore = _amm_import_esegui(c, n, sorgente, sha, ric, esatto, az, ente, imp_ric, da_fare)
            except Exception as e:                                                         # niente si perde in silenzio
                errore = f"Non sono riuscito a salvare: {e}"
            if errore:
                st.error(errore)
                return
            for kk in ("amm_imp_on", "amm_imp", "amm_imp_chiave"):
                st.session_state.pop(kk, None)
            st.rerun()
        if c2.button("✖ Scarta", key=k + "_no", width="stretch"):
            for kk in ("ca_bozza_in", "amm_imp", "amm_imp_chiave"):
                st.session_state.pop(kk, None)
            st.session_state["ca_giro"] = n + 1
            st.rerun()
    try:
        st.dialog("📖 Documento letto: controlla e conferma", width="large")(_finestra)()
    except TypeError:
        st.dialog("📖 Documento letto: controlla e conferma")(_finestra)()


def _amm_import_esegui(c, n, sorgente, sha, ric, esatto, az, ente, imp_ric, v):
    """Controlla TUTTO prima di archiviare (niente documento archiviato a metà), poi archivia e salva. → messaggio d'errore oppure None."""
    if az == "nuova":
        if not v["descr"].strip():
            return "Scrivi una descrizione."
        if not v["manuale"]:
            rate = []
            for i, (dt, im) in enumerate(v["rate_in"]):
                d_, i_ = amm_parse_data(dt), amm_importo(im)
                if not d_:
                    return f"La scadenza della rata {i + 1} non è una data valida (scrivila così: 15/12/2026)."
                if not i_ or i_ <= 0:
                    return f"L'importo della rata {i + 1} non è valido."
                rate.append((d_, i_))
            if len({x[0] for x in rate}) != len(rate):
                return "Due rate hanno la stessa data: correggi."
        else:
            tot = amm_importo(v["tot"])
            if not tot or tot <= 0:
                return "Scrivi l'importo totale (per esempio 1.200,00)."
            rate = list(zip(amm_genera_scadenze(v["prima"], v["n"], v["mesi"]), amm_ripartisci(tot, v["n"])))
        totale = round(sum(x[1] for x in rate), 2)
        did, msg = _amm_archivia_import(c, n, sorgente, sha, ric, esatto, "Lettera o comunicazione", ente, totale)
        nuova = amm_crea_spesa_da_rate(v["descr"], v["cat"], rate, v["adm"], "", v["giorni"])
        nuova["allegati"] = [did] if did else []
        _amm_salva(lambda cc: cc.setdefault("spese_amm", []).append(nuova), "Amministrazione: spesa da documento " + v["descr"].strip()[:30])
        st.session_state["messaggio"] = f"✅ Spesa «{v['descr'].strip()}» creata con {len(rate)} rata/e. " + msg
        return None
    if az == "ricevuta":
        if not v:
            return "Scegli la rata a cui collegare la ricevuta."
        imp = amm_importo(v["imp"])
        if not imp or imp <= 0:
            return "Scrivi un importo valido."
        sp_id, r_id = v["scelta"].split("|")
        sp = _amm_trova(c, "spese_amm", sp_id)
        r = next((x for x in (sp or {}).get("rate", []) if x.get("id") == r_id), None)
        if not r:
            return "Rata non trovata."
        if imp > amm_residuo(r) + 0.004:
            return f"L'importo supera quello che resta da pagare ({amm_euro(amm_residuo(r))})."
        did, msg = _amm_archivia_import(c, n, sorgente, sha, ric, esatto, "Ricevuta di pagamento", ente, imp)
        esito = {}

        def _fn(cc):
            x = _amm_trova(cc, "spese_amm", sp_id)
            esito["r"] = amm_registra_pagamento(x, r_id, imp, v["data"].isoformat(), v["modo"], "ricevuta allegata", did or "") if x else (False, "Spesa non trovata.")
            if x and esito["r"][0] and did:
                x.setdefault("allegati", [])
                if did not in x["allegati"]:
                    x["allegati"].append(did)
        _amm_salva(_fn, "Amministrazione: pagamento da ricevuta")
        if not esito["r"][0]:
            return esito["r"][1]
        st.session_state["messaggio"] = f"✅ Pagamento di {amm_euro(imp)} registrato sulla rata {r['n']} di «{sp['descrizione']}». " + msg
        return None
    if az == "allega":
        did, msg = _amm_archivia_import(c, n, sorgente, sha, ric, esatto, "Lettera o comunicazione" if not esatto else None, ente, None)

        def _fn(cc):
            x = _amm_trova(cc, "spese_amm", v["spesa"])
            if x and did and did not in x.setdefault("allegati", []):
                x["allegati"].append(did)
                _amm_log(x, "Documento allegato (importato)")
        _amm_salva(_fn, "Amministrazione: documento allegato")
        st.session_state["messaggio"] = "✅ Documento allegato alla spesa. " + msg
        return None
    did, msg = _amm_archivia_import(c, n, sorgente, sha, ric, esatto)
    st.session_state["messaggio"] = msg
    return None


# le rate dell'amministrazione entrano anche tra le scadenze di Casa (avvisi in cima, conteggio sul pulsante della Home): ca_scadenze è «avvolta», l'originale non cambia
if "_amm_ca_scadenze_prima" not in globals() and "ca_scadenze" in globals():
    _amm_ca_scadenze_prima = ca_scadenze


def ca_scadenze(c, oggi_, giorni=60):                                               # noqa: F811
    sc = _amm_ca_scadenze_prima(c, oggi_, giorni)
    try:
        sc["spese"] = amm_rate_vicine([x for x in c.get("spese_amm", []) if isinstance(x, dict)], oggi_)
    except Exception:
        sc["spese"] = []
    return sc
