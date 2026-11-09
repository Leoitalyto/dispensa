

# =====================================================================
# PARTE 2 - ARCHIVIO DEI DATI E ACCESSO CON PASSWORD
# =====================================================================
class Conflitto(Exception):
    pass


class ArchivioLocale:
    """File accanto all'app. ATTENZIONE: su Streamlit Cloud si cancellano quando l'app si riavvia."""
    permanente = False

    def __init__(self, cartella):
        self.cartella = cartella

    def _percorso(self, nome):
        return os.path.join(self.cartella, *nome.split("/"))

    def leggi(self, nome):
        try:
            with open(self._percorso(nome), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def modifica(self, nome, fn, messaggio=""):
        dati = self.leggi(nome)
        fn(dati)
        percorso = self._percorso(nome)
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(percorso), encoding="utf-8") as tmp:
            json.dump(dati, tmp, ensure_ascii=False)
        os.replace(tmp.name, percorso)
        return dati

    def elimina(self, nome, messaggio=""):
        try:
            os.remove(self._percorso(nome))
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------------------------------------------------
# MEMORIA DELLE LETTURE E DELLE SCRITTURE (velocità): prima ogni salvataggio faceva 3 richieste a GitHub (leggere, scrivere, rileggere per ridisegnare la pagina) e ogni file
# nuovo ne faceva 2 (una lettura che dava «non esiste» e la scrittura). Ora si ricorda l'ultimo contenuto e la sua impronta («sha»): il salvataggio parte subito con la scrittura
# (se nel frattempo qualcuno ha cambiato il file GitHub risponde «conflitto» e si rilegge, come sempre: i dati sono al sicuro) e dopo aver scritto non serve rileggere.
# Solo file piccoli (i dati), per poco tempo (60 secondi, come la memoria delle letture); i file grandi (foto, PDF) non si tengono in memoria. Si spegne con ARCHIVIO_VELOCE = "no".
# ---------------------------------------------------------------------------------------------------------------------
import copy as _gh_copy
import threading as _gh_thr
@st.cache_resource
def _gh_memoria_globale():
    """La memoria è UNA per tutto il server (e resta fra un ridisegno e l'altro: questo file si rilegge a ogni ridisegno, un semplice {} si svuoterebbe ogni volta)."""
    return {}, _gh_thr.Lock()


_GH_MEMORIA, _GH_BLOCCO = _gh_memoria_globale()               # (archivio, ramo, nome) -> {"dati", "sha", "t"}
_GH_TTL, _GH_MAX_BYTE, _GH_MAX_VOCI = 60.0, 600 * 1024, 40


def _gh_veloce():
    try:
        return str(st.secrets.get("ARCHIVIO_VELOCE", "si")).strip().lower() not in ("no", "off", "0", "spento")
    except Exception:
        return True


