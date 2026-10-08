#!/usr/bin/env python3
"""Render a coaching breakdown reel (1080x1920 MP4) from a game or practice video.

A breakdown plays a short moment from a video, freezes on the key frame, circles
the player or space that matters, explains one coaching point, then ends on a
question for coaches. The commentary is the point: it teaches, it does not just
replay a highlight.

Usage:
    python render_breakdown.py breakdowns/bd-001.json    # -> breakdowns/out/bd-001.mp4

Spec (JSON):
    source        path to the video file
    start, end    seconds in the source to play (keep end - start around 8-12s)
    freeze_at     second in the source to freeze on (between start and end)
    freeze_for    seconds to hold the freeze (default 4)
    mark          {"x": 0-1, "y": 0-1, "r": 0-1} circle on the frozen frame,
                  as fractions of the video's width and height
    mark_label    short label next to the circle, e.g. "#7 finds space"
    hook          on screen from frame 0, above the video
    point         [bold line, lighter line] shown from the freeze on
    question      the closing question for coaches
    credit        who filmed it, e.g. "Video: Riverside FC (used with permission)"
    number        breakdown number for the header (FILM TIP / 01)
"""

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from render_card import DIM, LIGHT, NAVY, ORANGE, WHITE, draw_text, font, wrap
from render_reel import (
    FPS, H, LEFT, PROGRESS_Y, RIGHT, W, base_frame, ease_out, rgba,
)

