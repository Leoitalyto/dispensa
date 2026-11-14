# -*- coding: utf-8 -*-
"""NAVIGAZIONE CHIARA E FRECCIA «TORNA SU».

1) nav_pagine(corrente): sei bottoni grandi, con la scritta dentro ben leggibile e un colore intenso per ogni pagina
   (Dispensa verde, Salute rosso, I miei documenti azzurro, Archivio indaco, Casa arancione, Utilità viola).
   Compare sotto il titolo della Dispensa e in cima a ogni sezione (al posto delle vecchie frecce ← →).
   La pagina in cui ti trovi ha un bordo bianco e un pallino. Le sezioni nascoste a una persona («Sezioni visibili») non compaiono.
2) pn_freccia_su(): una piccola freccia tonda, trasparente, che compare solo quando si scorre in basso e riporta in cima con un tocco.
   Sta a DESTRA (predefinito) o a SINISTRA, a scelta, sopra l'assistente e i pulsanti in basso, per non coprire le scritte.
   La scelta si fa in Utilità → «⚙️ Aspetto dell'app» e si ricorda per ogni persona.
Caricato da app_dispensa.py dopo sezioni.py."""
import json
from datetime import date

import streamlit as st

_PN_VOCI = [
    ("dispensa", "🏠 Dispensa", "#2ec4a6", "#00695c"),
    ("salute", "🩺 Salute", "#ff6f60", "#b71c1c"),
    ("documenti", "📁 I miei documenti", "#42b0ff", "#01579b"),
    ("archivio", "🗂️ Archivio", "#7986cb", "#283593"),
    ("casa", "🏡 Casa", "#ffb74d", "#d84315"),
    ("lavoro", "💼 Lavoro", "#90a4ae", "#37474f"),
    ("auto", "🚗 Auto", "#4dd0e1", "#006064"),
    ("utilita", "🧰 Utilità", "#c46bdc", "#4a148c"),
]


_PN_TESTI = {"normale": 100, "grande": 115, "molto grande": 130}


def pn_testo():
    """La grandezza dei testi scelta da questa persona (si ricorda): normale, grande, molto grande."""
    if "pn_testo" not in st.session_state:
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"])
            v = (d.get("impostazioni") or {}).get("testo", "normale")
        except Exception:
            v = "normale"
        st.session_state["pn_testo"] = v if v in _PN_TESTI else "normale"
    return st.session_state["pn_testo"]


def _pn_css_testo():
    pct = _PN_TESTI.get(pn_testo(), 100)
    if pct == 100:
        return ""
    return (f"<style>html{{font-size:{pct}% !important}} .stButton button,.stDownloadButton button,[data-testid='stLinkButton'] a{{min-height:3rem !important}} "
            "[data-testid='stTabs'] button{min-height:3rem}</style>")


def _pn_css(corrente, lampeggiano=()):
    r = ["<style>"
         ".st-key-nav_pagine[data-testid='stVerticalBlock'],.st-key-nav_pagine [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:1fr 1fr;gap:9px !important;margin:6px 0 12px}"
         ".st-key-nav_pagine button{width:100% !important;min-height:58px !important;border-radius:18px !important;color:#fff !important;font-weight:900 !important;"
         "border:2px solid rgba(255,255,255,.55) !important;box-shadow:0 4px 0 rgba(0,0,0,.25) !important;padding:6px 8px !important}"
         ".st-key-nav_pagine button p{color:#fff !important;font-weight:900 !important;font-size:1.04rem !important;line-height:1.15 !important;text-shadow:0 1px 3px rgba(0,0,0,.55);margin:0}"
         ".st-key-nav_pagine button:active{transform:translateY(2px);box-shadow:0 2px 0 rgba(0,0,0,.25) !important}"]
    for sez, _, c1, c2 in _PN_VOCI:
        r.append(f".st-key-navp_{sez} button,.st-key-navpa_{sez} button{{background:linear-gradient(135deg,{c1} 0%,{c2} 100%) !important}}")
        r.append(f".st-key-navpa_{sez} button{{outline:3px solid #fff !important;outline-offset:-5px;box-shadow:0 0 0 3px {c2},0 5px 0 rgba(0,0,0,.3) !important}}")
    r.append("@keyframes pn-lampeggia{0%,100%{filter:brightness(1);box-shadow:0 4px 0 rgba(0,0,0,.25),0 0 0 0 rgba(255,235,59,0)}"
             "50%{filter:brightness(1.3);box-shadow:0 4px 0 rgba(0,0,0,.25),0 0 16px 7px rgba(255,235,59,.95)}}")
    for sez in lampeggiano:                                         # le sezioni con cose in scadenza lampeggiano, appena si apre la pagina
        r.append(f".st-key-navp_{sez} button,.st-key-navpa_{sez} button{{animation:pn-lampeggia 1.15s ease-in-out infinite;outline:3px solid #ffeb3b !important;outline-offset:-5px}}")
    r.append("@media (prefers-reduced-motion:reduce){.st-key-nav_pagine button{animation:none !important}}")
    r.append("@media (max-width:340px){.st-key-nav_pagine[data-testid='stVerticalBlock'],.st-key-nav_pagine [data-testid='stVerticalBlock']{grid-template-columns:1fr}}</style>")
    return "".join(r)


