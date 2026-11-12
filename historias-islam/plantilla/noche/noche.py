# Estilo "noche": figuras de palitos, cielo estrellado, estrella de 8 puntas, suelo con capas.
# Ejemplo: TACAÑO vs GENEROSO (Sahih Muslim 2588). Uso: python3 noche.py salida_sin_audio.mp4
import math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 28.6
S = 2                      # supermuestreo
GY = 1180                  # línea del suelo
LX, RX = 280, 760          # personajes
CREAM = (232, 228, 214)
GOLD = (235, 210, 140)
TEAL = (40, 200, 205)
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
random.seed(7); np.random.seed(7)

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, k): return a + (b - a) * k

# ---------- fondo (dos versiones: oscuro y "amanecer turquesa") ----------
def make_bg(bright):
    y = np.linspace(0, 1, GY)[:, None]
    top = np.array([4, 8, 12.0]); mid = np.array([8, 26, 34.0]) * (1 + 1.6 * bright)
    hor = np.array([12, 40, 48.0]) + np.array([20, 150, 155.0]) * bright
    sky = np.where(y < 0.55, top + (mid - top) * (y / 0.55), mid + (hor - mid) * np.clip((y - 0.55) / 0.45, 0, 1) ** 1.4)
    sky = np.repeat(sky[:, None, :], W, axis=1).reshape(GY, W, 3)
    # halo de la estrella
    yy, xx = np.mgrid[0:GY, 0:W]
    d = np.sqrt((xx - W / 2) ** 2 + ((yy - 190) * 1.0) ** 2)
    sky += (np.exp(-(d / (260 + 120 * bright)) ** 2) * (60 + 60 * bright))[..., None] * np.array([0.35, 0.9, 0.9])
    ground = np.full((H - GY, W, 3), [9, 10, 12.0])
    ground += np.random.normal(0, 3, ground.shape)
    img = np.clip(np.concatenate([sky, ground]), 0, 255).astype(np.uint8)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    for _ in range(900):     # polvo en la tierra
        x, yv = random.randrange(W), random.randrange(GY + 5, H); c = random.randint(30, 60)
        d.point((x, yv), fill=(c, c, c + 4))
    for i, base in enumerate([1290, 1420, 1560, 1700, 1840]):   # capas onduladas
        pts = [(x, base + 9 * math.sin(x / 140 + i * 1.7) + 5 * math.sin(x / 47 + i)) for x in range(0, W + 10, 10)]
        d.line(pts, fill=(38, 40, 44), width=2)
    return np.asarray(im).astype(np.float32)

BG0, BG1 = make_bg(0.0), make_bg(1.0)
STARS = [(random.randrange(W), random.randrange(20, GY - 120), random.choice([1, 1, 2, 2, 3]), random.random() * 6.28) for _ in range(140)]

# ---------- raíces (árbol ramificado precalculado) ----------
def make_roots(x0, y0):
    segs = []
    def grow(x, y, ang, length, depth, t0):
        if depth > 5 or length < 18: return
        n = 5
        px, py = x, y
        for k in range(n):
            ang += random.uniform(-0.25, 0.25)
            nx, ny = px + math.cos(ang) * length / n, py + math.sin(ang) * length / n
            segs.append((px, py, nx, ny, t0 + k / n * 0.18, max(1.5, 7 - depth * 1.3)))
            px, py = nx, ny
            if k in (1, 3) and random.random() < 0.85:
                grow(px, py, ang + random.choice([-1, 1]) * random.uniform(0.6, 1.1), length * 0.55, depth + 1, t0 + (k + 1) / n * 0.18)
    grow(x0, y0, math.pi / 2, 330, 0, 0.0)
    grow(x0, y0, math.pi / 2 + 0.5, 200, 1, 0.12)
    grow(x0, y0, math.pi / 2 - 0.6, 180, 1, 0.15)
    m = max(s[4] for s in segs) + 0.18
    return [(a, b, c, d, t / m, w) for a, b, c, d, t, w in segs]
ROOTS = make_roots(880, GY + 18)

