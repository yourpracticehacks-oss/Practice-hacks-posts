#!/usr/bin/env python3
"""Render a Your Practice Hacks tip (JSON) into a 1080x1920 MP4 reel.

The reel walks through the tip in five short scenes (the moment, the idea,
the either/or question, the takeaway, the invitation to comment), with text
that rises in line by line. It also writes a cover image for the reel.

Usage:
    python render_reel.py tips/post-21.json     # -> reels/post-21.mp4 and reels/post-21-cover.png
    python render_reel.py tips/post-21.json -o out.mp4
"""

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from render_card import (
    DIM, HEADER_DIM, LIGHT, NAVY, ORANGE, RULE, SITE, TAGLINE, WHITE,
    as_list, draw_text, font, text_width, wrap,
)

ROOT = Path(__file__).resolve().parent

W, H = 1080, 1920
FPS = 30

BAR_W = 20
LEFT = BAR_W + 70
# Instagram and Facebook draw buttons down the right side and the caption
# along the bottom, so text stays clear of those areas.
RIGHT = W - 130
CONTENT_W = RIGHT - LEFT

HEADER_Y = 170
PROGRESS_Y = 222
CONTENT_TOP = 300
CONTENT_BOTTOM = 1400
FOOTER_Y = 1480

ENTER = 0.45       # seconds for a line to fade and rise in
STAGGER = 0.12     # delay between lines within one element
RISE = 36          # pixels a line rises while entering
EXIT = 0.3         # seconds for a scene to fade out
READ_WPS = 4.0     # skim-reading speed used to time each scene (words/second)


# --- Scenes -----------------------------------------------------------------
#
# A scene is a label plus a list of elements. Each element is a dict:
#   text, style, size, color, at (seconds after the scene starts), gap (px above)


def el(text, style, size, color, at=0.0, gap=0, tracking=0):
    return {"text": text, "style": style, "size": size, "color": color,
            "at": at, "gap": gap, "tracking": tracking}


def hook_of(tip):
    """The line on screen at frame 0. Falls back to the first intro line."""
    return tip.get("hook") or as_list(tip.get("intro"))[0]


def build_scenes(tip):
    intro = as_list(tip.get("intro"))
    if not tip.get("hook"):
        intro = intro[1:]
    cta_lines = as_list(tip.get("ctaLines"))
    return [
        # The hook: on screen from the very first frame.
        ("THE MOMENT", [
            el(hook_of(tip), "bold", 86, WHITE),
            *[el(line, "regular", 54, LIGHT, at=1.3 + i * 0.8, gap=48 if i == 0 else 12)
              for i, line in enumerate(intro)],
        ]),
        ("THE IDEA", [
            el(tip["statement"], "bold", 78, WHITE),
        ]),
        ("YOUR CALL", [
            el(tip["q1"], "regular", 54, LIGHT),
            el(tip["q2"], "bold", 60, WHITE, at=1.2, gap=28),
            el(tip["q3"], "italic", 44, DIM, at=2.6, gap=56),
        ]),
        ("THE TAKEAWAY", [
            el(tip["t1"], "regular", 52, LIGHT),
            el(tip["t2"], "bold", 64, WHITE, at=1.2, gap=24),
        ]),
        ("YOUR TURN", [
            el(tip["cta"], "bold", 64, ORANGE),
            *[el(line, "regular", 48, LIGHT, at=0.9 + i * 0.6, gap=36 if i == 0 else 14)
              for i, line in enumerate(cta_lines)],
            el(tip["ctaPrompt"], "semibold", 46, WHITE, at=0.9 + len(cta_lines) * 0.6 + 0.4, gap=56),
        ]),
    ]


def scene_duration(index, elements):
    last_at = max(e["at"] for e in elements)
    words = sum(len(e["text"].split()) for e in elements)
    hold = 2.5 if index == 4 else 1.3  # the comment prompt stays up longest
    return max(last_at + ENTER + hold, words / READ_WPS + 0.6)


def layout(elements):
    """Wrap and position elements, shrinking them until the scene fits.

    Returns a list of (element, [(line, font, y)]) with y relative to the
    top of the scene block, and the block height.
    """
    scale = 1.0
    while True:
        placed, y = [], 0.0
        for e in elements:
            fnt = font(e["style"], e["size"] * scale)
            y += e["gap"] * scale
            tr = e["tracking"] * scale
            lines = wrap(e["text"], fnt, CONTENT_W, tr)
            line_h = fnt.size * 1.22
            rows = [(ln, fnt, y + i * line_h, tr) for i, ln in enumerate(lines)]
            placed.append((e, rows))
            y += line_h * (len(lines) - 1) + fnt.size
        if y <= CONTENT_BOTTOM - CONTENT_TOP - 80 or scale <= 0.6:
            return placed, y
        scale -= 0.04


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# --- Drawing -----------------------------------------------------------------