def _pn_giorni(iso, oggi_):
    try:
        return (date.fromisoformat(str(iso)[:10]) - oggi_).days
    except (ValueError, TypeError):
        return None


def _pn_quando(g):
    return f"scaduto da {-g} giorni" if g < 0 else "scade oggi" if g == 0 else "scade domani" if g == 1 else f"scade tra {g} giorni"


def pn_scadenze():
    """Cosa c'è in scadenza, per sezione: {sezione: [testo, …]}. Dispensa, Salute (medicinali, ricette, visite, richiami, controlli), documenti personali e Casa (bollette, garanzie, manutenzioni)."""
    out = {}
    try:
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
        oggi_ = oggi()
    except Exception:
        return out
    try:
        for a in d.get("articoli", []):
            stato, g = stato_scadenza(a.get("scadenza"), oggi_)
            if stato in ("scaduto", "rosso", "arancione"):
                out.setdefault("dispensa", []).append(f"🥫 {a.get('nome', 'Prodotto')}: {_pn_quando(g)}")
        f = d.get("farmacia") or {}
        for m in f.get("medicinali", []):
            g = _pn_giorni(m.get("scadenza"), oggi_)
            if g is not None and g <= 60:
                out.setdefault("salute", []).append(f"💊 {m.get('nome', 'Medicinale')}: {_pn_quando(g)}")
        for x in f.get("prescrizioni", []):
            g = _pn_giorni(x.get("valida_fino"), oggi_)
            if g is not None and g <= 14 and x.get("stato") != "Usata":
                out.setdefault("salute", []).append(f"📝 Prescrizione {str(x.get('tipo', '')).lower()}: {_pn_quando(g)}")
        for x in f.get("visite", []):
            for chiave in ("prossimo", "data"):
                g = _pn_giorni(x.get(chiave), oggi_)
                if g is not None and 0 <= g <= 7:
                    out.setdefault("salute", []).append(f"📅 {x.get('categoria', 'Visita')}: " + ("oggi" if g == 0 else "domani" if g == 1 else f"tra {g} giorni"))
                    break
        for x in f.get("vaccinazioni", []):
            g = _pn_giorni(x.get("richiamo"), oggi_)
            if g is not None and -365 <= g <= 30:
                out.setdefault("salute", []).append(f"💉 Richiamo {x.get('nome', '')}: " + ("in ritardo di %d giorni" % -g if g < 0 else "oggi" if g == 0 else f"tra {g} giorni"))
        if "sp_esenzioni_scadenti" in globals():                                  # invalidità ed esenzioni: scadute o in scadenza entro 60 giorni
            for p in (f.get("profili") or []):
                for g, e in sp_esenzioni_scadenti(p, oggi_, 60):
                    out.setdefault("salute", []).append(f"🪪 {se_titolo(e)}" + (f" ({p.get('nome', '')})" if len(f.get("profili") or []) > 1 else "") + ": " + ("scaduta da %d giorni" % -g if g < 0 else "oggi" if g == 0 else f"scade tra {g} giorni"))
        if "scorta_in_esaurimento" in globals():                                   # medicinali che stanno per finire (e ricetta non ancora chiesta)
            try:
                for nome_p, nome_m, g, _stt in scorta_in_esaurimento(f, oggi_):
                    out.setdefault("salute", []).append(f"💊 {nome_m}" + (f" ({nome_p})" if len(f.get("profili") or []) > 1 else "") + ": " + ("finito" if g < 0 else "finisce oggi" if g == 0 else f"finisce tra {g} giorni"))
            except Exception:
                pass
        if "sp_controlli_scadenti" in globals():
            for p in (f.get("profili") or []):
                for g, c in sp_controlli_scadenti(p, oggi_, 30):
                    out.setdefault("salute", []).append(f"⏰ {c.get('nome', 'Controllo')}" + (f" ({p.get('nome', '')})" if len(f.get("profili") or []) > 1 else "") + ": " + ("in ritardo di %d giorni" % -g if g < 0 else "oggi" if g == 0 else f"tra {g} giorni"))
        for x in f.get("documenti", []):
            g = _pn_giorni(x.get("scadenza"), oggi_)
            if g is not None and g <= 90 and not x.get("senza_scadenza"):
                out.setdefault("documenti", []).append(f"📄 {x.get('tipo', 'Documento')}: {_pn_quando(g)}")
        if "au_scadenze_avviso" in globals():                                     # Auto: bollo, assicurazione, revisione, garanzie, tagliando, gomme (scadute o entro 30 giorni)
            for _g, _txt in au_scadenze_avviso(d.get("auto") or {}, oggi_, 30):
                out.setdefault("auto", []).append(_txt)
        if "ca_scadenze" in globals():
            c = d.get("casa") or {}
            for k in ("beni", "documenti", "manutenzioni"):
                c.setdefault(k, [])
            sc = ca_scadenze(c, oggi_)
            for nome, g in sc.get("garanzie", []):
                out.setdefault("casa", []).append(f"🛠️ Garanzia {nome}: " + ("scade tra %d giorni" % g))
            for nome, voce, g in sc.get("manutenzioni", []):
                out.setdefault("casa", []).append(f"🔧 {nome} · {voce}: " + ("in ritardo di %d giorni" % -g if g < 0 else "oggi" if g == 0 else f"tra {g} giorni"))
            for nome, g, imp in sc.get("spese", []):                                  # rate dell'amministrazione
                out.setdefault("casa", []).append(f"🏢 {nome}: " + ("scaduta da %d giorni" % -g if g < 0 else "da pagare oggi" if g == 0 else f"da pagare entro {g} giorni"))
            for nome, g, imp in sc.get("bollette", []):
                out.setdefault("casa", []).append(f"💶 {nome}: " + ("scaduta da %d giorni" % -g if g < 0 else "da pagare oggi" if g == 0 else f"da pagare entro {g} giorni"))
    except Exception:
        pass
    return out


