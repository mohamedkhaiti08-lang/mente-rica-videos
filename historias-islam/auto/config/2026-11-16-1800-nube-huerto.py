# Estilo Noche · GUARDA vs COMPARTE (da un tercio) · "la nube que regó un solo huerto" (Sahih Muslim 2984)
# Metáfora visual: dos huertos con la misma cosecha. Uno se lo guarda todo; el otro da un tercio al que lo necesita.
# Día 10: no llueve en ninguno. Día 30: una nube de luz cruza el cielo, pasa de largo el primer huerto
# y riega solo el del que da. Piezas nuevas: planta, cesta, fruta, nube_luz (en plantilla/noche/piezas.py).
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-16-1800-nube-huerto.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Dos huertos. Pero el cielo solo conoce a uno.",
         "Uno se lo guarda todo.",
         "El otro da un tercio a quien lo necesita.",
         "Día diez. No llueve.",
         "¿Dónde crees que va a llover?",
         "Día treinta.",
         "El Profeta, la paz sea con él, contó que un hombre oyó una voz dentro de una nube: riega el huerto de fulano. Y era el huerto del que daba un tercio.",
         "Da. El cielo sabe tu nombre.",
         "¿Y tú, qué parte de lo tuyo das?"]
PAUSAS = [0.6, 0.8, 1.0, 0.5, 2.2, 1.4, 0.8, 0.9, 1.6]
def SFX(s): return [dict(t=s[2] + 1.2, f=1320, dur=0.8, v=0.06), dict(t=s[5] + 1.6, f=660, dur=2.0, v=0.08), dict(t=s[5] + 1.75, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-16-1800-nube-huerto.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

FL, BL = 200, 100                       # izquierda: figura y cesta
FR, BR = 905, 990                       # derecha: figura y cesta
POBRE = 540
PL = [285, 345, 405, 462]               # plantas del huerto izquierdo
PR = [612, 672, 732, 792]               # plantas del huerto derecho
FLORES = [642, 702, 762]
def mirror(p): return {j: (-v[0], v[1]) for j, v in p.items()}
CLOUD_Y = 770

def frame(t):
    bright = 0.15 + 0.1 * seg(t, s2, s2 + 1.2) - 0.08 * seg(t, t10, t10 + 1.2) + 0.78 * seg(t, t30 + 1.6, t30 + 4.0)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    seco = 0.55 * seg(t, t10, t10 + 1.5)                      # día 10: los dos huertos se secan
    rainL = 0.0
    # ---------- nube de luz (día 30) ----------
    cx = None
    if t > t30:
        k1 = seg(t, t30, t30 + 1.3); k2 = seg(t, t30 + 1.7, t30 + 2.9)
        cx = lerp(-220, 380, k1) + (690 - 380) * k2
        Z.nube_luz(d, g, cx, CLOUD_Y + 6 * math.sin(t * 1.4), 255 * seg(t, t30, t30 + 0.6), t, lluvia=seg(t, t30 + 2.9, t30 + 3.4), ancho=0.85)
    agua = seg(t, t30 + 3.2, t30 + 4.6)
    # ---------- lo que no se ve ----------
    Z.grietas(d, 375, 0.3 * seg(t, t10, t10 + 1.5) + 0.7 * seg(t, t30 + 2.8, t30 + 4.5), seed=6)
    Z.roots(d, 0.3 * seg(t, s2 + 1.6, s2 + 3.2) + 0.2 * seg(t, t10, t10 + 1.5) + 0.5 * seg(t, t30 + 3.2, t30 + 5.5), x0=702)
    # ---------- huerto izquierdo ----------
    for i, x in enumerate(PL):
        Z.planta(d, g, x, 112 + 10 * (i % 2), 1.0, min(1.0, seco + 0.45 * seg(t, t30 + 2.8, t30 + 4.5)), t)
    # ---------- huerto derecho ----------
    Z.camino_luz(d, g, 590, 815, agua)
    for i, x in enumerate(PR):
        Z.planta(d, g, x, 112 + 10 * (i % 2), 1.0 + 0.45 * seg(t, t30 + 3.4, t30 + 5.2), seco * (1 - agua), t, luz=agua)
    for i, x in enumerate(FLORES):
        Z.flor(d, x, 150 * seg(t, t30 + 4.0 + 0.3 * i, t30 + 5.4 + 0.3 * i))
    # ---------- cestas ----------
    grisL = 0.3 * seg(t, t10, t10 + 1.5) + 0.7 * seg(t, t30 + 2.8, t30 + 4.5)
    Z.cesta(d, g, BL, 9, gris=grisL)
    given = sum(1 for a in (s2 + 0.4, s2 + 0.9, s2 + 1.4) if t >= a)
    Z.cesta(d, g, BR, 9 - given)
    for j, a in enumerate((s2 + 0.4, s2 + 0.9, s2 + 1.4)):     # fruta que vuela al que lo necesita
        k = seg(t, a, a + 1.0)
        tx, ty = POBRE + 34 + (j - 1) * 22, GY - 12
        if a <= t < a + 1.0:
            x_, y_ = lerp(BR, tx, k), lerp(GY - 110, ty, k) - 220 * math.sin(math.pi * k)
            Z.fruta(d, g, x_, y_)
        elif t >= a + 1.0:
            Z.fruta(d, g, tx, ty, r=12, glow=t < t30 + 2)
    if s2 + 1.0 < t < s2 + 2.6:                                 # semilla de luz que baja a la tierra (lo que se da, se planta)
        k = seg(t, s2 + 1.0, s2 + 1.8)
        Z.gota(d, g, lerp(BR - 30, 702, k), lerp(GY - 140, GY + 18, k) - 90 * math.sin(math.pi * k), r=8, col=GOLD, alpha=255 * (1 - seg(t, s2 + 2.0, s2 + 2.6)))
    # ---------- el que lo necesita ----------
    ap = seg(t, s1 - 0.3, s1 + 0.4)
    if ap > 0:
        if t < s2 + 0.4: pp = mirror(P["give"]) if t > s1 + 0.6 else P["stand"]         # pide a la izquierda
        elif t < s2 + 2.2: pp = P["stand"]
        else: pp = pose_mix("stand", "joy", seg(t, s2 + 2.2, s2 + 2.6) * (1 - seg(t, t10 - 0.4, t10)))
        Z.mini_figure(d, POBRE, pp, 0.6, alpha=225 * ap)
    # ---------- IZQUIERDA: LO GUARDA TODO ----------
    if t < s1: lp = P["stand"]
    elif t < t30 + 2.8: lp = mirror(pose_mix("stand", "hug", seg(t, s1, s1 + 0.7)))
    else: lp = mirror(pose_mix("hug", "sad", seg(t, t30 + 2.8, t30 + 4.0)))
    figure(d, FL, lp, alpha=int(255 * (1 - 0.35 * grisL)))
    # ---------- DERECHA: DA UN TERCIO ----------
    if t < s2: rp = P["stand"]
    elif t < s2 + 2.0: rp = pose_mix("stand", "give", seg(t, s2, s2 + 0.4) * (1 - seg(t, s2 + 1.6, s2 + 2.0)))
    elif t < t30 + 3.4: rp = P["stand"]
    else: rp = pose_mix("stand", "joy", seg(t, t30 + 3.4, t30 + 4.0) * (1 - seg(t, tfin - 0.8, tfin)))
    figure(d, FR, mirror(rp))
    if t > t30 + 3.4: g.ellipse([FR - 120, GY - 380, FR + 120, GY + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 3.4, t30 + 5))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "GUARDA", "COMPARTE", t10, t30, 50, lx=280, rx=745)
    Z.subs(d, t, [(0.5, s1 - 0.15, "EL CIELO SOLO CONOCE A UNO"), (s1, s2 - 0.15, "UNO SE LO GUARDA TODO"), (s2, t10 - 0.1, "EL OTRO DA UN TERCIO"),
                  (t10 + 0.6, tq - 0.1, "NO LLUEVE")])
    Z.pregunta(d, t, tq, t30, "¿DÓNDE LLOVERÁ?")
    Z.fuente(d, t, thad, tfin, ["UNA VOZ EN LA NUBE:", "«RIEGA EL HUERTO", "DE FULANO»"], "SAHIH MUSLIM 2984")
    Z.final(d, t, tfin, "DA. EL CIELO", "SABE TU NOMBRE.", task, "¿Y TÚ, QUÉ PARTE", "DE LO TUYO DAS?")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
