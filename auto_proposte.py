# -*- coding: utf-8 -*-
"""AUTO · PROPOSTE ALLA BASE CONDIVISA — nessuna spia entra nella base senza la verifica dell'amministratore.

PERCHÉ: la base condivisa (auto_base.py) è usata da tutti. Una voce sbagliata (per errore o per sabotaggio) potrebbe dare consigli pericolosi. Quindi:
• Le analisi dell'IA e le ricerche NON entrano più da sole nella base: restano private (storico personale).
• Chi ha trovato una spia con successo tocca un pulsante grande «Proponi alla base condivisa» e scrive PER QUALE MEZZO ha fatto la ricerca e il testo da salvare. Il programma dice chiaramente che il salvataggio avverrà SOLO dopo la verifica dell'amministratore.
• L'amministratore riceve: la FOTO (compressa, solo il cruscotto), il TESTO proposto, il TIPO DI RICERCA (foto / a parole / scritta a mano), il mezzo e il MODELLO, e chi l'ha inviata. Può correggere il testo, poi APPROVARE (la voce entra nella base già «verificata dall'amministratore») oppure RIFIUTARE (con un motivo).
• Limiti contro gli abusi: massimo 5 proposte al giorno per persona e 150 in attesa; l'amministratore vede sempre l'autore.
• Dove si vedono: l'amministratore in «Diagnostica veicoli → 🛠️ Proposte da verificare» e nella base condivisa; ogni utente vede lo stato delle SUE proposte (in attesa, approvata, rifiutata).
• Dati: conoscenza/proposte.json (elenco, solo testo) e conoscenza/proposte/<id>.json (la foto, che viene svuotata appena la proposta è decisa).
Caricato dopo auto_base.py."""
import base64
import io
import json
import re
import uuid
from datetime import datetime

import streamlit as st

PR_INDICE = "conoscenza/proposte.json"
PR_MAX_ATTESA = 150
PR_MAX_UTENTE_GIORNO = 5
_PR_TIPI_RICERCA = {"foto": "📷 foto di una spia", "parole": "🔎 ricerca a parole", "manuale": "✍️ scritta a mano dall'utente"}


def _pr_admin():
    return bool((st.session_state.get("sess") or {}).get("admin"))


def _pr_utente():
    s = st.session_state.get("sess") or {}
    return str(s.get("uid") or "anon"), str(s.get("nome") or "Utente")[:40]


def _pr_adesso():
    """L'ora italiana (il server è in UTC: senza questo il «giorno» cambierebbe all'una di notte)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Rome"))
    except Exception:
        return datetime.now()


def _pr_oggi():
    return _pr_adesso().strftime("%Y-%m-%d")


def pr_leggi():
    """Tutte le proposte (elenco): [{id, data, utente_id, utente_nome, tipo_ricerca, mezzo_tipo, marca, modello, anno, spia, nota, ha_foto, stato, motivo}]."""
    try:
        d = carica_dati(crea_archivio(), PR_INDICE)
    except Exception:
        return []
    return [p for p in (d or {}).get("proposte", []) if isinstance(p, dict) and p.get("id")]


def pr_conta_attesa():
    return sum(1 for p in pr_leggi() if p.get("stato") == "in attesa")


def pr_foto(pid):
    """La foto di una proposta (byte JPEG) oppure None."""
    try:
        d = carica_dati(crea_archivio(), f"conoscenza/proposte/{pid}.json")
        return base64.b64decode(d["foto"]) if d and d.get("foto") else None
    except Exception:
        return None


def pr_comprimi(jpeg):
    """La foto ridotta (max 800 px, qualità 70): resta leggera nell'archivio dei dati."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(jpeg)).convert("RGB")
        im.thumbnail((800, 800))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=70, optimize=True)
        return buf.getvalue()
    except Exception:
        return None


def _pr_pulisci_spia(sp):
    colore = str(sp.get("colore") or "giallo").lower()
    return {"nome": str(sp.get("nome") or "").strip()[:140], "colore": colore if colore in ("rosso", "giallo", "verde", "blu", "bianco") else "giallo",
            "urgenza": str(sp.get("urgenza") or "media")[:20], "significato": str(sp.get("significato") or "").strip()[:500],
            "azioni": [str(x).strip()[:300] for x in (sp.get("azioni") or []) if str(x).strip()][:8], "cause": [str(x).strip()[:160] for x in (sp.get("cause") or []) if str(x).strip()][:8],
            "aspetto": str(sp.get("aspetto") or "").strip()[:120], "simbolo_iso": str(sp.get("simbolo_iso") or "").strip()[:40]}


