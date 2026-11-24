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

# ---------------- piezas del 15 nov 2026 (ballena, mar, nube, dua que sube, montaña de bloques, postración) ----------------

def spline(pts, n=10):
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        for k in range(n):
            u = k / n; u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    out.append(pts[-1]); return out

def ballena(d, cx, cy, k, boca, alpha, t):
    """Ballena de líneas (mira a la izquierda). boca 0..1 abre la mandíbula."""
    if alpha <= 0: return
    c = CREAM + (int(alpha),); sw = 5 * S
    wob = 6 * math.sin(t * 1.6)
    top = [(-215, -5), (-170, -70), (-60, -105), (80, -92), (190, -48), (250, -16 + wob * 0.3)]
    tail = [(250, -16 + wob * 0.3), (300, -78 + wob), (292, -14), (318, 40 + wob), (250, 14)]
    bot = [(250, 14), (170, 52), (40, 82), (-110, 70), (-185, 38), (-215, 18 + 36 * boca)]
    q = lambda pts: [((cx + x * k) * S, (cy + y * k) * S) for x, y in pts]
    body = spline(top) + spline(bot)
    d.polygon(q(body), fill=(14, 30, 40, int(alpha * 0.92)))
    d.line(q(spline(top)), fill=c, width=sw, joint="curve"); d.line(q(spline(bot)), fill=c, width=sw, joint="curve")
    d.line(q(tail), fill=c, width=sw, joint="curve")
    d.line(q([(-215, -5), (-150, 8 + 10 * boca)]), fill=c, width=int(3 * S))          # línea de la boca
    ex, ey = cx - 150 * k, cy - 40 * k
    d.ellipse([(ex - 7) * S, (ey - 7) * S, (ex + 7) * S, (ey + 7) * S], fill=c)
    for i in range(3):                                                              # surcos de la tripa
        x0 = -120 + i * 30
        d.line(q([(x0, 52 - i * 2), (x0 + 60, 66 - i * 3)]), fill=CREAM + (int(alpha * 0.5),), width=int(2 * S))

def mar(d, t, k, x0=0):
    """Olas debajo del suelo (k 0..1 las va dibujando)."""
    if k <= 0: return
    for i in range(8):
        y = GY + 45 + i * 58; a = int(110 * k * (1 - i * 0.07))
        pts = [((x0 + x) * S, (y + 7 * math.sin(x / 70 + t * 1.3 + i)) * S) for x in range(0, int((W - x0) * min(1, k * 1.4 - i * 0.05)) + 1, 12)]
        if len(pts) > 1: d.line(pts, fill=(90, 210, 210, a), width=2 * S)

def nube(d, cx, cy, alpha, t, lluvia=1.0, col=(78, 82, 98)):
    """Nube oscura con lluvia (dibujar en una capa sin halo)."""
    if alpha <= 0: return
    for bx, by, r in [(-70, 10, 48), (-20, -22, 62), (45, -8, 54), (85, 16, 40), (0, 20, 50)]:
        d.ellipse([(cx + bx - r) * S, (cy + by - r) * S, (cx + bx + r) * S, (cy + by + r) * S], fill=col + (int(alpha),))
    for i in range(10):
        ph = (t * 1.4 + i * 0.37) % 1; x = cx - 90 + i * 20; y = cy + 50 + ph * 190
        d.line([(x * S, y * S), ((x - 5) * S, (y + 22) * S)], fill=(150, 160, 180, int(alpha * lluvia * (1 - ph))), width=2 * S)

def orbe(d, g, t, t0, dur, x0, y0, x1, y1):
    """Luz de la dua que sube de (x0, y0) a (x1, y1) dejando una estela."""
    if t < t0: return None
    k = seg(t, t0, t0 + dur)
    def pos(u): return lerp(x0, x1, u) + 60 * math.sin(u * 7), lerp(y0, y1, u)
    if k < 1:
        for j in range(24):
            u = max(0.0, k - j * 0.012)
            px, py = pos(u); r = 12 * (1 - j / 24) + 2
            d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=(170, 250, 245, int(240 * (1 - j / 24))))
        px, py = pos(k); g.ellipse([px - 60, py - 60, px + 60, py + 60], fill=(120, 245, 238, 200))
    return k

def bloque(d, g, x, y, k, col, alpha, glow_col=None, crack=0.0, BW=50, BH=36):
    """Bloque de una montaña de buenas obras (k escala de aparición, crack 0..1 grieta)."""
    if k <= 0 or alpha <= 0: return
    w, h = BW * k / 2, BH * k / 2
    d.rounded_rectangle([(x - w) * S, (y - h) * S, (x + w) * S, (y + h) * S], radius=5 * S, fill=col + (int(alpha),))
    if crack > 0:
        d.line([((x - 8) * S, (y - h) * S), ((x + 2) * S, (y - 2) * S), ((x - 4) * S, (y + h * crack) * S)], fill=(40, 40, 46, int(alpha)), width=2 * S)
    if glow_col: g.ellipse([x - 30, y - 26, x + 30, y + 26], fill=glow_col + (int(90 * alpha / 255),))

# Postración (mira a la derecha; para mirar a la izquierda, cambia el signo de x).
SUJUD = dict(head=(136, -34), neck=(100, -62), hip=(-10, -120), le=(110, -30), lh=(90, -6), re=(116, -32), rh=(96, -6),
             lk=(0, -8), lf=(-80, -6), rk=(8, -8), rf=(-72, -6))
def a_sujud(k, izquierda=True):
    sg = -1 if izquierda else 1
    return {j: (lerp(P["stand"][j][0], sg * SUJUD[j][0], k), lerp(P["stand"][j][1], SUJUD[j][1], k)) for j in SUJUD}
PHONE = dict(P["stand"]); PHONE.update(re=(34, -200), rh=(30, -262), head=(-4, -298))   # mira el móvil (pantalla en (x+34, GY-272))

# ---------------- piezas del 16 nov 2026 (puerta, cúpula de luz, planta, cesta, fruta, nube de luz, pobre) ----------------

def puerta(d, x, open_k=0.0, h=230, w=104, col=CREAM, alpha=255, lado=1):
    """Marco de puerta de pie sobre el suelo, centrado en x. open_k 0..1 abre la hoja hacia el lado (1 derecha, -1 izquierda)."""
    c = col + (int(alpha),); lw = 6 * S
    x0, x1, top = x - w / 2, x + w / 2, GY - h
    d.line([(x0 * S, GY * S), (x0 * S, top * S), (x1 * S, top * S), (x1 * S, GY * S)], fill=c, width=lw, joint="curve")
    d.rectangle([x0 * S, top * S, x1 * S, GY * S], fill=(250, 215, 140, int(alpha * 0.25 * open_k)))   # luz de dentro
    hinge = x1 if lado > 0 else x0
    leaf = hinge - lado * w * math.cos(open_k * 1.3)           # la hoja se estrecha al abrirse
    skew = 16 * open_k
    pts = [(hinge, top), (leaf, top - skew * 0.5), (leaf, GY + skew * 0.3), (hinge, GY)]
    d.polygon([(a * S, b * S) for a, b in pts], fill=(18, 22, 28, int(alpha)), outline=c, width=int(4 * S))
    kx = lerp(hinge, leaf, 0.82)
    d.ellipse([(kx - 6) * S, (GY - h / 2 - 6) * S, (kx + 6) * S, (GY - h / 2 + 6) * S], fill=c)

def cupula(d, g, x, k, t, r=210, col=(130, 240, 232), ry=1.25):
    """Cúpula de luz protectora alrededor de una figura (k 0..1 la levanta)."""
    if k <= 0: return
    rr = r * (0.6 + 0.4 * k); a = int(200 * k)
    for i in range(3):
        ri = rr - i * 10 + 4 * math.sin(t * 3 + i)
        d.arc([(x - ri) * S, (GY - ri * ry) * S, (x + ri) * S, (GY + ri * ry) * S], 180, 360, fill=col + (int(a * (1 - 0.3 * i)),), width=int((4 - i) * S))
    g.ellipse([x - rr, GY - rr * ry, x + rr, GY + 30], fill=col + (int(55 * k),))
    for i in range(10):                                  # chispas que recorren la cúpula
        ang = math.pi + (t * 0.7 + i / 10) % 1 * math.pi
        px, py = x + rr * math.cos(ang), GY + rr * ry * math.sin(ang)
        d.ellipse([(px - 4) * S, (py - 4) * S, (px + 4) * S, (py + 4) * S], fill=(220, 255, 250, int(a * 0.9)))

