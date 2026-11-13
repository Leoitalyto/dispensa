# -*- coding: utf-8 -*-
"""SALUTE · ALLARMI SUL CALENDARIO DEL TELEFONO: terapie e visite in un file .ics.

Il file si apre con il Calendario del telefono (Google Calendar o quello di Samsung ecc.): ogni terapia diventa un evento RIPETUTO all'ora giusta con un allarme,
ogni visita un evento con due allarmi (la sera prima alle 20 e poco prima). Gli allarmi suonano ANCHE con l'app, Chrome e internet chiusi: sono gratuiti.
• Le terapie a intervalli (ogni 15 giorni, ogni 2 settimane…) usano la ripetizione giusta; «ogni N mesi» si scrive come elenco delle prossime 12 volte (il calendario non sa fare «il 31»).
• Se la terapia ha una fine o un numero di volte, il calendario si ferma da solo.
• Gli «uid» sono stabili: importando di nuovo il file gli eventi si AGGIORNANO, non si duplicano. Se però togli o sospendi una terapia, gli eventi già nel calendario vanno
  cancellati a mano dal Calendario (il file non può cancellarli).
Le terapie sospese o già finite e le visite passate non entrano nel file. Dati e regole non cambiano: questo modulo legge soltanto."""
import hashlib as _cal_hl
from datetime import date, datetime, timedelta, timezone

import streamlit as st

_CAL_GIORNI = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _cal_testo(t):
    return str(t or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _cal_riga(riga):
    """Riga spezzata a 75 byte come richiede lo standard."""
    b, out = riga.encode("utf-8"), []
    while len(b) > 75:
        taglio = 75
        while taglio > 0 and (b[taglio] & 0xC0) == 0x80:
            taglio -= 1
        out.append(b[:taglio].decode("utf-8"))
        b = b" " + b[taglio:]
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)


def _cal_data(iso):
    try:
        return date.fromisoformat(str(iso)[:10]) if iso else None
    except ValueError:
        return None


def _cal_ora(txt):
    """'08:30' -> (8, 30) oppure None."""
    try:
        h, m = str(txt).strip().split(":")[:2]
        h, m = int(h), int(m)
        return (h, m) if 0 <= h < 24 and 0 <= m < 60 else None
    except (ValueError, TypeError):
        return None


def _cal_uid(*parti):
    return _cal_hl.sha1("|".join(str(p) for p in parti).encode("utf-8")).hexdigest()[:24] + "@dispensa"


def _cal_allarme(titolo, minuti_dopo_inizio):
    """Un allarme: minuti_dopo_inizio negativo = prima dell'inizio dell'evento."""
    m = int(minuti_dopo_inizio)
    return ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_cal_testo(titolo)}", f"TRIGGER:{'-' if m < 0 else ''}PT{abs(m)}M", "END:VALARM"]


def _cal_intestazione(nome):
    return ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//La nostra dispensa//Salute//IT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_cal_testo(nome)}"]


def _cal_chiudi(righe):
    righe.append("END:VCALENDAR")
    return ("\r\n".join(_cal_riga(r) for r in righe) + "\r\n").encode("utf-8")


def _cal_primo_giorno_settimana(t, da):
    """Il primo giorno >= `da` in cui la terapia (a giorni della settimana) si prende."""
    giorni = [g for g in (t.get("giorni") or []) if isinstance(g, int) and 0 <= g < 7]
    if not giorni:
        return None
    d = da
    for _ in range(8):
        if d.weekday() in giorni:
            return d
        d += timedelta(days=1)
    return None


