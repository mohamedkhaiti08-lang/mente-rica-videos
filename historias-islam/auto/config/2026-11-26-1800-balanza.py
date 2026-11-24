# Estilo Noche · BORDE vs AMABLE · "¿Qué es lo que más pesa en la balanza?" (Sunan Abi Dawud 4799)
# Explorar: metáfora nueva de LA BALANZA + acto concreto del día a día (cómo tratas al camarero que te atiende).
# Una balanza gigante entre los dos. Rezan lo mismo: caen los mismos bloques de luz en cada plato y la balanza queda igual.
# Uno le habla mal al camarero («¡ESPABILA!»): su bocadillo se vuelve humo y sus bloques se agrietan. El otro le sonríe
# y le da las gracias: su «GRACIAS» se vuelve una piedra de luz que vuela a su plato. Día 10 y 30 se acumulan; la balanza
# tiembla pero aguanta hasta la pregunta. Giro: se inclina de golpe hacia el amable y el cielo se ilumina.
# Objetos nuevos: balanza con mástil y estrella, bandeja de camarero, piedra de luz; poses CAMARERO, SENALA, GRACIAS.
# Uso: python3 2026-11-26-1800-balanza.py salida.mp4 [t1 t2 ...]
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Qué es lo que más pesa en la balanza? No es lo que crees.",
         "Dos personas. Rezan lo mismo. La balanza, igual.",
         "Uno le habla mal al camarero.",
         "El otro le sonríe y le da las gracias.",
         "Día diez.",
         "Día treinta.",
         "¿Hacia dónde se inclina?",
         "El Profeta, la paz sea con él, dijo: no hay nada que pese más en la balanza que el buen carácter.",
         "Reza. Y trata bien a la gente.",
         "¿Cómo tratas tú al que te atiende?"]
