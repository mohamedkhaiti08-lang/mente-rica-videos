# Motor de vídeos "Teórico B en 30s" (estilo azul señal DGT + amarillo, imágenes directas dibujadas, subtítulos karaoke).
# Uso:
#   python3 motor_b.py config.json stills t1 t2 ...      -> still_t1.png ... (para revisar)
#   python3 motor_b.py config.json video salida.mp4       -> vídeo final con voz + efectos (voz.wav junto al config)
# config.json:
#   {"label": "¿APROBARÍAS?", "times": "tiempos.json", "voice": "voz.wav", "tail": 1.2,
#    "sfx": [{"t": 12.0, "type": "beep|ding|buzz|whoosh"}],
#    "scenes": [ {"cap": "texto en pantalla de la frase", "hi": ["palabras", "en amarillo"], "vis": {"type": ...}} ]}
# Una escena por frase de la voz: cada escena empieza justo cuando empieza su frase (tiempos.json de voz.py).
# Tipos de "vis" (ver funciones vis_*): hook, road, quiz, countdown, reveal, compare, roof, cta, topdown, law,
#   nocross, save, sign, mito, stat (admite "dec": 1 para decimales), cruce (cruce sin señales con coches numerados),
#   tyre (neumático: tread | gauge | wet | compare), puntos (carné por puntos: card | steps),
#   bike (ciclista cenital y adelantamiento: approach | pass | twolanes), speedo (cuentakilómetros que baja de from a to),
#   sillita (tallímetro 1,35 m: measure | coche con sillita detrás: seat), pas (accidente: crash | tarjetas P·A·S: steps),
#   pov (calle urbana en primera persona con salpicadero y ciclista delante: approach | center | horn | options | gap),
#   cruce admite "dirt": true (brazo este = camino de tierra) y "dirt_hl".
#   glorieta (rotonda cenital con coches numerados dentro/entrando), alcohol (alcoholímetro: zero | trap | minor | limit | units | years | pending).
#   hook admite "img": "seat" (sillita) y "stamp_x" (posición del sello).
import math, json, sys, os, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
SB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
WHITE = (255, 255, 255); YEL = (255, 196, 0); NAVY = (6, 20, 43); BLUE = (18, 86, 190); BLUE_L = (60, 140, 255)
GREEN = (34, 197, 94); RED = (239, 68, 68); ORANGE = (255, 140, 0); DARK = (14, 18, 28); GREY = (120, 132, 150)

CFG = json.load(open(sys.argv[1]))
BASE = os.path.dirname(os.path.abspath(sys.argv[1]))
LINES = json.load(open(os.path.join(BASE, CFG.get("times", "tiempos.json"))))
SC = CFG["scenes"]
assert len(SC) == len(LINES), f"{len(SC)} escenas vs {len(LINES)} frases"
B = [0.0] + [LINES[i][0] - min(0.2, (LINES[i][0] - LINES[i - 1][1]) / 2) for i in range(1, len(LINES))]
DUR = round(LINES[-1][1] + CFG.get("tail", 1.2), 2)
B.append(DUR)
VZ = (330, 1230)          # zona visual (y)
CY = (VZ[0] + VZ[1]) // 2  # centro visual

@lru_cache(maxsize=None)
def F(p, s): return ImageFont.truetype(p, s)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def eback(t, s=1.8): t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def prog(t, s, d): return clamp((t - s) / d)
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))

def paste(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if x >= W or y >= H or x + im.width <= 0 or y + im.height <= 0: return
    dst.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

def ss(w, h):  # lienzo con supermuestreo x2 para formas suaves
    return Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
def down(im): return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)

def glow(im, r=18, a=0.8):
    g = im.filter(ImageFilter.GaussianBlur(r)); out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    g.putalpha(g.split()[3].point(lambda v: int(v * a))); out.alpha_composite(g); out.alpha_composite(im); return out

# ---------- texto ----------
@lru_cache(maxsize=4096)
def text(txt, size, col=WHITE, path=BLACK, shadow=True, stroke=0, scol=(0, 0, 0)):
    f = F(path, size); bb = f.getbbox(txt, stroke_width=stroke); asc, desc = f.getmetrics(); pad = 28
    im = Image.new("RGBA", (bb[2] - bb[0] + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - bb[0], pad + 6), txt, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(im).text((pad - bb[0], pad), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=scol)
    return im

def fit(lines, size, path=BLACK, maxw=920):
    while size > 30 and max(F(path, size).getlength(l) for l in lines) > maxw: size -= 2
    return size

def wrap(txt, size, path, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if F(path, size).getlength(test) <= maxw or not cur: cur = test
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

@lru_cache(maxsize=256)
def pill(txt, size=40, bg=YEL, fg=NAVY, path=XB, padx=34, pady=16):
    f = F(path, size); bb = f.getbbox(txt); w, h = int(f.getlength(txt)) + padx * 2, (bb[3] - bb[1]) + pady * 2
    im = ss(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=h, fill=bg)
    d.text((padx * 2, pady * 2 - bb[1] * 2), txt, font=F(path, size * 2), fill=fg)
    return down(im)

@lru_cache(maxsize=64)
def card(w, h, fill=(255, 255, 255, 245), r=44, border=None, bw=0):
    im = ss(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=r * 2, fill=fill, outline=border, width=bw * 2)
    im = down(im)
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 52, w + 40, h + 52), radius=r, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh

# ---------- iconos / imágenes dibujadas ----------
@lru_cache(maxsize=None)
def icon_check(s=120, col=GREEN):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.ellipse((0, 0, S - 1, S - 1), fill=col)
    d.line([(S * .26, S * .52), (S * .43, S * .68), (S * .74, S * .34)], fill=WHITE, width=int(S * .11), joint="curve")
    return down(im)

@lru_cache(maxsize=None)
def icon_x(s=120, col=RED):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.ellipse((0, 0, S - 1, S - 1), fill=col); k = S * .3
    d.line([(k, k), (S - k, S - k)], fill=WHITE, width=int(S * .11)); d.line([(S - k, k), (k, S - k)], fill=WHITE, width=int(S * .11))
    return down(im)

@lru_cache(maxsize=None)
def sign_b(s=200):  # señal circular azul con B
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.ellipse((0, 0, S - 1, S - 1), fill=WHITE); d.ellipse((S * .07, S * .07, S * .93, S * .93), fill=BLUE)
    f = F(BLACK, int(S * .62)); bb = f.getbbox("B")
    d.text((S / 2 - (bb[0] + bb[2]) / 2, S / 2 - (bb[1] + bb[3]) / 2), "B", font=f, fill=WHITE)
    return down(im)

@lru_cache(maxsize=None)
def triangle(s=300, grey=False):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    rc = (150, 150, 160) if grey else (220, 30, 40)
    pts = [(S / 2, S * .06), (S * .96, S * .9), (S * .04, S * .9)]
    d.polygon(pts, fill=rc)
    ip = [(S / 2, S * .27), (S * .79, S * .79), (S * .21, S * .79)]
    d.polygon(ip, fill=(235, 235, 240) if grey else WHITE)
    d.rectangle((S * .47, S * .9, S * .53, S * .99), fill=(90, 90, 100))
    return down(im)

@lru_cache(maxsize=None)
def beacon(s=150, on=True):  # baliza V-16
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.rounded_rectangle((S * .18, S * .62, S * .82, S * .92), radius=int(S * .08), fill=(30, 30, 36))
    dome = (255, 170, 20) if on else (190, 120, 30)
    d.pieslice((S * .2, S * .18, S * .8, S * 1.06), 180, 360, fill=dome)
    d.rectangle((S * .2, S * .6, S * .8, S * .66), fill=dome)
    d.ellipse((S * .36, S * .3, S * .5, S * .44), fill=(255, 240, 190) if on else (220, 170, 90))
    im = down(im)
    return glow(im, 22, 0.95) if on else im

@lru_cache(maxsize=None)
def car_rear(w=560, col=(226, 69, 60)):
    h = int(w * .78); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    dk = mix(col, (0, 0, 0), .35)
    d.rounded_rectangle((X * .14, Y * .02, X * .86, Y * .5), radius=int(X * .12), fill=dk)            # techo
    d.rounded_rectangle((X * .2, Y * .08, X * .8, Y * .42), radius=int(X * .07), fill=(40, 60, 90))     # luna trasera
    d.polygon([(X * .22, Y * .38), (X * .5, Y * .1), (X * .6, Y * .1), (X * .32, Y * .38)], fill=(80, 105, 140))  # reflejo
    d.rounded_rectangle((X * .02, Y * .4, X * .98, Y * .84), radius=int(X * .09), fill=col)             # carrocería
    d.rounded_rectangle((X * .3, Y * .55, X * .7, Y * .7), radius=int(X * .015), fill=WHITE)            # matrícula
    d.rectangle((X * .3, Y * .55, X * .35, Y * .7), fill=(30, 70, 170))
    f = F(XB, int(Y * .085)); d.text((X * .37, Y * .57), "3030 BTB", font=f, fill=(20, 20, 20))
    d.rounded_rectangle((X * .0, Y * .76, X * 1.0, Y * .9), radius=int(X * .05), fill=(28, 30, 36))    # paragolpes
    for x0 in (.06, .78):
        d.rounded_rectangle((X * x0, Y * .46, X * (x0 + .16), Y * .56), radius=int(X * .03), fill=(150, 20, 25))
    for x0 in (.08, .76):
        d.rounded_rectangle((X * x0, Y * .86, X * (x0 + .16), Y * .99), radius=int(X * .03), fill=(15, 15, 18))  # ruedas
    return down(im)

@lru_cache(maxsize=None)
def hazard(s=150):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((s * .2, s * .2, s * .8, s * .8), fill=(255, 160, 0, 255))
    return glow(im.filter(ImageFilter.GaussianBlur(6)), 26, 1.0)

@lru_cache(maxsize=None)
def car_top(col=(226, 69, 60), w=150):
    h = int(w * 1.8); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .3), fill=col)
    d.rounded_rectangle((X * .12, Y * .2, X * .88, Y * .36), radius=int(X * .12), fill=(40, 60, 90))   # parabrisas
    d.rounded_rectangle((X * .14, Y * .72, X * .86, Y * .84), radius=int(X * .1), fill=(40, 60, 90))   # luna trasera
    d.rounded_rectangle((X * .14, Y * .38, X * .86, Y * .7), radius=int(X * .1), fill=mix(col, (255, 255, 255), .15))
    for y0 in (.02, .93):
        for x0 in (.08, .72):
            d.rounded_rectangle((X * x0, Y * y0, X * (x0 + .2), Y * (y0 + .05)), radius=8, fill=(255, 240, 200) if y0 < .5 else (200, 30, 30))
    im = down(im)
    sh = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, h + 26), radius=int(w * .3), fill=(0, 0, 0, 140))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 20)); return sh

@lru_cache(maxsize=None)
def ambulance_top(w=170, lights=0):
    h = int(w * 2.1); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .18), fill=(250, 250, 250))
    d.rounded_rectangle((X * .1, Y * .08, X * .9, Y * .2), radius=int(X * .1), fill=(40, 60, 90))
    for i in range(6):
        d.rectangle((0, Y * (.3 + i * .1), X, Y * (.3 + i * .1 + .05)), fill=(255, 210, 0) if i % 2 else (40, 160, 70))
    d.rectangle((X * .38, Y * .5, X * .62, Y * .76), fill=(220, 30, 40)); d.rectangle((X * .26, Y * .58, X * .74, Y * .68), fill=(220, 30, 40))
    a, b = ((40, 120, 255), (180, 200, 255)) if lights == 0 else ((180, 200, 255), (40, 120, 255))
    d.rounded_rectangle((X * .1, Y * .22, X * .48, Y * .27), radius=8, fill=a)
    d.rounded_rectangle((X * .52, Y * .22, X * .9, Y * .27), radius=8, fill=b)
    im = down(im)
    g = Image.new("RGBA", (w + 200, h + 200), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    cx = 100 + (w * .3 if lights == 0 else w * .7); gd.ellipse((cx - 70, 100 + h * .245 - 70, cx + 70, 100 + h * .245 + 70), fill=(60, 140, 255, 150))
    g = g.filter(ImageFilter.GaussianBlur(28)); g.alpha_composite(im, (100, 100)); return g

@lru_cache(maxsize=None)
def semaphore(state):  # state 0..3: cuántas luces encendidas (rojo, ámbar, verde)
    w, h = 230, 600; im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=90, fill=(22, 24, 30), outline=(60, 64, 76), width=10)
    cols = [(239, 68, 68), (255, 176, 0), (34, 197, 94)]
    for i, c in enumerate(cols):
        on = state == i + 1
        d.ellipse((X * .17, Y * (.05 + i * .32), X * .83, Y * (.05 + i * .32) + X * .66), fill=c if on else mix(c, (22, 24, 30), .78))
    im = down(im)
    return glow(im, 30, .9)

@lru_cache(maxsize=None)
def bookmark(s=300):
    im = ss(s, int(s * 1.3)); d = ImageDraw.Draw(im); X, Y = s * 2, int(s * 1.3) * 2
    d.polygon([(X * .12, 0), (X * .88, 0), (X * .88, Y), (X * .5, Y * .72), (X * .12, Y)], fill=YEL)
    return glow(down(im), 30, .7)

@lru_cache(maxsize=None)
def bubble(w=760, h=360):
    im = ss(w, h + 80); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=120, fill=WHITE)
    d.polygon([(X * .2, Y - 4), (X * .34, Y - 4), (X * .16, Y + 150)], fill=WHITE)
    return down(im)

@lru_cache(maxsize=None)
def doc_card():
    w, h = 760, 720; c = card(w, h, fill=(252, 252, 250, 255), r=36); d = ImageDraw.Draw(c); ox, oy = 40, 40
    d.rectangle((ox, oy, ox + w, oy + 120), fill=BLUE);
    d.rounded_rectangle((ox, oy, ox + w, oy + 160), radius=36, fill=BLUE); d.rectangle((ox, oy + 100, ox + w, oy + 160), fill=(252, 252, 250))
    d.text((ox + 50, oy + 34), "BOE", font=F(BLACK, 58), fill=WHITE)
    d.text((ox + 230, oy + 50), "Normativa de tráfico", font=F(SB, 34), fill=(210, 225, 255))
    for i in range(5):
        y = oy + 440 + i * 52; d.rounded_rectangle((ox + 50, y, ox + w - 50 - (i % 3) * 90, y + 18), radius=9, fill=(214, 220, 230))
    return c

# ---------- fondo ----------
@lru_cache(maxsize=1)
def bg_base():
    yy = np.linspace(0, 1, H)[:, None, None]
    c1, c2 = np.array(NAVY, float), np.array((10, 52, 120), float)
    arr = (c1 * (1 - yy) + c2 * yy) * np.ones((1, W, 1))
    xx = np.linspace(-1, 1, W)[None, :, None]; yv = np.linspace(-1, 1, H)[:, None, None]
    vign = 1 - 0.35 * np.clip(xx ** 2 + (yv * .8) ** 2, 0, 1)
    im = Image.fromarray(np.clip(arr * vign, 0, 255).astype(np.uint8)).convert("RGBA")
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse((-300, 400, 700, 1400), fill=(30, 110, 255, 70)); d.ellipse((500, 900, 1400, 1800), fill=(255, 196, 0, 30))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(160)))
    return im

def background(t):
    im = bg_base().copy(); d = ImageDraw.Draw(im, "RGBA")
    # líneas de carretera en perspectiva que avanzan (sutiles)
    vx, vy = W / 2, 980
    for k in range(14):
        z = ((k / 14) + t * 0.35) % 1.0; z2 = z + 0.035
        y1, y2 = vy + (H - vy) * z ** 2, vy + (H - vy) * z2 ** 2
        for side in (-1, 1):
            x1, x2 = vx + side * 900 * z ** 2, vx + side * 900 * z2 ** 2
            d.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, int(40 * z)), width=max(2, int(14 * z)))
    return im