def cal_eventi_terapia(t, oggi_, ora_dopo_min=0):
    """Le righe VEVENT di UNA terapia (una per ogni orario). Lista vuota se la terapia non è attiva, è finita o non si sa quando si prende."""
    if not isinstance(t, dict) or t.get("stato", "attiva") != "attiva":
        return []
    inizio = _cal_data(t.get("inizio")) or oggi_
    fine = _cal_data(t.get("fine"))
    if fine and fine < oggi_:
        return []
    orari = sorted({o for o in (_cal_ora(x) for x in (t.get("orari") or [])) if o})
    if not orari:
        return []
    nome = str(t.get("nome_med") or "Medicinale")
    dose = str(t.get("quantita") or "").strip()
    titolo = f"💊 {nome}" + (f" – {dose}" if dose else "")
    desc = "Terapia dalla app «La nostra dispensa»." + (f" Note: {t['note']}" if t.get("note") else "")
    ora_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    iv = ter_intervallo(t) if "ter_intervallo" in globals() else None
    righe = []
    for (h, m) in orari:
        hhmm = f"{h:02d}{m:02d}00"
        base = ["BEGIN:VEVENT", f"DTSTAMP:{ora_stamp}", f"SUMMARY:{_cal_testo(titolo)}", f"DESCRIPTION:{_cal_testo(desc)}", "DURATION:PT15M", "TRANSP:TRANSPARENT"]
        fine_rr = f";UNTIL={fine.strftime('%Y%m%d')}T235959" if fine else ""
        if iv is None:                                                                   # giorni della settimana
            primo = _cal_primo_giorno_settimana(t, max(inizio, oggi_))
            if primo is None:
                continue
            giorni = ",".join(_CAL_GIORNI[g] for g in sorted(set(t.get("giorni"))) if isinstance(g, int) and 0 <= g < 7)
            righe += base + [f"UID:{_cal_uid(t.get('id'), h, m)}", f"DTSTART:{primo.strftime('%Y%m%d')}T{hhmm}", f"RRULE:FREQ=WEEKLY;BYDAY={giorni}{fine_rr}"]
            righe += _cal_allarme(titolo, ora_dopo_min) + ["END:VEVENT"]
        elif iv["tipo"] in ("giorni", "settimane"):
            try:
                volte = int(t.get("volte") or 0)
            except (TypeError, ValueError):
                volte = 0
            if volte > 0:
                fine_rr = f";COUNT={volte}"
            freq = "DAILY" if iv["tipo"] == "giorni" else "WEEKLY"
            righe += base + [f"UID:{_cal_uid(t.get('id'), h, m)}", f"DTSTART:{inizio.strftime('%Y%m%d')}T{hhmm}", f"RRULE:FREQ={freq};INTERVAL={iv['ogni']}{fine_rr}"]
            righe += _cal_allarme(titolo, ora_dopo_min) + ["END:VEVENT"]
        else:                                                                            # ogni N mesi: elenco delle prossime volte (max 12)
            date_ = ter_prossime(t, max(inizio, oggi_), 12) if "ter_prossime" in globals() else []
            for d in date_:
                righe += base + [f"UID:{_cal_uid(t.get('id'), h, m, d.isoformat())}", f"DTSTART:{d.strftime('%Y%m%d')}T{hhmm}"]
                righe += _cal_allarme(titolo, ora_dopo_min) + ["END:VEVENT"]
    return righe


def cal_ics_terapie(f, pid, nome_persona, oggi_, ora_dopo_min=0):
    """(file .ics in byte, numero di terapie incluse)."""
    righe, n = _cal_intestazione(f"Terapie – {nome_persona}"), 0
    for t in f.get("terapie", []):
        if t.get("profilo", "p0") != pid:
            continue
        ev = cal_eventi_terapia(t, oggi_, ora_dopo_min)
        if ev:
            righe += ev
            n += 1
    return _cal_chiudi(righe), n


def cal_eventi_visita(v, oggi_, nome_persona=""):
    """Gli eventi di una visita futura: il giorno (con ora se c'è) e l'eventuale «prossimo controllo». Con ora: allarmi la sera prima alle 20:00 e 2 ore prima.
    Senza ora: evento di tutto il giorno, allarmi la sera prima alle 20:00 e la mattina alle 8:00."""
    righe, ora_stamp = [], datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cat = str(v.get("categoria") or "Visita")
    chi = f" – {nome_persona}" if nome_persona else ""
    desc = " · ".join(x for x in (f"Medico: {v['medico']}" if v.get("medico") else "", f"Motivo: {v['motivo']}" if v.get("motivo") else "", v.get("note") or "") if x)
    d = _cal_data(v.get("data"))
    if d and d >= oggi_:
        titolo = f"🩺 {cat}{chi}"
        hm = _cal_ora(v.get("ora"))
        ev = ["BEGIN:VEVENT", f"UID:{_cal_uid('visita', v.get('id'), 'data')}", f"DTSTAMP:{ora_stamp}", f"SUMMARY:{_cal_testo(titolo)}"]
        if desc:
            ev.append(f"DESCRIPTION:{_cal_testo(desc)}")
        if hm:
            ev += [f"DTSTART:{d.strftime('%Y%m%d')}T{hm[0]:02d}{hm[1]:02d}00", "DURATION:PT1H"]
            # la sera prima alle 20:00 = 4 ore + (ora della visita) prima dell'inizio
            ev += _cal_allarme(titolo, -(24 * 60 - 20 * 60 + hm[0] * 60 + hm[1])) + _cal_allarme(titolo, -120)
        else:
            ev += [f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}"]
            ev += _cal_allarme(titolo, -4 * 60) + _cal_allarme(titolo, 8 * 60)
        ev += ["TRANSP:TRANSPARENT", "END:VEVENT"]
        righe += ev
    p = _cal_data(v.get("prossimo"))
    if p and p >= oggi_ and p != d:
        titolo = f"🔁 Controllo: {cat}{chi}"
        righe += ["BEGIN:VEVENT", f"UID:{_cal_uid('visita', v.get('id'), 'prossimo')}", f"DTSTAMP:{ora_stamp}", f"SUMMARY:{_cal_testo(titolo)}",
                  f"DTSTART;VALUE=DATE:{p.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(p + timedelta(days=1)).strftime('%Y%m%d')}", "TRANSP:TRANSPARENT"]
        righe += _cal_allarme(titolo, -4 * 60) + _cal_allarme(titolo, 8 * 60) + ["END:VEVENT"]
    return righe


