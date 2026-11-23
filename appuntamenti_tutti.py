# -*- coding: utf-8 -*-
"""📅 Appuntamenti e 📞 Numeri utili «che si parlano» con il resto dell'app.

1) Nella finestra 📅 Appuntamenti di una sezione compaiono ANCHE gli appuntamenti scritti altrove per la stessa persona
   (Salute: visite, controlli, cartelle di cura come il dentista); in Utilità c'è il riepilogo di TUTTI gli appuntamenti dell'app.
   Si leggono dalle schede originali (le stesse fonti dello Scadenziario): niente copie, niente doppioni.
2) Nei 📞 Numeri utili di Salute entra da solo lo studio di ogni cartella di cura (nome, medico, telefoni, email, indirizzo).
   Una volta inserito è un numero normale: lo puoi modificare o eliminare (se lo elimini non torna più)."""
import datetime as _at_dt
import re as _at_re

import streamlit as st

AT_SEZ_ICONE = {"salute": "🩺", "casa": "🏠", "auto": "🚗", "animali": "🐾", "lavoro": "💼", "documenti": "🪪", "utilita": "🧰", "chat": "💬",
                "scadenziario": "🗓️", "dispensa": "🥫"}


# =====================================================================================================================
# logica (senza Streamlit)
# =====================================================================================================================
def at_e_appuntamento(v):
    """Una voce dello Scadenziario è un appuntamento? (visite, incontri di lavoro, agenda animali, appuntamenti delle sezioni)"""
    k = str(v.get("chiave") or "")
    return v.get("categoria") in ("visite", "lavoro") or k.startswith("app:") or ":agenda:" in k


def at_filtra(voci, sez0, sez_vista, principale, oggi_):
    """Gli appuntamenti da mostrare in più nella finestra di «sez0», per la persona di «sez_vista» («salute» o «salute@p1»).
    In Utilità: tutti. Esclusi quelli già nella lista della finestra (app:{sez_vista}:…), i fatti e i passati."""
    base = str(sez0).split("@")[0]
    pid = str(sez_vista).split("@", 1)[1] if "@" in str(sez_vista) else principale
    out = []
    for v in voci or []:
        if not v or not at_e_appuntamento(v):
            continue
        if v.get("stato") in ("Completata", "Annullata") or v.get("solo_storico") or v.get("personale"):
            continue
        if not v.get("data") or v["data"] < oggi_:
            continue
        if str(v.get("chiave", "")).startswith(f"app:{sez_vista}:"):
            continue
        if base != "utilita":
            if v.get("sezione") != base:
                continue
            if base in ("salute", "documenti", "casa") and (v.get("profilo") or principale) != pid:
                continue
        out.append(v)
    return sorted(out, key=lambda v: (v["data"], v.get("ora") or "99:99", v.get("titolo") or ""))


def at_gruppo(dd, oggi_):
    if dd == oggi_:
        return "Oggi"
    if dd == oggi_ + _at_dt.timedelta(days=1):
        return "Domani"
    if dd <= oggi_ + _at_dt.timedelta(days=7):
        return "Nei prossimi 7 giorni"
    if dd <= oggi_ + _at_dt.timedelta(days=31):
        return "Entro un mese"
    return "Più avanti"


AT_TIPI = {"salute": ("🩺", "Salute"), "auto": ("🚗", "Auto"), "lavoro": ("💼", "Lavoro"), "casa": ("🏠", "Casa"), "animali": ("🐾", "Animali"),
           "documenti": ("🪪", "Documenti"), "utilita": ("🧰", "Altro (resta in Utilità)")}
AT_PRIORITA = {"Alta": ("🔴", 0), "Media": ("🟡", 1), "Bassa": ("🟢", 2)}


def at_tipo(v):
    """La tipologia di un appuntamento = la sezione a cui appartiene."""
    s = str(v.get("sezione") or "utilita")
    return s if s in AT_TIPI else "utilita"


def at_priorita(v):
    return v.get("priorita") if v.get("priorita") in AT_PRIORITA else "Media"


def at_ordina(voci, modo="data"):
    """«data»: prima i più vicini. «priorita»: prima le Alte (e tra loro i più vicini)."""
    chiave_data = lambda v: (v["data"], v.get("ora") or "99:99", v.get("titolo") or "")
    if modo == "priorita":
        return sorted(voci, key=lambda v: (AT_PRIORITA[at_priorita(v)][1],) + chiave_data(v))
    return sorted(voci, key=chiave_data)


