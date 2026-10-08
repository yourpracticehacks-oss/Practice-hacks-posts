#!/usr/bin/env python3
"""Turn a batch of written tips into tips/post-NN.json files with time slots.

Usage: python3 tools/gen_tips.py batch.json FIRST_POST YYYY-MM

batch.json is a list of tip dicts (topic, subtitle, hook, intro[2], statement,
q1, q2, q3, t1, t2, cta, ctaLines[2], ctaPrompt, choice). Tips are numbered
from FIRST_POST and placed, in order, into the free 10:00 and 17:00
America/New_York slots of the month. A slot is free if no existing tip file
already has that "publish" time. Each tip's "topic" must match the next
unused topic in topics.md (a topic is used once a tip file has its topicId).
"""
import calendar, datetime as d, json, os, re, sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("America/New_York")
HOURS = (10, 17)
TAGS = {
    "Keeping kids engaged": "#PracticePlanning #SoftballDrills",
    "Communication": "#PlayerDevelopment #SoftballCoach",
    "Handling parents": "#SoftballParents #SportsParents",
    "Game-day decisions": "#GameDay #SoftballCoach",
    "Building confidence": "#PlayerDevelopment #SoftballLife",
    "Practice habits": "#PracticePlanning #SoftballDrills",
}
BASE = "#YouthSoftball #Softball #FastpitchSoftball #YouthCoach #CoachingTips"
NO_ONE_ANSWER = ["There is no perfect answer.", "Both can work.", "Every team is different.",
                 "There is no single right way."]


def existing_tips():
    return [json.loads(p.read_text()) for p in sorted((ROOT / "tips").glob("post-*.json"))]


def free_slots(year, month):
    taken = {t["publish"] for t in existing_tips() if t.get("publish")}
    out = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        for h in HOURS:
            when = d.datetime(year, month, day, h, tzinfo=TZ)
            if when.isoformat() not in taken:
                out.append(when)
    return out


def unused_topics():
    used = {t.get("topicId") for t in existing_tips()}
    used |= {"T01", "T02", "T03", "T04"}  # posts 21-24 predate topicId tracking in some files
    rows = []
    for line in open(ROOT / "topics.md"):
        m = re.match(r"\|\s*(T\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1) not in used:
            rows.append(m.groups())
    return rows


def main():
    batch = json.load(open(sys.argv[1]))
    first = int(sys.argv[2])
    year, month = map(int, sys.argv[3].split("-"))
    slots, topics = free_slots(year, month), unused_topics()
    if len(batch) > len(slots):
        raise SystemExit(f"{len(batch)} tips but only {len(slots)} free slots")
    credits = json.load(open(ROOT / "music" / "tracks.json"))
    tracks = sorted(f for f in os.listdir(ROOT / "music") if f.endswith(".mp3"))
    for k, b in enumerate(batch):
        n, when = first + k, slots[k]
        tid, theme, topic = topics[k]
        if b["topic"] != topic:
            raise SystemExit(f"post {n}: batch topic {b['topic']!r} != next unused topic {topic!r}")
        music = tracks[n % len(tracks)]
        cta_q = re.sub(r"^Coaches\s*—\s*", "", b["cta"]); cta_q = cta_q[0].upper() + cta_q[1:]
        body = "\n".join([b["hook"], " ".join(b["intro"]), b["statement"],
                          f'{b["choice"]} {NO_ONE_ANSWER[n % 4]}',
                          f"{cta_q} Share your habit in the comments."])
        day = when.strftime("%A")
        tip = {"day": day, "post": n, "topicId": tid, "publish": when.isoformat(),
               "title": f"{day} Quick Tip", "subtitle": b["subtitle"], "hook": b["hook"],
               "intro": b["intro"], "statement": b["statement"],
               "q1": b["q1"], "q2": b["q2"], "q3": b["q3"], "t1": b["t1"], "t2": b["t2"],
               "cta": b["cta"], "ctaLines": b["ctaLines"], "ctaPrompt": b["ctaPrompt"],
               "caption": f'{body}\n\n{credits[music]["credit"]}\n\n{BASE} {TAGS[theme]}',
               "music": music}
        if any("!" in str(v) for v in tip.values()):
            raise SystemExit(f"post {n}: exclamation point")
        (ROOT / "tips" / f"post-{n}.json").write_text(json.dumps(tip, indent=2, ensure_ascii=False) + "\n")
        print(n, when.strftime("%a %b %d %H:%M"), tid, topic, music)


if __name__ == "__main__":
    main()
