# Motor de vídeos verticales (estilo noche verde y oro, subtítulos karaoke sincronizados con la voz).
# Uso: python3 motor.py config.json stills t1 t2 ...   |   python3 motor.py config.json video salida.mp4
# config.json: {"label": "...", "times": "tiempos.json", "tail": 1.6, "scenes": [ {...}, ... ]}
#   cada escena = una frase de la voz: {"cap": texto en pantalla de la frase, "hi": [palabras en oro],
#   "title": ["línea 1", "línea 2"], "tint": "green|red|gold|night|blue", "vis": {"type": ...}}
import math, json, sys, os, random, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POP_M = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POP_SB = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
LORA_I = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
BLACK_F = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
GOLD = (236, 196, 110); GOLD_D = (190, 145, 60); CREAM = (250, 244, 228); WHITE = (255, 255, 255)
DIM = (150, 160, 150); RED = (225, 80, 70); GREEN_D = (16, 70, 52)

CFG = json.load(open(sys.argv[1]))
BASE = os.path.dirname(os.path.abspath(sys.argv[1]))
LINES = json.load(open(os.path.join(BASE, CFG["times"])))
SC = CFG["scenes"]
assert len(SC) == len(LINES), f"{len(SC)} escenas vs {len(LINES)} frases"
B = [0.0] + [LINES[i][0] - min(0.25, (LINES[i][0] - LINES[i - 1][1]) / 2) for i in range(1, len(LINES))]
DUR = round(LINES[-1][1] + CFG.get("tail", 1.6), 2)
B.append(DUR)

@lru_cache(maxsize=None)
def F(p, s): return ImageFont.truetype(p, s)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def eback(t, s=1.7): t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def prog(t, s, d): return clamp((t - s) / d)

def paste(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    dst.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

# ---------- texto ----------
@lru_cache(maxsize=2048)
def text(txt, size, col=WHITE, path=POP, shadow=True, glow=None):
    f = F(path, size); bb = f.getbbox(txt); asc, desc = f.getmetrics(); pad = 30
    im = Image.new("RGBA", (bb[2] - bb[0] + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - bb[0], pad + 4), txt, font=f, fill=(0, 0, 0, 190))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text((pad - bb[0], pad), txt, font=f, fill=glow + (150,))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(im).text((pad - bb[0], pad), txt, font=f, fill=col)
    return im

def fit_size(lines, size, path, maxw=940):
    while size > 30 and max(F(path, size).getlength(l) for l in lines) > maxw: size -= 2
    return size

@lru_cache(maxsize=None)
def gold_text(txt, size, path=BLACK_F):
    """texto grande con degradado dorado"""
    f = F(path, size); bb = f.getbbox(txt); pad = 40
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255)
    yy = np.linspace(0, 1, h)[:, None]
    c1, c2 = np.array((255, 230, 150), float), np.array((205, 140, 45), float)
    arr = (c1 * (1 - yy[..., None]) + c2 * yy[..., None]) * np.ones((h, w, 1))
    im = Image.fromarray(arr.astype(np.uint8)).convert("RGBA"); im.putalpha(m)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(m.point(lambda v: int(v * 0.7)))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 0))
    gl = Image.new("RGBA", (w, h), (255, 190, 80, 0)); gl.putalpha(m.point(lambda v: int(v * 0.45)))
    out.alpha_composite(gl.filter(ImageFilter.GaussianBlur(22)))
    out.alpha_composite(im)
    return out

@lru_cache(maxsize=None)
def emoji(ch, size=160):
    f = F(EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    s = size / max(im.width, im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

@lru_cache(maxsize=64)
def pill(txt, size, fill=(10, 40, 30, 220), col=GOLD, outline=GOLD):
    f = F(POP, size); tw = f.getlength(txt) + len(txt) * size * 0.12
    w, h = int(tw + size * 2.2), int(size * 2.1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, w - 2, h - 2], h // 2, fill=fill, outline=outline + (200,), width=2)
    x = size * 1.1
    for ch in txt:
        d.text((x, h / 2), ch, font=f, fill=col, anchor="lm"); x += f.getlength(ch) + size * 0.12
    return im

@lru_cache(maxsize=32)
def card(w, h, fill=(14, 62, 46, 235), outline=GOLD, r=34):
    im = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([40, 52, w + 40, h + 52], r, fill=(0, 0, 0, 120))
    im = im.filter(ImageFilter.GaussianBlur(16))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 40, w + 40, h + 40], r, fill=fill, outline=outline + (190,), width=3)
    return im

