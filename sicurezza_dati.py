# -*- coding: utf-8 -*-
"""BACKUP, RIPRISTINO E SPAZIO — in Utilità, per ogni persona che usa l'app.
• «Fai il backup»: un file ZIP con TUTTO quello che la persona ha inserito (i suoi dati, le foto, i PDF, i messaggi). Se è grande viene diviso in più parti.
  L'app segna quando è stato fatto l'ultimo backup e avvisa se è passato troppo tempo.
• «Ripristina»: si carica il file ZIP e l'app rimette i dati. Prima di sostituire qualcosa salva da sola una copia di com'era adesso.
• «Spazio»: quanto spazio c'è, quanto se ne sta usando (grafico) e che cosa pesa di più.
• «Spazio in più»: i servizi cloud dove tenere le copie di backup (i più sicuri, noti ed economici), con i prezzi indicativi.
• Solo per l'amministratore: backup di TUTTA l'app (tutti gli utenti) e la lista di quello che va conservato per poter rimettere in piedi l'app.
Caricato da app_dispensa.py (aggiunge il riquadro in fondo a Utilità). Nomi con prefisso «bk_»."""
import io
import os
import re
import json
import zipfile
from datetime import datetime

import streamlit as st

BK_PARTE_MB = 40                         # ogni parte del backup contiene al massimo circa 40 MB di dati (così si scarica bene anche dal telefono)
BK_CONSIGLIATO = 1024 ** 3               # 1 GB: sotto questa misura l'archivio lavora al meglio (indicazione di GitHub)
BK_MASSIMO = 5 * 1024 ** 3               # 5 GB: da non superare (indicazione di GitHub)
BK_FILE_MAX = 100 * 1024 ** 2            # un singolo file non può superare 100 MB
BK_GIORNI_AVVISO = 30
_BK_PERCORSO_OK = re.compile(r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-\.]+)*\.json$")

BK_CLOUD = [   # (nome, gratis, a pagamento, perché, link) — prezzi indicativi rilevati a novembre 2026
    ("Proton Drive", "5 GB", "200 GB a 3,99 €/mese", "Il più riservato: i file sono cifrati sul tuo telefono prima di partire, nemmeno Proton li può leggere. Sede in Svizzera.", "https://proton.me/it/drive"),
    ("Google One (Google Drive)", "15 GB", "100 GB a 1,99 €/mese · 200 GB a 2,99 €/mese", "Il più comodo su Android: è già nel telefono. Il più economico per iniziare.", "https://one.google.com/about/plans?hl=it"),
    ("iCloud+ (Apple)", "5 GB", "50 GB a 0,99 €/mese · 200 GB a 2,99 €/mese", "Per chi ha iPhone o iPad: è già dentro il telefono.", "https://www.apple.com/it/icloud/"),
    ("Microsoft OneDrive", "5 GB", "100 GB a 2,00 €/mese", "Per chi usa Windows, Word ed Excel.", "https://www.microsoft.com/it-it/microsoft-365/onedrive/online-cloud-storage"),
    ("pCloud", "10 GB", "500 GB a 49,99 €/anno (oppure una volta sola, a vita)", "Sede in Svizzera, server in Europa. Si può pagare una volta sola invece che ogni mese.", "https://www.pcloud.com/it/"),
    ("MEGA", "20 GB", "400 GB a 4,99 €/mese", "Il più spazio gratuito. File cifrati sul tuo dispositivo.", "https://mega.io/it/pricing"),
    ("Dropbox", "2 GB", "2 TB a 11,99 €/mese", "Molto noto e affidabile, ma poco spazio gratuito e piani grandi.", "https://www.dropbox.com/it/plans"),
]


# ---------------------------------------------------------------------------------------------------------------------
# l'archivio: elenco dei file con il loro peso, lettura e scrittura
# ---------------------------------------------------------------------------------------------------------------------
def bk_uid():
    return str((st.session_state.get("sess") or {}).get("uid", "prova"))


def bk_admin():
    return bool((st.session_state.get("sess") or {}).get("admin"))