def planta(d, g, x, h, vida=1.0, seca=0.0, t=0.0, luz=0.0):
    """Planta del huerto: tallo con hojas. vida 0..1 (tamaño), seca 0..1 (gris y caída), luz 0..1 (verde turquesa con brillo)."""
    if h <= 2 or vida <= 0: return
    hh = h * vida * (1 - 0.35 * seca)
    verde = tuple(int(lerp(a, b, luz)) for a, b in zip(CREAM, (150, 245, 200)))
    col = tuple(int(lerp(a, b, seca)) for a, b in zip(verde, (110, 100, 92)))
    c = col + (255,)
    sway = 4 * math.sin(t * 1.8 + x * 0.05) * (1 - seca)
    bend = 40 * seca                                     # la punta se cae cuando está seca
    pts = [(x, GY), (x + sway * 0.5, GY - hh * 0.5), (x + sway + bend * 0.6, GY - hh * 0.9), (x + sway + bend, GY - hh + bend * 0.8)]
    d.line([(a * S, b * S) for a, b in pts], fill=c, width=int(5 * S), joint="curve")
    for j, fy in enumerate((0.35, 0.6, 0.82)):
        sg = -1 if j % 2 else 1
        bx, by = x + sway * fy, GY - hh * fy
        lx, ly = bx + sg * 30 * vida, by - 14 * vida + 22 * seca
        d.polygon([(bx * S, by * S), ((bx + sg * 12) * S, (ly - 10) * S), (lx * S, ly * S), ((bx + sg * 14) * S, (by + 4) * S)], fill=c)
    if luz > 0: g.ellipse([x - 40, GY - hh - 30, x + 40, GY + 10], fill=(120, 240, 210, int(110 * luz)))

def fruta(d, g, x, y, r=13, alpha=255, glow=True):
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=GOLD + (int(alpha),))
    d.line([(x * S, (y - r) * S), ((x + 3) * S, (y - r - 7) * S)], fill=CREAM + (int(alpha),), width=2 * S)
    if glow: g.ellipse([x - 24, y - 24, x + 24, y + 24], fill=(250, 220, 140, int(90 * alpha / 255)))

def cesta(d, g, x, n, alpha=255, gris=0.0, w=96, h=62):
    """Cesta de mimbre con n frutas apiladas encima. gris 0..1 apaga la fruta."""
    c = CREAM + (int(alpha),)
    d.polygon([((x - w / 2) * S, (GY - h) * S), ((x + w / 2) * S, (GY - h) * S), ((x + w / 2 - 12) * S, GY * S), ((x - w / 2 + 12) * S, GY * S)], fill=(40, 36, 30, int(alpha)), outline=c, width=int(4 * S))
    for k in range(1, 3): d.line([((x - w / 2 + 6 * k) * S, (GY - h + 20 * k) * S), ((x + w / 2 - 6 * k) * S, (GY - h + 20 * k) * S)], fill=c, width=int(2 * S))
    fc = tuple(int(lerp(a, b, gris)) for a, b in zip(GOLD, (100, 96, 92)))
    i = 0
    for row, cnt in enumerate((4, 3, 2, 1)):
        for k in range(cnt):
            if i >= n: return
            fx = x + (k - (cnt - 1) / 2) * 24; fy = GY - h - 10 - row * 19
            d.ellipse([(fx - 12) * S, (fy - 12) * S, (fx + 12) * S, (fy + 12) * S], fill=fc + (int(alpha),))
            i += 1

def nube_luz(d, g, cx, cy, alpha, t, lluvia=0.0, ancho=1.0):
    """Nube blanca luminosa (la nube buena). lluvia 0..1 deja caer gotas turquesa hasta el suelo."""
    if alpha <= 0: return
    for bx, by, r in [(-80, 12, 50), (-26, -24, 66), (44, -10, 58), (96, 16, 44), (8, 22, 54)]:
        bx *= ancho
        d.ellipse([(cx + bx - r) * S, (cy + by - r) * S, (cx + bx + r) * S, (cy + by + r) * S], fill=(236, 240, 236, int(alpha)))
    g.ellipse([cx - 170 * ancho, cy - 110, cx + 170 * ancho, cy + 90], fill=(200, 250, 245, int(90 * alpha / 255)))
    if lluvia > 0:
        span = GY - (cy + 60)
        for i in range(16):
            ph = (t * 1.1 + i * 0.29) % 1; x = cx - 110 * ancho + i * 14.5 * ancho; y = cy + 60 + ph * span
            d.line([(x * S, y * S), ((x - 3) * S, (y + 26) * S)], fill=(150, 245, 238, int(230 * lluvia * (1 - 0.5 * ph))), width=3 * S)

# ---------------- piezas del 17 nov 2026 (cama, tumbarse, farol guardián, haz de luz, luna, zzz, móvil, nieve, raíces escaladas, semilla, pose de frío) ----------------

def cama(d, x0, x1, h=64, col=CREAM, alpha=255, almohada="l"):
    """Cama baja de líneas sobre el suelo (colchón de x0 a x1, altura h). Devuelve la y del colchón."""
    c = col + (int(alpha),); top = GY - h
    d.rounded_rectangle([x0 * S, top * S, x1 * S, (top + 26) * S], radius=10 * S, fill=(24, 30, 38, int(alpha)), outline=c, width=int(4 * S))
    for xs in (x0 + 12, x1 - 12): d.line([(xs * S, (top + 26) * S), (xs * S, GY * S)], fill=c, width=int(6 * S))
    hx = x0 + 10 if almohada == "l" else x1 - 80
    d.rounded_rectangle([hx * S, (top - 16) * S, (hx + 70) * S, (top + 4) * S], radius=9 * S, fill=c)
    return top

def tumbar(d, xpie, k, y_cama, lado=-1, escala=0.92, col=CREAM, alpha=255, pose=None):
    """Figura que pasa de estar de pie (k=0) a tumbada en la cama (k=1). lado -1: cabeza a la izquierda; 1: a la derecha."""
    p = pose or P["stand"]
    mini_figure(d, xpie, p, k=lerp(1.0, escala, k), rot=lado * (math.pi / 2) * k * 0.97, col=col, alpha=alpha, y0=lerp(GY, y_cama - 4, k))

def manta(d, x0, x1, y_cama, alpha=255, col=(70, 84, 98)):
    """Manta sobre la figura tumbada (de x0 a x1)."""
    d.rounded_rectangle([x0 * S, (y_cama - 24) * S, x1 * S, (y_cama + 6) * S], radius=12 * S, fill=col + (int(alpha),), outline=CREAM + (int(alpha * 0.8),), width=int(3 * S))

def farol(d, g, x, y, k, t, col=GOLD):
    """Farol árabe que cuelga del cielo (k 0..1 aparece y brilla)."""
    if k <= 0: return
    a = int(255 * k); c = CREAM + (a,)
    d.line([(x * S, (y - 84) * S), (x * S, (y - 46) * S)], fill=CREAM + (int(a * 0.6),), width=int(2 * S))
    d.polygon([((x - 22) * S, (y - 46) * S), ((x + 22) * S, (y - 46) * S), (x * S, (y - 72) * S)], fill=c)
    body = [(x - 30, y - 40), (x + 30, y - 40), (x + 38, y), (x + 30, y + 40), (x - 30, y + 40), (x - 38, y)]
    d.polygon([(a_ * S, b_ * S) for a_, b_ in body], fill=col + (int(a * (0.75 + 0.25 * math.sin(t * 4))),), outline=c, width=int(4 * S))
    for xx in (x - 12, x + 12): d.line([(xx * S, (y - 40) * S), (xx * S, (y + 40) * S)], fill=(120, 90, 40, a), width=int(2 * S))
    d.polygon([((x - 20) * S, (y + 40) * S), ((x + 20) * S, (y + 40) * S), (x * S, (y + 58) * S)], fill=c)
    g.ellipse([x - 120, y - 120, x + 120, y + 120], fill=(250, 220, 150, int(150 * k)))

