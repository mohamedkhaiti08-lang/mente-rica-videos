# Estilo Noche · SE OLVIDA vs SE REFUGIA · "¿Sabes qué dice un musulmán antes de entrar al baño?" (Sahih al-Bujari 142)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (sombras que esperan tras la puerta), gancho de curiosidad para IG.
# Dos puertas iguales; por encima asoma humo oscuro. Uno abre sin decir nada: la sombra de dentro se le pega a la espalda
# y cada día lleva una más (humo que se acumula bajo el suelo). El otro dice «Oh Allah, me refugio en Ti»: cae una CORTINA
# DE LUZ sobre su puerta y la sombra se deshace en chispas al tocarla; le crecen raíces. Día 30: uno «ya no sale solo».
# Objetos nuevos: cortina de luz que cae, humo que asoma por encima de una puerta, sombras pegadas a la espalda, chispas que
# se deshacen, pose de dua (manos levantadas). Uso: python3 2026-11-25-1800-bano.py salida.mp4 [t1 t2 ...]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué dice un musulmán antes de entrar al baño?",
         "Uno abre la puerta sin decir nada.",
         "El otro dice: Oh Allah, me refugio en Ti.",
         "Día diez.",
         "Día treinta. Uno ya no sale solo.",
         "¿Y por qué al otro no se le acerca nada?",
         "Porque antes de entrar, pidió refugio.",
         "El Profeta, la paz sea con él, al entrar al baño decía: Oh Allah, me refugio en Ti de los demonios, machos y hembras.",
         "Una frase. Una cortina de luz.",
         "¿Tú la dices? Escribe: desde hoy."]
