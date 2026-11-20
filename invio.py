# -*- coding: utf-8 -*-
"""INVIO E ESPORTAZIONE di tutto quello che c'è nell'app: Salute (medicinali, terapie, prescrizioni, visite, vaccini, documenti,
scheda sanitaria), dispensa e lista della spesa. Si prepara un PDF (anche Excel e file da stampare) e si invia con:
  📤 Telefono: la finestra «Condividi» di Android/iPhone (WhatsApp, Gmail, Telegram, Drive, Signal, Messenger… con il file allegato)
  ✉️ Email: direttamente dall'app, con gli allegati (servono EMAIL_USER ed EMAIL_PASSWORD nei Secrets di Streamlit)
  💬 WhatsApp: apre WhatsApp con il riepilogo scritto (il file si manda dalla scheda «Telefono»)
  ✈️ Telegram: manda file e riepilogo nella tua chat con il bot (servono TELEGRAM_TOKEN nei Secrets e il tuo Chat ID salvato)
  📱 SMS: apre i messaggi con il riepilogo breve
  📋 Copia: il riepilogo da incollare dove vuoi.
Ogni voce (documento, medicinale, prescrizione, visita) ha anche il suo tasto «Invia».
Caricato da app_dispensa.py dopo famiglia.py; i tasti si agganciano in farmacia.py e famiglia.py."""
import base64
import html
import io
import json
import re
import smtplib
from datetime import date
from email.message import EmailMessage
from urllib.parse import quote

import streamlit as st

_MAX_ALLEGATI = 18 * 1024 * 1024            # limite sicuro per le email (Gmail arriva a 25 MB)
_MAX_CONDIVISIONE = 25 * 1024 * 1024
_MIME = {"pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "html": "text/html",
         "json": "application/json", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
_EMOJI_SEZ = {"Medicinali": "💊", "Terapie": "📅", "Prescrizioni (ricette)": "📝", "Assunzioni registrate": "✅", "Visite, esami e referti": "🩺",
              "Vaccinazioni": "💉", "Documenti": "📁"}


# ---------------------------------------------------------------------------------------------------------------------
# Pezzi di servizio
# ---------------------------------------------------------------------------------------------------------------------
def inv_segreto(nome):
    """Un valore dei Secrets di Streamlit (vuoto se non c'è)."""
    try:
        return str(st.secrets.get(nome, "") or "").strip()
    except Exception:
        return ""


def _pdf_txt(s):
    s = "" if s is None else str(s)
    return s.replace("\u00a0", " ").encode("cp1252", "ignore").decode("cp1252")


def inv_mime(nome):
    return _MIME.get(str(nome).rsplit(".", 1)[-1].lower(), "application/octet-stream")


def inv_solo_cifre(numero):
    c = re.sub(r"\D", "", str(numero or ""))
    return c[2:] if c.startswith("00") else c


def inv_link_whatsapp(numero, testo):
    base = "https://wa.me/" + inv_solo_cifre(numero) if inv_solo_cifre(numero) else "https://wa.me/"
    return f"{base}?text={quote(testo[:2500])}"


def inv_link_sms(numero, testo):
    return f"sms:{inv_solo_cifre(numero)}?&body={quote(testo[:450])}"


def inv_link_mailto(a, oggetto, testo):
    return f"mailto:{quote(a or '')}?subject={quote(oggetto)}&body={quote(testo[:1500])}"


# ---------------------------------------------------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------------------------------------------------
def inv_pdf(titolo, sottotitolo, pagine, nota=""):
    """Un PDF (A4 in orizzontale) dalle pagine di fam_pagine(). Ritorna i byte, oppure None se manca la libreria reportlab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception:
        return None
    buf = io.BytesIO()
    pag = landscape(A4)
    doc = SimpleDocTemplate(buf, pagesize=pag, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=15 * mm,
                            title=_pdf_txt(titolo), author="VitaMemo")
    stili = getSampleStyleSheet()
    verde, rosso, grigio = colors.HexColor("#0f766e"), colors.HexColor("#b71c1c"), colors.HexColor("#666666")
    s_t = ParagraphStyle("t", parent=stili["Title"], fontName="Helvetica-Bold", fontSize=18, textColor=verde, alignment=0)
    s_h = ParagraphStyle("h", parent=stili["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=rosso, spaceBefore=4, spaceAfter=4)
    s_h3 = ParagraphStyle("h3", parent=stili["Heading3"], fontName="Helvetica-Bold", fontSize=10, spaceBefore=8, spaceAfter=3)
    s_p = ParagraphStyle("p", parent=stili["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11)
    s_c = ParagraphStyle("c", parent=s_p, fontSize=7.4, leading=9)
    s_ch = ParagraphStyle("ch", parent=s_c, fontName="Helvetica-Bold", textColor=colors.white)
    s_v = ParagraphStyle("v", parent=s_p, textColor=grigio, fontSize=8)

    def P(testo, stile, taglia=700):
        t = _pdf_txt(testo)
        t = t if len(t) <= taglia else t[:taglia - 1] + "…".encode("cp1252").decode("cp1252")
        return Paragraph(html.escape(t).replace("\n", "<br/>"), stile)
    storia = [P(titolo, s_t), P(sottotitolo, s_v), Spacer(1, 4 * mm)]
    for n, pg in enumerate(pagine):
        if n:
            storia.append(PageBreak())
        storia.append(P(pg["titolo"], s_h))
        for riga in pg.get("intro", []):
            storia += [P(riga, s_p, 900), Spacer(1, 1.5 * mm)]
        for t_, intest, righe in pg["tabelle"]:
            storia.append(P(t_, s_h3))
            if righe and intest and intest[0] == "N°":
                storia.append(P("Per chiedere dei documenti basta indicare il loro N° (per esempio: «portami il 4, il 12 e il 17»).", s_v))
            if not righe:
                storia.append(P("Nessun dato inserito.", s_v))
                continue
            pesi = [max(len(_pdf_txt(h)), min(32, max(len(_pdf_txt(r[i])) if i < len(r) else 0 for r in righe))) + 3 for i, h in enumerate(intest)]
            larg = [doc.width * p_ / sum(pesi) for p_ in pesi]
            # nessuna parola spezzata: ogni colonna è larga almeno quanto la sua parola più lunga (le DATE restano su una riga: «22/03/2017»)
            try:
                from reportlab.pdfbase.pdfmetrics import stringWidth
                minimi = []
                for i, h in enumerate(intest):
                    parole = [w for r in righe if i < len(r) for w in _pdf_txt(r[i]).split()] + _pdf_txt(h).split()
                    lw = max([stringWidth(w, "Helvetica", 7.4) for w in parole[:4000]] + [stringWidth(w, "Helvetica-Bold", 7.4) for w in _pdf_txt(h).split()] + [8])
                    minimi.append(min(lw + 8, doc.width * .22))
                for _giro in range(4):
                    sotto = [i for i in range(len(larg)) if larg[i] < minimi[i]]
                    if not sotto:
                        break
                    manca = sum(minimi[i] - larg[i] for i in sotto)
                    for i in sotto:
                        larg[i] = minimi[i]
                    altri = [i for i in range(len(larg)) if i not in sotto and larg[i] > minimi[i]]
                    margine = sum(larg[i] - minimi[i] for i in altri)
                    if margine <= 0:
                        break
                    for i in altri:
                        larg[i] -= manca * (larg[i] - minimi[i]) / margine
                tot = sum(larg)
                larg = [w * doc.width / tot for w in larg]
            except Exception:
                pass
            s_n = ParagraphStyle("n", parent=s_c, fontName="Helvetica-Bold", fontSize=9, leading=11)
            dati = [[P(h, s_ch) for h in intest]] + [[P(r[i] if i < len(r) else "", s_n if (i == 0 and intest[0] == "N°") else s_c) for i in range(len(intest))] for r in righe]
            tab = Table(dati, colWidths=larg, repeatRows=1)
            tab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), verde), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#999999")),
                                     ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f7f6")]),
                                     ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                                     ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            storia.append(tab)
    if nota:
        storia += [Spacer(1, 6 * mm), P(nota, s_v, 900)]

    def _piede(c, d):
        c.saveState()
        c.setFont("Helvetica", 7.5)
        c.setFillColor(grigio)
        c.drawString(doc.leftMargin, 8 * mm, "VitaMemo - contiene dati personali")
        c.drawRightString(pag[0] - doc.rightMargin, 8 * mm, f"Pagina {d.page}")
        c.restoreState()
    doc.build(storia, onFirstPage=_piede, onLaterPages=_piede)
    return buf.getvalue()


def inv_testo(titolo, pagine, max_righe=10):
    """Il riepilogo scritto (per WhatsApp, SMS, email, copia): per ogni persona le voci principali."""
    righe = [titolo, ""]
    for pg in pagine:
        righe.append(f"👤 {pg['titolo']}")
        for intro in pg.get("intro", [])[:2]:
            righe.append("   " + (intro if len(intro) <= 160 else intro[:157] + "…"))
        for t_, intest, dati in pg["tabelle"]:
            if not dati:
                continue
            righe.append(f"{_EMOJI_SEZ.get(t_, '▪️')} {t_} ({len(dati)})")
            for r in dati[:max_righe]:
                celle = [str(c) for c in r if str(c).strip()][:4]
                righe.append("  • " + " · ".join(c if len(c) <= 48 else c[:45] + "…" for c in celle))
            if len(dati) > max_righe:
                righe.append(f"  …e altre {len(dati) - max_righe}")
        righe.append("")
    return "\n".join(righe).strip()


# ---------------------------------------------------------------------------------------------------------------------
# Invio: email, Telegram
# ---------------------------------------------------------------------------------------------------------------------
def inv_email_pronta():
    return bool(inv_segreto("EMAIL_USER") and inv_segreto("EMAIL_PASSWORD"))


def inv_indirizzi(testo):
    """Gli indirizzi email scritti (separati da virgola, punto e virgola o spazio). Ritorna (validi, non validi)."""
    parti = [x.strip() for x in re.split(r"[,\s;]+", testo or "") if x.strip()]
    ok = [x for x in parti if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", x)]
    return ok, [x for x in parti if x not in ok]


def inv_invia_email(destinatari, oggetto, testo, allegati):
    """Manda l'email con gli allegati. allegati = [(nome, mime, byte)]. Ritorna (True, '') oppure (False, motivo)."""
    utente, password = inv_segreto("EMAIL_USER"), inv_segreto("EMAIL_PASSWORD").replace(" ", "")      # Google mostra il codice a gruppi di 4: gli spazi non servono
    if not (utente and password):
        return False, "mancano EMAIL_USER o EMAIL_PASSWORD nei Secrets"
    if sum(len(a[2]) for a in allegati) > _MAX_ALLEGATI:
        return False, "gli allegati sono troppo grandi per una email: scegline meno"
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = utente, ", ".join(destinatari), oggetto
    msg.set_content(testo + "\n\n—\nInviato dall'app «VitaMemo». Contiene dati personali: non inoltrarlo a chi non deve vederlo.")
    for nome, mime, dati in allegati:
        tipo, sotto = (mime or "application/octet-stream").split("/", 1)
        msg.add_attachment(dati, maintype=tipo, subtype=sotto, filename=nome)
    try:
        with smtplib.SMTP_SSL(inv_segreto("EMAIL_SMTP") or "smtp.gmail.com", int(inv_segreto("EMAIL_PORT") or 465), timeout=40) as s:
            s.login(utente, password)
            s.send_message(msg)
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:160]}"
    return True, ""


