# Dos historias en estilo Noche, reutilizando las piezas del motor de ejemplo.
# Uso: python3 historias.py control|gracias salida.mp4   |  python3 historias.py control x 1 5 12 (fotogramas sueltos)
import math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import noche as N
from noche import S, W, H, GY, LX, RX, CREAM, GOLD, seg, ease, lerp, figure, P, pose_mix, star8, canopy, spaced

FPS = N.FPS
HIST = sys.argv[1]

def base_frame(t, bright):
    base = N.BG0 * (1 - bright) + N.BG1 * bright
    fg = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(fg)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    for x, y, r, ph in N.STARS:
        a = int((150 + 100 * math.sin(t * 2 + ph)) * (1 - 0.8 * bright * (y / GY)))
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(240, 240, 235, max(0, a)))
    star8(d, W / 2, 190, 56, t * 0.15)
    g.ellipse([W / 2 - 70, 120, W / 2 + 70, 260], fill=(60, 220, 220, 120))
    d.line([(0, GY * S), (W * S, GY * S)], fill=(225, 225, 220, 230), width=3 * S)
    return base, fg, d, glow, g

def finish(base, fg, glow, bright):
    fg1 = fg.resize((W, H), Image.LANCZOS)
    a = np.asarray(fg1)[..., 3].astype(np.float32)
    halo = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    halo = np.asarray(halo).astype(np.float32)[..., None] / 255 * np.array([90, 200, 200]) * (0.35 + 0.4 * bright)
    gl = glow.filter(ImageFilter.GaussianBlur(28)); ga = np.asarray(gl).astype(np.float32)
    out = base + halo + ga[..., :3] * (ga[..., 3:4] / 255)
    f = np.asarray(fg1).astype(np.float32); fa = f[..., 3:4] / 255
    return np.clip(out * (1 - fa) + f[..., :3] * fa, 0, 255).astype(np.uint8)

def roots_tree(d, t, rg, th, ck, x0=880):
    dx = x0 - 880
    if rg > 0: d.ellipse([(x0 - 16) * S, (GY + 10) * S, (x0 + 16) * S, (GY + 28) * S], fill=CREAM + (255,))
    for a, b, c, e, tb, w_ in N.ROOTS:
        if rg > tb:
            k = min(1, (rg - tb) / 0.06)
            d.line([((a + dx) * S, b * S), ((lerp(a, c, k) + dx) * S, lerp(b, e, k) * S)], fill=CREAM + (235,), width=int(w_ * S))
    if th > 1:
        d.line([(x0 * S, GY * S), (x0 * S, (GY - th) * S)], fill=CREAM + (255,), width=int(lerp(6, 16, th / 420) * S))
        canopy(d, x0, GY - th - 40, ck)

def spike(d, x, y, r, alpha=255, rot=0.0, col=(30, 32, 40)):
    pts = []
    for i in range(16):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 8
        pts.append(((x + rr * math.cos(a)) * S, (y + rr * math.sin(a)) * S))
    d.polygon(pts, fill=col + (int(alpha),), outline=(170, 40, 40, int(alpha)), width=2 * S)

def labels(d, t, la, l1, l2, t10, t30, size=46):
    spaced(d, l1, LX, 330, size, la); spaced(d, l2, RX, 330, size, la)
    day = "DÍA 1" if t < t10 else ("DÍA 10" if t < t30 else "DÍA 30")
    pulse = 1 + 0.25 * max(0, 1 - abs(t - t10) * 3) + 0.25 * max(0, 1 - abs(t - t30) * 3)
    for x_ in (LX, RX): spaced(d, day, x_, 400, int(38 * pulse), la * 0.8, col=(200, 225, 222))

def subs(d, t, lst, y=540):
    for a, b, txt in lst:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b))
        if al > 0: spaced(d, txt, W / 2, y, 40, al, bold=False, track=0.22, col=(190, 225, 222))