def bk_elenco(forza=False):
    """Tutti i file dell'archivio con il loro peso: [(percorso, byte)]. Si tiene in memoria per 5 minuti. Ritorna (elenco, avviso)."""
    ss = st.session_state
    mem = ss.get("bk_elenco_mem")
    if mem and not forza and (datetime.now() - mem["quando"]).total_seconds() < 300:
        return mem["elenco"], mem["avviso"]
    arch = crea_archivio()
    elenco, avviso = [], ""
    try:
        if getattr(arch, "permanente", False) and hasattr(arch, "intest"):
            def chiedi(rif):
                return arch.http.get(f"https://api.github.com/repos/{arch.repo}/git/trees/{rif}", headers=arch.intest, params={"recursive": "1"}, timeout=40)
            r = chiedi(arch.ramo or "HEAD")
            if r.status_code in (404, 409, 422) and not arch.ramo:
                info = arch.http.get(f"https://api.github.com/repos/{arch.repo}", headers=arch.intest, timeout=20)
                if info.status_code == 200:
                    r = chiedi(info.json().get("default_branch") or "main")
            if r.status_code == 409:                                  # archivio ancora vuoto
                elenco = []
            else:
                r.raise_for_status()
                j = r.json()
                elenco = [(x["path"], int(x.get("size") or 0)) for x in j.get("tree", []) if x.get("type") == "blob"]
                if j.get("truncated"):
                    avviso = "L'archivio è molto grande: l'elenco dei file potrebbe non essere completo."
        else:
            base = getattr(arch, "cartella", "dati_locali")
            for cart, _sotto, nomi in os.walk(base):
                for n in nomi:
                    p = os.path.join(cart, n)
                    elenco.append((os.path.relpath(p, base).replace(os.sep, "/"), os.path.getsize(p)))
            avviso = "" if getattr(arch, "permanente", False) else "⚠️ L'app sta salvando in una cartella provvisoria (non su GitHub): i dati si perdono al riavvio."
    except Exception as e:
        return [], f"Non sono riuscito a leggere l'elenco dei file ({type(e).__name__}). Riprova tra poco."
    ss["bk_elenco_mem"] = {"quando": datetime.now(), "elenco": elenco, "avviso": avviso}
    return elenco, avviso


def bk_e_mio(percorso, uid):
    return percorso == f"dispense/{uid}.json" or percorso.startswith(f"documenti/{uid}/") or percorso == f"posta/{uid}.json"


def bk_leggi(percorso):
    """Il contenuto di un file dell'archivio (così com'è salvato), in byte."""
    return json.dumps(crea_archivio().leggi(percorso), ensure_ascii=False).encode("utf-8")


def bk_scrivi(percorso, contenuto, messaggio):
    def _fn(d, nuovo=contenuto):
        d.clear()
        d.update(nuovo)
    crea_archivio().modifica(percorso, _fn, messaggio)


def bk_peso(n):
    n = float(n or 0)
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB".replace(".", ",")
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.1f} MB".replace(".", ",")
    return f"{max(1, round(n / 1024))} KB" if n else "0 KB"


# ---------------------------------------------------------------------------------------------------------------------
# quando è stato fatto l'ultimo backup
# ---------------------------------------------------------------------------------------------------------------------
def bk_stato():
    try:
        d = carica_dati(crea_archivio(), f"dispense/{bk_uid()}.json")
        return dict((d.get("impostazioni") or {}).get("backup") or {})
    except Exception:
        return {}


def bk_segna(tipo, n_file, n_byte, parte, parti):
    voce = {"il": datetime.now().isoformat(timespec="seconds"), "tipo": tipo, "file": n_file, "byte": n_byte, "parte": parte, "parti": parti}

    def _fn(d, v=voce):
        b = d.setdefault("impostazioni", {}).setdefault("backup", {})
        b["ultimo"] = v
        b["storia"] = ([v] + list(b.get("storia") or []))[:10]
    try:
        salva_file(f"dispense/{bk_uid()}.json", _fn, "Backup: segnato quando è stato fatto")
    except Exception:
        pass


def bk_quanto_fa(iso):
    try:
        g = (datetime.now() - datetime.fromisoformat(iso)).days
    except Exception:
        return None, ""
    return g, ("oggi" if g <= 0 else "ieri" if g == 1 else f"{g} giorni fa")


# ---------------------------------------------------------------------------------------------------------------------
# fare il backup
# ---------------------------------------------------------------------------------------------------------------------
def bk_parti(file_e_peso):
    """Divide i file in parti da circa BK_PARTE_MB. I dati principali (dispense/…) stanno sempre nella prima parte."""
    ordinati = sorted(file_e_peso, key=lambda x: (0 if x[0].startswith("dispense/") or "/" not in x[0] else 1, x[0]))
    parti, corrente, peso = [], [], 0
    for p, n in ordinati:
        if corrente and peso + n > BK_PARTE_MB * 1024 ** 2:
            parti.append(corrente)
            corrente, peso = [], 0
        corrente.append((p, n))
        peso += n
    if corrente:
        parti.append(corrente)
    return parti


def bk_crea_zip(tipo, file_e_peso, parte, parti, barra=None):
    """Costruisce una parte del backup. Ritorna (byte dello zip, file non letti)."""
    sess = st.session_state.get("sess") or {}
    buf, saltati = io.BytesIO(), []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        manifest = {"app": "VitaMemo", "versione": 1, "tipo": tipo, "uid": bk_uid(), "nome": sess.get("nome", ""), "creato": datetime.now().isoformat(timespec="seconds"),
                    "parte": parte, "parti": parti, "file": [p for p, _n in file_e_peso]}
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        z.writestr("LEGGIMI.txt", "Backup di VitaMemo.\nNon aprire e non modificare i file: per rimettere i dati apri l'app, vai in Utilità → Backup, ripristino e spazio → Ripristina, e carica questo file ZIP"
                   + (f" insieme alle altre parti (questa è la {parte} di {parti})." if parti > 1 else ".") + "\nContiene dati personali: tienilo in un posto sicuro.\n")
        for i, (p, _n) in enumerate(file_e_peso):
            try:
                z.writestr(p, bk_leggi(p))
            except Exception:
                saltati.append(p)
            if barra is not None:
                barra.progress((i + 1) / max(1, len(file_e_peso)), text=f"Copio i file… {i + 1} di {len(file_e_peso)}")
    return buf.getvalue(), saltati


