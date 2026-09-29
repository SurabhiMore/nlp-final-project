# Evidence

Raw evidence from real users trying the running product. There is one folder per round of
testing, named after the session, for example `artifacts/evidence/session05/`.

Each folder holds:

- the task sheet we used
- one record per person (`P1.md`, `P2.md`, ...) filled in during the session
- the question-and-answer log from the product for that person (`P1_log.jsonl`, ...), exported
  with `scripts/export_session_log.py`
- screen recordings, if the person agreed to be recorded
- a `README.md` with the results, what went wrong, and what we changed because of it

Commit it the same week the test happens, while it's still fresh.

People are P1, P2, and so on. No names, faces, or contact details, ever. If a recording or a
log catches something personal, we cut that part or keep only the written record. Raw audio
gets deleted once we have the transcript.

See `artifacts/user_research_plan.md` for how the tests themselves are run.
