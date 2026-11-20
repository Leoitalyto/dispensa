# -*- coding: utf-8 -*-
"""DONAZIONI A CHI HA FATTO L'APP (PayPal), con la memoria di chi ha donato.

COSA FA
 1. Un badge «Dona con PayPal» (nella lingua della persona) in alto, accanto al pulsante del menu, su ogni pagina dopo l'accesso.
    Emette onde di luce dal suo contorno, come un sasso che cade nell'acqua. Toccandolo si apre la finestra della donazione.
 2. Ogni donazione viene salvata PER SEMPRE nel file privato «donazioni.json» (nell'archivio dei dati, come utenti.json):
    chi, quando, quanto, se è verificata. Non si cancella da sola.
 3. Nell'elenco degli utenti (scheda «Utenti») chi ha donato ha il logo tondo PayPal nella riga principale e, aprendo la riga,
    vede tutte le sue donazioni. Chi gestisce può anche registrare a mano una donazione o confermare quelle «da confermare».
 4. L'utente stesso, nella finestra, vede il riepilogo delle proprie donazioni e un grazie.

DUE MODI (si sceglie con i «Secrets» di Streamlit, niente nel codice):
 A) AUTOMATICO E VERIFICATO (consigliato): conto PayPal Business gratuito + «App» sviluppatore PayPal →
        [paypal]
        client_id = "..."
        secret = "..."
        mode = "live"            # «sandbox» per provare senza soldi veri
    L'app crea l'ordine, l'utente paga su PayPal, torna all'app e l'app incassa e registra da sola: nessuno può inventarsi una donazione.
 B) SEMPLICE: solo il nome del tuo link PayPal.Me →
        paypal_me = "tuonome"
    L'utente paga su PayPal.Me e tocca «Ho completato la donazione»: resta «da confermare» finché chi gestisce non la conferma.
 Senza nessuno dei due il badge non compare (niente di rotto).
Non costa niente all'app: PayPal trattiene solo la sua commissione sulle donazioni ricevute. Caricato dopo vitamemo_lingua.py."""
import html as _h_dn
import json as _json_dn
import time as _time_dn
import uuid as _uuid_dn
from datetime import datetime as _dt_dn

import streamlit as st

DN_MIN, DN_MAX = 1.0, 500.0
DN_PRESET = (3, 5, 10, 20)
DN_FILE = "donazioni.json"
DN_MARCA = "⁣⁤⁣"                                       # segno invisibile messo nella riga dell'elenco utenti: serve a mettere il logo
_dn_disegnato = False


