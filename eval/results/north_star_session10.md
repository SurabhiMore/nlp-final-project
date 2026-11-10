# North Star rerun, Session 10 (issue #64)

Grounded answer accuracy on the 64 held-out questions (32 per exhibit; 46 answerable, 18 traps),
persona mode, rerun on `openai/gpt-oss-120b` so it can be compared like-for-like with Session 7.

- Run: 2026-11-10T20:00:57+00:00, `python -m eval.eval_answers --modes persona --sleep 20 --resume`
- Model `openai/gpt-oss-120b` on Groq, `LLM_REASONING_EFFORT=low`, 8 passages per question, BM25 search,
  question classifier on (`ENABLE_CLASSIFIER=1`, the default)
- 64 of 64 calls answered, 0 errors. Raw results: [`answers_results.json`](answers_results.json)
- Session 8 results kept as [`answers_results_session08_llama3.json`](answers_results_session08_llama3.json)
- Full table: [`north_star_comparison.md`](north_star_comparison.md), made by
  `python scripts/compare_north_star.py --out eval/results/north_star_comparison.md`

## Result

| Persona mode | Session 7 (gpt-oss-120b) | Session 8 (llama3) | Session 10 (gpt-oss-120b) |
|---|---|---|---|
| Van Gogh | 0.969 (31/32) | 0.844 (27/32) | 0.938 (30/32) |
| T. rex | 0.875 (28/32) | 0.875 (28/32) | 0.906 (29/32) |
| All | **0.922 (59/64)** | 0.859 (55/64) | **0.922 (59/64)** |
| Traps declined | 18/18 | 16/18 | 18/18 |
| Citations per answered reply | - | 1.44 | 1.31 |
| Decline rate (all questions) | - | 0.250 | 0.296 |

**Conclusion.** On the same model, grounded accuracy is back to Session 7's 59 of 64. The drop to
55 of 64 in Session 8 came from the model (llama3), not from the code. The changes since Session 7
(reply check, claim check, question classifier, multilingual handling) did not cost accuracy, and
all 18 traps are still declined.

Session 7's results file was never committed, so its numbers come from `reports/session07.md` and
a question-by-question comparison with Session 7 is not possible. The comparison below is against
Session 8.

## Changes against Session 8, question by question

**Fixed in Session 10 (7):** tr-07, tr-08, tr-20 (trap: eye colour, now `not_in_sources`),
vg-03, vg-21 (trap: "What is 17 times 23?", now blocked by the question classifier), vg-26, vg-30.
Only vg-21 can be credited to a code change; the others are the model.

**Newly wrong in Session 10 (3):** tr-24, tr-28, vg-07.

**Wrong in both (2):** tr-09, vg-08.

## The 5 misses

| Question | What went wrong | Kind |
|---|---|---|
| tr-09 How strong was your bite? | Answer says the bite was "the strongest of any land animal", with a supporting citation. The check needs the word "largest". | Scoring too strict |
| tr-24 What kind of vision did you have...? | Answer gives binocular vision, 55 degrees and "six kilometres", cited. The check needs "6 km" written with digits. | Scoring too strict |
| tr-28 Did you hunt during the day or at night? | Answer says "during the day" because its eyes "weren't great in dim light", cited. The check needs "low-light" or "poor". | Scoring too strict |
| vg-07 In Gauguin's portrait of you, what were you doing? | Declined (`not_in_sources`) although the passage about painting sunflowers was among the 8 retrieved. Session 8 answered it correctly. | Wrong decline (real regression) |
| vg-08 What did the countryside around Arles remind you of? | The passage that mentions Japan was not retrieved, so the answer describes Arles from another passage. Same miss in Session 8. | Search miss |

Three of the five misses are correct, cited answers that the automatic key-fact check does not
recognise. A human reader would score this run about 62 of 64. The same strict check was used in
Sessions 7 and 8, so the comparison between sessions is still fair. The two real problems are
one wrong decline (vg-07) and one search miss (vg-08).

## Follow-ups

- vg-07: find out whether the model or `check_reply` turned the answer into a decline
  (the `check` field of the row in `answers_results.json`).
- vg-08: the Japan passage is not found for this question; a search issue, not a model issue.
- Key-fact matching: accept number words ("six" for "6") and more synonyms (largest/strongest,
  low-light/dim light), or list them as alternatives in the question files. This would change the
  metric, so rescore Sessions 8 and 10 together if it is done.
- Plain-guide mode was not rerun (persona only, to stay within the Groq daily token limit).

## For the Session 10 weekly report

```yaml
north_star:
  metric: Grounded answer accuracy (persona mode, 32 held-out questions per exhibit)
  value: Van Gogh 0.938, T. rex 0.906 (59 of 64 overall), model openai/gpt-oss-120b
  previous: Van Gogh 0.969, T. rex 0.875 (59 of 64 overall), model openai/gpt-oss-120b (Session 7; same model, so like-for-like)
```

- **North Star rerun on gpt-oss-120b.** Persona mode 59 of 64 (Van Gogh 0.938, T. rex 0.906),
  the same total as Session 7 on the same model, with all 18 traps declined and no failed calls. The
  Session 8 drop to 55 of 64 was the model (llama3), not the code. Of the 5 misses, 3 are correct
  answers the strict key-fact check does not match, 1 is a wrong decline (vg-07) and 1 a search miss
  (vg-08) ([summary](../eval/results/north_star_session10.md),
  [comparison](../eval/results/north_star_comparison.md)) (evidence: #64).