class ArchivioGitHub:
    """Salva i file JSON in un repository GitHub privato (i dati restano per sempre)."""
    permanente = True

    def _mem_chiave(self, nome):
        return (self.repo, self.ramo or "", nome)

    def _mem_leggi(self, nome):
        if not _gh_veloce():
            return None
        with _GH_BLOCCO:
            e = _GH_MEMORIA.get(self._mem_chiave(nome))
            if e and time.time() - e["t"] <= _GH_TTL:
                return _gh_copy.deepcopy(e["dati"]), e["sha"]
        return None

    def _mem_metti(self, nome, dati, sha):
        if not _gh_veloce() or not sha:
            return self._mem_togli(nome)
        try:
            if len(json.dumps(dati, ensure_ascii=False)) > _GH_MAX_BYTE:              # file grandi (foto, PDF): non si tengono in memoria
                return self._mem_togli(nome)
            copia = _gh_copy.deepcopy(dati)
        except Exception:
            return self._mem_togli(nome)
        with _GH_BLOCCO:
            _GH_MEMORIA[self._mem_chiave(nome)] = {"dati": copia, "sha": sha, "t": time.time()}
            while len(_GH_MEMORIA) > _GH_MAX_VOCI:
                del _GH_MEMORIA[min(_GH_MEMORIA, key=lambda k: _GH_MEMORIA[k]["t"])]

    def _mem_togli(self, nome):
        with _GH_BLOCCO:
            _GH_MEMORIA.pop(self._mem_chiave(nome), None)

    def __init__(self, token, repo, ramo=None, http=requests):
        self.repo, self.ramo, self.http = repo, ramo, http
        self.intest = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                       "X-GitHub-Api-Version": "2022-11-28"}

    def _url(self, nome):
        return f"https://api.github.com/repos/{self.repo}/contents/{nome}"

    def _leggi(self, nome):
        par = {"ref": self.ramo} if self.ramo else None
        r = self.http.get(self._url(nome), headers=self.intest, params=par, timeout=20)
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        j = r.json()
        if j.get("content"):
            grezzo = base64.b64decode(j["content"])
        else:                                   # file grande: lo leggo come "blob"
            b = self.http.get(f"https://api.github.com/repos/{self.repo}/git/blobs/{j['sha']}",
                              headers=self.intest, timeout=30)
            b.raise_for_status()
            grezzo = base64.b64decode(b.json()["content"])
        try:
            dati_ = json.loads(grezzo.decode("utf-8"))
        except json.JSONDecodeError:
            dati_ = {}
        self._mem_metti(nome, dati_, j["sha"])
        return dati_, j["sha"]

    def leggi(self, nome):
        m = self._mem_leggi(nome)                                   # appena letto o scritto da noi: niente richiesta
        if m is not None:
            return m[0]
        dati, _ = self._leggi(nome)
        return dati if dati is not None else {}

    def _scrivi(self, nome, dati, sha, messaggio):
        corpo = {"message": messaggio or "Aggiornamento dispensa",
                 "content": base64.b64encode(json.dumps(dati, ensure_ascii=False).encode("utf-8")).decode()}
        if sha:
            corpo["sha"] = sha
        if self.ramo:
            corpo["branch"] = self.ramo
        r = self.http.put(self._url(nome), headers=self.intest, json=corpo, timeout=30)
        if r.status_code in (409, 422):
            self._mem_togli(nome)
            raise Conflitto()
        r.raise_for_status()
        try:
            nuovo_sha = ((r.json() or {}).get("content") or {}).get("sha")
        except Exception:
            nuovo_sha = None
        self._mem_metti(nome, dati, nuovo_sha)                       # così il ridisegno della pagina non deve rileggere il file

    def modifica(self, nome, fn, messaggio=""):
        for tentativo in range(4):
            m = self._mem_leggi(nome) if tentativo == 0 else None
            if m is not None:
                dati, sha = m                                        # lo so già: parto direttamente dalla scrittura (se è cambiato, GitHub risponde «conflitto» e si rilegge)
            elif tentativo == 0 and nome.startswith("documenti/") and _gh_veloce():
                dati, sha = {}, None                                 # un file di documento è quasi sempre NUOVO: provo a crearlo senza leggere prima
            else:
                dati, sha = self._leggi(nome)
                dati = dati if dati is not None else {}
            fn(dati)
            try:
                self._scrivi(nome, dati, sha, messaggio)
                return dati
            except Conflitto:                    # qualcun altro ha salvato nel frattempo: riprovo
                time.sleep(0.5 * (tentativo + 1))
        raise RuntimeError(t("Non riesco a salvare: troppe modifiche contemporanee. Riprova."))

    def elimina(self, nome, messaggio=""):
        self._mem_togli(nome)
        _, sha = self._leggi(nome)
        if sha is None:
            return
        corpo = {"message": messaggio or "Eliminato", "sha": sha}
        if self.ramo:
            corpo["branch"] = self.ramo
        r = self.http.delete(self._url(nome), headers=self.intest, json=corpo, timeout=30)
        self._mem_togli(nome)
        if r.status_code != 404:
            r.raise_for_status()


