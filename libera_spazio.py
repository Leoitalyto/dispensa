# -*- coding: utf-8 -*-
"""LIBERA SPAZIO — dopo aver archiviato un file, l'app propone di cancellare l'ORIGINALE dal telefono o dal computer.

Cosa è possibile davvero (i browser proteggono i file dell'utente):
• COMPUTER (Chrome, Edge): l'app può cancellare il file originale, ma solo se lo scegli tu e dai il permesso («🗑️ Elimina dal computer»).
• TELEFONO (Android/iPhone): un sito NON può cancellare file dal telefono, nemmeno con il permesso. L'app allora ti dice il NOME e il PESO del file, ti spiega in una riga dove cancellarlo
  e prova ad aprire i file del telefono con un tocco (su alcuni telefoni funziona, su altri no).
Il promemoria compare in TUTTE le sezioni (Casa, Lavoro, Salute, Archivio…) appena un file è stato archiviato; si può chiudere o spegnere per sempre da Utilità → Aspetto dell'app.
Caricato per ultimo da app_dispensa.py (avvolge le funzioni di Casa e di Salute senza modificarle)."""
import html as _html_ls
import json as _json_ls

import streamlit as st

_LS_JS = r"""
(function () {
  var w = window, doc = document;
  if (w.__liberaSpazio) return;
  w.__liberaSpazio = true;
  function avvisa(t, errore) {
    var el = doc.querySelector('[data-ls-msg]');
    if (el) { el.textContent = t; el.style.color = errore ? '#b71c1c' : '#0f766e'; el.style.display = 'block'; }
  }
  async function computer() {
    var mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');
    if (mobile || !w.showOpenFilePicker) { avvisa('Questo dispositivo non permette ai siti di cancellare i file. Apri «File» o «Galleria», cerca il file, tieni premuto e tocca Elimina.', true); return; }
    try {
      var hs = await w.showOpenFilePicker({multiple: false});
      var h = hs[0];
      if (!w.confirm('Eliminare DEFINITIVAMENTE «' + h.name + '» dal computer?\n\nL\'app lo ha già archiviato.')) { avvisa('Annullato: non ho toccato niente.'); return; }
      var perm = await h.requestPermission({mode: 'readwrite'});
      if (perm !== 'granted') { avvisa('Permesso negato: il file non è stato toccato.', true); return; }
      if (typeof h.remove === 'function') { await h.remove(); avvisa('✅ «' + h.name + '» eliminato dal computer.'); }
      else { avvisa('Questo browser non permette di eliminarlo da qui: cancellalo dalla cartella del computer.', true); }
    } catch (e) {
      if (e && e.name === 'AbortError') avvisa('Annullato: non ho toccato niente.');
      else avvisa('Non sono riuscito: ' + (e && e.message ? e.message : e), true);
    }
  }
  function telefono() {
    avvisa('Provo ad aprire i file del telefono… se non si apre niente, vai in «File» o «Galleria», cerca il file, tieni premuto e tocca Elimina.');
    try { w.location.href = 'intent:#Intent;action=android.intent.action.VIEW_DOWNLOADS;end'; } catch (e) {}
  }
  doc.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('[data-ls-azione]') : null;
    if (!b) return;
    ev.preventDefault();
    var a = b.getAttribute('data-ls-azione');
    if (a === 'pc') computer(); else if (a === 'tel') telefono();
  }, true);
})();
"""

_LS_CSS = ("<style>.ls-card{border:2px solid #f59e0b;border-radius:16px;padding:12px 14px;margin:10px 0;background:linear-gradient(135deg,#fffbeb,#fef3c7);color:#3a2d00}"
           ".ls-card b{font-weight:800}.ls-riga{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 6px}"
           ".ls-btn{border-radius:12px;padding:11px 8px;text-align:center;font-weight:800;font-size:14px;color:#fff;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent}"
           ".ls-pc{background:linear-gradient(135deg,#c62828,#ef5350)}.ls-tel{background:linear-gradient(135deg,#1565c0,#42a5f5)}.ls-btn:active{transform:scale(.97)}"
           ".ls-msg{display:none;margin-top:6px;font-weight:700;font-size:13.5px}</style>")


def ls_attivo():
    """True se il promemoria è acceso (si spegne da Utilità → Aspetto dell'app)."""
    if "ls_on" not in st.session_state:
        try:
            d = carica_dati(crea_archivio(), st.session_state["percorso"])
            v = (d.get("impostazioni") or {}).get("libera_spazio", True)
        except Exception:
            v = True
        st.session_state["ls_on"] = bool(v)
    return bool(st.session_state["ls_on"])


def ls_ui_impostazione():
    """L'interruttore, in Utilità → Aspetto dell'app."""
    on = st.checkbox("🧹 Dopo ogni archiviazione, ricordami di cancellare il file originale dal telefono o dal computer", value=ls_attivo(), key="ls_on_scelta")
    if on != ls_attivo():
        st.session_state["ls_on"] = on
        try:
            def _fn(d, v=on):
                d.setdefault("impostazioni", {})["libera_spazio"] = v
            salva(_fn, "Aspetto: promemoria libera spazio")
        except Exception as e:
            st.warning(f"Non sono riuscito a ricordare la scelta: {e}")
        st.rerun()


def ls_ricorda(nome, quanti_byte):
    """Un file è arrivato dal dispositivo: me lo segno (nome e peso)."""
    st.session_state["ls_pendente"] = {"nome": str(nome or "documento"), "kb": float(quanti_byte or 0) / 1024.0, "archiviato": False}


