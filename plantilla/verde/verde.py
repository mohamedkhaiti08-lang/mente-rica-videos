# Mente Rica – estilo VERDE (moderno, sin mascota)
# Cada escena se renderiza como un clip independiente de CLIP segundos.
# Todas las entradas ocurren en los primeros ~2,5 s y luego la escena "respira",
# así el clip se puede recortar o alargar para encajar con la voz sin desincronizarse.
import math, random, subprocess, sys, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
CLIP = 8.0
FD = "/usr/share/fonts/opentype/inter/"
F_BLACK = FD + "InterDisplay-Black.otf"
F_XB = FD + "InterDisplay-ExtraBold.otf"
F_B = FD + "InterDisplay-Bold.otf"
F_SB = FD + "InterDisplay-SemiBold.otf"
F_M = FD + "InterDisplay-Medium.otf"

WHITE = (255, 255, 255)
MUTED = (170, 205, 188)
MINT = (52, 211, 153)
EMERALD = (16, 185, 129)
LIME = (190, 242, 100)
DEEP = (4, 22, 15)
CORAL = (251, 113, 133)

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_out_quint(t): t = clamp(t); return 1 - (1 - t) ** 5
def ease_in_out(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def ease_out_back(t, s=1.4):
    t = clamp(t); t -= 1
    return t * t * ((s + 1) * t + s) + 1
def prog(t, start, dur): return clamp((t - start) / dur)

# ---------- fondo ----------
LW, LH = W // 4, H // 4
lyy, lxx = np.mgrid[0:LH, 0:LW].astype(np.float32)
_g = (lyy / LH)[..., None]
BASE = np.array([3, 26, 18], np.float32) * (1 - _g) + np.array([2, 12, 9], np.float32) * _g

def make_dots():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(30, H, 60):
        for x in range(30, W, 60):
            d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(160, 255, 210, 22))
    return g
DOTS = make_dots()

def bg_frame(T):
    img = BASE.copy()
    for (bx, by, r, col, s, ph) in [(0.20, 0.22, 0.55, EMERALD, 0.30, 0.0), (0.85, 0.55, 0.50, (20, 120, 90), 0.35, 2.0), (0.35, 0.95, 0.60, MINT, 0.14, 4.0)]:
        cx = (bx + 0.05 * math.sin(T * 0.25 + ph)) * LW
        cy = (by + 0.04 * math.cos(T * 0.2 + ph)) * LH
        rr = r * LW
        e = np.exp(-(((lxx - cx) ** 2 + (lyy - cy) ** 2) / (rr * rr)))[..., None]
        img = img + np.array(col, np.float32) * e * s
    # barrido de luz diagonal muy suave
    sweep = ((lxx * 0.6 + lyy * 0.4) / LW - (T * 0.08) % 3.0 + 0.5)
    img = img + np.exp(-(sweep ** 2) / 0.02)[..., None] * 10
    up = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).convert("RGBA")
    up.alpha_composite(DOTS)
    return up

# ---------- texto ----------
@lru_cache(maxsize=4096)
def text_img(txt, size, color=WHITE, path=F_XB, shadow=True):
    f = font(path, size)
    bbox = f.getbbox(txt)
    asc, desc = f.getmetrics()
    top = int(asc * 0.16)
    pad = 24
    w, h = bbox[2] - bbox[0] + pad * 2, asc + desc - top + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ox, oy = pad - bbox[0], pad - top
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((ox, oy + 6), txt, font=f, fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((ox, oy), txt, font=f, fill=color)
    return im

def paste_center(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1.0) > 0.002:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    dst.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

def words_in(dst, words, cx, cy, size, t, start, path=F_XB, stagger=0.05, max_w=900, line_gap=1.12, align="center"):
    """Entrada moderna palabra a palabra: sube 40 px y aparece. words = [(texto, color)]."""
    f = font(path, size); space = f.getlength(" ")
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
    for li, (ln, lw) in enumerate(lines):
        x = (cx - lw / 2) if align == "center" else cx
        for (wd, wl) in ln:
            p = prog(t, start + k * stagger, 0.55)
            if p > 0:
                img = text_img(wd[0], size, wd[1], path)
                paste_center(dst, img, x + wl / 2, y0 + li * lh + (1 - ease_out_quint(p)) * 42, 1.0, ease_out_cubic(p * 1.4))
            x += wl + space
            k += 1
    return y0 + (len(lines) - 1) * lh  # y de la última línea

# ---------- piezas ----------
@lru_cache(maxsize=256)
def glass(w, h, r=34, fill=(255, 255, 255, 16), border=(180, 255, 220, 55)):
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], r * s, fill=fill, outline=border, width=2 * s)
    return im.resize((w, h), Image.LANCZOS)

