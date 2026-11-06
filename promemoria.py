#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Promemoria di scadenza per "La nostra dispensa" e per Salute: Telegram, email e SMS.

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
  WhatsApp: (gratuito) ogni persona ha la sua chiave personale di CallMeBot, scritta nell'app: non servono segreti qui
"""
import base64
import calendar
import glob
import json
import os
import re
import smtplib
import ssl
import sys
import time
import urllib.error
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
                         + ": apri Salute per i dettagli")
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


def numero_e164(n):
    """+39… da come lo scrive una persona (spazi, 00, cellulare italiano senza prefisso)."""
    n = re.sub(r"[\s.\-()]", "", str(n or ""))
    if n.startswith("00"):
        n = "+" + n[2:]
    if n and not n.startswith("+") and re.fullmatch(r"3\d{8,9}", n):
        n = "+39" + n
    return n


_ULTIMO_WHATSAPP = [0.0]


def _risposta_pulita(corpo):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corpo or "")).strip()[:110]


def invia_whatsapp(numero, chiave, testo):
    """WhatsApp gratuito con CallMeBot (servizio esterno non ufficiale): la chiave la ottiene ogni persona scrivendo al bot.
    Si considera «ok» solo se il servizio risponde che il messaggio è in coda; altrimenti nel registro compare cosa ha risposto davvero.
    Tra un messaggio e l'altro passano alcuni secondi, per non farsi bloccare per eccesso di richieste."""
    numero, chiave = numero_e164(numero), str(chiave or "").strip()
    testo = testo if len(testo) <= 1500 else testo[:1450].rstrip() + "…\n(apri l'app per il resto)"
    if DRY:
        print(f"--- WhatsApp a {numero} ---\n{testo}\n")
        return "ok"
    if not (numero and chiave):
        return "saltato: mancano il numero o la chiave di CallMeBot"
    attesa = 7 - (time.time() - _ULTIMO_WHATSAPP[0])
    if attesa > 0:
        time.sleep(attesa)
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode({"phone": numero, "text": testo, "apikey": chiave})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "DispensaFamiglia/1.0"}), timeout=30) as r:
            corpo = r.read(1200).decode("utf-8", "replace")
            stato = r.status
    except urllib.error.HTTPError as e:
        try:
            corpo = e.read(600).decode("utf-8", "replace")
        except Exception:
            corpo = ""
        _ULTIMO_WHATSAPP[0] = time.time()
        return f"errore: CallMeBot risponde {e.code}: «{_risposta_pulita(corpo)}»"
    except Exception as e:
        _ULTIMO_WHATSAPP[0] = time.time()
        return f"errore: {type(e).__name__}"
    _ULTIMO_WHATSAPP[0] = time.time()
    if stato == 200 and re.search(r"queued|message\s+sent|sent\s+to", corpo, re.I) and not re.search(r"error|invalid|not\s+registered|wrong", corpo, re.I):
        return "ok"
    return f"errore: CallMeBot dice «{_risposta_pulita(corpo)}»"


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
    righe.append("Quando l'hai presa, segnalala in Salute nell'app (scheda Terapie).")
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
            blocco.append(("• 💊 1 medicinale" if len(meds) == 1 else f"• 💊 {len(meds)} medicinali") + ": apri Salute per i dettagli")
        blocchi.append("\n".join(blocco))
    testo = [f"👨‍👩‍👧 Riepilogo famiglia · {giorni_it[oggi.weekday()]} {oggi.strftime('%d/%m/%Y')}", ""] + ["\n\n".join(blocchi)] if blocchi else []
    if tranquilli:
        testo += ["", "✅ Nessun problema per: " + ", ".join(tranquilli)]
    if blocchi:
        testo += ["", "Apri Salute → Controllo famiglia per i dettagli."]
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


def raccogli_famiglia(d_fam, oggi, con_esaurimento=False):
    """La dispensa di famiglia: (in scadenza, già scaduti il lunedì, in esaurimento il lunedì). I prodotti hanno la stessa regola dei giorni della dispensa personale."""
    in_soglia, scaduti, esaurimento = [], [], []
    for r in d_fam.get("articoli", []):
        s = data_di(r.get("scadenza"))
        if not s:
            continue
        g = (s - oggi).days
        voce = (g, "🥫", r.get("nome", "Prodotto"), s, None)
        if g in SOGLIE:
            in_soglia.append(voce)
        elif g < 0 and oggi.weekday() == 0:
            scaduti.append(voce)
    if con_esaurimento and oggi.weekday() == 0:                       # ogni lunedì: prodotti di cui resta una sola unità in tutto
        totali, nomi = {}, {}
        for r in d_fam.get("articoli", []):
            chiave = (r.get("barcode") or "").strip() or (r.get("nome") or "").strip().lower()
            if not chiave:
                continue
            try:
                totali[chiave] = totali.get(chiave, 0.0) + float(r.get("quantita") or 0)
            except (TypeError, ValueError):
                continue
            nomi.setdefault(chiave, r.get("nome", "Prodotto"))
        esaurimento = sorted((nomi[k], q) for k, q in totali.items() if 0 < q <= 1)
    return sorted(in_soglia, key=lambda x: x[0]), sorted(scaduti, key=lambda x: x[0]), esaurimento


