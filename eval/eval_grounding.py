"""Before and after the reply check (issue #28), on the same questions, passages and model replies.

    python -m eval.eval_grounding --freeze        # once: save the passages search returns today
    python -m eval.eval_grounding --collect       # ask the model once per question and mode (needs .env)
    python -m eval.eval_grounding                 # score before and after from the saved replies (offline)

Why three steps:

  --freeze   writes eval/fixtures/frozen_passages.json: every held-out question, the
             passages search gives the model for it (TOP_K, same as the server) and
             the passages that support it. Both sides use this file, so changes to
             search (for example issue #31) cannot move these numbers.
  --collect  sends each question with its frozen passages to the model and saves the
             raw reply in eval/results/grounding_replies.jsonl. Use --sleep on a free
             tier and --resume to finish a stopped run.
  (default)  reads each saved reply twice: "before" with the reply handling on main
             before this change (commit 3bc6f54, copied below), "after" with
             pipeline.persona.parse_reply + check_reply. The prompt did not change, so
             both sides score the very same model reply, and the difference is only
             the check. This step makes no model calls, so anyone can rerun it.

Outputs, in eval/results/:
  grounding_before_after.json   every reply scored both ways, and the summary
  grounding_before_after.md     the tables and every question whose result changed

Metrics, for each side:
  grounded_accuracy        as in eval_answers.py (our north-star metric)
  answer_accuracy          answerable questions answered with every key fact
  decline_accuracy         trap questions declined
  unnecessary_declines     answerable questions declined although a supporting passage was given
  unsupported_text_shown   declined answerable questions whose shown text still states the answer
                           (the model answered from its own knowledge with nothing to cite)
  uncited_answers_shown    status "answered" shown with no valid citation
  unreadable_replies_shown replies that were not valid JSON, shown to the visitor as raw text
  crashes                  replies the reply handling could not process at all
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval import datasets  # noqa: E402
from eval.eval_answers import TOP_K, score, summarize  # noqa: E402
from pipeline import config, persona as engine  # noqa: E402

FROZEN_PATH = config.EVAL_DIR / "fixtures" / "frozen_passages.json"
RESULTS_DIR = config.EVAL_DIR / "results"
REPLIES_PATH = RESULTS_DIR / "grounding_replies.jsonl"
OUT_JSON = RESULTS_DIR / "grounding_before_after.json"
OUT_MD = RESULTS_DIR / "grounding_before_after.md"
MODES = ("persona", "neutral")
CHUNK_FIELDS = ("id", "text", "source", "section", "own_words", "url", "licence", "score", "rank")
QUESTION_FIELDS = ("id", "question", "type", "answerable", "gold_answer", "key_facts")


# ---------------------------------------------------------------- the reply handling before #28

def parse_reply_before(text, allowed_ids, allowed_sounds=()):
    """pipeline.persona.parse_reply as it was on main at commit 3bc6f54, unchanged."""
    obj = None
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text or "", re.S)
        if match:
            try:
                obj = json.loads(match.group(0))
            except json.JSONDecodeError:
                obj = None
    if not isinstance(obj, dict):
        return {"answer": (text or "").strip(), "status": "answered", "citations": [],
                "invalid_citations": [], "sound": None, "parse_error": True}

    answer_text = str(obj.get("answer", "")).strip()
    status = str(obj.get("status", "")).strip().lower()
    if status not in engine.STATUSES:
        status = "answered" if answer_text else "declined"
    raw = obj.get("citations") or []
    if isinstance(raw, str):
        raw = [raw]
    cited, invalid = [], []
    for item in raw:
        cid = str(item).strip().strip("[]")
        if cid in allowed_ids:
            if cid not in cited:
                cited.append(cid)
        else:
            invalid.append(cid)
    sound = str(obj.get("sound") or "").strip().lower()
    return {"answer": answer_text, "status": status, "citations": cited, "invalid_citations": invalid,
            "sound": sound if sound in allowed_sounds else None}


def handle_before(reply, persona, question, mode, allowed_ids):
    sounds = tuple(persona.get("sounds", {})) if mode == "persona" else ()
    try:
        return parse_reply_before(reply, allowed_ids, sounds)
    except Exception as error:  # on main this reached the server as a 502
        return {"answer": "", "status": "error", "citations": [], "invalid_citations": [], "sound": None,
                "crash": f"{type(error).__name__}: {error}"}


def handle_after(reply, persona, question, mode, allowed_ids):
    sounds = tuple(persona.get("sounds", {})) if mode == "persona" else ()
    return engine.check_reply(engine.parse_reply(reply, allowed_ids, sounds), persona, question, mode)


# ---------------------------------------------------------------- step 1: freeze the passages

def _git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=config.ROOT,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def freeze(path=FROZEN_PATH):
    from pipeline.retrieve import retrieve

    exhibits = {}
    for file in datasets.question_files():
        exhibit = file.stem
        chunks = datasets.load_chunks(exhibit)
        items = []
        for q in datasets.load_questions(exhibit):
            passages = retrieve(exhibit, q["question"], k=TOP_K)
            items.append({
                "question": {key: q[key] for key in QUESTION_FIELDS},
                "passages": [{key: c[key] for key in CHUNK_FIELDS if key in c} for c in passages],
                "support_ids": sorted(datasets.supporting_chunk_ids(q, chunks)),
            })
        exhibits[exhibit] = items
    frozen = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "commit": _git_commit(), "passages_per_question": TOP_K, "exhibits": exhibits}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(frozen, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(items) for items in exhibits.values())
    print(f"Froze {total} questions with {TOP_K} passages each to {path.relative_to(config.ROOT)}")


def load_frozen(path=FROZEN_PATH):
    if not path.exists():
        sys.exit(f"{path.relative_to(config.ROOT)} is missing. Run: python -m eval.eval_grounding --freeze")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- step 2: collect model replies

def load_replies(path=REPLIES_PATH):
    replies = {}
    if not path.exists():
        return replies
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:  # a line cut off when a run was stopped mid-write; --resume asks again
            continue
        replies[(row["exhibit"], row["mode"], row["question_id"])] = row
    return replies


def collect(frozen, modes, sleep=0.0, resume=False, limit=None):
    s = engine.settings()
    if s["provider"] == "offline" or not (s["base_url"] and s["model"]):
        sys.exit("--collect needs a language model. Set LLM_BASE_URL and LLM_MODEL in .env (see .env.example).")
    done = {k: v for k, v in load_replies().items() if v["model"] == s["model"]} if resume else {}
    if not resume:
        REPLIES_PATH.unlink(missing_ok=True)
    print(f"Model: {s['model']}   already saved: {len(done)}", flush=True)
    failures_in_a_row = 0
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for exhibit, items in frozen["exhibits"].items():
        persona = config.load_persona(exhibit)
        for item in items[:limit]:
            q = item["question"]
            for mode in modes:
                if (exhibit, mode, q["id"]) in done:
                    continue
                start = time.perf_counter()
                try:
                    reply = engine._call_llm(engine.build_messages(persona, q["question"], item["passages"], mode), s)
                except Exception as error:  # one failed call should not end a long run
                    failures_in_a_row += 1
                    print(f"  FAIL {exhibit:9} {mode:8} {q['id']:6} {error}"[:160], flush=True)
                    if failures_in_a_row >= 3:
                        sys.exit("Stopped: 3 calls in a row failed. Run again with --collect --resume to finish.")
                    continue
                failures_in_a_row = 0
                row = {"exhibit": exhibit, "mode": mode, "question_id": q["id"], "model": s["model"],
                       "reasoning_effort": s["reasoning_effort"], "temperature": s["temperature"],
                       "llm_ms": round((time.perf_counter() - start) * 1000), "reply": reply}
                with open(REPLIES_PATH, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(f"  ok   {exhibit:9} {mode:8} {q['id']:6} {reply[:70]!r}", flush=True)
                if sleep:
                    time.sleep(sleep)
    print(f"Saved replies to {REPLIES_PATH.relative_to(config.ROOT)}")


# ---------------------------------------------------------------- step 3: score before and after

def score_side(handle, reply_row, item, persona):
    q = item["question"]
    chunks_by_id = {c["id"]: c for c in item["passages"]}
    support = set(item["support_ids"])
    result = handle(reply_row["reply"], persona, q["question"], reply_row["mode"], set(chunks_by_id))
    row = {
        "answerable": q["answerable"], "status": result["status"], "answer": result["answer"],
        "citations": result["citations"], "invalid_citations": result.get("invalid_citations") or [],
        "llm_ms": reply_row.get("llm_ms", 0), "check": result.get("check"),
        "parse_error": bool(result.get("parse_error")), "crash": result.get("crash"),
    }
    row.update(score(q, result, chunks_by_id, support))
    declined = result["status"] in engine.DECLINED_STATUSES
    row["unnecessary_decline"] = bool(q["answerable"] and declined and support & set(chunks_by_id))
    row["unsupported_text_shown"] = bool(
        q["answerable"] and declined and datasets.key_facts_present(result["answer"], q["key_facts"]))
    # Before the check, an unreadable reply went to the visitor as raw text. After it, it is replaced.
    row["unreadable_reply_shown"] = bool(result.get("parse_error")) and result.get("check") != "unreadable_reply"
    return row


def summarize_side(rows):
    summary = summarize(rows)
    summary["unnecessary_declines"] = sum(r["unnecessary_decline"] for r in rows)
    summary["unsupported_text_shown"] = sum(r["unsupported_text_shown"] for r in rows)
    summary["uncited_answers_shown"] = summary.pop("answered_without_citation")
    summary["unreadable_replies_shown"] = sum(r["unreadable_reply_shown"] for r in rows)
    summary["crashes"] = sum(1 for r in rows if r.get("crash"))
    checks = {}
    for r in rows:
        if r.get("check"):
            checks[r["check"]] = checks.get(r["check"], 0) + 1
    summary["changed_by_check"] = checks
    return summary


def evaluate(frozen, replies):
    rows = []
    for exhibit, items in frozen["exhibits"].items():
        persona = config.load_persona(exhibit)
        for item in items:
            q = item["question"]
            for mode in MODES:
                reply_row = replies.get((exhibit, mode, q["id"]))
                if reply_row is None:
                    continue
                rows.append({
                    "exhibit": exhibit, "mode": mode, "question_id": q["id"], "question": q["question"],
                    "type": q["type"], "answerable": q["answerable"], "gold_answer": q["gold_answer"],
                    "support_in_passages": bool(set(item["support_ids"]) & {c["id"] for c in item["passages"]}),
                    "reply": reply_row["reply"],
                    "before": score_side(handle_before, reply_row, item, persona),
                    "after": score_side(handle_after, reply_row, item, persona),
                })
    groups = {}
    for r in rows:
        for key in (f"{r['exhibit']}/{r['mode']}", f"all/{r['mode']}", "all"):
            groups.setdefault(key, []).append(r)
    summary = {key: {side: summarize_side([r[side] for r in group]) for side in ("before", "after")}
               for key, group in sorted(groups.items())}
    return rows, summary


METRICS = [
    ("grounded_accuracy", "Grounded answer accuracy", "higher"),
    ("answer_accuracy", "Answerable questions answered correctly", "higher"),
    ("decline_accuracy", "Trap questions declined", "higher"),
    ("unnecessary_declines", "Unnecessary declines (support was in the passages)", "lower"),
    ("unsupported_text_shown", "Declines that still state the answer without a source", "lower"),
    ("uncited_answers_shown", "Answers shown with no valid citation", "lower"),
    ("unreadable_replies_shown", "Unreadable replies shown as raw text", "lower"),
    ("invalid_citations", "Invalid citation ids sent by the model (all removed)", "info"),
    ("crashes", "Replies that crashed the reply handling", "lower"),
]


def _fmt(value):
    return "-" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)


def write_markdown(frozen, replies, rows, summary, path=OUT_MD):
    models = sorted({r["model"] for r in replies.values()})
    n_questions = sum(len(items) for items in frozen["exhibits"].values())
    lines = [
        "# Reply check: before and after (issue #28)",
        "",
        f"- Questions: {n_questions} held-out questions frozen at commit {frozen['commit']} "
        f"({frozen['created_at']}), {frozen['passages_per_question']} passages each, "
        "from `eval/fixtures/frozen_passages.json`",
        f"- Model replies: {len(replies)} from {', '.join(models)}, one per question and mode, "
        "in `eval/results/grounding_replies.jsonl`",
        "- Before and after score the same replies. Before is the reply handling on main at 3bc6f54; "
        "after adds `check_reply` in `pipeline/persona.py`.",
        "- Reproduce: `python -m eval.eval_grounding` (no model calls). "
        "Fresh replies: `--collect`, then the same command.",
        "",
    ]
    for key in ["all", "all/persona", "all/neutral"] + [k for k in summary if k.count("/") and not k.startswith("all")]:
        if key not in summary:
            continue
        before, after = summary[key]["before"], summary[key]["after"]
        lines += [f"## {key} ({before['questions']} replies)", "", "| Metric | Before | After | Better is |",
                  "|---|---|---|---|"]
        lines += [f"| {label} | {_fmt(before[m])} | {_fmt(after[m])} | {better} |" for m, label, better in METRICS]
        changed = ", ".join(f"{k} {v}" for k, v in sorted(after["changed_by_check"].items())) or "none"
        lines += ["", f"Changed by the check: {changed}.", ""]

    changed_rows = [r for r in rows if (r["before"]["status"], r["before"]["answer"], r["before"]["grounded"])
                    != (r["after"]["status"], r["after"]["answer"], r["after"]["grounded"])]
    lines += ["## Every reply the check changed", ""]
    if not changed_rows:
        lines += ["None.", ""]
    else:
        lines += ["| Exhibit | Mode | Question | Answerable | Rule | Before (status: shown text) | After | "
                  "Grounded before → after |", "|---|---|---|---|---|---|---|---|"]
        for r in changed_rows:
            b, a = r["before"], r["after"]
            cell = lambda side: f"{side['status']}: {side['answer'][:90]}".replace("|", "/").replace("\n", " ")
            lines.append(f"| {r['exhibit']} | {r['mode']} | {r['question_id']}: {r['question']} | "
                         f"{'yes' if r['answerable'] else 'no'} | {a['check']} | {cell(b)} | {cell(a)} | "
                         f"{b['grounded']} → {a['grounded']} |")
        lines.append("")
    regressions = [r for r in rows if r["before"]["grounded"] and not r["after"]["grounded"]]
    lines += ["## Regressions (grounded before, not after)", ""]
    lines += [f"- {r['exhibit']} {r['mode']} {r['question_id']}: {r['question']} ({r['after']['check']})"
              for r in regressions] or ["None."]
    remaining = [r for r in rows if not r["after"]["grounded"]]
    lines += ["", "## Still wrong after the check", "",
              "| Exhibit | Mode | Question | Status | Support in passages | Why (automatic) |", "|---|---|---|---|---|---|"]
    for r in remaining:
        a = r["after"]
        if a["unnecessary_decline"]:
            why = "declined although a supporting passage was given"
        elif r["answerable"] and a["status"] in engine.DECLINED_STATUSES:
            why = "declined; search did not give a supporting passage"
        elif r["answerable"] and not a["facts_in_answer"]:
            why = "answer is missing a key fact (may be wording; check by hand)"
        elif r["answerable"]:
            why = "cited passages do not contain the answer"
        else:
            why = "answered a trap question"
        lines.append(f"| {r['exhibit']} | {r['mode']} | {r['question_id']}: {r['question']} | {a['status']} | "
                     f"{'yes' if r['support_in_passages'] else 'no'} | {why} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Before and after the reply check, on frozen passages.")
    parser.add_argument("--freeze", action="store_true", help="save today's search results for every question")
    parser.add_argument("--collect", action="store_true", help="ask the model and save its raw replies")
    parser.add_argument("--resume", action="store_true", help="with --collect: keep replies already saved")
    parser.add_argument("--sleep", type=float, default=0.0, help="with --collect: seconds between calls")
    parser.add_argument("--limit", type=int, help="with --collect: only the first N questions per exhibit")
    parser.add_argument("--modes", default="persona,neutral", help="with --collect: comma-separated modes")
    args = parser.parse_args()

    if args.freeze:
        freeze()
        return
    frozen = load_frozen()
    if args.collect:
        collect(frozen, [m.strip() for m in args.modes.split(",") if m.strip()], args.sleep, args.resume, args.limit)
    replies = load_replies()
    if not replies:
        sys.exit("No saved replies yet. Run: python -m eval.eval_grounding --collect")
    rows, summary = evaluate(frozen, replies)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"frozen_commit": frozen["commit"], "summary": summary, "replies": rows},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(frozen, replies, rows, summary)

    print(f"\n{'':26} {'before':>8} {'after':>8}")
    for metric, label, _ in METRICS:
        print(f"{metric:26} {_fmt(summary['all']['before'][metric]):>8} {_fmt(summary['all']['after'][metric]):>8}")
    print(f"\nSaved {OUT_JSON.relative_to(config.ROOT)} and {OUT_MD.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
