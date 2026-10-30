# -*- coding: utf-8 -*-
"""DISPENSA DI FAMIGLIA: una dispensa comune, condivisa davvero tra i familiari, con ruoli, storico e annullamento.

COME È FATTA
  • La dispensa comune è un file solo nell'archivio privato (famiglia/dispensa.json), con la stessa struttura delle dispense personali:
    per questo tutte le schermate che già esistono (schede, tabella, aggiungi, modifica, spesa, statistiche) funzionano uguali anche sulla comune.
    Chi ne ha il diritto vede in alto la scelta «La mia dispensa» / «Dispensa di famiglia».
  • Tre ruoli. AMMINISTRATORE (il capo famiglia): fa tutto, assegna i ruoli, annulla le operazioni sbagliate. COLLABORATORE: inserisce prodotti,
    cambia quantità e scadenze, registra i consumi, usa la lista della spesa; non elimina prodotti (salvo registrando che sono finiti o buttati).
    VISUALIZZATORE: guarda e basta. I ruoli si assegnano nella scheda Utenti, accanto a «Parte della famiglia».
  • Ogni salvataggio sulla dispensa comune passa da un punto solo (salva): lì si controlla il ruolo, si confrontano i prodotti prima e dopo,
    si scrive nello STORICO chi ha fatto cosa e quando (con i dati di prima e di dopo) e si aggiorna il numero di versione.
  • Modifiche contemporanee: l'archivio rilegge i dati più recenti e riapplica l'operazione (le quantità si sommano giuste anche se in due consumano
    insieme). Se due persone cambiano lo stesso campo nello stesso istante vince l'ultima, ma tutto resta nello storico e l'amministratore può tornare indietro.
  • Aggiornamento: ogni 10 secondi l'app controlla se qualcuno ha cambiato la dispensa; se chi guarda non sta usando l'app si aggiorna da sola, altrimenti
    compare «Aggiorna».
Caricato da app_dispensa.py dopo account.py (ridefinisce salva() per la dispensa comune)."""
import copy
import time
import uuid

import streamlit as st

FD_PERCORSO = "famiglia/dispensa.json"
FD_RUOLI = {"amministratore": "👑 Amministratore", "collaboratore": "✏️ Collaboratore", "visualizzatore": "👁️ Visualizzatore"}
FD_RUOLI_ASSEGNABILI = ["visualizzatore", "collaboratore"]
_FD_SERVIZIO = ("rev", "mod_da", "mod_il")
_FD_MAX_OPERAZIONI = 400
_FD_MAX_BYTE_STORICO = 600_000
_FD_GRANDE = 2000                      # i testi più lunghi (foto in base64) non si copiano nello storico, salvo per i prodotti eliminati
_FD_ETICHETTE = {"quantita": "quantità", "scadenza": "scadenza", "nome": "nome", "marca": "marca", "note": "note", "posto": "dove", "unita": "unità",
                 "per_chi": "sezione", "formato_valore": "contenuto", "formato_unita": "misura", "acquisto": "acquisto", "preso": "preso", "q_da_comprare": "da comprare"}


class FdPermesso(Exception):
    """Operazione non permessa dal ruolo."""


class FdConflitto(Exception):
    """L'annullamento tocca qualcosa che è stato cambiato dopo."""

    def __init__(self, problemi):
        super().__init__("; ".join(problemi))
        self.problemi = problemi


# ---------------------------------------------------------------------------------------------------------------------
# Ruoli
# ---------------------------------------------------------------------------------------------------------------------
def fd_ruolo_di(sess, utenti):
    """Il ruolo di una persona nella dispensa di famiglia, oppure None se non ne fa parte."""
    if not sess:
        return None
    if sess.get("admin"):
        return "amministratore"
    u = next((x for x in utenti if x.get("id") == sess.get("uid")), None)
    if not u or not u.get("attivo", True) or not u.get("famiglia"):
        return None
    return u["ruolo_fam"] if u.get("ruolo_fam") in FD_RUOLI_ASSEGNABILI else "visualizzatore"


def fd_ruolo():
    try:
        return fd_ruolo_di(st.session_state.get("sess"), leggi_utenti())
    except Exception:
        return None


def fd_attivo():
    """Si sta guardando la dispensa di famiglia (e se ne ha il diritto)."""
    return st.session_state.get("fd_modo") == "famiglia" and bool(fd_ruolo())


def fd_personale():
    sess = st.session_state.get("sess") or {}
    return f"dispense/{sess.get('uid', 'prova')}.json"


