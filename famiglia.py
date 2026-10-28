# -*- coding: utf-8 -*-
"""CONTROLLO FAMIGLIA (per il capo famiglia = amministratore).
Mette in un unico posto, in sola lettura, la Farmacia di tutte le persone della famiglia: i profili del capo famiglia e la Farmacia
delle persone che il capo famiglia ha inserito nella famiglia (interruttore «Parte della famiglia» nella scheda Utenti).
Per ogni persona: cosa c'è da fare oggi, medicinali e scadenze, terapie e prescrizioni, visite ed esami, vaccini, documenti, scheda sanitaria.
Tutto si esporta: report da stampare (o salvare in PDF), Excel e file JSON. Foto e PDF caricati non sono inclusi.
TRASPARENZA: chi è inserito nella famiglia lo vede scritto nella sua Farmacia. Chi non è inserito non è visibile.
Caricato da app_dispensa.py dopo farmacia.py; il pulsante si aggancia in farmacia.py."""
import html
import io
import json
import re
import zipfile
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------------------------------------------------
# Chi fa parte della famiglia
# ---------------------------------------------------------------------------------------------------------------------
def fam_e_capo():
    try:
        return bool(st.session_state["sess"].get("admin"))
    except Exception:
        return False


def _fam_profili(f, nome_default):
    return f.get("profili") or [{"id": "p0", "nome": nome_default}]


def fam_persone():
    """Elenco delle persone: i profili del capo famiglia e quelli delle persone inserite nella famiglia.
    Ogni persona è un dizionario: nome, origine (di chi è l'account), d (tutti i dati dell'account), f (la Farmacia), pid, p (profilo)."""
    persone = []
    d_capo = carica_dati(crea_archivio(), st.session_state["percorso"])
    f_capo = d_capo.get("farmacia") or {}
    for p in _fam_profili(f_capo, st.session_state["sess"]["nome"]):
        persone.append({"chiave": "io:" + p["id"], "nome": p["nome"], "origine": "", "d": d_capo, "f": f_capo, "pid": p["id"], "p": p})
    try:
        utenti = leggi_utenti()
    except Exception:
        utenti = []
    for u in utenti:
        if not u.get("famiglia") or not u.get("attivo", True):
            continue
        try:
            d_u = carica_dati(crea_archivio(), f"dispense/{u['id']}.json")
        except Exception:
            continue
        f_u = d_u.get("farmacia") or {}
        for p in _fam_profili(f_u, u["nome"]):
            nome = p["nome"] if p["nome"] != u["nome"] else u["nome"]
            persone.append({"chiave": f"{u['id']}:{p['id']}", "nome": nome, "origine": u["nome"], "d": d_u, "f": f_u, "pid": p["id"], "p": p})
    return persone


def _fam_etichetta(p):
    return p["nome"] + (f" (account di {p['origine']})" if p["origine"] and p["origine"] != p["nome"] else "")


def _fam_di(f, chiave, pid):
    return [x for x in f.get(chiave, []) if x.get("profilo", "p0") == pid]


