# Practice Hacks Posts

Weekly post generator for [Your Practice Hacks](https://yourpracticehacks.com).
Social media tips for youth sports coaches.

*Your Team. Your Kids. Your Practice.*

## Layout

- `voice.md`: voice and writing guide. Read it before writing a tip.
- `tips/`: one JSON file per tip (e.g. `tips/post-20.json`).
- `render_reel.py`: turns a tip into a 1080x1920 MP4 reel and a cover image.
- `reels/`: rendered reels and covers. Reels are the main format.
- `music/`: licensed background tracks for reels (see `music/README.md`).
- `render_card.py`: turns a tip into a 1080x1350 PNG card (still version).
- `cards/`: rendered cards.
- `topics.md`, `posted.md`, `ROUTINE.md`: topic backlog, post log, and the
  monthly posting routine.
- `fonts/`: Inter (SIL Open Font License, see `fonts/OFL.txt`).

## Make a reel or card

Needs Python 3, Pillow, and ffmpeg.

```sh
pip install -r requirements.txt
python render_reel.py tips/post-21.json      # writes reels/post-21.mp4 and reels/post-21-cover.png
python render_card.py tips/post-21.json      # writes cards/post-21.png
```

To add a new week, copy the latest tip JSON, bump `post`, edit the text, and
render it. If a tip runs long, the renderer shrinks the text slightly so it
still fits.
