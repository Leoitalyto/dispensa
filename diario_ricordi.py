# -*- coding: utf-8 -*-
"""📖 Diario dei ricordi (Compleanni): sotto la scheda di OGNI persona c'è un bottone verde rotondo. Toccandolo si apre un diario con le foto ricordo:
ogni pagina è larga come la scheda, ha i bordi stondati e una cornice neon; sopra la foto si possono mettere testi colorati e icone (emoji),
scegliendo colore, grandezza, carattere e posizione. Ogni pagina ha il bottone rosso per chiudere il diario.
Dati: p["ricordi"] = [{id, foto, did, els:[{id, k:"t"|"i", t, c, s, x, y, f}]}] dentro la scheda; le foto in documenti/<uid>/ (cp_file_*). Prefisso: dr_"""
import html as _dr_html
import io as _dr_io
import uuid as _dr_uuid

import streamlit as st

DR_FONT = {"Classico": "Georgia,'Times New Roman',serif", "Corsivo": "'Brush Script MT','Segoe Script','Snell Roundhand','Apple Chancery',cursive",
           "Stampatello": "Impact,'Arial Black','Segoe UI',sans-serif", "Macchina da scrivere": "'Courier New',monospace"}
DR_ICONE = ["❤️", "🌹", "🕯️", "🕊️", "⭐", "🎂", "🎁", "🙏", "✝️", "☀️", "🌙", "🌸", "🌻", "🍀", "👼", "💐", "😊", "😢", "🥂", "🎈", "🏠", "✈️", "📷", "🎶"]
DR_COLORI = ["#ffffff", "#ffe066", "#ff8fab", "#ff5c5c", "#7dd3fc", "#86efac", "#c4b5fd", "#ffb74d", "#000000"]


def dr_pagine(p):
    return [x for x in (p.get("ricordi") or []) if isinstance(x, dict)]


def dr_files(p):
    return [x.get("foto") for x in dr_pagine(p) if x.get("foto")]


def _dr_colore(p):
    try:
        if p.get("scomparso"):
            return CP_COLORE_MEMORIA
        d = cp_data(p.get("nascita"))
        return cp_colore(cp_segno(d)) if d else "#20e6ff"
    except Exception:
        return "#20e6ff"


def _dr_salva_persona(pid, fn, msg):
    def _m(d):
        for x in d.get("compleanni", []):
            if x.get("id") == pid:
                fn(x)
                return
    _cp_salva(_m, msg)


def _dr_comprimi(dati):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(_dr_io.BytesIO(dati))).convert("RGB")
    im.thumbnail((1400, 1400), Image.LANCZOS)
    b = _dr_io.BytesIO()
    im.save(b, "WEBP", quality=80, method=6)
    return b.getvalue()


def dr_el_html(e):
    t = _dr_html.escape(str(e.get("t") or "")).replace("\n", "<br>")
    if not t:
        return ""
    s = float(e.get("s") or 28)
    fam = DR_FONT.get(e.get("f"), DR_FONT["Classico"]) if e.get("k") == "t" else "inherit"
    return (f"<span class='dr-el' style=\"left:{float(e.get('x', 50)):.1f}%;top:{float(e.get('y', 50)):.1f}%;color:{_dr_html.escape(str(e.get('c') or '#fff'), quote=True)};"
            f"font-size:{s / 4:.2f}cqw;font-family:{fam}\">{t}</span>")


def dr_pagina_html(pg, els, col, extra=None):
    """La pagina: foto grande come la scheda, bordi stondati, testi e icone sopra."""
    dati = cp_file_leggi(pg.get("foto") or {}) if pg.get("foto") else None
    if not dati:
        img = "<div class='dr-vuota'>La foto non c'è più</div>"
    else:
        import base64 as _b64
        mime = (pg.get("foto") or {}).get("mime") or "image/webp"
        img = f"<img src='data:{mime};base64,{_b64.b64encode(dati).decode()}' alt=''>"
    sopra = "".join(dr_el_html(e) for e in list(els) + ([extra] if extra else []))
    did = str(pg.get("did") or "").strip()
    return (f"<div class='dr-pag' style='--c:{col}'><div class='dr-foto'>{img}{sopra}</div>"
            + (f"<div class='dr-did'>{_dr_html.escape(did)}</div>" if did else "") + "</div>")


