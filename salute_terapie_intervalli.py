# -*- coding: utf-8 -*-
"""SALUTE · TERAPIE A INTERVALLI: un medicinale da prendere ogni tanto (una fiala ogni 15 giorni, una al mese, ogni 3 mesi, ogni 2 settimane…).

PRIMA le terapie sapevano solo «quali giorni della settimana e a che ora». ORA nella finestra «Programma di terapia» c'è la scelta «Quando si prende»: nei giorni della settimana (come prima)
oppure «A intervalli»: ogni N giorni, settimane o mesi, a partire dalla DATA DELLA PRIMA VOLTA (che è il campo `inizio` della terapia). Il programma funziona come tutte le terapie:
• compare nei programmi del giorno e della settimana solo nei giorni giusti, con l'ORA scelta, e si segna «Ho preso»;
• i promemoria sul telefono arrivano all'ora giusta, e l'avviso «dose non registrata» vale solo in quei giorni;
• la SCORTA la legge da sola: «Scorte e rinnovo ricette» sa che si prende «1 ogni 15 giorni» e dice fino a quando bastano i flaconcini (stesso calcolo di prima, non si inserisce due volte).

DATI: `terapia.intervallo = {tipo: giorni|settimane|mesi, ogni: N}`; la prima volta è `terapia.inizio`; `terapia.giorni` resta vuoto (così, se per qualunque motivo la regola non fosse caricata,
non scatta nessun falso promemoria ogni giorno). Le terapie di prima non cambiano (`intervallo` assente = giorni della settimana)."""
import calendar as _ti_cal
from datetime import date, timedelta

import streamlit as st


def _ti_data(iso):
    try:
        return date.fromisoformat(str(iso)[:10]) if iso else None
    except ValueError:
        return None


def ter_intervallo(t):
    """{tipo, ogni} se la terapia è «a intervalli» ed è scritta bene, altrimenti None (cioè: giorni della settimana)."""
    iv = t.get("intervallo") if isinstance(t, dict) else None
    if not isinstance(iv, dict) or iv.get("tipo") not in ("giorni", "settimane", "mesi"):
        return None
    try:
        ogni = int(float(str(iv.get("ogni")).replace(",", ".")))
    except (TypeError, ValueError):
        return None
    return {"tipo": iv["tipo"], "ogni": ogni} if ogni >= 1 else None


def _ti_aggiungi_mesi(d, n):
    m = d.month - 1 + n
    a, m = d.year + m // 12, m % 12 + 1
    return date(a, m, min(d.day, _ti_cal.monthrange(a, m)[1]))


def terapia_e_giorno(t, d):
    """La terapia prevede una assunzione nel giorno `d`? (non guarda inizio/fine/stato: quelli si controllano a parte)"""
    iv = ter_intervallo(t)
    if iv is None:
        return d.weekday() in (t.get("giorni") or [])
    prima = _ti_data(t.get("inizio"))
    if prima is None or d < prima:
        return False
    if iv["tipo"] == "giorni":
        return (d - prima).days % iv["ogni"] == 0
    if iv["tipo"] == "settimane":
        return (d - prima).days % (7 * iv["ogni"]) == 0
    m = (d.year - prima.year) * 12 + d.month - prima.month
    return m % iv["ogni"] == 0 and d == _ti_aggiungi_mesi(prima, m)


def ter_giorni_testo(t, vuoto=""):
    """«ogni 15 giorni» / «ogni settimana» / «ogni 3 mesi» per le terapie a intervalli; «Lun, Mer, Ven» per le altre."""
    iv = ter_intervallo(t)
    if iv is None:
        nomi = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        return ", ".join(nomi[g] for g in (t.get("giorni") or []) if isinstance(g, int) and 0 <= g < 7) or vuoto
    unita = {"giorni": ("giorno", "giorni"), "settimane": ("settimana", "settimane"), "mesi": ("mese", "mesi")}[iv["tipo"]]
    return f"ogni {unita[0]}" if iv["ogni"] == 1 else f"ogni {iv['ogni']} {unita[1]}"


def ter_prossime(t, da, n=5):
    """Le prossime `n` date di assunzione a partire da `da` (comprese), fino alla data di fine se c'è."""
    fine = _ti_data(t.get("fine"))
    out, d = [], da
    for _ in range(2000):
        if len(out) >= n or (fine and d > fine):
            break
        if terapia_e_giorno(t, d):
            out.append(d)
        d += timedelta(days=1)
    return out


