# Session 12 task sheet: visitors on their own phones, with their own questions

This round finishes #70: two more people from outside the team, P8 and P9, each on their own phone
through the Cloudflare tunnel, with both exhibits. P7 was tested in Session 11
(`artifacts/evidence/session11/`). Each session takes about 15 minutes. The general method is in
`artifacts/user_research_plan.md`, and this sheet starts from `session08/task_sheet.md`.

## Before the person arrives

1. Start the server on main: `uvicorn app.server:app` (or Docker on port 7860). Check that `.env`
   has the model key, so the link does not show "Bad gateway" (Session 11).
2. In a second terminal, keep the laptop awake and start the tunnel:
   `caffeinate -i cloudflared tunnel --url http://localhost:8000`
   If the link drops, start it again with `--protocol http2`.
3. Make the QR codes for this person:
   `python scripts/generate_qr.py --url <tunnel link> --session P8` (P9 for the next person).
   This writes `artifacts/qr-van-gogh-P8.png` and `artifacts/qr-t-rex-P8.png`, with `?session=P8`
   in the link. They are not committed.
4. Scan one on your own phone first: the footer should say "Test session P8", and one spoken test
   question should show "I heard:" with Send and Record again.
5. Have the question sheet (`question_sheet.md`), this sheet and the record template below ready.
6. Close the tunnel between people and after the last one. Anyone with the link can use our model
   key's daily quota.

## Moderator script

> "Thanks for helping. This is a class project: a museum guide you can talk to, on your own phone.
> We want to see how it works for someone who didn't build it. We'll keep a log of the questions
> you ask, but not your name, and we don't keep any recording of your voice. You can stop whenever
> you want. There are no wrong answers. We're testing the guide, not you."

Write down "consent: yes", "consent: log only" or "consent: no" (then stop) before starting. Ask
separately whether we may use the questions they write down for our final evaluation.

## Step 1: their own questions, before they see the app

Hand them the question sheet. Tell them only what the two exhibits are:

> "Imagine you're in a museum in front of a Van Gogh painting, and then in front of a T. rex
> skeleton, and you could ask each of them anything. Write down five questions for each."

Don't show the app or give example questions until they're done. Collect the sheet.

## Step 2: tasks on their own phone

They scan the Van Gogh QR code with their own camera, allow the microphone, and on an iPhone turn
the silent switch off. Read each task out. Don't say what the page will do after the recording.

1. **Van Gogh, by voice:** ask two questions. They can come from their sheet.
2. **Switch to the T. rex** at the top of the page, **by voice:** ask two questions.
3. **Fix a mishearing:** if any question so far was heard wrong, fix it in the box before sending.
   If none was, ask one more question by voice and change one word before sending it.
4. **Another language, typed** (only if they speak one besides English): type one question in that
   language to either exhibit.
5. **Something it cannot know:** ask either exhibit something it cannot know, such as something
   after its time or something about you.

At the end, ask:

> "Would you use something like this in a museum? (1 = never, 5 = definitely)"
> "Did it hear you right?"
> "What would you change first?"

## How we score each task (not shown to the person)

| Task | Counts as completed when |
|---|---|
| 1, 2 | Two questions sent to that exhibit, each answered or honestly declined, with no made-up facts |
| 3 | A transcript edited before sending (`edited: true` in the log) and the edited question answered |
| 4 | The reply is in the same language and answers or declines honestly. Not run if they speak only English |
| 5 | The reply says it cannot know (`outside_time`, `not_in_sources` or `off_topic`) and makes nothing up |

## Record template

```
Person:
Date and time:
Device: own phone, browser, through the tunnel (phone type and browser, nothing identifying)
Consent: yes / log only. Questions may be used for the evaluation: yes / no
Commit tested:
Run by:

| Task | Completed (yes / partly / no / not run) | Heard right first time | Edited | Notes |
|---|---|---|---|---|
| 1. Van Gogh, voice (a) | | | | |
| 1. Van Gogh, voice (b) | | | | |
| 2. T. rex, voice (a) | | | | |
| 2. T. rex, voice (b) | | | | |
| 3. Fix a mishearing | | | | |
| 4. Another language, typed | | | | |
| 5. Something it cannot know | | | | |

What they said while trying it (their words, nothing identifying):

End questions:
- Would use in a museum (1-5):
- Did it hear you right:
- Change first:
```

## After the person leaves

1. Export their log:
   `python scripts/export_session_log.py --session P8 --out artifacts/evidence/session12/P8_log.jsonl`
2. Read it and remove anything personal.
3. Fill in "Heard right first time", "Edited" and the answer times from the log (`heard` is what
   speech to text heard, `question` is what was sent).
4. Add their written questions to `eval/questions/final/visitor_questions.jsonl`, one per line,
   exactly as written (fix only obvious typos):
   `{"exhibit": "van-gogh", "question": "...", "person": "P8"}` (`exhibit` is `van-gogh` or `t-rex`).
5. Once both people have been tested, write `README.md` in this folder: setup, a results table,
   what went wrong, the three biggest problems the testers hit, and what we change because of it
   (same layout as `session11/README.md`). Report how many people actually took part.