def pn_riepilogo():
    """Sulla Home, sotto i bottoni: «Ci sono N cose da guardare», sezione per sezione (oppure «Tutto a posto»)."""
    nasc = sv_nascoste() if "sv_nascoste" in globals() else set()
    sc = {k: v for k, v in pn_scadenze().items() if k not in nasc}
    nomi = {sez: etichetta for sez, etichetta, _a, _b in _PN_VOCI}
    tot = sum(len(v) for v in sc.values())
    if not tot:
        st.markdown("<div style='background:rgba(255,255,255,.8);border-radius:16px;padding:8px 14px;margin:8px 0;color:#1b5e20;font-weight:800'>✅ Tutto a posto: niente in scadenza.</div>", unsafe_allow_html=True)
        return
    righe = ""
    for sez in ("dispensa", "salute", "documenti", "casa", "auto", "animali"):
        if sez in sc:
            voci = sc[sez]
            righe += f"<div style='margin-top:6px'><b>{nomi.get(sez, sez)}</b> ({len(voci)})</div>" + "".join(f"<div style='margin-left:10px'>{_pn_h(v)}</div>" for v in voci[:3])
            if len(voci) > 3:
                righe += f"<div style='margin-left:10px;opacity:.8'>…e altre {len(voci) - 3}: apri la sezione per vederle</div>"
    st.markdown("<div style='background:rgba(255,248,225,.95);border:2px solid #ffb300;border-radius:18px;padding:10px 14px;margin:8px 0;color:#4e342e'>"
                f"<div style='font-weight:900;font-size:1.05rem'>🔔 Ci sono {tot} {'cosa' if tot == 1 else 'cose'} da guardare</div>"
                "<div style='font-size:.85rem;opacity:.9'>I bottoni che lampeggiano ti dicono dove: toccali per aprire.</div>" + righe + "</div>", unsafe_allow_html=True)


def _pn_h(t):
    import html as _hh
    return _hh.escape(str(t))


