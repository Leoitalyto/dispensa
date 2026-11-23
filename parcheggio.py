# -*- coding: utf-8 -*-
"""🅿️ PARCHEGGIO — «Salva dove ho parcheggiato», dalla Home, accanto a 🛒 Spesa Smart (richiesta del 23/11/2026).

• Un tocco su «📍 Salva qui (GPS)»: il telefono trova dove sei (se consenti) e salva da solo; l'indirizzo si aggiunge da OpenStreetMap
  (gratuito, senza chiave). Oppure scrivi tu l'indirizzo o il posto.
• Facoltativi: foto (il piano, la colonna, il cartello), note (piano, posto, colore delle strisce), quale veicolo, scadenza della sosta
  (con il file per il calendario del telefono che suona 10 minuti prima).
• Per tornare: «🧭 Portami all'auto» (Google Maps a piedi), «🗺️ Mappa», «📤 Manda la posizione».
• «✅ Ho ripreso l'auto» → lo storico (ultimi 15). La posizione va anche nella scheda del veicolo in Auto («Ultima posizione salvata»).
Dati: d["parcheggio"] = {"attivo": {...} | None, "storico": [...]} nel file personale. Prefisso: pk_ / PK_."""
import base64 as _pk_b64
import datetime as _pk_dt
import json as _pk_json
import urllib.parse as _pk_url
import uuid as _pk_uuid

import streamlit as st

PK_ETICHETTA = "Dove (posizione GPS o indirizzo)"

_PK_JS = r"""
(function () {
  var w = window, doc = document;
  if (w.__pkGps1) return;
  w.__pkGps1 = true;
  function msg(t, errore) {
    var el = doc.querySelector('[data-pk-msg]');
    if (el) { el.textContent = t; el.style.display = 'block'; el.style.color = errore ? '#ff8a80' : '#69f0ae'; }
  }
  function gps() {
    if (!navigator.geolocation) { msg('Questo browser non sa dove ti trovi: scrivi tu l\'indirizzo.', true); return; }
    msg('📡 Cerco la tua posizione… (se il telefono lo chiede, tocca «Consenti»)');
    navigator.geolocation.getCurrentPosition(function (p) {
      var lat = p.coords.latitude.toFixed(6), lon = p.coords.longitude.toFixed(6), acc = Math.round(p.coords.accuracy || 0);
      var inp = doc.querySelector('input[aria-label="__ETICHETTA__"]');
      if (!inp) { msg('Posizione: ' + lat + ', ' + lon + '. Scrivila nel campo e salva.', true); return; }
      var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
      try { inp.focus(); } catch (e) {}
      setter.call(inp, lat + ', ' + lon + ' ±' + acc + 'm');
      inp.dispatchEvent(new w.Event('input', {bubbles: true}));
      try { inp.blur(); } catch (e) {}
      inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
      msg('✅ Trovata (precisione circa ' + acc + ' m). Salvo…');
      setTimeout(function () {
        var b = doc.querySelector('[class*="st-key-pk_salva"] button');
        if (b) b.click(); else msg('✅ Posizione scritta: ora tocca «💾 Salva il parcheggio».');
      }, 900);
    }, function (e) {
      msg(e && e.code === 1 ? 'Non hai dato il permesso alla posizione: in Chrome tocca il lucchetto accanto all\'indirizzo → Autorizzazioni → Posizione → Consenti. Oppure scrivi tu dove sei.'
                            : 'Non riesco a trovare la posizione adesso (poco segnale GPS?). Riprova all\'aperto o scrivi tu dove sei.', true);
    }, {enableHighAccuracy: true, timeout: 20000, maximumAge: 0});
  }
  doc.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('[data-pk-azione="gps"]') : null;
    if (!b) return;
    ev.preventDefault();
    gps();
  }, true);
})();
""".replace("__ETICHETTA__", PK_ETICHETTA)

