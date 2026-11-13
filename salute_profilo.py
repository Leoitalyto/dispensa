# -*- coding: utf-8 -*-
"""SALUTE · il PROFILO scelto RESTA scelto (per esempio quello di mamma).

IL DIFETTO: il selettore «👤 Profilo» è disegnato solo nella schermata principale di Salute. Appena si apre un modulo a tutta pagina (Scorte, Documenti sanitari, Parametri, Esenzioni…)
o si va in «I miei documenti», il selettore non c'è più e Streamlit DIMENTICA la scelta: al ritorno si riparte dal primo profilo, cioè quello di chi usa l'app. Su Android succede anche
quando il browser ricarica la pagina (per esempio dopo aver scattato una foto).
(Scoperto con la prova nel browser: il programma ricordava la persona giusta, ma il TELEFONO ricreava il campo sul primo nome e alla prima azione rimandava quello.)

LA CORREZIONE (nessun dato cambia):
• la scelta si ricorda anche FUORI dal campo (`fa_profilo_ric`) e si rimette al suo posto all'inizio delle schermate Salute e «I miei documenti»;
• il campo viene sempre disegnato con `index=` sulla persona ricordata (così anche il telefono riparte da lei);
• la scelta si scrive anche nell'indirizzo della pagina (?p=…): se la pagina viene ricaricata si riparte dalla stessa persona;
• un profilo che non esiste più (eliminato) si ignora: si riparte dal primo."""
import streamlit as st


def spf_ripristina():
    """Se Streamlit ha dimenticato il profilo, si rimette l'ultimo scelto (dalla memoria della sessione, altrimenti dall'indirizzo ?p=)."""
    if "fa_profilo" in st.session_state:
        return
    uid = (st.session_state.get("sess") or {}).get("uid")
    ric = st.session_state.get("fa_profilo_ric")
    ric = ric.get("pid") if isinstance(ric, dict) and ric.get("uid") == uid else None     # la scelta vale solo per chi l'ha fatta (sullo stesso telefono possono entrare più persone)
    if not ric:
        try:
            ric = st.query_params.get("p")
        except Exception:
            ric = None
    if ric:
        st.session_state["fa_profilo"] = str(ric)


if not getattr(st.selectbox, "_spf", False):                                              # una volta sola per tutta la vita del programma
    def _spf_fabbrica(originale):
        def _spf_selectbox(label, options, *args, **kwargs):
            if kwargs.get("key") == "fa_profilo" and "index" not in kwargs and not args:
                # IL PUNTO CHIAVE: quando il campo torna sullo schermo dopo un modulo, il TELEFONO lo ricrea e lo mostra sul primo nome (il tuo) anche se il programma ricorda un'altra persona;
                # alla prima azione successiva il telefono rimanda «primo nome» e la scelta si perde. Per questo ogni volta si dice al campo da quale persona partire.
                options = list(options)
                att = st.session_state.get("fa_profilo")
                ric = st.session_state.get("fa_profilo_ric")
                ric = ric.get("pid") if isinstance(ric, dict) and ric.get("uid") == (st.session_state.get("sess") or {}).get("uid") else None
                voluta = att if att in options else (ric if ric in options else None)
                if voluta is not None:
                    kwargs["index"] = options.index(voluta)
            v = originale(label, options, *args, **kwargs)
            if kwargs.get("key") == "fa_profilo" and v is not None:
                st.session_state["fa_profilo_ric"] = {"uid": (st.session_state.get("sess") or {}).get("uid"), "pid": v}   # fuori dal campo: non si perde quando il campo non viene disegnato
                try:
                    if st.query_params.get("p") != v:
                        st.query_params["p"] = v
                except Exception:
                    pass
            return v
        _spf_selectbox._spf = True
        return _spf_selectbox
    st.selectbox = _spf_fabbrica(st.selectbox)


def _spf_avvolgi(nome):
    f = globals().get(nome)
    if f is None or getattr(f, "_spf", False):
        return

    def _nuova(*a, **k):
        try:
            spf_ripristina()
        except Exception:
            pass
        return f(*a, **k)
    _nuova._spf = True
    _nuova.__name__ = getattr(f, "__name__", nome)
    globals()[nome] = _nuova


for _n in ("schermata_farmacia", "schermata_documenti"):
    _spf_avvolgi(_n)
