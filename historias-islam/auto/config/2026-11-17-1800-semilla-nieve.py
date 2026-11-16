# Estilo Noche · SE RINDE vs AGUANTA · "dos semillas bajo la nieve" (Corán 94:5-6)
# Explorar: emoción esperanza (como TÚ vs YUNUS) con metáfora nueva: semilla bajo la nieve.
# Los dos plantan en pleno invierno y arriba nada cambia. Día 10: uno se cansa y arranca su semilla... y ya tenía raíces.
# El otro aguanta con frío; debajo del suelo sus raíces crecen sin que lo vea. Día 30: se derrite la nieve y brota un árbol.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-17-1800-semilla-nieve.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced, canopy

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Dos semillas bajo la nieve. Solo una verá la primavera.",
         "Los dos esperan. Y arriba, nada cambia.",
         "Día diez. Uno se cansa, y la arranca.",
         "Sin saber que ya tenía raíces.",
         "El otro sigue esperando. Con frío. Sin ver nada.",
         "¿Para qué seguir?",
         "Día treinta.",
         "Allah dice en el Corán: con la dificultad viene la facilidad. Con la dificultad, viene la facilidad.",
         "Aguanta. Ya está creciendo.",
         "¿Qué estás esperando tú? Escríbelo abajo."]
