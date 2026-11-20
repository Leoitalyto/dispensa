# -*- coding: utf-8 -*-
"""📖 IL LETTORE UNICO: lettura e catalogazione dei documenti con l'IA, UGUALE in tutta l'app (prefisso lu_).

RICHIESTA (Leonardo, 20 novembre): una soluzione più efficace per leggere e catalogare. Concordato:
1) un solo lettore per tutte le sezioni (I miei documenti, Casa, Lavoro, Auto, Animali; la Salute ha già il suo, ia_lettura.py);
2) lettura in DUE TEMPI: prima «che documento è» (fra i tipi della sezione), poi i dati con la SCHEDA SU MISURA di quel tipo (campi e regole);
3) CONTROLLI dopo la lettura: codice fiscale (carattere di controllo), numero della carta d'identità, passaporto, tessera sanitaria, targa, telaio,
   IBAN, POD/PDR, date (scadenza dopo il rilascio, rilascio non nel futuro, durata della carta d'identità…). Un campo che non passa resta
   «🟠 da verificare» e NON si propone come sicuro;
6) RICATALOGARE quello che c'è già, in ogni sezione, come in Salute: lavoro in sottofondo (continua anche con altre app), riquadro dal vivo,
   ogni documento salvato appena letto («controllato» o «proposta da confermare»), ✅ Applica / ✖ Non applicare, conto che scende.
Niente si cambia senza conferma. Usa le chiavi di ia_lettura.py (servizi gratuiti; DeepSeek solo per chi può)."""
import datetime as _lu_dt
import os as _lu_os
import html as _lu_html
import re as _lu_re
import threading as _lu_thr
import time as _lu_time

import streamlit as st

