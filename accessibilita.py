# -*- coding: utf-8 -*-
"""ACCESSIBILITÀ · gruppo A del progetto di ottimizzazione (solo aspetto, nessun dato e nessuna funzione cambia).

Misurato con un browser da telefono su tutte le sezioni (vedi PIANO_OTTIMIZZAZIONE_dispensa.md):
• i pulsanti principali dei moduli («💾 Salva», «✅ Conferma e archivia»…) erano del rosso predefinito di Streamlit con testo bianco (contrasto 3,3:1) e fuori stile; i pulsanti principali verdi avevano un contrasto di 2,5:1 nella parte chiara;
• molti comandi erano più bassi di 40 px (caselle di testo e menu a tendina 36-38 px, schede in basso 28 px, caselle da spuntare 13 px);
• le didascalie arrivavano a 12 px; accanto a ogni titolo c'erano minuscoli simboli «link» (16 px) che nessuno usa e che si possono toccare per sbaglio.
Cosa fa (gruppo A + rifiniture finali: intestazioni a tendina da 44 px, microfono di dettatura da 44 px, piccole «x» delle scelte multiple più grandi): verde scuro uniforme con testo bianco (contrasto ≥ 5:1) per i pulsanti principali, per le voci scelte nei selettori (anche quelle a più scelte, prima rosse) e per la scheda attiva in basso; comandi alti almeno 44 px; caselle da spuntare da 24 px; didascalie da almeno 13,5 px; nascosti i simboli «link» dei titoli.
Come: si aggiunge al CSS globale (come fanno gli altri moduli di stile), quindi non c'è nessun elemento in più nella pagina. Caricato dopo gli altri moduli di stile e prima della pagina principale."""
import streamlit as st

