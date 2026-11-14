# Estilo Noche · TÚ vs YUNUS · "las tres oscuridades" (Corán 21:87-88)
# Variante "lo que ves vs lo que Allah ve": arriba, TÚ en tu peor noche bajo una nube; debajo del suelo, el mar,
# y dentro de una ballena el profeta Yunus. Contador: OSCURIDAD 1 (noche) → 2 (mar) → 3 (ballena).
# Su dua sube como una luz por todas las capas hasta la estrella; el cielo se ilumina, la ballena lo deja en tierra
# y tu nube se deshace. Piezas nuevas: ballena, mar, orbe de dua con estela, nube con lluvia.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-15-1200-yunus-ballena.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Crees que estás en lo más oscuro?",
         "Mira debajo. El profeta Yunus.",
         "Primera oscuridad: la noche.",
         "Segunda: el fondo del mar.",
         "Tercera: dentro de una ballena.",
         "¿Quién le iba a oír ahí?",
         "Y desde dentro, dijo:",
         "No hay más dios que Tú. Glorificado seas.",
         "Yo he sido de los injustos.",
         "Y Allah le respondió, y le salvó de la angustia.",
         "Así salva Allah a los creyentes.",
         "Tú llama. Él te oye.",
         "¿Qué oscuridad estás pasando tú?"]