# ---------- capa fija (cabecera y cronómetro) ----------
def header(dst, t):
    paste(dst, sign_b(92), 104, 150)
    paste(dst, text("TEÓRICO B", 46, WHITE, BLACK, shadow=False), 152 + text("TEÓRICO B", 46, WHITE, BLACK, shadow=False).width / 2, 132)
    paste(dst, text("en 30 segundos", 30, YEL, SB, shadow=False), 152 + text("en 30 segundos", 30, YEL, SB, shadow=False).width / 2, 178)
    # cronómetro
    cx, cy, r = 960, 150, 58; d = ImageDraw.Draw(dst, "RGBA")
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 0, 90), outline=(255, 255, 255, 60), width=8)
    ang = -90 + 360 * clamp(t / 30.0)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, ang, fill=YEL, width=10)
    d.rounded_rectangle((cx - 14, cy - r - 24, cx + 14, cy - r - 8), radius=5, fill=YEL)
    s = f"{int(t):02d}"; paste(dst, text(s, 44, WHITE, BLACK, shadow=False), cx, cy - 2)
    lab = CFG.get("label")
    if lab: paste(dst, pill(lab, 38), W / 2, 268)

# ---------- subtítulos karaoke ----------
def captions(dst, t, i):
    sc = SC[i]; cap = sc.get("cap", ""); hi = set(w.lower().strip("¿?¡!.,:;") for w in sc.get("hi", []))
    if not cap: return
    s0, s1 = LINES[i]; words = cap.split(); size = 70
    lines = wrap(cap, size, POP, 860)
    while len(lines) > 3 and size > 44: size -= 4; lines = wrap(cap, size, POP, 860)
    total = sum(len(w) + 1 for w in words); acc = 0; starts = []
    for w in words: starts.append(s0 + (s1 - s0) * acc / total); acc += len(w) + 1
    appear = 1.0 if i == 0 else eout(prog(t, B[i], 0.18)); y0 = 1395 - (len(lines) - 1) * size * 0.62
    f = F(POP, size); wi = 0; lh = int(size * 1.24)
    # placa
    d = ImageDraw.Draw(dst, "RGBA")
    pw = max(f.getlength(l) + 16 * (len(l.split()) - 1) for l in lines) + 70; ph = lh * len(lines) + 40
    d.rounded_rectangle((W / 2 - pw / 2, y0 - 34, W / 2 + pw / 2, y0 - 34 + ph), radius=30, fill=(0, 0, 0, int(120 * appear)))
    for li, line in enumerate(lines):
        lw = line.split(); x = W / 2 - (f.getlength(line) + 16 * (len(lw) - 1)) / 2; y = y0 + li * lh
        for w in lw:
            st = starts[wi]; key = w.lower().strip("¿?¡!.,:;")
            said = t >= st; cur = st <= t < (starts[wi + 1] if wi + 1 < len(starts) else s1 + 0.3)
            col = YEL if (key in hi and said) else WHITE
            a = 1.0 if said else 0.38
            ww = f.getlength(w)
            if cur and appear > .5:
                bb = f.getbbox(w); d.rounded_rectangle((x - 12, y - size * .5 + 2, x + ww + 12, y + size * .62 + 2), radius=16, fill=YEL + (235,))
                col = NAVY
            im = text(w, size, col, POP, shadow=not cur, stroke=0)
            paste(dst, im, x + ww / 2, y + 6, alpha=a * appear)
            x += ww + f.getlength(" ") + 16; wi += 1

# ---------- visuales ----------
def big_lines(dst, lines, t, y, cols=None, size=150, stagger=0.22):
    size = fit(lines, size); lh = int(size * 1.02)
    for k, l in enumerate(lines):
        p = prog(t, k * stagger, 0.35); col = (cols[k] if cols else WHITE)
        paste(dst, text(l, size, tuple(col), BLACK, stroke=0), W / 2, y + k * lh, scale=0.6 + 0.4 * eback(p), alpha=ease(p * 2))

def vis_hook(dst, t, v, i):
    lines = v.get("lines", []); cols = [tuple(c) for c in v.get("cols", [])] or None
    n = len(lines); y = CY - (n - 1) * 80 - (40 if v.get("badge") else 0) - (150 if v.get("img") else 0)
    if i == 0: t = t + 0.6  # primer fotograma: el gancho ya está en pantalla
    shake = 0
    if v.get("stamp"):
        ps = prog(t, v.get("stamp_at", 0.8), 0.18)
        if 0 < ps < 1 or (ps == 1 and t - v.get("stamp_at", 0.8) < 0.45): shake = math.sin(t * 90) * 10 * (1 - prog(t, v.get("stamp_at", .8) + .18, .3))
    big_lines(dst, lines, t, y + shake, cols)
    if v.get("img") == "seat":  # sillita infantil que entra botando
        ip = prog(t, .25, .5); paste(dst, child_seat(300), W / 2 - 230, CY + 200 + math.sin(t * 5) * 8, scale=.85 * eback(ip), alpha=ease(ip * 2), rot=4 * math.sin(t * 3))
    if v.get("badge"):
        p = prog(t, 0.5, 0.35); paste(dst, pill(v["badge"], 46, YEL, NAVY), W / 2, y + n * 150 + 30, scale=eback(p), alpha=ease(p * 2))
    if v.get("stamp"):
        st = v.get("stamp_at", 0.8); ps = prog(t, st, 0.2)
        if ps > 0:
            im = stamp_img(v["stamp"]); paste(dst, im, W / 2 + v.get("stamp_x", 120), CY + 230, scale=lerp(2.2, 1.0, eout(ps)), alpha=ease(ps * 1.5), rot=-12)

@lru_cache(maxsize=16)
def stamp_img(txt):
    f = F(BLACK, 96); w = int(f.getlength(txt)) + 90; h = 170; im = ss(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w * 2 - 6, h * 2 - 6), radius=36, outline=RED, width=18)
    bb = F(BLACK, 192).getbbox(txt); d.text((w - (bb[0] + bb[2]) / 2, h - (bb[1] + bb[3]) / 2), txt, font=F(BLACK, 192), fill=RED)
    return down(im)

def road_scene(dst, t, horizon=560, label=None):
    d = ImageDraw.Draw(dst, "RGBA"); vx = W / 2; top, bot = horizon, VZ[1] + 20
    d.polygon([(vx - 60, top), (vx + 60, top), (vx + 620, bot), (vx - 620, bot)], fill=(34, 38, 48, 255))
    d.line([(vx - 60, top), (vx - 620, bot)], fill=(255, 255, 255, 200), width=8)
    d.line([(vx + 60, top), (vx + 620, bot)], fill=(255, 255, 255, 200), width=8)
    for k in range(10):
        z = ((k / 10) + t * 0.9) % 1.0; z2 = min(1, z + 0.05)
        y1, y2 = top + (bot - top) * z ** 1.6, top + (bot - top) * z2 ** 1.6
        for lx in (-0.33, 0.33):
            x1 = vx + lx * (60 + 560 * z ** 1.6) * 1.0; x2 = vx + lx * (60 + 560 * z2 ** 1.6)
            d.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, int(220 * z)), width=max(2, int(12 * z)))
    if label: paste(dst, pill(label, 36, WHITE, BLUE), W / 2, horizon - 60)

def vis_road(dst, t, v, i):
    road_scene(dst, t, label=v.get("label"))
    p = eback(prog(t, 0.0, 0.5)); y = lerp(1300, 980, p)
    car = car_rear(560); paste(dst, car, W / 2, y)
    if v.get("hazard", True) and int(t * 2.4) % 2 == 0:
        for dx in (-205, 205): paste(dst, hazard(170), W / 2 + dx, y - car.height / 2 + car.height * .51)
    if v.get("smoke"):
        for k in range(5):
            z = ((t * .6 + k / 5) % 1); paste(dst, puff(), W / 2 + 160 + k * 18, y - 140 - z * 260, scale=.5 + z, alpha=(1 - z) * .55)

@lru_cache(maxsize=1)
def puff():
    im = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((40, 40, 180, 180), fill=(220, 220, 225, 200))
    return im.filter(ImageFilter.GaussianBlur(24))

QC = (900, 0)
def quiz_card(dst, v, t, state, enter=0.0):
    """state: dict(opts_shown=[a,b,c alphas], reveal=0..1, small=False)"""
    q = v["q"]; opts = v["opts"]; corr = v["correct"]
    qs = 52; ql = wrap(q, qs, XB, 780)
    while len(ql) > 3: qs -= 4; ql = wrap(q, qs, XB, 780)
    ch = 150 + len(ql) * int(qs * 1.2) + 3 * 130 + 40
    p = eback(prog(t, enter, 0.45)); cy = CY + 20; top = cy - ch / 2
    c = card(880, int(ch), fill=(255, 255, 255, 250), r=46)
    paste(dst, c, W / 2, cy + (1 - p) * 200, alpha=ease(prog(t, enter, .25)))
    a = ease(prog(t, enter, .25)); off = (1 - p) * 200
    paste(dst, pill("PREGUNTA DE EXAMEN", 30, BLUE, WHITE), W / 2, top + 50 + off, alpha=a)
    for k, l in enumerate(ql):
        paste(dst, text(l, qs, DARK, XB, shadow=False), W / 2, top + 120 + k * qs * 1.2 + qs / 2 + off, alpha=a)
    oy = top + 150 + len(ql) * qs * 1.2 + 20
    for k, o in enumerate(opts):
        oa = state["opts"][k] * a
        if oa <= 0.01: continue
        rv = state.get("reveal", 0)
        fill = (241, 244, 250); bord = (210, 218, 232); lc = BLUE
        if rv > 0:
            if k == corr: fill = mix((241, 244, 250), (220, 252, 231), rv); bord = mix(bord, GREEN, rv); lc = GREEN
            else: fill = mix((241, 244, 250), (250, 235, 235), rv); bord = mix(bord, (240, 180, 180), rv); lc = mix(BLUE, RED, rv)
        im = opt_row("ABC"[k], o, fill, bord, lc, rv > .5 and k != corr)
        sx = (1 - eout(state["opts"][k])) * 120
        y = oy + k * 130 + 55 + off
        sc = 1 + (0.06 * math.sin(clamp(rv) * math.pi) if k == corr else 0)
        paste(dst, im, W / 2 + sx, y, alpha=oa * (0.55 + 0.45 * (1 - rv) if (rv > 0 and k != corr) else 1), scale=sc)
        if rv > 0.05:
            ic = icon_check(78) if k == corr else icon_x(78, (220, 90, 90))
            paste(dst, ic, W / 2 + 350, y, scale=eback(prog(rv, 0, 1)), alpha=clamp(rv * 2) * (1 if k == corr else .8))

@lru_cache(maxsize=64)
def opt_row(letter, o, fill, bord, lc, dim):
    w, h = 780, 108; im = ss(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=50, fill=fill, outline=bord, width=6)
    d.ellipse((24, 24, 24 + 168, 24 + 168), fill=lc)
    f = F(BLACK, 96); bb = f.getbbox(letter); d.text((108 - (bb[0] + bb[2]) / 2, 108 - (bb[1] + bb[3]) / 2), letter, font=f, fill=WHITE)
    s = 84
    while F(XB, s).getlength(o) > w * 2 - 300 and s > 50: s -= 4
    bb = F(XB, s).getbbox(o); d.text((230, 108 - (bb[1] + bb[3]) / 2), o, font=F(XB, s), fill=(120, 126, 140) if dim else DARK)
    return down(im)

def vis_quiz(dst, t, v, i):
    at = v.get("opt_at", [0.0, 0.0, 0.0]); dur = LINES[i][1] - LINES[i][0]
    if v.get("hide_opts"): shown = [0, 0, 0]
    else: shown = [eout(prog(t, a * dur if a <= 1 else a, 0.3)) for a in at]
    quiz_card(dst, v, t, {"opts": shown}, enter=0.0 if not v.get("cont") else -1)
    if v.get("hide_opts"):
        pk = .5 + .5 * math.sin(t * 6); paste(dst, text("?", 300, BLUE, BLACK, shadow=False), W / 2, CY + 150, scale=(.9 + .1 * pk) * eback(prog(t, .3, .4)), alpha=ease(prog(t, .3, .2)))

def vis_countdown(dst, t, v, i):
    q = SC[v.get("quiz_scene", i - 1)]["vis"]
    # tarjeta reducida arriba + semáforo
    sub = Image.new("RGBA", (W, H), (0, 0, 0, 0)); quiz_card(sub, q, 10, {"opts": [1, 1, 1]}, enter=-1)
    sub = sub.crop((0, VZ[0] - 40, W, VZ[1] + 60)).resize((int(W * .62), int((VZ[1] - VZ[0] + 100) * .62)), Image.LANCZOS)
    p = eout(prog(t, 0, 0.4)); paste(dst, sub, W / 2 - 150 * p, CY - 10, alpha=1)
    starts = v.get("at", [1.25, 2.15, 3.05]); n = sum(1 for s in starts if t >= s)
    paste(dst, semaphore(n), W / 2 + 330 * p, CY, scale=0.6 + 0.4 * eback(prog(t, 0, .4)))
    if n:
        num = str(4 - n); pk = prog(t, starts[n - 1], 0.25)
        paste(dst, text(num, 260, [RED, (255, 176, 0), GREEN][n - 1], BLACK), W / 2 - 150, CY + 330, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))

def vis_reveal(dst, t, v, i):
    q = SC[v.get("quiz_scene", 2)]["vis"]; to = v.get("then_at")
    if to is None or t < to:
        a = 1 - ease(prog(t, to, 0.3)) if to else 1
        sub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        quiz_card(sub, q, 10, {"opts": [1, 1, 1], "reveal": eout(prog(t, 0.05, 0.5))}, enter=-1)
        paste(dst, sub, W / 2, H / 2, alpha=a)
        # confeti
        if t > 0.1:
            for k in range(26):
                ang = k * 2.4; r = 120 + 520 * eout(prog(t, 0.1, 1.0)); y = CY + math.sin(ang) * r * .7 + 300 * prog(t, .4, 1.5) ** 2
                d = ImageDraw.Draw(dst, "RGBA"); x = W / 2 + math.cos(ang) * r
                c = [YEL, GREEN, WHITE, BLUE_L][k % 4]; al = int(255 * (1 - prog(t, 0.9, 0.8)))
                d.rounded_rectangle((x - 9, y - 16, x + 9, y + 16), radius=4, fill=c + (al,))
    if to is not None and t >= to - 0.05:
        vis_compare(dst, t - to, v["compare"], i)

def vis_compare(dst, t, v, i):
    # ANTES / AHORA con imágenes directas
    p1, p2 = eback(prog(t, 0, .45)), eback(prog(t, .35, .45))
    for k, (px, p, data) in enumerate(((W / 2 - 235, p1, v["antes"]), (W / 2 + 235, p2, v["ahora"]))):
        c = card(430, 620, fill=(255, 255, 255, 250) if k else (225, 230, 238, 245), r=40, border=GREEN if k else None, bw=6 if k else 0)
        y = CY + 30 + (1 - p) * 160; a = ease(prog(t, k * .35, .3))
        paste(dst, c, px, y, alpha=a)
        paste(dst, pill(data["tag"], 34, GREEN if k else GREY, WHITE), px, y - 250, alpha=a)
        img = triangle(250, grey=True) if data["img"] == "triangle" else (beacon(230, on=int(t * 3) % 2 == 0) if data["img"] == "beacon" else None)
        if img: paste(dst, img, px, y - 40, alpha=a)
        for j, l in enumerate(data["txt"]): paste(dst, text(l, 40, DARK if k else (90, 96, 110), XB, shadow=False), px, y + 140 + j * 50, alpha=a)
        if not k and t > .9: paste(dst, icon_x(90, (200, 80, 80)), px + 150, y - 150, scale=eback(prog(t, .9, .3)))
        if k and t > 1.1: paste(dst, icon_check(90), px + 150, y - 150, scale=eback(prog(t, 1.1, .3)))