DR_CSS = """<style>
[class*="st-key-dr_apri_"],[class*="st-key-dr_chiudi_"]{display:flex;flex-direction:column;align-items:center}
[class*="st-key-dr_apri_"] [data-testid="stButton"],[class*="st-key-dr_chiudi_"] [data-testid="stButton"]{width:auto !important;display:flex;justify-content:center}
[class*="st-key-dr_apri_"] button,[class*="st-key-dr_chiudi_"] button{width:68px !important;height:68px !important;min-height:0 !important;padding:0 !important;border-radius:50% !important;
 position:relative;transition:transform .12s}
[class*="st-key-dr_apri_"] button{background:radial-gradient(circle at 34% 26%,#d6ff7a 0,#86e01e 40%,#3fa510 100%) !important;border:3px solid #2e8f0d !important;
 box-shadow:0 5px 0 #1f6d08,0 0 14px rgba(120,230,40,.75),inset 0 -6px 10px rgba(0,80,0,.35) !important}
[class*="st-key-dr_chiudi_"] button{background:radial-gradient(circle at 34% 26%,#ff8a8a 0,#ee2230 42%,#b3121e 100%) !important;border:3px solid #9c0f1b !important;
 box-shadow:0 5px 0 #6e0a12,0 0 14px rgba(255,60,60,.7),inset 0 -6px 10px rgba(90,0,0,.4) !important}
[class*="st-key-dr_apri_"] button:active,[class*="st-key-dr_chiudi_"] button:active{transform:translateY(3px)}
[class*="st-key-dr_apri_"] button p,[class*="st-key-dr_chiudi_"] button p{font-size:2.1rem !important;line-height:1 !important;color:#fff !important;font-weight:900 !important;
 text-shadow:0 0 8px #fff,0 0 14px rgba(255,255,255,.9)}
.dr-leg{text-align:center;font-size:.78rem;font-weight:700;margin:4px 0 8px;color:#cfe}
.dr-pag{margin:10px 2px;padding:8px;border-radius:24px;border:2px solid var(--c);background:#0b1120;box-shadow:0 0 8px var(--c),0 0 20px var(--c);
 transform-origin:left center;animation:dr-sfoglia .55s ease-out}
.dr-foto{position:relative;container-type:inline-size;border-radius:18px;overflow:hidden;background:#05080f;line-height:0}
.dr-foto img{width:100%;height:auto;display:block}
.dr-vuota{padding:40px 10px;text-align:center;color:#9ab;line-height:1.3}
.dr-el{position:absolute;transform:translate(-50%,-50%);text-align:center;line-height:1.15;white-space:nowrap;font-weight:700;
 text-shadow:0 0 3px rgba(0,0,0,.95),0 1px 4px rgba(0,0,0,.95),0 0 10px rgba(0,0,0,.6)}
.dr-did{padding:8px 6px 2px;text-align:center;font-style:italic;color:#e9eefb;font-size:.92rem;line-height:1.35}
.dr-num{text-align:center;font-size:.8rem;opacity:.8;margin:2px 0}
@keyframes dr-sfoglia{from{transform:perspective(900px) rotateY(-65deg);opacity:.2}to{transform:perspective(900px) rotateY(0);opacity:1}}
@media (prefers-reduced-motion:reduce){.dr-pag{animation:none}}
</style>"""


def _dr_chiudi(pid, k):
    with st.container(key=f"dr_chiudi_{pid}_{k}"):
        if st.button("⏻", key=f"dr_x_{pid}_{k}", help="Chiudi il diario"):
            st.session_state["dr_aperto"] = None
            st.session_state["dr_mod"] = None
            st.rerun()
    st.markdown("<div class='dr-leg'>Chiudi il diario</div>", unsafe_allow_html=True)


def _dr_nuove(p, pid):
    """Carica una o più foto: ognuna diventa una pagina."""
    up = (ar_uploader("📷 Scegli le foto ricordo", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"dr_up_{pid}")
          if "ar_uploader" in globals() else st.file_uploader("📷 Scegli le foto ricordo", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"dr_up_{pid}"))
    if up and st.button(f"➕ Aggiungi {len(up)} pagina/e al diario", type="primary", key=f"dr_addp_{pid}", width="stretch"):
        nuove = []
        try:
            with st.spinner("Salvo le foto…"):
                for f in up:
                    rif = cp_file_salva(_dr_comprimi(f.getvalue()), "ricordo.webp", "image/webp")
                    nuove.append({"id": _dr_uuid.uuid4().hex[:10], "foto": rif, "did": "", "els": []})
        except Exception as e:
            st.error(f"Non sono riuscito a salvare una foto ({type(e).__name__}). Riprova.")
            return
        _dr_salva_persona(pid, lambda x: x.setdefault("ricordi", []).extend(nuove), "Diario ricordi: nuove pagine")
        st.session_state["dr_pag"] = len(dr_pagine(p)) + len(nuove) - 1
        st.session_state.pop(f"dr_up_{pid}", None)
        st.rerun()


