# Estilo Noche · SE ASUSTA vs SE REFUGIA · "¿Sabes qué hace un musulmán cuando tiene una pesadilla?" (Sahih al-Bujari 3292)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (la pesadilla viene del shaitán) + gancho de curiosidad.
# Dos camas, la misma pesadilla: sobre cada uno crece una NUBE DE SUEÑO oscura con una sombra y rayos dentro.
# Uno se despierta con miedo y se queda con ella: sentado en la cama, sudando, móvil encendido; la nube crece noche a noche
# (dos sombras el día 10), grietas bajo su cama; día 30 amanece agotado bajo una nube gris.
# El otro escupe levemente a su lado y pide refugio en Allah: la nube se deshace en chispas, vuelve a dormir (zzz) y le
# crecen raíces; el día 10 vuelve una nube pequeña y se deshace otra vez; día 30 se levanta con alegría y el cielo se ilumina.
# Objetos nuevos: nube de sueño, rayos, soplo leve (escupe). Piezas en noche/piezas.py (29 nov).
# Uso: python3 2026-11-29-1200-pesadilla.py salida.mp4 [t1 t2 ... fotogramas]   (NOVOZ=1 reutiliza el guion)
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué hace un musulmán cuando tiene una pesadilla?",
         "Dos camas. La misma pesadilla.",
         "Uno se despierta con miedo, y se queda con ella.",
         "El otro escupe levemente a su lado, y pide refugio en Allah.",
         "Día diez.",
         "¿Quién vuelve a dormir tranquilo?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: el buen sueño es de Allah, y la pesadilla, del shaitán.",
         "Escupe a tu izquierda, pide refugio en Allah, y no te hará daño.",
         "Él asusta. Allah protege.",
         "¿Lo sabías? Guárdalo para esta noche."]
