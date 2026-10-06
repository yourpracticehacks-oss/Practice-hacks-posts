# Practice Hacks Posts

Weekly post generator for [Your Practice Hacks](https://yourpracticehacks.com).
Social media tips for youth sports coaches.

*Your Team. Your Kids. Your Practice.*

## Layout

- `voice.md`: voice and writing guide. Read it before writing a tip.
- `tips/`: one JSON file per tip (e.g. `tips/post-20.json`).
- `render_card.py`: turns a tip into a 1080x1350 PNG card.
- `cards/`: rendered cards.
- `fonts/`: Inter (SIL Open Font License, see `fonts/OFL.txt`).

## Make a card

```sh
pip install -r requirements.txt
python render_card.py tips/post-20.json      # writes cards/post-20.png
```

To add a new week, copy the latest tip JSON, bump `post`, edit the text, and
render it. If a tip runs long, the renderer shrinks the text slightly so it
still fits.
