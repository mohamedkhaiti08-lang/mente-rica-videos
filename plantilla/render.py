import math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 40.0
NF = int(DUR * FPS)
FD = "/usr/share/fonts/opentype/inter/"
F_BLACK = FD + "InterDisplay-Black.otf"
F_XB = FD + "InterDisplay-ExtraBold.otf"
F_SB = FD + "InterDisplay-SemiBold.otf"

GREEN = (34, 197, 94)
GOLD = (250, 204, 21)
WHITE = (255, 255, 255)
SOFT = (210, 230, 218)
RED = (239, 68, 68)

_font_cache = {}
def font(path, size):
    k = (path, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in_out(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def ease_out_back(t, s=1.7):
    t = clamp(t); t -= 1
    return t * t * ((s + 1) * t + s) + 1
def prog(t, start, dur): return clamp((t - start) / dur)

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def make_bg():
    top = np.array([6, 32, 22], np.float32)
    bot = np.array([2, 8, 6], np.float32)
    g = (yy / H)[..., None]
    img = top * (1 - g) + bot * g
    # vignette
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.6)) ** 2)
    v = clamp_arr(1.15 - d * 0.55)
    img = img * v[..., None]
    return img
def clamp_arr(a): return np.clip(a, 0, 1)
BG = make_bg()

def glow_blob(cx, cy, r, color, strength):
    d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)
    return np.exp(-d2)[..., None] * np.array(color, np.float32) * strength

# precompute two moving glow layers at low res for speed
LW, LH = W // 4, H // 4
lyy, lxx = np.mgrid[0:LH, 0:LW].astype(np.float32)
def bg_frame(t):
    img = np.zeros((LH, LW, 3), np.float32)
    for (bx, by, r, col, s, ph) in [
        (0.25, 0.30, 0.55, GREEN, 0.22, 0.0),
        (0.80, 0.62, 0.50, GOLD, 0.10, 2.0),
        (0.50, 0.95, 0.60, GREEN, 0.14, 4.0),
    ]:
        cx = (bx + 0.06 * math.sin(t * 0.35 + ph)) * LW
        cy = (by + 0.04 * math.cos(t * 0.3 + ph)) * LH
        rr = r * LW
        d2 = ((lxx - cx) ** 2 + (lyy - cy) ** 2) / (rr * rr)
        img += np.exp(-d2)[..., None] * np.array(col, np.float32) * s
    up = np.array(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
    out = np.clip(BG + up, 0, 255).astype(np.uint8)
    return Image.fromarray(out).convert("RGBA")

# subtle grid lines layer
def make_grid():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 7), width=1)
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 7), width=1)
    return g
GRID = make_grid()

# particles
random.seed(7)
PARTS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(2, 5), random.uniform(15, 45), random.uniform(0, 6.28), random.choice([GREEN, GOLD, WHITE])) for _ in range(45)]
def draw_particles(img, t):
    d = ImageDraw.Draw(img)
    for (x, y, r, sp, ph, col) in PARTS:
        py = (y - t * sp) % H
        px = x + 18 * math.sin(t * 0.6 + ph)
        a = int(60 + 60 * math.sin(t * 1.5 + ph))
        d.ellipse([px - r, py - r, px + r, py + r], fill=col + (max(0, a),))

# ---------- helpers ----------
def text_img(txt, size, color=WHITE, path=F_BLACK, stroke=0, stroke_col=(0, 0, 0)):
    f = font(path, size)
    bbox = f.getbbox(txt, stroke_width=stroke)
    asc, desc = f.getmetrics()
    top = int(asc * 0.22)  # trim unused top of em box, keep a shared baseline for all words
    w, h = bbox[2] - bbox[0] + 20, asc + desc - top + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bbox[0], 10 - top), txt, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_col)
    return im

def gradient_text(txt, size, c1, c2, path=F_BLACK):
    mask = text_img(txt, size, (255, 255, 255), path).split()[3]
    w, h = mask.size
    gy = np.linspace(0, 1, h)[:, None]
    arr = np.array(c1, np.float32) * (1 - gy[..., None]) + np.array(c2, np.float32) * gy[..., None]
    arr = np.broadcast_to(arr, (h, w, 3)).astype(np.uint8)
    im = Image.fromarray(arr).convert("RGBA")
    im.putalpha(mask)
    return im

