# -*- coding: utf-8 -*-
"""🌐 TRADUZIONE AUTOMATICA DI TUTTE LE PAGINE (quando la lingua scelta non è l'italiano).

Molte pagine sono scritte solo in italiano. Questo file fa passare OGNI testo che l'app mostra (titoli, frasi, pulsanti, campi, schede, finestre, schede HTML)
per una traduzione:
  1. prima il dizionario dell'app (TRADUZIONI, quello di t());
  2. poi le traduzioni già fatte e salvate (archivio «traduzioni/<lingua>.json», uguali per tutti);
  3. se manca, la frase si mette in coda e un servizio IA gratuito (ia_lettura.py: Mistral, Gemini, Groq…) la traduce in sottofondo, a gruppi.
     Appena pronte, la pagina si ridisegna da sola (una volta) con le frasi tradotte. Ogni frase si traduce una volta sola, poi resta per sempre.
• Si traducono SOLO i testi scritti dal programma (riconosciuti dall'elenco delle frasi del codice): i dati delle persone (nomi, note, prodotti) restano come sono.
• I valori scelti nei menu non cambiano (si traduce solo come si vedono), quindi l'app funziona uguale in tutte le lingue.
• Senza chiavi IA tutto resta come prima (italiano dove manca la traduzione).
Caricato PER PRIMO (prima di chiudi_ovunque.py: così gli altri avvolgimenti vedono le etichette italiane e la traduzione si fa per ultima). Prefisso: ta_"""
import ast as _ta_ast
import glob as _ta_glob
import json as _ta_json
import os as _ta_os
import re as _ta_re
import threading as _ta_thr
import time as _ta_time

import streamlit as st

TA_NOMI_LINGUE = {"en": "English", "es": "Spanish (Spain)", "fr": "French", "de": "German", "pt": "Portuguese", "ro": "Romanian", "ar": "Arabic"}
TA_ORDINE = ["mistral", "gemini", "groq", "cloudflare", "nvidia", "openrouter", "deepseek", "cohere"]       # più veloci per tanti testi prima
TA_GRUPPO = 40
_TA_LOC = _ta_thr.local()


# ---------------------------------------------------------------------------------------------------------------------
# l'elenco delle frasi del programma (dal codice): serve a non tradurre i dati delle persone
# ---------------------------------------------------------------------------------------------------------------------
def _ta_norm(s):
    return _ta_re.sub(r"\s+", " ", str(s or "")).strip()


@st.cache_resource
def _ta_catalogo():
    esatte, coppie = set(), set()
    cart = _ta_os.path.dirname(_ta_os.path.abspath(globals().get("__file__") or "")) if globals().get("__file__") else globals().get("_cartella", ".")
    cart = globals().get("_cartella") or cart
    for f in _ta_glob.glob(_ta_os.path.join(cart, "*.py")):
        b = _ta_os.path.basename(f)
        if b.startswith(("prova", "lingue", "guida_", "test")) or b.endswith("_img.py") or "img_lingue" in b:
            continue
        try:
            albero = _ta_ast.parse(open(f, encoding="utf-8").read())
        except Exception:
            continue
        for n in _ta_ast.walk(albero):
            if isinstance(n, _ta_ast.Constant) and isinstance(n.value, str):
                pezzi = [n.value]
            else:
                continue
            for p in pezzi:
                if len(p) > 600 or "{" in p and ";" in p or "<style" in p or "function(" in p:
                    continue
                for seg in _ta_re.split(r"<[^>]+>", p):
                    s = _ta_norm(seg)
                    if len(_ta_re.findall(r"[A-Za-zÀ-ÿ]", s)) >= 2:
                        esatte.add(s.lower())
                        parole = _ta_re.findall(r"[a-zà-ÿ']{3,}", s.lower())
                        for a, c in zip(parole, parole[1:]):
                            coppie.add(a + " " + c)
    return esatte, coppie


def _ta_del_programma(s):
    n = _ta_norm(s).lower()
    if not n:
        return False
    esatte, coppie = _ta_catalogo()
    if n in esatte:
        return True
    parole = _ta_re.findall(r"[a-zà-ÿ']{3,}", n)
    return any((a + " " + c) in coppie for a, c in zip(parole, parole[1:]))