def haz(d, g, x, y, x0, x1, k, t, col=(150, 245, 238)):
    """Haz de luz en cono desde (x, y) hasta el suelo entre x0 y x1 (protección)."""
    if k <= 0: return
    pts = [(x - 20, y + 50), (x + 20, y + 50), (x1, GY), (x0, GY)]
    d.polygon([(a * S, b * S) for a, b in pts], fill=col + (int(38 * k),))
    for i, (xa, xb) in enumerate(((x - 20, x0), (x + 20, x1))):
        d.line([(xa * S, (y + 50) * S), (xb * S, GY * S)], fill=col + (int(150 * k * (0.8 + 0.2 * math.sin(t * 3 + i))),), width=int(3 * S))
    g.polygon([(x - 30, y + 50), (x + 30, y + 50), (x1, GY), (x0, GY)], fill=col + (int(45 * k),))

def luna(d, g, x, y, r=34, alpha=255):
    """Luna creciente."""
    if alpha <= 0: return
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(236, 232, 214, int(alpha)))
    d.ellipse([(x - r + 15) * S, (y - r - 8) * S, (x + r + 15) * S, (y + r - 8) * S], fill=(0, 0, 0, 0))
    g.ellipse([x - 70, y - 70, x + 70, y + 70], fill=(200, 230, 225, int(50 * alpha / 255)))

def zzz(d, x, y, t, alpha=255):
    """Zetas de sueño tranquilo que suben."""
    import noche as _N
    for i in range(3):
        ph = (t * 0.35 + i / 3) % 1
        a = alpha * min(1, ph * 4) * (1 - ph)
        if a > 2: spaced(d, "z", x + 40 * ph + 12 * math.sin(t + i), y - 120 * ph, int(26 + 16 * ph), a, col=(190, 235, 230))

def movil(d, g, x, y, alpha=255):
    """Pantalla de móvil encendida (luz azul fría)."""
    if alpha <= 0: return
    d.rounded_rectangle([(x - 13) * S, (y - 22) * S, (x + 13) * S, (y + 22) * S], radius=4 * S, fill=(150, 190, 255, int(alpha)), outline=CREAM + (int(alpha),), width=int(2 * S))
    g.ellipse([x - 60, y - 60, x + 60, y + 60], fill=(110, 150, 255, int(110 * alpha / 255)))

def copos(d, t, alpha, n=70, seed=21, ymax=GY):
    """Nieve que cae por todo el cielo."""
    if alpha <= 0: return
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(0.05, 0.11); r = rnd.choice((3, 4, 5, 6)); ph0 = rnd.random()
        ph = (ph0 + t * sp) % 1
        y = 60 + ph * (ymax - 60); x = x0 + 18 * math.sin(t * 0.9 + i)
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(240, 244, 248, int(alpha * 0.85)))

def manto_nieve(d, x0, x1, h, alpha=255, seed=3):
    """Capa de nieve ondulada sobre el suelo, de altura h."""
    if h <= 1 or alpha <= 0: return
    pts = [(x0, GY)] + [(x, GY - h * (0.75 + 0.25 * math.sin(x / 55 + seed))) for x in range(int(x0), int(x1) + 1, 12)] + [(x1, GY)]
    d.polygon([(a * S, b * S) for a, b in pts], fill=(236, 240, 244, int(alpha)))

def raices_en(d, rg, x0, y0, k=1.0, col=CREAM, alpha=255):
    """Raíces (las de noche.ROOTS) que nacen en (x0, y0) a escala k."""
    if rg <= 0 or alpha <= 0: return
    for a, b, c, e, tb, w_ in N.ROOTS:
        if rg > tb:
            q = min(1, (rg - tb) / 0.06)
            pa = (x0 + (a - 880) * k, y0 + (b - GY - 18) * k); pc = (x0 + (lerp(a, c, q) - 880) * k, y0 + (lerp(b, e, q) - GY - 18) * k)
            d.line([(pa[0] * S, pa[1] * S), (pc[0] * S, pc[1] * S)], fill=col + (int(alpha * 0.92),), width=max(2, int(w_ * k * S)))

def semilla(d, g, x, y, alpha=255, col=GOLD, brillo=1.0, r=13):
    if alpha <= 0: return
    d.ellipse([(x - r) * S, (y - r * 0.7) * S, (x + r) * S, (y + r * 0.7) * S], fill=col + (int(alpha),))
    if brillo > 0: g.ellipse([x - 36, y - 30, x + 36, y + 30], fill=(250, 220, 140, int(110 * brillo * alpha / 255)))

FRIO = dict(P["stand"]); FRIO.update(le=(-36, -200), lh=(22, -218), re=(36, -204), rh=(-22, -212), head=(0, -296))   # se abraza por el frío

# ---------------- piezas del 18 nov 2026 (espuma del mar, tasbih, contador, corazón, corona, likes, destellos) ----------------

def _burbujas(x0, x1, y0, y1, n, seed):
    rnd = random.Random(seed); out = []
    for i in range(n):
        x = rnd.uniform(x0, x1); y = rnd.uniform(y0, y1); r = rnd.uniform(9, 26) * (1 - 0.35 * (y - y0) / max(1, y1 - y0))
        out.append((x, y, r, rnd.uniform(0, 6.28), rnd.random()))
    out.sort(key=lambda b: -b[1])                        # se llena de abajo arriba
    return out

def espuma(d, g, x0, x1, k, t, limpio=0.0, seed=1, n=70, y0=GY + 40, y1=GY + 430, col=(96, 94, 108)):
    """Espuma oscura (pecados) bajo el suelo entre x0 y x1. k 0..1 cantidad visible (de abajo arriba).
    limpio 0..1: una ola de luz barre de izquierda a derecha y cada burbuja se vuelve gota turquesa que sube y se apaga."""
    if k <= 0: return
    bs = _burbujas(x0, x1, y0, y1, n, seed)
    for i, (x, y, r, ph, rr) in enumerate(bs):
        if i >= k * n: break
        pop = min(1.0, (k * n - i) / 2.5)
        thr = (x - x0) / max(1, x1 - x0)
        pr = max(0.0, min(1.0, (limpio * 1.35 - thr) / 0.35))
        if pr >= 1: continue
        xx = x + 4 * math.sin(t * 1.6 + ph); yy = y + 3 * math.cos(t * 1.3 + ph) - 120 * pr
        rad = r * (0.6 + 0.4 * pop) * (1 - 0.5 * pr)
        c = tuple(int(lerp(a, b, pr)) for a, b in zip(col, (150, 245, 238)))
        a = int(235 * (1 - pr))
        d.ellipse([(xx - rad) * S, (yy - rad) * S, (xx + rad) * S, (yy + rad) * S], fill=c + (a,), outline=(140, 138, 150, int(a * 0.8)), width=int(2 * S))
        d.ellipse([(xx - rad * 0.45) * S, (yy - rad * 0.6) * S, (xx - rad * 0.05) * S, (yy - rad * 0.25) * S], fill=(200, 200, 210, int(a * 0.5)))
        if pr > 0: g.ellipse([xx - 22, yy - 22, xx + 22, yy + 22], fill=(120, 245, 238, int(150 * (1 - pr))))

def ola_luz(d, g, x0, x1, k, y0=GY + 30, y1=GY + 450, col=(130, 240, 232)):
    """Frente de luz vertical que barre de x0 a x1 bajo el suelo (k 0..1)."""
    if k <= 0 or k >= 1: return
    x = lerp(x0, x1, k)
    for i in range(6):
        yy = lerp(y0, y1, i / 5)
        d.line([((x + 10 * math.sin(i * 1.7 + k * 8)) * S, (yy - 35) * S), ((x - 6) * S, (yy + 35) * S)], fill=col + (int(220 * math.sin(math.pi * k)),), width=int(5 * S))
    g.rectangle([x - 40, y0, x + 30, y1], fill=col + (int(120 * math.sin(math.pi * k)),))