ACC_CSS = """
/* ===== accessibilità: contrasto, comandi più grandi, testi leggibili ===== */
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primaryFormSubmit"]{background:linear-gradient(135deg,#0f766e 0%,#115e59 100%) !important;color:#fff !important;border:0 !important}
[data-testid="stBaseButton-primary"] p,[data-testid="stBaseButton-primaryFormSubmit"] p,[data-testid="stBaseButton-primary"] span,[data-testid="stBaseButton-primaryFormSubmit"] span{color:#fff !important}
[data-testid="stBaseButton-pillsActive"],[data-testid="stBaseButton-segmented_controlActive"],[data-testid="stBaseButton-pillsActive"] p,[data-testid="stBaseButton-segmented_controlActive"] p{background:#0f766e !important;color:#fff !important;border-color:#0f766e !important}
[role="tab"][aria-selected="true"]{background:linear-gradient(135deg,#0f766e,#115e59) !important}
[data-testid^="stBaseButton"]{min-height:44px}
[role="tab"]{min-height:38px !important}
[data-baseweb="select"]>div,[data-baseweb="input"],[data-baseweb="base-input"]{min-height:44px}
[data-testid="stCheckbox"] label,[data-testid="stRadio"] label{min-height:44px;align-items:center}
[data-baseweb="checkbox"]>span:first-of-type{width:24px !important;height:24px !important}
[data-testid="stMultiSelectTagsContainer"] span,[data-baseweb="tag"],[data-baseweb="tag"] span{background-color:#0f766e !important;color:#fff !important}[data-testid="stMultiSelectTagsContainer"] svg,[data-baseweb="tag"] svg{color:#fff !important;fill:#fff !important}
input:not([type="checkbox"]):not([type="radio"]):not([type="file"]){min-height:44px;box-sizing:border-box}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,[data-testid="stCaptionContainer"] small{font-size:max(.88rem,13.5px) !important}
[data-testid="stHeaderActionElements"]{display:none !important}
/* il pulsante «Salva in dispensa» resta sempre in vista mentre si compila il modulo (che è lungo): fisso sopra la barra in basso, lasciando libero il robottino a destra */
.st-key-salva_dispensa{position:fixed !important;left:12px;right:104px;bottom:84px;z-index:60;width:auto !important}
/* le schede che stanno DENTRO una tendina o una finestra (per esempio «Come attivo Telegram / l'email / WhatsApp») sono schede NORMALI, nel testo: non la barra fissa in basso della pagina
   (prima fluttuavano sopra il contenuto, larghe 186 px, e si vedeva una sola scheda su tre) */
html body [data-testid="stExpander"] [role="tablist"], html body [data-testid="stDialog"] [role="tablist"]{
 position:static !important;left:auto !important;right:auto !important;top:auto !important;bottom:auto !important;transform:none !important;
 width:100% !important;max-width:100% !important;z-index:auto !important;flex-wrap:wrap !important;gap:6px !important;
 background:rgba(255,255,255,.55) !important;backdrop-filter:none !important;-webkit-backdrop-filter:none !important;border-radius:16px !important;
 padding:6px !important;margin:6px 0 10px 0 !important;box-shadow:none !important;overflow:visible !important}
html body [data-testid="stExpander"] [role="tablist"] [data-baseweb="tab-highlight"], html body [data-testid="stExpander"] [role="tablist"] [data-baseweb="tab-border"],
html body [data-testid="stDialog"] [role="tablist"] [data-baseweb="tab-highlight"], html body [data-testid="stDialog"] [role="tablist"] [data-baseweb="tab-border"]{display:none !important}
html body [data-testid="stExpander"] [role="tablist"] [role="tab"], html body [data-testid="stDialog"] [role="tablist"] [role="tab"]{flex:1 1 auto !important;white-space:normal !important;text-align:center !important}
/* la linguetta della radio (cuffie) sul bordo sinistro non deve più coprire l'inizio delle scritte: è più stretta e il contenuto parte un po' più a destra (solo se la radio è attiva) */
@media (max-width:700px){
#mu-tab{width:24px !important}
body:has(#mu-tab:not([style*="display: none"])) [data-testid="stMainBlockContainer"]{padding-left:30px !important}
}
[data-testid="stExpander"] summary{min-height:44px;display:flex;align-items:center}
.vc-mic{width:44px !important;height:44px !important;right:2px !important}
[data-testid="stMultiSelect"] [data-baseweb="tag"],[data-testid="stMultiSelectTagsContainer"] span{min-height:36px}
[data-testid="stMultiSelect"] button[aria-label^="Remove"],[data-testid="stMultiSelect"] [aria-label^="Remove"]{min-width:30px !important;min-height:30px !important;padding:6px !important}
[data-testid="stDateInputCalendarButton"]{min-width:44px;min-height:36px}
"""
ACC_CSS_CMD = """
/* comandi riconoscibili a colpo d'occhio, uguali in tutta l'app: elimina = rosso, modifica = blu, invia/condividi = verde, indietro = grigio */
button[data-cmd="elimina"][data-testid="stBaseButton-secondary"]{border:2px solid #c62828 !important;color:#b71c1c !important;background:#fff6f6 !important}
button[data-cmd="modifica"][data-testid="stBaseButton-secondary"]{border:2px solid #1565c0 !important;color:#0d47a1 !important;background:#f2f7ff !important}
button[data-cmd="invia"][data-testid="stBaseButton-secondary"]{border:2px solid #2e7d32 !important;color:#1b5e20 !important;background:#f3fbf4 !important}
button[data-cmd="indietro"][data-testid="stBaseButton-secondary"]{border:2px solid #546e7a !important;color:#37474f !important;background:#f4f6f7 !important}
button[data-cmd] p,button[data-cmd] span{color:inherit !important}
/* quando i comandi stanno uno accanto all'altro l'ordine è sempre lo stesso: Modifica, Invia, e ELIMINA per ultimo (così non si tocca per sbaglio) */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(button[data-cmd="modifica"]){order:3}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(button[data-cmd="invia"]){order:5}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(button[data-cmd="elimina"]){order:9}
"""
_ACC_JS_CMD = r"""(function(){var w=window,d=w.document;if(w.__cmdColori)return;w.__cmdColori=1;
var R=[['elimina',/(Elimina|Togli|Svuota)/],['modifica',/(Modifica|Correggi)/],['invia',/(Invia|Condividi|Manda)/],['indietro',/^\s*(←|◀|⬅️)/]];
function tag(b){var t=(b.innerText||'').trim().slice(0,60);if(b.__tx===t)return;b.__tx=t;b.removeAttribute('data-cmd');
 for(var i=0;i<R.length;i++){if(R[i][1].test(t)){b.setAttribute('data-cmd',R[i][0]);break;}}}
function scan(){var l=d.querySelectorAll('button');for(var i=0;i<l.length;i++)tag(l[i]);}
new MutationObserver(function(){w.clearTimeout(w.__cmdT);w.__cmdT=w.setTimeout(scan,120);}).observe(d.body,{childList:true,subtree:true,characterData:true});
scan();})();"""
if "CSS" in globals():
    CSS = CSS.replace("</style>", ACC_CSS + ACC_CSS_CMD + "\n</style>")


def acc_inietta_comandi():
    """Una volta per sessione: dà ai pulsanti elimina/modifica/invia/indietro il colore giusto (lo script li riconosce dal testo)."""
    try:
        if not st.session_state.get("_inj_cmd") and "_inietta" in globals():
            st.session_state["_inj_cmd"] = True
            _inietta(_ACC_JS_CMD)
    except Exception:
        pass


if "_acc_nav_prima" not in globals() and "nav_pagine" in globals():
    _acc_nav_prima = nav_pagine


def nav_pagine(corrente):
    r = _acc_nav_prima(corrente)
    acc_inietta_comandi()
    return r
