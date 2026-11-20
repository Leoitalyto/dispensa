# -*- coding: utf-8 -*-
"""📅 FESTIVITÀ UFFICIALI NEL CONTROLLO ORE (Nager.Date: gratuito, senza chiave; con riserva calcolata dall'app).

RICHIESTA (Leonardo, 20 novembre): fra le API gratuite, quella delle festività per il Controllo ore.
• In Lavoro → 🧮 Controllo ore, dopo aver caricato foglio e busta: l'app confronta le date del foglio con le FESTE NAZIONALI italiane
  (Capodanno, Epifania, Pasquetta, 25 aprile, 1° maggio, 2 giugno, Ferragosto, Ognissanti, Immacolata, Natale, Santo Stefano)
  e con la FESTA DEL PATRONO della tua città (si sceglie una volta: Torino 24 giugno…).
  - giorno di festa lavorato ma NON segnato «festivo» nel foglio → avviso rosso con le ore e una stima di quanto potresti perdere;
  - giorno segnato «festivo» che non è una festa (né domenica) → avviso giallo da controllare.
• Se Nager.Date non risponde, le feste nazionali italiane le calcola l'app (anche la Pasqua): il controllo funziona sempre.
LIMITE: le regole del tuo contratto (per esempio se la domenica conta come festivo) le sa l'ufficio paghe: questo è un aiuto a vedere, non un calcolo ufficiale."""
from datetime import date as _fs_date, timedelta as _fs_td

import requests as _fs_req
import streamlit as st

FS_PATRONI = {"Nessuno": None, "Torino · San Giovanni (24 giugno)": (6, 24), "Genova · San Giovanni (24 giugno)": (6, 24), "Firenze · San Giovanni (24 giugno)": (6, 24),
              "Milano · Sant'Ambrogio (7 dicembre)": (12, 7), "Roma · Santi Pietro e Paolo (29 giugno)": (6, 29), "Napoli · San Gennaro (19 settembre)": (9, 19),
              "Bologna · San Petronio (4 ottobre)": (10, 4), "Bari · San Nicola (6 dicembre)": (12, 6), "Palermo · Santa Rosalia (15 luglio)": (7, 15),
              "Venezia · San Marco (25 aprile)": (4, 25), "Cagliari · San Saturnino (30 ottobre)": (10, 30), "Trieste · San Giusto (3 novembre)": (11, 3),
              "Altra città: scelgo io la data": "scelta"}


def _fs_pasqua(anno):
    """Domenica di Pasqua (calcolo di Gauss/Meeus)."""
    a, b, c = anno % 19, anno // 100, anno % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    mese = (h + l_ - 7 * m + 114) // 31
    giorno = ((h + l_ - 7 * m + 114) % 31) + 1
    return _fs_date(anno, mese, giorno)


def fs_feste_calcolate(anno):
    fisse = [(1, 1, "Capodanno"), (1, 6, "Epifania"), (4, 25, "Festa della Liberazione"), (5, 1, "Festa del Lavoro"), (6, 2, "Festa della Repubblica"),
             (8, 15, "Ferragosto"), (11, 1, "Ognissanti"), (12, 8, "Immacolata Concezione"), (12, 25, "Natale"), (12, 26, "Santo Stefano")]
    out = {_fs_date(anno, m, g): n for m, g, n in fisse}
    p = _fs_pasqua(anno)
    out[p] = "Pasqua"
    out[p + _fs_td(days=1)] = "Lunedì dell'Angelo (Pasquetta)"
    return out


@st.cache_data(ttl=30 * 24 * 3600, show_spinner=False)
def fs_feste(anno, paese="IT"):
    """{data: nome} delle feste nazionali: da Nager.Date, altrimenti calcolate dall'app."""
    out = fs_feste_calcolate(anno) if paese == "IT" else {}
    try:
        r = _fs_req.get(f"https://date.nager.at/api/v3/PublicHolidays/{int(anno)}/{paese}", timeout=8)
        if r.status_code == 200:
            for x in r.json() or []:
                if x.get("global", True):
                    try:
                        g = _fs_date.fromisoformat(x["date"])
                    except Exception:
                        continue
                    out.setdefault(g, x.get("localName") or x.get("name") or "Festa")
    except Exception:
        pass
    return out


def _fs_patrono():
    try:
        return ((carica_dati(crea_archivio(), percorso_mio()).get("impostazioni") or {}).get("patrono")) or {}
    except Exception:
        return {}


