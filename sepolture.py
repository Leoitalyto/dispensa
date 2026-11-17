# -*- coding: utf-8 -*-
"""⚰️ Dove riposa: nella scheda di una persona che non c'è più si segna dove è stata tumulata, con tutti i dettagli:
tipo (tomba, loculo, cappella di famiglia, cinerario…), cimitero e comune, posizione (settore, campo, fila, numero, piano), data del funerale,
concessione (numero, durata, scadenza), lampada votiva, telefono e orari del cimitero, come arrivare, foto della lapide, note.
I dati stanno nella scheda (p["sepoltura"]); le foto in documenti/<uid>/. Si collega a compleanni.py (modulo e elenco). Prefisso: sp_"""
import datetime as _sp_dt
import html as _sp_html
import urllib.parse as _sp_up

import streamlit as st

SP_TIPI = ["Tomba a terra", "Loculo", "Tomba di famiglia", "Cappella gentilizia / edicola", "Cinerario (urna)", "Ossario", "Cenere affidata o dispersa", "Altro"]


def sp_data(x):
    try:
        return _sp_dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def _sp_opz(k, etichetta, attuale):
    if not st.checkbox(etichetta, value=bool(attuale), key=k + "_ha"):
        return None
    return st.date_input(etichetta, value=attuale or _sp_dt.date.today(), min_value=_sp_dt.date(1900, 1, 1), max_value=_sp_dt.date(2200, 12, 31), format="DD/MM/YYYY", key=k + "_d", label_visibility="collapsed")


