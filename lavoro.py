# -*- coding: utf-8 -*-
"""LAVORO — una sezione nuova, fuori da Casa, con il suo bottone fra quelli delle pagine.

Dentro, per ora:
  💶 Buste paga   carichi la busta (PDF, foto o scansione: i modi sono gli stessi di Casa), l'app legge mese, lordo, netto e trattenute e te li propone: controlli e confermi.
                  Si possono anche inserire a mano (anche solo una voce). Per anno, mese per mese in ordine cronologico. Ogni busta si apre, si scarica, si corregge, si invia.
  📊 Anno per anno   grafici e tabelle: per ogni anno il netto ricevuto, il lordo, le trattenute totali (con 13ª, 14ª e voci a mano), confrontati con gli anni prima.
  Tutto si esporta (HTML e PDF) e si invia come il resto dell'app.
I dati restano dov'erano (documenti di tipo «Busta paga»): le buste già inserite si vedono qui. Le prossime voci del Lavoro si aggiungono in seguito.
Caricato da app_dispensa.py dopo casa.py, salute_plus.py e pagine_nav.py."""
import html as _h
from datetime import date

import streamlit as st

_LV_MESI = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
_LV_CSS = """<style>
.lv-hero{display:flex;align-items:center;gap:16px;background:linear-gradient(135deg,#78909c 0%,#455a64 55%,#263238 100%);color:#fff;padding:18px 22px;border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.18)}
.lv-hero .ico{font-size:3rem;line-height:1}
.lv-hero h1{margin:0;font-size:1.7rem;color:#fff}.lv-hero p{margin:2px 0 0;font-size:.95rem;opacity:.95}
.lv-card{background:rgba(255,255,255,.88);border-radius:16px;padding:10px 14px;margin:8px 0;color:#1b2b2b}
</style>"""

# ---------------------------------------------------------------------------------------------------------------------
# registrazione della sezione: bottoni, permessi, ordine
# ---------------------------------------------------------------------------------------------------------------------
try:
    if "SEZIONI_NAV" in globals() and "lavoro" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(SEZIONI_NAV.index("casa") + 1 if "casa" in SEZIONI_NAV else len(SEZIONI_NAV), "lavoro")
    if "NOMI_NAV" in globals():
        NOMI_NAV["lavoro"] = "Lavoro"
    if "SV_SEZIONI" in globals():
        SV_SEZIONI["lavoro"] = "💼 Lavoro"
    if "_SV_DA_SEZIONE_HOME" in globals():
        _SV_DA_SEZIONE_HOME["lavoro"] = "lavoro"
except Exception:
    pass


# ---------------------------------------------------------------------------------------------------------------------
# i dati: le buste paga, anno per anno
# ---------------------------------------------------------------------------------------------------------------------
def _lv_num(v):
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def lv_serie(docs):
    """[{id, anno, mese, mensilita, netto, lordo, trattenute, extra, stimato}] per ogni busta paga con il mese, dal più vecchio. Il terzo valore si ricava dagli altri due se manca."""
    out = []
    for d in docs:
        comp = str(d.get("competenza") or "")
        if d.get("tipo") != "Busta paga" or not (len(comp) == 7 and comp[4] == "-" and comp[:4].isdigit() and comp[5:].isdigit() and 1 <= int(comp[5:]) <= 12):
            continue
        n, l, t = _lv_num(d.get("netto")), _lv_num(d.get("lordo")), _lv_num(d.get("trattenute"))
        stimato = False
        if l is None and n is not None and t is not None:
            l, stimato = n + t, True
        elif t is None and l is not None and n is not None and n <= l:
            t, stimato = l - n, True
        elif n is None and l is not None and t is not None and t <= l:
            n, stimato = l - t, True
        extra = 0.0
        for v in (d.get("voci") or []):
            try:
                extra += float((v or {}).get("importo") or 0)
            except (ValueError, TypeError, AttributeError):
                pass
        if n is None and l is None and not extra:
            continue
        out.append({"id": d.get("id"), "anno": int(comp[:4]), "mese": int(comp[5:]), "mensilita": d.get("mensilita") or "Mensile", "netto": n or 0.0, "lordo": l, "trattenute": t,
                    "extra": round(extra, 2), "stimato": stimato})
    return sorted(out, key=lambda x: (x["anno"], x["mese"], x["mensilita"]))


def lv_riepilogo_anni(punti):
    """Per ogni anno: netto ricevuto (con 13ª, 14ª e voci a mano), lordo, trattenute, quanto pesano le trattenute sul lordo, e le differenze con l'anno prima (anche «a parità di mesi»)."""
    anni = sorted({p["anno"] for p in punti})
    out = []
    for a in anni:
        pa = [p for p in punti if p["anno"] == a]
        mens = [p for p in pa if p["mensilita"] in ("Mensile", "Altra")]
        mesi = sorted({p["mese"] for p in mens})
        netto = round(sum(p["netto"] + p["extra"] for p in pa), 2)
        lordo = round(sum(p["lordo"] for p in pa if p["lordo"] is not None), 2)
        tratt = round(sum(p["trattenute"] for p in pa if p["trattenute"] is not None), 2)
        r = {"anno": a, "n": len(pa), "mesi": mesi, "netto": netto, "lordo": lordo, "trattenute": tratt,
             "t13": round(sum(p["netto"] for p in pa if p["mensilita"] == "13ª mensilità"), 2), "t14": round(sum(p["netto"] for p in pa if p["mensilita"] == "14ª mensilità"), 2),
             "extra": round(sum(p["extra"] for p in pa), 2), "perc_tratt": round(tratt / lordo * 100, 1) if lordo else None,
             "media": round(sum(p["netto"] for p in mens) / len(mesi), 2) if mesi else None, "var": {}, "pari": {}}
        prec = out[-1] if out and out[-1]["anno"] == a - 1 else None
        if prec:
            for k in ("netto", "lordo", "trattenute"):
                if prec[k]:
                    r["var"][k] = (round(r[k] - prec[k], 2), round((r[k] - prec[k]) / prec[k] * 100, 1))
            if prec["media"] and r["media"]:
                r["var"]["media"] = (round(r["media"] - prec["media"], 2), round((r["media"] - prec["media"]) / prec["media"] * 100, 1))
            if mesi and len(mesi) < 12:                                          # anno non finito: si confronta con gli STESSI mesi dell'anno prima
                for k in ("netto", "lordo", "trattenute"):
                    ora = sum((p[k] or 0) for p in mens if p["mese"] in mesi)
                    pr = sum((p[k] or 0) for p in punti if p["anno"] == a - 1 and p["mensilita"] in ("Mensile", "Altra") and p["mese"] in mesi)
                    if pr:
                        r["pari"][k] = (round(ora - pr, 2), round((ora - pr) / pr * 100, 1))
        out.append(r)
    return out


def _lv_eur(v):
    return ("€ " + ca_importo_fmt(round(v, 2))) if v is not None else "—"


