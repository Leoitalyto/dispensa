# -*- coding: utf-8 -*-
"""VITAMEMO — il nome nuovo dell'app e la SCHERMATA INIZIALE con i dieci pulsanti luminosi.

Che cosa fa (senza rifare niente di ciò che esiste):
 1. vm_schermata_home(): la schermata iniziale è l'immagine «VitaMemo — Il tuo mondo, in ordine.» con dieci zone cliccabili
    (Dispensa, Salute, I miei documenti, Archivio, Casa, Lavoro, Auto, Animali, Chat, Utilità). Ogni zona porta alla sua sezione
    con lo stesso comando dei bottoni colorati (nav_vai). I numeri degli avvisi sono quelli di sempre (pn_scadenze: scadenze,
    richiami, messaggi nuovi…) ma in NEON FLUORESCENTE, e la sezione che ha avvisi PULSA di luce.
    Le sezioni che la persona non può usare restano spente, con il lucchetto.
 2. In cima a ogni pagina (sopra i bottoni colorati) c'è «🌐 VitaMemo · Home» per tornare alla schermata iniziale.
 3. Quando si entra si parte sempre dalla schermata iniziale. Solo se la pagina riparte da sola mentre la stavi usando
    (telefono in pausa per pochi minuti) torni nella sezione in cui eri, come prima.
 4. La pagina di accesso mostra la fascia «VitaMemo» e la scheda del browser porta il nome e l'icona nuovi.
 5. La guida «Informazioni» ha le voci di VitaMemo (cos'è, la schermata iniziale, i numeri luminosi, come tornare).
Le immagini stanno in vitamemo_img.py (dentro al programma: non serve caricare file a parte). Caricato dopo accessibilita.py.
Se questo file manca, l'app funziona come prima (si apre sulla Dispensa)."""
import base64 as _b64_vm
import html as _h_vm
import io as _io_vm
import time as _time_vm

import streamlit as st

VM_NOME = "VitaMemo"
VM_MOTTO = "Il tuo mondo, in ordine."
VM_NEON = "#ccff00"                       # il colore fluorescente dei numeri e della pulsazione
VM_RIPRESA_MIN = 20                       # entro quanti minuti, se la pagina riparte da sola, si torna nella sezione in cui si era
_VM_LARG, _VM_ALT = 720, 1280             # misure dell'immagine: le zone qui sotto sono in questi pixel
# sezione, nome letto dallo schermo, x0, y0, x1, y1
VM_ZONE = [
    ("dispensa", "Dispensa", 52, 294, 344, 481), ("salute", "Salute", 374, 294, 667, 481),
    ("documenti", "I miei documenti", 52, 503, 344, 693), ("archivio", "Archivio", 374, 503, 667, 693),
    ("casa", "Casa", 52, 713, 344, 887), ("lavoro", "Lavoro", 374, 713, 667, 887),
    ("auto", "Auto", 52, 903, 344, 1060), ("animali", "Animali", 374, 903, 667, 1060),
    ("chat", "Chat", 52, 1075, 344, 1233), ("utilita", "Utilità", 374, 1075, 667, 1233),
]
_VM_NOMI = {z[0]: z[1] for z in VM_ZONE}


# ---------------------------------------------------------------------------------------------------------------------
# immagini
# ---------------------------------------------------------------------------------------------------------------------
def _vm_img(nome):
    return globals().get(nome) or ""


def vm_icona():
    """L'icona con il mondo per la scheda del browser (se manca: l'emoji del mondo)."""
    try:
        from PIL import Image
        dati = _vm_img("VM_IMG_ICONA")
        return Image.open(_io_vm.BytesIO(_b64_vm.b64decode(dati))) if dati else "🌐"
    except Exception:
        return "🌐"


