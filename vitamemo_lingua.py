# -*- coding: utf-8 -*-
"""VITAMEMO NELLA LINGUA DI CHI LO APRE.

1. LINGUA AUTOMATICA: alla prima apertura l'app legge la lingua del telefono/browser (Accept-Language) e parte in quella:
   italiano, inglese, spagnolo, francese, tedesco, rumeno, arabo, portoghese. Se la lingua del telefono non è tra queste parte in inglese.
   Chi ha già scelto una lingua (menu «Lingua / Language») o ne ha una salvata nel suo profilo la ritrova com'era: la scelta della persona vince sempre.
2. SCHERMATA INIZIALE nella lingua: l'immagine con i dieci pulsanti ha le scritte della lingua (immagini in vitamemo_img_lingue.py).
   Le zone cliccabili sono le stesse. Il globo resta quello animato del programma.
3. Il pulsante rosso «Clicca per informazioni» ha il badge nella lingua.
4. Le scritte sotto l'immagine (quante cose ci sono da guardare, «Ciao, nome…») e i nomi letti dallo schermo sono nella lingua.
Caricato dopo vitamemo_tema.py. Se questo file manca, tutto resta come prima (italiano)."""
import html as _h_vmi

import streamlit as st

VMI_LINGUE = ("it", "en", "es", "fr", "de", "ro", "ar", "pt")


# ---------------------------------------------------------------------------------------------------------------------
# 1. la lingua del telefono
# ---------------------------------------------------------------------------------------------------------------------
def _vmi_lingua_da_intestazione(valore):
    """Dalla riga «it-IT,it;q=0.9,en;q=0.8» alla prima lingua che l'app sa (nell'ordine di preferenza). Nessuna in elenco → «en». Riga vuota → None."""
    valore = str(valore or "").strip()
    if not valore:
        return None
    cand = []
    for i, parte in enumerate(valore.split(",")):
        pezzi = parte.strip().split(";")
        tag = pezzi[0].strip().lower().replace("_", "-")
        if not tag or tag == "*":
            continue
        q = 1.0
        for extra in pezzi[1:]:
            extra = extra.strip()
            if extra.startswith("q="):
                try:
                    q = float(extra[2:])
                except ValueError:
                    q = 0.0
        if q > 0:
            cand.append((-q, i, tag.split("-")[0]))
    cand.sort()
    for _q, _i, lg in cand:
        if lg in VMI_LINGUE:
            return lg
    return "en" if cand else None


def _vmi_lingua_browser():
    try:
        h = st.context.headers
        return _vmi_lingua_da_intestazione(h.get("Accept-Language") or h.get("accept-language"))
    except Exception:
        return None


def _vmi_lingua_telefono():
    """L'ultima lingua usata su QUESTO telefono (biscottino «vm_lang»), così la pagina di accesso si apre già in quella lingua."""
    try:
        lg = (st.context.cookies or {}).get("vm_lang")
        return lg if lg in VMI_LINGUE else None
    except Exception:
        return None


if "lang" not in st.session_state and not st.session_state.get("_vmi_lingua_auto"):
    st.session_state["_vmi_lingua_auto"] = True
    _vmi_tel = _vmi_lingua_telefono()
    _vmi_l0 = _vmi_tel or _vmi_lingua_browser()
    if _vmi_l0:
        st.session_state["lang"] = _vmi_l0
    if _vmi_tel:
        st.session_state["_vmi_da_telefono"] = True                  # questo telefono ricorda l'ultima lingua usata: è quella che si vede e con cui si entra


def _vmi_ricorda_lingua_telefono():
    """Scrive sul telefono la lingua in uso (vale un anno). Se non si può, resta la lingua del telefono."""
    lg = st.session_state.get("lang")
    if lg not in VMI_LINGUE:
        return
    try:
        cod = ("<!doctype html><html><body><script>try{window.parent.document.cookie='vm_lang=" + lg + ";path=/;max-age=31536000;SameSite=Lax';}catch(e){}</script></body></html>")
        with st.container(key="nascosti_vmi_lang"):
            if hasattr(st, "iframe"):
                st.iframe(cod, height=1)
            else:
                import streamlit.components.v1 as _c_vmi
                _c_vmi.html(cod, height=1)
        st.markdown("<style>[class*='st-key-nascosti_vmi_lang']{display:none !important}</style>", unsafe_allow_html=True)
    except Exception:
        pass


_vmi_ricorda_lingua_telefono()                                       # a ogni pagina (accesso compreso): l'ultima lingua usata resta su questo telefono


def _vmi_lg():
    try:
        lg = st.session_state.get("lang", "it")
    except Exception:
        lg = "it"
    return lg if lg in VMI_LINGUE else "it"


