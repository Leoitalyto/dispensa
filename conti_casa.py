# -*- coding: utf-8 -*-
"""💶 Tenuta dei conti (in Casa): quanti soldi ci sono, dove. Conti correnti (per banca), Postepay, libretti postali, BOT/BTP e altri investimenti,
sempre più di uno, con il totale in fondo e un campo note. Dati in d["conti"] = {"voci": [...], "note": ""}."""
import streamlit as st

TCN_TIPI = [("💳", "Conto corrente"), ("🟡", "Postepay"), ("📘", "Libretto postale"), ("🏛️", "BOT"), ("🏛️", "BTP"), ("🏛️", "CCT / CTZ"),
            ("📈", "Fondo / ETF"), ("📊", "Azioni"), ("✉️", "Buoni postali"), ("💵", "Contanti"), ("🔒", "Altro investimento")]


def _tcn_icona(tipo):
    return next((i for i, t in TCN_TIPI if t == tipo), "💰")


def _tcn_ref(d, ctx="casa", crea=False):
    """Dove stanno i conti: per te d["conti"] (come prima); per un'altra persona d["conti_profili"]["casa@id"]."""
    if ctx in (None, "", "casa"):
        return d.setdefault("conti", {}) if crea else (d.get("conti") or {})
    base = d.setdefault("conti_profili", {}) if crea else (d.get("conti_profili") or {})
    return base.setdefault(ctx, {}) if crea else (base.get(ctx) or {})


def _tcn_voci(d, ctx="casa"):
    return [v for v in (_tcn_ref(d, ctx).get("voci") or []) if isinstance(v, dict)]


def tcn_totale(d, ctx="casa"):
    return sum(float(v.get("importo") or 0) for v in _tcn_voci(d, ctx))


def _tcn_salva(rec, ctx="casa"):
    def _m(d):
        c = _tcn_ref(d, ctx, True)
        lst = c.setdefault("voci", [])
        for i, x in enumerate(lst):
            if x.get("id") == rec["id"]:
                lst[i] = rec
                break
        else:
            lst.append(rec)
    sc_salva(_m, "Conti: " + str(rec.get("tipo", "")))


def _tcn_modulo(v, ctx="casa"):
    k = "tcn_f_" + ctx.replace("@", "_") + "_" + (v.get("id") or "nuovo")
    with st.container(border=True, key=k + "_box"):
        st.markdown("**" + ("✏️ Modifica" if v.get("id") else "➕ Aggiungi una voce") + "**")
        nomi = [t for _i, t in TCN_TIPI]
        tipo = st.selectbox("Cos'è", nomi, index=nomi.index(v["tipo"]) if v.get("tipo") in nomi else 0, key=k + "_t")
        etic = "Banca / ente" if tipo in ("Conto corrente", "Fondo / ETF", "Azioni") else "Dove (es. Poste Italiane)"
        banca = st.text_input(etic, value=v.get("banca", ""), key=k + "_b", placeholder="es. Intesa Sanpaolo, Poste, Fineco")
        nome = st.text_input("Nome o dettaglio (facoltativo)", value=v.get("nome", ""), key=k + "_n", placeholder="es. conto di casa, BTP 2029, libretto di Anna")
        importo = st.number_input("Quanto c'è (€)", value=float(v.get("importo") or 0.0), step=50.0, format="%.2f", key=k + "_i")
        scad = None
        if tipo in ("BOT", "BTP", "CCT / CTZ", "Buoni postali"):
            ha = st.checkbox("Ha una scadenza", value=bool(v.get("scadenza")), key=k + "_hs")
            if ha:
                scad = st.date_input("Scade il", value=sc_data(v.get("scadenza")) or sc_oggi(), format="DD/MM/YYYY", key=k + "_s")
        nota = st.text_input("Nota (facoltativa)", value=v.get("nota", ""), key=k + "_no")
        b1, b2 = st.columns(2, gap="small")
        if b1.button("✅ Salva", type="primary", key=k + "_ok", width="stretch"):
            rec = {**v, "id": v.get("id") or sc_id(), "tipo": tipo, "banca": banca.strip(), "nome": nome.strip(), "importo": float(importo or 0),
                   "scadenza": scad.isoformat() if scad else "", "nota": nota.strip(), "aggiornato": sc_oggi().isoformat()}
            _tcn_salva(rec, ctx)
            st.session_state["tcn_mod"] = None
            st.toast("✅ Salvato")
            sc_rerun()
        if b2.button("Annulla", key=k + "_no_", width="stretch"):
            st.session_state["tcn_mod"] = None
            sc_rerun()


