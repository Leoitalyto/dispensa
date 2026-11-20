# -*- coding: utf-8 -*-
"""VOCI A SCELTA LIBERA in tutti gli elenchi a tendina che hanno «Altro».

RICHIESTA (Leonardo, 20 novembre): «quello che hai fatto per Ecocert devi farlo in qualsiasi altro campo dell'app dove non c'è la possibilità di
inserire un nome a propria scelta».

COSA FA
• Negli elenchi a tendina con la voce «Altro» (tipi di documento, stanze, specie degli animali, tipi di sepoltura, ruoli dei medici, categorie del
  condominio, modi di pagamento, relazioni nei compleanni…) compare la casella «✍️ Non è nell'elenco? Scrivi il nome che vuoi».
  Fuori da un modulo compare quando scegli «Altro»; dentro un modulo (dove la pagina non si ridisegna finché non salvi) c'è sempre, sotto l'elenco.
• Se scegli «Altro» e scrivi un nome, viene salvato QUEL nome (non «Altro»).
• Il nome scritto si ricorda: da quel momento compare nell'elenco (prima di «Altro»), così la volta dopo lo scegli senza riscriverlo e, quando
  modifichi una scheda, l'elenco mostra il nome giusto. I nomi si ricordano nei dati di chi li ha scritti (o della dispensa di famiglia).
• Gli elenchi che decidono come funziona l'app (ogni quanto scadono le rate, quale intelligenza artificiale, il mezzo obbligatorio della diagnosi…)
  non si toccano. Quelli che avevano già una casella loro (INPS, «Come si paga», «Dove lo metti?») restano come sono.
Caricato prima di parte3.py (che disegna le pagine). Se manca, gli elenchi restano come prima."""
import functools as _vl_ft

import streamlit as st

# nome dell'elenco (variabile del programma) → è uno di quelli dove si può scrivere un nome proprio
VL_ELENCHI = ("CP_RELAZIONI", "TIPI_PRESC", "CA_STANZE", "CA_TIPI_MANUTENZIONE", "CA_ARGOMENTI", "CA_TIPI", "SE_TIPI", "_AU_TIPI", "_SP_RUOLI_MEDICO", "_SP_TIPI_DOC",
              "_SP_EVENTI_DENTI", "AMM_CATEGORIE", "SP_TIPI", "RBU_TIPI_PAG", "AN_SPECIE", "_CA_MODI_PAGAMENTO", "AMM_CATEGORIE_PROF")
VL_ALTRO = ("Altro", "Altra", "Altro mezzo", "Altri")
VL_SALTA = ("Che documento INPS è", "Come si paga", "Dove lo metti", "Per quale mezzo", "Ogni quanto", "Intelligenza artificiale", "Sesso")


def _vl_dati():
    try:
        return carica_dati(crea_archivio(), st.session_state["percorso"]).get("voci_libere") or {}
    except Exception:
        return {}


def _vl_altro(lista):
    return next((x for x in lista if isinstance(x, str) and x in VL_ALTRO), None)


def _vl_prepara():
    """A ogni ridisegnata: i nomi scritti dalla persona entrano negli elenchi (prima di «Altro»)."""
    if not (st.session_state.get("sess") or {}).get("uid"):
        return
    # gli elenchi «di base» (senza i nomi scritti dalle persone) restano in un posto fisso: l'avvolgimento li riconosce anche dentro le finestre,
    # che si ridisegnano con gli elenchi della volta in cui sono state aperte
    st._vl_basi = {n_: [x for x in globals()[n_] if isinstance(x, str) and x] for n_ in VL_ELENCHI if isinstance(globals().get(n_), list) and globals()[n_]}
    salvate = {k_: list(v_) for k_, v_ in _vl_dati().items()}
    for nome_, valore_ in st.session_state.get("_vl_da_salvare") or []:
        salvate.setdefault(nome_, []).append(valore_)
    for nome in VL_ELENCHI:
        lista = globals().get(nome)
        if not isinstance(lista, list):
            continue
        altro = _vl_altro(lista)
        for v in salvate.get(nome) or []:
            if isinstance(v, str) and v and v not in lista:
                lista.insert(lista.index(altro) if altro in lista else len(lista), v)


def _vl_ricorda(nome, valore, opzioni=None):
    """Il nome scritto entra subito nell'elenco; si SALVA alla ridisegnata completa successiva (salvare mentre si scrive chiuderebbe le finestre aperte)."""
    if not nome or not valore or (st.session_state.get("sess") or {}).get("uid") in (None, "prova"):
        return
    if isinstance(opzioni, list) and valore not in opzioni:
        altro = _vl_altro(opzioni)
        opzioni.insert(opzioni.index(altro) if altro in opzioni else len(opzioni), valore)
    coda = st.session_state.setdefault("_vl_da_salvare", [])
    if [nome, valore] not in coda:
        coda.append([nome, valore])


