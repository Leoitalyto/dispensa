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
import uuid as _lu_uuid
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


LU_CHI_CAMPI = {"intestatario": "NOME E COGNOME della persona a cui il documento è intestato o indirizzato (destinatario della lettera, intestatario della bolletta o del contratto, "
                                "titolare del documento, paziente, assicurato, condòmino). NON chi lo ha scritto o emesso. Vuoto se non c'è.",
                "cf_intestatario": "codice fiscale di quella persona (16 caratteri) se si legge",
                "sezione": "dove va nell'app: salute (referti, analisi, ricette, visite, certificati medici) | documenti (carta d'identità, patente, passaporto, tessera sanitaria, "
                           "codice fiscale, certificati anagrafici) | casa (bollette, condominio e amministrazione, tasse della casa, contratti, manuali, garanzie, assicurazione casa, "
                           "lettere su casa e utenze) | lavoro (busta paga, Certificazione Unica, INPS) | auto (veicoli: bollo, revisione, polizza auto, libretto) | animali (veterinario)"}
LU_CHI_REGOLE = ("Il destinatario di una lettera o bolletta è di solito nel riquadro dell'indirizzo («Gentile Sig.ra…», «Spett.le…», «Intestatario», «Cliente», «Condòmino»). "
                 "Scrivi il nome come è scritto, senza titoli (Sig., Sig.ra, Dott.).")


LU_RIASSUNTO_CAMPI = {"riassunto": "in 1-2 frasi semplici in italiano: che documento è, chi lo manda, a chi, di cosa parla, date e importi principali",
                      "parole_chiave": "6-12 parole utili per ritrovarlo con una ricerca (nomi, ditte, luoghi, oggetti, periodi), separate da virgola"}


def lu_leggi(files, sezione, tipi, contesto, testo="", memoria="", tipo_atteso=""):
    """files = [(nome, mime, byte)] (fronte, retro, pagine). → {tipo, campi, problemi, fonti, dubbi} oppure {} se l'IA non è disponibile.
    Velocità (27/11/2026): se si sa già che tipo dovrebbe essere («tipo_atteso»: quello archiviato, o quello letto dal testo), il secondo tempo
    (la scheda su misura) parte INSIEME al primo. Se il primo tempo conferma il tipo, si usa quella lettura (mezza attesa); se no, si rifà con il tipo giusto."""
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
    def _primo():
        return il_leggi_campi(contesto, {"tipo": "uno di: " + " | ".join(tipi), **LU_CHI_CAMPI}, testo=testo, immagini=immagini, quante=1,
                              regole=LU_CHI_REGOLE + (("\n" + memoria) if memoria else ""))

    def _secondo(tipo_):
        campi_s, regole = _lu_scheda(tipo_, sezione)
        critici = [k for k in ("numero", "scadenza", "data_doc", "importo", "competenza", "data", "netto") if k in campi_s][:3]
        campi_s = dict(campi_s, **LU_RIASSUNTO_CAMPI)
        return il_leggi_campi(f"{contesto}. È un documento di tipo «{tipo_ or 'non chiaro'}»", campi_s, testo=testo, immagini=immagini, quante=2, critici=critici,
                              regole=(regole or "") + (("\n" + memoria) if memoria else ""))
    tipo_atteso = tipo_atteso if tipo_atteso in tipi else ""
    if tipo_atteso and "il_in_parallelo" in globals():
        r1, r2 = il_in_parallelo([_primo, lambda: _secondo(tipo_atteso)], massimo=2)
        t1, f1 = r1 or ({}, [])
    else:
        t1, f1 = _primo()
        r2 = None
    # primo tempo: che documento è
    tipo = t1.get("tipo") if t1.get("tipo") in tipi else ""
    # secondo tempo: la scheda su misura (già pronta se il tipo era quello atteso)
    if r2 and tipo == tipo_atteso:
        c2, f2 = r2
    else:
        c2, f2 = _secondo(tipo)
    dubbi = c2.pop("_dubbi", [])
    riassunto = {k: str(c2.pop(k, "") or "").strip()[:400] for k in LU_RIASSUNTO_CAMPI}
    campi = {k: v for k, v in c2.items() if not k.startswith("_")}
    for k in ("numero", "targa", "telaio", "cf"):
        if campi.get(k):
            campi[k] = _lu_re.sub(r"\s+", "", campi[k]).upper()
    fonti = list(dict.fromkeys((f1 or []) + (f2 or [])))
    chi = {k: str(t1.get(k) or "").strip() for k in LU_CHI_CAMPI}
    chi["cf_intestatario"] = _lu_re.sub(r"\s+", "", chi["cf_intestatario"]).upper()
    if chi["cf_intestatario"] and not lu_cf_valido(chi["cf_intestatario"]):
        chi["cf_intestatario"] = ""
    if not chi.get("cf_intestatario") and lu_cf_valido(campi.get("cf") or ""):
        chi["cf_intestatario"] = campi["cf"]
    return {"tipo": tipo, "campi": campi, "problemi": lu_controlla(tipo, campi), "fonti": fonti, "dubbi": dubbi, "chi": chi,
            "riassunto": riassunto.get("riassunto", ""), "parole": riassunto.get("parole_chiave", "")}


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


# ---------------------------------------------------------------------------------------------------------------------
# 7. DI CHI È E DOVE VA (richiesta del 20 novembre: «se è diretto a mia madre va nelle cose di mia madre: amministrazione, salute…»)
#    Le persone sono i profili della Salute (con «nome e cognome come sui documenti» e codice fiscale); ogni casa può avere la sua persona.
# ---------------------------------------------------------------------------------------------------------------------
LU_SEZ_NOMI = {"salute": "🩺 Salute", "documenti": "🪪 I miei documenti", "casa": "🏠 Casa", "lavoro": "💼 Lavoro", "auto": "🚗 Auto", "animali": "🐾 Animali"}
LU_SPOSTABILI = {("casa", "salute"), ("casa", "documenti"), ("documenti", "salute"), ("documenti", "casa")}
_LU_NON_NOMI = {"sig", "sigra", "signor", "signora", "sigg", "dott", "dottssa", "dottoressa", "spett", "spettle", "gentile", "gent", "egregio", "alla", "al", "per", "di", "de", "del", "della", "e"}


