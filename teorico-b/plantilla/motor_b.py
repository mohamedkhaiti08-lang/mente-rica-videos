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
#   lluvia (carretera mojada / aquaplaning: slide | float | recover), pasos (EN 3 PASOS: tarjeta con n e icono gas | wheel | brake),
#   cinturon (niño en el asiento trasero con cinturón: hook | fit | neck | booster con elevador).
#   cruce admite "tram": true (el 3 es un tranvía sobre raíles, viene del oeste), "rails_hl" y "focus": 3 (brazo izquierdo del 1).
#   senal (SEÑAL MISTERIOSA: hook = señal girando con "?" | pair = R-101 vs R-100 | streets = qué permite cada una);
#   sign admite "kind": "empty" (R-100 vacía) y quiz admite "sign": "empty" | "noentry" (señal en la esquina de la tarjeta).
#   tunel (túnel: hook = perspectiva desde el coche con luces | trap = distancia 2 s vs 100 m/4 s con cronómetro | count = contar segundos con una marca),
#   autovia (autovía en 1ª persona al atardecer: hook | count | band = franja mín/máx | limit = señal del tramo | except = atasco/niebla/avería | exit = warnings y SALIDA),
#   cruce admite "amb": n (el vehículo de la posición n es una ambulancia con sirena: ondas y destellos), "labels": {"3": 1} (número que se ve en cada posición) y "amb_tag"; sfx admite "siren".
#   movil (móvil en la mano al volante: hook | glance = mirar el mapa con cronómetro | blind = metros a ciegas | holder = soporte ✓ / mano ✗); sfx "notif".
#   cruce admite "agent": true (agente cenital en el centro con brazos extendidos E-O), "agent_hl", "agent_zones" (ALTO N-S / PASAN E-O),
#     "lights": {"1": "g", "2": "r"} (semáforo de cada brazo) y "light_x": n; agente (agente de frente que extiende los brazos: sem, sem_x, arrows, tag);
#   jerarquia (orden de preferencia de las señales, art. 133 RGC: 5 filas que aparecen en "at"); puntos admite "tag_red".
#   giro (cruce con coche 1 que gira a la derecha y peatón 2 que cruza sin paso de cebra: car, ped, nozebra, both, rank con "P").
#   niebla (carretera convencional con niebla en 1ª persona: hook = coche con antiniebla trasera | light = niebla no espesa con testigo "?" |
#     list = 4 tarjetas niebla espesa / lluvia muy intensa / fuerte nevada / polvo o humo | front = curvas estrechas con antinieblas delanteras).
#   cuesta (carretera de montaña estrecha: side = vista lateral con el 2 que sube y el 1 que baja, narrow, nosigns, countdown, move, rank |
#     grade = triángulo 100 m / 7 m (gran pendiente ≥ 7 %) | bay = desde arriba, el que sube se mete en el apartadero | flat = llano con obras, pasa el que entró primero).
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
    if v.get("sign"): paste(dst, sign_generic(v["sign"], 0, 150), W / 2 - 360, top + 10 + off, alpha=a, rot=8 * math.sin(t * 2.5))
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
def sign_generic(kind, n, s, flat=False):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    if kind == "speed":
        d.ellipse((0, 0, S - 1, S - 1), fill=(220, 30, 40)); d.ellipse((S * .12, S * .12, S * .88, S * .88), fill=WHITE)
        f = F(BLACK, int(S * .42)); txt = str(n); bb = f.getbbox(txt)
        d.text((S / 2 - (bb[0] + bb[2]) / 2, S / 2 - (bb[1] + bb[3]) / 2), txt, font=f, fill=(20, 20, 20))
    elif kind == "noentry":
        d.ellipse((0, 0, S - 1, S - 1), fill=(220, 30, 40)); d.rounded_rectangle((S * .16, S * .42, S * .84, S * .58), radius=10, fill=WHITE)
    elif kind == "empty":  # R-100 circulación prohibida: blanca con borde rojo, vacía
        d.ellipse((0, 0, S - 1, S - 1), fill=(220, 30, 40)); d.ellipse((S * .12, S * .12, S * .88, S * .88), fill=WHITE)
    else:
        return sign_b(s)
    return down(im) if flat else glow(down(im), 30, .5)

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
    if v.get("tram"):  # vías del tranvía en el carril sur del brazo horizontal (por donde viene el 3, desde el oeste)
        ry = cy + RW / 2; hl = v.get("rails_hl")
        for k in range(0, W, 46): d.rectangle((40 + k, ry - 52, 40 + k + 14, ry + 52), fill=(58, 60, 66, 255))
        for dy in (-36, 36):
            d.line([(40, ry + dy), (W - 40, ry + dy)], fill=(20, 20, 24, 255), width=16)
            d.line([(40, ry + dy - 3), (W - 40, ry + dy - 3)], fill=(196, 200, 210, 255), width=7)
        if hl:
            pa = ease(prog(t, .2, .4)); a = int(255 * pa * (.6 + .4 * math.sin(t * 7)))
            d.rounded_rectangle((44, ry - 66, W - 44, ry + 66), radius=24, outline=ORANGE + (a,), width=10)
    fc = v.get("focus")
    if fc == 3 and v.get("tram"):  # el tranvía viene por la IZQUIERDA del 1: brazo oeste resaltado
        pa = ease(prog(t, .3, .5)); a = int(255 * pa * (.6 + .4 * math.sin(t * 6)))
        d.rounded_rectangle((48, cy - RW + 4, cx - RW - 4, cy + RW - 4), radius=22, outline=YEL + (a,), width=12); fc = None
    if fc:  # zona "su derecha" resaltada para el coche fc (1 = brazo este)
        pa = ease(prog(t, .3, .5)); a = int(120 * pa * (.75 + .25 * math.sin(t * 6)))
        d.rectangle((cx + RW, cy - RW, W - 40, cy + RW), fill=(34, 197, 94, a))
    done = set(v.get("done", [])); moves = {m[0]: (m[1], m[2]) for m in v.get("move", [])}
    for n in (1, 2, 3):
        if n in done: continue
        k = 0.0
        if n in moves: s, du = moves[n]; k = ease(prog(t, s, du)) ** 1.4
        x, y, rot = cruce_pos(n, k)
        istram = n == 3 and v.get("tram")
        if istram: x = lerp(cx - RW - 260, W + 420, k)
        x0, y0, _ = cruce_pos(n, 0.0)
        if k == 0 and t < .5 and not v.get("still"):  # entrada al cruce
            e = eout(prog(t, 0, .5)); dx, dy = {1: (0, 160), 2: (160, 0), 3: (-160, 0)}[n]; x += dx * (1 - e); y += dy * (1 - e)
        isamb = n == v.get("amb")
        if isamb:  # destellos azules en el asfalto + ondas de sirena hacia delante
            ph = int(t * 6) % 2; ga = int(90 + 60 * math.sin(t * 12))
            fx, fy, a0 = {1: (0, -60, 200), 2: (-60, 0, 110), 3: (60, 0, -70)}[n]
            for kk in range(3):
                z = (t * .9 + kk / 3) % 1; r = 150 + 210 * z; al = int(200 * (1 - z))
                d.arc((x + fx - r, y + fy - r, x + fx + r, y + fy + r), a0, a0 + 140, fill=((60, 140, 255) if (kk + ph) % 2 else (255, 70, 70)) + (al,), width=12)
            car = ambulance_top(124, ph)
        else: car = tram_top() if istram else car_top(CRUCE_COLS[n], 120)
        paste(lay, car, x, y, rot=rot)
        if k < .02 and not (v.get("agent") and n == 1):  # flecha de dirección
            al = int(230 * (.6 + .4 * math.sin(t * 5)))
            if n == 1: arrow_v(d, x, y - 175, -1, al)
            else: arrow(d, x + (-150 if n == 2 else (290 if istram else 150)), y, -1 if n == 2 else 1, al)
        bx, by = {1: (x + 125, y + 30), 2: (x + 20, y - 125), 3: (x + (60 if istram else -20), y + (140 if istram else 125))}[n]
        paste(lay, num_badge(int(v.get("labels", {}).get(str(n), n))), bx, by, scale=eback(prog(t, .15 + n * .12, .35)) if not v.get("still") else 1)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    if v.get("nosigns"):  # sin señales: ceda y semáforo tachados en las esquinas
        for k, (ix, iy) in enumerate(((cx - RW - 200, top + 150), (W - 150, bot - 150))):
            p = prog(t, .2 + k * .35, .35); im = sign_ceda(170) if k == 0 else semaphore(0).resize((92, 240), Image.LANCZOS)
            paste(dst, im, ix, iy, scale=.6 + .4 * eback(p), alpha=ease(p * 2))
            if t > .55 + k * .35: paste(dst, icon_x(110), ix + 60, iy + 70, scale=eback(prog(t, .55 + k * .35, .3)))
    cruce_extras(dst, t, v)
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
            if p > 0: paste(dst, rank_chip(j + 1, int(lab), int(v.get("labels", {}).get(str(lab), lab)), (WHITE if int(lab) == v.get("amb") else None)), cx - RW - 205, top + 62 + j * 90, scale=eback(p), alpha=ease(p * 2))
    if v.get("amb_tag"):  # rótulo "SERVICIO URGENTE" que parpadea en azul/rojo junto a la ambulancia
        ph = int(t * 3) % 2; paste(dst, pill(v["amb_tag"], 36, (40, 110, 255) if ph else (220, 40, 50), WHITE), W / 2, top + 60, scale=eback(prog(t, .3, .35)), alpha=ease(prog(t, .3, .3)))
    if v.get("tag"):
        ty = bot - 70 if v.get("tag_bottom") else top + 60
        paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, ty, scale=eback(prog(t, .4, .4)), alpha=ease(prog(t, .4, .3)))

@lru_cache(maxsize=16)
def rank_chip(pos, car, lab=None, col=None):
    p = pill(f"{pos}º", 44, NAVY if pos > 1 else YEL, WHITE if pos > 1 else NAVY, padx=26); b = num_badge(lab or car, 74, col or mix(CRUCE_COLS[car], WHITE, .15), NAVY)
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
            paste(dst, pill(v["tag"], 44, RED if (v.get("cross") or v.get("tag_red")) else YEL, WHITE if (v.get("cross") or v.get("tag_red")) else NAVY), W / 2 + 200, cy + 215,
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
            if p > 0: paste(dst, rank_chip(j + 1, int(lab), int(v.get("labels", {}).get(str(lab), lab)), (WHITE if int(lab) == v.get("amb") else None)), 160, top + 70 + j * 92, scale=eback(p), alpha=ease(p * 2))
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

# --- lluvia y aquaplaning (bloque conducción eficiente y clima) ---
# vis: {"type": "lluvia", "mode": "slide" | "float" | "recover", "lines": [...], "cols": [...], "tag": "...", "tag_at": 1.0}
#   slide: carretera mojada en perspectiva con lluvia, coche que culea y salpica | float: corte lateral de la rueda flotando sobre el agua
#   recover: el coche se endereza y sigue recto (flecha verde)
# vis: {"type": "pasos", "n": 1..3, "icon": "gas" | "wheel" | "brake", "title": "...", "sub": "...", "bad": false}
def rain(dst, t, n=70, a=120, box=None):
    x0, y0, x1, y1 = box or (40, VZ[0], W - 40, VZ[1] + 20); d = ImageDraw.Draw(dst, "RGBA")
    for k in range(n):
        sx = (k * 157.3) % (x1 - x0); sp = 1.4 + (k % 5) * .18; z = ((k * .137) + t * sp) % 1.0
        x = x0 + (sx + z * 90) % (x1 - x0); y = y0 + z * (y1 - y0); L = 34 + (k % 4) * 12
        if y + L < y1: d.line([(x, y), (x + L * .22, y + L)], fill=(200, 220, 255, a), width=3)

def wet_road(dst, t, horizon=520):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); vx = W / 2; top, bot = horizon, VZ[1] + 20
    for y in range(VZ[0], top):  # cielo gris de tormenta
        k = (y - VZ[0]) / max(1, top - VZ[0]); d.line([(40, y), (W - 40, y)], fill=mix((50, 58, 74), (110, 120, 138), k) + (255,))
    d.polygon([(40, top), (W - 40, top), (W - 40, bot), (40, bot)], fill=(52, 66, 58, 255))
    d.polygon([(vx - 70, top), (vx + 70, top), (vx + 640, bot), (vx - 640, bot)], fill=(30, 36, 46, 255))
    # reflejos del agua en el asfalto
    for k in range(7):
        z = ((k / 7) + t * .5) % 1.0; y = top + (bot - top) * z ** 1.5; wv = 60 + 380 * z ** 1.5
        d.ellipse((vx - wv, y - 6 - 10 * z, vx + wv, y + 6 + 10 * z), fill=(120, 160, 220, int(60 * z)))
    d.line([(vx - 70, top), (vx - 640, bot)], fill=(255, 255, 255, 200), width=8); d.line([(vx + 70, top), (vx + 640, bot)], fill=(255, 255, 255, 200), width=8)
    for k in range(10):
        z = ((k / 10) + t * 0.9) % 1.0; z2 = min(1, z + 0.05)
        y1, y2 = top + (bot - top) * z ** 1.6, top + (bot - top) * z2 ** 1.6
        x1 = vx + 0.0 * z; d.line([(vx, y1), (vx, y2)], fill=(255, 255, 255, int(220 * z)), width=max(2, int(12 * z)))
    # gran charco
    d.ellipse((vx - 420, bot - 330, vx + 420, bot - 130), fill=(90, 140, 210, 120))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, VZ[0], W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    return top, bot

@lru_cache(maxsize=2)
def splash(s=200):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(9):
        an = math.pi + k * math.pi / 8; r = s * .38
        d.ellipse((s / 2 + math.cos(an) * r - 16, s * .8 + math.sin(an) * r * .9 - 16, s / 2 + math.cos(an) * r + 16, s * .8 + math.sin(an) * r * .9 + 16), fill=(210, 230, 255, 210))
    return im.filter(ImageFilter.GaussianBlur(3))

