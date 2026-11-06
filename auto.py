# -*- coding: utf-8 -*-
"""AUTO — la sezione dei veicoli (auto e moto: benzina, diesel, GPL, metano, ibride, plug-in, elettriche). Sta nella Home PRIMA di Utilità.

Per ogni veicolo:
• 🪪 Scheda e documenti: dati tecnici, Carta di Circolazione, assicurazione, certificato di proprietà… nel «cassetto digitale» (si carica con il PULSANTE ARANCIONE, lo leggo io, tu confermi); per le elettriche/ibride anche cavi e tessere di ricarica.
• ⏰ Scadenze: bollo, assicurazione, revisione, garanzie, tagliando (a data o a km), cambio gomme — 🟢 ok · 🟡 entro 30 giorni · 🔴 scaduta. Avvisi a 30, 15 e 3 giorni (Home che lampeggia + promemoria sui canali scelti).
• 🔧 Manutenzione: tagliandi e interventi (con costo, km, officina, garanzia, fattura), carrozzeria, pneumatici, salute della batteria (SoH) per elettriche e ibride.
• ⛽ Rifornimenti e spese: carburante e ricariche, consumi reali, costo per km, spese totali (TCO) con grafico.
• 🧰 Ricambi e valore: spazzole, batteria 12V, olio, lampadine, wallbox; valutazione nel tempo.
• 🆘 Emergenza: spie del cruscotto, procedure per auto elettriche/ibride (mai toccare i cavi arancioni), batteria 12V, fumo/fuoco, e l'assistente per il sinistro (CAI) con il testo pronto per l'assicuratore.
Ogni voce: 👁️ vedi/scarica il file · ✏️ correggi · 📤 invia · 🗑️ elimina · 📎 allega un file.
Cosa NON c'è (serve un servizio a pagamento o un'IA esterna): recupero automatico dei dati dalla targa, ricerca nel manuale con linguaggio naturale, diagnosi delle spie da foto. Al loro posto: lettura della Carta di Circolazione, link di ricerca del manuale, catalogo delle spie.
Dati in d['auto']['veicoli'] (personali, come Casa). Caricato dopo salute_esenzioni.py."""
import hashlib
import html as _h_au
import re
import uuid
from datetime import date, datetime, timedelta

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# registrazione della sezione: PRIMA di Utilità
# ---------------------------------------------------------------------------------------------------------------------
try:
    if "SEZIONI_NAV" in globals() and "auto" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(SEZIONI_NAV.index("utilita") if "utilita" in SEZIONI_NAV else len(SEZIONI_NAV), "auto")
    if "NOMI_NAV" in globals():
        NOMI_NAV["auto"] = "Auto"
    if "SV_SEZIONI" in globals() and "auto" not in SV_SEZIONI:
        _vecchie = list(SV_SEZIONI.items())
        SV_SEZIONI.clear()
        for k_, v_ in _vecchie:
            if k_ == "utilita":
                SV_SEZIONI["auto"] = "🚗 Auto"
            SV_SEZIONI[k_] = v_
        SV_SEZIONI.setdefault("auto", "🚗 Auto")
    if "_SV_DA_SEZIONE_HOME" in globals():
        _SV_DA_SEZIONE_HOME["auto"] = "auto"
except Exception:
    pass

