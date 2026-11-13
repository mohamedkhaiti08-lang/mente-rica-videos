# Piezas reutilizables del estilo Noche (importables sin efectos secundarios).
# Uso típico en un script de historia:
#   sys.path.insert(0, "historias-islam/plantilla/noche"); import piezas as Z; from noche import ...
#   starts, dur = Z.voz(lineas, pausas, "voz.wav", sfx=[...], guion="x.guion.json")
#   Z.render(frame_fn, dur, "voz.wav", "salida.mp4")   |   Z.fotogramas(frame_fn, [0, 5, 12], "pref")
import json, math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import noche as N
from noche import S, W, H, GY, LX, RX, CREAM, GOLD, seg, lerp, P, star8, canopy, spaced

FPS = N.FPS
KOKORO_DIR = os.environ.get("KOKORO_DIR", "/home/claude/kok")
SHADOW = (66, 60, 82)

# ---------------- base y composición ----------------
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

def new_layer():
    """Capa extra SIN halo turquesa (para sombras, niebla oscura...). Se pasa a finish(..., over=)."""
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); return lay, ImageDraw.Draw(lay)

def finish(base, fg, glow, bright, over=None, under=None):
    out = base.copy()
    if under is not None:                        # debajo de todo (sin halo)
        u = np.asarray(under.resize((W, H), Image.BILINEAR)).astype(np.float32); ua = u[..., 3:4] / 255
        out = out * (1 - ua) + u[..., :3] * ua
    fg1 = fg.resize((W, H), Image.LANCZOS)
    a = np.asarray(fg1)[..., 3].astype(np.float32)
    halo = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    halo = np.asarray(halo).astype(np.float32)[..., None] / 255 * np.array([90, 200, 200]) * (0.35 + 0.4 * bright)
    gl = glow.filter(ImageFilter.GaussianBlur(28)); ga = np.asarray(gl).astype(np.float32)
    out = out + halo + ga[..., :3] * (ga[..., 3:4] / 255)
    f = np.asarray(fg1).astype(np.float32); fa = f[..., 3:4] / 255
    out = out * (1 - fa) + f[..., :3] * fa
    if over is not None:
        o = np.asarray(over.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))).astype(np.float32); oa = o[..., 3:4] / 255
        out = out * (1 - oa) + o[..., :3] * oa
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------------- textos ----------------
def fit(text, size, maxw=800, track=0.32):
    """Reduce el tamaño para que el texto quepa en maxw px (zona segura)."""
    n = len(text)
    while size > 20 and (n * 0.602 * size + (n - 1) * track * size) > maxw: size -= 1
    return size

def labels(d, t, la, l1, l2, t10, t30, size=46, lx=LX, rx=RX, days=("DÍA 1", "DÍA 10", "DÍA 30")):
    s = min(fit(l1, size, 420), fit(l2, size, 2 * (930 - rx) - 10))
    spaced(d, l1, lx, 330, s, la); spaced(d, l2, rx, 330, s, la)
    day = days[0] if t < t10 else (days[1] if t < t30 else days[2])
    pulse = 1 + 0.25 * max(0, 1 - abs(t - t10) * 3) + 0.25 * max(0, 1 - abs(t - t30) * 3)
    for x_ in (lx, rx): spaced(d, day, x_, 400, int(38 * pulse), la * 0.8, col=(200, 225, 222))

def subs(d, t, lst, y=540):
    for a, b, txt in lst:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b))
        if al > 0: spaced(d, txt, W / 2, y, fit(txt, 40, 760, 0.22), al, bold=False, track=0.22, col=(190, 225, 222))

def pregunta(d, t, a, b, txt):
    if a <= t < b:
        al = 255 * seg(t, a, a + 0.3) * (1 - seg(t, b - 0.3, b)); sc = 1 + 0.05 * math.sin((t - a) * 6)
        spaced(d, txt, W / 2, 560, int(fit(txt, 52, 760) * sc), al)