# ---------------------------------------------------------------------------------------------------------------------
# memoria delle traduzioni (una per tutto il server) e coda
# ---------------------------------------------------------------------------------------------------------------------
@st.cache_resource
def _ta_memoria():
    return {"tr": {}, "caricate": set(), "coda": {}, "versione": 0, "lavora": False, "pausa": 0.0, "dinamiche": {}}, _ta_thr.Lock()


_TA_M, _TA_B = _ta_memoria()


def _ta_carica(lingua_):
    with _TA_B:
        if lingua_ in _TA_M["caricate"]:
            return
        _TA_M["caricate"].add(lingua_)
    try:
        d = crea_archivio().leggi(f"traduzioni/{lingua_}.json") or {}
    except Exception:
        d = {}
    with _TA_B:
        _TA_M["tr"].setdefault(lingua_, {}).update({k: v for k, v in (d.get("t") or {}).items() if isinstance(v, str)})


def _ta_lingua():
    try:
        return lingua()
    except Exception:
        return st.session_state.get("lang", "it")


def ta_frase(s):
    """La frase tradotta nella lingua scelta (o la stessa, se non c'è ancora o se non va tradotta)."""
    if not isinstance(s, str) or not s.strip():
        return s
    lg = _ta_lingua()
    if lg == "it" or lg not in TA_NOMI_LINGUE:
        return s
    try:
        d = TRADUZIONI.get(lg, {})
        if s in d:
            return d[s]
    except Exception:
        pass
    testa = s[: len(s) - len(s.lstrip())]
    coda = s[len(s.rstrip()):]
    nucleo = s.strip()
    if len(_ta_re.findall(r"[A-Za-zÀ-ÿ]", nucleo)) < 2 or _ta_re.fullmatch(r"https?://\S+|[\w.+-]+@[\w.-]+", nucleo):
        return s
    _ta_carica(lg)
    chiave = _ta_norm(nucleo)
    with _TA_B:
        tr = _TA_M["tr"].get(lg, {}).get(chiave) or _TA_M["dinamiche"].get(lg, {}).get(chiave)
    if tr:
        return testa + tr + coda
    if not _ta_del_programma(nucleo):
        return s
    with _TA_B:
        _TA_M["coda"].setdefault(lg, set()).add(chiave)
    try:
        st.session_state["_ta_attese"] = True
    except Exception:
        pass
    _ta_avvia()
    return s


_TA_BLOCCHI = _ta_re.compile(r"(<style.*?</style>|<script.*?</script>|<[^>]+>|&[a-zA-Z#0-9]+;)", _ta_re.S | _ta_re.I)


def ta_testo(s):
    """Un testo che può contenere HTML o markdown: si traducono solo i pezzi di testo, i tag restano."""
    if not isinstance(s, str) or _ta_lingua() == "it":
        return s
    if "<" not in s:
        return ta_frase(s)
    pezzi = _TA_BLOCCHI.split(s)
    return "".join(p if (i % 2 == 1 or not p.strip()) else ta_frase(p) for i, p in enumerate(pezzi))


# ---------------------------------------------------------------------------------------------------------------------
# il lavoro in sottofondo: traduce la coda a gruppi con l'IA gratuita
# ---------------------------------------------------------------------------------------------------------------------
_TA_ISTR = """You translate the user interface of a family app (pantry, health, documents, house, car, pets) from Italian into {lingua}.
You receive a JSON object {{"id": "Italian text"}}. Return ONLY a JSON object with the same ids and the translations.
Rules: natural, short, simple words for elderly people using a phone; keep emoji, numbers, punctuation, markdown (**bold**, _italic_, [links](url)), HTML entities and
placeholders like {{nome}} exactly as they are; do NOT translate proper names of people, brands, places and app names (VitaMemo, Streamlit, GitHub, PayPal); keep the same tone."""


