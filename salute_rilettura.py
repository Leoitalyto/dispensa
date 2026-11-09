# -*- coding: utf-8 -*-
"""SALUTE · lettura migliore dei documenti sanitari e RILETTURA di quelli già archiviati.

PROBLEMA (Leonardo, 9 novembre, PDF del profilo di sua madre): fra gli esami di laboratorio uno (le urine) non compariva da nessuna parte: il titolo era il nome della Regione
(«REGIONE PIEMONTE - Azienda Sanitaria…»), nessuna specialità utile, nessun elenco degli esami contenuti. In più: il medico usciva come «Dott. Moniaci Diego Paziente», le
«Conclusioni» erano le intestazioni della tabella («UM. Val. Riferimento», «Metodica U.M.») e la struttura a volte era «Cartella Clinica di <nome della paziente>» o testo storpiato.

COSA FA
• La LETTURA (sp_leggi_doc) ora riconosce l'esame dal CONTENUTO: urine (colore, peso specifico, esterasi, nitriti, sedimento…), emocromo (globuli rossi/bianchi, piastrine, emoglobina,
  ematocrito, MCV…) e le altre analisi; se il documento non dice che esame è, lo ricava dalle analisi che contiene e riempie «Esami contenuti».
• Pulisce i campi sbagliati: medico (toglie «Paziente» e simili), conclusioni (scarta le intestazioni di tabella), struttura (scarta «Cartella clinica di…», il nome della persona, testo storpiato).
• 🔄 «Rileggi i documenti già archiviati»: legge di nuovo i file, ti MOSTRA cosa cambierebbe (titolo di prima → titolo nuovo, campi corretti) e cambia solo se tocchi «Applica».
  Non tocca ciò che hai scritto tu a mano: completa i campi vuoti e ripara quelli chiaramente sbagliati; il titolo cambia solo se era quello automatico.
• Nell'esportazione (PDF/Excel) la colonna «Contenuto» mostra gli esami contenuti (o le conclusioni, se valide) e i campi sbagliati non escono più."""
import re

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# riconoscere l'esame dal contenuto
# ---------------------------------------------------------------------------------------------------------------------
_SR_URINE_FORTI = r"\burin[ae]\b|urinari|urinocoltura|sedimento urinario|esame chimico.?fisico|chimico fisico delle urine"
_SR_URINE_ALTRI = [r"peso specifico", r"esterasi", r"nitriti", r"chetonic", r"urobilinogeno", r"sedimento", r"cilindri", r"cellule epiteliali", r"\bph\b", r"colore", r"aspetto", r"torbid"]
_SR_EMOCROMO = [r"emocromo", r"globuli rossi", r"eritrociti", r"globuli bianchi", r"leucociti", r"piastrine", r"emoglobina(?! glicata)", r"ematocrito", r"\bmcv\b", r"\bmch\b", r"\brdw\b",
                r"neutrofili", r"linfociti", r"monociti", r"eosinofili", r"basofili", r"\bhct\b", r"\bhgb\b", r"\bwbc\b", r"\brbc\b", r"\bplt\b"]


def sr_analisi_contenute(testo):
    """(elenco ordinato di esami riconosciuti, nome suggerito per il documento o '')."""
    tl = (testo or "").lower()
    trovati = []
    n_urine = sum(1 for rx in _SR_URINE_ALTRI if re.search(rx, tl))
    urine = bool(re.search(_SR_URINE_FORTI, tl)) and n_urine >= 2 or n_urine >= 5
    if urine:
        trovati.append("Esame delle urine")
    emo = sum(1 for rx in _SR_EMOCROMO if re.search(rx, tl))
    if re.search(r"emocromo", tl) or emo >= 3 and not (urine and not re.search(r"globuli rossi|piastrine|emocromo|ematocrito|\bmcv\b", tl)):
        trovati.append("Emocromo")
    sangue_forte = re.search(r"emocromo|globuli rossi|piastrine|colesterolo|trigliceridi|transaminasi|\btsh\b|ferritina|creatinina sierica|azotemia|emoglobina glicata", tl)
    if urine and not sangue_forte:
        return ["Esame delle urine"], "Esame delle urine"                         # il glucosio o le proteine nelle urine non sono analisi del sangue
    try:
        for nome, rx in _SP_ANALITI:
            if nome in ("Emocromo", "Esame delle urine") or nome in trovati:
                continue
            if re.search(rx, tl):
                trovati.append(nome)
    except Exception:
        pass
    if not trovati:
        return [], ""
    if len(trovati) == 1:
        nome = trovati[0]
    elif len(trovati) <= 3:
        nome = " + ".join(trovati)
    else:
        nome = "Esami del sangue" if "Esame delle urine" not in trovati else "Esami di laboratorio (sangue e urine)"
    return trovati, nome


