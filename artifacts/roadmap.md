# Roadmap

Echoes.ai, version 6, November 16, 2026. Owned by Pratham.

We want to build something a museum would actually use, and we want to learn real NLP while we
do it. So every week each of us builds a piece of the system, tests it on questions it hasn't
seen, and merges it with a number attached. We don't count something as done if it's just a
call to someone else's API.

The system is built to work for any exhibit, not one specific person. The speech, search,
answering and voice parts stay the same whatever the exhibit is. Only the source texts and a
small settings file change. We test it on two very different exhibits: Vincent van Gogh, a
person who left his own letters, and Tyrannosaurus rex, a creature known only through what
scientists have written. If one of them turns out to be a poor fit, we can swap in another
exhibit without rebuilding anything.

When we say we want to scale it, we mean three things. First, more exhibits: two very different
test exhibits now, then a third of another kind (an object), then exhibits built automatically
from museum records. Second, more visitors, through voice and later other languages. Third,
answers museums can trust, because every answer is checked against a source.

## Until the mid-semester presentation (October 6)

Everyone has something to build each session. The dates here are the course deadlines we have
to hit. The schedule in `artifacts/architecture.md` is the engineering build order for the
voice pipeline, so where the two differ, these dates are the ones that decide our grade.

**Session 4: plan the product and pick the data (done)**

- Pratham: lean canvas and roadmap
- Surabhi: choose the pilot persona's sources, with licences and known problems
- Saurabh: system design, diagrams, and repo setup
- Kshiti: user research plan and the evidence folder
- Aditi: board, issues, milestones, and the weekly report