def vis_roof(dst, t, v, i):
    road_scene(dst, t * 0, label=None)
    car = car_rear(600); y = 1010; paste(dst, car, W / 2, y)
    if int(t * 2.4) % 2 == 0:
        for dx in (-220, 220): paste(dst, hazard(170), W / 2 + dx, y - car.height / 2 + car.height * .51)
    on = int(t * 4) % 2 == 0; bp = eback(prog(t, 0.2, 0.5))
    by = y - car.height / 2 - 70 - (1 - bp) * 300
    if on and t > .5:
        d = ImageDraw.Draw(dst, "RGBA")
        for k in range(10):
            ang = k * math.pi / 9 + math.pi; r1, r2 = 90, 210 + 30 * math.sin(t * 8)
            d.line([(W / 2 + math.cos(ang) * r1, by + math.sin(ang) * r1), (W / 2 + math.cos(ang) * r2, by + math.sin(ang) * r2)], fill=(255, 190, 40, 160), width=10)
    paste(dst, beacon(230, on=on), W / 2, by, alpha=ease(prog(t, .2, .2)))
    lp = eout(prog(t, .8, .4))
    paste(dst, chip_ok("EN EL TECHO", True), W / 2 - 230, VZ[0] + 60, alpha=lp, scale=.8 + .2 * eback(prog(t, .8, .4)))
    lp2 = eout(prog(t, 1.4, .4))
    paste(dst, chip_ok("A LA CARRETERA", False), W / 2 + 230, VZ[0] + 60, alpha=lp2, scale=.8 + .2 * eback(prog(t, 1.4, .4)))

@lru_cache(maxsize=32)
def chip_ok(txt, ok):
    p = pill(txt, 36, WHITE, DARK, padx=34 + 52); im = Image.new("RGBA", (p.width + 20, p.height + 20), (0, 0, 0, 0))
    im.alpha_composite(p, (10, 10)); ic = (icon_check if ok else icon_x)(56)
    im.alpha_composite(ic, (22, 10 + (p.height - 56) // 2)); return im

def vis_cta(dst, t, v, i):
    bp = eback(prog(t, 0, .45)); bb = bubble(780, 360)
    paste(dst, bb, W / 2, CY - 40, scale=.7 + .3 * bp, alpha=ease(prog(t, 0, .2)))
    big = v.get("big", "¿A, B o C?"); s = fit([big], 140, BLACK, 680)
    paste(dst, text(big, s, BLUE, BLACK, shadow=False), W / 2, CY - 110, scale=.7 + .3 * bp, alpha=ease(prog(t, 0, .2)))
    paste(dst, text(v.get("small", "Dímelo en comentarios"), 44, DARK, XB, shadow=False), W / 2, CY + 20, alpha=ease(prog(t, .3, .3)))
    ay = CY + 300 + math.sin(t * 7) * 22; d = ImageDraw.Draw(dst, "RGBA"); a = int(255 * ease(prog(t, .4, .3)))
    d.polygon([(W / 2 - 70, ay - 40), (W / 2 + 70, ay - 40), (W / 2, ay + 50)], fill=YEL + (a,))
    d.rectangle((W / 2 - 26, ay - 120, W / 2 + 26, ay - 38), fill=YEL + (a,))

# --- vista cenital de autovía (pasillo de emergencia) ---
LANE_X = (W / 2 - 150, W / 2 + 150)
CAR_COLS = [(226, 69, 60), (245, 245, 245), (40, 40, 48), (255, 196, 0), (60, 140, 255), (130, 140, 155)]
def topdown(out, t, phase, pt, show_amb=True, highlight=False):
    """phase 0 atasco, 1 izquierda se aparta, 2 derecha se aparta, 3 ambulancia pasa. pt = progreso 0..1 de la fase"""
    dst = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dst, "RGBA"); x0, x1 = W / 2 - 340, W / 2 + 340; top, bot = VZ[0] + 10, VZ[1] + 20
    d.rectangle((x0 - 40, top, x1 + 40, bot), fill=(70, 80, 60, 255))
    d.rectangle((x0, top, x1, bot), fill=(36, 40, 50, 255))
    d.line([(x0 + 10, top), (x0 + 10, bot)], fill=(255, 255, 255, 230), width=8); d.line([(x1 - 10, top), (x1 - 10, bot)], fill=(255, 255, 255, 230), width=8)
    for k in range(9):
        y = top + k * 110; d.line([(W / 2, y), (W / 2, y + 60)], fill=(255, 255, 255, 200), width=8)
    kl = 1.0 if phase > 1 else (ease(pt) if phase == 1 else 0); kr = 1.0 if phase > 2 else (ease(pt) if phase == 2 else 0)
    if highlight or phase == 3:
        ha = int(110 * ease(pt if phase == 3 else 1)); cw = 90 + 0
        d.rectangle((W / 2 - cw, top, W / 2 + cw, bot), fill=(34, 197, 94, ha))
    rows = [top + 120 + r * 265 for r in range(3)]
    for row, y in enumerate(rows):
        for side, k in ((0, kl), (1, kr)):
            col = CAR_COLS[(row * 2 + side) % len(CAR_COLS)]
            x = LANE_X[side] + (-1 if side == 0 else 1) * 125 * k
            jig = math.sin(t * 3 + row + side) * 2
            paste(dst, car_top(col, 132), x + jig, y)
    for row, y in enumerate(rows):
        for side in (0, 1):
            if ((phase == 1 and side == 0) or (phase == 2 and side == 1)) and pt < .95:
                dirn = -1 if side == 0 else 1; a = int(255 * (1 - prog(pt, .7, .25)))
                arrow(d, W / 2 + dirn * 20, y, dirn, a)
    if show_amb:
        if phase < 3: ay = bot + 30 - 25 * ease(prog(t, 0, 1.0)) - 8 * math.sin(t * 3)
        else: ay = lerp(bot + 5, top + 200, ease(pt))
        paste(dst, ambulance_top(150, int(t * 6) % 2), W / 2, ay)
        for k in range(3):
            r = ((t * 1.4 + k / 3) % 1) * 260
            d.ellipse((W / 2 - r, ay - 120 - r, W / 2 + r, ay - 120 + r), outline=(80, 150, 255, int(170 * (1 - r / 260))), width=6)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((x0 - 40, top, x1 + 40, bot), radius=36, fill=255)
    dst.putalpha(Image.fromarray(np.minimum(np.array(dst.split()[3]), np.array(m))))
    out.alpha_composite(dst)

def arrow(d, x, y, dirn, a):
    d.polygon([(x + dirn * 60, y), (x, y - 40), (x, y + 40)], fill=YEL + (a,))
    d.rectangle((min(x, x - dirn * 50), y - 15, max(x, x - dirn * 50), y + 15), fill=YEL + (a,))

def vis_topdown(dst, t, v, i):
    ph = v.get("phase", 0); dur = max(1.0, (B[i + 1] - B[i]) * v.get("speed", 0.75))
    topdown(dst, t, ph, prog(t, 0.15, dur), highlight=v.get("highlight", False))
    if v.get("tag"):
        paste(dst, pill(v["tag"], 36, GREEN if ph == 3 else YEL, WHITE if ph == 3 else NAVY), W / 2, VZ[0] + 70,
              scale=eback(prog(t, .3, .4)), alpha=ease(prog(t, .3, .3)))

def vis_law(dst, t, v, i):
    p = eback(prog(t, 0, .5)); c = doc_card(); paste(dst, c, W / 2, CY + (1 - p) * 220, alpha=ease(prog(t, 0, .25)), rot=(1 - p) * 6)
    paste(dst, text(v.get("title1", "Reglamento General"), 50, DARK, BLACK, shadow=False), W / 2, CY - 130, alpha=ease(prog(t, .2, .3)))
    paste(dst, text(v.get("title2", "de Circulación"), 50, DARK, BLACK, shadow=False), W / 2, CY - 70, alpha=ease(prog(t, .2, .3)))
    sp = prog(t, .7, .22)
    if sp > 0: paste(dst, stamp2(v.get("stamp", "R.D. 518/2026")), W / 2 + 40, CY + 110, scale=lerp(2.2, 1, eout(sp)), alpha=ease(sp * 1.6), rot=-8)
    if v.get("badge"): paste(dst, pill(v["badge"], 40, YEL, NAVY), W / 2, CY + 330, scale=eback(prog(t, 1.1, .4)), alpha=ease(prog(t, 1.1, .3)))

@lru_cache(maxsize=8)
def stamp2(txt):
    f = F(BLACK, 76); w = int(f.getlength(txt)) + 80; h = 140; im = ss(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w * 2 - 6, h * 2 - 6), radius=30, outline=BLUE, width=16)
    bb = F(BLACK, 152).getbbox(txt); d.text((w - (bb[0] + bb[2]) / 2, h - (bb[1] + bb[3]) / 2), txt, font=F(BLACK, 152), fill=BLUE)
    return down(im)

def vis_nocross(dst, t, v, i):
    topdown(dst, t, 3, 1.0, show_amb=False, highlight=True)
    # coche que intenta cruzarse por delante en diagonal
    p = ease(prog(t, 0.2, 1.4)); x = lerp(W / 2 - 275, W / 2 + 40, p); y = lerp(VZ[0] + 830, VZ[0] + 540, p)
    d = ImageDraw.Draw(dst, "RGBA")
    for k in range(12):
        q = k / 12
        qx, qy = lerp(W / 2 - 275, W / 2 + 40, q), lerp(VZ[0] + 830, VZ[0] + 540, q)
        if q < p: d.ellipse((qx - 8, qy - 8, qx + 8, qy + 8), fill=RED + (220,))
    paste(dst, car_top((255, 120, 0), 140), x, y, rot=-35 * p)
    xp = prog(t, 1.4, .25)
    if xp > 0: paste(dst, icon_x(220), W / 2, CY, scale=lerp(2, 1, eout(xp)), alpha=ease(xp * 2))
    if xp > 0.5: paste(dst, pill("NUNCA", 56, RED, WHITE), W / 2, CY + 190, scale=eback(prog(t, 1.6, .35)))

def vis_save(dst, t, v, i):
    p = eback(prog(t, 0, .5)); paste(dst, bookmark(260), W / 2, CY - 120 + math.sin(t * 4) * 10, scale=.6 + .4 * p, alpha=ease(prog(t, 0, .2)))
    paste(dst, text(v.get("big", "GUÁRDALO"), 130, WHITE, BLACK), W / 2, CY + 170, scale=.7 + .3 * eback(prog(t, .2, .4)), alpha=ease(prog(t, .2, .3)))
    paste(dst, text(v.get("small", "para tu examen"), 56, YEL, XB), W / 2, CY + 290, alpha=ease(prog(t, .45, .3)))

def vis_mito(dst, t, v, i):
    # MITO o VERDAD: frase en tarjeta + sello
    p = eback(prog(t, 0, .45)); c = card(880, 520, fill=(255, 255, 255, 250), r=44); paste(dst, c, W / 2, CY, alpha=ease(prog(t, 0, .2)), scale=.85 + .15 * p)
    ql = wrap(v["frase"], 60, XB, 760)
    for k, l in enumerate(ql): paste(dst, text(l, 60, DARK, XB, shadow=False), W / 2, CY - (len(ql) - 1) * 38 + k * 76, alpha=ease(prog(t, .1, .3)))
    if v.get("verdict"):
        sp = prog(t, v.get("at", 1.0), .2)
        if sp > 0:
            col = GREEN if v["verdict"] == "VERDAD" else RED
            paste(dst, stamp_col(v["verdict"], col), W / 2 + 140, CY + 230, scale=lerp(2.2, 1, eout(sp)), alpha=ease(sp * 1.6), rot=-10)

@lru_cache(maxsize=8)
def stamp_col(txt, col):
    f = F(BLACK, 96); w = int(f.getlength(txt)) + 90; h = 170; im = ss(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w * 2 - 6, h * 2 - 6), radius=36, outline=col, width=18)
    bb = F(BLACK, 192).getbbox(txt); d.text((w - (bb[0] + bb[2]) / 2, h - (bb[1] + bb[3]) / 2), txt, font=F(BLACK, 192), fill=col)
    return down(im)

def vis_stat(dst, t, v, i):
    # número grande que cuenta hacia arriba (p. ej. "90 km/h")
    p = eout(prog(t, 0, 1.0)); val = v["value"]; dec = v.get("dec", 0); unit = v.get("unit", "")
    num = f"{val * p:.{dec}f}".replace(".", ",") if dec else f"{int(round(val * p))}"
    paste(dst, text(num, 300, YEL, BLACK), W / 2, CY - 60, scale=.8 + .2 * eback(prog(t, 0, .4)))
    paste(dst, text(unit, 80, WHITE, BLACK), W / 2, CY + 140, alpha=ease(prog(t, .3, .3)))
    if v.get("sub"): paste(dst, pill(v["sub"], 40, WHITE, BLUE), W / 2, CY + 270, alpha=ease(prog(t, .6, .3)))

def vis_sign(dst, t, v, i):
    # señal redonda genérica dibujada: {"kind": "speed", "n": 90} (límite) | {"kind": "noentry"} | {"kind": "b"}
    p = eback(prog(t, 0, .5)); s = 560
    paste(dst, sign_generic(v.get("kind", "speed"), v.get("n", 90), s), W / 2, CY - 30, scale=.5 + .5 * p, alpha=ease(prog(t, 0, .25)), rot=(1 - p) * -20)
    if v.get("tag"): paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, CY + 330, scale=eback(prog(t, .5, .35)), alpha=ease(prog(t, .5, .3)))

@lru_cache(maxsize=16)
def sign_generic(kind, n, s):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    if kind == "speed":
        d.ellipse((0, 0, S - 1, S - 1), fill=(220, 30, 40)); d.ellipse((S * .12, S * .12, S * .88, S * .88), fill=WHITE)
        f = F(BLACK, int(S * .42)); txt = str(n); bb = f.getbbox(txt)
        d.text((S / 2 - (bb[0] + bb[2]) / 2, S / 2 - (bb[1] + bb[3]) / 2), txt, font=f, fill=(20, 20, 20))
    elif kind == "noentry":
        d.ellipse((0, 0, S - 1, S - 1), fill=(220, 30, 40)); d.rounded_rectangle((S * .16, S * .42, S * .84, S * .58), radius=10, fill=WHITE)
    else:
        return sign_b(s)
    return glow(down(im), 30, .5)

# --- cruce sin señalizar visto desde arriba con coches numerados (formato ¿QUIÉN PASA PRIMERO?) ---
# coche 1: sube (viene del sur); coche 2: viene por el este hacia el oeste; coche 3: viene del oeste hacia el este.
# vis: {"type": "cruce", "nosigns": bool, "countdown": [t1,t2,t3], "done": [2], "move": [[2, 0.3, 1.2]],
#       "focus": 1, "tag": "...", "rank": ["2", "1", "3"], "rank_at": [..]}
RW = 150  # ancho de carril
CRUCE_COLS = {1: (226, 69, 60), 2: (60, 140, 255), 3: (255, 196, 0)}
def cruce_pos(n, k):
    """posición (x, y, rot) del coche n con avance k (0 parado en la línea, 1 fuera de la zona)."""
    cx, cy = W / 2, CY
    if n == 1: return cx + RW / 2, lerp(cy + RW + 140, VZ[0] - 220, k), 0
    if n == 2: return lerp(cx + RW + 150, -220, k), cy - RW / 2, 90
    return lerp(cx - RW - 150, W + 220, k), cy + RW / 2, -90

@lru_cache(maxsize=16)
def num_badge(n, s=86, col=WHITE, fg=NAVY):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.ellipse((0, 0, S - 1, S - 1), fill=fg); d.ellipse((S * .08, S * .08, S * .92, S * .92), fill=col)
    f = F(BLACK, int(S * .58)); txt = str(n); bb = f.getbbox(txt)
    d.text((S / 2 - (bb[0] + bb[2]) / 2, S / 2 - (bb[1] + bb[3]) / 2), txt, font=f, fill=fg)
    return down(im)

