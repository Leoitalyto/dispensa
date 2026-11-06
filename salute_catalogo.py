# -*- coding: utf-8 -*-
"""CATALOGO DELLE SPECIALITÀ — la classificazione a livelli della sezione Salute.

AREA MEDICA (Cardiologia…)  →  TIPO DI PRESTAZIONE (Visita specialistica · Esame diagnostico · Prestazione terapeutica · Screening · Controllo)
→  PRESTAZIONE o ESAME (Ecocardiogramma…)  →  DOCUMENTAZIONE (referto, immagini, ricetta, allegati).
Il catalogo non è chiuso: nei moduli si può scrivere anche una specialità o una prestazione che qui non c'è.
Il riconoscimento dal testo dà SEMPRE anche le parole che lo hanno fatto decidere, e non decide da solo: l'utente conferma.
Caricato da app_dispensa.py prima di salute_plus.py."""
import re

CAT_TIPI = ["Visita specialistica", "Esame diagnostico", "Prestazione terapeutica", "Screening", "Controllo di follow-up", "Altro"]
_T = {"V": "Visita specialistica", "E": "Esame diagnostico", "T": "Prestazione terapeutica", "S": "Screening", "C": "Controllo di follow-up", "A": "Altro"}

# (area, icona, parole dell'area, [(prestazione, tipo, parole)])
_CATALOGO = [
    ("Cardiologia", "🫀", ["cardiolog", "cardiac", "cardio", "coronar", "aritmi", "fibrillazione", "ventricolo", "atrio", "valvol", "frazione di eiezione"], [
        ("Visita cardiologica", "V", ["visita cardiologica", "cardiologo"]), ("Elettrocardiogramma (ECG)", "E", ["elettrocardiogramma", "ecg", "ekg"]),
        ("Ecocardiogramma", "E", ["ecocardiogramma", "ecocardio", "ecodoppler cardiaco"]), ("Holter cardiaco", "E", ["holter cardiaco", "holter ecg", "holter"]),
        ("Holter pressorio", "E", ["holter pressorio", "monitoraggio pressorio"]), ("Test da sforzo", "E", ["test da sforzo", "prova da sforzo", "ergometri"]),
        ("Controllo cardiologico", "C", ["controllo cardiologico"])]),
    ("Oculistica", "👁️", ["oculist", "oftalmolog", "oculare", "retina", "cataratta", "glaucoma", "diottri", "acuità visiva", "refrazione", "cornea"], [
        ("Visita oculistica", "V", ["visita oculistica", "oculista"]), ("Fondo oculare", "E", ["fondo oculare", "fundus"]),
        ("Misurazione della pressione oculare", "E", ["pressione oculare", "tonometria"]), ("Campo visivo", "E", ["campo visivo", "perimetria"]),
        ("OCT", "E", ["oct ", "tomografia a coerenza ottica"]), ("Controllo oculistico", "C", ["controllo oculistico"])]),
    ("Ortopedia e traumatologia", "🦴", ["ortoped", "traumatolog", "frattura", "artrosi", "scoliosi", "menisco", "legament", "tendin", "colonna vertebrale", "lombalgia", "cervicalgia", "ernia del disco"], [
        ("Visita ortopedica", "V", ["visita ortopedica", "ortopedico"]), ("Visita traumatologica", "V", ["visita traumatologica"]),
        ("Controllo post-operatorio", "C", ["controllo post-operatorio", "controllo postoperatorio", "post operatorio"]), ("Valutazione della colonna vertebrale", "V", ["colonna vertebrale", "rachide"])]),
    ("Dermatologia", "🧴", ["dermatolog", "dermatoscop", "nevi", "nevo", "melanoma", "psoriasi", "eczema", "acne", "lesioni cutanee", "cute"], [
        ("Visita dermatologica", "V", ["visita dermatologica", "dermatologo"]), ("Mappatura dei nei", "E", ["mappatura dei nei", "mappatura nevi", "epiluminescenza"]),
        ("Dermatoscopia", "E", ["dermatoscopia"]), ("Controllo delle lesioni cutanee", "C", ["lesioni cutanee"])]),
    ("Gastroenterologia", "🫃", ["gastroenter", "gastroscopia", "colonscopia", "egds", "reflusso", "helicobacter", "esofag", "colon", "digestiv", "epatolog", "fegato"], [
        ("Visita gastroenterologica", "V", ["visita gastroenterologica", "gastroenterologo"]), ("Gastroscopia", "E", ["gastroscopia", "esofagogastroduodenoscopia", "egds"]),
        ("Colonscopia", "E", ["colonscopia"]), ("Ecografia addominale", "E", ["ecografia addominale", "ecografia dell'addome", "ecografia epatica"])]),
    ("Neurologia", "🧠", ["neurolog", "encefal", "cefalea", "emicrania", "epilessia", "parkinson", "neuropatia", "sclerosi", "ictus", "vertigine"], [
        ("Visita neurologica", "V", ["visita neurologica", "neurologo"]), ("Elettroencefalogramma (EEG)", "E", ["elettroencefalogramma", "eeg"]),
        ("Elettromiografia (EMG)", "E", ["elettromiografia", "emg ", "elettroneurografia"]), ("Valutazione dei disturbi della memoria", "V", ["disturbi della memoria", "valutazione cognitiva", "mmse"])]),
    ("Endocrinologia e diabetologia", "🧬", ["endocrinolog", "diabetolog", "tiroid", "diabete", "emoglobina glicata", "hba1c", "ormon", "cortisolo", "paratiroid", "ipotiroidismo", "ipertiroidismo"], [
        ("Visita endocrinologica", "V", ["visita endocrinologica", "endocrinologo"]), ("Visita diabetologica", "V", ["visita diabetologica", "diabetologo"]),
        ("Controllo della tiroide", "C", ["ecografia tiroidea", "controllo tiroide", "tsh", "ft4"]), ("Monitoraggio del diabete", "C", ["monitoraggio glicemico", "emoglobina glicata", "hba1c"])]),
    ("Urologia e andrologia", "🚹", ["urolog", "androlog", "prostat", "psa", "vescica", "calcoli renali", "uroflussometria", "cistoscopia", "testicol"], [
        ("Visita urologica", "V", ["visita urologica", "urologo"]), ("Visita andrologica", "V", ["visita andrologica", "andrologo"]),
        ("Ecografia prostatica", "E", ["ecografia prostatica", "ecografia vescico-prostatica"]), ("Controllo della prostata", "S", ["psa", "controllo prostata"])]),
    ("Ginecologia", "🚺", ["ginecolog", "pap test", "hpv", "colposcopia", "utero", "ovaio", "ovarica", "vaginale", "menopausa", "ciclo mestruale"], [
        ("Visita ginecologica", "V", ["visita ginecologica", "ginecologo", "ginecologa"]), ("Pap test", "S", ["pap test", "pap-test", "citologia cervico"]),
        ("HPV test", "S", ["hpv"]), ("Ecografia ginecologica", "E", ["ecografia ginecologica", "ecografia transvaginale", "ecografia pelvica"]),
        ("Colposcopia", "E", ["colposcopia"])]),
    ("Pneumologia", "🫁", ["pneumolog", "polmon", "spirometria", "asma", "bpco", "apnee", "polisonnografia", "respirator", "bronch"], [
        ("Visita pneumologica", "V", ["visita pneumologica", "pneumologo"]), ("Spirometria", "E", ["spirometria"]), ("Test respiratori", "E", ["test respiratori", "diffusione alveolo", "dlco"]),
        ("Controllo delle apnee notturne", "E", ["apnee notturne", "polisonnografia", "saturimetria notturna"])]),
    ("Otorinolaringoiatria", "👂", ["otorinolaringoiatr", "orl ", "audiometri", "impedenzometri", "vestibolare", "laringoscopia", "sinusite", "otite", "timpan", "rinite", "tonsill"], [
        ("Visita ORL", "V", ["visita otorinolaringoiatrica", "visita orl", "otorino"]), ("Audiometria", "E", ["audiometria", "esame audiometrico", "impedenzometria"]),
        ("Esame vestibolare", "E", ["esame vestibolare", "vestibolare"]), ("Endoscopia nasale", "E", ["endoscopia nasale", "rinofibroscopia", "fibrolaringoscopia"])]),
    ("Odontoiatria", "🦷", ["odontoiatr", "dentist", "dentale", "dente", "denti", "carie", "parodont", "ortodonz", "otturazione", "devitalizzazione", "implantolog", "ortopantomografia"], [
        ("Visita odontoiatrica", "V", ["visita odontoiatrica", "visita dentistica", "dentista"]), ("Igiene dentale", "T", ["igiene dentale", "ablazione del tartaro", "pulizia dei denti"]),
        ("Panoramica dentale", "E", ["panoramica dentale", "ortopantomografia", "opt "]), ("Controllo dell'implantologia", "C", ["implantolog", "impianto dentale"])]),
    ("Medicina generale", "🩺", ["medico di famiglia", "medico di base", "medicina generale", "impegnativa", "certificato di malattia"], [
        ("Visita dal medico di famiglia", "V", ["medico di famiglia", "medico di base"]), ("Controllo periodico", "C", ["controllo periodico"])]),
    ("Medicina interna", "🧑‍⚕️", ["medicina interna", "internista", "internistic"], [("Visita internistica", "V", ["visita internistica", "internista"])]),
    ("Oncologia", "🎗️", ["oncolog", "tumor", "neoplasi", "chemioterapia", "radioterapia", "carcinoma", "istolog", "marker tumorali", "metast"], [
        ("Visita oncologica", "V", ["visita oncologica", "oncologo"]), ("Controllo oncologico (follow-up)", "C", ["follow-up oncologico", "controllo oncologico", "follow up"]),
        ("Chemioterapia", "T", ["chemioterapia"]), ("Radioterapia", "T", ["radioterapia"])]),
    ("Nefrologia", "🫘", ["nefrolog", "funzionalità renale", "clearance della creatinina", "egfr", "dialisi", "microalbuminuria", "renale"], [
        ("Visita nefrologica", "V", ["visita nefrologica", "nefrologo"]), ("Controllo della funzionalità renale", "C", ["funzionalità renale", "egfr", "creatinina"])]),
    ("Reumatologia", "🦵", ["reumatolog", "artrite", "reumatoide", "fattore reumatoide", "lupus", "fibromialgia", "gotta", "anti-ccp", "spondilo"], [
        ("Visita reumatologica", "V", ["visita reumatologica", "reumatologo"]), ("Controllo reumatologico", "C", ["controllo reumatologico"])]),
    ("Ematologia", "🩸", ["ematolog", "anemia", "linfoma", "leucemia", "coagulazione", "talassemia", "mieloma", "trombofilia"], [
        ("Visita ematologica", "V", ["visita ematologica", "ematologo"]), ("Controllo ematologico", "C", ["controllo ematologico"])]),
    ("Allergologia", "🤧", ["allergolog", "allergi", "prick test", "patch test", "rast", "immunoterapia specifica", "ige"], [
        ("Visita allergologica", "V", ["visita allergologica", "allergologo"]), ("Test allergologici", "E", ["prick test", "patch test", "test allergologic", "rast"])]),
    ("Immunologia", "🛡️", ["immunolog", "autoanticorp", "immunoglobulin", "complemento", "immunodeficienz"], [
        ("Visita immunologica", "V", ["visita immunologica", "immunologo"]), ("Controllo immunologico", "C", ["controllo immunologico"])]),
    ("Infettivologia", "🦠", ["infettivolog", "malattie infettive", "hiv", "epatite", "tubercolosi", "quantiferon", "sierolog", "borrelia"], [
        ("Visita infettivologica", "V", ["visita infettivologica", "infettivologo"]), ("Esami sierologici", "E", ["sierologia", "sierologico"])]),
    ("Psichiatria", "🧩", ["psichiatr", "ansia", "depressione", "bipolare", "psicofarmac", "disturbo del sonno", "attacchi di panico"], [
        ("Visita psichiatrica", "V", ["visita psichiatrica", "psichiatra"]), ("Controllo psichiatrico", "C", ["controllo psichiatrico"])]),
    ("Psicologia", "💬", ["psicolog", "psicoterap", "colloquio psicologico", "test psicodiagnostic"], [
        ("Colloquio psicologico", "V", ["colloquio psicologico", "psicologo", "psicologa"]), ("Seduta di psicoterapia", "T", ["psicoterapia", "seduta di psicoterapia"])]),
    ("Fisiatria", "♿", ["fisiatr", "riabilitazione", "riabilitativ", "medicina fisica"], [
        ("Visita fisiatrica", "V", ["visita fisiatrica", "fisiatra"]), ("Piano riabilitativo", "T", ["progetto riabilitativo", "piano riabilitativo"])]),
    ("Fisioterapia", "💆", ["fisioterap", "tecarterapia", "laserterapia", "ultrasuonoterapia", "massoterapia", "rieducazione", "kinesi"], [
        ("Seduta di fisioterapia", "T", ["seduta di fisioterapia", "fisioterapia", "tecarterapia", "laserterapia", "rieducazione"])]),
    ("Geriatria", "👵", ["geriatr", "valutazione geriatrica", "demenza", "fragilità"], [("Visita geriatrica", "V", ["visita geriatrica", "geriatra"])]),
    ("Medicina del lavoro", "🏭", ["medicina del lavoro", "medico competente", "idoneità lavorativa", "idoneità alla mansione", "sorveglianza sanitaria", "visita periodica"], [
        ("Visita di idoneità lavorativa", "V", ["idoneità lavorativa", "idoneità alla mansione", "medico competente"]), ("Visita periodica del lavoro", "C", ["visita periodica", "sorveglianza sanitaria"])]),
    ("Medicina dello sport", "🏃", ["medicina dello sport", "idoneità sportiva", "certificato agonistico", "non agonistico", "visita sportiva", "attività sportiva"], [
        ("Visita di idoneità sportiva", "V", ["idoneità sportiva", "certificato agonistico", "non agonistico", "medicina dello sport"])]),
    ("Dietologia e nutrizione", "🥗", ["dietolog", "nutrizion", "dietista", "bioimpedenziometria", "piano alimentare", "indice di massa corporea", "bmi"], [
        ("Valutazione nutrizionale", "V", ["valutazione nutrizionale", "visita nutrizionistica", "visita dietologica", "nutrizionista"]), ("Bioimpedenziometria", "E", ["bioimpedenziometria", "bia "])]),
    ("Ostetricia", "🤰", ["ostetric", "gravidanza", "gestazion", "morfologica", "translucenza nucale", "cardiotocografia", "ctg", "curva da carico", "settimana di gestazione", "feto"], [
        ("Visita ostetrica", "V", ["visita ostetrica"]), ("Ecografia ostetrica", "E", ["ecografia ostetrica", "ecografia morfologica", "translucenza nucale"]), ("Curva glicemica", "E", ["curva glicemica", "curva da carico"])]),
    ("Senologia", "🎀", ["senolog", "mammella", "mammograf", "seno", "tomosintesi", "mammario", "ecografia mammaria"], [
        ("Visita senologica", "V", ["visita senologica", "senologo"]), ("Mammografia", "S", ["mammografia", "tomosintesi"]), ("Ecografia mammaria", "E", ["ecografia mammaria", "ecografia delle mammelle"])]),
    ("Medicina preventiva e screening", "✅", ["screening", "prevenzione", "medicina preventiva", "check-up", "check up", "sangue occulto"], [
        ("Screening del colon (sangue occulto)", "S", ["sangue occulto", "screening colon"]), ("Check-up", "S", ["check-up", "check up"])]),
    ("Analisi di laboratorio", "🧪", ["emocromo", "glicemia", "colesterolo", "trigliceridi", "creatinina", "azotemia", "transaminasi", "gamma gt", "bilirubina", "urine", "ferritina", "sideremia", "vitamina d", "vitamina b12", "ves ", "proteina c", "pcr", "valori di riferimento", "intervallo di riferimento", "laboratorio analisi", "analisi del sangue", "esami del sangue", "prelievo", "campione", "emoglobina", "piastrine", "leucociti", "globuli"], [
        ("Esami del sangue", "E", ["emocromo", "esami del sangue", "analisi del sangue", "glicemia", "colesterolo", "trigliceridi", "creatinina", "transaminasi", "ferritina", "emoglobina"]),
        ("Esame delle urine", "E", ["esame delle urine", "urinocoltura", "esame urine"]), ("Esame delle feci", "E", ["esame delle feci", "coprocoltura", "parassitologico"]), ("Tampone", "E", ["tampone"])]),
    ("Radiologia e diagnostica per immagini", "🩻", ["radiolog", "radiografia", "tomografia", "tac ", "risonanza", "ecografia", "scintigrafia", "pet ", "moc ", "mineralometria", "rx ", "reperto", "quesito diagnostico", "mezzo di contrasto"], [
        ("Radiografia (RX)", "E", ["radiografia", "rx "]), ("TAC", "E", ["tac ", "tomografia computerizzata"]), ("Risonanza magnetica", "E", ["risonanza magnetica", "rmn", "rm "]),
        ("Ecografia", "E", ["ecografia", "ecocolordoppler", "eco-doppler"]), ("Mineralometria ossea (MOC)", "E", ["mineralometria", "moc "]), ("Scintigrafia", "E", ["scintigrafia"])]),
    ("Ricoveri e pronto soccorso", "🏥", ["dimissione", "ricovero", "degenza", "pronto soccorso", "decorso clinico", "dimesso", "reparto di"], [
        ("Lettera di dimissione", "A", ["lettera di dimissione", "dimissione"]), ("Pronto soccorso", "V", ["pronto soccorso", "triage"]), ("Intervento chirurgico", "T", ["intervento chirurgico", "verbale operatorio"])]),
]

