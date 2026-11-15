# -*- coding: utf-8 -*-
"""Casa con i PROFILI FAMILIARI: sopra le case c'è «👤 Di chi è la casa» (tu, tua madre, un familiare…). Ogni persona ha le sue case (principale + altre) e ognuna
è completa come la tua: Amministrazione, Beni, Documenti, Manutenzioni, Riferimenti. I profili sono gli stessi di Salute (👥 Gestisci profili): se aggiungi «Mamma»
qui, la ritrovi in Salute e viceversa. Ogni account ha i suoi (i dati sono per utente). Sostituisce ca_selettore_casa di casa.py; nomi con prefisso «cpf_»."""
import html as _cpf_html
import uuid as _cpf_uuid

import streamlit as st


def cpf_profili():
    """[(id, nome)] dei profili familiari dell'account (il primo è il tuo)."""
    try:
        f = _fa_dati()
    except Exception:
        f = {}
    try:
        return [(p["id"], p.get("nome") or "") for p in _fa_profili(f)]
    except Exception:
        return [("p0", (st.session_state.get("sess") or {}).get("nome", "Io"))]


def cpf_di_chi(casa, pids):
    """L'id del profilo a cui appartiene una casa (senza indicazione: il tuo)."""
    return casa.get("profilo") if casa.get("profilo") in pids else pids[0]


def cpf_case_persona(c, pid, pids):
    """Le case di UNA persona: per te anche la «Casa principale» (id vuoto)."""
    altre = [x for x in (c.get("case") or []) if isinstance(x, dict) and x.get("id") and cpf_di_chi(x, pids) == pid]
    return ([{"id": "", "nome": "Casa principale", "indirizzo": ""}] if pid == pids[0] else []) + altre


def _cpf_dialogo_togli(cid, nome):
    def _finestra():
        st.warning(f"Togliere la casa **{_cpf_html.escape(nome)}**? Quello che hai registrato per lei (beni, documenti, interventi, riferimenti) **non si cancella**: passa alla casa principale.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglila", key=f"ca_casa_si_{cid}", type="primary", width="stretch"):
            def _fn(cc):
                cc["case"] = [x for x in cc.get("case", []) if x.get("id") != cid]
                for k in _CA_LISTE_CASA:
                    for x in cc.get(k, []):
                        if isinstance(x, dict) and x.get("casa_id") == cid:
                            x["casa_id"] = ""
            _ca_salva(_fn, "Casa: casa tolta")
            st.session_state["ca_casa_sel"] = ""
            st.rerun()
        if s2.button("No, tienila", key=f"ca_casa_no_{cid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina la casa")(_finestra)()


def _cpf_pillole(titolo, etichette, corrente, chiave):
    if hasattr(st, "pills"):
        return st.pills(titolo, etichette, default=corrente, key=chiave, label_visibility="collapsed")
    return st.radio(titolo, etichette, index=etichette.index(corrente), horizontal=True, key=chiave, label_visibility="collapsed")