# ---------------------------------------------------------------------------------------------------------------------
# ripulire i campi
# ---------------------------------------------------------------------------------------------------------------------
_SR_CODA_MEDICO = {"paziente", "pz", "nato", "nata", "codice", "data", "sesso", "reparto", "cf", "c.f.", "età", "eta", "residente", "tessera", "luogo", "il", "del", "firma", "firmato"}


def sr_medico_pulito(s):
    parole = str(s or "").replace('"', "").strip(" .,;:-").split()
    while len(parole) > 2 and parole[-1].lower().strip(".,;:") in _SR_CODA_MEDICO:
        parole.pop()
    return " ".join(parole).strip(" .,;:-")


def _sr_alfa(s):
    s = str(s or "")
    return (sum(c.isalpha() or c.isspace() for c in s) / len(s)) if s else 0.0


def sr_conclusioni_valide(s):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) < 25 or len(s.split()) < 5 or _sr_alfa(s) < 0.7:
        return False
    if len(s.split()) <= 9 and re.search(r"(?i)\b(u\.?\s?m\.?|val\.?\s*(di\s*)?rif|valori di riferimento|riferimento|metodica|unit[àa] di misura|risultato)\b", s):
        return False
    return True


def sr_struttura_pulita(s, nome_persona=""):
    """La struttura ripulita (senza «|» e numeri iniziali) oppure '' se è chiaramente sbagliata."""
    t = re.sub(r"\s*\|\s*", " ", str(s or "")).strip()
    t = re.sub(r"^[\d\W_]+(?=[A-Za-zÀ-ÿ])", "", t).strip(" -–,:")
    if not t or _sr_alfa(t) < 0.75 or "=>" in str(s or ""):
        return ""
    if re.search(r"(?i)cartella clinica|paziente|nato il|codice fiscale", t):
        return ""
    nome = set(_sp_norm_nome(nome_persona)) if "_sp_norm_nome" in globals() else set()
    if len(nome) >= 2 and len(nome & set(_sp_norm_nome(t))) >= 2:
        return ""                                                                    # c'è il nome della persona: non è una struttura
    return t


# ---------------------------------------------------------------------------------------------------------------------
# la lettura (si aggiunge alla catena di sp_leggi_doc)
# ---------------------------------------------------------------------------------------------------------------------
_sr_leggi_prima = sp_leggi_doc


def sp_leggi_doc(testo, f=None, nome_file="", oggi_=None):                           # noqa: F811
    campi = _sr_leggi_prima(testo, f, nome_file, oggi_)
    try:
        def metti(k, v, aff, fonte="testo"):
            if v:
                campi[k] = {"valore": v, "affidabilita": aff, "fonte": fonte}
        if campi.get("medico"):
            m = sr_medico_pulito(campi["medico"]["valore"])
            if m:
                campi["medico"]["valore"] = m
        if campi.get("conclusioni") and not sr_conclusioni_valide(campi["conclusioni"]["valore"]):
            campi.pop("conclusioni", None)
        nome_pers = ""
        if campi.get("paziente"):
            nome_pers = campi["paziente"]["valore"]
        if campi.get("struttura"):
            s_ = sr_struttura_pulita(campi["struttura"]["valore"], nome_pers)
            if s_:
                campi["struttura"]["valore"] = s_
            else:
                campi.pop("struttura", None)
        # l'esame dal contenuto
        analisi, nome_es = sr_analisi_contenute(testo)
        tipo = (campi.get("tipo") or {}).get("valore", "")
        if analisi and (tipo in ("Esame di laboratorio", "") or len(analisi) >= 2):
            metti("esami_elenco", ", ".join(analisi), "media", "dal contenuto del documento")                # la lettura per contenuto sostituisce quella vecchia (che scambiava il glucosio delle urine per una glicemia)
            if nome_es and (not campi.get("esame") or campi["esame"]["affidabilita"] != "alta"):
                if not campi.get("esame") or campi["esame"]["valore"] in ("Esami del sangue",) or tipo == "Esame di laboratorio":
                    metti("esame", nome_es, "media", "dal contenuto del documento")
            if not campi.get("tipo"):
                metti("tipo", "Esame di laboratorio", "bassa", "contiene analisi")
    except Exception:
        pass
    return campi


