# Reel Music

Drop music files here (`.mp3`, `.m4a`, `.wav`, `.ogg`, `.flac`, `.aac`).
`render_reel.py` picks one per reel, rotating by post number, unless a tip
sets `"music": "<file name>"`. Tracks loop if they are short, fade in and out,
and are levelled to a steady, quiet volume under the text.

**Only add tracks you are licensed to use on social media**, such as tracks
from the YouTube Audio Library, Pixabay Music, or a paid stock-music service.
No popular or commercial songs: those can get a reel muted or taken down.

Fits the voice: calm, warm, unhurried. Acoustic guitar, soft piano, light
ambient. No vocals, no big drops.

## Tracks

Log every track and its license here, and add its credit text to
`tracks.json`. The renderer refuses a track that has no entry there, and
prints the credit to put in the caption. Remove a track if its license is
unclear.

Files are the first 45 seconds of each track (reels run about 30 seconds).

| File               | Title / Artist                | Source         | License   | Credit required |
|--------------------|-------------------------------|----------------|-----------|-----------------|
| `almost-bliss.mp3` | Almost Bliss / Kevin MacLeod  | incompetech.com | CC BY 4.0 | Yes             |
| `dreamer.mp3`      | Dreamer / Kevin MacLeod       | incompetech.com | CC BY 4.0 | Yes             |
| `easy-lemon.mp3`   | Easy Lemon / Kevin MacLeod    | incompetech.com | CC BY 4.0 | Yes             |
| `evening.mp3`      | Evening / Kevin MacLeod       | incompetech.com | CC BY 4.0 | Yes             |
| `morning.mp3`      | Morning / Kevin MacLeod       | incompetech.com | CC BY 4.0 | Yes             |

The credit for each goes in the caption, above the hashtags, exactly as in
`tracks.json`:

```
Music: "<Title>" Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0
http://creativecommons.org/licenses/by/4.0/
```

To add more tracks from incompetech.com, the catalog is at
`https://incompetech.com/music/royalty-free/pieces.json` and files download
from `https://incompetech.com/music/royalty-free/mp3-royaltyfree/<Title>.mp3`.
