# -*- coding: utf-8 -*-
"""TRASFERIMENTO DATI TRA UTENTI: il file «.dispensa».
Un utente crea un file con i dati che sceglie (tutto, alcune categorie, una persona, singole voci), lo manda a un altro utente
(email, Telegram…) e l'altro lo importa nella propria app: compare una NUOVA scheda con il nome della persona, con i contenuti nelle
loro sezioni (Medicinali, Terapie, Prescrizioni, Visite, Vaccinazioni, Documenti), allegati compresi.

FORMATO (versione 1) — un archivio ZIP, con estensione .dispensa, che contiene:
  manifest.json   formato, versione, data, mittente, consenso, elenco dei file con impronta SHA-256, impronta dei dati
  dati.json       le persone e le loro voci (medicinali, terapie, prescrizioni, visite, vaccinazioni, documenti, allergie)
  allegati/<id>   le foto e i PDF originali, byte per byte
Se si sceglie una password, l'intero archivio è cifrato (AES-256-GCM, chiave ricavata con scrypt) e comincia con la sigla DISPENSA1.
Le versioni future dell'app leggono anche i file delle versioni precedenti (il numero di versione è nel manifest).

REGOLE: nessuna sovrascrittura (si crea sempre una scheda nuova, o si aggiungono solo le voci mancanti a una scheda già importata dallo stesso mittente);
i documenti originali (foto, PDF, referti) si conservano identici, con il segno «originale»; chi riceve può correggere i dati scritti a mano
e aggiungere annotazioni separate, senza toccare i file originali.
Caricato da app_dispensa.py dopo archivio.py."""
import base64
import copy
import hashlib
import io
import json
import os
import re
import uuid
import zipfile
from datetime import date, datetime

import streamlit as st

TR_FORMATO = "dispensa-trasferimento"
TR_VERSIONE = 1
_TR_SIGLA = b"DISPENSA1"
_TR_MIME_AMMESSI = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_TR_MAX_TOTALE = 400 * 1024 * 1024
_TR_MAX_VOCI = 4000
TR_CATEGORIE = {"medicinali": "💊 Medicinali", "terapie": "📅 Terapie", "prescrizioni": "📝 Prescrizioni", "visite": "🩺 Visite ed esami",
                "vaccinazioni": "💉 Vaccinazioni", "documenti": "🪪 Documenti", "allergie": "⚠️ Allergie dichiarate"}
_TR_CON_RECORD = ("medicinali", "terapie", "prescrizioni", "visite", "vaccinazioni", "documenti")
TR_TESTO_CONSENSO = ("Dichiaro di avere il consenso delle persone a cui si riferiscono questi dati personali e sanitari e di volerli condividere "
                     "con il destinatario (GDPR).")


class TrErrore(Exception):
    """Un problema spiegabile all'utente (file non valido, password errata, versione troppo nuova…)."""


def _sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# Raccogliere i dati da esportare
# ---------------------------------------------------------------------------------------------------------------------
def _tr_refs(tipo, rec):
    """I riferimenti ai file (foto, PDF) di una voce, come lista di dizionari modificabili."""
    refs = []
    if tipo == "medicinali":
        if isinstance(rec.get("foto_grande"), dict):
            refs.append(rec["foto_grande"])
        refs += [a for a in rec.get("foglio", []) if isinstance(a, dict)]
    elif tipo in ("documenti", "prescrizioni", "visite"):
        refs += [a for a in rec.get("allegati", []) if isinstance(a, dict)]
    return refs


def tr_raccogli(f, pids, categorie, selezione=None, includi_file=True):
    """Il contenuto del file: {'persone': [...]}. selezione = {categoria: insieme di id}; None o categoria assente = tutte le voci."""
    nomi = {p["id"]: p for p in (f.get("profili") or [])}
    persone = []
    for pid in pids:
        p = nomi.get(pid, {"id": pid, "nome": pid})
        persona = {"id": pid, "nome": p.get("nome", ""), "profilo": {k: v for k, v in p.items() if k not in ("id", "nome", "importato")}}
        for cat in _TR_CON_RECORD:
            if cat not in categorie:
                persona[cat] = []
                continue
            voci = [copy.deepcopy(x) for x in f.get(cat, []) if x.get("profilo", "p0") == pid]
            if selezione and selezione.get(cat) is not None:
                voci = [x for x in voci if x.get("id") in selezione[cat]]
            persona[cat] = voci
        persona["allergie"] = list((f.get("allergie") or {}).get(pid, [])) if "allergie" in categorie else []
        persona["vaccini_doc"] = [dict(a) for a in (f.get("vaccini_doc") or {}).get(pid, [])] if ("vaccinazioni" in categorie and includi_file) else []
        nomi_med = {m.get("id"): m.get("nome", "") for m in f.get("medicinali", [])}
        for t in persona["terapie"]:                          # la terapia ricorda il nome del medicinale anche se il medicinale non viene esportato
            t["nome_med"] = t.get("nome_med") or nomi_med.get(t.get("med"), "")
        if not includi_file:                                  # senza foto e PDF: restano solo i dati scritti
            for rec in persona["medicinali"]:
                rec.pop("foto_grande", None)
                rec["foglio"] = []
            for cat in ("documenti", "prescrizioni", "visite"):
                for rec in persona[cat]:
                    rec["allegati"] = []
        persone.append(persona)
    return {"persone": persone}


