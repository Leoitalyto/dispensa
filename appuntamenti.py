# -*- coding: utf-8 -*-
"""📅 Appuntamenti (un bottone in ogni sezione tranne Dispensa).
Ogni appuntamento: nominativo, funzione, data, orario, telefono, motivazione, note. Dati in d["appuntamenti"][sezione]."""
import datetime as _ap_dt

import streamlit as st


def _apn_lista(d, sez):
    return [a for a in (d.get("appuntamenti") or {}).get(sez, []) if isinstance(a, dict)]


def _apn_quando(a):
    dd = sc_data(a.get("data"))
    if not dd:
        return None
    try:
        h, m = (a.get("ora") or "00:00").split(":")[:2]
        return _ap_dt.datetime.combine(dd, _ap_dt.time(int(h), int(m)))
    except Exception:
        return _ap_dt.datetime.combine(dd, _ap_dt.time(0, 0))


def apn_prossimi(sez):
    """Quanti appuntamenti ancora da fare (non conclusi e non passati)."""
    try:
        d = sc_dati()
        oggi_ = sc_oggi()
        return sum(1 for a in _apn_lista(d, sez) if not a.get("fatto") and sc_data(a.get("data")) and sc_data(a.get("data")) >= oggi_)
    except Exception:
        return 0


def _apn_salva(sez, rec):
    def _m(d):
        lst = d.setdefault("appuntamenti", {}).setdefault(sez, [])
        for i, x in enumerate(lst):
            if x.get("id") == rec["id"]:
                lst[i] = rec
                break
        else:
            lst.append(rec)
    sc_salva(_m, "Appuntamento: " + str(rec.get("nome", "")))


