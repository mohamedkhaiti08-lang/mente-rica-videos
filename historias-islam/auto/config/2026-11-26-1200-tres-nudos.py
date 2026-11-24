# Estilo Noche · SIGUE DORMIDO vs SE LEVANTA · "¿Sabes por qué te cuesta tanto levantarte?" (Sahih al-Bujari 1142)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (los tres nudos del shaitán), gancho «¿Sabes por qué…?».
# Dos camas. Una sombra ata una CUERDA CON TRES NUDOS sobre la nuca de cada uno («la noche es larga, duerme»).
# Suena el despertador: uno lo apaga y sigue durmiendo; el otro dice «Allah» (se suelta un nudo), hace el wudú (otro)
# y reza (el último): cada nudo se abre en un punto de luz que sube. Día 10 y 30: al que se levanta los nudos se le sueltan
# cada mañana y le crecen raíces; al otro la cuerda se le oscurece y engorda, y se levanta tarde y encorvado.
# Objetos nuevos: cuerda con nudos, despertador que suena, nudos que se abren en luz.
# Uso: python3 2026-11-26-1200-tres-nudos.py salida.mp4 [t1 t2 ...]
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes por qué te cuesta tanto levantarte?",
         "Mientras duermes, el shaitán te ata tres nudos.",
         "Suena la alarma. Uno la apaga… y sigue durmiendo.",
         "El otro dice: Allah. Se suelta un nudo.",
         "Hace el wudú. Otro nudo.",
         "Reza. Y se suelta el último.",
         "Día treinta.",
         "¿Quién empieza el día más ligero?",
         "El Profeta, la paz sea con él, dijo: así amanece activo y de buen ánimo. Si no, perezoso y de mal ánimo.",
         "Tres nudos. Tres pasos.",
         "¿Mañana los sueltas los tres? Escribe: in sha Allah."]