def fd_prepara():
    """Va chiamata prima di leggere i dati della dispensa: sceglie quale file usare (personale o di famiglia). Salute e le altre pagine restano sempre personali."""
    if "sess" not in st.session_state:
        return
    if st.session_state.get("fd_modo") == "famiglia" and not st.session_state.get("farmacia_aperta") and fd_ruolo():
        st.session_state["percorso"] = FD_PERCORSO
        st.session_state["fd_in_uso"] = True
    else:
        if st.session_state.get("fd_modo") == "famiglia" and not fd_ruolo():
            st.session_state["fd_modo"] = "personale"          # ha perso il diritto: torna alla sua
        if st.session_state.get("percorso") == FD_PERCORSO or st.session_state.get("fd_in_uso"):
            st.session_state["percorso"] = fd_personale()
        st.session_state["fd_in_uso"] = False


def fd_ripristina():
    """A fine pagina: il percorso torna sempre quello personale, qualunque cosa sia successo."""
    if st.session_state.get("percorso") == FD_PERCORSO:
        st.session_state["percorso"] = fd_personale()
    st.session_state["fd_in_uso"] = False


# ---------------------------------------------------------------------------------------------------------------------
# Differenze, storico, annullamento (funzioni pure: si possono provare senza Streamlit)
# ---------------------------------------------------------------------------------------------------------------------
def _pulito(a):
    return {k: v for k, v in a.items() if k not in _FD_SERVIZIO}


def _snap(a, tieni_grandi=False):
    if a is None:
        return None
    return {k: (v if (tieni_grandi or not isinstance(v, str) or len(v) <= _FD_GRANDE) else "…") for k, v in copy.deepcopy(a).items()}


def fd_diff(prima, dopo, lista="articoli"):
    """Cosa è cambiato tra due elenchi di voci (per id): aggiunte, modificate, eliminate."""
    p = {a["id"]: a for a in prima if isinstance(a, dict) and "id" in a}
    d = {a["id"]: a for a in dopo if isinstance(a, dict) and "id" in a}
    cambi = []
    for i, a in d.items():
        if i not in p:
            cambi.append({"tipo": "agg", "lista": lista, "id": i, "nome": a.get("nome", ""), "prima": None, "dopo": _snap(a)})
        elif _pulito(p[i]) != _pulito(a):
            cambi.append({"tipo": "mod", "lista": lista, "id": i, "nome": a.get("nome", ""), "prima": _snap(p[i]), "dopo": _snap(a)})
    for i, a in p.items():
        if i not in d:
            cambi.append({"tipo": "rim", "lista": lista, "id": i, "nome": a.get("nome", ""), "prima": _snap(a, True), "dopo": None})
    return cambi


def fd_descrivi_cambio(c):
    lista = "🛒 " if c.get("lista") == "spesa" else ""
    if c["tipo"] == "agg":
        return f"{lista}Aggiunto «{c['nome']}»"
    if c["tipo"] == "rim":
        return f"{lista}Eliminato «{c['nome']}»"
    pezzi = []
    for k in sorted(set(c["prima"]) | set(c["dopo"])):
        if k in _FD_SERVIZIO or c["prima"].get(k) == c["dopo"].get(k):
            continue
        a, b = c["prima"].get(k), c["dopo"].get(k)
        pezzi.append(f"{_FD_ETICHETTE.get(k, k)}: {'—' if a in (None, '') else a} → {'—' if b in (None, '') else b}")
    return f"{lista}«{c['nome']}»: " + ("; ".join(pezzi[:3]) + (" …" if len(pezzi) > 3 else "") if pezzi else "modificato")


def _fd_applica(d, fn, messaggio, ruolo, uid, nome, ora):
    """Il cuore: applica fn ai dati, controlla i permessi, timbra i prodotti cambiati e scrive l'operazione nello storico. Solleva FdPermesso."""
    prima_a, prima_s = copy.deepcopy(d.get("articoli", [])), copy.deepcopy(d.get("spesa", []))
    n_eventi = len(d.get("storico", []))
    fn(d)
    cambi = fd_diff(prima_a, d.get("articoli", []), "articoli") + fd_diff(prima_s, d.get("spesa", []), "spesa")
    if not cambi:
        return
    if ruolo == "collaboratore":
        eventi_nuovi = d.get("storico", [])[n_eventi:]
        nomi_motivati = {str(e.get("nome", "")).strip().lower() for e in eventi_nuovi}
        for c in cambi:
            if c["tipo"] == "rim" and c["lista"] == "articoli" and (c["nome"] or "").strip().lower() not in nomi_motivati:
                raise FdPermesso("Solo l'amministratore può eliminare i prodotti. Puoi dire che li hai consumati o buttati, oppure correggerli con «Modifica».")
    for c in cambi:                                                    # timbro i prodotti toccati
        if c["tipo"] in ("agg", "mod") and c["lista"] == "articoli":
            a = next((x for x in d["articoli"] if x.get("id") == c["id"]), None)
            if a is not None:
                a["rev"] = int((c["prima"] or {}).get("rev", 0) or 0) + 1
                a["mod_da"], a["mod_il"] = nome, ora
    ops = d.setdefault("operazioni", [])
    ops.append({"id": uuid.uuid4().hex[:10], "t": ora, "uid": uid, "chi": nome, "msg": messaggio or "", "cambi": cambi, "annullata": False})
    while len(ops) > _FD_MAX_OPERAZIONI or (len(ops) > 20 and len(repr(ops)) > _FD_MAX_BYTE_STORICO):
        ops.pop(0)
    d["versione"] = int(d.get("versione", 0) or 0) + 1


