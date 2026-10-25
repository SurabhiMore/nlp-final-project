# Roadmap

Echoes.ai, version 5, October 25, 2026. Owned by Pratham.

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

**Session 9 (November 3): the checks in the product**

- Connect the Session 8 checks to `/ask`, each behind a setting so it can be switched off, and
  measure the north star with and without them.
- Fix what the Session 8 results show. For the quote checker that means short quotes, and
  quotes from other translations of the letters, which need meaning-based matching.
- Put the product on a public https link, so user tests can run on phones from the QR code.

Owners for Session 9 onwards are picked when we write the issues each week.

## Sessions 10 to 12: scaling up (November 10, 17 and 24)

We'll pick two or three of these depending on what users ask for:

- a third exhibit of a new kind (an object), and then building exhibits automatically from
  museum and Wikidata records
- answers in Hindi, Marathi, Kannada and Spanish
- speech recognition errors by accent, and teaching it art words like "chiaroscuro"
- a curator dashboard that groups visitor questions by topic
- testing whether people can trick the persona into breaking its rules
- the question classifier (moved from Sessions 7 to 9)

Fixed dates in these weeks:

- Session 11 (November 17): our demo day slot is assigned.
- Session 12 (November 24): the last weekly report. Final numbers are measured on held-out
  questions with the model that runs in the demo.

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
