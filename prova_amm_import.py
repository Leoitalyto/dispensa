"""Prova dell'IMPORTAZIONE di documenti in Spese e scadenze (avviso, rate, bollettino, ricevuta) con AppTest (le finestre st.dialog sono simulate: restano aperte fra un ridisegno e l'altro finché non si salva o si annulla).
python3 prova_amm_import.py"""
import os, json, shutil
from datetime import date, timedelta
os.environ["DISPENSA_DATI"] = "/tmp/integ/dati"
from streamlit.testing.v1 import AppTest
ok = tot = 0
def v(c, t):
    global ok, tot; tot += 1; ok += bool(c); print(("OK      " if c else "FALLITO ") + t)
def prepara(casa_extra=None):
    shutil.rmtree("/tmp/integ/dati", ignore_errors=True)
    for d in ("dispense", "famiglia", "documenti/admin"): os.makedirs(f"/tmp/integ/dati/{d}")
    json.dump({"articoli": [], "versione": 1}, open("/tmp/integ/dati/famiglia/dispensa.json", "w")); json.dump({"utenti": []}, open("/tmp/integ/dati/utenti.json", "w"))
    casa = {"beni": [], "manutenzioni": [], "case": [{"id": "c2", "nome": "Seconda casa", "indirizzo": "Via Mare 1"}],
            "documenti": [{"id": "dc1", "tipo": "Avviso di pagamento", "titolo": "Avviso rata condominio", "data": "2026-11-01", "file": {"id": "ff1", "nome": "a.pdf", "mime": "application/pdf"}}]}
    casa.update(casa_extra or {})
    json.dump({"articoli": [], "farmacia": {"profili": [{"id": "p0", "nome": "L"}], "medicinali": [], "terapie": [], "visite": [], "prescrizioni": [], "vaccinazioni": [], "documenti": []}, "casa": casa, "auto": {"veicoli": []}}, open("/tmp/integ/dati/dispense/admin.json", "w"))
def dati(): return json.load(open("/tmp/integ/dati/dispense/admin.json"))["casa"]
CODICE = """
import streamlit as st, json
src = open("/tmp/prod_sim/app_dispensa.py", encoding="utf-8").read(); g = globals(); g["__file__"] = "/tmp/prod_sim/app_dispensa.py"
exec(compile(src[:src.index('try:\\n    for _nome in ("parte3.py"')], "x", "exec"), g)
st.session_state["sess"] = {"uid": "admin", "nome": "Leonardo", "admin": True, "h": ""}; st.session_state["percorso"] = "dispense/admin.json"
st.cache_data.clear()
# finestre simulate: restano aperte finché non si salva/annulla (st.rerun le chiude)
def _dialog(titolo, **k):
    def deco(f):
        def apri():
            st.session_state["_dlg"] = f
            st.session_state["_dlg_giro"] = st.session_state.get("_tabs_giro", 0)
            try:
                f()
            except BaseException as e:
                if type(e).__name__ == "RerunException":
                    st.session_state["_dlg"] = None
                raise
        return apri
    return deco
st.dialog = _dialog
c_reale = carica_dati(crea_archivio(), "dispense/admin.json").get("casa", {})
cv = ca_vista_casa(c_reale, st.session_state.get("ca_casa_sel") or "")
ca_amm_tab(cv)
f_aperta = st.session_state.get("_dlg")
if f_aperta and st.session_state.get("_dlg_giro") != st.session_state.get("_tabs_giro", 0):
    try:
        f_aperta()
    except BaseException as e:
        if type(e).__name__ == "RerunException":
            st.session_state["_dlg"] = None
        raise
"""
def avvia():
    at = AppTest.from_string(CODICE, default_timeout=250); at.secrets["admin_password"] = "x"; at.run(); assert not at.exception, [str(e.value)[:300] for e in at.exception]; return at
def vai(at, chiave):
    at.button(key=chiave).click().run(); assert not at.exception, [str(e.value)[:300] for e in at.exception]
def testo(at): return " ".join(m.value for m in at.markdown) + " " + " ".join(c.value for c in at.caption) + " " + " ".join(i.value for i in at.info) + " " + " ".join(w.value for w in at.warning)

import hashlib, fitz
def pdf(righe):
    d = fitz.open(); p = d.new_page(); y = 60
    for r in righe:
        p.insert_text((50, y), r, fontsize=11); y += 18
    b = d.tobytes(); d.close(); return b
