# -*- coding: utf-8 -*-
"""ACCESSIBILITÀ · gruppo A del progetto di ottimizzazione (solo aspetto, nessun dato e nessuna funzione cambia).

Misurato con un browser da telefono su tutte le sezioni (vedi PIANO_OTTIMIZZAZIONE_dispensa.md):
• i pulsanti principali dei moduli («💾 Salva», «✅ Conferma e archivia»…) erano del rosso predefinito di Streamlit con testo bianco (contrasto 3,3:1) e fuori stile; i pulsanti principali verdi avevano un contrasto di 2,5:1 nella parte chiara;
• molti comandi erano più bassi di 40 px (caselle di testo e menu a tendina 36-38 px, schede in basso 28 px, caselle da spuntare 13 px);
• le didascalie arrivavano a 12 px; accanto a ogni titolo c'erano minuscoli simboli «link» (16 px) che nessuno usa e che si possono toccare per sbaglio.
Cosa fa: verde scuro uniforme con testo bianco (contrasto ≥ 5:1) per i pulsanti principali, per le voci scelte nei selettori (anche quelle a più scelte, prima rosse) e per la scheda attiva in basso; comandi alti almeno 44 px; caselle da spuntare da 24 px; didascalie da almeno 13,5 px; nascosti i simboli «link» dei titoli.
Come: si aggiunge al CSS globale (come fanno gli altri moduli di stile), quindi non c'è nessun elemento in più nella pagina. Caricato dopo gli altri moduli di stile e prima della pagina principale."""
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
"""
if "CSS" in globals():
    CSS = CSS.replace("</style>", ACC_CSS + "\n</style>")
