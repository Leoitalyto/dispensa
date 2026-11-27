# -*- coding: utf-8 -*-
"""SCADENZIARIO — il «motore» comune (senza Streamlit): lo usano l'app (scadenziario.py) e gli avvisi ad app chiusa (promemoria.py nel repo dei dati).
ATTENZIONE: questo file esiste in DUE copie identiche: «dispensa/scadenziario_core.py» e «dispensa-dati/scadenziario_core.py». Se lo cambi, copialo in tutte e due.

IDEA: lo Scadenziario NON copia i dati delle sezioni. A ogni apertura legge le schede originali (Dispensa, Salute, I miei documenti, Casa, Auto, Animali,
appuntamenti di tutte le sezioni, compleanni…) e ne ricava le «attività» con una chiave stabile (fonte:id:campo). Se cambi una data nella sezione,
qui cambia da sola; se la scheda viene completata/pagata/eliminata, qui sparisce o diventa completata.
Nel file personale, chiave d["scadenziario"], c'è SOLO quello che è dello Scadenziario:
  personali   [{id, titolo, descrizione, data, ora, categoria, priorita, importo, files[], ricorrenza{tipo, ogni}, avvisi{…}, stato, completata_il, creato_il, modificato_il}]
  stati       {chiave: {stato: completata|annullata, data_rif, il, titolo, categoria, sezione}}   (per le attività delle sezioni: valgono solo per QUELLA data)
  avvisi      {chiave: {…}}                 configurazione degli avvisi di una singola attività delle sezioni (se diversa da quella della categoria)
  visto       {chiave: data_rif}            presa visione (ferma la ripetizione dell'avviso)
  impostazioni {ora_avvisi, avvisi_categoria{cat: {…}}, suono, suoni_categoria{cat: suono}, vibrazione, riepilogo{attivo, ora, settimanale, giorno}}
  registro    [{il, azione, chiave, titolo}]  (ultime 300 modifiche)
Le fonti sono in SZ_FONTI: una nuova sezione si aggiunge con sz_registra_fonte(nome, funzione) e le sue scadenze entrano da sole."""
import calendar as _sz_cal
import re as _sz_re
import uuid as _sz_uuid
from datetime import date as _sz_date, datetime as _sz_dt, time as _sz_time, timedelta as _sz_td

SZ_VERSIONE = 1
SZ_CATEGORIE = {
    "personali": ("📌", "Le mie scadenze personali"),
    "salute": ("🩺", "Salute e medicina"),
    "visite": ("📅", "Visite e appuntamenti"),
    "pagamenti": ("💶", "Pagamenti e rate"),
    "documenti": ("🪪", "Documenti e rinnovi"),
    "casa": ("🏠", "Casa e manutenzioni"),
    "auto": ("🚗", "Auto e mezzi"),
    "assicurazioni": ("🛡️", "Assicurazioni e contratti"),
    "famiglia": ("🎂", "Famiglia e ricorrenze"),
    "animali": ("🐾", "Animali"),
    "lavoro": ("💼", "Lavoro"),
    "dispensa": ("🥫", "Dispensa"),
}
SZ_SEZIONI = {"dispensa": "Dispensa", "salute": "Salute", "documenti": "I miei documenti", "casa": "Casa", "auto": "Auto", "animali": "Animali", "lavoro": "Lavoro",
              "utilita": "Utilità", "chat": "Chat", "scadenziario": "Scadenziario"}
SZ_PRIORITA = ["Alta", "Media", "Bassa"]
SZ_STATI = ["Da fare", "In scadenza", "Scaduta", "Completata", "Posticipata", "Annullata"]
SZ_PRESET = [(43200, "30 giorni prima"), (21600, "15 giorni prima"), (10080, "7 giorni prima"), (4320, "3 giorni prima"), (1440, "1 giorno prima"),
             (60, "1 ora prima"), (0, "All'ora stabilita")]
SZ_AVVISI_BASE = {"attivi": True, "anticipi": [10080, 1440, 0], "ripeti": False, "silenzio_fino": "", "rinvio_al": "", "suono": "", "vibrazione": True}
SZ_AVVISI_CATEGORIA = {"pagamenti": [10080, 4320, 1440, 0], "visite": [1440, 60], "salute": [10080, 1440, 0], "dispensa": [4320, 0], "famiglia": [10080, 1440, 0],
                       "documenti": [43200, 10080, 1440], "assicurazioni": [43200, 10080, 1440], "auto": [43200, 10080, 1440]}
SZ_RICORRENZE = {"": "Non si ripete", "giorno": "Ogni giorno", "settimana": "Ogni settimana", "mese": "Ogni mese", "anno": "Ogni anno", "giorni": "Ogni … giorni",
                 "settimane": "Ogni … settimane", "mesi": "Ogni … mesi"}
SZ_IN_SCADENZA_GIORNI = 7


# =====================================================================================================================
# utilità
# =====================================================================================================================
def sz_id():
    return _sz_uuid.uuid4().hex[:10]


def sz_d(x):
    if isinstance(x, _sz_dt):
        return x.date()
    if isinstance(x, _sz_date):
        return x
    try:
        return _sz_date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def sz_ora(x):
    """«9:5» → «09:05»; vuoto o non valido → ""."""
    m = _sz_re.match(r"^\s*(\d{1,2})[:.](\d{2})", str(x or ""))
    if not m:
        return ""
    h, mi = int(m.group(1)), int(m.group(2))
    return f"{h:02d}:{mi:02d}" if 0 <= h < 24 and 0 <= mi < 60 else ""


def sz_num(x):
    try:
        v = float(str(x).replace(",", ".")) if isinstance(x, str) else float(x)
        return v if v == v else None
    except Exception:
        return None


def sz_aggiungi_mesi(d, n, giorno=None):
    """Aggiunge n mesi tenendo il giorno (o il giorno «di base», così il 31 resta 31 quando c'è), e se non esiste usa l'ultimo del mese."""
    m = d.month - 1 + n
    a, m = d.year + m // 12, m % 12 + 1
    return _sz_date(a, m, min(int(giorno or d.day), _sz_cal.monthrange(a, m)[1]))


def sz_compleanno(nascita, anno):
    try:
        return nascita.replace(year=anno)
    except ValueError:                                                   # 29 febbraio negli anni non bisestili → 28
        return _sz_date(anno, 2, 28)


def sz_prossima(data, ric):
    """La data dopo, secondo la ricorrenza {tipo, ogni}. None se non si ripete."""
    t = (ric or {}).get("tipo") or ""
    n = max(int(sz_num((ric or {}).get("ogni")) or 1), 1)
    if not t or not data:
        return None
    if t == "giorno":
        return data + _sz_td(days=1)
    if t == "giorni":
        return data + _sz_td(days=n)
    if t == "settimana":
        return data + _sz_td(weeks=1)
    if t == "settimane":
        return data + _sz_td(weeks=n)
    g0 = (ric or {}).get("giorno")
    if t == "mese":
        return sz_aggiungi_mesi(data, 1, g0)
    if t == "mesi":
        return sz_aggiungi_mesi(data, n, g0)
    if t == "anno":
        return sz_aggiungi_mesi(data, 12, g0)
    return None


