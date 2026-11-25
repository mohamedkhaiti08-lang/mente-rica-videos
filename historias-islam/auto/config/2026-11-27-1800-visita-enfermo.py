# Estilo Noche · SE QUEDA vs VA A VERLE · "¿Sabes qué pasa cuando visitas a un enfermo?" (Sahih Muslim 2568)
# Explorar: «lo que ves vs lo que Allah ve» (arriba/abajo del suelo) con un acto concreto del día a día.
# Un amigo enfermo en la cama, entre los dos. Uno se queda en casa con el móvil («ya iré otro día»). El otro va a verle:
# arriba solo es una calle gris con llovizna, pero cada paso deja una huella de luz y, «mira debajo», bajo su camino crece
# un JARDÍN DE LUZ hacia abajo (árboles invertidos con frutas doradas). Día 30: jardín lleno; giro: el cielo se ilumina.
# Objetos nuevos: huellas de luz, árboles de luz que crecen hacia abajo con frutas, bocadillo de pensamiento.
# Uso: python3 2026-11-27-1800-visita-enfermo.py salida.mp4 [t1 t2 ...]   (NOVOZ=1 reutiliza el guion)
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["¿Sabes qué pasa cuando visitas a un enfermo?",
         "Uno dice: ya iré otro día.",
         "El otro coge el abrigo y va.",
         "Arriba, solo es una calle gris.",
         "Pero mira debajo.",
         "Día treinta.",
         "¿Quién ha caminado por el Paraíso?",
         "Cada paso hacia el enfermo, era un jardín.",
         "El Profeta, la paz sea con él, dijo: quien visita a un enfermo, sigue en el jardín del Paraíso hasta que vuelve.",
         "Ve a verle. Hoy.",
         "¿A quién vas a visitar esta semana? Escribe su nombre."]
