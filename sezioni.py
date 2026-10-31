# -*- coding: utf-8 -*-
"""SEZIONI VISIBILI: l'amministratore sceglie, persona per persona, quali sezioni dell'app può usare.

Come funziona (il modulo non cambia nessuna funzione esistente: «avvolge» tre punti già presenti):
  • nella scheda Utenti, sotto ogni persona, c'è «Sezioni che questa persona può usare» (Salute, I miei documenti, Archivio, Casa, Utilità). Le sezioni tolte
    vengono scritte in utenti.json (sezioni_nascoste). La Dispensa è sempre visibile. L'amministratore (il capo famiglia) vede sempre tutto.
  • la Home non mostra le icone delle sezioni tolte; le frecce ← → in alto le saltano;
  • il controllo vero è sul server: anche chi arrivasse a una sezione tolta (un vecchio segnalibro, una sessione già aperta) vede solo un avviso e un pulsante per tornare.
Attenzione: l'Archivio mostra anche i file della Salute (bugiardini, foto, documenti). Chi non deve vedere la Salute di solito non deve vedere nemmeno l'Archivio.
Caricato da app_dispensa.py dopo casa.py."""
import streamlit as st

SV_SEZIONI = {"salute": "🩺 Salute", "documenti": "📁 I miei documenti", "archivio": "🗂️ Archivio", "casa": "🏡 Casa", "utilita": "🧰 Utilità"}
_SV_DA_SEZIONE_HOME = {None: "salute", "documenti": "documenti", "archivio": "archivio", "trasferimento": "salute", "utilita": "utilita", "casa": "casa"}
_SV_ICONE_HOME = {"salute": "fa_icona", "documenti": "doc_icona", "utilita": "ut_icona", "casa": "casa_icona"}


def sv_da_utente(u):
    """Le sezioni nascoste di una persona, ripulite (solo nomi che esistono)."""
    return {s for s in ((u or {}).get("sezioni_nascoste") or []) if s in SV_SEZIONI} if isinstance((u or {}).get("sezioni_nascoste", []), list) else set()


def sv_nascoste():
    """Le sezioni che la persona collegata NON può usare. Il capo famiglia: nessuna."""
    sess = st.session_state.get("sess") or {}
    if not sess or sess.get("admin"):
        return set()
    try:
        u = next((x for x in leggi_utenti() if x.get("id") == sess.get("uid")), None)
    except Exception:
        return set()
    return sv_da_utente(u)


def sv_selettore(u):
    """Nella scheda Utenti (amministratore): le sezioni che una persona può usare. Si salva appena cambi."""
    nasc = sv_da_utente(u)
    visibili = [s for s in SV_SEZIONI if s not in nasc]
    scelte = st.multiselect("Sezioni che questa persona può usare", list(SV_SEZIONI), default=visibili, key=f"sv_{u['id']}", format_func=lambda k: SV_SEZIONI[k],
                            help="La Dispensa c'è sempre. Togli quelle che questa persona non deve vedere. Attenzione: l'Archivio mostra anche i file della Salute.")
    nuove = sorted(s for s in SV_SEZIONI if s not in scelte)
    if nuove != sorted(nasc):
        def _imposta(d, uid=u["id"], val=nuove):
            for x in d.get("utenti", []):
                if x["id"] == uid:
                    x["sezioni_nascoste"] = val
        try:
            salva_file("utenti.json", _imposta, f"Sezioni visibili: {u['nome']}")
            st.rerun()
        except Exception as e:
            st.error(t("Non sono riuscito a salvare: {e}", e=e))


def sv_blocca(chiave):
    """Cosa vede chi arriva a una sezione che non può usare."""
    st.markdown("<div style='background:#fff3e0;border-radius:18px;padding:16px 18px;margin:12px 0;color:#4e342e;font-weight:700'>"
                f"🔒 La sezione «{SV_SEZIONI.get(chiave, chiave)}» non è disponibile per il tuo account.<br>"
                "<span style='font-weight:500'>Se pensi che sia un errore, chiedi a chi gestisce l'app.</span></div>", unsafe_allow_html=True)
    if st.button("← Torna alla dispensa", key="sv_torna", width="stretch"):
        st.session_state.pop("sezione_home", None)
        st.session_state["farmacia_aperta"] = False
        st.rerun()


# ---- 1) la pagina: lo smistamento delle sezioni controlla il permesso prima di tutto
if "schermata_farmacia" in globals() and "_sv_schermata_prima" not in globals():
    _sv_schermata_prima = schermata_farmacia

    def schermata_farmacia():                                       # noqa: F811
        chiave = _SV_DA_SEZIONE_HOME.get(st.session_state.get("sezione_home"), "salute")
        if chiave in sv_nascoste():
            return sv_blocca(chiave)
        return _sv_schermata_prima()

# ---- 2) le frecce ← → saltano le sezioni nascoste
if "nav_barra" in globals() and "_sv_nav_prima" not in globals():
    _sv_nav_prima = nav_barra

    def nav_barra(sezione):                                         # noqa: F811
        nasc = sv_nascoste()
        if not nasc:
            return _sv_nav_prima(sezione)
        originale = list(SEZIONI_NAV)
        SEZIONI_NAV[:] = [s for s in originale if s not in nasc or s == sezione]
        try:
            return _sv_nav_prima(sezione)
        finally:
            SEZIONI_NAV[:] = originale

# ---- 3) la Home: niente icone per le sezioni nascoste (si toglie la colonna intera dell'icona)
if "casa_css" in globals() and "_sv_casa_css_prima" not in globals():
    _sv_casa_css_prima = casa_css

    def casa_css():                                                 # noqa: F811
        css = _sv_casa_css_prima()
        nasc = sv_nascoste()
        if not nasc:
            return css
        regole = ",".join(f".st-key-azioni_icone [data-testid='stColumn']:has(.st-key-{_SV_ICONE_HOME[s]})" for s in nasc if s in _SV_ICONE_HOME)
        return css + (regole + "{display:none !important}" if regole else "")

if "casa_pulsante" in globals() and "_sv_casa_pulsante_prima" not in globals():
    _sv_casa_pulsante_prima = casa_pulsante

    def casa_pulsante():                                            # noqa: F811
        if "casa" in sv_nascoste():
            return False
        return _sv_casa_pulsante_prima()

# ---- 4) la guida spiega la funzione
if "_GUIDE" in globals() and "_ID_GUIDA" in globals() and "dispensa" in _GUIDE:
    _GUIDE["dispensa"].append((
        "🔒 Nascondere delle sezioni a una persona",
        """L'amministratore può decidere **quali sezioni può usare ogni persona**.
1. Apri la dispensa e tocca la scheda **Utenti**.
2. Sotto il nome della persona trovi **«Sezioni che questa persona può usare»**, con Salute, I miei documenti, Archivio, Casa e Utilità.
3. **Togli** quelle che non deve vedere (tocca la crocetta accanto al nome). Si salva da solo.
4. Nella sua Home spariscono le icone e le frecce in alto le saltano.

La **Dispensa** c'è sempre, e tu, che sei l'amministratore, vedi tutto. Attenzione: l'**Archivio** mostra anche i file della Salute, quindi chi non deve vedere la Salute di solito non deve vedere nemmeno l'Archivio.""",
        "nascondere sezioni persona utente permessi visibili vedere salute casa archivio utilità bloccare account"))
    _ID_GUIDA["dispensa"].append("d_sezioni")
