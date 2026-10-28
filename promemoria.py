#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Promemoria di scadenza per "La nostra dispensa" e per la Farmacia: Telegram, email e SMS.

Gira ogni mattina su GitHub Actions dentro il repository dei dati (dispensa-dati).
Legge i file dispense/*.json e avvisa ogni persona con i canali che ha scelto nell'app.
Novità: avvisi per le PRESCRIZIONI in scadenza (14, 7, 3, 1 giorno e il giorno stesso) e, per il capo famiglia, il RIEPILOGO della famiglia
ogni mattina e l'avviso se una persona non registra una dose entro 90 minuti (si attivano nell'app, in «Scegli come ricevere gli avvisi»).
Uso:  python promemoria.py            -> invia i promemoria di oggi
      python promemoria.py --dosi     -> promemoria delle assunzioni programmate (ogni mezz'ora)
      python promemoria.py --prova    -> invia solo un messaggio di prova su tutti i canali scelti
      python promemoria.py --dry      -> non invia nulla, mostra i messaggi a schermo

Chiavi segrete (GitHub -> Settings -> Secrets and variables -> Actions), ognuna serve solo se usi quel canale:
  Telegram: TELEGRAM_TOKEN
  Email:    EMAIL_USER, EMAIL_PASSWORD  (facoltativi: EMAIL_SMTP, EMAIL_PORT; di base Gmail)
  SMS:      TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM
"""
import base64
import calendar
import glob
import json
import os
import smtplib
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

SOGLIE = (60, 30, 14, 7, 1, 0)          # giorni mancanti alla scadenza in cui arriva un messaggio
SOGLIE_PRESC = (14, 7, 3, 1, 0)         # per le prescrizioni (ricette), che durano poco
RITARDO_DOSE_MIN = 90                   # dopo quanti minuti avvisare il capo famiglia di una dose non registrata
DRY = "--dry" in sys.argv
PROVA = "--prova" in sys.argv
DOSI = "--dosi" in sys.argv
E = os.environ.get


def leggi(percorso):
    try:
        with open(percorso, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def data_di(iso):
    try:
        return date.fromisoformat(iso) if iso else None
    except ValueError:
        return None


def quando(giorni):
    if giorni < 0:
        return f"scaduto da {abs(giorni)} giorni"
    return "scade OGGI" if giorni == 0 else "scade domani" if giorni == 1 else f"scade tra {giorni} giorni"


def voci_utente(d):
    """Elenco (icona, nome, scadenza, profilo) di prodotti della dispensa e medicinali."""
    voci = []
    for r in d.get("articoli", []):
        s = data_di(r.get("scadenza"))
        if s:
            voci.append(("🥫", r.get("nome", "Prodotto"), s, None))
    f = d.get("farmacia") or {}
    profili = {p["id"]: p.get("nome", "") for p in f.get("profili", [])}
    for m in f.get("medicinali", []):
        s = data_di(m.get("scadenza"))
        if s:
            voci.append(("💊", m.get("nome", "Medicinale"), s, profili.get(m.get("profilo", "p0"), "")))
    return voci


def meno_mesi(d, n):
    """La data n mesi prima di d (il giorno si adatta se il mese è più corto)."""
    m = d.month - 1 - n
    anno, mese = d.year + m // 12, m % 12 + 1
    return date(anno, mese, min(d.day, calendar.monthrange(anno, mese)[1]))


def documenti_utente(d):
    """Documenti con scadenza: (tipo, profilo, scadenza)."""
    f = d.get("farmacia") or {}
    profili = {p["id"]: p.get("nome", "") for p in f.get("profili", [])}
    risultato = []
    for x in f.get("documenti", []):
        s = data_di(x.get("scadenza"))
        if s and not x.get("senza_scadenza"):
            risultato.append((x.get("tipo", "Documento"), profili.get(x.get("profilo", "p0"), ""), s))
    return risultato


def prescrizioni_utente(d):
    """Prescrizioni ancora da usare con una data di validità: (tipo, cosa è prescritto, profilo, valida fino al)."""
    f = d.get("farmacia") or {}
    profili = {p["id"]: p.get("nome", "") for p in f.get("profili", [])}
    risultato = []
    for x in f.get("prescrizioni", []):
        s = data_di(x.get("valida_fino"))
        if s and x.get("stato") != "Usata":
            risultato.append((x.get("tipo", "Prescrizione"), x.get("prescritto", ""), profili.get(x.get("profilo", "p0"), ""), s))
    return risultato


def raccogli(d, oggi):
    in_soglia, scaduti = [], []
    for icona, nome, s, profilo in voci_utente(d):
        g = (s - oggi).days
        if g in SOGLIE:
            in_soglia.append((g, icona, nome, s, profilo))
        elif g < 0 and oggi.weekday() == 0:          # i già scaduti: un promemoria ogni lunedì
            scaduti.append((g, icona, nome, s, profilo))
    for tipo, cosa, profilo, s in prescrizioni_utente(d):          # prescrizioni: icona 📝
        g = (s - oggi).days
        nome = f"Prescrizione {tipo.lower()}" + (f" ({cosa[:40]})" if cosa else "")
        if g in SOGLIE_PRESC:
            in_soglia.append((g, "📝", nome, s, profilo))
        elif g < 0 and oggi.weekday() == 0:
            scaduti.append((g, "📝", nome, s, profilo))
    docs = []                                   # (livello, tipo, profilo, scadenza, giorni): 1 = sei mesi prima, 2 = tre mesi prima
    for tipo, profilo, s in documenti_utente(d):
        g = (s - oggi).days
        if meno_mesi(s, 6) == oggi:
            docs.append((1, tipo, profilo, s, g))
        elif meno_mesi(s, 3) == oggi:
            docs.append((2, tipo, profilo, s, g))
        elif g < 0 and oggi.weekday() == 0:      # già scaduti: un promemoria ogni lunedì
            scaduti.append((g, "📄", tipo, s, profilo))
    return sorted(in_soglia, key=lambda x: x[0]), sorted(scaduti, key=lambda x: x[0]), docs


def testo_lungo(d, oggi, in_soglia, scaduti, docs=()):
    """Per Telegram ed email."""
    privacy = bool(d.get("telegram_privacy"))
    righe = [f"🔔 Promemoria scadenze del {oggi.strftime('%d/%m/%Y')}"]

    def blocco(titolo, elenco):
        if not elenco:
            return
        righe.extend(["", titolo])
        med = [x for x in elenco if x[1] == "💊"]
        for g, icona, nome, s, profilo in elenco:
            if icona == "💊" and privacy:
                continue                              # in modalità privacy niente nomi di medicinali
            if icona == "📝" and privacy:
                nome = nome.split(" (")[0]            # niente contenuto della prescrizione
            extra = f" ({profilo})" if profilo else ""
            righe.append(f"• {icona} {nome}{extra} – {quando(g)} ({s.strftime('%d/%m/%Y')})")
        if med and privacy:
            righe.append(("• 💊 1 medicinale" if len(med) == 1 else f"• 💊 {len(med)} medicinali")
                         + ": apri la Farmacia per i dettagli")
    secondi = [x for x in docs if x[0] == 2]
    primi = [x for x in docs if x[0] == 1]
    if secondi:                                  # secondo avviso: più insistente
        righe.extend(["", "🚨🚨 DOCUMENTI – SECONDO AVVISO: SCADONO TRA 3 MESI 🚨🚨"])
        righe.extend(f"• 🚨 {tipo.upper()}" + (f" ({profilo})" if profilo else "") + f" – SCADE IL {s.strftime('%d/%m/%Y')}: RINNOVALO SUBITO"
                     for _, tipo, profilo, s, g in secondi)
    if primi:
        righe.extend(["", "📄 Documenti – primo avviso: scadono tra 6 mesi"])
        righe.extend(f"• 📄 {tipo}" + (f" ({profilo})" if profilo else "") + f" – scade il {s.strftime('%d/%m/%Y')}"
                     for _, tipo, profilo, s, g in primi)
    blocco("⚠️ In scadenza:", in_soglia)
    blocco("⚫ Già scaduti (da buttare o controllare):", scaduti)
    return "\n".join(righe)


def testo_sms(oggi, in_soglia, scaduti, docs=()):
    """Per gli SMS: breve e senza nomi di medicinali (un SMS non è un canale riservato)."""
    def pl(n, uno, molti):
        return f"{n} {uno if n == 1 else molti}"
    prod = sum(1 for x in in_soglia if x[1] == "🥫")
    med = sum(1 for x in in_soglia if x[1] == "💊")
    pre = sum(1 for x in in_soglia if x[1] == "📝")
    parti = [x for x in (pl(prod, "prodotto", "prodotti") if prod else "",
                         pl(med, "medicinale", "medicinali") if med else "",
                         pl(pre, "prescrizione", "prescrizioni") if pre else "") if x]
    n_doc2 = sum(1 for x in docs if x[0] == 2)
    n_doc1 = sum(1 for x in docs if x[0] == 1)
    if n_doc2:
        parti.append("URGENTE " + pl(n_doc2, "documento", "documenti") + " in scadenza tra 3 mesi")
    if n_doc1:
        parti.append(pl(n_doc1, "documento", "documenti") + " in scadenza tra 6 mesi")
    testo = f"Dispensa {oggi.strftime('%d/%m')}: " + (" e ".join(parti) + (" in scadenza" if (prod or med or pre) else "") if parti else "nessuna scadenza vicina")
    if scaduti:
        testo += f"; {pl(len(scaduti), 'già scaduto', 'già scaduti')}"
    return testo + ". Apri l'app per i dettagli."


# ---------------------------------------------------------------- invio
def invia_telegram(chat, testo):
    token = E("TELEGRAM_TOKEN", "").strip()
    if DRY:
        print(f"--- TELEGRAM a {chat} ---\n{testo}\n")
        return "ok"
    if not token:
        return "saltato: manca TELEGRAM_TOKEN"
    for i in range(0, len(testo), 3900):                 # Telegram accetta al massimo ~4096 caratteri
        dati = urllib.parse.urlencode({"chat_id": chat, "text": testo[i:i + 3900]}).encode()
        try:
            with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", dati, timeout=20) as r:
                if r.status != 200:
                    return f"errore: Telegram risponde {r.status}"
        except Exception as e:
            return f"errore: {type(e).__name__}"
    return "ok"


def invia_email(indirizzo, oggetto, testo):
    utente, password = E("EMAIL_USER", "").strip(), E("EMAIL_PASSWORD", "").strip()
    if DRY:
        print(f"--- EMAIL a {indirizzo} · oggetto: {oggetto} ---\n{testo}\n")
        return "ok"
    if not utente or not password:
        return "saltato: mancano EMAIL_USER o EMAIL_PASSWORD"
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = oggetto, utente, indirizzo
    msg.set_content(testo)
    try:
        with smtplib.SMTP_SSL(E("EMAIL_SMTP", "smtp.gmail.com"), int(E("EMAIL_PORT", "465") or 465),
                              context=ssl.create_default_context(), timeout=30) as s:
            s.login(utente, password)
            s.send_message(msg)
    except Exception as e:
        return f"errore: {type(e).__name__}"
    return "ok"


def invia_sms(numero, testo):
    sid, token, mittente = E("TWILIO_SID", "").strip(), E("TWILIO_TOKEN", "").strip(), E("TWILIO_FROM", "").strip()
    if DRY:
        print(f"--- SMS a {numero} ---\n{testo}\n")
        return "ok"
    if not (sid and token and mittente):
        return "saltato: mancano TWILIO_SID, TWILIO_TOKEN o TWILIO_FROM"
    richiesta = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        urllib.parse.urlencode({"To": numero, "From": mittente, "Body": testo}).encode(),
        {"Authorization": "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode()})
    try:
        with urllib.request.urlopen(richiesta, timeout=20) as r:
            if r.status not in (200, 201):
                return f"errore: Twilio risponde {r.status}"
    except Exception as e:
        return f"errore: {type(e).__name__}"
    return "ok"


def adesso_roma():
    """Ora attuale in Italia (PM_ORA serve solo per le prove)."""
    if E("PM_ORA"):
        return datetime.fromisoformat(E("PM_ORA"))
    return datetime.now(ZoneInfo("Europe/Rome")).replace(tzinfo=None)


def dosi_nella_fascia(d, adesso):
    """Assunzioni previste nella mezz'ora corrente (00-29 o 30-59) e non ancora segnate come prese."""
    ini = adesso.replace(minute=0 if adesso.minute < 30 else 30, second=0, microsecond=0)
    fin = ini + timedelta(minutes=30)
    f = d.get("farmacia") or {}
    profili = {p["id"]: p.get("nome", "") for p in f.get("profili", [])}
    nomi_med = {m["id"]: m.get("nome", "") for m in f.get("medicinali", [])}
    registro = f.get("registro") or {}
    giorno = ini.date()
    risultato = []
    for t in f.get("terapie", []):
        if giorno.weekday() not in t.get("giorni", []):
            continue
        da, a = data_di(t.get("inizio")), data_di(t.get("fine"))
        if (da and giorno < da) or (a and giorno > a):
            continue
        if t.get("stato") == "sospesa":
            dal = data_di(t.get("stato_dal"))
            if dal is None or giorno >= dal:
                continue
        for ora in t.get("orari", []):
            try:
                momento = datetime.fromisoformat(f"{giorno.isoformat()}T{ora}")
            except ValueError:
                continue
            if not (ini <= momento < fin) or f"{t.get('id')}|{giorno.isoformat()}|{ora}" in registro:
                continue
            risultato.append((ora, nomi_med.get(t.get("med"), t.get("nome_med", "Medicinale")),
                              profili.get(t.get("profilo", "p0"), ""), t.get("quantita", "")))
    return sorted(risultato)


def testo_dosi(d, dosi):
    privacy = bool(d.get("telegram_privacy"))
    righe = [f"⏰ Promemoria terapia – ore {dosi[0][0]}"]
    for ora, nome, profilo, quantita in dosi:
        extra = f" ({profilo})" if profilo else ""
        if privacy:
            righe.append(f"• 💊 Terapia{extra} delle {ora}")
        else:
            righe.append(f"• 💊 {nome}{extra}" + (f" – {quantita}" if quantita else "") + f" – ore {ora}")
    righe.append("")
    righe.append("Quando l'hai presa, segnalala nella Farmacia dell'app (scheda Terapie).")
    return "\n".join(righe)


# ---------------------------------------------------------------- famiglia (solo per il capo famiglia)
def persone_famiglia():
    """Le persone da controllare: tutti i profili del capo famiglia e quelli delle persone con «Parte della famiglia» attivo.
    Ritorna una lista di (nome, farmacia, id profilo, è il primo profilo del capo famiglia)."""
    persone = []
    f_capo = (leggi("dispense/admin.json").get("farmacia") or {})
    for i, p in enumerate(f_capo.get("profili") or [{"id": "p0", "nome": "Io"}]):
        persone.append((p.get("nome", ""), f_capo, p["id"], i == 0))
    for u in leggi("utenti.json").get("utenti", []):
        if not u.get("famiglia") or not u.get("attivo", True):
            continue
        f_u = (leggi(f"dispense/{u.get('id')}.json").get("farmacia") or {})
        for p in f_u.get("profili") or [{"id": "p0", "nome": u.get("nome", "")}]:
            persone.append((p.get("nome", "") or u.get("nome", ""), f_u, p["id"], False))
    return persone


def dosi_del_giorno(f, pid, giorno):
    """Tutte le assunzioni previste in un giorno per un profilo: [(ora, medicinale, registrata?)]."""
    nomi_med = {m["id"]: m.get("nome", "") for m in f.get("medicinali", [])}
    registro = f.get("registro") or {}
    risultato = []
    for t in f.get("terapie", []):
        if t.get("profilo", "p0") != pid or giorno.weekday() not in t.get("giorni", []):
            continue
        da, a = data_di(t.get("inizio")), data_di(t.get("fine"))
        if (da and giorno < da) or (a and giorno > a):
            continue
        if t.get("stato") == "sospesa":
            dal = data_di(t.get("stato_dal"))
            if dal is None or giorno >= dal:
                continue
        for ora in t.get("orari", []):
            risultato.append((ora, nomi_med.get(t.get("med"), t.get("nome_med", "Medicinale")),
                              f"{t.get('id')}|{giorno.isoformat()}|{ora}" in (f.get("registro") or {})))
    return sorted(risultato)


def riepilogo_famiglia(oggi, privacy=False):
    """Il messaggio del mattino per il capo famiglia: per ogni persona le cose da controllare. Ritorna (testo, quante persone hanno qualcosa)."""
    giorni_it = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    blocchi, tranquilli = [], []
    for nome, f, pid, _ in persone_famiglia():
        righe = []
        di = lambda chiave: [x for x in f.get(chiave, []) if x.get("profilo", "p0") == pid]
        for m in di("medicinali"):
            s = data_di(m.get("scadenza"))
            if s and (s - oggi).days <= 30:
                g = (s - oggi).days
                righe.append(("💊", m.get("nome", "Medicinale"), f"{quando(g)} ({s.strftime('%d/%m/%Y')})"))
        for x in di("prescrizioni"):
            s = data_di(x.get("valida_fino"))
            if s and x.get("stato") != "Usata" and (s - oggi).days <= 7:
                g = (s - oggi).days
                righe.append(("📝", f"Prescrizione {str(x.get('tipo', '')).lower()}" + ("" if privacy or not x.get("prescritto") else f" ({x['prescritto'][:40]})"),
                              ("scaduta da " + str(abs(g)) + " giorni" if g < 0 else "scade OGGI" if g == 0 else f"scade tra {g} giorni") + f" ({s.strftime('%d/%m/%Y')})"))
        for v in di("visite"):
            for chiave in ("prossimo", "data"):
                s = data_di(v.get(chiave))
                if s and 0 <= (s - oggi).days <= 7:
                    righe.append(("📅", v.get("categoria", "Visita"), ("OGGI" if s == oggi else "domani" if (s - oggi).days == 1 else f"il {s.strftime('%d/%m/%Y')}")))
                    break
        for v in di("vaccinazioni"):
            s = data_di(v.get("richiamo"))
            if s and -365 <= (s - oggi).days <= 30:
                righe.append(("💉", f"Richiamo {v.get('nome', '')}", f"il {s.strftime('%d/%m/%Y')}"))
        for x in di("documenti"):
            s = data_di(x.get("scadenza"))
            if s and not x.get("senza_scadenza") and (s - oggi).days <= 90:
                righe.append(("📄", x.get("tipo", "Documento"), f"{quando((s - oggi).days)} ({s.strftime('%d/%m/%Y')})"))
        ieri = [x for x in dosi_del_giorno(f, pid, oggi - timedelta(days=1)) if not x[2]]
        if ieri:
            righe.append(("⚠️", "Ieri 1 assunzione non registrata" if len(ieri) == 1 else f"Ieri {len(ieri)} assunzioni non registrate", ""))
        if not righe:
            tranquilli.append(nome)
            continue
        blocco = [f"👤 {nome}"]
        meds = [r for r in righe if r[0] == "💊"]
        for icona, cosa, quando_ in righe:
            if icona == "💊" and privacy:
                continue
            blocco.append(f"• {icona} {cosa}" + (f" – {quando_}" if quando_ else ""))
        if meds and privacy:
            blocco.append(("• 💊 1 medicinale" if len(meds) == 1 else f"• 💊 {len(meds)} medicinali") + ": apri la Farmacia per i dettagli")
        blocchi.append("\n".join(blocco))
    testo = [f"👨‍👩‍👧 Riepilogo famiglia · {giorni_it[oggi.weekday()]} {oggi.strftime('%d/%m/%Y')}", ""] + ["\n\n".join(blocchi)] if blocchi else []
    if tranquilli:
        testo += ["", "✅ Nessun problema per: " + ", ".join(tranquilli)]
    if blocchi:
        testo += ["", "Apri la Farmacia → Controllo famiglia per i dettagli."]
    return "\n".join(testo), len(blocchi)


def dosi_in_ritardo(adesso, privacy=False):
    """Dosi previste 90 minuti fa (la mezz'ora che contiene quell'orario) e ancora non registrate, per le persone della famiglia
    (escluso il primo profilo del capo famiglia, cioè lui)."""
    prima = adesso - timedelta(minutes=RITARDO_DOSE_MIN)
    ini = prima.replace(minute=0 if prima.minute < 30 else 30, second=0, microsecond=0)
    fin = ini + timedelta(minutes=30)
    righe = []
    for nome, f, pid, e_capo in persone_famiglia():
        if e_capo:
            continue
        for ora, med, registrata in dosi_del_giorno(f, pid, ini.date()):
            try:
                momento = datetime.fromisoformat(f"{ini.date().isoformat()}T{ora}")
            except ValueError:
                continue
            if ini <= momento < fin and not registrata:
                righe.append((ora, nome, med))
    if not righe:
        return ""
    testo = ["⏰ Dose non registrata"]
    for ora, nome, med in sorted(righe):
        testo.append(f"• {nome}: la dose delle {ora}" + ("" if privacy else f" ({med})") + " non risulta ancora registrata")
    testo += ["", "Può essersela dimenticata, oppure averla presa senza segnarla."]
    return "\n".join(testo)


def invia_al_capo(d_capo, oggetto, testo, canali=("telegram", "email")):
    """Manda un messaggio al capo famiglia sui suoi canali (solo Telegram ed email: gli SMS non sono riservati). Ritorna [(canale, esito)]."""
    esiti = []
    for canale in canali_di(d_capo):
        if canale == "telegram" and canale in canali and str(d_capo.get("telegram_chat_id") or "").strip():
            esiti.append((canale, invia_telegram(str(d_capo["telegram_chat_id"]).strip(), testo)))
        elif canale == "email" and canale in canali and (d_capo.get("avviso_email") or "").strip():
            esiti.append((canale, invia_email(d_capo["avviso_email"].strip(), oggetto, testo)))
    return esiti


def canali_di(d):
    canali = d.get("avvisi_canali")
    if canali is None:                                    # chi ha solo il Chat ID di Telegram
        canali = ["telegram"] if d.get("telegram_chat_id") else []
    return [c for c in canali if c in ("telegram", "email", "sms")]


def main():
    adesso = adesso_roma()
    oggi = adesso.date()
    bloccati = {u.get("id") for u in leggi("utenti.json").get("utenti", []) if not u.get("attivo", True)}
    ok = errori = saltati = 0

    def registra(uid, canale, esito):
        nonlocal ok, errori, saltati
        print(f"[{uid}] {canale}: {esito}")
        if esito == "ok":
            ok += 1
        elif esito.startswith("saltato"):
            saltati += 1
        else:
            errori += 1

    for percorso in sorted(glob.glob("dispense/*.json")):
        uid = os.path.splitext(os.path.basename(percorso))[0]
        d = leggi(percorso)
        if uid in bloccati:
            continue
        if DOSI and not PROVA:                           # promemoria delle assunzioni: solo Telegram ed email
            if not d.get("avvisi_dosi"):
                continue
            dosi = dosi_nella_fascia(d, adesso)
            if not dosi:
                continue
            testo = testo_dosi(d, dosi)
            for canale in canali_di(d):
                if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                    registra(uid, canale, invia_telegram(str(d["telegram_chat_id"]).strip(), testo))
                elif canale == "email" and (d.get("avviso_email") or "").strip():
                    registra(uid, canale, invia_email(d["avviso_email"].strip(), "Promemoria terapia - La nostra dispensa", testo))
            continue
        in_soglia, scaduti, docs = raccogli(d, oggi)
        if not PROVA and not in_soglia and not scaduti and not docs:
            continue
        for canale in canali_di(d):
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui i promemoria della dispensa e della Farmacia." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti, docs)
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                testo = "Prova riuscita: da oggi ricevi via email i promemoria della dispensa e della Farmacia." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti, docs)
                esito = invia_email(d["avviso_email"].strip(), "Promemoria scadenze - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                testo = "Dispensa: prova riuscita, da oggi ricevi qui gli avvisi di scadenza." if PROVA \
                    else testo_sms(oggi, in_soglia, scaduti, docs)
                esito = invia_sms(d["avviso_sms"].strip(), testo)
            else:
                continue
            registra(uid, canale, esito)
    # il capo famiglia (account «admin»): riepilogo del mattino e dosi non registrate
    d_capo = leggi("dispense/admin.json")
    if "admin" not in bloccati:
        privacy = bool(d_capo.get("telegram_privacy"))
        if PROVA and (d_capo.get("avvisi_famiglia") or d_capo.get("avvisi_famiglia_ritardi")):
            for canale, esito in invia_al_capo(d_capo, "Prova famiglia - La nostra dispensa",
                                               "✅ Prova riuscita: qui arrivano il riepilogo della famiglia e gli avvisi sulle dosi non registrate."):
                registra("admin-famiglia", canale, esito)
        elif DOSI and d_capo.get("avvisi_famiglia_ritardi"):
            testo = dosi_in_ritardo(adesso, privacy)
            if testo:
                for canale, esito in invia_al_capo(d_capo, "Dose non registrata - La nostra dispensa", testo):
                    registra("admin-famiglia", canale, esito)
        elif not DOSI and d_capo.get("avvisi_famiglia"):
            testo, n = riepilogo_famiglia(oggi, privacy)
            if n:
                for canale, esito in invia_al_capo(d_capo, "Riepilogo famiglia - La nostra dispensa", testo):
                    registra("admin-famiglia", canale, esito)
    print(f"Messaggi inviati: {ok}, saltati: {saltati}, errori: {errori}")
    return 1 if errori or (PROVA and saltati) else 0


if __name__ == "__main__":
    sys.exit(main())
