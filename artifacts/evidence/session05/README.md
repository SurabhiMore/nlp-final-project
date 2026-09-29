# Session 5 user test

A first, small pilot: one person from outside the team used the running product on both exhibits.
The full round of tests (three or more people, all six tasks from `task_sheet.md`) is planned for
next week, before the October 6 presentation.

## Setup

- Date: Tuesday September 29, 2026, 12:14 to 12:16 ET
- Where: in person, on a team member's laptop, in a web browser at localhost
- Product version: `main` at commit 61a10ae plus the answer engine from PR #20 (commit 78a3955);
  language model openai/gpt-oss-120b, speech to text Whisper base
- Run by: Pratham
- Person: P1, a student who is not part of the team. Consent given before starting.

## Results

| Task | Completed | Time from question to answer (from the log) | Questions asked |
|---|---|---|---|
| 1. Van Gogh, the feeling of The Bedroom | yes | 3.2 s | 1 |
| 5. T. rex, ever met a human | yes | 4.7 s | 1 |

Tasks 2, 3, 4 and 6 were not run in this pilot. Tasks completed: 2 of 2. The tasks were not timed
with a stopwatch, so the times above are from the product log, not the full time for the task.

Other numbers from the log (`P1_log.jsonl`):

- Questions asked: 4, all by voice (3 to Van Gogh, 1 to the T. rex)
- Answer on screen after a median of 4.4 s from the end of the question (range 3.2 to 4.7 s)
- Would use it in a museum: 3.5 out of 5

## What went wrong

- One question was cut off: the button was let go too early, the page only received "What was...",
  and the guide said its sources did not cover it. Holding a button while speaking is easy to get
  wrong.
- P1 found the response a little slow. The voice starts later than the text, because speech is
  generated on a laptop CPU.
- No wrong answers: both task answers match their cited sources (the Bedroom answer quotes the
  letter where Van Gogh says the picture should be restful).

## What P1 asked in their own words

- "What was your inspiration behind your paintings?", answered with two sources.

## What we are changing because of it

Nothing is changed in the product yet. Planned for next week, from this session:

- Let visitors tap once to start and once to stop recording, instead of holding the button, so a
  question is not cut off.
- Speed up the voice by running speech generation on a GPU once the product is deployed.

## Raw files

- `P1.md`: the record from the session
- `P1_log.jsonl`: P1's questions and answers from the product log, with timings
- `task_sheet.md`: the tasks and how each one is scored
