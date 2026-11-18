# Estilo Noche · HIERE vs CUIDA (palabra mala vs palabra buena) · "una sola palabra" (Sahih al-Bujari 6478)
# Explorar: «lo que ves vs lo que Allah ve» con una metáfora nueva: cada palabra sale como un bocadillo y se convierte
# en una piedra que cae y se hunde bajo el suelo (palabra mala) o en una luz que sube hasta la estrella (palabra buena).
# Día 30: al de la palabra buena le aparecen escalones de luz (los «grados») y sube; al otro se le abre un pozo de piedras bajo los pies.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-19-1800-palabra.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Una palabra que dices sin pensar… puede subirte, o hundirte.",
         "Uno suelta lo primero que piensa.",
         "El otro dice algo bueno.",
         "Día diez.",
         "¿Dónde va cada palabra?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: dices una palabra que agrada a Allah, sin darle importancia, y te eleva grados. Y otra que le enfada, y por ella caes en el Fuego.",
         "Cada palabra va a algún sitio.",
         "¿Qué palabra buena vas a decir hoy?"]
PAUSAS = [0.6, 1.3, 1.3, 1.1, 2.2, 0.7, 0.8, 0.9, 1.6]
def SFX(s): return [dict(t=s[2] + 1.6, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-19-1800-palabra.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, XR = 300, 730
BL, BR, BY = 320, 700, 770            # bocadillos
STAR = (540, 230)
# (aparece, se transforma, texto) para cada lado
WL = [(-0.3, s1 + 0.5, "¡QUÉ PESADO!"), (t10 + 0.1, t10 + 0.9, "¡NO VALES NADA!")]
WR = [(-0.3, s2 + 1.3, "GRACIAS"), (t10 + 0.1, t10 + 0.9, "¿TE AYUDO?")]
STEP_X, STEP_N, STEP_W, STEP_H = XR - 40, 3, 130, 44

def frame(t):
    bright = 0.15 + 0.15 * seg(t, t10, t10 + 1.2) + 0.7 * seg(t, t30 + 0.4, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    dark = 0.3 * seg(t, s1 + 1.5, t10) + 0.25 * seg(t, t10 + 1.3, t10 + 2.5) + 0.45 * seg(t, t30, t30 + 2)
    # ---------- IZQUIERDA: piedras que caen y se hunden ----------
    pozo = seg(t, t30 + 0.2, t30 + 1.6)
    Z.grietas(d, XL, 0.3 * seg(t, s1 + 1.6, s1 + 2.6) + 0.3 * seg(t, t10 + 2.2, t10 + 3.2) + 0.4 * pozo, seed=7)
    if pozo > 0:                                           # se abre un pozo oscuro bajo sus pies
        d.ellipse([(XL - 120 * pozo) * S, (GY - 12 * pozo) * S, (XL + 120 * pozo) * S, (GY + 26 * pozo) * S], fill=(8, 8, 12, 255), outline=(150, 50, 45, int(200 * pozo)), width=3 * S)
    nst = 0
    for i, (a, b, txt) in enumerate(WL):
        if t >= b:                                         # la palabra se vuelve piedra: cae, atraviesa el suelo y se hunde
            k = seg(t, b, b + 0.9); sink = seg(t, b + 0.9, b + 3.0)
            y = lerp(BY, GY - 20, k) + 260 * sink + 40 * i + 90 * pozo
            Z.piedra(d, BL - 20 * i + 6 * math.sin(t + i), y, 32 + 4 * i, col=(120, 112, 124), rot=t * 0.6 * (1 - sink) + i)
            nst += 1
    if t > t30:                                            # día 30: lluvia de piedras que se hunden (todas las palabras de un mes)
        for j in range(6):
            a = t30 + 0.3 + j * 0.35; k = seg(t, a, a + 0.8)
            if t > a:
                Z.piedra(d, XL - 110 + j * 44, lerp(620, GY + 120 + 40 * (j % 3), k), 20 + (j % 3) * 5, col=(120, 112, 124), rot=j + t * 0.3 * (1 - k))
    lp = Z.lerp_pose(P["stand"], P["sad"], 0.15 * seg(t, t10 + 2.2, t10 + 3.2) + 0.85 * seg(t, t30 + 0.4, t30 + 1.6))
    for a, b, _ in WL:
        if a <= t < b: lp = Z.lerp_pose(lp, Z.HABLA, seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b)))
    figure(d, XL, lp, alpha=int(255 * (1 - 0.35 * dark)))
    for a, b, txt in WL:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b, b + 0.25))
        sc = 1 - 0.4 * seg(t, b - 0.1, b + 0.25)
        Z.bocadillo(d, BL, BY, txt, al, size=int(Z.fit(txt, 30, 300, 0.22) * sc), col=(235, 150, 140), borde=(200, 90, 80), cola=-1)
    # ---------- DERECHA: luces que suben a la estrella y escalones ----------
    for i, (a, b, txt) in enumerate(WR):
        k = Z.orbe(d, g, t, b, 1.8 if i == 0 else 1.2, BR, BY, STAR[0], STAR[1] + 40)
        if k is not None and k >= 1 and t < b + 2.6 and t30 + 2 > t:
            g.ellipse([STAR[0] - 110, STAR[1] - 110, STAR[0] + 110, STAR[1] + 110], fill=(120, 245, 238, int(200 * (1 - seg(t, b + 1.8, b + 2.6)))))
    Z.roots(d, 0.3 * seg(t, s2 + 1.6, s2 + 3.0) + 0.25 * seg(t, t10 + 2.3, t10 + 3.5) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), x0=XR)
    stk = 0.34 * seg(t, t10 + 2.6, t10 + 3.4) + 0.66 * seg(t, t30 + 0.3, t30 + 1.5)
    top = Z.escalones(d, g, STEP_X, STEP_N, stk, ancho=STEP_W, alto=STEP_H, lado=-1)
    climb = seg(t, t30 + 1.5, t30 + 3.3)
    tx = STEP_X - (STEP_N - 1) * STEP_W * 0.55
    xr = lerp(XR, tx, climb); yr = STEP_N * STEP_H * climb
    if 0 < climb < 1: rp = Z.walk_pose(t * 7)
    else: rp = P["stand"]
    for a, b, _ in WR:
        if a <= t < b: rp = Z.lerp_pose(rp, Z.HABLA, seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b)))
    if t > t30 + 3.3: rp = Z.lerp_pose(P["stand"], P["joy"], seg(t, t30 + 3.3, t30 + 3.8) * (1 - seg(t, thad + 4.0, thad + 4.8)))
    Z.mini_figure(d, xr, Z.espejo(rp), k=1.0, y0=GY - yr)
    for a, b, txt in WR:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b, b + 0.25))
        sc = 1 - 0.4 * seg(t, b - 0.1, b + 0.25)
        Z.bocadillo(d, BR, BY, txt, al, size=int(Z.fit(txt, 30, 300, 0.22) * sc), col=(170, 245, 238), borde=(120, 230, 225), cola=1)
    if t > t30 + 2.5: g.ellipse([xr - 120, GY - yr - 380, xr + 120, GY - yr + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 2.5, t30 + 3.8))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "HIERE", "CUIDA", t10, t30, 50, lx=XL - 10, rx=XR - 10)
    Z.subs(d, t, [(s1, s2 - 0.15, "UNO LA SUELTA SIN PENSAR"), (s2, s2 + 1.35, "EL OTRO DICE ALGO BUENO")])
    Z.pregunta(d, t, tq, t30, "¿DÓNDE VA CADA PALABRA?")
    Z.fuente(d, t, thad, tfin, ["UNA PALABRA,", "SIN DARLE IMPORTANCIA,", "TE ELEVA GRADOS…", "O TE HUNDE EN EL FUEGO"], "SAHIH AL-BUJARI 6478")
    Z.final(d, t, tfin, "CADA PALABRA", "VA A ALGÚN SITIO.", task, "¿QUÉ PALABRA BUENA", "VAS A DECIR HOY?")
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
