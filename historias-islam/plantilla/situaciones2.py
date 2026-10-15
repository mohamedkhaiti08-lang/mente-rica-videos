# "Situaciones de la vida" – dos personajes sin cara, comparativa y enseñanza.
# Uso: python3 situaciones.py config.json stills t1 t2 ... | python3 situaciones.py config.json video salida.mp4
import math, json, sys, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POP_M = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POP_R = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
LORA_I = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG1, BG2 = (247, 242, 231), (237, 227, 207)
INK = (34, 40, 49)
GREEN = (22, 128, 92)
RED = (214, 82, 70)
GOLD = (196, 150, 70)
GREY = (120, 126, 138)
AHMED_SHIRT = (88, 108, 140)
SKIN = (224, 184, 150)

CFG = json.load(open(sys.argv[1]))
LINES = CFG["lines"]
B = [0.0] + [LINES[i][0] - min(0.3, (LINES[i][0] - LINES[i - 1][1]) / 2) for i in range(1, len(LINES))]
DUR = CFG.get("dur", LINES[-1][1] + 1.4)

@lru_cache(maxsize=None)
def F(p, s): return ImageFont.truetype(p, s)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def eback(t, s=1.6): t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def prog(t, s, d): return clamp((t - s) / d)

# ---------- fondo ----------
def make_bg():
    yy = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(BG1, float) * (1 - yy) + np.array(BG2, float) * yy
    im = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im); s = 150
    for gy in range(0, H + s, s):
        for gx in range(0, W + s, s):
            r = s * 0.32
            for base in (0, 45):
                pts = [(gx + r * math.cos(math.radians(a + base)), gy + r * math.sin(math.radians(a + base))) for a in (0, 90, 180, 270)]
                d.polygon(pts, outline=GOLD + (20,))
    return im
BG = make_bg()

# ---------- utilidades de dibujo ----------
def paste(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    dst.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

@lru_cache(maxsize=512)
def text(txt, size, col=INK, path=POP):
    f = F(path, size); bb = f.getbbox(txt); asc, desc = f.getmetrics()
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, asc + desc + 10), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 0), txt, font=f, fill=col)
    return im

@lru_cache(maxsize=128)
def pill(txt, size, fill, col=(255, 255, 255), path=POP):
    t = text(txt, size, col, path)
    w, h = t.width + 50, int(size * 1.75)
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], h, fill=fill)
    im = im.resize((w, h), Image.LANCZOS)
    im.alpha_composite(t, (25, int((h - t.height) / 2 + size * 0.06)))
    return im

@lru_cache(maxsize=64)
def card(w, h, fill=(255, 255, 255, 240), r=36):
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([20, 28, w + 20, h + 28], r, fill=(60, 40, 10, 34))
    im = im.filter(ImageFilter.GaussianBlur(10))
    ImageDraw.Draw(im).rounded_rectangle([20, 20, w + 20, h + 20], r, fill=fill)
    return im

def text_lines(dst, lines, cx, y0, size, col, path, gap, t=None, starts=None, fade=0.35):
    for k, ln in enumerate(lines):
        a = 1.0 if starts is None else ease(prog(t, starts[k], fade))
        if a <= 0: continue
        im = text(ln, size, col, path)
        paste(dst, im, cx, y0 + k * gap + (1 - eout(a)) * 14, 1.0, a)

@lru_cache(maxsize=64)
def bubble(lines, size=40, col=INK, path=POP_M, tail="left"):
    ts = [text(l, size, col, path) for l in lines]
    w = max(t.width for t in ts) + 60; h = sum(int(size * 1.35) for _ in ts) + 40
    im = Image.new("RGBA", (w + 60, h + 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 20, w + 30, h + 20], 34, fill=(255, 255, 255, 250), outline=(0, 0, 0, 30), width=2)
    tx = 90 if tail == "left" else w - 30
    d.polygon([(tx - 20, h + 18), (tx + 20, h + 18), (tx - 10 if tail == "left" else tx + 10, h + 60)], fill=(255, 255, 255, 250))
    y = 38
    for t_ in ts:
        im.alpha_composite(t_, (int(30 + (w - t_.width) / 2), y)); y += int(size * 1.35)
    return im

