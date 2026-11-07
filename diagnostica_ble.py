# -*- coding: utf-8 -*-
"""DIAGNOSTICA · COLLEGA DISPOSITIVO (dongle OBD-II Bluetooth a basso consumo, BLE).

COSA È POSSIBILE (e cosa no) — detto chiaramente:
• Un sito web su Chrome/Android può parlare SOLO con dispositivi Bluetooth a BASSO CONSUMO (BLE, «Bluetooth 4.0 o superiore»). Quasi tutti i dongle economici sono invece Bluetooth CLASSICO (SPP) e quelli Wi-Fi usano un collegamento che il browser non può aprire: con questi NON si può. Per loro c'è «Leggi codici errore» (si scrivono i codici letti con un'app o in officina).
• Per essere compatibile con il maggior numero possibile di dongle BLE il browser cerca da solo il servizio giusto fra molti profili noti (FFF0, FFE0, 18F0, Nordic UART, ISSC, E7810A71…) e sceglie la caratteristica che «avvisa» e quella che «scrive».
• Parla il linguaggio ELM327 (AT) e usa SOLO comandi di LETTURA: 0101 (spia motore e numero codici), 03 (memorizzati), 07 (in attesa), 0A (permanenti), 0902 (VIN), ATRV (tensione 12V). NON invia mai il comando che CANCELLA i codici.
• Il browser manda al programma i testi grezzi; la DECODIFICA dei codici è in Python (si prova senza dongle). I codici si spiegano con diagnostica_dtc.py.
• Non è stato provato su dongle veri (non ho dongle né un telefono qui): l'app non dichiara compatibile nessun dongle. Chi lo prova può segnare «Ha funzionato» / «Non ha funzionato» e il risultato si accumula in un elenco condiviso (conoscenza/dongle.json).
Caricato dopo diagnostica_dtc.py."""
import json
import re
import uuid
from datetime import datetime

import streamlit as st

DG_PERCORSO_DONGLE = "conoscenza/dongle.json"

