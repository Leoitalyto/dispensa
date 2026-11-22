# =====================================================================================================================
# PATENTE SEMPRE IN DUE POSTI — richiesta del 22 novembre 2026: «in Auto la patente deve inserirsi in automatico se si trova già
# in Documenti, all'inverso deve trovarsi anche in Documenti se inserita in Auto».
#  - I miei documenti (farmacia.documenti, tipo «Patente di guida»)  ⇄  Auto → 👤 Patente e multe (auto.conducente.patenti)
#  - collegamento: doc["auto_pat_id"] ⇄ pat["doc_id"]; campi in comune: numero, scadenza, CQC (doc «scadenza_cqc» = auto «cqc»), di chi è.
#  - chi cambia vince: pat["ps_sinc"] ricorda gli ultimi valori allineati; se cambiano tutti e due, vince I miei documenti.
#  - Restano solo da una parte: rilascio, ente e foto (Documenti); categorie, visita medica, punti, note (Auto).
#  - Eliminare da una parte NON cancella l'altra (foto e punti non si perdono): la copia rimasta non viene più ricreata.
#  - Niente avvisi doppi: per le patenti collegate, scadenza e CQC le avvisa I miei documenti; l'Auto avvisa solo la visita medica.
# =====================================================================================================================
import uuid as _ps_uuid

_PS_TIPO = "Patente di guida"
_PS_CAMPI = (("numero", "numero"), ("scadenza", "scadenza"), ("scadenza_cqc", "cqc"))      # (campo Documenti, campo Auto)


