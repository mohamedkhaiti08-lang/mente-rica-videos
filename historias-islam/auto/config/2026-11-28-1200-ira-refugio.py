# Estilo Noche · ESTALLA vs SE REFUGIA · "¿Sabes qué dice un musulmán cuando se enfada?" (Sahih al-Bujari 3282)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (una sombra que sopla el fuego de la ira), gancho «¿Sabes qué…?».
# Alguien les grita a los dos («¡APARTA!») y a cada uno se le enciende un FUEGO EN EL PECHO. Detrás de cada uno, una sombra
# de humo SOPLA. Uno le deja soplar y grita: el fuego crece día a día y bajo el suelo se extienden BRASAS y grietas.
# El otro dice «me refugio en Allah del shaitán»: la sombra se deshace en chispas, el fuego se apaga en una luz turquesa
# y le crecen raíces. Objetos nuevos: fuego en el pecho, soplo de la sombra, brasas bajo tierra, poses GRITA / CALMA.
# Uso: python3 2026-11-28-1200-ira-refugio.py salida.mp4 [t1 t2 ... para fotogramas]   (NOVOZ=1 reutiliza el guion)
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué dice un musulmán cuando se enfada?",
         "Les gritan… y se enciende un fuego.",
         "Y detrás, alguien que no ves… sopla.",
         "Uno le deja soplar.",
         "El otro dice: me refugio en Allah del shaitán.",
         "Día diez.",
         "Día treinta. Uno vive ardiendo.",
         "¿Y por qué al otro ya no le prende?",
         "Dos hombres discutían, y el Profeta, la paz sea con él, dijo: conozco una frase que le quitaría la ira: me refugio en Allah del shaitán.",
         "No le dejes soplar.",
         "¿La dirás la próxima vez? Escríbela."]
