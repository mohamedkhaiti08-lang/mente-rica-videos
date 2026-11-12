# Motor 3D (Blender, Workbench) para vídeos "¿Tienes prioridad?" de la cuenta Teórico B en 30s.
# Uso: python3 motor3d.py spec.json carpeta_frames ini fin      |  ... --sueltos f1 f2 ...
# El spec lo crea generar.py (semilla, hora, cruces, actores, señales y la línea de tiempo del coche).
import bpy, math, random, sys, json

spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]
FPS = 30
rng = random.Random(spec["seed"])
YS = spec["ys"]
NOCHE = spec["hora"] == "tarde"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = FPS
COL = sc.collection

def mesh_from_op(op, **kw):
    op(**kw); o = bpy.context.active_object; m = o.data; bpy.data.objects.remove(o); return m
CUBE = bpy.data.meshes.new("cubo")
CUBE.from_pydata([(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)], [],
                 [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]); CUBE.update()
CYL = {n: mesh_from_op(bpy.ops.mesh.primitive_cylinder_add, vertices=n, radius=1, depth=1) for n in (6, 8, 12, 20)}
ICO = mesh_from_op(bpy.ops.mesh.primitive_ico_sphere_add, subdivisions=1, radius=1)
SPH = mesh_from_op(bpy.ops.mesh.primitive_uv_sphere_add, segments=10, ring_count=6, radius=1)
TRI = bpy.data.meshes.new("tri"); TRI.from_pydata([(-.5, 0, .5), (.5, 0, .5), (0, 0, -.5), (-.5, .02, .5), (.5, .02, .5), (0, .02, -.5)], [], [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]); TRI.update()

def hexc(h, a=1.0):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)
def obj(mesh, c, s, col, parent=None, rot=None):
    o = bpy.data.objects.new("o", mesh); COL.objects.link(o)
    o.location, o.scale = c, s
    o.color = hexc(col) if isinstance(col, str) else col
    if rot: o.rotation_euler = rot
    if parent: o.parent = parent
    return o
def box(c, s, col, parent=None, rot=None): return obj(CUBE, c, s, col, parent, rot)
def cyl(c, r, h, col, n=12, rot=None, parent=None): return obj(CYL[n], c, (r, r, h), col, parent, rot)
def text(t, c, size, col, rot=(0, 0, 0), parent=None):
    cu = bpy.data.curves.new("t", "FONT"); cu.body = t; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = 0.01
    o = bpy.data.objects.new("t", cu); COL.objects.link(o); o.location, o.rotation_euler, o.color = c, rot, hexc(col)
    if parent: o.parent = parent
    return o
def keycol(o, frame, col):
    o.color = hexc(col); o.keyframe_insert("color", frame=frame)
def fcurves(o):
    ad = o.animation_data
    if not (ad and ad.action): return []
    act = ad.action
    if hasattr(act, "fcurves"): return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
def const_interp(o, modo='CONSTANT'):
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = modo

# ---------- paletas de ciudad (cambian con la semilla) ----------
PALETAS = [
 ['#f4c98f', '#ffe2b8', '#f2a96b', '#fff1d9', '#e9b277', '#ffd6a5'],       # cálida mediterránea
 ['#ffffff', '#eaf3ff', '#f7e7c6', '#dff1ec', '#ffe9e3', '#f3f3f3'],       # blanca costera
 ['#c9643b', '#d98a5b', '#b85538', '#e3a77a', '#cf7449', '#f0c29a'],       # ladrillo
 ['#f7b8c4', '#a7d8f0', '#ffe08a', '#b9e3b0', '#f9c99a', '#d7c4f0'],       # colores vivos
 ['#d9d3c7', '#c7d3dd', '#e8dccb', '#bfc9c1', '#efe6d6', '#d4c2ad'],       # moderna neutra
]
FACH = rng.choice(PALETAS)
FRANJA = ['#ff9f1a', '#1f7ae0', '#22a95b', '#e8392b', '#8e44ad']
PARK = ['#e74c3c', '#27ae60', '#f39c12', '#95a5a6', '#bdc3c7', '#f1c40f', '#34495e', '#c0392b', '#ffffff', '#2c3e50', '#16a085', '#d35400']
H_MIN, H_MAX = rng.choice([(11, 15), (13, 19), (15, 22)])
ARBOLES = rng.random() < 0.75

