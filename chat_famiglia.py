# -*- coding: utf-8 -*-
"""CHAT · una sezione tutta sua («💬 Chat»), gratuita, dentro l'app: messaggi tra le persone della famiglia che usano «La nostra dispensa».

COSA C'È
• «👨‍👩‍👧 Tutti»: la chat di gruppo con tutte le persone dell'app.
• Una conversazione PRIVATA con ciascuna persona (solo voi due, dentro l'app).
• I messaggi nuovi si vedono da soli (la lista si aggiorna ogni 10 secondi mentre la chat è aperta). Sul bottone «💬 Chat» in alto compare «🔔 N» quando ci sono messaggi non letti
  (e lampeggia come gli altri); sulle linguette delle conversazioni compare il numero dei non letti.
• Si può eliminare un proprio messaggio (l'amministratore può eliminare qualunque messaggio). Si tengono gli ultimi 500 messaggi per conversazione.
• Solo testo (fino a 1000 caratteri): niente foto e niente file, così non si consuma spazio.
• L'amministratore può nascondere la Chat a una persona da «Sezioni visibili», come le altre sezioni.

DOVE STA: un file solo, `chat.json`, nell'archivio privato dei dati (lo stesso delle altre cose). I messaggi privati NON sono visibili alle altre persone nell'app, ma stanno nello stesso archivio
GitHub privato dell'app, quindi chi gestisce quell'archivio tecnicamente può leggerli: non scrivere cose segretissime.
DATI: {"prog": numero progressivo, "conv": {"tutti": [msg…], "p:<id1>|<id2>": [msg…]}, "letti": {uid: {conv: id dell'ultimo messaggio letto}}}; msg = {id, da (uid), nome, t (ISO), testo}.
Caricato dopo pagine_nav.py e sezioni.py."""
import html as _ch_html
import re as _ch_re
from datetime import datetime, timedelta

import streamlit as st

CH_FILE = "chat.json"
CH_MAX_CAR = 1000
CH_MAX_MSG = 500                      # messaggi conservati per conversazione
CH_ALTEZZA = 470                      # altezza (in pixel) della finestra dei messaggi: dentro si scorre su e giù, come su WhatsApp
CH_AGGIORNA = "10s"                   # ogni quanto si aggiorna la lista mentre la chat è aperta


# ---------------------------------------------------------------------------------------------------------------------
# logica (senza schermo: provata a parte)
# ---------------------------------------------------------------------------------------------------------------------
def ch_chiave_privata(a, b):
    """La chiave della conversazione privata fra due persone (uguale qualunque sia l'ordine)."""
    x, y = sorted([str(a), str(b)])
    return f"p:{x}|{y}"


def ch_partecipanti(chiave):
    """Gli uid di una conversazione privata, oppure None per «tutti»."""
    if chiave.startswith("p:") and "|" in chiave:
        return chiave[2:].split("|", 1)
    return None


def ch_puo(chiave, uid):
    """Questa persona può leggere e scrivere in questa conversazione?"""
    if chiave == "tutti":
        return True
    p = ch_partecipanti(chiave)
    return bool(p) and uid in p


def ch_pulisci_testo(testo):
    """Testo del messaggio ripulito (niente righe vuote di troppo, nessun carattere di controllo), al massimo CH_MAX_CAR."""
    t = str(testo or "").replace("\r", "")
    t = _ch_re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", t)
    t = _ch_re.sub(r"[ \t]+\n", "\n", t)
    t = _ch_re.sub(r"\n{3,}", "\n\n", t).strip()
    return t[:CH_MAX_CAR]


