---
team: Echoes.ai
session: 10
date: 2026-11-10
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
  value: Van Gogh 0.938, T. rex 0.906 (59 of 64 overall), model openai/gpt-oss-120b
  previous: Van Gogh 0.969, T. rex 0.875 (59 of 64 overall), model openai/gpt-oss-120b (Session 7; same model, so like-for-like)
---

## Shipped this week
- **North-star rerun on gpt-oss-120b.** Persona mode 59 of 64 (Van Gogh 0.938, T. rex 0.906), the same total as Session 7 on the same model, with all 18 traps declined and no failed calls. The drop to 55 of 64 in Session 8 came from llama3, not the code: the reply check, claim check, classifier and multilingual changes since Session 7 did not cost accuracy. Of the 5 misses, 3 are correct, cited answers the strict key-fact check does not match ("strongest" for "largest", "six kilometres" for "6 km", "dim light" for "low-light"), 1 is a wrong decline (vg-07) and 1 a search miss (vg-08). [`scripts/compare_north_star.py`](../scripts/compare_north_star.py) builds the Session 7, 8 and 10 table ([summary](../eval/results/north_star_session10.md), [comparison](../eval/results/north_star_comparison.md)) (evidence: #64, PR TODO).
- **Claim checker in `/ask`.** [`pipeline/claims.py`](../pipeline/claims.py) now runs on every answered reply in `/ask` and logs any date, number or name the cited passages do not contain as `unbacked_claims`, also returned in the response. `ENABLE_CLAIMS=0` switches it off ([test report](../tests/results/2026-11-09_feat-integrate-claims-check.md)) (evidence: #60, PR #65).
- **`check_reply` keeps honest "I am an AI guide" replies.** A reply that says the exhibit is an AI guide is no longer replaced when the visitor asked what the exhibit really is. An "As an AI guide, ..." reply to an ordinary question with uncited facts is still replaced. The robustness rerun on gpt-oss-120b went from 16 of 20 passed to 19 of 20, with 0 needing manual review ([results](../eval/results/robustness_results.md), [test report](../tests/results/2026-11-10_fix-check-reply-transparency.md)) (evidence: #62, PR #66).
- **Visitor questions grouped by topic on the curator page.** [`app/stats.py`](../app/stats.py) tags each logged question with a topic using keyword rules, with no language model, and `/stats.html` and `scripts/report_stats.py` show the questions and `not_in_sources` counts per topic. 56 of 66 held-out questions are tagged right (0.848), and 29 of 30 questions real visitors asked in the user tests ([results](../eval/results/topics_results.md), [test report](../tests/results/2026-11-10_feat-curator-topic-clustering.md)) (evidence: #61, PR #67).
- **Multilingual replies for T. rex, and Kannada.** The Session 9 evaluation covered only Van Gogh in Spanish, Hindi and Marathi. It now covers both exhibits and adds Kannada: 12 questions per exhibit (3 each in Spanish, Hindi, Marathi and Kannada), run through the live `/ask` endpoint on gpt-oss-120b. Language detection was 12 of 12 for each exhibit, and every reply came back in the visitor's language and script, with citation IDs kept in English. Kannada declines are no longer replaced, because `_SAYS_NO` now recognises Kannada "no" words, and Kannada has its own fixed decline lines. `eval/run_multilingual.py` takes `--persona` ([results](../eval/results/multilingual_results.md), [test report](../tests/results/2026-11-10_feat-multilingual-trex-and-kannada.md)) (evidence: #63, PR #68).

## User evidence
- TODO: outside user tests this week, if any.
- The 30 questions from all 6 user test logs, read together on the curator page, fall mostly under works (6), body and senses (5) and other or unclear (4). 11 of the 30 were `not_in_sources`, which shows where the corpus has gaps (evidence: #61).

## What we learned
- The model, not the code, explains the Session 8 drop. On the same model the north star is unchanged at 59 of 64, so model choice must be recorded with every north-star number (evidence: #64).
- The automatic north-star check is stricter than a person. 3 of the 5 misses are correct answers in other words, so a human reading would give about 62 of 64. The same check was used in every session, so comparisons between sessions are still fair (evidence: #64).
- The free Groq tier limits how we evaluate. A 64-question run uses about 180K of the 200K daily tokens per organization, so only persona mode was rerun this time, and a second key had to finish it (evidence: #64).
- The last robustness failure is the model, not our safety net: it agreed that Theo was older ("indeed") while declining the rest (evidence: #62).
- The topic rules work on real visitor wording (29 of 30) but miss questions about death and extinction, and the same person wrote the labels and the rules (evidence: #61).

## Next week
- vg-07: find out why the Gauguin portrait question is declined although the passage is retrieved (model or `check_reply`).
- vg-08: the passage about Japan is not retrieved for the Arles countryside question.
- Decide whether the key-fact check should accept number words and synonyms. If it changes, rescore Sessions 8 and 10 together.
- Rerun plain-guide mode on gpt-oss-120b so `compare_modes` can use the Session 10 results.
- Fix the knowledge-injection failure vg-adv-ki-03 ("Theo was older").
- Review and merge #68.
- TODO: carry-overs from Session 9 that are still open, for example voice in other languages.

## Each member
- **Pratham Bharati (Product):** Grouped visitor questions by topic on the curator stats page, with a labelled held-out set and an evaluation on real visitor questions (evidence: #61, PR #67).
- **Saurabh Gujar (Engineering):** Wired the claim checker into `/ask` behind `ENABLE_CLAIMS`, with unbacked claims logged and returned (evidence: #60, PR #65).
- **Surabhi More (Data&Eval):** Extended the multilingual evaluation to the T. rex exhibit and added Kannada, with 24 questions across both exhibits and Kannada-aware decline checks, and reviewed and merged PRs #65, #66 and #67 (evidence: #63, PR #68).
- **Kshiti Deshpande (Users&Research):** Fixed `check_reply` so honest "I am an AI guide" replies are kept, and reran the robustness evaluation to 19 of 20 (evidence: #62, PR #66).
- **Aditi Karanjkar (Operations):** Reran the north star on gpt-oss-120b, wrote the Session 7, 8 and 10 comparison script and summary, and wrote this report (evidence: #64, PR TODO).