_AU_CSS = """<style>
.au-hero{display:flex;align-items:center;gap:16px;background:linear-gradient(135deg,#26c6da 0%,#00838f 55%,#004d5a 100%);color:#fff;padding:18px 22px;border-radius:24px;margin:6px 0 12px;box-shadow:0 6px 18px rgba(0,60,70,.35)}
.au-hero .ico{font-size:3rem;line-height:1}.au-hero h1{margin:0;font-size:1.7rem;color:#fff}.au-hero p{margin:2px 0 0;font-size:.95rem;opacity:.95}
.au-card{background:rgba(255,255,255,.9);border-radius:16px;padding:10px 14px;margin:8px 0;color:#1b2b2b;border-left:6px solid #00acc1}
.au-card b.t{font-size:1.02rem}.au-card small{color:#33474a}
.au-scad{border-radius:14px;padding:9px 12px;margin:6px 0;font-weight:700}
.st-key-au_hub[data-testid='stVerticalBlock'],.st-key-au_hub [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:8px 0 12px}
.st-key-au_hub button{width:100% !important;min-height:62px !important;border-radius:18px !important;color:#fff !important;border:2px solid rgba(255,255,255,.55) !important;box-shadow:0 4px 0 rgba(0,0,0,.18),0 6px 14px rgba(0,0,0,.2) !important}
.st-key-au_hub button p{color:#fff !important;font-weight:900 !important;font-size:.95rem !important;line-height:1.12 !important;text-shadow:0 1px 3px rgba(0,0,0,.5);margin:0}
.st-key-au_h_doc button{background:linear-gradient(135deg,#42a5f5,#0d47a1) !important}.st-key-au_h_spie button{background:linear-gradient(135deg,#ffa726,#e65100) !important}
.st-key-au_h_ric button{background:linear-gradient(135deg,#26c6da,#00838f) !important}.st-key-au_h_man button{background:linear-gradient(135deg,#7e57c2,#4527a0) !important}
.st-key-au_h_soc button{background:linear-gradient(135deg,#ef5350,#b71c1c) !important}.st-key-au_h_tco button{background:linear-gradient(135deg,#66bb6a,#2e7d32) !important}
.st-key-au_h_ric2 button{background:linear-gradient(135deg,#8d6e63,#4e342e) !important}
.st-key-au_h_pat button{background:linear-gradient(135deg,#5c6bc0,#283593) !important}
.st-key-au_hub > div:nth-child(odd):last-child,.st-key-au_hub [data-testid='stVerticalBlock'] > div:nth-child(odd):last-child{grid-column:1 / -1}
.au-v{background:#e8f5e9;border-left:6px solid #2e7d32;color:#1b5e20}.au-g{background:#fff8e1;border-left:6px solid #f9a825;color:#6d4c00}.au-r{background:#ffebee;border-left:6px solid #c62828;color:#7f1111}.au-n{background:#eceff1;border-left:6px solid #90a4ae;color:#37474f}
</style>"""

_AU_TIPI = ["Auto", "Moto", "Ciclomotore / scooter", "Monopattino elettrico", "Bicicletta elettrica (e-bike)", "Furgone / veicolo commerciale", "Camion / TIR", "Autobus / pullman", "Camper", "Mezzo agricolo o da lavoro", "Altro mezzo"]
_AU_EMOJI = {"Auto": "🚗", "Moto": "🏍️", "Ciclomotore / scooter": "🛵", "Monopattino elettrico": "🛴", "Bicicletta elettrica (e-bike)": "🚲", "Furgone / veicolo commerciale": "🚐", "Camion / TIR": "🚚",
             "Autobus / pullman": "🚌", "Camper": "🚐", "Mezzo agricolo o da lavoro": "🚜", "Altro mezzo": "🚘"}
_AU_PARTI_USURA = ["Pastiglie freno anteriori", "Pastiglie freno posteriori", "Dischi freno", "Spazzole tergicristallo", "Filtro abitacolo / polline", "Filtro aria", "Liquido freni", "Liquido lavavetri",
                   "Liquido di raffreddamento", "Batteria 12V", "Cinghia o catena di distribuzione", "Catena e pignoni (moto, bici)", "Altro"]
_AU_ALIM = ["Benzina", "Diesel", "GPL", "Metano", "Ibrida (HEV)", "Ibrida plug-in (PHEV)", "Elettrica (BEV)"]
_AU_CONNETTORI = ["", "Type 2", "CCS Combo 2", "CHAdeMO", "Type 1", "Schuko / domestico", "Altro"]
_AU_DOC_TIPI = ["Carta di circolazione", "Certificato di proprietà", "Polizza assicurativa", "Bollo (ricevuta)", "Revisione (certificato)", "Garanzia", "Delega o permesso ZTL", "Fattura o ricevuta", "Perizia o sinistro", "Altro"]
_AU_DOC_ICONE = {"Carta di circolazione": "🪪", "Certificato di proprietà": "📜", "Polizza assicurativa": "🛡️", "Bollo (ricevuta)": "💶", "Revisione (certificato)": "🔍", "Garanzia": "🧾", "Delega o permesso ZTL": "🅿️",
                 "Fattura o ricevuta": "🧾", "Perizia o sinistro": "📝", "Altro": "📄"}