# ---------------------------------------------------------------------------------------------------------------------
# testi (8 lingue)
# ---------------------------------------------------------------------------------------------------------------------
_DN_T = {
    "it": dict(titolo="Sostieni VitaMemo", intro="VitaMemo è gratuita. Se ti è utile puoi offrirmi una donazione libera con PayPal: aiuta a mantenerla e a migliorarla. Grazie!",
               storia="Le tue donazioni", totale="Totale", importo="Scegli l'importo", altro="Altro importo", crea="Continua", vai="Apri PayPal",
               nota_api="Si apre PayPal in una nuova scheda. Dopo il pagamento chiudi quella scheda e torna qui.",
               me_nota="Dopo aver pagato su PayPal tocca qui sotto: la donazione resta «da confermare» finché chi gestisce l'app non la controlla.",
               me_fatto="Ho completato la donazione", da_conf="da confermare", ok_reg="Registrata, grazie!",
               grazie_t="Grazie di cuore!", grazie_x="La tua donazione di {imp} è stata ricevuta.", annullata="Donazione annullata: non è stato addebitato niente.",
               errore="Non sono riuscito a completare la donazione ({e}). Se PayPal non ti ha confermato il pagamento, non è stato addebitato niente.",
               torna="Torna a VitaMemo", nessuna="Non hai ancora fatto donazioni.", aria="Dona con PayPal"),
    "en": dict(titolo="Support VitaMemo", intro="VitaMemo is free. If it is useful to you, you can make a free donation with PayPal: it helps keep it running and improve it. Thank you!",
               storia="Your donations", totale="Total", importo="Choose the amount", altro="Other amount", crea="Continue", vai="Open PayPal",
               nota_api="PayPal opens in a new tab. After paying, close that tab and come back here.",
               me_nota="After paying on PayPal, tap below: the donation stays “to be confirmed” until the app manager checks it.",
               me_fatto="I have completed the donation", da_conf="to be confirmed", ok_reg="Saved, thank you!",
               grazie_t="Thank you so much!", grazie_x="Your donation of {imp} has been received.", annullata="Donation cancelled: nothing was charged.",
               errore="I could not complete the donation ({e}). If PayPal did not confirm the payment, nothing was charged.",
               torna="Back to VitaMemo", nessuna="You have not made any donations yet.", aria="Donate with PayPal"),
    "es": dict(titolo="Apoya VitaMemo", intro="VitaMemo es gratuita. Si te resulta útil puedes hacerme una donación libre con PayPal: ayuda a mantenerla y mejorarla. ¡Gracias!",
               storia="Tus donaciones", totale="Total", importo="Elige el importe", altro="Otro importe", crea="Continuar", vai="Abrir PayPal",
               nota_api="PayPal se abre en una pestaña nueva. Después de pagar, cierra esa pestaña y vuelve aquí.",
               me_nota="Después de pagar en PayPal, toca abajo: la donación queda «por confirmar» hasta que quien gestiona la app la compruebe.",
               me_fatto="He completado la donación", da_conf="por confirmar", ok_reg="¡Registrada, gracias!",
               grazie_t="¡Muchas gracias!", grazie_x="Hemos recibido tu donación de {imp}.", annullata="Donación cancelada: no se ha cobrado nada.",
               errore="No he podido completar la donación ({e}). Si PayPal no te ha confirmado el pago, no se ha cobrado nada.",
               torna="Volver a VitaMemo", nessuna="Todavía no has hecho donaciones.", aria="Donar con PayPal"),
    "fr": dict(titolo="Soutenir VitaMemo", intro="VitaMemo est gratuite. Si elle t'est utile, tu peux me faire un don libre avec PayPal : cela aide à la maintenir et à l'améliorer. Merci !",
               storia="Tes dons", totale="Total", importo="Choisis le montant", altro="Autre montant", crea="Continuer", vai="Ouvrir PayPal",
               nota_api="PayPal s'ouvre dans un nouvel onglet. Après le paiement, ferme cet onglet et reviens ici.",
               me_nota="Après avoir payé sur PayPal, touche ci-dessous : le don reste « à confirmer » tant que la personne qui gère l'appli ne l'a pas vérifié.",
               me_fatto="J'ai terminé le don", da_conf="à confirmer", ok_reg="Enregistré, merci !",
               grazie_t="Merci de tout cœur !", grazie_x="Ton don de {imp} a bien été reçu.", annullata="Don annulé : rien n'a été débité.",
               errore="Je n'ai pas pu terminer le don ({e}). Si PayPal ne t'a pas confirmé le paiement, rien n'a été débité.",
               torna="Retour à VitaMemo", nessuna="Tu n'as pas encore fait de dons.", aria="Faire un don avec PayPal"),
    "de": dict(titolo="VitaMemo unterstützen", intro="VitaMemo ist kostenlos. Wenn sie dir nützt, kannst du mir eine freiwillige Spende per PayPal geben: Sie hilft, die App zu erhalten und zu verbessern. Danke!",
               storia="Deine Spenden", totale="Summe", importo="Betrag wählen", altro="Anderer Betrag", crea="Weiter", vai="PayPal öffnen",
               nota_api="PayPal öffnet sich in einem neuen Tab. Schließe ihn nach der Zahlung und komm hierher zurück.",
               me_nota="Tippe nach der Zahlung bei PayPal unten: Die Spende bleibt „zu bestätigen“, bis die verwaltende Person sie geprüft hat.",
               me_fatto="Ich habe die Spende abgeschlossen", da_conf="zu bestätigen", ok_reg="Gespeichert, danke!",
               grazie_t="Herzlichen Dank!", grazie_x="Deine Spende von {imp} ist eingegangen.", annullata="Spende abgebrochen: Es wurde nichts abgebucht.",
               errore="Die Spende konnte nicht abgeschlossen werden ({e}). Wenn PayPal die Zahlung nicht bestätigt hat, wurde nichts abgebucht.",
               torna="Zurück zu VitaMemo", nessuna="Du hast noch nicht gespendet.", aria="Mit PayPal spenden"),
    "pt": dict(titolo="Apoie o VitaMemo", intro="O VitaMemo é gratuito. Se for útil para ti, podes fazer-me uma doação livre com o PayPal: ajuda a mantê-lo e a melhorá-lo. Obrigado!",
               storia="As tuas doações", totale="Total", importo="Escolhe o valor", altro="Outro valor", crea="Continuar", vai="Abrir o PayPal",
               nota_api="O PayPal abre num novo separador. Depois de pagar, fecha esse separador e volta aqui.",
               me_nota="Depois de pagar no PayPal, toca abaixo: a doação fica «por confirmar» até quem gere a aplicação a verificar.",
               me_fatto="Concluí a doação", da_conf="por confirmar", ok_reg="Registada, obrigado!",
               grazie_t="Muito obrigado!", grazie_x="A tua doação de {imp} foi recebida.", annullata="Doação cancelada: não foi cobrado nada.",
               errore="Não consegui concluir a doação ({e}). Se o PayPal não te confirmou o pagamento, não foi cobrado nada.",
               torna="Voltar ao VitaMemo", nessuna="Ainda não fizeste doações.", aria="Doar com o PayPal"),
    "ro": dict(titolo="Susține VitaMemo", intro="VitaMemo este gratuită. Dacă îți e de folos, poți face o donație liberă prin PayPal: ajută la menținerea și îmbunătățirea ei. Mulțumesc!",
               storia="Donațiile tale", totale="Total", importo="Alege suma", altro="Altă sumă", crea="Continuă", vai="Deschide PayPal",
               nota_api="PayPal se deschide într-o filă nouă. După plată, închide acea filă și revino aici.",
               me_nota="După ce ai plătit pe PayPal, atinge mai jos: donația rămâne „de confirmat” până o verifică persoana care administrează aplicația.",
               me_fatto="Am finalizat donația", da_conf="de confirmat", ok_reg="Înregistrată, mulțumesc!",
               grazie_t="Mulțumesc din inimă!", grazie_x="Donația ta de {imp} a fost primită.", annullata="Donație anulată: nu s-a debitat nimic.",
               errore="Nu am reușit să finalizez donația ({e}). Dacă PayPal nu ți-a confirmat plata, nu s-a debitat nimic.",
               torna="Înapoi la VitaMemo", nessuna="Nu ai făcut încă donații.", aria="Donează cu PayPal"),
    "ar": dict(titolo="ادعم VitaMemo", intro="تطبيق VitaMemo مجاني. إذا كان مفيدًا لك يمكنك تقديم تبرع حر عبر PayPal: يساعد على استمراره وتحسينه. شكرًا لك!",
               storia="تبرعاتك", totale="المجموع", importo="اختر المبلغ", altro="مبلغ آخر", crea="متابعة", vai="افتح PayPal",
               nota_api="يفتح PayPal في تبويب جديد. بعد الدفع أغلق ذلك التبويب وارجع إلى هنا.",
               me_nota="بعد الدفع في PayPal اضغط في الأسفل: يبقى التبرع «بانتظار التأكيد» حتى يراجعه مسؤول التطبيق.",
               me_fatto="أكملت التبرع", da_conf="بانتظار التأكيد", ok_reg="تم التسجيل، شكرًا!",
               grazie_t="شكرًا جزيلًا!", grazie_x="تم استلام تبرعك بقيمة {imp}.", annullata="أُلغي التبرع: لم يُخصم أي مبلغ.",
               errore="لم أتمكن من إكمال التبرع ({e}). إذا لم يؤكد PayPal الدفع فلم يُخصم أي مبلغ.",
               torna="العودة إلى VitaMemo", nessuna="لم تقم بأي تبرع بعد.", aria="تبرع عبر PayPal"),
}