# ---------------------------------------------------------------------------------------------------------------------
# il browser: collega, manda i comandi di sola lettura, restituisce i testi grezzi
# ---------------------------------------------------------------------------------------------------------------------
_DG_BLE_JS = r"""
(function () {
  var w = window, doc = document, nav = navigator;
  if (w.__dgBle) return;
  w.__dgBle = true;
  var SERVIZI = ['0000fff0-0000-1000-8000-00805f9b34fb', '0000ffe0-0000-1000-8000-00805f9b34fb', '000018f0-0000-1000-8000-00805f9b34fb', '0000ffe5-0000-1000-8000-00805f9b34fb',
    '0000ae00-0000-1000-8000-00805f9b34fb', '6e400001-b5a3-f393-e0a9-e50e24dcca9e', '49535343-fe7d-4ae5-8fa9-9fafd205e455', 'e7810a71-73ae-499d-8c15-faa9aef0c3f2',
    '0000fee7-0000-1000-8000-00805f9b34fb', '00001800-0000-1000-8000-00805f9b34fb', '0000180a-0000-1000-8000-00805f9b34fb'];
  var occupato = false;
  function msg(t, errore) {
    var el = doc.querySelector('[data-dg-msg]');
    if (el) { el.textContent = t; el.style.display = 'block'; el.style.color = errore ? '#b71c1c' : '#4a148c'; }
  }
  function consegna(obj) {
    var inp = doc.querySelector('input[aria-label="dg-ble-ricezione"]');
    if (!inp) { msg('Non trovo il campo di ricezione: riapri la pagina.', true); return; }
    var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
    try { inp.focus(); } catch (e) {}
    setter.call(inp, JSON.stringify(obj));
    inp.dispatchEvent(new w.Event('input', {bubbles: true}));
    ['keydown', 'keypress', 'keyup'].forEach(function (t) {
      inp.dispatchEvent(new w.KeyboardEvent(t, {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
    });
    try { inp.blur(); } catch (e) {}
    inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
  }
  function pausa(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  async function trovaCanali(server) {
    var servizi = [];
    try { servizi = await server.getPrimaryServices(); } catch (e) { servizi = []; }
    var migliore = null;
    for (var i = 0; i < servizi.length; i++) {
      var chars = [];
      try { chars = await servizi[i].getCharacteristics(); } catch (e) { continue; }
      var notifica = null, scrivi = null;
      for (var j = 0; j < chars.length; j++) {
        var p = chars[j].properties || {};
        if ((p.notify || p.indicate) && !notifica) notifica = chars[j];
        if ((p.write || p.writeWithoutResponse) && !scrivi) scrivi = chars[j];
      }
      // preferisco la caratteristica che fa entrambe le cose (FFE1) o la coppia nello stesso servizio
      for (var k = 0; k < chars.length; k++) {
        var q = chars[k].properties || {};
        if ((q.notify || q.indicate) && (q.write || q.writeWithoutResponse)) { notifica = chars[k]; scrivi = chars[k]; break; }
      }
      if (notifica && scrivi) { migliore = {servizio: servizi[i].uuid, notifica: notifica, scrivi: scrivi}; break; }
    }
    return migliore;
  }
  async function leggi() {
    if (occupato) return;
    if (!nav.bluetooth || !nav.bluetooth.requestDevice) {
      msg('Questo browser non può usare il Bluetooth dei siti. Usa Chrome su Android (non Safari né Firefox), con il Bluetooth e la posizione attivi.', true);
      consegna({ok: false, errore: 'bluetooth_non_supportato'});
      return;
    }
    occupato = true;
    var dev = null, buffer = '', attesa = null;
    try {
      msg('Scegli il dongle OBD dall\'elenco che compare (se non lo vedi: potrebbe essere Bluetooth classico o Wi-Fi, non compatibile).');
      dev = await nav.bluetooth.requestDevice({acceptAllDevices: true, optionalServices: SERVIZI});
      msg('Mi collego a ' + (dev.name || 'dispositivo') + '…');
      var server = await dev.gatt.connect();
      var canali = await trovaCanali(server);
      if (!canali) { throw new Error('canali_non_trovati'); }
      var enc = new TextEncoder(), dec = new TextDecoder();
      function dati(ev) {
        buffer += dec.decode(ev.target.value);
        if (attesa && buffer.indexOf('>') >= 0) { var r = attesa; attesa = null; r(); }
      }
      await canali.notifica.startNotifications();
      canali.notifica.addEventListener('characteristicvaluechanged', dati);
      async function cmd(c, timeout) {
        buffer = '';
        var fatto = new Promise(function (res) { attesa = res; });
        var bytes = enc.encode(c + '\r');
        var p = canali.scrivi.properties || {};
        for (var o = 0; o < bytes.length; o += 20) {
          var pezzo = bytes.slice(o, o + 20);
          if (p.writeWithoutResponse && canali.scrivi.writeValueWithoutResponse) await canali.scrivi.writeValueWithoutResponse(pezzo);
          else await canali.scrivi.writeValue(pezzo);
        }
        await Promise.race([fatto, pausa(timeout || 4000)]);
        attesa = null;
        return buffer.replace(/>/g, '').replace(/\r/g, '\n').trim();
      }
      var grezzo = {};
      msg('Preparo il dialogo con il dongle…');
      grezzo.ATZ = await cmd('ATZ', 5000);
      await cmd('ATE0', 2500); await cmd('ATL0', 2500); await cmd('ATS0', 2500); await cmd('ATH0', 2500);
      await cmd('ATSP0', 3000);
      msg('Cerco la centralina del veicolo (accendi il quadro, motore spento o al minimo)…');
      grezzo['0100'] = await cmd('0100', 12000);
      grezzo.ATDP = await cmd('ATDP', 3000);
      grezzo.ATRV = await cmd('ATRV', 3000);
      msg('Leggo i codici (solo lettura)…');
      grezzo['0101'] = await cmd('0101', 6000);
      grezzo['03'] = await cmd('03', 8000);
      grezzo['07'] = await cmd('07', 8000);
      grezzo['0A'] = await cmd('0A', 8000);
      try { grezzo['0902'] = await cmd('0902', 9000); } catch (e) { grezzo['0902'] = ''; }
      try { canali.notifica.removeEventListener('characteristicvaluechanged', dati); } catch (e) {}
      try { dev.gatt.disconnect(); } catch (e) {}
      msg('Letto. Guarda i risultati qui sotto.');
      consegna({ok: true, dispositivo: dev.name || '', servizio: canali.servizio, grezzo: grezzo, ts: Date.now()});
    } catch (e) {
      var nome = e && e.name ? e.name : '', testo = e && e.message ? e.message : String(e);
      if (nome === 'NotFoundError' && /cancel|chosen|selected/i.test(testo)) { msg('Annullato: nessun dispositivo scelto.'); consegna({ok: false, errore: 'annullato', ts: Date.now()}); }
      else if (testo === 'canali_non_trovati') { msg('Il dispositivo si è collegato ma non offre un canale seriale conosciuto: non è compatibile.', true); consegna({ok: false, errore: 'canali_non_trovati', dispositivo: dev && dev.name || '', ts: Date.now()}); }
      else { msg('Non sono riuscito a collegarmi o a leggere: ' + testo, true); consegna({ok: false, errore: testo.slice(0, 160), dispositivo: dev && dev.name || '', ts: Date.now()}); }
      try { if (dev && dev.gatt && dev.gatt.connected) dev.gatt.disconnect(); } catch (e2) {}
    }
    occupato = false;
  }
  doc.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('[data-dg-azione]') : null;
    if (!b) return;
    ev.preventDefault();
    if (b.getAttribute('data-dg-azione') === 'collega') leggi();
  }, true);
})();
"""

