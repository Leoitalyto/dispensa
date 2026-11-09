# -*- coding: utf-8 -*-
"""ASSISTENTE · gruppo D del progetto di ottimizzazione. Solo AGGIUNTE all'assistente che già esiste (assistente.py): niente è rifatto.

1) CONTESTO DELLA SCHERMATA. «📖 Spiegami questa pagina» e le domande brevi («come lo modifico?») funzionavano solo in Dispensa, Salute, Documenti e Utilità. Ora l'assistente sa anche in quale punto di Casa, Lavoro, Auto (garage, scadenze, diagnostica, fotografare una spia, proposte…) e Archivio ti trovi. Il contesto è «sezione:sottosezione» e si ricava da cosa è aperto, senza leggere dati personali.
2) VOCE: velocità regolabile (🐢 lenta · normale · veloce). Il pulsante sta nel pannello dell'assistente accanto a «Voce»; la scelta resta salvata sul telefono (localStorage `asst_rate`).
3) DOMANDE SENZA RISPOSTA: l'assistente non inventa. Se non trova una procedura lo dice con onestà («non voglio indicarti una procedura che potrebbe non funzionare») e suggerisce come proseguire.
4) 📚 CERCA NEI MIEI MANUALI E DOCUMENTI: una finestra (sotto il pulsante «Informazioni» di Dispensa, Casa, Auto, Utilità) che cerca nei manuali, nelle garanzie e nei documenti dei beni di Casa e nei documenti dei veicoli dell'UTENTE (mai di altre persone). Non carica tutto l'archivio: sceglie al massimo 3 documenti in base a titolo, marca, modello e bene, ne legge il testo UNA volta (tenuto in memoria un'ora), lo divide in passaggi e mostra i 3 più pertinenti con documento, pagina e posizione. Il passaggio si può far leggere ad alta voce. Non spiega e non riassume con l'intelligenza artificiale (servirebbe inviare il manuale a un servizio esterno): mostra le parole del manuale. Se non trova niente, lo dice senza inventare.
Nessun dato lascia l'app. Solo italiano. Caricato dopo assistente.py e guida_extra.py."""
import json
import math
import re
import unicodedata

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# 1) contesto
# ---------------------------------------------------------------------------------------------------------------------
_AE_CTX = {
    "casa": "c_cosa", "casa:documenti": "c_manuali", "casa:manutenzioni": "c_manutenzioni", "casa:riferimenti": "c_riferimenti",
    "lavoro": "l_cosa", "lavoro:buste": "l_carica", "lavoro:anni": "l_anni", "lavoro:cu": "l_cu", "lavoro:inps": "l_inps", "lavoro:contatti": "l_rubrica",
    "auto": "au_garage", "auto:scheda": "au_aggiungi", "auto:scadenze": "au_scadenze", "auto:manutenzione": "au_manut", "auto:rifornimenti": "au_manut",
    "auto:ricambi": "au_manut", "auto:emergenza": "au_emerg", "auto:patente": "au_patente", "auto:viaggi": "au_viaggi", "auto:diagnostica": "au_diag",
    "auto:foto": "au_foto_spia", "auto:archivio": "au_proposte", "auto:codici": "au_diag", "auto:dispositivo": "au_diag", "auto:storico": "au_diag", "auto:assistente": "au_diag",
    "archivio": "ar_cosa", "archivio:tabella": "ar_cercare",
}
_AE_AUTO_SEZ = [("scheda", "scheda"), ("scadenze", "scadenze"), ("manutenzione", "manutenzione"), ("rifornimenti", "rifornimenti"), ("ricambi", "ricambi"), ("emergenza", "emergenza"), ("patente", "patente"), ("diagnostica", "diagnostica")]
_AE_LV = [("buste", "buste"), ("anno", "anni"), ("certificazione", "cu"), ("inps", "inps"), ("sindacato", "contatti")]


def ae_contesto(contesto):
    """Da «auto», «lavoro», «archivio» a «auto:diagnostica»… secondo cosa è aperto adesso (solo le scelte fatte nell'interfaccia)."""
    try:
        ss = st.session_state
        if contesto == "auto" and ss.get("au_vista") == "sezione":
            et = str(ss.get("au_sezione") or "").lower()
            if "diagnostica" in et:
                vd = str(ss.get("dg_vista") or "")
                return "auto:" + (vd if vd in ("foto", "archivio", "dispositivo", "codici", "storico", "assistente") else "diagnostica")
            for chiave, nome in _AE_AUTO_SEZ:
                if chiave in et:
                    return "auto:" + nome
        if contesto == "lavoro":
            et = str(ss.get("lv_sezione") or "").lower()
            for chiave, nome in _AE_LV:
                if chiave in et:
                    return "lavoro:" + nome
        if contesto == "archivio" and str(ss.get("ar_vista") or "").lower().startswith("tabella"):
            return "archivio:tabella"
    except Exception:
        pass
    return contesto