def _dn_lg():
    try:
        lg = st.session_state.get("lang", "it")
    except Exception:
        lg = "it"
    return lg if lg in _DN_T else "it"


def _dn_t(chiave, **kw):
    s = _DN_T[_dn_lg()].get(chiave) or _DN_T["it"][chiave]
    return s.format(**kw) if kw else s


def _dn_eur(x, valuta="EUR"):
    sym = {"EUR": "€", "USD": "$", "GBP": "£"}.get(valuta, valuta)
    s = f"{float(x):.2f}"
    if _dn_lg() not in ("en", "ar"):
        s = s.replace(".", ",")
    return f"{s} {sym}"


# ---------------------------------------------------------------------------------------------------------------------
# configurazione (Secrets)
# ---------------------------------------------------------------------------------------------------------------------
def _dn_secret(nome, default=None):
    try:
        return st.secrets[nome]
    except Exception:
        return default


def dn_conf():
    """None se le donazioni non sono configurate; altrimenti un dizionario con il modo: «api» (automatico) o «me» (PayPal.Me)."""
    p = _dn_secret("paypal")
    try:
        p = dict(p) if p else {}
    except Exception:
        p = {}
    me = str(p.get("me") or _dn_secret("paypal_me") or "").strip().strip("/")
    if me.lower().startswith("http"):
        me = me.rstrip("/").split("/")[-1]
    me = me.replace("paypal.me/", "").replace("www.", "")
    valuta = str(p.get("valuta") or "EUR").upper()
    cid, sec = str(p.get("client_id") or "").strip(), str(p.get("secret") or "").strip()
    modo = str(p.get("mode") or "live").strip().lower()
    base = str(p.get("api_base") or ("https://api-m.sandbox.paypal.com" if modo == "sandbox" else "https://api-m.paypal.com")).rstrip("/")
    if cid and sec:
        return {"modo": "api", "cid": cid, "sec": sec, "base": base, "valuta": valuta, "me": me, "app_url": str(p.get("app_url") or "").strip()}
    if me:
        return {"modo": "me", "me": me, "valuta": valuta, "app_url": ""}
    return None