def bk_ui_backup(elenco):
    uid = bk_uid()
    stato = bk_stato()
    ultimo = stato.get("ultimo") or {}
    giorni, fa = bk_quanto_fa(ultimo.get("il", ""))
    if not ultimo:
        st.warning("🛟 **Non hai ancora fatto nessun backup.** Farlo richiede un minuto e ti mette al sicuro.")
    elif giorni is not None and giorni >= BK_GIORNI_AVVISO:
        st.warning(f"🛟 L'ultimo backup è di **{fa}** ({datetime.fromisoformat(ultimo['il']).strftime('%d/%m/%Y %H:%M')}). È ora di rifarlo.")
    else:
        st.success(f"🛟 Ultimo backup: **{datetime.fromisoformat(ultimo['il']).strftime('%d/%m/%Y alle %H:%M')}** ({fa}) · {ultimo.get('file', 0)} file · {bk_peso(ultimo.get('byte'))}"
                   + (f" · parte {ultimo.get('parte')} di {ultimo.get('parti')}" if (ultimo.get("parti") or 1) > 1 else ""))
    scelte = {"miei": "👤 I miei dati (tutto quello che ho inserito io)"}
    if bk_admin():
        scelte["tutto"] = "🏠 Tutta l'app: i dati di tutti gli utenti (solo amministratore)"
    tipo = st.radio("Di che cosa", list(scelte), format_func=lambda k: scelte[k], key="bk_tipo", label_visibility="collapsed") if len(scelte) > 1 else "miei"
    miei = [(p, n) for p, n in elenco if (tipo == "tutto" and _BK_PERCORSO_OK.match(p)) or (tipo == "miei" and bk_e_mio(p, uid))]
    if not miei:
        st.info("Non c'è ancora niente da salvare.")
        return
    parti = bk_parti(miei)
    tot = sum(n for _p, n in miei)
    st.caption(f"Da salvare: **{len(miei)} file**, {bk_peso(tot)}" + (f" → divisi in **{len(parti)} parti** (una alla volta, così si scaricano bene)." if len(parti) > 1 else "."))
    for i, gruppo in enumerate(parti, 1):
        etichetta = "🛟 Fai il backup adesso" if len(parti) == 1 else f"🛟 Prepara la parte {i} di {len(parti)} ({bk_peso(sum(n for _p, n in gruppo))})"
        if st.button(etichetta, key=f"bk_fai_{tipo}_{i}", type="primary" if i == 1 else "secondary", width="stretch"):
            barra = st.progress(0.0, text="Copio i file…")
            dati_zip, saltati = bk_crea_zip("utente" if tipo == "miei" else "completo", gruppo, i, len(parti), barra)
            barra.empty()
            nome = f"VitaMemo_backup_{'miei_dati' if tipo == 'miei' else 'tutta_app'}_{datetime.now().strftime('%Y-%m-%d_%H%M')}" + (f"_parte{i}di{len(parti)}" if len(parti) > 1 else "") + ".zip"
            st.session_state["bk_pronto"] = {"nome": nome, "dati": dati_zip, "saltati": saltati, "tipo": tipo, "parte": i}
            bk_segna("utente" if tipo == "miei" else "completo", len(gruppo) - len(saltati), sum(n for _p, n in gruppo), i, len(parti))
            st.rerun()                                           # ridisegno: in alto compare subito «Ultimo backup: oggi…» e sotto il tasto per scaricarlo
    pronto = st.session_state.get("bk_pronto")
    if pronto and pronto.get("tipo") == tipo:
        if pronto["saltati"]:
            st.warning(f"⚠️ {len(pronto['saltati'])} file non sono stati letti (riprova tra poco): " + ", ".join(pronto["saltati"][:3]))
        st.download_button(f"⬇️ Scarica {pronto['nome']} ({bk_peso(len(pronto['dati']))})", pronto["dati"], file_name=pronto["nome"], mime="application/zip", key="bk_scarica", width="stretch", type="primary")
        st.caption("Dopo averlo scaricato lo trovi nella cartella **Download**. Mettine una copia anche **fuori dal telefono** (vedi «Dove tenere i backup» qui sotto).")


