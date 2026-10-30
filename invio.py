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
                            title=_pdf_txt(titolo), author="La nostra dispensa")
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
            if not righe:
                storia.append(P("Nessun dato inserito.", s_v))
                continue
            pesi = [max(len(_pdf_txt(h)), min(32, max(len(_pdf_txt(r[i])) if i < len(r) else 0 for r in righe))) + 3 for i, h in enumerate(intest)]
            larg = [doc.width * p_ / sum(pesi) for p_ in pesi]
            dati = [[P(h, s_ch) for h in intest]] + [[P(r[i] if i < len(r) else "", s_c) for i in range(len(intest))] for r in righe]
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
        c.drawString(doc.leftMargin, 8 * mm, "La nostra dispensa - contiene dati personali")
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
    msg.set_content(testo + "\n\n—\nInviato dall'app «La nostra dispensa». Contiene dati personali: non inoltrarlo a chi non deve vederlo.")
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
      if (!P) { avviso(MSG.nondati); return; }
      if (!w.navigator.share) { avviso(MSG.nonsupp); return; }
      var files = [];
      try { files = (P.files || []).map(aFile); } catch (x) {}
      if (w.navigator.canShare) files = files.filter(function (f) { try { return w.navigator.canShare({files: [f]}); } catch (x) { return false; } });
      var dati = {title: P.titolo, text: P.testo};
      if (files.length) dati.files = files; else if ((P.files || []).length) avviso(MSG.solotesto);
      w.navigator.share(dati).catch(function (err) { if (!err || err.name !== 'AbortError') avviso(MSG.errore); });
    }, true);
  } catch (err) { /* resta la scelta di scaricare i file */ }
})();
"""

_MSG_JS = {"nondati": "Prima tocca «Prepara» così i file sono pronti da condividere.",
           "nonsupp": "Questo browser non ha la finestra «Condividi»: usa Email, WhatsApp o scarica il file.",
           "solotesto": "Questi file non si possono condividere da qui: mando solo il riepilogo. Per i file usa Email o scarica.",
           "errore": "Non sono riuscito ad aprire «Condividi». Prova con Email o scarica il file."}


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
        return carica_dati(crea_archivio(), st.session_state["percorso"])
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


def inv_canali(chiave, titolo, testo, allegati, oggetto=None):
    """I modi di inviare. allegati = [(nome, mime, byte)]; testo = il riepilogo scritto."""
    oggetto = oggetto or titolo
    allegati, doppi = _inv_senza_doppioni(list(allegati))
    allegati = _inv_nomi_unici(_inv_converti_immagini(allegati))
    chiave = re.sub(r"\W+", "_", str(chiave))                     # le chiavi dei pulsanti finiscono nei nomi di classe della pagina
    d_conto = _inv_dati_conto()
    st.warning("🔒 Stai per inviare **dati personali e sanitari**: controlla bene a chi li mandi.")
    if doppi:
        st.info(f"ℹ️ C'erano {doppi} file identici (la stessa foto salvata più volte): li mando una volta sola.")
    t_tel, t_mail, t_wa, t_tg, t_sms, t_copia = st.tabs(["📤 Telefono", "✉️ Email", "💬 WhatsApp", "✈️ Telegram", "📱 SMS", "📋 Copia"])
    with t_tel:
        st.caption("Si apre la finestra **Condividi** del telefono: scegli WhatsApp, Gmail, Telegram, Drive, Signal, Messenger… "
                   "il file va allegato.")
        inv_registra_condivisione(chiave, titolo, testo, allegati)
        with st.container(key=f"invio_share_{chiave}"):
            st.button("📤 Condividi con un'altra app", key=f"invio_btn_share_{chiave}", type="primary", width="stretch")
    with t_mail:
        if not inv_email_pronta():
            st.info("Per mandare l'email **direttamente dall'app** servono i dati della casella nei Secrets di Streamlit "
                    "(EMAIL_USER ed EMAIL_PASSWORD, gli stessi degli avvisi): la guida «Invio» spiega come. "
                    "Intanto usa la scheda «Telefono» e scegli Gmail, oppure apri la tua posta col riepilogo:")
            st.link_button("✉️ Apri la mia posta con il riepilogo", inv_link_mailto("", oggetto, testo), width="stretch")
        else:
            a = st.text_input("A chi (uno o più indirizzi, separati da virgola)", value=d_conto.get("avviso_email", ""), key=f"inv_a_{chiave}")
            msg = st.text_area("Messaggio", value="Ti mando in allegato i documenti. " if allegati else "Ecco il riepilogo.", key=f"inv_m_{chiave}", height=80)
            scelti = [x for i, x in enumerate(allegati) if st.checkbox(f"📎 {x[0]} ({len(x[2]) // 1024} KB)", value=True, key=f"inv_c_{chiave}_{i}")]
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
    with t_wa:
        if allegati:
            st.caption("**Con le foto e i file:** si apre «Condividi» del telefono, tocca **WhatsApp**, scegli la persona e invia: le foto sono allegate.")
            with st.container(key=f"invio_share_{chiave}__wa"):
                st.button("💬 Manda su WhatsApp con le foto", key=f"invio_btn_share_wa_{chiave}", type="primary", width="stretch")
            st.divider()
            st.caption("**Solo il testo** (senza foto):")
        num = st.text_input("Numero (facoltativo, con prefisso senza +, es. 39333…)", key=f"inv_wa_{chiave}")
        st.link_button("💬 Apri WhatsApp con il riepilogo scritto", inv_link_whatsapp(num, testo), width="stretch")
        if not allegati:
            st.caption("Questo invio è solo testo: non ci sono foto o file da allegare.")
    with t_tg:
        chat = str(d_conto.get("telegram_chat_id") or "").strip()
        if not inv_segreto("TELEGRAM_TOKEN"):
            st.info("Per mandare i file nella tua chat Telegram servono TELEGRAM_TOKEN nei Secrets di Streamlit (lo stesso del bot): "
                    "la guida «Invio» spiega come. Intanto usa la scheda «Telefono» e scegli Telegram.")
        elif not chat:
            st.info("Manca il tuo Chat ID: inseriscilo in «Scegli come ricevere gli avvisi» in Salute, poi torna qui.")
        else:
            st.caption("Riepilogo e file arrivano nella tua chat con **@dispensa_leo_bot**, da lì li inoltri a chi vuoi.")
            if st.button("✈️ Mandami tutto su Telegram", type="primary", key=f"inv_tg_{chiave}", width="stretch"):
                with st.spinner("Invio in corso…"):
                    esito, motivo = inv_invia_telegram(chat, testo, allegati)
                st.success("✅ Inviato: guarda Telegram.") if esito else st.error("Non sono riuscito a inviarlo: " + motivo)
    with t_sms:
        num2 = st.text_input("Numero (facoltativo)", key=f"inv_sms_{chiave}")
        st.link_button("📱 Apri i messaggi con il riepilogo breve", inv_link_sms(num2, testo), width="stretch")
        st.caption("Gli SMS sono brevi: va solo l'inizio del riepilogo.")
    with t_copia:
        st.caption("Tocca l'icona in alto a destra del riquadro per copiare, poi incolla dove vuoi.")
        st.code(testo, language=None)
    st.markdown("**⬇ Oppure scarica i file**")
    for i, (nome, mime, dati) in enumerate(allegati):
        st.download_button(f"⬇ {nome}", dati, file_name=nome, mime=mime, key=f"inv_dl_{chiave}_{i}", width="stretch")


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
                      "Documento creato dall'app «La nostra dispensa» con i dati inseriti dalle persone: non è verificato da un medico o da un farmacista. "
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


def inv_hub(chiave, persone, d_conto, titolo_rep, preselezione=None, solo_extra=False, chiave_exp=None):
    """«Esporta e invia»: si sceglie cosa e in che formato, si preme Prepara, poi si invia con il canale preferito."""
    oggi_ = oggi()
    scelte_possibili = FAM_TITOLI + [FAM_SCHEDA] + INV_EXTRA
    predefinite = preselezione or [x for x in scelte_possibili if x not in ("Assunzioni registrate",)]
    cb = dict(on_change=_inv_apri, args=(chiave_exp,)) if chiave_exp else {}
    scelte = st.multiselect("Cosa vuoi inviare o esportare", scelte_possibili, default=predefinite, key=f"inv_sc_{chiave}", **cb)
    formati = st.multiselect("Formato dei file", ["PDF", "Excel", "Da stampare (HTML)"], default=["PDF"], key=f"inv_fm_{chiave}", **cb)
    cbb = dict(on_click=_inv_apri, args=(chiave_exp,)) if chiave_exp else {}
    if st.button("📦 Prepara i file", type="primary", key=f"inv_prep_{chiave}", width="stretch", disabled=not (scelte and formati), **cbb):
        with st.spinner("Preparo i file…"):
            inv_prepara(chiave, persone, d_conto, scelte, formati, titolo_rep, oggi_)
    pronti = st.session_state.get(f"inv_pronti_{chiave}")
    if not pronti:
        st.caption("Scegli cosa includere e tocca **Prepara i file**: poi compaiono i modi di inviarli.")
        return
    attuale = (tuple(scelte), tuple(formati), tuple(p["chiave"] for p in persone))
    if pronti["firma"][0] != attuale[0] or pronti["firma"][2] != attuale[2] or not set(formati) <= set(pronti["firma"][1]):
        st.info("Hai cambiato le scelte: tocca di nuovo **Prepara i file**.")
        return
    for a in pronti["avvisi"]:
        st.warning(a)
    st.success("✅ File pronti: " + ", ".join(f"{n} ({len(d) // 1024} KB)" for n, _, d in pronti["allegati"]))
    inv_canali(chiave, titolo_rep, pronti["testo"], pronti["allegati"], oggetto=titolo_rep)


def inv_hub_miei(chiave="miei", preselezione=None, aperto=False):
    """Il pannello «Esporta e invia» per i dati dell'utente che ha fatto l'accesso (tutti i suoi profili, la dispensa, la lista della spesa)."""
    d = _inv_dati_conto()
    f = d.get("farmacia") or {}
    profili = _fa_profili(f)
    chiave_exp = f"inv_exp_{chiave}"
    with st.expander("📤 Esporta e invia: PDF, email, WhatsApp, Telegram…", expanded=aperto or bool(st.session_state.get(chiave_exp))):
        nomi = {p["id"]: p["nome"] for p in profili}
        opzioni = ["Tutti i profili"] + [p["id"] for p in profili] if len(profili) > 1 else [profili[0]["id"]]
        scelta = st.selectbox("Di chi", opzioni, format_func=lambda x: x if x == "Tutti i profili" else nomi[x], key=f"inv_chi_{chiave}",
                              on_change=_inv_apri, args=(chiave_exp,))
        sel = profili if scelta == "Tutti i profili" else [p for p in profili if p["id"] == scelta]
        persone = [{"chiave": "io:" + p["id"], "nome": p["nome"], "origine": "", "d": d, "f": f, "pid": p["id"], "p": p} for p in sel]
        inv_hub(f"{chiave}_{scelta}", persone, d, "Salute " + (st.session_state["sess"]["nome"] if scelta == "Tutti i profili" else nomi[scelta]), preselezione,
                chiave_exp=chiave_exp)


def inv_hub_famiglia(persone, scelta_nome, chiave="fam"):
    """Lo stesso pannello nel Controllo famiglia: tutta la famiglia o una persona."""
    d_capo = _inv_dati_conto()
    chiave_exp = f"inv_exp_{chiave}"
    with st.expander("📤 Invia tutto: PDF, email, WhatsApp, Telegram…", expanded=bool(st.session_state.get(chiave_exp))):
        inv_hub(chiave + "_" + re.sub(r"\W+", "", scelta_nome), persone, d_capo, "Salute famiglia" if len(persone) > 1 else "Salute " + persone[0]["nome"],
                chiave_exp=chiave_exp)
