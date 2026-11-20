# Estilo Noche · MIRA ARRIBA vs MIRA ABAJO · "Tienen lo mismo… ¿por qué uno se siente pobre?" (Sahih Muslim 2963)
# Explorar: «lo que ves vs lo que tienes» (comparación + metáfora de la mirada), emoción envidia/gratitud en 2ª persona.
# Los dos tienen la misma casita. Uno mira siempre hacia arriba: le salen burbujas doradas con casas más grandes, coches y móviles,
# su línea de mirada se va hacia ellas y su propia casa se apaga y se agrieta por debajo. El otro mira hacia abajo, a alguien que
# no tiene casa bajo una nube, y le da de lo suyo: la nube se va y su casa se llena de luz (ventana encendida, raíces).
# Giro: «tienen exactamente lo mismo» (signo = entre las dos casas). Lema: «Mira hacia abajo. Verás todo lo que tienes».
# Objetos nuevos: burbujas de deseo (casa grande, coche, móvil), línea de mirada punteada, ventana encendida, signo «=».
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-21-1800-mirar-abajo.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Tienen lo mismo. ¿Por qué uno se siente pobre?",
         "Uno mira siempre al que tiene más.",
         "El otro, al que tiene menos.",
         "Día diez.",
         "¿Quién crees que tiene más?",
         "Día treinta.",
         "Tienen exactamente lo mismo. Pero uno ya no ve lo que tiene.",
         "El Profeta, la paz sea con él, dijo: mirad al que tiene menos, no al que tiene más. Así no despreciaréis lo que Allah os ha dado.",
         "Mira hacia abajo. Verás todo lo que tienes.",
         "¿Y tú, hacia dónde miras?"]
PAUSAS = [0.6, 0.9, 1.3, 0.7, 1.9, 0.5, 0.6, 0.7, 0.8, 1.4]
def SFX(s): return [dict(t=s[2] + 1.2, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06),
                    dict(t=s[6] + 0.4, f=880, dur=1.2, v=0.05)]
