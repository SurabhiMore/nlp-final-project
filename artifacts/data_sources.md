# Data Sources

**Author:** Surabhi More  
**Date:** September 29, 2026  
**Status:** Draft v2. Corpora for our two test exhibits (Van Gogh and T. rex) are built with `scripts/build_corpus.py`, and the first held-out question sets are written and checked.  

---

## Overview

"Data" in this project means five distinct things, because the pipeline has five different places where data drives behaviour. This document covers all five, so every team member knows exactly what exists, what licence it carries, how to obtain it, and what its known problems are.

| # | What it feeds | Who owns it |
| --- | --- | --- |
| 1 | Exhibit knowledge base (RAG source documents) | Surabhi |
| 2 | Visitor eval set: held-out questions and labelled answers | Surabhi |
| 3 | Faithfulness-detector training data | Surabhi |
| 4 | Persona style data (only if we fine-tune generation) | Saurabh / Surabhi |
| 5 | Session logs for user-study evidence | Kshiti |

---

## 1 Exhibit Knowledge Base (RAG Source Documents)

### Why we need our own data

We could let the model answer from what it already knows, but then nothing checks what it says. Models make up quotes and facts, especially when asked to play a real person. If the answers come from sources we collected, we can show the visitor where each answer came from and measure how often the answers are right. It also keeps us from being just a wrapper around someone else's API, which the course guidelines rule out.

### Why two very different exhibits

The system is meant to work for any exhibit, so we test it on two that have very different kinds of sources:

- **Vincent van Gogh**, a person who left his own writing. His letters are available in English and in the public domain, so the persona can answer in something close to his own words. Two museums with open data, the Met and the Art Institute of Chicago, own his paintings. His life has clear dates (1853 to 1890), which makes it easy to test questions about things that happened after he died.
- **Tyrannosaurus rex**, a creature with no words of its own. Everything we know comes from scientists and museums, so the persona has to speak as a character built from expert facts and be honest about what is still debated. Its time (about 69 to 66 million years ago) gives a very different boundary to test.

If the same code and the same build script handle both, that is our evidence that adding an exhibit only needs a new `persona.json`.

### Sources in use: Van Gogh