_DG_CSS = """<style>.dg-ble{border-radius:14px;padding:14px 10px;text-align:center;font-weight:900;font-size:1.05rem;color:#fff;cursor:pointer;user-select:none;background:linear-gradient(135deg,#8e24aa,#4527a0);box-shadow:0 5px 0 rgba(50,20,110,.4);-webkit-tap-highlight-color:transparent;margin:6px 0}
.dg-ble:active{transform:scale(.98)}.st-key-dg_ricezione{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;opacity:0}</style>"""


# ---------------------------------------------------------------------------------------------------------------------
# la decodifica (in Python, provabile senza dongle)
# ---------------------------------------------------------------------------------------------------------------------
_SCARTA = ("SEARCHING", "NO DATA", "UNABLE", "BUS", "ERROR", "STOPPED", "CAN ", "?", "ELM", "OK", "DATA", "BUFFER", "FB ", "ACT ", "LV ")


def _dg_messaggi(testo, sid):
    """I messaggi (stringhe esadecimali) che iniziano con la risposta attesa (es. '43'), con le righe multi-frame «0:», «1:» riunite."""
    righe = [r.strip().upper() for r in re.split(r"[\r\n]+", str(testo or "")) if r.strip()]
    msg, corrente = [], None
    for r in righe:
        if any(r.startswith(x) for x in _SCARTA) or "UNABLE" in r or "NO DATA" in r:
            continue
        m = re.match(r"^([0-9A-F]):\s*(.*)$", r)
        brut = re.sub(r"[^0-9A-F]", "", m.group(2) if m else r)
        if m:                                              # riga di un messaggio lungo: si accoda
            corrente = (corrente or "") + brut
            continue
        if corrente is not None:
            msg.append(corrente)
            corrente = None
        if len(brut) == 3 and " " not in r:                 # «008»: solo la lunghezza che precede un messaggio lungo
            continue
        if brut:
            msg.append(brut)
    if corrente is not None:
        msg.append(corrente)
    return [x for x in msg if x.startswith(sid)]


def dg_decodifica_dtc(testo, modo="03", can=None):
    """I codici di una risposta ai comandi 03 (memorizzati), 07 (in attesa), 0A (permanenti). can=True se il protocollo è CAN (il primo byte dopo la risposta è il numero di codici)."""
    sid = {"03": "43", "07": "47", "0A": "4A"}[modo]
    codici = []
    for m in _dg_messaggi(testo, sid):
        i = m.find(sid)
        b = [int(m[k:k + 2], 16) for k in range(i + 2, len(m) - 1, 2)]
        if not b:
            continue
        coppie = lambda dati: [(dati[k], dati[k + 1]) for k in range(0, len(dati) - 1, 2)]
        if can is True:
            n = b[0]
            cp = coppie(b[1:])[:n] if n else []
        elif can is False:
            cp = coppie(b)
        else:                                               # protocollo non noto: se il primo byte è il numero dei codici non nulli, è un conteggio
            resto = coppie(b[1:])
            nz = sum(1 for x in resto if x != (0, 0))
            cp = resto[:b[0]] if b[0] == nz and nz > 0 else coppie(b)
        for hi, lo in cp:
            if hi == 0 and lo == 0:
                continue
            val = (hi << 8) | lo
            c = "PCBU"[(val >> 14) & 3] + str((val >> 12) & 3) + format(val & 0xFFF, "03X")
            if c not in codici:
                codici.append(c)
    return codici


