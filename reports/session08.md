---
team: Echoes.ai
session: 08
date: 2026-10-27
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
  value: Van Gogh 0.844, T. rex 0.875 (55 of 64 overall), model llama3
  previous: Van Gogh 0.97, T. rex 0.88 (59 of 64 overall), model openai/gpt-oss-120b (Session 7; different model, so not a like-for-like comparison)
---

## Shipped this week
- **Hybrid search, measured and not adopted.** Embedding search and a BM25 + embeddings hybrid (Reciprocal Rank Fusion) behind a `SEARCH_MODE` setting, plus fixed install steps. Hybrid did not beat BM25 on Hit@8 for both exhibits (Van Gogh 0.783 against 0.870, T. rex 0.696 against 0.957), so BM25 stays the default ([report](../eval/results/hybrid_search_report.md)) (evidence: #39, PR #44).
- **Quote checker for the exhibit's own words.** [`pipeline/quotes.py`](../pipeline/quotes.py) labels a quote verbatim, close paraphrase or not found against Van Gogh's letters. 44 of 46 test quotes labelled right, and no false quote was labelled verbatim ([results](../eval/results/quotes_results.md)). Lean canvas v4 and roadmap v5 (evidence: #42, PR #45).
- **Speech to text tuned to each exhibit, with an editable transcript.** Whisper small with a vocabulary prompt per exhibit cut word error rate from 0.101 to 0.053 on 40 spoken questions, and heard 19 of 20 exhibit names instead of 11 of 20. The cost is 0.82 s per clip instead of 0.25 s. Visitors now see and can fix the transcript before the exhibit answers, with a warning when Whisper is unsure ([results](../eval/results/stt_results.md)) (evidence: #41, PR #47).
- **Claim checker for unsupported details.** [`pipeline/claims.py`](../pipeline/claims.py) flags dates, numbers and names in an answer that its cited passages do not contain. It catches both Session 7 failures ("Auvers-sur-Oise" and "1890", "July 1890"), with precision and recall 1.000 on 123 labelled answers, 30 of them perturbed on purpose ([results](../eval/results/claims_results.md)) (evidence: #40, PR #48).
- **North-star rerun on main.** Persona mode 0.859 (55 of 64), plain guide 0.875 (56 of 64) ([results](../eval/results/answers_results.json)). This run used llama3, not the gpt-oss-120b of Session 7, so the drop from 59 of 64 may be the model and not the code (evidence: #40, PR #48).
- **Time-boundary check with Wikidata dates.** [`pipeline/timecheck.py`](../pipeline/timecheck.py) finds names, works and events in a question, looks up their dates on Wikidata and flags anything after the exhibit's `end_year`. On 62 Van Gogh questions it has precision 0.82 and recall 0.45, with 2 false flags ("The Yellow House" and "Japanese"), all listed in the [results](../eval/results/timecheck_results.md). It runs offline from a saved Wikidata cache and is not wired into `/ask` yet (evidence: #43, PR #49).
- **The model already respects the time boundary.** On 30 new, harder Van Gogh questions, gpt-oss-120b answered 0 of 16 after-time questions anyway, in both persona and plain-guide mode, so the check adds nothing yet beyond the prompt. One decline gave a wrong reason: the persona said the telephone (1876) came after his time ([results](../eval/results/timecheck_results.md)) (evidence: #43, PR #49).

## User evidence
- Two people from outside the team (P5 and P6) used the product by voice on October 26, with the new transcript step ([`artifacts/evidence/session08/`](../artifacts/evidence/session08/)). Tasks completed: 9 of the 11 that were run. Seeing what it heard helped: 4.5 of 5 for both. Would use it in a museum: 4 and 5 (evidence: #41, PR #47).
- **4 of 11 transcripts were misheard.** The warning showed on 3 of them and on none of the 7 heard right. P6 fixed 2 misheard questions before sending; one became a cited answer that could not have been answered as heard (evidence: #41, PR #47).
- **Name questions now work by voice.** All 6 tasks that depend on names (Gachet, Gauguin, Sue, Hell Creek) were answered correctly with sources (evidence: #41, PR #47).
- **People correct themselves out loud instead of editing.** P5 twice said "actually..." mid-question, and both false starts were sent. Nobody used Record again (evidence: #41, PR #47).
- **Unsupported details are still reaching visitors.** One answer added hatchlings weighing "just a few kilograms", which the cited passage does not say, the same failure as Session 7. The claim checker from #40 would catch this kind of detail, but it is not wired into `/ask` yet (evidence: #40, #41, PR #47, PR #48).

## What we learned
- Our safeguards are measured but not yet in the product. The claim checker, the quote checker and the time check all run offline only. The user test shows the claim failure still happens live.
- The model is the biggest unknown in our numbers. The north-star rerun used a different model from Session 7, so we cannot say whether the product got better or worse.
- Our time-boundary traps are too easy to show a model failure. Even the harder set got 16 of 16 declines. The time check's recall is limited because people are dated by birth (Picasso, Einstein, Monet) and ambiguous names are skipped on purpose.

## Next week
- Wire the claim checker into `/ask`, and measure how often it changes a live answer.
- Rerun the north-star with gpt-oss-120b so it is comparable with Session 7.
- Time check: skip nationalities, keep "The" in titles, and date people by their works, not their birth. Measure on a new held-out set, not these 30 questions.
- Add T. rex's machine-readable time range so the time check covers both exhibits.

## Each member
<!-- Each member: replace your TODO with one or two sentences on what you did this week, with an issue or PR link. -->
- **Pratham Bharati (Product):** Shipped the quote checker, lean canvas v4 and roadmap v5 (evidence: #42, PR #45). TODO
- **Saurabh Gujar (Engineering):** Shipped hybrid search and fixed install steps; kept BM25 as the default on the evidence (evidence: #39, PR #44). TODO
- **Surabhi More (Data&Eval):** Shipped the claim checker and the north-star rerun (evidence: #40, PR #48). TODO
- **Kshiti Deshpande (Users&Research):** Shipped speech to text per exhibit and ran the Session 8 user test with P5 and P6 (evidence: #41, PR #47). TODO
- **Aditi Karanjkar (Operations):** Shipped the Wikidata time-boundary check with 30 new questions and the model run in both modes, and wrote this report (evidence: #43, PR #49).
