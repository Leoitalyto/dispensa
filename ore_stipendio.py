# -*- coding: utf-8 -*-
"""«💰 Stipendio previsto» (pagina Lavoro): si inserisce UNA volta il modulo delle ore (ORE_LAVORO…xlsx, con 12 mesi + «Parametri» + «RIEPILOGO»);
l'app lo tiene nell'archivio e mostra SEMPRE la previsione dello stipendio, mese per mese e anno, secondo i parametri del contratto scritti nel modulo.
Quando il modulo viene compilato di nuovo si ricarica (stesso pulsante) e la previsione si aggiorna. Nessun servizio esterno, nessuna chiave.
Il calcolo è nel foglio Excel (cella per cella, controllato): qui si LEGGONO i risultati. Prefisso: ost_ / OST_."""
import io
import uuid
import html as _ost_html
from datetime import datetime
import streamlit as st

OST_MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
# voce → inizio dell'etichetta (colonna A del foglio mensile) da cercare nel blocco «STRAORDINARIO E PREVISIONE STIPENDIO»; il valore e' nella colonna F.
# Si cerca per etichetta (non per numero di riga): cosi' vale per il modulo con le righe piu' in basso e anche per la vecchia versione.
OST_ETICHETTE = [("lavorabili", ("ore lavorabili usate",)), ("lorde", ("ore lavorate lorde",)), ("assenza", ("ore di assenza",)), ("straord", ("ore di straordinario",)),
                 ("ore_ord", ("straordinario al 20%",)), ("ore_fest", ("straordinario festivo diurno",)), ("ore_nott", ("lavoro notturno (feriale)",)),
                 ("ore_nottfest", ("lavoro notturno festivo",)), ("paga", ("paga oraria base",)), ("imp_ord", ("importo straordinario 20%",)),
                 ("imp_fest", ("importo straordinario festivo",)), ("imp_nott", ("importo lavoro notturno 33%",)), ("imp_nottfest", ("importo lavoro notturno festivo",)),
                 ("tot_str", ("totale straordinario",)), ("base", ("retribuzione mensile fissa", "retribuzione base")), ("lordo", ("retribuzione lorda prevista",)),
                 ("netto", ("stipendio netto previsto",))]
OST_ETICHETTE_NUOVE = [("ore_13", ("straordinario al 13%",)), ("imp_13", ("importo straordinario 13%",)), ("gia13", ("ore al 13% già usate",)),
                       ("mens", ("mensilità aggiuntiva", "mensilita aggiuntiva")), ("unatan", ("altre voci una tantum",)), ("cred", ("rimborso 730",)),
                       ("detrazione", ("detrazione ore",)), ("p104", ("permessi legge 104 pagati",)), ("vestiario", ("indennità lavoro vestito", "indennita lavoro vestito")),
                       ("pasti", ("buoni pasto",))]                       # solo nel modulo nuovo (assenti nel vecchio)


OST_ASSENZE = ["Perm. legge 104", "Ferie", "Mutua", "Infortunio", "Visita medica", "Perm. retribuiti", "Perm. non retrib."]