def base_frame(tip):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, BAR_W - 1, H], fill=ORANGE)

    left_f = font("bold", 30)
    draw_text(d, (LEFT, HEADER_Y), "YOUR PRACTICE HACKS", left_f, ORANGE, 5)
    right = f"{str(tip.get('day', 'Friday')).upper()} TIP / {tip['post']}"
    right_f = font("semibold", 26)
    dy = left_f.getbbox("Y")[3] - right_f.getbbox("Y")[3]
    draw_text(d, (RIGHT - text_width(right, right_f, 4), HEADER_Y + dy), right, right_f, HEADER_DIM, 4)
    d.rectangle([LEFT, PROGRESS_Y, RIGHT, PROGRESS_Y + 3], fill=RULE)

    tag_f = font("semibold", 34)
    draw_text(d, (LEFT, FOOTER_Y), TAGLINE, tag_f, ORANGE)
    draw_text(d, (LEFT, FOOTER_Y + 56), SITE, font("regular", 28), DIM, 3)
    return img


def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(round(alpha * 255)),)


def draw_scene(frame, label, placed, block_h, t, duration, first):
    """Draw one scene onto frame at t seconds into the scene."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    fade_out = 1.0 - ease_out((t - (duration - EXIT)) / EXIT) if t > duration - EXIT else 1.0
    top = CONTENT_TOP + (CONTENT_BOTTOM - CONTENT_TOP - block_h - 80) / 2 + 80

    # Scene label with a short orange rule.
    a = (1.0 if first else ease_out(t / ENTER)) * fade_out
    lab_f = font("bold", 30)
    d.rectangle([LEFT, top - 62, LEFT + 44, top - 58], fill=rgba(ORANGE, a))
    draw_text(d, (LEFT + 62, top - 78), label, lab_f, rgba(ORANGE, a), 5)

    for e, rows in placed:
        for i, (line, fnt, y, tr) in enumerate(rows):
            start = e["at"] + i * STAGGER
            # The very first line of the reel is fully visible at frame 0.
            p = 1.0 if (first and e["at"] == 0) else ease_out((t - start) / ENTER)
            if p <= 0:
                continue
            draw_text(d, (LEFT, top + y + (1 - p) * RISE), line, fnt, rgba(e["color"], p * fade_out), tr)

    frame.alpha_composite(layer)


def render_reel(tip, out_path, cover_path):
    scenes = [(label, *layout(els), scene_duration(i, els))
              for i, (label, els) in enumerate(build_scenes(tip))]
    total = sum(s[3] for s in scenes)
    n_frames = int(round(total * FPS))
    base = base_frame(tip).convert("RGBA")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        # Silent stereo track: some players and uploaders expect an audio stream.
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest", "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for n in range(n_frames):
        t = n / FPS
        start = 0.0
        for i, (label, placed, block_h, dur) in enumerate(scenes):
            if t < start + dur or i == len(scenes) - 1:
                break
            start += dur
        frame = base.copy()
        draw_scene(frame, label, placed, block_h, t - start, dur, first=(i == 0))
        # Progress bar fills across the top so viewers see how short it is.
        d = ImageDraw.Draw(frame)
        d.rectangle([LEFT, PROGRESS_Y, LEFT + (RIGHT - LEFT) * (n + 1) / n_frames, PROGRESS_Y + 3], fill=ORANGE)
        proc.stdin.write(frame.convert("RGB").tobytes())

    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")

    write_cover(tip, base, cover_path)
    return total


def write_cover(tip, base, cover_path):
    """A still cover: the hook and the subtitle, centered for the 4:5 grid crop."""
    frame = base.copy()
    d = ImageDraw.Draw(frame)
    els = [
        el(hook_of(tip), "bold", 92, WHITE),
        el(tip["subtitle"].upper(), "semibold", 38, ORANGE, gap=48, tracking=5),
    ]
    placed, block_h = layout(els)
    top = (H - block_h) / 2
    d.rectangle([LEFT, top - 70, LEFT + 44, top - 66], fill=ORANGE)
    for e, rows in placed:
        for line, fnt, y, tr in rows:
            draw_text(d, (LEFT, top + y), line, fnt, e["color"], tr)
    frame.convert("RGB").save(cover_path, "PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tip", help="Path to tip JSON file")
    parser.add_argument("-o", "--out", help="Output MP4 (default: reels/<tip name>.mp4)")
    args = parser.parse_args()

    tip_path = Path(args.tip)
    tip = json.loads(tip_path.read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else ROOT / "reels" / f"{tip_path.stem}.mp4"
    cover = out.with_name(f"{out.stem}-cover.png")
    total = render_reel(tip, out, cover)
    print(f"Wrote {out} ({total:.1f}s) and {cover}")


if __name__ == "__main__":
    main()
