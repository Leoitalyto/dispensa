# -*- coding: utf-8 -*-
"""🛒💶 DISPENSA: PREZZI, PESO, €/kg E «QUANDO FINISCE» (richiesta del 24/11/2026).

1. PREZZI. Nella scheda di un prodotto della Dispensa: prezzo pagato, negozio, data, confezioni, peso/contenuto (o «venduto a peso»:
   €/kg × grammi). Il prezzo va nell'UNICO archivio dei prezzi di Spesa Smart (una rilevazione, fonte «acquisto»): niente doppioni,
   e «Dove costa meno», «Offerte» e la «Lista ottimizzata» lo usano subito. Sulla scheda: ultimo prezzo, €/kg, «in offerta da…»,
   «costa meno da…» e un piccolo storico.
2. 🛒 «Metti nella lista della spesa», con la quantità, su ogni prodotto.
3. QUANDO FINISCE non va più in lista da solo: l'app CHIEDE (🛒 lista · ⏰ più avanti · 💭 se conviene · 🚫 non lo ricompro).
   Regola per prodotto («Quando finisce»: chiedimi / sempre in lista / solo se in offerta / mai) e scorta minima (sotto → stessa regola).
   Se per un prodotto scegli sempre «lista», l'app propone di farla diventare la regola.
4. Nella lista della spesa, sopra la lista vera: ❓ Finiti, da decidere · 🏷️ Da ricomprare se conviene (si accendono se in offerta)
   · ⏰ Più avanti (con la data; quel giorno tornano da decidere o vanno in lista da soli, come scegli).

Dati nel file della dispensa (anche di famiglia): d["spesa_attesa"] = [{id, nome, marca, barcode, q, tipo: decidere|offerta|dopo, quando, poi, dal, motivo}],
d["spesa_regole"] = {chiave: {quando, minima, storia: [...]}}. Prezzi: d_personale["spesa_smart"]["rilevazioni"]. Prefisso: dp_ / DP_."""
import datetime as _dp_dt
import uuid as _dp_uuid

import streamlit as st

DP_REGOLE = {"chiedi": "❓ Chiedimi", "sempre": "🛒 Mettilo sempre in lista", "offerta": "🏷️ Solo se è in offerta", "mai": "🚫 Mai"}
DP_TIPI = {"decidere": "❓ Finiti, da decidere", "offerta": "🏷️ Da ricomprare se conviene", "dopo": "⏰ Più avanti"}
DP_STORIA_MAX = 6


# =====================================================================================================================
# logica (senza Streamlit)
# =====================================================================================================================
def dp_chiave(r):
    return ((r.get("barcode") or r.get("ean") or "").strip() or (r.get("nome") or "").strip().lower())


def dp_oggi():
    return _dp_dt.date.today()


def dp_regola(d, r):
    reg = dict((d.get("spesa_regole") or {}).get(dp_chiave(r)) or {})
    reg.setdefault("quando", "chiedi")
    reg.setdefault("minima", 0)
    reg.setdefault("storia", [])
    if reg["quando"] not in DP_REGOLE:
        reg["quando"] = "chiedi"
    return reg


def dp_imposta_regola(d, r, quando=None, minima=None):
    ch = dp_chiave(r)
    if not ch:
        return
    reg = d.setdefault("spesa_regole", {}).setdefault(ch, {"quando": "chiedi", "minima": 0, "storia": []})
    if quando is not None:
        reg["quando"] = quando if quando in DP_REGOLE else "chiedi"
    if minima is not None:
        try:
            reg["minima"] = max(0.0, float(minima))
        except (TypeError, ValueError):
            pass
    reg["nome"] = r.get("nome", "")


def dp_in_lista(d, ch):
    return any(dp_chiave(x) == ch and not x.get("preso") for x in d.get("spesa") or [])


def dp_in_attesa(d, ch):
    return next((x for x in d.get("spesa_attesa") or [] if dp_chiave(x) == ch), None)


def dp_totale(d, ch):
    tot = 0.0
    for a in d.get("articoli") or []:
        if dp_chiave(a) == ch:
            try:
                tot += float(a.get("quantita") or 0)
            except (TypeError, ValueError):
                pass
    return tot


def _dp_q(v):
    try:
        return max(1.0, float(v or 1))
    except (TypeError, ValueError):
        return 1.0


def _dp_voce(r, tipo, oggi_, motivo="finito", quando=None, poi="chiedi"):
    return {"id": _dp_uuid.uuid4().hex[:10], "nome": r.get("nome", ""), "marca": r.get("marca", ""), "barcode": r.get("barcode", "") or "",
            "per_chi": r.get("per_chi", "adulti"), "q": _dp_q(r.get("q")),
            "tipo": tipo, "quando": quando.isoformat() if quando else "", "poi": poi, "dal": oggi_.isoformat(), "motivo": motivo,
            "formato_valore": r.get("formato_valore"), "formato_unita": r.get("formato_unita") or ""}