def tr_id_file(payload):
    """Gli id di tutti i file citati nel contenuto."""
    ids = []
    for pers in payload["persone"]:
        for cat in ("medicinali", "documenti", "prescrizioni", "visite"):
            for rec in pers.get(cat, []):
                ids += [r["id"] for r in _tr_refs(cat, rec) if r.get("id")]
        ids += [a["id"] for a in pers.get("vaccini_doc", []) if a.get("id")]
    return list(dict.fromkeys(ids))


def tr_conteggi(payload):
    c = {k: 0 for k in TR_CATEGORIE}
    for pers in payload["persone"]:
        for k in _TR_CON_RECORD:
            c[k] += len(pers.get(k, []))
        c["allergie"] += len(pers.get("allergie", []))
    return c


# ---------------------------------------------------------------------------------------------------------------------
# Cifratura (facoltativa)
# ---------------------------------------------------------------------------------------------------------------------
def tr_cifra_disponibile():
    try:
        import cryptography.hazmat.primitives.ciphers.aead  # noqa: F401
        return True
    except Exception:
        return False


def _tr_chiave(password, sale):
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    return Scrypt(salt=sale, length=32, n=2 ** 15, r=8, p=1).derive(password.encode("utf-8"))


def tr_cifra(dati, password):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    sale, nonce = os.urandom(16), os.urandom(12)
    intestazione = _TR_SIGLA + sale + nonce
    return intestazione + AESGCM(_tr_chiave(password, sale)).encrypt(nonce, dati, _TR_SIGLA)


def tr_decifra(dati, password):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    n = len(_TR_SIGLA)
    sale, nonce, corpo = dati[n:n + 16], dati[n + 16:n + 28], dati[n + 28:]
    try:
        return AESGCM(_tr_chiave(password, sale)).decrypt(nonce, corpo, _TR_SIGLA)
    except InvalidTag:
        raise TrErrore("La password non è giusta, oppure il file è danneggiato.")


def tr_e_cifrato(dati):
    return dati[:len(_TR_SIGLA)] == _TR_SIGLA


# ---------------------------------------------------------------------------------------------------------------------
# Creare il file
# ---------------------------------------------------------------------------------------------------------------------
def tr_crea_pacchetto(payload, file_map, mittente_nome, mittente_id, password=None, ora=None):
    """file_map = {id: (nome, mime, byte)}. Ritorna i byte del file .dispensa."""
    ora = ora or datetime.now().replace(microsecond=0)
    dati_b = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    file_meta = [{"id": i, "nome": n, "mime": m, "dimensione": len(b), "sha256": _sha(b)} for i, (n, m, b) in file_map.items()]
    manifest = {"formato": TR_FORMATO, "versione": TR_VERSIONE, "app": "La nostra dispensa", "creato": ora.isoformat(),
                "mittente": {"nome": mittente_nome, "id": mittente_id}, "sha256_dati": _sha(dati_b), "file": file_meta,
                "conteggi": tr_conteggi(payload), "persone": [p["nome"] for p in payload["persone"]],
                "consenso": {"dichiarato": True, "testo": TR_TESTO_CONSENSO, "data": ora.isoformat()}, "cifrato": bool(password)}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        z.writestr("dati.json", dati_b)
        for i, (n, m, b) in file_map.items():
            z.writestr(f"allegati/{i}", b)
    dati = buf.getvalue()
    return tr_cifra(dati, password) if password else dati


# ---------------------------------------------------------------------------------------------------------------------
# Aprire e verificare il file
# ---------------------------------------------------------------------------------------------------------------------
def _tr_pulisci(x, profondita=0):
    """Tiene solo testo, numeri, vero/falso, liste e dizionari, con misure ragionevoli (il file viene da fuori: non ci si fida)."""
    if profondita > 8:
        raise TrErrore("Il file è strutturato in modo anomalo.")
    if isinstance(x, str):
        return x[:6000]
    if isinstance(x, (int, float, bool)) or x is None:
        return x
    if isinstance(x, list):
        if len(x) > 6000:
            raise TrErrore("Il file contiene troppe voci.")
        return [_tr_pulisci(v, profondita + 1) for v in x]
    if isinstance(x, dict):
        return {str(k)[:80]: _tr_pulisci(v, profondita + 1) for k, v in x.items()}
    raise TrErrore("Il file contiene dati non riconosciuti.")


