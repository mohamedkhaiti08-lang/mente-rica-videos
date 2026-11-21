# Estilo Noche · DE GOLPE vs CADA DÍA · "Empezó con todo… y al mes lo dejó. ¿Te suena?" (Sahih al-Bujari 6464)
# Explorar: metáfora del fuego (hoguera enorme que se apaga vs llama pequeña que nunca se apaga) + arco de luces que se cuenta día a día.
# Emoción: esperanza/autoexigencia (el que empieza con todo y lo deja). Tema nuevo: la constancia.
# Uno enciende una hoguera gigante el día 1 (lo quiere todo de golpe) y salta de alegría; día 10 la hoguera es la mitad y echa humo;
# día 30 solo quedan cenizas y él se sienta en la oscuridad (grietas debajo). El otro sostiene una llamita pequeña: cada día
# deja una luz más en un arco sobre su cabeza (contador de días); día 30 el arco está completo, brilla y crecen raíces de luz.
# Giro: «La llama grande se apagó. La pequeña, nunca.» Lema: «POCO. PERO CADA DÍA.»
# Objetos nuevos: hoguera (con brasas, humo y cenizas), vela de mano, arco de luces (contador de días).
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-23-1800-llama.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Empezó con todo. Y al mes lo dejó. ¿Te suena?",
         "Uno lo quiere hacer todo de golpe.",
         "El otro hace un poco. Pero cada día.",
         "Día diez.",
         "Día treinta.",
         "¿Quién crees que ha llegado más lejos?",
         "La llama grande se apagó. La pequeña, nunca.",
         "El Profeta, la paz sea con él, dijo: la obra más amada por Allah es la más constante, aunque sea poca.",
         "Poco. Pero cada día.",
         "¿Qué vas a hacer tú cada día?"]
PAUSAS = [0.6, 0.7, 1.4, 1.6, 0.8, 1.9, 0.7, 0.7, 0.8, 1.4]
def SFX(s): return [dict(t=s[2] + 1.0, f=1320, dur=0.8, v=0.05), dict(t=s[6] - 0.3, f=660, dur=2.0, v=0.08),
                    dict(t=s[6] - 0.15, f=990, dur=2.0, v=0.06), dict(t=s[8], f=880, dur=1.2, v=0.05)]