def segreto(nome, default=None):
    try:
        return st.secrets[nome]
    except Exception:
        return default


def password_admin():
    p = segreto("admin_password")
    return str(p) if p else ""


def nome_admin():
    return str(segreto("admin_nome", "Amministratore"))


@st.cache_resource
def crea_archivio():
    g = segreto("github")
    if g and g.get("token") and g.get("repo"):
        return ArchivioGitHub(g["token"], g["repo"], g.get("branch"))
    return ArchivioLocale(os.environ.get("DISPENSA_DATI", "dati_locali"))


@st.cache_data(ttl=15, show_spinner=False)
def carica_dati(_archivio, nome):
    return _archivio.leggi(nome)


def salva_file(nome, fn, messaggio):
    crea_archivio().modifica(nome, fn, messaggio)
    carica_dati.clear()


def salva(fn, messaggio):
    """Salva nella dispensa della persona che ha fatto l'accesso."""
    salva_file(st.session_state["percorso"], fn, messaggio)


def adesso():
    try:
        return datetime.now(ZoneInfo("Europe/Rome")).replace(tzinfo=None)
    except Exception:
        return datetime.now()


# ---------- password personali ----------
PAROLE = ["mela", "luna", "rosa", "sole", "fiore", "mare", "pino", "nuvola", "vento", "lago", "stella", "fiume",
          "prato", "limone", "arancia", "pera", "fico", "noce", "miele", "pane", "olio", "sale", "riso", "grano",
          "menta", "salvia", "basilico", "timo", "aglio", "cipolla", "carota", "zucca", "pesca", "uva", "melone",
          "fragola", "castagna", "mandorla", "nocciola", "ceci", "fagiolo", "farro", "orzo", "pepe", "zenzero",
          "cannella", "vaniglia", "anice", "bosco", "collina", "valle", "monte", "isola", "spiaggia", "sabbia",
          "roccia", "brezza", "alba", "tramonto", "pioggia", "neve", "ruscello", "campo", "orto", "sentiero", "ponte"]


def normalizza_password(pw):
    return re.sub(r"\s+", "", pw or "").lower()


def hash_password(pw):
    """Impronta della password: salvata al posto della password vera (che non si puo' ricostruire)."""
    chiave = str(segreto("pepper") or (password_admin() + "|dispensa")).encode("utf-8")
    return hmac.new(chiave, normalizza_password(pw).encode("utf-8"), hashlib.sha256).hexdigest()


def genera_password(impronte_esistenti):
    """Es.: Mela-Luna-Pino-4821 (casuale, diversa per ogni persona)."""
    sicuro = random.SystemRandom()
    while True:
        pw = "-".join(p.capitalize() for p in sicuro.sample(PAROLE, 3)) + "-" + str(sicuro.randrange(1000, 10000))
        if hash_password(pw) not in impronte_esistenti:
            return pw


@st.cache_resource
def registro_errori():
    return []


def troppi_tentativi():
    """Massimo 8 password sbagliate al minuto in tutta l'app: rende inutile provare a indovinare."""
    r = registro_errori()
    r[:] = [t for t in r if time.time() - t < 60]
    return len(r) >= 8


def cerca_accesso(pw, utenti):
    h = hash_password(pw)
    pa = password_admin()
    if pa and hmac.compare_digest(h, hash_password(pa)):
        return {"uid": "admin", "nome": nome_admin(), "admin": True, "h": h}
    for u in utenti:
        if u.get("attivo", True) and hmac.compare_digest(u.get("hash", ""), h):
            return {"uid": u["id"], "nome": u["nome"], "admin": False, "h": h}
    return None