**Session 5: a working system for two exhibits, and our first numbers (issues #11 to #15, done)**

- Saurabh (#11): repo skeleton, the server and speech to text, with every step timed
- Surabhi (#12): one script that builds the corpus for any exhibit, run for Van Gogh and T. rex,
  and 22 held-out questions per exhibit
- Aditi (#13): keyword search (BM25) with its evaluation, and the Session 5 report
- Pratham (#14): the answer engine, which adapts to the kind of exhibit, plus a plain museum
  guide as the baseline and the evaluation that compares them
- Kshiti (#15): the phone page and text to speech (moved from #11), plus the materials for
  the recorded tests with people from outside the team, which run before October 6

**Session 6 (October 6): the presentation (done)**

- Saurabh: the live demo, with a recorded backup
- Surabhi: the accuracy number next to the plain guide baseline
- Kshiti: what the outside users actually did, and what we changed because of it
- Pratham: the pitch, and the pivot or persevere call
- Aditi: slides put together, timing, and a rehearsal

## Sessions 7 to 9: the NLP work

The plan slipped by a week. Session 7 went into a shared test setup, more held-out questions and
fixing failures we had measured, so the NLP components started in Session 8.

**Session 7 (October 20): tests, more questions and measured fixes (done)**

- Pratham (#32, #30): the shared test setup with a test report for every pull request, and a
  paired test of whether the persona is less accurate than the plain guide
- Surabhi (#27): 20 more held-out questions and stricter checks on the question files
- Aditi (#31): T. rex search fixes, checked on 10 new T. rex questions written before tuning
- Saurabh (#29): clearer answer states and source cards on the phone page
- Kshiti (#28): a check on every model reply before the visitor sees it, and user tests with
  three people from outside the team

**Session 8 (October 27): the NLP components (issues #39 to #43)**

- Saurabh (#39): search that matches on meaning as well as keywords (embeddings combined with
  BM25), and install steps that work on a fresh clone
- Surabhi (#40): a claim checker that flags dates, numbers and names the cited passage does not
  contain, and the north star measured again on what is on main
- Kshiti (#41): speech to text tuned to each exhibit and measured by word error rate, a
  transcript the visitor can fix before sending, and user tests with two people
- Pratham (#42): a quote checker ("did you really say that?") that looks for a quote in the
  exhibit's own words, plus this roadmap and the lean canvas
- Aditi (#43): a time-boundary check that looks up dates on Wikidata, and the Session 8 report

The question classifier planned for Kshiti moved to the Sessions 10 to 12 list. Session 8 went
to speech to text instead, because all three people in the Session 7 user tests brought up being
misheard.

**Session 9 (November 3): the checks in the product (issues #50 to #54)**

- Surabhi (#50): replies in the visitor's language for typed questions in Hindi, Marathi and
  Spanish, with the question turned into English keywords for search
- Saurabh (#51): Docker, and a free Cloudflare tunnel with QR codes, so phones can use the
  microphone. There is no permanent link: Docker Spaces on Hugging Face now need a paid plan, and
  we are not spending money on this
- Pratham (#52): a question classifier that answers clearly off-topic questions without search
  or the model
- Aditi (#53): the curator stats page, and the Session 9 report
- Kshiti (#54): 20 adversarial prompts with an automatic check (16 of 20 held)

We had planned to connect all the Session 8 checks to `/ask` and measure the north star with and
without them. Only the claim checker went in, a week later (#60), and the with-and-without run
did not happen. The quote checker's misses on short quotes and other translations were not fixed.

Owners for Session 9 onwards are picked when we write the issues each week.

## Sessions 10 to 12: scaling up, then getting ready for demo day (November 10, 17 and 24)

We planned to pick two or three of these, depending on what users asked for. We did four:

- answers in Hindi, Marathi, Kannada and Spanish (#50, #63), typed only so far; voice is #71
- a curator dashboard that groups visitor questions by topic (#53, #61)
- testing whether people can trick the persona into breaking its rules (#54, #62)
- the question classifier (#52)

We dropped the other two, because there were not enough weeks left:

- a third exhibit of a new kind (an object), and building exhibits automatically from museum and
  Wikidata records. A new exhibit still needs only a `persona.json` and its sources.
- speech recognition errors by accent, and art words like "chiaroscuro". We measured the word
  error rate per speaker in Session 8 (#41) and did not go further.

**Session 10 (November 10): numbers on the same model (issues #60 to #64)**

- Aditi (#64): the north star again on gpt-oss-120b. It was 59 of 64, the same as Session 7, so
  the Session 8 drop came from llama3, not our code. Also the Session 10 report
- Saurabh (#60): the claim checker in `/ask`, behind `ENABLE_CLAIMS`. It logs details the cited
  passages do not contain, but does not block them
- Kshiti (#62): the reply check now keeps honest "I am an AI guide" answers, and robustness went
  from 16 to 19 of 20
- Pratham (#61): visitor questions grouped by topic on the curator page, with 29 of 30 real
  visitor questions tagged right
- Surabhi (#63): other languages for the T. rex as well, and Kannada

**Session 11 (November 17): users again, and the last new features (issues #70 to #74)**

- Kshiti (#70): a user test on people's own phones through the tunnel, our first since Session 8.
  The testers also write the questions for the final numbers, so nobody on the team writes them
- Saurabh (#71): spoken questions and answers in Hindi and Spanish
- Surabhi (#72): key-fact scoring that accepts number words and synonyms, with Sessions 7, 8 and
  10 rescored the same way, and why vg-07 and vg-08 fail
- Aditi (#73): the plain guide on gpt-oss-120b, the persona against it, and the Session 11 report
- Pratham (#74): the demo script, the outline of the final report, a README setup test with
  someone from outside the team, and this roadmap

Our demo day slot is assigned in this session.

**Session 12 (November 24): the final numbers**

The last weekly report. The final numbers are measured once, on the questions the Session 11
testers wrote, with gpt-oss-120b, the model in the demo. We also make the slides and record the
backup demo.

## Demo day (Sessions 13 and 14: December 1 and 8)

Everything is due at 5:00pm on Tuesday December 1, whichever of the two days we present.
Nothing committed after that is graded. On `main`, in `reports/final/`:

- `README.md`: a short summary, the live link and setup instructions
- slides, as a PDF or Markdown with the images committed
- `report.md`: 2 to 5 pages with the five areas as headings (problem and users, product, NLP
  method and evaluation, user evidence, ethics and limitations)
- optionally `demo.mp4`, a recorded demo

The talk is 12 minutes plus 3 for questions, with a demo; if it is live, we bring a recorded
backup. Before submitting we check that a stranger can set it up from the README, that the model
we report numbers for is the one in the demo, and that we name something that did not work.

## Course topics this touches

Hypothesis testing (week 1), evaluation (week 3), embeddings and lexical semantics (week 4),
neural classifiers (week 5), transformers and BERT-style models (weeks 7 and 8), retrieval
augmented generation (week 10), knowledge graphs (week 11), and bias and ethics (week 12).

## Rules we agreed on

- Something gets merged every week, with a number we can compare to last week.
- The model we report numbers for is the one running in the demo.
- From Session 5, someone outside the team uses the product every week, and we commit what we
  recorded that same week.
- If something does worse than its baseline, we say so.
- Every pull request gets an approving review from a teammate before it merges.
- Evidence for a claim is committed in the same week the claim is made.

## Changes

- Version 1, September 21: first version, planned around 10 artworks from the Met.
- Version 2, September 22: the team decided to start with one persona and to begin voice work in
  Session 5.
- Version 3, September 22, after Saurabh's review: written so the plan works for any persona
  with Van Gogh as the pilot, and the schedule now lists what each of us does every session.
- Version 4, September 29: extended from people to any exhibit, with T. rex as the second test
  exhibit; Session 5 now matches issues #11 to #15, and the Sessions 7 to 9 components work
  for any exhibit type.
- Version 5, October 25: the real schedule. Session 7 lists what we did, Session 8 matches issues
  #39 to #43, the question classifier moved to Sessions 10 to 12, and the plan now runs to demo
  day on December 1 and 8.
- Version 6, November 16: Sessions 9 and 10 as they went, Session 11 matches issues #70 to #74,
  Session 12 holds the final run, the https link is a free Cloudflare tunnel instead of Hugging
  Face Spaces (#51), and we list what we dropped from the scaling list.