def pregunta(d, t, a, b, txt):
    if a <= t < b:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b)); sc = 1 + 0.05 * math.sin((t - a) * 6)
        spaced(d, txt, W / 2, 560, int(52 * sc), al)

def fuente(d, t, a, b, lineas, ref):
    if a <= t < b:
        al = 255 * seg(t, a, a + 0.5) * (1 - seg(t, b - 0.4, b))
        for i, ln in enumerate(lineas):
            spaced(d, ln, W / 2, 330 + 70 * i, 50, al * seg(t, a + 0.7 * i, a + 0.7 * i + 0.5))
        spaced(d, ref, W / 2, 330 + 70 * len(lineas) + 20, 32, al * 0.85 * seg(t, a + 2.6, a + 3.1), bold=False, col=(190, 225, 222))

def final(d, t, a, l1, l2, ask_t, ask1, ask2):
    if t >= a:
        al = 255 * seg(t, a, a + 0.4)
        spaced(d, l1, W / 2, 360, 62, al); spaced(d, l2, W / 2, 440, 50, al * seg(t, a + 0.5, a + 0.9))
    if t >= ask_t:
        al = 255 * seg(t, ask_t, ask_t + 0.4)
        spaced(d, ask1, W / 2, 540, 40, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, ask2, W / 2, 595, 40, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, "COMENTA ↓", W / 2, 655, 34, al * (0.6 + 0.4 * math.sin(t * 5)), track=0.25, col=(120, 230, 225))

# ======================= HISTORIA 1: RESPONDE vs SE CONTROLA =======================
C = dict(lines=["Dos personas. El mismo insulto.", "Uno responde con otro peor.", "El otro respira, y se calla.",
                "Día diez.", "¿Quién crees que es más fuerte?", "Día treinta.",
                "El Profeta, la paz sea con él, dijo: el fuerte no es el que vence a los demás, sino el que se controla cuando se enfada.",
                "Contrólate. Eso es fuerza.", "¿Y tú, cuál de los dos eres?"])