def lv_html_riepilogo(docs, titolo="Buste paga"):
    """Il riepilogo anno per anno e mese per mese, in HTML (da stampare, salvare come PDF o inviare)."""
    e = _h.escape
    punti = lv_serie(docs)
    anni = lv_riepilogo_anni(punti)
    righe_anni = "".join(
        f"<tr><td><b>{r['anno']}</b></td><td>{_lv_eur(r['netto'])}</td><td>{_lv_eur(r['lordo']) if r['lordo'] else '—'}</td><td>{_lv_eur(r['trattenute']) if r['trattenute'] else '—'}</td>"
        f"<td>{(str(r['perc_tratt']).replace('.', ',') + '%') if r['perc_tratt'] is not None else '—'}</td><td>{r['n']}</td></tr>" for r in reversed(anni))
    var_txt = ""
    for r in reversed(anni):
        if r["var"] or r["pari"]:
            parti = []
            for k, nome in (("netto", "netto"), ("lordo", "lordo"), ("trattenute", "trattenute")):
                x = (r["pari"] or r["var"]).get(k)
                if x:
                    parti.append(f"{nome} {_ca_fmt_var(x[0], x[1])}")
            var_txt += f"<p><b>{r['anno']}</b> rispetto al {r['anno'] - 1}" + (" (a parità di mesi)" if r["pari"] else "") + ": " + e("; ".join(parti)) + "</p>"
    mesi_righe = ""
    for p in punti:
        mesi_righe += (f"<tr><td>{_LV_MESI[p['mese'] - 1]} {p['anno']}</td><td>{e(p['mensilita'])}</td><td>{_lv_eur(p['lordo']) if p['lordo'] is not None else '—'}</td>"
                       f"<td>{_lv_eur(p['trattenute']) if p['trattenute'] is not None else '—'}</td><td>{_lv_eur(p['netto'])}</td><td>{_lv_eur(p['extra']) if p['extra'] else ''}</td></tr>")
    stile = ("body{font-family:Arial,sans-serif;font-size:10.5pt;color:#111}h1{font-size:16pt}h2{font-size:12pt;border-bottom:1px solid #888;margin-top:14pt}"
             "table{border-collapse:collapse;width:100%}td,th{border:1px solid #999;padding:3px 5px;text-align:right}td:first-child,th:first-child{text-align:left}.nota{font-size:8.5pt;color:#444;margin-top:12pt}")
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><title>{e(titolo)}</title><style>{stile}</style></head><body>"
            f"<h1>{e(titolo)}</h1><h2>Anno per anno</h2><table><tr><th>Anno</th><th>Netto ricevuto</th><th>Lordo</th><th>Trattenute</th><th>Trattenute/lordo</th><th>Buste</th></tr>{righe_anni}</table>{var_txt}"
            f"<h2>Mese per mese</h2><table><tr><th>Mese</th><th>Tipo</th><th>Lordo</th><th>Trattenute</th><th>Netto</th><th>Voci a mano</th></tr>{mesi_righe}</table>"
            "<p class='nota'>Creato dall'app «La nostra dispensa» con i dati inseriti o letti dalle buste paga: controllali sugli originali. Il netto dell'anno comprende 13ª, 14ª e voci aggiunte a mano.</p></body></html>")


def _lv_pdf(html_str):
    return sp_pdf_da_html(html_str) if "sp_pdf_da_html" in globals() else None


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
# il modulo «Controlla e conferma» per i documenti del Lavoro: i campi importanti sono sempre in vista
# ---------------------------------------------------------------------------------------------------------------------
_LV_INPS_TIPI = ["Estratto conto contributivo", "Certificazione Unica INPS", "Cedolino della pensione", "Domanda o pratica", "ISEE", "Disoccupazione (NASpI)", "Malattia o maternità", "Ricevuta", "Lettera o comunicazione", "Altro"]


def _lv_form_documento(chiave, d, ric, modo):
    """Il modulo per busta paga ('busta'), Certificazione Unica ('cu') e documento INPS ('inps'). Ritorna (inviato, valori)."""
    campi = (ric or {}).get("campi") or {}
    val = lambda k: (d or {}).get(k) if d else (campi.get(k) or {}).get("valore", "")

    def aff(k):
        c_ = campi.get(k) or {}
        return f" {_CA_AFF.get(c_.get('affidabilita'), '')}" if c_ and not d else ""
    v = {}
    with st.form(chiave, border=False):
        if modo == "busta":
            comp0 = val("competenza") or ""
            mese0 = int(comp0[5:]) if re.fullmatch(r"\d{4}-\d{2}", comp0) and 1 <= int(comp0[5:]) <= 12 else oggi().month
            anno0 = int(comp0[:4]) if re.fullmatch(r"\d{4}-\d{2}", comp0) else oggi().year
            b1, b2 = st.columns(2)
            mese_c = b1.selectbox("Mese di competenza" + aff("competenza"), list(range(1, 13)), index=mese0 - 1, format_func=lambda m_: _CA_MESI_NOMI_IT[m_ - 1].capitalize())
            anno_c = b2.number_input("Anno", min_value=1990, max_value=2100, value=anno0, step=1)
            men_l = ["Mensile", "13ª mensilità", "14ª mensilità", "Altra"]
            mensilita = st.selectbox("Che busta è" + aff("mensilita"), men_l, index=men_l.index(val("mensilita")) if val("mensilita") in men_l else 0)
            b3, b4, b5 = st.columns(3)
            netto = b3.text_input("Netto in busta (€)" + aff("netto"), value=val("netto") or "", placeholder="es. 1450,00")
            lordo = b4.text_input("Lordo (€)" + aff("lordo"), value=val("lordo") or "", placeholder="es. 1900,00")
            tratt = b5.text_input("Trattenute (€)" + aff("trattenute"), value=val("trattenute") or "", placeholder="es. 450,00")
            voci_t = st.text_area("Voci aggiunte a mano (una per riga: descrizione = importo)", value=_ca_voci_a_testo((d or {}).get("voci") if d else None), height=90,
                                  placeholder="Premio produzione = 150,00\nStraordinari = 80,00\nArretrati = 120,00", help="Servono per i grafici: si sommano al netto di quel mese.")
            ente = st.text_input("Datore di lavoro" + aff("ente"), value=val("ente") or "")
            try:
                lavori_f = lv_lavori(_ca_dati())
            except Exception:
                lavori_f = lv_lavori({})
            att_l = (d or {}).get("lavoro_id", "") if d else st.session_state.get("lv_lavoro_default", "")
            ids_l = [x["id"] for x in lavori_f]
            lavoro_id = st.selectbox("Di quale lavoro è", ids_l, index=ids_l.index(att_l) if att_l in ids_l else 0, format_func=lambda i: next((x["nome"] for x in lavori_f if x["id"] == i), "Lavoro principale")) if len(ids_l) > 1 else ""
            v = {"tipo": "Busta paga", "argomento": "Buste paga", "lavoro_id": lavoro_id, "competenza": f"{int(anno_c):04d}-{int(mese_c):02d}", "mensilita": mensilita, "netto": _ca_importo_da_testo(netto),
                 "lordo": _ca_importo_da_testo(lordo), "trattenute": _ca_importo_da_testo(tratt), "voci": _ca_voci_da_testo(voci_t), "ente": ente}
        elif modo == "cu":
            c1, c2 = st.columns(2)
            a_cu = c1.number_input("Anno della CU" + aff("cu_anno"), min_value=2000, max_value=2100, value=int(val("cu_anno") or (oggi().year)), step=1)
            a_imp = c2.number_input("Anno d'imposta (dei redditi)" + aff("cu_anno_imposta"), min_value=2000, max_value=2100, value=int(val("cu_anno_imposta") or (oggi().year - 1)), step=1)
            ente = st.text_input("Chi l'ha emessa (datore di lavoro o INPS)" + aff("ente"), value=val("ente") or "")
            red = st.text_input("Redditi di lavoro dipendente o pensione (€)" + aff("cu_reddito"), value=val("cu_reddito") or "", placeholder="es. 24500,00")
            rit = st.text_input("Ritenute IRPEF (€)" + aff("cu_ritenute"), value=val("cu_ritenute") or "", placeholder="es. 4200,00")
            c3, c4 = st.columns(2)
            a_reg = c3.text_input("Addizionale regionale (€)" + aff("cu_add_reg"), value=val("cu_add_reg") or "")
            a_com = c4.text_input("Addizionale comunale (€)" + aff("cu_add_com"), value=val("cu_add_com") or "")
            v = {"tipo": "Certificazione Unica (CU)", "argomento": "Certificazioni Uniche", "ente": ente, "cu_anno": str(int(a_cu)), "cu_anno_imposta": str(int(a_imp)), "cu_reddito": _ca_importo_da_testo(red),
                 "cu_ritenute": _ca_importo_da_testo(rit), "cu_add_reg": _ca_importo_da_testo(a_reg), "cu_add_com": _ca_importo_da_testo(a_com)}
        else:
            tipo_i = st.selectbox("Che documento INPS è", _LV_INPS_TIPI, index=_LV_INPS_TIPI.index(val("inps_tipo")) if val("inps_tipo") in _LV_INPS_TIPI else len(_LV_INPS_TIPI) - 1)
            v = {"tipo": "Documento INPS", "argomento": "INPS", "ente": "INPS", "inps_tipo": tipo_i}
        data_doc = st.date_input("Data del documento (facoltativa)" + aff("data_doc"), value=_data(val("data_doc")), format="DD/MM/YYYY")
        note = st.text_input("Note (facoltative)", value=(d or {}).get("note", "") if d else "")
        ok = st.form_submit_button("✅ Conferma e archivia" if not d else "💾 Salva le correzioni", type="primary", width="stretch")
    v.update({"data_doc": data_doc, "titolo": (d or {}).get("titolo", "") if d else "", "link": (d or {}).get("link", "") if d else "", "note": note})
    return ok, v