def with_glow(im, color, radius=18, strength=1.0):
    a = im.split()[3]
    g = Image.new("RGBA", im.size, color + (0,))
    g.putalpha(a.point(lambda v: int(v * 0.85 * strength)))
    pad = radius * 3
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    big.alpha_composite(g, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(radius))
    big.alpha_composite(im, (pad, pad))
    return big

def paste_center(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    dst.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

def rounded_card(w, h, r=46, fill=(255, 255, 255, 22), border=(255, 255, 255, 60), bw=3, accent=None):
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], r * s, fill=fill, outline=border, width=bw * s)
    if accent:
        d.rounded_rectangle([bw * s, bw * s, w * s - bw * s, 14 * s], 8 * s, fill=accent + (220,))
    return im.resize((w, h), Image.LANCZOS)

def pop_words(dst, words, cx, cy, size, t, start, stagger=0.12, max_w=900, line_gap=1.12, path=F_BLACK, out_t=None):
    """words: list of (text, color). Word-by-word pop with overshoot, auto line wrap, centered."""
    f = font(path, size)
    space = f.getlength(" ")
    lines, cur, cw = [], [], 0
    for wd in words:
        wl = f.getlength(wd[0])
        if cur and cw + space + wl > max_w:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + wl
        cur.append((wd, wl))
    if cur: lines.append((cur, cw))
    lh = size * line_gap
    y0 = cy - (len(lines) - 1) * lh / 2
    k = 0
    fade = 1.0
    if out_t is not None:
        fade = 1 - ease_in_out(prog(t, out_t, 0.35))
    for li, (ln, lw) in enumerate(lines):
        x = cx - lw / 2
        for (wd, wl) in ln:
            p = prog(t, start + k * stagger, 0.42)
            if p > 0:
                sc = 0.55 + 0.45 * ease_out_back(p, 2.2)
                img = text_img(wd[0], size, wd[1], path)
                if wd[1] != WHITE:
                    img = with_glow(img, wd[1], 14, 0.55)
                yoff = (1 - ease_out_cubic(p)) * 40
                paste_center(dst, img, x + wl / 2, y0 + li * lh + yoff, sc, ease_out_cubic(p * 1.6) * fade)
            x += wl + space
            k += 1