def _ps_parole(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return {w for w in "".join(c if c.isalnum() else " " for c in t).split() if len(w) > 1}


def _ps_profilo_di(f, nome):
    """Il profilo della Salute che corrisponde a «Di chi è la patente» (nome scritto in Auto); di base il principale."""
    profili = f.get("profili") or [{"id": "p0", "nome": ""}]
    w = _ps_parole(nome)
    if w:
        for p in profili:
            pw = _ps_parole(p.get("nome")) | _ps_parole(p.get("nome_doc"))
            if w <= pw or pw and pw <= w:
                return p["id"]
        cand = [p["id"] for p in profili if w & _ps_parole(p.get("nome"))]          # basta il nome di battesimo, se corrisponde a una sola persona
        if len(cand) == 1:
            return cand[0]
    return profili[0]["id"]


def _ps_nome_di(f, pid):
    p = next((p for p in (f.get("profili") or []) if p.get("id") == pid), None)
    return (p or {}).get("nome") or ""


def _ps_norm(v):
    return str(v or "").replace(" ", "").upper()


def patente_sincronizza(d):
    """Allinea le patenti fra I miei documenti e Auto. Ritorna True se ha cambiato qualcosa."""
    f = d.setdefault("farmacia", {})
    docs = f.setdefault("documenti", [])
    a = d.setdefault("auto", {})
    a.setdefault("veicoli", [])
    cond = a.setdefault("conducente", {"id": "cond"})
    pats = cond.setdefault("patenti", [])
    cond.setdefault("verbali", [])
    cambiato = False
    doc_ids = {x["id"]: x for x in docs if x.get("id") and x.get("tipo") == _PS_TIPO}
    pat_ids = {p["id"]: p for p in pats if isinstance(p, dict) and p.get("id")}

    # 1) collegamenti rotti (una delle due è stata eliminata): la copia rimasta resta, scollegata e da non ricreare
    for x in doc_ids.values():
        if x.get("auto_pat_id") and x["auto_pat_id"] not in pat_ids:
            x.pop("auto_pat_id"); x["ps_no_auto"] = True; cambiato = True
    for p in pat_ids.values():
        if p.get("doc_id") and p["doc_id"] not in doc_ids:
            p.pop("doc_id"); p.pop("ps_sinc", None); p["ps_no_doc"] = True; cambiato = True

    # 2) patenti in Documenti senza la gemella in Auto
    for x in doc_ids.values():
        if x.get("auto_pat_id") or x.get("ps_no_auto"):
            continue
        gemella = next((p for p in pat_ids.values() if not p.get("doc_id") and x.get("numero") and _ps_norm(p.get("numero")) == _ps_norm(x.get("numero"))), None)
        if gemella is None:
            gemella = next((p for p in pat_ids.values() if not p.get("doc_id") and not p.get("numero")
                            and _ps_profilo_di(f, p.get("nome")) == x.get("profilo", "p0")), None)
        if gemella is None:
            gemella = {"id": _ps_uuid.uuid4().hex[:10], "nome": _ps_nome_di(f, x.get("profilo", "p0")), "categorie": "", "files": [],
                       "note": "Inserita da «I miei documenti»"}
            pats.append(gemella); pat_ids[gemella["id"]] = gemella
            for kd, ka in _PS_CAMPI:
                gemella[ka] = x.get(kd) or ""
        else:                                                       # c'era già in Auto: si completa a vicenda, i dati di Documenti valgono di più
            for kd, ka in _PS_CAMPI:
                if x.get(kd):
                    gemella[ka] = x[kd]
                elif gemella.get(ka):
                    x[kd] = gemella[ka]
        gemella["doc_id"] = x["id"]; x["auto_pat_id"] = gemella["id"]
        gemella["ps_sinc"] = {ka: gemella.get(ka) or "" for _kd, ka in _PS_CAMPI}
        cambiato = True

    # 3) patenti in Auto senza la gemella in Documenti
    for p in list(pat_ids.values()):
        if p.get("doc_id") or p.get("ps_no_doc"):
            continue
        prof = _ps_profilo_di(f, p.get("nome"))
        x = {"id": _ps_uuid.uuid4().hex[:10], "profilo": prof, "tipo": _PS_TIPO, "numero": p.get("numero") or "", "ente": "", "rilascio": None,
             "senza_scadenza": False, "scadenza": p.get("scadenza") or None, "scadenza_cqc": p.get("cqc") or None,
             "note": "Inserita da «Auto → Patente e multe»" + (f" · categorie {p['categorie']}" if p.get("categorie") else ""), "allegati": [], "auto_pat_id": p["id"]}
        docs.append(x); doc_ids[x["id"]] = x
        p["doc_id"] = x["id"]
        p["ps_sinc"] = {ka: p.get(ka) or "" for _kd, ka in _PS_CAMPI}
        cambiato = True

    # 4) coppie collegate: chi è cambiato dall'ultimo allineamento passa all'altra (se cambiano tutte e due, vince Documenti)
    for p in pat_ids.values():
        x = doc_ids.get(p.get("doc_id"))
        if not x:
            continue
        sinc = p.setdefault("ps_sinc", {})
        for kd, ka in _PS_CAMPI:
            vd, va, vs = x.get(kd) or "", p.get(ka) or "", sinc.get(ka, None)
            if vd == va:
                if vs != va:
                    sinc[ka] = va; cambiato = True
                continue
            if vs is not None and vd == vs:                         # cambiato solo in Auto
                x[kd] = va or None
            else:                                                   # cambiato in Documenti (o tutti e due)
                p[ka] = vd
            sinc[ka] = x.get(kd) or ""
            cambiato = True
        nome = _ps_nome_di(f, x.get("profilo", "p0"))
        if nome and not p.get("nome"):
            p["nome"] = nome; cambiato = True
    return cambiato


def ps_collegata(pt):
    """Una patente di Auto collegata a I miei documenti: scadenza e CQC le avvisa Documenti (niente doppioni)."""
    return isinstance(pt, dict) and bool(pt.get("doc_id"))


def _ps_controlla_e_salva():
    try:
        import copy
        d = carica_dati(crea_archivio(), st.session_state["percorso"])
        prova = copy.deepcopy({"farmacia": d.get("farmacia") or {}, "auto": d.get("auto") or {}})
        if patente_sincronizza(prova):
            salva(patente_sincronizza, "Patente allineata fra I miei documenti e Auto")
            if "doc_cqc_sincronizza" in globals():
                d2 = carica_dati(crea_archivio(), st.session_state["percorso"])
                p2 = copy.deepcopy(d2.get("farmacia") or {})
                if doc_cqc_sincronizza(p2):
                    salva(lambda dd: doc_cqc_sincronizza(dd.setdefault("farmacia", {})), "I miei documenti: scheda CQC dalla patente")
    except Exception:
        pass


for _ps_fn in ("schermata_documenti", "schermata_auto"):
    if _ps_fn in globals() and f"_ps_prima_{_ps_fn}" not in globals():
        globals()[f"_ps_prima_{_ps_fn}"] = globals()[_ps_fn]

        def _ps_avvolta(*a, _orig=globals()[_ps_fn], **k):
            _ps_controlla_e_salva()
            return _orig(*a, **k)
        globals()[_ps_fn] = _ps_avvolta

# ---- niente avvisi doppi in Auto (Home e pagina Auto): per le collegate solo la visita medica
if "au_scadenze_avviso" in globals() and "_ps_avv_prima" not in globals():
    _ps_avv_prima = au_scadenze_avviso

    def au_scadenze_avviso(a, *ar, **k):                                 # noqa: F811
        import copy
        a2 = copy.deepcopy(a or {})
        for pt in ((a2.get("conducente") or {}).get("patenti") or []):
            if ps_collegata(pt):
                pt.pop("scadenza", None); pt.pop("cqc", None)
        return _ps_avv_prima(a2, *ar, **k)

# ---- guida
try:
    if "_GUIDE" in globals() and "_ID_GUIDA" in globals():
        for _sez in ("documenti", "auto"):
            _ids = _ID_GUIDA.setdefault(_sez, [])
            if "x_patente_2posti" not in _ids:
                _ids.append("x_patente_2posti")
                _GUIDE.setdefault(_sez, []).append((
                    "🔗 La patente in I miei documenti e in Auto",
                    "La patente è **la stessa** in **📁 I miei documenti** e in **🚗 Auto → 👤 Patente e multe**: se la inserisci da una parte, compare da sola anche nell'altra.\n"
                    "Numero, scadenza e CQC restano **uguali**: se li cambi da una parte, cambiano anche dall'altra.\n"
                    "Solo in Documenti: foto, ente e data di rilascio. Solo in Auto: categorie, visita medica, saldo punti e multe.\n"
                    "Gli avvisi non arrivano due volte: scadenza e CQC li manda I miei documenti, la visita medica l'Auto.\n"
                    "Se la elimini da una parte, l'altra **resta** (così non perdi foto e punti): eliminala anche lì se non ti serve più.",
                    "patente auto documenti collegata stessa doppia sincronizzata cqc punti visita medica"))
except Exception:
    pass
