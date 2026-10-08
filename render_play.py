#!/usr/bin/env python3
"""Render an animated play breakdown (1080x1920 MP4) from a play diagram spec.

No game footage needed: players are drawn as dots on a soccer pitch or a
basketball court and move along paths you describe. The play runs, pauses on
the key moment, circles the player who matters, gives one coaching point, then
ends on a question for coaches.

Usage:
    python render_play.py plays/play-01.json    # -> plays/out/play-01.mp4, -cover.png, -caption.txt

Spec (JSON), times are seconds of play (the pause does not count):
    number        play number for the header (PLAY TIP / 01)
    sport         "soccer" or "basketball"
    hook          on screen from frame 0
    players       {"id": {"team": "us"|"them", "label": "8", "path": [[t, x, y], ...]}}
                  x, y are fractions of the field (0,0 top left); our team attacks up
    ball          [[t, "player id"], ...]; between two keys with different players
                  the ball travels as a pass
    lanes         [{"from": id, "to": id, "show": [t0, t1], "style": "blocked"|"open"}]
    shadows       [{"from": id, "behind": id, "show": [t0, t1]}] shades the space a
                  defender blocks from the ball
    freeze        {"at": t, "for": 4, "mark": id, "label": "short text",
                   "label_side": "below"|"above"|"left"|"right"}
    end           when the play stops
    point         [bold line, lighter line], shown from the pause on
    question      closing question for coaches
    music         a file in music/ (optional; rotates by number otherwise)
    caption_tags  hashtags for the caption
"""

import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from render_card import DIM, LIGHT, NAVY, ORANGE, WHITE, draw_text, font, wrap
from render_reel import (
    FPS, H, LEFT, PROGRESS_Y, RIGHT, W, audio_args, base_frame, ease_out,
    music_credit, pick_music, rgba,
)

