#!/usr/bin/env python3
"""Newspaper front page poster - 1024x1024 PNG, stdlib only, deterministic.
Written from scratch: own PNG encoder, own 5x7 bitmap font, own icons.
"""
import sys, os, struct, zlib, math

W = 1024
H = 1024

CREAM = (246, 240, 219)
PAPER = (252, 249, 238)
INK = (28, 26, 22)
RED = (178, 32, 28)
ORANGE = (204, 102, 18)
BLUE = (36, 78, 158)
GOLD = (150, 112, 14)
WHITE = (255, 255, 255)
GREY = (110, 105, 95)
LIGHT = (226, 218, 196)

FB = bytearray(W * H * 3)
for i in range(W * H):
    FB[i*3] = CREAM[0]; FB[i*3+1] = CREAM[1]; FB[i*3+2] = CREAM[2]

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        j = (y * W + x) * 3
        FB[j] = c[0]; FB[j+1] = c[1]; FB[j+2] = c[2]

def fill_rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, c)

def border_rect(x, y, w, h, c, t=2):
    fill_rect(x, y, w, t, c); fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c); fill_rect(x + w - t, y, t, h, c)

def hline(x, y, w, c, t=2):
    fill_rect(x, y, w, t, c)

def line(x0, y0, x1, y1, c, t=2):
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
    err = dx + dy; x, y = x0, y0
    while True:
        fill_rect(x - t//2, y - t//2, t, t, c)
        if x == x1 and y == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x += sx
        if e2 <= dx: err += dx; y += sy

def circle(cx, cy, r, c, t=2):
    for deg in range(360):
        rad = math.radians(deg)
        x = int(cx + r * math.cos(rad)); y = int(cy + r * math.sin(rad))
        fill_rect(x - t//2, y - t//2, t, t, c)

def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx)**2 + (yy - cy)**2 <= r * r:
                px(xx, yy, c)

def write_png(path):
    raw = bytearray()
    row = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(FB[y*row:(y+1)*row])
    comp = zlib.compress(bytes(raw), 9)
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        return out
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)

# ---- 5x7 bitmap typeface, drawn by hand (rows top to bottom, # = ink) ----
FONT = {
'A':(".###.","#...#","#...#","#####","#...#","#...#","#...#"),
'B':("####.","#...#","#...#","####.","#...#","#...#","####."),
'C':(".####","#....","#....","#....","#....","#....",".####"),
'D':("####.","#...#","#...#","#...#","#...#","#...#","####."),
'E':("#####","#....","#....","####.","#....","#....","#####"),
'F':("#####","#....","#....","####.","#....","#....","#...."),
'G':(".####","#....","#....","#.###","#...#","#...#",".###."),
'H':("#...#","#...#","#...#","#####","#...#","#...#","#...#"),
'I':("#####","..#..","..#..","..#..","..#..","..#..","#####"),
'J':("..###","....#","....#","....#","....#","#...#",".###."),
'K':("#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"),
'L':("#....","#....","#....","#....","#....","#....","#####"),
'M':("#...#","##.##","#.#.#","#.#.#","#...#","#...#","#...#"),
'N':("#...#","##..#","#.#.#","#..##","#...#","#...#","#...#"),
'O':(".###.","#...#","#...#","#...#","#...#","#...#",".###."),
'P':("####.","#...#","#...#","####.","#....","#....","#...."),
'Q':(".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"),
'R':("####.","#...#","#...#","####.","#.#..","#..#.","#...#"),
'S':(".####","#....","#....",".###.","....#","....#","####."),
'T':("#####","..#..","..#..","..#..","..#..","..#..","..#.."),
'U':("#...#","#...#","#...#","#...#","#...#","#...#",".###."),
'V':("#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."),
'W':("#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"),
'X':("#...#",".#.#.","..#..","..#..","..#..",".#.#.","#...#"),
'Y':("#...#","#...#",".#.#.","..#..","..#..","..#..","..#.."),
'Z':("#####","....#","...#.","..#..",".#...","#....","#####"),
'0':(".###.","#..##","#.#.#","##..#","#...#","#...#",".###."),
'1':("..#..",".##..","..#..","..#..","..#..","..#..",".###."),
'2':(".###.","#...#","....#","..##.",".#...","#....","#####"),
'3':("####.","....#","....#",".###.","....#","....#","####."),
'4':("...#.","..##.",".#.#.","#..#.","#####","...#.","...#."),
'5':("#####","#....","####.","....#","....#","#...#",".###."),
'6':(".###.","#....","#....","####.","#...#","#...#",".###."),
'7':("#####","....#","...#.","..#..",".#...",".#...",".#..."),
'8':(".###.","#...#","#...#",".###.","#...#","#...#",".###."),
'9':(".###.","#...#","#...#",".####","....#","....#",".###."),
' ':(".....",".....",".....",".....",".....",".....","....."),
'-':(".....",".....",".....","#####",".....",".....","....."),
'+':(".....","..#..","..#..","#####","..#..","..#..","....."),
':':(".....","..#..","..#..",".....","..#..","..#..","....."),
'.':(".....",".....",".....",".....",".....",".##..",".##.."),
',':(".....",".....",".....",".....",".##..",".##..",".#..."),
'$':("..#..",".####","#.#..",".###.","..#.#","####.","..#.."),
"'":("..#..","..#..",".#...",".....",".....",".....","....."),
'/':("....#","...#.","...#.","..#..",".#...",".#...","#...."),
'(' :(".#...","#....","#....","#....","#....","#....",".#..."),
')' :("...#.","....#","....#","....#","....#","....#","...#."),
}