try:
    _CTX_GUIDA.update(_AE_CTX)
    _TAB_CTX["casa"] = ["casa", "documenti", "manutenzioni", "riferimenti"]          # l'ordine delle schede in basso nella pagina Casa: Beni, Documenti, Manutenzioni, Riferimenti
except NameError:
    pass

if "_ae_assistente_prima" not in globals() and "assistente" in globals():
    _ae_assistente_prima = assistente


def assistente(contesto):
    try:
        contesto = ae_contesto(contesto)
    except Exception:
        pass
    return _ae_assistente_prima(contesto)


# ---------------------------------------------------------------------------------------------------------------------
# 2) voce: velocità regolabile  (si modifica il testo dello script dell'assistente; se un punto non si trova, resta com'era)
# ---------------------------------------------------------------------------------------------------------------------
AE_VOCE_OK = False


def _ae_patch_voce():
    global _JS_ASSISTENTE, AE_VOCE_OK
    js = _JS_ASSISTENTE
    if "velocita()" in js:
        AE_VOCE_OK = True
        return
    Q = '"'                                                                                          # le virgolette dentro lo script dell'assistente sono normali
    coppie = [
        ("u.rate = 1; u.pitch = 1.05;", "u.rate = velocita(); u.pitch = 1.05;"),
        ("data-az=" + Q + "silenzio" + Q + " data-ui=" + Q + "a_silenzio" + Q + "></button>",
         "data-az=" + Q + "vel" + Q + "></button>' +\n      '<button class=" + Q + "asst-b grigio" + Q + " data-az=" + Q + "silenzio" + Q + " data-ui=" + Q + "a_silenzio" + Q + "></button>"),
        ("btnVoce = pan.querySelector('[data-az=" + Q + "voce" + Q + "]');", "btnVoce = pan.querySelector('[data-az=" + Q + "voce" + Q + "]'), btnVel = pan.querySelector('[data-az=" + Q + "vel" + Q + "]');"),
        ("if (!SS) { btnVoce.style.display = 'none';", "if (!SS) { btnVel.style.display = 'none'; btnVoce.style.display = 'none';"),
        ("function aggiornaVoceBtn() { btnVoce.textContent = voceOn ? T('a_voce_on') : T('a_voce_off'); }",
         "function velocita() { var v = parseFloat(leggi('asst_rate', '1')); return (v >= 0.5 && v <= 2) ? v : 1; }\n"
         "  function aggiornaVoceBtn() { btnVoce.textContent = voceOn ? T('a_voce_on') : T('a_voce_off'); var v = velocita(); btnVel.textContent = T('a_vel') + ': ' + T(v < 0.9 ? 'a_vel_0' : (v > 1.1 ? 'a_vel_2' : 'a_vel_1')); }"),
        ("else if (az === 'voce') {", "else if (az === 'vel') { var v0 = velocita(), n0 = v0 < 0.9 ? 1 : (v0 > 1.1 ? 0.8 : 1.25); scrivi('asst_rate', String(n0)); aggiornaVoceBtn(); if (SS) parla(T('a_vel_prova')); }\n    else if (az === 'voce') {"),
    ]
    for a, b in coppie:
        if js.count(a) != 1:
            return                                                                                  # un punto non si trova: l'assistente resta com'era (nessun danno)
    for a, b in coppie:
        js = js.replace(a, b)
    _JS_ASSISTENTE = js
    AE_VOCE_OK = True


AE_RICERCA_OK = False