@lru_cache(maxsize=128)
def pill(txt, size=34, fill=MINT, color=DEEP, path=F_B, outline=False):
    t = text_img(txt, size, color, path, shadow=False)
    w, h = t.width + 16, t.height - 4
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if outline:
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], h * s // 2, fill=(255, 255, 255, 10), outline=fill + (200,), width=3 * s)
    else:
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], h * s // 2, fill=fill)
    im = im.resize((w, h), Image.LANCZOS)
    im.alpha_composite(t, (8, -2))
    return im

def glow(im, color, radius=22, strength=0.7):
    a = im.split()[3]
    g = Image.new("RGBA", im.size, color + (0,)); g.putalpha(a.point(lambda v: int(v * strength)))
    pad = radius * 3
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    big.alpha_composite(g, (pad, pad)); big = big.filter(ImageFilter.GaussianBlur(radius))
    big.alpha_composite(im, (pad, pad))
    return big

def pop(dst, im, cx, cy, t, start, dur=0.6, rise=50, scale_from=0.92):
    p = prog(t, start, dur)
    if p <= 0: return
    paste_center(dst, im, cx, cy + (1 - ease_out_quint(p)) * rise, scale_from + (1 - scale_from) * ease_out_back(p, 1.2), ease_out_cubic(p * 1.3))

# iconos de línea (trazo menta)
def icon(kind, size=260, col=MINT, wdt=10):
    s = 3; S = size * s
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    L = lambda pts: d.line([(x * S, y * S) for x, y in pts], fill=col, width=wdt * s, joint="curve")
    R = lambda b, r=0.06: d.rounded_rectangle([b[0] * S, b[1] * S, b[2] * S, b[3] * S], r * S, outline=col, width=wdt * s)
    E = lambda b: d.ellipse([b[0] * S, b[1] * S, b[2] * S, b[3] * S], outline=col, width=wdt * s)
    A = lambda b, a0, a1: d.arc([b[0] * S, b[1] * S, b[2] * S, b[3] * S], a0, a1, fill=col, width=wdt * s)
    if kind == "milk":
        L([(0.30, 0.40), (0.30, 0.92), (0.70, 0.92), (0.70, 0.40), (0.50, 0.20), (0.30, 0.40), (0.70, 0.40)])
        R((0.40, 0.06, 0.60, 0.20), 0.02); L([(0.30, 0.58), (0.70, 0.58)]); L([(0.30, 0.76), (0.70, 0.76)])
    elif kind == "cart":
        L([(0.08, 0.20), (0.22, 0.20), (0.32, 0.66), (0.80, 0.66), (0.90, 0.32), (0.26, 0.32)])
        E((0.30, 0.74, 0.42, 0.86)); E((0.68, 0.74, 0.80, 0.86))
    elif kind == "cup":
        L([(0.20, 0.36), (0.26, 0.88), (0.66, 0.88), (0.72, 0.36), (0.20, 0.36)])
        A((0.62, 0.46, 0.88, 0.70), 270, 90); L([(0.16, 0.36), (0.76, 0.36)])
        for x in (0.36, 0.46, 0.56): A((x - 0.04, 0.06, x + 0.04, 0.28), 100, 260)
    elif kind == "phone":
        R((0.28, 0.06, 0.72, 0.94), 0.08); L([(0.44, 0.14), (0.56, 0.14)])
        for r in (0.08, 0.15, 0.22): A((0.50 - r, 0.50 - r, 0.50 + r, 0.50 + r), -45, 45)
    elif kind == "cash":
        R((0.08, 0.26, 0.92, 0.74), 0.05); E((0.40, 0.38, 0.60, 0.62)); L([(0.18, 0.36), (0.18, 0.40)]); L([(0.82, 0.60), (0.82, 0.64)])
    elif kind == "plane":
        L([(0.10, 0.52), (0.90, 0.26), (0.62, 0.86), (0.48, 0.58), (0.10, 0.52)]); L([(0.48, 0.58), (0.90, 0.26)])
    elif kind == "piggy":
        E((0.14, 0.28, 0.82, 0.82)); L([(0.40, 0.20), (0.56, 0.20)]); L([(0.30, 0.80), (0.30, 0.92)]); L([(0.64, 0.80), (0.64, 0.92)])
        d.ellipse([0.60 * S, 0.44 * S, 0.66 * S, 0.50 * S], fill=col)
    elif kind == "list":
        R((0.18, 0.08, 0.82, 0.92), 0.06)
        for y in (0.30, 0.50, 0.70): L([(0.30, y), (0.36, y + 0.05), (0.46, y - 0.05)]); L([(0.54, y), (0.72, y)])
    elif kind == "eye":
        A((0.08, 0.20, 0.92, 0.80), 200, 340); A((0.08, 0.20, 0.92, 0.80), 20, 160); E((0.38, 0.38, 0.62, 0.62))
    elif kind == "candy":
        E((0.32, 0.32, 0.68, 0.68)); L([(0.32, 0.50), (0.12, 0.36), (0.12, 0.64), (0.32, 0.50)]); L([(0.68, 0.50), (0.88, 0.36), (0.88, 0.64), (0.68, 0.50)])
    elif kind == "wallet":
        R((0.10, 0.24, 0.90, 0.84), 0.06); R((0.58, 0.44, 0.90, 0.64), 0.04); L([(0.16, 0.24), (0.70, 0.10), (0.76, 0.24)])
    elif kind == "check":
        L([(0.18, 0.52), (0.40, 0.74), (0.82, 0.28)])
    return im.resize((size, size), Image.LANCZOS)