PAUSAS = [0.4, 0.6, 0.5, 0.4, 0.4, 1.5, 0.3, 1.7, 0.6, 0.6, 1.3]
def SFX(s): return [dict(t=s[3] + 1.4, f=1320, dur=0.8, v=0.05), dict(t=s[4] + 0.9, f=1320, dur=0.8, v=0.05),
                    dict(t=s[5] + 0.9, f=1320, dur=0.8, v=0.06), dict(t=s[8] - 0.3, f=660, dur=2.0, v=0.08),
                    dict(t=s[8] - 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-26-1200-tres-nudos.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, s3, s4, s5, t30, tq, thad, tfin, task = starts
t10 = ends[5] + 0.2                 # salto visual a DÍA 10 en la pausa
tgiro = thad - 0.3
print("DUR", DUR, starts)

LB0, LB1 = 100, 420                 # cama izquierda (cabeza a la izquierda)
RB0, RB1 = 560, 880                 # cama derecha (cabeza a la derecha)
LXC, RXC = 255, 720                 # etiquetas
ROPE_L, ROPE_R = (262, GY - 440), (720, GY - 440)

def nudos_dia(t, a, paso=0.35):
    """Al que se levanta: en cada salto de día la cuerda vuelve y se suelta rápido (time-lapse)."""
    return tuple(seg(t, a + paso * i, a + paso * i + 0.9) for i in range(3))

def frame(t):
    dawn = seg(t, t30 + 0.1, t30 + 2.5)
    bright = 0.1 + 0.12 * seg(t, t10, t10 + 1.0) + 0.18 * dawn + 0.6 * seg(t, tgiro, tgiro + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    Z.luna(d, g, 150, 215, alpha=255 * (1 - seg(t, t30, t30 + 1.0)))
    # ---------- lo que no se ve ----------
    hk = 0.3 * seg(t, s2 + 1.6, s3) + 0.3 * seg(t, t10, t10 + 1.2) + 0.4 * seg(t, t30, t30 + 2.0)
    Z.humo_dentro(du, 260, hk, t)
    Z.grietas(d, 260, seg(t, tq, tq + 2.2), seed=8)
    rg = 0.12 * seg(t, s3 + 1.0, s3 + 2.0) + 0.12 * seg(t, s4 + 0.8, s4 + 1.8) + 0.16 * seg(t, s5 + 0.8, s5 + 2.0) \
         + 0.25 * seg(t, t10, t10 + 1.5) + 0.35 * seg(t, t30 + 0.3, t30 + 2.5)
    Z.roots(d, rg, x0=RXC)
    # ---------- la sombra que ata los nudos ----------
    sh = seg(t, s1 - 0.2, s1 + 0.6) * (1 - seg(t, s2 + 0.2, s2 + 1.0))
    Z.sombra(du, 490 + 10 * math.sin(t), 0.62, 220 * sh, t)
    for i, (rx, ry) in enumerate((ROPE_L, ROPE_R)):
        a0 = s1 + 0.6 + 0.7 * i
        if a0 < t < a0 + 1.4:
            Z.hilo_sombra(d, 490, GY - 190, rx, ry, seg(t, a0, a0 + 0.8), t, alpha=200 * (1 - seg(t, a0 + 0.9, a0 + 1.4)))
    if sh > 0.05: Z.bocadillo(d, 470, GY - 520, "LA NOCHE ES LARGA. DUERME.", alpha=255 * sh * seg(t, s1 + 1.4, s1 + 1.8), size=22, cola=1, col=(200, 192, 214))
    # ---------- IZQUIERDA: SIGUE DORMIDO ----------
    yl = Z.cama(d, LB0, LB1, almohada="l")
    levanta = seg(t, t30 + 1.6, t30 + 3.0)                   # día 30: se levanta tarde y pesado
    kl = 1 - 0.75 * levanta
    toss = 0.05 * math.sin(t * 5.5) * seg(t, t10, t10 + 0.5) * (1 - seg(t, t30 + 1.2, t30 + 1.6))
    pose_l = pose_mix("stand", "sad", 0.4 * levanta)
    Z.mini_figure(d, 400, pose_l, k=lerp(1.0, 0.92, kl), rot=-(math.pi / 2) * kl * 0.97 + toss * kl, y0=lerp(GY, yl - 4, kl))
    if t < t30 + 1.8: Z.manta(d, 250, 405, yl, alpha=255 * (1 - seg(t, t30 + 1.4, t30 + 1.8)))
    suenaL = seg(t, s2, s2 + 0.2) * (1 - seg(t, s2 + 1.4, s2 + 1.6))
    Z.despertador(d, 62, GY - 34, t, suena=suenaL)
    if s2 + 1.2 < t < s2 + 1.9:                              # la mano sale y la apaga
        k_ = seg(t, s2 + 1.2, s2 + 1.5) * (1 - seg(t, s2 + 1.6, s2 + 1.9))
        d.line([(124 * S, (yl - 20) * S), (lerp(124, 70, k_) * S, lerp(yl - 20, GY - 60, k_) * S)], fill=CREAM + (255,), width=13 * S)
    if s2 + 1.9 < t < t10: Z.zzz(d, 150, yl - 80, t, alpha=200)
    osc = 0.5 * seg(t, t10, t10 + 1.0) + 0.5 * seg(t, t30, t30 + 1.5)
    ropeL_y = ROPE_L[1] + 120 * levanta * 0                  # la cuerda sigue sobre su cabeza
    head_l = (lerp(124, 400 + 36 * 0.4, levanta), lerp(yl - 18, GY - 260, levanta))
    Z.cuerda_nudos(d, g, ROPE_L[0], ropeL_y, seg(t, s1 + 0.9, s1 + 1.6), t, oscuro=osc, hilo_a=head_l, w=240)
    # ---------- DERECHA: SE LEVANTA ----------
    up = seg(t, s3 - 0.1, s3 + 0.8)                          # se levanta con la alarma
    bedA = 255 * (1 - up)
    yr = Z.cama(d, RB0, RB1, almohada="r", alpha=bedA)
    suenaR = seg(t, s2, s2 + 0.2) * (1 - seg(t, s3 - 0.2, s3))
    Z.despertador(d, 918, GY - 34, t, suena=suenaR, alpha=255 * (1 - up))
    kr = 1 - up
    dua = seg(t, s3 + 0.5, s3 + 0.9) * (1 - seg(t, s4 - 0.2, s4 + 0.2))
    wudu = seg(t, s4, s4 + 0.4) * (1 - seg(t, s5 - 0.2, s5 + 0.1))
    suj = seg(t, s5 + 0.1, s5 + 0.8) * (1 - seg(t, s5 + 1.8, s5 + 2.4))
    if t < s3 + 0.8 and kr > 0.02:
        xr = lerp(720, 585, kr)
        Z.mini_figure(d, xr, P["stand"], k=lerp(1.0, 0.92, kr), rot=(math.pi / 2) * kr * 0.97, y0=lerp(GY, yr - 4, kr))
        if kr > 0.9: Z.manta(d, 600, 755, yr, alpha=255, col=(60, 110, 112))
    else:
        WUDU = dict(P["stand"]); WUDU.update(le=(-6, -200), lh=(30, -176), re=(20, -200), rh=(48, -180), head=(6, -296))
        rp = Z.lerp_pose(P["stand"], Z.DUA, dua)
        rp = Z.lerp_pose(rp, WUDU, wudu)
        rp = Z.lerp_pose(rp, Z.a_sujud(1.0, izquierda=True), suj)
        rp = Z.lerp_pose(rp, P["joy"], seg(t, tgiro + 0.2, tgiro + 1.0) * (1 - seg(t, tfin - 0.3, tfin + 0.3)))
        figure(d, 720, rp)
    if s3 + 0.6 < t < s4 - 0.1:
        Z.bocadillo(d, 585, GY - 360, "ALLAH", alpha=255 * dua, size=30, cola=1)
    if wudu > 0.05:                                          # agua que cae sobre las manos
        for j in range(7):
            ph = (t * 1.3 + j / 7) % 1
            Z.gota(d, g, 752 + 14 * math.sin(j * 2.1), GY - 330 + 150 * ph, r=6, alpha=230 * wudu * (1 - ph))
    # sus nudos: uno por paso, y en cada salto de día se sueltan solos (time-lapse)
    sueltos = (seg(t, s3 + 1.0, s3 + 2.0), seg(t, s4 + 0.6, s4 + 1.6), seg(t, s5 + 0.7, s5 + 1.7))
    vis = seg(t, s1 + 1.6, s1 + 2.3)
    for a in (t10 + 0.1, t30 + 0.4):
        if t > a - 0.3:
            sueltos = nudos_dia(t, a); vis = seg(t, a - 0.3, a)
    if t > tgiro: vis *= 0
    head_r = (861, yr - 18) if t < s3 else (726, GY - 300)
    Z.cuerda_nudos(d, g, ROPE_R[0], ROPE_R[1], vis, t, sueltos=sueltos, hilo_a=head_r, w=240)
    for i, (a, sd) in enumerate(((s3 + 1.0, 3), (s4 + 0.6, 5), (s5 + 0.7, 7))):
        Z.chispas(d, ROPE_R[0] - 120 + 60 * (i + 1), ROPE_R[1], t, a, seed=sd)
    if t > tgiro: g.ellipse([RXC - 220, GY - 440, RXC + 220, GY + 30], fill=(80, 230, 225, int(80 * seg(t, tgiro, tgiro + 2.0))))
    Z.anillos(d, RXC, GY - 228, t, tgiro, 2.6)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SIGUE DORMIDO", "SE LEVANTA", t10, t30, 40, lx=LXC, rx=RXC)
    Z.subs(d, t, [(0.4, s1 - 0.15, "¿POR QUÉ CUESTA TANTO LEVANTARSE?"), (s1, s2 - 0.15, "EL SHAITÁN ATA TRES NUDOS"),
                  (s2, s3 - 0.15, "UNO APAGA LA ALARMA"), (s3, s4 - 0.1, "EL OTRO DICE «ALLAH» · 1"),
                  (s4, s5 - 0.1, "HACE EL WUDÚ · 2"), (s5, t10 - 0.05, "REZA · 3"),
                  (t30, tq - 0.05, "UNO SE LEVANTA PESADO")])
    Z.pregunta(d, t, tq, thad, "¿QUIÉN EMPIEZA MÁS LIGERO?")
    Z.fuente(d, t, thad, tfin, ["«AMANECE ACTIVO", "Y DE BUEN ÁNIMO;", "SI NO, PEREZOSO»"], "SAHIH AL-BUJARI 1142")
    Z.final(d, t, tfin, "TRES NUDOS.", "TRES PASOS.", task, "¿MAÑANA LOS SUELTAS?", "ESCRIBE «IN SHA ALLAH»")
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
