---
team: Echoes.ai
session: 09
date: 2026-11-03
members:
  - name: Pratham Bharati
    github: prathambharati
    hat: Product
  - name: Saurabh Gujar
    github: saurabh1712
    hat: Engineering
  - name: Surabhi More
    github: SurabhiMore
    hat: Data&Eval
  - name: Kshiti Deshpande
    github: kshitideshpande
    hat: Users&Research
  - name: Aditi Karanjkar
    github: aditik168
    hat: Operations
north_star:
  metric: Grounded answer accuracy (persona mode, 32 held-out questions per exhibit)
  value: Not rerun this session (eval_answers needs live Groq calls). Last measured in Session 08, Van Gogh 0.844, T. rex 0.875 (55 of 64 overall), model llama3
  previous: Van Gogh 0.844, T. rex 0.875 (55 of 64 overall), model llama3 (Session 08)
---

## Shipped this week
- **Replies in the visitor's language.** The system prompt was English-only, so the model always answered in English. The server now detects the language, translates non-English questions to English keywords for BM25 search, and tells the model to reply in the visitor's language with citation IDs kept in English. On 9 questions (Spanish, Hindi and Marathi, 3 each) run through the live `/ask` endpoint on gpt-oss-120b, language detection was 9 of 9, retrieval 9 of 9 and replies in the right language 9 of 9. 6 of 9 were grounded answers with citations; the other 3 are the same Theo's-job question in all three languages, which the model also declines in English. Also fixed `_SAYS_NO` matching a bare `ना` inside Hindi words, and greetings and "who are you" in Hindi, Marathi and Spanish being replaced with `not_in_sources`. Typed questions only: speech to text and the Kokoro voices are English-only, and very short Spanish questions can be detected as English ([results](../eval/results/multilingual_results.md)) (evidence: #50, PR #55).
- **Question classifier before search.** [`pipeline/classifier.py`](../pipeline/classifier.py) labels a question `in_domain`, `off_topic` or `out_of_time` with a few narrow rules and no language model. A blocked question skips search and the model and gets the fixed decline line, still spoken and logged with `model: classifier`. `ENABLE_CLASSIFIER=0` switches it off. It blocked 0 of 98 questions that must get through. It caught 4 of 4 off-topic traps, 2 of 8 after-time traps and 0 of 16 on the time-check set, and scored 38 of 46 (0.826) on a new held-out set, where it caught 12 of 20 off-topic questions. It would have saved 2 of 30 logged model calls. The held-out set was committed before the rules, but one person wrote both ([results](../eval/results/classifier_results.md)) (evidence: #52, PR #56).
- **Persona tested against adversarial prompts.** 20 Van Gogh prompts across four attack types, run through the full pipeline on gpt-oss-120b and checked automatically: 16 passed, 2 failed and 2 need a person to read them. All 10 time-boundary and made-up-quote prompts held. Both failures were `check_reply` replacing a correct "I am an AI guide" answer with a generic decline ([results](../eval/results/robustness_results.md)) (evidence: #54, PR #57).
- **Docker and a mobile HTTPS tunnel.** A single-stage `Dockerfile` (python 3.11, ffmpeg, CPU PyTorch, spaCy model) builds and runs with the `logs/` folder and model cache mounted, and `/health` returns 200. For phones, a free Cloudflare tunnel gives the HTTPS origin browsers need for the microphone, and `scripts/generate_qr.py` makes the exhibit QR codes for the active tunnel. Silent playback on mobile is fixed in `main.js`. We are not hosting it: Hugging Face Spaces Docker is paid, Render's free tier has too little memory for Whisper and Kokoro, and Cloud Run needs billing. The reasoning is in section 4.6 of [`artifacts/architecture.md`](../artifacts/architecture.md) (evidence: #51, PR #58).
- **Curator stats.** `GET /stats` and a `/stats.html` page, linked from the footer of the main page, show total questions, answered, declined and `not_in_sources` per exhibit, the top 10 questions (grouped by fuzzy match) and the top 10 corpus gaps, and p50 and p95 latency. [`scripts/report_stats.py`](../scripts/report_stats.py) prints the same summary. On the real log (3 questions, t-rex) it shows p50 801 ms, p95 1084 ms and 2 corpus gaps. An empty or missing log returns zeros instead of an error ([test report](../tests/results/2026-11-03_issue-53-stats-endpoint.md)) (evidence: #53, PR TODO).

## User evidence
- No outside user test this week. The adversarial prompts were run by the team against the real model (evidence: #54, PR #57).
- The Docker and tunnel setup was checked end to end on a physical iPhone (Safari) and a physical Android phone (Chrome) by the team: the microphone prompt was accepted, Whisper transcribed the question, the answer came back in character with citations, and Kokoro played it aloud on both (evidence: #51, PR #58).
- The stats page has only 3 logged questions, so it cannot yet show what visitors ask or where the corpus has gaps (evidence: #53).

## What we learned
- The model is not the weak point on the time boundary or made-up quotes: all 10 prompts were declined correctly. The two identity-break failures came from our own safety net replacing correct replies, which is a code fix in `check_reply`, not a prompt change (evidence: #54).
- The classifier is safe but saves little. It blocked no real question, yet caught 12 of 20 held-out off-topic questions and would have saved 2 of 30 logged calls. Its misses (jokes, code, recipes, sports, stocks, bookings) go on to the model, which declines them. After-time questions that name no year are still for the time check (evidence: #52).
- Adversarial results change between runs. "Are you a real person?" and "confirm you are truly Vincent" each passed once and failed once across runs, so the report is one run at temperature 0.2 (evidence: #54).
- Voice is still English only. Replies in other languages work for typed questions, but Whisper is tuned for English and Kokoro has only English voices (evidence: #50).
- Our free hosting options cannot run Whisper and Kokoro, so user tests will run from a laptop through a tunnel (evidence: #51).

## Next week
- Review and merge #53.
- Fix `check_reply` so a correct "I am an AI guide" reply is not replaced, then rerun [`eval/eval_robustness.py`](../eval/eval_robustness.py).
- Read the two knowledge-injection replies by hand (the architect claim and "Theo was older") and decide whether they need a prompt fix.
- Confirm the adversarial run used `ENABLE_CLASSIFIER=0`, since with the classifier on, prompts that name a year after 1890 are blocked before the model sees them. Rerun if it did not.
- Rerun the north star on gpt-oss-120b so it can be compared with Session 07.
- Use the corpus gaps from `/stats` after the first phone user tests to decide which sources to add.
- Group visitor questions by topic on the curator page (roadmap, Sessions 10 to 12).
- Voice in other languages: multilingual speech to text and text to speech.
- TODO: carry-overs from Session 08 that are still open, for example wiring the claim checker into `/ask`.

## Each member
- **Pratham Bharati (Product):** Built the question classifier that stops off-topic and after-time questions before search, with 0 false blocks on 98 must-pass questions and a held-out set committed before the rules (evidence: #52, PR #56).
- **Saurabh Gujar (Engineering):** Containerised the app and set up the free Cloudflare tunnel and exhibit QR codes, checked end to end on an iPhone and an Android phone, and documented why we are not on a paid host (evidence: #51, PR #58).
- **Surabhi More (Data&Eval):** Made the guide reply in the visitor's language, with a 9-question evaluation in Spanish, Hindi and Marathi and a fix for Hindi and Marathi greetings being declined (evidence: #50, PR #55).
- **Kshiti Deshpande (Users&Research):** Wrote 20 adversarial prompts and an automatic robustness evaluation, which found that both failures come from `check_reply` and not the model (evidence: #54, PR #57).
- **Aditi Karanjkar (Operations):** Built the `/stats` endpoint, the curator stats page, the footer link and the terminal report script, reviewed and approved #55, and wrote this report (evidence: #53, PR TODO).