def nav_pagine(corrente):
    """I bottoni colorati per passare da una pagina all'altra; quelli con cose in scadenza lampeggiano e dicono quante."""
    if "nu_aggiorna_sessione" in globals():                           # se l'amministratore ha cambiato il mio nome, lo vedo subito
        try:
            nu_aggiorna_sessione()
        except Exception:
            pass
    if "ls_banner" in globals() and st.session_state.get("_ls_giro") != st.session_state.get("_tabs_giro"):     # «🧹 Libera spazio»: dopo aver archiviato un file (una volta per ridisegno)
        st.session_state["_ls_giro"] = st.session_state.get("_tabs_giro")
        try:
            ls_banner()
        except Exception:
            pass
    try:                                                              # la sezione in cui sei si scrive nell'indirizzo: se la pagina riparte, si torna qui
        if st.query_params.get("s") != corrente:
            st.query_params["s"] = corrente
    except Exception:
        pass
    nasc = sv_nascoste() if "sv_nascoste" in globals() else set()
    sc = pn_scadenze()
    lampeggiano = [sez for sez in sc if sez not in nasc]
    st.markdown(_pn_css_testo(), unsafe_allow_html=True)
    st.markdown(_pn_css(corrente, lampeggiano), unsafe_allow_html=True)
    with st.container(key="nav_pagine"):
        for sez, etichetta, _c1, _c2 in _PN_VOCI:
            if sez != "dispensa" and ("SEZIONI_NAV" in globals() and sez not in SEZIONI_NAV):
                continue
            if sez in nasc:
                continue
            attiva = sez == corrente
            n = len(sc.get(sez, []))
            st.button((("● " if attiva else "") + etichetta) + (f" 🔔{n}" if n else ""), key=("navpa_" if attiva else "navp_") + sez, width="stretch",
                      on_click=(None if attiva else nav_vai), args=(None if attiva else (sez,)))
    pn_freccia_su()
    if "musica_inietta" in globals():                                  # la linguetta della radio di sottofondo (resta accesa in tutte le sezioni)
        try:
            musica_inietta()
        except Exception:
            pass


# ---------------------------------------------------------------------------------------------------------------------
# la freccia «torna su»
# ---------------------------------------------------------------------------------------------------------------------
_PN_JS = r"""
(function () {
  var w = window, doc = w.document, lato = __LATO__;
  var vecchia = doc.getElementById('pn-su');
  if (vecchia) { vecchia.setAttribute('data-lato', lato); vecchia.style[lato === 'sinistra' ? 'left' : 'right'] = '8px'; vecchia.style[lato === 'sinistra' ? 'right' : 'left'] = 'auto'; return; }
  var b = doc.createElement('button');
  b.id = 'pn-su'; b.type = 'button'; b.setAttribute('aria-label', 'Torna in cima'); b.setAttribute('data-lato', lato); b.textContent = '▲';
  b.style.cssText = 'position:fixed;bottom:250px;width:34px;height:34px;border-radius:50%;border:1px solid rgba(255,255,255,.7);background:rgba(0,105,92,.55);color:#fff;font-size:15px;line-height:30px;opacity:.55;'
    + 'padding:0;z-index:99990;display:none;box-shadow:0 2px 6px rgba(0,0,0,.2);cursor:pointer;-webkit-tap-highlight-color:transparent;transition:opacity .15s';
  b.addEventListener('touchstart', function () { b.style.opacity = '1'; }, {passive: true});
  b.style[lato === 'sinistra' ? 'left' : 'right'] = '8px';
  doc.body.appendChild(b);
  function contenitori() {
    var c = [doc.querySelector('[data-testid="stMain"]'), doc.querySelector('section.main'), doc.querySelector('[data-testid="stAppViewContainer"]'), doc.scrollingElement, doc.documentElement, doc.body];
    return c.filter(function (x) { return !!x; });
  }
  function posizione() {
    var m = 0, c = contenitori();
    for (var i = 0; i < c.length; i++) { m = Math.max(m, c[i].scrollTop || 0); }
    return Math.max(m, w.pageYOffset || 0);
  }
  function aggiorna() { b.style.display = posizione() > 500 ? 'block' : 'none'; }
  doc.addEventListener('scroll', aggiorna, true);
  w.addEventListener('scroll', aggiorna, true);
  w.setInterval(aggiorna, 700);
  b.addEventListener('click', function (e) {
    e.preventDefault(); e.stopPropagation();
    var c = contenitori();
    for (var i = 0; i < c.length; i++) { try { c[i].scrollTo({top: 0, behavior: 'smooth'}); } catch (x) { c[i].scrollTop = 0; } }
    try { w.scrollTo({top: 0, behavior: 'smooth'}); } catch (x) { w.scrollTo(0, 0); }
  });
})();
"""


