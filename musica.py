# -*- coding: utf-8 -*-
"""RADIO DI SOTTOFONDO — una linguetta «cool» sul bordo dello schermo, in tutte le sezioni.

Tocchi la linguetta 🎧 e si apre un pannello a scomparsa con:
  • una lista di stazioni lounge/chill pronte e una RICERCA tra migliaia di radio del mondo (per nome o per genere: lounge, chillout, jazz, classica, ambient, Italia…),
    dall'elenco pubblico e gratuito «Radio Browser»;
  • ▶/⏸ e ⏹, il VOLUME, le stazioni PREFERITE (★);
  • un EQUALIZZATORE a tre bande (bassi, medi, alti) e uno SPETTRO che si muove con il suono — se la stazione lo permette
    (alcune radio non consentono ai browser di leggere il suono: allora restano volume e musica, e lo spettro è solo un'animazione, dichiarata).
La musica vive nella pagina del browser, non nella pagina di Streamlit: continua a suonare quando cambi sezione o tocchi i pulsanti.
Se chiudi la scheda o ricarichi l'app, si ferma (e il telefono può fermarla con lo schermo spento: è una scelta di Android/Chrome).
Il primo ascolto parte solo dopo un tuo tocco: i telefoni non permettono di far partire l'audio da soli.
Si può nascondere da Utilità → Aspetto dell'app. Caricato da app_dispensa.py dopo pagine_nav.py."""
import json

import streamlit as st

# stazioni di partenza (lounge e chill). Se una non parte, il pannello lo dice: la ricerca ne ha migliaia.
_MU_PRESET = [
    {"n": "Groove Salad · chill e downtempo", "u": "https://ice1.somafm.com/groovesalad-128-mp3", "p": "SomaFM"},
    {"n": "Illinois Street Lounge · lounge anni 50-60", "u": "https://ice1.somafm.com/illstreet-128-mp3", "p": "SomaFM"},
    {"n": "Secret Agent · lounge e spy", "u": "https://ice1.somafm.com/secretagent-128-mp3", "p": "SomaFM"},
    {"n": "Lush · chill vellutato", "u": "https://ice1.somafm.com/lush-128-mp3", "p": "SomaFM"},
    {"n": "Sonic Universe · jazz moderno", "u": "https://ice1.somafm.com/sonicuniverse-128-mp3", "p": "SomaFM"},
    {"n": "Fluid · strumentale rilassante", "u": "https://ice1.somafm.com/fluid-128-mp3", "p": "SomaFM"},
    {"n": "Drone Zone · ambient", "u": "https://ice1.somafm.com/dronezone-128-mp3", "p": "SomaFM"},
    {"n": "Space Station Soma · ambient elettronico", "u": "https://ice1.somafm.com/spacestation-128-mp3", "p": "SomaFM"},
    {"n": "Radio Paradise · mix eclettico", "u": "https://stream.radioparadise.com/mp3-128", "p": "Radio Paradise"},
]