def fuente(d, t, a, b, lineas, ref):
    if a <= t < b:
        al = 255 * seg(t, a, a + 0.5) * (1 - seg(t, b - 0.4, b))
        s = min(fit(l, 50, 760) for l in lineas)
        for i, ln in enumerate(lineas):
            spaced(d, ln, W / 2, 330 + 70 * i, s, al * seg(t, a + 0.7 * i, a + 0.7 * i + 0.5))
        spaced(d, ref, W / 2, 330 + 70 * len(lineas) + 20, 32, al * 0.85 * seg(t, a + 2.6, a + 3.1), bold=False, col=(190, 225, 222))

def final(d, t, a, l1, l2, ask_t, ask1, ask2):
    if t >= a:
        al = 255 * seg(t, a, a + 0.4)
        spaced(d, l1, W / 2, 360, fit(l1, 62, 760), al); spaced(d, l2, W / 2, 440, fit(l2, 50, 760), al * seg(t, a + 0.5, a + 0.9))
    if t >= ask_t:
        al = 255 * seg(t, ask_t, ask_t + 0.4)
        s = min(fit(ask1, 40, 760, 0.22), fit(ask2, 40, 760, 0.22))
        spaced(d, ask1, W / 2, 540, s, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, ask2, W / 2, 595, s, al, bold=False, track=0.22, col=(190, 235, 230))
        spaced(d, "COMENTA ↓", W / 2, 655, 34, al * (0.6 + 0.4 * math.sin(t * 5)), track=0.25, col=(120, 230, 225))

# ---------------- objetos ----------------
def roots(d, rg, x0=880, col=CREAM):
    dx = x0 - 880
    if rg > 0: d.ellipse([(x0 - 16) * S, (GY + 10) * S, (x0 + 16) * S, (GY + 28) * S], fill=col + (255,))
    for a, b, c, e, tb, w_ in N.ROOTS:
        if rg > tb:
            k = min(1, (rg - tb) / 0.06)
            d.line([((a + dx) * S, b * S), ((lerp(a, c, k) + dx) * S, lerp(b, e, k) * S)], fill=col + (235,), width=int(w_ * S))

def grietas(d, x, cr, seed=5, col=(150, 50, 45)):
    if cr <= 0: return
    rnd = random.Random(seed)
    for j in range(5):
        px, py = x + rnd.uniform(-40, 40), GY + 4
        pts = [(px, py)]
        for _ in range(int(1 + 6 * cr)):
            px += rnd.uniform(-40, 40); py += rnd.uniform(25, 60); pts.append((px, py))
        d.line([(a * S, b * S) for a, b in pts], fill=col + (230,), width=4 * S)

def walk_pose(ph, amp=1.0, lift=0.0):
    """Pose de caminar (ph en radianes). lift levanta el pie adelantado (para pasar por encima de algo)."""
    s, c = math.sin(ph) * amp, math.cos(ph) * amp
    p = dict(P["stand"])
    p["lk"] = (-4 + 22 * s, -66); p["lf"] = (-6 + 46 * s, -max(0, 22 * c) - lift * max(0, s))
    p["rk"] = (4 - 22 * s, -66); p["rf"] = (6 - 46 * s, -max(0, -22 * c) - lift * max(0, -s))
    p["lh"] = (-10 - 40 * s, -150); p["rh"] = (10 + 40 * s, -150)
    p["le"] = (-10 - 22 * s, -210); p["re"] = (10 + 22 * s, -210)
    return p

def mini_figure(d, x, p, k=0.5, rot=0.0, col=CREAM, alpha=255, y0=GY):
    """Figura de palitos a escala k, girada rot rad alrededor de los pies (para gente pequeña, caídas...)."""
    c = col + (int(alpha),); cr, sr = math.cos(rot), math.sin(rot)
    def q(j):
        px, py = p[j][0] * k, p[j][1] * k
        return ((x + px * cr - py * sr) * S, (y0 + px * sr + py * cr) * S)
    w = max(3, 13 * k) * S
    for a, b in [("neck", "hip"), ("neck", "le"), ("le", "lh"), ("neck", "re"), ("re", "rh"), ("hip", "lk"), ("lk", "lf"), ("hip", "rk"), ("rk", "rf")]:
        d.line([q(a), q(b)], fill=c, width=int(w))
        for pt in (q(a), q(b)): d.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=c)
    hx, hy = q("head"); r = 34 * k * S
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=c)