def tr_apri(dati_file, password=None):
    """Legge e VERIFICA un file .dispensa. Ritorna {'manifest', 'payload', 'files': {id: (nome, mime, byte)}}. Solleva TrErrore se qualcosa non va."""
    if tr_e_cifrato(dati_file):
        if not password:
            raise TrErrore("Il file è protetto: serve la password.")
        if not tr_cifra_disponibile():
            raise TrErrore("Questa app non può leggere i file protetti (manca la libreria di cifratura).")
        dati_file = tr_decifra(dati_file, password)
    if dati_file[:2] != b"PK":
        raise TrErrore("Questo non è un file di trasferimento della dispensa.")
    try:
        z = zipfile.ZipFile(io.BytesIO(dati_file))
    except zipfile.BadZipFile:
        raise TrErrore("Il file è danneggiato (non si riesce ad aprire).")
    voci = z.infolist()
    if len(voci) > _TR_MAX_VOCI or sum(v.file_size for v in voci) > _TR_MAX_TOTALE:
        raise TrErrore("Il file è troppo grande o ha troppe parti.")
    nomi = {v.filename for v in voci}
    for n in nomi:
        if n.startswith("/") or ".." in n.split("/"):
            raise TrErrore("Il file contiene percorsi non sicuri: non lo apro.")
    if "manifest.json" not in nomi or "dati.json" not in nomi:
        raise TrErrore("Mancano le parti principali del file: potrebbe essere incompleto.")
    try:
        manifest = _tr_pulisci(json.loads(z.read("manifest.json").decode("utf-8")))
        dati_b = z.read("dati.json")
    except (ValueError, UnicodeDecodeError):
        raise TrErrore("Il file è danneggiato (contenuto illeggibile).")
    if not isinstance(manifest, dict) or manifest.get("formato") != TR_FORMATO:
        raise TrErrore("Non è un file della dispensa.")
    if not isinstance(manifest.get("versione"), int) or manifest["versione"] > TR_VERSIONE:
        raise TrErrore("Il file è stato creato con una versione più nuova dell'app: aggiorna l'app e riprova.")
    if _sha(dati_b) != manifest.get("sha256_dati"):
        raise TrErrore("Il file è stato modificato o è danneggiato: i dati non corrispondono all'impronta di controllo.")
    try:
        payload = _tr_pulisci(json.loads(dati_b.decode("utf-8")))
    except (ValueError, UnicodeDecodeError):
        raise TrErrore("Il file è danneggiato (dati illeggibili).")
    if not isinstance(payload, dict) or not isinstance(payload.get("persone"), list) or len(payload["persone"]) > 60:
        raise TrErrore("Il contenuto del file non è valido.")
    files = {}
    for meta in manifest.get("file", []):
        i, n = str(meta.get("id", "")), f"allegati/{meta.get('id', '')}"
        if not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", i) or n not in nomi:
            raise TrErrore("Nel file manca un allegato: potrebbe essere incompleto.")
        b = z.read(n)
        if _sha(b) != meta.get("sha256"):
            raise TrErrore(f"L'allegato «{str(meta.get('nome', ''))[:40]}» è danneggiato (l'impronta non corrisponde).")
        mime = str(meta.get("mime", ""))
        if mime not in _TR_MIME_AMMESSI:
            raise TrErrore(f"L'allegato «{str(meta.get('nome', ''))[:40]}» ha un tipo di file non ammesso ({mime[:30]}).")
        files[i] = (str(meta.get("nome", "file"))[:120], mime, b)
    for pers in payload["persone"]:
        if not isinstance(pers, dict) or not isinstance(pers.get("nome", ""), str):
            raise TrErrore("Il contenuto del file non è valido (persona).")
        for cat in _TR_CON_RECORD:
            if not isinstance(pers.get(cat, []), list) or any(not isinstance(r, dict) for r in pers.get(cat, [])):
                raise TrErrore(f"Il contenuto del file non è valido ({cat}).")
    return {"manifest": manifest, "payload": payload, "files": files}


# ---------------------------------------------------------------------------------------------------------------------
# Importare: sempre in una scheda nuova, senza sovrascrivere niente
# ---------------------------------------------------------------------------------------------------------------------
def _tr_nome_unico(nome, esistenti):
    nome = (nome or "Persona importata").strip()[:60] or "Persona importata"
    base, k, candidato = nome, 1, nome
    while candidato.lower() in {e.lower() for e in esistenti}:
        k += 1
        candidato = f"{base} ({k})"
    return candidato


def _tr_data_ok(v):
    try:
        return date.fromisoformat(str(v)) and str(v)[:10]
    except (ValueError, TypeError):
        return None


