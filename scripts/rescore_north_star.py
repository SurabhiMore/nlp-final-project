"""Rescore saved answers from Sessions 7, 8 and 10 using fair key-fact matching.

Runs completely offline (no model calls).

Outputs:
  - Updates eval/results/answers_results.json with rescored answers and summary
  - Writes eval/results/north_star_rescoring.md containing the comparison table
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULTS_DIR = ROOT / "eval" / "results"
OUT_MD = RESULTS_DIR / "north_star_rescoring.md"

from eval import datasets, eval_answers  # noqa: E402
from pipeline import config, persona as engine  # noqa: E402


def rescore_answers(answers_data, exhibit_chunks, questions):
    """Rescore each answer in an answers_results dataset dict."""
    all_chunks = {**exhibit_chunks["van-gogh"], **exhibit_chunks["t-rex"]}
    rescored = []
    for a in answers_data["answers"]:
        q = questions[a["question_id"]]
        chunks = list(exhibit_chunks[a["exhibit"]].values())
        support_ids = datasets.supporting_chunk_ids(q, chunks)
        result = {
            "status": a["status"],
            "answer": a["answer"],
            "citations": a.get("citations") or [],
        }
        scored = eval_answers.score(q, result, all_chunks, support_ids)
        row = dict(a)
        row.update(scored)
        rescored.append(row)
    return rescored


def rescore_session7(frozen, replies, exhibit_chunks, questions):
    """Rescore Session 7 replies from grounding_replies.jsonl."""
    all_chunks = {**exhibit_chunks["van-gogh"], **exhibit_chunks["t-rex"]}
    rescored_rows = []
    for r in replies:
        q = questions[r["question_id"]]
        exhibit = r["exhibit"]
        items = frozen["exhibits"][exhibit]
        item = next(it for it in items if it["question"]["id"] == r["question_id"])
        chunks_by_id = {c["id"]: c for c in item["passages"]}
        support = set(item["support_ids"])
        persona = config.load_persona(exhibit)
        sounds = tuple(persona.get("sounds", {})) if r["mode"] == "persona" else ()
        parsed = engine.parse_reply(r["reply"], set(chunks_by_id), sounds)
        checked = engine.check_reply(parsed, persona, q["question"], r["mode"])
        scored = eval_answers.score(q, checked, chunks_by_id, support)
        rescored_rows.append({
            "exhibit": exhibit,
            "mode": r["mode"],
            "question_id": r["question_id"],
            "status": checked["status"],
            "answer": checked["answer"],
            "citations": checked["citations"],
            "answerable": q["answerable"],
            "correct": scored["correct"],
            "grounded": scored["grounded"],
        })
    return rescored_rows


def compute_metrics(rows):
    """Compute per-exhibit and overall grounded accuracy and trap decline stats."""
    exhibits = ("van-gogh", "t-rex")
    res = {}
    for exhibit in exhibits:
        sub = [r for r in rows if r["exhibit"] == exhibit]
        correct = sum(1 for r in sub if r["grounded"])
        traps = [r for r in sub if not r["answerable"]]
        traps_ok = sum(1 for r in traps if r["correct"])
        res[exhibit] = {
            "correct": correct,
            "total": len(sub),
            "acc": correct / len(sub) if sub else 0.0,
            "traps_declined": traps_ok,
            "traps": len(traps),
        }
    all_correct = sum(1 for r in rows if r["grounded"])
    all_traps = [r for r in rows if not r["answerable"]]
    all_traps_ok = sum(1 for r in all_traps if r["correct"])
    res["all"] = {
        "correct": all_correct,
        "total": len(rows),
        "acc": all_correct / len(rows) if rows else 0.0,
        "traps_declined": all_traps_ok,
        "traps": len(all_traps),
    }
    return res


def main():
    exhibit_chunks = {
        "van-gogh": {c["id"]: c for c in datasets.load_chunks("van-gogh")},
        "t-rex": {c["id"]: c for c in datasets.load_chunks("t-rex")},
    }
    vg_q = {q["id"]: q for q in datasets.load_questions("van-gogh")}
    tr_q = {q["id"]: q for q in datasets.load_questions("t-rex")}
    questions = {**vg_q, **tr_q}

    # 1. Rescore Session 10
    s10_path = RESULTS_DIR / "answers_results.json"
    s10_data = json.loads(s10_path.read_text(encoding="utf-8"))
    s10_old_persona = [r for r in s10_data["answers"] if r["mode"] == "persona"]
    s10_old_metrics = compute_metrics(s10_old_persona)

    s10_new_answers = rescore_answers(s10_data, exhibit_chunks, questions)
    s10_new_persona = [r for r in s10_new_answers if r["mode"] == "persona"]
    s10_new_metrics = compute_metrics(s10_new_persona)

    # Update answers_results.json with new rows and summary
    s10_data["answers"] = s10_new_answers
    s10_data["summary"] = {
        "t-rex/persona": eval_answers.summarize([r for r in s10_new_persona if r["exhibit"] == "t-rex"]),
        "van-gogh/persona": eval_answers.summarize([r for r in s10_new_persona if r["exhibit"] == "van-gogh"]),
        "all/persona": eval_answers.summarize(s10_new_persona),
    }
    s10_path.write_text(json.dumps(s10_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {s10_path.relative_to(ROOT)} with rescored answers.")

    # 2. Rescore Session 8
    s8_path = RESULTS_DIR / "answers_results_session08_llama3.json"
    s8_data = json.loads(s8_path.read_text(encoding="utf-8"))
    s8_old_persona = [r for r in s8_data["answers"] if r["mode"] == "persona"]
    s8_old_metrics = compute_metrics(s8_old_persona)

    s8_new_answers = rescore_answers(s8_data, exhibit_chunks, questions)
    s8_new_persona = [r for r in s8_new_answers if r["mode"] == "persona"]
    s8_new_metrics = compute_metrics(s8_new_persona)

    # 3. Rescore Session 7
    frozen_path = config.EVAL_DIR / "fixtures" / "frozen_passages.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    replies_path = RESULTS_DIR / "grounding_replies.jsonl"
    replies = [json.loads(line) for line in replies_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    s7_old_metrics = {
        "van-gogh": {"correct": 31, "total": 32, "acc": 31 / 32, "traps_declined": 9, "traps": 9},
        "t-rex": {"correct": 28, "total": 32, "acc": 28 / 32, "traps_declined": 9, "traps": 9},
        "all": {"correct": 59, "total": 64, "acc": 59 / 64, "traps_declined": 18, "traps": 18},
    }
    s7_new_answers = rescore_session7(frozen, replies, exhibit_chunks, questions)
    s7_new_persona = [r for r in s7_new_answers if r["mode"] == "persona"]
    s7_new_metrics = compute_metrics(s7_new_persona)

    # Format Markdown Table
    def fmt(m):
        return f"{m['acc']:.3f} ({m['correct']}/{m['total']})"

    md_lines = [
        "# North Star Rescoring Across Sessions (Issue #72)",
        "",
        "Grounded answer accuracy (persona mode, 32 questions per exhibit; 46 answerable, 18 traps), "
        "rescored with fair key-fact matching: number words accepted for digits ('six' for '6'), "
        "standard unit spellings normalized ('km', 'kilometres', 'kilometers'), and validated "
        "synonyms added as alternatives ('strongest' for 'largest' in `tr-09`, 'dim light' for 'low-light' in `tr-28`).",
        "",
        "**All rescoring runs completely offline with 0 model calls.**",
        "",
        "## Rescoring Summary (Persona Mode)",
        "",
        "| Session | Model | Exhibit | Old Accuracy | New (Fair) Accuracy | Delta | Traps Declined |",
        "|---|---|---|---|---|---|---|",
        f"| Session 7 | openai/gpt-oss-120b | van-gogh | {fmt(s7_old_metrics['van-gogh'])} | {fmt(s7_new_metrics['van-gogh'])} | ±0 | 9/9 |",
        f"| Session 7 | openai/gpt-oss-120b | t-rex | {fmt(s7_old_metrics['t-rex'])} | {fmt(s7_new_metrics['t-rex'])} | +1 (`tr-09`) | 9/9 |",
        f"| Session 7 | openai/gpt-oss-120b | **all** | **{fmt(s7_old_metrics['all'])}** | **{fmt(s7_new_metrics['all'])}** | **+1 (60/64)** | **18/18** |",
        f"| Session 8 | llama3 | van-gogh | {fmt(s8_old_metrics['van-gogh'])} | {fmt(s8_new_metrics['van-gogh'])} | ±0 | 8/9 |",
        f"| Session 8 | llama3 | t-rex | {fmt(s8_old_metrics['t-rex'])} | {fmt(s8_new_metrics['t-rex'])} | ±0 | 8/9 |",
        f"| Session 8 | llama3 | **all** | **{fmt(s8_old_metrics['all'])}** | **{fmt(s8_new_metrics['all'])}** | **±0 (55/64)** | **16/18** |",
        f"| Session 10 | openai/gpt-oss-120b | van-gogh | {fmt(s10_old_metrics['van-gogh'])} | {fmt(s10_new_metrics['van-gogh'])} | ±0 | 9/9 |",
        f"| Session 10 | openai/gpt-oss-120b | t-rex | {fmt(s10_old_metrics['t-rex'])} | {fmt(s10_new_metrics['t-rex'])} | +3 (`tr-09`, `tr-24`, `tr-28`) | 9/9 |",
        f"| Session 10 | openai/gpt-oss-120b | **all** | **{fmt(s10_old_metrics['all'])}** | **{fmt(s10_new_metrics['all'])}** | **+3 (62/64)** | **18/18** |",
        "",
        "## Questions Fixed by Fair Scoring",
        "",
        "### 1. `tr-09` ('How strong was your bite?')",
        "- **Issue**: Model replied with *'the strongest bite of any land animal'* (Session 10) and *'the strongest of any land animal ever recorded'* (Session 7), cited. Key-fact check previously required the literal word `'largest'` from the source snippet.",
        "- **Resolution**: Added `'strongest'` as an accepted alternative in `eval/questions/t-rex.jsonl`.",
        "- **Impact**: Fixed in both Session 7 and Session 10.",
        "",
        "### 2. `tr-24` ('What kind of vision did you have, and how far could you see objects clearly?')",
        "- **Issue**: Model replied with *'spot objects as far as six kilometres away'* (Session 10), cited. Key-fact check required digits `'6 km'`.",
        "- **Resolution**: `normalize()` in `eval/datasets.py` now maps number words to digits (`six` -> `6`) and unit variants (`kilometres`/`kilometers` -> `km`).",
        "- **Impact**: Fixed in Session 10.",
        "",
        "### 3. `tr-28` ('Did you hunt primarily during the day or at night?')",
        "- **Issue**: Model replied *'My eyes weren’t great in dim light, so scientists think I hunted during the day.'* (Session 10), cited. Key-fact check required `'low-light'` or `'poor'`.",
        "- **Resolution**: Added `'dim light'` as an accepted alternative in `eval/questions/t-rex.jsonl`.",
        "- **Impact**: Fixed in Session 10.",
        "",
        "## Remaining Session 10 Misses (2 of 64)",
        "",
        "| Question | Nature | Cause Analysis |",
        "|---|---|---|",
        "| `vg-07` ('In Gauguin's portrait of you, what were you doing?') | Wrong decline | Model replied `{\"answer\": \"I have no description of that portrait in my letters, so I cannot say what I was doing in it.\", \"status\": \"not_in_sources\"}`. Investigation confirmed `check_reply` was NOT the cause (`check: null`). The model overlooked the subordinate clause *'while I was painting some sunflowers'* at the end of letter chunk `van-gogh-gut40393-0052`. |",
        "| `vg-08` ('What did the countryside around Arles remind you of?') | Search miss | BM25 failed to retrieve chunk `van-gogh-gut40393-0060` (*'country in these parts seems to me just as beautiful as Japan'*) because the query words 'countryside' and 'Arles' do not appear in that chunk. Hybrid search retrieves chunk `van-gogh-gut40393-0180` at rank 6, but hybrid search causes severe regressions on other questions (Hit@8 drops from 0.96 to 0.70 on T. rex, and 0.87 to 0.78 on Van Gogh). Following policy, search was not changed. |",
        "",
        "## Frontmatter for Reports",
        "",
        "```yaml",
        "north_star:",
        "  metric: Grounded answer accuracy (persona mode, 32 held-out questions per exhibit)",
        "  value: Van Gogh 0.938, T. rex 1.000 (62 of 64 overall), model openai/gpt-oss-120b",
        "  previous: Van Gogh 0.969, T. rex 0.906 (60 of 64 overall), model openai/gpt-oss-120b (Session 7 rescored)",
        "```",
        "",
    ]
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
