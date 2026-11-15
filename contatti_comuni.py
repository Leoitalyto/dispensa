# -*- coding: utf-8 -*-
"""Pezzi COMUNI a tutti i «badge» dei contatti (amministratore, casa, lavoro, medici…): una sola logica in tutta l'app.
  • cc_url(testo)           → indirizzo del sito pronto da aprire («idamministrazioni.it» diventa «https://idamministrazioni.it»)
  • cc_campo_sito(...)      → il campo «🌐 Sito web» da mettere in ogni modulo
  • cc_chiama(col, ...)     → il tasto «📞 Chiama»: se ci sono DUE numeri (fisso e cellulare) apre una scelta, se ce n'è uno chiama subito
  • cc_sito_pulsante(...)   → il tasto «🌐 Sito»
  • cc_riga_sito(url)       → la riga col sito dentro la scheda, cliccabile
Prefisso: cc_ . Nessuna chiave, nessun servizio esterno."""
import html as _cc_html
import re as _cc_re
import streamlit as st


def cc_cifre(n):
    """Solo cifre (e un + iniziale): quello che serve al telefono per comporre."""
    n = str(n or "").strip()
    return ("+" if n.startswith("+") else "") + _cc_re.sub(r"\D", "", n)


def cc_e_cellulare(n):
    """Italia: i cellulari iniziano con 3 (anche dopo +39 / 0039)."""
    d = _cc_re.sub(r"\D", "", str(n or ""))
    if d.startswith("0039"):
        d = d[4:]
    elif d.startswith("39") and len(d) > 10:
        d = d[2:]
    return d.startswith("3")


def cc_url(testo):
    """Rende pronto un sito scritto a mano. Vuoto o non valido → ''."""
    t = str(testo or "").strip()
    if not t or " " in t:
        return ""
    if _cc_re.match(r"^https?://\S+\.\S+", t, _cc_re.I):
        return t
    if _cc_re.match(r"^(www\.)?[\w-]+(\.[\w-]+)+(/\S*)?$", t, _cc_re.I):
        return "https://" + t
    return ""


def cc_campo_sito(valore="", chiave=None, etichetta="🌐 Sito web (facoltativo)"):
    """Il campo del sito, uguale in tutti i moduli."""
    return st.text_input(etichetta, value=valore or "", key=chiave, placeholder="es. www.nomesito.it",
                         help="Se lo scrivi, nella scheda compare il tasto «🌐 Sito» per aprirlo subito.")


def cc_riga_sito(sito):
    """Riga HTML col sito cliccabile (per le schede disegnate con st.markdown)."""
    u = cc_url(sito)
    if not u:
        return ""
    return f"🌐 <a href='{_cc_html.escape(u)}' target='_blank' rel='noopener'>{_cc_html.escape(str(sito).strip())}</a>"


def cc_sito_pulsante(col, sito, chiave, etichetta="🌐 Sito"):
    u = cc_url(sito)
    if u:
        col.link_button(etichetta, u, width="stretch", key=chiave)
        return True
    return False


def cc_numeri(fisso, cellulare):
    """Elenco dei numeri diversi: [(etichetta, numero scritto, numero per comporre)]."""
    voci, visti = [], set()
    for n in (fisso, cellulare):
        c = cc_cifre(n)
        if c and len(c.lstrip("+")) >= 3 and c not in visti:
            visti.add(c)
            voci.append(("📱 Cellulare" if cc_e_cellulare(n) else "☎️ Telefono fisso", str(n).strip(), c))
    return voci


def cc_chiama(col, chiave, fisso, cellulare=None, etichetta="📞 Chiama", chi=""):
    """Un solo numero → chiama subito. Due numeri → toccando «Chiama» si apre la scelta: telefono fisso o cellulare."""
    voci = cc_numeri(fisso, cellulare)
    if not voci:
        return False
    if len(voci) == 1:
        col.link_button(etichetta, "tel:" + voci[0][2], width="stretch", key=f"{chiave}_ch")
        return True
    with col.popover(etichetta, width="stretch"):
        st.markdown("**Quale numero chiami?**" + (f"  \n{_cc_html.escape(chi)}" if chi else ""))
        for i, (et, num, comp) in enumerate(voci):
            st.link_button(f"{et} · {num}", "tel:" + comp, width="stretch", key=f"{chiave}_ch{i}")
    return True


def cc_pulsanti(pulsanti, chiave, per_riga=3):
    """Disegna una fila di tasti. Ogni voce è (scritta, indirizzo) oppure (scritta, ("__chiama__", fisso, cellulare, chi))."""
    for i in range(0, len(pulsanti), per_riga):
        gruppo = pulsanti[i:i + per_riga]
        for j, (col, (et, url)) in enumerate(zip(st.columns(per_riga if len(gruppo) == per_riga else len(gruppo), gap="small"), gruppo)):
            if isinstance(url, tuple) and url and url[0] == "__chiama__":
                cc_chiama(col, f"{chiave}_{i + j}", url[1], url[2], et, url[3] if len(url) > 3 else "")
            else:
                col.link_button(et, url, width="stretch", key=f"{chiave}_{i + j}_b")