def _tcn_corpo():
    ctx = sc_scegli_profilo("casa") if "sc_scegli_profilo" in globals() else "casa"     # di chi sono i conti: tuoi o di un'altra persona
    d = sc_dati()
    voci = _tcn_voci(d, ctx)
    tot = tcn_totale(d, ctx)
    st.markdown(
        "<div style='padding:12px;border-radius:16px;border:2px solid #20e6ff;background:#0a1626;text-align:center;box-shadow:0 0 14px rgba(32,230,255,.45)'>"
        f"<div style='color:#8ff3ff;font-size:.85rem'>TOTALE A DISPOSIZIONE</div><div style='color:#fff;font-size:1.7rem;font-weight:800'>{sc_esc(sc_euro(tot))}</div></div>",
        unsafe_allow_html=True)
    if st.button("➕ Aggiungi conto, libretto o investimento", key="tcn_nuovo", type="primary", width="stretch"):
        st.session_state["tcn_mod"] = "__nuovo__"
        sc_rerun()
    if st.session_state.get("tcn_mod") == "__nuovo__":
        _tcn_modulo({}, ctx)
    if not voci:
        st.info("Non c'è ancora niente. Aggiungi per esempio un conto corrente e la banca.")
    ordine = [t for _i, t in TCN_TIPI]
    gruppi = {}
    for v in voci:
        gruppi.setdefault(v.get("tipo") or "Altro investimento", []).append(v)
    for tipo in sorted(gruppi, key=lambda t: ordine.index(t) if t in ordine else 99):
        sub = sum(float(x.get("importo") or 0) for x in gruppi[tipo])
        st.markdown(f"#### {_tcn_icona(tipo)} {sc_esc(tipo)} · {sc_esc(sc_euro(sub))}", unsafe_allow_html=True)
        for v in gruppi[tipo]:
            vid = v["id"]
            titolo = " · ".join(x for x in (v.get("banca"), v.get("nome")) if x) or tipo
            extra = []
            if sc_data(v.get("scadenza")):
                extra.append("scade " + sc_data_scritta(sc_data(v["scadenza"]), False))
            if v.get("nota"):
                extra.append(v["nota"])
            if sc_data(v.get("aggiornato")):
                extra.append("aggiornato " + sc_data_scritta(sc_data(v["aggiornato"]), False))
            st.markdown(f"<div class='rbu-card'><b class='rbu-nome'>{sc_esc(titolo)}</b> — <b>{sc_esc(sc_euro(v.get('importo')))}</b>"
                        + (f"<div class='rbu-righe'>{sc_esc(' · '.join(extra))}</div>" if extra else "") + "</div>", unsafe_allow_html=True)
            if st.session_state.get("tcn_mod") == vid:
                _tcn_modulo(v, ctx)
                continue
            c1, c2 = st.columns(2, gap="small")
            if c1.button("✏️ Modifica", key=f"tcn_ed_{vid}", width="stretch"):
                st.session_state["tcn_mod"] = vid
                sc_rerun()
            if st.session_state.get("tcn_conferma") == vid:
                s1, s2 = st.columns(2, gap="small")
                if s1.button("🗑️ Sì, elimina", key=f"tcn_si_{vid}", type="primary", width="stretch"):
                    sc_salva(lambda dd, vid=vid: _tcn_ref(dd, ctx, True).__setitem__("voci", [x for x in _tcn_ref(dd, ctx, True).get("voci", []) if x.get("id") != vid]), "Conti: voce eliminata")
                    st.session_state["tcn_conferma"] = None
                    sc_rerun()
                if s2.button("No", key=f"tcn_no2_{vid}", width="stretch"):
                    st.session_state["tcn_conferma"] = None
                    sc_rerun()
            elif c2.button("🗑️ Elimina", key=f"tcn_el_{vid}", width="stretch"):
                st.session_state["tcn_conferma"] = vid
                sc_rerun()
    if voci:
        st.markdown(f"### 🧮 Totale: {sc_esc(sc_euro(tot))}", unsafe_allow_html=True)
    note = st.text_area("📝 Note sui conti", value=_tcn_ref(d, ctx).get("note", ""), key="tcn_note_" + ctx, height=100)
    if note != _tcn_ref(d, ctx).get("note", "") and st.button("💾 Salva le note", key="tcn_note_ok_" + ctx, width="stretch"):
        sc_salva(lambda dd: _tcn_ref(dd, ctx, True).__setitem__("note", note), "Conti: note")
        st.toast("✅ Note salvate")
        sc_rerun()


def tcn_apri():
    st.session_state["tcn_mod"] = None
    st.session_state.pop("sc_pf_casa", None)                           # parte dalla persona scelta in Casa
    sc_dialogo("💶 Tenuta dei conti", lambda: (st.markdown(RBU_CSS, unsafe_allow_html=True) if "RBU_CSS" in globals() else None, _tcn_corpo()))


def cb_barra_casa(c=None):
    """In Casa, sopra le schede: 💶 Tenuta dei conti e (solo amministratore) 👵 Badante con il suo campanellino."""
    st.markdown(SC_CSS, unsafe_allow_html=True) if "SC_CSS" in globals() else None
    admin = bool((st.session_state.get("sess") or {}).get("admin"))
    with st.container(key="sc_barra_casa"):
        cols = st.columns(2 if admin else 1, gap="small")
        _chi = ""
        try:
            if "sc_contesto" in globals() and sc_contesto("casa") != "casa":
                _chi = sc_nome_profilo("casa")
        except Exception:
            _chi = ""
        if cols[0].button("💶 Conti di " + _chi if _chi else "💶 Tenuta dei conti", key="cb_conti", width="stretch"):
            tcn_apri()
        if admin and "bdt_apri" in globals():
            if cols[1].button("👵 Badante", key="cb_badante", width="stretch"):
                bdt_apri()
    if admin and "avs_apri" in globals() and "bdt_calcolo" in globals():
        try:
            d = sc_dati()
            b = d.get("badante") or {}
            if b.get("inizio"):
                r = bdt_calcolo(b, sc_oggi())
                if r["saldo"] < 0:
                    st.error("👵 Badante: i soldi sono finiti. Devi consegnarne altri.")
                elif r["giorni_rimasti"] is not None and r["giorni_rimasti"] <= 3:
                    st.warning("👵 Badante: i soldi bastano " + ("solo fino a OGGI." if r["giorni_rimasti"] == 0 else f"ancora {r['giorni_rimasti']} {'giorno' if r['giorni_rimasti'] == 1 else 'giorni'} (fino a {sc_data_scritta(r['fine'])})."))
            if st.button("🔔 Avvisi della badante", key="cb_badante_bell", width="stretch"):
                avs_apri("badante", "Badante")
        except Exception:
            pass