# ---------------------------------------------------------------------------------------------------------------------
# Riepilogo di una persona
# ---------------------------------------------------------------------------------------------------------------------
def fam_riepilogo(p, oggi_, ora_adesso):
    f, pid = p["f"], p["pid"]
    r = {"allerte": [], "dosi_oggi": [], "meds": _fam_di(f, "medicinali", pid)}
    # medicinali
    scaduti = [m for m in r["meds"] if m.get("scadenza") and stato_scadenza(m["scadenza"], oggi_)[0] == "scaduto"]
    in_scad = [m for m in r["meds"] if m.get("scadenza") and stato_scadenza(m["scadenza"], oggi_)[0] in ("arancione", "rosso")]
    r["scaduti"], r["in_scadenza"] = scaduti, in_scad
    if scaduti:
        r["allerte"].append(f"🔴 {len(scaduti)} medicinale/i scaduto/i: " + ", ".join(m.get("nome", "") for m in scaduti[:4]))
    if in_scad:
        r["allerte"].append(f"🟠 {len(in_scad)} medicinale/i in scadenza (entro 2 mesi): " + ", ".join(m.get("nome", "") for m in in_scad[:4]))
    # terapie e dosi di oggi
    r["terapie"] = _fam_di(f, "terapie", pid)
    r["terapie_attive"] = [t_ for t_ in r["terapie"] if t_.get("stato", "attiva") == "attiva"]
    reg = f.get("registro") or {}
    for ora, t_ in _fa_dosi_giorno(f, pid, oggi_):
        presa = _fa_chiave(t_, oggi_, ora) in reg
        momento = datetime.fromisoformat(f"{oggi_.isoformat()}T{ora}")
        stato = "presa" if presa else ("da_prendere" if momento <= ora_adesso else "piu_tardi")
        r["dosi_oggi"].append({"ora": ora, "medicinale": _fa_nome_med(f, t_.get("med"), t_.get("nome_med", "")),
                               "quantita": t_.get("quantita", ""), "stato": stato})
    ritardo = [x for x in r["dosi_oggi"] if x["stato"] == "da_prendere"]
    if ritardo:
        r["allerte"].append(f"⚠️ {len(ritardo)} assunzione/i di oggi non ancora registrata/e: " + ", ".join(f"{x['ora']} {x['medicinale']}" for x in ritardo[:4]))
    # prescrizioni da usare
    pres = _fam_di(f, "prescrizioni", pid)
    r["prescrizioni"] = pres
    pres_urg = [(x, _fa_presc_stato(x, oggi_)) for x in pres if _fa_presc_stato(x, oggi_)[0] in ("scaduta", "urgente")]
    r["presc_urgenti"] = pres_urg
    if pres_urg:
        r["allerte"].append("📝 Prescrizioni da usare, in scadenza o scadute: " + ", ".join(
            f"{x.get('tipo', '')}" + (f" ({x['prescritto'][:30]})" if x.get("prescritto") else "") + f" - {'scaduta' if st_[0] == 'scaduta' else 'scade tra ' + str(st_[1]) + ' g'}"
            for x, st_ in pres_urg[:3]))
    # visite ed esami
    vis = _fam_di(f, "visite", pid)
    prossime = []
    for v in vis:
        for chiave in ("prossimo", "data"):
            dv = _fa_data(v.get(chiave))
            if dv and dv >= oggi_:
                prossime.append((dv, v))
                break
    prossime.sort(key=lambda x: x[0])
    r["visite"], r["prossime"] = vis, prossime
    vicine = [(dv, v) for dv, v in prossime if (dv - oggi_).days <= 14]
    if vicine:
        r["allerte"].append("📅 Prossimi appuntamenti: " + ", ".join(f"{data_it(dv.isoformat())} {v.get('categoria', '')}" for dv, v in vicine[:3]))
    # vaccini
    vac = _fam_di(f, "vaccinazioni", pid)
    richiami = []
    for v in vac:
        dr = _fa_data(v.get("richiamo"))
        if dr and (dr - oggi_).days <= 90:
            richiami.append((dr, v))
    r["vaccini"], r["richiami"] = vac, sorted(richiami, key=lambda x: x[0])
    if richiami:
        r["allerte"].append("💉 Richiami vicini o scaduti: " + ", ".join(f"{v.get('nome', '')} ({data_it(dr.isoformat())})" for dr, v in r["richiami"][:3]))
    # documenti
    docs = _fam_di(f, "documenti", pid)
    r["documenti"] = docs
    in_rinnovo = []
    for x in docs:
        if x.get("senza_scadenza") or not x.get("scadenza"):
            continue
        s_, g_ = _doc_stato(x["scadenza"], oggi_)
        if s_ in ("scaduto", "urgente", "avviso"):
            in_rinnovo.append((s_, g_, x))
    r["doc_rinnovo"] = in_rinnovo
    if in_rinnovo:
        r["allerte"].append("📁 Documenti da rinnovare: " + ", ".join(f"{x.get('tipo', '')} ({data_it(x['scadenza'])})" for _, _, x in in_rinnovo[:3]))
    r["allergie"] = (f.get("allergie") or {}).get(pid, [])
    return r


