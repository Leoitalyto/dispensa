# -*- coding: utf-8 -*-
"""Segni zodiacali con movimento VERO (Compleanni, in Utilità): ogni segno è la stessa immagine ma divisa in «pezzi» morbidi
che si muovono ciascuno a modo suo: il granchio cammina e pizzica con le chele, lo scorpione sta in guardia e colpisce con la coda,
i pesci nuotano e si rincorrono, l'acquario versa acqua che scorre, il sagittario tende l'arco e la freccia scintilla…
Si carica DOPO compleanni.py: sostituisce il disegno del segno (sa_segno_html) e aggiunge il suo CSS (SA_CSS).
Ogni pezzo = (cx, cy, rx, ry  → zona morbida in %,  ox, oy → perno in %,  animazione, durata s, ampiezza, ritardo s)."""
import html as _sa_html

# proporzioni (larghezza/altezza) delle immagini
SA_PROPORZIONI = {"ariete": 277 / 199, "toro": 288 / 219, "gemelli": 234 / 206, "cancro": 248 / 204, "leone": 246 / 227, "vergine": 284 / 225,
                  "bilancia": 263 / 224, "scorpione": 246 / 220, "sagittario": 279 / 227, "capricorno": 300 / 219, "acquario": 263 / 227, "pesci": 274 / 223}

