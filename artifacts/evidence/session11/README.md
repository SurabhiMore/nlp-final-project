# Session 11 user test: a visitor's own phone

One person from outside the team, P7, used the running product on their own phone, through a free
Cloudflare tunnel to a teammate's laptop. It is our first test on a visitor's own phone, and our
first outside user test since Session 8. Issue #70 planned three people; only one could be done this
week, and more follow in Session 12. People are numbered on from session08 (P5 and P6), so this is
P7.

## Setup

- Date: Tuesday November 17, 2026, 14:20 to 14:21 ET. A first attempt from 08:45 ET left no log
  (see `P7.md`).
- Where: P7's own phone, in the browser, on the https link from a free Cloudflare tunnel to a
  laptop running the server
- Product version: the code on main at aae9925. Language model openai/gpt-oss-120b with low
  reasoning effort, speech to text Whisper small, the question classifier and the claim checker on.
- Run by: Pratham
- Person: P7, a teammate's roommate, not part of the team, who had tried an earlier version once
  before. Consent for the product log only; there were no recordings.
- Tasks: the three questions in `task_sheet.md`, given word for word and asked by voice. P7 did not
  add questions of his own.
- In the server log the session is labelled P7.

## Results

| Task | P7 |
|---|---|
| 1. Van Gogh: how many versions of The Bedroom | yes |
| 2. T. rex: how heavy it could get | yes |
| 3. T. rex: roar | yes |

- Heard right the first time: 3 of 3, and none edited. In Session 7, 6 of 12 spoken questions were
  misheard, but these three were short questions read from a sheet, so this is not a fair
  comparison.
- Speech to text took 0.8 to 1.1 s per question, and the server answered 0.5 to 0.6 s after the
  question was sent.
- Both factual answers were right and cited, every answer was spoken, and the roar played.
- Would use it in a museum: 3.5 to 4 out of 5.
- What P7 would change first: the look of the page, to make it more creative and interesting.

## What went wrong

- The link showed "Bad gateway" at first, because the server was still waiting for the model key to
  be added.
- The first tunnel dropped after about 17 minutes ("failed to accept QUIC stream" at 09:08 ET), so
  P7's first attempt never reached the server. We started a new tunnel with the laptop kept awake
  and over HTTP/2, and it held for the test.
- Visitors we don't know, probably crawlers, loaded the public page within minutes. None asked a
  question, but anyone with the link could, using up our model key's daily quota.

## What we change because of it

- The README now says to keep the laptop awake while the tunnel runs, how to do it on a Mac, and to
  try HTTP/2 if the link drops.
- The look of the page, P7's main request, goes to the team as a candidate for before demo day.
- This test was too small to measure much: one person and three questions we gave him. Session 12
  tests more people with their own questions (#70).
