# Estilo Noche · «LUEGO, MAMÁ» vs «YA VOY, MAMÁ» · "¿Sabes a quién manda el islam tratar mejor que a nadie?" (Sahih al-Bujari 5971)
# Explorar: acto concreto del día a día (ayudar a tu madre) + giro con cuenta atrás del hadiz «tu madre, tu madre, tu madre… tu padre».
# Dos madres con pañuelo cargan una caja pesada y piden ayuda. Uno sigue con el móvil («LUEGO…»): su madre carga sola, sudando,
# y se va apagando (gris); día 30 ya ni le pide nada y se sienta sola; grietas bajo el suelo.
# El otro deja el móvil, va y le coge la caja: a la madre se le enciende la luz y su dua sube al cielo como un corazón de luz;
# le crecen raíces. Giro: tarjeta con «TU MADRE» ×3 que aparece al ritmo de la voz y «TU PADRE» después; al tercer «tu madre»
# el primer hijo guarda el móvil y se gira hacia su madre (final que enlaza con el principio).
# Objetos nuevos: madre con pañuelo (velo), poses CARGA/LLEVA, corazón de luz. Piezas en noche/piezas.py (29 nov).
# Uso: python3 2026-11-29-1800-tu-madre.py salida.mp4 [t1 t2 ... fotogramas]   (NOVOZ=1 reutiliza el guion)
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes a quién manda el islam tratar mejor que a nadie?",
         "Su madre les pide ayuda.",
         "Uno dice: luego, mamá.",
         "El otro deja el móvil, y va.",
         "Día diez.",
         "Día treinta.",
         "¿Quién merece más tu cariño?",
         "Un hombre le preguntó al Profeta, la paz sea con él: ¿quién merece más mi buen trato? Tu madre.",
         "¿Y después? Tu madre.",
         "¿Y después? Tu madre.",
         "¿Y después? Tu padre.",
         "Di: ya voy, mamá.",
         "¿Cuándo fue la última vez que le dijiste: te quiero?"]
PAUSAS = [0.3, 0.4, 0.6, 0.7, 1.8, 1.5, 1.3, 0.35, 0.35, 0.35, 0.6, 0.5, 0.9]
def SFX(s): return [dict(t=s[3] + 1.6, f=1320, dur=0.8, v=0.05),
                    dict(t=s[8] - 0.45, f=990, dur=1.2, v=0.06), dict(t=s[9] - 0.45, f=1110, dur=1.2, v=0.06), dict(t=s[10] - 0.45, f=1320, dur=1.4, v=0.06),
                    dict(t=s[11], f=660, dur=2.0, v=0.07), dict(t=s[11] + 0.15, f=990, dur=2.0, v=0.05)]