def vis_lluvia(dst, t, v, i):
    if i == 0: t = t + 0.6
    mode = v.get("mode", "slide")
    if mode in ("slide", "recover"):
        top, bot = wet_road(dst, t)
        if mode == "slide":
            rot = 9 * math.sin(t * 3.2); dx = 70 * math.sin(t * 1.6)
        else:
            k = eout(prog(t, .1, 1.2)); rot = 10 * (1 - k) * math.cos(t * 4); dx = 60 * (1 - k)
        y = bot - 250; car = car_rear(470)
        for sx in (-1, 1):
            z = (t * 3 + (sx + 1) * .3) % 1
            paste(dst, splash(220), W / 2 + dx + sx * 190, y + 120, scale=.8 + .5 * z, alpha=.9 * (1 - z * .6))
        paste(dst, car, W / 2 + dx, y, rot=rot)
        if mode == "recover":
            pa = ease(prog(t, .7, .6)); d = ImageDraw.Draw(dst, "RGBA")
            if pa > 0:
                y0, y1 = y - 210, lerp(y - 210, top + 40, pa)
                d.line([(W / 2, y0), (W / 2, y1)], fill=GREEN + (230,), width=22)
                if pa > .95: d.polygon([(W / 2 - 40, y1 + 20), (W / 2 + 40, y1 + 20), (W / 2, y1 - 40)], fill=GREEN + (230,))
        rain(dst, t, 90, 150)
    else:  # float: corte lateral
        d = ImageDraw.Draw(dst, "RGBA"); g = CY + 250; a = ease(prog(t, 0, .25))
        d.rounded_rectangle((60, g, W - 60, g + 70), radius=20, fill=(38, 42, 52, int(255 * a)))   # asfalto
        wp = eout(prog(t, .2, 1.0)); lift = 34 * wp
        # cuña de agua que entra por delante de la rueda
        wx = lerp(W - 60, W / 2 - 160, wp)
        d.polygon([(W - 60, g - 70), (W - 60, g + 4), (wx, g + 4), (wx + 40, g - lift - 4)], fill=(70, 150, 255, int(200 * a)))
        d.rectangle((60, g - 14, W - 60, g + 4), fill=(70, 150, 255, int(150 * a)))
        for k in range(6):  # ondas
            x = (W - 120) * ((k / 6 + t * .4) % 1) + 60; d.arc((x - 40, g - 40, x + 40, g), 200, 340, fill=(190, 220, 255, int(200 * a)), width=5)
        r = 240; cx, cy = W / 2 + 20, g - r - lift + 6
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(24, 24, 28, 255))
        for k in range(16):  # dibujo del neumático
            an = k * math.pi / 8 + t * 2.5
            x1, y1 = cx + math.cos(an) * (r - 4), cy + math.sin(an) * (r - 4); x2, y2 = cx + math.cos(an) * (r - 40), cy + math.sin(an) * (r - 40)
            d.line([(x1, y1), (x2, y2)], fill=(70, 72, 80, 255), width=12)
        d.ellipse((cx - r * .58, cy - r * .58, cx + r * .58, cy + r * .58), fill=(170, 176, 190, 255))
        d.ellipse((cx - r * .18, cy - r * .18, cx + r * .18, cy + r * .18), fill=(90, 96, 110, 255))
        if wp > .6:  # hueco bajo la rueda resaltado
            pk = .5 + .5 * math.sin(t * 8)
            d.ellipse((cx - 120, g - lift - 30, cx + 120, g + 20), outline=RED + (int(160 + 90 * pk),), width=8)
        paste(dst, pill("AGUA", 40, (70, 150, 255), WHITE), W - 220, g - 130, alpha=ease(prog(t, .5, .3)))
        rain(dst, t, 50, 90)
    if v.get("lines"):
        cols = [tuple(c) for c in v.get("cols", [])] or None
        big_lines(dst, v["lines"], t, VZ[0] + 110, cols, size=120)
    if v.get("stamp"):
        sp = prog(t, v.get("stamp_at", 1.0), .2)
        if sp > 0: paste(dst, stamp_img(v["stamp"]), W / 2 + 60, VZ[0] + 400, scale=lerp(2.2, 1.0, eout(sp)), alpha=ease(sp * 1.5), rot=-12)
    if v.get("tag"):
        tp = prog(t, v.get("tag_at", 1.0), .35); col = GREEN if v.get("ok") else (RED if v.get("bad") else YEL)
        paste(dst, pill(v["tag"], 46, col, NAVY if col == YEL else WHITE), W / 2, VZ[1] - 40 if mode == "float" else VZ[0] + 70, scale=eback(tp), alpha=ease(tp * 2))

@lru_cache(maxsize=4)
def wheel_icon(s=420):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.ellipse((S * .04, S * .04, S * .96, S * .96), outline=(30, 32, 40), width=int(S * .1))
    d.ellipse((S * .04, S * .04, S * .96, S * .96), outline=(70, 74, 86), width=10)
    d.ellipse((S * .38, S * .38, S * .62, S * .62), fill=(40, 42, 50))
    for an in (180, 0, 90):
        r1, r2 = S * .12, S * .42; a = math.radians(an)
        d.line([(S / 2 + math.cos(a) * r1, S / 2 + math.sin(a) * r1), (S / 2 + math.cos(a) * r2, S / 2 + math.sin(a) * r2)], fill=(40, 42, 50), width=int(S * .08))
    d.ellipse((S * .44, S * .44, S * .56, S * .56), fill=YEL)
    return down(im)

@lru_cache(maxsize=4)
def pedal_icon(kind="gas", s=300):
    w, h = s, int(s * 1.25); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    if kind == "gas": box = (X * .3, Y * .06, X * .7, Y * .94)
    else: box = (X * .12, Y * .3, X * .88, Y * .8)
    d.rounded_rectangle(box, radius=int(X * .1), fill=(40, 42, 50), outline=(110, 116, 130), width=10)
    for k in range(5 if kind == "gas" else 3):
        if kind == "gas": y = Y * (.18 + k * .15); d.rounded_rectangle((X * .37, y, X * .63, y + Y * .05), radius=10, fill=(80, 84, 96))
        else: y = Y * (.4 + k * .12); d.rounded_rectangle((X * .2, y, X * .8, y + Y * .05), radius=10, fill=(80, 84, 96))
    return down(im)

@lru_cache(maxsize=2)
def shoe(s=230):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.rounded_rectangle((S * .2, S * .05, S * .8, S * .95), radius=int(S * .3), fill=(230, 235, 245))
    d.rounded_rectangle((S * .2, S * .6, S * .8, S * .95), radius=int(S * .3), fill=(60, 64, 76))
    return down(im)

def vis_pasos(dst, t, v, i):
    n = v.get("n", 1); ic = v.get("icon", "gas"); rain(dst, t, 40, 70); d = ImageDraw.Draw(dst, "RGBA")
    # puntos de progreso 1-2-3
    for k in range(3):
        on = k + 1 <= n; x = W / 2 + (k - 1) * 150; y = VZ[0] + 40
        paste(dst, num_badge(k + 1, 84, YEL if on else (70, 80, 100), NAVY if on else (150, 160, 180)), x, y, scale=(1.15 if k + 1 == n else 1) * (eback(prog(t, 0, .4)) if k + 1 == n else 1))
        if k < 2: d.line([(x + 50, y), (x + 100, y)], fill=(255, 255, 255, 120 if k + 1 < n else 50), width=6)
    p = eback(prog(t, 0, .45)); c = card(860, 720, fill=(255, 255, 255, 248), r=48)
    cy = CY + 60; paste(dst, c, W / 2, cy + (1 - p) * 160, alpha=ease(prog(t, 0, .2)))
    off = (1 - p) * 160
    paste(dst, text(f"PASO {n}", 46, BLUE, BLACK, shadow=False), W / 2, cy - 300 + off)
    tl = wrap(v.get("title", ""), 64, BLACK, 760)
    for k, l in enumerate(tl): paste(dst, text(l, 64, DARK, BLACK, shadow=False), W / 2, cy - 215 + k * 72 + off)
    iy = cy + 120 + off
    if ic == "gas":
        paste(dst, pedal_icon("gas", 250), W / 2 - 90, iy + 30)
        up = eout(prog(t, .5, 1.0)); paste(dst, shoe(200), W / 2 - 90, iy - 10 - 150 * up, rot=-15)
        if up > .3:
            for k in range(3):
                y = iy - 60 - k * 60 - 80 * up; d.polygon([(W / 2 + 140, y), (W / 2 + 190, y + 50), (W / 2 + 90, y + 50)], fill=GREEN + (int(255 * min(1, up * 1.5)) ,))
        paste(dst, pill(v.get("chip", "SUAVE"), 38, GREEN, WHITE), W / 2 + 170, iy + 160, alpha=ease(prog(t, .9, .3)))
    elif ic == "wheel":
        sh = 7 * math.sin(t * 22) * (1 - eout(prog(t, .6, .6)))
        paste(dst, wheel_icon(360), W / 2, iy + 20, rot=sh)
        for sx in (-1, 1):  # manos
            hp = eback(prog(t, .3, .4)); paste(dst, shoe(110), W / 2 + sx * 172, iy + 20 - 10, scale=hp, rot=sx * 90)
        paste(dst, pill(v.get("chip", "FIRME, SIN VOLANTAZOS"), 38, GREEN, WHITE), W / 2, iy - 150, alpha=ease(prog(t, .9, .3)))
    else:  # brake
        paste(dst, pedal_icon("brake", 300), W / 2, iy + 20)
        bp = prog(t, .4, .5); paste(dst, shoe(200), W / 2, iy - 140 + 60 * math.sin(clamp(bp) * math.pi), rot=-10)
        xp = prog(t, .9, .25)
        if xp > 0: paste(dst, icon_x(170), W / 2 + 240, iy - 40, scale=lerp(2, 1, eout(xp)), alpha=ease(xp * 2))
        paste(dst, pill(v.get("chip", "NI A FONDO"), 38, RED, WHITE), W / 2 + 240, iy + 110, alpha=ease(prog(t, 1.0, .3)))

# --- cinturón y elevador (bloque vehículo y seguridad, parte 2 de sillitas) ---
# vis: {"type": "cinturon", "mode": "hook" | "fit" | "neck" | "booster", "lines": [...], "tag": "...", "stamp": "SUSPENSO"}
def kid_front(dst, cx, hip, a=1.0, swing=0.0):
    d = ImageDraw.Draw(dst, "RGBA"); al = int(255 * a); skin = (240, 200, 170, al); shirt = (60, 140, 255, al); pants = (30, 40, 70, al)
    sh_y = hip - 250
    for sx in (-1, 1):  # piernas
        d.rounded_rectangle((cx + sx * 55 - 34, hip - 20, cx + sx * 55 + 34, hip + 150 + sx * swing), radius=30, fill=pants)
        d.rounded_rectangle((cx + sx * 55 - 38, hip + 140 + sx * swing, cx + sx * 55 + 38, hip + 175 + sx * swing), radius=16, fill=(20, 20, 24, al))
    d.rounded_rectangle((cx - 110, sh_y, cx + 110, hip + 10), radius=60, fill=shirt)                 # torso
    for sx in (-1, 1): d.rounded_rectangle((cx + sx * 140 - 30, sh_y + 20, cx + sx * 140 + 30, hip - 10), radius=30, fill=shirt)  # brazos
    d.rounded_rectangle((cx - 30, sh_y - 40, cx + 30, sh_y + 10), radius=14, fill=skin)            # cuello
    d.ellipse((cx - 85, sh_y - 200, cx + 85, sh_y - 30), fill=skin)                                   # cabeza
    d.pieslice((cx - 90, sh_y - 210, cx + 90, sh_y - 60), 180, 360, fill=(90, 60, 40, al))           # pelo
    for sx in (-1, 1): d.ellipse((cx + sx * 32 - 9, sh_y - 120, cx + sx * 32 + 9, sh_y - 102), fill=(30, 30, 40, al))
    d.arc((cx - 30, sh_y - 100, cx + 30, sh_y - 60), 20, 160, fill=(150, 60, 60, al), width=6)
    return sh_y

def vis_cinturon(dst, t, v, i):
    if i == 0: t = t + 0.6
    mode = v.get("mode", "fit"); d = ImageDraw.Draw(dst, "RGBA"); cx = W / 2 - 20
    seat_y = CY + 230 if not v.get("lines") else CY + 300
    # asiento trasero
    d.rounded_rectangle((cx - 230, seat_y - 470, cx + 230, seat_y + 30), radius=70, fill=(70, 78, 96, 255))
    d.rounded_rectangle((cx - 120, seat_y - 600, cx + 120, seat_y - 470), radius=40, fill=(56, 62, 78, 255))
    d.rounded_rectangle((cx - 270, seat_y, cx + 270, seat_y + 90), radius=40, fill=(84, 92, 112, 255))
    lift = 0.0; booster_a = 0.0
    if mode == "fit": lift = 70
    elif mode == "booster":
        bp = eout(prog(t, .6, .6)); lift = 70 * bp; booster_a = ease(prog(t, .3, .4))
    if mode in ("booster",):
        bx = lerp(cx - 600, cx, eout(prog(t, .3, .5)))
        d.rounded_rectangle((bx - 170, seat_y - 72, bx + 170, seat_y + 4), radius=24, fill=YEL + (int(255 * booster_a),))
        if booster_a > .5: paste(dst, pill("ELEVADOR", 36, YEL, NAVY), bx, seat_y + 150)
    hip = seat_y - 10 - lift; sw = 14 * math.sin(t * 5)
    sh_y = kid_front(dst, cx, hip, 1.0, sw)
    if mode == "hook":
        pk = .5 + .5 * math.sin(t * 6)
        paste(dst, text("?", 260, YEL, BLACK), cx + 300, sh_y - 120, scale=(.9 + .1 * pk) * eback(prog(t, .2, .4)), rot=10)
    else:
        good = (mode == "fit") or (mode == "booster" and lift > 60)
        anc = (cx + 235, seat_y - 300); buck = (cx - 120, seat_y - 30)
        contact = (cx + 60, seat_y - 285)
        col = GREEN if good else RED
        ba = ease(prog(t, .1, .3))
        d.line([anc, contact, buck], fill=(26, 28, 34, int(255 * ba)), width=46, joint="curve")
        d.line([anc, contact, buck], fill=col + (int(255 * ba),), width=14, joint="curve")
        d.line([(cx - 140, hip - 20), (cx + 150, hip - 20)], fill=(26, 28, 34, int(255 * ba)), width=40)
        d.ellipse((buck[0] - 26, buck[1] - 26, buck[0] + 26, buck[1] + 26), fill=(200, 205, 215, int(255 * ba)))
        ip = prog(t, .5 if mode != "booster" else 1.2, .3)
        if ip > 0: paste(dst, (icon_check if good else icon_x)(120), cx + 330, contact[1], scale=eback(ip))
    if v.get("lines"):
        cols = [tuple(c) for c in v.get("cols", [])] or None
        big_lines(dst, v["lines"], t, VZ[0] + 60, cols, size=118)
    if v.get("stamp"):
        sp = prog(t, v.get("stamp_at", 1.0), .2)
        if sp > 0: paste(dst, stamp_img(v["stamp"]), cx - 250, seat_y - 150, scale=lerp(2.2, .8, eout(sp)), alpha=ease(sp * 1.5), rot=-12)
    if v.get("tag"):
        tp = prog(t, v.get("tag_at", 1.0), .35); good_t = v.get("ok", mode != "neck")
        paste(dst, pill(v["tag"], 44, GREEN if good_t else RED, WHITE), W / 2, VZ[0] + 50, scale=eback(tp), alpha=ease(tp * 2))

# --- tranvía visto desde arriba (para el cruce: "tram": true sustituye al coche 3) ---
@lru_cache(maxsize=2)
def tram_top(w=124, L=470):
    im = ss(w, L); d = ImageDraw.Draw(im); X, Y = w * 2, L * 2
    for y0, y1 in ((0, Y * .49), (Y * .51, Y - 1)):  # dos módulos articulados
        d.rounded_rectangle((0, y0, X - 1, y1), radius=int(X * .22), fill=(236, 238, 242))
        d.rectangle((X * .06, y0 + 30, X * .16, y1 - 30), fill=(220, 40, 50)); d.rectangle((X * .84, y0 + 30, X * .94, y1 - 30), fill=(220, 40, 50))
        for k in range(4): yy = y0 + 60 + k * (y1 - y0 - 120) / 4; d.rounded_rectangle((X * .3, yy, X * .7, yy + 50), radius=10, fill=(200, 205, 214))
    d.rectangle((X * .25, Y * .47, X * .75, Y * .53), fill=(60, 64, 72))  # fuelle
    d.rounded_rectangle((X * .1, 8, X * .9, Y * .07), radius=int(X * .18), fill=(40, 60, 90))  # parabrisas delantero
    d.rounded_rectangle((X * .14, Y * .95, X * .86, Y - 10), radius=20, fill=(40, 60, 90))
    px, py = X / 2, Y * .25  # pantógrafo
    d.polygon([(px, py - 90), (px + 70, py), (px, py + 90), (px - 70, py)], outline=(30, 30, 34), width=10)
    d.line([(px - 100, py), (px + 100, py)], fill=(30, 30, 34), width=12)
    for x0 in (.08, .72): d.rounded_rectangle((X * x0, 2, X * (x0 + .2), 26), radius=8, fill=(255, 240, 200))
    im = down(im); sh = Image.new("RGBA", (w + 40, L + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, L + 26), radius=int(w * .22), fill=(0, 0, 0, 140))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 20)); return sh