_PK_CSS = """<style>
.pk-gps{border-radius:16px;padding:15px 10px;text-align:center;font-weight:900;font-size:1.08rem;color:#fff;cursor:pointer;user-select:none;
 background:linear-gradient(135deg,#1e88e5,#0d47a1);box-shadow:0 5px 0 rgba(0,30,90,.45),0 0 16px rgba(66,165,245,.55);-webkit-tap-highlight-color:transparent}
.pk-gps:active{transform:scale(.98)}
.pk-card{border:2px solid #42a5f5;border-radius:16px;padding:12px 14px;margin:6px 0 10px;background:rgba(66,165,245,.10)}
.pk-card b.pk-t{font-size:1.06rem}.pk-card .pk-s{opacity:.85;font-size:.9rem;margin-top:3px}
.pk-sosta{border-radius:12px;padding:8px 12px;margin:6px 0;font-weight:800}
.pk-ok{background:rgba(46,204,113,.15);border-left:6px solid #2ecc71}.pk-quasi{background:rgba(245,166,35,.18);border-left:6px solid #f5a623}.pk-scaduta{background:rgba(229,57,53,.2);border-left:6px solid #e53935}
</style>"""

_PK_CSS_HOME = """<style>
div[class*='st-key-vm_riga_ss'] [data-testid='stHorizontalBlock']{flex-wrap:nowrap !important;gap:10px !important;max-width:560px;margin:0 auto}
div[class*='st-key-vm_riga_ss'] [data-testid='stColumn']{min-width:0 !important;width:50% !important;flex:1 1 50% !important}
div[class*='st-key-vm_riga_ss'] .st-key-vm_ss{max-width:none !important;margin:0 !important}
div[class*='st-key-vm_riga_ss'] .st-key-vm_ss button p,.st-key-vm_pk button p{font-size:.98rem !important;white-space:nowrap}
.st-key-vm_pk button{width:100% !important;min-height:54px !important;border-radius:999px !important;background:linear-gradient(135deg,#020b1f,#0d47a1 60%,#42a5f5) !important;
 border:2px solid #42a5f5 !important;box-shadow:0 0 14px rgba(66,165,245,.6) !important}
.st-key-vm_pk button p{color:#fff !important;font-weight:900 !important}
</style>"""


# =====================================================================================================================
# logica
# =====================================================================================================================
def pk_ora():
    return _pk_dt.datetime.now().replace(microsecond=0)


def pk_coordinate(testo):
    """(lat, lon, precisione) da «45.070300, 7.686900 ±12m» (quello che scrive il GPS) o da una coppia di coordinate. None altrimenti."""
    import re
    m = re.fullmatch(r"\s*(-?\d{1,2}\.\d+)\s*[,;]\s*(-?\d{1,3}\.\d+)\s*(?:±\s*(\d+)\s*m)?\s*", str(testo or ""))
    if not m:
        return None
    lat, lon = float(m.group(1)), float(m.group(2))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon, (int(m.group(3)) if m.group(3) else None)


