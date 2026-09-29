# Session x task sheet

Will be used for the first round of tests on the running product in Session 6. Each
session takes about 15 minutes. The plan behind it is in `artifacts/user_research_plan.md`.

## Before the person arrives

- Start the server on the laptop: `uvicorn app.server:app`
- Open `http://localhost:8000/?persona=van-gogh&session=P1` (use P2, P3 for the next people).
  To use their own phone, open an https tunnel first (see the research plan) and send them the
  tunnel link with the same `?persona=van-gogh&session=P1` ending.
- Check that the footer shows "Test session P1" and that one test question gets a spoken answer.
- Start the screen recording only after the person agrees.

## What we say first (consent)

"This is a class project. We built a museum guide you can talk to, and we want to see how it
works for someone who didn't build it. Is it okay if we record your screen and voice while you
try it? We won't use your name, and you can stop whenever you want. There are no wrong answers;
we're testing the product, not you."

Write down "consent: yes" or "consent: log only" in the person's record before starting.

## Tasks (read these out, or show them on paper)

The exhibit menu at the top of the page switches between Van Gogh and the T. rex. You can hold
the button and speak, or type.

1. Find out what feeling Van Gogh wanted his painting *The Bedroom* to give.
2. Ask Van Gogh about something that happened after 1890.
3. Get Van Gogh to tell you something he wrote in one of his letters.
4. Switch to the T. rex. Find out how heavy a T. rex could get.
5. Ask the T. rex whether it ever met a human.
6. Ask either exhibit anything you like for two minutes.

## How we score each task (not shown to the person)

| Task | Counts as completed when |
|---|---|
| 1 | The answer is about rest or calm, and a source is listed under it |
| 2 | It says this is after its time, without making anything up |
| 3 | It gives something from his letters, and a letters source is listed |
| 4 | The answer gives a weight (about 8 to 9 tonnes), and a source is listed |
| 5 | It says it never met a human because humans came much later, and stays in character |
| 6 | Always completed; we note what they asked about |

Mark a task "partly" if they got there only with a hint from us. Stop a task after 2 minutes
and mark it "no". Time runs from when they start the task until they say they have the answer
or give up.

## What we write down for each person

Copy this into `P1.md`, `P2.md` and `P3.md`, and fill it in during the session.

```
Person: P1
Date and time:
Device: laptop / own phone (which browser)
Consent: yes / log only
Asked by voice, typing, or both:

| Task | Completed (yes / partly / no) | Time (s) | Questions asked | Wrong answer they noticed | Wrong answer we noticed | Natural (1 to 5) |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

Misheard questions (what they said, what the page showed):

Anything that confused them or that they commented on while using it:

After the tasks:
- Would you use something like this in a museum? (1 = never, 5 = definitely):
- What was the most annoying part?
- What would you change first?
```

## After the person leaves

1. Stop the recording. Delete the raw audio once the notes are written up.
2. Export their log:
   `python scripts/export_session_log.py --session P1 --out artifacts/evidence/session06/P1_log.jsonl`
3. Read the exported log and remove anything personal.
4. Check each answer in the log against its sources and fill in "Wrong answer we noticed".