def _lv_aggiungi_a_mano(c, v, utente, ora):
    import uuid
    d = _ca_pulisci(v, _CAMPI_DOC)
    d.update({"id": uuid.uuid4().hex[:10], "creato_il": ora, "file": {}, "a_mano": True, "conferma": {"stato": "confermato", "da": utente, "il": ora, "modificati": [], "bene_proposto": ""}})
    d["titolo"] = d.get("titolo") or ca_titolo_auto(d)
    c.setdefault("documenti", []).append(d)
    return d


def _lv_a_mano(modo, etichetta):
    """«✍️ Inserisci a mano»: senza file. Una linguetta chiusa."""
    with st.expander(f"✍️ {etichetta}"):
        ok, v = _lv_form_documento(f"lv_mano_{modo}", None, None, modo)
        if ok:
            try:
                _ca_salva(lambda cc, v=v: _lv_aggiungi_a_mano(cc, v, (st.session_state.get("sess") or {}).get("nome", ""), _ca_ora()), "Lavoro: documento inserito a mano")
                st.session_state["messaggio"] = "✅ Inserito."
                st.rerun()
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare: {ex}")


_LV_CSS_SEZ = """<style>
.st-key-lv_sezione button{border-radius:999px !important;font-weight:800 !important;min-height:2.6rem}
</style>"""


def lv_esporta(docs, etichetta, chiave):
    """I tasti per scaricare (HTML e PDF) e inviare il riepilogo."""
    punti = lv_serie(docs)
    if not punti:
        return
    html_str = lv_html_riepilogo(docs)
    nome_file = f"buste_paga_{date.today().isoformat()}"
    st.download_button("📄 Scarica il riepilogo (da stampare o salvare come PDF)", html_str.encode("utf-8"), file_name=nome_file + ".html", mime="text/html", width="stretch", key=f"lv_dl_html_{chiave}")
    pdf = _lv_pdf(html_str)
    if pdf:
        st.download_button("📕 Scarica il PDF", pdf, file_name=nome_file + ".pdf", mime="application/pdf", width="stretch", key=f"lv_dl_pdf_{chiave}")
    if "inv_voce" in globals():
        anni = lv_riepilogo_anni(punti)
        testo = "Buste paga – riepilogo\n" + "\n".join(f"• {r['anno']}: netto {_lv_eur(r['netto'])}" + (f", lordo {_lv_eur(r['lordo'])}" if r["lordo"] else "") + (f", trattenute {_lv_eur(r['trattenute'])}" if r["trattenute"] else "") for r in reversed(anni))
        inv_voce(f"lv_invia_{chiave}", etichetta, "Buste paga: riepilogo", testo, lambda: ([(nome_file + ".pdf", "application/pdf", pdf)] if pdf else [(nome_file + ".html", "text/html", html_str.encode("utf-8"))]))


def lv_archivio_buste(c, sel_l=None):
    docs = lv_filtra_lavoro([d for d in c.get("documenti", []) if d.get("tipo") == "Busta paga"], sel_l)
    st.markdown(f"#### 📚 Le tue buste paga ({len(docs)})")
    if not docs:
        st.info("Ancora nessuna busta paga. Caricane una qui sopra, oppure inseriscila a mano.")
        return
    def chiave(d):
        return (str(d.get("competenza") or d.get("data_doc") or "")[:7], {"Mensile": 0, "Altra": 1, "13ª mensilità": 2, "14ª mensilità": 3}.get(d.get("mensilita"), 0))
    per_anno = {}
    for d in docs:
        per_anno.setdefault(chiave(d)[0][:4] or "senza data", []).append(d)
    for anno in sorted(per_anno, reverse=True):
        lista = sorted(per_anno[anno], key=chiave)
        tot = sum(float(x.get("netto") or 0) + sum(float((v or {}).get("importo") or 0) for v in (x.get("voci") or [])) for x in lista)
        with st.expander(f"📅 {anno} · {len(lista)} buste" + (f" · netto ricevuto {_lv_eur(tot)}" if tot else ""), expanded=False):
            for d in lista:
                _ca_riga_documento(d, {}, "lv", docs)
    lv_esporta(docs, "📤 Invia il riepilogo delle buste paga", "archivio")


# ---------------------------------------------------------------------------------------------------------------------
# 💼 PIÙ LAVORI: il principale e quelli secondari (secondo lavoro, collaborazioni, partita IVA…)
# ---------------------------------------------------------------------------------------------------------------------
def lv_lavori(c):
    """[{id, nome}]: il lavoro principale (id vuoto) e quelli aggiunti."""
    return [{"id": "", "nome": "Lavoro principale"}] + [x for x in (c.get("lavori") or []) if isinstance(x, dict) and x.get("id")]


def lv_nome_lavoro(c, lid):
    return next((x["nome"] for x in lv_lavori(c) if x["id"] == (lid or "")), "Lavoro principale")


def lv_filtra_lavoro(docs, sel):
    """sel None = tutti i lavori; altrimenti solo le buste di quel lavoro ('' = principale)."""
    return docs if sel is None else [d for d in docs if (d.get("lavoro_id") or "") == sel]


def _lv_dialogo_togli_lavoro(lid, nome):
    def _finestra():
        st.warning(f"Togliere il lavoro **{_h.escape(nome)}**? Le sue buste paga restano archiviate e passano al «Lavoro principale».")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"lv_lav_si_{lid}", type="primary", width="stretch"):
            def _fn(cc):
                cc["lavori"] = [x for x in cc.get("lavori", []) if x.get("id") != lid]
                for d in cc.get("documenti", []):
                    if d.get("lavoro_id") == lid:
                        d["lavoro_id"] = ""
            _ca_salva(_fn, "Lavoro: lavoro tolto")
            st.session_state.pop("lv_lavoro_p", None) if False else None
            st.rerun()
        if s2.button("No, tienilo", key=f"lv_lav_no_{lid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Togli il lavoro")(_finestra)()


def lv_selettore_lavoro(c, chiave="lv_lavoro_p"):
    """Le pillole «Tutti · Lavoro principale · Secondo lavoro…» e l'aggiunta di un altro lavoro. Ritorna l'id scelto ('' = principale, None = tutti)."""
    import uuid
    lavori = lv_lavori(c)
    sel = None
    if len(lavori) > 1:
        etichette = ["🔎 Tutti i lavori"] + [f"💼 {x['nome']}" for x in lavori]
        if hasattr(st, "pills"):
            scelta = st.pills("Quale lavoro", etichette, default=etichette[0], key=chiave, label_visibility="collapsed")
        else:
            scelta = st.radio("Quale lavoro", etichette, horizontal=True, key=chiave, label_visibility="collapsed")
        if scelta and scelta in etichette and etichette.index(scelta) > 0:
            sel = lavori[etichette.index(scelta) - 1]["id"]
    st.session_state["lv_lavoro_default"] = sel or ""
    with st.expander("➕ Aggiungi un altro lavoro (secondo lavoro, collaborazione…)"):
        st.caption("Per seguire **più lavori**: ognuno ha le sue buste paga e i suoi totali. Potrai guardare un lavoro alla volta oppure **tutti insieme**.")
        with st.form(f"{chiave}_nuovo", border=False, clear_on_submit=True):
            nome = st.text_input("Nome del lavoro", placeholder="es. Secondo lavoro, Pulizie, Collaborazione")
            ente = st.text_input("Datore di lavoro (facoltativo)")
            ok = st.form_submit_button("💾 Aggiungi il lavoro", type="primary", width="stretch")
        if ok:
            if not nome.strip():
                st.error("Scrivi un nome per il lavoro.")
            else:
                nv = {"id": uuid.uuid4().hex[:8], "nome": nome.strip(), "ente": ente.strip()}
                _ca_salva(lambda cc, nv=nv: cc.__setitem__("lavori", list(cc.get("lavori", [])) + [nv]), "Lavoro: nuovo lavoro")
                st.session_state["messaggio"] = f"✅ Aggiunto «{nv['nome']}»."
                st.rerun()
        for x in lavori[1:]:
            r1, r2 = st.columns([3, 1], gap="small")
            r1.markdown(f"💼 **{_h.escape(x['nome'])}**" + (f" · {_h.escape(x['ente'])}" if x.get("ente") else ""))
            if r2.button("🗑️", key=f"lv_lav_t_{x['id']}", width="stretch"):
                _lv_dialogo_togli_lavoro(x["id"], x["nome"])
    return sel


