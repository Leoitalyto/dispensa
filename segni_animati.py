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

# Per ogni segno: "corpo" = movimento di tutta la figura (anim, durata, ampiezza); "parti" = pezzi ritagliati con un poligono (in %),
# ognuno col suo perno e il suo movimento: (poligono, (perno x, perno y), animazione, durata s, ampiezza, ritardo s).
# Il pezzo si toglie dall'immagine di base (niente doppioni): si vede solo quello che si muove.
SA_SEGNI = {
    "ariete": {"corpo": ("sa-butt", 4.6, 3), "parti": []},
    "toro": {"corpo": ("sa-rock", 5, 2.2), "parti": []},
    "gemelli": {"corpo": ("sa-rock", 5.2, 1.8), "parti": []},
    "leone": {"corpo": ("sa-flick", 2.8, 1.6), "parti": []},
    "cancro": {"corpo": ("sa-wave", 3.2, 3),
               "parti": [([(14, 38), (10, 30), (14, 22), (24, 14), (30, 18), (38, 13), (46, 9), (46, 13), (38, 16), (36, 20), (30, 24), (26, 32), (22, 38)], (17, 35), "sa-claw", 3.2, 0, 0),
                         ([(24, 14), (32, 7), (44, 5), (46, 9), (38, 13), (30, 18)], (17, 35), "sa-dito", 3.2, 0, 0),
                         ([(86, 38), (90, 30), (86, 22), (76, 14), (70, 18), (62, 13), (54, 9), (54, 13), (62, 16), (64, 20), (70, 24), (74, 32), (78, 38)], (83, 35), "sa-clawr", 3.2, 0, 0),
                         ([(76, 14), (68, 7), (56, 5), (54, 9), (62, 13), (70, 18)], (83, 35), "sa-ditor", 3.2, 0, 0),
                         ([(0, 60), (30, 54), (34, 66), (28, 80), (32, 98), (4, 98), (0, 80)], (30, 58), "sa-walk", 0.8, 4, 0),
                         ([(100, 60), (70, 54), (66, 66), (72, 80), (68, 98), (96, 98), (100, 80)], (70, 58), "sa-walk", 0.8, 4, 0.4)]},
    "scorpione": {"corpo": ("sa-guard", 4.4, 3),
                  "parti": [([(33, 38), (32, 22), (38, 8), (50, 0), (64, 2), (74, 10), (80, 22), (81, 34), (74, 40), (66, 34), (60, 22), (52, 18), (46, 22), (46, 34), (42, 42)], (72, 38), "sa-strike", 4.4, 22, 0),
                            ([(5, 62), (8, 52), (15, 48), (24, 48), (27, 56), (22, 64), (16, 70), (14, 78), (9, 80), (5, 72)], (25, 52), "sa-pinch", 2.8, 14, 0),
                            ([(30, 82), (40, 78), (52, 74), (60, 70), (67, 72), (70, 80), (66, 88), (58, 94), (46, 95), (34, 92)], (66, 76), "sa-pinchr", 2.8, 12, 1.4)]},
    "sagittario": {"corpo": None,
                   "parti": [([(58, 14), (80, 12), (100, 15), (100, 30), (80, 34), (60, 34)], (60, 24), "sa-pull", 4.8, 6, 0),
                             ([(22, 50), (10, 46), (2, 55), (0, 75), (6, 92), (20, 94), (24, 70)], (22, 52), "sa-skew", 2.4, 5, 0)]},
    "bilancia": {"corpo": None,
                 "parti": [([(12, 20), (16, 20), (40, 64), (40, 76), (3, 76), (2, 62)], (14, 20), "sa-bob", 3.8, 4, 0),
                           ([(84, 20), (88, 20), (98, 62), (98, 76), (61, 76), (60, 64)], (86, 20), "sa-bob", 3.8, 4, 1.9)]},
    "capricorno": {"corpo": ("sa-bob", 5, 2),
                   "parti": [([(58, 22), (68, 18), (76, 10), (88, 12), (90, 22), (84, 34), (76, 42), (70, 50), (62, 52), (58, 40)], (70, 52), "sa-flap", 2.6, 9, 0),
                             ([(18, 10), (40, 5), (55, 12), (52, 35), (36, 48), (14, 45), (10, 32)], (45, 50), "sa-rock", 5, 2, 0)]},
    "acquario": {"corpo": None,
                 "parti": [([(60, 8), (78, 5), (92, 18), (98, 38), (90, 52), (75, 45), (66, 30)], (62, 12), "sa-skew", 3.2, 4, 0),
                           ([(18, 22), (52, 18), (56, 40), (40, 52), (18, 48), (12, 36)], (45, 50), "sa-rock", 3.6, 2.5, 0)]},
    "pesci": {"corpo": ("sa-nuota", 3.6, 0), "parti": [], "liquido": True},
    "vergine": {"corpo": ("sa-bob", 5.5, 1.5),
                "parti": [([(66, 24), (80, 22), (82, 34), (76, 46), (66, 52), (60, 44)], (66, 48), "sa-rock", 3.4, 8, 0),
                          ([(14, 12), (22, 12), (26, 19), (22, 27), (14, 27), (10, 19)], (18, 19), "sa-bob", 4, 3, 0)]},
}
# scintille e altri effetti: (tipo, x, y, grandezza px, ritardo s, durata s)
SA_EFFETTI = {
    "ariete": [("occhio", 38.5, 44.5, 15, 0, 4.6), ("occhio", 61.5, 44.5, 15, 0, 4.6), ("st", 10, 70, 6, 0, 2.4), ("st", 88, 25, 5, 1.1, 2.8), ("st", 50, 8, 5, .5, 2.2)],
    "toro": [("fumo", 42, 83, 14, 0, 2.2), ("fumo", 58, 83, 14, 1.1, 2.2), ("st", 14, 40, 5, .4, 2.6)],
    "gemelli": [("cuore", 50, 30, 12, 0, 3.4), ("st", 90, 20, 5, 1, 2.4)],
    "cancro": [("st", 92, 8, 6, 0, 2.6), ("bolla", 50, 40, 8, 0, 3.2), ("bolla", 58, 55, 6, 1.4, 3.6)],
    "leone": [("st", 20, 15, 5, 0, 1.8), ("st", 12, 62, 6, .7, 2.1), ("st", 46, 8, 5, 1.2, 2)],
    "vergine": [("st", 28, 70, 5, 0, 2.4), ("st", 78, 40, 6, .9, 2.8), ("st", 20, 48, 5, 1.6, 2.2)],
    "bilancia": [("st", 50, 5, 7, 0, 2.2), ("st", 18, 40, 5, 1.2, 2.6), ("st", 82, 40, 5, .6, 2.4)],
    "scorpione": [("st", 36, 4, 7, 2.5, 4.4), ("st", 88, 70, 5, 0, 2.6)],
    "sagittario": [("lampo", 97, 22, 22, 0, 4.8), ("st", 12, 22, 5, .5, 2.6), ("st", 50, 8, 5, 1.4, 2.2)],
    "capricorno": [("st", 20, 74, 5, 0, 2.2), ("st", 86, 78, 6, .8, 2.6), ("st", 50, 8, 5, 1.5, 2.4)],
    "acquario": [("scorri", 0, 0, 0, 0, 0.9), ("goccia", 14, 70, 6, 0, 1.3), ("goccia", 30, 78, 6, .6, 1.3), ("st", 84, 20, 5, .8, 2.4)],
    "pesci": [("bolla2", 8, 78, 11, 0, 4.2), ("bolla2", 22, 90, 8, 1.3, 3.8), ("bolla2", 48, 92, 12, 2.4, 4.6), ("bolla2", 72, 88, 9, .7, 4.0), ("bolla2", 92, 70, 12, 1.9, 4.4), ("bolla2", 90, 35, 8, 3.1, 3.9), ("bolla2", 6, 40, 9, 2.0, 4.3), ("bolla2", 50, 50, 7, .4, 3.6), ("bolla2", 35, 20, 8, 3.3, 4.1), ("st", 12, 20, 5, .3, 2.4)],
}
# la zona dove scorre l'acqua dell'Acquario (poligono in %)
SA_ACQUA = [(6, 42), (34, 42), (42, 60), (46, 80), (40, 100), (0, 100), (4, 70)]


