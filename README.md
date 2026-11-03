---
title: Echoes.ai — Interactive AI Museum Guide
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

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

### Option A: Run natively on your machine (Fastest)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env               # fill in your LLM API key and settings
```

Check the test questions and start the server:

```bash
python -m eval.datasets --check
uvicorn app.server:app --reload
```

Open http://localhost:8000 in your browser.

### Option B: Run with Docker

The container encapsulates all system dependencies (`ffmpeg`, `libsndfile1`, CPU PyTorch, spaCy):

```bash
# Build the image (~3.5 GB)
docker build -t echoes-ai .

# Run the container (reads API keys from .env)
docker run --rm -p 7860:7860 --env-file .env echoes-ai
```

Open http://localhost:7860 in your browser, or verify with:
```bash
curl http://localhost:7860/health
```

### Testing on a Real Phone (Microphone & Voice)

Browsers (especially iOS Safari and Android Chrome) **block microphone access on plain HTTP**. To test on a real phone, create a free, secure HTTPS tunnel to your machine using Cloudflare:

1. **Install Cloudflare Tunnel (`cloudflared`):**
   - **macOS:** `brew install cloudflared`
   - **Linux:** `sudo apt-get install cloudflared` (or download from Cloudflare releases)
   - **Windows:** `winget install --id Cloudflare.cloudflared`

2. **Start the tunnel in a separate terminal:**
   ```bash
   # If running natively on port 8000:
   cloudflared tunnel --url http://localhost:8000

   # Or if running Docker on port 7860:
   cloudflared tunnel --url http://localhost:7860
   ```

3. **Open the HTTPS URL on your phone:**
   Cloudflare outputs a link like `https://random-words.trycloudflare.com`. Open that URL on your phone browser. Microphone permissions will prompt normally.
   *(Note for iPhone users: Ensure your phone's physical Silent/Ringer switch is OFF so Safari plays Web Audio out loud).*

4. **Generate QR codes for testing exhibits:**
   ```bash
   python scripts/generate_qr.py --space-url https://random-words.trycloudflare.com
   ```
   This generates `artifacts/qr-t-rex.png` and `artifacts/qr-van-gogh.png` ready for printing or scanning.

## Deploy to Hugging Face Spaces

> **Note on HF Spaces:** Hugging Face Spaces Docker SDK is now a paid feature. As documented in [`artifacts/architecture.md`](artifacts/architecture.md) §4.6, our primary setup for hands-free user testing uses the local container / server paired with Cloudflare Tunnel. If you have a paid HF Spaces account, you can deploy using the `Dockerfile` at the repo root:

**One-time setup:**

1. Go to https://huggingface.co/spaces and create a new Space. When it asks for the SDK,
   choose **Docker**.
2. Add the Space as a second remote in your local clone:
   ```
   git remote add space https://huggingface.co/spaces/<your-org>/<your-space-name>
   ```
3. Under **Space Settings → Variables and secrets**, add these three secrets (not plain
   variables — secrets are hidden in logs and never visible after you save them):

   | Secret name   | What to put in it |
   |---------------|-------------------|
   | `LLM_API_KEY`   | Your API key (Groq, OpenAI, etc.) |
   | `LLM_BASE_URL`  | e.g. `https://api.groq.com/openai/v1` |
   | `LLM_MODEL`     | e.g. `openai/gpt-oss-120b` |

**Deploying:**

```bash
git push space main
```

The Space will build the Docker image and start the server automatically. The first build
takes 5–10 minutes because it downloads PyTorch and the Whisper model. Subsequent pushes
are faster because Docker caches the dependency layer.

**Checking it worked:**

Once the Space shows "Running", open `https://<your-space-url>/health` in a browser. You
should see both exhibits listed and `"status": "ok"`. Then open the root URL on your phone
— the microphone permission prompt should appear because the connection is HTTPS.

**QR codes for user tests:**

The QR codes in `artifacts/` point at the live Space URL. Print one and stick it next to
an exhibit for a hands-free user test. Scan the code, ask a question, get an answer.

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
python -m eval.eval_quotes             # are quotes really in Van Gogh's letters? (pipeline/quotes.py)
python -m eval.eval_stt                # speech to text word error rate and speed (needs recordings, see below)
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

Speech to text is scored on recordings of 40 held-out questions read aloud by teammates and
friends. The recordings stay in `data/stt_audio/` and are never committed; only the reference
text (`eval/questions/stt/reference.jsonl`) and the results are. See
`eval/questions/stt/README.md` for how to record them, then:

```bash
python -m eval.eval_stt --check        # which clips are still missing
python -m eval.eval_stt                # -> eval/results/stt_results.md and .json
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
4. The exhibit now appears on the phone page. Link a QR code to `/?persona=<id>`. Speech to
   text gets a vocabulary prompt built from its persona.json and passages automatically.

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
