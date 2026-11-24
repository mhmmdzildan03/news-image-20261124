#!/usr/bin/env python3
"""One-day world news poster for Tuesday 24 November 2026.

Paints a 1024x1024 newspaper front page and saves it as a PNG at
/output/entry.png. Standard library only. The 5x7 typeface is kept
as seven integers per character, one integer per row, the five low
bits of each integer being that row's pixels from left to right.
All drawing happens on one flat pixel buffer, so the output bytes
never change between runs: no assets, no network, no clock.
"""

import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

SHEET = (246, 241, 227)
BLACK = (22, 27, 43)
MARINE = (18, 42, 86)
CRIMSON = (178, 34, 40)
AZURE = (33, 84, 158)
PINE = (14, 116, 110)
AMBER = (232, 119, 34)
OCHRE = (196, 148, 32)
SLATE = (96, 100, 110)
CREAM = (255, 253, 246)
ASH = (150, 148, 140)

# ------------------------------------------------------------ typeface
# Seven rows per glyph; in each row, bit 16 is the leftmost pixel.
TYPEFACE = {
    "A": (14, 17, 17, 31, 17, 17, 17), "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (15, 16, 16, 16, 16, 16, 15), "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31), "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (15, 16, 16, 23, 17, 17, 14), "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (31, 4, 4, 4, 4, 4, 31), "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17), "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17), "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14), "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13), "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30), "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14), "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17), "X": (17, 10, 4, 4, 4, 10, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4), "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 25, 21, 19, 17, 14), "1": (4, 12, 4, 4, 4, 4, 31),
    "2": (14, 17, 1, 6, 8, 16, 31), "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2), "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (14, 16, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 1, 14),
    " ": (0, 0, 0, 0, 0, 0, 0), ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 12, 8), "'": (12, 12, 8, 0, 0, 0, 0),
    "-": (0, 0, 0, 31, 0, 0, 0), ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 12, 8), "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 6, 4, 0, 4), "/": (1, 1, 2, 4, 8, 16, 16),
    "(": (2, 4, 8, 8, 8, 4, 2), ")": (8, 4, 2, 2, 2, 4, 8),
    "&": (12, 18, 20, 8, 21, 18, 13), "+": (0, 4, 4, 31, 4, 4, 0),
    "%": (25, 26, 1, 2, 4, 8, 23), '"': (10, 10, 10, 0, 0, 0, 0),
    "=": (0, 0, 31, 0, 31, 0, 0), "*": (0, 21, 14, 31, 14, 21, 0),
    "$": (4, 15, 20, 14, 5, 15, 4),
}


def glyph_rows(ch):
    if ch in TYPEFACE:
        return TYPEFACE[ch]
    if ch in "•·":
        return (0, 0, 14, 14, 14, 0, 0)
    if ch == "—":
        return TYPEFACE["-"]
    return TYPEFACE["?"]


