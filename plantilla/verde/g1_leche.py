import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verde import *

MILK = glow(icon("milk", 420), EMERALD, 26, 0.5)
CART = glow(icon("cart", 300), EMERALD, 20, 0.45)
CANDY = icon("candy", 130)
EYE = icon("eye", 130)

def s1(dst, t):
    pop(dst, pill("  SUPERMERCADOS  ", 34, MINT, MINT, F_B, outline=True), W / 2, CHIP_Y, t, 0.0, 0.5, 20)
    headline(dst, [("¿Por", WHITE), ("qué", WHITE), ("la", WHITE), ("leche", MINT), ("está", WHITE), ("al", WHITE), ("fondo?", MINT)], t, 0.15)
    p = prog(t, 0.8, 0.8)
    if p > 0:
        paste_center(dst, MILK, W / 2, VIS_Y + 60 + (1 - ease_out_quint(p)) * 80 + math.sin(t * 1.6) * 8, 0.9 + 0.1 * ease_out_back(p), ease_out_cubic(p))

def store_map(t):
    w, h = 900, 600
    im = glass(w, h).copy(); d = ImageDraw.Draw(im)
    for i in range(4):
        y = 130 + i * 105
        d.rounded_rectangle([70, y, 620, y + 44], 12, fill=(255, 255, 255, 22))
    d.rounded_rectangle([690, 50, 840, 540], 22, fill=MINT + (60,), outline=MINT, width=3)
    lab = text_img("LECHE", 40, WHITE, F_XB, shadow=False).rotate(90, expand=True)
    im.alpha_composite(lab, (765 - lab.width // 2, 295 - lab.height // 2))
    d.ellipse([52, 512, 88, 548], outline=MUTED, width=4)
    path = [(70, 530), (650, 530), (650, 415), (40, 415), (40, 310), (650, 310), (650, 205), (40, 205), (40, 90), (680, 90)]
    sp = ease_in_out(prog(t, 0.6, 2.0))
    segs = list(zip(path[:-1], path[1:])); lens = [math.dist(a, b) for a, b in segs]; goal = sp * sum(lens); last = path[0]
    for (a, b), L in zip(segs, lens):
        if goal <= 0: break
        f = min(1, goal / L); q = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, q], fill=LIME, width=8); last = q; goal -= L
    r = 14 + 4 * math.sin(t * 5)
    d.ellipse([last[0] - r, last[1] - r, last[0] + r, last[1] + r], fill=LIME)
    return im

def s2(dst, t):
    headline(dst, [("La", WHITE), ("ponen", WHITE), ("lejos", MINT), ("a", WHITE), ("propósito", WHITE)], t)
    p = prog(t, 0.4, 0.7)
    if p > 0:
        paste_center(dst, store_map(t), W / 2, VIS_Y + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

ITEMS = [("Chocolate", -260, -230), ("Snacks", 260, -230), ("Refrescos", -260, 230), ("Galletas", 260, 230)]
def s3(dst, t):
    headline(dst, [("Recorres", WHITE), ("toda", MINT), ("la", MINT), ("tienda", MINT)], t)
    pop(dst, CART, W / 2, VIS_Y, t, 0.4, 0.6)
    for i, (txt, dx, dy) in enumerate(ITEMS):
        im = pill(f"  {txt}  ", 44, (255, 255, 255), (255, 255, 255), F_SB, outline=True)
        p = prog(t, 0.8 + i * 0.2, 0.6)
        if p > 0:
            paste_center(dst, im, W / 2 + dx, VIS_Y + dy + (1 - ease_out_quint(p)) * 50 + math.sin(t * 1.5 + i) * 6, 1.0, ease_out_cubic(p))
    p = prog(t, 1.8, 0.45)
    if p > 0:
        b = pill(" +4 ", 54, CORAL, WHITE, F_BLACK)
        paste_center(dst, b, W / 2 + 125, VIS_Y - 95, 0.5 + 0.5 * ease_out_back(p, 2.5), ease_out_cubic(p))

def row(icon_im, l1, l2, w=900, h=230):
    c = glass(w, h).copy()
    c.alpha_composite(icon_im, (40, (h - icon_im.height) // 2))
    a = text_img(l1, 56, WHITE, F_XB, shadow=False)
    b = text_img(l2, 44, MINT, F_SB, shadow=False)
    c.alpha_composite(a, (200, 34)); c.alpha_composite(b, (200, 116))
    return c

R1 = row(CANDY, "Caprichos", "junto a la caja")
R2 = row(EYE, "Lo más caro", "a la altura de tus ojos")
def s4(dst, t):
    headline(dst, [("Más", WHITE), ("trucos", MINT), ("del", WHITE), ("súper", WHITE)], t)
    pop(dst, R1, W / 2, VIS_Y - 135, t, 0.5, 0.65)
    pop(dst, R2, W / 2, VIS_Y + 135, t, 0.9, 0.65)

CHECKS = ["Lleva una lista", "Ve directo a lo que necesitas", "Nunca compres con hambre"]
def s5(dst, t):
    tip_chip(dst, t)
    headline(dst, [("Compra", WHITE), ("con", WHITE), ("cabeza", MINT)], t, 0.2)
    p = prog(t, 0.4, 0.6)
    if p > 0:
        card = glass(920, 600).copy(); d = ImageDraw.Draw(card)
        for i, txt in enumerate(CHECKS):
            y = 60 + i * 180
            q = prog(t, 0.8 + i * 0.4, 0.4)
            d.rounded_rectangle([60, y, 150, y + 90], 24, fill=MINT if q > 0.5 else (255, 255, 255, 20), outline=MINT, width=4)
            if q > 0.5:
                card.alpha_composite(icon("check", 80, DEEP, 14), (65, y + 5))
            tx = text_img(txt, 50 if len(txt) < 20 else 44, WHITE, F_B, shadow=False)
            card.alpha_composite(tx, (190, y + 45 - tx.height // 2))
        paste_center(dst, card, W / 2, VIS_Y + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

SCENES = [s1, s2, s3, s4, s5, outro]
if __name__ == "__main__":
    main(SCENES, os.environ.get("OUT", "out_g1"))
