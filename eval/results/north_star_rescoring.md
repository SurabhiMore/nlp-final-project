# North Star Rescoring Across Sessions (Issue #72)

Grounded answer accuracy (persona mode, 32 questions per exhibit; 46 answerable, 18 traps), rescored with fair key-fact matching: number words accepted for digits ('six' for '6'), standard unit spellings normalized ('km', 'kilometres', 'kilometers'), and validated synonyms added as alternatives ('strongest' for 'largest' in `tr-09`, 'dim light' for 'low-light' in `tr-28`).

**All rescoring runs completely offline with 0 model calls.**

## Rescoring Summary (Persona Mode)

| Session | Model | Exhibit | Old Accuracy | New (Fair) Accuracy | Delta | Traps Declined |
|---|---|---|---|---|---|---|
| Session 7 | openai/gpt-oss-120b | van-gogh | 0.969 (31/32) | 0.969 (31/32) | ±0 | 9/9 |
| Session 7 | openai/gpt-oss-120b | t-rex | 0.875 (28/32) | 0.906 (29/32) | +1 (`tr-09`) | 9/9 |
| Session 7 | openai/gpt-oss-120b | **all** | **0.922 (59/64)** | **0.938 (60/64)** | **+1 (60/64)** | **18/18** |
| Session 8 | llama3 | van-gogh | 0.844 (27/32) | 0.844 (27/32) | ±0 | 8/9 |
| Session 8 | llama3 | t-rex | 0.875 (28/32) | 0.875 (28/32) | ±0 | 8/9 |
| Session 8 | llama3 | **all** | **0.859 (55/64)** | **0.859 (55/64)** | **±0 (55/64)** | **16/18** |
| Session 10 | openai/gpt-oss-120b | van-gogh | 0.938 (30/32) | 0.938 (30/32) | ±0 | 9/9 |
| Session 10 | openai/gpt-oss-120b | t-rex | 0.906 (29/32) | 1.000 (32/32) | +3 (`tr-09`, `tr-24`, `tr-28`) | 9/9 |
| Session 10 | openai/gpt-oss-120b | **all** | **0.922 (59/64)** | **0.969 (62/64)** | **+3 (62/64)** | **18/18** |

## Questions Fixed by Fair Scoring

### 1. `tr-09` ('How strong was your bite?')
- **Issue**: Model replied with *'the strongest bite of any land animal'* (Session 10) and *'the strongest of any land animal ever recorded'* (Session 7), cited. Key-fact check previously required the literal word `'largest'` from the source snippet.
- **Resolution**: Added `'strongest'` as an accepted alternative in `eval/questions/t-rex.jsonl`.
- **Impact**: Fixed in both Session 7 and Session 10.

### 2. `tr-24` ('What kind of vision did you have, and how far could you see objects clearly?')
- **Issue**: Model replied with *'spot objects as far as six kilometres away'* (Session 10), cited. Key-fact check required digits `'6 km'`.
- **Resolution**: `normalize()` in `eval/datasets.py` now maps number words to digits (`six` -> `6`) and unit variants (`kilometres`/`kilometers` -> `km`).
- **Impact**: Fixed in Session 10.

### 3. `tr-28` ('Did you hunt primarily during the day or at night?')
- **Issue**: Model replied *'My eyes weren’t great in dim light, so scientists think I hunted during the day.'* (Session 10), cited. Key-fact check required `'low-light'` or `'poor'`.
- **Resolution**: Added `'dim light'` as an accepted alternative in `eval/questions/t-rex.jsonl`.
- **Impact**: Fixed in Session 10.

## Remaining Session 10 Misses (2 of 64)

| Question | Nature | Cause Analysis |
|---|---|---|
| `vg-07` ('In Gauguin's portrait of you, what were you doing?') | Wrong decline | Model replied `{"answer": "I have no description of that portrait in my letters, so I cannot say what I was doing in it.", "status": "not_in_sources"}`. Investigation confirmed `check_reply` was NOT the cause (`check: null`). The model overlooked the subordinate clause *'while I was painting some sunflowers'* at the end of letter chunk `van-gogh-gut40393-0052`. |
| `vg-08` ('What did the countryside around Arles remind you of?') | Search miss | BM25 failed to retrieve chunk `van-gogh-gut40393-0060` (*'country in these parts seems to me just as beautiful as Japan'*) because the query words 'countryside' and 'Arles' do not appear in that chunk. Hybrid search retrieves chunk `van-gogh-gut40393-0180` at rank 6, but hybrid search causes severe regressions on other questions (Hit@8 drops from 0.96 to 0.70 on T. rex, and 0.87 to 0.78 on Van Gogh). Following policy, search was not changed. |

## Frontmatter for Reports

```yaml
north_star:
  metric: Grounded answer accuracy (persona mode, 32 held-out questions per exhibit)
  value: Van Gogh 0.938, T. rex 1.000 (62 of 64 overall), model openai/gpt-oss-120b
  previous: Van Gogh 0.969, T. rex 0.906 (60 of 64 overall), model openai/gpt-oss-120b (Session 7 rescored)
```
