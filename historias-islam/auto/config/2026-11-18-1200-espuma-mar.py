# Estilo Noche · SE OLVIDA vs SUBHANALLAH · "la espuma del mar" (Sahih al-Bujari 6405)
# Apuesta segura: hábito diario de la sunnah + «lo invisible» (como BISMILLAH en casa, 916 TikTok).
# Bajo el suelo de los dos aparece la misma espuma oscura (los errores). Uno sigue sin más y su espuma crece día a día.
# El otro repite 100 veces «subhanallahi wa bihamdihi» (tasbih + contador 0→100) y una ola de luz barre su espuma:
# cada burbuja se vuelve una gota turquesa que sube. Día 30: un mar lleno de espuma vs un mar limpio que brilla.
# Uso (desde la raíz del repo): python3 historias-islam/auto/config/2026-11-18-1200-espuma-mar.py salida.mp4 [t1 t2 ... fotogramas]
import math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "plantilla", "noche"))
import piezas as Z
from noche import S, W, GY, CREAM, GOLD, seg, lerp, P, pose_mix, figure, spaced

OUT = sys.argv[1]; TMP = os.path.splitext(OUT)[0]
LINES = ["Los mismos errores. Pero solo uno los ve desaparecer.",
         "Uno sigue su día, sin más.",
         "El otro repite cien veces: subjanal-láhi wa bijamdihi.",
         "Día diez.",
         "¿De quién crees que se borran?",
         "Día treinta.",
         "El Profeta, la paz sea con él, dijo: quien la diga cien veces al día, sus pecados se borran, aunque sean como la espuma del mar.",
         "Unos dos minutos al día.",
         "¿La has dicho hoy? Escríbela abajo."]
PAUSAS = [0.6, 0.5, 0.8, 0.5, 2.0, 0.6, 0.8, 0.8, 1.4]
def SFX(s): return [dict(t=s[2] + 2.6, f=1320, dur=0.8, v=0.06), dict(t=s[5], f=660, dur=2.0, v=0.08), dict(t=s[5] + 0.15, f=990, dur=2.0, v=0.06)]
GUION = os.path.join(HERE, "2026-11-18-1200-espuma-mar.guion.json")
if os.environ.get("NOVOZ"):
    g_ = json.load(open(GUION)); starts, ends, DUR = g_["starts"], g_["ends"], g_["duration"]
else:
    starts, ends, DUR = Z.voz(LINES, PAUSAS, TMP + ".wav", SFX, guion=GUION, speed=1.04)
s0, s1, s2, t10, tq, t30, thad, tfin, task = starts
print("DUR", DUR, starts, ends)

LX, RX = 280, 760
LS = (40, 520); RS = (565, 1040)               # mar de cada uno (bajo el suelo)