def _vl_salva_coda():
    """All'inizio di una ridisegnata completa: salva i nomi nuovi scritti prima (una sola scrittura)."""
    gia = _vl_dati()
    coda = [c_ for c_ in (st.session_state.get("_vl_da_salvare") or []) if c_[1] not in (gia.get(c_[0]) or [])]
    if not coda:
        st.session_state["_vl_da_salvare"] = []
        return
    if st.session_state.get("_vl_salvo"):
        return
    st.session_state["_vl_salvo"] = True
    try:
        def _m(d):
            vl = d.setdefault("voci_libere", {})
            for nome, valore in coda:
                vv = vl.setdefault(nome, [])
                if valore not in vv:
                    vv.append(valore)
                    del vv[:-60]
        salva_file(st.session_state["percorso"], _m, "Nuove voci negli elenchi")
        st.session_state["_vl_da_salvare"] = []
    except Exception:
        pass
    finally:
        st.session_state["_vl_salvo"] = False


def _vl_quale(opzioni):
    """Quale elenco del programma è: tutte le sue voci di base ci sono (anche se è una copia, con una voce vuota davanti o con nomi aggiunti)."""
    try:
        op = set(x for x in opzioni if isinstance(x, str))
    except Exception:
        return None
    for nome, base in (getattr(st, "_vl_basi", None) or {}).items():
        if base and all(x in op for x in base):
            return nome
    return None


def _vl_nel_modulo(dg):
    try:
        from streamlit.elements.lib.form_utils import current_form_id
        return bool(current_form_id(dg))
    except Exception:
        return False


_VL_DENTRO = {"n": 0}


def _vl_dopo(dg, label, options, r, k):
    """Dopo che l'elenco è disegnato: se serve, la casella per scrivere il nome. Ritorna il valore da dare al programma."""
    lab = str(label or "")
    if any(lab.startswith(s) or lab.lstrip("📂🚚 ").startswith(s) for s in VL_SALTA):
        return r
    nome = _vl_quale(options)
    altro = _vl_altro(list(options)) if nome else None
    if not altro:
        return r
    nel_modulo = _vl_nel_modulo(dg)
    if r != altro and not nel_modulo:
        return r
    base = str(k.get("key") or ("vl_" + str(abs(hash((lab, nome))))))
    scritto = dg.text_input("✍️ Non è nell'elenco? Scrivi il nome che vuoi" + (f" (vale se scegli «{altro}»)" if nel_modulo else ""),
                            key=base + "_vl", max_chars=80, placeholder="Scrivi qui il nome esatto…")
    scritto = (scritto or "").strip()
    if r == altro and scritto:
        _vl_ricorda(nome, scritto, options)
        return scritto
    return r


def _vl_avvolgi(orig, di_classe):
    @_vl_ft.wraps(orig)
    def selectbox(*a, **k):
        if _VL_DENTRO["n"]:                                         # già dentro un altro avvolgimento di questo file: non raddoppiare la casella
            return orig(*a, **k)
        _VL_DENTRO["n"] += 1
        try:
            r = orig(*a, **k)
        finally:
            _VL_DENTRO["n"] -= 1
        try:
            if di_classe:
                dg, resto = a[0], list(a[1:])
            else:
                dg, resto = st._main, list(a)
            label = resto[0] if resto else k.get("label")
            options = resto[1] if len(resto) > 1 else k.get("options", ())
            return _vl_dopo(dg, label, options, r, k)
        except Exception:
            return r
    selectbox._vl = True
    return selectbox


def _vl_installa():
    from streamlit.delta_generator import DeltaGenerator as _DG
    m = getattr(_DG, "selectbox", None)
    if m is not None and not getattr(m, "_vl", False):
        _DG.selectbox = _vl_avvolgi(m, True)
    g = getattr(st, "selectbox", None)
    if g is not None and not getattr(g, "_vl", False):
        if getattr(g, "__self__", None) is getattr(st, "_main", object()):
            st.selectbox = st._main.selectbox
        else:
            st.selectbox = _vl_avvolgi(g, False)                     # già avvolta da altri (es. la persona scelta in Salute): la avvolgo tenendo la sua


try:
    _vl_installa()
except Exception:
    pass
try:
    _vl_prepara()
except Exception:
    pass
try:
    _vl_salva_coda()                                                 # solo nelle ridisegnate complete (non dentro una finestra aperta)
except Exception:
    pass
