# -*- coding: utf-8 -*-
"""Avviso all'apertura: finestra con foto e nome dei prodotti scaduti / in scadenza entro 1 e 2 mesi, con tre suoni diversi
(sirena veloce = scaduti, doppio din-don = rossi, dolce din = arancioni). Il suono si puo' spegnere dal menu a sinistra."""
import wave

SR_SUONO = 22050


def _tono(freq, durata, volume, decadimento=False):
    n = int(SR_SUONO * durata)
    tt = np.arange(n) / SR_SUONO
    onda = np.sin(2 * np.pi * freq * tt) + (0.3 * np.sin(2 * np.pi * 2 * freq * tt) if decadimento else 0)
    inviluppo = np.exp(-4.0 * tt / durata) if decadimento else np.ones(n)
    a, r = max(1, int(SR_SUONO * 0.008)), max(1, int(SR_SUONO * 0.03))
    inviluppo[:a] *= np.linspace(0, 1, a)
    inviluppo[-r:] *= np.linspace(1, 0, r)
    return volume * onda * inviluppo / (1.3 if decadimento else 1)


def _pausa(durata):
    return np.zeros(int(SR_SUONO * durata))


def suono_scaduti():
    """Urgente: sirena veloce, acuta e forte (alterna due note)."""
    parti = []
    for i in range(12):
        parti += [_tono(1250 if i % 2 == 0 else 880, 0.13, 0.85), _pausa(0.02)]
    return np.concatenate(parti)


def suono_rossi():
    """Premura media: 'din-don' piu' lento e dolce, ripetuto due volte."""
    parti = []
    for _ in range(2):
        parti += [_tono(660, 0.35, 0.5, True), _pausa(0.05), _tono(880, 0.55, 0.5, True), _pausa(0.35)]
    return np.concatenate(parti)


def suono_arancioni():
    """Attenzione lieve: un solo 'din' basso e dolce, lento, ripetuto due volte."""
    parti = []
    for _ in range(2):
        parti += [_tono(587, 0.75, 0.4, True), _pausa(0.45)]
    return np.concatenate(parti)


@st.cache_data(show_spinner=False)
def suono_avviso(con_scaduti, con_rossi, con_arancioni):
    parti = []
    if con_scaduti:
        parti += [suono_scaduti(), _pausa(0.5)]
    if con_rossi:
        parti += [suono_rossi(), _pausa(0.4)]
    if con_arancioni:
        parti += [suono_arancioni()]
    pcm = (np.clip(np.concatenate(parti), -1, 1) * 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR_SUONO)
        w.writeframes(pcm)
    return buf.getvalue()


# --- menu a sinistra: suono si/no e riapertura dell'elenco ---
with st.sidebar:
    st.divider()
    _suono_ok = st.checkbox("🔔 " + t("Suono di avviso"), value=bool(dati.get("suono", True)), key="suono_attivo")
    if _suono_ok != bool(dati.get("suono", True)):
        try:
            salva(lambda d: d.__setitem__("suono", bool(_suono_ok)), "Suono")
        except Exception:
            pass
    if scaduti or rossi or arancioni:
        if st.button("⚠️ " + t("Prodotti da controllare")):
            st.session_state["avviso_mostrato"] = False
            st.rerun()


def _elenco_avviso():
    if _suono_ok:
        st.audio(suono_avviso(bool(scaduti), bool(rossi), bool(arancioni)), format="audio/wav", autoplay=True)
    for titolo, righe in (("⚫ " + t("Scaduti"), scaduti), ("🔴 " + t("Scadono entro 1 mese"), rossi),
                          ("🟠 " + t("Scadono entro 2 mesi"), arancioni)):
        if not righe:
            continue
        st.markdown(f"**{titolo} ({len(righe)})**")
        for r in righe:
            c1, c2 = st.columns([1, 4])
            src = src_sicuro(r.get("immagine") or "")
            if src:
                c1.image(src, width=64)
            else:
                c1.markdown("<div style='font-size:42px'>🥫</div>", unsafe_allow_html=True)
            stato, giorni = stato_scadenza(r.get("scadenza"), data_oggi)
            c2.markdown(f"**{r.get('nome', '')}**" + (f" · {r['marca']}" if r.get("marca") else ""))
            c2.caption(f"📦 {descrivi([r])} · {testo_giorni(stato, giorni)} · {data_it(r['scadenza'])}")
    st.caption(t("Suono: sirena veloce = prodotti scaduti, doppio din-don = scadono entro 1 mese, dolce din = scadono entro 2 mesi. "
                 "Se non lo senti, premi play (il telefono può bloccare il suono finché non tocchi lo schermo)."))
    if st.button(t("Chiudi"), type="primary", key="chiudi_avviso"):
        st.rerun()


if (scaduti or rossi or arancioni) and not st.session_state.get("avviso_mostrato"):
    st.session_state["avviso_mostrato"] = True
    st.dialog("⚠️ " + t("Prodotti da controllare"))(_elenco_avviso)()
