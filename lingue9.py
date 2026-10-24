# -*- coding: utf-8 -*-
"""Rumeno e arabo: registrazione delle lingue, scrittura da destra a sinistra (arabo), nomi degli allergeni
in rumeno e arabo, campi di Open Food Facts per queste lingue e collegamenti ai negozi dei due paesi."""

LINGUE["ro"] = "Română"
LINGUE["ar"] = "العربية"
LINGUE_DA_DESTRA.add("ar")

# nomi di prodotto e ingredienti di Open Food Facts anche in rumeno e arabo
CAMPI_OFF = CAMPI_OFF + ",product_name_ro,product_name_ar,ingredients_text_ro,ingredients_text_ar"

# allergeni scritti in rumeno o in arabo (senza accenti e con gli spazi al posto dei trattini) -> nome italiano
_SINONIMI_RO_AR = {
    "glutine": "cereale care contin gluten|الغلوتين|غلوتين",
    "latte": "lapte|lapte si produse derivate|الحليب|حليب",
    "uova": "oua|ou|البيض|بيض",
    "frutta a guscio": "fructe cu coaja lemnoasa|fructe cu coaja|nuci|alune|migdale|المكسرات|مكسرات",
    "arachidi": "arahide|alune de pamant|الفول السوداني|فول سوداني",
    "soia": "soia si produse derivate|الصويا|صويا",
    "pesce": "peste|pesti|السمك|سمك",
    "crostacei": "crustacee|القشريات|قشريات",
    "molluschi": "moluste|الرخويات|رخويات",
    "sedano": "telina|الكرفس|كرفس",
    "senape": "mustar|الخردل|خردل",
    "sesamo": "susan|seminte de susan|السمسم|سمسم",
    "solfiti": "sulfiti|dioxid de sulf|dioxid de sulf si sulfiti|الكبريتيت|كبريتيت|الكبريتات|كبريتات",
    "lupini": "lupin|الترمس|ترمس",
}
for _it, _parole in _SINONIMI_RO_AR.items():
    for _p in _parole.split("|"):
        SINONIMI_ALLERGENI[_p] = _it
for _it in ("glutine", "soia", "lupini"):                 # nomi uguali a quelli gia' presenti: gluten, soia, lupin
    SINONIMI_ALLERGENI.setdefault({"glutine": "gluten", "soia": "soia", "lupini": "lupin"}[_it], _it)

TRADUZIONI["ro"]["Cerca su eMAG"] = "Caută pe eMAG"

# scrittura da destra a sinistra (arabo): il codice rifa' questo calcolo a ogni apertura della pagina
if lingua() in LINGUE_DA_DESTRA:
    CSS = CSS.replace("</style>", """
.stApp, [data-testid="stSidebar"], [data-testid="stDialog"], [role="dialog"]{direction:rtl}
.stMarkdown, .stCaption, label, [data-testid="stMetric"], .stAlert, h1, h2, h3, h4{text-align:right}
[data-testid="stDataFrame"], [data-testid="stDataEditor"], code, pre, input[type="password"],
[data-testid="stNumberInput"] input{direction:ltr;text-align:left}
.avviso{border-left-width:0 !important;border-right-width:8px;border-right-style:solid}
.allergeni-box{border-left:0;border-right:8px solid #ef6c00}
.avviso ul, .allarme ul, .allergeni-box ul{padding-left:0;padding-right:20px}
.badge{margin:2px 0 0 3px}
</style>""")


# collegamenti ai negozi: Romania -> eMAG, paesi arabi -> Amazon.ae
_link_online_base = link_online


def link_online(nome, marca, codice, immagine):
    righe = _link_online_base(nome, marca, codice, immagine)
    ricerca = " ".join(x for x in (marca, nome) if x) or (codice or "")
    risultato = []
    for etichetta, url in righe:
        if url.startswith("https://www.amazon."):
            if lingua() == "ro":
                etichetta, url = "📦 " + t("Cerca su eMAG"), "https://www.emag.ro/search/" + urllib.parse.quote(ricerca, safe="")
            elif lingua() == "ar":
                url = "https://www.amazon.ae/s?k=" + urllib.parse.quote_plus(ricerca)
        risultato.append((etichetta, url))
    return risultato
