# -*- coding: utf-8 -*-
"""ANIMALI — la pagina: i sei bottoni in alto, la scelta dell'animale e le schede (Scheda, Salute, Documenti, Peso e cibo, Diario, Spese e contatti, Agenda,
Cartella completa, Report PDF, Esporta e importa). Avvisi nella Home, guida «Informazioni» e smistamento dalla pagina delle sezioni.
Caricato dopo animali.py, animali_doc.py, animali_report.py e animali_scambio.py."""
import html as _h_ap
from datetime import date, timedelta

import streamlit as st

_AN_SEZ = ["🐾 Scheda", "🩺 Salute", "📂 Documenti", "⚖️ Peso e cibo", "📔 Diario", "💶 Spese e contatti", "📅 Agenda", "🗃️ Cartella completa", "📄 Report PDF", "📦 Esporta e importa"]
_AN_SEZ_SOLO_SENZA_ANIMALI = ["📦 Esporta e importa"]
_AN_SALUTE = ["vaccini", "visite", "terapie", "esami", "interventi", "patologie", "allergie"]


def _an_scegli(label, voci, chiave):
    if st.session_state.get(chiave) not in voci:
        st.session_state.pop(chiave, None)
    if hasattr(st, "pills"):
        r = st.pills(label, voci, key=chiave, label_visibility="collapsed") if chiave in st.session_state else st.pills(label, voci, default=voci[0], key=chiave, label_visibility="collapsed")
    else:
        r = st.radio(label, voci, horizontal=True, key=chiave, label_visibility="collapsed")
    return r or voci[0]


def _an_vai(sezione, scope=None, modo=None, apri=None):
    """Callback dei bottoni: porta a una scheda (e dice se esportare/importare o aprire il caricamento)."""
    st.session_state["an_sezione"] = sezione
    if scope:
        st.session_state["an_scope"] = scope
    if modo:
        st.session_state["an_scambio_modo"] = modo
    if apri:
        st.session_state[apri] = True


def _an_torna_sezioni(dove):
    """Il bottone grande per tornare alla schermata iniziale con tutte le sezioni, in alto e in fondo alla pagina."""
    if "vm_vai_home" in globals():                                   # VitaMemo: la schermata iniziale con tutte le sezioni
        st.button("⬅️ Torna alle sezioni", key=f"an_torna_{dove}", width="stretch", on_click=vm_vai_home)
        return
    st.button("⬅️ Torna alle sezioni", key=f"an_torna_{dove}", width="stretch",
              on_click=(nav_vai if "nav_vai" in globals() else None), args=(("dispensa",) if "nav_vai" in globals() else None))


def _an_apri_nuovo():
    st.session_state["an_apri_nuovo"] = True


# ---------------------------------------------------------------------------------------------------------------------
# i sei bottoni principali e gli stessi strumenti dentro la scheda di un animale
# ---------------------------------------------------------------------------------------------------------------------
def _an_bottoni_principali():
    with st.container(key="an_top"):
        st.button("➕ Aggiungi animale", key="an_b_nuovo", type="primary", width="stretch", on_click=_an_apri_nuovo)
        st.button("🗃️ Visualizza cartella completa", key="an_b_cartella", width="stretch", on_click=_an_vai, args=("🗃️ Cartella completa", "tutti"))
        st.button("📎 Carica documenti", key="an_b_doc", width="stretch", on_click=_an_vai, args=("📂 Documenti", None, None, "an_doc_carica"))
        st.button("📄 Genera report PDF", key="an_b_report", width="stretch", on_click=_an_vai, args=("📄 Report PDF",))
        st.button("📦 Esporta tutto e condividi", key="an_b_esporta", width="stretch", on_click=_an_vai, args=("📦 Esporta e importa", "tutti", "Esporta"))
        st.button("📥 Importa archivio animale", key="an_b_importa", width="stretch", on_click=_an_vai, args=("📦 Esporta e importa", "tutti", "Importa"))


def _an_strumenti(x):
    """Gli stessi strumenti, limitati a UN animale (dentro la sua scheda)."""
    st.caption(f"Strumenti per {x.get('nome', '')}:")
    with st.container(key=f"an_tools_{x['id']}_{st.session_state.get('an_sezione', '')[:2]}"):
        st.button("📎 Carica documento", key=f"an_s_doc_{x['id']}", width="stretch", on_click=_an_vai, args=("📂 Documenti", None, None, "an_doc_carica"))
        st.button("🗃️ Cartella completa", key=f"an_s_cart_{x['id']}", width="stretch", on_click=_an_vai, args=("🗃️ Cartella completa", "uno"))
        st.button("📄 Genera report PDF", key=f"an_s_rep_{x['id']}", width="stretch", on_click=_an_vai, args=("📄 Report PDF",))
        st.button("📦 Esporta e condividi", key=f"an_s_exp_{x['id']}", width="stretch", on_click=_an_vai, args=("📦 Esporta e importa", "uno", "Esporta"))
        st.button("📥 Importa archivio", key=f"an_s_imp_{x['id']}", width="stretch", on_click=_an_vai, args=("📦 Esporta e importa", "uno", "Importa"))