@lru_cache(maxsize=4)
def sign_ceda(s=170):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.polygon([(S * .04, S * .1), (S * .96, S * .1), (S / 2, S * .92)], fill=(220, 30, 40))
    d.polygon([(S * .22, S * .21), (S * .78, S * .21), (S / 2, S * .7)], fill=WHITE)
    return down(im)

def vis_cruce(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: coches, números y pregunta ya en pantalla
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; cx, cy = W / 2, CY
    d.rectangle((40, top, W - 40, bot), fill=(64, 92, 60, 255))
    for k in range(40):  # textura de césped
        gx, gy = 60 + (k * 263) % (W - 120), top + (k * 157) % (bot - top)
        d.ellipse((gx - 30, gy - 18, gx + 30, gy + 18), fill=(74, 104, 68, 255))
    d.rectangle((40, cy - RW, W - 40, cy + RW), fill=(36, 40, 50, 255))
    d.rectangle((cx - RW, top, cx + RW, bot), fill=(36, 40, 50, 255))
    for x0, x1 in ((40, cx - RW), (cx + RW, W - 40)):  # bordes y eje en brazos horizontales
        d.line([(x0, cy - RW + 8), (x1, cy - RW + 8)], fill=(255, 255, 255, 220), width=6)
        d.line([(x0, cy + RW - 8), (x1, cy + RW - 8)], fill=(255, 255, 255, 220), width=6)
        x = x0 + 10
        while x < x1 - 40: d.line([(x, cy), (x + 50, cy)], fill=(255, 255, 255, 200), width=7); x += 95
    for y0, y1 in ((top, cy - RW), (cy + RW, bot)):
        d.line([(cx - RW + 8, y0), (cx - RW + 8, y1)], fill=(255, 255, 255, 220), width=6)
        d.line([(cx + RW - 8, y0), (cx + RW - 8, y1)], fill=(255, 255, 255, 220), width=6)
        y = y0 + 10
        while y < y1 - 40: d.line([(cx, y), (cx, y + 50)], fill=(255, 255, 255, 200), width=7); y += 95
    if v.get("dirt"):  # brazo este = camino de tierra (sin asfaltar): sin marcas, bordes irregulares, piedras y rodadas
        x0 = cx + RW; d.rectangle((x0, cy - RW - 14, W - 40, cy + RW + 14), fill=(64, 92, 60, 255))
        for k in range(8): gx = x0 + 40 + k * 70; d.ellipse((gx - 30, cy - RW - 30, gx + 30, cy - RW + 6), fill=(74, 104, 68, 255))
        L = W - 40 - x0
        up = [(x0, cy - RW)] + [(x0 + L * (k + 1) / 13, cy - RW + 12 + 10 * math.sin(k * 1.7)) for k in range(12)] + [(W - 40, cy - RW + 14)]
        lo = [(W - 40, cy + RW - 14)] + [(W - 40 - L * (k + 1) / 13, cy + RW - 12 - 10 * math.sin(k * 2.3)) for k in range(12)] + [(x0, cy + RW)]
        d.polygon(up + lo, fill=(158, 118, 72, 255))
        for k in range(60):  # gravilla
            gx = x0 + 20 + (k * 97) % (W - 80 - x0); gy = cy - RW + 30 + (k * 53) % (2 * RW - 60); r = 4 + (k % 4) * 2
            d.ellipse((gx - r, gy - r, gx + r, gy + r), fill=(120, 88, 52, 255) if k % 3 else (190, 160, 120, 255))
        for ty in (cy - RW / 2 - 40, cy - RW / 2 + 40, cy + RW / 2 - 40, cy + RW / 2 + 40):  # rodadas
            d.line([(x0 + 10, ty), (W - 40, ty + 6 * math.sin(ty))], fill=(132, 96, 58, 255), width=14)
        if v.get("dirt_hl"):
            pa = ease(prog(t, .2, .4)); a = int(255 * pa * (.6 + .4 * math.sin(t * 7)))
            d.rounded_rectangle((x0 + 4, cy - RW - 6, W - 44, cy + RW + 6), radius=20, outline=ORANGE + (a,), width=12)
    fc = v.get("focus")
    if fc:  # zona "su derecha" resaltada para el coche fc (1 = brazo este)
        pa = ease(prog(t, .3, .5)); a = int(120 * pa * (.75 + .25 * math.sin(t * 6)))
        d.rectangle((cx + RW, cy - RW, W - 40, cy + RW), fill=(34, 197, 94, a))
    done = set(v.get("done", [])); moves = {m[0]: (m[1], m[2]) for m in v.get("move", [])}
    for n in (1, 2, 3):
        if n in done: continue
        k = 0.0
        if n in moves: s, du = moves[n]; k = ease(prog(t, s, du)) ** 1.4
        x, y, rot = cruce_pos(n, k)
        x0, y0, _ = cruce_pos(n, 0.0)
        if k == 0 and t < .5 and not v.get("still"):  # entrada al cruce
            e = eout(prog(t, 0, .5)); dx, dy = {1: (0, 160), 2: (160, 0), 3: (-160, 0)}[n]; x += dx * (1 - e); y += dy * (1 - e)
        car = car_top(CRUCE_COLS[n], 120); paste(lay, car, x, y, rot=rot)
        if k < .02:  # flecha de dirección
            al = int(230 * (.6 + .4 * math.sin(t * 5)))
            if n == 1: arrow_v(d, x, y - 175, -1, al)
            else: arrow(d, x + (-150 if n == 2 else 150), y, -1 if n == 2 else 1, al)
        bx, by = {1: (x + 125, y + 30), 2: (x + 20, y - 125), 3: (x - 20, y + 125)}[n]
        paste(lay, num_badge(n), bx, by, scale=eback(prog(t, .15 + n * .12, .35)) if not v.get("still") else 1)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    if v.get("nosigns"):  # sin señales: ceda y semáforo tachados en las esquinas
        for k, (ix, iy) in enumerate(((cx - RW - 200, top + 150), (W - 150, bot - 150))):
            p = prog(t, .2 + k * .35, .35); im = sign_ceda(170) if k == 0 else semaphore(0).resize((92, 240), Image.LANCZOS)
            paste(dst, im, ix, iy, scale=.6 + .4 * eback(p), alpha=ease(p * 2))
            if t > .55 + k * .35: paste(dst, icon_x(110), ix + 60, iy + 70, scale=eback(prog(t, .55 + k * .35, .3)))
    cd = v.get("countdown")
    if cd:
        n = sum(1 for s in cd if t >= s); ix, iy = cx - RW - 270, top + 160
        paste(dst, semaphore(n).resize((115, 300), Image.LANCZOS), ix, iy, scale=eback(prog(t, 0, .4)))
        if n:
            pk = prog(t, cd[n - 1], .25)
            paste(dst, text(str(4 - n), 200, [RED, (255, 176, 0), GREEN][n - 1], BLACK), cx - RW - 105, iy, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))
    rk = v.get("rank")
    if rk:  # clasificación en la esquina superior izquierda (césped libre)
        ra = v.get("rank_at", [0] * len(rk))
        for j, (lab, at) in enumerate(zip(rk, ra)):
            p = prog(t, at, .35)
            if p > 0: paste(dst, rank_chip(j + 1, int(lab)), cx - RW - 205, top + 62 + j * 90, scale=eback(p), alpha=ease(p * 2))
    if v.get("tag"):
        paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, top + 60, scale=eback(prog(t, .4, .4)), alpha=ease(prog(t, .4, .3)))

@lru_cache(maxsize=16)
def rank_chip(pos, car):
    p = pill(f"{pos}º", 44, NAVY if pos > 1 else YEL, WHITE if pos > 1 else NAVY, padx=26); b = num_badge(car, 74, mix(CRUCE_COLS[car], WHITE, .15), NAVY)
    im = Image.new("RGBA", (p.width + b.width + 12, max(p.height, b.height)), (0, 0, 0, 0))
    im.alpha_composite(p, (0, (im.height - p.height) // 2)); im.alpha_composite(b, (p.width + 12, (im.height - b.height) // 2)); return im

def arrow_v(d, x, y, dirn, a):
    d.polygon([(x, y + dirn * 60), (x - 40, y), (x + 40, y)], fill=YEL + (a,))
    d.rectangle((x - 15, min(y, y - dirn * 50), x + 15, max(y, y - dirn * 50)), fill=YEL + (a,))

# --- neumático: dibujo y profundidad (formato CIFRA CLAVE, bloque vehículo y seguridad) ---
# vis: {"type": "tyre", "mode": "tread" | "gauge" | "wet" | "compare", "mm": 1.6, "from_mm": 8, "tag": "..."}
@lru_cache(maxsize=None)
def tyre_front(w=470, h=820, off=0):
    im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .22), fill=(34, 34, 40))
    gx = [X * .3, X * .5, X * .7]
    for k in range(-1, 14):  # laminillas diagonales (se desplazan con off para que parezca que rueda)
        y = k * Y / 12 + off * 2
        for a, b in ((X * .08, X * .26), (X * .34, X * .46), (X * .54, X * .66), (X * .74, X * .92)):
            d.line([(a, y), (b, y + Y * .045)], fill=(18, 18, 22), width=int(X * .025))
    for x in gx: d.rectangle((x - X * .03, 0, x + X * .03, Y), fill=(14, 14, 18))
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .22), outline=(70, 72, 82), width=int(X * .02))
    m = Image.new("L", (X, Y), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .22), fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.array(im.split()[3]), np.array(m))))
    return down(im)

PXMM = 34  # píxeles por milímetro en el corte del neumático
def tread_section(dst, cx, base, depth, w=760, col=(40, 40, 46), warn=False):
    d = ImageDraw.Draw(dst, "RGBA"); hgt = depth * PXMM
    d.rounded_rectangle((cx - w / 2, base, cx + w / 2, base + 120), radius=20, fill=(28, 28, 34, 255))  # carcasa
    nb = 4; gw = 56; bw = (w - gw * (nb - 1)) / nb
    for k in range(nb):
        x0 = cx - w / 2 + k * (bw + gw)
        d.rounded_rectangle((x0, base - hgt, x0 + bw, base + 10), radius=10, fill=col + (255,))
    d.rectangle((cx - w / 2, base - 4, cx + w / 2, base + 6), fill=(255, 80, 80, 200) if warn else (28, 28, 34, 255))
    return [cx - w / 2 + k * (bw + gw) + bw + gw / 2 for k in range(nb - 1)]

def depth_label(dst, x, base, depth, col, t, a=1.0):
    d = ImageDraw.Draw(dst, "RGBA"); top = base - depth * PXMM; al = int(255 * a)
    d.line([(x, top), (x, base)], fill=col + (al,), width=8)
    for yy in (top, base): d.line([(x - 22, yy), (x + 22, yy)], fill=col + (al,), width=8)
    s = f"{depth:.1f}".replace(".", ",") + " mm"; paste(dst, pill(s, 46, col, WHITE), x, top - 70, alpha=a)

