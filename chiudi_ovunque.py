# -*- coding: utf-8 -*-
"""REGOLA UNICA DELL'APP: ogni volta che dentro una scheda (linguetta) o una finestra c'è un pulsante che conferma (💾 Salva, ✅ Sposta, 📨 Invia, ➕ Aggiungi…),
accanto compare SEMPRE «✖ Chiudi», per il ripensamento. Lo fa questo modulo da solo, per TUTTI i moduli dell'app (anche quelli futuri): nessuno deve ricordarsi di aggiungerlo.
Cosa fa «✖ Chiudi» (sceglie da solo, in base a come si è aperto il modulo):
 · modulo che si è aperto DENTRO una scheda già aperta (es. «Modifica» di un documento): nasconde solo quel modulo, la scheda e l'elenco restano come sono;
 · modulo che sta dentro una scheda che hai aperto tu: chiude la scheda;
 · modulo dentro una finestra: chiude la finestra.
- Dove c'è già un pulsante per chiudere (Annulla, No, Chiudi…) o il pulsante sta già in una riga con un altro, non aggiunge niente.
- Per escluderlo di proposito: passare _chiudi=False al pulsante.
Caricato da app_dispensa.py. Nomi con prefisso «co_» per non scontrarsi con gli altri moduli."""
import re
import json
import hashlib
import threading
import functools
import streamlit as st
from streamlit.delta_generator import DeltaGenerator as _DG_co
from streamlit.delta_generator_singletons import context_dg_stack as _pila_co

_CO_LOC = threading.local()
_CO_E_CHIUDI = re.compile(r"^\W*(chiudi|annulla|indietro|no\b|lascia|torna|esci|✖|✕)", re.I)
# per i pulsanti NON dei moduli (st.button): solo quelli che salvano/confermano; gli «Elimina», «Aggiungi», «Invia»… della pagina sono pulsanti che aprono, non che confermano
_CO_E_CONFERMA = re.compile(r"^\W*(salva|conferma|registra|importa|applica|sposta)", re.I)
_CO_TESTO = "✖ Chiudi"
_CO_ESCLUSI = re.compile(r"^\W*(entra|cerca|chiedi|valuta|accedi)", re.I)


def co_css():
    st.markdown("""<style>
div[class*="st-key-vmduo_"]{flex-wrap:nowrap !important;gap:8px !important;width:100% !important}
div[class*="st-key-vmduo_"] > div{flex:1 1 0 !important;min-width:0 !important;width:auto !important}
div[class*="st-key-vmduo_"] [data-testid="stElementContainer"]{width:100% !important}
div[class*="st-key-vmduo_"] button{width:100% !important;min-width:0 !important}
div[class*="st-key-vmduo_chiudi_"] > div:last-child{flex:0 0 36% !important}
div[class*="st-key-vmnasc_"]{display:none !important}
</style>""", unsafe_allow_html=True)


def _co_ss():
    try:
        return st.session_state
    except Exception:
        return {}


def co_inizio_run():
    """Ad ogni ridisegnata: ricorda cosa si vedeva nella precedente (serve a capire se un modulo si è appena aperto DENTRO una scheda già aperta)."""
    ss = _co_ss()
    try:
        ss["_co_lg_prev"] = list(ss.get("_co_lg_cur") or [])
        ss["_co_lg_cur"] = []
        ss["_co_vis_prev"] = list(ss.get("_co_vis_cur") or [])
        ss["_co_vis_cur"] = []
        ss["_co_n"] = 0
        marcate = ss.pop("_co_js", None)
        if marcate:
            try:
                st.sidebar.html("<script>(function(){var L=" + json.dumps(marcate) + ";var t=0;var iv=setInterval(function(){var fatto=false;"
                                "document.querySelectorAll('[data-testid=\"stExpander\"] details').forEach(function(d){var s=d.querySelector('summary');if(!s||!d.open)return;"
                                "if(L.some(function(x){return s.innerText.indexOf(x)>=0;})){s.click();fatto=true;}});"
                                "if(fatto||++t>25)clearInterval(iv);},120);})();</script>", unsafe_allow_javascript=True)
            except Exception:
                pass
    except Exception:
        pass