def _lu_parole(x):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode().lower()
    return {w for w in _lu_re.sub(r"[^a-z ]", " ", t).split() if len(w) >= 2 and w not in _LU_NON_NOMI}


def _lu_in_sottofondo():
    """Siamo nel lavoro in sottofondo? Lì NON si tocca st.session_state (se la pagina si ridisegna, Streamlit ferma il filo)."""
    return getattr(globals().get("_IL_TL"), "lavoro", None) is not None


def _lu_nome_sessione():
    if _lu_in_sottofondo():
        return "Io"
    try:
        return (st.session_state.get("sess") or {}).get("nome", "Io")
    except Exception:
        return "Io"


def lu_persone(d):
    """[{id, nome, nomi, cf}]: le persone della famiglia (i profili della Salute)."""
    f = d.get("farmacia") or {}
    prof = f.get("profili") or [{"id": "p0", "nome": _lu_nome_sessione()}]
    out = []
    for p in prof:
        if not isinstance(p, dict) or not p.get("id"):
            continue
        nomi = [p.get("nome", ""), p.get("nome_doc", "")]
        if p["id"] == "p0":
            an = d.get("anagrafica") or {}
            nomi.append(f"{an.get('nome', '')} {an.get('cognome', '')}")
        cf = str(p.get("cf_doc") or "").upper().strip()
        if not cf and "_fa_cf_del_profilo" in globals():
            try:
                cf = _fa_cf_del_profilo(f, p["id"]) or ""
            except Exception:
                cf = ""
        out.append({"id": p["id"], "nome": p.get("nome") or "?", "nomi": [n for n in nomi if str(n).strip()], "cf": cf})
    return out


def lu_chi_e(d, nome, cf=""):
    """La persona a cui è intestato il documento (codice fiscale prima, poi nome e cognome); None se non si capisce con sicurezza."""
    pers = lu_persone(d)
    cf = _lu_re.sub(r"\s+", "", str(cf or "")).upper()
    if cf:
        for p in pers:
            if p["cf"] and p["cf"] == cf:
                return p
    parole = _lu_parole(nome)
    if len(parole) < 2:
        return None
    trovati = []
    for p in pers:
        for n in p["nomi"]:
            t = _lu_parole(n)
            if len(t) >= 2 and (t <= parole or len(t & parole) >= 2):
                trovati.append(p)
                break
    return trovati[0] if len(trovati) == 1 else None


def lu_case_di(d, pid):
    """Le case collegate a quella persona (id; «» = la casa principale)."""
    c = d.get("casa") or {}
    ids = [x["id"] for x in (c.get("case") or []) if isinstance(x, dict) and x.get("id") and (x.get("profilo") or x.get("persona")) == pid]
    if (c.get("persona_principale") or "p0") == pid:
        ids.insert(0, "")
    return ids


def _lu_nome_casa(d, cid):
    if not cid:
        return "Casa principale"
    return next((x.get("nome") or "Casa" for x in ((d.get("casa") or {}).get("case") or []) if isinstance(x, dict) and x.get("id") == cid), "Casa")


def _lu_nome_persona(d, pid):
    return next((p["nome"] for p in lu_persone(d) if p["id"] == pid), "?")


def _lu_file_refs(sez, x):
    if sez == "documenti":
        return [r for r in (x.get("allegati") or []) if isinstance(r, dict) and r.get("id")]
    if sez == "casa":
        return [x["file"]] if isinstance(x.get("file"), dict) and x["file"].get("id") else [r for r in (x.get("files") or []) if isinstance(r, dict) and r.get("id")]
    return []


def _lu_sezione_ia(testo):
    t = str(testo or "").strip().lower()
    for k in LU_SEZ_NOMI:
        if t.startswith(k) or t == k:
            return k
    return ""


def lu_destinazione(sez, x, letto, d):
    """({campo: [prima, dopo]}, {persona, casa_id, sezione}): di chi è e dove va. Solo proposte (si applicano con ✅ Applica)."""
    chi = letto.get("chi") or {}
    p = lu_chi_e(d, chi.get("intestatario"), chi.get("cf_intestatario"))
    dove = _lu_sezione_ia(chi.get("sezione"))
    cambi, dest = {}, {}
    if p:
        dest["persona"] = p["id"]
    if dove and dove != sez and (sez, dove) in LU_SPOSTABILI and not (dove == "salute" and len(_lu_file_refs(sez, x)) > 1):
        per = p["id"] if p else (x.get("profilo") or "p0")
        dest.update(sezione=dove, persona=per)
        if dove == "casa":
            case = lu_case_di(d, per)
            dest["casa_id"] = case[0] if len(case) == 1 else ""
            cambi["sezione"] = [LU_SEZ_NOMI[sez], f"{LU_SEZ_NOMI[dove]} › {_lu_nome_casa(d, dest['casa_id'])}"]
        else:
            cambi["sezione"] = [LU_SEZ_NOMI[sez], f"{LU_SEZ_NOMI[dove]} di {_lu_nome_persona(d, per)}"]
        return cambi, dest
    if dove == "auto" and sez in ("casa", "documenti") and len(_lu_file_refs(sez, x)) >= 1:
        vid = _lu_veicolo_per(d, x, letto)
        if vid:
            dest.update(sezione="auto", veicolo=vid)
            return {"sezione": [LU_SEZ_NOMI[sez], f"{LU_SEZ_NOMI['auto']} › {_lu_nome_veicolo(d, vid)}"]}, dest
    if dove and dove != sez and dove in LU_SEZ_NOMI and not (sez == "casa" and dove == "lavoro" and x.get("tipo") in ("Busta paga", "Certificazione Unica (CU)", "Documento INPS")):
        dest["segnala"] = dove                                           # non si sposta da solo: lo segnalo («📌 forse sta nella sezione sbagliata»)
    if not p:
        return cambi, dest
    if sez == "documenti" and p["id"] != (x.get("profilo") or "p0"):
        cambi["profilo"] = [_lu_nome_persona(d, x.get("profilo") or "p0"), p["nome"]]
    if sez == "casa":
        case = lu_case_di(d, p["id"])
        if len(case) == 1 and case[0] != (x.get("casa_id") or ""):
            dest["casa_id"] = case[0]
            cambi["casa_id"] = [_lu_nome_casa(d, x.get("casa_id") or ""), f"{_lu_nome_casa(d, case[0])} ({p['nome']})"]
    return cambi, dest