def _sa_poly(punti):
    return "polygon(" + ",".join(f"{x}% {y}%" for x, y in punti) + ")"


def _sa_riduci(punti, f=0.985):
    cx = sum(x for x, _y in punti) / len(punti)
    cy = sum(y for _x, y in punti) / len(punti)
    return [(cx + (x - cx) * f, cy + (y - cy) * f) for x, y in punti]


def _sa_foro(fori):
    """clip-path della base: tutta l'immagine meno i pezzi che si muovono (nessun doppione)."""
    if not fori:
        return ""
    pts = ["0 0", "100% 0", "100% 100%", "0 100%", "0 0"]
    for f in fori:
        f = _sa_riduci(f)
        pts += [f"{x:.1f}% {y:.1f}%" for x, y in f] + [f"{f[0][0]:.1f}% {f[0][1]:.1f}%", "0 0"]
    return "polygon(evenodd," + ",".join(pts) + ")"


# un filtro «acqua»: l'onda attraversa tutta la figura, pinne e code ondeggiano in modo morbido, senza tagli
SA_FILTRO = ("<svg width='0' height='0' style='position:absolute' aria-hidden='true'><filter id='sa-liquido' x='-10%' y='-10%' width='120%' height='120%' color-interpolation-filters='sRGB'>"
             "<feTurbulence type='fractalNoise' baseFrequency='0.012 0.020' numOctaves='2' seed='3' result='r'>"
             "<animate attributeName='baseFrequency' dur='7s' values='0.012 0.020;0.018 0.012;0.012 0.020' repeatCount='indefinite'/></feTurbulence>"
             "<feDisplacementMap in='SourceGraphic' in2='r' scale='9' xChannelSelector='R' yChannelSelector='G'/></filter></svg>")