# ---------- Moni (mascot) ----------
S2 = 2  # supersample
def coin_sprite(mouth="smile", eyes="open", brows="normal", arms="down"):
    R = 170
    pad = 150
    size = (R * 2 + pad * 2) * S2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size // 2
    r = R * S2
    def P(v): return int(v * S2)
    # legs & shoes
    for sx in (-1, 1):
        lx = c + sx * P(55)
        d.line([(lx, c + r - P(10)), (lx + sx * P(8), c + r + P(70))], fill=(40, 30, 10), width=P(16))
        d.rounded_rectangle([lx + sx * P(8) - P(40), c + r + P(58), lx + sx * P(8) + P(40), c + r + P(92)], P(18), fill=(22, 163, 74), outline=(255, 255, 255), width=P(4))
    # arms
    def arm(sx, ex, ey):
        sxp = c + sx * (r - P(12))
        syp = c + P(30)
        d.line([(sxp, syp), (ex, ey)], fill=(40, 30, 10), width=P(14))
        d.ellipse([ex - P(28), ey - P(28), ex + P(28), ey + P(28)], fill=(255, 255, 255), outline=(200, 200, 200), width=P(3))
    if arms == "down":
        arm(-1, c - r - P(55), c + P(120)); arm(1, c + r + P(55), c + P(120))
    elif arms == "point":
        arm(-1, c - r - P(55), c + P(120)); arm(1, c + r + P(95), c - P(60))
    elif arms == "up":
        arm(-1, c - r - P(85), c - P(110)); arm(1, c + r + P(85), c - P(110))
    elif arms == "thumb":
        arm(-1, c - r - P(55), c + P(120)); arm(1, c + r + P(90), c - P(30))
        tx, ty = c + r + P(90), c - P(30)
        d.rounded_rectangle([tx - P(10), ty - P(70), tx + P(10), ty - P(10)], P(10), fill=(255, 255, 255), outline=(200, 200, 200), width=P(3))
    # coin rim (darker) and face with radial gradient
    d.ellipse([c - r, c - r, c + r, c + r], fill=(176, 120, 8))
    face = np.zeros((2 * r, 2 * r, 4), np.float32)
    gy, gx = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
    dd = np.sqrt((gx - r * 0.75) ** 2 + (gy - r * 0.7) ** 2) / (r * 1.6)
    c1 = np.array([255, 236, 120], np.float32); c2 = np.array([226, 156, 12], np.float32)
    col = c1 * (1 - np.clip(dd, 0, 1))[..., None] + c2 * np.clip(dd, 0, 1)[..., None]
    rin = r - P(18)
    m = (((gx - r) ** 2 + (gy - r) ** 2) <= rin * rin).astype(np.float32)
    face[..., :3] = col; face[..., 3] = m * 255
    im.alpha_composite(Image.fromarray(face.astype(np.uint8)), (c - r, c - r))
    d = ImageDraw.Draw(im)
    # inner engraved ring
    d.ellipse([c - r + P(38), c - r + P(38), c + r - P(38), c + r - P(38)], outline=(205, 140, 10, 160), width=P(5))
    # highlight
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r + P(45), c - r + P(30), c - P(10), c - r + P(120)], fill=(255, 255, 255, 120))
    hl = hl.filter(ImageFilter.GaussianBlur(P(10)))
    im.alpha_composite(hl)
    d = ImageDraw.Draw(im)
    # sunglasses on top
    gy0 = c - r + P(10)
    for sx in (-1, 1):
        gx0 = c + sx * P(62)
        d.rounded_rectangle([gx0 - P(52), gy0 - P(26), gx0 + P(52), gy0 + P(30)], P(24), fill=(15, 15, 18), outline=(60, 60, 66), width=P(4))
        d.line([(gx0 - P(30), gy0 - P(12)), (gx0 - P(10), gy0 - P(16))], fill=(255, 255, 255, 140), width=P(5))
    d.line([(c - P(12), gy0 - P(6)), (c + P(12), gy0 - P(6))], fill=(15, 15, 18), width=P(8))
    # eyes
    ey = c - P(10)
    for sx in (-1, 1):
        ex = c + sx * P(58)
        if eyes == "open":
            d.ellipse([ex - P(34), ey - P(42), ex + P(34), ey + P(42)], fill=(255, 255, 255), outline=(120, 80, 5), width=P(3))
            d.ellipse([ex - P(18) + P(6), ey - P(18), ex + P(18) + P(6), ey + P(22)], fill=(25, 20, 15))
            d.ellipse([ex - P(4), ey - P(12), ex + P(8), ey], fill=(255, 255, 255))
        elif eyes == "wide":
            d.ellipse([ex - P(40), ey - P(50), ex + P(40), ey + P(50)], fill=(255, 255, 255), outline=(120, 80, 5), width=P(3))
            d.ellipse([ex - P(14), ey - P(14), ex + P(14), ey + P(18)], fill=(25, 20, 15))
            d.ellipse([ex - P(4), ey - P(8), ex + P(6), ey + P(2)], fill=(255, 255, 255))
        else:  # closed
            d.arc([ex - P(32), ey - P(10), ex + P(32), ey + P(30)], 200, 340, fill=(90, 60, 5), width=P(7))
    # brows
    by = ey - P(68) if brows == "raised" else ey - P(56)
    for sx in (-1, 1):
        bx = c + sx * P(58)
        tilt = P(8) if brows == "raised" else P(3)
        d.line([(bx - P(30), by + (tilt if sx < 0 else -tilt) * 0), (bx + P(30), by - (tilt if sx < 0 else -tilt))], fill=(110, 70, 5), width=P(10))
    # cheeks
    for sx in (-1, 1):
        chx = c + sx * P(105)
        ch = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(ch).ellipse([chx - P(26), c + P(40), chx + P(26), c + P(64)], fill=(255, 120, 80, 110))
        im.alpha_composite(ch.filter(ImageFilter.GaussianBlur(P(6))))
    d = ImageDraw.Draw(im)
    # mouth
    my = c + P(70)
    if mouth == "smile":
        d.arc([c - P(55), my - P(40), c + P(55), my + P(30)], 20, 160, fill=(90, 50, 5), width=P(9))
    elif mouth == "open":
        d.chord([c - P(48), my - P(30), c + P(48), my + P(48)], 0, 180, fill=(110, 30, 25), outline=(90, 50, 5), width=P(6))
        d.chord([c - P(26), my + P(12), c + P(26), my + P(44)], 180, 360, fill=(240, 110, 110))
    elif mouth == "mid":
        d.chord([c - P(44), my - P(20), c + P(44), my + P(28)], 0, 180, fill=(110, 30, 25), outline=(90, 50, 5), width=P(6))
    elif mouth == "o":
        d.ellipse([c - P(24), my - P(10), c + P(24), my + P(44)], fill=(110, 30, 25), outline=(90, 50, 5), width=P(6))
    out = im.resize((im.width // S2, im.height // S2), Image.LANCZOS)
    # soft drop shadow handled at composite
    return out

_sprites = {}
def moni(mouth, eyes, brows, arms):
    k = (mouth, eyes, brows, arms)
    if k not in _sprites:
        _sprites[k] = coin_sprite(*k)
    return _sprites[k]

def shadow(dst, cx, cy, w, a):
    sh = Image.new("RGBA", (int(w * 1.6), int(w * 0.5)), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([w * 0.3, w * 0.1, w * 1.3, w * 0.35], fill=(0, 0, 0, int(140 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    dst.alpha_composite(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2)))

# talking windows (when Moni "speaks" = when text is popping in)
TALK = [(0.6, 4.6), (6.4, 11.8), (13.6, 18.5), (21.0, 25.4), (27.4, 32.4), (34.2, 38.4)]
def talking(t): return any(a <= t <= b for a, b in TALK)

def draw_moni(dst, t, cx, cy, scale=1.0, alpha=1.0, mood="normal", arms="down", enter=None):
    bob = math.sin(t * 2.6) * 10
    sq = 1.0
    if enter is not None:
        p = prog(t, enter, 0.6)
        cy += (1 - ease_out_back(p, 1.5)) * 600
        sq = 1 + 0.12 * math.sin(p * math.pi) if p < 1 else 1
        alpha *= ease_out_cubic(p * 2)
    blink = (t % 3.7) < 0.12
    eyes = "closed" if blink else ("wide" if mood == "surprised" else "open")
    brows = "raised" if mood in ("surprised", "sly") else "normal"
    if talking(t):
        ph = int(t * 10) % 4
        mouth = ["open", "mid", "smile", "mid"][ph] if mood != "surprised" else ["o", "open", "o", "mid"][ph]
    else:
        mouth = "o" if mood == "surprised" else "smile"
    sp = moni(mouth, eyes, brows, arms)
    shadow(dst, cx, cy + 260 * scale, 260 * scale, alpha)
    im = sp
    w, h = int(sp.width * scale / sq), int(sp.height * scale * sq)
    im = sp.resize((w, h), Image.LANCZOS)
    rot = math.sin(t * 1.7) * 3
    paste_center(dst, im, cx, cy + bob - (sq - 1) * 100, 1.0, alpha, rot)

# ---------- persistent UI ----------
LOGO = with_glow(gradient_text("MENTE RICA", 40, (255, 240, 150), (226, 156, 12)), GOLD, 10, 0.5)
def draw_ui(dst, t):
    # logo top-left with small coin dot
    d = ImageDraw.Draw(dst)
    d.ellipse([60, 132, 92, 164], fill=GOLD, outline=(176, 120, 8), width=3)
    dst.alpha_composite(LOGO, (86, 104))
    # progress bar
    p = t / DUR
    d.rounded_rectangle([60, 70, W - 60, 78], 4, fill=(255, 255, 255, 40))
    d.rounded_rectangle([60, 70, 60 + int((W - 120) * p), 78], 4, fill=GREEN + (230,))

# ---------- scenes ----------
def price_tag(txt, color=WHITE, size=230, glowc=GREEN):
    return with_glow(text_img(txt, size, color, F_BLACK), glowc, 26, 0.9)

TAG999 = price_tag("9,99€", WHITE, 250, GREEN)
TAG10 = price_tag("10€", WHITE, 250, GOLD)

def scene1(dst, t):  # 0-6 hook
    st = 0.0
    pop_words(dst, [("¿Por", WHITE), ("qué", WHITE), ("casi", WHITE), ("todo", WHITE), ("cuesta", WHITE)], W / 2, 430, 84, t, st + 0.5, out_t=5.6)
    p = prog(t, 1.4, 0.55)
    if p > 0:
        sc = ease_out_back(p, 2.4)
        fade = 1 - ease_in_out(prog(t, 5.6, 0.35))
        wob = math.sin(t * 3) * 2
        paste_center(dst, TAG999, W / 2, 680, sc, fade, wob)
    pop_words(dst, [("y", WHITE), ("no", WHITE), ("10€?", GOLD)], W / 2, 900, 84, t, 2.4, out_t=5.6)
    draw_moni(dst, t, W / 2, 1320, 1.05, 1.0, "surprised", "up", enter=0.3)

def scene2(dst, t):  # 6-13 brain trick
    a = 6.0
    pop_words(dst, [("No", WHITE), ("es", WHITE), ("casualidad.", GREEN)], W / 2, 380, 92, t, a + 0.2, out_t=12.6)
    pop_words(dst, [("Tu", WHITE), ("cerebro", WHITE), ("lee", WHITE), ("de", WHITE), ("izquierda", GOLD), ("a", WHITE), ("derecha", GOLD)], W / 2, 560, 72, t, a + 1.3, out_t=12.6)
    # card with 9,99 and scanning highlight
    p = prog(t, a + 2.4, 0.5)
    if p > 0:
        fade = 1 - ease_in_out(prog(t, 12.6, 0.35))
        card = rounded_card(760, 300)
        layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
        layer.alpha_composite(card)
        num = text_img("9,99€", 190, WHITE, F_BLACK)
        nx, ny = (card.width - num.width) // 2, (card.height - num.height) // 2
        # highlight the first digit after scan
        sp = prog(t, a + 3.1, 1.3)
        dd = ImageDraw.Draw(layer)
        scanx = nx + int(sp * num.width)
        if sp > 0:
            dd.rounded_rectangle([nx + 10, 40, nx + 10 + int(min(1, sp * 4) * 135), card.height - 40], 24, fill=GREEN + (90,))
        layer.alpha_composite(num, (nx, ny))
        if 0 < sp < 1:
            dd.line([(scanx, 30), (scanx, card.height - 30)], fill=GOLD + (230,), width=8)
        paste_center(dst, layer, W / 2, 830, 0.8 + 0.2 * ease_out_back(p), ease_out_cubic(p) * fade)
    pop_words(dst, [("…y", WHITE), ("se", WHITE), ("queda", WHITE), ("con", WHITE), ("el", WHITE), ("PRIMER", GREEN), ("número", GREEN)], W / 2, 1060, 66, t, a + 4.6, out_t=12.6)
    draw_moni(dst, t, W / 2, 1390, 0.85, 1.0, "sly", "point")

def scene3(dst, t):  # 13-20 comparison
    a = 13.2
    fade = 1 - ease_in_out(prog(t, 20.0, 0.35))
    for i, (txt, col, gx, lab, lc) in enumerate([("9,99€", WHITE, W / 2 - 250, "PARECE BARATO", GREEN), ("10€", WHITE, W / 2 + 250, "PARECE CARO", RED)]):
        p = prog(t, a + 0.3 + i * 0.35, 0.55)
        if p <= 0: continue
        card = rounded_card(400, 380, accent=lc)
        layer = card.copy()
        n = text_img(txt, 108, col, F_BLACK)
        layer.alpha_composite(n, ((card.width - n.width) // 2, 95))
        l = text_img(lab, 40, lc, F_XB)
        layer.alpha_composite(l, ((card.width - l.width) // 2, 285))
        paste_center(dst, layer, gx, 560 + (1 - ease_out_back(p)) * 120, 1.0, ease_out_cubic(p) * fade)
    p = prog(t, a + 1.6, 0.5)
    if p > 0:
        vs = with_glow(text_img("VS", 70, GOLD, F_BLACK), GOLD, 12, 0.8)
        paste_center(dst, vs, W / 2, 800, ease_out_back(p, 2.5), fade)
    pop_words(dst, [("La", WHITE), ("diferencia", WHITE), ("es", WHITE), ("de", WHITE), ("solo", WHITE)], W / 2, 930, 76, t, a + 2.3, out_t=20.0)
    # counter 1 céntimo
    p = prog(t, a + 3.2, 0.9)
    if p > 0:
        val = int(round(ease_out_cubic(p) * 1))
        cnt = with_glow(text_img(f"{val} céntimo", 120, GOLD, F_BLACK), GOLD, 20, 0.8)
        paste_center(dst, cnt, W / 2, 1080, 0.7 + 0.3 * ease_out_back(prog(t, a + 3.2, 0.5), 2), fade)
    draw_moni(dst, t, W / 2, 1400, 0.8, 1.0, "normal", "up")

def tag_shape(txt, col):
    s = 2
    w, h = 470 * s, 170 * s
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(60 * s, 0), (w, 0), (w, h), (60 * s, h), (0, h // 2)], fill=col)
    d.ellipse([34 * s, h // 2 - 16 * s, 66 * s, h // 2 + 16 * s], fill=(10, 30, 20))
    im = im.resize((w // s, h // s), Image.LANCZOS)
    tx = text_img(txt, 92, (10, 30, 20), F_BLACK)
    im.alpha_composite(tx, (90 + (380 - tx.width) // 2, (im.height - tx.height) // 2))
    return im
OFERTA = tag_shape("OFERTA", GOLD)
OFERTA2 = tag_shape("-50%", GREEN)
OFERTA3 = tag_shape("CHOLLO", (250, 120, 60))

def scene4(dst, t):  # 20-26 always looks like a deal
    a = 20.4
    fade = 1 - ease_in_out(prog(t, 26.2, 0.35))
    pop_words(dst, [("Además,", WHITE), ("el", WHITE), (",99", GOLD), ("siempre", WHITE), ("parece", WHITE), ("una", WHITE)], W / 2, 400, 78, t, a, out_t=26.2)
    for i, (im, x, y, r) in enumerate([(OFERTA, W / 2, 660, -6), (OFERTA2, W / 2 - 170, 860, 8), (OFERTA3, W / 2 + 170, 1030, -10)]):
        p = prog(t, a + 1.0 + i * 0.45, 0.5)
        if p > 0:
            sw = math.sin(t * 2.2 + i) * 3
            paste_center(dst, with_glow(im, GOLD, 14, 0.35), x, y, 0.4 + 0.6 * ease_out_back(p, 2.6), fade, r + sw)
    p = prog(t, a + 3.2, 0.4)
    if p > 0:
        st = with_glow(text_img("…aunque NO lo sea", 70, WHITE, F_XB), RED, 12, 0.6)
        paste_center(dst, st, W / 2, 1210, 0.7 + 0.3 * ease_out_back(p, 2), ease_out_cubic(p) * fade)
        # strike line through tags
        sp = prog(t, a + 3.6, 0.4)
        if sp > 0:
            d = ImageDraw.Draw(dst)
            x0, y0, x1, y1 = W / 2 - 330, 1080, W / 2 + 330, 620
            d.line([(x0, y0), (x0 + (x1 - x0) * sp, y0 + (y1 - y0) * sp)], fill=RED + (int(230 * fade),), width=16)
    draw_moni(dst, t, 190, 1370, 0.66, 1.0, "sly", "down")

def scene5(dst, t):  # 26-33 tip
    a = 26.6
    fade = 1 - ease_in_out(prog(t, 33.4, 0.35))
    p = prog(t, a, 0.5)
    if p > 0:
        card = rounded_card(900, 760, accent=GREEN, fill=(255, 255, 255, 18))
        paste_center(dst, card, W / 2, 760, 0.85 + 0.15 * ease_out_back(p), ease_out_cubic(p) * fade)
        badge = with_glow(text_img("✓ TRUCO", 58, (10, 30, 20), F_BLACK), GREEN, 1, 0)
        bb = Image.new("RGBA", (badge.width + 40, badge.height + 10), (0, 0, 0, 0))
        ImageDraw.Draw(bb).rounded_rectangle([0, 0, bb.width - 1, bb.height - 1], 30, fill=GREEN)
        bb.alpha_composite(badge, (20, 5))
        paste_center(dst, bb, W / 2, 450, ease_out_back(p, 2), fade)
    pop_words(dst, [("Redondea", WHITE), ("siempre", WHITE), ("hacia", WHITE), ("ARRIBA", GREEN)], W / 2, 600, 76, t, a + 0.6, out_t=33.4, max_w=780)
    # morph 19,99 -> 20
    p1 = prog(t, a + 1.8, 0.45)
    if p1 > 0:
        mp = prog(t, a + 2.9, 0.6)
        old = text_img("19,99€", 130, (200, 200, 200), F_BLACK)
        new = with_glow(text_img("20€", 150, GOLD, F_BLACK), GOLD, 18, 0.8)
        paste_center(dst, old, W / 2, 770 - ease_in_out(mp) * 40, 1.0, ease_out_cubic(p1) * (1 - ease_in_out(mp)) * fade)
        paste_center(dst, new, W / 2, 790, 0.6 + 0.4 * ease_out_back(mp, 2.4), ease_out_cubic(mp) * fade)
        ar = text_img("→", 80, GREEN, F_BLACK)
    pop_words(dst, [("y", WHITE), ("pregúntate:", WHITE), ("¿de", GOLD), ("verdad", GOLD), ("lo", GOLD), ("necesito?", GOLD)], W / 2, 990, 62, t, a + 3.8, out_t=33.4, max_w=780)
    draw_moni(dst, t, W / 2, 1400, 0.72, 1.0, "normal", "point")

def scene6(dst, t):  # 33.6-40 outro
    a = 33.8
    pop_words(dst, [("Sígueme", WHITE), ("para", WHITE), ("tener", WHITE), ("una", WHITE)], W / 2, 420, 82, t, a)
    p = prog(t, a + 0.8, 0.6)
    if p > 0:
        big = with_glow(gradient_text("MENTE RICA", 150, (255, 244, 170), (230, 160, 10)), GOLD, 24, 0.9)
        paste_center(dst, big, W / 2, 590, 0.5 + 0.5 * ease_out_back(p, 2.2), ease_out_cubic(p))
    p = prog(t, a + 2.0, 0.5)
    if p > 0:
        btn = Image.new("RGBA", (560, 130), (0, 0, 0, 0))
        ImageDraw.Draw(btn).rounded_rectangle([0, 0, 559, 129], 65, fill=GREEN)
        tx = text_img("+ SEGUIR", 64, (10, 30, 20), F_BLACK)
        btn.alpha_composite(tx, ((560 - tx.width) // 2, (130 - tx.height) // 2))
        pulse = 1 + 0.04 * math.sin(t * 6)
        paste_center(dst, with_glow(btn, GREEN, 20, 0.7), W / 2, 790, (0.5 + 0.5 * ease_out_back(p, 2.4)) * pulse, ease_out_cubic(p))
    pop_words(dst, [("Comenta", WHITE), ("qué", WHITE), ("tema", WHITE), ("quieres", WHITE), ("mañana", GREEN)], W / 2, 980, 68, t, a + 2.7)
    p = prog(t, a + 3.6, 0.4)
    if p > 0:
        d = ImageDraw.Draw(dst)
        yy0 = 1080 + 18 * math.sin(t * 6)
        d.polygon([(W / 2 - 40, yy0), (W / 2 + 40, yy0), (W / 2, yy0 + 50)], fill=GOLD + (int(255 * ease_out_cubic(p)),))
    draw_moni(dst, t, W / 2, 1390, 0.85, 1.0, "normal", "thumb")

SCENES = [(0, 6.0, scene1), (6.0, 13.0, scene2), (13.0, 20.4, scene3), (20.4, 26.6, scene4), (26.6, 33.8, scene5), (33.8, 40.0, scene6)]

def flash(dst, t):
    for s, e, _ in SCENES[1:]:
        dt = t - s
        if 0 <= dt < 0.25:
            a = int(70 * (1 - dt / 0.25))
            ov = Image.new("RGBA", (W, H), (255, 255, 255, a))
            dst.alpha_composite(ov)

def render_frame(t):
    img = bg_frame(t)
    img.alpha_composite(GRID)
    draw_particles(img, t)
    # camera zoom per scene
    for s, e, fn in SCENES:
        if s <= t < e or (fn is scene6 and t >= s):
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            fn(layer, t)
            z = 1 + 0.03 * ((t - s) / (e - s))
            if z != 1:
                lw, lh = int(W * z), int(H * z)
                layer = layer.resize((lw, lh), Image.BILINEAR).crop(((lw - W) // 2, (lh - H) // 2, (lw - W) // 2 + W, (lh - H) // 2 + H))
            img.alpha_composite(layer)
            break
    draw_ui(img, t)
    flash(img, t)
    return img.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    if mode == "stills":
        for tt in [float(x) for x in sys.argv[2:]]:
            render_frame(tt).save(f"still_{tt:05.1f}.png")
    else:
        out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=44100:cl=stereo",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(NF):
            p.stdin.write(render_frame(i / FPS).tobytes())
            if i % 150 == 0: print(i, flush=True)
        p.stdin.close(); p.wait()