def inv_invia_telegram(chat_id, testo, allegati):
    """Manda riepilogo e file nella chat Telegram con il bot. Ritorna (True, '') oppure (False, motivo)."""
    import requests as _rq
    token = inv_segreto("TELEGRAM_TOKEN")
    if not token:
        return False, "manca TELEGRAM_TOKEN nei Secrets"
    base = f"https://api.telegram.org/bot{token}"
    try:
        r = _rq.post(base + "/sendMessage", data={"chat_id": chat_id, "text": testo[:4000]}, timeout=25)
        if not r.json().get("ok"):
            return False, str(r.json().get("description", "errore"))[:160]
        for nome, mime, dati in allegati:
            r = _rq.post(base + "/sendDocument", data={"chat_id": chat_id}, files={"document": (nome, dati, mime)}, timeout=60)
            if not r.json().get("ok"):
                return False, str(r.json().get("description", "errore"))[:160]
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:160]}"
    return True, ""


# ---------------------------------------------------------------------------------------------------------------------
# «Condividi»: la finestra di condivisione del telefono (Web Share), con i file allegati
# ---------------------------------------------------------------------------------------------------------------------
_JS_INVIO = r"""
(function () {
  var w = window, d = w.document;
  try {
    if (w.__invioAttivo) return;
    w.__invioAttivo = true;
    var MSG = __MSG__;
    function avviso(t) {
      var el = d.getElementById('invio-avviso');
      if (!el) {
        el = d.createElement('div'); el.id = 'invio-avviso';
        el.style.cssText = 'position:fixed;left:50%;top:78px;transform:translateX(-50%);max-width:92vw;background:#14302b;color:#fff;padding:10px 16px;' +
          'border-radius:16px;font:600 14px/1.3 sans-serif;z-index:100002;text-align:center;box-shadow:0 8px 24px rgba(0,0,0,.35)';
        d.body.appendChild(el);
      }
      el.textContent = t; el.style.display = 'block';
      w.clearTimeout(el.__t); el.__t = w.setTimeout(function () { el.style.display = 'none'; }, 6000);
    }
    /* una riga di stato sotto i pulsanti «Condividi»: dice se questo browser può condividere le foto e cosa è successo toccando */
    function nomeBrowser() {
      var ua = w.navigator.userAgent || '', m, nome = '';
      if (/FBAN|FBAV|Instagram|MicroMessenger|WhatsApp|Telegram|Line\//.test(ua)) nome = 'un browser dentro un\'altra app';
      else if ((m = ua.match(/(SamsungBrowser|EdgA|OPR|Firefox|FxiOS|CriOS)\/([\d]+)/))) nome = m[1].replace('SamsungBrowser', 'Samsung Internet').replace('EdgA', 'Edge').replace('OPR', 'Opera').replace('CriOS', 'Chrome').replace('FxiOS', 'Firefox') + ' ' + m[2];
      else if ((m = ua.match(/Chrome\/([\d]+)/))) nome = 'Chrome ' + m[1];
      else if (/Safari/.test(ua)) nome = 'Safari';
      return nome || 'browser sconosciuto';
    }
    function capacita() {
      var f = null, files = false;
      try { f = new w.File([new Uint8Array([1])], 'prova.jpg', {type: 'image/jpeg'}); } catch (x) {}
      try { files = !!(w.navigator.canShare && f && w.navigator.canShare({files: [f]})); } catch (x) {}
      return {share: !!w.navigator.share, files: files};
    }
    function stato(testo, tipo, tutti) {
      var els = d.querySelectorAll('.inv-diag');
      for (var i = 0; i < els.length; i++) {
        els[i].textContent = testo; els[i].setAttribute('data-ok', '1');
        els[i].style.color = tipo === 'ko' ? '#b71c1c' : (tipo === 'ok' ? '#1b5e20' : '#455a64');
      }
    }
    function diagnosi() {
      var els = d.querySelectorAll('.inv-diag:not([data-ok])'); if (!els.length) return;
      var c = capacita(), b = nomeBrowser(), t, tipo;
      if (!c.share) { t = '⚠️ ' + MSG.diag_no + ' (' + b + ')'; tipo = 'ko'; }
      else if (!c.files) { t = '⚠️ ' + MSG.diag_nofile + ' (' + b + ')'; tipo = 'ko'; }
      else { t = '✅ ' + MSG.diag_ok + ' (' + b + ')'; tipo = 'ok'; }
      for (var i = 0; i < els.length; i++) { els[i].textContent = t; els[i].setAttribute('data-ok', '1'); els[i].style.color = tipo === 'ko' ? '#b71c1c' : '#1b5e20'; }
    }
    diagnosi();
    var attesaDiag = null;
    new w.MutationObserver(function () { if (attesaDiag) return; attesaDiag = w.setTimeout(function () { attesaDiag = null; diagnosi(); }, 400); }).observe(d.body, {childList: true, subtree: true});
    function aFile(f) {
      var b = w.atob(f.b64), a = new Uint8Array(b.length);
      for (var i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
      return new w.File([a], f.nome, {type: f.mime});
    }
    d.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[class*="st-key-invio_share_"] button') : null;
      if (!b) return;
      var c = b.closest('[class*="st-key-invio_share_"]');
      var m = (c.className || '').match(/st-key-invio_share_(\S+)/);
      var P = m && w.__invioDati && (w.__invioDati[m[1]] || w.__invioDati[m[1].replace(/__\w+$/, '')]);
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
      if (!P) { avviso(MSG.nondati); stato('⚠️ ' + MSG.nondati, 'ko'); return; }
      if (!w.navigator.share) { avviso(MSG.nonsupp); stato('⚠️ ' + MSG.nonsupp, 'ko'); return; }
      var files = [];
      try { files = (P.files || []).map(aFile); } catch (x) {}
      if (w.navigator.canShare) files = files.filter(function (f) { try { return w.navigator.canShare({files: [f]}); } catch (x) { return false; } });
      var dati = {title: P.titolo, text: P.testo};
      if (files.length) dati.files = files; else if ((P.files || []).length) { avviso(MSG.solotesto); stato('⚠️ ' + MSG.solotesto, 'ko'); }
      else stato('⏳ ' + MSG.apro, 'info');
      if (files.length) stato('⏳ ' + MSG.apro + ' (' + files.length + ' ' + (files.length === 1 ? 'file' : 'file') + ')', 'info');
      var soloTesto = !files.length && (P.files || []).length > 0;
      w.navigator.share(dati).then(function () { if (soloTesto) stato('⚠️ ' + MSG.solotesto, 'ko'); else stato('✅ ' + MSG.fatto, 'ok'); }).catch(function (err) {
        if (err && err.name === 'AbortError') { stato('Annullato: puoi riprovare.', 'info'); return; }
        avviso(MSG.errore); stato('⚠️ ' + MSG.errore + ' [' + ((err && err.name) || 'errore') + ']', 'ko');
      });
    }, true);
  } catch (err) { /* resta la scelta di scaricare i file */ }
})();
"""