_AU_INT_CAT = ["Tagliando", "Meccanica (freni, distribuzione, frizione…)", "Impianto alta tensione", "Batteria 12V", "Batteria di trazione", "Carrozzeria e cristalli", "Pneumatici", "Altro"]
_AU_SPESE_CAT = ["Bollo", "Assicurazione", "Revisione", "Parcheggio", "Pedaggio", "Lavaggio", "Multa", "Altro"]
_AU_STAG = ["Estive", "Invernali", "4 stagioni", "Estive EV (bassa resistenza)", "Invernali EV (bassa resistenza)"]
_AU_RIC_LUOGO = ["Casa", "Colonnina pubblica AC", "Colonnina rapida DC", "Lavoro", "Altro"]

# ---------------------------------------------------------------------------------------------------------------------
# piccole utilità
# ---------------------------------------------------------------------------------------------------------------------
def _au_d(x):
    try:
        return date.fromisoformat(str(x)[:10]) if x else None
    except (TypeError, ValueError):
        return None


def _au_it(x):
    d_ = _au_d(x)
    return d_.strftime("%d/%m/%Y") if d_ else ""


def _au_n(x):
    """Numero da un testo («1.234,50», «45,2», «45.2»); None se vuoto o non valido."""
    s = str(x if x is not None else "").strip().replace("€", "").replace(" ", "")
    if not s:
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):                    # «44.000» è quarantaquattromila (punto delle migliaia), non 44
        s = s.replace(".", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _au_eur(x):
    n = _au_n(x) if not isinstance(x, (int, float)) else float(x)
    return "" if n is None else f"{n:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _au_oggi():
    try:
        return oggi()
    except Exception:
        return date.today()


def _au_micro(v):
    """Monopattini e biciclette elettriche: batteria al litio a bassa tensione (non alta tensione)."""
    return (v or {}).get("tipo_veicolo") in ("Monopattino elettrico", "Bicicletta elettrica (e-bike)")


def _au_pesante(v):
    return (v or {}).get("tipo_veicolo") in ("Camion / TIR", "Autobus / pullman")


def _au_solo_elettrico(v):
    return str(v.get("alimentazione", "")).startswith("Elettrica")


def _au_e_ev(v):
    """Veicolo elettrico con ALTA TENSIONE (auto, moto, furgoni, bus…): non i monopattini e le e-bike."""
    return _au_solo_elettrico(v) and not _au_micro(v)


def _au_ha_batteria(v):
    return str(v.get("alimentazione", "")).startswith(("Elettrica", "Ibrida")) or _au_micro(v)


def _au_ricarica(v):
    return str(v.get("alimentazione", "")).startswith(("Elettrica", "Ibrida plug"))


def _au_nome(v):
    return " ".join(x for x in (v.get("marca"), v.get("modello")) if x) or v.get("nome") or "Veicolo"


def _au_etichetta(v):
    return _AU_EMOJI.get(v.get("tipo_veicolo"), "🚗") + " " + (v.get("nome") or _au_nome(v)) + (f" · {v['targa']}" if v.get("targa") else "")


# ---------------------------------------------------------------------------------------------------------------------
# i dati
# ---------------------------------------------------------------------------------------------------------------------
def _au_dati():
    try:
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
    except Exception:
        return {"veicoli": []}
    a = dict(d.get("auto") or {})
    a.setdefault("veicoli", [])
    return a


def _au_salva(fn, msg):
    def _m(d):
        a = d.setdefault("auto", {})
        a.setdefault("veicoli", [])
        fn(a)
    salva(_m, msg)


def _au_cond(a=None):
    """Il «conducente»: patente, visita medica, CQC, punti e verbali. È un contenitore a parte (id «cond»), che si usa come un veicolo."""
    a = a if a is not None else _au_dati()
    c = dict(a.get("conducente") or {})
    c["id"] = "cond"
    c["nome"] = "Conducente"
    c.setdefault("patenti", [])
    c.setdefault("verbali", [])
    return c


def _au_mod(vid, fn, msg):
    """Modifica UN veicolo: fn(veicolo). Con vid «cond» modifica il conducente (patente e verbali)."""
    def _f(a):
        if vid == "cond":
            c = a.setdefault("conducente", {"id": "cond"})
            c.setdefault("patenti", [])
            c.setdefault("verbali", [])
            fn(c)
            return
        for v in a["veicoli"]:
            if v.get("id") == vid:
                fn(v)
    _au_salva(_f, msg)


# ---------------------------------------------------------------------------------------------------------------------
# moduli «a campi»: ogni elenco (interventi, rifornimenti…) è descritto da una lista di campi
# ---------------------------------------------------------------------------------------------------------------------
def _au_widgets(spec, val, chiave):
    """Disegna i campi di una lista e ritorna i valori. kind: t testo, a testo lungo, n numero, d data, s scelta, b sì/no."""
    out = {}
    for k, lab, kind, extra in spec:
        cur = val.get(k)
        kk = f"{chiave}_{k}"
        if kind == "t":
            out[k] = st.text_input(lab, value=str(cur or ""), key=kk).strip()
        elif kind == "a":
            out[k] = st.text_area(lab, value=str(cur or ""), key=kk, height=80).strip()
        elif kind == "n":
            t = st.text_input(lab, value=str(cur if cur not in (None, "") else ""), key=kk, placeholder=extra or "")
            n = _au_n(t)
            out[k] = "" if n is None else (str(int(n)) if float(n).is_integer() else str(n))
        elif kind == "d":
            x = st.date_input(lab, value=_au_d(cur), format="DD/MM/YYYY", key=kk)
            out[k] = x.isoformat() if x else ""
        elif kind == "s":
            opz = list(extra)
            out[k] = st.selectbox(lab, opz, index=opz.index(cur) if cur in opz else 0, key=kk)
        elif kind == "b":
            out[k] = bool(st.checkbox(lab, value=bool(cur), key=kk))
    return out


def _au_f_allegati(vid, coll, it):
    """I file di una voce: vedi/scarica e togli."""
    files = list(it.get("files") or [])
    if not files:
        return
    vedi = st.session_state.setdefault("au_vedi", [])
    for ref in files:
        c1, c2 = st.columns([4, 1], gap="small")
        aperto = ref.get("id") in vedi
        icona = "📄" if str(ref.get("mime", "")).endswith("pdf") else "🖼️"
        if c1.button(("🙈 Chiudi " if aperto else f"{icona} ") + (ref.get("nome") or "file")[:34], key=f"au_fv_{it['id']}_{ref.get('id')}", width="stretch"):
            vedi.remove(ref["id"]) if aperto else vedi.append(ref["id"])
            st.rerun()
        if c2.button("🗑️", key=f"au_fd_{it['id']}_{ref.get('id')}", width="stretch", help="Togli questo file"):
            _au_dialogo_togli_file(vid, coll, it["id"], ref)
        if aperto:
            _sp_mostra(ref)


def _au_dialogo_togli_file(vid, coll, iid, ref):
    def _finestra():
        st.warning(f"Togliere il file **{_h_au.escape(ref.get('nome') or '')}**? Verrà cancellato dall'app.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"au_fdy_{ref.get('id')}", type="primary", width="stretch"):
            def _fn(v):
                for x in v.get(coll, []):
                    if x.get("id") == iid:
                        x["files"] = [r for r in x.get("files", []) if r.get("id") != ref.get("id")]
            _au_mod(vid, _fn, "Auto: file tolto")
            try:
                _fa_cancella_files([ref["id"]])
            except Exception:
                pass
            st.rerun()
        if s2.button("No", key=f"au_fdn_{ref.get('id')}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Togli il file")(_finestra)()


def _au_dialogo_form(vid, coll, titolo_finestra, spec, it=None, aggiorna_km=True):
    """Aggiungere o correggere una voce di un elenco."""
    def _finestra():
        with st.form(f"au_form_{coll}_{(it or {}).get('id', 'nuovo')}", border=False):
            val = _au_widgets(spec, it or {}, f"au_{coll}_{(it or {}).get('id', 'n')}")
            ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
        if ok:
            def _fn(v, val=val, iid=(it or {}).get("id")):
                lista = list(v.get(coll, []))
                if iid:
                    for x in lista:
                        if x.get("id") == iid:
                            x.update(val)
                else:
                    lista.append(dict(val, id=uuid.uuid4().hex[:10], files=[]))
                v[coll] = lista
                km = _au_n(val.get("km"))
                if aggiorna_km and km and km > (_au_n(v.get("km_attuali")) or 0):
                    v["km_attuali"] = str(int(km))
            _au_mod(vid, _fn, f"Auto: {coll}")
            st.session_state["messaggio"] = "✅ Salvato."
            st.rerun()
    st.dialog(titolo_finestra)(_finestra)()


def _au_dialogo_togli(vid, coll, iid, titolo):
    def _finestra():
        st.warning(f"Eliminare **{_h_au.escape(titolo)}**?")
        st.caption("I file allegati verranno cancellati.")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=f"au_del_si_{iid}", type="primary", width="stretch"):
            ids = []

            def _fn(v):
                for x in v.get(coll, []):
                    if x.get("id") == iid:
                        ids.extend(r["id"] for r in x.get("files", []) if r.get("id"))
                v[coll] = [x for x in v.get(coll, []) if x.get("id") != iid]
            _au_mod(vid, _fn, f"Auto: {coll} eliminata")
            if ids:
                try:
                    _fa_cancella_files(ids)
                except Exception:
                    pass
            st.session_state["messaggio"] = "🗑️ Eliminato."
            st.rerun()
        if s2.button("No, tienila", key=f"au_del_no_{iid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Elimina")(_finestra)()


def _au_elenco(v, coll, titolo_sez, spec, titolo_fn, righe_fn, vuoto, nome_nuovo, ordine="data", inverso=True, filtro=None, aggiorna_km=True, icona="📄", extra_fn=None):
    """Un elenco completo: ➕ aggiungi, e per ogni voce 📎 allega · ✏️ correggi · 📤 invia · 🗑️ elimina (con i file allegati visibili)."""
    vid = v["id"]
    if st.button(f"➕ {nome_nuovo}", key=f"au_add_{coll}_{vid}", type="primary", width="stretch"):
        _au_dialogo_form(vid, coll, nome_nuovo, spec, None, aggiorna_km)
    voci = [x for x in v.get(coll, []) if (filtro is None or filtro(x))]
    if not voci:
        st.info(vuoto)
        return
    voci = sorted(voci, key=lambda x: (str(x.get(ordine) or ""), x.get("id", "")), reverse=inverso)
    for it in voci:
        righe = [r for r in righe_fn(it) if r]
        st.markdown(f"<div class='au-card'><b class='t'>{icona} {_h_au.escape(titolo_fn(it))}</b>" + "".join(f"<br><small>{_h_au.escape(r)}</small>" for r in righe) + "</div>", unsafe_allow_html=True)
        _au_f_allegati(vid, coll, it)
        b1, b2 = st.columns(2, gap="small")
        if b1.button("📎 Allega un file", key=f"au_all_{it['id']}", width="stretch"):
            st.session_state["au_allega"] = {"vid": vid, "coll": coll, "id": it["id"], "titolo": titolo_fn(it)}
            st.rerun()
        if b2.button("✏️ Correggi", key=f"au_cor_{it['id']}", width="stretch"):
            _au_dialogo_form(vid, coll, "Correggi", spec, it, aggiorna_km)
        b3, b4 = st.columns(2, gap="small")
        with b3:
            _fa_inv_voce(f"au_{it['id']}", "📤 Invia", f"{titolo_fn(it)} – {_au_nome(v)}", [(k, it.get(k)) for k, _l, kind, _e in spec if it.get(k) not in (None, "", False)], list(it.get("files") or []))
        if b4.button("🗑️ Elimina", key=f"au_del_{it['id']}", width="stretch"):
            _au_dialogo_togli(vid, coll, it["id"], titolo_fn(it))
        if extra_fn:
            extra_fn(v, it)


# ---------------------------------------------------------------------------------------------------------------------
# lettura della Carta di Circolazione e dei documenti
# ---------------------------------------------------------------------------------------------------------------------
def au_leggi_libretto(testo):
    """Legge una Carta di Circolazione (libretto): targa, marca, modello, telaio, prima immatricolazione, cilindrata, kW, alimentazione, classe Euro. Niente è definitivo: si conferma."""
    t = testo or ""
    campi = {}

    def metti(k, v, aff="media"):
        v = (v or "").strip(" .:-\t")
        if v:
            campi[k] = {"valore": v, "affidabilita": aff}
    m = re.search(r"\b([A-Z]{2})\s?(\d{3})\s?([A-Z]{2})\b", t)
    if m:
        metti("targa", m.group(1) + m.group(2) + m.group(3), "alta")
    else:
        m = re.search(r"\b([A-Z]{2})\s?(\d{5,6})\b", t)
        if m:
            metti("targa", m.group(1) + m.group(2), "media")

    def campo(sigla):
        mm = re.search(r"(?im)(?:^|\s|\()" + sigla + r"\)?[\s\.:\-]+([A-Z0-9][^\n]{1,40})", t)
        return re.split(r"\s{2,}|\t", mm.group(1))[0].strip() if mm else ""
    metti("marca", campo(r"D\.?\s?1"), "alta")
    modello = campo(r"D\.?\s?3") or campo(r"D\.?\s?2")
    metti("modello", modello)
    v17 = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", t)
    metti("telaio", v17.group(1) if v17 else campo("E"), "alta" if v17 else "media")
    imm = re.search(r"(?im)(?:^|\s|\()B\)?[\s\.:\-]+(\d{2})[/.\-](\d{2})[/.\-](\d{4})", t) or re.search(r"(?i)prima immatricolazione[^\d]{0,20}(\d{2})[/.\-](\d{2})[/.\-](\d{4})", t)
    if imm:
        metti("immatricolazione", f"{imm.group(3)}-{imm.group(2)}-{imm.group(1)}", "alta")
        metti("anno", imm.group(3), "alta")
    cil = re.search(r"(?im)(?:^|\s|\()P\.?\s?1\)?[\s\.:\-]+(\d{3,4})\b", t)
    metti("cilindrata", cil.group(1) if cil else "")
    kw = re.search(r"(?im)(?:^|\s|\()P\.?\s?2\)?[\s\.:\-]+(\d{1,3}(?:[.,]\d{1,2})?)\b", t)
    if kw:
        metti("kw", kw.group(1).replace(",", "."))
    alim = campo(r"P\.?\s?3").lower() or t.lower()
    tl = t.lower()
    if "ibrid" in alim or "ibrid" in tl:
        metti("alimentazione", "Ibrida plug-in (PHEV)" if re.search(r"plug|ricaricabile|esterna", tl) else "Ibrida (HEV)")
    elif re.search(r"elettric|elettricit", alim):
        metti("alimentazione", "Elettrica (BEV)")
    elif re.search(r"gasolio|diesel", alim):
        metti("alimentazione", "Diesel")
    elif "gpl" in alim:
        metti("alimentazione", "GPL")
    elif "metano" in alim:
        metti("alimentazione", "Metano")
    elif "benzina" in alim:
        metti("alimentazione", "Benzina")
    eu = re.search(r"(?i)euro\s*([0-9])", t)
    if eu:
        metti("classe_euro", "Euro " + eu.group(1))
    return campi


def au_leggi_doc(testo, tipo=""):
    """Dati utili da un documento del veicolo: compagnia, numero di polizza, importo, date (di emissione e di scadenza)."""
    t = testo or ""
    campi = {}

    def metti(k, v, aff="media"):
        if v:
            campi[k] = {"valore": v, "affidabilita": aff}
    try:
        date_t = _sp_date_nel_testo(t, _au_oggi() + timedelta(days=3650))
    except Exception:
        date_t = []
    scad = [d_ for d_, ctx in date_t if re.search(r"scadenza|scade|valid[oa] (?:fino|sino)? ?al|al\b|termine|entro", ctx)]
    emis = [d_ for d_, ctx in date_t if re.search(r"emess|data|decorrenza|dal\b|rilasciat", ctx) and d_ <= _au_oggi()]
    if scad:
        metti("scadenza", max(scad).isoformat())
    if emis:
        metti("data", min(emis).isoformat())
    pol = re.search(r"(?i)polizza\s*(?:n[°.º]?|numero)?\s*[:\-]?\s*([A-Za-z0-9/\-\.]{5,24})", t)
    if pol:
        metti("titolo", "Polizza " + pol.group(1))
    comp = re.search(r"(?i)\b(Generali|Unipol(?:sai)?|Allianz|AXA|Zurich|Reale Mutua|Cattolica|Groupama|Sara|Vittoria|Linear|Genertel|Direct Line|UnipolSai|Verti|Hdi|Itas|Poste Assicura)\b", t)
    if comp:
        metti("compagnia", comp.group(1))
    imp = re.search(r"(?i)(?:totale|premio|importo)[^\d]{0,25}(\d{1,5}[.,]\d{2})", t)
    if imp:
        metti("importo", imp.group(1).replace(",", "."))
    if not campi.get("titolo") and tipo:
        metti("titolo", tipo)
    return campi


# ---------------------------------------------------------------------------------------------------------------------
# scadenze
# ---------------------------------------------------------------------------------------------------------------------
_AU_SCAD = [("bollo", "💶 Bollo auto", [("data", "Scade il", "d", None), ("importo", "Importo (€)", "n", None), ("note", "Note", "t", None)]),
            ("assicurazione", "🛡️ Assicurazione RCA", [("data", "Scade il", "d", None), ("compagnia", "Compagnia", "t", None), ("polizza", "Numero di polizza", "t", None), ("telefono", "Telefono della compagnia / assistenza", "t", None), ("importo", "Premio (€)", "n", None)]),
            ("revisione", "🔍 Revisione periodica", [("ultima", "Ultima revisione il", "d", None), ("km_ultima", "Km alla revisione", "n", None), ("data", "Prossima scadenza", "d", None)]),
            ("garanzia_auto", "🧾 Garanzia del veicolo", [("data", "Scade il", "d", None), ("km", "Oppure fino a (km)", "n", None), ("note", "Note", "t", None)]),
            ("garanzia_batteria", "🔋 Garanzia della batteria di trazione", [("data", "Scade il", "d", None), ("km", "Oppure fino a (km)", "n", "es. 160000"), ("note", "Note (es. 8 anni / 160.000 km)", "t", None)]),
            ("tagliando", "🔧 Prossimo tagliando", [("data", "Entro il", "d", None), ("km", "Oppure a (km)", "n", "es. 45000")])]


_AU_SCAD_TACHIGRAFO = ("tachigrafo", "⏱️ Tachigrafo (taratura)", [("ultima", "Ultima taratura il", "d", None), ("data", "Prossima taratura entro il", "d", None), ("note", "Note", "t", None)])


def au_scad_def(v):
    """Le scadenze che hanno senso per questo tipo di mezzo: tutte per auto e moto; senza bollo e revisione per monopattini e e-bike; con il tachigrafo per camion e autobus."""
    out = []
    for chiave, etichetta, spec in _AU_SCAD:
        if _au_micro(v) and chiave in ("bollo", "revisione"):
            continue
        if chiave == "garanzia_batteria" and not _au_ha_batteria(v):
            continue
        if _au_micro(v) and chiave == "garanzia_batteria":
            etichetta = "🔋 Garanzia della batteria"
        out.append((chiave, etichetta, spec))
    if _au_pesante(v):
        out.append(_AU_SCAD_TACHIGRAFO)
    return out


def _au_stato(giorni):
    return "r" if giorni < 0 else "g" if giorni <= 30 else "v"


def au_scadenze(v, oggi_=None):
    """[{chiave, etichetta, data, giorni, stato ('r' scaduta, 'g' entro 30 giorni, 'v' ok), testo}] ordinate. Include scadenze, documenti con scadenza, cambio gomme, tagliando a km."""
    oggi_ = oggi_ or _au_oggi()
    out = []
    for chiave, etichetta, _spec in au_scad_def(v):
        s = (v.get("scadenze") or {}).get(chiave) or {}
        d_ = _au_d(s.get("data"))
        if d_:
            g = (d_ - oggi_).days
            out.append({"chiave": chiave, "etichetta": etichetta, "data": d_, "giorni": g, "stato": _au_stato(g), "avvisa": s.get("avvisa") is not False})
        km_t, km_a = _au_n(s.get("km")), _au_n(v.get("km_attuali"))
        if chiave in ("tagliando", "garanzia_auto", "garanzia_batteria") and km_t and km_a:
            r = km_t - km_a
            stato = "r" if r < 0 else "g" if r <= 1000 else "v"
            out.append({"chiave": chiave + "_km", "etichetta": etichetta + " (km)", "data": None, "giorni": None, "km_restanti": r, "stato": stato, "avvisa": s.get("avvisa") is not False})
    for dc in v.get("documenti", []):
        d_ = _au_d(dc.get("scadenza"))
        sc_ = v.get("scadenze") or {}
        if d_ and ((dc.get("tipo") == "Polizza assicurativa" and (_au_d((sc_.get("assicurazione") or {}).get("data")) == d_)) or (dc.get("tipo") == "Revisione (certificato)" and (_au_d((sc_.get("revisione") or {}).get("data")) == d_))):
            continue                                                       # è la stessa scadenza già impostata: non si conta due volte
        if d_:
            g = (d_ - oggi_).days
            out.append({"chiave": "doc_" + dc["id"], "etichetta": f"{_AU_DOC_ICONE.get(dc.get('tipo'), '📄')} {dc.get('titolo') or dc.get('tipo')}", "data": d_, "giorni": g, "stato": _au_stato(g), "avvisa": True})
    for us in v.get("usura", []):
        d_ = _au_d(us.get("prossima_data"))
        if d_:
            g = (d_ - oggi_).days
            out.append({"chiave": "usura_" + us["id"], "etichetta": f"🧩 {us.get('parte', 'Parte')}: da sostituire/controllare", "data": d_, "giorni": g, "stato": _au_stato(g), "avvisa": True})
        km_t, km_a = _au_n(us.get("prossima_km")), _au_n(v.get("km_attuali"))
        if km_t and km_a:
            r = km_t - km_a
            out.append({"chiave": "usura_km_" + us["id"], "etichetta": f"🧩 {us.get('parte', 'Parte')} (km)", "data": None, "giorni": None, "km_restanti": r, "stato": "r" if r < 0 else "g" if r <= 1000 else "v", "avvisa": True})
    for pn in v.get("pneumatici", []):
        d_ = _au_d(pn.get("cambio_entro"))
        if d_ and pn.get("stato") != "In deposito":
            g = (d_ - oggi_).days
            out.append({"chiave": "gomme_" + pn["id"], "etichetta": f"🛞 Cambio gomme ({pn.get('tipo', '')})", "data": d_, "giorni": g, "stato": _au_stato(g), "avvisa": True})
    return sorted(out, key=lambda x: (x["giorni"] if x["giorni"] is not None else 99999, x["etichetta"]))


def au_scadenze_avviso(a, oggi_=None, entro=30):
    """Per la Home e per Salute-stile: [(giorni|None, testo)] di tutte le auto, scadute o entro N giorni."""
    oggi_ = oggi_ or _au_oggi()
    out = []
    molte = len(a.get("veicoli", [])) > 1
    cond = a.get("conducente") or {}
    for pt in cond.get("patenti", []):
        for k, et in (("scadenza", "Patente"), ("visita_medica", "Visita medica della patente"), ("cqc", "CQC")):
            d_ = _au_d(pt.get(k))
            if d_ and pt.get("avvisa") is not False:
                g = (d_ - oggi_).days
                if g <= 90:
                    q = "scaduta da %d giorni" % -g if g < 0 else "oggi" if g == 0 else f"tra {g} giorni"
                    out.append((g, f"🪪 {et} di {pt.get('nome', '')}: {q}"))
    for vb in cond.get("verbali", []):
        d_ = _au_d(vb.get("scadenza_pagamento"))
        if d_ and vb.get("stato") == "Da pagare":
            g = (d_ - oggi_).days
            if g <= 15:
                q = "scaduto da %d giorni" % -g if g < 0 else "oggi" if g == 0 else f"tra {g} giorni"
                out.append((g, f"🧾 Verbale da pagare ({vb.get('tipo') or vb.get('luogo') or 'multa'}, {_au_eur(vb.get('importo'))}): {q}"))
    for v in a.get("veicoli", []):
        for s in au_scadenze(v, oggi_):
            if not s.get("avvisa", True):
                continue
            if s["giorni"] is not None and s["giorni"] <= entro:
                q = "scaduta da %d giorni" % -s["giorni"] if s["giorni"] < 0 else "oggi" if s["giorni"] == 0 else f"tra {s['giorni']} giorni"
                out.append((s["giorni"], f"🚗 {s['etichetta']}" + (f" ({_au_nome(v)})" if molte else "") + f": {q}"))
            elif s["giorni"] is None and s["stato"] in ("r", "g"):
                r = s["km_restanti"]
                out.append((r // 100 if r else 0, f"🚗 {s['etichetta']}" + (f" ({_au_nome(v)})" if molte else "") + (": superati di %d km" % -r if r < 0 else f": mancano {int(r)} km")))
    return sorted(out, key=lambda x: x[0])
