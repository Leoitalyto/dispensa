# -*- coding: utf-8 -*-
"""«🧮 Controllo ore» (pagina Lavoro): confronta il foglio Excel delle ore (già con il calcolo del contratto) con il PDF della busta paga
e dice, riga per riga (straordinario 20%, festivo 65%, notturno 33%, notturno festivo 75%), quanto la busta paga in più o in meno, in euro.
È il programma «Controllo busta paga» (repository controllo-busta-paga) portato dentro l'app. I file NON vengono salvati: si leggono e basta.
Serve pdfplumber e openpyxl (requirements.txt). Prefisso: cob_ / COB_."""
import re
import pandas as pd
import streamlit as st
from openpyxl import load_workbook

# Le 4 righe della busta paga. "piena" = la riga paga ore x paga x (1 + %);
# se "piena" e' False la riga paga solo la maggiorazione (ore x paga x %).
COB_VOCI = [
    {"chiave": "ord", "nome": "Straordinario 20%", "pct": 0.20, "piena": True,
     "schema": r"STRAORDINARIO\s*20\s*%"},
    {"chiave": "fest", "nome": "Straord. festivo diurno 65%", "pct": 0.65, "piena": True,
     "schema": r"STRAORD\.?\s*FEST\.?\s*DIURNO\s*65\s*%"},
    {"chiave": "nott", "nome": "Lavoro notturno 33%", "pct": 0.33, "piena": False,
     "schema": r"LAVORO\s+NOTTURNO\s*33\s*%"},
    {"chiave": "nottfest", "nome": "Lavoro notturno festivo 75%", "pct": 0.75, "piena": False,
     "schema": r"LAVORO\s+NOTT\.?\s*FEST\.?\s*75\s*%"},
]
COB_NUM = r"([\d\.,]+)"


def cob_numero_it(testo):
    """Trasforma '1.234,56' in 1234.56"""
    return float(testo.replace(".", "").replace(",", "."))


def cob_tariffa(paga, voce):
    return paga * (1 + voce["pct"]) if voce["piena"] else paga * voce["pct"]


def cob_leggi_excel(file):
    """Legge il foglio 'Ore' (intestazioni alla riga 5, 31 righe di giorni)."""
    xls = pd.ExcelFile(file)
    if "Ore" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="Ore", header=4, nrows=31)
        nuovo = True
    else:
        df = pd.read_excel(xls)          # vecchio formato
        df = df.rename(columns={"Ore_Lavorate": "Ore lavorate"})
        nuovo = False
    df.columns = [str(c).strip() for c in df.columns]
    if "Data" not in df.columns or "Ore lavorate" not in df.columns:
        raise ValueError("Non trovo le colonne 'Data' e 'Ore lavorate'. Colonne trovate: "
                         + ", ".join(df.columns))

    # --- CONTROLLI SULLE DATE E SUGLI ERRORI DEL FOGLIO ---
    primo_rigo = 6 if nuovo else 2          # numero della prima riga di dati in Excel
    if nuovo:
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            ws_ctrl = load_workbook(file, data_only=True)["Ore"]
            errati = [c.coordinate for riga in ws_ctrl["A6:V36"] for c in riga if c.data_type == "e"]
        except Exception:
            errati = []
        if errati:
            raise ValueError("il foglio contiene errori di calcolo (#VALORE! o simili) nelle celle "
                             + ", ".join(errati[:8]) + (" ..." if len(errati) > 8 else "")
                             + ". Di solito una data non è una vera data: scrivila come gg/mm/aaaa.")
    # Se per caso le date sono testo, le leggo come giorno/mese/anno.
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True, format="mixed")
    ore_tmp = pd.to_numeric(df["Ore lavorate"], errors="coerce").fillna(0.0)
    senza_data = df.index[df["Data"].isna() & (ore_tmp != 0)] + primo_rigo
    if len(senza_data):
        raise ValueError("ci sono righe con orari ma senza una data valida (righe Excel: "
                         + ", ".join(str(int(r)) for r in senza_data) + "). Scrivi la data come gg/mm/aaaa.")
    df = df.dropna(subset=["Data"]).copy()

    def num(nome):
        if nome in df.columns:
            return pd.to_numeric(df[nome], errors="coerce").fillna(0.0)
        return pd.Series(0.0, index=df.index)

    df["Ore lavorate"] = num("Ore lavorate")
    lorde_presenti = "Ore lorde (senza pausa)" in df.columns
    df["Ore lorde"] = num("Ore lorde (senza pausa)") if lorde_presenti else df["Ore lavorate"]
    df["Notturne"] = num("di cui notturne")
    df["Ore assenza"] = num("Ore assenza")
    if "Festivo" in df.columns:
        df["Giorno festivo"] = df["Festivo"].fillna("").astype(str).str.strip().str.lower().isin(["sì", "si"])
    else:
        df["Giorno festivo"] = False
    return df, nuovo, lorde_presenti