PAUSAS = [0.5, 0.6, 0.6, 0.7, 1.0, 0.4, 1.9, 0.6, 0.6, 1.4]
def SFX(s): return [dict(t=s[3] + 1.6, f=1320, dur=0.8, v=0.06), dict(t=s[4] + 0.6, f=1320, dur=0.8, v=0.05),
                    dict(t=s[7] - 0.3, f=660, dur=2.0, v=0.08), dict(t=s[7] - 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-26-1800-balanza.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, s3, t10, t30, tq, thad, tfin, task = starts
tgiro = thad - 0.4
print("DUR", DUR, starts)

XA, XB = 190, 860          # personajes
WA, WB = 400, 680          # camareros
CX, TOP = 540, 640         # balanza
LXC, RXC = 230, 780        # etiquetas
BLOQ = [(-50, -18), (0, -18), (50, -18), (-25, -54), (25, -54)]
PIED = [(0, -96), (-44, -92), (44, -92), (-22, -130), (22, -130)]
TEAL = (130, 240, 232)

def frame(t):
    bright = 0.1 + 0.08 * seg(t, t10, t10 + 1.0) + 0.08 * seg(t, t30, t30 + 1.0) + 0.74 * seg(t, tgiro, tgiro + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    # ---------- lo que no se ve ----------
    Z.grietas(d, XA, 0.3 * seg(t, s2 + 1.0, s3) + 0.3 * seg(t, t10, t10 + 1.2) + 0.4 * seg(t, t30, t30 + 1.5), seed=6)
    Z.roots(d, 0.3 * seg(t, s3 + 1.6, s3 + 3.0) + 0.3 * seg(t, t10, t10 + 1.4) + 0.4 * seg(t, t30, tgiro + 2.0), x0=XB)
    # ---------- la balanza ----------
    ang = 0.03 * math.sin(t * 1.9) * seg(t, s3, s3 + 1.0) * (1 - seg(t, tgiro - 0.2, tgiro)) + 0.15 * seg(t, tgiro, tgiro + 1.4)
    (lx, ly), (rx, ry) = Z.balanza(d, g, CX, TOP, ang, t, half=270, cadena=110, brillo=seg(t, tgiro, tgiro + 1.4))
    # bloques de oración (iguales en los dos platos)
    for i, (bx, by) in enumerate(BLOQ):
        a0 = s1 + 0.9 + 0.25 * i
        k = seg(t, a0, a0 + 0.5)
        if k <= 0: continue
        for side, (px, py) in enumerate(((lx, ly), (rx, ry))):
            fy = lerp(py - 170, py + by, k)
            if side == 0:
                crack = 0.5 * seg(t, s2 + 1.4, s2 + 2.4) + 0.5 * seg(t, t10, t10 + 1.2)
                gris = seg(t, t30, t30 + 1.5)
                col = tuple(int(lerp(c, q, gris)) for c, q in zip(CREAM, (120, 116, 126)))
                Z.bloque(d, g, px + bx, fy, 1.0, col, 255, glow_col=None if gris > 0.5 else (120, 240, 235), crack=crack)
            else:
                Z.bloque(d, g, px + bx, fy, 1.0, CREAM, 255, glow_col=(120, 240, 235))
    # piedras de luz (cada «gracias») que vuelan al plato del amable
    for i, a0 in enumerate((s3 + 1.4, t10 + 0.2, t10 + 0.6, t30 + 0.2, t30 + 0.6)):
        k = seg(t, a0, a0 + 0.9)
        if k <= 0: continue
        ox, oy = (WB + 30, GY - 300)
        tx, ty = rx + PIED[i][0], ry + PIED[i][1]
        px = lerp(ox, tx, k); py = lerp(oy, ty, k) - 120 * math.sin(math.pi * k)
        Z.piedra_luz(d, g, px, py, r=17, rot=i)
    # ---------- IZQUIERDA: BORDE ----------
    habla = seg(t, s2, s2 + 0.4) * (1 - seg(t, s2 + 2.0, s2 + 2.5)) + seg(t, t10 + 0.1, t10 + 0.4) * (1 - seg(t, t10 + 1.0, t10 + 1.3)) \
            + seg(t, t30 + 0.1, t30 + 0.4) * (1 - seg(t, t30 + 1.0, t30 + 1.3))
    pa = Z.lerp_pose(P["stand"], Z.SENALA, min(1, habla))
    pa = Z.lerp_pose(pa, Z.espejo(P["sad"]), seg(t, tgiro + 0.6, tgiro + 1.8))
    figure(d, XA, pa, alpha=int(255 - 70 * seg(t, tgiro, tgiro + 1.5)))
    if s2 + 0.2 < t < s3:
        al = 255 * seg(t, s2 + 0.2, s2 + 0.5) * (1 - seg(t, s2 + 1.8, s2 + 2.3))
        Z.bocadillo(d, 300, GY - 368, "¡ESPABILA!", alpha=al, size=24, cola=1, col=(235, 140, 130), borde=(200, 110, 100))
        if t > s2 + 1.6: Z.humo(du, 300, GY - 368, seg(t, s2 + 1.6, s2 + 2.6), t)
    for a0 in (t10 + 0.1, t30 + 0.1):
        if a0 < t < a0 + 1.4:
            al = 255 * seg(t, a0, a0 + 0.2) * (1 - seg(t, a0 + 0.9, a0 + 1.3))
            Z.bocadillo(d, 300, GY - 368, "¡VENGA YA!" if a0 < t30 else "¡QUÉ LENTO!", alpha=al, size=24, cola=1, col=(235, 140, 130), borde=(200, 110, 100))
    triste = seg(t, s2 + 0.8, s2 + 1.6)
    cw = Z.lerp_pose(Z.espejo(Z.CAMARERO), Z.espejo(P["sad"]), 0.35 * triste)
    Z.mini_figure(d, WA, cw, k=0.78)
    Z.bandeja(d, WA - 52, GY - 196 * 0.78 + 10 * triste)
    # ---------- DERECHA: AMABLE ----------
    gracias = seg(t, s3, s3 + 0.4) * (1 - seg(t, s3 + 2.4, s3 + 2.8))
    pb = Z.lerp_pose(P["stand"], Z.espejo(Z.GRACIAS), gracias)
    pb = Z.lerp_pose(pb, P["joy"], seg(t, tgiro + 0.4, tgiro + 1.2) * (1 - seg(t, tfin - 0.3, tfin + 0.3)))
    figure(d, XB, pb)
    if s3 + 0.2 < t < s3 + 1.6:
        al = 255 * seg(t, s3 + 0.2, s3 + 0.5) * (1 - seg(t, s3 + 1.2, s3 + 1.6))
        Z.bocadillo(d, 760, GY - 368, "¡GRACIAS!", alpha=al, size=24, cola=-1, col=(170, 245, 238), borde=TEAL)
    for a0 in (t10 + 0.0, t30 + 0.0):
        if a0 < t < a0 + 0.9:
            al = 255 * seg(t, a0, a0 + 0.2) * (1 - seg(t, a0 + 0.6, a0 + 0.9))
            Z.bocadillo(d, 760, GY - 368, "¡GRACIAS!" if a0 < t30 else "¡BUEN DÍA!", alpha=al, size=24, cola=-1, col=(170, 245, 238), borde=TEAL)
    feliz = seg(t, s3 + 0.8, s3 + 1.6)
    Z.mini_figure(d, WB, Z.lerp_pose(Z.CAMARERO, P["joy"], 0.3 * feliz), k=0.78)
    Z.bandeja(d, WB + 52, GY - 196 * 0.78 - 8 * feliz)
    if t > tgiro: g.ellipse([XB - 200, GY - 420, XB + 140, GY + 30], fill=(80, 230, 225, int(80 * seg(t, tgiro, tgiro + 2.0))))
    Z.anillos(d, rx, ry - 40, t, tgiro, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "BORDE", "AMABLE", t10, t30, 44, lx=LXC, rx=RXC)
    Z.subs(d, t, [(0.4, s1 - 0.15, "¿QUÉ PESA MÁS EN LA BALANZA?"), (s1, s2 - 0.15, "REZAN LO MISMO"),
                  (s2, s3 - 0.15, "UNO HABLA MAL AL CAMARERO"), (s3, t10 - 0.1, "EL OTRO LE DA LAS GRACIAS")], y=520)
    Z.pregunta(d, t, tq, thad, "¿HACIA DÓNDE SE INCLINA?")
    Z.fuente(d, t, thad, tfin, ["«NADA PESA MÁS", "EN LA BALANZA QUE", "EL BUEN CARÁCTER»"], "SUNAN ABI DAWUD 4799")
    if t >= tfin:                                   # final más arriba para no tocar la balanza
        al = 255 * seg(t, tfin, tfin + 0.4)
        spaced(d, "REZA.", W / 2, 330, 62, al)
        spaced(d, "Y TRATA BIEN A LA GENTE.", W / 2, 400, Z.fit("Y TRATA BIEN A LA GENTE.", 46, 760), al * seg(t, tfin + 0.5, tfin + 0.9))
    if t >= task:
        al = 255 * seg(t, task, task + 0.4); sz = Z.fit("AL QUE TE ATIENDE?", 40, 760, 0.22)
        spaced(d, "¿CÓMO TRATAS TÚ", W / 2, 470, sz, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, "AL QUE TE ATIENDE?", W / 2, 522, sz, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, "COMENTA ↓", W / 2, 572, 32, al * (0.6 + 0.4 * math.sin(t * 5)), track=0.25, col=(120, 230, 225))
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
