# -*- coding: utf-8 -*-
"""ANIMALI · ESPORTA TUTTO E IMPORTA — l'intera vita documentale e sanitaria di un animale (o di tutti) in UN file, da dare a un altro utente della stessa app.

IL PACCHETTO (file ZIP compresso, estensione .zip; si riconosce dal contenuto, non dal nome):
  manifest.json   formato «dispensa-animali», versione, data, chi lo ha creato, elenco animali, conteggi, e per OGNI file: percorso, SHA-256, dimensione (+ SHA-256 dei dati)
  dati.json       i dati strutturati: animali, vaccinazioni, visite, esami, terapie, interventi, patologie, allergie, pesi, diario, spese, contatti, agenda, documenti (con i testi letti)
  files/…         le foto (principale e galleria) e i documenti originali, byte per byte identici
  LEGGIMI.txt     due righe per chi lo apre
  Facoltativo: protezione con password (stessa cifratura AES-GCM dello scambio dati: tr_cifra / tr_decifra).
IMPORTAZIONE: riconosce il pacchetto, controlla formato e versione, verifica l'INTEGRITÀ (SHA-256 di dati e file), mostra un RIEPILOGO e chiede conferma; permette di importare tutti gli animali,
uno solo, o solo alcune informazioni. Controlla i DUPLICATI (id d'origine, microchip, nome+specie) e chiede: importa come nuovo / aggiorna la scheda / unisci / non importare.
NON sostituisce e NON cancella mai nulla senza conferma. Ogni cosa importata porta la PROVENIENZA e la data dell'importazione. Se l'importazione si interrompe, i file rimasti a metà vengono tolti
(ripristino sicuro) e i dati non vengono toccati; un'importazione finita si può ANNULLARE (tolte solo le cose aggiunte da lei).
Caricato dopo animali_report.py."""
import copy
import hashlib
import io
import json
import re
import uuid
import zipfile
from datetime import datetime

import streamlit as st

AN_PACCHETTO_FORMATO = "dispensa-animali"
AN_PACCHETTO_VERSIONE = 1
_AN_MAX_PACCHETTO = 300 * 1024 * 1024
_AN_MAX_FILE_PACCHETTO = 3000
_AN_CATEGORIE_SOTTO = ["vaccini", "visite", "terapie", "esami", "interventi", "patologie", "allergie", "peso", "diario", "spese", "agenda", "documenti", "contatti"]
AN_NOMI_CATEGORIA = {"vaccini": "💉 Vaccinazioni", "visite": "🩺 Visite", "terapie": "💊 Terapie", "esami": "🔬 Esami", "interventi": "🏥 Interventi e ricoveri", "patologie": "🩻 Patologie",
                     "allergie": "⚠️ Allergie", "peso": "⚖️ Pesi", "diario": "📔 Diario", "spese": "💶 Spese", "agenda": "📅 Agenda e promemoria", "documenti": "📂 Documenti", "contatti": "📇 Contatti"}
_AN_CAMPI_SCHEDA = ["nome", "specie", "razza", "sesso", "sterilizzato", "nascita", "colore", "microchip", "tatuaggio", "passaporto", "pedigree", "note"]
_AN_FIRMA = {"vaccini": ("nome", "data"), "visite": ("data", "motivo"), "terapie": ("farmaco", "dal"), "esami": ("data", "tipo"), "interventi": ("data", "tipo", "descrizione"),
             "patologie": ("nome", "dal"), "allergie": ("sostanza",), "peso": ("data", "kg"), "diario": ("data", "testo"), "spese": ("data", "voce", "importo"), "agenda": ("data", "titolo"),
             "documenti": ("sha_primo",), "contatti": ("nome", "tel")}


class AnErrore(Exception):
    """Un problema spiegabile all'utente (file non valido, password errata, versione troppo nuova…)."""


# ---------------------------------------------------------------------------------------------------------------------
# ESPORTARE
# ---------------------------------------------------------------------------------------------------------------------
def _an_riferimenti_file(a, ids_animali):
    """Tutti i riferimenti ai file usati dagli animali scelti: {id_file: rif}."""
    out = {}
    for x in an_animali(a):
        if x["id"] not in ids_animali:
            continue
        for r in ([x.get("foto")] if x.get("foto") else []) + list(x.get("galleria") or []):
            if isinstance(r, dict) and r.get("id"):
                out[r["id"]] = r
    for d_ in an_voci(a, "documenti"):
        if d_.get("animale") in ids_animali:
            for r in d_.get("allegati") or []:
                if isinstance(r, dict) and r.get("id"):
                    out[r["id"]] = r
    return out