# ---------------------------------------------------------------------------------------------------------------------
# 1. LE SCHEDE SU MISURA: per ogni tipo, i campi da leggere e le regole
# ---------------------------------------------------------------------------------------------------------------------
_LU_ID = {"numero": "numero del documento", "ente": "chi l'ha rilasciato", "rilascio": "data di emissione/rilascio AAAA-MM-GG", "scadenza": "data di scadenza AAAA-MM-GG"}
LU_SCHEDE = {
    # --- I miei documenti
    "Carta d'identità": (dict(_LU_ID, cf="codice fiscale (16 caratteri) se c'è", nascita="data di nascita AAAA-MM-GG"),
                         "Carta d'identità elettronica (CIE): NUMERO in alto a destra, 2 lettere + 5 cifre + 2 lettere (es. CA21222IJ). «EMISSIONE / ISSUING» = rilascio; «SCADENZA / EXPIRY» = scadenza "
                         "(di solito il giorno del compleanno, 5 o 10 anni dopo). Ente: «Comune di …» (se non si vede: Ministero dell'Interno). Carta cartacea: numero tipo AX 1234567."),
    "Patente di guida": (dict(_LU_ID, nascita="data di nascita AAAA-MM-GG"), "Patente UE: campo 3 = nascita, 4a = rilascio, 4b = scadenza, 4c = ente (es. MIT-UCO, Prefettura), 5 = numero (10 caratteri, es. U1A2345678B o TO1234567A)."),
    "Passaporto": (dict(_LU_ID, nascita="data di nascita AAAA-MM-GG"), "Numero: 2 lettere + 7 cifre (es. YA1234567). «Data di rilascio», «Data di scadenza», autorità (Questura di … / Ministero degli Affari Esteri)."),
    "Tessera sanitaria": ({"numero": "numero di identificazione della tessera (20 cifre, sul retro)", "cf": "codice fiscale (16 caratteri)", "scadenza": "data di scadenza AAAA-MM-GG", "ente": "Ministero dell'Economia e delle Finanze / Regione"},
                          "Il codice fiscale è sul fronte; il numero di 20 cifre è sul retro. La data di scadenza è sul fronte."),
    "Permesso di soggiorno": (_LU_ID, "Rilasciato dalla Questura; leggi il numero del documento e le date di rilascio e scadenza."),
    "Codice fiscale": ({"numero": "codice fiscale (16 caratteri)", "scadenza": "data di scadenza AAAA-MM-GG se c'è"}, "Il codice fiscale ha 16 caratteri: 6 lettere, 2 cifre, 1 lettera, 2 cifre, 1 lettera, 3 cifre, 1 lettera."),
    # --- Casa
    "Bolletta o fattura": ({"ente": "fornitore (es. Enel Energia, Iren, SMAT, TIM)", "argomento": "Luce | Gas | Luce e Gas | Acqua | Telefono e Internet | Rifiuti (TARI) | Condominio | Altro",
                            "numero_doc": "numero della fattura/bolletta", "data_doc": "data di emissione AAAA-MM-GG", "importo": "totale da pagare, es. 85,40", "scadenza_doc": "scadenza del pagamento AAAA-MM-GG",
                            "periodo_da": "inizio periodo fatturato AAAA-MM-GG", "periodo_a": "fine periodo fatturato AAAA-MM-GG", "codice_cliente": "codice cliente", "codice_fornitura": "POD (luce, IT…E…) o PDR (gas, 14 cifre)",
                            "consumo": "consumo del periodo (numero)", "iban": "IBAN se c'è (domiciliazione)"},
                           "Il totale da pagare non è l'imponibile né l'IVA. Il periodo fatturato è diverso dalla data di emissione e dalla scadenza. POD luce: IT + 3 cifre + E + 8 cifre (es. IT001E12345678). PDR gas: 14 cifre."),
    "Ricevuta di pagamento": ({"ente": "chi ha ricevuto il pagamento", "data_doc": "data del pagamento AAAA-MM-GG", "importo": "importo pagato", "numero_doc": "numero della bolletta/avviso pagato"}, ""),
    "Polizza assicurativa": ({"ente": "compagnia assicurativa", "numero_doc": "numero di polizza", "data_doc": "data di emissione o decorrenza AAAA-MM-GG", "scadenza_doc": "scadenza AAAA-MM-GG", "importo": "premio totale"}, ""),
    "Contratto": ({"ente": "l'altra parte (azienda, proprietario…)", "numero_doc": "numero del contratto", "data_doc": "data della firma AAAA-MM-GG", "scadenza_doc": "scadenza o rinnovo AAAA-MM-GG", "importo": "canone/importo"}, ""),
    "Fattura o scontrino": ({"ente": "negozio o azienda", "data_doc": "data di acquisto AAAA-MM-GG", "importo": "totale", "marca": "marca del prodotto", "modello": "modello", "seriale": "numero di serie", "sottocategoria": "che prodotto è"},
                            "La data di acquisto serve per la garanzia: leggila bene."),
    "Manuale": ({"marca": "marca", "modello": "modello esatto", "sottocategoria": "che apparecchio è (es. Lavatrice)", "lingua": "it|en|de|fr|es", "data_doc": "data del documento AAAA-MM-GG", "seriale": "numero di serie se c'è"}, ""),
    "Lettera o comunicazione": ({"ente": "chi scrive", "data_doc": "data AAAA-MM-GG", "scadenza_doc": "eventuale scadenza AAAA-MM-GG", "importo": "eventuale importo"}, ""),
    # --- Lavoro
    "Busta paga": ({"ente": "datore di lavoro", "competenza": "mese di competenza AAAA-MM", "mensilita": "Mensile | 13ª mensilità | 14ª mensilità | Altra", "netto": "netto in busta, es. 1450,00",
                    "lordo": "totale competenze lorde", "trattenute": "totale trattenute"}, "Il mese di competenza è quello lavorato (non la data di pagamento). Il netto è «netto del mese / netto in busta»."),
    "Certificazione Unica (CU)": ({"ente": "chi l'ha emessa", "cu_anno": "anno della CU (AAAA)", "cu_anno_imposta": "anno d'imposta dei redditi (AAAA, di solito l'anno prima)", "cu_reddito": "redditi di lavoro dipendente o pensione (punto 1 o 2)",
                                   "cu_ritenute": "ritenute IRPEF (punto 21)", "cu_add_reg": "addizionale regionale (punto 22)", "cu_add_com": "addizionale comunale (punti 26-27)"}, ""),
    "Documento INPS": ({"inps_tipo": "che documento INPS è (es. Estratto conto contributivo, ECOCERT, Cedolino della pensione, NASpI)", "data_doc": "data AAAA-MM-GG"}, ""),
    # --- Auto
    "Carta di circolazione": ({"targa": "targa (2 lettere, 3 cifre, 2 lettere)", "telaio": "telaio (E), 17 caratteri", "data": "data di immatricolazione (B) AAAA-MM-GG"}, "Targa italiana: AA123BB. Telaio: 17 caratteri senza I, O, Q."),
    "Polizza (veicolo)": ({"titolo": "titolo breve, es. Polizza RCA 12345", "data": "decorrenza AAAA-MM-GG", "scadenza": "scadenza AAAA-MM-GG", "importo": "premio totale", "targa": "targa assicurata"}, ""),
    "Bollo": ({"titolo": "es. Bollo 2026", "data": "data del pagamento AAAA-MM-GG", "scadenza": "scadenza del bollo AAAA-MM-GG", "importo": "importo", "targa": "targa"}, ""),
    "Revisione": ({"titolo": "es. Revisione 2026", "data": "data della revisione AAAA-MM-GG", "scadenza": "prossima revisione AAAA-MM-GG", "targa": "targa"}, ""),
    "Documento veicolo": ({"titolo": "titolo breve", "data": "data AAAA-MM-GG", "scadenza": "scadenza AAAA-MM-GG se c'è", "importo": "importo se c'è", "targa": "targa se c'è"}, ""),
    # --- Animali
    "Documento veterinario": ({"data": "data del documento AAAA-MM-GG", "scadenza": "scadenza AAAA-MM-GG", "richiamo": "prossimo richiamo AAAA-MM-GG", "microchip": "microchip (15 cifre)",
                               "veterinario": "veterinario", "importo": "importo se è una fattura"}, "Il microchip ha 15 cifre. Il richiamo del vaccino è una data futura."),
    # --- generico
    "Altro": ({"numero": "numero o identificativo", "ente": "chi l'ha emesso", "data_doc": "data AAAA-MM-GG", "scadenza": "scadenza AAAA-MM-GG se c'è", "importo": "importo se c'è"}, ""),
}


