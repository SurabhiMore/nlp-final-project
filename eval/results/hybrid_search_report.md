# Hybrid Search (BM25 and Embeddings) Evaluation Report

**Issue #39**: Meaning-based search next to BM25 and Reciprocal Rank Fusion (RRF).

---

## 1. Executive Summary & Default Mode Decision

### Acceptance Criterion for Default Mode
> *"Make hybrid the default only if it beats BM25 on Hit@8 for both exhibits without new regressions on the held-out set. Otherwise keep BM25 as the default and report why."*

### Recommendation
**Keep `bm25` as the default search mode.**

### Why BM25 Remains the Default
1. **Hit@8 on T. rex drops significantly with Hybrid**:
   - BM25 achieves **0.957** Hit@8 on the main T. rex questions (22 of 23 answerable questions have a supporting passage in the top 8).
   - Hybrid achieves **0.696** Hit@8 (16 of 23), causing 7 regressions on the main set.
   - The T. rex passages contain specialized paleontological terminology (e.g. *ceratopsian*, *digit*, *bite force*, *Hell Creek Formation*) where BM25 with exact matching and `TERM_MAP` strongly outperforms generic sentence embeddings.
2. **Hit@8 on Van Gogh drops with Hybrid**:
   - BM25 achieves **0.870** Hit@8 on Van Gogh main questions.
   - Hybrid achieves **0.783** Hit@8 (18 of 23), losing ground on specific biographical questions (such as `vg-05` and `vg-09`).
3. **Held-out Set Behavior**:
   - On the 10 held-out T. rex questions, Hybrid does improve Hit@8 (0.600 -> 0.800) and MRR@10 (0.234 -> 0.352), but introduces 1 new regression (`tr-h10`: rank 4 -> 5).
4. **Latency**:
   - BM25 executes in **0.12 ms** per question.
   - Dense and Hybrid add **~6.4 to 7.0 ms** of inference latency per question.

Because Hybrid does not beat BM25 on Hit@8 for both exhibits, `SEARCH_MODE` defaults to `bm25`, with `dense` and `hybrid` fully supported via environment variable or argument.

---

## 2. Evaluation Results Across All Three Modes

### Main Questions

| Exhibit | Mode | Questions | Hit@1 | Hit@5 | Hit@8 | Recall@5 | MRR@10 |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **t-rex** | **bm25 (default)** | 23 | **0.348** | **0.739** | **0.957** | **0.717** | **0.500** |
| | dense | 23 | 0.391 | 0.522 | 0.522 | 0.522 | 0.445 |
| | hybrid (RRF k=60) | 23 | 0.391 | 0.652 | 0.696 | 0.652 | 0.480 |
| **van-gogh** | **bm25 (default)** | 23 | **0.696** | **0.870** | **0.870** | **0.848** | **0.762** |
| | dense | 23 | 0.478 | 0.609 | 0.609 | 0.587 | 0.525 |
| | hybrid (RRF k=60) | 23 | 0.609 | 0.696 | 0.783 | 0.696 | 0.655 |

### Held-out Questions

*(Note: Van Gogh has no held-out question set; the held-out set currently covers T. rex).*

| Exhibit | Mode | Questions | Hit@1 | Hit@5 | Hit@8 | Recall@5 | MRR@10 |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **t-rex (heldout)** | bm25 (default) | 10 | 0.100 | 0.500 | 0.600 | 0.450 | 0.234 |
| | dense | 10 | **0.400** | **0.800** | **0.900** | **0.750** | **0.531** |
| | hybrid (RRF k=60) | 10 | 0.200 | 0.700 | 0.800 | 0.650 | 0.352 |


---

## 3. Specific Question Analysis: vg-03, vg-04, and vg-08

### vg-03: *"What was your brother Theo's job in Paris?"*
- **Supporting Chunk**: `van-gogh-aic-0001`
- **Passage Text**: *"...where his beloved brother Theo was a dealer..."*
- **Results**:
  - BM25: Rank 27 (miss in top 10)
  - Dense: Rank 233 (miss in top 10)
  - Hybrid: Rank 70 (miss in top 10)
- **Root Cause**: The supporting passage is an artwork provenance card from the Art Institute of Chicago for *The Bedroom*. The vast majority of the chunk is auction catalog details (*"V. W. van Gogh, Amsterdam; sold to the Art Institute, 1926..."*). While human intuition connects "job" to "dealer", the global embedding of this auction record is dominated by gallery and transaction tokens, scoring poorly against a biographical question about Theo's profession.

### vg-04: *"When did you arrive in Arles?"*
- **Supporting Chunk**: `van-gogh-wiki-0058`
- **Passage Text**: *"...Van Gogh's arrival in Arles in February 1888..."*
- **Results**:
  - BM25: Rank 13 (miss in top 10)
  - Dense: Rank 36 (miss in top 10)
  - Hybrid: Rank 17 (miss in top 10)
