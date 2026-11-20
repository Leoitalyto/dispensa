# -*- coding: utf-8 -*-
"""🗓️ SCADENZIARIO — il centro di controllo di tutte le scadenze, PRIMA di Utilità.

Il motore è in scadenziario_core.py (lo stesso file usato dagli avvisi ad app chiusa in promemoria.py): qui c'è solo l'interfaccia.
Legge le schede originali di tutte le sezioni (niente copie), aggiunge «📌 Le mie scadenze personali», gestisce stati, ricorrenze, avvisi
per attività (anticipi, rinvio, pausa, ripetizione, suono e vibrazione), riepilogo giornaliero/settimanale e calendario del telefono (.ics).
Caricato da app_dispensa.py dopo spesa_smart.py (scadenziario_core.py subito prima)."""
import html as _sz_h
import json as _sz_json
from datetime import date as _szd, datetime as _szdt, timedelta as _sztd

import streamlit as st

SZ_COLORI = ("#ff5c8a", "#9c1046")
SZ_SUONI = {"campanello": "🔔 Campanello", "ding": "🎵 Ding", "dolce": "🌸 Dolce", "allarme": "🚨 Allarme", "radar": "📡 Radar", "personale": "🎙️ Il mio suono"}
_SZ_COL_STATO = {"Scaduta": "#ff5252", "In scadenza": "#ffab40", "Da fare": "#69f0ae", "Posticipata": "#40c4ff", "Completata": "#9e9e9e", "Annullata": "#757575"}
_SZ_ICO_STATO = {"Scaduta": "🔴", "In scadenza": "🟠", "Da fare": "🟢", "Posticipata": "⏸️", "Completata": "✅", "Annullata": "⚪"}
_SZ_TILES = [("scadute", "🔴", "Scadute"), ("oggi", "📍", "Oggi"), ("7", "📆", "Prossimi 7 giorni"), ("30", "🗓️", "Prossimi 30 giorni"), ("future", "🔭", "Più avanti"),
             ("completate", "✅", "Completate")]

_SZ_CSS = """<style>
.sz-hero{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,#12020a 0%,#4a0820 55%,#ff5c8a 160%);color:#fff;padding:16px 18px;border-radius:22px;
 margin:6px 0 10px;border:2px solid rgba(255,92,138,.75);box-shadow:0 0 18px rgba(255,92,138,.35)}
.sz-hero .ico{font-size:2.6rem;line-height:1}.sz-hero h1{margin:0;font-size:1.55rem;color:#fff}.sz-hero p{margin:2px 0 0;font-size:.92rem;opacity:.95}
.st-key-sz_tiles[data-testid='stVerticalBlock'],.st-key-sz_tiles [data-testid='stVerticalBlock']{display:grid !important;grid-template-columns:repeat(3,1fr);gap:7px !important;margin:4px 0 10px}
.st-key-sz_tiles button{width:100% !important;min-height:64px !important;border-radius:16px !important;background:rgba(20,6,12,.92) !important;border:1.5px solid rgba(255,92,138,.45) !important;
 padding:4px !important}
.st-key-sz_tiles button p{color:#fff !important;font-weight:800 !important;font-size:.78rem !important;line-height:1.15 !important;margin:0;white-space:pre-line}
.st-key-sz_tiles [class*='st-key-szt_on_'] button{background:linear-gradient(135deg,#ff5c8a,#9c1046) !important;outline:3px solid #fff !important;outline-offset:-5px}
.st-key-sz_tiles .st-key-szt_scadute button{border-color:#ff5252 !important;box-shadow:0 0 10px rgba(255,82,82,.45)}
.st-key-sz_tiles .st-key-szt_oggi button{border-color:#ffab40 !important}
.sz-card{background:rgba(255,255,255,.96);color:#1b1b10;border-radius:14px;padding:9px 12px;margin:8px 0 2px;border-left:7px solid var(--c);overflow-wrap:anywhere}
.sz-card .t{font-weight:900;font-size:1rem}.sz-card .m{font-size:.84rem;color:#4a4a3a}.sz-card .q{font-weight:800;color:var(--c2)}
.sz-card .tag{display:inline-block;border-radius:10px;padding:0 7px;font-size:.74rem;font-weight:800;margin-right:4px;background:#f3ecd2;color:#5a4500}
.sz-card.fatta{opacity:.7}.sz-card.fatta .t{text-decoration:line-through}
.sz-giorno{margin:12px 0 0;font-weight:900;color:#ff5c8a;font-size:.95rem}
.st-key-vm_sz button{width:100% !important;min-height:54px !important;border-radius:999px !important;background:linear-gradient(135deg,#12020a,#4a0820 60%,#ff5c8a) !important;
 border:2px solid #ff5c8a !important;box-shadow:0 0 14px rgba(255,92,138,.6) !important}
.st-key-vm_sz{max-width:460px;margin:0 auto 6px}.st-key-vm_sz button p{color:#fff !important;font-weight:900 !important;font-size:1.05rem !important}
[class*='st-key-sza_'] [data-testid='stHorizontalBlock']{flex-wrap:nowrap !important;gap:.35rem !important}
[class*='st-key-sza_'] [data-testid='stColumn']{min-width:0 !important}
[class*='st-key-sza_'] button{min-height:2.4rem !important;padding:.15rem .3rem !important;border-radius:12px !important}
[class*='st-key-sza_'] button p{font-size:.8rem !important;font-weight:800 !important}
</style>"""


# ---------------------------------------------------------------------------------------------------------------------
# dati
# ---------------------------------------------------------------------------------------------------------------------
def _sz_adesso():
    try:
        from zoneinfo import ZoneInfo
        return _szdt.now(ZoneInfo("Europe/Rome")).replace(tzinfo=None, second=0, microsecond=0)
    except Exception:
        return _szdt.now().replace(second=0, microsecond=0)


def _sz_dati():
    """(dati personali, dati della dispensa aperta se diversa)."""
    try:
        d = carica_dati(crea_archivio(), percorso_mio())
    except Exception:
        d = {}
    extra = None
    try:
        p = st.session_state.get("percorso")
        if p and p != percorso_mio():
            extra = carica_dati(crea_archivio(), p)
    except Exception:
        extra = None
    return d, extra


def _sz_voci(adesso=None):
    d, extra = _sz_dati()
    return sz_raccogli(d, adesso or _sz_adesso(), extra), (d.get("scadenziario") if isinstance(d.get("scadenziario"), dict) else sz_migra({}))


def _sz_salva(fn, msg):
    salva_file(percorso_mio(), lambda d: fn(sz_migra(d)), "Scadenziario: " + msg)


def _sz_e(x):
    return _sz_h.escape(str(x or ""))


def _sz_quando(v, adesso):
    g = (v["data"] - adesso.date()).days
    if v["stato"] in ("Completata", "Annullata"):
        return v["stato"].lower()
    if g < 0:
        return f"scaduta da {-g} giorn{'o' if g == -1 else 'i'}"
    if g == 0:
        return "oggi" + (f" alle {v['ora']}" if v.get("ora") else "")
    if g == 1:
        return "domani" + (f" alle {v['ora']}" if v.get("ora") else "")
    return f"tra {g} giorni"


