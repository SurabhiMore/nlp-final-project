---
team: Echoes.ai
session: 07
date: 2026-10-20
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
  value: Van Gogh 0.97, T. rex 0.88 (59 of 64 overall)
  previous: Van Gogh 0.86, T. rex 0.86 on 22 questions per exhibit (Session 5; not the same question set)
---

## Shipped this week
- **Shared test setup.** `python -m pytest` with a smoke test of everything that already works, a rule that no test calls a real language model, and `--save-report`, which writes a per-PR test report to `tests/results/` (evidence: #32, PR #33). The test suite grew from 16 tests to 161 this week.
- **Is the persona really less accurate than the plain guide?** [`eval/compare_modes.py`](../eval/compare_modes.py) pairs the two modes question by question and runs an exact McNemar test with a 95% interval for the gap (evidence: #30, PR #34).
- **More held-out questions.** 20 new questions (64 in total, 46 answerable and 18 traps), stricter checks on the question files, and a [coverage summary](../eval/coverage_summary.md) (evidence: #27, PR #35).
- **Better T. rex search.** Query clean-up, `-ed`/`-ing` stemming and a three-word T. rex term map in [`pipeline/retrieve.py`](../pipeline/retrieve.py), checked on 10 new T. rex questions written before tuning, with a [before and after report](../eval/results/retrieval_comparison.md) that lists every question that got worse (evidence: #31, PR #36).
- **Clearer answer states on the phone page.** Each answer card shows whether it is loading, answered, not covered by the sources, or failed, and the sources are set apart from the answer (evidence: #29, PR #37).
- **A check on every model reply before the visitor sees it** (PR open, not merged yet). It replaces declines that answer anyway from the model's own knowledge, uncited answers and unreadable replies, measured before and after on the same 128 model replies ([summary](../eval/results/grounding_summary.md)) (evidence: #28, PR to be linked).
- **Second round of user tests** with three people from outside the team ([`artifacts/evidence/session07/`](../artifacts/evidence/session07/)) (evidence: #28).

## User evidence
- Three people from outside the team (P2, P3 and P4: a teammate's roommate, a teammate's friend, and one more person) used the running product in person on a laptop, on October 20. Each did five tasks across both exhibits: a question the sources cover and one they don't for each exhibit, then an off-topic question. P2 used the task sheet's wording. P3 and P4 asked their own questions of each kind. 12 questions were asked by voice and 3 typed.
- Tasks completed: 10 of 15, plus 4 partly and 1 not completed. Would use it in a museum: 3.5, 3 and 4 out of 5.
- **The guide stayed honest.** All 9 declines were correct and made nothing up: no name for Van Gogh's childhood dog, no number of weeks for the eggs, no "Paris", no "96".
- **Two answers cited a real passage but added a detail the passage does not have.** "Did you move to Arles?" added a later move to Auvers in 1890, and "Did you die?" gave "July 1890". P2 rated the Arles answer 5 of 5 for believing it and did not notice. Our evaluation had not shown this failure.
- **Speech to text misheard 6 of the 12 spoken questions** ("How well can you smell" became "How welcome you smell."). All three people brought it up. P4 switched to typing because of it and asked for "a live transcript of what it heard". P3 asked for "an undo button".
- **Raw artifact**: [`artifacts/evidence/session07/`](../artifacts/evidence/session07/): the task sheet with the moderator script, one record per person (`P2.md` to `P4.md`), their question and answer logs exported from the product, and a README with the results.
- What we changed as a result: nothing in the product yet. The two answer failures are written up as remaining failure modes in the #28 summary. Showing the transcript before the answer, with a way to redo the question, is planned for next week.

## Metrics snapshot
- Grounded answer accuracy, persona: Van Gogh 0.97 (31 of 32), T. rex 0.88 (28 of 32), 0.92 overall. Plain museum guide (baseline): exactly the same, 59 of 64 (was: persona 0.86 and plain guide 0.89 on 44 questions in Session 5).
- Trap questions handled correctly: 18 of 18 in both modes.
- Persona against plain guide, paired test on the Session 5 run: gap -2.3 points, 95% interval -12.1 to +7.0, McNemar p = 1.00. No evidence of a difference. On this week's 64 questions the two modes scored the same.
- Reply check, before and after on the same replies: declines that still stated the answer without a source 1 to 0, regressions 0, grounded accuracy 0.92 to 0.92. Accuracy was not expected to move, because the change is in what the visitor is shown, not in how the answers are scored.
- Search, supporting passage in the 8 passages the model gets (Hit@8): T. rex 0.74 to **0.96**, Van Gogh 0.91 to 0.87. Hit@1: T. rex 0.30 to 0.35, Van Gogh 0.70 to 0.70. MRR@10: T. rex 0.44 to 0.50, Van Gogh 0.75 to 0.76. On the 10 new T. rex questions, Hit@5 went from 0.40 to 0.50.
- User test: answer on screen a median of 1.2 s after the question (from the product log). Time to the first spoken word was not re-measured. It is still the Session 5 figure: 6.6 s median on a laptop CPU.
- Measured on: 64 held-out questions (32 per exhibit; 46 answerable, 18 traps) in [`eval/questions/`](../eval/questions/), plus 10 new held-out T. rex questions for search in `eval/questions/heldout/`. Results are in [`eval/results/`](../eval/results/).
- Is this the same model that is running in the product? The same language model (`openai/gpt-oss-120b`), prompt and 8 passages per question, but with two differences. The answer accuracy uses the passages search returned before this week's search change, frozen so the before and after comparison of the reply check is fair. And the reply check is in an open PR, not on main yet. The search numbers are for the search now on main.

## What did not work
- **One search fix made a question worse.** "When did you arrive in Arles?" (vg-04) now misses its passage in the top 10, where it used to be 6th, and two T. rex questions moved from 5th to 7th. The before and after report flags 3 regressions in total. Mapping "heavy" to "mass" was tried and dropped, because it pushed the right passage out of the top 10.
- **Search still misses Theo's job.** "What did your brother Theo do for a living?" got "my sources do not say" in the user test, although the corpus says he was an art dealer. The search fix only covered the T. rex.
- **The reply check cannot catch a wrong detail in an answer that cites a real passage** ("July 1890" above). It only checks that a passage is cited, not that every fact in the answer is in it.
- **Off-topic questions can get the wrong badge.** When the check replaces an uncited answer it always says "Not in my sources", even for an off-topic question such as "can you hello in spanish".
- **Setting up from scratch broke twice.** Kokoro, our text to speech, does not install on Python 3.13, and a new release of PyAV (19.0) broke faster-whisper's audio decoding. Both were fixed locally (Python 3.12, PyAV 18), but `requirements.txt` and the README do not say this yet.

## Challenges / blockers
- Groq's free daily limit stopped the answer evaluation (128 calls) partway through. We finished it with a second key using `--resume`.
- The Sessions 7 to 9 components in the roadmap (meaning-based search, the claim checker, the quote checker, the question classifier and the time-boundary check) have not started yet. This week went into the shared test setup, more questions, and fixing failures we had measured.
- The user tests are still run on a laptop at localhost, because the product is not deployed on an https link yet.

## Next week's goal
- Merge #28, then rerun the answer evaluation on the new search with the reply check on main, so the north star is measured on exactly what runs in the product.
- Show the transcript as soon as speech to text returns, with a way to redo the question, and test it with outside users.
- Start the roadmap's NLP components, beginning with the claim checker, which would catch the unsupported details found this week.

## Individual contributions
- Pratham Bharati (Product): the shared test setup and per-PR test reports, and the paired persona against plain guide comparison (evidence: #32, PR #33, #30, PR #34)
- Saurabh Gujar (Engineering): answer states and source cards on the phone page, with 12 server tests (evidence: #29, PR #37)
- Surabhi More (Data & Eval): 20 new held-out questions, stricter question checks with 22 tests, and the coverage summary (evidence: #27, PR #35)
- Kshiti Deshpande (Users & Research): the reply check with a before and after evaluation and 40 tests, the second round of user tests with three people, and this report (evidence: #28)
- Aditi Karanjkar (Operations): T. rex search improvements with 10 new held-out questions, the before and after search report and 47 tests (evidence: #31, PR #36)

## Lean canvas changes (if any)
- No changes this week. The lean canvas is still version 3 (September 29).
