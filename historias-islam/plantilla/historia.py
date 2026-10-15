# Historias del Islam – estilo minimalista nocturno (sin personas, sin música)
# Uso: python3 historia.py stills t1 t2 ...   |   python3 historia.py video salida.mp4
import math, random, subprocess, sys, json, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
LORA_I = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
INTER = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
INTER_L = "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf"

GOLD = (222, 188, 120)
GOLD_SOFT = (190, 160, 105)
CREAM = (240, 232, 214)
NIGHT = (6, 10, 24)

# tiempos de la narración: [(inicio, fin)] por frase  (se cargan de tiempos.json)
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "tiempos.json")) as f:
    LINES = [tuple(x) for x in json.load(f)]
LEAD = 0.35          # la imagen cambia un poco antes que la voz
XF = 0.6             # duración del fundido
BOUNDS = [0.0] + [LINES[i][0] - min(LEAD, (LINES[i][0] - LINES[i - 1][1]) / 2) for i in range(1, len(LINES))]
DUR = 62.4
BOUNDS.append(DUR)

@lru_cache(maxsize=None)
def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def prog(t, s, d): return clamp((t - s) / d)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def vgrad(c1, c2, power=1.0):
    g = ((yy / H) ** power)[..., None]
    return np.array(c1, np.float32) * (1 - g) + np.array(c2, np.float32) * g

def to_img(arr): return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def glow_spot(arr, cx, cy, r, col, s):
    e = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
    return arr + np.array(col, np.float32) * e * s

# ---------- capa fija: patrón geométrico islámico casi invisible + viñeta ----------
def make_pattern():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    s = 180
    for gy in range(-s, H + s, s):
        for gx in range(-s, W + s, s):
            cx, cy = gx + s / 2, gy + s / 2
            r = s * 0.36
            sq1 = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (45, 135, 225, 315)]
            sq2 = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (0, 90, 180, 270)]
            d.polygon(sq1, outline=GOLD + (16,)); d.polygon(sq2, outline=GOLD + (16,))
            d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=GOLD + (14,))
    return im
PATTERN = make_pattern()
vig = np.clip(1.25 - np.sqrt(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H * 0.5) / (H * 0.62)) ** 2) * 0.75, 0, 1)
VIGNETTE = Image.fromarray(((1 - vig) * 235).astype(np.uint8), "L")
BLACK = Image.new("RGBA", (W, H), (2, 3, 8, 255))

# ---------- elementos ----------
random.seed(3)
STARS = [(random.uniform(0, W), random.uniform(0, H * 0.62), random.uniform(1.0, 3.2), random.uniform(0, 6.28)) for _ in range(230)]
def draw_stars(im, t, alpha=1.0, ymax=1.0):
    d = ImageDraw.Draw(im)
    for (x, y, r, ph) in STARS:
        if y > H * ymax: continue
        a = int((120 + 110 * math.sin(t * 1.3 + ph * 3)) * alpha)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 248, 230, max(0, a)))