# ---------------------------------------------------------------------------------------------------------------------
# 🕒 GIORNI E ORARI: la STESSA tabella del medico (Giorno · Dalle · Alle · Note), per ogni badge che ha un ufficio o uno studio
# ---------------------------------------------------------------------------------------------------------------------
def _cc_giorni():
    return globals().get("GIORNI_SETT") or ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]


def cc_fasce_pulite(fasce):
    g = _cc_giorni()
    return sorted([dict(x) for x in (fasce or []) if isinstance(x, dict) and x.get("g") in g], key=lambda x: (g.index(x["g"]), x.get("da", "")))


def cc_fasce_editor(fasce, chiave, note_pred=("Aperto", "Su appuntamento", "Solo telefono")):
    """La tabella da compilare (menu a tendina): ritorna la tabella modificata."""
    import pandas as pd
    giorni = _cc_giorni()
    orari = globals().get("ORARI_STUDIO") or [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in (0, 15, 30, 45)]
    att = cc_fasce_pulite(fasce) or [{"g": x, "da": "", "a": "", "nota": ""} for x in giorni[:5]]
    extra = {v for f in att for v in (f.get("da"), f.get("a")) if v}
    opz = ["—"] + sorted(set(orari) | extra)
    note = ["—"] + list(note_pred) + sorted({f.get("nota") for f in att if f.get("nota")} - set(note_pred))
    df = pd.DataFrame([{"Giorno": f["g"], "Dalle": f.get("da") or "—", "Alle": f.get("a") or "—", "Note": f.get("nota") or "—"} for f in att])
    return st.data_editor(df, hide_index=True, num_rows="dynamic", key=chiave, width="stretch",
                          column_config={"Giorno": st.column_config.SelectboxColumn("Giorno", options=giorni, width="small"),
                                         "Dalle": st.column_config.SelectboxColumn("Dalle", options=opz, width="small"),
                                         "Alle": st.column_config.SelectboxColumn("Alle", options=opz, width="small"),
                                         "Note": st.column_config.SelectboxColumn("Note", options=note, width="medium")})


def cc_fasce_da_tabella(mod):
    """Dalla tabella compilata alle fasce da salvare. Ritorna (fasce, errori)."""
    import pandas as pd
    giorni = _cc_giorni()
    fasce, errori = [], []
    for _, r in mod.iterrows():
        g = r.get("Giorno")
        if g not in giorni:
            continue
        vuoto = lambda v: v is None or pd.isna(v) or str(v) in ("—", "")
        da = "" if vuoto(r["Dalle"]) else str(r["Dalle"])
        a = "" if vuoto(r["Alle"]) else str(r["Alle"])
        nota = "" if vuoto(r["Note"]) else str(r["Note"])
        if not da and not a:
            continue
        if bool(da) != bool(a):
            errori.append(f"{g}: scegli sia «Dalle» sia «Alle».")
        elif a <= da:
            errori.append(f"{g}: «Alle» deve essere dopo «Dalle».")
        else:
            fasce.append({"g": g, "da": da, "a": a, "nota": nota})
    return cc_fasce_pulite(fasce), errori


def cc_fasce_mostra(fasce, chi="L'ufficio"):
    """La riga «Oggi…» e la tabella degli orari, con il giorno di oggi evidenziato (come nella scheda del medico)."""
    fasce = cc_fasce_pulite(fasce)
    if not fasce:
        return
    giorni = _cc_giorni()
    try:
        g_oggi = giorni[(globals().get("oggi") or __import__("datetime").date.today)().weekday()]
    except Exception:
        g_oggi = ""
    oggi_f = [x for x in fasce if x["g"] == g_oggi]
    if oggi_f:
        st.info(f"🕘 Oggi ({g_oggi}) {chi.lower()} è aperto: " + " · ".join(f"{x['da']}–{x['a']}" + (f" ({x['nota']})" if x.get("nota") else "") for x in oggi_f))
    else:
        st.caption(f"Oggi ({g_oggi}) non è indicato nessun orario di apertura.")
    celle = ""
    for x in fasce:
        ev = "background:#c8e6c9;font-weight:800;" if x["g"] == g_oggi else ""
        celle += f"<tr style='{ev}'><td style='padding:5px 8px'>{x['g']}</td><td>{_cc_html.escape(x['da'])}</td><td>{_cc_html.escape(x['a'])}</td><td>{_cc_html.escape(x.get('nota') or '')}</td></tr>"
    st.markdown("<table style='width:100%;border-collapse:collapse;font-size:.9rem;color:#1b2b2b;background:rgba(255,255,255,.78);border-radius:12px;overflow:hidden'>"
                "<tr style='background:rgba(0,0,0,.06)'><th style='text-align:left;padding:5px 8px'>Giorno</th><th style='text-align:left'>Dalle</th><th style='text-align:left'>Alle</th><th style='text-align:left'>Note</th></tr>"
                + celle + "</table>", unsafe_allow_html=True)


def cc_fasce_testo(fasce):
    """Gli orari in una riga di testo (per «Invia»): «Lun 09:00–12:00; Mar 09:00–12:00 (su appuntamento)»."""
    return "; ".join(f"{x['g']} {x['da']}–{x['a']}" + (f" ({x['nota']})" if x.get("nota") else "") for x in cc_fasce_pulite(fasce))