def dn_attiva():
    return dn_conf() is not None


def _dn_url_app(conf):
    u = (conf or {}).get("app_url") or ""
    if not u:
        try:
            u = str(st.context.url)
        except Exception:
            u = ""
    return u.split("?")[0].split("#")[0]


# ---------------------------------------------------------------------------------------------------------------------
# archivio delle donazioni
# ---------------------------------------------------------------------------------------------------------------------
def _dn_leggi():
    try:
        d = carica_dati(crea_archivio(), DN_FILE) or {}
    except Exception:
        d = {}
    d.setdefault("donazioni", [])
    d.setdefault("ordini", {})
    return d


def _dn_scrivi(fn, messaggio):
    salva_file(DN_FILE, fn, messaggio)


def dn_di_utente(uid):
    v = [x for x in _dn_leggi().get("donazioni", []) if x.get("uid") == uid]
    return sorted(v, key=lambda x: x.get("data", ""), reverse=True)


def dn_marcatore(uid):
    """Segno invisibile da mettere nella riga dell'utente se ha fatto almeno una donazione (serve a mostrare il logo)."""
    try:
        return DN_MARCA if dn_di_utente(uid) else ""
    except Exception:
        return ""


def _dn_registra(uid, nome, importo, valuta, stato, fonte, id_=None, extra=None):
    voce = {"id": id_ or _uuid_dn.uuid4().hex[:12], "uid": uid, "nome": nome, "importo": round(float(importo), 2), "valuta": valuta,
            "data": _dt_dn.now().isoformat(timespec="minutes"), "stato": stato, "fonte": fonte}
    if extra:
        voce.update(extra)

    def f(d):
        d.setdefault("donazioni", [])
        if not any(x.get("id") == voce["id"] for x in d["donazioni"]):             # la stessa donazione non si registra due volte
            d["donazioni"].append(voce)
    _dn_scrivi(f, "Donazione")
    return voce


# ---------------------------------------------------------------------------------------------------------------------
# PayPal (modo automatico)
# ---------------------------------------------------------------------------------------------------------------------
def _dn_http(conf, metodo, percorso, **kw):
    import requests as _rq
    r = _rq.request(metodo, conf["base"] + percorso, timeout=25, **kw)
    return r


def _dn_token(conf):
    r = _dn_http(conf, "POST", "/v1/oauth2/token", auth=(conf["cid"], conf["sec"]), data={"grant_type": "client_credentials"}, headers={"Accept": "application/json"})
    if r.status_code != 200:
        raise RuntimeError("accesso a PayPal non riuscito (" + str(r.status_code) + ")")
    return r.json()["access_token"]


