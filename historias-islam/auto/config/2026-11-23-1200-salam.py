# Estilo Noche · CALLA vs SALUDA · "¿Sabes qué pasa cuando dices «as-salamu alaykum»?" (Sahih Muslim 54)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (lo que el saludo hace entre los corazones), gancho de curiosidad para IG.
# Los dos viven entre dos vecinos. Uno pasa mirando el móvil sin decir nada: entre él y cada vecino crece un muro gris de ladrillos.
# El otro saluda («AS-SALAMU ALAYKUM»): entre su corazón y el de cada vecino se tiende un lazo de luz, y bajo el suelo
# sus raíces se entrelazan. Día 30: los dos cargan una caja pesada. ¿A quién ayudarán? Los vecinos del que saluda vienen y
# la levantan con él; el otro la deja caer y se sienta solo detrás de sus muros.
# Objetos nuevos: muro de ladrillos que crece, lazo de luz entre corazones (con chispas que viajan), caja pesada, poses cargar/saludar.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-23-1200-salam.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué pasa cuando dices assalamu aleikum?",
         "Uno pasa al lado de la gente sin decir nada.",
         "El otro saluda a cada uno.",
         "Día diez.",
         "Día treinta. Los dos cargan algo pesado.",
         "¿A quién crees que ayudarán?",
         "Una frase pequeña abrió todos los corazones.",
         "El Profeta, la paz sea con él, dijo: ¿os digo algo que, si lo hacéis, os amaréis? Extended el salam entre vosotros.",
         "Saluda. Abre corazones.",
         "¿A quién vas a saludar hoy?"]
