# -*- coding: utf-8 -*-
"""👵 Badante (in Casa, SOLO per l'amministratore): le spese per la badante, i soldi consegnati e quando finiranno.
Dati in d["badante"] = {tariffa, ore, giorni_sett:[0..6], inizio, giorni:{data:{importo,ore,nota}}, consegne:[{id,data,importo,nota}], note, contatti}.
bdt_calcolo() è puro (la stessa regola è copiata in promemoria.py per gli avvisi 3 giorni prima e l'ultimo giorno)."""
import datetime as _bd_dt

import streamlit as st

BDT_GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]


def _bdt_d(x):
    try:
        return _bd_dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def bdt_inizio(b):
    """Da quando si contano le spese: la data scelta nelle Impostazioni, altrimenti il giorno della PRIMA consegna di soldi."""
    ini = _bdt_d(b.get("inizio"))
    if ini:
        return ini
    date_ = [_bdt_d(c.get("data")) for c in (b.get("consegne") or []) if isinstance(c, dict)]
    date_ = [x for x in date_ if x]
    return min(date_) if date_ else None


def bdt_costo(b, giorno):
    """Quanto costa la badante in quel giorno: scelta del giorno, altrimenti la tariffa se è un giorno di lavoro."""
    ov = (b.get("giorni") or {}).get(giorno.isoformat())
    if isinstance(ov, dict):
        return float(ov.get("importo") or 0)
    ini = bdt_inizio(b)
    if ini and giorno < ini:
        return 0.0
    if giorno.weekday() in (b.get("giorni_sett") if isinstance(b.get("giorni_sett"), list) else range(7)):
        return float(b.get("tariffa", 20) or 0)
    return 0.0


def bdt_calcolo(b, oggi):
    """→ {dato, speso, saldo, fine (ultimo giorno coperto o None), giorni_rimasti}"""
    dato = sum(float(c.get("importo") or 0) for c in (b.get("consegne") or []) if isinstance(c, dict) and (_bdt_d(c.get("data")) or oggi) <= oggi)
    ini = bdt_inizio(b)                  # ogni giorno di lavoro conta da solo come «venuta» (tariffa e ore normali), salvo i giorni cambiati a mano
    speso = 0.0
    if ini:
        g = ini
        while g <= oggi:
            speso += bdt_costo(b, g)
            g += _bd_dt.timedelta(days=1)
    saldo = dato - speso
    fine, resto, g = None, saldo, oggi
    for _ in range(730):
        g += _bd_dt.timedelta(days=1)
        c = bdt_costo(b, g)
        if c <= 0:
            continue
        if resto - c < -0.005:
            break
        resto -= c
        fine = g
    if fine is None and saldo >= 0:
        fine = oggi                      # oggi è l'ultimo giorno pagato
    return {"dato": dato, "speso": speso, "saldo": saldo, "fine": fine, "giorni_rimasti": (fine - oggi).days if fine else None}


def _bdt_cfg(d):
    b = d.get("badante")
    return b if isinstance(b, dict) else {}


def _bdt_salva(fn, msg):
    def _m(d):
        b = d.setdefault("badante", {})
        b.setdefault("tariffa", 20.0)
        b.setdefault("ore", 2.0)
        b.setdefault("giorni_sett", list(range(7)))
        b.setdefault("giorni", {})
        b.setdefault("consegne", [])
        fn(b)
    sc_salva(_m, msg)


