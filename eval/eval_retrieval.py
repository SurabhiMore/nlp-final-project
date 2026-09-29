"""How well does search find the passages that answer each question?

    python -m eval.eval_retrieval                 # every exhibit with a question file
    python -m eval.eval_retrieval --persona t-rex

Only answerable questions are scored, since traps have no supporting passage.
For each question, the supporting passages are the ones containing its
evidence text (see eval/datasets.py). Metrics:

  Hit@1, Hit@5   share of questions with a supporting passage in the top 1 / top 5
  Hit@8          the same for the top 8, which is how many passages the answer model sees
  Recall@5       share of all supporting passages that appear in the top 5, averaged
  MRR@10         average of 1 / (rank of the first supporting passage), 0 if not in the top 10

Results are saved to eval/results/retrieval_results.json.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval import datasets  # noqa: E402
from pipeline import config  # noqa: E402
from pipeline.retrieve import retrieve  # noqa: E402

RESULTS_DIR = config.EVAL_DIR / "results"


def evaluate(persona_id, depth=10):
    chunks = datasets.load_chunks(persona_id)
    rows = []
    for q in datasets.load_questions(persona_id):
        if not q["answerable"]:
            continue
        support = datasets.supporting_chunk_ids(q, chunks)
        ranked = [c["id"] for c in retrieve(persona_id, q["question"], k=depth)]
        first = next((i + 1 for i, cid in enumerate(ranked) if cid in support), None)
        top5 = set(ranked[:5])
        rows.append({
            "id": q["id"],
            "question": q["question"],
            "type": q["type"],
            "supporting": sorted(support),
            "top5": ranked[:5],
            "first_hit_rank": first,
            "hit@1": first == 1,
            "hit@5": first is not None and first <= 5,
            "hit@8": first is not None and first <= 8,
            "recall@5": len(top5 & support) / len(support) if support else 0.0,
            "rr@10": 1.0 / first if first else 0.0,
        })
    n = len(rows) or 1
    summary = {
        "questions": len(rows),
        "hit@1": round(sum(r["hit@1"] for r in rows) / n, 3),
        "hit@5": round(sum(r["hit@5"] for r in rows) / n, 3),
        "hit@8": round(sum(r["hit@8"] for r in rows) / n, 3),
        "recall@5": round(sum(r["recall@5"] for r in rows) / n, 3),
        "mrr@10": round(sum(r["rr@10"] for r in rows) / n, 3),
    }
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description="Evaluate BM25 search on the held-out questions.")
    parser.add_argument("--persona", help="only this exhibit")
    args = parser.parse_args()

    ids = [args.persona] if args.persona else [p.stem for p in datasets.question_files()]
    output = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "retriever": "BM25 (rank-bm25, light stemming, stopwords removed)", "exhibits": {}}

    print(f"{'exhibit':10} {'questions':>9} {'Hit@1':>7} {'Hit@5':>7} {'Hit@8':>7} {'Recall@5':>9} {'MRR@10':>7}")
    for persona_id in ids:
        summary, rows = evaluate(persona_id)
        output["exhibits"][persona_id] = {"summary": summary, "questions": rows}
        print(f"{persona_id:10} {summary['questions']:>9} {summary['hit@1']:>7.2f} {summary['hit@5']:>7.2f} "
              f"{summary['hit@8']:>7.2f} {summary['recall@5']:>9.2f} {summary['mrr@10']:>7.2f}")
        misses = [r["id"] for r in rows if not r["hit@5"]]
        if misses:
            print(f"{'':10} missed in top 5: {', '.join(misses)}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "retrieval_results.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()