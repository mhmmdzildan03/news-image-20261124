#!/usr/bin/env python3
"""One-day world news poster for Tuesday 24 November 2026.

Renders a 1024x1024 newspaper front page to /output/entry.png using
only the Python standard library. Every glyph of the 5x7 typeface is
stored as seven integers, one per row, whose five low bits are the
row's pixels. The picture is painted on a plain pixel canvas, so two
runs always write the same bytes: no assets, no network, no clock.
"""

import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (246, 241, 227)
INK = (22, 27, 43)
NAVY = (18, 42, 86)
RED = (178, 34, 40)
BLUE = (33, 84, 158)
TEAL = (14, 116, 110)
ORANGE = (232, 119, 34)
GOLD = (196, 148, 32)
GREY = (96, 100, 110)
WHITE = (255, 253, 246)
SMOKE = (150, 148, 140)

# ------------------------------------------------------------- typeface
# Seven rows per glyph; in each row, bit 16 is the leftmost pixel.
FONT = {
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


def glyph(ch):
    if ch in FONT:
        return FONT[ch]
    if ch in "•·":
        return (0, 0, 14, 14, 14, 0, 0)
    if ch == "—":
        return FONT["-"]
    return FONT["?"]


# --------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(colour) * max(0, x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, colour, t=3):
        self.rect(x, y, w, t, colour)
        self.rect(x, y + h - t, w, t, colour)
        self.rect(x, y, t, h, colour)
        self.rect(x + w - t, y, t, h, colour)

    def line(self, x0, y0, x1, y1, colour, t=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, t // 2)
        for s in range(steps + 1):
            cx = x0 + (x1 - x0) * s // steps
            cy = y0 + (y1 - y0) * s // steps
            self.rect(cx - r, cy - r, t, t, colour)

    def disc(self, cx, cy, rad, colour):
        for yy in range(cy - rad, cy + rad + 1):
            span = int((rad * rad - (yy - cy) ** 2) ** 0.5)
            self.rect(cx - span, yy, span * 2 + 1, 1, colour)

    def ring(self, cx, cy, rad, colour, t=4):
        for yy in range(cy - rad - t, cy + rad + t + 1):
            for xx in range(cx - rad - t, cx + rad + t + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if rad - t <= d <= rad:
                    self.set(xx, yy, colour)

    def poly(self, points, colour):
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
                self.rect(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, colour)

    # -------------------------------------------------------------- text
    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, colour, bold=False):
        cx = x
        for ch in s.upper():
            rows = glyph(ch)
            for ry, bits in enumerate(rows):
                for rx in range(5):
                    if bits & (16 >> rx):
                        self.rect(cx + rx * scale, y + ry * scale,
                                  scale, scale, colour)
                        if bold:
                            self.rect(cx + rx * scale + scale // 2,
                                      y + ry * scale, scale, scale, colour)
            cx += 6 * scale
        return cx - scale

    def text_centred(self, cx, y, s, scale, colour, bold=False):
        return self.text(cx - self.text_width(s, scale) // 2, y, s,
                         scale, colour, bold)

    def text_block(self, x, y, lines, scale, colour, gap=6, bold=False):
        for line in lines:
            self.text(x, y, line, scale, colour, bold)
            y += 7 * scale + gap
        return y


# ---------------------------------------------------------------- icons
def icon_globe(cv, cx, cy, rad):
    # a wire globe on two smoking stacks: the climate story in one mark
    cv.ring(cx, cy, rad, NAVY, 5)
    cv.line(cx - rad, cy, cx + rad, cy, NAVY, 4)
    for dx in (-rad // 2, 0, rad // 2):
        w = int((rad * rad - dx * dx) ** 0.5)
        cv.line(cx + dx, cy - w, cx + dx, cy + w, NAVY, 3)
    base = cy + rad + 10
    cv.rect(cx - rad + 6, base, 18, 26, INK)
    cv.rect(cx + rad - 24, base, 18, 26, INK)
    cv.disc(cx - rad + 15, base - 10, 8, SMOKE)
    cv.disc(cx - rad + 25, base - 20, 10, SMOKE)
    cv.disc(cx + rad - 15, base - 10, 8, SMOKE)
    cv.disc(cx + rad - 27, base - 21, 11, SMOKE)
    cv.rect(cx - rad - 6, base + 26, rad * 2 + 12, 6, RED)


def icon_tanker(cv, x, y):
    # compact tanker, hull and waves in a 76x54 box at x, y
    cv.poly([(x, y + 20), (x + 76, y + 20), (x + 64, y + 36),
             (x + 12, y + 36)], NAVY)
    cv.rect(x + 29, y + 7, 18, 13, RED)
    cv.rect(x + 4, y + 14, 20, 6, INK)
    cv.rect(x + 54, y + 14, 18, 6, INK)
    for i in range(3):
        wx = x + 2 + i * 25
        cv.line(wx, y + 48, wx + 7, y + 43, BLUE, 4)
        cv.line(wx + 7, y + 43, wx + 14, y + 48, BLUE, 4)
    # intercept burst above the stern
    bx, by = x + 64, y + 2
    for dx, dy in ((0, -8), (7, -6), (9, 2), (-7, -6), (-9, 2)):
        cv.line(bx, by, bx + dx, by + dy, GOLD, 4)
    cv.disc(bx, by, 4, ORANGE)


def icon_block(cv, x, y):
    # five-storey block, one corner fallen to rubble, in a 92x80 box
    cv.rect(x, y, 56, 80, NAVY)
    for floor in range(5):
        for win in range(2):
            cv.rect(x + 9 + win * 24, y + 8 + floor * 15, 13, 9, GOLD)
    cv.poly([(x + 56, y + 34), (x + 92, y + 80), (x + 56, y + 80)], GREY)
    cv.poly([(x + 44, y + 68), (x + 70, y + 48), (x + 92, y + 80),
             (x + 44, y + 80)], INK)
    cv.line(x + 56, y + 2, x + 76, y + 26, RED, 5)


def icon_factory(cv, x, y):
    # factory with a sawtooth roof in a 92x80 box at x, y
    cv.rect(x, y + 30, 92, 42, INK)
    for i in range(3):
        bx = x + i * 28
        cv.poly([(bx, y + 30), (bx + 13, y + 16), (bx + 28, y + 30)], INK)
    cv.rect(x + 76, y + 2, 11, 30, INK)
    for win in range(3):
        cv.rect(x + 9 + win * 28, y + 44, 17, 13, GOLD)
    # flame over the roof
    cv.poly([(x + 30, y + 18), (x + 42, y - 8), (x + 49, y + 4),
             (x + 58, y - 4), (x + 60, y + 18)], ORANGE)
    cv.poly([(x + 38, y + 18), (x + 45, y + 2), (x + 53, y + 18)], RED)
    # rescue light dots along the ground
    cv.disc(x + 12, y + 78, 5, BLUE)
    cv.disc(x + 46, y + 78, 5, RED)
    cv.disc(x + 80, y + 78, 5, BLUE)


def icon_chess(cv, x, y):
    # chess king: cross, crown ball, tapered body and base in a 92x80
    # box, with a small pawn standing beside it
    cv.rect(x + 41, y, 10, 18, INK)
    cv.rect(x + 35, y + 5, 22, 8, INK)
    cv.disc(x + 46, y + 27, 9, GOLD)
    cv.poly([(x + 35, y + 35), (x + 57, y + 35), (x + 63, y + 58),
             (x + 29, y + 58)], NAVY)
    cv.rect(x + 25, y + 58, 42, 7, INK)
    cv.disc(x + 78, y + 38, 6, RED)
    cv.poly([(x + 72, y + 46), (x + 84, y + 46), (x + 87, y + 58),
             (x + 69, y + 58)], TEAL)
    cv.rect(x + 68, y + 58, 20, 7, INK)


# --------------------------------------------------------------- layout
def kicker_chip(cv, x, y, kicker, kcolour):
    """Inverted colour chip holding the panel's kicker text."""
    w = cv.text_width(kicker, 3) + 24
    cv.rect(x + 3, y + 3, w, 32, kcolour)
    cv.text(x + 15, y + 9, kicker, 3, PAPER, bold=True)
    return w


def panel(cv, x, y, w, h, kicker, kcolour, headline, subs,
          icon=None, icon_dx=104):
    cv.frame(x, y, w, h, INK, 3)
    kicker_chip(cv, x, y, kicker, kcolour)
    tx = x + 20
    cv.text(tx, y + 46, headline, 4, INK, bold=True)
    cv.text_block(tx, y + 98, subs, 3, INK, gap=1)
    if icon is not None:
        icon(cv, x + w - icon_dx, y + 14)


def build():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    # masthead
    cv.rect(28, 18, WIDTH - 56, 8, INK)
    cv.text_centred(WIDTH // 2, 36, "THE WORLD IN ONE DAY", 7, NAVY, bold=True)
    cv.text_centred(WIDTH // 2, 94, "TUESDAY 24 NOVEMBER 2026", 4, RED, bold=True)
    cv.rect(28, 130, WIDTH - 56, 4, INK)
    cv.rect(28, 138, WIDTH - 56, 2, INK)

    # lead story: the world reacts to the COP31 collapse
    lx, ly, lw, lh = 28, 148, WIDTH - 56, 290
    cv.frame(lx, ly, lw, lh, INK, 4)
    kicker_chip(cv, lx, ly, "ANTALYA, TURKIYE - THE MORNING AFTER", RED)
    cv.text(lx + 22, ly + 48, "COP31: THE WORLD", 5, INK, bold=True)
    cv.text(lx + 22, ly + 90, "REACTS IN ANGER - DAY TWO", 4,
            NAVY, bold=True)
    icon_globe(cv, lx + lw - 64, ly + 82, 30)
    cv.text_block(lx + 22, ly + 126, [
        "A DAY OF FURY AFTER THE LONGEST SUMMIT",
        "EVER ENDS WITH NO DEAL. GUTERRES SAYS HE",
        "IS DEEPLY DISAPPOINTED. THE EU: THIS COP",
        "WAS HIJACKED BY OIL STATES. PANAMA: THE",
        "WORLD IS HELD HOSTAGE BY THE PETROLEUM",
        "MAFIA. ADOW: THE WORST COP EVER - A WAKE-UP",
        "CALL. ISLAND NATIONS REFUSED TO SIGN.",
    ], 3, INK, gap=1)

    # middle row: Banten and Hormuz
    panel(cv, 28, 446, 474, 240, "CIKANDE, BANTEN", ORANGE,
          "FIRE KILLS 24",
          ["24 DEAD ARE CONFIRMED IN",
           "THE CANDY FACTORY BLAZE;",
           "30 STILL MISSING IN THE",
           "RUINS. DNA TESTS TO NAME",
           "THE DEAD. A SAFETY PROBE",
           "OPENS INTO PT FONUSA."],
          icon=icon_factory)
    panel(cv, 522, 446, 474, 240, "STRAIT OF HORMUZ", RED,
          "OIL SLIDES",
          ["BRENT FALLS TO $89.37 -",
           "LOWEST SINCE AUGUST - AS",
           "OIL FLOWS PAST ATTACKS.",
           "TRUMP EYES NEW STRIKES",
           "IRAN AFTER NEW YEAR. THE",
           "OPEC+ MEETS ON SUNDAY."],
          icon=icon_tanker, icon_dx=84)

    # lower row: Kyiv and Geneva
    panel(cv, 28, 694, 474, 250, "KYIV REGION", BLUE,
          "STRIKES GO ON",
          ["FRESH DRONE + MISSILE",
           "STRIKES HIT KYIV REGION.",
           "THE BLOCK SEARCH GOES ON;",
           "MISSING ARE FEARED DEAD.",
           "AT SEA, THE SPARTA II",
           "CARGO SHIP STILL BURNS."],
          icon=icon_block)
    panel(cv, 522, 694, 474, 250, "GENEVA - GAME ONE", GOLD,
          "TITLE MATCH",
          ["THE WORLD CHESS TITLE",
           "MATCH OPENS TODAY: THE",
           "CHAMPION, D GUKESH OF",
           "INDIA, FACES JAVOKHIR",
           "SINDAROV OF UZBEKISTAN",
           "IN GAME ONE IN GENEVA."],
          icon=icon_chess)

    # bottom strip: the Ayodhya-Janankpur train, tennis and cricket
    cv.rect(28, 948, WIDTH - 56, 3, INK)
    cv.text(28, 954, "INDIA-NEPAL: MODI + SHAH FLAG OFF SARYU-KAMALA EXPRESS, AYODHYA-JANAKPUR.", 2, INK)
    cv.text(28, 969, "TENNIS: ALCARAZ BEATS ZVEREV IN TURIN TO WIN HIS FIRST ATP FINALS TITLE.", 2, INK)
    cv.text(28, 984, "CRICKET: PANT HITS 128 AS INDIA DRAW WITH NEW ZEALAND AT WELLINGTON.", 2, INK)

    # footer
    cv.text_centred(WIDTH // 2, 1002, "ANTALYA - BANTEN - HORMUZ - KYIV - GENEVA - TURIN - WELLINGTON - JANAKPUR", 2, NAVY, bold=True)
    return cv


def encode_png(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "ENTRY_OUT", "/output/entry.png")
    data = encode_png(build())
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