# --- SEÑAL MISTERIOSA: señal que entra girando con "?" | pareja de señales | dos calles con lo que permite cada una ---
# vis: {"type": "senal", "mode": "hook" | "pair" | "streets", "kind": "empty", "lines": [...], "tag": "...", "hl": 1}
def street_mini(dst, t, cx, kind, label, ok_down, at=0.0):
    d = ImageDraw.Draw(dst, "RGBA"); top, bot = VZ[0] + 260, VZ[1] - 40; hw = 120; a = int(255 * ease(prog(t, at, .3)))
    paste(dst, sign_generic(kind, 0, 150), cx, VZ[0] + 95, alpha=a / 255, scale=eback(prog(t, at, .4)))
    paste(dst, pill(label, 30, WHITE, NAVY, padx=22), cx, VZ[0] + 205, alpha=a / 255)
    d.rounded_rectangle((cx - hw - 26, top, cx + hw + 26, bot), radius=26, fill=(64, 92, 60, a))
    d.rectangle((cx - hw, top, cx + hw, bot), fill=(36, 40, 50, a))
    for x in (cx - hw + 7, cx + hw - 7): d.line([(x, top), (x, bot)], fill=(255, 255, 255, int(a * .85)), width=6)
    y = top + 20
    while y < bot - 40: d.line([(cx, y), (cx, y + 40)], fill=(255, 255, 255, int(a * .8)), width=6); y += 76
    ly = bot - 170; d.line([(cx + 4, ly), (cx + hw - 10, ly)], fill=(255, 255, 255, a), width=12)  # entrada (donde está la señal)
    # coche que quiere entrar subiendo (carril derecho): se para en la línea
    k = eout(prog(t, at + .2, .8)); yu = lerp(bot + 60, ly + 100, k)
    car = car_top((226, 69, 60), 96); paste(dst, car, cx + 60, min(yu, bot - car.height / 2 + 10), alpha=a / 255)
    if t > at + .9: paste(dst, icon_x(76), cx + 60, ly - 55, scale=eback(prog(t, at + .9, .3)))
    # coche que baja por el otro carril: con R-101 circula; con R-100 tampoco puede circular
    if ok_down:
        yd = lerp(top + 40, bot - 60, (prog(t, at + .2, 2.4)) % 1.0)
        paste(dst, car_top((60, 140, 255), 96), cx - 60, yd, rot=180, alpha=a / 255)
        if t > at + 1.1: paste(dst, icon_check(76), cx - 60, top - 0, scale=eback(prog(t, at + 1.1, .3)))
    else:
        paste(dst, car_top((60, 140, 255), 96), cx - 60, top + 130, rot=180, alpha=a / 255)
        if t > at + 1.1: paste(dst, icon_x(76), cx - 60, top + 270, scale=eback(prog(t, at + 1.1, .3)))

def vis_senal(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: texto y señal ya en pantalla
    mode = v.get("mode", "hook"); kind = v.get("kind", "empty")
    if mode == "hook":
        lines = v.get("lines", [])
        if lines: big_lines(dst, lines, t, VZ[0] + 70, [tuple(c) for c in v.get("cols", [])] or None, size=118)
        p = eback(prog(t, 0, .55)); sy = CY + 120 + math.sin(t * 2.2) * 10
        d = ImageDraw.Draw(dst, "RGBA"); d.rounded_rectangle((W / 2 - 16, sy + 200, W / 2 + 16, VZ[1] + 40), radius=8, fill=(150, 160, 175, 255))  # poste
        for k in range(3):  # ondas de "misterio"
            z = (t * .7 + k / 3) % 1; r = 260 + 200 * z
            d.ellipse((W / 2 - r, sy - r, W / 2 + r, sy + r), outline=(255, 196, 0, int(120 * (1 - z))), width=8)
        paste(dst, sign_generic(kind, 0, 480), W / 2, sy, scale=.4 + .6 * p, rot=(1 - p) * 200 + 4 * math.sin(t * 3))
        if v.get("q", True):
            pk = .5 + .5 * math.sin(t * 6); paste(dst, text("?", 260, (30, 30, 36), BLACK, shadow=False), W / 2, sy, scale=(.9 + .1 * pk) * eback(prog(t, .35, .4)), alpha=ease(prog(t, .35, .2)))
        if v.get("tag"): paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, VZ[1] - 20, scale=eback(prog(t, .1, .35)), alpha=ease(prog(t, .1, .3)))
    elif mode == "pair":
        data = [("noentry", "ENTRADA PROHIBIDA", "Roja con franja"), ("empty", "CIRCULACIÓN PROHIBIDA", "Blanca y vacía")]
        hl = v.get("hl", 1)
        for k, (kd, name, sub) in enumerate(data):
            px = W / 2 + (-215 if k == 0 else 215); p = eback(prog(t, k * .45, .45)); a = ease(prog(t, k * .45, .3))
            y = CY + 20 + (1 - p) * 160
            paste(dst, card(400, 640, fill=(255, 255, 255, 250), r=40, border=(GREEN if k == hl else None), bw=(8 if k == hl else 0)), px, y, alpha=a)
            paste(dst, sign_generic(kd, 0, 270, True), px, y - 110, alpha=a, scale=.7 + .3 * p)
            nm = name.split(" ")
            for j, l in enumerate(nm): paste(dst, text(l, 40, DARK, BLACK, shadow=False), px, y + 100 + j * 50, alpha=a)
            paste(dst, text(sub, 32, (90, 96, 110), XB, shadow=False), px, y + 220, alpha=a)
        if v.get("tag"): paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, VZ[0] + 20, scale=eback(prog(t, 1.0, .35)), alpha=ease(prog(t, 1.0, .3)))
    else:  # streets
        street_mini(dst, t, W / 2 - 235, "noentry", "ENTRADA PROHIBIDA", True, 0.0)
        street_mini(dst, t, W / 2 + 190, "empty", "CIRCULACIÓN PROHIBIDA", False, v.get("at2", 0.9))

# --- TÚNEL: perspectiva desde el coche (hook) | vista cenital con distancia 2 s vs 4 s (trap) | contar segundos con una marca (count) ---
# vis: {"type": "tunel", "mode": "hook" | "trap" | "count", "lines": [...], "cols": [...], "tag": "..."}
def tunnel_persp(dst, t, top):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    x0, x1, bot = 40, W - 40, VZ[1] + 20; vx, vy = W / 2, top + (bot - top) * .42
    d.rectangle((x0, top, x1, bot), fill=(18, 20, 26, 255))
    # boca del túnel al fondo (luz)
    for k in range(6):
        r = 40 + k * 14; d.ellipse((vx - r * 1.3, vy - r, vx + r * 1.3, vy + r), fill=(255, 236, 190, 40))
    d.ellipse((vx - 52, vy - 40, vx + 52, vy + 40), fill=(255, 244, 214, 255))
    # paredes, techo y calzada en perspectiva
    d.polygon([(x0, top), (vx - 60, vy - 45), (vx - 60, vy + 40), (x0, bot)], fill=(70, 74, 84, 255))
    d.polygon([(x1, top), (vx + 60, vy - 45), (vx + 60, vy + 40), (x1, bot)], fill=(62, 66, 76, 255))
    d.polygon([(x0, top), (x1, top), (vx + 60, vy - 45), (vx - 60, vy - 45)], fill=(40, 42, 50, 255))
    d.polygon([(x0 + 70, bot), (x1 - 70, bot), (vx + 50, vy + 40), (vx - 50, vy + 40)], fill=(44, 46, 54, 255))
    # azulejos de la pared y luces del techo que vienen hacia nosotros
    for k in range(16):
        z = ((k / 16) + t * .55) % 1.0; z2 = min(1.0, z + .03); e, e2 = z ** 2.2, z2 ** 2.2
        for side in (-1, 1):
            # luces del techo (dos filas)
            for off in (.28, .62):
                ax, ay = vx + side * 60 * off, vy - 45
                bx, by = vx + side * (W / 2 - 40) * off, top
                p1 = (lerp(ax, bx, e), lerp(ay, by, e)); p2 = (lerp(ax, bx, e2), lerp(ay, by, e2))
                d.line([p1, p2], fill=(255, 200, 90, int(80 + 175 * z)), width=max(2, int(18 * z)))
            # franja de la pared
            ax, ay = vx + side * 60, vy + 10; bx, by = (x0 if side < 0 else x1), top + (bot - top) * .55
            p1 = (lerp(ax, bx, e), lerp(ay, by, e)); p2 = (lerp(ax, bx, e2), lerp(ay, by, e2))
            d.line([p1, p2], fill=(120, 190, 120, int(60 + 120 * z)), width=max(2, int(20 * z)))
        # discontinua central
        p1 = (vx, lerp(vy + 40, bot, e)); p2 = (vx, lerp(vy + 40, bot, e2))
        d.line([p1, p2], fill=(255, 255, 255, int(90 + 165 * z)), width=max(2, int(26 * z)))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((x0, top, x1, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    # coche de delante (cerca: demasiado pegado)
    cy = vy + (bot - vy) * .42 + math.sin(t * 9) * 2; car = car_rear(300)
    paste(dst, car, vx + 70, cy)
    return vx, vy, bot

def stopwatch(dst, cx, cy, secs, a=1.0, col=YEL, r=88):
    d = ImageDraw.Draw(dst, "RGBA"); al = int(255 * a)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, al), outline=NAVY + (al,), width=10)
    d.rounded_rectangle((cx - 18, cy - r - 30, cx + 18, cy - r - 4), radius=6, fill=NAVY + (al,))
    frac = clamp(secs / 4.0)
    if frac > 0: d.pieslice((cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16), -90, -90 + 360 * frac, fill=col + (int(al * .55),))
    s = f"{int(secs)} s" if secs >= 1 else "0 s"
    paste(dst, text(s, 60, NAVY, BLACK, shadow=False), cx, cy + 4, alpha=a)

TUN = (330, 750)  # calzada del túnel (x)
def tunnel_top(dst, t, scroll=True):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; a, b = TUN
    d.rectangle((40, top, W - 40, bot), fill=(58, 54, 50, 255))
    for k in range(30):  # roca
        gx, gy = 60 + (k * 263) % (W - 120), top + (k * 157) % (bot - top)
        d.ellipse((gx - 34, gy - 22, gx + 34, gy + 22), fill=(68, 63, 58, 255))
    d.rectangle((a - 60, top, b + 60, bot), fill=(150, 154, 162, 255))  # paredes
    d.rectangle((a, top, b, bot), fill=(40, 43, 52, 255))
    off = (t * 260) % 95 if scroll else 0
    y = top - 95 + off
    while y < bot:
        d.line([((a + b) / 2, y), ((a + b) / 2, y + 50)], fill=(255, 255, 255, 200), width=7)
        for wx in (a - 30, b + 30): d.ellipse((wx - 11, y + 20, wx + 11, y + 42), fill=(255, 210, 110, 255))  # luces
        y += 95
    for x in (a + 8, b - 8): d.line([(x, top), (x, bot)], fill=(255, 255, 255, 220), width=6)
    return lay, top, bot

def clip_vz(dst, lay, top, bot):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)

def gap_bracket(d, x, y1, y2, col, a):
    d.line([(x, y1), (x, y2)], fill=col + (a,), width=8)
    for y, s in ((y1, 1), (y2, -1)): d.polygon([(x, y), (x - 22, y + s * 32), (x + 22, y + s * 32)], fill=col + (a,))

def vis_tunel(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: texto y túnel ya en pantalla
    mode = v.get("mode", "hook"); lane = TUN[0] + (TUN[1] - TUN[0]) * .75
    if mode == "hook":
        lines = v.get("lines", [])
        if lines: big_lines(dst, lines, t, VZ[0] + 40, [tuple(c) for c in v.get("cols", [])] or None, size=110)
        vx, vy, bot = tunnel_persp(dst, t, VZ[0] + 250)
        if v.get("tag"): paste(dst, pill(v["tag"], 40, RED, WHITE), W / 2, VZ[1] - 30, scale=eback(prog(t, .2, .35)), alpha=ease(prog(t, .2, .3)))
        return
    lay, top, bot = tunnel_top(dst, t, scroll=(mode != "count")); d = ImageDraw.Draw(lay, "RGBA")
    if mode == "trap":
        yf = top + 170; k = ease(prog(t, 1.6, .9)); gap2, gap4 = 300, 640
        yr = yf + lerp(gap2, gap4, k)
        paste(lay, car_top((60, 140, 255), 120), lane, yf); paste(lay, car_top((226, 69, 60), 120), lane, yr)
        clip_vz(dst, lay, top, bot); d = ImageDraw.Draw(dst, "RGBA")
        y1, y2 = yf + 115, yr - 115; col = RED if k < .5 else GREEN
        gap_bracket(d, lane - 120, y1, y2, col, int(255 * ease(prog(t, .2, .3))))
        lab = "2 s" if k < .5 else "100 m · 4 s"
        paste(dst, pill(lab, 44, col, WHITE), lane - 120, (y1 + y2) / 2, alpha=ease(prog(t, .3, .3)))
        if t > .7 and k < .5: paste(dst, icon_x(96), lane - 120, (y1 + y2) / 2 + 90, scale=eback(prog(t, .7, .3)))
        if k >= .99: paste(dst, icon_check(96), lane - 120, (y1 + y2) / 2 + 90, scale=eback(prog(t, 2.5, .3)))
        stopwatch(dst, 150, CY + 120, 2 + 2 * k, a=ease(prog(t, .2, .3)), col=(RED if k < .5 else GREEN))
        if v.get("tag"): paste(dst, pill(v["tag"], 38, YEL, NAVY), W / 2, top + 50, scale=eback(prog(t, .5, .35)), alpha=ease(prog(t, .5, .3)))
        return
    # count: marca fija en la calzada; el de delante la pasa y empezamos a contar hasta que la pasamos nosotros
    dur = LINES[i][1] - LINES[i][0]; T = clamp(dur - .3, 3.0, 4.6); ym = top + 260
    G = 560; vel = G / T; yf0 = ym + 30
    yf = yf0 - vel * t; yr = yf + G
    d.rectangle((TUN[0] + 10, ym - 10, TUN[1] - 10, ym + 10), fill=YEL + (255,))
    paste(lay, car_top((60, 140, 255), 120), lane, yf); paste(lay, car_top((226, 69, 60), 120), lane, yr)
    clip_vz(dst, lay, top, bot)
    paste(dst, pill("MARCA", 34, YEL, NAVY), TUN[0] + 95, ym - 46)
    t0 = 30 / vel; el = t - t0; n = 0 if el < 0 else min(4, int(el / (T / 4)) + 1)
    if yr <= ym + 4: n = 4
    stopwatch(dst, 150, CY + 120, n if n else 0, a=1.0, col=(GREEN if n >= 4 else YEL))
    if n:
        pk = prog(el, (n - 1) * T / 4, .25)
        paste(dst, text(str(n), 210, GREEN if n >= 4 else YEL, BLACK), 150, CY - 130, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))
    if yr <= ym + 4: paste(dst, icon_check(110), lane, ym - 110, scale=eback(prog(t, T + t0 - .1, .3)))