def ch_invia(d, chiave, uid, nome, testo, ora_iso):
    """Aggiunge un messaggio al file dei dati `d`. Ritorna il messaggio, oppure None se il testo è vuoto o la persona non può scrivere lì."""
    t = ch_pulisci_testo(testo)
    if not t or not ch_puo(chiave, uid):
        return None
    d["prog"] = int(d.get("prog") or 0) + 1
    msg = {"id": d["prog"], "da": str(uid), "nome": str(nome or ""), "t": ora_iso, "testo": t}
    lista = d.setdefault("conv", {}).setdefault(chiave, [])
    lista.append(msg)
    if len(lista) > CH_MAX_MSG:
        del lista[:len(lista) - CH_MAX_MSG]
    # chi scrive ha letto tutto fino a qui
    d.setdefault("letti", {}).setdefault(str(uid), {})[chiave] = msg["id"]
    return msg


def ch_elimina(d, chiave, msg_id, uid, admin=False):
    """Toglie un messaggio: solo il proprio (l'amministratore qualunque). True se tolto."""
    if not ch_puo(chiave, uid) and not admin:
        return False
    lista = (d.get("conv") or {}).get(chiave) or []
    for i, m in enumerate(lista):
        if m.get("id") == msg_id and (admin or m.get("da") == str(uid)):
            del lista[i]
            return True
    return False


def ch_conversazioni_di(d, uid):
    """Le chiavi delle conversazioni che questa persona può vedere e che esistono nel file (più «tutti», sempre)."""
    chiavi = ["tutti"]
    for k in (d.get("conv") or {}):
        if k != "tutti" and ch_puo(k, uid) and k not in chiavi:
            chiavi.append(k)
    return chiavi


def ch_non_letti(d, uid):
    """{conversazione: quanti messaggi di ALTRI non ha ancora letto}, solo i numeri maggiori di zero."""
    letti = ((d.get("letti") or {}).get(str(uid)) or {})
    out = {}
    for k in ch_conversazioni_di(d, uid):
        ultimo = int(letti.get(k) or 0)
        n = sum(1 for m in (d.get("conv") or {}).get(k, []) if m.get("id", 0) > ultimo and m.get("da") != str(uid))
        if n:
            out[k] = n
    return out


def ch_segna_letti(d, uid, chiave):
    """Segna come letti tutti i messaggi della conversazione. True se qualcosa è cambiato."""
    lista = (d.get("conv") or {}).get(chiave) or []
    ultimo = max([m.get("id", 0) for m in lista] or [0])
    mio = d.setdefault("letti", {}).setdefault(str(uid), {})
    if int(mio.get(chiave) or 0) >= ultimo:
        return False
    mio[chiave] = ultimo
    return True


def ch_partecipanti_app(utenti, admin_nome):
    """[(uid, nome)] di tutte le persone che possono usare la chat: l'amministratore e gli utenti attivi."""
    out = [("admin", admin_nome or "Amministratore")]
    for u in utenti or []:
        if u.get("attivo", True) and u.get("id") and u.get("nome"):
            out.append((str(u["id"]), str(u["nome"])))
    return out


def ch_etichetta(chiave, uid, nomi):
    """Il nome da mostrare sulla linguetta di una conversazione."""
    if chiave == "tutti":
        return "👨‍👩‍👧 Tutti"
    p = ch_partecipanti(chiave) or []
    altro = next((x for x in p if x != str(uid)), "")
    return "👤 " + (nomi.get(altro) or "Persona")


def ch_ora_it(iso, adesso_):
    """«14:32» se è di oggi, «ieri 14:32», altrimenti «13/11 14:32»."""
    try:
        t = datetime.fromisoformat(str(iso))
    except ValueError:
        return ""
    if t.date() == adesso_.date():
        return t.strftime("%H:%M")
    if t.date() == (adesso_ - timedelta(days=1)).date():
        return "ieri " + t.strftime("%H:%M")
    return t.strftime("%d/%m %H:%M")


_CH_GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
_CH_MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def ch_giorno_etichetta(iso, adesso_):
    """«Oggi», «Ieri» oppure «sabato 8 novembre» (con l'anno se è di un altro anno). Vuoto se la data non si legge."""
    try:
        t = datetime.fromisoformat(str(iso))
    except ValueError:
        return ""
    if t.date() == adesso_.date():
        return "Oggi"
    if t.date() == (adesso_ - timedelta(days=1)).date():
        return "Ieri"
    s = f"{_CH_GIORNI[t.weekday()]} {t.day} {_CH_MESI[t.month - 1]}"
    return s if t.year == adesso_.year else s + f" {t.year}"


