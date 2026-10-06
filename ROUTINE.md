# Monthly Posting Routine

Runs automatically on the **1st of each month** (a Claude Code Routine) and
builds the **following month**: on November 1 it builds December, on
December 1 it builds January, and so on. That keeps about a month of posts
lined up at all times.

Two reels a day, at **10:00 AM and 5:00 PM** `America/New_York`, on Facebook
and Instagram together. Each run **schedules its posts to go live** in
Metricool (the owner chose this on Oct 6, 2026). The owner can still review,
edit, or delete any post in Metricool before it goes out.

**Golden rule:** if any step fails (a reel will not render, a media link does
not load, git push is rejected, Metricool returns an error), **stop and report**
what failed and what has been done so far. Do not guess, retry with changed
content, or skip ahead.

## Fixed settings

| Setting         | Value                                                              |
|-----------------|--------------------------------------------------------------------|
| Branch          | `main`                                                             |
| Metricool brand | `7103553` (yourpracticehacks.com)                                  |
| Networks        | Facebook and Instagram, together in one post, as a Reel on both    |
| Post times      | 10:00 and 17:00 `America/New_York`, every day                      |
| Media URLs      | `https://raw.githubusercontent.com/yourpracticehacks-oss/Practice-hacks-posts/<commit SHA>/reels/post-NN.mp4` and `post-NN-cover.png` |

## Tools

| Tool                          | What it does                                                    |
|-------------------------------|-----------------------------------------------------------------|
| `tools/gen_tips.py`           | Turns a batch of written tips into `tips/post-NN.json` files, each with its time slot, day label, music, credit, and caption |
| `tools/render_range.sh A B`   | Renders reels, covers, and cards for posts A..B, three at a time |
| `tools/qa_reels.py A B out.png` | Checks length and audio level, and builds a contact sheet to look at |
| `tools/metricool_payloads.py A B SHA` | Prints the `createScheduledPost` request for each post, media pinned to the commit |

## Steps

### 1. Get up to date

```sh
git checkout main && git pull origin main
pip install -r requirements.txt
```

### 2. Work out the month

The target month is the month **after** the current one. Find the last post
number (the highest `tips/post-NN.json`); new posts continue from there.

Some or all of the month may already be written. Check how many open slots
remain:

```sh
python3 -c "import sys; sys.path.insert(0, 'tools'); import gen_tips as g; print(len(g.free_slots(2027, 1)))"
```

If it prints `0`, every tip for the month already exists. Skip to step 5 and
render, ship, and schedule the posts whose `publish` dates fall in the month.

### 3. Topics

Count unused topics:

```sh
python3 -c "import sys; sys.path.insert(0, 'tools'); import gen_tips as g; print(len(g.unused_topics()))"
```

If there are fewer unused topics than open slots, add new topics to the
bottom of `topics.md` first. Continue the IDs (T173, T174, ...), keep the six
themes rotating in order (Keeping kids engaged, Communication, Handling
parents, Game-day decisions, Building confidence, Practice habits), and do not
repeat a topic already in the table. Think about the season: winter sports,
holidays, and the start and end of seasons.

### 4. Write the tips

Read `voice.md` first. Write a batch file (a JSON list) with one entry per
open slot, in order, using the next unused topics in order. Each entry has:
`topic` (exactly as in `topics.md`), `subtitle`, `hook`, `intro` (two short
lines), `statement`, `q1` (ends with ` —`), `q2`, `q3`, `t1`, `t2`, `cta`
(starts with `Coaches — `), `ctaLines` (two lines), `ctaPrompt`, and `choice`
(the either/or in a few words, used in the caption).

Rules: no exclamation points, no emojis, no hype. The `hook` is the first
frame of the reel and the cover headline. Keep it under about 12 words and
follow the hook rules in `voice.md`. Vary the openers of `t1`; do not start
every one with "There is no perfect answer."

Then generate the tip files:

```sh
python3 tools/gen_tips.py batch.json <first post number> <YYYY-MM>
```

It assigns time slots, the day label, music, the music credit, and the
caption (hook, moment, idea, the either/or, the comment invitation, credit,
hashtags).

### 5. Render and check

```sh
tools/render_range.sh <first> <last>
python3 tools/qa_reels.py <first> <last> /tmp/sheet.png
```

Every reel must be 20-34 seconds with audible music (anything flagged
`CHECK` needs a look). Open the contact sheet and look at it: no cut-off
lines, no stranded words, and the hook fully visible on the first frame.

### 6. Commit, push, and verify links

Commit `tips/`, `reels/`, `cards/`, and `topics.md`, then push to `main`.
Check every video and cover link at the pushed commit returns `200` and the
same size as the local file. If any fails after five minutes, stop and report.

### 7. Save to Metricool

Call `getScheduledPosts` for the month first. If a slot already has a post,
skip that slot and report it.

Print the requests and send each one with `createScheduledPost`:

```sh
python3 tools/metricool_payloads.py <first> <last> <commit SHA>
```

Send each request as printed (`"draft": false`, scheduled to go live).
Check each response lists both networks and points `media` at a Metricool copy of the video.
Record each `plannerUrl`. If any call errors, stop and report.

### 8. Update the log

Add one row per post to `posted.md`: post number, date and time, topic ID,
topic, status (`scheduled`), reel link (the `main` URL), and Metricool link.
Commit and push.

Also check last month's drafts with `getScheduledPosts`: any that are now
scheduled (`"draft": false`) move from `draft` to `scheduled` in `posted.md`.

### 9. Summary

End with: the month built, how many posts, the first and last dates, any new
topics added, and anything skipped or flagged.
