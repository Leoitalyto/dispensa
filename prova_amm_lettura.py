"""Prova della LETTURA degli avvisi di pagamento condominiali (rate, bollettino, ricevuta) — solo testo, senza Streamlit.  python3 prova_amm_lettura.py [cartella dei moduli]"""
import sys, os, types
from datetime import date
cart = sys.argv[1] if len(sys.argv) > 1 else "/tmp/prod_sim"
sys.modules["streamlit"] = types.ModuleType("streamlit")
g = {"__name__": "amm"}
exec(compile(open(os.path.join(cart, "casa_amministrazione.py"), encoding="utf-8").read(), "amm", "exec"), g)
ok = tot = 0
def v(c, t):
    global ok, tot; tot += 1; ok += bool(c); print(("OK      " if c else "FALLITO ") + t)
L = g["amm_leggi_avviso"]; O = date(2026, 11, 13)
A = """AVVISO DI PAGAMENTO RATE CONDOMINIALI - ESERCIZIO 2026
Condominio Aurora - Via Mare 1, Torino
Amministratore: Rossi Mario - Studio Rossi
Piano rate:
1ª rata  scadenza 31/01/2026  € 300,00
2ª rata  scadenza 30/04/2026  € 300,00
3ª rata  scadenza 31/07/2026  € 300,00
4ª rata  scadenza 31/10/2026  € 300,00
Totale da versare € 1.200,00
IBAN: IT60 X054 2811 1010 0000 0123 456"""
r = L(A, O)
v(r["tipo"] == "avviso" and len(r["rate"]) == 4 and [x[2] for x in r["rate"]] == [1, 2, 3, 4] and r["rate"][1][0] == date(2026, 4, 30) and r["rate"][1][1] == 300.0, "avviso con «1ª rata scadenza … € 300,00»: 4 rate con numero, data e importo")
v(r["totale"] == 1200.0 and r["affidabilita"] == "alta" and not r["note"] and r["iban"] == "IT60X0542811101000000123456", "totale 1.200,00 letto e uguale alla somma; affidabilità alta; IBAN valido riconosciuto")
v(r["descrizione"] == "Rate condominio 2026" and r["categoria"] == "Spese condominiali ordinarie", "descrizione e categoria proposte")
B = """Condominio Parco Verde
Rata n. 2 di 4
Scadenza 15 dicembre 2026 importo euro 250,00
Rata n. 3 di 4
scade il 15/03/2027
importo € 250,00"""
r = L(B, O)
v(len(r["rate"]) == 2 and r["rate"][0][0] == date(2026, 12, 15) and r["rate"][0][1] == 250.0 and r["rate"][1][0] == date(2027, 3, 15) and r["n_dichiarato"] == 4, "«Rata n. 2 di 4 … 15 dicembre 2026» (mese scritto a parole) e dati su due righe: 2 rate; il documento dice 4")
v(any("4 rate" in n for n in r["note"]), "e lo segnala: «Il documento parla di 4 rate, io ne ho trovate 2»")
C = """Rata   Scadenza     Importo
1      10/02/2026   150,00
2      10/05/2026   150,00
3      10/08/2026   150,00
Totale  450,00"""
r = L(C, O)
v(len(r["rate"]) == 3 and r["totale"] == 450.0 and r["rate"][2][0] == date(2026, 8, 10), "tabella «Rata Scadenza Importo» con righe «1 10/02/2026 150,00»: 3 rate e totale")
D = """BOLLETTINO CONDOMINIO
Importo da pagare € 87,50
Scadenza 20/12/2026
Spese di riscaldamento"""
r = L(D, O)
v(r["tipo"] == "avviso" and len(r["rate"]) == 1 and r["rate"][0][0] == date(2026, 12, 20) and r["rate"][0][1] == 87.5 and r["categoria"] == "Riscaldamento", "bollettino con una sola scadenza: una rata di 87,50 € al 20/12/2026, categoria «Riscaldamento»")
E = """RICEVUTA DI PAGAMENTO
Bonifico eseguito il 12/11/2026
Importo € 300,00
Causale: 2ª rata condominio Aurora
CRO 12345678901"""
r = L(E, O)
v(r["tipo"] == "ricevuta" and r["pagamento"] == {"data": date(2026, 11, 12), "importo": 300.0}, "ricevuta di bonifico: riconosciuta come pagamento di 300,00 € del 12/11/2026 (la «2ª rata» nella causale non crea una rata)")
F = """AVVISO LAVORI STRAORDINARI FACCIATA
1ª rata 28/02/2027 € 1.500,50
2ª rata 30/06/2027 € 1.500,50
Totale € 3.001,00"""
r = L(F, O)
v(r["categoria"] == "Rata straordinaria o lavori" and r["descrizione"] == "Lavori straordinari 2027" and r["rate"][0][1] == 1500.5 and abs(sum(x[1] for x in r["rate"]) - 3001) < 0.01, "lavori straordinari: categoria e descrizione adatte, importi con migliaia «1.500,50»")
G = """Piano rate
1ª rata 31/01/2026 € 300,00
2ª rata 30/04/2026 € 300,00
Totale € 1.000,00"""
r = L(G, O)
v(r["affidabilita"] == "media" and any("non è uguale al totale" in n for n in r["note"]), "se la somma delle rate non torna col totale: affidabilità media e avviso")
v(L("", O)["tipo"] == "altro" and L("Lettera dell'amministratore: riunione di condominio il 3 ottobre", O)["rate"] == [], "testo vuoto o senza rate: nessuna proposta inventata")
v(L("1ª rata 31/01/1980 € 300,00\\n2ª rata 31/01/2099 € 300,00", O)["rate"] == [], "date impossibili (1980, 2099) scartate")
p = g["amm_parse_data"]
v([p("15/12/2026"), p("15-12-26"), p("15.12.2026"), p("2026-12-15"), p("15 dicembre 2026"), p("31/02/2026"), p("boh")] == [date(2026, 12, 15)] * 5 + [None, None], "date lette in 5 modi; 31/02 e testo non sono date")
# la spesa da rate già decise
S = g["amm_crea_spesa_da_rate"]("Rate condominio 2026", "Altro", [(date(2026, 4, 30), 300.0), (date(2026, 1, 31), 300.0), (date(2026, 7, 31), 299.99)])
v([x["n"] for x in S["rate"]] == [1, 2, 3] and S["rate"][0]["scadenza"] == "2026-01-31" and S["importo_totale"] == 899.99 and len({x["scadenza"] for x in S["rate"]}) == 3, "spesa creata da rate già decise: ordinate per data, numerate 1-2-3, totale 899,99")
# ricevute: quale rata?
S2 = g["amm_crea_spesa"]("Rate", "Altro", 1200, 4, date(2026, 1, 31), 3)
g["amm_registra_pagamento"](S2, S2["rate"][0]["id"], "300", "2026-01-30")
c = g["amm_trova_rata_per_ricevuta"]([S2], 300.0, "2026-04-29")
v(c and c[0][2] is True and c[0][1]["n"] == 2 and all(x[1]["n"] != 1 for x in c), "ricevuta di 300 € del 29/04: propone la rata 2 (30/04), la più vicina con lo stesso importo; la rata 1 già pagata non compare")
v(g["amm_trova_rata_per_ricevuta"]([S2], 123.45, "2026-04-29")[0][2] is False and g["amm_trova_rata_per_ricevuta"]([S2], 999.0, None) == [] and g["amm_trova_rata_per_ricevuta"]([S2], None, None) == [], "importo diverso: solo pagamento parziale possibile; importo più alto di ogni residuo o assente: nessuna proposta")
print(f"\n{ok}/{tot} controlli riusciti")
