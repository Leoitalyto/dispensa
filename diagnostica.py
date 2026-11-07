# -*- coding: utf-8 -*-
"""AUTO · DIAGNOSTICA VEICOLI — la voce che riunisce tutto in un posto solo.

Sei pulsanti (come da richiesta):
 1. 📷 Fotografa una spia            → la diagnosi visiva che c'è già (auto_diagnosi.py), IA a scelta, anche gratuita
 2. 📚 Consulta archivio spie        → archivio in 14 categorie (diagnostica_spie.py) + base condivisa (auto_base.py)
 3. 🔌 Collega dispositivo           → dongle OBD-II Bluetooth BLE, SPERIMENTALE (diagnostica_ble.py)
 4. 🔢 Leggi codici errore           → codici scritti o incollati, spiegati in italiano (diagnostica_dtc.py)
 5. 🗂️ Consulta storico guasti       → spie fotografate, letture di codici e consulti, con stato, intervento fatto e note
 6. 🤖 Chiedi all'assistente AI      → incrocia foto, modello, anno, codici, sintomi e storico; distingue guasto CONFERMATO / PROBABILE / POSSIBILE CAUSA / CONTROLLO e non dà mai un'ipotesi per certa

Regole che il programma fa rispettare (non solo l'IA):
• «Guasto confermato» è ammesso solo se l'IA lo appoggia a un codice letto o a una spia vista nella foto: altrimenti il programma lo declassa a «probabile».
• Con un pericolo (gravità rossa o «non proseguire») il programma mostra per primo l'avviso di fermarsi; non propone mai di continuare a guidare se il rischio non si può escludere.
• I dati del veicolo vengono da quelli già registrati; se mancano marca, modello, anno o alimentazione si possono completare qui.
Caricato per ultimo fra i moduli della diagnostica (dopo diagnostica_ble.py)."""
import html as _h_dg
import json
import re
import uuid
from datetime import datetime

import streamlit as st

DG_VOCI = [("foto", "📷 Fotografa una spia", "dg_h_foto"), ("archivio", "📚 Consulta archivio spie", "dg_h_arch"), ("dispositivo", "🔌 Collega dispositivo diagnostico", "dg_h_disp"),
           ("codici", "🔢 Leggi codici errore", "dg_h_cod"), ("storico", "🗂️ Consulta storico guasti", "dg_h_sto"), ("assistente", "🤖 Chiedi all'assistente AI", "dg_h_ass")]

_DG_HUB_CSS = """<style>
.st-key-dg_hub[data-testid='stVerticalBlock'],.st-key-dg_hub [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:8px 0 12px}
.st-key-dg_hub button{width:100% !important;min-height:74px !important;border-radius:18px !important;color:#fff !important;border:2px solid rgba(255,255,255,.55) !important;box-shadow:0 4px 0 rgba(0,0,0,.18),0 6px 14px rgba(0,0,0,.2) !important}
.st-key-dg_hub button p{color:#fff !important;font-weight:900 !important;font-size:.98rem !important;line-height:1.15 !important;text-shadow:0 1px 3px rgba(0,0,0,.5);margin:0}
.st-key-dg_h_foto button{background:linear-gradient(135deg,#ffa726,#e65100) !important}.st-key-dg_h_arch button{background:linear-gradient(135deg,#42a5f5,#0d47a1) !important}
.st-key-dg_h_disp button{background:linear-gradient(135deg,#8e24aa,#4527a0) !important}.st-key-dg_h_cod button{background:linear-gradient(135deg,#26a69a,#00695c) !important}
.st-key-dg_h_sto button{background:linear-gradient(135deg,#8d6e63,#4e342e) !important}.st-key-dg_h_ass button{background:linear-gradient(135deg,#ec407a,#ad1457) !important}
.dg-ass-r{background:#ffebee;border:2px solid #b71c1c;border-radius:12px;padding:10px 12px;color:#b71c1c;font-weight:900;margin:6px 0}
.dg-el{border-radius:12px;padding:9px 12px;margin:6px 0;border-left:6px solid #9e9e9e;background:#f5f5f5;color:#1b2b2b}
.dg-el b{display:block;margin-bottom:2px}</style>"""