# ---------------------------------------------------------------------------------------------------------------------
# suoni (WebAudio: nessun file da scaricare) e anteprima
# ---------------------------------------------------------------------------------------------------------------------
_SZ_JS_SUONI = r"""
function vmCtx(){
  var w = window.parent || window, C = w.AudioContext || w.webkitAudioContext || window.AudioContext || window.webkitAudioContext;
  if (!C) return null;
  if (!w.__vmAC || w.__vmAC.state === 'closed') { try { w.__vmAC = new C(); } catch (e) { return null; } }
  return w.__vmAC;
}
(function sblocca(){                                   // il primo tocco sulla pagina «sblocca» l'audio (Android lo vuole), così anche gli avvisi suonano
  var w = window.parent || window;
  if (w.__vmSblocco) return; w.__vmSblocco = 1;
  ['touchstart', 'pointerdown', 'click', 'keydown'].forEach(function (ev) {
    try { w.document.addEventListener(ev, function () { var a = vmCtx(); if (a && a.state !== 'running' && a.resume) a.resume(); }, {passive: true, capture: true}); } catch (e) {}
  });
})();
function vmSuona(ac, nome){
  var t = ac.currentTime + 0.05;
  function nota(f, ini, dur, tipo, vol){ var o = ac.createOscillator(), g = ac.createGain(); o.type = tipo||'sine'; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t+ini); g.gain.exponentialRampToValueAtTime(vol||0.5, t+ini+0.02); g.gain.exponentialRampToValueAtTime(0.0001, t+ini+dur);
    o.connect(g); g.connect(ac.destination); o.start(t+ini); o.stop(t+ini+dur+0.05); }
  if(nome==='ding'){ nota(1046,0,1.2); }
  else if(nome==='dolce'){ nota(523,0,.5); nota(659,.18,.5); nota(784,.36,.8); }
  else if(nome==='allarme'){ for(var i=0;i<3;i++){ nota(880,i*.32,.22,'square',.3); } }
  else if(nome==='radar'){ for(var j=0;j<4;j++){ nota(1250,j*.22,.1,'sine',.5); } }
  else { nota(880,0,.45); nota(660,.28,.7); }
  try { (window.parent || window).__vmUltimoSuono = nome + '|' + ac.state; } catch (e) {}
}
function vmSuono(nome, file){
  var w = window.parent || window;
  if (nome === 'personale' && file) {
    try { var A = new (w.Audio || Audio)(file); var p = A.play(); if (p && p.catch) p.catch(function () {}); w.__vmUltimoSuono = 'personale'; return; } catch (e) {}
  }
  var ac = vmCtx(); if (!ac) return;
  var r = (ac.state !== 'running' && ac.resume) ? ac.resume() : null;
  if (r && r.then) { r.then(function () { vmSuona(ac, nome); }, function () { vmSuona(ac, nome); }); } else { vmSuona(ac, nome); }
}
"""


def _sz_suono_html(nome, file_uri="", vibra=True, auto=False, etichetta="▶ Ascolta"):
    js = f"vmSuono({_sz_json.dumps(nome)}, {_sz_json.dumps(file_uri)});" + ("try{(window.parent.navigator||navigator).vibrate([250,120,250]);}catch(e){}" if vibra else "")
    bottone = ("<button onclick=\"" + _sz_h.escape(js, quote=True) + "\" style='width:100%;height:40px;border-radius:12px;border:1.5px solid #ff5c8a;background:#1a0510;"
               "color:#fff;font-weight:800;font-size:15px'>" + _sz_h.escape(etichetta) + "</button>")
    return ("<html><body style='margin:0;background:transparent'><script>" + _SZ_JS_SUONI + "</script>" + bottone
            + (f"<script>try{{{js}}}catch(e){{}}</script>" if auto else "") + "</body></html>")


def _sz_file_suono(imp):
    rif = imp.get("suono_file")
    if not rif:
        return ""
    try:
        import base64
        b = cp_file_leggi(rif)
        return f"data:{rif.get('mime') or 'audio/mpeg'};base64," + base64.b64encode(b).decode() if b else ""
    except Exception:
        return ""


def _sz_suono_di(sz, v):
    imp = sz.get("impostazioni") or {}
    cfg = sz_cfg_avvisi(sz, v)
    return cfg.get("suono") or (imp.get("suoni_categoria") or {}).get(v["categoria"]) or imp.get("suono") or "campanello"


def _sz_anteprima(nome, chiave, imp):
    import streamlit.components.v1 as _cmp
    _cmp.html(_sz_suono_html(nome, _sz_file_suono(imp) if nome == "personale" else "", True, False, "▶ Ascolta «" + SZ_SUONI.get(nome, nome).split(" ", 1)[-1] + "»"), height=46)


# ---------------------------------------------------------------------------------------------------------------------
# la configurazione degli avvisi (per un'attività o per una categoria)
# ---------------------------------------------------------------------------------------------------------------------
def _sz_ui_avvisi(k, cfg, imp, con_suono=True):
    """I controlli degli avvisi. Ritorna la nuova configurazione."""
    cfg = dict(SZ_AVVISI_BASE, **(cfg or {}))
    attivi = st.toggle("🔔 Avvisi accesi", value=bool(cfg.get("attivi", True)), key=k + "_on")
    preset = [m for m, _e in SZ_PRESET]
    scelti = [int(x) for x in cfg.get("anticipi") or [] if int(x) in preset]
    altri = [int(x) for x in cfg.get("anticipi") or [] if int(x) not in preset]
    sel = st.multiselect("Quando avvisarmi", preset, default=scelti, format_func=sz_etichetta_anticipo, key=k + "_ant", disabled=not attivi)
    c1, c2, c3 = st.columns([1.2, 1.6, 1.2], gap="small")
    n = c1.number_input("Anche", min_value=0, max_value=999, value=0, step=1, key=k + "_n", disabled=not attivi)
    u = c2.selectbox("unità", ["minuti prima", "ore prima", "giorni prima"], key=k + "_u", disabled=not attivi, label_visibility="hidden")
    if altri:
        c3.caption("Altri: " + ", ".join(sz_etichetta_anticipo(x) for x in altri))
    pers = altri + ([int(n) * {"minuti prima": 1, "ore prima": 60, "giorni prima": 1440}[u]] if n else [])
    ripeti = st.checkbox("🔁 Ripeti ogni giorno finché non confermo di averlo visto", value=bool(cfg.get("ripeti")), key=k + "_rip", disabled=not attivi)
    pausa = st.date_input("⏸️ Pausa degli avvisi fino al (facoltativo)", value=sz_d(cfg.get("silenzio_fino")), format="DD/MM/YYYY", key=k + "_pausa", disabled=not attivi)
    out = dict(cfg, attivi=attivi, anticipi=sorted(set(sel + pers), reverse=True), ripeti=ripeti, silenzio_fino=pausa.isoformat() if pausa else "")
    if con_suono:
        c4, c5 = st.columns([2, 1], gap="small")
        opz = [""] + list(SZ_SUONI)
        s_ = c4.selectbox("🎵 Suono (nell'app)", opz, index=opz.index(cfg.get("suono")) if cfg.get("suono") in opz else 0, key=k + "_suono",
                          format_func=lambda x: "Quello della categoria" if not x else SZ_SUONI[x])
        vib = c5.toggle("📳 Vibra", value=bool(cfg.get("vibrazione", True)), key=k + "_vib")
        _sz_anteprima(s_ or imp.get("suono") or "campanello", k + "_prova", imp)
        out.update(suono=s_, vibrazione=vib)
    return out


