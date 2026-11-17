# -*- coding: utf-8 -*-
"""📞 Numeri utili (un bottone in ogni sezione tranne Dispensa): la rubrica di chi serve in quella sezione.
Per ogni voce: nominativo, referente, mestiere/funzione, ambito, telefono (ufficio/cellulare), orari, sito, e-mail, indirizzo,
PREVENTIVO (importo, stato, PDF/foto, data inizio e fine lavori), DOCUMENTI ricevuti, PAGAMENTI (acconti, rate, saldo) e note.
I dati stanno in d["numeri_utili"][sezione] (una lista di voci con id). I file in documenti/<uid>/<id>.json (come i documenti)."""
import datetime as _rb_dt

import streamlit as st

RBU_MESTIERI = {
    "casa": ["Idraulico", "Elettricista", "Muratore", "Imbianchino", "Fabbro", "Falegname", "Giardiniere", "Caldaista / gas", "Serramentista", "Piastrellista",
             "Condizionatori", "Pulizie", "Amministratore di condominio", "Geometra / architetto", "Agenzia immobiliare", "Emergenze"],
    "salute": ["Medico di base", "Specialista", "Dentista", "Farmacia", "Infermiere", "Fisioterapista", "Ospedale / CUP", "Guardia medica", "Laboratorio analisi", "Emergenze"],
    "documenti": ["Commercialista", "Avvocato", "Notaio", "CAF / patronato", "Comune / anagrafe", "Banca", "Assicurazione", "Poste", "Emergenze"],
    "archivio": ["Commercialista", "Avvocato", "Notaio", "CAF / patronato", "Comune / anagrafe", "Banca", "Assicurazione"],
    "lavoro": ["Datore di lavoro", "Responsabile", "Collega", "Sindacato", "Consulente del lavoro", "Patronato", "Ufficio del personale"],
    "auto": ["Meccanico", "Gommista", "Carrozziere", "Elettrauto", "Soccorso stradale", "Assicurazione", "Centro revisioni", "Concessionario"],
    "animali": ["Veterinario", "Pronto soccorso veterinario", "Pensione", "Toelettatore", "Addestratore"],
    "utilita": ["Pronto intervento", "Banca", "Assicurazione", "Luce / gas", "Telefonia / internet", "Comune"],
}
RBU_STATI = ["Da chiedere", "Richiesto", "Ricevuto", "Accettato", "Lavori in corso", "Concluso", "Rifiutato"]
RBU_TIPI_PAG = ["Acconto", "Rata", "Saldo", "Altro"]
RBU_ALTRO = "✍️ Altro (lo scrivo io)"
RBU_FILE = ["pdf", "jpg", "jpeg", "png", "webp", "doc", "docx", "xls", "xlsx", "odt", "txt"]


def _rbu_voci(d, sez):
    return list((d.get("numeri_utili") or {}).get(sez, []))


def rbu_conta(d, sez):
    return len(_rbu_voci(d, sez))


def _rbu_salva_voce(sez, rec):
    def _m(d):
        lst = d.setdefault("numeri_utili", {}).setdefault(sez, [])
        for i, x in enumerate(lst):
            if x.get("id") == rec["id"]:
                lst[i] = rec
                break
        else:
            lst.append(rec)
    sc_salva(_m, "Numeri utili: " + str(rec.get("nome", "")))


def _rbu_elimina(sez, voce):
    sc_salva(lambda d: d.setdefault("numeri_utili", {}).__setitem__(sez, [x for x in d["numeri_utili"].get(sez, []) if x.get("id") != voce["id"]]),
             "Numeri utili: eliminato " + str(voce.get("nome", "")))
    cp_file_cancella(list(voce.get("preventivo_files") or []) + list(voce.get("documenti") or []))


def _rbu_totali(v):
    pag = [p for p in v.get("pagamenti") or [] if isinstance(p, dict)]
    pagato = sum(float(p.get("importo") or 0) for p in pag if p.get("pagato"))
    da_pagare = sum(float(p.get("importo") or 0) for p in pag if not p.get("pagato"))
    return pagato, da_pagare