def sz_descr_ricorrenza(ric):
    t = (ric or {}).get("tipo") or ""
    n = int(sz_num((ric or {}).get("ogni")) or 1)
    if t in ("giorni", "settimane", "mesi"):
        return f"Ogni {n} " + {"giorni": "giorni", "settimane": "settimane", "mesi": "mesi"}[t]
    return SZ_RICORRENZE.get(t, "")


def sz_quando(data, ora, ora_avvisi="09:00"):
    """datetime dell'attività (date senza ora: all'ora degli avvisi)."""
    o = sz_ora(ora) or sz_ora(ora_avvisi) or "09:00"
    return _sz_dt.combine(data, _sz_time(int(o[:2]), int(o[3:5])))


def _sz_voce(chiave, titolo, data, categoria, sezione, descrizione="", ora="", importo=None, priorita="", ricorrente="", rif=None, nav=None, profilo=None):
    d = sz_d(data)
    if not d:
        return None
    return {"chiave": chiave, "titolo": str(titolo or "Attività").strip()[:120], "descrizione": str(descrizione or "").strip()[:300], "data": d, "ora": sz_ora(ora),
            "categoria": categoria if categoria in SZ_CATEGORIE else "personali", "sezione": sezione, "importo": sz_num(importo), "priorita": priorita,
            "ricorrente": ricorrente, "rif": rif or {}, "nav": nav or {"sezione": sezione}, "personale": False, "profilo": profilo}


# =====================================================================================================================
# LE FONTI (una funzione per sezione: legge le schede originali e ne fa attività). Solo date VERE: niente date inventate.
# =====================================================================================================================
def _sz_f_dispensa(d, oggi):
    out = []
    for a in d.get("articoli") or []:
        if isinstance(a, dict) and a.get("scadenza") and a.get("id"):
            out.append(_sz_voce(f"dispensa:{a['id']}:scadenza", f"🥫 {a.get('nome') or 'Prodotto'} scade", a["scadenza"], "dispensa", "dispensa",
                             descrizione=" · ".join(x for x in (a.get("marca"), a.get("posto")) if x)))
    return out


def _sz_nome_prof(f, pid):
    prof = (f or {}).get("profili") or []
    if len(prof) <= 1:
        return ""
    return next((p.get("nome", "") for p in prof if p.get("id") == pid), "")


def _sz_f_salute(d, oggi):
    f = d.get("farmacia") or {}
    out = []
    per = lambda pid: (f" ({_sz_nome_prof(f, pid)})" if _sz_nome_prof(f, pid) else "")
    for m in f.get("medicinali") or []:
        if m.get("scadenza") and m.get("id"):
            out.append(_sz_voce(f"salute:med:{m['id']}", f"💊 {m.get('nome') or 'Medicinale'} scade" + per(m.get("profilo")), m["scadenza"], "salute", "salute",
                             descrizione=str(m.get("dosaggio") or ""), profilo=m.get("profilo")))
    for x in f.get("prescrizioni") or []:
        if x.get("valida_fino") and x.get("stato") != "Usata" and x.get("id"):
            out.append(_sz_voce(f"salute:presc:{x['id']}", f"📝 Prescrizione {str(x.get('tipo') or '').lower()} da usare entro" + per(x.get("profilo")), x["valida_fino"], "salute", "salute",
                             descrizione=str(x.get("farmaco") or x.get("descrizione") or x.get("note") or ""), profilo=x.get("profilo")))
    for x in f.get("visite") or []:
        if not x.get("id"):
            continue
        dv = sz_d(x.get("data"))
        if dv and dv >= oggi - _sz_td(days=1):
            out.append(_sz_voce(f"salute:visita:{x['id']}", f"🩺 Visita: {x.get('categoria') or 'visita'}" + per(x.get("profilo")), dv, "visite", "salute", ora=x.get("ora"),
                             descrizione=" · ".join(y for y in (x.get("medico"), x.get("motivo")) if y), profilo=x.get("profilo")))
        if x.get("prossimo"):
            out.append(_sz_voce(f"salute:visita_pross:{x['id']}", f"🩺 Prossimo controllo: {x.get('categoria') or 'visita'}" + per(x.get("profilo")), x["prossimo"], "visite", "salute",
                             descrizione=str(x.get("medico") or ""), profilo=x.get("profilo")))
    for x in f.get("vaccinazioni") or []:
        if x.get("richiamo") and x.get("id"):
            out.append(_sz_voce(f"salute:vacc:{x['id']}", f"💉 Richiamo {x.get('nome') or 'vaccino'}" + per(x.get("profilo")), x["richiamo"], "salute", "salute", profilo=x.get("profilo")))
    for t in f.get("terapie") or []:
        if t.get("fine") and t.get("id") and t.get("stato", "attiva") == "attiva":
            out.append(_sz_voce(f"salute:ter:{t['id']}", f"💊 Fine terapia {t.get('nome_med') or ''}".strip() + per(t.get("profilo")), t["fine"], "salute", "salute",
                             descrizione=", ".join(t.get("orari") or []), profilo=t.get("profilo")))
    for p in f.get("profili") or []:
        nome = f" ({p.get('nome', '')})" if len(f.get("profili") or []) > 1 else ""
        for c in p.get("controlli") or []:
            pr = sz_d(c.get("prossimo"))
            if not pr and c.get("ultimo") and int(sz_num(c.get("ogni_mesi")) or 0) > 0:
                u = sz_d(c["ultimo"])
                pr = sz_aggiungi_mesi(u, int(sz_num(c["ogni_mesi"]))) if u else None
            if pr and c.get("id"):
                out.append(_sz_voce(f"salute:contr:{p.get('id')}:{c['id']}", f"⏰ {c.get('nome') or 'Controllo periodico'}{nome}", pr, "salute", "salute",
                                 ricorrente=(f"ogni {int(sz_num(c.get('ogni_mesi')))} mesi" if sz_num(c.get("ogni_mesi")) else ""), profilo=p.get("id")))
        for e in p.get("esenzioni") or []:
            if e.get("permanente") or not e.get("id"):
                continue
            cand = [x for x in (sz_d(e.get("valida_fino")), sz_d(e.get("revisione"))) if x]
            if cand:
                out.append(_sz_voce(f"salute:esen:{p.get('id')}:{e['id']}", f"🪪 Esenzione/invalidità {e.get('codice') or e.get('nome') or ''}".strip() + nome, min(cand), "documenti", "salute", profilo=p.get("id")))
        for x in p.get("docsan") or []:
            if x.get("prossimo_controllo") and x.get("id"):
                out.append(_sz_voce(f"salute:docsan:{x['id']}", f"🩺 Controllo indicato: {x.get('titolo') or x.get('tipo') or 'referto'}{nome}", x["prossimo_controllo"], "visite", "salute", profilo=p.get("id")))
    # PERCORSI DI CURA (salute_percorsi.py): appuntamenti non ancora fatti e rate non coperte dai pagamenti (coperte in ordine di scadenza)
    for pc in f.get("percorsi") or []:
        if not pc.get("id") or pc.get("stato") in ("Concluso", "Sospeso"):
            continue
        nav = {"sezione": "salute", "percorso": pc["id"], "profilo": pc.get("profilo")}
        tit = str(pc.get("titolo") or "Percorso di cura")[:60]
        luogo = str((pc.get("struttura") or {}).get("nome") or "")
        for a in pc.get("appuntamenti") or []:
            dv = sz_d(a.get("data"))
            if a.get("id") and dv and not a.get("fatto") and dv >= oggi - _sz_td(days=1):
                v = _sz_voce(f"salute:percorso:{pc['id']}:app:{a['id']}", f"🗂️ {tit}" + (f": {a['cosa']}" if a.get("cosa") else "") + per(pc.get("profilo")), dv, "visite", "salute",
                             ora=a.get("ora"), descrizione=" · ".join(y for y in (luogo, a.get("note")) if y), nav=nav, profilo=pc.get("profilo"))
                if v:
                    out.append(v)
        pagato = sum(sz_num(x.get("importo")) or 0 for x in pc.get("pagamenti") or [])
        for r in sorted(pc.get("rate") or [], key=lambda r: (str(r.get("scadenza") or "9999"), str(r.get("id") or ""))):
            imp = sz_num(r.get("importo")) or 0
            cop = min(imp, max(0.0, pagato))
            pagato -= cop
            residuo = round(imp - cop, 2)
            if r.get("id") and residuo > 0.005 and sz_d(r.get("scadenza")):
                v = _sz_voce(f"salute:percorso:{pc['id']}:rata:{r['id']}", f"💶 {tit}: {r.get('nota') or 'rata'}" + per(pc.get("profilo")), r["scadenza"], "pagamenti", "salute",
                             importo=residuo, descrizione=luogo, priorita="Alta", nav=nav, profilo=pc.get("profilo"))
                if v:
                    out.append(v)
    return out


