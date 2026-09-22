# Roadmap

Echoes.ai, version 2, September 22, 2026. Owned by Pratham.

We want to build something a museum would actually use, and we want to learn real NLP while we
do it. So each week one of us builds a piece of the system, tests it on questions it hasn't
seen, and merges it with a number attached. We don't count something as done if it's just a
call to someone else's API.

When we say we want to scale it, we mean three things. First, more artists: Van Gogh now, then
a second artist to show the pipeline isn't hand-built for one person, then any painting in the
Met or Art Institute of Chicago collections. Second, more visitors, through voice and later
other languages. Third, answers museums can trust, because every answer is checked against a
source.

## Until the mid-semester presentation (October 6)

| Session | Who | What | How we'll know it works |
|---|---|---|---|
| 4 | Surabhi | Pick the Van Gogh sources and write down why, with licences | `artifacts/data_sources.md` merged |
| 5 | Saurabh | Voice loop: Whisper for speech to text, Kokoro for speech | Seconds from question to answer |
| 5 | Saurabh | Keyword search (BM25) over the letters and descriptions | Recall@5 |
| 5 | Pratham | Van Gogh persona that cites sources, plus a plain "museum guide" version to compare against | Grounded answer accuracy |
| 5 | Surabhi | Held-out questions: facts, dates, events after 1890, quote requests, off topic | Written before we see any answers |
| 5 and 6 | Kshiti | Recorded task tests with 3 to 5 people from outside the team | How many tasks they finish |
| Every week | Aditi | Board, issues and the weekly report | Report merged on time |

On October 6 we want to talk to Van Gogh live in class, show our first accuracy number next to
the plain guide, show what outside users did with it, and say whether we keep going or change
direction.

## Sessions 7 to 9: the NLP work

- Saurabh: search that matches on meaning as well as keywords (embeddings, then a reranker).
  We compare Recall@5 and MRR against the BM25 version.
- Surabhi: an answer checker that breaks each answer into claims and tests every claim against
  the source with an NLI model. We check it against our own labels.
- Pratham: "Did Van Gogh really say that?" A quote checker that looks for a quote in his
  letters, using fuzzy and meaning-based matching. Scored on real quotes and made-up ones.
- Kshiti: a classifier that sorts visitor questions into types (fact, opinion, personal, off
  topic, after 1890, unsafe). We label real questions together, check how much we agree, and
  fine-tune a small model.
- Aditi: a lifetime check. It finds names and events in a question, looks up their dates on
  Wikidata, and flags anything after 1890 so the persona doesn't pretend to know about it.
- Pratham: a significance test on whether the persona really is less accurate than the plain
  guide, or whether the gap is noise.

## Sessions 10 to 12: scaling up

We'll pick two or three of these depending on what users ask for:

- a second artist, and then building personas automatically from museum and Wikidata records
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
- Version 2, September 22: the team decided to start with Van Gogh only and to begin voice work
  in Session 5.
