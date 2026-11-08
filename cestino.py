# -*- coding: utf-8 -*-
"""CESTINO UNICO (gruppo B del progetto di ottimizzazione).

COSA FA: quando una persona elimina un elemento (un prodotto, un medicinale, un documento, un bene, un intervento dell'auto…) l'elemento NON sparisce subito: va nel Cestino, dove resta per 30 giorni (impostabile: 7, 15, 30, 60, 90). Si può ripristinare (torna dov'era, con i dati collegati) o eliminare per sempre. Allo scadere si cancella da solo.
COME (senza toccare le 25 e più funzioni di eliminazione che già esistono):
 • Tutti i dati PERSONALI passano da `salva_file()`: lo si avvolge. Prima e dopo ogni salvataggio si confrontano i dati; ogni elemento con un «id» che era in una lista e non c'è più in nessun punto dei dati nuovi è un elemento eliminato (se è stato solo spostato in un'altra lista l'id c'è ancora: non è un'eliminazione).
 • L'elemento eliminato (con tutto quello che contiene) va nell'elenco `cestino` DENTRO lo stesso file dei dati della persona: stesse autorizzazioni, stessa struttura, nessun archivio centrale. Si ricorda il percorso d'origine (per esempio auto → veicoli → [id] → documenti) per rimetterlo a posto.
 • Le liste che sono registri e non contenuti (storico, registro, eventi, lista della spesa…) restano fuori (`_CS_ESCLUDI`).
 • I FILE allegati (documenti, foto) stanno in file a parte e un solo punto li cancella (`_fa_cancella_files`): lo si avvolge, così i file vengono solo SEGNATI (`cestino_file`) e cancellati davvero alla scadenza o con «Elimina per sempre». Così il ripristino ritrova tutto.
 • Interruttore di emergenza: nei Secrets CESTINO = "no" spegne tutto (si torna come prima).
La dispensa di FAMIGLIA ha già il suo storico con annullamento: non passa da qui. L'eliminazione di un'intera persona (amministratore) resta com'era.
Caricato dopo gli altri moduli (avvolge funzioni che esistono già)."""
import copy
import json
from datetime import datetime, timedelta

import streamlit as st

CS = "cestino"
CS_FILE = "cestino_file"
CS_MAX = 400
CS_REG = "registro_mod"
RM_MAX = 300
RM_GIORNI = 180
_RM_NOISE = {"aggiornato", "aggiornata", "modificato", "modificato_il", "modificata_il", "ultimo_avviso", "gia_avvisato", "versione", "letto", "visto", "ultimo_accesso", "ts", "creato_il_agg"}
_CS_ESCLUDI = {CS, CS_FILE, CS_REG, "storico", "registro", "eventi", "spesa", "provati", "cronologia", "log", "sessioni"}
_CS_SEZIONI = {"articoli": "Dispensa", "farmacia": "Salute", "casa": "Casa", "auto": "Auto"}
_CS_TIPI_LAVORO = {"Busta paga", "Certificazione Unica (CU)", "Documento INPS"}
_CS_GIORNI = [7, 15, 30, 60, 90]


def cs_attivo():
    try:
        return str(st.secrets.get("CESTINO", "si")).strip().lower() not in ("no", "off", "0", "spento")
    except Exception:
        return True


def _cs_ora():
    try:
        return adesso().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M")


def _cs_giorni(d):
    try:
        g = int(((d.get("impostazioni") or {}).get("cestino_giorni")) or 30)
    except (TypeError, ValueError):
        g = 30
    return g if g in _CS_GIORNI else 30