| Source | What we get | Size in our corpus | Licence | Credit required |
| --- | --- | --- | --- | --- |
| [Letters of a Post-Impressionist](https://www.gutenberg.org/ebooks/40393), trans. Anthony M. Ludovici (Project Gutenberg) | His letters to Theo and to Emile Bernard | About 38,500 words of letters (252 passages) | Public domain (US) | None required; we credit it anyway |
| [Wikipedia: Vincent van Gogh](https://en.wikipedia.org/wiki/Vincent_van_Gogh) | Life story, dates, major works | About 11,600 words (71 passages) | CC BY-SA 4.0 | Must credit Wikipedia and link to the article |
| [Art Institute of Chicago API](https://api.artic.edu/docs/) | Painting descriptions (*The Bedroom*, a self-portrait and others) | 18 works by him, 9 with descriptions (10 passages) | Descriptions CC BY 4.0; everything else CC0 | Must credit [artic.edu](https://www.artic.edu) |
| [Met Open Access API](https://metmuseum.github.io/) | Catalog records: title, date, medium, dimensions | 47 search results, 30 by him (30 passages) | CC0 | The Met asks for credit |

The letters are what the persona leans on most, because they are in Van Gogh's own voice. Wikipedia fills in facts and dates. The museum records cover questions about specific paintings.

### Sources in use: T. rex

| Source | What we get | Size in our corpus | Licence | Credit required |
| --- | --- | --- | --- | --- |
| [Wikipedia: Tyrannosaurus](https://en.wikipedia.org/wiki/Tyrannosaurus) | Discovery, size, anatomy, diet, the scientific debates | About 15,800 words (109 passages) | CC BY-SA 4.0 | Must credit Wikipedia and link to the article |
| [Smithsonian Open Access](https://www.si.edu/openaccess) | Fossil specimen records (where and when found, rock formation, age) and tooth casts on display | 58 search results, 24 kept (24 passages) | CC0, checked on every record | Credit the Smithsonian |

We keep only the National Museum of Natural History's paleobiology and education records whose title names *Tyrannosaurus rex*. The rest of the search results were library catalogue entries for books (including a pop-up book), plus records for tyrannosaur relatives that lived earlier than T. rex, which would let the persona claim fossils that are not its own.

### How the corpus is built

`python scripts/build_corpus.py --persona <id>` reads the source list in `personas/<id>/persona.json`, downloads each source, cleans it, and splits it into passages of about 250 tokens (around 190 words), repeating the last sentence of each passage at the start of the next so facts are not cut in half. The same script builds both exhibits with no changes.

For the Gutenberg book, `persona.json` lists the book's parts by heading. We keep only the four sections of letters and mark them `own_words: true`. We drop the title page, the translator's 1,100-line introductory essay, his preface and his notes, because none of that is Van Gogh writing and the persona is only allowed to quote passages marked as its own words.

### Sources we looked at and chose not to use

**Full Met dataset (484,956 artworks, 318 MB).** It has only catalog details (title, date, medium) with no prose descriptions, so it cannot answer "why did you paint this?" The file also exceeds GitHub's 100 MB limit. We use the Met API for the 30 Van Gogh records instead.

**[vangoghletters.org](https://vangoghletters.org)** (Van Gogh Museum and Huygens ING scholarly edition). This is the most complete and accurate version of the letters, but we have not confirmed re-use rights. We read it for context only and do not copy its text.

**Model memory on its own.** There is no way to audit it.

### Known problems

-   **Translation chain.** The Gutenberg letters are Ludovici's English translation of a German edition, not Van Gogh's original Dutch and French. The book is also a selection, not a complete corpus. A matching quote means he wrote something close to it, not his exact words.
-   **Lexical gap.** The English is from the 1910s. Search must bridge the distance between a modern visitor's phrasing and that vocabulary. Our BM25 baseline misses questions like "How heavy could you get?" because the source says "mass" and "tons", which is the main case for adding meaning-based search.
-   **Wikipedia drift.** Wikipedia changes. The build records the exact revision (a URL with `oldid=`) and the download date for every passage.
-   **Uneven museum records.** One Art Institute painting, *The Poet's Garden*, has no description. A Met search for "Van Gogh" also returns things about him, not only by him: one result is a 1937 book of his letters, listing him as author 47 years after he died. A naive "was he alive then?" check would fail on that.
-   **Download formats.** Project Gutenberg has no plain-text file for book #40393, so the build falls back to the HTML edition. The Wikipedia text for T. rex also contained a leaked citation fragment, so the build strips footnote marks and citation debris.
-   **Uncertain science.** For T. rex, running speed, feathers and hunting versus scavenging are all debated. The sources describe the debate, and the persona must repeat that uncertainty instead of picking one answer.

### Storage and provenance

Each passage in `personas/<id>/chunks.jsonl` carries:

```
id | persona_id | text | source | source_type | section | own_words | url | licence | retrieved
```

The raw downloads and a `manifest.json` (URL, revision, download date and MD5 hash for each source) are saved in `personas/<id>/sources/`, which is not committed. `personas/<id>/corpus_stats.json`, which is committed, records how many passages and words came from each source.

The guide tells visitors which source an answer came from: every answer on the phone page lists its passages with a link to the original and the licence. The README has a credits section for Project Gutenberg, Wikipedia, the Art Institute of Chicago, the Met and the Smithsonian. None of these sources contain personal data.

---

## 2 Visitor Eval Set: Held-out Questions and Labelled Answers

This is the dataset we build ourselves. It is the one that actually proves whether the guide stays grounded, so it deserves the most team hours. It also provides the **grounded answer accuracy** number, the north-star metric from the lean canvas, measured against a plain "museum guide" baseline that gets the same retrieved passages but no persona. Comparing the two tells us whether speaking in character makes the answers less accurate.

### Question types per exhibit

| Type | Purpose | Example |
| --- | --- | --- |
| Factual and dates | Tests retrieval of facts | "When did you arrive in Arles?" |
| Painting and why | Tests reasoning over museum text | "What feeling did you want The Bedroom to give?" |
| Quote | Tests the persona's own words | "What did the countryside around Arles remind you of?" |
| Outside its time | Tests the time boundary | "Did you enjoy the 1956 film Lust for Life about your life?", "Did you ever see a human?" |
| Not in the sources | Tests fabrication on gaps | "How much money did you get for The Red Vineyard?" (true, but in none of our sources) |
| Off topic | Tests staying on topic | "What is the capital of France?" |

Outside-its-time and not-in-the-sources questions are the most important: they are designed to tempt the model into making things up. Some of them are harder than they look. The Van Gogh Wikipedia article does mention the 1956 film and his later fame, and the T. rex article mentions Jurassic Park, so the guide has to decline even though a passage contains the information.

### What we built in Session 5

`eval/questions/van-gogh.jsonl` and `eval/questions/t-rex.jsonl`, 22 questions each (15 and 16 answerable, 7 and 6 traps), written before looking at any model answers. Each line has:

```
id | question | type | answerable | gold_answer | key_facts | evidence | notes
```

`evidence` is exact text copied from the sources. We store evidence text instead of passage ids because passage ids change whenever the corpus is rebuilt with different settings. The supporting passages are worked out from the evidence each time an evaluation runs. `key_facts` are the facts a correct answer must contain. Each key fact is a list of accepted wordings, so "three" and "3" both count.

One change after writing: in trial runs on a different model, correct answers to "Were you a hunter or a scavenger?" said "hunter" or "predation" rather than "predator", so we added both as accepted wordings for that key fact. No question or gold answer was changed. The hand check exists to catch the cases where exact wording still marks a correct answer wrong.

`python -m eval.datasets --check` confirms that every evidence string really is in the sources and that the key facts appear in both the supporting passages and the gold answer. Both files currently pass with no problems.

### Answer labels

Each automatically scored answer can be hand-labelled in `eval/results/handcheck.csv`:

| Label | Meaning |
| --- | --- |
| `grounded` | Every claim in the answer is supported by a cited source passage |
| `partial` | Some claims are supported, others are not |
| `hallucinated` | One or more central claims contradict or are absent from our sources |
| `declined_ok` | A trap question, correctly declined |
| `declined_wrong` | Declined a question the sources can answer |

`python -m eval.eval_answers --score-handcheck eval/results/handcheck.csv` reports how often the automatic check agrees with our labels, with Cohen's kappa.

### Target size

Aiming for **200 to 250 labelled Q&A pairs** across all exhibits, split as follows:

| Split | Size | Purpose |
| --- | --- | --- |
| Development | ~150 pairs | Build and tune the detector prompt or classifier |
| Held-out test | ~75 pairs | Final reported numbers; no peeking during development |

We now have 44 questions across two exhibits. The rest grow as we add question batches and further exhibits.

### Inter-annotator agreement

At least two team members label a 20% random sample of the development set. We report Cohen's kappa. Disagreements are resolved by majority vote or by flagging as `partial`.

---

## 3 Faithfulness-Detector Training Data

If the detector is more than a prompted LLM judge, for example a fine-tuned classifier, it needs labelled faithfulness data before it ever sees our museum examples. We plan to use public datasets for this in Sessions 7 to 9.

### Public datasets

| Dataset | What it contains | Where to get it |
| --- | --- | --- |
| [TRUE benchmark](https://arxiv.org/abs/2204.04991) | 11 existing factual-consistency datasets in one format; each row is a (source, claim, label) pair | [GitHub](https://github.com/google-research/true) |
| [SummEval](https://arxiv.org/abs/2007.12626) | Human faithfulness ratings for CNN/DailyMail summaries | [GitHub](https://github.com/Yale-LILY/SummEval) |
| [FRANK benchmark](https://arxiv.org/abs/2104.13346) | Error-typed faithfulness annotations on summaries | [GitHub](https://github.com/artidoro/frank) |

We will record the exact size of each once downloaded rather than quoting estimates.

These give thousands of labelled (source, claim, label) examples that are structurally the same as our task: "is this answer grounded in this passage?" Our museum set then becomes the domain-adaptation and held-out test set, not the only training data.

### How we use them

1.  Start with a ready-made NLI model, and fine-tune or few-shot prompt it on TRUE and SummEval if it needs it, classifying each (source passage, answer claim) pair as supported or not.
2.  Evaluate on our held-out museum test split.
3.  Report both in-domain (TRUE test) and out-of-domain (museum) F1.

This gives us a generalisation story: the detector learned faithfulness in general, and we measure how well that transfers to the museum persona domain.

### Licence note

TRUE and SummEval are released for research use. Check the individual sub-dataset licences inside TRUE before any commercial use.

---

## 4 Persona Style Data (Only If We Fine-Tune Generation)

If we prompt a hosted model, we do not need persona training data, because the system prompt handles style. This section applies only if we fine-tune a smaller open model.

### Options

| Source | What it provides | Licence |
| --- | --- | --- |
| [PersonaChat](https://arxiv.org/abs/1801.07243) | Persona-conditioned dialogue pairs | Research use (Meta AI) |
| Van Gogh letters (already in section 1) | First-person voice, characteristic vocabulary | Public domain |
| Gold responses (hand-written) | 5 to 10 per exhibit, written by the team | Our own |

The letters give us an authentic Van Gogh voice. Exhibits without their own writing, like T. rex, rely on the prompt and on hand-written gold responses instead.

**Current decision:** defer fine-tuning. Use prompting for the initial version. Re-evaluate at the Session 6 checkpoint.

---

## 5 Session Logs for the User Study

Kshiti owns this stream. It is separate from the eval set. See `artifacts/user_research_plan.md` for how the tests are run.

### What we capture

With the participant's permission, each session produces:

| Field / Artefact | Format | Retention |
| --- | --- | --- |
| `session_id` | Random id with no personal data; participants are P1, P2, and so on | Permanent |
| `exhibit_id` | String | Permanent |
| `turn_count` | Integer | Permanent |
| `session_duration_s` | Float (sessions capped at 10 to 15 minutes) | Permanent |
| `raw_transcript` | JSON (utterance, role, timestamp) | Deleted after the transcript is extracted |
| `task_sheet` | Per-task completion, time, naturalness rating 1 to 5 | Permanent |
| `session_note` | Short written note: what happened, what we changed | Permanent |
| `screen_audio_recording` | Screen and voice capture (if consent is given) | Deleted after the transcript is extracted |

No names, faces or contact details are ever committed to the repo. Consent is verbal before recording starts. Raw audio is deleted once the transcript is extracted (target: within 2 weeks of the session). The server's request log (`logs/qa_log.jsonl`) is not committed either; only anonymized extracts go into the evidence folder.

### Target volume

| Phase | Participants | Cap per session | Total sessions | Purpose |
| --- | --- | --- | --- | --- |
| Pilot | 3 to 5 classmates or friends, not team members | 10 to 15 min | 3 to 5 | Formative: find usability breaks before the field round |
| Field validation | 12 to 15 campus gallery or museum visitors | 10 to 15 min | 12 to 15 | Summative: real visitor behaviour on the target audience |

Field participants are screened for one thing: whether they normally walk past exhibit plaques rather than stopping to read them.

### Where it goes in the repo

Each session is committed to `artifacts/evidence/<session>/` the same week it happens, containing the recording (if consent was given), the Q&A log, the task sheet and a session note.

---

## Versioning and Download Plan

### Tools

-   `scripts/build_corpus.py --persona <id>` downloads every source listed in `persona.json` into `personas/<id>/sources/` with a manifest (URL, revision, download date, MD5 hash), then cleans and chunks them into `chunks.jsonl`. It replaces the separate download script planned in v1.
-   `--offline` rebuilds `chunks.jsonl` from the saved downloads without touching the network.
-   **DVC** (Data Version Control) is planned for the large external detector datasets in Sessions 7 to 9. It is not set up yet.

### Directory layout

```
personas/
  van-gogh/
    persona.json                 # exhibit settings and source list
    chunks.jsonl                 # passages, committed
    corpus_stats.json            # passage and word counts per source, committed
    sources/                     # raw downloads and manifest.json, not committed
  t-rex/
    (same files)

eval/
  questions/
    van-gogh.jsonl               # held-out questions with gold answers and evidence
    t-rex.jsonl
  results/
    retrieval_results.json       # search metrics
    answers_results.json         # grounded answer accuracy, persona vs neutral
    handcheck.csv                # sample for hand labelling
    latency_results.json         # timing for each step

artifacts/evidence/
  README.md                      # Kshiti's guidelines for what goes here
  session05/                     # one folder per test session

data/external/                   # detector datasets (planned, DVC-tracked)
```

---

## Open Questions

1.  **[vangoghletters.org](https://vangoghletters.org) licence.** Can we use its text for research? If yes, we could replace the Ludovici translation, since the scholarly edition is more accurate and complete.
2.  **Third exhibit.** Resolved for now: T. rex is our second exhibit. A third should be a different kind again, for example an object such as a painting or a ship, to test the `object` type. Its sources must be public domain or openly licensed.
3.  **Fine-tune vs. prompt decision.** Finalise at the Session 6 checkpoint.

---

## Next Steps

1.  Add a second batch of questions per exhibit, aimed at the questions search currently misses.
2.  Label the hand-check sample from the first answer evaluation and report agreement with the automatic check.
3.  Split the labelled pairs into development and held-out test sets once there are enough.
4.  Download the detector datasets and set up DVC for them (Sessions 7 to 9).