def lv_tab_buste(c):
    n = st.session_state.get("ca_giro", 0)
    sel_l = lv_selettore_lavoro(c)
    st.markdown("#### ➕ Carica una busta paga")
    st.caption("Carica il **PDF**, una **foto** o una **scansione** della busta paga: leggo mese, **lordo**, **netto** e **trattenute** e te li propongo. **Controlli, correggi e confermi tu.** Il file resta com'è.")
    up = _ca_pannello_caricamento(n)
    _ca_flusso_documento(c, [], n, up, None, None, lavoro="busta", finestra=True)
    _lv_a_mano("busta", "Inserisci a mano una busta paga o una voce")
    _ca_correzione(c, [])
    lv_archivio_buste(c, sel_l)


def _lv_grafici_dati(punti):
    try:
        import pandas as pd
    except Exception:
        return None
    return pd


def lv_tab_grafici(c):
    sel_l = lv_selettore_lavoro(c, "lv_lavoro_g")
    docs_b = lv_filtra_lavoro([d for d in c.get("documenti", []) if d.get("tipo") == "Busta paga"], sel_l)
    punti = lv_serie(docs_b)
    if len(punti) < 2:
        st.info("Per i grafici servono almeno due buste paga con il mese. Caricane altre (o inseriscile a mano) e compaiono qui.")
        return
    pd = _lv_grafici_dati(punti)
    if pd is None:
        st.warning("I grafici non sono disponibili su questo dispositivo.")
        return
    anni = lv_riepilogo_anni(punti)
    st.markdown("**💶 Anno per anno: netto ricevuto, lordo e trattenute**")
    df = pd.DataFrame({"Netto ricevuto": [r["netto"] for r in anni], "Lordo": [r["lordo"] or 0 for r in anni], "Trattenute": [r["trattenute"] or 0 for r in anni]}, index=[str(r["anno"]) for r in anni])
    st.bar_chart(df, stack=False, height=280)
    st.caption("Il **netto** comprende 13ª, 14ª e le voci aggiunte a mano. Per le buste in cui manca un valore lo ricavo dagli altri due (lordo − trattenute = netto).")
    perc = [(str(r["anno"]), r["perc_tratt"]) for r in anni if r["perc_tratt"] is not None]
    if len(perc) >= 2:
        st.markdown("**📉 Quanto pesano le trattenute sul lordo (%)**")
        st.line_chart(pd.DataFrame({"Trattenute sul lordo (%)": [v for _, v in perc]}, index=[a for a, _ in perc]), height=200)
    st.markdown("**📅 Il netto mese per mese, un colore per anno**")
    mesi_df = pd.DataFrame({str(a): [round(sum(p["netto"] + p["extra"] for p in punti if p["anno"] == a and p["mese"] == m), 2) for m in range(1, 13)] for a in sorted({p["anno"] for p in punti})}, index=_LV_MESI)
    st.bar_chart(mesi_df, stack=False, height=260)
    with st.expander("🔍 Il confronto con gli anni prima", expanded=True):
        for r in reversed(anni):
            parziale = 0 < len(r["mesi"]) < 12
            st.markdown(f"**{r['anno']}** · netto ricevuto **{_lv_eur(r['netto'])}**" + (f" · lordo {_lv_eur(r['lordo'])}" if r["lordo"] else "") + (f" · trattenute {_lv_eur(r['trattenute'])}" if r["trattenute"] else "")
                        + (f" · pesano il {str(r['perc_tratt']).replace('.', ',')}% del lordo" if r["perc_tratt"] is not None else "")
                        + (f" (mesi: {', '.join(_LV_MESI[m - 1] for m in r['mesi'])})" if parziale else ""))
            st.caption(f"{r['n']} buste" + (f" · media mensile del netto {_lv_eur(r['media'])}" if r["media"] else "") + (f" · 13ª {_lv_eur(r['t13'])}" if r["t13"] else "") + (f" · 14ª {_lv_eur(r['t14'])}" if r["t14"] else "")
                       + (f" · voci a mano {_lv_eur(r['extra'])}" if r["extra"] else ""))
            conf = r["pari"] if r["pari"] else r["var"]
            if conf:
                st.markdown(f"&nbsp;&nbsp;↳ rispetto al {r['anno'] - 1}" + (" **a parità di mesi**" if r["pari"] else "") + ": " + " · ".join(f"{nome} {_ca_fmt_var(conf[k][0], conf[k][1])}" for k, nome in (("netto", "netto"), ("lordo", "lordo"), ("trattenute", "trattenute")) if k in conf))
                if r["pari"]:
                    st.caption(f"Il {r['anno']} non è ancora finito: il confronto giusto è con gli stessi mesi del {r['anno'] - 1}.")
                if "media" in r["var"]:
                    st.markdown(f"&nbsp;&nbsp;↳ **media mensile** del netto: {_ca_fmt_var(r['var']['media'][0], r['var']['media'][1])}")
    if sel_l is None and len(lv_lavori(c)) > 1:                                                   # tutti i lavori: quanto viene da ciascuno
        st.markdown("**💼 Il netto di ogni lavoro, anno per anno**")
        per = {}
        for x in lv_lavori(c):
            for r in lv_riepilogo_anni(lv_serie([d for d in docs_b if (d.get("lavoro_id") or "") == x["id"]])):
                per.setdefault(x["nome"], {})[str(r["anno"])] = r["netto"]
        anni_t = sorted({a for v_ in per.values() for a in v_})
        if anni_t and pd is not None:
            st.bar_chart(pd.DataFrame({n_: [per[n_].get(a, 0) for a in anni_t] for n_ in per}, index=anni_t), stack=True, height=240)
    lv_esporta(docs_b, "📤 Invia il riepilogo anno per anno", "grafici")


# ---------------------------------------------------------------------------------------------------------------------
# 🤝 SINDACATO · CAF · PATRONATO … la rubrica del lavoro
# ---------------------------------------------------------------------------------------------------------------------
_RUB_CASA_TIPI = {"Caldaista": ("🔥", "#d84315"), "Idraulico": ("🚰", "#0277bd"), "Elettricista": ("💡", "#f9a825"), "Fabbro": ("🔑", "#6d4c41"), "Amministratore di condominio": ("🏢", "#455a64"),
                  "Portineria": ("🛎️", "#00838f"), "Assicurazione": ("🛡️", "#6a1b9a"), "Agenzia immobiliare": ("🏘️", "#2e7d32"), "Fornitore (luce, gas, acqua, internet)": ("🔌", "#ef6c00"),
                  "Impresa di pulizie": ("🧹", "#00897b"), "Giardiniere": ("🌿", "#558b2f"), "Altro": ("📌", "#757575")}
_RUB = {"lavoro": {"chiave": "contatti_lavoro", "tipi": None, "titolo": "🤝 Sindacato · CAF · Patronato", "pref": "lv",
                   "intro": "Qui metti i **riferimenti del tuo lavoro**: il sindacato, il CAF, il patronato, il consulente, il commercialista… Ognuno ha il suo **badge colorato**, con nome, persona di riferimento, "
                            "indirizzo, telefono, email e il tasto per **scrivere su WhatsApp**. Tutto si modifica, si esporta e si invia.",
                   "aggiungi": "➕ Aggiungi un contatto (sindacato, CAF, patronato…)", "esempio": "es. CGIL Torino – Camera del Lavoro", "html": "Sindacato, CAF, Patronato e contatti del lavoro", "file": "rubrica_lavoro"},
        "casa": {"chiave": "contatti_casa", "tipi": "casa", "titolo": "📇 Riferimenti della casa", "pref": "rc",
                 "intro": "Qui metti i **riferimenti della tua casa**: il caldaista, l'idraulico, l'elettricista, l'amministratore di condominio, l'assicurazione, i fornitori… Ognuno ha il suo **badge colorato**, "
                          "con nome, persona di riferimento, indirizzo, telefono, email e il tasto per **scrivere su WhatsApp**. Tutto si modifica, si esporta e si invia.",
                 "aggiungi": "➕ Aggiungi un riferimento (caldaista, idraulico, amministratore…)", "esempio": "es. Termoidraulica Rossi", "html": "Riferimenti della casa", "file": "rubrica_casa"}}


def _rub_tipi(modo):
    return _RUB_CASA_TIPI if _RUB[modo]["tipi"] == "casa" else _LV_TIPI


_LV_TIPI = {"Sindacato": ("🤝", "#1565c0"), "CAF": ("🧾", "#2e7d32"), "Patronato": ("🛡️", "#6a1b9a"), "Consulente del lavoro": ("💼", "#ef6c00"), "Commercialista": ("📊", "#00838f"),
            "Avvocato": ("⚖️", "#4e342e"), "INPS": ("🏛️", "#37474f"), "Agenzia delle Entrate": ("🏦", "#455a64"), "Altro": ("📌", "#757575")}