def _pr_inserisci_diretto(sp, scope, fonte, dettaglio=""):
    """Inserisce nella base una voce GIÀ verificata (solo dall'amministratore). Ritorna l'id oppure None."""
    if not _pr_admin():
        return None
    eid, _nuova = bd_registra(sp, scope, fonte, str(dettaglio or "").replace("Fonte: ", "").strip())
    if eid:
        bd_admin(eid, "conferma")
    return eid


def pr_invia(spia, scope, tipo_ricerca, jpeg=None, nota=""):
    """Un utente propone una spia. Ritorna (ok, messaggio). L'amministratore invece la inserisce subito (è già lui il verificatore)."""
    sp = _pr_pulisci_spia(spia)
    if len(sp["nome"]) < 3:
        return False, "Scrivi il nome della spia (almeno 3 lettere)."
    if not sp["significato"] and not sp["azioni"]:
        return False, "Scrivi almeno cosa significa o cosa fare."
    if not (scope or {}).get("tipo"):
        return False, "Scegli per quale mezzo hai fatto la ricerca."
    if _pr_admin():
        sc = {"tipo": scope.get("tipo", ""), "marca": (scope.get("marca") or "").strip().lower(), "modello": (scope.get("modello") or "").strip().lower(), "anno": scope.get("anno", "")}
        eid = _pr_inserisci_diretto(sp, sc, "Inserita dall'amministratore", nota)
        foto_ok = bool(eid and jpeg and "ar_sp_foto_salva" in globals() and ar_sp_foto_salva(eid, jpeg, solo_se_manca=True))      # la foto resta con la voce (la vedi solo tu, in «Archivio completo»)
        return (True, "✅ Inserita nella base (sei l'amministratore: è già verificata)." + (" 📷 La foto è allegata alla voce: la trovi in «🗄️ Archivio completo»." if foto_ok else "")) if eid else (False, "Non sono riuscito a salvare nella base.")
    uid, nome = _pr_utente()
    oggi = _pr_oggi()
    esistenti = pr_leggi()
    if sum(1 for p in esistenti if p.get("utente_id") == uid and str(p.get("data", ""))[:10] == oggi) >= PR_MAX_UTENTE_GIORNO:
        return False, f"Hai già mandato {PR_MAX_UTENTE_GIORNO} proposte oggi: riprova domani (serve a tenere la base al sicuro)."
    if sum(1 for p in esistenti if p.get("stato") == "in attesa") >= PR_MAX_ATTESA:
        return False, "Ci sono troppe proposte in attesa: riprova fra qualche giorno."
    pid = uuid.uuid4().hex[:12]
    foto = pr_comprimi(jpeg) if jpeg else None
    voce = {"id": pid, "data": _pr_adesso().strftime("%Y-%m-%d %H:%M"), "utente_id": uid, "utente_nome": nome, "tipo_ricerca": tipo_ricerca if tipo_ricerca in _PR_TIPI_RICERCA else "manuale",
            "mezzo_tipo": str(scope.get("tipo", ""))[:60], "marca": str(scope.get("marca", ""))[:40], "modello": str(scope.get("modello", ""))[:40], "anno": str(scope.get("anno", ""))[:6],
            "spia": sp, "nota": str(nota or "")[:400], "ha_foto": bool(foto), "stato": "in attesa", "motivo": ""}
    try:
        if foto:
            salva_file(f"conoscenza/proposte/{pid}.json", lambda d: d.__setitem__("foto", base64.b64encode(foto).decode()), f"Proposta spia: foto {pid}")
        salva_file(PR_INDICE, lambda d: d.setdefault("proposte", []).append(voce), f"Proposta spia: {sp['nome'][:50]}")
    except Exception:
        return False, "Non sono riuscito a inviare la proposta. Riprova fra poco."
    return True, "✅ Proposta inviata all'amministratore. Entra nella base **solo dopo la sua verifica**: qui sotto vedi lo stato."