def casa(d, x0, x1, wall_h=390, roof_h=150, door=None, door_open=0.0, col=CREAM, alpha=255):
    """Casa de líneas. door=('l'|'r', alto). door_open 0..1 abre la puerta hacia fuera."""
    c = col + (int(alpha),); w = 6 * S; top = GY - wall_h; cx = (x0 + x1) / 2
    d.line([((x0 - 25) * S, top * S), (cx * S, (top - roof_h) * S), ((x1 + 25) * S, top * S)], fill=c, width=w, joint="curve")
    d.line([((x0 - 25) * S, top * S), ((x1 + 25) * S, top * S)], fill=c, width=w)
    for xs, side in ((x0, "l"), (x1, "r")):
        if door and door[0] == side:
            dh = door[1]
            d.line([(xs * S, top * S), (xs * S, (GY - dh) * S)], fill=c, width=w)
            d.line([((xs - 4) * S, (GY - dh) * S), ((xs + 4) * S, (GY - dh) * S)], fill=c, width=w)
            sg = 1 if side == "r" else -1                     # hoja de la puerta
            ang = door_open * 1.25
            ex = xs + sg * math.sin(ang) * 70; ey_off = math.cos(ang) * 0
            d.line([(xs * S, GY * S), (ex * S, GY * S)], fill=c, width=int(3 * S)) if door_open > 0.05 else None
            pts = [(xs, GY - dh), (ex, GY - dh + 14 * door_open), (ex, GY - 2), (xs, GY - 2)]
            if door_open > 0.05:
                d.polygon([(a * S, b * S) for a, b in pts], outline=c, width=int(4 * S))
            else:
                d.line([(xs * S, (GY - dh) * S), (xs * S, GY * S)], fill=c, width=w)
                d.ellipse([(xs - sg * 18 - 6) * S, (GY - dh / 2 - 6) * S, (xs - sg * 18 + 6) * S, (GY - dh / 2 + 6) * S], fill=c)
        else:
            d.line([(xs * S, top * S), (xs * S, GY * S)], fill=c, width=w)

def mesa(d, cx, half=70, h=120, col=CREAM, alpha=255):
    c = col + (int(alpha),)
    d.line([((cx - half) * S, (GY - h) * S), ((cx + half) * S, (GY - h) * S)], fill=c, width=8 * S)
    for sx in (-1, 1): d.line([((cx + sx * (half - 14)) * S, (GY - h) * S), ((cx + sx * (half - 22)) * S, GY * S)], fill=c, width=6 * S)

def plato(d, g, cx, nivel, h=120, gris=0.0, vapor=0.0, t=0.0, luz=0.0):
    """Plato con comida (nivel 0..1). gris apaga la comida; vapor y luz para el plato bendecido."""
    y = GY - h - 4
    food = tuple(int(lerp(a, b, gris)) for a, b in zip(GOLD, (95, 92, 96)))
    if nivel > 0.02:
        r = 42 * (0.35 + 0.65 * nivel); hh = 40 * nivel
        d.chord([(cx - r) * S, (y - hh) * S, (cx + r) * S, (y + hh) * S], 180, 360, fill=food + (255,))
    d.ellipse([(cx - 52) * S, (y - 9) * S, (cx + 52) * S, (y + 7) * S], fill=CREAM + (255,))
    for i in range(3):
        if vapor <= 0: break
        ph = (t * 0.6 + i / 3) % 1
        xs = cx - 22 + i * 22; ys = y - 46 - ph * 90
        pts = [((xs + 9 * math.sin(ph * 9 + k_ * 0.8)) * S, (ys - k_ * 8) * S) for k_ in range(5)]
        d.line(pts, fill=CREAM + (int(170 * vapor * (1 - ph)),), width=4 * S)
    if luz > 0:
        g.ellipse([cx - 80, y - 90, cx + 80, y + 40], fill=(250, 220, 140, int(140 * luz)))

