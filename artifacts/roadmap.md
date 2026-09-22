# Roadmap

Echoes.ai, version 3, September 22, 2026. Owned by Pratham.

We want to build something a museum would actually use, and we want to learn real NLP while we
do it. So every week each of us builds a piece of the system, tests it on questions it hasn't
seen, and merges it with a number attached. We don't count something as done if it's just a
call to someone else's API.

The system is built to work for any exhibit figure, not one specific person. The speech, search,
answering and voice parts stay the same whoever the persona is. Only the source texts and a
small settings file change. Our pilot persona is Vincent van Gogh, because his letters are free
to use and two open museum collections hold his paintings. If he turns out to be a poor fit, we
can swap in another figure without rebuilding anything.

When we say we want to scale it, we mean three things. First, more personas: the pilot now, then
a second figure to show the pipeline isn't hand-built for one person, then exhibits built
automatically from museum records. Second, more visitors, through voice and later other
languages. Third, answers museums can trust, because every answer is checked against a source.

## Until the mid-semester presentation (October 6)

Everyone has something to build each session. The dates here are the course deadlines we have
to hit. The schedule in `artifacts/architecture.md` is the engineering build order for the
voice pipeline, so where the two differ, these dates are the ones that decide our grade.

**Session 4 (this week): plan the product and pick the data**

- Pratham: lean canvas and roadmap
- Surabhi: choose the pilot persona's sources, with licences and known problems
- Saurabh: system design, diagrams, and repo setup
- Kshiti: user research plan and the evidence folder
- Aditi: board, issues, milestones, and the weekly report

**Session 5: first working loop, and our first numbers**

- Saurabh: voice loop (speech to text, then speech back), with each step timed
- Saurabh: keyword search (BM25) over the persona's sources, measured with Recall@5
- Pratham: the persona prompt with citations, plus a plain "museum guide" version to compare
  against
- Surabhi: build the corpus, and write held-out questions covering facts, dates, events after
  the persona's lifetime, quote requests and off-topic questions
- Kshiti: recruit three people from outside the team and run the first recorded task test
- Aditi: keep the board honest, and write the Session 5 report with our first numbers

**Session 6 (October 6): the presentation**

- Saurabh: the live demo, with a recorded backup
- Surabhi: the accuracy number next to the plain guide baseline
- Kshiti: what the outside users actually did, and what we changed because of it
- Pratham: the pitch, and the pivot or persevere call
- Aditi: slides put together, timing, and a rehearsal

## Sessions 7 to 9: the NLP work

Each of us owns one component, and all of them land in these three weeks.

- Saurabh: search that matches on meaning as well as keywords (embeddings, then a reranker).
  We compare Recall@5 and MRR against the BM25 version.
- Surabhi: an answer checker that breaks each answer into claims and tests every claim against
  the source with an NLI model. We check it against our own labels.
- Pratham: a quote checker ("did they really say that?") that looks for a quote in the
  persona's own writing, using fuzzy and meaning-based matching. Scored on real quotes and
  made-up ones.
- Kshiti: a classifier that sorts visitor questions into types (fact, opinion, personal, off
  topic, outside the persona's lifetime, unsafe). We label real questions together, check how
  much we agree, and fine-tune a small model.
- Aditi: a lifetime check. It finds names and events in a question, looks up their dates on
  Wikidata, and flags anything after the persona died (1890 for Van Gogh) so the guide doesn't
  pretend to know about it.
- Pratham: a significance test on whether the persona really is less accurate than the plain
  guide, or whether the gap is noise.

## Sessions 10 to 12: scaling up

We'll pick two or three of these depending on what users ask for:

- a second persona, and then building personas automatically from museum and Wikidata records
- answers in Hindi, Marathi, Kannada and Spanish
- speech recognition errors by accent, and teaching it art words like "chiaroscuro"
- a curator dashboard that groups visitor questions by topic
- testing whether people can trick the persona into breaking its rules

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

## Changes

- Version 1, September 21: first version, planned around 10 artworks from the Met.
- Version 2, September 22: the team decided to start with one persona and to begin voice work in
  Session 5.
- Version 3, September 22, after Saurabh's review: written so the plan works for any persona
  with Van Gogh as the pilot, and the schedule now lists what each of us does every session.