def _lu_veicolo_per(d, x, letto=None):
    """Il veicolo del documento: quello con la targa scritta nel documento, oppure l'unico veicolo."""
    veic = [v for v in ((d.get("auto") or {}).get("veicoli") or []) if isinstance(v, dict) and v.get("id")]
    if not veic:
        return None
    testo = _lu_re.sub(r"\s+", "", (_lu_testo_doc(x) + " " + str((letto or {}).get("campi") or "")).upper())
    for v in veic:
        t_ = _lu_re.sub(r"\s+", "", str(v.get("targa") or "")).upper()
        if len(t_) >= 5 and t_ in testo:
            return v["id"]
    return veic[0]["id"] if len(veic) == 1 else None


def _lu_nome_veicolo(d, vid):
    v = next((v for v in ((d.get("auto") or {}).get("veicoli") or []) if v.get("id") == vid), {})
    return " ".join(str(v.get(k) or "") for k in ("marca", "modello") if v.get(k)).strip() + (f" ({v['targa']})" if v.get("targa") else "") or "Veicolo"


def _lu_data_di(x):
    for k in ("data_doc", "data", "rilascio", "scadenza_doc", "scadenza"):
        v = str(x.get(k) or "")
        if _lu_re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return v
    return ""


def _lu_sposta(d, sez, x, dest):
    """Sposta il documento (col suo file, che resta dov'è nell'archivio) nella sezione e nella persona giuste. True se fatto."""
    refs = _lu_file_refs(sez, x)
    if not refs:
        return False
    ora = _lu_time.strftime("%Y-%m-%dT%H:%M:%S")
    titolo = _lu_titolo(x)
    dove, pid = dest.get("sezione"), dest.get("persona") or "p0"
    f = d.setdefault("farmacia", {})
    if dove == "salute":
        prof = f.get("profili") or []
        if not prof:
            prof = f["profili"] = [{"id": "p0", "nome": (st.session_state.get("sess") or {}).get("nome", "Io")}]
        p = next((q for q in prof if q.get("id") == pid), prof[0])
        r = refs[0]
        p.setdefault("docsan", []).append({"id": _lu_uuid.uuid4().hex[:10], "tipo": "Altro", "titolo": titolo, "data": _lu_data_di(x), "struttura": str(x.get("ente") or ""),
                                           "note": str(x.get("note") or ""), "file": {"id": r["id"], "nome": r.get("nome"), "mime": r.get("mime"), "sha": r.get("sha") or r.get("sha256")},
                                           "creato_il": ora, "spostato_da": sez})
    elif dove == "documenti":
        tipi = set(_lu_tipi_documenti())
        f.setdefault("documenti", []).append({"id": _lu_uuid.uuid4().hex[:10], "profilo": pid, "tipo": x.get("tipo") if x.get("tipo") in tipi else "Altro",
                                              "numero": str(x.get("numero") or x.get("numero_doc") or ""), "ente": str(x.get("ente") or ""), "rilascio": x.get("rilascio") or x.get("data_doc") or None,
                                              "scadenza": x.get("scadenza") or x.get("scadenza_doc") or None, "note": (str(x.get("note") or "") + ("\n" if x.get("note") else "") + titolo).strip(),
                                              "allegati": [{"id": r["id"], "nome": r.get("nome"), "mime": r.get("mime"), "sha": r.get("sha") or r.get("sha256")} for r in refs], "spostato_da": sez})
    elif dove == "auto":
        v = next((v for v in ((d.get("auto") or {}).get("veicoli") or []) if v.get("id") == dest.get("veicolo")), None)
        if v is None:
            return False
        tipi = set(globals().get("_AU_DOC_TIPI") or [])
        v.setdefault("documenti", []).append({"id": _lu_uuid.uuid4().hex[:10], "tipo": x.get("tipo") if x.get("tipo") in tipi else "Altro", "titolo": titolo,
                                             "data": _lu_data_di(x) or None, "scadenza": x.get("scadenza") or x.get("scadenza_doc") or None, "importo": x.get("importo"),
                                             "note": str(x.get("note") or ""), "files": [{"id": r["id"], "nome": r.get("nome"), "mime": r.get("mime"), "sha": r.get("sha") or r.get("sha256")} for r in refs],
                                             "spostato_da": sez})
    elif dove == "casa":
        c = d.setdefault("casa", {})
        tipi = set(globals().get("CA_TIPI") or [])
        r = refs[0]
        doc = {"id": _lu_uuid.uuid4().hex[:10], "tipo": x.get("tipo") if x.get("tipo") in tipi else "Lettera o comunicazione", "argomento": "Altro", "titolo": titolo,
               "ente": str(x.get("ente") or ""), "data_doc": _lu_data_di(x), "scadenza_doc": x.get("scadenza") or "", "note": str(x.get("note") or ""), "casa_id": dest.get("casa_id") or "",
               "file": {"id": r["id"], "nome": r.get("nome"), "mime": r.get("mime"), "sha256": r.get("sha") or r.get("sha256"), "originale": True}, "creato_il": ora, "spostato_da": sez,
               "conferma": {"stato": "confermato", "da": (st.session_state.get("sess") or {}).get("nome", ""), "il": ora, "modificati": [], "bene_proposto": ""}}
        if len(refs) > 1:
            doc["files"] = [dict(q, sha256=q.get("sha") or q.get("sha256")) for q in refs]
        c.setdefault("documenti", []).append(doc)
    else:
        return False
    if sez == "documenti":
        f["documenti"] = [q for q in f.get("documenti", []) if q is not x]
    elif sez == "casa":
        d["casa"]["documenti"] = [q for q in d["casa"].get("documenti", []) if q is not x]
    return True


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
                info = {"tipo": voce.get("tipo"), "problemi": voce.get("problemi"), "fonti": voce.get("fonti"), "dubbi": voce.get("dubbi"), "il": ora,
                        "dest": voce.get("dest") or {}, "chi": voce.get("chi") or {}, "riassunto": voce.get("riassunto") or "", "parole": voce.get("parole") or ""}
                if voce.get("cambi"):
                    x["proposta_lu"] = dict(info, cambi=voce["cambi"])
                else:
                    x.pop("proposta_lu", None)
                    x["lettura_lu"] = dict(info, nessun_cambio=True)
    if "il_salva_in_coda" in globals():                                   # in coda: il documento dopo si legge subito, senza aspettare GitHub
        il_salva_in_coda(percorso, _m, f"{LU_SEZIONI[sez]['nome']}: documento controllato con l'IA")
        return
    try:
        crea_archivio().modifica(percorso, _m, f"{LU_SEZIONI[sez]['nome']}: documento controllato con l'IA")
    except Exception:
        pass
    try:
        carica_dati.clear()
    except Exception:
        pass


