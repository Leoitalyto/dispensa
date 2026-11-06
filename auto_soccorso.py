# -*- coding: utf-8 -*-
"""AUTO · SOCCORSO ED EMERGENZA (EV, ibride e termiche) — la schermata da aprire quando qualcosa va storto.

• STATO: l'app NON è collegata all'auto, quindi NON può sapere se l'alta tensione è spenta né leggere la batteria. Per questo non mostra mai «sganciati in sicurezza»:
  - la batteria 12V si valuta dalla misura che fai tu con un tester (a auto spenta o accesa), con il giudizio 🟢/🟡/🔴;
  - un controllo di sicurezza a tre domande (spia rossa HV, fumo/odore, danni/allagamento) dice se allontanarsi e chiamare il 112;
  - la regola resta sempre: i cavi arancioni sono SEMPRE sotto tensione.
• PROCEDURE rapide: 1 sblocco del cavo di ricarica · 2 avviamento di emergenza 12V · 3 modalità tartaruga · 4 incendio/fumo/allagamento · sezionatore d'emergenza (con la nota sul punto in cui si trova nel TUO modello).
• CONTATTI a un tocco: soccorso stradale (numero dell'assicurazione se c'è), 112, Vigili del Fuoco 115, assistenza del costruttore.
• POSIZIONE: l'ultima salvata a mano + «📍 Condividi la mia posizione (GPS)»: il telefono trova dove sei (se consenti) e apre la condivisione (WhatsApp, SMS…). Non è trasmessa da sola.
Caricato dopo auto_diagnosi.py."""
import html as _h_as
import json as _json_as
import re
import urllib.parse
from datetime import date

import streamlit as st

_AS_JS = r"""
(function () {
  var w = window, doc = document;
  if (w.__soccorsoPos) return;
  w.__soccorsoPos = true;
  function avvisa(t, errore) {
    var el = doc.querySelector('[data-as-msg]');
    if (el) { el.textContent = t; el.style.display = 'block'; el.style.color = errore ? '#b71c1c' : '#0f766e'; }
  }
  function condividi() {
    if (!navigator.geolocation) { avvisa('Questo browser non sa dove ti trovi: scrivi tu la posizione e chiama il soccorso.', true); return; }
    avvisa('Cerco la tua posizione… (se il telefono lo chiede, consenti l\'accesso alla posizione)');
    navigator.geolocation.getCurrentPosition(function (p) {
      var lat = p.coords.latitude.toFixed(6), lon = p.coords.longitude.toFixed(6), acc = Math.round(p.coords.accuracy || 0);
      var link = 'https://www.google.com/maps?q=' + lat + ',' + lon;
      var testo = '🆘 Ho bisogno di soccorso. Sono qui: ' + link + ' (precisione circa ' + acc + ' m)';
      avvisa('Posizione trovata: ' + lat + ', ' + lon + ' (circa ' + acc + ' m). Scegli a chi mandarla.');
      if (navigator.share) { navigator.share({title: 'La mia posizione', text: testo}).catch(function () {}); }
      else { try { navigator.clipboard.writeText(testo); } catch (e) {} w.open('https://wa.me/?text=' + encodeURIComponent(testo), '_blank'); }
    }, function (e) {
      avvisa(e && e.code === 1 ? 'Non hai dato il permesso alla posizione: abilitalo nelle impostazioni del sito, oppure scrivi tu dove sei.' : 'Non riesco a trovare la posizione adesso (poco segnale GPS?). Scrivi tu dove sei.', true);
    }, {enableHighAccuracy: true, timeout: 15000, maximumAge: 0});
  }
  doc.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('[data-as-azione]') : null;
    if (!b) return;
    ev.preventDefault();
    if (b.getAttribute('data-as-azione') === 'gps') condividi();
  }, true);
})();
"""

_AS_CSS = """<style>
.as-hv{border:2px solid #b71c1c;border-radius:16px;padding:10px 14px;margin:8px 0;background:#fff5f5;color:#4a0d0d}
.as-stato{border-radius:14px;padding:9px 12px;margin:6px 0;font-weight:700}
.as-v{background:#e8f5e9;border-left:6px solid #2e7d32;color:#1b5e20}.as-g{background:#fff8e1;border-left:6px solid #f9a825;color:#6d4c00}.as-r{background:#ffebee;border-left:6px solid #c62828;color:#7f1111}
.as-pericolo{background:#b71c1c;color:#fff;border-radius:16px;padding:12px 14px;margin:8px 0;font-weight:900}
.as-gps{border-radius:14px;padding:13px 10px;text-align:center;font-weight:900;font-size:1.02rem;color:#fff;cursor:pointer;user-select:none;background:linear-gradient(135deg,#43a047,#1b5e20);box-shadow:0 5px 0 rgba(0,70,20,.35);-webkit-tap-highlight-color:transparent}
.as-gps:active{transform:scale(.98)}
</style>"""

