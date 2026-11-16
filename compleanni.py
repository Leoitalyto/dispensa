# -*- coding: utf-8 -*-
"""🎂 Compleanni (dentro Utilità): una scheda-badge per ogni persona.
- L'icona di apertura è il badge nella lingua dell'app (compleanni_img.py).
- Il segno zodiacale si sceglie dalla data di nascita; il nome del segno è scritto dal programma nella lingua.
- Cornice neon a due linee, nel colore del segno. Foto facoltativa.
- Se la persona non c'è più: al posto del segno compaiono le mani con la candela, con la fiamma che vibra come viva.
I dati stanno in d["compleanni"] (lista di schede con id). Caricato da app_dispensa.py dopo utilita.py (serve solo per _ut_chiama)."""
import base64
import calendar
import datetime as _cp_dt
import html as _cp_html
import io
import re as _cp_re
import uuid as _cp_uuid

import streamlit as st

# (chiave, mese e giorno di INIZIO, colore neon)
CP_SEGNI = [
    ("capricorno", (12, 22), "#e0ae4a"), ("acquario", (1, 20), "#34c1ff"), ("pesci", (2, 19), "#2de3d0"),
    ("ariete", (3, 21), "#f5c542"), ("toro", (4, 20), "#4aa8ff"), ("gemelli", (5, 21), "#ff5a5a"),
    ("cancro", (6, 21), "#a883ff"), ("leone", (7, 23), "#ff9a2e"), ("vergine", (8, 23), "#ff7cc8"),
    ("bilancia", (9, 23), "#3ddc84"), ("scorpione", (10, 23), "#ff3d3d"), ("sagittario", (11, 22), "#b862ff"),
]
CP_COLORE_MEMORIA = "#ffb347"
CP_NOMI_SEGNI = {
    "it": ["Ariete", "Toro", "Gemelli", "Cancro", "Leone", "Vergine", "Bilancia", "Scorpione", "Sagittario", "Capricorno", "Acquario", "Pesci"],
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    "fr": ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge", "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"],
    "ar": ["الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء", "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت"],
    "de": ["Widder", "Stier", "Zwillinge", "Krebs", "Löwe", "Jungfrau", "Waage", "Skorpion", "Schütze", "Steinbock", "Wassermann", "Fische"],
    "ro": ["Berbec", "Taur", "Gemeni", "Rac", "Leu", "Fecioară", "Balanță", "Scorpion", "Săgetător", "Capricorn", "Vărsător", "Pești"],
    "pt": ["Áries", "Touro", "Gémeos", "Caranguejo", "Leão", "Virgem", "Balança", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"],
    "es": ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"],
}
CP_ORDINE_SEGNI = ["ariete", "toro", "gemelli", "cancro", "leone", "vergine", "bilancia", "scorpione", "sagittario", "capricorno", "acquario", "pesci"]
CP_MESI = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "ro": ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
}
CP_RELAZIONI = ["", "Famiglia", "Amico/a", "Collega", "Vicino/a", "Conoscente", "Altro"]


def _cp_lg():
    lg = st.session_state.get("lang", "it")
    return lg if lg in CP_NOMI_SEGNI else "it"


def _cp_t(frase, **v):
    f = globals().get("t")
    return f(frase, **v) if callable(f) else (frase.format(**v) if v else frase)


def cp_segno(data):
    """Chiave del segno per una data (date)."""
    md = (data.month, data.day)
    scelto = "capricorno"
    for chiave, inizio, _c in sorted(CP_SEGNI, key=lambda x: x[1]):
        if md >= inizio:
            scelto = chiave
    if md < (1, 20):
        scelto = "capricorno"
    return scelto


def cp_colore(chiave):
    for k, _i, c in CP_SEGNI:
        if k == chiave:
            return c
    return "#4aa8ff"


def cp_nome_segno(chiave):
    return CP_NOMI_SEGNI[_cp_lg()][CP_ORDINE_SEGNI.index(chiave)]


def cp_data(testo):
    try:
        return _cp_dt.date.fromisoformat(str(testo)[:10])
    except Exception:
        return None


def cp_prossimo(nascita, oggi):
    """Prossimo compleanno (date). Il 29 febbraio negli anni non bisestili si festeggia il 28."""
    for anno in (oggi.year, oggi.year + 1):
        m, g = nascita.month, nascita.day
        if m == 2 and g == 29 and not calendar.isleap(anno):
            g = 28
        cand = _cp_dt.date(anno, m, g)
        if cand >= oggi:
            return cand
    return oggi


