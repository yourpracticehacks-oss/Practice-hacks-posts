#!/usr/bin/env python3
"""Apply text edits to tips and rebuild their captions with the current hashtags.

Usage: python3 tools/softball_fix.py edits.json FIRST LAST

edits.json maps a post number to the fields to replace, e.g.
{"31": {"intro": ["...", "..."], "choice": "Say something or say nothing."}}.
"choice" replaces the either/or line of the caption. Every tip from FIRST to
LAST gets its caption rebuilt from its fields, with hashtags from gen_tips.py.
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_tips as g

ROOT = g.ROOT
edits = json.load(open(sys.argv[1]))
first, last = int(sys.argv[2]), int(sys.argv[3])
themes = {}
for line in open(ROOT / "topics.md"):
    m = re.match(r"\|\s*(T\d+)\s*\|\s*([^|]+?)\s*\|", line)
    if m:
        themes[m.group(1)] = m.group(2)
credits = json.load(open(ROOT / "music" / "tracks.json"))

for n in range(first, last + 1):
    path = ROOT / "tips" / f"post-{n}.json"
    tip = json.loads(path.read_text())
    e = dict(edits.get(str(n), {}))
    choice = e.pop("choice", None)
    tip.update(e)
    old_lines = tip["caption"].split("\n\n")[0].split("\n")
    choice_line = f"{choice} {g.NO_ONE_ANSWER[n % 4]}" if choice else old_lines[3]
    cta_q = re.sub(r"^Coaches\s*—\s*", "", tip["cta"]); cta_q = cta_q[0].upper() + cta_q[1:]
    body = "\n".join([tip["hook"], " ".join(tip["intro"]), tip["statement"], choice_line,
                      f"{cta_q} Share your habit in the comments."])
    tip["caption"] = f'{body}\n\n{credits[tip["music"]]["credit"]}\n\n{g.BASE} {g.TAGS[themes[tip["topicId"]]]}'
    if any("!" in str(v) for v in tip.values()):
        raise SystemExit(f"post {n}: exclamation point")
    path.write_text(json.dumps(tip, indent=2, ensure_ascii=False) + "\n")
print(f"updated {first}-{last}")