# ---------------------------------------------------------------------------------------------------------------------
# foto
# ---------------------------------------------------------------------------------------------------------------------
def _an_riceve_file(n):
    """Il pulsante arancione + fotocamera + galleria (gli stessi di Auto e Casa): ritorna (nome, dati) quando un file arriva."""
    arr = None
    if "_ca_pannello_caricamento" in globals():
        if "_CA_CSS" in globals():
            st.markdown(_CA_CSS, unsafe_allow_html=True)
        up = _ca_pannello_caricamento(n, multi=False)
        if up is not None:
            arr = (up.name, up.getvalue())
        b = st.session_state.pop("ca_bozza_in", None)
        if b and b.get("dati"):
            arr = (b.get("nome") or "documento", b["dati"])
    else:
        up = st.file_uploader("Scegli il file", key=f"an_up_{n}")
        if up is not None:
            arr = (up.name, up.getvalue())
    return arr


def _an_pannello_foto(x):
    ctx = st.session_state.get("an_foto_ctx")
    if not ctx or ctx[1] != x["id"]:
        return
    st.markdown(f"<div class='an-card'><b class='t'>📷 {'Foto principale' if ctx[0] == 'principale' else 'Aggiungi alla galleria'} di {_an_e(x.get('nome'))}</b></div>", unsafe_allow_html=True)
    arr = _an_riceve_file(f"anfoto{st.session_state.get('an_giro', 0)}")
    if st.button("✖ Chiudi", key="an_foto_chiudi", width="stretch"):
        st.session_state.pop("an_foto_ctx", None)
        st.rerun()
    if not arr:
        return
    nome, dati = arr
    if an_mime_da_nome(nome, dati) not in ("image/jpeg", "image/png", "image/webp"):
        st.error("Per la foto serve un'immagine (JPG, PNG o WebP).")
        return
    try:
        rif = an_salva_originale(nome, dati, esistenti=([x["foto"]] if x.get("foto") else []) + list(x.get("galleria") or []))
    except Exception as ex:
        st.error(f"Non sono riuscito a salvare la foto: {ex}")
        return

    def _m(a):
        rec = an_trova(a, x["id"])
        if rec is not None:
            rif2 = {k: v for k, v in rif.items() if k != "doppione"}
            if ctx[0] == "principale":
                rec["foto"] = rif2
            elif not any(g.get("sha") == rif2.get("sha") for g in rec.setdefault("galleria", [])):
                rec["galleria"].append(rif2)
            rec["agg"] = _an_adesso()
    an_salva(_m, "Animali: foto")
    st.session_state["an_giro"] = st.session_state.get("an_giro", 0) + 1
    st.session_state.pop("an_foto_ctx", None)
    st.session_state["messaggio"] = "✅ Foto salvata (l'originale resta com'è)."
    st.rerun()


def _an_vai_foto(modo, aid):
    st.session_state["an_foto_ctx"] = (modo, aid)


# ---------------------------------------------------------------------------------------------------------------------
# le schede
# ---------------------------------------------------------------------------------------------------------------------
def _an_righe(coppie):
    h = "".join(f"<div class='an-riga'><b>{_an_e(k)}</b><span>{_an_e(v)}</span></div>" for k, v in coppie if v not in (None, "", False))
    st.markdown(f"<div class='an-card'>{h or 'Nessun dato.'}</div>", unsafe_allow_html=True)


def _an_eta(nascita):
    n = an_data(nascita)
    if not n:
        return ""
    o = _an_oggi()
    anni = o.year - n.year - ((o.month, o.day) < (n.month, n.day))
    if anni >= 1:
        return f"{anni} anni" if anni > 1 else "1 anno"
    mesi = (o.year - n.year) * 12 + o.month - n.month - (o.day < n.day)
    return f"{max(mesi, 0)} mesi"