_DG_STATI = ["Aperto", "In osservazione", "Risolto"]
_SPEC_STORICO = [("stato", "Stato del problema", "s", _DG_STATI), ("intervento", "Intervento effettuato", "a", None), ("data_intervento", "Data dell'intervento", "d", None), ("note", "Annotazioni", "a", None)]
_SPEC_LETTURE = [("sintomi", "Cosa notavi", "a", None), ("km", "Chilometri", "n", None)] + _SPEC_STORICO
_SPEC_CONSULTI = _SPEC_STORICO


# ---------------------------------------------------------------------------------------------------------------------
# i dati del mezzo (identificazione)
# ---------------------------------------------------------------------------------------------------------------------
def dg_dati_mezzo(v):
    """Se mancano dati importanti per interpretare spie e codici, lo dice e permette di completarli (si salvano nel veicolo)."""
    if not v:
        st.info("Nessun veicolo scelto: puoi usare la diagnostica lo stesso, indicando marca e modello a mano (campo facoltativo nelle schermate).")
        return
    mancano = [e for k, e in (("marca", "marca"), ("modello", "modello"), ("anno", "anno di immatricolazione"), ("alimentazione", "alimentazione")) if not str(v.get(k) or "").strip()]
    desc = " ".join(x for x in (v.get("marca"), v.get("modello"), v.get("anno")) if x)
    st.markdown(f"<div class='au-card'><b class='t'>{_h_dg.escape(v.get('tipo_veicolo') or 'Mezzo')}: {_h_dg.escape(desc or _au_nome(v))}</b><br><small>{_h_dg.escape(str(v.get('alimentazione') or 'alimentazione non indicata'))}"
                + (f" · {_h_dg.escape(str(v['cilindrata']))} cc" if v.get("cilindrata") else "") + (f" · {_h_dg.escape(str(v['kw']))} kW" if v.get("kw") else "") + (f" · {_h_dg.escape(str(v['allestimento']))}" if v.get("allestimento") else "") + "</small></div>", unsafe_allow_html=True)
    if not mancano:
        return
    st.warning("Per interpretare meglio spie e codici mi servono ancora: **" + ", ".join(mancano) + "**. Puoi completarli qui sotto (si salvano nella scheda del veicolo).")
    with st.form(f"dg_dati_{v['id']}", border=False):
        c1, c2 = st.columns(2, gap="small")
        marca = c1.text_input("Marca", value=str(v.get("marca") or ""), key=f"dg_m_{v['id']}")
        modello = c2.text_input("Modello", value=str(v.get("modello") or ""), key=f"dg_mo_{v['id']}")
        c3, c4 = st.columns(2, gap="small")
        anno = c3.text_input("Anno", value=str(v.get("anno") or ""), key=f"dg_a_{v['id']}")
        alim = c4.selectbox("Alimentazione", [""] + list(_AU_ALIM), index=([""] + list(_AU_ALIM)).index(v.get("alimentazione")) if v.get("alimentazione") in _AU_ALIM else 0, key=f"dg_al_{v['id']}")
        ok = st.form_submit_button("💾 Salva i dati del mezzo", type="primary", width="stretch")
    if ok:
        def _fn(x, d=dict(marca=marca.strip(), modello=modello.strip(), anno=anno.strip(), alimentazione=alim)):
            for k, val in d.items():
                if val:
                    x[k] = val
        _au_mod(v["id"], _fn, "Diagnostica: dati del mezzo")
        st.session_state["messaggio"] = "✅ Dati del mezzo salvati."
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# lo storico guasti (foto, letture, consulti)
# ---------------------------------------------------------------------------------------------------------------------
def _dg_voci_storico(v):
    """Tutte le voci dello storico: [(data, tipo, titolo, stato, gravita)] in ordine dal più recente."""
    out = []
    for d_ in v.get("diagnosi", []):
        nomi = ", ".join(s.get("nome", "") for s in d_.get("spie", [])[:2])
        grav = "rosso" if any(s.get("colore") == "rosso" or s.get("urgenza") == "critica" for s in d_.get("spie", [])) else ("giallo" if d_.get("spie") else "")
        out.append((str(d_.get("data") or ""), "foto", f"🔍 Spia fotografata: {nomi or 'diagnosi'}", d_.get("stato") or "Aperto", grav, d_))
    for l in v.get("letture", []):
        cod = ", ".join(c.get("codice", "") for c in l.get("codici", [])[:4])
        gr = [dtc_info(c["codice"])["it"]["g"] if dtc_info(c["codice"])["it"] else "" for c in l.get("codici", []) if c.get("codice") and c["codice"][0] in "PBCU"]
        grav = "rosso" if "rosso" in gr else ("giallo" if "giallo" in gr else "")
        out.append((str(l.get("data") or ""), "lettura", f"🔢 Lettura codici: {cod or 'nessun codice'}", l.get("stato") or "Aperto", grav, l))
    for c in v.get("consulti", []):
        out.append((str(c.get("data") or ""), "consulto", f"🤖 Consulto: {(c.get('riepilogo') or c.get('sintomi') or '')[:60]}", c.get("stato") or "Aperto", c.get("gravita", ""), c))
    return sorted(out, key=lambda x: x[0], reverse=True)


