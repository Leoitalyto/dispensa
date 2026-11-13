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
CH_PAGINA = 30                        # messaggi mostrati alla volta
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


def ch_bolla(m, mio, nome, adesso_):
    """Un messaggio in HTML sicuro (ogni carattere è «escapato»): a destra e verde se è mio, a sinistra e bianco se è di un altro."""
    testo = _ch_html.escape(m.get("testo", "")).replace("\n", "<br>")
    chi = "" if mio else f"<div style='font-size:.8rem;font-weight:800;color:#00695c;margin-bottom:2px'>{_ch_html.escape(nome or m.get('nome') or '')}</div>"
    ora = f"<div style='font-size:.72rem;opacity:.65;text-align:right;margin-top:3px'>{_ch_html.escape(ch_ora_it(m.get('t'), adesso_))}</div>"
    fondo, allinea = ("#d7f5e3", "flex-end") if mio else ("#ffffff", "flex-start")
    return (f"<div style='display:flex;justify-content:{allinea};margin:5px 0'><div style='max-width:86%;background:{fondo};color:#1b2b2b;border-radius:16px;padding:8px 12px;"
            f"box-shadow:0 1px 3px rgba(0,0,0,.15);font-weight:400;font-size:1rem;line-height:1.4;word-wrap:break-word;overflow-wrap:anywhere'>{chi}{testo}{ora}</div></div>")


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
.ch-box{background:rgba(255,255,255,.55);border-radius:18px;padding:6px 10px;margin:6px 0}
</style>"""


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
    """I messaggi della conversazione: si aggiornano da soli ogni 10 secondi mentre la chat è aperta."""
    sess = _ch_sess()
    uid = str(sess.get("uid"))
    d = _ch_dati()
    nomi = _ch_nomi()
    lista = (d.get("conv") or {}).get(chiave, []) if ch_puo(chiave, uid) else []
    mostra = int(st.session_state.get("ch_mostra_" + chiave, CH_PAGINA))
    adesso_ = _ch_ora()
    if len(lista) > mostra:
        if st.button(f"⬆️ Mostra i messaggi più vecchi ({len(lista) - mostra})", key="ch_vecchi_" + chiave, width="stretch"):
            st.session_state["ch_mostra_" + chiave] = mostra + CH_PAGINA
            st.rerun(scope="fragment")
    if not lista:
        st.markdown("<div class='ch-box' style='text-align:center;color:#37474f;font-weight:600'>Nessun messaggio ancora. Scrivi il primo qui sotto 👇</div>", unsafe_allow_html=True)
    righe = "".join(ch_bolla(m, m.get("da") == uid, nomi.get(m.get("da")), adesso_) for m in lista[-mostra:])
    st.markdown("<div class='ch-box'>" + righe + "</div>", unsafe_allow_html=True)
    if lista and uid not in ("", "None", "prova"):
        try:
            if ch_non_letti(d, uid).get(chiave):                         # qualcosa di nuovo che sto guardando: si segna letto (un solo salvataggio)
                _ch_segna(chiave)
        except Exception:
            pass
    st.caption(f"Aggiornato alle {adesso_.strftime('%H:%M:%S')} · la lista si aggiorna da sola ogni 10 secondi.")


def schermata_chat():
    """La pagina «Chat»."""
    if "nav_barra" in globals():
        nav_barra("chat")
    st.markdown(_CH_CSS, unsafe_allow_html=True)
    st.markdown("<div class='ch-hero'><div class='ico'>💬</div><div><h1>Chat</h1><p>Scrivi alle persone della famiglia, dentro l'app</p></div></div>", unsafe_allow_html=True)
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
    chiavi = ["tutti"] + [ch_chiave_privata(uid, u) for u, _n in altri]
    nl = ch_non_letti(d, uid)
    etich = {k: ch_etichetta(k, uid, nomi) + (f" 🔴{nl[k]}" if nl.get(k) else "") for k in chiavi}
    if len(chiavi) == 1:
        st.caption("Per ora sei l'unica persona nell'app: qui scrivi a «Tutti». Quando altre persone avranno la loro password compariranno anche le conversazioni private.")
    corrente_k = "ch_conv"
    if st.session_state.get(corrente_k) not in chiavi:
        st.session_state[corrente_k] = "tutti"
    if hasattr(st, "pills"):
        scelta = st.pills("Con chi vuoi parlare?", chiavi, format_func=lambda k: etich.get(k, k), default=st.session_state[corrente_k], key="ch_pills", label_visibility="collapsed")
    else:
        scelta = st.radio("Con chi vuoi parlare?", chiavi, format_func=lambda k: etich.get(k, k), index=chiavi.index(st.session_state[corrente_k]), horizontal=True, key="ch_pills", label_visibility="collapsed")
    chiave = scelta if scelta in chiavi else st.session_state[corrente_k]
    st.session_state[corrente_k] = chiave
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
                    st.session_state.pop("ch_mostra_" + chiave, None)
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
4. Per vedere i messaggi più vecchi tocca **⬆️ Mostra i messaggi più vecchi**.
**Se ti sei sbagliato:** apri **🗑️ Elimina un messaggio**, scegli il messaggio e tocca **🗑️ Elimina questo messaggio** (puoi togliere **solo i tuoi**; chi gestisce l'app può togliere qualunque messaggio).
**Solo testo:** niente foto e niente file. **Privacy:** le conversazioni private non le vedono le altre persone nell'app, ma stanno nello stesso archivio privato dell'app: non scriverci cose segretissime.""",
         "chat scrivere messaggio invia eliminare non letti notifica privata testo"),
    ])
    _ID_GUIDA.setdefault("chat", ["ch_cosa", "ch_usa"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("chat", "ch_cosa")
