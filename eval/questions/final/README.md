# Final Evaluation on Visitor-Written Questions

Pre-registered evaluation plan for the final benchmark numbers in Session 12 and the final report (Issue #82). This plan is written and committed before any visitor questions are annotated or evaluated, ensuring the evaluation criteria, scoring mechanisms, and contingency plans are fixed in advance.

---

## 1. Provenance of Questions

The test set is designed to evaluate the system on genuine visitor queries that no team member wrote:

1. **Source:** Collected during outside user phone testing (Issue #70, `artifacts/evidence/session11/` and Session 12 testing across participants P7, P8, P9, etc.).
2. **Collection timing:** Before testing the running application, each participant is asked to write down 5 questions they would naturally ask each exhibit (T. rex and Vincent van Gogh) without seeing the corpus, UI prompts, or previous model responses.
3. **Format:** Raw questions are deposited in `eval/questions/final/visitor_questions.jsonl` with records containing:
   - `person`: Tester identifier (e.g. `"P8"`).
   - `exhibit`: `"t-rex"` or `"van-gogh"`.
   - `question`: Verbatim string as written by the tester.

No team member adds, edits, or filters questions prior to annotation.

---

## 2. Question Annotation & Verification

Raw questions written by visitors will initially be collected in `eval/questions/final/visitor_questions.jsonl` (with fields `person`, `exhibit`, `question`).

To integrate seamlessly with the evaluation suite (`eval/datasets.py` and `eval/eval_answers.py`), which load corpora and questions per persona, the questions will be annotated and partitioned into:
- `eval/questions/final/t-rex.jsonl`
- `eval/questions/final/van-gogh.jsonl`

Each record adheres to the repository benchmark schema:

```json
{
  "id": "vst-vg-01",
  "question": "What kind of flowers did you like to paint most?",
  "type": "painting",
  "answerable": true,
  "gold_answer": "Sunflowers in yellow, as well as irises and blossoms.",
  "key_facts": [["sunflowers"], ["irises", "blossoms"]],
  "evidence": ["twelve sunflowers in a yellow vase", "irises"],
  "chunks": ["van-gogh-letters-0104"],
  "visitor_id": "P8"
}
```

### Annotation Rules

1. **Answerability:**
   - `answerable: true`: The question can be answered using facts directly documented in the exhibit's curated corpus passages (`data/corpora/{persona_id}_chunks.jsonl`).
   - `answerable: false`: The question is an inquiry whose answer is not in our sources, out-of-time (e.g., asking Van Gogh about events after his death in 1890 or T. rex about modern human history), or off-topic.
2. **Question Types (`type`):**
   - Answerable types: `fact`, `date`, `why`, `painting`, `quote`.
   - Unanswerable types: `outside_time`, `not_in_sources`, `off_topic`.
3. **Evidence & Key Facts:**
   - For `answerable: true`, non-empty `evidence` (exact substring snippets from supporting chunks), non-empty `key_facts` (grouped alternatives required for factual correctness), and non-empty `gold_answer` are required.
   - For `answerable: false`, `evidence` and `key_facts` must be empty lists (`[]`).
4. **Validation:**
   - All annotated question files must pass validation with zero problems:
     ```bash
     python -m eval.datasets --questions-dir eval/questions/final --check
     ```
   - If `visitor_questions.jsonl` is kept alongside in the directory, each persona can be verified individually:
     ```bash
     python -m eval.datasets --questions-dir eval/questions/final --persona t-rex --check
     python -m eval.datasets --questions-dir eval/questions/final --persona van-gogh --check
     ```
   - Validation checks that cited chunks exist in the corpus, evidence snippets exist in supporting chunks, and all key facts appear in both the supporting chunks and the gold answer.

---

## 3. Scoring Rules (Fair Key-Fact Check from #72)

Evaluation is performed using the fair scoring matcher implemented in `eval/datasets.py` (`key_facts_present`):

- **Normalization:** Text is lowercased, accent-folded, stripped of punctuation, and normalized.
- **Number words:** Number words are mapped to canonical digits (e.g. `"six"` $\rightarrow$ `"6"`, `"twenty"` $\rightarrow$ `"20"`).
- **Metric units:** Spelling variations are mapped to standard symbols (e.g. `"kilometres"`, `"kilometers"`, `"km"` $\rightarrow$ `"km"`).
- **Synonyms & Alternates:** Acceptable phrasing alternates are explicitly grouped in the inner lists of `key_facts` (e.g. `[["largest", "strongest"]]`).
- **Unanswerable Scoring:** Unanswerable trap questions score as correct if and only if the guide declines to answer with a valid decline status recognized by the pipeline (`status` in `"not_in_sources"`, `"outside_time"`, or `"declined"`).
- **Deterministic Evaluation:** Scoring code and thresholds remain identical to those finalized in Issue #72 / PR #77; no scoring rule is modified after model outputs are generated.

---

## 4. Evaluation Modes & Comparison

Every visitor question will be evaluated across two distinct interaction modes under identical retrieval conditions:

1. **Persona Mode:** The model responds in-character as the historical exhibit (Vincent van Gogh or Stan the T. rex) using first-person voice and exhibit persona prompts.
2. **Neutral Guide Mode:** The model responds as an objective, third-person museum docent delivering neutral explanatory answers from the same passages.

### Statistical Analysis

- **Paired comparison:** Disagreement counts ($b$ and $c$) between persona and neutral modes.
- **Significance:** Two-sided exact McNemar's test ($p$-value).
- **Confidence Interval:** Newcombe paired difference 95% confidence interval on accuracy difference.

---

## 5. Model Execution & Environment

- **Model:** `openai/gpt-oss-120b` via Groq.
- **Parameters:** `temperature = 0.2`, `reasoning_effort = "low"`.
- **Pipeline:** Top-8 BM25 retrieval, claim grounding check (`pipeline/claims.py`), reply sanity check (`pipeline/check_reply.py`), and question classifier (`pipeline/classifier.py`).
- **Single-Run Policy:** Exactly **one** production run per question per mode. No selective rerunning, manual cherry-picking, or post-hoc prompt iterations are permitted.
- **Execution Commands:**
  1. Evaluate questions across both modes (using `--sleep 2.0` to respect Groq rate limits):
     ```bash
     python -m eval.eval_answers --questions-dir eval/questions/final --out answers_results_final.json --sleep 2.0
     ```
  2. Compute paired McNemar and Newcombe interval comparison:
     ```bash
     python -m eval.compare_modes --results eval/results/answers_results_final.json --out-dir eval/results
     ```
- **Quota & Resumption Management:**
  - Each question uses $\approx 2,800$ tokens. Evaluating $\approx 40$ questions in both modes requires $\approx 224,000$ tokens, exceeding the daily free-tier limit on Groq.
  - `eval/eval_answers.py` logs each answer incrementally to `eval/results/answers_progress.jsonl`. If daily quotas are reached, execution can be paused and resumed using:
    ```bash
    python -m eval.eval_answers --questions-dir eval/questions/final --out answers_results_final.json --sleep 2.0 --resume
    ```
    This avoids re-calling the API for completed questions and allows finishing the run across two days or using a secondary key.
- **Committed Artifacts:**
  - Raw JSON outputs: `eval/results/answers_results_final.json`.
  - Final summary table and comparison: `eval/results/final_numbers.md`.

---

## 6. Contingency Plan (Under 20 Questions by Nov 25)

Our target corpus size is 20–30 answerable visitor questions. If fewer than 20 answerable questions are collected by Wednesday, November 25, 2026:

1. The set will be supplemented with genuine, unscripted visitor questions recorded in earlier user test logs (`artifacts/evidence/session05/`, `artifacts/evidence/session07/`, `artifacts/evidence/session08/`).
2. Only questions that were never used for prompt engineering, tuning, or dev/held-out evaluations will be eligible.
3. Every supplemented question will carry a `"source"` tag denoting the original test log session to ensure full transparency.

---

## 7. Resolution on `vg-08` Search Miss

The benchmark question `vg-08` ("What did the countryside around Arles remind you of?") misses chunk `0060`/`0180` under BM25 due to vocabulary mismatch ("Arles countryside" vs. "Japan").

- **Investigation (#72):** Dense and hybrid retrieval were evaluated in `tests/results/2026-11-17_feat-data-eval.md`. While hybrid search surfaced chunk `0180` at rank 6, it reduced overall retrieval Hit@8 on the T. rex benchmark from 0.96 to 0.70 and on Van Gogh from 0.87 to 0.78.
- **Decision:** As established in Session 11, search parameters will **not** be tuned to fix a single outlier question at the cost of overall retrieval accuracy. The BM25 search miss on `vg-08` is accepted and documented as a known system boundary in `eval/results/final_numbers.md` and the final report.
