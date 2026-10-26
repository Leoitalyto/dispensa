# -*- coding: utf-8 -*-
"""FARMACIA - Fasi 1-3 (profili, medicinali, terapie, visite, vaccini) e ricerca delle farmacie aperte.

Questo file si carica PRIMA di parte3.py (vedi app_dispensa.py). Non modifica la dispensa:
i medicinali sono salvati nella voce "farmacia" del file dati di ogni persona.
Serve solo a organizzare i dati inseriti dall'utente: non dà indicazioni mediche.
"""
from datetime import timedelta
import urllib.parse as _up

MAX_PROFILI = 12
FORME_MED = ["compresse", "capsule", "gocce", "sciroppo", "fiale", "bustine", "crema / pomata",
             "spray", "cerotti", "supposte", "collirio", "altro"]
UNITA_MED = ["pz", "ml", "g", "dosi"]
FILTRI_MED = {"tutti": "Tutti", "scaduti": "Scaduti", "1mese": "Entro 1 mese",
              "2mesi": "Entro 2 mesi", "ok": "Non in scadenza"}

_FA_CSS = """<style>
.fa-hero{background:linear-gradient(135deg,#b71c1c 0%,#e53935 55%,#ef6c00 100%);color:#fff;padding:20px 24px;
 border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.15)}
.fa-hero h1{margin:0;font-size:1.8rem;color:#fff;padding:0}
.fa-hero p{margin:4px 0 0;opacity:.92}
.fa-kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:8px 0 12px}
.fa-k{border-radius:20px;padding:10px 12px;background:rgba(255,255,255,.78);border:1px solid rgba(255,255,255,.95);
 box-shadow:0 4px 14px rgba(0,0,0,.08);color:#1b2b2b}
.fa-k b{display:block;font-size:1.7rem;line-height:1.1}
.fa-k span{font-size:.72rem;font-weight:700}
.fa-k.scaduto{background:#12263f;color:#fff}
.fa-k.rosso{background:#fde4e4}
.fa-k.arancione{background:#ffedd8}
.fa-med{border-left:8px solid var(--c);border-radius:14px;padding:4px 6px 4px 12px;color:#1b2b2b}
.fa-med .nome{font-weight:800;font-size:1.08rem}
.fa-med .riga{font-size:.9rem;opacity:.85;margin-top:2px}
.fa-med .scad{display:inline-block;color:#fff;background:var(--c);border-radius:999px;padding:3px 12px;
 font-size:.82rem;font-weight:700;margin-top:6px}
@media (max-width:640px){.fa-kpi{grid-template-columns:repeat(2,1fr)}}
</style>"""


