# Genera un vídeo "¿Tienes prioridad?" completo para Teórico B en 30s.
# Uso: KOKORO_DIR=/ruta python3 generar.py --seed 20261113 --out carpeta [--tipos der_sin,peaton,stop_otro] [--evitar a,b] [--hora dia|tarde]
#      [--prueba 3.5 9 20]  (solo renderiza esos segundos y monta fotogramas sueltos para revisar)
import argparse, json, math, os, random, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter
from tipos import TIPOS, INTROS, FINALES, ORD, elegir

AQUI = os.path.dirname(os.path.abspath(__file__))
FPS, W, H = 30, 1080, 1920
YS = [40.0, 85.0, 130.0]
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAVY, YEL, BLUE, GREEN, RED, GRAYB = (18, 32, 72), (255, 196, 20), (31, 95, 191), (40, 170, 80), (226, 58, 44), (215, 220, 228)
COLORES_YO = ['#1e4fd8', '#1565c0', '#0d47a1']
OTROS = ['#e53935', '#ffffff', '#8e9eab', '#43a047', '#fb8c00', '#fdd835', '#6d4c41', '#00897b', '#5e35b1', '#212121']

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, required=True); ap.add_argument("--out", required=True)
ap.add_argument("--tipos"); ap.add_argument("--evitar", default=""); ap.add_argument("--hora")
ap.add_argument("--prueba", nargs="*", type=float)
A = ap.parse_args()
rng = random.Random(A.seed); os.makedirs(A.out, exist_ok=True)
tipos = A.tipos.split(",") if A.tipos else elegir(rng, set(filter(None, A.evitar.split(","))))
hora = A.hora or rng.choice(["dia", "dia", "tarde"])

# ---------- guion ----------
cr = []
for i, t in enumerate(tipos):
    T = TIPOS[t]
    cr.append(dict(tipo=t, lado=rng.choice(T["lados"]), resp=T["resp"], pregunta=T["pregunta"], rotulo=T["rotulo"],
                   q=f"Cruce {ORD[i]}. " + rng.choice(T["voz_q"]), r=rng.choice(T["voz_r"])))
intro, final = rng.choice(INTROS), rng.choice(FINALES)

# ---------- voz ----------
from kokoro_onnx import Kokoro
KD = os.environ.get("KOKORO_DIR", ".")
kk = Kokoro(os.path.join(KD, "kokoro-v1.0.onnx"), os.path.join(KD, "voices-v1.0.bin"))
def voz(txt, nombre):
    a, sr = kk.create(txt, voice="ef_dora", speed=1.1, lang="es")
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0] - 240): idx[-1] + 480]
    p = os.path.join(A.out, nombre + ".wav"); sf.write(p, a, sr); return p, len(a) / sr
v_intro = voz(intro, "v_intro"); v_fin = voz(final, "v_fin")
for i, c in enumerate(cr): c["vq"] = voz(c["q"], f"v{i}q"); c["vr"] = voz(c["r"], f"v{i}r")

# ---------- línea de tiempo ----------
STOP = [Y - 10.0 for Y in YS]
yo = [(0.0, 4.0)]
A_i, T0 = 3.0, 2.6
for i, c in enumerate(cr):
    dq, dr = c["vq"][1], c["vr"][1]
    c["T0"] = T0; c["tq"] = T0 + 0.2
    c["C"] = max(A_i + 0.2, c["tq"] + dq + 0.15); c["R"] = c["C"] + 3.0; c["tr"] = c["R"] + 0.1
    c["E"] = c["tr"] + dr + 0.5
    c["L"] = c["R"] + (0.9 if c["resp"] == "SÍ" else 2.6)
    yo += [(A_i, STOP[i]), (c["L"], STOP[i])]
    A_i = c["L"] + 3.6; T0 = max(c["E"] + 0.1, A_i - 1.4)
FIN = cr[-1]["E"] + 0.1
DUR = round(FIN + 0.2 + v_fin[1] + 0.8, 2)
yo.append((DUR + 0.5, STOP[-1] + (DUR + 0.5 - cr[-1]["L"]) * 8))

