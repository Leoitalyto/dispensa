# =====================================================================================================================
# CQC (Carta di qualificazione del conducente) nei «I miei documenti» — richiesta del 22 novembre 2026:
# «non appare la scadenza della patente intesa come CQC, che vedo bene nell'app iPatente».
# Sulla patente la CQC è il codice 95 sul retro (colonna 12) con la SUA data di scadenza, diversa da quella della patente.
#  - la patente ha il campo «scadenza_cqc» (modulo, lettura automatica OCR + IA, lettore unico);
#  - da quel campo nasce da sola una scheda «CQC – Carta di qualificazione del conducente» collegata (cqc_della_patente):
#    così la CQC ha i suoi avvisi (6 e 3 mesi), entra nei contatori, nello Scadenziario, nei promemoria su Telegram/email.
# =====================================================================================================================
import uuid as _dq_uuid

_DQ_PATENTE = "Patente di guida"


def doc_cqc_sincronizza(f):
    """Allinea le schede CQC collegate alle patenti con «scadenza_cqc». Ritorna True se ha cambiato qualcosa."""
    docs = f.setdefault("documenti", [])
    tipo_cqc = globals().get("DOC_CQC", "CQC – Carta di qualificazione del conducente")
    cambiato = False
    patenti = {x["id"]: x for x in docs if x.get("id") and x.get("tipo") == _DQ_PATENTE and x.get("scadenza_cqc")}
    collegate = {x.get("cqc_della_patente"): x for x in docs if x.get("cqc_della_patente")}
    for pid_doc, pat in patenti.items():
        num = pat.get("numero") or ""
        voluto = {"profilo": pat.get("profilo", "p0"), "tipo": tipo_cqc, "numero": num, "ente": pat.get("ente") or "",
                  "scadenza": pat["scadenza_cqc"], "senza_scadenza": False,
                  "note": "Codice 95 sul retro della patente" + (f" n. {num}" if num else "")}
        c = collegate.get(pid_doc)
        if c is None:
            manuale = next((x for x in docs if x.get("tipo") == tipo_cqc and not x.get("cqc_della_patente")
                            and x.get("profilo", "p0") == voluto["profilo"] and x.get("scadenza") == voluto["scadenza"]), None)
            if manuale:                                                  # l'aveva già inserita a mano con la stessa data: niente doppione
                continue
            docs.append(dict(voluto, id=_dq_uuid.uuid4().hex[:10], allegati=[], cqc_della_patente=pid_doc))
            cambiato = True
        elif any(c.get(k) != v for k, v in voluto.items()):
            c.update(voluto)
            cambiato = True
    for x in list(docs):                                                 # patente eliminata o CQC tolta: via anche la scheda collegata
        if x.get("cqc_della_patente") and x["cqc_della_patente"] not in patenti:
            docs.remove(x)
            cambiato = True
    return cambiato


def _dq_controlla_e_salva():
    try:
        f = _fa_dati()
        prova = {"documenti": [dict(x) for x in (f.get("documenti") or [])]}
        if doc_cqc_sincronizza(prova):
            _fa_salva(doc_cqc_sincronizza, "I miei documenti: scheda CQC dalla patente")
    except Exception:
        pass


if "schermata_documenti" in globals() and "_dq_schermata_prima" not in globals():
    _dq_schermata_prima = schermata_documenti

    def schermata_documenti(*a, **k):                                    # noqa: F811
        _dq_controlla_e_salva()
        return _dq_schermata_prima(*a, **k)

# ---- il lettore unico (IA): la patente legge anche la CQC; la CQC ha la sua scheda
try:
    if "LU_SCHEDE" in globals():
        _c, _r = LU_SCHEDE.get(_DQ_PATENTE, ({}, ""))
        LU_SCHEDE[_DQ_PATENTE] = (dict(_c, scadenza_cqc="scadenza della CQC AAAA-MM-GG: sul RETRO, colonna 12, codice 95 con la data tra parentesi (es. 95(22.07.31) = 2031-07-22); vuoto se non c'è"),
                                  _r + " Sul RETRO, colonna 12, il codice 95 con una data tra parentesi è la scadenza della CQC (carta di qualificazione del conducente): mettila in scadenza_cqc, NON in scadenza.")
        LU_SCHEDE[globals().get("DOC_CQC", "CQC – Carta di qualificazione del conducente")] = (
            dict(_LU_ID), "CQC (carta di qualificazione del conducente, persone o merci): se è una patente, la scadenza della CQC è il codice 95 sul retro con la data tra parentesi.")
    if "LU_SEZIONI" in globals():
        LU_SEZIONI["documenti"]["campi"].setdefault("scadenza_cqc", "Scadenza CQC")
except Exception:
    pass

# ---- la guida
try:
    if "_GUIDE" in globals() and "_ID_GUIDA" in globals():
        _ids = _ID_GUIDA.setdefault("documenti", [])
        if "x_cqc" not in _ids:
            _ids.append("x_cqc")
            _GUIDE.setdefault("documenti", []).append((
                "🚛 La CQC (codice 95 della patente)",
                "La **CQC** (carta di qualificazione del conducente) ha una scadenza **diversa** da quella della patente. Sulla patente la trovi sul **retro**, "
                "colonna 12: il **codice 95** con la data tra parentesi, per esempio **95(22.07.31)** = 22/07/2031.\n"
                "Apri la tua **Patente di guida** → **✏️ Modifica** → campo **🚛 Solo per la patente: scadenza della CQC** (se fotografi il retro, l'app la legge da sola) → **💾 Salva**.\n"
                "L'app crea da sola la scheda **«CQC – Carta di qualificazione del conducente»** con i suoi avvisi (6 e 3 mesi prima), che compare anche nello **🗓️ Scadenziario**. "
                "Per cambiarla, modifica la patente. Se hai una CQC su tessera a parte, aggiungila come documento «CQC».",
                "cqc carta qualificazione conducente codice 95 patente professionale camion autobus scadenza retro"))
except Exception:
    pass