def dg_storico(v):
    """Lo storico dei problemi del veicolo: spie fotografate, letture di codici e consulti dell'assistente. Ogni voce: consulta, correggi, allega, invia, elimina."""
    st.markdown("#### 🗂️ Storico guasti")
    if not v:
        st.info("Lo storico è legato a un veicolo: scegline uno in alto.")
        return
    voci = _dg_voci_storico(v)
    aperti = sum(1 for x in voci if x[3] != "Risolto")
    st.caption(f"{len(voci)} voci · {aperti} ancora aperte o in osservazione. Per ogni voce puoi segnare **lo stato**, l'**intervento effettuato** e le tue **annotazioni**.")
    scelta = _au_scegli("Mostra", ["Tutto insieme", "🔍 Spie fotografate", "🔢 Letture codici", "🤖 Consulti"], f"dg_sto_{v['id']}")
    if scelta == "Tutto insieme":
        filtro = st.selectbox("Stato", ["Tutti", "Aperto", "In osservazione", "Risolto"], key="dg_sto_stato", label_visibility="collapsed")
        mostra = [x for x in voci if filtro == "Tutti" or x[3] == filtro]
        if not mostra:
            st.info("Ancora nessuna voce: ogni diagnosi da foto, lettura di codici o consulto che salvi compare qui.")
        for data, tipo, titolo, stato, grav, it in mostra:
            ic = {"rosso": "🔴", "giallo": "🟡"}.get(grav, "⚪")
            extra = [x for x in (("Intervento: " + it["intervento"]) if it.get("intervento") else "", ("Note: " + it["note"]) if it.get("note") else "") if x]
            st.markdown(f"<div class='au-card'><b class='t'>{ic} {_h_dg.escape(titolo)}</b><br><small>{_h_dg.escape(_au_it(data[:10]) if data else '')}{(' ' + _h_dg.escape(data[11:16])) if len(data) > 11 else ''} · stato: <b>{_h_dg.escape(stato)}</b>"
                        + "".join("<br>" + _h_dg.escape(e) for e in extra) + "</small></div>", unsafe_allow_html=True)
        st.caption("Per correggere, allegare, inviare o eliminare apri la scheda del tipo (qui sopra).")
    elif scelta == "🔍 Spie fotografate":
        if not v.get("diagnosi"):
            st.info("Nessuna spia fotografata e salvata: usa «📷 Fotografa una spia».")
        _ad_storico(v)
    elif scelta == "🔢 Letture codici":
        _au_elenco(v, "letture", "Letture", _SPEC_LETTURE, lambda x: f"{_au_it(str(x.get('data'))[:10])} · {', '.join(c.get('codice', '') for c in x.get('codici', [])[:4]) or 'lettura'}",
                   lambda x: [("Fonte: " + x["fonte"]) if x.get("fonte") else "", "Codici: " + "; ".join(f"{c.get('codice')} {c.get('titolo') or ''}".strip() for c in x.get("codici", [])) if x.get("codici") else "",
                              ("Cosa notavi: " + x["sintomi"]) if x.get("sintomi") else "", ("Km: " + str(x["km"])) if x.get("km") else "", ("Batteria 12V: %.1f V" % x["tensione_12v"]) if x.get("tensione_12v") else "",
                              "Stato: " + (x.get("stato") or "Aperto"), ("Intervento: " + x["intervento"]) if x.get("intervento") else "", ("Annotazioni: " + x["note"]) if x.get("note") else ""],
                   "Nessuna lettura salvata. In «Leggi codici errore» scrivi i codici e tocca «Salva questa lettura».", "Aggiungi una lettura a mano", ordine="data", icona="🔢", aggiorna_km=True)
    else:
        _au_elenco(v, "consulti", "Consulti", _SPEC_CONSULTI, lambda x: f"{_au_it(str(x.get('data'))[:10])} · {(x.get('riepilogo') or x.get('sintomi') or 'consulto')[:70]}",
                   lambda x: [("Sintomi: " + x["sintomi"]) if x.get("sintomi") else "", ("Codici: " + ", ".join(x["codici"])) if x.get("codici") else "", "Può proseguire? " + x["puo_proseguire_testo"] if x.get("puo_proseguire_testo") else "",
                              "Stato: " + (x.get("stato") or "Aperto"), ("Intervento: " + x["intervento"]) if x.get("intervento") else "", ("Annotazioni: " + x["note"]) if x.get("note") else ""],
                   "Nessun consulto salvato. In «Chiedi all'assistente AI» puoi salvare la risposta.", "Aggiungi un consulto a mano", ordine="data", icona="🤖", aggiorna_km=False)


