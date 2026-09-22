# Data Sources

**Author:** Surabhi More  
**Date:** September 22, 2026  
**Status:** Draft v1. Corpus selection, evaluation design, and versioning plan. Data download and labelling commence in Session 5.  

---

## Overview

“Data” in this project means five distinct things, because the pipeline has five different places where data drives behaviour. This document covers all five, so every team member knows exactly what exists, what licence it carries, how to obtain it, and what its known problems are.

| # | What it feeds | Who owns it |
| --- | --- | --- |
| 1 | Exhibit knowledge base (RAG source documents) | Surabhi |
| 2 | Visitor eval set — labelled Q&A pairs | Surabhi |
| 3 | Faithfulness-detector training data | Surabhi |
| 4 | Persona style data (only if we fine-tune generation) | Saurabh / Surabhi |
| 5 | Session logs for user-study evidence | Kshiti |

---

## 1 Exhibit Knowledge Base (RAG Source Documents)

### Why we need our own data

We could let the model answer from what it already knows, but then nothing checks what it says. Models make up quotes and facts, especially when asked to play a real person. If the answers come from sources we collected, we can show the visitor where each answer came from and measure how often the answers are right. It also keeps us from being just a wrapper around someone else’s API, which the course guidelines rule out.

### Why we started with Van Gogh

People have a lot of questions about him. His letters to his brother are available in English and in the public domain, so the persona can answer in something close to his own words. Two museums with open data — the Met and the Art Institute of Chicago — own his paintings, and their object records are openly licenced. His life has clear dates (1853–1890), which makes it easy to test questions about things that happened after he died.

### Sources in use