# ---------------------------------------------------------------------------------------------------------------------
# ripristinare
# ---------------------------------------------------------------------------------------------------------------------
def bk_apri_zip(caricati):
    """Legge uno o più file ZIP di backup. Ritorna (manifest, {percorso: contenuto}, errori)."""
    manifest, file_, errori = None, {}, []
    for c in caricati:
        try:
            z = zipfile.ZipFile(io.BytesIO(c.getvalue()))
            m = json.loads(z.read("manifest.json").decode("utf-8"))
            if m.get("app") != "VitaMemo":
                errori.append(f"«{c.name}» non è un backup di VitaMemo.")
                continue
            if manifest and (manifest.get("uid") != m.get("uid") or manifest.get("tipo") != m.get("tipo")):
                errori.append(f"«{c.name}» è di un altro backup: carica solo le parti dello stesso backup.")
                continue
            if not manifest or str(m.get("creato", "")) > str(manifest.get("creato", "")):
                manifest = dict(m, parti_caricate=(manifest or {}).get("parti_caricate", []))
            manifest.setdefault("parti_caricate", []).append(m.get("parte", 1))
            if sum(i.file_size for i in z.infolist()) > 700 * 1024 ** 2:
                errori.append(f"«{c.name}» è troppo grande per essere ripristinato da qui.")
                continue
            for info in z.infolist():
                p = info.filename
                if p in ("manifest.json", "LEGGIMI.txt") or p.endswith("/"):
                    continue
                if not _BK_PERCORSO_OK.match(p) or ".." in p or info.file_size > BK_FILE_MAX:
                    errori.append(f"File non valido nel backup, lo salto: {p[:60]}")
                    continue
                try:
                    file_[p] = json.loads(z.read(p).decode("utf-8"))
                except Exception:
                    errori.append(f"File rovinato nel backup, lo salto: {p[:60]}")
        except Exception:
            errori.append(f"«{getattr(c, 'name', 'file')}» non si apre: non è un file ZIP di backup valido.")
    return manifest, file_, errori


def bk_ui_ripristino(elenco):
    st.caption("Serve se i dati sono andati persi o rovinati. Carica il file ZIP del backup (se era diviso in parti, caricale tutte insieme).")
    caricati = st.file_uploader("File ZIP del backup", type=["zip"], accept_multiple_files=True, key="bk_carica", label_visibility="collapsed")
    if not caricati:
        return
    manifest, file_, errori = bk_apri_zip(caricati)
    for e in errori[:5]:
        st.warning("⚠️ " + e)
    if not manifest or not file_:
        st.error("In questo file non ho trovato dati da ripristinare.")
        return
    uid = bk_uid()
    completo = manifest.get("tipo") == "completo"
    if completo and not bk_admin():
        st.error("Questo è un backup di tutta l'app: lo può ripristinare solo l'amministratore.")
        return
    if not completo:
        if manifest.get("uid") != uid and not bk_admin():
            st.error("Questo backup è di un'altra persona: puoi ripristinare solo i tuoi backup.")
            return
        file_ = {p: c for p, c in file_.items() if bk_e_mio(p, str(manifest.get("uid")))}
    try:
        quando = datetime.fromisoformat(manifest.get("creato", "")).strftime("%d/%m/%Y alle %H:%M")
    except Exception:
        quando = "data sconosciuta"
    attese, avute = int(manifest.get("parti") or 1), sorted(set(manifest.get("parti_caricate") or [1]))
    st.info(f"📦 Backup del **{quando}** · {'tutta l’app' if completo else 'dati di ' + (manifest.get('nome') or manifest.get('uid', ''))} · **{len(file_)} file**"
            + (f" · parti caricate: {', '.join(str(x) for x in avute)} su {attese}" if attese > 1 else ""))
    if attese > 1 and len(avute) < attese:
        st.warning(f"⚠️ Mancano delle parti (ne hai caricate {len(avute)} su {attese}): posso rimettere solo quello che c'è in queste. Meglio caricarle tutte.")
    esistenti = {p for p, _n in elenco}
    mancanti = [p for p in file_ if p not in esistenti]
    modi = {"mancanti": f"🧩 Rimetti solo quello che manca ({len(mancanti)} file) — non tocca niente di quello che c'è adesso (consigliato)",
            "tutto": f"⏪ Riporta tutto com'era nel backup ({len(file_)} file) — SOSTITUISCE i dati di adesso con quelli del backup"}
    modo = st.radio("Come ripristinare", list(modi), format_func=lambda k: modi[k], key="bk_modo")
    da_scrivere = mancanti if modo == "mancanti" else list(file_)
    if modo == "tutto":
        st.warning("⚠️ Quello che hai inserito **dopo** il backup verrà sostituito. Prima di farlo, salvo da sola una copia di com'è adesso (cartella «backup_auto» dell'archivio).")
    if not da_scrivere:
        st.success("✅ Non manca niente: tutti i file del backup ci sono già.")
        return
    capito = st.checkbox("Ho capito, procedi", key="bk_capito")
    if st.button(f"♻️ Ripristina {len(da_scrivere)} file", key="bk_ripristina", type="primary", width="stretch", disabled=not capito):
        barra = st.progress(0.0, text="Ripristino…")
        marca, falliti = datetime.now().strftime("%Y%m%d_%H%M%S"), []
        for i, p in enumerate(da_scrivere):
            try:
                if modo == "tutto" and p in esistenti and (p.startswith("dispense/") or "/" not in p):      # copia di sicurezza dei dati principali che sto per sostituire
                    adesso_ = crea_archivio().leggi(p)
                    if adesso_:
                        bk_scrivi(f"backup_auto/{marca}/{p.replace('/', '__')}", adesso_, "Copia automatica prima del ripristino")
                bk_scrivi(p, file_[p], "Ripristino da backup")
            except Exception:
                falliti.append(p)
            barra.progress((i + 1) / len(da_scrivere), text=f"Ripristino… {i + 1} di {len(da_scrivere)}")
        barra.empty()
        try:
            carica_dati.clear()
        except Exception:
            pass
        st.session_state.pop("bk_elenco_mem", None)
        st.session_state["bk_esito"] = (len(da_scrivere) - len(falliti), falliti[:5])
        st.rerun()