def vis_tyre(dst, t, v, i):
    mode = v.get("mode", "tread")
    if mode in ("tread", "wet"):
        p = eback(prog(t, 0, .5)); off = int(t * 260) % int(820 * 2 / 12 / 2)
        tx = W / 2 if mode == "tread" else W / 2 - 150
        paste(dst, tyre_front(470, 820, off), tx, CY + 10, scale=.6 + .4 * p, alpha=ease(prog(t, 0, .25)))
        if mode == "tread":
            for k, gx in enumerate((.3, .5, .7)):  # ranuras principales señaladas
                pa = prog(t, .6 + k * .15, .3)
                if pa > 0:
                    x = tx - 235 + 470 * gx; dd = ImageDraw.Draw(dst, "RGBA")
                    dd.rounded_rectangle((x - 16, CY - 400, x + 16, CY + 420), radius=14, outline=YEL + (int(255 * ease(pa * 2)),), width=6)
        else:
            dd = ImageDraw.Draw(dst, "RGBA")
            for k in range(36):  # lluvia
                z = (t * 1.3 + k * .137) % 1; x = 120 + (k * 97) % (W - 240); y = VZ[0] + z * (VZ[1] - VZ[0])
                dd.line([(x, y), (x - 14, y + 46)], fill=(150, 200, 255, 170), width=5)
            dd.rounded_rectangle((tx - 330, CY + 395, tx + 330, CY + 445), radius=20, fill=(70, 140, 255, 150))  # lámina de agua
            for k in range(20):  # salpicadura a los lados del agua que no se evacúa
                z = (t * 1.6 + k / 20) % 1; sd = -1 if k % 2 else 1; ang = -1.1 - (k // 2) * .06
                x = tx + sd * (240 + (260 + (k // 2) * 14) * z); y = CY + 405 - (300 + (k // 2) * 10) * z + 360 * z * z
                r = 14 + 10 * (1 - z); dd.ellipse((x - r, y - r, x + r, y + r), fill=(110, 175, 255, int(230 * (1 - z))))
            pa = prog(t, .7, .3)
            paste(dst, icon_x(150), W / 2 + 270, CY - 200, scale=eback(pa), alpha=ease(pa * 2))
            paste(dst, pill(v.get("tag", "MENOS AGARRE"), 40, RED, WHITE), W / 2 + 270, CY - 50, scale=eback(prog(t, .9, .35)), alpha=ease(prog(t, .9, .3)))
            return
    elif mode == "gauge":
        base = CY + 240; fm, mm = v.get("from_mm", 8.0), v.get("mm", 1.6)
        k = ease(prog(t, .5, 1.4)); dep = lerp(fm, mm, k); warn = k > .98
        paste(dst, card(900, 760, fill=(236, 241, 250, 255), r=44), W / 2, CY + 20, alpha=ease(prog(t, 0, .25)))
        paste(dst, pill("CORTE DEL NEUMÁTICO", 34, BLUE, WHITE), W / 2, VZ[0] + 110, alpha=ease(prog(t, 0, .3)))
        gx = tread_section(dst, W / 2, base, dep, warn=warn)
        depth_label(dst, gx[1], base, dep, RED if warn else YEL, t)
        if warn: paste(dst, pill(v.get("tag", "MÍNIMO LEGAL"), 42, RED, WHITE), W / 2, base + 210, scale=eback(prog(t, 2.0, .35)))
    elif mode == "compare":
        for k, (mm, ok) in enumerate(((3.0, True), (1.6, False))):
            px = W / 2 + (-240 if k == 0 else 240); a = ease(prog(t, k * .45, .3)); y = CY + 30 + (1 - eback(prog(t, k * .45, .45))) * 150
            c = card(440, 640, fill=(255, 255, 255, 250), r=40, border=GREEN if ok else RED, bw=6); paste(dst, c, px, y, alpha=a)
            sub = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gx = tread_section(sub, W / 2, 1100, mm, w=640, warn=not ok)
            depth_label(sub, gx[1], 1100, mm, GREEN if ok else RED, t)
            sub = sub.crop((W / 2 - 200, 1100 - 190, W / 2 + 200, 1100 + 130))
            paste(dst, sub, px, y + 20, alpha=a)
            paste(dst, pill("CAMBIAR AQUÍ" if ok else "LÍMITE LEGAL", 32, GREEN if ok else RED, WHITE), px, y - 230, alpha=a)
            paste(dst, (icon_check if ok else icon_x)(96), px, y + 220, scale=eback(prog(t, .9 + k * .3, .3)))

# --- carné por puntos (formato ERROR DE NOVATO, bloque documentación, puntos y noveles) ---
# vis: {"type": "puntos", "mode": "card", "from": 12, "n": 8, "cross": true, "tag": "NOVEL"}
#      {"type": "puntos", "mode": "steps", "upto": 0..3}  -> escalera 8 > 12 > 14 > 15
@lru_cache(maxsize=None)
def licence_card(w=820, h=500):
    c = card(w, h, fill=(250, 226, 232, 255), r=34); d = ImageDraw.Draw(c); ox, oy = 40, 40
    d.rounded_rectangle((ox, oy, ox + w, oy + 110), radius=34, fill=BLUE); d.rectangle((ox, oy + 70, ox + w, oy + 110), fill=BLUE)
    d.text((ox + 40, oy + 30), "PERMISO DE CONDUCCIÓN", font=F(BLACK, 46), fill=WHITE)
    paste(c, sign_b(120), ox + w - 90, oy + 230)
    d.rounded_rectangle((ox + 40, oy + 150, ox + 230, oy + 400), radius=20, fill=(214, 200, 210))  # foto
    d.ellipse((ox + 95, oy + 185, ox + 175, oy + 265), fill=(150, 130, 145))
    d.pieslice((ox + 65, oy + 280, ox + 205, oy + 420), 180, 360, fill=(150, 130, 145))
    for k in range(5):
        y = oy + 170 + k * 46; d.rounded_rectangle((ox + 270, y, ox + w - 190 - (k % 2) * 80, y + 18), radius=9, fill=(222, 196, 206))
    return c

@lru_cache(maxsize=64)
def dots_row(n, total=15, s=46, col=YEL):
    gap = 12; im = ss(total * (s + gap), s); d = ImageDraw.Draw(im)
    for k in range(total):
        x = k * (s + gap) * 2
        if k < n: d.ellipse((x, 0, x + s * 2 - 1, s * 2 - 1), fill=col)
        else: d.ellipse((x + 4, 4, x + s * 2 - 5, s * 2 - 5), outline=(255, 255, 255, 110), width=6)
    return down(im)

def vis_puntos(dst, t, v, i):
    mode = v.get("mode", "card")
    if mode == "card":
        p = eback(prog(t, 0, .5)); cy = CY - 150
        paste(dst, licence_card(), W / 2, cy + (1 - p) * 180, alpha=ease(prog(t, 0, .25)), rot=(1 - p) * -8)
        fr, n = v.get("from", v.get("n", 8)), v.get("n", 8); cs = v.get("count_at", .5)
        k = ease(prog(t, cs, .9)); val = int(round(lerp(fr, n, k)))
        ny = CY + 230; col = YEL if val <= n or fr == n else WHITE
        paste(dst, text(str(val), 230, col, BLACK), W / 2 - 150, ny, scale=.8 + .2 * eback(prog(t, .2, .4)))
        paste(dst, text("PUNTOS", 84, WHITE, BLACK), W / 2 + 150, ny + 10, alpha=ease(prog(t, .3, .3)))
        paste(dst, dots_row(val), W / 2, ny + 165, alpha=ease(prog(t, .3, .3)))
        if v.get("cross"):
            xp = prog(t, v.get("cross_at", 1.0), .22)
            if xp > 0:
                d = ImageDraw.Draw(dst, "RGBA"); a = int(255 * ease(xp * 2)); L = 190 * eout(xp)
                cx, cyy = W / 2 - 150, ny
                d.line([(cx - L, cyy - L * .7), (cx + L, cyy + L * .7)], fill=RED + (a,), width=26)
                d.line([(cx - L, cyy + L * .7), (cx + L, cyy - L * .7)], fill=RED + (a,), width=26)
        if v.get("tag"):
            paste(dst, pill(v["tag"], 44, RED if v.get("cross") else YEL, WHITE if v.get("cross") else NAVY), W / 2 + 200, cy + 215,
                  scale=eback(prog(t, v.get("tag_at", 1.2), .35)), alpha=ease(prog(t, v.get("tag_at", 1.2), .3)), rot=-6)
    else:  # escalera de puntos
        steps = [(8, "INICIO"), (12, "+2 AÑOS"), (14, "+3 AÑOS"), (15, "+3 AÑOS")]; upto = v.get("upto", 3)
        d = ImageDraw.Draw(dst, "RGBA"); base = VZ[1] - 120; bw = 200; gap = 30; x0 = W / 2 - (4 * bw + 3 * gap) / 2
        d.line([(x0 - 30, base), (x0 + 4 * bw + 3 * gap + 30, base)], fill=(255, 255, 255, 120), width=6)
        for k, (n, lab) in enumerate(steps):
            if k > upto: continue
            new = k == upto; p = ease(prog(t, .1, .8)) if new else 1.0
            hgt = n * 40 * p; x = x0 + k * (bw + gap)
            col = (GREEN if n == 15 else YEL) if new else (90, 120, 170)
            d.rounded_rectangle((x, base - hgt, x + bw, base), radius=22, fill=col + (255,))
            num = str(int(round(n * p))) if new else str(n)
            paste(dst, text(num, 96, NAVY if new else WHITE, BLACK, shadow=False), x + bw / 2, base - hgt + 70, alpha=1 if hgt > 120 else 0)
            paste(dst, text(lab, 38, YEL if new else (190, 205, 230), XB), x + bw / 2, base + 50)
        if upto == 3:
            pa = prog(t, 1.0, .35); paste(dst, pill("MÁXIMO", 46, GREEN, WHITE), x0 + 3 * (bw + gap) + bw / 2, base - 15 * 40 - 70, scale=eback(pa), alpha=ease(pa * 2))
        if v.get("tag"): paste(dst, pill(v["tag"], 40, WHITE, BLUE), W / 2, VZ[0] + 40, alpha=ease(prog(t, .2, .3)))

# --- ciclista visto desde arriba + coche adelantando (formato POV, bloque peatones, ciclistas y patinetes) ---
# vis: {"type": "bike", "mode": "approach" | "pass" | "twolanes", "limit": 90, "tag": "..."}
@lru_cache(maxsize=8)
def cyclist_top(ph=0, s=1.0):
    w, h = 110, 230; im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((X * .44, Y * .02, X * .56, Y * .3), radius=10, fill=(20, 20, 24))      # rueda delantera
    d.rounded_rectangle((X * .44, Y * .7, X * .56, Y * .98), radius=10, fill=(20, 20, 24))      # rueda trasera
    d.line([(X * .5, Y * .2), (X * .5, Y * .8)], fill=(70, 74, 86), width=14)                    # cuadro
    d.line([(X * .12, Y * .24), (X * .88, Y * .24)], fill=(40, 40, 46), width=14)                # manillar
    lo = (1 if ph % 2 else -1) * Y * .05
    for sx, off in ((-1, lo), (1, -lo)):                                                         # piernas pedaleando
        d.rounded_rectangle((X * .5 + sx * X * .1 - X * .07, Y * .5 + off, X * .5 + sx * X * .1 + X * .07, Y * .68 + off), radius=14, fill=(30, 40, 70))
    d.line([(X * .22, Y * .42), (X * .14, Y * .25)], fill=(240, 200, 170), width=16)              # brazos
    d.line([(X * .78, Y * .42), (X * .86, Y * .25)], fill=(240, 200, 170), width=16)
    d.ellipse((X * .12, Y * .36, X * .88, Y * .58), fill=ORANGE)                                  # espalda (maillot)
    d.ellipse((X * .3, Y * .28, X * .7, Y * .46), fill=WHITE)                                     # casco
    d.rectangle((X * .47, Y * .28, X * .53, Y * .46), fill=RED)
    return glow(down(im), 14, .35)

def bike_road(dst, t, two_lanes=False, scroll=True):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; x0, x1 = W / 2 - 330, W / 2 + 330
    d.rectangle((40, top, W - 40, bot), fill=(64, 92, 60, 255))
    for k in range(30):
        gx = 60 + (k * 263) % (W - 120); gy = top + ((k * 157 + (t * 260 if scroll else 0)) % (bot - top))
        if x0 - 30 < gx < x1 + 30: continue
        d.ellipse((gx - 26, gy - 16, gx + 26, gy + 16), fill=(74, 104, 68, 255))
    d.rectangle((x0, top, x1, bot), fill=(36, 40, 50, 255))
    d.line([(x0 + 12, top), (x0 + 12, bot)], fill=(255, 255, 255, 230), width=8); d.line([(x1 - 12, top), (x1 - 12, bot)], fill=(255, 255, 255, 230), width=8)
    off = (t * 300) % 140 if scroll else 0
    for k in range(-1, 9):
        y = top + k * 140 + off; d.line([(W / 2, y), (W / 2, y + 70)], fill=(255, 255, 255, 210), width=9)
    if two_lanes:  # flechas pintadas: los dos carriles en el mismo sentido
        for lx in (W / 2 - 165, W / 2 + 165):
            for k in range(2):
                y = top + 200 + k * 520 + off
                if y < bot - 60:
                    d.polygon([(lx, y - 60), (lx - 40, y), (lx + 40, y)], fill=(255, 255, 255, 120)); d.rectangle((lx - 14, y, lx + 14, y + 60), fill=(255, 255, 255, 120))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    return top, bot

def vis_bike(dst, t, v, i):
    mode = v.get("mode", "approach"); top, bot = bike_road(dst, t, two_lanes=(mode == "twolanes"))
    bx, by = W / 2 + 255, CY - 60; ph = int(t * 5)
    car = car_top((60, 140, 255), 140); rx, lx = W / 2 + 160, W / 2 - 165
    if mode == "approach":
        y = lerp(bot + 60, bot - 210, eout(prog(t, 0, 1.0))); paste(dst, car, rx, y)
        paste(dst, cyclist_top(ph), bx, by, scale=1.5)
        if v.get("limit"):
            p = prog(t, .3, .4); paste(dst, sign_generic("speed", v["limit"], 180), 140, top + 140, scale=eback(p), alpha=ease(p * 2))
    elif mode == "pass":
        k1 = ease(prog(t, .1, .8)); k2 = ease(prog(t, .6, 1.2))
        x = lerp(rx, W / 2 + 10, k1); y = lerp(bot - 210, by + 10, k2)
        paste(dst, cyclist_top(ph), bx, by, scale=1.5); paste(dst, car, x, y, rot=-14 * math.sin(math.pi * k1))
        pa = prog(t, 1.6, .4)
        if pa > 0:  # separación lateral
            d = ImageDraw.Draw(dst, "RGBA"); a = int(255 * ease(pa * 2)); xa, xb = W / 2 + 10 + 72, bx - 75; yy = by - 210
            d.line([(xa, yy), (xb, yy)], fill=YEL + (a,), width=10)
            for xx in (xa, xb): d.line([(xx, yy - 34), (xx, yy + 34)], fill=YEL + (a,), width=10)
            paste(dst, pill(v.get("gap", "1,5 m"), 52, YEL, NAVY), (xa + xb) / 2, yy - 80, scale=eback(pa), alpha=ease(pa * 2))
    else:  # twolanes: cambio completo de carril
        k1 = ease(prog(t, .3, 1.1)); x = lerp(rx, lx, k1); y = lerp(bot - 230, by + 40, ease(prog(t, .3, 1.8)))
        a = int(110 * ease(prog(t, .8, .4)))
        if a > 0:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle((W / 2 - 318, top, W / 2 - 8, bot), fill=(34, 197, 94, a)); dst.alpha_composite(ov)
        paste(dst, cyclist_top(ph), bx, by, scale=1.5); paste(dst, car, x, y, rot=-16 * math.sin(math.pi * k1))
    if v.get("tag"):
        paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, top + 60, scale=eback(prog(t, v.get("tag_at", .4), .4)), alpha=ease(prog(t, v.get("tag_at", .4), .3)))
    if v.get("ask"):
        pk = .5 + .5 * math.sin(t * 6)
        paste(dst, text("?", 260, YEL, BLACK), W / 2 - 120, CY + 60, scale=(.9 + .1 * pk) * eback(prog(t, .2, .4)), alpha=ease(prog(t, .2, .2)))

# --- cuentakilómetros: la aguja baja de "from" a "to" (km/h) ---
# vis: {"type": "speedo", "from": 90, "to": 70, "tag": "-20 km/h", "max": 140}
def vis_speedo(dst, t, v, i):
    mx = v.get("max", 140); fr, to = v.get("from", 90), v.get("to", 70); k = ease(prog(t, v.get("at", .7), 1.0)); val = lerp(fr, to, k)
    cx, cy, R = W / 2, CY + 120, 400
    p = eback(prog(t, 0, .5)); a = ease(prog(t, 0, .25))
    g = ss(2 * R + 80, R + 120); d = ImageDraw.Draw(g); S = 2; c0 = (R + 40) * S
    d.pieslice((40 * S - 30, 40 * S - 30, (2 * R + 40) * S + 30, (2 * R + 40) * S + 30), 180, 360, fill=(14, 18, 28))
    d.arc((40 * S, 40 * S, (2 * R + 40) * S, (2 * R + 40) * S), 180, 360, fill=(70, 80, 100), width=16)
    ang_to = 180 + 180 * to / mx
    d.arc((40 * S + 30, 40 * S + 30, (2 * R + 40) * S - 30, (2 * R + 40) * S - 30), 180, ang_to, fill=GREEN, width=36)
    d.arc((40 * S + 30, 40 * S + 30, (2 * R + 40) * S - 30, (2 * R + 40) * S - 30), ang_to, 180 + 180 * fr / mx, fill=RED, width=36)
    for n in range(0, mx + 1, 10):
        an = math.radians(180 + 180 * n / mx); r1 = (R - 60) * S if n % 20 == 0 else (R - 40) * S; r2 = (R - 10) * S
        d.line([(c0 + math.cos(an) * r1, c0 + math.sin(an) * r1), (c0 + math.cos(an) * r2, c0 + math.sin(an) * r2)], fill=WHITE, width=10 if n % 20 == 0 else 5)
        if n % 20 == 0:
            f = F(XB, 64); s = str(n); bb = f.getbbox(s); rr = (R - 115) * S
            d.text((c0 + math.cos(an) * rr - (bb[0] + bb[2]) / 2, c0 + math.sin(an) * rr - (bb[1] + bb[3]) / 2), s, font=f, fill=(200, 210, 230))
    gim = down(g)
    paste(dst, gim, cx, cy - R / 2 + 20, scale=.7 + .3 * p, alpha=a)
    d2 = ImageDraw.Draw(dst, "RGBA"); an = math.radians(180 + 180 * val / mx); ox, oy = cx, cy - R / 2 + 20 - (R + 120) / 2 + R + 40
    d2.line([(ox, oy), (ox + math.cos(an) * (R - 70), oy + math.sin(an) * (R - 70))], fill=YEL + (int(255 * a),), width=16)
    d2.ellipse((ox - 34, oy - 34, ox + 34, oy + 34), fill=YEL + (int(255 * a),))
    paste(dst, text(f"{int(round(val))}", 170, WHITE if k < .99 else GREEN, BLACK), cx, oy + 130, alpha=a)
    paste(dst, text("km/h", 52, (200, 210, 230), XB), cx, oy + 235, alpha=a)
    if v.get("tag"):
        pa = prog(t, v.get("at", .7) + .9, .35); paste(dst, pill(v["tag"], 56, RED, WHITE), cx + 250, VZ[0] + 60, scale=eback(pa), alpha=ease(pa * 2), rot=-6)

# --- sillita infantil + tallímetro (bloque vehículo y seguridad) ---
# vis: {"type": "sillita", "mode": "measure", "h": 130, "from": 100, "line": 135, "tag": "..."}  -> niño junto a un tallímetro con la marca 1,35 m
#      {"type": "sillita", "mode": "seat", "tag": "..."}  -> coche visto desde arriba: sillita detrás (OK) y asiento delantero (X)
@lru_cache(maxsize=8)
def child_seat(s=300, col=(30, 70, 160)):  # sillita de lado, mirando a la izquierda
    w, h = s, int(s * 1.25); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    dk = mix(col, (0, 0, 0), .45)
    d.rounded_rectangle((X * .52, Y * .02, X * .9, Y * .2), radius=int(X * .08), fill=dk)               # reposacabezas
    d.rounded_rectangle((X * .58, Y * .08, X * .86, Y * .8), radius=int(X * .12), fill=col)             # respaldo
    d.rounded_rectangle((X * .12, Y * .62, X * .86, Y * .86), radius=int(X * .1), fill=col)             # asiento
    d.rounded_rectangle((X * .08, Y * .84, X * .9, Y * .96), radius=int(X * .05), fill=(40, 42, 50))    # base
    d.rounded_rectangle((X * .5, Y * .1, X * .62, Y * .2), radius=12, fill=(150, 170, 210))             # ala lateral
    d.line([(X * .66, Y * .24), (X * .38, Y * .7)], fill=(255, 196, 0), width=int(X * .05))              # arnés
    d.ellipse((X * .33, Y * .62, X * .45, Y * .74), fill=(220, 225, 235))                               # hebilla
    return glow(down(im), 16, .35)

@lru_cache(maxsize=8)
def child_seat_top(s=120):  # sillita vista desde arriba
    w, h = s, int(s * 1.25); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .3), fill=(30, 70, 160))
    d.rounded_rectangle((X * .18, Y * .05, X * .82, Y * .3), radius=int(X * .15), fill=(20, 45, 110))
    d.ellipse((X * .3, Y * .1, X * .7, Y * .42), fill=(240, 200, 170))                                  # cabeza del niño
    d.line([(X * .3, Y * .45), (X * .5, Y * .78)], fill=YEL, width=16); d.line([(X * .7, Y * .45), (X * .5, Y * .78)], fill=YEL, width=16)
    return down(im)

def child_side(dst, cx, base, hpx, a=1.0):
    d = ImageDraw.Draw(dst, "RGBA"); al = int(255 * a); hr = hpx * .085
    col = (255, 255, 255, al)
    d.ellipse((cx - hr, base - hpx, cx + hr, base - hpx + 2 * hr), fill=col)                             # cabeza
    d.rounded_rectangle((cx - hpx * .12, base - hpx + 2 * hr + 8, cx + hpx * .12, base - hpx * .45), radius=int(hpx * .06), fill=col)  # cuerpo
    for sx in (-1, 1):
        d.rounded_rectangle((cx + sx * hpx * .02 - hpx * .045 + sx * hpx * .03, base - hpx * .46, cx + sx * hpx * .02 + hpx * .045 + sx * hpx * .03, base), radius=int(hpx * .04), fill=col)
        d.rounded_rectangle((cx + sx * hpx * .14 - hpx * .035, base - hpx + 2 * hr + 14, cx + sx * hpx * .14 + hpx * .035, base - hpx * .5), radius=int(hpx * .03), fill=col)

def vis_sillita(dst, t, v, i):
    mode = v.get("mode", "measure")
    if mode == "measure":
        base, pxcm = VZ[1] - 40, 5.0; rx = W / 2 + 200; d = ImageDraw.Draw(dst, "RGBA"); a = ease(prog(t, 0, .25))
        # tallímetro
        d.rounded_rectangle((rx - 50, base - 160 * pxcm - 20, rx + 50, base + 10), radius=18, fill=YEL + (int(255 * a),))
        for cm in range(0, 161, 10):
            y = base - cm * pxcm; L = 50 if cm % 20 == 0 else 28
            d.line([(rx - 50, y), (rx - 50 + L, y)], fill=NAVY + (int(255 * a),), width=6)
            if cm % 20 == 0 and cm: paste(dst, text(str(cm), 30, NAVY, XB, shadow=False), rx + 18, y, alpha=a)
        # marca de 1,35 m
        line = v.get("line", 135); ly = base - line * pxcm; lp = eout(prog(t, v.get("line_at", .3), .4))
        if lp > 0:
            for x in range(int(W / 2 - 400), int(W / 2 - 400 + (rx - 50 - (W / 2 - 400)) * lp), 40):
                d.line([(x, ly), (x + 24, ly)], fill=RED + (230,), width=8)
            paste(dst, pill(v.get("line_txt", "1,35 m"), 44, RED, WHITE), W / 2 - 330, ly - 50, scale=eback(lp), alpha=ease(lp * 2))
        # niño que "crece" hasta su estatura
        h = v.get("h", 130); fr = v.get("from", h * .6)
        cur = lerp(fr, h, eout(prog(t, .1, 1.0))); child_side(dst, W / 2 - 60, base, cur * pxcm, a)
        d.line([(W / 2 - 160, base + 4), (rx + 60, base + 4)], fill=(255, 255, 255, 140), width=6)
        hy = base - cur * pxcm
        d.line([(W / 2 - 10, hy), (rx - 50, hy)], fill=WHITE + (int(200 * a),), width=5)
        num = f"{cur / 100:.2f}".replace(".", ",") + " m"
        paste(dst, pill(num, 50, WHITE, NAVY), W / 2 - 60, max(VZ[0] + 60, hy - 70), alpha=a)
        if v.get("tag"):
            tp = prog(t, v.get("tag_at", 1.1), .35)
            paste(dst, pill(v["tag"], 44, GREEN if v.get("ok") else YEL, WHITE if v.get("ok") else NAVY), W / 2 - 130, ly - 150, scale=eback(tp), alpha=ease(tp * 2))
    else:  # seat: coche desde arriba con la sillita detrás
        p = eback(prog(t, 0, .5)); car = car_top((226, 69, 60), 330); cy = CY + 10
        paste(dst, car, W / 2, cy + (1 - p) * 200, alpha=ease(prog(t, 0, .25)))
        ch = car.height - 40
        rear = (W / 2 + 70, cy + ch * .1); front = (W / 2 + 70, cy - ch * .1)
        sp = eback(prog(t, .4, .45)); pulse = .5 + .5 * math.sin(t * 6)
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((rear[0] - 95, rear[1] - 105, rear[0] + 95, rear[1] + 105), fill=(34, 197, 94, int(120 + 80 * pulse)))
        dst.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
        paste(dst, child_seat_top(120), rear[0], rear[1], scale=sp, alpha=ease(prog(t, .4, .2)))
        paste(dst, icon_check(84), rear[0] + 150, rear[1], scale=eback(prog(t, .8, .3)))
        xp = prog(t, 1.1, .3)
        if xp > 0: paste(dst, icon_x(84), front[0] + 150, front[1] - 20, scale=eback(xp))
        paste(dst, pill("DELANTE", 34, (90, 96, 110), WHITE), W / 2 - 290, front[1] - 20, alpha=ease(prog(t, 1.1, .3)))
        paste(dst, pill("DETRÁS", 34, GREEN, WHITE), W / 2 - 290, rear[1] + 20, alpha=ease(prog(t, .8, .3)))
        if v.get("tag"):
            tp = prog(t, v.get("tag_at", 1.4), .35)
            paste(dst, pill(v["tag"], 50, RED, WHITE), W / 2, VZ[0] + 50, scale=eback(tp), alpha=ease(tp * 2), rot=-4)

# --- conducta PAS en un accidente (bloque primeros auxilios y accidentes) ---
# vis: {"type": "pas", "mode": "crash", "lines": [...], "cols": [...]}  -> choque de 2 coches visto desde arriba (humo + warnings)
#      {"type": "pas", "mode": "steps", "upto": -1..2, "chips": [...]}    -> tarjetas P · A · S (chaleco, 112, botiquín)
@lru_cache(maxsize=4)
def vest_icon(s=170):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2; Y = (255, 214, 0)
    d.polygon([(S * .2, S * .1), (S * .4, S * .1), (S * .5, S * .38), (S * .6, S * .1), (S * .8, S * .1), (S * .96, S * .32),
               (S * .86, S * .44), (S * .86, S * .96), (S * .14, S * .96), (S * .14, S * .44), (S * .04, S * .32)], fill=Y)
    for y0 in (.56, .74):
        d.rectangle((S * .14, S * y0, S * .86, S * (y0 + .08)), fill=(200, 205, 215))
    d.line([(S * .5, S * .4), (S * .5, S * .96)], fill=mix(Y, (0, 0, 0), .25), width=6)
    return down(im)

@lru_cache(maxsize=4)
def phone_icon(s=170):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.rounded_rectangle((S * .26, S * .04, S * .74, S * .96), radius=int(S * .1), fill=(22, 24, 30))
    d.rounded_rectangle((S * .3, S * .12, S * .7, S * .84), radius=int(S * .05), fill=BLUE)
    f = F(BLACK, int(S * .2)); bb = f.getbbox("112"); d.text((S / 2 - (bb[0] + bb[2]) / 2, S * .48 - (bb[1] + bb[3]) / 2), "112", font=f, fill=WHITE)
    return down(im)

@lru_cache(maxsize=4)
def aid_icon(s=170):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.rounded_rectangle((S * .08, S * .2, S * .92, S * .9), radius=int(S * .12), fill=GREEN)
    d.rounded_rectangle((S * .36, S * .08, S * .64, S * .24), radius=20, outline=GREEN, width=18)
    d.rectangle((S * .44, S * .34, S * .56, S * .78), fill=WHITE); d.rectangle((S * .28, S * .5, S * .72, S * .62), fill=WHITE)
    return down(im)

@lru_cache(maxsize=4)
def burst(s=260):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2; pts = []
    for k in range(20):
        r = S * (.48 if k % 2 == 0 else .26); an = k * math.pi / 10
        pts.append((S / 2 + math.cos(an) * r, S / 2 + math.sin(an) * r))
    d.polygon(pts, fill=(255, 196, 0)); d.polygon([((x - S / 2) * .55 + S / 2, (y - S / 2) * .55 + S / 2) for x, y in pts], fill=WHITE)
    return down(im)

def vis_pas(dst, t, v, i):
    mode = v.get("mode", "steps")
    if mode == "crash":
        if i == 0: t = t + 0.6  # primer fotograma: choque y gancho ya en pantalla
        top, bot = bike_road(dst, t, scroll=False); cx, cy = W / 2, CY + 140
        k = eout(prog(t, 0, .45)); shake = math.sin(t * 70) * 8 * (1 - prog(t, .3, .5))
        paste(dst, car_top((226, 69, 60), 140), lerp(cx - 300, cx - 70, k) + shake, cy + 30, rot=lerp(0, 28, k))
        paste(dst, car_top((60, 140, 255), 140), cx + 90 + shake, lerp(cy - 420, cy - 120, k), rot=lerp(90, 70, k))
        bp = prog(t, .35, .3)
        if bp > 0: paste(dst, burst(260), cx, cy - 40, scale=eback(bp) * (1 - .3 * prog(t, .9, .5)), alpha=1 - .6 * prog(t, 1.0, .6))
        for kk in range(5):
            z = ((t * .5 + kk / 5) % 1); paste(dst, puff(), cx + 10 + kk * 14, cy - 80 - z * 300, scale=.5 + z, alpha=(1 - z) * .55 * prog(t, .4, .3))
        if int(t * 2.4) % 2 == 0 and t > .5:
            paste(dst, hazard(110), cx - 140, cy - 20); paste(dst, hazard(110), cx + 150, cy - 180)
        if v.get("lines"):
            big_lines(dst, v["lines"], t, VZ[0] + 110, [tuple(c) for c in v.get("cols", [])] or None, size=130, stagger=.18)
    else:
        upto = v.get("upto", -1); cw, chh, gap = 260, 400, 20; x0 = W / 2 - 40 - (3 * cw + 2 * gap) / 2 + cw / 2; cy = VZ[0] + 260  # sin pisar la zona derecha de botones
        data = [("P", "PROTEGER", vest_icon), ("A", "AVISAR", phone_icon), ("S", "SOCORRER", aid_icon)]
        for k, (L, word, ic) in enumerate(data):
            if upto == -1: p = prog(t, .15 + k * .45, .4)
            else: p = 1.0
            cur = k == upto; dim = upto >= 0 and k > upto
            a = ease(p * 2) * (.45 if dim else 1); sc = eback(p) * (1.08 + .02 * math.sin(t * 6) if cur else 1)
            x = x0 + k * (cw + gap)
            c = card(cw, chh, fill=(255, 255, 255, 250) if not dim else (210, 216, 228, 240), r=36, border=YEL if cur else None, bw=10 if cur else 0)
            paste(dst, c, x, cy, alpha=a, scale=sc)
            paste(dst, text(L, 110, BLUE if not cur else (200, 140, 0), BLACK, shadow=False), x, cy - 120 * sc, alpha=a, scale=sc)
            paste(dst, ic(150), x, cy + 30 * sc, alpha=a, scale=sc)
            paste(dst, text(word, 40, DARK, BLACK, shadow=False), x, cy + 150 * sc, alpha=a, scale=sc)
            if upto >= 0 and k < upto: paste(dst, icon_check(64), x + cw / 2 - 30, cy - chh / 2 + 30)
        for j, ch in enumerate(v.get("chips", [])):
            cp = prog(t, .35 + j * .4, .35); ok = not ch.startswith("!")
            paste(dst, chip_ok(ch.lstrip("!"), ok), W / 2 - 40, cy + chh / 2 + 90 + j * 125, scale=1.3 * (.8 + .2 * eback(cp)), alpha=ease(cp * 2))
        if v.get("big"):
            bp = prog(t, .4, .4); paste(dst, text(v["big"], 120, YEL, BLACK), W / 2, cy + chh / 2 + 150, scale=eback(bp), alpha=ease(bp * 2))

# --- glorieta vista desde arriba con coches numerados (formato ¿QUIÉN PASA PRIMERO?, parte 2) ---
# vis: {"type": "glorieta", "tag": "...", "still": true, "inside": [1, 3], "move": [[n, inicio, dur]], "done": [n],
#       "countdown": [t1, t2, t3], "rank": ["1", "3", "2"], "rank_at": [...], "focus": true (anillo en verde),
#       "right": "POR LA DERECHA" (resalta al que entra), "xright": t (tacha la pill)}
GL_C = (W / 2 - 30, CY - 30); GL_R0, GL_R1, GL_RL = 150, 300, 225
GL_TH0 = {1: 235, 3: 165}
def gl_pos(n, k):
    cx, cy = GL_C
    if n in GL_TH0:
        th = GL_TH0[n] + 170 * k; r = math.radians(th)
        return cx + GL_RL * math.cos(r), cy - GL_RL * math.sin(r), th
    # coche 2: espera en el brazo sur (carril derecho) y entra girando en sentido antihorario
    th_in = 285; jx, jy = cx + GL_RL * math.cos(math.radians(th_in)), cy - GL_RL * math.sin(math.radians(th_in))
    if k < .35:
        q = k / .35; return lerp(cx + 60, jx, q), lerp(cy + 400, jy, q), 0
    q = (k - .35) / .65; th = th_in + 140 * q; r = math.radians(th)
    return cx + GL_RL * math.cos(r), cy - GL_RL * math.sin(r), lerp(0, th - 360, clamp(q / .25))

def vis_glorieta(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: coches y pregunta ya en pantalla
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; cx, cy = GL_C; AW = 120
    d.rectangle((40, top, W - 40, bot), fill=(64, 92, 60, 255))
    for k in range(40):
        gx, gy = 60 + (k * 263) % (W - 120), top + (k * 157) % (bot - top)
        d.ellipse((gx - 30, gy - 18, gx + 30, gy + 18), fill=(74, 104, 68, 255))
    road = (36, 40, 50, 255)
    d.rectangle((cx - AW, top, cx + AW, bot), fill=road); d.rectangle((40, cy - AW, W - 40, cy + AW), fill=road)
    d.ellipse((cx - GL_R1, cy - GL_R1, cx + GL_R1, cy + GL_R1), fill=road)
    for x0, x1 in ((40, cx - GL_R1), (cx + GL_R1, W - 40)):  # eje discontinuo de los brazos
        x = x0 + 10
        while x < x1 - 40: d.line([(x, cy), (x + 44, cy)], fill=(255, 255, 255, 200), width=7); x += 85
    for y0, y1 in ((top, cy - GL_R1), (cy + GL_R1, bot)):
        y = y0 + 10
        while y < y1 - 40: d.line([(cx, y), (cx, y + 44)], fill=(255, 255, 255, 200), width=7); y += 85
    for k in range(48):  # línea discontinua exterior del anillo
        a0 = k * 7.5
        if any(abs(((a0 - c + 180) % 360) - 180) < 22 for c in (0, 90, 180, 270)): continue
        r = GL_R1 - 10; d.arc((cx - r, cy - r, cx + r, cy + r), -a0, -a0 + 4, fill=(255, 255, 255, 200), width=6)
    if v.get("focus"):  # anillo de "dentro" en verde
        pa = ease(prog(t, .2, .5)); a = int(130 * pa * (.7 + .3 * math.sin(t * 6)))
        d.ellipse((cx - GL_R1 + 14, cy - GL_R1 + 14, cx + GL_R1 - 14, cy + GL_R1 - 14), fill=(34, 197, 94, a))
        d.ellipse((cx - GL_R0 - 8, cy - GL_R0 - 8, cx + GL_R0 + 8, cy + GL_R0 + 8), fill=road)
    d.ellipse((cx - GL_R0 - 10, cy - GL_R0 - 10, cx + GL_R0 + 10, cy + GL_R0 + 10), fill=(235, 235, 235, 255))  # bordillo
    d.ellipse((cx - GL_R0, cy - GL_R0, cx + GL_R0, cy + GL_R0), fill=(78, 140, 70, 255))
    for k in range(6):  # arbustos de la isleta
        an = k * math.pi / 3 + .4; bx, by = cx + math.cos(an) * 80, cy + math.sin(an) * 80
        d.ellipse((bx - 30, by - 30, bx + 30, by + 30), fill=(54, 112, 52, 255))
    d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=(255, 196, 0, 255))
    # flechas de sentido de giro (antihorario) en el anillo
    for c in (45, 135, 225, 315):
        r = math.radians(c); ax, ay = cx + GL_RL * math.cos(r), cy - GL_RL * math.sin(r)
        hd = r + math.pi / 2; dx, dy = math.cos(hd), -math.sin(hd); px, py = -dy, dx
        al = int(110 + 60 * math.sin(t * 4 + c))
        d.polygon([(ax + dx * 34, ay + dy * 34), (ax - dx * 10 + px * 26, ay - dy * 10 + py * 26), (ax - dx * 10 - px * 26, ay - dy * 10 - py * 26)], fill=(255, 255, 255, al))
    done = set(v.get("done", [])); moves = {m[0]: (m[1], m[2]) for m in v.get("move", [])}
    if v.get("right") and 2 not in done and (2 not in moves or t < moves[2][0]):  # halo en el coche que quiere entrar
        x, y, _ = gl_pos(2, 0); pa = .6 + .4 * math.sin(t * 7)
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((x - 110, y - 150, x + 110, y + 150), fill=(255, 196, 0, int(150 * pa)))
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    for n in (3, 1, 2):
        if n in done: continue
        k = 0.0
        if n in moves: s, du = moves[n]; k = ease(prog(t, s, du))
        x, y, rot = gl_pos(n, k)
        if k == 0 and not v.get("still") and n in GL_TH0:  # al empezar, ya van girando
            k2 = -.12 * (1 - eout(prog(t, 0, .6))); x, y, rot = gl_pos(n, k2)
        paste(lay, car_top(CRUCE_COLS[n], 110), x, y, rot=rot)
        paste(lay, num_badge(n, 74), x, y, scale=eback(prog(t, .1 + n * .1, .35)) if not v.get("still") else 1)  # número sobre el techo
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    if v.get("right"):
        p = prog(t, .3, .35); pl = pill(v["right"], 40, YEL, NAVY); px, py = 60 + pl.width / 2, bot - 120
        paste(dst, pl, px, py, scale=eback(p), alpha=ease(p * 2))
        xr = v.get("xright")
        if xr is not None and t > xr: paste(dst, icon_x(90), px + pl.width / 2 + 10, py - 50, scale=eback(prog(t, xr, .3)))
    cd = v.get("countdown")
    if cd:
        n = sum(1 for s in cd if t >= s); ix, iy = 110, top + 170
        paste(dst, semaphore(n).resize((115, 300), Image.LANCZOS), ix, iy, scale=eback(prog(t, 0, .4)))
        if n:
            pk = prog(t, cd[n - 1], .25)
            paste(dst, text(str(4 - n), 190, [RED, (255, 176, 0), GREEN][n - 1], BLACK), 110, iy + 300, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))
    rk = v.get("rank")
    if rk:
        ra = v.get("rank_at", [0] * len(rk))
        for j, (lab, at) in enumerate(zip(rk, ra)):
            p = prog(t, at, .35)
            if p > 0: paste(dst, rank_chip(j + 1, int(lab)), 160, top + 70 + j * 92, scale=eback(p), alpha=ease(p * 2))
    if v.get("tag"):
        tp = prog(t, .35, .4) if i else 1.0
        paste(dst, pill(v["tag"], 58 if i == 0 else 42, YEL, NAVY), W / 2 - 30, bot - 50 if v.get("tag_low") else top + 60, scale=eback(tp), alpha=ease(tp * 2))