_MSG_JS = {"nondati": "Prima tocca «Prepara» così i file sono pronti da condividere.",
           "nonsupp": "Questo browser non ha la finestra «Condividi»: usa Email, WhatsApp o scarica il file.",
           "solotesto": "Questi file non si possono condividere da qui: mando solo il riepilogo. Per i file usa Email o scarica.",
           "errore": "Non sono riuscito ad aprire «Condividi». Prova con Email o scarica il file.",
           "apro": "Apro «Condividi»…", "fatto": "Fatto: controlla l'app che hai scelto.",
           "diag_ok": "Pronto: toccando il pulsante si apre «Condividi» con le foto",
           "diag_no": "Questo browser non ha «Condividi»: usa Chrome, oppure scarica le foto qui sotto e allegale in WhatsApp con la graffetta 📎",
           "diag_nofile": "Questo browser non può condividere le foto: usa Chrome, oppure scarica le foto qui sotto e allegale in WhatsApp con la graffetta 📎"}


def _inv_pagina_js(codice):
    """Inserisce un pezzo di JavaScript nella pagina vera (lo stesso metodo di voce.py e fotocamera.py)."""
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\\\"stApp\\\"],.stApp,[data-testid=\\\"stAppViewContainer\\\"]')}catch(e){return false}}"
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
            import streamlit.components.v1 as _comp_inv
            _comp_inv.html(pagina, height=0)
    except Exception:
        pass


def inv_registra_condivisione(chiave, titolo, testo, allegati):
    """Prepara nella pagina i file da condividere (si usano quando si tocca «Condividi»)."""
    if not st.session_state.get("_inv_js"):
        st.session_state["_inv_js"] = True
        _inv_pagina_js(_JS_INVIO.replace("__MSG__", json.dumps(_MSG_JS, ensure_ascii=False)))
    files = []
    if sum(len(a[2]) for a in allegati) <= _MAX_CONDIVISIONE:
        files = [{"nome": n, "mime": m, "b64": base64.b64encode(d).decode()} for n, m, d in allegati]
    dati = {"titolo": titolo, "testo": testo[:3000], "files": files}
    _inv_pagina_js("(function(){var w=window;w.__invioDati=w.__invioDati||{};w.__invioDati[" + json.dumps(chiave) + "]=" + json.dumps(dati) + ";})();")