# i titoli delle quattro procedure (come nello schema) e il testo breve
_AS_PROC_EV = [("🔌 1. Sblocco d'emergenza del cavo di ricarica", "🔌 Cavo di ricarica bloccato", "Tirante meccanico nel bagagliaio o sblocco da chiave, display o app."),
               ("⚡ 2. Avviamento di emergenza a 12V (jump-start)", "🔋 Batteria 12V scarica (elettrica/ibrida)", "Come alimentare la rete di bordo per sbloccare portiere, freni e centraline HV."),
               ("🐢 3. Gestione della «modalità tartaruga» (potenza limitata)", "🐢 Modalità tartaruga / potenza ridotta", "Cosa fare se l'auto limita la potenza per surriscaldamento o carica critica (sotto il 5%)."),
               ("🧯 4. Incendio, fumo o allagamento", "🔥 Fumo, fuoco o allagamento", "Allontanamento di 15-20 metri, cosa dire al 112 e dov'è il sezionatore d'emergenza.")]
_AS_PROC_MICRO = [("🔋 1. Batteria al litio che scalda, fuma o prende fuoco", "🔋 Batteria al litio (monopattino / e-bike)", "Cosa fare se la batteria si surriscalda, si gonfia o fuma, e come ricaricare in sicurezza."),
                  ("🧯 2. Incendio o fumo", "🔥 Fumo, fuoco o allagamento", "Allontanamento di 15-20 metri e cosa dire al 115 o al 112.")]
_AS_PROC_TERMICA = [("⚡ 1. Avviamento di emergenza a 12V (cavi di avviamento)", "🔋 Batteria 12V scarica (auto termica)", "Come far ripartire l'auto con un'altra auto o un booster."),
                    ("🧯 2. Incendio o fumo", "🔥 Fumo, fuoco o allagamento", "Allontanamento di 15-20 metri e cosa dire al 112.")]


def as_valuta_12v(volt, acceso):
    """(stato 'v'|'g'|'r', testo) per la tensione misurata sulla batteria 12V. acceso=True se l'auto è accesa (READY / motore in moto)."""
    try:
        x = float(str(volt).replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not 5 <= x <= 20:
        return ("g", "Il valore non sembra una tensione 12V: controlla di aver letto bene il tester.")
    if acceso:
        if x >= 13.2:
            return ("v", f"{x:.1f} V · Normale: con l'auto accesa la 12V si sta ricaricando.")
        if x >= 12.4:
            return ("g", f"{x:.1f} V · ⚠️ ATTENZIONE: con l'auto accesa dovrebbe stare sopra 13 V. La 12V non si ricarica bene (convertitore DC-DC o batteria): fai controllare.")
        return ("r", f"{x:.1f} V · 🔴 Troppo bassa con l'auto accesa: non si ricarica. Fai controllare subito e non contare sull'avviamento.")
    if x >= 12.4:
        return ("v", f"{x:.1f} V · Carica buona (a riposo una 12V sana sta sopra 12,4 V).")
    if x >= 11.8:
        return ("g", f"{x:.1f} V · ⚠️ ATTENZIONE: batteria 12V scarica a metà. Rischio che l'auto non si avvii: ricarica o sostituisci presto.")
    return ("r", f"{x:.1f} V · 🔴 12V molto scarica: l'auto potrebbe non aprirsi né partire. Usa l'avviamento di emergenza a 12V (procedura 2).")


def _as_numeri(v):
    ass = (((v or {}).get("scadenze") or {}).get("assicurazione") or {}).get("telefono") or ""
    sos = (v or {}).get("soccorso_tel") or ""
    if sos.strip():
        return re.sub(r"[^\d+]", "", sos), "Numero scelto da te"
    if ass.strip():
        return re.sub(r"[^\d+]", "", ass), "Numero della polizza"
    return "803116", "ACI 803.116"


def as_inietta():
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + _json_as.dumps(_AS_JS) + ";P.document.head.appendChild(s);s.parentNode.removeChild(s);})();</script>")
    if "pn_inietta_una_volta" in globals():
        pn_inietta_una_volta("soccorsogps", "1", pagina)
    else:
        try:
            st.html(pagina, unsafe_allow_javascript=True)
        except Exception:
            pass