# --- alcoholímetro (formato TRAMPAS DEL EXAMEN, bloque alcohol, drogas y móvil) ---
# vis: {"type": "alcohol", "mode": "zero" | "trap" | "minor" | "limit" | "units" | "years" | "pending", ...}
@lru_cache(maxsize=64)
def breathalyzer(val, col=GREEN, w=330, h=560):
    im = ss(w, h + 150); d = ImageDraw.Draw(im); X, Y = w * 2, (h + 150) * 2; o = 300
    d.rounded_rectangle((X * .4, 0, X * .6, o + 40), radius=26, fill=(235, 240, 248))           # boquilla
    d.rounded_rectangle((X * .43, 20, X * .57, 60), radius=12, fill=(190, 200, 215))
    d.rounded_rectangle((0, o, X - 1, Y - 1), radius=int(X * .18), fill=(28, 36, 54))            # cuerpo
    d.rounded_rectangle((14, o + 14, X - 15, Y - 15), radius=int(X * .16), outline=(70, 84, 110), width=10)
    d.rounded_rectangle((X * .1, o + 90, X * .9, o + 430), radius=36, fill=(12, 18, 14))         # pantalla
    d.rounded_rectangle((X * .13, o + 112, X * .87, o + 408), radius=26, fill=mix(col, (10, 16, 12), .78))
    f = F(BLACK, 170); bb = f.getbbox(val); d.text((X / 2 - (bb[0] + bb[2]) / 2, o + 230 - (bb[1] + bb[3]) / 2), val, font=f, fill=col)
    f2 = F(XB, 52); u = "mg/l aire"; bb = f2.getbbox(u); d.text((X / 2 - (bb[0] + bb[2]) / 2, o + 350 - (bb[1] + bb[3]) / 2), u, font=f2, fill=col)
    for k, c in enumerate(((34, 197, 94), (255, 196, 0), (239, 68, 68))):                          # leds
        cx = X * (.3 + .2 * k); d.ellipse((cx - 30, o + 500, cx + 30, o + 560), fill=c if c == col else mix(c, (28, 36, 54), .7))
    d.rounded_rectangle((X * .25, Y - 230, X * .75, Y - 120), radius=50, fill=(18, 86, 190))      # botón
    return down(im)