# ---------------------------------------------------------------------------------------------------------------------
# l'assistente AI
# ---------------------------------------------------------------------------------------------------------------------
_SYS_ASS = ("Sei un assistente per la diagnosi di veicoli (auto, moto, furgoni, camion, autobus, mezzi agricoli, elettrici) e per il soccorso. Parli in italiano semplice: ogni termine tecnico va spiegato tra parentesi. "
            "Ti do: mezzo, anno e motorizzazione, eventuali codici di errore LETTI dalla centralina, sintomi descritti dall'utente, eventuale spia vista in una foto e lo storico dei problemi precedenti. "
            "Devi DISTINGUERE sempre fra: «guasto_confermato» (SOLO se un codice letto o una spia vista nella foto lo indicano direttamente: indica in «basato_su» quel codice o «foto»), «guasto_probabile» (molto verosimile ma non confermato), "
            "«possibile_causa» (una delle cause da considerare) e «controllo» (una verifica pratica da fare). NON presentare mai un'ipotesi come diagnosi certa. Se i dati non bastano dillo e proponi i controlli. "
            "Sicurezza: se c'è un possibile pericolo (freni, sterzo, pressione olio, surriscaldamento, alta tensione, airbag, fumo, odore di bruciato) il primo elemento deve essere un avviso, «puo_proseguire» = «no» e «avviso_sicurezza» spiega di accostare e spegnere. "
            "Non consigliare MAI di continuare a guidare se non puoi escludere un rischio. Nei veicoli elettrici o ibridi non consigliare mai di toccare o tagliare i cavi arancioni. "
            'Rispondi SOLO con un oggetto JSON, senza altro testo: {"riepilogo": "2-3 frasi semplici", "puo_proseguire": "no|forse|si_con_prudenza", "avviso_sicurezza": "", '
            '"elementi": [{"tipo": "guasto_confermato|guasto_probabile|possibile_causa|controllo", "testo": "...", "gravita": "rosso|giallo|verde", "basato_su": ["P0420", "foto", "sintomi"]}], "domande_utili": ["..."]}.')
