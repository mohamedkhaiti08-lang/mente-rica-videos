# Estilo Noche · SIN MÁS vs AYAT AL-KURSI · "dos camas, la misma noche" (Sahih al-Bujari 2311)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (como BISMILLAH en casa y SIN DUA al salir).
# Uno se duerme con el móvil y las sombras se le acercan noche tras noche; el otro recita Ayat al-Kursi:
# aparece un farol guardián con un haz de luz sobre su cama y las sombras se deshacen al tocarlo.
# Día 30: amanece; uno se levanta descansado y el otro agotado.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-17-1200-ayat-kursi.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Dos camas. La misma noche. Pero solo una tiene guardián.",
         "Uno se duerme sin más.",
         "El otro recita Áyat al Kursi.",
         "Día diez.",
         "¿Quién duerme protegido?",
         "Día treinta.",
         "Recítala al acostarte: tendrás un guardián de Allah, y el shaitán no se te acercará hasta la mañana.",
         "Lo curioso: se lo enseñó el propio shaitán. Y el Profeta, la paz sea con él, dijo: te ha dicho la verdad, aunque es un mentiroso.",
         "Áyat al Kursi. Y duerme tranquilo.",
         "¿Tú la recitas antes de dormir?"]
PAUSAS = [0.5, 0.6, 0.9, 0.4, 1.7, 0.5, 0.6, 0.7, 0.8, 1.3]
def SFX(s): return [dict(t=s[2] + 0.9, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-17-1200-ayat-kursi.guion.json")
import json
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.06)
s0, s1, s2, t10, tq, t30, thad, tcur, tfin, task = starts
print("DUR", DUR, starts)

LB0, LB1 = 100, 420          # cama izquierda (cabeza a la izquierda)
RB0, RB1 = 560, 880          # cama derecha (cabeza a la derecha)
LXC, RXC = 265, 720          # centros de cada lado (etiquetas)
LAMP = (720, GY - 440)

def frame(t):
    bright = 0.1 + 0.12 * seg(t, t10, t10 + 1.2) + 0.78 * seg(t, t30 + 0.2, t30 + 3.0)   # el día 30 amanece
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer(); over, do = Z.new_layer()
    dawn = seg(t, t30 + 0.2, t30 + 3.0)
    # luna (se pone al amanecer)
    Z.luna(d, g, 150 + 40 * dawn, 215 + 260 * dawn, alpha=255 * (1 - dawn))
    # ---------- lo que no se ve ----------
    Z.grietas(d, 260, 0.3 * seg(t, s1 + 1.5, t10) + 0.3 * seg(t, t10, t10 + 1.5) + 0.4 * seg(t, t30, t30 + 2.5), seed=8)
    Z.roots(d, 0.3 * seg(t, s2 + 2.0, s2 + 3.6) + 0.25 * seg(t, t10, t10 + 1.5) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), x0=RXC)
    # ---------- IZQUIERDA: SE DUERME SIN MÁS ----------
    yl = Z.cama(d, LB0, LB1, almohada="l")
    kl = seg(t, s1 + 0.2, s1 + 1.3) * (1 - 0.75 * seg(t, t30 + 1.4, t30 + 2.8))           # se tumba; al amanecer se incorpora a medias
    toss = 0.06 * math.sin(t * 5.5) * seg(t, t10, t10 + 0.5) * (1 - seg(t, t30 + 1.0, t30 + 1.4))   # da vueltas, no descansa
    pose_l = pose_mix("stand", "sad", 0.4 * seg(t, t30 + 1.4, t30 + 2.8))
    xl = lerp(270, 400, seg(t, s1 + 0.2, s1 + 1.3))
    Z.mini_figure(d, xl, pose_l, k=lerp(1.0, 0.92, kl), rot=-(math.pi / 2) * kl * 0.97 + toss * kl, alpha=int(255 * (1 - 0.3 * dawn)), y0=lerp(GY, yl - 4, kl))
    if kl > 0.9 and t < t30 + 1.6: Z.manta(d, 250, 405, yl, alpha=255 * seg(t, s1 + 1.1, s1 + 1.5))
    phone = seg(t, s1 + 1.0, s1 + 1.5) * (1 - seg(t, t30 + 1.0, t30 + 1.6))
    Z.movil(d, g, 190, yl - 60, alpha=255 * phone)
    # sombras que se acercan noche tras noche (detrás de la cama)
    SH = [(-1.0, 470, 0.62, 0.0), (t10 + 0.2, 40, 0.66, 1.0), (tq + 0.4, 330, 0.55, 2.0)]
    for i, (a, xs, ks, sd) in enumerate(SH):
        if t > a:
            x = lerp(-130 if i != 2 else 1.0 * 330, xs, seg(t, a, a + 1.8)) + 6 * math.sin(t * 1.3 + i)
            if i == 0: x = lerp(-40, xs, seg(t, 1.6, t10 + 0.5)) + 6 * math.sin(t * 1.3)
            yy = GY if i != 2 else lerp(GY - 520, GY - 90, seg(t, a, a + 2.0))
            kk = ks * (1 + 0.15 * seg(t, t30, t30 + 2))
            reach = ((math.sin(t * 3 + i) + 1) / 2) * seg(t, t10, t10 + 0.8) if i == 0 else 0
            al = 225 * seg(t, a, a + 0.7) if i else 160 + 65 * seg(t, s1, t10)
            Z.sombra(du, x, kk, al, t + sd * 1.7, reach=reach, y0=yy)
    # ---------- DERECHA: RECITA ÁYAT AL KURSI ----------
    Z.haz(du, g, LAMP[0], LAMP[1], 540, 900, seg(t, s2 + 1.4, s2 + 2.2) * (1 - 0.55 * dawn), t)   # detrás de la cama y la figura
    yr = Z.cama(d, RB0, RB1, almohada="r")
    kr = seg(t, s2 + 1.6, s2 + 2.6) * (1 - seg(t, t30 + 1.2, t30 + 2.4))
    rec = seg(t, s2, s2 + 0.4) * (1 - seg(t, s2 + 1.4, s2 + 1.7))
    pose_r = pose_mix("stand", "joy", 0.35 * rec) if t < t30 else pose_mix("stand", "joy", seg(t, t30 + 2.2, t30 + 2.8) * (1 - seg(t, thad + 3.0, thad + 3.8)))
    xr = lerp(720, 585, kr if t < t30 else 1 - seg(t, t30 + 1.2, t30 + 2.4)) if t >= s2 + 1.6 else 720
    if t >= t30 + 2.4: xr = 720
    Z.mini_figure(d, xr, pose_r, k=lerp(1.0, 0.92, kr), rot=(math.pi / 2) * kr * 0.97, y0=lerp(GY, yr - 4, kr))
    if kr > 0.9: Z.manta(d, 600, 755, yr, alpha=255 * seg(t, s2 + 2.4, s2 + 2.8) * (1 - seg(t, t30 + 1.1, t30 + 1.4)), col=(60, 110, 112))
    # la recitación sube como luz y forma el farol
    for j in range(6):
        a0 = s2 + 0.1 + j * 0.18
        if a0 < t < a0 + 1.2:
            u = seg(t, a0, a0 + 1.2); px = lerp(720, LAMP[0], u) + 30 * math.sin(u * 6 + j); py = lerp(GY - 300, LAMP[1], u)
            Z.gota(d, g, px, py, r=7, alpha=230 * (1 - 0.6 * u))
    lamp = seg(t, s2 + 0.9, s2 + 1.6)
    Z.farol(d, g, LAMP[0], LAMP[1], lamp, t)
    if t30 > t > s2 + 3.0: Z.zzz(d, 860, yr - 70, t, alpha=220 * seg(t, s2 + 3.0, s2 + 3.6) * (1 - seg(t, t30, t30 + 0.6)))
    # sombras que intentan acercarse y se deshacen al tocar el haz
    for i, a in enumerate((s2 + 2.6, t10 + 0.5, tq + 0.3)):
        if a < t < a + 3.0:
            hit = a + 1.6
            sx = lerp(1160, 975, seg(t, a, hit))
            kk = 0.58 * (1 - 0.7 * seg(t, hit, hit + 0.9))
            al = 220 * seg(t, a, a + 0.5) * (1 - seg(t, hit + 0.1, hit + 0.9))
            Z.sombra(do, sx, kk, al, t + 2.3 + i)
            if hit < t < hit + 0.8:
                g.ellipse([900, GY - 330, 1060, GY - 60], fill=(120, 240, 235, int(200 * (1 - seg(t, hit, hit + 0.8)))))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0:
        spaced(d, "SIN MÁS", LXC, 330, 40, la); spaced(d, "ÁYAT AL-KURSI", RXC, 330, 38, la)
        day = "DÍA 1" if t < t10 else ("DÍA 10" if t < t30 else "DÍA 30")
        pulse = 1 + 0.25 * max(0, 1 - abs(t - t10) * 3) + 0.25 * max(0, 1 - abs(t - t30) * 3)
        for x_ in (LXC, RXC): spaced(d, day, x_, 400, int(38 * pulse), la * 0.8, col=(200, 225, 222))
    Z.subs(d, t, [(0.4, 2.0, "LA MISMA NOCHE..."), (2.0, s1 - 0.15, "SOLO UNA TIENE GUARDIÁN"), (s1, s2 - 0.15, "UNO SE DUERME SIN MÁS"), (s2, t10 - 0.1, "EL OTRO RECITA ÁYAT AL-KURSI")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN DUERME PROTEGIDO?")
    Z.fuente(d, t, thad, tcur, ["«UN GUARDIÁN", "DE ALLAH", "HASTA LA MAÑANA»"], "SAHIH AL-BUJARI 2311")
    if tcur <= t < tfin:                                   # la curiosidad del hadiz
        L = ends[7] - tcur
        al = 255 * seg(t, tcur, tcur + 0.4) * (1 - seg(t, tfin - 0.4, tfin))
        spaced(d, "¿LO CURIOSO?", W / 2, 330, 50, al)
        a1 = al * seg(t, tcur + 0.2 * L, tcur + 0.2 * L + 0.4)
        spaced(d, "SE LO ENSEÑÓ", W / 2, 400, 40, a1, col=(200, 225, 222)); spaced(d, "EL PROPIO SHAITÁN", W / 2, 452, 40, a1, col=(200, 225, 222))
        a2 = al * seg(t, tcur + 0.55 * L, tcur + 0.55 * L + 0.4)
        spaced(d, "«TE HA DICHO LA VERDAD,", W / 2, 520, Z.fit("«TE HA DICHO LA VERDAD,", 38, 760), a2, col=(150, 240, 232))
        spaced(d, "AUNQUE ES UN MENTIROSO»", W / 2, 572, Z.fit("«TE HA DICHO LA VERDAD,", 38, 760), a2, col=(150, 240, 232))
        spaced(d, "SAHIH AL-BUJARI 2311", W / 2, 628, 30, a2 * 0.85, bold=False, col=(190, 225, 222))
    Z.final(d, t, tfin, "ÁYAT AL-KURSI.", "Y DUERME TRANQUILO.", task, "¿TÚ LA RECITAS", "ANTES DE DORMIR?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