def frame_control(t, T):
    t10, tq, t30, thad, tfin, task = T["t10"], T["tq"], T["t30"], T["thad"], T["tfin"], T["task"]
    bright = 0.15 + 0.25 * seg(t, t10, t10 + 1.2) + 0.6 * seg(t, t30, t30 + 2.5)
    base, fg, d, glow, g = base_frame(t, bright)
    # insultos que llegan desde arriba (t 0.6 - 1.8)
    for k, (tx, x0) in enumerate(((LX, 140), (RX, 940))):
        kk = seg(t, 0.5, 1.7)
        if kk < 1 and t > 0.3:
            x = lerp(x0, tx + (40 if k == 0 else -40), kk); y = lerp(620, GY - 300, kk)
            spike(d, x, y, 34, 255, t * 3)
        elif k == 1 and t < 3.0:                         # al de la derecha se le deshace
            a = 255 * (1 - seg(t, 1.7, 3.0))
            for i in range(8):
                ang = i * math.pi / 4; rr = 20 + 60 * seg(t, 1.7, 3.0)
                d.ellipse([(RX - 40 + rr * math.cos(ang) - 5) * S, (GY - 300 + rr * math.sin(ang) - 5) * S,
                           (RX - 40 + rr * math.cos(ang) + 5) * S, (GY - 300 + rr * math.sin(ang) + 5) * S], fill=(40, 40, 46, int(a)))
    # el de la izquierda devuelve uno más grande (2.6 - 3.8)
    kk = seg(t, 2.6, 3.8)
    if 0 < kk < 1: spike(d, lerp(LX + 60, -60, kk), lerp(GY - 300, 560, kk), 48, 255, -t * 4)
    # nube de tormenta y grietas a la izquierda
    nube = 0.35 * seg(t, 3.4, 5) + 0.3 * seg(t, t10, t10 + 1.2) + 0.35 * seg(t, t30, t30 + 2)
    if nube > 0:
        cx, cy = LX, 690
        for bx, by, br in [(0, 0, 90), (-80, 20, 65), (80, 15, 70), (-40, -40, 70), (45, -45, 72)]:
            r = br * nube
            d.ellipse([(cx + bx * nube - r) * S, (cy + by * nube - r) * S, (cx + bx * nube + r) * S, (cy + by * nube + r) * S], fill=(58, 62, 74, 255))
        if nube > 0.5 and (int(t * 3) % 4 == 0):            # rayo
            d.line([(cx * S, (cy + 60) * S), ((cx - 20) * S, (cy + 120) * S), ((cx + 10) * S, (cy + 140) * S), ((cx - 15) * S, (cy + 210) * S)], fill=(255, 230, 120, 230), width=5 * S)
            g.ellipse([cx - 90, cy, cx + 90, cy + 200], fill=(255, 220, 120, 90))
        for i in range(int(6 * nube)):                     # gotas
            ph = (t * 1.3 + i * 0.37) % 1
            x = cx - 70 + i * 28; y = cy + 70 + ph * 260
            d.line([(x * S, y * S), (x * S, (y + 18) * S)], fill=(140, 160, 190, 200), width=3 * S)
    cr = 0.4 * seg(t, t10, t10 + 1.5) + 0.6 * seg(t, t30, t30 + 2.5)
    if cr > 0:                                            # grietas bajo el de la izquierda
        rnd = random.Random(5)
        for j in range(5):
            x, y = LX + rnd.uniform(-40, 40), GY + 4
            pts = [(x, y)]
            n = int(1 + 6 * cr)
            for _ in range(n):
                x += rnd.uniform(-40, 40); y += rnd.uniform(25, 60); pts.append((x, y))
            d.line([(a * S, b * S) for a, b in pts], fill=(150, 50, 45, 230), width=4 * S)
    # izquierda: pose
    if t < 2.6: lp = P["stand"]
    elif t < 3.8: lp = pose_mix("stand", "give", 1)       # lanza
    elif t < t30: lp = pose_mix("stand", "hug", seg(t, t10 - 1, t10))
    else: lp = pose_mix("hug", "sad", seg(t, t30, t30 + 1.2))
    if 2.6 <= t < 3.8:
        lp = {j: (-v[0], v[1]) if j in ("re", "rh") else v for j, v in P["give"].items()}
    figure(d, LX, lp, alpha=int(255 * (1 - 0.35 * seg(t, t30, t30 + 1.5))))
    # derecha: respira (anillo), raíces y árbol
    if 2.4 <= t < 5.4:
        for k in range(2):
            ph = ((t - 2.4) * 0.7 + k * 0.5) % 1
            r = 40 + 120 * ph
            d.ellipse([(RX - r) * S, (GY - 160 - r) * S, (RX + r) * S, (GY - 160 + r) * S], outline=(120, 230, 225, int(200 * (1 - ph))), width=3 * S)
    rg = 0.25 * seg(t, 3.0, 5.2) + 0.25 * seg(t, t10, t10 + 1.5) + 0.5 * seg(t, t30, t30 + 2.5)
    th = 90 * seg(t, t10 + 0.3, t10 + 1.5) + 290 * seg(t, t30, t30 + 2.2)
    roots_tree(d, t, rg, th, seg(t, t30 + 1.0, t30 + 2.6))
    rp = pose_mix("stand", "joy", seg(t, t30 + 1.8, t30 + 2.4) * (1 - seg(t, thad + 2.5, thad + 3.2))) if t > t30 else P["stand"]
    figure(d, RX, rp)
    if t > t30 + 1.5: g.ellipse([RX - 130, GY - 380, RX + 130, GY + 20], fill=(80, 230, 225, int(70 * seg(t, t30 + 1.5, t30 + 3))))
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: labels(d, t, la, "RESPONDE", "SE CONTROLA", t10, t30, 42)
    subs(d, t, [(0.6, T["s"][1] - 0.2, "EL MISMO INSULTO"), (T["s"][1], T["s"][2] - 0.2, "UNO RESPONDE"), (T["s"][2], t10 - 0.1, "EL OTRO SE CALLA")])
    pregunta(d, t, tq, t30, "¿QUIÉN ES MÁS FUERTE?")
    fuente(d, t, thad, tfin, ["«EL FUERTE ES", "EL QUE SE CONTROLA", "CUANDO SE ENFADA»"], "SAHIH AL-BUJARI 6114")
    final(d, t, tfin, "CONTRÓLATE.", "ESO ES FUERZA.", task, "¿Y TÚ,", "CUÁL DE LOS DOS ERES?")
    return finish(base, fg, glow, bright)