# --- peatón visto desde arriba + coche que gira (formato ¿QUIÉN PASA PRIMERO?, bloque peatones) ---
# vis: {"type": "giro", "car": [s0, s1, at, dur], "ped": [y0, y1, at, dur], "countdown": [...], "rank": ["P", "1"], "rank_at": [..],
#       "tag": "...", "nozebra": true, "both": true}
@lru_cache(maxsize=8)
def ped_top_img(ph, s=132):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    for k, sx in enumerate((-.16, .16)):  # pies (alternan)
        fy = S * (.5 + (.26 if (k == 0) == (ph == 0) else -.26))
        d.ellipse((S / 2 + sx * S - S * .08, fy - S * .1, S / 2 + sx * S + S * .08, fy + S * .1), fill=(30, 30, 36))
    d.ellipse((S * .14, S * .34, S * .86, S * .66), fill=(34, 160, 90))  # hombros
    for sx in (.1, .9): d.ellipse((S * sx - S * .08, S * (.5 - .08 + (.1 if (sx < .5) == (ph == 0) else -.1)), S * sx + S * .08, S * (.5 + .08 + (.1 if (sx < .5) == (ph == 0) else -.1))), fill=(240, 196, 160))
    d.ellipse((S * .32, S * .3, S * .68, S * .66), fill=(60, 40, 30))  # cabeza (pelo)
    im = down(im); sh = Image.new("RGBA", (s + 30, s + 30), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((15, 22, s + 15, s + 22), fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(8)); sh.alpha_composite(im, (15, 15)); return sh

GX = W / 2 + RW + 180  # x por donde cruza el peatón (brazo este)
def giro_pos(s):
    """coche 1: sube por el carril derecho y gira a la derecha hacia el brazo este. s en píxeles recorridos."""
    cx, cy = W / 2, CY; x0 = cx + RW / 2; ys = cy + RW + 140; L1 = ys - (cy + RW); R = RW / 2; L2 = math.pi / 2 * R
    if s <= L1: return x0, ys - s, 0
    if s <= L1 + L2:
        a = (s - L1) / R  # 0..pi/2
        ccx, ccy = cx + RW, cy + RW
        return ccx - R * math.cos(a), ccy - R * math.sin(a), -math.degrees(a)
    return cx + RW + (s - L1 - L2), cy + RW / 2, -90
GIRO_WAIT = 140 + math.pi / 2 * RW / 2  # final de la curva (el coche espera a mitad de curva, s≈200)

def curve_arrow(d, a, left=False):
    cx, cy = W / 2, CY; col = YEL + (a,)
    if not left:
        R = RW / 2; ccx, ccy = cx + RW, cy + RW
        pts = [(ccx - R * math.cos(k / 12 * math.pi / 2), ccy - R * math.sin(k / 12 * math.pi / 2)) for k in range(13)] + [(cx + RW + 70, cy + RW / 2)]
        d.line(pts, fill=col, width=30, joint="curve"); ex, ey = cx + RW + 70, cy + RW / 2
        d.polygon([(ex + 60, ey), (ex, ey - 42), (ex, ey + 42)], fill=col)
    else:
        x = cx + RW / 2; R = RW; ccx, ccy = cx - RW / 2 + 0, cy - RW / 2 + RW
        pts = [(x, cy + RW)] + [(ccx + R * math.cos(k / 12 * math.pi / 2), ccy - R * math.sin(k / 12 * math.pi / 2)) for k in range(13)] + [(cx - RW - 60, cy - RW / 2)]
        d.line(pts, fill=col, width=30, joint="curve"); ex, ey = cx - RW - 60, cy - RW / 2
        d.polygon([(ex - 60, ey), (ex, ey - 42), (ex, ey + 42)], fill=col)

@lru_cache(maxsize=8)
def rank_chip_ped(pos):
    p = pill(f"{pos}º", 44, NAVY if pos > 1 else YEL, WHITE if pos > 1 else NAVY, padx=26); b = num_badge(2, 74, mix((34, 160, 90), WHITE, .2), NAVY)
    im = Image.new("RGBA", (p.width + b.width + 12, max(p.height, b.height)), (0, 0, 0, 0))
    im.alpha_composite(p, (0, (im.height - p.height) // 2)); im.alpha_composite(b, (p.width + 12, (im.height - b.height) // 2)); return im

def vis_giro(dst, t, v, i):
    tt = t + 0.6 if i == 0 else t
    base = {"done": [1, 2, 3], "countdown": v.get("countdown")}
    vis_cruce(dst, t, base, i)
    cx, cy = W / 2, CY; top, bot = VZ[0] + 10, VZ[1] + 20
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    if v.get("nozebra"):  # dónde NO hay paso de cebra: contorno discontinuo naranja en el cruce del peatón
        a = int(255 * ease(prog(tt, .2, .4)) * (.6 + .4 * math.sin(tt * 7)))
        for y in range(int(cy - RW), int(cy + RW), 40): d.line([(GX - 70, y), (GX - 70, y + 22)], fill=ORANGE + (a,), width=8); d.line([(GX + 70, y), (GX + 70, y + 22)], fill=ORANGE + (a,), width=8)
        nz = True
    s0, s1, cat, cdu = v.get("car", [0, 0, 0, 1]); s = lerp(s0, s1, ease(prog(tt, cat, cdu)))
    if s0 == 0 and s1 == 0 and i == 0: s = -160 * (1 - eout(prog(tt, 0, .5)))
    if s < .5 and not v.get("noarrow"):
        al = int(230 * (.6 + .4 * math.sin(tt * 5))); curve_arrow(d, al)
        if v.get("both"): curve_arrow(d, al, left=True)
    peds = [v.get("ped", [cy + RW + 60, cy + RW + 60, 0, 1])]
    if v.get("both"): peds.append(v.get("ped2"))
    for j, pd in enumerate(peds):
        y0, y1, pat, pdu = pd; pk = prog(tt, pat, pdu); py = lerp(y0, y1, ease(pk)); px = GX if j == 0 else W / 2 - RW - 180
        walking = 0 < pk < 1 or v.get("walk_idle")
        paste(lay, ped_top_img(int(tt * 6) % 2 if walking else 0), px, py)
        paste(lay, num_badge(2, 74, mix((34, 160, 90), WHITE, .2), NAVY), px + 95, py + 20)
    x, y, rot = giro_pos(max(0, s)); 
    if s < 0: y -= s
    paste(lay, car_top(CRUCE_COLS[1], 120), x, y, rot=rot)
    bx, by = (x + 100, y + 40) if rot > -45 else (x - 30, y - 100)
    paste(lay, num_badge(1), bx, by)
    clip_vz(dst, lay, top, bot)
    if v.get("nozebra"): paste(dst, icon_x(80), GX + 120, CY - RW - 60, scale=eback(prog(tt, .5, .3)))
    if v.get("both"):
        for px in (GX, W / 2 - RW - 180): paste(dst, icon_check(84), px, cy - RW - 70, scale=eback(prog(tt, .9, .3)))
    rk = v.get("rank")
    if rk:
        ra = v.get("rank_at", [0] * len(rk))
        for j, (lab, at) in enumerate(zip(rk, ra)):
            p = prog(tt, at, .35)
            if p > 0: paste(dst, rank_chip_ped(j + 1) if lab == "P" else rank_chip(j + 1, int(lab)), cx - RW - 205, top + 62 + j * 90, scale=eback(p), alpha=ease(p * 2))
    if v.get("tag"):
        ty = bot - 70 if v.get("tag_bottom") else top + 60
        paste(dst, pill(v["tag"], 38, YEL, NAVY), W / 2, ty, scale=eback(prog(tt, .4, .4)), alpha=ease(prog(tt, .4, .3)))

# --- AUTOVÍA en primera persona al atardecer: mediana con bionda, 2 carriles, arcén; coche lento delante,
#     franja de velocidades mín/máx, señal de límite, excepciones (atasco, niebla, avería) y salida con warnings ---
# vis: {"type": "autovia", "mode": "hook" | "count" | "band" | "limit" | "except" | "exit",
#       "lines": [...], "cols": [...], "slow": 50, "max": 120, "lim": 80, "countdown": [t1,t2,t3], "tag": "..."}
def av_scene(dst, t, v, flow=1.0, fog=0.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; hz = top + 330; vx = W / 2 - 20
    for y in range(top, hz):  # cielo de atardecer
        k = (y - top) / (hz - top); d.line([(40, y), (W - 40, y)], fill=mix((22, 34, 78), (250, 150, 80), k ** 1.4) + (255,))
    d.ellipse((W - 330, hz - 120, W - 170, hz + 40), fill=(255, 210, 120, 255))  # sol bajo
    for k, (bx, bw, bh) in enumerate(((40, 260, 60), (260, 300, 90), (520, 260, 50), (740, 320, 80))):  # colinas
        d.ellipse((bx - 40, hz - bh, bx + bw + 40, hz + bh), fill=(70, 66, 96, 255))
    d.rectangle((40, hz, W - 40, bot), fill=(84, 110, 70, 255))  # campo
    U = lambda u: hz + (bot - hz) * u
    X = lambda lat, u: vx + (lat - .5) * 1500 * u + (lat - .5) * 26
    def quad(l0, l1, u0, u1, col):
        d.polygon([(X(l0, u0), U(u0)), (X(l1, u0), U(u0)), (X(l1, u1), U(u1)), (X(l0, u1), U(u1))], fill=col)
    quad(-1.45, -1.0, 0, 1, (96, 120, 80, 255))      # mediana con hierba
    quad(-1.0, 1.3, 0, 1, (48, 52, 62, 255))         # calzada (2 carriles + arcén)
    d.line([(X(-1, 0), U(0)), (X(-1, 1), U(1))], fill=(240, 240, 240, 255), width=10)   # borde izquierdo
    d.line([(X(1, 0), U(0)), (X(1, 1), U(1))], fill=(240, 240, 240, 255), width=12)     # línea continua del arcén
    for k in range(10):  # línea discontinua entre carriles (se mueve)
        z = ((k / 10) + t * .6 * flow) % 1.0; z2 = min(1, z + .05)
        d.line([(X(0, z ** 2), U(z ** 2)), (X(0, z2 ** 2), U(z2 ** 2))], fill=(255, 255, 255, 235), width=max(3, int(18 * z)))
    for k in range(14):  # bionda (barrera metálica) con postes que pasan
        z = ((k / 14) + t * .6 * flow) % 1.0; zz = z ** 2; y = U(zz); x = X(-1.18, zz)
        d.line([(x, y), (x, y - 70 * zz - 4)], fill=(150, 156, 168, 255), width=max(2, int(12 * zz)))
    d.line([(X(-1.18, 0), U(0) - 3), (X(-1.18, 1), U(1) - 70)], fill=(200, 206, 216, 255), width=16)
    for k in range(5):  # adelfas en la mediana
        z = ((k / 5 + .1) + t * .6 * flow) % 1.0; zz = z ** 2; x = X(-1.32, zz); y = U(zz); r = 8 + 70 * zz
        d.ellipse((x - r, y - 1.6 * r, x + r, y), fill=(56, 110, 64, 255)); d.ellipse((x - r * .4, y - 1.5 * r, x - r * .1, y - 1.2 * r), fill=(240, 120, 170, 255))
    if fog > 0:  # niebla
        fg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fg)
        for k in range(6): yy = hz - 60 + k * 70 + 10 * math.sin(t + k); fd.rectangle((40, yy, W - 40, yy + 90), fill=(225, 228, 235, int(120 * fog)))
        lay.alpha_composite(fg.filter(ImageFilter.GaussianBlur(26)))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    return top, bot, hz, vx, U, X

def av_dash(dst, sp, top, bot, warn=False, t=0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); dy = bot - 120
    d.ellipse((-200, dy, W + 200, dy + 420), fill=(18, 20, 26, 255)); d.ellipse((-200, dy - 6, W + 200, dy + 410), outline=(60, 64, 78, 255), width=6)
    d.ellipse((120, dy + 30, 620, dy + 530), outline=(30, 32, 38, 255), width=50)
    d.rounded_rectangle((W / 2 - 110, dy + 34, W / 2 + 110, dy + 106), radius=20, fill=(8, 10, 14, 255), outline=(60, 64, 78, 255), width=4)
    d.text((W / 2 - 92, dy + 44), str(sp), font=F(BLACK, 50), fill=(120, 220, 255)); d.text((W / 2 + 6, dy + 62), "km/h", font=F(XB, 26), fill=(120, 160, 200))
    if warn:  # botón de warnings que parpadea
        on = int(t * 2.5) % 2 == 0; c = (255, 150, 0) if on else (110, 70, 20); bx, by = W / 2 + 200, dy + 70
        d.polygon([(bx, by - 34), (bx + 38, by + 26), (bx - 38, by + 26)], outline=c + (255,), width=9)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)

def speed_band(dst, t, y, vmin=60, vmax=120, lim=None, at=0.0, marker=None):
    """franja 0-130 km/h: rojo por debajo del mínimo, verde entre mínimo y máximo (o el límite del tramo)."""
    a = ease(prog(t, at, .3)); x0, x1 = 120, 900; sc = lambda kmh: x0 + (x1 - x0) * kmh / 130
    paste(dst, card(860, 250, fill=(255, 255, 255, 248), r=36), W / 2 - 5, y, alpha=a)
    if a < .05: return
    d = ImageDraw.Draw(dst, "RGBA"); al = int(255 * a); top = vmax if lim is None else lim
    k = ease(prog(t, at + .2, .7))
    d.rounded_rectangle((x0, y - 30, x1, y + 30), radius=30, fill=(225, 229, 236, al))
    d.rounded_rectangle((x0, y - 30, lerp(x0, sc(vmin), k), y + 30), radius=30, fill=RED + (al,))
    if k > .99:
        k2 = ease(prog(t, at + .9, .6)); d.rectangle((sc(vmin), y - 30, lerp(sc(vmin), sc(top), k2), y + 30), fill=GREEN + (al,))
    for kmh in (0, 60, 120) if lim is None else (0, 60, lim, 120):
        x = sc(kmh); d.line([(x, y + 34), (x, y + 52)], fill=(60, 66, 80, al), width=5)
        paste(dst, text(str(kmh), 34, DARK, XB, shadow=False), x, y + 80, alpha=a)
    paste(dst, text("MÁS LENTO, NO", 30, RED, BLACK, shadow=False), (x0 + sc(vmin)) / 2 + 8, y - 70, alpha=ease(prog(t, at + .6, .3)))
    paste(dst, text("PERMITIDO", 30, (20, 140, 70), BLACK, shadow=False), (sc(vmin) + sc(top)) / 2, y - 70, alpha=ease(prog(t, at + 1.2, .3)))
    if marker is not None:
        mx = sc(marker); d.polygon([(mx, y - 4), (mx - 22, y - 44), (mx + 22, y - 44)], fill=NAVY + (al,))

def slow_car(dst, t, U, X, u, label=None, col=RED, hazard_on=False):
    y = U(u); x = X(.5, u); sc = .12 + 1.0 * u; car = car_rear(560, (245, 245, 245))
    paste(dst, car, x, y - car.height * sc / 2, scale=sc)
    if hazard_on and int(t * 2.5) % 2 == 0:
        for sx in (-.4, .4): paste(dst, hazard(110), x + sx * 560 * sc, y - car.height * sc * .5, scale=sc * 1.4)
    if label:
        pk = eback(prog(t, .25, .4)); bob = math.sin(t * 5) * 6
        paste(dst, pill(label, 46, col, WHITE), x, y - car.height * sc - 60 + bob, scale=pk, alpha=ease(prog(t, .25, .2)))

def exit_panel(s=1.0):
    w, h = 420, 230; im = ss(w, h); dd = ImageDraw.Draw(im); X2, Y2 = w * 2, h * 2
    dd.rounded_rectangle((0, 0, X2 - 1, Y2 - 1), radius=30, fill=(18, 86, 190), outline=WHITE, width=12)
    dd.text((50, 40), "SALIDA", font=F(BLACK, 96), fill=WHITE)
    dd.line([(X2 * .7, Y2 * .82), (X2 * .7, Y2 * .5), (X2 * .86, Y2 * .3)], fill=WHITE, width=28, joint="curve")
    dd.polygon([(X2 * .93, Y2 * .2), (X2 * .78, Y2 * .26), (X2 * .9, Y2 * .38)], fill=WHITE)
    dd.text((50, Y2 * .55), "1 km", font=F(XB, 70), fill=(210, 225, 255))
    return down(im)

def vis_autovia(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: texto, coche lento y su velocidad ya en pantalla
    mode = v.get("mode", "hook")
    fog = 0.0; flow = .55 if mode in ("hook", "count") else 1.0
    top, bot, hz, vx, U, X = av_scene(dst, t, v, flow, fog)
    if mode in ("hook", "count"):
        u = lerp(.3, .42, eout(prog(t, 0, 1.6))) if mode == "hook" else .42
        slow_car(dst, t, U, X, u, f"{v.get('slow', 50)} km/h")
        av_dash(dst, v.get("ours", 50), top, bot)
        lines = v.get("lines", [])
        if lines: big_lines(dst, lines, t, VZ[0] + 70, [tuple(c) for c in v.get("cols", [])] or None, size=112)
        cd = v.get("countdown")
        if cd:
            n = sum(1 for s in cd if t >= s); ix, iy = 180, top + 210
            paste(dst, semaphore(n).resize((115, 300), Image.LANCZOS), ix, iy, scale=eback(prog(t, 0, .4)))
            if n:
                pk = prog(t, cd[n - 1], .25)
                paste(dst, text(str(4 - n), 170, [RED, (255, 176, 0), GREEN][n - 1], BLACK), 305, iy, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))
            paste(dst, pill("MÍNIMO: ¿? km/h", 50, YEL, NAVY), W / 2, bot - 250, scale=eback(prog(t, .2, .35)), alpha=ease(prog(t, .2, .3)))
    elif mode == "band":
        slow_car(dst, t, U, X, .3, None)
        paste(dst, pill(f"{v.get('slow', 50)} km/h", 42, RED, WHITE), X(.5, .3) + 230, U(.3) - 60, alpha=ease(prog(t, .2, .3)))
        if t > 1.6: paste(dst, icon_x(90), X(.5, .3) + 230, U(.3) + 30, scale=eback(prog(t, 1.6, .3)))
        speed_band(dst, t, top + 170, 60, v.get("max", 120), None, 0.1, marker=v.get("slow", 50))
        p = prog(t, .9, .5); paste(dst, text("60", 210, YEL, BLACK), W / 2 - 250, bot - 200, scale=.6 + .4 * eback(p), alpha=ease(p * 2))
        paste(dst, pill("MÍNIMO", 34, YEL, NAVY), W / 2 - 250, bot - 100, alpha=ease(prog(t, 1.1, .3)))
    elif mode == "limit":
        lim = v.get("lim", 80); u = (prog(t, 0, 3.2) * .9 + .05) ** 1.5; sx = X(1.42, u); sy = U(u); s = 70 + 300 * u
        dd = ImageDraw.Draw(dst, "RGBA"); dd.line([(sx, sy), (sx, sy - s * 1.25)], fill=(150, 156, 168, 255), width=max(3, int(14 * u)))
        paste(dst, sign_generic("speed", lim, 300, True), min(sx, W - 160 - s / 2), max(sy - s * 1.25, top + 310 + s / 2), scale=s / 300)
        av_dash(dst, 70, top, bot)
        speed_band(dst, t, top + 170, 60, 120, lim, 0.0, marker=70)
        if t > 1.4: paste(dst, pill(f"MÍNIMO SIGUE EN 60", 42, YEL, NAVY), W / 2 - 160, CY + 150, scale=eback(prog(t, 1.4, .35)))
    elif mode == "except":  # tres tarjetas: atasco, niebla, avería
        dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(dark).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=(6, 20, 43, 170)); dst.alpha_composite(dark)
        items = [("ATASCO", "jam"), ("OBRAS", "works"), ("AVERÍA", "fail")]
        for k, (lab, ic) in enumerate(items):
            p = eback(prog(t, .1 + k * .45, .4)); a = ease(prog(t, .1 + k * .45, .25)); cx = W / 2 - 290 + k * 280; cy = CY - 30
            paste(dst, card(250, 400, fill=(255, 255, 255, 250), r=34), cx, cy + (1 - p) * 120, alpha=a)
            if a < .05: continue
            icon = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); idr = ImageDraw.Draw(icon, "RGBA")
            idr.rounded_rectangle((20, 10, 200, 210), radius=24, fill=(48, 52, 62, 255))
            if ic == "jam":
                for r in range(3):
                    for c in range(2): icon.alpha_composite(car_top([(226, 69, 60), (60, 140, 255), (255, 196, 0)][(r + c) % 3], 40).resize((40, 72)), (55 + c * 70, 18 + r * 64))
            elif ic == "works":  # conos de obra
                for cxx, cyy, cs in ((70, 150, 1.0), (150, 150, 1.0), (110, 80, .7)):
                    idr.polygon([(cxx, cyy - 70 * cs), (cxx + 34 * cs, cyy), (cxx - 34 * cs, cyy)], fill=(255, 120, 0, 255))
                    idr.polygon([(cxx - 13 * cs, cyy - 40 * cs), (cxx + 13 * cs, cyy - 40 * cs), (cxx + 19 * cs, cyy - 26 * cs), (cxx - 19 * cs, cyy - 26 * cs)], fill=WHITE + (255,))
                    idr.rectangle((cxx - 44 * cs, cyy, cxx + 44 * cs, cyy + 10 * cs), fill=(255, 120, 0, 255))
            else:
                cr = car_rear(150, (245, 245, 245)); icon.alpha_composite(cr, (35, 95))
                if int(t * 2.5) % 2 == 0:
                    for hx in (52, 168): idr.ellipse((hx - 16, 120, hx + 16, 152), fill=(255, 150, 0, 255))
                idr.polygon([(110, 26), (150, 86), (70, 86)], outline=(255, 150, 0, 255), width=8)
            paste(dst, icon, cx, cy - 50 + (1 - p) * 120, alpha=a)
            paste(dst, text(lab, 40, DARK, BLACK, shadow=False), cx, cy + 130 + (1 - p) * 120, alpha=a)
        if v.get("tag"): paste(dst, pill(v["tag"], 42, YEL, NAVY), W / 2, top + 70, scale=eback(prog(t, 1.5, .35)), alpha=ease(prog(t, 1.5, .3)))
    elif mode == "exit":  # avería: warnings y salida por la primera salida
        u = (prog(t, 0, 3.0) * .75 + .1) ** 1.4; px = X(1.6, u); py = U(u) - (60 + 380 * u)
        sc_ = .25 + .8 * u; paste(dst, exit_panel(), min(px, W - 160 - 210 * sc_), py, scale=sc_)
        av_dash(dst, 40, top, bot, warn=True, t=t)
        if int(t * 2.5) % 2 == 0:  # reflejo naranja de los warnings
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            for gx in (90, W - 90): gd.ellipse((gx - 120, bot - 260, gx + 120, bot - 20), fill=(255, 150, 0, 110))
            dst.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
        d = ImageDraw.Draw(dst, "RGBA"); a = int(255 * ease(prog(t, .5, .4)))
        pts = [(X(.5, .9), U(.9)), (X(.75, .5), U(.5)), (X(1.15, .25), U(.25))]
        d.line(pts, fill=YEL + (a,), width=26, joint="curve")
        if v.get("tag"): paste(dst, pill(v["tag"], 42, ORANGE, WHITE), W / 2 - 120, top + 70, scale=eback(prog(t, .3, .35)), alpha=ease(prog(t, .3, .3)))