def pk_posizione(testo, geocodifica=None):
    """{testo, lat, lon, precisione} dal campo: se sono coordinate aggiunge l'indirizzo (se la funzione c'è)."""
    t = str(testo or "").strip()
    c = pk_coordinate(t)
    if not c:
        return {"testo": t}
    lat, lon, acc = c
    ind = ""
    if geocodifica:
        try:
            ind = geocodifica(lat, lon) or ""
        except Exception:
            ind = ""
    return {"testo": ind or f"{lat:.5f}, {lon:.5f} (GPS)", "lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "precisione": acc}


def pk_url_mappa(p):
    q = f"{p['lat']},{p['lon']}" if p.get("lat") and p.get("lon") else (p.get("testo") or "")
    return "https://www.google.com/maps/search/?api=1&query=" + _pk_url.quote_plus(q)


def pk_url_portami(p):
    q = f"{p['lat']},{p['lon']}" if p.get("lat") and p.get("lon") else (p.get("testo") or "")
    return "https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=" + _pk_url.quote_plus(q)


def pk_testo_condividi(p):
    righe = ["🅿️ La macchina è parcheggiata qui: " + (p.get("testo") or "")]
    if p.get("note"):
        righe.append("📝 " + p["note"])
    righe.append("🗺️ " + pk_url_mappa(p))
    return "\n".join(righe)


def pk_da_quanto(p, adesso=None):
    try:
        t = _pk_dt.datetime.fromisoformat(p["il"])
    except Exception:
        return ""
    s = int(((adesso or pk_ora()) - t).total_seconds())
    if s < 60:
        return "adesso"
    if s < 3600:
        return f"da {s // 60} min"
    if s < 86400:
        return f"da {s // 3600} h {s % 3600 // 60:02d} min"
    g = s // 86400
    return f"da {g} {'giorno' if g == 1 else 'giorni'}"


def pk_sosta(p, adesso=None):
    """(classe, testo) per la scadenza della sosta, o None."""
    try:
        f = _pk_dt.datetime.fromisoformat(p["sosta_fino"])
    except Exception:
        return None
    s = int((f - (adesso or pk_ora())).total_seconds())
    if s <= 0:
        return "pk-scaduta", f"⛔ La sosta è scaduta alle {f:%H:%M}" + ("" if f.date() == (adesso or pk_ora()).date() else f" del {f:%d/%m}")
    h, m = s // 3600, s % 3600 // 60
    resto = (f"{h} h {m:02d} min" if h else f"{m} min")
    return ("pk-quasi" if s <= 900 else "pk-ok"), f"⏰ La sosta scade alle {f:%H:%M} (fra {resto})"


def pk_ics(p):
    """Il file per il calendario del telefono: un evento alla scadenza della sosta con l'avviso 10 minuti prima."""
    f = _pk_dt.datetime.fromisoformat(p["sosta_fino"])
    fmt = "%Y%m%dT%H%M%S"
    luogo = (p.get("testo") or "").replace(",", "\\,").replace(";", "\\;")
    desc = pk_testo_condividi(p).replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VitaMemo//Parcheggio//IT", "BEGIN:VEVENT",
             f"UID:pk-{p.get('id')}@vitamemo", f"DTSTAMP:{pk_ora().strftime(fmt)}", f"DTSTART:{f.strftime(fmt)}", f"DTEND:{(f + _pk_dt.timedelta(minutes=5)).strftime(fmt)}",
             "SUMMARY:🅿️ Scade la sosta", f"LOCATION:{luogo}", f"DESCRIPTION:{desc}",
             "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Tra 10 minuti scade la sosta", "TRIGGER:-PT10M", "END:VALARM",
             "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(righe) + "\r\n").encode("utf-8")


def pk_salva_in(d, p, max_storico=15):
    """Mette il parcheggio nuovo come attivo (il vecchio va nello storico) e lo scrive anche nel veicolo scelto, in Auto."""
    pk = d.setdefault("parcheggio", {})
    vecchio = pk.get("attivo")
    if vecchio:
        pk.setdefault("storico", []).insert(0, dict(vecchio, ripreso_il=vecchio.get("ripreso_il") or p["il"]))
    pk["attivo"] = p
    pk["storico"] = (pk.get("storico") or [])[:max_storico]
    vid = p.get("veicolo")
    for v in ((d.get("auto") or {}).get("veicoli") or []):
        if vid and v.get("id") == vid:
            v["posizione"] = {k: p[k] for k in ("testo", "lat", "lon") if p.get(k)}
            v["posizione"]["data"] = p["il"][:10]


def pk_ripresa_in(d, adesso=None):
    pk = d.setdefault("parcheggio", {})
    a = pk.get("attivo")
    if a:
        pk.setdefault("storico", []).insert(0, dict(a, ripreso_il=(adesso or pk_ora()).isoformat()))
        pk["storico"] = pk["storico"][:15]
    pk["attivo"] = None


# =====================================================================================================================
# Streamlit
# =====================================================================================================================
def _pk_dati():
    try:
        return dict((sc_dati() or {}).get("parcheggio") or {})
    except Exception:
        return {}


def _pk_veicoli():
    try:
        return [v for v in ((sc_dati() or {}).get("auto") or {}).get("veicoli") or [] if isinstance(v, dict) and v.get("id")]
    except Exception:
        return []


def _pk_nome_veicolo(v):
    nome = " ".join(str(v.get(k) or "") for k in ("marca", "modello")).strip() or str(v.get("nome") or "Veicolo")
    return nome + (f" · {v['targa']}" if v.get("targa") else "")


def _pk_inietta():
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + _pk_json.dumps(_PK_JS) + ";P.document.head.appendChild(s);s.parentNode.removeChild(s);})();</script>")
    if "pn_inietta_una_volta" in globals():
        pn_inietta_una_volta("parcheggio_gps", "1", pagina)
    else:
        try:
            st.html(pagina, unsafe_allow_javascript=True)
        except Exception:
            pass


def _pk_foto(p):
    if not p.get("foto"):
        return None
    try:
        f_ = _fa_inv_allegati([p["foto"]]) if "_fa_inv_allegati" in globals() else []
        return f_[0][2] if f_ else None
    except Exception:
        return None