ROOT = Path(__file__).resolve().parent
CONTENT_W = RIGHT - LEFT
HOOK_TOP = 290
FIELD = (LEFT, 560, W - LEFT + 20, 1180)  # x0, y0, x1, y1 on the frame
END_CARD = 3.0
SS = 2  # supersampling for smooth circles and lines
GRASS = "#22385A"
LINES = "#5A6D92"
THEM = "#C9CBDA"
BLOCKED = "#8A8DA8"


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def at_path(path, t):
    """Position on a [[t, x, y], ...] path at time t, eased between keys."""
    if t <= path[0][0]:
        return path[0][1], path[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(path, path[1:]):
        if t <= t1:
            k = smooth((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return lerp(x0, x1, k), lerp(y0, y1, k)
    return path[-1][1], path[-1][2]


def to_px(x, y, s=1):
    x0, y0, x1, y1 = FIELD
    return (x0 + x * (x1 - x0)) * s, (y0 + y * (y1 - y0)) * s


# --- Fields ------------------------------------------------------------------


def draw_soccer(d, s):
    x0, y0, x1, y1 = [v * s for v in FIELD]
    lw = 3 * s
    d.rounded_rectangle([x0, y0, x1, y1], 18 * s, fill=GRASS)
    fw, fh = x1 - x0, y1 - y0
    # Halfway line at the bottom, attacking goal at the top.
    d.line([x0 + 20 * s, y1 - 40 * s, x1 - 20 * s, y1 - 40 * s], fill=LINES, width=lw)
    cx = (x0 + x1) / 2
    r = fw * 0.13
    d.arc([cx - r, y1 - 40 * s - r, cx + r, y1 - 40 * s + r], 180, 360, fill=LINES, width=lw)
    box_w, box_h = fw * 0.6, fh * 0.24
    d.rectangle([cx - box_w / 2, y0 + 20 * s, cx + box_w / 2, y0 + 20 * s + box_h], outline=LINES, width=lw)
    six_w, six_h = fw * 0.28, fh * 0.09
    d.rectangle([cx - six_w / 2, y0 + 20 * s, cx + six_w / 2, y0 + 20 * s + six_h], outline=LINES, width=lw)
    goal_w = fw * 0.13
    d.rectangle([cx - goal_w / 2, y0 + 8 * s, cx + goal_w / 2, y0 + 20 * s], fill=LINES)
    d.line([x0 + 20 * s, y0 + 20 * s, x1 - 20 * s, y0 + 20 * s], fill=LINES, width=lw)
    d.line([x0 + 20 * s, y0 + 20 * s, x0 + 20 * s, y1 - 40 * s], fill=LINES, width=lw)
    d.line([x1 - 20 * s, y0 + 20 * s, x1 - 20 * s, y1 - 40 * s], fill=LINES, width=lw)


def draw_basketball(d, s):
    x0, y0, x1, y1 = [v * s for v in FIELD]
    lw = 3 * s
    d.rounded_rectangle([x0, y0, x1, y1], 18 * s, fill=GRASS)
    fw, fh = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    base = y0 + 20 * s
    d.line([x0 + 20 * s, base, x1 - 20 * s, base], fill=LINES, width=lw)
    d.line([x0 + 20 * s, base, x0 + 20 * s, y1 - 20 * s], fill=LINES, width=lw)
    d.line([x1 - 20 * s, base, x1 - 20 * s, y1 - 20 * s], fill=LINES, width=lw)
    lane_w, lane_h = fw * 0.2, fh * 0.42
    d.rectangle([cx - lane_w / 2, base, cx + lane_w / 2, base + lane_h], outline=LINES, width=lw)
    r = lane_w / 2
    d.arc([cx - r, base + lane_h - r, cx + r, base + lane_h + r], 0, 180, fill=LINES, width=lw)
    hoop_y = base + fh * 0.08
    d.line([cx - fw * 0.06, base + fh * 0.05, cx + fw * 0.06, base + fh * 0.05], fill=LINES, width=lw)
    d.ellipse([cx - 14 * s, hoop_y - 14 * s, cx + 14 * s, hoop_y + 14 * s], outline=ORANGE, width=lw)
    # Three-point line: short straights in the corners, then an arc.
    tr = fw * 0.42
    corner = x0 + 20 * s + fw * 0.05
    d.line([corner, base, corner, hoop_y], fill=LINES, width=lw)
    d.line([x1 - (corner - x0), base, x1 - (corner - x0), hoop_y], fill=LINES, width=lw)
    ang = math.degrees(math.acos(min((cx - corner) / tr, 1)))
    d.arc([cx - tr, hoop_y - tr, cx + tr, hoop_y + tr], ang, 180 - ang, fill=LINES, width=lw)


FIELDS = {"soccer": draw_soccer, "basketball": draw_basketball}


# --- Frames ------------------------------------------------------------------


def dashed(d, a, b, fill, width, dash, gap):
    (ax, ay), (bx, by) = a, b
    length = math.hypot(bx - ax, by - ay)
    if length == 0:
        return
    ux, uy = (bx - ax) / length, (by - ay) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        d.line([ax + ux * pos, ay + uy * pos, ax + ux * end, ay + uy * end], fill=fill, width=width)
        pos = end + gap


def ball_pos(spec, t, positions):
    keys = spec["ball"]
    if t <= keys[0][0]:
        return positions[keys[0][1]]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            if a == b:
                return positions[a]
            k = smooth((t - t0) / (t1 - t0))
            (ax, ay), (bx, by) = positions[a], positions[b]
            return lerp(ax, bx, k), lerp(ay, by, k)
    return positions[keys[-1][1]]


def draw_play(spec, t, field_img, mark_k=0.0):
    """The field layer (full frame size, RGBA) at play time t."""
    s = SS
    layer = field_img.copy()
    d = ImageDraw.Draw(layer)
    positions = {pid: at_path(p["path"], t) for pid, p in spec["players"].items()}
    px = {pid: to_px(x, y, s) for pid, (x, y) in positions.items()}

    for sh in spec.get("shadows", []):
        t0, t1 = sh["show"]
        if not t0 <= t <= t1:
            continue
        a = min(1.0, (t - t0) / 0.4, (t1 - t) / 0.4)
        (fx, fy), (dx, dy) = px[sh["from"]], px[sh["behind"]]
        length = math.hypot(dx - fx, dy - fy) or 1
        ux, uy = (dx - fx) / length, (dy - fy) / length
        nx, ny = -uy, ux
        r, reach = 36 * s, 300 * s
        poly = [(dx + nx * r, dy + ny * r), (dx - nx * r, dy - ny * r),
                (dx + ux * reach - nx * r * 2.4, dy + uy * reach - ny * r * 2.4),
                (dx + ux * reach + nx * r * 2.4, dy + uy * reach + ny * r * 2.4)]
        shade = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(shade).polygon(poly, fill=(0, 0, 0, int(110 * a)))
        layer.alpha_composite(shade)
        d = ImageDraw.Draw(layer)

    for lane in spec.get("lanes", []):
        t0, t1 = lane["show"]
        if not t0 <= t <= t1:
            continue
        a = min(1.0, (t - t0) / 0.3, (t1 - t) / 0.3)
        p1, p2 = px[lane["from"]], px[lane["to"]]
        if lane["style"] == "open":
            d.line([*p1, *p2], fill=rgba(ORANGE, a), width=7 * s)
        else:
            dashed(d, p1, p2, rgba(BLOCKED, a), 5 * s, 22 * s, 16 * s)
            # An X where the lane is cut.
            mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            if lane.get("cut"):
                mx, my = px[lane["cut"]]
                my += (p1[1] - my) * 0.35
            k = 18 * s
            d.line([mx - k, my - k, mx + k, my + k], fill=rgba(ORANGE, a), width=7 * s)
            d.line([mx - k, my + k, mx + k, my - k], fill=rgba(ORANGE, a), width=7 * s)

    pr = 34 * s
    num_f = font("bold", 34 * s)
    for pid, p in spec["players"].items():
        x, y = px[pid]
        if p["team"] == "us":
            d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=ORANGE, outline=WHITE, width=3 * s)
            label = p.get("label", pid)
            w = num_f.getlength(label)
            d.text((x - w / 2, y - 21 * s), label, font=num_f, fill=WHITE)
        else:
            d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=NAVY, outline=THEM, width=6 * s)
            k = 13 * s
            d.line([x - k, y - k, x + k, y + k], fill=THEM, width=5 * s)
            d.line([x - k, y + k, x + k, y - k], fill=THEM, width=5 * s)

    bx, by = ball_pos(spec, t, px)
    held = any(math.hypot(bx - x, by - y) < 1 for x, y in px.values())
    if held:
        bx, by = bx + 30 * s, by - 30 * s
    br = 13 * s
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=WHITE, outline=NAVY, width=3 * s)

    if mark_k > 0:
        fr = spec["freeze"]
        mx, my = px[fr["mark"]]
        r = (60 * s) * (1.7 - 0.7 * ease_out(mark_k / 0.35))
        a = ease_out(mark_k / 0.35)
        d.ellipse([mx - r, my - r, mx + r, my + r], outline=rgba(WHITE, a), width=7 * s)
        if fr.get("label"):
            lf = font("bold", 34 * s)
            tw = lf.getlength(fr["label"])
            fx0, _, fx1, _ = [v * s for v in FIELD]
            side = fr.get("label_side", "below")
            if side in ("left", "right"):
                lx = mx + 80 * s if side == "right" else mx - 80 * s - tw
                ly = my - 25 * s
            else:
                lx = mx - tw / 2
                ly = my + 72 * s if side == "below" else my - 122 * s
            lx = min(max(lx, fx0 + 24 * s), fx1 - tw - 24 * s)
            d.rounded_rectangle([lx - 16 * s, ly - 8 * s, lx + tw + 16 * s, ly + 50 * s], 10 * s,
                                fill=rgba(WHITE, 0.95 * a))
            d.text((lx, ly), fr["label"], font=lf, fill=rgba(NAVY, a))
    return layer.resize((W, H), Image.LANCZOS)