def pn_lato():
    """«destra» (predefinito) o «sinistra»: la scelta della persona, ricordata nei suoi dati."""
    if "pn_lato" not in st.session_state:
        lato = "destra"
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"]) or {}
            lato = (d.get("impostazioni") or {}).get("freccia", "destra")
        except Exception:
            pass
        st.session_state["pn_lato"] = lato if lato in ("destra", "sinistra") else "destra"
    return st.session_state["pn_lato"]


def pn_inietta_una_volta(chiave, versione, pagina):
    """Manda uno script alla pagina SOLO la prima volta di ogni sessione (o quando cambia la versione): lo script resta nel browser, rimandarlo a ogni tocco rallentava tutto."""
    if st.session_state.get("_inj_" + chiave) == versione:
        return
    st.session_state["_inj_" + chiave] = versione
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_pn
            _comp_pn.html(pagina, height=0)
    except Exception:
        pass


def pn_freccia_su():
    """Mette (o aggiorna) la freccia «torna su» nella pagina (una volta sola per sessione, o quando cambi il lato)."""
    lato = pn_lato()
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_PN_JS.replace("__LATO__", json.dumps(lato))) + ";P.document.head.appendChild(s);})();</script>")
    pn_inietta_una_volta("freccia", str(lato), pagina)


def pn_impostazioni():
    """Il riquadro «⚙️ Aspetto dell'app» (in Utilità): grandezza dei testi e da che parte sta la freccia «torna su»."""
    with st.expander("⚙️ Aspetto dell'app: testi, radio e freccia «torna su»"):
        if "nu_ui_proprio" in globals():
            nu_ui_proprio()
        if "ls_ui_impostazione" in globals():
            ls_ui_impostazione()
        if "musica_attiva" in globals():
            m_on = st.checkbox("🎧 Mostra la radio di sottofondo (la linguetta sul bordo dello schermo)", value=musica_attiva(), key="pn_musica_scelta")
            if m_on != musica_attiva():
                st.session_state["pn_musica"] = m_on
                try:
                    def _fnm(d, v=m_on):
                        d.setdefault("impostazioni", {})["musica"] = v
                    salva(_fnm, "Aspetto: radio di sottofondo")
                except Exception as e:
                    st.warning(f"Non sono riuscito a ricordare la scelta: {e}")
                st.rerun()
        t_sc = st.radio("🔤 Grandezza dei testi", list(_PN_TESTI), index=list(_PN_TESTI).index(pn_testo()), horizontal=True, key="pn_testo_scelta",
                        format_func=lambda x: {"normale": "Normale", "grande": "Grande", "molto grande": "Molto grande"}[x],
                        help="Se leggi meglio con le scritte più grandi: scegli «Grande» o «Molto grande». Vale per tutta l'app.")
        if t_sc != pn_testo():
            st.session_state["pn_testo"] = t_sc
            try:
                def _fnt(d, v=t_sc):
                    d.setdefault("impostazioni", {})["testo"] = v
                salva(_fnt, "Aspetto: grandezza dei testi")
            except Exception as e:
                st.warning(f"Non sono riuscito a ricordare la scelta: {e}")
            st.rerun()
        scelta = st.radio("La freccia che riporta in cima sta a…", ["destra", "sinistra"], index=0 if pn_lato() == "destra" else 1, horizontal=True, key="pn_lato_scelta",
                          format_func=lambda x: "➡️ destra (predefinito)" if x == "destra" else "⬅️ sinistra")
        st.caption("Compare in basso solo quando scorri una pagina lunga, e con un tocco ti riporta all'inizio. Sta sopra i pulsanti in basso, per non coprire le scritte.")
        if scelta != pn_lato():
            st.session_state["pn_lato"] = scelta
            try:
                def _fn(d, v=scelta):
                    d.setdefault("impostazioni", {})["freccia"] = v
                salva(_fn, "Aspetto: lato della freccia")
            except Exception as e:
                st.warning(f"Non sono riuscito a ricordare la scelta: {e}")
            st.rerun()


# ---- aggancio: le vecchie frecce ← → diventano i bottoni colorati; l'impostazione compare in Utilità
if "nav_barra" in globals() and "_pn_nav_prima" not in globals():
    _pn_nav_prima = nav_barra

    def nav_barra(sezione):                                          # noqa: F811
        try:
            return nav_pagine(sezione)
        except Exception:
            return _pn_nav_prima(sezione)

if "schermata_utilita" in globals() and "_pn_utilita_prima" not in globals():
    _pn_utilita_prima = schermata_utilita

    def schermata_utilita():                                         # noqa: F811
        _pn_utilita_prima()
        try:
            pn_impostazioni()
        except Exception:
            pass