def _tr_valida(cat, rec):
    """Controlla e sistema una voce arrivata da un file esterno: i campi di testo diventano testo, le liste liste, le date devono essere vere.
    Se manca qualcosa che l'app dà per scontato (la data di una visita, il nome di una vaccinazione…) la voce viene scartata (None):
    così un file sbagliato o malevolo non può far crollare le schermate di Salute."""
    r = dict(rec)
    testi = {"medicinali": ("nome", "marca", "principio", "dosaggio", "forma", "unita", "note", "categoria"),
             "terapie": ("nome_med", "quantita", "stato", "note"),
             "prescrizioni": ("tipo", "prescritto", "medico", "codice", "stato", "note"),
             "visite": ("categoria", "ora", "medico", "motivo", "controlli", "note"),
             "vaccinazioni": ("nome", "dose", "note"),
             "documenti": ("tipo", "numero", "ente", "note")}.get(cat, ())
    for k in testi:
        if k in r and r[k] is not None and not isinstance(r[k], str):
            r[k] = str(r[k])
    if cat == "medicinali":
        if not str(r.get("nome", "")).strip():
            return None
        try:
            r["quantita"] = float(r.get("quantita", 1) or 0)
        except (TypeError, ValueError):
            r["quantita"] = 1.0
        for k in ("scadenza", "acquisto"):
            if r.get(k) is not None:
                r[k] = _tr_data_ok(r[k])
    elif cat == "terapie":
        r["inizio"] = _tr_data_ok(r.get("inizio"))
        if not r["inizio"]:
            return None
        r["fine"] = _tr_data_ok(r.get("fine")) if r.get("fine") else None
        r["orari"] = [o for o in (r.get("orari") or []) if isinstance(o, str) and re.fullmatch(r"\d{1,2}:\d{2}", o)] if isinstance(r.get("orari"), list) else []
        r["giorni"] = [g for g in (r.get("giorni") or []) if isinstance(g, int) and 0 <= g <= 6] if isinstance(r.get("giorni"), list) else []
        r.setdefault("quantita", "")
    elif cat == "visite":
        r["data"] = _tr_data_ok(r.get("data"))
        if not r["data"]:
            return None
        if r.get("prossimo"):
            r["prossimo"] = _tr_data_ok(r["prossimo"])
    elif cat == "vaccinazioni":
        r["data"] = _tr_data_ok(r.get("data"))
        if not r["data"] or not str(r.get("nome", "")).strip():
            return None
        if r.get("richiamo"):
            r["richiamo"] = _tr_data_ok(r["richiamo"])
    elif cat == "prescrizioni":
        for k in ("data", "valida_fino"):
            if r.get(k):
                r[k] = _tr_data_ok(r[k]) or ""
    elif cat == "documenti":
        for k in ("rilascio", "scadenza"):
            if r.get(k):
                r[k] = _tr_data_ok(r[k])
    return r


