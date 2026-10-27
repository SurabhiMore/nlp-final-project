# Test report

- Run: 2026-10-27 00:34 (UTC-04:00)
- Code tested: commit 825afa4 on branch feat/timecheck-wikidata, no uncommitted changes
- Command: python -m pytest --save-report
- Python 3.11.17 on Darwin
- Result: 1 error, 1 not run in 0.3 s
- 1 test(s) failed or could not run.

| Test | File | Result | Time (s) |
|---|---|---|---|
| (file could not be loaded) | test_quotes.py | error | 0.00 |

Why they failed:

- (file could not be loaded) (test_quotes.py): ModuleNotFoundError: No module named 'rapidfuzz'

Not run (left out by -m or -k):

- test_voice_round_trip (test_smoke.py)
