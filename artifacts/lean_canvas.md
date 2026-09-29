# Lean canvas

Echoes.ai, version 3, September 29, 2026. Pratham keeps this page up to date and we go over it
as a team every week.

## Value proposition

We help museum visitors understand what they are looking at by letting them talk to the
exhibit itself, whether it is a person, a creature or an object, with answers taken from real
sources. It is more engaging than a plaque and more flexible than a pre-recorded audio guide.

## Users and their problem

Visitors: an audio guide plays the same recording for everyone. If you want to know why an
artist painted the same bedroom three times, or whether a dinosaur really hunted its food, you
can't ask it. Most people glance at the plaque for a few seconds and move on.

Curators and education staff: audio guide devices have to be bought, charged and repaired, and
every new exhibit means recording new tracks.

## What exists today

- Plaques. One paragraph and no follow-up questions.
- Rented audio guides. A fixed script on hardware the museum has to maintain.
- Human docents. The best option, but there are few of them and tours run on a schedule.
- AI chatbots. The Met ran "Chat with Natalie" for a fashion exhibition
  ([article](https://mymodernmet.com/ai-history-chatbots/)), and companies like FeelTheArt and
  [Hello History](https://www.hellohistory.ai/) offer chats with historical figures. These are
  mostly text based, and role-playing language models are known to make up facts and quotes
  ([TimeChara, ACL 2024](https://aclanthology.org/2024.findings-acl.197/)). We couldn't find
  any of them publishing how accurate their answers are.

Where we are different: you talk instead of type, there is nothing to install, it works for
any kind of exhibit, and every answer comes from a source we can point to. We also measure
how accurate the answers are and report that number.

## How it works

A visitor scans a QR code next to an exhibit, which opens a page on their phone. They ask a
question out loud. We turn the speech into text, search that exhibit's sources for relevant
passages, and have the model answer in the exhibit's voice while citing where the answer came
from. If the sources don't cover the question, it says so instead of guessing. The answer is
read back as speech, one sentence at a time.

The system doesn't depend on any one exhibit. Everything except the source texts and a small
settings file is the same for every exhibit. We test it on two very different ones:

- **Vincent van Gogh**, a person who left his own letters. He can quote his own writing and
  cannot know anything after he died in 1890.
- **Tyrannosaurus rex**, a creature with no words of its own. It speaks as a character built
  from what scientists have written, says when scientists are unsure, and never saw a human.

Later, curators get a page where they can upload material for their own exhibits and see what
visitors ask.

## How users find it

Visitors find it through the QR code next to each exhibit, which links straight to that
exhibit (`/?persona=<id>`). For museums, we want to pilot with a campus gallery, which we
haven't contacted yet. Until then we test with classmates from outside our team on a mock
gallery walk.

## Cost

During the course it costs nothing. We use Whisper for speech to text (MIT licence), Kokoro for
text to speech (Apache 2.0), and a free LLM tier or a local open model. For now it runs on our
laptops; we plan to host it for free on Hugging Face Spaces.

One visitor question is roughly 10 seconds of audio to transcribe, one LLM call with about
2,000 tokens in (eight passages plus the question) and 150 out, and 15 seconds of speech to
generate. On a free LLM tier that is no money, only rate limits. We are aiming for under one
cent per question on a paid tier, but that is a guess until we log real token counts.

## The number we watch

Grounded answer accuracy: out of a held-out set of visitor questions, how many does the guide
answer correctly with support from a source. Trap questions (after the exhibit's time, not in
the sources, off topic) count as correct only when the guide declines. We write the questions
before we look at any model answers, and we compare the persona against a plain museum guide
that gets the same passages.

We also track search quality (Recall@5), how long a reply takes, and task success in user tests.

## First numbers (Session 5)

| Measure | Van Gogh | T. rex |
|---|---|---|
| Grounded answer accuracy, persona | 0.86 | 0.86 |
| Grounded answer accuracy, plain guide | 0.91 | 0.86 |
| Search: supporting passage in the top 5 | 0.73 | 0.62 |

Model used: openai/gpt-oss-120b on Groq's free tier, with low reasoning effort. Measured on 22 held-out questions per exhibit. A hand check of 20 random answers agreed with the automatic scoring on all 20. Details in `eval/results/`.

## Ethics and privacy

Data. The Met's open data and the Smithsonian's open access records are CC0, so we can use
them freely, but we still credit both and never suggest they endorse us. We also use Wikipedia
(CC BY-SA, which requires credit), Art Institute of Chicago descriptions (CC BY 4.0, credit to
artic.edu) and Van Gogh's letters from Project Gutenberg (public domain in the US). Every
passage we store keeps a note of where it came from and its licence.

Voice. A recording of someone's voice is personal data. We never save the audio; it is turned
into text in memory. Request logs stay out of the repo, and only anonymized extracts go into
our evidence folder. Some visitors will be children.

Honesty. The guide says it is an AI. We use a made-up voice, never a clone of a real person's
voice.

Bias. Speech recognition does worse with accented speech, so we will measure errors by accent.

When it's wrong. It cites its source, admits when it doesn't know, and only quotes passages
marked as the exhibit's own words. Wrong answers found in testing feed our error analysis.

## Risks

1. It makes things up and museums stop trusting it. Test: 44 held-out questions including
   traps, scored in Session 5 for the persona and for a plain guide.
2. Voice is too slow to feel like a conversation. Found in Session 5: on a laptop CPU, the
   large Whisper model took about 14 seconds per question, so we use a smaller one on a CPU.
   Next: measure the full delay and try a GPU for the demo.
3. People feel awkward talking out loud in a quiet gallery. Test: recorded task tests with
   three people from outside the team, before the October 6 presentation.
4. Others are already doing this. Test: focus on measured accuracy, and ask a curator what they
   would actually need, before October 6.
5. The sources are too thin to answer "why" questions. Partly addressed: we added Van Gogh's
   letters and museum descriptions after finding the Met data has no descriptive text.
6. Exhibits without their own words, like the T. rex, must not state debated science as fact.
   Test: the T. rex questions about speed, feathers and hunting check that the answer says
   scientists disagree.

## Changes

- Version 1, September 21: first version. After downloading the Met dataset we found it has no
  descriptive text, so we added the persona's own letters and Wikipedia as sources, and added
  risk 5.
- Version 2, September 22, after Saurabh's review: rewritten so it works for any exhibit figure,
  with Van Gogh named as the pilot rather than assumed throughout.
- Version 3, September 29: extended from people to any exhibit, with T. rex as a second test
  exhibit; added the first Session 5 numbers, the latency finding and risk 6.