def _lv_badge(tipo, altro="", modo="lavoro"):
    icona, col = _rub_tipi(modo).get(tipo, _rub_tipi(modo)["Altro"])
    testo = (altro or tipo) if tipo == "Altro" else tipo
    return f"<span style='background:{col};color:#fff;border-radius:999px;padding:3px 12px;font-weight:800;font-size:.8rem'>{icona} {_h.escape(testo)}</span>"


def _lv_tel(t):
    return "".join(ch for ch in str(t or "") if ch.isdigit() or ch == "+")


def _lv_wa(cell):
    """Il numero per WhatsApp (con il prefisso del paese, senza + né spazi): un cellulare italiano «333 1234567» diventa 393331234567. '' se non sembra un cellulare."""
    d = "".join(ch for ch in str(cell or "") if ch.isdigit())
    if str(cell or "").strip().startswith("00"):
        d = d[2:]
    if not d:
        return ""
    if str(cell or "").strip().startswith("+") or str(cell or "").strip().startswith("00"):
        return d
    if d.startswith("39") and len(d) >= 11:
        return d
    if d.startswith("3") and 9 <= len(d) <= 10:
        return "39" + d
    return ""


def _lv_maps(indirizzo):
    from urllib.parse import quote
    return "https://www.google.com/maps/search/?api=1&query=" + quote(str(indirizzo or ""))


def _lv_dialogo_togli_contatto(cid, nome, modo="lavoro"):
    chiave_d = _RUB[modo]["chiave"]

    def _finestra():
        st.warning(f"Togliere **{_h.escape(nome)}** dalla rubrica?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, toglilo", key=f"lv_ct_si_{cid}", type="primary", width="stretch"):
            _ca_salva(lambda cc: cc.__setitem__(chiave_d, [x for x in cc.get(chiave_d, []) if x.get("id") != cid]), "Rubrica: contatto tolto")
            st.rerun()
        if s2.button("No, tienilo", key=f"lv_ct_no_{cid}", width="stretch"):
            st.rerun()
    st.dialog("🗑️ Togli dalla rubrica")(_finestra)()


def _lv_form_contatto(m=None, modo="lavoro"):
    import uuid
    m = m or {}
    cfg = _RUB[modo]
    TIPI = _rub_tipi(modo)
    tipi = list(TIPI)
    with st.form(f"{cfg['pref']}_form_cont_{m.get('id', 'nuovo')}", border=False):
        tipo = st.selectbox("Che tipo è (il badge)", tipi, index=tipi.index(m["tipo"]) if m.get("tipo") in tipi else 0, format_func=lambda x: f"{TIPI[x][0]} {x}")
        altro = st.text_input("Se «Altro», scrivi di che tipo è", value=m.get("altro", ""), placeholder="es. Scuola sindacale, Ufficio vertenze…")
        nome = st.text_input("Nome (l'ente o la sede)", value=m.get("nome", ""), placeholder=cfg["esempio"])
        ref = st.text_input("Persona di riferimento", value=m.get("referente", ""), placeholder="es. Dott.ssa Rossi")
        c1, c2 = st.columns(2)
        tel = c1.text_input("Telefono (ufficio)", value=m.get("telefono", ""), placeholder="es. 011 1234567")
        cell = c2.text_input("Cellulare / WhatsApp", value=m.get("cellulare", ""), placeholder="es. 333 1234567 oppure +39 333 1234567",
                             help="Se scrivi qui un cellulare, compare il tasto per scrivere su WhatsApp.")
        email = st.text_input("Email", value=m.get("email", ""), placeholder="nome@esempio.it")
        indirizzo = st.text_input("Indirizzo", value=m.get("indirizzo", ""), placeholder="Via, numero, città")
        sito = st.text_input("Sito web", value=m.get("sito", ""), placeholder="https://…")
        orari = st.text_area("Orari di apertura", value=m.get("orari", ""), height=80, placeholder="es. lun-ven 9-12; su appuntamento")
        note = st.text_area("Note", value=m.get("note", ""), height=80, placeholder="es. serve la tessera; pratica 730, ISEE, disoccupazione…")
        ok = st.form_submit_button("💾 Salva", type="primary", width="stretch")
    if ok:
        if not (nome.strip() or ref.strip()):
            st.error("Scrivi almeno il nome dell'ente o della persona.")
            return
        if email.strip() and ("@" not in email or "." not in email.split("@")[-1]):
            st.error("L'email non sembra giusta: controlla (deve essere tipo nome@esempio.it).")
            return
        if cell.strip() and not _lv_wa(cell):
            st.warning("Il cellulare non sembra un numero per WhatsApp (di solito inizia con 3, oppure con +39): lo salvo lo stesso, ma il tasto WhatsApp non comparirà.")
        nuovo = {"id": m.get("id") or uuid.uuid4().hex[:8], "tipo": tipo, "altro": altro.strip(), "nome": nome.strip(), "referente": ref.strip(), "telefono": tel.strip(), "cellulare": cell.strip(),
                 "email": email.strip(), "indirizzo": indirizzo.strip(), "sito": sito.strip(), "orari": orari.strip(), "note": note.strip()}
        _ca_salva(lambda cc, nv=nuovo, kk=cfg["chiave"]: cc.__setitem__(kk, [x for x in cc.get(kk, []) if x.get("id") != nv["id"]] + [nv]), "Rubrica: contatto")
        st.session_state.pop(f"{cfg['pref']}_cont_mod", None)
        st.session_state["messaggio"] = "✅ Contatto salvato."
        st.rerun()


def lv_html_rubrica(lista, modo="lavoro"):
    e = _h.escape
    stile = ("body{font-family:Arial,sans-serif;font-size:10.5pt;color:#111}h1{font-size:16pt}table{border-collapse:collapse;width:100%}td,th{border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:top}"
             ".nota{font-size:8.5pt;color:#444;margin-top:12pt}")
    righe = "".join("<tr>" + "".join(f"<td>{e(x)}</td>" for x in (f"{m.get('altro') or m.get('tipo', '')}", m.get("nome", ""), m.get("referente", ""), " / ".join(y for y in (m.get("telefono"), m.get("cellulare")) if y),
                                                                  m.get("email", ""), m.get("indirizzo", ""), (m.get("orari") or "").replace("\n", "; "), m.get("note", ""))) + "</tr>" for m in lista)
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'><title>{e(_RUB[modo]['html'])}</title><style>{stile}</style></head><body><h1>{e(_RUB[modo]['html'])}</h1>"
            f"<table><tr><th>Tipo</th><th>Nome</th><th>Riferimento</th><th>Telefono</th><th>Email</th><th>Indirizzo</th><th>Orari</th><th>Note</th></tr>{righe}</table>"
            "<p class='nota'>Creato dall'app «La nostra dispensa».</p></body></html>")


