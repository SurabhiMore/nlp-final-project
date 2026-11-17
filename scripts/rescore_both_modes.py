"""Rescore every saved answer in answers_results.json, both modes, with the current key-fact scoring.

No model calls. Run from the repo root:  python scripts/rescore_both_modes.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eval import datasets, eval_answers  # noqa: E402

path = ROOT / "eval" / "results" / "answers_results.json"
data = json.loads(path.read_text(encoding="utf-8"))
exhibits = sorted({r["exhibit"] for r in data["answers"]})
modes = [m for m in ("persona", "neutral") if any(r["mode"] == m for r in data["answers"])]
chunks = {e: datasets.load_chunks(e) for e in exhibits}
questions = {e: {q["id"]: q for q in datasets.load_questions(e)} for e in exhibits}

changed = []
for row in data["answers"]:
    q = questions[row["exhibit"]][row["question_id"]]
    exhibit_chunks = chunks[row["exhibit"]]
    support = datasets.supporting_chunk_ids(q, exhibit_chunks)
    result = {"status": row["status"], "answer": row["answer"], "citations": row.get("citations") or []}
    new = eval_answers.score(q, result, {c["id"]: c for c in exhibit_chunks}, support)
    if new["grounded"] != row["grounded"]:
        changed.append(f"{row['mode']:8} {row['question_id']}: {row['grounded']} -> {new['grounded']}")
    row.update(new)

summary = {}
for e in exhibits:
    for m in modes:
        summary[f"{e}/{m}"] = eval_answers.summarize([r for r in data["answers"] if r["exhibit"] == e and r["mode"] == m])
for m in modes:
    summary[f"all/{m}"] = eval_answers.summarize([r for r in data["answers"] if r["mode"] == m])
data["summary"] = summary
path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

print("Changed by rescoring:", *(changed or ["none"]), sep="\n  ")
for key, s in summary.items():
    print(f"{key:18} grounded {s['grounded_accuracy']:.3f}  ({round(s['grounded_accuracy'] * s['questions'])}/{s['questions']})  errors {s['errors']}")
