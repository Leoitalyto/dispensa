# -*- coding: utf-8 -*-
"""ANIMALI · REPORT VETERINARIO PDF — un PDF ordinato da consegnare al veterinario, a una clinica, a uno specialista o a una persona autorizzata.

Copertina (foto, nome, data di generazione, periodo considerato, ultimo aggiornamento dei dati, informazioni mancanti), indice, legenda e sezioni.
Otto tipi: A completo · B sintetico · C cronologico di visite e terapie · D vaccinazioni e prevenzione · E farmaci e trattamenti · F alimentazione e monitoraggio ·
G personalizzato (scegli le sezioni) · H completo con gli allegati (i documenti originali scelti vengono aggiunti in fondo al PDF; si può anche avere il pacchetto ZIP con gli originali).
Le diagnosi, le terapie e le prescrizioni REGISTRATE DAL VETERINARIO (o prese da un suo documento) sono sempre in una tabella separata dalle ANNOTAZIONI DEL PROPRIETARIO.
Usa reportlab (già nell'app: lo usa anche invio.py) e pypdf (già nell'app). Caricato dopo animali_doc.py."""
import io
import re
import zipfile
from datetime import date

import streamlit as st

AN_SEZ_REPORT = {
    "anagrafica": "Dati dell'animale e del proprietario", "foto": "Fotografie", "vaccini": "Vaccinazioni e prevenzione", "visite": "Visite veterinarie", "patologie": "Patologie conosciute",
    "allergie": "Allergie e intolleranze", "terapie_attuali": "Farmaci e terapie attuali", "terapie_precedenti": "Terapie precedenti", "interventi": "Interventi e ricoveri",
    "esami": "Esami effettuati", "referti": "Risultati e referti", "peso": "Andamento del peso", "alimentazione": "Alimentazione", "habitat": "Habitat",
    "diario": "Diario e annotazioni", "spese": "Spese", "documenti": "Documenti sanitari associati", "scadenze": "Prossime visite e scadenze", "contatti": "Veterinari e contatti",
    "cronologia": "Cronologia di visite e terapie", "prescrizioni": "Prescrizioni",
}
_AN_COMPLETO = ["anagrafica", "foto", "vaccini", "visite", "patologie", "allergie", "terapie_attuali", "terapie_precedenti", "interventi", "esami", "referti", "peso", "alimentazione",
                "habitat", "diario", "documenti", "scadenze", "contatti"]
AN_VARIANTI = {
    "A": ("A · Report sanitario completo", _AN_COMPLETO),
    "B": ("B · Report sanitario sintetico", ["anagrafica", "patologie", "allergie", "terapie_attuali", "vaccini", "visite", "peso", "scadenze"]),
    "C": ("C · Cronologia di tutte le visite e terapie", ["anagrafica", "cronologia"]),
    "D": ("D · Vaccinazioni e prevenzione", ["anagrafica", "vaccini", "scadenze"]),
    "E": ("E · Farmaci e trattamenti", ["anagrafica", "allergie", "terapie_attuali", "terapie_precedenti", "prescrizioni"]),
    "F": ("F · Alimentazione e monitoraggio", ["anagrafica", "alimentazione", "habitat", "peso", "diario"]),
    "G": ("G · Personalizzato (scelgo io cosa includere)", None),
    "H": ("H · Completo con gli allegati", _AN_COMPLETO),
}
_AN_VERDE = "#2e7d32"
_AN_ORO = "#8a5a00"


def _pt(s):
    """Testo sicuro per il PDF (Helvetica): niente emoji o caratteri fuori dal set occidentale; a capo conservati."""
    s = str(s if s is not None else "")
    s = s.replace("→", "->").replace("•", "-").replace("✅", "").replace("’", "'")
    s = s.encode("cp1252", "ignore").decode("cp1252")
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.replace("\n", "<br/>")


def _foto_pdf(rif, lato=900):
    """Una foto pronta per il PDF (JPEG RGB ridotto) come byte, oppure None."""
    dati = an_leggi_file(rif) if rif and rif.get("id") else None
    if not dati:
        return None
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(dati))).convert("RGB")
        im.thumbnail((lato, lato))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=85)
        return b.getvalue()
    except Exception:
        return None


def an_report_periodo(a, aid, dal=None, al=None):
    """(testo del periodo, dal, al): se non si sceglie, tutto lo storico."""
    date_voci = []
    for cat in ("vaccini", "visite", "terapie", "esami", "interventi", "patologie", "peso", "diario", "spese", "documenti"):
        for r in an_voci(a, cat, aid):
            d_ = an_data(r.get("data") or r.get("dal"))
            if d_:
                date_voci.append(d_)
    if dal or al:
        return f"dal {an_data_it(dal.isoformat()) if dal else 'primo dato'} al {an_data_it(al.isoformat()) if al else an_data_it(_an_oggi().isoformat())}", dal, al
    if date_voci:
        return f"tutto lo storico registrato (dal {an_data_it(min(date_voci).isoformat())} a oggi)", None, None
    return "tutto lo storico (non ci sono ancora dati con una data)", None, None