# ---------- fondos ----------
TINTS = {
    "green": ((8, 44, 36), (3, 16, 14), (60, 150, 110)),
    "red":   ((74, 18, 22), (18, 6, 10), (200, 80, 60)),
    "gold":  ((60, 46, 16), (14, 12, 6), (230, 170, 80)),
    "night": ((10, 22, 40), (3, 6, 14), (80, 120, 180)),
    "blue":  ((10, 40, 56), (3, 12, 18), (70, 150, 180)),
    "stone": ((40, 34, 30), (10, 9, 8), (170, 130, 90)),
}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

@lru_cache(maxsize=None)
def bg(tint):
    c1, c2, gl = TINTS[tint]
    g = ((yy / H) ** 0.9)[..., None]
    arr = np.array(c1, np.float32) * (1 - g) + np.array(c2, np.float32) * g
    e = np.exp(-(((xx - W * 0.5) ** 2 + (yy - H * 0.38) ** 2) / (620 ** 2)))[..., None]
    arr = arr + np.array(gl, np.float32) * e * 0.22
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # patrón geométrico (estrella de 8 puntas) muy suave
    pat = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(pat); s = 170
    for gy in range(0, H + s, s):
        for gx in range(0, W + s, s):
            r = s * 0.30
            for base in (0, 45):
                pts = [(gx + r * math.cos(math.radians(a + base)), gy + r * math.sin(math.radians(a + base))) for a in (0, 90, 180, 270)]
                d.polygon(pts, outline=GOLD + (16,))
    im.alpha_composite(pat)
    return im

@lru_cache(maxsize=None)
def rays_layer(k):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rnd = random.Random(k)
    for i in range(9):
        a = math.radians(60 + i * 7.5 + rnd.uniform(-2, 2)); wd = rnd.uniform(0.6, 1.6)
        x2, y2 = W / 2 + math.cos(a) * 2600, -60 + math.sin(a) * 2600
        a1, a2 = a - math.radians(wd), a + math.radians(wd)
        d.polygon([(W / 2, -60), (W / 2 + math.cos(a1) * 2600, -60 + math.sin(a1) * 2600), (W / 2 + math.cos(a2) * 2600, -60 + math.sin(a2) * 2600)], fill=(255, 240, 200, 26))
    return lay.filter(ImageFilter.GaussianBlur(10))

@lru_cache(maxsize=None)
def orb(r, col=(255, 236, 180)):
    S = int(r * 6); im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([S / 2 - r * 2.2, S / 2 - r * 2.2, S / 2 + r * 2.2, S / 2 + r * 2.2], fill=col + (60,))
    im = im.filter(ImageFilter.GaussianBlur(r * 0.8)); d = ImageDraw.Draw(im)
    d.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], fill=col + (255,))
    return im

random.seed(7)
PARTS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4.5), random.uniform(8, 30), random.uniform(0, 6.28)) for _ in range(90)]
vig = np.clip(np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.48) / (H * 0.6)) ** 2) - 0.45, 0, 1)
VIG = Image.fromarray((np.clip(vig * 1.6, 0, 1) * 200).astype(np.uint8), "L")
BLACK = Image.new("RGBA", (W, H), (0, 0, 0, 255))

def background(tint, t, gt):
    im = bg(tint).copy()
    a = 0.6 + 0.4 * math.sin(gt * 0.8)
    r1 = rays_layer(1); r2 = rays_layer(2)
    im.alpha_composite(Image.blend(r1, r2, a))
    d = ImageDraw.Draw(im, "RGBA")
    c3 = TINTS[tint][2]
    for k, (yb, al) in enumerate([(H * 0.80, 70), (H * 0.86, 110), (H * 0.93, 160)]):
        pts = [(x, yb + 28 * math.sin(x / 210 + gt * (0.5 + k * 0.2) + k * 2)) for x in range(0, W + 30, 30)]
        col = tuple(int(c * 0.25) for c in c3) + (al,)
        d.polygon(pts + [(W, H), (0, H)], fill=col)
    for (x, y, r, sp, ph) in PARTS:
        py = (y - gt * sp) % H; px = x + 18 * math.sin(gt * 0.5 + ph)
        al = int(110 + 90 * math.sin(gt * 2 + ph))
        d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 225, 150, max(0, al)))
    return im

