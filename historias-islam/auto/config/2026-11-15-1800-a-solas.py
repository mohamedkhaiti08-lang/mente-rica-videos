# Estilo Noche · DOS CARAS vs UNA CARA · "cuando nadie te ve" (Sunan Ibn Majah 4245)
# Variante "lo que ves vs lo que Allah ve": los dos levantan la misma montaña de buenas obras delante de la gente.
# A solas, uno hace lo que esconde (pantalla roja) y su montaña se agrieta por debajo; el otro se postra.
# Día 30: la montaña del de dos caras se deshace en polvo; la del sincero se ilumina.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-15-1800-a-solas.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Delante de todos, los dos son buenos.",
         "Pero cuando se quedan solos...",
         "Uno hace lo que delante nunca haría.",
         "El otro sigue igual, aunque nadie le vea.",
         "Día diez.",
         "¿Qué montaña crees que aguanta?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo que algunos vendrán con obras como montañas, y Allah las hará polvo. Porque a solas, hacían lo que Allah prohibió.",
         "Nadie te ve. Allah, sí.",
         "¿Eres el mismo cuando nadie te ve?"]
PAUSAS = [0.5, 0.6, 0.7, 0.7, 0.5, 2.2, 0.6, 0.8, 0.9, 1.6]
def SFX(s): return [dict(t=s[3] + 0.5, f=1320, dur=0.8, v=0.06), dict(t=s[6], f=660, dur=2.0, v=0.08), dict(t=s[6] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-15-1800-a-solas.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, s2, s3, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts)

FL, ML, FR, MR = 135, 345, 662, 862          # figura y montaña (izquierda / derecha)
BW, BH = 50, 36                              # bloque
ROWS = [5, 4, 3, 2, 1]
BLOCKS = [(r, c) for r, n in enumerate(ROWS) for c in range(n)]   # 15 bloques, de abajo arriba
def bpos(mx, r, c):
    n = ROWS[r]; x = mx + (c - (n - 1) / 2) * (BW + 4); y = GY - BH / 2 - 2 - r * (BH + 3)
    return x, y
AUD = [30, 70, 505, 540, 575]           # público (gente pequeña)
rnd = random.Random(9)
DUST = [[(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.6, 1.4), rnd.uniform(0, 6.28)) for _ in range(10)] for _ in BLOCKS]
SUJUD = dict(head=(136, -34), neck=(100, -62), hip=(-10, -120), le=(110, -30), lh=(90, -6), re=(116, -32), rh=(96, -6),
             lk=(0, -8), lf=(-80, -6), rk=(8, -8), rf=(-72, -6))
def to_sujud(k): return {j: (lerp(P["stand"][j][0], -SUJUD[j][0], k), lerp(P["stand"][j][1], SUJUD[j][1], k)) for j in SUJUD}
PHONE = dict(P["stand"]); PHONE.update(re=(34, -200), rh=(30, -262), head=(-4, -298))

def block(d, g, x, y, k, col, alpha, glow_col=None, crack=0.0):
    if k <= 0 or alpha <= 0: return
    w, h = BW * k / 2, BH * k / 2
    d.rounded_rectangle([(x - w) * S, (y - h) * S, (x + w) * S, (y + h) * S], radius=5 * S, fill=col + (int(alpha),))
    if crack > 0:
        d.line([((x - 8) * S, (y - h) * S), ((x + 2) * S, (y - 2) * S), ((x - 4) * S, (y + h * crack) * S)], fill=(40, 40, 46, int(alpha)), width=2 * S)
    if glow_col: g.ellipse([x - 30, y - 26, x + 30, y + 26], fill=glow_col + (int(90 * alpha / 255),))

