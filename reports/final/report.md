# Echoes.ai: final report

Outline, November 16 (#74). The finished report is 2 to 5 pages under these five headings. Each
section below lists what it will use. The final numbers come from one run in Session 12, on the
questions visitors wrote in Session 12 (#70, #72), with `openai/gpt-oss-120b`, the model in the
demo.

## Problem and users

- Visitors give a plaque a few seconds, and an audio guide plays the same recording for everyone
  and can't answer a question. Curators have to buy, charge and repair guide devices and record
  new tracks for every exhibit ([lean canvas](../../artifacts/lean_canvas.md), "Users and their
  problem").
- What exists: plaques, rented audio guides, human docents, and AI chatbots that are mostly text
  and don't publish how accurate they are (lean canvas, "What exists today").
- Who we tested with: 10 people from outside the team, 6 on a laptop in Sessions 5, 7 and 8 and 4
  on their own phones in Sessions 11 and 12 (#70, [user research plan](../../artifacts/user_research_plan.md)).

## Product

- A visit: the QR code, the phone page, hold to ask, fix the transcript if it misheard, then a
  spoken answer one sentence at a time with source cards (#15, #29, #41, #51).
- One codebase, two very different exhibits. Only `persona.json` and the sources change
  (`personas/`).
- Other languages: typed questions in Hindi, Marathi, Kannada and Spanish (#50, #63), and voice
  if #71 lands.
- The curator page: questions by topic, and the questions the sources could not answer (#53, #61).
- How it runs: a laptop and a free tunnel, and why there is no permanent link (#51, section 4.6
  of [`artifacts/architecture.md`](../../artifacts/architecture.md)).

## NLP method and evaluation

- The pipeline, and what each part was measured on:
  - speech to text: Whisper small with a prompt for each exhibit, word error rate 0.053 on 40
    clips from 5 speakers ([results](../../eval/results/stt_results.md), #41)
  - search: BM25 with query normalization, and hybrid search with embeddings as an option
    ([comparison](../../eval/results/retrieval_comparison.md), #31, #39)
  - answers: gpt-oss-120b speaking as the exhibit and citing passages (#14)
  - checks: the reply check (#28, #62), the claim checker in `/ask`
    ([results](../../eval/results/claims_results.md), #40, #60), the quote checker
    ([results](../../eval/results/quotes_results.md), #42), the time check with Wikidata dates
    ([results](../../eval/results/timecheck_results.md), #43) and the question classifier
    ([results](../../eval/results/classifier_results.md), #52)
  - topic tags on the curator page ([results](../../eval/results/topics_results.md), #61), and
    translation of other languages for search (#50)
- The north star across sessions: 59 of 64 in Sessions 7 and 10 on gpt-oss-120b, and 55 in
  Session 8 on llama3 ([comparison](../../eval/results/north_star_comparison.md)), rescored with
  the fairer key-fact check (#72), and the final number on the visitor-written questions.
- Persona against a plain museum guide on the same passages: a paired McNemar test with a
  Newcombe interval (last run on the Session 5 answers: -2.3 points, p = 1.00,
  [results](../../eval/results/compare_modes.md), #30; rerun on the current code in #73).
- Robustness: 20 adversarial prompts for Van Gogh, 16 held and then 19 after the reply check fix
  (#54, #62). With 5 for the T. rex (#80), 23 of 25 held on gpt-oss-120b: 19 of 20 for Van Gogh and
  4 of 5 for the T. rex. Both failures explained a made-up quote as if it were real
  ([results](../../eval/results/robustness_results.md), #83).
- Other languages: the language of 12 of 12 questions per exhibit was detected correctly, and in
  Session 9 all 9 Van Gogh questions were answered in the visitor's language (#50). The committed
  T. rex replies come from the offline stand-in, not the model, so the T. rex result needs a rerun
  on gpt-oss-120b before it goes in ([results](../../eval/results/multilingual_results.md), #63).
- Course topics this touches: hypothesis testing, evaluation, embeddings, classifiers, retrieval
  augmented generation, knowledge graphs (Wikidata) and bias and ethics.
- What did not work, with numbers. Candidates: the topic rules miss words that are not on their
  lists (0 of 2 on death and extinction, #61), the year rule catches only after-time questions
  that name a year (0 of 16 on the time check set, #52), the claim checker logs unbacked details
  but does not block them (#60), and the quote checker is not in `/ask` (#42).

## User evidence

Ten people from outside the team, P1 to P10, used the running product in five rounds. All of them
were friends, roommates or neighbours of the team, not museum visitors we recruited. Each round has
a task sheet, a record per person, their exported question log and a README in
[`artifacts/evidence/`](../../artifacts/evidence/).

| Round | People | Setup | Tasks completed | Would use it in a museum (1 to 5) |
|---|---|---|---|---|
| Session 5, September 29 | P1 | laptop, localhost | 2 of 2 | 3.5 |
| Session 7, October 20 | P2 to P4 | laptop, localhost | 10 of 15, 4 partly | 3.5, 3, 4 |
| Session 8, October 26 | P5, P6 | laptop, localhost | 9 of 11 | 4, 5 |
| Session 11, November 17 | P7 | own phone, tunnel | 3 of 3 | 3.5 to 4 |
| Session 12, November 24 | P8 to P10 | own phone, tunnel | TODO | TODO |

**What people did.** They asked each exhibit questions by voice, from tasks we read out (Sessions 5
and 11), from goals they put in their own words (Sessions 7 and 8), and from questions they wrote
down before seeing the app (Session 12). The tasks covered questions the sources answer, questions
they don't, off-topic questions, fixing a misheard question, and in Session 12 a typed question in
another language.

**What went wrong, and what we changed.**

- **Speech to text misheard people.** In Session 7, 6 of 12 spoken questions came out garbled, and
  all three people brought it up. We moved Session 8's work to speech to text (#41): Whisper small
  with each exhibit's vocabulary as a prompt, and the transcript shown before the exhibit answers,
  so it can be fixed or recorded again. In Session 8, 4 of 11 were still misheard, but the "not sure"
  warning flagged 3 of them, P6 fixed 2 before sending, and both people rated seeing the transcript
  4.5 out of 5. P7's 3 questions were all heard right, but they were short and read from a sheet.
- **Answers added true details that their sources don't contain** ("July 1890" in Session 7,
  hatchling weights in Session 8). Our offline evaluation had not shown this; the user tests did. It
  led to the claim checker (#40, #60), which now flags these details in `/ask` but does not block them.
- **Searches missed passages that were there** (Theo's job in Session 7, the skull length in
  Session 8), so the guide declined questions it could have answered. These are the same misses as
  held-out questions vg-03 and tr-h03.
- **Holding the button cut questions off** (Session 5), and **people corrected themselves out loud**
  instead of editing the transcript (P5, Session 8). We have not changed either: the page is still
  hold to ask, and a spoken "actually" is sent as part of the question.
- **The tunnel was fragile** (Session 11): the link showed "Bad gateway" until the model key was
  set, dropped when the laptop slept, and crawlers found the public page within minutes. The README
  now says to keep the laptop awake and to try HTTP/2, and the Session 12 sheet closes the tunnel
  between people.
- **The look of the page** was P7's first request. TODO: what Session 12 adds.
- Session 12: TODO, the three biggest problems P8 to P10 hit, from
  [`session12/README.md`](../../artifacts/evidence/session12/).

**What people asked.** The 30 questions real visitors asked in the user tests are part of the topic
tagging test for the curator page, and the rules tag 29 of them correctly
([results](../../eval/results/topics_results.md), #61). The questions P8 to P10 wrote before using the
app are the test set for the final numbers (#82), so nobody on the team wrote them.

## Ethics and limitations

- Data and licences: CC0, CC BY-SA, CC BY 4.0 and public domain, with the credit kept on every
  passage ([data sources](../../artifacts/data_sources.md)).
- Privacy: audio is never saved, the request logs stay out of the repo, and the evidence is
  anonymized.
- Honesty: it says it is an AI when asked (#62), and the voice is made up, not a clone of anyone.
- Bias: speech recognition by speaker (#41), and voice in English only (#71).
- Limits: two exhibits, one model on a free tier with daily token limits, a laptop and a tunnel
  instead of hosting, small user tests, and test sets for some checks written by the same person
  who wrote the rules (#52, #61).
- Something that did not work, named plainly, from the candidates above.