def _dr_editor(p, pid, pg, col):
    k = f"dr_e_{pg['id']}"
    els = list(pg.get("els") or [])
    ph = st.container()                                     # anteprima in alto, sopra i campi
    did = st.text_input("Didascalia sotto la foto (facoltativa)", value=pg.get("did", ""), key=k + "_did")
    st.markdown("**Testi e icone sopra la foto**")
    sel = st.session_state.get("dr_el")
    cur = next((e for e in els if e["id"] == sel), None)
    tipo = st.pills("Cosa aggiungo", ["✍️ Testo", "😊 Icona"], default=("😊 Icona" if cur and cur.get("k") == "i" else "✍️ Testo"), key=k + "_tipo", label_visibility="collapsed") or "✍️ Testo"
    kk = k + "_" + (sel or "n")
    extra = None
    if tipo.startswith("✍"):
        testo = st.text_area("Scrivi il testo", value=(cur or {}).get("t", "") if cur and cur.get("k") == "t" else "", key=kk + "_t", height=80)
        fnt = st.selectbox("Carattere", list(DR_FONT), index=list(DR_FONT).index(cur["f"]) if cur and cur.get("f") in DR_FONT else 0, key=kk + "_f")
    else:
        sc = st.pills("Scegli un'icona", DR_ICONE, key=kk + "_ic", label_visibility="collapsed")
        testo = st.text_input("Oppure scrivi un'icona (emoji)", value=sc or ((cur or {}).get("t", "") if cur and cur.get("k") == "i" else ""), key=kk + "_ic2" + (sc or ""))
        fnt = "Classico"
    colore = st.color_picker("Colore", value=(cur or {}).get("c", "#ffffff") if cur and cur.get("k") == ("t" if tipo.startswith("✍") else "i") else "#ffffff", key=kk + "_c") if tipo.startswith("✍") else "#ffffff"
    if tipo.startswith("✍"):
        st.caption("Colori veloci: bianco, giallo, rosa, rosso, azzurro, verde, viola, arancio, nero (scegli dal selettore qui sopra).")
    gr = st.slider("Grandezza", 12, 140 if not tipo.startswith("✍") else 80, int((cur or {}).get("s", 40 if not tipo.startswith("✍") else 28)), key=kk + "_s")
    x = st.slider("Posizione: sinistra ↔ destra", 0, 100, int((cur or {}).get("x", 50)), key=kk + "_x")
    y = st.slider("Posizione: alto ↕ basso", 0, 100, int((cur or {}).get("y", 50)), key=kk + "_y")
    nuovo = {"id": sel if cur else _dr_uuid.uuid4().hex[:8], "k": "t" if tipo.startswith("✍") else "i", "t": testo, "c": colore, "s": gr, "x": x, "y": y, "f": fnt}
    resto = [e for e in els if e["id"] != nuovo["id"]]
    ph.markdown(dr_pagina_html({**pg, "did": did}, resto, col, nuovo if testo.strip() else None), unsafe_allow_html=True)
    b1, b2 = st.columns(2, gap="small")
    if b1.button("💾 " + ("Salva le modifiche" if cur else "Metti sulla foto"), key=kk + "_ok", type="primary", width="stretch", disabled=not testo.strip()):
        def _fn(x_, pgid=pg["id"]):
            for q in x_.get("ricordi", []):
                if q.get("id") == pgid:
                    q["els"] = [e for e in q.get("els", []) if e.get("id") != nuovo["id"]] + [nuovo]
        _dr_salva_persona(pid, _fn, "Diario ricordi: testo/icona")
        st.session_state["dr_el"] = None
        for s_ in [s for s in st.session_state if str(s).startswith(k + "_")]:
            st.session_state.pop(s_, None)
        st.rerun()
    if cur and b2.button("Nuovo elemento", key=kk + "_nuovo", width="stretch"):
        st.session_state["dr_el"] = None
        st.rerun()
    if els:
        st.markdown("**Già sulla foto**")
        for e in els:
            r1, r2, r3 = st.columns([3, 1, 1], gap="small")
            r1.markdown(("✍️ " if e.get("k") == "t" else "") + _dr_html.escape(str(e.get("t", ""))[:28]))
            if r2.button("✏️", key=f"{k}_ed_{e['id']}", help="Modifica", width="stretch"):
                st.session_state["dr_el"] = e["id"]
                st.rerun()
            if r3.button("🗑️", key=f"{k}_del_{e['id']}", help="Togli", width="stretch"):
                _dr_salva_persona(pid, lambda x_, pgid=pg["id"], eid=e["id"]: [q.update(els=[z for z in q.get("els", []) if z.get("id") != eid]) for q in x_.get("ricordi", []) if q.get("id") == pgid], "Diario ricordi: tolto")
                st.rerun()
    st.markdown("**Cambia la foto**")
    nf = st.file_uploader("Nuova foto per questa pagina", type=["jpg", "jpeg", "png", "webp"], key=k + "_nf")
    c1, c2 = st.columns(2, gap="small")
    if c1.button("✅ Fatto", key=k + "_fatto", width="stretch"):
        def _fn2(x_, pgid=pg["id"]):
            for q in x_.get("ricordi", []):
                if q.get("id") == pgid:
                    q["did"] = did
        _dr_salva_persona(pid, _fn2, "Diario ricordi: didascalia")
        if nf is not None:
            try:
                rif = cp_file_salva(_dr_comprimi(nf.getvalue()), "ricordo.webp", "image/webp")
                vecchia = pg.get("foto")
                _dr_salva_persona(pid, lambda x_, pgid=pg["id"], r=rif: [q.update(foto=r) for q in x_.get("ricordi", []) if q.get("id") == pgid], "Diario ricordi: nuova foto")
                cp_file_cancella([vecchia])
            except Exception as e_:
                st.error(f"Non sono riuscito a cambiare la foto ({type(e_).__name__}).")
                return
        st.session_state["dr_mod"] = None
        st.session_state["dr_el"] = None
        st.rerun()
    if c2.button("🗑️ Elimina pagina", key=k + "_elim", width="stretch"):
        st.session_state["dr_conf"] = pg["id"]
        st.rerun()
    if st.session_state.get("dr_conf") == pg["id"]:
        st.warning("Eliminare questa pagina con la sua foto?")
        s1, s2 = st.columns(2, gap="small")
        if s1.button("🗑️ Sì, elimina", key=k + "_si", type="primary", width="stretch"):
            _dr_salva_persona(pid, lambda x_, pgid=pg["id"]: x_.__setitem__("ricordi", [q for q in x_.get("ricordi", []) if q.get("id") != pgid]), "Diario ricordi: pagina eliminata")
            cp_file_cancella([pg.get("foto")])
            st.session_state.update({"dr_conf": None, "dr_mod": None, "dr_el": None, "dr_pag": max(0, int(st.session_state.get("dr_pag", 0)) - 1)})
            st.rerun()
        if s2.button("No", key=k + "_no", width="stretch"):
            st.session_state["dr_conf"] = None
            st.rerun()