def text_block(d, lines, top, style, size, color, alpha=1.0, gap=0.25):
    fnt = font(style, size)
    y = top
    for para in lines:
        for ln in wrap(para, fnt, CONTENT_W):
            draw_text(d, (LEFT, y), ln, fnt, rgba(color, alpha))
            y += fnt.size * (1 + gap)
    return y


def timeline(spec):
    """(play time, phase, seconds into phase) for every output frame."""
    fr = spec["freeze"]
    hold = float(fr.get("for", 4))
    end = float(spec["end"])
    frames = []
    for i in range(int(fr["at"] * FPS)):
        frames.append((i / FPS, "play", i / FPS))
    for i in range(int(hold * FPS)):
        frames.append((fr["at"], "freeze", i / FPS))
    for i in range(int((end - fr["at"]) * FPS)):
        frames.append((fr["at"] + i / FPS, "after", i / FPS))
    for i in range(int(END_CARD * FPS)):
        frames.append((end, "end", i / FPS))
    return frames


def compose(spec, base, field_img, t, phase, tp, n, total):
    mark_k = tp if phase == "freeze" else 0.0
    frame = base.copy()
    frame.alpha_composite(draw_play(spec, t, field_img, mark_k))
    d = ImageDraw.Draw(frame)
    text_block(d, [spec["hook"]], HOOK_TOP, "bold", 62, WHITE)

    if phase == "freeze":
        chip = font("bold", 26)
        d.rounded_rectangle([FIELD[0] + 18, FIELD[1] + 18, FIELD[0] + 150, FIELD[1] + 60], 8, fill=ORANGE)
        d.text((FIELD[0] + 34, FIELD[1] + 22), "PAUSE", font=chip, fill=WHITE)

    if phase in ("freeze", "after", "end"):
        a = ease_out(tp / 0.4) if phase == "freeze" else 1.0
        y = text_block(d, [spec["point"][0]], FIELD[3] + 50, "bold", 52, WHITE, a)
        if len(spec["point"]) > 1:
            text_block(d, spec["point"][1:], y + 6, "regular", 40, LIGHT, a)

    if phase == "end":
        a = ease_out(tp / 0.4)
        frame.alpha_composite(Image.new("RGBA", (W, H), rgba(NAVY, 0.9 * a)))
        d = ImageDraw.Draw(frame)
        fnt = font("bold", 64)
        lines = wrap(spec["question"], fnt, CONTENT_W)
        y = 760 - len(lines) * 40
        for ln in lines:
            draw_text(d, (LEFT, y), ln, fnt, rgba(ORANGE, a))
            y += fnt.size * 1.2
        draw_text(d, (LEFT, y + 40), "Share your habit in the comments.", font("semibold", 44), rgba(WHITE, a))

    d.rectangle([LEFT, PROGRESS_Y, LEFT + (RIGHT - LEFT) * (n + 1) / total, PROGRESS_Y + 3], fill=ORANGE)
    return frame