# (cx, cy, rx, ry, ox, oy, animazione, durata, ampiezza, ritardo)
SA_PARTI = {
    "ariete": [(50, 52, 42, 46, 50, 85, "sa-butt", 4.6, 5, 0), (16, 48, 16, 30, 30, 50, "sa-rock", 4.6, 3, 0.2), (84, 48, 16, 30, 70, 50, "sa-rock", 4.6, 3, 0.2)],
    "toro": [(50, 50, 42, 48, 50, 90, "sa-rock", 5, 3, 0), (50, 84, 20, 10, 50, 80, "sa-breath", 2.2, 3, 0)],
    "gemelli": [(30, 52, 33, 50, 62, 95, "sa-rock", 5.2, 3.5, 0), (72, 52, 33, 50, 38, 95, "sa-rock", 5.2, 3.5, 2.6)],
    "cancro": [(14, 26, 17, 28, 36, 46, "sa-pinch", 3.2, 16, 0), (86, 26, 17, 28, 64, 46, "sa-pinchr", 3.2, 16, 1.6),
               (22, 78, 22, 20, 40, 55, "sa-walk", 0.7, 5, 0), (78, 78, 22, 20, 60, 55, "sa-walk", 0.7, 5, 0.35), (50, 56, 30, 26, 50, 50, "sa-wave", 2.8, 4, 0)],
    "leone": [(28, 50, 36, 50, 60, 55, "sa-flick", 2.6, 3, 0), (70, 55, 28, 42, 55, 70, "sa-rock", 4.2, 2, 0), (89, 86, 11, 12, 50, 50, "sa-bob", 3, 4, 0)],
    "vergine": [(60, 32, 14, 16, 52, 48, "sa-rock", 3.4, 9, 0), (45, 22, 17, 22, 50, 40, "sa-rock", 5, 2.5, 0.6), (60, 84, 38, 12, 50, 70, "sa-skew", 3.6, 2.5, 0), (9, 24, 10, 12, 50, 50, "sa-bob", 4, 5, 0)],
    "bilancia": [(50, 20, 40, 14, 50, 50, "sa-rock", 3.8, 2.2, 0), (22, 46, 22, 28, 22, 10, "sa-bob", 3.8, 5, 0), (78, 46, 22, 28, 78, 10, "sa-bob", 3.8, 5, 1.9)],
    "scorpione": [(40, 22, 20, 24, 56, 46, "sa-strike", 4.4, 38, 0), (15, 44, 17, 17, 36, 55, "sa-pinch", 2.8, 13, 0), (38, 68, 19, 13, 56, 56, "sa-pinchr", 2.8, 11, 1.4),
                  (55, 58, 48, 38, 55, 90, "sa-guard", 4.4, 4, 0)],
    "sagittario": [(63, 20, 30, 24, 42, 22, "sa-pull", 4.8, 7, 0), (9, 65, 15, 24, 20, 52, "sa-skew", 2.4, 5, 0), (40, 78, 30, 14, 50, 60, "sa-trot", 0.9, 2.5, 0)],
    "capricorno": [(73, 28, 20, 28, 62, 56, "sa-flap", 2.6, 10, 0), (60, 80, 30, 18, 60, 60, "sa-skew", 3, 3, 0), (28, 28, 22, 26, 40, 60, "sa-rock", 5, 3, 0)],
    "acquario": [(50, 82, 52, 20, 50, 80, "sa-wave", 2.4, 3.2, 0), (67, 30, 18, 30, 50, 15, "sa-skew", 3.2, 3.5, 0.5), (41, 30, 11, 15, 55, 55, "sa-rock", 3.6, 4, 0)],
    "pesci": [(28, 33, 30, 30, 50, 50, "sa-circle", 5, 5, 0), (62, 62, 30, 24, 50, 50, "sa-circle", 5, 5, 2.5), (68, 18, 15, 20, 62, 40, "sa-flap", 1.2, 9, 0)],
}
# scintille e altri effetti: (tipo, x, y, grandezza px, ritardo s, durata s)
SA_EFFETTI = {
    "ariete": [("st", 10, 70, 6, 0, 2.4), ("st", 88, 25, 5, 1.1, 2.8), ("st", 50, 8, 5, .5, 2.2)],
    "toro": [("fumo", 42, 83, 14, 0, 2.2), ("fumo", 58, 83, 14, 1.1, 2.2), ("st", 14, 40, 5, .4, 2.6)],
    "gemelli": [("cuore", 50, 30, 12, 0, 3.4), ("st", 90, 20, 5, 1, 2.4)],
    "cancro": [("st", 92, 8, 6, 0, 2.6), ("bolla", 50, 40, 8, 0, 3.2), ("bolla", 58, 55, 6, 1.4, 3.6)],
    "leone": [("st", 20, 15, 5, 0, 1.8), ("st", 12, 62, 6, .7, 2.1), ("st", 46, 8, 5, 1.2, 2)],
    "vergine": [("st", 28, 70, 5, 0, 2.4), ("st", 78, 40, 6, .9, 2.8), ("st", 20, 48, 5, 1.6, 2.2)],
    "bilancia": [("st", 50, 5, 7, 0, 2.2), ("st", 18, 40, 5, 1.2, 2.6), ("st", 82, 40, 5, .6, 2.4)],
    "scorpione": [("st", 36, 4, 7, 2.5, 4.4), ("st", 88, 70, 5, 0, 2.6)],
    "sagittario": [("lampo", 86, 19, 20, 0, 4.8), ("st", 12, 22, 5, .5, 2.6), ("st", 50, 8, 5, 1.4, 2.2)],
    "capricorno": [("st", 20, 74, 5, 0, 2.2), ("st", 86, 78, 6, .8, 2.6), ("st", 50, 8, 5, 1.5, 2.4)],
    "acquario": [("acqua", 25, 41, 7, 0, 1.1), ("goccia", 20, 62, 5, 0, 1.3), ("goccia", 30, 62, 5, .6, 1.3), ("st", 84, 20, 5, .8, 2.4)],
    "pesci": [("bolla", 46, 30, 7, 0, 3), ("bolla", 40, 45, 5, 1.1, 3.4), ("bolla", 80, 55, 6, 1.9, 3.1)],
}


def sa_segno_html(seg, b64, nome):
    e = _sa_html.escape
    prop = SA_PROPORZIONI.get(seg, 1.2)
    strati = ["<div class='sa-l sa-base'></div>"]
    for cx, cy, rx, ry, ox, oy, k, dur, amp, dl in SA_PARTI.get(seg, []):
        if k in ("sa-bob", "sa-circle", "sa-pull", "sa-wave"):
            val = f"{amp}px"
        else:
            val = f"{amp}deg"
        strati.append(f"<div class='sa-l' style=\"--mk:radial-gradient(ellipse {rx}% {ry}% at {cx}% {cy}%,#000 58%,transparent 100%);transform-origin:{ox}% {oy}%;"
                      f"animation:{k} {dur}s ease-in-out {-dl}s infinite;--a:{val}\"></div>")
    for tipo, x, y, g, dl, dur in SA_EFFETTI.get(seg, []):
        strati.append(f"<i class='sa-fx sa-{tipo}' style='left:{x}%;top:{y}%;--g:{g}px;animation-delay:{-dl}s;animation-duration:{dur}s'></i>")
    return (f"<div class='cp-segno sa cp-an-{seg}'><div class='sa-box' role='img' aria-label='{e(nome)}' "
            f"style=\"--im:url(data:image/webp;base64,{b64});--ar:{prop:.4f};--w:{min(150, 130 * prop):.1f}px\">" + "".join(strati) + f"</div><span>{e(nome)}</span></div>")