def frame(t):
    bright = 0.12 + 0.1 * seg(t, t10, t10 + 1.0) + 0.78 * seg(t, t30 + 0.3, t30 + 2.8)
    base, fg, d, glow, g = Z.base_frame(t, bright)
    # ---------- lo que no se ve: el mar y la espuma ----------
    Z.mar(d, t, 0.6 + 0.4 * seg(t, 0.0, 1.2))
    if t > t30 + 0.5:                                   # el mar del que recuerda brilla
        g.ellipse([RS[0] - 20, GY - 40, RS[1] + 20, GY + 500], fill=(90, 235, 228, int(80 * seg(t, t30 + 0.5, t30 + 2.5))))
    # mismos errores al principio (los dos)
    k0 = 0.12 + 0.23 * seg(t, 0.3, 2.6)
    # izquierda: crece día a día y se queda
    kl = k0 + 0.25 * seg(t, s1 + 0.3, s2) + 0.2 * seg(t, t10, t10 + 1.5) + 0.2 * seg(t, t30, t30 + 1.5)
    Z.espuma(d, g, LS[0], LS[1], kl, t, seed=3, n=80)
    # derecha: el mismo arranque; al llegar a 100 la ola lo limpia. Día 10 vuelve un poco y se limpia otra vez.
    w1a, w1b = s2 + 2.4, s2 + 4.0                     # primera ola (cuando el contador llega a 100)
    w2a, w2b = t10 + 1.6, t10 + 3.0                   # segunda ola (día 10)
    Z.espuma(d, g, RS[0], RS[1], k0, t, limpio=seg(t, w1a, w1b), seed=5, n=80)
    Z.espuma(d, g, RS[0], RS[1], 0.25 * seg(t, t10 - 0.6, t10 + 0.3), t, limpio=seg(t, w2a, w2b), seed=9, n=80)
    Z.ola_luz(d, g, RS[0], RS[1] + 30, seg(t, w1a, w1b)); Z.ola_luz(d, g, RS[0], RS[1] + 30, seg(t, w2a, w2b))
    if t > t30:                                       # luz que sube del mar limpio
        for i in range(int(14 * seg(t, t30 + 0.6, t30 + 3.0))):
            ph = (t * 0.35 + i / 14) % 1
            Z.gota(d, g, RS[0] + 40 + (i * 37) % (RS[1] - RS[0] - 80), GY + 420 - ph * 640, r=5 * (1 - ph) + 2, alpha=220 * (1 - ph))
    # ---------- IZQUIERDA: SE OLVIDA ----------
    lp = P["stand"] if t < t30 + 0.6 else pose_mix("stand", "sad", seg(t, t30 + 0.6, t30 + 1.8))
    ph = seg(t, s1, s1 + 0.5) * (1 - seg(t, t30, t30 + 0.5))      # sigue su día con el móvil
    if t < t30 + 0.6: lp = {j: (lerp(P["stand"][j][0], Z.PHONE[j][0], ph), lerp(P["stand"][j][1], Z.PHONE[j][1], ph)) for j in P["stand"]}
    figure(d, LX, lp, alpha=int(255 * (1 - 0.25 * seg(t, t30, t30 + 1.5))))
    Z.movil(d, g, LX + 34, GY - 272, alpha=255 * ph)
    # ---------- DERECHA: SUBHANALLAH x100 ----------
    rep1 = seg(t, s2 + 0.2, s2 + 2.4)                 # cuenta 0 → 100
    rep2 = seg(t, t10 + 0.1, t10 + 1.5)               # el día 10 otra vez
    act = (1 if (s2 + 0.2 < t < s2 + 2.4) or (t10 + 0.1 < t < t10 + 1.5) else 0.0)
    hold = seg(t, s2, s2 + 0.4) * (1 - seg(t, t30 + 0.6, t30 + 1.0))
    if t < t30 + 0.8: rp = {j: (lerp(P["stand"][j][0], Z.DHIKR[j][0], hold), lerp(P["stand"][j][1], Z.DHIKR[j][1], hold)) for j in P["stand"]}
    else: rp = pose_mix("stand", "joy", seg(t, t30 + 0.8, t30 + 1.5) * (1 - seg(t, thad + 3.5, thad + 4.3)))
    figure(d, RX, rp)
    Z.tasbih(d, g, RX + 52, GY - 228, t, activo=act, alpha=255 * hold)
    if s2 < t < t30 + 0.5:
        n = 100 * rep1 if t < t10 else 100 * rep2
        ca = 255 * seg(t, s2, s2 + 0.3) * (1 - seg(t, t30, t30 + 0.5))
        if t10 - 0.4 < t < t10 + 0.1: ca *= 0.3
        Z.contador(d, RX, GY - 380, n, ca, size=38)
    # ---------- TEXTOS ----------
    la = 255 * (1 - seg(t, thad - 0.4, thad))
    if la > 0: Z.labels(d, t, la, "SE OLVIDA", "SUBHANALLAH", t10, t30, 44)
    Z.subs(d, t, [(-0.3, 2.0, "LOS MISMOS ERRORES..."), (2.0, s1 - 0.15, "SOLO UNO LOS VE DESAPARECER"), (s1, s2 - 0.15, "UNO SIGUE SU DÍA, SIN MÁS"), (s2, t10 - 0.1, "EL OTRO LA REPITE 100 VECES")])
    if s2 + 0.3 < t < t10 - 0.1:
        al = 255 * seg(t, s2 + 0.3, s2 + 0.8) * (1 - seg(t, t10 - 0.4, t10 - 0.1))
        spaced(d, "«SUBHANALLAHI WA BIHAMDIHI»", W / 2, 600, Z.fit("«SUBHANALLAHI WA BIHAMDIHI»", 36, 760), al, col=(150, 240, 232))
        spaced(d, "GLORIFICADO SEA ALLAH, Y ALABADO", W / 2, 652, Z.fit("GLORIFICADO SEA ALLAH, Y ALABADO", 26, 760, 0.22), al * 0.85, bold=False, track=0.22, col=(190, 225, 222))
    Z.pregunta(d, t, tq, t30, "¿DE QUIÉN SE BORRAN?")
    Z.fuente(d, t, thad, tfin, ["«100 VECES AL DÍA:", "SUS PECADOS SE BORRAN,", "AUNQUE SEAN COMO", "LA ESPUMA DEL MAR»"], "SAHIH AL-BUJARI 6405")
    Z.final(d, t, tfin, "100 VECES.", "UNOS 2 MINUTOS AL DÍA.", task, "¿LA HAS DICHO HOY?", "ESCRIBE: SUBHANALLAH")
    return Z.finish(base, fg, glow, bright)

if len(sys.argv) > 2: Z.fotogramas(frame, sys.argv[2:], TMP)
else: Z.render(frame, DUR, TMP + ".wav", OUT); print("OK", OUT)
