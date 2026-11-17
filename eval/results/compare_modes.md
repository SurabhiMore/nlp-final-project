# Persona vs plain guide

Paired comparison on the same held-out questions, matched by exhibit and question id. Source: `eval/results/answers_results.json` (run 2026-11-17T19:23:46+00:00, model openai/gpt-oss-120b, 8 passages per question). Correct means grounded, as scored by eval_answers.py.

| | Questions | Persona | Plain guide | Difference (points) | 95% interval (points) | Both correct | Persona only | Plain guide only | Both wrong | Exact McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|
| All | 64 | 0.969 (62) | 0.953 (61) | +1.6 | -5.4 to +9.2 | 60 | 2 | 1 | 1 | 1.00 |
| t-rex | 32 | 1.000 (32) | 0.938 (30) | +6.2 | -5.4 to +20.1 | 30 | 2 | 0 | 0 | 0.50 |
| van-gogh | 32 | 0.938 (30) | 0.969 (31) | -3.1 | -15.4 to +6.9 | 30 | 0 | 1 | 1 | 1.00 |

**Conclusion.** No evidence of a difference (p = 1.00). The modes disagreed on only 3 questions, and even a 3 to 0 split would give p = 0.250, so this sample is too small to show a difference either way. The 95% interval for the gap runs from -5.4 to +9.2 points (persona minus plain guide).

## Questions where the modes disagree

| Exhibit | Question | Persona | Plain guide |
|---|---|---|---|
| t-rex | tr-09: How strong was your bite? | right | wrong |
| t-rex | tr-26: Which horned dinosaur was among your primary prey targets? | right | wrong |
| van-gogh | vg-07: In the portrait Gauguin painted of you, what were you doing? | wrong | right |

## Limitations

- Each mode answered each question once, so run-to-run variation of the model is not measured.
- The test treats questions as independent and uses only the questions where the modes disagree.
- The questions were written by the team, so they may not match what visitors really ask.