def tab_an_scheda(a, x):
    _an_pannello_foto(x)
    uri = an_uri_foto(x.get("foto"), 700)
    if uri:
        st.markdown(f"<img class='an-foto' src='{uri}' alt='{_an_e(x.get('nome'))}'>", unsafe_allow_html=True)
    st.markdown(f"### {an_etichetta_animale(x)}")
    c1, c2 = st.columns(2, gap="small")
    c1.button("✏️ Modifica la scheda", key=f"an_edit_{x['id']}", width="stretch", on_click=lambda i=x["id"]: st.session_state.__setitem__("an_apri_mod", i))
    c2.button("📷 Foto principale", key=f"an_fp_{x['id']}", width="stretch", on_click=_an_vai_foto, args=("principale", x["id"]))
    st.button("🖼️ Aggiungi foto alla galleria", key=f"an_fg_{x['id']}", width="stretch", on_click=_an_vai_foto, args=("galleria", x["id"]))
    p = x.get("proprietario") or {}
    _an_righe([("Specie", x.get("specie")), ("Razza", x.get("razza")), ("Sesso", x.get("sesso")), ("Sterilizzato / castrato", "sì" if x.get("sterilizzato") else ""),
               ("Nata/o il", (an_data_it(x.get("nascita")) + (f" ({_an_eta(x['nascita'])})" if _an_eta(x.get("nascita")) else "")) if x.get("nascita") else ""),
               ("Colore e segni", x.get("colore")), ("Microchip", x.get("microchip")), ("Altri identificativi", x.get("tatuaggio")), ("Passaporto / libretto", x.get("passaporto")),
               ("Pedigree", x.get("pedigree")), ("Proprietario", p.get("nome")), ("Telefono", p.get("tel")), ("Email", p.get("email")), ("Indirizzo", p.get("indirizzo")),
               ("Annotazioni", x.get("note"))])
    gal = list(x.get("galleria") or [])
    if gal:
        st.markdown("**🖼️ Galleria**")
        cols = st.columns(3, gap="small")
        for i, g in enumerate(gal):
            u = an_uri_foto(g, 260)
            if u:
                cols[i % 3].markdown(f"<img class='an-mini' src='{u}'>", unsafe_allow_html=True)
                if cols[i % 3].button("🗑️", key=f"an_gdel_{x['id']}_{i}", width="stretch"):
                    _an_dialogo_elimina_foto(x["id"], g["id"])
    in_corso = [t for t in an_voci(a, "terapie", x["id"]) if an_terapia_attiva(t)]
    allergie = an_voci(a, "allergie", x["id"])
    if in_corso or allergie:
        st.markdown("**⚡ Da sapere subito**")
        for t in in_corso:
            _an_scheda_voce("terapie", t, a, modificabile=False)
        for t in allergie:
            _an_scheda_voce("allergie", t, a, modificabile=False)
    _an_strumenti(x)
    if st.button("🗑️ Elimina questo animale", key=f"an_elim_{x['id']}", width="stretch"):
        _an_dialogo_elimina("lista", x["id"], f"{x.get('nome', '')} e tutta la sua cartella (visite, vaccini, documenti…)")


@st.dialog("🗑️ Togliere la foto?")
def _an_dialogo_elimina_foto(aid, fid):
    st.warning("La foto viene tolta dalla galleria e il file eliminato.")
    if st.button("🗑️ Sì, togli", type="primary", key=f"an_fdel_si_{fid}", width="stretch"):
        def _m(a):
            rec = an_trova(a, aid)
            if rec is not None:
                rec["galleria"] = [g for g in rec.get("galleria") or [] if g.get("id") != fid]
        an_salva(_m, "Animali: foto tolta")
        an_cancella_file([fid])
        st.rerun()


def tab_an_salute(a, x):
    if "an_sal_sez" not in st.session_state:
        st.session_state["an_sal_sez"] = _AN_SALUTE[0]
    nomi = {c: AN_CATEGORIE[c]["titolo"] for c in _AN_SALUTE}
    sc = _an_scegli("Che cosa", [nomi[c] for c in _AN_SALUTE], "an_sal_sez_p")
    cat = next(c for c in _AN_SALUTE if nomi[c] == sc)
    st.markdown("<div class='an-card'><span class='an-badge vet'>👨‍⚕️ Veterinario</span> = scritto o prescritto dal veterinario (anche da un suo documento). "
                "<span class='an-badge prop'>✍️ Proprietario</span> = una mia annotazione. Nel report PDF restano separati.</div>", unsafe_allow_html=True)
    an_elenco(cat, a, x["id"], vuoto="Ancora niente: tocca «Aggiungi».")


def tab_an_peso(a, x):
    st.markdown("#### ⚖️ Andamento del peso")
    pesi = an_ordina(an_voci(a, "peso", x["id"]), "data", recenti_prima=False)
    punti = []
    for r in pesi:
        try:
            punti.append((str(r.get("data")), float(str(r.get("kg")).replace(",", "."))))
        except (ValueError, TypeError):
            pass
    if len(punti) >= 2:
        try:
            import pandas as pd
            df = pd.DataFrame({"kg": [p[1] for p in punti]}, index=[an_data_it(p[0]) for p in punti])
            st.line_chart(df, height=200)
        except Exception:
            pass
    an_elenco("peso", a, x["id"], vuoto="Segna ogni tanto il peso: qui vedi come va.")
    st.markdown("#### 🍖 Alimentazione")
    al = x.get("alimentazione") or {}
    k = f"an_al_{x['id']}_"
    tipo = st.text_input("Che cosa mangia (crocchette, umido, BARF, semi, insetti…)", value=al.get("tipo", ""), key=k + "tipo")
    marca = st.text_input("Marca o prodotto", value=al.get("marca", ""), key=k + "marca")
    quantita = st.text_input("Quanto e quante volte al giorno", value=al.get("quantita", ""), key=k + "q")
    integr = st.text_input("Integratori", value=al.get("integratori", ""), key=k + "int")
    nota = st.text_area("Note sull'alimentazione (cosa non può mangiare, dieta del veterinario…)", value=al.get("note", ""), key=k + "note", height=80)
    st.markdown("#### 🏠 Habitat e ambiente")
    ha = x.get("habitat") or {}
    h_desc = st.text_area("Dove vive (casa, giardino, gabbia, acquario, terrario…)", value=ha.get("descrizione", ""), key=k + "hd", height=80)
    h_par = st.text_input("Temperatura, umidità, luce, acqua (se servono)", value=ha.get("parametri", ""), key=k + "hp")
    if st.button("💾 Salva alimentazione e habitat", key=k + "salva", type="primary", width="stretch"):
        def _m(a2):
            rec = an_trova(a2, x["id"])
            if rec is not None:
                rec["alimentazione"] = {"tipo": tipo.strip(), "marca": marca.strip(), "quantita": quantita.strip(), "integratori": integr.strip(), "note": nota.strip()}
                rec["habitat"] = {"descrizione": h_desc.strip(), "parametri": h_par.strip()}
                rec["agg"] = _an_adesso()
        an_salva(_m, "Animali: alimentazione")
        st.session_state["messaggio"] = "✅ Salvato."
        st.rerun()