def _sz_f_documenti(d, oggi):
    f = d.get("farmacia") or {}
    out = []
    for x in f.get("documenti") or []:
        if x.get("scadenza") and not x.get("senza_scadenza") and x.get("id"):
            nome = _sz_nome_prof(f, x.get("profilo"))
            out.append(_sz_voce(f"documenti:{x['id']}", f"🪪 {x.get('tipo') or 'Documento'} scade" + (f" ({nome})" if nome else ""), x["scadenza"], "documenti", "documenti",
                             descrizione=str(x.get("numero") or ""), profilo=x.get("profilo")))
    return out


def _sz_f_casa(d, oggi):
    c = d.get("casa") or {}
    out = []
    docs = [x for x in c.get("documenti") or [] if isinstance(x, dict)]
    pagate = {x.get("collegato_a") for x in docs if x.get("collegato_a")}
    for x in docs:
        if not x.get("id") or not x.get("scadenza_doc"):
            continue
        nome = x.get("titolo") or " · ".join(y for y in (x.get("argomento"), x.get("ente")) if y) or x.get("tipo") or "Documento"
        if x.get("tipo") in ("Bolletta o fattura", "Polizza assicurativa"):
            if x.get("pagata_il") or x["id"] in pagate or str(x.get("modo_pagamento") or "").startswith("Addebito"):
                continue                                                 # pagata: non è più da fare
            cat = "assicurazioni" if x.get("tipo") == "Polizza assicurativa" else "pagamenti"
            out.append(_sz_voce(f"casa:doc:{x['id']}", f"💶 Da pagare: {nome}", x["scadenza_doc"], cat, "casa", importo=x.get("importo"), priorita="Alta"))
        elif x.get("tipo") not in ("Busta paga", "Certificazione Unica (CU)", "Documento INPS"):
            out.append(_sz_voce(f"casa:doc:{x['id']}", f"📄 Scade: {nome}", x["scadenza_doc"], "assicurazioni" if "contratt" in str(x.get("tipo", "")).lower() else "casa", "casa"))
    nomi = {b.get("id"): b.get("nome", "") for b in c.get("beni") or [] if isinstance(b, dict)}
    for b in c.get("beni") or []:
        if isinstance(b, dict) and b.get("garanzia_fino") and b.get("id"):
            out.append(_sz_voce(f"casa:gar:{b['id']}", f"🧾 Fine garanzia: {b.get('nome') or 'bene'}", b["garanzia_fino"], "casa", "casa"))
    ultime = {}
    for m in sorted([m for m in c.get("manutenzioni") or [] if isinstance(m, dict)], key=lambda m: m.get("data") or ""):
        k = (m.get("intervento") or "", m.get("bene_id"), m.get("tipo"))
        ultime[k] = m
    for m in ultime.values():
        if m.get("prossima") and m.get("id") and (not m.get("bene_id") or m.get("bene_id") in nomi):
            voce = m.get("intervento") or m.get("descrizione") or m.get("tipo") or "Manutenzione"
            out.append(_sz_voce(f"casa:man:{m['id']}", f"🔧 {voce}" + (f" · {nomi.get(m.get('bene_id'))}" if nomi.get(m.get("bene_id")) else ""), m["prossima"], "casa", "casa"))
    for s in c.get("spese_amm") or []:
        if not isinstance(s, dict) or not s.get("id"):
            continue
        for r in s.get("rate") or []:
            pagato = sum(sz_num(p.get("importo")) or 0 for p in r.get("pagamenti") or [])
            residuo = round((sz_num(r.get("importo")) or 0) - pagato, 2)
            if residuo > 0.004 and r.get("scadenza") and r.get("id"):
                out.append(_sz_voce(f"casa:rata:{s['id']}:{r['id']}", f"🏢 {s.get('descrizione') or 'Spesa condominio'}" + (f" (rata {r.get('n')})" if len(s.get("rate") or []) > 1 else ""),
                                 r["scadenza"], "pagamenti", "casa", importo=residuo, priorita="Alta"))
    return out


_SZ_AUTO_ET = {"bollo": ("💶 Bollo", "pagamenti"), "assicurazione": ("🛡️ Assicurazione RCA", "assicurazioni"), "revisione": ("🔍 Revisione", "auto"),
               "garanzia_auto": ("🧾 Garanzia del veicolo", "auto"), "garanzia_batteria": ("🔋 Garanzia batteria", "auto"), "tagliando": ("🔧 Tagliando", "auto"),
               "tachigrafo": ("⏱️ Taratura tachigrafo", "auto")}