- **Root Cause**: Many passages from Van Gogh's letters and art descriptions discuss Arles in great detail (*"I arrived here in Arles during a snowstorm..."*, *"The Yellow House in Arles..."*). These competing passages push the single biographical sentence down past the top 10 threshold.

### vg-08: *"What did the countryside around Arles remind you of?"*
- **Supporting Chunk**: `van-gogh-gut40393-0060`
- **Passage Text**: *"...seems to me just as beautiful as Japan on account of the clearness of the atmosphere and the cheerful colour effects..."*
- **Results**:
  - BM25: Rank 193 (miss in top 10)
  - Dense: Rank 23 (miss in top 10)
  - Hybrid: Rank 58 (miss in top 10)
- **Insight**: Semantic search significantly closes the gap on figurative phrasing compared to BM25 (moving the passage from rank 193 up to rank 23), though competing letter excerpts about landscapes still take earlier ranks.

---

## 4. Regressions Under Hybrid Search

The following questions had a lower rank for their first supporting passage under Hybrid compared to BM25:

### T. rex (Main)
1. **tr-01** (*"When did you live?"*): Rank 7 -> miss
2. **tr-02** (*"Where did you live?"*): Rank 7 -> miss
3. **tr-03** (*"What does the rex in your name mean?"*): Rank 5 -> miss
4. **tr-07** (*"How long is the most complete T. rex skeleton?"*): Rank 6 -> Rank 7
5. **tr-08** (*"How heavy could you get?"*): Rank 7 -> miss
6. **tr-09** (*"How strong was your bite?"*): Rank 3 -> Rank 5
7. **tr-10** (*"How many fingers did you have on each hand?"*): Rank 5 -> miss
8. **tr-26** (*"Which horned dinosaur was among your primary prey targets?"*): Rank 7 -> miss
9. **tr-28** (*"Did you hunt primarily during the day or at night?"*): Rank 3 -> Rank 5

### Van Gogh (Main)
1. **vg-05** (*"What is considered your first major work?"*): Rank 1 -> miss
2. **vg-07** (*"In the portrait Gauguin painted of you, what were you doing?"*): Rank 5 -> Rank 6
3. **vg-09** (*"What did you say a painter should have a feeling for, to make life a joy?"*): Rank 1 -> miss
4. **vg-26** (*"What was your father's profession, and what church did he serve?"*): Rank 3 -> Rank 7
5. **vg-29** (*"What were your reported last words before you died in Auvers?"*): Rank 1 -> Rank 4

### T. rex (Held-out)
1. **tr-h10** (*"How big is the cast tooth in the Smithsonian education collection?"*): Rank 4 -> Rank 5

*(Total regressions: 15)*

---

## 5. Latency Measurements

Benchmarked over all 64 questions across both exhibits (3 runs, after model warmup):

| Search Mode | Mean Latency | Median Latency | 95th Percentile | Added Time vs BM25 |
|---|:---:|:---:|:---:|:---:|
| **BM25** | **0.12 ms** | **0.11 ms** | **0.24 ms** | *Baseline* |
| **Dense** | **6.40 ms** | **6.56 ms** | **8.67 ms** | **+6.28 ms** |
| **Hybrid** | **7.14 ms** | **7.14 ms** | **9.15 ms** | **+7.02 ms** |

---

## 6. How to Reproduce

All evaluations are fully reproducible using the commands below:

```bash
# 1. Run evaluation for all three search modes
python -m eval.eval_retrieval --mode bm25 --out retrieval_bm25.json
python -m eval.eval_retrieval --mode dense --out retrieval_dense.json
python -m eval.eval_retrieval --mode hybrid --out retrieval_hybrid.json

# 2. Run evaluation on held-out questions
python -m eval.eval_retrieval --mode bm25 --questions-dir eval/questions/heldout --out retrieval_bm25_heldout.json
python -m eval.eval_retrieval --mode dense --questions-dir eval/questions/heldout --out retrieval_dense_heldout.json
python -m eval.eval_retrieval --mode hybrid --questions-dir eval/questions/heldout --out retrieval_hybrid_heldout.json

# 3. Compare BM25 vs Hybrid
python -m eval.compare_retrieval \
  --set "Main questions" eval/results/retrieval_bm25.json eval/results/retrieval_hybrid.json \
  --set "Held-out questions" eval/results/retrieval_bm25_heldout.json eval/results/retrieval_hybrid_heldout.json \
  --out eval/results/hybrid_search_comparison.md

# 4. Run automated test suite
python -m pytest
```
