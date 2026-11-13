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
        except urllib.error.HTTPError as e:                          # 403: la persona non ha toccato «Avvia» nel bot; 400: il numero (Chat ID) non è giusto
            return f"errore: Telegram risponde {e.code}"
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


SOGLIE_AMM_DEFAULT = (30, 15, 7, 3, 1, 0)      # se la spesa non ha i suoi giorni di preavviso


def raccogli_spese_amm(d, oggi):
    """Rate dell'AMMINISTRAZIONE di Casa (spese condominiali…) non ancora pagate del tutto: [(giorni, «Descrizione · rata 2/4 · Casa», residuo, scadenza)].
    Avviso nei giorni di preavviso scelti per quella spesa (30, 15, 7, 3, 1 e il giorno stesso se non ne ha scelti); dopo la scadenza ogni giorno per i primi 30 giorni, poi ogni lunedì fino a un anno.
    Le spese con l'avviso spento non compaiono. Con più case il nome della casa è nella riga."""
    casa = d.get("casa") or {}
    case = {x.get("id"): x.get("nome") or "Seconda casa" for x in (casa.get("case") or []) if isinstance(x, dict) and x.get("id")}
    out = []
    for sp in casa.get("spese_amm", []):
        if not isinstance(sp, dict) or sp.get("avvisi_attivi") is False:
            continue
        try:
            giorni = {int(g) for g in (sp.get("avvisi_giorni") or SOGLIE_AMM_DEFAULT)}
        except (TypeError, ValueError):
            giorni = set(SOGLIE_AMM_DEFAULT)
        rate = sorted([r for r in sp.get("rate", []) if isinstance(r, dict)], key=lambda r: r.get("scadenza") or "")
        for k, r in enumerate(rate, 1):
            s_ = data_di(r.get("scadenza"))
            try:
                residuo = round(float(r.get("importo") or 0) - sum(float(x.get("importo") or 0) for x in r.get("pagamenti", []) if isinstance(x, dict)), 2)
            except (TypeError, ValueError):
                continue
            if not s_ or residuo <= 0.004:
                continue
            g = (s_ - oggi).days
            if g in giorni or (-30 <= g < 0) or (-365 <= g < -30 and oggi.weekday() == 0):
                nome = f"{sp.get('descrizione') or 'Spesa'} · rata {r.get('n') or k}/{len(rate)}"
                if case and (sp.get("casa_id") or "") != "":
                    nome += f" · {case.get(sp.get('casa_id'), 'altra casa')}"
                elif case:
                    nome += " · Casa principale"
                out.append((g, nome, residuo, s_))
    return sorted(out, key=lambda t: (t[0], t[1]))


# ----------------------------------------------------------------------------------------------------------------------
# ♻️ RACCOLTA DIFFERENZIATA e 🛋️ INGOMBRANTI (Casa → Amministrazione): promemoria la sera prima, la mattina stessa e un secondo promemoria. Si controllano a ogni giro «ogni mezz'ora»
# (--dosi): un promemoria parte nel giro della mezz'ora che contiene l'ora scelta (come per le assunzioni). Solo a chi ha acceso «Avvisami anche di Casa», sui canali che ha scelto.
# ----------------------------------------------------------------------------------------------------------------------
GIORNI_IT = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
COLORI_EMOJI = {"verde": "🟢", "blu": "🔵", "giallo": "🟡", "rosso": "🔴", "arancione": "🟠", "viola": "🟣", "marrone": "🟤", "grigio": "🔘", "bianco": "⚪", "nero": "⚫"}
COLORI_RIFIUTI_DEFAULT = {"Organico": "marrone", "Indifferenziato": "verde", "Carta": "giallo", "Vetro": "blu", "Plastica": "rosso", "Metalli": "grigio"}


def icona_rifiuto(tipo, colori=None):
    """Il pallino colorato di un tipo di rifiuto: quello scelto nell'app, altrimenti quello di partenza, altrimenti viola."""
    nome = (colori or {}).get(tipo)
    if nome not in COLORI_EMOJI:
        nome = COLORI_RIFIUTI_DEFAULT.get(tipo, "viola")
    return COLORI_EMOJI[nome]
AVVISI_RACCOLTA_DEFAULT = {"attivi": False, "sera": True, "ora_sera": "20:00", "mattina": False, "ora_mattina": "07:00", "secondo": False, "ora_secondo": "21:30", "tipi_spenti": []}