# ---------------------------------------------------------------------------------------------------------------------
# Righe delle tabelle (le stesse per lo schermo, l'HTML da stampare e l'Excel)
# ---------------------------------------------------------------------------------------------------------------------
def _fam_d(iso):
    return data_it(iso) if iso else ""


def _fam_righe_medicinali(p):
    f = p["f"]
    return [[m.get("nome", ""), m.get("marca", ""), m.get("principio", ""), m.get("dosaggio", ""), m.get("forma", ""),
             f"{fmt_num(float(m.get('quantita') or 0))} {m.get('unita', '')}".strip(), _fam_d(m.get("scadenza")), _fam_d(m.get("acquisto")),
             m.get("note", "")] for m in sorted(_fam_di(f, "medicinali", p["pid"]), key=lambda m: m.get("scadenza") or "9999")]


FAM_H_MEDICINALI = ["Nome", "Marca", "Principio attivo", "Dosaggio", "Forma", "Quantità", "Scadenza", "Acquisto", "Note"]


def _fam_righe_terapie(p):
    f = p["f"]
    return [[_fa_nome_med(f, t_.get("med"), t_.get("nome_med", "")), t_.get("quantita", ""),
             ", ".join(GIORNI_SETT[g] for g in t_.get("giorni", []) if 0 <= g < len(GIORNI_SETT)), ", ".join(t_.get("orari", [])),
             f"dal {_fam_d(t_.get('inizio'))}" + (f" al {_fam_d(t_['fine'])}" if t_.get("fine") else ""),
             STATI_TER.get(t_.get("stato", "attiva"), ""), t_.get("note", "")] for t_ in _fam_di(f, "terapie", p["pid"])]


FAM_H_TERAPIE = ["Medicinale", "Quantità", "Giorni", "Orari", "Periodo", "Stato", "Prescrizione e note"]


def _fam_righe_registro(p):
    reg = [r for r in (p["f"].get("registro") or {}).values() if r.get("p", "p0") == p["pid"]]
    reg.sort(key=lambda r: (r.get("d", ""), r.get("o", "")), reverse=True)
    return [[_fam_d(r.get("d")), r.get("o", ""), r.get("nome", ""), r.get("q", ""), (r.get("quando") or "").replace("T", " ")] for r in reg]


FAM_H_REGISTRO = ["Data", "Ora prevista", "Medicinale", "Quantità", "Registrata il"]


def _fam_righe_visite(p):
    vis = sorted(_fam_di(p["f"], "visite", p["pid"]), key=lambda v: v.get("data", ""), reverse=True)
    return [[_fam_d(v.get("data")) + (f" {v['ora']}" if v.get("ora") else ""), v.get("categoria", ""), v.get("medico", ""), v.get("motivo", ""),
             v.get("controlli", ""), _fam_d(v.get("prossimo")), v.get("note", ""), ", ".join(a["nome"] for a in v.get("allegati", []))] for v in vis]


FAM_H_VISITE = ["Data", "Tipo", "Medico o struttura", "Motivo", "Controlli successivi", "Prossimo appuntamento", "Note", "Documenti allegati"]


def _fam_righe_vaccini(p):
    vac = sorted(_fam_di(p["f"], "vaccinazioni", p["pid"]), key=lambda v: v.get("data", ""), reverse=True)
    return [[v.get("nome", ""), _fam_d(v.get("data")), v.get("dose", ""), _fam_d(v.get("richiamo")), v.get("note", "")] for v in vac]


FAM_H_VACCINI = ["Vaccino", "Data", "Dose o richiamo", "Prossimo richiamo", "Note"]


def _fam_righe_documenti(p):
    docs = sorted(_fam_di(p["f"], "documenti", p["pid"]), key=lambda x: x.get("scadenza") or "9999")
    return [[x.get("tipo", ""), x.get("numero", ""), x.get("ente", ""), _fam_d(x.get("rilascio")),
             "non scade" if x.get("senza_scadenza") else _fam_d(x.get("scadenza")), x.get("note", "")] for x in docs]


