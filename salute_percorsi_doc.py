# -*- coding: utf-8 -*-
"""🗂️ DOCUMENTI SANITARI → PERCORSO DI CURA (richiesta del 27/11/2026).

I documenti già archiviati in Salute → Documenti sanitari possono ENTRARE in un percorso di cura che c'è già, oppure DIVENTARE un percorso nuovo,
uno alla volta (tasto «🗂️ Percorso» sulla scheda del documento) o tanti insieme («🗂️ Metti più documenti in un percorso di cura»).
LA LORO CLASSIFICAZIONE RESTA INTATTA: il documento non si sposta e non si copia; nel percorso va solo un COLLEGAMENTO (stesso file, «da»: "docsan:<id>").
Tipo, area medica, prestazione, data, medico, struttura, conclusioni, N° e titolo restano quelli di prima. Se lo togli dal percorso, resta nei Documenti sanitari.
Sulla scheda del documento compare «🗂️ Nel percorso: …». Prefisso: pcd_."""
import streamlit as st

PCD_CATEGORIA = {"Diagnostica per immagini": "Radiografia / esame", "Esame di laboratorio": "Radiografia / esame", "Referto di visita": "Radiografia / esame",
                 "Piano terapeutico": "Piano di cura", "Ricovero e dimissione": "Altro", "Certificato medico": "Altro", "Ricetta medica": "Altro"}
PCD_TIPO_CURA = [(r"odont|dent|ortodon|implant|parodont|igiene orale", "🦷 Dentista"), (r"fisiot|riabilit|fisiatr", "🏃 Fisioterapia"),
                 (r"ocul|oftalm|vista", "👁️ Oculistica"), (r"ortoped|trauma", "🦴 Ortopedia"), (r"ricover|interven|chirurg|dimission", "🏥 Intervento / ricovero")]


# ---------------------------------------------------------------------------------------------------------------------
# logica (senza Streamlit)
# ---------------------------------------------------------------------------------------------------------------------
def pcd_chiave(doc):
    return f"docsan:{doc.get('id')}"


def pcd_refs(doc):
    return [r for r in [doc.get("file")] + list(doc.get("allegati") or []) if isinstance(r, dict) and r.get("id")]


def pcd_voce(doc, oggi_iso):
    """La voce del percorso per un documento sanitario: un COLLEGAMENTO (stesso file), con la sua classificazione ricordata a parte."""
    return {"id": pc_id(), "titolo": doc.get("titolo") or doc.get("esame") or doc.get("tipo") or "Documento sanitario",
            "categoria": PCD_CATEGORIA.get(doc.get("tipo") or "", "Altro"), "data": doc.get("data") or oggi_iso, "allegati": pcd_refs(doc),
            "da": pcd_chiave(doc), "collegato": True,
            "classificazione": {k: doc.get(k) for k in ("tipo", "specialita", "tipo_prestazione", "esame", "medico", "struttura") if doc.get(k)}}


def pcd_dove(f, pid):
    """{id documento sanitario: [(id percorso, titolo percorso)]} — in quali percorsi è già collegato ogni documento."""
    out = {}
    for p in f.get("percorsi") or []:
        if p.get("profilo", "p0") != pid:
            continue
        for x in p.get("documenti") or []:
            da = str(x.get("da") or "")
            if da.startswith("docsan:"):
                out.setdefault(da[7:], []).append((p.get("id"), p.get("titolo") or "Percorso di cura"))
    return out


def pcd_collega(f, pid, doc_ids, percorso_id, oggi_iso):
    """Collega i documenti al percorso (salta quelli già dentro). Non tocca i documenti sanitari. Ritorna quanti ne ha aggiunti."""
    prof = next((x for x in f.get("profili") or [] if x.get("id") == pid), {})
    docs = [d for d in prof.get("docsan") or [] if d.get("id") in set(doc_ids)]
    p = next((x for x in f.get("percorsi") or [] if x.get("id") == percorso_id), None)
    if p is None:
        return 0
    gia = {str(x.get("da") or "") for x in p.get("documenti") or []}
    nuovi = [pcd_voce(d, oggi_iso) for d in docs if pcd_chiave(d) not in gia and pcd_refs(d)]
    p.setdefault("documenti", []).extend(nuovi)
    if nuovi:
        p.setdefault("diario", []).append({"id": pc_id(), "data": oggi_iso, "testo": f"Collegati {len(nuovi)} documenti dai Documenti sanitari"})
    return len(nuovi)


