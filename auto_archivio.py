# -*- coding: utf-8 -*-
"""AUTO · ARCHIVIO COMPLETO DELLE SPIE — tutto in un solo posto (solo amministratore).

PERCHÉ: prima il testo di una spia stava nella base condivisa (auto_base.py), la foto nelle «Diagnosi salvate» del veicolo e le proposte degli utenti in un altro pannello: troppo dispersivo.
COME ORA: una pagina («🗄️ Archivio completo» in Diagnostica veicoli) con TRE sezioni:
 1. 🛠️ Le proposte da verificare (come prima, ma qui dentro);
 2. 📚 Tutte le voci della base, CON LA FOTO accanto al testo, con ricerca e filtri (colore, stato, mezzo) e i pulsanti: Conferma, Contesta, Correggi, Foto, Elimina;
 3. 📷 Le diagnosi salvate nel veicolo (con le loro foto), da cui si può aggiungere una spia alla base portandosi dietro la foto.
LA FOTO DI UNA VOCE: è una copia compressa (max 800 px) in conoscenza/foto_spie/<id>.json; la vede SOLO l'amministratore (la base condivisa resta fatta di soli testi per gli altri).
Quando la foto si allega da sola: (a) l'amministratore aggiunge una spia alla base partendo da una foto; (b) approva una proposta di un utente che aveva la foto.
Caricato dopo auto_proposte.py."""
import base64
import io
import uuid
from datetime import datetime

import streamlit as st

AR_SP_FOTO = "conoscenza/foto_spie/{}.json"
_AS_STATI = {"Tutte": "", "✅ Verificate": "verificata", "🟡 Da verificare": "da_verificare", "⚠️ Contestate": "contestata"}


def _as_admin():
    return bool((st.session_state.get("sess") or {}).get("admin"))


# ---------------------------------------------------------------------------------------------------------------------
# la foto di una voce
# ---------------------------------------------------------------------------------------------------------------------
def ar_sp_foto_leggi(eid):
    """La foto (byte JPEG) allegata alla voce, oppure None."""
    try:
        d = carica_dati(crea_archivio(), AR_SP_FOTO.format(eid))
        return base64.b64decode(d["foto"]) if d and d.get("foto") else None
    except Exception:
        return None


def ar_sp_foto_salva(eid, jpeg, solo_se_manca=False):
    """Allega la foto (compressa) alla voce. Ritorna True se l'ha salvata."""
    if not _as_admin() or not jpeg or not eid:
        return False
    if solo_se_manca and ar_sp_foto_leggi(eid):
        return False
    foto = pr_comprimi(jpeg) if "pr_comprimi" in globals() else jpeg
    if not foto:
        return False
    try:
        salva_file(AR_SP_FOTO.format(eid), lambda d: d.__setitem__("foto", base64.b64encode(foto).decode()), "Spia: foto allegata")
        return True
    except Exception:
        return False


def ar_sp_foto_togli(eid):
    if not _as_admin():
        return
    try:
        salva_file(AR_SP_FOTO.format(eid), lambda d: d.__setitem__("foto", ""), "Spia: foto tolta")
    except Exception:
        pass


def ar_foto_da_diagnosi(ref):
    """La foto di una diagnosi salvata nel veicolo (riferimento {'id', 'nome', 'mime'}) come byte, oppure None."""
    try:
        d = carica_dati(crea_archivio(), _fa_percorso_doc(ref["id"]))
        return base64.b64decode(d["b64"]) if d and d.get("b64") else None
    except Exception:
        return None


# ---------------------------------------------------------------------------------------------------------------------
# correggere una voce
# ---------------------------------------------------------------------------------------------------------------------
def bd_modifica(eid, spia, scope):
    """Solo amministratore: corregge nome, colore, urgenza, significato, azioni, cause, aspetto e mezzo di una voce. Ritorna True se l'ha fatto."""
    if not _as_admin():
        return False
    colore = str(spia.get("colore") or "").lower()
    nome = str(spia.get("nome") or "").strip()
    if len(nome) < 3 or colore not in _BD_COLORI:
        return False

    def _fn(lista):
        for e in lista:
            if e.get("id") == eid:
                e.update({"nome": nome[:140], "colore": colore, "urgenza": str(spia.get("urgenza") or "media")[:20], "significato": str(spia.get("significato") or "")[:500],
                          "azioni": [str(x)[:300] for x in (spia.get("azioni") or []) if str(x).strip()][:8], "cause": [str(x)[:160] for x in (spia.get("cause") or []) if str(x).strip()][:8],
                          "aspetto": str(spia.get("aspetto") or "")[:120], "tipo_mezzo": str((scope or {}).get("tipo", ""))[:60], "marca": str((scope or {}).get("marca", "")).strip().lower()[:40],
                          "modello": str((scope or {}).get("modello", "")).strip().lower()[:40], "ultima": _bd_oggi()})
    try:
        _bd_salva(_fn, f"Base spie: corretta {nome[:50]}")
        return True
    except Exception:
        return False


