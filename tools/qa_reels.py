"""QA for posts FIRST..LAST: duration, audio level, and a contact sheet of 5 frames per reel."""
import json, subprocess, sys
from PIL import Image
from pathlib import Path
R = str(Path(__file__).resolve().parent.parent / "reels")
a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rows = []
for n in range(a, b + 1):
    f = f"{R}/post-{n}.mp4"
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
    vol = subprocess.run(["ffmpeg", "-i", f, "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    mean = [l.split(":")[1].strip() for l in vol.splitlines() if "mean_volume" in l][0]
    flag = "" if 20 <= dur <= 34 and float(mean.split()[0]) > -30 else "  <-- CHECK"
    print(f"post {n}: {dur:.1f}s audio {mean}{flag}")
    frames = []
    for t in (0.0, 0.3, 0.5, 0.68, 0.93):
        png = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", f"{dur * t:.2f}", "-i", f, "-frames:v", "1",
                                       "-vf", "scale=216:-1", "-f", "image2pipe", "-vcodec", "png", "-"])
        import io; frames.append(Image.open(io.BytesIO(png)).convert("RGB"))
    rows.append(frames)
w, h = rows[0][0].size
sheet = Image.new("RGB", (w * 5, h * len(rows)), "white")
for i, fr in enumerate(rows):
    for j, im in enumerate(fr):
        sheet.paste(im, (j * w, i * h))
sheet.save(out)