def sa_segno_html(seg, b64, nome):
    e = _sa_html.escape
    prop = SA_PROPORZIONI.get(seg, 1.2)
    cfg = SA_SEGNI.get(seg, {"corpo": None, "parti": []})
    foro = _sa_foro([x[0] for x in cfg["parti"]])
    strati = ["<div class='sa-l sa-base'" + (f" style=\"clip-path:{foro}\"" if foro else "") + "></div>"]
    for poly, (ox, oy), k, dur, amp, dl in cfg["parti"]:
        val = f"{amp}%" if k in ("sa-bob", "sa-circle", "sa-pull", "sa-wave") else f"{amp}deg"
        strati.append(f"<div class='sa-l sa-p' style=\"clip-path:{_sa_poly(poly)};transform-origin:{ox}% {oy}%;animation:{k} {dur}s ease-in-out {-dl}s infinite;--a:{val}\"></div>")
    for tipo, x, y, g, dl, dur in SA_EFFETTI.get(seg, []):
        if tipo == "scorri":
            strati.append(f"<i class='sa-l sa-scorri' style=\"clip-path:{_sa_poly(SA_ACQUA)};animation-duration:{dur}s\"></i>")
        else:
            strati.append(f"<i class='sa-fx sa-{tipo}' style='left:{x}%;top:{y}%;--g:{g}px;animation-delay:{-dl}s;animation-duration:{dur}s'></i>")
    corpo = ""
    if cfg.get("liquido"):
        strati.insert(0, SA_FILTRO)
    if cfg["corpo"]:
        k, dur, amp = cfg["corpo"]
        val = f"{amp}%" if k in ("sa-bob", "sa-circle", "sa-pull", "sa-wave") else f"{amp}deg"
        corpo = f" style=\"animation:{k} {dur}s ease-in-out infinite;--a:{val};transform-origin:50% 85%\""
    return (f"<div class='cp-segno sa cp-an-{seg}'><div class='sa-box' role='img' aria-label='{e(nome)}' "
            f"style=\"--im:url(data:image/webp;base64,{b64});--ar:{prop:.4f};--w:{min(150, 130 * prop):.1f}px\"><div class='sa-corpo'{corpo}>" + "".join(strati) + f"</div></div><span>{e(nome)}</span></div>")


