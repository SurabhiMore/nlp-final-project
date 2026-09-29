---
team: Echoes.ai
session: 05
date: 2026-09-29
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
  metric: Grounded answer accuracy (persona mode, 22 held-out questions per exhibit)
  value: Van Gogh 0.86, T. rex 0.86
  previous: none (first measurement)
---

## Shipped this week
- **Server and speech to text.** A FastAPI server takes a spoken or typed question for any exhibit and returns a cited answer, with every step timed and logged. Speech to text uses Whisper through faster-whisper. Exhibits are defined by a `persona.json` file, so the same code serves a person (Van Gogh) and a creature (T. rex) (evidence: #11, PR #17).
- **Corpus builder and held-out questions.** One script, [`scripts/build_corpus.py`](../scripts/build_corpus.py), builds both exhibits from the sources listed in their `persona.json`: 363 passages for Van Gogh (252 of them from his letters) and 133 for T. rex. 22 held-out questions per exhibit in [`eval/questions/`](../eval/questions/), written before we saw any model answers, including trap questions (evidence: #12, PR #16; the T. rex corpus and questions came in PR #18).
- **Keyword search and its evaluation.** BM25 search for any exhibit in [`pipeline/retrieve.py`](../pipeline/retrieve.py), measured by [`eval/eval_retrieval.py`](../eval/eval_retrieval.py) (evidence: #13, PR #21).
- **Answer engine and baseline.** [`pipeline/persona.py`](../pipeline/persona.py) answers only from the retrieved passages, cites them, and adapts to the kind of exhibit. A plain museum guide answering from the same passages is our baseline, and [`eval/eval_answers.py`](../eval/eval_answers.py) scores both (evidence: #14, PR #20).
- **Phone page and text to speech.** Pick an exhibit, hold to talk or type, and see the answer with its sources while Kokoro reads it aloud, a short first piece first so the voice starts sooner. Every exhibit introduces itself when asked, and the T. rex roars on request, with a sound we synthesized and a note that nobody knows what it really sounded like (evidence: #15, PR #18).
- **Measurements.** The first user test (PR #22) and the voice latency results (PR #23).
- **Updated plans.** Lean canvas v3 and roadmap v4 (PR #20), data sources v2 (PR #19) and user research plan v2 (PR #18).
- The product runs locally with `uvicorn app.server:app`. It is not deployed yet.

## User evidence
- One person from outside the team (P1) used the running product in person on a laptop, by voice, and did two of the six tasks from the task sheet: the feeling of The Bedroom (Van Gogh) and whether the T. rex ever met a human. Tasks finished: 2 of 2. The tasks were not timed with a stopwatch; from the product log, answers appeared a median of 4.4 s after each question.
- P1 found holding the button while speaking awkward: one question was cut off because the button was let go too early, and the guide answered "not in my sources" to half a question. P1 also found the response a little slow, and rated it 3.5 out of 5 for using it in a museum. Both task answers matched their cited sources.
- **Raw artifact**: [`artifacts/evidence/session05/`](../artifacts/evidence/session05/): the task sheet, P1's record (`P1.md`) and P1's question and answer log exported from the product (`P1_log.jsonl`).
- What we changed as a result: nothing in the product yet. From this session, next week we will let visitors tap once to start and once to stop recording instead of holding the button, and move speech generation to a GPU when we deploy. This was a one-person pilot; the full round of tests (three or more people, all six tasks) is planned before October 6.

## Metrics snapshot
- Grounded answer accuracy, persona: Van Gogh 0.86, T. rex 0.86 (was: not measured)
- Grounded answer accuracy, plain museum guide (baseline): Van Gogh 0.91, T. rex 0.86
- Trap questions handled correctly (persona): Van Gogh 7 of 7, T. rex 6 of 6
- Search, supporting passage in the top 5 (Hit@5): Van Gogh 0.73, T. rex 0.62. Recall@5 0.70 and 0.62, MRR@10 0.67 and 0.42. In the top 8, which is what the answer model gets: 0.87 and 0.75 (was: not measured)
- Time from the end of the question to the start of the spoken answer, on a laptop CPU: median 6.6 s, worst 13.5 s ([`eval/results/latency_results.json`](../eval/results/latency_results.json))
- Hand check of 20 answers: our automatic scoring agreed with our own labels on 20 of 20 (Cohen's kappa 1.00)
- Measured on: 44 held-out questions (22 per exhibit; 31 answerable, 13 traps that should be declined), written before any model answers were seen. Results are in [`eval/results/`](../eval/results/).
- Is this the same model that is running in the product? Yes. The evaluation calls the same search and answer code, with the same settings (8 passages per question, model `openai/gpt-oss-120b`), as the server. The accuracy evaluation uses typed questions, so speech recognition errors are not included in that number; they are measured separately as word error rate in the latency results (0.05).

## What did not work
- **Keyword search misses when visitors use different words from the source.** T. rex Hit@5 is only 0.62 and MRR 0.42. "How heavy could you get?" misses because the article says "mass", and "What does the rex in your name mean?" never finds the passage that explains it. We now give the model 8 passages instead of 5, and meaning-based search is planned for Sessions 7 to 9.
- **Our 2 second target is not reachable on a laptop CPU.** Whisper large-v3-turbo took about 14 seconds to transcribe a 2.5 second question, so we switched to the smaller "base" model on CPU (about 1.6 seconds, same transcript). Kokoro takes a median of 3.3 s for the first spoken piece on CPU. We changed the design so the answer text appears first and the voice plays piece by piece, but the full voice delay is still a median of 6.6 s.
- **Speech generation is the slowest step, and our speed-up attempt failed.** Kokoro generates speech at roughly real time on our laptop CPU (about 3 seconds for a 12-word sentence), which is why the voice started 4 to 9 seconds after the text appeared. Speaking a short opening first (the answer split at its first comma) cut the wait to about 1 second for most T. rex answers, but answers with dates still wait 3 to 4 seconds. We also benchmarked the ONNX version of Kokoro, expecting it to be faster, and it was 2 to 7 times slower on the same sentences, so we kept the PyTorch version. A GPU is the real fix, and part of the deployment work next week.
- **The data was messier than we planned for.** Project Gutenberg's plain text file for the letters returned 404, so the builder falls back to the HTML edition. The book includes a translator's essay and notes, which would have been passed off as Van Gogh's own words, so we split it into parts and only mark the letters as his. 37 passages had footnote marks, and the Smithsonian search returned library books and other tyrannosaurs, which we filtered out (58 records down to 24).
- **A flaw in our own evaluation.** The automatic check looks for key facts as exact words, so a correct answer phrased differently can be marked wrong. The hand check agreed with the automatic check on all 20 sampled answers, but in the full run exact-word matching still marked some correct answers wrong (bite force, running speed and the Arles countryside), so the true accuracy is probably a little higher than reported. 20 rows and one labeller is a first check, not a final one.
- **Our first prompts got the time boundary wrong in both directions.** The first T. rex rule treated anything after the dinosaur's lifetime as off limits, so it would have refused "Who discovered you?". Then, in trial runs with a different free model, the T. rex gave an opinion on the Jurassic Park films, and Van Gogh answered "What did you think of Guernica?" with "not in my sources" instead of "after my time", because we had told the model to use only the passages and it would not use its own knowledge of when Guernica was painted. We now check the time boundary first, allow general knowledge only for judging dates, and let a creature share what scientists learned later without claiming to have seen it.
- **The persona did not beat the plain guide.** It scored one question lower overall (0.86 against 0.89; Van Gogh 0.86 against 0.91). On 44 questions that is too small to call a real difference, and a significance test is planned for Sessions 7 to 9. One clear persona miss: the T. rex declined "Who named you?" although the answer was in its passages, while the plain guide answered it from the same passages. And when search missed the passage, the model sometimes answered from its own knowledge anyway (for example "rex means king"), which the hand check flagged as not grounded.

## Challenges / blockers
- Free language model tiers are rate limited, so a full evaluation run (88 calls) needs pauses between calls and takes about 35 minutes. It hit Groq's free daily limit on the last 2 calls, which we finished on a second key with `--resume`.
- Browsers only allow the microphone on https pages, so user tests have to run on a laptop or through a tunnel until the product is deployed on an https link, which we need for October 6.
- Voice delay on CPU. We want to try a GPU (for example a free Colab or Hugging Face GPU) for the demo.

## Next week's goal
- The mid-semester presentation on October 6: a live demo of both exhibits on a phone, the accuracy number against the plain guide baseline, what outside users did with it, and our pivot or persevere decision.

## Individual contributions
- Pratham Bharati (Product): answer engine for any exhibit type, the plain guide baseline, the answer evaluation with a hand check, lean canvas v3 and roadmap v4, ran the first user test and the latency measurement (evidence: PR #20, #22, #23, #14)
- Saurabh Gujar (Engineering): repo structure, server, speech to text, the latency script and the roar generator, README (evidence: PR #17, #11)
- Surabhi More (Data & Eval): corpus builder, the Van Gogh corpus and questions with a checker, data sources v2 (evidence: PR #16, #19, #12)
- Kshiti Deshpande (Users & Research): phone page, text to speech (taken over from #11), user research plan v2, task sheet and log export for the user tests, and the T. rex exhibit files (evidence: PR #18, #15)
- Aditi Karanjkar (Operations): BM25 search and its evaluation, Session 05 board and milestone, this report (evidence: PR #21, PR #24, #13)

## Lean canvas changes (if any)
- Version 3: the product now covers any exhibit, not only historical people, with T. rex as a second test exhibit. Added the first measured numbers, the finding that voice on a CPU is too slow for our 2 second target, and a new risk: exhibits without their own words must not state debated science as fact.