def _sz_f_auto(d, oggi):
    a = d.get("auto") or {}
    out = []
    veic = [v for v in a.get("veicoli") or [] if isinstance(v, dict) and v.get("id")]
    for v in veic:
        nome = " ".join(str(v.get(k) or "") for k in ("marca", "modello") if v.get(k)).strip() or v.get("targa") or "veicolo"
        for k, s in (v.get("scadenze") or {}).items():
            if isinstance(s, dict) and s.get("data") and s.get("avvisa") is not False:
                et, cat = _SZ_AUTO_ET.get(k, (k.replace("_", " ").capitalize(), "auto"))
                out.append(_sz_voce(f"auto:{v['id']}:{k}", f"{et} · {nome}", s["data"], cat, "auto", importo=s.get("importo"),
                                 nav={"sezione": "auto", "veicolo": v["id"]}))
        sc = v.get("scadenze") or {}
        doppie = {(sc.get("assicurazione") or {}).get("data"), (sc.get("revisione") or {}).get("data")}
        for dc in v.get("documenti") or []:
            if isinstance(dc, dict) and dc.get("scadenza") and dc.get("id") and not (dc.get("tipo") in ("Polizza assicurativa", "Revisione (certificato)") and dc.get("scadenza") in doppie):
                out.append(_sz_voce(f"auto:{v['id']}:doc:{dc['id']}", f"📄 {dc.get('titolo') or dc.get('tipo') or 'Documento'} · {nome}", dc["scadenza"],
                                 "assicurazioni" if dc.get("tipo") == "Polizza assicurativa" else "auto", "auto", importo=dc.get("importo"), nav={"sezione": "auto", "veicolo": v["id"]}))
        for us in v.get("usura") or []:
            if isinstance(us, dict) and us.get("prossima_data") and us.get("id"):
                out.append(_sz_voce(f"auto:{v['id']}:usura:{us['id']}", f"🧩 {us.get('parte') or 'Parte'} da controllare · {nome}", us["prossima_data"], "auto", "auto",
                                 nav={"sezione": "auto", "veicolo": v["id"]}))
    cond = a.get("conducente") or {}
    for pt in cond.get("patenti") or []:
        if not isinstance(pt, dict) or pt.get("avvisa") is False:
            continue
        for k, et in (("scadenza", "Patente"), ("visita_medica", "Visita medica patente"), ("cqc", "CQC")):
            if pt.get(k) and not (pt.get("doc_id") and k in ("scadenza", "cqc")):     # collegata a I miei documenti: lì ci sono già patente e CQC
                out.append(_sz_voce(f"auto:pat:{pt.get('id') or pt.get('nome')}:{k}", f"🪪 {et}" + (f" di {pt['nome']}" if pt.get("nome") else ""), pt[k], "documenti", "auto"))
    for vb in cond.get("verbali") or []:
        if isinstance(vb, dict) and vb.get("stato") == "Da pagare" and vb.get("scadenza_pagamento"):
            out.append(_sz_voce(f"auto:verb:{vb.get('id') or vb.get('numero')}", f"🧾 Multa da pagare ({vb.get('tipo') or vb.get('luogo') or 'verbale'})", vb["scadenza_pagamento"],
                             "pagamenti", "auto", importo=vb.get("importo"), priorita="Alta"))
    return out


def _sz_f_animali(d, oggi):
    a = d.get("animali") or {}
    nomi = {x.get("id"): x.get("nome") or "" for x in a.get("lista") or [] if isinstance(x, dict)}
    out = []
    ultimi = {}
    for r in a.get("vaccini") or []:
        if isinstance(r, dict):
            k = (r.get("animale"), str(r.get("nome") or "").lower(), r.get("tipo"))
            if k not in ultimi or str(r.get("data") or "") >= str(ultimi[k].get("data") or ""):
                ultimi[k] = r
    for r in ultimi.values():
        if r.get("richiamo") and r.get("animale") in nomi and r.get("id"):
            out.append(_sz_voce(f"animali:vacc:{r['id']}", f"🐾 {nomi[r['animale']]}: {str(r.get('tipo') or 'richiamo').lower()} {r.get('nome') or ''}".strip(), r["richiamo"], "animali", "animali"))
    for cat, campo, testo in (("visite", "prossimo", "controllo veterinario"), ("terapie", "al", "fine terapia"), ("documenti", "scadenza", "scade")):
        for r in a.get(cat) or []:
            if isinstance(r, dict) and r.get(campo) and r.get("animale") in nomi and r.get("id"):
                det = r.get("farmaco") or r.get("titolo") or ""
                out.append(_sz_voce(f"animali:{cat}:{r['id']}", f"🐾 {nomi[r['animale']]}: {testo}" + (f" {det}" if det else ""), r[campo], "animali", "animali"))
    for r in a.get("agenda") or []:
        if isinstance(r, dict) and r.get("data") and not r.get("fatto") and r.get("animale") in nomi and r.get("id"):
            out.append(_sz_voce(f"animali:agenda:{r['id']}", f"🐾 {nomi[r['animale']]}: {r.get('titolo') or 'appuntamento'}", r["data"], "animali", "animali", ora=r.get("ora")))
    return out


_SZ_SEZ_APP = {"salute": "visite", "documenti": "documenti", "casa": "casa", "lavoro": "lavoro", "auto": "auto", "animali": "animali", "archivio": "visite", "utilita": "visite"}


def _sz_f_appuntamenti(d, oggi):
    out = []
    for sez, lst in (d.get("appuntamenti") or {}).items():
        base = str(sez).split("@")[0]
        for x in lst or []:
            if isinstance(x, dict) and x.get("data") and x.get("id") and not x.get("fatto"):
                cat = "lavoro" if base == "lavoro" else "visite"
                out.append(_sz_voce(f"app:{sez}:{x['id']}", f"📅 {x.get('nome') or 'Appuntamento'}" + (f" ({x['funzione']})" if x.get("funzione") else ""), x["data"], cat,
                                 base if base in SZ_SEZIONI else "salute", ora=x.get("ora"), descrizione=" · ".join(y for y in (x.get("motivo") or x.get("motivazione"), x.get("luogo"), x.get("telefono")) if y),
                                 priorita=x.get("priorita") or "", nav={"sezione": base, "appuntamenti": sez}, profilo=(str(sez).split("@", 1)[1] if "@" in str(sez) else None)))
    return out