def ls_segna_archiviato():
    p = st.session_state.get("ls_pendente")
    if p and not p.get("archiviato"):
        p["archiviato"] = True
        st.session_state["ls_pendente"] = p


def _ls_peso(kb):
    return f"{kb / 1024:.1f} MB".replace(".", ",") if kb >= 1024 else f"{max(1, round(kb))} KB"


def ls_inietta():
    """Manda alla pagina il programma dei due tasti (una volta per sessione)."""
    pagina = ("<script>(function(){"
              "function ok(x){try{return !!x.document.querySelector('[data-testid=\"stApp\"],.stApp,[data-testid=\"stAppViewContainer\"]')}catch(e){return false}}"
              "var P=window;if(!ok(P)){var c=window;for(var i=0;i<3&&c.parent&&c.parent!==c;i++){c=c.parent;if(ok(c)){P=c;break}}}"
              "var s=P.document.createElement('script');s.textContent=" + _json_ls.dumps(_LS_JS) + ";P.document.head.appendChild(s);s.parentNode.removeChild(s);})();</script>")
    if "pn_inietta_una_volta" in globals():
        pn_inietta_una_volta("liberaspazio", "1", pagina)
    else:
        try:
            st.html(pagina, unsafe_allow_javascript=True)
        except Exception:
            pass


def ls_banner():
    """Il promemoria «🧹 Libera spazio»: compare dopo che un file del dispositivo è stato archiviato."""
    p = st.session_state.get("ls_pendente")
    if not p or not p.get("archiviato") or not ls_attivo():
        return
    ls_inietta()
    nome, peso = _html_ls.escape(p["nome"]), _ls_peso(p["kb"])
    st.markdown(_LS_CSS + f"<div class='ls-card'><b>🧹 Libera spazio</b><br>Hai archiviato <b>«{nome}»</b> ({peso}). "
                f"L'originale è <b>ancora sul tuo dispositivo</b>: cancellalo per liberare spazio.<br>"
                f"<small>📱 <b>Telefono:</b> il browser non può cancellarlo da solo. Apri <b>Galleria</b> o <b>File</b>, cerca «{nome}», tieni premuto e tocca <b>Elimina</b>.<br>"
                f"💻 <b>Computer:</b> tocca il tasto rosso, scegli lo stesso file e confermi: lo cancello io.</small>"
                f"<div class='ls-riga'><div class='ls-btn ls-pc' role='button' tabindex='0' data-ls-azione='pc'>🗑️ Elimina dal computer</div>"
                f"<div class='ls-btn ls-tel' role='button' tabindex='0' data-ls-azione='tel'>📂 Apri i file del telefono</div></div>"
                f"<div class='ls-msg' data-ls-msg></div></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    if c1.button("✅ Fatto, grazie", key="ls_fatto", width="stretch"):
        st.session_state.pop("ls_pendente", None)
        st.rerun()
    if c2.button("🔕 Non ricordarmelo più", key="ls_mai", width="stretch"):
        st.session_state.pop("ls_pendente", None)
        st.session_state["ls_on"] = False
        try:
            salva(lambda d: d.setdefault("impostazioni", {}).__setitem__("libera_spazio", False), "Aspetto: promemoria libera spazio spento")
        except Exception:
            pass
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# Aggancio: si avvolgono le funzioni che RICEVONO un file dal dispositivo e quelle che lo ARCHIVIANO (senza modificarle)
# ---------------------------------------------------------------------------------------------------------------------
def _ls_avvolgi_ricezione():
    if "_ca_trasf_ricevi" in globals():
        _orig = _ca_trasf_ricevi

        def _ca_trasf_ricevi_ls(*a, **k):
            prima = st.session_state.get("ca_bozza_in")
            r = _orig(*a, **k)
            dopo = st.session_state.get("ca_bozza_in")
            if dopo and dopo is not prima and dopo.get("dati"):
                ls_ricorda(dopo.get("nome"), len(dopo["dati"]))
            return r
        globals()["_ca_trasf_ricevi"] = _ca_trasf_ricevi_ls
    if "_ca_ultimo_file" in globals():
        _orig2 = _ca_ultimo_file

        def _ca_ultimo_file_ls(candidati, chiave):
            fl = _orig2(candidati, chiave)
            if fl is not None:
                ident = f"{getattr(fl, 'file_id', '') or getattr(fl, 'name', '')}|{getattr(fl, 'size', '')}"
                if st.session_state.get("ls_ident") != ident:
                    st.session_state["ls_ident"] = ident
                    ls_ricorda(getattr(fl, "name", "documento"), getattr(fl, "size", 0))
            return fl
        globals()["_ca_ultimo_file"] = _ca_ultimo_file_ls


def _ls_avvolgi_archiviazione(nome_funzione):
    if nome_funzione not in globals():
        return
    _orig = globals()[nome_funzione]

    def _avvolta(*a, **k):
        try:
            r = _orig(*a, **k)
        except BaseException as e:
            if type(e).__name__ in ("RerunException", "StopException"):                  # l'archiviazione è finita e la pagina si ridisegna
                ls_segna_archiviato()
            raise
        ls_segna_archiviato()
        return r
    globals()[nome_funzione] = _avvolta


try:
    _ls_avvolgi_ricezione()
    _ls_avvolgi_archiviazione("_ca_archivia")
    _ls_avvolgi_archiviazione("_sp_archivia_docsan")
    _ls_avvolgi_archiviazione("_se_archivia")
except Exception:
    pass