def sombra(d, x, k, alpha, t, reach=0.0, col=SHADOW, y0=GY):
    """Silueta de humo oscura (lo que no se ve). Dibujar en una capa de new_layer(). reach 0..1 estira el brazo a la izquierda."""
    if alpha <= 0 or k <= 0: return
    rnd = random.Random(11)
    a = int(alpha)
    blobs = [(0, -60, 70, 60), (-6, -150, 58, 70), (-14, -235, 42, 42), (10, -30, 80, 34)]
    for bx, by, rx, ry in blobs:
        jx = 4 * math.sin(t * 3 + by); jy = 3 * math.cos(t * 2.3 + bx)
        d.ellipse([(x + (bx + jx - rx) * k) * S, (y0 + (by + jy - ry) * k) * S, (x + (bx + jx + rx) * k) * S, (y0 + (by + jy + ry) * k) * S], fill=col + (a,))
    for i in range(7):                                   # humo que sube
        ph = (t * 0.5 + i / 7) % 1
        px = x + (rnd.uniform(-40, 40) + 14 * math.sin(t * 2 + i)) * k; py = y0 + (-260 - ph * 120) * k
        r = (16 + 10 * ph) * k
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=col + (int(a * 0.7 * (1 - ph)),))
    if reach > 0:
        hx = x - (40 + 70 * reach) * k; hy = y0 - (150 - 30 * reach) * k
        d.line([((x - 20 * k) * S, (y0 - 170 * k) * S), (hx * S, hy * S)], fill=col + (a,), width=int(22 * k * S))
        d.ellipse([(hx - 14 * k) * S, (hy - 14 * k) * S, (hx + 14 * k) * S, (hy + 14 * k) * S], fill=col + (a,))

def rama(d, cx, y, ang=0.0, alpha=255, k=1.0, col=CREAM):
    """Rama con espinas (unos 170 px), centrada en (cx, y) y girada ang rad."""
    c = col + (int(alpha),); ca, sa = math.cos(ang), math.sin(ang)
    def tr(px, py): return ((cx + (px * ca - py * sa) * k) * S, (y + (px * sa + py * ca) * k) * S)
    d.line([tr(-85, 0), tr(-30, -4), tr(20, 2), tr(85, -6)], fill=c, width=int(9 * k * S), joint="curve")
    d.line([tr(10, 0), tr(45, -30), tr(60, -42)], fill=c, width=int(6 * k * S))
    d.line([tr(-40, -2), tr(-62, -30)], fill=c, width=int(5 * k * S))
    th = (200, 70, 60, int(alpha))
    for px, sg in [(-70, -1), (-50, 1), (-20, -1), (0, 1), (30, -1), (55, 1), (75, -1), (40, -1)]:
        d.polygon([tr(px - 6, 0), tr(px + 6, 0), tr(px, sg * 22)], fill=th)
    d.ellipse([tr(56, -50)[0] - 10 * S, tr(56, -50)[1] - 6 * S, tr(56, -50)[0] + 10 * S, tr(56, -50)[1] + 6 * S], fill=c)

def gota(d, g, x, y, r=9, col=(140, 245, 238), alpha=255):
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=col + (int(alpha),))
    g.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (int(120 * alpha / 255),))

def anillos(d, x, y, t, t0, dur, col=(120, 230, 225), rmax=160):
    if t0 <= t < t0 + dur:
        for k_ in range(2):
            ph = ((t - t0) * 0.8 + k_ * 0.5) % 1; r = 40 + rmax * ph
            d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], outline=col + (int(200 * (1 - ph)),), width=3 * S)