def _ta_avvia():
    with _TA_B:
        if _TA_M["lavora"] or _ta_time.time() < _TA_M["pausa"]:
            return
        _TA_M["lavora"] = True
    _ta_thr.Thread(target=_ta_lavora, daemon=True).start()


def _ta_lavora():
    try:
        while True:
            with _TA_B:
                lg = next((l_ for l_, c in _TA_M["coda"].items() if c), None)
                if not lg:
                    return
                gruppo = sorted(_TA_M["coda"][lg])[:TA_GRUPPO]
            if "il_testo" not in globals() and not _ta_os.environ.get("VM_TRADUZIONE_FINTA"):
                with _TA_B:
                    _TA_M["pausa"] = _ta_time.time() + 600
                return
            ingresso = {str(i): g for i, g in enumerate(gruppo)}
            if _ta_os.environ.get("VM_TRADUZIONE_FINTA"):                   # solo per le prove automatiche (nessun servizio vero)
                _ta_time.sleep(0.5)
                fatte = {i: f"[{lg.upper()}] {g}" for i, g in ingresso.items()}
                risp = _ta_json.dumps(fatte)
            else:
                risp, _prov = il_testo(_TA_ISTR.format(lingua=TA_NOMI_LINGUE[lg]), _ta_json.dumps(ingresso, ensure_ascii=False), max_tokens=6000, ordine=TA_ORDINE)
            fatte = il_json(risp) if "il_json" in globals() else None
            if not isinstance(fatte, dict):
                with _TA_B:
                    _TA_M["pausa"] = _ta_time.time() + 300                  # nessun servizio libero: riprovo fra 5 minuti
                return
            nuove = {}
            for i, it_ in ingresso.items():
                tr = fatte.get(i)
                if isinstance(tr, str) and tr.strip():
                    nuove[it_] = tr.strip()
            with _TA_B:
                for it_ in gruppo:
                    _TA_M["coda"][lg].discard(it_)
                stabili = {k: v for k, v in nuove.items() if k.lower() in _ta_catalogo()[0]}
                _TA_M["tr"].setdefault(lg, {}).update(stabili)
                din = _TA_M["dinamiche"].setdefault(lg, {})
                din.update({k: v for k, v in nuove.items() if k not in stabili})
                while len(din) > 5000:
                    din.pop(next(iter(din)))
                _TA_M["versione"] += 1
            if stabili:
                try:                                                        # restano per sempre, uguali per tutti
                    crea_archivio().modifica(f"traduzioni/{lg}.json", lambda d, s_=stabili: d.setdefault("t", {}).update(s_), f"Traduzioni automatiche ({lg})")
                except Exception:
                    pass
    finally:
        with _TA_B:
            _TA_M["lavora"] = False


def ta_attesa():
    """Da chiamare in alto in ogni pagina: se ci sono frasi in traduzione, appena pronte la pagina si ridisegna da sola (una volta, nei primi 2 minuti)."""
    if _ta_lingua() == "it":
        return
    ss = st.session_state
    with _TA_B:
        ver = _TA_M["versione"]
        attese = sum(len(c) for c in _TA_M["coda"].values())
    ss["_ta_ver"] = ver
    if not attese and not ss.get("_ta_attese"):
        return
    ss.setdefault("_ta_t0", _ta_time.time())
    if _ta_time.time() - ss["_ta_t0"] > 120:
        ss.pop("_ta_t0", None)
        ss["_ta_attese"] = False
        return

    @st.fragment(run_every=4)
    def _ta_controlla():
        with _TA_B:
            v = _TA_M["versione"]
            restano = sum(len(c) for c in _TA_M["coda"].values())
        if v != st.session_state.get("_ta_ver"):
            st.session_state["_ta_ver"] = v
            if not restano:
                st.session_state["_ta_attese"] = False
                st.session_state.pop("_ta_t0", None)
            st.rerun()
    try:
        _ta_controlla()
    except Exception:
        pass


