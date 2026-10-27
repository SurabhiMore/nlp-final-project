# Time-boundary check

Run at 2026-10-27T03:59:14+00:00. Command: `python -m eval.eval_timecheck --offline`

| exhibit / set | questions | flagged right | false flags | missed | precision | recall |
|---|---|---|---|---|---|---|
| all | 62 | 9 | 2 | 11 | 0.82 | 0.45 |
| van-gogh/existing | 32 | 2 | 0 | 2 | 1.00 | 0.50 |
| van-gogh/new | 30 | 7 | 2 | 9 | 0.78 | 0.44 |

## False flags (real questions the check would block)

- `vg-tc-01` Where was the house you painted in The Yellow House? — 'Yellow House': every Wikidata match dates after 1890 (earliest 2006)
- `vg-tc-04` Where did you buy Japanese woodcuts? — 'Japanese': every Wikidata match dates after 1890 (earliest 2001)

## Missed after-time questions

- `vg-16` What did you think of Picasso's painting Guernica? — no reason
- `vg-18` How does it feel to be one of the most famous painters in history today? — no reason
- `vg-tc-15` Did you ever ride the Paris Métro? — no reason
- `vg-tc-16` Have you seen Theo van Gogh's film Submission? — no reason
- `vg-tc-17` Did you see Monet's Water Lilies series? — no reason
- `vg-tc-18` What do you think of the Van Gogh Museum in Amsterdam? — no reason
- `vg-tc-19` Are you happy your paintings hang in the Musée d'Orsay? — no reason
- `vg-tc-23` What do you think of Einstein's theory of relativity? — no reason
- `vg-tc-24` Did you see the Wright brothers fly their airplane? — no reason
- `vg-tc-29` Did you ever watch a movie at the cinema? — no reason
- `vg-tc-30` Did you listen to the radio while you painted? — no reason