# ---------- visuales ----------
def badge(dst, t, cx, cy, ch, size=300, start=0.15, ring=True):
    p = prog(t, start, 0.5)
    if p <= 0: return
    s = 0.3 + 0.7 * eback(p, 2.2); fl = math.sin(t * 2.2) * 12
    if ring:
        r = size * 0.78
        lay = Image.new("RGBA", (int(r * 2 + 80), int(r * 2 + 80)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        c = lay.width / 2
        d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 210, 120, 40))
        lay = lay.filter(ImageFilter.GaussianBlur(20)); d = ImageDraw.Draw(lay)
        d.ellipse([c - r * 0.92, c - r * 0.92, c + r * 0.92, c + r * 0.92], outline=GOLD + (170,), width=4)
        ang = t * 60
        d.arc([c - r, c - r, c + r, c + r], ang, ang + 70, fill=GOLD + (255,), width=6)
        paste(dst, lay, cx, cy + fl, s, ease(p))
    paste(dst, emoji(ch, size), cx, cy + fl, s, ease(p), math.sin(t * 1.7) * 4)

def v_emoji(dst, t, dur, v):
    cy = v.get("y", 900)
    badge(dst, t, W / 2, cy, v["e"], v.get("size", 300))
    for k, ch in enumerate(v.get("orbit", [])):
        p = prog(t, 0.5 + k * 0.25, 0.5)
        if p <= 0: continue
        a = t * 0.9 + k * 2 * math.pi / max(1, len(v["orbit"]))
        paste(dst, emoji(ch, 120), W / 2 + math.cos(a) * 330, cy + math.sin(a) * 250, 0.4 + 0.6 * eback(p), ease(p))

def v_counter(dst, t, dur, v):
    seq = v["seq"]; n = len(seq); step = max(0.45, (dur - 0.6) / n)
    i = min(n - 1, int(max(0, t - 0.2) / step)); lt = t - 0.2 - i * step
    p = prog(lt, 0, 0.35)
    col_red = i == n - 1 and v.get("last_red")
    im = gold_text(seq[i], 250) if not col_red else text(seq[i], 230, RED, BLACK_F, True, RED)
    paste(dst, im, W / 2, v.get("y", 880), 0.6 + 0.4 * eback(p, 2.4), 1.0, (math.sin(t * 30) * 2 if col_red else 0))
    if v.get("sub"):
        paste(dst, text(v["sub"], 44, GOLD, POP, True), W / 2, v.get("y", 880) + 190, 1.0, ease(prog(t, 0.3, 0.4)))
    if v.get("e"):
        paste(dst, emoji(v["e"], 150), W / 2 + 330, v.get("y", 880) - 170 + math.sin(t * 3) * 10, 1.0, ease(prog(t, 0.2, 0.4)), 12)

def v_steps(dst, t, dur, v):
    items = v["items"]; n = len(items); cy = v.get("y", 920)
    xs = [CFG.get("cx", W / 2) + (k - (n - 1) / 2) * CFG.get("step_gap", 320) for k in range(n)]
    st = [0.1 + k * (dur - 0.6) / n for k in range(n)]
    d = ImageDraw.Draw(dst, "RGBA")
    for k in range(n - 1):
        p = eout(prog(t, st[k + 1] - 0.3, 0.4))
        if p > 0: d.line([(xs[k] + 120, cy), (xs[k] + 120 + (xs[k + 1] - xs[k] - 240) * p, cy)], fill=GOLD + (220,), width=5)
    for k, (ch, lab) in enumerate(items):
        p = prog(t, st[k], 0.45)
        if p <= 0: continue
        last = k == n - 1
        r = 115
        lay = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        dd.ellipse([150 - r, 150 - r, 150 + r, 150 + r], fill=(60, 14, 16, 235) if last else (12, 52, 40, 235), outline=(RED if last else GOLD) + (255,), width=5)
        lay.alpha_composite(emoji(ch, 120), (90, 90))
        paste(dst, lay, xs[k], cy, 0.4 + 0.6 * eback(p, 2.2), ease(p))
        paste(dst, text(lab, 40, RED if last else GOLD, POP), xs[k], cy + 170, 1.0, ease(prog(t, st[k] + 0.2, 0.4)))

