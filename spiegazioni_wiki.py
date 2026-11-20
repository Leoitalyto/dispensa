# -*- coding: utf-8 -*-
"""📖 «COS'È?» — DUE RIGHE DI SPIEGAZIONE DA WIKIPEDIA (gratuita, senza chiave).

RICHIESTA (Leonardo, 20 novembre): fra le API gratuite, Wikipedia per spiegare in Salute che cos'è un esame, una malattia o un farmaco scritto in un referto
(es. «ecocolordoppler», «duloxetina»), con il link alla pagina completa.
• In Salute → Documenti sanitari e → Medicinali: la tendina «📖 Cos'è? Spiegazione semplice» con una casella: scrivi la parola, compaiono fino a 4 voci,
  tocchi quella giusta e leggi il riassunto, nella lingua dell'app (se la voce non c'è in quella lingua, in italiano).
• È un'informazione GENERALE: non è un parere medico (lo dice sempre sotto il riassunto).
LIMITI: Wikipedia chiede solo di presentarsi (nome dell'app nella richiesta) e di non esagerare; i risultati restano in memoria un giorno."""
import html as _wk_html
import urllib.parse as _wk_url

import requests as _wk_req
import streamlit as st

_WK_UA = {"User-Agent": "VitaMemo/1.0 (app familiare; https://github.com/Leoitalyto/dispensa)", "Accept": "application/json"}


def _wk_lg():
    lg = lingua() if "lingua" in globals() else "it"
    return lg if lg in ("it", "en", "es", "fr", "de", "ro", "ar", "pt") else "it"


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def wk_cerca(testo, lg="it"):
    """Le voci di Wikipedia per quella parola: [titolo] (fino a 4)."""
    try:
        r = _wk_req.get(f"https://{lg}.wikipedia.org/w/api.php", headers=_WK_UA, timeout=8,
                        params={"action": "query", "list": "search", "srsearch": testo, "srlimit": 4, "format": "json", "utf8": 1})
        return [x["title"] for x in (r.json().get("query") or {}).get("search", [])] if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def wk_riassunto(titolo, lg="it"):
    """{titolo, testo, link} oppure {}."""
    try:
        r = _wk_req.get(f"https://{lg}.wikipedia.org/api/rest_v1/page/summary/" + _wk_url.quote(titolo.replace(" ", "_"), safe=""), headers=_WK_UA, timeout=8)
        if r.status_code != 200:
            return {}
        j = r.json()
        return {"titolo": j.get("title") or titolo, "testo": (j.get("extract") or "").strip(),
                "link": ((j.get("content_urls") or {}).get("mobile") or (j.get("content_urls") or {}).get("desktop") or {}).get("page", "")}
    except Exception:
        return {}


def wk_pannello(chiave, esempio="es. ecocolordoppler, duloxetina, emocromo"):
    """La tendina «📖 Cos'è?»."""
    with st.expander("📖 Cos'è? Spiegazione semplice (Wikipedia)"):
        testo = st.text_input("Scrivi il nome di un esame, una malattia o un farmaco", key=f"wk_q_{chiave}", placeholder=esempio).strip()
        if not testo:
            st.caption("Trovi due righe di spiegazione e il link alla pagina completa. È un'informazione generale, non un parere medico.")
            return
        lg = _wk_lg()
        voci = wk_cerca(testo, lg)
        if not voci and lg != "it":
            lg = "it"
            voci = wk_cerca(testo, lg)
        if not voci:
            st.info("Non ho trovato niente con questa parola (o Wikipedia adesso non risponde). Prova a scriverla in un altro modo.")
            return
        scelta = st.radio("Quale voce?", voci, key=f"wk_v_{chiave}_{abs(hash(testo))}", horizontal=False) if len(voci) > 1 else voci[0]
        r = wk_riassunto(scelta, lg)
        if not r.get("testo"):
            st.info("Questa voce non ha un riassunto: aprila con il link.")
        else:
            st.markdown(f"<div style='border-left:4px solid #0f766e;padding:6px 10px;margin:6px 0'><b>{_wk_html.escape(r['titolo'])}</b><br>{_wk_html.escape(r['testo'][:900])}</div>",
                        unsafe_allow_html=True)
        link = r.get("link") or f"https://{lg}.wikipedia.org/wiki/" + _wk_url.quote(scelta.replace(" ", "_"))
        st.link_button("🌐 Apri la pagina completa su Wikipedia", link, width="stretch")
        st.caption("ℹ️ Informazione generale da Wikipedia: **non è un parere medico**. Per la tua situazione chiedi sempre al medico o al farmacista.")


# ---- dove compare: Salute → Documenti sanitari (sotto i documenti) e Salute → Medicinali (sotto l'elenco)
if "sp_modulo_docsan" in globals() and "_wk_docsan_prima" not in globals():
    _wk_docsan_prima = sp_modulo_docsan

    def sp_modulo_docsan(pid):                                                       # noqa: F811
        _wk_docsan_prima(pid)
        try:
            wk_pannello(f"ds_{pid}")
        except Exception:
            pass

if "_fa_elenco_medicinali" in globals() and "_wk_med_prima" not in globals():
    _wk_med_prima = _fa_elenco_medicinali

    def _fa_elenco_medicinali(f, pid, visibili, vista, oggi_):                      # noqa: F811
        r = _wk_med_prima(f, pid, visibili, vista, oggi_)
        try:
            wk_pannello(f"med_{pid}", "es. duloxetina, colecalciferolo, acido folico")
        except Exception:
            pass
        return r