PAUSAS = [0.3, 0.4, 0.6, 0.8, 1.3, 1.4, 1.1, 0.4, 0.5, 0.5, 0.8]
def SFX(s): return [dict(t=s[3] + 1.8, f=1320, dur=0.8, v=0.05), dict(t=s[4] + 1.0, f=1320, dur=0.8, v=0.05),
                    dict(t=s[6], f=660, dur=2.0, v=0.08), dict(t=s[6] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-29-1200-pesadilla.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, s3, t10, tq, t30, thad, tpas, tfin, task = starts
print("DUR", DUR, starts)

LB0, LB1 = 90, 410            # cama izquierda (cabeza a la izquierda)
RB0, RB1 = 600, 920           # cama derecha (cabeza a la derecha)
LXC, RXC = 250, 760           # centros de cada lado
CL, CR = (290, 750), (720, 750)   # nubes de sueño
TEAL = (130, 240, 232)
SOMBRA_N = (104, 94, 128)

def frame(t):
    bright = 0.08 + 0.1 * seg(t, s3 + 1.6, s3 + 3.0) + 0.8 * seg(t, t30 + 0.2, t30 + 3.0)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer(); over, do = Z.new_layer()
    dawn = seg(t, t30 + 0.2, t30 + 3.0)
    Z.luna(d, g, 150 + 40 * dawn, 215 + 260 * dawn, alpha=255 * (1 - dawn))
    # ---------- bajo el suelo ----------
    Z.grietas(d, LXC, 0.3 * seg(t, s2 + 1.0, s2 + 2.5) + 0.3 * seg(t, t10, t10 + 1.5) + 0.4 * seg(t, t30, t30 + 2.5), seed=8)
    Z.humo_dentro(d, LXC, 0.4 * seg(t, s2 + 1.0, t10) + 0.6 * seg(t, t10, t30 + 2.0), t)
    Z.roots(d, 0.3 * seg(t, s3 + 2.4, s3 + 3.8) + 0.25 * seg(t, t10 + 1.2, t10 + 2.4) + 0.45 * seg(t, t30 + 0.4, t30 + 2.8), x0=RXC)
    # ---------- IZQUIERDA: SE ASUSTA ----------
    yl = Z.cama(d, LB0, LB1, almohada="l")
    sit_l = seg(t, s2 + 0.1, s2 + 0.5)                      # se incorpora del susto y ya no vuelve a dormir
    tired = seg(t, t30 + 1.0, t30 + 2.6)
    if sit_l < 1:
        Z.mini_figure(d, 395, P["stand"], k=0.92, rot=-(math.pi / 2) * 0.97, y0=yl - 4, alpha=255 * (1 - sit_l))
        Z.manta(d, 250, 400, yl, alpha=255 * (1 - sit_l))
    hl = (120, yl - 4)
    if sit_l > 0:
        shake = 0.03 * math.sin(t * 23) * (1 - tired)
        pl = Z.lerp_pose(Z.SENTADO_MIEDO, Z.SENTADO_CANSADO, tired)
        if t > s2 + 1.6: pl = Z.lerp_pose(pl, Z.SENTADO_MOVIL, seg(t, s2 + 1.6, s2 + 2.0) * (1 - tired))
        Z.mini_figure(d, 125, pl, k=0.92, rot=shake, y0=yl - 4, alpha=255 * sit_l)
        Z.manta(d, 200, 400, yl + 2, alpha=255 * sit_l)
        hl = (125 + pl["head"][0] * 0.92, yl - 4 + pl["head"][1] * 0.92)
        Z.gotas_sudor(d, hl[0] + 30, hl[1] - 10, t, alpha=230 * sit_l * (1 - tired))
        Z.movil(d, g, 125 + 62 * 0.92, yl - 4 - 128 * 0.92, alpha=255 * seg(t, s2 + 1.7, s2 + 2.1) * (1 - tired))
    kcl = (0.55 + 0.45 * seg(t, 0, s1 + 0.6)) * (1 + 0.08 * seg(t, s2 + 0.8, s2 + 2.0) + 0.08 * seg(t, t10, t10 + 1.2))
    oscl = 1 - 0.55 * dawn
    fin_a = 1 - seg(t, tfin - 0.6, tfin)
    rx, ry = Z.nube_sueno(do, CL[0], CL[1] - 10 * seg(t, t10, t10 + 1.2), kcl, t, hacia=hl, oscuro=oscl, alpha=255 * (1 - 0.35 * dawn) * fin_a)
    sh_a = 230 * seg(t, s1, s1 + 0.8) * (1 - 0.45 * dawn) * fin_a
    Z.sombra(do, CL[0] - 20, 0.36 * kcl, sh_a, t, y0=CL[1] + 74 * kcl, col=SOMBRA_N)
    if t > t10: Z.sombra(do, CL[0] + 75, 0.28 * kcl, sh_a * seg(t, t10 + 0.2, t10 + 1.0), t + 1.3, y0=CL[1] + 70 * kcl, col=SOMBRA_N)
    if t > s1 and math.sin(t * 2.7) > 0.3: Z.rayo(do, CL[0] - 90 * kcl, CL[1] - 55 * kcl, 60 * kcl, alpha=sh_a)
    if t > t10 and math.sin(t * 3.1 + 1) > 0.6: Z.rayo(do, CL[0] + 100 * kcl, CL[1] - 50 * kcl, 52 * kcl, alpha=sh_a)
    # ---------- DERECHA: SE REFUGIA ----------
    yr = Z.cama(d, RB0, RB1, almohada="r")
    sit_r = max(seg(t, s3 + 0.1, s3 + 0.5) * (1 - seg(t, s3 + 2.6, s3 + 3.0)), seg(t, t10 + 0.1, t10 + 0.4) * (1 - seg(t, t10 + 2.3, t10 + 2.7)))
    up_r = seg(t, t30 + 1.2, t30 + 2.0)                       # día 30: se levanta
    pose_r = pose_mix("stand", "joy", seg(t, t30 + 2.0, t30 + 2.6) * (1 - seg(t, thad + 2.0, thad + 2.8)))
    lie = (1 - sit_r) * (1 - up_r)
    if lie > 0:
        Z.mini_figure(d, 615, P["stand"], k=0.92, rot=(math.pi / 2) * 0.97, y0=yr - 4, alpha=255 * lie)
        Z.manta(d, 620, 770, yr, alpha=255 * lie, col=(60, 110, 112))
    hr = (900, yr - 4)
    if sit_r > 0:
        pr = Z.espejo(Z.SENTADO_DUA)
        Z.mini_figure(d, 895, pr, k=0.92, y0=yr - 4, alpha=255 * sit_r)
        Z.manta(d, 620, 820, yr + 2, alpha=255 * sit_r, col=(60, 110, 112))
        hr = (895 + pr["head"][0] * 0.92, yr - 4 + pr["head"][1] * 0.92)
    if up_r > 0: Z.mini_figure(d, lerp(700, 540, seg(t, t30 + 1.2, t30 + 2.0)), pose_r, k=1.0, alpha=255 * up_r)
    # escupe levemente y pide refugio (dos veces: noche 1 y noche 10)
    for a in (s3 + 0.7, t10 + 0.55):
        Z.escupe(d, hr[0] + 24, hr[1] + 10, seg(t, a, a + 0.8), t, lado=1)
        for j in range(5):                                    # la dua sube como luz
            a0 = a + 0.6 + j * 0.15
            if a0 < t < a0 + 1.1:
                u = seg(t, a0, a0 + 1.1)
                Z.gota(d, g, lerp(hr[0] - 20, CR[0], u) + 20 * math.sin(u * 6 + j), lerp(hr[1] - 30, CR[1] - 60, u), r=7, alpha=230 * (1 - 0.5 * u))
    pop1, pop2 = s3 + 1.8, t10 + 1.6
    kcr1 = (0.55 + 0.45 * seg(t, 0, s1 + 0.6)) * (1 - seg(t, pop1, pop1 + 0.35))
    kcr2 = 0.7 * seg(t, t10 - 0.1, t10 + 0.5) * (1 - seg(t, pop2, pop2 + 0.35))
    kcr = max(kcr1 if t < pop1 + 0.35 else 0, kcr2)
    if kcr > 0.02:
        Z.nube_sueno(do, CR[0], CR[1], kcr, t, hacia=hr, alpha=255)
        Z.sombra(do, CR[0] + 15, 0.36 * kcr, 230 * seg(t, s1, s1 + 0.8), t + 0.7, y0=CR[1] + 74 * kcr, col=SOMBRA_N)
        if t > s1 and math.sin(t * 2.9 + 2) > 0.3: Z.rayo(do, CR[0] + 90 * kcr, CR[1] - 55 * kcr, 60 * kcr, alpha=230)
    for p_ in (pop1, pop2):
        Z.chispas(d, CR[0], CR[1], t, p_, dur=1.3, n=22)
        if p_ < t < p_ + 0.8: g.ellipse([CR[0] - 170, CR[1] - 130, CR[0] + 170, CR[1] + 130], fill=(120, 240, 235, int(210 * (1 - seg(t, p_, p_ + 0.8)))))
    zz = seg(t, s3 + 3.3, s3 + 3.8) * (1 - seg(t, t10 - 0.1, t10 + 0.2)) + seg(t, t10 + 2.6, t10 + 3.0) * (1 - seg(t, t30 + 0.8, t30 + 1.2))
    if zz > 0: Z.zzz(d, 900, yr - 80, t, alpha=220 * zz)
    if t > t30: g.ellipse([540 - 200, GY - 430, 540 + 200, GY + 30], fill=(80, 230, 225, int(70 * dawn)))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SE ASUSTA", "SE REFUGIA", t10, t30, 46, lx=LXC, rx=RXC - 20)
    Z.subs(d, t, [(-0.4, s1 - 0.15, "¿QUÉ HACES TRAS UNA PESADILLA?"), (s1, s2 - 0.1, "LA MISMA PESADILLA"),
                  (s2, s3 - 0.1, "UNO SE QUEDA CON ELLA"), (s3, t10 - 0.1, "EL OTRO PIDE REFUGIO EN ALLAH")])
    Z.pregunta(d, t, tq, t30, "¿QUIÉN DUERME TRANQUILO?")
    Z.fuente(d, t, thad, tpas, ["«EL BUEN SUEÑO, DE ALLAH;", "LA PESADILLA,", "DEL SHAITÁN»"], "SAHIH AL-BUJARI 3292")
    if tpas <= t < tfin:
        L = ends[8] - tpas
        al = 255 * seg(t, tpas, tpas + 0.4) * (1 - seg(t, tfin - 0.4, tfin))
        for i, txt in enumerate(("1 · ESCUPE A TU IZQUIERDA", "2 · PIDE REFUGIO EN ALLAH", "3 · NO TE HARÁ DAÑO")):
            ai = al * seg(t, tpas + L * (0.0, 0.33, 0.68)[i], tpas + L * (0.0, 0.33, 0.68)[i] + 0.4)
            spaced(d, txt, W / 2, 340 + 62 * i, Z.fit("1 · ESCUPE A TU IZQUIERDA", 40, 760), ai, col=(235, 235, 230) if i < 2 else (150, 240, 232))
        spaced(d, "SAHIH AL-BUJARI 3292", W / 2, 530, 30, al * 0.85, bold=False, col=(190, 225, 222))
    Z.final(d, t, tfin, "ÉL ASUSTA.", "ALLAH PROTEGE.", task, "¿LO SABÍAS?", "GUÁRDALO PARA ESTA NOCHE")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
