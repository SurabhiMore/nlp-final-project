# Tests

Run them from the repo root:

```bash
python -m pytest            # the fast tests, about half a minute
python -m pytest -m slow    # also the ones that load Whisper and Kokoro
```

## Saving a report for your PR

Before you open a pull request, commit your code, then run every test and save a report:

```bash
python -m pytest -m "slow or not slow" --save-report
```

This writes `tests/results/<date>_<branch>.md`: every test, whether it passed, how long it
took, and the commit that was tested. Commit that file too and link it in the PR description.
Reports are named by date and branch, so pull requests never edit the same file, and the
folder keeps a record of every run for later sessions.

## Rules

- No test calls a real language model. `conftest.py` sets `LLM_PROVIDER=offline` for every
  test, so nothing uses up a Groq limit. To test how replies from a model are handled, pass a
  made-up reply string to the function that parses it.
- No network. Tests use the passages and question files already in the repo.
- Anything that loads the speech models gets `@pytest.mark.slow`.
- Use the `client` fixture for the server. It writes the request log to a temporary folder,
  so tests never add lines to `logs/qa_log.jsonl`.

## Where your tests go

One file per area, so pull requests don't edit the same file:

| File | Area |
|---|---|
| `test_smoke.py` | What already works end to end. Shared: only change it when behaviour changes on purpose |
| `test_datasets.py` | Question files and their validation |
| `test_retrieval.py` | Search and query normalization |
| `test_answers.py` | Answer generation, citations and reply parsing |
| `test_compare_modes.py` | Persona vs plain guide statistics |
| `test_quotes.py` | Quote checker and its evaluation |
| `test_stt.py` | Speech to text prompts and confidence flag, `/transcribe`, and its evaluation |
| `test_server.py` | Server endpoints beyond the smoke tests |

Name tests after the behaviour they check, for example
`test_citation_not_in_passages_is_dropped`, so a failure says what broke.