# ---------------------------------------------------------------------------------------------------------------------
# I canali, in una finestra a schede
# ---------------------------------------------------------------------------------------------------------------------
def _inv_alterna(chiave):
    st.session_state[chiave] = not st.session_state.get(chiave, False)


def _inv_dati_conto():
    try:
        return carica_dati(crea_archivio(), percorso_mio())
    except Exception:
        return {}


def _inv_senza_doppioni(allegati):
    """Toglie i file identici (stesso contenuto): capita che la stessa foto sia stata salvata due volte. Ritorna (elenco, quanti tolti)."""
    import hashlib
    visti, risultato = set(), []
    for nome, mime, dati in allegati:
        impronta = hashlib.sha256(dati).hexdigest()
        if impronta in visti:
            continue
        visti.add(impronta)
        risultato.append((nome, mime, dati))
    return risultato, len(allegati) - len(risultato)


def _inv_converti_immagini(allegati):
    """Le foto salvate nell'app sono in formato WebP: WhatsApp e altre app non le accettano sempre. Per l'invio diventano JPEG
    (le parti trasparenti, dove è stato tolto lo sfondo, diventano bianche)."""
    risultato = []
    for nome, mime, dati in allegati:
        if mime == "image/webp" or nome.lower().endswith(".webp"):
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(dati))
                if im.mode in ("RGBA", "LA") or "transparency" in im.info:
                    fondo = Image.new("RGB", im.size, (255, 255, 255))
                    fondo.paste(im.convert("RGBA"), mask=im.convert("RGBA").getchannel("A"))
                    im = fondo
                buf = io.BytesIO()
                im.convert("RGB").save(buf, "JPEG", quality=92, optimize=True)
                risultato.append((nome.rsplit(".", 1)[0] + ".jpg", "image/jpeg", buf.getvalue()))
                continue
            except Exception:
                pass
        risultato.append((nome, mime, dati))
    return risultato


def _inv_nomi_unici(allegati):
    """Se due file hanno lo stesso nome (succede: per esempio fronte e retro scattati dal telefono), il secondo diventa «nome (2)», il terzo «nome (3)»…
    Servono nomi diversi per le caselle, per i pulsanti di scarico e per gli allegati dell'email."""
    usati, risultato = set(), []
    for nome, mime, dati in allegati:
        base, punto, est = nome.rpartition(".")
        if not punto:
            base, est = nome, ""
        candidato, n = nome, 1
        while candidato in usati:
            n += 1
            candidato = f"{base} ({n})" + (f".{est}" if est else "")
        usati.add(candidato)
        risultato.append((candidato, mime, dati))
    return risultato


_INV_CSS_PULSA = ("<style>@keyframes invg-pulsa{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(38,198,218,.75)}50%{transform:scale(1.025);box-shadow:0 0 0 10px rgba(38,198,218,0)}}"
                  "div[class*='st-key-invg_'] button[kind='primary'],div[class*='st-key-invg_'] a[kind='primary'],div[class*='st-key-invg_'] [data-testid='stBaseButton-primary'],"
                  "div[class*='st-key-invg_'] [data-testid='stBaseLinkButton-primary']{animation:invg-pulsa 1.5s ease-in-out infinite !important}"
                  ".invg-fai{font-weight:800;font-size:.9rem;margin:6px 0 2px;opacity:.95}"
                  "@media (prefers-reduced-motion:reduce){div[class*='st-key-invg_'] button,div[class*='st-key-invg_'] a{animation:none !important}}</style>")
_INV_NUM = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]


def inv_dispositivo():
    """«telefono» oppure «computer»: lo si capisce da solo dal programma con cui stai usando l'app."""
    try:
        ua = str(st.context.headers.get("User-Agent", ""))
    except Exception:
        ua = ""
    return "telefono" if re.search(r"Mobi|Android|iPhone|iPad|iPod", ua, re.I) else "computer"


def _inv_base_nome(titolo):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(titolo or "")).encode("ascii", "ignore").decode()
    return (re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_") or "VitaMemo")[:50]


def inv_pdf_unico(titolo, testo, allegati):
    """Un solo PDF: una pagina col riepilogo scritto, poi tutte le foto (una per pagina) e le pagine dei PDF. None se non si riesce o se c'è un file che non si può mettere in un PDF."""
    try:
        try:
            import pymupdf as mu
        except Exception:
            import fitz as mu
        doc = mu.open()
        if (testo or "").strip():
            righe = []
            for riga in ((titolo or "") + "\n\n" + testo).split("\n"):
                while len(riga) > 92:
                    taglio = riga.rfind(" ", 0, 92)
                    taglio = taglio if taglio > 40 else 92
                    righe.append(riga[:taglio])
                    riga = riga[taglio:].lstrip()
                righe.append(riga)
            for i in range(0, len(righe), 58):
                pg = doc.new_page(width=595, height=842)
                try:
                    pg.insert_text((40, 56), "\n".join(_pdf_txt(r) for r in righe[i:i + 58]), fontsize=10, fontname="helv", lineheight=1.3)
                except TypeError:
                    pg.insert_text((40, 56), "\n".join(_pdf_txt(r) for r in righe[i:i + 58]), fontsize=10, fontname="helv")
        for nome, mime, dati in allegati:
            est = nome.lower().rsplit(".", 1)[-1]
            if mime == "application/pdf" or est == "pdf":
                src = mu.open(stream=dati, filetype="pdf")
                doc.insert_pdf(src)
                src.close()
            elif str(mime).startswith("image/") or est in ("jpg", "jpeg", "png", "webp", "gif", "bmp"):
                from PIL import Image, ImageOps
                im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
                im.thumbnail((2000, 2000))
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=88)
                lw, lh = (595, 842) if im.height >= im.width else (842, 595)
                pg = doc.new_page(width=lw, height=lh)
                s_ = min((lw - 40) / im.width, (lh - 40) / im.height)
                w_, h_ = im.width * s_, im.height * s_
                pg.insert_image(mu.Rect((lw - w_) / 2, (lh - h_) / 2, (lw + w_) / 2, (lh + h_) / 2), stream=buf.getvalue())
            else:
                doc.close()
                return None
        if doc.page_count == 0:
            doc.close()
            return None
        out = doc.tobytes(deflate=True, garbage=3)
        doc.close()
        return out
    except Exception:
        return None


def inv_zip(testo, allegati):
    """Un solo file ZIP con tutti i file e, se c'è, il riepilogo scritto."""
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if (testo or "").strip():
            z.writestr("Riepilogo.txt", testo)
        for nome, _mime, dati in allegati:
            z.writestr(nome, dati)
    return buf.getvalue()


def _inv_si_puo_pdf(allegati):
    return all(m == "application/pdf" or str(m).startswith("image/") or n.lower().rsplit(".", 1)[-1] in ("pdf", "jpg", "jpeg", "png", "webp", "gif", "bmp") for n, m, _d in allegati)


