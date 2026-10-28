# -*- coding: utf-8 -*-
"""Volantini: il pulsante 🏷️ sulla scheda di ogni prodotto (a destra della quantita'). Si sceglie la citta', si apre la ricerca nei
siti dei volantini gia' compilata con prodotto e citta', e se si trova l'offerta la si mette nella lista della spesa con il nome
del supermercato / ipermercato / discount. Cerca nel Paese della lingua scelta (si può cambiare) e in qualunque citta'.
I paesi, le citta' di partenza e i siti dei volantini sono in ricerca_paesi.py. Caricato da app_dispensa.py dopo guida.py."""
import unicodedata
from urllib.parse import quote_plus

CATENE = {
    "Supermercato": ["Conad", "Coop", "Carrefour Market", "Carrefour Express", "Esselunga", "Pam", "Despar", "Eurospar", "Famila",
                     "Iperal", "Tigros", "Simply", "Sigma", "Crai", "Gros Cido", "DOK", "Unes", "Sidis", "Prix", "Alì"],
    "Ipermercato": ["Ipercoop", "Carrefour Iper", "Iper La grande i", "Interspar", "Bennet", "Il Gigante", "Panorama",
                    "Famila Superstore", "Conad Superstore", "Leclerc Conad", "Auchan"],
    "Discount": ["Lidl", "Eurospin", "MD", "Aldi", "Penny Market", "In's Mercato", "Todis", "Tuodì", "Dpiù", " Finiper"],
}
ICONE_TIPO = {"Supermercato": "🛒", "Ipermercato": "🏬", "Discount": "💸"}
CATENE["Discount"] = [x.strip() for x in CATENE["Discount"]]