def vm_hero_login():
    """La fascia «VitaMemo — Il tuo mondo, in ordine.» per la pagina di accesso."""
    dati = _vm_img("VM_IMG_FASCIA")
    if not dati:
        return ("<div style='background:#04060d;border-radius:22px;padding:22px 18px;margin:0 0 14px;text-align:center'>"
                "<div style='color:#fff;font-size:2.4rem;font-weight:900;letter-spacing:.5px'>" + VM_NOME + "</div>"
                "<div style='color:#cfd8dc;font-size:1.05rem'>" + VM_MOTTO + "</div></div>")
    return ("<div style='background:#04060d;border-radius:22px;margin:0 0 14px;overflow:hidden;box-shadow:0 6px 18px rgba(0,0,0,.35)'>"
            "<img alt='" + VM_NOME + " — " + VM_MOTTO + "' src='data:image/webp;base64," + dati + "' "
            "style='display:block;width:100%;max-width:560px;margin:0 auto'></div>")


# ---------------------------------------------------------------------------------------------------------------------
# stato: quando si vede la schermata iniziale
# ---------------------------------------------------------------------------------------------------------------------
def _vm_minuto():
    return int(_time_vm.time() // 60)


def _vm_segna_tempo():
    """Scrive nell'indirizzo l'ora dell'ultimo uso (ogni 3 minuti al massimo): serve a capire se la pagina è ripartita da sola da poco."""
    try:
        m = _vm_minuto()
        if abs(m - int(st.session_state.get("_vm_t") or 0)) >= 3 or st.query_params.get("t") is None:
            st.session_state["_vm_t"] = m
            st.query_params["t"] = str(m)
    except Exception:
        pass


def vm_home_attiva():
    """True se adesso va mostrata la schermata iniziale. Alla prima pagina dopo l'accesso lo decide una volta:
    si parte dalla schermata iniziale, tranne quando la pagina è ripartita da sola da pochi minuti (allora si torna dove si era)."""
    ss = st.session_state
    sess = ss.get("sess") or {}
    if not sess:
        return False
    if "vm_home" not in ss or ss.get("_vm_uid") != sess.get("uid"):
        ss["_vm_uid"] = sess.get("uid")
        ripresa = False
        try:
            s = st.query_params.get("s")
            t_ = int(st.query_params.get("t") or 0)
            valide = set(globals().get("_SEZ_VALIDE") or ()) | {"dispensa"}
            ripresa = s in valide and abs(_vm_minuto() - t_) <= VM_RIPRESA_MIN
        except Exception:
            ripresa = False
        ss["vm_home"] = not ripresa
    return bool(ss.get("vm_home"))


def vm_vai_home():
    """Comando dei pulsanti «Home»: torna alla schermata iniziale."""
    for k in globals().get("_STATI_DA_CHIUDERE", ()):
        st.session_state.pop(k, None)
    st.session_state["vm_home"] = True


def vm_apri(sezione):
    """Comando delle dieci zone: apre la sezione (lo stesso comando dei bottoni colorati)."""
    st.session_state["vm_home"] = False
    if "nav_vai" in globals():
        nav_vai(sezione)


def vm_disponibile(sezione, nascoste=None):
    """La sezione esiste in questa app e la persona collegata può usarla."""
    if sezione != "dispensa" and "SEZIONI_NAV" in globals() and sezione not in SEZIONI_NAV:
        return False
    if nascoste is None:
        nascoste = _vm_nascoste()
    return sezione not in nascoste


def _vm_nascoste():
    try:
        return set(sv_nascoste()) if "sv_nascoste" in globals() else set()
    except Exception:
        return set()


def vm_avvisi():
    """{sezione: [avvisi]} — gli stessi dei bottoni colorati (scadenze, richiami, messaggi nuovi), senza le sezioni non disponibili."""
    try:
        sc = dict(pn_scadenze()) if "pn_scadenze" in globals() else {}
    except Exception:
        sc = {}
    nasc = _vm_nascoste()
    return {s: list(v) for s, v in sc.items() if v and s in _VM_NOMI and vm_disponibile(s, nasc)}


# ---------------------------------------------------------------------------------------------------------------------
# la schermata iniziale
# ---------------------------------------------------------------------------------------------------------------------
def _vm_pc(v, tot):
    return f"{v * 100.0 / tot:.3f}%"


def _vm_css_home(avvisi, spente):
    img = _vm_img("VM_IMG_HOME")
    r = ["<style>",
         # tutta la pagina diventa scura come l'immagine (solo qui)
         ".stApp,[data-testid='stAppViewContainer'],[data-testid='stMain']{background:#04060d !important;background-image:none !important}",
         "[data-testid='stHeader']{background:transparent !important}",
         "[data-testid='stMainBlockContainer']{padding-top:2.6rem !important}",
         ".st-key-vm_home{position:relative !important;display:block !important;width:100% !important;max-width:460px;margin:0 auto 10px !important;"
         f"aspect-ratio:{_VM_LARG}/{_VM_ALT};container-type:inline-size;border-radius:22px;overflow:hidden;"
         + (f"background:#04060d url('data:image/webp;base64,{img}') center/100% 100% no-repeat;" if img else "background:#04060d;")
         + "box-shadow:0 0 26px rgba(0,120,255,.25)}",
         ".st-key-vm_home [data-testid='stVerticalBlock']{position:static !important;display:block !important;height:0 !important;gap:0 !important}",
         "[class*='st-key-vmh_']{position:absolute !important;margin:0 !important;padding:0 !important;min-width:0 !important;max-width:none !important}",
         "[class*='st-key-vmh_'] [data-testid='stButton'],[class*='st-key-vmh_'] .stButton{width:100% !important;height:100% !important;margin:0 !important}",
         "[class*='st-key-vmh_'] button{position:absolute !important;inset:0 !important;width:100% !important;height:100% !important;min-height:0 !important;"
         "margin:0 !important;padding:0 !important;background:transparent !important;border:0 !important;border-radius:9% / 14% !important;box-shadow:none !important;"
         "color:transparent !important;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:background .12s,transform .12s}",
         "[class*='st-key-vmh_'] button p,[class*='st-key-vmh_'] button div{color:transparent !important;font-size:1px !important;line-height:1 !important}",
         "[class*='st-key-vmh_'] button:hover{background:rgba(255,255,255,.07) !important}",
         "[class*='st-key-vmh_'] button:active{background:rgba(255,255,255,.2) !important;transform:scale(.97)}",
         "[class*='st-key-vmh_'] button:focus-visible{outline:3px solid #fff !important;outline-offset:-4px}",
         # la pulsazione luminosa delle sezioni con avvisi e il numero al neon
         "@keyframes vm-pulsa{0%,100%{box-shadow:0 0 0 0 rgba(204,255,0,0),inset 0 0 0 0 rgba(204,255,0,0);-webkit-backdrop-filter:brightness(1);backdrop-filter:brightness(1)}"
         "50%{box-shadow:0 0 22px 6px rgba(204,255,0,.85),inset 0 0 18px 2px rgba(204,255,0,.5);-webkit-backdrop-filter:brightness(1.4) saturate(1.25);backdrop-filter:brightness(1.4) saturate(1.25)}}",
         "@keyframes vm-numero{0%,100%{transform:scale(1);box-shadow:0 0 8px 2px rgba(204,255,0,.9),0 0 20px 6px rgba(204,255,0,.45)}"
         "50%{transform:scale(1.14);box-shadow:0 0 12px 4px rgba(204,255,0,1),0 0 30px 12px rgba(204,255,0,.7)}}"]
    for sez, _nome, x0, y0, x1, y1 in VM_ZONE:
        r.append(f".st-key-vmh_{sez}{{left:{_vm_pc(x0, _VM_LARG)} !important;top:{_vm_pc(y0, _VM_ALT)} !important;"
                 f"width:{_vm_pc(x1 - x0, _VM_LARG)} !important;height:{_vm_pc(y1 - y0, _VM_ALT)} !important}}")
    for sez, n in avvisi.items():
        testo = str(n) if n < 100 else "99+"
        r.append(f".st-key-vmh_{sez} button{{animation:vm-pulsa 1.5s ease-in-out infinite}}")
        r.append(f".st-key-vmh_{sez}::after{{content:'{testo}';position:absolute;top:-5%;right:-3%;z-index:3;pointer-events:none;"
                 "min-width:8.6cqw;height:8.6cqw;padding:0 1.6cqw;box-sizing:border-box;border-radius:5cqw;display:flex;align-items:center;justify-content:center;"
                 f"background:{VM_NEON};color:#0b1200;font:900 5.2cqw/1 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;"
                 "border:.5cqw solid #f4ffb8;animation:vm-numero 1.5s ease-in-out infinite}")
    for sez in spente:
        r.append(f".st-key-vmh_{sez} button{{background:rgba(2,4,10,.72) !important;cursor:not-allowed;opacity:1 !important}}")
        r.append(f".st-key-vmh_{sez}::after{{content:'🔒';position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:9cqw;pointer-events:none;z-index:3;filter:drop-shadow(0 0 5px rgba(255,255,255,.95)) brightness(1.35)}}")
    r.append("@supports not (width:1cqw){[class*='st-key-vmh_']::after{min-width:30px !important;height:30px !important;font-size:18px !important;border-radius:16px !important;padding:0 6px !important;border-width:2px !important}}")
    r.append("@media (prefers-reduced-motion:reduce){[class*='st-key-vmh_'] button,[class*='st-key-vmh_']::after{animation:none !important}"
             + "".join(f".st-key-vmh_{s} button{{box-shadow:0 0 16px 4px rgba(204,255,0,.8),inset 0 0 12px 1px rgba(204,255,0,.45) !important}}" for s in avvisi) + "}")
    r.append(".vm-riep{max-width:460px;margin:8px auto 10px;padding:12px 14px;border-radius:18px;background:rgba(10,16,30,.92);border:2px solid rgba(204,255,0,.75);"
             "box-shadow:0 0 14px rgba(204,255,0,.35);color:#e8f1ff;font-size:.95rem}"
             ".vm-riep .tit{font-weight:900;font-size:1.08rem;color:" + VM_NEON + ";text-shadow:0 0 8px rgba(204,255,0,.6)}"
             ".vm-riep .sez{margin-top:8px;font-weight:800;color:#fff}.vm-riep .voce{margin-left:10px;color:#cfd8e6}.vm-riep .altro{margin-left:10px;opacity:.75}"
             ".vm-riep.ok{border-color:rgba(0,230,118,.7);box-shadow:0 0 12px rgba(0,230,118,.3)}.vm-riep.ok .tit{color:#69f0ae;text-shadow:0 0 8px rgba(0,230,118,.5)}"
             ".vm-ciao{max-width:460px;margin:0 auto 6px;color:#cfd8e6;font-size:.95rem;text-align:center}.vm-ciao b{color:#fff}")
    r.append("</style>")
    return "".join(r)


def _vm_riepilogo(sc):
    """Sotto l'immagine: quante cose ci sono da guardare, sezione per sezione (oppure «Tutto a posto»)."""
    tot = sum(len(v) for v in sc.values())
    if not tot:
        st.markdown("<div class='vm-riep ok'><div class='tit'>✅ Tutto a posto: niente da guardare.</div></div>", unsafe_allow_html=True)
        return
    righe = ""
    for sez, nome, *_resto in VM_ZONE:
        voci = sc.get(sez)
        if not voci:
            continue
        righe += f"<div class='sez'>{_h_vm.escape(nome)} ({len(voci)})</div>" + "".join(f"<div class='voce'>{_h_vm.escape(str(v))}</div>" for v in voci[:3])
        if len(voci) > 3:
            righe += f"<div class='altro'>…e altre {len(voci) - 3}: apri la sezione per vederle</div>"
    st.markdown(f"<div class='vm-riep'><div class='tit'>🔔 {'C’è 1 cosa' if tot == 1 else 'Ci sono ' + str(tot) + ' cose'} da guardare</div>"
                "<div style='font-size:.85rem;opacity:.85'>I pulsanti che pulsano di luce ti dicono dove: toccali per aprire.</div>" + righe + "</div>", unsafe_allow_html=True)


def vm_schermata_home():
    """La schermata iniziale di VitaMemo."""
    for nome_f in ("nu_aggiorna_sessione", "nav_pulisci_interfaccia"):
        if nome_f in globals():
            try:
                globals()[nome_f]()
            except Exception:
                pass
    try:
        if st.query_params.get("s") != "home":
            st.query_params["s"] = "home"
    except Exception:
        pass
    _vm_segna_tempo()
    nasc = _vm_nascoste()
    sc = vm_avvisi()
    spente = [z[0] for z in VM_ZONE if not vm_disponibile(z[0], nasc)]
    st.markdown(_vm_css_home({s: len(v) for s, v in sc.items()}, spente), unsafe_allow_html=True)
    if st.session_state.get("messaggio"):
        st.success(st.session_state.pop("messaggio"))
    with st.container(key="vm_home"):
        for sez, nome, *_resto in VM_ZONE:
            n = len(sc.get(sez, []))
            spenta = sez in spente
            etichetta = nome + (f": {n} " + ("avviso" if n == 1 else "avvisi") if n else "") + (" (non disponibile)" if spenta else "")
            st.button(etichetta, key=f"vmh_{sez}", on_click=vm_apri, args=(sez,), disabled=spenta)
    nome_persona = str((st.session_state.get("sess") or {}).get("nome") or "").strip()
    if nome_persona:
        st.markdown(f"<div class='vm-ciao'>Ciao, <b>{_h_vm.escape(nome_persona)}</b>: tocca un pulsante per entrare.</div>", unsafe_allow_html=True)
    _vm_riepilogo(sc)
    if "pulsante_info" in globals():
        try:
            pulsante_info("vitamemo")
        except Exception:
            pass
    if "musica_inietta" in globals():
        try:
            musica_inietta()
        except Exception:
            pass


# ---------------------------------------------------------------------------------------------------------------------
# «🌐 VitaMemo · Home» in cima a ogni pagina, sopra i bottoni colorati
# ---------------------------------------------------------------------------------------------------------------------
_VM_CSS_TORNA = ("<style>.st-key-vm_torna button{width:100% !important;min-height:50px !important;border-radius:16px !important;"
                 "background:linear-gradient(135deg,#04060d 0%,#0b1f4a 60%,#123a8a 100%) !important;border:2px solid #4fc3f7 !important;"
                 "box-shadow:0 0 12px rgba(79,195,247,.55),0 4px 0 rgba(0,0,0,.3) !important;margin:0 0 4px !important}"
                 ".st-key-vm_torna button p{color:#fff !important;font-weight:900 !important;font-size:1.05rem !important;letter-spacing:.3px;text-shadow:0 0 8px rgba(79,195,247,.9)}"
                 ".st-key-vm_torna button:active{transform:scale(.97)}</style>")


def vm_barra_home():
    st.markdown(_VM_CSS_TORNA, unsafe_allow_html=True)
    with st.container(key="vm_torna"):
        st.button("🌐 " + VM_NOME + " · Home", key="vm_torna_btn", width="stretch", on_click=vm_vai_home, help="Torna alla schermata iniziale con tutte le sezioni")


if "nav_pagine" in globals() and "_vm_nav_prima" not in globals():
    _vm_nav_prima = nav_pagine

    def nav_pagine(corrente):                                        # noqa: F811
        try:
            vm_barra_home()
        except Exception:
            pass
        r = _vm_nav_prima(corrente)
        _vm_segna_tempo()
        return r

if "nav_vai" in globals() and "_vm_vai_prima" not in globals():
    _vm_vai_prima = nav_vai

    def nav_vai(sezione):                                            # noqa: F811
        st.session_state["vm_home"] = False                          # chi apre una sezione (da qualunque pulsante) esce dalla schermata iniziale
        return _vm_vai_prima(sezione)


# ---------------------------------------------------------------------------------------------------------------------
# la guida «Informazioni» di VitaMemo e i titoli delle finestre
# ---------------------------------------------------------------------------------------------------------------------
if "UI_IT" in globals():
    UI_IT.setdefault("sez_vitamemo", "🌐 VitaMemo")
    UI_IT.setdefault("sez_animali", "🐾 Animali")
    UI_IT.setdefault("sez_chat", "💬 Chat")
if "_NOMI_SEZIONI" in globals() and "_GUIDE" in globals():
    _NOMI_SEZIONI.setdefault("vitamemo", "🌐 VitaMemo")
    _GUIDE.setdefault("vitamemo", [
        ("🌐 Cos'è VitaMemo",
         """**VitaMemo** è il nome nuovo dell'app (prima si chiamava «La nostra dispensa»). **Non cambia niente dei tuoi dati**: la password è la stessa, e prodotti, medicinali, documenti, auto, animali e messaggi sono tutti al loro posto.
VitaMemo tiene in ordine le cose di casa in dieci sezioni: **Dispensa**, **Salute**, **I miei documenti**, **Archivio**, **Casa**, **Lavoro**, **Auto**, **Animali**, **Chat** e **Utilità**.""",
         "vitamemo nome app nuovo cos'è come si chiama la nostra dispensa sezioni"),
        ("🏁 La schermata iniziale",
         """Quando entri vedi la **schermata iniziale**: il titolo **VitaMemo** e **dieci pulsanti luminosi**, uno per sezione.
1. **Tocca un pulsante** (per esempio **Salute**): si apre quella sezione.
2. Sotto i pulsanti leggi **quante cose ci sono da guardare** e in quale sezione.
3. Più sotto c'è il pulsante rosso **Clicca per informazioni** (questa guida) e, in basso a destra, il **robottino** che ti aiuta.""",
         "schermata iniziale home inizio pulsanti luminosi dieci sezioni entrare aprire partenza"),
        ("🔔 I numeri luminosi e la pulsazione",
         """Se su un pulsante compare un **numero giallo-verde fluorescente**, in quella sezione ci sono **cose da guardare**: una scadenza vicina, un richiamo, un messaggio nuovo. Il numero dice **quante**.
Il pulsante con il numero **pulsa di luce**, così lo noti subito. Toccalo: dentro la sezione trovi il dettaglio. Quando hai sistemato tutto, il numero sparisce e il pulsante smette di pulsare.""",
         "numero avvisi neon fluorescente pulsazione luminosa pulsa lampeggia scadenze notifiche campanella quante"),
        ("↩️ Tornare alla schermata iniziale",
         """In **ogni pagina**, in alto, c'è il pulsante scuro **🌐 VitaMemo · Home**: toccalo e torni alla schermata iniziale.
Subito sotto restano i **bottoni colorati** di sempre, per passare direttamente da una sezione all'altra senza tornare all'inizio.""",
         "tornare indietro home schermata iniziale pulsante vitamemo sezioni bottoni colorati"),
        ("🔒 Un pulsante è spento, con il lucchetto",
         """Vuol dire che quella sezione **non è disponibile per il tuo account**: l'ha deciso chi gestisce l'app. Se pensi che sia un errore, chiedi a lui.""",
         "lucchetto pulsante spento sezione non disponibile bloccata permesso"),
    ])
    if "_ID_GUIDA" in globals():
        _ID_GUIDA.setdefault("vitamemo", ["vm_cosa", "vm_home", "vm_numeri", "vm_torna", "vm_lucchetto"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("vitamemo", "vm_home")