CAT_AREE = [a for a, _i, _p, _s in _CATALOGO]
CAT_ICONE = {a: i for a, i, _p, _s in _CATALOGO}
CAT_PRESTAZIONI = {a: [(n, _T[t]) for n, t, _w in s] for a, _i, _p, s in _CATALOGO}

# come si chiamano le visite nella scheda «Visite» (categorie libere: Cardiologo, Dentista…) → area del catalogo
_ALIAS_VISITE = {"cardiolog": "Cardiologia", "oculist": "Oculistica", "ortoped": "Ortopedia e traumatologia", "traumat": "Ortopedia e traumatologia", "dermatolog": "Dermatologia", "gastro": "Gastroenterologia",
                 "neurolog": "Neurologia", "endocrin": "Endocrinologia e diabetologia", "diabet": "Endocrinologia e diabetologia", "urolog": "Urologia e andrologia", "androlog": "Urologia e andrologia",
                 "ginecolog": "Ginecologia", "pneumolog": "Pneumologia", "orl": "Otorinolaringoiatria", "otorino": "Otorinolaringoiatria", "dent": "Odontoiatria", "odontoiatr": "Odontoiatria",
                 "medico di": "Medicina generale", "base": "Medicina generale", "famiglia": "Medicina generale", "internist": "Medicina interna", "oncolog": "Oncologia", "nefrolog": "Nefrologia",
                 "reumat": "Reumatologia", "ematolog": "Ematologia", "allergolog": "Allergologia", "immunolog": "Immunologia", "infettiv": "Infettivologia", "psichiatr": "Psichiatria", "psicolog": "Psicologia",
                 "fisiatr": "Fisiatria", "fisioter": "Fisioterapia", "geriatr": "Geriatria", "lavoro": "Medicina del lavoro", "sport": "Medicina dello sport", "diet": "Dietologia e nutrizione", "nutriz": "Dietologia e nutrizione",
                 "ostetric": "Ostetricia", "senolog": "Senologia", "analisi": "Analisi di laboratorio", "sangue": "Analisi di laboratorio", "radiolog": "Radiologia e diagnostica per immagini",
                 "ecograf": "Radiologia e diagnostica per immagini", "pronto": "Ricoveri e pronto soccorso", "ricover": "Ricoveri e pronto soccorso"}