PAUSAS = [0.5, 0.6, 1.2, 1.2, 0.4, 1.9, 0.6, 0.7, 0.7, 1.4]
def SFX(s): return [dict(t=s[2] + 0.9, f=1320, dur=0.8, v=0.06), dict(t=s[3] + 0.9, f=1320, dur=0.8, v=0.05),
                    dict(t=s[6] - 0.3, f=660, dur=2.0, v=0.08), dict(t=s[6] - 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-23-1200-salam.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, t10, t30, tq, tgiro, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, XR = 290, 770
NL, NR = (95, 528), (610, 945)       # vecinos (izquierda y derecha)
TEAL = (130, 240, 232)
GRIS = (120, 116, 126)

# ---------- poses nuevas ----------
MOVIL = dict(P["stand"]); MOVIL.update(head=(10, -292), neck=(4, -258), re=(30, -205), rh=(44, -238))
SALUDA = dict(P["stand"]); SALUDA.update(re=(44, -262), rh=(70, -318))
CARGA = dict(head=(10, -284), neck=(6, -248), hip=(0, -122), le=(30, -206), lh=(66, -178), re=(40, -210), rh=(76, -184),
             lk=(-14, -58), lf=(-30, 0), rk=(18, -60), rf=(30, 0))
ERGUIDO = dict(CARGA); ERGUIDO.update(head=(4, -298), neck=(4, -260), hip=(0, -130), lk=(-14, -64), rk=(14, -64))  # carga ya sin esfuerzo

def muro(d, x, h, alpha=255, w=56, col=GRIS):
    """Muro de ladrillos grises que crece desde el suelo (h px). Objeto nuevo: la distancia que no se ve."""
    if h <= 2 or alpha <= 0: return
    bh = 26; n = int(h // bh) + 1
    for i in range(n):
        y1 = GY - i * bh; y0 = max(GY - h, y1 - bh)
        if y0 >= y1: break
        off = (bh / 2 if i % 2 else 0)
        d.rectangle([(x - w / 2) * S, y0 * S, (x + w / 2) * S, y1 * S], fill=(44, 44, 52, int(alpha * 0.9)), outline=col + (int(alpha),), width=int(2 * S))
        d.line([((x - w / 2 + 14 + off) * S, y0 * S), ((x - w / 2 + 14 + off) * S, y1 * S)], fill=col + (int(alpha * 0.8),), width=int(2 * S))

def lazo(d, g, x0, y0, x1, y1, k, t, alpha=255, alto=90, col=TEAL):
    """Lazo de luz en arco entre dos corazones; k 0..1 cuánto se ha tendido. Chispas que viajan por él (objeto nuevo)."""
    if k <= 0 or alpha <= 0: return
    pts = []
    for i in range(41):
        u = i / 40 * k
        pts.append((lerp(x0, x1, u), lerp(y0, y1, u) - alto * math.sin(math.pi * u)))
    d.line([(a * S, b * S) for a, b in pts], fill=col + (int(alpha * 0.9),), width=int(4 * S), joint="curve")
    for a, b in pts[::4]: g.ellipse([a - 18, b - 18, a + 18, b + 18], fill=(90, 235, 228, int(alpha * 0.35)))
    if k >= 1:
        for j in range(2):
            u = (t * 0.45 + j * 0.5) % 1
            a, b = lerp(x0, x1, u), lerp(y0, y1, u) - alto * math.sin(math.pi * u)
            d.ellipse([(a - 6) * S, (b - 6) * S, (a + 6) * S, (b + 6) * S], fill=(230, 255, 250, int(alpha)))
    for (a, b) in ((x0, y0), (pts[-1][0], pts[-1][1])):
        d.ellipse([(a - 9) * S, (b - 9) * S, (a + 9) * S, (b + 9) * S], fill=col + (int(alpha),))

def caja(d, x, y, alpha=255, w=112, h=84, col=CREAM, gris=0.0):
    """Caja de mudanza pesada (centro x, base y)."""
    c = tuple(int(lerp(a, b, gris)) for a, b in zip(col, (110, 108, 116))) + (int(alpha),)
    d.rectangle([(x - w / 2) * S, (y - h) * S, (x + w / 2) * S, y * S], fill=(30, 32, 40, int(alpha)), outline=c, width=int(5 * S))
    d.line([((x - w / 2) * S, (y - h + 18) * S), ((x + w / 2) * S, (y - h + 18) * S)], fill=c, width=int(3 * S))
    d.line([(x * S, (y - h) * S), (x * S, (y - h + 18) * S)], fill=c, width=int(3 * S))

def gotas_sudor(d, x, y, t, alpha=255):
    for i in range(2):
        ph = (t * 1.2 + i * 0.5) % 1
        yy = y + 30 * ph; xx = x + 20 * i
        d.ellipse([(xx - 4) * S, (yy - 7) * S, (xx + 4) * S, (yy + 5) * S], fill=(200, 225, 235, int(alpha * (1 - ph))))

K = 0.78
def frame(t):
    bright = 0.12 + 0.12 * seg(t, t10, t10 + 1.2) + 0.76 * seg(t, tgiro - 0.2, tgiro + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    # ---------- lo que no se ve ----------
    Z.grietas(d, XL, 0.3 * seg(t, t10 + 0.4, t10 + 2.0) + 0.7 * seg(t, tq + 0.8, tq + 3.0), seed=9)
    rg = 0.3 * seg(t, s2 + 1.2, s2 + 3.0) + 0.3 * seg(t, t10 + 0.6, t10 + 2.2) + 0.4 * seg(t, tq + 0.8, tq + 3.2)
    for i, nx in enumerate((XR,) + NR):
        Z.roots(d, rg * (1.0 if i == 0 else 0.75), x0=nx, col=CREAM if i == 0 else (200, 236, 230))
    # ---------- IZQUIERDA: pasa sin decir nada ----------
    hm = 70 * seg(t, s1 + 0.8, s1 + 2.4) + 90 * seg(t, t10 + 0.4, t10 + 2.0) + 110 * seg(t, t30 + 0.4, t30 + 2.0)
    for wx in (192, 472): muro(d, wx, hm)
    for nx in NL:
        Z.mini_figure(d, nx, P["stand"], k=K, alpha=225 - 95 * seg(t, s1 + 0.8, s1 + 2.4))
    carga = seg(t, t30, t30 + 0.8)
    cae = seg(t, tq + 1.0, tq + 1.8)
    lp = Z.lerp_pose(P["stand"], MOVIL, seg(t, s1, s1 + 0.5) * (1 - carga))
    lp = Z.lerp_pose(lp, CARGA, carga * (1 - cae)); lp = Z.lerp_pose(lp, Z.espejo(P["sad"]), cae)
    figure(d, XL, lp, alpha=int(255 - 80 * cae))
    if 0.05 < seg(t, s1, s1 + 0.5) and carga < 0.5:
        Z.movil(d, g, XL + 46, GY - 246, alpha=255 * (1 - carga * 2))
    if carga > 0:
        bx = XL + 96 - 6 * cae; by = lerp(GY - 140, GY, cae)
        caja(d, bx, by, alpha=255 * carga, gris=0.5 * cae)
        caja(d, bx + 6 * cae, by - 84, alpha=255 * carga, w=90, h=64, gris=0.5 * cae)
        if cae < 0.5: gotas_sudor(d, XL + 40, GY - 330, t, 255 * carga * (1 - 2 * cae))
    # ---------- DERECHA: saluda ----------
    sal = seg(t, s2, s2 + 0.5) * (1 - seg(t, s2 + 2.6, s2 + 3.0)) + seg(t, t10 + 0.2, t10 + 0.7) * (1 - seg(t, t10 + 2.4, t10 + 2.8))
    rp = Z.lerp_pose(P["stand"], SALUDA, sal)
    ayuda = seg(t, tq + 0.8, tq + 2.2); toma = seg(t, tq + 2.0, tq + 2.8)
    rp = Z.lerp_pose(rp, CARGA, carga)
    if t > tgiro + 0.6: rp = Z.lerp_pose(rp, ERGUIDO, seg(t, tgiro + 0.6, tgiro + 1.4))
    figure(d, XR, rp)
    vsal = seg(t, s2 + 1.0, s2 + 1.5) * (1 - seg(t, s2 + 2.8, s2 + 3.2)) + seg(t, t10 + 0.9, t10 + 1.4) * (1 - seg(t, t10 + 2.6, t10 + 3.0))
    VA, VB = XR - 120, XR + 205                       # donde se colocan los vecinos para ayudar
    for i, nx0 in enumerate(NR):
        nx = lerp(nx0, VA if i == 0 else VB, ayuda)
        vp = Z.lerp_pose(P["stand"], Z.espejo(SALUDA) if i == 0 else SALUDA, vsal)
        vp = Z.lerp_pose(vp, Z.walk_pose(t * 7, 0.8) if 0.02 < ayuda < 0.98 else vp, 1.0)
        vp = Z.lerp_pose(vp, Z.espejo(CARGA), toma)
        Z.mini_figure(d, nx, vp, k=K)
    if carga > 0:
        by = lerp(GY - 140, GY - 152, toma)
        caja(d, XR + 96, by, alpha=255 * carga)
        tx = lerp(XR + 96, VA - 56, toma); ty = lerp(by - 84, GY - 117, toma)
        caja(d, tx, ty, alpha=255 * carga, w=90, h=64)
        if toma < 0.5: gotas_sudor(d, XR + 40, GY - 330, t, 255 * carga * (1 - 2 * toma))
    # lazos de luz entre corazones
    la_k = 1 - seg(t, t30 - 0.2, t30 + 0.4) * (1 - seg(t, tq + 0.8, tq + 1.6))     # se esconden mientras carga, vuelven al ayudarle
    cx, cy = XR, GY - 228
    if ayuda < 0.05:
        lazo(d, g, cx - 20, cy, NR[0], GY - 178, seg(t, s2 + 0.9, s2 + 2.0), t, 255 * la_k, alto=70)
        lazo(d, g, cx + 20, cy, NR[1], GY - 178, seg(t, s2 + 1.6, s2 + 2.7), t, 255 * la_k, alto=70)
        lazo(d, g, NR[0], GY - 178, NR[1], GY - 178, seg(t, t10 + 1.0, t10 + 2.4), t, 220 * la_k, alto=150)
    else:
        a1, a2 = XR - 120, XR + 205
        for (x0, y0, x1, y1, h) in ((cx - 20, cy, a1, GY - 178, 80), (cx + 20, cy, a2, GY - 178, 110), (a1, GY - 178, a2, GY - 178, 230)):
            lazo(d, g, x0, y0, x1, y1, seg(t, tq + 2.4, tq + 3.4), t, 255, alto=h)
    if t > tgiro: g.ellipse([XR - 260, GY - 420, XR + 260, GY + 30], fill=(80, 230, 225, int(80 * seg(t, tgiro, tgiro + 2.0))))
    Z.anillos(d, XR, GY - 228, t, tgiro, 2.6)
    if sal > 0.05:
        Z.bocadillo(d, 735, GY - 420, "AS-SALAMU ALAYKUM", alpha=255 * sal, size=22, cola=1)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, tgiro - 0.4, tgiro))
    if la > 0: Z.labels(d, t, la, "CALLA", "SALUDA", t10, t30, 46, lx=300, rx=760)
    Z.subs(d, t, [(0.4, s1 - 0.15, "¿QUÉ PASA CUANDO SALUDAS?"), (s1, s2 - 0.15, "UNO PASA SIN DECIR NADA"), (s2, t10 - 0.1, "EL OTRO SALUDA A CADA UNO"),
                  (t30, tq - 0.1, "LOS DOS CARGAN ALGO PESADO")])
    Z.pregunta(d, t, tq, tgiro, "¿A QUIÉN AYUDARÁN?")
    if tgiro <= t < thad:
        al = 255 * seg(t, tgiro, tgiro + 0.4) * (1 - seg(t, thad - 0.4, thad))
        spaced(d, "UNA FRASE PEQUEÑA.", W / 2, 360, Z.fit("UNA FRASE PEQUEÑA.", 54, 760), al)
        spaced(d, "TODOS LOS CORAZONES.", W / 2, 440, Z.fit("TODOS LOS CORAZONES.", 44, 760), al * seg(t, tgiro + 1.4, tgiro + 1.9), col=(190, 225, 222))
    Z.fuente(d, t, thad, tfin, ["«¿OS DIGO ALGO QUE", "OS HARÁ AMAROS?", "DIFUNDID EL SALAM»"], "SAHIH MUSLIM 54")
    Z.final(d, t, tfin, "SALUDA.", "ABRE CORAZONES.", task, "¿A QUIÉN VAS A", "SALUDAR HOY?")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