def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0

def draw_text(x, y, s, scale, c):
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT[' '])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == '#':
                    fill_rect(cx + col*scale, y + r*scale, scale, scale, c)
        cx += 6 * scale
    return cx

def draw_centered(y, s, scale, c):
    x = (W - text_w(s, scale)) // 2
    draw_text(x, y, s, scale, c)

def draw_chip(x, y, s, scale, bg, fg=WHITE):
    w = text_w(s, scale) + 16
    h = 7 * scale + 10
    fill_rect(x, y, w, h, bg)
    draw_text(x + 8, y + 5, s, scale, fg)
    return w, h

# ---- hand-drawn icons ----
def icon_globe(x, y):
    circle(x+28, y+28, 26, INK, 3)
    # meridians / parallels
    for deg in (0,):
        hline(x+4, y+28, 48, INK, 2)
    # vertical ellipse hints
    for dx in (-13, 0, 13):
        for yy in range(y+6, y+51):
            import math as _m
            off = int(13 * _m.sin((yy-(y+28))/26*1.57)) if False else dx
            px(x+28+dx, yy, INK); px(x+29+dx, yy, INK)
    hline(x+6, y+16, 44, INK, 2); hline(x+6, y+40, 44, INK, 2)

def icon_factory(x, y):
    fill_rect(x+2, y+34, 52, 20, INK)
    fill_rect(x+6, y+18, 10, 18, INK); fill_rect(x+20, y+18, 10, 18, INK)
    fill_rect(x+8, y+40, 6, 6, PAPER); fill_rect(x+22, y+40, 6, 6, PAPER); fill_rect(x+36, y+40, 6, 6, PAPER)
    # flame above roof
    disc(x+42, y+22, 7, RED); disc(x+42, y+13, 5, ORANGE); disc(x+42, y+7, 3, GOLD)
    fill_rect(x+40, y+24, 5, 8, ORANGE)