# ---------- poses de la figura (coordenadas relativas a los pies) ----------
P = {
 "stand": dict(head=(0, -300), neck=(0, -262), hip=(0, -130), le=(-26, -212), lh=(-32, -150), re=(26, -212), rh=(32, -150), lk=(-14, -64), lf=(-30, 0), rk=(14, -64), rf=(30, 0)),
 "give":  dict(head=(6, -300), neck=(4, -262), hip=(0, -130), le=(-26, -212), lh=(-32, -150), re=(60, -235), rh=(118, -228), lk=(-14, -64), lf=(-30, 0), rk=(14, -64), rf=(30, 0)),
 "hug":   dict(head=(30, -178), neck=(22, -142), hip=(-24, -26), le=(10, -100), lh=(70, -96), re=(40, -112), rh=(84, -84), lk=(40, -86), lf=(64, 0), rk=(52, -80), rf=(78, 0)),
 "sad":   dict(head=(36, -150), neck=(26, -118), hip=(-24, -22), le=(22, -76), lh=(70, -84), re=(46, -88), rh=(86, -70), lk=(44, -80), lf=(66, 0), rk=(56, -74), rf=(80, 0)),
 "joy":   dict(head=(0, -304), neck=(0, -266), hip=(0, -132), le=(-48, -296), lh=(-78, -352), re=(48, -296), rh=(78, -352), lk=(-14, -64), lf=(-30, 0), rk=(14, -64), rf=(30, 0)),
}
def pose_mix(a, b, k): return {j: (lerp(P[a][j][0], P[b][j][0], k), lerp(P[a][j][1], P[b][j][1], k)) for j in P[a]}

def figure(d, x, p, col=CREAM, alpha=255):
    c = col + (alpha,)
    q = lambda j: ((x + p[j][0]) * S, (GY + p[j][1]) * S)
    w = 13 * S
    for a, b in [("neck", "hip"), ("neck", "le"), ("le", "lh"), ("neck", "re"), ("re", "rh"), ("hip", "lk"), ("lk", "lf"), ("hip", "rk"), ("rk", "rf")]:
        d.line([q(a), q(b)], fill=c, width=w)
        for pt in (q(a), q(b)): d.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=c)
    hx, hy = q("head"); r = 34 * S
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=c)

def coin(d, x, y, col=GOLD, alpha=255, r=24):
    d.ellipse([(x - r) * S, (y - r * 0.38) * S, (x + r) * S, (y + r * 0.38) * S], fill=col + (alpha,), outline=(150, 120, 60, alpha), width=2 * S)

def stack(d, x, n, col=GOLD, alpha=255):
    for i in range(n): coin(d, x, GY - 10 - i * 13, col, alpha)

def star8(d, cx, cy, r, ang, alpha=255):
    for off in (0, math.pi / 4):
        pts = [((cx + r * math.cos(ang + off + i * math.pi / 2)) * S, (cy + r * math.sin(ang + off + i * math.pi / 2)) * S) for i in range(4)]
        d.polygon(pts, fill=(222, 216, 196, alpha))
    rr = r * 0.42
    d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], fill=(30, 160, 170, alpha))

def chest(d, x, gray, crack, open_k):
    col = tuple(int(lerp(c, g, gray)) for c, g in zip((214, 186, 120), (95, 95, 98)))
    x0, y0, x1, y1 = x - 58, GY - 74, x + 58, GY
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=8 * S, fill=col + (255,), outline=(70, 55, 30, 255), width=3 * S)
    lid = -open_k * 40
    d.rounded_rectangle([(x0 - 4) * S, (y0 - 26 + lid) * S, (x1 + 4) * S, (y0 + 4 + lid) * S], radius=10 * S, fill=col + (255,), outline=(70, 55, 30, 255), width=3 * S)
    if open_k < 0.3:   # candado
        d.rectangle([(x - 12) * S, (y0 - 4) * S, (x + 12) * S, (y0 + 20) * S], fill=(60, 60, 64, 255))
        d.arc([(x - 9) * S, (y0 - 20) * S, (x + 9) * S, (y0 + 2) * S], 180, 360, fill=(60, 60, 64, 255), width=4 * S)
    if crack > 0:
        pts = [(x0 + 20, y0 + 6), (x0 + 34, y0 + 26), (x0 + 26, y0 + 40), (x0 + 44, y0 + 62)]
        n = 1 + int(crack * 3)
        d.line([(a * S, b * S) for a, b in pts[:n + 1]], fill=(30, 30, 32, 255), width=3 * S)