GUION = os.path.join(HERE, "2026-11-21-1800-mirar-abajo.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.07)
s0, s1, s2, t10, tq, t30, tgiro, thad, tfin, task = starts
print("DUR", DUR, starts)

XL, XR, XP = 330, 780, 640           # izquierda, derecha y la persona que tiene menos
HL, HR = (80, 230), (860, 1010)      # casas (x0, x1)
TEAL = (130, 240, 232)

# ---------- poses nuevas ----------
ARRIBA = dict(P["stand"]); ARRIBA.update(head=(-16, -298), neck=(-4, -262), le=(-34, -230), lh=(-70, -286))      # mira arriba y señala
ABAJO = dict(P["stand"]); ABAJO.update(head=(-14, -290), neck=(-6, -258))                                         # mira hacia abajo
DAR = dict(ABAJO); DAR.update(le=(-50, -214), lh=(-104, -196))                                                    # le da algo con la mano
SENTADO_TRISTE = Z.sentado(0.0, 0.8)

def mirada(d, x0, y0, x1, y1, k, t, col=CREAM, alpha=180):
    """Línea de mirada punteada que avanza (objeto nuevo)."""
    if k <= 0: return
    n = 16
    for i in range(int(n * k)):
        u = (i + (t * 2) % 1) / n
        if u > k: continue
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        d.ellipse([(x - 3) * S, (y - 3) * S, (x + 3) * S, (y + 3) * S], fill=col + (int(alpha),))

def casa_grande(d, cx, by, k, c):
    """Casa de dos plantas con cúpula, dentro de una burbuja."""
    w, h = 70 * k, 80 * k
    d.rectangle([(cx - w) * S, (by - h) * S, (cx + w) * S, by * S], outline=c, width=int(4 * S))
    d.line([((cx - w) * S, (by - h / 2) * S), ((cx + w) * S, (by - h / 2) * S)], fill=c, width=int(3 * S))
    d.arc([(cx - 34 * k) * S, (by - h - 34 * k) * S, (cx + 34 * k) * S, (by - h + 34 * k) * S], 180, 360, fill=c, width=int(4 * S))
    for i in (-1, 0, 1):
        d.rectangle([(cx + i * 36 * k - 9 * k) * S, (by - h / 2 - 28 * k) * S, (cx + i * 36 * k + 9 * k) * S, (by - h / 2 - 10 * k) * S], outline=c, width=int(2 * S))

def coche(d, cx, by, k, c):
    d.line([((cx - 70 * k) * S, (by - 20 * k) * S), ((cx - 66 * k) * S, (by - 44 * k) * S), ((cx - 30 * k) * S, (by - 48 * k) * S),
            ((cx - 12 * k) * S, (by - 74 * k) * S), ((cx + 34 * k) * S, (by - 74 * k) * S), ((cx + 54 * k) * S, (by - 48 * k) * S),
            ((cx + 72 * k) * S, (by - 42 * k) * S), ((cx + 72 * k) * S, (by - 20 * k) * S), ((cx - 70 * k) * S, (by - 20 * k) * S)], fill=c, width=int(4 * S), joint="curve")
    for wx in (-40, 42):
        r = 15 * k; d.ellipse([(cx + wx * k - r) * S, (by - 20 * k - r) * S, (cx + wx * k + r) * S, (by - 20 * k + r) * S], outline=c, width=int(4 * S))

def movil_grande(d, cx, by, k, c):
    d.rounded_rectangle([(cx - 30 * k) * S, (by - 110 * k) * S, (cx + 30 * k) * S, by * S], radius=int(8 * k * S), outline=c, width=int(4 * S))
    d.line([((cx - 8 * k) * S, (by - 10 * k) * S), ((cx + 8 * k) * S, (by - 10 * k) * S)], fill=c, width=int(3 * S))
    for j in range(3):
        d.line([((cx - 18 * k) * S, (by - 90 * k + j * 20 * k) * S), ((cx + 18 * k) * S, (by - 90 * k + j * 20 * k) * S)], fill=c, width=int(2 * S))

BUBS = [(210, 735, 72, "casa"), (400, 690, 62, "coche"), (80, 660, 46, "movil"), (520, 790, 48, "casa"), (330, 820, 42, "movil"), (60, 800, 40, "coche")]
def burbujas(d, g, t, n, alpha=255):
    """Burbujas doradas de lo que tienen otros (objeto nuevo). n = cuántas se ven (0..6)."""
    for i, (cx, cy, r, kind) in enumerate(BUBS):
        a = min(1.0, n - i)
        if a <= 0: continue
        cy += 6 * math.sin(t * 1.3 + i); rr = r * (0.6 + 0.4 * a)
        al = int(alpha * a); c = GOLD + (al,)
        d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline=c, width=int(3 * S))
        g.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(250, 210, 120, int(40 * a)))
        k = rr / 100
        if kind == "casa": casa_grande(d, cx, cy + 50 * k, k, c)
        elif kind == "coche": coche(d, cx, cy + 40 * k, k, c)
        else: movil_grande(d, cx, cy + 55 * k, k, c)

def ventana(d, g, x, y, luz, col=CREAM, alpha=255):
    """Ventana de la casa: se enciende (luz 0..1)."""
    d.rectangle([(x - 22) * S, (y - 22) * S, (x + 22) * S, (y + 22) * S], outline=col + (int(alpha),), width=int(4 * S))
    d.line([(x * S, (y - 22) * S), (x * S, (y + 22) * S)], fill=col + (int(alpha),), width=int(3 * S))
    if luz > 0:
        d.rectangle([(x - 18) * S, (y - 18) * S, (x + 18) * S, (y + 18) * S], fill=GOLD + (int(200 * luz),))
        g.ellipse([x - 70, y - 70, x + 70, y + 70], fill=(250, 215, 130, int(120 * luz)))

