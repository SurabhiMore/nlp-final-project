## North Star across sessions

| Session | Model | Mode | Exhibit | Grounded accuracy | Citations per answer | Decline rate | Traps declined | Errors |
|---|---|---|---|---|---|---|---|---|
| Session 7 | openai/gpt-oss-120b | persona | van-gogh | 0.969 (31/32) | - | - | 9/9 | 0 |
| Session 7 | openai/gpt-oss-120b | persona | t-rex | 0.875 (28/32) | - | - | 9/9 | 0 |
| Session 7 | openai/gpt-oss-120b | persona | all | 0.922 (59/64) | - | - | 18/18 | 0 |
| Session 8 | llama3 | persona | van-gogh | 0.844 (27/32) | 1.17 | 0.250 | 8/9 | 0 |
| Session 8 | llama3 | persona | t-rex | 0.875 (28/32) | 1.71 | 0.250 | 8/9 | 0 |
| Session 8 | llama3 | persona | all | 0.859 (55/64) | 1.44 | 0.250 | 16/18 | 0 |
| Session 10 | openai/gpt-oss-120b | persona | van-gogh | 0.938 (30/32) | 1.14 | 0.312 | 9/9 | 0 |
| Session 10 | openai/gpt-oss-120b | persona | t-rex | 0.906 (29/32) | 1.48 | 0.281 | 9/9 | 0 |
| Session 10 | openai/gpt-oss-120b | persona | all | 0.922 (59/64) | 1.31 | 0.296 | 18/18 | 0 |
| Session 7 | openai/gpt-oss-120b | neutral | van-gogh | 0.969 (31/32) | - | - | 9/9 | 0 |
| Session 7 | openai/gpt-oss-120b | neutral | t-rex | 0.875 (28/32) | - | - | 9/9 | 0 |
| Session 7 | openai/gpt-oss-120b | neutral | all | 0.922 (59/64) | - | - | 18/18 | 0 |
| Session 8 | llama3 | neutral | van-gogh | 0.906 (29/32) | 1.09 | 0.281 | 9/9 | 0 |
| Session 8 | llama3 | neutral | t-rex | 0.844 (27/32) | 1.60 | 0.219 | 7/9 | 0 |
| Session 8 | llama3 | neutral | all | 0.875 (56/64) | 1.35 | 0.250 | 16/18 | 0 |

Session 7 citations and decline rate are not known: its results file was never committed.

Sources:
- Session 7: openai/gpt-oss-120b, `reports/session07.md`
- Session 8: llama3, `eval/results/answers_results_session08_llama3.json` (run 2026-10-26T21:59:22+00:00)
- Session 10: openai/gpt-oss-120b, `eval/results/answers_results.json` (run 2026-11-10T20:00:57+00:00)

Report frontmatter:

```yaml
north_star:
  metric: Grounded answer accuracy (persona mode, 32 held-out questions per exhibit)
  value: Van Gogh 0.938, T. rex 0.906 (59 of 64 overall), model openai/gpt-oss-120b
  previous: Van Gogh 0.969, T. rex 0.875 (59 of 64 overall), model openai/gpt-oss-120b (Session 7; same model, so like-for-like)
```