def canopy(d, cx, cy, k):
    if k <= 0: return
    blobs = [(0, 0, 120), (-90, 30, 80), (95, 25, 85), (-50, -60, 85), (55, -62, 88), (0, 55, 90)]
    for bx, by, br in blobs:
        r = br * k
        d.ellipse([(cx + bx * k - r) * S, (cy + by * k - r) * S, (cx + bx * k + r) * S, (cy + by * k + r) * S], fill=(226, 224, 216, 255))
    rnd = random.Random(3)
    for _ in range(int(70 * k)):
        a, rr = rnd.random() * 6.28, rnd.random() * 150 * k
        px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8
        d.ellipse([(px - 2) * S, (py - 2) * S, (px + 2) * S, (py + 2) * S], fill=(150, 150, 150, 255))

def spaced(d, text, cx, cy, size, alpha=255, bold=True, track=0.32, col=(235, 235, 230)):
    f = ImageFont.truetype(FONT_B if bold else FONT, size * S)
    ws = [d.textlength(ch, font=f) for ch in text]
    total = sum(ws) + track * size * S * (len(text) - 1)
    x = cx * S - total / 2
    for ch, w_ in zip(text, ws):
        d.text((x, cy * S), ch, font=f, fill=col + (int(alpha),), anchor="lm")
        x += w_ + track * size * S

# ---------- línea de tiempo (segundos; cuadra con la voz) ----------
T_DAY10, T_Q, T_DAY30, T_HAD, T_FIN, T_ASK = 9.2, 10.8, 14.6, 16.6, 22.4, 25.4
SUBS = [(0.9, 2.9, "EL MISMO DINERO"), (2.9, 5.8, "UNO LO GUARDA TODO"), (5.8, 9.1, "EL OTRO DA UN POCO")]