def lv_tab_contatti(c, modo="lavoro"):
    cfg = _RUB[modo]
    TIPI = _rub_tipi(modo)
    pref = cfg["pref"]
    lista = list(c.get(cfg["chiave"], []))
    st.markdown(f"#### {cfg['titolo']}")
    st.caption(cfg["intro"])
    tipi_presenti = [t for t in TIPI if any(x.get("tipo") == t for x in lista)]
    if lista:
        f1, f2 = st.columns([1, 1], gap="small")
        filtro = f1.selectbox("Mostra", ["Tutti"] + tipi_presenti, key=f"{pref}_cont_filtro", format_func=lambda x: x if x == "Tutti" else f"{TIPI[x][0]} {x}")
        cerca = f2.text_input("Cerca", key=f"{pref}_cont_cerca", placeholder="nome, persona, città…")
        visibili = [m for m in lista if (filtro == "Tutti" or m.get("tipo") == filtro)
                    and (not cerca.strip() or cerca.strip().lower() in " ".join(str(v) for v in m.values()).lower())]
    else:
        visibili = []
    for m in sorted(visibili, key=lambda x: (list(TIPI).index(x["tipo"]) if x.get("tipo") in TIPI else 99, (x.get("nome") or "").lower())):
        righe = "<br>".join(x for x in (f"<b>{_h.escape(m.get('nome', ''))}</b>" if m.get("nome") else "", f"👤 {_h.escape(m['referente'])}" if m.get("referente") else "",
                                        f"📞 {_h.escape(m['telefono'])}" if m.get("telefono") else "", f"📱 {_h.escape(m['cellulare'])}" if m.get("cellulare") else "",
                                        f"✉️ {_h.escape(m['email'])}" if m.get("email") else "", f"📍 {_h.escape(m['indirizzo'])}" if m.get("indirizzo") else "",
                                        f"🕒 {_h.escape(m['orari']).replace(chr(10), '; ')}" if m.get("orari") else "", f"<i>{_h.escape(m['note'])}</i>" if m.get("note") else "") if x)
        st.markdown(f"<div class='lv-card'>{_lv_badge(m.get('tipo'), m.get('altro', ''), modo)}<div style='margin-top:6px'>{righe}</div></div>", unsafe_allow_html=True)
        pulsanti = []
        if m.get("telefono") or m.get("cellulare"):
            pulsanti.append(("📞 Chiama", "tel:" + _lv_tel(m.get("telefono") or m.get("cellulare"))))
        if _lv_wa(m.get("cellulare")):
            pulsanti.append(("💬 WhatsApp", "https://wa.me/" + _lv_wa(m["cellulare"])))
        if m.get("email"):
            pulsanti.append(("✉️ Scrivi", "mailto:" + m["email"]))
        if m.get("indirizzo"):
            pulsanti.append(("📍 Mappa", _lv_maps(m["indirizzo"])))
        if m.get("sito", "").startswith(("http://", "https://")):
            pulsanti.append(("🌐 Sito", m["sito"]))
        for i in range(0, len(pulsanti), 3):
            cols = st.columns(3, gap="small")
            for col, (et, url) in zip(cols, pulsanti[i:i + 3]):
                col.link_button(et, url, width="stretch")
        d1, d2, d3 = st.columns(3, gap="small")
        if d1.button("✏️ Modifica", key=f"{pref}_c_e_{m['id']}", width="stretch"):
            st.session_state[f"{pref}_cont_mod"] = m["id"]
            st.rerun()
        if d2.button("🗑️ Togli", key=f"{pref}_c_t_{m['id']}", width="stretch"):
            _lv_dialogo_togli_contatto(m["id"], m.get("nome") or m.get("referente") or "questo contatto", modo)
        with d3:
            if "_fa_inv_voce" in globals():
                _fa_inv_voce(f"{pref}_c_inv_{m['id']}", "📤 Invia", f"{m.get('altro') or m.get('tipo', '')}: {m.get('nome', '')}",
                             [("Tipo", m.get("altro") or m.get("tipo")), ("Nome", m.get("nome")), ("Riferimento", m.get("referente")), ("Telefono", m.get("telefono")), ("Cellulare", m.get("cellulare")),
                              ("Email", m.get("email")), ("Indirizzo", m.get("indirizzo")), ("Orari", m.get("orari")), ("Note", m.get("note"))], [])
        if st.session_state.get(f"{pref}_cont_mod") == m["id"]:
            _lv_form_contatto(m, modo)
    if lista and not visibili:
        st.info("Nessun contatto con questi filtri.")
    with st.expander(cfg["aggiungi"]):
        _lv_form_contatto(None, modo)
    if lista:
        html_r = lv_html_rubrica(lista, modo)
        nome_f = f"{cfg['file']}_{date.today().isoformat()}"
        st.download_button("📄 Scarica la rubrica (da stampare o salvare come PDF)", html_r.encode("utf-8"), file_name=nome_f + ".html", mime="text/html", width="stretch", key=f"{pref}_cont_dl")
        if "inv_voce" in globals():
            inv_voce(f"{pref}_cont_inv", "📤 Invia la rubrica", cfg["html"], "\n".join(f"• {m.get('altro') or m.get('tipo', '')}: {m.get('nome', '')} {m.get('telefono') or m.get('cellulare') or ''} {m.get('email', '')}".strip() for m in lista), [])


# ---------------------------------------------------------------------------------------------------------------------
# 📑 CERTIFICAZIONE UNICA
# ---------------------------------------------------------------------------------------------------------------------
def lv_cu_righe(docs):
    """Le CU, dalla più recente: [{id, anno, imposta, ente, reddito, ritenute, add_reg, add_com}]."""
    out = []
    for d in docs:
        if d.get("tipo") != "Certificazione Unica (CU)":
            continue
        out.append({"id": d.get("id"), "anno": str(d.get("cu_anno") or ""), "imposta": str(d.get("cu_anno_imposta") or ""), "ente": d.get("ente") or "", "reddito": _lv_num(d.get("cu_reddito")),
                    "ritenute": _lv_num(d.get("cu_ritenute")), "add_reg": _lv_num(d.get("cu_add_reg")), "add_com": _lv_num(d.get("cu_add_com"))})
    return sorted(out, key=lambda r: (r["anno"], r["ente"]), reverse=True)


def lv_html_cu(righe):
    e = _h.escape
    tr = "".join("<tr>" + "".join(f"<td>{e(str(x))}</td>" for x in (r["anno"], r["imposta"], r["ente"], _lv_eur(r["reddito"]), _lv_eur(r["ritenute"]), _lv_eur(r["add_reg"]), _lv_eur(r["add_com"]))) + "</tr>" for r in righe)
    return ("<!doctype html><html lang='it'><head><meta charset='utf-8'><title>Certificazioni Uniche</title><style>body{font-family:Arial,sans-serif;font-size:10.5pt}table{border-collapse:collapse;width:100%}"
            "td,th{border:1px solid #999;padding:4px 6px;text-align:right}td:nth-child(3),th:nth-child(3){text-align:left}</style></head><body><h1>Certificazioni Uniche</h1>"
            "<table><tr><th>Anno CU</th><th>Redditi del</th><th>Emessa da</th><th>Reddito</th><th>Ritenute IRPEF</th><th>Add. regionale</th><th>Add. comunale</th></tr>" + tr + "</table>"
            "<p style='font-size:8.5pt;color:#444'>Creato dall'app «La nostra dispensa»: controlla i dati sugli originali.</p></body></html>")


def lv_vista_scelta(chiave):
    """Schede o tabella: la scelta resta."""
    return st.radio("Come vuoi vederle", ["📇 Schede", "📋 Tabella"], horizontal=True, key=chiave, label_visibility="collapsed") == "📋 Tabella"


def lv_tab_cu(c):
    n = st.session_state.get("ca_giro", 0)
    st.markdown("#### ➕ Carica la Certificazione Unica")
    st.caption("Carica il **PDF** o una **foto** della CU: la riconosco da sola, leggo l'anno, chi l'ha emessa, il reddito, le ritenute e le addizionali, e te li propongo. **Controlli e confermi tu.**")
    up = _ca_pannello_caricamento(n)
    _ca_flusso_documento(c, [], n, up, None, None, lavoro="cu", finestra=True)
    _lv_a_mano("cu", "Inserisci a mano una Certificazione Unica")
    _ca_correzione(c, [])
    docs = [d for d in c.get("documenti", []) if d.get("tipo") == "Certificazione Unica (CU)"]
    st.markdown(f"#### 📑 Le tue Certificazioni Uniche ({len(docs)})")
    if not docs:
        st.info("Ancora nessuna Certificazione Unica. Caricane una qui sopra.")
        return
    righe = lv_cu_righe(docs)
    if lv_vista_scelta("lv_cu_vista"):
        try:
            import pandas as pd
            st.dataframe(pd.DataFrame([{"Anno CU": r["anno"], "Redditi del": r["imposta"], "Emessa da": r["ente"], "Reddito €": r["reddito"], "Ritenute IRPEF €": r["ritenute"], "Add. regionale €": r["add_reg"], "Add. comunale €": r["add_com"]} for r in righe]),
                         hide_index=True, width="stretch")
        except Exception:
            st.warning("La tabella non è disponibile su questo dispositivo.")
    else:
        for d in sorted(docs, key=lambda x: (str(x.get("cu_anno") or ""), x.get("ente") or ""), reverse=True):
            with st.expander(f"📑 CU {d.get('cu_anno') or '?'} · redditi {d.get('cu_anno_imposta') or '?'} · {d.get('ente') or ''}" + (f" · reddito {_lv_eur(_lv_num(d.get('cu_reddito')))}" if d.get("cu_reddito") else "")):
                _ca_riga_documento(d, {}, "lvcu", docs)
    anni = [r for r in righe if r["reddito"] is not None]
    if len(anni) >= 2:
        pd = _lv_grafici_dati(None)
        if pd is not None:
            st.markdown("**📊 Anno per anno: reddito e ritenute**")
            ordinate = sorted(anni, key=lambda r: r["anno"])
            st.bar_chart(pd.DataFrame({"Reddito": [r["reddito"] or 0 for r in ordinate], "Ritenute IRPEF": [r["ritenute"] or 0 for r in ordinate]}, index=[r["anno"] or r["imposta"] for r in ordinate]), stack=False, height=240)
            for a, b in zip(ordinate[1:], ordinate[:-1]):
                if b["reddito"]:
                    st.caption(f"CU {a['anno']} rispetto alla CU {b['anno']}: reddito {_ca_fmt_var(round((a['reddito'] or 0) - b['reddito'], 2), round(((a['reddito'] or 0) - b['reddito']) / b['reddito'] * 100, 1))}")
    html_cu = lv_html_cu(righe)
    st.download_button("📄 Scarica l'elenco (da stampare o salvare come PDF)", html_cu.encode("utf-8"), file_name=f"certificazioni_uniche_{date.today().isoformat()}.html", mime="text/html", width="stretch", key="lv_cu_dl")
    if "inv_voce" in globals():
        inv_voce("lv_cu_inv", "📤 Invia l'elenco delle CU", "Certificazioni Uniche", "\n".join(f"• CU {r['anno']} (redditi {r['imposta']}): reddito {_lv_eur(r['reddito'])}, ritenute {_lv_eur(r['ritenute'])} · {r['ente']}" for r in righe), [])