def _sz_f_compleanni(d, oggi):
    out = []
    for x in d.get("compleanni") or []:
        if not isinstance(x, dict) or x.get("scomparso") or not x.get("id"):
            continue
        n = sz_d(x.get("nascita"))
        if not n:
            continue
        p = sz_compleanno(n, oggi.year)
        if p < oggi:
            p = sz_compleanno(n, oggi.year + 1)
        nome = (str(x.get("nome") or "") + " " + str(x.get("cognome") or "")).strip() or "?"
        anni = "" if x.get("anno_ignoto") else f" ({p.year - n.year} anni)"
        out.append(_sz_voce(f"compleanni:{x['id']}", f"🎂 Compleanno di {nome}{anni}", p, "famiglia", "utilita", ricorrente="ogni anno", nav={"sezione": "utilita", "riquadro": "compleanni"}))
    return out


def _sz_bdt_costo(b, g, ini):
    ov = (b.get("giorni") or {}).get(g.isoformat())
    if isinstance(ov, dict):
        return sz_num(ov.get("importo")) or 0.0
    if ini and g < ini:
        return 0.0
    gs = b.get("giorni_sett") if isinstance(b.get("giorni_sett"), list) else range(7)
    return (sz_num(b.get("tariffa", 20)) or 0.0) if g.weekday() in gs else 0.0


def _sz_f_badante(d, oggi):
    """L'ultimo giorno in cui bastano i soldi della badante (stesso calcolo di badante.py)."""
    b = d.get("badante")
    if not isinstance(b, dict) or not b.get("consegne"):
        return []
    ini = sz_d(b.get("inizio")) or min([x for x in (sz_d(c.get("data")) for c in b["consegne"] if isinstance(c, dict)) if x] or [None]) if b.get("consegne") else None
    dato = sum(sz_num(c.get("importo")) or 0 for c in b["consegne"] if isinstance(c, dict) and (sz_d(c.get("data")) or oggi) <= oggi)
    speso, g = 0.0, ini
    while g and g <= oggi:
        speso += _sz_bdt_costo(b, g, ini)
        g += _sz_td(days=1)
    resto, fine, g = dato - speso, None, oggi
    for _ in range(730):
        g += _sz_td(days=1)
        c = _sz_bdt_costo(b, g, ini)
        if c <= 0:
            continue
        if resto - c < -0.005:
            break
        resto -= c
        fine = g
    if fine is None and dato - speso >= 0:
        fine = oggi
    if not fine:
        return []
    return [_sz_voce(f"badante:fine:{fine.isoformat()}", "👵 Ultimo giorno pagato della badante: dare altri soldi", fine, "famiglia", "casa", priorita="Alta",
                  nav={"sezione": "casa", "badante": True})]


SZ_FONTI = [("dispensa", _sz_f_dispensa), ("salute", _sz_f_salute), ("documenti", _sz_f_documenti), ("casa", _sz_f_casa), ("auto", _sz_f_auto), ("animali", _sz_f_animali),
            ("appuntamenti", _sz_f_appuntamenti), ("compleanni", _sz_f_compleanni), ("badante", _sz_f_badante)]


def sz_registra_fonte(nome, funzione):
    """Una sezione nuova porta le sue scadenze nello Scadenziario: funzione(d, oggi) → [_sz_voce(…)]."""
    global SZ_FONTI
    SZ_FONTI = [f for f in SZ_FONTI if f[0] != nome] + [(nome, funzione)]


# =====================================================================================================================
# LE SCADENZE PERSONALI
# =====================================================================================================================
def sz_migra(d):
    sz = d.get("scadenziario")
    if not isinstance(sz, dict):
        sz = d["scadenziario"] = {}
    for k, v in (("personali", []), ("stati", {}), ("avvisi", {}), ("visto", {}), ("impostazioni", {}), ("registro", [])):
        if not isinstance(sz.get(k), type(v)):
            sz[k] = v
    sz["versione"] = SZ_VERSIONE
    return sz


def sz_log(sz, azione, chiave="", titolo=""):
    sz.setdefault("registro", []).append({"il": _sz_dt.now().isoformat(timespec="seconds"), "azione": azione, "chiave": chiave, "titolo": str(titolo)[:80]})
    del sz["registro"][:-300]


def sz_valida_personale(p):
    err = []
    if not str(p.get("titolo") or "").strip():
        err.append("Scrivi il titolo.")
    if not sz_d(p.get("data")):
        err.append("Scegli la data.")
    if p.get("ora") and not sz_ora(p.get("ora")):
        err.append("L'ora deve essere come 09:30.")
    if p.get("importo") not in (None, "") and (sz_num(p.get("importo")) is None or sz_num(p.get("importo")) < 0):
        err.append("L'importo deve essere un numero.")
    r = p.get("ricorrenza") or {}
    if r.get("tipo") and r["tipo"] not in SZ_RICORRENZE:
        err.append("Ricorrenza non valida.")
    return err


def sz_nuova_personale(sz, p):
    err = sz_valida_personale(p)
    if err:
        raise ValueError(" ".join(err))
    ora = _sz_dt.now().isoformat(timespec="seconds")
    x = {"id": sz_id(), "titolo": str(p["titolo"]).strip(), "descrizione": str(p.get("descrizione") or "").strip(), "data": sz_d(p["data"]).isoformat(),
         "ora": sz_ora(p.get("ora")), "categoria": str(p.get("categoria") or "Personale").strip(), "profilo": p.get("profilo") or "", "priorita": p.get("priorita") if p.get("priorita") in SZ_PRIORITA else "Media",
         "importo": sz_num(p.get("importo")), "files": list(p.get("files") or []), "ricorrenza": dict(p.get("ricorrenza") or {"tipo": ""}, giorno=sz_d(p["data"]).day),
         "avvisi": dict(SZ_AVVISI_BASE, **(p.get("avvisi") or {})), "stato": "da fare", "completata_il": "", "creato_il": ora, "modificato_il": ora}
    sz["personali"].append(x)
    sz_log(sz, "creata", "pers:" + x["id"], x["titolo"])
    return x


def sz_completa_personale(sz, pid, oggi=None):
    """Completa; se si ripete crea SUBITO la prossima (una sola volta: se esiste già non la rifà). Ritorna la nuova (o None)."""
    oggi = oggi or _sz_date.today()
    x = next((p for p in sz["personali"] if p.get("id") == pid), None)
    if not x or x.get("stato") == "completata":
        return None
    x["stato"], x["completata_il"] = "completata", _sz_dt.now().isoformat(timespec="seconds")
    sz_log(sz, "completata", "pers:" + pid, x.get("titolo"))
    prossima = sz_prossima(sz_d(x["data"]), x.get("ricorrenza"))
    if not prossima:
        return None
    if x.get("successiva") and any(p.get("id") == x["successiva"] for p in sz["personali"]):
        return None
    nuova = dict(x, id=sz_id(), data=prossima.isoformat(), stato="da fare", completata_il="", creato_il=_sz_dt.now().isoformat(timespec="seconds"), precedente=pid)
    nuova.pop("successiva", None)
    nuova["avvisi"] = dict(x.get("avvisi") or SZ_AVVISI_BASE, rinvio_al="", silenzio_fino="")
    x["successiva"] = nuova["id"]
    sz["personali"].append(nuova)
    sz_log(sz, "ripetuta", "pers:" + nuova["id"], nuova["titolo"])
    return nuova