# ---------------------------------------------------------------------------------------------------------------------
# lo spazio: quanto ce n'è, quanto se ne usa, che cosa pesa
# ---------------------------------------------------------------------------------------------------------------------
_BK_CSS = """<style>
.st-key-bk_riquadro [role="tablist"]{position:relative !important;left:0 !important;right:auto !important;bottom:auto !important;top:auto !important;transform:none !important;width:100% !important;
 flex-wrap:wrap;overflow:visible !important;border-radius:16px;box-shadow:none !important;margin:0 0 10px;padding:4px !important;z-index:1}
.st-key-bk_riquadro [data-baseweb="tab-highlight"],.st-key-bk_riquadro [data-baseweb="tab-border"]{display:none !important}
.bk-barra{position:relative;height:30px;border-radius:15px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.25);overflow:hidden;margin:6px 0 2px}
.bk-barra>span{display:block;height:100%;float:left}
.bk-scala{display:flex;justify-content:space-between;font-size:.78rem;opacity:.85;margin-bottom:8px}
.bk-leg{display:grid;grid-template-columns:14px 1fr auto;gap:4px 8px;align-items:center;font-size:.92rem;margin:6px 0 10px}
.bk-leg i{width:14px;height:14px;border-radius:4px;display:block}
.bk-num{font-size:1.5rem;font-weight:800;line-height:1.2}
.bk-riga{display:grid;grid-template-columns:minmax(90px,34%) 1fr auto;gap:8px;align-items:center;font-size:.9rem;margin:3px 0}
.bk-riga div.b{height:12px;border-radius:6px;background:rgba(255,255,255,.10);overflow:hidden}
.bk-riga div.b>span{display:block;height:100%;border-radius:6px}
.bk-cloud{border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:10px 12px;margin:8px 0;background:rgba(255,255,255,.05)}
.bk-cloud b{font-size:1rem}.bk-cloud small{opacity:.9;line-height:1.45;display:block;margin-top:2px}
</style>"""
_BK_COLORI = ["#4aa3ff", "#2ecc71", "#f5a623", "#b388ff", "#ff6b6b", "#26c6da", "#ffd54f", "#90a4ae"]


def bk_categorie(elenco, uid):
    """I miei file divisi per tipo: [(nome, byte)]."""
    dati = sum(n for p, n in elenco if p == f"dispense/{uid}.json" or p == f"posta/{uid}.json")
    letture = sum(n for p, n in elenco if p.startswith(f"documenti/{uid}/lett"))
    foto = sum(n for p, n in elenco if p.startswith(f"documenti/{uid}/")) - letture
    return [("📷 Foto, PDF e documenti allegati", foto), ("📝 Dati scritti (schede, elenchi, messaggi)", dati), ("🔍 Letture dello scritto", letture)]


def bk_per_utente(elenco):
    """Tutta l'app divisa per utente (per l'amministratore): [(nome, byte)]."""
    try:
        utenti = {u.get("id"): u.get("nome", u.get("id")) for u in (carica_dati(crea_archivio(), "utenti.json").get("utenti") or [])}
    except Exception:
        utenti = {}
    pesi = {}
    for p, n in elenco:
        m = re.match(r"^(?:dispense/([^/]+)\.json|documenti/([^/]+)/|posta/([^/]+)\.json)", p)
        chi = (m.group(1) or m.group(2) or m.group(3)) if m else "__altro__"
        pesi[chi] = pesi.get(chi, 0) + n
    nomi = lambda k: "⚙️ Dati comuni dell'app (famiglia, chat, impostazioni)" if k == "__altro__" else "👤 " + str(nome_admin() if k == "admin" and "nome_admin" in globals() else utenti.get(k, k))
    return sorted(((nomi(k), v) for k, v in pesi.items()), key=lambda x: -x[1])