def _lu_avvia(sez, d, tutti=False, solo=None):
    memoria = lu_memoria_regole(d, sez)
    k = (_lu_chi(), sez)
    cfg = LU_SEZIONI[sez]
    docs = [dict(x) for x in lu_da_controllare(sez, d, tutti) if solo is None or x.get("id") in solo][:80]
    perm = {p for p in IL_FORNITORI if _il_permesso(p)} if "_il_permesso" in globals() else None
    lav = {"stato": "corre", "i": 0, "n": len(docs), "inizio": _lu_time.time(), "inizio_doc": _lu_time.time(), "segnale": _lu_time.time(), "servizio": "", "titolo": "",
           "fatti": 0, "cambi": 0, "errori": [], "stop": False, "percorso": st.session_state.get("percorso")}
    _LU_LAVORI[k] = lav
    tipi = cfg["tipi"]()
    anticipo = {}

    def _lu_con_dest(sez_, x, letto):
        cambi = lu_cambi(sez_, x, letto)
        try:
            c2, dest = lu_destinazione(sez_, x, letto, d)
        except Exception:
            c2, dest = {}, {}
        if c2.get("sezione"):                                              # va in un'altra sezione: gli altri cambi non servono
            cambi = {}
        cambi.update(c2)
        return dict(letto, cambi=cambi, dest=dest)

    def _uno(x):
        if _lu_os.environ.get("VM_LU_FINTO"):                              # solo per le prove automatiche: lettura finta
            _lu_time.sleep(float(_lu_os.environ["VM_LU_FINTO"]))
            letto = {"tipo": x.get("tipo") or tipi[0], "campi": {"scadenza": "2031-07-15", "numero": "CA12345AB", "scadenza_doc": "2026-12-31", "data": "2026-01-10"}, "problemi": {}, "fonti": ["groq"], "dubbi": []}
            letto["riassunto"] = "Documento di prova letto dall'IA: " + _lu_titolo(x)
            letto["parole"] = "prova, " + str(x.get("tipo") or "")
            if _lu_os.environ.get("VM_LU_CHI"):                            # prova: intestatario e sezione finti («nome|cf|sezione»)
                n_, c_, s_ = (_lu_os.environ["VM_LU_CHI"].split("|") + ["", "", ""])[:3]
                letto["chi"] = {"intestatario": n_, "cf_intestatario": c_, "sezione": s_}
            return _lu_con_dest(sez, x, letto)
        pronto = anticipo.pop(x.get("id"), None)
        files = (pronto(60) if pronto else None) or cfg["file"](x)          # il file era già stato scaricato in anticipo (velocità)?
        if not files:
            return {"errore": "file non trovato"}
        letto = lu_leggi(files, sez, tipi, cfg["contesto"], memoria=memoria, tipo_atteso=str(x.get("tipo") or ""))
        if not letto:
            return {"errore": "nessun servizio ha risposto"}
        return _lu_con_dest(sez, x, letto)

    def _corri():
        try:
            if "_IL_TL" in globals():
                _IL_TL.lavoro, _IL_TL.permessi = lav, perm
            for i, x in enumerate(docs):
                if lav.get("stop"):
                    break
                if "il_prepara_dopo" in globals() and not _lu_os.environ.get("VM_LU_FINTO"):    # il file del documento dopo si scarica mentre l'IA legge questo
                    for x_ in docs[i:i + 2]:
                        if x_.get("id") not in anticipo:
                            anticipo[x_.get("id")] = il_prepara_dopo(lambda x_=x_: cfg["file"](x_))
                lav.update(i=i, inizio_doc=_lu_time.time(), segnale=_lu_time.time(), titolo=_lu_titolo(x), servizio="")
                if "_IL_TL" in globals():
                    _IL_TL.scadenza = _lu_time.time() + LU_MAX_DOC
                    _IL_TL.doc_i = i
                ris = {}
                def fn(x=x):
                    try:
                        return _uno(x)
                    except Exception as e_:                                # un errore vero si dice (non «troppo lento»)
                        return {"errore": f"errore {type(e_).__name__}: {str(e_)[:80]}"}
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
            if "il_coda_attendi" in globals():
                il_coda_attendi(lav.get("percorso"))                          # prima di dire «fatto», tutto scritto
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