def at_dove_va(tipo, pid, principale):
    """Dove si salva un appuntamento scritto da Utilità: nella sezione del suo tipo (e della persona, dove ci sono le persone)."""
    tipo = tipo if tipo in AT_TIPI else "utilita"
    if tipo in ("salute", "documenti", "casa") and pid and pid != principale:
        return f"{tipo}@{pid}"
    return tipo


def _at_cifre(n):
    return "".join(c for c in str(n or "") if c.isdigit() or c == "+")


def at_dividi_telefoni(telefoni):
    """(fisso, cellulare): i numeri italiani che cominciano per 3 sono cellulari."""
    fisso, cell = "", ""
    for t in telefoni or []:
        c = _at_cifre(t).lstrip("+")
        if c.startswith("0039"):
            c = c[4:]
        elif c.startswith("39") and len(c) > 10:
            c = c[2:]
        if not c:
            continue
        if c.startswith("3") and not cell:
            cell = str(t).strip()
        elif not fisso:
            fisso = str(t).strip()
        elif not cell:
            cell = str(t).strip()
    return fisso, cell


def at_mestiere(tipo):
    t = str(tipo or "").lower()
    for chiave, m in (("dent", "Dentista"), ("fisio", "Fisioterapista"), ("ricover", "Ospedale / CUP"), ("intervent", "Ospedale / CUP")):
        if chiave in t:
            return m
    return "Specialista"


def at_voce_da_percorso(pc, oggi_=None):
    """Il numero utile dello studio di una cartella di cura (None se non c'è niente di utile da salvare)."""
    s = pc.get("struttura") or {}
    nome = str(s.get("nome") or "").strip()
    fisso, cell = at_dividi_telefoni(s.get("telefoni"))
    if not nome and not (fisso or cell or s.get("email")):
        return None
    note = [f"Inserito da solo dalla cartella di cura «{pc.get('titolo') or ''}»."]
    if s.get("partita_iva"):
        note.append("P. IVA " + str(s["partita_iva"]))
    return {"id": "pc_" + str(pc.get("id")), "nome": nome or (s.get("medico") or "Studio"), "referente": str(s.get("medico") or ""),
            "mestiere": at_mestiere(pc.get("tipo")), "ambito": str(pc.get("titolo") or ""), "telefono": fisso, "cellulare": cell,
            "email": str(s.get("email") or ""), "sito": "", "indirizzo": str(s.get("indirizzo") or ""), "orari": "", "note": "\n".join(note),
            "da_percorso": pc.get("id"), "creato_il": (oggi_ or _at_dt.date.today()).isoformat()}


def _at_stesso(a, b):
    """Lo stesso studio già scritto a mano? (stesso telefono o stesso nome)"""
    na, nb = _at_re.sub(r"\W+", " ", str(a.get("nome") or "").lower()).strip(), _at_re.sub(r"\W+", " ", str(b.get("nome") or "").lower()).strip()
    if na and nb and (na == nb or (len(na) > 6 and na in nb) or (len(nb) > 6 and nb in na)):
        return True
    ta = {_at_cifre(x)[-9:] for x in (a.get("telefono"), a.get("cellulare")) if len(_at_cifre(x)) >= 6}
    tb = {_at_cifre(x)[-9:] for x in (b.get("telefono"), b.get("cellulare")) if len(_at_cifre(x)) >= 6}
    return bool(ta & tb)


def at_sincronizza_rubrica(d, oggi_=None):
    """Mette nei Numeri utili di Salute (della persona giusta) lo studio di ogni cartella di cura non ancora inserita.
    Modifica «d» e restituisce quante voci ha aggiunto. Ogni cartella si inserisce UNA volta sola (segno «in_rubrica»)."""
    f = d.get("farmacia") or {}
    profili = [p.get("id") for p in f.get("profili") or [] if isinstance(p, dict) and p.get("id")] or ["p0"]
    aggiunte = 0
    for pc in f.get("percorsi") or []:
        if not isinstance(pc, dict) or pc.get("in_rubrica"):
            continue
        voce = at_voce_da_percorso(pc, oggi_)
        if not voce:
            continue                                                   # niente nome/telefono ancora: riprova quando ci saranno
        pid = pc.get("profilo") or "p0"
        sez = "salute" if pid == profili[0] else f"salute@{pid}"
        lst = d.setdefault("numeri_utili", {}).setdefault(sez, [])
        if not any(x.get("id") == voce["id"] or _at_stesso(x, voce) for x in lst if isinstance(x, dict)):
            lst.append(voce)
            aggiunte += 1
        pc["in_rubrica"] = True
    return aggiunte