# ---------------------------------------------------------------------------------------------------------------------
# scheda di un'attività + azioni rapide
# ---------------------------------------------------------------------------------------------------------------------
def _sz_card(v, adesso, sz):
    c = _SZ_COL_STATO.get(v["stato"], "#69f0ae")
    cat_i, cat_n = SZ_CATEGORIE.get(v["categoria"], ("📌", "Altro"))
    tags = [f"<span class='tag'>{cat_i} {_sz_e(v.get('categoria_pers') or cat_n)}</span>"]
    sc_ = st.session_state.get("_sz_profili_scelti") or []
    if v.get("profilo") and (len(sc_) > 1 or (sc_ and v["profilo"] != sc_[0])):
        tags.append(f"<span class='tag' style='background:#e3f2fd;color:#0d47a1'>👤 {_sz_e(st.session_state.get('_sz_nomi_p', {}).get(v['profilo'], ''))}</span>")
    if v.get("sezione") and v["sezione"] != "scadenziario":
        tags.append(f"<span class='tag'>↗ {_sz_e(SZ_SEZIONI.get(v['sezione'], v['sezione']))}</span>")
    if v.get("priorita") == "Alta":
        tags.append("<span class='tag' style='background:#ffe0e0;color:#a10000'>❗ Alta</span>")
    if v.get("ricorrente"):
        tags.append(f"<span class='tag'>🔁 {_sz_e(v['ricorrente'])}</span>")
    cfg = sz_cfg_avvisi(sz, v)
    if not cfg.get("attivi", True) or (cfg.get("silenzio_fino") and cfg["silenzio_fino"] >= adesso.date().isoformat()):
        tags.append("<span class='tag'>🔕</span>")
    if cfg.get("rinvio_al") and str(cfg["rinvio_al"]) > adesso.isoformat(timespec="minutes"):
        tags.append(f"<span class='tag'>⏰ avviso alle {_sz_e(str(cfg['rinvio_al'])[11:16])} del {_sz_e(str(cfg['rinvio_al'])[8:10] + '/' + str(cfg['rinvio_al'])[5:7])}</span>")
    imp_ = f" · 💶 {v['importo']:.2f} €".replace(".", ",") if v.get("importo") else ""
    return (f"<div class='sz-card{' fatta' if v['stato'] in ('Completata', 'Annullata') else ''}' style='--c:{c};--c2:{c if v['stato'] != 'Da fare' else '#1b7a3f'}'>"
            f"<div class='t'>{_SZ_ICO_STATO.get(v['stato'], '')} {_sz_e(v['titolo'])}</div>"
            f"<div class='m'><span class='q'>{_sz_e(_sz_quando(v, adesso))}</span> · {v['data'].strftime('%d/%m/%Y')}{(' ' + v['ora']) if v.get('ora') else ''}{imp_}</div>"
            + (f"<div class='m'>{_sz_e(v['descrizione'])}</div>" if v.get("descrizione") else "") + f"<div style='margin-top:3px'>{''.join(tags)}</div></div>")


def _sz_stato_sezione(sz, v, stato):
    """Completata/annullata per un'attività delle sezioni: vale SOLO per questa data (se la data cambia, torna da fare)."""
    sz["stati"][v["chiave"]] = {"stato": stato, "data_rif": v["data"].isoformat(), "il": _szdt.now().isoformat(timespec="seconds"), "titolo": v["titolo"],
                                "categoria": v["categoria"], "sezione": v.get("sezione"), "profilo": v.get("profilo")}
    sz_log(sz, stato, v["chiave"], v["titolo"])


def _sz_completa(v):
    esito = {}

    def _fn(sz):
        if v.get("personale"):
            esito["nuova"] = sz_completa_personale(sz, v["rif"]["id"])
        else:
            _sz_stato_sezione(sz, v, "completata")
    _sz_salva(_fn, "completata " + v["titolo"])
    st.session_state["sz_msg"] = f"✅ «{v['titolo']}» completata." + (f" Ho creato la prossima: {sz_d(esito['nuova']['data']).strftime('%d/%m/%Y')}." if esito.get("nuova") else "")


def _sz_riapri(v):
    def _fn(sz):
        if v.get("personale"):
            p = next((x for x in sz["personali"] if x.get("id") == v["rif"]["id"]), None)
            if p:
                p["stato"], p["completata_il"] = "da fare", ""
        else:
            sz["stati"].pop(v["chiave"], None)
        sz_log(sz, "riaperta", v["chiave"], v["titolo"])
    _sz_salva(_fn, "riaperta " + v["titolo"])


def _sz_cfg_set(v, nuova):
    def _fn(sz):
        if v.get("personale"):
            p = next((x for x in sz["personali"] if x.get("id") == v["rif"]["id"]), None)
            if p:
                p["avvisi"] = nuova
                p["modificato_il"] = _szdt.now().isoformat(timespec="seconds")
        else:
            sz["avvisi"][v["chiave"]] = nuova
        sz_log(sz, "avvisi", v["chiave"], v["titolo"])
    _sz_salva(_fn, "avvisi di " + v["titolo"])


def _sz_apri_origine(v):
    """↗️ Apri la scheda originale: va nella sezione (e, quando si può, apre direttamente la finestra o il veicolo giusto)."""
    nav = v.get("nav") or {}
    sez = nav.get("sezione") or v.get("sezione") or "scadenziario"
    if nav.get("veicolo"):
        st.session_state["au_sel"] = nav["veicolo"]
    if nav.get("appuntamenti") and "_apn_corpo" in globals():
        app_sez = nav["appuntamenti"]
        st.session_state["_sc_dlg"] = ("📅 Appuntamenti", (lambda s=app_sez: _apn_corpo(s)), "large", sez)
    if nav.get("badante") and "_bdt_corpo" in globals():
        st.session_state["_sc_dlg"] = ("👵 Badante", _bdt_corpo, "large", "casa")
    st.session_state["messaggio"] = f"↗️ Dallo Scadenziario: «{v['titolo']}» ({v['data'].strftime('%d/%m/%Y')})"
    if sez == "dispensa":
        nav_vai("dispensa")
    else:
        nav_vai(sez)