def _in_periodo(r, chiavi, dal, al):
    if not dal and not al:
        return True
    d_ = None
    for k in chiavi:
        d_ = an_data(r.get(k))
        if d_:
            break
    if d_ is None:
        return True
    if dal and d_ < dal:
        return False
    if al and d_ > al:
        return False
    return True


def an_report_mancanti(a, x, sezioni):
    """Le informazioni che mancano per un quadro completo (elenco di frasi)."""
    m = []
    aid = x["id"]
    if not x.get("microchip") and not x.get("tatuaggio"):
        m.append("Microchip o altro identificativo non registrato")
    if not x.get("nascita"):
        m.append("Data di nascita non registrata")
    if not x.get("razza"):
        m.append("Razza non indicata")
    p = x.get("proprietario") or {}
    if not p.get("nome") or not (p.get("tel") or p.get("email")):
        m.append("Dati del proprietario incompleti (nome e un recapito)")
    if "vaccini" in sezioni and not an_voci(a, "vaccini", aid):
        m.append("Nessuna vaccinazione registrata")
    if "visite" in sezioni and not an_voci(a, "visite", aid):
        m.append("Nessuna visita registrata")
    if "peso" in sezioni and not an_voci(a, "peso", aid):
        m.append("Nessun peso registrato")
    if "alimentazione" in sezioni and not (x.get("alimentazione") or {}).get("tipo"):
        m.append("Alimentazione non descritta")
    if "allergie" in sezioni and not an_voci(a, "allergie", aid):
        m.append("Allergie: non registrate (se non ne ha, va bene così)")
    da_compl = [d_ for d_ in an_voci(a, "documenti", aid) if d_.get("mancanti")]
    if da_compl:
        m.append(f"{len(da_compl)} documenti hanno informazioni da completare")
    if not an_voci(a, "contatti"):
        m.append("Nessun veterinario o clinica nei contatti")
    return m