def bk_ui_spazio(elenco, avviso):
    uid = bk_uid()
    tot = sum(n for _p, n in elenco)
    mio = sum(n for p, n in elenco if bk_e_mio(p, uid))
    perc = 100.0 * tot / BK_CONSIGLIATO
    colore = "#2ecc71" if perc < 60 else "#f5a623" if perc < 100 else "#ff5a5a"
    st.markdown(_BK_CSS, unsafe_allow_html=True)
    if avviso:
        st.warning(avviso)
    st.markdown(f"<div class='bk-num'>{bk_peso(tot)} usati su 1 GB <span style='font-size:.95rem;font-weight:600;opacity:.9'>({str(round(perc, 1)).replace('.', ',')}%)</span></div>", unsafe_allow_html=True)
    altri = max(0, tot - mio)
    w_mio, w_altri = min(100.0, 100.0 * mio / BK_CONSIGLIATO), min(100.0, 100.0 * altri / BK_CONSIGLIATO)
    w_altri = min(w_altri, 100.0 - w_mio)
    st.markdown(f"<div class='bk-barra'><span style='width:{max(w_mio, 0.6 if mio else 0):.2f}%;background:#4aa3ff'></span><span style='width:{max(w_altri, 0.6 if altri else 0):.2f}%;background:#b388ff'></span></div>"
                f"<div class='bk-scala'><span>0</span><span>250 MB</span><span>500 MB</span><span>750 MB</span><span>1 GB</span></div>"
                f"<div class='bk-leg'><i style='background:#4aa3ff'></i><span>I miei dati</span><b>{bk_peso(mio)}</b>"
                f"<i style='background:#b388ff'></i><span>{'Gli altri utenti e i dati comuni' if altri else 'Altri'}</span><b>{bk_peso(altri)}</b>"
                f"<i style='background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35)'></i><span>Ancora libero (fino a 1 GB)</span><b>{bk_peso(max(0, BK_CONSIGLIATO - tot))}</b></div>", unsafe_allow_html=True)
    if perc >= 100:
        st.error("🔴 Hai superato 1 GB: l'app funziona ancora, ma può rallentare. Conviene alleggerire (vedi i suggerimenti) — il limite da non superare mai è 5 GB.")
    elif perc >= 60:
        st.warning("🟠 Stai usando più della metà dello spazio consigliato: tieni d'occhio le foto più pesanti.")
    else:
        st.markdown(f"<div style='color:{colore};font-weight:700;margin:-4px 0 6px'>🟢 C'è tanto spazio libero.</div>", unsafe_allow_html=True)

    def righe(voci, titolo):
        massimo = max([v for _n, v in voci] + [1])
        st.markdown(f"**{titolo}**")
        st.markdown("".join(f"<div class='bk-riga'><span>{n}</span><div class='b'><span style='width:{100.0 * v / massimo:.1f}%;background:{_BK_COLORI[i % len(_BK_COLORI)]}'></span></div><b>{bk_peso(v)}</b></div>"
                            for i, (n, v) in enumerate(voci)), unsafe_allow_html=True)
    righe(bk_categorie(elenco, uid), "Che cosa pesa nei miei dati")
    if bk_admin():
        righe(bk_per_utente(elenco)[:12], "Chi occupa lo spazio (lo vedi solo tu, amministratore)")
    pesanti = sorted(((p, n) for p, n in elenco if bk_e_mio(p, uid) and p.startswith("documenti/")), key=lambda x: -x[1])[:1]
    st.caption("**Quanto spazio c'è.** I dati dell'app stanno in un archivio privato su GitHub, **gratuito**. Non c'è un contatore che blocca: GitHub chiede di restare "
               "**sotto 1 GB** (ideale) e comunque **sotto 5 GB**; un singolo file non può superare **100 MB**. "
               + (f"Il tuo file più pesante è di {bk_peso(pesanti[0][1])}. " if pesanti else "")
               + "Una foto fatta col telefono occupa in media 0,3–1 MB: in 1 GB ce ne stanno più di mille.")
    if st.button("🔄 Ricalcola lo spazio", key="bk_ricalcola"):
        st.session_state.pop("bk_elenco_mem", None)
        st.rerun()
    bk_ui_orfani(elenco)


def bk_cerca_orfani(elenco, uid):
    """I miei file in documenti/ che nessun dato usa più (foto di prodotti eliminati, vecchie foto sostituite…). Si cerca il loro nome in TUTTI i dati dell'app
    (anche degli altri, perché un file può essere condiviso) e nei file piccoli che fanno da elenco. Ritorna [(percorso, byte)]."""
    arch = crea_archivio()
    leggi_g = getattr(arch, "leggi_grezzo", arch.leggi)
    miei = [(p, n) for p, n in elenco if p.startswith(f"documenti/{uid}/") and p.endswith(".json")]
    testi = []
    for p, n in elenco:
        if not p.endswith(".json"):
            continue
        if p.startswith("documenti/") and n > 40000:
            continue                                            # i file grandi sono foto o PDF: non contengono riferimenti
        try:
            testi.append(json.dumps(leggi_g(p), ensure_ascii=False))
        except Exception:
            return None                                         # se non riesco a leggere tutto, non segnalo niente (meglio non rischiare)
    tutto = "\n".join(testi)
    return [(p, n) for p, n in miei if p.rsplit("/", 1)[-1][:-5] not in tutto]