PAUSAS = [0.4, 0.5, 0.35, 0.35, 0.6, 2.0, 0.2, 0.3, 0.6, 0.5, 0.7, 0.8, 1.6]
def SFX(s): return [dict(t=s[7], f=1320, dur=0.8, v=0.05), dict(t=s[9], f=660, dur=2.0, v=0.08), dict(t=s[9] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-15-1200-yunus-ballena.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, s3, s4, tq, sd0, sd1, sd2, sres, thad, tfin, task = starts
print("DUR", DUR, starts)

TX, YX = 230, 760                       # TÚ (arriba) y YUNUS (abajo, en el mar)
WX, WY = 700, 1460                      # ballena
rnd = random.Random(21)
BUB = [(rnd.uniform(470, 1050), rnd.uniform(0, 1), rnd.uniform(3, 7)) for _ in range(18)]

def spline(pts, n=10):
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        for k in range(n):
            u = k / n; u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    out.append(pts[-1]); return out

def ballena(d, cx, cy, k, boca, alpha, t):
    """Ballena de líneas (mira a la izquierda). boca 0..1 abre la mandíbula."""
    if alpha <= 0: return
    c = CREAM + (int(alpha),); sw = 5 * S
    wob = 6 * math.sin(t * 1.6)
    top = [(-215, -5), (-170, -70), (-60, -105), (80, -92), (190, -48), (250, -16 + wob * 0.3)]
    tail = [(250, -16 + wob * 0.3), (300, -78 + wob), (292, -14), (318, 40 + wob), (250, 14)]
    bot = [(250, 14), (170, 52), (40, 82), (-110, 70), (-185, 38), (-215, 18 + 36 * boca)]
    q = lambda pts: [((cx + x * k) * S, (cy + y * k) * S) for x, y in pts]
    body = spline(top) + spline(bot)
    d.polygon(q(body), fill=(14, 30, 40, int(alpha * 0.92)))
    d.line(q(spline(top)), fill=c, width=sw, joint="curve"); d.line(q(spline(bot)), fill=c, width=sw, joint="curve")
    d.line(q(tail), fill=c, width=sw, joint="curve")
    d.line(q([(-215, -5), (-150, 8 + 10 * boca)]), fill=c, width=int(3 * S))          # línea de la boca
    ex, ey = cx - 150 * k, cy - 40 * k
    d.ellipse([(ex - 7) * S, (ey - 7) * S, (ex + 7) * S, (ey + 7) * S], fill=c)
    for i in range(3):                                                              # surcos de la tripa
        x0 = -120 + i * 30
        d.line(q([(x0, 52 - i * 2), (x0 + 60, 66 - i * 3)]), fill=CREAM + (int(alpha * 0.5),), width=int(2 * S))

def mar(d, t, k, x0=0):
    """Olas debajo del suelo (k 0..1 las va dibujando)."""
    if k <= 0: return
    for i in range(8):
        y = GY + 45 + i * 58; a = int(110 * k * (1 - i * 0.07))
        pts = [((x0 + x) * S, (y + 7 * math.sin(x / 70 + t * 1.3 + i)) * S) for x in range(0, int((W - x0) * min(1, k * 1.4 - i * 0.05)) + 1, 12)]
        if len(pts) > 1: d.line(pts, fill=(90, 210, 210, a), width=2 * S)

def nube(d, cx, cy, alpha, t, lluvia=1.0, col=(78, 82, 98)):
    """Nube oscura con lluvia (dibujar en una capa sin halo)."""
    if alpha <= 0: return
    for bx, by, r in [(-70, 10, 48), (-20, -22, 62), (45, -8, 54), (85, 16, 40), (0, 20, 50)]:
        d.ellipse([(cx + bx - r) * S, (cy + by - r) * S, (cx + bx + r) * S, (cy + by + r) * S], fill=col + (int(alpha),))
    for i in range(10):
        ph = (t * 1.4 + i * 0.37) % 1; x = cx - 90 + i * 20; y = cy + 50 + ph * 190
        d.line([(x * S, y * S), ((x - 5) * S, (y + 22) * S)], fill=(150, 160, 180, int(alpha * lluvia * (1 - ph))), width=2 * S)

def orbe(d, g, t, t0, dur, x0, y0, x1, y1):
    """Luz de la dua que sube de (x0, y0) a (x1, y1) dejando una estela."""
    if t < t0: return None
    k = seg(t, t0, t0 + dur)
    def pos(u): return lerp(x0, x1, u) + 60 * math.sin(u * 7), lerp(y0, y1, u)
    if k < 1:
        for j in range(24):
            u = max(0.0, k - j * 0.012)
            px, py = pos(u); r = 12 * (1 - j / 24) + 2
            d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=(170, 250, 245, int(240 * (1 - j / 24))))
        px, py = pos(k); g.ellipse([px - 60, py - 60, px + 60, py + 60], fill=(120, 245, 238, 200))
    return k

def frame(t):
    bright = 0.16 - 0.1 * seg(t, s2, s2 + 1.0) + 0.9 * seg(t, sd2 + 1.6, sres + 1.5)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, od = Z.new_layer()
    # ---------- debajo del suelo: el mar ----------
    mar(d, t, seg(t, s1, s1 + 1.2) + 0.0 * seg(t, s3, s3 + 1.0))
    if t > s3:                                    # en el fondo del mar el agua se oscurece y suben burbujas
        for x, ph0, r in BUB:
            ph = (t * 0.25 + ph0) % 1; y = 1600 - ph * 380
            d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], outline=(120, 220, 220, int(130 * seg(t, s3, s3 + 1) * (1 - ph))), width=2 * S)
    # ---------- la ballena ----------
    wa = 255 * seg(t, s4 - 0.2, s4 + 0.8) * (1 - seg(t, thad + 0.5, thad + 2.0))
    wx = lerp(1300, WX, seg(t, s4 - 0.2, s4 + 1.4))
    wy = WY - 120 * seg(t, sres, sres + 1.5) + 140 * seg(t, thad + 0.5, thad + 2.0)
    boca = 1 - seg(t, s4 + 1.2, s4 + 1.7) + seg(t, sres, sres + 0.8)
    ballena(d, wx, wy, 1.15, boca, wa, t)
    # ---------- Yunus: se hunde, queda dentro, sale a tierra ----------
    if t < sres + 0.5:
        sink = seg(t, 0, s4 + 1.2)
        yx = lerp(YX, WX - 20, sink); yy = lerp(1300, WY + 40, sink)
        rot = 0.6 * math.sin(t * 0.8) * (1 - seg(t, s4 + 1.2, s4 + 1.6))
        Z.mini_figure(d, yx, P["sad"], 0.66, rot=rot, y0=yy)
        if t > sd0:                                # mientras reza, una luz suave le rodea
            g.ellipse([yx - 80, yy - 130, yx + 80, yy + 20], fill=(120, 240, 235, int(140 * seg(t, sd0, sd0 + 0.8))))
    else:
        ko = seg(t, sres + 0.5, sres + 2.2); ex = lerp(WX - 20, 900, ko); ey = lerp(WY - 80, GY, ko) - 160 * math.sin(math.pi * ko)
        pose = pose_mix("sad", "stand", seg(t, sres + 2.2, sres + 2.9))
        if t > thad + 1.0: pose = pose_mix("stand", "joy", seg(t, thad + 1.0, thad + 1.6) * (1 - seg(t, tfin + 2.5, tfin + 3.2)))
        if ko < 1: Z.mini_figure(d, ex, P["sad"], 0.66, rot=-2.5 * (1 - ko), y0=ey)
        else: Z.mini_figure(d, 900, pose, 0.8)
    # ---------- la dua sube hasta la estrella ----------
    k = orbe(d, g, t, sd1, sd2 + 1.6 - sd1, WX - 20, WY - 40, W / 2, 200)
    if k is not None:
        Z.anillos(d, W / 2, 190, t, sd2 + 1.5, 2.0, rmax=220)
        cross = sd1 + (sd2 + 1.6 - sd1) * 0.2
        Z.anillos(d, lerp(WX - 20, W / 2, 0.2), GY, t, cross, 1.2, rmax=120)
    # ---------- TÚ: arriba, bajo la nube ----------
    nube(od, TX + 10, GY - 470, 235 * (1 - seg(t, sres + 0.3, sres + 2.0)), t)
    tp = P["sad"] if t < sres + 0.6 else pose_mix("sad", "stand", seg(t, sres + 0.6, sres + 1.6))
    if t > thad + 1.0: tp = pose_mix("stand", "joy", seg(t, thad + 1.0, thad + 1.6) * (1 - seg(t, tfin + 2.5, tfin + 3.2)))
    figure(d, TX, tp)
    # ---------- TEXTOS ----------
    fa = sres + 1.7                               # la fuente entra antes para que se lea bien
    la = 255 * (1 - seg(t, fa - 0.4, fa))
    if la > 0:
        spaced(d, "TÚ", TX, 330, 50, la); spaced(d, "YUNUS", YX, 330, 50, la)
        n = 1 if t < s3 else (2 if t < s4 else 3)
        pulse = 1 + 0.3 * max(0, 1 - abs(t - s2) * 2.5) + 0.3 * max(0, 1 - abs(t - s3) * 2.5) + 0.3 * max(0, 1 - abs(t - s4) * 2.5)
        spaced(d, "AHORA", TX, 400, 36, la * 0.8, col=(200, 225, 222))
        spaced(d, f"OSCURIDAD {n}", YX, 400, int(36 * pulse), la * 0.85, col=(200, 225, 222))
    Z.subs(d, t, [(0.3, s1 - 0.1, "LO MÁS OSCURO"), (s1, s2 - 0.1, "MIRA DEBAJO"), (s2, s3 - 0.1, "1 · LA NOCHE"), (s3, s4 - 0.1, "2 · EL FONDO DEL MAR"),
                  (s4, tq - 0.1, "3 · UNA BALLENA"), (sd1, sd2 - 0.05, "«NO HAY MÁS DIOS QUE TÚ»"), (sd2, sres - 0.1, "«HE SIDO DE LOS INJUSTOS»"),
                  (sres, fa - 0.1, "ALLAH LE RESPONDIÓ")])
    Z.pregunta(d, t, tq, sd0, "¿QUIÉN LE OYE AHÍ?")
    if fa <= t < tfin:
        al = 255 * seg(t, fa, fa + 0.5) * (1 - seg(t, tfin - 0.4, tfin))
        for i, ln in enumerate(["«ASÍ SALVAMOS", "A LOS CREYENTES»"]):
            spaced(d, ln, W / 2, 330 + 70 * i, Z.fit("A LOS CREYENTES»", 50, 760), al * seg(t, fa + 0.5 * i, fa + 0.5 * i + 0.5))
        spaced(d, "CORÁN 21:87-88", W / 2, 490, 32, al * 0.85 * seg(t, fa + 1.2, fa + 1.7), bold=False, col=(190, 225, 222))
    Z.final(d, t, tfin, "TÚ LLAMA.", "ÉL TE OYE.", task, "¿QUÉ OSCURIDAD", "ESTÁS PASANDO TÚ?")
    return Z.finish(base, fg, glow, bright, over=over)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
