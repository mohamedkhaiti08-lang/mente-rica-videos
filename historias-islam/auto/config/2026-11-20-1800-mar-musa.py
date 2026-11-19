# Estilo Noche · MIEDO vs CONFIANZA · "el mar delante, un ejército detrás" (Corán 26:61-63, Sura Ash-Shu'ara)
# Explorar: historia del Corán en 2ª persona con tensión (como Yunus, 812 TikTok, 70 likes, 9 compartidos) y metáfora nueva:
# el camino que se abre donde no lo había. Etiquetas: MIEDO (su gente) vs CONFIANZA (Musa). Contador de etapas en vez de días:
# EL MAR DELANTE → EL EJÉRCITO DETRÁS → SIN SALIDA. Giro: «¡No! Mi Señor está conmigo»; golpea el mar y se abre en dos murallas.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-20-1800-mar-musa.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["El mar delante. Un ejército detrás.",
         "Su gente gritó: ¡nos van a alcanzar!",
         "Y el ejército, cada vez más cerca.",
         "¿Tú qué habrías dicho?",
         "Musa dijo: ¡No! Mi Señor está conmigo. Él me guiará.",
         "Allah le dijo: golpea el mar con tu bastón.",
         "Y el mar se abrió. Cada lado, como una gran montaña.",
         "Cuando no ves salida, Allah abre un camino.",
         "¿Cuál es tu mar ahora mismo?"]
PAUSAS = [0.8, 0.9, 0.8, 2.2, 0.8, 0.5, 0.9, 1.0, 1.5]
def SFX(s): return [dict(t=s[4] + 0.3, f=660, dur=1.6, v=0.06), dict(t=s[6], f=660, dur=2.2, v=0.08), dict(t=s[6] + 0.15, f=990, dur=2.2, v=0.06),
                    dict(t=s[6] - 0.25, f=1320, dur=0.8, v=0.05)]