def _inv_in_forma(chiave, forma, titolo, testo, allegati):
    """I file nella forma scelta (PDF unico, ZIP, oppure così come sono). Il lavoro si fa una volta sola e si tiene da parte."""
    import hashlib
    if forma == "come":
        return allegati, None
    firma = hashlib.md5((forma + "|" + titolo + "|" + str(len(testo or "")) + "|" + "|".join(f"{n}:{len(d)}" for n, _m, d in allegati)).encode("utf-8")).hexdigest()
    mem = st.session_state.get(f"inv_forma_mem_{chiave}")
    if mem and mem[0] == firma:
        return mem[1], mem[2]
    base = _inv_base_nome(titolo) + "_" + oggi().isoformat()
    avviso, pronti = None, allegati
    if forma == "pdf":
        pdf = inv_pdf_unico(titolo, testo, allegati)
        if pdf:
            pronti = [(base + ".pdf", "application/pdf", pdf)]
        else:
            avviso = "Non sono riuscito a unire tutto in un solo PDF: ti lascio i file così come sono."
    elif forma == "zip":
        pronti = [(base + ".zip", "application/zip", inv_zip(testo, allegati))]
    st.session_state[f"inv_forma_mem_{chiave}"] = (firma, pronti, avviso)
    return pronti, avviso


