"""Orari del riscaldamento decisi da VitaMemo (fasce giornaliere) — il «motore», senza Streamlit.

Lo stesso file sta in due posti, IDENTICO: nell'app (dispensa) e nel repository dei dati (dispensa-dati), dove lo usa
domotica_orari.py, il programma che GitHub esegue ogni mezz'ora anche ad app chiusa.

Come funziona (pensato per sbagliare il meno possibile):
  · all'inizio di ogni fascia si manda al termostato UN solo comando: «manuale a X° fino alla fine della fascia».
    Alla fine della fascia è il termostato stesso a tornare da solo al suo programma: se un controllo arriva in ritardo
    o salta, la fascia finisce comunque all'ora giusta;
  · fuori dalle fasce: o il programma del termostato (non si manda niente), o una temperatura ridotta
    («manuale a Y° fino all'inizio della prossima fascia»);
  · ogni passaggio ha una «chiave»: si manda una volta sola. Se nel frattempo qualcuno cambia la temperatura a mano,
    quella scelta resta valida fino al passaggio successivo (non viene ricoperta ogni mezz'ora).

Formato (dentro d["casa"]["domotica"]["orari"][id_apparecchio]):
  {"attivo": True,
   "fuori": {"tipo": "programma" | "temp", "temp": 16.0},
   "giorni": {"0": [{"dalle": "06:00", "alle": "08:30", "temp": 20.0}, …], …, "6": […]}}     # 0 = lunedì
"""
import datetime as _odt

OR_GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
OR_GIORNI_BREVI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
OR_ORARI = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]          # passi di mezz'ora (il controllo è ogni mezz'ora)
OR_ORARI_FINE = OR_ORARI[1:] + ["24:00"]
OR_TEMP_MIN, OR_TEMP_MAX = 5.0, 30.0
OR_TOLLERANZA_MIN = 3                                                          # un controllo alle 05:58 vale già per le 06:00
OR_RISPARMIO_PER_GRADO = 0.07                                                  # regola pratica: ~7% in meno per ogni grado in meno


def or_vuoto():
    return {"attivo": False, "fuori": {"tipo": "programma", "temp": 16.0}, "giorni": {str(i): [] for i in range(7)}}


def or_normalizza(prog):
    p = or_vuoto()
    p.update({k: v for k, v in (prog or {}).items() if k in ("attivo", "fuori", "giorni")})
    p["fuori"] = dict(or_vuoto()["fuori"], **(p.get("fuori") or {}))
    p["giorni"] = {str(i): list(((prog or {}).get("giorni") or {}).get(str(i)) or []) for i in range(7)}
    return p


def _or_min(hhmm):
    h, m = str(hhmm).split(":")
    return int(h) * 60 + int(m)


def or_controlla_giorno(fasce):
    """Errori di un giorno, in italiano (lista vuota = tutto giusto)."""
    err = []
    ordinate = sorted(fasce, key=lambda f: _or_min(f["dalle"]))
    for i, f in enumerate(ordinate, start=1):
        a, b = _or_min(f["dalle"]), _or_min(f["alle"])
        if b <= a:
            err.append(f"la fascia {f['dalle']}–{f['alle']} finisce prima di cominciare")
        try:
            t = float(f.get("temp"))
            if not OR_TEMP_MIN <= t <= OR_TEMP_MAX:
                err.append(f"la fascia {f['dalle']}–{f['alle']} ha {t:g}°: scegli tra {OR_TEMP_MIN:g}° e {OR_TEMP_MAX:g}°")
        except Exception:
            err.append(f"la fascia {f['dalle']}–{f['alle']} non ha la temperatura")
        if i < len(ordinate) and _or_min(ordinate[i]["dalle"]) < b:
            err.append(f"le fasce {f['dalle']}–{f['alle']} e {ordinate[i]['dalle']}–{ordinate[i]['alle']} si sovrappongono")
    return err


def or_fasce_data(prog, giorno):
    """Le fasce di una data: [(inizio, fine, temperatura)] in ordine."""
    out = []
    for f in (prog.get("giorni") or {}).get(str(giorno.weekday())) or []:
        try:
            a = _odt.datetime.combine(giorno, _odt.time()) + _odt.timedelta(minutes=_or_min(f["dalle"]))
            b = _odt.datetime.combine(giorno, _odt.time()) + _odt.timedelta(minutes=_or_min(f["alle"]))
            if b > a:
                out.append((a, b, float(f["temp"])))
        except Exception:
            continue
    return sorted(out)


def _or_fasce_vicine(prog, adesso):
    """Le fasce da ieri a fra 8 giorni (per trovare quella in corso, la precedente e la prossima)."""
    out = []
    for d in range(-1, 9):
        out += or_fasce_data(prog, adesso.date() + _odt.timedelta(days=d))
    # due fasce attaccate con la stessa temperatura diventano una sola (es. 22:00–24:00 e 00:00–06:00)
    unite = []
    for a, b, t in sorted(out):
        if unite and unite[-1][1] == a and unite[-1][2] == t:
            unite[-1] = (unite[-1][0], b, t)
        else:
            unite.append((a, b, t))
    return unite