def _rbu_card_html(v, oggi):
    e = sc_esc
    righe = []
    if v.get("mestiere"):
        righe.append(f"<span class='rbu-tag'>{e(v['mestiere'])}</span>")
    if v.get("ambito"):
        righe.append(f"<span class='rbu-tag rbu-tag2'>{e(v['ambito'])}</span>")
    testa = "".join(righe)
    rr = []
    if v.get("referente"):
        rr.append(f"👤 {e(v['referente'])}")
    if v.get("telefono"):
        rr.append(f"📞 {e(v['telefono'])}")
    if v.get("cellulare"):
        rr.append(f"📱 {e(v['cellulare'])}")
    if v.get("email"):
        rr.append(f"✉️ {e(v['email'])}")
    if v.get("indirizzo"):
        rr.append(f"📍 {e(v['indirizzo'])}")
    if v.get("sito") and cc_url(v["sito"]):
        rr.append(f"🌐 <a href='{e(cc_url(v['sito']))}' target='_blank' rel='noopener'>{e(v['sito'])}</a>")
    if v.get("orari"):
        rr.append("🕒 " + e(v["orari"]).replace("\n", " · "))
    extra = ""
    if v.get("ha_preventivo"):
        ini, fin = sc_data(v.get("lavori_inizio")), sc_data(v.get("lavori_fine"))
        parti = [f"🧾 <b>{e(v.get('stato') or 'Preventivo')}</b>"]
        if v.get("importo"):
            parti.append(sc_euro(v["importo"]))
        if ini or fin:
            parti.append("lavori " + (sc_data_scritta(ini, False) if ini else "?") + " → " + (sc_data_scritta(fin, False) if fin else "?"))
        pagato, da_pagare = _rbu_totali(v)
        if pagato or da_pagare:
            parti.append(f"pagato {sc_euro(pagato)} · da pagare {sc_euro(da_pagare)}")
        extra = "<div class='rbu-prev'>" + " · ".join(parti) + "</div>"
    if v.get("note"):
        rr.append(f"<i>{e(v['note'])}</i>")
    return (f"<div class='rbu-card'><b class='rbu-nome'>{e(v.get('nome', '—'))}</b><div>{testa}</div>"
            + ("<div class='rbu-righe'>" + "<br>".join(rr) + "</div>" if rr else "") + extra + "</div>")


RBU_CSS = """<style>
.rbu-card{margin:12px 0 4px;padding:11px 12px;border-radius:16px;border:1px solid rgba(110,200,255,.5);background:linear-gradient(160deg,#0f1b33,#0a1120);
 box-shadow:0 0 10px rgba(80,170,255,.25);color:#e9eefb}
.rbu-nome{font-size:1.08rem;color:#fff;word-break:break-word}
.rbu-tag{display:inline-block;margin:4px 6px 0 0;padding:1px 9px;border-radius:999px;border:1px solid #20e6ff;color:#8ff3ff;font-size:.75rem;font-weight:700}
.rbu-tag2{border-color:#ffb74d;color:#ffd699}
.rbu-righe{margin-top:6px;font-size:.88rem;line-height:1.45;word-break:break-word}.rbu-righe a{color:#8ff3ff}
.rbu-prev{margin-top:8px;padding:6px 9px;border-radius:10px;background:rgba(255,183,77,.13);border:1px solid rgba(255,183,77,.5);font-size:.85rem}
</style>"""


def _rbu_data_opz(k, etichetta, attuale):
    """Data facoltativa: un segno di spunta e poi la data."""
    ha = st.checkbox(etichetta, value=bool(attuale), key=k + "_ha")
    if not ha:
        return None
    return st.date_input(etichetta, value=attuale or _rb_dt.date.today(), format="DD/MM/YYYY", key=k + "_d", label_visibility="collapsed")