def frame(t):
    bright = 0.18 - 0.12 * seg(t, s1, s1 + 1.0) + 0.12 * seg(t, t10, t10 + 1.0) + 0.8 * seg(t, t30 + 0.6, t30 + 3.0)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    built = 15 * seg(t, 0.15, t10 - 0.3)                 # los dos levantan la misma montaña
    gris = seg(t, s2 + 0.3, s2 + 1.5) * 0.55
    # ---------- lo que no se ve: raíces (derecha) y grietas (izquierda) ----------
    Z.roots(d, 0.35 * seg(t, s3 + 0.3, s3 + 2.0) + 0.2 * seg(t, t10, t10 + 1.2) + 0.45 * seg(t, t30 + 0.5, t30 + 2.5), x0=MR)
    Z.grietas(d, ML, 0.35 * seg(t, s2 + 0.4, s2 + 2.0) + 0.25 * seg(t, t10, t10 + 1.2) + 0.4 * seg(t, t30, t30 + 1.2), seed=8)
    # ---------- montañas ----------
    for i, (r, c) in enumerate(BLOCKS):
        kb = max(0.0, min(1.0, built - i))
        pop = 1 + 0.25 * math.sin(math.pi * kb) if kb < 1 else 1.0
        # derecha: crema → turquesa brillante al final
        x, y = bpos(MR, r, c)
        lum = seg(t, t30 + 0.6 + 0.08 * i, t30 + 1.4 + 0.08 * i)
        colR = tuple(int(lerp(a, b, lum)) for a, b in zip(CREAM, (150, 245, 238)))
        block(d, g, x, y, kb * pop, colR, 255, glow_col=(120, 240, 232) if lum > 0 else (GOLD if kb < 1 else None))
        # izquierda: igual por fuera; a solas se agrieta; el día 30 se deshace en polvo
        x, y = bpos(ML, r, c)
        td = t30 + 0.2 + 0.12 * (14 - i)                # se deshace de arriba abajo
        colL = tuple(int(lerp(a, b, gris)) for a, b in zip(CREAM, (120, 118, 124)))
        if t < td:
            block(d, g, x, y, kb * pop, colL, 255 - 60 * gris, glow_col=GOLD if 0 < kb < 1 else None, crack=seg(t, s2 + 0.5 + 0.1 * i, s2 + 1.6 + 0.1 * i))
        else:
            kd = seg(t, td, td + 2.4)
            for dx, dy, sz, ph in DUST[i]:
                px = x + dx * 26 - 260 * kd * (0.6 + 0.4 * sz) + 18 * math.sin(t * 3 + ph)
                py = y + dy * 14 - 300 * kd * sz - 40 * math.sin(kd * 3 + ph)
                rr = 5 * sz * (1 - 0.5 * kd)
                d.ellipse([(px - rr) * S, (py - rr) * S, (px + rr) * S, (py + rr) * S], fill=colL + (int(220 * (1 - kd)),))
    if t30 + 1.0 < t: g.rectangle([MR - 140, GY - 230, MR + 140, GY], fill=(90, 235, 228, int(70 * seg(t, t30 + 1.0, t30 + 2.5))))
    for i in range(int(12 * seg(t, t30 + 1.4, t30 + 4.0))):           # luz que sube de la montaña buena
        ph = (t * 0.35 + i / 12) % 1
        Z.gota(d, g, MR + 90 * math.sin(i * 2.1 + t), GY - 200 - ph * 420, r=5 * (1 - ph) + 2, alpha=230 * (1 - ph))
    # ---------- público: está delante; a solas se va ----------
    aud = 1 - seg(t, s1, s1 + 1.0)
    for j, ax in enumerate(AUD):
        if aud > 0: Z.mini_figure(d, ax, P["stand"] if (int(t * 1.5 + j) % 3) else P["joy"], 0.36, alpha=170 * aud)
    # ---------- izquierda: DOS CARAS ----------
    if t < s2: lp = P["stand"]
    elif t < t30: lp = pose_mix("stand", "stand", 0) if False else {j: (lerp(P["stand"][j][0], PHONE[j][0], seg(t, s2, s2 + 0.5)), lerp(P["stand"][j][1], PHONE[j][1], seg(t, s2, s2 + 0.5))) for j in PHONE}
    else: lp = pose_mix("stand", "sad", seg(t, t30 + 0.8, t30 + 2.0))
    figure(d, FL, lp, alpha=int(255 * (1 - 0.35 * gris)))
    if s2 + 0.3 < t < t30 + 0.4:                        # pantalla roja escondida
        al = seg(t, s2 + 0.3, s2 + 0.8) * (1 - seg(t, t30, t30 + 0.4))
        hx, hy = FL + 34, GY - 272
        d.rounded_rectangle([(hx - 12) * S, (hy - 20) * S, (hx + 12) * S, (hy + 20) * S], radius=4 * S, fill=(230, 90, 80, int(255 * al)))
        g.ellipse([hx - 70, hy - 70, hx + 70, hy + 70], fill=(230, 70, 60, int(150 * al * (0.75 + 0.25 * math.sin(t * 7)))))
    # ---------- derecha: UNA CARA ----------
    if t < s3: rp = P["stand"]
    elif t < t10: rp = to_sujud(seg(t, s3, s3 + 0.8) * (1 - seg(t, t10 - 0.6, t10)))
    elif t < t30 + 1.6: rp = P["stand"]
    else: rp = pose_mix("stand", "joy", seg(t, t30 + 1.6, t30 + 2.3) * (1 - seg(t, thad + 3.0, thad + 3.8)))
    figure(d, FR, rp)
    if s3 + 0.8 < t < t10: g.ellipse([FR - 160, GY - 120, FR + 40, GY + 20], fill=(90, 235, 228, int(110 * seg(t, s3 + 0.8, s3 + 1.6))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "DOS CARAS", "UNA CARA", t10, t30, 46)
    Z.subs(d, t, [(0.4, s1 - 0.15, "DELANTE DE TODOS"), (s1, s2 - 0.15, "A SOLAS..."), (s2, s3 - 0.15, "UNO HACE LO QUE ESCONDE"), (s3, t10 - 0.1, "EL OTRO SIGUE IGUAL")])
    Z.pregunta(d, t, tq, t30, "¿QUÉ MONTAÑA AGUANTA?")
    Z.fuente(d, t, thad, tfin, ["«OBRAS COMO MONTAÑAS…", "Y ALLAH LAS HARÁ", "POLVO»"], "SUNAN IBN MAJAH 4245")
    Z.final(d, t, tfin, "NADIE TE VE.", "ALLAH, SÍ.", task, "¿ERES EL MISMO", "CUANDO NADIE TE VE?")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
