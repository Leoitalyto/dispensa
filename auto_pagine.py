# -*- coding: utf-8 -*-
"""AUTO — le pagine: scelta del veicolo, scheda, scadenze, manutenzione, rifornimenti e spese, ricambi e valore, emergenza. Caricato dopo auto.py."""
import hashlib
import html as _h_ap
import re
import urllib.parse
import uuid
from datetime import date, datetime, timedelta

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# elenchi (campi)
# ---------------------------------------------------------------------------------------------------------------------
_SPEC_VEICOLO = [("tipo_veicolo", "Che mezzo è", "s", _AU_TIPI), ("nome", "Soprannome (facoltativo)", "t", None), ("targa", "Targa", "t", None), ("marca", "Marca", "t", None), ("modello", "Modello", "t", None),
                 ("allestimento", "Allestimento", "t", None), ("anno", "Anno", "n", None), ("immatricolazione", "Prima immatricolazione", "d", None), ("alimentazione", "Alimentazione", "s", _AU_ALIM),
                 ("kw", "Potenza (kW)", "n", None), ("cv", "Potenza (CV)", "n", None), ("classe_euro", "Classe ambientale", "t", None), ("cilindrata", "Cilindrata (cc)", "n", None), ("telaio", "Numero di telaio", "t", None),
                 ("km_attuali", "Chilometri attuali", "n", None), ("pressione_pneumatici", "Pressione pneumatici consigliata", "t", None), ("serbatoio_l", "Serbatoio (litri)", "n", None), ("bagagliaio_l", "Bagagliaio (litri)", "n", None),
                 ("colore", "Colore", "t", None), ("serie", "Numero di serie o contrassegno (monopattini, e-bike, ciclomotori)", "t", None), ("massa_kg", "Massa complessiva (kg)", "n", None),
                 ("posti", "Posti", "n", None), ("assi", "Numero di assi", "n", None), ("velocita_max", "Velocità massima (km/h)", "n", None), ("autonomia_km", "Autonomia dichiarata (km)", "n", None),
                 ("potenza_w", "Potenza (W, per monopattini e e-bike)", "n", None), ("batteria_nominale_kwh", "🔋 Batteria di trazione: capacità nominale (kWh)", "n", None), ("batteria_utile_kwh", "🔋 Batteria di trazione: capacità utile (kWh)", "n", None),
                 ("ricarica_ac_kw", "⚡ Potenza massima di ricarica AC (kW)", "n", None), ("ricarica_dc_kw", "⚡ Potenza massima di ricarica DC (kW)", "n", None), ("connettore", "🔌 Connettore di bordo", "s", _AU_CONNETTORI),
                 ("note", "Note", "a", None)]
_SPEC_DOC = [("tipo", "Che documento è", "s", _AU_DOC_TIPI), ("titolo", "Titolo", "t", None), ("data", "Data del documento", "d", None), ("scadenza", "Scadenza (se c'è)", "d", None), ("importo", "Importo (€, se c'è)", "n", None), ("note", "Note", "a", None)]
_SPEC_INT = [("categoria", "Categoria", "s", _AU_INT_CAT), ("data", "Data", "d", None), ("km", "Chilometri", "n", None), ("costo", "Costo (€)", "n", None), ("officina", "Officina", "t", None),
             ("descrizione", "Che lavoro è stato fatto", "a", None), ("garanzia_fino", "Garanzia sui ricambi fino al", "d", None), ("prossimo_km", "Prossimo intervento a (km)", "n", None), ("prossima_data", "Oppure entro il", "d", None)]
_SPEC_GOMME = [("tipo", "Tipo", "s", _AU_STAG), ("marca", "Marca e modello", "t", None), ("misura", "Misura", "t", "es. 205/55 R16"), ("battistrada_mm", "Battistrada residuo (mm)", "n", None), ("stato", "Dove sono", "s", ["Montate", "In deposito"]),
               ("montata_dal", "Montate dal", "d", None), ("deposito", "Luogo di deposito", "t", None), ("cambio_entro", "Cambio stagionale entro il", "d", None), ("note", "Note", "a", None)]
_SPEC_SPESE = [("categoria", "Che spesa è", "s", _AU_SPESE_CAT), ("data", "Data", "d", None), ("importo", "Importo (€)", "n", None), ("note", "Note", "t", None)]
_SPEC_SOH = [("data", "Data del test", "d", None), ("km", "Chilometri", "n", None), ("soh", "Salute della batteria (SoH, %)", "n", "es. 94"), ("autonomia_reale", "Autonomia reale (km)", "n", None), ("autonomia_nominale", "Autonomia nominale (km)", "n", None), ("note", "Note (come l'hai misurato)", "t", None)]
_SPEC_VALORE = [("data", "Data", "d", None), ("valore", "Valore stimato (€)", "n", None), ("km", "Chilometri", "n", None), ("note", "Note (da dove viene la stima)", "t", None)]
_SPEC_CAVI = [("tipo", "Che cos'è", "s", ["Cavo Modo 2 (domestico)", "Cavo Modo 3 (Type 2)", "Adattatore", "Altro"]), ("specifica", "Potenza (A / kW) e lunghezza", "t", None), ("note", "Note", "a", None)]
_SPEC_TESSERE = [("nome", "Nome", "t", None), ("tipo", "Che cos'è", "s", ["Tessera RFID", "App di ricarica", "Abbonamento"]), ("note", "Numero, tessera o dove sta (non scrivere le password)", "a", None)]
_SPEC_USURA = [("parte", "Quale parte", "s", _AU_PARTI_USURA), ("data", "Data del controllo", "d", None), ("valore", "Misura o stato (es. 4 mm, 60%)", "t", None), ("stato", "Come sta", "s", ["OK", "Da controllare", "Da sostituire"]),
               ("prossima_km", "Da sostituire o controllare a (km)", "n", None), ("prossima_data", "Oppure entro il", "d", None), ("note", "Note", "a", None)]
_SPEC_VIAGGI = [("data", "Data", "d", None), ("partenza", "Partenza", "t", None), ("arrivo", "Arrivo", "t", None), ("km", "Km percorsi", "n", None), ("categoria", "Tipo di viaggio", "s", ["Personale", "Lavoro / aziendale"]), ("note", "Motivo o note", "t", None)]
_SPEC_PATENTI = [("nome", "Di chi è la patente", "t", None), ("categorie", "Categorie (es. B, A, C, D, CQC)", "t", None), ("numero", "Numero della patente (facoltativo)", "t", None), ("scadenza", "Scadenza della patente", "d", None),
                 ("visita_medica", "Scadenza della visita medica", "d", None), ("cqc", "Scadenza CQC (se ce l'hai)", "d", None), ("punti", "Saldo punti", "n", "es. 20"), ("note", "Note", "a", None)]
_SPEC_VERBALI = [("data", "Data dell'infrazione", "d", None), ("luogo", "Luogo", "t", None), ("tipo", "Che infrazione", "t", None), ("importo", "Importo (€)", "n", None), ("stato", "Stato", "s", ["Da pagare", "Pagato", "Ricorso in corso", "Annullato"]),
                 ("scadenza_pagamento", "Pagare entro il", "d", None), ("veicolo", "Targa del veicolo", "t", None), ("punti_tolti", "Punti tolti", "n", None), ("ricorso", "Note sul ricorso (data, ente…)", "a", None), ("note", "Note", "a", None)]
_SPEC_SINISTRO = [("data", "Data", "d", None), ("ora", "Ora", "t", None), ("luogo", "Luogo preciso", "t", None), ("dinamica", "Come è successo", "a", None), ("danni", "Danni al mio veicolo", "a", None),
                  ("feriti", "Ci sono feriti", "b", None), ("controparte_targa", "Targa dell'altro veicolo", "t", None), ("controparte_nome", "Nome dell'altro conducente", "t", None), ("controparte_telefono", "Telefono", "t", None),
                  ("controparte_compagnia", "Compagnia dell'altro", "t", None), ("controparte_polizza", "Polizza dell'altro", "t", None), ("testimoni", "Testimoni (nome e telefono)", "a", None),
                  ("concordato", "Abbiamo firmato insieme il modulo CAI", "b", None), ("note", "Altre note", "a", None)]


def _spec_rifornimenti(v):
    tipi = ["Ricarica"] if _au_solo_elettrico(v) else (["Ricarica", "Carburante"] if _au_ricarica(v) else ["Carburante"])
    return [("tipo", "Che cosa hai fatto", "s", tipi), ("data", "Data", "d", None), ("km", "Chilometri", "n", None), ("luogo", "Dove (casa, colonnina AC/DC, distributore)", "t", None),
            ("quantita", "Litri (carburante) o kWh (ricarica)", "n", None), ("costo", "Costo totale (€)", "n", None), ("prezzo", "Prezzo al litro o al kWh (se vuoto lo calcolo)", "n", None),
            ("potenza_max", "Potenza massima raggiunta (kW, ricarica)", "n", None), ("pieno", "Pieno fatto (serbatoio pieno / batteria carica)", "b", None), ("note", "Note", "t", None)]


# ---------------------------------------------------------------------------------------------------------------------
# la scheda del veicolo e il flusso «Carta di Circolazione»
# ---------------------------------------------------------------------------------------------------------------------
def _form_veicolo(chiave, valori, ric=None):
    ric = ric or {}
    base = {k: (ric.get(k) or {}).get("valore") for k in ric}
    base.update({k: x for k, x in (valori or {}).items() if x not in (None, "")})
    with st.form(chiave, border=False):
        st.caption("🟢 sicuro · 🟡 abbastanza · 🟠 poco: i dati letti vanno sempre controllati." if ric else "Compila quello che sai: tutto è modificabile dopo.")
        val = _au_widgets(_SPEC_VEICOLO, base, chiave)
        ok = st.form_submit_button("✅ Conferma e salva" if not (valori or {}).get("id") else "💾 Salva le modifiche", type="primary", width="stretch")
    val["targa"] = re.sub(r"\s+", "", val.get("targa", "")).upper()
    return ok, val


