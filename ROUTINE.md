# Monthly Posting Routine

Run once a month, before the month starts. It writes, renders, and schedules
one Friday tip for every Friday in the **next calendar month**. Each tip goes
out as a **reel** (a 9:16 video with a cover image). See the Reels section of
`voice.md`.

**Golden rule:** if any step fails (a reel will not render, a media link does
not load, git push is rejected, Metricool returns an error), **stop and report**
what failed and what has been done so far. Do not guess, retry with changed
content, or skip ahead.

## Fixed settings

| Setting         | Value                                                                 |
|-----------------|-----------------------------------------------------------------------|
| Branch          | `main`                                                                |
| Metricool brand | `7103553` (yourpracticehacks.com)                                     |
| Networks        | Facebook and Instagram, together in one post, as a Reel on both       |
| Post time       | 10:00 AM `America/New_York` on each Friday                            |
| Video URL       | `https://raw.githubusercontent.com/yourpracticehacks-oss/Practice-hacks-posts/main/reels/post-NN.mp4` |
| Cover URL       | `https://raw.githubusercontent.com/yourpracticehacks-oss/Practice-hacks-posts/main/reels/post-NN-cover.png` |

## Steps

### 1. Get up to date

```sh
git checkout main && git pull origin main
pip install -r requirements.txt
```

### 2. Find the Fridays

List every Friday in the next calendar month (for example, a run in late
October covers every Friday in November). Get the UTC offset for 10:00 AM
New York time on each date. Daylight saving time changes in March and
November, so do not assume the offset:

```sh
python3 -c "
import calendar, datetime as d; from zoneinfo import ZoneInfo
y, m = 2026, 11   # the NEXT calendar month
for day in range(1, calendar.monthrange(y, m)[1] + 1):
    t = d.datetime(y, m, day, 10, tzinfo=ZoneInfo('America/New_York'))
    if t.weekday() == 4: print(t.isoformat())"
```

Skip any Friday already in `posted.md`, so a run can be repeated safely.

### 3. Pick topics and post numbers

- Post numbers continue from the last row of `posted.md` (+1 per Friday, in
  date order).
- For each Friday, take the next topic from `topics.md`, top to bottom, whose
  ID is not in `posted.md`.
- If the backlog runs out, stop and report. Do not invent topics.

### 4. Write each tip

Read `voice.md` first. Create `tips/post-NN.json` using `tips/post-20.json` as
the template. Set `"day": "Friday"` and `"post": NN`, and fill every field
following the anatomy in `voice.md`: a hook, a real moment, one clear idea,
an honest either/or question, a gentle takeaway, an invitation to comment. No
exclamation points, no emojis, no hype. The `hook` matters most: it is the
first frame of the reel and the cover headline. Write three, keep the one a
coach would stop scrolling for, and follow the hook rules in `voice.md`. Keep `q1`, `q2`, `t1`, `t2` short
enough to sit on one line each (about 55 characters).

Add these fields to the same JSON:

- `"topicId"`: the topic ID, e.g. `"T01"`.
- `"caption"`: the social caption, written as:
  - The first line is the hook, or a close variant of it. It is all most
    people see before "more."
  - 3-5 short lines in total that restate the idea in the voice of `voice.md` and ask
    coaches to share their habit in the comments. Each line is its own
    sentence or short pair of sentences, separated by `\n`.
  - A blank line, then 5-8 hashtags on one line. Always include
    `#YouthSports` and `#YouthCoach`. Add others that fit the topic, such as
    `#VolunteerCoach`, `#CoachingTips`, `#YouthSoccer`, `#LittleLeague`,
    `#YouthBasketball`, `#PracticePlanning`, `#SportsParents`.
  - No emojis, no exclamation points.

### 5. Render and check the reels

```sh
python render_reel.py tips/post-NN.json   # reels/post-NN.mp4 and reels/post-NN-cover.png
python render_card.py tips/post-NN.json   # cards/post-NN.png, kept as a still version
```

Music comes from `music/`, rotating by post number (see `music/README.md`).
The renderer prints which track it used and the credit line for it. Add
that credit to the caption exactly as printed, on its own lines after the
caption text and above the hashtags. Also set `"music": "<file name>"` in the tip
JSON so the reel always re-renders with the same track. If `music/` has no tracks, the reel is
silent; say so in the summary.

Check each reel: it should be 20-32 seconds long. Pull a few frames and look
at them, including the very first frame (the hook must be fully visible) and
the last scene:

```sh
ffmpeg -v error -i reels/post-NN.mp4 -vf "fps=1/2,scale=270:-1,tile=8x2" -frames:v 1 /tmp/sheet.png
```

Check that no line is cut off and no word is stranded. Look at the cover and
the card too. If the card renderer prints a shrink note below about 90%,
shorten the text and render again.

### 6. Commit, push, and verify the media links

```sh
git add tips/ reels/ cards/
git commit -m "Add Friday tips for <Month YYYY> (posts NN-MM)"
git push -u origin main
```

Then check every video and cover link returns `200`. Covers return
`image/png`. Videos return `application/octet-stream`; that is how GitHub
serves MP4 files, and Metricool accepts it (confirmed with post 22).

```sh
for f in post-NN.mp4 post-NN-cover.png; do
  curl -sS -o /dev/null -w "$f %{http_code} %{content_type}\n" \
    https://raw.githubusercontent.com/yourpracticehacks-oss/Practice-hacks-posts/main/reels/$f
done
```

A new file can take a minute or two to appear on raw.githubusercontent.com.
Wait and check again, up to 5 minutes. If any link still fails, stop and report.

### 7. Schedule in Metricool

First, call `getScheduledPosts` for brand `7103553` over the month's dates in
`America/New_York`. If a post already exists for a Friday, do not create a
second one. Report it instead.

Then, for each Friday, call `createScheduledPost` once with:

- `blogId`: `7103553`
- `date`: the Friday at 10:00 with its offset, e.g. `2026-11-06T10:00:00-05:00`
- `info`:

```json
{
  "autoPublish": true,
  "draft": false,
  "descendants": [],
  "firstCommentText": "",
  "hasNotReadNotes": false,
  "media": ["<video URL for post-NN.mp4>"],
  "videoThumbnailUrl": "<cover URL for post-NN-cover.png>",
  "mediaAltText": ["<one sentence: the hook and the statement>"],
  "providers": [{"network": "facebook"}, {"network": "instagram"}],
  "publicationDate": {"dateTime": "2026-11-06T10:00:00", "timezone": "America/New_York"},
  "shortener": false,
  "smartLinkData": {"ids": []},
  "text": "<caption from the tip JSON>",
  "facebookData": {"type": "REEL"},
  "instagramData": {"type": "REEL", "showReelOnFeed": true}
}
```

Check that the response lists both networks and that `media` points at a
Metricool copy of the video. Record the `plannerUrl` from each response. If any call returns an error,
stop and report. Do not retry with altered text or settings.

### 8. Update the log

Add one row per post to `posted.md`: post number, date, topic ID, topic,
status (`scheduled`), reel link, and Metricool planner link. Then:

```sh
git add posted.md
git commit -m "Log Friday tips for <Month YYYY>"
git push -u origin main
```

### 9. Summary

End with a table: date, post number, topic, hook, reel link, Metricool link.
List anything that needs a person to look at it.

## Test runs

To test without publishing, set `"draft": true` in step 7 and log the status
as `draft`. A draft is not published until someone schedules it in the
Metricool app.