_lu_sp_proponi_vecchio = globals().get("sp_proponi_profilo")


def sp_proponi_profilo(f, paziente, cf):                                   # noqa: F811 — anche «nome e cognome come sui documenti» e codice fiscale delle persone
    try:
        dd = {"farmacia": f}
        if not _lu_in_sottofondo():                                    # in sottofondo niente session_state (vedi _lu_in_sottofondo)
            try:
                dd["anagrafica"] = carica_dati(crea_archivio(), percorso_mio()).get("anagrafica") or {}
            except Exception:
                pass
        p = lu_chi_e(dd, paziente, cf)
        if p:
            return p["id"], ("codice fiscale" if cf and p["cf"] == _lu_re.sub(r"\s+", "", str(cf)).upper() else "nome")
    except Exception:
        pass
    return _lu_sp_proponi_vecchio(f, paziente, cf) if _lu_sp_proponi_vecchio else (None, "")


def lu_ui_persone():
    """👥 Le persone e le case: come si chiamano sui documenti e di chi è ogni casa. Serve all'IA per mettere ogni documento nelle cose giuste."""
    try:
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
    except Exception:
        return
    f = d.get("farmacia") or {}
    prof = [p for p in (f.get("profili") or []) if isinstance(p, dict) and p.get("id")]
    case = ca_case(d.get("casa") or {}) if "ca_case" in globals() else [{"id": "", "nome": "Casa principale"}]
    with st.popover("👥 Di chi sono i documenti: persone e case", width="stretch"):
        st.caption("L'IA legge **a chi è intestato** ogni documento (lettere, bollette, referti…) e lo propone nelle **cose di quella persona**: i suoi documenti, "
                   "la sua Salute, la **sua casa** (con l'amministrazione). Scrivi qui **nome e cognome come sono scritti sui documenti** e, se lo sai, il **codice fiscale**.")
        if not prof:
            st.info("Le persone sono i profili della Salute: aggiungili in **Salute → 👥 Gestisci profili**.")
        nuovi = {}
        for p in prof:
            st.markdown(f"**👤 {_lu_html.escape(p.get('nome') or '?')}**")
            c1, c2 = st.columns([3, 2], gap="small")
            nd = c1.text_input("Nome e cognome sui documenti", value=p.get("nome_doc", ""), key=f"lu_pp_n_{p['id']}", placeholder="es. Maria Teresa Rossi")
            cf = c2.text_input("Codice fiscale", value=p.get("cf_doc", ""), key=f"lu_pp_c_{p['id']}", max_chars=16)
            nuovi[p["id"]] = (nd.strip(), cf.strip().upper())
        st.markdown("**🏠 Di chi è ogni casa**")
        nomi = {"": "— nessuno —"} | {p["id"]: p.get("nome") or "?" for p in prof}
        cc = d.get("casa") or {}
        scelte = {}
        for x in case:
            att = (cc.get("persona_principale") or ("p0" if "p0" in nomi else "")) if not x["id"] else (x.get("profilo") or x.get("persona") or "")
            scelte[x["id"]] = st.selectbox(x.get("nome") or "Casa", list(nomi), index=list(nomi).index(att) if att in nomi else 0, format_func=lambda i: nomi[i], key=f"lu_pc_{x['id'] or 'princ'}")
        cattivi = [p_ for p_, (_n, c_) in nuovi.items() if c_ and not lu_cf_valido(c_)]
        if cattivi:
            st.warning("🟠 Un codice fiscale non sembra giusto (controlla le 16 lettere e cifre).")
        if st.button("💾 Salva", key="lu_pp_ok", type="primary", width="stretch", disabled=bool(cattivi)):
            def _m(dd, nuovi=nuovi, scelte=scelte):
                for p in (dd.get("farmacia") or {}).get("profili") or []:
                    if p.get("id") in nuovi:
                        p["nome_doc"], p["cf_doc"] = nuovi[p["id"]]
                c_ = dd.setdefault("casa", {})
                for cid, pid in scelte.items():
                    if not cid:
                        c_["persona_principale"] = pid
                    else:
                        for x in c_.get("case") or []:
                            if x.get("id") == cid:
                                x["persona"] = pid
                                x["profilo"] = pid
            salva(_m, "Persone e case per i documenti")
            st.toast("Salvato ✅")
            st.rerun()


_LU_ETICH_DEST = {"profilo": "👤 Di chi è", "casa_id": "🏠 In quale casa", "sezione": "📦 Va spostato in"}


# ---------------------------------------------------------------------------------------------------------------------
# 8. IMPARARE DALLE CORREZIONI: quello che correggi prima di applicare (o il tipo che rifiuti) diventa una regola per le letture dopo
# ---------------------------------------------------------------------------------------------------------------------
LU_MEMORIA_MAX = 60


def _lu_chi_emette(x):
    for k in ("ente", "fornitore", "emittente", "compagnia", "datore", "clinica", "veterinario", "titolo"):
        v = str(x.get(k) or (x.get("campi") or {}).get(k) or "").strip()
        if v:
            return v[:60]
    return ""