def icon_tanker(x, y):
    # hull
    for i in range(48):
        fill_rect(x+4+i, y+36, 1, 8 - abs(i-24)//8, INK)
    fill_rect(x+4, y+32, 48, 6, INK)
    fill_rect(x+10, y+24, 30, 8, INK); fill_rect(x+42, y+18, 8, 14, INK)
    fill_rect(x+14, y+27, 4, 3, PAPER); fill_rect(x+22, y+27, 4, 3, PAPER); fill_rect(x+30, y+27, 4, 3, PAPER)
    # waves
    for wx in (6, 20, 34):
        line(x+wx, y+50, x+wx+5, y+46, BLUE, 2); line(x+wx+5, y+46, x+wx+10, y+50, BLUE, 2)

def icon_block(x, y):
    fill_rect(x+12, y+4, 32, 50, INK)
    for r in range(4):
        for cc in range(3):
            fill_rect(x+17+cc*9, y+9+r*11, 5, 6, PAPER)
    fill_rect(x+24, y+44, 8, 10, PAPER)
    line(x+4, y+14, x+12, y+8, RED, 3); disc(x+4, y+16, 3, RED)

def icon_king(x, y):
    # chess king: cross, crown, body, base
    fill_rect(x+25, y+2, 6, 14, INK); fill_rect(x+20, y+6, 16, 5, INK)
    fill_rect(x+16, y+20, 24, 8, INK)
    fill_rect(x+20, y+28, 16, 12, INK)
    fill_rect(x+12, y+40, 32, 6, INK); fill_rect(x+8, y+48, 40, 6, INK)
    disc(x+28, y+24, 3, PAPER)

# ---- page layout ----
def panel(x, y, w, h, kicker, kcol, headline, hscale, body, icon):
    fill_rect(x, y, w, h, PAPER)
    border_rect(x, y, w, h, INK, 3)
    cw, chh = draw_chip(x+12, y+10, kicker, 2, kcol)
    icon(x + w - 68, y + 8)
    draw_text(x+12, y+10+chh+8, headline, hscale, INK)
    by = y + 10 + chh + 8 + 7*hscale + 10
    for ln in body:
        draw_text(x+12, by, ln, 2, INK)
        by += 20
    return by

def render():
    border_rect(10, 10, W-20, H-20, INK, 4)
    # Masthead
    draw_centered(28, "THE WORLD IN ONE DAY", 6, INK)
    hline(28, 82, W-56, INK, 3); hline(28, 88, W-56, INK, 1)
    draw_centered(96, "TUESDAY 24 NOVEMBER 2026", 3, RED)
    hline(28, 124, W-56, INK, 3)
    # Lead panel
    lx, ly, lw = 28, 136, W-56
    fill_rect(lx, ly, lw, 272, PAPER); border_rect(lx, ly, lw, 272, INK, 3)
    cw, chh = draw_chip(lx+14, ly+12, "ANTALYA, TURKIYE - THE MORNING AFTER", 2, RED)
    icon_globe(lx+lw-76, ly+8)
    draw_text(lx+14, ly+54, "COP31: THE WORLD", 5, INK)
    draw_text(lx+14, ly+96, "REACTS IN ANGER - DAY TWO", 5, INK)
    lead = [
        "A DAY OF FURY AFTER THE LONGEST SUMMIT",
        "EVER ENDS WITH NO DEAL. GUTERRES SAYS HE",
        "IS DEEPLY DISAPPOINTED. THE EU: THIS COP",
        "WAS HIJACKED BY OIL STATES. PANAMA: THE",
        "WORLD IS HELD HOSTAGE BY THE PETROLEUM",
        "MAFIA. ADOW: THE WORST COP EVER - A WAKE-UP",
        "CALL. ISLAND NATIONS REFUSED TO SIGN.",
    ]
    by = ly + 140
    for ln in lead:
        draw_text(lx+14, by, ln, 2, INK); by += 19
    # Four panels 2x2
    pw = (W - 56 - 12) // 2; ph = 208
    x1, x2 = 28, 28 + pw + 12
    y1, y2 = 420, 420 + ph + 12
    panel(x1, y1, pw, ph, "CIKANDE, BANTEN", ORANGE, "FIRE KILLS 24", 4,
          ["24 DEAD ARE CONFIRMED IN","THE CANDY FACTORY BLAZE;","30 STILL MISSING IN THE","RUINS. DNA TESTS TO NAME","THE DEAD. A SAFETY PROBE","OPENS INTO PT FONUSA."], icon_factory)
    panel(x2, y1, pw, ph, "STRAIT OF HORMUZ", RED, "OIL SLIDES", 4,
          ["BRENT FALLS TO $89.37 -","LOWEST SINCE AUGUST - AS","OIL FLOWS PAST ATTACKS.","TRUMP EYES NEW STRIKES","IRAN AFTER NEW YEAR. THE","OPEC+ MEETS ON SUNDAY."], icon_tanker)
    panel(x1, y2, pw, ph, "KYIV REGION", BLUE, "STRIKES GO ON", 4,
          ["FRESH DRONE + MISSILE","STRIKES HIT KYIV REGION.","THE BLOCK SEARCH GOES ON;","MISSING ARE FEARED DEAD.","AT SEA, THE SPARTA II","CARGO SHIP STILL BURNS."], icon_block)
    panel(x2, y2, pw, ph, "GENEVA - GAME ONE", GOLD, "TITLE MATCH", 4,
          ["THE WORLD CHESS TITLE","MATCH OPENS TODAY: THE","CHAMPION, D GUKESH OF","INDIA, FACES JAVOKHIR","SINDAROV OF UZBEKISTAN","IN GAME ONE IN GENEVA."], icon_king)
    # Bottom strip
    sy = y2 + ph + 12
    fill_rect(28, sy, W-56, 92, LIGHT); border_rect(28, sy, W-56, 92, INK, 3)
    strip = [
        "INDIA-NEPAL: MODI + SHAH FLAG OFF SARYU-KAMALA EXPRESS, AYODHYA-JANAKPUR.",
        "TENNIS: ALCARAZ BEATS ZVEREV IN TURIN TO WIN HIS FIRST ATP FINALS TITLE.",
        "CRICKET: PANT HITS 128 AS INDIA DRAW WITH NEW ZEALAND AT WELLINGTON.",
    ]
    by = sy + 12
    for ln in strip:
        draw_text(40, by, ln, 2, INK); by += 24
    # Footer
    hline(28, sy+104, W-56, INK, 2)
    draw_centered(sy+114, "ANTALYA - BANTEN - HORMUZ - KYIV - GENEVA - TURIN - WELLINGTON - JANAKPUR", 2, INK)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/output/entry.png"
    render()
    write_png(out)

if __name__ == "__main__":
    main()