def sessione_valida(sess, utenti):
    """Controlla ad ogni azione che la password non sia stata cambiata o bloccata."""
    if sess.get("uid") == "prova":
        return True
    if sess.get("admin"):
        pa = password_admin()
        return bool(pa) and hmac.compare_digest(sess["h"], hash_password(pa))
    return any(u["id"] == sess["uid"] and u.get("attivo", True) and hmac.compare_digest(u.get("hash", ""), sess["h"])
               for u in utenti)


def registra_accesso(uid, utenti):
    """Annota l'ultimo accesso (al massimo una volta ogni 6 ore, per non fare salvataggi inutili)."""
    u = next((x for x in utenti if x["id"] == uid), None)
    if not u:
        return
    try:
        if u.get("ultimo_accesso") and (adesso() - datetime.fromisoformat(u["ultimo_accesso"])).total_seconds() < 6 * 3600:
            return
    except ValueError:
        pass

    def segna(d):
        for x in d.get("utenti", []):
            if x["id"] == uid:
                x["ultimo_accesso"] = adesso().isoformat(timespec="minutes")
    try:
        salva_file("utenti.json", segna, "Accesso")
    except Exception:
        pass


def applica_modifiche(d, modificata):
    """Applica alla dispensa le modifiche fatte nella tabella 'Gestisci'."""
    nuovi = []
    for r in d.get("articoli", []):
        if r["id"] not in modificata.index:
            nuovi.append(r)
            continue
        m = modificata.loc[r["id"]]
        if bool(m["🗑️"]):
            continue
        r["nome"] = str(m["Prodotto"]).strip() or r.get("nome", "")
        r["quantita"] = float(m["Unità"])
        r["formato_valore"] = float(m["Contenuto"]) if m["Contenuto"] else None
        r["formato_unita"] = m["Misura"] if m["Contenuto"] else None
        r["scadenza"] = pd.to_datetime(m["Scadenza"]).date().isoformat() if pd.notna(m["Scadenza"]) else None
        r["note"] = "" if pd.isna(m["Note"]) else str(m["Note"])
        if r["quantita"] > 0:
            nuovi.append(r)           # 0 unità = finito: lo tolgo dalla dispensa
    d["articoli"] = nuovi


# =====================================================================
# PARTE 3 - GRAFICA (HTML e colori)
# =====================================================================
CSS = """
<style>
.hero{background:linear-gradient(135deg,#1b5e20 0%,#00897b 55%,#0288d1 100%);color:#fff;padding:22px 26px;
 border-radius:22px;margin-bottom:14px;box-shadow:0 10px 30px rgba(0,0,0,.15)}
.hero h1{margin:0;font-size:1.9rem;color:#fff;padding:0}
.hero p{margin:4px 0 0;opacity:.92}
.avviso{border-radius:16px;padding:14px 18px;margin:10px 0;border-left:8px solid;box-shadow:0 4px 14px rgba(0,0,0,.08)}
.avviso h3{margin:0 0 4px 0;font-size:1.08rem;padding:0}
.avviso .tot{font-weight:700;margin-bottom:4px}
.avviso ul{margin:6px 0 0 0;padding-left:20px}
.avviso.rosso{background:#ffebee;border-color:#d32f2f;color:#7f0000}
.avviso.arancione{background:#fff3e0;border-color:#ef6c00;color:#6a3100}
.avviso.scaduto{background:#efebe9;border-color:#4e342e;color:#2b1b17}
.griglia{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:16px;margin-top:8px}
.scheda{background:var(--secondary-background-color,#fff);color:var(--text-color,#222);border-radius:20px;
 overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,.12);border-top:8px solid var(--c);display:flex;flex-direction:column}
.scheda .foto{height:150px;display:flex;align-items:center;justify-content:center;background:#fff;font-size:64px}
.scheda .foto img{max-height:140px;max-width:92%;object-fit:contain}
.scheda .corpo{padding:12px 14px 16px 14px;display:flex;flex-direction:column;gap:6px}
.scheda .nome{font-weight:700;font-size:1.05rem;line-height:1.2}
.scheda .marca{opacity:.65;font-size:.85rem;margin-top:-4px}
.scheda .quantita{font-size:.95rem}
.scadenza{display:inline-block;color:#fff;background:var(--c);border-radius:999px;padding:4px 12px;font-size:.85rem;font-weight:600;width:fit-content}
.data{font-size:.8rem;opacity:.7}
.badge{display:inline-block;border-radius:999px;padding:2px 9px;font-size:.75rem;margin:2px 3px 0 0;
 background:rgba(128,128,128,.18)}
.badge.pericolo{background:#d32f2f;color:#fff;font-weight:700}
.badge.attenzione{background:#fbc02d;color:#3b2d00;font-weight:700}
.badge.bene{background:#2e7d32;color:#fff}
.nota{opacity:.7;font-size:.8rem}
</style>
"""