def _cs_scaduto(rec, d, ora=None):
    try:
        dt = datetime.strptime(rec["eliminato_il"], "%Y-%m-%d %H:%M")
    except Exception:
        return False
    return dt + timedelta(days=_cs_giorni(d)) <= datetime.strptime(ora or _cs_ora(), "%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------------------------------------------------
# il confronto prima/dopo
# ---------------------------------------------------------------------------------------------------------------------
def _cs_ids(o, ids):
    if isinstance(o, dict):
        x = o.get("id")
        if isinstance(x, str):
            ids.add(x)
        for k, v in o.items():
            if k not in (CS, CS_FILE, CS_REG):
                _cs_ids(v, ids)
    elif isinstance(o, list):
        for v in o:
            _cs_ids(v, ids)


def _cs_rimossi(o, ids_dopo, percorso, out):
    """Cerca nei dati di PRIMA gli elementi (dizionari con «id» dentro una lista) che nei dati di DOPO non ci sono più."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k not in _CS_ESCLUDI:
                _cs_rimossi(v, ids_dopo, percorso + [k], out)
    elif isinstance(o, list):
        for x in o:
            if isinstance(x, dict) and isinstance(x.get("id"), str):
                if x["id"] not in ids_dopo:
                    out.append((percorso, x))                      # eliminato: lo si prende intero, senza scendere dentro
                else:
                    for k, v in x.items():
                        if k not in _CS_ESCLUDI:
                            _cs_rimossi(v, ids_dopo, percorso + [["id", x["id"]], k], out)


def _cs_etichetta(x):
    for k in ("nome", "titolo", "targa", "descrizione", "intervento", "tipo", "denominazione", "cognome"):
        v = x.get(k)
        if isinstance(v, str) and v.strip():
            extra = x.get("marca") if isinstance(x.get("marca"), str) and x.get("marca").strip() and k == "nome" else ""
            return (v.strip() + (f" · {extra.strip()}" if extra else ""))[:80]
    if x.get("marca") or x.get("modello"):
        return f"{x.get('marca', '')} {x.get('modello', '')}".strip()[:80]
    for k in ("data", "quando"):
        if isinstance(x.get(k), str) and x[k]:
            return f"Voce del {x[k][:10]}"
    return "Elemento"


def _cs_sezione(percorso, x):
    top = percorso[0] if percorso else ""
    if top == "casa":
        chiavi = [p for p in percorso if isinstance(p, str)]
        if "lavori" in chiavi or "contatti_lavoro" in chiavi or x.get("tipo") in _CS_TIPI_LAVORO or x.get("lavoro_id"):
            return "Lavoro"
    return _CS_SEZIONI.get(top, "Altro")


def _cs_icona(sez):
    return {"Dispensa": "🏠", "Salute": "🩺", "Casa": "🏡", "Lavoro": "💼", "Auto": "🚗"}.get(sez, "📁")


def _cs_file_di(voce):
    """Gli id dei file allegati (documenti, foto) contenuti in un elemento: riferimenti del tipo {id, nome, mime}."""
    ids = []

    def _giro(o):
        if isinstance(o, dict):
            if isinstance(o.get("id"), str) and (o.get("mime") or (o.get("nome") and o.get("sha"))):
                ids.append(o["id"])
            for v in o.values():
                _giro(v)
        elif isinstance(o, list):
            for v in o:
                _giro(v)
    _giro(voce)
    return list(dict.fromkeys(ids))


def _cs_applica(prima, d, escludi=()):
    """Dentro il salvataggio: sposta nel Cestino ciò che è stato eliminato e toglie ciò che è scaduto. Ritorna (nuovi record, id file da cancellare davvero)."""
    ids_dopo = set()
    _cs_ids({k: v for k, v in d.items() if k not in (CS, CS_FILE, CS_REG)}, ids_dopo)
    rimossi = []
    _cs_rimossi({k: v for k, v in prima.items() if k not in (CS, CS_FILE, CS_REG)}, ids_dopo, [], rimossi)
    cest = d.get(CS)
    if not isinstance(cest, list):
        cest = d[CS] = []
    nuovi, ora = [], _cs_ora()
    gruppo = "g" + ora.replace("-", "").replace(":", "").replace(" ", "") + (rimossi[0][1]["id"][:6] if rimossi else "")
    gia = {r.get("voce", {}).get("id") for r in cest if isinstance(r, dict)}
    for percorso, x in rimossi[:200]:
        if x["id"] in gia or x["id"] in escludi:                       # già nel Cestino, oppure un prodotto finito/buttato (statistiche): non è un'eliminazione da annullare
            continue
        rec = {"id": "cs" + x["id"][:10] + ora[-5:].replace(":", ""), "voce": copy.deepcopy(x), "percorso": percorso, "sezione": _cs_sezione(percorso, x), "etichetta": _cs_etichetta(x), "eliminato_il": ora, "gruppo": gruppo, "c": str(x.get("casa_id") or "")}
        cest.append(rec)
        nuovi.append(rec)
    da_cancellare = []
    for r in [r for r in cest if isinstance(r, dict) and _cs_scaduto(r, d, ora)]:          # scaduti: via, e con loro i file
        cest.remove(r)
        da_cancellare += _cs_file_di(r.get("voce"))
    if len(cest) > CS_MAX:                                                                    # troppo pieno: i più vecchi
        for r in cest[:len(cest) - CS_MAX]:
            da_cancellare += _cs_file_di(r.get("voce"))
        del cest[:len(cest) - CS_MAX]
    pend = d.get(CS_FILE)
    if isinstance(pend, list):
        in_cestino = set()
        for r in cest:
            in_cestino.update(_cs_file_di(r.get("voce")))
        giorni = _cs_giorni(d)
        for p_ in list(pend):
            try:
                vecchio = datetime.strptime(p_["quando"], "%Y-%m-%d %H:%M") + timedelta(days=giorni) <= datetime.strptime(ora, "%Y-%m-%d %H:%M")
            except Exception:
                vecchio = True
            if p_.get("id") in da_cancellare or (vecchio and p_.get("id") not in in_cestino):
                pend.remove(p_)
                da_cancellare.append(p_.get("id"))
    if not cest:
        d.pop(CS, None)
    return nuovi, list(dict.fromkeys(i for i in da_cancellare if i))


# ---------------------------------------------------------------------------------------------------------------------
# STORICO DELLE MODIFICHE: il registro delle OPERAZIONI (aggiunto, modificato, eliminato, ripristinato, quando e in quale sezione).
# Non è lo «storico dei contenuti» (gli elenchi di ciò che hai registrato): qui NON c'è il contenuto, solo il nome dell'elemento e i NOMI dei campi cambiati.
# ---------------------------------------------------------------------------------------------------------------------
def _rm_elementi(o, percorso, out):
    """{id: (percorso, dizionario)} di ogni elemento con «id» dentro una lista (qualsiasi profondità), senza i registri."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k not in _CS_ESCLUDI:
                _rm_elementi(v, percorso + [k], out)
    elif isinstance(o, list):
        for x in o:
            if isinstance(x, dict) and isinstance(x.get("id"), str):
                out[x["id"]] = (percorso, x)
                for k, v in x.items():
                    if k not in _CS_ESCLUDI:
                        _rm_elementi(v, percorso + [["id", x["id"]], k], out)


def _rm_scalari(x):
    """I campi semplici di un elemento (testo, numeri, sì/no, elenchi di testo): quelli annidati con altri elementi si seguono a parte."""
    out = {}
    for k, v in x.items():
        if k in _RM_NOISE or k.startswith("_") or k == "id":
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list) and all(isinstance(z, (str, int, float, bool)) for z in v):
            out[k] = v
        elif isinstance(v, dict) and "id" not in v and all(isinstance(z, (str, int, float, bool, type(None))) for z in v.values()):
            out[k] = v
    return out


