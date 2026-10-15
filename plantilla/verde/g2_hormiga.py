import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verde import *

CUP = glow(icon("cup", 280), EMERALD, 24, 0.5)

def s1(dst, t):
    pop(dst, pill("  TUS GASTOS  ", 34, MINT, MINT, F_B, outline=True), W / 2, CHIP_Y, t, 0.0, 0.5, 20)
    headline(dst, [("Este", WHITE), ("café", MINT), ("te", WHITE), ("cuesta…", WHITE)], t, 0.15)
    pop(dst, CUP, W / 2, VIS_Y - 110, t, 0.5, 0.7)
    p = prog(t, 0.9, 1.4)
    if p > 0:
        val = int(round(ease_out_cubic(p) * 730))
        num = glow(text_img(f"{val} €", 220, LIME, F_BLACK, shadow=False), (120, 200, 40), 26, 0.35)
        paste_center(dst, num, W / 2, VIS_Y + 190 + (1 - ease_out_quint(prog(t, 0.9, 0.6))) * 50, 1.0, ease_out_cubic(prog(t, 0.9, 0.4)))
    pop(dst, pill("  AL AÑO  ", 40, LIME, DEEP, F_XB), W / 2, VIS_Y + 380, t, 1.6, 0.5, 20)

def s2(dst, t):
    headline(dst, [("Haz", WHITE), ("la", WHITE), ("cuenta", MINT)], t)
    p = prog(t, 0.3, 0.6)
    if p > 0:
        card = glass(880, 660).copy(); d = ImageDraw.Draw(card)
        rows = [("2 €", "al día", 0.5), ("× 365", "días", 0.9)]
        for i, (a, b, st) in enumerate(rows):
            q = prog(t, st, 0.5)
            if q > 0:
                A = text_img(a, 120, WHITE, F_BLACK, shadow=False); B = text_img(b, 54, MUTED, F_M, shadow=False)
                y = 40 + i * 180 + (1 - ease_out_quint(q)) * 30
                for im_, x, yy in ((A, 60, y), (B, 880 - B.width - 60, y + 42)):
                    im2 = im_.copy(); im2.putalpha(im_.split()[3].point(lambda v: int(v * ease_out_cubic(q)))); card.alpha_composite(im2, (x, int(yy)))
        q = prog(t, 1.3, 0.5)
        if q > 0:
            d.line([(60, 410), (60 + 760 * ease_out_cubic(q), 410)], fill=(255, 255, 255, 70), width=3)
        q = prog(t, 1.5, 1.2)
        if q > 0:
            val = int(round(ease_out_cubic(q) * 730))
            C = text_img(f"{val} €", 150, LIME, F_BLACK, shadow=False)
            C2 = C.copy(); C2.putalpha(C.split()[3].point(lambda v: int(v * ease_out_cubic(q * 3))))
            card.alpha_composite(C2, ((880 - C.width) // 2, 440))
        paste_center(dst, card, W / 2, VIS_Y + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

ITEMS = [("Bebida", 2.0), ("Snack", 1.5), ("App", 0.99), ("Envío", 3.0)]
def s3(dst, t):
    headline(dst, [("Gastos", WHITE), ("hormiga", MINT)], t)
    p = prog(t, 0.3, 0.6)
    if p > 0:
        card = glass(880, 640).copy(); d = ImageDraw.Draw(card)
        for i, (name, val) in enumerate(ITEMS):
            q = prog(t, 0.6 + i * 0.25, 0.45)
            if q <= 0: continue
            y = 45 + i * 112; a = ease_out_cubic(q)
            N = text_img(name, 50, WHITE, F_B, shadow=False); V = text_img(f"{val:.2f} €".replace(".", ","), 50, MINT, F_XB, shadow=False)
            for im_, x in ((N, 50), (V, 880 - V.width - 50)):
                im2 = im_.copy(); im2.putalpha(im_.split()[3].point(lambda v: int(v * a))); card.alpha_composite(im2, (x, int(y + (1 - a) * 20)))
        q = prog(t, 1.8, 0.6)
        if q > 0:
            d.line([(50, 515), (830, 515)], fill=(255, 255, 255, 60), width=3)
            L = text_img("Al mes", 46, MUTED, F_M, shadow=False)
            V = text_img("225 €", 70, CORAL, F_BLACK, shadow=False)
            for im_, x, yy in ((L, 50, 538), (V, 880 - V.width - 50, 522)):
                im2 = im_.copy(); im2.putalpha(im_.split()[3].point(lambda v: int(v * ease_out_cubic(q)))); card.alpha_composite(im2, (x, yy))
        paste_center(dst, card, W / 2, VIS_Y + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

TILES = [("plane", "Un viaje"), ("phone", "Un móvil nuevo"), ("wallet", "Tus ahorros")]
def s4(dst, t):
    headline(dst, [("Con", WHITE), ("730 €", LIME), ("podrías…", WHITE)], t)
    for i, (ic, txt) in enumerate(TILES):
        c = glass(880, 200).copy()
        c.alpha_composite(icon(ic, 120), (50, 40))
        tx = text_img(txt, 58, WHITE, F_XB, shadow=False)
        c.alpha_composite(tx, (210, 100 - tx.height // 2))
        pop(dst, c, W / 2, VIS_Y - 160 + i * 225, t, 0.5 + i * 0.3, 0.6)

def s5(dst, t):
    tip_chip(dst, t)
    headline(dst, [("Apunta", WHITE), ("cada", WHITE), ("gasto", MINT)], t, 0.2)
    p = prog(t, 0.6, 0.6)
    if p > 0:
        card = glass(900, 300).copy(); d = ImageDraw.Draw(card)
        T = text_img("7 días", 60, LIME, F_BLACK, shadow=False); card.alpha_composite(T, ((900 - T.width) // 2, 10))
        days = ["L", "M", "X", "J", "V", "S", "D"]
        for i, dy in enumerate(days):
            x = 50 + i * 118
            q = prog(t, 1.0 + i * 0.16, 0.3)
            fill = MINT if q > 0.5 else (255, 255, 255, 16)
            d.rounded_rectangle([x, 150, x + 96, 246], 22, fill=fill, outline=MINT, width=3)
            lab = text_img(dy, 40, DEEP if q > 0.5 else MUTED, F_XB, shadow=False)
            card.alpha_composite(lab, (x + 48 - lab.width // 2, 198 - lab.height // 2))
        paste_center(dst, card, W / 2, VIS_Y + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

SCENES = [s1, s2, s3, s4, s5, outro]
if __name__ == "__main__":
    main(SCENES, os.environ.get("OUT", "out_g2"))
