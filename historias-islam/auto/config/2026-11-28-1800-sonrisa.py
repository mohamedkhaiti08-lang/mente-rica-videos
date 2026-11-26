# Estilo Noche · SERIO vs SONRÍE · "¿Sabes por qué un musulmán te sonríe?" (Jami' at-Tirmidhi 1956)
# Explorar: «lo que ves vs lo que Allah ve» con un acto concreto del día a día + gancho de curiosidad para quien no es musulmán.
# La misma calle: pasa gente. Uno sigue serio mirando el móvil (le dicen «hola» y no contesta; la gente se va apagada).
# El otro sonríe y saluda: a cada persona se le enciende una luz sobre la cabeza y una MONEDA DE LUZ cae atravesando
# la tierra hasta un COFRE enterrado. Día 30: «¿quién ha dado más?»… ninguno ha sacado nada. «Mira debajo»: un cofre vacío
# y gris; el otro se abre desbordando luz. Objetos nuevos: sonrisa, monedas de luz que caen, cofre de luz, gente que pasa.
# Uso: python3 2026-11-28-1800-sonrisa.py salida.mp4 [t1 t2 ... para fotogramas]   (NOVOZ=1 reutiliza el guion)
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes por qué un musulmán te sonríe?",
         "Dos personas. La misma calle.",
         "Uno pasa serio, sin mirar.",
         "El otro sonríe a cada uno.",
         "Día diez.",
         "Día treinta. Ninguno ha dado nada…",
         "¿O sí?",
         "Mira debajo.",
         "El Profeta, la paz sea con él, dijo: tu sonrisa a tu hermano es una sadaqa, una caridad.",
         "Sonreír también es dar.",
         "¿Quién te alegra el día con su sonrisa? Etiquétale."]