def _rm_calcola(prima, d, nuovi):
    """Le righe del registro per questo salvataggio: [(azione, sezione, etichetta, [campi])]."""
    a, b = {}, {}
    _rm_elementi({k: v for k, v in prima.items() if k not in (CS, CS_FILE, CS_REG)}, [], a)
    _rm_elementi({k: v for k, v in d.items() if k not in (CS, CS_FILE, CS_REG)}, [], b)
    righe = []
    for i, (perc, x) in b.items():
        if i not in a:
            righe.append(("aggiunto", _cs_sezione(perc, x), _cs_etichetta(x), [], str(x.get("casa_id") or "")))
        else:
            sa, sb = _rm_scalari(a[i][1]), _rm_scalari(x)
            campi = sorted(k for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))
            if campi:
                righe.append(("modificato", _cs_sezione(perc, x), _cs_etichetta(x), campi[:8], str(x.get("casa_id") or "")))
    for r in nuovi:                                                                             # gli eliminati: quelli finiti nel Cestino
        righe.append(("eliminato", r.get("sezione", "Altro"), r.get("etichetta", "Elemento"), [], r.get("c", "")))
    return righe


def _rm_scrivi(d, righe, quando):
    if not righe:
        return
    reg = d.get(CS_REG)
    if not isinstance(reg, list):
        reg = d[CS_REG] = []
    for az, sez, et, campi, *resto in righe[:20]:
        reg.append({"q": quando, "az": az, "sez": sez, "e": et, "campi": campi, "c": (resto[0] if resto else "")})
    if len(righe) > 20:
        reg.append({"q": quando, "az": "altro", "sez": "Altro", "e": f"…e altre {len(righe) - 20} operazioni", "campi": []})
    try:
        limite = (datetime.strptime(quando, "%Y-%m-%d %H:%M") - timedelta(days=RM_GIORNI)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        limite = ""
    d[CS_REG] = [r for r in reg if isinstance(r, dict) and r.get("q", "") >= limite][-RM_MAX:]


def _cs_percorso_personale():
    p = st.session_state.get("percorso") or ""
    return p if (p.startswith("dispense/") and p.endswith(".json")) else ""


def _cs_cancella_file_veri(ids):
    for i in ids:
        try:
            crea_archivio().elimina(_fa_percorso_doc(i), "Cestino: file eliminato per sempre")
        except Exception:
            pass
    if ids:
        carica_dati.clear()


# ---------------------------------------------------------------------------------------------------------------------
# aggancio: salva_file e _fa_cancella_files
# ---------------------------------------------------------------------------------------------------------------------
if "_cs_salva_file_prima" not in globals():
    _cs_salva_file_prima = salva_file


def salva_file(nome, fn, messaggio):
    personale = str(nome).startswith("dispense/") and str(nome).endswith(".json")
    if not personale or not cs_attivo() or st.session_state.get("_cs_pausa"):
        return _cs_salva_file_prima(nome, fn, messaggio)
    esito = {"nuovi": [], "file": []}

    def _fn2(d):
        prima = copy.deepcopy(d)
        st.session_state["_cs_eventi"] = set()
        fn(d)
        esito["nuovi"], esito["file"] = _cs_applica(prima, d, st.session_state.pop("_cs_eventi", set()))
        try:
            _rm_scrivi(d, _rm_calcola(prima, d, esito["nuovi"]), _cs_ora())
        except Exception:
            pass                                                                                # il registro non deve mai impedire un salvataggio
    st.session_state["_cs_nel_salvataggio"] = True
    try:
        r = _cs_salva_file_prima(nome, _fn2, messaggio)
    finally:
        st.session_state["_cs_nel_salvataggio"] = False
    coda = st.session_state.pop("_cs_file_coda", [])
    if coda:                                                                   # file «da cancellare» arrivati mentre si stava già salvando: ora si segnano
        _cs_segna_file(coda)
    if esito["nuovi"]:
        st.session_state["cs_ultimo"] = {"ids": [esito["nuovi"][0]["gruppo"]], "n": len(esito["nuovi"]), "etichetta": sorted(esito["nuovi"], key=lambda x: len(x["percorso"]))[0]["etichetta"], "quando": datetime.now().timestamp()}
    elif st.session_state.get("cs_ultimo") and not st.session_state.get("_cs_ripristino"):
        st.session_state.pop("cs_ultimo", None)                           # un'altra operazione: l'avviso «annulla» non vale più
    if esito["file"]:
        _cs_cancella_file_veri(esito["file"])
    return r


if "_cs_evento_prima" not in globals() and "registra_evento" in globals():
    _cs_evento_prima = registra_evento


def registra_evento(d, tipo, riga, *a, **k):
    """Un prodotto «consumato» o «buttato» è già nelle statistiche: non finisce nel Cestino."""
    try:
        if tipo in ("consumato", "sprecato", "scaduto", "buttato") and isinstance(riga, dict) and riga.get("id"):
            st.session_state.setdefault("_cs_eventi", set()).add(riga["id"])
    except Exception:
        pass
    return _cs_evento_prima(d, tipo, riga, *a, **k)


if "_cs_fa_cancella_prima" not in globals() and "_fa_cancella_files" in globals():
    _cs_fa_cancella_prima = _fa_cancella_files


def _cs_segna_file(ids):
    pers = _cs_percorso_personale()
    quando = _cs_ora()

    def _m(d):
        lista = d.setdefault(CS_FILE, [])
        presenti = {x.get("id") for x in lista if isinstance(x, dict)}
        for i in ids:
            if i not in presenti:
                lista.append({"id": i, "quando": quando})
    try:
        _cs_salva_file_prima(pers, _m, "Cestino: file in attesa")             # NON si cancellano ora: si cancellano alla scadenza o con «Elimina per sempre»
        carica_dati.clear()
    except Exception:
        _cs_fa_cancella_prima(ids)


def _fa_cancella_files(ids):
    ids = [i for i in (ids or []) if i]
    if not ids or not _cs_percorso_personale() or not cs_attivo():
        return _cs_fa_cancella_prima(ids)
    if st.session_state.get("_cs_nel_salvataggio"):                           # chiamata dentro un altro salvataggio: si mette in coda e si segna appena finisce
        st.session_state.setdefault("_cs_file_coda", []).extend(ids)
        return None
    _cs_segna_file(ids)


# ---------------------------------------------------------------------------------------------------------------------
# ripristino, eliminazione per sempre, impostazioni
# ---------------------------------------------------------------------------------------------------------------------
def _cs_risolvi(d, percorso):
    o = d
    for i, passo in enumerate(percorso):
        if isinstance(passo, str):
            if not isinstance(o, dict):
                return None
            if passo not in o:
                o[passo] = [] if i == len(percorso) - 1 else {}
            o = o[passo]
        else:
            if not isinstance(o, list):
                return None
            o = next((x for x in o if isinstance(x, dict) and x.get("id") == passo[1]), None)
            if o is None:
                return None
    return o if isinstance(o, list) else None


def cs_leggi():
    pers = _cs_percorso_personale()
    if not pers:
        return [], 30
    try:
        d = carica_dati(crea_archivio(), pers)
    except Exception:
        return [], 30
    return [r for r in (d.get(CS) or []) if isinstance(r, dict)], _cs_giorni(d)


def _cs_gruppo(d, rid):
    """I record di un gruppo (o il singolo record), dal più «alto» al più «basso» (prima i contenitori)."""
    cest = [r for r in (d.get(CS) or []) if isinstance(r, dict)]
    rec = next((r for r in cest if r.get("id") == rid or r.get("gruppo") == rid), None)
    if not rec:
        return []
    g = rec.get("gruppo")
    mem = [r for r in cest if r.get("gruppo") == g] if g else [rec]
    return sorted(mem, key=lambda r: len(r.get("percorso") or []))


def cs_ripristina(rid):
    """Rimette a posto l'elemento (o tutto il gruppo eliminato insieme) con quello che contiene. Ritorna (ok, messaggio)."""
    pers = _cs_percorso_personale()
    esito = {"ok": False, "msg": "Non l'ho trovato nel Cestino.", "n": 0}

    def _m(d):
        mem = _cs_gruppo(d, rid)
        if not mem:
            return
        fatti = 0
        for rec in mem:
            cont = _cs_risolvi(d, rec.get("percorso") or [])
            if cont is None:
                continue
            voce = rec["voce"]
            if not any(isinstance(x, dict) and x.get("id") == voce.get("id") for x in cont):
                cont.append(voce)
            d[CS].remove(rec)
            fatti += 1
            pend = d.get(CS_FILE)
            if isinstance(pend, list):
                fil = set(_cs_file_di(voce))
                d[CS_FILE] = [p_ for p_ in pend if p_.get("id") not in fil]
        if not d.get(CS):
            d.pop(CS, None)
        esito["n"] = fatti
        nome = mem[0].get("etichetta", "Elemento")
        if fatti:
            try:
                _rm_scrivi(d, [("ripristinato", mem[0].get("sezione", "Altro"), nome + (f" e altri {fatti - 1}" if fatti > 1 else ""), [], mem[0].get("c", ""))], _cs_ora())
            except Exception:
                pass
        if fatti == len(mem):
            esito["ok"], esito["msg"] = True, f"✅ «{nome}» è tornato al suo posto" + (f", con {fatti - 1} elementi collegati." if fatti > 1 else ".")
        elif fatti:
            esito["ok"], esito["msg"] = True, f"✅ Ripristinati {fatti} elementi su {len(mem)}: per gli altri manca l'elemento che li conteneva (ripristina prima quello)."
        else:
            esito["msg"] = "Non posso rimetterlo a posto: l'elemento che lo conteneva (per esempio il veicolo o il profilo) è stato eliminato. Ripristina prima quello."
    st.session_state["_cs_pausa"] = True
    try:
        _cs_salva_file_prima(pers, _m, "Cestino: ripristinato")
        carica_dati.clear()
    finally:
        st.session_state.pop("_cs_pausa", None)
    return esito["ok"], esito["msg"]


def cs_elimina_per_sempre(rids):
    """Elimina per sempre (con i file allegati) uno o più elementi/gruppi. Ritorna quanti elementi."""
    pers = _cs_percorso_personale()
    risultato = {"n": 0, "file": []}

    def _m(d):
        for rid in list(rids):
            for rec in _cs_gruppo(d, rid):
                d[CS].remove(rec)
                risultato["file"] += _cs_file_di(rec.get("voce"))
                risultato["n"] += 1
        if not d.get(CS):
            d.pop(CS, None)
        pend = d.get(CS_FILE)
        if isinstance(pend, list):
            d[CS_FILE] = [p_ for p_ in pend if p_.get("id") not in risultato["file"]]
    st.session_state["_cs_pausa"] = True
    try:
        _cs_salva_file_prima(pers, _m, "Cestino: eliminato per sempre")
        carica_dati.clear()
    finally:
        st.session_state.pop("_cs_pausa", None)
    _cs_cancella_file_veri(risultato["file"])
    return risultato["n"]


def cs_imposta_giorni(g):
    pers = _cs_percorso_personale()
    if pers and g in _CS_GIORNI:
        _cs_salva_file_prima(pers, lambda d: d.setdefault("impostazioni", {}).__setitem__("cestino_giorni", g), "Cestino: giorni di conservazione")
        carica_dati.clear()


# ---------------------------------------------------------------------------------------------------------------------
# lo schermo
# ---------------------------------------------------------------------------------------------------------------------
def _cs_quando(rec, giorni):
    try:
        dt = datetime.strptime(rec["eliminato_il"], "%Y-%m-%d %H:%M")
        resta = (dt + timedelta(days=giorni) - datetime.strptime(_cs_ora(), "%Y-%m-%d %H:%M")).days
        return f"eliminato il {dt.strftime('%d/%m/%Y')} alle {dt.strftime('%H:%M')} · si cancella da solo " + ("oggi" if resta <= 0 else f"tra {resta} giorni" if resta > 1 else "domani")
    except Exception:
        return ""


def cs_barra():
    """L'avviso «spostato nel Cestino · Annulla» dopo un'eliminazione (vale per pochi secondi)."""
    u = st.session_state.get("cs_ultimo")
    if not u or not cs_attivo():
        return
    if datetime.now().timestamp() - u.get("quando", 0) > 40:
        st.session_state.pop("cs_ultimo", None)
        return
    c1, c2 = st.columns([3, 1], gap="small", vertical_alignment="center")
    c1.info(f"🗑️ **{u['etichetta']}**" + (f" e altri {u['n'] - 1}" if u["n"] > 1 else "") + " spostato nel Cestino: lo puoi ripristinare.")
    if c2.button("↩️ Annulla", key="cs_annulla", width="stretch"):
        st.session_state["_cs_ripristino"] = True
        msg = ""
        for rid in u["ids"]:
            ok, m = cs_ripristina(rid)
            msg = m
        st.session_state.pop("_cs_ripristino", None)
        st.session_state.pop("cs_ultimo", None)
        st.session_state["messaggio"] = msg
        st.rerun()


def _cs_dialogo_per_sempre(rids, etichetta):
    @st.dialog("🗑️ Eliminare per sempre?")
    def _f():
        st.warning(f"Elimino per sempre **{etichetta}**" + (" e tutti gli allegati" if rids else "") + ". Questa operazione non si può annullare.")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("🗑️ Sì, per sempre", key="cs_perse_ok", type="primary", width="stretch"):
            n = cs_elimina_per_sempre(set(rids))
            st.session_state["messaggio"] = f"🗑️ Eliminati per sempre: {n}."
            st.rerun()
        if c2.button("No", key="cs_perse_no", width="stretch"):
            st.rerun()
    _f()


def _cs_casa_vista():
    """La casa guardata adesso in Casa («» = la principale): nella sezione Casa si vedono solo le cose di quella casa."""
    return str(st.session_state.get("ca_casa_sel") or "")


def _cs_della_sezione(r, sezione):
    if sezione and r.get("sezione") != sezione:
        return False
    if sezione == "Casa" and str(r.get("c", "") or "") != _cs_casa_vista():
        return False
    return True


def cs_pagina(sezione=None, chiave="cs"):
    """Il Cestino: elenco, ripristina, elimina per sempre. `sezione` = solo quella sezione."""
    recs, giorni = cs_leggi()
    mie = [r for r in recs if _cs_della_sezione(r, sezione)]
    if not mie:
        st.caption("Il Cestino è vuoto." + (" Quello che elimini finisce qui e lo puoi ripristinare per " + str(giorni) + " giorni." if not sezione else ""))
    gruppi = {}
    for r in mie:
        gruppi.setdefault(r.get("gruppo") or r["id"], []).append(r)
    for gid, mem in sorted(gruppi.items(), key=lambda kv: max(x.get("eliminato_il", "") for x in kv[1]), reverse=True):
        r = sorted(mem, key=lambda x: len(x.get("percorso") or []))[0]                       # l'elemento «principale» del gruppo
        con_file = any(_cs_file_di(x.get("voce")) for x in mem)
        st.markdown(f"**{_cs_icona(r.get('sezione'))} {r.get('etichetta', 'Elemento')}**" + (f" e altri {len(mem) - 1}" if len(mem) > 1 else "") + (f" · {r['sezione']}" if not sezione else ""))
        st.caption(_cs_quando(r, giorni) + (" · con allegati" if con_file else "") + (" · eliminati insieme" if len(mem) > 1 else ""))
        c1, c2 = st.columns(2, gap="small")
        if c1.button("↩️ Ripristina", key=f"{chiave}_rip_{gid}", width="stretch"):
            ok, m = cs_ripristina(gid)
            st.session_state["messaggio"] = m
            st.rerun()
        if c2.button("🗑️ Elimina per sempre", key=f"{chiave}_del_{gid}", width="stretch"):
            _cs_dialogo_per_sempre([gid], r.get("etichetta", "questo elemento") + (f" e altri {len(mem) - 1}" if len(mem) > 1 else ""))
    if len(gruppi) > 1 and not sezione:
        if st.button("🗑️ Svuota tutto il Cestino", key=f"{chiave}_svuota", width="stretch"):
            _cs_dialogo_per_sempre(list(gruppi), f"tutti gli elementi ({len(mie)})")
    if not sezione:
        g = st.selectbox("Per quanti giorni tenere gli elementi eliminati", _CS_GIORNI, index=_CS_GIORNI.index(giorni), format_func=lambda x: f"{x} giorni", key=f"{chiave}_giorni")
        if g != giorni:
            cs_imposta_giorni(g)
            st.rerun()


_RM_ICONE = {"aggiunto": "➕ Aggiunto", "modificato": "✏️ Modificato", "eliminato": "🗑️ Eliminato", "ripristinato": "↩️ Ripristinato", "altro": "…"}


def rm_leggi():
    pers = _cs_percorso_personale()
    if not pers:
        return []
    try:
        d = carica_dati(crea_archivio(), pers)
    except Exception:
        return []
    return [r for r in (d.get(CS_REG) or []) if isinstance(r, dict)]


def rm_pagina(sezione=None, chiave="rm", massimo=30):
    """Lo storico delle modifiche: cosa è stato aggiunto, modificato, eliminato o ripristinato, e quando (senza il contenuto)."""
    reg = [r for r in rm_leggi() if (not sezione or (r.get("sez") == sezione and (sezione != "Casa" or str(r.get("c", "") or "") == _cs_casa_vista())))]
    st.caption("È il **registro delle operazioni** (non l'elenco dei contenuti): ogni riga dice cosa è stato fatto e quando. Non contiene i dati veri, solo il nome dell'elemento e quali campi sono cambiati.")
    if not reg:
        st.caption("Per ora non c'è niente: le prossime operazioni compariranno qui.")
        return
    for r in sorted(reg, key=lambda x: x.get("q", ""), reverse=True)[:massimo]:
        try:
            dt = datetime.strptime(r["q"], "%Y-%m-%d %H:%M")
            quando = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            quando = r.get("q", "")
        campi = (" — campi: " + ", ".join(r["campi"])) if r.get("campi") else ""
        st.markdown(f"{_RM_ICONE.get(r.get('az'), r.get('az'))} · **{r.get('e', 'Elemento')}**" + (f" · {r.get('sez')}" if not sezione else "") + f"  \n<small>{quando}{campi}</small>", unsafe_allow_html=True)
    if len(reg) > massimo:
        st.caption(f"Ho mostrato le ultime {massimo} operazioni su {len(reg)}.")


def cs_riquadro(sezione):
    """Una linguetta «🗑️ Cestino (N)» in fondo a una sezione, solo con gli elementi di quella sezione."""
    if not cs_attivo():
        return
    recs, _g = cs_leggi()
    n = sum(1 for r in recs if _cs_della_sezione(r, sezione))
    with st.expander(f"🗑️ Cestino di questa sezione ({n})"):
        cs_pagina(sezione, "cs_" + sezione.lower())
    with st.expander("🕘 Storico delle modifiche di questa sezione"):
        rm_pagina(sezione, "rm_" + sezione.lower())


# ---------------------------------------------------------------------------------------------------------------------
# aggancio alle schermate esistenti
# ---------------------------------------------------------------------------------------------------------------------
if "_cs_nav_prima" not in globals() and "nav_pagine" in globals():
    _cs_nav_prima = nav_pagine


def nav_pagine(corrente):
    r = _cs_nav_prima(corrente)
    try:
        cs_barra()
    except Exception:
        pass
    return r


if "_cs_schermata_prima" not in globals() and "schermata_farmacia" in globals():
    _cs_schermata_prima = schermata_farmacia


def schermata_farmacia():
    r = _cs_schermata_prima()
    try:
        sez = {"salute": "Salute", "documenti": "Salute", "archivio": "Salute", "casa": "Casa", "lavoro": "Lavoro", "auto": "Auto"}.get(st.session_state.get("sezione_home") or "salute")
        if sez:
            cs_riquadro(sez)
    except Exception:
        pass
    return r


if "_cs_utilita_prima" not in globals() and "schermata_utilita" in globals():
    _cs_utilita_prima = schermata_utilita


def schermata_utilita():
    r = _cs_utilita_prima()
    try:
        if cs_attivo():
            recs, _g = cs_leggi()
            with st.expander(f"🗑️ Cestino ({len(recs)})"):
                cs_pagina(None, "cs_ut")
            with st.expander("🕘 Storico delle modifiche"):
                rm_pagina(None, "rm_ut")
    except Exception:
        pass
    return r
