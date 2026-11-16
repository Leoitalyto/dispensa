# 🗂️ «Allega dall'archivio»: in ogni punto di Salute dove si allegano file (referti, ricette, documenti, vaccini…) si può anche
# scegliere un file GIÀ presente nell'archivio, senza rifare la foto. Il file non viene copiato: si riusa lo stesso. Prefisso: ar_riuso_
import hashlib as _arr_hl


class _ArFile:
    """Un file dell'archivio che passa per «caricato»: serve a far funzionare gli stessi salvataggi di sempre."""
    def __init__(self, voce, rif):
        self.name = voce["nome"]
        self.type = voce["mime"]
        self._voce = voce
        self._rif = dict(rif)
        self._dati = None

    def getvalue(self):
        if self._dati is None:
            self._dati = _ar_carica(self._voce) or b""
        return self._dati

    def read(self):
        return self.getvalue()


def _ar_riuso_riferimenti(f):
    """{id: riferimento completo} di tutti i file di Salute (stessa ricerca di ar_voci)."""
    trovati = {}

    def giu(x):
        if isinstance(x, dict):
            if x.get("id") and x.get("nome") and (x.get("mime") or x.get("sha")):
                trovati.setdefault(x["id"], x)
            for v in x.values():
                giu(v)
        elif isinstance(x, list):
            for v in x:
                giu(v)
    giu(f)
    return trovati


def ar_uploader(etichetta, **kw):
    """Come st.file_uploader, più la scelta «🗂️ Oppure allega dall'archivio». Restituisce i file caricati + quelli scelti dall'archivio."""
    nuovi = st.file_uploader(etichetta, **kw)
    elenco = list(nuovi) if isinstance(nuovi, (list, tuple)) else ([nuovi] if nuovi else [])
    try:
        f = _fa_dati()
        nomi = {p["id"]: p["nome"] for p in _fa_profili(f)}
        voci = [v for v in ar_voci(f, nomi) if v["mime"] == "application/pdf" or str(v["mime"]).startswith("image/")]
        if not voci:
            return nuovi if not isinstance(nuovi, (list, tuple)) else elenco
        rifs = _ar_riuso_riferimenti(f)
        per_id = {v["id"]: v for v in voci if v["id"] in rifs}
        if not per_id:
            return nuovi if not isinstance(nuovi, (list, tuple)) else elenco
        k = "arup_" + _arr_hl.md5((etichetta + str(kw.get("key", ""))).encode()).hexdigest()[:10]
        ids = sorted(per_id, key=lambda i: per_id[i].get("data") or "", reverse=True)[:400]

        def nome_di(i):
            v = per_id[i]
            return v["nome"][:40] + (f" · {v['collegato'][:30]}" if v["collegato"] else "") + (f" · {v['persona']}" if v["persona"] else "")
        scelti = st.multiselect("🗂️ Oppure allega dall'archivio (file già presenti, senza rifare la foto)", ids, format_func=nome_di, key=k,
                                placeholder="Scrivi per cercare…")
        elenco += [_ArFile(per_id[i], rifs[i]) for i in scelti]
    except Exception as _e:
        st.caption(f"(archivio non disponibile: {type(_e).__name__})")
    return elenco if (isinstance(nuovi, (list, tuple)) or elenco) else nuovi


_ar_riuso_salva_originale = _fa_salva_files


def _fa_salva_files(caricati, esistenti=None):                                                       # noqa: F811
    """Come prima, ma i file scelti dall'archivio si collegano (stesso file) invece di salvarli un'altra volta."""
    veri = [u for u in (caricati or []) if not isinstance(u, _ArFile)]
    da_archivio = [u for u in (caricati or []) if isinstance(u, _ArFile)]
    gia = {a.get("id") for a in (esistenti or [])}
    risultato = _ar_riuso_salva_originale(veri, esistenti) if veri else []
    gia |= {a.get("id") for a in risultato}
    for u in da_archivio:
        if u._rif.get("id") not in gia:
            gia.add(u._rif["id"])
            risultato.append({x: y for x, y in u._rif.items() if x in ("id", "nome", "mime", "sha", "originale")})
    return risultato