def piano_rifiuti(programma, eccezioni, giorno):
    """(tipi, nota, nessuna raccolta): una variazione per quella data vale più del programma."""
    for e in eccezioni:
        if e.get("data") == giorno.isoformat():
            return ([] if e.get("nessuna") else list(e.get("tipi") or [])), e.get("nota") or "", bool(e.get("nessuna"))
    g = ((programma.get("giorni") or {}).get(str(giorno.weekday())) or {})
    return ([] if g.get("nessuna") else list(g.get("tipi") or [])), g.get("nota") or "", bool(g.get("nessuna"))


def raccogli_rifiuti(d, adesso):
    """[(tipo di promemoria, testo)] da mandare nella mezz'ora corrente (00-29 o 30-59)."""
    casa = d.get("casa") or {}
    programmi = [p for p in casa.get("raccolta", []) if isinstance(p, dict) and p.get("id")]
    if not programmi:
        return []
    eccezioni = [e for e in casa.get("raccolta_ecc", []) if isinstance(e, dict)]
    ingombranti = [m for m in casa.get("ingombranti", []) if isinstance(m, dict) and m.get("prossimo_ritiro")]
    case = {x.get("id"): x.get("nome") or "Seconda casa" for x in (casa.get("case") or []) if isinstance(x, dict) and x.get("id")}
    ini = adesso.replace(minute=0 if adesso.minute < 30 else 30, second=0, microsecond=0)
    fin = ini + timedelta(minutes=30)
    oggi = adesso.date()
    per_casa = {}
    for p in programmi:
        cid = p.get("casa_id") or ""
        if cid not in per_casa or (p.get("attivo") and not per_casa[cid].get("attivo")):
            per_casa[cid] = p
    out = []
    for cid, p in per_casa.items():
        av = {**AVVISI_RACCOLTA_DEFAULT, **(p.get("avvisi") or {})}
        if not av.get("attivi"):
            continue                                                                    # avvisi SPENTI (di partenza): niente messaggi sulla raccolta, nemmeno quelli degli ingombranti
        spenti = set(av.get("tipi_spenti") or [])
        ecc = [e for e in eccezioni if (e.get("programma_id") or p["id"]) == p["id"] and (e.get("casa_id") or "") == cid]
        for chiave, ora_k, giorno, intro in (("sera", "ora_sera", oggi + timedelta(days=1), "Domani"), ("mattina", "ora_mattina", oggi, "Oggi"), ("secondo", "ora_secondo", oggi + timedelta(days=1), "⏰ Promemoria: domani")):
            if not av.get(chiave):
                continue
            try:
                h, m = str(av.get(ora_k)).split(":")
                momento = datetime.combine(oggi, datetime.min.time()).replace(hour=int(h), minute=int(m))
            except ValueError:
                continue
            if not (ini <= momento < fin):
                continue
            tipi, nota, nessuna = piano_rifiuti(p, ecc, giorno)
            tipi = [t for t in tipi if t not in spenti]
            righe = []
            if tipi:
                righe += [f"• {icona_rifiuto(t, p.get('colori'))} {t}" for t in tipi]
                if nota:
                    righe.append(f"({nota})")
            for mi in ingombranti:
                if (mi.get("casa_id") or "") == cid and mi.get("prossimo_ritiro") == giorno.isoformat():
                    righe.append(f"🛋️ Ritiro ingombranti prenotato: {mi.get('nome', '')}" + (f" – {mi['orari']}" if mi.get("orari") else ""))
            if not righe:
                continue
            casa_n = f" ({case.get(cid, 'altra casa') if cid else 'Casa principale'})" if case else ""
            out.append((chiave, f"♻️ Raccolta differenziata{casa_n} – {intro.lower() if chiave == 'secondo' else intro}, {GIORNI_IT[giorno.weekday()]} {giorno.strftime('%d/%m')}:\n" + "\n".join(righe)
                        if chiave != "secondo" else f"♻️ {intro}, {GIORNI_IT[giorno.weekday()]} {giorno.strftime('%d/%m')}{casa_n}, si ritira:\n" + "\n".join(righe) + "\nRicordati di esporre."))
    return out