def _lu_scheda(tipo, sezione):
    """La scheda per quel tipo (anche dai nomi dei tipi delle sezioni)."""
    if tipo in LU_SCHEDE:
        return LU_SCHEDE[tipo]
    t = str(tipo or "").lower()
    if sezione == "animali":
        return LU_SCHEDE["Documento veterinario"]
    if sezione == "auto":
        for k, c in (("circolazione", "Carta di circolazione"), ("polizza", "Polizza (veicolo)"), ("bollo", "Bollo"), ("revisione", "Revisione")):
            if k in t:
                return LU_SCHEDE[c]
        return LU_SCHEDE["Documento veicolo"]
    for k, c in (("manuale", "Manuale"), ("scheda tecnica", "Manuale"), ("garanzia", "Fattura o scontrino"), ("istruzioni", "Manuale"), ("libretto di impianto", "Manuale"),
                 ("conformit", "Manuale"), ("intervento", "Fattura o scontrino"), ("polizza", "Polizza assicurativa"), ("assicurazione", "Polizza assicurativa"),
                 ("contratto", "Contratto"), ("affitto", "Contratto"), ("patente", "Patente di guida"), ("tessera sanitaria", "Tessera sanitaria")):
        if k in t:
            return LU_SCHEDE[c]
    return LU_SCHEDE["Altro"] if sezione == "documenti" else LU_SCHEDE.get("Lettera o comunicazione")


# ---------------------------------------------------------------------------------------------------------------------
# 3. I CONTROLLI dopo la lettura
# ---------------------------------------------------------------------------------------------------------------------
_LU_CF_DISP = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23]


def lu_cf_valido(cf):
    cf = _lu_re.sub(r"\s", "", str(cf or "")).upper()
    if not _lu_re.fullmatch(r"[A-Z]{6}[0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]", cf):
        return False
    val = lambda ch: int(ch) if ch.isdigit() else ord(ch) - 65
    s = sum(_LU_CF_DISP[val(ch)] if i % 2 == 0 else val(ch) for i, ch in enumerate(cf[:15]))
    return chr(65 + s % 26) == cf[15]


def lu_iban_valido(iban):
    s = _lu_re.sub(r"\s", "", str(iban or "")).upper()
    if not _lu_re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s):
        return False
    n = "".join(str(int(ch, 36)) for ch in s[4:] + s[:4])
    return int(n) % 97 == 1


def _lu_d(v):
    try:
        return _lu_dt.date.fromisoformat(str(v)[:10])
    except Exception:
        return None


