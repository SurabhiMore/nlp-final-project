# Lean canvas

Echoes.ai, version 2, September 22, 2026. Pratham keeps this page up to date and we go over it
as a team every week.

## Value proposition

We help museum visitors understand what they are looking at by letting them talk to the figure
behind the exhibit, with answers taken from real sources. It is more engaging than a plaque and
more flexible than a pre-recorded audio guide.

## Users and their problem

Visitors: an audio guide plays the same recording for everyone. If you want to know why an
artist painted the same bedroom three times, you can't ask it. Most people glance at the plaque
for a few seconds and move on.

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

Where we are different: you talk instead of type, there is nothing to install, and every
answer comes from a source we can point to. We also measure how accurate the answers are and
report that number.

## How it works

A visitor scans a QR code next to an exhibit, which opens a page on their phone. They ask a
question out loud. We turn the speech into text, search that exhibit's sources for relevant
passages, and have the model answer in the figure's voice while citing where the answer came
from. If the sources don't cover the question, it says so instead of guessing. The answer is
read back as speech.

The system doesn't depend on any one figure. Everything except the source texts and a small
settings file is the same for any persona. Our pilot is Vincent van Gogh, because his letters
are free to use and two open museum collections hold his paintings. If he turns out to be a
poor fit, we can swap in another figure without rebuilding the system.

Later, curators get a page where they can upload material for their own exhibits and see what
visitors ask.

## How users find it

Visitors find it through the QR code next to each exhibit. For museums, we want to pilot with
a campus gallery, which we haven't contacted yet. Until then we will test with classmates from
outside our team on a mock gallery walk.

## Cost

During the course it costs nothing. We use Whisper for speech to text (MIT licence), Kokoro for
text to speech (Apache 2.0), a free LLM tier or a local open model, and free hosting on Hugging
Face Spaces.

One visitor question is roughly 10 seconds of audio to transcribe, one LLM call with about
1,500 tokens in and 150 out, and 15 seconds of speech to generate. We will log the real numbers
in Session 5. We are aiming for under one cent per question, but that is a guess until we
measure it.

## The number we watch

Grounded answer accuracy: out of a held-out set of visitor questions, how many does the guide
answer correctly with support from a source. We write the questions before we look at any model
answers. We also track how long a reply takes (the goal is under about two seconds) and how many
questions a visitor asks.

## Ethics and privacy

Data. The Met's open dataset is CC0, so we can use it freely, but we still credit the Met and
never suggest they endorse us. It has no descriptive text, so we also use Wikipedia (CC BY-SA,
which requires credit) and Art Institute of Chicago descriptions (CC BY 4.0, credit to
artic.edu). Every passage we store keeps a note of where it came from.

Voice. A recording of someone's voice is personal data. By default we won't keep raw audio,
only anonymized transcripts, and the QR page will say so. Some visitors will be children.

Honesty. The guide says it is an AI. We use a made-up voice, never a clone of a real person's
voice.

Bias. Speech recognition does worse with accented speech, so we will measure errors by accent.

When it's wrong. It cites its source, admits when it doesn't know, and has a "report a wrong
answer" button. Those reports feed our error analysis.

## Risks

1. It makes things up and museums stop trusting it. Test: 20 trap questions (dates, events
   after the persona's lifetime, fake quotes) on the first prototype, in Session 5.
2. Voice is too slow to feel like a conversation. Test: time one full round trip on free
   hardware, in Session 5.
3. People feel awkward talking out loud in a quiet gallery. Test: a recorded task test with
   three people from outside the team in a quiet room, in Session 5.
4. Others are already doing this. Test: focus on measured accuracy, and ask a curator what they
   would actually need, before October 6.
5. The sources are too thin to answer "why" questions. Test: check how many of our test
   questions the persona's own writing and its Wikipedia article can answer, in Session 5.
   If a figure has too little written material, that is a reason to pick a different one.

## Changes

- Version 1, September 21: first version. After downloading the Met dataset we found it has no
  descriptive text, so we added the persona's own letters and Wikipedia as sources, and added
  risk 5.
- Version 2, September 22, after Saurabh's review: rewritten so it works for any exhibit figure,
  with Van Gogh named as the pilot rather than assumed throughout.
