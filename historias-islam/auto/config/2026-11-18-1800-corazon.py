# Estilo Noche · POR FUERA vs POR DENTRO · "lo que ves vs lo que Allah ve" (Sahih Muslim 2564)
# Explorar: variante arriba/abajo del suelo con gancho de curiosidad («¿Sabes qué mira Allah de ti?») para Instagram.
# Arriba: uno se pone corona, brilla y suben los likes (público que aplaude); el otro, sencillo, da en secreto y se postra.
# Debajo del suelo, sus corazones: el del que cuida la imagen se apaga y se agrieta; el del otro crece y se ilumina.
# Día 30 «ahora, mira debajo»: lo de fuera se apaga y el corazón bueno lanza una columna de luz hasta la estrella.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-18-1800-corazon.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced, coin

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué mira Al-lá de ti? Te doy una pista: no es tu foto.",
         "Uno cuida lo que se ve: la ropa, la foto, los likes.",
         "El otro cuida lo que no se ve.",
         "Día diez.",
         "¿Quién brilla más?",
         "Día treinta. Ahora, mira debajo.",
         "El Profeta, la paz sea con él, dijo: Al-lá no mira vuestras formas ni vuestras riquezas, sino vuestros corazones y vuestras obras.",
         "Lo de fuera se ve. Lo de dentro, cuenta.",
         "¿Qué cuidas más: tu foto, o tu corazón?"]
PAUSAS = [0.6, 0.6, 0.9, 0.5, 2.0, 0.7, 0.8, 0.8, 1.4]
def SFX(s): return [dict(t=s[2] + 2.2, f=1320, dur=0.8, v=0.06), dict(t=s[5] + 1.0, f=660, dur=2.0, v=0.08), dict(t=s[5] + 1.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-18-1800-corazon.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.04)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts, ends)

LX, RX = 280, 760
HY = GY + 250                     # corazones bajo el suelo
CROWD = [70, 130, 455]
POBRE = 900
REVEAL = t30 + 1.0                # «ahora, mira debajo»