# --------------------------------------------------------------- poster
class Poster:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.pix = bytearray(bg * (w * h))

    def put(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.pix[i:i + 3] = bytes(colour)

    def box(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(colour) * max(0, x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.pix[i:i + len(row)] = row

    def border(self, x, y, w, h, colour, t=3):
        self.box(x, y, w, t, colour)
        self.box(x, y + h - t, w, t, colour)
        self.box(x, y, t, h, colour)
        self.box(x + w - t, y, t, h, colour)

    def stroke(self, x0, y0, x1, y1, colour, t=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, t // 2)
        for s in range(steps + 1):
            cx = x0 + (x1 - x0) * s // steps
            cy = y0 + (y1 - y0) * s // steps
            self.box(cx - r, cy - r, t, t, colour)

    def dot(self, cx, cy, rad, colour):
        for yy in range(cy - rad, cy + rad + 1):
            span = int((rad * rad - (yy - cy) ** 2) ** 0.5)
            self.box(cx - span, yy, span * 2 + 1, 1, colour)

    def circle(self, cx, cy, rad, colour, t=4):
        for yy in range(cy - rad - t, cy + rad + t + 1):
            for xx in range(cx - rad - t, cx + rad + t + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if rad - t <= d <= rad:
                    self.put(xx, yy, colour)

    def shape(self, points, colour):
        ys = [p[1] for p in points]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.box(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, colour)

    # -------------------------------------------------------------- text
    def measure(self, s, scale):
        return len(s) * 6 * scale - scale

    def type(self, x, y, s, scale, colour, bold=False):
        cx = x
        for ch in s.upper():
            rows = glyph_rows(ch)
            for ry, bits in enumerate(rows):
                for rx in range(5):
                    if bits & (16 >> rx):
                        self.box(cx + rx * scale, y + ry * scale,
                                 scale, scale, colour)
                        if bold:
                            self.box(cx + rx * scale + scale // 2,
                                     y + ry * scale, scale, scale, colour)
            cx += 6 * scale
        return cx - scale

    def type_mid(self, cx, y, s, scale, colour, bold=False):
        return self.type(cx - self.measure(s, scale) // 2, y, s,
                         scale, colour, bold)

    def type_lines(self, x, y, lines, scale, colour, gap=6, bold=False):
        for line in lines:
            self.type(x, y, line, scale, colour, bold)
            y += 7 * scale + gap
        return y


# ---------------------------------------------------------------- marks
def draw_globe(pg, cx, cy, rad):
    # a wire globe on two smoking stacks: the climate story in one mark
    pg.circle(cx, cy, rad, MARINE, 5)
    pg.stroke(cx - rad, cy, cx + rad, cy, MARINE, 4)
    for dx in (-rad // 2, 0, rad // 2):
        w = int((rad * rad - dx * dx) ** 0.5)
        pg.stroke(cx + dx, cy - w, cx + dx, cy + w, MARINE, 3)
    base = cy + rad + 10
    pg.box(cx - rad + 6, base, 18, 26, BLACK)
    pg.box(cx + rad - 24, base, 18, 26, BLACK)
    pg.dot(cx - rad + 15, base - 10, 8, ASH)
    pg.dot(cx - rad + 25, base - 20, 10, ASH)
    pg.dot(cx + rad - 15, base - 10, 8, ASH)
    pg.dot(cx + rad - 27, base - 21, 11, ASH)
    pg.box(cx - rad - 6, base + 26, rad * 2 + 12, 6, CRIMSON)


def draw_tanker(pg, x, y):
    # compact tanker, hull and waves in a 76x54 box at x, y
    pg.shape([(x, y + 20), (x + 76, y + 20), (x + 64, y + 36),
              (x + 12, y + 36)], MARINE)
    pg.box(x + 29, y + 7, 18, 13, CRIMSON)
    pg.box(x + 4, y + 14, 20, 6, BLACK)
    pg.box(x + 54, y + 14, 18, 6, BLACK)
    for i in range(3):
        wx = x + 2 + i * 25
        pg.stroke(wx, y + 48, wx + 7, y + 43, AZURE, 4)
        pg.stroke(wx + 7, y + 43, wx + 14, y + 48, AZURE, 4)
    # intercept burst above the stern
    bx, by = x + 64, y + 2
    for dx, dy in ((0, -8), (7, -6), (9, 2), (-7, -6), (-9, 2)):
        pg.stroke(bx, by, bx + dx, by + dy, OCHRE, 4)
    pg.dot(bx, by, 4, AMBER)


def draw_block(pg, x, y):
    # five-storey block, one corner fallen to rubble, in a 92x80 box
    pg.box(x, y, 56, 80, MARINE)
    for floor in range(5):
        for win in range(2):
            pg.box(x + 9 + win * 24, y + 8 + floor * 15, 13, 9, OCHRE)
    pg.shape([(x + 56, y + 34), (x + 92, y + 80), (x + 56, y + 80)], SLATE)
    pg.shape([(x + 44, y + 68), (x + 70, y + 48), (x + 92, y + 80),
              (x + 44, y + 80)], BLACK)
    pg.stroke(x + 56, y + 2, x + 76, y + 26, CRIMSON, 5)


def draw_factory(pg, x, y):
    # factory with a sawtooth roof in a 92x80 box at x, y
    pg.box(x, y + 30, 92, 42, BLACK)
    for i in range(3):
        bx = x + i * 28
        pg.shape([(bx, y + 30), (bx + 13, y + 16), (bx + 28, y + 30)], BLACK)
    pg.box(x + 76, y + 2, 11, 30, BLACK)
    for win in range(3):
        pg.box(x + 9 + win * 28, y + 44, 17, 13, OCHRE)
    # flame over the roof
    pg.shape([(x + 30, y + 18), (x + 42, y - 8), (x + 49, y + 4),
              (x + 58, y - 4), (x + 60, y + 18)], AMBER)
    pg.shape([(x + 38, y + 18), (x + 45, y + 2), (x + 53, y + 18)], CRIMSON)
    # rescue light dots along the ground
    pg.dot(x + 12, y + 78, 5, AZURE)
    pg.dot(x + 46, y + 78, 5, CRIMSON)
    pg.dot(x + 80, y + 78, 5, AZURE)


def draw_chess(pg, x, y):
    # chess king: cross, crown ball, tapered body and base in a 92x80
    # box, with a small pawn standing beside it
    pg.box(x + 41, y, 10, 18, BLACK)
    pg.box(x + 35, y + 5, 22, 8, BLACK)
    pg.dot(x + 46, y + 27, 9, OCHRE)
    pg.shape([(x + 35, y + 35), (x + 57, y + 35), (x + 63, y + 58),
              (x + 29, y + 58)], MARINE)
    pg.box(x + 25, y + 58, 42, 7, BLACK)
    pg.dot(x + 78, y + 38, 6, CRIMSON)
    pg.shape([(x + 72, y + 46), (x + 84, y + 46), (x + 87, y + 58),
              (x + 69, y + 58)], PINE)
    pg.box(x + 68, y + 58, 20, 7, BLACK)


# --------------------------------------------------------------- layout
def chip(pg, x, y, kicker, kcolour):
    """Inverted colour chip holding the story's kicker text."""
    w = pg.measure(kicker, 3) + 24
    pg.box(x + 3, y + 3, w, 32, kcolour)
    pg.type(x + 15, y + 9, kicker, 3, SHEET, bold=True)
    return w


def story(pg, x, y, w, h, kicker, kcolour, headline, subs,
          mark=None, mark_dx=104):
    pg.border(x, y, w, h, BLACK, 3)
    chip(pg, x, y, kicker, kcolour)
    tx = x + 20
    pg.type(tx, y + 46, headline, 4, BLACK, bold=True)
    pg.type_lines(tx, y + 98, subs, 3, BLACK, gap=1)
    if mark is not None:
        mark(pg, x + w - mark_dx, y + 14)


def compose():
    pg = Poster(WIDTH, HEIGHT, SHEET)

    # masthead
    pg.box(28, 18, WIDTH - 56, 8, BLACK)
    pg.type_mid(WIDTH // 2, 36, "THE WORLD IN ONE DAY", 7, MARINE, bold=True)
    pg.type_mid(WIDTH // 2, 94, "TUESDAY 24 NOVEMBER 2026", 4, CRIMSON, bold=True)
    pg.box(28, 130, WIDTH - 56, 4, BLACK)
    pg.box(28, 138, WIDTH - 56, 2, BLACK)

    # lead story: the world reacts to the COP31 collapse
    lx, ly, lw = 28, 148, WIDTH - 56
    pg.border(lx, ly, lw, 290, BLACK, 4)
    chip(pg, lx, ly, "ANTALYA, TURKIYE - THE MORNING AFTER", CRIMSON)
    pg.type(lx + 22, ly + 48, "COP31: THE WORLD", 5, BLACK, bold=True)
    pg.type(lx + 22, ly + 90, "REACTS IN ANGER - DAY TWO", 4,
            MARINE, bold=True)
    draw_globe(pg, lx + lw - 64, ly + 82, 30)
    pg.type_lines(lx + 22, ly + 126, [
        "A DAY OF FURY AFTER THE LONGEST SUMMIT",
        "EVER ENDS WITH NO DEAL. GUTERRES SAYS HE",
        "IS DEEPLY DISAPPOINTED. THE EU: THIS COP",
        "WAS HIJACKED BY OIL STATES. PANAMA: THE",
        "WORLD IS HELD HOSTAGE BY THE PETROLEUM",
        "MAFIA. ADOW: THE WORST COP EVER - A WAKE-UP",
        "CALL. ISLAND NATIONS REFUSED TO SIGN.",
    ], 3, BLACK, gap=1)

    # middle row: Banten and Hormuz
    story(pg, 28, 446, 474, 240, "CIKANDE, BANTEN", AMBER,
          "FIRE KILLS 24",
          ["24 DEAD ARE CONFIRMED IN",
           "THE CANDY FACTORY BLAZE;",
           "30 STILL MISSING IN THE",
           "RUINS. DNA TESTS TO NAME",
           "THE DEAD. A SAFETY PROBE",
           "OPENS INTO PT FONUSA."],
          mark=draw_factory)
    story(pg, 522, 446, 474, 240, "STRAIT OF HORMUZ", CRIMSON,
          "OIL SLIDES",
          ["BRENT FALLS TO $89.37 -",
           "LOWEST SINCE AUGUST - AS",
           "OIL FLOWS PAST ATTACKS.",
           "TRUMP EYES NEW STRIKES",
           "IRAN AFTER NEW YEAR. THE",
           "OPEC+ MEETS ON SUNDAY."],
          mark=draw_tanker, mark_dx=84)

    # lower row: Kyiv and Geneva
    story(pg, 28, 694, 474, 250, "KYIV REGION", AZURE,
          "STRIKES GO ON",
          ["FRESH DRONE + MISSILE",
           "STRIKES HIT KYIV REGION.",
           "THE BLOCK SEARCH GOES ON;",
           "MISSING ARE FEARED DEAD.",
           "AT SEA, THE SPARTA II",
           "CARGO SHIP STILL BURNS."],
          mark=draw_block)
    story(pg, 522, 694, 474, 250, "GENEVA - GAME ONE", OCHRE,
          "TITLE MATCH",
          ["THE WORLD CHESS TITLE",
           "MATCH OPENS TODAY: THE",
           "CHAMPION, D GUKESH OF",
           "INDIA, FACES JAVOKHIR",
           "SINDAROV OF UZBEKISTAN",
           "IN GAME ONE IN GENEVA."],
          mark=draw_chess)

    # bottom strip: the Ayodhya-Janakpur train, tennis and cricket
    pg.box(28, 948, WIDTH - 56, 3, BLACK)
    pg.type(28, 954, "INDIA-NEPAL: MODI + SHAH FLAG OFF SARYU-KAMALA EXPRESS, AYODHYA-JANAKPUR.", 2, BLACK)
    pg.type(28, 969, "TENNIS: ALCARAZ BEATS ZVEREV IN TURIN TO WIN HIS FIRST ATP FINALS TITLE.", 2, BLACK)
    pg.type(28, 984, "CRICKET: PANT HITS 128 AS INDIA DRAW WITH NEW ZEALAND AT WELLINGTON.", 2, BLACK)

    # footer
    pg.type_mid(WIDTH // 2, 1002, "ANTALYA - BANTEN - HORMUZ - KYIV - GENEVA - TURIN - WELLINGTON - JANAKPUR", 2, MARINE, bold=True)
    return pg


def pack_png(pg):
    raw = bytearray()
    stride = pg.w * 3
    for yy in range(pg.h):
        raw.append(0)
        raw += pg.pix[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", pg.w, pg.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "ENTRY_OUT", "/output/entry.png")
    data = pack_png(compose())
    folder = os.path.dirname(out)
    if folder:
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            out = os.path.join(".", os.path.basename(out))
    with open(out, "wb") as fh:
        fh.write(data)
    print("wrote", out, len(data), "bytes")


if __name__ == "__main__":
    main()