def _as_procedura(titolo, chiave, riassunto, extra=None):
    p = _AE_PROCEDURE.get(chiave)
    if not p:
        return
    with st.expander(titolo):
        st.caption(riassunto)
        st.markdown(p["intro"])
        if extra:
            st.markdown(extra)
        st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(p["passi"], 1)))


def as_pagina(v):
    """La schermata «Soccorso ed emergenza»."""
    vid = (v or {}).get("id")
    micro = bool(v) and _au_micro(v)
    ev = bool(v) and _au_ha_batteria(v) and not micro
    st.markdown(_AS_CSS, unsafe_allow_html=True)
    t1, t2 = st.columns([1, 3], gap="small")
    if t1.button("← Indietro", key="as_indietro", width="stretch"):
        st.session_state["au_vista"] = "garage"
        st.rerun()
    t2.markdown("### 🚨 Soccorso ed emergenza" + (" EV" if ev else ""))
    n_sos, et_sos = _as_numeri(v)
    top1, top2 = st.columns(2, gap="small")
    top1.link_button("🆘 Pericolo: chiama il 112", "tel:112", width="stretch", type="primary")
    top2.link_button("🚒 Vigili del Fuoco · 115", "tel:115", width="stretch")
    # ---- stato del sistema (inserito da te)
    if ev:
        st.markdown("#### ⚠️ Stato del sistema ad alta tensione (HV)")
        st.markdown("<div class='as-hv'>🔴 <b>L'app non è collegata all'auto</b>: non può sapere se l'alta tensione è spenta. <b>Considera SEMPRE i cavi arancioni sotto tensione: non toccarli e non tagliarli.</b> Qui sotto controlli tu.</div>", unsafe_allow_html=True)
        st.markdown("**Controllo di sicurezza** (spunta quello che vedi):")
        a1 = st.checkbox("Vedo una spia ROSSA di alta tensione o della batteria di trazione", key="as_c1")
        a2 = st.checkbox("Vedo fumo, sento un odore acre o un rumore anomalo", key="as_c2")
        a3 = st.checkbox("L'auto ha avuto un urto forte o è stata in acqua", key="as_c3")
        if a1 or a2 or a3:
            st.markdown("<div class='as-pericolo'>🔴 PERICOLO — ALLONTANATI DI 15-20 METRI<br><small style='font-weight:700'>Fai scendere tutti, non toccare l'auto né i cavi arancioni e chiama il 112: di' che è un veicolo ELETTRICO (o ibrido).</small></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='as-stato as-g'>🟡 Nessun segnale di pericolo evidente. Questo <b>non</b> vuol dire che sia sicuro toccare i cavi arancioni.</div>", unsafe_allow_html=True)
    st.markdown("#### 🔋 Batteria 12V (servizi)")
    ultima = (v or {}).get("batt12v") or {}
    if ultima.get("v"):
        g = as_valuta_12v(ultima["v"], ultima.get("acceso"))
        if g:
            st.markdown(f"<div class='as-stato as-{g[0]}'>🔋 Ultima misura ({_au_it(ultima.get('data'))}{', auto accesa' if ultima.get('acceso') else ', auto spenta'}): {g[1]}</div>", unsafe_allow_html=True)
    with st.form(f"as_12v_{vid or 'x'}", border=False):
        c1, c2 = st.columns([2, 3], gap="small")
        volt = c1.text_input("Misura (V)", key=f"as_v_{vid or 'x'}", placeholder="es. 11,4")
        acceso = c2.radio("L'auto è…", ["spenta", "accesa (READY / motore in moto)"], horizontal=True, key=f"as_a_{vid or 'x'}")
        if st.form_submit_button("🔎 Valuta la 12V", width="stretch"):
            g = as_valuta_12v(volt, acceso.startswith("accesa"))
            if g is None:
                st.error("Scrivi la tensione misurata col tester (per esempio 12,4).")
            else:
                st.markdown(f"<div class='as-stato as-{g[0]}'>🔋 {g[1]}</div>", unsafe_allow_html=True)
                if vid:
                    _au_mod(vid, lambda x, volt=volt, ac=acceso.startswith("accesa"): x.__setitem__("batt12v", {"v": str(volt).replace(",", "."), "acceso": ac, "data": date.today().isoformat()}), "Auto: misura 12V")
    st.caption("La tensione della 12V la misuri tu con un tester sui morsetti (o sui punti di avviamento d'emergenza indicati dal manuale). Mai misurare o toccare l'alta tensione.")
    # ---- procedure rapide
    st.markdown("#### 🛠️ Procedure di emergenza rapida")
    if not micro:
        st.markdown(_AE_HV)
    for titolo, chiave, riassunto in (_AS_PROC_EV if ev else _AS_PROC_MICRO if micro else _AS_PROC_TERMICA):
        _as_procedura(titolo, chiave, riassunto, "**Se la carica è sotto il 5%:** l'auto può ridurre molto la potenza o fermarsi. Spegni clima e consumi e vai alla colonnina più vicina." if "tartaruga" in chiave else None)
    if ev:
        with st.expander("🔴 5. Sezionatore d'emergenza (Emergency Cut-Off)"):
            st.markdown("È il punto in cui si **stacca l'alta tensione**. **Serve ai Vigili del Fuoco e ai tecnici formati: tu non devi usarlo.** Sapere dove si trova nel tuo modello li aiuta (la «guida di soccorso» del costruttore lo indica).")
            q = " ".join(x for x in (v.get("marca"), v.get("modello"), v.get("anno")) if x)
            if q:
                l1, l2 = st.columns(2, gap="small")
                l1.link_button("📘 Guida di soccorso del mio modello", "https://www.google.com/search?q=" + urllib.parse.quote_plus(f"{q} emergency response guide guida di soccorso pdf"), width="stretch")
                l2.link_button("🔌 Dove si stacca la HV", "https://www.google.com/search?q=" + urllib.parse.quote_plus(f"{q} sezionatore emergenza alta tensione posizione"), width="stretch")
            if vid:
                with st.form(f"as_cut_{vid}", border=False):
                    nota = st.text_area("Dove si trova nel mio modello (dalla guida di soccorso)", value=v.get("cutoff_nota", ""), key=f"as_cutn_{vid}", height=80)
                    if st.form_submit_button("💾 Salva la nota", width="stretch"):
                        _au_mod(vid, lambda x, n=nota.strip(): x.__setitem__("cutoff_nota", n), "Auto: sezionatore")
                        st.rerun()
    # ---- contatti rapidi
    st.markdown("#### 📞 Contatti rapidi e assistenza")
    k1, k2 = st.columns(2, gap="small")
    k1.link_button(f"☎️ Soccorso stradale · {et_sos}", "tel:" + n_sos, width="stretch")
    k2.link_button("🚒 Vigili del Fuoco · 115", "tel:115", width="stretch")
    k3, k4 = st.columns(2, gap="small")
    k3.link_button("🆘 Emergenza · 112", "tel:112", width="stretch")
    ass_c = (v or {}).get("assistenza_tel") or ""
    if ass_c.strip():
        k4.link_button("🏭 Assistenza del costruttore", "tel:" + re.sub(r"[^\d+]", "", ass_c), width="stretch")
    with st.expander("⚙️ Cambia i numeri"):
        if vid:
            with st.form(f"as_num_{vid}", border=False):
                s = st.text_input("Soccorso stradale (lascia vuoto per usare quello della polizza o l'ACI)", value=v.get("soccorso_tel", ""), key=f"as_ns_{vid}")
                a_ = st.text_input("Assistenza del costruttore", value=v.get("assistenza_tel", ""), key=f"as_na_{vid}")
                if st.form_submit_button("💾 Salva i numeri", width="stretch"):
                    _au_mod(vid, lambda x, s=s.strip(), a_=a_.strip(): (x.__setitem__("soccorso_tel", s), x.__setitem__("assistenza_tel", a_)), "Auto: numeri")
                    st.rerun()
        st.caption("Il numero dell'assicurazione si scrive in ⏰ Scadenze → Assicurazione. Controlla sempre che i numeri siano giusti.")
    # ---- posizione
    st.markdown("#### 📍 La tua posizione")
    pos = (v or {}).get("posizione") or {}
    st.markdown(f"<div class='au-card'>📍 <b>Ultima posizione salvata a mano:</b> {_h_as.escape(pos.get('testo') or 'nessuna')}" + (f"<br><small>{_au_it(pos.get('data'))}</small>" if pos.get("data") else "") + "</div>", unsafe_allow_html=True)
    as_inietta()
    st.markdown("<div class='as-gps' role='button' tabindex='0' data-as-azione='gps'>📍 Condividi la mia posizione (GPS)</div><div data-as-msg style='display:none;margin-top:6px;font-weight:700;font-size:13.5px'></div>", unsafe_allow_html=True)
    st.caption("Il telefono trova dove sei (se consenti) e ti fa scegliere a chi mandare il link: soccorso, familiari, WhatsApp, SMS. **La posizione non viene trasmessa da sola.**")