def lu_controlla(tipo, campi):
    """{campo: perché non torna}."""
    p = {}
    oggi_ = _lu_dt.date.today()
    num = _lu_re.sub(r"\s", "", str(campi.get("numero") or "")).upper()
    if campi.get("cf") and not lu_cf_valido(campi["cf"]):
        p["cf"] = "il codice fiscale non supera il controllo (forse una lettera letta male)"
    if num:
        if tipo == "Carta d'identità" and not _lu_re.fullmatch(r"[A-Z]{2}\d{5}[A-Z]{2}|[A-Z]{2}\d{7}", num):
            p["numero"] = "non ha il formato della carta d'identità (es. CA12345AB)"
        elif tipo == "Passaporto" and not _lu_re.fullmatch(r"[A-Z]{2}\d{7}", num):
            p["numero"] = "non ha il formato del passaporto (2 lettere + 7 cifre)"
        elif tipo == "Tessera sanitaria" and not _lu_re.fullmatch(r"\d{20}", num) and not lu_cf_valido(num):
            p["numero"] = "il numero della tessera ha 20 cifre"
        elif tipo == "Codice fiscale" and not lu_cf_valido(num):
            p["numero"] = "il codice fiscale non supera il controllo"
        elif tipo == "Patente di guida" and not _lu_re.fullmatch(r"[A-Z0-9]{9,11}", num):
            p["numero"] = "numero della patente insolito: controllalo"
    if campi.get("targa") and not _lu_re.fullmatch(r"[A-Z]{2}\d{3}[A-Z]{2}", _lu_re.sub(r"\W", "", str(campi["targa"]).upper())):
        p["targa"] = "la targa italiana è AA123BB"
    if campi.get("telaio") and not _lu_re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", _lu_re.sub(r"\W", "", str(campi["telaio"]).upper())):
        p["telaio"] = "il telaio ha 17 caratteri (senza I, O, Q)"
    if campi.get("iban") and not lu_iban_valido(campi["iban"]):
        p["iban"] = "l'IBAN non supera il controllo"
    cf_ = _lu_re.sub(r"\s", "", str(campi.get("codice_fornitura") or "")).upper()
    if cf_ and not (_lu_re.fullmatch(r"IT\d{3}E\d{7,8}", cf_) or _lu_re.fullmatch(r"\d{14}", cf_)):
        p["codice_fornitura"] = "POD (IT001E12345678) o PDR (14 cifre) con un formato insolito"
    if campi.get("microchip") and not _lu_re.fullmatch(r"\d{15}", _lu_re.sub(r"\D", "", str(campi["microchip"]))):
        p["microchip"] = "il microchip ha 15 cifre"
    ril = _lu_d(campi.get("rilascio") or campi.get("data_doc") or campi.get("data"))
    sca = _lu_d(campi.get("scadenza") or campi.get("scadenza_doc"))
    nas = _lu_d(campi.get("nascita"))
    k_ril = "rilascio" if campi.get("rilascio") else ("data_doc" if campi.get("data_doc") else "data")
    k_sca = "scadenza" if campi.get("scadenza") else "scadenza_doc"
    if ril and ril > oggi_ + _lu_dt.timedelta(days=2) and tipo not in ("Bolletta o fattura",):
        p[k_ril] = "la data di rilascio/del documento è nel futuro"
    if ril and sca and sca <= ril and tipo not in ("Ricevuta di pagamento",):
        p[k_sca] = "la scadenza viene prima del rilascio: forse sono scambiate"
    if nas and (ril and ril == nas or sca and sca == nas):
        p["rilascio" if ril == nas else "scadenza"] = "è uguale alla data di nascita: forse è stata presa la data sbagliata"
    if tipo == "Carta d'identità" and ril and sca and not (2 <= (sca - ril).days / 365.25 <= 11.2) and "scadenza" not in p:
        p["scadenza"] = "la carta d'identità dura di solito 3, 5 o 10 anni: controlla le date"
    if campi.get("competenza") and not _lu_re.fullmatch(r"\d{4}-\d{2}", str(campi["competenza"])):
        p["competenza"] = "il mese di competenza va scritto AAAA-MM"
    for k in ("importo", "netto", "lordo", "trattenute"):
        if campi.get(k) and not _lu_re.fullmatch(r"-?\d{1,3}(?:[.\s]?\d{3})*(?:[.,]\d{1,2})?|-?\d+(?:[.,]\d{1,2})?", str(campi[k]).replace("€", "").strip()):
            p[k] = "non sembra un importo"
    return p


# ---------------------------------------------------------------------------------------------------------------------
# 2. LA LETTURA IN DUE TEMPI
# ---------------------------------------------------------------------------------------------------------------------
def _lu_testo_pdf(nome, mime, dati, max_car=7000):
    if not (str(mime or "").endswith("pdf") or str(nome or "").lower().endswith(".pdf")):
        return ""
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        doc = fitz.open(stream=dati, filetype="pdf")
        t = ""
        for i, pag in enumerate(doc):
            if i >= 4 or len(t) > max_car:
                break
            t += pag.get_text() + "\n"
        return t[:max_car]
    except Exception:
        return ""


def lu_attivo():
    if _lu_os.environ.get("VM_LU_FINTO"):
        return True
    return "il_leggi_campi" in globals() and bool(il_disponibili(IL_ORDINE_VISTA))


def lu_leggi(files, sezione, tipi, contesto, testo=""):
    """files = [(nome, mime, byte)] (fronte, retro, pagine). → {tipo, campi, problemi, fonti, dubbi} oppure {} se l'IA non è disponibile."""
    if not lu_attivo():
        return {}
    immagini, testo = [], str(testo or "")
    for nome, mime, dati in files[:3]:
        t_ = _lu_testo_pdf(nome, mime, dati)
        testo += ("\n" + t_) if t_ else ""
        if not t_ or len(t_.strip()) < 300:
            immagini += il_immagini(nome, mime, dati, max_pagine=2)
    immagini = immagini[:3]
    if not immagini and not testo.strip():
        return {}
    # primo tempo: che documento è
    t1, f1 = il_leggi_campi(contesto, {"tipo": "uno di: " + " | ".join(tipi)}, testo=testo, immagini=immagini, quante=1)
    tipo = t1.get("tipo") if t1.get("tipo") in tipi else ""
    # secondo tempo: la scheda su misura
    campi_s, regole = _lu_scheda(tipo, sezione)
    critici = [k for k in ("numero", "scadenza", "data_doc", "importo", "competenza", "data", "netto") if k in campi_s][:3]
    c2, f2 = il_leggi_campi(f"{contesto}. È un documento di tipo «{tipo or 'non chiaro'}»", campi_s, testo=testo, immagini=immagini, quante=2, critici=critici, regole=regole)
    dubbi = c2.pop("_dubbi", [])
    campi = {k: v for k, v in c2.items() if not k.startswith("_")}
    for k in ("numero", "targa", "telaio", "cf"):
        if campi.get(k):
            campi[k] = _lu_re.sub(r"\s+", "", campi[k]).upper()
    fonti = list(dict.fromkeys((f1 or []) + (f2 or [])))
    return {"tipo": tipo, "campi": campi, "problemi": lu_controlla(tipo, campi), "fonti": fonti, "dubbi": dubbi}