# ---------- calles ----------
ASF, ACERA, LINEA = '#45474e', '#d6d8dc', '#fafafa'
L0, L1 = -40, YS[-1] + 140
box((0, (L0 + L1) / 2, -0.05), (7.6, L1 - L0, 0.1), ASF)
for Y in YS: box((0, Y, -0.04), (180, 8, 0.1), ASF)
for sx in (-1, 1):
    box((sx * 5.0, (L0 + L1) / 2, 0.08), (2.4, L1 - L0, 0.16), ACERA)
    box((sx * 3.85, (L0 + L1) / 2, 0.1), (0.15, L1 - L0, 0.2), '#eeeeee')
for Y in YS:
    for sy in (-1, 1):
        box((48, Y + sy * 4.8, 0.08), (86, 1.6, 0.16), ACERA); box((-48, Y + sy * 4.8, 0.08), (86, 1.6, 0.16), ACERA)
    for k in range(7): box((-3.0 + k * 1.0, Y - 5.0, 0.012), (0.55, 2.2, 0.02), LINEA)
    for sx in (-1, 1):
        for k in range(6): box((sx * 5.0, Y - 2.8 + k * 1.1, 0.012), (2.2, 0.6, 0.02), LINEA)
    for xx in range(-60, 61, 6):                                             # eje de la transversal
        if abs(xx) > 7: box((xx, Y, 0.012), (2.6, 0.14, 0.02), '#e8e8e8')
for y in range(L0, int(L1), 6):
    if all(abs(y - Y) > 7 for Y in YS): box((-1.6, y, 0.012), (0.12, 2.5, 0.02), '#dedede')
for Y in YS[:]:                                                              # flechas pintadas
    yy = Y - 22
    box((1.4, yy, 0.012), (0.25, 2.2, 0.02), LINEA); obj(TRI, (1.4, yy + 1.55, 0.012), (0.9, 1, 0.9), LINEA, rot=(math.pi / 2, 0, 0))

# ---------- edificios ----------
blocks = [(L0, YS[0] - 5.6)] + [(YS[i] + 5.6, YS[i + 1] - 5.6) for i in range(len(YS) - 1)] + [(YS[-1] + 5.6, L1)]
for sx in (-1, 1):
    for y0, y1 in blocks:
        y = y0
        while y < y1 - 2:
            L = min(rng.uniform(9, 15), y1 - y); h = rng.uniform(H_MIN, H_MAX); h = 4.2 + 3.0 * round((h - 4.2) / 3.0)
            col = rng.choice(FACH); fx = sx * 6.2
            box((sx * 20.2, y + L / 2, h / 2), (28, L, h), col)
            box((sx * 6.35, y + L / 2, h + 0.35), (0.35, L, 0.7), col)                       # pretil
            if rng.random() < 0.4: box((sx * 12, y + L / 2, h + 0.9), (2.0, 2.0, 1.8), '#9aa3ad')  # depósito/caseta
            box((fx - sx * 0.05, y + L / 2, 3.25), (0.14, L, 0.35), rng.choice(FRANJA))
            yy = y + 1.6
            while yy < y + L - 1.2:
                r = rng.random()
                if r < 0.45:                                                         # persiana de local
                    box((fx - sx * 0.06, yy, 1.35), (0.1, 2.6, 2.7), '#9ba1a8')
                    for z in (0.5, 0.95, 1.4, 1.85, 2.3): box((fx - sx * 0.12, yy, z), (0.04, 2.5, 0.06), '#7d838b')
                elif r < 0.75:                                                       # tienda con toldo
                    box((fx - sx * 0.06, yy, 1.3), (0.1, 2.6, 2.4), '#33475b')
                    box((fx - sx * 0.08, yy, 1.3), (0.08, 2.7, 0.12), '#f2f2f2')
                    obj(CUBE, (fx - sx * 0.65, yy, 2.85), (1.2, 2.8, 0.12), rng.choice(FRANJA), rot=(0, sx * 0.35, 0))
                else:                                                                # portal
                    box((fx - sx * 0.06, yy, 1.25), (0.1, 1.3, 2.5), '#6b4a33')
                    box((fx - sx * 0.08, yy, 2.62), (0.1, 1.6, 0.18), '#f2f2f2')
                yy += 3.4
            z = 4.6; balc = rng.random() < 0.8
            while z < h - 1.0:
                yy = y + 1.8
                while yy < y + L - 1.2:
                    lit = NOCHE and rng.random() < 0.35
                    box((fx - sx * 0.03, yy, z + 1.0), (0.08, 1.55, 2.15), '#fbfbf7')       # marco
                    box((fx - sx * 0.06, yy, z + 1.0), (0.08, 1.3, 1.9), '#ffd27a' if lit else rng.choice(['#2f4766', '#35506f', '#283c58']))
                    if balc:
                        box((fx - sx * 0.6, yy, z), (1.2, 2.3, 0.14), '#3b3b40')
                        box((fx - sx * 1.17, yy, z + 0.5), (0.05, 2.3, 0.9), '#2a2a2e')
                        if rng.random() < 0.3: obj(ICO, (fx - sx * 0.85, yy + 0.7, z + 0.45), (0.32, 0.32, 0.32), rng.choice(['#3fa33a', '#2e8b57', '#e84393']))
                    else:
                        box((fx - sx * 0.12, yy, z + 0.02), (0.2, 1.6, 0.12), '#f2f2f2')
                    if rng.random() < 0.12: box((fx - sx * 0.35, yy + 0.95, z + 0.4), (0.6, 0.5, 0.45), '#d9dde2')  # aire acondicionado
                    yy += 3.3
                z += 3.0
            y += L + 0.3