# ======================= HISTORIA 2: SE QUEJA vs AGRADECE =======================
G = dict(lines=["Dos personas. La misma vida.", "Uno se queja de todo.", "El otro dice: alhamdulillah.",
                "Día diez.", "¿Quién crees que tiene más?", "Día treinta.",
                "Allah dice en el Corán: si sois agradecidos, os daré más.",
                "Da las gracias. Y mira lo que llega.", "¿Y tú, cuál de los dos eres?"])
def jarra(d, x, nivel, grieta, alpha=255, col=(120, 235, 228)):
    x0, x1, y0, y1 = x - 55, x + 55, GY - 170, GY
    if nivel > 0:
        top = y1 - (y1 - y0 - 8) * min(1, nivel)
        d.rectangle([(x0 + 6) * S, top * S, (x1 - 6) * S, (y1 - 5) * S], fill=col + (int(alpha * 0.9),))
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], 14 * S, outline=CREAM + (alpha,), width=5 * S)
    d.rectangle([(x0 - 8) * S, (y0 - 8) * S, (x1 + 8) * S, (y0 + 2) * S], fill=CREAM + (alpha,))
    if grieta > 0:
        pts = [(x0 + 18, y1 - 30), (x0 + 30, y1 - 55), (x0 + 22, y1 - 80), (x0 + 38, y1 - 110)]
        n = 1 + int(grieta * 3)
        d.line([(a * S, b * S) for a, b in pts[:n + 1]], fill=(40, 40, 46, 255), width=4 * S)
