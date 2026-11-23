# Demo day script

Echoes.ai, for demo day (December 1 or 8, whichever slot we get). First version by Pratham,
November 16 (#74). 12 minutes of talk and live demo, then 3 minutes of questions. Who presents
which part follows our hats, so swap parts if it suits someone better.

## Running order

| Time | Part | Who | What it covers |
|---|---|---|---|
| 0:00 to 1:30 | The problem | Pratham | People give a plaque a few seconds, and an audio guide can't answer a question. Our idea: talk to the exhibit, and every answer comes from a real source we can show |
| 1:30 to 3:00 | How it works | Saurabh | One diagram: phone page, Whisper, search, gpt-oss-120b speaking as the exhibit with citations, the checks, Kokoro. The same code runs a person and a dinosaur; only `persona.json` and the sources change |
| 3:00 to 7:00 | Live demo | Saurabh on the laptop, Kshiti asks on the phone, Aditi shows the curator page | The questions below |
| 7:00 to 9:00 | Does it work? | Surabhi | The north star across sessions, the final number on the questions visitors wrote, persona against the plain guide, and the misses |
| 9:00 to 10:30 | What visitors did | Kshiti | The user tests in Sessions 5, 7, 8 and 11: what people asked, what went wrong, and what we changed (the transcript box, after people were misheard) |
| 10:30 to 12:00 | Limits and ethics | Aditi | What did not work, no audio kept, it says it is an AI, free tier limits, no permanent link, and what we would do next |
| 12:00 to 15:00 | Questions | Everyone | |

## Live questions

Asked in this order, on a phone through the tunnel. The last column says where each answer was
checked. All but two were answered this way on `openai/gpt-oss-120b` in a Session 10 run, on the
code that is on main now. The Hindi question was last checked in Session 9, and the roar was never
in a saved run. Ask them all again on the demo laptop after the Session 12 code freeze.

| # | Exhibit | Ask | What should happen | What it shows | Checked in |
|---|---|---|---|---|---|
| 1 | Van Gogh | "What is considered your first major work?" (voice) | "My first major work is The Potato Eaters", with a source card | Answers in character, from a cited source | vg-05, `eval/results/answers_results.json` |
| 2 | Van Gogh | "How many versions of The Bedroom did you paint?" (voice) | "I painted three versions of The Bedroom" | Specific facts | vg-12, same file |
| 3 | Van Gogh | "What did you think of Picasso's painting Guernica?" (voice) | Declines: it came after his time | The time boundary | vg-16, same file |
| 4 | Van Gogh | "What was the name of your childhood dog?" (voice) | "I have no record of a childhood dog" | It says when the sources don't know, instead of making something up. A visitor asked this in Session 7 | vg-20, same file, and `artifacts/evidence/session07/P2_log.jsonl` |
| 5 | Van Gogh | "Are you a real person?" (voice) | "I am an AI guide speaking as Vincent van Gogh, not the historical man himself" | Honesty | vg-adv-ib-03 (asked there with more words), `eval/results/robustness_results.md` |
| 6 | Van Gogh | "आपका जन्म कब और कहाँ हुआ था?" ("When and where were you born?", typed) | The answer comes back in Hindi | Other languages | vg-multi-04, Session 9 run (`eval/results/multilingual_replies.json` at commit 14412b8) |
| 7 | T. rex | "Can you roar for me?" (voice) | A short line, then the roar | The exhibit's own sound | Not in a saved run: check in rehearsal |
| 8 | T. rex | "Did you have scales or feathers?" (voice) | "Scientists think I mostly wore scales..." | It says when scientists are unsure | tr-13, `eval/results/answers_results.json` |
| 9 | T. rex | "What is the capital of France?" (voice) | Declines at once, with no call to the model | The classifier | tr-21, same file (0 ms model time) |
| 10 | Curator page | Open "Curator stats" in the footer | Questions by topic, including the ones we just asked | What a museum gets | #61 |

If the demo runs long, drop 2 and 8. Since #71, the answer to question 6 is spoken in a Hindi
voice. Ask question 6 by voice only if a Hindi speaker has tried it in rehearsal; we could not test
a spoken Hindi question on our check below.

## Check on main, November 23

All nine questions, asked in order on main at e7ea205 with `openai/gpt-oss-120b`, the way the page
asks them: speech to text, then `/ask`, then `/speak` for each sentence. The spoken questions came
from the Mac's `say` voice (Samantha), on localhost with no tunnel, so this times the machine, not
the talking.

| # | Heard right | What happened | Answer on screen | First word spoken | Answer spoken for |
|---|---|---|---|---|---|
| 1 | yes | The Potato Eaters, cited | 3.2 s | 3.6 s | 4.0 s |
| 2 | yes | three versions, cited | 2.7 s | 3.1 s | 3.4 s |
| 3 | yes | declined, after his time | 3.0 s | 3.3 s | 5.2 s |
| 4 | yes | no record of a childhood dog | 15.0 s | 15.5 s | 4.4 s |
| 5 | yes | "I am an AI guide speaking as Vincent van Gogh." | 18.9 s | 19.3 s | 4.3 s |
| 6 | typed | answered in Hindi, cited, spoken in Hindi | 1.2 s | 3.2 s | 8.7 s |
| 7 | yes | a short line, then the roar | 5.1 s | 5.5 s | 3.7 s, plus the roar |
| 8 | yes | scales, with feathers possible, 2 sources | 19.9 s | 20.4 s | 13.8 s |
| 9 | yes | declined at once by the classifier | 2.2 s | 2.5 s | 7.3 s |

The curator page then showed the questions grouped by topic.

- Questions 4, 5 and 8 waited 13 to 17 s for the model, because we asked them back to back. Asked
  25 s apart, the same model answered in 0.5 to 1.8 s, so this was most likely the free tier's
  per-minute limit. In the demo, the talking between questions gives that gap.
- With normal answer times, waiting for and listening to all nine answers takes about 90 s. With
  the asking and switching exhibits, the live demo needs about 2.5 of its 4 minutes, which leaves
  about 1.5 minutes for talking.
- The first Hindi answer on a laptop downloads the Hindi voice. Here that took about 15 minutes
  the first time, and under 2 s after that.

## On the day

- Run it on the presenting laptop with `.env` set to `openai/gpt-oss-120b` and
  `LLM_REASONING_EFFORT=low`, the model we report numbers for, and keep the second key ready.
  The free tier gives about 200K tokens a day and a question uses about 2,800, so a rehearsal and
  the demo fit easily, but don't run an evaluation that day.
- Set `PRELOAD_MODELS=1`, so Whisper and Kokoro are loaded before we start.
- Start the tunnel, make the QR codes (`python scripts/generate_qr.py --url <tunnel link>`), and
  open the page on the phone once to allow the microphone. On an iPhone, turn the silent switch
  off.
- Before we go on, ask question 1 and question 6 once. Question 6 makes the laptop download the
  Hindi voice, which can take minutes the first time.
- Leave about 20 seconds between questions, so the free tier's per-minute limit does not slow the
  answers down.

## If something fails

- Record the whole demo (the phone screen with sound) after the Session 12 code freeze, and keep
  it on the laptop and as `reports/final/demo.mp4`. If the live demo fails (Wi-Fi, the tunnel, or
  the rate limit), switch to the recording at the same question and keep talking.
- If only the tunnel fails, use the laptop browser at http://localhost:8000 with the laptop
  microphone. Browsers allow the microphone on localhost.
- If the model is rate limited, switch to the second key, then to the recording.

## Timing

A run-through by Pratham alone on November 23: every part read out loud at presenting speed, and
the live demo done for real in the browser on localhost with real model answers. All nine questions
were heard right and answered as the script expects. A rehearsal with everyone talking is still
worth doing before December 1.

| Part | Planned | Real |
|---|---|---|
| The problem | 1:30 | 1:28 |
| How it works | 1:30 | 1:13 |
| Live demo | 4:00 | 7:04 |
| Does it work? | 2:00 | 1:21 |
| What visitors did | 1:30 | 1:06 |
| Limits and ethics | 1:30 | 1:11 |
| Total | 12:00 | 13:23 |

The live demo ran 3 minutes over. Each question took about 45 seconds, mostly waiting for the whole
answer to be spoken, while the talking parts came in 1:41 under. Dropping questions 2 and 8 saves
about 1:35, which would have made it about 11:50. "Does it work?" still needs about 15 seconds for
the final numbers, so that brings it to about 12:00.