def ca_selettore_casa(c):
    """Persona → casa. Ritorna l'id della casa scelta ('' = la principale di chi sei tu; «__vuota__» = la persona scelta non ha ancora una casa)."""
    profili = cpf_profili()
    pids = [p for p, _n in profili]
    nomi = dict(profili)
    # 1) di chi è la casa
    pers = st.session_state.get("ca_pers_sel")
    if pers not in pids:                                                       # all'inizio: la persona della casa che stavi guardando
        att = st.session_state.get("ca_casa_sel") or ""
        casa_att = next((x for x in (c.get("case") or []) if isinstance(x, dict) and x.get("id") == att), None)
        pers = cpf_di_chi(casa_att, pids) if casa_att else pids[0]
    if len(pids) > 1:
        etich_p = [f"👤 {nomi[p]}" for p in pids]
        scelta_p = _cpf_pillole("Di chi è la casa", etich_p, etich_p[pids.index(pers)], "ca_pers_pillole")
        if scelta_p in etich_p:
            pers = pids[etich_p.index(scelta_p)]
    st.session_state["ca_pers_sel"] = pers
    # 2) quale casa di quella persona
    case = cpf_case_persona(c, pers, pids)
    ids = [x["id"] for x in case]
    sel = st.session_state.get("ca_casa_sel") or ""
    if sel not in ids:
        sel = ids[0] if ids else "__vuota__"
    if len(case) > 1:
        etich = [f"🏡 {x['nome']}" for x in case]
        scelta = _cpf_pillole("Quale casa", etich, etich[ids.index(sel)], f"ca_casa_pillole_{pers}")
        if scelta in etich:
            sel = ids[etich.index(scelta)]
    st.session_state["ca_casa_sel"] = "" if sel == "__vuota__" else sel
    # 3) aggiungere una casa (per la persona scelta) e un profilo familiare
    di_chi_testo = "" if pers == pids[0] else f" di {nomi[pers]}"
    with st.expander(f"➕ Aggiungi una casa{di_chi_testo} (seconda casa, casa dei genitori…)", _aperta=(sel == "__vuota__")):
        st.caption("Per seguire **più case**: ognuna ha i suoi beni, documenti, bollette, manutenzioni e riferimenti. In alto scegli quale guardare; gli **avvisi di scadenza** valgono per tutte.")
        with st.form(f"ca_casa_nuova_{pers}", border=False, clear_on_submit=True):
            nome = st.text_input("Nome della casa", placeholder="es. Casa al mare, Casa della nonna" if pers == pids[0] else f"es. Casa di {nomi[pers]}")
            ind = st.text_input("Indirizzo (facoltativo)")
            ok = st.form_submit_button("💾 Aggiungi la casa", type="primary", width="stretch")
        if ok:
            if not nome.strip():
                st.error("Scrivi un nome per la casa.")
            else:
                nv = {"id": _cpf_uuid.uuid4().hex[:8], "nome": nome.strip(), "indirizzo": ind.strip(), "profilo": pers}
                _ca_salva(lambda cc, nv=nv: cc.__setitem__("case", list(cc.get("case", [])) + [nv]), "Casa: nuova casa")
                st.session_state["ca_casa_sel"] = nv["id"]
                st.session_state["ca_pers_sel"] = pers
                st.session_state.pop(f"ca_casa_pillole_{pers}", None)
                st.session_state["messaggio"] = f"✅ Aggiunta «{nv['nome']}». Ora stai guardando quella casa."
                st.rerun()
        for x in [y for y in case if y["id"]]:
            r1, r2 = st.columns([3, 1], gap="small")
            r1.markdown(f"🏡 **{_cpf_html.escape(x['nome'])}**" + (f" · {_cpf_html.escape(x['indirizzo'])}" if x.get("indirizzo") else ""))
            if r2.button("🗑️", key=f"ca_casa_t_{x['id']}", width="stretch"):
                _cpf_dialogo_togli(x["id"], x["nome"])
    with st.expander(f"👥 Profili familiari ({len(profili)}/{MAX_PROFILI if 'MAX_PROFILI' in globals() else 12})"):
        st.caption("Aggiungi una persona (tua madre, un figlio, un fratello…): potrai seguire **le sue case** come le tue. Sono gli stessi profili di **Salute**.")
        with st.form("ca_profilo_nuovo", border=False, clear_on_submit=True):
            nuovo = st.text_input("Nome del profilo", placeholder="es. Mamma, Luca")
            ok_p = st.form_submit_button("➕ Aggiungi il profilo", disabled=len(profili) >= (MAX_PROFILI if "MAX_PROFILI" in globals() else 12), width="stretch")
        if ok_p and nuovo.strip():
            nid = _cpf_uuid.uuid4().hex[:8]
            try:
                _fa_salva(lambda f, nid=nid, n=nuovo.strip(): f["profili"].append({"id": nid, "nome": n}), "Casa: profilo familiare")
                st.session_state["ca_pers_sel"] = nid
                st.session_state.pop("ca_pers_pillole", None)
                st.session_state["messaggio"] = f"✅ Profilo «{nuovo.strip()}» aggiunto. Ora aggiungi la sua casa."
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
    return sel


def cpf_titolo(c, sel_c):
    """L'intestazione sopra le schede: la casa guardata (e di chi è, se hai più persone)."""
    profili = cpf_profili()
    pids = [p for p, _n in profili]
    pers = st.session_state.get("ca_pers_sel") or pids[0]
    case = cpf_case_persona(c, pers, pids)
    nome = next((x["nome"] for x in case if x["id"] == sel_c), "Casa principale")
    di = f" · 👤 {_cpf_html.escape(dict(profili).get(pers, ''))}" if len(pids) > 1 else ""
    st.markdown(f"##### 🏡 {_cpf_html.escape(nome)}{di}")
