# -*- coding: utf-8 -*-
"""AUTO · BASE CONDIVISA DELLE SPIE E DEI GUASTI — la memoria interna dell'app, a disposizione di tutti.

• Ogni spia riconosciuta dall'IA (con la foto o a parole) e ogni voce aggiunta a mano entra in una base condivisa da TUTTE le persone che usano questa app (file conoscenza/spie.json nell'archivio dei dati).
  Contiene solo TESTO: nome, colore, urgenza, significato, azioni, cause, come è fatto il simbolo, mezzo (tipo, marca, modello). Mai foto, mai nomi di persone.
• La ricerca si fa prima qui, dentro l'app: gratis e subito. L'IA serve solo quando la spia non c'è ancora.
• Una voce scritta da un'IA può essere SBAGLIATA: per questo ha tre stati. 🟡 da verificare (nuova) · ✅ verificata (almeno 2 persone diverse l'hanno confermata con 👍, o l'amministratore) · ⚠️ contestata (👎 o l'amministratore).
  Ognuno può votare una volta per voce. L'amministratore può confermare, contestare o eliminare. L'avviso di PERICOLO per le spie rosse lo decide sempre il programma, non la base.
• Il modello del mezzo (marca, modello, anno) si può scrivere a mano: serve per una ricerca più precisa ed è facoltativo. Le voci specifiche per un modello vengono prima di quelle valide per tutti.
• Si spegne con BASE_SPIE = "no" nei Secrets; ognuno può scegliere di NON contribuire («Contribuisci alla base condivisa»).
• Per portare la base in un'altra installazione dell'app: l'amministratore la esporta e la importa (copia e incolla).
Caricato dopo auto_soccorso.py."""
import hashlib
import html as _h_bd
import json
import re
import unicodedata
import uuid
from datetime import date

import streamlit as st

BD_PERCORSO = "conoscenza/spie.json"
BD_MAX = 4000
_BD_STOP = {"di", "del", "della", "dei", "delle", "e", "ed", "il", "la", "lo", "le", "un", "una", "in", "a", "al", "per", "con", "da", "su", "spia", "sistema", "avviso", "guasto", "problema", "accesa", "acceso", "che", "si", "non"}
_BD_COLORI = ("rosso", "giallo", "verde", "blu", "bianco")
_BD_ICONA = {"rosso": "🔴", "giallo": "🟡", "verde": "🟢", "blu": "🔵", "bianco": "⚪"}


# ---------------------------------------------------------------------------------------------------------------------
# utilità
# ---------------------------------------------------------------------------------------------------------------------
def bd_attiva():
    try:
        return str(st.secrets.get("BASE_SPIE", "")).strip().lower() not in ("no", "off", "0", "false", "spenta")
    except Exception:
        return True


def _bd_oggi():
    try:
        return _au_oggi().isoformat()
    except Exception:
        return date.today().isoformat()


def _bd_uid():
    sess = st.session_state.get("sess") or {}
    return hashlib.sha1(str(sess.get("uid") or sess.get("nome") or "anon").encode("utf-8")).hexdigest()[:8]


def _bd_admin():
    return bool((st.session_state.get("sess") or {}).get("admin"))