def dp_finito(d, r, motivo="finito", oggi_=None):
    """Un prodotto è finito (o sotto la scorta minima): segue la sua regola. Ritorna: lista | offerta | decidere | mai | gia."""
    oggi_ = oggi_ or dp_oggi()
    ch = dp_chiave(r)
    if not ch:
        return "gia"
    if dp_in_lista(d, ch) or dp_in_attesa(d, ch):
        return "gia"
    q = dp_regola(d, r)["quando"]
    if q == "sempre":
        aggiungi_a_spesa(d, r)
        return "lista"
    if q == "mai":
        return "mai"
    d.setdefault("spesa_attesa", []).append(_dp_voce(r, "offerta" if q == "offerta" else "decidere", oggi_, motivo))
    return "offerta" if q == "offerta" else "decidere"


def dp_sotto_minima(d, r, oggi_=None):
    """Dopo un consumo: se il totale di quel prodotto è sceso alla scorta minima (o sotto), segue la regola. None se non serve."""
    reg = dp_regola(d, r)
    m = float(reg.get("minima") or 0)
    if m <= 0:
        return None
    if dp_totale(d, dp_chiave(r)) > m:
        return None
    return dp_finito(d, r, "scorta", oggi_)


def _dp_storia(d, r, scelta):
    ch = dp_chiave(r)
    if not ch:
        return
    reg = d.setdefault("spesa_regole", {}).setdefault(ch, {"quando": "chiedi", "minima": 0, "storia": []})
    reg["storia"] = (list(reg.get("storia") or []) + [scelta])[-DP_STORIA_MAX:]
    reg["nome"] = r.get("nome", "")


def dp_suggerisci_sempre(d, r):
    """True se le ultime 3 decisioni sono state «lista» e la regola è ancora «chiedi»."""
    reg = dp_regola(d, r)
    st_ = reg.get("storia") or []
    return reg["quando"] == "chiedi" and len(st_) >= 3 and all(x == "lista" for x in st_[-3:])


def dp_metti_in_lista(d, r, q=1):
    """🛒 Mette in lista (e lo toglie dall'attesa). Se è già in lista aggiorna la quantità. Ritorna: aggiunto | aggiornato."""
    ch = dp_chiave(r)
    d["spesa_attesa"] = [x for x in d.get("spesa_attesa") or [] if dp_chiave(x) != ch]
    for x in d.get("spesa") or []:
        if dp_chiave(x) == ch and not x.get("preso"):
            x["q"] = max(float(q or 1), 1.0)
            return "aggiornato"
    aggiungi_a_spesa(d, dict(r, q=q))
    return "aggiunto"


def dp_decidi(d, aid, scelta, quando=None, poi="chiedi", oggi_=None):
    """La decisione su un prodotto in attesa: lista | dopo | offerta | mai | togli. Ritorna la voce (o None)."""
    oggi_ = oggi_ or dp_oggi()
    voce = next((x for x in d.get("spesa_attesa") or [] if x.get("id") == aid), None)
    if voce is None:
        return None
    if scelta == "lista":
        dp_metti_in_lista(d, voce, voce.get("q") or 1)
    elif scelta == "dopo":
        voce.update(tipo="dopo", quando=(quando or oggi_ + _dp_dt.timedelta(days=7)).isoformat(), poi=poi if poi in ("chiedi", "lista") else "chiedi")
        voce.pop("tornato", None)
    elif scelta == "offerta":
        voce.update(tipo="offerta", quando="")
        voce.pop("tornato", None)
    elif scelta in ("mai", "togli"):
        d["spesa_attesa"] = [x for x in d.get("spesa_attesa") or [] if x.get("id") != aid]
        if scelta == "mai":
            dp_imposta_regola(d, voce, quando="mai")
    _dp_storia(d, voce, scelta)
    return voce


def dp_maturati(d, oggi_=None):
    """I «più avanti» arrivati al loro giorno: vanno in lista (poi=lista) o tornano «da decidere». Ritorna (in_lista, da_decidere) nomi."""
    oggi_ = oggi_ or dp_oggi()
    in_lista, da_decidere = [], []
    for v in list(d.get("spesa_attesa") or []):
        if v.get("tipo") != "dopo" or not v.get("quando") or v["quando"] > oggi_.isoformat():
            continue
        if v.get("poi") == "lista":
            dp_metti_in_lista(d, v, v.get("q") or 1)
            in_lista.append(v.get("nome", ""))
        else:
            v.update(tipo="decidere", tornato=True)
            da_decidere.append(v.get("nome", ""))
    return in_lista, da_decidere