def at_da_sincronizzare(d):
    return any(isinstance(pc, dict) and not pc.get("in_rubrica") and at_voce_da_percorso(pc)
               for pc in ((d.get("farmacia") or {}).get("percorsi") or []))


# =====================================================================================================================
# Streamlit
# =====================================================================================================================
def _at_voci_altrove(sez0, sez_vista):
    try:
        d = sc_dati()
        adesso = _sz_adesso() if "_sz_adesso" in globals() else _at_dt.datetime.now()
        voci = sz_raccogli(d, adesso, solo_aperte=True)
        princ = sz_principale(d)
        return at_filtra(voci, sez0, sez_vista, princ, sc_oggi())
    except Exception:
        return []


def _at_sez_vista(sez0):
    """La chiave dei dati che la finestra sta mostrando (la persona scelta con le pillole «Di chi»)."""
    pr = sc_profili() if "sc_profili" in globals() else []
    if sez0 not in globals().get("SC_CON_PROFILI", ()) or len(pr) < 2:
        return sez0
    ids = [i for i, _n in pr]
    pid = st.session_state.get("sc_pf_" + sez0) or sc_profilo_corrente(sez0)
    return sez0 if pid == ids[0] or pid not in ids else f"{sez0}@{pid}"


def _at_apri(v):
    prima = st.session_state.get("_sc_dlg")
    try:
        _sz_apri_origine(v)
    finally:
        if st.session_state.get("_sc_dlg") is prima:
            st.session_state.pop("_sc_dlg", None)                     # chiude questa finestra per andare alla scheda
    st.rerun()


def _at_card(v, i, mostra_sezione, nomi=None):
    e = sc_esc
    righe = []
    quando = sc_data_scritta(v["data"]) if "sc_data_scritta" in globals() else v["data"].strftime("%d/%m/%Y")
    righe.append(f"🕒 <b>{e(quando)}</b>" + (f" alle <b>{e(v['ora'])}</b>" if v.get("ora") else ""))
    if v.get("descrizione"):
        righe.append(e(v["descrizione"]))
    if mostra_sezione:
        sez = v.get("sezione") or ""
        righe.append(f"{AT_SEZ_ICONE.get(sez, '📌')} da: {e(SZ_SEZIONI.get(sez, sez) if 'SZ_SEZIONI' in globals() else sez)}")
        chi = (nomi or {}).get(v.get("profilo"))
        if chi and f"({chi})" not in str(v.get("titolo")):
            righe.append("👤 " + e(chi))
    st.markdown(f"<div class='rbu-card' style='border-color:rgba(120,190,255,.7)'><b class='rbu-nome'>{e(v.get('titolo'))}</b>"
                f"<div class='rbu-righe'>" + "<br>".join(righe) + "</div></div>", unsafe_allow_html=True)
    if st.button("↗️ Apri la scheda", key=f"at_apri_{i}_{abs(hash(v['chiave'])) % 10**8}", width="stretch"):
        _at_apri(v)


def at_blocco(sez0):
    """Il blocco «anche altrove» (o, in Utilità, il riepilogo di tutto) sotto la lista della finestra."""
    sez_vista = _at_sez_vista(sez0)
    voci = _at_voci_altrove(sez0, sez_vista)
    tutti = str(sez0).split("@")[0] == "utilita"
    st.markdown(f"### {'🗓️ Tutti gli appuntamenti dell’app' if tutti else '🔗 Dalle altre schede (visite, cartelle di cura…)'} ({len(voci)})")
    st.caption("Da tutte le sezioni (Salute, cartelle di cura, Casa, Auto, Animali, Lavoro…). Tocca «Apri la scheda» per vederli o cambiarli."
               if tutti else "Appuntamenti della stessa persona scritti in altre parti di questa sezione (visite, controlli, cartelle di cura).")
    if not voci:
        st.caption("Nessuno in programma.")
        return
    oggi_ = sc_oggi()
    pr = sc_profili() if "sc_profili" in globals() else []
    nomi = dict(pr[1:]) if tutti else {}                                # in Utilità: di chi è (te stesso non si scrive)
    gruppo = None
    for i, v in enumerate(voci):
        g = at_gruppo(v["data"], oggi_)
        if g != gruppo:
            gruppo = g
            st.markdown(f"**{g}**")
        _at_card(v, i, tutti, nomi)


