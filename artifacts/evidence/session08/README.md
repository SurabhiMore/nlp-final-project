# Session 8 user test: can visitors see and fix what was heard?

Two people from outside the team used the running product to test the change from issue #41: a
spoken question is shown as text before the exhibit answers, the visitor can fix it or record it
again, and the page warns when it is not sure it heard right. Speech to text now runs Whisper small
with a vocabulary prompt for each exhibit. People are numbered on from session07 (P2 to P4), so this
round is P5 and P6.

## Setup

- Date: Monday October 26, 2026, 16:08 to 16:17 ET
- Where: on a laptop, in a web browser at localhost
- Product version: branch `feat/stt-transcript` at 40667c7. Language model openai/gpt-oss-120b,
  speech to text Whisper small on CPU with the exhibit's vocabulary prompt, low-confidence
  threshold -0.35.
- Run by: Kshiti
- People: P5 (a teammate's neighbour) and P6 (a teammate's friend). Neither is part of the team.
  Both gave consent for the product log only. There were no screen recordings.
- Tasks: the six in `task_sheet.md`, given as goals, so each person asked in their own words. Both
  asked by voice only. P6 skipped task 5 by mistake.
- In the server log the sessions are labelled P5 and P6.

## Results

| Task | P5 | P6 |
|---|---|---|
| 1. Van Gogh: his doctor at the end of his life | yes | yes |
| 2. Van Gogh: when Gauguin came to stay | yes | yes |
| 3. T. rex: the rock formation Sue was found in | yes | yes |
| 4. T. rex: change one word before it answers | no | yes |
| 5. Switch to a different question | no | not done |
| 6. Free questions | yes | yes |
| Seeing what it heard helped (1 to 5) | 4.5 | 4.5 |
| Would use it in a museum (1 to 5) | 4 | 5 |

Tasks completed: 9 of the 11 that were run. Seeing what it heard helped: 4.5 out of 5 for both.
Would use it in a museum: 4 and 5, against a median of 3.5 in session07. That is two different
people on a different version, so we do not count it as an improvement.

From the logs (`P5_log.jsonl`, `P6_log.jsonl`) and the records:

- Questions sent: 11, all spoken, all through the new transcript step.
- **4 of the 11 transcripts were misheard.** The "not sure" warning appeared on 3 of those 4 and on
  none of the 7 that were heard right. The one misheard question without a warning (P5, task 2)
  still had both names right, "Paul Gauguin" and "Arles", and got the right answer.
- **P6 fixed 2 misheard transcripts before sending them,** both with the warning showing.
  "The T-Rex 8." became "what did T-Rex weigh" and got a cited answer; sent as heard, it could not
  have been answered. P5 fixed none.
- Tasks 1 to 3, which depend on names (Gachet, Gauguin, Sue, Hell Creek), were answered correctly
  and with sources by both people, 6 of 6.
- Speech to text took a median of 1.3 s per question (1.1 to 2.9 s). In session07, with Whisper
  base and no prompt, it was 0.45 s. This is the cost of the small model; see
  `eval/results/stt_results.md`.
- The answer came a median of 0.7 s after the question was sent, except once (below).

## What went wrong

- **P5 saw the edit box but corrected themselves out loud instead.** For task 4 they changed the
  question while speaking: the page sent "How long was the T-Rex's tail? Actually, how long was the
  T-Rex's skull?" Task 5 went the same way: "Go paint Starry Night while he was... wait. Actually,
  how many paintings did he sell during his lifetime?" Both were sent with the false start
  included. Speaking a correction seems more natural to some people than editing text, even when
  they know they can.
- **Nobody used Record again.** P5 switched questions out loud and P6 skipped task 5, so this round
  did not test it.
- **One answer added a detail that is not in its source.** P6's weight answer gave the adult and
  juvenile weights from the cited passage, then added that hatchlings weighed "just a few
  kilograms", which the passage does not say. This is the same failure session07 found.
- **One unnecessary decline.** For P5's tail-and-skull question the T. rex said its sources give no
  measurement for either, but they give the largest skulls as up to 1.52 m (held-out question
  tr-h03). This is a search or answering miss, not speech to text: the question was heard right.
- **Two broad questions were handled differently.** "Tell me everything interesting about this
  exhibit" (P5, Van Gogh) was declined, while "Give me a deep dive into the history of this
  display" (P6, T. rex) got a full answer, with every detail in its sources.
- **One slow answer:** P5's first question took 21 s, almost all of it waiting for the language
  model. Every other answer took 1.2 s or less once the question was sent.

What they said:

- P5 liked that the page warned when it was not sure. Their first change would be for it to
  understand names even when they are mispronounced: "sometimes we don't know how to pronounce
  these names e.g 'Gauguin', is there a way where it could understand even if we pronounce it
  wrongly?"
- P6 liked being able to fix a misheard sentence before sending it, instead of waiting for a wrong
  answer and asking again. No change suggested.

## What we are changing because of it

In the PR for #41: nothing more in the product. The vocabulary prompt already helps with P5's
point: for both people "Gauguin" came out right, even where the rest of the sentence did not.

Planned next:

- Handle spoken corrections, such as keeping only what comes after "actually" or "wait", so a
  visitor who corrects themselves out loud still sends a clean question. P5 knew about the edit box
  and still corrected out loud, so a clearer edit box alone would not fix this.
- Test Record again in the next round, since nobody used it in this one.
- For mispronounced names, try matching words in the transcript to the closest name in the
  exhibit's vocabulary.
- Log whether the "not sure" warning was shown with every question, so the next round does not
  rely on the moderator's notes for it.

## Limitations

- Two people, both friends or neighbours of the team, so they are not our real audience.
- P6 skipped task 5, so 11 tasks were run, not 12.
- Whether the warning was shown, and whether a transcript was heard right, come from the
  moderator's notes and the transcripts, not from the log.
- There were no screen recordings. The notes and the product log are the only record.

## Raw files

- `task_sheet.md`: the tasks, the moderator script and how each task is scored
- `P5.md`, `P6.md`: the record for each person
- `P5_log.jsonl`, `P6_log.jsonl`: their questions and answers from the product log, with what
  speech to text heard, whether it was edited, and timings