PAUSAS = [0.35, 0.5, 0.5, 0.5, 1.1, 1.1, 0.7, 1.6, 0.5, 0.5, 1.0]
def SFX(s): return [dict(t=s[4] + 1.6, f=1320, dur=0.8, v=0.06), dict(t=s[5] + 1.0, f=1320, dur=0.8, v=0.05),
                    dict(t=s[8] - 0.35, f=660, dur=2.0, v=0.08), dict(t=s[8] - 0.2, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-28-1200-ira-refugio.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.1)
s0, s1, s2, s3, s4, t10, t30, tq, thad, tfin, task = starts
print("DUR", DUR, starts)

FL, FR = 260, 790                      # figuras
SL, SR = 100, 965                      # sombras detrás
CY = GY - 190                          # altura del pecho
SOMBRA = (96, 86, 118)
TEAL = (130, 240, 232)
ENFADO = dict(P["stand"]); ENFADO.update(le=(-40, -230), lh=(-80, -250), re=(40, -230), rh=(80, -250))   # el que grita (brazos abiertos)
PROVOCA = [(s1 - 0.2, "¡APARTA!"), (t10 - 0.1, "¡TORPE!"), (t30 - 0.1, "¡QUÉ PESADO!")]
GRITOS = [(s3 + 0.3, s4 - 0.1, "¡¿Y TÚ QUÉ?!"), (t10 + 0.5, t30 - 0.3, "¡CÁLLATE!"), (t30 + 0.6, tq - 0.2, "¡BASTA YA!")]

def fuego_izq(t):
    return (0.35 * seg(t, s1 + 0.3, s1 + 1.0) + 0.45 * seg(t, s3, s3 + 1.2) + 0.25 * seg(t, t10 + 0.2, t10 + 1.4)
            + 0.2 * seg(t, t30 + 0.2, t30 + 1.4))

def fuego_der(t):
    k = 0.35 * seg(t, s1 + 0.3, s1 + 1.0) * (1 - seg(t, s4 + 0.9, s4 + 2.0))
    for t0 in (t10, t30):                                   # cada día prende un poco… y se apaga enseguida
        k += 0.3 * seg(t, t0 + 0.1, t0 + 0.5) * (1 - seg(t, t0 + 0.9, t0 + 1.6))
    return k

def frame(t):
    bright = 0.1 + 0.08 * seg(t, s4 + 1.5, s4 + 3.0) + 0.8 * seg(t, thad - 0.3, thad + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    kl, kr = fuego_izq(t), fuego_der(t)
    # ---------- bajo el suelo ----------
    Z.brasas(d, g, FL, 0.25 * seg(t, s3 + 0.6, s4 + 1.0) + 0.35 * seg(t, t10 + 0.4, t10 + 2.0) + 0.4 * seg(t, t30, t30 + 2.0), t)
    Z.grietas(d, FL, seg(t, t30 + 0.6, tq + 1.4), seed=4)
    rg = 0.3 * seg(t, s4 + 1.6, s4 + 3.0) + 0.3 * seg(t, t10 + 0.8, t10 + 2.4) + 0.4 * seg(t, tq + 0.4, thad + 1.0)
    Z.roots(d, rg, x0=FR)
    # ---------- el que provoca (en medio, pequeño) ----------
    for i, (t0, txt) in enumerate(PROVOCA):
        a = 255 * seg(t, t0, t0 + 0.3) * (1 - seg(t, t0 + 1.5, t0 + 1.9))
        if a > 0:
            Z.mini_figure(d, 540, Z.lerp_pose(P["stand"], ENFADO, seg(t, t0, t0 + 0.3)), k=0.62, alpha=a)
            Z.bocadillo(d, 540, GY - 262, txt, alpha=a, size=26, cola=0)
            Z.anillos(d, 540, GY - 170, t, t0, 0.9, col=(240, 150, 110), rmax=120)
    # ---------- sombras detrás (soplan) ----------
    al_l = 235 * seg(t, s2 - 0.2, s2 + 0.8)
    kl_s = 0.8 + 0.1 * seg(t, t10, t10 + 1.0) + 0.14 * seg(t, t30, t30 + 1.0)
    Z.sombra(du, SL, kl_s, al_l, t, col=SOMBRA)
    Z.soplo(d, SL + 30 * kl_s, GY - 235 * kl_s, FL - 30, CY - 20, seg(t, s2 + 0.3, s2 + 1.0), t)
    dis = seg(t, s4 + 0.6, s4 + 1.1)                         # la del refugio se deshace (y vuelve un instante cada día)
    al_r = 235 * seg(t, s2 - 0.2, s2 + 0.8) * (1 - dis)
    for t0 in (t10, t30):
        al_r += 200 * seg(t, t0 + 0.1, t0 + 0.4) * (1 - seg(t, t0 + 0.9, t0 + 1.2))
    Z.sombra(du, SR, 0.8, al_r, t + 2, col=SOMBRA)
    Z.soplo(d, SR - 30 * 0.8, GY - 235 * 0.8, FR + 30, CY - 20, seg(t, s2 + 0.3, s2 + 1.0) * (1 - dis), t + 0.5)
    for t0 in (s4 + 0.6, t10 + 0.9, t30 + 0.9):
        Z.chispas(d, SR - 10, GY - 150, t, t0, seed=int(t0 * 10))
    # ---------- IZQUIERDA: estalla ----------
    lp = Z.lerp_pose(P["stand"], Z.GRITA, seg(t, s3, s3 + 0.4))
    lp = Z.lerp_pose(lp, Z.espejo(P["sad"]), seg(t, tq + 0.4, tq + 1.6))
    figure(d, FL, lp, alpha=int(255 - 60 * seg(t, thad, thad + 1.5)))
    grita = max(seg(t, a, a + 0.2) * (1 - seg(t, b - 0.3, b)) for a, b, _ in GRITOS)
    Z.boca(d, FL + 22, GY - 282, grita)
    Z.fuego_pecho(d, g, FL + 6 - 36 * seg(t, tq + 0.4, tq + 1.6), CY + 84 * seg(t, tq + 0.4, tq + 1.6), min(kl, 1.25) * (1 - 0.35 * seg(t, thad, thad + 1.5)), t)
    for a, b, txt in GRITOS:
        al = 255 * seg(t, a, a + 0.25) * (1 - seg(t, b - 0.3, b))
        if al > 0: Z.bocadillo(d, FL + 10, 660, txt, alpha=al, size=26, cola=1)
    # ---------- DERECHA: se refugia ----------
    rp = Z.lerp_pose(P["stand"], Z.CALMA, seg(t, s4, s4 + 0.5))
    rp = Z.lerp_pose(rp, P["joy"], seg(t, thad + 0.2, thad + 1.0) * (1 - seg(t, thad + 3.2, thad + 3.8)))
    figure(d, FR, rp)
    Z.fuego_pecho(d, g, FR, CY, kr, t, seed=7)
    calma = seg(t, s4 + 1.2, s4 + 2.0)
    if calma > 0:                                            # el fuego se vuelve luz serena
        r = 16 + 3 * math.sin(t * 3)
        d.ellipse([(FR - r) * S, (CY - 10 - r) * S, (FR + r) * S, (CY - 10 + r) * S], fill=TEAL + (int(220 * calma),))
        g.ellipse([FR - 90, CY - 100, FR + 90, CY + 80], fill=(80, 230, 225, int(120 * calma)))
    for a, b in ((s4 + 0.1, t10 - 0.2), (t10 + 0.4, t10 + 1.9), (t30 + 0.4, t30 + 1.9)):
        al = 255 * seg(t, a, a + 0.25) * (1 - seg(t, b - 0.3, b))
        if al > 0: Z.bocadillo(d, 770, 660, "A'ÚDHU BILLAH", alpha=al, size=24, cola=-1, borde=TEAL)
    if t > thad: g.ellipse([FR - 220, GY - 430, FR + 240, GY + 30], fill=(80, 230, 225, int(70 * seg(t, thad, thad + 2.0))))
    Z.anillos(d, FR, CY - 10, t, thad, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "ESTALLA", "SE REFUGIA", t10, t30, 48, lx=FL, rx=735)
    Z.subs(d, t, [(-0.4, s1 - 0.15, "¿QUÉ DICE CUANDO SE ENFADA?"), (s1, s2 - 0.1, "SE LES ENCIENDE UN FUEGO"),
                  (s2, s3 - 0.1, "ALGUIEN QUE NO VES… SOPLA"), (s3, s4 - 0.1, "UNO LE DEJA SOPLAR"),
                  (s4, t10 - 0.1, "«ME REFUGIO EN ALLAH DEL SHAITÁN»"), (t30, tq - 0.1, "UNO VIVE ARDIENDO")])
    Z.pregunta(d, t, tq, thad, "¿Y AL OTRO?")
    Z.fuente(d, t, thad, tfin, ["«CONOZCO UNA FRASE", "QUE LE QUITARÍA LA IRA:", "ME REFUGIO EN ALLAH", "DEL SHAITÁN»"], "SAHIH AL-BUJARI 3282")
    Z.final(d, t, tfin, "NO LE DEJES", "SOPLAR.", task, "¿LA DIRÁS LA PRÓXIMA VEZ?", "ESCRÍBELA ABAJO")
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
