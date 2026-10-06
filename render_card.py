#!/usr/bin/env python3
"""Render a Your Practice Hacks tip (JSON) into a 1080x1350 PNG card.

Usage:
    python render_card.py tips/post-20.json              # -> cards/post-20.png
    python render_card.py tips/post-20.json -o out.png
"""

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"
FONTS = {
    "regular": FONT_DIR / "Inter-Regular.otf",
    "semibold": FONT_DIR / "Inter-SemiBold.otf",
    "bold": FONT_DIR / "Inter-Bold.otf",
    "italic": FONT_DIR / "Inter-Italic.otf",
}

W, H = 1080, 1350

NAVY = "#1B1D33"
ORANGE = "#E8501A"
HEADER_DIM = "#3A3C5C"
LIGHT = "#D5D6E2"
WHITE = "#FFFFFF"
BOX = "#12132A"
DIM = "#6E7090"
RULE = "#2E3050"

BAR_W = 20
LEFT = BAR_W + 70
RIGHT = W - 70
CONTENT_W = RIGHT - LEFT

HEADER_Y = 64
HEADER_RULE_Y = 116
FOOTER_RULE_Y = H - 112
FOOTER_Y = H - 76

BOX_PAD_X = 40
BOX_PAD_Y = 34
BOX_BORDER = 8

TAGLINE = "Your Team. Your Kids. Your Practice."
SITE = "yourpracticehacks.com"

_font_cache = {}


def font(style, size):
    key = (style, int(round(size)))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS[style]), key[1])
    return _font_cache[key]


def text_width(text, fnt, tracking=0):
    if not text:
        return 0
    if not tracking:
        return fnt.getlength(text)
    return sum(fnt.getlength(c) for c in text) + tracking * (len(text) - 1)


def draw_text(draw, xy, text, fnt, fill, tracking=0):
    """Draw text with its top-left at xy, applying letter spacing."""
    x, y = xy
    if not tracking:
        draw.text((x, y), text, font=fnt, fill=fill, anchor="la")
        return
    for c in text:
        draw.text((x, y), c, font=fnt, fill=fill, anchor="la")
        x += fnt.getlength(c) + tracking


def wrap(text, fnt, width, tracking=0):
    # Keep a dash with the word before it so it never starts or fills a line.
    words = [w for w in re.sub(r"\s+([—–])", "\u00a0\\1", text).split(" ") if w]
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}" if cur else word
        if text_width(trial, fnt, tracking) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    # Avoid a single word stranded on the last line.
    if len(lines) > 1 and " " not in lines[-1]:
        prev = lines[-2].rsplit(" ", 1)
        if len(prev) == 2:
            lines[-2], lines[-1] = prev[0], f"{prev[1]} {lines[-1]}"
    return [ln.replace("\u00a0", " ") for ln in lines]


def as_list(value):
    if not value:
        return []
    if isinstance(value, str):
        return [s.strip() for s in value.split(" / ") if s.strip()]
    return list(value)


# --- Layout ---------------------------------------------------------------
#
# The middle of the card is a vertical list of items:
#   ("text", style, size, color, tracking, [paragraphs], line_gap)
#   ("gap", px)            fixed gap (scaled)
#   ("flex", min_px)       flexible gap; leftover height is shared evenly
#   ("rule",)              thin divider line
#   ("box", [items])       dark callout box with orange left border
#
# Font sizes and fixed gaps are multiplied by `scale`, which shrinks until the
# content fits between the header and footer.


def build_items(tip):
    return [
        ("flex", 28),
        ("text", "bold", 84, WHITE, 0, [tip["title"]], 0.18),
        ("gap", 22),
        ("text", "semibold", 27, ORANGE, 4, [tip["subtitle"].upper()], 0.4),
        ("flex", 30),
        ("rule",),
        ("flex", 30),
        ("text", "regular", 35, LIGHT, 0, as_list(tip.get("intro")), 0.35),
        ("gap", 16),
        ("text", "bold", 42, WHITE, 0, [tip["statement"]], 0.25),
        ("flex", 30),
        ("box", [
            ("text", "regular", 32, LIGHT, 0, [tip["q1"]], 0.35),
            ("gap", 8),
            ("text", "bold", 34, WHITE, 0, [tip["q2"]], 0.3),
            ("gap", 16),
            ("text", "italic", 29, DIM, 0, [tip["q3"]], 0.35),
        ]),
        ("flex", 30),
        ("text", "regular", 32, LIGHT, 0, [tip["t1"]], 0.35),
        ("gap", 8),
        ("text", "bold", 36, WHITE, 0, [tip["t2"]], 0.3),
        ("flex", 30),
        ("rule",),
        ("flex", 30),
        ("text", "bold", 36, ORANGE, 0, [tip["cta"]], 0.3),
        ("gap", 14),
        ("text", "regular", 31, LIGHT, 0, as_list(tip.get("ctaLines")), 0.4),
        ("gap", 14),
        ("text", "regular", 27, DIM, 0, [tip["ctaPrompt"]], 0.4),
        ("flex", 28),
    ]


# A line may shrink to this fraction of its size to avoid wrapping.
MIN_FIT = 0.86


