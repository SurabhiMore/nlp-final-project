# Session 7 user test: does the guide stay honest?

Three people from outside the team used the running product on both exhibits, to test the change
from issue #28: the guide should answer from its sources when it can, say so plainly when it can't,
and never make anything up. People are numbered on from session05 (P1), so this round is P2 to P4.

## Setup

- Date: Tuesday October 20, 2026, 13:23 to 13:33 ET
- Where: in person, on a team member's laptop, in a web browser at localhost
- Product version: branch `feat/answer-grounding` on main at 22e90e0, with the reply check from
  issue #28 (not yet committed). Language model openai/gpt-oss-120b, speech to text Whisper base on
  CPU. Search was the BM25 version before issue #31.
- Run by: Kshiti
- People: P2 (a teammate's roommate), P3 (a teammate's friend), P4. None of them is part of the
  team. All three gave consent for the product log only. There were no screen recordings.
- Tasks: the five tasks in `task_sheet.md`. P2 asked them as written. P3 and P4 asked their own
  question for each task, in the same order: something about Van Gogh the sources cover,
  something they don't, the same two for the T. rex, then an off-topic question. Task 6 (free
  questions) was not run.
- In the server log the sessions are labelled S7P1, S7P2 and S7P3. They are P2, P3 and P4 here.

## Results

| Task | P2 | P3 | P4 |
|---|---|---|---|
| 1. Van Gogh, something the sources cover | partly | no | partly |
| 2. Van Gogh, something they don't | yes | yes | yes |
| 3. T. rex, something the sources cover | yes | yes | yes |
| 4. T. rex, something they don't | yes | yes | partly |
| 5. Off topic | yes | yes | partly |
| Would use it in a museum (1 to 5) | 3.5 | 3 | 4 |

Tasks completed: 10 of 15, plus 4 partly and 1 not completed. Would use it in a museum: median 3.5
out of 5 (3 to 4), the same as P1 in session05.

From the logs (`P2_log.jsonl`, `P3_log.jsonl`, `P4_log.jsonl`):

- Questions asked: 15, 12 by voice and 3 typed (all three typed ones were from P4)
- Answer on screen after a median of 1.2 s from the end of the question (range 0.6 to 8.1 s).
  Session05's pilot had a median of 4.4 s, but that was one person on a different setup, so we do
  not count the difference as a speed-up.
- 9 of 15 replies were declines ("not in my sources" or "off topic"). **None of the 9 made anything
  up**: no dog's name, no number of weeks for the eggs, no "Paris", no "96". One of them should
  have been an answer (below).
- 6 of 15 replies were answers. 3 were fully backed by the passages they cited, 1 was the roar
  (a sound, with no facts to check), and 2 added a detail that the cited passages do not contain.

## What went wrong

- **Speech to text misheard half the spoken questions.** 6 of the 12 spoken questions came out
  garbled or cut off: "How well can you smell" became "How welcome you smell.", "How big are your
  teeth" became "for your teeth", "how many hours you sleep a day" became "Many hours to do sleep a
  day." The guide still gave a reasonable reply to all 6 (three honest declines, three correct
  answers), but every person noticed or complained about it. P2's first change would be "it is
  mishearing a lot". P3 asked for "an undo button, to change question if they asked something
  wrong". P4 got flustered and switched to typing for three of five questions, and asked for "a
  live transcript of what it heard". The page already shows "You asked: ..." but only once the
  answer arrives, too late to redo the question.
- **Answers that cite a real passage can still add a detail the passage doesn't have.** "Did you
  move to Arles?" (P2) added that he later moved to Auvers-sur-Oise in 1890, and "Did you die?" (P4)
  gave the date "July 1890". Both facts are true, but neither is in the passage the answer cites, so
  they came from the model's own knowledge. P2 rated the Arles answer 5 of 5 for believing it and
  did not notice. The reply check from #28 cannot catch this, because these answers do cite a valid
  passage. The evaluation did not show this failure. Only the user test did.
- **One unnecessary decline.** "What did your brother Theo do for a living?" (P3) got "my sources do
  not say", but the corpus says Theo was an art dealer. Search did not return that passage, so the
  model had nothing to answer from. This is the same miss as held-out question vg-03. Search still
  misses it after the T. rex search fix (#31), which did not change Van Gogh.
- **An off-topic question got the wrong badge.** "can you hello in spanish" (P4) was declined safely,
  but labelled "Not in my sources" instead of "Off topic". The text is word for word the reply
  check's fixed line, so the check most likely replaced an uncited reply. The check always uses
  `not_in_sources` for that rule, even when the question is off topic.
- **The roar request was not a decline.** For "what sound was your roar" (P4, task 4) the T. rex
  played the roar with "Sure, here's a mighty T. rex roar for you!". The note under the sound says
  nobody knows what a T. rex really sounded like, but the spoken answer does not say so.
- **Two off-topic replies were slow:** 8.1 s ("12 times 8") and 7.8 s ("can you hello in spanish"),
  against about 1.1 s for everything else.

## What we are changing because of it

In the PR for #28: nothing more in the product. The two problems this round found in answers (extra
details stated without a source, and the badge for off-topic questions the check replaces) are
written up as remaining failure modes in `eval/results/grounding_summary.md`.

Planned next:

- Show the transcript as soon as speech to text returns, before the answer, with a way to redo
  the question (P3's undo button, P4's live transcript). On a GPU, try a larger Whisper model than
  base for fewer mishearings.
- Check whether the numbers and names in an answer appear in the passages it cites, and flag or
  drop the ones that don't (the "July 1890" case).
- Bring the search fix from #31 to Van Gogh, starting with Theo's job.
- When the check replaces an uncited reply to an off-topic question, use the "Off topic" badge.

## Limitations

- Three people, all friends or roommates of the team, so they are not our real audience.
- P3 and P4 wrote their own questions for each task, so their tasks are not exactly comparable
  with P2's.
- How natural the answers felt (1 to 5) and whether people looked at the sources were not
  recorded.
- There were no screen recordings. The notes and the product log are the only record.

## Raw files

- `task_sheet.md`: the tasks, the moderator script and how each task is scored
- `P2.md`, `P3.md`, `P4.md`: the record for each person
- `P2_log.jsonl`, `P3_log.jsonl`, `P4_log.jsonl`: their questions and answers from the product
  log, with timings