def an_costruisci_pacchetto(a, ids_animali, includi_file=True, nome_utente=""):
    """(byte dello ZIP, riepilogo). Il riepilogo dice cosa c'è dentro e se qualche file non si è trovato."""
    ids_animali = list(ids_animali)
    dati = {"formato": AN_PACCHETTO_FORMATO, "versione": AN_PACCHETTO_VERSIONE, "animali": [copy.deepcopy(x) for x in an_animali(a) if x["id"] in ids_animali]}
    for cat in _AN_CATEGORIE_SOTTO:
        if cat == "contatti":
            dati[cat] = [copy.deepcopy(r) for r in an_voci(a, cat)]
        else:
            dati[cat] = [copy.deepcopy(r) for r in an_voci(a, cat) if r.get("animale") in ids_animali]
    files, mancanti, buf_files = {}, [], {}
    if includi_file:
        for fid, rif in _an_riferimenti_file(a, set(ids_animali)).items():
            b = an_leggi_file(rif)
            if not b:
                mancanti.append(rif.get("nome") or fid)
                continue
            est = re.sub(r"[^a-z0-9]", "", (rif.get("nome") or "").rsplit(".", 1)[-1].lower())[:5] if "." in (rif.get("nome") or "") else ""
            percorso = f"files/{fid}" + (f".{est}" if est else "")
            buf_files[percorso] = b
            files[fid] = {"percorso": percorso, "sha256": hashlib.sha256(b).hexdigest(), "dimensione": len(b), "nome": rif.get("nome") or "file", "mime": rif.get("mime") or ""}
    else:                                                                       # senza file: le schede dei documenti restano, senza allegati
        for d_ in dati["documenti"]:
            d_["allegati"] = []
        for x in dati["animali"]:
            x.pop("foto", None)
            x["galleria"] = []
    dati_bytes = json.dumps(dati, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    conteggi = {"animali": len(dati["animali"])}
    conteggi.update({c: len(dati[c]) for c in _AN_CATEGORIE_SOTTO})
    conteggi["file"] = len(files)
    manifest = {"formato": AN_PACCHETTO_FORMATO, "versione": AN_PACCHETTO_VERSIONE, "creato": datetime.now().isoformat(timespec="seconds"), "app": "VitaMemo · Animali",
                "creato_da": nome_utente, "animali": [{"id": x["id"], "nome": x.get("nome"), "specie": x.get("specie"), "microchip": x.get("microchip")} for x in dati["animali"]],
                "conteggi": conteggi, "file": files, "dati_sha256": hashlib.sha256(dati_bytes).hexdigest(), "file_non_trovati": mancanti, "con_file": bool(includi_file)}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        z.writestr("dati.json", dati_bytes)
        for p, b in buf_files.items():
            z.writestr(p, b)
        z.writestr("LEGGIMI.txt", "Archivio ANIMALI dell'app VitaMemo.\nPer usarlo: apri l'app → Animali → «Importa archivio animale» e scegli questo file.\n"
                                  "Contiene dati e documenti sanitari: condividilo solo con chi deve riceverlo.\n")
    return buf.getvalue(), {"conteggi": conteggi, "mancanti": mancanti, "dimensione": len(buf.getvalue()), "nomi": [x.get("nome") for x in dati["animali"]]}


def an_proteggi_pacchetto(zip_bytes, password):
    """Con password: lo stesso involucro cifrato dello scambio dati (AES-GCM, chiave da scrypt)."""
    if not password:
        return zip_bytes
    if "tr_cifra" not in globals() or not tr_cifra_disponibile():
        raise AnErrore("La cifratura non è disponibile su questo server: crea il file senza password.")
    return tr_cifra(zip_bytes, password)


# ---------------------------------------------------------------------------------------------------------------------
# APRIRE E VERIFICARE
# ---------------------------------------------------------------------------------------------------------------------
def _an_pulisci(v, prof=0):
    """Dati importati: solo tipi semplici, testi limitati, niente strutture strane."""
    if prof > 6:
        return None
    if isinstance(v, str):
        return v[:20000]
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    if isinstance(v, list):
        return [_an_pulisci(z, prof + 1) for z in v[:3000]]
    if isinstance(v, dict):
        return {str(k)[:60]: _an_pulisci(z, prof + 1) for k, z in list(v.items())[:200]}
    return None


def an_apri_pacchetto(dati_file, password=None):
    """Legge e VERIFICA un pacchetto. Ritorna {'manifest', 'dati', 'files': {id: byte}, 'danneggiati': [nomi], 'mancanti': [nomi]}. Solleva AnErrore con un messaggio chiaro."""
    if not dati_file:
        raise AnErrore("Il file è vuoto.")
    if dati_file[:4] == b"DSP1":
        raise AnErrore("Questo è un file di scambio dati di Salute/Casa/Lavoro, non un archivio Animali. Aprilo da Utilità → «Scambia i dati con un altro utente».")
    if "tr_e_cifrato" in globals() and tr_e_cifrato(dati_file):
        if not password:
            raise AnErrore("PASSWORD")
        try:
            dati_file = tr_decifra(dati_file, password)
        except Exception as ex:
            raise AnErrore(str(ex) or "La password non è giusta, oppure il file è danneggiato.")
    if not zipfile.is_zipfile(io.BytesIO(dati_file)):
        raise AnErrore("Il file non è un archivio Animali (non è un pacchetto compresso valido). Potrebbe essere danneggiato o incompleto.")
    try:
        z = zipfile.ZipFile(io.BytesIO(dati_file))
        info = z.infolist()
        if len(info) > _AN_MAX_FILE_PACCHETTO or sum(i.file_size for i in info) > _AN_MAX_PACCHETTO:
            raise AnErrore("Il pacchetto è troppo grande o ha troppi file.")
        nomi = set(z.namelist())
        if "manifest.json" not in nomi or "dati.json" not in nomi:
            raise AnErrore("Questo file non è un archivio Animali di questa app (mancano le parti principali).")
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        if manifest.get("formato") != AN_PACCHETTO_FORMATO:
            raise AnErrore("Questo file non è un archivio Animali di questa app (formato non riconosciuto).")
        try:
            vers = int(manifest.get("versione") or 0)
        except (ValueError, TypeError):
            vers = 0
        if vers < 1:
            raise AnErrore("Versione del pacchetto non valida.")
        if vers > AN_PACCHETTO_VERSIONE:
            raise AnErrore(f"Il pacchetto è stato creato con una versione più nuova dell'app (versione {vers}): aggiorna l'app e riprova.")
        dati_bytes = z.read("dati.json")
        if hashlib.sha256(dati_bytes).hexdigest() != manifest.get("dati_sha256"):
            raise AnErrore("Il file è DANNEGGIATO: i dati non corrispondono al controllo di integrità. Chiedi di mandarlo di nuovo.")
        dati = json.loads(dati_bytes.decode("utf-8"))
        files, danneggiati, mancanti = {}, [], []
        for fid, m in (manifest.get("file") or {}).items():
            try:
                p = m["percorso"]
                if p not in nomi:
                    mancanti.append(m.get("nome") or fid)
                    continue
                b = z.read(p)
                if hashlib.sha256(b).hexdigest() != m.get("sha256") or len(b) != m.get("dimensione"):
                    danneggiati.append(m.get("nome") or fid)
                    continue
                files[fid] = b
            except (KeyError, zipfile.BadZipFile, RuntimeError):
                danneggiati.append((m or {}).get("nome") or fid)
    except AnErrore:
        raise
    except (zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError, KeyError, ValueError) as ex:
        raise AnErrore(f"Il file è danneggiato o incompleto ({type(ex).__name__}).")
    dati = _an_pulisci(dati)
    pul = {"animali": [x for x in (dati.get("animali") or []) if isinstance(x, dict) and re.fullmatch(r"[\w-]{1,40}", str(x.get("id") or ""))]}
    for cat in _AN_CATEGORIE_SOTTO:
        pul[cat] = [r for r in (dati.get(cat) or []) if isinstance(r, dict) and re.fullmatch(r"[\w-]{1,40}", str(r.get("id") or ""))]
    if not pul["animali"]:
        raise AnErrore("Il pacchetto non contiene nessun animale.")
    return {"manifest": manifest, "dati": pul, "files": files, "danneggiati": danneggiati, "mancanti": mancanti}


# ---------------------------------------------------------------------------------------------------------------------
# DUPLICATI
# ---------------------------------------------------------------------------------------------------------------------
def an_cerca_duplicati(a, x_imp):
    """[(animale esistente, forza 'sicuro'|'possibile', motivo)] per un animale del pacchetto."""
    out = []
    chip = an_solo_cifre(x_imp.get("microchip"))
    for e in an_animali(a):
        motivi = []
        forte = False
        if e["id"] == x_imp.get("id") or (e.get("origine") or {}).get("id_origine") == x_imp.get("id") or (x_imp.get("origine") or {}).get("id_origine") == e["id"]:
            motivi.append("è lo stesso animale già importato o esportato da qui")
            forte = True
        if chip and len(chip) >= 10 and an_solo_cifre(e.get("microchip")) == chip:
            motivi.append(f"stesso microchip ({chip})")
            forte = True
        if not forte:
            if an_norm(e.get("nome")) == an_norm(x_imp.get("nome")) and an_norm(e.get("specie")) == an_norm(x_imp.get("specie")):
                motivi.append("stesso nome e stessa specie" + (" e stessa data di nascita" if e.get("nascita") and e.get("nascita") == x_imp.get("nascita") else ""))
        if motivi:
            out.append((e, "sicuro" if forte else "possibile", ", ".join(motivi)))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# IMPORTARE
# ---------------------------------------------------------------------------------------------------------------------
def _an_firma(cat, r, files_sha):
    """L'«impronta» di una voce (per riconoscere che c'è già): categoria + ANIMALE + i campi che la identificano."""
    chiavi = _AN_FIRMA.get(cat, ("id",))
    if cat == "documenti":
        att = (r.get("allegati") or [{}])[0] if r.get("allegati") else {}
        return ("documenti", r.get("animale") or "", att.get("sha") or files_sha.get(att.get("id"), "") or an_norm(r.get("titolo")), r.get("data") or "")
    return (cat, r.get("animale") or "") + tuple(an_norm(r.get(k)) for k in chiavi)


def an_riepilogo_import(pacchetto, a):
    """Per ogni animale del pacchetto: conteggi e duplicati (per la schermata di conferma)."""
    d = pacchetto["dati"]
    out = []
    for x in d["animali"]:
        c = {cat: sum(1 for r in d[cat] if r.get("animale") == x["id"]) for cat in _AN_CATEGORIE_SOTTO if cat != "contatti"}
        n_file = len([1 for r in d["documenti"] if r.get("animale") == x["id"] for al in (r.get("allegati") or []) if al.get("id") in pacchetto["files"]])
        n_file += len([1 for al in ([x.get("foto")] if x.get("foto") else []) + list(x.get("galleria") or []) if isinstance(al, dict) and al.get("id") in pacchetto["files"]])
        out.append({"animale": x, "conteggi": c, "n_file": n_file, "duplicati": an_cerca_duplicati(a, x)})
    return out


def _an_nuovo_rif(rif, mappa_file, files_sha):
    """Il riferimento file con il nuovo id; None se il file non c'è (non incluso o danneggiato)."""
    if not isinstance(rif, dict) or rif.get("id") not in mappa_file:
        return None
    n = dict(rif)
    n["id"] = mappa_file[rif["id"]]
    return n


def an_applica_import(pacchetto, scelte, nome_pacchetto=""):
    """Esegue l'importazione. scelte = {'animali': {id_origine: {'azione': 'nuovo'|'aggiorna'|'unisci'|'salta', 'target': id esistente}}, 'categorie': [..], 'con_file': bool}.
    Ordine sicuro: 1) registro «in corso» (con i file previsti) 2) salvataggio dei file 3) UN solo salvataggio dei dati (tutto o niente) che chiude il registro.
    Se qualcosa va storto prima del punto 3 i file vengono tolti e i dati restano com'erano. Ritorna il riassunto dell'importazione."""
    d = pacchetto["dati"]
    categorie = [c for c in (scelte.get("categorie") or []) if c in _AN_CATEGORIE_SOTTO]
    scelti = {sid: s for sid, s in (scelte.get("animali") or {}).items() if s.get("azione") in ("nuovo", "aggiorna", "unisci")}
    if not scelti:
        raise AnErrore("Non hai scelto nessun animale da importare.")
    imp_id = an_nuovo_id()
    ora = _an_adesso()
    da = (pacchetto["manifest"].get("creato_da") or "").strip() or "un altro utente"
    # --- quali file servono
    ref_necessari = {}
    for sid in scelti:
        x = next((z for z in d["animali"] if z["id"] == sid), None)
        if not x:
            continue
        for r in ([x.get("foto")] if x.get("foto") else []) + list(x.get("galleria") or []):
            if isinstance(r, dict) and r.get("id") in pacchetto["files"]:
                ref_necessari[r["id"]] = r
        if "documenti" in categorie:
            for dd in d["documenti"]:
                if dd.get("animale") == sid:
                    for r in dd.get("allegati") or []:
                        if isinstance(r, dict) and r.get("id") in pacchetto["files"]:
                            ref_necessari[r["id"]] = r
    if not scelte.get("con_file", True):
        ref_necessari = {}
    a0 = an_dati()
    # file già presenti (stesso contenuto) in un animale di destinazione: non si duplicano
    sha_esistenti = {}
    for dd in an_voci(a0, "documenti"):
        for r in dd.get("allegati") or []:
            if r.get("sha"):
                sha_esistenti.setdefault((dd.get("animale"), r["sha"]), r)
    for x_ in an_animali(a0):
        for r_ in ([x_.get("foto")] if x_.get("foto") else []) + list(x_.get("galleria") or []):
            if isinstance(r_, dict) and r_.get("sha"):
                sha_esistenti.setdefault((x_["id"], r_["sha"]), r_)
    mappa_file, da_creare = {}, []
    for fid, r in ref_necessari.items():
        sha = hashlib.sha256(pacchetto["files"][fid]).hexdigest()
        riusa = None
        for sid, s in scelti.items():
            if s["azione"] in ("aggiorna", "unisci") and s.get("target"):
                riusa = riusa or sha_esistenti.get((s["target"], sha))
        if riusa:
            mappa_file[fid] = riusa["id"]
        else:
            mappa_file[fid] = uuid.uuid4().hex[:12]
            da_creare.append(fid)
    nuovi_ids = [mappa_file[f] for f in da_creare]
    sessione = st.session_state.setdefault("_an_sessione", uuid.uuid4().hex[:10])

    def _apri_registro(a):
        a["import"].append({"id": imp_id, "quando": ora, "da": da, "pacchetto": nome_pacchetto, "stato": "in corso", "file_creati": nuovi_ids, "sessione": sessione, "iniziata": ora})
    an_salva(_apri_registro, "Animali: importazione avviata")
    creati_files = []
    try:
        for fid in da_creare:
            r = ref_necessari[fid]
            b = pacchetto["files"][fid]
            nid = mappa_file[fid]
            corpo = {"nome": r.get("nome") or "file", "mime": r.get("mime") or an_mime_da_nome(r.get("nome"), b), "b64": __import__("base64").b64encode(b).decode()}
            salva_file(an_percorso_file(nid), lambda dd, c=corpo: dd.update(c), "Animali: file importato")
            creati_files.append(nid)
        files_sha = {fid: hashlib.sha256(b).hexdigest() for fid, b in pacchetto["files"].items()}
        riassunto = {"animali_nuovi": [], "animali_aggiornati": [], "creati": {}, "saltati": 0}
        prima = {}

        def _applica(a):
            mappa_id = {}
            prov = {"tipo": "importato", "da": da, "pacchetto": nome_pacchetto, "importato_il": ora, "import_id": imp_id}
            for sid, s in scelti.items():
                xi = next((z for z in d["animali"] if z["id"] == sid), None)
                if not xi:
                    continue
                if s["azione"] == "nuovo":
                    nid = uuid.uuid4().hex[:12]
                    x = {k: copy.deepcopy(xi.get(k)) for k in _AN_CAMPI_SCHEDA + ["proprietario", "alimentazione", "habitat"] if xi.get(k) not in (None, "")}
                    x.update({"id": nid, "creato": ora, "agg": ora, "origine": dict(prov, id_origine=sid)})
                    f_ = _an_nuovo_rif(xi.get("foto"), mappa_file, files_sha)
                    if f_:
                        x["foto"] = f_
                    x["galleria"] = [g for g in (_an_nuovo_rif(r, mappa_file, files_sha) for r in (xi.get("galleria") or [])) if g]
                    a["lista"].append(x)
                    riassunto["animali_nuovi"].append(nid)
                    mappa_id[sid] = nid
                else:
                    tid = s.get("target")
                    x = an_trova(a, tid)
                    if x is None:
                        raise AnErrore("L'animale da aggiornare non esiste più.")
                    prima[tid] = copy.deepcopy(x)
                    for k in _AN_CAMPI_SCHEDA:
                        nuovo = xi.get(k)
                        if nuovo in (None, ""):
                            continue
                        if s["azione"] == "aggiorna":
                            if k == "note" and x.get(k) and x.get(k) != nuovo:
                                x[k] = x[k] + "\n— dall'archivio importato: " + str(nuovo)
                            else:
                                x[k] = nuovo
                        elif x.get(k) in (None, ""):
                            x[k] = nuovo
                        elif k == "note" and x.get(k) != nuovo and str(nuovo) not in str(x.get(k)):
                            x[k] = str(x[k]) + "\n— dall'archivio importato: " + str(nuovo)
                    for blocco in ("proprietario", "alimentazione", "habitat"):
                        for k, v in (xi.get(blocco) or {}).items():
                            if v in (None, ""):
                                continue
                            cur = x.setdefault(blocco, {})
                            if s["azione"] == "aggiorna" or cur.get(k) in (None, ""):
                                cur[k] = v
                    f_ = _an_nuovo_rif(xi.get("foto"), mappa_file, files_sha)
                    if f_:
                        if not x.get("foto"):
                            x["foto"] = f_
                        elif x["foto"].get("sha") != f_.get("sha"):
                            if s["azione"] == "aggiorna":                             # la vecchia foto non si perde: va in galleria
                                x.setdefault("galleria", []).append(x["foto"])
                                x["foto"] = f_
                            else:
                                x.setdefault("galleria", []).append(f_)
                    gia = {g.get("sha") for g in x.get("galleria") or []} | {(x.get("foto") or {}).get("sha")}
                    for r in xi.get("galleria") or []:
                        g = _an_nuovo_rif(r, mappa_file, files_sha)
                        if g and g.get("sha") not in gia:
                            x.setdefault("galleria", []).append(g)
                            gia.add(g.get("sha"))
                    x["agg"] = ora
                    x.setdefault("storia_importazioni", []).append({"import_id": imp_id, "quando": ora, "da": da, "azione": s["azione"]})
                    riassunto["animali_aggiornati"].append(tid)
                    mappa_id[sid] = tid
            # --- le voci (i documenti prima, perché le altre voci ne citano l'id)
            for cat in ["documenti"] + [c for c in categorie if c not in ("documenti",)]:
                if cat not in categorie:
                    continue
                esistenti = {_an_firma(cat, r, {}) for r in a[cat]}
                for r in d[cat]:
                    if cat == "contatti":
                        dest = ""
                    else:
                        if r.get("animale") not in mappa_id:
                            continue
                        dest = mappa_id[r["animale"]]
                    n = copy.deepcopy(r)
                    n["id"] = uuid.uuid4().hex[:12]
                    mappa_id[r["id"]] = n["id"]
                    n["animale"] = dest
                    if cat == "documenti":
                        n["allegati"] = [z for z in (_an_nuovo_rif(al, mappa_file, files_sha) for al in (r.get("allegati") or [])) if z]
                        if r.get("allegati") and not n["allegati"]:
                            n["mancanti"] = list(n.get("mancanti") or []) + ["Il file originale non è stato incluso nel pacchetto: restano solo i dati letti."]
                    if n.get("doc"):
                        n["doc"] = mappa_id.get(n["doc"], "")
                    n["origine"] = dict(prov, id_origine=r["id"])
                    n["agg"] = ora
                    n.setdefault("creato", ora)
                    sig = _an_firma(cat, n, {})
                    if sig in esistenti and cat != "documenti":
                        riassunto["saltati"] += 1
                        mappa_id.pop(r["id"], None)
                        continue
                    if cat == "documenti" and sig in esistenti:
                        riassunto["saltati"] += 1
                        mappa_id.pop(r["id"], None)
                        continue
                    esistenti.add(sig)
                    a[cat].append(n)
                    riassunto["creati"].setdefault(cat, []).append(n["id"])
            for g in a["import"]:
                if g.get("id") == imp_id:
                    g.update({"stato": "completata", "completata": ora, "animali_creati": riassunto["animali_nuovi"], "animali_modificati": prima, "creati": riassunto["creati"],
                              "file_creati": nuovi_ids, "saltati": riassunto["saltati"]})
            a["import"] = a["import"][-12:]
        an_salva(_applica, "Animali: importazione completata")
    except Exception as ex:
        an_cancella_file(creati_files or nuovi_ids)                                # ripristino: via i file messi a metà; i dati non sono stati toccati

        def _chiudi(a):
            for g in a["import"]:
                if g.get("id") == imp_id:
                    g.update({"stato": "fallita e ripristinata", "errore": str(ex)[:200]})
        try:
            an_salva(_chiudi, "Animali: importazione fallita")
        except Exception:
            pass
        if isinstance(ex, AnErrore):
            raise
        raise AnErrore(f"L'importazione non è riuscita ({type(ex).__name__}): non è stato cambiato nulla e i file rimasti a metà sono stati tolti. Riprova.")
    a2 = an_dati()
    in_uso = {r.get("id") for dd in a2.get("documenti") or [] for r in dd.get("allegati") or []} | {r.get("id") for x_ in an_animali(a2) for r in ([x_.get("foto")] if x_.get("foto") else []) + list(x_.get("galleria") or []) if isinstance(r, dict)}
    orfani = [i_ for i_ in nuovi_ids if i_ not in in_uso]
    if orfani:                                                                   # file messi nell'archivio ma non usati da nessuna voce (voce già presente): si tolgono
        an_cancella_file(orfani)
    usati = [i_ for i_ in nuovi_ids if i_ in in_uso]

    def _agg_reg(a):
        for g in a["import"]:
            if g.get("id") == imp_id:
                g["file_creati"] = usati
    try:
        an_salva(_agg_reg, "Animali: registro importazione")
    except Exception:
        pass
    riassunto["import_id"] = imp_id
    riassunto["file_creati"] = len(usati)
    return riassunto


def an_ripristina_interrotte():
    """Se un'importazione si è interrotta a metà (ancora «in corso» da più di 5 minuti): toglie i file rimasti e la segna come ripristinata. Ritorna quanti file ha tolto."""
    a = an_dati()
    adesso_ = datetime.now()
    da_fare = []
    for g in a.get("import") or []:
        if g.get("stato") == "in corso":
            try:
                eta = (adesso_ - datetime.fromisoformat(str(g.get("iniziata") or g.get("quando")))).total_seconds()
            except ValueError:
                eta = 99999
            if eta > 300:
                da_fare.append(g)
    if not da_fare:
        return 0
    n = 0
    for g in da_fare:
        ids = list(g.get("file_creati") or [])
        in_uso = {r.get("id") for dd in a.get("documenti") or [] for r in dd.get("allegati") or []} | {r.get("id") for x in an_animali(a) for r in ([x.get("foto")] if x.get("foto") else []) + list(x.get("galleria") or []) if isinstance(r, dict)}
        ids = [i for i in ids if i not in in_uso]
        an_cancella_file(ids)
        n += len(ids)
    chiavi = {g["id"] for g in da_fare}

    def _m(a2):
        for g in a2["import"]:
            if g.get("id") in chiavi:
                g["stato"] = "interrotta e ripristinata"
    an_salva(_m, "Animali: importazione interrotta ripristinata")
    return n


def an_annulla_import(imp_id):
    """Toglie ciò che quell'importazione ha AGGIUNTO (animali nuovi, voci nuove, file) e rimette com'erano le schede aggiornate. Ritorna un riassunto."""
    a = an_dati()
    g = next((z for z in a.get("import") or [] if z.get("id") == imp_id), None)
    if not g or g.get("stato") != "completata":
        raise AnErrore("Questa importazione non si può annullare.")
    ids_file = list(g.get("file_creati") or [])
    tolti = {"voci": 0, "animali": 0}

    def _m(a2):
        creati = g.get("creati") or {}
        for cat, ids in creati.items():
            antes = len(a2[cat])
            a2[cat] = [r for r in a2[cat] if r.get("id") not in set(ids)]
            tolti["voci"] += antes - len(a2[cat])
        nuovi = set(g.get("animali_creati") or [])
        for k in AN_ORDINE_CATEGORIE[1:]:
            a2[k] = [r for r in a2[k] if r.get("animale") not in nuovi]
        antes = len(a2["lista"])
        a2["lista"] = [x for x in a2["lista"] if x.get("id") not in nuovi]
        tolti["animali"] = antes - len(a2["lista"])
        for tid, snap in (g.get("animali_modificati") or {}).items():
            for i, x in enumerate(a2["lista"]):
                if x.get("id") == tid:
                    a2["lista"][i] = snap
        for gg in a2["import"]:
            if gg.get("id") == imp_id:
                gg["stato"] = "annullata"
                gg["annullata"] = _an_adesso()
    an_salva(_m, "Animali: importazione annullata")
    a2 = an_dati()
    in_uso = {r.get("id") for dd in a2.get("documenti") or [] for r in dd.get("allegati") or []} | {r.get("id") for x in an_animali(a2) for r in ([x.get("foto")] if x.get("foto") else []) + list(x.get("galleria") or []) if isinstance(r, dict)}
    an_cancella_file([i for i in ids_file if i not in in_uso])
    return tolti


# ---------------------------------------------------------------------------------------------------------------------
# LE SCHERMATE
# ---------------------------------------------------------------------------------------------------------------------
def _an_conteggi_testo(c):
    nomi = {"animali": "animali", "vaccini": "vaccinazioni", "visite": "visite", "terapie": "terapie", "esami": "esami", "interventi": "interventi", "patologie": "patologie", "allergie": "allergie",
            "peso": "pesi", "diario": "note di diario", "spese": "spese", "agenda": "appuntamenti", "documenti": "documenti", "contatti": "contatti", "file": "file (foto e documenti)"}
    return ", ".join(f"{n} {nomi[k]}" for k, n in c.items() if n and k in nomi)


def _an_esporta_ui(a, x):
    st.markdown("#### 📦 Esporta tutto e condividi")
    st.caption("Crea **un solo file** con tutto: schede, foto, documenti originali, visite, terapie, spese, agenda. Chi lo riceve lo carica nella sua app con «Importa archivio animale» e ritrova tutto com'era.")
    animali = an_animali(a)
    scope_def = st.session_state.get("an_scope", "uno" if x else "tutti")
    scelte = ["uno", "tutti"] if len(animali) > 1 else ["uno"]
    scope = st.radio("Che cosa esporto?", scelte, index=scelte.index(scope_def) if scope_def in scelte else 0,
                     format_func=lambda s: (f"Solo {x.get('nome', '')}" if s == "uno" else f"Tutti gli animali ({len(animali)})"), key="an_exp_scope")
    includi = st.checkbox("Includi foto e documenti originali", value=True, key="an_exp_file")
    pw = st.text_input("Password per proteggere il file (facoltativa, consigliata: dentro ci sono dati sanitari)", type="password", key="an_exp_pw")
    if pw and "tr_cifra_disponibile" in globals() and not tr_cifra_disponibile():
        st.warning("La cifratura non è disponibile su questo server: il file sarà senza password.")
        pw = ""
    if st.button("📦 Prepara il pacchetto", type="primary", key="an_exp_go", width="stretch"):
        ids = [z["id"] for z in animali] if scope == "tutti" else [x["id"]]
        with st.spinner("Preparo e controllo il pacchetto…"):
            try:
                nome_ut = (st.session_state.get("sess") or {}).get("nome", "")
                zb, riep = an_costruisci_pacchetto(a, ids, includi, nome_ut)
                an_apri_pacchetto(zb)                                                  # prova di lettura: il file appena creato deve superare i suoi stessi controlli
                finale = an_proteggi_pacchetto(zb, pw)
                if pw:
                    an_apri_pacchetto(finale, pw)
            except AnErrore as ex:
                st.error(f"Non sono riuscito a creare il pacchetto: {ex}")
                return
        base = "Animali_" + (re.sub(r"[^A-Za-z0-9_-]+", "_", x.get("nome", "")) if scope == "uno" else "tutti") + "_" + _an_oggi().isoformat() + ".zip"
        st.session_state["an_exp_ris"] = {"dati": finale, "nome": base, "riep": riep, "pw": bool(pw)}
    r = st.session_state.get("an_exp_ris")
    if r:
        st.success(f"✅ Pacchetto pronto e controllato ({len(r['dati']) // 1024} KB): {_an_conteggi_testo(r['riep']['conteggi'])}." + (" Protetto da password." if r["pw"] else ""))
        if r["riep"]["mancanti"]:
            st.warning("Alcuni file originali non si sono trovati e non sono nel pacchetto: " + ", ".join(r["riep"]["mancanti"][:6]))
        if len(r["dati"]) > 20 * 1024 * 1024:
            st.info("Il file è grande: per mandarlo per email potrebbe servire un altro mezzo (WhatsApp, Telegram, Drive).")
        st.download_button("⬇ Scarica il pacchetto", r["dati"], file_name=r["nome"], mime="application/zip", key="an_exp_dl", type="primary", width="stretch")
        if "inv_voce" in globals():
            inv_voce("anexp", "📤 Condividi (WhatsApp, email, Telegram…)", "Archivio Animali: " + ", ".join(str(n) for n in r["riep"]["nomi"] if n)[:80],
                     "Ti mando l'archivio degli animali dell'app VitaMemo: aprila → Animali → «Importa archivio animale» e scegli questo file." + (" Il file è protetto da password." if r["pw"] else ""),
                     lambda r_=r: [(r_["nome"], "application/zip", r_["dati"])])


def _an_importa_ui(a):
    st.markdown("#### 📥 Importa archivio animale")
    st.caption("Scegli il file che ti hanno mandato. Controllo che sia intero, ti mostro cosa contiene e **chiedo conferma**: non sostituisco e non cancello niente di ciò che hai già.")
    imp = st.session_state.get("an_imp")
    ultima = next((g for g in reversed(a.get("import") or []) if g.get("stato") == "completata"), None)
    if not imp:
        arr = _an_riceve_file(f"animp{st.session_state.get('an_giro', 0)}")
        if arr:
            nome, dati = arr
            st.session_state["an_imp"] = {"nome": nome, "dati": dati, "pacchetto": None, "pw": ""}
            st.rerun()
        if ultima:
            _an_riquadro_ultima(ultima)
        return
    if st.button("✖ Scegli un altro file", key="an_imp_altro", width="stretch"):
        st.session_state.pop("an_imp", None)
        st.session_state["an_giro"] = st.session_state.get("an_giro", 0) + 1
        st.rerun()
    if imp["pacchetto"] is None:
        try:
            with st.spinner("Controllo il file…"):
                imp["pacchetto"] = an_apri_pacchetto(imp["dati"], imp.get("pw") or None)
        except AnErrore as ex:
            if str(ex) == "PASSWORD":
                st.info("🔒 Il file è protetto da password.")
                pw = st.text_input("Password", type="password", key="an_imp_pw")
                if st.button("🔓 Apri", key="an_imp_pw_ok", type="primary", width="stretch"):
                    imp["pw"] = pw
                    st.rerun()
                return
            st.error("❌ " + str(ex))
            return
    p = imp["pacchetto"]
    m = p["manifest"]
    st.success(f"✅ Archivio Animali riconosciuto e controllato (creato il {an_data_it(str(m.get('creato'))[:10])}" + (f" da {m['creato_da']}" if m.get("creato_da") else "") + ").")
    st.caption("Contenuto: " + _an_conteggi_testo(m.get("conteggi") or {}))
    if p["danneggiati"] or p["mancanti"]:
        st.error("⚠️ Alcuni file non hanno superato il controllo: " + ", ".join((p["danneggiati"] + p["mancanti"])[:8]))
        ok_senza = st.checkbox("Importa comunque, senza i file danneggiati o mancanti (le schede restano, senza quell'allegato)", key="an_imp_senza")
        if not ok_senza:
            st.stop()
    riep = an_riepilogo_import(p, a)
    scelte_an = {}
    for i, r in enumerate(riep):
        x = r["animale"]
        st.markdown(f"<div class='an-card'><div class='t'>{AN_EMOJI.get(x.get('specie'), '🐾')} {_an_e(x.get('nome'))}</div><div class='s'>{_an_e(' · '.join(z for z in (x.get('specie'), x.get('razza')) if z))}<br>"
                    f"{_an_e(_an_conteggi_testo(dict(r['conteggi'], file=r['n_file'])))}</div></div>", unsafe_allow_html=True)
        k = f"an_imp_{x['id']}_"
        if not st.checkbox(f"Importa {x.get('nome', '')}", value=True, key=k + "si"):
            scelte_an[x["id"]] = {"azione": "salta"}
            continue
        if r["duplicati"]:
            for e, forza, motivo in r["duplicati"]:
                st.warning(f"⚠️ Forse esiste già: **{e.get('nome')}** ({'molto probabile' if forza == 'sicuro' else 'possibile'}): {motivo}.")
            e0 = r["duplicati"][0][0]
            opz = {"nuovo": "➕ Importa come NUOVO animale", "aggiorna": f"🔄 Aggiorna la scheda di {e0.get('nome')} (i dati importati prendono il posto di quelli uguali; non si cancella nulla)",
                   "unisci": f"🔗 Unisci le informazioni con {e0.get('nome')} (completo solo ciò che manca)", "salta": "✖ Non importare questo animale"}
            sc = st.radio("Che cosa faccio?", list(opz), format_func=lambda z: opz[z], index=None, key=k + "az")
            if sc is None:
                scelte_an[x["id"]] = {"azione": "attesa"}
            else:
                scelte_an[x["id"]] = {"azione": sc, "target": e0["id"]}
        else:
            scelte_an[x["id"]] = {"azione": "nuovo"}
    presenti = [c for c in _AN_CATEGORIE_SOTTO if any(r["conteggi"].get(c) for r in riep) or (c == "contatti" and p["dati"]["contatti"])]
    cat = st.multiselect("Che informazioni importo?", presenti, default=presenti, format_func=lambda c: AN_NOMI_CATEGORIA[c], key="an_imp_cat")
    st.caption("La scheda dell'animale (dati, proprietario, foto) viene sempre importata. Le voci uguali a quelle che hai già vengono saltate.")
    con_file = st.checkbox("Importa anche foto e documenti originali", value=bool(p["files"]), disabled=not p["files"], key="an_imp_con_file")
    in_attesa = [k for k, v in scelte_an.items() if v["azione"] == "attesa"]
    da_fare = [k for k, v in scelte_an.items() if v["azione"] in ("nuovo", "aggiorna", "unisci")]
    if in_attesa:
        st.info("Scegli cosa fare per ogni animale che esiste già, poi potrai confermare.")
    st.markdown(f"<div class='an-card'><b class='t'>Riepilogo: importo {len(da_fare)} animali</b><div class='s'>Tutto ciò che importo porta scritto da dove viene e quando.</div></div>", unsafe_allow_html=True)
    if st.button("✅ Conferma l'importazione", type="primary", key="an_imp_ok", width="stretch", disabled=bool(in_attesa) or not da_fare):
        try:
            with st.spinner("Importo… (non chiudere la pagina)"):
                ris = an_applica_import(p, {"animali": {k: v for k, v in scelte_an.items() if v["azione"] != "attesa"}, "categorie": cat, "con_file": con_file and bool(p["files"])}, imp["nome"])
        except AnErrore as ex:
            st.error("❌ " + str(ex))
            return
        st.session_state.pop("an_imp", None)
        st.session_state["an_giro"] = st.session_state.get("an_giro", 0) + 1
        n_voci = sum(len(v) for v in ris["creati"].values())
        st.session_state["an_imp_esito"] = (f"✅ Importazione completata: {len(ris['animali_nuovi'])} animali nuovi, {len(ris['animali_aggiornati'])} aggiornati, {n_voci} voci aggiunte, "
                                            f"{ris['file_creati']} file ripristinati" + (f", {ris['saltati']} voci già presenti saltate" if ris["saltati"] else "") + ".")
        st.session_state["an_sezione_dopo"] = "🐾 Scheda"   # applicato dalla pagina PRIMA di creare le schede
        st.session_state["messaggio"] = st.session_state["an_imp_esito"]
        if ris["animali_nuovi"]:
            st.session_state["an_sel"] = ris["animali_nuovi"][0]
        elif ris["animali_aggiornati"]:
            st.session_state["an_sel"] = ris["animali_aggiornati"][0]
        st.rerun()


def _an_riquadro_ultima(g):
    st.markdown(f"<div class='an-card'><b class='t'>Ultima importazione</b><div class='s'>{_an_e(an_data_it(str(g.get('quando'))[:10]))} da {_an_e(g.get('da'))}</div></div>", unsafe_allow_html=True)
    if st.button("↩️ Annulla l'ultima importazione", key=f"an_annulla_{g['id']}", width="stretch"):
        _an_dialogo_annulla(g["id"])


@st.dialog("↩️ Annullare l'importazione?")
def _an_dialogo_annulla(imp_id):
    st.warning("Tolgo SOLO ciò che quell'importazione ha aggiunto (animali nuovi, voci e file) e rimetto com'erano le schede che aveva aggiornato. Le tue cose di prima non si toccano.")
    if st.button("↩️ Sì, annulla", type="primary", key="an_annulla_si", width="stretch"):
        try:
            t = an_annulla_import(imp_id)
            st.session_state["messaggio"] = f"↩️ Importazione annullata: tolti {t['animali']} animali e {t['voci']} voci."
        except AnErrore as ex:
            st.session_state["messaggio"] = "❌ " + str(ex)
        st.rerun()


def an_tab_scambio(a, x):
    modi = ["Esporta", "Importa"]
    if st.session_state.get("an_scambio_modo") not in modi:
        st.session_state["an_scambio_modo"] = "Importa" if not an_animali(a) else "Esporta"
    modo = _an_scegli("Cosa vuoi fare", modi, "an_scambio_modo")
    if modo == "Esporta" and x:
        _an_esporta_ui(a, x)
    elif modo == "Esporta":
        st.info("Non hai ancora animali da esportare. Puoi importarne uno con «Importa».")
    else:
        _an_importa_ui(a)
    st.caption("Storico importazioni: " + (", ".join(f"{an_data_it(str(g.get('quando'))[:10])} ({g.get('stato')})" for g in (a.get("import") or [])[-4:]) or "nessuna"))