SA_CSS = """<style>
.cp-segno.sa .sa-box{position:relative;margin:0 auto;width:min(var(--w),62%);aspect-ratio:var(--ar);filter:drop-shadow(0 0 8px var(--cg))}
.sa-l{position:absolute;inset:0;background:var(--im) center/100% 100% no-repeat;will-change:transform}
.sa-l:not(.sa-base){-webkit-mask-image:var(--mk);mask-image:var(--mk)}
@keyframes sa-rock{0%,100%{transform:rotate(calc(var(--a) / -1))}50%{transform:rotate(var(--a))}}
@keyframes sa-butt{0%,55%,100%{transform:rotate(0) translateY(0)}62%{transform:rotate(calc(var(--a) / -1)) translateY(2px)}74%{transform:rotate(var(--a)) translateY(6px) scale(1.04)}86%{transform:rotate(0) translateY(0)}}
@keyframes sa-bob{0%,100%{transform:translateY(calc(var(--a) / -1))}50%{transform:translateY(var(--a))}}
@keyframes sa-wave{0%,100%{transform:translateX(calc(var(--a) / -1))}50%{transform:translateX(var(--a))}}
@keyframes sa-circle{0%{transform:translate(var(--a),0)}25%{transform:translate(0,var(--a)) rotate(3deg)}50%{transform:translate(calc(var(--a) / -1),0)}75%{transform:translate(0,calc(var(--a) / -1)) rotate(-3deg)}100%{transform:translate(var(--a),0)}}
@keyframes sa-skew{0%,100%{transform:skewX(calc(var(--a) / -1))}50%{transform:skewX(var(--a))}}
@keyframes sa-breath{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes sa-flick{0%,100%{transform:skewX(0) scale(1)}20%{transform:skewX(calc(var(--a) / -1)) scale(1.03)}45%{transform:skewX(var(--a)) scale(.99)}70%{transform:skewX(calc(var(--a) / -2)) scale(1.04)}}
@keyframes sa-flap{0%,100%{transform:rotate(calc(var(--a) / -1)) skewY(-3deg)}50%{transform:rotate(var(--a)) skewY(3deg)}}
@keyframes sa-trot{0%,100%{transform:translateY(0) skewX(calc(var(--a) / -1))}50%{transform:translateY(-2px) skewX(var(--a))}}
@keyframes sa-walk{0%,100%{transform:translateY(0) skewX(calc(var(--a) / -1))}50%{transform:translateY(-2px) skewX(var(--a))}}
@keyframes sa-pinch{0%,52%,100%{transform:rotate(0)}58%{transform:rotate(var(--a))}64%{transform:rotate(0)}70%{transform:rotate(var(--a))}76%{transform:rotate(0)}}
@keyframes sa-pinchr{0%,52%,100%{transform:rotate(0)}58%{transform:rotate(calc(var(--a) / -1))}64%{transform:rotate(0)}70%{transform:rotate(calc(var(--a) / -1))}76%{transform:rotate(0)}}
@keyframes sa-strike{0%,30%,100%{transform:rotate(0)}38%{transform:rotate(calc(var(--a) / -2))}46%{transform:rotate(var(--a))}52%{transform:rotate(calc(var(--a) / 1.25))}62%{transform:rotate(0)}}
@keyframes sa-guard{0%,100%{transform:translateX(0) rotate(0)}18%{transform:translateX(-3px) rotate(calc(var(--a) / -1.6667))}36%{transform:translateX(0) rotate(0)}60%{transform:translateX(3px) rotate(calc(var(--a) / 1.6667))}80%{transform:translateX(0) rotate(0)}}
@keyframes sa-pull{0%,45%,100%{transform:translateX(0)}60%,72%{transform:translateX(calc(var(--a) / -1))}76%{transform:translateX(calc(var(--a) / 2))}86%{transform:translateX(0)}}
.sa-fx{position:absolute;width:var(--g);height:var(--g);margin:calc(var(--g) / -2) 0 0 calc(var(--g) / -2);pointer-events:none}
.sa-st{background:radial-gradient(circle,#fff 0,var(--c) 38%,transparent 70%);clip-path:polygon(50% 0,60% 40%,100% 50%,60% 60%,50% 100%,40% 60%,0 50%,40% 40%);animation:sa-tw 2.4s ease-in-out infinite}
@keyframes sa-tw{0%,100%{opacity:0;transform:scale(.3) rotate(0)}50%{opacity:1;transform:scale(1.1) rotate(45deg)}}
.sa-lampo{background:radial-gradient(circle,#fff 0,#fff 20%,var(--c) 45%,transparent 72%);clip-path:polygon(50% 0,58% 42%,100% 50%,58% 58%,50% 100%,42% 58%,0 50%,42% 42%);opacity:0;animation:sa-lampo 4.8s ease-in-out infinite}
@keyframes sa-lampo{0%,70%{opacity:0;transform:scale(.2)}76%{opacity:1;transform:scale(1.4) rotate(20deg)}88%{opacity:.5;transform:scale(.8) rotate(60deg)}100%{opacity:0}}
.sa-fumo{border-radius:50%;background:radial-gradient(circle,rgba(220,240,255,.85),rgba(160,200,255,.25) 60%,transparent 75%);opacity:0;animation:sa-fumo 2.2s ease-out infinite}
@keyframes sa-fumo{0%{opacity:0;transform:translate(0,0) scale(.3)}25%{opacity:.9}100%{opacity:0;transform:translate(0,10px) scale(1.8)}}
.sa-bolla{border-radius:50%;border:1px solid rgba(220,250,255,.9);background:radial-gradient(circle at 30% 30%,rgba(255,255,255,.7),rgba(120,220,255,.15) 60%);opacity:0;animation:sa-bolla 3s ease-in infinite}
@keyframes sa-bolla{0%{opacity:0;transform:translate(0,6px) scale(.5)}20%{opacity:.9}100%{opacity:0;transform:translate(3px,-22px) scale(1.1)}}
.sa-cuore{background:none;animation:sa-cuore 3.4s ease-in-out infinite}
.sa-cuore:after{content:"💗";font-size:var(--g);line-height:1;position:absolute;left:0;top:0}
@keyframes sa-cuore{0%,100%{opacity:0;transform:scale(.4) translateY(4px)}40%,60%{opacity:1;transform:scale(1) translateY(-4px)}}
.sa-acqua{width:calc(var(--g) / 1.1111);height:34%;margin:0 0 0 calc(var(--g) / -2);border-radius:6px;
 background:repeating-linear-gradient(180deg,rgba(150,240,255,.95) 0,rgba(150,240,255,.95) 5px,rgba(60,170,255,.15) 5px,rgba(60,170,255,.15) 11px);background-size:100% 11px;
 -webkit-mask-image:linear-gradient(180deg,#000 55%,transparent);mask-image:linear-gradient(180deg,#000 55%,transparent);filter:drop-shadow(0 0 4px #5ff);animation:sa-acqua .55s linear infinite}
@keyframes sa-acqua{from{background-position:0 0}to{background-position:0 11px}}
.sa-goccia{border-radius:50% 50% 50% 50%/60% 60% 40% 40%;background:radial-gradient(circle at 35% 30%,#fff,#5fe3ff 60%,transparent);opacity:0;animation:sa-goccia 1.3s ease-in infinite}
@keyframes sa-goccia{0%{opacity:0;transform:translateY(-10px)}30%{opacity:1}100%{opacity:0;transform:translateY(16px)}}
@media (prefers-reduced-motion:reduce){.sa-l,.sa-fx{animation:none !important}.sa-fx{display:none}}
</style>"""

try:
    if "CP_CSS" in globals() and "sa-box" not in CP_CSS:
        CP_CSS = CP_CSS + SA_CSS                        # noqa: F811
except Exception:
    pass