ROOT = Path(__file__).resolve().parent
CONTENT_W = RIGHT - LEFT
HOOK_TOP = 290
VIDEO_TOP = 560
END_CARD = 3.0


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height",
        "-of", "json", str(path)])
    streams = json.loads(out)["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in streams)
    return v["width"], v["height"], has_audio


def read_frames(path, start, end, vw, vh):
    """Decode the segment at FPS, scaled to vw x vh, as a list of RGB images."""
    proc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-ss", f"{start}", "-to", f"{end}", "-i", str(path),
        "-vf", f"fps={FPS},scale={vw}:{vh}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    size = vw * vh * 3
    frames = []
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        frames.append(Image.frombytes("RGB", (vw, vh), buf))
    proc.wait()
    if not frames:
        raise SystemExit(f"No frames read from {path} between {start}s and {end}s")
    return frames


def text_block(d, lines, top, style, size, color, alpha=1.0, gap=0.25):
    fnt = font(style, size)
    y = top
    for para in lines:
        for ln in wrap(para, fnt, CONTENT_W):
            draw_text(d, (LEFT, y), ln, fnt, rgba(color, alpha))
            y += fnt.size * (1 + gap)
    return y


def render(spec, out_path):
    src = (ROOT / spec["source"]) if not Path(spec["source"]).is_absolute() else Path(spec["source"])
    start, end, freeze_at = float(spec["start"]), float(spec["end"]), float(spec["freeze_at"])
    freeze_for = float(spec.get("freeze_for", 4))
    if not start < freeze_at < end:
        raise SystemExit("freeze_at must be between start and end")

    sw, sh, has_audio = probe(src)
    vw = W
    vh = min(int(round(W * sh / sw / 2)) * 2, 760)  # 16:9 -> 608px; cap tall video
    frames = read_frames(src, start, end, vw, vh)
    freeze_idx = min(int((freeze_at - start) * FPS), len(frames) - 1)

    play1 = frames[:freeze_idx]
    still = frames[freeze_idx]
    play2 = frames[freeze_idx:]
    n_freeze = int(freeze_for * FPS)
    n_end = int(END_CARD * FPS)
    total_frames = len(play1) + n_freeze + len(play2) + n_end

    # Header reads "FILM TIP / <number>".
    base = base_frame({"day": "Film", "post": f'{int(spec.get("number", 1)):02d}'}).convert("RGBA")
    mx, my, mr = spec["mark"]["x"] * vw, spec["mark"]["y"] * vh, spec["mark"]["r"] * vw

    out_path.parent.mkdir(parents=True, exist_ok=True)
    silent = out_path.with_suffix(".video.mp4")
    enc = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        str(silent)], stdin=subprocess.PIPE)

    def compose(n, video, phase, t_phase):
        frame = base.copy()
        d = ImageDraw.Draw(frame)
        # Hook: on screen from frame 0.
        text_block(d, [spec["hook"]], HOOK_TOP, "bold", 62, WHITE)
        frame.paste(video, (0, VIDEO_TOP))
        video_bottom = VIDEO_TOP + vh
        d.text((LEFT, video_bottom + 14), spec["credit"], font=font("regular", 24), fill=DIM)

        if phase in ("freeze", "after", "end"):
            # Coaching point appears with the freeze and stays.
            a = ease_out(t_phase / 0.4) if phase == "freeze" else 1.0
            y = text_block(d, [spec["point"][0]], video_bottom + 70, "bold", 50, WHITE, a)
            if len(spec["point"]) > 1:
                text_block(d, [spec["point"][1]], y + 10, "regular", 40, LIGHT, a)

        if phase == "freeze":
            overlay = Image.new("RGBA", (vw, vh), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.rectangle([0, 0, vw, vh], fill=(0, 0, 0, 70))
            grow = ease_out(t_phase / 0.35)
            r = mr * (1.6 - 0.6 * grow)
            od.ellipse([mx - r, my - r, mx + r, my + r], outline=rgba(ORANGE, grow), width=8)
            if spec.get("mark_label"):
                lf = font("bold", 34)
                lx = min(mx + r + 16, vw - lf.getlength(spec["mark_label"]) - 30)
                ly = max(my - r - 50, 10)
                tw = lf.getlength(spec["mark_label"])
                od.rectangle([lx - 12, ly - 6, lx + tw + 12, ly + 44], fill=rgba(NAVY, 0.85 * grow))
                od.text((lx, ly), spec["mark_label"], font=lf, fill=rgba(ORANGE, grow))
            chip = font("bold", 26)
            od.rectangle([20, 20, 150, 62], fill=rgba(ORANGE, 0.95))
            od.text((34, 24), "PAUSE", font=chip, fill=(255, 255, 255, 255))
            frame.alpha_composite(overlay, (0, VIDEO_TOP))

        if phase == "end":
            a = ease_out(t_phase / 0.4)
            veil = Image.new("RGBA", (W, H), rgba(NAVY, 0.88 * a))
            frame.alpha_composite(veil)
            d = ImageDraw.Draw(frame)
            fnt = font("bold", 64)
            lines = wrap(spec["question"], fnt, CONTENT_W)
            y = 760 - len(lines) * 40
            for ln in lines:
                draw_text(d, (LEFT, y), ln, fnt, rgba(ORANGE, a))
                y += fnt.size * 1.2
            draw_text(d, (LEFT, y + 40), "Share your habit in the comments.",
                      font("semibold", 44), rgba(WHITE, a))

        d = ImageDraw.Draw(frame)
        d.rectangle([LEFT, PROGRESS_Y, LEFT + (RIGHT - LEFT) * (n + 1) / total_frames, PROGRESS_Y + 3],
                    fill=ORANGE)
        enc.stdin.write(frame.convert("RGB").tobytes())

    n = 0
    for i, f in enumerate(play1):
        compose(n, f, "play", i / FPS); n += 1
    for i in range(n_freeze):
        compose(n, still, "freeze", i / FPS); n += 1
    for i, f in enumerate(play2):
        compose(n, f, "after", i / FPS); n += 1
    for i in range(n_end):
        compose(n, frames[-1], "end", i / FPS); n += 1
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("ffmpeg video encode failed")

    # Audio: the clip's own sound, quieter, with silence during the freeze and end card.
    total = total_frames / FPS
    if has_audio:
        pre, post = freeze_at - start, end - freeze_at
        filt = (f"[1:a]atrim=start={start}:end={freeze_at},asetpts=PTS-STARTPTS,volume=0.6[a1];"
                f"anullsrc=r=44100:cl=stereo,atrim=0:{freeze_for}[s1];"
                f"[1:a]atrim=start={freeze_at}:end={end},asetpts=PTS-STARTPTS,volume=0.6[a2];"
                f"anullsrc=r=44100:cl=stereo,atrim=0:{END_CARD}[s2];"
                f"[a1]aresample=44100,aformat=channel_layouts=stereo[b1];"
                f"[a2]aresample=44100,aformat=channel_layouts=stereo[b2];"
                f"[b1][s1][b2][s2]concat=n=4:v=0:a=1[aout]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(src),
               "-filter_complex", filt, "-map", "0:v", "-map", "[aout]"]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(silent),
               "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.2f}",
            "-movflags", "+faststart", str(out_path)]
    subprocess.check_call(cmd)
    silent.unlink()
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
    note = "" if 15 <= total <= 20 else "  (outside 15-20s: adjust start/end or freeze_for)"
    print(f"Wrote {out} ({total:.1f}s){note}")


if __name__ == "__main__":
    main()