def cp_data_scritta(data, con_anno=True):
    m = CP_MESI[_cp_lg()][data.month - 1]
    return f"{data.day} {m}" + (f" {data.year}" if con_anno else "")


def cp_nuovo_id():
    return _cp_uuid.uuid4().hex[:12]


def cp_foto_da_file(f, lato=320):
    """Foto quadrata al centro, piccola (webp) → data URI da tenere nella scheda."""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(f.getvalue()))).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 4 if h > w else (h - s) // 2, (w - s) // 2 + s, (h - s) // 4 + s if h > w else (h - s) // 2 + s)).resize((lato, lato), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def cp_rgba(hex_, a):
    h = hex_.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def cp_telegram_url(v):
    v = str(v or "").strip()
    if not v:
        return ""
    if v.lower().startswith(("http://", "https://", "t.me/")):
        return v if v.lower().startswith("http") else "https://" + v
    if v.startswith("@"):
        return "https://t.me/" + v[1:]
    cifre = _cp_re.sub(r"[^\d+]", "", v)
    if cifre and len(cifre.lstrip("+")) >= 6 and not _cp_re.search(r"[A-Za-z_]", v):
        return "https://t.me/" + (cifre if cifre.startswith("+") else "+" + cifre)
    return "https://t.me/" + v


def cp_whatsapp_url(v):
    c = cc_cifre(v) if "cc_cifre" in globals() else _cp_re.sub(r"[^\d+]", "", str(v or ""))
    c = c.lstrip("+")
    return f"https://wa.me/{c}" if len(c) >= 6 else ""


CP_CSS = """<style>
.cp-card{position:relative;margin:14px 2px 6px;padding:14px 12px 12px;border-radius:20px;color:#e9eefb;
 background:radial-gradient(120% 90% at 50% 0%,#16213a 0%,#0b1120 70%);border:2px solid var(--c);
 box-shadow:0 0 6px var(--cg),0 0 18px var(--cg),inset 0 0 12px var(--cg)}
.cp-card:before{content:"";position:absolute;inset:5px;border-radius:15px;border:1px solid var(--c);opacity:.8;pointer-events:none;
 box-shadow:0 0 6px var(--cg)}
.cp-testa{display:flex;gap:10px;align-items:center}
.cp-foto{flex:0 0 64px;width:64px;height:64px;border-radius:50%;border:2px solid var(--c);box-shadow:0 0 10px var(--cg);
 background:#0f172a center/cover no-repeat;display:flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:800;color:var(--c)}
.cp-nome{flex:1;min-width:0}.cp-nome b{display:block;font-size:1.12rem;line-height:1.2;color:#fff;word-break:break-word}
.cp-nome i{font-style:normal;font-size:.8rem;opacity:.75;display:block}
.cp-nome .cp-chip{display:inline-block;margin-top:5px;padding:2px 9px;border-radius:999px;border:1px solid var(--c);color:var(--c);font-size:.78rem;font-weight:700;background:var(--cg2);white-space:nowrap}
.cp-segno{margin:8px auto 0;text-align:center}.cp-segno img{width:150px;max-width:62%;height:auto;max-height:130px;object-fit:contain;filter:drop-shadow(0 0 8px var(--cg))}
.cp-segno span{display:block;font-size:.72rem;letter-spacing:.04em;color:var(--c);font-weight:700;margin-top:1px}
.cp-righe{margin-top:10px;display:grid;gap:3px;font-size:.88rem}
.cp-righe div{display:flex;gap:7px;line-height:1.3;word-break:break-word}.cp-righe div>span:first-child{flex:0 0 1.4em}
.cp-righe a{color:var(--c)}
.cp-sez{margin-top:8px;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--c);opacity:.85;border-top:1px dashed var(--cg);padding-top:6px}
/* la fiaccola: mani con la candela e la fiamma viva */
.cp-fiacc{position:relative;width:190px;max-width:70%;margin:8px auto 0}
.cp-fiacc img.cp-base{width:100%;display:block;filter:drop-shadow(0 0 10px rgba(255,170,60,.55))}
.cp-alone{position:absolute;left:37%;top:-4%;width:26%;aspect-ratio:1/1;border-radius:50%;pointer-events:none;
 background:radial-gradient(circle,rgba(255,200,90,.85) 0%,rgba(255,150,40,.35) 40%,rgba(255,120,20,0) 70%);mix-blend-mode:screen;animation:cp-alone 2.3s ease-in-out infinite}
.cp-fiamma{position:absolute;left:45.5%;top:13.9%;width:10.1%;height:26.2%;pointer-events:none;mix-blend-mode:screen;
 transform-origin:50% 100%;animation:cp-fiamma 1.35s ease-in-out infinite}
@keyframes cp-fiamma{0%{transform:scale(1,1) skewX(0);opacity:.95}12%{transform:scale(.93,1.07) skewX(-4deg);opacity:1}
 27%{transform:scale(1.06,.94) skewX(3deg);opacity:.85}41%{transform:scale(.96,1.1) skewX(-2deg);opacity:1}
 58%{transform:scale(1.04,.97) skewX(4deg);opacity:.9}73%{transform:scale(.95,1.06) skewX(-3deg);opacity:1}
 88%{transform:scale(1.02,.98) skewX(2deg);opacity:.88}100%{transform:scale(1,1) skewX(0);opacity:.95}}
@keyframes cp-alone{0%,100%{opacity:.55;transform:scale(.92)}20%{opacity:.95;transform:scale(1.08)}45%{opacity:.7;transform:scale(.97)}
 70%{opacity:1;transform:scale(1.12)}85%{opacity:.65;transform:scale(1)}}
[class*="st-key-cp_azioni_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.4rem !important}
[class*="st-key-cp_azioni_"] [data-testid="stColumn"]{min-width:0 !important;flex:1 1 0 !important;width:auto !important}
[class*="st-key-cp_azioni_"] a,[class*="st-key-cp_azioni_"] button{font-size:.8rem !important;padding:.25rem .3rem !important;min-height:2.3rem !important}
[class*="st-key-cp_data_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.4rem !important}
[class*="st-key-cp_data_"] [data-testid="stColumn"]{min-width:0 !important}
@media (prefers-reduced-motion:reduce){.cp-fiamma,.cp-alone{animation:none}}
</style>"""


