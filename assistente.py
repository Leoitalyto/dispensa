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

# Cosa dice l'assistente quando si tocca «Spiegami questa pagina»
_PAGINE = {
    "dispensa": ("Sei nella Dispensa",
                 "Qui vedi tutti i prodotti che hai in casa, con il colore della scadenza: verde se manca più di due mesi, "
                 "arancione entro due mesi, rosso entro un mese e scuro se è già scaduto. Per aggiungere un prodotto tocca "
                 "Aggiungi, nella barra in basso. Le tre icone che pulsano ti portano in Farmacia, in I miei documenti e nelle Utilità. "
                 "Chiedimi pure quello che vuoi sapere."),
    "farmacia": ("Sei nella Farmacia",
                 "Qui trovi i medicinali con le scadenze, le terapie e il calendario, le visite, i vaccini, la scheda sanitaria e la "
                 "scheda del dottore. In alto ci sono tre badge: il gruppo sanguigno, la dottoressa e la tessera sanitaria, con i "
                 "collegamenti al fascicolo sanitario, alle vaccinazioni e alle spese detraibili."),
    "documenti": ("Sei in I miei documenti",
                  "Qui tieni carta d'identità, patente, tessera sanitaria e gli altri documenti. Tocca Aggiungi un documento, "
                  "fai la foto del fronte e del retro, e l'app prova a leggere tipo, numero e scadenza. Ti avvisa sei mesi e "
                  "tre mesi prima della scadenza, così non ti dimentichi i rinnovi."),
    "utilita": ("Sei nelle Utilità",
                "Qui trovi app e siti utili. Tocca il grande pulsante di un'app per avviarla, e tocca il suo nome per leggere il "
                "bugiardino, cioè una spiegazione di cosa fa."),
}