PAUSAS = [0.4, 0.5, 0.9, 1.3, 1.6, 0.6, 1.6, 1.4, 0.6, 0.6, 1.2]
def SFX(s): return [dict(t=s[3] + 0.9, f=1320, dur=0.8, v=0.05), dict(t=s[4] + 0.9, f=1320, dur=0.8, v=0.05),
                    dict(t=s[7] + 0.5, f=660, dur=2.0, v=0.08), dict(t=s[7] + 0.65, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-28-1800-sonrisa.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, s3, t10, t30, tq, tmira, thad, tfin, task = starts
print("DUR", DUR, starts)

FL, FR = 255, 800                     # figuras
CYF = GY + 250                        # cofres bajo tierra
TEAL = (130, 240, 232)
MOVIL = dict(P["stand"]); MOVIL.update(head=(4, -296), re=(30, -204), rh=(14, -244), le=(-26, -212), lh=(-32, -150))
GRIS = (130, 128, 138)
SALUDA_I = dict(P["stand"]); SALUDA_I.update(le=(-40, -246), lh=(-56, -310))   # saluda con la mano izquierda (hacia el centro)
# encuentros: (lado, t0)
ENC_L = [s2 + 0.1, t10 + 0.05, t30 + 0.25]
FS = [1.0, 0.68, 0.8]                 # velocidad de cada encuentro (días 10 y 30 más rápidos para no solaparse)
ENC_R = [s3 + 0.1, t10 + 0.15, t30 + 0.4]

def paseante(t, t0, x_out, x_stop, f=1.0):
    """Persona que llega desde el centro, se para delante y se va (f < 1 lo acelera). Devuelve (x, pose, alpha, parado) o None."""
    a1, a2, a3 = t0 + 0.9 * f, t0 + 2.3 * f, t0 + 3.2 * f
    if t < t0 or t > a3 + 0.2: return None
    if t < a1: u = seg(t, t0, a1); x = lerp(x_out, x_stop, u); p = Z.walk_pose(t * 9); par = 0.0
    elif t < a2: x = x_stop; p = P["stand"]; par = seg(t, a1, a1 + 0.2)
    else: u = seg(t, a2, a3); x = lerp(x_stop, x_out, u); p = Z.walk_pose(t * 9); par = 1.0
    a = 255 * seg(t, t0, t0 + 0.3) * (1 - seg(t, a3 - 0.4, a3 + 0.1))
    return x, p, a, par

def monedas_der(t):
    """Monedas que ya han llegado al cofre de la derecha."""
    n = 0
    for i, t0 in enumerate(ENC_R):
        n += (1, 4, 7)[i] * (t > t0 + (1.5 * FS[i]) + 1.2)
    return n

def frame(t):
    bright = 0.1 + 0.06 * seg(t, s3 + 1.0, s3 + 2.5) + 0.82 * seg(t, tmira + 0.3, thad + 2.0)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    mira = seg(t, tmira, tmira + 1.0)
    # ---------- bajo el suelo: cofres (casi no se ven hasta «mira debajo») ----------
    Z.cofre_luz(d, g, FL, CYF, 0, 0.35 * mira, t, alpha=90 + 165 * mira, gris=1.0)
    if mira > 0:                                          # el cofre vacío solo suelta polvo
        Z.polvo(d, FL - 70, FL + 70, mira * (1 - seg(t, tmira + 2.0, tmira + 3.0)), t)
    Z.cofre_luz(d, g, FR, CYF, monedas_der(t), mira, t, alpha=90 + 165 * mira, gris=0.35 * (1 - mira))
    if mira > 0:
        g.ellipse([FR - 260, GY - 40, FR + 260, GY + 520], fill=(250, 220, 140, int(90 * mira)))
        Z.destellos(d, g, FR, CYF - 60, GY - 200, t, mira * (1 - 0.5 * seg(t, tfin, tfin + 1.0)))
    # ---------- gente que pasa ----------
    for i, t0 in enumerate(ENC_L):                      # al serio: le saludan y no contesta
        f = FS[i]; r = paseante(t, t0, 560, FL + 140, f)
        if r:
            x, p, a, par = r
            gris = seg(t, t0 + 1.5 * f, t0 + 2.2 * f)
            col = tuple(int(lerp(c, gg, gris)) for c, gg in zip(CREAM, GRIS))
            p = Z.lerp_pose(p, Z.SALUDA, par * (1 - seg(t, t0 + 1.4 * f, t0 + 1.8 * f))) if t < t0 + 2.3 * f else p
            Z.mini_figure(d, x, Z.espejo(p), k=0.58, col=col, alpha=a)
            if t0 + 0.9 * f < t < t0 + 2.0 * f:
                Z.bocadillo(d, x + 10, GY - 255, ("HOLA", "¡BUENAS!", "HOLA…")[i], alpha=a * seg(t, t0 + 0.9 * f, t0 + 0.9 * f + 0.2) * (1 - seg(t, t0 + 2.0 * f - 0.2, t0 + 2.0 * f)), size=24, cola=-1)
    for i, t0 in enumerate(ENC_R):                      # al que sonríe: se les enciende una luz
        f = FS[i]; r = paseante(t, t0, 520, FR - 145, f)
        if r:
            x, p, a, par = r
            luz = seg(t, t0 + 1.2 * f, t0 + 1.7 * f)
            if par and t < t0 + 2.3 * f: p = Z.lerp_pose(p, P["joy"], 0.5 * luz)
            Z.mini_figure(d, x, p, k=0.58, alpha=a)
            hy = GY - 300 * 0.58
            Z.sonrisa(d, x, hy + 6, luz, alpha=a)
            if luz > 0:
                g.ellipse([x - 70, hy - 80, x + 70, hy + 60], fill=(80, 230, 225, int(140 * luz * a / 255)))
                d.ellipse([(x - 30) * S, (hy - 60) * S, (x + 30) * S, (hy - 48) * S], outline=TEAL + (int(200 * luz * a / 255),), width=int(3 * S))
        # monedas de luz que caen hasta el cofre
        for j in range((1, 4, 7)[i]):
            tc = t0 + 1.5 * FS[i] + j * 0.12
            u = seg(t, tc, tc + 1.0)
            if 0 < u < 1:
                mx = lerp(FR - 145 + 30, FR - 20 + (j % 4) * 14, u); my = lerp(GY - 220, CYF - 30, u * u)
                Z.moneda_luz(d, g, mx, my, r=13, alpha=255 * (1 - seg(u, 0.85, 1.0)))
    # ---------- IZQUIERDA: serio con el móvil ----------
    lp = MOVIL
    lp = Z.lerp_pose(lp, Z.espejo(P["sad"]), seg(t, tmira + 0.8, tmira + 2.0))
    figure(d, FL, lp, alpha=int(255 - 60 * seg(t, thad, thad + 1.5)))
    movil_a = 255 * (1 - seg(t, tmira + 0.6, tmira + 1.0))
    Z.movil(d, g, FL + 16, GY - 250, movil_a)
    if movil_a > 0: Z.sonrisa(d, FL + 4, GY - 288, 0.0, alpha=movil_a)
    # ---------- DERECHA: sonríe ----------
    sal = max([seg(t, t0 + 0.9 * f, t0 + 0.9 * f + 0.3) * (1 - seg(t, t0 + 2.0 * f, t0 + 2.0 * f + 0.4)) for t0, f in zip(ENC_R, FS)])
    rp = Z.lerp_pose(P["stand"], SALUDA_I, sal)
    rp = Z.lerp_pose(rp, P["joy"], seg(t, tmira + 0.5, tmira + 1.2) * (1 - seg(t, thad + 3.0, thad + 3.6)))
    figure(d, FR, rp)
    Z.sonrisa(d, FR + rp["head"][0], GY + rp["head"][1] + 10, 0.3 + 0.7 * max(sal, seg(t, tmira + 0.5, tmira + 1.0)))
    for t0, f, txt in zip(ENC_R, FS, ("¡BUENOS DÍAS!", "¡HOLA!", "¿QUÉ TAL?")):
        al = 255 * seg(t, t0 + 0.9 * f, t0 + 0.9 * f + 0.2) * (1 - seg(t, t0 + 1.9 * f, t0 + 1.9 * f + 0.3))
        if al > 0: Z.bocadillo(d, 770, GY - 450, txt, alpha=al, size=24, cola=1, borde=TEAL)
    if t > tmira: g.ellipse([FR - 220, GY - 430, FR + 240, GY + 30], fill=(80, 230, 225, int(70 * seg(t, tmira, tmira + 2.0))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SERIO", "SONRÍE", t10, t30, 48, lx=FL, rx=FR - 20)
    Z.subs(d, t, [(-0.4, s1 - 0.15, "¿POR QUÉ UN MUSULMÁN TE SONRÍE?"), (s1, s2 - 0.1, "LA MISMA CALLE"),
                  (s2, s3 - 0.1, "UNO PASA SERIO"), (s3, t10 - 0.1, "EL OTRO SONRÍE A CADA UNO"),
                  (t30, tq - 0.1, "NINGUNO HA DADO NADA…")])
    Z.pregunta(d, t, tq, tmira, "¿O SÍ?")
    Z.pregunta(d, t, tmira, thad, "MIRA DEBAJO ↓")
    Z.fuente(d, t, thad, tfin, ["«TU SONRISA", "A TU HERMANO", "ES UNA SADAQA»"], "JAMI' AT-TIRMIDHI 1956")
    Z.final(d, t, tfin, "SONREÍR", "TAMBIÉN ES DAR.", task, "¿QUIÉN TE ALEGRA EL DÍA", "CON SU SONRISA? ETIQUÉTALE")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
