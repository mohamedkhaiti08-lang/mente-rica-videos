import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verde import *

MILK = glow(icon("milk", 380), EMERALD, 24, 0.5)
CART = icon("cart", 150)
CANDY = icon("candy", 130)
EYE = icon("eye", 130)
LISTI = icon("list", 120)

def s1(dst, t):
    pop(dst, pill("  SUPERMERCADOS  ", 34, MINT, MINT, F_B, outline=True), W / 2, 420, t, 0.0, 0.5, 20)
    words_in(dst, [("¿Por", WHITE), ("qué", WHITE), ("la", WHITE), ("leche", MINT), ("siempre", WHITE), ("está", WHITE), ("al", WHITE), ("fondo?", MINT)], W / 2, 640, 100, t, 0.15, path=F_BLACK, max_w=990)
    p = prog(t, 0.8, 0.8)
    if p > 0:
        paste_center(dst, MILK, W / 2, 1110 + (1 - ease_out_quint(p)) * 80 + math.sin(t * 1.6) * 8, 0.9 + 0.1 * ease_out_back(p), ease_out_cubic(p))
    words_in(dst, [("No", MUTED), ("es", MUTED), ("casualidad.", WHITE)], W / 2, 1420, 60, t, 1.5, path=F_SB)

def store_map(t):
    w, h = 900, 600
    im = glass(w, h).copy(); d = ImageDraw.Draw(im)
    for i in range(4):
        y = 130 + i * 105
        d.rounded_rectangle([70, y, 620, y + 44], 12, fill=(255, 255, 255, 22))
    d.rounded_rectangle([690, 50, 840, 540], 22, fill=MINT + (60,), outline=MINT, width=3)
    lab = text_img("LECHE", 40, WHITE, F_XB, shadow=False).rotate(90, expand=True)
    im.alpha_composite(lab, (765 - lab.width // 2, 295 - lab.height // 2))
    ent = text_img("ENTRADA", 30, MUTED, F_SB, shadow=False)
    im.alpha_composite(ent, (40, h - 76))
    path = [(70, 530), (650, 530), (650, 415), (40, 415), (40, 310), (650, 310), (650, 205), (40, 205), (40, 90), (680, 90)]
    sp = ease_in_out(prog(t, 0.9, 2.2))
    segs = list(zip(path[:-1], path[1:])); lens = [math.dist(a, b) for a, b in segs]; goal = sp * sum(lens); last = path[0]
    for (a, b), L in zip(segs, lens):
        if goal <= 0: break
        f = min(1, goal / L); q = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, q], fill=LIME, width=8); last = q; goal -= L
    r = 14 + 4 * math.sin(t * 5)
    d.ellipse([last[0] - r, last[1] - r, last[0] + r, last[1] + r], fill=LIME)
    return im

def s2(dst, t):
    words_in(dst, [("Es", WHITE), ("de", WHITE), ("lo", WHITE), ("que", WHITE), ("más", MINT), ("se", WHITE), ("compra…", WHITE)], W / 2, 480, 84, t, 0.1, path=F_BLACK)
    words_in(dst, [("y", MUTED), ("la", MUTED), ("colocan", MUTED), ("lejos", WHITE), ("a", MUTED), ("propósito.", MUTED)], W / 2, 640, 60, t, 0.6, path=F_SB)
    p = prog(t, 0.6, 0.7)
    if p > 0:
        paste_center(dst, store_map(t), W / 2, 1090 + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

ITEMS = [("Chocolate", -230, 860), ("Snacks", 240, 950), ("Refrescos", -200, 1050), ("Galletas", 230, 1140)]
def s3(dst, t):
    words_in(dst, [("Para", WHITE), ("llegar,", WHITE), ("recorres", WHITE), ("toda", MINT), ("la", MINT), ("tienda", MINT)], W / 2, 500, 84, t, 0.1, path=F_BLACK)
    pop(dst, glow(CART, EMERALD, 16, 0.4), W / 2, 700, t, 0.5, 0.6)
    for i, (txt, dx, y) in enumerate(ITEMS):
        im = pill(f"  {txt}  ", 44, (255, 255, 255), (255, 255, 255), F_SB, outline=True)
        p = prog(t, 0.9 + i * 0.22, 0.6)
        if p > 0:
            paste_center(dst, im, W / 2 + dx, y + (1 - ease_out_quint(p)) * 50 + math.sin(t * 1.5 + i) * 6, 1.0, ease_out_cubic(p))
    p = prog(t, 2.0, 0.6)
    if p > 0:
        card = glass(820, 200).copy()
        a = text_img("…y acabas comprando", 50, WHITE, F_SB, shadow=False)
        b = text_img("de más", 64, CORAL, F_BLACK, shadow=False)
        card.alpha_composite(a, ((820 - a.width) // 2, 22)); card.alpha_composite(b, ((820 - b.width) // 2, 92))
        paste_center(dst, card, W / 2, 1360 + (1 - ease_out_quint(p)) * 50, 1.0, ease_out_cubic(p))

def row(icon_im, l1, l2, w=900, h=230):
    c = glass(w, h).copy()
    c.alpha_composite(icon_im, (40, (h - icon_im.height) // 2))
    a = text_img(l1, 54, WHITE, F_XB, shadow=False)
    b = text_img(l2, 42, MUTED, F_M, shadow=False)
    c.alpha_composite(a, (200, 36)); c.alpha_composite(b, (200, 118))
    return c

R1 = row(CANDY, "Caprichos", "junto a la caja")
R2 = row(EYE, "Lo más caro", "a la altura de tus ojos")
def s4(dst, t):
    words_in(dst, [("No", WHITE), ("es", WHITE), ("la", WHITE), ("única", WHITE), ("estrategia", MINT)], W / 2, 560, 88, t, 0.1, path=F_BLACK, max_w=820)
    pop(dst, R1, W / 2, 920, t, 0.7, 0.65)
    pop(dst, R2, W / 2, 1190, t, 1.2, 0.65)

CHECKS = ["Lleva una lista", "Ve directo a lo que necesitas", "Nunca compres con hambre"]
def s5(dst, t):
    tip_chip(dst, t, 560)
    p = prog(t, 0.3, 0.6)
    if p > 0:
        card = glass(920, 640).copy(); d = ImageDraw.Draw(card)
        for i, txt in enumerate(CHECKS):
            y = 70 + i * 190
            q = prog(t, 0.8 + i * 0.45, 0.45)
            d.rounded_rectangle([60, y, 150, y + 90], 24, fill=MINT if q > 0.5 else (255, 255, 255, 20), outline=MINT, width=4)
            if q > 0.5:
                ck = icon("check", 80, DEEP, 14); card.alpha_composite(ck, (65, y + 5))
            tx = text_img(txt, 50 if len(txt) < 20 else 44, WHITE, F_B, shadow=False)
            card.alpha_composite(tx, (190, y + 45 - tx.height // 2))
        paste_center(dst, card, W / 2, 1000 + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

SCENES = [s1, s2, s3, s4, s5, outro]
if __name__ == "__main__":
    main(SCENES, sys.argv[0].replace(".py", "_out") if False else os.environ.get("OUT", "out_g1"))