def tr_costruisci_import(f_dest, pacchetto, salta_duplicati=True, oggi=None):
    """Prepara l'importazione SENZA scrivere niente. Ritorna (nuovi_file {id: (nome, mime, byte, sha)}, modifica(f), riepilogo).
    modifica(f) aggiunge a f (i dati di Salute di chi importa) schede, voci e allegati; non tocca e non cancella nulla di esistente."""
    oggi = (oggi or date.today()).isoformat()
    man, payload, files = pacchetto["manifest"], pacchetto["payload"], pacchetto["files"]
    id_mitt, nome_mitt = str((man.get("mittente") or {}).get("id", "")), str((man.get("mittente") or {}).get("nome", "")) or "sconosciuto"
    nuovi_file, aggiunte = {}, []
    riepilogo = {"mittente": nome_mitt, "profili_nuovi": [], "profili_aggiornati": [], "importati": {k: 0 for k in TR_CATEGORIE}, "saltati": 0, "scartati": 0, "file": 0, "byte": 0}
    nomi_esistenti = [p.get("nome", "") for p in (f_dest.get("profili") or [])]

    def nuovo_rif(vecchio):
        i = vecchio.get("id")
        if i not in files:
            return None
        nome, mime, b = files[i]
        nid = uuid.uuid4().hex[:12]
        nuovi_file[nid] = (nome, mime, b, _sha(b))
        riepilogo["file"] += 1
        riepilogo["byte"] += len(b)
        return {"id": nid, "nome": nome, "mime": mime, "sha": _sha(b), "originale": True}

    for pers in payload["persone"]:
        pid_orig = str(pers.get("id", ""))
        esistente = next((p for p in (f_dest.get("profili") or []) if (p.get("importato") or {}).get("id_mittente") == id_mitt and id_mitt
                          and (p.get("importato") or {}).get("persona") == pid_orig), None) if salta_duplicati else None
        if esistente:
            pid, profilo_nuovo = esistente["id"], None
            riepilogo["profili_aggiornati"].append(esistente["nome"])
        else:
            pid = "p" + uuid.uuid4().hex[:8]
            nome = _tr_nome_unico(pers.get("nome", ""), nomi_esistenti)
            nomi_esistenti.append(nome)
            extra = {k: v for k, v in (pers.get("profilo") or {}).items() if k in ("gruppo", "nato", "sesso")}
            profilo_nuovo = {"id": pid, "nome": nome, **extra, "importato": {"da": nome_mitt, "id_mittente": id_mitt, "persona": pid_orig, "data": oggi, "versione": man.get("versione")}}
            riepilogo["profili_nuovi"].append(nome)
        gia = {c: {(r.get("origine") or {}).get("orig_id") for r in f_dest.get(c, [])
                   if (r.get("origine") or {}).get("id_mittente") == id_mitt and id_mitt} for c in _TR_CON_RECORD}
        mappa = {c: {} for c in _TR_CON_RECORD}
        nomi_med = {m.get("id"): m.get("nome", "") for m in pers.get("medicinali", [])}
        nuove_voci = {c: [] for c in _TR_CON_RECORD}
        for cat in ("medicinali", "documenti", "prescrizioni", "visite", "vaccinazioni", "terapie"):
            for rec in pers.get(cat, []):
                oid = rec.get("id")
                if salta_duplicati and oid in gia[cat]:
                    riepilogo["saltati"] += 1
                    existing = next((r for r in f_dest.get(cat, []) if (r.get("origine") or {}).get("orig_id") == oid and (r.get("origine") or {}).get("id_mittente") == id_mitt), None)
                    if existing:
                        mappa[cat][oid] = existing["id"]
                    continue
                nuovo = _tr_valida(cat, copy.deepcopy(rec))
                if nuovo is None:                                           # voce incompleta o rovinata: non si importa
                    riepilogo["scartati"] += 1
                    continue
                nid = uuid.uuid4().hex[:10]
                mappa[cat][oid] = nid
                nuovo["id"], nuovo["profilo"] = nid, pid
                nuovo["origine"] = {"da": nome_mitt, "id_mittente": id_mitt, "orig_id": oid, "importato": oggi}
                if cat == "medicinali":
                    if isinstance(nuovo.get("foto_grande"), dict):
                        nuovo["foto_grande"] = nuovo_rif(nuovo["foto_grande"])
                    nuovo["foglio"] = [r for r in (nuovo_rif(a) for a in nuovo.get("foglio", []) if isinstance(a, dict)) if r]
                elif cat in ("documenti", "prescrizioni", "visite"):
                    visti_sha, rifs = set(), []
                    for a in nuovo.get("allegati", []):
                        r = nuovo_rif(a) if isinstance(a, dict) else None
                        if r and r["sha"] not in visti_sha:
                            visti_sha.add(r["sha"])
                            rifs.append(r)
                    nuovo["allegati"] = rifs
                elif cat == "terapie":
                    m_vecchio = rec.get("med")
                    if m_vecchio and m_vecchio in mappa["medicinali"]:
                        nuovo["med"] = mappa["medicinali"][m_vecchio]
                    else:
                        nuovo["nome_med"] = rec.get("nome_med") or nomi_med.get(m_vecchio, "")
                        nuovo["med"] = None
                nuove_voci[cat].append(nuovo)
                riepilogo["importati"][cat] += 1
        vacc_doc = []
        gia_sha = {x.get("sha") for x in (f_dest.get("vaccini_doc") or {}).get(pid, []) if x.get("sha")}
        for a in pers.get("vaccini_doc", []):
            if not isinstance(a, dict) or a.get("id") not in files:
                continue
            if salta_duplicati and _sha(files[a["id"]][2]) in gia_sha:                  # la stessa pagina del libretto è già stata importata
                riepilogo["saltati"] += 1
                continue
            r = nuovo_rif(a)
            if r:
                vacc_doc.append(r)
                gia_sha.add(r["sha"])
        allergie = [str(x)[:120] for x in pers.get("allergie", []) if str(x).strip()]
        riepilogo["importati"]["allergie"] += len(allergie)
        aggiunte.append({"pid": pid, "profilo": profilo_nuovo, "voci": nuove_voci, "vaccini_doc": vacc_doc, "allergie": allergie})

    def modifica(f):
        f.setdefault("profili", [])
        for ag in aggiunte:
            if ag["profilo"]:
                f["profili"].append(ag["profilo"])
            for cat, voci in ag["voci"].items():
                f.setdefault(cat, []).extend(voci)
            if ag["vaccini_doc"]:
                f.setdefault("vaccini_doc", {}).setdefault(ag["pid"], []).extend(ag["vaccini_doc"])
            if ag["allergie"]:
                lista = f.setdefault("allergie", {}).setdefault(ag["pid"], [])
                lista.extend(x for x in ag["allergie"] if x.lower() not in {y.lower() for y in lista})
    riepilogo["pid_nuovi"] = [ag["pid"] for ag in aggiunte]
    return nuovi_file, modifica, riepilogo


