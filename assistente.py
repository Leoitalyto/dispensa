# -*- coding: utf-8 -*-
"""Assistente digitale: un robottino che compare con un tasto rotondo (la sua testa) e aiuta a capire come si usa l'app.
 - PARLA: legge le spiegazioni ad alta voce con la voce del telefono (gratis, nessuna chiave)
 - ASCOLTA: si tocca il microfono, si fa una domanda a voce e risponde con la guida dell'app (Chrome su Android)
 - GIRO GUIDATO: spiega l'app passo per passo; «Novità» dice cosa c'è di nuovo e dove trovarlo
 - SI DISATTIVA: dal pannello («Disattiva assistente») e si riattiva da «Clicca per informazioni».
   La scelta resta salvata sul telefono.
Le risposte vengono dalla guida di info_sezioni.py: non è un'intelligenza artificiale che risponde a qualsiasi cosa.
Viene inserito nella pagina da pulsante_info() di info_sezioni.py. Se manca un'immagine o il browser non ha la voce,
funziona lo stesso (solo testo)."""
import base64
import json
import os

import streamlit as st

_VERSIONE_ASSISTENTE = "1"

# Il giro guidato in italiano (le altre lingue stanno in guida_xx.py, codici tour1..tour8)
_TOUR = [
    ("Benvenuto!", "Ciao, sono il tuo assistente. Ti faccio un giro veloce dell'app. Con i pulsanti Avanti e Indietro vai al tuo ritmo, "
                   "e puoi fermarmi quando vuoi."),
    ("La Dispensa", "Nella Dispensa tieni l'elenco di quello che hai in casa. Tocca Aggiungi, fotografa il prodotto, scrivi il nome e la "
                    "scadenza. I colori ti dicono quando agire: verde tranquillo, arancione entro due mesi, rosso entro un mese."),
    ("Allergeni e ingredienti", "Se scegli le tue allergie nel menu a sinistra, i prodotti pericolosi per te si riconoscono subito e "
                                "compare una sirena. Su ogni scheda il pulsante Ingredienti mostra la composizione."),
    ("Salute", "Con la prima icona entri in Salute: medicinali con scadenza, terapie con promemoria su Telegram o email, "
                    "visite, vaccini e un profilo per ogni persona della famiglia."),
    ("Tessera sanitaria", "In Salute, accanto alla dottoressa, c'è il badge azzurro della tessera sanitaria: mostra fronte e "
                          "retro e ti fa salvare i collegamenti al fascicolo sanitario, alle vaccinazioni e alle spese detraibili."),
    ("I miei documenti", "Con la seconda icona entri in I miei documenti. Fai la foto del documento: l'app toglie lo sfondo, lo "
                         "raddrizza e prova a leggere tipo, numero e scadenza. Puoi sempre correggere i campi. "
                         "Ti avvisa sei e tre mesi prima della scadenza."),
    ("Le Utilità", "Con la terza icona entri nelle Utilità: app utili come Velocity Music e Wimbi. Tocca il pulsante per avviarle e "
                   "il nome per leggere il bugiardino."),
    ("Aiuto sempre a portata di mano", "In alto, in ogni pagina, c'è il pulsante rosso Clicca per informazioni, con la guida e la ricerca. "
                                       "E io sono qui: toccami quando vuoi, anche con il microfono. Se non ti servo, mi disattivi dal pannello, "
                                       "e mi riattivi dal pulsante rosso. Buon lavoro!"),
]

# A quale voce della guida corrisponde ogni pagina / sottopagina: è il testo che l'assistente ha già pronto quando lo apri
_CTX_GUIDA = {
    "dispensa": "d_inizio", "dispensa:aggiungi": "d_aggiungere", "dispensa:gestisci": "d_gestisci", "dispensa:utenti": "d_account",
    "dispensa:spesa": "d_spesa", "dispensa:messaggi": "d_account", "dispensa:info": "d_icone",
    "farmacia": "f_cosa", "farmacia:medicinali": "f_medicinale", "farmacia:terapie": "f_terapie", "farmacia:visite": "f_visite",
    "farmacia:vaccini": "f_vaccini", "farmacia:sanitaria": "f_scheda", "farmacia:dottore": "f_scheda", "farmacia:tessera": "f_tessera",
    "farmacia:medicinale": "f_medicinale", "documenti": "x_cosa", "documenti:nuovo": "x_aggiungere", "utilita": "u_cosa",
}
# L'ordine delle schede in basso (per sapere quale è aperta): Dispensa (con «Utenti» solo per l'amministratore) e Salute
_TAB_CTX = {"dispensa": ["dispensa", "aggiungi", "gestisci", "utenti", "spesa", "messaggi", "info"],
            "farmacia": ["farmacia", "terapie", "visite", "vaccini"]}


def _cartella_as():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return "."


