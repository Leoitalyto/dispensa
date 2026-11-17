# -*- coding: utf-8 -*-
"""Pezzi comuni delle sezioni (Numeri utili, Appuntamenti, Conti, Badante) e i due bottoni sotto il campanellino 🔔:
📞 Numeri utili · 📅 Appuntamenti — in tutte le sezioni tranne Dispensa (e Chat).
Anche qui: gli «interruttori» neon per le pillole/selettori (la voce attiva si accende e pulsa, le altre sembrano spente).
Si carica DOPO pagine_nav.py/avvisi_sezione.py/compleanni.py: avvolge nav_pagine."""
import datetime as _sc_dt
import html as _sc_html
import uuid as _sc_uuid

import streamlit as st

SC_ESCLUSE = ("dispensa", "chat")


def sc_id():
    return _sc_uuid.uuid4().hex[:10]


def sc_oggi():
    try:
        return oggi()
    except Exception:
        return _sc_dt.date.today()


def sc_dati():
    return carica_dati(crea_archivio(), st.session_state["percorso"])


def sc_salva(fn, msg):
    salva(fn, msg)


def sc_euro(x):
    try:
        v = float(x or 0)
    except Exception:
        v = 0.0
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s + " €"


def sc_data(testo):
    try:
        return _sc_dt.date.fromisoformat(str(testo)[:10])
    except Exception:
        return None


def sc_data_scritta(d, con_giorno=True):
    if not d:
        return ""
    gs = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
    return (gs[d.weekday()] + " " if con_giorno else "") + d.strftime("%d/%m/%Y")


def sc_rerun():
    """Dentro una finestra (dialog) ridisegna solo la finestra, senza chiuderla."""
    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()


def _sc_chiuso():
    st.session_state.pop("_sc_dlg", None)


def _sc_corpo_chiudibile(corpo):
    def _c():
        if st.button("✖ Chiudi", key="sc_chiudi_dlg", width="stretch"):
            st.session_state.pop("_sc_dlg", None)
            st.rerun()                                   # ridisegno completo: la finestra sparisce
        corpo()
    return _c


def sc_dialogo(titolo, corpo, larghezza="large"):
    """Finestra che NON si chiude da sola: né toccando fuori, né col tasto indietro, né se la pagina si ridisegna mentre scrivi.
    Si chiude solo con «✖ Chiudi»."""
    st.session_state["_sc_dlg"] = (titolo, corpo, larghezza, st.session_state.get("_sc_sez_corr"))
    st.session_state["_sc_aperto_ora"] = True
    st.dialog(titolo, width=larghezza, dismissible=False)(_sc_corpo_chiudibile(corpo))()


def _sc_riapri(corrente):
    d = st.session_state.get("_sc_dlg")
    if not d:
        return
    titolo, corpo, larghezza, sez = d
    if sez != corrente:
        st.session_state.pop("_sc_dlg", None)
        return
    st.dialog(titolo, width=larghezza, dismissible=False)(_sc_corpo_chiudibile(corpo))()


def sc_esc(x):
    return _sc_html.escape(str(x or ""))


def sc_tel_link(n):
    return "tel:" + (cc_cifre(n) if "cc_cifre" in globals() else "".join(ch for ch in str(n) if ch.isdigit() or ch == "+"))


def sc_chiamate(chiave, fisso="", cellulare="", etichette=("📞 Ufficio", "📱 Cellulare")):
    """Tasti di chiamata semplici (senza finestre): uno per numero, adatti anche dentro una finestra."""
    voci = []
    if str(fisso or "").strip():
        voci.append((etichette[0], sc_tel_link(fisso)))
    if str(cellulare or "").strip():
        voci.append((etichette[1], sc_tel_link(cellulare)))
    return voci


def sc_tasti(voci, chiave):
    """Fila di tasti-collegamento (testo, url) in una riga che non va a capo."""
    if not voci:
        return
    with st.container(key="sc_tasti_" + chiave):
        for i, (col, (et, url)) in enumerate(zip(st.columns(len(voci), gap="small"), voci)):
            col.link_button(et, url, width="stretch", key=f"{chiave}_{i}")


def sc_wa(n):
    c = (cc_cifre(n) if "cc_cifre" in globals() else "".join(ch for ch in str(n or "") if ch.isdigit() or ch == "+")).lstrip("+")
    return f"https://wa.me/{c}" if len(c) >= 6 else ""


def sc_maps(ind):
    import urllib.parse
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(str(ind or ""))


def sc_ics(titolo, data, ora=None, descrizione="", luogo="", minuti=60):
    """Un appuntamento in formato calendario (.ics)."""
    def esc(t):
        return str(t or "").replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")
    uid = sc_id() + "@vitamemo"
    adesso_ = _sc_dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if ora:
        ini = _sc_dt.datetime.combine(data, ora)
        fin = ini + _sc_dt.timedelta(minutes=minuti)
        quando = f"DTSTART:{ini.strftime('%Y%m%dT%H%M%S')}\r\nDTEND:{fin.strftime('%Y%m%dT%H%M%S')}"
    else:
        quando = f"DTSTART;VALUE=DATE:{data.strftime('%Y%m%d')}\r\nDTEND;VALUE=DATE:{(data + _sc_dt.timedelta(days=1)).strftime('%Y%m%d')}"
    return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//VitaMemo//IT\r\nBEGIN:VEVENT\r\n" f"UID:{uid}\r\nDTSTAMP:{adesso_}\r\n{quando}\r\n"
            f"SUMMARY:{esc(titolo)}\r\nDESCRIPTION:{esc(descrizione)}\r\nLOCATION:{esc(luogo)}\r\n"
            "BEGIN:VALARM\r\nTRIGGER:-PT60M\r\nACTION:DISPLAY\r\nDESCRIPTION:Promemoria\r\nEND:VALARM\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")