def bk_ui_orfani(elenco):
    uid = bk_uid()
    st.markdown("**🧹 File non più usati**")
    st.caption("Foto e documenti che l'app non usa più (per esempio la foto di un prodotto eliminato). Prima scarichi una copia, poi puoi eliminarli.")
    if st.button("🔎 Cerca i file non più usati", key="bk_orf_cerca", width="stretch"):
        with st.spinner("Controllo tutti i dati… (può volerci qualche secondo)"):
            st.session_state["bk_orfani"] = bk_cerca_orfani(elenco, uid)
        st.session_state["bk_orf_scaricati"] = False
    orf = st.session_state.get("bk_orfani")
    if orf is None and "bk_orfani" in st.session_state:
        st.warning("Non sono riuscito a leggere tutti i dati: per sicurezza non ti segnalo niente. Riprova più tardi.")
        return
    if not orf:
        if "bk_orfani" in st.session_state:
            st.success("✅ Nessun file inutile: è tutto in ordine.")
        return
    peso = sum(n for _p, n in orf)
    st.info(f"Ho trovato {len(orf)} file non più usati, per {bk_peso(peso)}.")
    zip_b, _salt = bk_crea_zip("non_usati", orf, 1, 1)
    st.download_button("⬇️ 1 · Scarica una copia di sicurezza (ZIP)", zip_b, file_name=f"vitamemo_file_non_usati_{datetime.now():%Y%m%d}.zip", mime="application/zip",
                       key="bk_orf_zip", width="stretch", on_click=lambda: st.session_state.__setitem__("bk_orf_scaricati", True))
    if not st.session_state.get("bk_orf_scaricati"):
        st.caption("Dopo aver scaricato la copia compare il tasto per eliminarli.")
        return
    if st.button(f"🗑️ 2 · Elimina questi {len(orf)} file", key="bk_orf_elim", type="primary", width="stretch"):
        barra = st.progress(0.0, text="Elimino…")
        arch, fatti = crea_archivio(), 0
        for i, (p, _n) in enumerate(orf):
            try:
                arch.elimina(p, "File non più usato")
                fatti += 1
            except Exception:
                pass
            barra.progress((i + 1) / len(orf), text=f"Elimino… {i + 1} di {len(orf)}")
        st.session_state.pop("bk_orfani", None)
        st.session_state.pop("bk_elenco_mem", None)
        st.success(f"Fatto: eliminati {fatti} file ({bk_peso(peso)} liberati).")


def bk_ui_cloud():
    st.markdown(_BK_CSS, unsafe_allow_html=True)
    st.info("**Da sapere prima di comprare.** Lo spazio dell'app è gratuito e **non si compra**: se un giorno non bastasse, si alleggerisce l'archivio. "
            "Lo spazio qui sotto serve a un'altra cosa, altrettanto importante: **tenere al sicuro le copie di backup** fuori dal telefono. "
            "Un backup pesa poco: quasi sempre **basta lo spazio gratuito**.")
    st.caption("In ordine: prima i più sicuri e riservati, poi i più comodi ed economici. Prezzi indicativi rilevati a novembre 2026: controlla sempre sul sito prima di pagare.")
    for nome, gratis, paga, perche, link in BK_CLOUD:
        st.markdown(f"<div class='bk-cloud'><b>{nome}</b><small>🆓 Gratis: <b>{gratis}</b> · 💶 {paga}<br>{perche}</small></div>", unsafe_allow_html=True)
        st.link_button(f"Apri {nome}", link, width="stretch")


def bk_ui_suggerimenti():
    st.markdown("""
- **Ogni quanto:** una volta al mese, e sempre dopo aver caricato molti documenti. Se passano 30 giorni l'app te lo ricorda qui.
- **Regola del 3-2-1:** tieni il backup in **due posti diversi**, di cui **uno fuori casa** (per esempio: sul telefono e su Google Drive o Proton Drive).
- **Non lasciarlo solo sul telefono:** se il telefono si rompe o si perde, perdi anche il backup. Dopo averlo scaricato, caricalo sul cloud o mandalo alla tua email.
- **È un file riservato:** dentro ci sono dati personali e sanitari. Non mandarlo su chat di gruppo e non lasciarlo su computer di altri.
- **Non aprirlo e non rinominare i file dentro:** serve solo all'app. Per avere documenti da leggere usa invece «📤 Esporta» (PDF o ZIP).
- **Tieni gli ultimi 2 o 3:** cancella i più vecchi, ma non restare mai con uno solo.
- **Prova il ripristino una volta:** carica il backup in «Ripristina» e scegli «Rimetti solo quello che manca»: se dice che non manca niente, il backup è buono.
- **Se è diviso in parti:** scaricale tutte e tienile insieme nella stessa cartella.
- **Per occupare meno spazio:** fotografa i documenti senza zoom e senza flash, usa «🧹 Doppi» nei documenti per togliere le foto salvate due volte, ed elimina ciò che non serve più (resta 30 giorni nel Cestino).
""")