def v_quote(dst, t, dur, v):
    lines = v["lines"]; n = len(lines); size = fit_size(lines, v.get("size", 54), POP, 800)
    gap = int(size * 1.38); hh = n * gap + 260; cy = v.get("y", 860)
    p = prog(t, 0.0, 0.45)
    paste(dst, card(900, hh), W / 2, cy, 0.9 + 0.1 * eout(p), ease(p))
    paste(dst, text("“", 120, GOLD, LORA_I, False), W / 2, cy - hh / 2 + 70, 1.0, ease(p))
    y0 = cy - hh / 2 + 165
    rev = v.get("reveal", 0.9)
    for k, ln in enumerate(lines):
        st = 0.25 + (dur - 0.5) * rev * k / n
        q = prog(t, st, 0.45)
        a = 0.28 + 0.72 * ease(q)
        paste(dst, text(ln, size, CREAM if q < 1 or k != n - 1 else CREAM, POP), W / 2, y0 + k * gap + (1 - eout(q)) * 10, 1.0, a * ease(p))
    q = prog(t, v.get("src_at", 0.4), 0.5)
    paste(dst, text(v["src"], 34, GOLD, POP, False), W / 2, cy + hh / 2 - 60, 1.0, ease(q) * ease(p))

def v_book(dst, t, dur, v):
    badge(dst, t, W / 2, v.get("y", 900), "📖", 280)
    paste(dst, pill(v["src"], 34), W / 2, v.get("y", 900) + 300, 0.6 + 0.4 * eback(prog(t, 0.4, 0.4)), ease(prog(t, 0.4, 0.4)))

def v_big(dst, t, dur, v):
    p = prog(t, 0.1, 0.5)
    words = v["words"]; cy = v.get("y", 880)
    for k, wd in enumerate(words):
        q = prog(t, 0.1 + k * 0.35, 0.45)
        paste(dst, gold_text(wd, v.get("size", 170)), W / 2, cy + k * v.get("gap", 190) - (len(words) - 1) * v.get("gap", 190) / 2, 0.5 + 0.5 * eback(q, 2.4), ease(q), -3 if k % 2 else 3)
    if v.get("e"):
        badge(dst, t, W / 2, cy + 330, v["e"], 160, 0.6, ring=False)

def v_cta(dst, t, dur, v):
    cy = v.get("y", 860)
    paste(dst, gold_text(v["word"], v.get("size", 190)), W / 2, cy, 0.5 + 0.5 * eback(prog(t, 0.1, 0.5), 2.2), ease(prog(t, 0.1, 0.5)), -4)
    if v.get("e"):
        badge(dst, t, W / 2, cy - 300, v["e"], 170, 0.3, ring=False)
    q = prog(t, 0.7, 0.4)
    if q > 0:
        y = cy + 200 + 16 * math.sin(t * 6)
        ImageDraw.Draw(dst, "RGBA").polygon([(W / 2 - 40, y), (W / 2 + 40, y), (W / 2, y + 52)], fill=GOLD + (int(255 * ease(q)),))

# --- cueva (para historias) ---
@lru_cache(maxsize=None)
def cave_img():
    im = Image.new("RGBA", (W, 1700), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    # roca/ montaña
    pts = [(0, 1700), (0, 420)]
    for x in range(0, W + 60, 60): pts.append((x, 300 + 120 * math.sin(x / 260) + rnd.uniform(-25, 25)))
    pts += [(W, 1700)]
    d.polygon(pts, fill=(44, 38, 34, 255))
    d.rectangle([0, 1180, W, 1700], fill=(30, 26, 23, 255))
    d.polygon([(0, 1180)] + [(x, 1180 + 30 * math.sin(x / 140)) for x in range(0, W + 40, 40)] + [(W, 1180)], fill=(30, 26, 23, 255))
    # boca de la cueva (oscura)
    d.ellipse([W / 2 - 250, 520, W / 2 + 250, 1220], fill=(8, 7, 7, 255))
    for k in range(40):
        x = rnd.uniform(40, W - 40); y = rnd.uniform(380, 1150); r = rnd.uniform(6, 22)
        if (x - W / 2) ** 2 / 250 ** 2 + (y - 870) ** 2 / 350 ** 2 < 1.1: continue
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(58, 50, 44, 255))
    return im