def ch_ora_breve(iso):
    """«14:32» (l'ora, senza il giorno: il giorno lo dice la riga di separazione)."""
    try:
        return datetime.fromisoformat(str(iso)).strftime("%H:%M")
    except ValueError:
        return ""


def ch_bolla(m, mio, nome, adesso_, breve=False):
    """Un messaggio in HTML sicuro (ogni carattere è «escapato»): a destra e verde se è mio, a sinistra e bianco se è di un altro. `breve`: solo l'ora (c'è già la riga del giorno)."""
    testo = _ch_html.escape(m.get("testo", "")).replace("\n", "<br>")
    chi = "" if mio else f"<div style='font-size:.8rem;font-weight:800;color:#00695c;margin-bottom:2px'>{_ch_html.escape(nome or m.get('nome') or '')}</div>"
    ora = f"<div style='font-size:.72rem;opacity:.65;text-align:right;margin-top:3px'>{_ch_html.escape(ch_ora_breve(m.get('t')) if breve else ch_ora_it(m.get('t'), adesso_))}</div>"
    fondo, allinea = ("#d7f5e3", "flex-end") if mio else ("#ffffff", "flex-start")
    return (f"<div style='display:flex;justify-content:{allinea};margin:5px 0'><div style='max-width:86%;background:{fondo};color:#1b2b2b;border-radius:16px;padding:8px 12px;"
            f"box-shadow:0 1px 3px rgba(0,0,0,.15);font-weight:400;font-size:1rem;line-height:1.4;word-wrap:break-word;overflow-wrap:anywhere'>{chi}{testo}{ora}</div></div>")


def ch_righe(lista, uid, nomi, adesso_):
    """TUTTI i messaggi di una conversazione come HTML, con la riga del giorno («Oggi», «Ieri», «sabato 8 novembre») ogni volta che il giorno cambia."""
    out, giorno = [], None
    for m in lista:
        g = ch_giorno_etichetta(m.get("t"), adesso_)
        if g and g != giorno:
            giorno = g
            out.append(f"<div style='text-align:center;margin:10px 0 4px'><span style='background:rgba(255,255,255,.85);color:#37474f;font-size:.75rem;font-weight:700;padding:3px 12px;border-radius:999px;box-shadow:0 1px 2px rgba(0,0,0,.12)'>{_ch_html.escape(g)}</span></div>")
        out.append(ch_bolla(m, m.get("da") == str(uid), nomi.get(m.get("da")), adesso_, breve=True))
    return "".join(out)


def ch_ultimo_messaggio(d, chiave):
    """L'ora (testo ISO) dell'ultimo messaggio di una conversazione, oppure «» se è vuota."""
    lista = (d.get("conv") or {}).get(chiave) or []
    return str(lista[-1].get("t") or "") if lista else ""


def ch_ordine_conversazioni(d, uid, vista_uids):
    """Le conversazioni da mostrare come pulsanti, in ordine: «Tutti», poi QUELLE CHE HANNO MESSAGGI (la più recente per prima, così non si perde mai un pezzo di chat),
    poi le persone scelte a mano in «Chi tenere in vista» che non hanno ancora messaggi. Ritorna (pulsanti, altre_persone_senza_messaggi)."""
    con_msg = [k for k in ch_conversazioni_di(d, uid) if k != "tutti" and (d.get("conv") or {}).get(k)]
    con_msg.sort(key=lambda k: ch_ultimo_messaggio(d, k), reverse=True)
    scelte = [ch_chiave_privata(uid, u) for u in vista_uids]
    pulsanti = ["tutti"] + con_msg + [k for k in scelte if k not in con_msg]
    return pulsanti, con_msg


