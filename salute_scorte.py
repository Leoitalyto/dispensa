# -*- coding: utf-8 -*-
"""SALUTE · 💊 SCORTE E RINNOVO RICETTE.

Per ogni medicinale di una persona (per esempio tua madre) scrivi:
• la DATA DI AVVIO (da quando comincia a prenderlo),
• quante PASTIGLIE ci sono nella scatola,
• quante se ne prendono al giorno (di solito si legge da sola dal programma di terapia: «1 compressa» × gli orari scelti; altrimenti la scrivi tu).
L'app calcola DA SOLA quando le pastiglie finiscono, ti avvisa qualche giorno prima (di partenza 7; sul telefono e dentro l'app) e prepara una BOZZA di email per la dottoressa con la lista dei
medicinali che stanno per finire. La bozza la ricontrolli e la mandi TU: l'app non invia niente al medico e non decide ricette né terapie.

COME SI INTEGRA (senza toccare quello che c'è):
• i dati stanno nel medicinale, sotto la chiave nuova `scorta` (il modulo Medicinali, quando salva, aggiorna solo i suoi campi: `scorta` non si perde);
• la terapia (giorni, orari, quantità, inizio, fine, sospesa) resta la sola fonte degli orari: qui si legge soltanto;
• gli avvisi usano gli stessi canali già scelti dalla persona (programma automatico, `promemoria.py`).
Il calcolo è una STIMA (si presume che le dosi previste vengano prese): con «Ne ho contate…» e «Ho comprato…» si corregge in un attimo."""
import hashlib
import html as _sc_h
import re
import urllib.parse
import uuid
from datetime import date, datetime, timedelta

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# CALCOLO (senza Streamlit: si prova da solo; il programma automatico ha la stessa copia in promemoria.py)
# ---------------------------------------------------------------------------------------------------------------------
SCORTA_PREAVVISI = [3, 5, 7, 10, 14]
_SCORTA_PAROLE = {"mezza": 0.5, "mezzo": 0.5, "un": 1, "una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6}


def _scorta_num(v):
    """Un numero scritto come «2», «0,5», «1/15» (una frazione). None se non è un numero."""
    t = str(v).strip().replace(",", ".")
    try:
        if "/" in t:
            a, b = t.split("/", 1)
            return float(a) / float(b) if float(b) else None
        return float(t)
    except (ValueError, TypeError):
        return None


def _scorta_data(iso):
    try:
        return date.fromisoformat(str(iso)[:10]) if iso else None
    except ValueError:
        return None


def scorta_parse_dose(testo):
    """«1 compressa», «2 compresse», «1/2», «½ compressa», «mezza compressa», «1,5», «una cpr», «due» → quante pastiglie per assunzione (None se non si capisce)."""
    t = str(testo or "").lower().strip()
    if not t:
        return None
    t = t.replace("½", " 0.5 ").replace("¼", " 0.25 ").replace("¾", " 0.75 ")
    m = re.search(r"(\d+)\s*/\s*(\d+)", t)
    if m and int(m.group(2)) > 0:
        return round(int(m.group(1)) / int(m.group(2)), 4)
    m = re.search(r"\d+(?:[.,]\d+)?", t)
    if m:
        return _scorta_num(m.group(0))
    for parola, valore in _SCORTA_PAROLE.items():
        if re.search(r"\b" + parola + r"\b", t):
            return float(valore)
    return None


def _scorta_terapie_di(terapie, pid, med_id):
    return [t for t in terapie if isinstance(t, dict) and t.get("profilo", "p0") == pid and t.get("med") == med_id]


def _scorta_consumo_terapie(rilevanti, d):
    """Pastiglie previste dalle terapie in un giorno (stesse regole di Terapie: giorni, inizio, fine, sospesa)."""
    tot = 0.0
    for t in rilevanti:
        if not (terapia_e_giorno(t, d) if "terapia_e_giorno" in globals() else d.weekday() in (t.get("giorni") or [])):
            continue
        ini, fin = _scorta_data(t.get("inizio")), _scorta_data(t.get("fine"))
        if (ini and d < ini) or (fin and d > fin):
            continue
        if t.get("stato") in ("sospesa", "terminata"):
            dal = _scorta_data(t.get("stato_dal"))
            if dal is None or d >= dal:
                continue
        q = scorta_parse_dose(t.get("quantita"))
        if q is None:
            continue
        tot += q * len(t.get("orari") or [])
    return tot


def _scorta_aggiungi_mesi(d, n):
    import calendar as _cal
    m = d.month - 1 + n
    a, m = d.year + m // 12, m % 12 + 1
    return date(a, m, min(d.day, _cal.monthrange(a, m)[1]))


def scorta_freq_valida(freq):
    """La frequenza «a intervalli» (una dose ogni N giorni, settimane o mesi) se è scritta bene, altrimenti None."""
    if not isinstance(freq, dict) or freq.get("tipo") not in ("giorni", "settimane", "mesi"):
        return None
    ogni, dose = _scorta_num(freq.get("ogni")), _scorta_num(freq.get("dose"))
    if not ogni or ogni < 1 or not dose or dose <= 0:
        return None
    return {"tipo": freq["tipo"], "ogni": int(ogni), "dose": dose, "prima": _scorta_data(freq.get("prima"))}


def scorta_descrivi_freq(freq):
    f = scorta_freq_valida(freq)
    if not f:
        return ""
    unita = {"giorni": ("giorno", "giorni"), "settimane": ("settimana", "settimane"), "mesi": ("mese", "mesi")}[f["tipo"]]
    return f"{f['dose']:g} " + (f"ogni {unita[0]}" if f["ogni"] == 1 else f"ogni {f['ogni']} {unita[1]}")


def _scorta_e_giorno_di_dose(f, prima, d):
    if d < prima:
        return False
    if f["tipo"] == "giorni":
        return (d - prima).days % f["ogni"] == 0
    if f["tipo"] == "settimane":
        return (d - prima).days % (7 * f["ogni"]) == 0
    m = (d.year - prima.year) * 12 + d.month - prima.month
    return m % f["ogni"] == 0 and d == _scorta_aggiungi_mesi(prima, m)


def scorta_calcola(med, terapie, pid, oggi_):
    """Lo stato della scorta di un medicinale.
    → {stato: spento | dati_mancanti | senza_terapia | dose_non_capita | nessun_consumo | ok | ok_lungo | in_esaurimento | finito, ultima (ultima dose coperta), fino_al (l'ultimo giorno
    in cui la scorta basta: il giorno PRIMA della prima dose non coperta), giorni (da oggi a fino_al), restano, per_giorno, preavviso, richiesto}
    Le assunzioni possono essere ogni giorno (dalla terapia o scritte a mano) oppure A INTERVALLI (una dose ogni N giorni, settimane o mesi, per esempio una fiala ogni 15 giorni)."""
    sc = med.get("scorta") or {}
    if not sc.get("attiva"):
        return {"stato": "spento"}
    avvio, iniz = _scorta_data(sc.get("avvio")), _scorta_num(sc.get("pastiglie"))
    pre = int(_scorta_num(sc.get("preavviso")) or 7)
    ris = {"stato": "dati_mancanti", "ultima": None, "fino_al": None, "giorni": None, "restano": None, "per_giorno": None, "preavviso": pre, "richiesto": _scorta_data(sc.get("rinnovo_richiesto"))}
    if avvio is None or iniz is None or iniz < 0:
        return ris
    freq = scorta_freq_valida(sc.get("frequenza"))
    manuale = _scorta_num(sc.get("per_giorno"))
    if manuale is not None and manuale <= 0:
        manuale = None
    rilevanti = _scorta_terapie_di(terapie, pid, med.get("id"))
    if freq is None and manuale is None:
        if not rilevanti:
            ris["stato"] = "senza_terapia"
            return ris
        if any(scorta_parse_dose(t.get("quantita")) is None for t in rilevanti if t.get("stato") not in ("terminata",)):
            ris["stato"] = "dose_non_capita"
            return ris
    prima = (freq["prima"] if freq else None) or avvio

    def consumo(d):
        if freq is not None:
            return freq["dose"] if _scorta_e_giorno_di_dose(freq, prima, d) else 0.0
        return manuale if manuale is not None else _scorta_consumo_terapie(rilevanti, d)
    cum, ultima, d, finisce, passati, scoperta = 0.0, None, min(avvio, prima), False, 0.0, None
    for _ in range(2400):
        c = consumo(d)
        if d >= avvio and d < oggi_:
            passati += c
        if c > 0 and d >= avvio:
            if cum + c > iniz + 1e-9:
                finisce, scoperta = True, d
                break
            cum += c
            ultima = d
        d += timedelta(days=1)
    ris["restano"] = max(0.0, round(iniz - passati, 2))
    ris["per_giorno"] = round(sum(consumo(oggi_ + timedelta(days=k)) for k in range(7)) / 7, 2)
    if ultima is None and not finisce:
        ris["stato"] = "nessun_consumo"
        return ris
    if not finisce:
        ris["stato"], ris["ultima"], ris["fino_al"], ris["giorni"] = "ok_lungo", ultima, ultima, (ultima - oggi_).days
        return ris
    if ultima is None:                                                                  # non bastano nemmeno per la prima dose
        ultima = avvio - timedelta(days=1)
    fino_al = scoperta - timedelta(days=1)                                              # la scorta basta fino al giorno prima della prima dose che non si riesce a coprire
    if freq is None:
        fino_al = max(fino_al, ultima)
    ris["ultima"], ris["fino_al"], ris["giorni"] = ultima, fino_al, (fino_al - oggi_).days
    ris["stato"] = "finito" if ris["giorni"] < 0 else ("in_esaurimento" if ris["giorni"] <= pre else "ok")
    return ris


def scorta_nuova_base(med, pastiglie, oggi_, nota=""):
    """Un nuovo punto di partenza: «da oggi ci sono N pastiglie» (dopo un conteggio o un acquisto). Il conto riparte e la richiesta di ricetta si azzera."""
    sc = med.setdefault("scorta", {})
    sc.update({"attiva": True, "avvio": oggi_.isoformat(), "pastiglie": round(float(pastiglie), 2), "rinnovo_richiesto": ""})
    sc.setdefault("storico", []).append({"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "testo": f"Da oggi {pastiglie:g} pastiglie" + (f" ({nota})" if nota else "")})
    sc["storico"] = sc["storico"][-30:]
    med["quantita"] = round(float(pastiglie), 2)                                         # la quantità mostrata nella scheda del medicinale riparte da qui


def scorta_descrivi_dose(med, terapie, pid):
    """Come si prende, a parole: «1 compressa alle 08:00 e alle 20:00»."""
    sc = med.get("scorta") or {}
    fr = scorta_descrivi_freq(sc.get("frequenza"))
    if fr:
        return fr
    man = _scorta_num(sc.get("per_giorno"))
    if man and man > 0:
        return f"{man:g} al giorno"
    parti = []
    for t in _scorta_terapie_di(terapie, pid, med.get("id")):
        if t.get("stato") in ("terminata",):
            continue
        orari = [o for o in (t.get("orari") or [])]
        if orari:
            quando_ = (" " + ter_giorni_testo(t)) if "ter_intervallo" in globals() and ter_intervallo(t) else ""        # terapia a intervalli: «1 flaconcino ogni 15 giorni alle 08:00»
            parti.append(f"{(t.get('quantita') or '').strip() or '1 dose'}{quando_} alle " + " e alle ".join(orari))
    return "; ".join(parti)


def scorta_giorni_it(g):
    return "oggi" if g == 0 else "domani" if g == 1 else f"tra {g} giorni" if g > 1 else ("ieri" if g == -1 else f"{-g} giorni fa")


# ---------------------------------------------------------------------------------------------------------------------
# LA BOZZA PER LA DOTTORESSA
# ---------------------------------------------------------------------------------------------------------------------
def scorta_testo_richiesta(paziente, medico, mio_nome, voci, cf=""):
    """La bozza di email (testo semplice). voci: [(nome completo, come si prende, ultimo giorno coperto o None)]. È una BOZZA: chi la manda la ricontrolla."""
    tipo = (medico or {}).get("tipo")
    saluto = "Gentile dottoressa" if tipo == "Dottoressa" else "Gentile dottore" if tipo == "Dottore" else "Gentile dottore/dottoressa"
    nome_m = ((medico or {}).get("nome") or "").strip()
    righe = [f"{saluto}" + (f" {nome_m}" if nome_m else "") + ",", "",
             f"sono {mio_nome}, mi occupo di {paziente}" + (f" (codice fiscale {cf})" if cf else "") + ".",
             "Le chiedo gentilmente la ricetta per i seguenti medicinali, che stanno per terminare:", ""]
    for nome, dose, ultima in voci:
        riga = f"• {nome}" + (f" — {dose}" if dose else "")
        if ultima:
            riga += f" — la scorta basta fino al {ultima.strftime('%d/%m/%Y')}"
        righe.append(riga)
    righe += ["", "La ringrazio e Le porgo cordiali saluti,", mio_nome]
    return "\n".join(righe)


# ---------------------------------------------------------------------------------------------------------------------
# AVVISI DENTRO L'APP (pulsante di Salute, Home)
# ---------------------------------------------------------------------------------------------------------------------
def scorta_in_esaurimento(f, oggi_=None):
    """[(nome persona, nome medicinale, giorni, stato)] per i medicinali che stanno per finire (o sono finiti) e per cui non si è ancora chiesta la ricetta."""
    oggi_ = oggi_ or oggi()
    out = []
    profili = {p.get("id"): p.get("nome", "") for p in (f.get("profili") or [])}
    for m in f.get("medicinali", []):
        r = scorta_calcola(m, f.get("terapie", []), m.get("profilo", "p0"), oggi_)
        if r["stato"] in ("in_esaurimento", "finito") and not r.get("richiesto"):
            out.append((profili.get(m.get("profilo", "p0"), ""), m.get("nome", ""), r["giorni"], r["stato"]))
    return sorted(out, key=lambda x: x[2])


# ---------------------------------------------------------------------------------------------------------------------
# INTERFACCIA
# ---------------------------------------------------------------------------------------------------------------------
_SCORTA_CSS = """<style>
.sco-card{background:rgba(255,255,255,.88);border-radius:18px;padding:12px 14px;margin:8px 0;border:1px solid rgba(0,0,0,.06);box-shadow:0 3px 10px rgba(0,0,0,.07)}
.sco-st{display:inline-block;border-radius:999px;padding:2px 10px;font-weight:800;font-size:.86rem;color:#fff}
.sco-barra{height:9px;border-radius:99px;background:rgba(0,0,0,.12);overflow:hidden;margin:6px 0}
.sco-barra span{display:block;height:100%}
</style>"""
_SCORTA_STATI = {"ok": ("🟢", "Scorta a posto", "#2e7d32"), "ok_lungo": ("🟢", "Basta fino alla fine della terapia", "#2e7d32"), "in_esaurimento": ("🟠", "Sta per finire", "#e65100"),
                 "finito": ("🔴", "Finito", "#b71c1c")}


def _scorta_salva_med(med_id, fn, msg):
    def _m(f):
        for m in f.get("medicinali", []):
            if m.get("id") == med_id:
                fn(m)
    _fa_salva(_m, msg)


def _scorta_dlg_imposta(f, pid, med):
    def _finestra():
        k = "scorta_im_" + med["id"]
        sc = med.get("scorta") or {}
        st.markdown(f"**{_sc_h.escape(med.get('nome', ''))}** {_sc_h.escape(med.get('dosaggio', ''))}")
        att = st.checkbox("Tieni il conto e avvisami quando stanno per finire", value=bool(sc.get("attiva", True)), key=k + "_att")
        avvio = st.date_input("Da quando comincia a prenderlo (data di avvio)", value=_scorta_data(sc.get("avvio")) or _scorta_data(med.get("acquisto")) or oggi(), key=k + "_av", format="DD/MM/YYYY")
        past = st.number_input("Quante pastiglie (o fiale, bustine…) ci sono nella scatola", min_value=0.0, step=1.0, value=float(_scorta_num(sc.get("pastiglie")) or _scorta_num(med.get("quantita")) or 30.0), key=k + "_pa")
        fr0 = scorta_freq_valida(sc.get("frequenza"))
        modi = ["Ogni giorno (o più volte al giorno)", "A intervalli: una volta ogni N giorni", "A intervalli: una volta ogni N settimane", "A intervalli: una volta ogni N mesi"]
        idx = {None: 0, "giorni": 1, "settimane": 2, "mesi": 3}[fr0["tipo"] if fr0 else None]
        modo = st.selectbox("Ogni quanto si prende", modi, index=idx, key=k + "_modo")
        tipo_f = {1: "giorni", 2: "settimane", 3: "mesi"}.get(modi.index(modo))
        pg, freq = "", None
        terapie = f.get("terapie", [])
        if tipo_f is None:
            rilev = _scorta_terapie_di(terapie, pid, med["id"])
            da_terapia = scorta_descrivi_dose(dict(med, scorta={}), terapie, pid)
            if rilev and da_terapia:
                st.success("Dal programma di terapia: " + da_terapia + ". Lo uso così, se sotto non scrivi niente.")
            elif rilev:
                st.warning("C'è una terapia ma non capisco la quantità: scrivi qui sotto quante pastiglie si prendono al giorno.")
            else:
                st.info("Non c'è ancora una terapia per questo medicinale: scrivi qui sotto quante pastiglie si prendono al giorno (oppure crea la terapia nella scheda Terapie). "
                        "Se si prende solo ogni tanto (una fiala ogni 15 giorni, una al mese…) scegli «A intervalli» qui sopra.")
            pg = st.text_input("Pastiglie al giorno (lascia vuoto per usare la terapia)", value=("" if sc.get("per_giorno") in (None, "") else f"{_scorta_num(sc.get('per_giorno')):g}".replace(".", ",")), key=k + "_pg",
                               placeholder="es. 2   oppure   0,5")
        else:
            st.info("**Esempio:** 4 fiale, una ogni 15 giorni → scegli «ogni N giorni», scrivi **15**, **1** per dose, e la **data della prima fiala**. Per «una al mese» scegli «ogni N mesi» con **1**.")
            etichetta = {"giorni": "giorni", "settimane": "settimane", "mesi": "mesi"}[tipo_f]
            ogni = st.number_input(f"Ogni quanti {etichetta}", min_value=1, max_value=365, step=1, value=int(fr0["ogni"]) if fr0 and fr0["tipo"] == tipo_f else (15 if tipo_f == "giorni" else 1), key=f"{k}_og_{tipo_f}")
            dose = st.number_input("Quante pastiglie (o fiale) a ogni volta", min_value=0.25, step=0.25, value=float(fr0["dose"]) if fr0 else 1.0, key=k + "_do")
            prima = st.date_input("Data della prima volta", value=(fr0 or {}).get("prima") or avvio, key=k + "_pr", format="DD/MM/YYYY")
            freq = {"tipo": tipo_f, "ogni": int(ogni), "dose": float(dose), "prima": prima.isoformat()}
        pre = st.selectbox("Avvisami quando mancano", SCORTA_PREAVVISI, index=SCORTA_PREAVVISI.index(int(_scorta_num(sc.get("preavviso")) or 7)) if int(_scorta_num(sc.get("preavviso")) or 7) in SCORTA_PREAVVISI else 2,
                           key=k + "_pre", format_func=lambda g: f"{g} giorni")
        if freq and past > 0:                                                              # anteprima: quante volte bastano e fino a quando
            prova = {"id": med["id"], "scorta": {"attiva": True, "avvio": avvio.isoformat(), "pastiglie": float(past), "frequenza": freq, "preavviso": int(pre)}}
            r_ = scorta_calcola(prova, [], pid, oggi())
            if r_.get("fino_al"):
                n_dosi = int(past // freq["dose"])
                st.success(f"Con queste impostazioni bastano per **{n_dosi} volte**. L'ultima è il **{r_['ultima'].strftime('%d/%m/%Y')}**; la scorta basta fino al **{r_['fino_al'].strftime('%d/%m/%Y')}**: "
                           "entro quel giorno serve una nuova scatola.")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva", key=k + "_ok", type="primary", width="stretch"):
            pgn = _scorta_num(pg) if str(pg).strip() else None
            if str(pg).strip() and (pgn is None or pgn <= 0):
                st.error("Le pastiglie al giorno devono essere un numero maggiore di zero (per esempio 2 oppure 0,5).")
                return
            if att and past <= 0:
                st.error("Scrivi quante pastiglie ci sono nella scatola.")
                return
            nuovo = {"attiva": bool(att), "avvio": avvio.isoformat(), "pastiglie": float(past), "per_giorno": None if freq else pgn, "preavviso": int(pre), "frequenza": freq}

            def _fn(m):
                sc_ = m.setdefault("scorta", {})
                cambiata = (sc_.get("avvio"), sc_.get("pastiglie")) != (nuovo["avvio"], nuovo["pastiglie"])
                sc_.update(nuovo)
                if freq is None:
                    sc_.pop("frequenza", None)
                if cambiata:
                    sc_["rinnovo_richiesto"] = ""
                    sc_.setdefault("storico", []).append({"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "testo": f"Impostata: {nuovo['pastiglie']:g} pastiglie dal {avvio.strftime('%d/%m/%Y')}"})
                    m["quantita"] = float(past)
            _scorta_salva_med(med["id"], _fn, "Salute: scorta di " + med.get("nome", "")[:30])
            st.session_state["fa_msg"] = "✅ Scorta salvata."
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("📦 Scorta del medicinale")(_finestra)()


def _scorta_dlg_conteggio(f, pid, med, r):
    def _finestra():
        k = "scorta_co_" + med["id"]
        st.markdown(f"**{_sc_h.escape(med.get('nome', ''))}**")
        st.caption(f"Secondo il calcolo ne restano circa **{(r.get('restano') or 0):g}**. Conta quelle che ci sono davvero e scrivile: da oggi il conto riparte da lì.")
        n = st.number_input("Quante pastiglie ci sono adesso", min_value=0.0, step=1.0, value=float(round(r.get("restano") or 0)), key=k + "_n")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva il conteggio", key=k + "_ok", type="primary", width="stretch"):
            _scorta_salva_med(med["id"], lambda m: scorta_nuova_base(m, n, oggi(), "contate"), "Salute: pastiglie contate")
            st.session_state["fa_msg"] = "✅ Conteggio salvato."
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("🔢 Ne ho contate…")(_finestra)()


def _scorta_dlg_acquisto(f, pid, med, r):
    def _finestra():
        k = "scorta_ac_" + med["id"]
        st.markdown(f"**{_sc_h.escape(med.get('nome', ''))}**")
        resto = r.get("restano") or 0
        st.caption(f"Ne restano circa **{resto:g}**: le pastiglie della nuova scatola si sommano e il conto riparte da oggi.")
        n = st.number_input("Quante pastiglie ci sono nella nuova scatola", min_value=1.0, step=1.0, value=float(_scorta_num((med.get("scorta") or {}).get("pastiglie")) or 30.0), key=k + "_n")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("💾 Salva l'acquisto", key=k + "_ok", type="primary", width="stretch"):
            _scorta_salva_med(med["id"], lambda m: scorta_nuova_base(m, resto + n, oggi(), f"{resto:g} rimaste + {n:g} nuove"), "Salute: nuova scatola")
            st.session_state["fa_msg"] = "✅ Nuova scatola registrata."
            st.rerun()
        if c2.button("Annulla", key=k + "_no", width="stretch"):
            st.rerun()
    st.dialog("🛒 Ho comprato altre pastiglie")(_finestra)()


def _scorta_scheda(f, pid, med, oggi_):
    terapie = f.get("terapie", [])
    r = scorta_calcola(med, terapie, pid, oggi_)
    nome = _sc_h.escape(med.get("nome", "") + (f" {med['dosaggio']}" if med.get("dosaggio") else ""))
    stato = r["stato"]
    if stato in _SCORTA_STATI:
        ic, et, col = _SCORTA_STATI[stato]
        riga = f"<span class='sco-st' style='background:{col}'>{ic} {et}</span>"
        det = [f"Ne restano circa <b>{(r['restano'] or 0):g}</b>"]
        fr = scorta_descrivi_freq((med.get("scorta") or {}).get("frequenza"))
        if r.get("fino_al"):
            det.append(f"bastano fino al <b>{r['fino_al'].strftime('%d/%m/%Y')}</b> ({scorta_giorni_it(r['giorni'])})" if stato != "finito" else f"sono finite {scorta_giorni_it(r['giorni'])}")
        if fr and r.get("ultima"):
            det.append(f"si prende {fr} · l'ultima volta coperta è il {r['ultima'].strftime('%d/%m/%Y')}")
        elif r["per_giorno"]:
            det.append(f"{r['per_giorno']:g} al giorno")
        if r.get("richiesto"):
            det.append(f"✅ ricetta chiesta il {r['richiesto'].strftime('%d/%m/%Y')}")
        sc = med.get("scorta") or {}
        tot = _scorta_num(sc.get("pastiglie")) or 0
        perc = int(100 * (r["restano"] or 0) / tot) if tot else 0
        barra = f"<div class='sco-barra'><span style='width:{min(100, max(0, perc))}%;background:{col}'></span></div>"
        corpo = " · ".join(det)
    else:
        riga = "<span class='sco-st' style='background:#757575'>⚪ Conto non attivo</span>" if stato == "spento" else "<span class='sco-st' style='background:#6d4c41'>🟤 Da completare</span>"
        barra = ""
        corpo = {"spento": "Non tengo il conto delle pastiglie di questo medicinale.",
                 "dati_mancanti": "Mancano la data di avvio o il numero di pastiglie.",
                 "senza_terapia": "Manca la terapia: scrivi quante pastiglie si prendono al giorno (⚙️ Cambia), oppure crea la terapia.",
                 "dose_non_capita": "Non capisco la quantità scritta nella terapia: scrivi tu quante pastiglie al giorno (⚙️ Cambia).",
                 "nessun_consumo": "Con la terapia di adesso non sono previste dosi: controlla giorni e orari."}.get(stato, "")
    st.markdown(f"<div class='sco-card'><div style='display:flex;justify-content:space-between;gap:8px;align-items:center'><b>💊 {nome}</b>{riga}</div>{barra}<div style='font-size:.93rem'>{corpo}</div></div>", unsafe_allow_html=True)
    attivo = stato != "spento"
    b1, b2, b3 = st.columns(3, gap="small")
    if b1.button("⚙️ Cambia" if attivo else "➕ Tieni il conto", key=f"scorta_b_im_{med['id']}", width="stretch", type="secondary" if attivo else "primary"):
        _scorta_dlg_imposta(f, pid, med)
    if attivo and stato in _SCORTA_STATI:
        if b2.button("🔢 Ne ho contate", key=f"scorta_b_co_{med['id']}", width="stretch"):
            _scorta_dlg_conteggio(f, pid, med, r)
        if b3.button("🛒 Ho comprato", key=f"scorta_b_ac_{med['id']}", width="stretch"):
            _scorta_dlg_acquisto(f, pid, med, r)
    return r


def _scorta_mio_nome(p):
    try:
        anag = carica_dati(crea_archivio(), st.session_state["percorso"]).get("anagrafica") or {}
        n = " ".join(x for x in (anag.get("nome"), anag.get("cognome")) if x)
    except Exception:
        n = ""
    return n or (st.session_state.get("sess") or {}).get("nome", "") or "un familiare"


def _scorta_rinnovo(f, p, pid, oggi_, meds, stati):
    st.markdown("#### ✉️ Rinnovo ricette: la bozza per la dottoressa")
    tracciati = [m for m in meds if stati[m["id"]]["stato"] in _SCORTA_STATI]
    if not tracciati:
        st.caption("Quando tieni il conto di almeno un medicinale, qui compare la lista di quelli che stanno per finire e la bozza della richiesta.")
        return
    da_chiedere = [m["id"] for m in tracciati if stati[m["id"]]["stato"] in ("in_esaurimento", "finito") and not stati[m["id"]].get("richiesto")]
    if not da_chiedere:
        st.success("Nessun medicinale sta per finire adesso (o la ricetta è già stata chiesta). Se vuoi prepararla lo stesso, scegli i medicinali qui sotto.")
    scelti = st.multiselect("Medicinali da includere nella richiesta", [m["id"] for m in tracciati], default=da_chiedere, key="scorta_scelti_" + pid,
                            format_func=lambda i: next((m.get("nome", "") + (f" {m['dosaggio']}" if m.get("dosaggio") else "") + (f" · {scorta_giorni_it(stati[i]['giorni'])}" if stati[i].get("giorni") is not None else "") for m in tracciati if m["id"] == i), i))
    if not scelti:
        st.info("Scegli almeno un medicinale per vedere la bozza.")
        return
    medico = p.get("dottore") or {}
    cf = _fa_cf_del_profilo(f, pid) if "_fa_cf_del_profilo" in globals() else ""
    usa_cf = st.checkbox("Scrivi anche il codice fiscale", value=bool(cf), key="scorta_cf_" + pid, disabled=not cf, help="Lo prendo dai documenti della persona (tessera sanitaria).") if cf else False
    voci = []
    for m in tracciati:
        if m["id"] in scelti:
            r = stati[m["id"]]
            voci.append((m.get("nome", "") + (f" {m['dosaggio']}" if m.get("dosaggio") else "") + (f" ({m['forma']})" if m.get("forma") else ""), scorta_descrivi_dose(m, f.get("terapie", []), pid), r.get("fino_al") or r.get("ultima")))
    mio = _scorta_mio_nome(p)
    bozza = scorta_testo_richiesta(p.get("nome", "la persona"), medico, mio, voci, cf if usa_cf else "")
    firma = hashlib.md5((bozza).encode("utf-8")).hexdigest()[:8]
    st.caption("Questa è una **bozza**: **leggila e correggila** prima di mandarla. Non parte niente da solo.")
    testo = st.text_area("Testo della richiesta", value=bozza, height=300, key=f"scorta_testo_{pid}_{firma}")
    email = st.text_input("Email della dottoressa", value=medico.get("email", ""), key="scorta_email_" + pid, placeholder="nome@esempio.it")
    oggetto = st.text_input("Oggetto", value=f"Richiesta ricette per {p.get('nome', '')}", key="scorta_ogg_" + pid)
    if not medico.get("email"):
        st.caption("Non c'è ancora l'email del medico: scrivila qui sopra, oppure aggiungila in **👩‍⚕️ Medici e riferimenti → scheda del medico di base**.")
    url = "mailto:" + urllib.parse.quote(email.strip(), safe="@") + "?subject=" + urllib.parse.quote(oggetto, safe="") + "&body=" + urllib.parse.quote(testo.replace("\n", "\r\n"), safe="")
    b1, b2 = st.columns(2, gap="small")
    if len(url) > 1900:
        b1.caption("Il testo è lungo: se la mail non si apre, copia il testo qui sotto.")
    if email.strip() and "@" in email:
        b1.link_button("✉️ Apri la mail (la controlli e la mandi tu)", url, width="stretch")
    else:
        b1.button("✉️ Apri la mail", key="scorta_mail_no", disabled=True, width="stretch")
    if b2.button("✅ Ho chiesto le ricette", key="scorta_chiesto_" + pid, width="stretch", help="Da quel momento non ti avviso più per questi medicinali, finché non registri una nuova scatola."):
        def _fn(m):
            if m.get("id") in scelti:
                m.setdefault("scorta", {})["rinnovo_richiesto"] = oggi_.isoformat()
        def _m(ff):
            for mm in ff.get("medicinali", []):
                _fn(mm)
        _fa_salva(_m, "Salute: ricette chieste")
        st.session_state["fa_msg"] = "✅ Segnato: non ti avviso più per questi medicinali finché non registri la nuova scatola."
        st.rerun()
    tel = medico.get("telefono", "")
    if tel and "_lv_wa" in globals() and _lv_wa(tel):
        st.link_button("💬 Oppure mandala su WhatsApp", "https://wa.me/" + _lv_wa(tel) + "?text=" + urllib.parse.quote(testo, safe=""), width="stretch")
    st.caption("Per copiare il testo tocca l'icona a destra:")
    st.code(testo, language=None)


def scorta_pagina(pid):
    f, p = _sp_intestazione("💊 Scorte e rinnovo ricette", pid)
    st.markdown(_SCORTA_CSS, unsafe_allow_html=True)
    oggi_ = oggi()
    st.caption("Per ogni medicinale scrivi **da quando comincia a prenderlo**, **quante pastiglie ci sono nella scatola** e quante se ne prendono al giorno (di solito le leggo dalla terapia). "
               "Io calcolo **quando finiscono**, ti avviso **prima** e preparo la richiesta per la dottoressa. È una stima: si corregge con «Ne ho contate» e «Ho comprato».")
    meds = [m for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid]
    if not meds:
        st.info("Questa persona non ha ancora medicinali. Aggiungili nella scheda **💊 Medicinali**, poi torna qui.")
        return
    stati = {}
    ordine = {"finito": 0, "in_esaurimento": 1, "ok": 2, "ok_lungo": 2, "senza_terapia": 3, "dose_non_capita": 3, "dati_mancanti": 3, "nessun_consumo": 3, "spento": 4}
    for m in sorted(meds, key=lambda x: (ordine.get(scorta_calcola(x, f.get("terapie", []), pid, oggi_)["stato"], 5), x.get("nome", "").lower())):
        stati[m["id"]] = _scorta_scheda(f, pid, m, oggi_)
    st.divider()
    _scorta_rinnovo(f, p, pid, oggi_, meds, stati)


def scorta_n_esaurimento(f, pid, oggi_=None):
    oggi_ = oggi_ or oggi()
    n = 0
    for m in f.get("medicinali", []):
        if m.get("profilo", "p0") == pid:
            r = scorta_calcola(m, f.get("terapie", []), pid, oggi_)
            n += 1 if (r["stato"] in ("in_esaurimento", "finito") and not r.get("richiesto")) else 0
    return n
