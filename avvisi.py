# -*- coding: utf-8 -*-
"""Avviso all'apertura: finestra con foto e nome dei prodotti scaduti / in scadenza entro 1 e 2 mesi.
Ogni sezione ha i suoi suoni (suona quello dell'urgenza maggiore di ciascuna sezione):
  adulti:  sirena veloce (scaduti), doppio din-don (1 mese), dolce din (2 mesi)
  neonati: pianto di due bebe' (scaduti), bimbo (1 mese), bimba (2 mesi)
  animali: ruggito di leone (scaduti), cane (1 mese), gatto (2 mesi)
I suoni sono sintetici; se in suoni/ ci sono file veri (bimba.mp3, gatto.wav...) l'app usa quelli."""
import wave

try:
    import soundfile as _sf
except Exception:          # senza soundfile funzionano solo i file .wav
    _sf = None

SR_SUONO = 22050
_rng = np.random.default_rng(7)


# ---------------------------------------------------------------------
# Strumenti per sintetizzare i suoni
# ---------------------------------------------------------------------
def _pausa(durata):
    return np.zeros(int(SR_SUONO * durata))


def _curva(punti, n):
    """Curva liscia che passa per i valori dati, lunga n campioni."""
    if np.ndim(punti) == 0:
        return np.full(n, float(punti))
    return np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(punti)), np.asarray(punti, float))


