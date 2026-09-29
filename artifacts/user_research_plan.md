# User research plan

**Author:** Kshiti Deshpande
**Date:** September 29, 2026
**Status:** v2. Updated for two test exhibits and the first round of tests on the running product.

## Who our users are

Adults visiting a museum or gallery, especially the ones who usually walk past the plaques. And
the curators and education staff who would set the guide up and need to trust it.

## What we want to find out

- Will people actually talk out loud to an exhibit, or will it feel awkward?
- What do they ask about? Facts, stories, the exhibit's opinions, or things we haven't thought of?
- Do they trust what it says, and do they notice when an answer is wrong?
- Is the reply fast enough to feel like a conversation?
- Does it work as well for a creature with no words of its own (T. rex) as for a person who left
  letters (Van Gogh)?

## Who we'll test with

Two rounds, matched to how far the prototype has come.

**Pilot round (Sessions 6):** three to five people recruited by convenience, such as
classmates or friends outside our team, 18 or older. They use the running product, so this
counts as user evidence, but they aren't our real audience, so we treat what we learn as a way
to find and fix the obvious problems. Five users is enough to surface most usability problems
(Nielsen's rule of thumb is that five users find roughly 85% of them). Our own team trying it
doesn't count.

**Field round (once the pilot problems are fixed):** actual visitors at a campus gallery, or a
partner museum if we can arrange access. Recruited on site, and screened for one thing: whether
they're the kind of visitor who normally walks past the plaques rather than stopping to read
them, since that's the behaviour the product is meant to change. Sessions are capped at 10 to 15
minutes so we're not eating into someone's visit.

The pilot gives us cheap, fast iteration. The field round is what actually tells us whether the
product works for the audience it's built for.

## The first test (Session 6)

Each person gets a short sheet with six tasks across both exhibits and uses the running
prototype while we watch. The full sheet is in `artifacts/evidence/session05/task_sheet.md`.

1. Find out what feeling Van Gogh wanted his painting The Bedroom to give. (Did they get an
   answer, and did it name a source?)
2. Ask Van Gogh about something from after 1890. (Does he handle it without making something
   up?)
3. Get Van Gogh to tell you something he wrote in his letters. (Does it come from his letters?)
4. Find out how heavy a T. rex could get. (Did they get a number with a source?)
5. Ask the T. rex whether it ever met a human. (Does it say no, and stay in character?)
6. Ask either exhibit anything you like for two minutes. (What do people ask when nobody tells
   them what to ask?)

For each task we note whether they finished it, how long it took, how many questions they
asked, whether they caught a wrong answer, and how natural it felt on a 1 to 5 scale.

## How we run it

- The product runs on one of our laptops (`uvicorn app.server:app`).
- The easiest setup is the person using the laptop itself at `http://localhost:8000`.
- To use their own phone, the page needs an https link, because browsers only allow the
  microphone on secure pages. We open one with a free tunnel such as
  `cloudflared tunnel --url http://localhost:8000` and share the link it prints.
- Each person gets their own link ending in `&session=P1`, `&session=P2` and so on, so their
  questions are labelled in the product's log and we can export exactly their part.

## What we record

With the person's permission: a screen recording (with audio if they agree), the question and
answer log from the product, and the filled-in record for each task. It all goes into
`artifacts/evidence/session06/` in the same week as the test.

## Consent and privacy

Before we start recording we say something like: "This is a class project. Is it okay if we
record your screen and voice while you try it? We won't use your name, and you can stop
whenever you want."

We call people P1, P2 and so on, and we never commit names, faces or contact details. If a
recording or a log shows something personal, we cut that part or keep only the written record.
Raw audio gets deleted once we have the transcript. The product itself never saves the audio;
only the transcribed question goes into the log.

## Changes

- v1, September 22: first version.
- v2, September 29: tasks cover both test exhibits (Van Gogh and T. rex); added how the test is run and how logs are labelled.