def cal_ics_visite(f, pid, nome_persona, oggi_):
    """(file .ics in byte, numero di eventi)."""
    righe, n = _cal_intestazione(f"Visite – {nome_persona}"), 0
    for v in f.get("visite", []):
        if v.get("profilo", "p0") != pid:
            continue
        ev = cal_eventi_visita(v, oggi_, "")
        n += sum(1 for r in ev if r == "BEGIN:VEVENT")
        righe += ev
    return _cal_chiudi(righe), n


def cal_pannello(f, pid, nomi, oggi_, cosa):
    """Il riquadro «📅 Allarmi sul Calendario» con il pulsante di scarico. cosa = 'terapie' | 'visite'."""
    nome = (nomi or {}).get(pid, "") if isinstance(nomi, dict) else ""
    if cosa == "terapie":
        dati, n = cal_ics_terapie(f, pid, nome or "Salute", oggi_)
        vuoto = "Non c'è nessuna terapia attiva da mettere nel Calendario."
        pulsante, nomefile = f"📅 Scarica gli allarmi di {n} terapi{'a' if n == 1 else 'e'} (.ics)", "terapie.ics"
    else:
        dati, n = cal_ics_visite(f, pid, nome or "Salute", oggi_)
        vuoto = "Non ci sono visite future da mettere nel Calendario."
        pulsante, nomefile = f"📅 Scarica gli allarmi di {n} appuntament{'o' if n == 1 else 'i'} (.ics)", "visite.ics"
    with st.expander("📅 Allarmi sul Calendario del telefono", expanded=False):
        if not n:
            st.caption(vuoto)
            return
        if cosa == "terapie":
            st.caption("Ogni terapia diventa un evento ripetuto all'ora giusta, con allarme. Suona anche con l'app chiusa.")
        else:
            st.caption("Ogni visita ha due allarmi: la sera prima alle 20:00 e poco prima (2 ore prima, o alle 8:00 se non c'è l'ora).")
        st.download_button(pulsante, dati, file_name=nomefile, mime="text/calendar", key=f"cal_ics_{cosa}_{pid}", width="stretch")
        st.caption("Aprilo dalle notifiche di Chrome o da «File»: il telefono chiede in quale calendario metterlo. Se importi di nuovo lo stesso file gli eventi si aggiornano, non si duplicano. "
                   "Se sospendi o elimini una terapia, cancella a mano i suoi eventi dal Calendario.")


# le schede Terapie e Visite mostrano il riquadro in fondo (le schede originali non si toccano: si «avvolgono»)
if "_cal_tab_terapie_prima" not in globals() and "_fa_tab_terapie" in globals():
    _cal_tab_terapie_prima = _fa_tab_terapie
    _cal_tab_visite_prima = _fa_tab_visite

    def _fa_tab_terapie(f, pid, nomi, oggi_):                                                # noqa: F811
        r = _cal_tab_terapie_prima(f, pid, nomi, oggi_)
        try:
            cal_pannello(f, pid, nomi, oggi_, "terapie")
        except Exception as e:                                                               # un problema qui non deve rompere la scheda
            st.caption(f"Gli allarmi sul Calendario non sono disponibili adesso ({type(e).__name__}).")
        return r

    def _fa_tab_visite(f, pid, nomi, oggi_):                                                 # noqa: F811
        r = _cal_tab_visite_prima(f, pid, nomi, oggi_)
        try:
            cal_pannello(f, pid, nomi, oggi_, "visite")
        except Exception as e:
            st.caption(f"Gli allarmi sul Calendario non sono disponibili adesso ({type(e).__name__}).")
        return r