@st.cache_resource(show_spinner=False)
def _as_uri_cache(nome, data_file):
    try:
        with open(os.path.join(_cartella_as(), nome), "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode()
    except OSError:
        return ""


def _as_uri(nome):
    try:
        data = os.path.getmtime(os.path.join(_cartella_as(), nome))
    except OSError:
        data = 0
    return _as_uri_cache(nome, data)


_JS_ASSISTENTE = r"""
(function () {
  var w = window, doc = w.document;
  var CFG = __CONFIG__;
  try {
  if (w.__assistente) { w.__assistente.aggiorna(CFG); return; }
  var D = CFG, SS = w.speechSynthesis, SR = w.SpeechRecognition || w.webkitSpeechRecognition;
  function leggi(k, def) { try { var v = w.localStorage.getItem(k); return v === null ? def : v; } catch (e) { return def; } }
  function scrivi(k, v) { try { w.localStorage.setItem(k, v); } catch (e) {} }
  function T(k) { return (D.ui && D.ui[k]) || ''; }
  var attivo = leggi('asst_attivo', '1') === '1', voceOn = leggi('asst_voce', '1') === '1';
  var ultimoCmd = (D.cmd && D.cmd.id) || '';
  var tourIdx = -1, riconoscimento = null, aperto = false, ctxCorrente = D.ctx;

  /* ---------- aspetto ---------- */
  var st = doc.createElement('style');
  st.textContent =
    '@keyframes asstAnello{0%{box-shadow:0 0 0 0 rgba(25,80,180,.55)}70%{box-shadow:0 0 0 14px rgba(25,80,180,0)}100%{box-shadow:0 0 0 0 rgba(25,80,180,0)}}' +
    '@keyframes asstFluttua{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}' +
    '@keyframes asstParla{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}' +
    '@keyframes asstAscolta{0%{box-shadow:0 0 0 0 rgba(229,72,77,.7)}100%{box-shadow:0 0 0 18px rgba(229,72,77,0)}}' +
    '#asst-btn{position:fixed;right:12px;bottom:108px;width:62px;height:62px;border-radius:50%;border:0;padding:0;background:transparent;' +
      'z-index:99998;cursor:pointer;animation:asstAnello 2.4s infinite;box-shadow:0 6px 14px rgba(0,0,0,.28)}' +
    '#asst-btn img{width:100%;height:100%;display:block;border-radius:50%}#asst-btn:active{transform:scale(.93)}' +
    '#asst-pan{position:fixed;left:8px;right:8px;bottom:8px;max-width:560px;margin:0 auto;z-index:100000;background:#fff;color:#14302b;' +
      'border-radius:26px;border:3px solid #ffd600;box-shadow:0 14px 40px rgba(0,0,0,.4);max-height:84vh;overflow:auto;' +
      'font-family:inherit;padding:12px 12px 10px;display:none}' +
    '#asst-pan *{box-sizing:border-box}' +
    '.asst-top{display:flex;gap:10px;align-items:flex-start}' +
    '.asst-robot{flex:0 0 92px}.asst-robot img{width:92px;height:auto;display:block;animation:asstFluttua 3s ease-in-out infinite}' +
    '.asst-robot.parla img{animation:asstParla .55s ease-in-out infinite;filter:drop-shadow(0 0 10px rgba(255,214,0,.9))}' +
    '.asst-robot.ascolta img{filter:drop-shadow(0 0 10px rgba(229,72,77,.9))}' +
    '.asst-bolla{flex:1;min-width:0;background:#eef6ff;border:2px solid #1950b4;border-radius:18px 18px 18px 4px;padding:9px 12px;' +
      'max-height:34vh;overflow:auto;font-size:14.5px;line-height:1.35}' +
    '#asst-pan[dir=rtl] .asst-bolla{border-radius:18px 18px 4px 18px}' +
    '.asst-titolo{font-weight:900;color:#1950b4;margin-bottom:3px;font-size:15px}.asst-testo b{font-weight:800}' +
    '.asst-x{flex:0 0 auto;width:34px;height:34px;border-radius:50%;border:0;background:#e9eef2;font-size:16px;cursor:pointer;color:#14302b}' +
    '.asst-azioni{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0 6px}' +
    '#asst-pan button.asst-b{border:0;border-radius:14px;padding:11px 8px;font-size:13.5px;font-weight:800;cursor:pointer;color:#fff;' +
      'background:linear-gradient(135deg,#1950b4,#2f80ed)}' +
    '#asst-pan button.asst-b.giallo{background:linear-gradient(135deg,#f5b800,#ffd600);color:#3a2d00}' +
    '#asst-pan button.asst-b.verde{background:linear-gradient(135deg,#0f9d74,#26a69a)}' +
    '#asst-pan button.asst-b.rosso{background:linear-gradient(135deg,#c62828,#ef5350)}' +
    '#asst-pan button.asst-b.grigio{background:#e9eef2;color:#14302b}' +
    '#asst-pan button.asst-b.ascolta{background:#e5484d;animation:asstAscolta 1s infinite}' +
    '.asst-tour{display:none;grid-template-columns:1fr auto 1fr auto;gap:6px;align-items:center;margin:6px 0}.asst-tour span{font-weight:800;font-size:13px}' +
    '.asst-chiedi{display:flex;gap:6px;margin:6px 0}' +
    '.asst-chiedi input{flex:1;min-width:0;border:2px solid #b9c8d8;border-radius:14px;padding:10px 12px;font-size:14.5px;background:#fff;color:#14302b}' +
    '.asst-sugg{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}' +
    '.asst-sugg button{border:2px solid #1950b4;background:#fff;color:#1950b4;border-radius:999px;padding:6px 11px;font-size:12.5px;font-weight:700;cursor:pointer}' +
    '.asst-pie{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.asst-pie button{flex:1 1 auto}' +
    '#asst-toast{position:fixed;left:50%;transform:translateX(-50%);bottom:120px;max-width:90vw;background:#14302b;color:#fff;padding:10px 16px;' +
      'border-radius:16px;font-size:13.5px;z-index:100001;display:none;text-align:center}';
  doc.head.appendChild(st);

  var btn = doc.createElement('button'); btn.id = 'asst-btn';
  btn.innerHTML = D.img.testa ? '<img alt="" src="' + D.img.testa + '">' : '<span style="font-size:34px">🤖</span>';
  var pan = doc.createElement('div'); pan.id = 'asst-pan'; pan.setAttribute('role', 'dialog');
  pan.innerHTML =
    '<div class="asst-top"><div class="asst-robot">' + (D.img.intero ? '<img alt="" src="' + D.img.intero + '">' : '<span style="font-size:60px">🤖</span>') + '</div>' +
    '<div class="asst-bolla"><div class="asst-titolo"></div><div class="asst-testo"></div></div>' +
    '<button class="asst-x" aria-label="X">✕</button></div>' +
    '<div class="asst-azioni">' +
      '<button class="asst-b" data-az="pagina" data-ui="a_rileggi"></button>' +
      '<button class="asst-b giallo" data-az="giro" data-ui="a_giro"></button>' +
      '<button class="asst-b verde" data-az="novita" data-ui="a_novita"></button>' +
      '<button class="asst-b rosso" data-az="mic" data-ui="a_mic"></button></div>' +
    '<div class="asst-tour"><button class="asst-b grigio" data-az="indietro" data-ui="a_indietro"></button><span></span>' +
      '<button class="asst-b" data-az="avanti" data-ui="a_avanti"></button><button class="asst-b grigio" data-az="fine" data-ui="a_fine"></button></div>' +
    '<div class="asst-chiedi"><input type="text"><button class="asst-b" data-az="chiedi" data-ui="a_chiedi"></button></div>' +
    '<div class="asst-sugg"></div>' +
    '<div class="asst-pie"><button class="asst-b grigio" data-az="voce"></button>' +
      '<button class="asst-b grigio" data-az="silenzio" data-ui="a_silenzio"></button>' +
      '<button class="asst-b grigio" data-az="off" data-ui="a_off"></button></div>';
  var toast = doc.createElement('div'); toast.id = 'asst-toast';
  doc.body.appendChild(btn); doc.body.appendChild(pan); doc.body.appendChild(toast);
  function $(s) { return pan.querySelector(s); }
  var elTitolo = $('.asst-titolo'), elTesto = $('.asst-testo'), elRobot = $('.asst-robot'), elTour = $('.asst-tour'),
      elSugg = $('.asst-sugg'), elInput = $('.asst-chiedi input'), btnMic = pan.querySelector('[data-az="mic"]'), btnVoce = pan.querySelector('[data-az="voce"]');
  if (!SR) btnMic.style.display = 'none';
  if (!SS) { btnVoce.style.display = 'none'; pan.querySelector('[data-az="silenzio"]').style.display = 'none'; }
  function aggiornaVoceBtn() { btnVoce.textContent = voceOn ? T('a_voce_on') : T('a_voce_off'); }
  function applicaUI() {
    [].forEach.call(pan.querySelectorAll('[data-ui]'), function (b) { b.textContent = T(b.getAttribute('data-ui')); });
    elInput.placeholder = T('a_ph'); btn.setAttribute('aria-label', T('a_aria')); pan.setAttribute('aria-label', T('a_aria'));
    pan.setAttribute('dir', D.rtl ? 'rtl' : 'ltr'); toast.setAttribute('dir', D.rtl ? 'rtl' : 'ltr'); aggiornaVoceBtn();
  }

  /* ---------- testi e voce ---------- */
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function mdHtml(s) {
    return esc(s).replace(/^#{1,6}\s*/gm, '').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`([^`]*)`/g, '$1')
      .replace(/^\s*[-•]\s+/gm, '• ').replace(/\n/g, '<br>');
  }
  var RX_EMOJI = /[\u{1F000}-\u{1FAFF}\u{2190}-\u{21FF}\u{2300}-\u{23FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}]/gu;
  function perVoce(s) {
    return String(s).replace(/\*\*/g, '').replace(/`/g, '').replace(/^#{1,6}\s*/gm, '').replace(RX_EMOJI, '')
      .replace(/https?:\/\/\S+/g, '').replace(/[«»]/g, '').replace(/^\s*[-•]\s+/gm, '').replace(/\n+/g, '. ').replace(/\s+/g, ' ').replace(/\.\s*\./g, '.').trim();
  }
  function scegliVoce() {
    var pre = (D.lang || 'it-IT').slice(0, 2).toLowerCase(), rx = new RegExp('^' + pre, 'i');
    var vs = (SS && SS.getVoices && SS.getVoices()) || [], ok = vs.filter(function (v) { return rx.test(v.lang); });
    return ok.filter(function (v) { return /google|natural|neural|premium/i.test(v.name); })[0] || ok[0] || null;
  }
  function spezza(testo) {
    var frasi = testo.split(/(?<=[.!?;:،؛؟])\s+/), out = [], cur = '';
    frasi.forEach(function (f) {
      if ((cur + ' ' + f).length > 190 && cur) { out.push(cur); cur = f; } else { cur = cur ? cur + ' ' + f : f; }
    });
    if (cur) out.push(cur);
    return out;
  }
  function ferma() { try { if (SS) SS.cancel(); } catch (e) {} elRobot.classList.remove('parla'); }
  function parla(testo, alFine) {
    ferma();
    if (!SS || !voceOn) { if (alFine) w.setTimeout(alFine, 0); return; }
    var pezzi = spezza(perVoce(testo)), i = 0, voce = scegliVoce();
    if (!pezzi.length) return;
    function dici() {
      if (i >= pezzi.length) { elRobot.classList.remove('parla'); if (alFine) alFine(); return; }
      var u = new w.SpeechSynthesisUtterance(pezzi[i++]); u.lang = D.lang || 'it-IT'; u.rate = 1; u.pitch = 1.05;
      if (voce) u.voice = voce;
      u.onend = dici; u.onerror = function () { elRobot.classList.remove('parla'); };
      elRobot.classList.add('parla'); SS.speak(u);
    }
    dici();
  }
  function mostra(titolo, testo, voceTesto, parlare, alFine) {
    elTitolo.textContent = titolo || ''; elTesto.innerHTML = mdHtml(testo); $('.asst-bolla').scrollTop = 0;
    if (parlare === false) return;
    parla((titolo ? titolo + (/[.!?:؟]$/.test(titolo) ? ' ' : '. ') : '') + (voceTesto || testo), alFine);
  }
  function avviso(m) { toast.textContent = m; toast.style.display = 'block'; w.setTimeout(function () { toast.style.display = 'none'; }, 5200); }

  /* ---------- ricerca nella guida (nella lingua scelta) ---------- */
  function norm(s) { return String(s).toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/[^\p{L}\p{N}]+/gu, ' '); }
  function stem(p) { return p.length > 4 ? p.replace(/[aeiou]+$/, '') : p; }
  var stopSet = null;
  function parole(s) {
    if (!stopSet) { stopSet = {}; (D.stop || []).forEach(function (x) { stopSet[norm(x).trim()] = 1; }); }
    var min = /^ar/i.test(D.lang || '') ? 2 : 3, o = {};
    var ar = /^ar/i.test(D.lang || '');
    norm(s).split(' ').forEach(function (p) { if (p.length >= min && !stopSet[p]) o[stem(ar && p.length > 4 ? p.replace(/^(وال|بال|كال|لل|ال)/, '') : p)] = 1; });
    return Object.keys(o);
  }
  function combacia(q, ins) { for (var i = 0; i < ins.length; i++) { var x = ins[i]; if (x.indexOf(q) === 0 || (x.length >= 4 && q.indexOf(x) === 0)) return true; } return false; }
  var indice = null;
  function costruisci() { indice = D.guida.map(function (g) { return {g: g, t: parole(g.t), k: parole(g.k), b: parole(g.b)}; }); }
  /* ---------- capire COSA si vuole fare (azione) e SU COSA (oggetto), e ricordare l'argomento della conversazione ---------- */
  var memoria = {az: null, og: null};
  function rileva(testo) {
    var n = ' ' + norm(testo).trim() + ' ', I = D.intenti || {az: {}, og: {}}, r = {az: null, og: null};
    ['az', 'og'].forEach(function (tipo) {
      var best = 1e9;
      Object.keys(I[tipo] || {}).forEach(function (k) {
        I[tipo][k].forEach(function (p) {
          var esatta = p.charAt(0) === '=', q = norm(esatta ? p.slice(1) : p).trim(), pos = q ? n.indexOf(' ' + q + (esatta ? ' ' : '')) : -1;   /* «=parola»: parola intera */
          if (pos >= 0 && pos < best) { best = pos; r[tipo] = k; }
        });
      });
    });
    var rec = (I.az && I.az.recupera) || [];                          /* «per sbaglio», «recuperare»…: vince su tutto (non vuole eliminare, vuole riavere) */
    if (rec.some(function (p) { var esatta = p.charAt(0) === '=', q = norm(esatta ? p.slice(1) : p).trim(); return q && n.indexOf(' ' + q + (esatta ? ' ' : '')) >= 0; })) r.az = 'recupera';
    return r;
  }
  function cerca(domanda, intento) {
    if (!indice) costruisci();
    var q = parole(domanda); if (!q.length) return [];
    var az = intento && intento.az, og = intento && intento.og, ris = [], esatte = 0;
    indice.forEach(function (e) {
      var pt = 0, tr = 0, bonus = 0, ex = false;
      q.forEach(function (x) {
        if (combacia(x, e.t)) { pt += 3; tr++; } else if (combacia(x, e.k)) { pt += 2; tr++; } else if (combacia(x, e.b)) { pt += 1; tr++; }
      });
      var a = e.g.a, o = e.g.o;
      if (az && a) bonus += (a === az) ? 6 : -8;                    /* l'azione giusta (es. eliminare) conta più delle parole */
      if (og && o) bonus += (o === og) ? 6 : -4;
      if (az && og && a === az && o === og) { bonus += 12; ex = true; }
      if (ex) esatte++;
      if (pt + bonus > 0) ris.push({p: pt + tr + bonus + (e.g.s === D.sezione ? 1 : 0), g: e.g, ex: ex});
    });
    ris.sort(function (a, b) { return b.p - a.p; });
    if (!ris.length) return [];
    if (esatte) return [ris[0].g];                                  /* azione e oggetto coincidono: una risposta sola, quella giusta */
    var top = ris[0].p; return ris.filter(function (r) { return r.p * 2 >= top; }).slice(0, 4).map(function (r) { return r.g; });
  }
  function argomento(g, parlare, prefisso) {
    elTour.style.display = 'none'; tourIdx = -1;
    var testo = (prefisso || '') + g.b;
    var corto = perVoce(testo); if (corto.length > 900) corto = corto.slice(0, 900).replace(/[^.!?؟]*$/, '') || corto.slice(0, 900);
    mostra(g.t, testo, corto, parlare);
  }
  function chipsTesto(lista) {                                       /* pulsanti con una frase già pronta da inviare come domanda */
    elSugg.innerHTML = '';
    lista.forEach(function (x) {
      var b = doc.createElement('button'); b.textContent = x[0]; b.addEventListener('click', function () { elInput.value = x[1]; chiedi(x[1]); }); elSugg.appendChild(b);
    });
  }
  function chips(lista) {
    elSugg.innerHTML = '';
    lista.forEach(function (g) {
      var b = doc.createElement('button'); b.textContent = g.t; b.addEventListener('click', function () { argomento(g); chips([]); }); elSugg.appendChild(b);
    });
  }
  function voceGuida(id) { for (var i = 0; i < D.guida.length; i++) if (D.guida[i].id === id) return D.guida[i]; return null; }
  function argomentiSezione(escludi) { return D.guida.filter(function (g) { return g.s === D.sezione && g.id !== escludi; }).slice(0, 8); }

  /* ---------- la pagina in cui sei: il testo è già pronto ---------- */
  function ctxAttuale() {
    var base = D.ctx || D.sezione; if (base.indexOf(':') >= 0) return base;
    var lista = D.tabs && D.tabs[D.sezione]; if (!lista) return base;
    var attesi = D.sezione === 'dispensa' ? [6, 7] : [lista.length];
    var liste = doc.querySelectorAll('[data-baseweb="tab-list"]');
    for (var k = 0; k < liste.length; k++) {
      var tabs = liste[k].querySelectorAll('[role="tab"]'), n = tabs.length;
      if (attesi.indexOf(n) < 0) continue;
      var idx = -1; for (var i = 0; i < n; i++) if (tabs[i].getAttribute('aria-selected') === 'true') idx = i;
      if (idx <= 0) return base;
      var nomi = lista.slice(); if (D.sezione === 'dispensa' && n === 6) nomi.splice(3, 1);
      return nomi[idx] ? D.sezione + ':' + nomi[idx] : base;
    }
    return base;
  }
  function guidaCtx() {
    var c = ctxAttuale(), id = D.ctxmap[c] || D.ctxmap[D.sezione] || D.ctxmap.dispensa;
    return voceGuida(id);
  }
  function paginaCorrente(parlare) {
    var g = guidaCtx(); if (!g) return;
    elTour.style.display = 'none'; tourIdx = -1;
    var corto = perVoce(g.b); if (corto.length > 900) corto = corto.slice(0, 900).replace(/[^.!?؟]*$/, '') || corto.slice(0, 900);
    mostra(g.t, g.b + '\n\n' + T('a_vedi'), corto, parlare);
    chips(argomentiSezione(g.id));
  }
  function novita() {
    elTour.style.display = 'none'; tourIdx = -1; chips([]);
    if (!D.novita.length) { mostra(T('a_nov_none_t'), T('a_nov_none_x')); return; }
    var testo = D.novita.map(function (n) { return '**' + n.i + ' ' + n.t + '**\n📍 ' + n.d; }).join('\n\n');
    var voceT = T('a_nov_voce') + ' ' + D.novita.map(function (n) { return n.t + '. ' + T('a_nov_trovi') + ' ' + n.d + '.'; }).join(' ');
    mostra(T('a_nov_t'), testo, voceT);
  }
  function tourVai(i) {
    tourIdx = Math.max(0, Math.min(D.tour.length - 1, i)); chips([]);
    elTour.style.display = 'grid'; elTour.querySelector('span').textContent = (tourIdx + 1) + ' / ' + D.tour.length;
    var s = D.tour[tourIdx]; mostra(s[0], s[1]);
  }
  function tourFine() { elTour.style.display = 'none'; tourIdx = -1; ferma(); mostra(T('a_fine_t'), T('a_fine_x')); chips(argomentiSezione()); }
  function ascolta() {
    if (!SR) { mostra(T('a_mic_t'), T('a_mic_no')); return; }
    if (riconoscimento) { try { riconoscimento.stop(); } catch (e) {} return; }
    ferma();
    var r = new SR(); riconoscimento = r; r.lang = D.lang || 'it-IT'; r.interimResults = false; r.maxAlternatives = 1;
    btnMic.classList.add('ascolta'); elRobot.classList.add('ascolta'); btnMic.textContent = T('a_ascolto_btn');
    mostra(T('a_ascolto_t'), T('a_ascolto_x'), ' ', false);
    var detto = false;
    function fine() { riconoscimento = null; btnMic.classList.remove('ascolta'); elRobot.classList.remove('ascolta'); btnMic.textContent = T('a_mic'); }
    r.onresult = function (e) { detto = true; var t = e.results[0][0].transcript; fine(); elInput.value = t; chiedi(t); };
    r.onerror = function (e) {
      fine(); detto = true;
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') mostra(T('a_mic_t'), T('a_mic_perm'), ' ', false);
      else if (e.error === 'no-speech') mostra(T('a_nulla_t'), T('a_nulla_x'), ' ', false);
      else mostra(T('a_mic_t'), T('a_mic_err'), ' ', false);
    };
    r.onend = function () { if (!detto) { fine(); mostra(T('a_nulla_t'), T('a_nulla_x'), ' ', false); } else { fine(); } };
    try { r.start(); } catch (e) { fine(); }
  }
  function haParola(n, lista) { return String(lista || '').split(' ').some(function (x) { x = norm(x).trim(); return x && n.indexOf(x) >= 0; }); }
  /* ---------- assistente con intelligenza artificiale (facoltativo): se c'è, la domanda va al modello; se non risponde, vale la guida ---------- */
  var storia = [], inAttesa = null;
  function ricorda(q, r) { storia.push({r: 'u', t: q}, {r: 'a', t: String(r || '').slice(0, 700)}); if (storia.length > 12) storia = storia.slice(-12); }
  function mandaAlModello(inp, valore) {
    var setter = Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, valore);
    inp.dispatchEvent(new w.Event('input', {bubbles: true}));
    inp.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
    inp.dispatchEvent(new w.FocusEvent('focusout', {bubbles: true}));
  }
  function chiedi(testo) {
    testo = (testo || '').trim();
    var A = D.ai, n0 = ' ' + norm(testo) + ' ';
    var speciale = !testo || (haParola(n0, T('i_off')) && haParola(n0, T('i_ass'))) || haParola(n0, T('i_silenzio')) || haParola(n0, T('i_novita')) || haParola(n0, T('i_giro')) ||
      (n0.trim().split(' ').length <= 3 && haParola(n0, T('i_saluto')));
    var inp = A && A.attivo && /^it/i.test(D.lang || 'it') && !speciale ? doc.querySelector('input[aria-label="asst-llm-q"]') : null;
    if (!inp) { chiediLocale(testo); ricorda(testo, elTitolo.textContent + '. ' + elTesto.textContent); return; }
    var it = rileva(testo); if (it.az) memoria.az = it.az; if (it.og) memoria.og = it.og;      /* la guida ricorda l'argomento anche se risponde il modello */
    var id = String(Date.now()) + String(Math.floor(Math.random() * 1000));
    if (inAttesa) w.clearTimeout(inAttesa.t);
    inAttesa = {id: id, testo: testo, t: w.setTimeout(function () {                 /* il modello non risponde: vale la guida */
      if (inAttesa && inAttesa.id === id) { var q = inAttesa.testo; inAttesa = null; chiediLocale(q); ricorda(q, elTitolo.textContent + '. ' + elTesto.textContent); }
    }, A.timeout || 35000)};
    mostra('💭 ' + (A.pensando || ''), A.attendi || '', ' ', false);
    chips([]);
    mandaAlModello(inp, JSON.stringify({id: id, q: testo.slice(0, 500), h: storia.slice(-6)}));
  }
  function rispostaModello(r) {
    if (!inAttesa || !r || r.id !== inAttesa.id) return;
    w.clearTimeout(inAttesa.t);
    var q = inAttesa.testo; inAttesa = null;
    if (r.ok && r.testo) {
      mostra('💬 ' + ((D.ai && D.ai.titolo) || ''), r.testo, perVoce(r.testo).slice(0, 700));
      ricorda(q, r.testo);
      chips(argomentiSezione());
    } else { chiediLocale(q); ricorda(q, elTitolo.textContent + '. ' + elTesto.textContent); }
  }
  function chiediLocale(testo) {
    testo = (testo || '').trim(); if (!testo) { mostra(T('a_dimmi_t'), T('a_dimmi_x'), ' ', false); return; }
    var n = norm(testo);
    if (haParola(n, T('i_off')) && haParola(n, T('i_ass'))) { mostra(T('a_off_t'), T('a_off_x')); chips([]); return; }
    if (haParola(n, T('i_silenzio'))) { ferma(); return; }
    if (haParola(n, T('i_novita'))) { novita(); return; }
    if (haParola(n, T('i_giro'))) { tourVai(0); return; }
    if (n.trim().split(' ').length <= 3 && haParola(n, T('i_saluto'))) { paginaCorrente(true); return; }
    var it = rileva(testo), italiano = /^it/i.test(D.lang || 'it');
    var og = it.og || ((it.az && memoria.og) ? memoria.og : null), az = it.az;     /* «e come lo modifico?»: l'argomento è quello di prima */
    var verbi = {elimina: 'eliminare', aggiungi: 'aggiungere', modifica: 'modificare', vedi: 'vedere', condividi: 'inviare', esporta: 'esportare', recupera: 'recuperare'};
    var nomi = {medicinale: 'un medicinale', terapia: 'una terapia', prescrizione: 'una prescrizione', visita: 'una visita o un esame',
                vaccino: 'una vaccinazione', documento: 'un documento', profilo: 'una persona', foto: 'una foto', bugiardino: 'il bugiardino'};
    if (italiano && az && !og && !/(foglio|sbaglio|whatsapp|email|mail|telegram|sms|pdf|excel)/.test(n)) {          /* so cosa vuole fare, non su cosa: chiedo */
      mostra('Su cosa?', 'Certo, ti aiuto a ' + (verbi[az] || 'farlo') + '. Dimmi **su cosa**: scegli qui sotto.');
      chipsTesto(['medicinale', 'terapia', 'prescrizione', 'visita', 'vaccino', 'documento'].map(function (o) { return [nomi[o].replace(/^(un|una|il) /, ''), (verbi[az] || '') + ' ' + o]; }));
      memoria.az = az; return;
    }
    if (italiano && og && !az && n.trim().split(' ').length <= 3 && nomi[og]) {                                      /* so l'argomento, non l'azione: chiedo */
      mostra('Cosa vuoi fare?', 'Vuoi **aggiungere**, **modificare**, **eliminare** o **inviare** ' + nomi[og] + '? Scegli qui sotto, oppure scrivimelo.');
      chipsTesto([['Aggiungere', 'aggiungere ' + og], ['Modificare', 'modificare ' + og], ['Eliminare', 'eliminare ' + og], ['Inviare', 'inviare ' + og]]);
      memoria.og = og; return;
    }
    var ris = cerca(testo, italiano ? {az: az, og: og} : null);
    if (!ris.length) { mostra(T('a_trov_t'), T('a_trov_x')); chips(argomentiSezione()); return; }
    var guaio = italiano && /(non riesco|non funziona|errore|problema|aiuto|non trovo|non capisco|sbagli)/.test(n);
    var prefisso = guaio ? 'Mi dispiace per il disagio, vediamo subito insieme.\n\n' : '';
    if (az) memoria.az = az;
    if (og) memoria.og = og;
    argomento(ris[0], undefined, prefisso); chips(ris.slice(1));
  }
  function apri() {
    if (!attivo) return; aperto = true; pan.style.display = 'block'; btn.style.display = 'none';
    ctxCorrente = ctxAttuale(); paginaCorrente(true);          /* subito la spiegazione della pagina in cui sei */
  }
  function chiudi() { aperto = false; pan.style.display = 'none'; ferma(); if (riconoscimento) { try { riconoscimento.abort(); } catch (e) {} } if (attivo) btn.style.display = 'block'; }
  function imposta(on) {
    attivo = on; scrivi('asst_attivo', on ? '1' : '0');
    if (!on) { chiudi(); btn.style.display = 'none'; avviso(T('a_toast_off')); }
    else { btn.style.display = aperto ? 'none' : 'block'; avviso(T('a_toast_on')); }
  }
  function controllaCtx() {
    var c = ctxAttuale(); if (c === ctxCorrente) return; ctxCorrente = c;
    if (aperto && tourIdx < 0) paginaCorrente(false);          /* se il pannello è aperto, aggiorna il testo (senza parlare) */
  }

  btn.addEventListener('click', apri);
  pan.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('button') : null; if (!b) return;
    if (b.classList.contains('asst-x')) { chiudi(); return; }
    var az = b.getAttribute('data-az'); if (!az) return;
    if (az === 'pagina') paginaCorrente(true); else if (az === 'giro') tourVai(0); else if (az === 'novita') novita(); else if (az === 'mic') ascolta();
    else if (az === 'avanti') { if (tourIdx >= D.tour.length - 1) tourFine(); else tourVai(tourIdx + 1); }
    else if (az === 'indietro') tourVai(tourIdx - 1); else if (az === 'fine') tourFine();
    else if (az === 'chiedi') chiedi(elInput.value);
    else if (az === 'voce') { voceOn = !voceOn; scrivi('asst_voce', voceOn ? '1' : '0'); if (!voceOn) ferma(); aggiornaVoceBtn(); }
    else if (az === 'silenzio') ferma(); else if (az === 'off') imposta(false);
  });
  elInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); chiedi(elInput.value); } });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && aperto) chiudi(); });
  doc.addEventListener('click', function (e) { if (e.target && e.target.closest && e.target.closest('[role="tab"]')) w.setTimeout(controllaCtx, 350); }, true);
  try {
    var attesa = null;
    new w.MutationObserver(function () { if (attesa) return; attesa = w.setTimeout(function () { attesa = null; controllaCtx(); }, 400); })
      .observe(doc.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['aria-selected']});
  } catch (e) {}
  applicaUI();
  btn.style.display = attivo ? 'block' : 'none';

  w.__assistente = {
    versione: D.versione,
    aggiorna: function (c) {
      var cambiaUI = false;
      ['ui', 'tour', 'lang', 'rtl', 'ctxmap', 'tabs', 'img'].forEach(function (k) { if (c[k] !== undefined) { D[k] = c[k]; cambiaUI = true; } });
      if (c.stop) { D.stop = c.stop; stopSet = null; indice = null; }
      if (c.guida) { D.guida = c.guida; indice = null; }
      if (c.novita) D.novita = c.novita;
      if (c.ai !== undefined) D.ai = c.ai;
      if (c.sezione) D.sezione = c.sezione;
      if (c.ctx) D.ctx = c.ctx;
      if (cambiaUI) applicaUI();
      if (c.cmd && c.cmd.id && c.cmd.id !== ultimoCmd) { ultimoCmd = c.cmd.id; if (c.cmd.az === 'on') imposta(true); else if (c.cmd.az === 'off') imposta(false); }
      ctxCorrente = ctxAttuale();
      if (aperto && tourIdx < 0) paginaCorrente(false);
    },
    llm: rispostaModello,
    apri: apri, chiudi: chiudi
  };
  } catch (err) { /* se qualcosa non va, l'app funziona come prima, senza assistente */ }
})();
"""


def _inietta(codice):
    """Inserisce lo script nella pagina principale (stesso metodo di voce.py e fotocamera.py)."""
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(codice) + ";P.document.head.appendChild(s);})();</script>")
    try:
        st.html(pagina, unsafe_allow_javascript=True)
    except Exception:
        pass
    try:
        if hasattr(st, "iframe"):
            st.iframe(pagina, height=1)
        else:
            import streamlit.components.v1 as _comp_asst
            _comp_asst.html(pagina, height=0)
    except Exception:
        pass