def sz_duplica_personale(sz, pid):
    x = next((p for p in sz["personali"] if p.get("id") == pid), None)
    if not x:
        return None
    n = dict(x, id=sz_id(), titolo=x["titolo"] + " (copia)", stato="da fare", completata_il="", creato_il=_sz_dt.now().isoformat(timespec="seconds"))
    n.pop("successiva", None), n.pop("precedente", None)
    sz["personali"].append(n)
    sz_log(sz, "duplicata", "pers:" + n["id"], n["titolo"])
    return n


# =====================================================================================================================
# RACCOLTA, STATI, RIEPILOGO
# =====================================================================================================================
def sz_cfg_avvisi(sz, voce):
    """La configurazione degli avvisi di un'attività: la sua, oppure quella della categoria, oppure quella di base."""
    imp = sz.get("impostazioni") or {}
    if voce.get("personale"):
        base = voce.get("avvisi") or {}
    else:
        base = (sz.get("avvisi") or {}).get(voce["chiave"]) or {}
    cat = (imp.get("avvisi_categoria") or {}).get(voce["categoria"]) or {}
    out = dict(SZ_AVVISI_BASE, anticipi=list(SZ_AVVISI_CATEGORIA.get(voce["categoria"], SZ_AVVISI_BASE["anticipi"])))
    out.update(cat)
    out.update(base)
    return out


def sz_stato(voce, adesso, sz=None):
    """Da fare | In scadenza | Scaduta | Completata | Posticipata | Annullata."""
    s = voce.get("_stato_fisso")
    if s:
        return s
    oggi = adesso.date()
    cfg = sz_cfg_avvisi(sz or {}, voce) if sz is not None else {}
    rinvio = cfg.get("rinvio_al")
    quando = sz_quando(voce["data"], voce.get("ora"), ((sz or {}).get("impostazioni") or {}).get("ora_avvisi") or "09:00")
    if voce["data"] < oggi or (voce.get("ora") and quando < adesso):
        return "Scaduta"
    if rinvio and str(rinvio) > adesso.isoformat(timespec="minutes"):
        return "Posticipata"
    if (voce["data"] - oggi).days <= SZ_IN_SCADENZA_GIORNI:
        return "In scadenza"
    return "Da fare"


def sz_profili(d):
    """[(id, nome)] delle persone seguite (i profili di Salute: il primo è il principale)."""
    prof = [(p.get("id"), p.get("nome") or "?") for p in ((d.get("farmacia") or {}).get("profili") or []) if isinstance(p, dict) and p.get("id")]
    return prof or [("p0", "Io")]


def sz_principale(d):
    return sz_profili(d)[0][0]


def _sz_assegna_profili(d, voci):
    """Di chi è ogni attività: quella scritta nella scheda; per Casa la persona della casa (casa_id); altrimenti il profilo principale."""
    ids = [i for i, _n in sz_profili(d)]
    princ = ids[0]
    c = d.get("casa") or {}
    case = {x.get("id"): (x.get("profilo") or x.get("persona")) for x in (c.get("case") or []) if isinstance(x, dict) and x.get("id")}
    case[""] = c.get("persona_principale") or princ
    per_id = {}
    for lista in ("documenti", "beni", "manutenzioni", "spese_amm"):
        for x in c.get(lista) or []:
            if isinstance(x, dict) and x.get("id"):
                per_id[x["id"]] = case.get(x.get("casa_id") or "", princ)
    for v in voci:
        if v.get("profilo") in ids:
            continue
        if v.get("sezione") == "casa" and v["chiave"].startswith("casa:"):
            pz = v["chiave"].split(":")
            v["profilo"] = per_id.get(pz[2] if len(pz) > 2 else "", princ) if per_id.get(pz[2] if len(pz) > 2 else "") in ids else princ
        else:
            v["profilo"] = princ


def sz_raccogli(d, adesso, d_extra=None, solo_aperte=False):
    """Tutte le attività: sezioni (lette ora dalle schede originali) + personali. Ogni voce ha 'stato'. Niente doppioni (chiave unica)."""
    oggi = adesso.date()
    sz = sz_migra(dict(d)) if not isinstance(d.get("scadenziario"), dict) else d["scadenziario"]
    voci, viste = [], set()
    fonti_dati = [d] + ([d_extra] if d_extra is not None and d_extra is not d else [])
    for dd in fonti_dati:
        for nome, fn in SZ_FONTI:
            if dd is not d and nome != "dispensa":
                continue                                                 # dalla dispensa di famiglia solo i prodotti
            try:
                nuove = fn(dd, oggi)
            except Exception:
                nuove = []
            for v in nuove:
                if v and v["chiave"] not in viste:
                    viste.add(v["chiave"])
                    voci.append(v)
    _sz_assegna_profili(d, voci)
    stati = sz.get("stati") or {}
    for v in voci:
        st_ = stati.get(v["chiave"])
        if st_ and st_.get("data_rif") == v["data"].isoformat():
            v["_stato_fisso"] = "Completata" if st_.get("stato") == "completata" else "Annullata" if st_.get("stato") == "annullata" else None
            if st_.get("priorita"):
                v["priorita"] = st_["priorita"]
        elif st_ and st_.get("priorita") and not st_.get("stato"):
            v["priorita"] = st_["priorita"]
    for p in sz.get("personali") or []:
        dp = sz_d(p.get("data"))
        if not dp or not p.get("id"):
            continue
        v = {"chiave": "pers:" + p["id"], "titolo": p.get("titolo") or "Attività", "descrizione": p.get("descrizione") or "", "data": dp, "ora": sz_ora(p.get("ora")),
             "categoria": "personali", "categoria_pers": p.get("categoria") or "Personale", "sezione": "scadenziario", "importo": sz_num(p.get("importo")),
             "priorita": p.get("priorita") or "Media", "ricorrente": sz_descr_ricorrenza(p.get("ricorrenza")), "rif": {"id": p["id"]}, "nav": {"sezione": "scadenziario"},
             "personale": True, "avvisi": p.get("avvisi") or {}, "files": p.get("files") or [], "profilo": p.get("profilo") or sz_principale(d)}
        if p.get("stato") == "completata":
            v["_stato_fisso"] = "Completata"
        elif p.get("stato") == "annullata":
            v["_stato_fisso"] = "Annullata"
        voci.append(v)
    for v in voci:
        if not v.get("priorita"):
            g = (v["data"] - oggi).days
            v["priorita"] = "Alta" if (v["categoria"] == "pagamenti" or g < 0) else "Media" if g <= 30 else "Bassa"
        v["stato"] = sz_stato(v, adesso, sz)
    # le completate/annullate delle sezioni che non esistono più alla fonte restano nello storico (solo titolo e data)
    for k, st_ in stati.items():
        if st_.get("stato") in ("completata", "annullata") and k not in viste and sz_d(st_.get("data_rif")):
            voci.append({"chiave": k, "titolo": st_.get("titolo") or k, "descrizione": "", "data": sz_d(st_["data_rif"]), "ora": "", "categoria": st_.get("categoria") or "personali",
                         "sezione": st_.get("sezione") or "scadenziario", "importo": None, "priorita": "Bassa", "ricorrente": "", "rif": {}, "nav": {"sezione": st_.get("sezione") or "scadenziario"},
                         "personale": False, "stato": "Completata" if st_["stato"] == "completata" else "Annullata", "solo_storico": True,
                         "profilo": st_.get("profilo") or sz_principale(d)})
    if solo_aperte:
        voci = [v for v in voci if v["stato"] not in ("Completata", "Annullata")]
    voci.sort(key=lambda v: (v["data"], v.get("ora") or "99:99", v["titolo"]))
    return voci