def foto_html(r):
    src = src_sicuro(r.get("immagine") or "")
    return f"<img src='{html.escape(src, quote=True)}' alt=''>" if src else "🥫"


def badge_allergeni(r, mie):
    pezzi = []
    allergeni, tracce = r.get("allergeni") or [], r.get("tracce") or []
    if not r.get("allergeni_noti") and not allergeni:
        pezzi.append(f"<span class='badge'>❔ {t('Allergeni non verificati')}</span>")
    for a in allergeni:
        classe = "pericolo" if a in mie else ""
        icona = f"⚠️ {t('Contiene')} " if a in mie else ""
        pezzi.append(f"<span class='badge {classe}'>{icona}{html.escape(t_all(a))}</span>")
    for a in tracce:
        classe = "attenzione" if a in mie else ""
        pezzi.append(f"<span class='badge {classe}'>{t('tracce di')} {html.escape(t_all(a))}</span>")
    if r.get("senza_glutine"):
        pezzi.append(f"<span class='badge bene'>🌾 {t('Senza glutine')}</span>")
    return "".join(pezzi)


def scheda_html(r, data_oggi, mie):
    stato, giorni = stato_scadenza(r.get("scadenza"), data_oggi)
    colore = COLORI[stato]
    marca = f"<div class='marca'>{html.escape(r['marca'])}</div>" if r.get("marca") else ""
    data = f"<div class='data'>{data_it(r['scadenza'])}</div>" if r.get("scadenza") else ""
    nota = f"<div class='nota'>📝 {html.escape(r['note'])}</div>" if r.get("note") else ""
    return (f"<div class='scheda' style='--c:{colore}'><div class='foto'>{foto_html(r)}</div>"
            f"<div class='corpo'><div class='nome'>{html.escape(r.get('nome', ''))}</div>{marca}"
            f"<div class='quantita'>📦 {html.escape(descrivi([r]))}</div>"
            f"<span class='scadenza'>{ICONE[stato]} {testo_giorni(stato, giorni)}</span>{data}"
            f"<div>{badge_allergeni(r, mie)}</div>{nota}</div></div>")


def avviso_html(titolo, classe, righe, data_oggi):
    voci = "".join(
        f"<li><b>{html.escape(r.get('nome', ''))}</b>: {html.escape(descrivi([r]))} "
        f"· {t('scade il')} {data_it(r['scadenza'])} ({testo_giorni(*stato_scadenza(r['scadenza'], data_oggi))})</li>"
        for r in righe)
    return (f"<div class='avviso {classe}'><h3>{titolo}</h3>"
            f"<div class='tot'>{t('In totale:')} {html.escape(descrivi(righe))}</div><ul>{voci}</ul></div>")


GRADO_COLORI = {"a": "#038141", "b": "#85bb2f", "c": "#fecb02", "d": "#ee8100", "e": "#e63e11"}


def badge_grado(nome, grado):
    if not grado:
        return ""
    testo = "#3b2d00" if grado == "c" else "#fff"
    return (f"<span class='badge' style='background:{GRADO_COLORI[grado]};color:{testo};font-weight:700'>"
            f"{html.escape(nome)} {grado.upper()}</span>")