def _inviluppo(n, attacco, rilascio):
    e = np.ones(n)
    a, r = min(n // 2, max(1, int(SR_SUONO * attacco))), min(n // 2, max(1, int(SR_SUONO * rilascio)))
    e[:a] = np.linspace(0, 1, a)
    e[n - r:] *= np.linspace(1, 0, r)
    return e


def _voce(durata, f0, formanti, rumore=0.0, vibrato=(0.0, 6.0), armoniche=50, pendenza=1.0, tremolo=(0.0, 0.0),
          jitter=0.0, aria=6):
    """Voce sintetica: tante armoniche di un tono (f0) filtrate da 'formanti' = [(frequenza, larghezza, peso), ...]."""
    n = int(SR_SUONO * durata)
    tt = np.arange(n) / SR_SUONO
    f = _curva(f0, n) * (1 + vibrato[0] * np.sin(2 * np.pi * vibrato[1] * tt))
    if jitter:
        passo = np.convolve(_rng.normal(0, 1, n), np.ones(900) / 900, "same")
        f = f * (1 + jitter * passo / (np.abs(passo).max() + 1e-9))
    fase = 2 * np.pi * np.cumsum(f) / SR_SUONO
    forme = [(_curva(fr, n), bw, g) for fr, bw, g in formanti]
    out = np.zeros(n)
    for k in range(1, armoniche + 1):
        fk = k * f
        peso = 0.04 + sum(g * np.exp(-0.5 * ((fk - fr) / bw) ** 2) for fr, bw, g in forme)
        out += np.where(fk < 0.45 * SR_SUONO, peso / k ** pendenza, 0) * np.sin(k * fase)
    if rumore:
        soffio = np.convolve(_rng.normal(0, 1, n), np.ones(aria) / aria, "same")      # piu' 'aria' e' alto, piu' il fruscio e' grave
        soffio = soffio / (np.abs(soffio).max() + 1e-9)
        out = out / (np.abs(out).max() + 1e-9) + rumore * soffio
    if tremolo[0]:
        out = out * (1 - tremolo[0] + tremolo[0] * np.sin(2 * np.pi * tremolo[1] * tt) ** 2)
    return out / (np.abs(out).max() + 1e-9)


def _livello(x, picco):
    return picco * x / (np.abs(x).max() + 1e-9)


# ---------------------------------------------------------------------
# Adulti (quelli di prima)
# ---------------------------------------------------------------------
def _tono(freq, durata, volume, decadimento=False):
    n = int(SR_SUONO * durata)
    tt = np.arange(n) / SR_SUONO
    onda = np.sin(2 * np.pi * freq * tt) + (0.3 * np.sin(2 * np.pi * 2 * freq * tt) if decadimento else 0)
    inviluppo = np.exp(-4.0 * tt / durata) if decadimento else np.ones(n)
    a, r = max(1, int(SR_SUONO * 0.008)), max(1, int(SR_SUONO * 0.03))
    inviluppo[:a] *= np.linspace(0, 1, a)
    inviluppo[-r:] *= np.linspace(1, 0, r)
    return volume * onda * inviluppo / (1.3 if decadimento else 1)


def suono_scaduti():
    """Sirena veloce, acuta e forte (alterna due note)."""
    parti = []
    for i in range(12):
        parti += [_tono(1250 if i % 2 == 0 else 880, 0.13, 0.85), _pausa(0.02)]
    return np.concatenate(parti)


def suono_rossi():
    """'Din-don' piu' lento e dolce, ripetuto due volte."""
    parti = []
    for _ in range(2):
        parti += [_tono(660, 0.35, 0.5, True), _pausa(0.05), _tono(880, 0.55, 0.5, True), _pausa(0.35)]
    return np.concatenate(parti)


def suono_arancioni():
    """Un solo 'din' basso e dolce, lento, ripetuto due volte."""
    parti = []
    for _ in range(2):
        parti += [_tono(587, 0.75, 0.4, True), _pausa(0.45)]
    return np.concatenate(parti)


# ---------------------------------------------------------------------
# Neonati: bimba (2 mesi), bimbo (1 mese), entrambi i bebe' (scaduti)
# ---------------------------------------------------------------------
def suono_bimba():
    """Bimba: due dolci 'aaa-uuu' di un bebe' contento (voce acuta e leggera)."""
    parti = []
    for _ in range(2):
        x = _voce(0.5, [500, 640, 590, 520], [([850, 650, 480], 220, 1.0), ([2500, 2100, 1300], 350, 0.7)],
                  rumore=0.02, vibrato=(0.025, 6))
        parti += [x * _inviluppo(len(x), 0.08, 0.2), _pausa(0.25)]
    return _livello(np.concatenate(parti), 0.5)


def suono_bimbo():
    """Bimbo: tre piccoli lamenti 'eh-eh-eh' (voce piu' bassa e nasale, un po' piu' insistente)."""
    parti = []
    for i in range(3):
        x = _voce(0.32, [380 + 25 * i, 470 + 25 * i, 420 + 25 * i], [(560, 150, 1.0), (1750, 260, 0.8), (2900, 400, 0.4)],
                  rumore=0.05, vibrato=(0.03, 7), tremolo=(0.35, 12))
        parti += [x * _inviluppo(len(x), 0.03, 0.12), _pausa(0.16)]
    return _livello(np.concatenate(parti), 0.7)


def _pianto(base, rasp):
    parti = []
    for i in range(2):
        x = _voce(0.8, [base * 0.85, base * 1.35, base * 1.2, base * (1.0 - 0.1 * i)],
                  [([1000, 1250, 1100], 320, 1.0), (2900, 520, 0.9), (4300, 700, 0.4)],
                  rumore=rasp, vibrato=(0.035, 5.5), tremolo=(0.25, 9))
        parti += [x * _inviluppo(len(x), 0.05, 0.3), _pausa(0.25)]
    return np.concatenate(parti)


def suono_bebe_scaduti():
    """Pianto di tutti e due i bebe' (bimba piu' acuta, bimbo piu' grave) che si sovrappongono."""
    a, b = _pianto(600, 0.06), _pianto(430, 0.12)
    out = np.zeros(max(len(a), len(b) + int(SR_SUONO * 0.12)))
    out[:len(a)] += a
    out[int(SR_SUONO * 0.12):int(SR_SUONO * 0.12) + len(b)] += 0.9 * b
    return _livello(out, 0.9)


# ---------------------------------------------------------------------
# Animali: gatto (2 mesi), cane (1 mese), leone (scaduti)
# ---------------------------------------------------------------------
def suono_gatto():
    """Gatto: due 'miaooo'."""
    parti = []
    for d, alt in ((0.95, 1.0), (0.75, 0.9)):
        x = _voce(d, [430 * alt, 540 * alt, 780 * alt, 700 * alt, 520 * alt, 410 * alt],
                  [([650, 800, 780, 620], 200, 1.0), ([1300, 1900, 2400, 1750, 1300], 280, 0.85), (3200, 450, 0.3)],
                  rumore=0.04, vibrato=(0.02, 7))
        forma = np.sin(np.linspace(0, np.pi, len(x))) ** 0.6
        parti += [x * forma * _inviluppo(len(x), 0.05, 0.15), _pausa(0.3)]
    return _livello(np.concatenate(parti), 0.5)


def suono_cane():
    """Cane: tre abbai 'bau bau bau'."""
    parti = []
    for i, (f_i, f_f, d) in enumerate(((560, 330, 0.2), (520, 300, 0.2), (480, 270, 0.26))):
        x = _voce(d, [f_i, f_f], [(700, 180, 1.0), (1150, 250, 0.8), (2200, 500, 0.35)], rumore=0.3, jitter=0.02, aria=10)
        tt = np.arange(len(x)) / SR_SUONO
        x = x * (1 - np.exp(-tt / 0.004)) * np.exp(-tt / (0.09 + 0.02 * i))
        parti += [x, _pausa(0.14)]
    return _livello(np.concatenate(parti), 0.75)


def suono_leone():
    """Leone: ruggito lungo e roco, con il 'grugnito' finale."""
    x = _voce(2.4, [90, 135, 120, 90, 70, 60], [([520, 600, 480], 260, 1.0), (1100, 350, 0.9), (1900, 500, 0.45)],
              rumore=0.5, pendenza=0.8, tremolo=(0.55, 24), jitter=0.07, armoniche=45, aria=28)
    forma = np.interp(np.linspace(0, 1, len(x)), [0, 0.08, 0.3, 0.7, 1], [0.1, 1.0, 0.95, 0.7, 0.0])
    return _livello(x * forma, 0.95)


# ---------------------------------------------------------------------
# Quale suono per quale situazione
# ---------------------------------------------------------------------
STATI_AVVISO = ("scaduto", "rosso", "arancione")          # dal piu' urgente al meno urgente
SUONI = {   # (sezione, stato) -> (nome del file eventuale, funzione che lo sintetizza, nome mostrato)
    ("adulti", "scaduto"): ("adulti_scaduto", suono_scaduti, "sirena veloce"),
    ("adulti", "rosso"): ("adulti_1mese", suono_rossi, "doppio din-don"),
    ("adulti", "arancione"): ("adulti_2mesi", suono_arancioni, "dolce din"),
    ("neonati", "scaduto"): ("bebe", suono_bebe_scaduti, "pianto di due bebè"),
    ("neonati", "rosso"): ("bimbo", suono_bimbo, "bimbo"),
    ("neonati", "arancione"): ("bimba", suono_bimba, "bimba"),
    ("animali", "scaduto"): ("leone", suono_leone, "ruggito di leone"),
    ("animali", "rosso"): ("cane", suono_cane, "cane che abbaia"),
    ("animali", "arancione"): ("gatto", suono_gatto, "gatto che miagola"),
}


def _file_suono(nome):
    for est in (".wav", ".mp3", ".ogg", ".flac"):
        p = os.path.join(_cartella, "suoni", nome + est)
        if os.path.isfile(p):
            return p
    return None


def _leggi_file_suono(percorso, massimo=4.0):
    """Legge un file audio vero (wav; con soundfile anche mp3, ogg, flac) e lo porta al formato dell'app."""
    if _sf is not None:
        dati, sr = _sf.read(percorso, dtype="float32", always_2d=True)
        mono = dati.mean(axis=1)
    else:
        with wave.open(percorso, "rb") as w:
            sr, canali = w.getframerate(), w.getnchannels()
            mono = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype("float32") / 32768
            mono = mono.reshape(-1, canali).mean(axis=1)
    mono = mono[: int(sr * massimo)]
    n = max(1, int(len(mono) * SR_SUONO / sr))
    x = np.interp(np.linspace(0, len(mono) - 1, n), np.arange(len(mono)), mono)
    x = x * _inviluppo(len(x), 0.01, 0.15)
    return x


def suono_per(sezione, stato):
    """Il suono (array) per una sezione e uno stato: il file vero se c'e', altrimenti quello sintetico."""
    nome, fun, _ = SUONI[(sezione, stato)]
    p = _file_suono(nome)
    if p:
        try:
            return _leggi_file_suono(p)
        except Exception:
            pass
    return fun()


@st.cache_data(show_spinner=False)
def suono_avviso(situazioni):
    """File WAV con i suoni delle situazioni date: ((sezione, stato), ...)."""
    parti = []
    for sezione, stato in situazioni:
        parti += [suono_per(sezione, stato), _pausa(0.45)]
    pcm = (np.clip(np.concatenate(parti), -1, 1) * 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR_SUONO)
        w.writeframes(pcm)
    return buf.getvalue()


def situazioni_presenti():
    """Per ogni sezione, la situazione piu' urgente tra i prodotti da controllare."""
    trovate = {}
    for stato, righe in (("scaduto", scaduti), ("rosso", rossi), ("arancione", arancioni)):
        for r in righe:
            trovate.setdefault(categoria_di(r), set()).add(stato)
    return tuple((c, next(s for s in STATI_AVVISO if s in trovate[c])) for c in CATEGORIE if c in trovate)


# ---------------------------------------------------------------------
# Menu a sinistra e finestra dell'avviso
# ---------------------------------------------------------------------
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
        _wav = suono_avviso(situazioni_presenti())
        try:
            import streamlit.components.v1 as _comp
            _comp.html(player_html(_wav), height=96)
        except Exception:
            st.audio(_wav, format="audio/wav", autoplay=True)
    for titolo, righe, classe in (("⚫ " + t("Scaduti"), scaduti, "s-scaduti"), ("🔴 " + t("Scadono entro 1 mese"), rossi, "s-rossi"),
                                  ("🟠 " + t("Scadono entro 2 mesi"), arancioni, "s-arancio")):
        if not righe:
            continue
        st.markdown(intestazione_sezione(titolo, len(righe), classe), unsafe_allow_html=True)
        for r in righe:
            c1, c2 = st.columns([1, 4])
            src = src_sicuro(r.get("immagine") or "")
            if src:
                c1.image(src, width=64)
            else:
                c1.markdown("<div style='font-size:42px'>🥫</div>", unsafe_allow_html=True)
            stato, giorni = stato_scadenza(r.get("scadenza"), data_oggi)
            c2.markdown(f"**{r.get('nome', '')}**" + (f" · {r['marca']}" if r.get("marca") else ""))
            c2.markdown(f"<div class='chip-info'>📦 {html.escape(descrivi([r]))} · {testo_giorni(stato, giorni)} · {data_it(r['scadenza'])}</div>"
                        f"<span class='scadenza' style='--c:{COLORI[stato]}'>{testo_giorni(stato, giorni)}</span>",
                        unsafe_allow_html=True)
            if st.button(t("Elimina"), icon=":material/delete:", key="cest_av_" + r["id"], width="stretch"):
                st.session_state["elimina_dopo"] = [r["id"]]
                st.rerun()
    with st.expander("🔊 " + t("Cosa significano i suoni?")):
        st.caption(t("Per ogni sezione suona il suono dell'urgenza maggiore."))
        for c in CATEGORIE:
            n_s, n_r, n_a = (t(SUONI[(c, s)][2]) for s in STATI_AVVISO)
            st.markdown(f"**{nome_cat(c)}:** {n_s} = {t('Scaduti')} · {n_r} = {t('Entro 1 mese')} · {n_a} = {t('Entro 2 mesi')}")
    st.caption(t("Se non lo senti, premi play (il telefono può bloccare il suono finché non tocchi lo schermo)."))
    if st.button(t("Chiudi"), type="primary", key="chiudi_avviso"):
        st.rerun()


if (scaduti or rossi or arancioni) and not st.session_state.get("avviso_mostrato"):
    st.session_state["avviso_mostrato"] = True
    st.dialog("⚠️ " + t("Prodotti da controllare"))(_elenco_avviso)()

if st.session_state.get("elimina_dopo"):          # "Elimina" premuto nell'avviso: si apre la finestra di eliminazione
    apri_elimina(st.session_state.pop("elimina_dopo"))