def bk_ui_admin():
    st.markdown("""
Se un giorno dovessi rimettere in piedi l'app da zero (telefono perso, account bloccato), servono **queste cose**. Conservale **fuori dall'app**, su carta o in un gestore di password: **qui non vengono mostrate**.

**1. Gli accessi**
- **GitHub:** nome utente, password e i **codici di recupero** della verifica in due passaggi (Settings → Password and authentication → Recovery codes).
- **Streamlit:** l'account con cui entri su share.streamlit.io (di solito è lo stesso di GitHub).
- L'**indirizzo dell'app** (quello che finisce con .streamlit.app).

**2. I due archivi su GitHub**
- **`dispensa`**: il programma. È pubblico su GitHub: basta sapere che c'è.
- **`dispensa-dati`**: i dati di tutti (privato). È la cosa più preziosa: il «backup di tutta l'app» qui sopra ne fa una copia.

**3. I «Secrets» di Streamlit** (share.streamlit.io → la tua app → ⋮ → Settings → Secrets). Copia **tutto il testo** e conservalo: senza, l'app non parte.
- `[github]` token, repo, branch — la chiave per leggere e scrivere i dati.
- `admin_password`, `admin_nome` — il tuo accesso.
- `pepper` — serve a riconoscere le password degli utenti. **Se la perdi o la cambi, nessun utente riesce più a entrare** (se non c'è la riga `pepper`, al suo posto vale `admin_password`: allora è quella che non va cambiata alla leggera).
- `EMAIL_USER`, `EMAIL_PASSWORD` (ed eventuali `EMAIL_SMTP`, `EMAIL_PORT`) — per gli avvisi e gli invii per email.
- `TELEGRAM_TOKEN` — il bot degli avvisi.
- Le chiavi dell'intelligenza artificiale che hai messo (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`).
- `paypal_me` oppure `[paypal]` client_id, secret, mode — le donazioni.

**4. I «Secrets» di GitHub per i promemoria automatici** (repository `dispensa` → Settings → Secrets and variables → Actions): `DATI_REPO`, `DATI_TOKEN`, `EMAIL_USER`, `EMAIL_PASSWORD`, `TELEGRAM_TOKEN` e, se usi gli SMS, `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM`.

**5. Gli altri account collegati:** la casella email degli avvisi, il bot Telegram (@BotFather), PayPal, i siti dove hai creato le chiavi dell'intelligenza artificiale.

**6. I backup:** l'ultimo «backup di tutta l'app», in due posti diversi.
""")


# ---------------------------------------------------------------------------------------------------------------------
# il riquadro in Utilità
# ---------------------------------------------------------------------------------------------------------------------
def bk_pannello():
    esito = st.session_state.pop("bk_esito", None)
    if esito:
        (st.success if not esito[1] else st.warning)(f"♻️ Ripristino fatto: {esito[0]} file rimessi." + (f" Non riusciti: {', '.join(esito[1])}. Riprova." if esito[1] else " Controlla che sia tutto a posto."))
    elenco, avviso = bk_elenco()
    schede = ["🛟 Backup", "♻️ Ripristina", "📊 Spazio", "💡 Suggerimenti", "☁️ Dove tenere i backup"] + (["🔐 Cosa conservare"] if bk_admin() else [])
    tab = st.tabs(schede)
    with tab[0]:
        if avviso and not elenco:
            st.warning(avviso)
        bk_ui_backup(elenco)
    with tab[1]:
        bk_ui_ripristino(elenco)
    with tab[2]:
        bk_ui_spazio(elenco, avviso)
    with tab[3]:
        bk_ui_suggerimenti()
    with tab[4]:
        bk_ui_cloud()
    if bk_admin():
        with tab[5]:
            bk_ui_admin()


def _bk_alterna():
    st.session_state["bk_aperto"] = not st.session_state.get("bk_aperto", False)


def bk_blocco_utilita():
    """Backup, ripristino e spazio: riquadro «Sicurezza dei tuoi dati» della pagina Utilità (utilita.py)."""
    if True:
        try:
            stato = bk_stato().get("ultimo") or {}
            giorni, _fa = bk_quanto_fa(stato.get("il", ""))
            da_fare = not stato or (giorni is not None and giorni >= BK_GIORNI_AVVISO)
            aperto = bool(st.session_state.get("bk_aperto"))       # un pulsante che apre e chiude (non una linguetta): così resta aperto mentre lo usi
            st.button(("✖ Chiudi «Backup, ripristino e spazio»" if aperto else "🛟 Backup, ripristino e spazio" + (" · ⚠️ backup da fare" if da_fare else "")),
                      key="bk_apri", width="stretch", type="secondary" if aperto else "primary", on_click=_bk_alterna)
            if aperto:
                with st.container(border=True, key="bk_riquadro"):
                    bk_pannello()
        except Exception as ex:
            st.warning(f"Il riquadro del backup non è disponibile ({type(ex).__name__}).")
