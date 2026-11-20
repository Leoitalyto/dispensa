# -*- coding: utf-8 -*-
"""AVVISI METEO UTILI (Open-Meteo: gratuito, senza chiave, senza registrazione).

RICHIESTA (Leonardo, 20 novembre): fra le API gratuite aggiungere quelle utili all'uso dell'app. Open-Meteo serve per avvisi PRATICI, non per il meteo in sé:
• SALUTE  → caldo forte (bere spesso, niente uscite nelle ore calde, attenzione ad anziani e bambini) e freddo intenso;
• AUTO    → gelo (ghiaccio su parabrezza e strade), pioggia forte, raffiche di vento;
• ANIMALI → caldo (passeggiate presto o la sera, asfalto che scotta, acqua fresca, mai in auto) e freddo.
Si guardano i prossimi 3 giorni. Gli avvisi compaiono in cima alla sezione solo quando servono; se non c'è niente da segnalare non compare nulla.

DOVE: ognuno sceglie la sua città in Utilità → 🌦️ Avvisi meteo (si salva nei SUOI dati). Senza città, nessun avviso.
LIMITI: Open-Meteo è gratuito per uso NON commerciale (fino a 10.000 richieste al giorno). Le previsioni si tengono in memoria 3 ore: poche richieste.
Se il servizio non risponde, semplicemente non compare nulla."""
import html as _mt_html
from datetime import date as _mt_date

import requests as _mt_req
import streamlit as st

MT_SOGLIE = {"caldo": 32.0, "caldo_animali": 30.0, "gelo": 1.0, "freddo": -3.0, "pioggia": 30.0, "vento": 70.0}
_MT_GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def _mt_impostazione():
    try:
        return (carica_dati(crea_archivio(), percorso_mio()).get("impostazioni") or {}).get("meteo") or {}
    except Exception:
        return {}