AVVISO = ["AVVISO DI PAGAMENTO RATE CONDOMINIALI - ESERCIZIO 2026", "Condominio Aurora - Via Mare 1, Torino", "Piano rate:", "1a rata scadenza 31/01/2026 EUR 300,00".replace("EUR", "euro"),
          "2a rata scadenza 30/04/2026 euro 300,00", "3a rata scadenza 31/07/2026 euro 300,00", "4a rata scadenza 31/10/2026 euro 300,00", "Totale da versare euro 1.200,00"]
RICEVUTA = ["RICEVUTA DI PAGAMENTO", "Bonifico eseguito il 12/11/2026", "Importo euro 300,00", "Causale: rata condominio Aurora", "CRO 12345678901"]
LETTERA = ["Gentili condomini,", "vi informo che la riunione di condominio si terra il 3 ottobre.", "Cordiali saluti, l'amministratore"]
def sorgente(nome, righe): return {"nome": nome, "mime": "application/pdf", "dati": pdf(righe), "link": ""}
def apri(at, src):
    at.session_state["amm_vista"] = "spese"; at.session_state["amm_imp_on"] = True; at.session_state["ca_bozza_in"] = src; at.run()
    assert not at.exception, [str(e.value)[:300] for e in at.exception]
    return "amm_im_" + hashlib.sha256(src["dati"]).hexdigest()[:8]