# ---------- personaje sin cara ----------
@lru_cache(maxsize=64)
def character(shirt, mood="calm", arms_phase=0, scale=1.0, cap=True, flip=False):
    s = 2; w, h = int(320 * s * scale), int(580 * s * scale)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    S = lambda v: v * s * scale
    cx = w / 2
    d.rounded_rectangle([cx - S(60), S(390), cx - S(12), S(560)], S(22), fill=(60, 66, 80))
    d.rounded_rectangle([cx + S(12), S(390), cx + S(60), S(560)], S(22), fill=(60, 66, 80))
    d.rounded_rectangle([cx - S(64), S(540), cx - S(4), S(570)], S(14), fill=(40, 44, 54))
    d.rounded_rectangle([cx + S(4), S(540), cx + S(64), S(570)], S(14), fill=(40, 44, 54))
    d.rounded_rectangle([cx - S(95), S(200), cx + S(95), S(420)], S(70), fill=shirt)
    aw = int(S(40))
    if mood == "angry":
        up = 120 if arms_phase == 0 else 95
        d.line([(cx - S(85), S(240)), (cx - S(150), S(up))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(240)), (cx + S(150), S(up))], fill=shirt, width=aw)
        d.ellipse([cx - S(176), S(up - 26), cx - S(124), S(up + 26)], fill=SKIN); d.ellipse([cx + S(124), S(up - 26), cx + S(176), S(up + 26)], fill=SKIN)
    elif mood == "calm":
        d.line([(cx - S(85), S(250)), (cx - S(40), S(340))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(250)), (cx + S(40), S(340))], fill=shirt, width=aw)
        d.ellipse([cx - S(32), S(310), cx + S(32), S(362)], fill=SKIN)
    elif mood == "give":        # brazo extendido hacia la derecha
        d.line([(cx - S(85), S(250)), (cx - S(110), S(380))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(250)), (cx + S(185), S(270))], fill=shirt, width=aw)
        d.ellipse([cx - S(136), S(360), cx - S(84), S(410)], fill=SKIN); d.ellipse([cx + S(170), S(244), cx + S(222), S(296)], fill=SKIN)
    elif mood == "point":       # señalando con el brazo
        d.line([(cx - S(85), S(250)), (cx - S(110), S(380))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(240)), (cx + S(190), S(170))], fill=shirt, width=aw)
        d.ellipse([cx - S(136), S(360), cx - S(84), S(410)], fill=SKIN); d.ellipse([cx + S(174), S(144), cx + S(226), S(196)], fill=SKIN)
    else:                       # brazos abajo
        d.line([(cx - S(85), S(250)), (cx - S(110), S(380))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(250)), (cx + S(110), S(380))], fill=shirt, width=aw)
        d.ellipse([cx - S(136), S(360), cx - S(84), S(410)], fill=SKIN); d.ellipse([cx + S(84), S(360), cx + S(136), S(410)], fill=SKIN)
    d.ellipse([cx - S(70), S(40), cx + S(70), S(180)], fill=SKIN)
    if cap: d.chord([cx - S(68), S(36), cx + S(68), S(140)], 180, 360, fill=(250, 250, 250))
    im = im.resize((w // s, h // s), Image.LANCZOS)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    out = Image.new("RGBA", (im.width, im.height + 24), (0, 0, 0, 0))
    sh = Image.new("RGBA", (im.width, 44), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([40, 6, im.width - 40, 38], fill=(0, 0, 0, 45))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (0, im.height - 24)); out.alpha_composite(im)
    return out

def draw_char(dst, t, cx, cy, shirt, mood, scale=1.0, alpha=1.0, cap=True, flip=False):
    phase = int(t * 6) % 2 if mood == "angry" else 0
    dx = math.sin(t * 40) * 5 if mood == "angry" else math.sin(t * 1.5) * 3
    breathe = 1 + 0.012 * math.sin(t * 2.4)
    im = character(shirt, mood, phase, scale, cap, flip)
    paste(dst, im, cx + dx, cy - (breathe - 1) * 200, 1.0, alpha)

def angry_symbols(dst, t, cx, cy, alpha=1.0):
    sc = 1 + 0.12 * abs(math.sin(t * 7))
    paste(dst, text("#@!", 74, RED, POP), cx, cy, sc, alpha, math.sin(t * 9) * 6)

def calm_glow(dst, t, cx, cy, alpha=1.0):
    lay = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = 150 + 12 * math.sin(t * 2)
    d.ellipse([210 - r, 210 - r, 210 + r, 210 + r], fill=(255, 220, 140, int(70 * alpha)))
    dst.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40)), (int(cx - 210), int(cy - 210)))