def sp_campi(p, k):
    """I campi nel modulo della persona. → (dati, nuove_foto, foto_da_togliere)"""
    s = dict(p.get("sepoltura") or {})
    k = k + "_sp_"
    st.markdown("<div style='margin-top:10px;font-weight:700'>⚰️ Dove riposa</div>", unsafe_allow_html=True)
    ha = st.checkbox("Segno dove è stata tumulata", value=bool(s), key=k + "on")
    if not ha:
        return None, [], []
    tipo = st.selectbox("Tipo di sepoltura", SP_TIPI, index=SP_TIPI.index(s["tipo"]) if s.get("tipo") in SP_TIPI else 0, key=k + "tipo")
    dfun = _sp_opz(k + "df", "Data del funerale o della sepoltura", sp_data(s.get("data")))
    st.markdown("<b>Il cimitero</b>", unsafe_allow_html=True)
    cim = st.text_input("Nome del cimitero", value=s.get("cimitero", ""), key=k + "cim", placeholder="es. Cimitero Monumentale")
    com = st.text_input("Comune", value=s.get("comune", ""), key=k + "com")
    ind = st.text_input("Indirizzo del cimitero", value=s.get("indirizzo", ""), key=k + "ind")
    st.markdown("<b>Dove si trova dentro il cimitero</b>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    sett = c1.text_input("Reparto / settore / blocco", value=s.get("settore", ""), key=k + "set")
    campo = c2.text_input("Campo / riquadro / viale", value=s.get("campo", ""), key=k + "cam")
    c3, c4, c5 = st.columns(3, gap="small")
    fila = c3.text_input("Fila", value=s.get("fila", ""), key=k + "fila")
    num = c4.text_input("Numero", value=s.get("numero", ""), key=k + "num", help="Numero del loculo, della tomba o della cappella")
    piano = c5.text_input("Piano", value=s.get("piano", ""), key=k + "pia")
    come = st.text_area("Come trovarla (indicazioni)", value=s.get("come", ""), key=k + "come", height=80, placeholder="es. entrando a destra, dopo la cappella, terzo viale")
    gps = st.text_input("Posizione sulla mappa (facoltativa: scrivi le coordinate o incolla il link di Google Maps)", value=s.get("gps", ""), key=k + "gps")
    st.markdown("<b>Concessione e lampada votiva</b>", unsafe_allow_html=True)
    ncon = st.text_input("Numero del contratto / concessione", value=s.get("concessione_n", ""), key=k + "ncon")
    durata = st.text_input("Durata (es. 30 anni, perpetua)", value=s.get("durata", ""), key=k + "dur")
    scad = _sp_opz(k + "sc", "La concessione scade il", sp_data(s.get("scadenza")))
    lamp = st.text_input("Lampada votiva (numero del contratto o a chi è intestata)", value=s.get("lampada", ""), key=k + "lamp")
    lamp_sc = _sp_opz(k + "ls", "Il canone della lampada si paga entro il", sp_data(s.get("lampada_scadenza")))
    st.markdown("<b>Contatti del cimitero</b>", unsafe_allow_html=True)
    tel = st.text_input("📞 Telefono (ufficio cimiteriale / custode)", value=s.get("telefono", ""), key=k + "tel")
    orari = st.text_area("🕒 Orari di apertura", value=s.get("orari", ""), key=k + "ora", height=70)
    st.markdown("<b>Foto e note</b>", unsafe_allow_html=True)
    foto = list(s.get("foto") or [])
    togli = []
    for i, r in enumerate(foto):
        if st.checkbox(f"🗑️ Togli la foto «{r.get('nome', 'foto')}»", key=f"{k}tf{i}"):
            togli.append(r)
    nuove = (ar_uploader("📷 Aggiungi foto (lapide, posizione, ingresso)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=k + "up")
             if "ar_uploader" in globals() else st.file_uploader("📷 Aggiungi foto (lapide, posizione, ingresso)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=k + "up"))
    nota = st.text_area("📝 Note sulla sepoltura", value=s.get("nota", ""), key=k + "nota", height=80)
    dati = {"tipo": tipo, "data": dfun.isoformat() if dfun else "", "cimitero": cim.strip(), "comune": com.strip(), "indirizzo": ind.strip(), "settore": sett.strip(),
            "campo": campo.strip(), "fila": fila.strip(), "numero": num.strip(), "piano": piano.strip(), "come": come.strip(), "gps": gps.strip(),
            "concessione_n": ncon.strip(), "durata": durata.strip(), "scadenza": scad.isoformat() if scad else "", "lampada": lamp.strip(),
            "lampada_scadenza": lamp_sc.isoformat() if lamp_sc else "", "telefono": tel.strip(), "orari": orari.strip(), "nota": nota.strip(), "foto": foto}
    return dati, list(nuove or []), togli


def sp_salva_foto(dati, nuove, togli):
    """Salva le foto nuove e toglie quelle tolte. → dati pronti, elenco dei file da cancellare"""
    dati = dict(dati)
    dati["foto"] = [r for r in dati.get("foto", []) if r not in togli] + [cp_file_salva(f.getvalue(), getattr(f, "name", "foto"), getattr(f, "type", None) or "image/jpeg") for f in nuove]
    return dati, list(togli)


def sp_files(p):
    return list((p.get("sepoltura") or {}).get("foto") or [])


def sp_mappa(s):
    g = str(s.get("gps") or "").strip()
    if g.startswith("http"):
        return g
    q = g or ", ".join(x for x in (s.get("cimitero"), s.get("indirizzo"), s.get("comune")) if x)
    return "https://www.google.com/maps/search/?api=1&query=" + _sp_up.quote(q) if q else ""


def sp_mostra(p):
    """Nell'elenco: «⚰️ Dove riposa» con tutti i dettagli, i tasti mappa/telefono e le foto."""
    s = p.get("sepoltura")
    if not isinstance(s, dict) or not any(v for k, v in s.items() if k != "foto") and not s.get("foto"):
        return
    e = _sp_html.escape
    scad = sp_data(s.get("scadenza"))
    oggi = _sp_dt.date.today()
    with st.expander("⚰️ Dove riposa" + (f" · {s['cimitero']}" if s.get("cimitero") else "")):
        pos = [x for x in (("Settore " + s["settore"]) if s.get("settore") else "", ("Campo " + s["campo"]) if s.get("campo") else "", ("Fila " + s["fila"]) if s.get("fila") else "",
                           ("N. " + s["numero"]) if s.get("numero") else "", ("Piano " + s["piano"]) if s.get("piano") else "") if x]
        righe = []
        if s.get("tipo"):
            righe.append(f"<b>{e(s['tipo'])}</b>")
        if s.get("cimitero") or s.get("comune"):
            righe.append("🪦 " + e(" · ".join(x for x in (s.get("cimitero"), s.get("comune")) if x)))
        if s.get("indirizzo"):
            righe.append("📍 " + e(s["indirizzo"]))
        if pos:
            righe.append("🧭 " + e(" · ".join(pos)))
        if s.get("come"):
            righe.append("➡️ " + e(s["come"]))
        if sp_data(s.get("data")):
            righe.append("🕊️ Sepoltura: " + sp_data(s["data"]).strftime("%d/%m/%Y"))
        if s.get("concessione_n") or s.get("durata") or scad:
            t = "📜 Concessione" + (f" n. {e(s['concessione_n'])}" if s.get("concessione_n") else "") + (f" · {e(s['durata'])}" if s.get("durata") else "")
            if scad:
                g = (scad - oggi).days
                t += f" · scade il {scad.strftime('%d/%m/%Y')}" + (" <b>(SCADUTA)</b>" if g < 0 else f" <b>(tra {g} giorni)</b>" if g <= 365 else "")
            righe.append(t)
        if s.get("lampada") or sp_data(s.get("lampada_scadenza")):
            ls = sp_data(s.get("lampada_scadenza"))
            righe.append("🕯️ Lampada votiva" + (f": {e(s['lampada'])}" if s.get("lampada") else "") + (f" · canone entro il {ls.strftime('%d/%m/%Y')}" if ls else ""))
        if s.get("telefono"):
            righe.append("📞 " + e(s["telefono"]))
        if s.get("orari"):
            righe.append("🕒 " + e(s["orari"]).replace("\n", " · "))
        if s.get("nota"):
            righe.append("<i>" + e(s["nota"]) + "</i>")
        st.markdown("<div style='line-height:1.55;font-size:.92rem'>" + "<br>".join(righe) + "</div>", unsafe_allow_html=True)
        tasti = []
        if sp_mappa(s):
            tasti.append(("🗺️ Apri la mappa", sp_mappa(s)))
        tel = "".join(ch for ch in str(s.get("telefono") or "") if ch.isdigit() or ch == "+")
        if len(tel) >= 6:
            tasti.append(("📞 Chiama il cimitero", "tel:" + tel))
        if tasti:
            with st.container(key="cp_azioni_sp_" + str(p.get("id"))):
                for col, (et, url) in zip(st.columns(len(tasti), gap="small"), tasti):
                    col.link_button(et, url, width="stretch")
        for i, r in enumerate(s.get("foto") or []):
            d = cp_file_leggi(r)
            if d:
                st.image(d, caption=r.get("nome"), width="stretch")