# ---------------------------------------------------------------------------------------------------------------------
# 🏛️ INPS
# ---------------------------------------------------------------------------------------------------------------------
def lv_tab_inps(c):
    n = st.session_state.get("ca_giro", 0)
    link = (c.get("inps_link") or "").strip()
    st.markdown("#### 🏛️ INPS")
    st.link_button("🔗 Apri la mia pagina INPS" if link else "🔗 Apri il sito dell'INPS", link or "https://www.inps.it", type="primary", width="stretch")
    if "_fa_inv_voce" in globals():
        _fa_inv_voce("lv_inps_link_inv", "📤 Invia il link", "Pagina INPS", [("Collegamento", link or "https://www.inps.it")], [])
    with st.expander("✏️ Scrivi o cambia il link alla mia pagina INPS"):
        st.caption("Apri la tua pagina INPS nel browser, tocca la barra dell'indirizzo, **copia** il link e **incollalo** qui sotto. "
                   "Qui **non si scrivono mai password, PIN o codici**: serve solo l'indirizzo della pagina.")
        nuovo = st.text_input("Link alla mia pagina INPS", value=link, placeholder="https://…", key="lv_inps_link_t")
        if st.button("💾 Salva il link", key="lv_inps_link_s", width="stretch"):
            if nuovo.strip() and not nuovo.strip().startswith(("http://", "https://")):
                st.error("Il link deve cominciare con https:// (copialo dalla barra dell'indirizzo).")
            else:
                _ca_salva(lambda cc, u=nuovo.strip(): cc.__setitem__("inps_link", u), "Lavoro: link INPS")
                st.session_state["messaggio"] = "✅ Link salvato."
                st.rerun()
    st.markdown("#### 📎 Documenti scaricati dall'INPS")
    st.caption("Estratto conto contributivo, Certificazione Unica, cedolini, ISEE, domande: scaricali dal sito dell'INPS e caricali qui. Poi li **vedi**, li **scarichi** di nuovo, li **invii** o li **elimini**.")
    up = _ca_pannello_caricamento(n)
    _ca_flusso_documento(c, [], n, up, None, None, lavoro="inps", finestra=True)
    _lv_a_mano("inps", "Aggiungi una voce a mano (senza file)")
    _ca_correzione(c, [])
    docs = [d for d in c.get("documenti", []) if d.get("tipo") == "Documento INPS"]
    st.markdown(f"#### 📚 I tuoi documenti INPS ({len(docs)})")
    if not docs:
        st.info("Ancora nessun documento INPS. Caricane uno qui sopra.")
        return
    ordinati = sorted(docs, key=lambda d: str(d.get("data_doc") or d.get("creato_il") or ""), reverse=True)
    if lv_vista_scelta("lv_inps_vista"):
        try:
            import pandas as pd
            st.dataframe(pd.DataFrame([{"Documento": d.get("inps_tipo") or "", "Data": _ca_data_it(d.get("data_doc")) if d.get("data_doc") else "", "Note": d.get("note") or "", "File": (d.get("file") or {}).get("nome", "a mano")} for d in ordinati]),
                         hide_index=True, width="stretch")
        except Exception:
            st.warning("La tabella non è disponibile su questo dispositivo.")
    else:
        tipi = sorted({d.get("inps_tipo") or "Altro" for d in ordinati})
        for t_ in tipi:
            with st.expander(f"📁 {t_} ({sum(1 for d in ordinati if (d.get('inps_tipo') or 'Altro') == t_)})"):
                for d in [x for x in ordinati if (x.get("inps_tipo") or "Altro") == t_]:
                    _ca_riga_documento(d, {}, "lvinps", docs)


def schermata_lavoro():
    """La pagina «Lavoro»."""
    if "nav_barra" in globals():
        nav_barra("lavoro")
    if "_CA_CSS" in globals():
        st.markdown(_CA_CSS, unsafe_allow_html=True)
    st.markdown(_LV_CSS, unsafe_allow_html=True)
    st.markdown("<div class='lv-hero'><div class='ico'>💼</div><div><h1>Lavoro</h1><p>Le buste paga, anno per anno: netto, lordo e trattenute a confronto</p></div></div>", unsafe_allow_html=True)
    if st.session_state.get("messaggio"):
        st.success(st.session_state.pop("messaggio"))
    if "pulsante_info" in globals():
        try:
            pulsante_info("lavoro")
        except Exception:
            pass
    try:
        c = _ca_dati()
    except Exception as ex:
        st.error(f"Non riesco a leggere i dati ({type(ex).__name__}). Riprova fra poco.")
        return
    voci = ["💶 Buste paga", "📊 Anno per anno", "📑 Certificazione Unica", "🏛️ INPS", "🤝 Sindacato · CAF · Patronato"]
    st.markdown(_LV_CSS_SEZ, unsafe_allow_html=True)
    if hasattr(st, "pills"):
        scelta = st.pills("Che cosa vuoi vedere?", voci, default=voci[0], key="lv_sezione", label_visibility="collapsed")
    else:
        scelta = st.radio("Che cosa vuoi vedere?", voci, horizontal=True, key="lv_sezione", label_visibility="collapsed")
    scelta = scelta or voci[0]
    if scelta == voci[0]:
        lv_tab_buste(c)
    elif scelta == voci[1]:
        lv_tab_grafici(c)
    elif scelta == voci[2]:
        lv_tab_cu(c)
    elif scelta == voci[3]:
        lv_tab_inps(c)
    else:
        lv_tab_contatti(c)


# ---- lo smistamento: «lavoro» va alla sua pagina (con il controllo dei permessi di «Sezioni visibili»), il resto come prima
if "schermata_farmacia" in globals() and "_lv_schermata_prima" not in globals():
    _lv_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "lavoro":
            if "sv_nascoste" in globals() and "lavoro" in sv_nascoste():
                return sv_blocca("lavoro")
            return schermata_lavoro()
        return _lv_schermata_prima()


# ---- la guida «Informazioni» della sezione
def _lv_guida_aggiungi(sezione, voci):
    """Aggiunge alla guida di una sezione le voci nuove (id, titolo, testo, parole), una sola volta."""
    if "_GUIDE" not in globals() or sezione not in _GUIDE or "_ID_GUIDA" not in globals():
        return
    ids = list(_ID_GUIDA.get(sezione, []))
    if voci[0][0] in ids or len(ids) != len(_GUIDE[sezione]):
        return
    _GUIDE[sezione] = list(_GUIDE[sezione]) + [(t, c, k) for _i, t, c, k in voci]
    _ID_GUIDA[sezione] = ids + [x[0] for x in voci]