@st.cache_data(ttl=3 * 3600, show_spinner=False)
def mt_previsioni(lat, lon):
    """Prossimi 4 giorni: [{giorno, max, min, pioggia, vento}] oppure [] se il servizio non risponde."""
    import os as _mt_os
    if _mt_os.environ.get("VM_METEO_FINTO"):                         # solo per le prove automatiche
        g0 = oggi() if "oggi" in globals() else _mt_date.today()
        return [{"giorno": g0.isoformat(), "max": 35, "min": -2, "pioggia": 0, "vento": 10}]
    try:
        r = _mt_req.get("https://api.open-meteo.com/v1/forecast", timeout=8, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 4,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_gusts_10m_max"})
        if r.status_code != 200:
            return []
        d = r.json().get("daily") or {}
        out = []
        for i, g in enumerate(d.get("time") or []):
            val = lambda k: (d.get(k) or [None] * 9)[i]
            out.append({"giorno": g, "max": val("temperature_2m_max"), "min": val("temperature_2m_min"), "pioggia": val("precipitation_sum"), "vento": val("wind_gusts_10m_max")})
        return out
    except Exception:
        return []


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def mt_cerca_luogo(nome, lingua="it"):
    """Città con quel nome: [{nome, lat, lon}] (fino a 6)."""
    try:
        r = _mt_req.get("https://geocoding-api.open-meteo.com/v1/search", timeout=8, params={"name": nome, "count": 6, "language": lingua, "format": "json"})
        out = []
        for x in (r.json().get("results") or []) if r.status_code == 200 else []:
            etich = ", ".join(str(v) for v in (x.get("name"), x.get("admin2") or x.get("admin1"), x.get("country")) if v)
            out.append({"nome": etich, "lat": x.get("latitude"), "lon": x.get("longitude")})
        return out
    except Exception:
        return []


def _mt_quando(iso):
    try:
        g = _mt_date.fromisoformat(iso)
        oggi_ = oggi() if "oggi" in globals() else _mt_date.today()
        diff = (g - oggi_).days
        return "oggi" if diff == 0 else "domani" if diff == 1 else f"{_MT_GIORNI[g.weekday()]} {g.day}"
    except Exception:
        return str(iso)


def mt_avvisi(sezione, prev):
    """Gli avvisi utili per quella sezione nei prossimi 3 giorni: [(icona, testo)]."""
    prev = [p for p in (prev or [])[:3] if p]
    out = []

    def primo(cond):
        return next((p for p in prev if cond(p)), None)
    num = lambda v: v is not None
    if sezione == "salute":
        p = primo(lambda p: num(p["max"]) and p["max"] >= MT_SOGLIE["caldo"])
        if p:
            out.append(("🥵", f"Caldo forte {_mt_quando(p['giorno'])}: fino a {round(p['max'])}°C. Bevi spesso anche senza sete, evita di uscire dalle 11 alle 17, "
                              "tieni fresca la casa. Attenzione soprattutto ad anziani, bambini e a chi prende farmaci per pressione o cuore."))
        p = primo(lambda p: num(p["min"]) and p["min"] <= MT_SOGLIE["freddo"])
        if p:
            out.append(("🥶", f"Freddo intenso {_mt_quando(p['giorno'])}: fino a {round(p['min'])}°C. Copriti bene, casa riscaldata; attenzione al ghiaccio se esci (cadute)."))
    elif sezione == "auto":
        p = primo(lambda p: num(p["min"]) and p["min"] <= MT_SOGLIE["gelo"])
        if p:
            out.append(("🧊", f"Possibile gelo {_mt_quando(p['giorno'])}: minima {round(p['min'])}°C. Ghiaccio sul parabrezza e sulle strade: esci qualche minuto prima, "
                              "non usare acqua calda sul vetro, guida piano su ponti e curve."))
        p = primo(lambda p: num(p["pioggia"]) and p["pioggia"] >= MT_SOGLIE["pioggia"])
        if p:
            out.append(("🌧️", f"Pioggia forte {_mt_quando(p['giorno'])}: circa {round(p['pioggia'])} mm. Evita sottopassi allagati, distanza di sicurezza più lunga, controlla i tergicristalli."))
        p = primo(lambda p: num(p["vento"]) and p["vento"] >= MT_SOGLIE["vento"])
        if p:
            out.append(("💨", f"Raffiche di vento forti {_mt_quando(p['giorno'])}: fino a {round(p['vento'])} km/h. Non parcheggiare sotto alberi o impalcature; attenzione con furgoni e moto."))
    elif sezione == "animali":
        p = primo(lambda p: num(p["max"]) and p["max"] >= MT_SOGLIE["caldo_animali"])
        if p:
            out.append(("🐾", f"Caldo {_mt_quando(p['giorno'])}: fino a {round(p['max'])}°C. Passeggiate al mattino presto o la sera, l'asfalto scotta le zampe "
                              "(prova con il dorso della mano), sempre acqua fresca, MAI lasciarli in auto nemmeno pochi minuti."))
        p = primo(lambda p: num(p["min"]) and p["min"] <= MT_SOGLIE["freddo"])
        if p:
            out.append(("❄️", f"Freddo {_mt_quando(p['giorno'])}: fino a {round(p['min'])}°C. Animali piccoli, anziani o a pelo corto: riparo caldo, cappottino se serve, acqua che non geli."))
    return out


def mt_mostra(sezione):
    """In cima alla sezione: gli avvisi, solo se ce ne sono."""
    if sezione not in ("salute", "auto", "animali"):
        return
    imp = _mt_impostazione()
    if not imp.get("lat") or imp.get("spento"):
        return
    avvisi = mt_avvisi(sezione, mt_previsioni(round(float(imp["lat"]), 3), round(float(imp["lon"]), 3)))
    if not avvisi:
        return
    righe = "".join(f"<div style='margin:3px 0'>{i} {_mt_html.escape(t)}</div>" for i, t in avvisi)
    st.markdown(f"<div style='border:1px solid #f59e0b;background:rgba(245,158,11,.10);border-radius:14px;padding:8px 12px;margin:6px 0;font-size:.92rem'>"
                f"<div style='font-weight:700;margin-bottom:2px'>🌦️ Avvisi meteo · {_mt_html.escape(str(imp.get('nome', '')).split(',')[0])}</div>{righe}"
                f"<div style='opacity:.7;font-size:.78rem;margin-top:4px'>Previsioni Open-Meteo. La città si cambia in Utilità → 🌦️ Avvisi meteo.</div></div>", unsafe_allow_html=True)


def mt_blocco_utilita():
    """Utilità → 🌦️ Avvisi meteo: scegliere la città."""
    imp = _mt_impostazione()
    st.caption("Avvisi **utili** quando servono: in **Salute** il caldo forte e il freddo intenso, in **Auto** gelo, pioggia forte e vento, in **Animali** caldo e freddo. "
               "Gratuito, senza chiavi (servizio Open-Meteo).")
    if imp.get("nome"):
        st.markdown(f"📍 Città scelta: **{_mt_html.escape(imp['nome'])}**" + (" · ⏸️ avvisi spenti" if imp.get("spento") else ""))
    nome = st.text_input("Scrivi la tua città", key="mt_cerca", placeholder="es. Torino")
    if nome.strip():
        trovati = mt_cerca_luogo(nome.strip(), lingua() if "lingua" in globals() else "it")
        if not trovati:
            st.warning("Non trovo questa città (o il servizio non risponde adesso). Prova a scriverla in un altro modo.")
        else:
            scelta = st.radio("Quale?", list(range(len(trovati))), format_func=lambda i: trovati[i]["nome"], key="mt_scelta")
            if st.button("💾 Usa questa città", key="mt_salva", type="primary", width="stretch"):
                def _fn(d, x=trovati[scelta]):
                    d.setdefault("impostazioni", {})["meteo"] = {"nome": x["nome"], "lat": x["lat"], "lon": x["lon"]}
                salva_file(percorso_mio(), _fn, "Città per gli avvisi meteo")
                st.success("Fatto ✅")
                st.rerun()
    if imp.get("nome"):
        spento = st.toggle("Spegni gli avvisi meteo", value=bool(imp.get("spento")), key="mt_spento")
        if spento != bool(imp.get("spento")):
            def _fn2(d, v=spento):
                d.setdefault("impostazioni", {}).setdefault("meteo", {})["spento"] = v
            salva_file(percorso_mio(), _fn2, "Avvisi meteo accesi/spenti")
            st.rerun()
        prev = mt_previsioni(round(float(imp["lat"]), 3), round(float(imp["lon"]), 3))
        if prev:
            st.caption("Prossimi giorni: " + " · ".join(f"{_mt_quando(p['giorno'])} {round(p['min'])}°/{round(p['max'])}°" for p in prev[:3] if p["min"] is not None and p["max"] is not None))
        else:
            st.caption("Le previsioni adesso non arrivano: riprova più tardi.")