def co_contesto():
    """Dove siamo: dentro una finestra (dialog) e/o dentro quali linguette. Solo ciò che sta DENTRO l'ultima finestra aperta."""
    try:
        pila = list(_pila_co.get())
    except Exception:
        return None
    ultimo_dlg = -1
    for i, d in enumerate(pila):
        if getattr(d, "_block_type", None) == "dialog":
            ultimo_dlg = i
    dentro = pila[ultimo_dlg + 1:] if ultimo_dlg >= 0 else pila
    linguette = [d for d in dentro if isinstance(d.__dict__.get("_vm_linguetta"), str)]
    modulo = next((d.__dict__["_vm_form_key"] for d in reversed(dentro) if isinstance(d.__dict__.get("_vm_form_key"), str)), None)
    return {"finestra": ultimo_dlg >= 0, "linguette": [d.__dict__["_vm_linguetta"] for d in linguette], "modulo": modulo}


def co_prossimo():
    """Numero progressivo per i riquadri (si riparte da 1 a ogni ridisegno della pagina, per ogni persona collegata)."""
    try:
        ss = st.session_state
        ss["_co_n"] = int(ss.get("_co_n", 0)) + 1
        return ss["_co_n"]
    except Exception:
        return id(object())


def co_chiave(self, label, kw):
    """Chiave stabile (uguale a ogni ridisegno, anche della sola finestra) per il «Chiudi» che sta accanto a un pulsante."""
    try:
        from streamlit.elements.lib.form_utils import current_form_id
        modulo = current_form_id(self._active_dg)
    except Exception:
        modulo = ""
    base = f"{modulo}|{kw.get('key') or ''}|{label}"
    return "vmco_" + hashlib.md5(base.encode("utf-8")).hexdigest()[:14]


def co_e_chiudi(label):
    return bool(_CO_E_CHIUDI.match(str(label or "")))


def co_modo(ctx, ident, e_modulo):
    """Come si chiude questo modulo: «nascondi» (si è aperto dentro una scheda già aperta), «scheda» (sta in una scheda aperta da te) o «finestra»."""
    ss = _co_ss()
    try:
        visti = set(ss.get("_co_vis_prev") or []) | set(ss.get("_co_vis_cur") or [])
        modi = ss.setdefault("_co_modi", {})
        if ident in visti and ident in modi:
            modo = modi[ident]
        else:
            prima = set(ss.get("_co_lg_prev") or [])
            if not ctx["linguette"] and not ctx["finestra"]:
                modo = "nascondi"
            elif ctx["linguette"]:
                modo = "nascondi" if (e_modulo and ctx.get("modulo") and prima and set(ctx["linguette"]) <= prima) else "scheda"
            else:
                modo = "finestra"
            modi[ident] = modo
        ss["_co_vis_cur"] = list(ss.get("_co_vis_cur") or []) + [ident]
        return modo
    except Exception:
        return "scheda" if ctx["linguette"] else "finestra"


def co_chiudi(ctx, modo):
    """Chiude l'ambiente giusto e ridisegna subito la pagina."""
    ss = _co_ss()
    try:
        adesso = int(ss.get("_vm_run", 0))
        if modo == "nascondi" and ctx.get("modulo"):
            chiusi = dict(ss.get("_co_chiusi") or {})
            chiusi[ctx["modulo"]] = adesso + 1                    # fino a che non lo riapri toccando di nuovo «Modifica» (o simili)
            ss["_co_chiusi"] = chiusi
        elif ctx["linguette"] and modo == "scheda":
            elenco = list(ctx["linguette"])
            ultimo = elenco.pop()
            ss["_linguette_vive"] = elenco
            ss["_co_js"] = [ultimo.replace("\n", " ").strip()]            # se l'hai aperta tu col dito, la chiude anche sullo schermo
        else:
            salta = dict(ss.get("_dlg_salta") or {})
            salta[ss.get("_co_dlg") or "*"] = adesso + 1          # alla prossima ridisegnata, quella finestra non si riapre
            ss["_dlg_salta"] = salta
    except Exception:
        pass
    st.rerun()