PAUSAS = [0.5, 0.6, 0.5, 0.7, 0.6, 1.8, 0.5, 0.6, 0.8, 1.3]
def SFX(s): return [dict(t=s[3], f=520, dur=1.2, v=0.05), dict(t=s[6], f=660, dur=2.0, v=0.08), dict(t=s[6] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-17-1800-semilla-nieve.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.04)
s0, s1, t10, s3, s4, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, SL = 230, 410            # figura y semilla de la izquierda
XR, SR = 880, 650            # figura y semilla de la derecha
SY = GY + 40                 # profundidad de las semillas
def mirror(p): return {j: (-v[0], v[1]) for j, v in p.items()}
def lerp_pose(a, b, k): return {j: (lerp(a[j][0], b[j][0], k), lerp(a[j][1], b[j][1], k)) for j in a}
def shiver(p, t, a):
    return {j: (v[0] + a * 2.5 * math.sin(t * 40 + i), v[1]) for i, (j, v) in enumerate(p.items())}

def frame(t):
    spring = seg(t, t30 + 0.2, t30 + 2.4)
    bright = 0.1 + 0.1 * seg(t, t10, t10 + 1.0) + 0.8 * spring
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer(); over, do = Z.new_layer()
    # ---------- invierno ----------
    snow_h = (12 + 26 * seg(t, 0, t10) + 18 * seg(t, t10, tq + 1)) * (1 - seg(t, t30 + 0.3, t30 + 2.0))
    Z.copos(do, t, 255 * (1 - seg(t, t30, t30 + 1.2)))
    # ---------- IZQUIERDA: SE RINDE ----------
    pull = seg(t, t10 + 1.9, t10 + 2.6)                       # la saca de la tierra
    drop = seg(t, s3 + 1.6, s3 + 2.2)                         # la deja caer
    sy_l = lerp(SY, GY - 160, pull) if drop == 0 else lerp(GY - 160, GY - snow_h - 16, drop)
    sx_l = lerp(SL, SL + 40, drop)
    gris = seg(t, s3 + 0.6, s3 + 2.2)
    rcol = tuple(int(lerp(a, b, gris)) for a, b in zip(CREAM, (110, 104, 100)))
    rg_l = 0.24 * seg(t, s1, t10 + 1.0) + 0.1 * pull
    Z.raices_en(d, rg_l, sx_l, sy_l + 6, k=0.62 * (1 - 0.35 * drop), col=rcol, alpha=255 * (1 - 0.65 * drop))
    Z.semilla(d, g, sx_l, sy_l, col=tuple(int(lerp(a, b, gris)) for a, b in zip(GOLD, (110, 104, 100))), brillo=1 - gris)
    if s3 < t < s3 + 2.0: Z.anillos(d, SL, GY - 130, t, s3, 2.0, col=(250, 225, 160), rmax=140)
    walk = seg(t, t10 + 0.6, t10 + 1.4)
    xl = lerp(XL, 330, walk)
    if t < t10 + 0.6: lp = shiver(Z.FRIO, t, 1 - seg(t, t10, t10 + 0.6)) if t > s1 else Z.FRIO
    elif t < t10 + 1.4: lp = Z.walk_pose(t * 7)
    elif t < t10 + 2.7: lp = lerp_pose(P["stand"], P["hug"], seg(t, t10 + 1.4, t10 + 1.9) * (1 - 0.5 * pull))
    elif t < s3 + 1.6: lp = lerp_pose(P["hug"], P["stand"], 0.5 + 0.5 * seg(t, t10 + 2.6, t10 + 3.0))
    else: lp = lerp_pose(P["stand"], P["sad"], seg(t, s3 + 1.8, s3 + 2.8))
    if t10 + 1.9 < t < s3 + 1.6 and t > t10 + 2.6:            # sostiene la semilla en alto
        lp = dict(lp); lp["rh"] = (SL - 330, -172); lp["re"] = (44, -205)
    figure(d, xl, lp, alpha=int(255 * (1 - 0.3 * spring)))
    # ---------- DERECHA: AGUANTA ----------
    rg_r = 0.24 * seg(t, s1, t10 + 1.0) + 0.26 * seg(t, s4, tq + 1.0) + 0.5 * seg(t, t30 + 0.2, t30 + 3.0)
    Z.raices_en(d, rg_r, SR, SY + 6, k=0.8)
    Z.semilla(d, g, SR, SY, brillo=1 + 0.5 * seg(t, s4, tq))
    if t > t30 + 0.4:                                         # brota: planta y luego árbol
        sp = seg(t, t30 + 0.4, t30 + 1.6); tr = seg(t, t30 + 1.5, t30 + 3.3)
        if tr < 0.15: Z.planta(d, g, SR, 170 * sp, vida=sp, t=t, luz=spring)
        if tr > 0:
            d.line([(SR * S, GY * S), (SR * S, (GY - 300 * tr) * S)], fill=CREAM + (255,), width=int(12 * S))
            canopy(d, SR, GY - 330, 0.85 * seg(t, t30 + 2.0, t30 + 3.3))
        for i, fx in enumerate((520, 580, 730, 790)):
            Z.flor(d, fx, 40 * seg(t, t30 + 2.4 + 0.2 * i, t30 + 3.2 + 0.2 * i))
        if t > t30 + 2.2: g.ellipse([SR - 200, GY - 520, SR + 200, GY - 140], fill=(120, 240, 225, int(70 * seg(t, t30 + 2.2, t30 + 3.4))))
    if t < t30 + 1.0: rp = shiver(Z.FRIO, t, 0.7 * seg(t, s4, s4 + 0.4))
    elif t < t30 + 2.0: rp = lerp_pose(Z.FRIO, P["stand"], seg(t, t30 + 1.0, t30 + 1.6))
    else: rp = pose_mix("stand", "joy", seg(t, t30 + 2.0, t30 + 2.6) * (1 - seg(t, thad + 3.5, thad + 4.3)))
    figure(d, XR, mirror(rp))
    # nieve encima de todo lo que está en el suelo
    Z.manto_nieve(d, 0, W, snow_h)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SE RINDE", "AGUANTA", t10, t30, 46, lx=320, rx=745)
    Z.subs(d, t, [(0.4, 1.9, "DOS SEMILLAS BAJO LA NIEVE"), (1.9, s1 - 0.15, "SOLO UNA VERÁ LA PRIMAVERA"), (s1, t10 - 0.1, "ARRIBA, NADA CAMBIA"),
                  (t10, s3 - 0.1, "UNO SE CANSA... Y LA ARRANCA"), (s3, s4 - 0.1, "YA TENÍA RAÍCES"), (s4, tq - 0.1, "EL OTRO SIGUE ESPERANDO")])
    Z.pregunta(d, t, tq, t30, "¿PARA QUÉ SEGUIR?")
    Z.fuente(d, t, thad, tfin, ["«CON LA DIFICULTAD", "VIENE LA FACILIDAD»"], "CORÁN 94:5-6")
    if thad + 0.5 * (ends[7] - thad) < t < tfin:
        a0 = thad + 0.5 * (ends[7] - thad)
        al = 255 * seg(t, a0, a0 + 0.4) * (1 - seg(t, tfin - 0.4, tfin))
        spaced(d, "LO DICE DOS VECES", W / 2, 555, int(36 * (1 + 0.15 * max(0, 1 - (t - a0) * 2))), al, col=(150, 240, 232))
    Z.final(d, t, tfin, "AGUANTA.", "YA ESTÁ CRECIENDO.", task, "¿QUÉ ESTÁS ESPERANDO TÚ?", "ESCRÍBELO ABAJO")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
