# Session 12 user test: visitors on their own phones, with their own questions

Three people from outside the team, P8, P9 and P10, used the running product on their own phones
through a free Cloudflare tunnel, with both exhibits. Before seeing the app, each wrote down five
questions for each exhibit; those 30 questions are the test set for the final numbers (#82). This
finishes #70 together with P7 from Session 11. People are numbered on from session11 (P7).

## Setup

- Date: Monday November 23, 2026, 19:33 to 20:40 ET
- Where: each person's own phone, in the browser, on the https link from one Cloudflare tunnel to
  Kshiti's laptop. Each person had their own QR codes (`generate_qr.py --session P8`), so their
  questions are labelled in the log.
- Product version: commit ea3f496 (main at 5088752, with the museum look from #84, plus the
  Session 12 task sheet). Language model openai/gpt-oss-120b with low reasoning effort, speech to
  text Whisper small, the question classifier and the claim checker on.
- Run by: Kshiti
- People: three grad students at UMD, friends of a teammate, none part of the team. All three
  agreed to the product log; there were no recordings. All three agreed to their written
  questions being used for the evaluation.
- Tasks: the five in `task_sheet.md`. Each person first wrote their questions on the question
  sheet, then asked mostly from their own list.
- In the server log the sessions are labelled P8, P9 and P10.

## Results

| | P8 | P9 | P10 |
|---|---|---|---|
| Questions sent (all by voice) | 7 | 7 | 7 |
| Tasks completed, of those run | 7 of 7 | 6 of 8, 2 partly | 6 of 7, 1 not |
| Task 4, another language | not run | not run | not run |
| Transcripts edited before sending | 1 | 1 | 1 |
| Speech to text, median per question | 3.2 s | 3.2 s | 3.1 s |
| Answer after sending, median | 0.6 s | 0.7 s | 0.6 s |
| Would use it in a museum (1 to 5) | 5 | 4.9 | 4 |

- Tasks completed: 19 of the 22 that were run, plus 2 partly and 1 not completed. Nobody typed a
  question in another language, so task 4 was not run.
- Heard right: 19 of 21 questions were heard right the first time. "Can you roar?" came out as
  "Can you road?" (P10), and P9's first question had "And that's it." in front of it. Both were
  fixed in the transcript box before sending. P8 had nothing misheard and changed a word instead.
- Things the exhibit cannot know: all 5 such questions (a CEO in the news, the 2026 midterms,
  self-driving cars, how artists will fare from now on, how his work is read today) were declined,
  and nothing was made up.
- Answers: 13 questions were answered. 2 played the roar, 9 were backed by the passages they cite,
  1 was wrong and 1 was only half an answer. Of the 8 declines, 1 was not needed (below).
- Would use it in a museum: 5, 4.9 and 4, against 3.5 to 4 for P7 in Session 11.

## What went wrong

- **The QR link failed at first on every phone.** All three phones showed "This site can't be
  reached" on the first scan, while the same link loaded on the laptop. Scanning again fixed it.
  The tunnel's address is new each time, and a phone that looks it up too early seems to keep the
  failure for a while.
- **One wrong answer that the checks can't catch.** "What is your most famous painting?" (P10) got
  The Bedroom. The cited passage calls it "perhaps the most famous depiction of a bedroom in
  Western art history", and the model read that as his most famous painting. The answer cites a
  real passage that contains the words, so neither the reply check nor the claim checker flags it.
- **An unnecessary decline.** "What were the species of animals, birds, etc. that were alive
  during your time?" (P9) got "my sources don't list the other species". One of the passages it
  retrieved names Edmontosaurus, and another names Triceratops.
- **Half an answer.** "Why do you think your artwork was never valued when you were alive?" (P9)
  was answered from a letter about artists pooling their sales. It talks about a poor market but
  does not say why his own work was not valued.
- **Speech to text was slow:** about 3 s per question for everyone, against 0.8 to 1.1 s for P7 in
  Session 11 on the same model. This run was on a different laptop, which is the likely cause; we
  have not checked. Nobody complained about it, and the answer itself came in under a second.
- **The conversation disappears when switching exhibits** (P9).

What they said:

- P8 loved the roar and the voices, and found holding the button to speak fine. First change: show
  Van Gogh and the T. rex instead of the painting, and have them move while they talk.
- P9 liked switching between the characters. First change: a more artistic page ("painting looks
  unreal") and a more comfortable way to speak than holding the button. Also wanted Van Gogh to
  explain more from an artist's point of view, and the history kept after switching.
- P10 found it "very entertaining and user interactive" and "helpful to those who cannot read".
  First change: some answers were longer than the question needed.

## The three biggest problems

1. **The QR link did not open on the first scan, on all three phones.** In a museum, a visitor
   would likely give up there.
2. **A cited answer can still be wrong** (The Bedroom as his most famous painting), and our checks
   only test whether the cited passage is real and contains the details, not whether it answers
   the question.
3. **The page still feels static.** P8 wants the exhibit to move while it talks, P9 wants a more
   artistic page and the history kept when switching, even with the new look from #84.

## What we change because of it

- The task sheet now says to wait about a minute after starting a tunnel, and to scan again or
  turn airplane mode on and off if the page can't be reached. A permanent link would remove the
  problem, but we have no free hosting (section 4.6 of `artifacts/architecture.md`).
- The Bedroom answer, the species decline and the half answer go into the final report as
  failure modes. The 30 written questions include all three, so the final numbers (#82) measure
  them on questions nobody on the team wrote.
- Keeping the conversation per exhibit when switching, an animated exhibit while it speaks, and
  shorter answers go to the team as candidates for before demo day.

## Limitations

- Three people, all grad students and friends of a teammate, so they are not our real audience.
- Nobody tried another language, so typed questions in other languages were not tested this round.
- Speech to text times come from a different laptop than Session 11, so the two are not
  comparable.
- Most questions asked in the test came from the person's own written list, so the final test set
  overlaps with what they asked here. No answer was changed because of it.
- There were no recordings. The notes and the product log are the only record.

## Raw files

- `task_sheet.md`: the tasks, the moderator script and how each task is scored
- `question_sheet.md`: the sheet each person filled in before using the app
- `P8.md`, `P9.md`, `P10.md`: the record for each person, with their written questions
- `P8_log.jsonl`, `P9_log.jsonl`, `P10_log.jsonl`: their questions and answers from the product
  log, with what speech to text heard, whether it was edited, and timings
- `eval/questions/final/visitor_questions.jsonl`: the 30 written questions, word for word