def sz_riepilogo(voci, adesso):
    oggi = adesso.date()
    r = {"scadute": 0, "oggi": 0, "7": 0, "30": 0, "future": 0, "completate": 0}
    for v in voci:
        if v["stato"] in ("Completata", "Annullata"):
            r["completate"] += v["stato"] == "Completata"
            continue
        g = (v["data"] - oggi).days
        if v["stato"] == "Scaduta":
            r["scadute"] += 1
        elif g == 0:
            r["oggi"] += 1
        elif g <= 7:
            r["7"] += 1
        elif g <= 30:
            r["30"] += 1
        else:
            r["future"] += 1
    return r


def sz_periodo(v, adesso):
    """In quale riquadro del riepilogo sta."""
    if v["stato"] in ("Completata", "Annullata"):
        return "completate"
    g = (v["data"] - adesso.date()).days
    return "scadute" if v["stato"] == "Scaduta" else "oggi" if g == 0 else "7" if g <= 7 else "30" if g <= 30 else "future"


def sz_filtra(voci, testo="", categorie=None, periodo="", stati=None, priorita=None, sezioni=None, solo_personali=False, adesso=None, profili=None):
    out = []
    parole = [w for w in _sz_re.sub(r"[^\w\s]", " ", str(testo or "").lower()).split() if w]
    for v in voci:
        if profili and v.get("profilo") not in profili:
            continue
        if categorie and v["categoria"] not in categorie:
            continue
        if stati and v["stato"] not in stati:
            continue
        if priorita and v.get("priorita") not in priorita:
            continue
        if sezioni and v.get("sezione") not in sezioni:
            continue
        if solo_personali and not v.get("personale"):
            continue
        if periodo and adesso and sz_periodo(v, adesso) != periodo:
            continue
        if parole:
            t = (v["titolo"] + " " + v.get("descrizione", "") + " " + str(v.get("categoria_pers") or "") + " " + SZ_CATEGORIE.get(v["categoria"], ("", ""))[1]).lower()
            if not all(w in t for w in parole):
                continue
        out.append(v)
    return out


# =====================================================================================================================
# AVVISI (anche ad app chiusa): quali mandare adesso, senza doppioni
# =====================================================================================================================
def sz_etichetta_anticipo(minuti):
    m = int(minuti)
    for v, et in SZ_PRESET:
        if v == m:
            return et
    if m % 1440 == 0:
        return f"{m // 1440} giorni prima"
    if m % 60 == 0:
        return f"{m // 60} ore prima"
    return f"{m} minuti prima"


def sz_avvisi_da_mandare(d, adesso, finestra_min=60, voci=None):
    """[(voce, motivo, chiave_registro)] da mandare ADESSO: per ogni anticipo scelto, se l'orario dell'avviso è caduto negli ultimi «finestra_min» minuti;
    il rinvio («posticipa avviso») manda un avviso all'ora scelta; «ripeti finché non confermi» ripete ogni giorno all'ora degli avvisi.
    La chiave del registro (con data e anticipo) evita doppioni anche se il controllo gira più volte."""
    sz = sz_migra(d) if not isinstance(d.get("scadenziario"), dict) else d["scadenziario"]
    ora_avv = (sz.get("impostazioni") or {}).get("ora_avvisi") or "09:00"
    voci = voci if voci is not None else sz_raccogli(d, adesso, solo_aperte=True)
    out = []
    da = adesso - _sz_td(minutes=finestra_min)
    for v in voci:
        if v["stato"] in ("Completata", "Annullata") or v.get("solo_storico"):
            continue
        cfg = sz_cfg_avvisi(sz, v)
        if not cfg.get("attivi", True):
            continue
        if cfg.get("silenzio_fino") and str(cfg["silenzio_fino"])[:10] >= adesso.date().isoformat():
            continue
        quando = sz_quando(v["data"], v.get("ora"), ora_avv)
        base_k = f"scad|{v['chiave']}|{v['data'].isoformat()}"
        for m in sorted({int(sz_num(x) or 0) for x in cfg.get("anticipi") or []}, reverse=True):
            t_ = quando - _sz_td(minutes=m)
            if da < t_ <= adesso:
                out.append((v, sz_etichetta_anticipo(m), f"{base_k}|{m}"))
        rin = cfg.get("rinvio_al")
        if rin:
            try:
                tr = _sz_dt.fromisoformat(str(rin)[:16])
                if da < tr <= adesso:
                    out.append((v, "promemoria rinviato", f"{base_k}|rinvio|{str(rin)[:16]}"))
            except ValueError:
                pass
        if cfg.get("ripeti") and (sz.get("visto") or {}).get(v["chiave"]) != v["data"].isoformat() and v["data"] <= adesso.date():
            t_ = sz_quando(adesso.date(), ora_avv)
            if da < t_ <= adesso and quando < t_:
                out.append((v, "non ancora confermato", f"{base_k}|ripeti|{adesso.date().isoformat()}"))
    return out


def sz_testo_avviso(v, motivo, adesso):
    g = (v["data"] - adesso.date()).days
    q = "oggi" if g == 0 else "domani" if g == 1 else f"tra {g} giorni" if g > 0 else f"scaduta da {-g} giorni"
    righe = [f"⏰ Scadenziario: {v['titolo']}", f"📅 {v['data'].strftime('%d/%m/%Y')}" + (f" alle {v['ora']}" if v.get("ora") else "") + f" ({q})"]
    if v.get("importo"):
        righe.append(f"💶 {v['importo']:.2f} €".replace(".", ","))
    if v.get("descrizione"):
        righe.append(v["descrizione"][:200])
    righe.append(f"({motivo} · {SZ_CATEGORIE.get(v['categoria'], ('', ''))[1]})")
    return "\n".join(righe)