SA_CSS = """<style>
.cp-segno.sa .sa-box{position:relative;margin:0 auto;width:min(var(--w),62%);aspect-ratio:var(--ar);filter:drop-shadow(0 0 8px var(--cg))}
.sa-l{position:absolute;inset:0;background:var(--im) center/100% 100% no-repeat;will-change:transform}
.sa-corpo{position:absolute;inset:0}
.cp-an-pesci .sa-corpo{filter:url(#sa-liquido)}
.sa-scorri{background:repeating-linear-gradient(172deg,rgba(170,245,255,0) 0,rgba(170,245,255,.5) 7px,rgba(170,245,255,0) 14px);background-size:100% 14px;mix-blend-mode:screen;-webkit-mask-image:var(--im);mask-image:var(--im);-webkit-mask-size:100% 100%;mask-size:100% 100%;animation:sa-scorri .9s linear infinite}
@keyframes sa-scorri{from{background-position:0 0}to{background-position:0 14px}}
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
@keyframes sa-nuota{0%,100%{transform:translate(-2.5%,1.5%) rotate(-3.5deg)}25%{transform:translate(0,-1.5%) rotate(0deg) scale(1.02)}50%{transform:translate(2.5%,1.5%) rotate(3.5deg)}75%{transform:translate(0,-1.5%) rotate(0deg) scale(1.02)}}
@keyframes sa-claw{0%,50%,100%{transform:rotate(0)}58%{transform:rotate(-7deg)}66%{transform:rotate(2deg)}74%{transform:rotate(-7deg)}84%{transform:rotate(0)}}
@keyframes sa-dito{0%,50%,100%{transform:rotate(0) translate(11%,-18%) rotate(0) translate(-11%,18%)}58%{transform:rotate(-7deg) translate(11%,-18%) rotate(24deg) translate(-11%,18%)}66%{transform:rotate(2deg) translate(11%,-18%) rotate(-10deg) translate(-11%,18%)}74%{transform:rotate(-7deg) translate(11%,-18%) rotate(24deg) translate(-11%,18%)}84%{transform:rotate(0) translate(11%,-18%) rotate(0) translate(-11%,18%)}}
@keyframes sa-clawr{0%,50%,100%{transform:rotate(0)}58%{transform:rotate(7deg)}66%{transform:rotate(-2deg)}74%{transform:rotate(7deg)}84%{transform:rotate(0)}}
@keyframes sa-ditor{0%,50%,100%{transform:rotate(0) translate(-11%,-18%) rotate(0) translate(11%,18%)}58%{transform:rotate(7deg) translate(-11%,-18%) rotate(-24deg) translate(11%,18%)}66%{transform:rotate(-2deg) translate(-11%,-18%) rotate(10deg) translate(11%,18%)}74%{transform:rotate(7deg) translate(-11%,-18%) rotate(-24deg) translate(11%,18%)}84%{transform:rotate(0) translate(-11%,-18%) rotate(0) translate(11%,18%)}}
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
.sa-bolla2{border-radius:50%;border:1.5px solid rgba(225,252,255,.95);background:radial-gradient(circle at 32% 30%,rgba(255,255,255,.85),rgba(120,225,255,.18) 55%,rgba(80,200,255,.08));box-shadow:0 0 6px rgba(150,240,255,.8);opacity:0;animation:sa-bolla2 4s ease-in-out infinite}
@keyframes sa-bolla2{0%{opacity:0;transform:translate(0,0) scale(.5)}12%{opacity:1}35%{transform:translate(9px,-18px) scale(.9)}65%{opacity:.95;transform:translate(-8px,-36px) scale(1)}100%{opacity:0;transform:translate(6px,-56px) scale(1.15)}}
.sa-occhio{border-radius:50%;background:radial-gradient(circle,#fff 0,#fff3a0 22%,#ff9a1f 45%,rgba(255,80,0,.55) 65%,transparent 78%);mix-blend-mode:screen;opacity:0;filter:drop-shadow(0 0 5px #ff8a00);animation:sa-occhio 4.6s ease-in-out infinite}
@keyframes sa-occhio{0%,52%{opacity:0;transform:scale(.4)}60%{opacity:.8;transform:scale(.9)}66%,76%{opacity:1;transform:scale(1.5)}86%{opacity:.35;transform:scale(1)}94%,100%{opacity:0;transform:scale(.4)}}
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