def inv_canali(chiave, titolo, testo, allegati, oggetto=None, passo=1, forma_fissa=False, prima="invia"):
    """Il percorso unico per scaricare o inviare, a passi numerati: in che forma (PDF, ZIP, così come sono) → cosa fare (scaricare qui / inviare) → con cosa e a chi.
    allegati = [(nome, mime, byte)]; testo = il riepilogo scritto. passo = da che numero partire (se prima ci sono già altri passi); forma_fissa = la forma è già stata scelta prima."""
    oggetto = oggetto or titolo
    allegati, doppi = _inv_senza_doppioni(list(allegati))
    allegati = _inv_nomi_unici(_inv_converti_immagini(allegati))
    chiave = re.sub(r"\W+", "_", str(chiave))                     # le chiavi dei pulsanti finiscono nei nomi di classe della pagina
    d_conto = _inv_dati_conto()
    disp = inv_dispositivo()
    num = lambda: _INV_NUM[min(passo - 1, len(_INV_NUM) - 1)]
    if doppi:
        st.info(f"ℹ️ C'erano {doppi} file identici (la stessa foto salvata più volte): li tengo una volta sola.")

    # ---- in che forma
    if not allegati:                                               # solo testo: per scaricarlo diventa un PDF (e resta il testo da copiare)
        pdf_testo = inv_pdf_unico(titolo, testo, []) if (testo or "").strip() else None
        da_scaricare = ([(_inv_base_nome(titolo) + ".pdf", "application/pdf", pdf_testo)] if pdf_testo else []) + \
                       ([(_inv_base_nome(titolo) + ".txt", "text/plain", (testo or "").encode("utf-8"))] if (testo or "").strip() else [])
        pronti = []
    else:
        forme = ["come"]
        if not forma_fissa:
            if _inv_si_puo_pdf(allegati) and not (len(allegati) == 1 and allegati[0][1] == "application/pdf"):
                forme.append("pdf")
            if len(allegati) > 1:
                forme.append("zip")
        forma = "come"
        if len(forme) > 1:
            n_f = len(allegati)
            nomi_forme = {"come": f"📎 Così come {'è' if n_f == 1 else 'sono'} ({n_f} file)" if n_f > 1 else "📎 Così com'è (la foto)",
                          "pdf": "📄 In un solo PDF (comodo da leggere e stampare)", "zip": "🗜️ In un solo ZIP (un pacchetto con tutti i file)"}
            st.markdown(f"**{num()} In che forma lo vuoi?**")
            forma = st.radio("In che forma lo vuoi?", forme, format_func=lambda k: nomi_forme[k], index=(forme.index("pdf") if "pdf" in forme and n_f > 1 else 0),
                             key=f"inv_forma_{chiave}", label_visibility="collapsed")
            passo += 1
        pronti, avviso = _inv_in_forma(chiave, forma, titolo, testo, allegati)
        if avviso:
            st.warning(avviso)
        da_scaricare = pronti

    # ---- cosa fare
    st.markdown(f"**{num()} Cosa vuoi fare?**")
    azioni = {"scarica": f"⬇️ Scaricarlo su questo {disp}", "invia": "📤 Inviarlo a qualcuno"}
    azione = st.radio("Cosa vuoi fare?", list(azioni), format_func=lambda k: azioni[k], index=(1 if prima == "invia" else 0), key=f"inv_az_{chiave}", label_visibility="collapsed")   # dal tasto «Invia» è già scelto «inviare»
    passo += 1

    if azione == "scarica":
        if not da_scaricare:
            st.caption("Non c'è niente da scaricare.")
        for i, (nome, mime, dati) in enumerate(da_scaricare):
            st.download_button(f"⬇️ Scarica {nome} ({max(1, len(dati) // 1024)} KB)", dati, file_name=nome, mime=mime, key=f"inv_dl_{chiave}_{i}", width="stretch",
                               type="primary" if i == 0 else "secondary")
        if da_scaricare:
            st.caption(f"Dopo il tocco lo trovi nella cartella **Download** del {disp}" + (" (o nelle notifiche in alto)." if disp == "telefono" else "."))
        return

    # ---- con cosa e a chi
    st.warning("🔒 Stai per inviare **dati personali**: controlla bene a chi li mandi.")
    ha_file = bool(pronti)

    def _azione(canale):
        """Il campo «a chi» e il pulsante per inviare: stanno DENTRO il riquadro della voce scelta (non in fondo alla pagina)."""
        st.markdown("<div class='invg-fai'>👇 " + ("Scrivi a chi e invia" if canale in ("email", "wa", "sms") else "Tocca per inviare") + "</div>", unsafe_allow_html=True)
        if canale == "app":
            st.caption("Si apre la finestra **Condividi**: scegli l'app (WhatsApp, Gmail, Telegram, Drive…) e poi la persona. " + ("I file sono già allegati." if ha_file else ""))
            inv_registra_condivisione(chiave, titolo, testo, pronti)
            with st.container(key=f"invio_share_{chiave}"):
                st.button("📤 Invia adesso: scegli WhatsApp, Gmail…", key=f"invio_btn_share_{chiave}", type="primary", width="stretch")
            st.markdown("<div class='inv-diag' style='font-size:.82rem;margin:2px 0 6px'></div>", unsafe_allow_html=True)
            if ha_file:
                st.caption("Se non si apre: torna al passo «Cosa vuoi fare?», scegli **Scaricarlo** e poi allegalo a mano nell'app con la graffetta 📎.")
        elif canale == "email":
            if not inv_email_pronta():
                st.info("L'app non ha ancora una casella per spedire da sola (servono EMAIL_USER ed EMAIL_PASSWORD nei Secrets di Streamlit: la guida «Invio» spiega come). "
                        "Intanto si apre **la tua posta** con il testo già scritto" + ("; i file allegali dopo averli scaricati." if ha_file else "."))
                a = st.text_input("Indirizzo email di chi lo riceve (facoltativo)", key=f"inv_a_{chiave}")
                st.link_button("✉️ Apri la mia posta", inv_link_mailto(a.strip(), oggetto, testo), width="stretch", type="primary")
            else:
                a = st.text_input("Indirizzo email di chi lo riceve (più indirizzi: separali con la virgola)", value=d_conto.get("avviso_email", ""), key=f"inv_a_{chiave}")
                msg = st.text_area("Messaggio", value="Ti mando in allegato i documenti. " if ha_file else "Ecco il riepilogo.", key=f"inv_m_{chiave}", height=80)
                scelti = [x for i, x in enumerate(pronti) if st.checkbox(f"📎 {x[0]} ({len(x[2]) // 1024} KB)", value=True, key=f"inv_c_{chiave}_{i}")]
                if sum(len(x[2]) for x in scelti) > _MAX_ALLEGATI:
                    st.warning("I file scelti sono troppo pesanti per una sola email: togline qualcuno, oppure scaricali e mandali con un servizio per file grandi.")
                if st.button("✉️ Invia l'email", type="primary", key=f"inv_si_{chiave}", width="stretch"):
                    ok, ko = inv_indirizzi(a)
                    if not ok:
                        st.error("Scrivi un indirizzo email valido.")
                    elif ko:
                        st.error("Indirizzo non valido: " + ", ".join(ko))
                    elif len(ok) > 5:
                        st.error("Al massimo 5 indirizzi per volta.")
                    elif st.session_state.get("inv_n_email", 0) >= 20:
                        st.error("Hai già mandato molte email in questa sessione: riapri l'app per continuare.")
                    else:
                        with st.spinner("Invio in corso…"):
                            esito, motivo = inv_invia_email(ok, oggetto, (msg.strip() + "\n\n" + testo)[:20000], scelti)
                        if esito:
                            st.session_state["inv_n_email"] = st.session_state.get("inv_n_email", 0) + 1
                            st.success("✅ Email inviata a " + ", ".join(ok))
                        else:
                            st.error("Non sono riuscito a inviarla: " + motivo)
        elif canale == "wa":
            num_wa = st.text_input("Numero di chi lo riceve (facoltativo: con prefisso, senza +, es. 39333…)", key=f"inv_wa_{chiave}")
            st.link_button("💬 Apri WhatsApp con il testo", inv_link_whatsapp(num_wa, testo), width="stretch", type="primary")
            st.caption("Senza numero, WhatsApp ti fa scegliere la persona." + (" Va solo il testo: per mandare anche il file scegli «WhatsApp, Telegram, Gmail…» nel riquadro verde." if ha_file else ""))
        elif canale == "tg":
            chat = str(d_conto.get("telegram_chat_id") or "").strip()
            if not inv_segreto("TELEGRAM_TOKEN"):
                st.info("Per mandare i file nella tua chat Telegram serve TELEGRAM_TOKEN nei Secrets di Streamlit (lo stesso del bot): la guida «Invio» spiega come. "
                        "Intanto scegli «WhatsApp, Telegram, Gmail o un'altra app» e poi Telegram.")
            elif not chat:
                st.info("Manca il tuo Chat ID: inseriscilo in «Scegli come ricevere gli avvisi» in Salute, poi torna qui.")
            else:
                st.caption("Testo e file arrivano nella **tua** chat con il bot dell'app: da lì li inoltri a chi vuoi.")
                if st.button("✈️ Mandami tutto su Telegram", type="primary", key=f"inv_tg_{chiave}", width="stretch"):
                    with st.spinner("Invio in corso…"):
                        esito, motivo = inv_invia_telegram(chat, testo, pronti)
                    st.success("✅ Inviato: guarda Telegram.") if esito else st.error("Non sono riuscito a inviarlo: " + motivo)
        elif canale == "sms":
            num2 = st.text_input("Numero di chi lo riceve (facoltativo)", key=f"inv_sms_{chiave}")
            st.link_button("📱 Apri i messaggi con il testo", inv_link_sms(num2, testo), width="stretch", type="primary")
            st.caption("Gli SMS sono brevi: va solo l'inizio del testo.")
        else:
            st.caption("Tocca l'icona in alto a destra del riquadro per copiare, poi incolla dove vuoi.")
            st.code(testo, language=None, wrap_lines=True)
    st.markdown(f"**{num()} Con cosa lo mandi?**")
    passo += 1
    k_f, k_t = f"inv_canf_{chiave}", f"inv_cant_{chiave}"
    testo_g = {"wa": "💬 WhatsApp", "sms": "📱 SMS (solo l'inizio del testo)", "copia": "📋 Copiare il testo"}
    if ha_file:                                                   # due riquadri: CON IL FILE (verde, consigliato) e SOLO IL TESTO (arancione). Se ne sceglie uno solo fra tutti e due.
        nome_f = "il file" if len(pronti) == 1 else "i file"
        file_g = {"app": ("💬 WhatsApp, Telegram, Gmail o un'altra app" if disp == "telefono" else "📤 Un'altra app del computer (se il programma lo permette)"),
                  "email": "✉️ Email", "tg": "✈️ Telegram, nella mia chat"}
        if disp != "telefono":
            file_g = {"email": file_g["email"], "tg": file_g["tg"], "app": file_g["app"]}
        if not inv_email_pronta():                                # senza la casella dell'app l'email porta solo il testo
            testo_g = {"wa": testo_g["wa"], "email": "✉️ Email (si apre la tua posta)", "sms": testo_g["sms"], "copia": testo_g["copia"]}
            file_g.pop("email")
        if st.session_state.get(k_f) not in file_g and st.session_state.get(k_t) not in testo_g:
            st.session_state[k_f], st.session_state[k_t] = next(iter(file_g)), None
        st.markdown("<style>div[class*='st-key-invg_file_']{border:2px solid #2ecc71 !important;border-radius:16px !important;background:rgba(46,204,113,.09) !important;padding:10px 12px !important}"
                    "div[class*='st-key-invg_testo_']{border:2px solid #f5a623 !important;border-radius:16px !important;background:rgba(245,166,35,.08) !important;padding:10px 12px !important}"
                    ".invg-t{font-weight:800;font-size:.95rem;margin:0 0 2px}.invg-t.f{color:#57e39a}.invg-t.t{color:#ffc061}</style>" + _INV_CSS_PULSA, unsafe_allow_html=True)

        def _scelto(questo, altro):
            if st.session_state.get(questo) is not None:
                st.session_state[altro] = None
        with st.container(key=f"invg_file_{chiave}"):
            st.markdown(f"<div class='invg-t f'>📎 CON {nome_f.upper()} · consigliato</div>", unsafe_allow_html=True)
            st.radio("Con il file", list(file_g), format_func=lambda k: file_g[k], index=None, key=k_f, label_visibility="collapsed", on_change=_scelto, args=(k_f, k_t))
            if st.session_state.get(k_f) in file_g:
                _azione(st.session_state[k_f])
        with st.container(key=f"invg_testo_{chiave}"):
            st.markdown("<div class='invg-t t'>✍️ SOLO IL TESTO · senza " + nome_f + "</div>", unsafe_allow_html=True)
            st.radio("Solo il testo", list(testo_g), format_func=lambda k: testo_g[k], index=None, key=k_t, label_visibility="collapsed", on_change=_scelto, args=(k_t, k_f))
            if st.session_state.get(k_t) in testo_g:
                _azione(st.session_state[k_t])
        if not (st.session_state.get(k_f) or st.session_state.get(k_t)):
            st.caption("Scegli una voce in uno dei due riquadri.")
    else:                                                         # non ci sono file: è tutto testo, un riquadro solo
        tutti = {"app": ("📤 WhatsApp, Telegram, Gmail o un'altra app" if disp == "telefono" else "📤 Un'altra app del computer"), "email": "✉️ Email", "wa": "💬 WhatsApp (a un numero)",
                 "tg": "✈️ Telegram, nella mia chat", "sms": testo_g["sms"], "copia": testo_g["copia"]}
        if disp != "telefono":
            tutti = {k: tutti[k] for k in ("email", "wa", "tg", "sms", "copia", "app")}
        st.markdown("<style>div[class*='st-key-invg_solo_']{border:2px solid #4aa3ff !important;border-radius:16px !important;background:rgba(74,163,255,.08) !important;padding:10px 12px !important}</style>"
                    + _INV_CSS_PULSA, unsafe_allow_html=True)
        with st.container(key=f"invg_solo_{chiave}"):
            canale = st.radio("Con cosa lo mandi?", list(tutti), format_func=lambda k: tutti[k], key=f"inv_can_{chiave}", label_visibility="collapsed")
            _azione(canale)