def or_obiettivo(prog, adesso):
    """Cosa deve fare il termostato adesso. None = niente da fare (orari spenti, oppure fuori fascia col programma del termostato)
    Altrimenti {"chiave", "tipo": "fascia"|"ridotta"|"programma", "temp", "fino", "descr"}."""
    prog = or_normalizza(prog)
    if not prog.get("attivo"):
        return None
    ora = adesso + _odt.timedelta(minutes=OR_TOLLERANZA_MIN)
    fasce = _or_fasce_vicine(prog, adesso)
    for a, b, t in fasce:
        if a <= ora < b:
            return {"chiave": f"F|{a:%Y-%m-%dT%H:%M}|{b:%Y-%m-%dT%H:%M}|{t:g}", "tipo": "fascia", "temp": t, "fino": b,
                    "descr": f"{t:g}° fino alle {b:%H:%M}".replace(".", ",")}
    prima = max((b for a, b, t in fasce if b <= ora), default=None)
    dopo = min((a for a, b, t in fasce if a > ora), default=None)
    inizio = f"{prima:%Y-%m-%dT%H:%M}" if prima else "-"
    if prog["fuori"].get("tipo") == "temp":
        t = float(prog["fuori"].get("temp") or 16.0)
        return {"chiave": f"R|{inizio}|{dopo:%Y-%m-%dT%H:%M}|{t:g}" if dopo else f"R|{inizio}|-|{t:g}", "tipo": "ridotta", "temp": t, "fino": dopo,
                "descr": (f"ridotta {t:g}°" + (f" fino alle {dopo:%H:%M}" if dopo else "")).replace(".", ",")}
    return {"chiave": f"P|{inizio}", "tipo": "programma", "temp": None, "fino": dopo, "descr": "programma del termostato"}


def or_prossimo_cambio(prog, adesso):
    """(quando, testo) del prossimo passaggio, per mostrarlo nell'app."""
    prog = or_normalizza(prog)
    if not prog.get("attivo"):
        return None
    ora = adesso + _odt.timedelta(minutes=OR_TOLLERANZA_MIN)
    for a, b, t in _or_fasce_vicine(prog, adesso):
        if a <= ora < b:
            dopo = "temperatura ridotta" if prog["fuori"].get("tipo") == "temp" else "programma del termostato"
            return b, f"alle {b:%H:%M} si passa a: {dopo}"
        if a > ora:
            quando = "oggi" if a.date() == adesso.date() else ("domani" if a.date() == adesso.date() + _odt.timedelta(days=1) else OR_GIORNI[a.weekday()].lower())
            return a, f"{quando} alle {a:%H:%M} → {t:g}°".replace(".", ",")
    return None


def or_stima(prog):
    """Ore di comfort a settimana, temperatura media e risparmio stimato rispetto a tenere sempre la temperatura più alta."""
    prog = or_normalizza(prog)
    ore, gradi_ore, alta = 0.0, 0.0, None
    for i in range(7):
        for f in prog["giorni"][str(i)]:
            try:
                h = (_or_min(f["alle"]) - _or_min(f["dalle"])) / 60
                t = float(f["temp"])
            except Exception:
                continue
            if h > 0:
                ore += h
                gradi_ore += h * t
                alta = t if alta is None else max(alta, t)
    if alta is None:
        return None
    ridotta = float(prog["fuori"].get("temp") or 16.0) if prog["fuori"].get("tipo") == "temp" else None
    out = {"ore_comfort": ore, "ore_settimana": 168.0, "alta": alta, "ridotta": ridotta}
    if ridotta is not None:
        media = (gradi_ore + (168 - ore) * ridotta) / 168
        out["media"] = media
        out["risparmio"] = max(0.0, min(0.6, (alta - media) * OR_RISPARMIO_PER_GRADO))
    return out


def or_corpo_manuale(temp, fino, adesso, funzione="heating", programma=1):
    """Il comando per Legrand (lo stesso che manda l'app): manuale a «temp» fino a «fino» (None = finché non si cambia)."""
    fmt = "%Y-%m-%dT%H:%M:%S"
    corpo = {"function": funzione or "heating", "mode": "manual", "setPoint": {"value": f"{float(temp):.1f}", "unit": "°C"}}
    if fino is not None:
        corpo["activationTime"] = adesso.replace(microsecond=0).strftime(fmt) + "/" + fino.replace(second=0, microsecond=0).strftime(fmt)
    else:
        corpo["programs"] = [{"number": int(programma or 1)}]
    return corpo


OR_MODELLI = {
    "🏢 Lavoro fuori casa": {"0-4": [("06:00", "08:00", 20.0), ("17:30", "22:30", 20.0)], "5-6": [("08:00", "23:00", 20.0)]},
    "🏠 Sempre a casa": {"0-6": [("07:00", "13:00", 20.0), ("13:00", "17:00", 19.0), ("17:00", "22:30", 20.5)]},
    "🌙 Solo mattina e sera": {"0-6": [("06:30", "08:30", 20.0), ("18:00", "22:00", 20.0)]},
}


def or_da_modello(nome):
    p = or_vuoto()
    for giorni, fasce in OR_MODELLI[nome].items():
        a, b = (int(x) for x in giorni.split("-"))
        for g in range(a, b + 1):
            p["giorni"][str(g)] = [{"dalle": x, "alle": y, "temp": t} for x, y, t in fasce]
    return p