# ---------------------------------------------------------------------------------------------------------------------
# 6. RICATALOGARE QUELLO CHE C'È GIÀ: le sezioni
# ---------------------------------------------------------------------------------------------------------------------
def _lu_tipi_documenti():
    cat = globals().get("CATALOGO_DOCUMENTI") or {}
    return [t for lista in cat.values() for t in lista] or ["Carta d'identità", "Passaporto", "Patente di guida", "Tessera sanitaria", "Altro"]


def _lu_file_fa(refs):
    return _fa_inv_allegati(list(refs or [])[:3]) if "_fa_inv_allegati" in globals() else []


def _lu_file_an(refs):
    out = []
    for r in list(refs or [])[:3]:
        b = an_leggi_file(r) if "an_leggi_file" in globals() and r.get("id") else None
        if b:
            out.append((r.get("nome") or "doc", r.get("mime") or "application/octet-stream", b))
    return out


def _lu_docs_auto(d):
    for v in ((d.get("auto") or {}).get("veicoli") or []):
        for x in v.get("documenti") or []:
            yield x


LU_SEZIONI = {
    "documenti": {"nome": "I miei documenti", "contesto": "un DOCUMENTO PERSONALE italiano (identità, patente, tessere, certificati, contratti…)",
                  "docs": lambda d: (d.get("farmacia") or {}).get("documenti") or [], "tipi": _lu_tipi_documenti,
                  "file": lambda x: _lu_file_fa(x.get("allegati")), "campi": {"tipo": "Tipo", "numero": "Numero", "ente": "Rilasciato da", "rilascio": "Rilascio", "scadenza": "Scadenza"}},
    "casa": {"nome": "Casa", "contesto": "un documento di CASA (bolletta, fattura, manuale, garanzia, polizza, contratto, ricevuta…)",
             "docs": lambda d: [x for x in ((d.get("casa") or {}).get("documenti") or []) if x.get("tipo") not in ("Busta paga", "Certificazione Unica (CU)", "Documento INPS")],
             "tipi": lambda: [t for t in (globals().get("CA_TIPI") or []) if t not in ("Busta paga", "Certificazione Unica (CU)", "Documento INPS")],
             "file": lambda x: _lu_file_fa([x["file"]] if x.get("file") else x.get("files")),
             "campi": {"tipo": "Tipo", "argomento": "Argomento", "ente": "Ente", "numero_doc": "Numero", "data_doc": "Data", "importo": "Importo", "scadenza_doc": "Scadenza",
                       "periodo_da": "Periodo dal", "periodo_a": "Periodo al", "codice_fornitura": "POD/PDR", "marca": "Marca", "modello": "Modello", "seriale": "N. di serie"}},
    "lavoro": {"nome": "Lavoro", "contesto": "un documento di LAVORO (busta paga, Certificazione Unica, documento INPS)",
               "docs": lambda d: [x for x in ((d.get("casa") or {}).get("documenti") or []) if x.get("tipo") in ("Busta paga", "Certificazione Unica (CU)", "Documento INPS")],
               "tipi": lambda: ["Busta paga", "Certificazione Unica (CU)", "Documento INPS"], "file": lambda x: _lu_file_fa([x["file"]] if x.get("file") else x.get("files")),
               "campi": {"tipo": "Tipo", "ente": "Ente", "competenza": "Mese", "netto": "Netto", "lordo": "Lordo", "trattenute": "Trattenute", "cu_anno": "Anno CU", "cu_reddito": "Reddito",
                         "cu_ritenute": "Ritenute", "inps_tipo": "Documento INPS", "data_doc": "Data"}},
    "auto": {"nome": "Auto", "contesto": "un documento di un VEICOLO (carta di circolazione, polizza, bollo, revisione, fattura dell'officina…)",
             "docs": lambda d: list(_lu_docs_auto(d)), "tipi": lambda: list(globals().get("_AU_DOC_TIPI") or ["Altro"]), "file": lambda x: _lu_file_fa(x.get("files")),
             "campi": {"tipo": "Tipo", "titolo": "Titolo", "data": "Data", "scadenza": "Scadenza", "importo": "Importo"}},
    "animali": {"nome": "Animali", "contesto": "un documento VETERINARIO di un animale domestico", "docs": lambda d: (d.get("animali") or {}).get("documenti") or [],
                "tipi": lambda: list(globals().get("AN_TIPI_DOC") or ["Altro"]), "file": lambda x: _lu_file_an(x.get("allegati")),
                "campi": {"tipo": "Tipo", "data": "Data", "scadenza": "Scadenza"}},
}


