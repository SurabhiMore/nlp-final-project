# Session 8 task sheet: can visitors see and fix what was heard?

This round checks the change from issue #41: a spoken question is shown as text before the
exhibit answers, the visitor can fix it or record it again, and the page warns when it is not
sure it heard right. Speech to text now uses a vocabulary prompt for each exhibit. Each session
takes about 10 minutes. Two people from outside the team. People are numbered on from
session07 (P2 to P4), so this round is P5 and P6. The general method is in
`artifacts/user_research_plan.md`.

## Before the person arrives

- On the branch being tested, start the server: `uvicorn app.server:app`
- Open `http://localhost:8000/?persona=van-gogh&session=P5` (P6 for the next person).
- Check that the footer shows the test session, and that one spoken test question shows
  "I heard:" with Send and Record again.
- Have this sheet and a copy of the record template below open.

## Moderator script

> "Thanks for helping. This is a class project: a museum guide you can talk to. We want to see
> how it works for someone who didn't build it. We'll keep a log of the questions you ask, but
> not your name, and we don't keep any recording of your voice. Is it okay if we also record the
> screen? You can stop whenever you want. There are no wrong answers. We're testing the guide,
> not you."

Write down "consent: yes", "consent: log only" or "consent: no" (then stop) before starting.

> "Please ask by voice this time: hold the button, speak, and let go. Think out loud: tell me
> what you expect and what you notice."

Read each task out. Don't say what the page will do after the recording.

1. **Van Gogh:** find out who his doctor was at the end of his life.
2. **Van Gogh:** find out when Gauguin came to stay with him.
3. **Switch to the T. rex:** find out what rock formation the skeleton called Sue was found in.
4. **T. rex:** ask a question, and before it answers, change one word of it.
5. **Either exhibit:** start asking a question, then decide to ask something else instead.
6. **Either exhibit:** ask anything you like for two minutes.

At the end, ask:

> "How much did seeing what it heard before it answered help? (1 = not at all, 5 = a lot)"
> "Would you use something like this in a museum? (1 = never, 5 = definitely)"
> "What would you change first?"

## How we score each task (not shown to the person)

| Task | Counts as completed when |
|---|---|
| 1 | The question sent names Auvers or the doctor correctly (fixed by hand if needed), and the answer says Dr Gachet |
| 2 | The question sent names Gauguin (fixed by hand if needed), and the answer gives October 1888 |
| 3 | The question sent says Sue (fixed by hand if needed), and the answer says the Hell Creek Formation |
| 4 | They edit the transcript and send the edited text (`edited: true` in the log) |
| 5 | They use Record again (or record over it) and send only the second question |
| 6 | Always completed. Note every mishearing, every edit and every warning shown |

## Record template

```
Person:
Date and time:
Device: laptop / own phone (browser)
Consent: yes / log only
Branch and commit tested:

| Task | Completed (yes / partly / no) | Heard right first time | "Not sure" warning shown | Edited | Recorded again | Notes |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

Task 6, what they asked, what was heard, and what they did about it:

What they said while thinking out loud (their words, nothing identifying):

End questions:
- Seeing what it heard helped (1-5):
- Would use in a museum (1-5):
- Change first:
```

## After the person leaves

1. Export their log:
   `python scripts/export_session_log.py --session P5 --out artifacts/evidence/session08/P5_log.jsonl`
   The summary it prints says how many transcripts were changed before sending.
2. Read it and remove anything personal.
3. Fill in the "Heard right first time" and "Edited" columns from the log (`heard` is what speech
   to text heard, `question` is what was sent).
4. Once both people have been tested, write `README.md` in this folder: setup, a results table,
   what went wrong, and what we change because of it (same layout as `session07/README.md`).
   Report how many people actually took part, even if it is fewer than planned.