def _as_dialogo_correggi(e):
    @st.dialog("✏️ Correggi la voce")
    def _f():
        k = f"arc_{e['id']}"
        nome = st.text_input("Nome della spia", value=e.get("nome", ""), key=f"{k}_n")
        c1, c2 = st.columns(2, gap="small")
        col = c1.selectbox("Colore", list(_BD_COLORI), index=list(_BD_COLORI).index(e.get("colore")) if e.get("colore") in _BD_COLORI else 1, key=f"{k}_c")
        urg = c2.selectbox("Urgenza", ["critica", "alta", "media", "informazione"], index=["critica", "alta", "media", "informazione"].index(e.get("urgenza")) if e.get("urgenza") in ("critica", "alta", "media", "informazione") else 2, key=f"{k}_u")
        sig = st.text_area("Significato", value=e.get("significato", ""), key=f"{k}_s", height=90)
        azi = st.text_area("Cosa fare (un passo per riga)", value="\n".join(e.get("azioni", [])), key=f"{k}_a", height=100)
        cau = st.text_area("Possibili cause (una per riga)", value="\n".join(e.get("cause", [])), key=f"{k}_ca", height=80)
        asp = st.text_input("Com'è fatto il simbolo", value=e.get("aspetto", ""), key=f"{k}_p")
        d1, d2, d3 = st.columns(3, gap="small")
        tipo = d1.text_input("Mezzo", value=e.get("tipo_mezzo", ""), key=f"{k}_t")
        marca = d2.text_input("Marca (vuoto = tutti)", value=(e.get("marca") or "").title(), key=f"{k}_m")
        modello = d3.text_input("Modello (vuoto = tutti)", value=(e.get("modello") or "").title(), key=f"{k}_o")
        if st.button("💾 Salva le correzioni", key=f"{k}_ok", type="primary", width="stretch"):
            ok = bd_modifica(e["id"], {"nome": nome, "colore": col, "urgenza": urg, "significato": sig, "azioni": azi.splitlines(), "cause": cau.splitlines(), "aspetto": asp}, {"tipo": tipo, "marca": marca, "modello": modello})
            st.session_state["messaggio"] = "✅ Voce corretta." if ok else "Non sono riuscito a salvare: controlla il nome (almeno 3 lettere)."
            st.rerun()
    _f()


def _as_dialogo_elimina(e):
    @st.dialog("🗑️ Eliminare questa voce?")
    def _f():
        st.warning(f"Elimino **{e.get('nome', '')}** dalla base condivisa (e la sua foto). Non si può annullare.")
        c1, c2 = st.columns(2, gap="small")
        if c1.button("🗑️ Sì, elimina", key=f"are_{e['id']}", type="primary", width="stretch"):
            ar_sp_foto_togli(e["id"])
            bd_admin(e["id"], "elimina")
            st.session_state["messaggio"] = "🗑️ Voce eliminata."
            st.rerun()
        if c2.button("No", key=f"arn_{e['id']}", width="stretch"):
            st.rerun()
    _f()