def _lu_valore(x, k):
    v = x.get(k)
    if v in (None, "") and isinstance(x.get("campi"), dict):
        v = x["campi"].get(k)
    return "" if v is None else str(v)


def lu_cambi(sez, x, letto):
    """{campo: [prima, dopo]} solo per i campi della sezione, letti con sicurezza (senza problemi) e diversi da prima. Il tipo solo se è fra quelli della sezione."""
    cfg = LU_SEZIONI[sez]
    out = {}
    nuovi = dict(letto.get("campi") or {})
    if letto.get("tipo"):
        nuovi["tipo"] = letto["tipo"]
    for k in cfg["campi"]:
        v = str(nuovi.get(k) or "").strip()
        if not v or k in (letto.get("problemi") or {}):
            continue
        prima = _lu_valore(x, k).strip()
        if k in (x.get("lu_corretti") or []):                           # corretto a mano dopo una lettura: non si tocca
            continue
        if prima.lower().replace(",", ".") != v.lower().replace(",", "."):
            out[k] = [prima, v]
    return out


def _lu_doc_ok(x):
    return bool(x.get("lettura_lu") or x.get("proposta_lu"))


def lu_da_controllare(sez, d, tutti=False):
    cfg = LU_SEZIONI[sez]
    return [x for x in cfg["docs"](d) if isinstance(x, dict) and x.get("id") and (tutti or not _lu_doc_ok(x))]


def _lu_titolo(x):
    return str(x.get("titolo") or x.get("tipo") or x.get("nome") or "Documento")[:80]


_LU_TL = _lu_thr.local()


@st.cache_resource
def _lu_lavori_globali():
    return {}


_LU_LAVORI = _lu_lavori_globali()
LU_MAX_DOC = 150


def _lu_chi():
    try:
        return str((st.session_state.get("sess") or {}).get("uid") or "anonimo")
    except Exception:
        return "anonimo"


def _lu_salva_esito(percorso, sez, did, voce):
    """Appena letto: «controllato» (niente da cambiare) o «proposta da confermare». Così il conto scende e niente si perde."""
    ora = _lu_time.strftime("%Y-%m-%dT%H:%M:%S")

    def _m(d):
        for x in LU_SEZIONI[sez]["docs"](d):
            if isinstance(x, dict) and x.get("id") == did:
                info = {"tipo": voce.get("tipo"), "problemi": voce.get("problemi"), "fonti": voce.get("fonti"), "dubbi": voce.get("dubbi"), "il": ora}
                if voce.get("cambi"):
                    x["proposta_lu"] = dict(info, cambi=voce["cambi"])
                else:
                    x.pop("proposta_lu", None)
                    x["lettura_lu"] = dict(info, nessun_cambio=True)
    try:
        crea_archivio().modifica(percorso, _m, f"{LU_SEZIONI[sez]['nome']}: documento controllato con l'IA")
    except Exception:
        pass
    try:
        carica_dati.clear()
    except Exception:
        pass


def _lu_avvia(sez, d, tutti=False):
    k = (_lu_chi(), sez)
    cfg = LU_SEZIONI[sez]
    docs = [dict(x) for x in lu_da_controllare(sez, d, tutti)][:80]
    perm = {p for p in IL_FORNITORI if _il_permesso(p)} if "_il_permesso" in globals() else None
    lav = {"stato": "corre", "i": 0, "n": len(docs), "inizio": _lu_time.time(), "inizio_doc": _lu_time.time(), "segnale": _lu_time.time(), "servizio": "", "titolo": "",
           "fatti": 0, "cambi": 0, "errori": [], "stop": False, "percorso": st.session_state.get("percorso")}
    _LU_LAVORI[k] = lav
    tipi = cfg["tipi"]()

    def _uno(x):
        if _lu_os.environ.get("VM_LU_FINTO"):                              # solo per le prove automatiche: lettura finta
            _lu_time.sleep(float(_lu_os.environ["VM_LU_FINTO"]))
            letto = {"tipo": x.get("tipo") or tipi[0], "campi": {"scadenza": "2031-07-15", "numero": "CA12345AB", "scadenza_doc": "2026-12-31", "data": "2026-01-10"}, "problemi": {}, "fonti": ["groq"], "dubbi": []}
            return dict(letto, cambi=lu_cambi(sez, x, letto))
        files = cfg["file"](x)
        if not files:
            return {"errore": "file non trovato"}
        letto = lu_leggi(files, sez, tipi, cfg["contesto"])
        if not letto:
            return {"errore": "nessun servizio ha risposto"}
        return dict(letto, cambi=lu_cambi(sez, x, letto))

    def _corri():
        try:
            if "_IL_TL" in globals():
                _IL_TL.lavoro, _IL_TL.permessi = lav, perm
            for i, x in enumerate(docs):
                if lav.get("stop"):
                    break
                lav.update(i=i, inizio_doc=_lu_time.time(), segnale=_lu_time.time(), titolo=_lu_titolo(x), servizio="")
                if "_IL_TL" in globals():
                    _IL_TL.scadenza = _lu_time.time() + LU_MAX_DOC
                    _IL_TL.doc_i = i
                ris = {}
                fn = (lambda x=x: _uno(x))
                if "_il_con_controllo" in globals():
                    finito, ris = _il_con_controllo(fn, LU_MAX_DOC + 20)
                    ris = ris if finito and ris else {"errore": "troppo lento, saltato"}
                else:
                    ris = fn()
                if ris.get("errore"):
                    lav["errori"].append(f"{_lu_titolo(x)} ({ris['errore']})")
                else:
                    _lu_salva_esito(lav["percorso"], sez, x["id"], ris)
                    lav["fatti"] += 1
                    lav["cambi"] += 1 if ris.get("cambi") else 0
            lav["stato"] = "fermato" if lav.get("stop") else "fatto"
        except Exception as e_:
            lav["stato"], lav["errore"] = "errore", f"{type(e_).__name__}: {e_}"[:200]
        finally:
            lav["fine"] = _lu_time.time()
            if "_IL_TL" in globals():
                _IL_TL.lavoro = _IL_TL.permessi = _IL_TL.scadenza = None

    t_ = _lu_thr.Thread(target=_corri, daemon=True, name=f"lu_{sez}")
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
        add_script_run_ctx(t_, get_script_run_ctx())
    except Exception:
        pass
    t_.start()