def dg_stato_motore(testo):
    """Da 0101: (spia motore accesa, numero di codici memorizzati) oppure (None, None)."""
    for m in _dg_messaggi(testo, "4101"):
        i = m.find("4101")
        try:
            a = int(m[i + 4:i + 6], 16)
            return bool(a & 0x80), a & 0x7F
        except ValueError:
            continue
    return None, None


def dg_tensione(testo):
    m = re.search(r"(\d{1,2}(?:[.,]\d)?)\s*V", str(testo or ""), re.I)
    return float(m.group(1).replace(",", ".")) if m else None


def dg_vin(testo):
    """Il VIN (17 caratteri) da 0902, se il dongle lo restituisce."""
    msgs = _dg_messaggi(testo, "4902")
    if not msgs:
        return ""
    testo_hex = "".join(msgs)
    i = testo_hex.find("4902")
    b = [int(testo_hex[k:k + 2], 16) for k in range(i + 4, len(testo_hex) - 1, 2)]
    if b and b[0] in (1, 2):
        b = b[1:]
    vin = "".join(chr(x) for x in b if 48 <= x <= 90 and chr(x) not in "IOQ" or 97 <= x <= 122)
    vin = vin.upper()
    return vin[-17:] if len(vin) >= 17 else ""


def dg_protocollo_can(testo):
    t = str(testo or "").upper()
    if "CAN" in t or "15765" in t:
        return True
    if any(x in t for x in ("9141", "14230", "KWP", "J1850", "SAE")):
        return False
    return None


def dg_analizza(payload):
    """Dal testo grezzo del dongle a un risultato leggibile."""
    g = payload.get("grezzo") or {}
    can = dg_protocollo_can(g.get("ATDP"))
    sem_trovato = "UNABLE" in str(g.get("0100", "")).upper() or "ERROR" in str(g.get("0100", "")).upper()
    mil, n = dg_stato_motore(g.get("0101"))
    return {"dispositivo": payload.get("dispositivo", ""), "protocollo": str(g.get("ATDP", "")).strip().replace("\n", " ")[:60], "tensione": dg_tensione(g.get("ATRV")),
            "mil": mil, "conteggio": n, "memorizzati": dg_decodifica_dtc(g.get("03"), "03", can), "in_attesa": dg_decodifica_dtc(g.get("07"), "07", can),
            "permanenti": dg_decodifica_dtc(g.get("0A"), "0A", can), "vin": dg_vin(g.get("0902")), "veicolo_non_trovato": sem_trovato, "ts": payload.get("ts")}


# ---------------------------------------------------------------------------------------------------------------------
# elenco condiviso dei dongle provati
# ---------------------------------------------------------------------------------------------------------------------
def dg_dongle_leggi():
    try:
        d = carica_dati(crea_archivio(), DG_PERCORSO_DONGLE)
    except Exception:
        return []
    return [x for x in (d or {}).get("provati", []) if isinstance(x, dict)]


def dg_dongle_segna(nome, esito, protocollo=""):
    def _m(d):
        d.setdefault("provati", []).append({"id": uuid.uuid4().hex[:8], "nome": (nome or "sconosciuto")[:60], "esito": esito, "protocollo": protocollo[:40], "data": datetime.now().strftime("%Y-%m-%d")})
        if len(d["provati"]) > 500:
            del d["provati"][:len(d["provati"]) - 500]
    try:
        salva_file(DG_PERCORSO_DONGLE, _m, f"Dongle provato: {nome}")
        return True
    except Exception:
        return False


def dg_dongle_riepilogo(voci):
    r = {}
    for x in voci:
        k = (x.get("nome") or "").strip().lower()
        e = r.setdefault(k, {"nome": x.get("nome"), "ok": 0, "no": 0})
        e["ok" if x.get("esito") == "ok" else "no"] += 1
    return sorted(r.values(), key=lambda e: (-e["ok"], e["nome"] or ""))


# ---------------------------------------------------------------------------------------------------------------------
# la schermata
# ---------------------------------------------------------------------------------------------------------------------
def _dg_inietta():
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(_DG_BLE_JS) + ";P.document.head.appendChild(s);s.parentNode.removeChild(s);})();</script>")
    if "pn_inietta_una_volta" in globals():
        pn_inietta_una_volta("dgble", "1", pagina)
    else:
        try:
            st.html(pagina, unsafe_allow_javascript=True)
        except Exception:
            pass


