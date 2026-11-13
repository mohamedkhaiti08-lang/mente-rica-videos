# Estilo Noche · SE OLVIDA vs BISMILLAH · "dos casas, la misma cena" (Sahih Muslim 2018)
# Variante "lo que ves vs lo que no ves": una sombra de humo entra en la casa del que no nombra a Allah y se sienta a su mesa.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-14-1200-bismillah-casa.py salida.mp4 [t1 t2 ... para fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, star8, spaced, figure

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Dos casas. La misma cena.",
         "Uno entra y come, sin decir nada.",
         "El otro dice: bismillah.",
         "Día diez.",
         "¿Quién crees que cena solo?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: si entras y comes sin nombrar a Allah, el shaitán dice: aquí tenemos casa y cena.",
         "Di bismillah. Cierra la puerta.",
         "¿Y tú, te acuerdas siempre?"]
PAUSAS = [0.7, 0.8, 1.2, 0.7, 2.2, 0.8, 1.0, 1.0, 1.6]
def SFX(s): return [dict(t=s[2] + 0.9, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=os.path.join(HERE, "2026-11-14-1200-bismillah-casa.guion.json"))
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

LXc, RXc = 270, 810                 # centros de las casas
FL, TL, SL = 160, 320, 425          # izquierda: figura, mesa, sitio de la sombra
FR, TR = 920, 760                   # derecha: figura, mesa
def mirror(p): return {j: (-v[0], v[1]) for j, v in p.items()}
def eat_pose(t, ph=0.0):
    k = (math.sin(t * 4 + ph) + 1) / 2
    p = dict(P["stand"]); p["re"] = (44, -206); p["rh"] = (lerp(116, 34, k), lerp(-126, -268, k)); return p

def frame(t):
    bright = 0.15 + 0.2 * seg(t, t10, t10 + 1.2) + 0.65 * seg(t, t30, t30 + 2.5)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer(); over, do = Z.new_layer()
    dark = 0.3 * seg(t, s1 + 1.5, t10) + 0.25 * seg(t, t10, t10 + 1.5) + 0.45 * seg(t, t30, t30 + 2)
    # interior de las casas: la izquierda se oscurece, la derecha se llena de luz cálida
    du.rectangle([62 * S, (GY - 388) * S, 478 * S, GY * S], fill=(4, 4, 8, int(170 * dark)))
    warm = 0.25 * seg(t, s2, s2 + 1.2) + 0.25 * seg(t, t10, t10 + 1.2) + 0.5 * seg(t, t30, t30 + 2)
    g.rectangle([610, GY - 380, 1010, GY], fill=(250, 210, 130, int(70 * warm)))
    # ---------- IZQUIERDA: SE OLVIDA ----------
    Z.grietas(d, LXc, 0.4 * seg(t, t10, t10 + 1.5) + 0.6 * seg(t, t30, t30 + 2.5))
    Z.casa(d, 60, 480, door=("r", 215), door_open=seg(t, s1 - 0.2, s1 + 0.5), alpha=255 * (1 - 0.3 * dark))
    Z.mesa(d, TL, alpha=255 * (1 - 0.3 * dark))
    nl = 1 - 0.2 * seg(t, s1 + 2.2, t10) - 0.35 * seg(t, t10, t10 + 1.5) - 0.45 * seg(t, t30, t30 + 2.2)
    Z.plato(d, g, TL, nl, gris=dark, vapor=1 - seg(t, s1 + 1, t10), t=t)
    # sombra 1: entra por la puerta abierta y se sienta a la mesa
    if t > s1 + 0.1:
        ks = 0.8 + 0.15 * seg(t, t10, t10 + 1.5) + 0.25 * seg(t, t30, t30 + 2)
        x = lerp(600, SL + 15, seg(t, s1 + 0.3, s1 + 2.1))
        reach = ((math.sin(t * 4 + 2) + 1) / 2) * seg(t, s1 + 2.1, s1 + 2.5)
        Z.sombra(do, x, ks, 235 * seg(t, s1 + 0.1, s1 + 0.8), t, reach=reach)
    if t > t30:                                 # y trae compañía
        Z.sombra(do, lerp(640, 520, seg(t, t30 + 0.3, t30 + 2)), 0.7, 200 * seg(t, t30 + 0.3, t30 + 1.2), t + 1.7)
    if t < s1 + 0.4: lp = P["stand"]
    elif t < t30: lp = eat_pose(t)
    else: lp = pose_mix("stand", "sad", seg(t, t30, t30 + 1.2))
    figure(d, FL, lp, alpha=int(255 * (1 - 0.35 * dark)))
    # ---------- DERECHA: BISMILLAH ----------
    Z.roots(d, 0.25 * seg(t, s2 + 0.6, s2 + 2.6) + 0.25 * seg(t, t10, t10 + 1.5) + 0.5 * seg(t, t30, t30 + 2.5), x0=RXc)
    Z.casa(d, 600, 1020, door=("l", 215), door_open=0)
    shield = seg(t, s2 + 0.2, s2 + 0.8)
    if shield > 0:                               # la puerta se ilumina
        d.line([(600 * S, (GY - 215) * S), (600 * S, GY * S)], fill=(130, 240, 232, int(255 * shield)), width=8 * S)
        g.rectangle([585, GY - 230, 615, GY], fill=(80, 230, 225, int(150 * shield)))
    Z.mesa(d, TR)
    Z.plato(d, g, TR, 1.0, vapor=1.0, t=t + 0.4, luz=0.4 * seg(t, s2, s2 + 1) + 0.6 * seg(t, t30, t30 + 2))
    Z.anillos(d, FR, GY - 300, t, s2, 2.6)
    # sombras que lo intentan y rebotan en la puerta
    for a in (s2 - 0.3, t10 + 0.2):              # sombras que bajan del cielo y se deshacen sobre el tejado
        if a < t < a + 2.6:
            hit = a + 1.2
            y = lerp(GY - 630, GY - 548, seg(t, a, hit))
            kk = 0.48 * (1 - 0.7 * seg(t, hit, hit + 0.9))
            al = 220 * seg(t, a, a + 0.5) * (1 - seg(t, hit + 0.2, hit + 1.0))
            Z.sombra(du, RXc, kk, al, t + 3.1, y0=y)   # debajo de los textos
            if hit < t < hit + 0.8:
                g.ellipse([RXc - 170, GY - 640, RXc + 170, GY - 470], fill=(120, 240, 235, int(190 * (1 - seg(t, hit, hit + 0.8)))))
    if t < s2: rp = P["stand"]
    elif t < s2 + 1.6: rp = pose_mix("stand", "joy", 0.35 * seg(t, s2, s2 + 0.4) * (1 - seg(t, s2 + 1.2, s2 + 1.6)))
    elif t < t30 + 1.6: rp = eat_pose(t, 1.3)
    else: rp = pose_mix("stand", "joy", seg(t, t30 + 1.6, t30 + 2.2) * (1 - seg(t, thad + 2.5, thad + 3.2)))
    figure(d, FR, mirror(rp))
    lamp = seg(t, t30 + 0.8, t30 + 2.2)
    if lamp > 0:                                 # se enciende una lámpara colgada en la casa bendecida
        ly = GY - 330
        d.line([(RXc * S, (GY - 388) * S), (RXc * S, (ly - 22) * S)], fill=CREAM + (int(255 * lamp),), width=3 * S)
        star8(d, RXc, ly, 24 * lamp, t * 0.3)
        g.ellipse([RXc - 110, ly - 100, RXc + 110, ly + 100], fill=(250, 220, 140, int(160 * lamp)))
    if t > t30 + 1.5: g.ellipse([FR - 120, GY - 380, FR + 120, GY + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 1.5, t30 + 3))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SE OLVIDA", "BISMILLAH", t10, t30, 44, lx=LXc, rx=770)
    Z.subs(d, t, [(0.6, s1 - 0.2, "LA MISMA CENA"), (s1, s2 - 0.2, "UNO NO DICE NADA"), (s2, t10 - 0.1, "EL OTRO: «BISMILLAH»")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN CENA SOLO?")
    Z.fuente(d, t, thad, tfin, ["SIN NOMBRAR A ALLAH,", "EL SHAITÁN TIENE", "CASA Y CENA"], "SAHIH MUSLIM 2018")
    Z.final(d, t, tfin, "DI BISMILLAH.", "CIERRA LA PUERTA.", task, "¿Y TÚ,", "TE ACUERDAS SIEMPRE?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