GUION = os.path.join(HERE, "2026-11-23-1800-llama.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.07)
s0, s1, s2, t10, t30, tq, tgiro, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, XR = 230, 770
FX = XL + 150                         # hoguera
TEAL = (130, 240, 232)
FUEGO = (250, 196, 120)

VELA_P = dict(P["stand"]); VELA_P.update(re=(36, -214), rh=(70, -232))        # sostiene la llamita delante
CANSADO = dict(P["stand"]); CANSADO.update(head=(16, -282), neck=(8, -248), lh=(-20, -140), rh=(24, -140))

def llama(d, g, x, y, h, w, t, alpha=255, col=FUEGO, seed=0):
    """Una lengua de fuego (gota alargada que tiembla)."""
    if h <= 2 or alpha <= 0: return
    sw = 1 + 0.08 * math.sin(t * 9 + seed); hh = h * (1 + 0.1 * math.sin(t * 7 + seed * 2))
    tip = x + w * 0.35 * math.sin(t * 5 + seed)
    pts = []
    for i in range(13):
        a = math.pi * i / 12
        pts.append((x - w * sw * math.cos(a), y - w * 0.55 * math.sin(a) * 0.6))
    pts += [(x + w * 0.6, y - hh * 0.4), (tip, y - hh), (x - w * 0.6, y - hh * 0.4)]
    d.polygon([(a * S, b * S) for a, b in pts], fill=col + (int(alpha),))
    inner = [(x + (px - x) * 0.5, y + (py - y) * 0.5) for px, py in pts]
    d.polygon([(a * S, b * S) for a, b in inner], fill=(255, 244, 214, int(alpha)))

def hoguera(d, g, x, k, t, ceniza=0.0):
    """Hoguera (objeto nuevo): k 0..1 tamaño del fuego; ceniza 0..1 brasas y ceniza gris cuando se apaga."""
    leña = tuple(int(lerp(a, b, ceniza)) for a, b in zip(CREAM, (100, 98, 104)))
    for a in (-0.35, 0.35, 0.0):
        dx = 90 * math.cos(a) ; dy = 90 * math.sin(a) * 0.25
        d.line([((x - dx) * S, (GY - 10 - dy) * S), ((x + dx) * S, (GY - 10 + dy) * S)], fill=leña + (255,), width=int(12 * S))
    if ceniza > 0:
        d.ellipse([(x - 80) * S, (GY - 22) * S, (x + 80) * S, (GY + 4) * S], fill=(80, 78, 84, int(220 * ceniza)))
        for i in range(5):
            bx = x - 50 + i * 25; d.ellipse([(bx - 5) * S, (GY - 16) * S, (bx + 5) * S, (GY - 6) * S], fill=(230, 120, 80, int(200 * ceniza * (1 - seg(ceniza, 0.6, 1.0)) * (0.5 + 0.5 * math.sin(t * 4 + i)))))
    if k > 0.02:
        for i, (ox, hk, wk) in enumerate(((0, 1.0, 1.0), (-48, 0.7, 0.7), (48, 0.75, 0.7), (-20, 0.55, 0.5), (26, 0.6, 0.5))):
            llama(d, g, x + ox * k, GY - 18, 330 * k * hk, 60 * k * wk + 6, t, seed=i)
        g.ellipse([x - 260 * k, GY - 420 * k - 40, x + 260 * k, GY + 40], fill=(255, 180, 90, int(150 * k)))
        rnd = random.Random(3)
        for i in range(int(14 * k)):                      # chispas
            ph = (t * 0.7 + rnd.random()) % 1
            sx = x + rnd.uniform(-90, 90) * k + 20 * math.sin(t * 3 + i); sy = GY - 60 - ph * 520 * k
            d.ellipse([(sx - 3) * S, (sy - 3) * S, (sx + 3) * S, (sy + 3) * S], fill=FUEGO + (int(255 * (1 - ph)),))

def humo(d, x, y, k, t, seed=4):
    """Humo gris que sube de lo que se apaga."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(10):
        ph = (t * 0.25 + i / 10) % 1
        px = x + 30 * math.sin(ph * 6 + i) + rnd.uniform(-20, 20); py = y - ph * 420
        r = 18 + 40 * ph
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=(110, 108, 118, int(120 * k * (1 - ph))))

def vela(d, g, x, y, t, alpha=255):
    """Vela pequeña en la mano: cuerpo blanco y llamita constante (objeto nuevo)."""
    d.rounded_rectangle([(x - 9) * S, (y - 4) * S, (x + 9) * S, (y + 40) * S], radius=3 * S, fill=CREAM + (int(alpha),))
    llama(d, g, x, y - 6, 34, 9, t * 0.6, alpha)
    g.ellipse([x - 70, y - 90, x + 70, y + 40], fill=(255, 200, 120, int(130 * alpha / 255)))

ARC_C, ARC_R = (XR, GY - 150), 250
def arco(d, g, n, t, brillo=0.0):
    """Arco de 30 luces sobre el personaje: n luces encendidas (contador de días). brillo 0..1 al completarse."""
    for i in range(30):
        a = math.radians(200 - i * 220 / 29)
        x = ARC_C[0] + ARC_R * math.cos(a); y = ARC_C[1] - ARC_R * math.sin(a) * 1.02
        q = max(0.0, min(1.0, n - i))
        if q <= 0:
            d.ellipse([(x - 4) * S, (y - 4) * S, (x + 4) * S, (y + 4) * S], fill=(90, 110, 115, 120)); continue
        r = 8 + 3 * q + 3 * brillo * (0.5 + 0.5 * math.sin(t * 3 + i))
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(int(lerp(250, 150, brillo)), int(lerp(214, 245, brillo)), int(lerp(150, 238, brillo)), int(255 * q)))
        g.ellipse([x - 26, y - 26, x + 26, y + 26], fill=(120, 240, 230, int((90 + 90 * brillo) * q)))

def dias_n(t):
    return (1 + 2 * seg(t, s2 + 0.6, s2 + 2.0) + 7 * seg(t, t10, t10 + 1.6) + 20 * seg(t, t30, t30 + 2.0))

def frame(t):
    bright = 0.1 + 0.12 * seg(t, t10, t10 + 1.2) + 0.78 * seg(t, tgiro - 0.2, tgiro + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, do = Z.new_layer()
    # ---------- lo que no se ve ----------
    Z.grietas(d, XL + 60, 0.35 * seg(t, t10 + 0.6, t10 + 2.2) + 0.65 * seg(t, t30 + 0.6, t30 + 2.6), seed=13)
    rg = 0.25 * seg(t, s2 + 1.0, s2 + 2.6) + 0.3 * seg(t, t10 + 0.6, t10 + 2.2) + 0.45 * seg(t, t30 + 0.6, t30 + 2.8)
    Z.roots(d, rg, x0=XR, col=(200, 240, 234) if t < tgiro else CREAM)
    # ---------- IZQUIERDA: todo de golpe ----------
    k = lerp(0.55, 1.0, seg(t, 0, s1 + 1.0)) * (1 - 0.5 * seg(t, t10, t10 + 1.8)) * (1 - seg(t, t30, t30 + 1.8))
    ceniza = seg(t, t30 + 0.6, t30 + 2.4)
    hoguera(d, g, FX, k, t, ceniza)
    humo(do, FX, GY - 60, seg(t, t10 + 0.4, t10 + 1.6), t)
    joy = seg(t, s1, s1 + 0.5) * (1 - seg(t, t10 - 0.2, t10 + 0.6))
    lp = Z.lerp_pose(P["stand"], P["joy"], joy * (0.75 + 0.25 * math.sin(t * 6)))
    lp = Z.lerp_pose(lp, CANSADO, seg(t, t10, t10 + 0.8))
    sad = seg(t, t30 + 0.6, t30 + 1.6)
    lp = Z.lerp_pose(lp, P["sad"], sad)
    figure(d, XL, lp, alpha=int(255 - 70 * sad))
    # ---------- DERECHA: poco pero cada día ----------
    rp = Z.lerp_pose(P["stand"], VELA_P, seg(t, 0, 0.4) if t > 0.05 else 1.0)
    if t > tgiro + 0.8: rp = Z.lerp_pose(rp, P["joy"], seg(t, tgiro + 0.8, tgiro + 1.6) * 0.0)
    figure(d, XR, rp)
    vela(d, g, XR + rp["rh"][0] + 4, GY + rp["rh"][1] - 34, t)
    arco(d, g, dias_n(t), t, brillo=seg(t, tgiro - 0.2, tgiro + 1.6))
    # «+1» que sube de la vela al arco cuando se añade una luz
    for a0 in (s2 + 0.6, s2 + 1.3, t10 + 0.2, t10 + 0.8, t30 + 0.2, t30 + 0.8, t30 + 1.4):
        if a0 <= t < a0 + 0.7:
            u = (t - a0) / 0.7; vx, vy = XR + 74, GY - 280
            n_ = dias_n(a0 + 0.7); ang = math.radians(200 - min(29, int(n_) - 1) * 220 / 29)
            ax, ay = ARC_C[0] + ARC_R * math.cos(ang), ARC_C[1] - ARC_R * math.sin(ang) * 1.02
            px, py = lerp(vx, ax, u), lerp(vy, ay, u) - 40 * math.sin(math.pi * u)
            d.ellipse([(px - 6) * S, (py - 6) * S, (px + 6) * S, (py + 6) * S], fill=FUEGO + (int(255 * (1 - 0.3 * u)),))
    if t > tgiro: g.ellipse([XR - 300, GY - 480, XR + 300, GY + 30], fill=(80, 230, 225, int(70 * seg(t, tgiro, tgiro + 2.0))))
    Z.anillos(d, XR, GY - 230, t, tgiro, 2.6)
    # contador de días bajo el arco
    if t < tgiro:
        n = int(dias_n(t) + 0.02)
        spaced(d, f"{n}/30", XR, GY - 440, 30, 220 * seg(t, s2, s2 + 0.4) * (1 - seg(t, tgiro - 0.4, tgiro)), col=(200, 240, 234))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, tgiro - 0.4, tgiro))
    if la > 0: Z.labels(d, t, la, "DE GOLPE", "CADA DÍA", t10, t30, 46, lx=280, rx=760)
    Z.subs(d, t, [(0.4, s1 - 0.15, "EMPEZÓ CON TODO…"), (s1, s2 - 0.15, "UNO LO QUIERE TODO DE GOLPE"), (s2, t10 - 0.1, "EL OTRO, UN POCO CADA DÍA")])
    Z.pregunta(d, t, tq, tgiro, "¿QUIÉN LLEGA MÁS LEJOS?")
    if tgiro <= t < thad:
        al = 255 * seg(t, tgiro, tgiro + 0.4) * (1 - seg(t, thad - 0.4, thad))
        spaced(d, "LA GRANDE SE APAGÓ.", W / 2, 360, Z.fit("LA GRANDE SE APAGÓ.", 52, 760), al)
        spaced(d, "LA PEQUEÑA, NUNCA.", W / 2, 440, Z.fit("LA PEQUEÑA, NUNCA.", 46, 760), al * seg(t, tgiro + 1.4, tgiro + 1.9), col=(190, 225, 222))
    Z.fuente(d, t, thad, tfin, ["«LA OBRA MÁS AMADA", "POR ALLAH ES LA MÁS", "CONSTANTE, AUNQUE", "SEA POCA»"], "SAHIH AL-BUJARI 6464")
    Z.final(d, t, tfin, "POCO.", "PERO CADA DÍA.", task, "¿QUÉ VAS A HACER TÚ", "CADA DÍA?")
    return Z.finish(base, fg, glow, bright, over=over)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