# ---------------------------------------------------------------------------------------------------------------------
# registrazione della sezione (come Lavoro): bottone nella barra, permessi, ordine
# ---------------------------------------------------------------------------------------------------------------------
try:
    if "SEZIONI_NAV" in globals() and "chat" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(len(SEZIONI_NAV) - 1 if "utilita" in SEZIONI_NAV else len(SEZIONI_NAV), "chat")
    if "NOMI_NAV" in globals():
        NOMI_NAV["chat"] = "Chat"
    if "SV_SEZIONI" in globals():
        SV_SEZIONI["chat"] = "💬 Chat"
    if "_SV_DA_SEZIONE_HOME" in globals():
        _SV_DA_SEZIONE_HOME["chat"] = "chat"
    if "_PN_VOCI" in globals() and not any(v[0] == "chat" for v in _PN_VOCI):
        _i = next((i for i, v in enumerate(_PN_VOCI) if v[0] == "utilita"), len(_PN_VOCI))
        _PN_VOCI.insert(_i, ("chat", "💬 Chat", "#26c6da", "#00838f"))
except Exception:
    pass


# ---------------------------------------------------------------------------------------------------------------------
# lettura e scrittura
# ---------------------------------------------------------------------------------------------------------------------
def _ch_sess():
    return st.session_state.get("sess") or {}


def _ch_dati():
    try:
        return carica_dati(crea_archivio(), CH_FILE) or {}
    except Exception:
        return {}


def _ch_utenti():
    try:
        return leggi_utenti()
    except Exception:
        return []


def _ch_nome_admin():
    try:
        return nome_admin()
    except Exception:
        return "Amministratore"


def _ch_nomi():
    """{uid: nome} di tutte le persone (i nomi si leggono ogni volta: se il nome cambia, cambia anche qui)."""
    return dict(ch_partecipanti_app(_ch_utenti(), _ch_nome_admin()))


def _ch_ora():
    return adesso() if "adesso" in globals() else datetime.now()


def ch_non_letti_miei():
    """Quanti messaggi non letti ha la persona collegata (tutte le conversazioni). 0 se non c'è nessuna sessione o la chat non è disponibile."""
    sess = _ch_sess()
    if not sess or sess.get("uid") in (None, "prova"):
        return 0
    try:
        return sum(ch_non_letti(_ch_dati(), sess["uid"]).values())
    except Exception:
        return 0


# ---------------------------------------------------------------------------------------------------------------------
# schermata
# ---------------------------------------------------------------------------------------------------------------------
_CH_CSS = """<style>
.ch-hero{background:linear-gradient(135deg,#00838f 0%,#26c6da 55%,#80deea 100%);color:#fff;padding:16px 20px;border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.15);display:flex;align-items:center;gap:14px}
.ch-hero .ico{font-size:3rem;line-height:1}.ch-hero h1{margin:0;font-size:1.7rem;line-height:1.15;color:#fff;padding:0}.ch-hero p{margin:2px 0 0;font-size:.95rem;opacity:.95}
.ch-hero .ico-img{height:122px;width:auto;max-width:36%;flex:0 0 auto;filter:drop-shadow(0 0 7px rgba(255,255,255,.45)) drop-shadow(0 4px 6px rgba(0,0,0,.4))}
.ch-box{padding:2px 4px;margin:0}
.st-key-ch_scroll{background:rgba(255,255,255,.55);border-radius:18px;padding:4px 8px;margin:6px 0;border:1px solid rgba(0,0,0,.06)}
</style>"""


# ---------------------------------------------------------------------------------------------------------------------
# chi tenere in vista: le persone scelte stanno come pulsanti, tutte le altre in UN SOLO menu a tendina
# ---------------------------------------------------------------------------------------------------------------------
def ch_vista_pulita(vista, uids):
    """Le persone da tenere in vista, ripulite: solo quelle che esistono ancora, senza doppioni, nell'ordine scelto."""
    viste, out = set(), []
    for u in vista or []:
        if u in uids and u not in viste:
            viste.add(u)
            out.append(u)
    return out


