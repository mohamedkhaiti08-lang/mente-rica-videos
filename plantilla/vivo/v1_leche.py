import sys, math
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import vivo as V
from vivo import *

DUR = 40.0
V.TALK.extend([(0.5, 4.8), (6.4, 11.6), (13.4, 19.0), (20.8, 25.6), (27.0, 32.6), (34.0, 38.6)])

def milk_carton(scale=1.0):
    w, h = 300, 440
    im = icon_canvas(w + 20, h + 20); d = ImageDraw.Draw(im)
    ink_poly(d, [(40, 150), (260, 150), (260, 420), (40, 420)], WHITE)
    ink_poly(d, [(40, 150), (150, 40), (260, 150)], (230, 240, 255))
    ink_poly(d, [(110, 10), (190, 10), (190, 50), (110, 50)], CYAN)
    ink_poly(d, [(40, 230), (260, 230), (260, 330), (40, 330)], CYAN)
    tx = text_img("LECHE", 52, WHITE, F_BLACK)
    im.alpha_composite(tx, (150 - tx.width // 2, 280 - tx.height // 2))
    return im
MILK = milk_carton()

def store_map():
    w, h = 820, 520
    im = sticker_card(w, h, WHITE).copy(); d = ImageDraw.Draw(im)
    for i in range(3):
        y = 120 + i * 120
        d.rounded_rectangle([90, y, 600, y + 50], 14, fill=(255, 200, 230), outline=INK, width=5)
    d.rounded_rectangle([660, 40, 780, 470], 18, fill=CYAN, outline=INK, width=5)
    lab = text_img("LECHE", 34, WHITE, F_BLACK)
    im.alpha_composite(lab.rotate(90, expand=True), (720 - lab.height // 2, 255 - lab.width // 2))
    ent = text_img("ENTRADA", 32, INK, F_BLACK, stroke=0, shadow=False)
    im.alpha_composite(ent, (40, h - 70))
    return im
MAP = store_map()
PATH = [(90, 450), (630, 450), (630, 350), (60, 350), (60, 230), (630, 230), (630, 110), (60, 110), (60, 60), (650, 60)]

def scene1(dst, t):
    pop_words(dst, [("¿Por", WHITE), ("qué", WHITE), ("la", WHITE), ("LECHE", CYAN), ("siempre", WHITE), ("está", WHITE)], W / 2, 400, 92, t, 0.4, out_t=5.6)
    p = prog(t, 1.3, 0.5)
    if p > 0:
        fade = 1 - ease_in_out(prog(t, 5.6, 0.3))
        paste_center(dst, MILK, W / 2, 760, 0.3 + 0.7 * ease_out_back(p, 2.6), fade, math.sin(t * 4) * 6)
    p = prog(t, 2.3, 0.4)
    if p > 0:
        fade = 1 - ease_in_out(prog(t, 5.6, 0.3))
        paste_center(dst, badge("AL FONDO?", 90, YELLOW), W / 2, 1050, 0.3 + 0.7 * ease_out_back(p, 3), fade, -4 + math.sin(t * 5) * 2)
    draw_moni(dst, t, W / 2, 1390, 0.9, 1.0, "surprised", "up", enter=0.2)

def scene2(dst, t):
    a = 6.0; end = 13.0
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Es", WHITE), ("lo", WHITE), ("que", WHITE), ("MÁS", YELLOW), ("compras…", WHITE), ("y", WHITE), ("la", WHITE), ("ponen", WHITE), ("LEJOS", PINK), ("a", WHITE), ("propósito", WHITE)], W / 2, 430, 72, t, a + 0.2, stagger=0.13, max_w=980, out_t=end - 0.35)
    p = prog(t, a + 2.3, 0.45)
    if p > 0:
        layer = MAP.copy(); d = ImageDraw.Draw(layer)
        sp = prog(t, a + 2.8, 3.0)
        # recorrido en zigzag desde la entrada hasta la leche
        segs = list(zip(PATH[:-1], PATH[1:]))
        lens = [math.dist(a_, b_) for a_, b_ in segs]; tot = sum(lens); goal = sp * tot
        last = PATH[0]
        for (p0, p1), L in zip(segs, lens):
            if goal <= 0: break
            f = min(1, goal / L)
            q = (p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f)
            d.line([p0, q], fill=PINK, width=12)
            last = q; goal -= L
        d.ellipse([last[0] - 20, last[1] - 20, last[0] + 20, last[1] + 20], fill=YELLOW, outline=INK, width=5)
        paste_center(dst, layer, W / 2, 860, 0.6 + 0.4 * ease_out_back(p, 2), ease_out_cubic(p) * fade)
    draw_moni(dst, t, 175, 1420, 0.62, 1.0, "sly", "point")

ITEMS = [("CHOCOLATE", PINK, -260, 690, -8), ("PATATAS", YELLOW, 250, 760, 7), ("REFRESCOS", CYAN, -200, 880, 5), ("GALLETAS", LIME, 230, 960, -6)]
def scene3(dst, t):
    a = 13.0; end = 20.4
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("Para", WHITE), ("llegar,", WHITE), ("pasas", WHITE), ("por", WHITE), ("delante", WHITE), ("de", WHITE), ("TODO", YELLOW)], W / 2, 400, 82, t, a + 0.2, out_t=end - 0.35)
    for i, (txt, col, dx, y, r) in enumerate(ITEMS):
        p = prog(t, a + 1.6 + i * 0.5, 0.4)
        if p > 0:
            paste_center(dst, badge(txt, 54, col), W / 2 + dx, y, 0.3 + 0.7 * ease_out_back(p, 3), fade, r + math.sin(t * 3 + i) * 3)
    p = prog(t, a + 4.2, 0.4)
    if p > 0:
        pop_words(dst, [("…y", WHITE), ("acabas", WHITE), ("comprando", WHITE), ("de", WHITE), ("MÁS", RED)], W / 2, 1110, 62, t, a + 4.2, max_w=1000, out_t=end - 0.35)
    draw_moni(dst, t, W / 2, 1420, 0.66, 1.0, "surprised", "down")

def scene4(dst, t):
    a = 20.4; end = 26.6
    fade = 1 - ease_in_out(prog(t, end - 0.35, 0.3))
    pop_words(dst, [("¡Y", WHITE), ("no", WHITE), ("es", WHITE), ("el", WHITE), ("único", WHITE), ("truco!", YELLOW)], W / 2, 380, 84, t, a + 0.2, out_t=end - 0.35)
    for i, (l1, l2, col, y, r) in enumerate([("Caprichos", "EN LA CAJA", PINK, 640, -4), ("Lo más caro", "A LA ALTURA DE TUS OJOS", CYAN, 940, 3)]):
        p = prog(t, a + 1.2 + i * 1.6, 0.45)
        if p > 0:
            card = sticker_card(900, 230, WHITE).copy()
            t1 = text_img(l1, 64, INK, F_BLACK, stroke=0, shadow=False)
            card.alpha_composite(t1, ((900 - t1.width) // 2, 28))
            t2 = text_img(l2, 60 if len(l2) < 14 else 48, col, F_BLACK)
            card.alpha_composite(t2, ((900 - t2.width) // 2, 110))
            paste_center(dst, card, W / 2, y, 0.4 + 0.6 * ease_out_back(p, 2.4), ease_out_cubic(p) * fade, r)
    draw_moni(dst, t, W - 190, 1400, 0.62, 1.0, "sly", "point")

def scene5(dst, t):
    scene_truco(dst, t, 26.6, 33.8,
                [("Haz", INK), ("LISTA", PINK), ("y", INK), ("ve", INK), ("DIRECTO", PINK), ("a", INK), ("lo", INK), ("que", INK), ("necesitas", INK)],
                [("…y", WHITE), ("nunca", WHITE), ("vayas", WHITE), ("con", WHITE), ("HAMBRE", YELLOW)])

def scene6(dst, t): scene_outro(dst, t, 33.8)

SCENES = [(0, 6.0, scene1), (6.0, 13.0, scene2), (13.0, 20.4, scene3), (20.4, 26.6, scene4), (26.6, 33.8, scene5), (33.8, 40.0, scene6)]

if __name__ == "__main__":
    main(SCENES, DUR)