def dp_conteggi(d, oggi_=None):
    oggi_ = oggi_ or dp_oggi()
    c = {"decidere": 0, "offerta": 0, "dopo": 0, "maturi": 0}
    for v in d.get("spesa_attesa") or []:
        c[v.get("tipo", "decidere")] = c.get(v.get("tipo", "decidere"), 0) + 1
        if v.get("tipo") == "dopo" and v.get("quando") and v["quando"] <= oggi_.isoformat():
            c["maturi"] += 1
    return c


# --- prezzi -----------------------------------------------------------------------------------------------------------
def dp_unita_ss(u):
    u = str(u or "").strip()
    return "l" if u in ("L", "lt", "litri") else u.lower()


def dp_prezzo_da_peso(euro_kg, grammi):
    """Venduto a peso: €/kg × grammi → prezzo pagato (2 decimali)."""
    try:
        return round(float(euro_kg) * float(grammi) / 1000.0, 2)
    except (TypeError, ValueError):
        return None


def dp_registra_prezzo(ss, r, prezzo, negozio_nome, confezioni=1, valore=None, unita=None, data=None, promo=False, prezzo_pieno=None,
                       oggi_=None):
    """Mette il prezzo pagato nell'archivio di Spesa Smart (fonte «acquisto»). Ritorna (rilevazione, prodotto, errori)."""
    oggi_ = oggi_ or dp_oggi()
    try:
        prezzo = float(str(prezzo).replace(",", "."))
    except (TypeError, ValueError):
        return None, None, ["Scrivi il prezzo pagato (per esempio 1,89)."]
    if prezzo <= 0:
        return None, None, ["Il prezzo deve essere più di 0."]
    if isinstance(negozio_nome, (tuple, list)):                       # (negozio_id, negozio nuovo) dal campo unico ss_campo_negozio
        neg_scelta = tuple(negozio_nome) + (None, None)
        if not neg_scelta[0] and not (neg_scelta[1] or {}).get("nome"):
            return None, None, ["Scegli o scrivi il negozio."]
    elif not str(negozio_nome or "").strip():
        return None, None, ["Scegli o scrivi il negozio."]
    else:
        neg_scelta = None
    p = ss_prodotto_per_riga_disp(ss, r)
    if p is None:
        base = ss_da_dispensa(r)
        if valore:
            base["formato_valore"], base["formato_unita"] = valore, dp_unita_ss(unita)
        p, _nuovo = ss_aggiungi_prodotto(ss, base)
    if neg_scelta is not None:
        n = ss_negozio_da_scelta(ss, neg_scelta[0], neg_scelta[1])
    else:
        n = ss_trova_negozio_da_testo(ss, negozio_nome)
        if n is None:
            n, _nn = ss_aggiungi_negozio(ss, {"nome": str(negozio_nome).strip()})
    kw = dict(confezioni=confezioni or 1, formato_valore=valore if valore else None, formato_unita=dp_unita_ss(unita) if valore else None,
              data=data or oggi_.isoformat(), fonte="acquisto", oggi_=oggi_)
    if promo and prezzo_pieno:
        ril, err = ss_nuova_rilevazione(ss, p["id"], n["id"], prezzo=prezzo_pieno, prezzo_promo=prezzo, promo_dal=kw["data"], promo_al=kw["data"], **kw)
    else:
        ril, err = ss_nuova_rilevazione(ss, p["id"], n["id"], prezzo=prezzo, **kw)
    return ril, p, err


def dp_info_prezzi(ss, r, oggi_=None):
    """Quello che si mostra sulla scheda: ultimo prezzo, migliore oggi, offerta, storico breve. {} se non c'è niente."""
    oggi_ = oggi_ or dp_oggi()
    p = ss_prodotto_per_riga_disp(ss, r)
    if not p:
        return {}
    storico = ss_storico(ss, p["id"])
    if not storico:
        return {"prodotto": p}
    ult = storico[-1]
    n_ult = ss_trova(ss, "negozi", ult.get("negozio_id"))
    out = {"prodotto": p, "ultimo": ult, "ultimo_negozio": ss_nome_negozio(n_ult) if n_ult else "",
           "storico": [(x.get("data"), x.get("prezzo_promo") or x.get("prezzo"), x.get("prezzo_unitario"), x.get("unita_base")) for x in storico[-6:]]}
    cor = ss_prezzi_correnti(ss, p["id"], oggi_)
    if cor:
        m = cor[0]
        out["migliore"] = m
        out["migliore_negozio"] = ss_nome_negozio(ss_trova(ss, "negozi", m["negozio_id"]))
        val = (lambda x: x["unitario"] if x.get("confrontabile") and x.get("unitario") is not None else x["prezzo"])
        u_ult = ult.get("prezzo_unitario") if m.get("confrontabile") else (ult.get("prezzo_promo") or ult.get("prezzo"))
        if m["negozio_id"] != ult.get("negozio_id") and u_ult and val(m) and val(m) < u_ult * 0.97:
            out["risparmio_pct"] = round((1 - val(m) / u_ult) * 100)
    off = ss_offerte_interessanti(ss, oggi_, {p["id"]})
    if off:
        o = off[0]
        out["offerta"] = o
        out["offerta_negozio"] = ss_nome_negozio(ss_trova(ss, "negozi", o["corrente"]["negozio_id"]))
    return out