def mark(dst, cx, cy, ok, t, start):
    p = prog(t, start, 0.4)
    if p <= 0: return
    c = Image.new("RGBA", (90, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.ellipse([0, 0, 89, 89], fill=GREEN if ok else RED)
    sym = text("✓" if ok else "✗", 52, (255, 255, 255), DJ)
    c.alpha_composite(sym, (45 - sym.width // 2, 12))
    paste(dst, c, cx, cy, 0.4 + 0.6 * eback(p, 2.5), ease(p * 1.5))

# ---------- props ----------
@lru_cache(maxsize=None)
def bus():
    im = Image.new("RGBA", (700, 320), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 40, 680, 250], 44, fill=(242, 178, 60))
    for x in range(70, 600, 118): d.rounded_rectangle([x, 74, x + 92, 146], 14, fill=(205, 232, 246))
    d.rectangle([20, 180, 680, 196], fill=(225, 150, 40))
    d.ellipse([110, 205, 205, 300], fill=INK); d.ellipse([500, 205, 595, 300], fill=INK)
    d.ellipse([140, 235, 175, 270], fill=(150, 150, 150)); d.ellipse([530, 235, 565, 270], fill=(150, 150, 150))
    return im

@lru_cache(maxsize=None)
def counter():
    im = Image.new("RGBA", (760, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 150, 740, 340], 24, fill=(160, 120, 86))
    d.rectangle([20, 150, 740, 186], fill=(130, 94, 66))
    d.rounded_rectangle([430, 40, 680, 160], 18, fill=(70, 80, 96))
    d.rounded_rectangle([455, 60, 655, 110], 10, fill=(160, 220, 170))
    t_ = text("CAJA", 34, (255, 255, 255), POP); im.alpha_composite(t_, (90, 230))
    return im

@lru_cache(maxsize=None)
def banknote(label="10 €"):
    im = Image.new("RGBA", (300, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 299, 159], 16, fill=(120, 170, 110), outline=(80, 120, 74), width=5)
    d.ellipse([110, 40, 190, 120], outline=(80, 120, 74), width=5)
    t_ = text(label, 48, (255, 255, 255), POP); im.alpha_composite(t_, (150 - t_.width // 2, 50))
    return im

@lru_cache(maxsize=None)
def icon_card(kind):
    S = 420
    im = Image.new("RGBA", (S + 40, S + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([20, 28, S + 20, S + 28], fill=(60, 40, 10, 30))
    im = im.filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(im)
    d.ellipse([20, 20, S + 20, S + 20], fill=(255, 255, 255, 245))
    c = 20 + S / 2
    Y = (242, 178, 60); B = (88, 130, 190); DG = (70, 76, 90)
    if kind == "controller":
        d.rounded_rectangle([c - 140, c - 60, c + 140, c + 70], 60, fill=DG)
        d.rectangle([c - 98, c - 10, c - 50, c + 6], fill=(255, 255, 255)); d.rectangle([c - 82, c - 26, c - 66, c + 22], fill=(255, 255, 255))
        for dx, dy, col in ((60, -14, RED), (92, 10, GREEN), (60, 34, Y)): d.ellipse([c + dx - 14, c + dy - 14, c + dx + 14, c + dy + 14], fill=col)
    elif kind == "plate":
        d.ellipse([c - 150, c - 100, c + 150, c + 100], fill=(235, 235, 240), outline=(200, 200, 210), width=6)
        d.ellipse([c - 100, c - 64, c + 100, c + 64], fill=(250, 250, 252))
        d.pieslice([c - 90, c - 56, c + 90, c + 56], 200, 340, fill=(214, 150, 80))
        d.ellipse([c - 30, c + 0, c + 30, c + 36], fill=(120, 170, 90)); d.ellipse([c + 20, c - 10, c + 70, c + 26], fill=RED)
    elif kind == "exam":
        d.rounded_rectangle([c - 110, c - 150, c + 110, c + 150], 16, fill=(250, 250, 250), outline=(200, 200, 205), width=5)
        for k in range(6): d.line([(c - 80, c - 70 + k * 34), (c + 60, c - 70 + k * 34)], fill=(190, 195, 205), width=8)
        f = F(POP, 84); d.text((c + 20, c - 160), "3", font=f, fill=RED); d.ellipse([c + 4, c - 150, c + 100, c - 50], outline=RED, width=7)
    elif kind == "gossip":
        for (x, y, col) in ((c - 70, c - 40, B), (c + 60, c + 50, RED)):
            d.rounded_rectangle([x - 90, y - 60, x + 90, y + 60], 40, fill=col)
            d.polygon([(x - 40, y + 55), (x - 10, y + 55), (x - 50, y + 95)], fill=col)
            for k in range(3): d.ellipse([x - 50 + k * 40, y - 10, x - 30 + k * 40, y + 10], fill=(255, 255, 255))
    elif kind == "wallet":
        d.rounded_rectangle([c - 140, c - 90, c + 140, c + 100], 24, fill=(120, 80, 50))
        d.rounded_rectangle([c + 40, c - 30, c + 150, c + 40], 18, fill=(100, 64, 40)); d.ellipse([c + 70, c - 8, c + 96, c + 18], fill=Y)
        d.rounded_rectangle([c - 110, c - 130, c + 60, c - 70], 10, fill=(120, 170, 110))
    elif kind == "gift":
        d.rectangle([c - 120, c - 40, c + 120, c + 130], fill=GREEN); d.rectangle([c - 140, c - 90, c + 140, c - 30], fill=(30, 150, 110))
        d.rectangle([c - 18, c - 90, c + 18, c + 130], fill=Y)
        d.ellipse([c - 80, c - 150, c - 4, c - 86], outline=Y, width=14); d.ellipse([c + 4, c - 150, c + 80, c - 86], outline=Y, width=14)
    elif kind == "bags":
        for (x, col) in ((c - 70, (214, 170, 110)), (c + 70, (190, 150, 95))):
            d.rounded_rectangle([x - 80, c - 60, x + 80, c + 140], 14, fill=col)
            d.arc([x - 45, c - 120, x + 45, c - 20], 180, 360, fill=(120, 90, 60), width=10)
        d.ellipse([c - 120, c - 110, c - 70, c - 60], fill=(120, 170, 90)); d.rectangle([c + 40, c - 130, c + 60, c - 50], fill=(240, 220, 160))
    elif kind == "door":
        d.rounded_rectangle([c - 100, c - 160, c + 100, c + 150], 12, fill=(160, 110, 70)); d.rectangle([c - 70, c - 130, c + 70, c - 20], fill=(140, 94, 58)); d.rectangle([c - 70, c + 10, c + 70, c + 120], fill=(140, 94, 58))
        d.ellipse([c + 54, c - 6, c + 78, c + 18], fill=Y)
        for k in range(3): d.line([(c + 120, c - 80 + k * 50), (c + 170, c - 100 + k * 50)], fill=RED, width=8)
    elif kind == "alarm":
        d.ellipse([c - 120, c - 110, c + 120, c + 130], fill=RED); d.ellipse([c - 95, c - 85, c + 95, c + 105], fill=(255, 255, 255))
        d.ellipse([c - 150, c - 160, c - 70, c - 80], fill=RED); d.ellipse([c + 70, c - 160, c + 150, c - 80], fill=RED)
        d.line([(c, c + 10), (c, c - 55)], fill=INK, width=10); d.line([(c, c + 10), (c + 45, c + 30)], fill=INK, width=10)
        f = F(POP, 40); d.text((c - 60, c + 140), "5:45", font=f, fill=INK)
    elif kind == "shoes":
        for (x, y, col) in ((c - 20, c - 50, B), (c + 10, c + 70, (60, 160, 120))):
            d.polygon([(x - 150, y + 30), (x - 140, y - 40), (x - 50, y - 55), (x + 10, y - 15), (x + 150, y + 0), (x + 155, y + 30)], fill=col)
            d.rounded_rectangle([x - 158, y + 22, x + 162, y + 58], 16, fill=(250, 250, 250), outline=(210, 210, 215), width=3)
            for k in range(3): d.line([(x - 60 + k * 26, y - 40 + k * 8), (x - 40 + k * 26, y - 20 + k * 8)], fill=(255, 255, 255), width=7)
        d.polygon([(c + 120, c - 170), (c + 132, c - 138), (c + 166, c - 138), (c + 140, c - 118), (c + 150, c - 86), (c + 120, c - 106), (c + 90, c - 86), (c + 100, c - 118), (c + 74, c - 138), (c + 108, c - 138)], fill=Y)
    return im

def prop_scene1(dst, t, kind):
    if kind not in ("bus", "insult", "money"):
        p = prog(t, 0.7, 0.6)
        if p > 0: paste(dst, icon_card(kind), W / 2 + 230, 900 + math.sin(t * 2) * 10, 0.5 + 0.5 * eback(p, 2.2), ease(p), math.sin(t * 1.5) * 3)
        return
    if kind == "bus":
        x = 600 + ease(prog(t, 1.8, 2.6)) * 820
        paste(dst, bus(), x, 860, 1.0, 1.0)
        for k in range(3):
            p = prog(t, 1.9 + k * 0.25, 0.8)
            if 0 < p < 1 and t > 1.8:
                ImageDraw.Draw(dst).ellipse([x - 380 - p * 120 - k * 30, 930 - p * 40, x - 330 - p * 120 - k * 30, 980 - p * 40], fill=(180, 180, 180, int(160 * (1 - p))))
    elif kind == "insult":
        draw_char(dst, t, 860, 980, (110, 110, 118), "point", 0.82, 1.0, cap=False, flip=True)
        p = prog(t, 0.8, 0.4)
        if p > 0: paste(dst, bubble(("#@!&%",), 56, RED, POP, "right"), 830, 640, 0.5 + 0.5 * eback(p, 2.5), ease(p))
    elif kind == "money":
        paste(dst, counter(), W / 2 + 120, 930, 1.0, 1.0)
        p = prog(t, 1.0, 0.5)
        if p > 0:
            paste(dst, banknote("+10 €"), W / 2 + 220, 760 - eout(p) * 40 + math.sin(t * 3) * 8, 0.6 + 0.4 * eback(p, 2.5), ease(p), -8)

# ---------- fases ----------
def phase_hook(dst, t):
    paste(dst, text(CFG["title1"], 84, INK, POP), W / 2, 360 + (1 - eout(prog(t, 0.1, 0.5))) * 20, 1.0, ease(prog(t, 0.1, 0.5)))
    paste(dst, text(CFG["title2"], 84, GREEN, POP), W / 2, 462 + (1 - eout(prog(t, 0.45, 0.5))) * 20, 1.0, ease(prog(t, 0.45, 0.5)))
    prop_scene1(dst, t, CFG["prop"])
    draw_char(dst, t, 230 if CFG["prop"] != "money" else 200, 1330, AHMED_SHIRT, "down", 0.9)
    draw_char(dst, t, 470 if CFG["prop"] != "money" else 420, 1330, GREEN, "down", 0.9)
    p = prog(t, LINES[0][1] - B[0] - 1.8, 0.5)
    if p > 0: paste(dst, pill("¿Quién reacciona mejor?", 46, INK, (247, 242, 231), POP), W / 2, 1680, 0.7 + 0.3 * eback(p, 2), ease(p))

def phase_split(dst, t):       # t absoluto
    tb, tc, td = B[1], B[2], B[3]
    left_active = tb <= t < tc or t >= td
    right_active = t >= tc
    la = 1.0 if (t < tc or t >= td) else 0.45
    ra = 0.35 if t < tc else 1.0
    d = ImageDraw.Draw(dst)
    d.line([(W / 2, 270), (W / 2, 1560)], fill=GOLD + (150,), width=3)
    paste(dst, pill("AHMED", 40, RED), W * 0.25, 320, 1.0, max(la, 0.6))
    paste(dst, pill("BILAL", 40, GREEN), W * 0.75, 320, 1.0, max(ra, 0.6))
    lt = t - tb
    ahmed_mood = CFG.get("ahmed_mood", "angry") if t >= tb + 0.3 else "down"
    if CFG["prop"] == "money": ahmed_mood = "calm" if t >= tb + 0.3 else "down"
    draw_char(dst, lt, W * 0.25, 760, AHMED_SHIRT, ahmed_mood, 0.92, la)
    if CFG["prop"] != "money" and CFG.get("ahmed_symbols", True) and t >= tb + 0.3: angry_symbols(dst, lt, W * 0.25, 430, la)
    if CFG.get("ahmed_bubble") and t >= tb + 0.3:
        p = prog(t, tb + 0.9, 0.4)
        if p > 0: paste(dst, bubble(tuple(CFG["ahmed_bubble"]), 34, RED, POP_M), W * 0.25, 470, 0.5 + 0.5 * eback(p), ease(p) * la)
    if CFG["prop"] == "money" and t >= tb + 0.3:
        paste(dst, banknote(), W * 0.25 + 30, 780, 0.55, la, -10)
        p = prog(t, tb + 0.9, 0.4)
        if p > 0: paste(dst, bubble(("Error suyo,", "no mío"), 34, INK, POP_M), W * 0.25, 470, 0.5 + 0.5 * eback(p), ease(p) * la)
    rt = t - tc
    if right_active:
        calm_glow(dst, rt, W * 0.75, 700, ra)
    bil_mood = CFG.get("bilal_mood", "calm")
    if CFG["prop"] == "money" and right_active: bil_mood = "give"
    if CFG["prop"] == "insult" and right_active: bil_mood = "calm"
    draw_char(dst, rt if right_active else 0, W * 0.75, 760, GREEN, bil_mood, 0.92, ra)
    if right_active and CFG.get("bilal_bubble"):
        p = prog(t, tc + 0.8, 0.4)
        if p > 0: paste(dst, bubble(tuple(CFG["bilal_bubble"]), 34, GREEN, POP_M, "right"), W * 0.75, 470, 0.5 + 0.5 * eback(p), ease(p))
    if CFG["prop"] == "money" and right_active:
        p = eout(prog(t, tc + 0.6, 1.2))
        paste(dst, banknote(), W * 0.75 + 140 - p * 60, 760 - p * 40, 0.5, ra * (1 - prog(t, tc + 1.8, 0.4)))
    # tarjetas
    for x, lines, ok, st, alpha in [(W * 0.25, CFG["ahmed"], False, tb + 0.4, la), (W * 0.75, CFG["bilal"], True, tc + 0.4, ra)]:
        p = prog(t, st, 0.45)
        if p <= 0: continue
        c = card(450, 300)
        paste(dst, c, x, 1250 + (1 - eout(p)) * 40, 1.0, ease(p) * max(alpha, 0.55))
        mark(dst, x, 1100 + (1 - eout(p)) * 40, ok, t, st + 0.15)
        if p > 0.5:
            text_lines(dst, lines, x, 1180, 42, INK, POP_M, 62)
    # frase final
    if t >= td:
        p = prog(t, td + 0.1, 0.5); q = prog(t, td + 0.7, 0.5)
        paste(dst, text(CFG["tag1"], 58, INK, LORA_I), W / 2, 1530 + (1 - eout(p)) * 16, 1.0, ease(p))
        paste(dst, text(CFG["tag2"], 66, GREEN, POP), W / 2, 1620 + (1 - eout(q)) * 16, 1.0, ease(q))

def phase_teach(dst, t):
    t5, t6 = B[4], B[5]
    p = prog(t, t5, 0.5)
    paste(dst, pill("LA ENSEÑANZA", 38, GOLD), W / 2, 330, 0.7 + 0.3 * eback(p, 2), ease(p))
    paste(dst, card(920, 980), W / 2, 950, 1.0, ease(prog(t, t5 + 0.1, 0.5)))
    text_lines(dst, CFG["intro"], W / 2, 520, 48, GREEN, POP, 66, t, [t5 + 0.3 + k * 0.3 for k in range(len(CFG["intro"]))])
    q = CFG["quote"]; n = len(q)
    d6 = LINES[5][1] - LINES[5][0]
    starts = [LINES[5][0] - 0.1 + d6 * CFG.get('reveal', 0.92) * k / n for k in range(n)]
    y0 = 700 if len(CFG["intro"]) > 1 else 650
    text_lines(dst, q, W / 2, y0, 50, INK, LORA_I, 78, t, starts, 0.5)
    ls = min(LINES[5][1] - 0.2, t5 + 1.0) if CFG.get("early_source") else LINES[5][1] - 0.2
    pl = eout(prog(t, ls, 0.6))
    if pl > 0:
        ImageDraw.Draw(dst).line([(W / 2 - 80 * pl, 1360), (W / 2 + 80 * pl, 1360)], fill=GOLD, width=4)
        paste(dst, text(CFG["source"], 38, GREEN, POP_M), W / 2, 1410, 1.0, ease(prog(t, ls + 0.1, 0.5)))

def phase_cta(dst, t):
    t7 = B[6]; lt = t - t7
    paste(dst, text("¿Tú eres más…", 80, INK, POP), W / 2, 420, 1.0, ease(prog(lt, 0.1, 0.5)))
    draw_char(dst, lt, W * 0.28, 880, AHMED_SHIRT, "down", 0.85, ease(prog(lt, 0.3, 0.5)))
    draw_char(dst, lt, W * 0.72, 880, GREEN, "calm", 0.85, ease(prog(lt, 0.6, 0.5)))
    paste(dst, pill("AHMED", 46, RED), W * 0.28, 1230, 0.7 + 0.3 * eback(prog(lt, 0.4, 0.4)), ease(prog(lt, 0.4, 0.4)))
    paste(dst, pill("BILAL", 46, GREEN), W * 0.72, 1230, 0.7 + 0.3 * eback(prog(lt, 0.7, 0.4)), ease(prog(lt, 0.7, 0.4)))
    paste(dst, text("o", 60, GREY, LORA_I), W / 2, 1230, 1.0, ease(prog(lt, 0.6, 0.4)))
    p = prog(lt, 1.6, 0.5)
    if p > 0:
        paste(dst, text("Dímelo en los comentarios", 50, GREEN, POP_M), W / 2, 1420, 1.0, ease(p))
        y = 1500 + 14 * math.sin(lt * 6)
        ImageDraw.Draw(dst).polygon([(W / 2 - 34, y), (W / 2 + 34, y), (W / 2, y + 44)], fill=GOLD + (int(255 * ease(p)),))

def layer_for(t):
    im = BG.copy()
    if t < B[1]: phase_hook(im, t)
    elif t < B[4]: phase_split(im, t)
    elif t < B[6]: phase_teach(im, t)
    else: phase_cta(im, t)
    im.alpha_composite(pill("SITUACIONES DE LA VIDA", 30, INK, (247, 242, 231)), (int(W / 2 - pill("SITUACIONES DE LA VIDA", 30, INK, (247, 242, 231)).width / 2), 130))
    return im

XF = 0.4
def render(t):
    im = layer_for(t)
    for b in (B[1], B[4], B[6]):
        if b <= t < b + XF:
            prev = layer_for(b - 0.001)
            im = Image.blend(prev, im, ease((t - b) / XF))
    a = min(prog(t, 0, 0.3), 1 - prog(t, DUR - 0.5, 0.5))
    if a < 1: im = Image.blend(Image.new("RGBA", (W, H), BG1 + (255,)), im, a)
    return im.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "stills":
        for tt in sys.argv[3:]: render(float(tt)).save(f"still_{float(tt):05.1f}.png")
    else:
        out = sys.argv[3]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out], stdin=subprocess.PIPE)
        nf = int(round(DUR * FPS))
        for f in range(nf): p.stdin.write(render(f / FPS).tobytes())
        p.stdin.close(); p.wait(); print("done", DUR, flush=True)
