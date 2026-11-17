---
team: Echoes.ai
session: 11
date: 2026-11-17
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
  value: Van Gogh 0.938, T. rex 1.000 (62 of 64 overall), model openai/gpt-oss-120b, fair key-fact scoring
  previous: Van Gogh 0.938, T. rex 0.906 (59 of 64 overall), model openai/gpt-oss-120b (Session 10; the same answers, scored with the old exact-word check)
---

## Shipped this week
- **Persona vs plain guide on the same model and code.** The plain guide was rerun on the 64 held-out questions with `openai/gpt-oss-120b`, and the Session 10 persona answers were reused, so both modes now come from the same model and code. With fair scoring, persona scores 62 of 64 (0.969) and the plain guide 61 of 64 (0.953), and both decline all 18 traps. The two modes disagree on only 3 questions: persona alone is right on tr-09 and tr-26, the plain guide alone on vg-07, and both miss vg-08. The difference is +1.6 points, with a 95% interval from -5.4 to +9.2 and exact McNemar p = 1.00, so there is no evidence that either mode is more accurate. Even a 3 to 0 split would only give p = 0.250 ([comparison](../eval/results/compare_modes.md), [answers](../eval/results/answers_results.json), [test report](../tests/results/2026-11-17_eval-plain-guide-rerun-session11.md)) (evidence: #73, PR #79).
- **Fair key-fact scoring, and the vg-07 and vg-08 misses explained.** The check now accepts number words ("six" for "6"), common unit spellings ("kilometres" for "km") and listed synonyms ("strongest" for "largest", "dim light" for "low-light"). This moved Session 10 from 59 to 62 of 64 and Session 7 from 59 to 60, and left Session 8 at 55, all offline with no model calls. vg-07 is the model missing a clause in a retrieved letter, not `check_reply`. vg-08 is a BM25 miss that hybrid search would fix but makes worse elsewhere, so search was not changed ([rescoring](../eval/results/north_star_rescoring.md), [test report](../tests/results/2026-11-17_feat-data-eval.md)) (evidence: #72, PR #77).
- **Voice in Hindi and Spanish.** Whisper now detects the spoken language and falls back to English when it is unsure (below `WHISPER_LANG_MIN_PROB`, default 0.6). It skips the English vocabulary prompt for other languages, and Kokoro speaks the answer back in Hindi or Spanish (this needs `espeak-ng`). `/ask` prefers the language Whisper detected ([test report](../tests/results/2026-11-16_feat-multilingual-voice.md)) (evidence: #71, PR #76).
- **Demo script, final report outline, and a setup dry run.** A 15-minute demo-day script (12 minutes of talk and live demo, then questions) with the questions to ask and the results file behind each one, the outline of the final report, roadmap v6 and lean canvas v5. A team dry run from a fresh clone got to a spoken answer in about 2 minutes and fixed three README problems: `python3.12`, where to get a model key, and a path too long for espeak-ng. The setup test with a person from outside the team is still to do ([demo script](../artifacts/demo_script.md), [final outline](../reports/final/report.md), [dry run](../artifacts/setup_dry_run.md)) (evidence: #74, PR #75).
- **Five adversarial prompts for the T. rex.** Until now the robustness set only attacked Van Gogh (20 prompts). It now has 5 for the T. rex, one per attack type plus a second knowledge injection: false facts ("you hunted Stegosaurus", "you lived in Africa"), a time-boundary trick (Jurassic Park), a made-up quote on the sign, and "are you a real dinosaur?". A test checks the file loads and covers every attack type. The prompts have not been run against the model yet ([prompts](../eval/questions/adversarial/t-rex.jsonl), [test report](../tests/results/2026-11-17_eval-t-rex-adversarial-prompts.md)) (evidence: #80, PR #81).

## User evidence
- **P7, on his own phone.** One person from outside the team used the running product on his own phone through a free Cloudflare tunnel. It was our first test on a visitor's own phone, and our first outside user test since Session 8. #70 planned three people, and only one could be done this week. He asked 3 questions we gave him, by voice. All 3 were heard right the first time with no edits, both factual answers were right and cited (vg-12, three versions of The Bedroom; tr-08, about 8.8 tonnes), every answer was spoken, and the roar played. Speech to text took 0.8 to 1.1 s and the server answered 0.5 to 0.6 s later. He rated it 3.5 to 4 out of 5 for use in a museum, and would change the look of the page first, "more creative and interesting" ([summary](../artifacts/evidence/session11/README.md), [notes](../artifacts/evidence/session11/P7.md), [log](../artifacts/evidence/session11/P7_log.jsonl)) (evidence: #70, PR #78).
- What did not work: the first tunnel dropped mid-test, after about 17 minutes, so P7's first try left no log. We also did not get a person from outside the team to do the README setup test (#74). Unknown visitors, probably crawlers, loaded the public page within minutes, and anyone with the link could use up our model key's daily quota. The README now says to keep the laptop awake and try HTTP/2 if the link drops (evidence: #70, PR #78).

## What we learned
- On the same model and code, the persona does not cost accuracy: 62 against 61 of 64, p = 1.00. The 64 questions are too few to show a difference either way, so the final report should present the modes as equally accurate rather than claim persona is better (evidence: #73).
- Most of the gap between our check and a person was wording, not wrong answers. With fair scoring, 2 real misses are left out of 64: a missed clause (vg-07, persona only) and a search miss (vg-08, both modes) (evidence: #72, #73).
- The phone, voice and tunnel work end to end on a visitor's own phone. But with 1 person and 3 questions read from a sheet, the test says nothing about how people phrase their own questions, and the 3 of 3 heard right can't be compared with Session 7's 6 of 12 (evidence: #70).
- A public tunnel is a risk to our model quota, so it should run only during a test or the demo (evidence: #70).
- Reusing the Session 10 persona answers meant the plain-guide rerun cost one mode of tokens (about 180K), which fits the free Groq daily limit with one key (evidence: #73).

## Next week
- Demo day: December 1. Rehearse the demo script once with a timer before Session 12 and write the real times in it.
- Kshiti's phone tests, moved from this week: two more people asking their own questions, as #70 planned.
- Run the final numbers once in Session 12, on the questions visitors write, with `openai/gpt-oss-120b`, as the final report outline says.
- Run the 5 T. rex adversarial prompts against the model and add them to the robustness results.
- The setup test with a person from outside the team (#74).
- P7's main request, the look of the page, as a candidate before demo day.
- vg-08: decide whether to accept the search miss or try a fix that does not hurt T. rex.

## Each member
- **Pratham Bharati (Product):** Wrote this week's issues, the demo script, the final report outline and README, roadmap v6 and lean canvas v5, and fixed three README setup problems found on a fresh clone (now about 2 minutes from clone to a spoken answer). Ran this week's user test with P7 on his own phone (evidence: #74, PR #75; #70, PR #78).
- **Saurabh Gujar (Engineering):** Added Hindi and Spanish voice: language detection with an English fallback in speech to text, and Hindi and Spanish speech in Kokoro (evidence: #71, PR #76).
- **Surabhi More (Data&Eval):** Made the key-fact check fair, rescored Sessions 7, 8 and 10 offline, explained the vg-07 and vg-08 misses, and reran the T. rex multilingual evaluation on gpt-oss-120b (evidence: #72, PR #77).
- **Kshiti Deshpande (Users&Research):** Wrote five adversarial prompts for the T. rex, one per attack type, with a test that they cover every type (evidence: #80, PR #81).
- **Aditi Karanjkar (Operations):** Reran the plain guide on gpt-oss-120b, rescored both modes with the fair check, ran the persona vs plain guide comparison, and wrote this report (evidence: #73, PR #79).