def _sz_azioni(v, adesso, sz, i):
    k = f"{i}_{abs(hash(v['chiave'])) % 10**8}"
    fatta = v["stato"] in ("Completata", "Annullata")
    with st.container(key="sza_" + k):
        c1, c2, c3 = st.columns(3, gap="small")
        if fatta:
            if not v.get("solo_storico") and c1.button("↩️ Riapri", key="szr_" + k, width="stretch"):
                _sz_riapri(v)
                st.rerun()
        elif c1.button("✅ Fatto", key="szf_" + k, width="stretch"):
            _sz_completa(v)
            st.rerun()
        if not fatta:
            with c2.popover("⏰ Rinvia", width="stretch"):
                st.caption("Rinvia **solo l'avviso**: la data della scadenza resta quella.")
                scelte = {"Tra 1 ora": adesso + _sztd(hours=1), "Tra 3 ore": adesso + _sztd(hours=3), "Domani mattina": _szdt.combine(adesso.date() + _sztd(days=1), _szdt.min.time()).replace(hour=9),
                          "Tra 3 giorni": _szdt.combine(adesso.date() + _sztd(days=3), _szdt.min.time()).replace(hour=9)}
                for j, (et, quando) in enumerate(scelte.items()):
                    if st.button(et, key=f"szrv_{k}_{j}", width="stretch"):
                        cfg = sz_cfg_avvisi(sz, v)
                        _sz_cfg_set(v, dict((v.get("avvisi") if v.get("personale") else (sz.get("avvisi") or {}).get(v["chiave"])) or {}, rinvio_al=quando.isoformat(timespec="minutes"),
                                            **({} if cfg.get("anticipi") is None else {})))
                        st.session_state["sz_msg"] = f"⏰ Ti avviso di nuovo {et.lower()}."
                        st.rerun()
                cd, co = st.columns(2, gap="small")
                dd = cd.date_input("Giorno", value=adesso.date() + _sztd(days=1), format="DD/MM/YYYY", key=f"szrvd_{k}")
                oo = co.time_input("Ora", value=_szdt.strptime("09:00", "%H:%M").time(), key=f"szrvo_{k}")
                if st.button("⏰ Rinvia a questo giorno e ora", key=f"szrvx_{k}", width="stretch"):
                    _sz_cfg_set(v, dict((v.get("avvisi") if v.get("personale") else (sz.get("avvisi") or {}).get(v["chiave"])) or {},
                                        rinvio_al=_szdt.combine(dd, oo).isoformat(timespec="minutes")))
                    st.rerun()
        with c3.popover("⋯", width="stretch"):
            if v.get("nav", {}).get("sezione") not in (None, "scadenziario") and not v.get("solo_storico"):
                st.button("↗️ Apri la scheda originale", key="szo_" + k, width="stretch", on_click=_sz_apri_origine, args=(v,))
            if v.get("personale"):
                if st.button("✏️ Modifica", key="szm_" + k, width="stretch"):
                    st.session_state["sz_mod"] = v["rif"]["id"]
                    st.rerun()
                if st.button("📄 Duplica", key="szd_" + k, width="stretch"):
                    _sz_salva(lambda sz_: sz_duplica_personale(sz_, v["rif"]["id"]), "duplicata")
                    st.rerun()
            if not fatta and not v.get("solo_storico"):
                with st.expander("🔔 Avvisi di questa attività"):
                    nuova = _sz_ui_avvisi("szav_" + k, sz_cfg_avvisi(sz, v), sz.get("impostazioni") or {})
                    if st.button("💾 Salva gli avvisi", key="szavok_" + k, type="primary", width="stretch"):
                        _sz_cfg_set(v, nuova)
                        st.session_state["sz_msg"] = "🔔 Avvisi salvati."
                        st.rerun()
                pr = st.selectbox("Priorità", SZ_PRIORITA, index=SZ_PRIORITA.index(v.get("priorita")) if v.get("priorita") in SZ_PRIORITA else 1, key="szp_" + k)
                if pr != v.get("priorita") and st.button("💾 Salva la priorità", key="szpok_" + k, width="stretch"):
                    def _fn(sz_, pr=pr):
                        if v.get("personale"):
                            for p in sz_["personali"]:
                                if p.get("id") == v["rif"]["id"]:
                                    p["priorita"] = pr
                        else:
                            sz_["stati"].setdefault(v["chiave"], {})["priorita"] = pr
                    _sz_salva(_fn, "priorità")
                    st.rerun()
                if v["stato"] == "Scaduta" and sz_cfg_avvisi(sz, v).get("ripeti") and (sz.get("visto") or {}).get(v["chiave"]) != v["data"].isoformat():
                    if st.button("👁️ Visto (ferma la ripetizione)", key="szv_" + k, width="stretch"):
                        _sz_salva(lambda sz_: sz_["visto"].__setitem__(v["chiave"], v["data"].isoformat()), "visto")
                        st.rerun()
                if not v.get("personale") and st.button("❌ Annulla (per questa data)", key="sza_x_" + k, width="stretch"):
                    _sz_salva(lambda sz_: _sz_stato_sezione(sz_, v, "annullata"), "annullata")
                    st.rerun()
            if v.get("personale"):
                if not fatta and st.button("❌ Annulla", key="szan_" + k, width="stretch"):
                    def _fn(sz_):
                        for p in sz_["personali"]:
                            if p.get("id") == v["rif"]["id"]:
                                p["stato"] = "annullata"
                        sz_log(sz_, "annullata", v["chiave"], v["titolo"])
                    _sz_salva(_fn, "annullata")
                    st.rerun()
                if st.checkbox("Voglio eliminarla", key="szdel_c_" + k) and st.button("🗑️ Elimina per sempre", key="szdel_" + k, width="stretch"):
                    def _fn(sz_):
                        sz_["personali"] = [p for p in sz_["personali"] if p.get("id") != v["rif"]["id"]]
                        sz_log(sz_, "eliminata", v["chiave"], v["titolo"])
                    _sz_salva(_fn, "eliminata")
                    st.rerun()
            elif not v.get("solo_storico"):
                st.caption("Le attività delle altre sezioni si eliminano dalla loro scheda (↗️).")
        for f_ in (v.get("files") or [])[:2]:
            if st.toggle("📎 " + str(f_.get("nome", "allegato"))[:30], key=f"szfile_{k}_{f_.get('id')}") and "sc_file_mostra" in globals():
                sc_file_mostra(f_, f"szfd_{k}_{f_.get('id')}")