def _pk_mostra(p):
    nota = f"<br>📝 {sc_esc(p['note'])}" if p.get("note") else ""
    veic = f"<br>🚗 {sc_esc(p['veicolo_nome'])}" if p.get("veicolo_nome") else ""
    prec = f" · precisione circa {p['precisione']} m" if p.get("precisione") else ""
    try:
        quando = _pk_dt.datetime.fromisoformat(p["il"]).strftime("%d/%m alle %H:%M")
    except Exception:
        quando = ""
    st.markdown(f"<div class='pk-card'><b class='pk-t'>📍 {sc_esc(p.get('testo') or '')}</b><div class='pk-s'>🕒 {quando} ({pk_da_quanto(p)}){prec}{veic}{nota}</div></div>",
                unsafe_allow_html=True)
    sosta = pk_sosta(p)
    if sosta:
        st.markdown(f"<div class='pk-sosta {sosta[0]}'>{sosta[1]}</div>", unsafe_allow_html=True)
    foto = _pk_foto(p)
    if foto:
        st.image(foto, width="stretch")


def _pk_attivo(p):
    _pk_mostra(p)
    st.link_button("🧭 Portami all'auto (a piedi)", pk_url_portami(p), type="primary", width="stretch")
    c1, c2 = st.columns(2, gap="small")
    c1.link_button("🗺️ Mappa", pk_url_mappa(p), width="stretch")
    testo = pk_testo_condividi(p)
    c2.link_button("📤 Manda", "https://wa.me/?text=" + _pk_url.quote(testo), width="stretch", help="Manda la posizione con WhatsApp")
    if p.get("sosta_fino"):
        try:
            st.download_button("📲 Avviso nel calendario (10 min prima)", pk_ics(p), file_name="sosta.ics", mime="text/calendar", width="stretch", key="pk_ics")
        except Exception:
            pass
    if st.button("✅ Ho ripreso l'auto", key="pk_ripresa", width="stretch"):
        sc_salva(lambda d: pk_ripresa_in(d), "Parcheggio: auto ripresa")
        st.toast("✅ Bene! Il parcheggio va nello storico.")
        sc_rerun()


def _pk_nuovo(vecchio):
    st.markdown("**📍 Salva il parcheggio**" if not vecchio else "**🔄 Hai parcheggiato da un'altra parte? Salva qui il nuovo posto**")
    _pk_inietta()
    n_ = st.session_state.get("pk_n", 0)                             # cambia dopo ogni salvataggio: i campi ripartono vuoti
    st.markdown("<div class='pk-gps' role='button' tabindex='0' data-pk-azione='gps'>📍 Salva qui (GPS)</div>"
                "<div data-pk-msg style='display:none;margin:6px 0;font-weight:700;font-size:13.5px'></div>", unsafe_allow_html=True)
    st.caption("Un tocco: il telefono trova dove sei e salva da solo. **Oppure scrivi tu** l'indirizzo o il posto qui sotto.")
    testo = st.text_input(PK_ETICHETTA, key=f"pk_testo{n_}", placeholder="es. Via Roma 10, Torino · parcheggio Ikea, fila C")
    with st.expander("➕ Foto, note, veicolo, scadenza della sosta (facoltativo)"):
        note = st.text_input("📝 Note (piano, posto, colonna, colore delle strisce…)", key=f"pk_note{n_}", placeholder="es. Piano -2, colonna B14, strisce blu")
        foto = st.file_uploader("📷 Foto (il cartello del piano, la colonna, la via)", type=["jpg", "jpeg", "png", "webp", "heic"], key=f"pk_foto{n_}")
        veicoli = _pk_veicoli()
        vid = None
        if veicoli:
            ids = [None] + [v["id"] for v in veicoli]
            nomi = {v["id"]: _pk_nome_veicolo(v) for v in veicoli}
            vid = st.selectbox("🚗 Quale veicolo", ids, index=1, key=f"pk_veicolo{n_}", format_func=lambda i: "— nessuno —" if i is None else nomi[i])
        sosta = st.toggle("⏰ La sosta ha una scadenza (strisce blu, disco orario…)", key=f"pk_sosta_si{n_}")
        fino = None
        if sosta:
            c1, c2 = st.columns(2, gap="small")
            ore = c1.number_input("Ore", min_value=0, max_value=48, value=1, step=1, key=f"pk_sosta_h{n_}")
            minuti = c2.selectbox("Minuti", [0, 15, 30, 45], index=0, key=f"pk_sosta_m{n_}")
            fino = pk_ora() + _pk_dt.timedelta(hours=int(ore), minutes=int(minuti))
            st.caption(f"Scade alle **{fino:%H:%M}**" + ("" if fino.date() == pk_ora().date() else f" del {fino:%d/%m}") + ". Dopo il salvataggio puoi metterlo nel calendario del telefono con l'avviso.")
    if st.button("💾 Salva il parcheggio", key="pk_salva", type="primary", width="stretch"):
        if not str(testo or "").strip():
            st.error("Tocca «📍 Salva qui (GPS)» oppure scrivi dove hai parcheggiato.")
            return
        geo = globals().get("au_geocodifica")
        with st.spinner("Salvo… (cerco anche l'indirizzo)"):
            pos = pk_posizione(testo, geo)
            p = {"id": _pk_uuid.uuid4().hex[:10], "il": pk_ora().isoformat(), **pos,
                 "note": str(st.session_state.get(f"pk_note{n_}") or "").strip()}
            if fino:
                p["sosta_fino"] = fino.isoformat()
            vid_ = st.session_state.get(f"pk_veicolo{n_}") if veicoli else None
            if vid_:
                p["veicolo"] = vid_
                p["veicolo_nome"] = next((_pk_nome_veicolo(v) for v in veicoli if v["id"] == vid_), "")
            up = st.session_state.get(f"pk_foto{n_}")
            if up is not None:
                try:
                    dati, mime, nome = up.getvalue(), up.type or "image/jpeg", up.name or "parcheggio.jpg"
                    try:
                        from PIL import Image, ImageOps
                        import io as _pk_io
                        im = ImageOps.exif_transpose(Image.open(_pk_io.BytesIO(dati))).convert("RGB")
                        im.thumbnail((1400, 1400))
                        b = _pk_io.BytesIO()
                        im.save(b, "JPEG", quality=80)
                        dati, mime, nome = b.getvalue(), "image/jpeg", "parcheggio.jpg"
                    except Exception:
                        pass
                    fid = "pk_" + _pk_uuid.uuid4().hex[:12]
                    _ca_scrivi_file(fid, nome, mime, dati)
                    p["foto"] = {"id": fid, "nome": nome, "mime": mime}
                except Exception:
                    pass
            sc_salva(lambda d, p=p: pk_salva_in(d, p), "Parcheggio: posizione salvata")
        st.session_state["pk_n"] = n_ + 1
        st.toast("🅿️ Parcheggio salvato")
        sc_rerun()