def crescent(r, col=(250, 236, 200)):
    s = 3; S = int(r * 2 * s + 20)
    m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m)
    d.ellipse([10, 10, S - 10, S - 10], fill=255)
    d.ellipse([10 + r * 0.55 * s, 10 - r * 0.15 * s, S - 10 + r * 0.55 * s, S - 10 - r * 0.15 * s], fill=0)
    m = m.resize((S // s, S // s), Image.LANCZOS)
    im = Image.new("RGBA", m.size, col + (0,)); im.putalpha(m)
    g = Image.new("RGBA", (im.width + 160, im.height + 160), (0, 0, 0, 0))
    gl = Image.new("RGBA", im.size, (255, 220, 160, 0)); gl.putalpha(m.point(lambda v: v // 2))
    g.alpha_composite(gl, (80, 80)); g = g.filter(ImageFilter.GaussianBlur(28)); g.alpha_composite(im, (80, 80))
    return g
MOON = crescent(70)

@lru_cache(maxsize=None)
def skyline(seed, base_y, col, scale=1.0, domes=True):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = -20
    while x < W + 20:
        w = rnd.randint(60, 150) * scale; h = rnd.randint(80, 260) * scale
        d.rectangle([x, base_y - h, x + w, H], fill=col)
        if domes and rnd.random() < 0.45:
            dw = w * 0.7
            d.ellipse([x + (w - dw) / 2, base_y - h - dw * 0.55, x + (w + dw) / 2, base_y - h + dw * 0.45], fill=col)
        if domes and rnd.random() < 0.18:
            mx = x + w * 0.5; mh = rnd.randint(180, 300) * scale
            d.rectangle([mx - 9 * scale, base_y - h - mh, mx + 9 * scale, base_y - h], fill=col)
            d.ellipse([mx - 16 * scale, base_y - h - mh - 26 * scale, mx + 16 * scale, base_y - h - mh + 6 * scale], fill=col)
        x += w + rnd.randint(-10, 18)
    return im

def waves(im, t, base_y, col, amp, freq, speed, ph=0.0):
    d = ImageDraw.Draw(im)
    pts = [(x, base_y + amp * math.sin(x * freq + t * speed + ph) + amp * 0.4 * math.sin(x * freq * 2.3 - t * speed * 0.7)) for x in range(0, W + 30, 30)]
    d.polygon(pts + [(W, H), (0, H)], fill=col)

def whale_sprite(w=900, col=(12, 24, 44), rim=(70, 110, 140)):
    s = 2; Wd, Hd = int(w * s), int(w * 0.5 * s)
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cy = Hd * 0.45
    top, bot = [], []
    N = 80
    for k in range(N + 1):
        u = k / N                       # 0 = cabeza (izquierda), 1 = cola
        x = Wd * (0.04 + 0.74 * u)
        th = (math.sin(math.pi * min(1, (u + 0.08) / 1.0)) ** 0.7) * (1 - 0.82 * u ** 1.6)
        top.append((x, cy - Hd * 0.30 * th - Hd * 0.02 * u))
        bot.append((x, cy + Hd * 0.26 * th + Hd * 0.03 * (1 - u)))
    tail_x = Wd * 0.78
    poly = top + [(tail_x, cy - Hd * 0.03), (Wd * 0.97, cy - Hd * 0.26), (Wd * 0.90, cy), (Wd * 0.97, cy + Hd * 0.24), (tail_x, cy + Hd * 0.04)] + bot[::-1]
    d.polygon(poly, fill=col)
    d.polygon([(Wd * 0.28, cy + Hd * 0.18), (Wd * 0.40, cy + Hd * 0.42), (Wd * 0.40, cy + Hd * 0.20)], fill=col)   # aleta
    d.ellipse([Wd * 0.13, cy - Hd * 0.04, Wd * 0.13 + 14 * s, cy - Hd * 0.04 + 14 * s], fill=(70, 100, 130))      # ojo
    out = im.resize((Wd // s, Hd // s), Image.LANCZOS)
    a = out.split()[3]
    edge = a.filter(ImageFilter.GaussianBlur(4))
    rimL = Image.new("RGBA", out.size, rim + (0,)); rimL.putalpha(Image.fromarray(np.clip((np.array(edge, np.int16) - np.array(a, np.int16)) * 3, 0, 255).astype(np.uint8)))
    base = Image.new("RGBA", out.size, (0, 0, 0, 0)); base.alpha_composite(rimL); base.alpha_composite(out)
    return base
WHALE = whale_sprite()

def ship(im, cx, cy, t, scale=1.0, col=(8, 12, 22)):
    s = scale; layer = Image.new("RGBA", (int(420 * s), int(420 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    w, h = layer.size
    d.polygon([(w * 0.08, h * 0.70), (w * 0.92, h * 0.70), (w * 0.78, h * 0.86), (w * 0.22, h * 0.86)], fill=col)
    d.rectangle([w * 0.49, h * 0.12, w * 0.52, h * 0.71], fill=col)
    d.polygon([(w * 0.53, h * 0.16), (w * 0.53, h * 0.64), (w * 0.86, h * 0.62)], fill=col)
    d.polygon([(w * 0.48, h * 0.22), (w * 0.48, h * 0.64), (w * 0.20, h * 0.62)], fill=col)
    rot = math.sin(t * 1.6) * 7
    lay = layer.rotate(rot, resample=Image.BICUBIC)
    im.alpha_composite(lay, (int(cx - w / 2), int(cy - h * 0.78 + math.sin(t * 1.6 + 1) * 10)))

def rays(im, t, cx, top_y, n=6, col=(150, 200, 230), alpha=26, spread=520, length=2300):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = cx - spread / 2 + spread * i / (n - 1) + 40 * math.sin(t * 0.4 + i)
        wdt = 50 + 25 * math.sin(t * 0.7 + i * 2)
        d.polygon([(x - wdt / 2, top_y), (x + wdt / 2, top_y), (x + wdt * 2.4 + (x - cx) * 0.6, top_y + length), (x - wdt * 2.4 + (x - cx) * 0.6, top_y + length)], fill=col + (alpha,))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)))

# ---------- texto elegante ----------
@lru_cache(maxsize=512)
def text_img(txt, size, col=CREAM, path=LORA, weight=500, spacing=0, shadow=True):
    f = font(path, size, weight)
    if spacing:
        widths = [f.getlength(ch) for ch in txt]; tw = int(sum(widths) + spacing * (len(txt) - 1))
    else:
        tw = int(f.getlength(txt))
    asc, desc = f.getmetrics(); pad = 40
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def put(dd, fill):
        x = pad
        if spacing:
            for ch, wch in zip(txt, widths): dd.text((x, pad), ch, font=f, fill=fill); x += wch + spacing
        else: dd.text((x, pad), txt, font=f, fill=fill)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); put(ImageDraw.Draw(sh), (0, 0, 0, 200))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    put(d, col)
    return im

def put_text(dst, im, cx, cy, t, start, dur=1.0, rise=24):
    p = prog(t, start, dur)
    if p <= 0: return
    a = ease(p)
    im2 = im.copy(); im2.putalpha(im.split()[3].point(lambda v: int(v * a)))
    dst.alpha_composite(im2, (int(cx - im.width / 2), int(cy - im.height / 2 + (1 - eout(p)) * rise)))

def gold_line(dst, cx, cy, t, start, w=160):
    p = eout(prog(t, start, 1.2))
    if p <= 0: return
    ImageDraw.Draw(dst).line([(cx - w / 2 * p, cy), (cx + w / 2 * p, cy)], fill=GOLD + (200,), width=3)

# ---------- escenas (t = tiempo local desde que empieza la escena) ----------
def sc_ocean(t, whale=True, deep=0.0):
    arr = vgrad((10, 40, 70), (2, 8, 20), 0.8)
    arr = glow_spot(arr, W * 0.5, -100, 900, (60, 120, 160), 0.35)
    if deep: arr = arr * (1 - deep)
    im = to_img(arr)
    rays(im, t, W * 0.5, 0, alpha=int(22 * (1 - deep)))
    if whale:
        x = W * 0.5 + 140 - t * 40
        paste = WHALE
        im.alpha_composite(paste, (int(x - paste.width / 2), int(H * 0.56 - paste.height / 2 + math.sin(t * 0.8) * 14)))
    # partículas
    d = ImageDraw.Draw(im)
    for i in range(60):
        px = (i * 137.5) % W; py = (H - ((i * 291 + t * (12 + i % 7)) % H))
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(180, 220, 240, 60))
    return im

@lru_cache(maxsize=None)
def ancient_city():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    far = (26, 24, 42, 255); near = (12, 11, 22, 255)
    # zigurat escalonado al fondo
    cx, by = W * 0.42, H * 0.76
    for k in range(5):
        w = 520 - k * 95; h = 70
        d.rectangle([cx - w / 2, by - (k + 1) * h, cx + w / 2, by - k * h], fill=far)
    rnd = random.Random(4)
    x = 0
    while x < W:
        w = rnd.randint(90, 170); h = rnd.randint(60, 140)
        d.rectangle([x, H * 0.80 - h, x + w, H], fill=far); x += w - 6
    # muralla con almenas
    wy = H * 0.82
    d.rectangle([0, wy, W, H], fill=near)
    for x in range(0, W, 46):
        d.rectangle([x, wy - 26, x + 26, wy], fill=near)
    return im

def sc_city(t, dusk=True):
    arr = vgrad((14, 20, 48), (78, 48, 48), 1.6)
    arr = glow_spot(arr, W * 0.5, H * 0.72, 700, (210, 130, 70), 0.28)
    im = to_img(arr)
    draw_stars(im, t, 0.8, 0.5)
    im.alpha_composite(MOON, (int(W * 0.68), int(H * 0.16 + math.sin(t * 0.3) * 6)))
    im.alpha_composite(ancient_city())
    d = ImageDraw.Draw(im); rnd = random.Random(1)
    for _ in range(14):
        x = rnd.uniform(40, W - 40); y = rnd.uniform(H * 0.72, H * 0.79)
        a = int(150 + 80 * math.sin(t * 2 + x))
        d.ellipse([x, y, x + 9, y + 9], fill=(240, 180, 100, a))
    return im

def sc_leaving(t):
    arr = vgrad((8, 12, 30), (30, 24, 34), 1.4)
    im = to_img(arr)
    draw_stars(im, t, 1.0, 0.55)
    im.alpha_composite(MOON, (int(W * 0.12), int(H * 0.12)))
    d = ImageDraw.Draw(im)
    for k, (yb, col) in enumerate([(H * 0.70, (34, 28, 40)), (H * 0.78, (22, 18, 28)), (H * 0.88, (12, 10, 18))]):
        pts = [(x, yb + 40 * math.sin(x / 260 + k * 2)) for x in range(0, W + 40, 40)]
        d.polygon(pts + [(W, H), (0, H)], fill=col + (255,))
    # camino de luz que se aleja
    p = eout(prog(t, 0.2, 3.5))
    d.line([(W * 0.5, H), (W * 0.5 + 60, H * 0.88), (W * 0.62, H * 0.80), (W * 0.70, H * 0.74)], fill=GOLD_SOFT + (int(90 * p),), width=6)
    return im

def sc_sea(t):
    arr = vgrad((10, 14, 30), (16, 30, 50), 1.0)
    im = to_img(arr)
    draw_stars(im, t, 0.5, 0.35)
    cl = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); dc = ImageDraw.Draw(cl)
    for i in range(6):
        cx = ((i * 300 + t * 22) % (W + 500) - 250) / 4
        dc.ellipse([cx - 70, (150 + i * 45) / 4 - 25, cx + 70, (150 + i * 45) / 4 + 30], fill=(30, 36, 56, 150))
    im.alpha_composite(cl.filter(ImageFilter.GaussianBlur(8)).resize((W, H), Image.BILINEAR))
    waves(im, t, H * 0.60, (20, 40, 66, 255), 26, 0.008, 1.4)
    ship(im, W * 0.5, H * 0.60, t, 1.1)
    waves(im, t, H * 0.64, (14, 30, 52, 255), 34, 0.006, 1.8, 1.0)
    waves(im, t, H * 0.72, (8, 20, 38, 255), 44, 0.005, 2.2, 2.0)
    return im

def sc_dark(t):
    arr = np.zeros((H, W, 3), np.float32)
    bands = [(0, 0.33, (14, 18, 40)), (0.33, 0.66, (8, 16, 30)), (0.66, 1.0, (4, 6, 10))]
    for i, (a, b, col) in enumerate(bands):
        p = ease(prog(t, 0.2 + i * 0.9, 1.0))
        m = ((yy >= a * H) & (yy < b * H))[..., None]
        arr = arr + m * np.array(col, np.float32) * p
    im = to_img(arr)
    d = ImageDraw.Draw(im)
    for i in (1, 2):
        p = eout(prog(t, 0.6 + i * 0.9, 0.8))
        d.line([(W / 2 - 300 * p, H * i / 3), (W / 2 + 300 * p, H * i / 3)], fill=GOLD + (60,), width=2)
    return im

def sc_light(t):
    arr = np.full((H, W, 3), 3, np.float32)
    r = 80 + 160 * eout(prog(t, 0.3, 4.0)) + 10 * math.sin(t * 2)
    arr = glow_spot(arr, W / 2, H * 0.52, r * 2.2, (255, 210, 140), 0.55)
    arr = glow_spot(arr, W / 2, H * 0.52, r * 0.5, (255, 240, 210), 0.9)
    return to_img(arr)

def sc_verse(t):
    arr = np.full((H, W, 3), 3, np.float32)
    arr = glow_spot(arr, W / 2, H * 0.50, 700, (255, 210, 140), 0.10)
    im = to_img(arr)
    d = ImageDraw.Draw(im)
    p = ease(prog(t, 0.0, 1.0))
    x0, y0, x1, y1 = 110, H * 0.30, W - 110, H * 0.70
    d.rounded_rectangle([x0, y0, x1, y1], 28, outline=GOLD + (int(150 * p),), width=2)
    d.rounded_rectangle([x0 + 14, y0 + 14, x1 - 14, y1 - 14], 20, outline=GOLD + (int(60 * p),), width=1)
    return im

def sc_dawn(t):
    arr = vgrad((40, 50, 90), (240, 170, 120), 1.3)
    sun_y = H * 0.66 - 120 * eout(prog(t, 0, 5))
    arr = glow_spot(arr, W / 2, sun_y, 520, (255, 200, 140), 0.55)
    arr = glow_spot(arr, W / 2, sun_y, 120, (255, 240, 210), 0.9)
    im = to_img(arr)
    waves(im, t, H * 0.66, (60, 80, 120, 255), 10, 0.01, 0.8)
    waves(im, t, H * 0.70, (40, 60, 100, 255), 14, 0.008, 1.0, 1.5)
    d = ImageDraw.Draw(im)
    pts = [(x, H * 0.78 - 60 * math.exp(-((x - W * 0.75) / 300) ** 2)) for x in range(0, W + 40, 40)]
    d.polygon(pts + [(W, H), (0, H)], fill=(196, 160, 120, 255))
    # planta que crece en la orilla
    g = eout(prog(t, 0.6, 3.0))
    if g > 0:
        bx, by = W * 0.74, H * 0.73
        L = 260 * g
        stem = [(bx + 40 * math.sin(i / 6), by - L * i / 20) for i in range(21)]
        d.line(stem, fill=(70, 110, 70, 255), width=8)
        for i in range(3, 21, 3):
            if i / 20 > g: break
            sx, sy = stem[i]; side = 1 if i % 6 else -1
            d.ellipse([sx + side * 10 - (0 if side > 0 else 70), sy - 26, sx + side * 10 + (70 if side > 0 else 0), sy + 18], fill=(90, 140, 85, 255))
    return im

def sc_sky(t):
    arr = vgrad((4, 8, 22), (18, 26, 60), 1.1)
    arr = glow_spot(arr, W / 2, H * 0.95, 900, (80, 70, 130), 0.25)
    im = to_img(arr)
    draw_stars(im, t, 1.0, 1.0)
    im.alpha_composite(MOON, (int(W / 2 - MOON.width / 2), int(H * 0.20)))
    return im

def sc_outro(t):
    arr = np.full((H, W, 3), 0, np.float32) + np.array(NIGHT, np.float32)
    arr = glow_spot(arr, W / 2, H * 0.45, 700, (120, 100, 70), 0.12)
    return to_img(arr)

# ---------- textos por escena ----------
LABEL = text_img("HISTORIAS DEL ISLAM", 30, GOLD, INTER, None, 9, False)

def texts(i, dst, t):
    if i == 0:
        put_text(dst, text_img("El hombre", 96, CREAM, LORA, 500), W / 2, H * 0.30, t, 0.5)
        put_text(dst, text_img("y la ballena", 96, GOLD, LORA_I, 500), W / 2, H * 0.30 + 120, t, 0.9)
    elif i == 1:
        put_text(dst, text_img("Yunus", 150, CREAM, LORA, 500), W / 2, H * 0.34, t, 0.3)
        put_text(dst, text_img("la paz sea con él", 46, GOLD, LORA_I, 400), W / 2, H * 0.34 + 120, t, 0.8)
        gold_line(dst, W / 2, H * 0.34 + 190, t, 1.0)
        put_text(dst, text_img("NÍNIVE", 30, (200, 200, 210), INTER, None, 10, False), W / 2, H * 0.34 + 250, t, 1.4)
    elif i == 2:
        put_text(dst, text_img("Se marchó", 104, CREAM, LORA_I, 500), W / 2, H * 0.32, t, 0.6)
    elif i == 3:
        put_text(dst, text_img("En mitad del mar", 88, CREAM, LORA, 500), W / 2, H * 0.24, t, 0.4)
    elif i == 4:
        put_text(dst, text_img("La ballena", 104, CREAM, LORA_I, 500), W / 2, H * 0.26, t, 0.3)
    elif i == 5:
        for k, w in enumerate(["La noche", "El mar", "La ballena"]):
            put_text(dst, text_img(w, 64, CREAM if k < 2 else GOLD, LORA_I, 400), W / 2, H * (k / 3 + 1 / 6), t, 0.4 + k * 0.9)
    elif i == 6:
        put_text(dst, text_img("La súplica", 104, GOLD, LORA_I, 500), W / 2, H * 0.30, t, 0.5)
    elif i == 7:
        lines = ["«No hay más dios", "que Tú. Glorificado", "seas. Yo he sido", "de los injustos.»"]
        for k, ln in enumerate(lines):
            put_text(dst, text_img(ln, 68, CREAM, LORA_I, 400), W / 2, H * 0.40 + k * 92, t, 0.3 + k * 0.25)
        gold_line(dst, W / 2, H * 0.40 + 4 * 92 + 10, t, 1.4, 120)
        put_text(dst, text_img("Corán 21:87", 36, GOLD, INTER, None, 4, False), W / 2, H * 0.40 + 4 * 92 + 70, t, 1.6)
    elif i == 8:
        put_text(dst, text_img("La salvación", 100, (40, 30, 40), LORA_I, 500, 0, False), W / 2, H * 0.24, t, 0.5)
    elif i == 9:
        put_text(dst, text_img("Nunca es tarde", 96, CREAM, LORA_I, 500), W / 2, H * 0.50, t, 0.5)
        put_text(dst, text_img("para volver a Allah", 56, GOLD, LORA, 400), W / 2, H * 0.50 + 110, t, 1.1)
    elif i == 10:
        put_text(dst, text_img("¿Qué historia", 96, CREAM, LORA, 500), W / 2, H * 0.42, t, 0.3)
        put_text(dst, text_img("cuento ahora?", 96, GOLD, LORA_I, 500), W / 2, H * 0.42 + 120, t, 0.6)
        gold_line(dst, W / 2, H * 0.42 + 220, t, 1.0)
        put_text(dst, text_img("Escríbelo en comentarios", 40, (200, 200, 210), INTER_L, None, 1, False), W / 2, H * 0.42 + 290, t, 1.3)

SCENES = [lambda t: sc_ocean(t), lambda t: sc_city(t), sc_leaving, sc_sea, lambda t: sc_ocean(t, True, 0.25),
          sc_dark, sc_light, sc_verse, sc_dawn, sc_sky, sc_outro]

def scene_frame(i, t):
    lt = t - BOUNDS[i]
    span = BOUNDS[i + 1] - BOUNDS[i]
    bg = SCENES[i](lt)
    z = 1.0 + 0.05 * (lt / max(span, 1))           # movimiento lento de cámara
    if z > 1.001:
        lw, lh = int(W * z), int(H * z)
        bg = bg.resize((lw, lh), Image.BILINEAR).crop(((lw - W) // 2, (lh - H) // 2, (lw - W) // 2 + W, (lh - H) // 2 + H))
    bg.alpha_composite(PATTERN)
    texts(i, bg, lt)
    return bg

def render(t):
    i = max(k for k in range(len(SCENES)) if BOUNDS[k] <= t) if t < DUR else len(SCENES) - 1
    im = scene_frame(i, t)
    # fundido con la escena anterior
    if i > 0 and t - BOUNDS[i] < XF:
        prev = scene_frame(i - 1, t)
        im = Image.blend(prev, im, ease((t - BOUNDS[i]) / XF))
    im = Image.composite(BLACK, im, VIGNETTE)
    im.alpha_composite(LABEL, (int(W / 2 - LABEL.width / 2), 120))
    # fundido de entrada y salida
    a = min(prog(t, 0, 0.5), 1 - prog(t, DUR - 0.8, 0.8))
    if a < 1: im = Image.blend(BLACK, im, a)
    return im.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "stills":
        for tt in sys.argv[2:]:
            render(float(tt)).save(f"still_{float(tt):05.1f}.png")
    else:
        out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out], stdin=subprocess.PIPE)
        nf = int(round(DUR * FPS))
        for f in range(nf):
            p.stdin.write(render(f / FPS).tobytes())
            if f % 150 == 0: print(f, nf, flush=True)
        p.stdin.close(); p.wait()
        print("done", DUR)