# ---------------------------------------------------------------------------------------------------------------------
# modulo delle scadenze personali
# ---------------------------------------------------------------------------------------------------------------------
def _sz_modulo(sz, pid):
    p = next((x for x in sz["personali"] if x.get("id") == pid), None) if pid != "nuova" else None
    p = p or {}
    k = "szform_" + (pid or "nuova")
    imp = sz.get("impostazioni") or {}
    with st.container(border=True, key=k + "_box"):
        st.markdown("**" + ("✏️ Modifica la scadenza" if p else "➕ Nuova scadenza personale") + "**")
        titolo = st.text_input("Titolo *", value=p.get("titolo", ""), key=k + "_t", placeholder="es. Telefonare al commercialista")
        descr = st.text_area("Descrizione (facoltativa)", value=p.get("descrizione", ""), key=k + "_d", height=70)
        c1, c2 = st.columns(2, gap="small")
        data = c1.date_input("Data *", value=sz_d(p.get("data")) or _sz_adesso().date(), format="DD/MM/YYYY", key=k + "_data")
        try:
            ora0 = _szdt.strptime(p["ora"], "%H:%M").time() if p.get("ora") else None
        except Exception:
            ora0 = None
        ora = c2.time_input("Ora (se serve)", value=ora0, key=k + "_ora", step=300)
        cats = sorted({x.get("categoria") or "Personale" for x in sz["personali"]} | {"Personale", "Commissioni", "Telefonate", "Pagamenti", "Casa", "Famiglia"})
        c3, c4 = st.columns(2, gap="small")
        cat_s = c3.selectbox("Categoria", cats + ["✍️ Un'altra…"], index=(cats.index(p["categoria"]) if p.get("categoria") in cats else cats.index("Personale")), key=k + "_cat")
        cat = c3.text_input("Nuova categoria", key=k + "_catn", placeholder="es. Scuola") if cat_s == "✍️ Un'altra…" else cat_s
        pr = c4.selectbox("Priorità", SZ_PRIORITA, index=SZ_PRIORITA.index(p.get("priorita")) if p.get("priorita") in SZ_PRIORITA else 1, key=k + "_pr")
        profili = st.session_state.get("_sz_nomi_p") or {}
        per_chi = ""
        if len(profili) > 1:
            ids = list(profili)
            dflt = p.get("profilo") or (st.session_state.get("_sz_profili_scelti") or ids)[0]
            per_chi = st.selectbox("👤 Per chi è", ids, index=ids.index(dflt) if dflt in ids else 0, format_func=profili.get, key=k + "_chi")
        importo = st.number_input("💶 Importo (facoltativo)", min_value=0.0, value=sz_num(p.get("importo")), step=1.0, format="%.2f", key=k + "_imp", placeholder="es. 35,00")
        ric0 = p.get("ricorrenza") or {}
        c5, c6 = st.columns([2, 1], gap="small")
        tipi = list(SZ_RICORRENZE)
        rt = c5.selectbox("🔁 Si ripete", tipi, index=tipi.index(ric0.get("tipo", "")) if ric0.get("tipo", "") in tipi else 0, format_func=SZ_RICORRENZE.get, key=k + "_rt")
        ogni = c6.number_input("Ogni", min_value=1, max_value=365, value=int(sz_num(ric0.get("ogni")) or 2), step=1, key=k + "_ogni") if rt in ("giorni", "settimane", "mesi") else 1
        files = list(p.get("files") or [])
        nuovi = st.file_uploader("📎 Foto o documento (facoltativo)", type=["jpg", "jpeg", "png", "webp", "pdf", "heic"], accept_multiple_files=True, key=k + "_f")
        if files:
            st.caption("Già allegati: " + ", ".join(str(f_.get("nome", "")) for f_ in files))
        with st.expander("🔔 Avvisi", expanded=not p):
            avvisi = _sz_ui_avvisi(k + "_av", p.get("avvisi") or {"anticipi": [1440, 0]}, imp)
        b1, b2 = st.columns(2, gap="small")
        if b1.button("💾 Salva", key=k + "_ok", type="primary", width="stretch"):
            rec = {"titolo": titolo, "descrizione": descr, "data": data.isoformat() if data else "", "ora": ora.strftime("%H:%M") if ora else "", "categoria": (cat or "Personale").strip(),
                   "priorita": pr, "importo": importo, "ricorrenza": {"tipo": rt, "ogni": int(ogni)}, "avvisi": avvisi, "profilo": per_chi}
            err = sz_valida_personale(rec)
            if err:
                for e in err:
                    st.warning(e)
                return
            try:
                for f_ in nuovi or []:
                    files.append(sc_file_salva(f_))
            except Exception as e:
                st.warning(f"Allegato non salvato: {e}")
            rec["files"] = files

            def _fn(sz_):
                if p:
                    x = next((y for y in sz_["personali"] if y.get("id") == p["id"]), None)
                    if x is not None:
                        x.update({kk: vv for kk, vv in rec.items() if kk != "ricorrenza"}, ricorrenza=dict(rec["ricorrenza"], giorno=sz_d(rec["data"]).day),
                                 modificato_il=_szdt.now().isoformat(timespec="seconds"), importo=sz_num(rec["importo"]))
                        sz_log(sz_, "modificata", "pers:" + x["id"], x["titolo"])
                else:
                    sz_nuova_personale(sz_, rec)
            _sz_salva(_fn, "scadenza personale")
            st.session_state.pop("sz_mod", None)
            st.session_state["sz_msg"] = "✅ Salvata."
            st.rerun()
        if b2.button("Annulla", key=k + "_no", width="stretch"):
            st.session_state.pop("sz_mod", None)
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# impostazioni: avvisi per categoria, suoni, ora, riepilogo, calendario
# ---------------------------------------------------------------------------------------------------------------------
def _sz_impostazioni(sz, voci, adesso):
    imp = dict(sz.get("impostazioni") or {})
    with st.expander("⚙️ Avvisi, suoni e riepilogo"):
        st.caption("Gli avvisi arrivano **anche ad app chiusa** sui canali scelti in **Utilità → 🔔 Avvisi** (Telegram, email, WhatsApp, SMS): il suono è quello di quell'app. "
                   "Il **suono qui sotto** è quello che senti **nell'app aperta**. Per avere la **sveglia del telefono** con suono e vibrazione anche senza internet, usa "
                   "**📅 Metti nel calendario del telefono** qui sotto.")
        c1, c2 = st.columns(2, gap="small")
        try:
            ora_av = c1.time_input("Ora degli avvisi (per le date senza ora)", value=_szdt.strptime(imp.get("ora_avvisi") or "09:00", "%H:%M").time(), key="szi_ora", step=900)
        except Exception:
            ora_av = None
        suono = c2.selectbox("Suono principale", list(SZ_SUONI), index=list(SZ_SUONI).index(imp.get("suono")) if imp.get("suono") in SZ_SUONI else 0, format_func=SZ_SUONI.get, key="szi_suono")
        _sz_anteprima(suono, "szi_prova", imp)
        if suono == "personale":
            up = st.file_uploader("🎙️ Il tuo suono (mp3/ogg/m4a, breve)", type=["mp3", "ogg", "m4a", "wav", "aac"], key="szi_file")
            if up is not None and up.size <= 600_000:
                imp["_nuovo_file"] = up
            elif up is not None:
                st.warning("Il file è troppo grande: scegline uno più corto (meno di 600 KB).")
        vib = st.toggle("📳 Vibrazione (se il telefono la permette)", value=imp.get("vibrazione", True), key="szi_vib")
        st.markdown("**🎵 Suono per categoria**")
        suoni_cat = dict(imp.get("suoni_categoria") or {})
        for cat, (ico, nome) in SZ_CATEGORIE.items():
            opz = [""] + list(SZ_SUONI)
            suoni_cat[cat] = st.selectbox(f"{ico} {nome}", opz, index=opz.index(suoni_cat.get(cat, "")) if suoni_cat.get(cat, "") in opz else 0,
                                          format_func=lambda x: "Il principale" if not x else SZ_SUONI[x], key="szi_sc_" + cat)
        st.markdown("**🔔 Avvisi di base per categoria** (ogni attività può avere i suoi)")
        cat_sel = st.selectbox("Categoria", list(SZ_CATEGORIE), format_func=lambda c: " ".join(SZ_CATEGORIE[c]), key="szi_cat")
        base_cat = dict(SZ_AVVISI_BASE, anticipi=list(SZ_AVVISI_CATEGORIA.get(cat_sel, SZ_AVVISI_BASE["anticipi"])), **((imp.get("avvisi_categoria") or {}).get(cat_sel) or {}))
        nuova_cat = _sz_ui_avvisi("szi_av_" + cat_sel, base_cat, imp, con_suono=False)
        st.markdown("**☀️ Riepilogo automatico**")
        rp = dict(imp.get("riepilogo") or {})
        c3, c4 = st.columns(2, gap="small")
        rp_on = c3.toggle("Ogni giorno", value=bool(rp.get("attivo")), key="szi_rp")
        try:
            rp_ora = c4.time_input("Alle", value=_szdt.strptime(rp.get("ora") or "07:30", "%H:%M").time(), key="szi_rp_ora", step=900)
        except Exception:
            rp_ora = None
        c5, c6 = st.columns(2, gap="small")
        rp_set = c5.toggle("Anche ogni settimana", value=bool(rp.get("settimanale")), key="szi_rps")
        giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
        rp_g = c6.selectbox("Il", list(range(7)), index=int(sz_num(rp.get("giorno")) or 0), format_func=lambda i: giorni[i], key="szi_rpg")
        st.caption("Il riepilogo e gli avvisi partono tra le 6 e le 23 circa (il controllo automatico gira ogni mezz'ora).")
        if st.button("💾 Salva le impostazioni", key="szi_ok", type="primary", width="stretch"):
            rif_file = None
            if imp.get("_nuovo_file") is not None:
                try:
                    rif_file = sc_file_salva(imp["_nuovo_file"])
                except Exception as e:
                    st.warning(f"Suono non salvato: {e}")

            def _fn(sz_):
                i_ = sz_["impostazioni"]
                i_["ora_avvisi"] = ora_av.strftime("%H:%M") if ora_av else "09:00"
                i_["suono"], i_["vibrazione"] = suono, vib
                i_["suoni_categoria"] = {k_: v_ for k_, v_ in suoni_cat.items() if v_}
                i_.setdefault("avvisi_categoria", {})[cat_sel] = nuova_cat
                i_["riepilogo"] = {"attivo": rp_on, "ora": rp_ora.strftime("%H:%M") if rp_ora else "07:30", "settimanale": rp_set, "giorno": rp_g}
                if rif_file:
                    i_["suono_file"] = rif_file
                sz_log(sz_, "impostazioni")
            _sz_salva(_fn, "impostazioni")
            st.session_state["sz_msg"] = "⚙️ Impostazioni salvate."
            st.rerun()
        st.markdown("**📅 Calendario del telefono**")
        st.caption("Scarica il file e aprilo: il telefono aggiunge le scadenze al suo **Calendario** con gli **allarmi** che hai scelto (suonano e vibrano anche ad app chiusa). "
                   "Se cambi qualcosa, scaricalo di nuovo: le attività si aggiornano (non si duplicano).")
        st.download_button("📅 Metti nel calendario del telefono", sz_ics(voci, sz, adesso), file_name="vitamemo_scadenziario.ics", mime="text/calendar", key="szi_ics",
                           width="stretch")