def pr_decidi(pid, azione, spia=None, scope=None, motivo=""):
    """Solo amministratore: 'approva' (la voce entra nella base, già verificata) oppure 'rifiuta'. Ritorna (ok, messaggio)."""
    if not _pr_admin():
        return False, "Solo l'amministratore può decidere."
    voce = next((p for p in pr_leggi() if p["id"] == pid), None)
    if not voce or voce.get("stato") != "in attesa":
        return False, "Questa proposta non è più in attesa."
    if azione == "approva":
        sp = _pr_pulisci_spia(spia or voce["spia"])
        sc = scope or {"tipo": voce["mezzo_tipo"], "marca": voce["marca"], "modello": voce["modello"], "anno": voce["anno"]}
        sc = {"tipo": sc.get("tipo", ""), "marca": (sc.get("marca") or "").strip().lower(), "modello": (sc.get("modello") or "").strip().lower(), "anno": sc.get("anno", "")}
        eid = _pr_inserisci_diretto(sp, sc, f"Verificata dall'amministratore (proposta di {voce.get('utente_nome', '')})", voce.get("nota", ""))
        if not eid:
            return False, "Non sono riuscito a inserirla nella base."
        nuovo_stato = "approvata"
        if voce.get("ha_foto") and "ar_sp_foto_salva" in globals():             # la foto della proposta passa alla voce della base (solo amministratore) prima di essere svuotata
            ar_sp_foto_salva(eid, pr_foto(pid), solo_se_manca=True)
    else:
        nuovo_stato = "rifiutata"

    def _m(d):
        for p in d.get("proposte", []):
            if p.get("id") == pid:
                p["stato"] = nuovo_stato
                p["motivo"] = str(motivo or "")[:300]
                p["decisa"] = _pr_adesso().strftime("%Y-%m-%d %H:%M")
    try:
        salva_file(PR_INDICE, _m, f"Proposta spia {nuovo_stato}")
        if voce.get("ha_foto"):
            salva_file(f"conoscenza/proposte/{pid}.json", lambda d: d.__setitem__("foto", ""), "Proposta spia: foto svuotata")
    except Exception:
        return False, "Non sono riuscito a salvare la decisione."
    return True, "✅ Approvata e inserita nella base." if azione == "approva" else "🗑️ Rifiutata."