def avvisi_raccolta(adesso, bloccati, registra):
    for uid, d in utenti_attivi(bloccati):
        if not d.get("avvisi_casa") or not canali_di(d):
            continue
        for chiave, testo in raccogli_rifiuti(d, adesso):
            for canale in canali_di(d):
                if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                    esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
                elif canale == "email" and (d.get("avviso_email") or "").strip():
                    esito = invia_email(d["avviso_email"].strip(), "Raccolta differenziata - La nostra dispensa", testo)
                elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                    esito = invia_sms(d["avviso_sms"].strip(), testo.replace("\n", " ")[:150])
                elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                    esito = invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), testo)
                else:
                    continue
                registra(f"{uid}-raccolta-{chiave}", canale, esito)


def _euro(v):
    try:
        return "€ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return ""


def testo_casa(oggi, garanzie, manut, bollette=(), spese=()):
    righe = [f"🏡 Casa – promemoria del {oggi.strftime('%d/%m/%Y')}"]
    if spese:
        righe += ["", "🏢 Amministrazione – rate da pagare:"] + [f"• {nome}: {_euro(imp)} – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, imp, s_ in spese]
    if bollette:
        righe += ["", "💶 Bollette da pagare:"] + [f"• {nome}" + (f" ({_euro(imp)})" if _euro(imp) else "") + f" – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, imp, s_ in bollette]
    if garanzie:
        righe += ["", "🛡️ Garanzie in scadenza:"] + [f"• {nome} – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, s_ in garanzie]
    if manut:
        righe += ["", "🔧 Manutenzioni:"] + [f"• {nome}: {voce} – {quando(g)} ({s_.strftime('%d/%m/%Y')})" for g, nome, voce, s_ in manut]
    return "\n".join(righe)


def testo_sms_casa(oggi, garanzie, manut, bollette=(), spese=()):
    parti = []
    if spese:
        parti.append(f"{len(spese)} rat{'a' if len(spese) == 1 else 'e'} dell'amministrazione da pagare")
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
        print(f"[{uid}] Casa: {len(raccogli_spese_amm(d, oggi))} rate dell'amministrazione da avvisare oggi · {len(_non_pagate)} bollette non pagate ({len(_scadute)} scadute) · avvisi di Casa: {'SPUNTATI' if d.get('avvisi_casa') else 'NON spuntati'} · canali scelti: {', '.join(canali_di(d)) or 'nessuno'} · oggi {oggi.strftime('%d/%m/%Y')} ({'lunedì' if oggi.weekday() == 0 else 'non è lunedì'}) · da avvisare oggi: {len(raccogli_bollette(d, oggi))}")
        if not d.get("avvisi_casa"):
            if raccogli_bollette(d, oggi) or raccogli_spese_amm(d, oggi) or raccogli_casa(d, oggi) != ([], []):
                print(f"[{uid}] ci sono cose da avvisare in Casa (bollette, garanzie o manutenzioni) ma «Avvisami anche di Casa» NON è spuntato: nessun messaggio. "
                      f"Spuntalo in Salute → Scegli come ricevere gli avvisi.")
            continue
        garanzie, manut = raccogli_casa(d, oggi)
        bollette = raccogli_bollette(d, oggi)
        spese = raccogli_spese_amm(d, oggi)
        if not canali_di(d):
            print(f"[{uid}] «Avvisami anche di Casa» è spuntato ma non c'è nessun canale scelto (Telegram, email, WhatsApp, SMS): nessun messaggio.")
            continue
        if not PROVA and not (garanzie or manut or bollette or spese):
            continue
        for canale in canali_di(d):
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui gli avvisi di Casa." if PROVA else testo_casa(oggi, garanzie, manut, bollette, spese)
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                testo = "Prova riuscita: da oggi ricevi via email gli avvisi di Casa." if PROVA else testo_casa(oggi, garanzie, manut, bollette, spese)
                esito = invia_email(d["avviso_email"].strip(), "Casa - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                testo = "Casa: prova riuscita." if PROVA else testo_sms_casa(oggi, garanzie, manut, bollette, spese)
                esito = invia_sms(d["avviso_sms"].strip(), testo)
            elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui gli avvisi di Casa." if PROVA else testo_casa(oggi, garanzie, manut, bollette, spese)
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
    # AUTO: bollo, assicurazione, revisione, garanzie, tagliando, documenti con scadenza, cambio gomme. Avviso a 30, 15 e 3 giorni prima, il giorno stesso, e ogni lunedì se in ritardo (fino a 180 giorni)
    veicoli = ((d.get("auto") or {}).get("veicoli")) or []
    for v in veicoli:
        if not isinstance(v, dict):
            continue
        nome_v = " ".join(x for x in (v.get("marca"), v.get("modello")) if x) or v.get("nome") or "Veicolo"
        sc = v.get("scadenze") or {}
        etich = {"bollo": "Bollo", "assicurazione": "Assicurazione", "revisione": "Revisione", "garanzia_auto": "Garanzia", "garanzia_batteria": "Garanzia batteria", "tagliando": "Tagliando", "tachigrafo": "Tachigrafo (taratura)"}
        voci = [(etich.get(k, k), data_di((s_ or {}).get("data"))) for k, s_ in sc.items() if isinstance(s_, dict) and s_.get("avvisa") is not False]
        for dc in (v.get("documenti") or []):
            dd = data_di(dc.get("scadenza"))
            if dd and not ((dc.get("tipo") == "Polizza assicurativa" and data_di((sc.get("assicurazione") or {}).get("data")) == dd) or (dc.get("tipo") == "Revisione (certificato)" and data_di((sc.get("revisione") or {}).get("data")) == dd)):
                voci.append((dc.get("titolo") or dc.get("tipo") or "Documento", dd))
        for pn in (v.get("pneumatici") or []):
            if pn.get("stato") != "In deposito" and data_di(pn.get("cambio_entro")):
                voci.append(("Cambio gomme", data_di(pn.get("cambio_entro"))))
        for us in (v.get("usura") or []):
            if data_di(us.get("prossima_data")):
                voci.append((f"{us.get('parte', 'Parte')} (usura)", data_di(us.get("prossima_data"))))
        for etichetta, dd in voci:
            if not dd:
                continue
            g = (dd - oggi).days
            if g in (90, 30, 15, 3, 0) or (-180 <= g < 0 and oggi.weekday() == 0):
                out.append((g, f"🚗 {etichetta} · {nome_v}" + (f" ({v.get('targa')})" if v.get("targa") else ""), dd))
    # CONDUCENTE: patente, visita medica, CQC (90, 30, 15, 3 giorni prima) e verbali da pagare (15, 5, 3, 0 giorni prima)
    cond = (d.get("auto") or {}).get("conducente") or {}
    for pt in (cond.get("patenti") or []):
        for k, et in (("scadenza", "Patente"), ("visita_medica", "Visita medica della patente"), ("cqc", "CQC")):
            dd = data_di(pt.get(k))
            if not dd or pt.get("avvisa") is False:
                continue
            g = (dd - oggi).days
            if g in (90, 30, 15, 3, 0) or (-180 <= g < 0 and oggi.weekday() == 0):
                out.append((g, f"🪪 {et} · {pt.get('nome', '')}", dd))
    for vb in (cond.get("verbali") or []):
        dd = data_di(vb.get("scadenza_pagamento"))
        if dd and vb.get("stato") == "Da pagare":
            g = (dd - oggi).days
            if g in (15, 5, 3, 0) or (-180 <= g < 0 and oggi.weekday() == 0):
                out.append((g, f"🧾 Verbale da pagare ({vb.get('tipo') or vb.get('luogo') or 'multa'})", dd))
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


# ----------------------------------------------------------------------------------------------------------------------
# 💊 SCORTE DEI MEDICINALI (Salute → Scorte e rinnovo ricette): avviso prima che le pastiglie finiscano. Il CALCOLO è la stessa copia di salute_scorte.py (l'app e questo programma
# devono dare gli stessi giorni: c'è una prova che li confronta). Avvisa quando mancano i giorni scelti per quel medicinale (7 se non scelti), 3, 1 e il giorno stesso; se è finito, ogni
# giorno per 3 giorni. Se si è segnato «Ho chiesto le ricette» non avvisa più, finché non si registra una nuova scatola.
# ----------------------------------------------------------------------------------------------------------------------
_SCORTA_PAROLE = {"mezza": 0.5, "mezzo": 0.5, "un": 1, "una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6}


def _scorta_num(v):
    """Un numero scritto come «2», «0,5», «1/15» (una frazione). None se non è un numero."""
    t = str(v).strip().replace(",", ".")
    try:
        if "/" in t:
            a, b = t.split("/", 1)
            return float(a) / float(b) if float(b) else None
        return float(t)
    except (ValueError, TypeError):
        return None


def _scorta_data(iso):
    try:
        return date.fromisoformat(str(iso)[:10]) if iso else None
    except ValueError:
        return None


def scorta_parse_dose(testo):
    """«1 compressa», «2 compresse», «1/2», «½ compressa», «mezza compressa», «1,5», «una cpr», «due» → quante pastiglie per assunzione (None se non si capisce)."""
    t = str(testo or "").lower().strip()
    if not t:
        return None
    t = t.replace("½", " 0.5 ").replace("¼", " 0.25 ").replace("¾", " 0.75 ")
    m = re.search(r"(\d+)\s*/\s*(\d+)", t)
    if m and int(m.group(2)) > 0:
        return round(int(m.group(1)) / int(m.group(2)), 4)
    m = re.search(r"\d+(?:[.,]\d+)?", t)
    if m:
        return _scorta_num(m.group(0))
    for parola, valore in _SCORTA_PAROLE.items():
        if re.search(r"\b" + parola + r"\b", t):
            return float(valore)
    return None


def _scorta_terapie_di(terapie, pid, med_id):
    return [t for t in terapie if isinstance(t, dict) and t.get("profilo", "p0") == pid and t.get("med") == med_id]


def _scorta_consumo_terapie(rilevanti, d):
    """Pastiglie previste dalle terapie in un giorno (stesse regole di Terapie: giorni, inizio, fine, sospesa)."""
    tot = 0.0
    for t in rilevanti:
        if d.weekday() not in (t.get("giorni") or []):
            continue
        ini, fin = _scorta_data(t.get("inizio")), _scorta_data(t.get("fine"))
        if (ini and d < ini) or (fin and d > fin):
            continue
        if t.get("stato") in ("sospesa", "terminata"):
            dal = _scorta_data(t.get("stato_dal"))
            if dal is None or d >= dal:
                continue
        q = scorta_parse_dose(t.get("quantita"))
        if q is None:
            continue
        tot += q * len(t.get("orari") or [])
    return tot


def _scorta_aggiungi_mesi(d, n):
    import calendar as _cal
    m = d.month - 1 + n
    a, m = d.year + m // 12, m % 12 + 1
    return date(a, m, min(d.day, _cal.monthrange(a, m)[1]))


def scorta_freq_valida(freq):
    """La frequenza «a intervalli» (una dose ogni N giorni, settimane o mesi) se è scritta bene, altrimenti None."""
    if not isinstance(freq, dict) or freq.get("tipo") not in ("giorni", "settimane", "mesi"):
        return None
    ogni, dose = _scorta_num(freq.get("ogni")), _scorta_num(freq.get("dose"))
    if not ogni or ogni < 1 or not dose or dose <= 0:
        return None
    return {"tipo": freq["tipo"], "ogni": int(ogni), "dose": dose, "prima": _scorta_data(freq.get("prima"))}


def scorta_descrivi_freq(freq):
    f = scorta_freq_valida(freq)
    if not f:
        return ""
    unita = {"giorni": ("giorno", "giorni"), "settimane": ("settimana", "settimane"), "mesi": ("mese", "mesi")}[f["tipo"]]
    return f"{f['dose']:g} " + (f"ogni {unita[0]}" if f["ogni"] == 1 else f"ogni {f['ogni']} {unita[1]}")


def _scorta_e_giorno_di_dose(f, prima, d):
    if d < prima:
        return False
    if f["tipo"] == "giorni":
        return (d - prima).days % f["ogni"] == 0
    if f["tipo"] == "settimane":
        return (d - prima).days % (7 * f["ogni"]) == 0
    m = (d.year - prima.year) * 12 + d.month - prima.month
    return m % f["ogni"] == 0 and d == _scorta_aggiungi_mesi(prima, m)


def scorta_calcola(med, terapie, pid, oggi_):
    """Lo stato della scorta di un medicinale.
    → {stato: spento | dati_mancanti | senza_terapia | dose_non_capita | nessun_consumo | ok | ok_lungo | in_esaurimento | finito, ultima (ultima dose coperta), fino_al (l'ultimo giorno
    in cui la scorta basta: il giorno PRIMA della prima dose non coperta), giorni (da oggi a fino_al), restano, per_giorno, preavviso, richiesto}
    Le assunzioni possono essere ogni giorno (dalla terapia o scritte a mano) oppure A INTERVALLI (una dose ogni N giorni, settimane o mesi, per esempio una fiala ogni 15 giorni)."""
    sc = med.get("scorta") or {}
    if not sc.get("attiva"):
        return {"stato": "spento"}
    avvio, iniz = _scorta_data(sc.get("avvio")), _scorta_num(sc.get("pastiglie"))
    pre = int(_scorta_num(sc.get("preavviso")) or 7)
    ris = {"stato": "dati_mancanti", "ultima": None, "fino_al": None, "giorni": None, "restano": None, "per_giorno": None, "preavviso": pre, "richiesto": _scorta_data(sc.get("rinnovo_richiesto"))}
    if avvio is None or iniz is None or iniz < 0:
        return ris
    freq = scorta_freq_valida(sc.get("frequenza"))
    manuale = _scorta_num(sc.get("per_giorno"))
    if manuale is not None and manuale <= 0:
        manuale = None
    rilevanti = _scorta_terapie_di(terapie, pid, med.get("id"))
    if freq is None and manuale is None:
        if not rilevanti:
            ris["stato"] = "senza_terapia"
            return ris
        if any(scorta_parse_dose(t.get("quantita")) is None for t in rilevanti if t.get("stato") not in ("terminata",)):
            ris["stato"] = "dose_non_capita"
            return ris
    prima = (freq["prima"] if freq else None) or avvio

    def consumo(d):
        if freq is not None:
            return freq["dose"] if _scorta_e_giorno_di_dose(freq, prima, d) else 0.0
        return manuale if manuale is not None else _scorta_consumo_terapie(rilevanti, d)
    cum, ultima, d, finisce, passati, scoperta = 0.0, None, min(avvio, prima), False, 0.0, None
    for _ in range(2400):
        c = consumo(d)
        if d >= avvio and d < oggi_:
            passati += c
        if c > 0 and d >= avvio:
            if cum + c > iniz + 1e-9:
                finisce, scoperta = True, d
                break
            cum += c
            ultima = d
        d += timedelta(days=1)
    ris["restano"] = max(0.0, round(iniz - passati, 2))
    ris["per_giorno"] = round(sum(consumo(oggi_ + timedelta(days=k)) for k in range(7)) / 7, 2)
    if ultima is None and not finisce:
        ris["stato"] = "nessun_consumo"
        return ris
    if not finisce:
        ris["stato"], ris["ultima"], ris["fino_al"], ris["giorni"] = "ok_lungo", ultima, ultima, (ultima - oggi_).days
        return ris
    if ultima is None:                                                                  # non bastano nemmeno per la prima dose
        ultima = avvio - timedelta(days=1)
    fino_al = scoperta - timedelta(days=1)                                              # la scorta basta fino al giorno prima della prima dose che non si riesce a coprire
    if freq is None:
        fino_al = max(fino_al, ultima)
    ris["ultima"], ris["fino_al"], ris["giorni"] = ultima, fino_al, (fino_al - oggi_).days
    ris["stato"] = "finito" if ris["giorni"] < 0 else ("in_esaurimento" if ris["giorni"] <= pre else "ok")
    return ris




def raccogli_scorte(d, oggi):
    """[(medicinale con dosaggio, persona o '', giorni, ultimo giorno coperto, restano, stato)] per i medicinali da avvisare oggi."""
    f = d.get("farmacia") or {}
    profili = {x.get("id"): x.get("nome", "") for x in (f.get("profili") or []) if isinstance(x, dict)}
    out = []
    for m in f.get("medicinali", []):
        if not isinstance(m, dict):
            continue
        pid = m.get("profilo", "p0")
        try:
            r = scorta_calcola(m, f.get("terapie", []), pid, oggi)
        except Exception:
            continue
        if r["stato"] not in ("in_esaurimento", "finito") or r.get("richiesto"):
            continue
        g = r["giorni"]
        if g in {r["preavviso"], 3, 1, 0} or -3 <= g < 0:
            nome = (m.get("nome") or "Medicinale") + (f" {m['dosaggio']}" if m.get("dosaggio") else "")
            out.append((nome, profili.get(pid, "") if len(profili) > 1 else "", g, r.get("fino_al") or r["ultima"], r["restano"], r["stato"]))
    return sorted(out, key=lambda x: x[2])


def testo_scorte(oggi, voci):
    righe = [f"💊 Scorte – promemoria del {oggi.strftime('%d/%m/%Y')}", ""]
    for nome, pers, g, ultima, restano, stato in voci:
        quando = "è finito" if g < 0 else "finisce oggi" if g == 0 else "finisce domani" if g == 1 else f"finisce tra {g} giorni"
        righe.append(f"• {nome}" + (f" ({pers})" if pers else "") + f": {quando}" + (f" (le pastiglie bastano fino al {ultima.strftime('%d/%m/%Y')})" if ultima and g >= 0 else "") + (f" – ne restano circa {restano:g}" if g >= 0 and restano is not None else "") + ".")
    righe += ["", "Per chiedere la ricetta: apri l'app → Salute → 💊 Scorte e rinnovo ricette. Lì trovi la bozza dell'email per la dottoressa: la ricontrolli e la mandi tu."]
    return "\n".join(righe)


def avvisi_scorte(oggi, bloccati, registra):
    """Le scorte che stanno per finire, a chiunque tenga il conto di qualche medicinale, sui canali che ha scelto."""
    for uid, d in utenti_attivi(bloccati):
        voci = raccogli_scorte(d, oggi)
        if not voci:
            continue
        testo = testo_scorte(oggi, voci)
        for canale in canali_di(d):
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                esito = invia_email(d["avviso_email"].strip(), "Scorte dei medicinali - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                esito = invia_sms(d["avviso_sms"].strip(), f"Scorte: {len(voci)} medicinal{'e' if len(voci) == 1 else 'i'} in esaurimento. Apri l'app.")
            elif canale == "whatsapp" and (d.get("avviso_whatsapp") or "").strip():
                esito = invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), testo)
            else:
                continue
            registra(f"{uid}-scorte", canale, esito)


# ----------------------------------------------------------------------------------------------------------------------
# «📨 Mandami un messaggio di prova»: la persona tocca il pulsante nell'app (che scrive d["avviso_prova"] = {id, quando} nei suoi dati). Qui, a ogni controllo automatico
# (ogni mezz'ora di giorno e ogni mattina), si manda il messaggio di prova su OGNI canale che ha scelto e si scrive l'ESITO in prove_avvisi/<persona>.json: l'app lo legge e
# mostra ✅ o ❌ per canale, con cosa fare. Serve il permesso di scrittura del workflow (permissions: contents: write + GITHUB_TOKEN, come per la posta): se manca, il messaggio
# parte lo stesso ma solo per richieste recenti (al massimo 35 minuti), per non ripeterlo a ogni controllo.
# ----------------------------------------------------------------------------------------------------------------------
CARTELLA_PROVE = "prove_avvisi"
ORE_VALIDITA_PROVA = 26
TESTO_PROVA = "✅ Prova riuscita! Da oggi ricevi qui gli avvisi di «La nostra dispensa». Se stai leggendo questo messaggio, questo canale funziona."


class ArchivioEsiti:
    """Scrive i file dell'esito con le API di GitHub (GITHUB_TOKEN e GITHUB_REPOSITORY, come in posta.py)."""

    def __init__(self, repo, token, ramo="main"):
        self.repo, self.token, self.ramo = repo, token, ramo

    def _chiama(self, metodo, percorso, corpo=None):
        url = f"https://api.github.com/repos/{self.repo}/contents/{percorso}" + (f"?ref={self.ramo}" if metodo == "GET" else "")
        req = urllib.request.Request(url, method=metodo, data=json.dumps(corpo).encode() if corpo is not None else None,
                                     headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                                              "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "DispensaFamiglia/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8") or "{}")

    def sha(self, percorso):
        try:
            return self._chiama("GET", percorso).get("sha")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def scrivi(self, percorso, dati, messaggio):
        corpo = {"message": messaggio, "branch": self.ramo,
                 "content": base64.b64encode(json.dumps(dati, ensure_ascii=False).encode("utf-8")).decode()}
        sha = self.sha(percorso)
        if sha:
            corpo["sha"] = sha
        return self._chiama("PUT", percorso, corpo)


def _invia_prova(canale, d):
    """L'esito («ok», «errore: …» o «saltato: …») dell'invio del messaggio di prova su un canale."""
    if canale == "telegram":
        if not str(d.get("telegram_chat_id") or "").strip():
            return "saltato: manca il Chat ID di Telegram"
        return invia_telegram(str(d["telegram_chat_id"]).strip(), TESTO_PROVA)
    if canale == "email":
        if not (d.get("avviso_email") or "").strip():
            return "saltato: manca l'indirizzo email"
        return invia_email(d["avviso_email"].strip(), "Prova riuscita - La nostra dispensa", TESTO_PROVA)
    if canale == "sms":
        if not (d.get("avviso_sms") or "").strip():
            return "saltato: manca il numero di cellulare"
        return invia_sms(d["avviso_sms"].strip(), "Dispensa: prova riuscita, qui ricevi gli avvisi.")
    if canale == "whatsapp":
        if not (d.get("avviso_whatsapp") or "").strip():
            return "saltato: manca il numero di WhatsApp"
        return invia_whatsapp(d["avviso_whatsapp"], d.get("avviso_whatsapp_chiave"), TESTO_PROVA)
    return "saltato: canale sconosciuto"


def prove_richieste(adesso, bloccati, archivio=None):
    """Elabora le richieste «Mandami un messaggio di prova». Ritorna quante ne ha elaborate. Non fa mai fallire il programma (non tocca il codice di uscita)."""
    fatte = 0
    if archivio is None and E("GITHUB_TOKEN") and E("GITHUB_REPOSITORY") and not DRY:
        archivio = ArchivioEsiti(E("GITHUB_REPOSITORY"), E("GITHUB_TOKEN"))
    for percorso in sorted(glob.glob("dispense/*.json")):
        uid = os.path.splitext(os.path.basename(percorso))[0]
        if uid in bloccati:
            continue
        d = leggi(percorso)
        rich = d.get("avviso_prova")
        if not (isinstance(rich, dict) and rich.get("id")):
            continue
        if leggi(f"{CARTELLA_PROVE}/{uid}.json").get("id") == rich["id"]:
            continue                                                       # già fatta (o in corso da un altro controllo)
        try:
            quando = datetime.fromisoformat(str(rich.get("quando")))
        except ValueError:
            continue
        if adesso - quando > timedelta(hours=ORE_VALIDITA_PROVA) or quando > adesso + timedelta(hours=1):
            continue                                                       # troppo vecchia o con l'ora sbagliata: non si manda più
        file_esito = f"{CARTELLA_PROVE}/{uid}.json"
        puo_scrivere = False
        if archivio is not None:
            try:                                                           # 1) segno subito «in corso»: così un altro controllo non la ripete
                archivio.scrivi(file_esito, {"id": rich["id"], "stato": "in corso", "richiesta": rich.get("quando")}, "Prova avvisi: in corso")
                puo_scrivere = True
            except Exception as e:
                print(f"[{uid}] prova: non riesco a scrivere l'esito ({type(e).__name__}): serve «permissions: contents: write» nel file promemoria.yml")
        if not DRY and not puo_scrivere and adesso - quando > timedelta(minutes=35):
            continue                                                       # senza poter scrivere l'esito (manca il permesso o GITHUB_TOKEN) si manda solo se è recente: al massimo 2 volte
        canali = canali_di(d)
        esiti = {}
        for canale in canali:
            esiti[canale] = _invia_prova(canale, d)
            print(f"[{uid}] prova {canale}: {esiti[canale]}")
        risultato = {"id": rich["id"], "stato": "fatto" if canali else "nessun canale", "richiesta": rich.get("quando"),
                     "inviata": adesso.isoformat(timespec="minutes"), "esiti": esiti}
        if puo_scrivere:
            try:
                archivio.scrivi(file_esito, risultato, "Prova avvisi: esito")
            except Exception as e:
                print(f"[{uid}] prova: esito non salvato ({type(e).__name__})")
        elif archivio is None:
            print(f"[{uid}] prova: {json.dumps(risultato, ensure_ascii=False)}")
        fatte += 1
    return fatte


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

    try:
        n_prove = prove_richieste(adesso, bloccati)                    # le richieste «📨 Mandami un messaggio di prova» fatte dall'app
        if n_prove:
            print(f"Messaggi di prova richiesti dalle persone: {n_prove}")
    except Exception as e:
        print(f"Prove richieste dalle persone: errore ({type(e).__name__}: {e})")
    if DOSI and not PROVA:                                             # promemoria della raccolta differenziata (nella mezz'ora che contiene l'ora scelta)
        try:
            avvisi_raccolta(adesso, bloccati, registra)
        except Exception as e:
            print(f"Raccolta differenziata: errore ({type(e).__name__}: {e})")
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
        try:
            avvisi_scorte(oggi, bloccati, registra)
        except Exception as e:                                            # una scorta con dati strani non ferma gli altri avvisi
            print(f"Scorte: errore ({type(e).__name__}: {e})")
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
