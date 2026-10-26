#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Promemoria di scadenza per "La nostra dispensa" e per la Farmacia: Telegram, email e SMS.

Gira ogni mattina su GitHub Actions dentro il repository dei dati (dispensa-dati).
Legge i file dispense/*.json e avvisa ogni persona con i canali che ha scelto nell'app.
Uso:  python promemoria.py            -> invia i promemoria di oggi
      python promemoria.py --prova    -> invia solo un messaggio di prova su tutti i canali scelti
      python promemoria.py --dry      -> non invia nulla, mostra i messaggi a schermo

Chiavi segrete (GitHub -> Settings -> Secrets and variables -> Actions), ognuna serve solo se usi quel canale:
  Telegram: TELEGRAM_TOKEN
  Email:    EMAIL_USER, EMAIL_PASSWORD  (facoltativi: EMAIL_SMTP, EMAIL_PORT; di base Gmail)
  SMS:      TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM
"""
import base64
import glob
import json
import os
import smtplib
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

SOGLIE = (60, 30, 14, 7, 1, 0)          # giorni mancanti alla scadenza in cui arriva un messaggio
DRY = "--dry" in sys.argv
PROVA = "--prova" in sys.argv
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


def raccogli(d, oggi):
    in_soglia, scaduti = [], []
    for icona, nome, s, profilo in voci_utente(d):
        g = (s - oggi).days
        if g in SOGLIE:
            in_soglia.append((g, icona, nome, s, profilo))
        elif g < 0 and oggi.weekday() == 0:          # i già scaduti: un promemoria ogni lunedì
            scaduti.append((g, icona, nome, s, profilo))
    return sorted(in_soglia, key=lambda x: x[0]), sorted(scaduti, key=lambda x: x[0])


def testo_lungo(d, oggi, in_soglia, scaduti):
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
            extra = f" ({profilo})" if profilo else ""
            righe.append(f"• {icona} {nome}{extra} – {quando(g)} ({s.strftime('%d/%m/%Y')})")
        if med and privacy:
            righe.append(("• 💊 1 medicinale" if len(med) == 1 else f"• 💊 {len(med)} medicinali")
                         + ": apri la Farmacia per i dettagli")
    blocco("⚠️ In scadenza:", in_soglia)
    blocco("⚫ Già scaduti (da buttare o controllare):", scaduti)
    return "\n".join(righe)


def testo_sms(oggi, in_soglia, scaduti):
    """Per gli SMS: breve e senza nomi di medicinali (un SMS non è un canale riservato)."""
    def pl(n, uno, molti):
        return f"{n} {uno if n == 1 else molti}"
    prod = sum(1 for x in in_soglia if x[1] == "🥫")
    med = sum(1 for x in in_soglia if x[1] == "💊")
    parti = [x for x in (pl(prod, "prodotto", "prodotti") if prod else "",
                         pl(med, "medicinale", "medicinali") if med else "") if x]
    testo = f"Dispensa {oggi.strftime('%d/%m')}: " + (" e ".join(parti) + " in scadenza" if parti else "nessuna scadenza vicina")
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


def canali_di(d):
    canali = d.get("avvisi_canali")
    if canali is None:                                    # chi ha solo il Chat ID di Telegram
        canali = ["telegram"] if d.get("telegram_chat_id") else []
    return [c for c in canali if c in ("telegram", "email", "sms")]


def main():
    oggi = datetime.now(ZoneInfo("Europe/Rome")).date()
    bloccati = {u.get("id") for u in leggi("utenti.json").get("utenti", []) if not u.get("attivo", True)}
    ok = errori = saltati = 0
    for percorso in sorted(glob.glob("dispense/*.json")):
        uid = os.path.splitext(os.path.basename(percorso))[0]
        d = leggi(percorso)
        if uid in bloccati:
            continue
        in_soglia, scaduti = raccogli(d, oggi)
        if not PROVA and not in_soglia and not scaduti:
            continue
        for canale in canali_di(d):
            if canale == "telegram" and str(d.get("telegram_chat_id") or "").strip():
                testo = "✅ Prova riuscita: da oggi ricevi qui i promemoria della dispensa e della Farmacia." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti)
                esito = invia_telegram(str(d["telegram_chat_id"]).strip(), testo)
            elif canale == "email" and (d.get("avviso_email") or "").strip():
                testo = "Prova riuscita: da oggi ricevi via email i promemoria della dispensa e della Farmacia." if PROVA \
                    else testo_lungo(d, oggi, in_soglia, scaduti)
                esito = invia_email(d["avviso_email"].strip(), "Promemoria scadenze - La nostra dispensa", testo)
            elif canale == "sms" and (d.get("avviso_sms") or "").strip():
                testo = "Dispensa: prova riuscita, da oggi ricevi qui gli avvisi di scadenza." if PROVA \
                    else testo_sms(oggi, in_soglia, scaduti)
                esito = invia_sms(d["avviso_sms"].strip(), testo)
            else:
                continue
            print(f"[{uid}] {canale}: {esito}")
            if esito == "ok":
                ok += 1
            elif esito.startswith("saltato"):
                saltati += 1
            else:
                errori += 1
    print(f"Messaggi inviati: {ok}, saltati: {saltati}, errori: {errori}")
    return 1 if errori or (PROVA and saltati) else 0


if __name__ == "__main__":
    sys.exit(main())
