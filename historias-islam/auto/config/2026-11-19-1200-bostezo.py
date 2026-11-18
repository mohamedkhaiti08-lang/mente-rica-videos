# Estilo Noche · BOCA ABIERTA vs SE LA TAPA · "al bostezar" (Sahih Muslim 2995)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (la sombra que se cuela), como Bismillah (925 TikTok) y salir de casa (806).
# Gancho de curiosidad para Instagram: «¿Sabes por qué un musulmán se tapa la boca al bostezar?».
# Uno bosteza con la boca abierta y un hilo de humo se le cuela dentro; debajo del suelo se le acumula humo oscuro y cada día está más cansado.
# El otro se tapa con la mano: el humo choca contra la mano y se deshace en luz; debajo le crecen raíces. Día 30: uno hundido con la sombra encima, el otro en pie con luz.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-19-1200-bostezo.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes por qué un musulmán se tapa la boca al bostezar?",
         "Uno bosteza con la boca abierta.",
         "El otro se la tapa con la mano.",
         "Día diez.",
         "¿Qué crees que se le cuela?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: cuando bosteces, tápate la boca con la mano, porque el shaitán entra.",
         "Un gesto pequeño. Una puerta cerrada.",
         "¿Tú te tapas la boca al bostezar?"]
PAUSAS = [0.7, 1.4, 1.4, 1.0, 2.2, 0.7, 0.8, 0.9, 1.6]
def SFX(s): return [dict(t=s[2] + 1.3, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-19-1200-bostezo.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, XR = 300, 780

def yawn_k(t, a, dur=2.2):
    """0→1→0: intensidad del bostezo que empieza en a."""
    return seg(t, a, a + 0.5) * (1 - seg(t, a + dur - 0.5, a + dur))

def frame(t):
    bright = 0.15 + 0.15 * seg(t, t10, t10 + 1.2) + 0.7 * seg(t, t30 + 0.4, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, do = Z.new_layer(); under, du = Z.new_layer()
    dark = 0.3 * seg(t, s1 + 2.0, t10) + 0.25 * seg(t, t10, t10 + 2.0) + 0.45 * seg(t, t30, t30 + 2)
    # bostezos
    yL = max(yawn_k(t, s1 + 0.1), yawn_k(t, t10 + 0.3))
    yR = max(yawn_k(t, s2 + 0.1), yawn_k(t, t10 + 0.6))
    # ---------- lo que no se ve ----------
    Z.humo_dentro(d, XL, 0.3 * seg(t, s1 + 1.6, s1 + 3.0) + 0.3 * seg(t, t10 + 1.4, t10 + 3.0) + 0.4 * seg(t, t30, t30 + 2.4), t)
    Z.roots(d, 0.3 * seg(t, s2 + 1.6, s2 + 3.2) + 0.25 * seg(t, t10 + 1.6, t10 + 3.0) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), x0=XR)
    # ---------- IZQUIERDA: BOCA ABIERTA ----------
    tired = 0.2 * seg(t, t10 + 2.4, t10 + 3.4) + 0.8 * seg(t, t30 + 0.3, t30 + 1.6)
    lp = Z.lerp_pose(Z.lerp_pose(P["stand"], P["sad"], tired), Z.BOSTEZO, yL)
    figure(d, XL, lp, alpha=int(255 * (1 - 0.35 * dark)))
    hx, hy = XL + lp["head"][0], GY + lp["head"][1]
    Z.boca(d, hx + 14, hy + 8, yL)
    # la sombra que espera a su lado (ya visible en el primer fotograma) y crece cada vez que se cuela algo
    kL = 0.55 + 0.15 * seg(t, s1 + 1.6, s1 + 2.6) + 0.12 * seg(t, t10 + 1.4, t10 + 2.4) + 0.2 * seg(t, t30, t30 + 2)
    xs = lerp(120, 150, seg(t, 1.2, 2.6)) + 30 * seg(t, t10 + 1.4, t10 + 2.4) + 40 * seg(t, t30, t30 + 2) + 6 * math.sin(t * 1.3)
    reach = 0.6 * seg(t, tq, tq + 0.8) * (1 - seg(t, t30, t30 + 0.6)) * (0.6 + 0.4 * math.sin(t * 3))
    Z.sombra(du, xs, kL, 230 * seg(t, -0.5, 0.4), t, reach=0)
    for a in (s1 + 0.5, t10 + 0.7):                       # el humo se cuela en la boca abierta
        k = seg(t, a, a + 1.2)
        if 0 < k and t < a + 1.6:
            Z.hilo_sombra(do, xs + 20, GY - 230 * kL, hx + 14, hy + 8, k, t, alpha=230 * (1 - seg(t, a + 1.2, a + 1.6)))
    if t > t30 + 0.3:                                     # día 30: otra sombra se le sube encima
        k2 = seg(t, t30 + 0.3, t30 + 2.2)
        Z.sombra(du, lerp(620, XL + 150, k2), 0.7, 220 * k2, t + 1.7)
    # ---------- DERECHA: SE LA TAPA ----------
    cover = max(seg(t, s2 + 0.35, s2 + 0.75) * (1 - seg(t, s2 + 1.8, s2 + 2.2)), seg(t, t10 + 0.85, t10 + 1.25) * (1 - seg(t, t10 + 2.3, t10 + 2.7)))
    rp = Z.lerp_pose(Z.lerp_pose(P["stand"], Z.BOSTEZO, yR), Z.TAPA, cover)
    if t > t30: rp = Z.lerp_pose(rp, P["joy"], seg(t, t30 + 1.4, t30 + 2.0) * (1 - seg(t, thad + 3.0, thad + 3.8)))
    rp = Z.espejo(rp)
    figure(d, XR, rp)
    rhx, rhy = XR + rp["head"][0], GY + rp["head"][1]
    Z.boca(d, rhx - 14, rhy + 8, yR * (1 - cover) * 0.6)
    kR = 0.55 * (1 - seg(t, t30 + 0.4, t30 + 2.4))
    xsr = 965 + 6 * math.sin(t * 1.2 + 2)
    Z.sombra(du, xsr, kR, 220 * seg(t, -0.5, 0.4) * (1 - seg(t, t30 + 0.4, t30 + 2.4)), t + 3.1, y0=GY - 300 * seg(t, t30 + 0.4, t30 + 2.4))
    for a in (s2 + 0.5, t10 + 1.0):                       # el humo choca con la mano y se deshace en luz
        hit = a + 1.0; k = seg(t, a, hit)
        if a < t < hit + 0.2:
            Z.hilo_sombra(do, xsr - 20, GY - 140, rhx - 22, rhy + 10, k, t, alpha=225 * (1 - seg(t, hit, hit + 0.2)))
        if hit <= t < hit + 0.9:
            q = seg(t, hit, hit + 0.9)
            g.ellipse([rhx - 22 - 70, rhy - 60, rhx - 22 + 70, rhy + 80], fill=(120, 240, 235, int(200 * (1 - q))))
            for i in range(8):
                ang = i * math.pi / 4; rr = 14 + 70 * q
                px, py = rhx - 22 + rr * math.cos(ang), rhy + 10 + rr * math.sin(ang)
                d.ellipse([(px - 5) * S, (py - 5) * S, (px + 5) * S, (py + 5) * S], fill=(150, 245, 238, int(230 * (1 - q))))
    if t > t30 + 1.2: g.ellipse([XR - 120, GY - 380, XR + 120, GY + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 1.2, t30 + 2.8))))
    Z.anillos(d, XR, GY - 200, t, t30 + 1.0, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "BOCA ABIERTA", "SE LA TAPA", t10, t30, 46, lx=XL - 10, rx=XR - 10)
    Z.subs(d, t, [(0.6, s1 - 0.15, "ALGO ESPERA..."), (s1, s2 - 0.15, "UNO BOSTEZA ASÍ"), (s2, t10 - 0.1, "EL OTRO SE TAPA")])
    Z.pregunta(d, t, tq, t30, "¿QUÉ SE LE CUELA?")
    Z.fuente(d, t, thad, tfin, ["«TÁPATE LA BOCA,", "PORQUE EL SHAITÁN", "ENTRA»"], "SAHIH MUSLIM 2995")
    Z.final(d, t, tfin, "UN GESTO PEQUEÑO.", "UNA PUERTA CERRADA.", task, "¿TÚ TE TAPAS LA BOCA", "AL BOSTEZAR?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