def _cp_scheda_html(p, oggi):
    nascita = cp_data(p.get("nascita"))
    scomparso = bool(p.get("scomparso"))
    seg = cp_segno(nascita) if nascita else "ariete"
    col = CP_COLORE_MEMORIA if scomparso else cp_colore(seg)
    e = _cp_html.escape
    nome = (str(p.get("nome", "")) + " " + str(p.get("cognome", ""))).strip() or "—"
    senza_anno = bool(p.get("anno_ignoto"))
    chip, sotto = "", ""
    if nascita:
        pross = cp_prossimo(nascita, oggi)
        giorni = (pross - oggi).days
        eta = pross.year - nascita.year
        if giorni == 0:
            chip = _cp_t("🎉 Oggi!") if not scomparso else _cp_t("🕯️ Oggi")
        elif giorni == 1:
            chip = _cp_t("Domani")
        else:
            chip = _cp_t("tra {n} giorni", n=giorni)
        if scomparso:
            sotto = cp_data_scritta(nascita, not senza_anno) + (" · † " + cp_data_scritta(cp_data(p["data_scomparsa"])) if cp_data(p.get("data_scomparsa")) else " · †")
            if not senza_anno:
                chip += " · " + _cp_t("{n} anni", n=eta)
        else:
            sotto = cp_data_scritta(nascita, not senza_anno)
            if not senza_anno:
                chip += " · " + _cp_t("{n} anni", n=eta)
    soprannome = f"<i>«{e(str(p.get('soprannome')))}»</i>" if p.get("soprannome") else ""
    relaz = f"<i>{e(_cp_t(p['relazione']))}</i>" if p.get("relazione") else ""
    # foto o iniziale
    if p.get("foto"):
        foto = f"<div class='cp-foto' style=\"background-image:url('{e(p['foto'], quote=True)}')\"></div>"
    else:
        ini = (str(p.get("nome", "?"))[:1] + str(p.get("cognome", ""))[:1]).upper() or "?"
        foto = f"<div class='cp-foto'>{e(ini)}</div>"
    # a destra: segno oppure fiaccola
    if scomparso:
        destra = ("<div class='cp-fiacc'><img class='cp-base' alt='' src='data:image/webp;base64," + CPI_FIACCOLA + "'>"
                  "<div class='cp-alone'></div><img class='cp-fiamma' alt='' src='data:image/webp;base64," + CPI_FIAMMA + "'></div>")
    else:
        destra = ("<div class='cp-segno'><img alt='" + e(cp_nome_segno(seg)) + "' src='data:image/webp;base64," + CPI_ZODIACO[seg] + "'>"
                  "<span>" + e(cp_nome_segno(seg)) + "</span></div>")
    righe = []

    def riga(ic, testo, link=""):
        if testo:
            righe.append(f"<div><span>{ic}</span><span>" + (f"<a href='{e(link, quote=True)}' target='_blank' rel='noopener'>{e(testo)}</a>" if link else e(testo)) + "</span></div>")
    if p.get("luogo"):
        righe.append(f"<div class='cp-sez' style='grid-column:1'>{e(_cp_t('Nascita'))}</div>")
        riga("📍", _cp_t("Nato/a a {luogo}", luogo=p["luogo"]))
    contatti = []
    for ic, chiave, fn in (("📱", "cellulare", lambda v: "tel:" + _cp_re.sub(r"[^\d+]", "", v)), ("☎️", "fisso", lambda v: "tel:" + _cp_re.sub(r"[^\d+]", "", v)),
                           ("🟢", "whatsapp", cp_whatsapp_url), ("✈️", "telegram", cp_telegram_url), ("✉️", "email", lambda v: "mailto:" + v)):
        v = str(p.get(chiave) or "").strip()
        if v:
            contatti.append((ic, v, fn(v) if fn(v) != "tel:" else ""))
    if contatti:
        righe.append(f"<div class='cp-sez'>{e(_cp_t('Contatti'))}</div>")
        for ic, v, link in contatti:
            riga(ic, v, link)
    if p.get("indirizzo") or p.get("sito"):
        righe.append(f"<div class='cp-sez'>{e(_cp_t('Dove'))}</div>")
        riga("🏠", p.get("indirizzo", ""))
        if p.get("sito") and cc_url(p["sito"]):
            riga("🌐", str(p["sito"]).strip(), cc_url(p["sito"]))
    if p.get("regalo") or p.get("note"):
        righe.append(f"<div class='cp-sez'>{e(_cp_t('Da ricordare'))}</div>")
        riga("🎁", p.get("regalo", ""))
        riga("📝", p.get("note", ""))
    return (f"<div class='cp-card' style='--c:{col};--cg:{cp_rgba(col, .45)};--cg2:{cp_rgba(col, .14)}'>"
            f"<div class='cp-testa'>{foto}<div class='cp-nome'><b>{e(nome)}</b>{soprannome}{relaz}"
            f"<i>{e(sotto)}</i>" + (f"<span class='cp-chip'>{e(chip)}</span>" if chip else "") + f"</div></div>{destra}"
            f"<div class='cp-righe'>{''.join(righe)}</div></div>")