| Source | What we get | Approx. size | Licence | Credit required |
| --- | --- | --- | --- | --- |
| [Letters of a Post-Impressionist](https://www.gutenberg.org/ebooks/40393), trans. Anthony M. Ludovici (Project Gutenberg) | His letters in English | ~57,000 words | Public domain (US) | None required; we will credit anyway |
| [Wikipedia — Vincent van Gogh](https://en.wikipedia.org/wiki/Vincent_van_Gogh) | Life story, dates, major works | ~10,800 words | CC BY-SA 4.0 | Must credit Wikipedia and link to article |
| [Art Institute of Chicago API](https://api.artic.edu/docs/) | Painting descriptions (*The Bedroom*, self-portrait, etc.) | 100-290 words per object | Descriptions CC BY 4.0; everything else CC0 | Must credit [artic.edu](http://artic.edu) |
| [Met Open Access](https://github.com/metmuseum/openaccess) | Catalog records: title, date, medium, gallery | 47 search results for Van Gogh | CC0 | Met asks for credit |

The letters are what the persona leans on most, because they are in Van Gogh’s own voice. Wikipedia fills in facts and dates. The museum descriptions cover questions about specific paintings.

### Sources we looked at and chose not to use

**Full Met dataset (484,956 artworks, 318 MB).** It has only catalog details — title, date, medium — with no prose descriptions, so it cannot answer “why did you paint this?” The file also exceeds GitHub’s 100 MB limit. We use it only for date and title lookups, not as a RAG source.

**[vangoghletters.org](http://vangoghletters.org)** (Van Gogh Museum / Huygens ING scholarly edition). This is the most complete and accurate version of the letters, but we have not confirmed re-use rights. We read it for context only; we do not copy its text.

**Model memory on its own.** There is no way to audit it.

### Known problems

-   **Translation chain.** The Gutenberg letters are Ludovici’s English translation of a German edition, not Van Gogh’s original Dutch and French. The book is also a selection, not a complete corpus. A matching quote means he wrote something close to it, not his exact words.
-   **Lexical gap.** The English is from the 1910s. Search must bridge the distance between a modern visitor’s phrasing and that vocabulary.
-   **Wikipedia drift.** Wikipedia changes. We will save the exact revision (URL with `oldid=`) and the download date.
-   **Uneven museum records.** One Art Institute painting we checked, *The Poet’s Garden*, has no description. A Met search for “Van Gogh” also returns things *about* him: one result is a 1937 book of his letters, listing him as author 47 years after he died. A naive “was he alive then?” check would fail on that.

### Storage and provenance

Each passage in the knowledge base carries:

```
source_name   | source_url       | licence   | downloaded_on | passage_id
```

The guide surface tells visitors which source an answer came from. We maintain a credits page for the Met, the Art Institute of Chicago, Wikipedia, and Project Gutenberg. None of these sources contain personal data.

---

## 2 Visitor Eval Set — Labelled Q&A Pairs

This is the dataset we build ourselves. It is the one that actually proves whether the hallucination detector works, so it deserves the most team hours. The eval set also provides the **grounded answer accuracy** number — the north-star metric from the lean canvas — measured against a plain “museum guide” baseline that answers the same questions without persona or RAG.

### What it contains

For each exhibit we write a battery of questions and then run the full pipeline to generate answers. A human labeller then tags each answer.

**Question types per exhibit**

| Type | Purpose | Example (Van Gogh) |
| --- | --- | --- |
| Factual | Tests date/title retrieval | “When was *The Bedroom* painted?” |
| Inferential | Tests reasoning over source text | “Why did Van Gogh use yellow so often?” |
| Persona-baiting | Tests in-character scope | “What is your favourite food?” |
| Adversarial | Tests fabrication on gaps | “What did you think of Monet’s *Water Lilies*?” (not in our source text) |
| Post-mortem | Tests temporal boundary | “What do you think of the 1956 film *Lust for Life* about your life?” |

Adversarial and post-mortem questions are the most important for the detector: they are designed to tempt the model into making things up.

**Answer labels**

| Label | Meaning |
| --- | --- |
| `grounded` | Every claim in the answer is supported by a sentence in our source documents |
| `partial` | Some claims are supported, others are not |
| `hallucinated` | One or more central claims contradict or are absent from our source documents |

Each labelled row also records the specific source passage (by `passage_id`) that supports or refutes the answer.

### Target size

Aiming for **200–250 labelled Q&A pairs** across all exhibits, split as follows:

| Split | Size | Purpose |
| --- | --- | --- |
| Development | ~150 pairs | Build and tune the detector prompt / classifier |
| Held-out test | ~75 pairs | Final reported numbers; no peeking during development |

For the Van Gogh pilot we target ~15 questions. The total of 200–250 pairs scales as additional personas are confirmed. At Draft v1, Van Gogh is the only confirmed exhibit.

### Label schema (full fields)

```
question_id       | exhibit_id        | question_text     | question_type
answer_text       | pipeline_version  | label             | label_confidence
supporting_passage_ids                | labeller_initials | labelled_on
notes
```

`label_confidence` is a 1–3 score (1 = uncertain, 3 = clear-cut). Pairs marked 1 get a second labeller.

### Inter-annotator agreement

At least two team members label a 20% random sample of the development set. We report Cohen’s κ. Disagreements are resolved by majority vote or by flagging as `partial`.

---

## 3 Faithfulness-Detector Training Data

If the detector is more than a prompted LLM judge — for example, a fine-tuned classifier — it needs labelled faithfulness data before it ever sees our museum examples. We use public datasets for this.

### Public datasets

| Dataset | What it contains | Size | Where to get it |
| --- | --- | --- | --- |
| [TRUE benchmark](https://arxiv.org/abs/2204.04991) | Aggregate of 11 faithfulness datasets; each row is (source, claim, label) | ~50,000 pairs | [GitHub](https://github.com/google-research/true) |
| [SummEval](https://arxiv.org/abs/2007.12626) | Human faithfulness ratings for CNN/DM summaries | 1,600 summaries × 23 systems | [GitHub](https://github.com/Yale-LILY/SummEval) |
| [FRANK benchmark](https://arxiv.org/abs/2104.13346) | Error-typed faithfulness annotations on summarisation | 2,250 pairs | [GitHub](https://github.com/artidoro/frank) |

These give thousands of labelled (source, claim, label) triples that are structurally identical to our task: “is this answer grounded in this passage?” Our 200-pair museum set then becomes the domain-adaptation / held-out test set, not the only training data.

### How we use them

1.  Fine-tune or few-shot prompt the detector on TRUE + SummEval, using an NLI-style model that classifies each (source passage, answer claim) pair as supported or contradicted.
2.  Evaluate on our held-out museum test split.
3.  Report both in-domain (TRUE test) and out-of-domain (museum) F1.

This framing gives us a meaningful generalisation story: the detector learned faithfulness in general, and we measure how well that transfers to the museum persona domain.

### Licence note

TRUE and SummEval are released for research use. Check the individual sub-dataset licences inside TRUE before any commercial use.

---

## 4 Persona Style Data (Only If We Fine-Tune Generation)

If we prompt a frontier API (GPT-4o, Claude, Gemini), we do not need persona training data — the system prompt handles style. This section applies only if we fine-tune a smaller open model.

### Options

| Source | What it provides | Licence |
| --- | --- | --- |
| [PersonaChat](https://arxiv.org/abs/1801.07243) | Persona-conditioned dialogue pairs | Research use (Meta AI) |
| Van Gogh letters (already in §1) | First-person voice, characteristic vocabulary | Public domain |
| Gold responses (hand-written) | 5–10 per exhibit, written by the team | Our own |

The letters give us authentic Van Gogh voice for the Van Gogh exhibit. For other exhibits we would need comparable primary-source text (historical diaries, speeches, published letters).

**Current decision:** defer fine-tuning. Use prompt-engineering with a frontier model for the initial version. Re-evaluate at the Session 6 checkpoint.

---

## 5 Session Logs for the User Study

Kshiti owns this stream. It is separate from the eval set. See `artifacts/user_research_plan.md` for how the tests are run.

### What we capture

With the participant’s permission, each session produces:

| Field / Artefact | Format | Retention |
| --- | --- | --- |
| `session_id` | UUID, no PII — participants are P1, P2, … | Permanent |
| `exhibit_id` | String | Permanent |
| `turn_count` | Integer | Permanent |
| `session_duration_s` | Float (sessions capped at 10–15 min) | Permanent |
| `raw_transcript` | JSON (utterance, role, timestamp) | Deleted after transcript extracted |
| `task_sheet` | Per-task completion, time, naturalness rating 1–5 | Permanent |
| `session_note` | Short written note: what happened, what we changed | Permanent |
| `screen_audio_recording` | Screen + voice capture (if consent given) | Deleted after transcript extracted |

No names, faces, or contact details are ever committed to the repo. Consent is verbal before recording starts. Raw audio is deleted once the transcript is extracted (target: within 2 weeks of the session).

### Target volume

| Phase | Participants | Cap per session | Total sessions | Purpose |
| --- | --- | --- | --- | --- |
| Pilot | 3–5 classmates or friends, not team members | 10–15 min | 3–5 | Formative — find usability breaks before the field round |
| Field validation | 12–15 campus gallery or museum visitors | 10–15 min | 12–15 | Summative — real visitor behaviour on the target audience |

Field participants are screened for one thing: whether they normally walk past exhibit plaques rather than stopping to read them.

### Where it goes in the repo

Each session is committed to `evidence/<session-name>/` the same week it happens, containing the recording (if consent was given), the Q&A log, the task sheet, and a session note. Nothing goes in `evidence/` until the product is running.

---

## Versioning and Download Plan

### Tools

-   **DVC** (Data Version Control) tracks large files without committing them to Git.
-   A script `scripts/download_sources.py` will fetch each source and drop it into the persona’s `sources/` folder with a manifest JSON recording URL, download date, and MD5 hash.
-   `scripts/build_corpus.py --persona <id>` (Saurabh’s script) then cleans and chunks the sources into `chunks.jsonl`. 
-   Wikipedia: use the `wikipedia` Python package with `page.revision_id` to pin the exact revision.
-   Art Institute of Chicago: store the raw API response JSON, not just the extracted text.
-   Met CSV: store only the 47-row filtered slice, not the full 318 MB file.

### Directory layout (target)

Source files and chunks live inside the persona folder, matching the architecture spec. Eval files, external detector-training data, and user-study evidence sit at the repo root.

```
personas/
  van-gogh/
    persona.json
    sources/
      gutenberg_letters.txt      # downloaded, do not edit
      wikipedia_vangogh.txt      # pinned revision (oldid= URL)
      aic_objects.json           # raw API responses
      met_vangogh_filtered.csv   # 47-row slice
    chunks.jsonl                 # 256-token chunks built by build_corpus.py

eval/
  questions.json                 # 20 automated benchmark queries (feeds score.py)
  dev_set.jsonl                  # ~150 human-labelled Q&A pairs (annotation set)
  test_set.jsonl                 # ~75 human-labelled Q&A pairs (held out)

evidence/
  README.md                      # Kshiti's guidelines for what goes here
  gallery-pilot/                 # one folder per test session
    recording.webm               # screen + audio (if consent given)
    qa_log.jsonl                 # product Q&A log for that session
    task_sheet.md                # filled-in task sheet
    session_note.md              # what happened, what we changed

data/
  external/
    true_benchmark/              # DVC-tracked
    summeval/                    # DVC-tracked
```

**Note on the two eval formats.** `eval/questions.json` (20 queries with gold answers) is the automated benchmark that Saurabh’s `score.py` runs against on every pipeline change — it measures Precision@5 and ROUGE-L automatically. `dev_set.jsonl` and `test_set.jsonl` are the larger human-labelled annotation set that Surabhi builds for the hallucination detector — they carry question type, three-way label, and supporting passage IDs. Both live in `eval/` but serve different purposes and should not be confused.

---

## Open Questions

1.  **[vangoghletters.org](http://vangoghletters.org) licence.** Can we use its text for research? If yes, replace the Ludovici translation entirely — the scholarly edition is more accurate and complete.
2.  **Second exhibit persona.** Van Gogh is the proof-of-concept. What is the second persona (likely needed for exhibit-to-exhibit generalisation in the eval)? Frida Kahlo and Ada Lovelace both have public-domain primary-source text available.
3.  **Fine-tune vs. prompt decision.** Finalise at the Session 6 checkpoint.

---

## Next Steps

1.  `scripts/download_sources.py` — downloads each source into `personas/van-gogh/sources/` with provenance metadata (URL, download date, MD5).
2.  Run `scripts/build_corpus.py --persona van-gogh` — cleans and chunks the sources into `personas/van-gogh/chunks.jsonl` at 256 tokens with 32-token overlap.
3.  Write 20 benchmark questions covering facts, post-lifetime events, quote requests, and off-topic traps; save to `eval/questions.json` to feed Saurabh’s `score.py`.
4.  Write the Van Gogh question battery (~15 questions across all five types), run the pipeline, and label answers into `eval/dev_set.jsonl`. Reserve 25% as `eval/test_set.jsonl` (held out, no peeking).
5.  Set up DVC for `data/external/true_benchmark` and `data/external/summeval`.