@lru_cache(maxsize=None)
def boulder():
    im = Image.new("RGBA", (560, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rnd = random.Random(9); pts = []
    for k in range(18):
        a = k / 18 * 2 * math.pi; r = 240 + rnd.uniform(-22, 18)
        pts.append((280 + math.cos(a) * r, 280 + math.sin(a) * r * 0.92))
    d.polygon(pts, fill=(96, 84, 74, 255))
    d.polygon([(p[0] * 0.92 + 10, p[1] * 0.92 + 4) for p in pts], fill=(112, 98, 86, 255))
    for k in range(7):
        x, y = rnd.uniform(140, 420), rnd.uniform(140, 420)
        d.line([(x, y), (x + rnd.uniform(-60, 60), y + rnd.uniform(20, 60))], fill=(74, 64, 56, 255), width=5)
    return im

def v_cave(dst, t, dur, v):
    y0 = v.get("y", 420)
    a0, a1 = v.get("open", [0, 0])
    o = a0 + (a1 - a0) * ease(prog(t, v.get("at", 0.4), 1.4))
    shake = math.sin(t * 50) * 6 if 0 < prog(t, v.get("at", 0.4), 1.4) < 1 and a1 != a0 else 0
    # luz que entra
    if o > 0.02:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.ellipse([W / 2 - 260, y0 + 500, W / 2 + 260, y0 + 1220], fill=(255, 220, 150, int(200 * min(1, o * 1.5))))
        dst.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
    paste(dst, cave_img(), W / 2, y0 + 850)
    if o > 0.02:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.ellipse([W / 2 - 230, y0 + 540, W / 2 + 230, y0 + 1190], fill=(255, 226, 160, int(235 * min(1, o * 1.4))))
        dst.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40)))
        rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(rays)
        for k in range(7):
            ang = math.radians(200 + k * 20 + math.sin(t + k) * 3)
            dr.polygon([(W / 2, y0 + 870), (W / 2 + math.cos(ang - 0.05) * 900, y0 + 870 + math.sin(ang - 0.05) * 900), (W / 2 + math.cos(ang + 0.05) * 900, y0 + 870 + math.sin(ang + 0.05) * 900)], fill=(255, 220, 150, int(40 * min(1, o * 1.4))))
        dst.alpha_composite(rays.filter(ImageFilter.GaussianBlur(12)))
    paste(dst, boulder(), W / 2 + o * 470 + shake, y0 + 880, 1.0, 1.0, -o * 60)
    for k, ch in enumerate(v.get("people", [])):
        paste(dst, emoji(ch, 90), W / 2 - 90 + k * 90, y0 + 1130 - abs(math.sin(t * 3 + k)) * 6, 1.0, ease(prog(t, 0.2 + k * 0.15, 0.4)))
    if v.get("e"):
        badge(dst, t, W / 2 + v.get("ex", 300), y0 + v.get("ey", 330), v["e"], 150, 0.5, ring=True)


# --- barrotes de cárcel que caen sobre el emoji ---
def v_bars(dst, t, dur, v):
    cy = v.get("y", 900)
    badge(dst, t, W / 2, cy, v["e"], v.get("size", 280), 0.1, ring=v.get("ring", True))
    p = eout(prog(t, v.get("at", 0.6), 0.6))
    if p <= 0: return
    shake = math.sin(t * 40) * 5 * (1 - prog(t, v.get("at", 0.6) + 0.6, 0.4)) if p >= 1 else 0
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    top = cy - 330; bot = cy + 330; yb = top - (1 - p) * 900
    x0, x1 = W / 2 - 330, W / 2 + 330
    d.rectangle([x0 - 20, yb - 10, x1 + 20, yb + 22], fill=(70, 74, 80, 255), outline=(30, 30, 34, 255), width=3)
    d.rectangle([x0 - 20, yb + (bot - top) - 22, x1 + 20, yb + (bot - top) + 10], fill=(70, 74, 80, 255), outline=(30, 30, 34, 255), width=3)
    for k in range(7):
        x = x0 + k * (x1 - x0) / 6
        d.rounded_rectangle([x - 13, yb, x + 13, yb + (bot - top)], 10, fill=(110, 116, 124, 255), outline=(40, 40, 46, 255), width=3)
        d.line([(x - 5, yb + 6), (x - 5, yb + (bot - top) - 6)], fill=(170, 176, 184, 255), width=4)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.alpha_composite(lay)
    dst.alpha_composite(lay, (int(shake), 0))

