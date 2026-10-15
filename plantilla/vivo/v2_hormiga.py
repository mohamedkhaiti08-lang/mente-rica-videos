import sys, math
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import vivo as V
from vivo import *

DUR = 40.0
V.TALK.extend([(0.5, 5.0), (6.4, 11.4), (13.4, 19.2), (20.8, 25.4), (27.0, 32.0), (34.0, 38.6)])

def coffee_cup():
    im = icon_canvas(380, 420); d = ImageDraw.Draw(im)
    d.ellipse([200, 200, 320, 320], outline=INK, width=36)
    d.ellipse([214, 214, 306, 306], outline=WHITE, width=12)
    ink_poly(d, [(40, 150), (270, 150), (240, 400), (70, 400)], WHITE)
    ink_poly(d, [(55, 230), (255, 230), (246, 300), (63, 300)], PINK)
    ink_poly(d, [(25, 110), (285, 110), (285, 155), (25, 155)], (120, 60, 30))
    for i, x in enumerate([100, 155, 210]):
        d.arc([x - 20, 10, x + 20, 70], 90, 270, fill=WHITE, width=10)
        d.arc([x - 20, 50, x + 20, 105], 270, 90, fill=WHITE, width=10)
    return im
CUP = coffee_cup()

def scene1(dst, t):
    end = 6.0
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Este", WHITE), ("CAFÉ", YELLOW), ("te", WHITE), ("cuesta…", WHITE)], W / 2, 380, 96, t, 0.4, out_t=end - 0.35)
    p = prog(t, 1.2, 0.5)
    if p > 0:
        paste_center(dst, CUP, W / 2 - 270, 730, 0.25 + 0.6 * ease_out_back(p, 2.6), fade, math.sin(t * 4) * 6)
    p = prog(t, 2.0, 0.45)
    if p > 0:
        shake = math.sin(t * 40) * 6 * (1 - prog(t, 2.0, 0.8))
        paste_center(dst, text_img("730€", 200, LIME, F_BLACK), W / 2 + 175 + shake, 720, 0.3 + 0.7 * ease_out_back(p, 3), fade, -6)
    p = prog(t, 2.9, 0.4)
    if p > 0:
        paste_center(dst, badge("¡AL AÑO!", 90, PINK, WHITE), W / 2, 1010, 0.3 + 0.7 * ease_out_back(p, 3), fade, 4 + math.sin(t * 5) * 2)
    draw_moni(dst, t, W / 2, 1400, 0.88, 1.0, "surprised", "up", enter=0.2)

def scene2(dst, t):
    a = 6.0; end = 13.0
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Haz", WHITE), ("la", WHITE), ("cuenta:", YELLOW)], W / 2, 380, 92, t, a + 0.2, out_t=end - 0.35)
    rows = [("2€", "cada día", CYAN), ("× 365", "días", PINK)]
    for i, (big, small, col) in enumerate(rows):
        p = prog(t, a + 1.1 + i * 0.9, 0.45)
        if p > 0:
            card = sticker_card(760, 190, WHITE).copy()
            b = text_img(big, 120, col, F_BLACK)
            card.alpha_composite(b, (50, (190 - b.height) // 2))
            s_ = text_img(small, 64, INK, F_BLACK, 0, False)
            card.alpha_composite(s_, (760 - s_.width - 60, (190 - s_.height) // 2))
            paste_center(dst, card, W / 2, 590 + i * 230, 0.4 + 0.6 * ease_out_back(p, 2.2), ease_out_cubic(p) * fade, -2 if i else 2)
    p = prog(t, a + 3.1, 1.4)
    if p > 0:
        val = int(round(ease_out_cubic(p) * 730))
        num = text_img(f"= {val}€", 160, LIME, F_BLACK)
        paste_center(dst, num, W / 2, 1090, 0.6 + 0.4 * ease_out_back(prog(t, a + 3.1, 0.45), 2.5), fade)
    draw_moni(dst, t, W - 210, 1430, 0.6, 1.0, "sly", "point")

ITEMS = [("Bebida  2€", CYAN, -230, 760, -6), ("Snack  1,50€", YELLOW, 220, 850, 6), ("App  0,99€", LIME, -190, 950, 4), ("Envío  3€", PINK, 230, 1050, -5)]
def scene3(dst, t):
    a = 13.0; end = 20.4
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Son", WHITE), ("los", WHITE), ("GASTOS", YELLOW), ("HORMIGA", YELLOW)], W / 2, 370, 92, t, a + 0.2, out_t=end - 0.35)
    pop_words(dst, [("pequeñitos…", WHITE), ("¡pero", WHITE), ("SUMAN!", PINK)], W / 2, 600, 70, t, a + 1.4, out_t=end - 0.35)
    for i, (txt, col, dx, y, r) in enumerate(ITEMS):
        p = prog(t, a + 2.3 + i * 0.45, 0.4)
        if p > 0:
            paste_center(dst, badge(txt, 56, col), W / 2 + dx, y, 0.3 + 0.7 * ease_out_back(p, 3), fade, r + math.sin(t * 3 + i) * 3)
    draw_moni(dst, t, W / 2, 1420, 0.66, 1.0, "surprised", "down")

def scene4(dst, t):
    a = 20.4; end = 26.6
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Con", WHITE), ("730€", LIME), ("te", WHITE), ("pagas…", WHITE)], W / 2, 380, 92, t, a + 0.2, out_t=end - 0.35)
    for i, (txt, col, y, r) in enumerate([("UN VIAJE", CYAN, 620, -5), ("UN MÓVIL", YELLOW, 820, 4), ("UNA CONSOLA", PINK, 1020, -3)]):
        p = prog(t, a + 1.0 + i * 0.8, 0.45)
        if p > 0:
            paste_center(dst, badge(txt, 90, col, INK if col != PINK else WHITE), W / 2, y, 0.3 + 0.7 * ease_out_back(p, 3), fade, r + math.sin(t * 4 + i) * 2)
    draw_moni(dst, t, W / 2, 1420, 0.66, 1.0, "happy", "up", jump=True)

def scene5(dst, t):
    scene_truco(dst, t, 26.6, 33.8,
                [("Apunta", INK), ("TODO", PINK), ("lo", INK), ("que", INK), ("gastas", INK), ("durante", INK), ("7", PINK), ("DÍAS", PINK)],
                [("¡Te", WHITE), ("vas", WHITE), ("a", WHITE), ("SORPRENDER!", YELLOW)])

def scene6(dst, t): scene_outro(dst, t, 33.8)

SCENES = [(0, 6.0, scene1), (6.0, 13.0, scene2), (13.0, 20.4, scene3), (20.4, 26.6, scene4), (26.6, 33.8, scene5), (33.8, 40.0, scene6)]

if __name__ == "__main__":
    main(SCENES, DUR)