def write_caption(spec, music, path):
    parts = [spec["hook"], " ".join(spec["point"]), f'{spec["question"]} Share your habit in the comments.']
    if music:
        parts.append(music_credit(music))
    parts.append(spec.get("caption_tags", "#YouthSports #YouthCoach #CoachingTips #KidsSports"))
    path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def render(spec, out_path):
    field_img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    FIELDS[spec.get("sport", "soccer")](ImageDraw.Draw(field_img), SS)
    base = base_frame({"day": "Play", "post": f'{int(spec.get("number", 1)):02d}'}).convert("RGBA")
    frames = timeline(spec)
    total = len(frames) / FPS

    music = pick_music({"music": spec.get("music"), "post": spec.get("number", 1)})
    audio_in, audio_filter = audio_args(music, total)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        *audio_in, "-shortest", "-map", "0:v", "-map", "1:a", *audio_filter,
        "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        str(out_path)], stdin=subprocess.PIPE)
    cover = None
    for n, (t, phase, tp) in enumerate(frames):
        frame = compose(spec, base, field_img, t, phase, tp, n, len(frames))
        if phase == "freeze" and tp >= 1.5 and cover is None:
            cover = frame
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")

    stem = out_path.with_suffix("")
    cover.convert("RGB").save(f"{stem}-cover.png", "PNG", optimize=True)
    write_caption(spec, music, Path(f"{stem}-caption.txt"))
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else spec_path.parent / "out" / f"{spec_path.stem}.mp4"
    total = render(spec, out)
    note = "" if 15 <= total <= 20 else "  (outside 15-20s: adjust end or freeze length)"
    print(f"Wrote {out} ({total:.1f}s){note}")


if __name__ == "__main__":
    main()