# --- móvil en la mano al volante (formato ERROR DE NOVATO, bloque alcohol, drogas y móvil) ---
# vis: {"type": "movil", "mode": "hook" | "glance" | "blind" | "holder", "big": "4 DE CADA 10", "small": "...", "tag": "..."}
SKIN = (233, 186, 150); SKIN_D = (205, 152, 118)
@lru_cache(maxsize=8)
def phone_img(screen="notif", w=250, h=500):
    im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    d.rounded_rectangle((0, 0, X - 1, Y - 1), radius=int(X * .16), fill=(22, 24, 30), outline=(70, 74, 86), width=6)
    sx0, sy0, sx1, sy1 = X * .06, Y * .035, X * .94, Y * .965
    if screen == "map":
        d.rounded_rectangle((sx0, sy0, sx1, sy1), radius=int(X * .12), fill=(226, 230, 222))
        for k in range(6): d.line([(sx0, sy0 + Y * (.1 + k * .16)), (sx1, sy0 + Y * (.02 + k * .16))], fill=WHITE, width=22)
        for k in range(4): d.line([(sx0 + X * (.1 + k * .26), sy0), (sx0 + X * (.2 + k * .22), sy1)], fill=WHITE, width=18)
        d.rectangle((sx0 + X * .55, sy0 + Y * .2, sx0 + X * .8, sy0 + Y * .3), fill=(170, 214, 160))
        route = [(X * .5, Y * .9), (X * .46, Y * .62), (X * .66, Y * .44), (X * .62, Y * .16)]
        d.line(route, fill=(40, 120, 255), width=26, joint="curve")
        d.polygon([(X * .5, Y * .8), (X * .44, Y * .88), (X * .56, Y * .88)], fill=(20, 60, 200))
        d.rounded_rectangle((sx0 + 20, sy0 + 20, sx1 - 20, sy0 + Y * .11), radius=30, fill=(20, 110, 70))
        d.polygon([(X * .2, sy0 + Y * .075), (X * .27, sy0 + Y * .04), (X * .27, sy0 + Y * .11)], fill=WHITE)
        d.text((X * .33, sy0 + Y * .045), "300 m", font=F(BLACK, 60), fill=WHITE)
    else:
        d.rounded_rectangle((sx0, sy0, sx1, sy1), radius=int(X * .12), fill=(30, 60, 120))
        d.text((X * .5 - F(BLACK, 110).getlength("10:00") / 2, Y * .12), "10:00", font=F(BLACK, 110), fill=WHITE)
        for k in range(2):  # notificaciones
            y0 = Y * (.34 + k * .2); d.rounded_rectangle((sx0 + 24, y0, sx1 - 24, y0 + Y * .16), radius=34, fill=(245, 247, 250))
            d.ellipse((sx0 + 50, y0 + 30, sx0 + 150, y0 + 130), fill=(34, 197, 94) if k == 0 else (60, 140, 255))
            d.rounded_rectangle((sx0 + 180, y0 + 40, sx1 - 70, y0 + 70), radius=14, fill=(60, 66, 80))
            d.rounded_rectangle((sx0 + 180, y0 + 95, sx1 - 140, y0 + 120), radius=12, fill=(170, 176, 190))
    return down(im)