# ---------- mobiliario: árboles y farolas ----------
def arbol(x, y):
    cyl((x, y, 1.3), 0.14, 2.6, '#7a5235', 8)
    g = rng.choice(['#3fae49', '#2f9e44', '#58b947'])
    obj(ICO, (x, y, 3.2), (1.2, 1.2, 1.1), g); obj(ICO, (x + 0.4, y + 0.3, 3.8), (0.8, 0.8, 0.75), g)
    box((x, y, 0.17), (1.1, 1.1, 0.04), '#6b5a48')
def farola(x, y, sx):
    cyl((x, y, 2.6), 0.07, 5.2, '#3d4148', 8)
    box((x - sx * 0.45, y, 5.15), (0.9, 0.12, 0.08), '#3d4148'); box((x - sx * 0.85, y, 5.05), (0.45, 0.28, 0.14), '#fff3c4' if NOCHE else '#e9e9e9')
for y in range(L0 + 8, int(L1), 13):
    if all(not (-24 < y - Y < 12) for Y in YS):
        if ARBOLES and rng.random() < 0.8: arbol(4.7, y + 3)
        if rng.random() < 0.7: farola(-4.3, y - 2, -1)

# ---------- vehículos ----------
def car(col, name, amb=False):
    e = bpy.data.objects.new(name, None); COL.objects.link(e)
    body = '#ffffff' if amb else col
    box((0, 0, 0.62), (1.85, 4.3, 0.75), body, e)
    box((0, -0.25, 1.27), (1.66, 2.2, 0.56), body, e)
    if amb:
        box((0, -0.1, 1.15), (1.68, 2.6, 1.0), '#ffffff', e)
        for sx in (-1, 1):
            box((sx * 0.935, 0, 0.85), (0.02, 4.2, 0.22), '#ffd200', e)
            box((sx * 0.94, -0.6, 1.25), (0.02, 0.9, 0.28), '#e1251b', e); box((sx * 0.94, -0.6, 1.25), (0.02, 0.28, 0.9), '#e1251b', e)
        box((0, -0.6, 1.66), (0.9, 0.28, 0.02), '#e1251b', e); box((0, -0.6, 1.66), (0.28, 0.9, 0.02), '#e1251b', e)
    box((0, 0.88, 1.24), (1.6, 0.06, 0.5), '#1d2838', e, rot=(-0.5, 0, 0))
    box((0, -1.38, 1.24), (1.6, 0.06, 0.5), '#1d2838', e, rot=(0.55, 0, 0))
    for sx in (-1, 1):
        box((sx * 0.84, -0.25, 1.27), (0.02, 1.95, 0.38), '#1d2838', e)
        box((sx * 0.935, 0.2, 0.75), (0.02, 0.03, 0.55), '#00000022' if False else '#2b2b2b', e)
        box((sx * 1.0, 0.55, 1.02), (0.18, 0.1, 0.12), body, e)                       # retrovisores
        box((sx * 0.6, -2.16, 0.8), (0.44, 0.04, 0.17), '#ff2e1f', e)
        box((sx * 0.62, 2.16, 0.78), (0.4, 0.04, 0.15), '#fff7d6', e)
        for sy in (-1.35, 1.35):
            cyl((sx * 0.86, sy, 0.36), 0.36, 0.28, '#151515', 12, rot=(0, math.pi / 2, 0), parent=e)
            cyl((sx * 1.0, sy, 0.36), 0.2, 0.02, '#b7bcc2', 12, rot=(0, math.pi / 2, 0), parent=e)
    box((0, -2.17, 0.52), (0.66, 0.03, 0.18), '#f6f6f6', e)
    box((0, 0, 0.21), (1.7, 4.0, 0.15), '#202020', e)
    luces = []
    if amb:
        for k, sx in enumerate((-1, 1)):
            luces.append(box((sx * 0.45, 0.6, 1.72), (0.55, 0.32, 0.16), '#1e5bff', e))
    return e, luces