@lru_cache(maxsize=4)
def drop_icon(s=160):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.polygon([(S / 2, S * .04), (S * .2, S * .55), (S * .8, S * .55)], fill=RED); d.ellipse((S * .18, S * .34, S * .82, S * .96), fill=RED)
    d.ellipse((S * .3, S * .55, S * .44, S * .72), fill=(255, 170, 170)); return down(im)

@lru_cache(maxsize=4)
def breath_icon(s=160):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2; c = BLUE_L
    for k, (x, y, r) in enumerate(((.3, .55, .2), (.52, .42, .24), (.72, .58, .18), (.5, .66, .2))):
        d.ellipse((S * (x - r), S * (y - r), S * (x + r), S * (y + r)), fill=c)
    for k in range(3): d.arc((S * .08, S * (.1 + k * .1), S * .5, S * (.4 + k * .1)), 200, 320, fill=WHITE, width=12)
    return down(im)

@lru_cache(maxsize=8)
def calendar_page(lab, s=250):
    im = ss(s, int(s * 1.1)); d = ImageDraw.Draw(im); S = s * 2; Hh = int(S * 1.1)
    d.rounded_rectangle((0, 20, S - 1, Hh - 1), radius=40, fill=WHITE); d.rounded_rectangle((0, 20, S - 1, S * .34), radius=40, fill=RED)
    d.rectangle((0, S * .22, S - 1, S * .34), fill=RED)
    for x in (.28, .72): d.rounded_rectangle((S * x - 14, 0, S * x + 14, 70), radius=12, fill=(60, 70, 90))
    f = F(BLACK, int(S * .13)); bb = f.getbbox("AÑO"); d.text((S / 2 - (bb[0] + bb[2]) / 2, S * .2 - (bb[1] + bb[3]) / 2), "AÑO", font=f, fill=WHITE)
    f = F(BLACK, int(S * .5)); bb = f.getbbox(lab); d.text((S / 2 - (bb[0] + bb[2]) / 2, S * .7 - (bb[1] + bb[3]) / 2), lab, font=f, fill=DARK)
    return down(im)

def vis_alcohol(dst, t, v, i):
    mode = v.get("mode", "zero")
    if i == 0: t = t + 0.6  # primer fotograma: gancho ya en pantalla
    bx, by = W / 2 - 40, CY + 130
    if mode in ("zero", "trap", "minor", "limit"):
        if mode == "limit":
            val = v.get("value", .15) * eout(prog(t, .2, 1.4)); s = f"{val:.2f}".replace(".", ",")
            col = GREEN if val < v.get("value", .15) - .001 else (255, 196, 0)
        else: s, col = "0,00", (GREEN if mode == "minor" else (255, 196, 0))
        p = eback(prog(t, 0, .5)); wob = math.sin(t * 3) * 3
        cx = bx - (170 if mode in ("limit", "minor") else 0)
        paste(dst, breathalyzer(s, col, 290, 490), cx, by + (1 - p) * 160 + (math.sin(t * 2.5) * 10 if mode != "limit" else 0), alpha=ease(prog(t, 0, .25)), rot=wob if mode != "limit" else 0)
        if mode in ("zero", "trap"):
            big_lines(dst, v.get("lines", ["¿NOVEL =", "TASA CERO?"]), t, VZ[0] + 70, [tuple(c) for c in v.get("cols", [])] or [WHITE, YEL], size=120, stagger=.18)
            if mode == "zero":
                qp = prog(t, .5, .4); paste(dst, text("?", 220, YEL, BLACK), bx + 250, by - 120 + math.sin(t * 5) * 14, scale=eback(qp), alpha=ease(qp * 2), rot=-10)
            else:
                sp = prog(t, .35, .2)
                if sp > 0: paste(dst, stamp_col("TRAMPA", RED), bx + 20, by + 40, scale=lerp(2.2, 1, eout(sp)), alpha=ease(sp * 1.6), rot=-12)
        if mode == "minor":
            paste(dst, pill(v.get("tag", "MENORES DE EDAD"), 40, GREEN, WHITE), W / 2 + 170, CY - 80, scale=eback(prog(t, .3, .35)), alpha=ease(prog(t, .3, .3)))
            paste(dst, text("0,0", 190, WHITE, BLACK), W / 2 + 170, CY + 90, scale=eback(prog(t, .5, .35)), alpha=ease(prog(t, .5, .3)))
        if mode == "limit":  # barra con el límite del novel
            gx, g0, g1 = W / 2 + 230, VZ[1] - 40, VZ[0] + 60; d = ImageDraw.Draw(dst, "RGBA"); vmax = .30
            yv = lambda q: g0 - (g0 - g1) * q / vmax
            a = ease(prog(t, 0, .3)); lim = v.get("value", .15)
            d.rounded_rectangle((gx - 55, g1, gx + 55, g0), radius=30, fill=(255, 255, 255, int(40 * a)))
            d.rounded_rectangle((gx - 55, g1, gx + 55, yv(lim)), radius=30, fill=RED + (int(140 * a),))
            d.rectangle((gx - 55, yv(lim), gx + 55, g0 - 30), fill=GREEN + (int(140 * a),))
            d.rounded_rectangle((gx - 55, g0 - 60, gx + 55, g0), radius=30, fill=GREEN + (int(140 * a),))
            d.rounded_rectangle((gx - 34, min(yv(val), g0 - 60), gx + 34, g0 - 14), radius=22, fill=WHITE + (int(230 * a),))
            for q, lab in ((0, "0"), (.15, "0,15"), (.25, "0,25")):
                d.line([(gx - 75, yv(q)), (gx - 55, yv(q))], fill=WHITE + (int(200 * a),), width=6)
                paste(dst, text(lab, 34, WHITE, XB, shadow=False), gx - 130, yv(q), alpha=a)
            lp = prog(t, 1.4, .35)
            paste(dst, pill(v.get("tag", "LÍMITE NOVEL"), 40, YEL, NAVY), W / 2 - 90, VZ[0] + 70, scale=eback(lp), alpha=ease(lp * 2))
    elif mode == "units":
        for k, (ic, big, unit, lab) in enumerate(((breath_icon, "0,15", "mg/l", "EN AIRE"), (drop_icon, "0,3", "g/l", "EN SANGRE"))):
            p = eback(prog(t, k * .45, .45)); a = ease(prog(t, k * .45, .3)); x = W / 2 - 40 + (k * 2 - 1) * 225; y = CY + 10 + (1 - p) * 150
            paste(dst, card(400, 600, fill=(255, 255, 255, 250), r=40, border=YEL if k else None, bw=8 if k else 0), x, y, alpha=a)
            paste(dst, pill(lab, 34, BLUE if not k else RED, WHITE), x, y - 240, alpha=a)
            paste(dst, ic(170), x, y - 80, alpha=a, scale=1 + .04 * math.sin(t * 5 + k))
            paste(dst, text(big, 120, DARK, BLACK, shadow=False), x, y + 100, alpha=a)
            paste(dst, text(unit, 50, (90, 96, 110), XB, shadow=False), x, y + 200, alpha=a)
        ep = prog(t, .9, .3); paste(dst, text("=", 120, YEL, BLACK), W / 2 - 40, CY + 10, scale=eback(ep), alpha=ease(ep * 2))
    elif mode == "years":
        for k in range(2):
            p = prog(t, .1 + k * .5, .4); x = W / 2 - 40 + (k * 2 - 1) * 170
            paste(dst, calendar_page(str(k + 1)), x, CY - 40 + (1 - eback(p)) * 120, alpha=ease(p * 2), rot=(1 - eout(p)) * 15 * (k * 2 - 1))
            if t > .5 + k * .5: paste(dst, icon_check(80), x + 95, CY - 170, scale=eback(prog(t, .5 + k * .5, .3)))
        paste(dst, pill(v.get("tag", "PERMISO NOVEL: 0,15"), 46, YEL, NAVY), W / 2 - 40, CY + 260, scale=eback(prog(t, 1.2, .35)), alpha=ease(prog(t, 1.2, .3)))
    else:  # pending: documento con sello rojo "NO EN VIGOR"
        p = eback(prog(t, 0, .5)); c = doc_card(); paste(dst, c, W / 2 - 40, CY + (1 - p) * 220, alpha=ease(prog(t, 0, .25)), rot=(1 - p) * 6)
        paste(dst, text(v.get("title1", "Rebaja a 0,2 g/l"), 54, DARK, BLACK, shadow=False), W / 2 - 40, CY - 130, alpha=ease(prog(t, .2, .3)))
        paste(dst, text(v.get("title2", "en el Congreso"), 46, (90, 96, 110), XB, shadow=False), W / 2 - 40, CY - 65, alpha=ease(prog(t, .2, .3)))
        sp = prog(t, .7, .22)
        if sp > 0: paste(dst, stamp_col(v.get("stamp", "NO EN VIGOR"), RED), W / 2 - 20, CY + 110, scale=lerp(2.2, 1, eout(sp)) * .8, alpha=ease(sp * 1.6), rot=-8)
        if v.get("badge"): paste(dst, pill(v["badge"], 40, YEL, NAVY), W / 2 - 40, CY + 330, scale=eback(prog(t, 1.1, .4)), alpha=ease(prog(t, 1.1, .3)))

