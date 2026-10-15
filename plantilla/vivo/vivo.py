# Mente Rica – estilo "VIVO" (colores vivos, look sticker, más energía)
# Módulo base: cada vídeo importa esto y define sus escenas.
import math, random, subprocess, sys
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/"
F_BLACK = FD + "InterDisplay-Black.otf"
F_XB = FD + "InterDisplay-ExtraBold.otf"

# paleta viva
YELLOW = (255, 222, 0)
CYAN = (0, 229, 255)
LIME = (170, 255, 30)
PINK = (255, 70, 170)
ORANGE = (255, 140, 0)
RED = (255, 55, 70)
WHITE = (255, 255, 255)
INK = (18, 10, 40)          # "negro" violeta para bordes y sombras

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in_out(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def ease_out_back(t, s=1.7):
    t = clamp(t); t -= 1
    return t * t * ((s + 1) * t + s) + 1
def prog(t, start, dur): return clamp((t - start) / dur)

# ---------- fondo: degradado violeta → rosa, manchas de luz y rayos giratorios ----------
LW, LH = W // 4, H // 4
lyy, lxx = np.mgrid[0:LH, 0:LW].astype(np.float32)
TOP = np.array([92, 30, 230], np.float32)
BOT = np.array([235, 40, 150], np.float32)
_g = (lyy / LH)[..., None]
BASE = TOP * (1 - _g) + BOT * _g
RCX, RCY = LW / 2, LH * 0.70
THETA = np.arctan2(lyy - RCY, lxx - RCX)
RDIST = np.sqrt((lxx - RCX) ** 2 + (lyy - RCY) ** 2) / LH

def bg_frame(t):
    img = BASE.copy()
    for (bx, by, r, col, s, ph) in [(0.15, 0.18, 0.45, CYAN, 0.45, 0.0), (0.88, 0.40, 0.42, YELLOW, 0.30, 2.0), (0.30, 0.92, 0.50, ORANGE, 0.30, 4.0)]:
        cx = (bx + 0.07 * math.sin(t * 0.5 + ph)) * LW
        cy = (by + 0.05 * math.cos(t * 0.4 + ph)) * LH
        rr = r * LW
        d2 = ((lxx - cx) ** 2 + (lyy - cy) ** 2) / (rr * rr)
        img = img * (1 - np.exp(-d2)[..., None] * s) + np.array(col, np.float32) * np.exp(-d2)[..., None] * s
    rays = (np.sin(THETA * 14 + t * 0.6) > 0.25).astype(np.float32) * np.exp(-RDIST * 1.4) * 0.16
    img = img + rays[..., None] * 255
    up = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return up.convert("RGBA")

# confeti
random.seed(11)
CONF = [(random.uniform(0, W), random.uniform(0, H), random.uniform(8, 16), random.uniform(40, 110), random.uniform(0, 6.28),
         random.choice([YELLOW, CYAN, LIME, WHITE, PINK]), random.choice(["r", "c"])) for _ in range(34)]
def draw_confetti(img, t):
    d = ImageDraw.Draw(img)
    for (x, y, s, sp, ph, col, kind) in CONF:
        py = (y + t * sp) % H
        px = x + 25 * math.sin(t * 0.8 + ph)
        a = 150
        if kind == "c":
            d.ellipse([px - s / 2, py - s / 2, px + s / 2, py + s / 2], fill=col + (a,))
        else:
            ang = t * 2 + ph
            w2 = s * abs(math.cos(ang)) / 2 + 1
            d.polygon([(px - w2, py - s / 3), (px + w2, py - s / 3), (px + w2, py + s / 3), (px - w2, py + s / 3)], fill=col + (a,))

# ---------- texto estilo sticker ----------
@lru_cache(maxsize=4096)
def text_img(txt, size, color=WHITE, path=F_BLACK, stroke=None, shadow=True):
    if stroke is None: stroke = max(4, size // 11)
    f = font(path, size)
    bbox = f.getbbox(txt, stroke_width=stroke)
    asc, desc = f.getmetrics()
    top = int(asc * 0.18)
    sh = int(size * 0.09) if shadow else 0
    pad = 10 + stroke
    w, h = bbox[2] - bbox[0] + pad * 2, asc + desc - top + pad * 2 + sh
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = pad - bbox[0], pad - top
    if shadow:
        d.text((ox, oy + sh), txt, font=f, fill=INK + (200,), stroke_width=stroke, stroke_fill=INK + (200,))
    d.text((ox, oy), txt, font=f, fill=color, stroke_width=stroke, stroke_fill=INK)
    return im

def paste_center(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1.0) > 0.002:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    dst.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

def layout_words(words, size, max_w, path=F_BLACK):
    f = font(path, size); space = f.getlength(" ") + size * 0.08
    lines, cur, cw = [], [], 0
    for wd in words:
        wl = f.getlength(wd[0]) + size * 0.12
        if cur and cw + space + wl > max_w:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + wl
        cur.append((wd, wl))
    if cur: lines.append((cur, cw))
    return lines, space

def pop_words(dst, words, cx, cy, size, t, start, stagger=0.10, max_w=920, line_gap=1.16, path=F_BLACK, out_t=None):
    """words: list of (texto, color). Aparición palabra a palabra con rebote y ligero giro."""
    lines, space = layout_words(words, size, max_w, path)
    lh = size * line_gap
    y0 = cy - (len(lines) - 1) * lh / 2
    fade = 1.0 if out_t is None else 1 - ease_in_out(prog(t, out_t, 0.3))
    k = 0
    for li, (ln, lw) in enumerate(lines):
        x = cx - lw / 2
        for (wd, wl) in ln:
            p = prog(t, start + k * stagger, 0.38)
            if p > 0:
                sc = 0.3 + 0.7 * ease_out_back(p, 3.0)
                rot = (1 - ease_out_cubic(p)) * (12 if k % 2 else -12)
                img = text_img(wd[0], size, wd[1], path, 0, False) if wd[1] == INK else text_img(wd[0], size, wd[1], path)
                paste_center(dst, img, x + wl / 2, y0 + li * lh, sc, min(1, p * 3) * fade, rot)
            x += wl + space
            k += 1

@lru_cache(maxsize=256)
def sticker_card(w, h, fill=WHITE, r=44, bw=7, sh=16):
    im = Image.new("RGBA", (w + sh, h + sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([sh, sh, w + sh - 1, h + sh - 1], r, fill=INK + (210,))
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=fill, outline=INK, width=bw)
    return im

def badge(txt, size, fill, color=INK):
    t = text_img(txt, size, color, F_BLACK, stroke=0, shadow=False)
    w, h = t.width + 50, t.height + 16
    c = sticker_card(w, h, fill, r=h // 2, bw=6, sh=10).copy()
    c.alpha_composite(t, (25, 8))
    return c

# ---------- iconos sencillos ----------
def icon_canvas(w, h): return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def ink_poly(d, pts, fill, bw=7):
    d.polygon(pts, fill=fill, outline=INK)
    d.line(pts + [pts[0]], fill=INK, width=bw, joint="curve")

# ---------- Moni ----------
S2 = 2
def coin_sprite(mouth="smile", eyes="open", brows="normal", arms="down"):
    R = 170; pad = 150
    size = (R * 2 + pad * 2) * S2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size // 2; r = R * S2
    def P(v): return int(v * S2)
    for sx in (-1, 1):
        lx = c + sx * P(55)
        d.line([(lx, c + r - P(10)), (lx + sx * P(8), c + r + P(70))], fill=INK, width=P(16))
        d.rounded_rectangle([lx + sx * P(8) - P(40), c + r + P(58), lx + sx * P(8) + P(40), c + r + P(92)], P(18), fill=CYAN, outline=INK, width=P(5))
    def arm(sx, ex, ey):
        d.line([(c + sx * (r - P(12)), c + P(30)), (ex, ey)], fill=INK, width=P(14))
        d.ellipse([ex - P(28), ey - P(28), ex + P(28), ey + P(28)], fill=WHITE, outline=INK, width=P(5))
    if arms == "down":
        arm(-1, c - r - P(55), c + P(120)); arm(1, c + r + P(55), c + P(120))
    elif arms == "point":
        arm(-1, c - r - P(55), c + P(120)); arm(1, c + r + P(95), c - P(60))
    elif arms == "up":
        arm(-1, c - r - P(85), c - P(110)); arm(1, c + r + P(85), c - P(110))
    elif arms == "wave":
        arm(-1, c - r - P(55), c + P(120)); arm(1, c + r + P(70), c - P(130))
    d.ellipse([c - r - P(6), c - r - P(6), c + r + P(6), c + r + P(6)], fill=INK)
    d.ellipse([c - r, c - r, c + r, c + r], fill=(196, 128, 0))
    gy, gx = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
    dd = np.sqrt((gx - r * 0.75) ** 2 + (gy - r * 0.7) ** 2) / (r * 1.6)
    c1 = np.array([255, 245, 120], np.float32); c2 = np.array([255, 170, 0], np.float32)
    col = c1 * (1 - np.clip(dd, 0, 1))[..., None] + c2 * np.clip(dd, 0, 1)[..., None]
    rin = r - P(18)
    m = (((gx - r) ** 2 + (gy - r) ** 2) <= rin * rin).astype(np.float32)
    face = np.zeros((2 * r, 2 * r, 4), np.float32); face[..., :3] = col; face[..., 3] = m * 255
    im.alpha_composite(Image.fromarray(face.astype(np.uint8)), (c - r, c - r))
    d = ImageDraw.Draw(im)
    d.ellipse([c - r + P(38), c - r + P(38), c + r - P(38), c + r - P(38)], outline=(225, 150, 0, 170), width=P(5))
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r + P(45), c - r + P(30), c - P(10), c - r + P(120)], fill=(255, 255, 255, 140))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(P(10))))
    d = ImageDraw.Draw(im)
    gy0 = c - r + P(10)
    for sx in (-1, 1):
        gx0 = c + sx * P(62)
        d.rounded_rectangle([gx0 - P(52), gy0 - P(26), gx0 + P(52), gy0 + P(30)], P(24), fill=(255, 40, 150), outline=INK, width=P(5))
        d.line([(gx0 - P(30), gy0 - P(12)), (gx0 - P(10), gy0 - P(16))], fill=(255, 255, 255, 190), width=P(5))
    d.line([(c - P(12), gy0 - P(6)), (c + P(12), gy0 - P(6))], fill=INK, width=P(8))
    ey = c - P(10)
    for sx in (-1, 1):
        ex = c + sx * P(58)
        if eyes == "open":
            d.ellipse([ex - P(34), ey - P(42), ex + P(34), ey + P(42)], fill=WHITE, outline=INK, width=P(4))
            d.ellipse([ex - P(12), ey - P(18), ex + P(24), ey + P(22)], fill=INK)
            d.ellipse([ex - P(4), ey - P(12), ex + P(8), ey], fill=WHITE)
        elif eyes == "wide":
            d.ellipse([ex - P(40), ey - P(50), ex + P(40), ey + P(50)], fill=WHITE, outline=INK, width=P(4))
            d.ellipse([ex - P(14), ey - P(14), ex + P(14), ey + P(18)], fill=INK)
            d.ellipse([ex - P(4), ey - P(8), ex + P(6), ey + P(2)], fill=WHITE)
        elif eyes == "happy":
            d.arc([ex - P(32), ey - P(20), ex + P(32), ey + P(30)], 200, 340, fill=INK, width=P(9))
        else:
            d.arc([ex - P(32), ey - P(10), ex + P(32), ey + P(30)], 200, 340, fill=INK, width=P(7))
    by = ey - P(68) if brows == "raised" else ey - P(56)
    for sx in (-1, 1):
        bx = c + sx * P(58)
        tilt = P(8) if brows == "raised" else P(3)
        d.line([(bx - P(30), by), (bx + P(30), by - (tilt if sx < 0 else -tilt))], fill=INK, width=P(10))
    for sx in (-1, 1):
        chx = c + sx * P(105)
        ch = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(ch).ellipse([chx - P(28), c + P(38), chx + P(28), c + P(66)], fill=(255, 80, 140, 150))
        im.alpha_composite(ch.filter(ImageFilter.GaussianBlur(P(6))))
    d = ImageDraw.Draw(im)
    my = c + P(70)
    if mouth == "smile":
        d.chord([c - P(55), my - P(30), c + P(55), my + P(40)], 0, 180, fill=(120, 20, 40), outline=INK, width=P(6))
        d.chord([c - P(30), my + P(12), c + P(30), my + P(40)], 180, 360, fill=(255, 110, 130))
    elif mouth == "open":
        d.chord([c - P(52), my - P(34), c + P(52), my + P(54)], 0, 180, fill=(120, 20, 40), outline=INK, width=P(6))
        d.chord([c - P(28), my + P(16), c + P(28), my + P(50)], 180, 360, fill=(255, 110, 130))
    elif mouth == "mid":
        d.chord([c - P(46), my - P(22), c + P(46), my + P(32)], 0, 180, fill=(120, 20, 40), outline=INK, width=P(6))
    elif mouth == "o":
        d.ellipse([c - P(26), my - P(10), c + P(26), my + P(48)], fill=(120, 20, 40), outline=INK, width=P(6))
    return im.resize((im.width // S2, im.height // S2), Image.LANCZOS)

@lru_cache(maxsize=None)
def moni(mouth, eyes, brows, arms): return coin_sprite(mouth, eyes, brows, arms)

@lru_cache(maxsize=8)
def shadow_img(w):
    sh = Image.new("RGBA", (int(w * 1.6), int(w * 0.5)), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([w * 0.3, w * 0.1, w * 1.3, w * 0.35], fill=INK + (130,))
    return sh.filter(ImageFilter.GaussianBlur(14))

TALK = []
def talking(t): return any(a <= t <= b for a, b in TALK)

def draw_moni(dst, t, cx, cy, scale=1.0, alpha=1.0, mood="happy", arms="down", enter=None, jump=False):
    bob = math.sin(t * 3.2) * 12
    if jump: bob -= abs(math.sin(t * 5.0)) * 45
    sq = 1.0
    if enter is not None:
        p = prog(t, enter, 0.55)
        cy += (1 - ease_out_back(p, 1.6)) * 650
        sq = 1 + 0.14 * math.sin(p * math.pi) if p < 1 else 1
        alpha *= ease_out_cubic(p * 2)
    blink = (t % 3.3) < 0.12
    if mood == "surprised": eyes = "wide"
    elif mood == "happy" and not talking(t): eyes = "happy"
    else: eyes = "open"
    if blink and eyes != "happy": eyes = "closed"
    brows = "raised" if mood in ("surprised", "sly") else "normal"
    if talking(t):
        ph = int(t * 11) % 4
        mouth = ["open", "mid", "smile", "mid"][ph] if mood != "surprised" else ["o", "open", "o", "mid"][ph]
    else:
        mouth = "o" if mood == "surprised" else "smile"
    sp = moni(mouth, eyes, brows, arms)
    sw = int(260 * scale)
    shi = shadow_img(sw)
    dst.alpha_composite(shi, (int(cx - shi.width / 2), int(cy + 260 * scale - shi.height / 2)))
    w, h = int(sp.width * scale / sq), int(sp.height * scale * sq)
    im = sp.resize((w, h), Image.BILINEAR)
    paste_center(dst, im, cx, cy + bob - (sq - 1) * 100, 1.0, alpha, math.sin(t * 2.2) * 5)

# ---------- UI fija ----------
LOGO = text_img("MENTE RICA", 44, YELLOW, F_BLACK)
def draw_ui(dst, t, dur):
    d = ImageDraw.Draw(dst)
    d.ellipse([58, 128, 96, 166], fill=YELLOW, outline=INK, width=5)
    d.text((70, 131), "€", font=font(F_BLACK, 26), fill=INK)
    dst.alpha_composite(LOGO, (98, 110))
    p = clamp(t / dur)
    d.rounded_rectangle([60, 64, W - 60, 82], 9, fill=(255, 255, 255, 70), outline=INK, width=4)
    if p > 0.01:
        d.rounded_rectangle([62, 66, 62 + int((W - 124) * p), 80], 7, fill=YELLOW)

# ---------- motor ----------
def make_renderer(SCENES, DUR):
    def flash(dst, t):
        for s, e, _ in SCENES[1:]:
            dt = t - s
            if 0 <= dt < 0.2:
                dst.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(90 * (1 - dt / 0.2)))))
    def render_frame(t):
        img = bg_frame(t)
        draw_confetti(img, t)
        for i, (s, e, fn) in enumerate(SCENES):
            if s <= t < e or (i == len(SCENES) - 1 and t >= s):
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                fn(layer, t)
                punch = 0.06 * (1 - ease_out_cubic(prog(t, s, 0.3))) if i > 0 else 0
                z = 1 + 0.025 * ((t - s) / (e - s)) + punch
                lw, lh = int(W * z), int(H * z)
                layer = layer.resize((lw, lh), Image.BILINEAR).crop(((lw - W) // 2, (lh - H) // 2, (lw - W) // 2 + W, (lh - H) // 2 + H))
                img.alpha_composite(layer)
                break
        draw_ui(img, t, DUR)
        flash(img, t)
        return img.convert("RGB")
    return render_frame

def main(SCENES, DUR):
    render_frame = make_renderer(SCENES, DUR)
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    if mode == "stills":
        for tt in [float(x) for x in sys.argv[2:]]:
            render_frame(tt).save(f"still_{tt:05.1f}.png")
    else:
        out = sys.argv[2]
        nf = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=44100:cl=stereo",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(nf):
            p.stdin.write(render_frame(i / FPS).tobytes())
            if i % 150 == 0: print(i, flush=True)
        p.stdin.close(); p.wait()

# ---------- escenas comunes ----------
def scene_truco(dst, t, a, end, lines1, lines2, moni_arms="point"):
    """Tarjeta TRUCO: lines1 grande dentro de la tarjeta, lines2 debajo."""
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    p = prog(t, a, 0.45)
    if p > 0:
        card = sticker_card(920, 720, (255, 255, 255, 235))
        paste_center(dst, card, W / 2, 760, 0.8 + 0.2 * ease_out_back(p, 2), ease_out_cubic(p) * fade)
        paste_center(dst, badge("✓ TRUCO", 64, LIME), W / 2, 420, ease_out_back(prog(t, a + 0.15, 0.45), 2.5), fade, math.sin(t * 4) * 3)
    pop_words(dst, lines1, W / 2, 650, 80, t, a + 0.6, out_t=end - 0.35, max_w=800)
    pop_words(dst, lines2, W / 2, 930, 68, t, a + 2.2, out_t=end - 0.35, max_w=800)
    draw_moni(dst, t, W / 2, 1400, 0.74, 1.0, "happy", moni_arms, jump=True)

def scene_outro(dst, t, a):
    pop_words(dst, [("Sígueme", WHITE), ("para", WHITE), ("tener", WHITE), ("una", WHITE)], W / 2, 400, 84, t, a)
    p = prog(t, a + 0.8, 0.5)
    if p > 0:
        big = text_img("MENTE RICA", 150, YELLOW, F_BLACK)
        paste_center(dst, big, W / 2, 580, (0.4 + 0.6 * ease_out_back(p, 2.6)) * (1 + 0.03 * math.sin(t * 5)), ease_out_cubic(p), math.sin(t * 3) * 2)
    p = prog(t, a + 1.8, 0.45)
    if p > 0:
        btn = badge("+ SEGUIR", 76, PINK, WHITE)
        paste_center(dst, btn, W / 2, 790, (0.4 + 0.6 * ease_out_back(p, 2.6)) * (1 + 0.06 * math.sin(t * 7)), ease_out_cubic(p))
    pop_words(dst, [("Comenta", WHITE), ("qué", WHITE), ("tema", WHITE), ("quieres", WHITE), ("mañana", CYAN)], W / 2, 990, 70, t, a + 2.6)
    p = prog(t, a + 3.4, 0.4)
    if p > 0:
        d = ImageDraw.Draw(dst)
        y0 = 1085 + 18 * math.sin(t * 7)
        d.polygon([(W / 2 - 44, y0), (W / 2 + 44, y0), (W / 2, y0 + 54)], fill=YELLOW, outline=INK, width=6)
    draw_moni(dst, t, W / 2, 1390, 0.86, 1.0, "happy", "wave", jump=True)