DHIKR = dict(P["stand"]); DHIKR.update(re=(34, -196), rh=(52, -228), le=(-26, -212), lh=(-32, -150))   # sostiene el tasbih delante del pecho (mano en (x+52, GY-228))

def tasbih(d, g, hx, hy, t, activo=0.0, n=15, alpha=255, col=CREAM):
    """Tasbih (cuentas) colgando de la mano en (hx, hy). activo 0..1 hace correr las cuentas y brillar la que pasa."""
    if alpha <= 0: return
    cx, cy, rx, ry = hx, hy + 44, 20, 40
    pos = (t * 9 * activo) % n
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * (i + 0.5) / n
        px, py = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        hi = max(0.0, 1 - abs(((i - pos + n / 2) % n) - n / 2)) * activo
        c = tuple(int(lerp(a, b, hi)) for a, b in zip(col, (150, 245, 238)))
        r = 6 + 2 * hi
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=c + (int(alpha),))
        if hi > 0.3: g.ellipse([px - 24, py - 24, px + 24, py + 24], fill=(120, 245, 238, int(160 * hi)))
    d.line([(cx * S, (cy + ry + 4) * S), (cx * S, (cy + ry + 26) * S)], fill=col + (int(alpha),), width=int(3 * S))
    d.ellipse([(cx - 5) * S, (cy + ry + 24) * S, (cx + 5) * S, (cy + ry + 34) * S], fill=col + (int(alpha),))

def contador(d, x, y, n, alpha=255, size=40, total=100, col=(190, 235, 230)):
    """Contador «n/total» encima de una figura."""
    if alpha <= 0: return
    txt = f"{int(n)}/{total}" if n < total else f"×{total}"
    spaced(d, txt, x, y, size, alpha, col=col if n < total else (130, 240, 232))

def corazon(d, g, cx, cy, r, col=CREAM, alpha=255, brillo=0.0, grieta=0.0, glow_col=(120, 240, 232)):
    """Corazón relleno (lo de dentro). brillo 0..1 halo; grieta 0..1 lo parte."""
    if alpha <= 0 or r <= 1: return
    pts = []
    for i in range(60):
        u = 2 * math.pi * i / 60
        x = 16 * math.sin(u) ** 3; y = -(13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u))
        pts.append(((cx + x * r / 16) * S, (cy + y * r / 16) * S))
    d.polygon(pts, fill=col + (int(alpha),))
    if grieta > 0:
        zz = [(cx - 2, cy - r * 0.55), (cx + r * 0.12, cy - r * 0.2), (cx - r * 0.1, cy + r * 0.1), (cx + r * 0.1, cy + r * 0.45), (cx, cy + r * 0.8)]
        m = 1 + int(grieta * 4)
        d.line([(a * S, b * S) for a, b in zz[:m]], fill=(20, 20, 24, int(alpha)), width=int(max(3, r * 0.07) * S), joint="curve")
    if brillo > 0: g.ellipse([cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2], fill=glow_col + (int(170 * brillo * alpha / 255),))

def corona(d, g, x, y, k=1.0, alpha=255, col=GOLD, brillo=1.0):
    """Corona dorada centrada en (x, y) (base). k escala."""
    if alpha <= 0 or k <= 0: return
    w, h = 44 * k, 34 * k
    pts = [(x - w, y), (x - w, y - h * 0.6), (x - w * 0.5, y - h * 0.2), (x, y - h), (x + w * 0.5, y - h * 0.2), (x + w, y - h * 0.6), (x + w, y)]
    d.polygon([(a * S, b * S) for a, b in pts], fill=col + (int(alpha),), outline=(150, 120, 60, int(alpha)), width=int(2 * S))
    for px in (x - w, x, x + w):
        py = y - (h if px == x else h * 0.6)
        d.ellipse([(px - 5 * k) * S, (py - 5 * k) * S, (px + 5 * k) * S, (py + 5 * k) * S], fill=col + (int(alpha),))
    if brillo > 0: g.ellipse([x - 70, y - 70, x + 70, y + 30], fill=(250, 220, 140, int(120 * brillo * alpha / 255)))

def likes(d, g, x, y, t, k, seed=4, col=(235, 110, 120)):
    """Corazoncitos de «me gusta» que suben desde (x, y). k 0..1 intensidad."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(10):
        ph0 = rnd.random(); sp = rnd.uniform(0.35, 0.6); dx = rnd.uniform(-40, 70)
        ph = (ph0 + t * sp) % 1
        px = x + dx * ph + 10 * math.sin(t * 3 + i); py = y - 30 - 230 * ph
        a = 230 * k * min(1, ph * 5) * (1 - ph)
        corazon(d, g, px, py, 11 + 4 * ph, col=col, alpha=a, brillo=0)

def destellos(d, g, x, y0, y1, t, k, seed=6, col=GOLD):
    """Brillos dorados alrededor de una figura (lo que luce por fuera)."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(9):
        px = x + rnd.uniform(-90, 90); py = rnd.uniform(y0, y1); ph = (t * 1.3 + rnd.random()) % 1
        s = 12 * math.sin(math.pi * ph) * k
        if s <= 0.5: continue
        c = col + (int(240 * k),)
        d.line([((px - s) * S, py * S), ((px + s) * S, py * S)], fill=c, width=int(3 * S))
        d.line([(px * S, (py - s) * S), (px * S, (py + s) * S)], fill=c, width=int(3 * S))
        g.ellipse([px - 18, py - 18, px + 18, py + 18], fill=(250, 220, 140, int(100 * k * math.sin(math.pi * ph))))

# ---------------- piezas del 19 nov 2026 (bostezo, boca, hilo de sombra, humo bajo tierra, bocadillo, piedra, escalones de luz) ----------------

# Bostezo: estira los brazos arriba y echa la cabeza un poco atrás (mirando a la derecha; usa mirror para la izquierda).
BOSTEZO = dict(P["stand"]); BOSTEZO.update(head=(4, -304), neck=(0, -264), le=(-40, -286), lh=(-58, -342), re=(40, -286), rh=(58, -342))
# Se tapa la boca con la mano derecha mientras bosteza (la mano queda en (x+20, GY-294)).
TAPA = dict(P["stand"]); TAPA.update(head=(4, -304), neck=(0, -264), le=(-40, -286), lh=(-58, -342), re=(36, -232), rh=(22, -292))
# Habla gesticulando con una mano abierta hacia delante (derecha).
HABLA = dict(P["stand"]); HABLA.update(re=(44, -228), rh=(92, -246))

def lerp_pose(a, b, k):
    return {j: (lerp(a[j][0], b[j][0], k), lerp(a[j][1], b[j][1], k)) for j in a}

def espejo(p):
    return {j: (-v[0], v[1]) for j, v in p.items()}

def boca(d, x, y, k, alpha=255):
    """Boca abierta (óvalo oscuro) en la cara de una figura sin rasgos; k 0..1 cuánto se abre."""
    if k <= 0.02 or alpha <= 0: return
    rx, ry = 9 + 3 * k, 4 + 13 * k
    d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=(16, 18, 26, int(alpha)))

def hilo_sombra(d, x0, y0, x1, y1, k, t, alpha=220, n=14, col=SHADOW, r=16):
    """Hilo de humo oscuro que va de (x0, y0) a (x1, y1) (k 0..1 cuánto ha avanzado la punta). Para algo que «se cuela»."""
    if k <= 0 or alpha <= 0: return
    for i in range(n):
        u = k - i * 0.05
        if u <= 0: break
        u = min(1.0, u)
        px = lerp(x0, x1, u) + 18 * math.sin(u * 9 + t * 3) * (1 - u)
        py = lerp(y0, y1, u) - 40 * math.sin(math.pi * u)
        rr = r * (1 - i / n) * (1 - 0.5 * u) + 3
        d.ellipse([(px - rr) * S, (py - rr) * S, (px + rr) * S, (py + rr) * S], fill=col + (int(alpha * (1 - i / n)),))