# ---------------------------------------------------------------------------------------------------------------------
# Annotazioni: note del destinatario, separate dai documenti originali
# ---------------------------------------------------------------------------------------------------------------------
def tr_aggiungi_annotazione(f, tipo, rec_id, testo, autore, oggi=None):
    for rec in f.get(tipo, []):
        if rec.get("id") == rec_id:
            rec.setdefault("annotazioni", []).append({"data": (oggi or date.today()).isoformat(), "testo": testo.strip()[:1500], "da": autore})
            return True
    return False


def tr_annotazioni_ui(tipo, rec_id, chiave):
    """Le annotazioni di una voce (documento, prescrizione, visita, medicinale): si vedono e se ne aggiungono, senza toccare i file originali."""
    f = _fa_dati()
    rec = next((r for r in f.get(tipo, []) if r.get("id") == rec_id), None)
    if rec is None:
        return
    note = rec.get("annotazioni") or []
    orig = (rec.get("origine") or {}).get("da")
    if orig:
        st.caption(f"📥 Ricevuto da **{orig}**. I file originali restano invariati: puoi correggere i dati scritti e aggiungere annotazioni.")
    with st.expander(f"📝 Annotazioni ({len(note)})", expanded=False):
        for n in sorted(note, key=lambda x: x.get("data", ""), reverse=True):
            st.markdown(f"**{n.get('data', '')[8:10]}/{n.get('data', '')[5:7]}/{n.get('data', '')[:4]}** · {n.get('da', '')}: {n.get('testo', '')}")
        testo = st.text_area("Aggiungi un'annotazione", key=f"tr_nota_{chiave}", height=80, placeholder="Scrivi qui: non cambia il documento originale.")
        if st.button("Aggiungi l'annotazione", key=f"tr_nota_btn_{chiave}", width="stretch", disabled=not testo.strip()):
            autore = st.session_state.get("sess", {}).get("nome", "")
            _fa_salva(lambda f_: tr_aggiungi_annotazione(f_, tipo, rec_id, testo, autore), "Salute: annotazione")
            st.session_state.pop(f"tr_nota_{chiave}", None)
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# Schermate
# ---------------------------------------------------------------------------------------------------------------------
def _tr_leggi_file(i):
    try:
        d = carica_dati(crea_archivio(), _fa_percorso_doc(i))
        return (d.get("nome") or "file", d.get("mime") or "application/octet-stream", base64.b64decode(d["b64"])) if d.get("b64") else None
    except Exception:
        return None


def _tr_scrivi_file(nid, nome, mime, dati):
    corpo = {"nome": nome, "mime": mime, "b64": base64.b64encode(dati).decode()}
    salva_file(_fa_percorso_doc(nid), lambda d, c=corpo: d.update(c), "Salute: documento importato")


def _tr_etichetta(cat, rec, nomi_med=None):
    if cat == "medicinali":
        return rec.get("nome", "")
    if cat == "terapie":
        return f"Terapia {(nomi_med or {}).get(rec.get('med')) or rec.get('nome_med') or ''}".strip()
    if cat == "prescrizioni":
        return f"{rec.get('tipo', '')} {(rec.get('prescritto') or '')[:30]} ({rec.get('data', '')})".strip()
    if cat == "visite":
        return f"{rec.get('categoria', '')} {rec.get('data', '')}".strip()
    if cat == "vaccinazioni":
        return f"{rec.get('nome', '')} {rec.get('data', '')}".strip()
    return f"{rec.get('tipo', '')} {rec.get('numero', '')}".strip()