def _ch_vista():
    """Le persone che questa persona ha scelto di tenere in vista (si ricorda nel suo file personale). Nessuna, finché non sceglie."""
    if "ch_vista" not in st.session_state:
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"]) or {}
            v = (d.get("impostazioni") or {}).get("chat_vista", [])
        except Exception:
            v = []
        st.session_state["ch_vista"] = [str(x) for x in v] if isinstance(v, list) else []
    return st.session_state["ch_vista"]


def _ch_salva_vista():
    """Chiamata quando si cambia la scelta nel riquadro «Chi tenere in vista»."""
    scelte = [str(x) for x in (st.session_state.get("ch_vista_sel") or [])]
    st.session_state["ch_vista"] = scelte
    try:
        salva(lambda d, v=scelte: d.setdefault("impostazioni", {}).__setitem__("chat_vista", v), "Chat: persone in vista")
    except Exception as e:
        st.session_state["ch_avviso"] = f"Non sono riuscito a ricordare la scelta ({type(e).__name__})."


def _ch_ultima():
    """L'ultima conversazione aperta da questa persona (si ricorda nel suo file personale: riaprendo l'app ritrova la stessa)."""
    if "ch_ultima" not in st.session_state:
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"]) or {}
            v = (d.get("impostazioni") or {}).get("chat_ultima")
        except Exception:
            v = None
        st.session_state["ch_ultima"] = str(v) if v else "tutti"
    return st.session_state["ch_ultima"]


def _ch_ricorda_ultima(chiave):
    """Salva la conversazione aperta, ma solo se è cambiata (un salvataggio solo quando si passa a un'altra)."""
    if chiave == st.session_state.get("ch_ultima"):
        return
    st.session_state["ch_ultima"] = chiave
    try:
        salva(lambda d, v=chiave: d.setdefault("impostazioni", {}).__setitem__("chat_ultima", v), "Chat: ultima conversazione")
    except Exception:
        pass                                                         # se non si salva, nessun danno: alla prossima apertura parte da «Tutti»


def _ch_da_pills():
    v = st.session_state.get("ch_pills")
    if v:
        st.session_state["ch_conv"] = v
        _ch_ricorda_ultima(v)


def _ch_da_menu():
    v = st.session_state.get("ch_menu")
    if v:
        st.session_state["ch_conv"] = v
        _ch_ricorda_ultima(v)


def _ch_salva_messaggio(chiave, testo):
    sess = _ch_sess()
    esito = {}

    def _fn(d):
        esito["m"] = ch_invia(d, chiave, sess["uid"], sess.get("nome"), testo, _ch_ora().isoformat(timespec="seconds"))
    salva_file(CH_FILE, _fn, "Chat: messaggio")
    return esito.get("m")


def _ch_segna(chiave):
    sess = _ch_sess()
    esito = {}

    def _fn(d):
        esito["c"] = ch_segna_letti(d, sess["uid"], chiave)
    salva_file(CH_FILE, _fn, "Chat: letti")
    return esito.get("c")


