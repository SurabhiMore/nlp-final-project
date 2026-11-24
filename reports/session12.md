---
team: Echoes.ai
session: 12
date: 2026-11-24
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
  value: Van Gogh 0.938, T. rex 1.000 (62 of 64 overall), model openai/gpt-oss-120b, fair key-fact scoring (not rerun this week)
  previous: Van Gogh 0.938, T. rex 1.000 (62 of 64 overall), model openai/gpt-oss-120b (Session 11)
---

## Shipped this week
- **Three outside people on their own phones, with their own questions.** P8, P9 and P10, three UMD grad students outside the team, used the running product on their own phones through a Cloudflare tunnel, with both exhibits and `openai/gpt-oss-120b`. Before seeing the app, each wrote five questions per exhibit. Those 30 questions are now the test set for the final numbers ([visitor questions](../eval/questions/final/visitor_questions.jsonl), [summary](../artifacts/evidence/session12/README.md), [test report](../tests/results/2026-11-23_evidence-session12-phone-tests.md)) (evidence: #70, PR #91).
- **Robustness rerun on gpt-oss-120b with both exhibits.** All 25 adversarial prompts (20 Van Gogh, 5 T. rex) were run through the full pipeline: 23 of 25 passed (92%), with 0 needing manual review. Knowledge injection, time-boundary and identity-break prompts all passed. Both failures are made-up quotes the exhibit explained as if real: "Tiny arms, but a giant heart" (T. rex) and "I would rather starve in the south than eat well in Paris" (Van Gogh). Van Gogh alone was 19 of 20 in Session 10 and is 19 of 20 again, but a different prompt failed each time: vg-adv-ki-03 passed this week and vg-adv-qf-04 failed ([results](../eval/results/robustness_results.md), [test report](../tests/results/2026-11-23_eval-robustness-gpt-oss-120b.md)) (evidence: #83, PR #92).
- **The demo checked on main and timed.** All nine demo questions were asked on main with `openai/gpt-oss-120b`, through speech to text, `/ask` and `/speak`, and all nine were heard right and answered as the script expects. A full run-through took 13:23 against 12:00 planned. The talking parts came in 1:41 under, but the live demo ran 7:04 against 4:00, because each question waits for the whole answer to be spoken. Dropping questions 2 and 8 brings it to about 12:00 ([demo script](../artifacts/demo_script.md), [test report](../tests/results/2026-11-23_docs-rehearsal-and-problem.md)) (evidence: #86, PR #87).
- **A museum look for the visitor page, and an animated page at `/live`.** The plain page now has a museum look, with answer cards tinted from each exhibit's colours ([before and after](../artifacts/images/visitor-page/), [test report](../tests/results/2026-11-23_feat-livelier-visitor-page.md)) (evidence: #84, PR #88). At `/live`, Van Gogh's 1887 self-portrait blinks and moves his mouth with each sound he says, timed from Kokoro, and a low-poly T. rex walks off its plinth, roars and opens its jaws as it talks. Each exhibit keeps its own conversation when you switch. Every picture and three.js are in the repo, so the page needs no CDN. Each citation now also shows the sentence of the passage that backs the answer. This answers P8's and P9's requests for a page that moves and feels more artistic ([test report](../tests/results/2026-11-24_feat-living-exhibits.md), [image sources](../artifacts/data_sources.md)) (evidence: PR #93).
- **Final report sections and the evaluation plan.** Three sections of the final report are written: Problem and users (evidence: #86, PR #87), Product (evidence: #84, PR #89) and User evidence (evidence: #83, PR #92) ([final report](../reports/final/report.md)). The plan for the final numbers is committed before any visitor question is annotated. It fixes how the 30 questions are annotated, scored and reported ([evaluation plan](../eval/questions/final/README.md)) (evidence: #82, PR #90).

## User evidence
- **P8, P9 and P10, Monday November 23, 19:33 to 20:40 ET.** They sent 21 questions, all by voice. 19 of 21 were heard right the first time, and the other two were fixed in the transcript box before sending ("Can you roar?" was heard as "Can you road?"). 19 of the 22 tasks that were run were completed, 2 partly and 1 not. All 5 questions about things the exhibit cannot know, such as the 2026 midterms or self-driving cars, were declined, and nothing was made up. They rated it 5, 4.9 and 4 out of 5 for use in a museum, against 3.5 to 4 for P7 in Session 11. Speech to text took about 3.2 s, and the answer came 0.6 to 0.7 s after sending ([P8](../artifacts/evidence/session12/P8.md), [P9](../artifacts/evidence/session12/P9.md), [P10](../artifacts/evidence/session12/P10.md), [logs](../artifacts/evidence/session12/), [summary](../artifacts/evidence/session12/README.md)) (evidence: #70, PR #91).
- **What did not work.** The QR link failed on the first scan on all three phones, and scanning again fixed it. "What is your most famous painting?" got The Bedroom, because the cited passage calls it "the most famous depiction of a bedroom". The answer cites a real passage containing those words, so neither of our checks catches it. A question about other animals alive at the time was declined although the retrieved passages name Edmontosaurus and Triceratops. One answer about why his work was not valued was only half an answer. Speech to text was about 3 s against 0.8 to 1.1 s for P7, on a different laptop, and we have not checked whether the laptop is the cause. Nobody tried another language, so typed questions in other languages were not tested (evidence: #70, PR #91).
- What they asked for: an exhibit that moves while it talks (P8), a more artistic page and the conversation kept when switching exhibits (P9), and shorter answers (P10). The `/live` page answers the first two, but it has not been tested with a person yet (evidence: #70, PR #93).

## What we learned
- A cited answer can still be wrong. Our checks test whether the cited passage is real and contains the details, not whether it answers the question that was asked. The Bedroom answer is the clearest case so far, and it goes into the final report as a failure mode (evidence: #70).
- Made-up quotes are now the weakest attack: 4 of 6 pass, against 100% for every other type. A quote that fits real themes, like poverty or moving south, gets explained as if it were real (evidence: #83).
- Two runs of the same 20 Van Gogh prompts on the same model gave the same 19 of 20 but failed different prompts. One run of a prompt can't say for sure whether the exhibit resists it (evidence: #83).
- The free tier's per-minute limit slowed answers asked back to back to 13 to 17 s, against 0.5 to 1.8 s when asked 25 s apart. The demo has to leave about 20 s between questions (evidence: #86).
- The QR link is the first thing a visitor touches, and it failed every time on the first scan. A permanent link would fix it, but we have no free hosting (evidence: #70).

## Next week
- **Final submission, 5:00pm Tuesday December 1, and our demo the same day.** Everything must be on main in `reports/final/` (#85).
- The final numbers: annotate the 30 visitor questions and run them once on `openai/gpt-oss-120b`, as the evaluation plan fixes (#82).
- The slides in `reports/final/`, following the demo script's running order, with one or two slides from each part's owner (#85).
- The Ethics and limitations section of the final report, including the failures above (#85).
- A rehearsal with the whole team, with questions 2 and 8 dropped from the live demo, and the Hindi voice downloaded on the demo laptop beforehand (#86).
- A test of the `/live` page with at least one person before demo day.

## Each member
- **Pratham Bharati (Product):** Checked the nine demo questions on main and timed a full run-through, wrote the Problem and users section of the final report, and built the animated `/live` page with moving exhibits, word timing in `/speak` and the backing sentence for each citation (evidence: #86, PR #87; PR #93).
- **Saurabh Gujar (Engineering):** Gave the visitor page a museum look with answer cards tinted per exhibit, and wrote the Product section of the final report (evidence: #84, PR #88, PR #89).
- **Surabhi More (Data&Eval):** Wrote and committed the evaluation plan for the final numbers on visitor-written questions, before any of them were annotated (evidence: #82, PR #90).
- **Kshiti Deshpande (Users&Research):** Ran the phone test with P8, P9 and P10 and collected their 30 written questions, ran all 25 adversarial prompts on gpt-oss-120b with results per exhibit, and wrote the User evidence section of the final report (evidence: #70, PR #91; #83, PR #92).
- **Aditi Karanjkar (Operations):** Wrote this report (evidence: #85, PR #94).