@lru_cache(maxsize=8)
def hand_phone(screen="notif"):
    w, h = 470, 820; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ph = phone_img(screen)
    lay = ss(w, h); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((w * .62, h * 1.18, w * 1.38, h * 2), radius=60, fill=(30, 52, 96))            # manga
    d.rounded_rectangle((w * .66, h * 1.06, w * 1.34, h * 1.36), radius=80, fill=SKIN_D)              # muñeca
    d.ellipse((w * .5, h * .78, w * 1.5, h * 1.3), fill=SKIN)                                          # palma
    im.alpha_composite(down(lay)); im.alpha_composite(ph, ((w - ph.width) // 2, 40))
    lay = ss(w, h); d = ImageDraw.Draw(lay)
    for k in range(4):  # dedos por la derecha
        y = h * (.86 + k * .17); d.rounded_rectangle((w * 1.36, y, w * 1.62, y + h * .14), radius=50, fill=SKIN if k % 2 == 0 else SKIN_D)
    th = Image.new("RGBA", (120, 360), (0, 0, 0, 0)); ImageDraw.Draw(th).rounded_rectangle((0, 0, 119, 359), radius=60, fill=SKIN)   # pulgar
    th = th.rotate(-28, resample=Image.BICUBIC, expand=True); lay.alpha_composite(th, (int(w * .36), int(h * .86)))
    im.alpha_composite(down(lay)); return im

def vis_movil(dst, t, v, i):
    if i == 0: t = t + 0.6
    mode = v.get("mode", "hook")
    if mode in ("hook", "blind", "holder"):
        top, bot, hz, vx = pov_scene(dst, t * (0.4 if mode == "blind" else 1), {})
        dy = pov_dash(dst, t, {"speed": 50}, top, bot)
    if mode == "hook":
        hp = eback(prog(t, .1, .5)); buzz = math.sin(t * 70) * 6 * (1 if (t % 1.2) < .35 else 0)
        paste(dst, hand_phone("notif"), 590 + buzz, 985 + (1 - hp) * 260, scale=.95, rot=-8 + buzz * .4)
        d = ImageDraw.Draw(dst, "RGBA")
        for k in range(3):  # ondas de vibración
            z = (t * 1.4 + k / 3) % 1; r = 180 + 140 * z; a = int(150 * (1 - z))
            d.arc((590 - r, 775 - r * .6, 590 + r, 775 + r * .6), 200, 340, fill=YEL + (a,), width=8)
        big = v.get("big", "4 DE CADA 10"); s = fit([big], 128, BLACK, 900)
        paste(dst, text(big, s, YEL, BLACK), W / 2, top + 95, scale=.8 + .2 * eback(prog(t, 0, .4)))
        if v.get("small"): paste(dst, pill(v["small"], 34, WHITE, BLUE), W / 2, top + 205, alpha=ease(prog(t, .3, .3)))
    elif mode == "glance":
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); top, bot, hz, vx = pov_scene(lay, t, {}); pov_dash(lay, t, {"speed": 50}, top, bot)
        dk = ease(prog(t, .2, .6)); paste(dst, lay.filter(ImageFilter.GaussianBlur(int(2 + 10 * dk))), W / 2, H / 2)
        d = ImageDraw.Draw(dst, "RGBA"); d.rounded_rectangle((40, top, W - 40, bot), radius=36, fill=(0, 0, 0, int(110 * dk)))
        hp = eout(prog(t, 0, .45)); paste(dst, hand_phone("map"), 560, lerp(1150, 870, hp), scale=lerp(.9, 1.12, hp), rot=lerp(-8, -3, hp))
        stopwatch(dst, 230, top + 170, clamp((t - .3) / .8), a=ease(prog(t, .3, .3)))
        paste(dst, pill("OJOS EN LA PANTALLA", 36, RED, WHITE), W / 2, bot - 60, alpha=ease(prog(t, .7, .3)), scale=eback(prog(t, .7, .35)))
    elif mode == "blind":
        d = ImageDraw.Draw(dst, "RGBA"); m = float(v.get("m", 14)); k = ease(prog(t, .3, 1.6))
        # barra de distancia sobre la calzada: de los pies del coche hacia el horizonte
        y0, y1 = dy - 20, hz + 40; yk = lerp(y0, y1 + (y0 - y1) * .25, k)
        d.polygon([(vx - 300, y0), (vx + 300, y0), (vx + 300 * (yk - hz) / (y0 - hz) + 10, yk), (vx - 300 * (yk - hz) / (y0 - hz) - 10, yk)], fill=(255, 196, 0, 120))
        d.line([(vx - 320 * (yk - hz) / (y0 - hz), yk), (vx + 320 * (yk - hz) / (y0 - hz), yk)], fill=YEL + (255,), width=10)
        bl = .5 + .5 * math.sin(t * 5)  # "ojos cerrados": párpados que bajan
        ea = ease(prog(t, .1, .4)); d.rectangle((40, top, W - 40, top + 120 * ea), fill=(0, 0, 0, 200)); 
        paste(dst, text(f"{int(round(m * k))} m", 190, YEL, BLACK), W / 2, top + 170, scale=.8 + .2 * eback(prog(t, .2, .4)))
        paste(dst, pill(v.get("tag", "A 50 KM/H · 1 SEGUNDO"), 38, WHITE, BLUE), W / 2, top + 300, alpha=ease(prog(t, .4, .3)))
    elif mode == "holder":
        hp = eback(prog(t, .1, .5)); hx, hy = 700, dy - 120
        d = ImageDraw.Draw(dst, "RGBA")
        d.rounded_rectangle((hx - 30, hy + 140, hx + 30, dy + 30), radius=14, fill=(40, 44, 52, 255))      # brazo del soporte
        d.rounded_rectangle((hx - 150, hy - 220, hx + 150, hy + 160), radius=36, fill=(40, 44, 52, 255))  # pinza
        paste(dst, phone_img("map", 230, 420), hx, hy - 30 - (1 - hp) * 80, alpha=ease(prog(t, .1, .25)))
        paste(dst, icon_check(130), hx + 150, hy - 220, scale=eback(prog(t, .6, .35)))
        paste(dst, hand_phone("notif"), 270, 1010, scale=.55, alpha=.85 * ease(prog(t, .3, .3)), rot=-10)
        paste(dst, icon_x(110), 360, 860, scale=eback(prog(t, .8, .35)))
        paste(dst, pill(v.get("tag", "EN EL SOPORTE, SIN TOCARLO"), 40, YEL, NAVY), W / 2, top + 70, scale=eback(prog(t, .4, .35)), alpha=ease(prog(t, .4, .3)))

# --- agente de tráfico (QUIÉN PASA PRIMERO parte 6, bloque señales: orden de preferencia, art. 133 RGC) ---
@lru_cache(maxsize=4)
def agent_top(s=1.0):
    w, h = int(300 * s), int(130 * s); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2; cx, cy = X / 2, Y / 2
    d.rounded_rectangle((X * .05, cy - Y * .1, X * .95, cy + Y * .1), radius=int(Y * .1), fill=(255, 212, 0))   # brazos (manga de chaleco)
    for sx in (X * .03, X * .97): d.ellipse((sx - Y * .14, cy - Y * .14, sx + Y * .14, cy + Y * .14), fill=WHITE)  # guantes
    d.ellipse((cx - X * .2, cy - Y * .36, cx + X * .2, cy + Y * .36), fill=(255, 212, 0))                       # hombros con chaleco
    d.line([(cx - X * .18, cy - Y * .12), (cx + X * .18, cy - Y * .12)], fill=(210, 214, 222), width=int(Y * .06))
    d.ellipse((cx - Y * .24, cy - Y * .24, cx + Y * .24, cy + Y * .24), fill=(20, 34, 70))                      # gorra
    d.ellipse((cx - Y * .12, cy - Y * .12, cx + Y * .12, cy + Y * .12), fill=WHITE)
    im = down(im); sh = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((20 + w * .3, 30, 20 + w * .7, 26 + h), fill=(0, 0, 0, 120)); sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(im, (20, 20)); return sh

def agent_front(dst, cx, cy, arm=1.0, sc=1.0, a=1.0):
    """agente de frente (pies en cy + 300*sc). arm: 0 brazos abajo, 1 extendidos en horizontal."""
    w, h = 900, 760; lay = ss(w, h); d = ImageDraw.Draw(lay); X, Y = w * 2, h * 2; c = X / 2; S = 2
    def R(x0, y0, x1, y1, col, r=20): d.rounded_rectangle((c + x0 * S, y0 * S, c + x1 * S, y1 * S), radius=r * S, fill=col)
    R(-70, 470, -12, 740, (20, 34, 70), 18); R(12, 470, 70, 740, (20, 34, 70), 18)               # piernas
    R(-90, 720, -6, 756, (14, 14, 18), 14); R(6, 720, 90, 756, (14, 14, 18), 14)                   # botas
    for sx in (-1, 1):  # brazos
        ang = math.radians(lerp(-80, 0, arm)) ; L = 250; x0, y0 = sx * 92, 260
        x1, y1 = x0 + sx * L * math.cos(ang), y0 - L * math.sin(ang) * -1
        d.line([(c + x0 * S, y0 * S), (c + x1 * S, y1 * S)], fill=(255, 212, 0), width=64 * S)
        d.ellipse((c + x1 * S - 40 * S, y1 * S - 40 * S, c + x1 * S + 40 * S, y1 * S + 40 * S), fill=WHITE)
    R(-105, 230, 105, 500, (255, 212, 0), 50)                                                       # chaleco
    for yy in (330, 420): R(-105, yy, 105, yy + 26, (210, 214, 222), 6)                              # bandas reflectantes
    R(-24, 230, 24, 500, (20, 34, 70), 10)
    d.ellipse((c - 70 * S, 90 * S, c + 70 * S, 240 * S), fill=SKIN)                                 # cara
    d.ellipse((c - 34 * S, 150 * S, c - 16 * S, 168 * S), fill=(30, 30, 40)); d.ellipse((c + 16 * S, 150 * S, c + 34 * S, 168 * S), fill=(30, 30, 40))
    d.arc((c - 30 * S, 170 * S, c + 30 * S, 210 * S), 20, 160, fill=(120, 60, 50), width=6 * S)
    R(-88, 70, 88, 130, (20, 34, 70), 26); R(-100, 118, 100, 140, (14, 24, 50), 10)                  # gorra
    R(-88, 96, 88, 116, (255, 212, 0), 4)
    paste(dst, down(lay), cx, cy, scale=sc, alpha=a)

SEM_POS = {1: (W / 2 + RW + 190, CY + RW + 120), 2: (W / 2 + RW + 40, CY - RW - 90)}
def cruce_extras(dst, t, v):
    cx, cy = W / 2, CY
    if v.get("agent_zones"):  # zonas: se paran (N y S, rojo) / pasan (E y O, verde)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); pa = ease(prog(t, .3, .5))
        top, bot = VZ[0] + 10, VZ[1] + 20; a = int(110 * pa * (.8 + .2 * math.sin(t * 6)))
        d.rectangle((cx - RW, top, cx + RW, cy - RW), fill=(239, 68, 68, a)); d.rectangle((cx - RW, cy + RW, cx + RW, bot), fill=(239, 68, 68, a))
        d.rectangle((40, cy - RW, cx - RW, cy + RW), fill=(34, 197, 94, a)); d.rectangle((cx + RW, cy - RW, W - 40, cy + RW), fill=(34, 197, 94, a))
        dst.alpha_composite(lay)
        for (x, y, lab, col) in ((cx, top + 70, "ALTO", RED), (cx, bot - 40, "ALTO", RED), (220, cy, "PASAN", GREEN), (W - 240, cy, "PASAN", GREEN)):
            paste(dst, pill(lab, 38, col, WHITE), x, y, scale=eback(prog(t, .5, .35)), alpha=ease(prog(t, .5, .3)))
    for n, st in v.get("lights", {}).items():  # semáforo de cada brazo (r = rojo, g = verde)
        x, y = SEM_POS[int(n)]; im = semaphore(1 if st == "r" else 3).resize((72, 188), Image.LANCZOS)
        paste(dst, im, x, y, scale=eback(prog(t, .1, .35)) if not v.get("still") else 1)
        if v.get("light_x") == int(n): paste(dst, icon_x(70), x + 40, y + 60, scale=eback(prog(t, .5, .3)))
    if v.get("agent"):
        ax, ay = cx, cy + 62
        if v.get("agent_hl"):
            d = ImageDraw.Draw(dst, "RGBA"); r = 175 + 12 * math.sin(t * 6); a = int(255 * ease(prog(t, .2, .3)))
            d.ellipse((ax - r, ay - r * .62, ax + r, ay + r * .62), outline=YEL + (a,), width=10)
        paste(dst, agent_top(0.95), ax, ay, scale=1 + (.06 * math.sin(t * 5) if v.get("agent_hl") else 0))

def vis_agente(dst, t, v, i):
    p = eback(prog(t, 0, .45)); arm = ease(prog(t, .2, .6)) if v.get("raise", True) else 1.0
    c = card(900, 860, fill=(232, 238, 248, 255), r=46); paste(dst, c, W / 2, CY + 20, alpha=ease(prog(t, 0, .25)), scale=.9 + .1 * p)
    d = ImageDraw.Draw(dst, "RGBA"); d.rectangle((W / 2 - 440, CY + 280, W / 2 + 440, CY + 420), fill=(56, 60, 70, 255))
    for k in range(6): d.rectangle((W / 2 - 420 + k * 150, CY + 342, W / 2 - 340 + k * 150, CY + 356), fill=(255, 255, 255, 230))
    agent_front(dst, W / 2, CY + 50, arm, sc=.95)
    if v.get("sem"):
        im = semaphore(3 if v["sem"] == "g" else 1).resize((96, 250), Image.LANCZOS); paste(dst, im, W / 2 + 350, CY - 150, scale=eback(prog(t, .3, .35)))
        if v.get("sem_x"): paste(dst, icon_x(90), W / 2 + 380, CY - 70, scale=eback(prog(t, .8, .35)))
    if v.get("arrows"):  # flechas: ALTO de frente / PASAN por los lados
        a = int(255 * ease(prog(t, .7, .3)))
        for sx in (-1, 1): arrow(d, W / 2 + sx * 400, CY - 330, sx, a)
        paste(dst, pill("PASAN", 34, GREEN, WHITE), W / 2 - 330, CY - 400, alpha=a / 255); paste(dst, pill("PASAN", 34, GREEN, WHITE), W / 2 + 330, CY - 400, alpha=a / 255)
        paste(dst, pill("ALTO: DE FRENTE Y DE ESPALDAS", 36, RED, WHITE), W / 2, CY + 470, scale=eback(prog(t, 1.0, .35)), alpha=ease(prog(t, 1.0, .3)))
    if v.get("tag"): paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, CY + 470, scale=eback(prog(t, .5, .35)), alpha=ease(prog(t, .5, .3)))

@lru_cache(maxsize=8)
def cone_icon(s=120):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.polygon([(S * .5, S * .06), (S * .78, S * .86), (S * .22, S * .86)], fill=(255, 110, 20))
    d.polygon([(S * .4, S * .36), (S * .6, S * .36), (S * .66, S * .54), (S * .34, S * .54)], fill=WHITE)
    d.rounded_rectangle((S * .1, S * .84, S * .9, S * .96), radius=10, fill=(230, 90, 10)); return down(im)

@lru_cache(maxsize=8)
def marks_icon(s=120):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    d.rounded_rectangle((0, S * .1, S, S * .9), radius=20, fill=(56, 60, 70))
    for k in range(3): d.rectangle((S * (.08 + k * .32), S * .44, S * (.3 + k * .32), S * .56), fill=WHITE)
    return down(im)

def vis_jerarquia(dst, t, v, i):
    rows = [("AGENTE", "agent"), ("SEÑALES PROVISIONALES", "cone"), ("SEMÁFORO", "sem"), ("SEÑAL VERTICAL", "sign"), ("MARCAS VIALES", "marks")]
    top = VZ[0] + 60; rh = 150; d = ImageDraw.Draw(dst, "RGBA"); at = v.get("at", [0, .9, 1.8, 2.5, 3.0])
    for k, (lab, ic) in enumerate(rows):
        p = prog(t, at[k], .35)
        if p <= 0: continue
        y = top + k * rh + 70; wdt = 880 - k * 60; hl = k == 0
        c = card(wdt, 120, fill=(255, 212, 0, 255) if hl else ((255, 255, 255, 245) if k != 2 else (226, 236, 255, 255)), r=34)
        paste(dst, c, W / 2, y, scale=.85 + .15 * eback(p), alpha=ease(p * 2))
        x0 = W / 2 - wdt / 2 + 70
        paste(dst, num_badge(k + 1, 80, NAVY if hl else BLUE, WHITE if hl else WHITE), x0, y, alpha=ease(p * 2))
        if ic == "agent": im = agent_top(.6)
        elif ic == "cone": im = cone_icon(96)
        elif ic == "sem": im = semaphore(3).resize((44, 116), Image.LANCZOS)
        elif ic == "sign":
            im = ss(92, 92); dd = ImageDraw.Draw(im); dd.ellipse((0, 0, 183, 183), fill=(220, 30, 40)); dd.ellipse((22, 22, 161, 161), fill=WHITE)
            ff = F(BLACK, 76); bb = ff.getbbox("50"); dd.text((92 - (bb[0] + bb[2]) / 2, 92 - (bb[1] + bb[3]) / 2), "50", font=ff, fill=DARK); im = down(im)
        else: im = marks_icon(96)
        paste(dst, im, x0 + 110, y, alpha=ease(p * 2))
        s = 46
        while F(BLACK, s).getlength(lab) > wdt - 300: s -= 2
        paste(dst, text(lab, s, NAVY if hl else DARK, BLACK, shadow=False), x0 + 180 + F(BLACK, s).getlength(lab) / 2, y, alpha=ease(p * 2))
    if v.get("tag"): paste(dst, pill(v["tag"], 38, WHITE, BLUE), W / 2, VZ[1] - 20, alpha=ease(prog(t, .4, .3)))

