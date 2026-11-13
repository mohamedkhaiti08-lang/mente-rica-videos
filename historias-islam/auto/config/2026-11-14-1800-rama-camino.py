# Estilo Noche · LA DEJA vs LA QUITA · "la misma rama en el camino" (Sahih al-Bujari 2472)
# Metáfora: el camino. Gente pequeña pasa cada día: en un lado tropiezan; en el otro pasan y cada paso sube al cielo como una estrella.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-14-1800-rama-camino.py salida.mp4 [t1 t2 ... para fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Dos personas. La misma rama en el camino.",
         "Uno pasa por encima, y sigue.",
         "El otro se agacha, y la quita.",
         "Día diez.",
         "¿Quién crees que ha ganado más?",
         "Día treinta.",
         "El Profeta, la paz sea con él, contó que un hombre quitó una rama con espinas del camino, y Allah se lo agradeció, y le perdonó.",
         "Lo pequeño. Allah lo ve.",
         "¿Qué cosa pequeña has hecho hoy?"]
PAUSAS = [0.7, 0.9, 1.4, 0.7, 2.2, 0.8, 1.0, 1.0, 1.6]
def SFX(s): return [dict(t=s[2] + 2.0, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=os.path.join(HERE, "2026-11-14-1800-rama-camino.guion.json"))
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

BL, BR, SEED = 300, 790, 930            # rama izquierda, rama derecha, donde cae la rama tirada
SPD = 240                               # velocidad de la gente pequeña (px/s)
rnd = random.Random(4)
SKY = [(rnd.uniform(600, 1030), rnd.uniform(720, 1010)) for _ in range(40)]   # estrellas que deja cada paso
WALK_T = [t10 - 0.6 + 1.25 * i for i in range(12)]

def stars_right(t):
    """Momentos en que un caminante pasa por el sitio limpio (cada uno deja una estrella)."""
    out = [a + (BR - 560) / SPD for a in WALK_T if a + (BR - 520) / SPD < min(t, thad)]
    burst = int(28 * seg(t, t30 + 0.3, t30 + 2.5))           # día 30: se llena el cielo
    return out, burst

def frame(t):
    bright = 0.15 + 0.2 * seg(t, t10, t10 + 1.2) + 0.65 * seg(t, t30, t30 + 2.5)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    # ---------- DERECHA: estrellas de cada paso, raíces y camino de luz ----------
    passes, burst = stars_right(t)
    for i, tp in enumerate(passes):
        k = seg(t, tp, tp + 1.4); sx, sy = SKY[i]
        x = lerp(BR, sx, k); y = lerp(GY - 110, sy, k) - 80 * math.sin(math.pi * k)
        Z.gota(d, g, x, y, r=6 + 2 * k)
    for i in range(burst):
        sx, sy = SKY[(len(passes) + i) % len(SKY)]
        tw = 0.7 + 0.3 * math.sin(t * 3 + i)
        Z.gota(d, g, sx, sy, r=6 * tw)
    Z.roots(d, 0.25 * seg(t, s2 + 2.6, s2 + 4.2) + 0.25 * seg(t, t10, t10 + 1.5) + 0.5 * seg(t, t30, t30 + 2.5), x0=SEED)
    Z.camino_luz(d, g, 545, 1080, seg(t, t30 + 0.2, t30 + 2.4))
    fl = seg(t, t30 + 1.4, t30 + 3.4)
    for i, fx in enumerate((585, 625, 870, 1000, 1045)):
        Z.flor(d, fx, 64 * min(1, max(0, fl * 1.5 - i * 0.1)))
    # ---------- IZQUIERDA: la rama se queda; grietas ----------
    Z.grietas(d, BL, 0.4 * seg(t, t10, t10 + 1.5) + 0.6 * seg(t, t30, t30 + 2.5))
    gris = 0.35 * seg(t, t10, t10 + 1) + 0.65 * seg(t, t30, t30 + 1.5)
    Z.rama(d, BL, GY - 14, 0.05, k=1.5 + 0.3 * seg(t, t30, t30 + 2))
    # ---------- gente pequeña ----------
    for j, a in enumerate(WALK_T):
        if not (a <= t < thad + 0.3): continue
        fade = 1 - seg(t, thad - 0.3, thad + 0.3)
        # izquierda: llega a la rama y tropieza
        x = -30 + SPD * (t - a); hitL = a + (BL - 125 + 30) / SPD
        if t < hitL:
            Z.mini_figure(d, x, Z.walk_pose((t - a) * 9), 0.5, alpha=200 * fade * seg(t, a, a + 0.3))
        else:
            kf = seg(t, hitL, hitL + 0.45)
            al = 200 * fade * (1 - seg(t, hitL + 0.9, hitL + 1.3))
            if al > 0: Z.mini_figure(d, BL - 125 + 25 * kf, P["stand"], 0.5, rot=1.45 * kf, alpha=al)
            if hitL < t < hitL + 0.5: g.ellipse([BL - 175, GY - 80, BL - 75, GY + 20], fill=(230, 80, 70, int(170 * (1 - seg(t, hitL, hitL + 0.5)))))
        # derecha: pasa sin problema por el camino limpio
        x = 560 + SPD * (t - a)
        if x < 1110 and t > s2 + 2.2:
            Z.mini_figure(d, x, Z.walk_pose((t - a) * 9), 0.5, alpha=220 * fade * seg(t, a, a + 0.4))
    # ---------- figura izquierda: LA DEJA ----------
    if t < s1: lx, lp = 110, P["stand"]
    elif t < s1 + 2.3:
        k = seg(t, s1, s1 + 2.3); lx = lerp(110, 460, k)
        lift = 70 if 150 < lx < 440 else 0
        lp = Z.walk_pose((t - s1) * 7, 1.0, lift)
    elif t < t30: lx, lp = 460, P["stand"]
    else: lx, lp = 460, pose_mix("stand", "sad", seg(t, t30, t30 + 1.2))
    figure(d, lx, lp, alpha=int(255 * (1 - 0.35 * gris)))
    # ---------- figura derecha: LA QUITA ----------
    a, b, c, e, f = s2, s2 + 0.8, s2 + 1.4, s2 + 2.0, s2 + 2.8   # andar, agacharse, levantar, lanzar, cae
    rx = 590
    if t < a: rp = P["stand"]
    elif t < b: rx = lerp(590, 690, seg(t, a, b)); rp = Z.walk_pose((t - a) * 7, 0.7)
    elif t < c: rx = 690; rp = pose_mix("stand", "hug", seg(t, b, b + 0.4))
    elif t < e: rx = 690; rp = pose_mix("hug", "joy", seg(t, c, c + 0.45))
    elif t < t30 + 1.6: rx = 690; rp = pose_mix("joy", "stand", seg(t, e, e + 0.5))
    else: rx = 690; rp = pose_mix("stand", "joy", seg(t, t30 + 1.6, t30 + 2.2) * (1 - seg(t, thad + 2.5, thad + 3.2)))
    # la rama: en el suelo → en las manos → vuela → se hunde en la tierra y se vuelve semilla de luz
    if t < c: Z.rama(d, BR, GY - 14, 0.05, k=1.5)
    elif t < e:
        k = seg(t, c, c + 0.45); Z.rama(d, lerp(BR, rx, k), lerp(GY - 14, GY - 360, k), 0.05, k=1.5)
    elif t < f:
        k = seg(t, e, f); x = lerp(rx, SEED, k); y = lerp(GY - 360, GY + 30, k) - 160 * math.sin(math.pi * k)
        Z.rama(d, x, y, 0.05 + 3.5 * k, alpha=255 * (1 - seg(t, f - 0.25, f)), k=1.5 * (1 - 0.5 * k))
    if f - 0.2 < t < f + 0.8: g.ellipse([SEED - 70, GY - 40, SEED + 70, GY + 80], fill=(120, 240, 235, int(200 * (1 - seg(t, f, f + 0.8)))))
    figure(d, rx, rp)
    if t > t30 + 1.5: g.ellipse([rx - 120, GY - 380, rx + 120, GY + 20], fill=(80, 230, 225, int(60 * seg(t, t30 + 1.5, t30 + 3))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "LA DEJA", "LA QUITA", t10, t30, 48)
    Z.subs(d, t, [(0.6, s1 - 0.2, "LA MISMA RAMA"), (s1, s2 - 0.2, "UNO PASA POR ENCIMA"), (s2, t10 - 0.1, "EL OTRO LA QUITA")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN GANA MÁS?")
    Z.fuente(d, t, thad, tfin, ["«QUITÓ UNA RAMA", "DEL CAMINO, Y ALLAH", "LE PERDONÓ»"], "SAHIH AL-BUJARI 2472")
    Z.final(d, t, tfin, "LO PEQUEÑO.", "ALLAH LO VE.", task, "¿QUÉ COSA PEQUEÑA", "HAS HECHO HOY?")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