def _tr_esporta():
    f = _fa_dati()
    profili = _fa_profili(f)
    nomi = {p["id"]: p["nome"] for p in profili}
    sess = st.session_state.get("sess", {})
    st.markdown("**1️⃣ Chi sei, per chi riceve**")
    mitt = st.text_input("Il tuo nome nel file", value=sess.get("nome", ""), key="tr_mitt", help="È il nome che vedrà chi riceve il file.")
    st.markdown("**2️⃣ Cosa vuoi mandare**")
    modo = st.radio("Cosa esportare", ["Tutto", "Solo alcune categorie", "Scelgo io le singole voci"], key="tr_modo", label_visibility="collapsed")
    pids = st.multiselect("Di quali persone", list(nomi), default=list(nomi), format_func=lambda p: nomi[p], key="tr_persone")
    categorie = list(TR_CATEGORIE)
    if modo != "Tutto":
        categorie = st.multiselect("Quali categorie", list(TR_CATEGORIE), default=list(TR_CATEGORIE), format_func=lambda c: TR_CATEGORIE[c], key="tr_cat")
    selezione = None
    nomi_med = {m["id"]: m.get("nome", "") for m in f.get("medicinali", [])}
    if modo == "Scelgo io le singole voci":
        selezione = {}
        for cat in [c for c in categorie if c in _TR_CON_RECORD]:
            voci = [x for x in f.get(cat, []) if x.get("profilo", "p0") in pids]
            if voci:
                scelte = st.multiselect(TR_CATEGORIE[cat], [x["id"] for x in voci], default=[x["id"] for x in voci], key=f"tr_sel_{cat}",
                                        format_func=lambda i, voci=voci, cat=cat: next((f"{_tr_etichetta(cat, x, nomi_med)} · {nomi.get(x.get('profilo', 'p0'), '')}" for x in voci if x["id"] == i), i))
                selezione[cat] = set(scelte)
            else:
                selezione[cat] = set()
    includi = st.checkbox("Includi foto e PDF originali", value=True, key="tr_file")
    st.markdown("**3️⃣ Proteggi il file**")
    pw = pw2 = ""
    if tr_cifra_disponibile():
        pw = st.text_input("Password (consigliata)", type="password", key="tr_pw", help="Il file si apre solo con questa password.")
        if pw:
            pw2 = st.text_input("Ripeti la password", type="password", key="tr_pw2")
        st.caption("Dai la password al destinatario **a voce o con un altro messaggio**, non insieme al file.")
    else:
        st.warning("Questa app non può proteggere il file con una password (manca la libreria di cifratura).")
    st.markdown("**4️⃣ Consenso**")
    consenso = st.checkbox(TR_TESTO_CONSENSO, key="tr_consenso")
    problema = ""
    if not pids:
        problema = "Scegli almeno una persona."
    elif pw and pw != pw2:
        problema = "Le due password non sono uguali."
    elif not mitt.strip():
        problema = "Scrivi il tuo nome."
    elif not consenso:
        problema = "Per creare il file serve il consenso."
    if st.button("📦 Crea il file da inviare", type="primary", width="stretch", key="tr_crea", disabled=bool(problema)):
        with st.spinner("Preparo il file…"):
            payload = tr_raccogli(f, pids, categorie, selezione, includi)
            file_map, mancanti = {}, []
            for i in (tr_id_file(payload) if includi else []):
                r = _tr_leggi_file(i)
                if r:
                    file_map[i] = r
                else:
                    mancanti.append(i)
            dati = tr_crea_pacchetto(payload, file_map, mitt.strip(), hashlib.sha256(("dispensa|" + str(sess.get("uid", mitt))).encode()).hexdigest()[:16], pw or None)
        st.session_state["tr_pronto"] = {"dati": dati, "conteggi": tr_conteggi(payload), "file": len(file_map), "mancanti": len(mancanti), "cifrato": bool(pw),
                                         "nome": f"dispensa_{re.sub(r'[^A-Za-z0-9]+', '_', mitt.strip())}_{date.today().isoformat()}.dispensa"}
    elif problema:
        st.caption("⚠️ " + problema)
    pronto = st.session_state.get("tr_pronto")
    if pronto:
        c = pronto["conteggi"]
        st.success("✅ File pronto: " + " · ".join(f"{TR_CATEGORIE[k]} {n}" for k, n in c.items() if n) + f" · {pronto['file']} allegati · {len(pronto['dati']) // 1024} KB"
                   + (" · 🔒 protetto da password" if pronto["cifrato"] else " · ⚠️ senza password"))
        if pronto["mancanti"]:
            st.warning(f"{pronto['mancanti']} allegati non sono stati trovati e non sono nel file.")
        st.download_button("⬇ Scarica il file (.dispensa)", pronto["dati"], file_name=pronto["nome"], mime="application/octet-stream", key="tr_dl", width="stretch")
        st.markdown("**Come mandarlo:** scarica il file e invialo per email o Telegram; per WhatsApp usa la graffetta 📎 e scegli «Documento».")
        if "inv_canali" in globals():
            with st.expander("✉️ Invia da qui (email o Telegram)"):
                inv_canali("trasf", "File di trasferimento della dispensa", f"Ti mando i miei dati per «La nostra dispensa»: apri l'app, vai in Salute → Trasferisci dati → Importa."
                           + (" Il file è protetto: ti dirò la password a parte." if pronto["cifrato"] else ""),
                           [(pronto["nome"], "application/octet-stream", pronto["dati"])], oggetto="Dati per La nostra dispensa")