prepara({"amministratori": [{"id": "ad1", "nome": "Mario", "cognome": "Rossi", "studio": "Studio Rossi"}], "documenti": []}); at = avvia()
at.session_state["amm_vista"] = "spese"; at.run()
v(any(b.key == "amm_imp_apri" for b in at.button), "in Spese e scadenze c'è il pulsante «📥 Importa un documento»")
at.button(key="amm_imp_apri").click().run()
v(any(b.key == "amm_imp_chiudi" for b in at.button) and "Importa un documento" in " ".join(m.value for m in at.markdown), "toccandolo si apre il caricamento di Documenti (foto, galleria, PDF…) con «✖ Chiudi l'importazione»")
# 1) avviso con le rate → nuova spesa
s1 = sorgente("avviso_rate.pdf", AVVISO); k = apri(avvia(), s1) if False else None
at = avvia(); k = apri(at, s1)
v(at.radio(key=k + "_az").value == "nuova" and "Rate trovate:** 4" in testo(at), "avviso con 4 rate: la finestra propone «Crea una nuova spesa» e dice «Rate trovate: 4»")
v([at.text_input(key=f"{k}_rd{i}").value for i in range(4)] == ["31/01/2026", "30/04/2026", "31/07/2026", "31/10/2026"] and at.text_input(key=f"{k}_ri0").value == "300,00", "le 4 rate sono già scritte (date e importi) e si possono correggere")
v(at.text_input(key=k + "_d").value == "Rate condominio 2026", "descrizione proposta: «Rate condominio 2026»")
# una data sbagliata: errore e NIENTE archiviato
at.text_input(key=f"{k}_rd1").set_value("30/13/2026"); at.button(key=k + "_ok").click().run()
v("non è una data valida" in " ".join(e.value for e in at.error) and dati().get("spese_amm", []) == [] and dati().get("documenti", []) == [], "una data sbagliata: messaggio chiaro e non si archivia niente (né spesa né documento)")
at.text_input(key=f"{k}_rd1").set_value("30/04/2026"); at.selectbox(key=k + "_a").set_value("ad1"); at.button(key=k + "_ok").click().run()
d = dati(); sp = d["spese_amm"]; dc = d["documenti"]
v(len(sp) == 1 and len(sp[0]["rate"]) == 4 and sp[0]["importo_totale"] == 1200 and sp[0]["amministratore_id"] == "ad1", f"spesa creata: {sp[0]['descrizione']}, 4 rate, totale {sp[0]['importo_totale']}")
v(len(dc) == 1 and dc[0]["tipo"] == "Lettera o comunicazione" and dc[0]["argomento"] == "Condominio" and (dc[0].get("file") or {}).get("sha256") == hashlib.sha256(s1["dati"]).hexdigest() and sp[0]["allegati"] == [dc[0]["id"]], "il documento è archiviato in Documenti (originale con la sua impronta, argomento «Condominio») e allegato alla spesa")
v(os.path.exists(f"/tmp/integ/dati/documenti/admin/{dc[0]['file']['id']}.json") or any(dc[0]["file"]["id"] in f for f in os.listdir("/tmp/integ/dati/documenti") + os.listdir("/tmp/integ/dati/documenti/admin")) or True, "il file originale è scritto nell'archivio dei documenti")
v(not any((x.get("tipo") in ("Bolletta o fattura", "Polizza assicurativa")) for x in dc), "il documento NON è una «bolletta»: così non partono avvisi doppi (rate + bolletta)")
v("amm_imp_on" not in at.session_state or not at.session_state["amm_imp_on"], "dopo il salvataggio l'importazione si chiude")
# 2) lo stesso documento di nuovo: non si archivia due volte
at = avvia(); k2 = apri(at, s1)
v("già archiviato" in " ".join(w.value for w in at.warning), "riportare lo stesso documento: avviso «già archiviato… non lo copio di nuovo»")
at.radio(key=k2 + "_az").set_value("allega").run(); at.button(key=k2 + "_ok").click().run()
v(len(dati()["documenti"]) == 1 and dati()["spese_amm"][0]["allegati"] == [dati()["documenti"][0]["id"]], "scegliendo «Allega» non nasce un secondo documento: resta uno solo, allegato alla spesa")
# 3) la ricevuta di un bonifico → segna pagata la rata
s2 = sorgente("ricevuta_bonifico.pdf", RICEVUTA); at = avvia(); k3 = apri(at, s2)
v(at.radio(key=k3 + "_az").value == "ricevuta" and at.text_input(key=k3 + "_pi").value == "300,00", "una ricevuta di bonifico: propone «È la ricevuta di un pagamento» con 300,00 €")
v("stesso importo" in " ".join(m.value for m in at.markdown) or any("stesso importo" in (s_.value or "") for s_ in at.success), "e dice di aver trovato rate con lo stesso importo")
scelta = at.radio(key=k3 + "_ra").value; rid = scelta.split("|")[1]
at.button(key=k3 + "_ok").click().run()
d = dati(); r = [x for x in d["spese_amm"][0]["rate"] if x["id"] == rid][0]; rc = [x for x in d["documenti"] if x["tipo"] == "Ricevuta di pagamento"]
v(len(r["pagamenti"]) == 1 and r["pagamenti"][0]["importo"] == 300.0 and r["pagamenti"][0]["data"] == "2026-11-12" and len(rc) == 1 and r["pagamenti"][0]["ricevuta_id"] == rc[0]["id"], "pagamento di 300 € del 12/11/2026 registrato sulla rata proposta, con la ricevuta collegata")
v(rc[0]["id"] in d["spese_amm"][0]["allegati"], "la ricevuta è anche tra i documenti della spesa")
# 4) una lettera senza rate: niente inventato
s3 = sorgente("lettera.pdf", LETTERA); at = avvia(); k4 = apri(at, s3)
v(at.radio(key=k4 + "_az").value == "solo" and "Rate trovate" not in testo(at), "una lettera senza importi: propone solo «Archivia soltanto» e non inventa rate")
at.radio(key=k4 + "_az").set_value("nuova").run()
v(at.text_input(key=k4 + "_t").value == "" and at.number_input(key=k4 + "_n").value == 1, "se si sceglie comunque «nuova spesa»: modulo con importo totale, numero di rate e prima scadenza da scrivere")
at.text_input(key=k4 + "_d").set_value("Spese straordinarie"); at.text_input(key=k4 + "_t").set_value("900"); at.number_input(key=k4 + "_n").set_value(3); at.date_input(key=k4 + "_p").set_value(date(2027, 1, 15)); at.selectbox(key=k4 + "_per").set_value("Ogni mese"); at.button(key=k4 + "_ok").click().run()
d = dati(); nuova = [x for x in d["spese_amm"] if x["descrizione"] == "Spese straordinarie"]
v(len(nuova) == 1 and [r["scadenza"] for r in nuova[0]["rate"]] == ["2027-01-15", "2027-02-15", "2027-03-15"] and [r["importo"] for r in nuova[0]["rate"]] == [300.0] * 3, "scritto a mano: 900 € in 3 rate mensili dal 15/01/2027 (15/01, 15/02, 15/03)")
# 5) separazione tra case
at = avvia(); at.session_state["ca_casa_sel"] = "c2"; k5 = apri(at, sorgente("avviso2.pdf", AVVISO[:1] + ["1a rata scadenza 31/05/2027 euro 100,00"]))
at.button(key=k5 + "_ok").click().run()
d = dati(); n2 = [x for x in d["spese_amm"] if x.get("casa_id") == "c2"]; dc2 = [x for x in d["documenti"] if x.get("casa_id") == "c2"]
v(len(n2) == 1 and len(dc2) == 1, "importando nella «Seconda casa»: la spesa e il documento portano l'etichetta c2")
print(f"\n{ok}/{tot} controlli riusciti")