def dp_testi_prezzo(info):
    """Le righe di testo per la scheda (lista di stringhe)."""
    righe = []
    u = info.get("ultimo")
    if u:
        prezzo = u.get("prezzo_promo") or u.get("prezzo")
        formato = ss_fmt_formato(u)
        d_ = ss_data_it(u.get("data")) if u.get("data") else ""
        righe.append("💶 **" + ss_euro(prezzo) + "**" + (f" · {formato}" if formato else "")
                     + (f" · **{ss_fmt_unitario(u.get('prezzo_unitario'), u.get('unita_base'))}**" if u.get("prezzo_unitario") and u.get("unita_base") != "pz" else "")
                     + (f" · {info.get('ultimo_negozio')}" if info.get("ultimo_negozio") else "") + (f" · {d_}" if d_ else ""))
    o = info.get("offerta")
    if o:
        c = o["corrente"]
        fine = f" fino al {ss_data_it(o['fine'])}" if o.get("fine") else ""
        if c.get("offerta"):
            righe.append(f"🏷️ **In offerta da {info.get('offerta_negozio')}: {ss_euro(c['prezzo'])}** (−{o['risparmio_pct']:.0f}%){fine}")
        else:
            righe.append(f"💡 **Costa meno da {info.get('offerta_negozio')}: {ss_euro(c['prezzo'])}** (−{o['risparmio_pct']:.0f}% sul solito prezzo)")
    elif info.get("risparmio_pct"):
        m = info["migliore"]
        righe.append(f"💡 Costa meno da **{info.get('migliore_negozio')}**: {ss_fmt_unitario(m['unitario'], m['base']) if m.get('confrontabile') and m.get('unitario') and m.get('base') != 'pz' else ss_euro(m['prezzo'])}"
                     f" (−{info['risparmio_pct']}%)")
    return righe


def dp_attesa_in_offerta(ss, d, oggi_=None, volantini=None):
    """{id_attesa: testo} per le voci «se conviene» (e da decidere) che oggi sono in offerta."""
    out = {}
    for v in d.get("spesa_attesa") or []:
        if v.get("tipo") not in ("offerta", "decidere"):
            continue
        try:
            x = ss_esauriti_con_offerta(ss, {"spesa": [dict(v, preso=False)]}, oggi_, volantini)
        except Exception:
            x = []
        if x:
            out[v["id"]] = x[0][1]
    return out


# =====================================================================================================================
# aggancio a spesa.py: quando un prodotto finisce (o scende sotto la scorta minima)
# =====================================================================================================================
def _spesa_finito(d, r, motivo="finito"):                            # noqa: F811 — sostituisce «mettilo subito in lista»
    return dp_finito(d, r, motivo)


def _spesa_sotto_minima(d, r):                                         # noqa: F811
    return dp_sotto_minima(d, r)


# =====================================================================================================================
# Streamlit
# =====================================================================================================================
_DP_CSS = """<style>
.dp-box{border:2px solid #ffb300;border-radius:16px;padding:10px 12px;margin:8px 0;background:rgba(255,179,0,.08)}
.dp-off{border:2px solid #00e676;border-radius:12px;padding:6px 10px;margin:4px 0;background:rgba(0,230,118,.10);font-weight:700}
.dp-voce{border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:8px 10px;margin:6px 0;background:rgba(255,255,255,.04)}
</style>"""


def _dp_dati():
    try:
        return carica_dati(crea_archivio(), st.session_state.get("percorso") or percorso_mio())
    except Exception:
        return {}


def _dp_ss():
    try:
        ss, _disp = _ss_leggi()
        return ss
    except Exception:
        return None


def _dp_volantini():
    try:
        return _ss_offerte_volantini()
    except Exception:
        return None


def _dp_ricarica():
    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()


def _dp_negozi(ss):
    try:
        return sorted({ss_nome_negozio(n).split(" · ")[0] for n in (ss or {}).get("negozi") or []})
    except Exception:
        return []