# ---------- actores y señales ----------
actores, senales = [], []
for i, c in enumerate(cr):
    Y, C, R, L, t, lado = YS[i], c["C"], c["R"], c["L"], c["tipo"], c["lado"]
    der = lado == "der"
    sgn = 1 if der else -1
    lane_y, rz = (Y + 2.0, 90) if der else (Y - 2.0, -90)
    wait_x = 8.9 if der else -7.6
    pasa_otro = c["resp"] == "NO" or t == "sem_rojo"
    col = rng.choice(OTROS)
    if TIPOS[t]["actor"] == "peaton":
        x0, x1 = (-5.4, 5.3) if not der else (5.4, -5.3)
        prz = -90 if x1 > x0 else 90
        actores.append(dict(tipo="peaton", color=rng.choice(['#e74c3c', '#8e44ad', '#f39c12', '#16a085']),
                            keys=[(0, x0, Y - 5.0, prz), (C - 1.4, x0, Y - 5.0, prz), (R + 2.6, x1, Y - 5.0, prz)], camina=(C - 1.4, R + 2.6)))
    else:
        kind = "ambulancia" if TIPOS[t]["actor"] == "ambulancia" else "coche"
        keys = [(0, sgn * 60, lane_y, rz), (C - 4.5, sgn * 42, lane_y, rz), (C - 0.5, wait_x, lane_y, rz)]
        if pasa_otro: keys += [(R + 0.2, wait_x, lane_y, rz), (R + 2.3, -sgn * 48, lane_y, rz)]
        else: keys += [(L + 2.0, wait_x, lane_y, rz), (L + 4.6, -sgn * 48, lane_y, rz)]
        actores.append(dict(tipo=kind, color=col, keys=keys, lado=lado, C=C, R=R))
    linea_mia = dict(tipo="linea", x=0, y=Y - 6.6, w=7.6, h=0.4)
    ox, oy = (6.6, Y + 4.9) if der else (-5.1, Y - 4.5)
    orz = 20 if der else -15
    if t == "stop_otro": senales += [dict(tipo="stop", x=ox, y=oy, rz=orz), dict(tipo="linea", x=sgn * 6.5, y=lane_y, w=0.4, h=4.0)]
    if t == "ceda_otro": senales += [dict(tipo="ceda", x=ox, y=oy, rz=orz), dict(tipo="linea", x=sgn * 6.5, y=lane_y, w=0.25, h=4.0)]
    if t == "stop_mio": senales += [dict(tipo="stop", x=4.7, y=Y - 7.6, rz=0), linea_mia]
    if t == "ceda_mio": senales += [dict(tipo="ceda", x=4.7, y=Y - 7.6, rz=0), dict(tipo="dientes", x0=-3.3, y=Y - 6.8, n=8, paso=0.95, rz=180)]
    if t in ("sem_rojo", "sem_verde"):
        cx, cy, crz = (6.9, Y + 5.0, 90) if der else (-6.9, Y - 5.0, -90)
        if t == "sem_rojo":
            senales += [dict(tipo="semaforo", x=4.75, y=Y - 7.2, rz=0, estados=[(0, "rojo"), (R + 2.0, "verde")]),
                        dict(tipo="semaforo", x=cx, y=cy, rz=crz, estados=[(0, "verde"), (R + 1.4, "ambar"), (R + 2.0, "rojo")]), linea_mia]
        else:
            senales += [dict(tipo="semaforo", x=4.75, y=Y - 7.2, rz=0, estados=[(0, "verde")]),
                        dict(tipo="semaforo", x=cx, y=cy, rz=crz, estados=[(0, "rojo")]), linea_mia]

spec = dict(seed=A.seed, hora=hora, ys=YS, dur=DUR, yo=yo, color_yo=rng.choice(COLORES_YO), actores=actores, senales=senales)
json.dump(spec, open(os.path.join(A.out, "spec.json"), "w"), indent=1, ensure_ascii=False)
guion = dict(seed=A.seed, hora=hora, tipos=tipos, intro=intro, final=final, dur=DUR,
             cruces=[{k: v for k, v in c.items() if k not in ("vq", "vr")} for c in cr])
json.dump(guion, open(os.path.join(A.out, "guion.json"), "w"), indent=1, ensure_ascii=False)
print("TIPOS", tipos, "HORA", hora, "DUR", DUR)