def fs_patrono_ui():
    """Scegliere la festa del patrono (una volta, resta salvata)."""
    pat = _fs_patrono()
    nomi = list(FS_PATRONI)
    att = pat.get("nome") if pat.get("nome") in nomi else "Nessuno"
    scelta = st.selectbox("⛪ Festa del patrono della tua città (conta come festivo)", nomi, index=nomi.index(att), key="fs_patrono")
    mese, giorno = pat.get("mese"), pat.get("giorno")
    if FS_PATRONI[scelta] == "scelta":
        c1, c2 = st.columns(2)
        giorno = c1.number_input("Giorno", 1, 31, int(giorno or 1), key="fs_pg")
        mese = c2.number_input("Mese", 1, 12, int(mese or 1), key="fs_pm")
    elif FS_PATRONI[scelta]:
        mese, giorno = FS_PATRONI[scelta]
    else:
        mese = giorno = None
    nuovo = {"nome": scelta, "mese": mese, "giorno": giorno}
    cambiato = nuovo != {k: pat.get(k) for k in nuovo} and not (not pat and scelta == "Nessuno")
    if cambiato and st.button("💾 Ricorda il patrono", key="fs_salva", width="stretch"):
        def _fn(d, v=nuovo):
            d.setdefault("impostazioni", {})["patrono"] = v
        salva_file(percorso_mio(), _fn, "Festa del patrono")
        st.rerun()
    return nuovo


def fs_controllo_ore(df, paga=0.0):
    """Dopo «Controllo ore e importi»: feste lavorate ma non segnate festive, e festivi segnati che non sono feste."""
    try:
        if df is None or df.empty or "Data" not in df.columns:
            return
        st.markdown("##### 📅 Giorni di festa")
        with st.expander("⛪ Festa del patrono e feste dell'anno"):
            pat = fs_patrono_ui()
            anni = sorted({int(x.year) for x in df["Data"].dropna()})
            for a_ in anni:
                st.caption(f"Feste nazionali {a_}: " + " · ".join(f"{g.day}/{g.month} {n}" for g, n in sorted(fs_feste(a_).items())))
        pat = _fs_patrono()
        mancanti, dubbi = [], []
        for _i, r in df.iterrows():
            g = r["Data"].date() if hasattr(r["Data"], "date") else r["Data"]
            feste = fs_feste(g.year)
            nome = feste.get(g)
            if not nome and pat.get("mese") and pat.get("giorno") and (g.month, g.day) == (int(pat["mese"]), int(pat["giorno"])):
                nome = "Patrono · " + str(pat.get("nome", "")).split("·")[-1].strip()
            try:
                ore = float(r.get("Ore lavorate") or 0)
            except Exception:
                ore = 0.0
            festivo = bool(r.get("Giorno festivo"))
            if nome and ore > 0 and not festivo:
                mancanti.append((g, nome, ore))
            elif festivo and not nome and g.weekday() != 6:
                dubbi.append(g)
        if mancanti:
            ore_tot = sum(o for _g, _n, o in mancanti)
            stima = ore_tot * float(paga or 0) * 0.45
            st.error("⚠️ Hai lavorato in **giorni di festa** che nel foglio **non sono segnati come festivi**: "
                     + "; ".join(f"**{g.day}/{g.month}** ({n}, {o:.2f} h)" for g, n, o in mancanti)
                     + (f". Quelle ore andrebbero pagate come **festivo** (65%) e non come straordinario normale (20%): la differenza può arrivare a circa **{stima:.2f} €**" if stima else "")
                     + ". Segna «festivo» quei giorni nel foglio e ricarica, oppure chiedi all'ufficio paghe.")
        else:
            st.success("✅ Nessun giorno di festa lavorato senza il segno «festivo».")
        if dubbi:
            st.warning("Questi giorni sono segnati **festivi** ma non sono feste nazionali né del patrono (e non sono domenica): "
                       + ", ".join(f"{g.day}/{g.month}" for g in dubbi) + ". Controlla nel foglio (potrebbe valere una regola del tuo contratto).")
        st.caption("Feste nazionali da Nager.Date (gratuito); se non risponde le calcola l'app. Le regole del tuo contratto (es. domeniche) le conosce l'ufficio paghe.")
    except Exception as e_:
        st.caption(f"(controllo delle feste non disponibile: {type(e_).__name__})")
