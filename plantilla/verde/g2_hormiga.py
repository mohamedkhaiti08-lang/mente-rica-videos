import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verde import *

CUP = glow(icon("cup", 300), EMERALD, 24, 0.5)

def s1(dst, t):
    pop(dst, pill("  TUS GASTOS  ", 34, MINT, MINT, F_B, outline=True), W / 2, 420, t, 0.0, 0.5, 20)
    words_in(dst, [("Este", WHITE), ("café", MINT), ("te", WHITE), ("cuesta", WHITE)], W / 2, 560, 96, t, 0.15, path=F_BLACK)
    pop(dst, CUP, W / 2, 830, t, 0.5, 0.7)
    p = prog(t, 0.9, 1.4)
    if p > 0:
        val = int(round(ease_out_cubic(p) * 730))
        num = text_img(f"{val} €", 230, LIME, F_BLACK)
        paste_center(dst, num, W / 2, 1150 + (1 - ease_out_quint(prog(t, 0.9, 0.6))) * 50, 1.0, ease_out_cubic(prog(t, 0.9, 0.4)))
    words_in(dst, [("al", MUTED), ("año.", WHITE)], W / 2, 1340, 64, t, 1.8, path=F_SB)

def s2(dst, t):
    words_in(dst, [("Haz", WHITE), ("la", WHITE), ("cuenta", MINT)], W / 2, 480, 96, t, 0.1, path=F_BLACK)
    p = prog(t, 0.4, 0.6)
    if p > 0:
        card = glass(880, 720).copy(); d = ImageDraw.Draw(card)
        rows = [("2 €", "al día", WHITE, 0.6), ("× 365", "días", WHITE, 1.1)]
        for i, (a, b, col, st) in enumerate(rows):
            q = prog(t, st, 0.5)
            if q > 0:
                A = text_img(a, 120, col, F_BLACK, shadow=False); B = text_img(b, 54, MUTED, F_M, shadow=False)
                y = 50 + i * 190 + (1 - ease_out_quint(q)) * 30
                A2 = A.copy(); A2.putalpha(A.split()[3].point(lambda v: int(v * ease_out_cubic(q))))
                B2 = B.copy(); B2.putalpha(B.split()[3].point(lambda v: int(v * ease_out_cubic(q))))
                card.alpha_composite(A2, (60, int(y))); card.alpha_composite(B2, (880 - B.width - 60, int(y) + 42))
        q = prog(t, 1.6, 0.5)
        if q > 0:
            d.line([(60, 440), (60 + (760) * ease_out_cubic(q), 440)], fill=(255, 255, 255, 70), width=3)
        q = prog(t, 1.8, 1.2)
        if q > 0:
            val = int(round(ease_out_cubic(q) * 730))
            C = text_img(f"= {val} €", 150, LIME, F_BLACK, shadow=False)
            C2 = C.copy(); C2.putalpha(C.split()[3].point(lambda v: int(v * ease_out_cubic(q * 3))))
            card.alpha_composite(C2, ((880 - C.width) // 2, 480))
        paste_center(dst, card, W / 2, 1040 + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

ITEMS = [("Bebida", 2.0), ("Snack", 1.5), ("App", 0.99), ("Envío", 3.0)]
def s3(dst, t):
    words_in(dst, [("Son", WHITE), ("los", WHITE), ("gastos", MINT), ("hormiga", MINT)], W / 2, 440, 96, t, 0.1, path=F_BLACK)
    words_in(dst, [("Pequeños,", MUTED), ("casi", MUTED), ("invisibles…", MUTED)], W / 2, 650, 56, t, 0.5, path=F_SB)
    p = prog(t, 0.6, 0.6)
    if p > 0:
        card = glass(880, 640).copy(); d = ImageDraw.Draw(card)
        tot = 0
        for i, (name, val) in enumerate(ITEMS):
            q = prog(t, 0.9 + i * 0.3, 0.45)
            if q <= 0: continue
            y = 50 + i * 115
            a = ease_out_cubic(q)
            N = text_img(name, 50, WHITE, F_B, shadow=False); V = text_img(f"{val:.2f} €".replace(".", ","), 50, MINT, F_XB, shadow=False)
            for im_, x in ((N, 50), (V, 880 - V.width - 50)):
                im2 = im_.copy(); im2.putalpha(im_.split()[3].point(lambda v: int(v * a))); card.alpha_composite(im2, (x, int(y + (1 - a) * 20)))
            tot += val * a
        q = prog(t, 2.2, 0.6)
        if q > 0:
            d.line([(50, 520), (830, 520)], fill=(255, 255, 255, 60), width=3)
            L = text_img("Al mes, si es diario:", 44, MUTED, F_M, shadow=False)
            V = text_img(f"{7.49 * 30:.0f} €", 64, CORAL, F_BLACK, shadow=False)
            for im_, x, yy in ((L, 50, 540), (V, 880 - V.width - 50, 528)):
                im2 = im_.copy(); im2.putalpha(im_.split()[3].point(lambda v: int(v * ease_out_cubic(q)))); card.alpha_composite(im2, (x, yy))
        paste_center(dst, card, W / 2, 1100 + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

TILES = [("plane", "Un viaje"), ("phone", "Un móvil nuevo"), ("wallet", "Empezar a ahorrar")]
def s4(dst, t):
    words_in(dst, [("Con", WHITE), ("730 €", LIME), ("al", WHITE), ("año", WHITE), ("podrías…", WHITE)], W / 2, 520, 88, t, 0.1, path=F_BLACK, max_w=920)
    for i, (ic, txt) in enumerate(TILES):
        c = glass(880, 210).copy()
        c.alpha_composite(icon(ic, 130), (50, 40))
        tx = text_img(txt, 58, WHITE, F_XB, shadow=False)
        c.alpha_composite(tx, (220, 105 - tx.height // 2))
        pop(dst, c, W / 2, 790 + i * 245, t, 0.6 + i * 0.35, 0.6)

def s5(dst, t):
    tip_chip(dst, t, 500)
    words_in(dst, [("Apunta", WHITE), ("cada", WHITE), ("gasto", MINT), ("durante", WHITE), ("7", LIME), ("días", LIME)], W / 2, 680, 88, t, 0.3, path=F_BLACK, max_w=900)
    p = prog(t, 0.9, 0.6)
    if p > 0:
        card = glass(900, 300).copy(); d = ImageDraw.Draw(card)
        days = ["L", "M", "X", "J", "V", "S", "D"]
        for i, dy in enumerate(days):
            x = 50 + i * 118
            q = prog(t, 1.3 + i * 0.18, 0.3)
            fill = MINT if q > 0.5 else (255, 255, 255, 16)
            d.rounded_rectangle([x, 70, x + 96, 166], 22, fill=fill, outline=MINT, width=3)
            lab = text_img(dy, 40, DEEP if q > 0.5 else MUTED, F_XB, shadow=False)
            card.alpha_composite(lab, (x + 48 - lab.width // 2, 118 - lab.height // 2))
        tx = text_img("Los números no mienten.", 44, MUTED, F_SB, shadow=False)
        card.alpha_composite(tx, ((900 - tx.width) // 2, 196))
        paste_center(dst, card, W / 2, 1000 + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

SCENES = [s1, s2, s3, s4, s5, outro]
if __name__ == "__main__":
    main(SCENES, os.environ.get("OUT", "out_g2"))