def _as_dialogo_foto(e, v):
    @st.dialog("📷 Foto della voce")
    def _f():
        k = f"arf_{e['id']}"
        att = ar_sp_foto_leggi(e["id"])
        if att:
            st.image(att, caption="Foto attuale (la vedi solo tu)", width="stretch")
            if st.button("🗑️ Togli questa foto", key=f"{k}_t", width="stretch"):
                ar_sp_foto_togli(e["id"])
                st.session_state["messaggio"] = "Foto tolta."
                st.rerun()
        st.markdown("**Aggiungi o cambia la foto**")
        diag = [d_ for d_ in ((v or {}).get("diagnosi") or []) if d_.get("files")]
        if diag:
            nomi = [f"{_au_it(d_.get('data'))}: " + ", ".join(s['nome'] for s in d_.get('spie', [])[:2]) for d_ in diag]
            sc = st.selectbox("Dalle mie diagnosi salvate", nomi, key=f"{k}_d")
            if st.button("📎 Usa la foto di questa diagnosi", key=f"{k}_u", width="stretch"):
                foto = ar_foto_da_diagnosi(diag[nomi.index(sc)]["files"][0])
                ok = bool(foto) and ar_sp_foto_salva(e["id"], foto)
                st.session_state["messaggio"] = "✅ Foto collegata alla voce." if ok else "Non sono riuscito a leggere quella foto."
                st.rerun()
        else:
            st.caption("Non ci sono diagnosi con foto salvate in questo veicolo.")
        up = st.file_uploader("Oppure scegli una foto dal telefono", type=["jpg", "jpeg", "png", "webp"], key=f"{k}_f")
        if up is not None and st.button("📎 Usa questa foto", key=f"{k}_fu", width="stretch"):
            ok = ar_sp_foto_salva(e["id"], up.getvalue())
            st.session_state["messaggio"] = "✅ Foto collegata alla voce." if ok else "Non sono riuscito a salvare la foto."
            st.rerun()
    _f()


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def _as_scheda(e, v, n):
    stato, su, giu = bd_stato(e)
    ic = _BD_ICONA.get(e.get("colore"), "⚪")
    etic = {"verificata": "✅ Verificata", "contestata": "⚠️ Contestata", "da_verificare": "🟡 Da verificare"}[stato]
    foto = ar_sp_foto_leggi(e["id"])
    mezzo = " · ".join(x for x in (e.get("tipo_mezzo"), (e.get("marca", "") + " " + e.get("modello", "")).strip().title()) if x)
    with st.expander(f"{ic} {e['nome']} — {etic}" + (" 📷" if foto else "")):
        if foto:
            st.image(foto, caption="La foto di questa voce (la vedi solo tu)", width="stretch")
        else:
            st.caption("📷 Nessuna foto allegata a questa voce: toccando «Foto» puoi aggiungerla.")
        righe = [f"**Colore:** {e.get('colore', '')} · **Urgenza:** {e.get('urgenza', '')}", f"**Vale per:** {mezzo or 'tutti i mezzi'}"]
        if e.get("aspetto"):
            righe.append(f"**Com'è fatto il simbolo:** {e['aspetto']}")
        if e.get("simbolo_iso"):
            righe.append(f"**Codice simbolo:** {e['simbolo_iso']}")
        if e.get("significato"):
            righe.append(f"**Significato:** {e['significato']}")
        st.markdown("  \n".join(righe))
        if e.get("azioni"):
            st.markdown("**Cosa fare**\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(e["azioni"], 1)))
        if e.get("cause"):
            st.caption("Possibili cause: " + ", ".join(e["cause"]) + ".")
        st.caption(f"Fonti: {'; '.join(e.get('fonti') or ['—'])} · Aggiunta il {e.get('creata', '')} · usata {e.get('usi', 1)} volte · 👍 {su} · 👎 {giu}")
        b1, b2 = st.columns(2, gap="small")
        if b1.button("✅ Conferma" if stato != "verificata" else "↩️ Togli la conferma", key=f"arv_{n}_{e['id']}", width="stretch"):
            bd_admin(e["id"], "conferma" if stato != "verificata" else "ripristina")
            st.rerun()
        if b2.button("⚠️ Contesta" if stato != "contestata" else "↩️ Togli la contestazione", key=f"arx_{n}_{e['id']}", width="stretch"):
            bd_admin(e["id"], "contesta" if stato != "contestata" else "ripristina")
            st.rerun()
        c1, c2, c3 = st.columns(3, gap="small")
        if c1.button("✏️ Correggi", key=f"arm_{n}_{e['id']}", width="stretch"):
            _as_dialogo_correggi(e)
        if c2.button("📷 Foto", key=f"arp_{n}_{e['id']}", width="stretch"):
            _as_dialogo_foto(e, v)
        if c3.button("🗑️ Elimina", key=f"ard_{n}_{e['id']}", width="stretch"):
            _as_dialogo_elimina(e)


def ar_pagina_admin(v=None):
    """La pagina «🗄️ Archivio completo»: proposte, voci della base con foto, diagnosi salvate."""
    if not _as_admin():
        return
    st.markdown("<style>.st-key-as_pag [data-testid='stExpander'] summary p{font-weight:800}</style>", unsafe_allow_html=True)
    voci = bd_leggi()
    n_ver = sum(1 for e in voci if bd_stato(e)[0] == "verificata")
    n_foto = sum(1 for e in voci if ar_sp_foto_leggi(e["id"]))                  # pochi file, solo amministratore
    st.markdown("### 🗄️ Archivio completo delle spie")
    st.success(f"**{len(voci)}** voci nella base ({n_ver} verificate) · **{n_foto}** con foto · **{pr_conta_attesa() if 'pr_conta_attesa' in globals() else 0}** proposte da verificare. Qui trovi tutto insieme: testo e foto.")
    if st.session_state.get("messaggio"):
        st.info(st.session_state.pop("messaggio"))
    with st.container(key="as_pag"):
        n_att = pr_conta_attesa() if "pr_conta_attesa" in globals() else 0
        if "pr_pannello_admin" in globals():
            with st.expander(f"🛠️ 1 · Proposte da verificare ({n_att})" + (" 🔔" if n_att else "")):
                pr_pannello_admin()
        st.markdown("#### 📚 2 · Le voci della base, con la foto")
        c1, c2 = st.columns([3, 2], gap="small")
        q = c1.text_input("🔍 Cerca (nome, significato, mezzo…)", key="as_q", placeholder="es. gasolio, freni, camion")
        stato_s = c2.selectbox("Stato", list(_AS_STATI), key="as_stato")
        d1, d2 = st.columns(2, gap="small")
        col_s = d1.selectbox("Colore", ["Tutti"] + [f"{_BD_ICONA[c]} {c}" for c in _BD_COLORI], key="as_col")
        tipi = sorted({e.get("tipo_mezzo") for e in voci if e.get("tipo_mezzo")})
        tipo_s = d2.selectbox("Mezzo", ["Tutti"] + tipi, key="as_tipo")
        solo_foto = st.checkbox("Mostra solo le voci con foto", key="as_solofoto")
        sel = []
        for e in sorted(voci, key=lambda x: (x.get("ultima") or "", x.get("creata") or ""), reverse=True):
            if _AS_STATI[stato_s] and bd_stato(e)[0] != _AS_STATI[stato_s]:
                continue
            if col_s != "Tutti" and e.get("colore") != col_s.split(" ", 1)[1]:
                continue
            if tipo_s != "Tutti" and e.get("tipo_mezzo") != tipo_s:
                continue
            testo = " ".join(str(e.get(k, "")) for k in ("nome", "significato", "aspetto", "tipo_mezzo", "marca", "modello")).lower() + " " + " ".join(e.get("azioni", []) + e.get("cause", [])).lower()
            if q.strip() and not all(p in testo for p in q.lower().split()):
                continue
            if solo_foto and not ar_sp_foto_leggi(e["id"]):
                continue
            sel.append(e)
        if not voci:
            st.info("La base è ancora vuota: si riempie con le spie che aggiungi tu o che approvi dalle proposte.")
        elif not sel:
            st.info("Nessuna voce corrisponde ai filtri.")
        limite = st.session_state.get("as_limite", 12)
        for e in sel[:limite]:
            _as_scheda(e, v, "l")
        if len(sel) > limite:
            st.caption(f"Ne mostro {limite} su {len(sel)}.")
            if st.button("➕ Mostra altre", key="as_altre", width="stretch"):
                st.session_state["as_limite"] = limite + 12
                st.rerun()
        st.markdown("#### 📷 3 · Le diagnosi salvate nel veicolo")
        diag = sorted((v or {}).get("diagnosi", []), key=lambda x: x.get("data", ""), reverse=True)
        if not diag:
            st.caption("Nessuna diagnosi salvata in questo veicolo. Quando fai una foto, tocca «💾 Salva nel veicolo» per tenerla qui.")
        for d_ in diag:
            titolo = f"{_au_it(d_.get('data'))}: " + ", ".join(s["nome"] for s in d_.get("spie", [])[:2])
            with st.expander("🔍 " + titolo + (" 📷" if d_.get("files") else "")):
                foto = ar_foto_da_diagnosi(d_["files"][0]) if d_.get("files") else None
                if foto:
                    st.image(foto, width="stretch")
                for s_ in d_.get("spie", []):
                    st.markdown(f"**{_BD_ICONA.get(s_.get('colore'), '⚪')} {s_['nome']}** — {s_.get('significato', '')}")
                st.caption(f"{d_.get('mezzo', '')} · affidabilità {d_.get('confidenza', '')}" + (f" · Stato: {d_['stato']}" if d_.get("stato") else "") + (f" · Intervento: {d_['intervento']}" if d_.get("intervento") else ""))
                if "pr_form_proponi" in globals() and d_.get("spie"):
                    sc = {"tipo": (v or {}).get("tipo_veicolo") or "", "marca": "", "modello": "", "anno": ""}
                    pr_form_proponi(d_["spie"], foto, sc, "foto", "ds" + str(d_["id"])[:8], d_.get("mezzo", ""))
