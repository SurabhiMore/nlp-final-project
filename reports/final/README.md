# Echoes.ai: talk to the exhibit

Our final submission for DATA/MSML 641. This is the outline from November 16 (#74). The final
numbers, the slides and the recorded demo are added after the Session 12 run.

## What it is

A voice guide for museums. A visitor scans the QR code next to an exhibit, asks a question out
loud on their phone, and the exhibit answers in its own voice, citing the sources it used. When
the sources don't cover a question, it says so instead of guessing. The same code runs two very
different exhibits: Vincent van Gogh, who left his own letters, and a Tyrannosaurus rex, known
only through what scientists have written. Curators get a page that shows what visitors ask.

## Team

| Name | Role |
|---|---|
| Pratham Bharati | Product |
| Saurabh Gujar | Engineering |
| Surabhi More | Data and evaluation |
| Kshiti Deshpande | Users and research |
| Aditi Karanjkar | Operations |

## Live link

There is no permanent public link. We could not host Whisper and Kokoro for free: Docker Spaces on
Hugging Face now need a paid plan, and the other free options either have too little memory or
need a credit card (section 4.6 of [`artifacts/architecture.md`](../../artifacts/architecture.md)).
We chose not to spend money, so we run it on a laptop. For phones, a free Cloudflare tunnel gives a temporary https link, and
`scripts/generate_qr.py` makes the QR codes for it.

## Set it up

You need Python 3.10, 3.11 or 3.12 (on a Mac, check `python3.12 --version`).

```bash
git clone https://github.com/SurabhiMore/nlp-final-project.git
cd nlp-final-project
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
```

Then add a language model to `.env`. We report numbers for `openai/gpt-oss-120b` on Groq's free
tier, which is also the model in the demo. Make a free key at https://console.groq.com/keys and set:

```bash
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your-key
LLM_MODEL=openai/gpt-oss-120b
LLM_REASONING_EFFORT=low
```

Start it with `uvicorn app.server:app` and open http://localhost:8000. To try it without a key,
set `LLM_PROVIDER=offline`. Docker, phones through the tunnel, and troubleshooting are in the
[main README](../../README.md).

## In this folder

- [`report.md`](report.md): the final report
- slides: added after Session 12
- `demo.mp4`: the recorded demo, added after Session 12

## Where the evidence is

- [`eval/results/`](../../eval/results/): every evaluation result
- [`artifacts/evidence/`](../../artifacts/evidence/): raw records from the user tests
- [`reports/`](../): the weekly reports
- [`tests/results/`](../../tests/results/): the test report for every pull request
- [`artifacts/demo_script.md`](../../artifacts/demo_script.md): the demo plan