def cob_leggi_busta(testo):
    """Legge dal testo del PDF le 4 righe di straordinario/notturno e i dati del mese."""
    busta = {"voci": {}}
    for v in COB_VOCI:
        m = re.search(v["schema"] + r"\s+" + COB_NUM + r"\s+" + COB_NUM + r"\s+" + COB_NUM, testo, flags=re.IGNORECASE)
        try:
            busta["voci"][v["chiave"]] = (
                {"riga": m.group(0), "ore": cob_numero_it(m.group(1)),
                 "tariffa": cob_numero_it(m.group(2)), "importo": cob_numero_it(m.group(3))} if m else None)
        except ValueError:
            busta["voci"][v["chiave"]] = None

    def uno(schema, gruppo=1):
        m = re.search(schema, testo, flags=re.IGNORECASE)
        try:
            return cob_numero_it(m.group(gruppo)) if m else None
        except ValueError:
            return None

    busta["lavorabili"] = uno(r"ORE\s+LAVORABILI\s+" + COB_NUM)
    busta["effettive"] = uno(r"ORE\s+EFFETT\.?\s+LAVORATE\s+" + COB_NUM)
    busta["paga"] = uno(r"COMPETENZE\s+MESE\s+" + COB_NUM + r"\s+" + COB_NUM, 2)
    return busta


def cob_ore_attese(df, lavorabili):
    """Calcola le ore delle 4 righe con il metodo MENSILE della busta:
    straordinario = ore effettive - (ore lavorabili - ore di assenza legge 104).
    Le ore festive vanno prima nella riga festiva, il resto al 20%.
    Il notturno e' pagato su tutte le ore notturne lavorate."""
    lorde = float(df["Ore lorde"].sum())
    assenze = float(df["Ore assenza"].sum())
    straord = max(0.0, lorde - (lavorabili - assenze))
    f = df["Giorno festivo"]
    fest_lorde = float(df.loc[f, "Ore lorde"].sum())
    notte_fest = float(df.loc[f, "Notturne"].sum())
    notte_fer = float(df.loc[~f, "Notturne"].sum())
    fest_tot = min(fest_lorde, straord)
    n_f = min(notte_fest, fest_tot)
    ore = {"ord": straord - fest_tot, "fest": fest_tot - n_f, "nott": notte_fer, "nottfest": n_f}
    return ore, lorde, assenze, straord


def cob_ore_per_settimana(df, soglia):
    d = df.copy()
    d["Inizio settimana"] = d["Data"].dt.to_period("W-SUN").apply(lambda p: p.start_time.date())
    s = d.groupby("Inizio settimana")["Ore lavorate"].sum().reset_index()
    s["Oltre soglia"] = (s["Ore lavorate"] - soglia).clip(lower=0)
    return s



def cob_testo_pdf(pdf_file):
    """Il testo di tutte le pagine del PDF (pdfplumber, come nel programma originale; se manca, PyMuPDF)."""
    dati = pdf_file.getvalue() if hasattr(pdf_file, "getvalue") else pdf_file.read()
    try:
        import io
        import pdfplumber
        testo = ""
        with pdfplumber.open(io.BytesIO(dati)) as pdf:
            for page in pdf.pages:
                testo += (page.extract_text() or "") + "\n"
        return testo
    except ImportError:
        import fitz
        with fitz.open(stream=dati, filetype="pdf") as doc:
            return "\n".join(p.get_text() for p in doc)