def _bd_norm(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _bd_tok(t):
    return {w for w in re.findall(r"[a-z0-9]{3,}", _bd_norm(t)) if w not in _BD_STOP}


def bd_scope(v=None):
    """Il mezzo per cui si cerca: il modello scritto a mano (facoltativo) oppure quello scelto. {tipo, marca, modello, anno} (marca e modello in minuscolo)."""
    marca = str(st.session_state.get("mz_marca", "") or "").strip()
    modello = str(st.session_state.get("mz_modello", "") or "").strip()
    anno = str(st.session_state.get("mz_anno", "") or "").strip()
    tipo = (v or {}).get("tipo_veicolo") or ""
    if not (marca or modello) and v:
        marca, modello, anno = (v.get("marca") or ""), (v.get("modello") or ""), (v.get("anno") or "")
    if not tipo:
        sel = st.session_state.get("ad_mezzo")
        tipo = sel if sel and sel != "Il veicolo scelto" else ""
    return {"tipo": tipo, "marca": _bd_norm(marca).strip(), "modello": _bd_norm(modello).strip(), "anno": anno}


def bd_scope_desc(sc, v=None):
    nome = " ".join(x for x in ((st.session_state.get("mz_marca") or (v or {}).get("marca") or sc.get("marca") or "").strip(), (st.session_state.get("mz_modello") or (v or {}).get("modello") or sc.get("modello") or "").strip(), sc.get("anno") or "") if x)
    return (nome + (f" ({sc['tipo']})" if sc.get("tipo") else "")).strip() or sc.get("tipo") or "mezzo non specificato"


# ---------------------------------------------------------------------------------------------------------------------
# la base (file condiviso)
# ---------------------------------------------------------------------------------------------------------------------
def bd_leggi():
    try:
        d = carica_dati(crea_archivio(), BD_PERCORSO)
    except Exception:
        return []
    return [e for e in (d.get("spie") or []) if isinstance(e, dict) and e.get("nome")]


def _bd_salva(fn, msg):
    def _m(d):
        d.setdefault("versione", 1)
        fn(d.setdefault("spie", []))
    salva_file(BD_PERCORSO, _m, msg)


def bd_stato(e):
    """('verificata'|'contestata'|'da_verificare', su, giu)."""
    voti = e.get("voti") or {}
    su, giu = sum(1 for x in voti.values() if x > 0), sum(1 for x in voti.values() if x < 0)
    if e.get("contestata_admin"):
        return "contestata", su, giu
    if e.get("confermata_admin") or (su >= 2 and su >= 2 * giu):
        return "verificata", su, giu
    if giu >= 2 and giu >= su:
        return "contestata", su, giu
    return "da_verificare", su, giu


def bd_registra(spia, scope, fonte, dettaglio=""):
    """Aggiunge una voce (o, se la spia c'è già per lo stesso mezzo, conta un uso in più). Ritorna (id, nuova) oppure (None, False)."""
    nome = str(spia.get("nome") or "").strip()
    colore = str(spia.get("colore") or "").lower().strip()
    if len(nome) < 3 or colore not in _BD_COLORI:
        return None, False
    marca, modello = (scope or {}).get("marca", ""), (scope or {}).get("modello", "")
    esito = {}

    def _fn(lista):
        tok = _bd_tok(nome)
        for e in lista:
            if e.get("colore") != colore or (e.get("marca") or "", e.get("modello") or "") != (marca, modello):
                continue
            b = _bd_tok(e.get("nome"))
            com = tok & b
            if com and len(com) / max(1, min(len(tok), len(b))) >= 0.6:
                e["usi"] = int(e.get("usi", 1)) + 1
                e["ultima"] = _bd_oggi()
                fonti = list(e.get("fonti") or [])
                f = (fonte + (f": {dettaglio}" if dettaglio else "")).strip()
                if f and f not in fonti:
                    fonti.append(f)
                e["fonti"] = fonti[:6]
                if not e.get("aspetto") and spia.get("aspetto"):
                    e["aspetto"] = str(spia["aspetto"])[:120]
                esito["r"] = (e["id"], False)
                return
        nuova = {"id": uuid.uuid4().hex[:12], "nome": nome[:140], "colore": colore, "urgenza": str(spia.get("urgenza") or "media")[:20], "significato": str(spia.get("significato") or "")[:500],
                 "azioni": [str(x)[:300] for x in (spia.get("azioni") or [])][:8], "cause": [str(x)[:160] for x in (spia.get("cause") or [])][:8], "aspetto": str(spia.get("aspetto") or "")[:120],
                 "simbolo_iso": str(spia.get("simbolo_iso") or "")[:40], "tipo_mezzo": (scope or {}).get("tipo", ""), "marca": marca, "modello": modello, "anno": (scope or {}).get("anno", ""),
                 "fonti": [(fonte + (f": {dettaglio}" if dettaglio else "")).strip()], "creata": _bd_oggi(), "ultima": _bd_oggi(), "usi": 1, "voti": {}}
        lista.append(nuova)
        esito["r"] = (nuova["id"], True)
        if len(lista) > BD_MAX:                                       # la base non cresce senza fine: se serve, via le voci più deboli e vecchie
            lista.sort(key=lambda x: (bd_stato(x)[0] == "verificata", int(x.get("usi", 1)), x.get("ultima", "")))
            del lista[:len(lista) - BD_MAX]
    try:
        _bd_salva(_fn, f"Base spie: {nome[:60]}")
    except Exception:
        return None, False
    return esito.get("r", (None, False))


def bd_registra_risultato(ris, scope, fonte):
    """Le spie di un'analisi dell'IA entrano nella base. Ritorna quante (nuove, aggiornate)."""
    nuove = agg = 0
    for s in (ris or {}).get("spie", []):
        _id, nuova = bd_registra(s, scope, fonte)
        if _id:
            nuove += 1 if nuova else 0
            agg += 0 if nuova else 1
    return nuove, agg


def bd_vota(eid, segno):
    uid = _bd_uid()

    def _fn(lista):
        for e in lista:
            if e.get("id") == eid:
                voti = dict(e.get("voti") or {})
                if voti.get(uid) == segno:
                    voti.pop(uid, None)                              # lo stesso voto due volte lo toglie
                else:
                    voti[uid] = segno
                e["voti"] = voti
    _bd_salva(_fn, "Base spie: voto")


def bd_admin(eid, azione):
    """Solo amministratore: 'conferma', 'contesta', 'ripristina', 'elimina'."""
    if not _bd_admin():
        return

    def _fn(lista):
        for e in list(lista):
            if e.get("id") == eid:
                if azione == "elimina":
                    lista.remove(e)
                elif azione == "conferma":
                    e["confermata_admin"], e["contestata_admin"] = True, False
                elif azione == "contesta":
                    e["confermata_admin"], e["contestata_admin"] = False, True
                else:
                    e["confermata_admin"], e["contestata_admin"] = False, False
    _bd_salva(_fn, f"Base spie: {azione}")


# ---------------------------------------------------------------------------------------------------------------------
# la ricerca
# ---------------------------------------------------------------------------------------------------------------------
def bd_cerca(q="", colore="", scope=None, limite=25, voci=None):
    """Le voci che corrispondono, le più utili per prime: verificate, specifiche per il modello, più confermate, più usate."""
    voci = voci if voci is not None else bd_leggi()
    scope = scope or {}
    qt = _bd_tok(q)
    ris = []
    for e in voci:
        if colore and e.get("colore") != colore:
            continue
        punti = 0.0
        if qt:
            nome_t = _bd_tok(e.get("nome"))
            altro_t = _bd_tok(" ".join([e.get("significato", ""), e.get("aspetto", ""), " ".join(e.get("cause") or []), e.get("tipo_mezzo", "")]))
            punti = 3.0 * len(qt & nome_t) + 1.0 * len(qt & altro_t)
            if punti <= 0:
                continue
        stato, su, giu = bd_stato(e)
        if scope.get("marca") and e.get("marca") == scope["marca"]:
            punti += 3
            if scope.get("modello") and e.get("modello") == scope["modello"]:
                punti += 3
        elif e.get("marca") and scope.get("marca") and e.get("marca") != scope["marca"]:
            punti -= 2                                                # una voce di un'altra marca conta meno
        if scope.get("tipo") and e.get("tipo_mezzo") == scope["tipo"]:
            punti += 1
        punti += {"verificata": 3, "contestata": -3}.get(stato, 0) + 0.3 * su - 0.5 * giu + min(2.0, 0.1 * int(e.get("usi", 1)))
        ris.append((punti, e))
    ris.sort(key=lambda x: -x[0])
    return [e for _p, e in ris[:limite]]


def bd_abbina(nome, scope=None, colore=None, voci=None):
    """La voce della base più simile a un nome di spia (per mostrare «già trovata da altri»), oppure None."""
    voci = voci if voci is not None else bd_leggi()
    a = _bd_tok(nome)
    migliore, punti = None, 0.0
    for e in voci:
        if colore and e.get("colore") != colore:
            continue
        b = _bd_tok(e.get("nome"))
        com = a & b
        if not com:
            continue
        sc = len(com) / max(1, min(len(a), len(b))) + (0.3 if (scope or {}).get("marca") and e.get("marca") == scope.get("marca") else 0) + {"verificata": 0.3, "contestata": -0.5}.get(bd_stato(e)[0], 0)
        if sc > punti:
            migliore, punti = e, sc
    return migliore if punti >= 0.6 else None


# ---------------------------------------------------------------------------------------------------------------------
# la schermata
# ---------------------------------------------------------------------------------------------------------------------
def _bd_badge(e):
    stato, su, giu = bd_stato(e)
    return {"verificata": f"✅ Verificata ({su} 👍)", "contestata": f"⚠️ Contestata ({giu} 👎)", "da_verificare": "🟡 Da verificare"}[stato] + (f" · 👍{su} 👎{giu}" if stato == "da_verificare" and (su or giu) else "")


def _bd_scheda(e, scope, chiave):
    """Una voce, con i tasti per confermarla o segnalarla (e, per l'amministratore, gli strumenti)."""
    stato, su, giu = bd_stato(e)
    specifico = (" ".join(x for x in (e.get("marca", "").title(), e.get("modello", "").title(), e.get("anno", "")) if x) or "") + (f" ({e['tipo_mezzo']})" if e.get("tipo_mezzo") else "")
    with st.expander(f"{_BD_ICONA.get(e.get('colore'), '🟡')} {e['nome']} · {_bd_badge(e)}"):
        if e.get("colore") == "rosso" or e.get("urgenza") == "critica":
            st.markdown(f"<div style='background:#b71c1c;color:#fff;border-radius:12px;padding:9px 12px;font-weight:900'>🔴 PERICOLO — accosta subito in sicurezza e spegni il veicolo.</div>", unsafe_allow_html=True)
        if stato != "verificata":
            st.caption("Questa voce non è ancora verificata e può contenere errori: per il tuo mezzo vale il manuale.")
        st.markdown(f"**Valida per:** {specifico if e.get('marca') or e.get('modello') else (e.get('tipo_mezzo') or 'qualsiasi mezzo')}" + (f"  \n**Aspetto del simbolo:** {e['aspetto']}" if e.get("aspetto") else "")
                    + (f"  \n**Colore:** {e['colore'].capitalize()} · **Urgenza:** {e.get('urgenza', '')}") + (f"  \n**Codice simbolo:** {e['simbolo_iso']} (da verificare)" if e.get("simbolo_iso") else ""))
        if e.get("significato"):
            st.markdown("**Significato:** " + e["significato"])
        if e.get("azioni"):
            st.markdown("**Cosa fare**\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(e["azioni"], 1)))
        if e.get("cause"):
            st.caption("Possibili cause: " + ", ".join(e["cause"]) + ".")
        st.caption(f"Trovata {int(e.get('usi', 1))} {'volta' if int(e.get('usi', 1)) == 1 else 'volte'} · fonti: {', '.join(e.get('fonti') or ['—'])}")
        mio = (e.get("voti") or {}).get(_bd_uid(), 0)
        c1, c2 = st.columns(2, gap="small")
        if c1.button(("✅ " if mio > 0 else "") + "👍 È giusta", key=f"bd_su_{chiave}_{e['id']}", width="stretch"):
            bd_vota(e["id"], 1)
            st.rerun()
        if c2.button(("✅ " if mio < 0 else "") + "👎 È sbagliata", key=f"bd_giu_{chiave}_{e['id']}", width="stretch"):
            bd_vota(e["id"], -1)
            st.rerun()
        if _bd_admin():
            a1, a2, a3 = st.columns(3, gap="small")
            if a1.button("✅ Conferma", key=f"bd_ok_{chiave}_{e['id']}", width="stretch"):
                bd_admin(e["id"], "conferma")
                st.rerun()
            if a2.button("⚠️ Contesta", key=f"bd_no_{chiave}_{e['id']}", width="stretch"):
                bd_admin(e["id"], "contesta")
                st.rerun()
            if a3.button("🗑️ Elimina", key=f"bd_del_{chiave}_{e['id']}", width="stretch"):
                bd_admin(e["id"], "elimina")
                st.rerun()


def bd_mostra_abbinamento(nome, colore=None, chiave="x"):
    """Sotto il risultato dell'IA: se la spia è già nella base condivisa, lo dice (e mostra cosa ne pensano gli altri)."""
    if not bd_attiva():
        return
    sc = st.session_state.get("ad_scope") or {}
    e = bd_abbina(nome, sc, colore)
    if e:
        stato, su, giu = bd_stato(e)
        st.caption(f"📚 Nella base condivisa: {_bd_badge(e)} · trovata {int(e.get('usi', 1))} volte da chi usa l'app.")
        _bd_scheda(e, sc, "abb" + chiave)


def bd_checkbox_contribuisci():
    """La casella «Contribuisci…»: una sola volta per ridisegno (la usano sia la diagnosi sia la base)."""
    giro = st.session_state.get("_tabs_giro")
    if st.session_state.get("_bd_cb_giro") == giro and giro is not None:
        return
    st.session_state["_bd_cb_giro"] = giro
    st.checkbox("📚 Contribuisci alla base condivisa con le spie che trovo (solo testo, mai le foto)", value=True, key="bd_contrib")


def _bd_form_modello():
    giro = st.session_state.get("_tabs_giro")
    if st.session_state.get("_bd_mod_giro") == giro and giro is not None:
        return
    st.session_state["_bd_mod_giro"] = giro
    _bd_form_modello_vero()


def _bd_form_modello_vero():
    """Il modello del mezzo scritto a mano: facoltativo, per una ricerca più precisa."""
    with st.expander("✍️ Scrivi il modello del mezzo (facoltativo, per una ricerca più precisa)"):
        st.caption("Se vuoi, scrivi marca, modello e anno: la ricerca mette prima le spie e i guasti noti per quel modello. Se lasci vuoto, vale il mezzo scelto.")
        c1, c2, c3 = st.columns([3, 3, 2], gap="small")
        c1.text_input("Marca", key="mz_marca", placeholder="es. Iveco")
        c2.text_input("Modello", key="mz_modello", placeholder="es. Daily 35C14")
        c3.text_input("Anno", key="mz_anno", placeholder="es. 2018")


def _bd_form_aggiungi(scope, v):
    with st.expander("➕ Aggiungi una spia o un guasto alla base (verificato da te)"):
        st.caption("Hai trovato la risposta online o nel manuale? Scrivila qui: entra nella base e aiuta gli altri. Resta «da verificare» finché non la confermano.")
        with st.form("bd_nuova", border=False, clear_on_submit=True):
            nome = st.text_input("Nome della spia o del guasto", key="bd_n_nome", placeholder="es. Spia pressione aria freni")
            c1, c2 = st.columns(2, gap="small")
            colore = c1.selectbox("Colore", list(_BD_COLORI), key="bd_n_col", format_func=lambda x: f"{_BD_ICONA[x]} {x}")
            urg = c2.selectbox("Urgenza", ["critica", "alta", "media", "informazione"], index=2, key="bd_n_urg")
            aspetto = st.text_input("Com'è fatto il simbolo (facoltativo)", key="bd_n_asp", placeholder="es. cerchio rosso con una P")
            sign = st.text_area("Cosa significa", key="bd_n_sig", height=70)
            azioni = st.text_area("Cosa fare (un passo per riga)", key="bd_n_azi", height=90)
            cause = st.text_area("Possibili cause (una per riga)", key="bd_n_cau", height=70)
            fonte = st.text_input("Dove l'hai verificato (sito, manuale, officina)", key="bd_n_fon", placeholder="es. manuale pag. 142, sito del costruttore")
            solo_mod = st.checkbox("Vale solo per questo modello" + (f" ({bd_scope_desc(scope, v)})" if (scope.get("marca") or scope.get("modello")) else " (scrivi prima il modello qui sopra)"), value=False, key="bd_n_mod")
            ok = st.form_submit_button("💾 Aggiungi alla base", type="primary", width="stretch")
        if ok:
            if len(nome.strip()) < 3:
                st.error("Scrivi il nome della spia o del guasto.")
            elif not sign.strip() and not azioni.strip():
                st.error("Scrivi almeno cosa significa o cosa fare.")
            else:
                sp = {"nome": nome.strip(), "colore": colore, "urgenza": urg, "aspetto": aspetto.strip(), "significato": sign.strip(),
                      "azioni": [x.strip() for x in azioni.splitlines() if x.strip()], "cause": [x.strip() for x in cause.splitlines() if x.strip()]}
                sc = dict(scope) if solo_mod else {"tipo": scope.get("tipo", ""), "marca": "", "modello": "", "anno": ""}
                _id, nuova = bd_registra(sp, sc, "Aggiunta da un utente", fonte.strip())
                if _id:
                    st.session_state["messaggio"] = "✅ Aggiunta alla base condivisa." if nuova else "✅ C'era già: ho contato un uso in più e aggiunto la fonte."
                    st.rerun()
                else:
                    st.error("Non sono riuscito a salvare nella base. Riprova fra poco.")


def _bd_admin_strumenti(voci):
    if not _bd_admin():
        return
    with st.expander("🛠️ Strumenti dell'amministratore (esporta, importa)"):
        st.caption("Esporta la base per portarla in un'altra installazione dell'app, o importa quella di un'altra (copia e incolla). Le voci con lo stesso identificativo non si duplicano.")
        st.download_button("⬇️ Esporta la base (file)", data=json.dumps({"versione": 1, "spie": voci}, ensure_ascii=False, indent=1).encode("utf-8"), file_name="base_spie.json", mime="application/json", width="stretch", key="bd_esporta")
        testo = st.text_area("Oppure incolla qui il testo di una base da importare", key="bd_import", height=90)
        if st.button("⬆️ Importa", key="bd_importa_b", width="stretch") and testo.strip():
            try:
                nuove = [e for e in (json.loads(testo).get("spie") or []) if isinstance(e, dict) and e.get("nome") and e.get("id")]
            except Exception:
                nuove = None
            if nuove is None:
                st.error("Il testo non è una base di spie valida.")
            else:
                n = {"x": 0}

                def _fn(lista):
                    ids = {e.get("id") for e in lista}
                    for e in nuove:
                        if e["id"] not in ids and e.get("colore") in _BD_COLORI:
                            e = dict(e)
                            e["voti"] = {}
                            e["confermata_admin"] = False
                            lista.append(e)
                            n["x"] += 1
                _bd_salva(_fn, "Base spie: importazione")
                st.session_state["messaggio"] = f"✅ Importate {n['x']} voci (da verificare)."
                st.rerun()


def bd_pannello(v=None):
    """La base condivisa: ricerca (anche a parole e con il modello scritto a mano), voti, aggiunta a mano e, se serve, la domanda all'IA."""
    if not bd_attiva():
        return
    voci = bd_leggi()
    n_ver = sum(1 for e in voci if bd_stato(e)[0] == "verificata")
    st.markdown("#### 📚 Base condivisa delle spie e dei guasti")
    st.caption(f"**{len(voci)}** voci ({n_ver} verificate), a disposizione di **tutte le persone che usano l'app**. Cresce con l'uso: ogni spia riconosciuta dall'IA o aggiunta da qualcuno entra qui (**solo testo, mai foto**), così la prossima volta la ricerca è interna, gratis e subito.")
    bd_checkbox_contribuisci()
    _bd_form_modello()
    scope = bd_scope(v)
    st.session_state["ad_scope"] = scope
    q = st.text_input("🔍 Cerca una spia o un guasto (a parole)", key="bd_q", placeholder="es. spia olio accesa a freddo, fumo bianco, cambio che slitta")
    c1, c2 = st.columns([3, 2], gap="small")
    col_s = c2.selectbox("Colore", ["Tutti", "🔴 Rosse", "🟡 Gialle", "🟢 Verdi", "🔵 Blu"], key="bd_col", label_visibility="collapsed")
    colore = {"🔴 Rosse": "rosso", "🟡 Gialle": "giallo", "🟢 Verdi": "verde", "🔵 Blu": "blu"}.get(col_s, "")
    c1.caption(f"Cerco per: {bd_scope_desc(scope, v)}")
    ris = bd_cerca(q, colore, scope, voci=voci)
    if not voci:
        st.info("La base è ancora vuota: si riempie da sola con le spie che l'IA riconosce, e con quelle che aggiungete voi.")
    elif not ris:
        st.info("Nessuna voce corrisponde nella base." if (q or colore) else "Scrivi qualcosa per cercare, oppure sfoglia le voci scegliendo un colore.")
    for e in (ris if (q or colore) else ris[:8]):
        _bd_scheda(e, scope, "r")
    if not (q or colore) and len(ris) > 8:
        st.caption(f"Ne mostro 8 su {len(ris)}: scrivi una parola per cercare.")
    # ---- se non c'è: l'IA (a parole) o la tua app di IA
    if q.strip() and not ris:
        desc = bd_scope_desc(scope, v)
        if ad_attivo():
            if st.button("🤖 Chiedi all'intelligenza artificiale (a parole)", key="bd_chiedi_ia", type="primary", width="stretch"):
                with st.spinner("Cerco la risposta…"):
                    st.session_state["bd_ia_ris"] = {"q": q.strip(), "ris": ad_analizza_testo(q.strip(), desc)}
        else:
            st.info("🤖 L'IA dell'app non è attiva: puoi chiedere alla **tua app di IA** (gratis) con le istruzioni qui sotto, poi **aggiungere la risposta alla base** (modulo in fondo). Oppure scegli un'IA e incolla la tua chiave nella scheda «📷 Diagnosi visiva».")
            st.code(ad_prompt_libero(desc, q.strip()), language=None)
            cols = st.columns(3, gap="small")
            for i, (nome_ia, url) in enumerate(_AD_APP_IA):
                cols[i % 3].link_button(nome_ia, url, width="stretch")
    risp = st.session_state.get("bd_ia_ris")
    if risp and q.strip() and risp.get("q") == q.strip():
        r = risp["ris"]
        if r.get("errore"):
            st.warning({"chiave": "La chiave dell'IA non è valida o manca.", "limite": "Limite di analisi raggiunto: riprova più tardi.", "rete": "Non riesco a collegarmi al servizio adesso.",
                        "rifiuto": "Il servizio non ha potuto rispondere.", "formato": "La risposta non era leggibile.", "pagamento": "Questo modello è a pagamento e non ci sono crediti: scegline uno «:free».", "modello": "Questo modello non esiste più: cambia il nome del modello."}.get(r["errore"], "Qualcosa non ha funzionato."))
        elif not r.get("riconosciuta"):
            st.warning("L'IA non ha trovato una risposta sicura." + (" " + r["note"] if r.get("note") else " Prova a descrivere meglio la spia o il guasto."))
        else:
            _ad_risultato(r, v, bd_scope_desc(scope, v), "testo", None)
            if st.session_state.get("bd_contrib", True) and not st.session_state.get(f"bd_reg_{q.strip()}"):
                st.session_state[f"bd_reg_{q.strip()}"] = True
                nuove, agg = bd_registra_risultato(r, scope, "IA (a parole)")
                st.success(f"📚 Aggiunta alla base condivisa ({nuove} nuove, {agg} già presenti).")
    _bd_form_aggiungi(scope, v)
    _bd_admin_strumenti(voci)


# ---- la base entra nella ricerca delle spie già esistente (il catalogo verificato resta com'è)
if "ae_spie" in globals() and "_bd_ae_spie_prima" not in globals():
    _bd_ae_spie_prima = ae_spie

    def ae_spie(v=None):                                           # noqa: F811
        _bd_ae_spie_prima(v)
        try:
            bd_pannello(v)
        except Exception as ex:
            st.caption(f"La base condivisa non è disponibile adesso ({type(ex).__name__}).")