PAUSAS = [0.5, 0.9, 1.4, 1.3, 0.6, 1.9, 0.6, 0.7, 0.7, 1.4]
def SFX(s): return [dict(t=s[2] + 1.6, f=1320, dur=0.8, v=0.06), dict(t=s[3] + 0.9, f=1320, dur=0.8, v=0.05),
                    dict(t=s[6] - 0.3, f=660, dur=2.0, v=0.08), dict(t=s[6] - 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-25-1800-bano.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, t10, t30, tq, tgiro, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, DL = 250, 420        # figura y puerta de la izquierda
XR, DR = 640, 810        # figura y puerta de la derecha
DH = 260                 # alto de las puertas
TEAL = (130, 240, 232)
OSCURO = (52, 48, 66)

# ---------- poses nuevas ----------
DUA = dict(P["stand"]); DUA.update(le=(14, -214), lh=(40, -262), re=(40, -210), rh=(66, -256), head=(4, -300))   # manos levantadas hacia la puerta
ABRE = dict(P["stand"]); ABRE.update(re=(52, -214), rh=(96, -200))                                                 # mano en el pomo
CARGADO = dict(P["stand"]); CARGADO.update(head=(18, -270), neck=(10, -236), hip=(0, -124), le=(30, -180), lh=(40, -122),
                                           re=(36, -182), rh=(50, -124), lk=(-10, -60), rk=(18, -60))            # encorvado

# ---------- objetos nuevos ----------
def humo_puerta(d, x, k, t, seed=3, top=GY - DH):
    """Humo oscuro que asoma por encima de una puerta cerrada (algo espera detrás)."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(9):
        ph = (t * 0.35 + i / 9) % 1
        px = x + rnd.uniform(-36, 36) + 16 * math.sin(t * 1.6 + i); py = top + 6 - ph * 150
        r = 12 + 22 * ph
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=OSCURO + (int(200 * k * (1 - ph)),))

def cortina(d, g, x, k, t, w=112, h=DH, brillo=0.0, col=TEAL):
    """Cortina de luz que cae desde el dintel y tapa la puerta (k 0..1 cuánto ha bajado). Objeto nuevo."""
    if k <= 0: return
    top = GY - h - 6; largo = (h + 6) * k
    n = 9
    for i in range(n):
        u = i / (n - 1); bx = x - w / 2 + u * w
        pts = []
        for j in range(13):
            v = j / 12; yy = top + largo * v
            pts.append(((bx + 5 * math.sin(t * 2.2 + i * 0.9 + v * 5) * v) * S, yy * S))
        a = int((150 + 90 * brillo) * (0.6 + 0.4 * math.sin(t * 3 + i)))
        d.line(pts, fill=col + (a,), width=int(4 * S), joint="curve")
        ex, ey = pts[-1][0] / S, pts[-1][1] / S
        d.ellipse([(ex - 5) * S, (ey - 5) * S, (ex + 5) * S, (ey + 5) * S], fill=(225, 255, 250, a))
    d.line([((x - w / 2 - 10) * S, top * S), ((x + w / 2 + 10) * S, top * S)], fill=col + (240,), width=int(6 * S))
    g.rectangle([x - w / 2 - 20, top - 10, x + w / 2 + 20, top + largo], fill=(80, 230, 225, int((70 + 90 * brillo) * k)))

def chispas(d, x, y, t, t0, dur=1.4, n=16, col=(200, 255, 250), seed=7):
    """Chispas turquesa que salen de un punto (algo oscuro que se deshace en luz)."""
    if not (t0 <= t < t0 + dur): return
    rnd = random.Random(seed); u = (t - t0) / dur
    for i in range(n):
        ang = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(60, 170)
        px = x + math.cos(ang) * sp * u; py = y + math.sin(ang) * sp * u - 40 * u
        r = 6 * (1 - u) + 1
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=col + (int(255 * (1 - u)),))

K = 0.5
def frame(t):
    bright = 0.12 + 0.1 * seg(t, t10, t10 + 1.2) + 0.78 * seg(t, tgiro - 0.2, tgiro + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    # ---------- lo que no se ve (bajo el suelo) ----------
    hk = 0.35 * seg(t, s1 + 1.6, s1 + 3.2) + 0.3 * seg(t, t10 + 0.4, t10 + 2.0) + 0.35 * seg(t, t30 + 0.4, t30 + 2.2)
    Z.humo_dentro(du, XL + 60, hk, t)
    Z.grietas(d, XL + 60, seg(t, tq + 0.6, tq + 2.6), seed=9)
    rg = 0.3 * seg(t, s2 + 2.4, s2 + 4.0) + 0.3 * seg(t, t10 + 0.5, t10 + 2.1) + 0.4 * seg(t, tq + 0.6, tq + 3.0)
    Z.roots(d, rg, x0=XR + 60)
    # ---------- IZQUIERDA: abre sin decir nada ----------
    ab = seg(t, s1 + 0.3, s1 + 0.9) * (1 - seg(t, s1 + 2.4, s1 + 3.0))
    sale = seg(t, s1 + 0.7, s1 + 2.0)                                   # la sombra de dentro sale hacia él
    humo_puerta(du, DL, seg(t, s0 + 0.6, s0 + 1.6) * (1 - 0.6 * sale) + 0.4 * seg(t, t10, t10 + 1.0), t)
    if ab > 0.02 and sale < 1:
        Z.sombra(du, lerp(DL, XL - 40, sale), 0.55, 230 * ab, t, y0=GY)
    Z.puerta(d, DL, ab, h=DH, w=112, lado=1)
    # sombras pegadas a la espalda (1 → 2 → 3)
    pegadas = [(XL - 60, sale > 0.98, 0.55, 0.0), (XL + 70, t > t10 + 0.6, 0.5, seg(t, t10 + 0.6, t10 + 1.6)),
               (XL - 120, t > t30 + 0.4, 0.6, seg(t, t30 + 0.4, t30 + 1.6))]
    for i, (px, on, kk, aparece) in enumerate(pegadas):
        if not on: continue
        a = 230 if i == 0 else 230 * aparece
        if i == 0:
            px = XL - 40 - 20 * seg(t, s1 + 2.0, s1 + 2.6)
        Z.sombra(du, px, kk, a, t + i * 1.3)
    if t10 + 0.2 < t < t10 + 1.8: Z.hilo_sombra(d, DL, GY - 200, XL + 70, GY - 180, seg(t, t10 + 0.2, t10 + 1.0), t, alpha=200 * (1 - seg(t, t10 + 1.2, t10 + 1.8)))
    if t30 + 0.1 < t < t30 + 1.7: Z.hilo_sombra(d, DL, GY - 200, XL - 120, GY - 180, seg(t, t30 + 0.1, t30 + 0.9), t, alpha=200 * (1 - seg(t, t30 + 1.1, t30 + 1.7)))
    lp = Z.lerp_pose(P["stand"], ABRE, ab)
    lp = Z.lerp_pose(lp, CARGADO, 0.45 * seg(t, t10 + 0.8, t10 + 1.8))
    lp = Z.lerp_pose(lp, CARGADO, seg(t, t30 + 0.4, t30 + 1.6))
    lp = Z.lerp_pose(lp, Z.espejo(P["sad"]), seg(t, tq + 0.6, tq + 1.8))
    figure(d, XL, lp, alpha=int(255 - 70 * seg(t, tgiro, tgiro + 1.5)))
    # ---------- DERECHA: pide refugio ----------
    dua = seg(t, s2, s2 + 0.5) * (1 - seg(t, s2 + 3.0, s2 + 3.5)) + seg(t, t10 + 0.1, t10 + 0.5) * (1 - seg(t, t10 + 1.6, t10 + 2.0))
    cae = seg(t, s2 + 1.0, s2 + 2.1)
    abR = seg(t, s2 + 2.4, s2 + 2.9) * (1 - seg(t, s2 + 4.2, s2 + 4.8))
    humo_puerta(du, DR, seg(t, s0 + 0.8, s0 + 1.8) * (1 - seg(t, s2 + 1.4, s2 + 2.2)), t, seed=5)
    if abR > 0.02:
        Z.sombra(du, DR - 30 * abR, 0.55, 230 * abR * (1 - seg(t, s2 + 2.8, s2 + 3.4)), t + 2.0)
    Z.puerta(d, DR, abR, h=DH, w=112, lado=1)
    chispas(d, DR - 30, GY - 140, t, s2 + 2.8)
    chispas(d, DR, GY - 220, t, t10 + 1.0, seed=11)
    chispas(d, DR, GY - 180, t, t30 + 0.8, seed=13)
    cortina(d, g, DR, cae, t, brillo=seg(t, tgiro, tgiro + 1.5) + 0.3 * seg(t, t10, t10 + 1)) if cae > 0 else None
    if t10 < t < t30 + 2.0:                                       # humo que intenta acercarse y se deshace
        for t0_ in (t10 + 0.2, t30 + 0.1):
            k_ = seg(t, t0_, t0_ + 0.8)
            if 0 < k_ < 1: Z.hilo_sombra(d, DR + 60, GY - 300, DR + 10, GY - 200, k_, t, alpha=200)
    rp = Z.lerp_pose(P["stand"], DUA, dua)
    rp = Z.lerp_pose(rp, P["joy"], seg(t, tgiro + 0.4, tgiro + 1.2) * (1 - seg(t, thad - 0.3, thad + 0.3)))
    figure(d, XR, rp)
    if t > tgiro: g.ellipse([XR - 200, GY - 420, XR + 280, GY + 30], fill=(80, 230, 225, int(80 * seg(t, tgiro, tgiro + 2.0))))
    Z.anillos(d, XR, GY - 228, t, tgiro, 2.6)
    if dua > 0.05 and t < t10:
        Z.bocadillo(d, 650, GY - 440, "ME REFUGIO EN TI", alpha=255 * dua, size=24, cola=-1)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, tgiro - 0.4, tgiro))
    if la > 0: Z.labels(d, t, la, "SE OLVIDA", "SE REFUGIA", t10, t30, 40, lx=245, rx=705)
    Z.subs(d, t, [(0.4, s1 - 0.15, "¿QUÉ DICE ANTES DE ENTRAR AL BAÑO?"), (s1, s2 - 0.15, "UNO ABRE SIN DECIR NADA"),
                  (s2, t10 - 0.1, "EL OTRO PIDE REFUGIO EN ALLAH"), (t30, tq - 0.1, "UNO YA NO SALE SOLO")])
    Z.pregunta(d, t, tq, tgiro, "¿Y POR QUÉ A ÉL NO?")
    if tgiro <= t < thad:
        al = 255 * seg(t, tgiro, tgiro + 0.4) * (1 - seg(t, thad - 0.4, thad))
        spaced(d, "UNA FRASE EN LA PUERTA.", W / 2, 360, Z.fit("UNA FRASE EN LA PUERTA.", 52, 760), al)
        spaced(d, "Y NADA ENTRA CON ÉL.", W / 2, 440, Z.fit("Y NADA ENTRA CON ÉL.", 44, 760), al * seg(t, tgiro + 1.2, tgiro + 1.7), col=(190, 225, 222))
    Z.fuente(d, t, thad, tfin, ["«OH ALLAH, ME REFUGIO", "EN TI DE LOS DEMONIOS,", "MACHOS Y HEMBRAS»"], "SAHIH AL-BUJARI 142")
    Z.final(d, t, tfin, "UNA FRASE.", "UNA CORTINA DE LUZ.", task, "¿TÚ LA DICES?", "ESCRIBE «DESDE HOY»")
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
