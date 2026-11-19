# Estilo Noche · IZQUIERDA vs DERECHA · "¿por qué los musulmanes comen con la derecha?" (Sahih Muslim 2020)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (como Bismillah 926 TikTok, salir de casa 807), gancho de curiosidad para IG.
# Dos personas sentadas en el suelo con su plato. Uno come con la izquierda: frente a él, una mano de humo imita cada bocado
# (día 10 ya se ve el brazo; día 30 aparece entera la sombra sentada que come igual que él). El otro come con la derecha:
# su mano deja luz, el plato brilla y bajo el suelo se le acumulan granos dorados. Lema: «No te parezcas a él».
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-20-1200-mano-derecha.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes por qué los musulmanes comen con la mano derecha?",
         "Uno come con la izquierda, sin pensar.",
         "El otro, siempre con la derecha.",
         "Día diez.",
         "¿Quién crees que come igual que él?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: come con tu derecha, porque el shaitán come con su izquierda.",
         "Come con la derecha. No te parezcas a él.",
         "¿Y tú, con qué mano comes?"]
PAUSAS = [0.7, 1.3, 1.4, 1.0, 2.2, 0.7, 0.9, 1.0, 1.6]
def SFX(s): return [dict(t=s[2] + 1.0, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-20-1200-mano-derecha.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, PL, SHX = 215, 340, 470        # izquierda: figura, plato, sombra (sentada enfrente)
XR, PR = 865, 740                  # derecha: figura, plato

def comer(t, a, per=1.7, ph=0.0):
    """0 = mano en el plato, 1 = mano en la boca. Empieza en a."""
    if t < a: return 0.0
    u = ((t - a) / per + ph) % 1
    return 0.5 - 0.5 * math.cos(2 * math.pi * u)

def tocando(t, a, per=1.7):
    """True justo cuando la mano coge comida del plato."""
    if t < a: return 0.0
    u = ((t - a) / per) % 1
    return max(0.0, 1 - min(u, 1 - u) * 8)

def frame(t):
    bright = 0.15 + 0.15 * seg(t, t10, t10 + 1.2) + 0.7 * seg(t, t30 + 0.4, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, do = Z.new_layer(); under, du = Z.new_layer()
    dark = 0.25 * seg(t, t10, t10 + 2.0) + 0.45 * seg(t, t30, t30 + 2)
    # ---------- lo que no se ve ----------
    Z.grietas(d, PL - 40, 0.35 * seg(t, t10 + 1.0, t10 + 2.6) + 0.65 * seg(t, t30 + 0.4, t30 + 2.6), seed=7)
    Z.granos(d, g, PR + 20, 0.25 * seg(t, s2 + 1.0, s2 + 3.0) + 0.3 * seg(t, t10 + 1.0, t10 + 2.6) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), t)
    # ---------- IZQUIERDA: con la izquierda ----------
    Z.mantel(d, PL - 10, 170, alpha=255 * (1 - 0.3 * dark))
    eL = comer(t, s1 + 0.2)
    droop = 0.6 * seg(t, t30 + 0.6, t30 + 2.0)
    lp = Z.sentado(eL, droop)
    figure(d, XL, lp, alpha=int(255 * (1 - 0.35 * dark)))
    hx, hy = XL + lp["rh"][0], GY + lp["rh"][1]
    Z.plato(d, g, PL, 1.0 - 0.25 * seg(t, s1, t30), h=6, gris=0.6 * dark)
    # la mano de humo enfrente imita cada bocado (mano y brazo antes de que aparezca entera)
    sh = 70 * seg(t, s1 + 1.0, s1 + 2.0) + 90 * seg(t, t10 + 0.6, t10 + 1.6) + 70 * seg(t, tq, tq + 0.8)
    cuerpo = seg(t, t30, t30 + 1.8)
    if sh > 0 or cuerpo > 0:
        sp = Z.espejo(Z.sentado(eL, 0.0))                   # la sombra es su espejo: come igual que él, con la izquierda
        sx = SHX + 4 * math.sin(t * 1.2)
        if cuerpo > 0:
            Z.mini_figure(do, sx, sp, k=1.0, col=Z.SHADOW, alpha=235 * cuerpo)
            hx2, hy2 = sx + sp["head"][0], GY + sp["head"][1]
            for i in range(6):                               # humo que le sale de la cabeza
                ph = (t * 0.5 + i / 6) % 1
                px, py = hx2 + 14 * math.sin(t * 2 + i), hy2 - 40 - 110 * ph; r = 14 + 10 * ph
                do.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=Z.SHADOW + (int(200 * cuerpo * (1 - ph)),))
        a = int(min(235, sh + 235 * cuerpo))
        nx, ny = sx + sp["neck"][0], GY + sp["neck"][1] + 30
        ax, ay = sx + sp["re"][0], GY + sp["re"][1]; bx, by = sx + sp["rh"][0], GY + sp["rh"][1]
        do.line([(nx * S, ny * S), (ax * S, ay * S), (bx * S, by * S)], fill=Z.SHADOW + (a,), width=int(16 * S), joint="curve")
        do.ellipse([(bx - 13) * S, (by - 13) * S, (bx + 13) * S, (by + 13) * S], fill=Z.SHADOW + (a,))
        for i in range(4):                                   # humo que sale de la mano
            ph = (t * 0.8 + i / 4) % 1
            px, py = bx + 10 * math.sin(t * 3 + i), by - 20 - 70 * ph
            do.ellipse([(px - 9) * S, (py - 9) * S, (px + 9) * S, (py + 9) * S], fill=Z.SHADOW + (int(a * 0.6 * (1 - ph)),))
    # humo en su propia mano izquierda
    if t > s1 + 0.4:
        a = int(140 * seg(t, s1 + 0.4, s1 + 1.4) * (1 - 0.0 * t))
        for i in range(3):
            ph = (t * 0.9 + i / 3) % 1
            do.ellipse([(hx - 8 + 6 * math.sin(t * 4 + i)) * S, (hy - 14 - 50 * ph) * S, (hx + 8 + 6 * math.sin(t * 4 + i)) * S, (hy + 2 - 50 * ph) * S], fill=Z.SHADOW + (int(a * (1 - ph)),))
    # ---------- DERECHA: con la derecha ----------
    Z.mantel(d, PR + 10, 170)
    eR = comer(t, s2 + 0.2, ph=0.3) * (1 - seg(t, t30 + 1.0, t30 + 1.4)) + comer(t, s2 + 0.2, ph=0.3) * seg(t, thad + 3.0, thad + 3.8)
    joy = seg(t, t30 + 1.4, t30 + 2.2) * (1 - seg(t, thad + 3.0, thad + 3.8))
    rp = Z.sentado(eR * (1 - joy), 0.0, joy=joy)
    rp = Z.espejo(rp)
    figure(d, XR, rp)
    rhx, rhy = XR + rp["rh"][0], GY + rp["rh"][1]
    luz = 0.3 * seg(t, s2 + 0.6, s2 + 1.6) + 0.25 * seg(t, t10 + 0.6, t10 + 1.6) + 0.45 * seg(t, t30 + 0.4, t30 + 2.4)
    Z.plato(d, g, PR, 1.0 - 0.15 * seg(t, s2, t30), h=6, vapor=1.0, t=t + 0.4, luz=luz)
    if t > s2 + 0.2 and joy < 0.5:                           # la mano derecha deja luz
        g.ellipse([rhx - 34, rhy - 34, rhx + 34, rhy + 34], fill=(120, 240, 232, int(150 * seg(t, s2 + 0.2, s2 + 0.9))))
        tc = tocando(t, s2 + 0.2 - 0.3 * 1.7)
        if tc > 0:
            for i in range(6):
                ang = i * math.pi / 3; rr = 18 + 40 * (1 - tc)
                px, py = PR + rr * math.cos(ang), GY - 30 + rr * 0.5 * math.sin(ang)
                d.ellipse([(px - 4) * S, (py - 4) * S, (px + 4) * S, (py + 4) * S], fill=(160, 245, 238, int(220 * tc)))
    if t > t30 + 1.2: g.ellipse([XR - 160, GY - 330, XR + 60, GY + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 1.2, t30 + 2.8))))
    Z.anillos(d, PR, GY - 60, t, t30 + 1.0, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "IZQUIERDA", "DERECHA", t10, t30, 46, lx=XL + 60, rx=XR - 80)
    Z.subs(d, t, [(0.6, s1 - 0.15, "LA MISMA COMIDA"), (s1, s2 - 0.15, "UNO COME CON LA IZQUIERDA"), (s2, t10 - 0.1, "EL OTRO, CON LA DERECHA")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN COME IGUAL QUE ÉL?")
    Z.fuente(d, t, thad, tfin, ["«COME CON TU DERECHA:", "EL SHAITÁN COME", "CON SU IZQUIERDA»"], "SAHIH MUSLIM 2020")
    Z.final(d, t, tfin, "COME CON LA DERECHA.", "NO TE PAREZCAS A ÉL.", task, "¿Y TÚ, CON QUÉ MANO", "COMES?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