# ---------------- voz y render ----------------
def voz(lines, pausas, wav, sfx_fn=None, guion=None, t0=0.3, speed=1.0):
    """Genera la voz em_alex con pausas; devuelve (starts, dur). Escribe también un guion.json compatible con audio.py."""
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(KOKORO_DIR, "kokoro-v1.0.onnx"), os.path.join(KOKORO_DIR, "voices-v1.0.bin"))
    sr = 24000; clips = []
    for ln in lines:
        a, sr = k.create(ln, voice="em_alex", speed=speed, lang="es")
        idx = np.where(np.abs(a) > 0.01)[0]; clips.append(a[max(0, idx[0] - 240): idx[-1] + 480])
    starts, t = [], t0
    for c, p in zip(clips, pausas): starts.append(round(t, 2)); t += len(c) / sr + p
    dur = round(t + 0.6, 2)
    out = np.zeros(int(sr * dur), np.float32)
    for c, s in zip(clips, starts): out[int(s * sr): int(s * sr) + len(c)] += c
    sfx = sfx_fn(starts) if sfx_fn else []
    for s_ in sfx:
        n = int(s_["dur"] * sr); x = np.arange(n) / sr; f = s_["f"]; v = s_["v"]
        w = v * np.sin(2 * np.pi * f * x) * np.exp(-x * 3.5) + v * 0.4 * np.sin(4 * np.pi * f * x) * np.exp(-x * 5)
        i = int(s_["t"] * sr); out[i:i + n] += w[:len(out) - i]
    sf.write(wav, np.clip(out, -1, 1), sr)
    ends = [round(s + len(c) / sr, 2) for s, c in zip(starts, clips)]
    if guion:
        json.dump(dict(lines=lines, starts=starts, ends=ends, duration=dur, sfx=sfx), open(guion, "w"), ensure_ascii=False, indent=1)
    return starts, ends, dur

def _render_part(args):
    frame_fn, i0, i1, path = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame_fn(i / FPS).tobytes())
    p.stdin.close(); p.wait(); return path

def render(frame_fn, dur, wav, out, workers=None):
    """Renderiza en paralelo por tramos (fork), une los tramos y añade la voz (AAC 128k)."""
    import multiprocessing as mp
    n = int(dur * FPS); workers = workers or max(1, os.cpu_count() or 1)
    cuts = [round(n * k / workers) for k in range(workers + 1)]
    parts = [(frame_fn, cuts[k], cuts[k + 1], f"{out}.part{k}.mp4") for k in range(workers)]
    with mp.get_context("fork").Pool(workers) as pool: paths = pool.map(_render_part, parts)
    lst = out + ".txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(q)}'\n" for q in paths))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", out], check=True)
    for q in paths + [lst]: os.remove(q)

def fotogramas(frame_fn, ts, pref):
    for tt in ts: Image.fromarray(frame_fn(float(tt))).save(f"{pref}_{tt}.png")

def flor(d, fx, h, col=(255, 245, 230)):
    """Flor que crece desde el suelo hasta altura h."""
    if h <= 2: return
    d.line([(fx * S, GY * S), (fx * S, (GY - h) * S)], fill=(150, 230, 170, 255), width=4 * S)
    for a in range(5):
        ang = a * 2 * math.pi / 5
        d.ellipse([(fx + 11 * math.cos(ang) - 8) * S, (GY - h + 11 * math.sin(ang) - 8) * S, (fx + 11 * math.cos(ang) + 8) * S, (GY - h + 11 * math.sin(ang) + 8) * S], fill=col + (255,))
    d.ellipse([(fx - 6) * S, (GY - h - 6) * S, (fx + 6) * S, (GY - h + 6) * S], fill=GOLD + (255,))

def camino_luz(d, g, x0, x1, k, col=(130, 240, 232)):
    """La línea del suelo se vuelve de luz de x0 a x1 (k 0..1)."""
    if k <= 0: return
    xe = lerp(x0, x1, k)
    d.line([(x0 * S, GY * S), (xe * S, GY * S)], fill=col + (255,), width=6 * S)
    g.rectangle([x0, GY - 14, xe, GY + 14], fill=col + (170,))