def _dr_diario(p, pid, col):
    pagine = dr_pagine(p)
    if not pagine:
        st.info("Il diario è vuoto. Scegli una o più foto: ognuna sarà una pagina.")
        _dr_nuove(p, pid)
        _dr_chiudi(pid, "v")
        return
    i = max(0, min(int(st.session_state.get("dr_pag", 0)), len(pagine) - 1))
    st.session_state["dr_pag"] = i
    pg = pagine[i]
    st.markdown(f"<div class='dr-num'>📖 Pagina {i + 1} di {len(pagine)}</div>", unsafe_allow_html=True)
    if st.session_state.get("dr_mod") == pg["id"]:
        _dr_editor(p, pid, pg, col)
        return
    st.markdown(dr_pagina_html(pg, pg.get("els") or [], col), unsafe_allow_html=True)
    n1, n2 = st.columns(2, gap="small")
    if n1.button("◀ Indietro", key=f"dr_prev_{pid}", width="stretch", disabled=i == 0):
        st.session_state["dr_pag"] = i - 1
        st.rerun()
    if n2.button("Avanti ▶", key=f"dr_next_{pid}", width="stretch", disabled=i >= len(pagine) - 1):
        st.session_state["dr_pag"] = i + 1
        st.rerun()
    m1, m2 = st.columns(2, gap="small")
    if m1.button("✏️ Testi e icone", key=f"dr_mod_{pid}", width="stretch"):
        st.session_state["dr_mod"] = pg["id"]
        st.session_state["dr_el"] = None
        st.rerun()
    with m2:
        pass
    with st.expander("➕ Aggiungi altre foto al diario"):
        _dr_nuove(p, pid)
    _dr_chiudi(pid, "p")                                      # il bottone rosso in ogni pagina


def dr_blocco(p):
    """Sotto la scheda: il bottone verde e, se aperto, il diario."""
    pid = p["id"]
    st.markdown(DR_CSS, unsafe_allow_html=True)
    n = len(dr_pagine(p))
    aperto = st.session_state.get("dr_aperto") == pid
    if not aperto:
        with st.container(key=f"dr_apri_{pid}"):
            if st.button("⏻", key=f"dr_o_{pid}", help="Apri il diario dei ricordi"):
                st.session_state["dr_aperto"] = pid
                st.session_state["dr_pag"] = 0
                st.session_state["dr_mod"] = None
                st.rerun()
        st.markdown(f"<div class='dr-leg'>📖 Diario dei ricordi{f' ({n})' if n else ''}</div>", unsafe_allow_html=True)
        return
    _dr_diario(p, pid, _dr_colore(p))