def dg_dispositivo(v=None):
    """«Collega dispositivo diagnostico»: lettura dei codici da un dongle OBD-II Bluetooth BLE (sperimentale)."""
    st.markdown("#### 🔌 Collega dispositivo diagnostico")
    st.warning("🧪 **Funzione sperimentale.** Non è stata provata su dongle veri: per questo non dichiaro compatibile nessun dongle. Se la provi, ti chiedo di segnare se ha funzionato.")
    st.markdown("**Cosa serve e cosa no**")
    st.markdown("- ✅ Un dongle OBD-II con **Bluetooth a basso consumo (BLE)**: sulla confezione cerca «**Bluetooth 4.0**» o superiore, «**BLE**».\n"
                "- ❌ Non funzionano da qui i dongle **Bluetooth classico** (la maggior parte dei più economici), **Wi-Fi** e **USB**, e quelli che richiedono la loro app: il browser non può usarli.\n"
                "- 📱 Serve **Chrome su Android**, con **Bluetooth** e **posizione** attivi (Android lo richiede per cercare i dispositivi). Su iPhone non funziona.\n"
                "- 🚗 Vale per **auto e furgoni** con presa OBD-II/EOBD (benzina dal 2001, diesel dal 2004 in Europa). Camion, trattori e macchine operatrici di solito usano J1939: da qui **non** sono collegabili (puoi scrivere i codici in «Leggi codici errore»).\n"
                "- 🔒 L'app fa **solo lettura**. Non cancella mai i codici.")
    st.markdown("**Come si fa** (da fermo, con il veicolo parcheggiato)")
    st.markdown("1. Inserisci il dongle nella presa OBD-II (di solito sotto il volante). 2. Gira la chiave su «quadro acceso» (motore spento o al minimo). 3. Tocca il tasto viola e scegli il dongle nell'elenco. 4. Aspetta circa un minuto.")
    _dg_inietta()
    st.markdown(_DG_CSS + "<div class='dg-ble' role='button' tabindex='0' data-dg-azione='collega'>🔌 Collega il dongle e leggi i codici</div>"
                "<div data-dg-msg style='display:none;margin:4px 0;font-weight:700;font-size:13.5px'></div>", unsafe_allow_html=True)
    with st.container(key="dg_ricezione"):
        st.text_input("dg-ble-ricezione", key="dg_ble_in", label_visibility="collapsed")
    # ---- risultato ricevuto dal browser
    grezzo = st.session_state.get("dg_ble_in") or ""
    if grezzo:
        try:
            payload = json.loads(grezzo)
        except Exception:
            payload = None
        if isinstance(payload, dict) and payload.get("ts") != (st.session_state.get("dg_ble_ts") or -1):
            st.session_state["dg_ble_ts"] = payload.get("ts")
            st.session_state["dg_ble_ris"] = payload if not payload.get("ok") else dict(dg_analizza(payload), ok=True)
    ris = st.session_state.get("dg_ble_ris")
    if ris is not None:
        _dg_mostra(ris, v)
    # ---- dongle provati
    st.divider()
    prov = dg_dongle_riepilogo(dg_dongle_leggi())
    st.markdown("**🧾 Dongle provati dagli utenti di questa app**")
    if not prov:
        st.caption("Nessuno ancora. Finché un dongle non è stato provato, non lo dichiaro compatibile.")
    for e in prov[:12]:
        st.markdown(f"- {e['nome']}: ✅ {e['ok']} funzionato · ❌ {e['no']} non funzionato")
    st.caption("Nessun dato personale: solo il nome del dongle, l'esito e la data.")