def _lu_vivo(sez):
    @st.fragment(run_every=2)
    def _f():
        lav = _LU_LAVORI.get((_lu_chi(), sez))
        if not lav:
            return
        ora = _lu_time.time()
        if lav["stato"] == "corre" and ora - lav.get("segnale", ora) > LU_MAX_DOC + 90:
            lav.update(stato="errore", errore="la lettura non rispondeva più", fine=ora)
        if lav["stato"] != "corre":
            st.rerun()
        i, n = lav.get("i", 0), max(1, lav.get("n", 1))
        su_doc, tot = int(ora - lav.get("inizio_doc", ora)), int(ora - lav.get("inizio", ora))
        punti = "●" * (1 + tot % 4) + "○" * (3 - tot % 4)
        st.markdown(f"<div style='border:1px solid #38bdf8;border-radius:14px;padding:10px 12px;margin:6px 0'><b>🤖 Lettura in corso {punti}</b><br>"
                    f"📄 Documento <b>{min(i + 1, n)} di {n}</b>: {_lu_html.escape(lav.get('titolo', ''))}<br>⏱️ Su questo documento da <b>{su_doc} s</b><br>"
                    f"🔄 Sto chiedendo a: <b>{_lu_html.escape(lav.get('servizio') or 'preparo il documento…')}</b><br>"
                    f"✅ Letti: <b>{lav.get('fatti', 0)}</b> · da cambiare: <b>{lav.get('cambi', 0)}</b><br>⌛ {tot // 60} min {tot % 60} s</div>", unsafe_allow_html=True)
        st.progress(min(1.0, (i + 0.5) / n))
        st.caption("📱 Puoi usare altre app o spegnere lo schermo: la lettura continua. Ogni documento è salvato appena letto.")
        if st.button("⏹ Ferma la lettura", key=f"lu_stop_{sez}", width="stretch"):
            lav["stop"] = True
    _f()


def _lu_salva_conferma(sez, scelti, tutti_ids):
    """Applica le proposte scelte; tutte diventano «controllate»."""
    scelti, tutti_ids = set(scelti), set(tutti_ids)
    ora = _lu_time.strftime("%Y-%m-%dT%H:%M:%S")
    campi_sez = LU_SEZIONI[sez]["campi"]

    def _m(d):
        for x in LU_SEZIONI[sez]["docs"](d):
            pr = x.get("proposta_lu") if isinstance(x, dict) else None
            if not pr or x.get("id") not in tutti_ids:
                continue
            if x["id"] in scelti:
                for k, (_a, b) in (pr.get("cambi") or {}).items():
                    if k not in campi_sez:
                        continue
                    if k not in x and isinstance(x.get("campi"), dict) and sez == "animali" and k not in ("tipo", "data", "scadenza"):
                        x["campi"][k] = b
                    else:
                        x[k] = b
                x["lettura_lu"] = {k: v for k, v in pr.items() if k != "cambi"} | {"il": ora, "applicata": True}
            else:
                x["lettura_lu"] = {k: v for k, v in pr.items() if k != "cambi"} | {"il": ora, "rifiutata": True}
            x.pop("proposta_lu", None)
    salva(_m, f"{LU_SEZIONI[sez]['nome']}: proposte dell'IA confermate")