def _rbu_modulo(sez, voce):
    k = "rbu_f_" + sez + "_" + (voce.get("id") or "nuovo")
    mest = RBU_MESTIERI.get(sez, []) + [RBU_ALTRO]
    with st.container(border=True, key=k + "_box"):
        st.markdown("**" + ("✏️ Modifica" if voce.get("id") else "➕ Nuovo numero utile") + "**")
        # 1) chi è
        st.markdown("<b>1 · Chi è</b>", unsafe_allow_html=True)
        nome = st.text_input("Nominativo o ditta *", value=voce.get("nome", ""), key=k + "_nome")
        referente = st.text_input("Persona di riferimento", value=voce.get("referente", ""), key=k + "_ref")
        att = voce.get("mestiere", "")
        idx = mest.index(att) if att in mest else (len(mest) - 1 if att else None)
        scelta = st.selectbox("Mestiere / funzione", mest, index=idx, placeholder="Scegli…", key=k + "_mes")
        mestiere = st.text_input("Scrivi il mestiere o la funzione", value=(att if att not in mest else ""), key=k + "_mes2") if scelta == RBU_ALTRO else (scelta or "")
        ambito = st.text_input("Ambito (per cosa lo chiamo)", value=voce.get("ambito", ""), key=k + "_amb", placeholder="es. perdite d'acqua, impianto elettrico, urgenze")
        # 2) come si contatta
        st.markdown("<b>2 · Come lo trovo</b>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        tel = c1.text_input("📞 Telefono ufficio", value=voce.get("telefono", ""), key=k + "_tel")
        cel = c2.text_input("📱 Cellulare", value=voce.get("cellulare", ""), key=k + "_cel")
        email = st.text_input("✉️ Email", value=voce.get("email", ""), key=k + "_mail")
        sito = cc_campo_sito(voce.get("sito", ""), k + "_sito")
        indirizzo = st.text_input("📍 Indirizzo", value=voce.get("indirizzo", ""), key=k + "_ind")
        orari = st.text_area("🕒 Orari (es. lun-ven 8-12 e 15-18; sabato 8-12)", value=voce.get("orari", ""), key=k + "_ora", height=80)
        # 3) preventivo
        st.markdown("<b>3 · Preventivo e lavori</b>", unsafe_allow_html=True)
        ha_prev = st.checkbox("C'è un preventivo o un lavoro da seguire", value=bool(voce.get("ha_preventivo")), key=k + "_hp")
        stato, importo, descr, ini, fin, prev_files, nuovi_prev, togli_prev = voce.get("stato", ""), voce.get("importo", 0.0), voce.get("descrizione", ""), None, None, list(voce.get("preventivo_files") or []), [], []
        if ha_prev:
            stato = st.selectbox("Stato", RBU_STATI, index=RBU_STATI.index(voce["stato"]) if voce.get("stato") in RBU_STATI else 0, key=k + "_st")
            importo = st.number_input("Importo del preventivo (€)", min_value=0.0, value=float(voce.get("importo") or 0.0), step=10.0, format="%.2f", key=k + "_imp")
            descr = st.text_area("Che lavoro è (descrizione)", value=voce.get("descrizione", ""), key=k + "_desc", height=80)
            ini = _rbu_data_opz(k + "_ini", "Data di inizio lavori", sc_data(voce.get("lavori_inizio")))
            fin = _rbu_data_opz(k + "_fin", "Data di fine lavori", sc_data(voce.get("lavori_fine")))
            for i, r in enumerate(prev_files):
                if st.checkbox(f"🗑️ Togli «{r.get('nome', 'file')}»", key=f"{k}_tp{i}"):
                    togli_prev.append(r)
            nuovi_prev = ar_uploader("📎 Preventivo (PDF o foto)", type=RBU_FILE, accept_multiple_files=True, key=k + "_up_p") if "ar_uploader" in globals() \
                else st.file_uploader("📎 Preventivo (PDF o foto)", type=RBU_FILE, accept_multiple_files=True, key=k + "_up_p")
        # 4) documenti
        st.markdown("<b>4 · Documenti ricevuti</b>", unsafe_allow_html=True)
        docs, togli_doc = list(voce.get("documenti") or []), []
        for i, r in enumerate(docs):
            if st.checkbox(f"🗑️ Togli «{r.get('nome', 'file')}»", key=f"{k}_td{i}"):
                togli_doc.append(r)
        nuovi_doc = ar_uploader("📎 Aggiungi documenti (PDF, foto, fatture, contratti…)", type=RBU_FILE, accept_multiple_files=True, key=k + "_up_d") if "ar_uploader" in globals() \
            else st.file_uploader("📎 Aggiungi documenti", type=RBU_FILE, accept_multiple_files=True, key=k + "_up_d")
        # 5) note
        st.markdown("<b>5 · Note</b>", unsafe_allow_html=True)
        note = st.text_area("📝 Note", value=voce.get("note", ""), key=k + "_note", height=100)
        st.caption("💶 Gli acconti, le rate e il saldo si segnano dalla scheda, col tasto «Apri preventivo, file e pagamenti».")
        b1, b2 = st.columns(2, gap="small")
        if b1.button("✅ Salva", type="primary", key=k + "_ok", width="stretch"):
            if not nome.strip():
                st.error("Scrivi almeno il nominativo.")
                return
            rec = {**voce, "id": voce.get("id") or sc_id(), "nome": nome.strip(), "referente": referente.strip(), "mestiere": mestiere.strip(), "ambito": ambito.strip(),
                   "telefono": tel.strip(), "cellulare": cel.strip(), "email": email.strip(), "sito": (sito or "").strip(), "indirizzo": indirizzo.strip(),
                   "orari": orari.strip(), "ha_preventivo": bool(ha_prev), "note": note.strip()}
            if ha_prev:
                rec.update({"stato": stato, "importo": float(importo or 0), "descrizione": descr.strip(), "lavori_inizio": ini.isoformat() if ini else "", "lavori_fine": fin.isoformat() if fin else ""})
            da_cancellare = list(togli_prev) + list(togli_doc)
            try:
                with st.spinner("Salvo i file…"):
                    rec["preventivo_files"] = [r for r in prev_files if r not in togli_prev] + [sc_file_salva(f) for f in (nuovi_prev or [])]
                    rec["documenti"] = [r for r in docs if r not in togli_doc] + [sc_file_salva(f) for f in (nuovi_doc or [])]
            except Exception as _e:
                st.error(f"Non sono riuscito a salvare un file ({type(_e).__name__}). Riprova.")
                return
            _rbu_salva_voce(sez, rec)
            cp_file_cancella(da_cancellare)
            st.session_state["rbu_mod"] = None
            st.toast("✅ Salvato")
            sc_rerun()
        if b2.button("Annulla", key=k + "_no", width="stretch"):
            st.session_state["rbu_mod"] = None
            sc_rerun()


def _rbu_pagamenti(sez, voce):
    """Acconti, rate e saldo di una voce."""
    k = f"rbu_pg_{voce['id']}"
    pag = sorted([p for p in voce.get("pagamenti") or [] if isinstance(p, dict)], key=lambda p: p.get("data") or "")
    pagato, da_pagare = _rbu_totali(voce)
    imp = float(voce.get("importo") or 0)
    st.markdown(f"**💶 Pagamenti** · pagato **{sc_euro(pagato)}** · ancora da pagare **{sc_euro(da_pagare)}**" + (f" · preventivo {sc_euro(imp)}" if imp else ""))
    if imp and pagato + da_pagare < imp - 0.005:
        st.caption(f"Non ancora programmato: {sc_euro(imp - pagato - da_pagare)}")
    oggi_ = sc_oggi()
    for p in pag:
        dd = sc_data(p.get("data"))
        scad = (not p.get("pagato")) and dd and dd < oggi_
        st.markdown(f"{'✅' if p.get('pagato') else ('⚠️' if scad else '🕒')} **{sc_esc(p.get('tipo'))}** {sc_euro(p.get('importo'))} · {sc_data_scritta(dd, False) if dd else 'senza data'}"
                    + (f" · {sc_esc(p['per'])}" if p.get("per") else "") + (" · **scaduto**" if scad else ""))
        a1, a2 = st.columns(2, gap="small")
        if a1.button("↩️ Segna da pagare" if p.get("pagato") else "✅ Segna pagato", key=f"{k}_s_{p['id']}", width="stretch"):
            def _m(d, pid=p["id"]):
                for x in d["numeri_utili"][sez]:
                    if x["id"] == voce["id"]:
                        for y in x.get("pagamenti", []):
                            if y.get("id") == pid:
                                y["pagato"] = not y.get("pagato")
            sc_salva(_m, "Numeri utili: pagamento")
            sc_rerun()
        if a2.button("🗑️ Togli", key=f"{k}_t_{p['id']}", width="stretch"):
            def _m2(d, pid=p["id"]):
                for x in d["numeri_utili"][sez]:
                    if x["id"] == voce["id"]:
                        x["pagamenti"] = [y for y in x.get("pagamenti", []) if y.get("id") != pid]
            sc_salva(_m2, "Numeri utili: pagamento tolto")
            sc_rerun()
    with st.expander("➕ Aggiungi un acconto, una rata o il saldo"):
        tipo = st.selectbox("Cos'è", RBU_TIPI_PAG, key=k + "_tipo")
        c1, c2 = st.columns(2, gap="small")
        data = c1.date_input("Data", value=oggi_, format="DD/MM/YYYY", key=k + "_data")
        cifra = c2.number_input("Importo (€)", min_value=0.0, step=10.0, format="%.2f", key=k + "_cifra")
        per = st.text_input("Per cosa", key=k + "_per", placeholder="es. materiali, anticipo lavori, fine lavori")
        fatto = st.checkbox("L'ho già pagato", key=k + "_fatto")
        if st.button("💾 Aggiungi pagamento", key=k + "_add", type="primary", width="stretch"):
            if cifra <= 0:
                st.error("Scrivi l'importo.")
            else:
                nuovo = {"id": sc_id(), "tipo": tipo, "data": data.isoformat(), "importo": float(cifra), "per": per.strip(), "pagato": bool(fatto)}

                def _m3(d):
                    for x in d["numeri_utili"][sez]:
                        if x["id"] == voce["id"]:
                            x.setdefault("pagamenti", []).append(nuovo)
                sc_salva(_m3, "Numeri utili: nuovo pagamento")
                for s in (k + "_cifra", k + "_per", k + "_fatto"):
                    st.session_state.pop(s, None)
                sc_rerun()


def _rbu_dettagli(sez, voce):
    with st.container(border=True):
        if voce.get("descrizione"):
            st.markdown("**Lavoro:** " + sc_esc(voce["descrizione"]))
        for i, r in enumerate(voce.get("preventivo_files") or []):
            st.caption("🧾 Preventivo")
            sc_file_mostra(r, f"rbu_dlp_{voce['id']}_{i}")
        if voce.get("documenti"):
            st.caption("📚 Documenti ricevuti")
        for i, r in enumerate(voce.get("documenti") or []):
            sc_file_mostra(r, f"rbu_dld_{voce['id']}_{i}")
        if not (voce.get("preventivo_files") or voce.get("documenti")):
            st.caption("Nessun file allegato. Si aggiungono con «✏️ Modifica».")
        st.divider()
        _rbu_pagamenti(sez, voce)


def _rbu_corpo(sez):
    st.markdown(RBU_CSS, unsafe_allow_html=True)
    d = sc_dati()
    lista = _rbu_voci(d, sez)
    st.caption("Chi chiamare quando serve: mestiere, orari, preventivi, documenti e pagamenti. I tuoi numeri sono visibili solo a te.")
    if st.button("➕ Aggiungi un numero utile", key="rbu_nuovo_" + sez, type="primary", width="stretch"):
        st.session_state["rbu_mod"] = "__nuovo__"
        sc_rerun()
    if st.session_state.get("rbu_mod") == "__nuovo__":
        _rbu_modulo(sez, {})
    if not lista:
        st.info("Non c'è ancora nessun numero. Tocca «Aggiungi un numero utile».")
        return
    cerca = st.text_input("🔍 Cerca (nome, mestiere, ambito…)", key="rbu_cerca_" + sez).strip().lower() if len(lista) > 4 else ""
    mestieri = sorted({v.get("mestiere") for v in lista if v.get("mestiere")})
    if len(mestieri) > 1:
        filtro = st.selectbox("Mostra", ["Tutti"] + mestieri, key="rbu_filtro_" + sez)
    else:
        filtro = "Tutti"
    visibili = [v for v in lista if (filtro == "Tutti" or v.get("mestiere") == filtro) and (not cerca or cerca in " ".join(str(x) for x in v.values()).lower())]
    oggi_ = sc_oggi()
    for v in sorted(visibili, key=lambda x: ((x.get("mestiere") or "zzz").lower(), (x.get("nome") or "").lower())):
        vid = v["id"]
        st.markdown(_rbu_card_html(v, oggi_), unsafe_allow_html=True)
        tasti = sc_chiamate("c" + vid, v.get("telefono"), v.get("cellulare"))
        if sc_wa(v.get("cellulare") or v.get("telefono")):
            tasti.append(("💬 WhatsApp", sc_wa(v.get("cellulare") or v.get("telefono"))))
        if v.get("email"):
            tasti.append(("✉️ Scrivi", "mailto:" + v["email"]))
        if v.get("indirizzo"):
            tasti.append(("📍 Mappa", sc_maps(v["indirizzo"])))
        if cc_url(v.get("sito")):
            tasti.append(("🌐 Sito", cc_url(v["sito"])))
        for i in range(0, len(tasti), 3):
            sc_tasti(tasti[i:i + 3], f"rbu{sez}{vid}{i}")
        if st.session_state.get("rbu_mod") == vid:
            _rbu_modulo(sez, v)
            continue
        aperto = st.session_state.get("rbu_aperto") == vid
        if v.get("ha_preventivo") or v.get("preventivo_files") or v.get("documenti") or v.get("pagamenti") or aperto:
            if st.button(("🔽 Chiudi" if aperto else "📂 Apri") + " preventivo, file e pagamenti", key=f"rbu_ap_{vid}", width="stretch"):
                st.session_state["rbu_aperto"] = None if aperto else vid
                sc_rerun()
            if aperto:
                _rbu_dettagli(sez, v)
        e1, e2 = st.columns(2, gap="small")
        if e1.button("✏️ Modifica", key=f"rbu_ed_{vid}", width="stretch"):
            st.session_state["rbu_mod"] = vid
            st.session_state["rbu_conferma"] = None
            sc_rerun()
        if st.session_state.get("rbu_conferma") == vid:
            st.warning(f"Eliminare «{v.get('nome', '')}»? Anche i suoi file e pagamenti.")
            s1, s2 = st.columns(2, gap="small")
            if s1.button("🗑️ Sì, elimina", key=f"rbu_si_{vid}", type="primary", width="stretch"):
                _rbu_elimina(sez, v)
                st.session_state["rbu_conferma"] = None
                sc_rerun()
            if s2.button("No", key=f"rbu_no_{vid}", width="stretch"):
                st.session_state["rbu_conferma"] = None
                sc_rerun()
        elif e2.button("🗑️ Elimina", key=f"rbu_el_{vid}", width="stretch"):
            st.session_state["rbu_conferma"] = vid
            sc_rerun()


def rbu_apri(sez):
    st.session_state["rbu_mod"] = None
    sc_dialogo("📞 Numeri utili", lambda: _rbu_corpo(sez))