def lu_memoria_aggiungi(d, sez, voce):
    m = d.setdefault("lu_memoria", {}).setdefault(sez, [])
    chiave = (voce.get("campo"), str(voce.get("letto")), str(voce.get("giusto")), voce.get("ente"), voce.get("rifiutato", False))
    m[:] = [v for v in m if (v.get("campo"), str(v.get("letto")), str(v.get("giusto")), v.get("ente"), v.get("rifiutato", False)) != chiave]
    m.append(voce)
    del m[:-LU_MEMORIA_MAX]


def lu_memoria_regole(d, sez):
    """Le correzioni passate, scritte come regole per l'IA (le più recenti, al massimo 15)."""
    m = ((d or {}).get("lu_memoria") or {}).get(sez) or []
    if not m:
        return ""
    righe = []
    for v in m[-15:]:
        dove = f"per un documento di «{v['ente']}»" if v.get("ente") else "per un documento simile"
        dove += f" (tipo «{v['tipo']}»)" if v.get("tipo") else ""
        if v.get("rifiutato"):
            righe.append(f"- {dove}: il campo «{v.get('campo')}» NON è «{v.get('letto')}».")
        else:
            righe.append(f"- {dove}: il campo «{v.get('campo')}» era stato letto «{v.get('letto')}», il valore giusto era «{v.get('giusto')}».")
    return "CORREZIONI FATTE DALL'UTENTE IN PASSATO (imparale e non ripetere gli stessi errori):\n" + "\n".join(righe)


def _lu_salva_conferma(sez, scelti, tutti_ids, correzioni=None):
    """Applica le proposte scelte; tutte diventano «controllate». correzioni = {doc_id: {campo: valore giusto}} (si applica quello e si impara)."""
    scelti, tutti_ids = set(scelti), set(tutti_ids)
    correzioni = correzioni or {}
    ora = _lu_time.strftime("%Y-%m-%dT%H:%M:%S")
    campi_sez = LU_SEZIONI[sez]["campi"]

    def _m(d):
        da_spostare = []
        for x in LU_SEZIONI[sez]["docs"](d):
            pr = x.get("proposta_lu") if isinstance(x, dict) else None
            if not pr or x.get("id") not in tutti_ids:
                continue
            if x["id"] in scelti:
                dest = pr.get("dest") or {}
                cam = pr.get("cambi") or {}
                if "profilo" in cam and dest.get("persona"):
                    x["profilo"] = dest["persona"]
                if "casa_id" in cam and "casa_id" in dest:
                    x["casa_id"] = dest["casa_id"]
                if "sezione" in cam and dest.get("sezione"):
                    da_spostare.append((x, dest))
                corr = correzioni.get(x["id"]) or {}
                for k, (_a, b) in cam.items():
                    if k not in campi_sez:
                        continue
                    if k in corr and str(corr[k]).strip() != str(b):
                        giusto = str(corr[k]).strip()
                        lu_memoria_aggiungi(d, sez, {"campo": k, "letto": b, **({"giusto": giusto} if giusto else {"rifiutato": True}),
                                                     "tipo": x.get("tipo") or pr.get("tipo") or "", "ente": _lu_chi_emette(x), "il": ora})
                        b = str(corr[k]).strip()
                        if not b:
                            continue
                    if k not in x and isinstance(x.get("campi"), dict) and sez == "animali" and k not in ("tipo", "data", "scadenza"):
                        x["campi"][k] = b
                    else:
                        x[k] = b
                x["lettura_lu"] = {k: v for k, v in pr.items() if k != "cambi"} | {"il": ora, "applicata": True}
            else:
                x["lettura_lu"] = {k: v for k, v in pr.items() if k != "cambi"} | {"il": ora, "rifiutata": True}
                tp = (pr.get("cambi") or {}).get("tipo")
                if tp and x["id"] in (correzioni.get("_rifiuta_tipo") or set()):
                    lu_memoria_aggiungi(d, sez, {"campo": "tipo", "letto": tp[1], "rifiutato": True, "tipo": x.get("tipo") or "", "ente": _lu_chi_emette(x), "il": ora})
            x.pop("proposta_lu", None)
        for x, dest in da_spostare:
            _lu_sposta(d, sez, x, dest)
    salva(_m, f"{LU_SEZIONI[sez]['nome']}: proposte dell'IA confermate")


def _lu_nuovi_in_automatico(sez, d, tutti_docs):
    """I documenti NUOVI (non visti l'ultima volta) si leggono da soli in sottofondo: l'IA propone di chi sono e dove vanno (si conferma con ✅ Applica)."""
    ids = [x["id"] for x in tutti_docs]
    visti = (d.get("lu_visti") or {}).get(sez)
    if visti is not None and set(ids) <= set(visti):
        return False
    nuovi = [x["id"] for x in tutti_docs if visti is not None and x["id"] not in visti and not _lu_doc_ok(x)]
    try:
        salva(lambda dd, ids=ids: dd.setdefault("lu_visti", {}).__setitem__(sez, ids), "Documenti visti")
    except Exception:
        return False
    if not nuovi or not lu_attivo() or ((d.get("impostazioni") or {}).get("lu_auto") is False):
        return False
    _lu_avvia(sez, d, False, solo=set(nuovi))
    return True


# ---------------------------------------------------------------------------------------------------------------------
# 9. RIASSUNTO E RICERCA IN TUTTI I DOCUMENTI (anche dentro: riassunto e parole chiave dell'IA, dati letti)
# ---------------------------------------------------------------------------------------------------------------------
LU_NOMI_SEZ = {"documenti": "🪪 I miei documenti", "casa": "🏠 Casa", "lavoro": "💼 Lavoro", "auto": "🚗 Auto", "animali": "🐾 Animali", "salute": "🩺 Salute"}