# ---------------------------------------------------------------------------------------------------------------------
# lo schermo dell'UTENTE: il pulsante grande e il modulo
# ---------------------------------------------------------------------------------------------------------------------
def pr_form_proponi(spie, jpeg, scope, tipo_ricerca, chiave, mezzo_testo=""):
    """Il pulsante grande «Proponi alla base condivisa» e, sotto, il modulo. spie = elenco di dizionari (nome, colore, significato, azioni…)."""
    if not spie or ("bd_attiva" in globals() and not bd_attiva()):
        return
    st.markdown("<style>.st-key-pr_big button{min-height:64px !important;border-radius:18px !important;font-weight:900 !important;font-size:1.08rem !important}</style>", unsafe_allow_html=True)
    k = f"pr_{chiave}"
    chi_e_admin = _pr_admin()
    st.markdown("#### 📚 Questa spia è giusta? Aiuta gli altri")
    st.info("🔒 **Non entra subito nella base condivisa:** il salvataggio avviene **SOLO dopo la verifica dell'amministratore**, che controlla la foto e il testo. Così la base resta sicura per tutti." if not chi_e_admin
            else "Sei l'amministratore: la voce entra subito nella base, già verificata.")
    with st.container(key="pr_big"):
        if st.button("📤 PROPONI ALLA BASE CONDIVISA" if not chi_e_admin else "📤 AGGIUNGI ALLA BASE CONDIVISA", key=f"{k}_apri", type="primary", width="stretch"):
            st.session_state[f"{k}_aperto"] = True
    msg = st.session_state.pop(f"{k}_msg", None)
    if msg:
        (st.success if msg[0] else st.error)(msg[1])
    if not st.session_state.get(f"{k}_aperto"):
        return
    st.caption("Verranno inviati all'amministratore: **la foto** (solo il cruscotto), **il testo** qui sotto, **il tipo di ricerca** e **il mezzo e il modello** che scrivi. Controlla che sia tutto giusto.")
    nomi = [s.get("nome", "") for s in spie]
    with st.form(f"{k}_form", border=True):
        i = 0
        if len(spie) > 1:
            sc_n = st.selectbox("Quale spia vuoi proporre", nomi, key=f"{k}_quale")
            i = nomi.index(sc_n)
        s = spie[i]
        from_tipi = list(_AU_TIPI) + ["Altro mezzo"] if "_AU_TIPI" in globals() else ["Auto", "Moto", "Camion / TIR", "Autobus / pullman", "Altro mezzo"]
        tipo0 = (scope or {}).get("tipo") or ""
        tipo = st.selectbox("🚚 Per quale mezzo hai fatto la ricerca? (obbligatorio)", [""] + [t_ for t_ in dict.fromkeys(from_tipi)], index=([""] + list(dict.fromkeys(from_tipi))).index(tipo0) if tipo0 in from_tipi else 0,
                            format_func=lambda x: x or "— scegli —", key=f"{k}_tipo")
        c1, c2 = st.columns(2, gap="small")
        marca = c1.text_input("Marca (facoltativa)", value=str((scope or {}).get("marca", "")).title(), key=f"{k}_marca", placeholder="es. Iveco")
        modello = c2.text_input("Modello (facoltativo)", value=str((scope or {}).get("modello", "")).title(), key=f"{k}_modello", placeholder="es. Daily")
        nome = st.text_input("Nome della spia", value=s.get("nome", ""), key=f"{k}_nome")
        col = st.selectbox("Colore", ["rosso", "giallo", "verde", "blu", "bianco"], index=["rosso", "giallo", "verde", "blu", "bianco"].index(s.get("colore", "giallo")) if s.get("colore") in ("rosso", "giallo", "verde", "blu", "bianco") else 1, key=f"{k}_col")
        sig = st.text_area("Cosa significa (il testo che vuoi salvare)", value=s.get("significato", ""), key=f"{k}_sig", height=80)
        azi = st.text_area("Cosa fare (un passo per riga)", value="\n".join(s.get("azioni", [])), key=f"{k}_azi", height=100)
        asp = st.text_input("Com'è fatto il simbolo (facoltativo)", value=s.get("aspetto", ""), key=f"{k}_asp", placeholder="es. filtro con una goccia")
        nota = st.text_input("Come sei sicuro che sia giusta? (facoltativo)", key=f"{k}_nota", placeholder="es. l'ho confrontata con il manuale a pag. 80")
        ok_ctrl = st.checkbox("Ho controllato il testo e la foto: è davvero questa la spia", key=f"{k}_ok")
        invia = st.form_submit_button("📤 Invia all'amministratore" if not chi_e_admin else "📤 Aggiungi alla base", type="primary", width="stretch")
    if invia:
        if not ok_ctrl:
            st.error("Spunta «Ho controllato il testo e la foto» per inviare.")
            return
        sp = {"nome": nome, "colore": col, "urgenza": "critica" if col == "rosso" else "media", "significato": sig, "azioni": [x for x in azi.splitlines() if x.strip()], "cause": s.get("cause", []), "aspetto": asp, "simbolo_iso": s.get("simbolo_iso", "")}
        ok, testo = pr_invia(sp, {"tipo": tipo, "marca": marca, "modello": modello, "anno": (scope or {}).get("anno", "")}, tipo_ricerca, jpeg, nota)
        st.session_state[f"{k}_msg"] = (ok, testo)
        if ok:
            st.session_state[f"{k}_aperto"] = False
        st.rerun()


def pr_le_mie():
    """Lo stato delle proposte inviate da questo utente."""
    uid, _n = _pr_utente()
    mie = [p for p in pr_leggi() if p.get("utente_id") == uid][-12:]
    if not mie:
        return
    with st.expander(f"📬 Le mie proposte ({len(mie)})"):
        for p in reversed(mie):
            stato = {"in attesa": "⏳ in attesa di verifica", "approvata": "✅ approvata: è nella base", "rifiutata": "❌ rifiutata"}.get(p.get("stato"), p.get("stato", ""))
            st.markdown(f"**{p['spia']['nome']}** · {p.get('mezzo_tipo', '')} — {stato}" + (f"  \n_Motivo: {p['motivo']}_" if p.get("stato") == "rifiutata" and p.get("motivo") else ""))


