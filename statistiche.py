# -*- coding: utf-8 -*-
"""STATISTICHE SUGLI SPRECHI della dispensa (nuova scheda «Statistiche»).
Da quando c'è questo modulo l'app ricorda, nello «storico» della dispensa di ogni persona, tre cose:
  • consumato   un'unità consumata («Ne ho consumato uno») o un prodotto finito
  • sprecato    un prodotto eliminato perché scaduto o buttato (motivo scelto quando si elimina)
  • (l'eliminazione per errore di inserimento non conta: è una correzione)
La scheda mostra quanto si consuma e quanto si spreca, per sezione (adulti, neonati, animali), mese per mese, i prodotti più sprecati
e quelli che ora rischiano di scadere. I dati cominciano da quando si installa questo aggiornamento.
Caricato da app_dispensa.py dopo spesa.py; la scheda è agganciata a parte3.py."""
from collections import Counter
from datetime import date, datetime, timedelta

_STORICO_MAX = 4000
MOTIVI_ELIMINA = ["Era scaduto: l'ho buttato", "L'ho consumato / finito", "L'ho buttato (non era scaduto)", "Ho sbagliato a inserirlo"]
_TIPO_DA_MOTIVO = {MOTIVI_ELIMINA[0]: "sprecato", MOTIVI_ELIMINA[1]: "consumato", MOTIVI_ELIMINA[2]: "sprecato", MOTIVI_ELIMINA[3]: None}


def registra_evento(d, tipo, riga, quantita=None, motivo=""):
    """Aggiunge un evento allo storico (tipo: 'consumato' o 'sprecato'). Si usa DENTRO la funzione che modifica i dati (d = dati della dispensa)."""
    if tipo not in ("consumato", "sprecato"):
        return
    cat = riga.get("per_chi") if riga.get("per_chi") in ("adulti", "neonati", "animali") else "adulti"
    try:
        q = float(quantita if quantita is not None else (riga.get("quantita") or 1))
    except (TypeError, ValueError):
        q = 1.0
    storico = d.setdefault("storico", [])
    storico.append({"t": datetime.now().isoformat(timespec="seconds"), "tipo": tipo, "nome": str(riga.get("nome", ""))[:80],
                    "cat": cat, "q": max(q, 0), "scad": riga.get("scadenza") or None, "motivo": motivo})
    if len(storico) > _STORICO_MAX:
        del storico[:len(storico) - _STORICO_MAX]


def tipo_da_motivo(motivo):
    return _TIPO_DA_MOTIVO.get(motivo)


def _mese(iso):
    return iso[:7]


def statistiche_calcola(storico, articoli, oggi_, giorni=None):
    """Numeri per la scheda. giorni=None → da sempre. Ritorna un dizionario."""
    inizio = (oggi_ - timedelta(days=giorni)).isoformat() if giorni else ""
    eventi = [e for e in (storico or []) if e.get("t", "")[:10] >= inizio]
    cons = [e for e in eventi if e.get("tipo") == "consumato"]
    spre = [e for e in eventi if e.get("tipo") == "sprecato"]
    n_c, n_s = sum(e.get("q", 1) for e in cons), sum(e.get("q", 1) for e in spre)
    tot = n_c + n_s
    per_cat = {c: {"consumati": sum(e.get("q", 1) for e in cons if e.get("cat") == c), "sprecati": sum(e.get("q", 1) for e in spre if e.get("cat") == c)}
               for c in ("adulti", "neonati", "animali")}
    mesi = []
    ym = oggi_.year * 12 + oggi_.month - 1
    for k in range(5, -1, -1):                                    # gli ultimi 6 mesi, anche vuoti
        m = ym - k
        chiave = f"{m // 12}-{m % 12 + 1:02d}"
        mesi.append({"mese": chiave, "consumati": sum(e.get("q", 1) for e in cons if _mese(e.get("t", "")) == chiave),
                     "sprecati": sum(e.get("q", 1) for e in spre if _mese(e.get("t", "")) == chiave)})
    top = Counter()
    for e in spre:
        top[(e.get("nome") or "").strip().title()] += e.get("q", 1)
    a_rischio = []
    for r in articoli or []:
        s = r.get("scadenza")
        if not s:
            continue
        try:
            g = (date.fromisoformat(s) - oggi_).days
        except ValueError:
            continue
        if g <= 30:
            a_rischio.append({"nome": r.get("nome", ""), "giorni": g, "scadenza": s, "q": r.get("quantita")})
    a_rischio.sort(key=lambda x: x["giorni"])
    return {"consumati": n_c, "sprecati": n_s, "tasso": round(100 * n_s / tot) if tot else None, "per_cat": per_cat, "mesi": mesi,
            "top_sprecati": top.most_common(5), "a_rischio": a_rischio, "eventi": len(eventi), "da": (storico[0]["t"][:10] if storico else None)}