def testo_famiglia_dispensa(oggi, in_soglia, scaduti, esaurimento):
    righe = [f"🏠 Dispensa di famiglia – promemoria del {oggi.strftime('%d/%m/%Y')}"]
    if in_soglia:
        righe += ["", "⚠️ In scadenza:"] + [f"• 🥫 {nome} – {quando(g)} ({s.strftime('%d/%m/%Y')})" for g, _, nome, s, _ in in_soglia]
    if scaduti:
        righe += ["", "⚫ Già scaduti (da buttare o controllare):"] + [f"• 🥫 {nome} – {quando(g)} ({s.strftime('%d/%m/%Y')})" for g, _, nome, s, _ in scaduti]
    if esaurimento:
        righe += ["", "📉 In esaurimento (ne resta una sola unità):"] + [f"• {nome}" for nome, _ in esaurimento]
    return "\n".join(righe)


def testo_sms_famiglia(oggi, in_soglia, scaduti, esaurimento):
    n = len(in_soglia) + len(scaduti)
    parti = []
    if n:
        parti.append(f"{n} prodott{'o' if n == 1 else 'i'} in scadenza o scadut{'o' if n == 1 else 'i'}")
    if esaurimento:
        parti.append(f"{len(esaurimento)} in esaurimento")
    return "Dispensa di famiglia: " + ", ".join(parti) + ". Apri l'app per i dettagli."


def membri_famiglia(bloccati):
    """Chi fa parte della dispensa di famiglia: il capo famiglia e gli utenti con «Parte della famiglia» (con i loro dati personali, dove stanno i canali degli avvisi)."""
    risultato = []
    if "admin" not in bloccati:
        risultato.append(("admin", leggi("dispense/admin.json")))
    for u in leggi("utenti.json").get("utenti", []):
        if u.get("famiglia") and u.get("attivo", True) and u.get("id") and u["id"] not in bloccati:
            risultato.append((u["id"], leggi(f"dispense/{u['id']}.json")))
    return risultato


def avvisi_dispensa_famiglia(oggi, bloccati, registra):
    """Gli avvisi della dispensa comune, solo a chi li ha scelti (ognuno li riceve sui suoi canali)."""
    d_fam = leggi("famiglia/dispensa.json")
    if not d_fam.get("articoli") and not PROVA:
        return
    for uid, d in membri_famiglia(bloccati):
        vuole_s, vuole_e = bool(d.get("avvisi_famiglia_dispensa")), bool(d.get("avvisi_famiglia_esaurimento"))
        if not (vuole_s or vuole_e):
            continue
        in_soglia, scaduti, esaurimento = raccogli_famiglia(d_fam, oggi, vuole_e)
        if not vuole_s:
            in_soglia, scaduti = [], []
        if not PROVA and not (in_soglia or scaduti or esaurimento):
            continue
        for canale in canali_di(d):
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui gli avvisi della dispensa di famiglia." if PROVA else testo_famiglia_dispensa(oggi, in_soglia, scaduti, esaurimento)
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                testo = "Prova riuscita: da oggi ricevi via email gli avvisi della dispensa di famiglia." if PROVA else testo_famiglia_dispensa(oggi, in_soglia, scaduti, esaurimento)
                esito = invia_email(d["avviso_email"].strip(), "Dispensa di famiglia - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                testo = "Dispensa di famiglia: prova riuscita." if PROVA else testo_sms_famiglia(oggi, in_soglia, scaduti, esaurimento)
                esito = invia_sms(d["avviso_sms"].strip(), testo)
            elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui gli avvisi della dispensa di famiglia." if PROVA else testo_famiglia_dispensa(oggi, in_soglia, scaduti, esaurimento)
                esito = invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), testo)
            else:
                continue
            registra(f"{uid}-famiglia-dispensa", canale, esito)