def sino(v):
    return {"si": t("Sì"), "no": t("No")}.get(v, t("Non noto"))


def mostra_scheda(p, mie, mostra_link=True):
    """Pannello con le informazioni di un prodotto: valori nutrizionali, ingredienti, prezzi e collegamenti online."""
    extra = p.get("extra") or {}
    c1, c2 = st.columns([1, 3])
    src = src_sicuro(p.get("immagine") or "")
    if src:
        c1.image(src, width=110)
    c2.markdown(f"**{p.get('nome', '')}**" + (f" · {p['marca']}" if p.get("marca") else ""))
    c2.caption(descrivi([p]) if p.get("quantita") else "")
    gradi = badge_grado("Nutri-Score", extra.get("nutriscore")) + badge_grado("Eco-Score", extra.get("ecoscore"))
    if extra.get("nova"):
        gradi += f"<span class='badge'>NOVA {extra['nova']}</span>"
    st.markdown(gradi + badge_allergeni(p, mie), unsafe_allow_html=True)

    n = extra.get("nutrienti") or {}
    if n:
        voci = [("energia_kcal", "Energia (kcal)"), ("grassi", "Grassi (g)"), ("saturi", "di cui saturi (g)"),
                ("carboidrati", "Carboidrati (g)"), ("zuccheri", "di cui zuccheri (g)"), ("fibre", "Fibre (g)"),
                ("proteine", "Proteine (g)"), ("sale", "Sale (g)")]
        st.dataframe(pd.DataFrame([{t("Valori nutrizionali"): t(nome), t("Per 100 g"): fmt_num(n[k])}
                                   for k, nome in voci if k in n]), hide_index=True)
    else:
        st.caption(t("Nessun dato nutrizionale disponibile."))

    righe = []
    categoria = p.get("categoria") or ""
    if categoria:
        righe.append(f"**{t('Categoria')}:** {categoria}")
    if any(extra.get(k, "?") != "?" for k in ("vegano", "vegetariano", "olio_palma")):
        righe.append(f"**{t('Vegano')}:** {sino(extra.get('vegano'))} · **{t('Vegetariano')}:** "
                     f"{sino(extra.get('vegetariano'))} · **{t('Olio di palma')}:** {sino(extra.get('olio_palma'))}")
    if extra.get("origine"):
        righe.append(f"**{t('Provenienza')}:** {extra['origine']}")
    if extra.get("paesi"):
        righe.append(f"**{t('Venduto in')}:** {extra['paesi']}")
    if extra.get("additivi") is not None:
        righe.append(f"**{t('Additivi')}:** {extra['additivi']}")
    if p.get("ingredienti"):
        righe.append(f"**{t('Ingredienti')}:** {p['ingredienti']}")
    if righe:
        st.markdown("\n\n".join(righe))

    if mostra_link:
        if p.get("barcode"):
            prezzi = cerca_prezzi(p["barcode"])
            if prezzi:
                st.markdown(f"**💶 {t('Prezzi segnalati dalla community (Open Prices)')}**")
                for z in prezzi:
                    importo = f"{z['prezzo']:.2f}" if lingua() == "en" else f"{z['prezzo']:.2f}".replace(".", ",")
                    st.write(f"{importo} {z['valuta']} · {z['negozio'] or '—'} · {z['data']}")
            else:
                st.caption(t("Nessun prezzo segnalato."))
        st.markdown(f"**🔗 {t('Cerca online')}**")
        colonne = st.columns(2)
        for i, (etichetta, url) in enumerate(link_online(p.get("nome", ""), p.get("marca", ""), p.get("barcode", ""),
                                                           p.get("immagine", ""))):
            colonne[i % 2].link_button(etichetta, url, width="stretch")
        st.caption(t("I collegamenti aprono siti esterni: prezzi e recensioni non sono verificati da questa app."))


# >>> FINE PARTE 2 di 4: adesso incolla la PARTE 3 qui sotto <<<