def an_report_pdf(a, aid, variante="A", sezioni=None, dal=None, al=None, allegati_ids=None, nome_utente=""):
    """Costruisce il report e ritorna i byte del PDF. Ritorna None se manca reportlab."""
    try:
        from reportlab.graphics.charts.lineplots import LinePlot
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.platypus.tableofcontents import TableOfContents
    except Exception:
        return None
    x = an_trova(a, aid)
    if not x:
        return None
    nome_var, sez_var = AN_VARIANTI.get(variante, AN_VARIANTI["A"])
    sezioni = list(sezioni if (variante == "G" and sezioni is not None) else (sez_var or _AN_COMPLETO))
    oggi_ = _an_oggi()
    periodo, dal, al = an_report_periodo(a, aid, dal, al)
    ultimo = an_ultimo_aggiornamento(a, aid)
    mancanti = an_report_mancanti(a, x, sezioni)
    st_ = getSampleStyleSheet()
    base = ParagraphStyle("b", parent=st_["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12)
    piccolo = ParagraphStyle("p", parent=base, fontSize=7.8, leading=10, textColor=colors.HexColor("#555555"))
    cella = ParagraphStyle("c", parent=base, fontSize=8.3, leading=10.4)
    cella_b = ParagraphStyle("cb", parent=cella, fontName="Helvetica-Bold")
    cella_prop = ParagraphStyle("cp", parent=cella, fontName="Helvetica-Oblique", textColor=colors.HexColor("#455a64"))
    h1 = ParagraphStyle("H1", parent=base, fontName="Helvetica-Bold", fontSize=13.5, leading=17, textColor=colors.white, backColor=colors.HexColor(_AN_ORO), borderPadding=(5, 6, 5, 6), spaceBefore=14, spaceAfter=9)
    h2 = ParagraphStyle("H2", parent=base, fontName="Helvetica-Bold", fontSize=10.3, leading=13, textColor=colors.HexColor(_AN_VERDE), spaceBefore=8, spaceAfter=3)
    h2p = ParagraphStyle("H2p", parent=h2, textColor=colors.HexColor("#546e7a"))
    titolo_st = ParagraphStyle("t", parent=base, fontName="Helvetica-Bold", fontSize=25, leading=30, alignment=TA_CENTER, textColor=colors.HexColor(_AN_ORO))
    sotto_st = ParagraphStyle("s", parent=base, fontSize=11.5, leading=15, alignment=TA_CENTER)
    L = 174 * mm

    class _Doc(BaseDocTemplate):
        def afterFlowable(self, fl):
            if isinstance(fl, Paragraph) and fl.style.name == "H1":
                testo = fl.getPlainText()
                chiave = f"s{self.seq.nextf('toc')}"
                self.canv.bookmarkPage(chiave)
                self.canv.addOutlineEntry(testo, chiave, 0, 0)
                self.notify("TOCEntry", (0, testo, self.page, chiave))

    def _pie(canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 7.5)
        canv.setFillColor(colors.HexColor("#666666"))
        canv.drawString(18 * mm, 10 * mm, f"Report veterinario di {x.get('nome', '')} - generato il {an_data_it(oggi_.isoformat())}".encode("cp1252", "ignore").decode("cp1252"))
        canv.drawRightString(192 * mm, 10 * mm, f"Pagina {doc.page}")
        canv.setStrokeColor(colors.HexColor("#c9a23a"))
        canv.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
        canv.restoreState()
    buf = io.BytesIO()
    doc = _Doc(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm, title=f"Report veterinario - {x.get('nome', '')}",
               author=nome_utente or "Dispensa", subject="Report veterinario")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=_pie)])
    el = []

    def tabella(intest, righe, larghezze, stile_prop=False):
        dati = [[Paragraph(_pt(h), cella_b) for h in intest]] + [[Paragraph(_pt(c), cella_prop if stile_prop else cella) for c in riga] for riga in righe]
        t = Table(dati, colWidths=[w * L for w in larghezze], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3e3b5" if not stile_prop else "#e3eaee")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return t

    def sezione_fonte(titolo, righe_vet, righe_prop, intest, larghezze, vuoto="Nessun dato registrato."):
        """Due tabelle: ciò che è scritto dal veterinario e ciò che è annotazione del proprietario."""
        if not righe_vet and not righe_prop:
            el.append(Paragraph(_pt(vuoto), base))
            return
        if righe_vet:
            el.append(Paragraph(_pt("Registrato dal veterinario (o preso da un suo documento)"), h2))
            el.append(tabella(intest, righe_vet, larghezze))
        if righe_prop:
            el.append(Paragraph(_pt("Annotazioni del proprietario (non sono diagnosi né prescrizioni del veterinario)"), h2p))
            el.append(tabella(intest, righe_prop, larghezze, stile_prop=True))

    def dividi(voci, riga_fn):
        vet = [riga_fn(r) for r in voci if r.get("fonte") == "veterinario"]
        prop = [riga_fn(r) for r in voci if r.get("fonte") != "veterinario"]
        return vet, prop

    # ------------------------------------------------------------ copertina
    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("Report veterinario", titolo_st))
    el.append(Spacer(1, 3 * mm))
    el.append(Paragraph(_pt(nome_var), sotto_st))
    el.append(Spacer(1, 6 * mm))
    jpg = _foto_pdf(x.get("foto"), 900)
    if jpg:
        try:
            from PIL import Image as _PI
            w0, h0 = _PI.open(io.BytesIO(jpg)).size
            wf = 80 * mm
            hf = wf * h0 / w0
            if hf > 85 * mm:
                hf = 85 * mm
                wf = hf * w0 / h0
            im = Image(io.BytesIO(jpg), width=wf, height=hf)
            im.hAlign = "CENTER"
            el.append(im)
            el.append(Spacer(1, 4 * mm))
        except Exception:
            pass
    el.append(Paragraph(_pt(x.get("nome", "")), ParagraphStyle("n", parent=titolo_st, fontSize=22, textColor=colors.HexColor("#3a2a08"))))
    el.append(Paragraph(_pt(" - ".join(z for z in (x.get("specie"), x.get("razza")) if z)), sotto_st))
    el.append(Spacer(1, 6 * mm))
    info = [["Nome dell'animale", x.get("nome", "")], ["Data di generazione del report", an_data_it(oggi_.isoformat())], ["Periodo considerato", periodo],
            ["Ultimo aggiornamento dei dati", an_data_it(ultimo) if ultimo else "non disponibile"], ["Generato da", nome_utente or "app VitaMemo"]]
    t = Table([[Paragraph(_pt(k), cella_b), Paragraph(_pt(v), cella)] for k, v in info], colWidths=[0.4 * L, 0.6 * L])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3e3b5")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    el.append(t)
    el.append(Spacer(1, 5 * mm))
    if mancanti:
        el.append(Paragraph(_pt("Informazioni mancanti o da completare"), h2))
        for mm_ in mancanti:
            el.append(Paragraph(_pt("- " + mm_), base))
    else:
        el.append(Paragraph(_pt("Nessuna informazione essenziale risulta mancante."), base))
    el.append(PageBreak())
    # ------------------------------------------------------------ indice e legenda
    el.append(Paragraph("Indice", ParagraphStyle("ind", parent=h2, fontSize=15, leading=19)))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("t0", parent=base, fontSize=10.5, leading=16, leftIndent=0)]
    el.append(toc)
    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph(_pt("Come leggere questo documento"), h2))
    el.append(Paragraph(_pt("Le informazioni scritte o prescritte da un veterinario (anche prese da un suo documento) stanno nelle tabelle intitolate «Registrato dal veterinario». "
                            "Le annotazioni del proprietario stanno in tabelle separate, in corsivo, e NON sostituiscono una diagnosi o una prescrizione. Le date sono nel formato giorno/mese/anno."), base))
    el.append(PageBreak())

    # ------------------------------------------------------------ sezioni
    def intesta(chiave):
        el.append(Paragraph(_pt(AN_SEZ_REPORT[chiave]), h1))

    ordine = [s for s in ["anagrafica", "foto", "patologie", "allergie", "terapie_attuali", "terapie_precedenti", "prescrizioni", "vaccini", "visite", "interventi", "esami", "referti", "cronologia",
                          "peso", "alimentazione", "habitat", "diario", "spese", "documenti", "scadenze", "contatti"] if s in sezioni]
    for s in ordine:
        if s == "anagrafica":
            intesta(s)
            p = x.get("proprietario") or {}
            righe = [("Nome", x.get("nome")), ("Specie", x.get("specie")), ("Razza", x.get("razza")), ("Sesso", x.get("sesso")), ("Sterilizzato / castrato", "si" if x.get("sterilizzato") else ""),
                     ("Data di nascita", an_data_it(x.get("nascita"))), ("Colore e segni particolari", x.get("colore")), ("Microchip", x.get("microchip")), ("Altri identificativi", x.get("tatuaggio")),
                     ("Passaporto / libretto", x.get("passaporto")), ("Pedigree", x.get("pedigree")), ("Proprietario", p.get("nome")), ("Telefono", p.get("tel")), ("Email", p.get("email")),
                     ("Indirizzo", p.get("indirizzo")), ("Annotazioni importanti (del proprietario)", x.get("note"))]
            righe = [[k, v] for k, v in righe if v]
            el.append(tabella(["Dato", "Valore"], righe, [0.36, 0.64]) if righe else Paragraph(_pt("Nessun dato anagrafico."), base))
        elif s == "foto":
            gal = list(x.get("galleria") or [])[:9]
            if not gal:
                continue
            intesta(s)
            celle = []
            for g in gal:
                j = _foto_pdf(g, 600)
                if j:
                    try:
                        from PIL import Image as _PI
                        w0, h0 = _PI.open(io.BytesIO(j)).size
                        wf = 52 * mm
                        celle.append(Image(io.BytesIO(j), width=wf, height=min(wf * h0 / w0, 52 * mm)))
                    except Exception:
                        pass
            if celle:
                righe = [celle[i:i + 3] + [""] * (3 - len(celle[i:i + 3])) for i in range(0, len(celle), 3)]
                el.append(Table(righe, colWidths=[58 * mm] * 3))
        elif s == "patologie":
            intesta(s)
            voci = [r for r in an_voci(a, "patologie", aid)]
            vet, prop = dividi(voci, lambda r: [r.get("nome"), r.get("stato"), an_data_it(r.get("dal")), r.get("note")])
            sezione_fonte(s, vet, prop, ["Patologia", "Stato", "Dal", "Note"], [0.32, 0.18, 0.14, 0.36])
        elif s == "allergie":
            intesta(s)
            voci = an_voci(a, "allergie", aid)
            vet, prop = dividi(voci, lambda r: [r.get("sostanza"), r.get("reazione"), r.get("note")])
            sezione_fonte(s, vet, prop, ["A che cosa", "Reazione", "Note"], [0.35, 0.3, 0.35], vuoto="Nessuna allergia o intolleranza registrata.")
        elif s in ("terapie_attuali", "terapie_precedenti"):
            intesta(s)
            tutte = [r for r in an_voci(a, "terapie", aid) if _in_periodo(r, ["dal", "al"], dal, al)]
            voci = [r for r in tutte if (an_terapia_attiva(r) == (s == "terapie_attuali"))]
            vet, prop = dividi(an_ordina(voci, "dal"), lambda r: [r.get("farmaco"), " ".join(z for z in (r.get("dose"), r.get("frequenza")) if z), an_data_it(r.get("dal")) + (" - " + an_data_it(r["al"]) if r.get("al") else " - in corso"), r.get("motivo")])
            sezione_fonte(s, vet, prop, ["Farmaco", "Dose e frequenza", "Periodo", "Per"], [0.28, 0.26, 0.24, 0.22],
                          vuoto="Nessuna terapia in corso." if s == "terapie_attuali" else "Nessuna terapia precedente registrata.")
        elif s == "prescrizioni":
            intesta(s)
            docs = [d_ for d_ in an_voci(a, "documenti", aid) if d_.get("tipo") == "Prescrizione / Ricetta" and _in_periodo(d_, ["data"], dal, al)]
            if not docs:
                el.append(Paragraph(_pt("Nessuna prescrizione archiviata."), base))
            else:
                el.append(Paragraph(_pt("Prescrizioni archiviate (documento del veterinario)"), h2))
                el.append(tabella(["Data", "Documento", "Veterinario", "Indicazioni lette dal documento"], [[an_data_it(d_.get("data")), d_.get("titolo"), (d_.get("campi") or {}).get("veterinario"), (d_.get("campi") or {}).get("terapia")] for d_ in an_ordina(docs, "data")], [0.12, 0.26, 0.2, 0.42]))
        elif s == "vaccini":
            intesta(s)
            voci = [r for r in an_voci(a, "vaccini", aid) if _in_periodo(r, ["data"], dal, al)]
            vet, prop = dividi(an_ordina(voci, "data"), lambda r: [an_data_it(r.get("data")), r.get("tipo"), r.get("nome"), an_data_it(r.get("richiamo")), r.get("lotto"), r.get("vet")])
            sezione_fonte(s, vet, prop, ["Data", "Tipo", "Nome", "Richiamo", "Lotto", "Veterinario"], [0.12, 0.15, 0.25, 0.12, 0.13, 0.23])
        elif s == "visite":
            intesta(s)
            voci = [r for r in an_voci(a, "visite", aid) if _in_periodo(r, ["data"], dal, al)]
            vet, prop = dividi(an_ordina(voci, "data"), lambda r: [an_data_it(r.get("data")), r.get("motivo"), " ".join(z for z in (r.get("vet"), r.get("clinica")) if z), r.get("diagnosi"), r.get("indicazioni")])
            sezione_fonte(s, vet, prop, ["Data", "Motivo", "Veterinario / clinica", "Diagnosi", "Cure e indicazioni"], [0.11, 0.17, 0.2, 0.25, 0.27])
        elif s == "interventi":
            intesta(s)
            voci = [r for r in an_voci(a, "interventi", aid) if _in_periodo(r, ["data"], dal, al)]
            vet, prop = dividi(an_ordina(voci, "data"), lambda r: [an_data_it(r.get("data")) + (" - " + an_data_it(r["fine"]) if r.get("fine") else ""), r.get("tipo"), r.get("descrizione"), r.get("clinica")])
            sezione_fonte(s, vet, prop, ["Data", "Che cosa", "Descrizione", "Clinica"], [0.2, 0.2, 0.38, 0.22], vuoto="Nessun intervento o ricovero registrato.")
        elif s == "esami":
            intesta(s)
            voci = [r for r in an_voci(a, "esami", aid) if _in_periodo(r, ["data"], dal, al)]
            vet, prop = dividi(an_ordina(voci, "data"), lambda r: [an_data_it(r.get("data")), r.get("tipo"), r.get("esito"), r.get("vet")])
            sezione_fonte(s, vet, prop, ["Data", "Esame", "Risultato", "Veterinario / laboratorio"], [0.12, 0.2, 0.46, 0.22], vuoto="Nessun esame registrato.")
        elif s == "referti":
            docs = [d_ for d_ in an_voci(a, "documenti", aid) if d_.get("tipo") in ("Referto / Esame", "Cartella clinica / Dimissione", "Certificato") and _in_periodo(d_, ["data"], dal, al)]
            intesta(s)
            if not docs:
                el.append(Paragraph(_pt("Nessun referto archiviato."), base))
            else:
                el.append(Paragraph(_pt("Referti e certificati archiviati (documenti originali conservati nell'app)"), h2))
                el.append(tabella(["Data", "Documento", "Tipo", "Esito / conclusioni lette dal documento"], [[an_data_it(d_.get("data")), d_.get("titolo"), d_.get("tipo"), (d_.get("campi") or {}).get("esito") or (d_.get("campi") or {}).get("diagnosi")] for d_ in an_ordina(docs, "data")], [0.12, 0.26, 0.2, 0.42]))
        elif s == "cronologia":
            intesta(s)
            righe = []
            for cat, ch, et in (("visite", "data", "Visita"), ("terapie", "dal", "Terapia"), ("interventi", "data", "Intervento / ricovero"), ("esami", "data", "Esame"), ("vaccini", "data", "Vaccinazione / prevenzione")):
                for r in an_voci(a, cat, aid):
                    if not _in_periodo(r, [ch], dal, al):
                        continue
                    t_, det = an_riassunto_voce(cat, r)
                    righe.append((str(r.get(ch) or ""), et, t_, det, "Veterinario" if r.get("fonte") == "veterinario" else "Proprietario"))
            righe.sort(key=lambda z: z[0])
            if not righe:
                el.append(Paragraph(_pt("Nessuna visita o terapia registrata."), base))
            else:
                el.append(Paragraph(_pt("In ordine di data, dalla più vecchia. La colonna «Chi» dice chi ha scritto l'informazione."), piccolo))
                el.append(tabella(["Data", "Tipo", "Che cosa", "Dettagli", "Chi"], [[an_data_it(z[0]), z[1], z[2], z[3], z[4]] for z in righe], [0.11, 0.15, 0.2, 0.42, 0.12]))
        elif s == "peso":
            intesta(s)
            pesi = [r for r in an_ordina(an_voci(a, "peso", aid), "data", recenti_prima=False) if _in_periodo(r, ["data"], dal, al)]
            punti = []
            for r in pesi:
                try:
                    punti.append((an_data(r.get("data")), float(str(r.get("kg")).replace(",", ".")), r.get("note")))
                except (ValueError, TypeError):
                    pass
            if not punti:
                el.append(Paragraph(_pt("Nessun peso registrato."), base))
            else:
                if len(punti) >= 2 and all(p[0] for p in punti):
                    dr = Drawing(170 * mm, 55 * mm)
                    lp = LinePlot()
                    lp.x, lp.y, lp.width, lp.height = 14 * mm, 8 * mm, 148 * mm, 42 * mm
                    lp.data = [[(p[0].toordinal(), p[1]) for p in punti]]
                    lp.lines[0].strokeColor = colors.HexColor(_AN_ORO)
                    lp.lines[0].strokeWidth = 1.6
                    lp.lines[0].symbol = None
                    lp.xValueAxis.labelTextFormat = lambda v: date.fromordinal(int(v)).strftime("%d/%m/%y")
                    lp.xValueAxis.labels.fontSize = 6.5
                    lp.yValueAxis.labels.fontSize = 6.5
                    if len(punti) <= 8:
                        lp.xValueAxis.valueSteps = [p[0].toordinal() for p in punti]
                    dr.add(lp)
                    el.append(dr)
                    var = punti[-1][1] - punti[0][1]
                    el.append(Paragraph(_pt(f"Primo peso: {punti[0][1]:g} kg il {an_data_it(punti[0][0].isoformat())} - ultimo peso: {punti[-1][1]:g} kg il {an_data_it(punti[-1][0].isoformat())} "
                                            f"(variazione {var:+.2f} kg)."), base))
                el.append(tabella(["Data", "Peso (kg)", "Note"], [[an_data_it(p[0].isoformat()) if p[0] else "", f"{p[1]:g}", p[2]] for p in punti], [0.2, 0.2, 0.6]))
                el.append(Paragraph(_pt("I pesi sono annotazioni del proprietario, salvo diversa indicazione del veterinario."), piccolo))
        elif s == "alimentazione":
            intesta(s)
            al_ = x.get("alimentazione") or {}
            righe = [[k, v] for k, v in (("Che cosa mangia", al_.get("tipo")), ("Marca o prodotto", al_.get("marca")), ("Quanto e quante volte", al_.get("quantita")), ("Integratori", al_.get("integratori")), ("Note", al_.get("note"))) if v]
            el.append(tabella(["Voce", "Descrizione (annotazione del proprietario)"], righe, [0.3, 0.7], stile_prop=True) if righe else Paragraph(_pt("Alimentazione non descritta."), base))
        elif s == "habitat":
            ha = x.get("habitat") or {}
            if not (ha.get("descrizione") or ha.get("parametri")):
                continue
            intesta(s)
            el.append(tabella(["Voce", "Descrizione (annotazione del proprietario)"], [[k, v] for k, v in (("Dove vive", ha.get("descrizione")), ("Parametri", ha.get("parametri"))) if v], [0.3, 0.7], stile_prop=True))
        elif s == "diario":
            voci = [r for r in an_ordina(an_voci(a, "diario", aid), "data") if _in_periodo(r, ["data"], dal, al)]
            intesta(s)
            if not voci:
                el.append(Paragraph(_pt("Nessuna annotazione nel diario."), base))
            else:
                el.append(Paragraph(_pt("Annotazioni del proprietario"), h2p))
                el.append(tabella(["Data", "Annotazione"], [[an_data_it(r.get("data")), r.get("testo")] for r in voci[:80]], [0.15, 0.85], stile_prop=True))
        elif s == "spese":
            voci = [r for r in an_ordina(an_voci(a, "spese", aid), "data") if _in_periodo(r, ["data"], dal, al)]
            intesta(s)
            if not voci:
                el.append(Paragraph(_pt("Nessuna spesa registrata."), base))
            else:
                tot = 0.0
                for r in voci:
                    try:
                        tot += float(str(r.get("importo") or 0).replace(",", "."))
                    except (ValueError, TypeError):
                        pass
                el.append(tabella(["Data", "Voce", "Importo"], [[an_data_it(r.get("data")), r.get("voce"), (f"{float(str(r['importo']).replace(',', '.')):.2f} EUR" if r.get("importo") not in (None, "") else "")] for r in voci], [0.18, 0.62, 0.2]))
                el.append(Paragraph(_pt(f"Totale: {tot:.2f} EUR"), base))
        elif s == "documenti":
            docs = [d_ for d_ in an_voci(a, "documenti", aid) if _in_periodo(d_, ["data"], dal, al)]
            intesta(s)
            if not docs:
                el.append(Paragraph(_pt("Nessun documento archiviato."), base))
            else:
                el.append(tabella(["Data", "Documento", "Tipo", "Scadenza", "Origine"], [[an_data_it(d_.get("data")), d_.get("titolo"), d_.get("tipo"), an_data_it(d_.get("scadenza")),
                                                                                            "Veterinario" if d_.get("fonte") == "veterinario" else "Altro"] for d_ in an_ordina(docs, "data")], [0.12, 0.4, 0.24, 0.12, 0.12]))
                if variante == "H":
                    el.append(Paragraph(_pt("I documenti originali scelti sono allegati in fondo a questo PDF."), piccolo))
        elif s == "scadenze":
            intesta(s)
            sc = an_scadenze(a, oggi_, 365)
            mie = [(g, t) for g, t in sc if an_nome(a, aid) in t]
            if not mie:
                el.append(Paragraph(_pt("Nessuna scadenza o visita in programma."), base))
            else:
                el.append(tabella(["Quando", "Che cosa"], [[("tra %d giorni" % g) if g > 1 else ("domani" if g == 1 else ("oggi" if g == 0 else "in ritardo di %d giorni" % -g)), re.sub(r"^\W+\s*", "", t)] for g, t in mie], [0.22, 0.78]))
        elif s == "contatti":
            voci = an_voci(a, "contatti")
            if not voci:
                continue
            intesta(s)
            el.append(tabella(["Nome", "Chi è", "Telefono", "Email"], [[r.get("nome"), r.get("ruolo"), r.get("tel"), r.get("email")] for r in voci], [0.3, 0.22, 0.22, 0.26]))
    doc.multiBuild(el)
    pdf = buf.getvalue()
    if variante == "H" or (allegati_ids is not None and allegati_ids):
        pdf = _aggiungi_allegati(pdf, a, aid, allegati_ids)
    return pdf