# ---------------------------------------------------------------------------------------------------------------------
# 2. la schermata iniziale nella lingua
# ---------------------------------------------------------------------------------------------------------------------
if "_vm_img" in globals() and "_vmi_img_prima" not in globals():
    _vmi_img_prima = _vm_img

    def _vm_img(nome):                                               # noqa: F811
        if nome == "VM_IMG_HOME":
            d = (globals().get("VMI_HOME") or {}).get(_vmi_lg())
            if d:
                return d
        return _vmi_img_prima(nome)

_VMI_SEZ = {
    "en": dict(dispensa="Pantry", salute="Health", documenti="My documents", archivio="Archive", casa="Home", lavoro="Work", auto="Car", animali="Animals", chat="Chat", utilita="Utilities"),
    "es": dict(dispensa="Despensa", salute="Salud", documenti="Mis documentos", archivio="Archivo", casa="Casa", lavoro="Trabajo", auto="Auto", animali="Animales", chat="Chat", utilita="Utilidades"),
    "fr": dict(dispensa="Garde-manger", salute="Santé", documenti="Mes documents", archivio="Archives", casa="Maison", lavoro="Travail", auto="Voiture", animali="Animaux", chat="Chat", utilita="Utilitaires"),
    "de": dict(dispensa="Vorrat", salute="Gesundheit", documenti="Meine Dokumente", archivio="Archiv", casa="Zuhause", lavoro="Arbeit", auto="Auto", animali="Tiere", chat="Chat", utilita="Nützliches"),
    "pt": dict(dispensa="Despensa", salute="Saúde", documenti="Meus documentos", archivio="Arquivo", casa="Casa", lavoro="Trabalho", auto="Carro", animali="Animais", chat="Chat", utilita="Utilitários"),
    "ro": dict(dispensa="Cămară", salute="Sănătate", documenti="Documentele mele", archivio="Arhivă", casa="Casă", lavoro="Muncă", auto="Mașină", animali="Animale", chat="Chat", utilita="Utilități"),
    "ar": dict(dispensa="المخزن", salute="الصحة", documenti="مستنداتي", archivio="الأرشيف", casa="المنزل", lavoro="العمل", auto="السيارة", animali="الحيوانات", chat="الدردشة", utilita="الأدوات"),
}
_VMI_FR = {
    "it": dict(av1="avviso", avn="avvisi", nd="(non disponibile)", ok="Tutto a posto: niente da guardare.", una="C’è 1 cosa", molte="Ci sono {n} cose",
               suff=" da guardare", pulsa="I pulsanti che pulsano di luce ti dicono dove: toccali per aprire.", altre="…e altre {n}: apri la sezione per vederle",
               ciao="Ciao, <b>{nome}</b>: tocca un pulsante per entrare."),
    "en": dict(av1="alert", avn="alerts", nd="(not available)", ok="All good: nothing to look at.", una="There is 1 thing", molte="There are {n} things",
               suff=" to look at", pulsa="The buttons that pulse with light tell you where: tap them to open.", altre="…and {n} more: open the section to see them",
               ciao="Hi, <b>{nome}</b>: tap a button to enter."),
    "es": dict(av1="aviso", avn="avisos", nd="(no disponible)", ok="Todo en orden: nada que revisar.", una="Hay 1 cosa", molte="Hay {n} cosas",
               suff=" que revisar", pulsa="Los botones que laten con luz te dicen dónde: tócalos para abrir.", altre="…y {n} más: abre la sección para verlas",
               ciao="Hola, <b>{nome}</b>: toca un botón para entrar."),
    "fr": dict(av1="alerte", avn="alertes", nd="(indisponible)", ok="Tout est en ordre : rien à regarder.", una="Il y a 1 chose", molte="Il y a {n} choses",
               suff=" à regarder", pulsa="Les boutons qui pulsent de lumière t'indiquent où : touche-les pour ouvrir.", altre="…et {n} autres : ouvre la section pour les voir",
               ciao="Salut, <b>{nome}</b> : touche un bouton pour entrer."),
    "de": dict(av1="Hinweis", avn="Hinweise", nd="(nicht verfügbar)", ok="Alles in Ordnung: nichts anzusehen.", una="Es gibt 1 Sache", molte="Es gibt {n} Sachen",
               suff=" zum Ansehen", pulsa="Die Tasten, die leuchtend pulsieren, zeigen dir, wo: tippe darauf, um sie zu öffnen.", altre="…und {n} weitere: öffne den Bereich, um sie zu sehen",
               ciao="Hallo, <b>{nome}</b>: tippe auf eine Taste, um einzutreten."),
    "pt": dict(av1="aviso", avn="avisos", nd="(indisponível)", ok="Está tudo em ordem: nada para ver.", una="Há 1 coisa", molte="Há {n} coisas",
               suff=" para ver", pulsa="Os botões que pulsam de luz mostram onde: toque neles para abrir.", altre="…e mais {n}: abra a área para vê-las",
               ciao="Olá, <b>{nome}</b>: toque num botão para entrar."),
    "ro": dict(av1="alertă", avn="alerte", nd="(indisponibil)", ok="Totul e în ordine: nimic de văzut.", una="E 1 lucru", molte="Sunt {n} lucruri",
               suff=" de văzut", pulsa="Butoanele care pulsează luminos îți arată unde: atinge-le pentru a deschide.", altre="…și încă {n}: deschide secțiunea ca să le vezi",
               ciao="Salut, <b>{nome}</b>: atinge un buton ca să intri."),
    "ar": dict(av1="تنبيه", avn="تنبيهات", nd="(غير متاح)", ok="كل شيء على ما يرام: لا شيء للمراجعة.", una="هناك شيء واحد", molte="هناك {n} أشياء",
               suff=" للمراجعة", pulsa="الأزرار التي تنبض بالضوء تدلك على المكان: المسها لتفتحها.", altre="…و{n} أخرى: افتح القسم لرؤيتها",
               ciao="مرحباً <b>{nome}</b>: المس زرًا للدخول."),
}