def frame(t):
    bright = 0.15 + 0.25 * seg(t, T_DAY10, T_DAY10 + 1.2) + 0.6 * seg(t, T_DAY30, T_DAY30 + 2.5)
    base = BG0 * (1 - bright) + BG1 * bright
    fg = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(fg)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)

    for x, y, r, ph in STARS:   # estrellas que titilan y se desvanecen con la luz
        a = int((150 + 100 * math.sin(t * 2 + ph)) * (1 - 0.8 * bright * (y / GY)))
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(240, 240, 235, max(0, a)))
    star8(d, W / 2, 190, 56, t * 0.15)
    g.ellipse([W / 2 - 70, 120, W / 2 + 70, 260], fill=(60, 220, 220, 120))
    d.line([(0, GY * S), (W * S, GY * S)], fill=(225, 225, 220, 230), width=3 * S)

    # --- IZQUIERDA: TACAÑO ---
    into = seg(t, 3.2, 4.4)
    if t < 2.9: lp = P["stand"]
    elif t < T_DAY30: lp = pose_mix("stand", "hug", seg(t, 2.9, 3.6))
    else: lp = pose_mix("hug", "sad", seg(t, T_DAY30, T_DAY30 + 1.2))
    gray = 0.35 * seg(t, T_DAY10, T_DAY10 + 1) + 0.65 * seg(t, T_DAY30, T_DAY30 + 1.5)
    if t >= 3.0: chest(d, LX + 120, gray, seg(t, T_DAY30 + 0.5, T_DAY30 + 2), 1 - seg(t, 4.4, 4.8) if t < 4.8 else 0)
    for i in range(5):          # monedas entrando en el cofre
        ki = seg(t, 3.2 + i * 0.18, 3.7 + i * 0.18)
        if ki >= 1: continue
        sx, sy = LX + 130, GY - 10 - i * 13
        ex, ey = LX + 120, GY - 90
        cx_, cy_ = lerp(sx, ex, ki), lerp(sy, ey, ki) - 60 * math.sin(math.pi * ki)
        coin(d, cx_, cy_)
    if t < 3.0:
        pass
    fig_alpha = int(255 * (1 - 0.35 * gray))
    figure(d, LX - (0 if t < 2.9 else 40 * seg(t, 2.9, 3.6)), lp, alpha=fig_alpha)

    # --- DERECHA: GENEROSO ---
    if t < 5.8: rp = P["stand"]
    elif t < 8.6:
        k = seg(t, 5.8, 6.2) * (1 - seg(t, 8.2, 8.6)); rp = pose_mix("stand", "give", k)
    elif t < T_DAY30 + 1.8: rp = P["stand"]
    else: rp = pose_mix("stand", "joy", seg(t, T_DAY30 + 1.8, T_DAY30 + 2.4) * (1 - seg(t, T_HAD + 2.5, T_HAD + 3.2)))
    gift = [(6.2, 7.0), (7.3, 8.1)]
    given = sum(1 for a, b in gift if t >= a)
    rained = int(min(6, max(0, (t - (T_DAY30 + 2.2)) / 0.6))) if t > T_DAY30 + 2.2 else 0
    stack(d, RX - 120, 5 - given + rained)
    for a, b in gift:           # moneda que vuela y se planta en la tierra
        if a <= t < b + 0.4:
            k = seg(t, a, b)
            x_ = lerp(RX + 110, 880, k); y_ = lerp(GY - 228, GY + 18, k) - 120 * math.sin(math.pi * k)
            coin(d, x_, y_, r=18)
            g.ellipse([x_ - 40, y_ - 40, x_ + 40, y_ + 40], fill=(250, 220, 140, int(170 * (1 - seg(t, b, b + 0.4)))))
    # raíces bajo tierra
    rg = 0.25 * seg(t, 6.9, 8.5) + 0.25 * seg(t, T_DAY10, T_DAY10 + 1.5) + 0.5 * seg(t, T_DAY30, T_DAY30 + 2.5)
    if t >= 6.9:
        d.ellipse([(880 - 16) * S, (GY + 10) * S, (880 + 16) * S, (GY + 28) * S], fill=CREAM + (255,))
    for x0, y0, x1, y1, tb, w_ in ROOTS:
        if rg > tb:
            k = min(1, (rg - tb) / 0.06)
            d.line([(x0 * S, y0 * S), (lerp(x0, x1, k) * S, lerp(y0, y1, k) * S)], fill=CREAM + (235,), width=int(w_ * S))
    # brote y árbol
    th = 90 * seg(t, T_DAY10 + 0.3, T_DAY10 + 1.5) + 290 * seg(t, T_DAY30, T_DAY30 + 2.2)
    if th > 1:
        d.line([(880 * S, GY * S), (880 * S, (GY - th) * S)], fill=CREAM + (255,), width=int(lerp(6, 16, th / 420) * S))
        if th < 140:
            lk = seg(t, T_DAY10 + 0.8, T_DAY10 + 1.8)
            for sgn in (-1, 1):
                d.ellipse([(880 + sgn * 34 * lk - 26 * lk) * S, (GY - th + 4 - 12 * lk) * S, (880 + sgn * 34 * lk + 26 * lk) * S, (GY - th + 4 + 12 * lk) * S], fill=CREAM + (255,))
        canopy(d, 880, GY - th - 40, seg(t, T_DAY30 + 1.0, T_DAY30 + 2.6))
    if t > T_DAY30 + 2.2:       # monedas de luz que caen del árbol
        for i in range(6):
            a = T_DAY30 + 2.2 + i * 0.6
            if a <= t < a + 0.6:
                k = seg(t, a, a + 0.6)
                x_, y_ = lerp(840 - i * 8, RX - 120, k), lerp(GY - 470, GY - 10 - (5 - 2 + i) * 13, k)
                coin(d, x_, y_, r=20)
                g.ellipse([x_ - 36, y_ - 36, x_ + 36, y_ + 36], fill=(250, 220, 140, 150))
    figure(d, RX, rp)
    if t > T_DAY30 + 1.5:       # aura del generoso
        g.ellipse([RX - 130, GY - 380, RX + 130, GY + 20], fill=(80, 230, 225, int(70 * seg(t, T_DAY30 + 1.5, T_DAY30 + 3))))

    # --- TEXTOS ---
    la = 255 * (1 - seg(t, T_HAD - 0.4, T_HAD))
    if la > 0:
        spaced(d, "TACAÑO", LX, 330, 50, la)
        spaced(d, "GENEROSO", RX, 330, 50, la)
        day = "DÍA 1" if t < T_DAY10 else ("DÍA 10" if t < T_DAY30 else "DÍA 30")
        pulse = 1 + 0.25 * max(0, 1 - abs(t - T_DAY10) * 3) + 0.25 * max(0, 1 - abs(t - T_DAY30) * 3)
        for x_ in (LX, RX): spaced(d, day, x_, 400, int(38 * pulse), la * 0.8, col=(200, 225, 222))
    for a, b, txt in SUBS:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b))
        if al > 0: spaced(d, txt, W / 2, 540, 40, al, bold=False, track=0.22, col=(190, 225, 222))
    if T_Q <= t < T_DAY30:
        al = 255 * seg(t, T_Q, T_Q + 0.3) * (1 - seg(t, T_DAY30 - 0.3, T_DAY30))
        sc = 1 + 0.05 * math.sin((t - T_Q) * 6)
        spaced(d, "¿QUIÉN TIENE MÁS?", W / 2, 560, int(56 * sc), al)
    if T_HAD <= t < T_FIN:
        al = 255 * seg(t, T_HAD, T_HAD + 0.5) * (1 - seg(t, T_FIN - 0.4, T_FIN))
        spaced(d, "«LA CARIDAD", W / 2, 330, 54, al)
        spaced(d, "NO DISMINUYE", W / 2, 405, 54, al * seg(t, T_HAD + 0.8, T_HAD + 1.3))
        spaced(d, "LA RIQUEZA»", W / 2, 480, 54, al * seg(t, T_HAD + 1.8, T_HAD + 2.3))
        spaced(d, "SAHIH MUSLIM 2588", W / 2, 560, 32, al * 0.85 * seg(t, T_HAD + 3, T_HAD + 3.5), bold=False, col=(190, 225, 222))
    if t >= T_FIN:
        al = 255 * seg(t, T_FIN, T_FIN + 0.4)
        spaced(d, "DA.", W / 2, 360, 66, al)
        spaced(d, "NO PIERDES NADA.", W / 2, 440, 54, al * seg(t, T_FIN + 0.5, T_FIN + 0.9))
    if t >= T_ASK:
        al = 255 * seg(t, T_ASK, T_ASK + 0.4)
        spaced(d, "¿Y TÚ,", W / 2, 540, 40, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, "CUÁL DE LOS DOS ERES?", W / 2, 595, 40, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, "COMENTA ↓", W / 2, 1060 - 520, 0, 0) if False else None
        spaced(d, "COMENTA ↓", W / 2, 655, 34, al * (0.6 + 0.4 * math.sin(t * 5)), track=0.25, col=(120, 230, 225))

    fg1 = fg.resize((W, H), Image.LANCZOS)
    # resplandor: blanco suave alrededor de todo lo dibujado + luces
    a = np.asarray(fg1)[..., 3].astype(np.float32)
    halo = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    halo = np.asarray(halo).astype(np.float32)[..., None] / 255 * np.array([90, 200, 200]) * (0.35 + 0.4 * bright)
    gl = glow.filter(ImageFilter.GaussianBlur(28)); ga = np.asarray(gl).astype(np.float32)
    out = base + halo + ga[..., :3] * (ga[..., 3:4] / 255)
    f = np.asarray(fg1).astype(np.float32); fa = f[..., 3:4] / 255
    out = out * (1 - fa) + f[..., :3] * fa
    return np.clip(out, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    if len(sys.argv) > 2:      # modo prueba: guarda fotogramas sueltos
        for tt in sys.argv[2:]:
            Image.fromarray(frame(float(tt))).save(f"f_{tt}.png")
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", sys.argv[1]], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