def _lu_testo_doc(x):
    pezzi = []

    def _raccogli(v, prof=0):
        if prof > 4:
            return
        if isinstance(v, str):
            if len(v) < 600 and not v.startswith(("data:", "http", "vmimg:")):
                pezzi.append(v)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            pezzi.append(str(v))
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 not in ("file", "files", "allegati", "conferma", "dest", "fonti", "id", "sha", "sha256"):
                    _raccogli(v2, prof + 1)
        elif isinstance(v, list):
            for v2 in v[:30]:
                _raccogli(v2, prof + 1)
    _raccogli(x)
    return " ".join(pezzi)


def _lu_riassunto_di(x):
    for k in ("lettura_lu", "proposta_lu", "lettura_ia", "proposta_ia"):
        r = (x.get(k) or {}) if isinstance(x.get(k), dict) else {}
        if r.get("riassunto"):
            return str(r["riassunto"])
        ia = r.get("ia") if isinstance(r.get("ia"), dict) else {}
        if ia.get("riassunto"):
            return str(ia["riassunto"])
    return str(x.get("riassunto") or x.get("conclusioni") or "")


def lu_cerca(d, domanda, massimo=40):
    """[(sezione, documento, riassunto, punteggio)]: tutte le parole cercate devono esserci (senza accenti, maiuscole/minuscole uguali)."""
    parole = [w for w in _lu_parole(domanda) if len(w) >= 2] or [w for w in _lu_re.findall(r"\d+", str(domanda or ""))]
    num = _lu_re.findall(r"\d{2,}", str(domanda or ""))
    if not parole and not num:
        return []
    out = []
    fonti = [(s_, x) for s_ in ("documenti", "casa", "lavoro", "auto", "animali") for x in LU_SEZIONI[s_]["docs"](d) if isinstance(x, dict)]
    for p in ((d.get("farmacia") or {}).get("profili") or []):
        for x in p.get("docsan") or []:
            if isinstance(x, dict):
                fonti.append(("salute", dict(x, _persona=p.get("nome", ""))))
    for s_, x in fonti:
        testo = _lu_testo_doc(x)
        t_parole = _lu_parole(testo)
        t_norm = " ".join(sorted(t_parole))
        ok = all(any(w == tw or (len(w) >= 4 and tw.startswith(w)) for tw in t_parole) for w in parole) and all(n in testo.replace(" ", "") for n in num)
        if not ok:
            continue
        ri = _lu_riassunto_di(x)
        punti = sum(3 for w in parole if w in _lu_parole(_lu_titolo(x) if s_ != "salute" else str(x.get("titolo") or x.get("tipo") or ""))) + len(parole) + (1 if ri else 0)
        out.append((s_, x, ri, punti, len(t_norm)))
    out.sort(key=lambda r: (-r[3], -len(r[2])))
    return [(a, b, c, e) for a, b, c, e, _f in out[:massimo]]


def lu_ricerca_ui(chiave):
    """🔎 Cerca in tutti i documenti (anche dentro): risultato con sezione, titolo, riassunto e il file da vedere."""
    with st.expander("🔎 Cerca in tutti i documenti (anche dentro)"):
        q = st.text_input("Cosa cerchi?", key=f"lu_q_{chiave}", placeholder="es. enel luglio, revisione, vaccino gatto, condominio 2025")
        st.caption("Cerco in **tutte le sezioni**: titoli, tipi, numeri, chi l'ha emesso e anche nel **riassunto** e nelle **parole chiave** scritte dall'IA quando ha letto il documento.")
        if not q.strip():
            return
        try:
            d = carica_dati(crea_archivio(), st.session_state.get("percorso") or percorso_mio())
        except Exception:
            return
        ris = lu_cerca(d, q)
        if not ris:
            st.info("Non ho trovato niente. Prova con meno parole o con una parola diversa. (I documenti non ancora letti dall'IA si trovano solo per titolo e dati.)")
            return
        st.caption(f"Trovati: {len(ris)}")
        for i, (s_, x, ri, _p) in enumerate(ris):
            titolo = (str(x.get("titolo") or x.get("tipo") or "Documento") + (f" · {x['_persona']}" if x.get("_persona") else "")) if s_ == "salute" else _lu_titolo(x)
            st.markdown(f"**{LU_NOMI_SEZ.get(s_, s_)} › {_lu_html.escape(titolo)}**" + (f"<br><span style='font-size:.88rem;opacity:.9'>📝 {_lu_html.escape(ri)}</span>" if ri else ""),
                        unsafe_allow_html=True)
            if st.toggle("👁️ Vedi il file", key=f"lu_qv_{chiave}_{i}"):
                try:
                    files = _lu_file_fa([x["file"]]) if s_ == "salute" and x.get("file") else LU_SEZIONI[s_]["file"](x)
                except Exception:
                    files = []
                if not files:
                    st.caption("Nessun file collegato.")
                for j, (nome, mime, dati) in enumerate(files[:3]):
                    if str(mime).startswith("image/"):
                        st.image(dati, caption=nome, width="stretch")
                    st.download_button("⬇️ " + str(nome)[:40], dati, file_name=nome or "documento", mime=mime or "application/octet-stream", key=f"lu_qd_{chiave}_{i}_{j}", width="stretch")