def _dp_scelte_voce(v, k, ricarica, offerta_txt=""):
    """I 4 bottoni per una voce in attesa (+ la scelta della data per «più avanti»)."""
    nome = v.get("nome", "") + (f" · {v['marca']}" if v.get("marca") else "")
    sotto = ("tornato oggi: era tra i «più avanti»" if v.get("tornato") else
             "sotto la scorta minima" if v.get("motivo") == "scorta" else f"finito il {ss_data_it(v.get('dal'))}" if v.get("dal") else "finito")
    st.markdown(f"<div class='dp-voce'><b>{sc_esc(nome)}</b><br><small>{sc_esc(sotto)}</small></div>", unsafe_allow_html=True)
    if offerta_txt:
        st.markdown(f"<div class='dp-off'>🔥 In offerta: {sc_esc(offerta_txt)}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    scelta = None
    if c1.button("🛒 Mettilo nella lista", key=f"{k}_l", type="primary", width="stretch"):
        scelta = ("lista", None, "chiedi")
    if c2.button("🚫 Non lo ricompro", key=f"{k}_m", width="stretch"):
        scelta = ("mai", None, "chiedi")
    c3, c4 = st.columns(2, gap="small")
    if v.get("tipo") != "offerta" and c3.button("💭 Solo se conviene", key=f"{k}_o", width="stretch", help="Lo tengo da parte: ti avviso quando è in offerta"):
        scelta = ("offerta", None, "chiedi")
    with c4.popover("⏰ Più avanti", width="stretch"):
        quando = st.radio("Quando?", ["1 settimana", "2 settimane", "1 mese", "Scelgo la data"], key=f"{k}_qq", horizontal=False)
        oggi_ = dp_oggi()
        giorni = {"1 settimana": 7, "2 settimane": 14, "1 mese": 30}.get(quando)
        data = oggi_ + _dp_dt.timedelta(days=giorni) if giorni else st.date_input("Data", value=oggi_ + _dp_dt.timedelta(days=7),
                                                                                       min_value=oggi_ + _dp_dt.timedelta(days=1), format="DD/MM/YYYY", key=f"{k}_qd")
        poi = st.radio("Quel giorno…", ["chiedi", "lista"], key=f"{k}_qp",
                       format_func=lambda x: "❓ me lo richiedi" if x == "chiedi" else "🛒 lo metti in lista da solo")
        if st.button("✅ Va bene", key=f"{k}_qok", type="primary", width="stretch"):
            scelta = ("dopo", data, poi)
    if scelta:
        cosa, data, poi = scelta
        esito = {}

        def _fn(d):
            voce = dp_decidi(d, v["id"], cosa, data, poi)
            esito["sugg"] = bool(voce) and cosa == "lista" and dp_suggerisci_sempre(d, voce)
        salva(_fn, "Spesa: " + {"lista": "in lista", "mai": "non lo ricompro", "offerta": "se conviene", "dopo": "più avanti"}[cosa] + " · " + v.get("nome", ""))
        st.session_state["messaggio"] = {"lista": f"🛒 {v.get('nome')} è nella lista della spesa.", "mai": f"🚫 {v.get('nome')}: non te lo propongo più.",
                                         "offerta": f"💭 {v.get('nome')}: ti avviso quando è in offerta.",
                                         "dopo": f"⏰ {v.get('nome')}: te lo ripropongo il {data:%d/%m/%Y}." if data else ""}[cosa]
        if esito.get("sugg"):
            st.session_state["dp_sugg_sempre"] = {k_: v.get(k_, "") for k_ in ("nome", "marca", "barcode")}
        ricarica()


def _dp_sugg_sempre(ricarica):
    s = st.session_state.get("dp_sugg_sempre")
    if not s:
        return
    with st.container(border=True):
        st.markdown(f"💡 **{sc_esc(s.get('nome'))}**: le ultime volte l'hai sempre rimesso in lista. Quando finisce, **lo metto in lista da solo**?")
        a, b = st.columns(2, gap="small")
        if a.button("✅ Sì, sempre", key="dp_sugg_si", type="primary", width="stretch"):
            salva(lambda d: dp_imposta_regola(d, s, quando="sempre"), "Spesa: regola «sempre in lista»")
            st.session_state.pop("dp_sugg_sempre", None)
            ricarica()
        if b.button("No, chiedimelo", key="dp_sugg_no", width="stretch"):
            st.session_state.pop("dp_sugg_sempre", None)
            ricarica()


def dp_sezioni_spesa(ricarica=None):
    """Sopra la lista della spesa: ❓ da decidere · 🏷️ se conviene · ⏰ più avanti."""
    ricarica = ricarica or _dp_ricarica
    st.markdown(_DP_CSS, unsafe_allow_html=True)
    d = _dp_dati()
    if any(v.get("tipo") == "dopo" and v.get("quando") and v["quando"] <= dp_oggi().isoformat() for v in d.get("spesa_attesa") or []):
        esito = {}
        salva(lambda dd: esito.update(zip(("lista", "decidere"), dp_maturati(dd))), "Spesa: arrivato il giorno dei «più avanti»")
        if esito.get("lista"):
            st.success("⏰ Oggi in lista: " + ", ".join(esito["lista"]))
        d = _dp_dati()
    _dp_sugg_sempre(ricarica)
    attesa = d.get("spesa_attesa") or []
    if not attesa:
        return
    ss = _dp_ss()
    off = dp_attesa_in_offerta(ss, d, dp_oggi(), _dp_volantini()) if ss else {}
    for tipo in ("decidere", "offerta", "dopo"):
        voci = [v for v in attesa if v.get("tipo") == tipo]
        if not voci:
            continue
        n_off = sum(1 for v in voci if v["id"] in off)
        titolo = DP_TIPI[tipo] + f" ({len(voci)})" + (f" · 🔥 {n_off} in offerta" if n_off else "")
        with st.expander(titolo, expanded=(tipo == "decidere" or n_off > 0)):
            if tipo == "offerta":
                st.caption("Non sono nella lista: si accendono 🔥 quando li trovo in offerta (prezzi di Spesa Smart e volantini).")
            if tipo == "dopo":
                st.caption("Tornano il giorno scelto: da decidere, oppure direttamente in lista.")
            for v in sorted(voci, key=lambda x: (x["id"] not in off, x.get("quando") or "", x.get("nome") or "")):
                if tipo == "dopo":
                    q = ss_data_it(v.get("quando")) if v.get("quando") else ""
                    st.markdown(f"<div class='dp-voce'><b>{sc_esc(v.get('nome'))}</b><br><small>⏰ il {q} · "
                                f"{'🛒 andrà in lista da solo' if v.get('poi') == 'lista' else '❓ te lo richiedo'}</small></div>", unsafe_allow_html=True)
                    a, b = st.columns(2, gap="small")
                    if a.button("🛒 Mettilo ora in lista", key=f"dp_do_l_{v['id']}", width="stretch"):
                        salva(lambda dd, v=v: dp_decidi(dd, v["id"], "lista"), "Spesa: in lista · " + v.get("nome", ""))
                        ricarica()
                    if b.button("🗑️ Togli", key=f"dp_do_x_{v['id']}", width="stretch"):
                        salva(lambda dd, v=v: dp_decidi(dd, v["id"], "togli"), "Spesa: tolto · " + v.get("nome", ""))
                        ricarica()
                else:
                    _dp_scelte_voce(v, f"dp_{tipo}_{v['id']}", ricarica, off.get(v["id"], ""))


def dp_box_finiti():
    """In Dispensa, sotto i messaggi: «❓ Finito: cosa faccio?» per i prodotti appena finiti (al massimo 3, gli altri nella Spesa)."""
    st.markdown(_DP_CSS, unsafe_allow_html=True)
    d = _dp_dati()
    _dp_sugg_sempre(st.rerun)
    voci = [v for v in d.get("spesa_attesa") or [] if v.get("tipo") == "decidere"]
    if not voci:
        return
    ss = _dp_ss()
    off = dp_attesa_in_offerta(ss, d, dp_oggi(), _dp_volantini()) if ss else {}
    with st.container(key="dp_box_finiti"):
        st.markdown(f"<div class='dp-box'><b>❓ {'È finito' if len(voci) == 1 else f'Sono finiti {len(voci)} prodotti'}: cosa faccio?</b><br>"
                    "<small>Non li metto in lista da solo: scegli tu. Puoi decidere anche dopo, nella scheda 🛒 Spesa.</small></div>", unsafe_allow_html=True)
        for v in voci[-3:][::-1]:
            _dp_scelte_voce(v, f"dpb_{v['id']}", st.rerun, off.get(v["id"], ""))


def _dp_pannello_prezzo(r, ss):
    k = f"dpp_{r.get('id')}"
    with st.expander("💶 Prezzo, peso e prezzo al kg"):
        st.caption("Il prezzo va nell'archivio di 🛒 Spesa Smart: così sai dove costa meno e quando è in offerta.")
        a_peso = st.toggle("⚖️ Venduto a peso (frutta, verdura, carne, gastronomia…)", key=k + "_peso")
        neg_noti = _dp_negozi(ss)
        if a_peso:
            c1, c2 = st.columns(2, gap="small")
            ekg = c1.number_input("Prezzo al kg (€)", min_value=0.0, step=0.10, format="%.2f", key=k + "_ekg")
            gr = c2.number_input("Quanti grammi", min_value=0, step=50, value=1000, key=k + "_gr")
            prezzo = dp_prezzo_da_peso(ekg, gr) if ekg and gr else None
            st.caption(f"Hai pagato **{ss_euro(prezzo)}**" if prezzo else "Scrivi prezzo al kg e grammi.")
            conf, val, uni = 1, float(gr or 0), "g"
        else:
            c1, c2 = st.columns(2, gap="small")
            prezzo = c1.number_input("Prezzo pagato (€)", min_value=0.0, step=0.05, format="%.2f", key=k + "_p")
            conf = c2.number_input("Confezioni", min_value=1, step=1, value=1, key=k + "_c", help="Per esempio 3 se era una confezione da 3 × 500 g")
            c3, c4 = st.columns(2, gap="small")
            fv0 = ss_num(r.get("formato_valore"))
            val = c3.number_input("Peso / contenuto di 1 pezzo", min_value=0.0, step=50.0, value=float(fv0 or 0), key=k + "_v")
            unita = ["g", "kg", "ml", "l", "pz", "lavaggi"]
            u0 = dp_unita_ss(r.get("formato_unita")) or "g"
            uni = c4.selectbox("Unità", unita, index=unita.index(u0) if u0 in unita else 0, key=k + "_u")
            pu, base = ss_prezzo_unitario(prezzo, conf, val, uni) if prezzo else (None, None)
            if pu:
                st.markdown(f"➡️ Prezzo al {('kg' if base == 'kg' else 'litro' if base == 'l' else base)}: **{ss_fmt_unitario(pu, base)}**")
        neg = ss_campo_negozio(ss, k + "_n") if ss is not None else (None, None)      # lo stesso modo semplice di Spesa Smart
        data = st.date_input("📅 Data", value=dp_oggi(), max_value=dp_oggi(), format="DD/MM/YYYY", key=k + "_d")
        promo = st.checkbox("🏷️ Era in offerta", key=k + "_pr")
        pieno = st.number_input("Prezzo normale (senza offerta, €)", min_value=0.0, step=0.05, format="%.2f", key=k + "_pp") if promo else None
        if st.button("💾 Salva il prezzo", key=k + "_ok", type="primary", width="stretch"):
            esito = {}

            def _fn(ss_):
                ril, _p, err = dp_registra_prezzo(ss_, r, prezzo, neg, conf, val or None, uni, data.isoformat(), promo=promo, prezzo_pieno=pieno)
                esito.update(err=err, ril=ril)
            try:
                _ss_salva(_fn, "prezzo dalla Dispensa · " + r.get("nome", ""))
            except Exception as e:
                esito["err"] = [f"Non riesco a salvare ({type(e).__name__})."]
            if esito.get("err"):
                for e in esito["err"]:
                    st.error(e)
            else:
                if val and not r.get("formato_valore") and uni not in ("pz",):
                    try:
                        def _f2(d):
                            for a in d.get("articoli") or []:
                                if dp_chiave(a) == dp_chiave(r):
                                    a["formato_valore"], a["formato_unita"] = val, ("L" if uni == "l" else uni)
                        salva(_f2, "Peso del prodotto · " + r.get("nome", ""))
                    except Exception:
                        pass
                ril = esito.get("ril") or {}
                st.session_state["messaggio"] = f"💶 Prezzo salvato: {ss_euro(prezzo)}" + (
                    f" · {ss_fmt_unitario(ril.get('prezzo_unitario'), ril.get('unita_base'))}" if ril.get("prezzo_unitario") and ril.get("unita_base") != "pz" else "")
                st.rerun()


def _dp_pannello_regola(r):
    d = _dp_dati()
    reg = dp_regola(d, r)
    k = f"dpr_{r.get('id')}"
    with st.expander(f"⚙️ Quando finisce: {DP_REGOLE[reg['quando']]}" + (f" · scorta minima {reg['minima']:g}" if reg.get("minima") else "")):
        quando = st.radio("Quando finisce…", list(DP_REGOLE), index=list(DP_REGOLE).index(reg["quando"]), format_func=DP_REGOLE.get, key=k + "_q")
        minima = st.number_input("📦 Scorta minima (0 = nessuna): quando ne restano così pochi, è come se fosse finito", min_value=0.0, step=1.0,
                                 value=float(reg.get("minima") or 0), key=k + "_m")
        if st.button("💾 Salva la regola", key=k + "_ok", width="stretch"):
            salva(lambda dd: dp_imposta_regola(dd, r, quando=quando, minima=minima), "Regola «quando finisce» · " + r.get("nome", ""))
            st.session_state["messaggio"] = f"⚙️ {r.get('nome')}: {DP_REGOLE[quando]}" + (f", scorta minima {minima:g}" if minima else "")
            st.rerun()


def dp_pannello(r):
    """Sotto la scheda di un prodotto della Dispensa: prezzi, 🛒 in lista, regola «quando finisce»."""
    st.markdown(_DP_CSS, unsafe_allow_html=True)
    ss = _dp_ss()
    info = dp_info_prezzi(ss, r) if ss else {}
    righe = dp_testi_prezzo(info) if info else []
    with st.container(border=True, key=f"dp_pan_{r.get('id')}"):
        if righe:
            for x in righe:
                st.markdown(x)
            if len(info.get("storico") or []) > 1:
                st.caption("📈 Ultimi prezzi: " + " → ".join(f"{ss_euro(p_)}" for _d, p_, _u, _b in info["storico"] if p_))
        else:
            st.caption("💶 Nessun prezzo ancora: aggiungilo qui sotto (serve per sapere dove costa meno).")
        d = _dp_dati()
        ch = dp_chiave(r)
        gia = dp_in_lista(d, ch)
        c1, c2 = st.columns([1, 2], gap="small", vertical_alignment="bottom")
        q = c1.number_input("Quanti", min_value=1, step=1, value=1, key=f"dp_q_{r.get('id')}")
        if c2.button("🛒 " + ("Aggiorna la quantità in lista" if gia else "Metti nella lista della spesa"), key=f"dp_lista_{r.get('id')}", type="primary", width="stretch"):
            esito = {}
            salva(lambda dd: esito.__setitem__("e", dp_metti_in_lista(dd, r, q)), "In lista dalla Dispensa · " + r.get("nome", ""))
            st.session_state["messaggio"] = f"🛒 {r.get('nome')}: " + ("quantità aggiornata nella lista." if esito.get("e") == "aggiornato" else f"messo nella lista della spesa ({q}).")
            st.rerun()
        if gia:
            st.caption("✅ È già nella lista della spesa.")
    _dp_pannello_prezzo(r, ss)
    _dp_pannello_regola(r)


def dp_negozio_spesa(k):
    """Sopra i prodotti presi: DOVE hai fatto la spesa (uno per tutti). Ritorna (negozio_id, negozio nuovo) o None."""
    ss = _dp_ss()
    if ss is None:
        return None
    return ss_campo_negozio(ss, k, etichetta="🏪 Dove hai fatto la spesa")


def dp_campi_prezzo_presi(x, ss_neg=None):
    """Nella lista della spesa, per un prodotto preso: quanto l'hai pagato (facoltativo). Il negozio è quello scelto sopra. Ritorna (prezzo, negozio)."""
    p = st.number_input("💶 Pagato (€, facoltativo)", min_value=0.0, step=0.05, format="%.2f", key=f"dp_sp_p_{x['id']}")
    return p, ss_neg


def dp_salva_prezzi_presi(voci):
    """voci = [(riga della lista, prezzo, negozio)]: salva i prezzi validi nell'archivio di Spesa Smart. Ritorna quanti."""
    buone = [(x, p, n) for x, p, n in voci if p and p > 0 and n and (not isinstance(n, (tuple, list)) or n[0] or (n[1] or {}).get("nome"))]
    if not buone:
        return 0
    conta = {"n": 0}

    def _fn(ss_):
        for x, p, n in buone:
            ril, _pp, err = dp_registra_prezzo(ss_, x, p, n, 1, x.get("formato_valore"), x.get("formato_unita"))
            if ril:
                conta["n"] += 1
    try:
        _ss_salva(_fn, "prezzi dalla lista della spesa")
    except Exception:
        return 0
    return conta["n"]


# --- agganci ------------------------------------------------------------------------------------------------------------
if "pn_scadenze" in globals() and "_dp_scad_prima" not in globals():
    _dp_scad_prima = pn_scadenze

    def pn_scadenze():                                                   # noqa: F811 — 🔔 finiti da decidere, «più avanti» arrivati, «se conviene» in offerta
        out = _dp_scad_prima()
        try:
            d = _dp_dati()
            oggi_ = dp_oggi().isoformat()
            voci = []
            for v in d.get("spesa_attesa") or []:
                if v.get("tipo") == "decidere":
                    voci.append(f"❓ {v.get('nome')}: è finito, lo ricompri?")
                elif v.get("tipo") == "dopo" and v.get("quando") and v["quando"] <= oggi_:
                    voci.append(f"⏰ {v.get('nome')}: è il giorno di ricomprarlo?")
            if voci:
                out = dict(out)
                out["dispensa"] = list(out.get("dispensa") or []) + voci
            ss = _dp_ss()
            if ss:
                off = dp_attesa_in_offerta(ss, {"spesa_attesa": [v for v in d.get("spesa_attesa") or [] if v.get("tipo") == "offerta"]},
                                           dp_oggi(), _dp_volantini())
                if off:
                    nomi = {v["id"]: v.get("nome") for v in d.get("spesa_attesa") or []}
                    out = dict(out)
                    out["spesa_smart"] = list(out.get("spesa_smart") or []) + [f"🏷️ {nomi.get(i)} (se conviene): {t_}" for i, t_ in off.items()]
        except Exception:
            pass
        return out