def _tr_importa():
    f = _fa_dati()
    st.markdown("**1️⃣ Scegli il file ricevuto** (si chiama «….dispensa»)")
    up = st.file_uploader("File di trasferimento", key="tr_up", label_visibility="collapsed")
    if up is None:
        st.caption("Salva prima sul telefono il file che ti hanno mandato, poi sceglilo qui.")
        return
    dati_file = up.getvalue()
    pw = None
    if tr_e_cifrato(dati_file):
        pw = st.text_input("🔒 Il file è protetto: scrivi la password", type="password", key="tr_pw_imp")
        if not pw:
            return
    try:
        with st.spinner("Controllo il file…"):
            pacchetto = tr_apri(dati_file, pw)
    except TrErrore as e:
        st.error(f"⚠️ {e}")
        return
    except Exception:
        st.error("⚠️ Non riesco a leggere il file: potrebbe essere danneggiato.")
        return
    man, payload = pacchetto["manifest"], pacchetto["payload"]
    mitt = (man.get("mittente") or {}).get("nome", "sconosciuto")
    st.success("✅ File controllato: formato riconosciuto e integrità verificata (nessuna parte è stata alterata).")
    st.markdown(f"**Da:** {mitt}  \n**Creato il:** {str(man.get('creato', ''))[:10]}  \n**Persone:** {', '.join(p.get('nome', '') for p in payload['persone'])}")
    c = tr_conteggi(payload)
    st.caption(" · ".join(f"{TR_CATEGORIE[k]} {n}" for k, n in c.items() if n) + f" · {len(pacchetto['files'])} allegati")
    st.markdown("**2️⃣ Consenso**")
    ok = st.checkbox(f"Ho ricevuto questi dati da {mitt} e voglio importarli come nuova scheda.", key="tr_ok_imp")
    salta = st.checkbox("Se li ho già importati, salta i duplicati (consigliato)", value=True, key="tr_salta")
    st.caption("Non si sovrascrive niente: i dati arrivano in una scheda separata con il nome della persona. Foto e PDF restano originali; i dati scritti si possono correggere.")
    if st.button("📥 Importa", type="primary", width="stretch", key="tr_importa_btn", disabled=not ok):
        salvati = []
        try:
            with st.spinner("Importo…"):
                nuovi_file, modifica, riepilogo = tr_costruisci_import(f, pacchetto, salta)
                for nid, (nome, mime, b, _sha_) in nuovi_file.items():
                    _tr_scrivi_file(nid, nome, mime, b)
                    salvati.append(nid)
                _fa_salva(modifica, f"Salute: importati dati da {mitt}")
        except Exception as e:
            try:
                _fa_cancella_files(salvati)
            except Exception:
                pass
            st.error(f"Non sono riuscito a importare: {e}. Non è stato cambiato niente.")
            return
        st.session_state["tr_esito"] = riepilogo
        if riepilogo["pid_nuovi"]:
            st.session_state["fa_profilo"] = riepilogo["pid_nuovi"][0]
        st.rerun()
    esito = st.session_state.get("tr_esito")
    if esito:
        st.success("✅ Importato. " + (f"Nuove schede: {', '.join(esito['profili_nuovi'])}. " if esito["profili_nuovi"] else "")
                   + (f"Aggiornate: {', '.join(esito['profili_aggiornati'])}. " if esito["profili_aggiornati"] else "")
                   + " · ".join(f"{TR_CATEGORIE[k]} {n}" for k, n in esito["importati"].items() if n) + (f" · già presenti e saltati: {esito['saltati']}" if esito["saltati"] else "")
                   + (f" · ⚠️ non importate perché incomplete: {esito['scartati']}" if esito.get("scartati") else ""))
        st.button("Apri Salute", key="tr_apri_salute", width="stretch", on_click=nav_vai, args=("salute",))


def schermata_trasferimento():
    st.button("← Salute", key="tr_indietro", on_click=nav_vai, args=("salute",))
    st.markdown("<div style='background:linear-gradient(135deg,#00695c 0%,#26a69a 60%,#80cbc4 100%);color:#fff;padding:20px 24px;border-radius:24px;margin:6px 0 12px;"
                "box-shadow:0 10px 30px rgba(0,0,0,.15)'><h1 style='margin:0;font-size:1.8rem;color:#fff;padding:0'>🔁 Trasferisci dati</h1>"
                "<p style='margin:4px 0 0;opacity:.92'>Manda i tuoi dati a un'altra persona, o importa quelli che hai ricevuto</p></div>", unsafe_allow_html=True)
    st.info("🔒 Sono **dati personali e sanitari**: mandali solo a chi conosci e, se puoi, proteggi il file con una password.")
    t1, t2 = st.tabs(["📤 Esporta", "📥 Importa"])
    with t1:
        _tr_esporta()
    with t2:
        _tr_importa()


def trasferimento_pulsante(dove):
    st.button("🔁 Trasferisci dati (esporta e importa)", key=f"tr_apri_{dove}", width="stretch", on_click=nav_vai, args=("trasferimento",))