def raccogli_casa(d, oggi):
    """Casa: (garanzie in scadenza, manutenzioni in arrivo o in ritardo). Garanzie a 60, 30, 14, 7, 1 giorno e il giorno stesso; manutenzioni a 30, 14, 7, 1, oggi e, se in ritardo, ogni lunedì."""
    casa = d.get("casa") or {}
    beni = {b.get("id"): b.get("nome", "Bene") for b in casa.get("beni", []) if isinstance(b, dict)}
    garanzie, manut = [], []
    for b in casa.get("beni", []):
        s_ = data_di(b.get("garanzia_fino")) if isinstance(b, dict) else None
        if s_ and (s_ - oggi).days in SOGLIE:
            garanzie.append(((s_ - oggi).days, b.get("nome", "Bene"), s_))
    ultime = {}
    for m in sorted([x for x in casa.get("manutenzioni", []) if isinstance(x, dict)], key=lambda x: x.get("data") or ""):
        ultime[(m.get("bene_id"), m.get("tipo"))] = m                  # conta l'ultima di ogni tipo: le vecchie sono già state fatte
    for m in ultime.values():
        s_ = data_di(m.get("prossima"))
        if not s_ or m.get("bene_id") not in beni:
            continue
        g = (s_ - oggi).days
        if g in (30, 14, 7, 1, 0) or (g < 0 and oggi.weekday() == 0):
            manut.append((g, beni[m["bene_id"]], m.get("descrizione") or m.get("tipo") or "Manutenzione", s_))
    return sorted(garanzie, key=lambda x: x[0]), sorted(manut, key=lambda x: x[0])


SOGLIE_BOLLETTE = (7, 3, 1, 0)            # giorni mancanti alla scadenza in cui arriva l'avviso di una bolletta da pagare (e, se scaduta, ogni lunedì)


def raccogli_bollette(d, oggi):
    """Bollette, fatture e polizze di Casa NON ancora pagate (né «pagata il», né ricevuta collegata): [(giorni, «Luce · Octopus Energy», importo, scadenza)]."""
    casa = d.get("casa") or {}
    docs = [x for x in casa.get("documenti", []) if isinstance(x, dict)]
    pagate = {x.get("collegato_a") for x in docs if x.get("collegato_a")}
    out = []
    for x in docs:
        if x.get("tipo") not in ("Bolletta o fattura", "Polizza assicurativa") or x.get("pagata_il") or x.get("id") in pagate:
            continue
        s_ = data_di(x.get("scadenza_doc"))
        if not s_:
            continue
        g = (s_ - oggi).days
        # prima: 7, 3, 1 giorno e il giorno stesso. Dopo la scadenza: ogni giorno per i primi 30 giorni, poi ogni lunedì, fino a un anno.
        if g in SOGLIE_BOLLETTE or (-30 <= g < 0) or (-365 <= g < -30 and oggi.weekday() == 0):
            nome = " · ".join(v for v in ((x.get("argomento") if x.get("argomento") not in (None, "", "Altro") else ""), x.get("ente") or "") if v) or (x.get("titolo") or "Bolletta")
            out.append((g, nome, x.get("importo") or "", s_))
    return sorted(out, key=lambda t: t[0])


def _euro(v):
    try:
        return "€ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return ""