def _bdt_corpo():
    if not bool((st.session_state.get("sess") or {}).get("admin")):
        st.error("Questa parte è solo per l'amministratore.")
        return
    d = sc_dati()
    b = _bdt_cfg(d)
    oggi_ = sc_oggi()
    tariffa = float(b.get("tariffa", 20) or 0)
    ore = float(b.get("ore", 2) or 0)
    if not bdt_inizio(b):
        st.info("Per cominciare segna i soldi consegnati (qui sotto): da quel giorno l'app conta le spese da sola.")
    elif not b.get("inizio"):
        st.caption(f"Conto le spese dal {sc_data_scritta(bdt_inizio(b))}, giorno della prima consegna (si cambia in «⚙️ Impostazioni»).")
    r = bdt_calcolo(b, oggi_)
    colore = "#20e6ff" if r["saldo"] >= 0 else "#ff5c7a"
    if r["fine"] is not None and r["giorni_rimasti"] is not None:
        quando = ("fino a OGGI" if r["giorni_rimasti"] == 0 else f"fino a {sc_data_scritta(r['fine'])} ({r['giorni_rimasti']} " + ("giorno" if r["giorni_rimasti"] == 1 else "giorni") + ")")
        frase = f"I soldi bastano {quando}."
    elif r["saldo"] < 0:
        frase = "I soldi sono già finiti: devi consegnarne altri."
    else:
        frase = "Nessun giorno di lavoro previsto."
    st.markdown(f"<div style='padding:12px;border-radius:16px;border:2px solid {colore};background:#0a1626;text-align:center;box-shadow:0 0 14px {colore}66'>"
                f"<div style='color:#8ff3ff;font-size:.85rem'>RIMASTO DA DARE ALLA BADANTE</div><div style='color:#fff;font-size:1.7rem;font-weight:800'>{sc_esc(sc_euro(r['saldo']))}</div>"
                f"<div style='color:#e9eefb'>{sc_esc(frase)}</div>"
                f"<div style='color:#9fb0cc;font-size:.8rem'>consegnati {sc_esc(sc_euro(r['dato']))} · spesi {sc_esc(sc_euro(r['speso']))}</div></div>", unsafe_allow_html=True)
    # oggi
    st.markdown("### 📆 Oggi")
    ov = (b.get("giorni") or {}).get(oggi_.isoformat())
    costo_oggi = bdt_costo(b, oggi_)
    st.caption(f"Oggi: {sc_euro(costo_oggi)}" + (f" ({ov.get('nota')})" if isinstance(ov, dict) and ov.get("nota") else "")
               + f". **Ogni giorno conta da solo come venuta** ({ore:g} h · {sc_euro(tariffa)}): tocca **❌ Non è venuta** solo se non è venuta, "
               "oppure «Un altro giorno o un altro importo» se è rimasta più o meno ore.")
    c1, c2 = st.columns(2, gap="small")
    if c1.button(f"✅ Venuta ({ore:g} h · {sc_euro(tariffa)})", key="bdt_oggi_ok", width="stretch"):
        _bdt_salva(lambda bb: bb["giorni"].__setitem__(oggi_.isoformat(), {"importo": tariffa, "ore": ore, "nota": ""}), "Badante: oggi")
        sc_rerun()
    if c2.button("❌ Non è venuta", key="bdt_oggi_no", width="stretch"):
        _bdt_salva(lambda bb: bb["giorni"].__setitem__(oggi_.isoformat(), {"importo": 0.0, "ore": 0.0, "nota": "non è venuta"}), "Badante: oggi no")
        sc_rerun()
    with st.expander("✍️ Un altro giorno o un altro importo"):
        gg = st.date_input("Giorno", value=oggi_, format="DD/MM/YYYY", key="bdt_gg")
        a1, a2 = st.columns(2, gap="small")
        ore_x = a1.number_input("Ore", min_value=0.0, value=ore, step=0.5, key="bdt_ore_x")
        imp_x = a2.number_input("Importo (€)", min_value=0.0, value=bdt_costo(b, gg) or tariffa, step=1.0, format="%.2f", key=f"bdt_imp_x_{gg.isoformat()}")
        nota_x = st.text_input("Nota (es. è rimasta di più)", key="bdt_nota_x")
        x1, x2 = st.columns(2, gap="small")
        if x1.button("💾 Salva il giorno", key="bdt_x_ok", type="primary", width="stretch"):
            _bdt_salva(lambda bb: bb["giorni"].__setitem__(gg.isoformat(), {"importo": float(imp_x), "ore": float(ore_x), "nota": nota_x.strip()}), "Badante: giorno")
            sc_rerun()
        if (b.get("giorni") or {}).get(gg.isoformat()) is not None and x2.button("↩️ Torna normale", key="bdt_x_no", width="stretch"):
            _bdt_salva(lambda bb: bb["giorni"].pop(gg.isoformat(), None), "Badante: giorno normale")
            sc_rerun()
    # soldi dati alla mamma
    st.markdown("### 💶 Soldi consegnati")
    cons = sorted([c for c in (b.get("consegne") or []) if isinstance(c, dict)], key=lambda c: c.get("data") or "", reverse=True)
    for c in cons[:6]:
        k1, k2 = st.columns([4, 1], gap="small")
        k1.markdown(f"**{sc_esc(sc_euro(c.get('importo')))}** · {sc_data_scritta(_bdt_d(c.get('data')), False)}" + (f" · {sc_esc(c['nota'])}" if c.get("nota") else ""))
        if k2.button("🗑️", key=f"bdt_dc_{c['id']}", help="Togli", width="stretch"):
            _bdt_salva(lambda bb, cid=c["id"]: bb.__setitem__("consegne", [x for x in bb["consegne"] if x.get("id") != cid]), "Badante: consegna tolta")
            sc_rerun()
    if len(cons) > 6:
        st.caption(f"…e altre {len(cons) - 6} più vecchie.")
    with st.expander("➕ Ho dato dei soldi a mia madre", expanded=not cons):
        y1, y2 = st.columns(2, gap="small")
        dg = y1.date_input("Quando", value=oggi_, format="DD/MM/YYYY", key="bdt_dg")
        di = y2.number_input("Quanto (€)", min_value=0.0, step=10.0, format="%.2f", key="bdt_di")
        dn = st.text_input("Nota (facoltativa)", key="bdt_dn")
        if st.button("💾 Segna i soldi dati", key="bdt_d_ok", type="primary", width="stretch"):
            if di <= 0:
                st.error("Scrivi quanto hai dato.")
            else:
                _bdt_salva(lambda bb: bb["consegne"].append({"id": sc_id(), "data": dg.isoformat(), "importo": float(di), "nota": dn.strip()}), "Badante: soldi dati")
                for s in ("bdt_di", "bdt_dn"):
                    st.session_state.pop(s, None)
                sc_rerun()
    # impostazioni
    with st.expander("⚙️ Impostazioni (tariffa, giorni, inizio)"):
        s1, s2 = st.columns(2, gap="small")
        n_tar = s1.number_input("Tariffa al giorno (€)", min_value=0.0, value=tariffa, step=1.0, format="%.2f", key="bdt_tar")
        n_ore = s2.number_input("Ore al giorno", min_value=0.0, value=ore, step=0.5, key="bdt_oreset")
        att = b.get("giorni_sett") if isinstance(b.get("giorni_sett"), list) else list(range(7))
        sel = st.multiselect("Giorni in cui viene di solito", BDT_GIORNI, default=[BDT_GIORNI[i] for i in att if 0 <= i < 7], key="bdt_gs")
        ini = st.date_input("Conto le spese dal giorno", value=bdt_inizio(b) or oggi_, format="DD/MM/YYYY", key="bdt_ini")
        if st.button("💾 Salva le impostazioni", key="bdt_set_ok", width="stretch"):
            _bdt_salva(lambda bb: bb.update({"tariffa": float(n_tar), "ore": float(n_ore), "giorni_sett": [BDT_GIORNI.index(x) for x in sel], "inizio": ini.isoformat()}), "Badante: impostazioni")
            st.toast("✅ Salvate")
            sc_rerun()
    # contatti e note
    st.markdown("### 📇 Contatti e note")
    contatti = st.text_area("Contatti della badante (nome, telefono…)", value=b.get("contatti", ""), key="bdt_cont", height=90)
    note = st.text_area("📝 Note", value=b.get("note", ""), key="bdt_note", height=90)
    if (contatti != b.get("contatti", "") or note != b.get("note", "")) and st.button("💾 Salva contatti e note", key="bdt_cn_ok", width="stretch"):
        _bdt_salva(lambda bb: bb.update({"contatti": contatti, "note": note}), "Badante: contatti e note")
        st.toast("✅ Salvato")
        sc_rerun()
    tel = "".join(ch for ch in (b.get("contatti") or "") if ch.isdigit() or ch == "+")
    if len(tel) >= 6:
        sc_tasti([("📞 Chiama", sc_tel_link(tel))], "bdt_call")
    st.caption("Gli avvisi (3 giorni prima e l'ultimo giorno) si regolano col tasto «🔔 Avvisi della badante», fuori da questa finestra.")


def bdt_apri():
    sc_dialogo("👵 Badante", _bdt_corpo)