def _aggiungi_allegati(pdf, a, aid, ids=None):
    """In fondo al report i documenti originali scelti: i PDF si uniscono, le foto diventano pagine."""
    try:
        import pypdf
    except Exception:
        return pdf
    docs = [d_ for d_ in an_voci(a, "documenti", aid) if (ids is None or d_.get("id") in ids)]
    if not docs:
        return pdf
    w = pypdf.PdfWriter()
    for p in pypdf.PdfReader(io.BytesIO(pdf)).pages:
        w.add_page(p)
    for d_ in docs:
        for r in d_.get("allegati") or []:
            dati = an_leggi_file(r)
            if not dati:
                continue
            try:
                if r.get("mime") == "application/pdf":
                    rd = pypdf.PdfReader(io.BytesIO(dati))
                    inizio = len(w.pages)
                    for p in rd.pages:
                        w.add_page(p)
                    w.add_outline_item(f"Allegato: {d_.get('titolo', '')}"[:80].encode("cp1252", "ignore").decode("cp1252"), inizio)
                elif str(r.get("mime", "")).startswith("image/"):
                    from PIL import Image as _PI, ImageOps
                    from reportlab.lib.pagesizes import A4
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.utils import ImageReader
                    im = ImageOps.exif_transpose(_PI.open(io.BytesIO(dati))).convert("RGB")
                    im.thumbnail((1800, 1800))
                    b = io.BytesIO()
                    c = canvas.Canvas(b, pagesize=A4)
                    pw, ph = A4
                    c.setFont("Helvetica", 8)
                    c.drawString(36, ph - 28, f"Allegato: {d_.get('titolo', '')}"[:90].encode("cp1252", "ignore").decode("cp1252"))
                    ir = ImageReader(im)
                    s = min((pw - 72) / im.width, (ph - 90) / im.height)
                    c.drawImage(ir, (pw - im.width * s) / 2, ph - 44 - im.height * s, im.width * s, im.height * s)
                    c.showPage()
                    c.save()
                    inizio = len(w.pages)
                    for p in pypdf.PdfReader(io.BytesIO(b.getvalue())).pages:
                        w.add_page(p)
                    w.add_outline_item(f"Allegato: {d_.get('titolo', '')}"[:80].encode("cp1252", "ignore").decode("cp1252"), inizio)
            except Exception:
                continue
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