def frame(t):
    rv = seg(t, REVEAL, REVEAL + 2.2)
    bright = 0.12 + 0.08 * seg(t, t10, t10 + 1.0) + 0.8 * rv
    base, fg, d, glow, g = Z.base_frame(t, bright)
    # ---------- lo que no se ve: los corazones ----------
    rl = 46 * (1 - 0.35 * seg(t, s1 + 1.0, t30 + 1.5))
    gl = seg(t, s1 + 1.0, t30 + 1.5)
    coll = tuple(int(lerp(a, b, gl)) for a, b in zip(CREAM, (88, 86, 96)))
    Z.corazon(d, g, LX, HY, rl, col=coll, alpha=235, grieta=0.4 * seg(t, t10, t10 + 1.2) + 0.6 * seg(t, REVEAL, REVEAL + 1.0))
    gr = 0.25 * seg(t, s2 + 0.8, s2 + 2.6) + 0.25 * seg(t, t10 + 0.3, t10 + 1.6) + 0.5 * rv
    rr = 46 + 40 * gr
    colr = tuple(int(lerp(a, b, gr)) for a, b in zip(CREAM, (150, 245, 238)))
    pulse = 1 + 0.04 * math.sin(t * 5) * gr
    Z.corazon(d, g, RX, HY, rr * pulse, col=colr, alpha=245, brillo=gr)
    if rv > 0:                                        # columna de luz del corazón a la estrella
        top = lerp(HY, 720, rv)                       # sube vertical hasta debajo de los textos
        g.polygon([(RX - 46, HY), (RX + 46, HY), (RX + 70, top), (RX - 70, top)], fill=(120, 245, 238, int(90 * rv)))
        for i in range(10):                           # chispas que suben por la columna
            ph = (t * 0.5 + i / 10) % 1; yy = lerp(HY - 40, 740, ph)
            if yy > top: Z.gota(d, g, RX + 34 * math.sin(i * 2.3 + t * 2), yy, r=4 + 3 * (1 - ph), alpha=230 * rv * (1 - ph))
    # ---------- IZQUIERDA: POR FUERA ----------
    out_k = seg(t, s1 + 0.3, s1 + 1.0) * (1 - seg(t, REVEAL, REVEAL + 1.2))   # lo que luce
    if t < REVEAL + 0.6:
        ph = seg(t, s1 + 0.3, s1 + 0.8) * (1 - seg(t, REVEAL - 0.3, REVEAL + 0.3))
        lp = {j: (lerp(P["stand"][j][0], Z.PHONE[j][0], ph), lerp(P["stand"][j][1], Z.PHONE[j][1], ph)) for j in P["stand"]}
    else:
        lp = pose_mix("stand", "sad", seg(t, REVEAL + 0.6, REVEAL + 1.8))
    figure(d, LX, lp, alpha=int(255 * (1 - 0.3 * rv)))
    Z.destellos(d, g, LX, GY - 330, GY - 20, t, out_k * (0.6 + 0.4 * seg(t, t10, t10 + 1)))
    # corona: aparece en la cabeza; el día 30 se apaga y cae al suelo
    if t > s1 + 0.4:
        fall = seg(t, REVEAL, REVEAL + 1.0)
        hx = LX + (-4 if t < REVEAL else lerp(-4, 70, fall)); hy = lerp(GY - 334, GY - 4, fall * fall)
        cg = tuple(int(lerp(a, b, fall)) for a, b in zip(GOLD, (100, 98, 96)))
        Z.corona(d, g, hx, hy, k=0.8 * seg(t, s1 + 0.4, s1 + 0.9) * (1 + 0.15 * math.sin(math.pi * seg(t, s1 + 0.4, s1 + 0.9))), col=cg, brillo=1 - fall)
    Z.movil(d, g, LX + 34, GY - 272, alpha=255 * seg(t, s1 + 0.3, s1 + 0.8) * (1 - seg(t, REVEAL - 0.3, REVEAL + 0.3)))
    Z.likes(d, g, LX + 34, GY - 290, t, out_k * (0.5 + 0.5 * seg(t, t10, t10 + 1)))
    # contador de likes encima
    if s1 + 0.6 < t < REVEAL + 1.2:
        n = int(1200 * seg(t, s1 + 0.6, s2) + 8800 * seg(t, t10, t10 + 1.2) + 40000 * seg(t, tq, t30))
        txt = f"{n/1000:.1f}K".replace(".0K", "K").replace(".", ",") if n >= 1000 else str(n)
        ca = 255 * seg(t, s1 + 0.6, s1 + 0.9) * (1 - seg(t, REVEAL, REVEAL + 1.2))
        Z.corazon(d, g, LX - 46, GY - 392, 15, col=(235, 110, 120), alpha=ca)
        spaced(d, txt, LX + 30, GY - 392, 36, ca, col=(240, 200, 200))
    # público que aplaude (día 10) y se va el día 30
    crowd = seg(t, t10, t10 + 0.8) * (1 - seg(t, REVEAL, REVEAL + 1.0))
    for j, cx in enumerate(CROWD):
        if crowd > 0: Z.mini_figure(d, cx, P["joy"] if (int(t * 3 + j) % 2) else P["stand"], 0.38, alpha=190 * crowd)
    # ---------- DERECHA: POR DENTRO ----------
    pob = seg(t, s2 - 0.2, s2 + 0.4) * (1 - seg(t, t10 - 0.3, t10 + 0.2))
    if pob > 0: Z.mini_figure(d, POBRE, pose_mix("stand", "sad", 0.5), 0.55, alpha=220 * pob)
    if t < s2 + 1.6:
        rp = pose_mix("stand", "give", seg(t, s2 + 0.1, s2 + 0.5) * (1 - seg(t, s2 + 1.3, s2 + 1.6)))
    elif t < t10 + 1.8:                                # se postra a solas (también el día 10)
        k1 = seg(t, s2 + 1.6, s2 + 2.2) * (1 - seg(t, t10 - 0.4, t10)) + seg(t, t10 + 0.2, t10 + 0.8) * (1 - seg(t, t10 + 1.4, t10 + 1.8))
        rp = Z.a_sujud(k1, izquierda=True)
    elif t < REVEAL + 0.8: rp = P["stand"]
    else: rp = pose_mix("stand", "joy", seg(t, REVEAL + 0.8, REVEAL + 1.5) * (1 - seg(t, thad + 3.5, thad + 4.3)))
    figure(d, RX, rp)
    if s2 + 0.3 < t < s2 + 1.3:                        # la moneda pasa al que lo necesita, sin que nadie lo vea
        u = seg(t, s2 + 0.3, s2 + 1.1)
        coin(d, lerp(RX + 118, POBRE - 20, u), lerp(GY - 228, GY - 150, u) - 30 * math.sin(math.pi * u), r=16)
    for a0 in (s2 + 0.9, s2 + 2.2, t10 + 0.7):        # cada obra en secreto baja como luz al corazón
        if a0 < t < a0 + 1.1:
            u = seg(t, a0, a0 + 1.1)
            Z.gota(d, g, lerp(RX + 60, RX, u) + 20 * math.sin(u * 6), lerp(GY - 80, HY - 20, u), r=8, alpha=240 * (1 - 0.4 * u))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "POR FUERA", "POR DENTRO", t10, t30, 44)
    Z.subs(d, t, [(-0.3, 2.3, "¿SABES QUÉ MIRA ALLAH DE TI?"), (2.3, s1 - 0.15, "PISTA: NO ES TU FOTO"), (s1, s2 - 0.15, "UNO CUIDA LO QUE SE VE"), (s2, t10 - 0.1, "EL OTRO, LO QUE NO SE VE"),
                  (REVEAL - 0.2, thad - 0.1, "AHORA, MIRA DEBAJO ↓")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN BRILLA MÁS?")
    Z.fuente(d, t, thad, tfin, ["«ALLAH NO MIRA", "VUESTRAS FORMAS NI", "VUESTRAS RIQUEZAS,", "SINO VUESTROS", "CORAZONES Y OBRAS»"], "SAHIH MUSLIM 2564")
    Z.final(d, t, tfin, "LO DE FUERA SE VE.", "LO DE DENTRO CUENTA.", task, "¿QUÉ CUIDAS MÁS:", "TU FOTO O TU CORAZÓN?")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