for y in range(L0 + 6, int(L1), 6):
    if all(abs(y - Y) > 11 for Y in YS) and rng.random() < 0.85:
        c, _ = car(rng.choice(PARK), "aparcado"); c.location = (-2.75, y + rng.uniform(-0.4, 0.4), 0)

def peaton(col, name):
    e = bpy.data.objects.new(name, None); COL.objects.link(e)
    box((0, 0, 1.25), (0.5, 0.32, 0.75), col, e)
    lg = [box((sx * 0.12, 0, 0.45), (0.18, 0.2, 0.9), '#2c3e60', e) for sx in (-1, 1)]
    obj(SPH, (0, 0, 1.86), (0.2, 0.2, 0.2), '#e0b48a', e); obj(SPH, (0, 0.02, 1.95), (0.21, 0.21, 0.12), '#3b2a20', e)
    return e, lg
for k in range(rng.randint(5, 9)):
    sx = rng.choice([-1, 1]); y = rng.uniform(L0 + 10, L1 - 20)
    if all(abs(y - Y) > 8 for Y in YS):
        p, _ = peaton(rng.choice(['#e74c3c', '#2980b9', '#e67e22', '#27ae60', '#9b59b6', '#f1c40f']), "p"); p.location = (sx * 4.9, y, 0.16)

# ---------- señales ----------
def poste(x, y, h=2.7): cyl((x, y, h / 2), 0.05, h, '#a3a9b0', 8)
def face_offset(rz, d): return (math.sin(rz) * d, -math.cos(rz) * d)
def stop_sign(x, y, rz, r=0.62):
    poste(x, y)
    o = cyl((x, y, 2.85), r, 0.04, '#d61f17', 8); o.rotation_euler = (math.pi / 2, math.pi / 8, rz)
    o2 = cyl((x, y, 2.85), r * 1.08, 0.03, '#ffffff', 8); o2.rotation_euler = (math.pi / 2, math.pi / 8, rz)
    dx, dy = face_offset(rz, 0.05); o2.location = (x - dx * 0.4, y - dy * 0.4, 2.85)
    dx, dy = face_offset(rz, 0.04); text("STOP", (x + dx, y + dy, 2.83), r * 0.62, '#ffffff', rot=(math.pi / 2, 0, rz))
def ceda_sign(x, y, rz, r=0.75):
    poste(x, y)
    obj(TRI, (x, y, 2.75), (r * 1.15, 1, r), '#d61f17', rot=(0, 0, rz))
    dx, dy = face_offset(rz, 0.03)
    obj(TRI, (x + dx, y + dy, 2.79), (r * 0.72, 1, r * 0.62), '#ffffff', rot=(0, 0, rz))
def semaforo(x, y, rz, estados):
    """estados: [(t, 'rojo'|'verde')]"""
    poste(x, y, 3.0)
    box((x, y, 3.55), (0.42, 0.36, 1.25), '#22252b', rot=(0, 0, rz))
    dx, dy = face_offset(rz, 0.2)
    lamps = {}
    for nm, z in (("rojo", 3.95), ("ambar", 3.55), ("verde", 3.15)):
        lamps[nm] = cyl((x + dx, y + dy, z), 0.15, 0.06, '#333333', 12, rot=(math.pi / 2, 0, rz))
    ON = {"rojo": '#ff2a1a', "ambar": '#ffb400', "verde": '#22ff6a'}; OFF = {"rojo": '#4a1a17', "ambar": '#4a3a12', "verde": '#173d22'}
    for t, st in estados:
        for nm, lo in lamps.items(): keycol(lo, round(t * FPS), ON[nm] if nm == st else OFF[nm])
    for lo in lamps.values(): const_interp(lo)