def cp_campo_data(k, etichetta, attuale=None):
    """Data a tre menu (giorno, mese, anno): sul telefono è più comoda di una data da digitare. Ritorna date oppure None."""
    st.markdown(f"<div style='font-weight:600;margin:2px 0 -4px'>{_cp_html.escape(etichetta)}</div>", unsafe_allow_html=True)
    riga = st.container(key="cp_data_" + k)
    c1, c2, c3 = riga.columns([1.05, 1.75, 1.45], gap="small")
    giorni = list(range(1, 32))
    mesi = CP_MESI[_cp_lg()]
    anni = list(range(_cp_dt.date.today().year, 1899, -1))
    g = c1.selectbox(_cp_t("Giorno"), giorni, index=giorni.index(attuale.day) if attuale else None, placeholder="—", key=k + "_g", label_visibility="collapsed")
    m = c2.selectbox(_cp_t("Mese"), list(range(1, 13)), index=attuale.month - 1 if attuale else None, placeholder=_cp_t("Mese"),
                     format_func=lambda x: mesi[x - 1], key=k + "_m", label_visibility="collapsed")
    a = c3.selectbox(_cp_t("Anno"), anni, index=anni.index(attuale.year) if attuale and attuale.year in anni else None, placeholder=_cp_t("Anno"), key=k + "_a", label_visibility="collapsed")
    if g and m and a:
        try:
            return _cp_dt.date(a, m, g)
        except ValueError:
            st.caption("⚠️ " + _cp_t("Questa data non esiste: controlla giorno e mese."))
    return None


