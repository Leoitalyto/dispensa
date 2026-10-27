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
.cm{width:100%;border-collapse:separate;border-spacing:3px;table-layout:fixed}
.cm th{font-size:.72rem;font-weight:800;color:#1b2b2b;padding:2px}
.cm td{height:58px;vertical-align:top;border-radius:10px;padding:3px 4px;font-size:.7rem;color:#1b2b2b;background:rgba(255,255,255,.55)}
.cm td b{font-size:.85rem}.cm td.oggi{outline:3px solid #0f766e}
</style>"""


# ---------------------------------------------------------------- icona nella Home
def _fa_mtime(nome):
    """Data dell'ultima modifica di un file accanto all'app: serve a rileggere le immagini quando vengono sostituite."""
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    try:
        return os.path.getmtime(os.path.join(cartella, nome))
    except OSError:
        return 0


def _fa_icona_uri():
    return _fa_icona_uri_cache(_fa_mtime("farmacia.webp"))


@st.cache_resource
def _fa_icona_uri_cache(_data_file):
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    try:
        with open(os.path.join(cartella, "farmacia.webp"), "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode()
    except OSError:
        return ""


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
def _fa_dialogo(pid, med_id=None):
    """Apre il modulo del medicinale in una pagina intera, non in una finestra: se il telefono sospende il browser
    mentre si scatta la foto, la pagina resta lì e la foto non si perde."""
    st.session_state["fa_modulo_med"] = {"pid": pid, "med_id": med_id}
    st.rerun()


def _fa_modulo_medicinale(pid, med_id=None):
    _fa_assicura_fotocamera()
    if st.button("← Annulla e torna ai medicinali", key="fa_modulo_annulla"):
        st.session_state.pop("fa_modulo_med", None)
        st.rerun()
    st.subheader("✏️ Modifica medicinale" if med_id else "➕ Nuovo medicinale")
    f = _fa_dati()
    profili = _fa_profili(f)
    m = next((x for x in f.get("medicinali", []) if x["id"] == med_id), {}) if med_id else {}
    nomi = {p["id"]: p["nome"] for p in profili}
    # la foto sta in cima, come nella dispensa: fotocamera posteriore, sfondo tolto, righello e ritaglio
    st.markdown("**📷 Foto della confezione** (facoltativa)")
    ck = "fa_" + (med_id or "nuovo")
    try:
        foto_nuova = campo_foto(ck, m.get("foto", ""))
    except NameError:                                  # manca foto_prodotto.py: si va avanti senza foto
        foto_nuova = ""
        st.caption("La foto non è disponibile in questo momento.")
    with st.expander("📎 Se la foto non compare, usa questo campo"):
        alt = st.file_uploader("Scatta o scegli la foto", type=["jpg", "jpeg", "png", "webp"], key="fa_alt_" + ck)
        if alt is not None and not foto_nuova:
            with st.spinner("Sto preparando la foto…"):
                try:
                    foto_nuova = _foto_lavorata(alt.getvalue())          # sfondo tolto e raddrizzata, come nella dispensa
                except Exception:
                    foto_nuova = foto_a_data_uri(alt.getvalue(), 720)
            st.image(base64.b64decode(foto_nuova.split(",", 1)[1]))
            st.caption("✅ Foto pronta: sarà salvata con il medicinale.")
    scelta_arch = _fa_scegli_da_archivio(f, ck)
    with st.form("fa_form_med"):
        togli_foto = st.checkbox("Rimuovi la foto attuale") if m.get("foto") else False
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
        grande, da_cancellare = (None if togli_foto else m.get("foto_grande")), ([m["foto_grande"]["id"]] if togli_foto and m.get("foto_grande") else [])
        if foto_nuova:
            try:
                foto = _fa_miniatura(foto_nuova, 360)
                nuovo_rif = _fa_salva_files([_FaFile("foto.webp", base64.b64decode(foto_nuova.split(",", 1)[1]))])[0]
            except ValueError as e:
                st.error(str(e))
                return
            except Exception:
                st.error("Non riesco a leggere o salvare la foto: prova con un'altra.")
                return
            if grande:
                da_cancellare.append(grande["id"])
            grande = nuovo_rif
        elif scelta_arch:                                   # foto già usata, presa dall'archivio
            foto = scelta_arch["mini"]
            try:
                dd = carica_dati(crea_archivio(), _fa_percorso_doc(scelta_arch["grande"]["id"]))
                if dd.get("b64"):
                    foto = _fa_miniatura("data:image/webp;base64," + dd["b64"], 360)
            except Exception:
                pass
            if grande and grande["id"] != scelta_arch["grande"]["id"]:
                da_cancellare.append(grande["id"])
            grande = scelta_arch["grande"]
        nuova_voce = None
        if foto_nuova:
            try:
                nuova_voce = {"id": uuid.uuid4().hex[:8], "nome": nome.strip(), "mini": _fa_miniatura(foto_nuova, 160),
                              "grande": grande, "data": oggi().isoformat()}
            except Exception:
                nuova_voce = None
        rec = {"foto": foto, "foto_grande": grande, "nome": nome.strip(), "marca": marca.strip(), "principio": principio.strip(),
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
            if nuova_voce:                                   # la foto nuova entra nell'archivio, per le prossime volte
                arch = f.setdefault("archivio_foto", [])
                arch.insert(0, nuova_voce)
                while len(arch) > 60:
                    da_cancellare.append(arch.pop()["grande"]["id"])
        try:
            _fa_salva(_scrivi, "Farmacia: medicinale")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        usati = _fa_ids_foto_usati(_fa_dati())
        _fa_cancella_files([i for i in da_cancellare if i not in usati])
        st.session_state.pop("fa_arch_scelta_" + ck, None)
        trovate = _fa_conflitti(f, per, rec)
        st.session_state["fa_msg"] = ("⚠️ Medicinale salvato, ma attenzione: contiene «" + "», «".join(trovate) +
                                      "», segnato come allergia di questo profilo." if trovate else "✅ Medicinale salvato.")
        st.session_state.pop("fa_modulo_med", None)
        st.rerun()


@st.dialog("Elimina medicinale")
def _fa_cancella_medicinali(ids):
    f = _fa_dati()
    foto = [m["foto_grande"]["id"] for m in f.get("medicinali", []) if m["id"] in ids and m.get("foto_grande")]
    foto += [a["id"] for m in f.get("medicinali", []) if m["id"] in ids for a in m.get("foglio", [])]
    _fa_salva(lambda f: f.__setitem__("medicinali", [x for x in f["medicinali"] if x["id"] not in ids]),
              "Farmacia: eliminato")
    usati = _fa_ids_foto_usati(_fa_dati())                  # le foto dell'archivio restano
    _fa_cancella_files([i for i in foto if i not in usati])


def _fa_dialogo_elimina(med_id, nome):
    _fa_dialogo_elimina_medicinali([med_id], nome)


@st.dialog("Elimina medicinale")
def _fa_dialogo_elimina_medicinali(ids, etichetta):
    st.write(f"Vuoi eliminare **{etichetta}**?")
    c1, c2 = st.columns(2)
    if c1.button("Sì, elimina", type="primary", width="stretch"):
        try:
            _fa_cancella_medicinali(list(ids))
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "🗑️ Medicinale eliminato." if len(ids) == 1 else "🗑️ Medicinali eliminati."
        st.rerun()
    if c2.button("Annulla", width="stretch"):
        st.rerun()


@st.dialog("Foto della confezione", width="large")
def _fa_dialogo_foto(m):
    dati = None
    g = m.get("foto_grande")
    if g:
        d = carica_dati(crea_archivio(), _fa_percorso_doc(g["id"]))
        if d.get("b64"):
            dati = base64.b64decode(d["b64"])
    if dati is None and m.get("foto"):
        dati = base64.b64decode(m["foto"].split(",", 1)[1])
    st.caption(m.get("nome", ""))
    if dati:
        st.image(dati)
    else:
        st.info("Nessuna foto.")


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
        foto = (f"<img src='{e(m['foto'], quote=True)}' alt='' style='float:right;max-width:120px;max-height:120px;"
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
    if st.session_state.get("sezione_home") == "utilita" and "schermata_utilita" in globals():
        schermata_utilita()
        return
    if st.session_state.get("sezione_home") == "documenti":
        schermata_documenti()
        return
    if st.button("← Torna alla dispensa", key="fa_indietro"):
        st.session_state.pop("fa_modulo_med", None)
        st.session_state.pop("fa_modulo_foglio", None)
        st.session_state.pop("fa_modulo_dottore", None)
        st.session_state.pop("fa_modulo_sanitario", None)
        st.session_state.pop("fa_modulo_tessera", None)
        st.session_state["farmacia_aperta"] = False
        st.rerun()
    st.markdown("<div class='fa-hero'><h1>🏥 Farmacia</h1><p>Medicinali e scadenze della tua famiglia</p></div>",
                unsafe_allow_html=True)
    if st.session_state.get("fa_msg"):
        _msg = st.session_state.pop("fa_msg")
        (st.warning if _msg.startswith("⚠️") else st.success)(_msg)
    if st.session_state.get("fa_modulo_med"):
        _fa_modulo_medicinale(**st.session_state["fa_modulo_med"])
        return
    if st.session_state.get("fa_modulo_foglio"):
        _fa_modulo_foglio(**st.session_state["fa_modulo_foglio"])
        return
    if st.session_state.get("fa_modulo_dottore"):
        _fa_modulo_dottore(**st.session_state["fa_modulo_dottore"])
        return
    if st.session_state.get("fa_modulo_sanitario"):
        _fa_modulo_sanitario(**st.session_state["fa_modulo_sanitario"])
        return
    if st.session_state.get("fa_modulo_tessera"):
        _fa_modulo_tessera(**st.session_state["fa_modulo_tessera"])
        return

    _fa_info("farmacia")
    if st.button("🔎 Trova una farmacia aperta", key="fa_trova", type="primary", width="stretch"):
        _fa_dialogo_farmacie()

    _fa_blocco_avvisi()
    _fa_blocco_personale()

    f = _fa_dati()
    profili = _fa_profili(f)
    nomi = {p["id"]: p["nome"] for p in profili}
    if st.session_state.get("fa_profilo") not in nomi:
        st.session_state["fa_profilo"] = profili[0]["id"]
    gruppi_p = {p["id"]: p.get("gruppo") for p in profili}
    pid = st.selectbox("👤 Profilo", list(nomi),
                       format_func=lambda i: nomi[i] + (f" · 🩸 {gruppi_p[i]}" if gruppi_p.get(i) else ""),
                       key="fa_profilo")
    _fa_riga_profilo(profili, pid, nomi[pid], gruppi_p.get(pid))

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
            nuovo_nome = st.text_input(f"Nome del profilo «{nomi[pid]}»", value=nomi[pid])
            opzioni_g = ["Non indicato"] + GRUPPI
            scelto_g = st.radio("🩸 Gruppo sanguigno", opzioni_g, horizontal=True, key="fa_gruppo_" + pid,
                                index=opzioni_g.index(gruppi_p[pid]) if gruppi_p.get(pid) in GRUPPI else 0)
            ok_rin = st.form_submit_button("Salva nome e gruppo")
        if ok_rin:
            def _rin(f):
                for p in f["profili"]:
                    if p["id"] == pid:
                        p["nome"] = nuovo_nome.strip() or p["nome"]
                        p["gruppo"] = None if scelto_g == "Non indicato" else scelto_g
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
        vista = st.radio("Vista", ["Schede", "Tabella"], horizontal=True, key="fa_vista", label_visibility="collapsed")

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
        _fa_elenco_medicinali(f, pid, visibili, vista, oggi_)

        if visibili:
            st.caption("📖 Controindicazioni e avvertenze sono nel foglio illustrativo ufficiale: leggilo o chiedi al "
                       "medico o al farmacista. L'app non valuta se un medicinale va bene per una malattia.")

    with tab_ter:
        _fa_tab_terapie(f, pid, nomi, oggi_)
        _fa_report_medico(f, pid, nomi, oggi_)
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
    reg = f.get("registro", {}).get(k)
    presa = bool(reg)
    momento = datetime.fromisoformat(f"{d.isoformat()}T{ora}")
    if presa:
        try:
            dettaglio = datetime.fromisoformat(reg["quando"]).strftime(" il %d/%m alle %H:%M")
        except Exception:
            dettaglio = ""
        stato, colore = f"✅ PRESA{dettaglio}", "#2e7d32"
    elif momento <= ora_adesso:
        stato, colore = ("⚠️ DA PRENDERE", "#e65100") if d == ora_adesso.date() else ("❌ NON REGISTRATA", "#b71c1c")
    else:
        stato, colore = "⏳ Più tardi", "#555"
    nome = _fa_nome_med(f, t_.get("med"), t_.get("nome_med", ""))
    q = t_.get("quantita", "")
    with st.container(border=True):
        st.markdown(f"<span style='color:{colore};font-weight:800'>{stato}</span><br>"
                    f"<b>{ora}</b> · 💊 <b>{html.escape(nome)}</b>" + (f" · {html.escape(q)}" if q else ""),
                    unsafe_allow_html=True)
        if d <= ora_adesso.date():
            if st.button("↩ Annulla" if presa else "✔ Ho preso la medicina", key=f"fa_d_{prefisso}_{k}",
                         type="secondary" if presa else "primary", width="stretch"):
                try:
                    _fa_segna(f, pid, t_, d, ora, not presa)
                except Exception as e:
                    st.error(f"Non sono riuscito a salvare: {e}")
                    return
                st.session_state["fa_msg"] = (
                    "↩ Registrazione annullata." if presa else
                    f"✅ Registrato: {nome} delle {ora}, segnata alle {adesso().strftime('%H:%M')}. "
                    "Resta nello storico e nel report per il medico.")
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
    st.caption("Di solito le assunzioni già registrate restano nello storico. Se vuoi solo fermarlo, "
               "è meglio mettere lo stato «Sospesa» o «Terminata».")
    anche_storico = st.checkbox("Elimina anche le assunzioni già registrate di questo programma (per esempio se era solo una prova)",
                                key="fa_del_ter_storico_" + ter_id)
    c1, c2 = st.columns(2)
    if c1.button("Sì, elimina", type="primary", width="stretch"):
        def _m(f):
            f["terapie"] = [x for x in f.get("terapie", []) if x["id"] != ter_id]
            if anche_storico:
                f["registro"] = {k: v for k, v in (f.get("registro") or {}).items() if v.get("t") != ter_id}
        try:
            _fa_salva(_m, "Farmacia: terapia eliminata")
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
        st.warning(f"⏰ {nomi[pid]}: {n_r} assunzione DA PRENDERE." if n_r == 1
                   else f"⏰ {nomi[pid]}: {n_r} assunzioni DA PRENDERE.")
        st.caption("Quando l'hai presa tocca «✔ Ho preso la medicina»: viene salvata da sola nello storico e nel report per il medico.")
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

    _fa_calendario_mese(f, pid, oggi_)

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
    ids += [m["foto_grande"]["id"] for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid and m.get("foto_grande")]
    ids += [a["id"] for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid for a in m.get("foglio", [])]
    ids += [a["id"] for x in f.get("documenti", []) if x.get("profilo", "p0") == pid for a in x.get("allegati", [])]

    def _m(f):
        f["profili"] = [p for p in f["profili"] if p["id"] != pid]
        for chiave in ("medicinali", "terapie", "visite", "vaccinazioni", "documenti"):
            f[chiave] = [x for x in f.get(chiave, []) if x.get("profilo", "p0") != pid]
        f["registro"] = {k: r for k, r in (f.get("registro") or {}).items() if r.get("p", "p0") != pid}
        (f.get("vaccini_doc") or {}).pop(pid, None)
        (f.get("allergie") or {}).pop(pid, None)
    _fa_salva(_m, "Farmacia: profilo eliminato")
    usati = _fa_ids_foto_usati(_fa_dati())                  # le foto dell'archivio restano
    _fa_cancella_files([i for i in ids if i not in usati])


def _fa_rimuovi_allegato(tipo, proprietario, did):
    def _m(f):
        if tipo == "visita":
            for v in f.get("visite", []):
                if v["id"] == proprietario:
                    v["allegati"] = [a for a in v.get("allegati", []) if a["id"] != did]
        elif tipo == "documento":
            for v in f.get("documenti", []):
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
    if lista in ("visite", "documenti"):
        st.caption("Verranno eliminati anche i file allegati.")
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
        dati = {"profilo": nomi[pid],
                "dottore": next((p.get("dottore") for p in f.get("profili", []) if p["id"] == pid), None),
                "scheda_sanitaria": next((p.get("sanitario") for p in f.get("profili", []) if p["id"] == pid), None),
                "documenti": [x for x in f.get("documenti", []) if x.get("profilo", "p0") == pid],
                "gruppo_sanguigno": next((p.get("gruppo") for p in f.get("profili", []) if p["id"] == pid), None)}
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
    if attivi and d.get("avvisi_dosi") and ("telegram" in canali or "email" in canali):
        attivi.append("⏰ Promemoria delle assunzioni attivi")
    stile = ("background:rgba(255,255,255,.78);border-radius:16px;padding:8px 14px;margin:6px 0;color:#1b2b2b;"
             "font-weight:700")
    if attivi:
        st.markdown(f"<div style='{stile}'>🔔 Avvisi di scadenza attivi:<br>" + "<br>".join(attivi) + "</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='{stile}'>🔕 Nessun avviso di scadenza attivo</div>", unsafe_allow_html=True)
    with st.expander("🔔 Scegli come ricevere gli avvisi"):
        st.caption("Puoi attivare più canali insieme: gli avvisi arrivano su tutti quelli che spunti.")
        _fa_guida_avvisi()
        with st.form("fa_form_avvisi"):
            c_tg = st.checkbox("📱 Telegram (gratuito)", value="telegram" in canali)
            v_tg = st.text_input("Chat ID di Telegram (solo numeri)", value=chat, placeholder="es. 123456789")
            c_ml = st.checkbox("✉️ Email (gratuita)", value="email" in canali)
            v_ml = st.text_input("Indirizzo email", value=mail, placeholder="nome@esempio.it")
            c_sm = st.checkbox("💬 SMS (a pagamento)", value="sms" in canali)
            v_sm = st.text_input("Numero di cellulare", value=sms, placeholder="es. 333 1234567")
            privacy = st.checkbox("Nei messaggi non scrivere i nomi dei medicinali (solo quanti sono)",
                                  value=bool(d.get("telegram_privacy")))
            dosi = st.checkbox("⏰ Avvisami anche all'ora delle assunzioni programmate (solo Telegram ed email)",
                               value=bool(d.get("avvisi_dosi")))
            ok = st.form_submit_button("Salva")
        st.caption("Gli avvisi arrivano quando mancano 60, 30, 14, 7 giorni, 1 giorno e il giorno stesso, e ogni lunedì "
                   "per ciò che è già scaduto. Gli SMS sono brevi e non riportano mai i nomi dei medicinali. "
                   "Perché i messaggi partano, l'amministratore deve aver attivato ogni canale su GitHub; "
                   "gli SMS richiedono anche un abbonamento a un servizio di invio, con un costo per messaggio. "
                   "I promemoria delle assunzioni partono ogni mezz'ora: l'avviso arriva nella mezz'ora che contiene "
                   "l'orario della terapia (per esempio quello delle 8:15 arriva tra le 8:00 e le 8:30) e non arriva "
                   "se hai già toccato «✔ Ho preso la medicina». Sono un aiuto in più, non un allarme preciso.")
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
                                      "avviso_sms": v_sm, "telegram_privacy": bool(privacy),
                                      "avvisi_dosi": bool(dosi)}), "Avvisi")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Impostazioni degli avvisi salvate." if scelti else "✅ Avvisi disattivati."
        st.rerun()


# =====================================================================
# REPORT PER IL MEDICO: assunzioni previste e registrate, da scaricare e stampare
# =====================================================================
def _fa_righe_report(f, pid, da, a, adesso_):
    """Una riga per ogni assunzione prevista nel periodo (più quelle registrate fuori dal programma attuale)."""
    registro = f.get("registro") or {}
    righe, viste = [], set()
    giorno = da
    while giorno <= a:
        for ora, t_ in _fa_dosi_giorno(f, pid, giorno):
            k = _fa_chiave(t_, giorno, ora)
            viste.add(k)
            nome = _fa_nome_med(f, t_.get("med"), t_.get("nome_med", ""))
            reg = registro.get(k)
            if reg:
                stato, nota = "Presa", reg.get("quando", "").replace("T", " ")
            elif datetime.fromisoformat(f"{giorno.isoformat()}T{ora}") < adesso_:
                stato, nota = "Non registrata", ""
            else:
                stato, nota = "Da fare", ""
            righe.append({"data": giorno, "ora": ora, "medicinale": nome, "quantita": t_.get("quantita", ""),
                          "stato": stato, "registrata": nota})
        giorno += timedelta(days=1)
    for k, r in registro.items():                       # registrate, ma il programma è stato poi cambiato o eliminato
        d_ = _fa_data(r.get("d"))
        if k not in viste and r.get("p", "p0") == pid and d_ and da <= d_ <= a:
            righe.append({"data": d_, "ora": r.get("o", ""), "medicinale": r.get("nome", ""),
                          "quantita": r.get("q", ""), "stato": "Presa", "registrata": r.get("quando", "").replace("T", " ")})
    righe.sort(key=lambda x: (x["data"], x["ora"]))
    return righe


def _fa_html_report(f, pid, nomi, da, a, righe, riepilogo, oggi_):
    e = html.escape
    terapie = [t_ for t_ in f.get("terapie", []) if t_.get("profilo", "p0") == pid and t_.get("stato", "attiva") == "attiva"]
    allergie = (f.get("allergie") or {}).get(pid, [])
    san = next((p.get("sanitario") for p in f.get("profili", []) if p["id"] == pid), None) or {}
    blocco_san = "".join(f"<h2>{tit}</h2><p>{e(san[k]).replace(chr(10), '<br>')}</p>"
                         for tit, k in (("Patologie", "patologie"), ("Interventi subiti", "interventi"),
                                        ("Storia clinica di rilievo", "storia")) if san.get(k))
    celle = lambda riga: "".join(f"<td>{e(str(c))}</td>" for c in riga)
    t_ter = "".join("<tr>" + celle([_fa_nome_med(f, t_.get("med"), t_.get("nome_med", "")), t_.get("quantita", ""),
                                    ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", [])),
                                    ", ".join(t_.get("orari", [])),
                                    f"dal {data_it(t_['inizio'])}" + (f" al {data_it(t_['fine'])}" if t_.get("fine") else ""),
                                    t_.get("note", "")]) + "</tr>" for t_ in terapie) or "<tr><td colspan='6'>Nessuna terapia attiva</td></tr>"
    t_dosi = "".join("<tr>" + celle([data_it(r["data"].isoformat()), r["ora"], r["medicinale"], r["quantita"], r["stato"],
                                     r["registrata"]]) + "</tr>" for r in righe) or "<tr><td colspan='6'>Nessuna assunzione nel periodo</td></tr>"
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report terapie - {e(nomi[pid])}</title>
<style>body{{font-family:Arial,sans-serif;margin:16px;color:#111}}h1{{font-size:1.3rem}}h2{{font-size:1.05rem;margin-top:22px}}
table{{border-collapse:collapse;width:100%;font-size:.85rem}}th,td{{border:1px solid #999;padding:4px 6px;text-align:left}}th{{background:#eee}}
.nota{{font-size:.8rem;color:#444;margin-top:18px}}.box{{background:#f3f3f3;padding:8px 12px;border-radius:8px}}</style></head><body>
<h1>Report delle terapie – {e(nomi[pid])}</h1>
<p>Periodo: dal {data_it(da.isoformat())} al {data_it(a.isoformat())} · Creato il {data_it(oggi_.isoformat())}</p>
<p>Gruppo sanguigno: <b>{e(next((p.get("gruppo") for p in f.get("profili", []) if p["id"] == pid), None) or "non indicato")}</b></p>
<div class="box"><b>Riepilogo:</b> {riepilogo}</div>
<h2>Allergie e intolleranze dichiarate</h2><p>{e(", ".join(allergie)) if allergie else "Nessuna dichiarata"}</p>
{blocco_san}
<h2>Terapie attive</h2><table><tr><th>Medicinale</th><th>Quantità</th><th>Giorni</th><th>Orari</th><th>Periodo</th><th>Note</th></tr>{t_ter}</table>
<h2>Assunzioni</h2><table><tr><th>Data</th><th>Ora prevista</th><th>Medicinale</th><th>Quantità</th><th>Stato</th><th>Registrata il</th></tr>{t_dosi}</table>
<p class="nota">Documento creato dall'app «La nostra dispensa» con i dati inseriti dall'utente. «Presa» significa che la persona ha toccato
il pulsante nell'app: non è verificato da un medico o da un farmacista.</p></body></html>"""


def _fa_report_medico(f, pid, nomi, oggi_):
    with st.expander("📋 Report per il medico (assunzioni registrate)"):
        c1, c2 = st.columns(2)
        da = c1.date_input("Dal", value=oggi_ - timedelta(days=30), format="DD/MM/YYYY", key="fa_rep_da",
                           min_value=date(2000, 1, 1), max_value=oggi_)
        a = c2.date_input("Al", value=oggi_, format="DD/MM/YYYY", key="fa_rep_a",
                          min_value=date(2000, 1, 1), max_value=oggi_)
        if da > a:
            st.error("La data iniziale non può essere dopo quella finale.")
            return
        if (a - da).days > 366:
            st.error("Scegli un periodo di al massimo un anno.")
            return
        righe = _fa_righe_report(f, pid, da, a, adesso())
        previste = [r for r in righe if r["stato"] != "Da fare"]
        prese = sum(1 for r in previste if r["stato"] == "Presa")
        non_reg = sum(1 for r in previste if r["stato"] == "Non registrata")
        perc = f" ({round(100 * prese / len(previste))}%)" if previste else ""
        riepilogo = f"{len(previste)} assunzioni previste · {prese} registrate come prese{perc} · {non_reg} non registrate"
        st.markdown(f"**{html.escape(nomi[pid])}** · {riepilogo}")
        st.caption("«Non registrata» vuol dire che nell'app non è stato toccato «✔ Ho preso la medicina»: può darsi che la dose sia stata "
                   "presa e non segnata.")
        if righe:
            st.dataframe(pd.DataFrame([{"Data": data_it(r["data"].isoformat()), "Ora": r["ora"], "Medicinale": r["medicinale"],
                                        "Quantità": r["quantita"], "Stato": r["stato"], "Registrata il": r["registrata"]}
                                       for r in righe]), hide_index=True)
        else:
            st.caption("Nessuna assunzione nel periodo scelto.")
        nome_file = f"report_{nomi[pid].replace(' ', '_')}_{da.isoformat()}_{a.isoformat()}"
        csv = pd.DataFrame([{"Data": data_it(r["data"].isoformat()), "Ora": r["ora"], "Medicinale": r["medicinale"],
                             "Quantità": r["quantita"], "Stato": r["stato"], "Registrata il": r["registrata"]}
                            for r in righe]).to_csv(index=False, sep=";").encode("utf-8-sig")
        b1, b2 = st.columns(2, gap="small")
        b1.download_button("🖨️ Scarica da stampare", _fa_html_report(f, pid, nomi, da, a, righe, riepilogo, oggi_).encode("utf-8"),
                           file_name=nome_file + ".html", mime="text/html", width="stretch")
        b2.download_button("📊 Scarica per Excel", csv, file_name=nome_file + ".csv", mime="text/csv", width="stretch")
        st.caption("Il file «da stampare» si apre nel browser: da lì puoi stamparlo o salvarlo in PDF e mostrarlo al medico.")


# =====================================================================
# GRUPPO SANGUIGNO (icone a goccia) E ELENCO MEDICINALI A SCHEDE O TABELLA
# =====================================================================
GRUPPI = ["A+", "B+", "AB+", "0+", "A-", "B-", "AB-", "0-"]
_FA_FOTO_VUOTA = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="


def _fa_icone_gruppi():
    return _fa_icone_gruppi_cache(_fa_mtime("gruppi.webp"))


@st.cache_resource
def _fa_icone_gruppi_cache(_data_file):
    """Ritaglia le otto gocce dall'immagine gruppi.webp (4 colonne x 2 righe) e le dà come immagini piccole."""
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    foglio = Image.open(os.path.join(cartella, "gruppi.webp")).convert("RGBA")   # se manca, non si memorizza l'errore
    w, h = foglio.width // 4, foglio.height // 2
    risultato = {}
    for i, g in enumerate(GRUPPI):
        cella = foglio.crop(((i % 4) * w, (i // 4) * h, (i % 4) * w + w, (i // 4) * h + h))
        buf = io.BytesIO()
        cella.save(buf, "WEBP", quality=88)
        risultato[g] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    return risultato


def _fa_scheda_gruppo(nome, gruppo):
    stile = ("display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.82);border-radius:18px;"
             "padding:8px 10px;margin:0;color:#1b2b2b;min-width:0;border:2px solid rgba(183,28,28,.35);"
             "animation:fa-pulso-r 2.6s infinite")
    freccia = "<div style='margin-left:auto;font-size:1.8rem;color:#b71c1c;font-weight:900;line-height:1'>›</div>"
    if gruppo:
        try:
            uri = _fa_icone_gruppi().get(gruppo)
        except Exception:
            uri = None
        goccia = (f"<img src='{uri}' alt='{html.escape(gruppo)}' style='height:72px;flex:0 0 auto'>" if uri
                  else "<span style='font-size:2rem'>🩸</span>")
        corpo = (f"<b style='font-size:1rem;line-height:1.15'>{html.escape(nome)}</b><br>"
                 f"<span style='font-size:.78rem'>Gruppo sanguigno</span><br>"
                 f"<b style='font-size:1.5rem;color:#b71c1c;line-height:1.1'>{html.escape(gruppo)}</b>")
    else:
        goccia = "<span style='font-size:2rem'>🩸</span>"
        corpo = (f"<b style='font-size:1rem;line-height:1.15'>{html.escape(nome)}</b><br>"
                 "<span style='font-size:.78rem'>Gruppo sanguigno non indicato</span>")
    st.markdown(f"<div style='{stile}'>{goccia}<div style='min-width:0;word-break:break-word'>{corpo}</div>{freccia}</div>",
                unsafe_allow_html=True)


def _fa_elenco_medicinali(f, pid, visibili, vista, oggi_):
    if vista == "Tabella":
        sfondi = {"rosso": "background-color:#ffcdd2", "arancione": "background-color:#ffe0b2",
                  "scaduto": "background-color:#d7ccc8", "ok": "", "nessuna": ""}
        righe = []
        for m in visibili:
            stato, giorni = stato_scadenza(m.get("scadenza"), oggi_)
            righe.append({"Foto": src_sicuro(m.get("foto") or "") or _FA_FOTO_VUOTA, "Medicinale": m.get("nome", ""),
                          "Marca": m.get("marca", ""), "Principio attivo": m.get("principio", ""),
                          "Dosaggio": m.get("dosaggio", ""), "Forma": m.get("forma", ""),
                          "Quantità": f"{fmt_num(float(m.get('quantita') or 0))} {m.get('unita', '')}",
                          "Scadenza": data_it(m["scadenza"]) if m.get("scadenza") else "",
                          "Stato": f"{ICONE[stato]} {testo_giorni(stato, giorni)}",
                          "Allergia": "🚨" if _fa_conflitti(f, pid, m) else "", "_stato": stato})
        if not righe:
            return
        tab = pd.DataFrame(righe)
        tab.insert(0, "🗑️", False)
        tab.index = [m["id"] for m in visibili]
        stile = tab.style.apply(lambda riga: [sfondi[riga["_stato"]]] * len(riga), axis=1)
        mod = st.data_editor(stile, hide_index=True, height=min(700, 60 + 72 * len(tab)), key="fa_tab_" + pid,
                             disabled=[c for c in tab.columns if c != "🗑️"],
                             column_config={"🗑️": st.column_config.CheckboxColumn("🗑️", width="small"),
                                            "Foto": st.column_config.ImageColumn("Foto", width="small"), "_stato": None})
        spunte = list(mod.index[mod["🗑️"]])
        t1, t2 = st.columns(2, gap="small")
        if t1.button("Elimina le righe spuntate", icon=":material/delete:", key="fa_tab_el_" + pid,
                     disabled=not spunte, width="stretch"):
            nomi_sp = ", ".join(m.get("nome", "") for m in visibili if m["id"] in spunte)
            _fa_dialogo_elimina_medicinali(spunte, nomi_sp)
        if t2.button("Modifica la riga spuntata", icon=":material/edit:", key="fa_tab_mo_" + pid,
                     disabled=len(spunte) != 1, width="stretch"):
            _fa_dialogo(pid, spunte[0])
        sel = next((m for m in visibili if len(spunte) == 1 and m["id"] == spunte[0]), None)
        if sel and sel.get("foto") and st.button("🔍 Ingrandisci la foto della riga spuntata", key="fa_tab_foto_" + pid,
                                                 width="stretch"):
            _fa_dialogo_foto(sel)
        if sel and st.button("📖 Foglio illustrativo della riga spuntata", key="fa_tab_fogl_" + pid, width="stretch"):
            if sel.get("foglio") or sel.get("foglio_link"):
                _fa_dialogo_foglio(sel)
            else:
                st.session_state["fa_modulo_foglio"] = {"pid": pid, "med_id": sel["id"]}
                st.rerun()
        if len(spunte) > 1:
            st.caption("Spunta una sola riga da modificare.")
        return
    for m in visibili:
        with st.container(border=True):
            st.markdown(_fa_card(m, oggi_, _fa_conflitti(f, pid, m)), unsafe_allow_html=True)
            if m.get("foto") and st.button("🔍 Ingrandisci la foto", key="fa_foto_" + m["id"], width="stretch"):
                _fa_dialogo_foto(m)
            if m.get("foglio") or m.get("foglio_link"):
                if st.button("📖 Apri il foglio illustrativo", key="fa_fogl_" + m["id"], type="primary", width="stretch"):
                    _fa_dialogo_foglio(m)
            elif st.button("📖 Aggiungi il foglio illustrativo", key="fa_fogl_" + m["id"], width="stretch"):
                st.session_state["fa_modulo_foglio"] = {"pid": pid, "med_id": m["id"]}
                st.rerun()
            b1, b2 = st.columns(2, gap="small")
            if b1.button("Elimina", icon=":material/delete:", key="fa_el_" + m["id"], width="stretch"):
                _fa_dialogo_elimina(m["id"], m.get("nome", ""))
            if b2.button("Modifica", icon=":material/edit:", key="fa_mo_" + m["id"], width="stretch"):
                _fa_dialogo(pid, m["id"])


# =====================================================================
# I MIEI DATI PERSONALI: nome e cognome + report completo di tutto ciò che è stato inserito
# =====================================================================
import copy as _copy


def _fa_senza_immagini(x):
    """Copia dei dati senza le foto incorporate (che renderebbero l'esportazione enorme)."""
    if isinstance(x, dict):
        return {k: _fa_senza_immagini(v) for k, v in x.items() if k not in ("foto", "immagine", "mini")}
    if isinstance(x, list):
        return [_fa_senza_immagini(v) for v in x]
    return x


def _fa_tabella_html(titolo, intestazioni, righe):
    e = html.escape
    if not righe:
        return f"<h3>{e(titolo)}</h3><p class='vuoto'>Nessun dato inserito.</p>"
    th = "".join(f"<th>{e(h)}</th>" for h in intestazioni)
    tr = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in righe)
    return f"<h3>{e(titolo)}</h3><table><tr>{th}</tr>{tr}</table>"


def _fa_html_completo(d, oggi_):
    e = html.escape
    D = lambda iso: data_it(iso) if iso else ""
    f = d.get("farmacia") or {}
    anag = d.get("anagrafica") or {}
    nome_completo = " ".join(x for x in (anag.get("nome"), anag.get("cognome")) if x) or st.session_state["sess"]["nome"]
    profili = f.get("profili") or [{"id": "p0", "nome": st.session_state["sess"]["nome"]}]
    parti = []
    for p in profili:
        pid = p["id"]
        allergie = (f.get("allergie") or {}).get(pid, [])
        parti.append(f"<h2>👤 {e(p['nome'])}</h2><p>Gruppo sanguigno: <b>{e(p.get('gruppo') or 'non indicato')}</b><br>"
                     f"Allergie e intolleranze dichiarate: <b>{e(', '.join(allergie)) if allergie else 'nessuna'}</b></p>")
        dott = p.get("dottore") or {}
        if dott.get("nome") or dott.get("telefono") or dott.get("email"):
            parti.append(f"<p><b>Il mio {e(dott.get('tipo', 'Dottore').lower())}:</b> {e(dott.get('nome', ''))}"
                         + (f" · tel. {e(dott['telefono'])}" if dott.get("telefono") else "")
                         + (f" · {e(dott['email'])}" if dott.get("email") else "")
                         + (f" · {e(dott['indirizzo'])}" if dott.get("indirizzo") else "") + "</p>")
        san = p.get("sanitario") or {}
        for titolo_s, chiave_s in (("Patologie", "patologie"), ("Interventi subiti", "interventi"),
                                   ("Storia clinica di rilievo", "storia"), ("Familiarità", "famiglia"), ("Altre informazioni", "altro")):
            if san.get(chiave_s):
                parti.append(f"<p><b>{titolo_s}:</b><br>{e(san[chiave_s]).replace(chr(10), '<br>')}</p>")
        docs_p = sorted([x for x in f.get("documenti", []) if x.get("profilo", "p0") == pid], key=lambda x: x.get("scadenza") or "9999")
        parti.append(_fa_tabella_html("Documenti", ["Tipo", "Numero", "Rilasciato da", "Rilascio", "Scadenza"],
                                      [[x.get("tipo", ""), x.get("numero", ""), x.get("ente", ""), D(x.get("rilascio")),
                                        "non scade" if x.get("senza_scadenza") else D(x.get("scadenza"))] for x in docs_p]))
        meds = [m for m in f.get("medicinali", []) if m.get("profilo", "p0") == pid]
        parti.append(_fa_tabella_html("Medicinali", ["Nome", "Marca", "Principio attivo", "Dosaggio", "Forma", "Quantità",
                                                      "Scadenza", "Acquisto", "Note"],
                                      [[m.get("nome", ""), m.get("marca", ""), m.get("principio", ""), m.get("dosaggio", ""),
                                        m.get("forma", ""), f"{fmt_num(float(m.get('quantita') or 0))} {m.get('unita', '')}",
                                        D(m.get("scadenza")), D(m.get("acquisto")), m.get("note", "")] for m in meds]))
        ter = [t_ for t_ in f.get("terapie", []) if t_.get("profilo", "p0") == pid]
        parti.append(_fa_tabella_html("Terapie", ["Medicinale", "Quantità", "Giorni", "Orari", "Periodo", "Stato", "Note"],
                                      [[_fa_nome_med(f, t_.get("med"), t_.get("nome_med", "")), t_.get("quantita", ""),
                                        ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", [])), ", ".join(t_.get("orari", [])),
                                        f"dal {D(t_.get('inizio'))}" + (f" al {D(t_['fine'])}" if t_.get("fine") else ""),
                                        STATI_TER.get(t_.get("stato", "attiva"), ""), t_.get("note", "")] for t_ in ter]))
        reg = sorted([r for r in (f.get("registro") or {}).values() if r.get("p", "p0") == pid],
                     key=lambda r: (r.get("d", ""), r.get("o", "")), reverse=True)
        parti.append(_fa_tabella_html("Assunzioni registrate come prese", ["Data", "Ora prevista", "Medicinale", "Quantità", "Registrata il"],
                                      [[D(r.get("d")), r.get("o", ""), r.get("nome", ""), r.get("q", ""),
                                        (r.get("quando") or "").replace("T", " ")] for r in reg]))
        vis = sorted([v for v in f.get("visite", []) if v.get("profilo", "p0") == pid],
                     key=lambda v: v.get("data", ""), reverse=True)
        parti.append(_fa_tabella_html("Visite, esami e referti", ["Data", "Tipo", "Medico o struttura", "Motivo",
                                                                    "Controlli successivi", "Prossimo appuntamento", "Note", "Documenti allegati"],
                                      [[D(v.get("data")) + (f" {v['ora']}" if v.get("ora") else ""), v.get("categoria", ""),
                                        v.get("medico", ""), v.get("motivo", ""), v.get("controlli", ""), D(v.get("prossimo")),
                                        v.get("note", ""), ", ".join(a["nome"] for a in v.get("allegati", []))] for v in vis]))
        vac = sorted([v for v in f.get("vaccinazioni", []) if v.get("profilo", "p0") == pid],
                     key=lambda v: v.get("data", ""), reverse=True)
        parti.append(_fa_tabella_html("Vaccinazioni", ["Vaccino", "Data", "Dose o richiamo", "Prossimo richiamo", "Note"],
                                      [[v.get("nome", ""), D(v.get("data")), v.get("dose", ""), D(v.get("richiamo")),
                                        v.get("note", "")] for v in vac]))
        pagine = (f.get("vaccini_doc") or {}).get(pid, [])
        parti.append(f"<p>Documento vaccinale caricato: <b>{len(pagine)}</b> pagina/e" +
                     (f" ({e(', '.join(a['nome'] for a in pagine))})" if pagine else "") + "</p>")
    canali = d.get("avvisi_canali") or []
    avvisi = [("Telegram", d.get("telegram_chat_id")), ("Email", d.get("avviso_email")), ("SMS", d.get("avviso_sms"))]
    righe_avvisi = [[n, v or "", "attivo" if n.lower() in canali and v else "non attivo"] for n, v in avvisi]
    gen = _fa_tabella_html("Avvisi di scadenza", ["Canale", "Contatto", "Stato"], righe_avvisi)
    gen += (f"<p>Promemoria all'ora delle assunzioni: <b>{'sì' if d.get('avvisi_dosi') else 'no'}</b> · Nei messaggi non scrivere i "
            f"nomi dei medicinali: <b>{'sì' if d.get('telegram_privacy') else 'no'}</b></p>")
    al_d, al_n = d.get("allergie") or [], d.get("allergie_neonato") or []
    gen += (f"<p>Allergie segnalate nella dispensa: <b>{e(', '.join(al_d)) if al_d else 'nessuna'}</b> · "
            f"Allergie del neonato: <b>{e(', '.join(al_n)) if al_n else 'nessuna'}</b> · "
            f"Prodotti nella dispensa: <b>{len(d.get('articoli', []))}</b></p>")
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report completo - {e(nome_completo)}</title>
<style>body{{font-family:Arial,sans-serif;margin:16px;color:#111}}h1{{font-size:1.4rem}}h2{{font-size:1.15rem;margin-top:28px;border-bottom:2px solid #b71c1c}}
h3{{font-size:1rem;margin:16px 0 4px}}table{{border-collapse:collapse;width:100%;font-size:.8rem}}th,td{{border:1px solid #999;padding:3px 5px;text-align:left;vertical-align:top}}
th{{background:#eee}}.vuoto{{color:#666;font-size:.85rem;margin:2px 0}}.nota{{font-size:.8rem;color:#444;margin-top:22px}}
.box{{background:#f3f3f3;padding:8px 12px;border-radius:8px}}@media print{{h2{{page-break-before:auto}}}}</style></head><body>
<h1>Report completo dei dati personali</h1>
<div class="box"><b>{e(nome_completo)}</b><br>Creato il {data_it(oggi_.isoformat())} · Profili: {len(profili)}</div>
{''.join(parti)}
<h2>Impostazioni generali</h2>{gen}
<p class="nota">Documento creato dall'app «La nostra dispensa» con i dati inseriti dall'utente: non è verificato da un medico o da un
farmacista. Le foto e i PDF caricati non sono inclusi: si scaricano uno per uno dalla loro scheda. Contiene dati sanitari: conservalo
con cura.</p></body></html>"""


def _fa_blocco_personale():
    d = carica_dati(crea_archivio(), st.session_state["percorso"])
    anag = d.get("anagrafica") or {}
    nome_completo = " ".join(x for x in (anag.get("nome"), anag.get("cognome")) if x)
    with st.expander("🧾 I miei dati personali e report completo" + (f" · {nome_completo}" if nome_completo else "")):
        with st.form("fa_form_anagrafica"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome", value=anag.get("nome", ""))
            cognome = c2.text_input("Cognome", value=anag.get("cognome", ""))
            ok = st.form_submit_button("Salva nome e cognome")
        st.caption("Qui trovi tutto ciò che hai inserito, in un unico documento: profili, gruppo sanguigno, allergie, medicinali, "
                   "terapie, assunzioni, visite, vaccinazioni e impostazioni degli avvisi.")
        oggi_ = oggi()
        base = (nome_completo or st.session_state["sess"]["nome"]).replace(" ", "_")
        b1, b2 = st.columns(2, gap="small")
        b1.download_button("📄 Report completo (da stampare)", _fa_html_completo(d, oggi_).encode("utf-8"),
                           file_name=f"report_completo_{base}_{oggi_.isoformat()}.html", mime="text/html", width="stretch")
        b2.download_button("📦 Tutti i dati (file JSON)",
                           _json.dumps(_fa_senza_immagini(d), ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"dati_{base}_{oggi_.isoformat()}.json", mime="application/json", width="stretch")
        st.caption("Il report si apre nel browser: da lì puoi stamparlo o salvarlo in PDF. Contiene dati sanitari: non "
                   "condividerlo con chi non deve vederlo.")
    if ok:
        try:
            salva(lambda d: d.__setitem__("anagrafica", {"nome": nome.strip(), "cognome": cognome.strip()}), "Anagrafica")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state["fa_msg"] = "✅ Nome e cognome salvati."
        st.rerun()


# =====================================================================
# FOTO DEL MEDICINALE: stessa fotocamera e stesso editor della dispensa (foto_prodotto.py e fotocamera.py)
# =====================================================================
class _FaFile:
    """Una foto già pronta, resa uguale a un file caricato (nome e contenuto)."""
    def __init__(self, nome, dati):
        self.name, self._dati = nome, dati

    def getvalue(self):
        return self._dati


def _fa_miniatura(uri, lato=360):
    """Versione piccola della foto (mantiene la trasparenza) da tenere nella scheda del medicinale."""
    im = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("RGBA")
    im.thumbnail((lato, lato), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def _fa_assicura_fotocamera():
    """La Farmacia si apre prima che la dispensa carichi fotocamera.py: lo carico qui, così i tasti
    «Scatta la foto» e «Carica dal telefono» aprono la fotocamera posteriore come nella dispensa."""
    if "_avvia_fotocamera_posteriore" in globals():
        return
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    percorso = os.path.join(cartella, "fotocamera.py")
    try:
        with open(percorso, encoding="utf-8") as fh:
            exec(compile(fh.read(), percorso, "exec"), globals())
    except Exception:
        pass


# =====================================================================
# CALENDARIO MENSILE (si può sfogliare fino a 20 anni avanti)
# =====================================================================
import calendar as _cal

MESI_IT = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre",
           "Novembre", "Dicembre"]


def _fa_calendario_mese(f, pid, oggi_):
    with st.expander("📆 Calendario mensile (si può sfogliare fino a 20 anni)"):
        c1, c2 = st.columns(2)
        anni = list(range(oggi_.year - 1, oggi_.year + 21))
        anno = c1.selectbox("Anno", anni, index=anni.index(oggi_.year), key="fa_cal_anno")
        mese = c2.selectbox("Mese", list(range(1, 13)), format_func=lambda i: MESI_IT[i - 1], index=oggi_.month - 1,
                            key="fa_cal_mese")
        registro = f.get("registro") or {}
        righe_html = ""
        con_dosi = []
        for sett in _cal.Calendar(firstweekday=0).monthdayscalendar(anno, mese):
            righe_html += "<tr>"
            for giorno in sett:
                if giorno == 0:
                    righe_html += "<td style='background:transparent'></td>"
                    continue
                d = date(anno, mese, giorno)
                dosi = _fa_dosi_giorno(f, pid, d)
                tot = len(dosi)
                prese = sum(1 for ora, t_ in dosi if _fa_chiave(t_, d, ora) in registro)
                if tot:
                    con_dosi.append(giorno)
                if not tot:
                    sfondo, testo = "", ""
                elif d > oggi_:
                    sfondo, testo = "background:#e3f2fd;", f"⏳ {tot}"
                elif prese == tot:
                    sfondo, testo = "background:#c8e6c9;", f"✅ {prese}/{tot}"
                elif prese == 0 and d < oggi_:
                    sfondo, testo = "background:#ffcdd2;", f"❌ 0/{tot}"
                else:
                    sfondo, testo = "background:#ffe0b2;", f"⚠️ {prese}/{tot}"
                classe = " class='oggi'" if d == oggi_ else ""
                righe_html += f"<td{classe} style='{sfondo}'><b>{giorno}</b><br>{testo}</td>"
            righe_html += "</tr>"
        st.markdown("<table class='cm'><tr>" + "".join(f"<th>{g}</th>" for g in GIORNI_SETT) + "</tr>" + righe_html + "</table>",
                    unsafe_allow_html=True)
        st.caption("✅ tutte prese · ⚠️ alcune da registrare · ❌ nessuna registrata · ⏳ ancora da fare. "
                   "Scegli un giorno qui sotto per vedere le assunzioni e segnarle.")
        if not con_dosi:
            st.caption("Nessuna assunzione programmata in questo mese.")
            return
        predefinito = oggi_.day if (anno, mese) == (oggi_.year, oggi_.month) and oggi_.day in con_dosi else con_dosi[0]
        giorno_sel = st.selectbox("Apri un giorno", con_dosi, index=con_dosi.index(predefinito), key="fa_cal_giorno",
                                  format_func=lambda g: f"{g} {MESI_IT[mese - 1]}")
        d_sel = date(anno, mese, giorno_sel)
        ora_adesso = adesso()
        for ora, t_ in _fa_dosi_giorno(f, pid, d_sel):
            _fa_riga_dose(f, pid, d_sel, ora, t_, ora_adesso, "m")


# =====================================================================
# FOGLIO ILLUSTRATIVO (BUGIARDINO) ALLEGATO AL MEDICINALE
# =====================================================================
def _fa_url_https(testo):
    testo = (testo or "").strip()
    if testo and not testo.lower().startswith(("http://", "https://")):
        testo = "https://" + testo
    return testo


@st.dialog("Foglio illustrativo", width="large")
def _fa_dialogo_foglio(m):
    st.markdown(f"### 💊 {html.escape(m.get('nome', ''))}")
    link = m.get("foglio_link")
    if link:
        st.link_button("🔗 Apri il foglio illustrativo online", link, width="stretch")
    for a in m.get("foglio", []):
        d = carica_dati(crea_archivio(), _fa_percorso_doc(a["id"]))
        if not d.get("b64"):
            st.warning(f"Non trovo il file «{a['nome']}».")
            continue
        dati = base64.b64decode(d["b64"])
        if d.get("mime", "").startswith("image/"):
            st.image(dati)
        else:
            st.download_button("📄 Apri il PDF: " + a["nome"], dati, file_name=a["nome"], mime="application/pdf",
                               width="stretch", key="fa_fogl_dl_" + a["id"])
    if st.button("✏️ Aggiungi o cambia il foglio illustrativo", key="fa_fogl_cambia_" + m["id"], width="stretch"):
        st.session_state["fa_modulo_foglio"] = {"pid": m.get("profilo", "p0"), "med_id": m["id"]}
        st.rerun()
    st.caption("📖 Controindicazioni e avvertenze sono in questo documento: leggilo o chiedi al medico o al farmacista. "
               "L'app non valuta se un medicinale va bene per una malattia.")


def _fa_modulo_foglio(pid, med_id):
    f = _fa_dati()
    m = next((x for x in f.get("medicinali", []) if x["id"] == med_id), None)
    if not m:
        st.session_state.pop("fa_modulo_foglio", None)
        st.rerun()
    if st.button("← Torna ai medicinali", key="fa_fogl_indietro"):
        st.session_state.pop("fa_modulo_foglio", None)
        st.rerun()
    st.subheader(f"📖 Foglio illustrativo di {m.get('nome', '')}")

    st.markdown("**1️⃣ Trova il foglio illustrativo**")
    cerca = _up.quote_plus(" ".join(x for x in ("foglio illustrativo", m.get("nome", ""), m.get("principio", "")) if x) + " AIFA")
    c1, c2 = st.columns(2, gap="small")
    c1.link_button("🏛️ Cerca sul sito AIFA", "https://medicinali.aifa.gov.it/", width="stretch")
    c2.link_button("🔎 Cerca con Google", "https://www.google.com/search?q=" + cerca, width="stretch")
    st.caption(f"Sul sito AIFA scrivi «{m.get('nome', '')}» e scarica il foglio illustrativo.")

    st.markdown("**2️⃣ Scaricalo, oppure fotografa il foglietto della scatola**")
    st.markdown("**3️⃣ Caricalo qui**")
    caricati = st.file_uploader("Scegli il PDF scaricato oppure scatta le foto delle pagine", key="fa_fogl_up_" + med_id,
                                type=["pdf", "jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    link = st.text_input("Oppure incolla qui il link del foglio illustrativo", value=m.get("foglio_link", ""),
                         key="fa_fogl_link_" + med_id, placeholder="https://…")

    if m.get("foglio"):
        st.markdown("**Già allegato:**")
        for a in m["foglio"]:
            r1, r2 = st.columns([3, 1], gap="small")
            r1.markdown(("📄 " if a.get("mime") == "application/pdf" else "🖼️ ") + html.escape(a["nome"]))
            if r2.button("🗑️", key="fa_fogl_del_" + a["id"], help="Elimina questo file"):
                def _togli(f, did=a["id"]):
                    for x in f["medicinali"]:
                        if x["id"] == med_id:
                            x["foglio"] = [y for y in x.get("foglio", []) if y["id"] != did]
                try:
                    _fa_salva(_togli, "Farmacia: foglio illustrativo")
                    _fa_cancella_files([a["id"]])
                except Exception as e:
                    st.error(f"Non sono riuscito a eliminarlo: {e}")
                else:
                    st.rerun()

    if st.button("💾 Salva il foglio illustrativo", type="primary", key="fa_fogl_salva", width="stretch"):
        link = _fa_url_https(link)
        if not caricati and link == (m.get("foglio_link") or ""):
            st.warning("Scegli un file o incolla un link, poi tocca Salva.")
            return
        try:
            nuovi = _fa_salva_files(caricati) if caricati else []
        except ValueError as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(f"Non sono riuscito a salvare i file: {e}")
            return

        def _scrivi(f):
            for x in f["medicinali"]:
                if x["id"] == med_id:
                    x["foglio"] = (x.get("foglio") or []) + nuovi
                    x["foglio_link"] = link
        try:
            _fa_salva(_scrivi, "Farmacia: foglio illustrativo")
        except Exception as e:
            st.error(f"Non sono riuscito a salvare: {e}")
            return
        st.session_state.pop("fa_modulo_foglio", None)
        st.session_state["fa_msg"] = f"✅ Foglio illustrativo di {m.get('nome', '')} salvato: ora lo apri dal pulsante «📖 Apri il foglio illustrativo»."
        st.rerun()


# =====================================================================
# ARCHIVIO DELLE FOTO DEI MEDICINALI (per riusarle quando si ricompra lo stesso medicinale)
# =====================================================================
def _fa_ids_foto_usati(f):
    """File delle foto grandi ancora in uso da un medicinale o dall'archivio."""
    usati = {m["foto_grande"]["id"] for m in f.get("medicinali", []) if m.get("foto_grande")}
    usati |= {e["grande"]["id"] for e in f.get("archivio_foto", []) if e.get("grande")}
    return usati


def _fa_scegli_da_archivio(f, ck):
    arch = f.get("archivio_foto") or []
    chiave = "fa_arch_scelta_" + ck
    with st.expander(f"🗂️ Scegli una foto già usata ({len(arch)})"):
        if not arch:
            st.caption("Qui compaiono le foto dei medicinali che salvi: se ricompri lo stesso medicinale, "
                       "basta sceglierla e non devi rifare la foto.")
        else:
            miniature = "".join(
                f"<div style='width:88px;text-align:center;font-size:.7rem'><img src='{html.escape(e['mini'], quote=True)}' alt='' "
                f"style='height:84px;max-width:84px;object-fit:contain'><br>{html.escape(e['nome'][:16])}</div>" for e in arch)
            st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:8px'>{miniature}</div>", unsafe_allow_html=True)
            nomi = {e["id"]: f"{e['nome']} · {data_it(e['data'])}" for e in arch}
            scelto = st.selectbox("Quale vuoi usare?", list(nomi), format_func=lambda i: nomi[i], key="fa_arch_sel_" + ck)
            voce = next(e for e in arch if e["id"] == scelto)
            c1, c2 = st.columns(2, gap="small")
            if c1.button("✔ Usa questa foto", key="fa_arch_usa_" + ck, type="primary", width="stretch"):
                st.session_state[chiave] = scelto
                st.rerun()
            if c2.button("🗑️ Togli dall'archivio", key="fa_arch_del_" + ck, width="stretch"):
                try:
                    _fa_salva(lambda f: f.__setitem__("archivio_foto", [e for e in f.get("archivio_foto", []) if e["id"] != scelto]),
                              "Farmacia: archivio foto")
                    if voce.get("grande") and voce["grande"]["id"] not in _fa_ids_foto_usati(_fa_dati()):
                        _fa_cancella_files([voce["grande"]["id"]])
                except Exception as e:
                    st.error(f"Non sono riuscito a eliminarla: {e}")
                else:
                    if st.session_state.get(chiave) == scelto:
                        st.session_state.pop(chiave, None)
                    st.rerun()
    voce_scelta = next((e for e in arch if e["id"] == st.session_state.get(chiave)), None)
    if voce_scelta:
        st.success(f"✅ Foto scelta dall'archivio: {voce_scelta['nome']}. Tocca Salva in fondo per usarla.")
        try:
            st.image(base64.b64decode(voce_scelta["mini"].split(",", 1)[1]), width=160)
        except Exception:
            pass
        if st.button("↩ Non usare questa foto", key="fa_arch_no_" + ck):
            st.session_state.pop(chiave, None)
            st.rerun()
    return voce_scelta


# =====================================================================
# IL MIO DOTTORE: pulsante con l'immagine accanto al gruppo sanguigno e scheda con tutti i dati
# =====================================================================
def _fa_icone_dottori():
    return _fa_icone_dottori_cache(_fa_mtime("dottori.webp"))


@st.cache_resource
def _fa_icone_dottori_cache(_data_file):
    """Le due immagini (dottore e dottoressa) ritagliate da dottori.webp, in due metà."""
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    foglio = Image.open(os.path.join(cartella, "dottori.webp")).convert("RGBA")
    w = foglio.width // 2
    risultato = {}
    for i, nome in enumerate(("Dottore", "Dottoressa")):
        buf = io.BytesIO()
        foglio.crop((i * w, 0, i * w + w, foglio.height)).save(buf, "WEBP", quality=88)
        risultato[nome] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    return risultato


def _fa_scheda_gruppo_quadrata(nome, gruppo):
    """Il badge del gruppo sanguigno in formato quadrato stondato (goccia, gruppo e nome), che pulsa."""
    stile = ("aspect-ratio:200/236;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;"
             "background:rgba(255,255,255,.82);border-radius:22px;padding:4px;margin:0;color:#1b2b2b;min-width:0;"
             "overflow:hidden;border:2px solid rgba(183,28,28,.35);animation:fa-pulso-r 2.6s infinite")
    uri = None
    if gruppo:
        try:
            uri = _fa_icone_gruppi().get(gruppo)
        except Exception:
            uri = None
    goccia = (f"<img src='{uri}' alt='{html.escape(gruppo)}' style='height:56px;flex:0 0 auto'>" if uri
              else "<span style='font-size:2.2rem;line-height:1'>🩸</span>")
    testo = (f"<b style='font-size:1.3rem;color:#b71c1c;line-height:1'>{html.escape(gruppo)}</b>" if gruppo
             else "<span style='font-size:.7rem;text-align:center;line-height:1.1'>Gruppo non indicato</span>")
    st.markdown(f"<div style='{stile}'>{goccia}{testo}"
                f"<span style='font-size:.66rem;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>"
                f"{html.escape(nome)}</span></div>", unsafe_allow_html=True)


def _fa_riga_profilo(profili, pid, nome, gruppo):
    """Una sola striscia con tre badge: gruppo sanguigno (apre la scheda sanitaria), dottore e tessera sanitaria."""
    dott = next((p.get("dottore") for p in profili if p["id"] == pid), None) or {}
    tipo = dott.get("tipo")
    try:
        uri = _fa_icone_dottori().get(tipo)
    except Exception:
        uri = None
    sfondo = f"url({uri}) center/contain no-repeat," if uri else ""
    uri_ts = _fa_file_uri("tessera.webp")
    sfondo_ts = f"url({uri_ts}) center/90% auto no-repeat," if uri_ts else ""
    st.markdown(
        "<style>"
        ".st-key-azioni_gruppo [data-testid='stHorizontalBlock']{align-items:flex-start !important;gap:8px !important}"
        ".st-key-azioni_gruppo [data-testid='stColumn'],.st-key-azioni_gruppo [data-testid='column']"
        "{flex:1 1 0 !important;min-width:0 !important;width:auto !important}"
        ".st-key-fa_dottore_btn [data-testid='stButton'],.st-key-fa_dottore_btn2 [data-testid='stButton'],"
        ".st-key-fa_ts_btn [data-testid='stButton'],.st-key-fa_ts_btn2 [data-testid='stButton']{width:100%}"
        ".st-key-fa_dottore_btn button,.st-key-fa_ts_btn button{width:100%;height:auto;aspect-ratio:200/236;min-height:0;"
        "border-radius:22px;border:0;padding:0;font-size:2.6rem;color:transparent}"
        f".st-key-fa_dottore_btn button{{background:{sfondo}rgba(255,255,255,.7);animation:fa-pulso 2.6s infinite}}"
        f".st-key-fa_ts_btn button{{background:{sfondo_ts}linear-gradient(160deg,#eaf4ff,#bfdcff);animation:fa-pulso-b 2.2s infinite}}"
        ".st-key-fa_dottore_btn button p,.st-key-fa_ts_btn button p{font-size:0}"
        "@keyframes fa-pulso{0%{box-shadow:0 0 0 0 rgba(13,148,136,.55)}70%{box-shadow:0 0 0 12px rgba(13,148,136,0)}"
        "100%{box-shadow:0 0 0 0 rgba(13,148,136,0)}}"
        "@keyframes fa-pulso-r{0%{box-shadow:0 0 0 0 rgba(198,40,40,.5)}70%{box-shadow:0 0 0 10px rgba(198,40,40,0)}"
        "100%{box-shadow:0 0 0 0 rgba(198,40,40,0)}}"
        "@keyframes fa-pulso-b{0%{transform:scale(1);box-shadow:0 0 0 0 rgba(21,101,192,.6)}"
        "45%{transform:scale(1.045)}70%{box-shadow:0 0 0 12px rgba(21,101,192,0)}"
        "100%{transform:scale(1);box-shadow:0 0 0 0 rgba(21,101,192,0)}}"
        ".st-key-fa_dottore_btn2 button,.st-key-fa_gruppo_btn2 button,.st-key-fa_ts_btn2 button"
        "{width:100%;min-height:46px;border-radius:18px;border:0;padding:3px 6px}"
        ".st-key-fa_gruppo_btn2{margin-top:13px !important}"
        ".st-key-fa_dottore_btn2 button{background:linear-gradient(135deg,#00a98f,#0288d1);box-shadow:0 3px 0 rgba(0,70,90,.3)}"
        ".st-key-fa_gruppo_btn2 button{background:linear-gradient(135deg,#c62828,#ef5350);box-shadow:0 3px 0 rgba(110,20,20,.35)}"
        ".st-key-fa_ts_btn2 button{background:linear-gradient(135deg,#1565c0,#42a5f5);box-shadow:0 3px 0 rgba(10,50,110,.35)}"
        ".st-key-fa_dottore_btn2 button p,.st-key-fa_gruppo_btn2 button p,.st-key-fa_ts_btn2 button p{color:#fff !important;"
        "font-weight:800 !important;font-size:.74rem !important;line-height:1.1;margin:0;white-space:normal !important;"
        "overflow:visible !important;text-overflow:clip !important;text-align:center}"
        ".st-key-fa_gruppo_btn2 [data-testid='stButton']{width:100%}"
        ".st-key-fa_gruppo_box{position:relative}"
        ".st-key-fa_gruppo_btn{position:absolute !important;top:0;left:0;right:0;bottom:0;width:100% !important;"
        "height:100% !important;margin:0 !important;z-index:3}"
        ".st-key-fa_gruppo_btn [data-testid='stButton']{width:100%;height:100%}"
        ".st-key-fa_gruppo_btn button{width:100%;height:100%;min-height:0;opacity:0;cursor:pointer}"
        "</style>", unsafe_allow_html=True)
    etichetta = "La mia dottoressa" if tipo == "Dottoressa" else "Il mio dottore"
    with st.container(key="azioni_gruppo"):
        c1, c2, c3 = st.columns(3, gap="small")
        with c1:
            with st.container(key="fa_gruppo_box"):
                _fa_scheda_gruppo_quadrata(nome, gruppo)
                premuto_g = st.button("Apri la scheda sanitaria", key="fa_gruppo_btn", width="stretch")
            premuto_g2 = st.button("📋 Scheda sanitaria ›", key="fa_gruppo_btn2", width="stretch")
        with c2:
            premuto = st.button("🩺" if not uri else etichetta, key="fa_dottore_btn", help="Apri la scheda del dottore",
                                width="stretch")
            premuto2 = st.button(etichetta + " ›", key="fa_dottore_btn2", help="Apri la scheda del dottore", width="stretch")
        with c3:
            premuto_t = st.button("🪪" if not uri_ts else "Tessera sanitaria", key="fa_ts_btn",
                                  help="Tessera sanitaria e fascicolo sanitario", width="stretch")
            premuto_t2 = st.button("Tessera sanitaria · Fascicolo sanitario ›", key="fa_ts_btn2",
                                   help="Tessera sanitaria e fascicolo sanitario", width="stretch")
    if premuto_g or premuto_g2:
        st.session_state["fa_modulo_sanitario"] = {"pid": pid}
        st.rerun()
    if premuto or premuto2:
        st.session_state["fa_modulo_dottore"] = {"pid": pid}
        st.rerun()
    if premuto_t or premuto_t2:
        st.session_state["fa_modulo_tessera"] = {"pid": pid}
        st.rerun()


def _fa_tel(numero):
    return re.sub(r"[^\d+]", "", numero or "")


def _fa_modulo_dottore(pid):
    f = _fa_dati()
    profili = _fa_profili(f)
    profilo = next((p for p in profili if p["id"] == pid), profili[0])
    d = profilo.get("dottore") or {}
    dati_utente = carica_dati(crea_archivio(), st.session_state["percorso"])
    anag = dati_utente.get("anagrafica") or {}
    mio_nome = " ".join(x for x in (anag.get("nome"), anag.get("cognome")) if x) or profilo.get("nome", "")
    mia_email_pred = d.get("mia_email") or dati_utente.get("avviso_email") or ""
    e = html.escape
    ha_dati = any(d.get(k) for k in ("nome", "telefono", "email", "indirizzo"))
    chiave_mod = "fa_dott_modifica_" + pid
    modifica = st.session_state.get(chiave_mod, not ha_dati)          # senza dati si apre subito in modifica
    tipo_salvato = d.get("tipo")
    femmina = tipo_salvato == "Dottoressa"

    if st.button("← Torna alla Farmacia", key="fa_dott_indietro"):
        st.session_state.pop("fa_modulo_dottore", None)
        st.session_state.pop(chiave_mod, None)
        st.rerun()
    st.subheader(("👩‍⚕️ La mia dottoressa" if femmina else "👨‍⚕️ Il mio dottore") + f" · {profilo.get('nome', '')}")
    try:
        icone = _fa_icone_dottori()
    except Exception:
        icone = {}
    if tipo_salvato in icone:
        st.markdown(f"<div style='text-align:center'><img src='{icone[tipo_salvato]}' alt='' style='height:150px'></div>", unsafe_allow_html=True)

    giorno_oggi = GIORNI_SETT[oggi().weekday()]
    if not modifica:
        # ------------------------------------------------ SCHEDA (sola lettura)
        if d.get("nome"):
            st.markdown(f"### {e(d['nome'])}")
        if st.button("✏️ Modifica i dati", key="fa_dott_modifica_btn", type="primary", width="stretch"):
            st.session_state[chiave_mod] = True
            st.rerun()
        righe = []
        if d.get("indirizzo"):
            righe.append(f"📍 {e(d['indirizzo'])}")
        if d.get("telefono"):
            righe.append(f"📞 {e(d['telefono'])}")
        if d.get("email"):
            righe.append(f"✉️ {e(d['email'])}")
        if righe:
            st.markdown("<div style='background:rgba(255,255,255,.78);border-radius:18px;padding:12px 14px;color:#1b2b2b;"
                        "line-height:1.7;font-weight:600'>" + "<br>".join(righe) + "</div>", unsafe_allow_html=True)
        fasce_d = _fa_fasce_dottore(d)
        oggi_f = [x for x in fasce_d if x["g"] == giorno_oggi]
        if oggi_f:
            st.info(f"🕘 Oggi ({giorno_oggi}) riceve: " + " · ".join(
                f"{x['da']}–{x['a']}" + (f" ({x['nota']})" if x.get("nota") else "") for x in oggi_f))
        elif fasce_d:
            st.caption(f"Oggi ({giorno_oggi}) non è indicato nessun orario di ricevimento.")
        b1, b2 = st.columns(2, gap="small")
        if _fa_tel(d.get("telefono")):
            b1.link_button("📞 Chiama", "tel:" + _fa_tel(d["telefono"]), width="stretch")
        if d.get("indirizzo"):
            b2.link_button("🧭 Indicazioni", "https://www.google.com/maps/search/?api=1&query=" + _up.quote_plus(d["indirizzo"]), width="stretch")

        if d.get("email"):
            with st.expander("✉️ Scrivi un messaggio " + ("alla dottoressa" if femmina else "al dottore")):
                oggetto = st.text_input("Oggetto", value="Richiesta", key="fa_dott_ogg_" + pid)
                testo = st.text_area("Messaggio", key="fa_dott_msg_" + pid, placeholder="Scrivi qui il tuo messaggio…")
                firma = st.checkbox("Aggiungi in fondo il mio nome e la mia email per la risposta", value=True, key="fa_dott_firma_" + pid)
                corpo = testo
                if firma:
                    corpo += f"\n\n--\n{mio_nome}"
                    if profilo.get("nome") and profilo["nome"] != mio_nome:
                        corpo += f"\nPaziente: {profilo['nome']}"
                    if mia_email_pred:
                        corpo += f"\nPer rispondermi: {mia_email_pred}"
                st.link_button("📧 Apri la posta e invia", f"mailto:{d['email']}?subject={_up.quote(oggetto)}&body={_up.quote(corpo)}",
                               type="primary", width="stretch")
                st.caption("Si apre la tua app di posta con il messaggio già pronto: tocca Invia. Il medico risponde al tuo indirizzo.")

        if fasce_d:
            st.markdown("**🕘 Orari di ricevimento**")
            celle = ""
            for x in fasce_d:
                evid = "background:#c8e6c9;font-weight:800;" if x["g"] == giorno_oggi else ""
                celle += (f"<tr style='{evid}'><td style='padding:5px 8px'>{x['g']}</td><td>{e(x['da'])}</td>"
                          f"<td>{e(x['a'])}</td><td>{e(x.get('nota') or '')}</td></tr>")
            st.markdown("<table style='width:100%;border-collapse:collapse;font-size:.9rem;color:#1b2b2b;background:rgba(255,255,255,.78);"
                        "border-radius:12px;overflow:hidden'><tr style='background:rgba(0,0,0,.06)'><th style='text-align:left;padding:5px 8px'>Giorno</th>"
                        "<th style='text-align:left'>Dalle</th><th style='text-align:left'>Alle</th><th style='text-align:left'>Note</th></tr>"
                        + celle + "</table>", unsafe_allow_html=True)

        sost = d.get("sostituto") or {}
        if sost.get("nome") or sost.get("telefono") or sost.get("email"):
            with st.expander("🔁 Sostituto: " + (sost.get("nome") or "dati salvati")):
                if sost.get("indirizzo"):
                    st.write("📍 " + sost["indirizzo"])
                s1, s2 = st.columns(2, gap="small")
                if _fa_tel(sost.get("telefono")):
                    s1.link_button("📞 Chiama il sostituto", "tel:" + _fa_tel(sost["telefono"]), width="stretch")
                if sost.get("email"):
                    s2.link_button("✉️ Scrivi al sostituto", "mailto:" + sost["email"], width="stretch")
                if sost.get("note"):
                    st.caption("📝 " + sost["note"])
        if d.get("note"):
            st.markdown("**📝 Note**")
            st.markdown("<div style='background:rgba(255,255,255,.78);border-radius:14px;padding:10px 12px;color:#1b2b2b'>"
                        + e(d["note"]).replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
        return

    # ------------------------------------------------ MODIFICA
    if ha_dati and st.button("Annulla la modifica", key="fa_dott_annulla"):
        st.session_state[chiave_mod] = False
        st.rerun()
    st.markdown("**✏️ Dati del medico**: compila e tocca **Salva** in fondo")
    with st.form("fa_form_dottore_" + pid):
        tipo = st.radio("Scegli", ["Dottore", "Dottoressa"], horizontal=True, index=1 if femmina else 0)
        nome = st.text_input("Nominativo (nome e cognome)", value=d.get("nome", ""), placeholder="es. Dott. Mario Rossi")
        indirizzo = st.text_input("Indirizzo dello studio", value=d.get("indirizzo", ""))
        telefono = st.text_input("Numero di telefono", value=d.get("telefono", ""))
        email = st.text_input("Email del medico", value=d.get("email", ""))
        mia_email = st.text_input("La mia email (a cui il medico può rispondere)", value=mia_email_pred)
        st.markdown("**🕘 Orari di ricevimento**")
        st.caption("Una riga per ogni orario: scegli il giorno, «Dalle» e «Alle» dal menu, e se vuoi una nota. "
                   "Per un secondo orario nello stesso giorno aggiungi un'altra riga con il «+» in fondo alla tabella; "
                   "per toglierne una, spunta la riga a sinistra e usa il cestino.")
        fasce_att = _fa_fasce_dottore(d) or [{"g": g, "da": "", "a": "", "nota": ""} for g in GIORNI_SETT[:5]]
        extra_t = {x for fs in fasce_att for x in (fs.get("da"), fs.get("a")) if x}
        opzioni = ["—"] + sorted(set(ORARI_STUDIO) | extra_t)
        note_pred = ["Accesso libero", "Su appuntamento", "Telefonico"]
        opz_note = ["—"] + note_pred + sorted({fs.get("nota") for fs in fasce_att if fs.get("nota")} - set(note_pred))
        df_f = pd.DataFrame([{"Giorno": fs["g"], "Dalle": fs.get("da") or "—", "Alle": fs.get("a") or "—",
                              "Note": fs.get("nota") or "—"} for fs in fasce_att])
        mod = st.data_editor(df_f, hide_index=True, num_rows="dynamic", key="fa_dott_fasce_" + pid, width="stretch",
                             column_config={"Giorno": st.column_config.SelectboxColumn("Giorno", options=GIORNI_SETT, width="small"),
                                            "Dalle": st.column_config.SelectboxColumn("Dalle", options=opzioni, width="small"),
                                            "Alle": st.column_config.SelectboxColumn("Alle", options=opzioni, width="small"),
                                            "Note": st.column_config.SelectboxColumn("Note", options=opz_note, width="medium")})
        with st.expander("🔁 Sostituto (se il medico è assente)"):
            sv = d.get("sostituto") or {}
            s_nome = st.text_input("Nominativo del sostituto", value=sv.get("nome", ""))
            s_tel = st.text_input("Telefono del sostituto", value=sv.get("telefono", ""))
            s_email = st.text_input("Email del sostituto", value=sv.get("email", ""))
            s_ind = st.text_input("Indirizzo del sostituto", value=sv.get("indirizzo", ""))
            s_note = st.text_area("Note sul sostituto (giorni, orari…)", value=sv.get("note", ""))
        note = st.text_area("📝 Note", value=d.get("note", ""), placeholder="Qualsiasi cosa da ricordare su questo medico")
        invio = st.form_submit_button("💾 Salva i dati del medico", type="primary", width="stretch")
    if invio:
        if email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", email.strip()):
            st.error("L'email del medico non sembra corretta.")
            return
        fasce_nuove, errori_o = [], []
        for _, r in mod.iterrows():
            g_ = r.get("Giorno")
            if g_ not in GIORNI_SETT:
                continue
            vuoto = lambda v: v is None or pd.isna(v) or str(v) in ("—", "")
            da_ = "" if vuoto(r["Dalle"]) else str(r["Dalle"])
            a_ = "" if vuoto(r["Alle"]) else str(r["Alle"])
            nota_ = "" if vuoto(r["Note"]) else str(r["Note"])
            if not da_ and not a_:
                continue
            if bool(da_) != bool(a_):
                errori_o.append(f"{g_}: scegli sia «Dalle» sia «Alle».")
            elif a_ <= da_:
                errori_o.append(f"{g_}: «Alle» deve essere dopo «Dalle».")
            else:
                fasce_nuove.append({"g": g_, "da": da_, "a": a_, "nota": nota_})
        if errori_o:
            st.error("Controlla gli orari: " + " ".join(errori_o))
            return
        fasce_nuove.sort(key=lambda x: (GIORNI_SETT.index(x["g"]), x["da"]))
        nuovo = {"tipo": tipo, "nome": nome.strip(), "indirizzo": indirizzo.strip(), "telefono": telefono.strip(),
                 "email": email.strip(), "mia_email": mia_email.strip(),
                 "fasce": fasce_nuove,
                 "sostituto": {"nome": s_nome.strip(), "telefono": s_tel.strip(), "email": s_email.strip(),
                               "indirizzo": s_ind.strip(), "note": s_note.strip()},
                 "note": note.strip()}

        def _scrivi(f):
            for p in f["profili"]:
                if p["id"] == pid:
                    p["dottore"] = nuovo
        try:
            _fa_salva(_scrivi, "Farmacia: dottore")
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare: {ex}")
            return
        st.session_state[chiave_mod] = False
        st.session_state["fa_msg"] = "✅ Dati del medico salvati."
        st.rerun()


# =====================================================================
# ORARI A TENDINA E SCHEDA SANITARIA
# =====================================================================
ORARI_STUDIO = [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in (0, 15, 30, 45)]


def _fa_parse_fascia(testo):
    """Da «9:00-12:30» (o simili) a ('09:00', '12:30'); se non si capisce ('', '')."""
    m = re.search(r"(\d{1,2})(?:[:.](\d{2}))?\s*[-–]\s*(\d{1,2})(?:[:.](\d{2}))?", testo or "")
    if not m:
        return "", ""
    return f"{int(m.group(1)):02d}:{int(m.group(2) or 0):02d}", f"{int(m.group(3)):02d}:{int(m.group(4) or 0):02d}"


def _fa_righe_html(testo, vuoto="— nessuna indicazione —"):
    righe = [r.strip() for r in (testo or "").splitlines() if r.strip()]
    if not righe:
        return f"<span style='opacity:.6'>{vuoto}</span>"
    return "<br>".join("• " + html.escape(r) for r in righe)


def _fa_sezione(titolo, corpo_html):
    st.markdown(f"<div style='background:rgba(255,255,255,.8);border-radius:16px;padding:10px 14px;margin:8px 0;color:#1b2b2b'>"
                f"<b>{titolo}</b><div style='margin-top:4px;line-height:1.6'>{corpo_html}</div></div>", unsafe_allow_html=True)


def _fa_html_sanitaria(f, pid, intestatario):
    e = html.escape
    D = lambda iso: data_it(iso) if iso else ""
    profilo = next((p for p in _fa_profili(f) if p["id"] == pid), {})
    san = profilo.get("sanitario") or {}
    dott = profilo.get("dottore") or {}
    allergie = (f.get("allergie") or {}).get(pid, [])
    vacc = sorted([v for v in f.get("vaccinazioni", []) if v.get("profilo", "p0") == pid], key=lambda v: v.get("data", ""), reverse=True)
    ter = [t_ for t_ in f.get("terapie", []) if t_.get("profilo", "p0") == pid and t_.get("stato", "attiva") == "attiva"]

    def blocco(titolo, testo):
        return f"<h2>{titolo}</h2><p>{e(testo).replace(chr(10), '<br>') if testo else '<i>nessuna indicazione</i>'}</p>"
    vac_html = "".join(f"<li>{e(v['nome'])} – {D(v.get('data'))}" + (f" ({e(v['dose'])})" if v.get("dose") else "")
                       + (f" – richiamo {D(v['richiamo'])}" if v.get("richiamo") else "") + "</li>" for v in vacc)
    ter_html = "".join(f"<li>{e(_fa_nome_med(f, t_.get('med'), t_.get('nome_med', '')))} – {e(t_.get('quantita', ''))} – "
                       f"{e(', '.join(t_.get('orari', [])))}</li>" for t_ in ter)
    medico = ""
    if dott.get("nome") or dott.get("telefono"):
        medico = f"<p><b>Medico:</b> {e(dott.get('nome', ''))} {e(dott.get('telefono', ''))} {e(dott.get('email', ''))}</p>"
    allergie_html = e(', '.join(allergie)) if allergie else '<i>nessuna dichiarata</i>'
    vacc_blocco = ('<ul>' + vac_html + '</ul>') if vac_html else '<p><i>nessuna registrata</i></p>'
    ter_blocco = ('<ul>' + ter_html + '</ul>') if ter_html else '<p><i>nessuna</i></p>'
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scheda sanitaria - {e(profilo.get('nome', ''))}</title>
<style>body{{font-family:Arial,sans-serif;margin:16px;color:#111}}h1{{font-size:1.4rem}}h2{{font-size:1.05rem;margin:16px 0 2px;border-bottom:1px solid #999}}
.box{{background:#f3f3f3;padding:8px 12px;border-radius:8px}}.nota{{font-size:.8rem;color:#444;margin-top:22px}}</style></head><body>
<h1>Scheda sanitaria – {e(profilo.get('nome', ''))}</h1>
<div class="box"><b>Intestatario:</b> {e(intestatario)}<br><b>Gruppo sanguigno:</b> {e(profilo.get('gruppo') or 'non indicato')}<br>
<b>Aggiornata il</b> {data_it(oggi().isoformat())}</div>{medico}
<h2>Allergie e intolleranze ai farmaci</h2><p>{allergie_html}</p>
{blocco('Patologie', san.get('patologie'))}{blocco('Interventi subiti', san.get('interventi'))}
{blocco('Storia clinica di rilievo', san.get('storia'))}{blocco('Familiarità', san.get('famiglia'))}
{blocco('Altre informazioni', san.get('altro'))}
<h2>Vaccinazioni</h2>{vacc_blocco}
<h2>Terapie in corso</h2>{ter_blocco}
<p class="nota">Documento creato dall'app «La nostra dispensa» con i dati inseriti dall'utente: non è verificato da un medico.</p>
</body></html>"""


def _fa_modulo_sanitario(pid):
    f = _fa_dati()
    profili = _fa_profili(f)
    profilo = next((p for p in profili if p["id"] == pid), profili[0])
    san = profilo.get("sanitario") or {}
    dott = profilo.get("dottore") or {}
    allergie = (f.get("allergie") or {}).get(pid, [])
    dati_utente = carica_dati(crea_archivio(), st.session_state["percorso"])
    anag = dati_utente.get("anagrafica") or {}
    intestatario = " ".join(x for x in (anag.get("nome"), anag.get("cognome")) if x) or profilo.get("nome", "")
    chiave_mod = "fa_san_modifica_" + pid
    modifica = st.session_state.get(chiave_mod, False)
    e = html.escape

    if st.button("← Torna alla Farmacia", key="fa_san_indietro"):
        st.session_state.pop("fa_modulo_sanitario", None)
        st.session_state.pop(chiave_mod, None)
        st.rerun()
    st.subheader(f"📋 Scheda sanitaria · {profilo.get('nome', '')}")

    if modifica:
        # ------------------------------------------------ MODIFICA
        if st.button("Annulla la modifica", key="fa_san_annulla"):
            st.session_state[chiave_mod] = False
            st.rerun()
        st.markdown("**✏️ Compila quello che ti serve** e tocca **Salva** in fondo. Tutto è facoltativo.")
        with st.form("fa_form_san_" + pid):
            patologie = st.text_area("🩺 Patologie (una per riga, con l'anno se vuoi)", value=san.get("patologie", ""),
                                     placeholder="es. Ipertensione (dal 2015)\nDiabete tipo 2", height=110)
            all_t = st.text_area("💊 Allergie e intolleranze ai farmaci (separate da virgola)", value=", ".join(allergie),
                                 placeholder="es. penicillina, ibuprofene",
                                 help="Sono le stesse del riquadro Allergie: l'app le usa per avvisarti sui medicinali.")
            interventi = st.text_area("🏥 Interventi subiti (uno per riga: anno, intervento, dove)", value=san.get("interventi", ""),
                                      placeholder="es. 2019 – Appendicectomia – Ospedale Molinette", height=110)
            storia = st.text_area("📜 Storia clinica di rilievo", value=san.get("storia", ""),
                                  placeholder="Ricoveri, malattie importanti, esami da ricordare…", height=130)
            famiglia = st.text_area("👪 Malattie in famiglia (familiarità)", value=san.get("famiglia", ""), height=90)
            altro = st.text_area("➕ Altre informazioni importanti", value=san.get("altro", ""),
                                 placeholder="es. porta un pacemaker, donatore di organi, contatto di emergenza…", height=110)
            invio = st.form_submit_button("💾 Salva la scheda sanitaria", type="primary", width="stretch")
        if invio:
            nuovo = {"patologie": patologie.strip(), "interventi": interventi.strip(), "storia": storia.strip(),
                     "famiglia": famiglia.strip(), "altro": altro.strip()}
            lista_all = [x.strip() for x in re.split(r"[,;\n]", all_t) if x.strip()]

            def _scrivi(f):
                for p in f["profili"]:
                    if p["id"] == pid:
                        p["sanitario"] = nuovo
                f.setdefault("allergie", {})[pid] = lista_all
            try:
                _fa_salva(_scrivi, "Farmacia: scheda sanitaria")
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare: {ex}")
                return
            st.session_state[chiave_mod] = False
            st.session_state["fa_msg"] = "✅ Scheda sanitaria salvata."
            st.rerun()
        return

    # ------------------------------------------------ SCHEDA (sola lettura)
    gruppo = profilo.get("gruppo")
    try:
        uri = _fa_icone_gruppi().get(gruppo) if gruppo else None
    except Exception:
        uri = None
    st.markdown(
        "<div style='display:flex;align-items:center;gap:14px;background:rgba(255,255,255,.82);border-radius:18px;padding:10px 14px;color:#1b2b2b'>"
        + (f"<img src='{uri}' alt='' style='height:90px'>" if uri else "<span style='font-size:2.4rem'>🩸</span>")
        + f"<div><b style='font-size:1.15rem'>{e(intestatario)}</b><br>Gruppo sanguigno: "
        + f"<b style='font-size:1.6rem;color:#b71c1c'>{e(gruppo or 'non indicato')}</b></div></div>", unsafe_allow_html=True)
    if st.button("✏️ Modifica la scheda sanitaria", key="fa_san_modifica_btn", type="primary", width="stretch"):
        st.session_state[chiave_mod] = True
        st.rerun()
    if dott.get("nome") or dott.get("telefono"):
        _fa_sezione("👩‍⚕️ Medico curante" if dott.get("tipo") == "Dottoressa" else "👨‍⚕️ Medico curante",
                    e(" · ".join(x for x in (dott.get("nome"), dott.get("telefono")) if x)))
    _fa_sezione("💊 Allergie e intolleranze ai farmaci",
                e(", ".join(allergie)) if allergie else "<span style='opacity:.6'>— nessuna dichiarata —</span>")
    _fa_sezione("🩺 Patologie", _fa_righe_html(san.get("patologie")))
    _fa_sezione("🏥 Interventi subiti", _fa_righe_html(san.get("interventi")))
    _fa_sezione("📜 Storia clinica di rilievo",
                e(san.get("storia", "")).replace("\n", "<br>") or "<span style='opacity:.6'>— nessuna indicazione —</span>")
    if san.get("famiglia"):
        _fa_sezione("👪 Malattie in famiglia", e(san["famiglia"]).replace("\n", "<br>"))
    if san.get("altro"):
        _fa_sezione("➕ Altre informazioni", e(san["altro"]).replace("\n", "<br>"))
    vacc = sorted([v for v in f.get("vaccinazioni", []) if v.get("profilo", "p0") == pid], key=lambda v: v.get("data", ""), reverse=True)
    righe_v = "<br>".join(f"• {e(v['nome'])} – {data_it(v['data'])}" + (f" ({e(v['dose'])})" if v.get("dose") else "")
                          + (f" – richiamo {data_it(v['richiamo'])}" if v.get("richiamo") else "") for v in vacc)
    pagine = len((f.get("vaccini_doc") or {}).get(pid, []))
    _fa_sezione("💉 Vaccinazioni", (righe_v or "<span style='opacity:.6'>— nessuna registrata —</span>")
                + (f"<br><small>📄 Documento vaccinale: {pagine} pagina/e</small>" if pagine else "")
                + "<br><small>Si gestiscono nella scheda 💉 Vaccini.</small>")
    ter = [t_ for t_ in f.get("terapie", []) if t_.get("profilo", "p0") == pid and t_.get("stato", "attiva") == "attiva"]
    if ter:
        _fa_sezione("📅 Terapie in corso", "<br>".join(
            f"• {e(_fa_nome_med(f, t_.get('med'), t_.get('nome_med', '')))} – {e(t_.get('quantita', ''))} – {e(', '.join(t_.get('orari', [])))}"
            for t_ in ter))
    st.download_button("📄 Scarica la scheda (da stampare o inviare)", _fa_html_sanitaria(f, pid, intestatario).encode("utf-8"),
                       file_name=f"scheda_sanitaria_{profilo.get('nome', '').replace(' ', '_')}_{oggi().isoformat()}.html",
                       mime="text/html", width="stretch")
    st.caption("Contiene dati sanitari: condividila solo con chi deve vederla.")



def _fa_fasce_dottore(d):
    """Orari di ricevimento come elenco di fasce [{g, da, a, nota}]. Capisce anche il vecchio formato mattina/pomeriggio."""
    fasce = d.get("fasce")
    if fasce is None:
        fasce = []
        for g in GIORNI_SETT:
            o = (d.get("orari") or {}).get(g) or {}
            for k in ("m", "p"):
                da, a = _fa_parse_fascia(o.get(k))
                if da and a:
                    fasce.append({"g": g, "da": da, "a": a, "nota": ""})
    return sorted([dict(x) for x in fasce if x.get("g") in GIORNI_SETT],
                  key=lambda x: (GIORNI_SETT.index(x["g"]), x.get("da", "")))


# =====================================================================
# I MIEI DOCUMENTI: catalogo dei documenti personali con avvisi di scadenza a 6 e a 3 mesi
# =====================================================================
CATALOGO_DOCUMENTI = {
    "🪪 Identità": ["Carta d'identità", "Passaporto", "Patente di guida", "Codice fiscale", "Permesso di soggiorno",
                    "Certificato di nascita", "Stato di famiglia", "Certificato di residenza", "Tessera elettorale"],
    "🏥 Salute": ["Tessera sanitaria", "Esenzione ticket", "Certificato medico sportivo", "Certificato di invalidità",
                  "Piano terapeutico", "Polizza sanitaria"],
    "🚗 Veicoli": ["Libretto / carta di circolazione", "Assicurazione auto (RCA)", "Bollo auto", "Revisione del veicolo",
                   "Assicurazione moto", "Patente nautica", "Contrassegno invalidi", "Telepass / abbonamento"],
    "🏠 Casa": ["Contratto di affitto", "Atto di proprietà", "Assicurazione casa", "Attestato energetico (APE)",
                "Libretto impianto / caldaia", "Visura catastale", "Contratto luce", "Contratto gas",
                "Contratto internet / telefono", "Regolamento condominiale"],
    "💼 Lavoro": ["Contratto di lavoro", "Tesserino professionale", "Abilitazione / patentino", "Attestato corso sicurezza",
                  "Idoneità lavorativa", "Iscrizione all'albo"],
    "🎓 Studio": ["Diploma", "Laurea", "Libretto universitario", "Certificazione linguistica", "Attestato di corso"],
    "💳 Soldi e assicurazioni": ["Carta di credito / bancomat", "Carta prepagata", "Conto corrente", "Polizza vita",
                                  "Polizza infortuni", "ISEE", "Dichiarazione dei redditi", "Pensione / INPS",
                                  "Mutuo / finanziamento"],
    "✈️ Viaggi": ["Visto", "Assicurazione viaggio", "Abbonamento trasporti", "Biglietto / prenotazione"],
    "🐾 Animali": ["Libretto sanitario animale", "Microchip animale", "Assicurazione animale"],
    "📄 Altro": ["Licenza di caccia o pesca", "Porto d'armi", "Tessera associazione / sport", "Abbonamento (palestra, ecc.)",
                 "Garanzia / scontrino", "Testamento / documenti legali", "Altro"],
}
_DOC_COL = {"scaduto": "#4e342e", "urgente": "#d32f2f", "avviso": "#ef6c00", "ok": "#2e7d32", "nessuna": "#00897b"}
_DOC_ICO = {"scaduto": "⚫", "urgente": "🚨", "avviso": "🟠", "ok": "🟢", "nessuna": "⚪"}


def _doc_catalogo(f):
    """Tipi di documento per categoria: quelli di serie (meno quelli nascosti) più quelli aggiunti dall'utente."""
    nascosti = set(f.get("tipi_nascosti") or [])
    cat = {c: [t for t in lst if t not in nascosti] for c, lst in CATALOGO_DOCUMENTI.items()}
    for x in f.get("tipi_documento") or []:
        cat.setdefault(x.get("cat") or "📄 Altro", [])
        if x["nome"] not in cat[x.get("cat") or "📄 Altro"]:
            cat[x.get("cat") or "📄 Altro"].append(x["nome"])
    return {c: lst for c, lst in cat.items() if lst}


def _doc_stato(scad_iso, oggi_):
    """('scaduto' | 'urgente' entro 3 mesi | 'avviso' entro 6 mesi | 'ok' | 'nessuna', giorni mancanti)."""
    d_ = _fa_data(scad_iso)
    if not d_:
        return "nessuna", None
    giorni = (d_ - oggi_).days
    if giorni < 0:
        return "scaduto", giorni
    if d_ <= aggiungi_mesi(oggi_, 3):
        return "urgente", giorni
    if d_ <= aggiungi_mesi(oggi_, 6):
        return "avviso", giorni
    return "ok", giorni


def _doc_conteggi_home():
    try:
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
        docs = (d.get("farmacia") or {}).get("documenti", [])
    except Exception:
        return 0, 0
    oggi_ = oggi()
    stati = [_doc_stato(x.get("scadenza"), oggi_)[0] for x in docs if not x.get("senza_scadenza")]
    return sum(1 for s in stati if s in ("urgente", "scaduto")), sum(1 for s in stati if s == "avviso")


def _fa_file_uri(nome, mime="image/webp"):
    return _fa_file_uri_cache(nome, mime, _fa_mtime(nome))


@st.cache_resource
def _fa_file_uri_cache(nome, mime, _data_file):
    try:
        cartella = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        cartella = "."
    try:
        with open(os.path.join(cartella, nome), "rb") as fh:
            return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()
    except OSError:
        return ""


def _css_icona(chiave, uri, aspetto, animazione, durata, larghezza=100):
    return (f".st-key-{chiave}{{--img:url({uri})}}"
            f".st-key-{chiave} button,.st-key-{chiave} button:hover,.st-key-{chiave} button:focus,.st-key-{chiave} button:active"
            "{background:var(--img) center/contain no-repeat !important;border:0 !important;box-shadow:none !important;color:transparent}"
            f".st-key-{chiave} button{{width:{larghezza}px;height:auto;aspect-ratio:{aspetto};min-height:0;padding:0;border-radius:0;"
            f"cursor:pointer;animation:{animazione} {durata}s ease-in-out infinite}}"
            f".st-key-{chiave} button:active{{transform:scale(.94);animation:none}}"
            f".st-key-{chiave} button p{{font-size:0}}")


def icona_farmacia():
    """Le due icone della Home, una accanto all'altra: Farmacia e I miei documenti. Pulsano piano per far capire che si toccano."""
    uri = _fa_icona_uri()
    uri_d = _fa_file_uri("documenti.webp")
    urg, avv = _doc_conteggi_home()
    css = ("<style>.st-key-azioni_icone [data-testid='stHorizontalBlock']{flex-direction:row !important;flex-wrap:wrap !important;"
           "gap:8px !important;align-items:flex-start !important}"
           ".st-key-azioni_icone [data-testid='stColumn'],.st-key-azioni_icone [data-testid='column']"
           "{flex:0 0 auto !important;width:auto !important;min-width:0 !important}"
           "@keyframes fa-battito{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.25))}"
           "50%{transform:scale(1.07);filter:drop-shadow(0 0 14px rgba(229,57,53,.9))}}"
           "@keyframes doc-battito{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.25))}"
           "50%{transform:scale(1.07);filter:drop-shadow(0 0 14px rgba(2,136,209,.95))}}"
           "@keyframes doc-allarme{0%,100%{transform:scale(1);filter:drop-shadow(0 0 4px rgba(211,47,47,.6))}"
           "50%{transform:scale(1.09);filter:drop-shadow(0 0 18px rgba(211,47,47,1))}}")
    if uri:
        css += _css_icona("fa_icona", uri, "1/1", "fa-battito", 2.2)
    if uri_d:
        css += _css_icona("doc_icona", uri_d, "360/345", "doc-allarme" if urg else "doc-battito", 1.2 if urg else 2.2)
    uri_u = _fa_file_uri("utilita.webp") if "schermata_utilita" in globals() else ""
    if uri_u:
        css += ("@keyframes ut-battito{0%,100%{transform:scale(1);filter:drop-shadow(0 4px 6px rgba(0,0,0,.25))}"
                "50%{transform:scale(1.07);filter:drop-shadow(0 0 14px rgba(0,188,212,.95))}}")
        css += _css_icona("ut_icona", uri_u, "360/345", "ut-battito", 2.2)
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)
    with st.container(key="azioni_icone"):
        c1, c2, c3 = st.columns(3, gap="small")
        premuto_u = False
        with c3:
            if uri_u:
                premuto_u = st.button("Utilità", key="ut_icona", help="Apri le Utilità")
        with c1:
            premuto = st.button("Farmacia" if uri else "🏥 Farmacia", key="fa_icona", help="Apri la Farmacia")
        with c2:
            premuto_d = st.button("I miei documenti" if uri_d else "📁 I miei documenti", key="doc_icona",
                                  help="Apri i miei documenti")
            if urg or avv:
                st.markdown(f"<div style='width:112px;text-align:center;font-weight:800;font-size:.72rem;"
                            f"color:{'#b71c1c' if urg else '#e65100'}'>{'🚨' if urg else '⚠️'} {urg or avv} "
                            f"{'da rinnovare' if urg else 'in scadenza'}</div>", unsafe_allow_html=True)
    if premuto_u:
        st.session_state["sezione_home"] = "utilita"
        st.session_state["farmacia_aperta"] = True
        st.rerun()
    if premuto:
        st.session_state.pop("sezione_home", None)
        st.session_state["farmacia_aperta"] = True
        st.rerun()
    if premuto_d:
        st.session_state["sezione_home"] = "documenti"
        st.session_state["farmacia_aperta"] = True
        st.rerun()


def _doc_css():
    st.markdown("<style>@keyframes doc-pulso{0%{box-shadow:0 0 0 0 rgba(211,47,47,.55)}70%{box-shadow:0 0 0 12px rgba(211,47,47,0)}"
                "100%{box-shadow:0 0 0 0 rgba(211,47,47,0)}}"
                ".doc-urg{animation:doc-pulso 1.6s infinite;background:#ffebee}"
                ".doc-allarme-box{background:linear-gradient(135deg,#b71c1c,#e53935);color:#fff;border-radius:18px;padding:12px 16px;"
                "margin:8px 0;font-weight:800;animation:doc-pulso 1.6s infinite}"
                ".doc-hero{background:linear-gradient(135deg,#0277bd 0%,#039be5 55%,#26c6da 100%);color:#fff;padding:20px 24px;"
                "border-radius:24px;margin:6px 0 12px;box-shadow:0 10px 30px rgba(0,0,0,.15)}"
                ".doc-hero h1{margin:0;font-size:1.8rem;color:#fff;padding:0}.doc-hero p{margin:4px 0 0;opacity:.92}</style>",
                unsafe_allow_html=True)


def _doc_card(x, oggi_, emoji):
    e = html.escape
    stato, g = _doc_stato(x.get("scadenza"), oggi_)
    if x.get("senza_scadenza"):
        stato = "nessuna"
    righe = f"<div class='nome'>{emoji} {e(x.get('tipo', ''))}</div>"
    if x.get("numero"):
        righe += f"<div class='riga'>🔢 {e(x['numero'])}</div>"
    if x.get("ente"):
        righe += f"<div class='riga'>🏛️ {e(x['ente'])}</div>"
    if x.get("rilascio"):
        righe += f"<div class='riga'>📅 Rilasciato il {data_it(x['rilascio'])}</div>"
    if x.get("senza_scadenza"):
        righe += "<span class='scad'>♾️ Non scade</span>"
    elif x.get("scadenza"):
        testo = {"scaduto": f"SCADUTO da {abs(g or 0)} giorni", "urgente": f"URGENTE · scade tra {g} giorni (entro 3 mesi)",
                 "avviso": f"Scade tra {g} giorni (entro 6 mesi)", "ok": f"Scade tra {g} giorni"}.get(stato, "")
        righe += f"<span class='scad'>{_DOC_ICO[stato]} {e(testo)} · {data_it(x['scadenza'])}</span>"
    if x.get("note"):
        righe += f"<div class='riga'>📝 {e(x['note'])}</div>"
    classe = "fa-med doc-urg" if stato == "urgente" else "fa-med"
    return f"<div class='{classe}' style='--c:{_DOC_COL[stato]}'>{righe}</div>"


def schermata_documenti():
    st.markdown(_FA_CSS, unsafe_allow_html=True)
    _doc_css()
    if st.button("← Torna alla dispensa", key="doc_indietro"):
        st.session_state.pop("sezione_home", None)
        st.session_state.pop("doc_modulo", None)
        st.session_state["farmacia_aperta"] = False
        st.rerun()
    st.markdown("<div class='doc-hero'><h1>📁 I miei documenti</h1><p>Scadenze sempre sotto controllo: ti avviso 6 e 3 mesi prima</p></div>",
                unsafe_allow_html=True)
    if st.session_state.get("fa_msg"):
        _msg = st.session_state.pop("fa_msg")
        (st.warning if _msg.startswith("⚠️") else st.success)(_msg)
    if st.session_state.get("doc_modulo"):
        _doc_modulo(**st.session_state["doc_modulo"])
        return

    _fa_info("documenti")
    f = _fa_dati()
    profili = _fa_profili(f)
    nomi = {p["id"]: p["nome"] for p in profili}
    if st.session_state.get("fa_profilo") not in nomi:
        st.session_state["fa_profilo"] = profili[0]["id"]
    pid = st.selectbox("👤 Documenti di", list(nomi), format_func=lambda i: nomi[i], key="fa_profilo")
    oggi_ = oggi()
    docs = [x for x in f.get("documenti", []) if x.get("profilo", "p0") == pid]
    stati = [(x, "nessuna" if x.get("senza_scadenza") else _doc_stato(x.get("scadenza"), oggi_)[0]) for x in docs]
    n = lambda *s: sum(1 for _, st_ in stati if st_ in s)
    st.markdown(
        "<div class='fa-kpi'>"
        f"<div class='fa-k'><span>Documenti</span><b>{len(stati)}</b></div>"
        f"<div class='fa-k arancione'><span>Entro 6 mesi</span><b>{n('avviso')}</b></div>"
        f"<div class='fa-k rosso'><span>Entro 3 mesi</span><b>{n('urgente')}</b></div>"
        f"<div class='fa-k scaduto'><span>Scaduti</span><b>{n('scaduto')}</b></div></div>", unsafe_allow_html=True)

    urgenti = [x for x, s_ in stati if s_ == "urgente"]
    scaduti = [x for x, s_ in stati if s_ == "scaduto"]
    avvisi = [x for x, s_ in stati if s_ == "avviso"]
    if urgenti or scaduti:
        elenco = ", ".join(html.escape(x.get("tipo", "")) + (f" ({data_it(x['scadenza'])})" if x.get("scadenza") else "")
                           for x in urgenti + scaduti)
        st.markdown(f"<div class='doc-allarme-box'>🚨 SECONDO AVVISO · SCADENZA VICINA O GIÀ PASSATA<br>"
                    f"<span style='font-weight:600'>{elenco}</span></div>", unsafe_allow_html=True)
        if not st.session_state.get("doc_toast_" + pid):
            st.session_state["doc_toast_" + pid] = True
            st.toast("🚨 Hai documenti da rinnovare con urgenza", icon="🚨")
    if avvisi:
        st.warning("🟠 **Primo avviso** · scadono entro 6 mesi: " + ", ".join(
            f"{x.get('tipo', '')} ({data_it(x['scadenza'])})" for x in avvisi))

    if st.button("➕ Aggiungi un documento", type="primary", key="doc_aggiungi", width="stretch"):
        st.session_state["doc_modulo"] = {"pid": pid, "doc_id": None}
        st.rerun()

    cat = _doc_catalogo(f)
    emoji_di = {t: c.split(" ")[0] for c, lst in cat.items() for t in lst}
    c1, c2 = st.columns([3, 2])
    cerca = c1.text_input("Cerca", placeholder="tipo, numero, ente, note…", label_visibility="collapsed", key="doc_cerca")
    categorie = ["Tutte le categorie"] + list(cat)
    filtro = c2.selectbox("Categoria", categorie, label_visibility="collapsed", key="doc_cat")
    visibili = []
    for x, s_ in stati:
        testo = " ".join(str(x.get(k, "")) for k in ("tipo", "numero", "ente", "note")).lower()
        if cerca and cerca.lower() not in testo:
            continue
        if filtro != "Tutte le categorie" and x.get("tipo") not in cat.get(filtro, []):
            continue
        visibili.append(x)
    visibili.sort(key=lambda x: (x.get("senza_scadenza") or not x.get("scadenza"), x.get("scadenza") or "9999-12-31"))

    if not docs:
        st.info("Nessun documento per questo profilo. Tocca «Aggiungi un documento» per inserire il primo.")
    elif not visibili:
        st.info("Nessun documento corrisponde ai filtri.")
    for x in visibili:
        with st.container(border=True):
            st.markdown(_doc_card(x, oggi_, emoji_di.get(x.get("tipo"), "📄")), unsafe_allow_html=True)
            _fa_bottoni_allegati(x.get("allegati", []), "documento", x["id"])
            b1, b2 = st.columns(2, gap="small")
            if b1.button("Elimina", icon=":material/delete:", key="doc_el_" + x["id"], width="stretch"):
                _fa_dialogo_elimina_voce("documenti", x["id"], x.get("tipo", "documento"))
            if b2.button("Modifica", icon=":material/edit:", key="doc_mo_" + x["id"], width="stretch"):
                st.session_state["doc_modulo"] = {"pid": pid, "doc_id": x["id"]}
                st.rerun()
    _doc_gestione_tipi(f)
    st.caption("🔔 Gli avvisi su Telegram e per email (se li hai attivati) arrivano 6 mesi prima (primo avviso) e 3 mesi prima "
               "(secondo avviso, più insistente). Contiene dati personali: non condividerli con chi non deve vederli.")


def _doc_modulo(pid, doc_id=None):
    f = _fa_dati()
    profili = _fa_profili(f)
    nomi = {p["id"]: p["nome"] for p in profili}
    x = next((d_ for d_ in f.get("documenti", []) if d_["id"] == doc_id), {}) if doc_id else {}
    if st.button("← Annulla e torna ai documenti", key="doc_mod_annulla"):
        st.session_state.pop("doc_modulo", None)
        st.rerun()
    _fa_assicura_fotocamera()
    st.subheader("✏️ Modifica documento" if doc_id else "➕ Nuovo documento")
    cat = _doc_catalogo(f)
    tutti = [t for lst in cat.values() for t in lst]
    if x.get("tipo") and x["tipo"] not in tutti:
        tutti.insert(0, x["tipo"])
    emoji_di = {t: c.split(" ")[0] for c, lst in cat.items() for t in lst}

    if x.get("allegati"):
        st.markdown("**Già allegato:**")
        for a in x["allegati"]:
            r1, r2, r3 = st.columns([3, 1, 1], gap="small")
            r1.markdown(("📄 " if a.get("mime") == "application/pdf" else "🖼️ ") + html.escape(a["nome"]))
            if r2.button("Apri", key="doc_ap_" + a["id"]):
                _fa_dialogo_doc(a, "documento", doc_id)
            if r3.button("🗑️", key="doc_del_" + a["id"], help="Elimina questo file"):
                try:
                    _fa_rimuovi_allegato("documento", doc_id, a["id"])
                except Exception as ex:
                    st.error(f"Non sono riuscito a eliminarlo: {ex}")
                else:
                    st.rerun()

    # le foto stanno FUORI dal modulo (come nei medicinali): fotocamera posteriore, sfondo tolto, raddrizzatura e ritocco a mano
    st.markdown("**📷 Foto del documento** (facoltativa)")
    st.caption("Fai la foto del **fronte** e, se serve, del **retro**: scatta oppure carica dal telefono. "
               "Poi raddrizza e taglia a mano se vuoi, e in fondo tocca **Salva il documento**.")
    chiave_d = "doc_" + (doc_id or "nuovo")
    foto_fronte = foto_retro = ""
    try:
        foto_fronte = campo_foto_doc(chiave_d + "_fronte", "📄 Fronte")
        foto_retro = campo_foto_doc(chiave_d + "_retro", "📄 Retro")
    except NameError:                                  # manca foto_prodotto.py: resta il campo «Altri file»
        st.caption("La foto con ritocco non è disponibile in questo momento: usa il campo «Altri file» qui sotto.")
    pre = {}
    if foto_fronte or foto_retro:                       # dalla foto si ricavano tipo, numero, ente e date da proporre nei campi
        try:
            pre = _doc_precompila(chiave_d, foto_fronte, foto_retro, tutti)
        except Exception as ex:
            st.warning(f"La lettura automatica non è riuscita ({type(ex).__name__}): compila i campi a mano.")
    with st.form("doc_form_" + (doc_id or "nuovo")):
        tipo = st.selectbox("Tipo di documento", tutti, index=_fa_idx(tutti, pre.get("tipo") or x.get("tipo")),
                            format_func=lambda t: f"{emoji_di.get(t, '📄')} {t}")
        nuovo_tipo = st.text_input("Non lo trovi? Scrivi qui il nuovo tipo", placeholder="es. Tessera della biblioteca")
        cat_nuovo = st.selectbox("Categoria del nuovo tipo", list(CATALOGO_DOCUMENTI), index=len(CATALOGO_DOCUMENTI) - 1)
        per = st.selectbox("Di chi è", list(nomi), format_func=lambda i: nomi[i], index=_fa_idx(list(nomi), x.get("profilo", pid)))
        numero = st.text_input("Numero o identificativo", value=pre.get("numero") or x.get("numero", ""))
        ente = st.text_input("Rilasciato da", value=pre.get("ente") or x.get("ente", ""))
        rilascio = st.date_input("Data di rilascio (facoltativa)", value=_fa_data(pre.get("rilascio") or x.get("rilascio")), format="DD/MM/YYYY",
                                 min_value=date(1930, 1, 1), max_value=date(2100, 12, 31))
        senza = st.checkbox("Questo documento non scade", value=bool(x.get("senza_scadenza")))
        scadenza = st.date_input("Data di scadenza", value=_fa_data(pre.get("scadenza") or x.get("scadenza")), format="DD/MM/YYYY",
                                 min_value=date(1930, 1, 1), max_value=date(2100, 12, 31))
        note = st.text_area("Note", value=x.get("note") or pre.get("note", ""))
        nuovi = st.file_uploader("Altri file (facoltativo): PDF o foto di altre pagine", type=TIPI_FILE,
                                 accept_multiple_files=True)
        invio = st.form_submit_button("💾 Salva il documento", type="primary", width="stretch")
    st.caption("L'avviso arriva 6 mesi prima della scadenza (primo avviso) e 3 mesi prima (secondo avviso, più insistente).")
    if invio:
        tipo_f = nuovo_tipo.strip() or tipo
        nome_base = _re_doc.sub(r"[^\w\- ]+", "", tipo_f).strip() or "Documento"
        da_salvare = [_FaFile(f"{lato_d} - {nome_base}.webp", base64.b64decode(foto_d.split(",", 1)[1]))
                      for foto_d, lato_d in ((foto_fronte, "Fronte"), (foto_retro, "Retro")) if foto_d]
        da_salvare += list(nuovi or [])
        try:
            riferimenti = _fa_salva_files(da_salvare) if da_salvare else []
        except ValueError as ex:
            st.error(str(ex))
            return
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare i file: {ex}")
            return
        rec = {"profilo": per, "tipo": tipo_f, "numero": numero.strip(), "ente": ente.strip(),
               "rilascio": rilascio.isoformat() if rilascio else None, "senza_scadenza": bool(senza),
               "scadenza": None if senza or not scadenza else scadenza.isoformat(), "note": note.strip()}

        def _scrivi(f):
            f.setdefault("documenti", [])
            noti = {t for lst in _doc_catalogo(f).values() for t in lst} | set(CATALOGO_DOCUMENTI.get("📄 Altro", []))
            if nuovo_tipo.strip() and tipo_f not in noti:
                f.setdefault("tipi_documento", []).append({"nome": tipo_f, "cat": cat_nuovo})
            if doc_id:
                for d_ in f["documenti"]:
                    if d_["id"] == doc_id:
                        d_.update(rec)
                        d_["allegati"] = (d_.get("allegati") or []) + riferimenti
            else:
                rec["id"] = uuid.uuid4().hex[:10]
                rec["allegati"] = riferimenti
                f["documenti"].append(rec)
        try:
            _fa_salva(_scrivi, "Documenti: salvataggio")
        except Exception as ex:
            st.error(f"Non sono riuscito a salvare: {ex}")
            return
        st.session_state.pop("doc_modulo", None)
        stato_, _g = _doc_stato(rec["scadenza"], oggi())
        st.session_state["fa_msg"] = ("⚠️ Documento salvato, ma attenzione: " + ("è già scaduto." if stato_ == "scaduto"
                                      else "scade entro 3 mesi: rinnovalo presto.") if stato_ in ("scaduto", "urgente")
                                      else "✅ Documento salvato.")
        st.rerun()


def _doc_gestione_tipi(f):
    with st.expander("⚙️ Gestisci i tipi di documento"):
        st.caption("Aggiungi i tuoi tipi, toglili o nascondi quelli che non usi.")
        with st.form("doc_form_tipo", clear_on_submit=True):
            nome = st.text_input("Nuovo tipo di documento", placeholder="es. Tessera della biblioteca")
            categoria = st.selectbox("Categoria", list(CATALOGO_DOCUMENTI), index=len(CATALOGO_DOCUMENTI) - 1)
            ok = st.form_submit_button("Aggiungi il tipo")
        if ok and nome.strip():
            try:
                _fa_salva(lambda f: f.setdefault("tipi_documento", []).append({"nome": nome.strip(), "cat": categoria}),
                          "Documenti: tipo")
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare: {ex}")
            else:
                st.rerun()
        for i, t_ in enumerate(f.get("tipi_documento") or []):
            r1, r2 = st.columns([4, 1], gap="small")
            r1.markdown(f"{t_.get('cat', '📄 Altro').split(' ')[0]} {html.escape(t_['nome'])}")
            if r2.button("🗑️", key=f"doc_tipo_del_{i}", help="Togli questo tipo (i documenti già inseriti restano)"):
                try:
                    _fa_salva(lambda f, i=i: f["tipi_documento"].pop(i), "Documenti: tipo eliminato")
                except Exception as ex:
                    st.error(f"Non sono riuscito a salvare: {ex}")
                else:
                    st.rerun()
        tutti_di_serie = [t for lst in CATALOGO_DOCUMENTI.values() for t in lst]
        nascosti = st.multiselect("Nascondi i tipi che non usi", tutti_di_serie, default=[t for t in (f.get("tipi_nascosti") or []) if t in tutti_di_serie],
                                  key="doc_nascosti")
        if st.button("Salva i tipi nascosti", key="doc_salva_nascosti"):
            try:
                _fa_salva(lambda f: f.__setitem__("tipi_nascosti", list(nascosti)), "Documenti: tipi nascosti")
            except Exception as ex:
                st.error(f"Non sono riuscito a salvare: {ex}")
            else:
                st.rerun()


# =====================================================================
# DOCUMENTI: FOTO DEL FRONTE E DEL RETRO (come nella dispensa: fotocamera posteriore o caricamento,
# sfondo tolto, raddrizzatura automatica e righello + cornice per ritoccare a mano)
# =====================================================================
import re as _re_doc
import hashlib as _hl_doc

_VERSIONE_FOTO_DOC = 1


def _fa_guida_avvisi():
    """Spiegazione passo per passo di Telegram ed email (info_sezioni.py). Se il file manca, non compare e il resto funziona."""
    if "guida_avvisi" in globals():
        try:
            guida_avvisi()
        except Exception:
            pass


def _fa_info(sezione):
    """Pulsante «Informazioni» con la guida a tendina (info_sezioni.py). Se il file manca, il pulsante non compare e il resto funziona."""
    if "pulsante_info" in globals():
        try:
            pulsante_info(sezione)
        except Exception:
            pass


def _doc_senza_scontorno(dati, lato=1600):
    """La foto intera, solo girata come l'ha scattata il telefono e ridotta: per quando il ritaglio automatico sbaglia."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGBA")
    img.thumbnail((lato, lato), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=88, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def _doc_scontorna(dati, lato=1600):
    """Come «scontorna_e_addrizza» della dispensa, ma l'immagine resta più grande (nei documenti si leggono scritte piccole).
    Maschera e angolo si calcolano su una copia ridotta (veloce), la rotazione e il ritaglio sull'immagine grande.
    Da una foto (bytes) a un WebP trasparente, ritagliato sul documento e addrizzato. Ritorna 'data:image/webp;base64,...'."""
    import cv2
    import numpy as np
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
    img.thumbnail((1800, 1800), Image.LANCZOS)
    rgb = np.array(img)
    h, w = rgb.shape[:2]
    sc = 1000.0 / max(h, w) if max(h, w) > 1000 else 1.0
    piccola = cv2.resize(rgb, (max(1, int(w * sc)), max(1, int(h * sc))), interpolation=cv2.INTER_AREA) if sc < 1 else rgb
    mask_p = _maschera_ai(piccola)
    if mask_p is None:                                                       # riserva: metodo senza modello
        bgr_p = cv2.cvtColor(piccola, cv2.COLOR_RGB2BGR)
        sc2 = 360.0 / max(bgr_p.shape[:2]) if max(bgr_p.shape[:2]) > 360 else 1.0
        mini = cv2.resize(bgr_p, (max(1, int(bgr_p.shape[1] * sc2)), max(1, int(bgr_p.shape[0] * sc2))), interpolation=cv2.INTER_AREA)
        mp = _maschera_prodotto(mini)
        if mp is not None:
            mask_p = cv2.resize(mp, (piccola.shape[1], piccola.shape[0]), interpolation=cv2.INTER_LINEAR)
            mask_p = cv2.GaussianBlur(mask_p, (0, 0), 1.6)
            mask_p = np.clip((mask_p.astype(np.float32) - 110) * 255 / 90, 0, 255).astype(np.uint8)
    if mask_p is None:
        rgba = np.dstack([rgb, np.full((h, w), 255, np.uint8)])
    else:
        mask = cv2.resize(mask_p, (w, h), interpolation=cv2.INTER_CUBIC) if sc < 1 else mask_p
        rgba = np.dstack([rgb, mask])
        ang = _angolo_totale(piccola, mask_p)
        if ang:
            diag = int(np.hypot(h, w)) + 4
            M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
            M[0, 2] += (diag - w) / 2
            M[1, 2] += (diag - h) / 2
            rgba = cv2.warpAffine(rgba, M, (diag, diag), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
        ys, xs = np.where(rgba[:, :, 3] > 40)
        if len(xs):
            marg = int(0.02 * max(xs.max() - xs.min(), ys.max() - ys.min()))
            y0, y1 = max(0, ys.min() - marg), min(rgba.shape[0], ys.max() + marg + 1)
            x0, x1 = max(0, xs.min() - marg), min(rgba.shape[1], xs.max() + marg + 1)
            rgba = rgba[y0:y1, x0:x1]
    out = Image.fromarray(rgba, "RGBA")
    out.thumbnail((lato, lato), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, "WEBP", quality=86, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def _doc_lavorata(dati, tieni_sfondo=False):
    """Scontorna e addrizza una sola volta per ogni foto (la scelta resta in memoria durante la sessione)."""
    mem = st.session_state.setdefault("_doc_lavorate", {})
    chiave = (hash(dati), bool(tieni_sfondo), _VERSIONE_FOTO_DOC)
    if chiave not in mem:
        if len(mem) >= 4:
            mem.pop(next(iter(mem)))
        try:
            mem[chiave] = _doc_senza_scontorno(dati) if tieni_sfondo else _doc_scontorna(dati)
        except Exception:
            mem[chiave] = _doc_senza_scontorno(dati)          # se qualcosa va storto resta la foto intera
    return mem[chiave]


def campo_foto_doc(chiave, titolo):
    """Un punto foto per il FRONTE o il RETRO di un documento: a sinistra «Scatta la foto» (fotocamera posteriore),
    a destra «Carica dal telefono». Ritorna la foto pronta ('data:image/webp;base64,...') oppure '' se non c'è."""
    st.markdown(f"**{titolo}**")
    with st.container(key="azioni_foto_" + chiave):
        c_cam, c_gal = st.columns(2, gap="small")
        premuto_cam = c_cam.button("📷 " + t("Scatta la foto"), key=f"scatta_{chiave}", width="stretch")
        premuto_gal = c_gal.button("📁 " + t("Carica dal telefono"), key=f"galleria_{chiave}", width="stretch")
    with st.container(key="nascosti_" + chiave):
        foto_cam = st.file_uploader("camera", type=["jpg", "jpeg", "png", "webp"], key=f"fotocam_{chiave}")
        foto_gal = st.file_uploader("galleria", type=["jpg", "jpeg", "png", "webp"], key=f"fotogal_{chiave}")
    if premuto_cam:
        st.session_state[f"{chiave}_fall_cam"] = True
    if premuto_gal:
        st.session_state[f"{chiave}_fall_gal"] = True
    fall_cam = st.camera_input(f"Scatta la foto: {titolo}", key=f"camfall_{chiave}") if st.session_state.get(f"{chiave}_fall_cam") else None
    fall_gal = st.file_uploader(t("Carica dal telefono"), type=["jpg", "jpeg", "png", "webp"], key=f"galfall_{chiave}") if st.session_state.get(f"{chiave}_fall_gal") else None

    # via di riserva sempre visibile: il normale campo di Streamlit (offre «Fotocamera» o «File» del telefono)
    with st.expander("🛟 La foto non arriva? Prova da qui"):
        st.caption("Tocca il campo qui sotto e scegli **Fotocamera** per scattare, oppure una foto già presente nel telefono.")
        foto_soc = st.file_uploader("Scegli o scatta la foto", type=["jpg", "jpeg", "png", "webp"],
                                    key=f"docsoc_{chiave}", label_visibility="collapsed")

    # tra le possibili foto vale l'ultima arrivata
    viste = st.session_state.setdefault(f"{chiave}_viste", {})
    ultima = st.session_state.get(f"{chiave}_ultima")
    candidati = {"cam": foto_cam, "gal": foto_gal, "fcam": fall_cam, "fgal": fall_gal, "soc": foto_soc}
    for nome, fl in candidati.items():
        if fl is None:
            viste.pop(nome, None)
            continue
        ident = getattr(fl, "file_id", None) or f"{fl.name}{fl.size}"
        if viste.get(nome) != ident:
            viste[nome] = ident
            ultima = nome
    st.session_state[f"{chiave}_ultima"] = ultima
    file = candidati.get(ultima) or next((fl for fl in candidati.values() if fl is not None), None)

    if file is None:
        st.session_state.pop(f"{chiave}_scartata", None)
        st.caption("Ancora nessuna foto: tocca uno dei due pulsanti.")
        return ""
    ident_f = f"{chiave}_{getattr(file, 'file_id', None) or file.name + str(file.size)}"
    if st.session_state.get(f"{chiave}_scartata") == ident_f:
        st.caption("Foto tolta. Tocca uno dei due pulsanti per sceglierne un'altra.")
        return ""
    st.caption(f"📥 Foto ricevuta: {file.name} ({file.size // 1024} KB)")
    tieni = st.checkbox("Tieni anche lo sfondo (se il documento viene tagliato male)", key=f"docsf_{ident_f}")
    with st.spinner("Sto togliendo lo sfondo e raddrizzando il documento… (può richiedere qualche secondo)"):
        automatica = _doc_lavorata(file.getvalue(), tieni)
    # editor come quello del telefono: righello per raddrizzare e cornice per tagliare
    nuova = automatica
    try:
        sigla = _hl_doc.md5((ident_f + str(tieni)).encode()).hexdigest()[:10]
        etichetta = f"ritocco{sigla}"
        with st.container(key="nascosti_rit_" + sigla):
            params = st.text_input(etichetta, key=f"rit_{sigla}", label_visibility="collapsed")
        _mostra_editor(_editor_html(automatica, etichetta))
        nuova = _ritocco_params(automatica, params)
        with st.expander("🛠️ " + t("Controlli di riserva"), expanded=False):
            grado = st.slider("↻ " + t("Gira (gradi): positivo = senso antiorario"), -30.0, 30.0, 0.0, 0.5, key=f"rot_{sigla}")
            c1, c2 = st.columns(2)
            sopra = c1.slider("⬆️ " + t("Taglia sopra (%)"), 0, 40, 0, key=f"ts_{sigla}")
            sotto = c2.slider("⬇️ " + t("Taglia sotto (%)"), 0, 40, 0, key=f"tb_{sigla}")
            sinistra = c1.slider("⬅️ " + t("Taglia a sinistra (%)"), 0, 40, 0, key=f"tl_{sigla}")
            destra = c2.slider("➡️ " + t("Taglia a destra (%)"), 0, 40, 0, key=f"tr_{sigla}")
        if grado or sopra or sotto or sinistra or destra:
            nuova = _ritocco(nuova, grado, sopra, sotto, sinistra, destra)
    except Exception as ex:                                      # l'editor non deve mai impedire di salvare la foto
        st.warning(f"L'editor di ritocco non è partito ({type(ex).__name__}); salvo la foto già sistemata in automatico.")
    st.markdown(foto_ampia_html(nuova), unsafe_allow_html=True)
    st.caption(f"✅ {titolo}: foto pronta. Sarà salvata quando tocchi «Salva il documento».")
    if st.button("🗑️ Togli questa foto", key=f"docscarta_{chiave}"):
        st.session_state[f"{chiave}_scartata"] = ident_f
        st.rerun()
    return nuova


# =====================================================================
# TESSERA SANITARIA E FASCICOLO SANITARIO (badge accanto alla dottoressa)
# =====================================================================
def _fa_tessera_del_profilo(f, pid):
    """Il documento «Tessera sanitaria» di questo profilo (se già inserito nei documenti) e i suoi file."""
    for x in f.get("documenti", []):
        if x.get("profilo", "p0") == pid and (x.get("tipo") or "").strip().lower() == "tessera sanitaria":
            return x, list(x.get("allegati") or [])
    return None, []


def _fa_url_valido(testo):
    """Ritorna il link sistemato (con https:// davanti se manca), '' se è vuoto, None se non sembra un indirizzo."""
    t_ = (testo or "").strip()
    if not t_:
        return ""
    if not re.match(r"^https?://", t_, re.I):
        t_ = "https://" + t_
    if not re.fullmatch(r"https?://[^\s/]+\.[^\s/]{2,}(/\S*)?", t_, re.I):
        return None
    return t_


def _fa_salva_link(pid, chiave, url):
    def _m(f):
        for p in f["profili"]:
            if p["id"] == pid:
                link = dict(p.get("link_sanitari") or {})
                if url:
                    link[chiave] = url
                else:
                    link.pop(chiave, None)
                p["link_sanitari"] = link
    _fa_salva(_m, "Farmacia: collegamenti sanitari")


@st.dialog("🪪 La mia tessera sanitaria", width="large")
def _fa_dialogo_tessera(pid):
    f = _fa_dati()
    _x, allegati = _fa_tessera_del_profilo(f, pid)
    immagini = [a for a in allegati if str(a.get("mime", "")).startswith("image/")]
    fronte = next((a for a in immagini if a["nome"].lower().startswith("fronte")), None) or (immagini[0] if immagini else None)
    retro = next((a for a in immagini if a["nome"].lower().startswith("retro")), None)
    if retro is None:
        altre = [a for a in immagini if a is not fronte]
        retro = altre[0] if altre else None
    for titolo, a in (("📄 Fronte", fronte), ("📄 Retro", retro)):
        st.markdown(f"**{titolo}**")
        if not a:
            st.caption("Non c'è ancora: puoi aggiungerla dalla scheda del documento, in I miei documenti.")
            continue
        d = carica_dati(crea_archivio(), _fa_percorso_doc(a["id"]))
        if d.get("b64"):
            st.image(base64.b64decode(d["b64"]))
        else:
            st.error("Non trovo questa immagine.")
    for a in allegati:                                            # eventuali PDF
        if not str(a.get("mime", "")).startswith("image/"):
            d = carica_dati(crea_archivio(), _fa_percorso_doc(a["id"]))
            if d.get("b64"):
                st.download_button("⬇ " + a["nome"], base64.b64decode(d["b64"]), file_name=a["nome"],
                                   mime=d.get("mime", "application/pdf"), key="fa_ts_pdf_" + a["id"], width="stretch")


def _fa_modulo_tessera(pid):
    f = _fa_dati()
    profili = _fa_profili(f)
    profilo = next((p for p in profili if p["id"] == pid), profili[0])
    link = profilo.get("link_sanitari") or {}

    if st.button("← Torna alla Farmacia", key="fa_ts_indietro"):
        st.session_state.pop("fa_modulo_tessera", None)
        st.rerun()
    st.subheader(f"🪪 Tessera sanitaria e fascicolo · {profilo.get('nome', '')}")

    # ------------------------------------------------ la tessera, presa dai documenti
    st.markdown("### 🪪 La mia tessera sanitaria")
    doc, allegati = _fa_tessera_del_profilo(f, pid)
    if allegati:
        if st.button("👁️ Mostra fronte e retro della tessera", type="primary", key="fa_ts_mostra", width="stretch"):
            _fa_dialogo_tessera(pid)
    else:
        if doc:
            st.warning("📌 Hai inserito il documento «Tessera sanitaria» ma senza foto. Aprilo in I miei documenti, "
                       "tocca Modifica e aggiungi la foto del **fronte** e del **retro**.")
        else:
            st.warning("📌 Non hai ancora inserito la tessera sanitaria. Vai in **I miei documenti**, tocca "
                       "**➕ Aggiungi un documento**, scegli **Tessera sanitaria** e fai la foto del fronte e del retro. "
                       "Questo avviso sparisce da solo appena l'hai inserita.")
        if st.button("📁 Vai a I miei documenti", key="fa_ts_vai_doc", width="stretch"):
            st.session_state.pop("fa_modulo_tessera", None)
            st.session_state["fa_profilo"] = pid
            st.session_state["sezione_home"] = "documenti"
            st.rerun()

    # ------------------------------------------------ i collegamenti online
    st.markdown("### 🔗 I miei collegamenti online")
    st.caption("Incolla l'indirizzo (link) della pagina e tocca **Salva**. Da quel momento basta toccare il pulsante per "
               "aprirla. Puoi cambiarlo o toglierlo quando vuoi.")
    with st.expander("❓ Come copio il link di una pagina?"):
        st.markdown("1. Apri la pagina nel browser (per esempio dal sito della tua Regione).\n"
                    "2. Tocca la **barra dell'indirizzo** in alto: il testo si seleziona tutto.\n"
                    "3. Tocca **Copia**.\n"
                    "4. Torna qui, tocca il campo e scegli **Incolla**.\n"
                    "5. Tocca **💾 Salva**.")
    campi = (("fse", "📂 Il mio fascicolo sanitario elettronico", "🔗 Apri il mio fascicolo sanitario"),
             ("vaccini", "💉 Le mie vaccinazioni online", "🔗 Apri le mie vaccinazioni"),
             ("spese", "🧾 Le mie spese sanitarie detraibili", "🔗 Apri le mie spese sanitarie"))
    for chiave, titolo, pulsante in campi:
        url = (link.get(chiave) or "").strip()
        k_mod = f"fa_ts_mod_{chiave}_{pid}"
        st.markdown(f"**{titolo}**")
        if url and not st.session_state.get(k_mod):
            c1, c2 = st.columns([3, 1.4], gap="small")
            c1.link_button(pulsante, url, type="primary", width="stretch")
            if c2.button("✏️ Modifica", key=f"fa_ts_btnmod_{chiave}_{pid}", width="stretch"):
                st.session_state[k_mod] = True
                st.rerun()
            continue
        with st.form(f"fa_ts_form_{chiave}_{pid}"):
            nuovo = st.text_input(titolo, value=url, placeholder="incolla qui il link, per esempio https://…",
                                  label_visibility="collapsed")
            b1, b2 = st.columns(2)
            salva_b = b1.form_submit_button("💾 Salva", type="primary", width="stretch")
            togli_b = b2.form_submit_button("🗑️ Togli il link" if url else "Annulla", width="stretch")
        if salva_b:
            valido = _fa_url_valido(nuovo)
            if valido is None:
                st.error("Il link non sembra corretto: copialo per intero dalla barra dell'indirizzo (di solito comincia con https://).")
            elif not valido:
                st.error("Il campo è vuoto: incolla il link e tocca Salva.")
            else:
                try:
                    _fa_salva_link(pid, chiave, valido)
                except Exception as ex:
                    st.error(f"Non sono riuscito a salvare: {ex}")
                else:
                    st.session_state.pop(k_mod, None)
                    st.session_state["fa_msg"] = "✅ Collegamento salvato."
                    st.rerun()
        elif togli_b:
            if url:
                try:
                    _fa_salva_link(pid, chiave, "")
                except Exception as ex:
                    st.error(f"Non sono riuscito a toglierlo: {ex}")
                    continue
                st.session_state["fa_msg"] = "🗑️ Collegamento tolto."
            st.session_state.pop(k_mod, None)
            st.rerun()


# =====================================================================
# DOCUMENTI: LETTURA AUTOMATICA (OCR con Tesseract) E COMPILAZIONE DEI CAMPI
# Serve il file packages.txt nel repository (tesseract-ocr e tesseract-ocr-ita). Se manca, la lettura non parte
# e l'app funziona come prima: i campi si compilano a mano. I campi letti restano sempre modificabili.
# =====================================================================
import shutil as _sh_doc
import subprocess as _sp_doc
import tempfile as _tmp_doc
import unicodedata as _ud_doc
import time as _tempo_doc

_MESI_DOC = {"GEN": 1, "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAG": 5, "MAY": 5, "GIU": 6, "JUN": 6, "LUG": 7, "JUL": 7,
             "AGO": 8, "AUG": 8, "SET": 9, "SEP": 9, "OTT": 10, "OCT": 10, "NOV": 11, "DIC": 12, "DEC": 12}


@st.cache_resource(show_spinner=False)
def _doc_ocr_lingue():
    """Le lingue di Tesseract da usare ('ita+eng', 'eng') oppure '' se Tesseract non c'è."""
    if not _sh_doc.which("tesseract"):
        return ""
    try:
        r = _sp_doc.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=15)
        elenco = set((r.stdout or "").split())
    except Exception:
        return ""
    if "ita" in elenco and "eng" in elenco:
        return "ita+eng"
    return "ita" if "ita" in elenco else ("eng" if "eng" in elenco else "")


def _doc_tesseract(img, psm):
    with _tmp_doc.TemporaryDirectory() as cartella:
        percorso = os.path.join(cartella, "doc.png")
        img.save(percorso)
        r = _sp_doc.run(["tesseract", percorso, "stdout", "-l", _doc_ocr_lingue(), "--psm", psm],
                        capture_output=True, text=True, timeout=45)
    return r.stdout or ""


def _doc_varianti_ocr(uri):
    """Le immagini da leggere, dalla più promettente: soglia adattiva ingrandita, colore, grigio.
    Sulle carte con fondo a righe (tessere, patenti) il testo si legge meglio dopo la soglia adattiva."""
    import cv2
    import numpy as np
    img = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("RGBA")
    fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    fondo.alpha_composite(img)
    rgb = fondo.convert("RGB")
    grigio = np.array(rgb.convert("L"))
    soglia = cv2.adaptiveThreshold(cv2.medianBlur(grigio, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 12)
    s = Image.fromarray(soglia)
    if s.width < 1800:
        s = s.resize((s.width * 2, s.height * 2), Image.LANCZOS)
    yield s, "6"
    yield rgb, "11"
    yield s, "11"
    yield Image.fromarray(grigio), "6"


def _doc_ocr_testo(uri, validi=None):
    """Il testo letto da una foto (data URI). Prova più varianti dell'immagine e si ferma appena capisce tipo, numero e scadenza.
    '' se Tesseract non c'è."""
    if not _doc_ocr_lingue() or not uri:
        return ""
    cache = st.session_state.setdefault("_doc_ocr_cache", {})
    chiave = hash(uri)
    if chiave in cache:
        return cache[chiave]
    inizio = _tempo_doc.time()
    testi = []
    for immagine, psm in _doc_varianti_ocr(uri):
        if testi and _tempo_doc.time() - inizio > 50:
            break
        try:
            testi.append(_doc_tesseract(immagine, psm))
        except Exception:
            continue
        if validi is not None:
            trovato = _doc_analizza("\n".join(testi), validi)
            if trovato.get("tipo") and trovato.get("numero") and trovato.get("scadenza"):
                break
    testo = "\n".join(testi)
    if len(cache) >= 6:
        cache.pop(next(iter(cache)))
    cache[chiave] = testo
    return testo


def _doc_norm(testo):
    t_ = _ud_doc.normalize("NFD", str(testo).upper())
    t_ = "".join(c for c in t_ if _ud_doc.category(c) != "Mn")
    return t_.replace("’", "'").replace("`", "'").replace("´", "'")


def _doc_date_trovate(t_):
    """[(posizione, data)] di tutte le date nel testo normalizzato: 31/12/2030, 31.12.2030, 31 12 2030, 31 DIC/DEC 2030."""
    t_ = re.sub(r"(?<![A-Z0-9])[0-9OIL|]{2}\s?[./\-]\s?[0-9OIL|]{2}\s?[./\-]\s?[0-9OIL|]{4}(?![A-Z0-9])",
                lambda m: m.group(0).replace("O", "0").replace("I", "1").replace("L", "1").replace("|", "1"), t_)
    trovate = []
    for m in re.finditer(r"(?<!\d)(\d{1,2})\s?[./\-]\s?(\d{1,2})\s?[./\-]\s?(\d{4})(?!\d)", t_):
        try:
            trovate.append((m.start(), date(int(m.group(3)), int(m.group(2)), int(m.group(1)))))
        except ValueError:
            pass
    for m in re.finditer(r"(?<!\d)(\d{1,2})\s*([A-Z]{3})[A-Z]*(?:\s*/\s*[A-Z]+)?\s*(\d{4})(?!\d)", t_):
        mese = _MESI_DOC.get(m.group(2))
        if mese:
            try:
                trovate.append((m.start(), date(int(m.group(3)), mese, int(m.group(1)))))
            except ValueError:
                pass
    return sorted(x for x in trovate if 1900 <= x[1].year <= 2100)


def _doc_etichetta_data(t_, pos):
    """Che cos'è la data che comincia in 'pos'? La parola chiave più vicina scritta subito prima: 'scad', 'ril' o 'nasc'."""
    prima = t_[max(0, pos - 45):pos]
    classi = {"scad": r"SCAD|EXPIR|VALID|FINO\s+AL|\b4\s?B\b",
              "ril": r"RILASC|EMISS|EMESS|ISSUE|\b4\s?A\b",
              "nasc": r"NAT[OA]\b|NASCITA|BIRTH"}
    migliore, fine = None, -1
    for nome, rx in classi.items():
        for m in re.finditer(rx, prima):
            if m.end() > fine:
                migliore, fine = nome, m.end()
    return migliore


def _doc_riconosci_tipo(t_, validi):
    regole = (
        (r"PATENTE\s+(DI\s+)?GUIDA|DRIVING\s+LICEN|PATENTE\s+DI\s+GUIDA", "Patente di guida"),
        (r"PASSAPORTO|PASSPORT", "Passaporto"),
        (r"TESSERA\s+SANITARIA|CARTA\s+NAZIONALE\s+DEI\s+SERVIZI|TESSERA\s+EUROPEA|MALATTIA|SSN\s?-?\s?MIN|MIN(ISTERO)?\s+SALUTE|DELLA\s+TESSERA", "Tessera sanitaria"),
        (r"CARTA\s+(D\s?['I]?\s?|DI\s+)IDENTIT", "Carta d'identità"),
        (r"PERMESSO\s+DI\s+SOGGIORNO", "Permesso di soggiorno"),
        (r"LIBRETTO\s+DI\s+CIRCOLAZIONE|CARTA\s+DI\s+CIRCOLAZIONE|CERTIFICATO\s+DI\s+PROPRIETA|CARTA\s+DI\s+CIRCOL", "Libretto / carta di circolazione"),
        (r"TESSERA\s+ELETTORALE", "Tessera elettorale"),
        (r"PORTO\s+D\s?['I]?\s?ARMI", "Porto d'armi"),
        (r"CODICE\s+FISCALE", "Codice fiscale"),
    )
    for rx, tipo in regole:
        if re.search(rx, t_) and tipo in validi:
            return tipo
    return None


_CF_DISPARI = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23]


def _doc_cf_valido(cf):
    if not re.fullmatch(r"[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]", cf):
        return False
    somma = 0
    for i, c in enumerate(cf[:15]):
        v = int(c) if c.isdigit() else ord(c) - 65
        somma += _CF_DISPARI[v] if i % 2 == 0 else v
    return chr(65 + somma % 26) == cf[15]


def _doc_trova_cf(testo):
    """Un codice fiscale (anche se l'OCR l'ha spezzato con spazi) il cui carattere di controllo è corretto, oppure None."""
    senza_spazi = re.sub(r"[^A-Z0-9]", "", testo)
    for i in range(len(senza_spazi) - 15):
        cand = senza_spazi[i:i + 16]
        if _doc_cf_valido(cand):
            class _R:
                def group(self, _n=0, _c=cand):
                    return _c
            return _R()
    return None


def _doc_numero_tessera(testo):
    """Il numero della tessera sanitaria: 20 cifre che cominciano per 8038 (l'OCR a volte le separa con spazi)."""
    for m in re.finditer(r"(?<!\d)(?:\d[ ]?){19}\d(?!\d)", testo):
        cifre = re.sub(r"\s", "", m.group(0))
        if cifre.startswith("8038"):
            return cifre
    return None


def _doc_analizza(testo, validi):
    """Dal testo letto ricava: tipo, numero, ente, rilascio, scadenza (date in formato ISO). Solo ciò che trova."""
    t_ = _doc_norm(testo)
    esito = {}
    tipo = _doc_riconosci_tipo(t_, validi)
    if tipo:
        esito["tipo"] = tipo
    # --- date
    date_t = _doc_date_trovate(t_)
    scad_l, ril_l, non_nasc = [], [], []
    for pos, d_ in date_t:
        et = _doc_etichetta_data(t_, pos)
        if et == "scad":
            scad_l.append(d_)
        elif et == "ril":
            ril_l.append(d_)
        elif et != "nasc":
            non_nasc.append(d_)
    oggi_ = oggi()

    def _moda(lst):                                            # la data scritta più volte; a parità la più recente
        conta = {}
        for d_ in lst:
            conta[d_] = conta.get(d_, 0) + 1
        top = max(conta.values())
        return max(d_ for d_, n in conta.items() if n == top)
    scad = _moda(scad_l) if scad_l else None
    ril = _moda(ril_l) if ril_l else None
    if not scad and non_nasc:
        futuri = [d_ for d_ in non_nasc if d_ >= date(oggi_.year - 1, oggi_.month, 1)]
        candidata = _moda(futuri) if futuri else (max(non_nasc) if len(set(non_nasc)) >= 2 else None)
        if candidata and (not ril or candidata > ril):
            scad = candidata
    if scad and not ril:
        possibili = [d_ for d_ in non_nasc if d_ < scad and (scad - d_).days <= 366 * 16]
        if possibili:
            ril = _moda(possibili)
    if scad and not (1990 <= scad.year <= oggi_.year + 25):
        scad = None
    if ril and not (1950 <= ril.year <= oggi_.year + 1):
        ril = None
    if scad:
        esito["scadenza"] = scad.isoformat()
    if ril and (not scad or ril < scad):
        esito["rilascio"] = ril.isoformat()
    # --- numero
    compatto = re.sub(r"[ \t]+", " ", t_)
    numero = None
    cf = _doc_trova_cf(t_)
    if tipo == "Patente di guida":
        m = re.search(r"\b[A-Z]{1,2}\s?\d{7}\s?[A-Z]\b", compatto)
        numero = m.group(0) if m else None
    elif tipo == "Carta d'identità":
        m = re.search(r"\bC[A-Z]\s?\d{5}\s?[A-Z]{2}\b", compatto) or re.search(r"\b[A-Z]{2}\s?\d{7}\b", compatto)
        numero = m.group(0) if m else None
    elif tipo == "Passaporto":
        m = re.search(r"\b[A-Z]{2}\s?\d{7}\b", compatto)
        numero = m.group(0) if m else None
    elif tipo == "Tessera sanitaria":
        numero = _doc_numero_tessera(compatto)
    elif tipo == "Codice fiscale":
        numero = cf.group(0) if cf else None
    if not tipo and "Tessera sanitaria" in validi and _doc_numero_tessera(compatto):
        tipo = "Tessera sanitaria"                                    # il numero di 20 cifre che comincia per 8038 è solo delle tessere
        esito["tipo"] = tipo
        numero = _doc_numero_tessera(compatto)
    if not numero and tipo != "Tessera sanitaria":
        m = re.search(r"(?:\bN\.?\s?|\bNR\.?\s?|N°\s?|\bNUMERO\s+|\bNUMBER\s+)[:.]?\s*([A-Z0-9]{6,16})\b", compatto)
        if m and re.search(r"\d", m.group(1)):
            numero = m.group(1)
    if numero:
        esito["numero"] = re.sub(r"\s+", "", numero) if tipo != "Tessera sanitaria" else re.sub(r"\s+", "", numero)
    # --- ente che ha rilasciato
    ente = None
    m = re.search(r"COMUNE\s+DI\s+([A-Z' ]{3,28})", t_)
    if m:
        ente = "Comune di " + m.group(1).strip().title()
    elif re.search(r"MIT\s?[-–]?\s?UCO|MOTORIZZAZIONE", t_):
        ente = "Motorizzazione civile (MIT-UCO)"
    else:
        m = re.search(r"(QUESTURA|PREFETTURA)\s+DI\s+([A-Z' ]{3,28})", t_)
        if m:
            ente = f"{m.group(1).title()} di {m.group(2).strip().title()}"
        elif re.search(r"MINISTERO\s+DELL'?\s?INTERNO", t_):
            ente = "Ministero dell'Interno"
        elif re.search(r"MINISTERO\s+DELL'?\s?ECONOMIA", t_):
            ente = "Ministero dell'Economia e delle Finanze"
        elif re.search(r"AGENZIA\s+DELLE\s+ENTRATE", t_):
            ente = "Agenzia delle Entrate"
    if ente:
        esito["ente"] = ente
    if cf:
        esito["cf"] = cf.group(0)
    return esito


def _doc_precompila(chiave_d, foto_fronte, foto_retro, validi):
    """Legge le foto (fronte e retro), mostra cosa ha capito e ritorna i valori da proporre nei campi del modulo."""
    lingue = _doc_ocr_lingue()
    st.markdown("**🔎 Lettura automatica del documento**")
    if not lingue:
        st.info("La lettura automatica non è ancora attiva (manca il file packages.txt nel repository, vedi le istruzioni). "
                "Intanto compila i campi qui sotto a mano.")
        return {}
    with st.spinner("Sto leggendo il documento… (qualche secondo)"):
        testo = ""
        for uri in (foto_fronte, foto_retro):
            if uri:
                try:
                    testo += "\n" + _doc_ocr_testo(uri, validi)
                except Exception:
                    pass
    esito = _doc_analizza(testo, validi) if testo.strip() else {}
    if esito and not esito.get("numero") and esito.get("cf"):          # ripiego: senza numero della tessera, il codice fiscale
        esito["numero"] = esito["cf"]
    if esito.get("cf") and esito.get("numero") != esito["cf"]:          # il codice fiscale letto finisce nelle note
        esito["note"] = f"Codice fiscale: {esito['cf']}"
    if not esito:
        st.warning("Non sono riuscito a leggere i dati da questa foto (prova con più luce e il documento ben dritto, "
                   "oppure compila a mano). La foto resta salvata.")
    else:
        righe = []
        if esito.get("tipo"):
            righe.append(f"**Tipo:** {esito['tipo']}")
        if esito.get("numero"):
            righe.append(f"**Numero:** {esito['numero']}")
        if esito.get("ente"):
            righe.append(f"**Rilasciato da:** {esito['ente']}")
        if esito.get("rilascio"):
            righe.append(f"**Rilascio:** {data_it(esito['rilascio'])}")
        if esito.get("scadenza"):
            righe.append(f"**Scadenza:** {data_it(esito['scadenza'])}")
        if esito.get("note"):
            righe.append(f"**Note:** {esito['note']}")
        st.success("✅ Ho letto questi dati e li ho scritti nei campi qui sotto. **Controllali e correggi se serve:**\n\n"
                   + "  \n".join(righe))
    if testo.strip():
        with st.expander("📝 Testo letto dalla foto", expanded=not esito):
            st.text(testo.strip()[:3000])
    return esito