# ---------------------------------------------------------------------------------------------------------------------
# file (preventivi, documenti): nella scheda resta solo il riferimento
# ---------------------------------------------------------------------------------------------------------------------
def sc_file_salva(f):
    """f = file caricato o scelto dall'archivio → {id, nome, mime}."""
    dati = f.getvalue()
    nome = getattr(f, "name", "file")
    mime = getattr(f, "type", None) or "application/octet-stream"
    return cp_file_salva(dati, nome, mime)


def sc_file_mostra(rif, chiave):
    """Anteprima o scarico di un file salvato."""
    dati = cp_file_leggi(rif)
    if not dati:
        st.caption(f"⚠️ {sc_esc(rif.get('nome'))}: file non trovato")
        return
    if str(rif.get("mime", "")).startswith("image/"):
        st.image(dati, caption=rif.get("nome"), width="stretch")
    st.download_button("⬇️ " + str(rif.get("nome", "file"))[:40], dati, file_name=rif.get("nome", "file"), mime=rif.get("mime") or "application/octet-stream",
                       key=chiave, width="stretch")


# ---------------------------------------------------------------------------------------------------------------------
# i due bottoni sotto il campanellino + gli interruttori neon
# ---------------------------------------------------------------------------------------------------------------------
SC_CSS = """<style>
[class*="st-key-sc_barra"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.5rem !important}
[class*="st-key-sc_barra"] [data-testid="stColumn"]{min-width:0 !important}
[class*="st-key-sc_barra"] button{border-radius:16px !important;min-height:3.1rem !important;border:2px solid rgba(110,200,255,.55) !important;
 background:linear-gradient(135deg,#0f2a4a,#123b63) !important}
[class*="st-key-sc_barra"] button p{font-weight:800 !important;font-size:.95rem !important;line-height:1.15 !important}
[class*="st-key-sc_tasti_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.4rem !important}
[class*="st-key-sc_tasti_"] [data-testid="stColumn"]{min-width:0 !important}
[class*="st-key-sc_tasti_"] a{font-size:.8rem !important;padding:.25rem .3rem !important;min-height:2.3rem !important}
/* gli INTERRUTTORI: voce accesa = neon che pulsa; le altre = spente, come un interruttore */
[data-testid="stButtonGroup"] button[role="radio"]{transition:all .25s ease;border-radius:999px !important}
[data-testid="stButtonGroup"] button[role="radio"][aria-checked="false"]{background:#0a0e18 !important;border:1px solid rgba(255,255,255,.14) !important;
 box-shadow:inset 0 3px 7px rgba(0,0,0,.75) !important;opacity:.62;filter:grayscale(.55)}
[data-testid="stButtonGroup"] button[role="radio"][aria-checked="false"] p{color:#7d8798 !important;font-weight:500 !important}
[data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"]{background:rgba(0,229,255,.16) !important;border:2px solid #20e6ff !important;
 box-shadow:0 0 8px #20e6ff,0 0 18px rgba(32,230,255,.75),inset 0 0 10px rgba(32,230,255,.45) !important;opacity:1;animation:sc-neon 1.7s ease-in-out infinite}
[data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"] p{color:#bff8ff !important;font-weight:800 !important;text-shadow:0 0 8px #20e6ff}
@keyframes sc-neon{0%,100%{box-shadow:0 0 6px #20e6ff,0 0 14px rgba(32,230,255,.6),inset 0 0 8px rgba(32,230,255,.35)}
 50%{box-shadow:0 0 12px #6ff3ff,0 0 28px rgba(32,230,255,.95),inset 0 0 14px rgba(32,230,255,.6)}}
@media (prefers-reduced-motion:reduce){[data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"]{animation:none}}
</style>"""


def sc_barra(corrente):
    if corrente in SC_ESCLUSE:
        return
    st.markdown(SC_CSS, unsafe_allow_html=True)
    st.session_state["_sc_sez_corr"] = corrente
    prossimi = 0
    try:
        if "apn_prossimi" in globals():
            prossimi = apn_prossimi(corrente)
    except Exception:
        pass
    with st.container(key="sc_barra"):
        c1, c2 = st.columns(2, gap="small")
        if c1.button("📞 Numeri utili", key="sc_nu_" + corrente, width="stretch") and "rbu_apri" in globals():
            rbu_apri(corrente)
        if c2.button("📅 Appuntamenti" + (f" ({prossimi})" if prossimi else ""), key="sc_ap_" + corrente, width="stretch") and "apn_apri" in globals():
            apn_apri(corrente)
    if not st.session_state.pop("_sc_aperto_ora", False):
        _sc_riapri(corrente)


if "_sc_nav_prima" not in globals() and "nav_pagine" in globals():
    _sc_nav_prima = nav_pagine

    def nav_pagine(corrente):                                          # noqa: F811
        r = _sc_nav_prima(corrente)
        try:
            sc_barra(corrente)
        except Exception as _e:
            st.caption(f"(bottoni numeri utili/appuntamenti non disponibili: {type(_e).__name__})")
        return r