def fd_annulla_su(d, op_id, forza=False):
    """Annulla un'operazione dello storico (lavora su d). Se dopo è stato cambiato qualcosa di quello che tocca, avvisa (FdConflitto) a meno che forza=True."""
    op = next((o for o in d.get("operazioni", []) if o.get("id") == op_id), None)
    if op is None:
        raise FdConflitto(["l'operazione non c'è più nello storico"])
    if op.get("annullata"):
        raise FdConflitto(["questa operazione è già stata annullata"])
    problemi = []
    for c in reversed(op["cambi"]):
        lista = d.setdefault(c.get("lista", "articoli"), [])
        corrente = next((a for a in lista if a.get("id") == c["id"]), None)
        if c["tipo"] == "agg":
            if corrente is None:
                continue
            if not forza and _snap(_pulito(corrente)) != _snap(_pulito(c["dopo"])):
                problemi.append(f"«{c['nome']}» è stato cambiato dopo")
                continue
            lista.remove(corrente)
        elif c["tipo"] == "mod":
            if corrente is None:
                problemi.append(f"«{c['nome']}» non c'è più")
                continue
            if not forza and _snap(_pulito(corrente)) != _snap(_pulito(c["dopo"])):
                problemi.append(f"«{c['nome']}» è stato cambiato dopo")
                continue
            for k, v in c["prima"].items():
                if k in _FD_SERVIZIO or v == "…":
                    continue
                corrente[k] = copy.deepcopy(v)
            for k in list(corrente):
                if k not in c["prima"] and k not in _FD_SERVIZIO:
                    corrente.pop(k)
        elif c["tipo"] == "rim":
            if corrente is None:
                lista.append(copy.deepcopy(c["prima"]))
    if problemi and not forza:
        raise FdConflitto(problemi)
    op["annullata"] = True


# ---------------------------------------------------------------------------------------------------------------------
# Il punto unico di scrittura
# ---------------------------------------------------------------------------------------------------------------------
if "_fd_salva_originale" not in globals():                          # (se il file venisse caricato due volte, non si riavvolge su se stesso)
    _fd_salva_originale = salva


def salva(fn, messaggio):                                           # noqa: F811 — sostituisce salva() di parte2.py
    """Come prima per la dispensa personale; per quella di famiglia controlla il ruolo e scrive lo storico."""
    if st.session_state.get("percorso") != FD_PERCORSO:
        return _fd_salva_originale(fn, messaggio)
    ruolo = fd_ruolo()
    if ruolo not in ("amministratore", "collaboratore"):
        raise FdPermesso("Nella dispensa di famiglia hai solo il permesso di consultare.")
    sess = st.session_state["sess"]
    ora = adesso().isoformat(timespec="seconds")
    salva_file(FD_PERCORSO, lambda d: _fd_applica(d, fn, messaggio, ruolo, sess.get("uid", ""), sess.get("nome", ""), ora), messaggio)


def fd_annulla(op_id, forza=False):
    """Solo l'amministratore. Annulla un'operazione registrando l'annullamento come una nuova operazione."""
    if fd_ruolo() != "amministratore":
        raise FdPermesso("Solo l'amministratore può annullare le operazioni.")
    salva_file(FD_PERCORSO, lambda d: _fd_applica(d, lambda dd: fd_annulla_su(dd, op_id, forza), "↩️ Operazione annullata", "amministratore",
                                                   st.session_state["sess"].get("uid", ""), st.session_state["sess"].get("nome", ""),
                                                   adesso().isoformat(timespec="seconds")), "Dispensa di famiglia: operazione annullata")


# ---------------------------------------------------------------------------------------------------------------------
# Schermate
# ---------------------------------------------------------------------------------------------------------------------
def _fd_cambia_modo():
    st.session_state["fd_modo"] = st.session_state.get("fd_modo_w") or "personale"