def _co_avvolgi(originale, solo_conferme):
    @functools.wraps(originale)
    def _nuovo(self, *a, **kw):
        voglio = kw.pop("_chiudi", True)
        if getattr(_CO_LOC, "dentro", False) or self is not getattr(st, "_main", None):
            return originale(self, *a, **kw)
        label = a[0] if a else kw.get("label", "")
        ctx = co_contesto()
        if ctx:
            try:
                ss = st.session_state
                ss["_co_lg_cur"] = list(ss.get("_co_lg_cur") or []) + ctx["linguette"]
            except Exception:
                pass
        if not voglio or not ctx or co_e_chiudi(label) or (solo_conferme and not _CO_E_CONFERMA.match(str(label or ""))):
            return originale(self, *a, **kw)
        if not ctx["finestra"] and not ctx["linguette"]:           # modulo sulla pagina (non in una scheda o finestra): solo i moduli veri, non accesso/ricerca/chat
            if solo_conferme or not ctx.get("modulo") or _CO_ESCLUSI.match(str(label or "")):
                return originale(self, *a, **kw)
        ident = f"{ctx.get('modulo') or ''}|{kw.get('key') or ''}|{label}"
        modo = co_modo(ctx, ident, not solo_conferme)
        _CO_LOC.dentro = True
        try:
            co_css()
            with self.container(horizontal=True, gap="small", key=f"vmduo_chiudi_{co_prossimo()}"):
                esito = originale(self, *a, **kw)
                chiuso = originale(self, _CO_TESTO, key=co_chiave(self, label, kw), width="stretch")
        finally:
            _CO_LOC.dentro = False
        if chiuso:
            co_chiudi(ctx, modo)
        return esito
    _nuovo._vm_chiudi = True
    return _nuovo


def _co_avvolgi_form(originale):
    @functools.wraps(originale)
    def _nuovo(self, key, *a, **kw):
        ss = _co_ss()
        nascosto = False
        try:
            adesso = int(ss.get("_vm_run", 0))
            chiusi = dict(ss.get("_co_chiusi") or {})
            ultimo = chiusi.get(key)
            nascosto = ultimo is not None and ultimo >= adesso - 2
            if ultimo is not None:
                if nascosto:
                    chiusi[key] = adesso
                else:
                    chiusi.pop(key, None)
                ss["_co_chiusi"] = chiusi
        except Exception:
            nascosto = False
        if nascosto:
            co_css()
            with self.container(key="vmnasc_" + hashlib.md5(str(key).encode("utf-8")).hexdigest()[:12]):
                f = originale(st._main, key, *a, **kw)
        else:
            f = originale(self, key, *a, **kw)
        try:
            f._vm_form_key = key
        except Exception:
            pass
        return f
    _nuovo._vm_chiudi = True
    return _nuovo


if not getattr(_DG_co.form_submit_button, "_vm_chiudi", False):
    try:
        _DG_co.form_submit_button = _co_avvolgi(_DG_co.form_submit_button, False)
        _DG_co.button = _co_avvolgi(_DG_co.button, True)
        _DG_co.form = _co_avvolgi_form(_DG_co.form)
        for _n_co in ("form_submit_button", "button", "form"):
            if hasattr(st, _n_co):
                setattr(st, _n_co, getattr(st._main, _n_co))
    except Exception:
        pass

# Le finestre (dialog): se dentro si tocca «✖ Chiudi» la finestra non si riapre da sola alla ridisegnata che segue.
if not getattr(st.dialog, "_vm_chiudi", False):
    _dialog_originale = st.dialog

    def _co_dialog(titolo=None, *a, **kw):
        if callable(titolo) or titolo is None:
            return _dialog_originale(titolo, *a, **kw)
        decoratore = _dialog_originale(titolo, *a, **kw)

        def _decora(fn):
            chiave = f"{titolo}|{getattr(fn, '__qualname__', '')}"

            @functools.wraps(fn)
            def _corpo(*x, **y):
                prima = st.session_state.get("_co_dlg")
                st.session_state["_co_dlg"] = chiave
                try:
                    return fn(*x, **y)
                finally:
                    st.session_state["_co_dlg"] = prima
            aperta = decoratore(_corpo)

            @functools.wraps(fn)
            def _apri(*x, **y):
                try:
                    salta = dict(st.session_state.get("_dlg_salta") or {})
                    adesso = st.session_state.get("_vm_run", 0)
                    if salta.get(chiave) == adesso or salta.get("*") == adesso:
                        return None
                except Exception:
                    pass
                return aperta(*x, **y)
            return _apri
        return _decora
    _co_dialog._vm_chiudi = True
    st.dialog = _co_dialog

co_inizio_run()