def inv_voce(chiave, etichetta, titolo, testo, carica_allegati):
    """Il tasto «Invia» di una singola voce (documento, medicinale, prescrizione, visita): apre i canali con i suoi file allegati."""
    k = f"inv_aperto_{chiave}"
    aperto = st.session_state.get(k, False)
    st.button("🙈 Chiudi l'invio" if aperto else etichetta, key=f"inv_tasto_{chiave}", width="stretch", on_click=_inv_alterna, args=(k,))
    if aperto:
        try:
            inv_canali(chiave, titolo, testo, list(carica_allegati()), oggetto=titolo)
        except Exception as e:
            st.error(f"Non riesco ad aprire l'invio ({type(e).__name__}). Chiudi e riprova; se capita ancora, scrivimelo.")


# ---------------------------------------------------------------------------------------------------------------------
# «Esporta e invia» di tutto: da Salute, dai Documenti e dal Controllo famiglia
# ---------------------------------------------------------------------------------------------------------------------
INV_EXTRA = ["Dispensa (prodotti)", "Lista della spesa"]


def _inv_extra_conto(d, scelte):
    """Dispensa e lista della spesa dell'account: (fogli, tabelle per il PDF/HTML)."""
    fogli, tabelle = [], []
    if "Dispensa (prodotti)" in scelte:
        intest = ["Prodotto", "Marca", "Per chi", "Quantità", "Scadenza", "Note"]
        righe = []
        for r in sorted(d.get("articoli", []), key=lambda r: r.get("scadenza") or "9999-12-31"):
            try:
                q = descrivi([r])
            except Exception:
                q = str(r.get("quantita", ""))
            righe.append([r.get("nome", ""), r.get("marca", ""), r.get("per_chi", ""), q, data_it(r["scadenza"]) if r.get("scadenza") else "", r.get("note", "")])
        fogli.append(("Dispensa (prodotti)", intest, righe))
        tabelle.append(("Dispensa (prodotti)", intest, righe))
    if "Lista della spesa" in scelte:
        intest = ["Prodotto", "Marca", "Per chi", "Stato"]
        righe = [[r.get("nome", ""), r.get("marca", ""), r.get("per_chi", ""), "preso" if r.get("preso") else "da comprare"] for r in d.get("spesa", [])]
        fogli.append(("Lista della spesa", intest, righe))
        tabelle.append(("Lista della spesa", intest, righe))
    return fogli, tabelle


def _inv_html_extra(tabelle):
    return "".join(_fa_tabella_html(t_, i_, r_) for t_, i_, r_ in tabelle) if tabelle else ""


def inv_prepara(chiave, persone, d_conto, scelte, formati, titolo_rep, oggi_):
    """Costruisce i file scelti e il riepilogo; li tiene da parte per i canali."""
    sez = [x for x in scelte if x in FAM_TITOLI or x == FAM_SCHEDA]
    fogli_extra, tabelle_extra = _inv_extra_conto(d_conto, scelte)
    pagine = fam_pagine(persone, sez) if sez else []
    if tabelle_extra:
        pagine = pagine + [{"titolo": "Dispensa e lista della spesa", "intro": [], "tabelle": tabelle_extra}]
    base = re.sub(r"[^A-Za-z0-9_]+", "_", titolo_rep).strip("_") or "farmacia"
    data = oggi_.isoformat()
    allegati, avvisi = [], []
    if "PDF" in formati:
        pdf = inv_pdf(titolo_rep, f"Creato il {data_it(data)}", pagine,
                      "Documento creato dall'app «VitaMemo» con i dati inseriti dalle persone: non è verificato da un medico o da un farmacista. "
                      "Le foto e i PDF caricati non sono inclusi.")
        if pdf:
            allegati.append((f"{base}_{data}.pdf", "application/pdf", pdf))
        else:
            avvisi.append("Per creare il PDF serve la libreria reportlab (riga «reportlab» in requirements.txt): ho preparato il file da stampare.")
            formati = list(formati) + ["Da stampare (HTML)"]
    if "Excel" in formati:
        allegati.append((f"{base}_{data}.xlsx", _MIME["xlsx"], fam_xlsx(fam_fogli(persone, sez, fogli_extra))))
    if "Da stampare (HTML)" in formati:
        allegati.append((f"{base}_{data}.html", "text/html", fam_html(persone if sez else [], oggi_, sez, _inv_html_extra(tabelle_extra)).encode("utf-8")))
    st.session_state[f"inv_pronti_{chiave}"] = {"allegati": allegati, "testo": inv_testo(titolo_rep + f" · {data_it(data)}", pagine), "avvisi": avvisi,
                                                 "firma": (tuple(scelte), tuple(formati), tuple(p["chiave"] for p in persone))}