def pcd_proposta_nuovo(docs):
    """Titolo, tipo di cura, studio e medico proposti per un percorso nuovo, presi dalla classificazione dei documenti (non cambiano i documenti)."""
    import re
    docs = list(docs or [])
    testo = " ".join(str(d.get(k) or "") for d in docs for k in ("specialita", "tipo", "esame", "prestazione", "titolo", "struttura")).lower()
    tipo = next((t for rx, t in PCD_TIPO_CURA if re.search(rx, testo)), "🩺 Specialistica" if any(d.get("specialita") for d in docs) else "📋 Altro")
    conta = lambda k: max(({str(d.get(k)).strip(): sum(1 for y in docs if str(y.get(k) or "").strip() == str(d.get(k)).strip()) for d in docs if d.get(k)} or {"": 0}).items(),
                          key=lambda kv: kv[1])[0]
    spec = conta("specialita")
    struttura, medico = conta("struttura"), conta("medico")
    titolo = (tipo.split(" ", 1)[1] if " " in tipo and tipo not in ("🩺 Specialistica", "📋 Altro") else (spec or "Percorso di cura"))
    if struttura:
        titolo += f" · {struttura}"
    return {"titolo": titolo[:80], "tipo": tipo, "struttura": struttura, "medico": medico}


def pcd_crea(f, pid, doc_ids, titolo, tipo, struttura, medico, oggi_):
    """Crea un percorso NUOVO con i documenti collegati. Ritorna il percorso."""
    p = pc_nuovo(titolo, pid, oggi_)
    p["tipo"] = tipo if tipo in PC_TIPI else p["tipo"]
    p["struttura"].update({"nome": (struttura or "").strip(), "medico": (medico or "").strip()})
    p["diario"].append({"id": pc_id(), "data": oggi_.isoformat(), "testo": "Cartella creata dai Documenti sanitari"})
    f.setdefault("percorsi", []).append(p)
    pcd_collega(f, pid, doc_ids, p["id"], oggi_.isoformat())
    return p


# ---------------------------------------------------------------------------------------------------------------------
# Streamlit
# ---------------------------------------------------------------------------------------------------------------------
def pcd_scelta(f, pid, doc_ids, chiave):
    """Il riquadro: «in quale percorso?» (uno che c'è già, oppure ➕ nuovo) e il tasto per collegare. doc_ids = documenti scelti."""
    import datetime as _dt
    oggi_ = _dt.date.today()
    prof = next((x for x in f.get("profili") or [] if x.get("id") == pid), {})
    docs = [d for d in prof.get("docsan") or [] if d.get("id") in set(doc_ids)]
    percorsi = [p for p in f.get("percorsi") or [] if p.get("profilo", "p0") == pid]
    percorsi.sort(key=lambda p: (p.get("stato") == "Concluso", p.get("titolo") or ""))
    opz = [p["id"] for p in percorsi] + ["__nuovo__"]
    nomi = {p["id"]: ("🗂️ " + (p.get("titolo") or "Percorso") + (" (concluso)" if p.get("stato") == "Concluso" else "")) for p in percorsi}
    nomi["__nuovo__"] = "➕ Crea un percorso NUOVO con " + ("questo documento" if len(doc_ids) == 1 else "questi documenti")
    scelta = st.radio("In quale percorso di cura?", opz, format_func=nomi.get, key=chiave + "_pc", index=0)
    st.caption("🔒 Il documento **resta dov'è, con la sua classificazione** (tipo, area medica, data, medico, N°): nel percorso va solo un collegamento allo stesso file.")
    if scelta == "__nuovo__":
        prop = pcd_proposta_nuovo(docs)
        titolo = st.text_input("Nome del percorso", value=prop["titolo"], key=chiave + "_tit")
        tipo = st.selectbox("Tipo di cura", PC_TIPI, index=PC_TIPI.index(prop["tipo"]) if prop["tipo"] in PC_TIPI else 0, key=chiave + "_tipo")
        c1, c2 = st.columns(2, gap="small")
        strutt = c1.text_input("Studio o struttura", value=prop["struttura"], key=chiave + "_str")
        medico = c2.text_input("Medico", value=prop["medico"], key=chiave + "_med")
        if st.button("💾 Crea il percorso e collega", key=chiave + "_crea", type="primary", width="stretch", disabled=not (titolo or "").strip() or not docs):
            esito = {}

            def _fn(f_):
                p = pcd_crea(f_, pid, doc_ids, titolo, tipo, strutt, medico, oggi_)
                esito.update(id=p["id"], n=len(p.get("documenti") or []))
            _fa_salva(_fn, "Salute: nuovo percorso di cura dai documenti sanitari")
            st.session_state["fa_msg"] = f"✅ Percorso «{titolo.strip()}» creato con {esito.get('n', 0)} documenti collegati. I documenti restano anche nei Documenti sanitari."
            st.session_state.pop(chiave + "_aperto", None)
            return True
        return False
    gia = {str(x.get("da") or "") for p in percorsi if p["id"] == scelta for x in p.get("documenti") or []}
    nuovi = [d for d in docs if pcd_chiave(d) not in gia]
    if docs and not nuovi:
        st.info("✅ " + ("È già" if len(docs) == 1 else "Sono già tutti") + " in questo percorso.")
        return False
    if st.button(f"🔗 Collega {'il documento' if len(nuovi) == 1 else str(len(nuovi)) + ' documenti'}", key=chiave + "_ok", type="primary", width="stretch", disabled=not nuovi):
        esito = {}
        _fa_salva(lambda f_: esito.__setitem__("n", pcd_collega(f_, pid, [d["id"] for d in nuovi], scelta, oggi_.isoformat())),
                  "Salute: documenti collegati a un percorso di cura")
        st.session_state["fa_msg"] = f"✅ {esito.get('n', 0)} documenti collegati a «{nomi[scelta][2:]}». Restano anche nei Documenti sanitari, con la loro classificazione."
        st.session_state.pop(chiave + "_aperto", None)
        return True
    return False