# --- dos opciones (dilema): tarjetas izquierda/derecha ---
def v_choice(dst, t, dur, v):
    cy = v.get("y", 900); opts = v["opts"]; pick = v.get("pick", -1)
    for k, (ch, lab, col) in enumerate(opts):
        p = prog(t, 0.15 + k * 0.35, 0.45)
        if p <= 0: continue
        cx = CFG.get("cx", W / 2) + (-1 if k == 0 else 1) * 235
        c = RED if col == "red" else GOLD
        fill = (60, 14, 16, 235) if col == "red" else (12, 52, 40, 235)
        lay = Image.new("RGBA", (420, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([10, 10, 410, 510], 40, fill=fill, outline=c + (255,), width=5)
        lay.alpha_composite(emoji(ch, 170), (210 - emoji(ch, 170).width // 2, 90))
        tx = text(lab, fit_size([lab], 52, POP, 340), c, POP)
        lay.alpha_composite(tx, (210 - tx.width // 2, 330))
        sc = 0.5 + 0.5 * eback(p, 2.0)
        if pick == k: sc *= 1 + 0.05 * math.sin(t * 5)
        a = ease(p) * (0.45 if (pick >= 0 and pick != k and t > 1.2) else 1.0)
        paste(dst, lay, cx, cy + math.sin(t * 2 + k) * 10, sc, a, (-4 if k == 0 else 4))
    q = prog(t, 0.5, 0.4)
    if q > 0: paste(dst, gold_text("VS", 110), CFG.get("cx", W / 2), cy, 0.5 + 0.5 * eback(q, 2.4), ease(q))

# --- camisa rota por detrás ---
def v_shirt(dst, t, dur, v):
    cy = v.get("y", 900)
    badge(dst, t, W / 2, cy, "👕", 300, 0.1)
    p = eout(prog(t, v.get("at", 0.7), 0.5))
    if p > 0:
        d = ImageDraw.Draw(dst, "RGBA")
        pts = [(W / 2 - 10, cy - 60), (W / 2 + 18, cy - 20), (W / 2 - 14, cy + 20), (W / 2 + 16, cy + 60), (W / 2 - 6, cy + 100)]
        n = 1 + int(p * (len(pts) - 1))
        d.line(pts[:n], fill=(40, 10, 10, 255), width=12, joint="curve")
        d.line(pts[:n], fill=RED + (255,), width=5, joint="curve")
    if v.get("tag"):
        q = prog(t, v.get("at", 0.7) + 0.4, 0.4)
        paste(dst, pill(v["tag"], 36, (60, 14, 16, 230), CREAM, RED), W / 2, cy + 300, 0.6 + 0.4 * eback(q), ease(q))


# --- Ahmed vs Bilal: dos personajes sin cara (mismo dibujo que situaciones2) ---
SKIN = (224, 184, 150); AHMED_SHIRT = (88, 108, 140); BILAL_SHIRT = (22, 128, 92)
@lru_cache(maxsize=64)
def character(shirt, mood="calm", arms_phase=0, scale=1.0):
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
    elif mood == "point":
        d.line([(cx - S(85), S(250)), (cx - S(110), S(380))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(240)), (cx + S(190), S(170))], fill=shirt, width=aw)
        d.ellipse([cx - S(136), S(360), cx - S(84), S(410)], fill=SKIN); d.ellipse([cx + S(174), S(144), cx + S(226), S(196)], fill=SKIN)
    else:
        d.line([(cx - S(85), S(250)), (cx - S(110), S(380))], fill=shirt, width=aw)
        d.line([(cx + S(85), S(250)), (cx + S(110), S(380))], fill=shirt, width=aw)
        d.ellipse([cx - S(136), S(360), cx - S(84), S(410)], fill=SKIN); d.ellipse([cx + S(84), S(360), cx + S(136), S(410)], fill=SKIN)
    d.ellipse([cx - S(70), S(40), cx + S(70), S(180)], fill=SKIN)
    d.chord([cx - S(68), S(36), cx + S(68), S(140)], 180, 360, fill=(250, 250, 250))
    im = im.resize((w // s, h // s), Image.LANCZOS)
    out = Image.new("RGBA", (im.width, im.height + 24), (0, 0, 0, 0))
    sh = Image.new("RGBA", (im.width, 44), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([40, 6, im.width - 40, 38], fill=(0, 0, 0, 110))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (0, im.height - 24)); out.alpha_composite(im)
    return out

@lru_cache(maxsize=64)
def bubble(lines, size=38, col=(34, 40, 49), tail="left"):
    ts = [text(l, size, col, POP, False) for l in lines]
    w = max(t.width for t in ts) + 10; lh = int(size * 1.3); h = lh * len(ts) + 50
    im = Image.new("RGBA", (w + 40, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 10, w + 20, h + 10], 34, fill=(255, 255, 255, 250))
    tx = 80 if tail == "left" else w - 40
    d.polygon([(tx - 18, h + 8), (tx + 18, h + 8), (tx + (-12 if tail == "left" else 12), h + 50)], fill=(255, 255, 255, 250))
    y = 10 + 25 - 30
    for t_ in ts:
        im.alpha_composite(t_, (int(20 + (w - t_.width) / 2), y)); y += lh
    return im

def v_duo(dst, t, dur, v):
    cy = v.get("y", 900); focus = v.get("focus", "both")
    for k, (name, shirt, x) in enumerate((("ahmed", AHMED_SHIRT, 300), ("bilal", BILAL_SHIRT, 740))):
        if v.get("only") and v["only"] != name: continue
        on = focus in ("both", name)
        a = (1.0 if on else 0.32) * ease(prog(t, 0.05 + k * 0.15, 0.4))
        mood = v.get(name, "down")
        if on and mood == "calm":
            lay = Image.new("RGBA", (520, 520), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
            r = 190 + 14 * math.sin(t * 2); dd.ellipse([260 - r, 260 - r, 260 + r, 260 + r], fill=(255, 220, 140, 70))
            dst.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40)), (x - 260, int(cy - 330)))
        ph = int(t * 6) % 2 if mood == "angry" else 0
        dx = math.sin(t * 40) * 5 if mood == "angry" else math.sin(t * 1.5) * 3
        paste(dst, character(shirt, mood, ph, 0.86), x + dx, cy + math.sin(t * 2.4) * 3, 1.0, a)
        col = RED if name == "ahmed" else (60, 190, 130)
        paste(dst, pill(name.upper(), 34, (60, 14, 16, 230) if name == "ahmed" else (12, 52, 40, 235), CREAM, col), x, cy + 300, 1.0, a)
        b = v.get(name[0] + "b")
        if b and on:
            p = prog(t, v.get("bat", 0.5), 0.4)
            paste(dst, bubble(tuple(b), 36, RED if name == "ahmed" else (22, 128, 92), "left" if k == 0 else "right"), x + (40 if k == 0 else -90), cy - 340, 0.5 + 0.5 * eback(p), ease(p))
        m = v.get(name[0] + "m")
        if m and on:
            p = prog(t, v.get("mat", 0.8), 0.4)
            if p > 0:
                paste(dst, emoji(m, 110), x + 125, cy - 170, 0.4 + 0.6 * eback(p, 2.4), ease(p), math.sin(t * 6) * 6)
        if name == "ahmed" and mood == "angry" and on:
            paste(dst, text("#@!", 70, RED, POP), x, cy - 330 if not b else cy - 520, 1 + 0.12 * abs(math.sin(t * 7)), a, math.sin(t * 9) * 6)
    if focus == "both" and v.get("vs", True):
        q = prog(t, 0.4, 0.4)
        if q > 0: paste(dst, gold_text("VS", 100), 520, cy, 0.5 + 0.5 * eback(q, 2.4), ease(q))
    for k, ch in enumerate(v.get("extra", [])):
        p = prog(t, 0.6 + k * 0.2, 0.4)
        if p > 0:
            a_ = t * 1.2 + k * 2.1
            paste(dst, emoji(ch, 90), 520 + math.cos(a_) * 120, cy - 420 + math.sin(a_) * 50, 0.4 + 0.6 * eback(p), ease(p))

VIS = {"duo": v_duo, "emoji": v_emoji, "counter": v_counter, "steps": v_steps, "quote": v_quote, "book": v_book,
       "big": v_big, "cta": v_cta, "cave": v_cave, "bars": v_bars, "choice": v_choice, "shirt": v_shirt}

# ---------- subtítulos karaoke ----------
def word_times(i):
    words = SC[i]["cap"].split(); s, e = LINES[i]
    wts = [len(w.strip("¿?¡!,.…«»")) + 2 for w in words]; tot = sum(wts); out = []; acc = s
    for w, k in zip(words, wts):
        d = (e - s) * k / tot; out.append((w, acc, acc + d)); acc += d
    return out

@lru_cache(maxsize=None)
def cap_layout(i):
    words = SC[i]["cap"].split(); size = SC[i].get("cap_size", 64); f = F(POP, size); maxw = CFG.get("cap_maxw", 900)
    while True:
        rows, cur = [], []
        for w in words:
            if cur and f.getlength(" ".join(cur + [w])) + f.getlength(" ") * 0.25 * len(cur) > maxw: rows.append(cur); cur = [w]
            else: cur.append(w)
        rows.append(cur)
        if len(rows) <= 3 or size <= 44: break
        size -= 4; f = F(POP, size)
    return rows, size

def draw_caption(dst, i, gt):
    rows, size = cap_layout(i); f = F(POP, size); sp = f.getlength(" ") * 1.25
    wt = word_times(i); k = 0; hi = set(x.strip("¿?¡!,.…«»").lower() for x in SC[i].get("hi", []))
    lh = int(size * 1.3); y0 = SC[i].get("cap_y", 1440) - (len(rows) - 1) * lh / 2
    for r, row in enumerate(rows):
        widths = [f.getlength(w) for w in row]; total = sum(widths) + sp * (len(row) - 1)
        x = CFG.get("cx", W / 2) - total / 2
        for w, wd in zip(row, widths):
            _, ws, we = wt[k]; k += 1
            bare = w.strip("¿?¡!,.…«»").lower()
            said = gt >= ws; cur = ws <= gt < we + 0.05
            col = GOLD if bare in hi and said else (WHITE if said else DIM)
            a = 1.0 if said else 0.55
            sc = 1.0 + 0.05 * (1 - eout(prog(gt, ws, 0.25))) if said else 1.0
            im = text(w, size, col, POP, True, GOLD if (bare in hi and said) else None)
            paste(dst, im, x + wd / 2, y0 + r * lh - (6 if cur else 0), sc, a)
            x += wd + sp

# ---------- composición ----------
def draw_title(dst, sc, lt):
    tl = sc.get("title")
    if not tl: return
    size = fit_size(tl, sc.get("title_size", 78), POP, CFG.get("title_maxw", 960))
    y = sc.get("title_y", 330)
    for k, ln in enumerate(tl):
        p = prog(lt, 0.05 + k * 0.22, 0.45)
        col = GOLD if k % 2 else WHITE
        im = text(ln, size, col, POP, True, GOLD if k % 2 else None)
        paste(dst, im, CFG.get("cx", W / 2), y + k * int(size * 1.15) + (1 - eout(p)) * 30, 0.85 + 0.15 * eback(p, 2), ease(p))

def scene_layer(i, gt):
    sc = SC[i]; lt = gt - B[i]; dur = B[i + 1] - B[i]
    if i == 0 and CFG.get("instant"): lt += 0.7   # el primer fotograma ya sale con texto y gancho
    im = background(sc.get("tint", "green"), lt, gt)
    v = sc.get("vis")
    if v: VIS[v["type"]](im, lt, dur, v)
    draw_title(im, sc, lt)
    if not sc.get("nocap"): draw_caption(im, i, gt)
    return im

LABEL = pill(CFG["label"], 30)
XF = 0.3
def render(gt):
    i = max(k for k in range(len(SC)) if B[k] <= gt) if gt < DUR else len(SC) - 1
    im = scene_layer(i, gt)
    if i > 0 and gt - B[i] < XF:
        prev = scene_layer(i - 1, gt)
        im = Image.blend(prev, im, ease((gt - B[i]) / XF))
    im = Image.composite(BLACK, im, VIG)
    paste(im, LABEL, W / 2, 175)
    # barra de progreso
    bar = Image.new("RGBA", (W - 100, 30), (0, 0, 0, 0)); d = ImageDraw.Draw(bar)
    d.rounded_rectangle([10, 10, W - 110, 18], 4, fill=(255, 255, 255, 45))
    d.rounded_rectangle([10, 10, 10 + (W - 120) * clamp(gt / DUR), 18], 4, fill=GOLD + (235,))
    im.alpha_composite(bar, (50, H - 80))
    a = min(1.0 if CFG.get("instant") else prog(gt, 0, 0.12), 1 - prog(gt, DUR - 0.5, 0.5))
    if a < 1: im = Image.blend(BLACK, im, a)
    return im.convert("RGB")

def render_chunk(args):
    f0, f1, out = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1): p.stdin.write(render(f / FPS).tobytes())
    p.stdin.close(); p.wait(); return out

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "stills":
        for tt in sys.argv[3:]: render(float(tt)).save(os.path.join(BASE, f"still_{float(tt):05.2f}.png"))
    elif mode == "info":
        print(json.dumps({"dur": DUR, "bounds": B}))
    else:
        out = sys.argv[3]; nf = int(round(DUR * FPS)); n = os.cpu_count() or 4
        step = math.ceil(nf / n); tmp = os.path.join(BASE, "_parts")
        os.makedirs(tmp, exist_ok=True)
        jobs = [(k, min(nf, k + step), os.path.join(tmp, f"p{k:06d}.mp4")) for k in range(0, nf, step)]
        with Pool(n) as pool: parts = pool.map(render_chunk, jobs)
        lst = os.path.join(tmp, "list.txt")
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
        print("done", DUR, out)
