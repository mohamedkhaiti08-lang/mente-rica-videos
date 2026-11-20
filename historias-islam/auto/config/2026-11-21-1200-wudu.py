# Estilo Noche · SIN WUDU vs CON WUDU · "¿Sabes qué se va con el agua cuando un musulmán hace el wudu?" (Sahih Muslim 244)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (Bismillah 916 TikTok, el mejor Noche), gancho de curiosidad para IG.
# Los dos se manchan cada día (manchas de humo en los ojos, las manos y los pies). Uno sigue con el móvil: las manchas se acumulan,
# se apaga y bajo el suelo crece un barro oscuro. El otro hace el wudu en una fuente: cada gota que cae de su cara y sus manos
# se lleva una mancha, que al tocar la tierra se vuelve luz; bajo el suelo corre un río de luz. Lema: «El agua se lleva más de lo que ves».
# Objetos nuevos: fuente (grifo + pila), poses LAVA_MANOS / LAVA_CARA, manchas en el cuerpo, gotas que se llevan manchas, río de luz y barro.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-21-1200-wudu.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué se va con el agua cuando un musulmán hace el wudu?",
         "Los dos fallan cada día, con lo que miran y lo que tocan.",
         "Uno sigue sin más.",
         "El otro hace el wudu.",
         "Día diez.",
         "¿Quién crees que llega limpio?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: cuando el musulmán lava su cara, el agua se lleva los pecados de sus ojos… hasta que termina limpio.",
         "El agua se lleva más de lo que ves.",
         "¿Cuántas veces al día haces el wudu?"]