GUION = os.path.join(HERE, "2026-11-20-1800-mar-musa.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION)
s0, s1, t10, tq, tgiro, tbast, tabre, tfin, task = starts
print("DUR", DUR, starts)

XM = 560                              # Musa
GENTE = [(300, 0.0), (372, 1.3), (444, 2.1)]   # su gente (x, fase)
GX = 820                              # donde se abre el mar

def frame(t):
    bright = 0.1 + 0.08 * seg(t, s1, t10) + 0.3 * seg(t, tgiro, tgiro + 1.5) + 0.52 * seg(t, tabre, tabre + 2.2)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    over, do = Z.new_layer(); under, du = Z.new_layer()
    abre = seg(t, tabre - 0.2, tabre + 2.4)
    # ---------- el mar ----------
    Z.mar_alto(d, g, 620, W + 20, 250, t, abre=abre, gx=GX, hmax=470)
    # ---------- lo que no se ve: grietas bajo el miedo, raíces bajo la confianza ----------
    Z.grietas(d, 372, (0.5 * seg(t, s1, s1 + 1.5) + 0.5 * seg(t, t10, tq + 1)) * (1 - seg(t, tabre, tabre + 1.5)), seed=9)
    Z.roots(d, 0.15 * seg(t, 0.5, 2.5) + 0.85 * seg(t, tgiro + 0.3, tabre + 1.5), x0=XM)
    # ---------- el ejército (por la izquierda) ----------
    avance = lerp(-260, -40, seg(t, 0.0, 3.5)) + 110 * seg(t, s1, t10 + 0.5) + 110 * seg(t, t10, tq + 0.5)
    para = seg(t, tgiro, tgiro + 1.0)                     # se detienen cuando habla Musa
    av = 1 - para
    a_ej = 230 * (1 - 0.45 * seg(t, tabre, tabre + 2))
    for i in range(6):
        x = avance - i * 62 - (i % 2) * 18
        if x > -60: Z.soldado(do, g, x, t * av + para * 10, k=0.9 - 0.04 * (i % 3), alpha=a_ej, antorcha=(i % 2 == 0), ph=i * 1.1, andar=av)
    Z.polvo(du, avance - 400, avance + 40, (0.4 + 0.6 * seg(t, s1, t10)) * av, t)
    # ---------- su gente: MIEDO ----------
    miedo = seg(t, s1, s1 + 0.6) * (1 - seg(t, tabre + 0.6, tabre + 1.6))
    camina = seg(t, tfin - 1.2, tfin + 3.0)
    for i, (x, ph) in enumerate(GENTE):
        p = Z.lerp_pose(P["stand"], Z.MIEDO, miedo)
        if miedo > 0: p = {j: (v[0] + 3 * math.sin(t * 9 + ph) * miedo, v[1]) for j, v in p.items()}
        if camina > 0: p = Z.lerp_pose(p, Z.walk_pose(t * 5 + ph, amp=0.8), min(1, camina * 3))
        xx = x + (GX - 120 + i * 70 - x) * camina
        Z.mini_figure(d, xx, p, k=0.78, alpha=int(255 * (1 - 0.5 * camina * (i == 0))))
    # ---------- Musa: CONFIANZA ----------
    alza = seg(t, tbast + 0.5, tbast + 1.4) * (1 - seg(t, tabre - 0.45, tabre - 0.2))
    golpe = seg(t, tabre - 0.45, tabre - 0.15) * (1 - seg(t, tabre + 2.0, tabre + 2.8))
    mp = dict(P["stand"]); mp["re"] = (30, -214); mp["rh"] = (40, -168)
    mp = Z.lerp_pose(mp, dict(mp, re=(44, -268), rh=(64, -330), head=(4, -302)), alza)
    mp = Z.lerp_pose(mp, dict(mp, re=(48, -236), rh=(96, -238)), golpe)
    xm = XM + (GX - 40 - XM) * camina
    if camina > 0: mp = Z.lerp_pose(mp, Z.walk_pose(t * 5, amp=0.8), min(1, camina * 3))
    figure(d, xm, mp)
    ang = lerp(lerp(0.0, -2.75, alza), -1.9, golpe)
    hx, hy = xm + mp["rh"][0], GY + mp["rh"][1]
    tipx, tipy = Z.baston(d, hx, hy, ang, largo=250)
    if t > tgiro: g.ellipse([xm - 140, GY - 400, xm + 140, GY + 20], fill=(80, 230, 225, int(70 * seg(t, tgiro, tgiro + 1.5))))
    if alza > 0.5: g.ellipse([tipx - 50, tipy - 50, tipx + 50, tipy + 50], fill=(150, 245, 238, int(160 * alza)))
    Z.anillos(d, 650, GY - 200, t, tabre - 0.2, 2.4, rmax=220)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, tgiro - 0.4, tgiro))
    if la > 0:
        spaced(d, "MIEDO", 250, 330, 46, la); spaced(d, "CONFIANZA", 680, 330, 46, la)
        etapa = "EL MAR DELANTE" if t < s1 else ("EL EJÉRCITO DETRÁS" if t < t10 else "SIN SALIDA")
        pulse = 1 + 0.25 * max(0, 1 - abs(t - s1) * 3) + 0.25 * max(0, 1 - abs(t - t10) * 3)
        spaced(d, etapa, W / 2, 405, int(36 * pulse), la * 0.85, col=(200, 225, 222))
    Z.subs(d, t, [(0.6, s1 - 0.15, "MUSA Y SU GENTE, HUYENDO"), (t10, tq - 0.1, "CADA VEZ MÁS CERCA")])
    if s1 + 0.3 < t < tq + 0.2:
        Z.bocadillo(d, 372, GY - 330, "¡NOS ALCANZAN!", alpha=255 * seg(t, s1 + 0.3, s1 + 0.7) * (1 - seg(t, tq - 0.2, tq + 0.2)), size=32, cola=1)
    Z.pregunta(d, t, tq, tgiro, "¿TÚ QUÉ HABRÍAS DICHO?")
    Z.fuente(d, t, tgiro, tfin, ["«¡NO! MI SEÑOR", "ESTÁ CONMIGO,", "ÉL ME GUIARÁ»"], "CORÁN 26:61-63")
    Z.final(d, t, tfin, "CUANDO NO VES SALIDA,", "ALLAH ABRE UN CAMINO.", task, "¿CUÁL ES TU MAR", "AHORA MISMO?")
    return Z.finish(base, fg, glow, bright, over=over, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