def _ae_patch_ricerca():
    """Una domanda senza senso non deve «trovare» una scheda a caso: con 3 o più parole che contano, una sola parola in comune con una scheda non basta (a meno che l'azione, per esempio «eliminare», non coincida)."""
    global _JS_ASSISTENTE, AE_RICERCA_OK
    js = _JS_ASSISTENTE
    if "forte = true" in js:
        AE_RICERCA_OK = True
        return
    coppie = [
        ("var pt = 0, tr = 0, bonus = 0, ex = false;", "var pt = 0, tr = 0, bonus = 0, ex = false, forte = false;"),
        ("if (combacia(x, e.t)) { pt += 3; tr++; } else if (combacia(x, e.k)) { pt += 2; tr++; }", "if (combacia(x, e.t)) { pt += 3; tr++; forte = true; } else if (combacia(x, e.k)) { pt += 2; tr++; forte = true; }"),
        ("if (pt + bonus > 0) ris.push(", "if (pt + bonus > 0 && (bonus > 0 || tr >= 2 || q.length <= 2)) ris.push("),
    ]
    if any(js.count(a_) != 1 for a_, _b in coppie):
        return                                                                                  # un punto non si trova: resta com'era
    for a_, b_ in coppie:
        js = js.replace(a_, b_)
    _JS_ASSISTENTE = js
    AE_RICERCA_OK = True


try:
    UI_IT.update({"a_vel": "🐢 Velocità della voce", "a_vel_0": "lenta", "a_vel_1": "normale", "a_vel_2": "veloce", "a_vel_prova": "Questa è la mia voce con la nuova velocità.",
                  # 3) niente procedure inventate
                  "a_trov_t": "Non trovo istruzioni su questo",
                  "a_trov_x": "Non voglio indicarti una procedura che potrebbe non funzionare: forse questa funzione non esiste nell'app, oppure uso parole diverse dalle tue. Prova con altre parole (anche una sola: foto, scadenza, password) o scegli un argomento qui sotto. Se riguarda un tuo apparecchio, apri «📚 Cerca nei miei manuali e documenti»."})
    _ae_patch_voce()
    _ae_patch_ricerca()
    _extra_stop = ("faccio", "fare", "fai", "fatto", "posso", "puoi", "devo", "voglio", "vorrei", "quanto", "quanti", "quanta", "quante", "quale", "quali", "qual")      # parole comuni che non dicono di che cosa si parla
    _it_stop = _STOP_LANG.get("it", ())
    _STOP_LANG["it"] = (_it_stop | set(_extra_stop)) if isinstance(_it_stop, (set, frozenset)) else (type(_it_stop)(list(_it_stop) + [x for x in _extra_stop if x not in _it_stop]) if isinstance(_it_stop, (list, tuple)) else _it_stop)
except NameError:
    pass


# ---------------------------------------------------------------------------------------------------------------------
# 4) cercare nei manuali e nei documenti dell'utente
# ---------------------------------------------------------------------------------------------------------------------
_MR_STOP = set("il lo la le gli un una uno di da del dello della dei degli delle in con su per tra fra che chi cosa come dove quando perche non mi ti si ci vi ho ha hai sono e ed o ma se piu poco molto questo questa questi queste quello quella al allo alla ai agli alle nel nello nella nei negli nelle sul sullo sulla sui sugli sulle puo posso devo fare fatto faccio vuole voglio vorrei anche solo gia ancora quanto quale quali".split())
_MR_TIPI_LAVORO = {"Busta paga", "Certificazione Unica (CU)", "Documento INPS"}
# i tipi VERI di Casa (CA_TIPI) che sono manuali o istruzioni; gli altri documenti (bollette, contratti…) si cercano solo se il nome o il bene c'entrano con la domanda
_MR_TIPI_MANUALE = ("Manuale d'uso", "Manuale di installazione", "Manuale di manutenzione", "Scheda tecnica", "Certificato di garanzia", "Libretto di impianto", "Dichiarazione di conformità", "Istruzioni di montaggio")
MR_MAX_DOC = 3
MR_MAX_DOC_TUTTI = 8
MR_MAX_BYTE = 25 * 1024 * 1024
MR_MAX_PAGINE = 150