# ---------------------------------------------------------------------------------------------------------------------
# avvolgere Streamlit (una volta sola per tutta la vita del programma)
# ---------------------------------------------------------------------------------------------------------------------
_TA_TESTO_PRIMO = ("markdown", "caption", "header", "subheader", "title", "info", "warning", "error", "success", "toast", "write")
_TA_ETICHETTA = ("button", "link_button", "download_button", "form_submit_button", "expander", "popover", "metric", "text_input", "text_area", "number_input", "date_input",
                 "time_input", "checkbox", "toggle", "slider", "select_slider", "color_picker", "file_uploader", "camera_input", "audio_input", "chat_input")
_TA_OPZIONI = ("selectbox", "multiselect", "radio", "pills", "segmented_control", "select_slider")


def _ta_avvolgi(orig, tipo, di_classe=False):
    def _f(*args, **kw):
        try:
            if _ta_lingua() != "it" and not getattr(_TA_LOC, "dentro", False):
                args = list(args)
                sé = [args.pop(0)] if di_classe and args else []
                if tipo == "testo":
                    if args and isinstance(args[0], str) and (len(args) == 1 or orig.__name__ != "write"):
                        args[0] = ta_testo(args[0])
                    elif "body" in kw and isinstance(kw["body"], str):
                        kw["body"] = ta_testo(kw["body"])
                else:
                    nascosta = kw.get("label_visibility") in ("collapsed", "hidden")   # etichette nascoste: spesso servono allo script per trovare il campo
                    if nascosta:
                        pass
                    elif args and isinstance(args[0], str):
                        args[0] = ta_testo(args[0])
                    elif isinstance(kw.get("label"), str):
                        kw["label"] = ta_testo(kw["label"])
                    for k in ("help", "placeholder"):
                        if isinstance(kw.get(k), str):
                            kw[k] = ta_testo(kw[k])
                    if tipo == "opzioni":
                        ff = kw.get("format_func") or str
                        kw["format_func"] = lambda x, _ff=ff: ta_testo(_ff(x)) if isinstance(_ff(x), str) else _ff(x)
                    if tipo == "schede" and args and isinstance(args[0], (list, tuple)):
                        args[0] = [ta_testo(x) if isinstance(x, str) else x for x in args[0]]
                args = sé + args
        except Exception:
            pass
        _TA_LOC.dentro = True                                              # i pulsanti fatti da altri «avvolgimenti» dentro questo non si ritraducono
        try:
            return orig(*args, **kw)
        finally:
            _TA_LOC.dentro = False
    try:
        import functools as _ft
        _ft.update_wrapper(_f, orig)                                       # tiene anche i «segni» degli altri avvolgimenti (es. _sempre_chiusa)
    except Exception:
        pass
    _f._ta = True
    return _f


def _ta_installa():
    from streamlit.delta_generator import DeltaGenerator as _DG
    gruppi = [(n, "testo") for n in _TA_TESTO_PRIMO] + [(n, "etichetta") for n in _TA_ETICHETTA] + [(n, "opzioni") for n in _TA_OPZIONI] + [("tabs", "schede")]
    for nome, tipo in gruppi:
        m = getattr(_DG, nome, None)
        if m is not None and not getattr(m, "_ta", False):
            setattr(_DG, nome, _ta_avvolgi(m, tipo, di_classe=True))         # per colonne, contenitori, finestre
        g = getattr(st, nome, None)
        if g is None or getattr(g, "_ta", False):
            continue
        if getattr(g, "__self__", None) is getattr(st, "_main", object()):
            setattr(st, nome, getattr(st._main, nome))                       # st.qualcosa(...) passa dallo stesso avvolgimento
        else:
            setattr(st, nome, _ta_avvolgi(g, tipo))                          # già avvolta da altri (es. le linguette sempre chiuse): la avvolgo tenendo i suoi segni
    dlg = getattr(st, "dialog", None)
    if dlg is not None and not getattr(dlg, "_ta", False):
        def _dialog(title, *a, **k):
            return dlg(ta_testo(title) if isinstance(title, str) else title, *a, **k)
        _dialog._ta = True
        st.dialog = _dialog


if not getattr(st, "_ta_installato", False):
    try:
        _ta_installa()
        st._ta_installato = True
    except Exception:
        pass