def lu_pannello(sez):
    """Il riquadro «🤖 Rileggi e ricataloga con l'IA» in fondo alla sezione."""
    if sez not in LU_SEZIONI:
        return
    try:
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
    except Exception:
        return
    tutti_docs = [x for x in LU_SEZIONI[sez]["docs"](d) if isinstance(x, dict) and x.get("id")]
    if not tutti_docs:
        return
    n, resta = len(tutti_docs), len(lu_da_controllare(sez, d))
    pend = [x for x in tutti_docs if x.get("proposta_lu")]
    lav = _LU_LAVORI.get((_lu_chi(), sez))
    corre = bool(lav and lav["stato"] == "corre")
    if corre or pend:
        with st.container(border=True, key=f"lu_vista_{sez}"):
            st.markdown("<div style='font-weight:700'>🤖 Rileggi e ricataloga con l'IA</div>", unsafe_allow_html=True)
            if corre:
                _lu_vivo(sez)
            if pend:
                st.markdown(f"<div style='font-weight:700;margin:6px 0'>🟡 Proposte da confermare: {len(pend)}</div>", unsafe_allow_html=True)
                scelti = []
                for x in pend:
                    pr = x["proposta_lu"]
                    st.markdown(f"**📄 {_lu_html.escape(_lu_titolo(x))}**")
                    for k, (a, b) in (pr.get("cambi") or {}).items():
                        st.markdown(f"<div style='font-size:.88rem;margin-left:8px'>{LU_SEZIONI[sez]['campi'].get(k, k)}: <s>{_lu_html.escape(str(a or '—'))}</s> → <b>{_lu_html.escape(str(b))}</b></div>",
                                    unsafe_allow_html=True)
                    avvisi = [f"🟠 {LU_SEZIONI[sez]['campi'].get(k, k)}: {m}" for k, m in (pr.get("problemi") or {}).items()] + [f"⚠️ {x_}" for x_ in (pr.get("dubbi") or [])[:2]]
                    if avvisi:
                        st.caption(" · ".join(avvisi))
                    if st.checkbox("Applica a questo documento", value=True, key=f"lu_sc_{sez}_{x['id']}"):
                        scelti.append(x["id"])
                c1, c2 = st.columns(2, gap="small")
                ids = [x["id"] for x in pend]
                if c1.button(f"✅ Applica ({len(scelti)})", key=f"lu_app_{sez}", type="primary", width="stretch", disabled=not scelti):
                    _lu_salva_conferma(sez, scelti, ids)
                    st.toast(f"Aggiornati {len(scelti)} documenti")
                    st.rerun()
                if c2.button("✖ Non applicare", key=f"lu_no_{sez}", width="stretch"):
                    _lu_salva_conferma(sez, [], ids)
                    st.rerun()
    with st.expander("🤖 Rileggi e ricataloga con l'IA"):
        if not lu_attivo():
            st.info("Serve almeno una chiave dei servizi di intelligenza artificiale: l'amministratore la mette in **Utilità → 🤖 Intelligenza artificiale**.")
            return
        st.caption("L'IA rilegge i documenti già archiviati in **due tempi**: prima capisce **che documento è**, poi legge i dati con la **scheda giusta per quel tipo** "
                   "e li **controlla** (codice fiscale, numeri, targhe, date…). Ti mostra **cosa cambierebbe**: niente si cambia senza **✅ Applica**. I dati che non passano i controlli restano 🟠 da verificare.")
        st.markdown(f"**Da controllare: {resta} di {n}**" + (f" · da confermare: {len(pend)} (qui sopra)" if pend else "") + (" · tutti controllati ✅" if not resta and not pend else ""))
        if corre:
            st.caption("La lettura è in corso: la vedi qui sopra.")
            return
        if lav and lav["stato"] != "corre":
            st.caption(f"Ultima lettura: {lav.get('fatti', 0)} documenti controllati" + (" · non letti: " + "; ".join(lav.get("errori", [])[:4]) if lav.get("errori") else "")
                       + (f" · interrotta ({lav.get('errore')})" if lav.get("errore") else ""))
        tutti = st.checkbox(f"Rileggi anche quelli già controllati (tutti i {n})", key=f"lu_tutti_{sez}")
        quanti = n if tutti else resta
        if st.button(f"🔍 Leggi e cataloga {quanti} document" + ("o" if quanti == 1 else "i"), key=f"lu_via_{sez}", width="stretch", disabled=not quanti):
            _lu_avvia(sez, d, tutti)
            st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# dove compare: in fondo a ogni sezione
# ---------------------------------------------------------------------------------------------------------------------
def _lu_aggancia(nome_fn, sez):
    prima = globals().get(nome_fn)
    if not callable(prima) or getattr(prima, "_lu", False):
        return

    def nuova(*a, **k):
        r = prima(*a, **k)
        try:
            lu_pannello(sez)
        except Exception as e_:
            st.caption(f"(rilettura con l'IA non disponibile: {type(e_).__name__})")
        return r
    nuova._lu = True
    nuova.__name__ = nome_fn
    globals()[nome_fn] = nuova


for _lu_fn, _lu_sez in (("schermata_documenti", "documenti"), ("_ca_tab_manuali", "casa"), ("lv_tab_buste", "lavoro"), ("schermata_auto", "auto"), ("schermata_animali", "animali")):
    _lu_aggancia(_lu_fn, _lu_sez)
