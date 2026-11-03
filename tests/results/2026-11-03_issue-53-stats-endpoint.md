# Test Report: issue-53 stats endpoint

- **Date:** 2026-11-03
- **Branch:** issue-53-stats-endpoint
- **Issue:** #53
- **Python:** 3.11

## Automated tests

### New tests (`pytest tests/test_server.py -k stats -v`)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.17, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/aditikaranjkar/Documents/GitHub/nlp-final-project
configfile: pytest.ini
plugins: anyio-4.15.1
collected 24 items / 21 deselected / 3 selected

tests/test_server.py ...                                                 [100%]

=============================== warnings summary ===============================
venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  /Users/aditikaranjkar/Documents/GitHub/nlp-final-project/venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================= 3 passed, 21 deselected, 1 warning in 0.41s ==================
```

| Test | Checks | Result |
|---|---|---|
| `test_stats_with_data` | top-level keys, total = 3, near-duplicates merged (count 2), p50 = 900 | PASS |
| `test_stats_empty_log` | empty file returns 200 and zero total | PASS |
| `test_stats_missing_log` | missing file returns 200 and p50/p95 = 0 | PASS |

### Full file (`pytest tests/test_server.py -v`, after `pip install -r requirements.txt`)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.17, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/aditikaranjkar/Documents/GitHub/nlp-final-project
configfile: pytest.ini
plugins: anyio-4.15.1
collected 24 items

tests/test_server.py ........................                            [100%]

=============================== warnings summary ===============================
venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  /Users/aditikaranjkar/Documents/GitHub/nlp-final-project/venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 24 passed, 1 warning in 0.73s =========================
```

All 24 tests in the file pass, including the three new `/stats` tests.

## Manual checks (real log, 3 entries)

| Check | Result |
|---|---|
| `GET /stats` returns all five keys | PASS |
| `/stats.html` renders four sections with matching data | PASS |
| `scripts/report_stats.py` output matches `/stats` | PASS |
| Footer link opens `/stats.html` | PASS |

### `scripts/report_stats.py` output

```
Total questions: 3

Per exhibit
  t-rex                answered=1  declined=0  not_in_sources=2

Top questions
    1  Hello, who are you?
    1  House.
    1  How strong was the T-Rex bite?

Corpus gaps (not_in_sources)
    1  Hello, who are you?
    1  House.

Latency: p50=801 ms  p95=1084 ms
```

### `GET /stats` output

```json
{"total_questions":3,"per_exhibit":{"t-rex":{"answered":1,"declined":0,"not_in_sources":2}},"top_questions":[{"question":"Hello, who are you?","count":1},{"question":"House.","count":1},{"question":"How strong was the T-Rex bite?","count":1}],"top_not_in_sources":[{"question":"Hello, who are you?","count":1},{"question":"House.","count":1}],"latency_ms":{"p50":801,"p95":1084}}
```