def humo_dentro(d, x, k, t, col=(58, 54, 72), seed=8):
    """Humo oscuro que se acumula bajo el suelo debajo de x (lo que se ha colado). k 0..1."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(int(4 + 22 * k)):
        bx = x + rnd.uniform(-150, 150) * (0.4 + 0.6 * k); by = GY + 40 + rnd.uniform(0, 330) * (0.3 + 0.7 * k)
        r = rnd.uniform(24, 52) * (0.5 + 0.5 * k)
        bx += 8 * math.sin(t * 0.9 + i); by += 5 * math.cos(t * 0.7 + i)
        d.ellipse([(bx - r) * S, (by - r) * S, (bx + r) * S, (by + r) * S], fill=col + (int(170 + 60 * k),))

def bocadillo(d, x, y, txt, alpha=255, size=30, col=CREAM, fondo=(18, 22, 30), cola=-1, borde=None):
    """Bocadillo de diálogo con texto espaciado centrado en (x, y). cola -1 apunta abajo-izquierda, 1 abajo-derecha."""
    if alpha <= 0: return
    a = int(alpha); n = len(txt)
    w = n * size * (0.602 + 0.22) + 40; h = size + 34
    bc = (borde or col) + (a,)
    tx = x + cola * w * 0.22
    d.polygon([((tx - 14) * S, (y + h / 2 - 3) * S), ((tx + 14) * S, (y + h / 2 - 3) * S), ((tx + cola * 26) * S, (y + h / 2 + 26) * S)], fill=fondo + (a,), outline=bc, width=int(3 * S))
    d.rounded_rectangle([(x - w / 2) * S, (y - h / 2) * S, (x + w / 2) * S, (y + h / 2) * S], radius=int(h / 2 * S), fill=fondo + (a,), outline=bc, width=int(3 * S))
    d.line([((tx - 11) * S, (y + h / 2 - 2) * S), ((tx + 11) * S, (y + h / 2 - 2) * S)], fill=fondo + (a,), width=int(5 * S))
    spaced(d, txt, x, y, size, alpha, track=0.22, col=col)

def piedra(d, x, y, r=20, alpha=255, rot=0.0, col=(92, 86, 96)):
    """Piedra oscura irregular (una palabra que pesa y cae)."""
    if alpha <= 0: return
    pts = []
    for i, f in enumerate((1.0, 0.82, 1.08, 0.9, 1.0, 0.78, 1.05)):
        ang = rot + i * 2 * math.pi / 7
        pts.append(((x + r * f * math.cos(ang)) * S, (y + r * f * 0.85 * math.sin(ang)) * S))
    d.polygon(pts, fill=col + (int(alpha),), outline=(140, 132, 140, int(alpha * 0.8)), width=int(2 * S))

def escalones(d, g, x, n, k, ancho=150, alto=46, lado=1, col=(130, 240, 232)):
    """Escalones de luz (grados) que suben desde el suelo junto a x, hacia el lado indicado. k 0..1 cuántos se ven (de n).
    Devuelve la altura (px sobre el suelo) del último escalón completo, para subir a una figura."""
    top = 0.0
    for i in range(n):
        q = max(0.0, min(1.0, k * n - i))
        if q <= 0: break
        x0 = x + lado * i * ancho * 0.55 - ancho / 2; y = GY - (i + 1) * alto
        w = ancho * q
        d.rounded_rectangle([x0 * S, (y - 6) * S, (x0 + w) * S, (y + 6) * S], radius=6 * S, fill=col + (int(235 * q),))
        g.rectangle([x0, y - 18, x0 + w, y + 18], fill=col + (int(110 * q),))
        if q >= 1: top = (i + 1) * alto
    return top

# ---------------- piezas del 20 nov 2026 (sentado en el suelo comiendo, mantel, granos de baraka) ----------------

def sentado(comer=0.0, droop=0.0, joy=0.0):
    """Figura sentada en el suelo con las piernas cruzadas, mirando a la derecha (usa espejo() para la izquierda).
    comer 0..1 lleva la mano 're/rh' del plato (x+118, GY-20) a la boca; droop 0..1 se encoge; joy 0..1 levanta los brazos."""
    p = dict(head=(12, -206), neck=(4, -168), hip=(-10, -40), le=(22, -110), lh=(50, -56), re=(64, -90), rh=(118, -20),
             lk=(48, -40), lf=(18, -6), rk=(38, -30), rf=(4, -4))
    p["re"] = (lerp(64, 62, comer), lerp(-90, -122, comer)); p["rh"] = (lerp(118, 40, comer), lerp(-20, -186, comer))
    if droop > 0:
        for j, v in dict(head=(42, -168), neck=(26, -140), le=(34, -96), lh=(56, -50)).items():
            p[j] = (lerp(p[j][0], v[0], droop), lerp(p[j][1], v[1], droop))
    if joy > 0:
        for j, v in dict(le=(-20, -220), lh=(-46, -276), re=(30, -224), rh=(56, -280)).items():
            p[j] = (lerp(p[j][0], v[0], joy), lerp(p[j][1], v[1], joy))
    return p

def mantel(d, cx, w=170, alpha=255, col=CREAM):
    """Mantel (sufra) extendido en el suelo, con un dibujo de puntos."""
    if alpha <= 0: return
    a = int(alpha)
    d.rounded_rectangle([(cx - w / 2) * S, (GY - 7) * S, (cx + w / 2) * S, (GY + 5) * S], radius=5 * S, fill=(34, 40, 50, a), outline=col + (a,), width=int(3 * S))
    for i in range(7):
        x = cx - w / 2 + 16 + i * (w - 32) / 6
        d.ellipse([(x - 3) * S, (GY - 3) * S, (x + 3) * S, (GY + 3) * S], fill=GOLD + (int(a * 0.7),))

def granos(d, g, x, k, t, seed=12, col=GOLD):
    """Montón de granos dorados que se acumula bajo el suelo debajo de x (baraka, lo que no se ve). k 0..1."""
    if k <= 0: return
    rnd = random.Random(seed); n = int(60 * k)
    for i in range(n):
        u = rnd.random(); v = rnd.random()
        hw = 170 * (1 - v * 0.75)                     # forma de montaña: más ancho abajo
        bx = x + (u - 0.5) * 2 * hw; by = GY + 380 - v * 300 * (0.4 + 0.6 * k)
        r = rnd.uniform(5, 9); tw = 0.75 + 0.25 * math.sin(t * 3 + i)
        d.ellipse([(bx - r) * S, (by - r * 0.7) * S, (bx + r) * S, (by + r * 0.7) * S], fill=col + (int(235 * tw),))
    g.ellipse([x - 190, GY + 120 - 200 * k, x + 190, GY + 400], fill=(250, 220, 140, int(70 * k)))

# ---------------- piezas del 20 nov 2026 (b): mar que se abre en dos murallas, bastón, soldado con lanza y antorcha, polvo, pose de miedo ----------------

MIEDO = dict(P["stand"]); MIEDO.update(le=(-34, -250), lh=(-14, -300), re=(34, -250), rh=(14, -300), head=(0, -296))   # manos a la cabeza

def mar_alto(d, g, x0, x1, h0, t, abre=0.0, gx=820, gw_max=110, hmax=560, col=(18, 66, 80)):
    """Mar por ENCIMA del suelo, de x0 a x1 con altura h0. abre 0..1 lo parte en dos murallas alrededor de gx
    (hueco de 2*gw_max px con un camino de luz en el fondo). hmax: altura de las murallas (no taparlas con texto)."""
    gw = gw_max * abre
    def top(x):
        if abre > 0 and abs(x - gx) < gw - 0.5: return None
        dist = abs(x - gx) - gw
        hh = h0 + (hmax - h0) * abre * math.exp(-(dist / 150) ** 2) if abre > 0 else h0
        return GY - hh + 9 * math.sin(x / 45 + t * 1.6) * (1 - 0.6 * abre)
    for a, b in ((x0, gx - gw if abre > 0 else x1), (gx + gw, x1) if abre > 0 else (None, None)):
        if a is None or b - a < 4: continue
        xs = [a + (b - a) * i / 40 for i in range(41)]
        pts = [(a, GY)] + [(x, top(x)) for x in xs] + [(b, GY)]
        d.polygon([(px * S, py * S) for px, py in pts], fill=col + (235,))
        d.line([(x * S, top(x) * S) for x in xs], fill=(150, 235, 235, 230), width=int(4 * S))          # espuma de la superficie
        for k in range(1, 9):                                                                             # olas dentro del agua
            y = GY - k * 40
            seg_pts = [((x) * S, (y + 6 * math.sin(x / 38 + t * 1.3 + k)) * S) for x in xs if top(x) < y - 10]
            if len(seg_pts) > 1: d.line(seg_pts, fill=(90, 200, 205, 110), width=int(2 * S))
        if abre > 0:                                                                                      # bordes de las murallas
            for xe in (a, b):
                if abs(xe - gx) <= gw + 1:
                    ty = top(xe - 1 if xe == b else xe + 1)
                    d.line([(xe * S, ty * S), (xe * S, GY * S)], fill=(190, 250, 248, int(230 * abre)), width=int(4 * S))
                    g.rectangle([xe - 14, ty, xe + 14, GY], fill=(120, 240, 235, int(90 * abre)))
    if abre > 0:                                                                                          # camino de luz en el fondo
        d.line([((gx - gw) * S, (GY - 2) * S), ((gx + gw) * S, (GY - 2) * S)], fill=(150, 245, 238, 255), width=int(6 * S))
        g.rectangle([gx - gw, GY - 120 * abre, gx + gw, GY + 10], fill=(140, 245, 238, int(120 * abre)))

def baston(d, hx, hy, ang, largo=330, col=CREAM, alpha=255):
    """Bastón que sale de la mano (hx, hy) con ángulo ang (rad, 0 = vertical hacia abajo; positivo gira hacia la derecha).
    El punto de agarre está a 1/3 del largo. Devuelve la punta inferior."""
    ux, uy = -math.sin(ang), math.cos(ang)
    x0, y0 = hx - ux * largo / 3, hy - uy * largo / 3; x1, y1 = hx + ux * largo * 2 / 3, hy + uy * largo * 2 / 3
    d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=col + (int(alpha),), width=int(7 * S))
    d.arc([(x0 - 16) * S, (y0 - 16) * S, (x0 + 16) * S, (y0 + 16) * S], 180, 360, fill=col + (int(alpha),), width=int(6 * S))
    return x1, y1

def soldado(d, g, x, t, k=0.85, alpha=230, antorcha=False, ph=0.0, andar=1.0, col=(88, 80, 106)):
    """Soldado de sombra que marcha hacia la derecha con una lanza (y antorcha si antorcha=True)."""
    if alpha <= 0: return
    p = walk_pose(t * 6 + ph, amp=0.8 * andar)
    mini_figure(d, x, p, k=k, col=col, alpha=alpha)
    hx, hy = x + p["rh"][0] * k, GY + p["rh"][1] * k
    d.line([((hx - 10) * S, (hy + 60 * k) * S), ((hx + 24) * S, (hy - 250 * k) * S)], fill=(90, 84, 104, int(alpha)), width=int(4 * S))
    d.polygon([((hx + 24) * S, (hy - 250 * k - 26) * S), ((hx + 16) * S, (hy - 250 * k + 4) * S), ((hx + 32) * S, (hy - 250 * k + 2) * S)], fill=(120, 112, 130, int(alpha)))
    if antorcha:
        lx, ly = x + p["lh"][0] * k, GY + p["lh"][1] * k - 70 * k
        d.line([(lx * S, (ly + 70 * k) * S), (lx * S, ly * S)], fill=(90, 84, 104, int(alpha)), width=int(4 * S))
        fl = 1 + 0.2 * math.sin(t * 13 + ph)
        d.ellipse([(lx - 9 * fl) * S, (ly - 22 * fl) * S, (lx + 9 * fl) * S, (ly + 4) * S], fill=(240, 170, 90, int(alpha)))
        g.ellipse([lx - 46, ly - 50, lx + 46, ly + 36], fill=(240, 150, 70, int(110 * alpha / 255)))

def polvo(d, x0, x1, k, t, col=(70, 66, 80), seed=5):
    """Nube de polvo baja que levanta un ejército (dibujar en capa sin halo)."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(18):
        bx = rnd.uniform(x0, x1) + 20 * math.sin(t * 0.8 + i); by = GY - rnd.uniform(10, 90) - 10 * math.sin(t + i)
        r = rnd.uniform(30, 60)
        d.ellipse([(bx - r) * S, (by - r * 0.6) * S, (bx + r) * S, (by + r * 0.6) * S], fill=col + (int(110 * k),))


