# Estilo Noche · ABIERTA vs CERRADA · "¿Sabes por qué un musulmán cierra la puerta diciendo bismillah?" (Sahih al-Bujari 3304)
# Apuesta segura: hábito diario de la sunnah + «lo invisible», gancho «¿Sabes por qué…?» (curiosidad para IG).
# Cae la noche (el sol se esconde) y las sombras SALEN DE LA TIERRA entre dos casas. Uno deja la puerta abierta: las sombras
# se cuelan y día a día su casa se llena de humo. El otro la cierra diciendo «bismillah»: aparece un SELLO DE LUZ (cerrojo +
# estrella de 8 puntas) y cada sombra que empuja se deshace en chispas; su ventana se enciende y le crecen raíces.
# Objetos nuevos: sol poniente, sombras que salen de la tierra, sello de luz en la puerta, casa llena de humo, ventana.
# Uso: python3 2026-11-27-1200-puerta-noche.py salida.mp4 [t1 t2 ... para fotogramas]   (NOVOZ=1 reutiliza el guion)
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes por qué un musulmán cierra la puerta diciendo bismillah?",
         "Cae la noche… y salen las sombras.",
         "Uno deja la puerta abierta.",
         "El otro la cierra y dice: bismillah.",
         "Día diez.",
         "Día treinta. Una casa llena de humo.",
         "¿Y por qué en la otra no entra nada?",
         "El Profeta, la paz sea con él, dijo: cerrad las puertas y nombrad a Allah, porque el shaitán no abre una puerta cerrada.",
         "Una puerta. Un nombre.",
         "¿Esta noche la cierras así? Escribe: bismillah."]