PAUSAS = [0.4, 0.7, 1.4, 0.6, 1.5, 0.7, 1.9, 0.6, 0.6, 0.5, 1.2]
def SFX(s): return [dict(t=s[4] + 0.9, f=1320, dur=0.8, v=0.06), dict(t=s[5] + 0.7, f=1320, dur=0.8, v=0.05),
                    dict(t=s[7] - 0.3, f=660, dur=2.0, v=0.08), dict(t=s[7] - 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-27-1800-visita-enfermo.guion.json")
if os.environ.get("NOVOZ"):
    import json; g_ = json.load(open(GUION)); starts, DUR = g_["starts"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.08)
s0, s1, s2, t10, smira, t30, tq, tgiro, thad, tfin, task = starts
print("DUR", DUR, starts)

FL = 150                                  # el que se queda (en su casa)
BED = (330, 610)                          # cama del amigo enfermo
FR0, FR1 = 1000, 690                       # el que va: sale de aquí y llega aquí
TEAL = (130, 240, 232)
GRIS = (120, 116, 126)
ARBOLES = [(715, 2), (840, 5), (965, 8)]  # (x, semilla) del jardín bajo el camino

def frame(t):
    bright = 0.1 + 0.1 * seg(t, smira, smira + 1.5) + 0.8 * seg(t, tgiro - 0.2, tgiro + 2.4)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    under, du = Z.new_layer()
    # ---------- casa del que se queda ----------
    Z.casa(d, 20, 290, wall_h=340, roof_h=120)
    Z.ventana(d, g, 232, GY - 250, 0.3)
    # ---------- amigo enfermo en la cama ----------
    yc = Z.cama(d, *BED, almohada="l")
    Z.tumbar(d, BED[1] - 14, 1.0, yc, lado=-1)
    Z.manta(d, BED[0] + 110, BED[1] - 6, yc)
    Z.gotas_sudor(d, BED[0] + 40, yc - 70, t, alpha=255 * (1 - seg(t, tgiro, tgiro + 1.5)))
    if t > tgiro: g.ellipse([BED[0] - 40, yc - 160, BED[1] + 40, GY + 20], fill=(80, 230, 225, int(70 * seg(t, tgiro, tgiro + 2))))
    # ---------- IZQUIERDA: se queda con el móvil ----------
    lp = Z.lerp_pose(P["stand"], Z.PHONE, seg(t, s1 - 0.4, s1 + 0.2))
    lp = Z.lerp_pose(lp, Z.espejo(P["sad"]), seg(t, tgiro + 0.4, tgiro + 1.6))
    figure(d, FL, lp, alpha=int(255 - 70 * seg(t, tgiro, tgiro + 1.5)))
    Z.movil(d, g, FL + 30, GY - 272, alpha=255 * seg(t, s1 - 0.4, s1 + 0.2) * (1 - seg(t, tgiro + 0.4, tgiro + 1.0)))
    for a_, b_, txt in ((s1, s2 + 1.2, "YA IRÉ OTRO DÍA"), (t10 + 0.2, smira - 0.2, "OTRO DÍA…"), (t30 + 0.1, tq - 0.2, "MAÑANA…")):
        al = 255 * seg(t, a_, a_ + 0.3) * (1 - seg(t, b_ - 0.3, b_))
        if al > 0: Z.pensamiento(d, 320, GY - 480, txt, alpha=al, size=24, hacia=(FL + 20, GY - 330))
    # ---------- DERECHA: va a verle ----------
    u = seg(t, s2 + 0.2, s2 + 2.6)
    x = lerp(FR0, FR1, u)
    if 0 < u < 1:
        rp = Z.espejo(Z.walk_pose(t * 7.0, amp=0.9))
    else:
        rp = P["stand"] if u == 0 else Z.lerp_pose(P["stand"], Z.espejo(P["give"]), seg(t, s2 + 2.6, s2 + 3.2) * (1 - seg(t, tgiro + 0.2, tgiro + 0.8)))
    rp = Z.lerp_pose(rp, P["joy"], seg(t, tgiro + 0.3, tgiro + 1.0) * (1 - seg(t, thad + 1.0, thad + 1.6)))
    figure(d, x, rp)
    # huellas: grises arriba hasta que «mira debajo» las revela como luz
    rev = seg(t, smira, smira + 0.8)
    for i in range(10):
        hx = FR0 - 22 - i * 31
        if x < hx + 6 or u >= 1:
            col = tuple(int(lerp(a_, b_, rev)) for a_, b_ in zip(GRIS, TEAL))
            Z.huella(d, g, hx, 120 + 135 * rev, col=col)
    # calle gris: nube con llovizna sobre el camino (arriba no se ve nada especial)
    Z.nube(d, 850, 720, 220 * seg(t, t10, t10 + 0.8) * (1 - seg(t, tgiro - 0.2, tgiro + 0.8)), t, lluvia=1.0)
    # ---------- lo que no se ve: jardín de luz bajo el camino ----------
    for j, (ax, sd) in enumerate(ARBOLES):
        k = 0.45 * seg(t, smira + 0.2 * j, smira + 1.4 + 0.2 * j) + 0.3 * seg(t, t30 + 0.1 * j, t30 + 1.2) + 0.25 * seg(t, tgiro, tgiro + 1.4)
        Z.arbol_invertido(d, g, ax, k, t, alto=350 - 40 * (j % 2), seed=sd, frutas=seg(t, t30 + 0.4, tq) + seg(t, tgiro, tgiro + 1.5))
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, tgiro - 0.4, tgiro))
    if la > 0: Z.labels(d, t, la, "SE QUEDA", "VA A VERLE", t10, t30, 46, lx=230, rx=760)
    Z.subs(d, t, [(-0.4, s1 - 0.15, "¿QUÉ PASA CUANDO VISITAS A UN ENFERMO?"), (s2, t10 - 0.1, "EL OTRO COGE EL ABRIGO Y VA"),
                  (t10, smira - 0.1, "ARRIBA, SOLO UNA CALLE GRIS"), (smira, t30 - 0.1, "PERO MIRA DEBAJO ↓")])
    Z.pregunta(d, t, tq, tgiro, "¿QUIÉN PASEÓ POR EL PARAÍSO?")
    if tgiro <= t < thad:
        al = 255 * seg(t, tgiro, tgiro + 0.4) * (1 - seg(t, thad - 0.4, thad))
        spaced(d, "CADA PASO HACIA ÉL", W / 2, 360, Z.fit("CADA PASO HACIA ÉL", 52, 760), al)
        spaced(d, "ERA UN JARDÍN.", W / 2, 440, Z.fit("ERA UN JARDÍN.", 48, 760), al * seg(t, tgiro + 1.0, tgiro + 1.5), col=(190, 225, 222))
    Z.fuente(d, t, thad, tfin, ["«QUIEN VISITA A UN ENFERMO", "SIGUE EN EL JARDÍN", "DEL PARAÍSO", "HASTA QUE VUELVE»"], "SAHIH MUSLIM 2568")
    Z.final(d, t, tfin, "VE A VERLE.", "HOY.", task, "¿A QUIÉN VAS A VISITAR?", "ESCRIBE SU NOMBRE")
    return Z.finish(base, fg, glow, bright, under=under)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