# ---------------------------------------------------------------------------------------------------------------------
# la pagina
# ---------------------------------------------------------------------------------------------------------------------
def _sz_prof_cb(princ):
    if not st.session_state.get("sz_prof_w"):
        st.session_state["sz_prof_w"] = [princ]                           # almeno uno resta sempre acceso


def _sz_imposta_periodo(p):
    st.session_state["sz_periodo"] = None if st.session_state.get("sz_periodo") == p else p


def schermata_scadenziario():
    st.markdown(_SZ_CSS, unsafe_allow_html=True)
    if "nav_pagine" in globals():
        nav_pagine("scadenziario")
    st.markdown("<div class='sz-hero'><div class='ico'>🗓️</div><div><h1>Scadenziario</h1>"
                "<p>Tutte le scadenze di VitaMemo in un posto solo: si aggiornano da sole dalle sezioni.</p></div></div>", unsafe_allow_html=True)
    if "pulsante_info" in globals():
        try:
            pulsante_info("scadenziario")
        except Exception:
            pass
    msg = st.session_state.pop("sz_msg", None)
    if msg:
        st.success(msg)
    adesso = _sz_adesso()
    try:
        voci, sz = _sz_voci(adesso)
    except Exception as e:
        st.error(f"Non riesco a leggere le scadenze: {type(e).__name__}: {e}")
        return
    d_pers, _x = _sz_dati()
    profili = sz_profili(d_pers)
    nomi_p = dict(profili)
    princ = profili[0][0]
    if len(profili) > 1:
        st.markdown("<div style='font-weight:800;margin:2px 0 4px'>👥 Di chi vuoi vedere le scadenze</div>", unsafe_allow_html=True)
        if not st.session_state.get("sz_prof_w"):
            st.session_state["sz_prof_w"] = [princ]                       # si parte sempre dal profilo principale
        st.markdown("<style>.st-key-sz_prof button[aria-pressed='false']{background:#0a0e18 !important;border:1px solid rgba(255,255,255,.14) !important;"
                    "box-shadow:inset 0 3px 7px rgba(0,0,0,.75) !important;opacity:.62;filter:grayscale(.55)}"
                    ".st-key-sz_prof button[aria-pressed='false'] p{color:#7d8798 !important}"
                    ".st-key-sz_prof button[aria-pressed='true']{background:rgba(255,92,138,.18) !important;border:2px solid #ff5c8a !important;"
                    "box-shadow:0 0 8px #ff5c8a,0 0 18px rgba(255,92,138,.75),inset 0 0 10px rgba(255,92,138,.45) !important;animation:sz-neon 1.7s ease-in-out infinite}"
                    ".st-key-sz_prof button[aria-pressed='true'] p{color:#ffe3ec !important;font-weight:800 !important;text-shadow:0 0 8px #ff5c8a}"
                    "@keyframes sz-neon{0%,100%{box-shadow:0 0 6px #ff5c8a,0 0 14px rgba(255,92,138,.6)}50%{box-shadow:0 0 12px #ff9ab8,0 0 28px rgba(255,92,138,.95)}}"
                    "@media (prefers-reduced-motion:reduce){.st-key-sz_prof button{animation:none !important}}</style>", unsafe_allow_html=True)
        _box_prof = st.container(key="sz_prof")
        scelti = _box_prof.pills("Di chi", [i for i, _n in profili], selection_mode="multi", format_func=lambda i: ("👤 " if i == princ else "👥 ") + nomi_p.get(i, "?"),
                          key="sz_prof_w", label_visibility="collapsed", on_change=_sz_prof_cb, args=(princ,)) or [princ]
        st.caption("Tocca i nomi per seguire anche le scadenze delle persone che segui (più nomi insieme si sommano). Quando rientri si riparte da **" + _sz_e(nomi_p[princ]) + "**.")
    else:
        scelti = [princ]
    st.session_state["_sz_profili_scelti"] = list(scelti)
    st.session_state["_sz_nomi_p"] = nomi_p
    voci = [v for v in voci if v.get("profilo") in scelti]
    rie = sz_riepilogo(voci, adesso)
    per = st.session_state.get("sz_periodo")
    with st.container(key="sz_tiles"):
        for k_, ico, nome in _SZ_TILES:
            st.button(f"{ico} {rie[k_]}\n{nome}", key=("szt_on_" if per == k_ else "szt_") + k_, width="stretch", on_click=_sz_imposta_periodo, args=(k_,))
    b1, b2 = st.columns(2, gap="small")
    if b1.button("➕ Nuova scadenza personale", key="sz_nuova", type="primary", width="stretch"):
        st.session_state["sz_mod"] = "nuova"
    vista = b2.segmented_control("Vista", ["📋 Per data", "🗂️ Per categoria"], default="📋 Per data", key="sz_vista", label_visibility="collapsed") or "📋 Per data"
    if st.session_state.get("sz_mod"):
        _sz_modulo(sz, st.session_state["sz_mod"])
    with st.expander("🔎 Cerca e filtra"):
        q = st.text_input("Cerca", key="sz_q", placeholder="es. bollo, dentista, mamma, condominio")
        c1, c2 = st.columns(2, gap="small")
        cats = c1.multiselect("Categoria", list(SZ_CATEGORIE), format_func=lambda c: " ".join(SZ_CATEGORIE[c]), key="sz_fc")
        stati = c2.multiselect("Stato", SZ_STATI, key="sz_fs")
        c3, c4 = st.columns(2, gap="small")
        prio = c3.multiselect("Priorità", SZ_PRIORITA, key="sz_fp")
        sez_pres = sorted({v.get("sezione") for v in voci if v.get("sezione")})
        sezioni = c4.multiselect("Sezione", sez_pres, format_func=lambda s: SZ_SEZIONI.get(s, s), key="sz_fz")
        solo_pers = st.checkbox("📌 Solo le mie scadenze personali", key="sz_fpers")
    filtrate = sz_filtra(voci, q, set(cats) or None, per or "", set(stati) or None, set(prio) or None, set(sezioni) or None, solo_pers, adesso)
    if not per and not stati:
        filtrate = [v for v in filtrate if v["stato"] not in ("Completata", "Annullata")]       # le completate stanno nel loro riquadro
    if per == "completate":
        filtrate.sort(key=lambda v: v["data"], reverse=True)
    titolo_lista = (dict((k_, n) for k_, _i, n in _SZ_TILES).get(per, "") if per else "Da fare") + f" · {len(filtrate)}"
    st.markdown(f"#### {titolo_lista}")
    if not filtrate:
        st.info("Niente da mostrare qui. 🎉" if not (q or cats or stati or prio or sezioni or solo_pers) else "Nessuna attività con questi filtri.")
    elif vista.startswith("🗂️"):
        gruppi = {}
        for v in filtrate:
            gruppi.setdefault(v["categoria"], []).append(v)
        for cat in [c for c in SZ_CATEGORIE if c in gruppi] + [c for c in gruppi if c not in SZ_CATEGORIE]:
            lst = gruppi[cat]
            n_sc = sum(1 for v in lst if v["stato"] == "Scaduta")
            ico, nome = SZ_CATEGORIE.get(cat, ("📌", cat))
            with st.expander(f"{ico} {nome} · {len(lst)}" + (f" · 🔴 {n_sc} scadute" if n_sc else ""), expanded=bool(n_sc)):
                for i, v in enumerate(lst[:60]):
                    st.markdown(_sz_card(v, adesso, sz), unsafe_allow_html=True)
                    _sz_azioni(v, adesso, sz, f"c{cat}{i}")
    else:
        n_max = st.session_state.get("sz_quanti", 40)
        ultimo = None
        for i, v in enumerate(filtrate[:n_max]):
            g = v["data"]
            if g != ultimo:
                gg = (g - adesso.date()).days
                st.markdown(f"<div class='sz-giorno'>{'Oggi' if gg == 0 else 'Domani' if gg == 1 else 'Ieri' if gg == -1 else ''} {g.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
                ultimo = g
            st.markdown(_sz_card(v, adesso, sz), unsafe_allow_html=True)
            _sz_azioni(v, adesso, sz, f"l{i}")
        if len(filtrate) > n_max and st.button(f"⬇️ Mostra altre {min(40, len(filtrate) - n_max)}", key="sz_altre", width="stretch"):
            st.session_state["sz_quanti"] = n_max + 40
            st.rerun()
    _sz_impostazioni(sz, voci, adesso)
    with st.expander("🧾 Registro delle modifiche"):
        for r in reversed((sz.get("registro") or [])[-30:]):
            st.caption(f"{str(r.get('il', ''))[:16].replace('T', ' ')} · {r.get('azione')} · {r.get('titolo', '')}")


# ---------------------------------------------------------------------------------------------------------------------
# avvisi nell'app aperta (suono + vibrazione), su ogni pagina: un controllo leggero ogni minuto
# ---------------------------------------------------------------------------------------------------------------------
def _sz_avvisi_app():
    if not st.session_state.get("sess"):
        return
    try:
        adesso = _sz_adesso()
        d, extra = _sz_dati()
        sz = d.get("scadenziario") if isinstance(d.get("scadenziario"), dict) else None
        if not sz:
            return
        visti = st.session_state.setdefault("_sz_suonati", set())
        nuovi = [(v, m, k) for v, m, k in sz_avvisi_da_mandare(d, adesso, 3, sz_raccogli(d, adesso, extra, solo_aperte=True)) if k not in visti]
        if not nuovi:
            return
        imp = sz.get("impostazioni") or {}
        for v, motivo, k in nuovi[:3]:
            visti.add(k)
            st.toast(f"⏰ {v['titolo']} — {_sz_quando(v, adesso)} ({motivo})", icon="🗓️")
        v0 = nuovi[0][0]
        nome = _sz_suono_di(sz, v0)
        import streamlit.components.v1 as _cmp
        _cmp.html(_sz_suono_html(nome, _sz_file_suono(imp) if nome == "personale" else "", bool(sz_cfg_avvisi(sz, v0).get("vibrazione", imp.get("vibrazione", True))), True, "🔔"),
                  height=0)
    except Exception:
        pass


# =====================================================================================================================
# AGGANCI: la sezione prima di Utilità, il pulsante colorato, la Home, il numero sul pulsante, la guida
# =====================================================================================================================
try:
    if "SEZIONI_NAV" in globals() and "scadenziario" not in SEZIONI_NAV:
        SEZIONI_NAV.insert(SEZIONI_NAV.index("utilita") if "utilita" in SEZIONI_NAV else len(SEZIONI_NAV), "scadenziario")
    if "NOMI_NAV" in globals():
        NOMI_NAV["scadenziario"] = "Scadenziario"
    if "_PN_VOCI" in globals() and not any(v_[0] == "scadenziario" for v_ in _PN_VOCI):
        _i_sz = next((i_ for i_, v_ in enumerate(_PN_VOCI) if v_[0] == "utilita"), len(_PN_VOCI))
        _PN_VOCI.insert(_i_sz, ("scadenziario", "🗓️ Scadenziario", SZ_COLORI[0], SZ_COLORI[1]))
    if "SC_ESCLUSE" in globals() and "scadenziario" not in SC_ESCLUSE:
        SC_ESCLUSE = tuple(SC_ESCLUSE) + ("scadenziario",)
    if "_SEZ_VALIDE" in globals():
        _SEZ_VALIDE.add("scadenziario")
except Exception:
    pass

if "schermata_farmacia" in globals() and "_sz_schermata_prima" not in globals():
    _sz_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                        # noqa: F811
        if st.session_state.get("sezione_home") == "scadenziario":
            return schermata_scadenziario()
        return _sz_schermata_prima()

if "pn_scadenze" in globals() and "_sz_scad_prima" not in globals():
    _sz_scad_prima = pn_scadenze

    def pn_scadenze():                                               # noqa: F811 — il pulsante 🗓️ lampeggia con le scadute e quelle di oggi
        out = _sz_scad_prima()
        try:
            adesso = _sz_adesso()
            d, extra = _sz_dati()
            urg = [v for v in sz_raccogli(d, adesso, extra, solo_aperte=True) if v["stato"] == "Scaduta" or v["data"] == adesso.date()]
            if urg:
                out["scadenziario"] = [f"{_SZ_ICO_STATO.get(v['stato'], '')} {v['titolo']}: {_sz_quando(v, adesso)}" for v in urg[:40]]
        except Exception:
            pass
        return out

if "nav_pagine" in globals() and "_sz_nav_prima" not in globals():
    _sz_nav_prima = nav_pagine

    def nav_pagine(corrente):                                        # noqa: F811
        if corrente != "scadenziario":
            st.session_state.pop("sz_prof_w", None)                    # rientrando nello Scadenziario si riparte dal profilo principale
        r = _sz_nav_prima(corrente)
        try:
            (st.fragment(run_every=60)(_sz_avvisi_app) if hasattr(st, "fragment") else _sz_avvisi_app)()
        except Exception:
            pass
        return r

if "_vm_riepilogo" in globals() and "_sz_riep_prima" not in globals():
    _sz_riep_prima = _vm_riepilogo

    def _vm_riepilogo(sc):                                           # noqa: F811 — in Home, sotto i pulsanti: 🗓️ Scadenziario (con le cose di oggi e in ritardo)
        try:
            st.markdown(_SZ_CSS, unsafe_allow_html=True)
            n = len((sc.get("scadenziario") if isinstance(sc, dict) else None) or pn_scadenze().get("scadenziario") or [])
            st.button("🗓️ Scadenziario" + (f" · 🔔 {n} da guardare" if n else ""), key="vm_sz", on_click=vm_apri, args=("scadenziario",))
        except Exception:
            pass
        return _sz_riep_prima({k: v for k, v in sc.items() if k != "scadenziario"} if isinstance(sc, dict) else sc)

if "_NOMI_SEZIONI" in globals():
    _NOMI_SEZIONI.setdefault("scadenziario", "🗓️ Scadenziario")
    if "_ID_GUIDA" in globals():
        _ID_GUIDA.setdefault("scadenziario", ["sz_cosa", "sz_azioni", "sz_personali", "sz_avvisi", "sz_cerca"])
    if "UI_IT" in globals():
        UI_IT.setdefault("sez_scadenziario", "🗓️ Scadenziario")
    _GUIDE.setdefault("scadenziario", [
        ("🗓️ Cos'è lo Scadenziario",
         """È il **centro di controllo** di tutte le scadenze: si apre dal pulsante **🗓️ Scadenziario**, prima di Utilità.
Raccoglie **da solo** quello che hai già scritto nelle sezioni: prodotti della Dispensa, medicinali, ricette, visite, vaccini, controlli, esenzioni, documenti, bollette e rate del condominio, garanzie e manutenzioni, bollo, assicurazione e revisione, animali, appuntamenti di tutte le sezioni, compleanni, la badante.
**Non copia niente**: se cambi una data nella sezione, qui cambia da sola; se paghi una bolletta o completi qualcosa nella sezione, qui sparisce.
In cima vedi i numeri: **🔴 Scadute, 📍 Oggi, 📆 7 giorni, 🗓️ 30 giorni, 🔭 Più avanti, ✅ Completate**: toccane uno per vedere solo quelle.""",
         "scadenziario scadenze tutte centro controllo riepilogo scadute oggi settimana mese completate sezioni"),
        ("✅ Fatto, ⏰ Rinvia, ⋯",
         """Sotto ogni attività:
- **✅ Fatto**: la segni completata (va nelle ✅ Completate). Se si ripete, compare **subito la prossima**.
- **⏰ Rinvia**: ti avviso di nuovo tra 1 ora, 3 ore, domani o quando vuoi. **La data della scadenza NON cambia.**
- **⋯**: **↗️ Apri la scheda originale** (ti porta nella sezione giusta), **🔔 Avvisi di questa attività**, **Priorità**, **👁️ Visto**, **❌ Annulla**; per le tue scadenze anche **✏️ Modifica, 📄 Duplica, 🗑️ Elimina**.
Le attività scadute restano **rosse** finché non fai qualcosa.""",
         "fatto completata rinvia posticipa avviso apri scheda originale modifica duplica elimina annulla priorità"),
        ("📌 Le mie scadenze personali",
         """Tocca **➕ Nuova scadenza personale** per tutto quello che non sta in altre sezioni: telefonare a qualcuno, ritirare un pacco, una commissione, una spesa.
Scrivi **titolo**, (se vuoi) **descrizione**, **data**, **ora**, **categoria** (anche una tua), **priorità**, **importo**, una **foto o documento**, se **si ripete** (ogni giorno, settimana, mese, anno o ogni N giorni/settimane/mesi) e gli **avvisi**. Poi **💾 Salva**.""",
         "scadenza personale nuova telefonare pacco commissione ricorrenza ripete categoria importo foto"),
        ("🔔 Avvisi e suoni",
         """Per ogni attività scegli **quando avvisarti**: 30, 15, 7, 3, 1 giorno prima, 1 ora prima, all'ora stabilita, oppure un tempo tuo (minuti, ore, giorni). Puoi farlo **ripetere ogni giorno finché non confermi**, o metterlo **in pausa** fino a una data.
Gli avvisi arrivano **anche ad app chiusa** su Telegram, email, WhatsApp o SMS (quelli scelti in **Utilità → 🔔 Avvisi**). Ogni categoria ha i suoi avvisi di base (in **⚙️ Avvisi, suoni e riepilogo**).
**Suoni**: scegli il suono (anche diverso per categoria o un **tuo file**) e tocca **▶ Ascolta**. Il suono e la vibrazione si sentono **con l'app aperta**; per avere la **sveglia del telefono** anche ad app chiusa e senza internet usa **📅 Metti nel calendario del telefono**.
**☀️ Riepilogo**: ogni mattina all'ora che vuoi (e, se vuoi, uno settimanale) con cosa fare oggi, appuntamenti, pagamenti, cose in ritardo e i prossimi giorni.""",
         "avvisi notifiche anticipo giorni ore minuti suono vibrazione ascolta calendario telefono sveglia riepilogo mattina settimanale pausa ripeti"),
        ("🔎 Cerca e filtra",
         """In **🔎 Cerca e filtra** scrivi una parola (es. «bollo», «dentista») oppure scegli **categoria, stato, priorità, sezione**, o **solo le mie scadenze**.
In alto puoi vedere tutto **📋 Per data** (in ordine di giorno e ora) oppure **🗂️ Per categoria** (ogni categoria si apre da sola).""",
         "cerca filtri categoria stato priorità sezione vista data categoria"),
    ])