for s in spec["senales"]:
    k = s["tipo"]
    if k == "stop": stop_sign(s["x"], s["y"], math.radians(s["rz"]))
    elif k == "ceda": ceda_sign(s["x"], s["y"], math.radians(s["rz"]))
    elif k == "semaforo": semaforo(s["x"], s["y"], math.radians(s["rz"]), s["estados"])
    elif k == "linea": box((s["x"], s["y"], 0.014), (s["w"], s["h"], 0.02), LINEA)
    elif k == "dientes":
        for i in range(int(s["n"])):
            obj(TRI, (s["x0"] + i * s["paso"], s["y"], 0.014), (0.55, 1, 0.7), LINEA, rot=(math.pi / 2, 0, math.radians(s.get("rz", 0))))
    elif k == "texto_suelo": text(s["txt"], (s["x"], s["y"], 0.015), s["size"], '#ffffff', rot=(0, 0, math.radians(s.get("rz", 0))))

# ---------- actores con movimiento ----------
def keyloc(o, t, loc, rz=None):
    o.location = loc; o.keyframe_insert("location", frame=round(t * FPS))
    if rz is not None: o.rotation_euler = (0, 0, math.radians(rz)); o.keyframe_insert("rotation_euler", frame=round(t * FPS))
yo, _ = car(spec["color_yo"], "yo")
for t, y in spec["yo"]: keyloc(yo, t, (1.2, y, 0))
for a in spec["actores"]:
    if a["tipo"] == "peaton":
        o, legs = peaton(a["color"], "peaton")
        for t, x, y, rz in a["keys"]: keyloc(o, t, (x, y, 0.08), rz)
        const_interp(o, 'LINEAR')
        # pasos: balanceo de piernas mientras camina
        t0, t1 = a["camina"]
        for i, lg in enumerate(legs):
            n = int((t1 - t0) / 0.3)
            for k in range(n + 1):
                lg.rotation_euler = (0.45 * (1 if (k + i) % 2 else -1), 0, 0); lg.keyframe_insert("rotation_euler", frame=round((t0 + k * 0.3) * FPS))
            lg.rotation_euler = (0, 0, 0); lg.keyframe_insert("rotation_euler", frame=round((t1 + 0.2) * FPS))
    else:
        o, luces = car(a["color"], a["tipo"], amb=a["tipo"] == "ambulancia")
        for t, x, y, rz in a["keys"]: keyloc(o, t, (x, y, 0), rz)
        if luces:
            t = 0.0; k = 0
            while t < spec["dur"]:
                for i, lo in enumerate(luces): keycol(lo, round(t * FPS), '#2f6bff' if (k + i) % 2 == 0 else '#0b1a40')
                t += 0.18; k += 1
            for lo in luces: const_interp(lo)

# ---------- cámara ----------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("c")); COL.objects.link(cam)
cam.parent = yo; cam.location = (-0.8, -7.8, 4.1); cam.rotation_euler = (math.radians(74.5), 0, math.radians(-1.5))
cam.data.lens = 17; cam.data.sensor_width = 36; sc.camera = cam

# ---------- render ----------
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.film_transparent = True
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'OBJECT'
sh.show_shadows = True; sh.shadow_intensity = 0.42 if not NOCHE else 0.5
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.cavity_ridge_factor = 0.6; sh.cavity_valley_factor = 0.8
sh.show_specular_highlight = True
try: sh.studio_light = 'outdoor.sl'
except Exception: pass
sc.display.light_direction = (0.55, -0.35, 0.76) if not NOCHE else (0.85, -0.25, 0.45)
sc.display.render_aa = 'FXAA'
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'

if "--sueltos" in sys.argv: frames = [int(x) for x in sys.argv[sys.argv.index("--sueltos") + 1:]]
else: frames = range(int(sys.argv[3]), int(sys.argv[4]))
for fr in frames:
    sc.frame_set(fr); sc.render.filepath = f"{OUT}/{fr:04d}.png"
    bpy.ops.render.render(write_still=True)