def _mr_norm(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def mr_token(testo):
    """Le parole che contano di una frase (senza parole comuni), in forma ridotta per confrontare «filtro/filtri»."""
    out = []
    for p in re.findall(r"[a-z0-9]{3,}", _mr_norm(testo)):
        if p in _MR_STOP:
            continue
        out.append(p[:6] if len(p) > 6 else p)
    return list(dict.fromkeys(out))


def _mr_ridotte(testo):
    return [p[:6] if len(p) > 6 else p for p in re.findall(r"[a-z0-9]{3,}", _mr_norm(testo))]


def mr_documenti(d):
    """I documenti in cui cercare: SOLO quelli dell'utente (manuali, garanzie e documenti dei beni di Casa; documenti dei veicoli). [{id, titolo, dove, riferimenti[], meta, fonte}]"""
    out = []
    casa = (d or {}).get("casa") or {}
    beni = {b.get("id"): b for b in casa.get("beni", []) if isinstance(b, dict)}
    for x in casa.get("documenti", []) or []:
        if not isinstance(x, dict) or x.get("tipo") in _MR_TIPI_LAVORO:
            continue
        rif = x.get("file") if isinstance(x.get("file"), dict) else None
        if not rif or not rif.get("id"):
            continue
        tipo_x = str(x.get("tipo") or "")
        manuale = tipo_x in _MR_TIPI_MANUALE or tipo_x.startswith("Manuale") or tipo_x in ("Garanzia", "Manuale") or x.get("argomento") == "Manuali e istruzioni" or bool(x.get("bene_id"))
        bene = beni.get(x.get("bene_id")) or {}
        meta = " ".join(str(v) for v in (x.get("titolo"), x.get("tipo"), x.get("argomento"), x.get("marca"), x.get("modello"), x.get("categoria"), x.get("sottocategoria"), bene.get("nome"), bene.get("marca"), bene.get("modello")) if v)
        out.append({"id": x.get("id"), "titolo": x.get("titolo") or rif.get("nome") or "Documento", "dove": "Casa → 📚 Documenti" + (f" (bene: {bene.get('nome')})" if bene.get("nome") else ""), "riferimenti": [rif], "meta": meta, "fonte": "casa", "manuale": manuale})
    for v in ((d or {}).get("auto") or {}).get("veicoli", []) or []:
        if not isinstance(v, dict):
            continue
        nome_v = " ".join(str(z) for z in (v.get("marca"), v.get("modello"), v.get("targa")) if z)
        for x in v.get("documenti", []) or []:
            if not isinstance(x, dict):
                continue
            ris = [r for r in (x.get("files") or []) if isinstance(r, dict) and r.get("id")]
            if not ris:
                continue
            out.append({"id": x.get("id"), "titolo": (x.get("titolo") or x.get("tipo") or "Documento") + (f" · {v.get('targa')}" if v.get("targa") else ""), "dove": "Auto → " + (nome_v or "veicolo") + " → 🪪 Scheda e documenti",
                        "riferimenti": ris[:2], "meta": " ".join(str(z) for z in (x.get("titolo"), x.get("tipo"), x.get("categoria"), nome_v) if z), "fonte": "auto", "manuale": "manuale" in _mr_norm(x.get("titolo", "") + " " + str(x.get("tipo", "")))})
    return out


def mr_scegli(documenti, domanda, tutti=False):
    """Quali documenti leggere: prima quelli che c'entrano per titolo/marca/modello/bene; se nessuno, i manuali. Ritorna (scelti, altri_non_letti)."""
    tok = mr_token(domanda)
    punti = []
    for doc in documenti:
        m = set(_mr_ridotte(doc["meta"]))
        p = sum(1 for t in tok if t in m)
        punti.append((p, 1 if doc.get("manuale") else 0, doc))
    punti.sort(key=lambda z: (-z[0], -z[1]))
    limite = MR_MAX_DOC_TUTTI if tutti else MR_MAX_DOC
    con = [z for z in punti if z[0] > 0]
    scelti = [z[2] for z in (con if con else punti)][:limite]                                # se nessuno c'entra per nome: prima i manuali, poi gli altri
    if tutti:
        scelti = [z[2] for z in punti][:limite]
    return scelti, max(0, len(documenti) - len(scelti))


@st.cache_data(ttl=3600, max_entries=16, show_spinner=False)
def _mr_pagine_file(uid, fid, nome, mime, dimensione):
    """[(pagina, testo)] di un file (lo si legge UNA volta e si tiene un'ora in memoria). `uid` fa parte della chiave: la memoria è per persona."""
    try:
        file_ = _ca_leggi_file({"id": fid, "nome": nome, "mime": mime})
    except Exception:
        return []
    if not file_:
        return []
    nome_, mime_, dati = file_[0]
    if not dati or len(dati) > MR_MAX_BYTE:
        return []
    pagine = []
    if mime_ == "application/pdf":
        try:
            try:
                import pymupdf as _mu
            except Exception:
                import fitz as _mu
            doc = _mu.open(stream=dati, filetype="pdf")
            for i in range(min(MR_MAX_PAGINE, doc.page_count)):
                try:
                    t = doc[i].get_text("text", sort=True) or ""
                except Exception:
                    t = ""
                if t.strip():
                    pagine.append((i + 1, t[:8000]))
            doc.close()
        except Exception:
            pagine = []
    if not pagine:                                                                             # foto o scansione: lettura con OCR (una pagina sola)
        try:
            testo, _info = ca_estrai_testo(nome_, mime_, dati, max_pagine=3, max_car=12000)
            if (testo or "").strip():
                pagine.append((1, testo))
        except Exception:
            pass
    return pagine


def _mr_passaggi(pagine, lung=650):
    out = []
    for n, t in pagine:
        blocchi = [b.strip() for b in re.split(r"\n\s*\n", t) if b.strip()] or [t.strip()]
        cur = ""
        for b in blocchi:
            b = re.sub(r"[ \t]+", " ", b)
            if len(cur) + len(b) <= lung:
                cur = (cur + "\n" + b).strip()
            else:
                if cur:
                    out.append((n, cur))
                while len(b) > lung:                                                           # un blocco lungo: si spezza alla fine di una frase
                    taglio = max(b.rfind(". ", 0, lung), b.rfind("; ", 0, lung), lung // 2)
                    out.append((n, b[:taglio + 1].strip()))
                    b = b[taglio + 1:].strip()
                cur = b
        if cur:
            out.append((n, cur))
    return out


def mr_cerca(d, domanda, tutti=False, massimo=3):
    """Cerca nei documenti dell'utente. Ritorna {"passaggi": [...], "letti": [titoli], "non_letti": n, "nessun_documento": bool}."""
    docs = mr_documenti(d)
    if not docs:
        return {"passaggi": [], "letti": [], "non_letti": 0, "nessun_documento": True}
    tok = mr_token(domanda)
    scelti, non_letti = mr_scegli(docs, domanda, tutti)
    letti, cand, df, n_tot = [], [], {}, 0
    for doc in scelti:
        rif = doc["riferimenti"][0]
        meta_doc = set(_mr_ridotte(doc["meta"]))
        hit_doc = sum(1 for t in tok if t in meta_doc)                         # parole della domanda già presenti nel nome del documento / del bene
        pagine = []
        for r in doc["riferimenti"]:
            pagine = _mr_pagine_file((st.session_state.get("sess") or {}).get("uid", ""), r.get("id"), r.get("nome", ""), r.get("mime", ""), int(r.get("dimensione") or 0)) or pagine
            if pagine:
                break
        letti.append(doc["titolo"])
        for n, testo in _mr_passaggi(pagine):
            parole = set(_mr_ridotte(testo))
            n_tot += 1
            for t in tok:
                if t in parole:
                    df[t] = df.get(t, 0) + 1
            cand.append((doc, n, testo, parole, hit_doc))
    ris = []
    for doc, n, testo, parole, hit_doc in cand:
        trovate = [t for t in tok if t in parole]
        if not trovate:
            continue
        # con due o più parole nella domanda, nel passaggio ne servono almeno due, meno quelle che già dicono di che documento si parla (nome o bene):
        # «pressione caldaia» in un documento della caldaia basta «pressione»; in un manuale di altro (un giradischi) servono tutte e due
        servono = max(1, min(2, len(tok)) - hit_doc)
        if len(trovate) < servono:
            continue
        punteggio = sum(math.log(1 + n_tot / (1 + df.get(t, 0))) for t in trovate) * (1.0 + 0.5 * (len(trovate) - 1)) + 2.0 * hit_doc
        ris.append({"titolo": doc["titolo"], "pagina": n, "testo": testo, "dove": doc["dove"], "punteggio": round(punteggio, 2), "parole": trovate})
    ris.sort(key=lambda r: -r["punteggio"])
    visti, out = set(), []
    for r in ris:
        k = (r["titolo"], r["pagina"])
        if k in visti:
            continue
        visti.add(k)
        out.append(r)
        if len(out) >= massimo:
            break
    return {"passaggi": out, "letti": letti, "non_letti": non_letti, "nessun_documento": False}


def _mr_js_voce(testo):
    """Legge ad alta voce un passaggio con la velocità scelta nel pannello dell'assistente."""
    pulito = re.sub(r"\s+", " ", re.sub(r"[*_`#]", "", testo)).strip()
    return ("(function(){var w=window,SS=w.speechSynthesis;if(!SS)return;SS.cancel();var r=1;try{r=parseFloat(w.localStorage.getItem('asst_rate')||'1')||1}catch(e){}if(r<0.5||r>2)r=1;"
            "var t=" + json.dumps(pulito, ensure_ascii=False) + ";var p=t.match(/[^.;:!?]+[.;:!?]?/g)||[t],i=0;"
            "function dici(){if(i>=p.length)return;var u=new w.SpeechSynthesisUtterance(p[i++].trim());u.lang='it-IT';u.rate=r;u.onend=dici;SS.speak(u);}dici();})();")


def _mr_dialogo(sezione):
    @st.dialog("📚 Cerca nei miei manuali e documenti", width="large")
    def _f():
        st.caption("Scrivi cosa cerchi (per esempio «spia rossa lavatrice» o «pulire il filtro caldaia»). Cerco **solo nei tuoi** manuali, garanzie e documenti di Casa e dei veicoli, e ti mostro **i passaggi che c'entrano**, non tutto il PDF.")
        q = st.text_input("Cosa cerchi", key="mr_q", placeholder="es. come sbloccare il cestello", label_visibility="collapsed")
        cerca = st.button("🔎 Cerca", key="mr_vai", width="stretch", type="primary")
        if cerca:
            st.session_state["mr_tutti"] = False                                                   # una nuova ricerca parte dai documenti più adatti
        tutti = st.session_state.get("mr_tutti", False)
        if q.strip() and (cerca or st.session_state.get("mr_ultima") == q.strip()):
            st.session_state["mr_ultima"] = q.strip()
            try:
                d = carica_dati(crea_archivio(), st.session_state["percorso"])
            except Exception:
                st.error("Non riesco a leggere i tuoi documenti ora. Riprova fra poco.")
                return
            with st.spinner("Leggo i documenti…"):
                r = mr_cerca(d, q, tutti=tutti)
            if r["nessun_documento"]:
                st.info("Non hai ancora manuali o documenti archiviati. Apri **Casa → 📚 Documenti** e carica un manuale (PDF o foto): poi potrò cercare dentro.")
                return
            if not r["passaggi"]:
                st.warning("Non ho trovato niente su «" + q.strip() + "» nei documenti che ho letto. **Non voglio inventare una risposta.**")
                st.caption("Ho letto: " + "; ".join(r["letti"]) + ".")
                if r["non_letti"] and not tutti:
                    if st.button(f"🔎 Cerca anche negli altri {r['non_letti']} documenti (più lento)", key="mr_tutti_b", width="stretch"):
                        st.session_state["mr_tutti"] = True
                        st.rerun(scope="fragment")
                st.caption("Prova con altre parole, oppure apri il documento e cercalo a mano.")
                return
            n_p = len(r["passaggi"])
            st.markdown(f"**{n_p} " + ("passaggio trovato" if n_p == 1 else "passaggi trovati") + "** (in: " + "; ".join(r["letti"]) + ")")
            for i, p in enumerate(r["passaggi"]):
                with st.container(border=True):
                    st.markdown(f"**📄 {p['titolo']}** · pagina {p['pagina']}")
                    st.caption(f"📍 Dove si trova: {p['dove']}")
                    st.markdown(p["testo"])
                    c1, c2 = st.columns(2, gap="small")
                    if c1.button("🔊 Leggi ad alta voce", key=f"mr_leggi_{i}", width="stretch"):
                        _inietta(_mr_js_voce(p["testo"]))
                    if c2.button("⏹ Ferma la voce", key=f"mr_ferma_{i}", width="stretch"):
                        _inietta("(function(){try{window.speechSynthesis.cancel()}catch(e){}})();")
            st.caption("Sono le parole del manuale, non una mia spiegazione: se qualcosa non è chiaro, chiedi a una persona di fiducia. Per cambiare la velocità della voce usa il robottino: «🐢 Velocità della voce».")
    _f()


if "_ae_info_prima" not in globals() and "pulsante_info" in globals():
    _ae_info_prima = pulsante_info


def pulsante_info(sezione):
    r = _ae_info_prima(sezione)
    if sezione in ("dispensa", "casa", "auto", "utilita"):
        try:
            if st.button("📚 Cerca nei miei manuali e documenti", key=f"mr_btn_{sezione}", width="stretch"):
                _mr_dialogo(sezione)
        except Exception:
            pass
    return r