def _apn_modulo(sez, a):
    k = "apn_f_" + sez + "_" + (a.get("id") or "nuovo")
    with st.container(border=True, key=k + "_box"):
        st.markdown("**" + ("✏️ Modifica appuntamento" if a.get("id") else "➕ Nuovo appuntamento") + "**")
        st.markdown("<b>1 · Con chi</b>", unsafe_allow_html=True)
        nome = st.text_input("Nominativo *", value=a.get("nome", ""), key=k + "_n")
        funzione = st.text_input("Funzione (es. dentista, idraulico, notaio)", value=a.get("funzione", ""), key=k + "_f")
        tel = st.text_input("📞 Telefono", value=a.get("telefono", ""), key=k + "_t")
        st.markdown("<b>2 · Quando</b>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        data = c1.date_input("Data", value=sc_data(a.get("data")) or sc_oggi(), format="DD/MM/YYYY", key=k + "_d")
        try:
            h0, m0 = (a.get("ora") or "09:00").split(":")[:2]
            ora0 = _ap_dt.time(int(h0), int(m0))
        except Exception:
            ora0 = _ap_dt.time(9, 0)
        ora = c2.time_input("Orario", value=ora0, key=k + "_o", step=300)
        luogo = st.text_input("📍 Dove (facoltativo)", value=a.get("luogo", ""), key=k + "_l")
        st.markdown("<b>3 · Perché</b>", unsafe_allow_html=True)
        motivo = st.text_input("Motivazione", value=a.get("motivo", ""), key=k + "_m")
        note = st.text_area("📝 Note", value=a.get("note", ""), key=k + "_note", height=90)
        b1, b2 = st.columns(2, gap="small")
        if b1.button("✅ Salva", type="primary", key=k + "_ok", width="stretch"):
            if not nome.strip():
                st.error("Scrivi almeno il nominativo.")
                return
            rec = {**a, "id": a.get("id") or sc_id(), "nome": nome.strip(), "funzione": funzione.strip(), "telefono": tel.strip(), "data": data.isoformat(),
                   "ora": ora.strftime("%H:%M"), "luogo": luogo.strip(), "motivo": motivo.strip(), "note": note.strip(), "fatto": bool(a.get("fatto"))}
            _apn_salva(sez, rec)
            st.session_state["apn_mod"] = None
            st.toast("✅ Appuntamento salvato")
            sc_rerun()
        if b2.button("Annulla", key=k + "_no", width="stretch"):
            st.session_state["apn_mod"] = None
            sc_rerun()


def _apn_card(sez, a, passato):
    e = sc_esc
    aid = a["id"]
    dd = sc_data(a.get("data"))
    oggi_ = sc_oggi()
    if dd == oggi_:
        quando = "OGGI"
    elif dd == oggi_ + _ap_dt.timedelta(days=1):
        quando = "DOMANI"
    else:
        quando = sc_data_scritta(dd)
    righe = [f"🕒 <b>{e(quando)}</b> alle <b>{e(a.get('ora', ''))}</b>"]
    if a.get("funzione"):
        righe.append("💼 " + e(a["funzione"]))
    if a.get("motivo"):
        righe.append("🎯 " + e(a["motivo"]))
    if a.get("luogo"):
        righe.append("📍 " + e(a["luogo"]))
    if a.get("telefono"):
        righe.append("📞 " + e(a["telefono"]))
    if a.get("note"):
        righe.append("<i>" + e(a["note"]) + "</i>")
    colore = "rgba(160,160,170,.4)" if (passato or a.get("fatto")) else "rgba(255,183,77,.7)"
    st.markdown(f"<div class='rbu-card' style='border-color:{colore};{'opacity:.7' if passato or a.get('fatto') else ''}'><b class='rbu-nome'>"
                f"{'✔️ ' if a.get('fatto') else ''}{e(a.get('nome'))}</b><div class='rbu-righe'>" + "<br>".join(righe) + "</div></div>", unsafe_allow_html=True)
    tasti = sc_chiamate("a" + aid, a.get("telefono"), "", etichette=("📞 Chiama", ""))
    if a.get("luogo"):
        tasti.append(("📍 Mappa", sc_maps(a["luogo"])))
    sc_tasti(tasti, f"apn{sez}{aid}") if tasti else None
    if st.session_state.get("apn_mod") == aid:
        _apn_modulo(sez, a)
        return
    c1, c2, c3 = st.columns(3, gap="small")
    if c1.button("↩️ Da fare" if a.get("fatto") else "✅ Fatto", key=f"apn_fa_{aid}", width="stretch"):
        def _m(d):
            for x in d["appuntamenti"][sez]:
                if x["id"] == aid:
                    x["fatto"] = not x.get("fatto")
        sc_salva(_m, "Appuntamento: stato")
        sc_rerun()
    if c2.button("✏️ Modifica", key=f"apn_ed_{aid}", width="stretch"):
        st.session_state["apn_mod"] = aid
        sc_rerun()
    if c3.button("🗑️", key=f"apn_el_{aid}", width="stretch", help="Elimina"):
        st.session_state["apn_conferma"] = aid
        sc_rerun()
    if st.session_state.get("apn_conferma") == aid:
        st.warning("Eliminare questo appuntamento?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=f"apn_si_{aid}", type="primary", width="stretch"):
            sc_salva(lambda d: d["appuntamenti"].__setitem__(sez, [x for x in d["appuntamenti"].get(sez, []) if x.get("id") != aid]), "Appuntamento eliminato")
            st.session_state["apn_conferma"] = None
            sc_rerun()
        if s2.button("No", key=f"apn_no_{aid}", width="stretch"):
            st.session_state["apn_conferma"] = None
            sc_rerun()
    if dd:
        try:
            ora_ = _ap_dt.datetime.strptime(a.get("ora") or "09:00", "%H:%M").time()
        except Exception:
            ora_ = None
        st.download_button("📲 Metti nel calendario del telefono", sc_ics(f"{a.get('nome', '')} – {a.get('funzione', '')}".strip(" –"), dd, ora_,
                                                                        a.get("motivo", "") + ("\n" + a["note"] if a.get("note") else ""), a.get("luogo", "")).encode("utf-8"),
                           file_name="appuntamento.ics", mime="text/calendar", key=f"apn_ics_{aid}", width="stretch")


def _apn_corpo(sez0):
    sez = sc_scegli_profilo(sez0) if "sc_scegli_profilo" in globals() else sez0
    st.markdown(RBU_CSS, unsafe_allow_html=True) if "RBU_CSS" in globals() else None
    d = sc_dati()
    lista = _apn_lista(d, sez)
    st.caption("Visite, lavori, incontri: segna chi, quando e perché. Ti avviso col campanellino 🔔.")
    if st.button("➕ Aggiungi un appuntamento", key="apn_nuovo_" + sez, type="primary", width="stretch"):
        st.session_state["apn_mod"] = "__nuovo__"
        sc_rerun()
    if st.session_state.get("apn_mod") == "__nuovo__":
        _apn_modulo(sez, {})
    if not lista:
        st.info("Nessun appuntamento scritto qui. Per aggiungerne uno tocca «Aggiungi un appuntamento».")
        return
    oggi_ = sc_oggi()
    futuri = sorted([a for a in lista if not a.get("fatto") and (sc_data(a.get("data")) or oggi_) >= oggi_], key=lambda a: _apn_quando(a) or _ap_dt.datetime.max)
    passati = sorted([a for a in lista if a not in futuri], key=lambda a: _apn_quando(a) or _ap_dt.datetime.min, reverse=True)
    st.markdown(f"### 📅 Prossimi ({len(futuri)})")
    if not futuri:
        st.caption("Niente in programma.")
    for a in futuri:
        _apn_card(sez, a, False)
    if passati:
        with st.expander(f"🗂️ Passati o fatti ({len(passati)})"):
            for a in passati:
                _apn_card(sez, a, True)


def apn_apri(sez):
    st.session_state["apn_mod"] = None
    sc_dialogo("📅 Appuntamenti", lambda: _apn_corpo(sez))