def _novita_recenti():
    """Le novità degli ultimi 14 giorni, nella lingua scelta (i codici nov1, nov2… seguono l'ordine di _NOVITA)."""
    try:
        from datetime import date as _d
        oggi_ = oggi() if "oggi" in globals() else _d.today()
        tr = GUIDA_TR.get(_lingua_guida(), {}) if _lingua_guida() != "it" else {}
        out = []
        for k, n in enumerate(_NOVITA, start=1):
            if (oggi_ - _d.fromisoformat(n[0])).days <= 14:
                x = tr.get(f"nov{k}")
                out.append({"i": n[1], "t": x[0] if x else n[2], "d": x[1] if x else n[3]})
        return out[:6]
    except Exception:
        return []


def _config_assistente(contesto, completo, cmd):
    sezione = contesto.split(":")[0]
    cfg = {"ctx": contesto, "sezione": sezione, "novita": _novita_recenti()}
    if "ai_config" in globals() and _lingua_guida() == "it":
        cfg["ai"] = ai_config()                            # l'intelligenza artificiale è facoltativa, solo in italiano
    if cmd:
        cfg["cmd"] = {"id": str(__import__("time").time()), "az": cmd}
    if completo:
        lg = _lingua_guida()
        tr = GUIDA_TR.get(lg, {}) if lg != "it" else {}
        cfg["versione"] = _VERSIONE_ASSISTENTE
        cfg["lang"] = LINGUE_BCP47.get(lg, "it-IT")
        cfg["rtl"] = lg == "ar" or ("LINGUE_DA_DESTRA" in globals() and lg in LINGUE_DA_DESTRA)
        cfg["stop"] = list(_STOP_LANG.get(lg, _STOP_LANG["it"]))
        cfg["ui"] = {k: _u(k) for k in UI_IT if k.startswith(("a_", "i_"))}
        cfg["guida"] = [{"id": v["id"], "s": v["sez"], "t": v["titolo"], "b": v["corpo"], "k": v["chiavi"],
                         "a": (_META_GUIDA.get(v["id"]) or (None, None))[0], "o": (_META_GUIDA.get(v["id"]) or (None, None))[1]} for v in tutte_voci()]
        cfg["intenti"] = _INTENTI
        cfg["ctxmap"] = dict(_CTX_GUIDA)
        cfg["tabs"] = {k: list(v) for k, v in _TAB_CTX.items()}
        tour = []
        for k, (t_it, x_it) in enumerate(_TOUR, start=1):
            x = tr.get(f"tour{k}")
            tour.append([x[0], x[1]] if x else [t_it, x_it])
        cfg["tour"] = tour
        cfg["img"] = {"intero": _as_uri("assistente.webp"), "testa": _as_uri("assistente_testa.webp")}
    return cfg