FAM_H_DOCUMENTI = ["Tipo", "Numero", "Rilasciato da", "Rilascio", "Scadenza", "Note"]


def _fam_anagrafica(p):
    pr = p["p"]
    dott = pr.get("dottore") or {}
    return {"Persona": p["nome"], "Account": p["origine"] or "Capo famiglia", "Gruppo sanguigno": pr.get("gruppo") or "non indicato",
            "Allergie dichiarate": ", ".join((p["f"].get("allergie") or {}).get(p["pid"], [])) or "nessuna",
            "Medico": dott.get("nome", ""), "Telefono medico": dott.get("telefono", ""), "Email medico": dott.get("email", "")}


def _fam_righe_prescrizioni(p):
    pres = sorted(_fam_di(p["f"], "prescrizioni", p["pid"]), key=lambda x: x.get("data", ""), reverse=True)
    return [[_fam_d(x.get("data")), x.get("tipo", ""), x.get("medico", ""), x.get("prescritto", ""), x.get("codice", ""), _fam_d(x.get("valida_fino")),
             x.get("stato", ""), x.get("note", ""), ", ".join(a["nome"] for a in x.get("allegati", []))] for x in pres]


FAM_H_PRESCRIZIONI = ["Data", "Tipo", "Medico", "Cosa è prescritto", "Codice", "Valida fino al", "Stato", "Note", "Documenti allegati"]

FAM_SEZIONI = [("Medicinali", FAM_H_MEDICINALI, _fam_righe_medicinali), ("Terapie", FAM_H_TERAPIE, _fam_righe_terapie),
               ("Prescrizioni (ricette)", FAM_H_PRESCRIZIONI, _fam_righe_prescrizioni),
           ("Assunzioni registrate", FAM_H_REGISTRO, _fam_righe_registro), ("Visite, esami e referti", FAM_H_VISITE, _fam_righe_visite),
           ("Vaccinazioni", FAM_H_VACCINI, _fam_righe_vaccini), ("Documenti", FAM_H_DOCUMENTI, _fam_righe_documenti)]