PAUSAS = [0.4, 0.7, 0.6, 1.3, 1.3, 0.8, 2.0, 0.7, 0.6, 1.2]
def SFX(s): return [dict(t=s[3] + 1.5, f=1320, dur=0.8, v=0.06), dict(t=s[4] + 0.9, f=1320, dur=0.8, v=0.05),
                    dict(t=s[7] - 0.35, f=660, dur=2.0, v=0.08), dict(t=s[7] - 0.2, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-27-1200-puerta-noche.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, s3, t10, t30, tq, thad, tfin, task = starts
print("DUR", DUR, starts)

HL = (40, 470); HR = (610, 1040)          # casas
DL, DR = 400, 680                         # puertas
FL, FR = 215, 790                         # figuras
DH = 230
TEAL = (130, 240, 232)
SOMBRA = (96, 86, 118)              # algo más clara para que se lea sobre el cielo

ABRE = dict(P["stand"]); ABRE.update(re=(52, -214), rh=(96, -200))           # mano hacia la puerta (derecha)
CIERRA = Z.espejo(ABRE)                                                      # mano hacia la puerta (izquierda)
CARGADO = dict(P["stand"]); CARGADO.update(head=(18, -270), neck=(10, -236), hip=(0, -124), le=(30, -180), lh=(40, -122),
                                           re=(36, -182), rh=(50, -124), lk=(-10, -60), rk=(18, -60))

def golpe(t, t0):
    """Sombra que va hacia la puerta derecha y se deshace al tocar el sello: devuelve (x, alpha)."""
    u = seg(t, t0, t0 + 1.0)
    return lerp(560, DR - 80, u), 245 * (1 - seg(t, t0 + 0.9, t0 + 1.2))

def frame(t):
    bright = 0.1 + 0.08 * seg(t, s3, s3 + 1.5) + 0.8 * seg(t, thad - 0.3, thad + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    # ---------- el sol se esconde ----------
    Z.sol_poniente(d, g, 540, seg(t, 0.0, s1 + 1.2))
    # ---------- bajo el suelo ----------
    hk = 0.3 * seg(t, s2 + 1.2, s2 + 2.6) + 0.3 * seg(t, t10 + 0.4, t10 + 2.0) + 0.4 * seg(t, t30, t30 + 2.0)
    Z.humo_dentro(du, FL + 40, hk, t)
    Z.grietas(d, FL + 40, seg(t, tq + 0.4, tq + 2.4), seed=4)
    rg = 0.3 * seg(t, s3 + 1.6, s3 + 3.0) + 0.3 * seg(t, t10 + 0.6, t10 + 2.2) + 0.4 * seg(t, tq + 0.6, thad + 1.0)
    Z.roots(d, rg, x0=FR + 60)
    # ---------- casas ----------
    Z.casa(d, *HL, wall_h=340, roof_h=120)
    Z.casa(d, *HR, wall_h=340, roof_h=120)
    Z.ventana(d, g, 950, GY - 250, 0.25 * seg(t, s3 + 1.5, s3 + 2.5) + 0.75 * seg(t, thad, thad + 1.5))
    Z.ventana(d, g, 120, GY - 250, 0.2 * (1 - seg(t, t10, t30 + 1.0)), alpha=255 * (1 - 0.35 * seg(t, t30, t30 + 1.5)))
    # ---------- sombras que salen de la tierra (entre las casas) ----------
    sal = [(520, s1 + 0.3), (585, s1 + 0.8), (545, t10 + 0.1), (590, t10 + 0.4), (530, t30 + 0.1), (575, t30 + 0.3)]
    dentro = []                                         # sombras que se cuelan en la casa abierta
    destino_l = [300, 140, 330, 95, 260, 180]
    for i, (sx, t0) in enumerate(sal):
        rise = seg(t, t0, t0 + 1.2)
        if rise <= 0: continue
        if i % 2 == 0:                                  # van a la casa abierta
            u = seg(t, max(t0 + 1.2, s2 + 0.6), max(t0 + 1.2, s2 + 0.6) + 1.6)
            x = lerp(sx, destino_l[i], u)
            Z.sombra_sale(du, x, 0.55, rise, 245 - 30 * u, t, seed=i, col=SOMBRA)
        else:                                           # van a la puerta cerrada y se deshacen
            t_go = max(t0 + 1.2, s3 + 1.6)
            if t < t_go: Z.sombra_sale(du, sx, 0.55, rise, 245, t, seed=i, col=SOMBRA)
            else:
                x, a = golpe(t, t_go)
                Z.sombra(du, x, 0.55, a, t + i, col=SOMBRA)
                Z.chispas(d, DR - 52, GY - 120, t, t_go + 0.9, seed=7 + i)
    Z.humo_casa(du, HL[0], HL[1], GY - 330, 0.25 * seg(t, t10 + 1.0, t10 + 2.5) + 0.75 * seg(t, t30 + 0.4, t30 + 2.4), t)
    # ---------- IZQUIERDA: puerta abierta ----------
    Z.puerta(d, DL, 0.65, h=DH, w=104, lado=1)
    lp = Z.lerp_pose(P["stand"], CARGADO, 0.4 * seg(t, t10 + 0.8, t10 + 1.8))
    lp = Z.lerp_pose(lp, CARGADO, seg(t, t30 + 0.6, t30 + 1.6))
    lp = Z.lerp_pose(lp, Z.espejo(P["sad"]), seg(t, tq + 0.6, tq + 1.8))
    figure(d, FL, lp, alpha=int(255 - 70 * seg(t, thad, thad + 1.5)))
    # ---------- DERECHA: la cierra con bismillah ----------
    cierra = seg(t, s3 + 0.2, s3 + 1.0)
    Z.puerta(d, DR, 0.65 * (1 - cierra), h=DH, w=104, lado=-1)
    Z.sello_luz(d, g, DR, GY - DH / 2, seg(t, s3 + 1.2, s3 + 2.0) * (1 + 0.0 * t), t)
    mano = seg(t, s3, s3 + 0.4) * (1 - seg(t, s3 + 1.6, s3 + 2.1))
    rp = Z.lerp_pose(P["stand"], CIERRA, mano)
    rp = Z.lerp_pose(rp, P["joy"], seg(t, thad + 0.2, thad + 1.0) * (1 - seg(t, thad + 3.2, thad + 3.8)))
    figure(d, FR, rp)
    if s3 + 0.1 < t < t10 - 0.2:
        Z.bocadillo(d, 840, GY - 420, "BISMILLAH", alpha=255 * seg(t, s3 + 0.1, s3 + 0.4) * (1 - seg(t, t10 - 0.6, t10 - 0.2)), size=28, cola=-1)
    if t > thad: g.ellipse([FR - 220, GY - 430, FR + 240, GY + 30], fill=(80, 230, 225, int(70 * seg(t, thad, thad + 2.0))))
    Z.anillos(d, DR, GY - DH / 2, t, thad, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "ABIERTA", "CERRADA", t10, t30, 46, lx=255, rx=790)
    Z.subs(d, t, [(-0.4, s1 - 0.15, "¿POR QUÉ LA CIERRA CON «BISMILLAH»?"), (s1, s2 - 0.1, "CAE LA NOCHE… Y SALEN LAS SOMBRAS"),
                  (s2, s3 - 0.1, "UNO DEJA LA PUERTA ABIERTA"), (s3, t10 - 0.1, "EL OTRO LA CIERRA: «BISMILLAH»"),
                  (t30, tq - 0.1, "UNA CASA LLENA DE HUMO")])
    Z.pregunta(d, t, tq, thad, "¿Y EN LA OTRA?")
    Z.fuente(d, t, thad, tfin, ["«CERRAD LAS PUERTAS", "Y NOMBRAD A ALLAH:", "EL SHAITÁN NO ABRE", "UNA PUERTA CERRADA»"], "SAHIH AL-BUJARI 3304")
    Z.final(d, t, tfin, "UNA PUERTA.", "UN NOMBRE.", task, "¿ESTA NOCHE LA CIERRAS ASÍ?", "ESCRIBE «BISMILLAH»")
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