def _dg_mostra(ris, v):
    if not ris.get("ok"):
        err = ris.get("errore", "")
        testo = {"bluetooth_non_supportato": "Questo browser non può usare il Bluetooth dei siti: apri l'app in Chrome su Android.", "annullato": "Hai annullato: nessun dispositivo scelto.",
                 "canali_non_trovati": "Il dispositivo si è collegato ma non ha un canale seriale conosciuto: non è compatibile con questa funzione."}.get(err, f"Non sono riuscito a leggere: {err}")
        st.error(testo)
        if err not in ("annullato", "bluetooth_non_supportato") and ris.get("dispositivo"):
            if st.button(f"❌ Segna che «{ris['dispositivo']}» non ha funzionato", key="dg_no_funz", width="stretch"):
                dg_dongle_segna(ris["dispositivo"], "no")
                st.session_state["messaggio"] = "Grazie: segnato."
                st.rerun()
        return
    st.success(f"✅ Letto da **{ris.get('dispositivo') or 'dispositivo'}**" + (f" · protocollo: {ris['protocollo']}" if ris.get("protocollo") else ""))
    if ris.get("veicolo_non_trovato"):
        st.warning("Il dongle non ha trovato la centralina del veicolo: controlla che il quadro sia acceso e che il dongle sia ben inserito. I valori qui sotto potrebbero essere vuoti.")
    if ris.get("tensione") is not None:
        t = ris["tensione"]
        if "as_valuta_12v" in globals():
            try:
                stato12 = as_valuta_12v(t, t >= 13.0)               # sopra 13 V il motore sta caricando; sotto, motore spento
                st.markdown(f"🔋 **Batteria 12V: {t:.1f} V** — {stato12[1] if isinstance(stato12, (tuple, list)) else stato12}")
            except Exception:
                st.markdown(f"🔋 **Batteria 12V: {t:.1f} V**")
        else:
            st.markdown(f"🔋 **Batteria 12V: {t:.1f} V**" + (" (sotto 12,0 V a motore spento è scarica)" if t < 12.0 else ""))
    if ris.get("mil") is not None:
        st.markdown(f"{'🔴' if ris['mil'] else '🟢'} Spia motore (MIL): **{'accesa' if ris['mil'] else 'spenta'}** · codici dichiarati dalla centralina: **{ris.get('conteggio')}**")
    if ris.get("vin"):
        st.caption(f"VIN letto: {ris['vin']}")
    tutti = []
    for chiave, titolo in (("memorizzati", "Memorizzati (confermati)"), ("in_attesa", "In attesa (visti una volta, da confermare)"), ("permanenti", "Permanenti (non si cancellano da soli)")):
        elenco = ris.get(chiave) or []
        st.markdown(f"**{titolo}: {len(elenco)}**")
        mezzo = bd_scope_desc(bd_scope(v), v) if "bd_scope" in globals() else ""
        for c in elenco:
            tutti.append(c)
            _dtc_carta({"codice": c, "tipo": "obd"}, v, mezzo, "ble" + chiave[:2])
    if not tutti:
        st.info("Nessun codice di errore trovato. Se il veicolo ha una spia accesa, il guasto potrebbe non essere nei codici OBD (per esempio ABS, airbag o cambio non si leggono con il comando generico).")
    st.session_state["dg_ultimi_codici"] = tutti
    c1, c2 = st.columns(2, gap="small")
    if c1.button("✅ Ha funzionato", key="dg_ok_funz", width="stretch"):
        dg_dongle_segna(ris.get("dispositivo"), "ok", ris.get("protocollo", ""))
        st.session_state["messaggio"] = "Grazie: segnato. Aiuti chi usa l'app dopo di te."
        st.rerun()
    if c2.button("❌ Non ha funzionato bene", key="dg_ko_funz", width="stretch"):
        dg_dongle_segna(ris.get("dispositivo"), "no", ris.get("protocollo", ""))
        st.session_state["messaggio"] = "Grazie: segnato."
        st.rerun()
    if v and st.button("💾 Salva questa lettura nello storico del veicolo", key="dg_ble_salva", type="primary", width="stretch"):
        voce = {"id": uuid.uuid4().hex[:8], "data": datetime.now().strftime("%Y-%m-%d %H:%M"), "fonte": f"Dongle Bluetooth ({ris.get('dispositivo') or 'sconosciuto'})", "origine": "Memorizzati, in attesa e permanenti", "km": "",
                "codici": [{"codice": c, "titolo": dtc_riepilogo(dtc_info(c))[1]} for c in tutti], "sintomi": "", "tensione_12v": ris.get("tensione"), "spia_motore": ris.get("mil"),
                "stato": "Aperto", "intervento": "", "note": "", "files": []}
        _au_mod(v["id"], lambda x, vv=voce: x.setdefault("letture", []).append(vv), "Diagnostica: lettura dongle")
        st.session_state["messaggio"] = "✅ Lettura salvata nello storico."
        st.rerun()