# ---------------------------------------------------------------------------------------------------------------------
# lo schermo dell'AMMINISTRATORE
# ---------------------------------------------------------------------------------------------------------------------
def pr_pannello_admin():
    """Le proposte da verificare: foto, testo, tipo di ricerca, mezzo e modello, e chi l'ha inviata. Correggi, poi approva o rifiuta."""
    if not _pr_admin():
        return
    prop = pr_leggi()
    attesa = [p for p in prop if p.get("stato") == "in attesa"]
    st.markdown(f"#### 🛠️ Proposte da verificare ({len(attesa)})")
    st.caption("Controlla la **foto** e il **testo**: se è giusto, **approva** e la voce entra nella base già «verificata dall'amministratore». Puoi correggere il testo prima di approvare. Se è sbagliata o sospetta, **rifiuta**.")
    if not attesa:
        st.info("Nessuna proposta in attesa.")
    for p in reversed(attesa):
        sp = p["spia"]
        ic_ = {"rosso": "🔴", "giallo": "🟡", "verde": "🟢", "blu": "🔵"}.get(sp.get("colore"), "⚪")
        with st.expander(f"{ic_} {sp['nome']} · {p.get('mezzo_tipo', '')} · da {p.get('utente_nome', '')} · {p.get('data', '')}"):
            if p.get("ha_foto"):
                f = pr_foto(p["id"])
                if f:
                    st.image(f, caption="La foto inviata", width="stretch")
                else:
                    st.caption("(la foto non è più disponibile)")
            else:
                st.caption("Nessuna foto allegata.")
            st.markdown(f"**Tipo di ricerca:** {_PR_TIPI_RICERCA.get(p.get('tipo_ricerca'), p.get('tipo_ricerca'))}  \n**Mezzo:** {p.get('mezzo_tipo', '')}  \n**Modello:** {(p.get('marca', '') + ' ' + p.get('modello', '')).strip().title() or '— non indicato —'}"
                        + (f" ({p['anno']})" if p.get("anno") else "") + f"  \n**Inviata da:** {p.get('utente_nome', '')}" + (f"  \n**Nota dell'utente:** {p['nota']}" if p.get("nota") else ""))
            k = f"prad_{p['id']}"
            nome = st.text_input("Nome della spia", value=sp["nome"], key=f"{k}_n")
            c1, c2 = st.columns(2, gap="small")
            col = c1.selectbox("Colore", ["rosso", "giallo", "verde", "blu", "bianco"], index=["rosso", "giallo", "verde", "blu", "bianco"].index(sp["colore"]), key=f"{k}_c")
            urg = c2.selectbox("Urgenza", ["critica", "alta", "media", "informazione"], index=["critica", "alta", "media", "informazione"].index(sp["urgenza"]) if sp["urgenza"] in ("critica", "alta", "media", "informazione") else 2, key=f"{k}_u")
            sig = st.text_area("Significato", value=sp["significato"], key=f"{k}_s", height=80)
            azi = st.text_area("Cosa fare (un passo per riga)", value="\n".join(sp["azioni"]), key=f"{k}_a", height=90)
            asp = st.text_input("Aspetto del simbolo", value=sp.get("aspetto", ""), key=f"{k}_p")
            d1, d2, d3 = st.columns([3, 3, 3], gap="small")
            tipo = d1.text_input("Mezzo", value=p.get("mezzo_tipo", ""), key=f"{k}_t")
            marca = d2.text_input("Marca (vuoto = vale per tutti)", value=p.get("marca", ""), key=f"{k}_m")
            modello = d3.text_input("Modello (vuoto = tutti)", value=p.get("modello", ""), key=f"{k}_o")
            motivo = st.text_input("Motivo del rifiuto (facoltativo, lo vede l'utente)", key=f"{k}_mot")
            b1, b2 = st.columns(2, gap="small")
            if b1.button("✅ Verifica e inserisci nella base", key=f"{k}_ok", type="primary", width="stretch"):
                ok, m = pr_decidi(p["id"], "approva", {"nome": nome, "colore": col, "urgenza": urg, "significato": sig, "azioni": [x for x in azi.splitlines() if x.strip()], "cause": sp.get("cause", []), "aspetto": asp, "simbolo_iso": sp.get("simbolo_iso", "")},
                                  {"tipo": tipo, "marca": marca, "modello": modello, "anno": p.get("anno", "")})
                st.session_state["messaggio"] = m
                st.rerun()
            if b2.button("🗑️ Rifiuta", key=f"{k}_no", width="stretch"):
                ok, m = pr_decidi(p["id"], "rifiuta", motivo=motivo)
                st.session_state["messaggio"] = m
                st.rerun()
    decise = [p for p in prop if p.get("stato") != "in attesa"][-8:]
    if decise:
        with st.expander(f"🗂️ Ultime decisioni ({len(decise)})"):
            for p in reversed(decise):
                st.markdown(f"{'✅' if p['stato'] == 'approvata' else '❌'} **{p['spia']['nome']}** · {p.get('mezzo_tipo', '')} · da {p.get('utente_nome', '')} · {p.get('decisa', '')}" + (f" — _{p['motivo']}_" if p.get("motivo") else ""))