def _ost_n(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ost_eur(v):
    return "—" if v is None else f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def ost_leggi(dati):
    """Legge il modulo. Ritorna (risultato, errore). risultato = {anno, mesi:[{nome, …}], tot:{…}, par:{paga, trattenute}, calcolato:bool}."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(dati), data_only=True, read_only=False)
    except Exception as e:
        return None, f"Non riesco ad aprire il file Excel ({type(e).__name__})."
    mancanti = [m for m in OST_MESI if m not in wb.sheetnames]
    if mancanti or "Parametri" not in wb.sheetnames:
        return None, "Questo non è il modulo «ORE LAVORO»: mancano i fogli dei mesi o il foglio «Parametri». Carica il file ORE_LAVORO_20_ANNI aggiornato."
    mesi, calcolato = [], False
    for m in OST_MESI:
        ws = wb[m]
        riga = {"nome": m}
        inizio = None
        for rr in range(40, 100):
            if str(ws.cell(rr, 1).value or "").upper().startswith("STRAORDINARIO E PREVISIONE"):
                inizio = rr
                break
        if inizio is None:
            return None, f"Il foglio {m} non ha il blocco «previsione stipendio». Carica il modulo ORE_LAVORO aggiornato con le nuove formule."
        etichette = {}
        for rr in range(inizio + 1, inizio + 36):
            et = str(ws.cell(rr, 1).value or "").strip().lower()
            if et and et not in etichette:
                etichette[et] = rr
        for k, inizi in OST_ETICHETTE + OST_ETICHETTE_NUOVE:
            r = next((rr for et, rr in etichette.items() if any(et.startswith(i) for i in inizi)), None)
            if r is None:
                if (k, inizi) in OST_ETICHETTE:
                    return None, f"Il foglio {m} non ha la riga «{inizi[0]}» della previsione. Carica il modulo ORE_LAVORO aggiornato con le nuove formule."
                riga[k] = None
                continue
            riga[k] = _ost_n(ws.cell(r, 6).value)
        conti = {}
        for r in range(7, 38):
            if ws.cell(r, 1).value in (None, ""):
                continue
            visti = {str(ws.cell(r, col).value).strip() for col in (4, 7) if ws.cell(r, col).value}
            for et in visti & set(OST_ASSENZE):
                conti[et] = conti.get(et, 0) + 1
        riga["assenze_giorni"] = conti
        riga["ore_lavorate"] = _ost_n(ws["A41"].value)
        riga["giorni"] = _ost_n(ws["A42"].value)
        if riga["lordo"] is not None:
            calcolato = True
        mesi.append(riga)
    p = wb["Parametri"]
    def _par(inizio):
        for rr_ in range(3, 40):
            if str(p.cell(rr_, 1).value or "").strip().lower().startswith(inizio):
                return _ost_n(p.cell(rr_, 2).value)
        return None
    par = {"paga": _par("paga oraria base"), "trattenute": _par("trattenute stimate") or _par("trattenute sul lordo"), "ore_sett": _par("ore settimanali")}
    ore_g = {}
    for r in range(4, 12):
        nome_a = str(p.cell(r, 5).value or "").strip()
        if nome_a in OST_ASSENZE:
            ore_g[nome_a] = _ost_n(p.cell(r, 6).value) or 0.0
    par["ore_assenza"] = ore_g
    for riga in mesi:                       # ore delle assenze a giornata intera, secondo la tabella dei Parametri
        riga["assenze_ore_attese"] = sum(g * ore_g.get(t, 0.0) for t, g in riga["assenze_giorni"].items())
    try:
        anno = int(wb["GENNAIO"]["O1"].value)
    except (TypeError, ValueError):
        anno = None
    tot = {k: sum((x.get(k) or 0.0) for x in mesi) for k in ("lordo", "base", "tot_str", "straord", "ore_lavorate", "lavorabili")}
    return {"anno": anno, "mesi": mesi, "tot": tot, "par": par, "calcolato": calcolato}, ""


def ost_rapporto_trattenute(c):
    """Quanto resta del lordo secondo le TUE ultime buste paga: (rapporto netto/lordo, quante buste) oppure (None, 0)."""
    try:
        docs = [d for d in c.get("documenti", []) if d.get("tipo") == "Busta paga"]
        serie = lv_serie(docs) if "lv_serie" in globals() else []
    except Exception:
        serie = []
    rr = [s["netto"] / s["lordo"] for s in serie if s.get("netto") and s.get("lordo") and 0.3 < s["netto"] / s["lordo"] < 1.0]
    rr = rr[-6:]
    return (sum(rr) / len(rr), len(rr)) if rr else (None, 0)


def ost_arriva():
    """Il file portato dal pulsante arancione (o dal caricamento di riserva). Ritorna (nome, dati) oppure None."""
    riserva = None
    err_t = ack_t = ""
    if "_ca_avvia_trasferimento" in globals():
        with st.container(key="nascosti_cadocost"):
            riserva = st.file_uploader("canale2", key="fotopdf_cadocost")
        _ca_avvia_trasferimento()
        ack_t, err_t = _ca_trasf_ricevi()
        if riserva is not None:
            ack_t = _ost_html.escape(f"upl:{riserva.name}:{riserva.size}", quote=True)
        with st.container(key="ca_ricezione"):
            st.text_input("ca-pdf-trasf", key="ca_trasf_in", label_visibility="collapsed")
    if "_CA_CSS_FOTO" in globals():
        st.markdown(_CA_CSS_FOTO, unsafe_allow_html=True)
    arrivato = None
    nuovo = st.session_state.pop("ca_bozza_in", None)
    if nuovo and nuovo.get("dati"):
        arrivato = (nuovo.get("nome") or "modulo.xlsx", nuovo["dati"])
    if riserva is not None and st.session_state.get("ost_riserva_vista") != f"{riserva.name}{riserva.size}":
        st.session_state["ost_riserva_vista"] = f"{riserva.name}{riserva.size}"
        arrivato = (riserva.name, riserva.getvalue())
    return arrivato, ack_t, err_t


def ost_pagina(c):
    st.markdown("#### 💰 Stipendio previsto")
    st.caption("Inserisci **una volta** il modulo delle ore (**ORE_LAVORO…xlsx**). L'app lo tiene qui e ti mostra **sempre la previsione dello stipendio**, "
               "calcolata dagli orari che hai scritto e dai **parametri del tuo contratto** (foglio «Parametri» del modulo). "
               "Ogni volta che compili altri giorni, ricarica il modulo: la previsione si aggiorna.")
    arrivato, ack_t, err_t = ost_arriva()
    salvato = c.get("modulo_ore") or {}
    messaggio = ""
    if arrivato:
        nome, dati = arrivato
        if not nome.lower().endswith((".xlsx", ".xlsm")):
            messaggio = f"Il file «{nome}» non è un foglio Excel (.xlsx)."
        else:
            ris, err = ost_leggi(dati)
            if err:
                messaggio = err
            else:
                nid = "mo" + uuid.uuid4().hex[:10]
                _ca_scrivi_file(nid, nome, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", dati)
                rif = {"id": nid, "nome": nome, "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "aggiornato": datetime.now().isoformat(timespec="minutes")}
                _ca_salva(lambda cc, r=rif: cc.__setitem__("modulo_ore", r), "Lavoro: modulo ore")
                st.session_state["messaggio"] = f"✅ Modulo «{nome}» salvato: ecco la previsione."
                st.rerun()
    if "_ca_avvia_trasferimento" in globals():
        st.markdown(f"<div class='ca-pdf-btn' role='button' tabindex='0' data-ca-pdf='1' style='background:linear-gradient(135deg,#2e7d32,#00897b)'>"
                    f"📊 {'Sostituisci il modulo ore con uno più recente' if salvato else 'Scegli il modulo ore (ORE_LAVORO…xlsx)'}</div>"
                    f"<div class='ca-pdf-stato' data-ca-stato='1'>{'⚠️ ' + _ost_html.escape(err_t) if err_t else 'Tocca il pulsante e scegli il file: il telefono mostra tutti i file.'}</div>"
                    f"<span data-ca-ack='{ack_t}' style='display:none'></span><pre data-ca-log='1' style='display:none'></pre>", unsafe_allow_html=True)
    with st.expander("Se il pulsante non funziona: caricamento normale"):
        fx = st.file_uploader("Modulo ore (.xlsx)", key="ost_xlsx")
        if fx is not None and st.session_state.get("ost_x_vista") != f"{fx.name}{fx.size}":
            st.session_state["ost_x_vista"] = f"{fx.name}{fx.size}"
            st.session_state["ca_bozza_in"] = {"nome": fx.name, "dati": fx.getvalue()}
            st.rerun()
    if messaggio:
        st.error(messaggio)
    if not salvato:
        st.info("Ancora nessun modulo. Tocca il pulsante verde qui sopra e scegli il tuo file **ORE_LAVORO…xlsx**.")
        return
    letto = _ca_leggi_file(salvato) if "_ca_leggi_file" in globals() else []
    if not letto:
        st.warning("Il modulo salvato non si legge più. Caricalo di nuovo con il pulsante verde.")
        return
    nome_f, mime_f, dati_f = letto[0]
    quando = str(salvato.get("aggiornato") or "")[:16].replace("T", " alle ")
    st.success(f"📎 Modulo in uso: **{salvato.get('nome') or nome_f}**" + (f" · caricato il {quando}" if quando else ""))
    ris, err = ost_leggi(dati_f)
    if err:
        st.error(err)
        return
    if not ris["calcolato"]:
        st.warning("Il file non contiene i risultati dei calcoli (non è mai stato aperto in Excel). Aprilo con Excel o Fogli Google, salvalo e caricalo di nuovo.")
        return
    mesi = ris["mesi"]
    oggi_ = datetime.now()
    idx_def = max(0, min(11, oggi_.month - 1))
    attivi = [i for i, m in enumerate(mesi) if (m.get("ore_lavorate") or 0) > 0 or (m.get("assenza") or 0) > 0 or m.get("assenze_giorni")]
    if attivi and (idx_def not in attivi or (ris["anno"] and ris["anno"] != oggi_.year)):
        idx_def = attivi[-1]                                                     # il mese corrente è ancora vuoto: si parte dall'ultimo mese compilato
    scelta = st.selectbox("Mese", [m["nome"].capitalize() for m in mesi], index=idx_def, key="ost_mese")
    m = next(x for x in mesi if x["nome"].capitalize() == scelta)
    st.markdown(f"##### 📅 {scelta} {ris['anno'] or ''}")
    rapporto, n_buste = (None, 0)
    tratt = ris["par"].get("trattenute")
    if m.get("netto") is not None:
        rapporto = None
        origine = (f"con le trattenute del foglio «Parametri» ({tratt * 100:.1f}% del lordo di un mese normale; 13ª e 14ª tassate di più)" if tratt else "dal foglio del modulo")
    elif tratt:
        rapporto = 1 - tratt
        origine = f"con le trattenute del modulo ({tratt * 100:.1f}%)"
    else:
        rapporto, n_buste = ost_rapporto_trattenute(c)
        origine = f"in base alle tue ultime {n_buste} buste paga (resta circa il {rapporto * 100:.0f}% del lordo)" if rapporto else ""
    lordo = m.get("lordo")
    netto = m.get("netto") if m.get("netto") is not None else (round(lordo * rapporto, 2) if (lordo is not None and rapporto) else None)
    c1, c2 = st.columns(2)
    c1.metric("💶 Lordo previsto", _ost_eur(lordo))
    c2.metric("💰 Netto previsto (stima)", _ost_eur(netto) if netto is not None else "—")
    if netto is None:
        st.caption("Per vedere anche il **netto** serve una stima delle trattenute: carica le tue buste paga in **💶 Buste paga**, oppure scrivi la percentuale nel foglio «Parametri» del modulo (cella «Trattenute stimate»).")
    elif origine:
        st.caption(f"Netto calcolato {origine}. È una stima: la busta reale può differire.")
    if (m.get("ore_lavorate") or 0) == 0 and (m.get("assenza") or 0) == 0 and not (m.get("assenze_giorni") or {}):
        st.info("In questo mese non è ancora stato scritto nessun orario: la previsione comprende solo la retribuzione base. Compila il modulo e ricaricalo.")
    h104 = (m.get("assenze_giorni") or {}).get("Perm. legge 104", 0) * ((ris["par"].get("ore_assenza") or {}).get("Perm. legge 104") or 0)
    righe = [("Ore lavorabili del mese", f"{m['lavorabili']:.2f}" if m.get("lavorabili") is not None else "—"),
             ("Ore lavorate lorde (senza pausa)", f"{m['lorde']:.2f}" if m.get("lorde") is not None else "—"),
             ("Ore di assenza", f"{m['assenza']:.2f}" if m.get("assenza") is not None else "—"),
             ("Ore di straordinario", f"{m['straord']:.2f}" if m.get("straord") is not None else "—"),
             ("Retribuzione mensile fissa" if m.get("detrazione") is not None else "Retribuzione base", _ost_eur(m.get("base"))),
             *([("Detrazione ore (permessi 104 e non retribuiti)", _ost_eur(m.get("detrazione"))),
                ("Permessi Legge 104 pagati" + (f" ({h104:.2f} h)" if h104 else ""), _ost_eur(m.get("p104"))),
                ("Indennità lavoro vestito", _ost_eur(m.get("vestiario"))),
                ("Buoni pasto", _ost_eur(m.get("pasti")))] if m.get("detrazione") is not None else
               ([("   di cui permessi Legge 104 (retribuiti)", f"{h104:.2f} h · {_ost_eur(round(h104 * (m.get('paga') or 0), 2))}")] if h104 else [])),
             *([("Straordinario 13% (entro il tetto annuo)", f"{m.get('ore_13') or 0:.2f} h · {_ost_eur(m.get('imp_13'))}")] if m.get("ore_13") is not None else []),
             ("Straordinario 20%", f"{m.get('ore_ord') or 0:.2f} h · {_ost_eur(m.get('imp_ord'))}"),
             ("Straordinario festivo 65%", f"{m.get('ore_fest') or 0:.2f} h · {_ost_eur(m.get('imp_fest'))}"),
             ("Lavoro notturno 33%", f"{m.get('ore_nott') or 0:.2f} h · {_ost_eur(m.get('imp_nott'))}"),
             ("Lavoro notturno festivo 75%", f"{m.get('ore_nottfest') or 0:.2f} h · {_ost_eur(m.get('imp_nottfest'))}"),
             ("Totale straordinario e notturno", _ost_eur(m.get("tot_str"))),
             *([("Mensilità aggiuntiva (13ª / 14ª)", _ost_eur(m.get("mens")))] if m.get("mens") else []),
             *([("Altre voci una tantum", _ost_eur(m.get("unatan")))] if m.get("unatan") else []),
             *([("Rimborso 730 / crediti netti", _ost_eur(m.get("cred")))] if m.get("cred") else [])]
    gg = m.get("assenze_giorni") or {}
    if gg:
        og = ris["par"].get("ore_assenza") or {}
        righe_ass = [(("🩺 " if t == "Perm. legge 104" else "🏖️ " if t == "Ferie" else "📌 ") + t,
                      f"{n} giorn{'o' if n == 1 else 'i'}" + (f" · {n * og.get(t, 0):.2f} ore" if og.get(t) else " · ore dagli orari")) for t, n in gg.items()]
        st.markdown("**Assenze e permessi scritti nel mese** (i permessi 104 sono pagati con la loro paga, le altre assenze dentro la paga fissa)")
        st.markdown("<table style='width:100%;border-collapse:collapse;font-size:.92rem;color:#1b2b2b;background:rgba(255,255,255,.82);border-radius:12px;overflow:hidden'>"
                    + "".join(f"<tr style='border-bottom:1px solid #0001'><td style='padding:6px 9px'>{_ost_html.escape(a)}</td><td style='text-align:right;padding:6px 9px;font-weight:700'>{_ost_html.escape(b)}</td></tr>" for a, b in righe_ass)
                    + "</table>", unsafe_allow_html=True)
        if (m.get("assenza") or 0) + 0.01 < (m.get("assenze_ore_attese") or 0):
            st.warning("⚠️ Nel modulo ci sono permessi o assenze, ma i calcoli non li comprendono: il file è stato modificato senza ricalcolare. "
                       "Aprilo con **Excel** o **Fogli Google**, aspetta che i numeri si aggiornino, **salvalo** e caricalo di nuovo.")
    st.markdown("<table style='width:100%;border-collapse:collapse;font-size:.92rem;color:#1b2b2b;background:rgba(255,255,255,.82);border-radius:12px;overflow:hidden'>"
                + "".join(f"<tr style='border-bottom:1px solid #0001'><td style='padding:6px 9px'>{_ost_html.escape(a)}</td><td style='text-align:right;padding:6px 9px;font-weight:700'>{_ost_html.escape(b)}</td></tr>" for a, b in righe)
                + "</table>", unsafe_allow_html=True)
    st.caption("La previsione si calcola con il «metodo della busta»: straordinario = ore lavorate − (ore lavorabili − ore di assenza). Le ore lavorabili si possono correggere nel modulo (cella gialla del mese).")
    st.markdown("##### 📊 Tutto l'anno")
    try:
        import pandas as pd
        def _netto_m(x):
            if x.get("netto") is not None:
                return x["netto"]
            return round(x["lordo"] * rapporto, 2) if (x.get("lordo") is not None and rapporto) else 0.0
        tab = pd.DataFrame([{"Mese": x["nome"].capitalize(), "Ore lavorate": round(x.get("ore_lavorate") or 0, 2), "Straord. (h)": round(x.get("straord") or 0, 2),
                             "Lordo previsto (€)": round(x.get("lordo") or 0, 2), "Netto previsto (€)": round(_netto_m(x) or 0, 2)} for x in mesi])
        st.dataframe(tab, hide_index=True, width="stretch")
        gr = tab[["Mese", "Lordo previsto (€)", "Netto previsto (€)"]].copy()
        gr["Mese"] = [f"{i + 1:02d} {n[:3]}" for i, n in enumerate(gr["Mese"])]          # nell'ordine dei mesi (non alfabetico)
        st.bar_chart(gr.set_index("Mese"), height=240)
    except Exception:
        st.warning("La tabella non è disponibile su questo dispositivo.")
    netto_anno = sum((x.get("netto") if x.get("netto") is not None else (round((x.get("lordo") or 0) * rapporto, 2) if rapporto else 0)) for x in mesi) or None
    st.caption(f"Totale anno: lordo previsto **{_ost_eur(ris['tot']['lordo'])}** · straordinario e notturno **{_ost_eur(ris['tot']['tot_str'])}**" + (f" · netto previsto **{_ost_eur(netto_anno)}**." if netto_anno else "."))
    st.download_button("📥 Scarica il modulo salvato (per compilarlo)", dati_f, file_name=salvato.get("nome") or nome_f, mime=mime_f, width="stretch", key="ost_scarica")
    rapporto_txt = "\n".join([f"PREVISIONE STIPENDIO {scelta} {ris['anno'] or ''}", ""] + [f"{a}: {b}" for a, b in righe] + ["", f"Lordo previsto: {_ost_eur(lordo)}", f"Netto previsto (stima): {_ost_eur(netto) if netto is not None else '—'}"])
    st.download_button("📄 Scarica la previsione del mese (testo)", rapporto_txt.encode("utf-8"), file_name=f"previsione_{scelta.lower()}.txt", mime="text/plain", width="stretch", key="ost_scarica_t")