def _inv_apri(chiave_exp):
    """Si usa nei pulsanti e nelle scelte (on_click / on_change): ricorda che il pannello va tenuto aperto quando la pagina si ridisegna."""
    st.session_state[chiave_exp] = True


def inv_hub(chiave, persone, d_conto, titolo_rep, preselezione=None, solo_extra=False, chiave_exp=None, passo=1):
    """«Esporta»: a passi numerati. Cosa → in che formato (PDF o ZIP) → Prepara → poi scaricare o inviare (inv_canali)."""
    oggi_ = oggi()
    scelte_possibili = FAM_TITOLI + [FAM_SCHEDA] + INV_EXTRA
    predefinite = preselezione or [x for x in scelte_possibili if x not in ("Assunzioni registrate",)]
    cb = dict(on_change=_inv_apri, args=(chiave_exp,)) if chiave_exp else {}
    st.markdown(f"**{_INV_NUM[passo - 1]} Cosa vuoi esportare?**")
    scelte = st.multiselect("Cosa vuoi esportare?", scelte_possibili, default=predefinite, key=f"inv_sc_{chiave}", label_visibility="collapsed", **cb)
    st.caption("Togli con la ✕ le voci che non ti servono.")
    st.markdown(f"**{_INV_NUM[passo]} In che formato?**")
    nomi_f = {"pdf": "📄 PDF · da leggere, stampare o mandare", "zip": "🗜️ ZIP · un pacchetto con PDF + Excel + pagina da stampare"}
    formato = st.radio("In che formato?", list(nomi_f), format_func=lambda k: nomi_f[k], key=f"inv_fmt_{chiave}", label_visibility="collapsed", **cb)
    formati = ["PDF"] if formato == "pdf" else ["PDF", "Excel", "Da stampare (HTML)"]
    if chiave_exp:
        st.session_state[chiave_exp] = True                      # lo stai usando: resta aperto
    if st.button("✅ Prepara", type="primary", key=f"inv_prep_{chiave}", width="stretch", disabled=not scelte):      # senza on_click: altrimenti la pagina si ridisegna prima di preparare
        with st.spinner("Preparo i file…"):
            inv_prepara(chiave, persone, d_conto, scelte, formati, titolo_rep, oggi_)
        st.rerun()                                               # ridisegno subito: il riquadro resta aperto con i passi successivi
    pronti = st.session_state.get(f"inv_pronti_{chiave}")
    if not pronti:
        st.caption("Tocca **Prepara**: subito dopo scegli se scaricarlo qui o inviarlo a qualcuno.")
        return
    attuale = (tuple(scelte), tuple(formati), tuple(p["chiave"] for p in persone))
    if pronti["firma"][0] != attuale[0] or pronti["firma"][2] != attuale[2] or not set(formati) <= set(pronti["firma"][1]):
        st.info("Hai cambiato le scelte: tocca di nuovo **Prepara**.")
        return
    for a in pronti["avvisi"]:
        st.warning(a)
    allegati = list(pronti["allegati"])
    if formato == "pdf":
        allegati = [x for x in allegati if x[0].lower().endswith(".pdf")] or allegati
    else:
        allegati = [(_inv_base_nome(titolo_rep) + "_" + oggi_.isoformat() + ".zip", "application/zip", inv_zip(pronti["testo"], allegati))]
    st.success("✅ Pronto: " + ", ".join(f"{n} ({max(1, len(d) // 1024)} KB)" for n, _, d in allegati))
    inv_canali(chiave, titolo_rep, pronti["testo"], allegati, oggetto=titolo_rep, passo=passo + 2, forma_fissa=True, prima="scarica")


def _inv_altro_scambio(sezione):
    """In fondo al pannello: le altre due strade (passare i dati a un altro utente dell'app, copia completa). Stanno qui, e non più sparse nella pagina."""
    if "sc_pulsante" not in globals() and "trasferimento_pulsante" not in globals():
        return
    with st.expander("🔁 Passare i dati a un'altra persona che usa l'app, o fare una copia di tutto"):
        st.caption("Qui sopra esporti dati **da leggere** (PDF, ZIP). Qui invece prepari un file che **un'altra persona con VitaMemo può importare** nella sua app, oppure una copia completa.")
        try:
            if "sc_pulsante" in globals():
                sc_pulsante(sezione)
            if "trasferimento_pulsante" in globals() and sezione == "salute":
                trasferimento_pulsante("salute")
        except Exception:
            pass


def inv_hub_miei(chiave="miei", preselezione=None, aperto=False):
    """Il pannello «Esporta e invia» per i dati dell'utente che ha fatto l'accesso (tutti i suoi profili, la dispensa, la lista della spesa)."""
    d = _inv_dati_conto()
    f = d.get("farmacia") or {}
    profili = _fa_profili(f)
    chiave_exp = f"inv_exp_{chiave}"
    with st.expander("📤 Esporta: scarica o invia i dati (PDF, ZIP, email, WhatsApp…)", expanded=aperto or bool(st.session_state.get(chiave_exp))):
        nomi = {p["id"]: p["nome"] for p in profili}
        opzioni = ["Tutti i profili"] + [p["id"] for p in profili] if len(profili) > 1 else [profili[0]["id"]]
        st.markdown("**1️⃣ Di chi?**")
        predef = st.session_state.get("fa_profilo")
        scelta = st.selectbox("Di chi?", opzioni, format_func=lambda x: "👨‍👩‍👧 Tutti i profili" if x == "Tutti i profili" else "👤 " + nomi[x], key=f"inv_chi_{chiave}",
                              index=(opzioni.index(predef) if predef in opzioni else 0), label_visibility="collapsed", on_change=_inv_apri, args=(chiave_exp,))
        sel = profili if scelta == "Tutti i profili" else [p for p in profili if p["id"] == scelta]
        persone = [{"chiave": "io:" + p["id"], "nome": p["nome"], "origine": "", "d": d, "f": f, "pid": p["id"], "p": p} for p in sel]
        inv_hub(f"{chiave}_{scelta}", persone, d, "Salute – " + (st.session_state["sess"]["nome"] if scelta == "Tutti i profili" else nomi[scelta]), preselezione,
                chiave_exp=chiave_exp, passo=2)
        _inv_altro_scambio({"farm": "salute", "doc": "documenti"}.get(chiave, "salute"))


def inv_hub_famiglia(persone, scelta_nome, chiave="fam"):
    """Lo stesso pannello nel Controllo famiglia: tutta la famiglia o una persona."""
    d_capo = _inv_dati_conto()
    chiave_exp = f"inv_exp_{chiave}"
    with st.expander("📤 Esporta: scarica o invia i dati (PDF, ZIP, email, WhatsApp…)", expanded=bool(st.session_state.get(chiave_exp))):
        inv_hub(chiave + "_" + re.sub(r"\W+", "", scelta_nome), persone, d_capo, "Salute famiglia" if len(persone) > 1 else "Salute – " + persone[0]["nome"],
                chiave_exp=chiave_exp)