# ---------------------------------------------------------------------------------------------------------------------
# Esportazione: HTML da stampare, Excel, JSON
# ---------------------------------------------------------------------------------------------------------------------
def fam_html(persone, oggi_):
    e = html.escape
    parti = []
    for i, p in enumerate(persone):
        pr, f, pid = p["p"], p["f"], p["pid"]
        dott = pr.get("dottore") or {}
        corpo = [f"<h2 class='persona{' prima' if i == 0 else ''}'>👤 {e(p['nome'])}"
                 + (f" <small>(account di {e(p['origine'])})</small>" if p["origine"] and p["origine"] != p["nome"] else "") + "</h2>",
                 f"<p>Gruppo sanguigno: <b>{e(pr.get('gruppo') or 'non indicato')}</b><br>Allergie e intolleranze dichiarate: "
                 f"<b>{e(', '.join((f.get('allergie') or {}).get(pid, [])) or 'nessuna')}</b></p>"]
        if dott.get("nome") or dott.get("telefono") or dott.get("email"):
            corpo.append(f"<p><b>Il mio {e(str(dott.get('tipo', 'Dottore')).lower())}:</b> {e(dott.get('nome', ''))}"
                         + (f" · tel. {e(dott['telefono'])}" if dott.get("telefono") else "") + (f" · {e(dott['email'])}" if dott.get("email") else "")
                         + (f" · {e(dott['indirizzo'])}" if dott.get("indirizzo") else "") + "</p>")
        san = pr.get("sanitario") or {}
        for titolo, ch in (("Patologie", "patologie"), ("Interventi subiti", "interventi"), ("Storia clinica di rilievo", "storia"),
                           ("Familiarità", "famiglia"), ("Altre informazioni", "altro")):
            if san.get(ch):
                corpo.append(f"<p><b>{titolo}:</b><br>{e(san[ch]).replace(chr(10), '<br>')}</p>")
        for titolo, intest, fn in FAM_SEZIONI:
            corpo.append(_fa_tabella_html(titolo, intest, fn(p)))
        parti.append("".join(corpo))
    nomi = ", ".join(p["nome"] for p in persone)
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report famiglia - {e(data_it(oggi_.isoformat()))}</title>
<style>@page{{size:A4;margin:12mm}}body{{font-family:Arial,sans-serif;margin:16px;color:#111}}h1{{font-size:1.4rem}}
h2{{font-size:1.2rem;margin-top:28px;border-bottom:2px solid #b71c1c;padding-bottom:3px}}h2 small{{font-weight:400;font-size:.8rem}}
h3{{font-size:1rem;margin:16px 0 4px}}table{{border-collapse:collapse;width:100%;font-size:.78rem}}
th,td{{border:1px solid #999;padding:3px 5px;text-align:left;vertical-align:top}}th{{background:#eee}}
.vuoto{{color:#666;font-size:.85rem;margin:2px 0}}.nota{{font-size:.8rem;color:#444;margin-top:22px}}.box{{background:#f3f3f3;padding:8px 12px;border-radius:8px}}
@media print{{h2.persona{{page-break-before:always;break-before:page}}h2.prima{{page-break-before:auto;break-before:auto}}table{{page-break-inside:auto}}tr{{page-break-inside:avoid}}}}</style></head><body>
<h1>Report famiglia · Farmacia</h1>
<div class="box"><b>{len(persone)} persone</b>: {e(nomi)}<br>Creato il {data_it(oggi_.isoformat())}</div>
{''.join(parti)}
<p class="nota">Documento creato dall'app «La nostra dispensa» con i dati inseriti dalle persone: non è verificato da un medico o da un farmacista.
Le foto e i PDF caricati non sono inclusi. Contiene dati sanitari: conservalo con cura e non condividerlo con chi non deve vederlo.</p></body></html>"""


def _fam_nome_foglio(nome, usati):
    base = "".join(c for c in nome if c not in "[]:*?/\\")[:31] or "Foglio"
    n, k = base, 2
    while n in usati:
        n = f"{base[:28]} {k}"
        k += 1
    usati.add(n)
    return n


def _fam_colonna(i):
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def fam_xlsx(fogli):
    """Un vero file Excel (.xlsx) senza librerie in più. fogli = [(nome, intestazioni, righe)]."""
    usati, nomi = set(), []
    xml_fogli = []
    for nome, intest, righe in fogli:
        nomi.append(_fam_nome_foglio(nome, usati))
        larg = [max(8, min(60, len(str(h)) + 2)) for h in intest]
        for r in righe:
            for i, v in enumerate(r[:len(larg)]):
                larg[i] = max(larg[i], min(60, len(str(v)) + 2))
        celle = lambda riga, stile: "".join(
            f'<c r="{_fam_colonna(i)}{riga[0]}" t="inlineStr"{stile}><is><t xml:space="preserve">{_xml_escape(str(v))}</t></is></c>'
            for i, v in enumerate(riga[1]))
        righe_xml = [f'<row r="1">{celle((1, intest), " s=" + chr(34) + "1" + chr(34))}</row>']
        for n, r in enumerate(righe, start=2):
            righe_xml.append(f'<row r="{n}">{celle((n, r), "")}</row>')
        cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(larg))
        xml_fogli.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                         '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
                         f'<cols>{cols}</cols><sheetData>{"".join(righe_xml)}</sheetData></worksheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(len(nomi))) + "</Types>")
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{_xml_escape(n, {chr(34): "&quot;"})}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, n in enumerate(nomi)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>'
                             for i in range(len(nomi)))
                   + f'<Relationship Id="rId{len(nomi) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
                   '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
                   '<fill><patternFill patternType="solid"><fgColor rgb="FF0F766E"/><bgColor indexed="64"/></patternFill></fill></fills>'
                   '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
                   '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                   '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                   '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
                   '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        for i, x in enumerate(xml_fogli):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", x)
    return buf.getvalue()


def fam_fogli(persone):
    """I fogli dell'Excel: un foglio per argomento, con una colonna «Persona» per distinguere chi è chi."""
    anag = [_fam_anagrafica(p) for p in persone]
    fogli = [("Persone", list(anag[0].keys()) if anag else ["Persona"], [list(a.values()) for a in anag])]
    for titolo, intest, fn in FAM_SEZIONI:
        righe = []
        for p in persone:
            righe += [[p["nome"]] + r for r in fn(p)]
        fogli.append((titolo, ["Persona"] + intest, righe))
    return fogli


def fam_json(persone):
    out = []
    for p in persone:
        out.append({"persona": p["nome"], "account": p["origine"] or "capo famiglia", "anagrafica": _fam_anagrafica(p),
                    "scheda_sanitaria": p["p"].get("sanitario"),
                    **{re.sub(r"[^a-z0-9_]", "", titolo.lower().replace(" ", "_")): [dict(zip(intest, r)) for r in fn(p)] for titolo, intest, fn in FAM_SEZIONI}})
    return json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8")


# ---------------------------------------------------------------------------------------------------------------------
# Schermata
# ---------------------------------------------------------------------------------------------------------------------
def _fam_tabella(intest, righe, vuoto="Niente da mostrare."):
    if not righe:
        st.caption(vuoto)
        return
    st.dataframe(pd.DataFrame(righe, columns=intest), hide_index=True, width="stretch")


def _fam_dettaglio_persona(p, oggi_, ora_adesso):
    r = fam_riepilogo(p, oggi_, ora_adesso)
    anag = _fam_anagrafica(p)
    st.markdown(f"**🩸 Gruppo sanguigno:** {anag['Gruppo sanguigno']} · **Allergie dichiarate:** {anag['Allergie dichiarate']}"
                + (f" · **Medico:** {html.escape(anag['Medico'])}" if anag["Medico"] else "")
                + (f" · 📞 {html.escape(anag['Telefono medico'])}" if anag["Telefono medico"] else ""))
    for a in r["allerte"]:
        st.warning(a)
    if not r["allerte"]:
        st.success("Tutto in ordine: niente di urgente.")
    t_oggi, t_med, t_ter, t_pre, t_vis, t_vac, t_doc, t_san = st.tabs(["⏰ Oggi", "💊 Medicinali", "📅 Terapie", "📝 Prescrizioni", "🩺 Visite ed esami", "💉 Vaccini",
                                                                       "📁 Documenti", "🩻 Scheda sanitaria"])
    with t_oggi:
        icone = {"presa": "✅ presa", "da_prendere": "⚠️ da prendere", "piu_tardi": "⏳ più tardi"}
        _fam_tabella(["Ora", "Medicinale", "Quantità", "Stato"], [[x["ora"], x["medicinale"], x["quantita"], icone[x["stato"]]] for x in r["dosi_oggi"]],
                 "Nessuna assunzione prevista oggi.")
    with t_med:
        _fam_tabella(FAM_H_MEDICINALI, _fam_righe_medicinali(p), "Nessun medicinale inserito.")
    with t_ter:
        _fam_tabella(FAM_H_TERAPIE, _fam_righe_terapie(p), "Nessuna terapia inserita.")
        st.markdown("**Assunzioni registrate (le più recenti)**")
        _fam_tabella(FAM_H_REGISTRO, _fam_righe_registro(p)[:30], "Nessuna assunzione registrata.")
    with t_pre:
        _fam_tabella(FAM_H_PRESCRIZIONI, _fam_righe_prescrizioni(p), "Nessuna prescrizione inserita.")
    with t_vis:
        _fam_tabella(FAM_H_VISITE, _fam_righe_visite(p), "Nessuna visita o esame inserito.")
    with t_vac:
        _fam_tabella(FAM_H_VACCINI, _fam_righe_vaccini(p), "Nessuna vaccinazione inserita.")
    with t_doc:
        _fam_tabella(FAM_H_DOCUMENTI, _fam_righe_documenti(p), "Nessun documento inserito.")
    with t_san:
        san = p["p"].get("sanitario") or {}
        voci = [("Patologie", "patologie"), ("Interventi subiti", "interventi"), ("Storia clinica di rilievo", "storia"),
                ("Familiarità", "famiglia"), ("Altre informazioni", "altro")]
        if not any(san.get(ch) for _, ch in voci):
            st.caption("Scheda sanitaria non compilata.")
        for titolo, ch in voci:
            if san.get(ch):
                st.markdown(f"**{titolo}**")
                st.write(san[ch])


def schermata_famiglia():
    if not fam_e_capo():
        st.error("Questa pagina è riservata al capo famiglia.")
        return
    if st.button("← Torna alla Farmacia", key="fam_indietro"):
        st.session_state.pop("fa_famiglia", None)
        st.rerun()
    st.markdown("<div class='fa-hero'><h1>👨‍👩‍👧 Controllo famiglia</h1><p>Medicinali, terapie, visite e documenti di tutta la famiglia</p></div>",
                unsafe_allow_html=True)
    oggi_ = oggi()
    ora_adesso = adesso()
    persone = fam_persone()
    riepiloghi = {p["chiave"]: fam_riepilogo(p, oggi_, ora_adesso) for p in persone}

    n_persone = len(persone)
    n_scad = sum(len(r["scaduti"]) + len(r["in_scadenza"]) for r in riepiloghi.values())
    n_dosi = sum(sum(1 for x in r["dosi_oggi"] if x["stato"] == "da_prendere") for r in riepiloghi.values())
    n_app = sum(len([1 for dv, _ in r["prossime"] if (dv - oggi_).days <= 30]) for r in riepiloghi.values())
    n_doc = sum(len(r["doc_rinnovo"]) for r in riepiloghi.values())
    st.markdown("<div class='fa-kpi'>"
                f"<div class='fa-k'><span>Persone</span><b>{n_persone}</b></div>"
                f"<div class='fa-k arancione'><span>Medicinali in scadenza</span><b>{n_scad}</b></div>"
                f"<div class='fa-k rosso'><span>Da prendere oggi</span><b>{n_dosi}</b></div>"
                f"<div class='fa-k'><span>Appuntamenti 30 giorni</span><b>{n_app}</b></div>"
                f"<div class='fa-k scaduto'><span>Documenti da rinnovare</span><b>{n_doc}</b></div></div>", unsafe_allow_html=True)
    st.caption("Vedi anche la Farmacia delle persone che hai inserito nella famiglia dalla scheda **Utenti** (interruttore «Parte della famiglia»): "
               "loro lo vedono scritto nella loro Farmacia. Si può solo guardare ed esportare: per modificare serve l'account della persona.")

    st.subheader("🔔 Da controllare")
    con_allerte = [(p, riepiloghi[p["chiave"]]) for p in persone if riepiloghi[p["chiave"]]["allerte"]]
    if not con_allerte:
        st.success("Tutto in ordine: nessuna persona ha cose urgenti.")
    for p, r in con_allerte:
        with st.container(border=True):
            st.markdown(f"**👤 {html.escape(_fam_etichetta(p))}**")
            for a in r["allerte"]:
                st.markdown(f"- {a}")

    st.subheader("🔍 Dettaglio di una persona")
    scelta = st.selectbox("Persona", [p["chiave"] for p in persone], format_func=lambda c: _fam_etichetta(next(p for p in persone if p["chiave"] == c)),
                          key="fam_persona", label_visibility="collapsed")
    _fam_dettaglio_persona(next(p for p in persone if p["chiave"] == scelta), oggi_, ora_adesso)

    st.subheader("🖨️ Esporta e stampa")
    cosa = st.radio("Cosa esportare", ["Tutta la famiglia", "Solo la persona scelta sopra"], horizontal=True, key="fam_cosa", label_visibility="collapsed")
    sel = persone if cosa == "Tutta la famiglia" else [p for p in persone if p["chiave"] == scelta]
    base = "famiglia" if cosa == "Tutta la famiglia" else sel[0]["nome"].replace(" ", "_")
    e1, e2, e3 = st.columns(3, gap="small")
    e1.download_button("🖨️ Da stampare (PDF)", fam_html(sel, oggi_).encode("utf-8"), file_name=f"report_{base}_{oggi_.isoformat()}.html",
                       mime="text/html", width="stretch", key="fam_dl_html")
    e2.download_button("📊 Excel", fam_xlsx(fam_fogli(sel)), file_name=f"farmacia_{base}_{oggi_.isoformat()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch", key="fam_dl_xlsx")
    e3.download_button("📦 Dati (JSON)", fam_json(sel), file_name=f"farmacia_{base}_{oggi_.isoformat()}.json", mime="application/json",
                       width="stretch", key="fam_dl_json")
    st.caption("«Da stampare» si apre nel browser: tocca Stampa e scegli «Salva come PDF» oppure stampa su carta (una persona per pagina). "
               "Contiene dati sanitari: non condividerlo con chi non deve vederlo. Foto e PDF caricati non sono inclusi.")


# ---------------------------------------------------------------------------------------------------------------------
# Pezzi che si inseriscono nella Farmacia
# ---------------------------------------------------------------------------------------------------------------------
def fam_pulsante_capo():
    """Il pulsante «Controllo famiglia» in cima alla Farmacia del capo famiglia."""
    if fam_e_capo() and st.button("👨‍👩‍👧 Controllo famiglia: tutte le persone, terapie, visite, documenti", key="fa_famiglia_apri",
                                  type="primary", width="stretch"):
        st.session_state["fa_famiglia"] = True
        st.rerun()


def fam_avviso_membro():
    """Alle persone inserite nella famiglia: avviso ben visibile che il capo famiglia vede la loro Farmacia."""
    if fam_e_capo():
        return
    try:
        mio = next((u for u in leggi_utenti() if u["id"] == st.session_state["sess"].get("uid")), None)
    except Exception:
        mio = None
    if mio and mio.get("famiglia"):
        st.info("👨‍👩‍👧 **Sei nella famiglia.** Il capo famiglia può vedere i tuoi medicinali, le terapie, le visite, i vaccini e i documenti "
                "(non le foto) per aiutarti a tenere tutto in ordine. Puoi chiedere di essere tolto dalla famiglia.")


def fam_catalogo_medicinali(f, pid):
    """I medicinali già in casa che si possono riusare per non riscriverli: quelli della Farmacia della persona (di tutti i suoi profili) e,
    se la persona fa parte della famiglia, quelli del capo famiglia; il capo famiglia vede anche quelli delle persone inserite nella famiglia.
    Ritorna una lista di (etichetta, dati senza foto né quantità)."""
    visti, risultato = set(), []

    def _aggiungi(meds, nomi):
        for m in meds:
            chiave = (str(m.get("nome", "")).strip().lower(), str(m.get("dosaggio", "")).strip().lower(), str(m.get("forma", "")).strip().lower())
            if not chiave[0] or chiave in visti:
                continue
            visti.add(chiave)
            di_chi = nomi.get(m.get("profilo", "p0"), "")
            etichetta = " · ".join(x for x in (m.get("nome"), m.get("dosaggio"), m.get("forma")) if x) + (f"  (di {di_chi})" if di_chi else "")
            risultato.append((etichetta, {k: m.get(k, "") for k in ("nome", "marca", "principio", "dosaggio", "forma", "unita")}))
    _aggiungi(f.get("medicinali", []), {p_["id"]: p_["nome"] for p_ in _fa_profili(f)})
    try:
        utenti = leggi_utenti()
        if fam_e_capo():
            for u in utenti:
                if u.get("famiglia") and u.get("attivo", True):
                    f_u = carica_dati(crea_archivio(), f"dispense/{u['id']}.json").get("farmacia") or {}
                    _aggiungi(f_u.get("medicinali", []), {p_["id"]: p_["nome"] for p_ in _fam_profili(f_u, u["nome"])})
        else:
            mio = next((u for u in utenti if u["id"] == st.session_state["sess"].get("uid")), None)
            if mio and mio.get("famiglia"):
                f_capo = carica_dati(crea_archivio(), "dispense/admin.json").get("farmacia") or {}
                _aggiungi(f_capo.get("medicinali", []), {p_["id"]: p_["nome"] for p_ in _fam_profili(f_capo, "capo famiglia")})
    except Exception:
        pass
    return sorted(risultato, key=lambda x: x[0].lower())
