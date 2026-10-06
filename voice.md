# Your Practice Hacks — Voice Guide

**Tagline:** Your Team. Your Kids. Your Practice.

Your Practice Hacks shares short, useful tips for youth sports coaches. Most of
our readers are volunteers. They coach after work, on weekends, often for their
own kid's team. Every post should respect their time and their judgment.

## Tone

- **Calm.** We are a steady voice on a noisy sideline. Nothing is urgent.
- **Plain.** Everyday words. No jargon, no buzzwords, no "game-changers."
- **Thoughtful.** We raise a real question and leave room for the coach to think.
- **Respectful.** Volunteer coaches are doing their best. We never scold, shame,
  or talk down. We do not assume there is one correct way to coach.

## Style rules

- Short sentences. One idea per sentence.
- No hype. No "amazing," "insane," "must-try," or "you won't believe."
- No exclamation points.
- No emojis on cards. (A caption may use one sparingly, but default to none.)
- Address coaches directly as "you" or "coaches."
- Prefer concrete moments over general advice.

## Anatomy of a tip

Every tip follows the same shape:

1. **A real moment.** Name a specific practice or game situation a coach will
   recognize. *"The field gets noisy. You repeat the same instruction louder
   and louder."*
2. **One clear idea.** State it in a single sentence. *"Volume does not
   guarantee attention."*
3. **An honest either/or question.** Offer two reasonable approaches. There is
   no single right answer, and we say so. *"Do you call the player's name and
   wait for eye contact — or coach the moment before it disappears?"*
4. **A gentle takeaway.** Acknowledge the tradeoff and leave the coach with one
   thing to keep in mind.
5. **An invitation.** Ask coaches to share their own habit in the comments.
   Remind them there are no wrong answers.

## Reels

Reels are the main format. Each Friday tip becomes a 25-30 second vertical
video, built from the same tip JSON. The voice does not change. A reel draws
people in by being specific and useful, not by being loud.

- **The first second decides.** The `hook` is on screen from frame 0, in large
  type. It points a coach at something they can picture or check at their own
  practice: *"At your next practice, count the kids standing in line."*
- **Good hooks** name a moment, ask a question a coach has already asked
  themselves, or give a small thing to notice. Keep them under about 12 words.
- **Not hooks:** "You're doing this wrong," "Stop doing X," "Nobody talks about
  this," countdowns, shock, or anything that shames a volunteer.
- **One idea per screen.** The reel moves through five scenes: the moment, the
  idea, your call (the either/or), the takeaway, your turn (the comment
  prompt). Each scene holds just long enough to read.
- **End on the question.** The last scene asks for a comment and stays up
  longest, so it is on screen when the reel loops.

## Words we use / avoid

| Use                         | Avoid                              |
|-----------------------------|------------------------------------|
| players, kids, your team    | athletes (for young kids), assets  |
| try, consider, notice       | must, never, always                |
| habit, approach, cue        | hack your way to, secret, trick    |
| There is no perfect answer. | The right way is...                |

## Tip fields

Tips are stored as JSON in `tips/`. `render_reel.py` turns a tip into a reel
and its cover; `render_card.py` turns it into a 4:5 image card.

| Field       | Purpose                                                       |
|-------------|---------------------------------------------------------------|
| `day`       | Day label in the top-right header (e.g. `FRIDAY`)             |
| `post`      | Post number                                                   |
| `title`     | Large heading (e.g. "Friday Quick Tip")                       |
| `subtitle`  | The idea in a few words                                       |
| `hook`      | Reel opener and cover headline, under about 12 words          |
| `intro`     | 1-2 lines naming the real moment                              |
| `statement` | The one clear idea                                            |
| `q1`        | First half of the either/or question                          |
| `q2`        | Second half of the either/or question                         |
| `q3`        | A follow-up reflection question                               |
| `t1`        | Lead-in to the takeaway                                       |
| `t2`        | The takeaway                                                  |
| `cta`       | Question for coaches                                          |
| `ctaLines`  | 1-2 lines sketching possible answers                          |
| `ctaPrompt` | Closing invitation to comment                                 |
| `topicId`   | Topic ID from `topics.md`                                     |
| `caption`   | Social caption (see `ROUTINE.md`)                             |