# --- niebla en carretera convencional en 1ª persona (antiniebla trasera / delantera, bloque conducción eficiente y clima) ---
# vis: {"type": "niebla", "mode": "hook" | "light" | "list" | "front", "lines": [...], "cols": [...], "tag": "...", "dens": 0..1}
def fog_road(dst, t, dens=.8, curve=0.0, flow=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; hz = top + 300; vx = W / 2
    for y in range(top, hz):  # cielo gris
        k = (y - top) / (hz - top); d.line([(40, y), (W - 40, y)], fill=mix((120, 130, 146), (196, 202, 210), k) + (255,))
    d.rectangle((40, hz, W - 40, bot), fill=(70, 86, 66, 255))  # campo
    def cxu(u): return vx + curve * 520 * (1 - u) ** 2.2   # eje de la carretera (curva hacia el horizonte)
    def hw(u): return 18 + 560 * u                           # media anchura
    U = lambda u: hz + (bot - hz) * u
    us = [k / 40 for k in range(41)]
    left = [(cxu(u) - hw(u), U(u)) for u in us]; right = [(cxu(u) + hw(u), U(u)) for u in reversed(us)]
    d.polygon(left + right, fill=(58, 62, 72, 255))
    for side in (-1, 1):  # líneas de borde
        d.line([(cxu(u) + side * hw(u) * .93, U(u)) for u in us], fill=(235, 235, 235, 255), width=8, joint="curve")
    for k in range(9):  # línea central discontinua que avanza
        z = ((k / 9) + t * .5 * flow) % 1.0; z2 = min(1, z + .045)
        u1, u2 = z ** 2, z2 ** 2
        d.line([(cxu(u1), U(u1)), (cxu(u2), U(u2))], fill=(255, 255, 255, 240), width=max(3, int(16 * u2)))
    for k in range(8):  # hitos de arista con reflectante que pasan
        z = ((k / 8) + t * .5 * flow) % 1.0; u = z ** 2
        for side in (-1, 1):
            x = cxu(u) + side * hw(u) * 1.12; y = U(u); hh = 8 + 120 * u; ww = 3 + 22 * u
            d.rectangle((x - ww / 2, y - hh, x + ww / 2, y), fill=(236, 236, 236, 255))
            d.rectangle((x - ww / 2, y - hh * .82, x + ww / 2, y - hh * .68), fill=(255, 150, 0, 255) if side > 0 else (230, 40, 40, 255))
    for k in range(7):  # árboles a los lados (siluetas)
        z = ((k / 7 + .07) + t * .5 * flow) % 1.0; u = z ** 2
        for side in (-1, 1):
            x = cxu(u) + side * (hw(u) * 1.5 + 40 + 200 * u); y = U(u); r = 10 + 120 * u
            d.rectangle((x - r * .12, y - r * 1.2, x + r * .12, y), fill=(52, 46, 40, 255))
            d.ellipse((x - r, y - r * 2.6, x + r, y - r * .9), fill=(46, 70, 50, 255))
    # niebla: más densa cerca del horizonte, con bancos que se mueven
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fg)
    for y in range(top, bot, 6):
        k = clamp((y - top) / (bot - top)); a = dens * (235 * (1 - k) ** 1.2 + 40)
        fd.rectangle((40, y, W - 40, y + 6), fill=(214, 218, 224, int(clamp(a, 0, 245))))
    for k in range(7):
        yy = hz - 120 + k * 95 + 14 * math.sin(t * .8 + k); xx = ((t * 40 * (1 + k % 3) + k * 210) % (W + 600)) - 300
        fd.ellipse((xx - 420, yy, xx + 420, yy + 110), fill=(226, 230, 236, int(120 * dens)))
    lay.alpha_composite(fg.filter(ImageFilter.GaussianBlur(22)))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    return top, bot, hz, U, cxu

@lru_cache(maxsize=8)
def fog_icon(kind="rear", s=120, col=None):
    """testigo del salpicadero: trasera (ámbar, luz hacia la derecha con rayas horizontales) | delantera (verde, hacia la izquierda, rayas inclinadas)"""
    col = col or ((255, 170, 0) if kind == "rear" else (40, 200, 90))
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2; wdt = int(S * .07)
    if kind == "rear":
        d.chord((S * .06, S * .2, S * .58, S * .8), -90, 90, outline=col, width=wdt)
        d.line([(S * .32, S * .2), (S * .32, S * .8)], fill=col, width=wdt)
        for k in range(3): y = S * (.32 + k * .18); d.line([(S * .66, y), (S * .94, y)], fill=col, width=wdt)
        wav = [(S * (.8 + .05 * math.sin(k * .7)), S * (.18 + k * .052)) for k in range(13)]
    else:
        d.chord((S * .42, S * .2, S * .94, S * .8), 90, 270, outline=col, width=wdt)
        d.line([(S * .68, S * .2), (S * .68, S * .8)], fill=col, width=wdt)
        for k in range(3): y = S * (.3 + k * .18); d.line([(S * .34, y), (S * .06, y + S * .1)], fill=col, width=wdt)
        wav = [(S * (.2 + .05 * math.sin(k * .7)), S * (.18 + k * .052)) for k in range(13)]
    d.line(wav, fill=col, width=int(wdt * .8), joint="curve")
    return down(im)

def fog_car(dst, t, U, cxu, u, rearfog=True, dens=.8):
    y = U(u); x = cxu(u); sc = .12 + 1.0 * u; car = car_rear(560, (60, 66, 80))
    paste(dst, car, x, y - car.height * sc / 2, scale=sc, alpha=1 - .55 * dens)
    for sx in (-.36, .36):  # pilotos de posición
        g = hazard(110).copy(); paste(dst, red_glow(80), x + sx * 560 * sc, y - car.height * sc * .5, scale=sc * 1.6, alpha=.85)
    if rearfog:  # antiniebla trasera: una luz roja muy intensa a la izquierda del paragolpes
        pk = .85 + .15 * math.sin(t * 9)
        paste(dst, red_glow(220), x - .3 * 560 * sc, y - car.height * sc * .2, scale=sc * 2.2 * pk)

@lru_cache(maxsize=4)
def red_glow(s=200):
    im = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((s * .7, s * .85, s * 1.3, s * 1.15), fill=(255, 40, 40, 255))
    g = im.filter(ImageFilter.GaussianBlur(s * .18)); g.alpha_composite(im.filter(ImageFilter.GaussianBlur(4))); return g

def fog_dash(dst, t, top, bot, icon=None, ask=False, on=True):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); dy = bot - 130
    d.rectangle((40, dy + 40, W - 40, bot), fill=(18, 20, 26, 255))
    d.ellipse((-160, dy, W + 160, dy + 300), fill=(18, 20, 26, 255))
    d.arc((W / 2 - 300, dy + 40, W / 2 + 300, dy + 640), 200, 340, fill=(36, 38, 46, 255), width=46)  # volante
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    if icon:
        blink = on and (int(t * 2.6) % 2 == 0 or not ask)
        ic = fog_icon(icon, 110) if blink else fog_icon(icon, 110, (90, 80, 60))
        paste(dst, card(190, 150, fill=(8, 10, 14, 255), r=28), W / 2 + 290, dy + 40)
        paste(dst, ic, W / 2 + 290, dy + 40)
        if ask: paste(dst, text("?", 110, YEL, BLACK), W / 2 + 420, dy + 20, scale=.9 + .1 * math.sin(t * 6))

def vis_niebla(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: niebla, coche y texto ya en pantalla
    mode = v.get("mode", "hook"); dens = v.get("dens", {"hook": .85, "light": .35, "list": .9, "front": .45}.get(mode, .7))
    curve = (.85 + .12 * math.sin(t * .9)) if mode == "front" else 0.0
    top, bot, hz, U, cxu = fog_road(dst, t, dens, curve, flow=.7)
    if mode in ("hook", "light"):
        u = lerp(.22, .36, eout(prog(t, 0, 2.0))) if mode == "hook" else .5
        fog_car(dst, t, U, cxu, u, rearfog=v.get("rearfog", mode == "hook"), dens=dens * (.6 if mode == "light" else 1))
        fog_dash(dst, t, top, bot, icon="rear", ask=(mode == "light"))
        lines = v.get("lines", [])
        if lines: big_lines(dst, lines, t, VZ[0] + 80, [tuple(c) for c in v.get("cols", [])] or None, size=118)
        if mode == "light":
            paste(dst, pill("SE VE BIEN AL DE DELANTE", 38, WHITE, BLUE), W / 2, U(.5) - 300, scale=eback(prog(t, .9, .35)), alpha=ease(prog(t, .9, .3)))
    elif mode == "list":
        dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(dark).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=(6, 20, 43, 175)); dst.alpha_composite(dark)
        hp = eback(prog(t, 0, .4))
        paste(dst, card(820, 130, fill=(8, 10, 14, 250), r=34), W / 2, top + 95, scale=.8 + .2 * hp, alpha=ease(prog(t, 0, .25)))
        paste(dst, fog_icon("rear", 96), W / 2 - 320, top + 95, alpha=ease(prog(t, 0, .25)))
        paste(dst, text("TRASERA, SOLO CON:", 50, (255, 170, 0), BLACK, shadow=False), W / 2 + 50, top + 95, alpha=ease(prog(t, .1, .25)))
        items = [("NIEBLA", "ESPESA", "fog"), ("LLUVIA", "MUY INTENSA", "rain"), ("NEVADA", "FUERTE", "snow"), ("POLVO O", "HUMO DENSO", "smoke")]
        at = v.get("at", [0.2, 0.9, 1.6, 2.3])
        for k, (l1, l2, ic) in enumerate(items):
            p = eback(prog(t, at[k], .4)); a = ease(prog(t, at[k], .25)); cx = W / 2 - 195 + (k % 2) * 390; cy = top + 330 + (k // 2) * 330
            if a < .02: continue
            paste(dst, card(360, 300, fill=(255, 255, 255, 250), r=34), cx, cy + (1 - p) * 90, alpha=a)
            paste(dst, weather_icon(ic, int(t * 6) % 3), cx, cy - 50 + (1 - p) * 90, alpha=a)
            paste(dst, text(l1, 40, DARK, BLACK, shadow=False), cx, cy + 62 + (1 - p) * 90, alpha=a)
            paste(dst, text(l2, 34, (200, 110, 0), XB, shadow=False), cx, cy + 106 + (1 - p) * 90, alpha=a)
        if v.get("tag"): paste(dst, pill(v["tag"], 32, WHITE, BLUE), W / 2, bot - 60, alpha=ease(prog(t, 2.6, .3)))
    elif mode == "front":
        # haces de las antinieblas delanteras: anchos y bajos, pegados al asfalto
        beam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam)
        a = int(190 * ease(prog(t, .2, .5)))
        for side in (-1, 1):
            bx = W / 2 + side * 260
            bd.polygon([(bx, bot - 120), (cxu(.45) + side * 430, U(.45)), (cxu(.45) + side * 40, U(.45))], fill=(255, 244, 200, a))
        dst.alpha_composite(beam.filter(ImageFilter.GaussianBlur(30)))
        # paneles de curva (flechas) en el exterior de la curva
        cdir = 1 if curve >= 0 else -1; d = ImageDraw.Draw(dst, "RGBA")
        for k in range(3):
            u = .22 + k * .09; x = cxu(u) + cdir * -1 * (18 + 560 * u) * 1.25; y = U(u) - 40 - 40 * u; s = 30 + 90 * u
            d.rectangle((x - s, y - s * .6, x + s, y + s * .6), fill=(30, 60, 160, 255))
            for j in range(2):
                ox = x - s * .5 + j * s * .6
                d.line([(ox - cdir * s * .2, y - s * .4), (ox + cdir * s * .2, y), (ox - cdir * s * .2, y + s * .4)], fill=WHITE + (255,), width=max(3, int(s * .16)))
        fog_dash(dst, t, top, bot, icon="front", on=True)
        if v.get("tag"):
            tl = v["tag"] if isinstance(v["tag"], list) else [v["tag"]]
            for k, l in enumerate(tl):
                paste(dst, pill(l, 40, (40, 200, 90), WHITE), W / 2, top + 70 + k * 84, scale=eback(prog(t, .4 + k * .4, .35)), alpha=ease(prog(t, .4 + k * .4, .3)))

@lru_cache(maxsize=16)
def weather_icon(kind, ph=0, s=170):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2
    cloud = (150, 160, 176)
    if kind == "fog":
        for k in range(4):
            y = S * (.2 + k * .19); off = (ph + k) % 3 * S * .04
            d.rounded_rectangle((S * .08 + off, y, S * .92 - (S * .08 - off), y + S * .09), radius=int(S * .045), fill=(160, 168, 182))
    else:
        d.ellipse((S * .1, S * .2, S * .55, S * .6), fill=cloud); d.ellipse((S * .35, S * .1, S * .9, S * .6), fill=cloud)
        d.rounded_rectangle((S * .1, S * .38, S * .9, S * .6), radius=int(S * .1), fill=cloud)
        if kind == "rain":
            for k in range(7):
                x = S * (.16 + k * .11); y = S * (.66 + ((k + ph) % 3) * .05)
                d.line([(x, y), (x - S * .05, y + S * .16)], fill=(40, 120, 255), width=int(S * .045))
        elif kind == "snow":
            for k in range(5):
                x = S * (.2 + k * .15); y = S * (.72 + ((k + ph) % 2) * .1); r = S * .05
                for a in range(3):
                    ang = a * math.pi / 3; d.line([(x - r * math.cos(ang), y - r * math.sin(ang)), (x + r * math.cos(ang), y + r * math.sin(ang))], fill=(90, 170, 255), width=int(S * .025))
        else:  # polvo o humo: nubes oscuras que suben
            d.rectangle((0, 0, S, S * .62), fill=(0, 0, 0, 0))
            for k in range(4):
                r = S * (.14 + k * .03); x = S * (.25 + k * .17); y = S * (.75 - k * .12 - ph * .02)
                d.ellipse((x - r, y - r, x + r, y + r), fill=(110, 104, 98) if k % 2 else (150, 136, 116))
    return down(im)

# --- carretera de montaña estrecha vista de lado y desde arriba (¿QUIÉN PASA PRIMERO? parte 7: gran pendiente) ---
# vis: {"type": "cuesta", "mode": "side" | "grade" | "bay" | "flat", "narrow": bool, "countdown": [...], "move": [at, dur],
#       "rank": true, "rank_at": t, "tag": "...", "nosigns": bool}
@lru_cache(maxsize=None)
def car_side(col=(226, 69, 60), w=250, flip=False):
    h = int(w * .5); im = ss(w, h); d = ImageDraw.Draw(im); X, Y = w * 2, h * 2
    dk = mix(col, (0, 0, 0), .3)
    d.polygon([(X * .24, Y * .42), (X * .36, Y * .08), (X * .7, Y * .08), (X * .84, Y * .42)], fill=dk)          # cabina
    d.polygon([(X * .3, Y * .4), (X * .39, Y * .15), (X * .52, Y * .15), (X * .52, Y * .4)], fill=(150, 190, 230))   # ventana trasera
    d.polygon([(X * .56, Y * .4), (X * .56, Y * .15), (X * .68, Y * .15), (X * .78, Y * .4)], fill=(150, 190, 230))  # ventana delantera
    d.rounded_rectangle((X * .02, Y * .38, X * .98, Y * .78), radius=int(Y * .16), fill=col)                   # carrocería
    d.rounded_rectangle((X * .9, Y * .46, X * .98, Y * .56), radius=8, fill=(255, 240, 190))                  # faro (delante = derecha)
    d.rounded_rectangle((X * .02, Y * .46, X * .07, Y * .58), radius=8, fill=(200, 30, 30))                    # piloto
    for x0 in (.24, .76):
        d.ellipse((X * x0 - Y * .2, Y * .58, X * x0 + Y * .2, Y * .98), fill=(20, 20, 24)); d.ellipse((X * x0 - Y * .09, Y * .69, X * x0 + Y * .09, Y * .87), fill=(160, 166, 178))
    im = down(im)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im

SIDE = ((90, 1100), (930, 590))   # extremos del eje de la carretera en vista lateral (abajo-izquierda → arriba-derecha)
def side_pt(s):
    (x0, y0), (x1, y1) = SIDE; return lerp(x0, x1, s), lerp(y0, y1, s)
SIDE_ANG = math.degrees(math.atan2(SIDE[0][1] - SIDE[1][1], SIDE[1][0] - SIDE[0][0]))