def fd_selettore():
    """In cima alla dispensa: scelta fra la propria e quella di famiglia (solo per chi ne fa parte) e avvisi di ruolo e di aggiornamento."""
    ruolo = fd_ruolo()
    if not ruolo:
        return
    fd_nascondi_modifiche(ruolo == "visualizzatore" and st.session_state.get("fd_modo") == "famiglia")
    st.segmented_control("Quale dispensa", ["personale", "famiglia"], key="fd_modo_w", default=st.session_state.get("fd_modo", "personale"),
                         format_func=lambda m: "🧑 La mia dispensa" if m == "personale" else "👨‍👩‍👧 Dispensa di famiglia", on_change=_fd_cambia_modo,
                         label_visibility="collapsed", width="stretch")
    if st.session_state.get("fd_modo") == "famiglia":
        st.caption(f"👨‍👩‍👧 Dispensa di famiglia · il tuo ruolo: **{FD_RUOLI[ruolo]}**")
        if ruolo == "visualizzatore":
            st.info("👁️ Puoi consultare prodotti, quantità e scadenze, ma non modificarli.")
        try:
            st.session_state["fd_versione_vista"] = int(carica_dati(crea_archivio(), FD_PERCORSO).get("versione", 0) or 0)
        except Exception:
            pass
        st.session_state["fd_ultimo_giro"] = time.time()
        fd_sync()
        if ruolo in ("amministratore", "collaboratore"):
            fd_porta_prodotti()


def fd_copie_da_personale(articoli, scelti):
    """Copie (con id nuovi) dei prodotti scelti della dispensa personale, pronte per la dispensa di famiglia."""
    copie = []
    for a in articoli:
        if a.get("id") in scelti:
            c = copy.deepcopy(a)
            c["id"] = uuid.uuid4().hex[:10]
            for k in _FD_SERVIZIO:
                c.pop(k, None)
            copie.append(c)
    return copie


def fd_porta_prodotti():
    """«Porta qui prodotti dalla mia dispensa»: copia (non sposta) alcuni prodotti personali nella dispensa di famiglia."""
    try:
        miei = carica_dati(crea_archivio(), fd_personale()).get("articoli", [])
    except Exception:
        miei = []
    if not miei:
        return
    with st.expander("📥 Porta qui prodotti dalla mia dispensa personale"):
        st.caption("Li **copio** nella dispensa di famiglia: nella tua personale restano dove sono.")
        scelti = st.multiselect("Quali prodotti", [a["id"] for a in miei], key="fd_porta_sel",
                                format_func=lambda i: next((f"{a.get('nome', '')} · {a.get('scadenza') or 'senza scadenza'}" for a in miei if a["id"] == i), i))
        if st.button("📥 Copia nella dispensa di famiglia", key="fd_porta_ok", width="stretch", disabled=not scelti):
            copie = fd_copie_da_personale(miei, set(scelti))
            try:
                salva(lambda d: d.setdefault("articoli", []).extend(copie), f"Portati {len(copie)} prodotti dalla dispensa personale")
                st.session_state["messaggio"] = f"📥 Copiati {len(copie)} prodotti nella dispensa di famiglia."
                st.session_state.pop("fd_porta_sel", None)
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito: {e}")


_FD_JS_SOLA_LETTURA = r"""
(function () {
  var w = window, d = w.document;
  try {
    w.__fdSL = __ATTIVO__;
    if (w.__fdSLpronto) { w.__fdSLagg(); return; }
    w.__fdSLpronto = true;
    var stile = d.createElement('style'); stile.id = 'fd-sola-lettura'; d.head.appendChild(stile);
    var css = '[class*="st-key-cest_"],[class*="st-key-modif_"],[class*="st-key-spesa_aggiungi"],[class*="st-key-spesa_salva"],[class*="st-key-spesa_pulisci"],' +
              '[class*="st-key-spesa_in_dispensa"]{display:none !important}';
    w.__fdSLagg = function () {
      stile.textContent = w.__fdSL ? css : '';
      var tl = d.querySelector('[data-baseweb="tab-list"]');            // le schede «Aggiungi» e «Gestisci» (2ª e 3ª)
      if (!tl) return;
      var tabs = tl.querySelectorAll('[role="tab"]');
      [1, 2].forEach(function (i) { if (tabs[i]) tabs[i].style.display = w.__fdSL ? 'none' : ''; });
    };
    new w.MutationObserver(function () { w.__fdSLagg(); }).observe(d.body, {childList: true, subtree: true});
    w.__fdSLagg();
  } catch (e) { /* se non si può, restano i messaggi di sola consultazione */ }
})();
"""