# Il giro guidato: (titolo, testo)
_TOUR = [
    ("Benvenuto!", "Ciao, sono il tuo assistente. Ti faccio un giro veloce dell'app. Con i pulsanti Avanti e Indietro vai al tuo ritmo, "
                   "e puoi fermarmi quando vuoi."),
    ("La Dispensa", "Nella Dispensa tieni l'elenco di quello che hai in casa. Tocca Aggiungi, fotografa il prodotto, scrivi il nome e la "
                    "scadenza. I colori ti dicono quando agire: verde tranquillo, arancione entro due mesi, rosso entro un mese."),
    ("Allergeni e ingredienti", "Se scegli le tue allergie nel menu a sinistra, i prodotti pericolosi per te si riconoscono subito e "
                                "compare una sirena. Su ogni scheda il pulsante Ingredienti mostra la composizione."),
    ("La Farmacia", "Con la prima icona entri nella Farmacia: medicinali con scadenza, terapie con promemoria su Telegram o email, "
                    "visite, vaccini e un profilo per ogni persona della famiglia."),
    ("Tessera sanitaria", "Nella Farmacia, accanto alla dottoressa, c'è il badge azzurro della tessera sanitaria: mostra fronte e "
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
  var attivo = leggi('asst_attivo', '1') === '1', voceOn = leggi('asst_voce', '1') === '1';
  var ultimoCmd = (D.cmd && D.cmd.id) || '';
  var corrente = null, tourIdx = -1, tourAttivo = false, riconoscimento = null, aperto = false;

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

  var btn = doc.createElement('button'); btn.id = 'asst-btn'; btn.setAttribute('aria-label', 'Assistente digitale');
  btn.innerHTML = D.img.testa ? '<img alt="" src="' + D.img.testa + '">' : '<span style="font-size:34px">🤖</span>';
  var pan = doc.createElement('div'); pan.id = 'asst-pan'; pan.setAttribute('role', 'dialog'); pan.setAttribute('aria-label', 'Assistente digitale');
  pan.innerHTML =
    '<div class="asst-top"><div class="asst-robot">' + (D.img.intero ? '<img alt="" src="' + D.img.intero + '">' : '<span style="font-size:60px">🤖</span>') + '</div>' +
    '<div class="asst-bolla"><div class="asst-titolo"></div><div class="asst-testo"></div></div>' +
    '<button class="asst-x" aria-label="Chiudi">✕</button></div>' +
    '<div class="asst-azioni">' +
      '<button class="asst-b" data-az="pagina">📖 Spiegami questa pagina</button>' +
      '<button class="asst-b giallo" data-az="giro">🧭 Giro guidato dell\'app</button>' +
      '<button class="asst-b verde" data-az="novita">🆕 Cosa c\'è di nuovo</button>' +
      '<button class="asst-b rosso" data-az="mic">🎤 Fai una domanda</button></div>' +
    '<div class="asst-tour"><button class="asst-b grigio" data-az="indietro">◀ Indietro</button><span></span>' +
      '<button class="asst-b" data-az="avanti">Avanti ▶</button><button class="asst-b grigio" data-az="fine">Fine</button></div>' +
    '<div class="asst-chiedi"><input type="text" placeholder="Scrivi qui la tua domanda…" aria-label="Domanda">' +
      '<button class="asst-b" data-az="chiedi">Chiedi</button></div>' +
    '<div class="asst-sugg"></div>' +
    '<div class="asst-pie"><button class="asst-b grigio" data-az="voce"></button>' +
      '<button class="asst-b grigio" data-az="silenzio">⏹ Silenzio</button>' +
      '<button class="asst-b grigio" data-az="off">⛔ Disattiva assistente</button></div>';
  var toast = doc.createElement('div'); toast.id = 'asst-toast';
  doc.body.appendChild(btn); doc.body.appendChild(pan); doc.body.appendChild(toast);
  function $(s) { return pan.querySelector(s); }
  var elTitolo = $('.asst-titolo'), elTesto = $('.asst-testo'), elRobot = $('.asst-robot'), elTour = $('.asst-tour'),
      elSugg = $('.asst-sugg'), elInput = $('.asst-chiedi input'), btnMic = pan.querySelector('[data-az="mic"]'), btnVoce = pan.querySelector('[data-az="voce"]');
  if (!SR) btnMic.style.display = 'none';
  if (!SS) { btnVoce.style.display = 'none'; pan.querySelector('[data-az="silenzio"]').style.display = 'none'; }

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
    var vs = (SS && SS.getVoices && SS.getVoices()) || [], it = vs.filter(function (v) { return /^it/i.test(v.lang); });
    return it.filter(function (v) { return /google|natural|neural|premium/i.test(v.name); })[0] || it[0] || null;
  }
  function spezza(testo) {
    var frasi = testo.split(/(?<=[.!?;:])\s+/), out = [], cur = '';
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
      var u = new w.SpeechSynthesisUtterance(pezzi[i++]); u.lang = 'it-IT'; u.rate = 1; u.pitch = 1.05;
      if (voce) u.voice = voce;
      u.onend = dici; u.onerror = function () { elRobot.classList.remove('parla'); };
      elRobot.classList.add('parla'); SS.speak(u);
    }
    dici();
  }
  function mostra(titolo, testo, voceTesto, alFine) {
    elTitolo.textContent = titolo || ''; elTesto.innerHTML = mdHtml(testo); $('.asst-bolla').scrollTop = 0;
    parla((titolo ? titolo + (/[.!?:]$/.test(titolo) ? ' ' : '. ') : '') + (voceTesto || testo), alFine);
  }
  function avviso(m) { toast.textContent = m; toast.style.display = 'block'; w.setTimeout(function () { toast.style.display = 'none'; }, 5200); }

  /* ---------- ricerca nella guida (come quella scritta) ---------- */
  var STOP = {}; ('il lo la i gli le un uno una di a da in con su per tra fra e o ma che chi cui come dove quando cosa quale quali mi ti si ci vi non ' +
    'del dello della dei degli delle al allo alla ai agli alle dal dallo dalla dai dagli dalle nel nello nella nei negli nelle sul sullo sulla sui sugli sulle ' +
    'è sono ho hai ha posso puoi fare faccio fa devo voglio vorrei se questo questa quello quella mio mia miei mie tuo tua app dell all anche più poi può modo').split(' ').forEach(function (p) { STOP[p] = 1; });
  function norm(s) { return String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' '); }
  function stem(p) { return p.length > 4 ? p.replace(/[aeiou]+$/, '') : p; }
  function parole(s) { var o = {}; norm(s).split(' ').forEach(function (p) { if (p.length >= 3 && !STOP[p]) o[stem(p)] = 1; }); return Object.keys(o); }
  function combacia(q, ins) { for (var i = 0; i < ins.length; i++) { var x = ins[i]; if (x.indexOf(q) === 0 || (x.length >= 4 && q.indexOf(x) === 0)) return true; } return false; }
  var indice = null;
  function costruisci() { indice = D.guida.map(function (g) { return {g: g, t: parole(g.t), k: parole(g.k), b: parole(g.b)}; }); }
  function cerca(domanda) {
    if (!indice) costruisci();
    var q = parole(domanda); if (!q.length) return [];
    var ris = [];
    indice.forEach(function (e) {
      var pt = 0, tr = 0;
      q.forEach(function (x) {
        if (combacia(x, e.t)) { pt += 3; tr++; } else if (combacia(x, e.k)) { pt += 2; tr++; } else if (combacia(x, e.b)) { pt += 1; tr++; }
      });
      if (pt) ris.push({p: pt + tr + (e.g.s === D.sezione ? 1 : 0), g: e.g});
    });
    ris.sort(function (a, b) { return b.p - a.p; });
    if (!ris.length) return [];
    var top = ris[0].p; return ris.filter(function (r) { return r.p * 2 >= top; }).slice(0, 4).map(function (r) { return r.g; });
  }
  function argomento(g) {
    tourAttivo = false; elTour.style.display = 'none';
    var corto = perVoce(g.b); if (corto.length > 900) corto = corto.slice(0, 900).replace(/[^.]*$/, '') || corto.slice(0, 900);
    mostra(g.t, g.b, corto);
    chips([]);
  }
  function chips(lista, titolo) {
    elSugg.innerHTML = '';
    lista.forEach(function (g) {
      var b = doc.createElement('button'); b.textContent = g.t; b.addEventListener('click', function () { argomento(g); }); elSugg.appendChild(b);
    });
  }
  function argomentiSezione() { return D.guida.filter(function (g) { return g.s === D.sezione; }).slice(0, 8); }

  /* ---------- azioni ---------- */
  function paginaCorrente() {
    tourAttivo = false; elTour.style.display = 'none';
    var p = D.pagine[D.sezione] || D.pagine.dispensa;
    mostra(p[0], p[1] + '\n\nTocca un argomento qui sotto per saperne di più.');
    chips(argomentiSezione());
  }
  function novita() {
    tourAttivo = false; elTour.style.display = 'none'; chips([]);
    if (!D.novita.length) { mostra('Novità', 'Per ora non ci sono novità recenti. Ti avviso io quando ne arrivano!'); return; }
    var testo = D.novita.map(function (n) { return '**' + n.i + ' ' + n.t + '**\n📍 ' + n.d; }).join('\n\n');
    var voceT = 'Ecco le novità. ' + D.novita.map(function (n) { return n.t + '. La trovi così: ' + n.d + '.'; }).join(' ');
    mostra('Cosa c\'è di nuovo', testo, voceT);
  }
  function tourVai(i) {
    tourIdx = Math.max(0, Math.min(D.tour.length - 1, i)); tourAttivo = true; chips([]);
    elTour.style.display = 'grid'; elTour.querySelector('span').textContent = (tourIdx + 1) + ' / ' + D.tour.length;
    var s = D.tour[tourIdx]; mostra(s[0], s[1]);
  }
  function tourFine() { tourAttivo = false; elTour.style.display = 'none'; ferma(); mostra('Fine del giro', 'Ecco fatto! Se ti serve altro, chiedimi.'); chips(argomentiSezione()); }
  function ascolta() {
    if (!SR) { mostra('Microfono', 'Su questo telefono non riesco ad ascoltarti: scrivi la domanda qui sotto.'); return; }
    if (riconoscimento) { try { riconoscimento.stop(); } catch (e) {} return; }
    ferma();
    var r = new SR(); riconoscimento = r; r.lang = 'it-IT'; r.interimResults = false; r.maxAlternatives = 1;
    btnMic.classList.add('ascolta'); elRobot.classList.add('ascolta'); btnMic.textContent = '⏹ Sto ascoltando…';
    mostra('Ti ascolto', 'Parla ora: per esempio «come aggiungo una foto al documento?»', ' ');
    var detto = false;
    function fine() { riconoscimento = null; btnMic.classList.remove('ascolta'); elRobot.classList.remove('ascolta'); btnMic.textContent = '🎤 Fai una domanda'; }
    r.onresult = function (e) { detto = true; var t = e.results[0][0].transcript; fine(); elInput.value = t; chiedi(t); };
    r.onerror = function (e) {
      fine(); detto = true;
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') mostra('Microfono', 'Consenti l\'uso del microfono al browser per parlare con me.', ' ');
      else if (e.error === 'no-speech') mostra('Non ho sentito niente', 'Riprova: tocca il microfono e parla.', ' ');
      else mostra('Microfono', 'Non riesco a usare la voce ora: scrivi la domanda qui sotto.', ' ');
    };
    r.onend = function () { if (!detto) { fine(); mostra('Non ho sentito niente', 'Riprova: tocca il microfono e parla.', ' '); } else { fine(); } };
    try { r.start(); } catch (e) { fine(); }
  }
  function chiedi(testo) {
    testo = (testo || '').trim(); if (!testo) { mostra('Dimmi pure', 'Scrivi o dì cosa vuoi sapere.', ' '); return; }
    var n = norm(testo);
    if (/\b(silenzio|zitto|basta|smetti)\b/.test(n)) { ferma(); return; }
    if (/(disattiv|spegn).*(assistent|te)|non voglio.*assistent/.test(n)) { mostra('Vuoi che mi disattivi?', 'Tocca il pulsante «⛔ Disattiva assistente» qui sotto. Mi riattivi dal pulsante rosso «Clicca per informazioni».'); chips([]); return; }
    if (/(novit|nuovo|nuove|aggiornament)/.test(n)) { novita(); return; }
    if (/(giro|tutorial|spiegami l app|come si usa l app|guida completa|inizia)/.test(n)) { tourVai(0); return; }
    if (/^(ciao|salve|buongiorno|buonasera|aiuto|help)\b/.test(n)) { paginaCorrente(); return; }
    var ris = cerca(testo);
    if (!ris.length) { mostra('Non ho trovato la risposta', 'Prova con altre parole (per esempio una sola: foto, scadenza, password) oppure scegli un argomento qui sotto.', 'Non ho trovato la risposta. Prova con altre parole, oppure scegli un argomento qui sotto.'); chips(argomentiSezione()); return; }
    argomento(ris[0]); chips(ris.slice(1));
  }
  function aggiornaVoceBtn() { btnVoce.textContent = voceOn ? '🔊 Voce: attiva' : '🔇 Voce: spenta'; }
  function apri() {
    if (!attivo) return; aperto = true; pan.style.display = 'block'; btn.style.display = 'none';
    if (!corrente) { corrente = 1; mostra('Ciao, sono il tuo assistente!', 'Ti aiuto a capire come si usa l\'app. Scegli cosa vuoi: spiegarti questa pagina, farti fare un giro dell\'app, dirti le novità, oppure fammi una domanda a voce o scrivendo.', 'Ti aiuto a capire come si usa l\'app. Scegli cosa vuoi che ti spieghi.'); chips(argomentiSezione()); }
  }
  function chiudi() { aperto = false; pan.style.display = 'none'; ferma(); if (riconoscimento) { try { riconoscimento.abort(); } catch (e) {} } if (attivo) btn.style.display = 'block'; }
  function imposta(on) {
    attivo = on; scrivi('asst_attivo', on ? '1' : '0');
    if (!on) { chiudi(); btn.style.display = 'none'; avviso('Assistente disattivato. Lo riattivi da «Clicca per informazioni».'); }
    else { btn.style.display = aperto ? 'none' : 'block'; avviso('Assistente attivo: tocca il robottino.'); }
  }

  btn.addEventListener('click', apri);
  pan.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('button') : null; if (!b) return;
    if (b.classList.contains('asst-x')) { chiudi(); return; }
    var az = b.getAttribute('data-az'); if (!az) return;
    if (az === 'pagina') paginaCorrente(); else if (az === 'giro') tourVai(0); else if (az === 'novita') novita(); else if (az === 'mic') ascolta();
    else if (az === 'avanti') { if (tourIdx >= D.tour.length - 1) tourFine(); else tourVai(tourIdx + 1); }
    else if (az === 'indietro') tourVai(tourIdx - 1); else if (az === 'fine') tourFine();
    else if (az === 'chiedi') chiedi(elInput.value);
    else if (az === 'voce') { voceOn = !voceOn; scrivi('asst_voce', voceOn ? '1' : '0'); if (!voceOn) ferma(); aggiornaVoceBtn(); }
    else if (az === 'silenzio') ferma(); else if (az === 'off') imposta(false);
  });
  elInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); chiedi(elInput.value); } });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && aperto) chiudi(); });
  if (SS && SS.addEventListener) SS.addEventListener('voiceschanged', function () {});
  aggiornaVoceBtn();
  btn.style.display = attivo ? 'block' : 'none';

  w.__assistente = {
    versione: D.versione,
    aggiorna: function (c) {
      if (c.sezione) D.sezione = c.sezione;
      if (c.guida) { D.guida = c.guida; indice = null; }
      if (c.novita) D.novita = c.novita;
      if (c.cmd && c.cmd.id && c.cmd.id !== ultimoCmd) { ultimoCmd = c.cmd.id; if (c.cmd.az === 'on') imposta(true); else if (c.cmd.az === 'off') imposta(false); }
    },
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
    try:
        from datetime import date as _d
        oggi_ = oggi() if "oggi" in globals() else _d.today()
        return [{"i": n[1], "t": n[2], "d": n[3]} for n in _NOVITA if (oggi_ - _d.fromisoformat(n[0])).days <= 14][:6]
    except Exception:
        return []


def _config_assistente(sezione, completo, cmd):
    cfg = {"sezione": sezione, "novita": _novita_recenti()}
    if cmd:
        cfg["cmd"] = {"id": str(__import__("time").time()), "az": cmd}
    if completo:
        cfg["versione"] = _VERSIONE_ASSISTENTE
        cfg["guida"] = [{"s": sez, "t": titolo, "b": corpo, "k": chiavi}
                        for sez, voci in _GUIDE.items() for (titolo, corpo, chiavi) in voci]
        cfg["pagine"] = {k: list(v) for k, v in _PAGINE.items()}
        cfg["tour"] = [list(x) for x in _TOUR]
        cfg["img"] = {"intero": _as_uri("assistente.webp"), "testa": _as_uri("assistente_testa.webp")}
    return cfg


def assistente(sezione):
    """Mostra (o aggiorna) il robottino assistente. Va chiamato dalle pagine principali; invia lo script completo solo la prima
    volta, poi solo la pagina in cui ci si trova e gli eventuali comandi (Attiva / Disattiva)."""
    cmd = st.session_state.pop("_asst_cmd", None)
    completo = not st.session_state.get("_asst_inviato")
    if not completo and st.session_state.get("_asst_sezione") == sezione and not cmd:
        return
    st.session_state["_asst_inviato"] = True
    st.session_state["_asst_sezione"] = sezione
    cfg = _config_assistente(sezione, completo, cmd)
    if completo:
        codice = _JS_ASSISTENTE.replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False))
    else:
        codice = ("(function(){var a=window.__assistente;if(a)a.aggiorna(" + json.dumps(cfg, ensure_ascii=False) + ");})();")
    _inietta(codice)
