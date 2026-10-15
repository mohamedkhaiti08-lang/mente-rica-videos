import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verde import *

PHONE = glow(icon("phone", 340), EMERALD, 24, 0.5)
CASH = icon("cash", 200, LIME, 10)
WALLET = icon("wallet", 220)

def s1(dst, t):
    pop(dst, pill("  PSICOLOGÍA DEL DINERO  ", 34, MINT, MINT, F_B, outline=True), W / 2, 420, t, 0.0, 0.5, 20)
    words_in(dst, [("¿Pagar", WHITE), ("con", WHITE), ("el", WHITE), ("móvil", MINT), ("te", WHITE), ("hace", WHITE), ("gastar", WHITE), ("más?", MINT)], W / 2, 620, 92, t, 0.15, path=F_BLACK, max_w=960)
    pop(dst, PHONE, W / 2, 1040 + math.sin(t * 1.6) * 8, t, 0.7, 0.7)
    p = prog(t, 1.6, 0.5)
    if p > 0:
        paste_center(dst, glow_text("Sí.", 150, LIME, F_BLACK, EMERALD), W / 2, 1360 + (1 - ease_out_quint(p)) * 40, 0.9 + 0.1 * ease_out_back(p, 2), ease_out_cubic(p))

def s2(dst, t):
    words_in(dst, [("Con", WHITE), ("efectivo,", LIME), ("ves", WHITE), ("cómo", WHITE), ("sale", WHITE), ("tu", WHITE), ("dinero", WHITE)], W / 2, 520, 88, t, 0.1, path=F_BLACK, max_w=920)
    pop(dst, WALLET, W / 2 - 230, 1000, t, 0.5, 0.6)
    for i in range(3):
        st = 1.0 + i * 0.6
        if t < st: continue
        k = int((t - st) // 1.8)
        p = prog(t, st + k * 1.8, 1.6)
        if 0 < p < 1:
            x = W / 2 - 200 + ease_in_out(p) * 470
            y = 1000 - math.sin(p * math.pi) * 200 + (i - 1) * 40
            a = min(1, p * 5) * (1 - prog(p, 0.75, 0.25))
            paste_center(dst, CASH, x, y, 1.0, a, -8 + p * 22)
    words_in(dst, [("Y", MUTED), ("eso", MUTED), ("se", MUTED), ("nota.", WHITE)], W / 2, 1330, 60, t, 1.4, path=F_SB)

def meter(label, sub, level, col, t, st):
    c = glass(420, 560).copy(); d = ImageDraw.Draw(c)
    a = text_img(label, 56, WHITE, F_XB, shadow=False); c.alpha_composite(a, ((420 - a.width) // 2, 40))
    b = text_img(sub, 40, col, F_B, shadow=False); c.alpha_composite(b, ((420 - b.width) // 2, 470))
    d.rounded_rectangle([170, 150, 250, 450], 40, fill=(255, 255, 255, 18))
    lv = ease_out_cubic(prog(t, st, 1.0)) * level
    if lv > 0.02:
        d.rounded_rectangle([170, 450 - 300 * lv, 250, 450], 40, fill=col)
    return c

def s3(dst, t):
    words_in(dst, [("Con", WHITE), ("el", WHITE), ("móvil,", MINT), ("ni", WHITE), ("lo", WHITE), ("notas", WHITE)], W / 2, 500, 88, t, 0.1, path=F_BLACK, max_w=1000)
    p = prog(t, 0.5, 0.6)
    if p > 0:
        paste_center(dst, meter("Efectivo", "Lo notas", 0.9, CORAL, t, 0.9), W / 2 - 230, 980 + (1 - ease_out_quint(p)) * 50, 1.0, ease_out_cubic(p))
    p = prog(t, 0.75, 0.6)
    if p > 0:
        paste_center(dst, meter("Móvil", "No lo notas", 0.18, MINT, t, 1.1), W / 2 + 230, 980 + (1 - ease_out_quint(p)) * 50, 1.0, ease_out_cubic(p))
    words_in(dst, [("…y", MUTED), ("gastas", MUTED), ("más", WHITE), ("sin", MUTED), ("darte", MUTED), ("cuenta.", MUTED)], W / 2, 1360, 56, t, 1.8, path=F_SB)

def s4(dst, t):
    words_in(dst, [("Los", MUTED), ("psicólogos", MUTED), ("lo", MUTED), ("llaman", MUTED)], W / 2, 600, 64, t, 0.1, path=F_SB)
    p = prog(t, 0.5, 0.7)
    if p > 0:
        a = glow_text("El dolor", 150, WHITE, F_BLACK, EMERALD, 26, 0.25)
        b = glow_text("de pagar", 150, MINT, F_BLACK, EMERALD, 26, 0.5)
        paste_center(dst, a, W / 2, 800 + (1 - ease_out_quint(p)) * 50, 1.0, ease_out_cubic(p))
        q = prog(t, 0.75, 0.7)
        paste_center(dst, b, W / 2, 960 + (1 - ease_out_quint(q)) * 50, 1.0, ease_out_cubic(q))
    p = prog(t, 1.6, 0.6)
    if p > 0:
        d = ImageDraw.Draw(dst)
        d.line([(W / 2 - 160 * ease_out_cubic(p), 1110), (W / 2 + 160 * ease_out_cubic(p), 1110)], fill=MINT + (180,), width=4)
    words_in(dst, [("Y", WHITE), ("las", WHITE), ("tiendas", WHITE), ("lo", WHITE), ("saben.", LIME)], W / 2, 1230, 72, t, 1.8, path=F_XB)

def s5(dst, t):
    tip_chip(dst, t, 500)
    words_in(dst, [("Fija", WHITE), ("un", WHITE), ("límite", MINT), ("semanal", MINT)], W / 2, 680, 92, t, 0.3, path=F_BLACK)
    p = prog(t, 0.9, 0.6)
    if p > 0:
        card = glass(900, 420).copy(); d = ImageDraw.Draw(card)
        L = text_img("Esta semana", 44, MUTED, F_M, shadow=False); card.alpha_composite(L, (50, 30))
        lv = ease_out_cubic(prog(t, 1.3, 1.4)) * 0.62
        V = text_img(f"{int(round(lv / 0.62 * 31))} € de 50 €", 44, WHITE, F_B, shadow=False); card.alpha_composite(V, (900 - V.width - 50, 30))
        d.rounded_rectangle([50, 120, 850, 160], 20, fill=(255, 255, 255, 20))
        if lv > 0.02: d.rounded_rectangle([50, 120, 50 + 800 * lv, 160], 20, fill=MINT)
        d.line([(50, 220), (850, 220)], fill=(255, 255, 255, 40), width=2)
        card.alpha_composite(icon("eye", 110), (40, 250))
        T1 = text_img("Revisa tu saldo", 52, WHITE, F_XB, shadow=False); T2 = text_img("cada noche", 44, MINT, F_B, shadow=False)
        card.alpha_composite(T1, (180, 250)); card.alpha_composite(T2, (180, 318))
        paste_center(dst, card, W / 2, 1050 + (1 - ease_out_quint(p)) * 60, 1.0, ease_out_cubic(p))

SCENES = [s1, s2, s3, s4, s5, outro]
if __name__ == "__main__":
    main(SCENES, os.environ.get("OUT", "out_g3"))
