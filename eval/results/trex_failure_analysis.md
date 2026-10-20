# T-Rex retrieval failure analysis (issue #31)

Source: `eval/results/retrieval_baseline.json` (BM25 before any change), main T-Rex question set
(`eval/questions/t-rex.jsonl`). The held-out set (`eval/questions/heldout/t-rex.jsonl`) was **not**
used for this analysis or for choosing any mapping.

"Rank" is the rank of the first supporting passage in the top 10 ("miss" = not in the top 10).
"Query terms" are what BM25 searched for after stopword removal and stemming.

| ID | Question | Query terms (baseline) | Supporting chunk | Baseline rank | Retrieved instead (top 3) | Likely cause | Fix tried | Rank after |
|---|---|---|---|---|---|---|---|---|
| tr-01 | When did you live? | `live` | t-rex-wiki-0000 | 5 | wiki-0043, wiki-0046, wiki-0010 | Passage says "lived"; stemmer did not strip `-ed`. "you" is a stopword, so one generic term is left | `-ed` stemming | 7 (worse, still in top 8) |
| tr-03 | What does the rex in your name mean? | `rex name mean` | t-rex-wiki-0000 | miss | wiki-0063, si-0014, wiki-0004 | Passage says "meaning"; `-ing` not stripped | `-ing` stemming | 5 |
| tr-04 | Who gave you the name Tyrannosaurus rex, and when? | `gave name tyrannosauru rex` | t-rex-wiki-0005 | miss | si-0014, si-0019, si-0021 | Passage says "named"; museum catalogue records repeat "Tyrannosaurus rex" and outrank it | `-ed` stemming | miss (unchanged) |
| tr-07 | How long is the most complete T. rex skeleton? | `long complete t rex skeleton` | t-rex-wiki-0001 | 6 | wiki-0010, wiki-0009, wiki-0057 | Passage says "measures 12.3 m", not "long"; "long" is too common to map safely | none | 6 |
| tr-08 | How heavy could you get? | `heavy get` | t-rex-wiki-0001 | 7 | wiki-0081, wiki-0056, wiki-0058 | Passage gives mass in tonnes ("8.8 t"); never says "heavy" | `heavy -> mass, weigh` tried, **rejected** (pushed it out of top 10) | 7 |
| tr-09 | How strong was your bite? | `strong bite` | t-rex-wiki-0001 | 10 | wiki-0090, wiki-0091, wiki-0096 | Passage says "bite force"; "strong" matches nothing useful | `bite -> force` | 3 |
| tr-10 | How many fingers did you have on each hand? | `many finger hand` | t-rex-wiki-0000, -0001 | miss | wiki-0018, wiki-0035, wiki-0099 | Passage says "two clawed digits" | `finger -> digit` | 5 |
| tr-26 | Which horned dinosaur was among your primary prey targets? | `horned dinosaur among primary prey target` | t-rex-wiki-0081 | miss | wiki-0099, wiki-0001, wiki-0071 | Passage says "ceratopsians such as Triceratops" | `horned -> ceratopsian` | 7 |
| tr-28 | Did you hunt primarily during the day or at night? | `hunt primarily day night` | t-rex-wiki-0082 | 9 | wiki-0092, wiki-0097, wiki-0076 | Passage says "hunted"; `-ed` not stripped | `-ed` stemming | 3 |

## Two kinds of failure

- **Word endings** (tr-01, tr-03, tr-04, tr-28): fixed for every exhibit by extending `_stem` to `-ed`/`-ing`.
- **Different wording** (tr-07, tr-08, tr-09, tr-10, tr-26): fixed only where a single, specific word
  maps to the passage's word, via `TERM_MAP["t-rex"]` in `pipeline/retrieve.py`. Generic words
  ("long", "heavy") were not mapped because the passage words they would map to are too common.

Not fixed: tr-04 (catalogue records dominate) and tr-07/tr-08 (no safe mapping).
