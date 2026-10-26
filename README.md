# Company Name - Echoes.ai

## Project Name - Interactive AI Museum

_We help museum visitors discover and understand exhibits through interactive conversations, better, faster, and more engagingly than static audio guides and exhibit plaques._


| Member  | Hat                            | Main Responsibility                                                 |
| --------- | -------------------------------- | --------------------------------------------------------------------- |
| Pratham | Developer, Product             | The user, the roadmap, the lean canvas, the pitch                   |
| Saurabh | Developer, Engineering         | Architecture, code review, repo health, deployment                  |
| Surabhi | Developer, Data and Evaluation | Data and licensing, the evaluation harness, metrics, error analysis |
| Kshiti  | Developer, Users and Research  | Recruiting users, running sessions, capturing the raw evidence      |
| Aditi   | Developer, Operations          | Planning, the board, the weekly report, keeping the repo honest     |

## What it does

A visitor scans a QR code next to an exhibit, asks a question out loud on their phone, and
hears the exhibit answer: a painter, a dinosaur, or any other exhibit we set up. Answers come
only from the exhibit's sources (letters, museum records, Wikipedia), each answer cites where
it came from, and the guide says so when its sources do not cover a question.

```
voice -> speech to text (Whisper) -> search the exhibit's passages (BM25) -> answer from those passages (LLM) -> speech (Kokoro)
```

Our two test exhibits are Vincent van Gogh (a person, with his own letters) and
Tyrannosaurus rex (a creature, with only expert sources). The same code runs both.

## Run it locally

Needs Python 3.10 to 3.12 (Kokoro does not install on Python 3.13; `av` is pinned to `<19` and `preshed` to `<3.0.14` in `requirements.txt`).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in the language model settings
```

The first run downloads the speech models (a few hundred MB) and Kokoro may download a
small English language model. After that everything runs offline except the language model.

Each exhibit's passages are already in the repo (`personas/<id>/chunks.jsonl`), so you can
check the test questions and start the server straight away:

```bash
python -m eval.datasets --check
uvicorn app.server:app --reload
```

Open http://localhost:8000 on the same computer. Browsers only allow the microphone on
`localhost` or on an https site, so to test on a phone, open an https tunnel to your laptop
(for example `cloudflared tunnel --url http://localhost:8000`) and use the link it prints.

To rebuild the passages from the sources, run `python scripts/build_corpus.py --all`. This
downloads the latest version of each source, so if Wikipedia has changed, the passages and
the numbers in `eval/results/` can shift a little. After one online build, `--offline`
rebuilds from the downloads saved in `personas/<id>/sources/` (these stay on your computer and
are not committed).

## Measure it

```bash
python -m eval.eval_retrieval          # does search find the right passages?
python -m eval.eval_answers            # grounded answer accuracy, persona vs plain guide
python -m eval.compare_modes           # is the gap between persona and plain guide real or chance?
python -m eval.eval_grounding          # reply check before and after, on frozen passages (see the script)
python scripts/measure_latency.py      # how long each step takes
```

Results are written to `eval/results/` and are what the weekly reports quote.

Search is also scored on held-out T-Rex questions (`eval/questions/heldout/`) that were written
before search was tuned and are never used to choose terminology mappings. To reproduce the
before/after search comparison (issue #31):

```bash
python -m eval.eval_retrieval                                   # main questions -> retrieval_results.json
python -m eval.eval_retrieval --questions-dir eval/questions/heldout --out retrieval_results_heldout.json
python -m eval.compare_retrieval \
  --set "Main questions" eval/results/retrieval_baseline.json eval/results/retrieval_results.json \
  --set "Held-out questions" eval/results/retrieval_baseline_heldout.json eval/results/retrieval_results_heldout.json \
  --out eval/results/retrieval_comparison.md
```

The baseline files were produced by the same commands with `--out retrieval_baseline*.json`
on the code before the change.

Search supports three modes via `SEARCH_MODE` (`bm25`, `dense`, or `hybrid`; defaults to `bm25`):

```bash
# Evaluate each search mode
python -m eval.eval_retrieval --mode bm25 --out retrieval_bm25.json
python -m eval.eval_retrieval --mode dense --out retrieval_dense.json
python -m eval.eval_retrieval --mode hybrid --out retrieval_hybrid.json

# Compare BM25 vs Hybrid
python -m eval.compare_retrieval \
  --set "Main questions" eval/results/retrieval_bm25.json eval/results/retrieval_hybrid.json \
  --set "Held-out questions" eval/results/retrieval_bm25_heldout.json eval/results/retrieval_hybrid_heldout.json \
  --out eval/results/hybrid_search_comparison.md
```

Run the tests with `python -m pytest` (see `tests/README.md`).

## Add a new exhibit (no code changes)

1. Create `personas/<id>/persona.json` (copy one of the existing ones). Set the name, the type
   (`person`, `creature`, `object` or `place`), the time period, how it speaks, a Kokoro voice
   (with an optional `pitch` below 1 for a deeper voice), optional sounds it can play when asked
   (the T. rex roars), and its sources (Project Gutenberg, Wikipedia, Art Institute of Chicago,
   the Met, or the Smithsonian).
2. Run `python scripts/build_corpus.py --persona <id>`.
3. Add test questions in `eval/questions/<id>.jsonl` and run `python -m eval.datasets --check`.
4. The exhibit now appears on the phone page. Link a QR code to `/?persona=<id>`.

## Repo layout

```
app/          server.py and the phone page (app/static/)
pipeline/     config, speech to text, search, answer engine, text to speech
personas/     one folder per exhibit: persona.json, chunks.jsonl, corpus_stats.json
scripts/      corpus builder, latency measurement, user test log export, report numbers, roar
eval/         test questions, evaluation scripts, results
artifacts/    lean canvas, roadmap, architecture, data sources, research plan, evidence
reports/      weekly reports
```

## Sources and credits

Every answer on the phone page lists the passages it came from, with a link to the original
and its licence. The sources we use:

- Vincent van Gogh, *The Letters of a Post-Impressionist*, translated by Anthony M. Ludovici,
  from [Project Gutenberg](https://www.gutenberg.org/ebooks/40393). Public domain in the US.
- Wikipedia articles [Vincent van Gogh](https://en.wikipedia.org/wiki/Vincent_van_Gogh) and
  [Tyrannosaurus](https://en.wikipedia.org/wiki/Tyrannosaurus), under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Each passage links to the
  exact revision we used.
- Artwork descriptions from the [Art Institute of Chicago](https://www.artic.edu), under
  CC BY 4.0.
- Collection records from [The Metropolitan Museum of Art](https://www.metmuseum.org) Open
  Access (CC0).
- Specimen records from [Smithsonian Open Access](https://www.si.edu/openaccess) (CC0).
- The T. rex roar: "Epic T-Rex Roaring Sound Effect - Powerful Dinosaur" by PWLPL, from
  [Pixabay](https://pixabay.com/sound-effects/nature-epic-t-rex-roaring-sound-effect-powerful-dinosaur-444199/),
  under the Pixabay Content License. It is AI-generated, not a recording.

None of these institutions endorse this project. Details and known problems with each source
are in `artifacts/data_sources.md`.