_TIPI_EL = {"guasto_confermato": ("✅", "Guasto confermato", "#2e7d32"), "guasto_probabile": ("🟠", "Guasto probabile", "#e65100"), "possibile_causa": ("🟡", "Possibile causa", "#f9a825"), "controllo": ("🔎", "Controllo da fare", "#0277bd")}
_ORD_EL = ["guasto_confermato", "guasto_probabile", "possibile_causa", "controllo"]


def dg_contesto(v, codici, sintomi, con_foto, con_storico, mezzo):
    """Il testo con tutto quello che l'assistente deve incrociare."""
    righe = [f"Mezzo: {mezzo}."]
    if v:
        dett = [f"{k}: {v[k]}" for k in ("tipo_veicolo", "alimentazione", "anno", "cilindrata", "kw", "classe_euro", "km_attuali", "allestimento") if v.get(k)]
        if dett:
            righe.append("Dati del veicolo: " + "; ".join(dett) + ".")
    if codici:
        righe.append("Codici di errore LETTI: " + "; ".join(f"{c} ({dtc_riepilogo(dtc_info(c))[1] or 'senza descrizione'})" if c[0] in "PBCU" else c for c in codici) + ".")
    else:
        righe.append("Nessun codice di errore letto.")
    righe.append("Sintomi descritti dall'utente: " + (sintomi.strip() or "nessuno descritto") + ".")
    if con_foto and v and v.get("diagnosi"):
        ultima = sorted(v["diagnosi"], key=lambda x: x.get("data", ""))[-1]
        righe.append("Spie viste nell'ultima foto: " + "; ".join(f"{s.get('nome')} ({s.get('colore')})" for s in ultima.get("spie", [])) + ".")
    if con_storico and v:
        storico = [x for x in _dg_voci_storico(v)][:5]
        if storico:
            righe.append("Storico recente dei problemi: " + " | ".join(f"{x[0][:10]} {x[2]} (stato: {x[3]}" + (f", intervento: {x[5]['intervento']}" if x[5].get("intervento") else "") + ")" for x in storico) + ".")
    return "\n".join(righe)


def dg_normalizza_risposta(d, codici):
    """Fa rispettare le regole al posto dell'IA: niente «confermato» senza codice o foto; l'avviso di pericolo per primo; mai «puoi proseguire» se c'è un rosso."""
    elementi = []
    for e in (d.get("elementi") or []):
        if not isinstance(e, dict) or not e.get("testo"):
            continue
        tipo = e.get("tipo") if e.get("tipo") in _TIPI_EL else "possibile_causa"
        base = [str(b).upper() for b in (e.get("basato_su") or [])]
        if tipo == "guasto_confermato" and not any(b in [c.upper() for c in codici] or b == "FOTO" for b in base):
            tipo = "guasto_probabile"                                          # non c'è un codice letto né una spia vista: non si può dire «confermato»
        grav = e.get("gravita") if e.get("gravita") in ("rosso", "giallo", "verde") else "giallo"
        elementi.append({"tipo": tipo, "testo": str(e["testo"])[:400], "gravita": grav, "basato_su": base})
    elementi.sort(key=lambda e: _ORD_EL.index(e["tipo"]))
    # gravità dei codici letti secondo il database locale (non secondo l'IA)
    grav_codici = [dtc_info(c)["it"]["g"] for c in codici if c and c[0] in "PBCU" and dtc_info(c)["it"]]
    rosso = "rosso" in grav_codici or any(e["gravita"] == "rosso" for e in elementi)
    prosegui = str(d.get("puo_proseguire") or "").lower()
    if rosso or prosegui not in ("si_con_prudenza",):
        testo_p = "NO: fermati in sicurezza e spegni il veicolo. Non proseguire." if rosso or prosegui == "no" else "Non è possibile escludere un rischio: fermati in sicurezza e fai controllare prima di proseguire."
        sicuro = False
    else:
        testo_p = "Solo con prudenza e se la guida è normale: raggiungi l'officina piano, senza sforzare il mezzo; se noti anomalie fermati subito."
        sicuro = True
    return {"riepilogo": str(d.get("riepilogo") or "")[:600], "avviso": str(d.get("avviso_sicurezza") or "")[:400], "puo_proseguire": prosegui if prosegui else "forse", "puo_proseguire_testo": testo_p,
            "puo_proseguire_ok": sicuro, "elementi": elementi, "domande": [str(x)[:200] for x in (d.get("domande_utili") or [])][:4], "gravita": "rosso" if rosso else ("giallo" if elementi else "")}