def _dn_crea_ordine(conf, importo, uid, nome):
    tok = _dn_token(conf)
    app = _dn_url_app(conf)
    if not app:
        raise RuntimeError("indirizzo dell'app sconosciuto")
    corpo = {"intent": "CAPTURE",
             "purchase_units": [{"reference_id": uid[:60], "custom_id": uid[:120], "description": "Donazione VitaMemo",
                                 "amount": {"currency_code": conf["valuta"], "value": f"{float(importo):.2f}"}}],
             "application_context": {"brand_name": "VitaMemo", "user_action": "PAY_NOW", "shipping_preference": "NO_SHIPPING",
                                     "return_url": app + "?dn=ok", "cancel_url": app + "?dn=no"}}
    r = _dn_http(conf, "POST", "/v2/checkout/orders", json=corpo,
                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json", "PayPal-Request-Id": _uuid_dn.uuid4().hex})
    if r.status_code not in (200, 201):
        raise RuntimeError("ordine non creato (" + str(r.status_code) + ")")
    j = r.json()
    url = next((l.get("href") for l in j.get("links", []) if l.get("rel") in ("approve", "payer-action")), None)
    if not j.get("id") or not url:
        raise RuntimeError("risposta di PayPal incompleta")
    oid = j["id"]

    def f(d):
        d.setdefault("ordini", {})
        limite = _time_dn.time() - 3 * 86400
        for k in [k for k, v in d["ordini"].items() if v.get("t", 0) < limite]:
            d["ordini"].pop(k, None)
        d["ordini"][oid] = {"uid": uid, "nome": nome, "importo": round(float(importo), 2), "valuta": conf["valuta"], "t": _time_dn.time()}
    _dn_scrivi(f, "Ordine donazione")
    return url


def _dn_cattura(conf, oid):
    """Incassa l'ordine dopo che la persona ha pagato. Ritorna (importo, valuta, id_incasso). Solo ordini creati da noi."""
    ordini = _dn_leggi().get("ordini", {})
    if oid not in ordini and not any(x.get("id") == oid for x in _dn_leggi().get("donazioni", [])):
        raise RuntimeError("ordine sconosciuto")
    tok = _dn_token(conf)
    h = {"Authorization": "Bearer " + tok, "Content-Type": "application/json"}
    r = _dn_http(conf, "POST", f"/v2/checkout/orders/{oid}/capture", json={}, headers=h)
    if r.status_code == 422:                                                       # già incassato (per esempio pagina ricaricata): si rilegge
        r = _dn_http(conf, "GET", f"/v2/checkout/orders/{oid}", headers=h)
    if r.status_code not in (200, 201):
        raise RuntimeError("PayPal ha risposto " + str(r.status_code))
    j = r.json()
    if str(j.get("status")) != "COMPLETED":
        raise RuntimeError("pagamento non completato (" + str(j.get("status")) + ")")
    try:
        cap = j["purchase_units"][0]["payments"]["captures"][0]
        return float(cap["amount"]["value"]), cap["amount"]["currency_code"], cap.get("id")
    except Exception:
        o = ordini.get(oid, {})
        return float(o.get("importo", 0)), o.get("valuta", conf["valuta"]), None


def _dn_ritorno():
    """La persona torna da PayPal (?dn=ok&token=…). Incassa, registra e mostra il grazie; poi «Torna a VitaMemo»."""
    esito = st.session_state.get("_dn_esito")
    if esito is None:
        stato = st.query_params.get("dn")
        oid = st.query_params.get("token")
        conf = dn_conf()
        esito = {"ok": False, "msg": ""}
        if stato == "no":
            esito["msg"] = _dn_t("annullata")
        elif stato == "ok" and oid and conf and conf["modo"] == "api":
            try:
                gia = next((x for x in _dn_leggi().get("donazioni", []) if x.get("id") == oid), None)
                if gia:
                    imp, val = gia["importo"], gia["valuta"]
                else:
                    imp, val, cap = _dn_cattura(conf, oid)
                    o = _dn_leggi().get("ordini", {}).get(oid, {})
                    _dn_registra(o.get("uid", ""), o.get("nome", ""), imp, val, "verificata", "paypal", id_=oid, extra={"incasso": cap})

                    def f(d):
                        d.get("ordini", {}).pop(oid, None)
                    _dn_scrivi(f, "Ordine donazione chiuso")
                esito = {"ok": True, "imp": _dn_eur(imp, val), "msg": ""}
            except Exception as e:
                esito["msg"] = _dn_t("errore", e=str(e)[:120])
        else:
            esito["msg"] = _dn_t("annullata")
        st.session_state["_dn_esito"] = esito
    if "HERO" in globals():
        st.markdown(HERO, unsafe_allow_html=True)
    rtl = "direction:rtl;text-align:right;" if _dn_lg() == "ar" else ""
    if esito.get("ok"):
        st.markdown(f"<div style='{rtl}padding:18px;border-radius:18px;border:2px solid #ffc439;background:rgba(255,196,57,.12);font-size:1.05rem'>"
                    f"<div style='font-size:1.4rem;font-weight:900'>💛 {_h_dn.escape(_dn_t('grazie_t'))}</div>{_h_dn.escape(_dn_t('grazie_x', imp=esito['imp']))}</div>", unsafe_allow_html=True)
    else:
        st.warning(esito.get("msg") or _dn_t("annullata"))
    if st.button(_dn_t("torna"), type="primary", key="dn_torna"):
        st.session_state.pop("_dn_esito", None)
        st.query_params.clear()
        st.rerun()
    st.stop()


# ---------------------------------------------------------------------------------------------------------------------
# il badge in alto con le onde di luce
# ---------------------------------------------------------------------------------------------------------------------
def _dn_css_badge():
    b = (globals().get("DN_BTN") or {}).get(_dn_lg())
    if not b:
        return ""
    img, w, h = b
    larg = 120 if w / h > 4 else 112
    alt = round(larg * h / w, 1)
    # misure FISSE (larghezza e altezza in px) per il riquadro e per gli anelli: durante il cambio di pagina il contenitore può allungarsi un attimo
    # e gli anelli, se seguono il contenitore, si deformano. Così restano sempre della forma del bottone.
    dim = f"width:{larg}px;height:{alt}px;"
    return ("<style>"
            ".st-key-dn_badge{position:fixed !important;top:11px;left:46px;z-index:999995;" + dim + "max-height:" + str(alt) + "px;overflow:visible !important;margin:0 !important;padding:0 !important;gap:0 !important}"
            ".st-key-dn_badge [data-testid='stElementContainer'],.st-key-dn_badge [data-testid='stButton'],.st-key-dn_badge .stButton{width:" + str(larg) + "px !important;max-width:" + str(larg) + "px !important;height:" + str(alt) + "px !important;margin:0 !important}"
            ".st-key-dn_badge button{position:relative;z-index:2;display:block !important;" + dim + "min-height:0 !important;max-height:" + str(alt) + "px;"
            "padding:0 !important;margin:0 !important;border:0 !important;border-radius:999px !important;background:url('data:image/webp;base64," + img + "') center/100% 100% no-repeat !important;"
            "color:transparent !important;box-shadow:0 0 10px 1px rgba(255,196,57,.55) !important;cursor:pointer;animation:dn-luce 3.2s ease-in-out infinite;-webkit-tap-highlight-color:transparent}"
            ".st-key-dn_badge button p,.st-key-dn_badge button div{font-size:0 !important;color:transparent !important}"
            ".st-key-dn_badge button:active{transform:scale(.94);animation:none}"
            # le onde: anelli che partono dal contorno e si allargano svanendo, uno dopo l'altro, come i cerchi di un sasso nell'acqua
            ".st-key-dn_badge::before,.st-key-dn_badge::after{content:'';position:absolute;left:0;top:0;" + dim + "box-sizing:border-box;border-radius:999px;pointer-events:none;z-index:1;"
            "border:2px solid rgba(255,206,70,.95);box-shadow:0 0 8px 2px rgba(255,206,70,.55),inset 0 0 6px rgba(255,206,70,.4);opacity:0;animation:dn-onda 3s cubic-bezier(.2,.6,.3,1) infinite}"
            ".st-key-dn_badge::after{animation-delay:1.5s}"
            ".st-key-dn_badge [data-testid='stButton']{position:relative}"
            ".st-key-dn_badge [data-testid='stButton']::before{content:'';position:absolute;left:0;top:0;" + dim + "box-sizing:border-box;border-radius:999px;pointer-events:none;z-index:1;"
            "border:1.5px solid rgba(255,230,140,.9);opacity:0;animation:dn-onda 3s cubic-bezier(.2,.6,.3,1) infinite;animation-delay:.75s}"
            "@keyframes dn-onda{0%{transform:scale(1);opacity:.95}70%{opacity:.25}100%{transform:scale(1.5,2.5);opacity:0}}"
            "@keyframes dn-luce{0%,100%{box-shadow:0 0 8px 0 rgba(255,196,57,.45)}50%{box-shadow:0 0 16px 4px rgba(255,214,102,.8)}}"
            "@media (max-width:991px){body:has(section[data-testid='stSidebar'][aria-expanded='true']) .st-key-dn_badge{display:none !important}}"
            "@media (min-width:992px){.st-key-dn_badge{left:calc(50% - 60px) !important}}"
            "@media (prefers-reduced-motion:reduce){.st-key-dn_badge button,.st-key-dn_badge::before,.st-key-dn_badge::after,.st-key-dn_badge [data-testid='stButton']::before{animation:none !important}}"
            "</style>")


def dn_badge():
    """Disegna il badge (una volta per pagina) se le donazioni sono attive e la persona ha fatto l'accesso."""
    global _dn_disegnato
    if _dn_disegnato:
        return
    sess = st.session_state.get("sess") or {}
    if not sess.get("uid") or sess.get("uid") == "prova" or not dn_attiva():
        return
    _dn_disegnato = True
    css = _dn_css_badge()
    if not css:
        return
    st.markdown(css, unsafe_allow_html=True)
    with st.container(key="dn_badge"):
        premuto = st.button(_dn_t("aria"), key="dn_apri")
    if premuto:
        _dn_dialogo()


def _dn_righe_storia(voci):
    righe = ""
    for x in voci:
        stato = "" if x.get("stato") == "verificata" else f" · <i>{_h_dn.escape(_dn_t('da_conf'))}</i>"
        data = str(x.get("data", ""))[:10]
        try:
            data = _dt_dn.fromisoformat(data).strftime("%d/%m/%Y")
        except Exception:
            pass
        righe += f"<div>💛 {_h_dn.escape(data)} · <b>{_h_dn.escape(_dn_eur(x.get('importo', 0), x.get('valuta', 'EUR')))}</b>{stato}</div>"
    return righe


def _dn_contenuto():
    conf = dn_conf()
    sess = st.session_state.get("sess") or {}
    uid, nome = sess.get("uid", ""), sess.get("nome", "")
    if _dn_lg() == "ar":
        st.markdown("<style>[data-testid='stDialog'] [data-testid='stVerticalBlock']{direction:rtl;text-align:right}</style>", unsafe_allow_html=True)
    st.write(_dn_t("intro"))
    voci = dn_di_utente(uid)
    if voci:
        tot = {}
        for x in voci:
            tot[x.get("valuta", "EUR")] = tot.get(x.get("valuta", "EUR"), 0) + float(x.get("importo", 0))
        st.markdown(f"**{_h_dn.escape(_dn_t('storia'))}** · {_h_dn.escape(_dn_t('totale'))}: **" + " + ".join(_dn_eur(v, k) for k, v in tot.items()) + "**"
                    f"<div style='margin-top:4px'>{_dn_righe_storia(voci[:8])}</div>", unsafe_allow_html=True)
    st.markdown(f"**{_h_dn.escape(_dn_t('importo'))}**")
    valuta = conf["valuta"]
    scelte = [_dn_eur(p, valuta) for p in DN_PRESET] + [_dn_t("altro")]
    s = st.radio(_dn_t("importo"), scelte, index=1, horizontal=True, key="dn_importo", label_visibility="collapsed")
    if s == scelte[-1]:
        imp = st.number_input(_dn_t("altro"), min_value=DN_MIN, max_value=DN_MAX, value=5.0, step=1.0, key="dn_altro", label_visibility="collapsed")
    else:
        imp = float(DN_PRESET[scelte.index(s)])
    b = (globals().get("DN_BTN") or {}).get(_dn_lg())
    if conf["modo"] == "api":
        if st.button(_dn_t("crea"), type="primary", width="stretch", key="dn_crea"):
            try:
                st.session_state["_dn_url"] = _dn_crea_ordine(conf, imp, uid, nome)
            except Exception as e:
                st.session_state.pop("_dn_url", None)
                st.error(_dn_t("errore", e=str(e)[:120]))
        url = st.session_state.get("_dn_url")
        if url:
            if b:
                st.markdown("<style>.st-key-dn_vai a{display:flex !important;min-height:0 !important;width:100% !important;max-width:360px;margin:6px auto !important;padding:0 !important;"
                            "aspect-ratio:" + f"{b[1]}/{b[2]}" + ";border:0 !important;border-radius:999px !important;background:url('data:image/webp;base64," + b[0] + "') center/100% 100% no-repeat !important;"
                            "color:transparent !important;box-shadow:0 0 14px 2px rgba(255,196,57,.6)}.st-key-dn_vai a p,.st-key-dn_vai a div{font-size:0 !important;color:transparent !important}</style>", unsafe_allow_html=True)
            with st.container(key="dn_vai"):
                st.link_button(_dn_t("vai"), url, width="stretch")
            st.caption(_dn_t("nota_api"))
    else:
        url = f"https://www.paypal.me/{conf['me']}/{imp:.2f}{valuta}"
        st.link_button("💛 " + _dn_t("vai"), url, width="stretch")
        st.caption(_dn_t("me_nota"))
        if st.button(_dn_t("me_fatto"), type="primary", width="stretch", key="dn_fatto"):
            _dn_registra(uid, nome, imp, valuta, "da_confermare", "paypal.me")
            st.success(_dn_t("ok_reg"))


def _dn_dialogo():
    st.dialog("💛 " + _dn_t("titolo"))(_dn_contenuto)()


# ---------------------------------------------------------------------------------------------------------------------
# l'elenco degli utenti (chi gestisce): logo tondo nella riga + tutte le donazioni dentro
# ---------------------------------------------------------------------------------------------------------------------
_DN_JS_LOGO = r"""(function(){
 var w=window, doc=w.document; if(w.__dnLogo) return; w.__dnLogo=1;
 var M='⁣⁤⁣', SRC='data:image/webp;base64,__LOGO__';
 function passa(){
  [].forEach.call(doc.querySelectorAll('[data-testid=stExpander] summary'), function(s){
   var t=s.textContent||''; var ha=t.indexOf(M)>=0, im=s.querySelector('img.dn-logo');
   if(ha&&!im){ var i=doc.createElement('img'); i.className='dn-logo'; i.src=SRC; i.alt='PayPal'; i.title='PayPal';
     i.style.cssText='width:34px;height:34px;flex:none;margin-left:auto;border-radius:50%;box-shadow:0 0 8px rgba(255,196,57,.8)'; s.appendChild(i); }
   if(!ha&&im) im.remove();
  });
 }
 var tm=null; function pianifica(){ if(tm) return; tm=w.setTimeout(function(){ tm=null; try{passa();}catch(e){} },200); }
 try{ new MutationObserver(pianifica).observe(doc.body,{childList:true,subtree:true,characterData:true}); }catch(e){}
 w.setInterval(function(){ try{passa();}catch(e){} },2000); pianifica();
})();"""


def _dn_logo_js():
    if st.session_state.get("_dn_logo_js") or "_inietta" not in globals() or not globals().get("DN_LOGO"):
        return
    st.session_state["_dn_logo_js"] = True
    try:
        _inietta(_DN_JS_LOGO.replace("__LOGO__", DN_LOGO))
    except Exception:
        pass


def dn_ui_admin(u):
    """Dentro alla riga di una persona nella scheda «Utenti»: le sue donazioni, e per chi gestisce conferma / registrazione a mano."""
    _dn_logo_js()
    voci = dn_di_utente(u["id"])
    st.markdown("**💛 Donazioni**" + (f" · totale **{_dn_eur(sum(float(x.get('importo', 0)) for x in voci if x.get('valuta', 'EUR') == 'EUR'))}**" if voci else ""))
    if not voci:
        st.caption("Nessuna donazione.")
    for x in voci:
        c1, c2 = st.columns([4, 2])
        stato = "" if x.get("stato") == "verificata" else " · ⏳ da confermare"
        try:
            data = _dt_dn.fromisoformat(x["data"]).strftime("%d/%m/%Y %H:%M")
        except Exception:
            data = str(x.get("data", ""))
        c1.markdown(f"💛 {data} · **{_dn_eur(x.get('importo', 0), x.get('valuta', 'EUR'))}** · {x.get('fonte', '')}{stato}")
        if x.get("stato") != "verificata":
            if c2.button("✅ Conferma", key=f"dn_ok_{x['id']}"):
                def f(d, i=x["id"]):
                    for y in d.get("donazioni", []):
                        if y.get("id") == i:
                            y["stato"] = "verificata"
                _dn_scrivi(f, "Donazione confermata")
                st.rerun()
        if c2.button("🗑 Togli", key=f"dn_del_{x['id']}"):
            def g(d, i=x["id"]):
                d["donazioni"] = [y for y in d.get("donazioni", []) if y.get("id") != i]
            _dn_scrivi(g, "Donazione tolta")
            st.rerun()
    with st.popover("➕ Registra una donazione a mano"):
        cifra = st.number_input("Importo in euro", min_value=1.0, max_value=DN_MAX, value=5.0, step=1.0, key=f"dn_man_{u['id']}")
        if st.button("💾 Registra", key=f"dn_man_b_{u['id']}", type="primary", width="stretch"):
            _dn_registra(u["id"], u.get("nome", ""), cifra, "EUR", "verificata", "a mano")
            st.rerun()


if "nu_ui_admin" in globals() and "_dn_nu_prima" not in globals():
    _dn_nu_prima = nu_ui_admin

    def nu_ui_admin(u, elenco):                                      # noqa: F811
        r = _dn_nu_prima(u, elenco)
        try:
            dn_ui_admin(u)
        except Exception:
            pass
        return r


for _dn_nome in ("vm_barra_home", "vm_schermata_home"):
    if _dn_nome in globals() and ("_dn_prima_" + _dn_nome) not in globals():
        globals()["_dn_prima_" + _dn_nome] = globals()[_dn_nome]

        def _dn_avvolgi(prima):
            def _nuova(*a, **k):
                r = prima(*a, **k)
                try:
                    dn_badge()
                except Exception:
                    pass
                return r
            return _nuova
        globals()[_dn_nome] = _dn_avvolgi(globals()["_dn_prima_" + _dn_nome])

# ritorno da PayPal: funziona anche se la persona non è (ancora) entrata
try:
    if st.query_params.get("dn") in ("ok", "no") and dn_attiva():
        _dn_ritorno()
except Exception as _e_dn:
    if type(_e_dn).__name__ in ("StopException", "RerunException"):
        raise