def cat_area_da_nome(nome):
    """L'area del catalogo per un nome scritto a mano («Cardiologo», «Dentista»…). '' se non la riconosco."""
    n = str(nome or "").lower()
    if not n:
        return ""
    for a in CAT_AREE:
        if n == a.lower():
            return a
    for chiave, area in _ALIAS_VISITE.items():
        if chiave in n:
            return area
    return ""


def _conta(t, parola):
    return len(re.findall(r"(?<![a-zà-ÿ])" + re.escape(parola.strip()) + (r"" if parola.endswith(" ") else r""), t)) if parola.strip() else 0


def cat_classifica(testo):
    """Dal testo di un documento: {area, prestazione, tipo, parole (quelle che hanno deciso), punti, alternative}. Non decide mai da solo: l'utente conferma."""
    t = " " + re.sub(r"\s+", " ", (testo or "").lower()) + " "
    punti, parole = {}, {}
    for area, _ic, par_area, prest in _CATALOGO:
        p, trovate = 0, []
        for w in par_area:
            n = len(re.findall(r"(?<![a-zà-ÿ0-9])" + re.escape(w.strip()), t))
            if n:
                p += 2 * min(n, 3)
                trovate.append(w.strip())
        for _nome, _tp, par_p in prest:
            for w in par_p:
                n = len(re.findall(r"(?<![a-zà-ÿ0-9])" + re.escape(w.strip()), t))
                if n:
                    p += 4 * min(n, 2)
                    trovate.append(w.strip())
        punti[area], parole[area] = p, trovate
    ordinate = sorted(punti.items(), key=lambda kv: -kv[1])
    area, p = ordinate[0]
    if p < 4:
        return {"area": "", "prestazione": "", "tipo": "", "parole": [], "punti": p, "alternative": []}
    # prestazione: la sottocategoria con più parole trovate
    migliore, mp = ("", ""), 0
    for nome, tp, par_p in next(s for a, _i, _pa, s in _CATALOGO if a == area):
        q = sum(min(len(re.findall(r"(?<![a-zà-ÿ0-9])" + re.escape(w.strip()), t)), 2) * (2 if " " in w.strip() else 1) for w in par_p)
        if q > mp:
            migliore, mp = (nome, _T[tp]), q
    tipo = migliore[1]
    if not tipo:                                                                   # nessuna prestazione precisa: si capisce dal tipo di documento
        if re.search(r"anamnesi|esame obiettivo|conclusioni|visita", t):
            tipo = "Visita specialistica"
        elif re.search(r"referto|reperto|esito|valori", t):
            tipo = "Esame diagnostico"
    return {"area": area, "prestazione": migliore[0], "tipo": tipo, "parole": list(dict.fromkeys(parole[area]))[:6], "punti": p,
            "alternative": [a for a, q in ordinate[1:3] if q >= max(4, p * 0.6)]}