def _au_chiudi(coda):
    if coda:
        coda.pop(0)
    st.session_state["ca_giro"] = st.session_state.get("ca_giro", 0) + 1
    st.session_state.pop("au_fin", None)


def _au_corpo(coda):
    c = coda[0]
    modo = c["modo"]
    st.markdown(f"#### {'🪪 Nuovo veicolo' if modo.startswith('libretto') else '📄 Nuovo documento'}" + (f" · {_h_ap.escape(c['nome'])}" if c.get("nome") else ""))
    ric, letto = {}, False
    if c.get("dati"):
        mime = _ca_mime(c["nome"], "", c["dati"]) if "_ca_mime" in globals() else ("application/pdf" if c["nome"].lower().endswith(".pdf") else "image/jpeg")
        if mime.startswith("image/"):
            st.image(c["dati"], width=240)
        chiave_l = f"au_lett_{c['sha']}"
        if chiave_l not in st.session_state:
            with st.spinner("Leggo il documento…"):
                try:
                    testo, _info = ca_estrai_testo(c["nome"], mime, c["dati"])
                except Exception:
                    testo = ""
                st.session_state[chiave_l] = ((au_leggi_libretto(testo) if modo.startswith("libretto") else au_leggi_doc(testo)) if (testo or "").strip() else {}, bool((testo or "").strip()))
        ric, letto = st.session_state[chiave_l]
        if letto and ric:
            st.success("Ho letto il documento. **Controlla e correggi**: i dati che non ho trovato restano vuoti.")
        else:
            st.info("Non sono riuscito a leggere tutto: compila tu i dati qui sotto.")
    b = st.columns(1)[0]
    if b.button("✖ Scarta", key="au_scarta", width="stretch"):
        _au_chiudi(coda)
        st.rerun()
    if modo.startswith("libretto"):
        pre = {"tipo_veicolo": c.get("tipo") or "Auto"}
        if pre["tipo_veicolo"] in ("Monopattino elettrico", "Bicicletta elettrica (e-bike)"):
            pre["alimentazione"] = "Elettrica (BEV)"
        ok, val = _form_veicolo("au_fv_" + c["sha"][:8], pre, ric)
        if ok:
            vid = uuid.uuid4().hex[:10]
            rif = {}
            if c.get("dati"):
                try:
                    rif = (_fa_salva_files([_SpUp(c["nome"], c["dati"])]) or [{}])[0]
                except Exception as ex:
                    st.error(f"Non sono riuscito a salvare il file: {ex}")
                    return
            nuovo = dict(val, id=vid, scadenze={}, documenti=[], interventi=[], pneumatici=[], rifornimenti=[], spese=[], soh=[], valutazioni=[], cavi=[], tessere=[], sinistri=[], ricambi={})
            if rif:
                nuovo["documenti"] = [{"id": uuid.uuid4().hex[:10], "tipo": "Carta di circolazione", "titolo": "Carta di circolazione", "data": val.get("immatricolazione", ""), "scadenza": "", "importo": "", "note": "", "files": [rif]}]
            _au_salva(lambda a, n=nuovo: a["veicoli"].append(n), "Auto: nuovo veicolo")
            if rif and "ls_segna_archiviato" in globals():
                ls_segna_archiviato()
            st.session_state["au_sel"] = vid
            st.session_state.pop("au_vpill", None)                  # la scelta si rifà da «au_sel» (il nuovo veicolo)
            _au_chiudi(coda)
            st.session_state["messaggio"] = f"✅ Aggiunto «{_au_nome(nuovo)}»."
            st.rerun()
        return
    # documento del veicolo
    spec = _SPEC_DOC
    base = {k: (ric.get(k) or {}).get("valore") for k in ric}
    with st.form("au_fd_" + c["sha"][:8], border=False):
        val = _au_widgets(spec, base, "au_fd_" + c["sha"][:8])
        agg = st.checkbox("🔄 Aggiorna anche le scadenze del veicolo (assicurazione o revisione) con questi dati", value=True)
        ok = st.form_submit_button("✅ Conferma e archivia", type="primary", width="stretch")
    if ok:
        rif = {}
        if c.get("dati"):
            try:
                rif = (_fa_salva_files([_SpUp(c["nome"], c["dati"])]) or [{}])[0]
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare il file: {ex}")
                return
        doc = dict(val, id=uuid.uuid4().hex[:10], files=[rif] if rif else [])
        extra = {k: (ric.get(k) or {}).get("valore") for k in ("compagnia",)}

        def _fn(v, doc=doc, agg=agg, extra=extra):
            v.setdefault("documenti", []).append(doc)
            sc = v.setdefault("scadenze", {})
            if agg and doc["tipo"] == "Polizza assicurativa" and doc.get("scadenza"):
                s = sc.setdefault("assicurazione", {})
                s.update({"data": doc["scadenza"]})
                if doc.get("importo"):
                    s["importo"] = doc["importo"]
                if extra.get("compagnia"):
                    s["compagnia"] = extra["compagnia"]
            if agg and doc["tipo"] == "Revisione (certificato)":
                s = sc.setdefault("revisione", {})
                if doc.get("data"):
                    s["ultima"] = doc["data"]
                if doc.get("scadenza"):
                    s["data"] = doc["scadenza"]
        _au_mod(c["vid"], _fn, "Auto: documento")
        if rif and "ls_segna_archiviato" in globals():
            ls_segna_archiviato()
        _au_chiudi(coda)
        st.session_state["messaggio"] = "✅ Documento archiviato."
        st.rerun()


def _au_finestra(coda):
    chiave = coda[0]["sha"]

    def _apri():
        def _fin():
            _au_corpo(coda)
        try:
            st.dialog("🚗 Controlla e conferma", width="large")(_fin)()
        except TypeError:
            st.dialog("🚗 Controlla e conferma")(_fin)()
    if st.session_state.get("au_fin") != chiave:
        st.session_state["au_fin"] = chiave
        _apri()
    else:
        st.info(f"📖 C'è un documento aperto: «{_h_ap.escape(coda[0].get('nome') or 'a mano')}». Se hai chiuso la finestra, riaprila.")
        r1, r2 = st.columns(2, gap="small")
        if r1.button("📖 Riapri", key="au_riapri", type="primary", width="stretch"):
            _apri()
        if r2.button("✖ Scarta", key="au_scarta_f", width="stretch"):
            _au_chiudi(coda)
            st.rerun()


def _au_ricevi():
    """Il pulsante arancione: ritorna (nome, dati) quando un file arriva."""
    arr = None
    if "_ca_pannello_caricamento" in globals():
        up = _ca_pannello_caricamento(st.session_state.get("ca_giro", 0), multi=False)
        if up is not None:
            arr = (up.name, up.getvalue())
        b = st.session_state.pop("ca_bozza_in", None)
        if b and b.get("dati"):
            arr = (b.get("nome") or "documento", b["dati"])
    return arr


def _au_pannello(v, coda):
    """Il pannello del pulsante arancione, quando serve: nuovo veicolo / nuovo documento / allegare un file."""
    ctx = st.session_state.get("au_pannello")
    al = st.session_state.get("au_allega")
    if al and al["vid"] != "cond" and (not v or al["vid"] != v["id"]):
        al = None
    if not ctx and not al:
        return
    st.markdown(f"<div class='au-card'><b class='t'>📎 {'Allega un file a: ' + _h_ap.escape(al['titolo']) if al else ('Carica la Carta di Circolazione' if ctx == 'libretto' else 'Scegli la foto del veicolo' if ctx == 'foto' else 'Carica un documento del veicolo')}</b></div>", unsafe_allow_html=True)
    arr = _au_ricevi()
    if st.button("✖ Chiudi questo pannello", key="au_chiudi_pannello", width="stretch"):
        st.session_state.pop("au_pannello", None)
        st.session_state.pop("au_allega", None)
        st.rerun()
    if not arr:
        return
    nome, dati = arr
    sha = hashlib.sha256(dati).hexdigest()
    if al:
        try:
            rif = (_fa_salva_files([_SpUp(nome, dati)]) or [{}])[0]
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare il file: {ex}")
            return

        def _fn(vv, al=al, rif=rif):
            for x in vv.get(al["coll"], []):
                if x.get("id") == al["id"]:
                    x["files"] = list(x.get("files") or []) + [rif]
        _au_mod(al["vid"], _fn, "Auto: file allegato")
        if "ls_segna_archiviato" in globals():
            ls_segna_archiviato()
        st.session_state.pop("au_allega", None)
        st.session_state["ca_giro"] = st.session_state.get("ca_giro", 0) + 1
        st.session_state["messaggio"] = f"✅ «{nome}» allegato."
        st.rerun()
    if ctx == "foto":
        mime = _ca_mime(nome, "", dati) if "_ca_mime" in globals() else ("image/jpeg" if not nome.lower().endswith(".pdf") else "application/pdf")
        if not str(mime).startswith("image/"):
            st.error("Per la foto scegli un'immagine (non un PDF).")
            return
        try:
            rif = (_fa_salva_files([_SpUp(nome, dati)]) or [{}])[0]
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare la foto: {ex}")
            return
        vecchia = (v.get("foto") or {}).get("id")
        _au_mod(v["id"], lambda x, rif=rif: x.__setitem__("foto", rif), "Auto: foto del veicolo")
        if vecchia:
            try:
                _fa_cancella_files([vecchia])
            except Exception:
                pass
        if "ls_segna_archiviato" in globals():
            ls_segna_archiviato()
        st.session_state.pop("au_pannello", None)
        st.session_state["ca_giro"] = st.session_state.get("ca_giro", 0) + 1
        st.session_state["messaggio"] = "✅ Foto salvata."
        st.rerun()
    modo = "libretto" if ctx == "libretto" else "doc"
    if not any(c_["sha"] == sha for c_ in coda):
        coda.append({"modo": modo, "nome": nome, "dati": dati, "sha": sha, "vid": (v or {}).get("id"), "tipo": st.session_state.get("au_nuovo_tipo", "Auto")})
    st.session_state.pop("au_pannello", None)


