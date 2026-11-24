# Echoes.ai: final report

Draft, November 23 (#86). "Problem and users" is written. The other four sections are outlines
until their owners write them: Product (Saurabh, #84), NLP method and evaluation (Surabhi, #82),
User evidence (Kshiti, #83) and Ethics and limitations (Aditi, #85). The finished report is 2 to 5
pages. The final numbers come from one run on the questions visitors write (#70, #82), with
`openai/gpt-oss-120b`, the model in the demo.

## Problem and users

Museum visitors give a plaque a few seconds and move on. An audio guide plays the same recording to
everyone and can't take a question, and a human docent, the best option, is rare and runs on a
schedule. Curators have their own problem: guide devices have to be bought, charged and repaired,
and every new exhibit means recording new tracks ([lean canvas](../../artifacts/lean_canvas.md)).

Talking to a historical figure through AI is not new. The Met ran "Chat with Natalie" for a
fashion exhibition ([article](https://mymodernmet.com/ai-history-chatbots/)), and
[Hello History](https://www.hellohistory.ai/) offers chats with historical figures. These are
mostly text, none we found says how accurate its answers are, and language models that play a
character are known to make up facts and quotes
([TimeChara, ACL 2024](https://aclanthology.org/2024.findings-acl.197/)).

Echoes.ai lets a visitor scan the QR code next to an exhibit and ask it a question out loud on
their own phone, with nothing to install. The exhibit answers in its own voice, from sources it
cites, and says so when its sources don't cover the question. The same code runs two very
different exhibits: Vincent van Gogh, who left his own letters, and a Tyrannosaurus rex, known
only through what scientists have written.

Our users are museum visitors, some of them children, and the curators who run the exhibits and
want to know what visitors ask. Seven people from outside the team tried it in Sessions 5, 7, 8 and
11, on a laptop at first and in Session 11 on their own phone (see User evidence).

We judge it by one number, grounded answer accuracy: of the held-out visitor questions, how many
get a correct answer backed by a cited source. A question the exhibit should not answer, such as
one about something after its time, counts as correct only when it declines.

## Product

### What a visit looks like

A visitor walks up to an exhibit and scans the QR code beside it. A page opens on their own phone,
with nothing to install and no account. It opens on that exhibit, with its picture and colours at
the top and a greeting in its voice: "Hello, small mammal. I am Tyrannosaurus rex." (#15, #84).

They hold down the round talk button, ask their question out loud and let go. Before anything is
answered, the page shows what it heard in an "I heard" box. The visitor can fix a word, record
again or send it. If speech recognition was unsure, the box says so and asks them to check it.
We added this step after the Session 7 user tests, where 6 of 12 spoken questions were misheard
(#41). Visitors can also type instead.

The answer appears as text within about a second and is then spoken in the exhibit's own voice,
one sentence at a time. Each next sentence is made while the current one plays (#15). Under the
answer are source cards: which museum or encyclopedia each fact came from, its licence, and the
passage itself (#29). When the sources don't cover a question, the exhibit says so ("I have no
record of a childhood dog in my letters") instead of inventing an answer. A question about
something after its time, such as Van Gogh on Guernica, gets a polite refusal. An off-topic
question, such as the capital of France, is turned down at once without calling the language
model (#52). The T. rex can also roar on request: it says a short line, then plays the sound.

Questions can be asked in Hindi, Marathi, Kannada and Spanish, and the answer comes back in the
same language (#50, #63). Hindi and Spanish also work by voice, both asked and spoken back (#71).
Marathi and Kannada answers are shown as text only, because Kokoro has no voice for them. Visitors' audio is turned
into text and never saved.

A curator opens "Curator stats" from the footer. It shows how many questions each exhibit got,
what visitors ask about grouped by topic, and which questions the sources could not answer. That
last list shows where a museum could add sources (#53, #61).

### How the parts fit together

```mermaid
flowchart TD
  Phone["Phone page (app/static)"]
  subgraph Laptop["Laptop: one FastAPI server (app/server.py)"]
    STT["/transcribe<br/>Whisper small + exhibit vocabulary prompt"]
    Ask["/ask"]
    CLS["Question classifier<br/>declines off-topic questions at once"]
    RET["Search: BM25, top 8 passages<br/>(other languages translated first)"]
    LLM["gpt-oss-120b on Groq<br/>speaks as the exhibit, cites passages"]
    CHK["Reply check and claim checker"]
    TTS["/speak<br/>Kokoro, the exhibit's voice"]
    LOG[("Question log, no audio")]
    STATS["/stats.html curator page"]
    Ask --> CLS --> RET --> LLM --> CHK
    Ask --> LOG --> STATS
  end
  P[("personas/&lt;exhibit&gt;/<br/>persona.json + licensed passages")]
  Phone -- "1. recording" --> STT
  STT -- "what was heard" --> Phone
  Phone -- "2. checked question" --> Ask
  CHK -- "answer, status, source cards" --> Phone
  Phone -- "3. one sentence at a time" --> TTS
  TTS -- "audio" --> Phone
  P -.-> Laptop
```

The phone page talks to one FastAPI server through four requests. `/transcribe` turns the
recording into text with Whisper. The `small` model gets a vocabulary prompt built from the
exhibit's own names, such as Theo, Arles or Maastrichtian, so it spells them right (#41).

`/ask` does the answering. The question classifier first catches questions the exhibit should not
answer, such as off-topic ones or ones that name a year after the exhibit's time (#52).
Otherwise a BM25 search picks the 8 passages most likely to hold the answer from that exhibit's
sources. Questions in other languages are translated for the search. gpt-oss-120b then answers in
character from those passages and names the ones it used. It also gives the reply a status:
answered, not in the sources, outside its time, or declined. The reply check makes sure what the
visitor sees is backed by the passages. An "answered" reply with no valid citation becomes "not
in my sources". A reply that can't be read, or a decline that answers anyway, is replaced with a
fixed line (#28, #62). The claim checker logs any detail the
passages do not back (#40, #60). The answer comes back with its source cards.

The page then calls `/speak` for each sentence, and Kokoro reads it in the exhibit's voice, or in
a Hindi or Spanish voice when the visitor asked in that language. Every question is logged
without audio, and `/stats` builds the curator page from that log.

Both exhibits run on the same code. Everything that makes Van Gogh different from the T. rex
lives in `personas/<exhibit>/`: `persona.json` (name, time period, speaking style, voice,
greeting and sounds) and the licensed passages it may cite. Adding an exhibit means adding a
folder, not changing code.

It runs on a laptop. A free Cloudflare tunnel gives phones a temporary https link, and
`scripts/generate_qr.py` turns that link into the QR codes. There is no permanent link because
we could not host Whisper and Kokoro for free (#51, section 4.6 of
[`artifacts/architecture.md`](../../artifacts/architecture.md)). The older picture in
`artifacts/images/system_architecture.png` is from the September design. It still shows a
Hugging Face Space and audio streamed in one request, so the diagram above replaces it.

In a rehearsal on November 23, with nothing else running, each step took about this long:

| Step | Time |
|---|---|
| Transcript | 2.6 to 3.0 s |
| Answer text | 0.5 to 1.4 s |
| First spoken sentence | 0.4 to 0.6 s more |

Asking questions back to back hits Groq's free-tier limit per minute, and answers then took 10 to
21 s ([demo script](../../artifacts/demo_script.md)).

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