def gota(d, g, x, y, r=9, col=(140, 245, 238)):
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=col + (255,)); g.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (120,))
def frame_gracias(t, T):
    t10, tq, t30, thad, tfin, task = T["t10"], T["tq"], T["t30"], T["thad"], T["tfin"], T["task"]
    bright = 0.15 + 0.25 * seg(t, t10, t10 + 1.2) + 0.6 * seg(t, t30, t30 + 2.5)
    base, fg, d, glow, g = base_frame(t, bright)
    JL, JR = LX + 130, RX - 130
    # gotas de luz que caen de la estrella en las dos jarras, cada 1,4 s
    k = 0; tt = 0.6
    while tt < min(t, thad):
        for jx in (JL, JR):
            ph = (t - tt) / 1.6
            if 0 <= ph < 1: gota(d, g, lerp(W / 2, jx, ph), lerp(250, GY - 150, ph ** 1.5))
        tt += 1.4; k += 1
    llegadas = sum(1 for i in range(40) if 0.6 + i * 1.4 + 1.6 <= min(t, thad + 1.6))
    nivel_l = min(0.25, 0.06 * llegadas) * (1 - 0.6 * seg(t, t30, t30 + 2)) if t > 2.8 else min(0.25, 0.06 * llegadas)
    nivel_r = min(1.15, 0.05 * llegadas + 0.25 * seg(t, t10, t10 + 1) + 0.6 * seg(t, t30, t30 + 2))
    gris = 0.35 * seg(t, t10, t10 + 1) + 0.65 * seg(t, t30, t30 + 1.5)
    jarra(d, JL, nivel_l, seg(t, 3.0, 4.2), alpha=255, col=tuple(int(lerp(c, 90, gris)) for c in (120, 235, 228)))
    if t > 3.4 and nivel_l > 0.02:                          # se escapa por la grieta
        for i in range(3):
            ph = (t * 1.5 + i * 0.33) % 1
            d.ellipse([(JL - 37 - 4) * S, (GY - 30 + ph * 26 - 4) * S, (JL - 37 + 4) * S, (GY - 30 + ph * 26 + 4) * S], fill=(110, 200, 196, int(200 * (1 - ph))))
    roots_tree(d, t, 0.25 * seg(t, 5.0, 7.0) + 0.25 * seg(t, t10, t10 + 1.5) + 0.5 * seg(t, t30, t30 + 2.5), 0, 0, x0=JR)
    jarra(d, JR, min(1, nivel_r), 0)
    if nivel_r > 1.0:                                       # rebosa: cascada de luz y flores
        for i in range(6):
            ph = (t * 1.2 + i / 6) % 1
            for sx in (-1, 1): gota(d, g, JR + sx * (60 + 30 * ph), GY - 175 + ph * 170, 6)
        fl = seg(t, t30 + 1.0, t30 + 3.0)
        for i, fx in enumerate((RX - 260, RX - 210, RX + 70, RX + 120, RX + 170, RX - 300)):
            h = 70 * min(1, fl * 1.5 - i * 0.08)
            if h > 2:
                d.line([(fx * S, GY * S), (fx * S, (GY - h) * S)], fill=(150, 230, 170, 255), width=4 * S)
                for a in range(5):
                    ang = a * 2 * math.pi / 5
                    d.ellipse([(fx + 11 * math.cos(ang) - 8) * S, (GY - h + 11 * math.sin(ang) - 8) * S, (fx + 11 * math.cos(ang) + 8) * S, (GY - h + 11 * math.sin(ang) + 8) * S], fill=(255, 245, 230, 255))
                d.ellipse([(fx - 6) * S, (GY - h - 6) * S, (fx + 6) * S, (GY - h + 6) * S], fill=GOLD + (255,))
    # bocadillos: quejas (garabatos grises) y gracias (corazones turquesa)
    for i in range(3):
        a0 = 2.0 + i * 1.1 + (0 if t < t10 else 0)
        for rep in range(4):
            tb = a0 + rep * 6.5
            if tb <= t < tb + 1.4 and t < thad:
                ph = (t - tb) / 1.4
                y = GY - 330 - 120 * ph; al = int(255 * (1 - ph))
                x = LX - 30 + i * 25
                d.rounded_rectangle([(x - 40) * S, (y - 26) * S, (x + 40) * S, (y + 26) * S], 18 * S, fill=(70, 74, 86, al))
                d.line([((x - 25 + j * 10) * S, (y + (8 if j % 2 else -8)) * S) for j in range(6)], fill=(200, 200, 205, al), width=3 * S)
                x = RX - 10 + i * 20
                cx, cy, r = x, y, 13
                d.ellipse([(cx - r - 9) * S, (cy - r) * S, (cx - 9 + r) * S, (cy + r) * S], fill=(110, 235, 225, al))
                d.ellipse([(cx + 9 - r) * S, (cy - r) * S, (cx + 9 + r) * S, (cy + r) * S], fill=(110, 235, 225, al))
                d.polygon([((cx - 23) * S, (cy + 4) * S), ((cx + 23) * S, (cy + 4) * S), (cx * S, (cy + 30) * S)], fill=(110, 235, 225, al))
    lp = P["stand"] if t < t10 else pose_mix("stand", "hug" if t < t30 else "sad", seg(t, t10, t10 + 1) if t < t30 else seg(t, t30, t30 + 1.2))
    figure(d, LX - 40, lp, alpha=int(255 * (1 - 0.35 * gris)))
    rp = pose_mix("stand", "joy", seg(t, t30 + 1.8, t30 + 2.4) * (1 - seg(t, thad + 2.5, thad + 3.2))) if t > t30 else P["stand"]
    figure(d, RX + 40, rp)
    if t > t30 + 1.5: g.ellipse([RX - 90, GY - 380, RX + 170, GY + 20], fill=(80, 230, 225, int(70 * seg(t, t30 + 1.5, t30 + 3))))
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: labels(d, t, la, "SE QUEJA", "AGRADECE", t10, t30, 46)
    subs(d, t, [(0.6, T["s"][1] - 0.2, "LA MISMA VIDA"), (T["s"][1], T["s"][2] - 0.2, "UNO SE QUEJA"), (T["s"][2], t10 - 0.1, "EL OTRO DA LAS GRACIAS")])
    pregunta(d, t, tq, t30, "¿QUIÉN TIENE MÁS?")
    fuente(d, t, thad, tfin, ["«SI SOIS", "AGRADECIDOS,", "OS DARÉ MÁS»"], "CORÁN 14:7")
    final(d, t, tfin, "DA LAS GRACIAS.", "Y MIRA LO QUE LLEGA.", task, "¿Y TÚ,", "CUÁL DE LOS DOS ERES?")
    return finish(base, fg, glow, bright)