@st.fragment(run_every=CH_AGGIORNA)
def _ch_lista(chiave):
    """TUTTI i messaggi della conversazione, in una finestra che si scorre su e giù (si apre già sull'ultimo messaggio). Si aggiorna da sola ogni 10 secondi."""
    sess = _ch_sess()
    uid = str(sess.get("uid"))
    d = _ch_dati()
    nomi = _ch_nomi()
    lista = (d.get("conv") or {}).get(chiave, []) if ch_puo(chiave, uid) else []
    adesso_ = _ch_ora()
    try:
        finestra = st.container(height=CH_ALTEZZA, border=False, key="ch_scroll", autoscroll=True)
    except TypeError:                                                 # versione di Streamlit più vecchia: nessuno scorrimento automatico in fondo
        finestra = st.container(height=CH_ALTEZZA, border=False, key="ch_scroll")
    with finestra:
        if not lista:
            st.markdown("<div class='ch-box' style='text-align:center;color:#37474f;font-weight:600'>Nessun messaggio ancora. Scrivi il primo qui sotto 👇</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='ch-box'>" + ch_righe(lista, uid, nomi, adesso_) + "</div>", unsafe_allow_html=True)
    firma = f"{chiave}|{len(lista)}|{lista[-1].get('id') if lista else 0}"                # cambia quando arriva un messaggio o si apre un'altra conversazione
    if st.session_state.get("_ch_firma") != firma and "_inietta" in globals():
        st.session_state["_ch_firma"] = firma                          # per sicurezza, in fondo ci si porta anche con un piccolo comando (oltre allo scorrimento automatico)
        try:
            _inietta("(function(){var n=0;function v(){var b=window.document.querySelector('.st-key-ch_scroll');if(b){var e=[b].concat([].slice.call(b.querySelectorAll('*'))).filter(function(x){return x.scrollHeight>x.clientHeight+4&&/(auto|scroll)/.test(window.getComputedStyle(x).overflowY)})[0];if(e)e.scrollTop=e.scrollHeight}if(++n<8)window.setTimeout(v,250)}v()})();")
        except Exception:
            pass
    if lista and uid not in ("", "None", "prova"):
        try:
            if ch_non_letti(d, uid).get(chiave):                         # qualcosa di nuovo che sto guardando: si segna letto (un solo salvataggio)
                _ch_segna(chiave)
        except Exception:
            pass
    st.caption(f"💬 {len(lista)} messaggi: scorri in alto per vedere i più vecchi · aggiornato alle {adesso_.strftime('%H:%M:%S')}, si aggiorna da solo.")


