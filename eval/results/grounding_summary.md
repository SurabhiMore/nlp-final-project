# Answer grounding: what we changed and what still fails (issue #28)

Full tables: [`grounding_before_after.md`](grounding_before_after.md). Raw replies:
[`grounding_replies.jsonl`](grounding_replies.jsonl). Run on 2026-10-20 with openai/gpt-oss-120b
(temperature 0.2, reasoning effort low), on 64 held-out questions (46 answerable, 18 traps) in both
modes, with the 8 passages per question frozen at commit 3bc6f54 in
[`../fixtures/frozen_passages.json`](../fixtures/frozen_passages.json).

## The failures we started from

From the 2026-09-29 evaluation (`answers_results.json`) and its hand check (`handcheck.csv`):

| Failure | Example | Seen |
|---|---|---|
| A decline that answers anyway, with nothing to cite | tr-03 "What does the rex in your name mean?": status `not_in_sources`, text "rex is Latin for king". vg-03: status `not_in_sources`, text "Theo worked as an art dealer" | 3 of 88 replies |
| An off-topic decline that does not say it is off topic | tr-21 neutral: "I'm the museum's guide for Tyrannosaurus rex, here to answer questions about that dinosaur." | 1 (hand check note) |
| A decline although the answer was in the passages | tr-04 persona, vg-07 both modes | 3 of 88 |
| Malformed replies (not JSON, cut off, wrong field types) | none seen in that run, but `"citations": 5` crashed the pipeline and a non-JSON reply was shown as raw text | found by testing |

Citations to passages the model was not given were already removed before this change.

## The change

One deterministic check, `check_reply()` in `pipeline/persona.py`, applied to every reply after
the existing citation filter. The prompt did not change. Three rules:

1. A reply that cannot be read becomes a short "my sources do not say" line, never raw model text.
2. `answered` with no valid citation becomes `not_in_sources` (greetings, "who are you" and sound
   requests excepted).
3. A decline whose text does not actually say no (no "not", "never", "can't", "only", ...) gets
   a fixed decline line for its status.

The response schema, statuses and `/ask` fields are unchanged. The result gains a `check` field
naming the rule that fired, which the server ignores.

## Before and after (same 128 replies, scored both ways)

| | Before | After |
|---|---|---|
| Grounded answer accuracy | 0.922 | 0.922 |
| Answerable questions answered correctly | 0.891 | 0.891 |
| Trap questions declined | 1.000 | 1.000 |
| Unnecessary declines (support was in the passages) | 0 | 0 |
| Declines that still state the answer without a source | **1** | **0** |
| Answers shown with no valid citation | 0 | 0 |
| Unreadable replies shown / crashes | 0 / 0 | 0 / 0 |
| Regressions | | none |

The check changed 2 of 128 replies:

- **tr-03 persona (fixed).** The same failure as on 2026-09-29 came back: search did not give the
  passage about the name, and the model said "My name means 'king', the Latin word rex" under
  status `not_in_sources`. The visitor now hears "My sources do not say anything about that."
- **tr-21 neutral (clearer).** The off-topic reply that did not say no now says "I can only answer
  questions about Tyrannosaurus rex and the museum."

Grounded accuracy does not move, and we did not expect it to. These replies were already scored as
wrong (tr-03) or right (tr-21). The change is to what the visitor is shown: an unsourced claim
labelled as "not in my sources" no longer reaches them. Malformed replies did not occur in this
run. The 40 tests in `tests/test_answers.py` cover them, including 11 malformed reply shapes.

We checked by hand all 40 declines after the check. All 36 trap declines are correct and none of
them leaks an answer. The other 4 are on answerable questions where search gave no supporting
passage (tr-03 and tr-28, both modes). Declining is the right behaviour there.

## What still fails (future scope)

| Question | What happens | Cause | Where to fix |
|---|---|---|---|
| tr-03, tr-28 (both modes) | Honest decline on an answerable question | Search never returns the supporting passage | Search, issue #31 |
| vg-08 (both modes) | Answers "a foreign country" from the passage it got, but the expected answer is "Japan" | Search returned a related passage, not the right one | Search |
| tr-26 (both modes) | "Horned ceratopsians" without naming Triceratops | Supporting passage not retrieved; the answer is vague but not wrong | Search |
| tr-09 persona | Correct and cited ("strongest of any land animal") but marked wrong | Exact-word key-fact scoring | Scoring in `eval/eval_answers.py` |
| tr-09 neutral | Gives the newtons figure but not "largest of any land animal" | Partial answer | Prompt or scoring |

The T. rex search fix from issue #31 (PR #36) was merged after this run. With it, search now
returns the supporting passage for tr-03, tr-28, tr-26 and tr-09. It still misses vg-08 and vg-03
(Theo's job), because #31 only changed the T. rex. These numbers use the passages frozen before
#31, so the before and after comparison stays fair. The improvement from #31 is not in them.

The user test (`artifacts/evidence/session07/`, three people, 15 questions) found two more failures:

- **An answer that cites a real passage but adds a detail the passage doesn't have.** "Did you move
  to Arles?" added a move to Auvers in 1890, and "Did you die?" gave "July 1890". Neither detail is
  in the cited passage. The check cannot catch this, because the citation is valid. A next step
  would be to check that the numbers and names in an answer appear in the passages it cites.
- **The badge for an off-topic question that the check replaces.** "can you hello in spanish" got
  the fixed `not_in_sources` line, with the "Not in my sources" badge, where "Off topic" fits. Rule
  2 always uses `not_in_sources`.

In that test all 9 declines were honest, and none of them made anything up.

Known limits of the check itself:

- A decline that says no and then answers anyway ("my sources don't say, but I think...") passes
  rule 3, because it contains "don't". This did not happen in either run.
- Unnecessary declines are measured but not fixed. There were 3 on 2026-09-29 and 0 in this run, so
  for now this varies between runs more than it is a steady failure. A prompt change ("read every
  passage before saying the sources do not say") would need its own before and after run.
- Each question was asked once per mode, so run-to-run variation is not measured. The tr-03 leak
  showed up in both runs. The 09-29 vg-03 and tr-03 neutral leaks did not repeat.
- The fixed lines are less in character than the model's own declines. User testing in
  `artifacts/evidence/session07/` checks whether visitors find the declines fair.

## Reproduce

```bash
python -m eval.eval_grounding                  # rescore the saved replies, no model calls
python -m eval.eval_grounding --collect        # new replies (needs .env), then run the line above
python -m eval.eval_grounding --freeze         # only to refreeze the passages; this changes the baseline
python -m pytest tests/test_answers.py
```
