# Lean canvas

Echoes.ai, version 5, November 16, 2026. Pratham keeps this page up to date and we go over it
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

Questions typed in Hindi, Marathi, Kannada or Spanish get answers in the same language
(#50, #63). Voice is English only so far (#71).

Curators get a page (`/stats.html`) that shows what visitors ask, grouped by topic, and which
questions the sources could not answer (#53, #61). Uploading material for new exhibits is still
for later.

## How users find it

Visitors find it through the QR code next to each exhibit, which links straight to that
exhibit (`/?persona=<id>`). For museums, we want to pilot with a campus gallery, which we
haven't contacted yet. Until then we test in person with people from outside the team: one in
Session 5, three in Session 7 and two in Session 8, all on a laptop, and in Session 11 on
people's own phones (#70). A QR code needs an https link, so for each test session a free
Cloudflare tunnel gives us one, but only while a laptop runs the server (#51).

## Cost

During the course it costs nothing. We use Whisper for speech to text (MIT licence), Kokoro for
text to speech (Apache 2.0), and a free LLM tier or a local open model. It runs on our laptops,
with a free Cloudflare tunnel for user tests on phones. We dropped the plan to host it on Hugging
Face Spaces, because Docker Spaces now need a paid plan and we aren't spending money on this.

One visitor question is roughly 10 seconds of audio to transcribe, one LLM call with about
2,000 tokens in (eight passages plus the question) and 150 out, and 15 seconds of speech to
generate. On a free LLM tier that is no money, only rate limits, and those limits already
matter: the 128-call answer evaluation in Session 7 hit Groq's daily limit and needed a second
key, and a 64-question run in Session 10 used about 180K of the 200K tokens a day. We are aiming
for under one cent per question on a paid tier, but that is a guess until we log real token
counts.

## The number we watch

Grounded answer accuracy: out of a held-out set of visitor questions (now 64, 32 per exhibit,
18 of them traps), how many does the guide answer correctly with support from a source. Trap questions (after the exhibit's time, not in
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

## Numbers now (Session 10)

| Measure | Van Gogh | T. rex |
|---|---|---|
| Grounded answer accuracy, persona | 0.938 (30 of 32) | 0.906 (29 of 32) |
| Trap questions declined | 9 of 9 | 9 of 9 |

Same model as Session 7 (openai/gpt-oss-120b, low reasoning effort, 8 passages per question) and
the same 64 questions, so the totals compare directly: 59 of 64 both times, after the classifier,
the claim checker and the language changes went in ([comparison](../eval/results/north_star_comparison.md)).
3 of the 5 misses are correct answers in other words that the strict check does not accept. #72
changes the check and rescores every session the same way. The plain guide was not rerun this
time (#73).

Also measured since Session 7, all on gpt-oss-120b: 19 of 20 adversarial prompts held (#62), the
classifier blocked 0 of 98 questions it must let through (#52), the topic tags were right on 29 of
30 real visitor questions (#61), the language of 12 of 12 questions per exhibit in Hindi, Marathi,
Kannada and Spanish was detected correctly, and in Session 9 all 9 Van Gogh questions in Spanish,
Hindi and Marathi were answered in the same language (#50, #63).

## Session 7 numbers

| Measure | Van Gogh | T. rex |
|---|---|---|
| Grounded answer accuracy, persona | 0.97 (31 of 32) | 0.88 (28 of 32) |
| Grounded answer accuracy, plain guide | 0.97 (31 of 32) | 0.88 (28 of 32) |
| Trap questions declined, both modes | 9 of 9 | 9 of 9 |
| Search: supporting passage in the top 5 | 0.87 | 0.74 |
| Search: supporting passage in the 8 the model sees | 0.87 | 0.96 |

Same model as Session 5 (openai/gpt-oss-120b, low reasoning effort, 8 passages per question),
on 32 held-out questions per exhibit, so not the same question set as the table above. The answer numbers use passages frozen before the Session 7
search change ([summary](../eval/results/grounding_summary.md)), and #40 reruns them on what is
on main now. Persona against plain guide, paired test on the Session 5 run: -2.3 points, 95%
interval -12.1 to +7.0, p = 1.00, so no evidence of a difference.

What three people from outside the team did in Session 7 ([evidence](evidence/session07/)):
10 of 15 tasks completed, 4 partly and 1 not. Would use it in a museum: 3.5, 3 and 4 out of 5.
Speech to text misheard 6 of the 12 spoken questions. The answer was on screen a median of 1.2
seconds after the question; the first spoken word took 6.6 seconds in Session 5 and has not been
measured again.

## Ethics and privacy

Data. The Met's open data and the Smithsonian's open access records are CC0, so we can use
them freely, but we still credit both and never suggest they endorse us. We also use Wikipedia
(CC BY-SA, which requires credit), Art Institute of Chicago descriptions (CC BY 4.0, credit to
artic.edu) and Van Gogh's letters from Project Gutenberg (public domain in the US). Every
passage we store keeps a note of where it came from and its licence.

Voice. A recording of someone's voice is personal data. We never save the audio; it is turned
into text in memory. Request logs stay out of the repo, and only anonymized extracts go into
our evidence folder. Some visitors will be children.

Honesty. The guide says it is an AI when asked, and our reply check keeps that answer (#62). We
use a made-up voice, never a clone of a real person's voice.

Bias. Speech recognition does worse with accented speech. In Session 7 it misheard 6 of the 12
spoken questions. In Session 8 we measured it on 40 recorded questions from 5 speakers: a word
error rate of 0.053 with the small model and the exhibit prompt (#41). Voice is English only, so
visitors who speak other languages have to type (#50, #63, #71).

When it's wrong. It cites its source, admits when it doesn't know, and only quotes passages
marked as the exhibit's own words. Session 7 showed a gap: an answer can cite a real passage and
still add a detail that passage does not have. So we built checks that test answers against
their sources. The claim checker runs on every answer in `/ask` and logs dates, numbers and names
the passages do not contain (#40, #60), but does not block them yet. The quote checker (#42) is
not connected to `/ask`. Wrong answers found in testing feed our error analysis.

## Risks

1. It makes things up and museums stop trusting it. Test: 64 held-out questions including 18
   traps, scored for the persona and for a plain guide; all 18 traps were declined in both modes
   in Session 7. Found in Session 7: two answers cited a real passage but added a detail it does
   not have ("July 1890"), and a participant rated one of them 5 of 5 for believing it. Next: the
   claim checker (#40) and the quote checker (#42). The quote checker gets 44 of 46 held-out
   quotes right (0.957) and called no false quote word for word
   ([results](../eval/results/quotes_results.md)). Session 10: the claim checker runs in `/ask`
   (#60), and 19 of 20 adversarial prompts held. The one that failed agreed that Theo was older
   than Vincent, which he was not (#62).
2. Voice is too slow to feel like a conversation. Found in Session 5: on a laptop CPU, the
   large Whisper model took about 14 seconds per question, so we use a smaller one on a CPU.
   Found in Session 7: the answer is on screen about 1.2 seconds after the question, but the
   first spoken word took 6.6 seconds when last measured. Across all 30 user test questions, the
   server took a median of 1.1 seconds to answer, and the slowest 5% took about 8 seconds. The
   time to the first spoken word is measured again in #71.
3. People feel awkward talking out loud in a quiet gallery. Test: recorded task tests with
   people from outside the team. Found in Session 7: 12 of 15 questions were asked by voice, and
   what people complained about was being misheard, not talking out loud (risk 7). Those tests
   were on a laptop, not in a quiet gallery.
4. Others are already doing this. Test: focus on measured accuracy, and ask a curator what they
   would actually need (still not done; the topic page in #61 is our guess at it).
5. The sources are too thin to answer "why" questions. Partly addressed: we added Van Gogh's
   letters and museum descriptions after finding the Met data has no descriptive text.
6. Exhibits without their own words, like the T. rex, must not state debated science as fact.
   Test: the T. rex questions about speed, feathers and hunting check that the answer says
   scientists disagree.
7. Speech to text mishears questions, especially names. Found in Session 7: 6 of 12 spoken
   questions were misheard, all three people brought it up, and one switched to typing. Test:
   word error rate on recorded questions for several speech settings, and a transcript the
   visitor can fix before the question is sent (#41). Result: a word error rate of 0.053 on 40
   clips from 5 speakers with the small model and the exhibit prompt, and the transcript box is in
   the product.

## Changes

- Version 1, September 21: first version. After downloading the Met dataset we found it has no
  descriptive text, so we added the persona's own letters and Wikipedia as sources, and added
  risk 5.
- Version 2, September 22, after Saurabh's review: rewritten so it works for any exhibit figure,
  with Van Gogh named as the pilot rather than assumed throughout.
- Version 3, September 29: extended from people to any exhibit, with T. rex as a second test
  exhibit; added the first Session 5 numbers, the latency finding and risk 6.
- Version 4, October 25: added the Session 7 numbers and user test results, updated risks 1 to 4
  with what Session 7 showed, added risk 7 (misheard questions), and added the claim and quote
  checkers to what happens when it's wrong.
- Version 5, November 16: replaced the Hugging Face Spaces plan with a laptop and a free
  Cloudflare tunnel, because Docker Spaces now need a paid plan (#51); added the Session 10
  numbers, other languages, the curator page and the Session 8 speech results; updated risks 1, 2,
  4 and 7.