def tab_an_diario(a, x):
    an_elenco("diario", a, x["id"], vuoto="Il diario è vuoto: scrivi come sta, cosa ha fatto, cosa ti ha colpito.")


def tab_an_spese(a, x):
    voci = an_voci(a, "spese", x["id"])
    per_anno = {}
    for r in voci:
        try:
            per_anno[str(r.get("data") or "")[:4] or "senza data"] = per_anno.get(str(r.get("data") or "")[:4] or "senza data", 0.0) + float(str(r.get("importo") or 0).replace(",", "."))
        except (ValueError, TypeError):
            pass
    if per_anno:
        st.markdown("<div class='an-card'><b>Totale per anno:</b> " + " · ".join(f"{k}: {v:.2f} €".replace(".", ",") for k, v in sorted(per_anno.items(), reverse=True)) + "</div>", unsafe_allow_html=True)
    an_elenco("spese", a, x["id"], vuoto="Nessuna spesa segnata.")
    an_elenco("contatti", a, x["id"], vuoto="Aggiungi il veterinario, la clinica, il pronto soccorso: li trovi qui in un attimo.")


def tab_an_agenda(a, x):
    st.markdown("#### 📅 Agenda e promemoria")
    if st.button("➕ Aggiungi appuntamento", key=f"an_add_agenda_{x['id']}", type="primary", width="stretch"):
        _an_dialogo_voce("agenda", None, x["id"])
    voci = an_voci(a, "agenda", x["id"])
    da_fare = sorted([v for v in voci if not v.get("fatto")], key=lambda v: str(v.get("data")))
    fatte = sorted([v for v in voci if v.get("fatto")], key=lambda v: str(v.get("data")), reverse=True)
    oggi_ = _an_oggi()
    if not voci:
        st.caption("Niente in programma.")
    for r in da_fare:
        d_ = an_data(r.get("data"))
        scaduta = d_ and d_ < oggi_
        t, det = an_riassunto_voce("agenda", r)
        ritardo = "<span class='an-badge no'>in ritardo</span>" if scaduta else ""
        da_doc = "<span class='an-badge tipo'>📎 da documento</span>" if r.get("doc") else ""
        classe = "scad" if scaduta else ""
        st.markdown(f"<div class='an-card {classe}'><div class='t'>{_an_e(t)}</div><div>{ritardo}{da_doc}</div><div class='s'>{_an_e(det)}</div></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="small")
        c1.button("✅ Fatto", key=f"an_fatto_{r['id']}", width="stretch", on_click=_an_segna_fatto, args=(r["id"], True))
        if c2.button("✏️", key=f"an_mod_agenda_{r['id']}", width="stretch"):
            _an_dialogo_voce("agenda", r["id"], x["id"])
        if c3.button("🗑️", key=f"an_del_agenda_{r['id']}", width="stretch"):
            _an_dialogo_elimina("agenda", r["id"], t)
    if fatte:
        st.markdown("**Già fatti**")
        for r in fatte[:15]:
            t, det = an_riassunto_voce("agenda", r)
            st.markdown(f"<div class='an-card'><div class='t'>✅ {_an_e(t)}</div><div class='s'>{_an_e(det)}</div></div>", unsafe_allow_html=True)
            st.button("↩️ Rimetti da fare", key=f"an_ripr_{r['id']}", width="stretch", on_click=_an_segna_fatto, args=(r["id"], False))


def _an_segna_fatto(rid, stato):
    def _m(a):
        for r in a.get("agenda") or []:
            if r.get("id") == rid:
                r["fatto"] = stato
                r["agg"] = _an_adesso()
    an_salva(_m, "Animali: agenda")


# ---------------------------------------------------------------------------------------------------------------------
# la cartella completa
# ---------------------------------------------------------------------------------------------------------------------
_AN_TIPI_RIGA = {"vaccini": "💉 Vaccino", "visite": "🩺 Visita", "terapie": "💊 Terapia", "esami": "🔬 Esame", "interventi": "🏥 Intervento", "patologie": "🩻 Patologia",
                 "allergie": "⚠️ Allergia", "peso": "⚖️ Peso", "diario": "📔 Diario", "spese": "💶 Spesa", "agenda": "📅 Agenda", "documenti": "📂 Documento"}


def an_cronologia(a, aid):
    """Tutto ciò che riguarda l'animale in ordine di data (dal più recente): [(data_iso, categoria, voce)]."""
    righe = []
    for cat, chiave in (("vaccini", "data"), ("visite", "data"), ("terapie", "dal"), ("esami", "data"), ("interventi", "data"), ("patologie", "dal"), ("peso", "data"),
                        ("diario", "data"), ("spese", "data"), ("agenda", "data"), ("documenti", "data")):
        for r in an_voci(a, cat, aid):
            righe.append((str(r.get(chiave) or r.get("creato") or "")[:10], cat, r))
    for r in an_voci(a, "allergie", aid):
        righe.append((str(r.get("creato") or "")[:10], "allergie", r))
    return sorted(righe, key=lambda z: z[0], reverse=True)


def an_testo_voce(cat, r):
    """Tutto il testo di una voce (per la ricerca)."""
    parti = [str(v) for k, v in r.items() if isinstance(v, (str, int, float)) and k not in ("id", "animale", "creato", "agg")]
    if cat == "documenti":
        parti.append(str(r.get("testo") or ""))
        parti.extend(str(v) for v in (r.get("campi") or {}).values())
    return an_norm(" ".join(parti))


def tab_an_cartella(a, x):
    st.markdown(f"### 🗃️ Cartella di {_an_e(x.get('nome'))}")
    q = st.text_input("🔎 Cerca nella cartella (nome, farmaco, data, parole dei documenti…)", key=f"an_cerca_{x['id']}").strip()
    righe = an_cronologia(a, x["id"])
    tipi = sorted({c for _d, c, _r in righe})
    scelti = st.multiselect("Mostra solo", [_AN_TIPI_RIGA[t] for t in tipi], key=f"an_cart_tipi_{x['id']}")
    if q:
        nq = an_norm(q)
        righe = [z for z in righe if nq in an_testo_voce(z[1], z[2])]
    if scelti:
        righe = [z for z in righe if _AN_TIPI_RIGA[z[1]] in scelti]
    st.caption(f"{len(righe)} voci, dalla più recente.")
    for d_iso, cat, r in righe[:150]:
        if cat == "documenti":
            tit = r.get("titolo") or "Documento"
            det = " · ".join(z for z in (r.get("tipo"), an_data_it(r.get("data")), ("scade " + an_data_it(r["scadenza"])) if r.get("scadenza") else "") if z)
            st.markdown(f"<div class='an-card'><div class='t'>📂 {_an_e(tit)}</div><div class='s'>{_an_e(det)}</div></div>", unsafe_allow_html=True)
        else:
            t, det = an_riassunto_voce(cat, r)
            cl = "vet" if r.get("fonte") == "veterinario" else "prop" if r.get("fonte") == "proprietario" else ""
            st.markdown(f"<div class='an-card {cl}'><div class='s'>{_AN_TIPI_RIGA[cat]} · {an_data_it(d_iso)}</div><div class='t'>{_an_e(t)}</div>"
                        f"<div>{an_badge_fonte(r)}</div><div class='s'>{_an_e(det)}</div></div>", unsafe_allow_html=True)
    if len(righe) > 150:
        st.caption("Ci sono altre voci: usa la ricerca per trovarle.")
    st.markdown("#### 📂 Documenti originali")
    an_lista_documenti(a, x["id"], chiave="cart")
    _an_strumenti(x)


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def schermata_animali():
    """La pagina «Animali»."""
    if "nav_barra" in globals():
        nav_barra("animali")
    if "_CA_CSS" in globals():
        st.markdown(_CA_CSS, unsafe_allow_html=True)
    st.markdown(_AN_CSS, unsafe_allow_html=True)
    uri = ih_uri("animali.webp", 360) if "ih_uri" in globals() else ""
    if not uri and "_AN_LOGO_B64" in globals():
        uri = "data:image/webp;base64," + _AN_LOGO_B64
    ico = f"<img class='ico-img' alt='Animali' src='{uri}'>" if uri else "<div class='ico'>🐾</div>"
    st.markdown(f"<div class='an-hero'>{ico}<div><h1>I miei animali</h1><p>Schede, salute, documenti letti da soli, report per il veterinario ed esportazione completa</p></div></div>", unsafe_allow_html=True)
    if st.session_state.get("messaggio"):
        st.success(st.session_state.pop("messaggio"))
    _an_torna_sezioni("su")
    if "pulsante_info" in globals():
        try:
            pulsante_info("animali")
        except Exception:
            pass
    try:
        ripristinati = an_ripristina_interrotte()
        if ripristinati:
            st.warning(f"⚠️ Un'importazione precedente si era interrotta: ho rimesso a posto tutto (nessun dato tuo è stato toccato, tolti {ripristinati} file rimasti a metà).")
    except Exception:
        pass
    a = an_dati()
    lista = an_animali(a)
    _an_bottoni_principali()
    if st.session_state.pop("an_apri_nuovo", False):
        _an_dialogo_animale(None)
    mod = st.session_state.pop("an_apri_mod", None)
    if mod:
        _an_dialogo_animale(mod)
    if not lista:
        st.markdown("<div class='an-card'><div class='t'>🐾 Non c'è ancora nessun animale</div><div class='s'>Tocca «➕ Aggiungi animale», oppure «📥 Importa archivio animale» se qualcuno te ne ha mandato uno.</div></div>", unsafe_allow_html=True)
        if st.session_state.get("an_sezione") == "📦 Esporta e importa":
            an_tab_scambio(a, None)
        return
    # --- l'animale scelto
    etichette = {x["id"]: an_etichetta_animale(x) for x in lista}
    sel = st.session_state.get("an_sel")
    if sel not in etichette:
        sel = lista[0]["id"]
    if len(lista) > 1:
        st.session_state["an_sel_pill"] = etichette[sel]
        scelta = _an_scegli("Animale", list(etichette.values()), "an_sel_pill")
        sel = next((i for i, e in etichette.items() if e == scelta), sel)
    st.session_state["an_sel"] = sel
    x = an_trova(a, sel)
    if st.session_state.get("an_sezione_dopo"):
        st.session_state["an_sezione"] = st.session_state.pop("an_sezione_dopo")
    sezione = _an_scegli("Che cosa vuoi vedere?", _AN_SEZ, "an_sezione")
    if sezione == _AN_SEZ[0]:
        tab_an_scheda(a, x)
    elif sezione == _AN_SEZ[1]:
        tab_an_salute(a, x)
    elif sezione == _AN_SEZ[2]:
        an_tab_documenti(a, x)
    elif sezione == _AN_SEZ[3]:
        tab_an_peso(a, x)
    elif sezione == _AN_SEZ[4]:
        tab_an_diario(a, x)
    elif sezione == _AN_SEZ[5]:
        tab_an_spese(a, x)
    elif sezione == _AN_SEZ[6]:
        tab_an_agenda(a, x)
    elif sezione == _AN_SEZ[7]:
        tab_an_cartella(a, x)
    elif sezione == _AN_SEZ[8]:
        an_tab_report(a, x)
    else:
        an_tab_scambio(a, x)
    st.divider()
    _an_torna_sezioni("giu")


# ---- lo smistamento: «animali» va alla sua pagina (con il controllo dei permessi), il resto come prima
if "schermata_farmacia" in globals() and "_an_schermata_prima" not in globals():
    _an_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "animali":
            if "sv_nascoste" in globals() and "animali" in sv_nascoste():
                return sv_blocca("animali")
            return schermata_animali()
        return _an_schermata_prima()


# ---------------------------------------------------------------------------------------------------------------------
# avvisi nella Home: richiami, controlli, terapie che finiscono, appuntamenti, documenti in scadenza
# ---------------------------------------------------------------------------------------------------------------------
def an_scadenze(a, oggi_=None, entro=30):
    """[(giorni, testo)] di ciò che è in scadenza: richiami (anche in ritardo fino a un anno), prossimi controlli, terapie che finiscono entro 3 giorni, agenda, documenti."""
    oggi_ = oggi_ or _an_oggi()
    out = []

    def _g(iso):
        d_ = an_data(iso)
        return (d_ - oggi_).days if d_ else None

    def _quando(g):
        return f"in ritardo di {-g} giorni" if g < 0 else "oggi" if g == 0 else "domani" if g == 1 else f"tra {g} giorni"
    nomi = {x["id"]: x.get("nome") or "" for x in an_animali(a)}
    ultimi = {}
    for r in an_voci(a, "vaccini"):
        k = (r.get("animale"), an_norm(r.get("nome")), r.get("tipo"))
        if k not in ultimi or str(r.get("data") or "") >= str(ultimi[k].get("data") or ""):
            ultimi[k] = r
    for r in ultimi.values():
        g = _g(r.get("richiamo"))
        if g is not None and -365 <= g <= entro and r.get("animale") in nomi:
            out.append((g, f"🐾 {nomi[r['animale']]}: {str(r.get('tipo') or 'richiamo').lower()} {r.get('nome', '')} — {_quando(g)}"))
    for r in an_voci(a, "visite"):
        g = _g(r.get("prossimo"))
        if g is not None and -30 <= g <= 14 and r.get("animale") in nomi:
            out.append((g, f"🐾 {nomi[r['animale']]}: controllo veterinario — {_quando(g)}"))
    for r in an_voci(a, "terapie"):
        g = _g(r.get("al"))
        if g is not None and 0 <= g <= 3 and r.get("animale") in nomi:
            out.append((g, f"🐾 {nomi[r['animale']]}: la terapia {r.get('farmaco', '')} finisce {_quando(g)}"))
    for r in an_voci(a, "agenda"):
        g = _g(r.get("data"))
        if not r.get("fatto") and g is not None and -14 <= g <= 7 and r.get("animale") in nomi:
            out.append((g, f"🐾 {nomi[r['animale']]}: {r.get('titolo', 'appuntamento')} — {_quando(g)}"))
    for r in an_voci(a, "documenti"):
        g = _g(r.get("scadenza"))
        if g is not None and -60 <= g <= entro and r.get("animale") in nomi:
            out.append((g, f"🐾 {nomi[r['animale']]}: «{r.get('titolo', 'documento')}» scade — {_quando(g)}"))
    return sorted(out)


if "pn_scadenze" in globals() and "_an_scad_prima" not in globals():
    _an_scad_prima = pn_scadenze

    def pn_scadenze():                                               # noqa: F811
        out = _an_scad_prima()
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"])
            voci = an_scadenze(d.get("animali") or {})
            if voci:
                out = dict(out)
                out.setdefault("animali", []).extend(t for _g, t in voci)
        except Exception:
            pass
        return out


# ---------------------------------------------------------------------------------------------------------------------
# guida «Informazioni»
# ---------------------------------------------------------------------------------------------------------------------
if "_NOMI_SEZIONI" in globals() and "_GUIDE" in globals():
    _NOMI_SEZIONI.setdefault("animali", "🐾 Animali")
    if "UI_IT" in globals():
        UI_IT.setdefault("sez_animali", "🐾 Animali")              # il titolo della finestra «Informazioni»
    _GUIDE.setdefault("animali", [
        ("🐾 Cos'è la sezione Animali",
         """Qui tieni **la cartella completa di ogni animale di casa**: cani, gatti, conigli, uccelli, pesci, rettili… Si apre dal bottone **🐾 Animali**, accanto ad **Auto** e prima di **Chat**.
In alto ci sono sei bottoni: **➕ Aggiungi animale**, **🗃️ Visualizza cartella completa**, **📎 Carica documenti**, **📄 Genera report PDF**, **📦 Esporta tutto e condividi**, **📥 Importa archivio animale**.
Sotto scegli l'animale e cosa vedere: **Scheda**, **Salute** (vaccini, visite, terapie, esami, interventi, patologie, allergie), **Documenti**, **Peso e cibo**, **Diario**, **Spese e contatti**, **Agenda**.""",
         "animali animale cane gatto coniglio pappagallo pesce veterinario cartella sezione"),
        ("➕ Aggiungere un animale",
         """1. Apri **🐾 Animali** e tocca **➕ Aggiungi animale**.
2. Scrivi il **nome** (è l'unica cosa obbligatoria), la specie, la razza, il microchip e il proprietario. Il resto si può aggiungere dopo.
3. Tocca **✅ Salva**. Poi, dalla scheda, **📷 Foto principale** e **🖼️ Aggiungi foto alla galleria**.""",
         "aggiungere aggiungo inserire inserisco nuovo animale animali scheda foto microchip cane gatto coniglio criceto pappagallo animale domestico mio cucciolo"),
        ("📂 Documenti, certificati di vaccinazione e referti del cane e del gatto: li leggo io",
         """Tocca **📎 Carica documenti** e scegli la foto o il PDF (referto, certificato, prescrizione, fattura, libretto, passaporto…): puoi **scattare la foto**, prenderla **dalla galleria** o usare il **pulsante arancione**.
Leggo il documento, riconosco il **tipo**, trovo **date, scadenze, microchip, vaccini e importi**, e ti propongo **a quale animale** appartiene. **Se non sono sicuro te lo chiedo.** Controlli, correggi se serve, e conferma: il file **originale resta identico**.
Dopo si può **cercare** (anche nelle parole del documento), **correggere la classificazione**, **scaricare l'originale**, **inviare** o **esportare più documenti insieme**.""",
         "documenti documento animale animali cane gatto carica carico caricare referto certificato vaccinazione prescrizione fattura libretto passaporto classificazione leggere"),
        ("📄 Report PDF per il veterinario",
         """Tocca **📄 Genera report PDF**, scegli il tipo (**completo**, **sintetico**, **cronologico**, **vaccinazioni e prevenzione**, **farmaci e trattamenti**, **alimentazione e monitoraggio**, **personalizzato**, **completo con allegati**) e il periodo.
Il PDF ha **indice**, foto, dati dell'animale, **data di generazione** e di **ultimo aggiornamento** e l'elenco di ciò che **manca**. Le diagnosi e le prescrizioni del **veterinario** sono tenute **separate** dalle mie annotazioni. Si scarica o si invia come tutto il resto.""",
         "report pdf veterinario stampa clinica specialista consegnare"),
        ("📦 Esportare e importare un animale",
         """**📦 Esporta tutto e condividi** crea **un solo file** con tutto: dati, foto, documenti originali, spese, agenda. Scegli **un animale** o **tutti**; puoi metterci una **password**. Poi lo scarichi o lo mandi (WhatsApp, email, Telegram…).
Chi riceve il file apre **📥 Importa archivio animale** nella sua app: controllo che il file sia **intero e non danneggiato**, mostro **cosa contiene** e chiedo conferma. **Non sostituisco mai niente** di ciò che ha già: se c'è un animale uguale (stesso microchip o stesso nome) chiedo se **importarlo come nuovo**, **aggiornare**, **unire** o **annullare**. Se qualcosa si interrompe, rimetto tutto a posto.""",
         "esportare importare condividere pacchetto animale password duplicati"),
        ("🩺 Salute: vaccini, visite, terapie, esami",
         """Apri l'animale e tocca la scheda **🩺 Salute**. Ci sono sette parti: **vaccini**, **visite**, **terapie**, **esami**, **interventi**, **patologie** e **allergie**. Per ognuna tocca **➕ Aggiungi** e compila: la **data** e il **nome** bastano.
Ogni voce ha un badge che dice **chi l'ha scritta**: **👨‍⚕️ Veterinario** (per esempio letta da un referto) oppure **✍️ Proprietario** (le tue annotazioni). Nel report le due cose restano **separate**, così il veterinario vede cosa è stato diagnosticato e cosa hai solo osservato tu.
Nei **vaccini** puoi scrivere il **richiamo**: la data finisce nell'**Agenda** e, qualche giorno prima, compare un avviso nella **Home**. Con **✏️ Modifica** correggi, con **🗑️** elimini (te lo chiedo sempre prima).""",
         "salute vaccini richiamo visite terapie esami interventi patologie allergie veterinario proprietario annotazione"),
        ("⚖️ Peso e cibo, 📔 Diario, 💶 Spese, 📅 Agenda",
         """**⚖️ Peso e cibo**: scrivi il peso con la data e vedi il **grafico**; annota anche **cibo**, quantità e integratori.
**📔 Diario**: le osservazioni di ogni giorno (appetito, comportamento, sintomi), utili da leggere al veterinario.
**💶 Spese e contatti**: cosa hai speso (visite, farmaci, cibo, toelettatura) con il **totale**, e la rubrica di **veterinario, clinica, pensione, allevatore**.
**📅 Agenda**: appuntamenti e **scadenze** (richiami, controlli, antiparassitari). Quando carichi un documento con una scadenza, il promemoria lo **propongo io**.""",
         "peso grafico cibo alimentazione diario spese totale contatti rubrica agenda appuntamenti scadenze antiparassitario"),
        ("🗃️ Cartella completa",
         """Tocca **🗃️ Visualizza cartella completa** (o la scheda **🗃️ Cartella completa**): vedi **tutto insieme**, in ordine di data, per l'animale scelto o per **tutti**: vaccini, visite, terapie, esami, pesi, diario, spese e **documenti con i loro file originali**.
Puoi **filtrare** per tipo (**Mostra solo**) e **cercare una parola** (nome, farmaco, data o parole dei documenti). Ogni voce dice se viene dal **veterinario** o da te, e se ha **informazioni mancanti o poco leggibili** (il badge **da completare**).""",
         "cartella completa tutto insieme cronologia filtra cerca visualizza mancanti"),
        ("🛡️ Sicurezza: duplicati, conferme, annulla",
         """L'app **non cancella e non sostituisce mai niente da sola**. Prima di eliminare chiede sempre conferma. Quando importi un animale che **esiste già** (stesso microchip o stesso nome e specie) ti mostra le differenze e **tu scegli**: **importa come nuovo**, **aggiorna**, **unisci** o **annulla**.
Ogni cosa importata ha scritto **da dove arriva** e **quando** è stata importata. Se l'importazione si interrompe a metà, l'app **rimette tutto a posto**. E dopo un'importazione trovi il pulsante **↩️ Annulla l'ultima importazione**: toglie solo ciò che quell'importazione ha aggiunto.""",
         "sicurezza duplicati sovrascrivere conferma annulla importazione ripristino unisci aggiorna provenienza"),
        ("🔔 Avvisi e promemoria",
         """Richiami dei vaccini, controlli e scadenze scritte in **Agenda** compaiono come avvisi nella **Home** e sul pulsante **🐾 Animali** (la campanella con il numero). Il documento letto con una scadenza propone da solo il promemoria: tu lo confermi o lo togli.""",
         "avvisi promemoria scadenze campanella richiamo home notifiche"),
        ("❓ Se qualcosa non va",
         """**Il documento non è stato letto bene?** Aprilo da **📂 Documenti** → **✏️ Correggi**: cambi tipo, animale, date e testo; l'originale non cambia. Se la foto è storta o scura, rifalla con più luce e **tutta la pagina inquadrata**.
**Mi ha proposto l'animale sbagliato?** Scegli quello giusto prima di confermare (o dopo, con **Correggi**).
**Non trovo un documento?** Usa la ricerca nella scheda **📂 Documenti**: cerca anche dentro alle parole del documento.
**Il file esportato non si apre?** Si apre solo con **📥 Importa archivio animale** nell'app; se hai messo una password, serve la stessa.""",
         "problemi errore non funziona documento letto male correggi non trovo ricerca password file"),
    ])
    if "_ID_GUIDA" in globals():
        _ID_GUIDA.setdefault("animali", ["an_cosa", "an_aggiungi", "an_doc", "an_report", "an_scambio", "an_salute", "an_altre", "an_cartella", "an_sicurezza", "an_avvisi", "an_problemi"])
    if "_CTX_GUIDA" in globals():
        _CTX_GUIDA.setdefault("animali", "an_cosa")