def schermata_chat():
    """La pagina «Chat»."""
    if "nav_barra" in globals():
        nav_barra("chat")
    st.markdown(_CH_CSS, unsafe_allow_html=True)
    _uri = ih_uri("chat.webp", 330) if "ih_uri" in globals() else ""                                  # l'icona blu e oro, senza sfondo; se il file manca resta l'emoji
    _ico = f"<img class='ico-img' alt='Chat' src='{_uri}'>" if _uri else "<div class='ico'>💬</div>"
    st.markdown(f"<div class='ch-hero'>{_ico}<div><h1>Chat</h1><p>Scrivi alle persone della famiglia, dentro l'app</p></div></div>", unsafe_allow_html=True)
    if "pulsante_info" in globals():
        try:
            pulsante_info("chat")
        except Exception:
            pass
    sess = _ch_sess()
    uid = str(sess.get("uid"))
    if uid in ("", "None", "prova"):
        st.info("La chat non è disponibile in prova: entra con la tua password.")
        return
    nomi = _ch_nomi()
    d = _ch_dati()
    altri = [(u, n) for u, n in nomi.items() if u != uid]
    vista = ch_vista_pulita(_ch_vista(), [u for u, _n in altri])
    k_pills, _con_msg = ch_ordine_conversazioni(d, uid, vista)                 # «Tutti» + ogni conversazione che ha messaggi + le persone scelte a mano
    k_menu = [ch_chiave_privata(uid, u) for u, _n in altri if ch_chiave_privata(uid, u) not in k_pills]
    chiavi = k_pills + k_menu
    nl = ch_non_letti(d, uid)
    etich = lambda k: ch_etichetta(k, uid, nomi) + (f" 🔴{nl[k]}" if nl.get(k) else "")
    if len(chiavi) == 1:
        st.caption("Per ora sei l'unica persona nell'app: qui scrivi a «Tutti». Quando altre persone avranno la loro password compariranno anche le conversazioni private.")
    if "ch_conv" not in st.session_state:                                         # appena aperta la chat: riparte dall'ultima conversazione che stavi guardando
        st.session_state["ch_conv"] = _ch_ultima()
    if st.session_state.get("ch_conv") not in chiavi:
        st.session_state["ch_conv"] = "tutti"
    attuale = st.session_state["ch_conv"]
    st.session_state["ch_pills"] = attuale if attuale in k_pills else None                       # i due comandi mostrano sempre la stessa conversazione
    if hasattr(st, "pills"):
        st.pills("Con chi vuoi parlare?", k_pills, format_func=etich, selection_mode="single", key="ch_pills", on_change=_ch_da_pills, label_visibility="collapsed")
    else:
        st.radio("Con chi vuoi parlare?", k_pills, format_func=etich, index=k_pills.index(attuale) if attuale in k_pills else 0, horizontal=True, key="ch_pills_r", on_change=lambda: st.session_state.update(ch_conv=st.session_state.get("ch_pills_r")), label_visibility="collapsed")
    if k_menu:
        n_fuori = sum(nl.get(k, 0) for k in k_menu)
        st.session_state["ch_menu"] = attuale if attuale in k_menu else None
        st.selectbox("Altre persone", k_menu, index=None, format_func=etich, key="ch_menu", on_change=_ch_da_menu,
                     placeholder=f"👥 Altre persone ({len(k_menu)})" + (f" 🔴{n_fuori}" if n_fuori else "") + "…", label_visibility="collapsed")
    chiave = st.session_state["ch_conv"]
    if altri:
        with st.expander("⭐ Scegli chi tenere in vista"):
            st.caption("Le persone che scegli qui compaiono come pulsanti in alto. Tutte le altre restano nel menu a tendina «Altre persone».")
            st.multiselect("Persone sempre in vista", [u for u, _n in altri], default=vista, format_func=lambda u: nomi.get(u, u), key="ch_vista_sel", on_change=_ch_salva_vista, label_visibility="collapsed", placeholder="Scegli le persone…")
            if st.session_state.get("ch_avviso"):
                st.warning(st.session_state.pop("ch_avviso"))
    if chiave != "tutti":
        st.caption("🔒 Conversazione privata: la vedete solo voi due nell'app.")
    _ch_lista(chiave)
    with st.form("ch_form_" + chiave, clear_on_submit=True):
        testo = st.text_area("Il tuo messaggio", height=90, max_chars=CH_MAX_CAR, placeholder="Scrivi qui…", label_visibility="collapsed")
        invia = st.form_submit_button("📨 Invia", type="primary", width="stretch")
    if invia:
        if not ch_pulisci_testo(testo):
            st.warning("Scrivi qualcosa prima di inviare.")
        else:
            try:
                if _ch_salva_messaggio(chiave, testo):
                    st.rerun()
                else:
                    st.error("Non sono riuscito a inviare il messaggio. Riprova.")
            except Exception as e:
                st.error(f"Non sono riuscito a inviare il messaggio ({type(e).__name__}). Riprova fra poco.")
    mie = [m for m in ((_ch_dati().get("conv") or {}).get(chiave) or []) if m.get("da") == uid or sess.get("admin")]
    if mie:
        with st.expander("🗑️ Elimina un messaggio"):
            ult = mie[-10:][::-1]
            sel = st.selectbox("Quale messaggio?", [m["id"] for m in ult], format_func=lambda i: next((f"{ch_ora_it(m.get('t'), _ch_ora())} · " + (m.get("nome") if m.get("da") != uid else "io") + ": " + m.get("testo", "")[:50].replace("\n", " ") for m in ult if m["id"] == i), str(i)), key="ch_del_sel")
            if st.button("🗑️ Elimina questo messaggio", key="ch_del_btn", width="stretch"):
                esito = {}
                salva_file(CH_FILE, lambda dd: esito.__setitem__("ok", ch_elimina(dd, chiave, sel, uid, bool(sess.get("admin")))), "Chat: messaggio eliminato")
                st.session_state["messaggio"] = "🗑️ Messaggio eliminato." if esito.get("ok") else "Non ho trovato il messaggio."
                st.rerun()
            st.caption("Vedi i tuoi ultimi 10 messaggi" + (" (come amministratore, anche quelli degli altri)." if sess.get("admin") else "."))
    if st.session_state.get("messaggio"):
        st.success(st.session_state.pop("messaggio"))