def cob_pagina():
    """La voce «🧮 Controllo ore» del Lavoro."""
    st.markdown("#### 🧮 Controllo della busta paga")
    st.caption("Carica il **foglio Excel delle ore** (quello con il calcolo del tuo contratto già dentro) e il **PDF della busta paga**: "
               "l'app confronta ore e importi delle 4 righe di **straordinario e lavoro notturno** e ti dice **in euro** cosa va a tuo vantaggio o svantaggio.")
    st.info("🔒 I due file **non vengono salvati**: sono letti e basta. Il calcolo è una stima: per chiedere una correzione confrontati con l'ufficio paghe o con il sindacato.")
    with st.expander("⚙️ Solo se il PDF non viene letto"):
        paga_manuale = st.number_input("Paga oraria base (€)", value=13.22260, format="%.5f", key="cob_paga")
        lavorabili_manuale = st.number_input("Ore lavorabili del mese", value=0.0, step=0.5, key="cob_lav")
        soglia = st.number_input("Soglia settimanale (solo tabella informativa)", value=38.0, step=0.5, key="cob_soglia")
    excel_file = st.file_uploader("1️⃣ Carica il file Excel delle ore", type=["xlsx"], key="cob_xlsx")
    pdf_file = st.file_uploader("2️⃣ Carica il PDF della busta paga", type=["pdf"], key="cob_pdf")
    if not (excel_file and pdf_file):
        st.caption("Quando hai caricato **tutti e due** i file compare qui sotto il responso.")
        return
    try:
        df, nuovo, lorde_presenti = cob_leggi_excel(excel_file)
    except Exception as e:
        st.error(f"Non riesco a leggere il file Excel: {e}")
        return
    if df.empty:
        st.warning("Nel foglio non ci sono date compilate.")
        return
    try:
        testo_pdf = cob_testo_pdf(pdf_file)
    except Exception as e:
        st.error(f"Non riesco a leggere il PDF ({type(e).__name__}). Controlla che sia la busta paga in PDF (non una foto).")
        return
    busta = cob_leggi_busta(testo_pdf)
    paga = busta["paga"] or paga_manuale
    lavorabili = busta["lavorabili"] or lavorabili_manuale
    if not lavorabili:
        st.error("Non trovo le ore lavorabili nel PDF. Scrivile qui sopra, in «⚙️ Solo se il PDF non viene letto».")
        return
    if not lorde_presenti:
        st.warning("Nel foglio Excel manca la colonna 'Ore lorde (senza pausa)': usa il foglio aggiornato, altrimenti le ore lavorate risultano più basse della busta.")
    ore, lorde, assenze, straord = cob_ore_attese(df, lavorabili)
    rapporto = ["CONTROLLO BUSTA PAGA", ""]

    st.markdown("##### Controllo ore e importi")
    righe, effetti, non_lette = [], [], []
    tot_busta = tot_atteso = 0.0
    for v in COB_VOCI:
        b = busta["voci"][v["chiave"]]
        ore_att = ore[v["chiave"]]
        tar_att = cob_tariffa(paga, v)
        D = round(ore_att * tar_att, 2)
        diff_riga = None
        if b:
            A = b["importo"]
            B = round(b["ore"] * b["tariffa"], 2)
            C = round(b["ore"] * tar_att, 2)
            tot_busta += A
            tot_atteso += D
            diff_riga = round(A - D, 2)
            for euro, testo in [
                (round(C - D, 2), f"{v['nome']}: la busta paga {b['ore']:.2f} ore, il foglio ne conta {ore_att:.2f} ({b['ore'] - ore_att:+.2f} ore)"),
                (round(B - C, 2), f"{v['nome']}: tariffa in busta {b['tariffa']:.5f} invece di {tar_att:.5f}"),
                (round(A - B, 2), f"{v['nome']}: l'importo in busta ({A:.2f}) non è ore x tariffa ({B:.2f})"),
            ]:
                if abs(euro) >= 0.01:
                    effetti.append((testo, euro))
        else:
            non_lette.append(v["nome"])
        righe.append({"Voce": v["nome"], "Ore busta": b["ore"] if b else None, "Ore foglio": round(ore_att, 2),
                      "Importo busta (€)": b["importo"] if b else None, "Importo atteso (€)": D, "Differenza (€)": diff_riga})
        rapporto.append(f"{v['nome']}: ore busta {b['ore'] if b else '—'} / foglio {ore_att:.2f}; importo busta {b['importo'] if b else '—'} / atteso {D:.2f}")
    st.dataframe(pd.DataFrame(righe), hide_index=True, width="stretch")
    if non_lette:
        st.warning("Non ho trovato nel PDF queste righe: " + ", ".join(non_lette) + ". I totali qui sotto non le comprendono.")

    st.markdown("##### Vantaggi e svantaggi per te")
    vantaggio = sum(e for _, e in effetti if e > 0)
    svantaggio = -sum(e for _, e in effetti if e < 0)
    saldo = round(tot_busta - tot_atteso, 2)
    m1, m2, m3 = st.columns(3)
    m1.metric("A tuo vantaggio", f"{vantaggio:.2f} €")
    m2.metric("A tuo svantaggio", f"{svantaggio:.2f} €")
    m3.metric("Saldo", f"{saldo:+.2f} €")
    rapporto += ["", f"A tuo vantaggio: {vantaggio:.2f} €", f"A tuo svantaggio: {svantaggio:.2f} €", f"Saldo: {saldo:+.2f} €", ""]
    if not effetti:
        st.success("✅ Nessuna differenza: busta e foglio coincidono.")
        rapporto.append("Nessuna differenza: busta e foglio coincidono.")
    for testo, euro in effetti:
        if euro > 0:
            st.success(f"A tuo VANTAGGIO: la busta paga {euro:.2f} € in più. {testo}")
            rapporto.append(f"VANTAGGIO +{euro:.2f} €: {testo}")
        else:
            st.error(f"A tuo SVANTAGGIO: la busta paga {abs(euro):.2f} € in meno. {testo}")
            rapporto.append(f"SVANTAGGIO -{abs(euro):.2f} €: {testo}")
    bf, bn = busta["voci"]["fest"], busta["voci"]["nottfest"]
    if bf and bn:
        d_f, d_n = bf["ore"] - ore["fest"], bn["ore"] - ore["nottfest"]
        if abs(d_f) > 0.01 and abs(d_f + d_n) <= 0.01:
            if d_f > 0:
                st.info(f"La busta ha spostato {abs(d_f):.2f} ore dalla riga 'notturno festivo' alla riga 'festivo diurno': quelle ore sono pagate come festivo diurno (tariffa più alta) invece che con la sola maggiorazione notturna.")
            else:
                st.info(f"La busta ha spostato {abs(d_f):.2f} ore dalla riga 'festivo diurno' alla riga 'notturno festivo': quelle ore sono pagate con la sola maggiorazione notturna (tariffa più bassa) invece che come festivo diurno.")
    if not non_lette:
        verso = "più alta" if saldo > 0 else "più bassa" if saldo < 0 else "uguale"
        st.caption(f"Totale delle 4 righe: busta {tot_busta:.2f} €, foglio {tot_atteso:.2f} € (busta {verso}).")

    st.markdown("##### Altri controlli")
    if busta["effettive"] is not None:
        d_ore = busta["effettive"] - lorde
        if abs(d_ore) <= 0.01:
            st.success(f"✅ Ore effettive lavorate: {busta['effettive']:.2f} in busta = {lorde:.2f} nel foglio (senza pausa).")
        else:
            stima = abs(d_ore) * paga
            if d_ore < 0:
                st.error(f"A tuo SVANTAGGIO: la busta conta {abs(d_ore):.2f} ore lavorate in meno del foglio ({busta['effettive']:.2f} contro {lorde:.2f}): circa {stima:.2f} € in meno (stima, in parte già compresa nelle righe sopra).")
            else:
                st.success(f"A tuo VANTAGGIO: la busta conta {d_ore:.2f} ore lavorate in più del foglio ({busta['effettive']:.2f} contro {lorde:.2f}): circa {stima:.2f} € in più (stima, in parte già compresa nelle righe sopra).")
    for v in COB_VOCI:
        b = busta["voci"][v["chiave"]]
        if b and abs(b["tariffa"] - cob_tariffa(paga, v)) < 0.0001 and abs(b["ore"] * b["tariffa"] - b["importo"]) < 0.02:
            st.success(f"✅ {v['nome']}: tariffa {b['tariffa']:.5f} e importo corretti.")
    st.info(f"Metodo della busta: straordinario = ore effettive {lorde:.2f} - (ore lavorabili {lavorabili:.2f} - ore di assenza {assenze:.2f}) = {straord:.2f} ore. Le ore festive vanno nella riga festiva, le altre al 20%.")
    rapporto += ["", f"Straordinario = ore effettive {lorde:.2f} - (lavorabili {lavorabili:.2f} - assenza {assenze:.2f}) = {straord:.2f} ore.",
                 "Calcolo stimato: per una correzione confrontati con l'ufficio paghe o con il sindacato."]
    st.download_button("📄 Scarica il responso (testo)", "\n".join(rapporto).encode("utf-8"), file_name="controllo_busta_paga.txt", mime="text/plain", width="stretch", key="cob_scarica")
    with st.expander("Calcolo settimanale oltre soglia (solo informativo)"):
        st.dataframe(cob_ore_per_settimana(df, soglia).round(2), hide_index=True, width="stretch")
        st.caption("La busta non usa questo metodo: serve solo per confronto.")
    with st.expander("Testo letto dal PDF (per controllo)"):
        for v in COB_VOCI:
            b = busta["voci"][v["chiave"]]
            st.write(v["nome"], "→", b["riga"] if b else "non trovata")
        st.text(testo_pdf[:4000])