# ---------- render 3D (2 procesos) ----------
FR = os.path.join(A.out, "frames"); os.makedirs(FR, exist_ok=True)
NF = int(DUR * FPS)
motor = os.path.join(AQUI, "motor3d.py"); sp = os.path.join(A.out, "spec.json")
if A.prueba:
    fr = [str(min(NF - 1, int(t * FPS))) for t in A.prueba]
    subprocess.run([sys.executable, motor, sp, FR, "--sueltos", *fr], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
else:
    falta = [i for i in range(NF) if not os.path.exists(f"{FR}/{i:04d}.png")]
    if falta:
        a, b = falta[0], NF; m = (a + b) // 2
        ps = [subprocess.Popen([sys.executable, motor, sp, FR, str(x), str(y)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for x, y in ((a, m), (m, b))]
        for p in ps: p.wait()
    falta = [i for i in range(NF) if not os.path.exists(f"{FR}/{i:04d}.png")]
    if falta: sys.exit(f"ERROR: faltan {len(falta)} fotogramas")

# ---------- montaje ----------
def ease(x): x = max(0., min(1., x)); return 1 - (1 - x) ** 3
def font(s): return ImageFont.truetype(FB, s)
y = np.linspace(0, 1, H)[:, None]
if hora == "dia": top, hor = np.array([92, 160, 235.]), np.array([238, 244, 250.])
else: top, hor = np.array([70, 90, 170.]), np.array([255, 178, 110.])
SKY = Image.fromarray(np.repeat(((top + (hor - top) * np.clip(y / 0.42, 0, 1) ** 1.5))[:, None, :], W, axis=1).astype(np.uint8))
VIG = Image.fromarray((255 * np.clip(1 - 0.35 * (((np.linspace(-1, 1, W)[None, :]) ** 2 * 0.6 + (np.linspace(-1, 1, H)[:, None]) ** 2 * 0.4)), 0, 1)).astype(np.uint8))

def card(d, header, title, hcol, htxt, t, t0):
    k = ease((t - t0) / 0.3); dy = int((1 - k) * -60)
    if k <= 0: return
    x0, x1 = 50, 1030
    d.rounded_rectangle([x0, 200 + dy, x1, 400 + dy], 34, fill=(255, 255, 255, int(245 * k)))
    d.rounded_rectangle([x0, 200 + dy, x1, 286 + dy], 34, fill=hcol + (int(255 * k),))
    d.rectangle([x0, 250 + dy, x1, 286 + dy], fill=hcol + (int(255 * k),))
    d.text((W / 2, 244 + dy), header, font=font(46), fill=htxt + (int(255 * k),), anchor="mm")
    d.text((W / 2, 344 + dy), title, font=font(66), fill=NAVY + (int(255 * k),), anchor="mm")
def buttons(d, t, t0, reveal, good):
    k = ease((t - t0) / 0.3)
    if k <= 0: return
    for lab, x0 in (("SÍ", 90), ("NO", 570)):
        fill, tc = (255, 255, 255, int(240 * k)), NAVY + (int(255 * k),)
        ok = t >= reveal and lab == good
        if t >= reveal: fill, tc = (GREEN + (255,), (255, 255, 255, 255)) if ok else (GRAYB + (200,), (150, 155, 165, 255))
        sc = 1 + (0.08 * math.sin(min(1, (t - reveal) / 0.35) * math.pi) if ok else 0)
        cx, cy, w, h = x0 + 210, 490, 420 * sc, 112 * sc
        d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 58, fill=fill)
        d.text((cx - (30 if ok else 0), cy), lab, font=font(int(68 * sc)), fill=tc, anchor="mm")
        if ok: d.line([(cx + 70, cy), (cx + 96, cy + 26), (cx + 146, cy - 30)], fill=(255, 255, 255, 255), width=14, joint="curve")
def explain(d, t, reveal, txt):
    k = ease((t - reveal - 0.25) / 0.3)
    if k <= 0: return
    f = font(42 if len(txt) < 30 else 37); w = d.textlength(txt, font=f) + 80
    cy = 640 + int((1 - k) * 30)
    d.rounded_rectangle([W / 2 - w / 2, cy - 46, W / 2 + w / 2, cy + 46], 46, fill=RED + (int(250 * k),))
    d.text((W / 2, cy), txt, font=f, fill=(255, 255, 255, int(255 * k)), anchor="mm")
def countdown(d, t, c0):
    if not (c0 <= t < c0 + 3): return
    n = 3 - int(t - c0); fr = (t - c0) % 1; cx, cy, r = W / 2, 672, 104
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(18, 28, 52, 190))
    d.arc([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], -90, -90 + 360 * (t - c0) / 3, fill=YEL + (255,), width=16)
    s = 1 + 0.25 * (1 - ease(fr / 0.25))
    d.text((cx, cy + 4), str(n), font=font(int(116 * s)), fill=(255, 255, 255, 255), anchor="mm")
def overlay(t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if t < cr[0]["T0"]:
        card(d, "EXAMEN PRÁCTICO", "¿Circularías bien?", BLUE, (255, 255, 255), t, -0.3)
        if t > 0.5: d.text((W / 2, 480), "3 CRUCES · 3 SEGUNDOS", font=font(50), fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=NAVY + (255,))
    for i, c in enumerate(cr):
        if c["T0"] <= t < c["E"]:
            card(d, f"CRUCE {i + 1} DE 3", c["pregunta"], YEL, NAVY, t, c["T0"])
            buttons(d, t, c["C"] - 0.6, c["R"], c["resp"]); countdown(d, t, c["C"])
            if t >= c["R"]: explain(d, t, c["R"], c["rotulo"])
    if t >= FIN:
        card(d, "¿CUÁNTAS HAS ACERTADO?", "Dímelo en comentarios", BLUE, (255, 255, 255), t, FIN)
        k = ease((t - FIN - 0.6) / 0.3)
        if k > 0:
            d.rounded_rectangle([W / 2 - 230, 450, W / 2 + 230, 550], 50, fill=YEL + (int(255 * k),))
            d.text((W / 2, 500), "0 · 1 · 2 · 3 ↓", font=font(54), fill=NAVY + (int(255 * k),), anchor="mm")
    return im
def frame(i):
    t = i / FPS; base = SKY.copy()
    f3 = Image.open(f"{FR}/{min(i, NF - 1):04d}.png").convert("RGBA")
    rgb = f3.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(1.5); rgb = ImageEnhance.Brightness(rgb).enhance(1.14); rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
    if hora == "tarde":
        r, g, b = rgb.split(); rgb = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.08 + 8))), g, b.point(lambda v: int(v * 0.9))))
    f3 = Image.merge("RGBA", (*rgb.split(), f3.split()[3])); base.paste(f3, (0, 0), f3)
    glow = base.point(lambda v: max(0, v - 200) * 3).filter(ImageFilter.GaussianBlur(14))      # brillo suave en luces
    base = Image.blend(base, Image.composite(base, Image.new("RGB", (W, H)), VIG), 0.6)
    base = Image.fromarray(np.clip(np.asarray(base, np.int16) + np.asarray(glow, np.int16) // 3, 0, 255).astype(np.uint8))
    base = base.filter(ImageFilter.UnsharpMask(1.2, 60, 2))
    ov = overlay(t)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(ov.split()[3].point(lambda v: int(v * 0.45)))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); base = base.convert("RGBA")
    base.paste(sh, (0, 8), sh); base.paste(ov, (0, 0), ov)
    return base.convert("RGB")

if A.prueba:
    for t in A.prueba: frame(min(NF - 1, int(t * FPS))).save(os.path.join(A.out, f"prueba_{t}.png"))
    sys.exit()

# audio
SR = 24000; out = np.zeros(int(SR * DUR), np.float32)
def put(a, t):
    i = int(t * SR); out[i:i + len(a)] += a[:max(0, len(out) - i)]
def tone(f, dur, v, dec=6):
    x = np.arange(int(dur * SR)) / SR; return (v * np.sin(2 * np.pi * f * x) * np.exp(-x * dec)).astype(np.float32)
put(sf.read(v_intro[0], dtype="float32")[0], 0.15); put(sf.read(v_fin[0], dtype="float32")[0], FIN + 0.2)
for i, c in enumerate(cr):
    put(sf.read(c["vq"][0], dtype="float32")[0], c["tq"]); put(sf.read(c["vr"][0], dtype="float32")[0], c["tr"])
    put(tone(660, 0.35, 0.10, 3), c["T0"])
    for k in range(3): put(tone(1000, 0.16, 0.16, 8), c["C"] + k)
    put(tone(1320, 0.9, 0.14, 4), c["R"]); put(tone(1760, 0.7, 0.08, 4), c["R"] + 0.08)
    if c["tipo"] == "ambulancia":                     # sirena de dos tonos que se acerca y se aleja
        t0, t1 = c["C"] - 3.5, c["R"] + 3.0; n = int((t1 - t0) * SR); x = np.arange(n) / SR
        f = np.where((x % 1.0) < 0.5, 660, 880); ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.interp(x, [0, (c["R"] + 0.6 - t0), t1 - t0], [0.01, 0.07, 0.01])
        put((np.sin(ph) * env).astype(np.float32), t0)
sf.write(os.path.join(A.out, "audio.wav"), np.clip(out, -1, 1), SR)
mp4 = os.path.join(A.out, "video.mp4")
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-i", os.path.join(A.out, "audio.wav"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                      "-c:a", "aac", "-b:a", "128k", "-shortest", mp4], stdin=subprocess.PIPE)
for i in range(NF): p.stdin.write(frame(i).tobytes())
p.stdin.close(); p.wait()
print("OK", mp4, DUR)
