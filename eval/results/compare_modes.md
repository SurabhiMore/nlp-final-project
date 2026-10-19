# Persona vs plain guide

Paired comparison on the same held-out questions, matched by exhibit and question id. Source: `eval/results/answers_results.json` (run 2026-09-29T14:57:27+00:00, model openai/gpt-oss-120b, 8 passages per question). Correct means grounded, as scored by eval_answers.py.

| | Questions | Persona | Plain guide | Difference (points) | 95% interval (points) | Both correct | Persona only | Plain guide only | Both wrong | Exact McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|
| All | 44 | 0.864 (38) | 0.886 (39) | -2.3 | -12.1 to +7.0 | 37 | 1 | 2 | 4 | 1.00 |
| t-rex | 22 | 0.864 (19) | 0.864 (19) | +0.0 | -15.9 to +15.9 | 18 | 1 | 1 | 2 | 1.00 |
| van-gogh | 22 | 0.864 (19) | 0.909 (20) | -4.5 | -19.6 to +8.3 | 19 | 0 | 1 | 2 | 1.00 |

**Conclusion.** No evidence of a difference (p = 1.00). The modes disagreed on only 3 questions, and even a 3 to 0 split would give p = 0.250, so this sample is too small to show a difference either way. The 95% interval for the gap runs from -12.1 to +7.0 points (persona minus plain guide).

## Questions where the modes disagree

| Exhibit | Question | Persona | Plain guide |
|---|---|---|---|
| t-rex | tr-04: Who gave you the name Tyrannosaurus rex, and when? | wrong | right |
| t-rex | tr-11: How fast could you run? | right | wrong |
| van-gogh | vg-03: What was your brother Theo's job in Paris? | wrong | right |

## Limitations

- Each mode answered each question once, so run-to-run variation of the model is not measured.
- The test treats questions as independent and uses only the questions where the modes disagree.
- The questions were written by the team, so they may not match what visitors really ask.