def _dg_json(testo):
    m = re.search(r"\{.*\}", testo or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def dg_riepilogo_senza_ia(codici):
    """Senza IA: cosa dicono i codici letti secondo il database locale (gravità e cosa controllare)."""
    voci = []
    for c in codici:
        if c and c[0] in "PBCU":
            info = dtc_info(c)
            g, t = dtc_riepilogo(info)
            voci.append((c, g, t or "senza descrizione gratuita", (info["it"] or {}).get("c", [])))
    return voci


def dg_assistente(v):
    """«Chiedi all'assistente AI»: incrocia foto, modello, codici, sintomi e storico."""
    st.markdown("#### 🤖 Chiedi all'assistente AI")
    st.caption("Scrivi cosa noti e, se ce li hai, i codici di errore. L'assistente li incrocia con il modello del mezzo, l'ultima spia fotografata e lo storico, e ti risponde **distinguendo** ciò che è confermato da ciò che è solo probabile. "
               "Non dà mai un'ipotesi per diagnosi certa.")
    if "dg_ass_codici" in st.session_state:
        st.session_state["dg_ass_cod"] = (st.session_state.get("dg_ass_cod", "") + " " + st.session_state.pop("dg_ass_codici")).strip()
    elif "dg_ass_cod" not in st.session_state and st.session_state.get("dg_ultimi_codici"):
        st.session_state["dg_ass_cod"] = " ".join(st.session_state["dg_ultimi_codici"])
    sintomi = st.text_area("Cosa noti? (rumori, strappi, fumo, odori, quando succede…)", key="dg_ass_sint", height=90, placeholder="es. strappi in accelerazione a freddo, la spia motore si è accesa ieri")
    cod_t = st.text_input("Codici di errore letti (facoltativo)", key="dg_ass_cod", placeholder="es. P0420 P0171")
    c1, c2 = st.columns(2, gap="small")
    con_foto = c1.checkbox("Includi l'ultima spia fotografata", value=True, key="dg_ass_foto", disabled=not (v and v.get("diagnosi")))
    con_storico = c2.checkbox("Includi lo storico recente", value=True, key="dg_ass_stor", disabled=not (v and _dg_voci_storico(v)))
    codici = [c["codice"] for c in dtc_estrai(cod_t)]
    mezzo = bd_scope_desc(bd_scope(v), v) if "bd_scope" in globals() else (_au_nome(v) if v else "mezzo non specificato")
    contesto = dg_contesto(v, codici, sintomi, con_foto, con_storico, mezzo)
    # ---- riepilogo senza IA: sempre disponibile
    if codici:
        st.markdown("**📋 Cosa dicono i codici (senza IA, dal database locale)**")
        voci = dg_riepilogo_senza_ia(codici)
        if any(g == "rosso" for _c, g, _t, _k in voci):
            st.markdown("<div class='dg-ass-r'>🔴 PERICOLO — almeno un codice è grave: fermati in sicurezza e spegni il veicolo. Non proseguire.</div>", unsafe_allow_html=True)
        for c, g, t, k in voci:
            st.markdown(f"- {DTC_GRAVITA.get(g, DTC_GRAVITA[''])[0]} **{c}** — {t}" + (f" · controlla: {'; '.join(k[:3])}" if k else ""))
    ris = st.session_state.get("dg_ass_ris")
    if "ad_attivo" in globals() and ad_attivo():
        if st.button("🤖 Chiedi all'assistente", key="dg_ass_vai", type="primary", width="stretch"):
            if not (sintomi.strip() or codici):
                st.warning("Scrivi almeno un sintomo o un codice.")
            else:
                prov = ad_provider_scelto()
                cfg = ad_cfg(prov)
                if cfg["fonte"] == "app" and not ad_puo():
                    st.session_state["dg_ass_ris"] = {"errore": ad_errore_stop()}
                else:
                    with st.spinner("L'assistente sta ragionando…"):
                        testo, err = _ad_invia(prov, cfg, _SYS_ASS, [("u", contesto)], None, 1800, json_out=True)
                    d = _dg_json(testo) if not err else None
                    st.session_state["dg_ass_ris"] = {"errore": err or "formato"} if not d else dict(dg_normalizza_risposta(d, codici), ok=True, sintomi=sintomi.strip(), codici=codici, fonte=AD_PROVIDER[prov]["nome"].split(" (")[0])
                ris = st.session_state.get("dg_ass_ris")
    else:
        st.info("🤖 L'IA dell'app non è attiva: qui sopra hai già il riepilogo dei codici. **Senza pagare** puoi anche copiare queste istruzioni nella tua app di IA (ChatGPT, Gemini, Claude…); oppure scegli un'IA nella scheda «📷 Fotografa una spia».")
        st.code(contesto + "\n\nSpiegami in italiano semplice cosa può essere, distinguendo fra guasto confermato (solo se c'è un codice letto o una spia vista), guasto probabile, possibile causa e controllo da fare. "
                           "Non presentare ipotesi come certezze. Se c'è un possibile pericolo dimmi di fermarmi in sicurezza; non dirmi mai di continuare a guidare se non puoi escludere un rischio.", language=None)
        cols = st.columns(3, gap="small")
        for i, (nome_ia, url) in enumerate(_AD_APP_IA):
            cols[i % 3].link_button(nome_ia, url, width="stretch")
    if ris:
        _dg_mostra_risposta(ris, v)


def _dg_mostra_risposta(r, v):
    if not r.get("ok"):
        ad_mostra_errore(r.get("errore"), {"limite_app": "Hai raggiunto il tetto di analisi dell'app (per ora o per oggi). Riprova più tardi.", "limite": "Limite di analisi raggiunto: riprova più tardi.", "chiave": "La chiave dell'IA non è valida o manca.", "rete": "Non riesco a collegarmi al servizio adesso.", "rifiuto": "Il servizio non ha potuto rispondere.",
                    "formato": "La risposta non era leggibile: riprova.", "pagamento": "Questo modello è a pagamento: scegline uno «:free».", "modello": "Questo modello non esiste più o non legge il testo: cambia modello."}.get(r.get("errore"), "Qualcosa non ha funzionato."))
        return
    st.markdown(_DG_HUB_CSS, unsafe_allow_html=True)
    if not r["puo_proseguire_ok"] or r.get("avviso"):
        st.markdown(f"<div class='dg-ass-r'>⚠️ {_h_dg.escape(r.get('avviso') or 'Possibile pericolo.')} — {_h_dg.escape(r['puo_proseguire_testo'])}</div>", unsafe_allow_html=True)
    if r.get("riepilogo"):
        st.markdown("**In breve:** " + r["riepilogo"])
    st.markdown(f"**Posso proseguire il viaggio?** {r['puo_proseguire_testo']}")
    for e in r["elementi"]:
        ic, nome, col = _TIPI_EL[e["tipo"]]
        st.markdown(f"<div class='dg-el' style='border-left-color:{col}'><b>{ic} {nome}</b>{_h_dg.escape(e['testo'])}"
                    + (f"<br><small>basato su: {_h_dg.escape(', '.join(e['basato_su']))}</small>" if e.get("basato_su") else "") + "</div>", unsafe_allow_html=True)
    if r.get("domande"):
        st.markdown("**Per capire meglio, rispondi se puoi:** " + " · ".join(r["domande"]))
    fonte_r = r.get("fonte") or "un'IA"
    st.caption(f"Risposta di {fonte_r}. È un aiuto, **non una diagnosi certa**: per il tuo mezzo vale il manuale e il parere di un meccanico.")
    if v and st.button("💾 Salva questa consulenza nello storico", key="dg_ass_salva", width="stretch"):
        voce = {"id": uuid.uuid4().hex[:8], "data": datetime.now().strftime("%Y-%m-%d %H:%M"), "sintomi": r.get("sintomi", ""), "codici": r.get("codici", []), "riepilogo": r.get("riepilogo", ""),
                "puo_proseguire_testo": r["puo_proseguire_testo"], "elementi": r["elementi"], "gravita": r.get("gravita", ""), "stato": "Aperto", "intervento": "", "note": "", "files": []}
        _au_mod(v["id"], lambda x, vv=voce: x.setdefault("consulti", []).append(vv), "Diagnostica: consulto")
        st.session_state["messaggio"] = "✅ Consulenza salvata nello storico."
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# la voce «Diagnostica veicoli» di Auto
# ---------------------------------------------------------------------------------------------------------------------
def tab_diagnostica(v=None):
    """La schermata «🩺 Diagnostica veicoli»: sei pulsanti e, sotto, la funzione scelta."""
    st.markdown(_DG_HUB_CSS, unsafe_allow_html=True)
    vista = st.session_state.get("dg_vista")
    if vista:
        if st.button("← Diagnostica veicoli", key="dg_indietro", width="stretch"):
            st.session_state.pop("dg_vista", None)
            st.rerun()
        {"foto": lambda: ad_pagina(v), "archivio": lambda: (aa_pagina(v), bd_pannello(v)), "dispositivo": lambda: dg_dispositivo(v), "codici": lambda: dtc_pannello(v),
         "storico": lambda: dg_storico(v), "assistente": lambda: dg_assistente(v), "proposte": lambda: pr_pannello_admin()}.get(vista, lambda: None)()
        return
    st.markdown("<div style='background:linear-gradient(135deg,#00897b,#004d40);color:#fff;border-radius:18px;padding:14px 18px;margin:4px 0 8px'><b style='font-size:1.15rem'>🩺 Diagnostica veicoli</b><br>"
                "<small>Capisci cosa vuol dire una spia o un codice di errore, e cosa fare. Vale per auto, moto, furgoni, camion, autobus e mezzi da lavoro. Nessun dispositivo è obbligatorio.</small></div>", unsafe_allow_html=True)
    dg_dati_mezzo(v)
    with st.container(key="dg_hub"):
        scelte = [st.button(t, key=k, width="stretch") for _id, t, k in DG_VOCI]
    for (id_, _t, _k), premuto in zip(DG_VOCI, scelte):
        if premuto:
            st.session_state["dg_vista"] = id_
            st.rerun()
    if (st.session_state.get("sess") or {}).get("admin") and "pr_conta_attesa" in globals():          # solo per l'amministratore: le proposte degli utenti da verificare
        n_pr = pr_conta_attesa()
        if st.button(f"🛠️ Proposte da verificare ({n_pr})" + (" 🔔" if n_pr else ""), key="dg_proposte", type="primary" if n_pr else "secondary", width="stretch"):
            st.session_state["dg_vista"] = "proposte"
            st.rerun()
    n_arch = len(_AE_SPIE) if "_AE_SPIE" in globals() else 0
    st.caption(f"📚 {n_arch} spie nel catalogo · 🔢 {len(dtc_db()) or len(DTC_IT)} codici di errore · tutto dentro l'app, senza IA e senza servizi esterni. L'IA è facoltativa e serve per l'analisi da foto e per l'assistente.")
    st.caption("Non è una diagnosi certa: per il tuo veicolo vale il manuale. Con una spia rossa, fermati in sicurezza.")