def fd_nascondi_modifiche(attivo):
    """Ai visualizzatori nasconde i pulsanti che modificano (Elimina, Modifica, Aggiungi alla lista…) e le schede Aggiungi e Gestisci; agli altri li rimostra."""
    if "_nav_pagina_js" not in globals():
        return
    _nav_pagina_js(_FD_JS_SOLA_LETTURA.replace("__ATTIVO__", "true" if attivo else "false"))


def _fd_aggiorna_ora():
    carica_dati.clear()


@st.fragment(run_every=10)
def fd_sync():
    """Ogni 10 secondi: se qualcuno ha cambiato la dispensa, la aggiorna da sola (se non si sta usando l'app) oppure propone «Aggiorna»."""
    try:
        v = int(carica_dati(crea_archivio(), FD_PERCORSO).get("versione", 0) or 0)
    except Exception:
        return
    if v == st.session_state.get("fd_versione_vista", v):
        return
    if time.time() - st.session_state.get("fd_ultimo_giro", 0) > 45:
        st.rerun()
    else:
        st.info("🔄 Qualcuno ha aggiornato la dispensa di famiglia.")
        if st.button("Aggiorna", key="fd_aggiorna", on_click=_fd_aggiorna_ora):
            st.rerun()


def fd_selettore_ruolo(u):
    """Nella scheda Utenti (amministratore): il ruolo di un familiare nella dispensa di famiglia."""
    attuale = u.get("ruolo_fam") if u.get("ruolo_fam") in FD_RUOLI_ASSEGNABILI else "visualizzatore"
    scelto = st.selectbox("Ruolo nella dispensa di famiglia", FD_RUOLI_ASSEGNABILI, index=FD_RUOLI_ASSEGNABILI.index(attuale), key=f"fdr_{u['id']}",
                          format_func=lambda r: FD_RUOLI[r])
    if scelto != attuale:
        def _imposta(d, uid=u["id"], val=scelto):
            for x in d.get("utenti", []):
                if x["id"] == uid:
                    x["ruolo_fam"] = val
        try:
            salva_file("utenti.json", _imposta, f"Ruolo famiglia: {u['nome']}")
            st.rerun()
        except Exception as e:
            st.error(t("Non sono riuscito a salvare: {e}", e=e))


def _fd_ora_it(iso):
    try:
        return f"{iso[8:10]}/{iso[5:7]} {iso[11:16]}"
    except Exception:
        return iso


def fd_scheda_storico():
    """La scheda «Storico»: chi ha fatto cosa e quando; l'amministratore può annullare."""
    dati = carica_dati(crea_archivio(), FD_PERCORSO)
    ops = list(reversed(dati.get("operazioni", [])))
    admin = fd_ruolo() == "amministratore"
    st.markdown("### 🕘 Storico della dispensa di famiglia")
    st.caption("Ogni modifica con chi l'ha fatta e quando." + (" Puoi annullare quelle sbagliate: l'annullamento si registra e si può a sua volta annullare." if admin else " Solo l'amministratore può annullare."))
    solo_elim = st.toggle("Solo le eliminazioni", key="fd_solo_elim")
    if solo_elim:
        ops = [o for o in ops if any(c["tipo"] == "rim" for c in o["cambi"])]
    if not ops:
        st.info("Non c'è ancora niente nello storico.")
        return
    for o in ops[:60]:
        with st.container(border=True, key=f"fd_op_{o['id']}"):
            st.markdown(f"**{_fd_ora_it(o.get('t', ''))}** · 👤 {o.get('chi', '')}" + (" · ↩️ _annullata_" if o.get("annullata") else ""))
            for c in o["cambi"][:6]:
                st.markdown("- " + fd_descrivi_cambio(c))
            if len(o["cambi"]) > 6:
                st.caption(f"… e altre {len(o['cambi']) - 6} modifiche")
            if admin and not o.get("annullata"):
                forza = st.session_state.get(f"fd_forza_{o['id']}", False)
                if st.button("↩️ Annulla questa operazione", key=f"fd_ann_{o['id']}", width="stretch"):
                    try:
                        fd_annulla(o["id"], forza)
                        st.session_state["messaggio"] = "↩️ Operazione annullata."
                        st.rerun()
                    except FdConflitto as e:
                        st.session_state[f"fd_forza_{o['id']}"] = True
                        st.warning("Attenzione: " + "; ".join(e.problemi) + ". Se vuoi annullare comunque, tocca di nuovo il pulsante.")
                    except Exception as e:
                        st.error(f"Non sono riuscito: {e}")