# ---------------- piezas del 23 nov 2026 (muro de distancia, lazo de luz entre corazones, caja pesada, hoguera, vela) ----------------
GRIS = (120, 116, 126)
TEAL_L = (130, 240, 232)
FUEGO = (250, 196, 120)

def muro(d, x, h, alpha=255, w=56, col=GRIS):
    """Muro de ladrillos grises que crece desde el suelo (h px). Objeto nuevo: la distancia que no se ve."""
    if h <= 2 or alpha <= 0: return
    bh = 26; n = int(h // bh) + 1
    for i in range(n):
        y1 = GY - i * bh; y0 = max(GY - h, y1 - bh)
        if y0 >= y1: break
        off = (bh / 2 if i % 2 else 0)
        d.rectangle([(x - w / 2) * S, y0 * S, (x + w / 2) * S, y1 * S], fill=(44, 44, 52, int(alpha * 0.9)), outline=col + (int(alpha),), width=int(2 * S))
        d.line([((x - w / 2 + 14 + off) * S, y0 * S), ((x - w / 2 + 14 + off) * S, y1 * S)], fill=col + (int(alpha * 0.8),), width=int(2 * S))

def lazo(d, g, x0, y0, x1, y1, k, t, alpha=255, alto=90, col=TEAL_L):
    """Lazo de luz en arco entre dos corazones; k 0..1 cuánto se ha tendido. Chispas que viajan por él (objeto nuevo)."""
    if k <= 0 or alpha <= 0: return
    pts = []
    for i in range(41):
        u = i / 40 * k
        pts.append((lerp(x0, x1, u), lerp(y0, y1, u) - alto * math.sin(math.pi * u)))
    d.line([(a * S, b * S) for a, b in pts], fill=col + (int(alpha * 0.9),), width=int(4 * S), joint="curve")
    for a, b in pts[::4]: g.ellipse([a - 18, b - 18, a + 18, b + 18], fill=(90, 235, 228, int(alpha * 0.35)))
    if k >= 1:
        for j in range(2):
            u = (t * 0.45 + j * 0.5) % 1
            a, b = lerp(x0, x1, u), lerp(y0, y1, u) - alto * math.sin(math.pi * u)
            d.ellipse([(a - 6) * S, (b - 6) * S, (a + 6) * S, (b + 6) * S], fill=(230, 255, 250, int(alpha)))
    for (a, b) in ((x0, y0), (pts[-1][0], pts[-1][1])):
        d.ellipse([(a - 9) * S, (b - 9) * S, (a + 9) * S, (b + 9) * S], fill=col + (int(alpha),))

def caja(d, x, y, alpha=255, w=112, h=84, col=CREAM, gris=0.0):
    """Caja de mudanza pesada (centro x, base y)."""
    c = tuple(int(lerp(a, b, gris)) for a, b in zip(col, (110, 108, 116))) + (int(alpha),)
    d.rectangle([(x - w / 2) * S, (y - h) * S, (x + w / 2) * S, y * S], fill=(30, 32, 40, int(alpha)), outline=c, width=int(5 * S))
    d.line([((x - w / 2) * S, (y - h + 18) * S), ((x + w / 2) * S, (y - h + 18) * S)], fill=c, width=int(3 * S))
    d.line([(x * S, (y - h) * S), (x * S, (y - h + 18) * S)], fill=c, width=int(3 * S))

def gotas_sudor(d, x, y, t, alpha=255):
    for i in range(2):
        ph = (t * 1.2 + i * 0.5) % 1
        yy = y + 30 * ph; xx = x + 20 * i
        d.ellipse([(xx - 4) * S, (yy - 7) * S, (xx + 4) * S, (yy + 5) * S], fill=(200, 225, 235, int(alpha * (1 - ph))))

def llama(d, g, x, y, h, w, t, alpha=255, col=FUEGO, seed=0):
    """Una lengua de fuego (gota alargada que tiembla)."""
    if h <= 2 or alpha <= 0: return
    sw = 1 + 0.08 * math.sin(t * 9 + seed); hh = h * (1 + 0.1 * math.sin(t * 7 + seed * 2))
    tip = x + w * 0.35 * math.sin(t * 5 + seed)
    pts = []
    for i in range(13):
        a = math.pi * i / 12
        pts.append((x - w * sw * math.cos(a), y - w * 0.55 * math.sin(a) * 0.6))
    pts += [(x + w * 0.6, y - hh * 0.4), (tip, y - hh), (x - w * 0.6, y - hh * 0.4)]
    d.polygon([(a * S, b * S) for a, b in pts], fill=col + (int(alpha),))
    inner = [(x + (px - x) * 0.5, y + (py - y) * 0.5) for px, py in pts]
    d.polygon([(a * S, b * S) for a, b in inner], fill=(255, 244, 214, int(alpha)))

def hoguera(d, g, x, k, t, ceniza=0.0):
    """Hoguera (objeto nuevo): k 0..1 tamaño del fuego; ceniza 0..1 brasas y ceniza gris cuando se apaga."""
    leña = tuple(int(lerp(a, b, ceniza)) for a, b in zip(CREAM, (100, 98, 104)))
    for a in (-0.35, 0.35, 0.0):
        dx = 90 * math.cos(a) ; dy = 90 * math.sin(a) * 0.25
        d.line([((x - dx) * S, (GY - 10 - dy) * S), ((x + dx) * S, (GY - 10 + dy) * S)], fill=leña + (255,), width=int(12 * S))
    if ceniza > 0:
        d.ellipse([(x - 80) * S, (GY - 22) * S, (x + 80) * S, (GY + 4) * S], fill=(80, 78, 84, int(220 * ceniza)))
        for i in range(5):
            bx = x - 50 + i * 25; d.ellipse([(bx - 5) * S, (GY - 16) * S, (bx + 5) * S, (GY - 6) * S], fill=(230, 120, 80, int(200 * ceniza * (1 - seg(ceniza, 0.6, 1.0)) * (0.5 + 0.5 * math.sin(t * 4 + i)))))
    if k > 0.02:
        for i, (ox, hk, wk) in enumerate(((0, 1.0, 1.0), (-48, 0.7, 0.7), (48, 0.75, 0.7), (-20, 0.55, 0.5), (26, 0.6, 0.5))):
            llama(d, g, x + ox * k, GY - 18, 330 * k * hk, 60 * k * wk + 6, t, seed=i)
        g.ellipse([x - 260 * k, GY - 420 * k - 40, x + 260 * k, GY + 40], fill=(255, 180, 90, int(150 * k)))
        rnd = random.Random(3)
        for i in range(int(14 * k)):                      # chispas
            ph = (t * 0.7 + rnd.random()) % 1
            sx = x + rnd.uniform(-90, 90) * k + 20 * math.sin(t * 3 + i); sy = GY - 60 - ph * 520 * k
            d.ellipse([(sx - 3) * S, (sy - 3) * S, (sx + 3) * S, (sy + 3) * S], fill=FUEGO + (int(255 * (1 - ph)),))

def humo(d, x, y, k, t, seed=4):
    """Humo gris que sube de lo que se apaga."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(10):
        ph = (t * 0.25 + i / 10) % 1
        px = x + 30 * math.sin(ph * 6 + i) + rnd.uniform(-20, 20); py = y - ph * 420
        r = 18 + 40 * ph
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=(110, 108, 118, int(120 * k * (1 - ph))))

def vela(d, g, x, y, t, alpha=255):
    """Vela pequeña en la mano: cuerpo blanco y llamita constante (objeto nuevo)."""
    d.rounded_rectangle([(x - 9) * S, (y - 4) * S, (x + 9) * S, (y + 40) * S], radius=3 * S, fill=CREAM + (int(alpha),))
    llama(d, g, x, y - 6, 34, 9, t * 0.6, alpha)
    g.ellipse([x - 70, y - 90, x + 70, y + 40], fill=(255, 200, 120, int(130 * alpha / 255)))

# ---- piezas del 25/11 (baño: SE OLVIDA vs SE REFUGIA) ----
DUA = dict(P["stand"]); DUA.update(le=(14, -214), lh=(40, -262), re=(40, -210), rh=(66, -256), head=(4, -300))   # manos levantadas (dua) hacia la derecha
CARGADO = dict(P["stand"]); CARGADO.update(head=(18, -270), neck=(10, -236), hip=(0, -124), le=(30, -180), lh=(40, -122),
                                           re=(36, -182), rh=(50, -124), lk=(-10, -60), rk=(18, -60))            # encorvado, cargado

def humo_puerta(d, x, k, t, seed=3, top=GY - 260, col=(52, 48, 66)):
    """Humo oscuro que asoma por encima de una puerta cerrada (algo espera detrás). Dibujar en capa under."""
    if k <= 0: return
    rnd = random.Random(seed)
    for i in range(9):
        ph = (t * 0.35 + i / 9) % 1
        px = x + rnd.uniform(-36, 36) + 16 * math.sin(t * 1.6 + i); py = top + 6 - ph * 150
        r = 12 + 22 * ph
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=col + (int(200 * k * (1 - ph)),))

def cortina(d, g, x, k, t, w=112, h=260, brillo=0.0, col=(130, 240, 232)):
    """Cortina de luz que cae desde el dintel y tapa una puerta (k 0..1 cuánto ha bajado)."""
    if k <= 0: return
    top = GY - h - 6; largo = (h + 6) * k; n = 9
    for i in range(n):
        u = i / (n - 1); bx = x - w / 2 + u * w
        pts = [((bx + 5 * math.sin(t * 2.2 + i * 0.9 + (j / 12) * 5) * (j / 12)) * S, (top + largo * j / 12) * S) for j in range(13)]
        a = int((150 + 90 * brillo) * (0.6 + 0.4 * math.sin(t * 3 + i)))
        d.line(pts, fill=col + (a,), width=int(4 * S), joint="curve")
        ex, ey = pts[-1][0] / S, pts[-1][1] / S
        d.ellipse([(ex - 5) * S, (ey - 5) * S, (ex + 5) * S, (ey + 5) * S], fill=(225, 255, 250, a))
    d.line([((x - w / 2 - 10) * S, top * S), ((x + w / 2 + 10) * S, top * S)], fill=col + (240,), width=int(6 * S))
    g.rectangle([x - w / 2 - 20, top - 10, x + w / 2 + 20, top + largo], fill=(80, 230, 225, int((70 + 90 * brillo) * k)))

def chispas(d, x, y, t, t0, dur=1.4, n=16, col=(200, 255, 250), seed=7):
    """Chispas turquesa que salen de un punto (algo oscuro que se deshace en luz)."""
    if not (t0 <= t < t0 + dur): return
    rnd = random.Random(seed); u = (t - t0) / dur
    for i in range(n):
        ang = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(60, 170)
        px = x + math.cos(ang) * sp * u; py = y + math.sin(ang) * sp * u - 40 * u
        r = 6 * (1 - u) + 1
        d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=col + (int(255 * (1 - u)),))

# ---------------- piezas del 26 nov 2026 (cuerda con nudos, despertador, balanza, bandeja, piedra de luz) ----------------
NUDO = (78, 70, 96)

def cuerda_nudos(d, g, cx, cy, k, t, sueltos=(0.0, 0.0, 0.0), oscuro=0.0, w=170, hilo_a=None, alpha=255):
    """Cuerda de humo flotante con 3 nudos (los nudos del shaitán). k 0..1 aparece; sueltos[i] 0..1 deshace el nudo i
    (se abre y queda un punto de luz que sube); oscuro 0..1 la cuerda se oscurece y engorda (pesa más).
    hilo_a=(x, y): hilo fino que baja de la cuerda hasta la nuca."""
    if k <= 0 or alpha <= 0: return
    a = alpha * k
    grosor = 6 + 4 * oscuro
    col = tuple(int(lerp(c1, c2, oscuro)) for c1, c2 in zip((120, 112, 138), (60, 52, 74)))
    pts = []
    for j in range(25):
        u = j / 24; x = cx - w / 2 + w * u
        pts.append((x * S, (cy + 8 * math.sin(u * 7 + t * 1.6)) * S))
    vivos = sum(1 for s in sueltos if s < 0.5)
    if vivos and a > 0:
        d.line(pts, fill=col + (int(a * 0.95),), width=int(grosor * S), joint="curve")
    else:
        d.line(pts, fill=(130, 240, 232, int(a * 0.25)), width=int(3 * S), joint="curve")
    if hilo_a and vivos:
        hx, hy = hilo_a
        d.line([(cx * S, (cy + 10) * S), ((cx + hx) / 2 * S, ((cy + hy) / 2 + 10 * math.sin(t * 2)) * S), (hx * S, hy * S)],
               fill=col + (int(a * 0.6),), width=int(3 * S), joint="curve")
    for i, s in enumerate(sueltos):
        u = (i + 1) / 4; nx = cx - w / 2 + w * u; ny = cy + 8 * math.sin(u * 7 + t * 1.6)
        r = (22 + 5 * oscuro) * (1 - s)
        if r > 1:
            d.ellipse([(nx - r) * S, (ny - r) * S, (nx + r) * S, (ny + r) * S], fill=col + (int(a),),
                      outline=(150, 142, 166, int(a)), width=int(3 * S))
            d.arc([(nx - r * 0.55) * S, (ny - r * 0.55) * S, (nx + r * 0.55) * S, (ny + r * 0.55) * S], 200, 520,
                  fill=(30, 26, 40, int(a)), width=int(3 * S))
        if 0 < s < 1:                                   # el nudo se abre en luz que sube
            py = ny - 140 * s
            d.ellipse([(nx - 8) * S, (py - 8) * S, (nx + 8) * S, (py + 8) * S], fill=(200, 255, 250, int(255 * (1 - s * 0.5))))
            g.ellipse([nx - 40, py - 40, nx + 40, py + 40], fill=(120, 240, 235, int(200 * (1 - s))))
        if s > 0.02:
            g.ellipse([nx - 22, ny - 22, nx + 22, ny + 22], fill=(120, 240, 235, int(90 * min(1, s * 3) * (1 - s))))

def despertador(d, x, y, t, suena=0.0, alpha=255, col=CREAM):
    """Despertador clásico de dos campanas (x, y = centro de la esfera). suena 0..1 vibra y saca ondas."""
    if alpha <= 0: return
    a = int(alpha); c = col + (a,)
    jx = 3 * math.sin(t * 60) * suena
    x = x + jx; r = 30
    for sgn in (-1, 1):
        d.pieslice([(x + sgn * 22 - 14) * S, (y - r - 18) * S, (x + sgn * 22 + 14) * S, (y - r + 10) * S], 180, 360, fill=c)
        d.line([((x + sgn * 20) * S, (y + r - 6) * S), ((x + sgn * 30) * S, (y + r + 10) * S)], fill=c, width=int(5 * S))
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(24, 30, 38, a), outline=c, width=int(5 * S))
    d.line([(x * S, y * S), (x * S, (y - 18) * S)], fill=c, width=int(4 * S))
    d.line([(x * S, y * S), ((x + 13) * S, (y + 4) * S)], fill=c, width=int(4 * S))
    if suena > 0:
        for i in range(2):
            ph = (t * 2.2 + i * 0.5) % 1; rr = r + 10 + 40 * ph
            for sgn in (-1, 1):
                d.arc([(x - rr) * S, (y - rr) * S, (x + rr) * S, (y + rr) * S], 300 if sgn > 0 else 200, 340 if sgn > 0 else 240,
                      fill=col + (int(a * suena * (1 - ph)),), width=int(3 * S))

def balanza(d, g, cx, top, ang, t, half=290, cadena=150, alpha=255, col=CREAM, brillo=0.0, plato_w=170):
    """Balanza grande con mástil desde el suelo. ang (rad) > 0 inclina hacia la derecha (el plato derecho baja).
    Devuelve ((xl, yl), (xr, yr)): centro superior de cada plato, para apilar cosas encima."""
    a = int(alpha); c = col + (a,)
    d.line([(cx * S, GY * S), (cx * S, (top + 10) * S)], fill=c, width=int(9 * S))
    d.polygon([((cx - 60) * S, GY * S), ((cx + 60) * S, GY * S), (cx * S, (GY - 40) * S)], fill=c)
    ca, sa = math.cos(ang), math.sin(ang)
    lx, ly = cx - half * ca, top - half * sa; rx_, ry_ = cx + half * ca, top + half * sa
    d.line([(lx * S, ly * S), (rx_ * S, ry_ * S)], fill=c, width=int(9 * S))
    star8(d, cx, top - 4, 22, t * 0.2, alpha=a)
    platos = []
    for (ex, ey) in ((lx, ly), (rx_, ry_)):
        py = ey + cadena
        for sgn in (-1, 1):
            d.line([(ex * S, ey * S), ((ex + sgn * plato_w / 2) * S, py * S)], fill=col + (int(a * 0.7),), width=int(3 * S))
        d.chord([(ex - plato_w / 2) * S, (py - 26) * S, (ex + plato_w / 2) * S, (py + 26) * S], 0, 180, fill=(24, 30, 38, a), outline=c, width=int(5 * S))
        d.line([((ex - plato_w / 2) * S, py * S), ((ex + plato_w / 2) * S, py * S)], fill=c, width=int(5 * S))
        d.ellipse([(ex - 9) * S, (ey - 9) * S, (ex + 9) * S, (ey + 9) * S], fill=c)
        platos.append((ex, py))
    if brillo > 0:
        g.ellipse([platos[1][0] - 160, platos[1][1] - 160, platos[1][0] + 160, platos[1][1] + 120], fill=(120, 240, 235, int(160 * brillo)))
    return platos

def bandeja(d, x, y, alpha=255, col=CREAM, vaso=True):
    """Bandeja de camarero sostenida en (x, y) (centro), con un vaso encima."""
    if alpha <= 0: return
    a = int(alpha); c = col + (a,)
    d.line([((x - 40) * S, y * S), ((x + 40) * S, y * S)], fill=c, width=int(6 * S))
    if vaso:
        d.polygon([((x - 12) * S, (y - 4) * S), ((x + 12) * S, (y - 4) * S), ((x + 15) * S, (y - 40) * S), ((x - 15) * S, (y - 40) * S)],
                  outline=c, fill=(110, 170, 200, int(a * 0.5)), width=int(3 * S))

def piedra_luz(d, g, x, y, r=18, alpha=255, rot=0.0):
    """Piedra de luz (un acto bueno que pesa): como piedra() pero dorada-turquesa y con halo."""
    if alpha <= 0: return
    piedra(d, x, y, r=r, alpha=alpha, rot=rot, col=(150, 240, 228))
    g.ellipse([x - r * 2.4, y - r * 2.4, x + r * 2.4, y + r * 2.4], fill=(120, 240, 235, int(140 * alpha / 255)))

# Poses del 26 nov: camarero con bandeja (brazo derecho delante), borde (señala con el dedo), sonríe/agradece (mano al pecho)
CAMARERO = dict(P["stand"]); CAMARERO.update(re=(30, -206), rh=(70, -196))
SENALA = dict(P["stand"]); SENALA.update(re=(52, -238), rh=(110, -250), head=(4, -300))
GRACIAS = dict(P["stand"]); GRACIAS.update(re=(22, -206), rh=(-6, -230), head=(6, -298))
DESPEREZA = dict(P["stand"]); DESPEREZA.update(le=(-40, -290), lh=(-30, -350), re=(40, -290), rh=(30, -350))
