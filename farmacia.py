# -*- coding: utf-8 -*-
"""FARMACIA - Fase 1: icona nella Home, profili, medicinali e scadenze.

Questo file si carica PRIMA di parte3.py (vedi app_dispensa.py). Non modifica la dispensa:
i medicinali sono salvati nella voce "farmacia" del file dati di ogni persona.
Serve solo a organizzare i dati inseriti dall'utente: non dà indicazioni mediche.
"""
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
        rec = {"nome": nome.strip(), "marca": marca.strip(), "principio": principio.strip(),
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
        st.session_state["fa_msg"] = "✅ Medicinale salvato."
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
def _fa_card(m, data_oggi):
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
    return (f"<div class='fa-med' style='--c:{COLORI[stato]}'><div class='nome'>💊 {e(m.get('nome', ''))}</div>"
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
        st.success(st.session_state.pop("fa_msg"))

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
            conferma = st.checkbox(f"Elimina il profilo «{nomi[pid]}» e i suoi {n_med} medicinali", key="fa_conf_del")
            if st.button("Elimina profilo", disabled=not conferma):
                def _del(f):
                    f["profili"] = [p for p in f["profili"] if p["id"] != pid]
                    f["medicinali"] = [m for m in f["medicinali"] if m.get("profilo") != pid]
                try:
                    _fa_salva(_del, "Farmacia: profilo eliminato")
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
            st.markdown(_fa_card(m, oggi_), unsafe_allow_html=True)
            b1, b2 = st.columns(2, gap="small")
            if b1.button("Elimina", icon=":material/delete:", key="fa_el_" + m["id"], width="stretch"):
                _fa_dialogo_elimina(m["id"], m.get("nome", ""))
            if b2.button("Modifica", icon=":material/edit:", key="fa_mo_" + m["id"], width="stretch"):
                _fa_dialogo(pid, m["id"])

    st.caption("ℹ️ Questa sezione serve solo a organizzare i dati che inserisci tu. Non dà consigli medici e non "
               "cambia le terapie: per dosi e cure segui sempre le indicazioni del medico o del farmacista.")