if "_NOMI_SEZIONI" in globals():
    _NOMI_SEZIONI.setdefault("lavoro", "💼 Lavoro")
    _GUIDE.setdefault("lavoro", [
        ("💼 Cos'è la sezione Lavoro",
         """Qui sta tutto ciò che riguarda il tuo lavoro. In alto scegli cosa vuoi vedere (sono **pulsanti a pillola**): **💶 Buste paga**, **📊 Anno per anno**, **📑 Certificazione Unica**, **🏛️ INPS** e **🤝 Sindacato · CAF · Patronato**.
Si apre dal bottone **💼 Lavoro**, accanto agli altri.""", "lavoro buste paga stipendio netto lordo trattenute"),
        ("💶 Caricare una busta paga",
         """1. Apri **💼 Lavoro** → **💶 Buste paga**.
2. Tocca **📎 Scegli il PDF o il file** (oppure **📷 Scatta foto** o **🖼️ Dalla galleria**). Puoi anche scegliere **più buste insieme**.
3. Si apre **una finestra sopra la pagina** con il **mese**, il **lordo**, il **netto** e le **trattenute** letti dal documento: **controlla e correggi** quello che serve, poi tocca **✅ Conferma e archivia**.
4. Se non riesce a leggere un valore, lo scrivi tu. Puoi aggiungere **voci a mano** (premio, straordinari, arretrati): contano nei totali.
Se la stessa busta (stesso mese) sembra già archiviata, ti avviso prima. Per inserirla **a mano**, senza file, apri **✍️ Inserisci a mano una busta paga o una voce**.""", "carica busta paga pdf foto leggi netto lordo trattenute voci 13esima 14esima finestra"),
        ("📊 Anno per anno: grafici e confronto",
         """Scegli **📊 Anno per anno**. Vedi, per ogni anno, il **netto ricevuto** (con 13ª, 14ª e voci a mano), il **lordo** e le **trattenute totali**, e quanto pesano le trattenute sul lordo.
Sotto, **il confronto con gli anni prima**, in euro e in percentuale. Per l'anno non ancora finito il confronto è **«a parità di mesi»**.
Puoi **scaricare** il riepilogo (HTML o PDF) e **inviarlo** per email, WhatsApp o Telegram.""", "grafico anno confronto netto lordo trattenute percentuale riepilogo esporta"),
        ("🤝 Sindacato, CAF, Patronato: la rubrica",
         """Scegli **🤝 Sindacato · CAF · Patronato**. Tocca **➕ Aggiungi un contatto**, scegli il **badge** (Sindacato, CAF, Patronato, Consulente del lavoro, Commercialista, Avvocato, INPS, Agenzia delle Entrate, Altro) e scrivi nome, persona di riferimento, telefono, **cellulare**, email, indirizzo, orari e note.
Su ogni contatto: **📞 Chiama**, **💬 WhatsApp** (compare se hai scritto un cellulare), **✉️ Scrivi**, **📍 Mappa**, **🌐 Sito**, poi **✏️ Modifica**, **🗑️ Togli** (ti chiedo conferma) e **📤 Invia**.
In alto puoi **filtrare per badge** e **cercare**. In fondo **scarichi** la rubrica o la **invii**.""", "sindacato caf patronato rubrica contatti telefono whatsapp email indirizzo badge consulente commercialista"),
        ("📑 Certificazione Unica (CU)",
         """Scegli **📑 Certificazione Unica**. Carica il PDF o una foto: l'app **la riconosce da sola** come Certificazione Unica e legge l'**anno**, **chi l'ha emessa**, il **reddito**, le **ritenute IRPEF** e le **addizionali**. Controlli e confermi.
Le vedi **a schede** (una per anno) o **in tabella**, con il **grafico** e il confronto con l'anno prima. Si **scarica** l'elenco e si **invia**. Se una CU non viene letta bene, la correggi o la inserisci **a mano**.""", "certificazione unica cu certificato unico reddito ritenute irpef addizionale sostituto d'imposta"),
        ("🏛️ INPS",
         """Scegli **🏛️ INPS**. Il tasto **🔗 Apri la mia pagina INPS** ti porta alla tua pagina: la prima volta apri **✏️ Scrivi o cambia il link**, incolla l'indirizzo della tua pagina e salva. **Non si scrivono mai password o PIN.**
Sotto, i **documenti scaricati dall'INPS** (estratto conto contributivo, CU, ISEE, domande…): li carichi, li **vedi**, li **scarichi**, li **invii** o li **elimini**. Si vedono a elenco per tipo o **in tabella**.""", "inps pagina link documenti estratto conto contributivo isee pensione spid"),
    ])
    _ID_GUIDA.setdefault("lavoro", ["l_cosa", "l_carica", "l_anni", "l_rubrica", "l_cu", "l_inps"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("lavoro", "l_cosa")
    _lv_guida_aggiungi("lavoro", [
        ("l_lavori", "💼 Più lavori (principale e secondari)", """Nelle **💶 Buste paga** e in **📊 Anno per anno** apri **➕ Aggiungi un altro lavoro** (secondo lavoro, collaborazione…): dai un nome e, se vuoi, il datore. Da quel momento in alto compaiono le **pillole**: **Tutti i lavori**, **Lavoro principale** e gli altri. Ogni busta ha il suo lavoro («Di quale lavoro è»). Nei grafici vedi un lavoro alla volta oppure **tutti insieme**, con il netto di ognuno anno per anno.""", "lavori secondo lavoro secondario collaborazione piu lavori"),
    ])
    _lv_guida_aggiungi("dispensa", [
        ("h_radio", "🎧 La radio di sottofondo", """Sul bordo sinistro dello schermo c'è la **linguetta 🎧**. Toccala: si apre il pannello. Scegli una stazione **lounge e chill** già pronta, oppure **cerca tra migliaia di radio** (per nome o per genere: Lounge, Jazz, Classica…). Hai **▶ ⏸ ⏹**, il **volume**, le **★ preferite**, l'**equalizzatore** (bassi, medi, alti) e lo **spettro**. La musica **resta accesa in tutte le sezioni**. Il primo ascolto parte solo dopo un tuo tocco. Alcune radio non permettono equalizzatore e spettro: il pannello lo dice. Si nasconde da **Utilità → Aspetto dell'app**.""", "radio musica sottofondo lounge equalizzatore volume spettro"),
        ("h_scambio", "📦 Scambiare i dati con un altro utente", """In **🧰 Utilità → 📦 Scambia i dati con un altro utente** (e dal pulsante in fondo a ogni sezione): **📤 Esporta** → scegli le sezioni, metti una **password** e scarica il file **.dispensa**. L'altro utente va in **📥 Importa**, sceglie il file con il pulsante arancione, scrive la password, guarda cosa contiene e **aggiunge** le tue cose alle sue: non cancella e non cambia niente di suo.""", "scambio esporta importa file utente famiglia dati condividere"),
    ])
    _lv_guida_aggiungi("casa", [
        ("c_interventi", "🔧 Interventi ripetuti: lo storico", """In **🏡 Casa → 🔧 Manutenzioni** registri ogni intervento (anche sulla casa in generale, senza un bene). Dai un **nome** all'intervento (per esempio «Controllo fumi caldaia»): tutte le volte che lo fai finiscono **nello stesso gruppo**.
Per ogni gruppo vedi **quante volte**, **quando**, **quanto hai speso** (anche anno per anno) e puoi toccare **➕ Registra un'altra volta**. Lo storico si **scarica** e si **invia**.""", "interventi manutenzione caldaia storico ripetuti spesa"),
        ("c_riferimenti", "📇 Riferimenti della casa", """In **🏡 Casa → 📇 Riferimenti** metti caldaista, idraulico, elettricista, amministratore, assicurazione, fornitori… Ognuno ha il suo **badge colorato** e i tasti **📞 Chiama**, **💬 WhatsApp**, **✉️ Scrivi**, **📍 Mappa**. Si modifica, si toglie (con conferma), si esporta e si invia.""", "riferimenti casa caldaista idraulico elettricista amministratore rubrica whatsapp"),
    ])
    _lv_guida_aggiungi("dispensa", [
        ("h_lampeggio", "🔔 I bottoni che lampeggiano", """Se in una sezione c'è qualcosa **in scadenza o scaduto** (prodotti, medicinali, ricette, visite, documenti, bollette, garanzie, manutenzioni, controlli), il suo **bottone colorato lampeggia** e mostra il numero, per esempio **🩺 Salute 🔔2**. Sotto i bottoni, il riquadro **«Ci sono N cose da guardare»** dice cosa. Se non c'è niente: **«✅ Tutto a posto»**.""", "lampeggia bottoni scadenza avvisi cose da guardare"),
        ("h_testi", "🔤 Scritte più grandi", """Vai in **🧰 Utilità → ⚙️ Aspetto dell'app** e scegli **🔤 Grandezza dei testi**: **Normale**, **Grande** o **Molto grande**. Vale per tutta l'app e si ricorda.""", "testi grandi grandezza carattere leggere aspetto"),
    ])