def _at_rec(d, chiave):
    """Dalla chiave «app:{sezione}:{id}» → (sezione, appuntamento originale)."""
    try:
        _, resto = chiave.split(":", 1)
        sez, aid = resto.rsplit(":", 1)
    except ValueError:
        return None, None
    return sez, next((a for a in (d.get("appuntamenti") or {}).get(sez, []) if isinstance(a, dict) and a.get("id") == aid), None)


def _at_riga_tipo(v, nomi):
    ico, nome = AT_TIPI[at_tipo(v)]
    nome = "Utilità" if at_tipo(v) == "utilita" else nome
    chi = nomi.get(v.get("profilo"))
    pr = at_priorita(v)
    return f"{ico} **{nome}**" + (f" · 👤 {chi}" if chi and f"({chi})" not in str(v.get("titolo")) else "") + f" · {AT_PRIORITA[pr][0]} priorità {pr.lower()}"


def _at_cambia_priorita(v, pr):
    def _fn(sz_):
        sz_.setdefault("stati", {}).setdefault(v["chiave"], {})["priorita"] = pr
    _sz_salva(_fn, "priorità di " + str(v.get("titolo") or ""))
    sc_rerun()


def at_utilita_corpo():
    """Utilità → 📅 Appuntamenti: TUTTI gli appuntamenti dell'app, per tipologia e per data o priorità.
    Un appuntamento nuovo scritto da qui va nella sezione del suo tipo (Salute, Auto, Lavoro…)."""
    st.markdown(RBU_CSS, unsafe_allow_html=True) if "RBU_CSS" in globals() else None
    d = sc_dati()
    oggi_ = sc_oggi()
    pr_ = sc_profili() if "sc_profili" in globals() else []
    ids = [i for i, _n in pr_] or ["p0"]
    nomi_tutti = dict(pr_)
    nomi = dict(pr_[1:])
    st.caption("Qui vedi TUTTI gli appuntamenti dell'app, da ogni sezione. Ognuno resta anche nella sua sezione (Salute in Salute, Auto in Auto…).")
    # ➕ nuovo: si sceglie il tipo e va nella sua sezione
    if st.button("➕ Aggiungi un appuntamento", key="at_nuovo", type="primary", width="stretch"):
        st.session_state["apn_mod"] = "__nuovo__"
        sc_rerun()
    if st.session_state.get("apn_mod") == "__nuovo__":
        with st.container(border=True, key="at_nuovo_box"):
            tipo = st.selectbox("Di che tipo è? (andrà anche nella sua sezione)", list(AT_TIPI), key="at_nuovo_tipo",
                                format_func=lambda t: " ".join(AT_TIPI[t]))
            pid = ids[0]
            if tipo in ("salute", "documenti", "casa") and len(ids) > 1:
                pid = st.radio("Per chi?", ids, horizontal=True, key="at_nuovo_chi", format_func=lambda i: "👤 " + str(nomi_tutti.get(i, "")))
            _apn_modulo(at_dove_va(tipo, pid, ids[0]), {})
    try:
        voci = sz_raccogli(d, _sz_adesso() if "_sz_adesso" in globals() else _at_dt.datetime.now(), solo_aperte=True)
        voci = at_filtra(voci, "utilita", "__tutte__", sz_principale(d), oggi_)
    except Exception:
        voci = []
    st.markdown(f"### 🗓️ Tutti gli appuntamenti ({len(voci)})")
    if not voci:
        st.info("Nessun appuntamento in programma. Tocca «Aggiungi un appuntamento».")
    else:
        presenti = [t for t in AT_TIPI if any(at_tipo(v) == t for v in voci)]
        conta = {t: sum(1 for v in voci if at_tipo(v) == t) for t in presenti}
        etich = lambda t: "Tutte" if t == "tutte" else f"{AT_TIPI[t][0]} {'Utilità' if t == 'utilita' else AT_TIPI[t][1]} ({conta[t]})"
        tipo_sel = st.pills("Tipologia", ["tutte"] + presenti, selection_mode="single", default="tutte", key="at_f_tipo", format_func=etich) or "tutte"
        modo = st.radio("Ordina per", ["data", "priorita"], horizontal=True, key="at_f_ordine",
                        format_func=lambda m: "📅 Data" if m == "data" else "⭐ Priorità")
        lista = at_ordina([v for v in voci if tipo_sel == "tutte" or at_tipo(v) == tipo_sel], modo)
        gruppo = None
        for i, v in enumerate(lista):
            g = at_gruppo(v["data"], oggi_) if modo == "data" else f"{AT_PRIORITA[at_priorita(v)][0]} Priorità {at_priorita(v).lower()}"
            if g != gruppo:
                gruppo = g
                st.markdown(f"#### {g}")
            st.markdown(_at_riga_tipo(v, nomi))
            if v["chiave"].startswith("app:"):
                sez, rec = _at_rec(d, v["chiave"])
                if rec:
                    _apn_card(sez, rec, False)                         # come nella sua sezione: Fatto, Modifica (anche priorità), Elimina, calendario
                    continue
            _at_card(v, i, False)
            with st.popover(f"⭐ Cambia priorità", width="stretch"):
                for pr in AT_PRIORITA:
                    if st.button(f"{AT_PRIORITA[pr][0]} {pr}", key=f"at_pr_{i}_{pr}_{abs(hash(v['chiave'])) % 10**8}", width="stretch",
                                 type="primary" if pr == at_priorita(v) else "secondary"):
                        _at_cambia_priorita(v, pr)
    # passati o fatti (scritti con il bottone 📅 nelle sezioni)
    vecchi = []
    for sez, lst in (d.get("appuntamenti") or {}).items():
        for a in lst or []:
            if isinstance(a, dict) and a.get("id") and (a.get("fatto") or (sc_data(a.get("data")) and sc_data(a.get("data")) < oggi_)):
                vecchi.append((sez, a))
    if vecchi:
        vecchi.sort(key=lambda x: str(x[1].get("data") or ""), reverse=True)
        with st.expander(f"🗂️ Passati o fatti ({len(vecchi)})"):
            for sez, a in vecchi[:40]:
                b = str(sez).split("@")[0]
                ico, nome = AT_TIPI.get(b, AT_TIPI["utilita"])
                st.caption(f"{ico} {'Utilità' if b == 'utilita' else nome}" + (f" · 👤 {nomi_tutti.get(sez.split('@', 1)[1], '')}" if "@" in sez else ""))
                _apn_card(sez, a, True)