def pcd_badge(f, pid, doc_id):
    """La riga «🗂️ Nel percorso: …» sotto la scheda di un documento (vuota se non è in nessun percorso)."""
    dove = pcd_dove(f, pid).get(doc_id) or []
    if dove:
        st.caption("🗂️ Nel percorso di cura: " + ", ".join(f"**{t}**" for _i, t in dove))


def pcd_pannello_doc(f, pid, d):
    """Sotto la scheda di UN documento, se è stato toccato «🗂️ Percorso»."""
    chiave = f"pcd_{d['id']}"
    with st.container(border=True):
        st.markdown(f"**🗂️ Metti «{d.get('titolo') or 'documento'}» in un percorso di cura**")
        if pcd_scelta(f, pid, [d["id"]], chiave):
            st.session_state.pop("pcd_aperto", None)
            st.rerun()
        if st.button("✖ Chiudi", key=chiave + "_chiudi", width="stretch"):
            st.session_state.pop("pcd_aperto", None)
            st.rerun()


def pcd_pannello_molti(f, pid, docs, numeri=None):
    """Sopra l'elenco dei documenti: sceglierne tanti (per esempio gli 8 del dentista) e metterli insieme in un percorso."""
    if not docs:
        return
    numeri = numeri or {}
    dove = pcd_dove(f, pid)
    aperta = bool(st.session_state.get(f"pcd_molti_{pid}"))            # con dei documenti già scelti la linguetta resta aperta (si sceglie uno alla volta)
    try:
        lingu = st.expander("🗂️ Metti più documenti in un percorso di cura", _aperta=aperta)
    except TypeError:
        lingu = st.expander("🗂️ Metti più documenti in un percorso di cura", expanded=aperta)
    with lingu:
        st.caption("Scegli i documenti (anche tanti insieme) e il percorso: uno che c'è già oppure uno nuovo. "
                   "**Restano anche qui, con la loro classificazione**: nel percorso va solo il collegamento.")
        ordinati = sorted(docs, key=lambda x: x.get("data") or "", reverse=True)
        etich = {d["id"]: (f"N° {numeri[d['id']]} · " if numeri.get(d["id"]) else "") + (d.get("titolo") or d.get("tipo") or "Documento")
                 + (f" · {d['data'][8:10]}/{d['data'][5:7]}/{d['data'][:4]}" if len(str(d.get("data") or "")) >= 10 else "")
                 + (" · 🗂️" if dove.get(d["id"]) else "") for d in ordinati}
        scelti = st.multiselect("Documenti", [d["id"] for d in ordinati], format_func=etich.get, key=f"pcd_molti_{pid}", placeholder="Tocca e scegli i documenti…")
        if scelti:
            st.caption(f"Scelti: **{len(scelti)}**")
            if pcd_scelta(f, pid, scelti, f"pcd_m_{pid}"):
                st.session_state.pop(f"pcd_molti_{pid}", None)
                st.rerun()
