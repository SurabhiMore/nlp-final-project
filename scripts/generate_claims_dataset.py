"""Build eval/claims_labels.jsonl: the labelled dataset for the claim checker.

Sources:
1. All answered replies in eval/results/grounding_replies.jsonl (88 rows).
2. All answered questions from Session 7 user tests in artifacts/evidence/session07/ (5 rows).
3. Perturbed answers created from supported answers by changing exactly one date,
   number/quantity, or proper name (30 rows: 10 dates, 10 numbers, 10 names).

Each row contains:
- id: unique identifier
- source: "grounding_replies", "session07", or "perturbed"
- is_perturbed: bool
- exhibit: "t-rex" or "van-gogh"
- mode: "persona" or "neutral"
- question_id: question id or session test id
- question: the question text
- answer: the answer text
- citations: list of passage chunk ids cited
- has_unsupported: bool (True if the answer contains any detail not in cited passages)
- unsupported_details: list of strings (each unsupported detail, empty if supported)
- perturbation_type: "date" | "number" | "name" | null
- original_value: str | null
- perturbed_value: str | null
"""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eval import datasets

def main():
    vg_chunks = {c["id"]: c for c in datasets.load_chunks("van-gogh")}
    tr_chunks = {c["id"]: c for c in datasets.load_chunks("t-rex")}
    vg_q = {q["id"]: q for q in datasets.load_questions("van-gogh")}
    tr_q = {q["id"]: q for q in datasets.load_questions("t-rex")}

    rows = []

    # 1. Grounding replies (88 answered replies)
    # Grounding replies containing unsupported details:
    # - tr-04 (both modes): mentions "Henry Fairfield Osborn" while t-rex-si-0014 only contains "Osborn, 1905"
    # - tr-14 (neutral): mentions "Smithsonian" while t-rex-si-0004 only says "Education and Outreach collection"
    # - vg-06 (neutral): mentions "Paul Gauguin" while van-gogh-wiki-0030 only says "Gauguin"
    # - vg-27 (both modes): mentions "in Arles" while van-gogh-wiki-0031 only describes the Yellow House without naming Arles
    grounding_unsupported = {
        ("t-rex", "persona", "tr-04"): ["Henry Fairfield Osborn"],
        ("t-rex", "neutral", "tr-04"): ["Henry Fairfield Osborn"],
        ("t-rex", "neutral", "tr-14"): ["Smithsonian"],
        ("van-gogh", "neutral", "vg-06"): ["Paul Gauguin"],
        ("van-gogh", "persona", "vg-27"): ["Arles"],
        ("van-gogh", "neutral", "vg-27"): ["Arles"],
    }

    grounding_path = ROOT / "eval" / "results" / "grounding_replies.jsonl"
    with open(grounding_path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            d = json.loads(line)
            reply = json.loads(d["reply"])
            if reply.get("status") != "answered":
                continue
            qid = d["question_id"]
            ex = d["exhibit"]
            mode = d["mode"]
            qmap = vg_q if ex == "van-gogh" else tr_q
            qtext = qmap[qid]["question"] if qid in qmap else ""

            key = (ex, mode, qid)
            unsupported = grounding_unsupported.get(key, [])
            has_unsupported = len(unsupported) > 0

            row = {
                "id": f"grounding-{ex}-{mode}-{qid}",
                "source": "grounding_replies",
                "is_perturbed": False,
                "exhibit": ex,
                "mode": mode,
                "question_id": qid,
                "question": qtext,
                "answer": reply.get("answer", ""),
                "citations": reply.get("citations", []),
                "has_unsupported": has_unsupported,
                "unsupported_details": unsupported,
                "perturbation_type": None,
                "original_value": None,
                "perturbed_value": None,
            }
            rows.append(row)

    # 2. Session 7 user test answers
    session07_answers = [
        {
            "id": "session07-P2-q1",
            "source": "session07",
            "is_perturbed": False,
            "exhibit": "van-gogh",
            "mode": "persona",
            "question_id": "P2-q1",
            "question": "Did you move to Arles?",
            "answer": "Yes, I moved often, for example I signed a lease in Arles in May 1888 and lived there in the Yellow House, and I later moved to Auvers-sur-Oise in 1890.",
            "citations": ["van-gogh-wiki-0050", "van-gogh-wiki-0027"],
            "has_unsupported": True,
            "unsupported_details": ["Auvers-sur-Oise", "1890"],
            "perturbation_type": None,
            "original_value": None,
            "perturbed_value": None,
        },
        {
            "id": "session07-P2-q3",
            "source": "session07",
            "is_perturbed": False,
            "exhibit": "t-rex",
            "mode": "persona",
            "question_id": "P2-q3",
            "question": "How welcome you smell.",
            "answer": "My nose was huge and packed with powerful olfactory bulbs, giving me a sense of smell as keen as modern vultures, able to sniff out carcasses from far away.",
            "citations": ["t-rex-wiki-0082", "t-rex-wiki-0083", "t-rex-wiki-0092"],
            "has_unsupported": False,
            "unsupported_details": [],
            "perturbation_type": None,
            "original_value": None,
            "perturbed_value": None,
        },
        {
            "id": "session07-P3-q3",
            "source": "session07",
            "is_perturbed": False,
            "exhibit": "t-rex",
            "mode": "persona",
            "question_id": "P3-q3",
            "question": "for your teeth",
            "answer": "My teeth were a mix of chisel‑like front incisors and robust, banana‑shaped teeth behind, some up to 30.5 cm long, with ridges and a backward curve to keep them from snapping when I bit down.",
            "citations": ["t-rex-wiki-0014", "t-rex-wiki-0013"],
            "has_unsupported": False,
            "unsupported_details": [],
            "perturbation_type": None,
            "original_value": None,
            "perturbed_value": None,
        },
        {
            "id": "session07-P4-q1",
            "source": "session07",
            "is_perturbed": False,
            "exhibit": "van-gogh",
            "mode": "persona",
            "question_id": "P4-q1",
            "question": "Did you die?",
            "answer": "Yes, I died in July 1890, as recorded in the letters about my final days.",
            "citations": ["van-gogh-gut40393-0251"],
            "has_unsupported": True,
            "unsupported_details": ["July 1890"],
            "perturbation_type": None,
            "original_value": None,
            "perturbed_value": None,
        },
        {
            "id": "session07-P4-q3",
            "source": "session07",
            "is_perturbed": False,
            "exhibit": "t-rex",
            "mode": "persona",
            "question_id": "P4-q3",
            "question": "on the back.",
            "answer": "My back was made of thirteen vertebrae, part of a sturdy torso column.",
            "citations": ["t-rex-wiki-0016"],
            "has_unsupported": False,
            "unsupported_details": [],
            "perturbation_type": None,
            "original_value": None,
            "perturbed_value": None,
        },
    ]
    rows.extend(session07_answers)

    # 3. Perturbed answers (30 rows, created from supported grounding replies)
    grounding_by_key = {(r["exhibit"], r["mode"], r["question_id"]): r for r in rows if r["source"] == "grounding_replies"}

    perturbations = [
        # 10 Dates
        ("t-rex", "persona", "tr-01", "69 to 66 million years ago", "85 to 80 million years ago", "date", "85 to 80 million years ago"),
        ("t-rex", "neutral", "tr-01", "69 to 66 million years ago", "85 to 80 million years ago", "date", "85 to 80 million years ago"),
        ("t-rex", "persona", "tr-05", "1900", "1925", "date", "1925"),
        ("t-rex", "neutral", "tr-05", "1900", "1932", "date", "1932"),
        ("t-rex", "persona", "tr-06", "August 12, 1990", "November 18, 1995", "date", "November 18, 1995"),
        ("t-rex", "neutral", "tr-06", "August 12, 1990", "April 5, 1982", "date", "April 5, 1982"),
        ("van-gogh", "persona", "vg-01", "1853", "1865", "date", "1865"),
        ("van-gogh", "neutral", "vg-01", "1853", "1868", "date", "1868"),
        ("van-gogh", "persona", "vg-04", "February 1888", "April 1891", "date", "April 1891"),
        ("van-gogh", "persona", "vg-14", "1889", "1894", "date", "1894"),
        # 10 Numbers
        ("t-rex", "persona", "tr-07", "12.3–12.4\u202fmetres", "16.5–16.8\u202fmetres", "number", "16.5 m"),
        ("t-rex", "neutral", "tr-07", "12.3–12.4\u202fmetres", "17.2–17.5\u202fmetres", "number", "17.2 m"),
        ("t-rex", "persona", "tr-08", "8.8\u202ftons", "14.5\u202ftons", "number", "14.5 t"),
        ("t-rex", "neutral", "tr-08", "8.8 tons", "15.2 tons", "number", "15.2 t"),
        ("t-rex", "persona", "tr-10", "two clawed fingers", "four clawed fingers", "number", "four"),
        ("t-rex", "neutral", "tr-10", "two clawed fingers", "five clawed fingers", "number", "five"),
        ("t-rex", "persona", "tr-11", "4.5–6.8\u202fm/s", "12.5–15.8\u202fm/s", "number", "12.5"),
        ("t-rex", "neutral", "tr-11", "4.5–6.8 meters per second", "14.2–18.5 meters per second", "number", "14.2 m"),
        ("t-rex", "persona", "tr-15", "28 years old", "55 years old", "number", "55"),
        ("van-gogh", "persona", "vg-12", "three versions", "seven versions", "number", "seven"),
        # 10 Names
        ("t-rex", "persona", "tr-02", "Laramidia", "Gondwana", "name", "Gondwana"),
        ("t-rex", "neutral", "tr-02", "Laramidia", "Pangaea", "name", "Pangaea"),
        ("t-rex", "persona", "tr-05", "Barnum Brown", "Roy Chapman Andrews", "name", "Roy Chapman Andrews"),
        ("t-rex", "neutral", "tr-05", "eastern Wyoming", "northern Alberta", "name", "Alberta"),
        ("t-rex", "persona", "tr-06", "Sue Hendrickson", "Mary Anning", "name", "Mary Anning"),
        ("t-rex", "persona", "tr-16", "Hell Creek Formation", "Morrison Formation", "name", "Morrison Formation"),
        ("t-rex", "neutral", "tr-16", "Hell Creek Formation", "Cedar Mountain Formation", "name", "Cedar Mountain Formation"),
        ("van-gogh", "persona", "vg-03", "Paris", "London", "name", "London"),
        ("van-gogh", "persona", "vg-05", "The Potato Eaters", "Water Lilies", "name", "Water Lilies"),
        ("van-gogh", "persona", "vg-11", "Yellow House", "Blue Studio", "name", "Blue Studio"),
    ]

    for ex, mode, qid, orig_sub, pert_sub, ptype, detail in perturbations:
        base_row = grounding_by_key.get((ex, mode, qid))
        if not base_row:
            print(f"Warning: base row not found for ({ex}, {mode}, {qid})")
            continue
        orig_answer = base_row["answer"]
        if orig_sub not in orig_answer:
            print(f"Warning: {orig_sub!r} not in answer for ({ex}, {mode}, {qid})")
            continue
        pert_answer = orig_answer.replace(orig_sub, pert_sub, 1)
        row = {
            "id": f"perturbed-{ex}-{mode}-{qid}",
            "source": "perturbed",
            "is_perturbed": True,
            "exhibit": ex,
            "mode": mode,
            "question_id": qid,
            "question": base_row["question"],
            "answer": pert_answer,
            "citations": base_row["citations"],
            "has_unsupported": True,
            "unsupported_details": [detail],
            "perturbation_type": ptype,
            "original_value": orig_sub,
            "perturbed_value": pert_sub,
        }
        rows.append(row)

    out_path = ROOT / "eval" / "claims_labels.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Saved {len(rows)} labelled rows to {out_path}")
    real_rows = [r for r in rows if not r["is_perturbed"]]
    pert_rows = [r for r in rows if r["is_perturbed"]]
    print(f"  Real rows: {len(real_rows)} ({sum(1 for r in real_rows if r['has_unsupported'])} unsupported, {sum(1 for r in real_rows if not r['has_unsupported'])} fully supported)")
    print(f"  Perturbed rows: {len(pert_rows)} (all {len(pert_rows)} unsupported)")

if __name__ == "__main__":
    main()
