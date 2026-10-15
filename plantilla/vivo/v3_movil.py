import sys, math
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import vivo as V
from vivo import *

DUR = 40.0
V.TALK.extend([(0.5, 5.2), (6.4, 11.4), (13.4, 19.0), (20.8, 25.4), (27.0, 31.8), (34.0, 38.6)])

def phone():
    im = icon_canvas(300, 520); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, 280, 500], 46, fill=INK)
    d.rounded_rectangle([38, 60, 262, 440], 26, fill=CYAN)
    d.rounded_rectangle([110, 34, 190, 46], 6, fill=(80, 80, 110))
    # icono contactless
    for i, r in enumerate([40, 75, 110]):
        d.arc([150 - r, 250 - r, 150 + r, 250 + r], -50, 50, fill=WHITE, width=14)
    d.ellipse([140, 240, 160, 260], fill=WHITE)
    return im
PHONE = phone()

def banknote():
    im = icon_canvas(420, 230); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 410, 220], 26, fill=LIME, outline=INK, width=8)
    d.ellipse([150, 50, 270, 170], fill=(120, 220, 60), outline=INK, width=6)
    e = text_img("€", 80, INK, F_BLACK, 0, False)
    im.alpha_composite(e, (210 - e.width // 2, 112 - e.height // 2))
    return im
NOTE = banknote()

def scene1(dst, t):
    end = 6.0
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Pagar", WHITE), ("con", WHITE), ("el", WHITE), ("MÓVIL", CYAN), ("te", WHITE), ("hace", WHITE), ("gastar", WHITE)], W / 2, 400, 88, t, 0.4, out_t=end - 0.35)
    p = prog(t, 1.5, 0.5)
    if p > 0:
        paste_center(dst, PHONE, W / 2 - 160, 790, 0.3 + 0.7 * ease_out_back(p, 2.6), fade, -8 + math.sin(t * 4) * 4)
    p = prog(t, 2.4, 0.4)
    if p > 0:
        paste_center(dst, badge("MÁS", 150, YELLOW), W / 2 + 210, 760, 0.3 + 0.7 * ease_out_back(p, 3), fade, 6 + math.sin(t * 6) * 3)
    draw_moni(dst, t, W / 2, 1400, 0.88, 1.0, "surprised", "up", enter=0.2)

def scene2(dst, t):
    a = 6.0; end = 13.0
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("En", WHITE), ("EFECTIVO", LIME), ("ves", WHITE), ("cómo", WHITE), ("se", WHITE), ("va", WHITE), ("tu", WHITE), ("dinero", WHITE)], W / 2, 420, 82, t, a + 0.2, out_t=end - 0.35)
    for i in range(3):
        st = a + 1.6 + i * 0.7
        if t < st: continue
        k = int((t - st) // 2.1)
        p = prog(t, st + k * 2.1, 1.9)
        if p > 0 and p < 1:
            x = W / 2 - 200 + ease_in_out(p) * 420 + i * 30
            y = 780 + i * 60 - math.sin(p * math.pi) * 160
            paste_center(dst, NOTE, x, y, 0.9, min(1, p * 4) * (1 - prog(p, 0.85, 0.15)) * fade, -10 + p * 30)
    p = prog(t, a + 3.6, 0.45)
    if p > 0:
        paste_center(dst, badge("…y DUELE", 90, PINK, WHITE), W / 2, 1080, 0.3 + 0.7 * ease_out_back(p, 3), fade, -4)
    draw_moni(dst, t, 170, 1430, 0.6, 1.0, "sly", "point")

def scene3(dst, t):
    a = 13.0; end = 20.4
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Con", WHITE), ("el", WHITE), ("móvil", WHITE), ("solo", WHITE), ("haces…", WHITE)], W / 2, 360, 84, t, a + 0.2, out_t=end - 0.35)
    p = prog(t, a + 1.3, 0.4)
    if p > 0:
        pulse = 1 + 0.08 * abs(math.sin(t * 8))
        paste_center(dst, text_img("¡BIP!", 170, CYAN, F_BLACK), W / 2, 560, (0.3 + 0.7 * ease_out_back(p, 3.2)) * pulse, fade, -5)
    for i, (top, low, col, gx) in enumerate([("EFECTIVO", "DUELE", LIME, W / 2 - 235), ("MÓVIL", "NI LO NOTAS", CYAN, W / 2 + 235)]):
        p = prog(t, a + 2.4 + i * 0.6, 0.45)
        if p > 0:
            card = sticker_card(420, 300, WHITE).copy()
            t1 = text_img(top, 62, col, F_BLACK)
            card.alpha_composite(t1, ((420 - t1.width) // 2, 50))
            t2 = text_img(low, 66 if len(low) < 8 else 52, INK, F_BLACK, 0, False)
            card.alpha_composite(t2, ((420 - t2.width) // 2, 180))
            paste_center(dst, card, gx, 870, 0.4 + 0.6 * ease_out_back(p, 2.4), ease_out_cubic(p) * fade, -3 if i == 0 else 3)
    pop_words(dst, [("…y", WHITE), ("gastas", WHITE), ("sin", WHITE), ("darte", WHITE), ("cuenta", YELLOW)], W / 2, 1110, 66, t, a + 4.0, out_t=end - 0.35, max_w=1000)
    draw_moni(dst, t, W / 2, 1430, 0.6, 1.0, "surprised", "down")

def scene4(dst, t):
    a = 20.4; end = 26.6
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Los", WHITE), ("psicólogos", WHITE), ("lo", WHITE), ("llaman", WHITE)], W / 2, 400, 82, t, a + 0.2, out_t=end - 0.35)
    p = prog(t, a + 1.2, 0.45)
    if p > 0:
        card = sticker_card(860, 300, YELLOW).copy()
        t1 = text_img("EL DOLOR", 110, INK, F_BLACK, 0, False)
        t2 = text_img("DE PAGAR", 110, PINK, F_BLACK)
        card.alpha_composite(t1, ((860 - t1.width) // 2, 30))
        card.alpha_composite(t2, ((860 - t2.width) // 2, 145))
        paste_center(dst, card, W / 2, 680, 0.3 + 0.7 * ease_out_back(p, 2.6), ease_out_cubic(p) * fade, -3 + math.sin(t * 3) * 1.5)
    pop_words(dst, [("¡Y", WHITE), ("las", WHITE), ("tiendas", WHITE), ("lo", WHITE), ("SABEN!", CYAN)], W / 2, 1000, 78, t, a + 3.0, out_t=end - 0.35)
    draw_moni(dst, t, W - 210, 1420, 0.62, 1.0, "sly", "point")

def scene5(dst, t):
    scene_truco(dst, t, 26.6, 33.8,
                [("Ponte", INK), ("un", INK), ("LÍMITE", PINK), ("SEMANAL", PINK)],
                [("y", WHITE), ("mira", WHITE), ("tu", WHITE), ("SALDO", YELLOW), ("cada", WHITE), ("noche", WHITE)])

def scene6(dst, t): scene_outro(dst, t, 33.8)

SCENES = [(0, 6.0, scene1), (6.0, 13.0, scene2), (13.0, 20.4, scene3), (20.4, 26.6, scene4), (26.6, 33.8, scene5), (33.8, 40.0, scene6)]

if __name__ == "__main__":
    main(SCENES, DUR)
