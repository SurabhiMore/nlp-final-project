"""Print the numbers for the weekly report straight from eval/results/.

    python scripts/report_numbers.py

Copying numbers by hand is how reports end up not matching the repo, so the
metrics section of the report should be filled from this output. Any results
file that has not been generated yet is reported as missing.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"


def load(name):
    path = RESULTS / name
    if not path.exists():
        print(f"\n{name}: missing (run the script that makes it first)")
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n{name} (run at {data.get('run_at', '?')})")
    return data


def fmt(value, digits=2):
    return "-" if value is None else f"{value:.{digits}f}"


def retrieval():
    data = load("retrieval_results.json")
    if not data:
        return
    print(f"  retriever: {data.get('retriever', '?')}")
    for exhibit, result in sorted(data["exhibits"].items()):
        s = result["summary"]
        print(f"  {exhibit:10} questions {s['questions']:>3}  Hit@1 {fmt(s['hit@1'])}  Hit@5 {fmt(s['hit@5'])}  "
              f"Hit@8 {fmt(s.get('hit@8'))}  Recall@5 {fmt(s['recall@5'])}  MRR@10 {fmt(s['mrr@10'])}")


def answers():
    data = load("answers_results.json")
    if not data:
        return
    print(f"  model: {data.get('model')}   passages per question: {data.get('passages_per_question')}")
    for key, s in data["summary"].items():
        traps = s["trap_questions"]
        declined = round((s["decline_accuracy"] or 0) * traps)
        print(f"  {key:18} grounded accuracy {fmt(s['grounded_accuracy'])} "
              f"({round(s['grounded_accuracy'] * s['questions'])} of {s['questions']})  "
              f"answerable {fmt(s['grounded_on_answerable'])}  traps declined {declined} of {traps}  "
              f"errors {s.get('errors', 0)}")
    if str(data.get("model", "")).startswith("offline"):
        print("  WARNING: made with the offline test stand-in, not a real model. Do not report these.")
    failed = sum(1 for a in data.get("answers", []) if a.get("status") == "error")
    if failed:
        print(f"  WARNING: {failed} calls failed in this run. Rerun eval_answers before reporting.")


def latency():
    data = load("latency_results.json")
    if not data:
        return
    print(f"  whisper model: {data.get('whisper_model')}   language model: {data.get('llm')}   "
          f"questions: {len(data.get('questions', []))}")
    s = data["summary"]
    for step in ("stt_ms", "retrieval_ms", "llm_ms", "tts_first_ms", "time_to_first_audio_ms"):
        v = s[step]
        print(f"  {step:24} median {v['median'] / 1000:5.1f} s   p90 {v['p90'] / 1000:5.1f} s   "
              f"max {v['max'] / 1000:5.1f} s")
    print(f"  mean word error rate: {fmt(s.get('mean_wer'))}")
    if str(data.get("llm", "")).startswith("offline"):
        print("  WARNING: made with the offline test stand-in, not a real model. Do not report these.")
    if data.get("llm") == "none":
        print("  NOTE: this run skipped the language model (--no-llm), so it is not the full delay.")


def main():
    if not RESULTS.exists():
        sys.exit("eval/results/ does not exist yet.")
    retrieval()
    answers()
    latency()
    print("\nHand check agreement and kappa: run  python -m eval.eval_answers --score-handcheck eval/results/handcheck.csv")


if __name__ == "__main__":
    main()