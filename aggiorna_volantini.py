# -*- coding: utf-8 -*-
"""Aggiornamento automatico dei volantini (da lanciare ogni settimana, per esempio con GitHub Actions).
Legge gli indirizzi salvati nella scheda Offerte > Fonti, scarica i PDF, ne estrae le offerte e le salva in offerte.json.

Uso con GitHub:   DATI_TOKEN=... DATI_REPO=Nome/dispensa-dati python aggiorna_volantini.py
Uso di prova:     python aggiorna_volantini.py --locale percorso/offerte.json
"""
import base64
import json
import os
import sys
import time
from datetime import datetime

import requests

import estrazione_volantini as ev

FILE = "offerte.json"


class DatiGitHub:
    def __init__(self, token, repo, ramo=None):
        base = os.environ.get("GITHUB_API", "https://api.github.com")
        self.url = f"{base}/repos/{repo}/contents/{FILE}"
        self.ramo = ramo
        self.h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    def leggi(self):
        r = requests.get(self.url, headers=self.h, params={"ref": self.ramo} if self.ramo else None, timeout=30)
        if r.status_code == 404:
            return {}, None
        r.raise_for_status()
        j = r.json()
        grezzo = base64.b64decode(j["content"]) if j.get("content") else base64.b64decode(
            requests.get(self.url.rsplit("/contents/", 1)[0] + f"/git/blobs/{j['sha']}", headers=self.h, timeout=30).json()["content"])
        return json.loads(grezzo.decode("utf-8") or "{}"), j["sha"]

    def scrivi(self, dati, sha, messaggio):
        corpo = {"message": messaggio, "content": base64.b64encode(json.dumps(dati, ensure_ascii=False).encode("utf-8")).decode()}
        if sha:
            corpo["sha"] = sha
        if self.ramo:
            corpo["branch"] = self.ramo
        r = requests.put(self.url, headers=self.h, json=corpo, timeout=40)
        r.raise_for_status()


class DatiLocali:
    def __init__(self, percorso):
        self.percorso = percorso

    def leggi(self):
        try:
            with open(self.percorso, encoding="utf-8") as f:
                return json.load(f), None
        except FileNotFoundError:
            return {}, None

    def scrivi(self, dati, sha, messaggio):
        with open(self.percorso, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False)


def aggiorna(archivio):
    """Scorre le fonti e aggiorna l'archivio. Ritorna (quante fonti ok, quante in errore)."""
    for tentativo in range(4):
        dati, sha = archivio.leggi()
        fonti = dati.get("fonti", [])
        if not fonti:
            print("Nessuna fonte salvata: aggiungile nella scheda Offerte > Fonti.")
            return 0, 0
        ok = ko = 0
        for f in fonti:
            etichetta = f"{f.get('negozio')} ({f.get('citta')})"
            try:
                pdf, url_pdf = ev.leggi_fonte(f["url"])
                ris = ev.estrai_volantino(pdf)
                if not (ris.get("dal") and ris.get("al")):
                    raise ValueError("date di validità non trovate nel volantino")
                n = ev.registra_volantino(dati, ris["offerte"], f["negozio"], f.get("tipo", "Supermercato"), f["citta"],
                                          ris["dal"], ris["al"], url_pdf, "aggiornamento automatico")
                print(f"OK  {etichetta}: {n} offerte ({ris['dal']} - {ris['al']})")
                ok += 1
            except Exception as e:
                print(f"ERR {etichetta}: {e}")
                ko += 1
        dati["ultimo_aggiornamento"] = datetime.now().isoformat(timespec="seconds")
        try:
            archivio.scrivi(dati, sha, f"Aggiornamento automatico volantini ({ok} ok, {ko} errori)")
            return ok, ko
        except requests.HTTPError as e:                   # qualcuno ha salvato nel frattempo: riprovo
            if e.response is not None and e.response.status_code in (409, 422):
                time.sleep(2 * (tentativo + 1))
                continue
            raise
    raise RuntimeError("Troppe modifiche contemporanee: riprova più tardi.")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--locale":
        arch = DatiLocali(sys.argv[2])
    else:
        token, repo = os.environ.get("DATI_TOKEN"), os.environ.get("DATI_REPO")
        if not (token and repo):
            sys.exit("Mancano DATI_TOKEN e DATI_REPO (vedi la guida).")
        arch = DatiGitHub(token, repo, os.environ.get("DATI_BRANCH") or None)
    ok, ko = aggiorna(arch)
    print(f"Fatto: {ok} aggiornati, {ko} con errore.")
    sys.exit(1 if (ko and not ok) else 0)