@st.fragment
def _ai_frammento(contesto):
    """Il campo nascosto da cui il browser manda la domanda al modello. Sta in un «frammento»: la risposta non ricarica la pagina e non chiude le finestre aperte."""
    st.markdown("<style>[class*='st-key-nascosti_asst_ai']{display:none !important}</style>", unsafe_allow_html=True)
    with st.container(key="nascosti_asst_ai"):
        valore = st.text_input("asst-llm-q", key="_asst_llm_q", label_visibility="collapsed")
    if valore and valore != st.session_state.get("_ai_visto"):
        st.session_state["_ai_visto"] = valore
        ris = ai_gestisci(valore, contesto) if "ai_gestisci" in globals() else None
        if ris:
            _inietta("(function(){var a=window.__assistente;if(a&&a.llm)a.llm(" + json.dumps(ris, ensure_ascii=False) + ");})();")


def assistente(contesto):
    """Mostra (o aggiorna) il robottino assistente e gli dice in quale pagina ci si trova (es. «farmacia», «farmacia:tessera»).
    Lo script completo parte la prima volta (e quando cambia la lingua); poi si manda solo la pagina e gli eventuali comandi."""
    if "nav_pulisci_interfaccia" in globals():
        nav_pulisci_interfaccia()                          # nasconde la linguetta «Manage app» che copre i pulsanti in basso
    if "ai_attivo" in globals() and ai_attivo():
        _ai_frammento(contesto)
    cmd = st.session_state.pop("_asst_cmd", None)
    lg = _lingua_guida()
    completo = (not st.session_state.get("_asst_inviato")) or st.session_state.get("_asst_lang") != lg
    if not completo and st.session_state.get("_asst_ctx") == contesto and not cmd:
        return
    st.session_state["_asst_inviato"] = True
    st.session_state["_asst_lang"] = lg
    st.session_state["_asst_ctx"] = contesto
    cfg = _config_assistente(contesto, completo, cmd)
    if completo:
        codice = _JS_ASSISTENTE.replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False))
    else:
        codice = ("(function(){var a=window.__assistente;if(a)a.aggiorna(" + json.dumps(cfg, ensure_ascii=False) + ");})();")
    _inietta(codice)