# ---- lo smistamento: «chat» va alla sua pagina (con il controllo di «Sezioni visibili»), il resto come prima
if "schermata_farmacia" in globals() and "_ch_schermata_prima" not in globals():
    _ch_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "chat":
            if "sv_nascoste" in globals() and "chat" in sv_nascoste():
                return sv_blocca("chat")
            return schermata_chat()
        return _ch_schermata_prima()


# ---- i messaggi non letti fanno lampeggiare il bottone «💬 Chat» con il numero (ma non entrano nel riepilogo della Home, che elenca solo scadenze)
if "pn_scadenze" in globals() and "_ch_scad_prima" not in globals():
    _ch_scad_prima = pn_scadenze

    def pn_scadenze():                                               # noqa: F811
        out = _ch_scad_prima()
        if st.session_state.get("_ch_senza"):
            return out
        try:
            n = ch_non_letti_miei()
            if n:
                out = dict(out)
                out["chat"] = ["💬 messaggio da leggere"] * min(n, 99)
        except Exception:
            pass
        return out

if "pn_riepilogo" in globals() and "_ch_riep_prima" not in globals():
    _ch_riep_prima = pn_riepilogo

    def pn_riepilogo():                                              # noqa: F811
        st.session_state["_ch_senza"] = True
        try:
            return _ch_riep_prima()
        finally:
            st.session_state["_ch_senza"] = False


if "_NOMI_SEZIONI" in globals():
    _NOMI_SEZIONI.setdefault("chat", "💬 Chat")
    _GUIDE.setdefault("chat", [
        ("💬 Cos'è la Chat",
         """Qui scrivi **alle persone della famiglia** che usano l'app, **gratis** e **senza uscire dall'app**. Si apre dal bottone **💬 Chat** in alto, accanto agli altri.
In cima scegli **con chi parlare**: **👨‍👩‍👧 Tutti** (il gruppo di tutta la famiglia) oppure **👤 una persona** (conversazione **privata**, solo voi due). Sotto vedi i messaggi: **i tuoi a destra in verde**, **quelli degli altri a sinistra in bianco**, con il nome e l'ora.""",
         "chat messaggi famiglia scrivere gruppo privata conversazione"),
        ("✉️ Scrivere e leggere i messaggi",
         """1. Apri **💬 Chat** e scegli **con chi parlare**.
2. In fondo scrivi il messaggio (fino a **1000 caratteri**) e tocca **📨 Invia**.
3. I messaggi **nuovi arrivano da soli**: la lista si aggiorna **ogni 10 secondi** finché la chat è aperta. Se c'è un messaggio che non hai letto, vedi **🔔** sul bottone **💬 Chat** e **🔴 con il numero** sulla persona.
4. **Tutti i messaggi restano sempre lì**: la finestra dei messaggi si **scorre con il dito** verso l'alto per rivedere quelli più vecchi (si apre già sull'ultimo). Le conversazioni che hanno messaggi compaiono **da sole come pulsanti** in alto, la più recente per prima; quando riapri l'app ritrovi **l'ultima conversazione** che stavi guardando.
**Se ti sei sbagliato:** apri **🗑️ Elimina un messaggio**, scegli il messaggio e tocca **🗑️ Elimina questo messaggio** (puoi togliere **solo i tuoi**; chi gestisce l'app può togliere qualunque messaggio).
**Solo testo:** niente foto e niente file. **Privacy:** le conversazioni private non le vedono le altre persone nell'app, ma stanno nello stesso archivio privato dell'app: non scriverci cose segretissime.""",
         "chat scrivere messaggio invia eliminare non letti notifica privata testo"),
    ])
    _ID_GUIDA.setdefault("chat", ["ch_cosa", "ch_usa"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("chat", "ch_cosa")