# ---------------------------------------------------------------------------------------------------------------------
# rileggere i documenti già archiviati
# ---------------------------------------------------------------------------------------------------------------------
def _sr_testo_file(doc):
    """Il testo del file di un documento (PDF con testo o foto con OCR); '' se non si riesce."""
    refs = _stt_files(doc) if "_stt_files" in globals() else ([doc["file"]] if isinstance(doc.get("file"), dict) else [])
    for rif in refs[:1]:
        try:
            car = _fa_inv_allegati([rif])
            if car and "ca_estrai_testo" in globals():
                nome, mime, dati = car[0]
                testo, _info = ca_estrai_testo(nome, mime, dati)
                return testo or "", nome
        except Exception:
            continue
    return "", ""


def _sr_titolo_auto(d):
    return sp_titolo_doc(d)


def sr_cambiamenti(doc, campi, nome_persona):
    """{campo: (vecchio, nuovo)} dei miglioramenti che si possono fare a un documento, in base ad una nuova lettura. Non sovrascrive ciò che c'è di buono."""
    c = {}
    v = lambda k: (campi.get(k) or {}).get("valore", "")
    # medico
    pul = sr_medico_pulito(doc.get("medico"))
    if doc.get("medico") and pul != doc.get("medico"):
        c["medico"] = (doc.get("medico"), pul)
    elif not doc.get("medico") and v("medico"):
        c["medico"] = ("", v("medico"))
    # conclusioni
    if doc.get("conclusioni") and not sr_conclusioni_valide(doc["conclusioni"]):
        c["conclusioni"] = (doc["conclusioni"], v("conclusioni") if sr_conclusioni_valide(v("conclusioni")) else "")
    elif not doc.get("conclusioni") and sr_conclusioni_valide(v("conclusioni")):
        c["conclusioni"] = ("", v("conclusioni"))
    # struttura
    att = doc.get("struttura") or ""
    buona = sr_struttura_pulita(att, nome_persona)
    if att and buona != att:
        c["struttura"] = (att, buona or v("struttura"))
    elif not att and v("struttura"):
        c["struttura"] = ("", v("struttura"))
    # esame, esami contenuti, specialità, tipo di prestazione
    for k in ("esame", "esami_elenco", "specialita", "prestazione", "tipo_prestazione"):
        if v(k) and not doc.get(k):
            c[k] = ("", v(k))
    if v("esami_elenco") and doc.get("esami_elenco") and doc["esami_elenco"] != v("esami_elenco") and (len(v("esami_elenco")) > len(doc["esami_elenco"]) or v("esami_elenco") == "Esame delle urine"):
        c["esami_elenco"] = (doc["esami_elenco"], v("esami_elenco"))
    for k in ("medico", "conclusioni", "struttura"):
        if k in c and c[k][0] == c[k][1]:
            c.pop(k)
    return c


def sr_proposte(f, pid, progress=None):
    """Rilegge i documenti con file di una persona. Ritorna [{id, titolo_vecchio, titolo_nuovo, cambi, senza_testo}]."""
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {})
    docs = [d for d in (p.get("docsan") or []) if _stt_files(d)]
    out = []
    for i, d in enumerate(docs):
        if progress:
            progress(i / max(1, len(docs)), f"Rileggo {i + 1} di {len(docs)}: {d.get('titolo') or d.get('esame') or d.get('tipo') or ''}"[:80])
        testo, nome_file = _sr_testo_file(d)
        if not testo.strip():
            tv = d.get("titolo") or sp_titolo_doc(d)
            out.append({"id": d.get("id"), "titolo_vecchio": tv, "titolo_nuovo": tv, "cambi": {}, "senza_testo": True})
            continue
        campi = sp_leggi_doc(testo, f, nome_file)
        cambi = sr_cambiamenti(d, campi, p.get("nome", ""))
        nuovo = dict(d)
        nuovo.update({k: val[1] for k, val in cambi.items()})
        vecchio_auto = sp_titolo_doc(d)
        t_vecchio = d.get("titolo") or vecchio_auto
        t_nuovo = t_vecchio
        if not d.get("titolo") or d.get("titolo") == vecchio_auto:
            t_nuovo = sp_titolo_doc(nuovo)
        out.append({"id": d.get("id"), "titolo_vecchio": t_vecchio, "titolo_nuovo": t_nuovo, "cambi": cambi, "senza_testo": False})
    if progress:
        progress(1.0, "Fatto")
    return out