# ---------------------------------------------------------------- icona nella Home
@st.cache_resource
def _fa_icona_uri():
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    try:
        with open(os.path.join(cartella, "farmacia.webp"), "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode()
    except OSError:
        return ""


def icona_farmacia():
    """Icona cliccabile (croce rossa) che apre la sezione Farmacia."""
    uri = _fa_icona_uri()
    if uri:
        st.markdown(
            "<style>.st-key-fa_icona button{width:112px;height:112px;min-height:112px;border-radius:26px;"
            "border:2px solid rgba(255,255,255,.95);box-shadow:0 8px 22px rgba(0,0,0,.18);"
            f"background:url({uri}) center/82% no-repeat,rgba(255,255,255,.55);color:transparent}}"
            ".st-key-fa_icona button p{font-size:0}</style>", unsafe_allow_html=True)
        premuto = st.button("Farmacia", key="fa_icona", help="Apri la Farmacia")
    else:                                             # se manca farmacia.webp resta un pulsante semplice
        premuto = st.button("🏥 Farmacia", key="fa_icona")
    if premuto:
        st.session_state["farmacia_aperta"] = True
        st.rerun()


# ---------------------------------------------------------------- dati
def _fa_dati():
    return carica_dati(crea_archivio(), st.session_state["percorso"]).get("farmacia") or {}


def _fa_profili(f):
    return f.get("profili") or [{"id": "p0", "nome": st.session_state["sess"]["nome"]}]


def _fa_salva(fn, messaggio):
    nome = st.session_state["sess"]["nome"]

    def _m(d):
        f = d.setdefault("farmacia", {})
        if not f.get("profili"):
            f["profili"] = [{"id": "p0", "nome": nome}]
        f.setdefault("medicinali", [])
        fn(f)
    salva(_m, messaggio)


def _fa_data(iso):
    try:
        return date.fromisoformat(iso) if iso else None
    except ValueError:
        return None


def _fa_idx(lista, valore):
    return lista.index(valore) if valore in lista else 0


# ---------------------------------------------------------------- finestre
@st.dialog("Medicinale")
def _fa_dialogo(pid, med_id=None):
    f = _fa_dati()
    profili = _fa_profili(f)
    m = next((x for x in f.get("medicinali", []) if x["id"] == med_id), {}) if med_id else {}
    nomi = {p["id"]: p["nome"] for p in profili}
    with st.form("fa_form_med"):
        togli_foto = False
        if m.get("foto"):
            try:
                st.image(base64.b64decode(m["foto"].split(",", 1)[1]), width=120)
            except Exception:
                pass
            togli_foto = st.checkbox("Rimuovi la foto attuale")
        foto_up = st.file_uploader("📷 Foto della confezione (facoltativa): scatta o scegli",
                                   type=["jpg", "jpeg", "png", "webp"])
        nome = st.text_input("Nome del medicinale *", value=m.get("nome", ""))
        marca = st.text_input("Marca commerciale", value=m.get("marca", ""))
        principio = st.text_input("Principio attivo", value=m.get("principio", ""))
        dosaggio = st.text_input("Dosaggio (es. 500 mg)", value=m.get("dosaggio", ""))
        forma = st.selectbox("Forma", FORME_MED, index=_fa_idx(FORME_MED, m.get("forma")))
        c1, c2 = st.columns(2)
        quantita = c1.number_input("Quantità", min_value=0.0, step=1.0, value=float(m.get("quantita", 1.0)))
        unita = c2.selectbox("Unità", UNITA_MED, index=_fa_idx(UNITA_MED, m.get("unita")))
        scadenza = st.date_input("Data di scadenza", value=_fa_data(m.get("scadenza")), format="DD/MM/YYYY",
                                 min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
        acquisto = st.date_input("Data di acquisto (facoltativa)", value=_fa_data(m.get("acquisto")),
                                 format="DD/MM/YYYY", min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
        per = st.selectbox("Per chi è", list(nomi), format_func=lambda i: nomi[i],
                           index=_fa_idx(list(nomi), m.get("profilo", pid)))
        note = st.text_area("Note personali", value=m.get("note", ""))
        inviato = st.form_submit_button("Salva", type="primary")
    if inviato:
        if not nome.strip():
            st.error("Scrivi il nome del medicinale.")
            return
        foto = "" if togli_foto else m.get("foto", "")
        if foto_up is not None:
            try:
                foto = foto_a_data_uri(foto_up.getvalue(), 400)
            except Exception:
                st.error("Non riesco a leggere la foto: prova con un'altra.")
                return
        rec = {"foto": foto, "nome": nome.strip(), "marca": marca.strip(), "principio": principio.strip(),
               "dosaggio": dosaggio.strip(), "forma": forma, "quantita": float(quantita), "unita": unita,
               "scadenza": scadenza.isoformat() if scadenza else None,
               "acquisto": acquisto.isoformat() if acquisto else None, "profilo": per, "note": note.strip()}

        def _scrivi(f):
            if med_id:
                for x in f["medicinali"]:
                    if x["id"] == med_id:
                        x.update(rec)
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                f["medicinali"].append(rec)
        try:
            _fa_salva(_scrivi, "Farmacia: medicinale")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        trovate = _fa_conflitti(f, per, rec)
        st.session_state["fa_msg"] = ("⚠️ Medicinale salvato, ma attenzione: contiene «" + "», «".join(trovate) +
                                      "», segnato come allergia di questo profilo." if trovate else "✅ Medicinale salvato.")
        st.rerun()


@st.dialog("Elimina medicinale")
def _fa_dialogo_elimina(med_id, nome):
    st.write(f"Vuoi eliminare **{nome}**?")
    c1, c2 = st.columns(2)
    if c1.button("Sì, elimina", type="primary", width="stretch"):
        try:
            _fa_salva(lambda f: f.__setitem__("medicinali", [x for x in f["medicinali"] if x["id"] != med_id]),
                      "Farmacia: eliminato")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "🗑️ Medicinale eliminato."
        st.rerun()
    if c2.button("Annulla", width="stretch"):
        st.rerun()


# ---------------------------------------------------------------- schermata
def _fa_card(m, data_oggi, conflitti=()):
    stato, giorni = stato_scadenza(m.get("scadenza"), data_oggi)
    e = html.escape
    riga1 = " · ".join(x for x in (m.get("marca"), m.get("principio"), m.get("dosaggio"), m.get("forma")) if x)
    scad = f"{ICONE[stato]} {testo_giorni(stato, giorni)}"
    if m.get("scadenza"):
        scad += f" · {data_it(m['scadenza'])}"
    extra = ""
    if m.get("acquisto"):
        extra += f"<div class='riga'>🛍️ Acquistato il {data_it(m['acquisto'])}</div>"
    if m.get("note"):
        extra += f"<div class='riga'>📝 {e(m['note'])}</div>"
    foto = ""
    if m.get("foto") and src_sicuro(m["foto"]):
        foto = (f"<img src='{e(m['foto'], quote=True)}' alt='' style='float:right;max-width:84px;max-height:84px;"
                "border-radius:12px;margin-left:8px'>")
    for c in conflitti:
        extra = (f"<div class='riga' style='color:#b71c1c;font-weight:800'>🚨 Attenzione: «{e(c)}» è segnato come "
                 f"allergia di questo profilo</div>") + extra
    sfondo = ";background:#ffebee" if conflitti else ""
    return (f"<div class='fa-med' style='--c:{COLORI[stato]}{sfondo}'>{foto}<div class='nome'>💊 {e(m.get('nome', ''))}</div>"
            f"<div class='riga'>{e(riga1)}</div>"
            f"<div class='riga'>📦 {fmt_num(float(m.get('quantita') or 0))} {e(m.get('unita', ''))}</div>"
            f"<span class='scad'>{e(scad)}</span>{extra}</div>")


def schermata_farmacia():
    st.markdown(_FA_CSS, unsafe_allow_html=True)
    if st.button("← Torna alla dispensa", key="fa_indietro"):
        st.session_state["farmacia_aperta"] = False
        st.rerun()
    st.markdown("<div class='fa-hero'><h1>🏥 Farmacia</h1><p>Medicinali e scadenze della tua famiglia</p></div>",
                unsafe_allow_html=True)
    if st.session_state.get("fa_msg"):
        _msg = st.session_state.pop("fa_msg")
        (st.warning if _msg.startswith("⚠️") else st.success)(_msg)

    if st.button("🔎 Trova una farmacia aperta", key="fa_trova", type="primary", width="stretch"):
        _fa_dialogo_farmacie()

    _fa_blocco_avvisi()

    f = _fa_dati()
    profili = _fa_profili(f)
    nomi = {p["id"]: p["nome"] for p in profili}
    if st.session_state.get("fa_profilo") not in nomi:
        st.session_state["fa_profilo"] = profili[0]["id"]
    pid = st.selectbox("👤 Profilo", list(nomi), format_func=lambda i: nomi[i], key="fa_profilo")

    with st.expander(f"👥 Gestisci profili ({len(profili)}/{MAX_PROFILI})"):
        with st.form("fa_nuovo_profilo", clear_on_submit=True):
            nuovo = st.text_input("Nome del nuovo profilo (es. Mamma, Luca)")
            ok_nuovo = st.form_submit_button("Aggiungi profilo", disabled=len(profili) >= MAX_PROFILI)
        if ok_nuovo and nuovo.strip():
            try:
                _fa_salva(lambda f: f["profili"].append({"id": uuid.uuid4().hex[:8], "nome": nuovo.strip()}),
                          "Farmacia: profilo")
                st.session_state["fa_msg"] = f"✅ Profilo «{nuovo.strip()}» aggiunto."
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
        with st.form("fa_rinomina"):
            nuovo_nome = st.text_input(f"Cambia il nome di «{nomi[pid]}»", value=nomi[pid])
            ok_rin = st.form_submit_button("Cambia nome")
        if ok_rin and nuovo_nome.strip():
            def _rin(f):
                for p in f["profili"]:
                    if p["id"] == pid:
                        p["nome"] = nuovo_nome.strip()
            try:
                _fa_salva(_rin, "Farmacia: nome profilo")
                st.rerun()
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
        if len(profili) > 1:
            n_med = sum(1 for m in f.get("medicinali", []) if m.get("profilo") == pid)
            conferma = st.checkbox(f"Elimina il profilo «{nomi[pid]}» con tutti i suoi dati ({n_med} medicinali, terapie, visite, documenti)", key="fa_conf_del")
            if st.button("Elimina profilo", disabled=not conferma):
                try:
                    _fa_elimina_profilo(f, pid)
                    st.session_state.pop("fa_conf_del", None)
                    st.session_state["fa_msg"] = "🗑️ Profilo eliminato."
                    st.rerun()
                except Exception as e:
                    st.error(f"Non sono riuscito a salvare: {e}")

    oggi_ = oggi()
    del_profilo = [m for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid]
    stati = [(m, stato_scadenza(m.get("scadenza"), oggi_)[0]) for m in del_profilo]
    n = lambda *s: sum(1 for _, x in stati if x in s)
    st.markdown(
        "<div class='fa-kpi'>"
        f"<div class='fa-k'><span>Medicinali</span><b>{len(stati)}</b></div>"
        f"<div class='fa-k arancione'><span>Entro 2 mesi</span><b>{n('arancione')}</b></div>"
        f"<div class='fa-k rosso'><span>Entro 1 mese</span><b>{n('rosso')}</b></div>"
        f"<div class='fa-k scaduto'><span>Scaduti</span><b>{n('scaduto')}</b></div></div>",
        unsafe_allow_html=True)

    tab_med, tab_ter, tab_vis, tab_vac = st.tabs(["💊 Medicinali", "📅 Terapie", "🩺 Visite", "💉 Vaccini"])
    with tab_med:
        _fa_blocco_allergie(f, pid, nomi, del_profilo)
        if st.button("➕ Aggiungi medicinale", type="primary", key="fa_aggiungi", width="stretch"):
            _fa_dialogo(pid)

        c1, c2, c3 = st.columns([3, 2, 2])
        cerca = c1.text_input("Cerca", placeholder="nome, marca o principio attivo", label_visibility="collapsed",
                              key="fa_cerca")
        filtro = c2.selectbox("Mostra", list(FILTRI_MED), format_func=lambda k: FILTRI_MED[k],
                              label_visibility="collapsed", key="fa_filtro")
        ordine = c3.selectbox("Ordina", ["Per scadenza", "Per nome"], label_visibility="collapsed", key="fa_ordine")

        visibili = []
        for m, s in stati:
            testo = " ".join(m.get(k, "") for k in ("nome", "marca", "principio")).lower()
            if cerca and cerca.lower() not in testo:
                continue
            if filtro == "scaduti" and s != "scaduto":
                continue
            if filtro == "1mese" and s not in ("rosso", "scaduto"):
                continue
            if filtro == "2mesi" and s not in ("arancione", "rosso", "scaduto"):
                continue
            if filtro == "ok" and s not in ("ok", "nessuna"):
                continue
            visibili.append(m)
        if ordine == "Per nome":
            visibili.sort(key=lambda m: m.get("nome", "").lower())
        else:
            visibili.sort(key=lambda m: m.get("scadenza") or "9999-12-31")

        if not del_profilo:
            st.info(f"Nessun medicinale per {nomi[pid]}. Tocca «Aggiungi medicinale» per inserire il primo.")
        elif not visibili:
            st.info("Nessun medicinale corrisponde ai filtri.")
        for m in visibili:
            with st.container(border=True):
                st.markdown(_fa_card(m, oggi_, _fa_conflitti(f, pid, m)), unsafe_allow_html=True)
                _q = _up.quote_plus(" ".join(x for x in ("foglio illustrativo", m.get("nome", ""), m.get("principio", "")) if x) + " AIFA")
                l1, l2 = st.columns(2, gap="small")
                l1.link_button("📖 Foglio illustrativo", "https://www.google.com/search?q=" + _q, width="stretch")
                l2.link_button("🏛️ Banca dati AIFA", "https://www.aifa.gov.it/riassunto-caratteristiche-e-foglio-illustrativo",
                               width="stretch")
                b1, b2 = st.columns(2, gap="small")
                if b1.button("Elimina", icon=":material/delete:", key="fa_el_" + m["id"], width="stretch"):
                    _fa_dialogo_elimina(m["id"], m.get("nome", ""))
                if b2.button("Modifica", icon=":material/edit:", key="fa_mo_" + m["id"], width="stretch"):
                    _fa_dialogo(pid, m["id"])

        if visibili:
            st.caption("📖 Controindicazioni e avvertenze sono nel foglio illustrativo ufficiale: leggilo o chiedi al "
                       "medico o al farmacista. L'app non valuta se un medicinale va bene per una malattia.")

    with tab_ter:
        _fa_tab_terapie(f, pid, nomi, oggi_)
    with tab_vis:
        _fa_tab_visite(f, pid, nomi, oggi_)
    with tab_vac:
        _fa_tab_vaccini(f, pid, nomi, oggi_)
    _fa_esporta(f, pid, nomi)

    st.caption("ℹ️ Questa sezione serve solo a organizzare e ricordare i dati che inserisci tu. Non dà consigli medici e non "
               "cambia le terapie: per dosi e cure segui sempre le indicazioni del medico o del farmacista.")


# =====================================================================
# FASE 2 - TERAPIE, CALENDARIO SETTIMANALE E STORICO DELLE ASSUNZIONI
# =====================================================================
GIORNI_SETT = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
ORARI_TER = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 15, 30, 45)]
STATI_TER = {"attiva": "Attiva", "sospesa": "Sospesa", "terminata": "Terminata"}


def _fa_nome_med(f, med_id, fallback=""):
    m = next((x for x in f.get("medicinali", []) if x["id"] == med_id), None)
    return m.get("nome", fallback) if m else fallback


def _fa_dosi_giorno(f, pid, d):
    """Assunzioni previste per un profilo in un giorno: lista di (orario, terapia), in ordine di orario."""
    risultato = []
    for t_ in f.get("terapie", []):
        if t_.get("profilo", "p0") != pid or d.weekday() not in t_.get("giorni", []):
            continue
        ini, fin = _fa_data(t_.get("inizio")), _fa_data(t_.get("fine"))
        if (ini and d < ini) or (fin and d > fin):
            continue
        if t_.get("stato") == "sospesa":
            dal = _fa_data(t_.get("stato_dal"))
            if dal is None or d >= dal:
                continue
        for ora in t_.get("orari", []):
            risultato.append((ora, t_))
    risultato.sort(key=lambda x: x[0])
    return risultato


def _fa_chiave(t_, d, ora):
    return f"{t_['id']}|{d.isoformat()}|{ora}"


def _fa_segna(f, pid, t_, d, ora, presa):
    k = _fa_chiave(t_, d, ora)
    nome = _fa_nome_med(f, t_.get("med"), t_.get("nome_med", ""))

    def _m(f):
        reg = f.setdefault("registro", {})
        if presa:
            reg[k] = {"t": t_["id"], "p": pid, "d": d.isoformat(), "o": ora, "nome": nome,
                      "q": t_.get("quantita", ""), "quando": adesso().isoformat(timespec="minutes")}
        else:
            reg.pop(k, None)
    _fa_salva(_m, "Farmacia: assunzione")


def _fa_riga_dose(f, pid, d, ora, t_, ora_adesso, prefisso):
    k = _fa_chiave(t_, d, ora)
    presa = k in f.get("registro", {})
    momento = datetime.fromisoformat(f"{d.isoformat()}T{ora}")
    if presa:
        icona = "✅"
    elif momento < ora_adesso:
        icona = "⚠️" if d == ora_adesso.date() else "❌"
    else:
        icona = "⏳"
    nome = _fa_nome_med(f, t_.get("med"), t_.get("nome_med", ""))
    q = t_.get("quantita", "")
    c1, c2 = st.columns([3, 2], gap="small")
    c1.markdown(f"{icona} **{ora}** · 💊 {html.escape(nome)}" + (f" · {html.escape(q)}" if q else ""))
    if d <= ora_adesso.date():
        if c2.button("↩ Annulla" if presa else "✔ Presa", key=f"fa_d_{prefisso}_{k}", width="stretch"):
            try:
                _fa_segna(f, pid, t_, d, ora, not presa)
            except Exception as e:
                st.error(f"Non sono riuscito a salvare: {e}")
                return
            st.rerun()


@st.dialog("Programma di terapia")
def _fa_dialogo_terapia(pid, ter_id=None):
    f = _fa_dati()
    meds = [m for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid]
    ter = next((x for x in f.get("terapie", []) if x["id"] == ter_id), {}) if ter_id else {}
    if not meds and not ter:
        st.info("Prima aggiungi almeno un medicinale a questo profilo (scheda 💊 Medicinali).")
        return
    ids = [m["id"] for m in meds]
    etich = {m["id"]: m["nome"] + (f" {m['dosaggio']}" if m.get("dosaggio") else "") for m in meds}
    if ter.get("med") and ter["med"] not in ids:
        ids.insert(0, ter["med"])
        etich[ter["med"]] = ter.get("nome_med", "(medicinale eliminato)")
    with st.form("fa_form_ter"):
        med = st.selectbox("Medicinale", ids, format_func=lambda i: etich[i], index=_fa_idx(ids, ter.get("med")))
        quantita = st.text_input("Quantità per ogni assunzione, come scritto nella prescrizione",
                                 value=ter.get("quantita", ""), placeholder="es. 1 compressa")
        giorni = st.multiselect("Giorni della settimana", list(range(7)), default=ter.get("giorni", list(range(7))),
                                format_func=lambda i: GIORNI_SETT[i])
        orari = st.multiselect("Orari (puoi sceglierne più di uno)", ORARI_TER,
                               default=[o for o in ter.get("orari", []) if o in ORARI_TER])
        c1, c2 = st.columns(2)
        inizio = c1.date_input("Inizio", value=_fa_data(ter.get("inizio")) or oggi(), format="DD/MM/YYYY",
                               min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
        fine = c2.date_input("Fine (facoltativa)", value=_fa_data(ter.get("fine")), format="DD/MM/YYYY",
                             min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
        note = st.text_area("Istruzioni o note della prescrizione", value=ter.get("note", ""))
        stato = st.selectbox("Stato", list(STATI_TER), format_func=lambda k: STATI_TER[k],
                             index=_fa_idx(list(STATI_TER), ter.get("stato", "attiva")))
        inviato = st.form_submit_button("Salva", type="primary")
    if inviato:
        if not giorni or not orari:
            st.error("Scegli almeno un giorno e almeno un orario.")
            return
        if fine and fine < inizio:
            st.error("La data di fine non può essere prima di quella di inizio.")
            return
        rec = {"profilo": pid, "med": med, "nome_med": etich[med], "quantita": quantita.strip(),
               "giorni": sorted(giorni), "orari": sorted(orari), "inizio": inizio.isoformat(),
               "fine": fine.isoformat() if fine else None, "note": note.strip(), "stato": stato}
        if stato != ter.get("stato", "attiva"):          # sospesa o terminata da oggi: lo storico resta
            rec["stato_dal"] = oggi().isoformat()
            if stato == "terminata" and (not fine or fine > oggi()):
                rec["fine"] = oggi().isoformat()
        else:
            rec["stato_dal"] = ter.get("stato_dal")

        def _scrivi(f):
            f.setdefault("terapie", [])
            if ter_id:
                for x in f["terapie"]:
                    if x["id"] == ter_id:
                        x.update(rec)
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                f["terapie"].append(rec)
        try:
            _fa_salva(_scrivi, "Farmacia: terapia")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Programma salvato."
        st.rerun()


@st.dialog("Elimina programma")
def _fa_dialogo_elimina_terapia(ter_id, nome):
    st.write(f"Vuoi eliminare il programma di **{nome}**?")
    st.caption("Le assunzioni già registrate restano nello storico. Se vuoi solo fermarlo, "
               "è meglio mettere lo stato «Sospesa» o «Terminata».")
    c1, c2 = st.columns(2)
    if c1.button("Sì, elimina", type="primary", width="stretch"):
        try:
            _fa_salva(lambda f: f.__setitem__("terapie", [x for x in f.get("terapie", []) if x["id"] != ter_id]),
                      "Farmacia: terapia eliminata")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "🗑️ Programma eliminato."
        st.rerun()
    if c2.button("Annulla", width="stretch"):
        st.rerun()


def _fa_tab_terapie(f, pid, nomi, oggi_):
    ora_adesso = adesso()
    st.subheader("📍 Oggi")
    dosi = _fa_dosi_giorno(f, pid, oggi_)
    in_ritardo = [1 for ora, t_ in dosi
                  if _fa_chiave(t_, oggi_, ora) not in f.get("registro", {})
                  and datetime.fromisoformat(f"{oggi_.isoformat()}T{ora}") < ora_adesso]
    if in_ritardo:
        n_r = len(in_ritardo)
        st.warning(f"⏰ Per {nomi[pid]} c'è {n_r} assunzione da registrare." if n_r == 1
                   else f"⏰ Per {nomi[pid]} ci sono {n_r} assunzioni da registrare.")
        st.caption("Tocca «✔ Presa» quando l'hai fatta.")
    if not dosi:
        st.caption("Nessuna assunzione programmata per oggi.")
    for ora, t_ in dosi:
        _fa_riga_dose(f, pid, oggi_, ora, t_, ora_adesso, "oggi")
    if st.button("➕ Nuovo programma di terapia", type="primary", key="fa_nuova_ter", width="stretch"):
        _fa_dialogo_terapia(pid)

    st.subheader("📅 Settimana")
    if "fa_sett" not in st.session_state:
        st.session_state["fa_sett"] = 0
    n1, n2, n3 = st.columns(3, gap="small")
    if n1.button("◀ Prima", key="fa_sett_prec", width="stretch"):
        st.session_state["fa_sett"] -= 1
        st.rerun()
    if n2.button("Oggi", key="fa_sett_oggi", width="stretch"):
        st.session_state["fa_sett"] = 0
        st.rerun()
    if n3.button("Dopo ▶", key="fa_sett_succ", width="stretch"):
        st.session_state["fa_sett"] += 1
        st.rerun()
    lunedi = oggi_ - timedelta(days=oggi_.weekday()) + timedelta(weeks=st.session_state["fa_sett"])
    st.caption(f"Settimana dal {lunedi.strftime('%d/%m/%Y')} al {(lunedi + timedelta(days=6)).strftime('%d/%m/%Y')}")
    for i in range(7):
        d = lunedi + timedelta(days=i)
        dosi_d = _fa_dosi_giorno(f, pid, d)
        etichetta = f"{'📍 ' if d == oggi_ else ''}{GIORNI_SETT[i]} {d.strftime('%d/%m')}" + (f" · {len(dosi_d)}" if dosi_d else "")
        with st.expander(etichetta, expanded=(d == oggi_)):
            if not dosi_d:
                st.caption("Nessuna assunzione.")
            for ora, t_ in dosi_d:
                _fa_riga_dose(f, pid, d, ora, t_, ora_adesso, f"s{i}")

    st.subheader("📋 Programmi di terapia")
    programmi = [t_ for t_ in f.get("terapie", []) if t_.get("profilo", "p0") == pid]
    if not programmi:
        st.caption("Nessun programma inserito.")
    for t_ in programmi:
        nome = _fa_nome_med(f, t_.get("med"), t_.get("nome_med", ""))
        giorni = ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []))
        periodo = f"dal {data_it(t_['inizio'])}" + (f" al {data_it(t_['fine'])}" if t_.get("fine") else "")
        with st.container(border=True):
            st.markdown(f"💊 **{html.escape(nome)}** · {STATI_TER.get(t_.get('stato', 'attiva'))}  \n"
                        f"{html.escape(t_.get('quantita', ''))} · {', '.join(t_.get('orari', []))}  \n"
                        f"{giorni} · {periodo}"
                        + (f"  \n📝 {html.escape(t_['note'])}" if t_.get("note") else ""))
            b1, b2 = st.columns(2, gap="small")
            if b1.button("Elimina", icon=":material/delete:", key="fa_elt_" + t_["id"], width="stretch"):
                _fa_dialogo_elimina_terapia(t_["id"], nome)
            if b2.button("Modifica", icon=":material/edit:", key="fa_mot_" + t_["id"], width="stretch"):
                _fa_dialogo_terapia(pid, t_["id"])

    with st.expander("📜 Storico delle assunzioni registrate"):
        reg = [r for r in f.get("registro", {}).values() if r.get("p", "p0") == pid]
        reg.sort(key=lambda r: (r["d"], r["o"]), reverse=True)
        if not reg:
            st.caption("Ancora nessuna assunzione registrata.")
        else:
            st.dataframe(pd.DataFrame([{"Data": data_it(r["d"]), "Ora": r["o"], "Medicinale": r.get("nome", ""),
                                        "Quantità": r.get("q", ""),
                                        "Registrata il": r.get("quando", "").replace("T", " ")} for r in reg[:200]]),
                         hide_index=True)
    st.caption("🔔 I promemoria per ora si vedono dentro l'app (avviso «da registrare»). Le notifiche sul telefono "
               "arriveranno in una fase successiva.")


# =====================================================================
# FASE 3 - VISITE, ESAMI, REFERTI E DOCUMENTO VACCINALE
# =====================================================================
import json as _json

CATEGORIE_VISITE = [
    "Medicina generale", "Cardiologia", "Dermatologia", "Oculistica", "Otorinolaringoiatria",
    "Odontoiatria e ortodonzia", "Ortopedia e traumatologia", "Neurologia", "Endocrinologia e diabetologia",
    "Gastroenterologia", "Urologia e nefrologia", "Ginecologia e ostetricia", "Pneumologia", "Oncologia",
    "Ematologia", "Reumatologia", "Allergologia e immunologia", "Psichiatria e psicologia",
    "Fisiatria e fisioterapia", "Chirurgia e visite preoperatorie", "Esami del sangue e analisi",
    "Radiologia, ecografie, TAC e risonanze", "Elettrocardiogramma e esami cardiologici", "Endoscopie",
    "Screening e controlli preventivi", "Vaccinazioni", "Pronto soccorso e ricoveri", "Certificazioni mediche",
    "Altro"]
TIPI_FILE = ["pdf", "jpg", "jpeg", "png", "webp"]
MAX_PDF = 8 * 1024 * 1024
MAX_IMMAGINE = int(2.5 * 1024 * 1024)


def _fa_percorso_doc(did):
    return f"documenti/{st.session_state['sess']['uid']}/{did}.json"


def _fa_prepara_file(up):
    """Controlla un file caricato. Le foto piccole restano originali; quelle molto grandi vengono ridotte."""
    nome, dati = up.name, up.getvalue()
    ext = nome.lower().rsplit(".", 1)[-1] if "." in nome else ""
    if ext == "pdf":
        if len(dati) > MAX_PDF:
            raise ValueError(f"«{nome}» è troppo grande (massimo 8 MB per i PDF).")
        return {"nome": nome, "mime": "application/pdf"}, dati
    mime = {"png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    if len(dati) > MAX_IMMAGINE:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
        img.thumbnail((2600, 2600))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88, optimize=True)
        dati, mime = buf.getvalue(), "image/jpeg"
    return {"nome": nome, "mime": mime}, dati


def _fa_salva_files(caricati):
    """Salva i file nell'archivio (uno per documento) e restituisce i riferimenti da mettere nella scheda."""
    pronti = [_fa_prepara_file(u) for u in caricati]          # se uno non va bene, non si salva nulla
    riferimenti = []
    with st.spinner("Salvo i documenti…"):
        for meta, dati in pronti:
            did = uuid.uuid4().hex[:12]
            corpo = {"nome": meta["nome"], "mime": meta["mime"], "b64": base64.b64encode(dati).decode()}
            salva_file(_fa_percorso_doc(did), lambda d, c=corpo: d.update(c), "Farmacia: documento")
            riferimenti.append({"id": did, "nome": meta["nome"], "mime": meta["mime"]})
    return riferimenti


def _fa_cancella_files(ids):
    for did in ids:
        try:
            crea_archivio().elimina(_fa_percorso_doc(did), "Farmacia: documento eliminato")
        except Exception:
            pass
    carica_dati.clear()


def _fa_elimina_profilo(f, pid):
    ids = [a["id"] for v in f.get("visite", []) if v.get("profilo", "p0") == pid for a in v.get("allegati", [])]
    ids += [a["id"] for a in (f.get("vaccini_doc") or {}).get(pid, [])]

    def _m(f):
        f["profili"] = [p for p in f["profili"] if p["id"] != pid]
        for chiave in ("medicinali", "terapie", "visite", "vaccinazioni"):
            f[chiave] = [x for x in f.get(chiave, []) if x.get("profilo", "p0") != pid]
        f["registro"] = {k: r for k, r in (f.get("registro") or {}).items() if r.get("p", "p0") != pid}
        (f.get("vaccini_doc") or {}).pop(pid, None)
        (f.get("allergie") or {}).pop(pid, None)
    _fa_salva(_m, "Farmacia: profilo eliminato")
    _fa_cancella_files(ids)


def _fa_rimuovi_allegato(tipo, proprietario, did):
    def _m(f):
        if tipo == "visita":
            for v in f.get("visite", []):
                if v["id"] == proprietario:
                    v["allegati"] = [a for a in v.get("allegati", []) if a["id"] != did]
        else:
            vd = f.setdefault("vaccini_doc", {})
            vd[proprietario] = [a for a in vd.get(proprietario, []) if a["id"] != did]
    _fa_salva(_m, "Farmacia: allegato eliminato")
    _fa_cancella_files([did])


@st.dialog("Documento", width="large")
def _fa_dialogo_doc(allegato, tipo, proprietario):
    d = carica_dati(crea_archivio(), _fa_percorso_doc(allegato["id"]))
    if not d.get("b64"):
        st.error("Non trovo questo documento.")
        return
    dati = base64.b64decode(d["b64"])
    st.caption(allegato["nome"])
    if d.get("mime", "").startswith("image/"):
        st.image(dati)
    else:
        st.info("PDF: scaricalo per aprirlo.")
    st.download_button("⬇ Scarica / apri il file", dati, file_name=allegato["nome"],
                       mime=d.get("mime", "application/octet-stream"), width="stretch")
    conferma = st.checkbox("Voglio eliminare questo documento", key="fa_del_doc_" + allegato["id"])
    if st.button("🗑️ Elimina il documento", disabled=not conferma, key="fa_btn_del_doc_" + allegato["id"]):
        try:
            _fa_rimuovi_allegato(tipo, proprietario, allegato["id"])
        except Exception as e:
            st.error(f"Non sono riuscito a eliminarlo: {e}")
            return
        st.session_state["fa_msg"] = "🗑️ Documento eliminato."
        st.rerun()


def _fa_bottoni_allegati(allegati, tipo, proprietario):
    for a in allegati:
        icona = "📄" if a.get("mime") == "application/pdf" else "🖼️"
        etichetta = a["nome"] if len(a["nome"]) <= 30 else a["nome"][:27] + "…"
        if st.button(f"{icona} {etichetta}", key=f"fa_all_{tipo}_{a['id']}", width="stretch"):
            _fa_dialogo_doc(a, tipo, proprietario)


@st.dialog("Visita o esame")
def _fa_dialogo_visita(pid, vis_id=None):
    f = _fa_dati()
    v = next((x for x in f.get("visite", []) if x["id"] == vis_id), {}) if vis_id else {}
    categorie = CATEGORIE_VISITE[:-1] + (f.get("categorie_extra") or []) + [CATEGORIE_VISITE[-1]]
    with st.form("fa_form_vis"):
        c1, c2 = st.columns(2)
        data_v = c1.date_input("Data", value=_fa_data(v.get("data")) or oggi(), format="DD/MM/YYYY",
                               min_value=date(1950, 1, 1), max_value=date(2100, 12, 31))
        ora_v = c2.text_input("Orario (facoltativo)", value=v.get("ora", ""), placeholder="es. 09:30")
        cat = st.selectbox("Tipo di visita o esame", categorie, index=_fa_idx(categorie, v.get("categoria")))
        nuova = st.text_input("Oppure crea una nuova categoria (lascia vuoto per usare quella scelta sopra)")
        medico = st.text_input("Medico, specialista o struttura", value=v.get("medico", ""))
        motivo = st.text_input("Motivo della visita o dell'esame", value=v.get("motivo", ""))
        controlli = st.text_area("Indicazioni per i controlli successivi", value=v.get("controlli", ""))
        prossimo = st.date_input("Data del prossimo appuntamento (facoltativa)", value=_fa_data(v.get("prossimo")),
                                 format="DD/MM/YYYY", min_value=date(1950, 1, 1), max_value=date(2100, 12, 31))
        note = st.text_area("Note personali", value=v.get("note", ""))
        if v.get("allegati"):
            st.caption(f"Documenti già allegati: {len(v['allegati'])} (si aprono ed eliminano dalla scheda).")
        nuovi = st.file_uploader("Allega referti: scatta una foto o scegli PDF e immagini", type=TIPI_FILE,
                                 accept_multiple_files=True)
        inviato = st.form_submit_button("Salva", type="primary")
    if inviato:
        categoria = nuova.strip() or cat
        try:
            riferimenti = _fa_salva_files(nuovi) if nuovi else []
        except ValueError as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(f"Non sono riuscito a salvare i documenti: {e}")
            return
        rec = {"profilo": pid, "data": data_v.isoformat(), "ora": ora_v.strip(), "categoria": categoria,
               "medico": medico.strip(), "motivo": motivo.strip(), "controlli": controlli.strip(),
               "prossimo": prossimo.isoformat() if prossimo else None, "note": note.strip()}

        def _scrivi(f):
            f.setdefault("visite", [])
            if nuova.strip() and categoria not in CATEGORIE_VISITE + (f.get("categorie_extra") or []):
                f.setdefault("categorie_extra", []).append(categoria)
            if vis_id:
                for x in f["visite"]:
                    if x["id"] == vis_id:
                        x.update(rec)
                        x["allegati"] = (x.get("allegati") or []) + riferimenti
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                rec["allegati"] = riferimenti
                f["visite"].append(rec)
        try:
            _fa_salva(_scrivi, "Farmacia: visita")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Visita salvata."
        st.rerun()


@st.dialog("Vaccinazione")
def _fa_dialogo_vaccinazione(pid, vac_id=None):
    f = _fa_dati()
    v = next((x for x in f.get("vaccinazioni", []) if x["id"] == vac_id), {}) if vac_id else {}
    with st.form("fa_form_vac"):
        nome = st.text_input("Vaccino o tipologia *", value=v.get("nome", ""), placeholder="es. Antitetanica")
        data_v = st.date_input("Data della vaccinazione", value=_fa_data(v.get("data")) or oggi(),
                               format="DD/MM/YYYY", min_value=date(1930, 1, 1), max_value=date(2100, 12, 31))
        dose = st.text_input("Dose o richiamo (facoltativo)", value=v.get("dose", ""), placeholder="es. 2ª dose")
        richiamo = st.date_input("Data del prossimo richiamo (facoltativa)", value=_fa_data(v.get("richiamo")),
                                 format="DD/MM/YYYY", min_value=date(1930, 1, 1), max_value=date(2100, 12, 31))
        note = st.text_area("Note (lotto, struttura, ecc.)", value=v.get("note", ""))
        inviato = st.form_submit_button("Salva", type="primary")
    if inviato:
        if not nome.strip():
            st.error("Scrivi il nome del vaccino.")
            return
        rec = {"profilo": pid, "nome": nome.strip(), "data": data_v.isoformat(), "dose": dose.strip(),
               "richiamo": richiamo.isoformat() if richiamo else None, "note": note.strip()}

        def _scrivi(f):
            f.setdefault("vaccinazioni", [])
            if vac_id:
                for x in f["vaccinazioni"]:
                    if x["id"] == vac_id:
                        x.update(rec)
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                f["vaccinazioni"].append(rec)
        try:
            _fa_salva(_scrivi, "Farmacia: vaccinazione")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Vaccinazione salvata."
        st.rerun()


@st.dialog("Conferma eliminazione")
def _fa_dialogo_elimina_voce(lista, rec_id, etichetta):
    st.write(f"Vuoi eliminare **{etichetta}**?")
    if lista == "visite":
        st.caption("Verranno eliminati anche i documenti allegati a questa visita.")
    c1, c2 = st.columns(2)
    if c1.button("Sì, elimina", type="primary", width="stretch"):
        f = _fa_dati()
        rec = next((x for x in f.get(lista, []) if x["id"] == rec_id), {})
        ids = [a["id"] for a in rec.get("allegati", [])]
        try:
            _fa_salva(lambda f: f.__setitem__(lista, [x for x in f.get(lista, []) if x["id"] != rec_id]),
                      "Farmacia: eliminato")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        _fa_cancella_files(ids)
        st.session_state["fa_msg"] = "🗑️ Eliminato."
        st.rerun()
    if c2.button("Annulla", width="stretch"):
        st.rerun()


def _fa_tab_visite(f, pid, nomi, oggi_):
    visite = [v for v in f.get("visite", []) if v.get("profilo", "p0") == pid]
    prossimi = sorted([v for v in visite if v.get("prossimo") and v["prossimo"] >= oggi_.isoformat()],
                      key=lambda v: v["prossimo"])[:5]
    if prossimi:
        st.subheader("📅 Prossimi appuntamenti")
        for v in prossimi:
            st.markdown(f"• **{data_it(v['prossimo'])}** · {html.escape(v.get('categoria', ''))}"
                        + (f" · {html.escape(v['medico'])}" if v.get("medico") else ""))
    if st.button("➕ Aggiungi visita o esame", type="primary", key="fa_nuova_vis", width="stretch"):
        _fa_dialogo_visita(pid)
    c1, c2 = st.columns([3, 2])
    cerca = c1.text_input("Cerca", placeholder="medico, motivo, note…", label_visibility="collapsed", key="fa_cerca_vis")
    presenti = sorted({v.get("categoria", "") for v in visite if v.get("categoria")})
    cat = c2.selectbox("Tipo", ["Tutti i tipi"] + presenti, label_visibility="collapsed", key="fa_cat_vis")
    visibili = []
    for v in sorted(visite, key=lambda v: (v.get("data", ""), v.get("ora", "")), reverse=True):
        testo = " ".join(str(v.get(k, "")) for k in ("categoria", "medico", "motivo", "note", "controlli")).lower()
        if cerca and cerca.lower() not in testo:
            continue
        if cat != "Tutti i tipi" and v.get("categoria") != cat:
            continue
        visibili.append(v)
    if not visite:
        st.info(f"Nessuna visita o esame per {nomi[pid]}. Tocca «Aggiungi visita o esame».")
    elif not visibili:
        st.info("Nessun risultato.")
    e = html.escape
    for v in visibili:
        righe = f"<div class='nome'>🩺 {e(v.get('categoria', ''))}</div>"
        righe += f"<div class='riga'>📅 {data_it(v['data'])}" + (f" · {e(v['ora'])}" if v.get("ora") else "") + "</div>"
        for icona, chiave in (("👨‍⚕️", "medico"), ("❓", "motivo"), ("🔁", "controlli"), ("📝", "note")):
            if v.get(chiave):
                righe += f"<div class='riga'>{icona} {e(v[chiave])}</div>"
        if v.get("prossimo"):
            righe += f"<span class='scad'>📅 Prossimo: {data_it(v['prossimo'])}</span>"
        with st.container(border=True):
            st.markdown(f"<div class='fa-med' style='--c:#00897b'>{righe}</div>", unsafe_allow_html=True)
            _fa_bottoni_allegati(v.get("allegati", []), "visita", v["id"])
            b1, b2 = st.columns(2, gap="small")
            if b1.button("Elimina", icon=":material/delete:", key="fa_elv_" + v["id"], width="stretch"):
                _fa_dialogo_elimina_voce("visite", v["id"], f"{v.get('categoria', '')} del {data_it(v['data'])}")
            if b2.button("Modifica", icon=":material/edit:", key="fa_mov_" + v["id"], width="stretch"):
                _fa_dialogo_visita(pid, v["id"])


def _fa_tab_vaccini(f, pid, nomi, oggi_):
    st.subheader(f"📄 Documento vaccinale di {nomi[pid]}")
    pagine = (f.get("vaccini_doc") or {}).get(pid, [])
    with st.form("fa_form_vacdoc_" + pid, clear_on_submit=True):
        nuovi = st.file_uploader("Fotografa il documento o scegli le pagine (foto o PDF)", type=TIPI_FILE,
                                 accept_multiple_files=True, key="fa_up_vac_" + pid)
        invio = st.form_submit_button("Salva le pagine")
    if invio and nuovi:
        try:
            riferimenti = _fa_salva_files(nuovi)
            _fa_salva(lambda f: f.setdefault("vaccini_doc", {}).setdefault(pid, []).extend(riferimenti),
                      "Farmacia: documento vaccinale")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
        else:
            st.session_state["fa_msg"] = f"✅ {len(riferimenti)} pagina/e salvata/e."
            st.rerun()
    if pagine:
        st.caption("Tocca una pagina per aprirla e ingrandirla. Le foto piccole restano come le hai scattate.")
    for i, a in enumerate(pagine, 1):
        icona = "📄" if a.get("mime") == "application/pdf" else "🖼️"
        if st.button(f"{icona} Pagina {i} · {a['nome'][:26]}", key=f"fa_all_vacc_{a['id']}", width="stretch"):
            _fa_dialogo_doc(a, "vaccino", pid)

    st.subheader("💉 Vaccinazioni registrate")
    if st.button("➕ Aggiungi vaccinazione", type="primary", key="fa_nuova_vac", width="stretch"):
        _fa_dialogo_vaccinazione(pid)
    vacc = sorted([v for v in f.get("vaccinazioni", []) if v.get("profilo", "p0") == pid],
                  key=lambda v: v.get("data", ""), reverse=True)
    if not vacc:
        st.caption("Nessuna vaccinazione registrata.")
    e = html.escape
    for v in vacc:
        righe = f"<div class='nome'>💉 {e(v['nome'])}</div><div class='riga'>📅 {data_it(v['data'])}"
        righe += (f" · {e(v['dose'])}" if v.get("dose") else "") + "</div>"
        colore = "#00897b"
        if v.get("richiamo"):
            stato, g = stato_scadenza(v["richiamo"], oggi_)
            colore = COLORI[stato]
            testo = (f"Richiamo in ritardo di {abs(g)} giorni" if g < 0 else "Richiamo oggi" if g == 0
                     else f"Richiamo tra {g} giorni")
            righe += f"<span class='scad'>{ICONE[stato]} {testo} · {data_it(v['richiamo'])}</span>"
        if v.get("note"):
            righe += f"<div class='riga'>📝 {e(v['note'])}</div>"
        with st.container(border=True):
            st.markdown(f"<div class='fa-med' style='--c:{colore}'>{righe}</div>", unsafe_allow_html=True)
            b1, b2 = st.columns(2, gap="small")
            if b1.button("Elimina", icon=":material/delete:", key="fa_elw_" + v["id"], width="stretch"):
                _fa_dialogo_elimina_voce("vaccinazioni", v["id"], v["nome"])
            if b2.button("Modifica", icon=":material/edit:", key="fa_mow_" + v["id"], width="stretch"):
                _fa_dialogo_vaccinazione(pid, v["id"])


def _fa_esporta(f, pid, nomi):
    with st.expander("📦 Esporta i dati di questo profilo"):
        chiavi = ("medicinali", "terapie", "visite", "vaccinazioni")
        dati = {"profilo": nomi[pid]}
        for k in chiavi:
            dati[k] = [x for x in f.get(k, []) if x.get("profilo", "p0") == pid]
        dati["allergie_dichiarate"] = (f.get("allergie") or {}).get(pid, [])
        dati["registro_assunzioni"] = [r for r in (f.get("registro") or {}).values() if r.get("p", "p0") == pid]
        st.caption("Scarica un file con medicinali, terapie, visite e vaccinazioni (l'elenco, non le foto). "
                   "I documenti si scaricano uno per uno dalla loro scheda.")
        st.download_button("⬇ Scarica i dati (JSON)", _json.dumps(dati, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"farmacia_{nomi[pid].replace(' ', '_')}.json", mime="application/json")


# =====================================================================
# ALLERGIE DICHIARATE DALL'UTENTE (confronto con nome, marca e principio attivo)
# =====================================================================
def _fa_termini_allergie(f, pid):
    return [x.strip().lower() for x in (f.get("allergie") or {}).get(pid, []) if len(x.strip()) >= 3]


def _fa_conflitti(f, pid, m):
    testo = " ".join(str(m.get(k, "")) for k in ("nome", "marca", "principio")).lower()
    return [t_ for t_ in _fa_termini_allergie(f, pid) if t_ in testo]


def _fa_blocco_allergie(f, pid, nomi, medicinali):
    termini = (f.get("allergie") or {}).get(pid, [])
    nomi_conflitto = [m.get("nome", "") for m in medicinali if _fa_conflitti(f, pid, m)]
    if nomi_conflitto:
        st.error(f"🚨 Attenzione: per {nomi[pid]} questi medicinali contengono sostanze segnate come allergia: "
                 + ", ".join(nomi_conflitto) + ".")
    with st.expander(f"⚠️ Allergie e intolleranze di {nomi[pid]}" + (f" ({len(termini)})" if termini else "")):
        with st.form("fa_form_allergie_" + pid):
            testo = st.text_area("Scrivi le sostanze o i principi attivi, separati da virgola",
                                 value=", ".join(termini), placeholder="es. amoxicillina, ibuprofene, lattosio")
            ok = st.form_submit_button("Salva")
        st.caption("L'app confronta solo le parole che scrivi con nome, marca e principio attivo dei medicinali. "
                   "Se c'è un'allergia a una famiglia di farmaci, scrivi anche i nomi dei singoli principi attivi. "
                   "Non sostituisce il parere del medico o del farmacista.")
    if ok:
        lista = [x.strip() for x in re.split(r"[,;\n]", testo) if x.strip()]
        try:
            _fa_salva(lambda f: f.setdefault("allergie", {}).__setitem__(pid, lista), "Farmacia: allergie")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
        else:
            st.session_state["fa_msg"] = "✅ Allergie salvate."
            st.rerun()


# =====================================================================
# TROVA UNA FARMACIA APERTA (dati di OpenStreetMap: mappa aperta, orari inseriti da volontari)
# =====================================================================
import math as _math

_GG = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_RE_ORA = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")
_SERVER_OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def _fa_oh_parse(oh):
    """Legge gli orari nel formato di OpenStreetMap. Ritorna {0..6: [(inizio, fine)]} in minuti, oppure None
    se non sono sicuro di averli capiti (meglio dire «non verificabile» che sbagliare)."""
    oh = (oh or "").strip()
    if not oh:
        return None
    if oh == "24/7":
        return {g: [(0, 1440)] for g in range(7)}
    orari = {g: [] for g in range(7)}
    letto = False
    for regola in [r.strip() for r in oh.split(";") if r.strip()]:
        parte_giorni = re.split(r"\d{1,2}:\d{2}|\boff\b|\bclosed\b", regola, maxsplit=1, flags=re.I)[0].strip()
        orari_regola = _RE_ORA.findall(regola)
        spento = bool(re.search(r"\b(off|closed)\b", regola, re.I))
        residuo = _RE_ORA.sub("", regola.replace(parte_giorni, "", 1))
        residuo = re.sub(r"\b(off|closed)\b|[,\s]", "", residuo, flags=re.I)
        if residuo or (not orari_regola and not spento):
            return None
        giorni, speciale = set(), False
        for tok in [x for x in re.split(r"[,\s]+", parte_giorni) if x]:
            m = re.fullmatch(r"(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?", tok)
            if m:
                a = _GG.index(m.group(1))
                b = _GG.index(m.group(2)) if m.group(2) else a
                i = a
                giorni.add(i)
                while i != b:
                    i = (i + 1) % 7
                    giorni.add(i)
            elif tok in ("PH", "SH"):
                speciale = True
            else:
                return None
        if not giorni:
            if speciale:
                continue                      # regola solo per festivi: la ignoro (vedi avvertenza nell'app)
            giorni = set(range(7))
        letto = True
        for g in giorni:
            orari[g] = [] if spento else [(int(h1) * 60 + int(m1), int(h2) * 60 + int(m2))
                                         for h1, m1, h2, m2 in orari_regola]
    return orari if letto else None


def _fa_fmt_minuti(x):
    return f"{x // 60:02d}:{x % 60:02d}"


def _fa_stato_apertura(oh, quando):
    """('aperta' | 'chiusa' | 'ignoto', testo degli orari di oggi). Mai «aperta» se il dato non è chiaro."""
    orari = _fa_oh_parse(oh)
    if orari is None:
        return "ignoto", ""
    g, minuti = quando.weekday(), quando.hour * 60 + quando.minute
    oggi_txt = ", ".join(f"{_fa_fmt_minuti(a)}–{_fa_fmt_minuti(b)}" for a, b in orari[g]) or "chiusa oggi"
    for a, b in orari[g]:
        if a <= minuti < (b if b > a else b + 1440):
            return "aperta", oggi_txt
    for a, b in orari[(g - 1) % 7]:
        if b <= a and minuti < b:             # turno che finisce dopo la mezzanotte
            return "aperta", oggi_txt
    return "chiusa", oggi_txt


def _fa_distanza_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = _math.radians(lat1), _math.radians(lat2)
    dp, dl = p2 - p1, _math.radians(lon2 - lon1)
    a = _math.sin(dp / 2) ** 2 + _math.cos(p1) * _math.cos(p2) * _math.sin(dl / 2) ** 2
    return 2 * r * _math.asin(_math.sqrt(a))


@st.cache_data(ttl=86400, show_spinner=False)
def _fa_geocodifica(testo):
    t_ = testo.strip()
    tentativi = [{"postalcode": t_, "country": "Italy"}, {"q": f"{t_}, Italia"}] if re.fullmatch(r"\d{5}", t_) \
        else [{"q": f"{t_}, Italia"}]
    for par in tentativi:
        r = requests.get("https://nominatim.openstreetmap.org/search", headers=UA, timeout=15,
                         params={**par, "format": "json", "limit": 1, "countrycodes": "it"})
        r.raise_for_status()
        j = r.json()
        if j:
            return float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("display_name", "")
    return None


@st.cache_data(ttl=600, show_spinner=False)
def _fa_overpass(lat, lon, raggio):
    query = f'[out:json][timeout:25];nwr["amenity"="pharmacy"](around:{raggio},{lat},{lon});out center tags 80;'
    ultimo = None
    for url in _SERVER_OVERPASS:
        try:
            r = requests.post(url, data={"data": query}, headers=UA, timeout=30)
            r.raise_for_status()
            return r.json().get("elements", [])
        except Exception as e:
            ultimo = e
    raise ultimo


def _fa_cerca_farmacie(lat, lon, quando):
    elementi = []
    for raggio in (3000, 8000, 15000):
        elementi = _fa_overpass(lat, lon, raggio)
        if elementi:
            break
    righe = []
    for el in elementi:
        tag = el.get("tags") or {}
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is None or lo is None:
            continue
        via = " ".join(x for x in (tag.get("addr:street"), tag.get("addr:housenumber")) if x)
        citta = " ".join(x for x in (tag.get("addr:postcode"), tag.get("addr:city")) if x)
        tel = (tag.get("phone") or tag.get("contact:phone") or "").split(";")[0].strip()
        stato, oggi_txt = _fa_stato_apertura(tag.get("opening_hours"), quando)
        righe.append({"nome": tag.get("name") or tag.get("operator") or "Farmacia",
                      "indirizzo": ", ".join(x for x in (via, citta) if x), "tel": tel,
                      "km": _fa_distanza_km(lat, lon, la, lo), "lat": la, "lon": lo,
                      "stato": stato, "oggi": oggi_txt, "orari": tag.get("opening_hours", "")})
    righe.sort(key=lambda r: r["km"])
    return righe


@st.dialog("Trova una farmacia aperta", width="large")
def _fa_dialogo_farmacie():
    with st.form("fa_form_farm"):
        dove = st.text_input("CAP (consigliato) oppure nome della città o del comune",
                             placeholder="es. 10121 oppure Torino")
        cerca = st.form_submit_button("Cerca", type="primary")
    if cerca:
        if not dove.strip():
            st.error("Scrivi un CAP o il nome di una città.")
        else:
            try:
                with st.spinner("Cerco le farmacie…"):
                    posto = _fa_geocodifica(dove)
                    if not posto:
                        st.session_state["fa_farm"] = {"dove": dove, "errore": "Non trovo questo CAP o questa città. "
                                                       "Controlla come l'hai scritto."}
                    else:
                        quando = adesso()
                        st.session_state["fa_farm"] = {"dove": dove, "luogo": posto[2], "quando": quando.isoformat(),
                                                       "righe": _fa_cerca_farmacie(posto[0], posto[1], quando)}
            except Exception:
                st.session_state["fa_farm"] = {"dove": dove, "errore": "Non riesco a collegarmi al servizio delle "
                                               "mappe in questo momento. Riprova tra poco."}
    ris = st.session_state.get("fa_farm")
    if not ris:
        st.caption("Scrivi il CAP o la città e tocca Cerca.")
    elif ris.get("errore"):
        st.error(ris["errore"])
    else:
        solo_aperte = st.checkbox("Mostra solo quelle che risultano aperte adesso", key="fa_solo_aperte")
        righe = [r for r in ris["righe"] if not solo_aperte or r["stato"] == "aperta"]
        st.caption(f"Ricerca vicino a: {ris['luogo']} · alle {datetime.fromisoformat(ris['quando']).strftime('%H:%M del %d/%m/%Y')}")
        if not ris["righe"]:
            st.warning("Non ho trovato farmacie vicino a questo posto. Prova con un altro CAP o con il nome del comune.")
        elif not righe:
            st.info("Nessuna farmacia risulta aperta adesso secondo gli orari disponibili. Controlla anche quelle "
                    "con orari non verificabili e quelle di turno.")
        e = html.escape
        for r in righe[:12]:
            icona, testo = {"aperta": ("🟢", "Risulta aperta adesso"), "chiusa": ("🔴", "Risulta chiusa adesso"),
                            "ignoto": ("⚪", "Orari non verificabili: chiama prima")}[r["stato"]]
            with st.container(border=True):
                riga = f"**{e(r['nome'])}** · {r['km']:.1f} km<br>"
                riga += f"📍 {e(r['indirizzo'])}<br>" if r["indirizzo"] else ""
                riga += f"{icona} {testo}" + (f" · oggi {e(r['oggi'])}" if r["oggi"] else "")
                if r["tel"]:
                    riga += f"<br>📞 {e(r['tel'])}"
                st.markdown(riga, unsafe_allow_html=True)
                c1, c2 = st.columns(2, gap="small")
                c1.link_button("🧭 Portami lì", f"https://www.google.com/maps/dir/?api=1&destination={r['lat']},{r['lon']}",
                               width="stretch")
                numero = re.sub(r"[^\d+]", "", r["tel"])
                if numero:
                    c2.link_button("📞 Chiama", "tel:" + numero, width="stretch")
        st.link_button("🌙 Cerca le farmacie di turno (notte e festivi)",
                       "https://www.google.com/search?q=" + _up.quote_plus("farmacie di turno " + ris["dove"]),
                       width="stretch")
        st.caption("ℹ️ Posizioni e orari arrivano da OpenStreetMap, una mappa aperta aggiornata da volontari: possono "
                   "essere incompleti o non aggiornati. Nei giorni festivi e di notte gli orari normali non valgono. "
                   "L'app non può sapere quali farmacie sono di turno: usa il pulsante qui sopra o telefona per "
                   "esserne sicuro.")


# =====================================================================
# AVVISI DI SCADENZA: Telegram, email e SMS a scelta (li invia il programma promemoria.py su GitHub)
# =====================================================================
def _fa_blocco_avvisi():
    d = carica_dati(crea_archivio(), st.session_state["percorso"])
    chat, mail, sms = str(d.get("telegram_chat_id") or ""), str(d.get("avviso_email") or ""), str(d.get("avviso_sms") or "")
    canali = d.get("avvisi_canali")
    if canali is None:                                        # chi aveva già inserito solo il Chat ID
        canali = ["telegram"] if chat else []
    attivi = []
    if "telegram" in canali and chat:
        attivi.append(f"📱 Telegram {html.escape(chat)}")
    if "email" in canali and mail:
        attivi.append(f"✉️ Email {html.escape(mail)}")
    if "sms" in canali and sms:
        attivi.append(f"💬 SMS {html.escape(sms)}")
    stile = ("background:rgba(255,255,255,.78);border-radius:16px;padding:8px 14px;margin:6px 0;color:#1b2b2b;"
             "font-weight:700")
    if attivi:
        st.markdown(f"<div style='{stile}'>🔔 Avvisi di scadenza attivi:<br>" + "<br>".join(attivi) + "</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='{stile}'>🔕 Nessun avviso di scadenza attivo</div>", unsafe_allow_html=True)
    with st.expander("🔔 Scegli come ricevere gli avvisi"):
        st.caption("Puoi attivare più canali insieme: gli avvisi arrivano su tutti quelli che spunti.")
        with st.form("fa_form_avvisi"):
            c_tg = st.checkbox("📱 Telegram (gratuito)", value="telegram" in canali)
            v_tg = st.text_input("Chat ID di Telegram (solo numeri)", value=chat, placeholder="es. 123456789")
            c_ml = st.checkbox("✉️ Email (gratuita)", value="email" in canali)
            v_ml = st.text_input("Indirizzo email", value=mail, placeholder="nome@esempio.it")
            c_sm = st.checkbox("💬 SMS (a pagamento)", value="sms" in canali)
            v_sm = st.text_input("Numero di cellulare", value=sms, placeholder="es. 333 1234567")
            privacy = st.checkbox("Nei messaggi non scrivere i nomi dei medicinali (solo quanti sono)",
                                  value=bool(d.get("telegram_privacy")))
            ok = st.form_submit_button("Salva")
        st.caption("Gli avvisi arrivano quando mancano 60, 30, 14, 7 giorni, 1 giorno e il giorno stesso, e ogni lunedì "
                   "per ciò che è già scaduto. Gli SMS sono brevi e non riportano mai i nomi dei medicinali. "
                   "Perché i messaggi partano, l'amministratore deve aver attivato ogni canale su GitHub; "
                   "gli SMS richiedono anche un abbonamento a un servizio di invio, con un costo per messaggio.")
    if ok:
        v_tg, v_ml, v_sm = v_tg.strip(), v_ml.strip(), re.sub(r"[\s.\-]", "", v_sm)
        if v_sm and re.fullmatch(r"3\d{8,9}", v_sm):               # cellulare italiano scritto senza prefisso
            v_sm = "+39" + v_sm
        errore = ""
        if v_tg and not re.fullmatch(r"-?\d{5,15}", v_tg):
            errore = "Il Chat ID di Telegram è un numero (per esempio 123456789)."
        elif v_ml and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", v_ml):
            errore = "L'indirizzo email non sembra corretto."
        elif v_sm and not re.fullmatch(r"\+\d{8,15}", v_sm):
            errore = "Il numero deve essere un cellulare, per esempio 333 1234567 oppure +39 333 1234567."
        elif (c_tg and not v_tg) or (c_ml and not v_ml) or (c_sm and not v_sm):
            errore = "Hai spuntato un canale ma hai lasciato vuoto il suo campo."
        if errore:
            st.error(errore)
            return
        scelti = [n for n, c in (("telegram", c_tg), ("email", c_ml), ("sms", c_sm)) if c]
        try:
            salva(lambda d: d.update({"avvisi_canali": scelti, "telegram_chat_id": v_tg, "avviso_email": v_ml,
                                      "avviso_sms": v_sm, "telegram_privacy": bool(privacy)}), "Avvisi")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Impostazioni degli avvisi salvate." if scelti else "✅ Avvisi disattivati."
        st.rerun()
