# Coaching Breakdowns

Short (15-20 second) reels that teach from real game or practice footage:
play the moment, freeze on the key frame, circle what matters, give one
coaching point, end on a question for coaches.

The commentary is the point. These teach; they do not just replay highlights.

## Before using any footage

- **Use footage you filmed, or have the owner's permission.** Put who filmed it
  in `credit`, e.g. `"Video: Riverside FC (used with permission)"`.
- **Kids on camera:** only use footage where the families are fine with it
  being shared. Never name a child; use a jersey number or "the left back".
- Keep the coaching point positive. Point at what a player did well, or at a
  space or habit. Never single out a child's mistake.

## Make one

1. Put the video in `videos/` (or anywhere in the repo).
2. Copy `bd-template.json` to `bd-NNN.json` and fill it in. Keep `end - start`
   around 8-12 seconds and `freeze_for` around 4, so the reel lands at 15-20s.
3. Render:

   ```sh
   python render_breakdown.py breakdowns/bd-001.json   # -> breakdowns/out/bd-001.mp4
   ```

4. Watch it. Check the circle sits on the right player at the freeze.

Voice rules from `voice.md` apply: calm, plain, no hype, no exclamation points,
end on an honest question.