def testo_casa(oggi, garanzie, manut, bollette=()):
    righe = [f"🏡 Casa – promemoria del {oggi.strftime('%d/%m/%Y')}"]
    if bollette:
        righe += ["", "💶 Bollette da pagare:"] + [f"• {nome}" + (f" ({_euro(imp)})" if _euro(imp) else "") + f" – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, imp, s_ in bollette]
    if garanzie:
        righe += ["", "🛡️ Garanzie in scadenza:"] + [f"• {nome} – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, s_ in garanzie]
    if manut:
        righe += ["", "🔧 Manutenzioni:"] + [f"• {nome}: {voce} – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, voce, s_ in manut]
    return "\n".join(righe)


def testo_sms_casa(oggi, garanzie, manut, bollette=()):
    parti = []
    if bollette:
        parti.append(f"{len(bollette)} bollett{'a' if len(bollette) == 1 else 'e'} da pagare")
    if garanzie:
        parti.append(f"{len(garanzie)} garanzi{'a' if len(garanzie) == 1 else 'e'} in scadenza")
    if manut:
        parti.append(f"{len(manut)} manutenzion{'e' if len(manut) == 1 else 'i'} da fare")
    return "Casa: " + ", ".join(parti) + ". Apri l'app per i dettagli."


def utenti_attivi(bloccati):
    """Tutte le persone con un account attivo (capo famiglia compreso) con i loro dati personali."""
    risultato = []
    if "admin" not in bloccati:
        risultato.append(("admin", leggi("dispense/admin.json")))
    for u in leggi("utenti.json").get("utenti", []):
        if u.get("id") and u.get("attivo", True) and u["id"] not in bloccati:
            risultato.append((u["id"], leggi(f"dispense/{u['id']}.json")))
    return risultato


def avvisi_casa(oggi, bloccati, registra):
    """Garanzie, manutenzioni e BOLLETTE DA PAGARE di Casa, solo a chi ha spuntato «Avvisami anche di Casa», sui canali che ha scelto."""
    for uid, d in utenti_attivi(bloccati):
        # una riga di RIEPILOGO sempre (anche quando non parte niente), per capire dal registro cosa succede
        _docs = [x for x in ((d.get("casa") or {}).get("documenti") or []) if isinstance(x, dict) and x.get("tipo") in ("Bolletta o fattura", "Polizza assicurativa")]
        _pagate = {x.get("collegato_a") for x in ((d.get("casa") or {}).get("documenti") or []) if isinstance(x, dict) and x.get("collegato_a")}
        _non_pagate = [x for x in _docs if not x.get("pagata_il") and x.get("id") not in _pagate]
        _scadute = [x for x in _non_pagate if data_di(x.get("scadenza_doc")) and data_di(x.get("scadenza_doc")) < oggi]
        print(f"[{uid}] Casa: {len(_non_pagate)} bollette non pagate ({len(_scadute)} scadute) · avvisi di Casa: {'SPUNTATI' if d.get('avvisi_casa') else 'NON spuntati'} · canali scelti: {', '.join(canali_di(d)) or 'nessuno'} · oggi {oggi.strftime('%d/%m/%Y')} ({'lunedì' if oggi.weekday() == 0 else 'non è lunedì'}) · da avvisare oggi: {len(raccogli_bollette(d, oggi))}")
        if not d.get("avvisi_casa"):
            if raccogli_bollette(d, oggi) or raccogli_casa(d, oggi) != ([], []):
                print(f"[{uid}] ci sono cose da avvisare in Casa (bollette, garanzie o manutenzioni) ma «Avvisami anche di Casa» NON è spuntato: nessun messaggio. "
                      f"Spuntalo in Salute → Scegli come ricevere gli avvisi.")
            continue
        garanzie, manut = raccogli_casa(d, oggi)
        bollette = raccogli_bollette(d, oggi)
        if not canali_di(d):
            print(f"[{uid}] «Avvisami anche di Casa» è spuntato ma non c'è nessun canale scelto (Telegram, email, WhatsApp, SMS): nessun messaggio.")
            continue
        if not PROVA and not (garanzie or manut or bollette):
            continue
        for canale in canali_di(d):
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui gli avvisi di Casa." if PROVA else testo_casa(oggi, garanzie, manut, bollette)
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                testo = "Prova riuscita: da oggi ricevi via email gli avvisi di Casa." if PROVA else testo_casa(oggi, garanzie, manut, bollette)
                esito = invia_email(d["avviso_email"].strip(), "Casa - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                testo = "Casa: prova riuscita." if PROVA else testo_sms_casa(oggi, garanzie, manut, bollette)
                esito = invia_sms(d["avviso_sms"].strip(), testo)
            elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui gli avvisi di Casa." if PROVA else testo_casa(oggi, garanzie, manut, bollette)
                esito = invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), testo)
            else:
                continue
            registra(f"{uid}-casa", canale, esito)


def _aggiungi_mesi(d, n):
    m = d.month - 1 + int(n)
    a, me = d.year + m // 12, m % 12 + 1
    giorno = min(d.day, [31, 29 if (a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][me - 1])
    return date(a, me, giorno)


def raccogli_controlli(d, oggi):
    """Controlli periodici della Salute (dentista, vista, vaccini…) e scadenze di invalidità ed esenzioni: [(giorni, «Nome · Persona», scadenza)]. Avviso a 30, 7, 1 giorno prima, il giorno stesso, e ogni lunedì se in ritardo (fino a 180 giorni).
    Solo quelli con l'avviso acceso. Il «prossimo» è l'ultimo fatto + ogni quanti mesi."""
    out = []
    for p in ((d.get("farmacia") or {}).get("profili") or []):
        for c in (p.get("controlli") or []):
            if not isinstance(c, dict) or c.get("avvisa") is False:
                continue
            ultimo = data_di(c.get("ultimo"))
            try:
                mesi = int(c.get("ogni_mesi") or 0)
            except (TypeError, ValueError):
                mesi = 0
            prossimo = data_di(c.get("prossimo")) or (_aggiungi_mesi(ultimo, mesi) if (ultimo and mesi > 0) else None)
            if not prossimo:
                continue
            g = (prossimo - oggi).days
            if g in (30, 7, 1, 0) or (-180 <= g < 0 and oggi.weekday() == 0):
                nome = c.get("nome") or "Controllo"
                if len((d.get("farmacia") or {}).get("profili") or []) > 1:
                    nome += f" · {p.get('nome', '')}"
                out.append((g, nome, prossimo))
        # invalidità ed esenzioni: fine validità (se non è permanente) o prossima revisione. Avviso a 60, 30, 7, 1 giorno prima, il giorno stesso, e ogni lunedì se in ritardo (fino a 180 giorni)
        for e in (p.get("esenzioni") or []):
            if not isinstance(e, dict) or e.get("avvisa") is False:
                continue
            fino = None if e.get("permanente") else data_di(e.get("valida_fino"))
            rev = data_di(e.get("revisione"))
            cand = [x for x in (fino, rev) if x]
            if not cand:
                continue
            scad = min(cand)
            g = (scad - oggi).days
            if g in (60, 30, 7, 1, 0) or (-180 <= g < 0 and oggi.weekday() == 0):
                nome = "🪪 " + (e.get("tipo") or "Esenzione") + ((" " + e["codice"]) if e.get("codice") else "") + (" (revisione)" if (rev and scad == rev and not (fino and fino == rev)) else " (scadenza)")
                if len((d.get("farmacia") or {}).get("profili") or []) > 1:
                    nome += f" · {p.get('nome', '')}"
                out.append((g, nome, scad))
    return sorted(out, key=lambda t: t[0])


def testo_controlli(oggi, controlli):
    return "\n".join([f"⏰ Controlli periodici – {oggi.strftime('%d/%m/%Y')}", ""] + [f"• {nome} – " + ("in ritardo di %d giorni" % -g if g < 0 else "OGGI" if g == 0 else "domani" if g == 1 else f"tra {g} giorni") + f" ({s_.strftime('%d/%m/%Y')})" for g, nome, s_ in controlli])


def avvisi_controlli(oggi, bloccati, registra):
    """I controlli periodici, a chiunque abbia dei controlli con l'avviso acceso, sui canali che ha scelto."""
    for uid, d in utenti_attivi(bloccati):
        controlli = raccogli_controlli(d, oggi)
        if not PROVA and not controlli:
            continue
        for canale in canali_di(d):
            testo = "✅ Prova riuscita: da oggi ricevi qui i promemoria dei controlli." if PROVA else testo_controlli(oggi, controlli)
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                esito = invia_email(d["avviso_email"].strip(), "Controlli periodici - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                esito = invia_sms(d["avviso_sms"].strip(), f"Controlli periodici: {len(controlli)} in scadenza. Apri l'app." if not PROVA else "Controlli: prova riuscita.")
            elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                esito = invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), testo)
            else:
                continue
            registra(f"{uid}-controlli", canale, esito)


def canali_di(d):
    canali = d.get("avvisi_canali")
    if canali is None:                                    # chi ha solo il Chat ID di Telegram
        canali = ["telegram"] if d.get("telegram_chat_id") else []
    return [c for c in canali if c in ("telegram", "email", "sms", "whatsapp")]


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
                testo = "✅ Prova riuscita: da oggi ricevi qui i promemoria della dispensa e di Salute." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti, docs)
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                testo = "Prova riuscita: da oggi ricevi via email i promemoria della dispensa e di Salute." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti, docs)
                esito = invia_email(d["avviso_email"].strip(), "Promemoria scadenze - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                testo = "Dispensa: prova riuscita, da oggi ricevi qui gli avvisi di scadenza." if PROVA \
                    else testo_sms(oggi, in_soglia, scaduti, docs)
                esito = invia_sms(d["avviso_sms"].strip(), testo)
            elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui i promemoria della dispensa e di Salute." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti, docs)
                esito = invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), testo)
            else:
                continue
            registra(uid, canale, esito)
    if not DOSI:                                                     # avvisi della dispensa di famiglia e di Casa (ogni mattina, non nei controlli delle dosi)
        avvisi_dispensa_famiglia(oggi, bloccati, registra)
        avvisi_casa(oggi, bloccati, registra)
        avvisi_controlli(oggi, bloccati, registra)
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