def statistiche_consigli(s):
    """Qualche suggerimento semplice dai numeri (niente di medico: solo organizzazione della spesa)."""
    c = []
    if s["tasso"] is not None and s["tasso"] >= 30:
        c.append("Butti via più di un prodotto su tre: prova a comprarne meno alla volta e a mettere davanti quelli che scadono prima.")
    if s["top_sprecati"]:
        nome, n = s["top_sprecati"][0]
        c.append(f"Il prodotto che sprechi di più è «{nome}»: la prossima volta prendine una confezione in meno.")
    scad = [x for x in s["a_rischio"] if x["giorni"] <= 7]
    if scad:
        c.append(f"{len(scad)} prodotto/i scadono entro una settimana: usali per primi.")
    if s["tasso"] == 0 and s["consumati"]:
        c.append("Ottimo: finora non hai sprecato niente di quello che hai registrato.")
    return c


def schermata_statistiche():
    """Il contenuto della scheda «Statistiche»."""
    dati = carica_dati(crea_archivio(), st.session_state["percorso"])
    storico, articoli = dati.get("storico", []), dati.get("articoli", [])
    st.markdown("### 📊 " + t("Statistiche e sprechi"))
    st.caption("Conto quanto consumi e quanto butti. I numeri partono da quando hai installato questo aggiornamento: più usi l'app, più diventano precisi.")
    periodo = st.radio("Periodo", ["30 giorni", "3 mesi", "12 mesi", "Da sempre"], horizontal=True, key="stat_periodo", label_visibility="collapsed")
    giorni = {"30 giorni": 30, "3 mesi": 92, "12 mesi": 365, "Da sempre": None}[periodo]
    s = statistiche_calcola(storico, articoli, oggi(), giorni)
    if not s["eventi"]:
        st.info("Non ho ancora niente da contare. Quando premi **«Ne ho consumato uno»**, oppure elimini un prodotto scegliendo **perché** lo togli "
                "(scaduto, consumato…), lo registro qui.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Consumati", f"{s['consumati']:g}")
        c2.metric("🗑️ Sprecati", f"{s['sprecati']:g}")
        c3.metric("📉 Spreco", f"{s['tasso']}%" if s["tasso"] is not None else "—")
        st.markdown("**Per sezione**")
        nomi = {"adulti": "🧑 Adulti", "neonati": "👶 Neonati", "animali": "🐾 Animali"}
        righe = [{"Sezione": nomi[k], "Consumati": v["consumati"], "Sprecati": v["sprecati"]} for k, v in s["per_cat"].items() if v["consumati"] or v["sprecati"]]
        if righe:
            st.dataframe(righe, hide_index=True, width="stretch")
        if any(m["consumati"] or m["sprecati"] for m in s["mesi"]):
            st.markdown("**Mese per mese**")
            st.bar_chart({"Mese": [m["mese"] for m in s["mesi"]], "Consumati": [m["consumati"] for m in s["mesi"]], "Sprecati": [m["sprecati"] for m in s["mesi"]]},
                         x="Mese", y=["Consumati", "Sprecati"], color=["#2e7d32", "#c62828"])
        if s["top_sprecati"]:
            st.markdown("**I prodotti che sprechi di più**")
            for nome, n in s["top_sprecati"]:
                st.markdown(f"- {nome or '(senza nome)'}: **{n:g}**")
        for frase in statistiche_consigli(s):
            st.info("💡 " + frase)
    if s["a_rischio"]:
        st.markdown("**⏳ Ora rischiano di scadere**")
        for x in s["a_rischio"][:12]:
            g = x["giorni"]
            st.markdown(f"- {'⚫ scaduto da ' + str(abs(g)) + ' giorni' if g < 0 else ('🔴 scade oggi' if g == 0 else ('🔴' if g <= 7 else '🟠') + f' scade tra {g} giorni')} · **{x['nome']}**")