def _lu_segnalati_ui(sez, tutti_docs):
    """📌 Documenti che l'IA pensa siano nella sezione sbagliata (Auto con più veicoli, Animali, Lavoro…): li segnala, si sistemano a mano."""
    seg = [x for x in tutti_docs if ((x.get("lettura_lu") or {}).get("dest") or {}).get("segnala") and not (x.get("lettura_lu") or {}).get("segnala_ok")]
    if not seg:
        return
    with st.container(border=True, key=f"lu_seg_{sez}"):
        st.markdown(f"**📌 Forse nella sezione sbagliata: {len(seg)}**")
        st.caption("L'IA pensa che questi documenti stiano meglio in un'altra sezione. Aprili da lì e caricali di nuovo (oppure tocca «Va bene qui»).")
        for x in seg[:15]:
            dove = x["lettura_lu"]["dest"]["segnala"]
            c1, c2 = st.columns([4, 2], gap="small")
            c1.markdown(f"📄 {_lu_html.escape(_lu_titolo(x))} → **{LU_SEZ_NOMI.get(dove, dove)}**")
            if c2.button("Va bene qui", key=f"lu_segok_{sez}_{x['id']}", width="stretch"):
                def _m(d, i=x["id"]):
                    for y in LU_SEZIONI[sez]["docs"](d):
                        if isinstance(y, dict) and y.get("id") == i and isinstance(y.get("lettura_lu"), dict):
                            y["lettura_lu"]["segnala_ok"] = True
                salva(_m, f"{LU_SEZIONI[sez]['nome']}: documento lasciato dov'è")
                st.rerun()


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
    lav = _LU_LAVORI.get((_lu_chi(), sez))
    corre = bool(lav and lav["stato"] == "corre")
    if not corre and _lu_nuovi_in_automatico(sez, d, tutti_docs):         # documento appena caricato: l'IA lo legge da sola e propone dove va
        lav = _LU_LAVORI.get((_lu_chi(), sez))
        corre = bool(lav and lav["stato"] == "corre")
    pend = [x for x in tutti_docs if x.get("proposta_lu")]
    if corre or pend:
        with st.container(border=True, key=f"lu_vista_{sez}"):
            st.markdown("<div style='font-weight:700'>🤖 Rileggi e ricataloga con l'IA</div>", unsafe_allow_html=True)
            if corre:
                _lu_vivo(sez)
            if pend:
                st.markdown(f"<div style='font-weight:700;margin:6px 0'>🟡 Proposte da confermare: {len(pend)}</div>", unsafe_allow_html=True)
                scelti, correzioni, rifiuta_tipo = [], {}, set()
                for x in pend:
                    pr = x["proposta_lu"]
                    st.markdown(f"**📄 {_lu_html.escape(_lu_titolo(x))}**")
                    for k, (a, b) in (pr.get("cambi") or {}).items():
                        st.markdown(f"<div style='font-size:.88rem;margin-left:8px'>{_LU_ETICH_DEST.get(k) or LU_SEZIONI[sez]['campi'].get(k, k)}: <s>{_lu_html.escape(str(a or '—'))}</s> → <b>{_lu_html.escape(str(b))}</b></div>",
                                    unsafe_allow_html=True)
                    avvisi = [f"🟠 {LU_SEZIONI[sez]['campi'].get(k, k)}: {m}" for k, m in (pr.get("problemi") or {}).items()] + [f"⚠️ {x_}" for x_ in (pr.get("dubbi") or [])[:2]]
                    if (pr.get("chi") or {}).get("intestatario"):
                        avvisi.insert(0, "👤 Intestato a: " + str(pr["chi"]["intestatario"])[:60] + ("" if (pr.get("dest") or {}).get("persona") else " (non so chi è: scrivilo in «👥 Di chi sono i documenti»)"))
                    if avvisi:
                        st.caption(" · ".join(avvisi))
                    dati_c = [(k, b) for k, (a, b) in (pr.get("cambi") or {}).items() if k in LU_SEZIONI[sez]["campi"]]
                    if dati_c:
                        with st.popover("✏️ Correggi prima di applicare (l'IA impara)", width="stretch"):
                            st.caption("Scrivi il valore giusto: lo applico e **me lo ricordo** per le prossime letture. Lascia vuoto per non cambiare quel dato.")
                            cor = {}
                            for k, b in dati_c:
                                v = st.text_input(LU_SEZIONI[sez]["campi"].get(k, k), value=str(b), key=f"lu_cor_{sez}_{x['id']}_{k}")
                                if v.strip() != str(b):
                                    cor[k] = v.strip()
                            if "tipo" in dict(dati_c):
                                if st.checkbox("Il tipo proposto è sbagliato: non propormelo più per documenti così", key=f"lu_rt_{sez}_{x['id']}"):
                                    rifiuta_tipo.add(x["id"])
                            if cor:
                                correzioni[x["id"]] = cor
                    if st.checkbox("Applica a questo documento", value=True, key=f"lu_sc_{sez}_{x['id']}"):
                        scelti.append(x["id"])
                c1, c2 = st.columns(2, gap="small")
                ids = [x["id"] for x in pend]
                if c1.button(f"✅ Applica ({len(scelti)})", key=f"lu_app_{sez}", type="primary", width="stretch", disabled=not scelti):
                    for i_ in rifiuta_tipo:                                  # tipo rifiutato: quel dato non si applica e si impara
                        correzioni.setdefault(i_, {})["tipo"] = ""
                    _lu_salva_conferma(sez, scelti, ids, correzioni | ({"_rifiuta_tipo": rifiuta_tipo} if rifiuta_tipo else {}))
                    st.toast(f"Aggiornati {len(scelti)} documenti" + (" · ho imparato le tue correzioni" if correzioni or rifiuta_tipo else ""))
                    st.rerun()
                if c2.button("✖ Non applicare", key=f"lu_no_{sez}", width="stretch"):
                    _lu_salva_conferma(sez, [], ids, {"_rifiuta_tipo": rifiuta_tipo} if rifiuta_tipo else None)
                    st.rerun()
    _lu_segnalati_ui(sez, tutti_docs)
    lu_ricerca_ui(sez)
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
        if sez in ("documenti", "casa"):
            lu_ui_persone()
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
