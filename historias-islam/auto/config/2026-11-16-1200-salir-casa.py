# Estilo Noche · SIN DUA vs CON DUA · "al salir de casa" (Sunan Abi Dawud 5095)
# Continuación de BISMILLAH en casa (14 nov, el mejor vídeo Noche): dos personas salen por su puerta cada mañana.
# Al que sale sin decir nada le siguen sombras de humo; al que dice «Bismillah, confío en Allah» le cubre una cúpula de luz
# y las sombras se deshacen al tocarla. Día 30: las sombras rodean al primero y huyen del segundo.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-16-1200-salir-casa.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Los dos salen de casa. Pero algo les sigue.",
         "Uno abre la puerta y se va, sin decir nada.",
         "El otro dice: bismillah, confío en Allah.",
         "Día diez.",
         "¿A quién crees que siguen?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: al que sale de casa y dice esto, se le dice: has sido guiado, protegido, y te basta. Y los demonios se apartan de él.",
         "Bismillah. Y sal tranquilo.",
         "¿Tú lo dices al salir de casa?"]
PAUSAS = [0.6, 0.7, 1.0, 0.5, 2.2, 0.6, 0.8, 0.9, 1.6]
def SFX(s): return [dict(t=s[2] + 1.0, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-16-1200-salir-casa.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

DL, DR = 110, 950            # puertas
FL0, FL1 = 110, 300          # izquierda: sale de la puerta y anda hasta aquí
FR0, FR1 = 950, 770          # derecha
def mirror(p): return {j: (-v[0], v[1]) for j, v in p.items()}
def lerp_pose(a, b, k): return {j: (lerp(a[j][0], b[j][0], k), lerp(a[j][1], b[j][1], k)) for j in a}

def frame(t):
    bright = 0.15 + 0.15 * seg(t, t10, t10 + 1.2) + 0.7 * seg(t, t30 + 0.4, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer(); over, do = Z.new_layer()
    dark = 0.3 * seg(t, s1 + 1.2, t10) + 0.25 * seg(t, t10, t10 + 1.5) + 0.45 * seg(t, t30, t30 + 2)
    # ---------- lo que no se ve ----------
    Z.grietas(d, FL1, 0.35 * seg(t, s1 + 1.5, t10) + 0.25 * seg(t, t10, t10 + 1.5) + 0.4 * seg(t, t30, t30 + 2.5), seed=4)
    Z.roots(d, 0.3 * seg(t, s2 + 3.0, s2 + 4.6) + 0.25 * seg(t, t10, t10 + 1.5) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), x0=FR1)
    # ---------- puertas ----------
    Z.puerta(d, DL, seg(t, s1 - 0.2, s1 + 0.4) * (1 - seg(t, s1 + 2.0, s1 + 2.5)), alpha=255 * (1 - 0.3 * dark), lado=1)
    Z.puerta(d, DR, seg(t, s2 - 0.9, s2 - 0.4) * (1 - seg(t, s2 + 1.4, s2 + 1.9)), lado=-1)
    # ---------- IZQUIERDA: SALE SIN DUA ----------
    wk = seg(t, s1 + 0.2, s1 + 2.0)
    xl = lerp(FL0, FL1, wk)
    if t < s1 + 0.2: lp = P["stand"]
    elif t < s1 + 2.0: lp = Z.walk_pose(t * 7)
    elif t < t30: lp = lerp_pose(P["stand"], P["sad"], 0.18 * seg(t, t10, t10 + 1.0))       # se encoge un poco
    else: lp = lerp_pose(lerp_pose(P["stand"], P["sad"], 0.18), P["sad"], seg(t, t30 + 0.3, t30 + 1.5))
    if t < s1 - 0.1: xl = FL0 + 0  # dentro de la puerta
    figure(d, xl, lp, alpha=int(255 * (1 - 0.35 * dark)))
    # sombras que le siguen (en capa sin halo, por encima)
    SH = [(-1.0, 175, 0.62), (t10 + 0.2, 440, 0.7), (t30 + 0.3, 205, 0.85)]
    for i, (a, xs, ks) in enumerate(SH):
        if t > a:
            x0 = -120 if i != 1 else 620
            x = lerp(x0, xs, seg(t, a, a + 1.8)) + 6 * math.sin(t * 1.3 + i)
            if i == 0: x = lerp(540, xs, seg(t, s1 + 0.6, s1 + 2.6)) + 6 * math.sin(t * 1.3)   # ya está ahí desde el primer fotograma
            kk = ks * (1 + 0.15 * seg(t, t30, t30 + 2))
            reach = ((math.sin(t * 3 + i) + 1) / 2) * (seg(t, s1 + 2.6, s1 + 3.1) if i == 0 else seg(t, a + 1.8, a + 2.3)) if i != 1 else 0
            Z.sombra(do, x, kk, 225 * seg(t, a, a + 0.7), t + i * 1.7, reach=reach)
    # ---------- DERECHA: SALE CON DUA ----------
    wr = seg(t, s2 + 1.4, s2 + 3.0)
    xr = lerp(FR0, FR1, wr)
    if t < s2: rp = P["stand"]
    elif t < s2 + 1.4: rp = pose_mix("stand", "joy", 0.3 * seg(t, s2, s2 + 0.4) * (1 - seg(t, s2 + 1.0, s2 + 1.4)))   # levanta un poco las manos al decirlo
    elif t < s2 + 3.0: rp = Z.walk_pose(t * 7)
    elif t < t30 + 1.4: rp = P["stand"]
    else: rp = pose_mix("stand", "joy", seg(t, t30 + 1.4, t30 + 2.0) * (1 - seg(t, thad + 3.0, thad + 3.8)))
    figure(d, xr, mirror(rp))
    dome = seg(t, s2 + 0.6, s2 + 1.6) * (0.75 + 0.25 * seg(t, t30 + 0.4, t30 + 2.0))
    Z.cupula(d, g, xr, dome, t, r=170, ry=2.25)
    Z.anillos(d, xr, GY - 300, t, s2 + 0.2, 2.4)
    # sombras que intentan acercarse y se deshacen al tocar la cúpula
    for i, a in enumerate((s2 + 3.2, t10 + 0.4, tq + 0.6)):
        if a < t < a + 3.0:
            hit = a + 1.6
            sx = lerp(1150, xr + 200, seg(t, a, hit)) if i != 1 else lerp(560, xr - 205, seg(t, a, hit))
            kk = 0.6 * (1 - 0.7 * seg(t, hit, hit + 0.9))
            al = 220 * seg(t, a, a + 0.5) * (1 - seg(t, hit + 0.1, hit + 0.9))
            Z.sombra(do, sx, kk, al, t + 2.3 + i)
            if hit < t < hit + 0.8:
                fx = xr + (175 if i != 1 else -175)
                g.ellipse([fx - 110, GY - 330, fx + 110, GY - 90], fill=(120, 240, 235, int(200 * (1 - seg(t, hit, hit + 0.8)))))
    if t > t30 + 0.4:                                    # día 30: las sombras huyen hacia arriba y se deshacen
        for i in range(2):
            k = seg(t, t30 + 0.4 + 0.3 * i, t30 + 2.6 + 0.3 * i)
            if 0 < k < 1:
                Z.sombra(do, xr + (-265 + 465 * i), 0.5 * (1 - 0.6 * k), 200 * (1 - k), t + i, y0=GY - 40 - 520 * k)
    if t > t30 + 1.2: g.ellipse([xr - 120, GY - 380, xr + 120, GY + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 1.2, t30 + 2.8))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SIN DUA", "CON DUA", t10, t30, 50, lx=290, rx=770)
    Z.subs(d, t, [(0.5, s1 - 0.15, "ALGO LES SIGUE..."), (s1, s2 - 0.15, "UNO SALE SIN DECIR NADA"), (s2, t10 - 0.1, "EL OTRO: «BISMILLAH»")])
    Z.pregunta(d, t, tq, t30, "¿A QUIÉN SIGUEN?")
    Z.fuente(d, t, thad, tfin, ["«HAS SIDO GUIADO,", "PROTEGIDO", "Y TE BASTA»"], "SUNAN ABI DAWUD 5095")
    Z.final(d, t, tfin, "BISMILLAH.", "Y SAL TRANQUILO.", task, "¿TÚ LO DICES", "AL SALIR DE CASA?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