# --- POV en primera persona: calle urbana vista desde el asiento del conductor (salpicadero, volante) con ciclista delante ---
# vis: {"type": "pov", "mode": "approach" | "center" | "horn" | "options" | "gap",
#       "z": 0.45 (profundidad del ciclista 0 horizonte..1 cerca), "z0": 0.25 (approach: desde), "tag": "...", "tag_at": .4,
#       "opts": ["2 m", "5 m", "10 m"], "ok": 1 (índice correcto, se marca si "reveal": true), "countdown": [t1, t2, t3],
#       "gap": "5 m", "horn_x": true, "speed": 30}
@lru_cache(maxsize=8)
def cyclist_rear(ph=0, s=240):
    w, h = s, int(s * 1.9); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((X * .44, Y * .62, X * .56, Y * .99), radius=int(X * .06), fill=(20, 20, 24))           # rueda trasera
    d.rounded_rectangle((X * .42, Y * .6, X * .58, Y * .66), radius=8, fill=(60, 64, 76))                       # guardabarros
    d.rounded_rectangle((X * .45, Y * .66, X * .55, Y * .72), radius=6, fill=(255, 40, 40))                     # piloto trasero
    lo = (1 if ph % 2 else -1) * Y * .04
    for sx, off in ((-1, lo), (1, -lo)):                                                                      # piernas
        d.rounded_rectangle((X * .5 + sx * X * .16 - X * .07, Y * .45 + off, X * .5 + sx * X * .16 + X * .07, Y * .78 + off), radius=20, fill=(30, 40, 70))
        d.rounded_rectangle((X * .5 + sx * X * .16 - X * .08, Y * .76 + off, X * .5 + sx * X * .16 + X * .08, Y * .81 + off), radius=10, fill=(15, 15, 18))
    d.rounded_rectangle((X * .34, Y * .4, X * .66, Y * .5), radius=30, fill=(30, 40, 70))                       # culotte
    d.rounded_rectangle((X * .24, Y * .16, X * .76, Y * .46), radius=int(X * .16), fill=ORANGE)                 # espalda
    d.rectangle((X * .47, Y * .18, X * .53, Y * .44), fill=(255, 196, 0))
    d.line([(X * .27, Y * .22), (X * .08, Y * .3)], fill=(240, 200, 170), width=int(X * .08))                   # brazos
    d.line([(X * .73, Y * .22), (X * .92, Y * .3)], fill=(240, 200, 170), width=int(X * .08))
    d.line([(X * .02, Y * .3), (X * .98, Y * .3)], fill=(40, 40, 46), width=int(X * .05))                       # manillar
    d.ellipse((X * .33, Y * .02, X * .67, Y * .2), fill=WHITE)                                                  # casco
    d.rectangle((X * .47, Y * .02, X * .53, Y * .2), fill=RED)
    return down(im)

@lru_cache(maxsize=4)
def horn_icon(s=170):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.polygon([(S * .12, S * .38), (S * .3, S * .38), (S * .58, S * .16), (S * .58, S * .84), (S * .3, S * .62), (S * .12, S * .62)], fill=YEL)
    for k, r in enumerate((.18, .3)):
        d.arc((S * (.58 - r), S * (.5 - r * 1.3), S * (.58 + r), S * (.5 + r * 1.3)), -50, 50, fill=YEL, width=int(S * .06))
    return glow(down(im), 16, .6)

def pov_scene(dst, t, v):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; hz = top + 300; vx = W / 2 + 40
    for y in range(top, hz):  # cielo
        k = (y - top) / (hz - top); d.line([(40, y), (W - 40, y)], fill=mix((70, 120, 200), (190, 215, 240), k) + (255,))
    # edificios al fondo
    for k, (bx, bw, bh, col) in enumerate(((60, 170, 210, (120, 130, 160)), (220, 140, 260, (150, 120, 110)), (350, 120, 170, (110, 140, 150)),
                                           (650, 130, 190, (160, 140, 120)), (770, 150, 250, (110, 120, 150)), (910, 140, 200, (140, 110, 120)))):
        d.rectangle((bx, hz - bh, bx + bw, hz), fill=col + (255,))
        for wy in range(int(hz - bh + 20), int(hz - 20), 40):
            for wx in range(bx + 16, bx + bw - 26, 36): d.rectangle((wx, wy, wx + 18, wy + 22), fill=(230, 235, 245, 200) if (wx + wy) % 3 else (255, 220, 140, 220))
    # aceras y calzada
    d.polygon([(40, hz), (vx - 70, hz), (vx - 900, bot), (40, bot)], fill=(150, 154, 164, 255))
    d.polygon([(vx + 70, hz), (W - 40, hz), (W - 40, bot), (vx + 900, bot)], fill=(150, 154, 164, 255))
    d.polygon([(vx - 70, hz), (vx + 70, hz), (vx + 900, bot), (vx - 900, bot)], fill=(46, 50, 60, 255))
    for sx in (-1, 1): d.line([(vx + sx * 70, hz), (vx + sx * 900, bot)], fill=(230, 230, 230, 255), width=10)  # bordillos
    # farolas / árboles a los lados que pasan
    for k in range(4):
        z = ((k / 4) + t * 0.45) % 1.0; zz = z ** 2; y = hz + (bot - hz) * zz
        for sx in (-1, 1):
            x = vx + sx * (100 + 1000 * zz); hgt = 40 + 520 * zz
            d.line([(x, y), (x, y - hgt)], fill=(40, 44, 52, 255), width=max(2, int(16 * zz)))
            d.ellipse((x - 10 - 30 * zz, y - hgt - 8 - 20 * zz, x + 10 + 30 * zz, y - hgt + 8 + 20 * zz), fill=(255, 230, 150, 255))
    # línea discontinua del eje (a la izquierda: sentido contrario)
    for k in range(9):
        z = ((k / 9) + t * 0.55) % 1.0; z2 = min(1, z + .045)
        x1, y1 = vx - 40 - 460 * z ** 2, hz + (bot - hz) * z ** 2; x2, y2 = vx - 40 - 460 * z2 ** 2, hz + (bot - hz) * z2 ** 2
        d.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 230), width=max(3, int(16 * z)))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    return top, bot, hz, vx

def pov_dash(dst, t, v, top, bot):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); dy = bot - 150
    d.ellipse((-200, dy, W + 200, dy + 420), fill=(18, 20, 26, 255))                               # salpicadero
    d.ellipse((-200, dy - 6, W + 200, dy + 410), outline=(60, 64, 78, 255), width=6)
    d.ellipse((90, dy + 20, 640, dy + 570), outline=(28, 30, 36, 255), width=54)                    # volante
    d.ellipse((90, dy + 20, 640, dy + 570), outline=(50, 54, 64, 255), width=8)
    d.rounded_rectangle((700, dy + 40, 900, dy + 120), radius=20, fill=(8, 10, 14, 255), outline=(60, 64, 78, 255), width=4)
    sp = str(v.get("speed", 30)); d.text((740, dy + 52), sp, font=F(BLACK, 54), fill=(120, 220, 255)); d.text((815, dy + 70), "km/h", font=F(XB, 26), fill=(120, 160, 200))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    return dy

def vis_pov(dst, t, v, i):
    if i == 0: t = t + 0.6
    mode = v.get("mode", "approach"); top, bot, hz, vx = pov_scene(dst, t, v)
    z = v.get("z", .45)
    if mode == "approach": z = lerp(v.get("z0", .22), z, eout(prog(t, 0, 1.6)))
    zz = z ** 1.5; cyx = vx + 15 + 185 * zz; cyy = hz + (bot - hz) * zz; sc = .3 + 1.4 * zz
    clip = Image.new("L", (W, H), 0); ImageDraw.Draw(clip).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255); clip = np.array(clip)
    def put(ov):
        ov.putalpha(Image.fromarray(np.minimum(np.array(ov.split()[3]), clip))); dst.alpha_composite(ov)
    if mode == "center":  # carril propio resaltado
        pa = ease(prog(t, .2, .5)); a = int(110 * pa * (.75 + .25 * math.sin(t * 6)))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.polygon([(vx - 40, hz), (vx + 70, hz), (vx + 900, bot), (vx - 500, bot)], fill=(34, 197, 94, a)); put(ov)
    if mode == "gap":  # escalera de distancia en el suelo, del capó a la rueda del ciclista
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); pg = ease(prog(t, .05, .8)); n = 5; u0 = (bot - 150 - hz) / (bot - hz)
        labs = []
        for k in range(n + 1):
            f = k / n
            if f > pg + 1e-3: break
            u = lerp(u0, zz, f); y = hz + (bot - hz) * u; xl, xr = vx - 40 - 460 * u, vx + 70 + 830 * u
            od.line([(xl, y), (xr, y)], fill=YEL + (235,), width=max(4, int(16 * u)))
            if 0 < k: labs.append((k, xl + 50 + 30 * u, y + 30 * u, u))
        put(ov)
        for k, x, y, u in labs: paste(dst, text(f"{n - k + 1}" if False else f"{k}", int(34 + 50 * u), YEL, BLACK), max(110, x), y - 34 * u - 6)
    paste(dst, cyclist_rear(int(t * 5) % 2), cyx, cyy - 230 * sc, scale=sc)
    dy = pov_dash(dst, t, v, top, bot)
    if mode == "gap":
        pa = prog(t, .7, .4); paste(dst, pill(v.get("gap", "5 m"), 60, YEL, NAVY), 290, hz + 70, scale=eback(pa), alpha=ease(pa * 2))
    if mode == "center":
        p = prog(t, .6, .35); paste(dst, icon_check(110), cyx + 150 * sc + 40, cyy - 300 * sc, scale=eback(p))
        paste(dst, pill(v.get("lab", "CENTRO DEL CARRIL"), 40, GREEN, WHITE), W / 2 - 40, dy - 40, scale=eback(prog(t, .9, .35)), alpha=ease(prog(t, .9, .3)))
    if mode != "center" and v.get("lab"):
        la = v.get("lab_at", 0); paste(dst, pill(v["lab"], 40, YEL, NAVY), W / 2 - 40, dy - 40, scale=eback(prog(t, la, .35)), alpha=ease(prog(t, la, .3)))
    if mode == "horn":
        pk = .5 + .5 * math.sin(t * 14); p = prog(t, .2, .35)
        paste(dst, horn_icon(190), W / 2 - 200, hz + 150, scale=eback(p) * (.95 + .08 * pk), alpha=ease(p * 2))
        paste(dst, text("¡PII!", 110, YEL, BLACK), W / 2 - 60, hz - 110, scale=eback(prog(t, .35, .3)) * (.95 + .05 * pk), alpha=ease(prog(t, .35, .2)), rot=6)
        if v.get("horn_x") and t > .9: paste(dst, icon_x(130), W / 2 - 130, hz + 230, scale=eback(prog(t, .9, .3)))
    opts = v.get("opts")
    if opts:
        ok = v.get("ok", 1); rv = v.get("reveal", False); ra = eout(prog(t, .05, .4)) if rv else 0
        for k, o in enumerate(opts):
            p = prog(t, v.get("opts_at", [.15, .37, .59])[k], .3) if not v.get("opts_on") else 1
            good = rv and k == ok
            bg = mix(WHITE, GREEN, ra) if good else (mix(WHITE, (150, 156, 170), ra) if rv else WHITE)
            im = pill(f"{'ABC'[k]}  {o}", 52, bg, WHITE if good and ra > .5 else NAVY, padx=30)
            x = W / 2 - 60 + (k - 1) * 270; y = top + 70
            paste(dst, im, x, y, scale=eback(p) * (1 + .12 * ra if good else 1), alpha=ease(p * 2) * (1 - .45 * ra if rv and not good else 1))
            if good and t > .4: paste(dst, icon_check(70), x + 115, y - 40, scale=eback(prog(t, .4, .3)))
    cd = v.get("countdown")
    if cd:
        n = sum(1 for s_ in cd if t >= s_); ix, iy = 150, hz + 30
        paste(dst, semaphore(n).resize((105, 275), Image.LANCZOS), ix, iy, scale=eback(prog(t, 0, .4)))
        if n:
            pk = prog(t, cd[n - 1], .25)
            paste(dst, text(str(4 - n), 190, [RED, (255, 176, 0), GREEN][n - 1], BLACK), ix + 170, iy + 10, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))
    if v.get("tag"):
        at = v.get("tag_at", .3); ty = top + 60 if not opts else top + 170
        paste(dst, pill(v["tag"], 44, YEL, NAVY), W / 2 - 40, ty, scale=eback(prog(t, at, .4)), alpha=ease(prog(t, at, .3)))

VIS = {k[4:]: v for k, v in globals().items() if k.startswith("vis_")}

def frame(n):
    t = n / FPS
    i = max(k for k in range(len(SC)) if B[k] <= t + 1e-6); i = min(i, len(SC) - 1)
    lt = t - B[i]
    im = background(t); header(im, t)
    v = SC[i].get("vis", {})
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    VIS[v.get("type", "hook")](layer, lt, v, i)
    # entrada de escena: pequeño zoom + flash
    if i > 0 and lt < 0.12 and not v.get("no_flash"):
        k = lt / 0.12; layer = layer.resize((int(W * (1.04 - .04 * k)), int(H * (1.04 - .04 * k))), Image.BICUBIC)
        layer = layer.crop(((layer.width - W) // 2, (layer.height - H) // 2, (layer.width - W) // 2 + W, (layer.height - H) // 2 + H))
    im.alpha_composite(layer)
    captions(im, t, i)
    # barra de progreso
    d = ImageDraw.Draw(im, "RGBA"); d.rectangle((0, 0, W, 10), fill=(255, 255, 255, 40)); d.rectangle((0, 0, int(W * t / DUR), 10), fill=YEL)
    if i > 0 and lt < 0.08 and not v.get("no_flash"):
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(70 * (1 - lt / 0.08)))))
    return im.convert("RGB")

def raw(n): return frame(n).tobytes()

# ---------- audio: voz + efectos ----------
def tone(f, d, sr=24000, vol=.25, decay=6):
    t = np.arange(int(sr * d)) / sr; return (np.sin(2 * np.pi * f * t) * np.exp(-t * decay) * vol).astype(np.float32)
def sfx_wave(kind, sr=24000):
    if kind == "beep": return tone(880, .16, sr, .22, 8)
    if kind == "ding": return np.concatenate([tone(1046, .12, sr, .25, 5), tone(1568, .45, sr, .25, 5)])
    if kind == "buzz":
        t = np.arange(int(sr * .35)) / sr; return (np.sign(np.sin(2 * np.pi * 140 * t)) * .08 * np.exp(-t * 4)).astype(np.float32)
    if kind == "whoosh":
        n = int(sr * .3); x = np.random.default_rng(1).standard_normal(n).astype(np.float32)
        x = np.convolve(x, np.ones(30) / 30, mode="same"); env = np.sin(np.linspace(0, np.pi, n)) ** 2; return (x * env * .12).astype(np.float32)
    return np.zeros(1, np.float32)

def build_audio(out):
    import soundfile as sf
    v, sr = sf.read(os.path.join(BASE, CFG.get("voice", "voz.wav")), dtype="float32")
    if v.ndim > 1: v = v.mean(axis=1)
    total = np.zeros(int(DUR * sr) + sr, np.float32); total[:len(v)] += v
    events = list(CFG.get("sfx", []))
    for k in range(1, len(SC)): events.append({"t": B[k], "type": "whoosh"})
    for e in events:
        w = sfx_wave(e["type"], sr); s = int(e["t"] * sr); total[s:s + len(w)] += w[:max(0, len(total) - s)]
    total = total[:int(DUR * sr)]; total /= max(1.0, np.abs(total).max() / 0.95)
    sf.write(out, total, sr)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "stills":
        for ts in sys.argv[3:]:
            frame(int(float(ts) * FPS)).save(os.path.join(BASE, f"still_{ts}.png")); print("ok", ts)
    else:
        out = sys.argv[3]; tmp = out + ".silent.mp4"; aud = out + ".wav"; N = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        with Pool(os.cpu_count()) as pool:
            for k, b in enumerate(pool.imap(raw, range(N), chunksize=4)):
                p.stdin.write(b)
                if k % 150 == 0: print(f"{k}/{N}", flush=True)
        p.stdin.close(); p.wait()
        build_audio(aud)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        os.remove(tmp); os.remove(aud); print("listo", out, f"{DUR:.1f}s")