def side_scene(dst, t, narrow=False):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20
    for y in range(top, bot):  # cielo
        k = (y - top) / (bot - top); d.line([(40, y), (W - 40, y)], fill=mix((120, 180, 240), (210, 230, 250), k) + (255,))
    d.polygon([(40, top + 330), (240, top + 150), (420, top + 280), (640, top + 90), (860, top + 240), (W - 40, top + 160), (W - 40, bot), (40, bot)], fill=(150, 160, 190, 255))  # montañas lejanas
    d.polygon([(560, top + 150), (640, top + 90), (700, top + 135), (660, top + 150), (620, top + 128)], fill=(245, 248, 252, 255))     # nieve en la cima
    (x0, y0), (x1, y1) = SIDE; nx, ny = -math.sin(math.radians(SIDE_ANG)), -math.cos(math.radians(SIDE_ANG))
    # ladera de roca por encima de la carretera
    d.polygon([(x0 - 200, y0 - 70), (x1 + 200, y1 - 70 - 104), (W - 40, top + 250), (W - 40, top + 200), (700, y1 - 150), (300, y0 - 260), (40, y0 - 240)], fill=(122, 104, 88, 255))
    for k in range(12):
        s = k / 11; px, py = side_pt(s); d.ellipse((px - 40, py - 150 - 30 * (k % 3), px + 30, py - 90 - 30 * (k % 3)), fill=(104, 88, 74, 255))
    # terraplén y barranco por debajo
    d.polygon([(40, y0 + 18), (x1 + 100, y1 + 18 - 52), (W - 40, y1 - 30), (W - 40, bot), (40, bot)], fill=(84, 112, 70, 255))
    for k in range(9):
        s = k / 8; px, py = side_pt(s); d.ellipse((px - 30, py + 70, px + 50, py + 140), fill=(64, 94, 58, 255))
    # calzada (banda gruesa) y quitamiedos
    th = 34
    d.polygon([(x0 - 60, y0 + 31), (x1 + 60, y1 - 31), (x1 + 60, y1 - 31 + th), (x0 - 60, y0 + 31 + th)], fill=(46, 50, 60, 255))
    d.line([(x0 - 60, y0 + 31), (x1 + 60, y1 - 31)], fill=(70, 74, 86, 255), width=6)
    for k in range(15):  # bionda en el borde del barranco (por debajo de la calzada)
        s = k / 14; px, py = side_pt(s); d.line([(px, py + 34 + th), (px, py + 4 + th)], fill=(170, 176, 186, 255), width=7)
    d.line([(x0 - 60, y0 + 31 + th + 4), (x1 + 60, y1 - 31 + th + 4)], fill=(200, 206, 216, 255), width=8)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    if narrow:  # tramo estrecho: contorno naranja discontinuo que parpadea
        a = int(255 * (.55 + .45 * math.sin(t * 6)))
        (ax, ay), (bx, by) = side_pt(.38), side_pt(.62); dd = ImageDraw.Draw(dst, "RGBA")
        pts = [(ax, ay - 130), (bx, by - 130), (bx, by + 70), (ax, ay + 70)]
        for k in range(4):
            p0, p1 = pts[k], pts[(k + 1) % 4]
            for j in range(10):
                if j % 2: continue
                q0, q1 = j / 10, (j + 1) / 10
                dd.line([(lerp(p0[0], p1[0], q0), lerp(p0[1], p1[1], q0)), (lerp(p0[0], p1[0], q1), lerp(p0[1], p1[1], q1))], fill=ORANGE + (a,), width=10)
    return top, bot

def side_car(dst, s, n, col, flip, t=0, still=False):
    px, py = side_pt(s); car = car_side(col, 250, flip); a = math.radians(SIDE_ANG)
    cx = px - math.sin(a) * (car.height / 2 - 4); cy = py - math.cos(a) * (car.height / 2 - 4)
    bob = 0 if still else math.sin(t * 9 + n) * 1.5
    paste(dst, car, cx, cy + bob, rot=SIDE_ANG)
    paste(dst, num_badge(n, 80), cx, cy - 120)
    return cx, cy

def vis_cuesta(dst, t, v, i):
    if i == 0: t = t + 0.6  # primer fotograma: montaña, coches y números ya en pantalla
    mode = v.get("mode", "side")
    if mode in ("side", "grade"):
        top, bot = side_scene(dst, t, v.get("narrow", False))
        mv = v.get("move"); s2 = .16; s1 = .84
        if mv: s2 = lerp(.16, .64, ease(prog(t, mv[0], mv[1])))
        elif not v.get("still"): s2 = .16 + .015 * math.sin(t * 2); s1 = .84 - .015 * math.sin(t * 2)
        if mode == "grade": c1 = c2 = (0, 0)
        else:
            c2 = side_car(dst, s2, 2, CRUCE_COLS[2], False, t, still=bool(mv) and t > mv[0] + mv[1])
            c1 = side_car(dst, s1, 1, CRUCE_COLS[1], True, t, still=bool(mv))
        if not mv and mode == "side":  # flechas de sentido
            d = ImageDraw.Draw(dst, "RGBA"); al = int(255 * ease(prog(t, .2, .3)))
            paste(dst, pill("SUBE ↗", 34, WHITE, NAVY), c2[0] + 40, c2[1] + 150, alpha=al / 255)
            paste(dst, pill("↙ BAJA", 34, WHITE, NAVY), c1[0] - 20, c1[1] + 150, alpha=al / 255)
        if v.get("nosigns"):
            for k, (ix, iy) in enumerate(((190, top + 140), (380, top + 140))):
                p = prog(t, .2 + k * .3, .35); im = sign_ceda(150) if k == 0 else stop_mini(150)
                paste(dst, im, ix, iy, scale=.6 + .4 * eback(p), alpha=ease(p * 2))
                if t > .55 + k * .3: paste(dst, icon_x(100), ix + 55, iy + 60, scale=eback(prog(t, .55 + k * .3, .3)))
        if mv and v.get("rank"):
            ra = v.get("rank_at", mv[0] + mv[1])
            p = prog(t, ra, .35)
            if p > 0:
                paste(dst, pill("1º", 52, YEL, NAVY, padx=26), c2[0], c2[1] - 210, scale=eback(p), alpha=ease(p * 2))
                paste(dst, pill("ESPERA", 36, NAVY, WHITE), c1[0], c1[1] - 210, scale=eback(prog(t, ra + .3, .35)), alpha=ease(prog(t, ra + .3, .3)))
        cd = v.get("countdown")
        if cd:
            n = sum(1 for s in cd if t >= s); ix, iy = 150, top + 200
            paste(dst, semaphore(n).resize((115, 300), Image.LANCZOS), ix, iy, scale=eback(prog(t, 0, .4)))
            if n:
                pk = prog(t, cd[n - 1], .25)
                paste(dst, text(str(4 - n), 190, [RED, (255, 176, 0), GREEN][n - 1], BLACK), 290, iy, scale=lerp(1.6, 1, eout(pk)), alpha=ease(pk * 2))
        if mode == "grade":
            dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(dark).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=(6, 20, 43, 150)); dst.alpha_composite(dark)
            p = eback(prog(t, 0, .45)); cy = CY + 10
            paste(dst, card(860, 560, fill=(255, 255, 255, 250), r=40), W / 2, cy + (1 - p) * 120, alpha=ease(prog(t, 0, .25)))
            d = ImageDraw.Draw(dst, "RGBA"); k = ease(prog(t, .3, .9)); al = int(255 * ease(prog(t, .2, .3)))
            ax, ay = W / 2 - 330, cy + 170; bx = W / 2 + 330; by = ay - 210 * k
            d.polygon([(ax, ay), (bx, ay), (bx, by)], fill=(255, 196, 0, int(al * .35)))
            d.line([(ax, ay), (bx, ay)], fill=DARK + (al,), width=8); d.line([(bx, ay), (bx, by)], fill=RED + (al,), width=10)
            d.line([(ax, ay), (bx, by)], fill=(46, 50, 60, al), width=22)
            paste(dst, car_side(CRUCE_COLS[2], 150), lerp(ax, bx, .55), lerp(ay, by, .55) - 44, rot=math.degrees(math.atan2(ay - by, bx - ax)), alpha=al / 255)
            paste(dst, text("100 m", 40, DARK, XB, shadow=False), W / 2, ay + 44, alpha=al / 255)
            if k > .5: paste(dst, text("7 m", 40, RED, BLACK, shadow=False), bx - 70, (ay + by) / 2 + 10, alpha=ease(prog(t, .8, .3)))
            val = 7 * eout(prog(t, .3, 1.0))
            paste(dst, text(f"≥ {int(round(val))} %", 130, BLUE, BLACK, shadow=False), W / 2 - 150, cy - 160, scale=.8 + .2 * eback(prog(t, .3, .4)))
            if v.get("tag"): paste(dst, pill(v["tag"], 38, YEL, NAVY), W / 2, top + 70, scale=eback(prog(t, 1.0, .35)), alpha=ease(prog(t, 1.0, .3)))
            return
        if v.get("tag"):
            paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, bot - 60 if v.get("tag_bottom") else top + 60, scale=eback(prog(t, .4, .4)), alpha=ease(prog(t, .4, .3)))
        return
    # vista desde arriba: carretera estrecha de montaña en vertical (el 2 sube desde abajo, el 1 baja desde arriba)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    top, bot = VZ[0] + 10, VZ[1] + 20; cx = W / 2
    flat = mode == "flat"; hw = 210 if flat else 105
    d.rectangle((40, top, W - 40, bot), fill=(84, 112, 70, 255) if flat else (118, 102, 86, 255))
    for k in range(36):  # rocas o césped
        gx, gy = 60 + (k * 263) % (W - 120), top + (k * 157) % (bot - top)
        if abs(gx - cx) < hw + 60: continue
        d.ellipse((gx - 34, gy - 22, gx + 34, gy + 22), fill=(74, 104, 68, 255) if flat else (100, 86, 72, 255))
    d.rectangle((cx - hw, top, cx + hw, bot), fill=(46, 50, 60, 255))
    bay_y = CY + 170
    if mode == "bay":  # apartadero a la derecha, cerca del que sube
        d.polygon([(cx + hw, bay_y - 190), (cx + hw + 190, bay_y - 110), (cx + hw + 190, bay_y + 110), (cx + hw, bay_y + 190)], fill=(46, 50, 60, 255))
        d.line([(cx + hw, bay_y - 190), (cx + hw + 190, bay_y - 110), (cx + hw + 190, bay_y + 110), (cx + hw, bay_y + 190)], fill=(240, 240, 240, 255), width=6)
    for side in (-1, 1):
        x = cx + side * (hw - 8)
        if mode == "bay" and side == 1:
            d.line([(x, top), (x, bay_y - 190)], fill=(240, 240, 240, 255), width=6); d.line([(x, bay_y + 190), (x, bot)], fill=(240, 240, 240, 255), width=6)
        else: d.line([(x, top), (x, bot)], fill=(240, 240, 240, 255), width=6)
    if flat:  # eje discontinuo de una carretera llana de doble sentido
        y = top + 10
        while y < bot - 40: d.line([(cx, y), (cx, y + 50)], fill=(255, 255, 255, 200), width=7); y += 95
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, top, W - 40, bot), radius=36, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(m)))); dst.alpha_composite(lay)
    if flat:
        d = ImageDraw.Draw(dst, "RGBA"); d.rectangle((cx + 10, CY - 260, cx + hw - 10, CY + 140), fill=(255, 140, 0, 70))
        for k in range(5): paste(dst, cone_icon(80), cx + 100, CY - 230 + k * 92)
        paste(dst, pill("OBRAS", 34, ORANGE, WHITE), cx + hw + 120, CY - 60)
        paste(dst, pill("LLANO", 34, WHITE, NAVY), cx - hw - 130, bot - 90)
    else:  # indicador de pendiente
        paste(dst, pill("SUBIDA ↑", 38, WHITE, NAVY), cx - hw - 200, bot - 90)
        paste(dst, pill("≥ 7 %", 38, YEL, NAVY), cx - hw - 200, bot - 180)
    if mode == "bay":
        # el 2 sube hasta el apartadero y se mete; luego baja el 1
        k1 = ease(prog(t, .1, 1.0)); k2 = ease(prog(t, 1.0, .7)); k3 = ease(prog(t, 1.6, 1.6))
        y2 = lerp(bot - 110, bay_y + 60, k1); x2 = lerp(cx, cx + hw + 95, k2); r2 = -30 * math.sin(k2 * math.pi)
        paste(dst, car_top(CRUCE_COLS[2], 120), x2, y2, rot=r2); paste(dst, num_badge(2, 70), x2 + (90 if k2 < .5 else 120), y2)
        y1 = lerp(top + 120, bot + 200, k3)
        paste(dst, car_top(CRUCE_COLS[1], 120), cx, y1, rot=180); paste(dst, num_badge(1, 70), cx - 110, y1)
        ap = prog(t, .2, .4)
        paste(dst, pill("APARTADERO", 36, YEL, NAVY), cx + hw + 95, bay_y - 250, scale=eback(ap), alpha=ease(ap * 2))
        if k2 > .9: paste(dst, pill("SE APARTA EL QUE SUBE", 38, GREEN, WHITE), W / 2, top + 60, scale=eback(prog(t, 1.6, .35)), alpha=ease(prog(t, 1.6, .3)))
    elif mode == "flat":
        # el 1 ya está dentro del estrechamiento y sigue; el 2 espera en la entrada
        k3 = ease(prog(t, .6, 2.2)); y1 = lerp(CY - 120, bot + 200, k3); x1 = cx - 95
        paste(dst, car_top(CRUCE_COLS[1], 120), x1, y1, rot=180); paste(dst, num_badge(1, 70), x1 - 110, y1)
        if t < 1.7: paste(dst, pill("ENTRÓ PRIMERO", 34, GREEN, WHITE), x1 - 10, y1 - 200, alpha=ease(prog(t, .1, .3)) * (1 - prog(t, 1.4, .3)))
        k4 = ease(prog(t, 2.4, 1.2)); y2 = lerp(CY + 330, CY - 330, k4) + (4 * math.sin(t * 3) if k4 == 0 else 0)
        x2 = cx + 95 - 190 * math.sin(clamp((CY + 200 - y2) / 500) * math.pi) if k4 > 0 else cx + 95
        paste(dst, car_top(CRUCE_COLS[2], 120), x2, y2); paste(dst, num_badge(2, 70), x2 + 110, y2)
        if k4 == 0: paste(dst, pill("ESPERA", 34, NAVY, WHITE), cx + 95, y2 + 200, alpha=ease(prog(t, .5, .3)))
    if v.get("tag"):
        paste(dst, pill(v["tag"], 40, YEL, NAVY), W / 2, top + 60 if mode != "bay" else top + 140, scale=eback(prog(t, .3, .4)), alpha=ease(prog(t, .3, .3)))

@lru_cache(maxsize=4)
def stop_mini(s=150):
    im = ss(s, s); d = ImageDraw.Draw(im); S = s * 2; r = S / 2
    pts = [(r + r * .96 * math.cos(math.radians(22.5 + 45 * k)), r + r * .96 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    d.polygon(pts, fill=(220, 30, 40)); f = F(BLACK, int(S * .3)); bb = f.getbbox("STOP")
    d.text((r - (bb[0] + bb[2]) / 2, r - (bb[1] + bb[3]) / 2), "STOP", font=f, fill=WHITE); return down(im)


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
    if kind == "siren":  # dos tonos alternos (ni-no ni-no), suave
        seg = []
        for k in range(4):
            f = 660 if k % 2 == 0 else 880; tt = np.arange(int(sr * .32)) / sr
            seg.append((np.sin(2 * np.pi * f * tt) * .07 * np.minimum(1, tt * 40) * np.minimum(1, (.32 - tt) * 40)).astype(np.float32))
        return np.concatenate(seg)
    if kind == "notif":  # aviso de mensaje del móvil (dos notas cortas) + vibración
        t = np.arange(int(sr * .3)) / sr; vib = (np.sign(np.sin(2 * np.pi * 90 * t)) * .05 * np.exp(-t * 6)).astype(np.float32)
        return np.concatenate([tone(1318, .09, sr, .2, 10), tone(1760, .2, sr, .2, 9), vib])
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