def an_report_zip(pdf, nome_pdf, a, aid, ids=None):
    """Il pacchetto: il report + gli originali dei documenti scelti."""
    buf = io.BytesIO()
    docs = [d_ for d_ in an_voci(a, "documenti", aid) if ids is None or d_.get("id") in ids]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(nome_pdf, pdf)
        usati = set()
        for d_ in docs:
            for r in d_.get("allegati") or []:
                dati = an_leggi_file(r)
                if not dati:
                    continue
                nome = "documenti_originali/" + re.sub(r"[\\/:*?\"<>|]+", "_", r.get("nome") or "file")
                base, _, est = nome.rpartition(".")
                cand, n = nome, 1
                while cand in usati:
                    n += 1
                    cand = f"{base or nome} ({n})" + (f".{est}" if base else "")
                usati.add(cand)
                z.writestr(cand, dati)
    return buf.getvalue()


def an_report_nome_file(x, estensione="pdf"):
    nome = re.sub(r"[^A-Za-z0-9_-]+", "_", str(x.get("nome") or "animale")).strip("_") or "animale"
    return f"Report_veterinario_{nome}_{_an_oggi().isoformat()}.{estensione}"


def an_tab_report(a, x):
    st.markdown("#### 📄 Genera report veterinario PDF")
    st.caption(f"Un PDF ordinato di **{x.get('nome', '')}**, con indice e foto, da consegnare al veterinario, a una clinica o a uno specialista. Le diagnosi e le prescrizioni del veterinario restano separate dalle mie annotazioni.")
    chiavi = list(AN_VARIANTI)
    var = st.radio("Che report vuoi?", chiavi, format_func=lambda k: AN_VARIANTI[k][0], key=f"an_rep_var_{x['id']}")
    sezioni = None
    if var == "G":
        tutte = list(AN_SEZ_REPORT)
        sezioni = st.multiselect("Cosa includere", tutte, default=["anagrafica", "vaccini", "visite", "terapie_attuali"], format_func=lambda k: AN_SEZ_REPORT[k], key=f"an_rep_sez_{x['id']}")
    tutto = st.checkbox("Tutto lo storico", value=True, key=f"an_rep_tutto_{x['id']}")
    dal = al = None
    if not tutto:
        c1, c2 = st.columns(2)
        dal = c1.date_input("Dal", value=date(_an_oggi().year, 1, 1), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=f"an_rep_dal_{x['id']}")
        al = c2.date_input("Al", value=_an_oggi(), min_value=date(1990, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY", key=f"an_rep_al_{x['id']}")
    docs = an_voci(a, "documenti", x["id"])
    ids = None
    zip_orig = False
    if docs:
        if var == "H":
            scelti = st.multiselect("Allegati da mettere in fondo al PDF", [d_["id"] for d_ in docs], default=[d_["id"] for d_ in docs],
                                    format_func=lambda i: next((d_.get("titolo", "") for d_ in docs if d_["id"] == i), i), key=f"an_rep_all_{x['id']}")
            ids = set(scelti)
        zip_orig = st.checkbox("📦 Voglio anche il pacchetto ZIP con il report e gli originali dei documenti", value=(var == "H"), key=f"an_rep_zip_{x['id']}")
    if st.button("📄 Genera il PDF", type="primary", key=f"an_rep_go_{x['id']}", width="stretch"):
        if var == "G" and not sezioni:
            st.error("Scegli almeno una sezione.")
        else:
            with st.spinner("Preparo il report…"):
                nome_ut = (st.session_state.get("sess") or {}).get("nome", "")
                pdf = an_report_pdf(a, x["id"], var, sezioni, dal, al, ids, nome_ut)
            if pdf is None:
                st.error("Non riesco a creare il PDF: manca la libreria reportlab (si installa con requirements.txt).")
            else:
                st.session_state[f"an_rep_{x['id']}"] = {"pdf": pdf, "nome": an_report_nome_file(x), "var": var, "zip": an_report_zip(pdf, an_report_nome_file(x), a, x["id"], ids) if zip_orig else None}
    r = st.session_state.get(f"an_rep_{x['id']}")
    if r:
        st.success(f"✅ Report pronto ({len(r['pdf']) // 1024} KB).")
        st.download_button("⬇ Scarica il PDF", r["pdf"], file_name=r["nome"], mime="application/pdf", key=f"an_rep_dl_{x['id']}", type="primary", width="stretch")
        if r.get("zip"):
            st.download_button("⬇ Scarica il pacchetto ZIP (report + originali)", r["zip"], file_name=r["nome"].replace(".pdf", ".zip"), mime="application/zip", key=f"an_rep_dlz_{x['id']}", width="stretch")
        if "inv_voce" in globals():
            allegati = [(r["nome"], "application/pdf", r["pdf"])] + ([(r["nome"].replace(".pdf", ".zip"), "application/zip", r["zip"])] if r.get("zip") else [])
            inv_voce(f"anrep_{x['id']}", "📤 Invia il report (veterinario, clinica, famiglia…)", f"Report veterinario di {x.get('nome', '')}",
                     f"Report veterinario di {x.get('nome', '')} ({AN_VARIANTI[r['var']][0]}), generato il {an_data_it(_an_oggi().isoformat())}.", lambda al_=allegati: al_)
        try:
            try:
                import pymupdf as _mu
            except Exception:
                import fitz as _mu
            pg = _mu.open(stream=r["pdf"], filetype="pdf")
            st.image(pg[0].get_pixmap(dpi=70).tobytes("png"), caption=f"Anteprima della copertina ({pg.page_count} pagine)", width="stretch")
        except Exception:
            pass