def sz_testo_riepilogo(voci, adesso, settimanale=False):
    """Il riepilogo quotidiano (o settimanale): oggi, appuntamenti, pagamenti, in ritardo, prossimi giorni. '' se non c'è niente."""
    oggi = adesso.date()
    aperte = [v for v in voci if v["stato"] not in ("Completata", "Annullata") and not v.get("solo_storico")]
    oggi_v = [v for v in aperte if v["data"] == oggi]
    ritardo = [v for v in aperte if v["stato"] == "Scaduta" and v["data"] < oggi]
    giorni = 7 if settimanale else 3
    prossimi = [v for v in aperte if 0 < (v["data"] - oggi).days <= giorni]
    if not (oggi_v or ritardo or prossimi):
        return ""
    fmt = lambda v: f"• {v['titolo']}" + (f" alle {v['ora']}" if v.get("ora") else "") + (f" — {v['importo']:.2f} €".replace(".", ",") if v.get("importo") else "")
    r = [("🗓️ Riepilogo della settimana" if settimanale else "☀️ Riepilogo di oggi") + f" — {oggi.strftime('%d/%m/%Y')}"]
    app = [v for v in oggi_v if v["categoria"] == "visite"]
    pag = [v for v in oggi_v if v["categoria"] == "pagamenti"]
    altro = [v for v in oggi_v if v not in app and v not in pag]
    if altro:
        r += ["", "✅ Da fare oggi:"] + [fmt(v) for v in altro[:12]]
    if app:
        r += ["", "📅 Appuntamenti di oggi:"] + [fmt(v) for v in app[:10]]
    if pag:
        r += ["", "💶 Da pagare oggi:"] + [fmt(v) for v in pag[:10]]
    if ritardo:
        r += ["", f"🔴 In ritardo ({len(ritardo)}):"] + [fmt(v) + f" (dal {v['data'].strftime('%d/%m')})" for v in ritardo[:10]]
    if prossimi:
        r += ["", f"🔜 Nei prossimi {giorni} giorni:"] + [f"• {v['data'].strftime('%d/%m')} {v['titolo']}" for v in prossimi[:15]]
    return "\n".join(r)


def sz_riepilogo_da_mandare(d, adesso, finestra_min=60):
    """[(testo, chiave_registro)]: il quotidiano all'ora scelta; il settimanale nel giorno scelto (0 = lunedì)."""
    sz = d.get("scadenziario") if isinstance(d.get("scadenziario"), dict) else {}
    rp = (sz.get("impostazioni") or {}).get("riepilogo") or {}
    if not rp.get("attivo") and not rp.get("settimanale"):
        return []
    o = sz_ora(rp.get("ora")) or "07:30"
    t_ = _sz_dt.combine(adesso.date(), _sz_time(int(o[:2]), int(o[3:5])))
    if not (adesso - _sz_td(minutes=finestra_min) < t_ <= adesso):
        return []
    voci = sz_raccogli(d, adesso)
    out = []
    if rp.get("settimanale") and adesso.weekday() == int(sz_num(rp.get("giorno")) or 0):
        tx = sz_testo_riepilogo(voci, adesso, settimanale=True)
        if tx:
            out.append((tx, f"scadriep|sett|{adesso.date().isoformat()}"))
    elif rp.get("attivo"):
        tx = sz_testo_riepilogo(voci, adesso)
        if tx:
            out.append((tx, f"scadriep|giorno|{adesso.date().isoformat()}"))
    return out


# =====================================================================================================================
# CALENDARIO DEL TELEFONO (.ics): gli avvisi suonano e vibrano anche ad app chiusa e senza internet
# =====================================================================================================================
def _sz_ics_txt(s):
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def sz_ics(voci, sz, adesso):
    ora_avv = (sz.get("impostazioni") or {}).get("ora_avvisi") or "09:00"
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VitaMemo//Scadenziario//IT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:VitaMemo Scadenziario",
             "X-WR-TIMEZONE:Europe/Rome"]
    stamp = adesso.strftime("%Y%m%dT%H%M%S")
    for v in voci:
        if v["stato"] in ("Completata", "Annullata") or v.get("solo_storico"):
            continue
        uid = _sz_re.sub(r"[^A-Za-z0-9]", "-", v["chiave"]) + "@vitamemo"
        righe += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}", f"SUMMARY:{_sz_ics_txt(v['titolo'])}"]
        if v.get("ora"):
            ini = sz_quando(v["data"], v["ora"])
            righe += [f"DTSTART;TZID=Europe/Rome:{ini.strftime('%Y%m%dT%H%M%S')}", f"DTEND;TZID=Europe/Rome:{(ini + _sz_td(minutes=30)).strftime('%Y%m%dT%H%M%S')}"]
        else:
            righe += [f"DTSTART;VALUE=DATE:{v['data'].strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(v['data'] + _sz_td(days=1)).strftime('%Y%m%d')}"]
        desc = " · ".join(x for x in (v.get("descrizione"), (f"{v['importo']:.2f} €" if v.get("importo") else ""), SZ_CATEGORIE.get(v["categoria"], ("", ""))[1]) if x)
        if desc:
            righe.append(f"DESCRIPTION:{_sz_ics_txt(desc)}")
        if v.get("personale") and v.get("rif"):
            p = next((x for x in sz.get("personali") or [] if x.get("id") == v["rif"].get("id")), {})
            t = (p.get("ricorrenza") or {}).get("tipo")
            n = int(sz_num((p.get("ricorrenza") or {}).get("ogni")) or 1)
            rr = {"giorno": "FREQ=DAILY", "giorni": f"FREQ=DAILY;INTERVAL={n}", "settimana": "FREQ=WEEKLY", "settimane": f"FREQ=WEEKLY;INTERVAL={n}", "mese": "FREQ=MONTHLY",
                  "mesi": f"FREQ=MONTHLY;INTERVAL={n}", "anno": "FREQ=YEARLY"}.get(t)
            if rr:
                righe.append("RRULE:" + rr)
        elif v["chiave"].startswith("compleanni:"):
            righe.append("RRULE:FREQ=YEARLY")
        cfg = sz_cfg_avvisi(sz, v)
        if cfg.get("attivi", True):
            base_min = 0 if v.get("ora") else -(int(ora_avv[:2]) * 60 + int(ora_avv[3:5]))   # evento di un giorno intero: gli avvisi all'ora degli avvisi
            for m in sorted({int(sz_num(x) or 0) for x in cfg.get("anticipi") or []}):
                tot = m + base_min
                trig = f"-PT{tot}M" if tot >= 0 else f"PT{-tot}M"
                righe += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_sz_ics_txt(v['titolo'])}", f"TRIGGER:{trig}", "END:VALARM"]
        righe.append("END:VEVENT")
    righe.append("END:VCALENDAR")
    return "\r\n".join(righe) + "\r\n"