_MU_JS = r"""
(function () {
  var w = window, doc = w.document, ATTIVA = __ATTIVA__, PRESET = __PRESET__;
  if (w.__musica) { w.__musica.attiva(ATTIVA); return; }
  var M = w.__musica = {};
  var LS = null; try { LS = w.localStorage; } catch (e) { LS = null; }
  function leggi(k, d) { try { var v = LS ? LS.getItem('mu_' + k) : null; return (v === null || v === undefined) ? d : JSON.parse(v); } catch (e) { return d; } }
  function scrivi(k, v) { try { if (LS) LS.setItem('mu_' + k, JSON.stringify(v)); } catch (e) {} }
  var S = { duck: false, audio: null, ctx: null, nodi: null, staz: leggi('ultima', null), limitata: false, vol: leggi('vol', 0.7), eq: leggi('eq', [0, 0, 0]), fav: leggi('fav', []), suona: false, aperto: false, risultati: [] };
  if (typeof S.vol !== 'number') S.vol = 0.7;
  if (!S.eq || S.eq.length !== 3) S.eq = [0, 0, 0];
  if (!Array.isArray(S.fav)) S.fav = [];
  function el(t, c, h) { var e = doc.createElement(t); if (c) e.className = c; if (h !== undefined) e.innerHTML = h; return e; }
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  // ---------- stile ----------
  var css = el('style'); css.id = 'mu-css';
  css.textContent =
    '#mu-tab{position:fixed;left:0;top:46%;z-index:99989;width:32px;height:88px;border-radius:0 18px 18px 0;opacity:.92;border:2px solid rgba(255,255,255,.75);border-left:0;background:linear-gradient(160deg,#7c4dff 0%,#00bcd4 100%);' +
    'box-shadow:0 6px 18px rgba(60,30,140,.45);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:0;-webkit-tap-highlight-color:transparent;transition:transform .2s}' +
    '#mu-tab:active{transform:translateX(3px)} #mu-tab .ic{font-size:1.15rem;line-height:1;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))}' +
    '#mu-tab .bar{display:flex;gap:2px;align-items:flex-end;height:16px}#mu-tab .bar i{display:block;width:3px;height:5px;border-radius:2px;background:#fff;opacity:.55}' +
    '#mu-tab.on .bar i{opacity:1;animation:mu-sal 0.9s ease-in-out infinite}#mu-tab.on .bar i:nth-child(2){animation-delay:.2s}#mu-tab.on .bar i:nth-child(3){animation-delay:.4s}#mu-tab.on .bar i:nth-child(4){animation-delay:.1s}' +
    '#mu-tab.on{box-shadow:0 0 0 0 rgba(124,77,255,.8),0 6px 18px rgba(60,30,140,.45);animation:mu-puls 1.8s ease-out infinite}' +
    '@keyframes mu-sal{0%,100%{height:4px}50%{height:16px}}@keyframes mu-puls{0%{box-shadow:0 0 0 0 rgba(124,255,230,.75),0 6px 18px rgba(60,30,140,.45)}100%{box-shadow:0 0 0 16px rgba(124,255,230,0),0 6px 18px rgba(60,30,140,.45)}}' +
    '@media (prefers-reduced-motion:reduce){#mu-tab.on,#mu-tab.on .bar i{animation:none !important}}' +
    '#mu-pan{position:fixed;left:8px;top:7vh;z-index:99991;width:min(94vw,390px);max-height:84vh;overflow:auto;border-radius:24px;padding:14px 14px 16px;color:#fff;font-family:inherit;' +
    'background:linear-gradient(180deg,rgba(25,18,60,.97) 0%,rgba(10,30,52,.97) 100%);border:2px solid transparent;background-clip:padding-box;box-shadow:0 0 0 2px rgba(124,255,230,.55),0 18px 44px rgba(0,0,0,.55);' +
    'transform:translateX(-115%);transition:transform .28s ease;visibility:hidden}' +
    '#mu-pan.ap{transform:translateX(0);visibility:visible}' +
    '#mu-pan h3{margin:0;font-size:1.1rem;color:#fff}#mu-pan .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}' +
    '#mu-pan button{font-family:inherit;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '#mu-pan .x{background:rgba(255,255,255,.15);color:#fff;border:0;border-radius:50%;width:36px;height:36px;font-size:1.1rem}' +
    '#mu-pan .st{font-size:.88rem;color:#b2ebf2;min-height:1.3em;margin:2px 0 8px;word-break:break-word}' +
    '#mu-pan .ctl{display:flex;gap:8px;align-items:center;margin-bottom:8px}' +
    '#mu-pan .pl{flex:0 0 58px;height:58px;border-radius:50%;border:0;background:linear-gradient(135deg,#00e5ff,#7c4dff);color:#fff;font-size:1.6rem;box-shadow:0 4px 12px rgba(0,229,255,.4)}' +
    '#mu-pan .sm{flex:0 0 44px;height:44px;border-radius:50%;border:0;background:rgba(255,255,255,.16);color:#fff;font-size:1.1rem}' +
    '#mu-pan input[type=range]{flex:1;min-width:0;height:34px;accent-color:#00e5ff}' +
    '#mu-pan canvas{width:100%;height:70px;display:block;border-radius:14px;background:rgba(0,0,0,.35);margin:4px 0 2px}' +
    '#mu-pan .nota{font-size:.74rem;color:#90a4ae;margin:0 0 8px}' +
    '#mu-pan .eq{display:grid;grid-template-columns:62px 1fr 38px;gap:2px 8px;align-items:center;margin:6px 0 4px;font-size:.84rem}' +
    '#mu-pan .eq span.v{text-align:right;color:#80deea}#mu-pan .eq.off{opacity:.4}' +
    '#mu-pan h4{margin:12px 0 5px;font-size:.92rem;color:#e1bee7}' +
    '#mu-pan .lis{display:flex;flex-direction:column;gap:6px;max-height:34vh;overflow:auto}' +
    '#mu-pan .r{display:flex;gap:6px;align-items:stretch}#mu-pan .r .n{flex:1;text-align:left;background:rgba(255,255,255,.1);border:0;border-radius:14px;color:#fff;padding:9px 12px;font-size:.88rem;min-height:44px;line-height:1.25}' +
    '#mu-pan .r .n small{display:block;color:#90caf9;font-size:.72rem}#mu-pan .r .n.cor{background:linear-gradient(135deg,rgba(0,229,255,.35),rgba(124,77,255,.4));outline:2px solid #00e5ff}' +
    '#mu-pan .r .f{flex:0 0 44px;border:0;border-radius:14px;background:rgba(255,255,255,.1);color:#ffd54f;font-size:1.15rem}' +
    '#mu-pan .cer{display:flex;gap:6px;margin-bottom:6px}#mu-pan .cer input[type=text]{flex:1;min-width:0;border-radius:14px;border:0;padding:10px 12px;font-size:.95rem;background:#fff;color:#111}' +
    '#mu-pan .cer button{flex:0 0 52px;border:0;border-radius:14px;background:#7c4dff;color:#fff;font-size:1.1rem}' +
    '#mu-pan .gen{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px}#mu-pan .gen button{border:0;border-radius:999px;padding:7px 12px;background:rgba(255,255,255,.14);color:#fff;font-size:.82rem;min-height:36px}' +
    '#mu-pan .spegni{width:100%;margin-top:12px;min-height:46px;border-radius:14px;border:2px solid rgba(255,255,255,.5);background:transparent;color:#fff;font-size:.95rem}';
  doc.head.appendChild(css);

  // ---------- elementi ----------
  var tab = el('button', '', '<span class="ic">🎧</span><span class="bar"><i></i><i></i><i></i><i></i></span>');
  tab.id = 'mu-tab'; tab.type = 'button'; tab.setAttribute('aria-label', 'Radio di sottofondo');
  var pan = el('div'); pan.id = 'mu-pan'; pan.setAttribute('role', 'dialog'); pan.setAttribute('aria-label', 'Radio di sottofondo');
  pan.innerHTML =
    '<div class="top"><h3>🎧 Radio di sottofondo</h3><button class="x" type="button" data-a="chiudi" aria-label="Chiudi">✕</button></div>' +
    '<div class="st" data-r="stato">Scegli una stazione e tocca ▶</div>' +
    '<div class="ctl"><button class="pl" type="button" data-a="play" aria-label="Avvia o metti in pausa">▶</button><button class="sm" type="button" data-a="stop" aria-label="Spegni">⏹</button>' +
    '<button class="sm" type="button" data-a="muto" aria-label="Muto">🔊</button><input type="range" min="0" max="100" step="1" data-r="vol" aria-label="Volume"></div>' +
    '<canvas data-r="spettro" width="360" height="70"></canvas><div class="nota" data-r="notaspettro"></div>' +
    '<div class="eq" data-r="eq"><span>🔈 Bassi</span><input type="range" min="-12" max="12" step="1" data-b="0"><span class="v" data-v="0">0</span>' +
    '<span>🎤 Medi</span><input type="range" min="-12" max="12" step="1" data-b="1"><span class="v" data-v="1">0</span>' +
    '<span>✨ Alti</span><input type="range" min="-12" max="12" step="1" data-b="2"><span class="v" data-v="2">0</span></div>' +
    '<div class="nota" data-r="notaeq"></div><button class="sm" type="button" data-a="piatto" style="width:auto;border-radius:14px;padding:0 12px;font-size:.8rem">↺ Equalizzatore piatto</button>' +
    '<h4>⭐ Le tue preferite</h4><div class="lis" data-r="fav"></div>' +
    '<h4>🌙 Lounge e chill (pronte)</h4><div class="lis" data-r="preset"></div>' +
    '<h4>🔎 Cerca tra migliaia di radio</h4><div class="cer"><input type="text" data-r="q" placeholder="nome o genere (es. lounge, jazz, Radio Capital)" aria-label="Cerca una radio"><button type="button" data-a="cerca" aria-label="Cerca">🔎</button></div>' +
    '<div class="gen" data-r="gen"></div><div class="st" data-r="statocerca"></div><div class="lis" data-r="ris"></div>' +
    '<button class="spegni" type="button" data-a="spegni">⏹ Spegni la radio e chiudi</button>';
  doc.body.appendChild(tab); doc.body.appendChild(pan);
  function q(r) { return pan.querySelector('[data-r="' + r + '"]'); }

  // ---------- audio ----------
  function mostraStato(t) { q('stato').textContent = t; }
  function segna(on) { S.suona = on; tab.classList.toggle('on', on); pan.querySelector('[data-a="play"]').textContent = on ? '⏸' : '▶'; }
  function grafo(e) {
    try {
      var AC = w.AudioContext || w.webkitAudioContext; if (!AC) return false;
      if (!S.ctx) S.ctx = new AC();
      if (S.ctx.resume) S.ctx.resume();
      var src = S.ctx.createMediaElementSource(e);
      var b = S.ctx.createBiquadFilter(); b.type = 'lowshelf'; b.frequency.value = 200;
      var m = S.ctx.createBiquadFilter(); m.type = 'peaking'; m.frequency.value = 1000; m.Q.value = 1;
      var a = S.ctx.createBiquadFilter(); a.type = 'highshelf'; a.frequency.value = 4000;
      var an = S.ctx.createAnalyser(); an.fftSize = 128; an.smoothingTimeConstant = .78;
      src.connect(b); b.connect(m); m.connect(a); a.connect(an); an.connect(S.ctx.destination);
      S.nodi = { f: [b, m, a], an: an }; applicaEq(); return true;
    } catch (x) { S.nodi = null; return false; }
  }
  function applicaEq() { if (!S.nodi) return; for (var i = 0; i < 3; i++) { try { S.nodi.f[i].gain.value = S.eq[i]; } catch (e) {} } }
  function volEff() { return (S.muto || S.duck) ? 0 : S.vol; }
  function applicaVol() { if (S.audio) { try { S.audio.volume = volEff(); } catch (x) {} } }
  function ferma() {
    if (S.audio) { try { S.audio.onerror = null; S.audio.pause(); S.audio.removeAttribute('src'); S.audio.load(); } catch (e) {} }
    S.audio = null; S.nodi = null; segna(false); aggiornaNote();
  }
  function avvia(st, senzaCors) {
    ferma(); S.staz = st; scrivi('ultima', st); aggiornaLista(); mostraStato('Mi collego a «' + st.n + '»…');
    if (!/^https:/i.test(st.u || '')) { mostraStato('Questa stazione non è sicura (non https): scegline un\'altra.'); return; }
    var e = new Audio(); e.preload = 'none'; e.volume = volEff();
    if (!senzaCors) e.crossOrigin = 'anonymous';
    S.audio = e; S.limitata = !!senzaCors; var partito = false;
    if (!senzaCors) grafo(e);
    e.addEventListener('playing', function () { partito = true; segna(true); mostraStato('🎶 In ascolto: ' + st.n); aggiornaNote(); });
    e.addEventListener('waiting', function () { if (S.audio === e) mostraStato('Un attimo… carico la musica'); });
    e.addEventListener('error', function () {
      if (S.audio !== e) return;
      if (partito) { mostraStato('Il collegamento si è interrotto: riprovo…'); setTimeout(function () { if (S.audio === e) avvia(st, senzaCors); }, 2500); return; }
      if (!senzaCors) { avvia(st, true); return; }
      segna(false); mostraStato('Questa stazione non risponde: scegline un\'altra.');
    });
    e.src = st.u;
    var p; try { p = e.play(); } catch (x) { p = null; }
    if (p && p.catch) p.catch(function (x) { if (x && x.name === 'NotAllowedError') mostraStato('Tocca ▶ per far partire la musica'); });
  }
  function aggiornaNote() {
    q('notaspettro').textContent = S.audio && S.limitata ? 'Animazione: questa stazione non permette di leggere il suono.' : '';
    var off = !!(S.audio && S.limitata);
    q('eq').classList.toggle('off', off);
    q('notaeq').textContent = off ? 'Questa stazione non permette l\'equalizzatore: restano musica e volume. Prova un\'altra stazione.' : '';
    var ins = pan.querySelectorAll('.eq input'); for (var i = 0; i < ins.length; i++) ins[i].disabled = off;
  }

  // ---------- liste ----------
  function eFav(u) { for (var i = 0; i < S.fav.length; i++) if (S.fav[i].u === u) return true; return false; }
  function riga(st, extra) {
    var r = el('div', 'r'); var cor = S.staz && S.staz.u === st.u;
    var n = el('button', 'n' + (cor ? ' cor' : ''), esc(st.n) + (extra ? '<small>' + esc(extra) + '</small>' : '')); n.type = 'button';
    n.addEventListener('click', function () { avvia(st, false); });
    var f = el('button', 'f', eFav(st.u) ? '★' : '☆'); f.type = 'button'; f.setAttribute('aria-label', 'Preferita');
    f.addEventListener('click', function () {
      if (eFav(st.u)) S.fav = S.fav.filter(function (x) { return x.u !== st.u; }); else S.fav.push({ n: st.n, u: st.u, p: st.p || '' });
      scrivi('fav', S.fav); aggiornaLista(); });
    r.appendChild(n); r.appendChild(f); return r;
  }
  function riempi(id, lista, vuoto) {
    var c = q(id); c.innerHTML = ''; if (!lista.length) { c.appendChild(el('div', 'nota', vuoto)); return; }
    lista.forEach(function (s) { c.appendChild(riga(s, s.p)); });
  }
  function aggiornaLista() {
    riempi('fav', S.fav, 'Tocca la ☆ accanto a una radio per tenerla qui.'); riempi('preset', PRESET, '');
    var c = q('ris'); c.innerHTML = ''; S.risultati.forEach(function (s) { c.appendChild(riga(s, s.p)); });
  }
  var GEN = [['Lounge', 'lounge'], ['Chillout', 'chillout'], ['Jazz', 'jazz'], ['Classica', 'classical'], ['Ambient', 'ambient'], ['Bossa nova', 'bossa nova'], ['Pop', 'pop'], ['Rock', 'rock'], ['Anni 80', '80s'], ['Dance', 'dance'], ['🇮🇹 Italia', '@IT']];
  GEN.forEach(function (g) { var b = el('button', '', g[0]); b.type = 'button'; b.addEventListener('click', function () { cerca('', g[1]); }); q('gen').appendChild(b); });
  function host() {
    if (M.host) return Promise.resolve(M.host);
    return w.fetch('https://all.api.radio-browser.info/json/servers').then(function (r) { return r.json(); }).then(function (a) {
      var h = (a || []).map(function (x) { return x && x.name; }).filter(Boolean); M.host = h.length ? h[Math.floor(Math.random() * h.length)] : 'de1.api.radio-browser.info'; return M.host;
    }).catch(function () { M.host = 'de1.api.radio-browser.info'; return M.host; });
  }
  function cerca(testo, tag) {
    q('statocerca').textContent = 'Cerco…'; q('ris').innerHTML = '';
    host().then(function (h) {
      var u = 'https://' + h + '/json/stations/search?limit=80&hidebroken=true&order=clickcount&reverse=true';
      if (testo) u += '&name=' + encodeURIComponent(testo);
      if (tag === '@IT') u += '&countrycode=IT'; else if (tag) u += '&tag=' + encodeURIComponent(tag);
      return w.fetch(u);
    }).then(function (r) { return r.json(); }).then(function (a) {
      var ok = (a || []).filter(function (s) { var u = s.url_resolved || s.url || ''; return /^https:/i.test(u) && /mp3|aac|ogg|mpeg/i.test(s.codec || 'mp3'); });
      S.risultati = ok.slice(0, 30).map(function (s) { return { n: (s.name || 'Radio').trim(), u: s.url_resolved || s.url, p: [s.countrycode, s.codec, s.bitrate ? s.bitrate + 'k' : ''].filter(Boolean).join(' · ') }; });
      q('statocerca').textContent = S.risultati.length ? 'Trovate ' + S.risultati.length + ' radio: tocca il nome per ascoltare.' : 'Nessuna radio trovata con questi criteri: prova un\'altra parola o un genere.';
      aggiornaLista();
    }).catch(function () { q('statocerca').textContent = 'Non riesco a cercare ora: controlla la connessione e riprova.'; });
  }

  // ---------- spettro ----------
  var cv = q('spettro'), g2 = cv.getContext ? cv.getContext('2d') : null, t0 = 0;
  function disegna() {
    if (!S.aperto) return; if (w.requestAnimationFrame) w.requestAnimationFrame(disegna);
    if (!g2) return; var W = cv.width, H = cv.height; g2.clearRect(0, 0, W, H);
    var N = 32, bw = W / N, dati = null;
    if (S.nodi && S.nodi.an && S.suona) { dati = new Uint8Array(S.nodi.an.frequencyBinCount); S.nodi.an.getByteFrequencyData(dati); }
    t0 += 0.08;
    for (var i = 0; i < N; i++) {
      var v;
      if (dati) v = (dati[Math.min(dati.length - 1, Math.floor(i * dati.length / N / 1.4))] || 0) / 255;
      else if (S.suona) v = 0.25 + 0.2 * Math.sin(t0 + i * 0.5) + 0.15 * Math.sin(t0 * 1.7 + i * 1.3);
      else v = 0.04;
      var h = Math.max(2, v * H * 0.95);
      var gr = g2.createLinearGradient(0, H, 0, 0); gr.addColorStop(0, '#00e5ff'); gr.addColorStop(0.6, '#7c4dff'); gr.addColorStop(1, '#ff4081');
      g2.fillStyle = gr; g2.fillRect(i * bw + 1, H - h, bw - 3, h);
    }
  }

  // ---------- comandi ----------
  function apri(si) {
    S.aperto = si; pan.classList.toggle('ap', si); if (si) { aggiornaLista(); aggiornaNote(); disegna(); }
  }
  tab.addEventListener('click', function () { apri(!S.aperto); });
  pan.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.getAttribute && ev.target.getAttribute('data-a'); if (!a) return;
    if (a === 'chiudi') apri(false);
    else if (a === 'play') {
      if (S.audio && S.suona) { S.audio.pause(); segna(false); mostraStato('In pausa'); }
      else if (S.audio) { var p = S.audio.play(); if (p && p.catch) p.catch(function () {}); }
      else if (S.staz) avvia(S.staz, false);
      else if (PRESET.length) avvia(PRESET[0], false);
    }
    else if (a === 'stop') { ferma(); mostraStato('Fermata'); }
    else if (a === 'spegni') { ferma(); mostraStato('Radio spenta'); apri(false); }
    else if (a === 'muto') { S.muto = !S.muto; applicaVol(); ev.target.textContent = S.muto ? '🔇' : '🔊'; }
    else if (a === 'piatto') { S.eq = [0, 0, 0]; scrivi('eq', S.eq); mostraEq(); applicaEq(); }
    else if (a === 'cerca') cerca(q('q').value.trim(), '');
  });
  q('q').addEventListener('keydown', function (ev) { if (ev.key === 'Enter') cerca(q('q').value.trim(), ''); });
  var vol = q('vol'); vol.value = Math.round(S.vol * 100);
  vol.addEventListener('input', function () { S.vol = vol.value / 100; S.muto = false; applicaVol(); scrivi('vol', S.vol); });
  function mostraEq() { for (var i = 0; i < 3; i++) { pan.querySelector('[data-b="' + i + '"]').value = S.eq[i]; pan.querySelector('[data-v="' + i + '"]').textContent = (S.eq[i] > 0 ? '+' : '') + S.eq[i]; } }
  [0, 1, 2].forEach(function (i) {
    pan.querySelector('[data-b="' + i + '"]').addEventListener('input', function (ev) { S.eq[i] = parseInt(ev.target.value, 10) || 0; scrivi('eq', S.eq); mostraEq(); applicaEq(); });
  });
  mostraEq(); aggiornaLista(); aggiornaNote();
  if (S.staz) mostraStato('Ultima stazione: ' + S.staz.n + ' (tocca ▶)');
  // quando si apre il pannello dell'assistente la radio tace da sola, e riprende quando si chiude
  setInterval(function () {
    var a = doc.getElementById('asst-pan'); var ap = !!(a && a.style && a.style.display === 'block');
    if (ap !== S.duck) {
      S.duck = ap; applicaVol();
      if (S.audio && S.suona && S.staz) mostraStato(ap ? '🔇 In silenzio mentre parla l\'assistente' : '🎶 In ascolto: ' + S.staz.n);
    }
  }, 300);
  M.attiva = function (si) { tab.style.display = si ? 'flex' : 'none'; if (!si) { ferma(); apri(false); } };
  M.stato = S; M.avvia = avvia; M.cerca = cerca;
  M.attiva(ATTIVA);
})();
"""


def musica_attiva():
    """True se la radio è visibile (si spegne da Utilità → Aspetto dell'app)."""
    if "pn_musica" not in st.session_state:
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"])
            v = (d.get("impostazioni") or {}).get("musica", True)
        except Exception:
            v = True
        st.session_state["pn_musica"] = bool(v)
    return bool(st.session_state["pn_musica"])


def musica_inietta():
    """Mette (o aggiorna) la linguetta della radio nella pagina. La musica non si interrompe quando l'app si ridisegna."""
    codice = _MU_JS.replace("__ATTIVA__", "true" if musica_attiva() else "false").replace("__PRESET__", json.dumps(_MU_PRESET, ensure_ascii=False))
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + json.dumps(codice) + ";P.document.head.appendChild(s);s.parentNode.removeChild(s);})();</script>")
    if "pn_inietta_una_volta" in globals():
        pn_inietta_una_volta("musica", "on" if musica_attiva() else "off", pagina)
    else:
        try:
            st.html(pagina, unsafe_allow_javascript=True)
        except Exception:
            pass