# ======================= voz + tiempos =======================
def voz(lines, pausas):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro('/home/claude/kok/kokoro-v1.0.onnx', '/home/claude/kok/voices-v1.0.bin')
    sr = 24000; clips = []
    for ln in lines:
        a, sr = k.create(ln, voice='em_alex', speed=1.0, lang='es')
        idx = np.where(np.abs(a) > 0.01)[0]; clips.append(a[max(0, idx[0] - 240): idx[-1] + 480])
    starts, t = [], 0.3
    for c, p in zip(clips, pausas): starts.append(t); t += len(c) / sr + p
    dur = round(t + 0.6, 2)
    out = np.zeros(int(sr * dur), np.float32)
    for c, s in zip(clips, starts): out[int(s * sr): int(s * sr) + len(c)] += c
    def tone(t0, f, d_, v):
        n = int(d_ * sr); x = np.arange(n) / sr
        w = v * np.sin(2 * np.pi * f * x) * np.exp(-x * 3.5) + v * 0.4 * np.sin(4 * np.pi * f * x) * np.exp(-x * 5)
        i = int(t0 * sr); out[i:i + n] += w[:len(out) - i]
    tone(starts[5], 660, 2.0, 0.08); tone(starts[5] + 0.15, 990, 2.0, 0.06)
    sf.write(f"/home/claude/ej/{HIST}.wav", np.clip(out, -1, 1), sr)
    return starts, dur

H_ = C if HIST == "control" else G
fr_fn = frame_control if HIST == "control" else frame_gracias
pausas = [0.7, 0.7, 1.0, 0.7, 2.2, 0.8, 1.0, 1.0, 1.4]
starts, DUR = voz(H_["lines"], pausas)
T = dict(s=starts, t10=starts[3], tq=starts[4], t30=starts[5], thad=starts[6], tfin=starts[7], task=starts[8])
print("DUR", DUR, [round(s, 1) for s in starts])
if len(sys.argv) > 3:
    for tt in sys.argv[3:]: Image.fromarray(fr_fn(float(tt), T)).save(f"/home/claude/ej/{HIST}_{tt}.png")
    sys.exit()
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-i", f"/home/claude/ej/{HIST}.wav", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                      "-c:a", "aac", "-b:a", "128k", "-shortest", sys.argv[2]], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)): p.stdin.write(fr_fn(i / FPS, T).tobytes())
p.stdin.close(); p.wait(); print("OK", sys.argv[2])