# ---------------------------------------------------------------------------------------------------------------------
# le schede
# ---------------------------------------------------------------------------------------------------------------------
def _au_scegli(label, voci, chiave):
    """Pillole (o scelta a bottoni) che ricordano la scelta; si può impostare da fuori (es. dal garage) senza avvisi."""
    if st.session_state.get(chiave) not in voci:
        st.session_state.pop(chiave, None)
    if hasattr(st, "pills"):
        r = st.pills(label, voci, key=chiave, label_visibility="collapsed") if chiave in st.session_state else st.pills(label, voci, default=voci[0], key=chiave, label_visibility="collapsed")
    else:
        r = st.radio(label, voci, horizontal=True, key=chiave, label_visibility="collapsed")
    return r or voci[0]


def _cerca_url(q):
    return "https://www.google.com/search?q=" + urllib.parse.quote_plus(q)


def tab_scheda(v):
    vid = v["id"]
    dett = [("Mezzo", v.get("tipo_veicolo")), ("Targa", v.get("targa")), ("Numero di serie o contrassegno", v.get("serie")), ("Alimentazione", v.get("alimentazione")), ("Anno", v.get("anno")), ("Allestimento", v.get("allestimento")), ("Potenza", (v["kw"] + " kW" + ((" / " + v["cv"] + " CV") if v.get("cv") else "")) if v.get("kw") else ""),
            ("Classe", v.get("classe_euro")), ("Cilindrata", (v["cilindrata"] + " cc") if v.get("cilindrata") else ""), ("Telaio", v.get("telaio")), ("Prima immatricolazione", _au_it(v.get("immatricolazione"))),
            ("Pneumatici", v.get("pressione_pneumatici")), ("Serbatoio", (v["serbatoio_l"] + " L") if v.get("serbatoio_l") else ""), ("Bagagliaio", (v["bagagliaio_l"] + " L") if v.get("bagagliaio_l") else ""), ("Colore", v.get("colore")),
            ("Massa complessiva", (v["massa_kg"] + " kg") if v.get("massa_kg") else ""), ("Posti", v.get("posti")), ("Assi", v.get("assi")), ("Velocità massima", (v["velocita_max"] + " km/h") if v.get("velocita_max") else ""),
            ("Autonomia dichiarata", (v["autonomia_km"] + " km") if v.get("autonomia_km") else ""), ("Potenza", (v["potenza_w"] + " W") if v.get("potenza_w") else "")]
    if _au_ha_batteria(v):
        dett += [("Batteria (nominale / utile)", " / ".join(x for x in ((v.get("batteria_nominale_kwh") or "") and v["batteria_nominale_kwh"] + " kWh", (v.get("batteria_utile_kwh") or "") and v["batteria_utile_kwh"] + " kWh") if x)),
                 ("Ricarica max AC / DC", " / ".join(x for x in ((v.get("ricarica_ac_kw") or "") and v["ricarica_ac_kw"] + " kW", (v.get("ricarica_dc_kw") or "") and v["ricarica_dc_kw"] + " kW") if x)), ("Connettore", v.get("connettore"))]
    righe = "".join(f"<br><small><b>{k}:</b> {_h_ap.escape(str(x))}</small>" for k, x in dett if x)
    st.markdown(f"<div class='au-card'><b class='t'>{_h_ap.escape(_au_etichetta(v))}</b>{righe}" + (f"<br><small>📝 {_h_ap.escape(v['note'])}</small>" if v.get("note") else "") + "</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    if c1.button("✏️ Modifica la scheda", key=f"au_mod_{vid}", width="stretch"):
        def _fin():
            ok, val = _form_veicolo(f"au_ev_{vid}", v)
            if ok:
                _au_mod(vid, lambda x, val=val: x.update(val), "Auto: scheda modificata")
                st.session_state["messaggio"] = "✅ Scheda salvata."
                st.rerun()
        st.dialog("Modifica la scheda", width="large")(_fin)()
    if c2.button("🗑️ Elimina il veicolo", key=f"au_elv_{vid}", width="stretch"):
        def _fin2():
            st.warning(f"Eliminare **{_h_ap.escape(_au_etichetta(v))}** con tutto quello che ha dentro (documenti, interventi, rifornimenti)?")
            s1, s2 = st.columns(2, gap="small")
            if s1.button("🗑️ Sì, elimina tutto", key=f"au_elvs_{vid}", type="primary", width="stretch"):
                ids = []
                for coll in ("documenti", "interventi", "pneumatici", "sinistri", "cavi", "tessere"):
                    for x in v.get(coll, []):
                        ids += [r["id"] for r in x.get("files", []) if r.get("id")]
                _au_salva(lambda a: a.__setitem__("veicoli", [x for x in a["veicoli"] if x.get("id") != vid]), "Auto: veicolo eliminato")
                if ids:
                    try:
                        _fa_cancella_files(ids)
                    except Exception:
                        pass
                st.session_state.pop("au_sel", None)
                st.session_state.pop("au_vpill", None)
                st.session_state["messaggio"] = "🗑️ Veicolo eliminato."
                st.rerun()
            if s2.button("No", key=f"au_elvn_{vid}", width="stretch"):
                st.rerun()
        st.dialog("🗑️ Elimina il veicolo")(_fin2)()
    with st.form(f"au_km_{vid}", border=False):
        k1, k2 = st.columns([3, 2], gap="small")
        km = k1.text_input("🛣️ Chilometri attuali", value=v.get("km_attuali", ""), key=f"au_kmv_{vid}", label_visibility="collapsed", placeholder="Chilometri attuali")
        if k2.form_submit_button("💾 Aggiorna i km", width="stretch"):
            n = _au_n(km)
            if n is None:
                st.error("Scrivi un numero.")
            else:
                _au_mod(vid, lambda x, n=n: x.__setitem__("km_attuali", str(int(n))), "Auto: km")
                st.session_state["messaggio"] = "✅ Chilometri aggiornati."
                st.rerun()
    q = " ".join(x for x in (v.get("marca"), v.get("modello"), v.get("anno")) if x)
    if q:
        st.markdown("**🔎 Manuali online** (si aprono in una nuova pagina)")
        m1, m2 = st.columns(2, gap="small")
        m1.link_button("📘 Manuale d'uso (PDF)", _cerca_url(f"manuale uso e manutenzione {q} pdf"), width="stretch")
        m2.link_button("🔌 Scatola fusibili", _cerca_url(f"scatola fusibili {q}"), width="stretch")
        m3, m4 = st.columns(2, gap="small")
        m3.link_button("🚦 Mappa delle spie", _cerca_url(f"spie cruscotto significato {q}"), width="stretch")
        m4.link_button("🛞 Pressione gomme", _cerca_url(f"pressione pneumatici {q}"), width="stretch")
    st.markdown("#### 🗄️ Cassetto digitale dei documenti")
    if st.button("📎 Carica un documento (lo leggo io)", key=f"au_pdoc_{vid}", type="primary", width="stretch"):
        st.session_state["au_pannello"] = f"doc"
        st.rerun()
    _au_elenco(v, "documenti", "Documenti", _SPEC_DOC, lambda x: f"{x.get('titolo') or x.get('tipo')}", lambda x: [x.get("tipo"), ("Data: " + _au_it(x.get("data"))) if x.get("data") else "", ("Scadenza: " + _au_it(x.get("scadenza"))) if x.get("scadenza") else "",
               ("Importo: " + _au_eur(x.get("importo"))) if x.get("importo") else "", x.get("note")], "Nessun documento: carica la Carta di Circolazione, il certificato di proprietà, la polizza…", "Aggiungi un documento a mano",
               icona="📄", aggiorna_km=False)
    if _au_ricarica(v):
        st.markdown("#### 🔌 Wallet di ricarica")
        st.caption("I cavi che hai in dotazione e le tessere o le app di ricarica collegate. Non scrivere le password.")
        w1, w2 = st.columns(2, gap="small")
        with w1:
            st.markdown("**Cavi e adattatori**")
            _au_elenco(v, "cavi", "Cavi", _SPEC_CAVI, lambda x: x.get("tipo", "Cavo"), lambda x: [x.get("specifica"), x.get("note")], "Nessun cavo registrato.", "Aggiungi un cavo", ordine="tipo", inverso=False, icona="🔌", aggiorna_km=False)
        with w2:
            st.markdown("**Tessere e app**")
            _au_elenco(v, "tessere", "Tessere", _SPEC_TESSERE, lambda x: x.get("nome", "Tessera"), lambda x: [x.get("tipo"), x.get("note")], "Nessuna tessera registrata.", "Aggiungi una tessera", ordine="nome", inverso=False, icona="💳", aggiorna_km=False)


def _carta_scad(s, v):
    cls = {"r": "au-r", "g": "au-g", "v": "au-v"}[s["stato"]]
    ic = {"r": "🔴", "g": "🟡", "v": "🟢"}[s["stato"]]
    if s.get("giorni") is None:
        r = s["km_restanti"]
        testo = ("superati di %d km" % -r) if r < 0 else f"mancano {int(r)} km"
    else:
        g = s["giorni"]
        testo = f"{_au_it(s['data'].isoformat())} · " + ("SCADUTA da %d giorni" % -g if g < 0 else "scade oggi" if g == 0 else f"tra {g} giorni")
    st.markdown(f"<div class='au-scad {cls}'>{ic} {_h_ap.escape(s['etichetta'])}<br><small>{_h_ap.escape(testo)}</small></div>", unsafe_allow_html=True)


def tab_scadenze(v):
    vid = v["id"]
    st.caption("🟢 tutto a posto · 🟡 scade entro 30 giorni · 🔴 scaduta. Ti avviso **30, 15 e 3 giorni prima**: la Home lampeggia e, con gli avvisi accesi, ricevi il messaggio sui tuoi canali.")
    attive = au_scadenze(v)
    if attive:
        for s in attive:
            _carta_scad(s, v)
    else:
        st.info("Nessuna scadenza impostata. Tocca ✏️ qui sotto per bollo, assicurazione, revisione, garanzie e tagliando.")
    st.markdown("#### ✏️ Imposta o cambia")
    q = " ".join(x for x in (v.get("marca"), v.get("modello")) if x)
    for chiave, etichetta, spec in au_scad_def(v):
        s = (v.get("scadenze") or {}).get(chiave) or {}
        riga = f"{etichetta}" + (f" — {_au_it(s.get('data'))}" if s.get("data") else " — non impostata")
        if st.button(riga, key=f"au_sc_{chiave}_{vid}", width="stretch"):
            def _fin(chiave=chiave, spec=spec, s=s, etichetta=etichetta):
                with st.form(f"au_fsc_{chiave}_{vid}", border=False):
                    val = _au_widgets(spec, s, f"au_scv_{chiave}_{vid}")
                    avv = st.checkbox("🔔 Avvisami prima della scadenza", value=s.get("avvisa", True), key=f"au_sca_{chiave}_{vid}")
                    ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
                if ok:
                    val["avvisa"] = bool(avv)
                    _au_mod(vid, lambda x, val=val, chiave=chiave: x.setdefault("scadenze", {}).__setitem__(chiave, val), "Auto: scadenza")
                    st.session_state["messaggio"] = "✅ Scadenza salvata."
                    st.rerun()
            st.dialog(etichetta)(_fin)()
    st.markdown("#### 🔗 Servizi")
    l1, l2 = st.columns(2, gap="small")
    l1.link_button("💶 Bollo: calcolo e pagamento", _cerca_url("calcolo bollo auto ACI pagamento PagoPA"), width="stretch")
    l2.link_button("🛡️ Verifica copertura assicurativa", _cerca_url("verifica copertura assicurativa targa portale dell'automobilista"), width="stretch")
    l3, l4 = st.columns(2, gap="small")
    l3.link_button("🔍 Prenota la revisione", _cerca_url("prenota revisione auto vicino a me"), width="stretch")
    tel = ((v.get("scadenze") or {}).get("assicurazione") or {}).get("telefono")
    if tel:
        l4.link_button("📞 Chiama la compagnia", "tel:" + re.sub(r"[^\d+]", "", tel), width="stretch")
    st.caption("Il calcolo del bollo dipende dalla Regione, dai kW e dalla classe ambientale (con esenzioni e riduzioni per elettriche e ibride): usa il servizio ufficiale, poi registra l'importo pagato in «Altre spese».")


def tab_manutenzione(v):
    voci = ["🔧 Interventi e tagliandi", "🧩 Parti di usura", "🛞 Pneumatici"] + (["🔋 Salute batteria (SoH)"] if _au_ha_batteria(v) else [])
    sc = _au_scegli("Manutenzione", voci, f"au_man_{v['id']}")
    if sc == voci[0]:
        cats = ["Tutte le categorie"] + _AU_INT_CAT
        f = st.selectbox("Filtra", cats, key=f"au_intf_{v['id']}", label_visibility="collapsed")
        tot = sum(_au_n(x.get("costo")) or 0 for x in v.get("interventi", []) if f == cats[0] or x.get("categoria") == f)
        if tot:
            st.markdown(f"💶 **Speso in totale:** {_au_eur(tot)}")
        _au_elenco(v, "interventi", "Interventi", _SPEC_INT, lambda x: f"{x.get('categoria', 'Intervento')} · {_au_it(x.get('data'))}", lambda x: [("Km: " + x["km"]) if x.get("km") else "", ("Costo: " + _au_eur(x["costo"])) if x.get("costo") else "",
                   ("Officina: " + x["officina"]) if x.get("officina") else "", x.get("descrizione"), ("Garanzia sui ricambi fino al " + _au_it(x["garanzia_fino"])) if x.get("garanzia_fino") else "",
                   ("Prossimo: " + " / ".join(z for z in ((x["prossimo_km"] + " km") if x.get("prossimo_km") else "", _au_it(x.get("prossima_data"))) if z)) if (x.get("prossimo_km") or x.get("prossima_data")) else ""],
                   "Nessun intervento registrato. Registra tagliandi, riparazioni, carrozzeria e cristalli (con le foto prima e dopo: tasto 📎).", "Registra un intervento", filtro=lambda x: f == cats[0] or x.get("categoria") == f, icona="🔧")
    elif sc == voci[1]:
        st.caption("Il logorio che non si vede ma conta: pastiglie e dischi dei freni, spazzole, filtri, liquidi, batteria 12V, distribuzione. Annota la misura e quando va sostituita: ti avviso.")
        _au_elenco(v, "usura", "Usura", _SPEC_USURA, lambda x: f"{x.get('parte', 'Parte')} · {x.get('stato', '')}".strip(" ·"), lambda x: [("Controllato il " + _au_it(x["data"])) if x.get("data") else "", ("Misura: " + x["valore"]) if x.get("valore") else "",
                   ("Da sostituire/controllare a " + x["prossima_km"] + " km") if x.get("prossima_km") else "", ("Entro il " + _au_it(x["prossima_data"])) if x.get("prossima_data") else "", "🔴 Da sostituire" if x.get("stato") == "Da sostituire" else "🟡 Da controllare" if x.get("stato") == "Da controllare" else "", x.get("note")],
                   "Nessuna parte registrata. Annota per esempio lo spessore delle pastiglie dei freni o la data dei filtri.", "Registra una parte di usura", ordine="data", icona="🧩", aggiorna_km=False)
    elif sc == voci[2]:
        st.caption("Le gomme montate, quelle in deposito, il battistrada e il cambio stagionale.")
        _au_elenco(v, "pneumatici", "Pneumatici", _SPEC_GOMME, lambda x: f"{x.get('tipo', 'Gomme')} · {x.get('misura', '')}".strip(" ·"), lambda x: [x.get("marca"), x.get("stato"), ("Battistrada: " + x["battistrada_mm"] + " mm") if x.get("battistrada_mm") else "",
                   ("Montate dal " + _au_it(x["montata_dal"])) if x.get("montata_dal") else "", ("Deposito: " + x["deposito"]) if x.get("deposito") else "", ("Cambio entro il " + _au_it(x["cambio_entro"])) if x.get("cambio_entro") else "", x.get("note")],
                   "Nessuna gomma registrata.", "Aggiungi un treno di gomme", ordine="stato", inverso=False, icona="🛞", aggiorna_km=False)
    else:
        st.caption("Registra ogni test di degrado della batteria di trazione: la salute residua (SoH) e l'autonomia reale rispetto a quella nominale.")
        _au_elenco(v, "soh", "SoH", _SPEC_SOH, lambda x: f"SoH {x.get('soh', '?')}% · {_au_it(x.get('data'))}", lambda x: [("Km: " + x["km"]) if x.get("km") else "", ("Autonomia reale: " + x["autonomia_reale"] + " km" + ((" su " + x["autonomia_nominale"] + " nominali") if x.get("autonomia_nominale") else "")) if x.get("autonomia_reale") else "", x.get("note")],
                   "Nessun test registrato.", "Registra un test SoH", icona="🔋")
        punti = sorted([(x.get("data"), _au_n(x.get("soh"))) for x in v.get("soh", []) if x.get("data") and _au_n(x.get("soh")) is not None])
        if len(punti) >= 2:
            try:
                import pandas as pd
                st.markdown("**Andamento della salute della batteria (%)**")
                st.line_chart(pd.DataFrame({"SoH %": [p[1] for p in punti]}, index=[p[0] for p in punti]))
            except Exception:
                pass


def au_consumi(v):
    """Consumi reali tra un pieno e il successivo (carburante) e tra la prima e l'ultima ricarica (elettrico)."""
    out = {}
    ric = [x for x in v.get("rifornimenti", []) if _au_n(x.get("km")) is not None and _au_n(x.get("quantita"))]
    car = sorted([x for x in ric if x.get("tipo") == "Carburante"], key=lambda x: _au_n(x["km"]))
    pieni = [x for x in car if x.get("pieno")]
    if len(pieni) >= 2:
        k0, k1 = _au_n(pieni[0]["km"]), _au_n(pieni[-1]["km"])
        lit = sum(_au_n(x["quantita"]) for x in car if k0 < _au_n(x["km"]) <= k1)
        if k1 > k0 and lit > 0:
            out["carburante"] = {"l100": lit / (k1 - k0) * 100, "kml": (k1 - k0) / lit, "km": k1 - k0, "litri": lit}
    ele = sorted([x for x in ric if x.get("tipo") == "Ricarica"], key=lambda x: _au_n(x["km"]))
    if len(ele) >= 2:
        k0, k1 = _au_n(ele[0]["km"]), _au_n(ele[-1]["km"])
        kwh = sum(_au_n(x["quantita"]) for x in ele[1:])
        if k1 > k0 and kwh > 0:
            out["ricarica"] = {"kwh100": kwh / (k1 - k0) * 100, "kmkwh": (k1 - k0) / kwh, "km": k1 - k0, "kwh": kwh}
    return out


def au_tco(v):
    """{anno: {categoria: euro}} dalle spese registrate."""
    t = {}

    def add(data, cat, imp):
        n = _au_n(imp)
        if n and data:
            t.setdefault(str(data)[:4], {}).setdefault(cat, 0.0)
            t[str(data)[:4]][cat] += n
    for x in v.get("rifornimenti", []):
        add(x.get("data"), "Carburante e ricariche", x.get("costo"))
    for x in v.get("interventi", []):
        add(x.get("data"), "Manutenzione", x.get("costo"))
    for x in v.get("spese", []):
        c = x.get("categoria")
        add(x.get("data"), "Scadenze fiscali (bollo, assicurazione, revisione)" if c in ("Bollo", "Assicurazione", "Revisione") else "Parcheggi, pedaggi e altro", x.get("importo"))
    return t


def tab_rifornimenti(v):
    voci = ["⛽ Rifornimenti e ricariche", "💸 Altre spese", "📊 Consumi e spese totali", "🧭 Viaggi e rimborsi"]
    sc = _au_scegli("Rifornimenti", voci, f"au_rif_{v['id']}")
    if sc == voci[0]:
        _au_elenco(v, "rifornimenti", "Rifornimenti", _spec_rifornimenti(v), lambda x: f"{'🔌' if x.get('tipo') == 'Ricarica' else '⛽'} {x.get('tipo', '')} · {_au_it(x.get('data'))}", lambda x: [("Km: " + x["km"]) if x.get("km") else "", x.get("luogo"),
                   ((x["quantita"] + (" kWh" if x.get("tipo") == "Ricarica" else " litri")) if x.get("quantita") else ""), ("Costo: " + _au_eur(x["costo"])) if x.get("costo") else "",
                   ("Prezzo: " + (_au_eur(x["prezzo"]) if x.get("prezzo") else (_au_eur(_au_n(x["costo"]) / _au_n(x["quantita"])) if _au_n(x.get("costo")) and _au_n(x.get("quantita")) else "")) + ("/kWh" if x.get("tipo") == "Ricarica" else "/L")) if (x.get("prezzo") or (x.get("costo") and x.get("quantita"))) else "",
                   ("Potenza max: " + x["potenza_max"] + " kW") if x.get("potenza_max") else "", "✅ Pieno" if x.get("pieno") else ""],
                   "Nessun rifornimento o ricarica registrato.", "Registra un rifornimento o una ricarica", ordine="data", icona="⛽")
    elif sc == voci[1]:
        _au_elenco(v, "spese", "Spese", _SPEC_SPESE, lambda x: f"{x.get('categoria', 'Spesa')} · {_au_it(x.get('data'))}", lambda x: [("Importo: " + _au_eur(x["importo"])) if x.get("importo") else "", x.get("note")],
                   "Nessuna spesa registrata: bollo, assicurazione, revisione, parcheggi, pedaggi, lavaggi, multe.", "Registra una spesa", icona="💸", aggiorna_km=False)
    elif sc == voci[3]:
        tab_viaggi(v)
    else:
        cons = au_consumi(v)
        if not cons:
            st.info("Per calcolare i consumi servono almeno **due pieni** (carburante) o **due ricariche** (elettrico) con i chilometri.")
        if "carburante" in cons:
            c = cons["carburante"]
            st.markdown(f"<div class='au-card'><b class='t'>⛽ Consumo reale</b><br><small><b>{c['l100']:.1f} l/100 km</b> · {c['kml']:.1f} km/l (su {int(c['km'])} km e {c['litri']:.0f} litri)</small></div>", unsafe_allow_html=True)
        if "ricarica" in cons:
            c = cons["ricarica"]
            st.markdown(f"<div class='au-card'><b class='t'>🔌 Consumo reale</b><br><small><b>{c['kwh100']:.1f} kWh/100 km</b> · {c['kmkwh']:.1f} km/kWh (su {int(c['km'])} km e {c['kwh']:.0f} kWh)</small></div>", unsafe_allow_html=True)
        tco = au_tco(v)
        if not tco:
            st.info("Registra rifornimenti, interventi e spese: qui vedi il costo totale di gestione.")
            return
        anni = sorted(tco, reverse=True)
        anno = st.selectbox("Anno", ["Tutti gli anni"] + anni, key=f"au_tcoa_{v['id']}")
        tot = {}
        for a_ in (anni if anno.startswith("Tutti") else [anno]):
            for cat, imp in tco[a_].items():
                tot[cat] = tot.get(cat, 0) + imp
        somma = sum(tot.values())
        st.markdown(f"### 💶 Costo totale: {_au_eur(somma)}")
        km_range = None
        kms = [_au_n(x.get("km")) for coll in ("rifornimenti", "interventi") for x in v.get(coll, []) if _au_n(x.get("km"))]
        if len(kms) >= 2 and max(kms) > min(kms):
            km_range = max(kms) - min(kms)
            if anno.startswith("Tutti"):
                st.markdown(f"🛣️ **Costo per chilometro:** {_au_eur(somma / km_range)} (su {int(km_range)} km)")
        try:
            import pandas as pd
            st.bar_chart(pd.DataFrame({"Euro": list(tot.values())}, index=list(tot.keys())))
        except Exception:
            pass
        for cat, imp in sorted(tot.items(), key=lambda kv: -kv[1]):
            st.markdown(f"- {cat}: **{_au_eur(imp)}** ({imp / somma * 100:.0f}%)")


def au_report_viaggi(v, anno, mese, tariffa):
    """Il testo del report dei viaggi di lavoro (per il rimborso chilometrico)."""
    voci = [x for x in v.get("viaggi", []) if x.get("categoria") == "Lavoro / aziendale" and str(x.get("data", ""))[:4] == anno and (mese == "Tutti" or str(x.get("data", ""))[5:7] == mese)]
    voci.sort(key=lambda x: x.get("data", ""))
    km = sum(_au_n(x.get("km")) or 0 for x in voci)
    righe = [f"RIMBORSO CHILOMETRICO — {anno}" + ("" if mese == "Tutti" else f"/{mese}"), f"Veicolo: {_au_nome(v)} {v.get('targa', '')}", ""]
    righe += [f"{_au_it(x.get('data'))} · {x.get('partenza', '')} → {x.get('arrivo', '')} · {x.get('km', '')} km" + (f" · {x['note']}" if x.get("note") else "") for x in voci]
    righe += ["", f"Km di lavoro: {km:.0f}", f"Tariffa: {_au_eur(tariffa)}/km" if tariffa else "Tariffa: da indicare", (f"Rimborso: {_au_eur(km * tariffa)}" if tariffa else "")]
    return "\n".join(x for x in righe)


def tab_viaggi(v):
    """Diario di bordo: i tragitti (personali o di lavoro) e il rimborso chilometrico dei viaggi di lavoro."""
    vid = v["id"]
    st.caption("Annota i tragitti: partenza, arrivo, km e se sono **personali** o di **lavoro**. Per i viaggi di lavoro calcolo il rimborso con la tariffa €/km che scrivi qui sotto.")
    with st.form(f"au_tar_{vid}", border=False):
        c1, c2 = st.columns([3, 2], gap="small")
        tar = c1.text_input("Tariffa di rimborso (€/km)", value=str(v.get("tariffa_km", "")), key=f"au_tarv_{vid}", placeholder="es. 0,38")
        if c2.form_submit_button("💾 Salva la tariffa", width="stretch"):
            n = _au_n(tar)
            _au_mod(vid, lambda x, n=n: x.__setitem__("tariffa_km", "" if n is None else str(n)), "Auto: tariffa")
            st.rerun()
    q = " ".join(x for x in (v.get("marca"), v.get("modello")) if x)
    if q:
        st.link_button("🔎 Cerca la tabella ACI dei costi chilometrici del mio modello", "https://www.google.com/search?q=" + urllib.parse.quote_plus(f"tabelle ACI costi chilometrici {q} rimborso"), width="stretch")
    st.caption("Le tabelle ACI ufficiali non sono incluse: le trovi sul sito dell'ACI; scrivi qui la tariffa del tuo modello.")
    _au_elenco(v, "viaggi", "Viaggi", _SPEC_VIAGGI, lambda x: f"{_au_it(x.get('data'))} · {x.get('partenza', '')} → {x.get('arrivo', '')}".strip(" ·→ "), lambda x: [("Km: " + x["km"]) if x.get("km") else "", x.get("categoria"), x.get("note")],
               "Nessun viaggio registrato.", "Registra un viaggio", icona="🧭", aggiorna_km=False)
    anni = sorted({str(x.get("data", ""))[:4] for x in v.get("viaggi", []) if x.get("data")}, reverse=True)
    if not anni:
        return
    st.markdown("#### 📊 Riepilogo")
    c1, c2 = st.columns(2, gap="small")
    anno = c1.selectbox("Anno", anni, key=f"au_vgi_a_{vid}")
    mese = c2.selectbox("Mese", ["Tutti"] + [f"{i:02d}" for i in range(1, 13)], key=f"au_vgi_m_{vid}")
    sel = [x for x in v.get("viaggi", []) if str(x.get("data", ""))[:4] == anno and (mese == "Tutti" or str(x.get("data", ""))[5:7] == mese)]
    km_l = sum(_au_n(x.get("km")) or 0 for x in sel if x.get("categoria") == "Lavoro / aziendale")
    km_p = sum(_au_n(x.get("km")) or 0 for x in sel if x.get("categoria") != "Lavoro / aziendale")
    tar = _au_n(v.get("tariffa_km"))
    st.markdown(f"<div class='au-card'><b class='t'>🧭 {anno}{'' if mese == 'Tutti' else '/' + mese}</b><br><small>Km personali: <b>{km_p:.0f}</b> · Km di lavoro: <b>{km_l:.0f}</b>" + (f"<br>💶 Rimborso dei viaggi di lavoro: <b>{_au_eur(km_l * tar)}</b> (a {_au_eur(tar)}/km)" if tar else "<br>Scrivi la tariffa per vedere il rimborso.") + "</small></div>", unsafe_allow_html=True)
    if km_l:
        _fa_inv_voce(f"au_rimb_{vid}", "📤 Invia il report del rimborso", f"Rimborso chilometrico {anno} – {_au_nome(v)}", [("Report", au_report_viaggi(v, anno, mese, tar))], [])


def tab_conducente(v=None):
    """Patente, visita medica, CQC, saldo punti e verbali (multe) con stato dei pagamenti e ricorsi. Sono dati della PERSONA, non del veicolo."""
    c = _au_cond()
    st.caption("Patente, visita medica e CQC con la scadenza (ti avviso **90, 30, 15 e 3 giorni prima**), il saldo punti e le multe con lo stato del pagamento e dei ricorsi. Valgono per te, non per un solo veicolo.")
    st.markdown("#### 🪪 Patenti")
    _au_elenco(c, "patenti", "Patenti", _SPEC_PATENTI, lambda x: f"Patente {x.get('categorie', '')} · {x.get('nome', '')}".strip(" ·"), lambda x: [("Scade il " + _au_it(x["scadenza"])) if x.get("scadenza") else "", ("Visita medica entro il " + _au_it(x["visita_medica"])) if x.get("visita_medica") else "",
               ("CQC fino al " + _au_it(x["cqc"])) if x.get("cqc") else "", ("Saldo punti: " + x["punti"]) if x.get("punti") else "", ("N. " + x["numero"]) if x.get("numero") else "", x.get("note")],
               "Nessuna patente registrata: scrivi la scadenza della patente e della visita medica, e l'eventuale CQC.", "Aggiungi una patente", ordine="scadenza", inverso=False, icona="🪪", aggiorna_km=False)
    for pt in c.get("patenti", []):
        for k, et in (("scadenza", "Patente"), ("visita_medica", "Visita medica"), ("cqc", "CQC")):
            d_ = _au_d(pt.get(k))
            if d_:
                g = (d_ - _au_oggi()).days
                stato = "r" if g < 0 else "g" if g <= 30 else "v"
                _carta_scad({"etichetta": f"🪪 {et} di {pt.get('nome', '')}", "data": d_, "giorni": g, "stato": stato}, v)
    st.markdown("#### 🧾 Verbali e multe")
    da_pagare = sum(_au_n(x.get("importo")) or 0 for x in c.get("verbali", []) if x.get("stato") == "Da pagare")
    if da_pagare:
        st.markdown(f"<div class='au-scad au-g'>💶 Da pagare in totale: {_au_eur(da_pagare)}</div>", unsafe_allow_html=True)
    st.caption("Sul verbale trovi i termini (indicativi: sconto se paghi entro 5 giorni dalla notifica; ricorso al Prefetto entro 60 giorni o al Giudice di pace entro 30). Controlla sempre il tuo verbale.")
    _au_elenco(c, "verbali", "Verbali", _SPEC_VERBALI, lambda x: f"{x.get('tipo') or 'Verbale'} · {_au_it(x.get('data'))}", lambda x: [("Importo: " + _au_eur(x["importo"])) if x.get("importo") else "", ("Stato: " + x["stato"]) if x.get("stato") else "",
               ("Pagare entro il " + _au_it(x["scadenza_pagamento"])) if x.get("scadenza_pagamento") else "", x.get("luogo"), ("Veicolo: " + x["veicolo"]) if x.get("veicolo") else "", ("Punti tolti: " + x["punti_tolti"]) if x.get("punti_tolti") else "", x.get("ricorso")],
               "Nessun verbale registrato. Fotografa la multa e allegala (tasto 📎): tieni insieme importo, scadenza e ricorso.", "Registra un verbale", ordine="data", icona="🧾", aggiorna_km=False)


def tab_ricambi(v):
    vid = v["id"]
    r = v.get("ricambi") or {}
    st.markdown("#### 🧰 Ricambi compatibili")
    with st.form(f"au_ric_{vid}", border=False):
        spec = [("spazzole", "Spazzole tergicristallo (misure)", "t", None), ("batteria12v", "Batteria 12V (codice)", "t", None), ("olio", "Olio motore (specifica)", "t", None), ("lampadine", "Lampadine (tipi)", "t", None),
                ("filtri", "Filtri (olio, aria, abitacolo)", "t", None), ("wallbox", "Wallbox domestica", "t", None), ("altro", "Altro", "a", None)]
        val = _au_widgets(spec, r, f"au_ricv_{vid}")
        if st.form_submit_button("💾 Salva i ricambi", type="primary", width="stretch"):
            _au_mod(vid, lambda x, val=val: x.__setitem__("ricambi", val), "Auto: ricambi")
            st.session_state["messaggio"] = "✅ Ricambi salvati."
            st.rerun()
    st.markdown("#### 📈 Valore stimato nel tempo")
    st.caption("Annota ogni tanto quanto vale il veicolo (da un sito di quotazioni o da un'offerta): vedi come cala col tempo e con i chilometri.")
    _au_elenco(v, "valutazioni", "Valutazioni", _SPEC_VALORE, lambda x: f"{_au_eur(x.get('valore'))} · {_au_it(x.get('data'))}", lambda x: [("Km: " + x["km"]) if x.get("km") else "", x.get("note")], "Nessuna valutazione registrata.", "Aggiungi una valutazione", icona="📈")
    punti = sorted([(x.get("data"), _au_n(x.get("valore"))) for x in v.get("valutazioni", []) if x.get("data") and _au_n(x.get("valore")) is not None])
    if len(punti) >= 2:
        try:
            import pandas as pd
            st.line_chart(pd.DataFrame({"Valore €": [p[1] for p in punti]}, index=[p[0] for p in punti]))
        except Exception:
            pass


def au_testo_sinistro(v, s):
    righe = [f"DENUNCIA DI SINISTRO — {datetime.now().strftime('%d/%m/%Y')}", "",
             f"Data e ora: {_au_it(s.get('data'))} {s.get('ora', '')}".strip(), f"Luogo: {s.get('luogo', '')}", "",
             "IL MIO VEICOLO", f"{_au_nome(v)} — targa {v.get('targa', '')}",
             f"Assicurazione: {((v.get('scadenze') or {}).get('assicurazione') or {}).get('compagnia', '')} — polizza {((v.get('scadenze') or {}).get('assicurazione') or {}).get('polizza', '')}", "",
             "L'ALTRO VEICOLO", f"Targa: {s.get('controparte_targa', '')}", f"Conducente: {s.get('controparte_nome', '')} — tel. {s.get('controparte_telefono', '')}", f"Compagnia: {s.get('controparte_compagnia', '')} — polizza {s.get('controparte_polizza', '')}", "",
             "COME È SUCCESSO", s.get("dinamica", ""), "", "DANNI AL MIO VEICOLO", s.get("danni", ""), "", f"Feriti: {'SÌ' if s.get('feriti') else 'no'}", f"Modulo CAI firmato da entrambi: {'sì' if s.get('concordato') else 'no'}"]
    if s.get("testimoni"):
        righe += ["", "TESTIMONI", s["testimoni"]]
    if s.get("note"):
        righe += ["", "NOTE", s["note"]]
    righe += ["", f"Foto allegate: {len(s.get('files') or [])}"]
    return "\n".join(x for x in righe)


def _extra_sinistro(v, s):
    if st.button("📝 Testo per l'assicuratore", key=f"au_txs_{s['id']}", width="stretch"):
        st.session_state["au_testo_sin"] = None if st.session_state.get("au_testo_sin") == s["id"] else s["id"]
        st.rerun()
    if st.session_state.get("au_testo_sin") == s["id"]:
        st.text_area("Copia e incolla nel messaggio all'assicuratore", value=au_testo_sinistro(v, s), height=300, key=f"au_txa_{s['id']}")


def tab_emergenza(v):
    voci = ["🚦 Spie del cruscotto", "📷 Diagnosi visiva (foto)", "🚨 Soccorso ed emergenza", "📝 Sinistro (CAI)"]
    sc = _au_scegli("Emergenza", voci, f"au_em_{v['id']}")
    if sc == voci[0]:
        ae_spie(v)
    elif sc == voci[1]:
        if "ad_pagina" in globals():
            ad_pagina(v)
        else:
            st.info("La diagnosi visiva non è disponibile.")
    elif sc == voci[2]:
        if "as_pagina" in globals():
            as_pagina(v)
        else:
            ae_procedure(v)
    else:
        st.info("🚨 In caso di incidente: sicurezza prima di tutto. Se ci sono feriti chiama il **112**.")
        ae_cai_guida()
        st.markdown("#### 📝 I miei sinistri")
        _au_elenco(v, "sinistri", "Sinistri", _SPEC_SINISTRO, lambda x: f"Sinistro del {_au_it(x.get('data'))}" + (f" · {x['luogo']}" if x.get("luogo") else ""), lambda x: [x.get("dinamica"), ("Controparte: " + " ".join(z for z in (x.get("controparte_targa"), x.get("controparte_nome")) if z)) if (x.get("controparte_targa") or x.get("controparte_nome")) else "",
                   "🚑 Con feriti" if x.get("feriti") else ""], "Nessun sinistro registrato. Registra i dati subito: poi crei il testo per l'assicuratore e alleghi le foto (tasto 📎).", "Registra un sinistro", icona="📝", aggiorna_km=False, extra_fn=_extra_sinistro)


# ---------------------------------------------------------------------------------------------------------------------
# il GARAGE: la schermata iniziale (foto, stato, scadenze in evidenza, accessi rapidi, ultima posizione)
# ---------------------------------------------------------------------------------------------------------------------
_AU_SEZ = ["🪪 Scheda e documenti", "⏰ Scadenze", "🔧 Manutenzione", "⛽ Rifornimenti e spese", "🧰 Ricambi e valore", "🆘 Emergenza", "👤 Patente e multe"]


def _au_vai(sezione, extra=None, vid=None):
    """Dal garage alla sezione scelta (e, se serve, alla sua sotto-scheda)."""
    st.session_state["au_vista"] = "sezione"
    st.session_state["au_sezione"] = sezione
    for k, val in (extra or {}).items():
        st.session_state[k] = val
    st.rerun()


def _au_ultimo_soh(v):
    punti = sorted([x for x in v.get("soh", []) if x.get("data") and _au_n(x.get("soh")) is not None], key=lambda x: x["data"])
    return (punti[-1]["soh"], punti[-1]["data"]) if punti else (None, None)


def garage(v):
    vid = v["id"]
    st.markdown("#### 🚘 Il tuo veicolo")
    c1, c2 = st.columns([2, 3], gap="small")
    with c1:
        mostrata = False
        ref = v.get("foto") or {}
        if ref.get("id"):
            dati = _sp_dati_file(ref)
            if dati:
                st.image(dati, width="stretch")
                mostrata = True
        if not mostrata:
            st.markdown(f"<div style='font-size:3.6rem;text-align:center;background:rgba(255,255,255,.75);border-radius:16px;padding:16px 0'>{_AU_EMOJI.get(v.get('tipo_veicolo'), '🚗')}</div>", unsafe_allow_html=True)
        if st.button("📷 Cambia foto" if mostrata else "📷 Aggiungi foto", key=f"au_foto_{vid}", width="stretch"):
            st.session_state["au_pannello"] = "foto"
            st.rerun()
    with c2:
        titolo = " ".join(x for x in (v.get("marca"), v.get("modello"), v.get("allestimento")) if x) or v.get("nome") or "Veicolo"
        riga2 = " · ".join(x for x in (v.get("alimentazione"), v.get("anno")) if x)
        stato = ""
        if _au_ha_batteria(v):
            sc = v.get("stato_carica") or {}
            soh, soh_d = _au_ultimo_soh(v)
            stato = "🔋 " + (f"SOC: <b>{_h_ap.escape(str(sc.get('soc')))}%</b>" + (f" ({_h_ap.escape(str(sc.get('km')))} km)" if sc.get("km") else "") if sc.get("soc") else "SOC: non indicato") + (f" · SoH <b>{_h_ap.escape(str(soh))}%</b>" if soh else "")
            if sc.get("data"):
                stato += f"<br><small>carica aggiornata il {_au_it(sc['data'])}</small>"
        elif v.get("km_attuali"):
            stato = f"🛣️ <b>{_h_ap.escape(v['km_attuali'])}</b> km"
        st.markdown(f"<div class='au-card'><b class='t'>{_h_ap.escape(titolo)}</b><br><small>{_h_ap.escape(riga2)}</small>" + (f"<br><small>Targa: <b>{_h_ap.escape(v['targa'])}</b></small>" if v.get("targa") else "") + (f"<hr style='margin:6px 0;border:none;border-top:1px solid #b2ebf2'>{stato}" if stato else "") + "</div>", unsafe_allow_html=True)
    if _au_ha_batteria(v):
        with st.expander("🔋 Aggiorna la carica (la leggi dal display dell'auto)"):
            with st.form(f"au_soc_{vid}", border=False):
                k1, k2 = st.columns(2, gap="small")
                soc = k1.text_input("Carica attuale (%)", value=str((v.get("stato_carica") or {}).get("soc", "")), key=f"au_soc_v_{vid}")
                kmr = k2.text_input("Autonomia indicata (km)", value=str((v.get("stato_carica") or {}).get("km", "")), key=f"au_soc_k_{vid}")
                if st.form_submit_button("💾 Salva", type="primary", width="stretch"):
                    n = _au_n(soc)
                    if n is None or not 0 <= n <= 100:
                        st.error("Scrivi la carica come numero da 0 a 100.")
                    else:
                        dd = {"soc": str(int(n)), "km": str(int(_au_n(kmr))) if _au_n(kmr) is not None else "", "data": _au_oggi().isoformat()}
                        _au_mod(vid, lambda x, dd=dd: x.__setitem__("stato_carica", dd), "Auto: carica")
                        st.rerun()
            st.caption("L'app non è collegata all'auto: carica e autonomia le scrivi tu.")
    # ---- scadenze in evidenza
    st.markdown("#### ⚠️ Scadenze in evidenza")
    sc_ = au_scadenze(v)
    if sc_:
        urgenti = [x for x in sc_ if x["stato"] in ("r", "g")][:3] or sc_[:2]
        for x in urgenti:
            _carta_scad(x, v)
        if st.button("⏰ Vedi tutte le scadenze", key=f"au_g_scad_{vid}", width="stretch"):
            _au_vai(_AU_SEZ[1])
    else:
        st.info("Nessuna scadenza impostata: tocca il bottone qui sotto per bollo, assicurazione, revisione, tagliando…")
        if st.button("⏰ Imposta le scadenze", key=f"au_g_scad_{vid}", type="primary", width="stretch"):
            _au_vai(_AU_SEZ[1])
    # ---- accessi rapidi
    st.markdown("#### 🛠️ Accessi rapidi")
    ric = "🔋 Ricarica e sessioni" if _au_ricarica(v) else "⛽ Rifornimenti"
    with st.container(key="au_hub"):
        t = [st.button("📖 Manuali e documenti", key="au_h_doc", width="stretch"), st.button("📷 Diagnosi spie (foto)", key="au_h_spie", width="stretch"),
             st.button(ric, key="au_h_ric", width="stretch"), st.button("🔧 Storico manutenzione", key="au_h_man", width="stretch"),
             st.button("🚨 Soccorso ed emergenza", key="au_h_soc", width="stretch"), st.button("📊 Spese e consumi (TCO)", key="au_h_tco", width="stretch"),
             st.button("🧰 Ricambi e valore", key="au_h_ric2", width="stretch"), st.button("🪪 Patente e multe", key="au_h_pat", width="stretch")]
    if t[0]:
        _au_vai(_AU_SEZ[0])
    elif t[1]:
        _au_vai(_AU_SEZ[5], {f"au_em_{vid}": "📷 Diagnosi visiva (foto)"})
    elif t[2]:
        _au_vai(_AU_SEZ[3], {f"au_rif_{vid}": "⛽ Rifornimenti e ricariche"})
    elif t[3]:
        _au_vai(_AU_SEZ[2], {f"au_man_{vid}": "🔧 Interventi e tagliandi"})
    elif t[4]:
        _au_vai(_AU_SEZ[5], {f"au_em_{vid}": "🚨 Soccorso ed emergenza"})
    elif t[5]:
        _au_vai(_AU_SEZ[3], {f"au_rif_{vid}": "📊 Consumi e spese totali"})
    elif t[6]:
        _au_vai(_AU_SEZ[4])
    elif t[7]:
        _au_vai(_AU_SEZ[6])
    st.caption("La diagnosi delle spie da una **foto** usa l'intelligenza artificiale (si attiva con la chiave nei Secrets); senza, la foto si confronta col catalogo delle spie.")
    # ---- ultima posizione
    pos = v.get("posizione") or {}
    st.markdown(f"<div class='au-card'>📍 <b>Ultima posizione salvata:</b> {_h_ap.escape(pos.get('testo') or 'nessuna')}" + (f"<br><small>{_au_it(pos.get('data'))}</small>" if pos.get("data") else "") + "</div>", unsafe_allow_html=True)
    with st.expander("📍 Salva dove hai parcheggiato"):
        if "as_inietta" in globals():
            as_inietta()
            st.markdown(_AS_CSS, unsafe_allow_html=True)
            st.markdown("<div class='as-gps' role='button' tabindex='0' data-as-azione='gps_campo' data-as-label='Dove (via, parcheggio, piano, posto)'>📍 Usa la mia posizione (GPS)</div>"
                        "<div data-as-msg style='display:none;margin:6px 0;font-weight:700;font-size:13.5px'></div>", unsafe_allow_html=True)
            st.caption("Il telefono trova dove sei (se consenti) e scrive le coordinate qui sotto; toccando «Salva la posizione» aggiungo anche l'indirizzo. **Oppure scrivi tu l'indirizzo.**")
        with st.form(f"au_pos_{vid}", border=False):
            testo = st.text_input("Dove (via, parcheggio, piano, posto)", value=pos.get("testo", ""), key=f"au_pos_t_{vid}", placeholder="es. Via Baveno, Torino")
            if st.form_submit_button("💾 Salva la posizione", type="primary", width="stretch"):
                dati_pos = au_posizione_da_testo(testo) if "au_posizione_da_testo" in globals() else {"testo": testo.strip()}
                dati_pos["data"] = _au_oggi().isoformat()
                _au_mod(vid, lambda x, d_=dati_pos: x.__setitem__("posizione", d_), "Auto: posizione")
                st.rerun()
    if pos.get("testo"):
        st.link_button("🗺️ Apri sulla mappa", au_mappa_url(pos) if "au_mappa_url" in globals() else "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(pos["testo"]), width="stretch")


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def schermata_auto():
    """La pagina «Auto»."""
    if "nav_barra" in globals():
        nav_barra("auto")
    if "_CA_CSS" in globals():
        st.markdown(_CA_CSS, unsafe_allow_html=True)
    st.markdown(_AU_CSS, unsafe_allow_html=True)
    _uri_auto = ih_uri("auto.webp", 360) if "ih_uri" in globals() else ""                 # l'icona verde e oro nell'intestazione (senza il riquadro di vetro); se manca, resta l'emoji
    _ico_auto = f"<img class='ico-img' alt='Auto' src='{_uri_auto}'>" if _uri_auto else "<div class='ico'>🚗</div>"
    st.markdown(f"<div class='au-hero'>{_ico_auto}<div><h1>Garage personale</h1><p>Documenti, scadenze, manutenzione, consumi ed emergenze dei tuoi mezzi</p></div></div>", unsafe_allow_html=True)
    if st.session_state.get("messaggio"):
        st.success(st.session_state.pop("messaggio"))
    if "pulsante_info" in globals():
        try:
            pulsante_info("auto")
        except Exception:
            pass
    a = _au_dati()
    vs = a["veicoli"]
    coda = st.session_state.setdefault("au_coda", [])
    # ---- scelta del veicolo
    sel = st.session_state.get("au_sel")
    v = next((x for x in vs if x["id"] == sel), vs[0] if vs else None)
    if vs:
        et = [_au_etichetta(x) for x in vs]
        cur = _au_etichetta(v)
        if len(vs) > 1:
            if st.session_state.get("au_vpill") not in et:
                st.session_state.pop("au_vpill", None)
            if hasattr(st, "pills"):
                scelta = st.pills("Quale veicolo", et, key="au_vpill", label_visibility="collapsed") if "au_vpill" in st.session_state else st.pills("Quale veicolo", et, default=cur, key="au_vpill", label_visibility="collapsed")
            else:
                scelta = st.radio("Quale veicolo", et, index=et.index(cur), horizontal=True, key="au_vpill", label_visibility="collapsed")
            if scelta in et:
                v = vs[et.index(scelta)]
        st.session_state["au_sel"] = v["id"]
    # ---- aggiungere un veicolo
    with st.expander("➕ Aggiungi un mezzo (auto, moto, scooter, monopattino, camion, bus…)", expanded=False):
        tipo_n = st.selectbox("Che mezzo è", _AU_TIPI, format_func=lambda x: f"{_AU_EMOJI.get(x, '🚘')} {x}", key="au_nuovo_tipo")
        micro_n = tipo_n in ("Monopattino elettrico", "Bicicletta elettrica (e-bike)")
        if micro_n:
            st.caption("Monopattini ed e-bike non hanno la Carta di Circolazione: inserisci i dati a mano (marca, modello, numero di serie o contrassegno, batteria, assicurazione).")
        else:
            st.caption("Carica la **Carta di Circolazione** (PDF o foto): la leggo e ti propongo targa, marca, modello, anno, alimentazione, potenza e classe. Oppure inserisci i dati a mano.")
            if st.button("📷 Carica la Carta di Circolazione (la leggo io)", key="au_pl", type="primary", width="stretch"):
                st.session_state["au_pannello"] = "libretto"
                st.rerun()
        if st.button("✍️ Inserisci a mano", key="au_man_v", type="primary" if micro_n else "secondary", width="stretch") and not any(c_["modo"] == "libretto_manuale" for c_ in coda):
            coda.insert(0, {"modo": "libretto_manuale", "nome": "", "dati": b"", "sha": "manuale" + uuid.uuid4().hex[:8], "tipo": tipo_n})
            st.session_state.pop("au_fin", None)
            st.rerun()
    if not vs and not st.session_state.get("au_pannello") and not coda:
        st.info("Ancora nessun veicolo. Apri **➕ Aggiungi un mezzo** e carica la Carta di Circolazione, oppure inserisci i dati a mano.")
    _au_pannello(v, coda)
    if coda:
        _au_finestra(coda)
    if not v:
        if "ad_pagina" in globals():
            if st.session_state.get("ad_libera"):
                return ad_pagina(None)
            if st.button("📷 Diagnosi visiva delle spie (senza veicolo)", key="ad_libera_b", width="stretch"):
                st.session_state["ad_libera"] = True
                st.rerun()
        if st.session_state.get("au_cond_libero"):
            _au_pannello(_au_cond(), coda)
            if st.button("← Chiudi", key="au_cond_chiudi", width="stretch"):
                st.session_state.pop("au_cond_libero", None)
                st.rerun()
            return tab_conducente(None)
        if st.button("🪪 Patente e multe (senza veicolo)", key="au_cond_b", width="stretch"):
            st.session_state["au_cond_libero"] = True
            st.rerun()
        return
    # ---- il veicolo scelto
    sc = au_scadenze(v)
    rosse, gialle = sum(1 for s in sc if s["stato"] == "r"), sum(1 for s in sc if s["stato"] == "g")
    if rosse or gialle:
        st.markdown(f"<div class='au-scad {'au-r' if rosse else 'au-g'}'>⏰ {'🔴 ' + str(rosse) + ' scadut' + ('a' if rosse == 1 else 'e') if rosse else ''}{' · ' if rosse and gialle else ''}{'🟡 ' + str(gialle) + ' in scadenza' if gialle else ''} — apri ⏰ Scadenze</div>", unsafe_allow_html=True)
    if st.session_state.get("au_vista") != "sezione":
        return garage(v)
    if st.button("← Torna al garage", key="au_garage", width="stretch"):
        st.session_state["au_vista"] = "garage"
        st.rerun()
    voci = _AU_SEZ
    scelta = _au_scegli("Che cosa vuoi vedere?", voci, "au_sezione")
    {voci[0]: tab_scheda, voci[1]: tab_scadenze, voci[2]: tab_manutenzione, voci[3]: tab_rifornimenti, voci[4]: tab_ricambi, voci[5]: tab_emergenza, voci[6]: tab_conducente}[scelta](v)


# ---- lo smistamento: «auto» va alla sua pagina (con il controllo dei permessi), il resto come prima
if "schermata_farmacia" in globals() and "_au_schermata_prima" not in globals():
    _au_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "auto":
            if "sv_nascoste" in globals() and "auto" in sv_nascoste():
                return sv_blocca("auto")
            return schermata_auto()
        return _au_schermata_prima()


# ---- la guida «Informazioni» della sezione
if "_NOMI_SEZIONI" in globals():
    _NOMI_SEZIONI.setdefault("auto", "🚗 Auto")
    _GUIDE.setdefault("auto", [
        ("🚗 Cos'è la sezione Auto",
         """Qui tieni **tutto quello che riguarda i tuoi mezzi**: auto, moto, ciclomotori, **monopattini ed e-bike**, furgoni, **camion e autobus**, camper, mezzi agricoli (benzina, diesel, GPL, metano, ibridi ed elettrici). Si apre dal bottone **🚗 Auto**, **prima di Utilità**.
In alto scegli il mezzo (se ne hai più di uno) e poi cosa vedere: **🪪 Scheda e documenti**, **⏰ Scadenze**, **🔧 Manutenzione** (con le **parti di usura**), **⛽ Rifornimenti e spese** (con **viaggi e rimborsi**), **🧰 Ricambi e valore**, **🆘 Emergenza**, **👤 Patente e multe**.""", "auto moto scooter monopattino bicicletta e-bike camion tir autobus furgone camper veicolo targa libretto mezzo"),
        ("➕ Aggiungere un veicolo",
         """1. Apri **🚗 Auto** → **➕ Aggiungi un mezzo**.
2. Tocca **📷 Carica la Carta di Circolazione** e scegli il PDF o la foto con il **pulsante arancione**. Lo leggo e ti propongo **targa, marca, modello, anno, alimentazione, potenza, classe, telaio**.
3. **Controlli e correggi**, poi **✅ Conferma e salva**. Il libretto resta nel cassetto dei documenti.
Se preferisci, **✍️ Inserisci a mano**. Per le elettriche e le plug-in aggiungi batteria (kWh), potenza di ricarica AC/DC e connettore.
*Non c'è il recupero automatico dalla targa: serve un servizio a pagamento.*""", "aggiungere veicolo carta di circolazione libretto targa leggere"),
        ("⏰ Scadenze e avvisi",
         """In **⏰ Scadenze** imposti **bollo**, **assicurazione**, **revisione**, **garanzie** (anche della batteria), **tagliando** (a data o a km) e il **cambio gomme**. Colori: 🟢 ok, 🟡 entro 30 giorni, 🔴 scaduta.
Ti avviso **30, 15 e 3 giorni prima**: la Home lampeggia e ricevi il promemoria sui canali scelti. Ci sono i link ai servizi ufficiali per **bollo**, **verifica assicurazione** e **revisione**.""", "scadenze bollo assicurazione revisione tagliando garanzia avvisi"),
        ("🔧 Manutenzione, ⛽ rifornimenti e spese",
         """**🔧 Manutenzione:** registra tagliandi e interventi con **data, km, costo, officina, garanzia sui ricambi** e allega la fattura o le foto (tasto **📎**). Ci sono **pneumatici** e, per elettriche/ibride, la **salute della batteria (SoH)** con grafico.
**⛽ Rifornimenti e spese:** registra rifornimenti e ricariche (kWh, costo, potenza). Con **due pieni** o **due ricariche** calcolo i **consumi reali** (l/100 km, kWh/100 km). **📊 Consumi e spese totali** mostra il costo totale per voce e per chilometro.""", "manutenzione tagliando rifornimenti ricariche consumi spese costo chilometro soh batteria"),
        ("🆘 Emergenza e sinistro",
         """**🚦 Spie del cruscotto:** cerca per nome o filtra per colore: per le rosse il **pericolo** è scritto per primo. **⚡ Procedure di emergenza:** batteria 12V scarica, cavo di ricarica bloccato, modalità tartaruga, fumo/fuoco/allagamento. **Mai toccare o tagliare i cavi arancioni** (alta tensione).
**📝 Sinistro (CAI):** guida passo passo, registri i dati, allegi le foto e crei il **testo pronto per l'assicuratore**. **📷 Diagnosi visiva:** fotografi il cruscotto (pulsante arancione: **📷 Scatta foto** o **🖼️ Dalla galleria**, anche di camion, TIR e autobus) e l'**intelligenza artificiale** riconosce la spia: se è rossa compare per primo il **PERICOLO**, poi nome, colore, urgenza, azioni e cause, con il **soccorso a un tocco**, il **112**, la chat per approfondire e il report da salvare o condividere. **Senza pagare:** puoi usare **la tua app di IA** (ChatGPT, Gemini, Claude, Copilot…) col tasto **📤 Manda foto e istruzioni alla mia IA**, oppure una **tua chiave** (per esempio la chiave gratuita di Gemini, o un modello gratuito di OpenRouter), che resta solo nella sessione e non viene salvata. Se l'amministratore mette **ANTHROPIC_API_KEY** nei Secrets, l'app usa quella (a suo costo, con i tetti giornalieri). In ogni caso resta il catalogo delle spie. **📚 Base condivisa:** ogni spia riconosciuta dall'IA, e ogni voce che aggiungi tu a mano (con dove l'hai verificata), entra in una base **a disposizione di tutte le persone che usano l'app** (solo testo, mai foto). La ricerca si fa prima lì, a parole, gratis e subito; se non c'è, chiedi all'IA o aggiungi tu la risposta. Le voci nuove sono «da verificare»: con **👍** da almeno 2 persone diverse (o dall'amministratore) diventano **✅ verificate**; con **👎** si segnalano gli errori. Se vuoi, scrivi **a mano il modello del mezzo** (marca, modello, anno) per una ricerca più precisa. L'IA può sbagliare: se la spia è rossa fermati comunque.""", "emergenza spie cruscotto sinistro cai incidente elettrica alta tensione"),
    ])
    _ID_GUIDA.setdefault("auto", ["au_cosa", "au_aggiungi", "au_scadenze", "au_manut", "au_emerg"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("auto", "au_cosa")