def _cp_dati():
    return carica_dati(crea_archivio(), st.session_state["percorso"])


def _cp_salva(fn, msg):
    salva(fn, msg)


def _cp_pulsanti(p, k):
    pul = []
    n_f, n_c = str(p.get("fisso") or ""), str(p.get("cellulare") or "")
    if cc_numeri(n_f, n_c):
        pul.append(("📞 " + _cp_t("Chiama"), ("__chiama__", n_f, n_c, str(p.get("nome", "")))))
    if cp_whatsapp_url(p.get("whatsapp") or n_c):
        pul.append(("🟢 WhatsApp", cp_whatsapp_url(p.get("whatsapp") or n_c)))
    if cp_telegram_url(p.get("telegram")):
        pul.append(("✈️ Telegram", cp_telegram_url(p.get("telegram"))))
    if str(p.get("email") or "").strip():
        pul.append(("✉️ Email", "mailto:" + str(p["email"]).strip()))
    if cc_url(p.get("sito")):
        pul.append(("🌐 " + _cp_t("Sito"), cc_url(p["sito"])))
    if pul:
        with st.container(key="cp_azioni_" + k):
            cc_pulsanti(pul, "cp_pul_" + k, per_riga=3)


def _cp_modulo(pid):
    """Il modulo di una persona (pid = id oppure '' per una nuova)."""
    lista = _cp_dati().get("compleanni", [])
    p = next((x for x in lista if x.get("id") == pid), {}) if pid else {}
    k = "cpf_" + (pid or "nuovo")
    with st.container(border=True, key=k + "_box"):
        st.markdown("**" + ("✏️ " + _cp_t("Modifica") if pid else "➕ " + _cp_t("Nuova persona")) + "**")
        # 1) foto
        foto_att = st.session_state.get(k + "_foto", p.get("foto", ""))
        if foto_att:
            st.markdown(f"<div style='width:84px;height:84px;border-radius:50%;background:url(\"{_cp_html.escape(foto_att, quote=True)}\") center/cover;margin:2px 0 6px'></div>", unsafe_allow_html=True)
        f = st.file_uploader("📷 " + _cp_t("Foto (facoltativa)"), type=["jpg", "jpeg", "png", "webp"], key=k + "_up")
        if f is not None:
            try:
                st.session_state[k + "_foto"] = cp_foto_da_file(f)
                foto_att = st.session_state[k + "_foto"]
            except Exception:
                st.warning(_cp_t("Non riesco a leggere questa foto: provane un'altra."))
        if foto_att and st.checkbox("🗑️ " + _cp_t("Togli la foto"), key=k + "_togli"):
            foto_att = ""
        # 2) chi è
        c1, c2 = st.columns(2, gap="small")
        nome = c1.text_input(_cp_t("Nome") + " *", value=p.get("nome", ""), key=k + "_nome")
        cognome = c2.text_input(_cp_t("Cognome"), value=p.get("cognome", ""), key=k + "_cogn")
        sopr = st.text_input(_cp_t("Soprannome (facoltativo)"), value=p.get("soprannome", ""), key=k + "_sopr")
        rel_att = p.get("relazione", "")
        relazione = st.selectbox(_cp_t("Chi è per te"), CP_RELAZIONI, index=CP_RELAZIONI.index(rel_att) if rel_att in CP_RELAZIONI else 0,
                                 format_func=lambda x: _cp_t(x) if x else "—", key=k + "_rel")
        # 3) nascita
        nasc_att = cp_data(p.get("nascita"))
        nascita = cp_campo_data(k + "_nasc", "🎂 " + _cp_t("Data di nascita") + " *", nasc_att)
        anno_ignoto = st.checkbox(_cp_t("Non conosco l'anno (conta solo giorno e mese)"), value=bool(p.get("anno_ignoto")), key=k + "_anno")
        luogo = st.text_input("📍 " + _cp_t("Luogo di nascita"), value=p.get("luogo", ""), key=k + "_luogo")
        # 4) contatti
        st.markdown("<div style='margin-top:6px;font-weight:700'>" + _cp_html.escape(_cp_t("Contatti")) + "</div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2, gap="small")
        cell = c3.text_input("📱 " + _cp_t("Cellulare"), value=p.get("cellulare", ""), key=k + "_cell")
        fisso = c4.text_input("☎️ " + _cp_t("Telefono fisso"), value=p.get("fisso", ""), key=k + "_fisso")
        wa = st.text_input("🟢 WhatsApp", value=p.get("whatsapp", ""), key=k + "_wa", placeholder=_cp_t("se vuoto uso il cellulare"))
        tg = st.text_input("✈️ Telegram", value=p.get("telegram", ""), key=k + "_tg", placeholder="@nomeutente")
        email = st.text_input("✉️ Email", value=p.get("email", ""), key=k + "_mail")
        # 5) dove
        indirizzo = st.text_area("🏠 " + _cp_t("Indirizzo"), value=p.get("indirizzo", ""), key=k + "_ind", height=70)
        sito = cc_campo_sito(p.get("sito", ""), k + "_sito")
        # 6) da ricordare
        regalo = st.text_input("🎁 " + _cp_t("Idee regalo"), value=p.get("regalo", ""), key=k + "_reg")
        note = st.text_area("📝 " + _cp_t("Note"), value=p.get("note", ""), key=k + "_note", height=70)
        # 7) scomparsa
        scomp = st.checkbox("🕯️ " + _cp_t("Questa persona non c'è più"), value=bool(p.get("scomparso")), key=k + "_sc",
                            help=_cp_t("Al posto del segno zodiacale compare una candela accesa."))
        data_sc = None
        if scomp:
            data_sc = cp_campo_data(k + "_dsc", _cp_t("Data (facoltativa)"), cp_data(p.get("data_scomparsa")))
        b1, b2 = st.columns(2, gap="small")
        if b1.button("✅ " + _cp_t("Salva"), type="primary", key=k + "_ok", width="stretch"):
            if not nome.strip():
                st.error(_cp_t("Scrivi almeno il nome."))
                return
            if not nascita:
                st.error(_cp_t("Scegli la data di nascita."))
                return
            nid = pid or cp_nuovo_id()
            rec = {"id": nid, "nome": nome.strip(), "cognome": cognome.strip(), "soprannome": sopr.strip(), "relazione": relazione,
                   "nascita": nascita.isoformat(), "anno_ignoto": bool(anno_ignoto), "luogo": luogo.strip(), "cellulare": cell.strip(),
                   "fisso": fisso.strip(), "whatsapp": wa.strip(), "telegram": tg.strip(), "email": email.strip(), "indirizzo": indirizzo.strip(),
                   "sito": (sito or "").strip(), "regalo": regalo.strip(), "note": note.strip(), "foto": foto_att, "scomparso": bool(scomp),
                   "data_scomparsa": data_sc.isoformat() if (scomp and data_sc) else ""}

            def _m(d):
                lst = d.setdefault("compleanni", [])
                for i, x in enumerate(lst):
                    if x.get("id") == nid:
                        lst[i] = rec
                        break
                else:
                    lst.append(rec)
            _cp_salva(_m, "Compleanni: " + rec["nome"])
            for s in [x for x in st.session_state if str(x).startswith(k)]:
                st.session_state.pop(s, None)
            st.session_state["cp_modulo"] = None
            st.session_state["messaggio"] = "✅ " + _cp_t("{nome} salvato/a.", nome=rec["nome"])
            st.rerun()
        if b2.button(_cp_t("Annulla"), key=k + "_no", width="stretch"):
            st.session_state["cp_modulo"] = None
            st.rerun()


def _cp_elenco():
    oggi = _cp_dt.date.today()
    lista = [x for x in _cp_dati().get("compleanni", []) if cp_data(x.get("nascita"))]
    if not lista:
        st.info("🎂 " + _cp_t("Non c'è ancora nessuno. Tocca «Aggiungi una persona»."))
        return
    cerca = st.text_input("🔍 " + _cp_t("Cerca per nome"), key="cp_cerca").strip().lower() if len(lista) > 5 else ""
    if cerca:
        lista = [x for x in lista if cerca in (str(x.get("nome", "")) + " " + str(x.get("cognome", "")) + " " + str(x.get("soprannome", ""))).lower()]
    vivi = sorted([x for x in lista if not x.get("scomparso")], key=lambda x: cp_prossimo(cp_data(x["nascita"]), oggi))
    memoria = sorted([x for x in lista if x.get("scomparso")], key=lambda x: cp_prossimo(cp_data(x["nascita"]), oggi))
    for titolo, gruppo in (("", vivi), ("🕯️ " + _cp_t("In memoria"), memoria)):
        if not gruppo:
            continue
        if titolo:
            st.markdown(f"<div style='margin:18px 0 0;font-weight:800;color:{CP_COLORE_MEMORIA}'>{_cp_html.escape(titolo)}</div>", unsafe_allow_html=True)
        for p in gruppo:
            pid = p["id"]
            st.markdown(_cp_scheda_html(p, oggi), unsafe_allow_html=True)
            _cp_pulsanti(p, pid)
            if st.session_state.get("cp_modulo") == pid:
                _cp_modulo(pid)
                continue
            c1, c2 = st.columns(2, gap="small")
            if c1.button("✏️ " + _cp_t("Modifica"), key=f"cp_mod_{pid}", width="stretch"):
                st.session_state["cp_modulo"] = pid
                st.session_state["cp_elimina"] = None
                st.rerun()
            if st.session_state.get("cp_elimina") == pid:
                st.warning(_cp_t("Eliminare {nome}? Finisce nel cestino e lo puoi recuperare.", nome=p.get("nome", "")))
                s1, s2 = st.columns(2, gap="small")
                if s1.button("🗑️ " + _cp_t("Sì, elimina"), key=f"cp_siel_{pid}", type="primary", width="stretch"):
                    _cp_salva(lambda d, _i=pid: d.__setitem__("compleanni", [x for x in d.get("compleanni", []) if x.get("id") != _i]), "Compleanni: eliminato " + str(p.get("nome", "")))
                    st.session_state["cp_elimina"] = None
                    st.rerun()
                if s2.button(_cp_t("No"), key=f"cp_noel_{pid}", width="stretch"):
                    st.session_state["cp_elimina"] = None
                    st.rerun()
            elif c2.button("🗑️ " + _cp_t("Elimina"), key=f"cp_el_{pid}", width="stretch"):
                st.session_state["cp_elimina"] = pid
                st.rerun()


def cp_blocco_utilita():
    """Il contenuto del riquadro «Compleanni» in Utilità: il badge nella lingua apre e chiude la sezione."""
    st.markdown(CP_CSS, unsafe_allow_html=True)
    b = CPI_BADGE.get(_cp_lg()) or CPI_BADGE["it"]
    st.markdown("<style>div.st-key-cp_apri [data-testid=stButton],div.st-key-cp_apri [data-testid=stElementContainer]{display:flex !important;justify-content:center;width:100% !important}div.st-key-cp_apri{display:flex;justify-content:center}div.st-key-cp_apri button{background:url('data:image/webp;base64," + b +
                "') center/contain no-repeat !important;border:0 !important;box-shadow:none !important;color:transparent !important;width:210px !important;"
                "max-width:70vw;aspect-ratio:410/420;height:auto !important;min-height:0 !important;padding:0 !important;border-radius:0 !important}"
                "div.st-key-cp_apri button p{font-size:0 !important}div.st-key-cp_apri button:hover{filter:drop-shadow(0 0 12px rgba(255,200,90,.9))}</style>",
                unsafe_allow_html=True)
    with st.container(key="cp_apri"):
        if st.button(_cp_t("Compleanni"), key="cp_apri_b"):
            st.session_state["cp_aperto"] = not st.session_state.get("cp_aperto")
            st.rerun()
    if not st.session_state.get("cp_aperto"):
        st.caption(_cp_t("Tocca il badge per aprire i compleanni."))
        return
    if "avs_apri" in globals() and st.button("🔔 " + _cp_t("Avvisi dei compleanni"), key="cp_campanello", width="stretch"):
        avs_apri("compleanni", "Compleanni")
    if st.button("➕ " + _cp_t("Aggiungi una persona"), key="cp_nuovo", type="primary", width="stretch"):
        st.session_state["cp_modulo"] = "__nuovo__"
        st.rerun()
    if st.session_state.get("cp_modulo") == "__nuovo__":
        _cp_modulo("")
    _cp_elenco()