def igual(d, g, t, a, b):
    """Signo = grande entre las dos casas en el giro."""
    if t < a or t > b: return
    al = 255 * seg(t, a, a + 0.4) * (1 - seg(t, b - 0.4, b)); cx, cy = 600, 650
    for dy in (-16, 16):
        d.line([((cx - 60) * S, (cy + dy) * S), ((cx + 60) * S, (cy + dy) * S)], fill=TEAL + (int(al),), width=int(10 * S))
    g.ellipse([cx - 100, cy - 60, cx + 100, cy + 60], fill=(80, 230, 225, int(al * 0.4)))
    for x0, x1 in (HL, HR):                                    # las dos casas se marcan iguales
        Z.casa(d, x0, x1, wall_h=210, roof_h=90, col=TEAL, alpha=al * 0.9)

def frame(t):
    bright = 0.15 + 0.15 * seg(t, t10, t10 + 1.2) + 0.7 * seg(t, t30 + 0.4, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, do = Z.new_layer()
    dark = 0.3 * seg(t, t10, t10 + 2.0) + 0.4 * seg(t, t30, t30 + 2)
    # ---------- lo que no se ve ----------
    Z.grietas(d, (HL[0] + HL[1]) / 2, 0.35 * seg(t, t10 + 0.6, t10 + 2.2) + 0.65 * seg(t, t30 + 0.4, t30 + 2.6), seed=11)
    rg = 0.3 * seg(t, s2 + 1.0, s2 + 3.0) + 0.3 * seg(t, t10 + 0.6, t10 + 2.2) + 0.4 * seg(t, t30 + 0.4, t30 + 2.8)
    Z.roots(d, rg, x0=(HR[0] + HR[1]) / 2 - 20)
    # ---------- IZQUIERDA: mira arriba ----------
    gris = 1 - 0.55 * dark
    hc = tuple(int(c * gris + 70 * (1 - gris)) for c in CREAM)
    Z.casa(d, HL[0], HL[1], wall_h=210, roof_h=90, col=hc)
    ventana(d, g, (HL[0] + HL[1]) / 2, GY - 120, 0.0, col=hc)
    lp = Z.lerp_pose(P["stand"], ARRIBA, seg(t, s1, s1 + 0.6))
    if t > t30 + 0.6:                                          # se encoge, sigue mirando arriba
        dr = seg(t, t30 + 0.6, t30 + 2.0); lp = dict(lp); lp["lh"] = (lerp(lp["lh"][0], -36, dr), lerp(lp["lh"][1], -150, dr)); lp["le"] = (lerp(lp["le"][0], -28, dr), lerp(lp["le"][1], -212, dr))
    figure(d, XL, lp, alpha=int(255 * (1 - 0.35 * dark)))
    nb = 2 * seg(t, s1 + 0.3, s1 + 2.0) + 2 * seg(t, t10, t10 + 1.6) + 2 * seg(t, t30, t30 + 1.8)
    burbujas(d, g, t, nb, alpha=255 * (1 - 0.6 * seg(t, thad - 0.4, thad)))
    if t > s1:
        hx, hy = XL + lp["head"][0], GY + lp["head"][1]
        mirada(d, hx - 20, hy - 30, 240, 790, seg(t, s1 + 0.2, s1 + 1.2) * (1 - seg(t, thad - 0.4, thad)), t, col=GOLD, alpha=200)
    # ---------- DERECHA: mira abajo ----------
    luz = 0.35 * seg(t, s2 + 1.0, s2 + 2.4) + 0.25 * seg(t, t10 + 0.6, t10 + 2.0) + 0.4 * seg(t, t30 + 0.4, t30 + 2.4)
    Z.casa(d, HR[0], HR[1], wall_h=210, roof_h=90)
    ventana(d, g, (HR[0] + HR[1]) / 2, GY - 120, luz)
    dar = seg(t, s2 + 0.8, s2 + 1.4) * (1 - seg(t, s2 + 2.6, s2 + 3.2)) + seg(t, t10 + 0.6, t10 + 1.2) * (1 - seg(t, t10 + 2.4, t10 + 3.0))
    rp = Z.lerp_pose(P["stand"], ABAJO, seg(t, s2, s2 + 0.6)); rp = Z.lerp_pose(rp, DAR, dar)
    rp = Z.lerp_pose(rp, P["joy"], seg(t, t30 + 1.2, t30 + 2.0) * (1 - seg(t, tgiro + 2.6, tgiro + 3.4)))
    figure(d, XR, rp)
    if t > s2:
        hx, hy = XR + rp["head"][0], GY + rp["head"][1]
        mirada(d, hx - 26, hy + 10, XP + 40, GY - 210, seg(t, s2 + 0.2, s2 + 1.0) * (1 - seg(t, thad - 0.4, thad)), t, col=TEAL, alpha=200)
    # la persona que tiene menos: sentada bajo una nube; recibe pan y se levanta contenta
    alegre = seg(t, t30 + 0.6, t30 + 2.0)
    pp = Z.lerp_pose(SENTADO_TRISTE, Z.sentado(0.0, 0.0, joy=1.0), alegre)
    Z.mini_figure(d, XP, pp, k=0.85, alpha=235)
    Z.nube(do, XP + 10, GY - 450, 230 * (1 - seg(t, s2 + 1.2, s2 + 2.4)) + 0, t, lluvia=1.0)
    if dar > 0.05:
        fx = lerp(XR - 104, XP + 60, seg(t, s2 + 1.4, s2 + 2.4) if t < t10 else seg(t, t10 + 1.2, t10 + 2.2))
        fy = lerp(GY - 200, GY - 90, seg(t, s2 + 1.4, s2 + 2.4) if t < t10 else seg(t, t10 + 1.2, t10 + 2.2))
        Z.fruta(d, g, fx, fy, alpha=255 * dar)
    nfr = seg(t, s2 + 2.4, s2 + 2.8) + seg(t, t10 + 2.2, t10 + 2.6)
    for i in range(int(nfr + 0.5)): Z.fruta(d, g, XP + 70 + i * 30, GY - 14)
    if t > t30 + 1.0: g.ellipse([XR - 120, GY - 360, XR + 120, GY + 20], fill=(80, 230, 225, int(70 * seg(t, t30 + 1.0, t30 + 2.6))))
    Z.anillos(d, (HR[0] + HR[1]) / 2, GY - 120, t, t30 + 1.0, 2.6)
    igual(d, g, t, tgiro + 0.2, thad - 0.2)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, tgiro - 0.4, tgiro))
    if la > 0: Z.labels(d, t, la, "MIRA ARRIBA", "MIRA ABAJO", t10, t30, 46, lx=280, rx=760)
    Z.subs(d, t, [(0.6, s1 - 0.15, "LA MISMA CASA"), (s1, s2 - 0.15, "UNO MIRA AL QUE TIENE MÁS"), (s2, t10 - 0.1, "EL OTRO, AL QUE TIENE MENOS")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN TIENE MÁS?")
    if tgiro <= t < thad:
        al = 255 * seg(t, tgiro, tgiro + 0.4) * (1 - seg(t, thad - 0.4, thad))
        spaced(d, "TIENEN LO MISMO.", W / 2, 360, Z.fit("TIENEN LO MISMO.", 56, 760), al)
        spaced(d, "UNO YA NO LO VE.", W / 2, 440, Z.fit("UNO YA NO LO VE.", 46, 760), al * seg(t, tgiro + 1.6, tgiro + 2.1), col=(190, 225, 222))
    Z.fuente(d, t, thad, tfin, ["«MIRAD AL QUE TIENE", "MENOS, NO AL QUE", "TIENE MÁS»"], "SAHIH MUSLIM 2963")
    Z.final(d, t, tfin, "MIRA HACIA ABAJO.", "VERÁS TODO LO QUE TIENES.", task, "¿Y TÚ, HACIA DÓNDE", "MIRAS?")
    return Z.finish(base, fg, glow, bright, over=over)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