# ---------- cabecera fija ----------
WORDMARK = text_img("MENTE RICA", 34, WHITE, F_B, shadow=False)
def draw_header(dst, idx, total):
    d = ImageDraw.Draw(dst)
    d.ellipse([64, 118, 88, 142], fill=MINT)
    dst.alpha_composite(WORDMARK, (84, 96))
    num = text_img(f"{idx:02d} / {total:02d}", 30, MUTED, F_M, shadow=False)
    dst.alpha_composite(num, (W - 64 - num.width + 24, 98))
    # segmentos de progreso por escena
    seg_w = (W - 128 - (total - 1) * 10) / total
    for i in range(total):
        x0 = 64 + i * (seg_w + 10)
        d.rounded_rectangle([x0, 70, x0 + seg_w, 76], 3, fill=(255, 255, 255, 45) if i + 1 > idx else MINT + (255,))

@lru_cache(maxsize=64)
def glow_text(txt, size, color, path, gcol, r=26, st=0.45):
    return glow(text_img(txt, size, color, path), gcol, r, st)

def outro(dst, t):
    words_in(dst, [("Sígueme", WHITE), ("para", WHITE), ("tener", WHITE), ("una", WHITE)], W / 2, 700, 76, t, 0.15, path=F_B)
    p = prog(t, 0.5, 0.7)
    if p > 0:
        big = glow_text("MENTE RICA", 150, MINT, F_BLACK, EMERALD, 30, 0.45)
        paste_center(dst, big, W / 2, 860 + (1 - ease_out_quint(p)) * 50, 0.94 + 0.06 * ease_out_back(p) + 0.01 * math.sin(t * 2), ease_out_cubic(p))
    p = prog(t, 1.1, 0.6)
    if p > 0:
        btn = pill("  + Seguir  ", 58, MINT, DEEP, F_B)
        pulse = 1 + 0.025 * math.sin(max(0, t - 1.7) * 4)
        paste_center(dst, btn, W / 2, 1080 + (1 - ease_out_quint(p)) * 40, pulse * (0.92 + 0.08 * ease_out_back(p)), ease_out_cubic(p))
    words_in(dst, [("Comenta", MUTED), ("qué", MUTED), ("tema", MUTED), ("quieres", MUTED), ("mañana", WHITE)], W / 2, 1250, 52, t, 1.6, path=F_SB)

def tip_chip(dst, t, y=470):
    pop(dst, pill("  ✓  EL TRUCO  ", 40, LIME, DEEP, F_XB), W / 2, y, t, 0.1, 0.5, 30)

# ---------- motor ----------
def render_scene(fn, idx, total, t, T):
    img = bg_frame(T)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(layer, t)
    z = 1 + 0.018 * (t / CLIP)
    lw, lh = int(W * z), int(H * z)
    layer = layer.resize((lw, lh), Image.BILINEAR).crop(((lw - W) // 2, (lh - H) // 2, (lw - W) // 2 + W, (lh - H) // 2 + H))
    img.alpha_composite(layer)
    draw_header(img, idx, total)
    # fundido de entrada desde el fondo (0,15 s)
    return img.convert("RGB")

def main(SCENES, outdir):
    mode = sys.argv[1] if len(sys.argv) > 1 else "clips"
    total = len(SCENES)
    if mode == "stills":
        # stills  escena:tiempo ...
        for a in sys.argv[2:]:
            i, tt = a.split(":"); i = int(i); tt = float(tt)
            render_scene(SCENES[i - 1], i, total, tt, (i - 1) * CLIP + tt).save(f"still_{i}_{tt:04.1f}.png")
        return
    only = [int(x) for x in sys.argv[2:]] or list(range(1, total + 1))
    os.makedirs(outdir, exist_ok=True)
    for i in only:
        out = os.path.join(outdir, f"escena-{i}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out], stdin=subprocess.PIPE)
        for f in range(int(CLIP * FPS)):
            t = f / FPS
            p.stdin.write(render_scene(SCENES[i - 1], i, total, t, (i - 1) * CLIP + t).tobytes())
        p.stdin.close(); p.wait()
        print("ok", out, flush=True)