PAUSAS = [0.5, 0.8, 0.9, 1.5, 0.7, 1.9, 0.5, 0.7, 0.8, 1.4]
def SFX(s): return [dict(t=s[3] + 1.2, f=1320, dur=0.8, v=0.06), dict(t=s[6], f=660, dur=2.0, v=0.08), dict(t=s[6] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-21-1200-wudu.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.07)
s0, s1, s2, s3, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, XR = 270, 740
FX = XR + 62                      # chorro de la fuente
TEAL = (130, 240, 232)

# ---------- poses nuevas ----------
LAVA_MANOS = dict(P["stand"]); LAVA_MANOS.update(le=(22, -214), lh=(56, -176), re=(36, -218), rh=(66, -180), head=(6, -298))
LAVA_CARA = dict(P["stand"]); LAVA_CARA.update(le=(-40, -238), lh=(-14, -300), re=(44, -240), rh=(16, -300), head=(4, -300))
PHONE = dict(P["stand"]); PHONE.update(re=(34, -200), rh=(30, -262), head=(-4, -298))

def fuente(d, g, x, t, agua=1.0):
    """Fuente de pared: poste, caño, pila y chorro de agua (objeto nuevo)."""
    c = CREAM + (255,); w = 6 * S
    px = x + 90
    d.line([(px * S, GY * S), (px * S, (GY - 380) * S)], fill=c, width=8 * S)                       # poste
    d.line([(px * S, (GY - 360) * S), ((x + 6) * S, (GY - 360) * S), ((x + 6) * S, (GY - 340) * S)], fill=c, width=w, joint="curve")  # caño
    d.ellipse([(px - 18) * S, (GY - 396) * S, (px + 18) * S, (GY - 360) * S], outline=c, width=4 * S)  # llave
    d.line([((x - 70) * S, (GY - 70) * S), ((x - 56) * S, GY * S), ((x + 76) * S, GY * S), ((x + 90) * S, (GY - 70) * S)], fill=c, width=w, joint="curve")  # pila
    if agua > 0:
        for i in range(9):                                                                            # chorro
            ph = (t * 2.2 + i / 9) % 1; y = GY - 336 + ph * 270
            d.ellipse([(x + 6 - 5) * S, (y - 9) * S, (x + 6 + 5) * S, (y + 9) * S], fill=TEAL + (int(230 * agua),))
        g.line([x + 6, GY - 336, x + 6, GY - 66], fill=(90, 230, 225, int(110 * agua)), width=22)
        d.line([((x - 52) * S, (GY - 46) * S), ((x + 74) * S, (GY - 46) * S)], fill=TEAL + (int(200 * agua),), width=4 * S)

SPOTS = [("head", -12, -6), ("head", 12, 4), ("rh", 0, 0), ("lh", 0, 0), ("rf", 0, -8), ("lf", 0, -8), ("neck", 8, 30),
         ("hip", -6, -20), ("le", 0, 0), ("re", 0, 0), ("lk", 0, 0), ("rk", 0, 0), ("head", 0, 16), ("hip", 6, 20)]
def manchas(d, x, p, n, k, alpha=230, seed=3):
    """Manchas de humo pegadas al cuerpo (ojos, manos, pies...). n = cuántas, k = tamaño."""
    if k <= 0 or alpha <= 0: return
    rnd = random.Random(seed)
    for i in range(min(int(math.ceil(n)), len(SPOTS))):
        j, ox, oy = SPOTS[i]; fr = min(1.0, n - i)
        r = (9 + 5 * rnd.random()) * k * fr
        cx, cy = x + p[j][0] + ox, GY + p[j][1] + oy
        d.ellipse([(cx - r) * S, (cy - r * 0.8) * S, (cx + r) * S, (cy + r * 0.8) * S], fill=Z.SHADOW + (int(alpha),))

def barro(d, x, k, t, col=(58, 54, 70)):
    """Barro oscuro que se acumula bajo el suelo (objeto nuevo)."""
    if k <= 0: return
    rnd = random.Random(9)
    for i in range(int(26 * k)):
        bx = x + rnd.uniform(-150, 150); by = GY + 30 + rnd.uniform(0, 330 * k); r = rnd.uniform(18, 40)
        d.ellipse([(bx - r) * S, (by - r * 0.6) * S, (bx + r) * S, (by + r * 0.6) * S], fill=col + (int(220 * min(1, k * 1.6)),))

def rio_luz(d, g, x, k, t):
    """Río de luz que corre bajo el suelo: ondas turquesa que crecen (objeto nuevo)."""
    if k <= 0: return
    for j in range(4):
        y0 = GY + 70 + j * 80
        if k < j * 0.22: continue
        kk = min(1, (k - j * 0.22) / 0.4); half = 60 + 190 * kk
        pts = [(x + u, y0 + 12 * math.sin(u / 34 + t * 2 + j)) for u in range(int(-half), int(half) + 1, 12)]
        d.line([(a * S, b * S) for a, b in pts], fill=TEAL + (int(200 * kk),), width=4 * S)
        g.line(pts, fill=(80, 230, 225, int(90 * kk)), width=14)

def wudu_pose(t, a):
    """Alterna lavarse las manos y la cara (ciclo de 2,4 s). Devuelve (pose, fase_cara)."""
    if t < a: return P["stand"], 0.0
    u = ((t - a) / 2.4) % 1; k = 0.5 - 0.5 * math.cos(2 * math.pi * u)
    k0 = seg(t, a, a + 0.5)
    pm = Z.lerp_pose(LAVA_MANOS, LAVA_CARA, k)
    return Z.lerp_pose(P["stand"], pm, k0), k * k0

def gotas_manchadas(d, g, t, a, b, x0, y0, n=5, seed=4):
    """Gotas que caen de la cara/manos: cada una lleva una mancha que se deshace en luz al tocar la tierra."""
    if t < a or t > b + 1.4: return
    rnd = random.Random(seed)
    for i in range(n):
        ph = ((t - a) * 0.7 + i / n) % 1
        if t > b and ph > (t - b) / 1.4 * 0 + 1: continue
        fx = x0 + rnd.uniform(-26, 26); y = y0 + ph * (GY + 40 - y0)
        al = 255 * seg(t, a, a + 0.5) * (1 - seg(t, b, b + 1.4))
        if y < GY:
            Z.gota(d, g, fx, y, r=12, alpha=al)
            dk = 1 - min(1, max(0, (y - y0) / (GY - y0)))                 # la mancha va desapareciendo al caer
            d.ellipse([(fx - 6) * S, (y - 5) * S, (fx + 6) * S, (y + 5) * S], fill=(40, 36, 52, int(al * dk)))
        else:
            r = 6 + 20 * (y - GY) / 40
            g.ellipse([fx - r, GY - r * 0.4, fx + r, GY + r * 0.4], fill=(120, 240, 232, int(al * 0.7)))

def frame(t):
    bright = 0.15 + 0.15 * seg(t, t10, t10 + 1.2) + 0.7 * seg(t, t30 + 0.4, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, do = Z.new_layer()
    dark = 0.3 * seg(t, t10, t10 + 2.0) + 0.45 * seg(t, t30, t30 + 2)
    # ---------- lo que no se ve ----------
    barro(do, XL, 0.15 * seg(t, s2 + 0.5, s2 + 2.5) + 0.35 * seg(t, t10 + 0.6, t10 + 2.4) + 0.5 * seg(t, t30 + 0.4, t30 + 2.6), t)
    Z.grietas(d, XL, 0.6 * seg(t, t30 + 0.4, t30 + 2.6), seed=7)
    rio_luz(d, g, XR + 20, 0.25 * seg(t, s3 + 1.0, s3 + 3.0) + 0.3 * seg(t, t10 + 1.0, t10 + 2.6) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), t)
    # ---------- IZQUIERDA: sin wudu ----------
    lp = Z.lerp_pose(P["stand"], PHONE, seg(t, s2, s2 + 0.6))
    if t > t30 + 0.6:
        droop = 0.5 * seg(t, t30 + 0.6, t30 + 2.0)
        lp = dict(lp); lp["head"] = (lp["head"][0] + 14 * droop, lp["head"][1] + 22 * droop); lp["neck"] = (lp["neck"][0] + 8 * droop, lp["neck"][1] + 12 * droop)
    figure(d, XL, lp, alpha=int(255 * (1 - 0.4 * dark)))
    if t > s2 + 0.3: Z.movil(d, g, XL + 34, GY - 272, alpha=255 * seg(t, s2 + 0.3, s2 + 0.8))
    nL = 3 * seg(t, s1 + 0.4, s1 + 2.2) + 3 * seg(t, t10, t10 + 1.6) + 2 * seg(t, tq, tq + 1.4) + 3 * seg(t, t30, t30 + 2.2)
    manchas(do, XL, lp, nL, 1.0 + 0.3 * seg(t, t10, t30 + 2), seed=3)
    # ---------- DERECHA: con wudu ----------
    fuente(d, g, FX, t, agua=seg(t, s3 - 0.4, s3 + 0.4) * (1 - seg(t, t30 + 2.2, t30 + 3.0)))
    lav_b = t30 + 2.2
    rp, cara = wudu_pose(t, s3 + 0.2)
    if t > lav_b: rp = Z.lerp_pose(rp, P["joy"], seg(t, lav_b, lav_b + 0.8))
    figure(d, XR, rp)
    # manchas: aparecen igual que al otro; el wudu se las lleva (y cada día vuelven pequeñas y se van otra vez)
    nR = 3 * seg(t, s1 + 0.4, s1 + 2.2) * (1 - seg(t, s3 + 0.6, s3 + 2.8)) \
        + 2 * seg(t, t10, t10 + 1.0) * (1 - seg(t, t10 + 1.4, t10 + 2.8)) \
        + 3 * seg(t, t30, t30 + 0.8) * (1 - seg(t, t30 + 1.0, t30 + 2.2))
    manchas(do, XR, rp, nR, 1.0, seed=3)
    for a_, b_ in ((s3 + 0.4, s3 + 3.0), (t10 + 1.2, t10 + 3.0), (t30 + 0.8, t30 + 2.4)):
        gotas_manchadas(d, g, t, a_, b_, XR + 40, GY - 290 + 80 * (1 - cara), n=6, seed=int(a_ * 10))
    if t > t30 + 1.2: g.ellipse([XR - 110, GY - 360, XR + 110, GY + 20], fill=(80, 230, 225, int(70 * seg(t, t30 + 1.2, t30 + 2.8))))
    Z.anillos(d, XR, GY - 160, t, t30 + 1.6, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SIN WUDU", "CON WUDU", t10, t30, 46, lx=XL, rx=XR - 20)
    Z.subs(d, t, [(0.6, s1 - 0.15, "LOS DOS, EL MISMO DÍA"), (s1, s2 - 0.15, "LO QUE MIRAN. LO QUE TOCAN."), (s2, s3 - 0.15, "UNO SIGUE SIN MÁS"),
                  (s3, t10 - 0.1, "EL OTRO HACE EL WUDU")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN LLEGA LIMPIO?")
    Z.fuente(d, t, thad, tfin, ["«CON EL AGUA SALEN", "LOS PECADOS… HASTA", "QUE TERMINA LIMPIO»"], "SAHIH MUSLIM 244")
    Z.final(d, t, tfin, "EL AGUA SE LLEVA", "MÁS DE LO QUE VES.", task, "¿CUÁNTAS VECES AL DÍA", "HACES EL WUDU?")
    return Z.finish(base, fg, glow, bright, over=over)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