def at_conta_altrove(sez):
    base = str(sez).split("@")[0]
    return len(_at_voci_altrove(base, sez))


# --- aggancio alla finestra 📅 Appuntamenti -------------------------------------------------------------------------
if "_apn_corpo" in globals() and "_at_apn_corpo_prima" not in globals():
    _at_apn_corpo_prima = _apn_corpo

    def _apn_corpo(sez0):                                              # noqa: F811
        if str(sez0).split("@")[0] == "utilita":
            try:
                at_utilita_corpo()
                return
            except Exception as _e:
                st.caption(f"(il riepilogo non si può mostrare: {type(_e).__name__})")
        _at_apn_corpo_prima(sez0)
        try:
            st.divider()
            at_blocco(sez0)
        except Exception as _e:
            st.caption(f"(gli appuntamenti delle altre schede non si possono mostrare: {type(_e).__name__})")

if "apn_prossimi" in globals() and "_at_apn_prossimi_prima" not in globals():
    _at_apn_prossimi_prima = apn_prossimi

    def apn_prossimi(sez):                                             # noqa: F811
        n = _at_apn_prossimi_prima(sez)
        try:
            n += at_conta_altrove(sez)
        except Exception:
            pass
        return n

# --- aggancio ai 📞 Numeri utili: lo studio delle cartelle di cura entra da solo ------------------------------------
if "_rbu_corpo" in globals() and "_at_rbu_corpo_prima" not in globals():
    _at_rbu_corpo_prima = _rbu_corpo

    def _rbu_corpo(sez0):                                              # noqa: F811
        try:
            if str(sez0).split("@")[0] == "salute" and at_da_sincronizzare(sc_dati()):
                sc_salva(lambda d: at_sincronizza_rubrica(d, sc_oggi()), "Numeri utili: studi delle cartelle di cura")
        except Exception:
            pass
        _at_rbu_corpo_prima(sez0)