if "VM_ZONE" in globals():
    if "_VMI_ZONE_IT" not in globals():
        _VMI_ZONE_IT = list(VM_ZONE)
    VM_ZONE = [(z[0], _VMI_SEZ.get(_vmi_lg(), {}).get(z[0], z[1])) + tuple(z[2:]) for z in _VMI_ZONE_IT]      # i nomi letti dallo schermo, nella lingua


def _vmi_etichetta(nome, n, spenta):
    f = _VMI_FR[_vmi_lg()]
    return nome + (f": {n} " + (f["av1"] if n == 1 else f["avn"]) if n else "") + (" " + f["nd"] if spenta else "")


def _vmi_ciao(nome_persona):
    f = _VMI_FR[_vmi_lg()]
    return "<div class='vm-ciao'>" + f["ciao"].format(nome=_h_vmi.escape(str(nome_persona))) + "</div>"


if "_vm_riepilogo" in globals() and "_vmi_riep_prima" not in globals():
    _vmi_riep_prima = _vm_riepilogo

    def _vm_riepilogo(sc):                                           # noqa: F811
        if _vmi_lg() == "it":
            return _vmi_riep_prima(sc)
        f = _VMI_FR[_vmi_lg()]
        rtl = " style='direction:rtl;text-align:right'" if _vmi_lg() == "ar" else ""
        tot = sum(len(v) for v in sc.values())
        if not tot:
            st.markdown(f"<div class='vm-riep ok'{rtl}><div class='tit'>✅ {_h_vmi.escape(f['ok'])}</div></div>", unsafe_allow_html=True)
            return
        righe = ""
        for sez, nome, *_resto in VM_ZONE:
            voci = sc.get(sez)
            if not voci:
                continue
            righe += f"<div class='sez'>{_h_vmi.escape(nome)} ({len(voci)})</div>" + "".join(f"<div class='voce'>{_h_vmi.escape(str(v))}</div>" for v in voci[:3])
            if len(voci) > 3:
                righe += "<div class='altro'>" + _h_vmi.escape(f["altre"].format(n=len(voci) - 3)) + "</div>"
        frase = (f["una"] if tot == 1 else f["molte"].format(n=tot)) + f["suff"]
        st.markdown(f"<div class='vm-riep'{rtl}><div class='tit'>🔔 {_h_vmi.escape(frase)}</div>"
                    f"<div style='font-size:.85rem;opacity:.85'>{_h_vmi.escape(f['pulsa'])}</div>" + righe + "</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------------------------------------------------
# 3. il badge «Clicca per informazioni» nella lingua
# ---------------------------------------------------------------------------------------------------------------------
if "_info_uri" in globals() and "_vmi_uri_prima" not in globals():
    _vmi_uri_prima = _info_uri

    def _info_uri():                                                 # noqa: F811
        b = (globals().get("VMI_BADGE") or {}).get(_vmi_lg())
        if b:
            return "data:image/webp;base64," + b[0]
        return _vmi_uri_prima()


def _vmi_badge_css(sezione):
    b = (globals().get("VMI_BADGE") or {}).get(_vmi_lg())
    if not b:
        return ""
    larg, alt = b[1], b[2]
    mw = min(640, int(round(200.0 * larg / alt)))                    # il badge a due righe è più stretto, quello a una riga più largo: altezza simile
    return (f"<style>div.st-key-ginfo_{sezione} button{{aspect-ratio:{larg}/{alt} !important;max-width:{mw}px !important}}</style>")


if "pulsante_info" in globals() and "_vmi_info_prima" not in globals():
    _vmi_info_prima = pulsante_info

    def pulsante_info(sezione):                                      # noqa: F811
        css = _vmi_badge_css(sezione)
        if css:
            try:
                st.markdown(css, unsafe_allow_html=True)
            except Exception:
                pass
        return _vmi_info_prima(sezione)