def text_lines(item, scale, width):
    _, style, size, _, tracking, paras, line_gap = item
    fit = 1.0
    while fit > MIN_FIT and any(
            text_width(p, font(style, size * scale * fit), tracking * scale * fit) > width
            for p in paras):
        fit -= 0.02
    if fit <= MIN_FIT:
        fit = 1.0  # Too long for one line anyway; wrap at full size.
    fnt = font(style, size * scale * fit)
    tr = tracking * scale * fit
    lines = [ln for p in paras for ln in wrap(p, fnt, width, tr)]
    line_h = fnt.size * (1 + line_gap)
    return fnt, tr, lines, line_h


def text_height(item, scale, width):
    fnt, _, lines, line_h = text_lines(item, scale, width)
    if not lines:
        return 0
    # Last line takes only the font size, not the trailing line gap.
    return line_h * (len(lines) - 1) + fnt.size


def measure(items, scale, width):
    """Return (fixed_height, flex_count)."""
    fixed, flex = 0.0, 0
    for item in items:
        kind = item[0]
        if kind == "text":
            fixed += text_height(item, scale, width)
        elif kind == "gap":
            fixed += item[1] * scale
        elif kind == "flex":
            fixed += item[1] * scale
            flex += 1
        elif kind == "rule":
            fixed += 2
        elif kind == "box":
            inner_w = width - BOX_BORDER - 2 * BOX_PAD_X
            h, _ = measure(item[1], scale, inner_w)
            fixed += h + 2 * BOX_PAD_Y * scale
    return fixed, flex


def render(items, draw, x, y, width, scale, extra_per_flex):
    for item in items:
        kind = item[0]
        if kind == "text":
            fnt, tr, lines, line_h = text_lines(item, scale, width)
            color = item[3]
            for i, line in enumerate(lines):
                draw_text(draw, (x, y + i * line_h), line, fnt, color, tr)
            y += text_height(item, scale, width)
        elif kind == "gap":
            y += item[1] * scale
        elif kind == "flex":
            y += item[1] * scale + extra_per_flex
        elif kind == "rule":
            draw.rectangle([x, y, x + width, y + 1], fill=RULE)
            y += 2
        elif kind == "box":
            inner_w = width - BOX_BORDER - 2 * BOX_PAD_X
            h, _ = measure(item[1], scale, inner_w)
            box_h = h + 2 * BOX_PAD_Y * scale
            draw.rectangle([x, y, x + width, y + box_h], fill=BOX)
            draw.rectangle([x, y, x + BOX_BORDER - 1, y + box_h], fill=ORANGE)
            render(item[1], draw, x + BOX_BORDER + BOX_PAD_X,
                   y + BOX_PAD_Y * scale, inner_w, scale, 0)
            y += box_h
    return y


def draw_header(draw, tip):
    left_f = font("bold", 24)
    draw_text(draw, (LEFT, HEADER_Y), "YOUR PRACTICE HACKS", left_f, ORANGE, 4)

    day = str(tip.get("day", "Friday")).upper()
    right = f"{day} / TIP / POST {tip['post']}"
    right_f = font("semibold", 22)
    rw = text_width(right, right_f, 4)
    # Align baselines: nudge the smaller font down by the cap-height difference.
    dy = left_f.getbbox("Y")[3] - right_f.getbbox("Y")[3]
    draw_text(draw, (RIGHT - rw, HEADER_Y + dy), right, right_f, HEADER_DIM, 4)

    draw.rectangle([LEFT, HEADER_RULE_Y, RIGHT, HEADER_RULE_Y + 1], fill=RULE)


def draw_footer(draw):
    draw.rectangle([LEFT, FOOTER_RULE_Y, RIGHT, FOOTER_RULE_Y + 1], fill=RULE)

    tag_f = font("semibold", 25)
    draw_text(draw, (LEFT, FOOTER_Y), TAGLINE, tag_f, ORANGE)

    site_f = font("regular", 21)
    sw = text_width(SITE, site_f, 3)
    dy = tag_f.getbbox("Y")[3] - site_f.getbbox("Y")[3]
    draw_text(draw, (RIGHT - sw, FOOTER_Y + dy), SITE, site_f, DIM, 3)


def render_card(tip, out_path):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, BAR_W - 1, H], fill=ORANGE)
    draw_header(draw, tip)
    draw_footer(draw)

    top = HEADER_RULE_Y + 2
    available = FOOTER_RULE_Y - top
    items = build_items(tip)

    scale = 1.0
    while True:
        fixed, flex = measure(items, scale, CONTENT_W)
        if fixed <= available or scale <= 0.5:
            break
        scale -= 0.02

    extra = max(0.0, (available - fixed) / flex) if flex else 0
    render(items, draw, LEFT, top, CONTENT_W, scale, extra)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return scale


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tip", help="Path to tip JSON file")
    parser.add_argument("-o", "--out", help="Output PNG (default: cards/<tip name>.png)")
    args = parser.parse_args()

    tip_path = Path(args.tip)
    tip = json.loads(tip_path.read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else ROOT / "cards" / f"{tip_path.stem}.png"
    scale = render_card(tip, out)
    note = "" if scale >= 1.0 else f" (text scaled to {scale:.0%} to fit)"
    print(f"Wrote {out}{note}")


if __name__ == "__main__":
    main()