def pk_corpo():
    st.markdown(_PK_CSS, unsafe_allow_html=True)
    pk = _pk_dati()
    a = pk.get("attivo")
    if a:
        _pk_attivo(a)
        st.divider()
        with st.expander("🔄 Ho parcheggiato da un'altra parte"):
            _pk_nuovo(a)
    else:
        _pk_nuovo(None)
    storico = [x for x in pk.get("storico") or [] if isinstance(x, dict)]
    if storico:
        with st.expander(f"🕘 Parcheggi precedenti ({len(storico)})"):
            for i, x in enumerate(storico):
                try:
                    q = _pk_dt.datetime.fromisoformat(x["il"]).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    q = ""
                a1, a2 = st.columns([4, 1], gap="small")
                a1.markdown(f"**{sc_esc(x.get('testo') or '')}**  \n<small>{q}" + (f" · {sc_esc(x['note'])}" if x.get("note") else "") + "</small>", unsafe_allow_html=True)
                a2.link_button("🗺️", pk_url_mappa(x), width="stretch")


@st.dialog("🅿️ Dove ho parcheggiato", width="large")
def pk_dialogo():
    if st.button("✖ Chiudi", key="pk_chiudi", width="stretch"):
        st.session_state.pop("_sc_dlg", None)
        st.rerun()
    pk_corpo()


def pk_etichetta_home():
    a = _pk_dati().get("attivo")
    if not a:
        return "🅿️ Parcheggio"
    s = pk_sosta(a)
    return "🅿️ Dov'è l'auto" + (" ⛔" if s and s[0] == "pk-scaduta" else " ⏰" if s and s[0] == "pk-quasi" else "")


def _pk_apri():
    st.session_state["pk_apri"] = True


# --- in Home: accanto a 🛒 Spesa Smart ------------------------------------------------------------------------------------
if "_vm_riepilogo" in globals() and "_pk_riep_prima" not in globals():
    _pk_riep_prima = _vm_riepilogo

    def _vm_riepilogo(sc):                                           # noqa: F811
        if st.session_state.pop("pk_apri", False):
            try:
                pk_dialogo()
            except Exception:
                pass
        return _pk_riep_prima(sc)