def _slug(testo):
    s = unicodedata.normalize("NFKD", testo or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _link_ricerca(prodotto, citta, sito="", cc="IT"):
    parole = (PAESI.get(cc) or PAESI["IT"])["offerta"] if "PAESI" in globals() else "offerta volantino"
    q = f"{prodotto} {parole} {citta}".strip()
    if sito:
        q += f" site:{sito}"
    return "https://www.google.com/search?q=" + quote_plus(q)


def _dove(x):
    """Testo 'Lidl · Torino · 1,29 € · fino al 31/10' per la lista della spesa."""
    pezzi = [x.get("negozio") or "", x.get("citta") or ""]
    if x.get("prezzo"):
        pezzi.append(f"{float(x['prezzo']):.2f}".replace(".", ",") + " €")
    if x.get("valido_fino"):
        try:
            pezzi.append("fino al " + date.fromisoformat(x["valido_fino"]).strftime("%d/%m"))
        except Exception:
            pass
    return " · ".join(p for p in pezzi if p)


def _aggiungi_offerta(d, r, negozio, tipo, citta, prezzo, valido, cc="IT"):
    """Mette il prodotto nella lista della spesa con il negozio. False se c'e' gia' la stessa offerta."""
    lista = d.setdefault("spesa", [])
    chiave = _chiave_prodotto(r)
    for x in lista:
        if (_chiave_prodotto(x) == chiave and not x.get("preso") and (x.get("negozio") or "").lower() == negozio.lower()
                and (x.get("citta") or "").lower() == citta.lower()):
            return False
    lista.append({"id": uuid.uuid4().hex[:10], "nome": r.get("nome", ""), "marca": r.get("marca", ""), "barcode": r.get("barcode", ""),
                  "per_chi": r.get("per_chi", "adulti"), "preso": False, "aggiunto_il": datetime.now().isoformat(timespec="seconds"),
                  "negozio": negozio, "tipo_negozio": tipo, "citta": citta, "prezzo": float(prezzo) if prezzo else None,
                  "valido_fino": valido.isoformat() if valido else None, "fonte": "volantino"})
    d["citta_volantini"] = citta
    d["citta_volantini_paese"] = cc
    return True


def apri_volantini(rid):
    """Il pulsante 🏷️: finestra con la ricerca nei volantini e l'inserimento nella lista della spesa."""
    giro = st.session_state["vol_giro"] = st.session_state.get("vol_giro", 0) + 1

    def _finestra():
        dati_ = carica_dati(crea_archivio(), st.session_state["percorso"])
        r = next((x for x in dati_.get("articoli", []) if x["id"] == rid), None)
        if r is None:
            st.info(t("Prodotto non trovato."))
            return
        K = lambda nome: f"vol_{giro}_{nome}_{rid}"
        _nome_p, _marca_p = (r.get("nome") or "").strip(), (r.get("marca") or "").strip()
        prodotto = _nome_p if (not _marca_p or _marca_p.lower() in _nome_p.lower()) else f"{_nome_p} {_marca_p}"
        st.markdown(f"**🏷️ {html.escape(prodotto)}**")
        cc = rp_selettore() if "rp_selettore" in globals() else "IT"           # parte dal Paese della lingua; si può cambiare
        P = PAESI.get(cc) or PAESI["IT"]
        salvata = dati_.get("citta_volantini", "")
        di_partenza = salvata if (salvata and dati_.get("citta_volantini_paese", "IT") == cc) else P["citta"]
        citta = st.text_input(rp_t("v_citta"), value=di_partenza, key=K("citta_" + cc), placeholder=rp_t("dove_ph", citta=P["citta"])).strip()

        st.markdown(rp_t("v_cerca_h"))
        st.caption(rp_t("v_cap"))
        if not citta:
            st.info(rp_t("v_scrivi_citta"))
        else:
            st.link_button(rp_t("v_cerca_btn", citta=citta), _link_ricerca(prodotto, citta, "", cc), width="stretch")
            siti = P["siti"]
            for k in range(0, len(siti), 2):
                for colonna, (nome_sito, dominio) in zip(st.columns(2), siti[k:k + 2]):
                    colonna.link_button(nome_sito, _link_ricerca(prodotto, citta, dominio, cc), width="stretch")
            if cc == "IT" and _slug(citta):
                st.link_button(rp_t("v_tutti", citta=citta), f"https://www.doveconviene.it/{_slug(citta)}/iper-e-super", width="stretch")
            else:
                st.link_button(rp_t("v_tutti", citta=citta), "https://www.google.com/search?q=" + quote_plus(f"{P['tutti']} {citta}"),
                               width="stretch")

        st.markdown("**2️⃣ L'hai trovato in offerta? Mettilo nella lista della spesa**")
        catene = P.get("catene") or CATENE
        tipo = st.radio("Dove", list(catene), horizontal=True, key=K("tipo_" + cc), format_func=lambda x: ICONE_TIPO[x] + " " + rp_t("v_tipo_" + x),
                        label_visibility="collapsed")
        scelta = st.selectbox("Nome del negozio", catene[tipo] + ["Altro (scrivo il nome)"], key=K("neg_" + cc + "_" + tipo))
        negozio = st.text_input("Scrivi il nome del negozio", key=K("neg_altro")).strip() if scelta.startswith("Altro") else scelta
        p1, p2 = st.columns(2)
        prezzo = p1.number_input("💶 Prezzo in offerta (facoltativo)", min_value=0.0, step=0.05, format="%.2f", key=K("prezzo"))
        con_data = p2.checkbox("Indico fino a quando vale", key=K("condata"))
        valido = st.date_input("Valido fino al", value=date.today(), format="DD/MM/YYYY", key=K("valido")) if con_data else None
        if st.button("🛒 Aggiungi alla lista della spesa", type="primary", key=K("ok"), width="stretch"):
            if not citta:
                st.error("Scrivi la città.")
            elif not negozio:
                st.error("Scrivi il nome del negozio.")
            else:
                esito = {}
                try:
                    salva(lambda d: esito.update(ok=_aggiungi_offerta(d, r, negozio, tipo, citta, prezzo, valido, cc)), "Spesa: offerta " + (r.get("nome") or ""))
                    if esito.get("ok"):
                        st.session_state["messaggio"] = f"🛒 {r.get('nome', '')}: messo nella lista della spesa ({negozio}, {citta})."
                    else:
                        st.session_state["messaggio"] = "È già nella lista della spesa per questo negozio."
                    st.rerun()
                except Exception as e:
                    st.error(t("Non sono riuscito a salvare: {e}", e=e))

    st.dialog(rp_t("v_titolo") if "rp_t" in globals() else "🏷️ Offerte nei volantini", width="large")(_finestra)()


# ---------------------------------------------------------------------
# il pulsante sulla scheda, a destra della quantita'
# ---------------------------------------------------------------------
_scheda_html_prima_vol = scheda_html


def scheda_html(r, data_oggi, mie):
    h = _scheda_html_prima_vol(r, data_oggi, mie)
    chip = f"<span class='vol-chip' data-vol='{html.escape(str(r.get('id', '')), quote=True)}' role='button' tabindex='0'>🏷️ Volantini</span>"
    if "<div class='riga-qv'>" in h:
        return h.replace("<div class='riga-qv'>", "<div class='riga-qv'>" + chip, 1)
    return re.sub(r"(<div class='quantita'>.*?</div>)", lambda m: f"<div class='riga-qv'>{m.group(1)}{chip}</div>", h, count=1, flags=re.S)


CSS = CSS.replace("</style>", """
.vol-chip{order:99;margin-left:auto;display:inline-flex;align-items:center;gap:6px;padding:7px 16px;border-radius:999px;cursor:pointer;
 font-weight:800;color:#fff;text-shadow:0 1px 1px rgba(0,0,0,.4);border:2px solid #7c3f00;
 background:linear-gradient(#ffd180,#ffa726 50%,#e65100);box-shadow:0 3px 0 #8a3b00,0 6px 10px rgba(0,0,0,.25),inset 0 2px 2px rgba(255,255,255,.6);
 user-select:none;-webkit-tap-highlight-color:transparent}
.vol-chip:active{transform:translateY(2px);box-shadow:0 1px 0 #8a3b00}
</style>""")
