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

## Words we use / avoid

| Use                         | Avoid                              |
|-----------------------------|------------------------------------|
| players, kids, your team    | athletes (for young kids), assets  |
| try, consider, notice       | must, never, always                |
| habit, approach, cue        | hack your way to, secret, trick    |
| There is no perfect answer. | The right way is...                |

## Card fields

Tips are stored as JSON in `tips/` and rendered with `render_card.py`.

| Field       | Purpose                                                       |
|-------------|---------------------------------------------------------------|
| `day`       | Day label in the top-right header (e.g. `FRIDAY`)             |
| `post`      | Post number                                                   |
| `title`     | Large heading (e.g. "Friday Quick Tip")                       |
| `subtitle`  | The idea in a few words                                       |
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