def sr_applica(pid, proposte):
    """Applica le proposte (una sola scrittura)."""
    mappa = {x["id"]: x for x in proposte if x.get("cambi") or x.get("titolo_nuovo") != x.get("titolo_vecchio")}

    def _fn(f_):
        for pr in f_.get("profili", []):
            if pr.get("id") != pid:
                continue
            for d_ in pr.get("docsan", []):
                pro = mappa.get(d_.get("id"))
                if not pro:
                    continue
                vecchio_auto = sp_titolo_doc(d_)
                auto = not d_.get("titolo") or d_.get("titolo") == vecchio_auto
                for k, (_a, b) in pro["cambi"].items():
                    d_[k] = b
                if auto:
                    d_["titolo"] = sp_titolo_doc(d_)
    _fa_salva(_fn, "Salute: documenti sanitari riletti (titoli ed esami migliorati)")
    return len(mappa)


_SR_ETICHETTE = {"medico": "Medico", "conclusioni": "Conclusioni", "struttura": "Struttura", "esame": "Esame", "esami_elenco": "Esami contenuti", "specialita": "Specialità", "prestazione": "Prestazione",
              "tipo_prestazione": "Tipo di prestazione"}


def sr_pannello(pid):
    """La finestra «Rileggi i documenti già archiviati» (dentro Documenti sanitari)."""
    f = _fa_dati()
    p = next((x for x in (f.get("profili") or []) if x.get("id") == pid), {})
    n = sum(1 for d in (p.get("docsan") or []) if _stt_files(d))
    if not n:
        return
    with st.expander(f"🔄 Rileggi i documenti già archiviati ({n}) — migliora titoli ed esami contenuti"):
        st.caption("Rileggo i file di questa persona con la lettura migliorata: riconosco **che esame è** (urine, emocromo…) dal contenuto, riempio **«Esami contenuti»** e sistemo medico, struttura "
                   "e conclusioni chiaramente sbagliati. **Prima ti mostro cosa cambierebbe**; cambia solo se tocchi **Applica**. Quello che hai scritto tu a mano non viene toccato.")
        chiave = f"sr_prop_{pid}"
        if st.button("🔍 Controlla cosa posso migliorare", key=f"sr_ctrl_{pid}", width="stretch"):
            barra = st.progress(0.0, text="Rileggo i documenti…")
            st.session_state[chiave] = sr_proposte(f, pid, lambda x, t_: barra.progress(min(1.0, x), text=t_))
            barra.empty()
        prop = st.session_state.get(chiave)
        if prop is None:
            return
        con = [x for x in prop if x["cambi"] or x["titolo_nuovo"] != x["titolo_vecchio"]]
        senza = [x for x in prop if x["senza_testo"]]
        st.markdown(f"**Controllati {len(prop)} documenti: {len(con)} da migliorare.**" + (f" ({len(senza)} senza testo leggibile: scansioni o foto sfocate)" if senza else ""))
        for x in con:
            righe = []
            if x["titolo_nuovo"] != x["titolo_vecchio"]:
                righe.append(f"**Titolo:** {x['titolo_vecchio']} → **{x['titolo_nuovo']}**")
            for k, (a, b) in x["cambi"].items():
                righe.append(f"**{_SR_ETICHETTE.get(k, k)}:** {a or '—'} → {b or '(tolto: era sbagliato)'}")
            st.markdown("• " + "  \n   ".join(righe))
        if senza:
            st.caption("Senza testo leggibile: " + "; ".join(x["titolo_vecchio"] for x in senza[:6]) + ". Per questi apri «Modifica» e scrivi tu il nome dell'esame.")
        if con:
            c1, c2 = st.columns(2, gap="small")
            if c1.button(f"✅ Applica i {len(con)} miglioramenti", key=f"sr_app_{pid}", type="primary", width="stretch"):
                n_ = sr_applica(pid, prop)
                st.session_state.pop(chiave, None)
                st.toast(f"Aggiornati {n_} documenti")
                st.rerun()
            if c2.button("✖ Non applicare", key=f"sr_no_{pid}", width="stretch"):
                st.session_state.pop(chiave, None)
                st.rerun()
        else:
            st.success("Non c'è niente da migliorare.")


_sr_modulo_docsan_prima = sp_modulo_docsan


def sp_modulo_docsan(pid):                                                           # noqa: F811
    _sr_modulo_docsan_prima(pid)
    try:
        sr_pannello(pid)
    except Exception as ex:
        st.caption(f"(la rilettura non è disponibile adesso: {type(ex).__name__})")
