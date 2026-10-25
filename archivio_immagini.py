# -*- coding: utf-8 -*-
"""Archivio delle immagini: ogni foto di prodotto salvata (gia' scontornata e raddrizzata) resta in archivio e si puo' riusare
quando aggiungi o modifichi un prodotto ("🗂️ Archivio"). Ogni persona ha il suo archivio. Le foto stanno come file nel repository
dei dati (immagini/<persona>/<id>.webp) e un indice con le miniature. Caricato da app_dispensa.py prima di foto_prodotto.py."""
import hashlib as _hl


def _cartella_img():
    uid = os.path.basename(str(st.session_state.get("percorso", "dispense/prova.json"))).rsplit(".", 1)[0] or "prova"
    return f"immagini/{uid}"


def _bin_leggi(nome):
    a = crea_archivio()
    if hasattr(a, "intest"):                       # GitHub
        par = {"ref": a.ramo} if a.ramo else None
        r = a.http.get(a._url(nome), headers=a.intest, params=par, timeout=25)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        j = r.json()
        if j.get("content"):
            return base64.b64decode(j["content"])
        b = a.http.get(f"https://api.github.com/repos/{a.repo}/git/blobs/{j['sha']}", headers=a.intest, timeout=30)
        b.raise_for_status()
        return base64.b64decode(b.json()["content"])
    try:
        with open(a._percorso(nome), "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _bin_scrivi(nome, dati, messaggio="Immagine"):
    a = crea_archivio()
    if hasattr(a, "intest"):
        par = {"ref": a.ramo} if a.ramo else None
        r = a.http.get(a._url(nome), headers=a.intest, params=par, timeout=25)
        sha = r.json().get("sha") if r.status_code == 200 else None
        corpo = {"message": messaggio, "content": base64.b64encode(dati).decode()}
        if sha:
            corpo["sha"] = sha
        if a.ramo:
            corpo["branch"] = a.ramo
        p = a.http.put(a._url(nome), headers=a.intest, json=corpo, timeout=40)
        p.raise_for_status()
        return
    percorso = a._percorso(nome)
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    with open(percorso, "wb") as f:
        f.write(dati)


def _bin_elimina(nome, messaggio="Immagine eliminata"):
    a = crea_archivio()
    if hasattr(a, "intest"):
        par = {"ref": a.ramo} if a.ramo else None
        r = a.http.get(a._url(nome), headers=a.intest, params=par, timeout=25)
        if r.status_code != 200:
            return
        corpo = {"message": messaggio, "sha": r.json()["sha"]}
        if a.ramo:
            corpo["branch"] = a.ramo
        a.http.delete(a._url(nome), headers=a.intest, json=corpo, timeout=30)
        return
    try:
        os.remove(a._percorso(nome))
    except FileNotFoundError:
        pass


def _uri_in_bytes(uri):
    if not isinstance(uri, str) or not uri.startswith("data:image/") or "," not in uri:
        return None
    try:
        return base64.b64decode(uri.split(",", 1)[1])
    except Exception:
        return None


def _miniatura(dati, lato=150):
    im = Image.open(io.BytesIO(dati)).convert("RGBA")
    im.thumbnail((lato, lato))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=70, method=4)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def indice_immagini():
    return list(carica_dati(crea_archivio(), _cartella_img() + "/indice.json").get("immagini", []))


def archivia_immagine(nome, marca, barcode, uri):
    """Mette la foto nell'archivio (una volta sola: se e' identica a una gia' presente aggiorna solo i dati). Ritorna l'id o None."""
    dati = _uri_in_bytes(uri)
    if not dati:
        return None
    ident = _hl.md5(dati).hexdigest()[:12]
    cartella = _cartella_img()
    presente = any(x.get("id") == ident for x in indice_immagini())
    if not presente:
        _bin_scrivi(f"{cartella}/{ident}.webp", dati, "Immagine di " + (nome or "prodotto"))
    mini = _miniatura(dati)

    def _agg(d):
        lista = d.setdefault("immagini", [])
        voce = next((x for x in lista if x.get("id") == ident), None)
        if voce is None:
            voce = {"id": ident, "mini": mini, "creato": datetime.now().isoformat(timespec="seconds")}
            lista.insert(0, voce)
        voce.update({"nome": (nome or "").strip(), "marca": (marca or "").strip(), "barcode": (barcode or "").strip()})
    salva_file(cartella + "/indice.json", _agg, "Archivio immagini")
    return ident


def immagine_da_archivio(ident):
    dati = _bin_leggi(f"{_cartella_img()}/{ident}.webp")
    return ("data:image/webp;base64," + base64.b64encode(dati).decode()) if dati else ""


def elimina_da_archivio(ident):
    _bin_elimina(f"{_cartella_img()}/{ident}.webp")

    def _togli(d):
        d["immagini"] = [x for x in d.get("immagini", []) if x.get("id") != ident]
    salva_file(_cartella_img() + "/indice.json", _togli, "Immagine tolta dall'archivio")


def selettore_archivio(chiave):
    """Griglia delle foto in archivio con ricerca. Ritorna l'id scelto (o '')."""
    voci = indice_immagini()
    if not voci:
        st.info("L'archivio è vuoto: ogni foto che salvi con un prodotto ci finisce da sola.")
    cerca = st.text_input("🔎 Cerca nell'archivio", key=f"{chiave}_arch_cerca", placeholder="nome, marca o codice").strip().lower()
    if cerca:
        voci = [v for v in voci if cerca in f"{v.get('nome', '')} {v.get('marca', '')} {v.get('barcode', '')}".lower()]
    scelta = ""
    for i in range(0, min(len(voci), 24), 3):
        with st.container(key=f"azioni_arch_{chiave}_{i}"):          # tre foto per riga anche sul telefono
            cols = st.columns(3, gap="small")
        for col, v in zip(cols, voci[i:i + 3]):
            with col:
                st.markdown(f"<div class='foto-ampia' style='height:110px;padding:4px'><img src='{html.escape(v.get('mini', ''), quote=True)}' alt=''></div>",
                            unsafe_allow_html=True)
                st.caption((v.get("nome") or "(senza nome)")[:28])
                if st.button("Usa", key=f"{chiave}_arch_usa_{v['id']}", width="stretch"):
                    scelta = v["id"]
                if st.button("🗑️", key=f"{chiave}_arch_del_{v['id']}", width="stretch", help="Toglie la foto dall'archivio"):
                    try:
                        elimina_da_archivio(v["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Non sono riuscito a eliminarla: {e}")
    if len(voci) > 24:
        st.caption(f"Mostro 24 foto su {len(voci)}: usa la ricerca per trovare le altre.")
    return scelta


def archivia_foto_esistenti(massimo=25):
    """Mette in archivio le foto dei prodotti gia' in dispensa (a gruppi, per non fare troppe richieste)."""
    articoli = carica_dati(crea_archivio(), st.session_state["percorso"]).get("articoli", [])
    gia = {x.get("id") for x in indice_immagini()}
    fatte = 0
    visti = set()
    for r in articoli:
        uri = r.get("immagine") or ""
        dati = _uri_in_bytes(uri)
        if not dati:
            continue
        ident = _hl.md5(dati).hexdigest()[:12]
        if ident in gia or ident in visti:
            continue
        visti.add(ident)
        archivia_immagine(r.get("nome"), r.get("marca"), r.get("barcode"), uri)
        fatte += 1
        if fatte >= massimo:
            break
    return fatte