GUION = os.path.join(HERE, "2026-11-29-1800-tu-madre.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, s3, t10, t30, tq, thad, tm2, tm3, tpad, tfin, task = starts
print("DUR", DUR, starts)

ML, HL = 110, 330             # madre e hijo de la izquierda
HR, MR = 650, 870             # hijo y madre de la derecha
LXC, RXC = 230, 760
KM = 0.88                     # escala de las madres
TEAL = (130, 240, 232)
MOVIL = dict(P["stand"]); MOVIL.update(head=(4, -296), re=(30, -204), rh=(14, -244), le=(-26, -212), lh=(-32, -150))
# momentos de "tu madre" (cuando la voz lo dice: final de cada frase)
TM = [ends[7] - 0.75, ends[8] - 0.75, ends[9] - 0.75]
TP = ends[10] - 0.75
SENT_SOLA = dict(Z.SENTADO_CANSADO)

def caja_en(d, x, y, alpha=255, gris=0.0):
    Z.caja(d, x, y, alpha=alpha, w=92, h=70, gris=gris)

def frame(t):
    card = seg(t, thad, thad + 0.6)
    bright = 0.08 + 0.06 * seg(t, s3 + 1.5, s3 + 3.0) + 0.06 * seg(t, t10 + 1.5, t10 + 3.0) + 0.2 * seg(t, t30 + 0.3, t30 + 2.0) \
        + 0.55 * seg(t, TM[0], TP + 1.0)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer(); over, do = Z.new_layer()
    # ---------- bajo el suelo ----------
    Z.grietas(d, LXC, 0.3 * seg(t, s2 + 1.0, s2 + 2.5) + 0.3 * seg(t, t10, t10 + 1.5) + 0.4 * seg(t, t30, t30 + 2.0), seed=4)
    Z.roots(d, 0.3 * seg(t, s3 + 1.8, s3 + 3.2) + 0.25 * seg(t, t10 + 1.4, t10 + 2.6) + 0.45 * seg(t, t30 + 0.3, tq + 1.0), x0=RXC)
    if t > tq: Z.flor(d, RXC - 90, 120 * seg(t, tq, tq + 1.0)); Z.flor(d, RXC + 100, 90 * seg(t, tq + 0.4, tq + 1.4))
    # ================= IZQUIERDA: «LUEGO, MAMÁ» =================
    gris_l = min(1.0, 0.35 * seg(t, s2 + 0.8, s2 + 2.2) + 0.3 * seg(t, t10 + 0.8, t10 + 2.0) + 0.35 * seg(t, t30, t30 + 1.5)) * (1 - seg(t, TM[2] + 0.6, TM[2] + 1.6))
    sola = seg(t, t30 + 0.2, t30 + 1.0)                    # día 30: ya no pide; se sienta sola
    carga_l = (1 - sola)
    tremor = 3 * math.sin(t * 19) * seg(t, s2 + 0.6, s2 + 1.0) * carga_l
    if carga_l > 0:
        Z.madre(d, ML + tremor, Z.CARGA, k=KM, gris=gris_l, alpha=255 * carga_l)
        caja_en(d, ML + 46 * KM + tremor, GY - 150 * KM + 48, alpha=255 * carga_l, gris=gris_l)
        if t > s2 + 0.8: Z.gotas_sudor(d, ML + 40, GY - 270, t, alpha=200 * carga_l)
    if sola > 0:
        pm = Z.lerp_pose(SENT_SOLA, Z.SENTADO_DUA, seg(t, TM[2] + 0.6, TM[2] + 1.6))
        Z.madre(d, ML - 20, pm, k=KM, gris=gris_l, alpha=255 * sola)
        caja_en(d, ML + 120, GY, alpha=255 * sola, gris=gris_l)
    for a, b in ((s1 + 0.1, s2 + 0.6), (t10 + 0.05, t10 + 1.6)):          # la madre pide ayuda
        al = 255 * seg(t, a, a + 0.2) * (1 - seg(t, b - 0.25, b))
        if al > 0: Z.bocadillo(d, ML + 70, GY - 420, "¿ME AYUDAS?", alpha=al, size=24, cola=-1)
    for a, b in ((s2 + 0.3, s3 - 0.1), (t10 + 0.8, t30 - 0.2)):            # el hijo: «LUEGO…»
        al = 255 * seg(t, a, a + 0.2) * (1 - seg(t, b - 0.25, b))
        if al > 0: Z.bocadillo(d, HL + 40, GY - 440, "LUEGO…", alpha=al, size=26, cola=1)
    turn = seg(t, TM[2] + 0.3, TM[2] + 0.6)                 # al tercer «tu madre» guarda el móvil y va hacia ella
    walk = seg(t, TM[2] + 0.6, TM[2] + 1.8)
    xh = lerp(HL, 300, walk)
    if turn < 0.5: figure(d, xh, MOVIL); Z.movil(d, g, HL + 16, GY - 250, alpha=255 * (1 - 2 * turn))
    else: figure(d, xh, Z.espejo(Z.walk_pose(t * 9) if 0 < walk < 1 else (P["give"] if walk >= 1 else P["stand"])))
    # ================= DERECHA: «YA VOY, MAMÁ» =================
    mom_r = Z.espejo(Z.CARGA)
    if t < t30:
        t0, f = (s3 + 0.1, 1.0) if t < t10 else (t10 + 0.4, 0.8)      # salto de tiempo en «DÍA 10»: vuelve a empezar
        go = seg(t, t0, t0 + 1.0 * f); take = seg(t, t0 + 1.0 * f, t0 + 1.0 * f + 0.4)
        xs = lerp(HR, MR - 150, go)
        if t < s3 - 0.05: pose_s = MOVIL
        elif 0.0 < go < 1.0: pose_s = Z.walk_pose(t * 9)
        else: pose_s = Z.lerp_pose(P["stand"], Z.LLEVA, take)
        pm_r = Z.lerp_pose(mom_r, Z.espejo(Z.MAYOR), take)
        pm_r = Z.lerp_pose(pm_r, P["joy"], 0.45 * seg(t, t0 + 1.0 * f + 0.4, t0 + 1.0 * f + 0.9))
        Z.madre(d, MR, pm_r, k=KM)
        caja_en(d, lerp(MR - 46 * KM, xs + 46, take), lerp(GY - 150 * KM + 48, GY - 122, take))
        figure(d, xs, pose_s)
        take_glow = take
    else:                                                    # día 30: juntos, sin carga; la madre feliz
        xs = MR - 150
        Z.madre(d, MR, Z.lerp_pose(Z.espejo(Z.MAYOR), P["joy"], 0.6 * seg(t, t30 + 0.2, t30 + 1.0) * (1 - 0.5 * card)), k=KM)
        figure(d, xs, Z.lerp_pose(P["stand"], P["give"], 0.6 * seg(t, t30 + 0.2, t30 + 1.0)))
        take_glow = 1.0
    if t < s3 + 0.3: Z.movil(d, g, HR + 16, GY - 250, alpha=255 * (1 - seg(t, s3 - 0.1, s3 + 0.3)))
    help1, help2 = s3 + 0.1, t10 + 0.4
    for a, b in ((s1 + 0.1, s3 + 0.2), (t10 + 0.05, t10 + 0.85)):
        al = 255 * seg(t, a, a + 0.2) * (1 - seg(t, b - 0.25, b))
        if al > 0: Z.bocadillo(d, MR - 60, GY - 420, "¿ME AYUDAS?", alpha=al, size=24, cola=1)
    for a, b in ((s3 + 0.3, t10 - 0.2), (t10 + 0.9, t10 + 2.0)):
        al = 255 * seg(t, a, a + 0.2) * (1 - seg(t, b - 0.25, b))
        if al > 0: Z.bocadillo(d, HR + 30, GY - 470, "¡YA VOY!", alpha=al, size=26, cola=-1, borde=TEAL)
    # la dua de la madre sube como corazones de luz
    for t0 in (help1 + 1.5, help2 + 1.3, t30 + 0.3, t30 + 0.9, t30 + 1.5, TM[0], TM[1], TM[2]):
        if t0 < t < t0 + 1.8:
            u = seg(t, t0, t0 + 1.8)
            Z.corazon_luz(d, g, lerp(MR, W / 2, u) + 30 * math.sin(u * 7), lerp(GY - 300, 230, u), 16 * (1 - 0.4 * u), alpha=255 * (1 - seg(u, 0.85, 1)))
    if take_glow > 0.5: g.ellipse([MR - 200, GY - 420, MR + 120, GY + 20], fill=(80, 230, 225, int(70 * take_glow)))
    # ================= TEXTOS =================
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "«LUEGO, MAMÁ»", "«YA VOY, MAMÁ»", t10, t30, 42, lx=LXC, rx=RXC - 10)
    Z.subs(d, t, [(-0.4, s1 - 0.15, "¿A QUIÉN DEBES TRATAR MEJOR?"), (s1, s2 - 0.1, "SU MADRE LES PIDE AYUDA"),
                  (s2, s3 - 0.1, "UNO DICE: «LUEGO»"), (s3, t10 - 0.1, "EL OTRO DEJA EL MÓVIL Y VA")])
    Z.pregunta(d, t, tq, thad, "¿QUIÉN MERECE MÁS TU CARIÑO?")
    if thad <= t < tfin:
        al = 255 * card * (1 - seg(t, tfin - 0.4, tfin))
        q = "¿QUIÉN MERECE MÁS MI BUEN TRATO?"
        spaced(d, q, W / 2, 330, Z.fit(q, 38, 760, 0.22), al * seg(t, thad + 0.8, thad + 1.3), bold=False, track=0.22, col=(190, 225, 222))
        for i, tm in enumerate(TM):
            ai = al * seg(t, tm, tm + 0.3)
            pulse = 1 + 0.18 * max(0, 1 - abs(t - tm - 0.15) * 4)
            spaced(d, "TU MADRE", W / 2, 410 + 72 * i, int(60 * pulse), ai, col=(235, 240, 235) if i < 2 else (150, 240, 232))
            if tm < t < tm + 0.7: g.ellipse([W / 2 - 260, 360 + 72 * i, W / 2 + 260, 460 + 72 * i], fill=(90, 230, 225, int(120 * (1 - seg(t, tm, tm + 0.7)))))
        spaced(d, "TU PADRE", W / 2, 640, 40, al * 0.85 * seg(t, TP, TP + 0.3), col=(200, 220, 218))
        spaced(d, "SAHIH AL-BUJARI 5971", W / 2, 700, 30, al * 0.85 * seg(t, thad + 1.0, thad + 1.5), bold=False, col=(190, 225, 222))
    Z.final(d, t, tfin, "DI:", "«YA VOY, MAMÁ».", task, "¿CUÁNDO FUE LA ÚLTIMA VEZ", "QUE LE DIJISTE «TE QUIERO»?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
