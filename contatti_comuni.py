# -*- coding: utf-8 -*-
"""Pezzi COMUNI a tutti i «badge» dei contatti (amministratore, casa, lavoro, medici…): una sola logica in tutta l'app.
  • cc_url(testo)           → indirizzo del sito pronto da aprire («idamministrazioni.it» diventa «https://idamministrazioni.it»)
  • cc_campo_sito(...)      → il campo «🌐 Sito web» da mettere in ogni modulo
  • cc_chiama(col, ...)     → il tasto «📞 Chiama»: se ci sono DUE numeri (fisso e cellulare) apre una scelta, se ce n'è uno chiama subito
  • cc_sito_pulsante(...)   → il tasto «🌐 Sito»
  • cc_riga_sito(url)       → la riga col sito dentro la scheda, cliccabile
Prefisso: cc_ . Nessuna chiave, nessun servizio esterno."""
import html as _cc_html
import re as _cc_re
import streamlit as st


def cc_cifre(n):
    """Solo cifre (e un + iniziale): quello che serve al telefono per comporre."""
    n = str(n or "").strip()
    return ("+" if n.startswith("+") else "") + _cc_re.sub(r"\D", "", n)


def cc_e_cellulare(n):
    """Italia: i cellulari iniziano con 3 (anche dopo +39 / 0039)."""
    d = _cc_re.sub(r"\D", "", str(n or ""))
    if d.startswith("0039"):
        d = d[4:]
    elif d.startswith("39") and len(d) > 10:
        d = d[2:]
    return d.startswith("3")


def cc_url(testo):
    """Rende pronto un sito scritto a mano. Vuoto o non valido → ''."""
    t = str(testo or "").strip()
    if not t or " " in t:
        return ""
    if _cc_re.match(r"^https?://\S+\.\S+", t, _cc_re.I):
        return t
    if _cc_re.match(r"^(www\.)?[\w-]+(\.[\w-]+)+(/\S*)?$", t, _cc_re.I):
        return "https://" + t
    return ""


def cc_campo_sito(valore="", chiave=None, etichetta="🌐 Sito web (facoltativo)"):
    """Il campo del sito, uguale in tutti i moduli."""
    return st.text_input(etichetta, value=valore or "", key=chiave, placeholder="es. www.nomesito.it",
                         help="Se lo scrivi, nella scheda compare il tasto «🌐 Sito» per aprirlo subito.")


def cc_riga_sito(sito):
    """Riga HTML col sito cliccabile (per le schede disegnate con st.markdown)."""
    u = cc_url(sito)
    if not u:
        return ""
    return f"🌐 <a href='{_cc_html.escape(u)}' target='_blank' rel='noopener'>{_cc_html.escape(str(sito).strip())}</a>"


def cc_sito_pulsante(col, sito, chiave, etichetta="🌐 Sito"):
    u = cc_url(sito)
    if u:
        col.link_button(etichetta, u, width="stretch", key=chiave)
        return True
    return False


def cc_numeri(fisso, cellulare):
    """Elenco dei numeri diversi: [(etichetta, numero scritto, numero per comporre)]."""
    voci, visti = [], set()
    for n in (fisso, cellulare):
        c = cc_cifre(n)
        if c and len(c.lstrip("+")) >= 3 and c not in visti:
            visti.add(c)
            voci.append(("📱 Cellulare" if cc_e_cellulare(n) else "☎️ Telefono fisso", str(n).strip(), c))
    return voci


def cc_chiama(col, chiave, fisso, cellulare=None, etichetta="📞 Chiama", chi=""):
    """Un solo numero → chiama subito. Due numeri → toccando «Chiama» si apre la scelta: telefono fisso o cellulare."""
    voci = cc_numeri(fisso, cellulare)
    if not voci:
        return False
    if len(voci) == 1:
        col.link_button(etichetta, "tel:" + voci[0][2], width="stretch", key=f"{chiave}_ch")
        return True
    with col.popover(etichetta, width="stretch"):
        st.markdown("**Quale numero chiami?**" + (f"  \n{_cc_html.escape(chi)}" if chi else ""))
        for i, (et, num, comp) in enumerate(voci):
            st.link_button(f"{et} · {num}", "tel:" + comp, width="stretch", key=f"{chiave}_ch{i}")
    return True


def cc_pulsanti(pulsanti, chiave, per_riga=3):
    """Disegna una fila di tasti. Ogni voce è (scritta, indirizzo) oppure (scritta, ("__chiama__", fisso, cellulare, chi))."""
    for i in range(0, len(pulsanti), per_riga):
        gruppo = pulsanti[i:i + per_riga]
        for j, (col, (et, url)) in enumerate(zip(st.columns(per_riga if len(gruppo) == per_riga else len(gruppo), gap="small"), gruppo)):
            if isinstance(url, tuple) and url and url[0] == "__chiama__":
                cc_chiama(col, f"{chiave}_{i + j}", url[1], url[2], et, url[3] if len(url) > 3 else "")
            else:
                col.link_button(et, url, width="stretch", key=f"{chiave}_{i + j}_b")