@st.dialog("Programma di terapia")
def _fa_dialogo_terapia(pid, ter_id=None):                                                  # noqa: F811
    """La finestra di prima, con in più «Quando si prende»: giorni della settimana oppure a intervalli (ogni N giorni, settimane o mesi)."""
    f = _fa_dati()
    meds = [m for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid]
    ter = next((x for x in f.get("terapie", []) if x["id"] == ter_id), {}) if ter_id else {}
    if not meds and not ter:
        st.info("Prima aggiungi almeno un medicinale a questo profilo (scheda 💊 Medicinali).")
        return
    ids = [m["id"] for m in meds]
    etich = {m["id"]: m["nome"] + (f" {m['dosaggio']}" if m.get("dosaggio") else "") for m in meds}
    if ter.get("med") and ter["med"] not in ids:
        ids.insert(0, ter["med"])
        etich[ter["med"]] = ter.get("nome_med", "(medicinale eliminato)")
    k = "ti_" + (ter_id or "nuova")
    iv0 = ter_intervallo(ter)
    modi = ["📅 Nei giorni della settimana", "🔁 A intervalli (ogni 15 giorni, ogni mese…)"]
    modo = st.radio("Quando si prende", modi, index=1 if iv0 else 0, key=k + "_modo")
    a_intervalli = modo == modi[1]
    tipo_i = ogni_i = prima_i = None
    if a_intervalli:
        tipi = ["giorni", "settimane", "mesi"]
        c1, c2 = st.columns(2, gap="small")
        tipo_i = c1.selectbox("Ogni", tipi, index=tipi.index(iv0["tipo"]) if iv0 else 0, key=k + "_tipo")
        ogni_i = c2.number_input("Quanti", min_value=1, max_value=365, step=1, value=int(iv0["ogni"]) if iv0 else 15, key=k + "_ogni")
        prima_i = st.date_input("Data della prima volta", value=_fa_data(ter.get("inizio")) or oggi(), format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31), key=k + "_prima")
        st.info("**Esempio:** 4 flaconcini da prendere uno ogni 15 giorni → **Ogni: giorni**, **Quanti: 15**, **Data della prima volta**: il giorno del primo flaconcino, "
                "**Quantità**: «1 flaconcino da 2,5 ml». Per «uno al mese» scegli **mesi** e **1**.")
        prossime = ter_prossime({"intervallo": {"tipo": tipo_i, "ogni": int(ogni_i)}, "inizio": prima_i.isoformat()}, prima_i, 5)
        if prossime:
            st.success("Le prime volte: " + " · ".join(d.strftime("%d/%m/%Y") for d in prossime))
    with st.form("fa_form_ter"):
        med = st.selectbox("Medicinale", ids, format_func=lambda i: etich[i], index=_fa_idx(ids, ter.get("med")))
        quantita = st.text_input("Quantità per ogni assunzione, come scritto nella prescrizione", value=ter.get("quantita", ""), placeholder="es. 1 compressa" if not a_intervalli else "es. 1 flaconcino da 2,5 ml")
        giorni = []
        if not a_intervalli:
            giorni = st.multiselect("Giorni della settimana", list(range(7)), default=ter.get("giorni", list(range(7))) if not iv0 else list(range(7)), format_func=lambda i: GIORNI_SETT[i])
        orari = st.multiselect("Orari (puoi sceglierne più di uno)" if not a_intervalli else "A che ora (il promemoria arriva a quest'ora)", ORARI_TER, default=[o for o in ter.get("orari", []) if o in ORARI_TER])
        if a_intervalli:
            fine = st.date_input("Fine (facoltativa)", value=_fa_data(ter.get("fine")), format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
            inizio = prima_i
        else:
            c1, c2 = st.columns(2)
            inizio = c1.date_input("Inizio", value=_fa_data(ter.get("inizio")) or oggi(), format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
            fine = c2.date_input("Fine (facoltativa)", value=_fa_data(ter.get("fine")), format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
        note = st.text_area("Istruzioni o note della prescrizione", value=ter.get("note", ""))
        stato = st.selectbox("Stato", list(STATI_TER), format_func=lambda k_: STATI_TER[k_], index=_fa_idx(list(STATI_TER), ter.get("stato", "attiva")))
        inviato = st.form_submit_button("Salva", type="primary")
    if inviato:
        if (not a_intervalli and not giorni) or not orari:
            st.error("Scegli almeno un giorno e almeno un orario." if not a_intervalli else "Scegli almeno un orario.")
            return
        if fine and fine < inizio:
            st.error("La data di fine non può essere prima di quella di inizio." if not a_intervalli else "La data di fine non può essere prima della data della prima volta.")
            return
        rec = {"profilo": pid, "med": med, "nome_med": etich[med], "quantita": quantita.strip(), "giorni": sorted(giorni) if not a_intervalli else [], "orari": sorted(orari), "inizio": inizio.isoformat(),
               "fine": fine.isoformat() if fine else None, "note": note.strip(), "stato": stato, "intervallo": {"tipo": tipo_i, "ogni": int(ogni_i)} if a_intervalli else None}
        if stato != ter.get("stato", "attiva"):                                             # sospesa o terminata da oggi: lo storico resta
            rec["stato_dal"] = oggi().isoformat()
            if stato == "terminata" and (not fine or fine > oggi()):
                rec["fine"] = oggi().isoformat()
        else:
            rec["stato_dal"] = ter.get("stato_dal")

        def _scrivi(f):
            f.setdefault("terapie", [])
            if ter_id:
                for x in f["terapie"]:
                    if x["id"] == ter_id:
                        x.update(rec)
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                f["terapie"].append(rec)
        try:
            _fa_salva(_scrivi, "Salute: terapia")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Programma salvato."
        st.rerun()
