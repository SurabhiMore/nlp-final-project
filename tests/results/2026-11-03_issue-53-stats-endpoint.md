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
================= 3 passed, 21 deselected, 1 warning in 0.38s ==================
```

| Test | Checks | Result |
|---|---|---|
| `test_stats_with_data` | top-level keys, total = 3, near-duplicates merged (count 2), p50 = 900 | PASS |
| `test_stats_empty_log` | empty file returns 200 and zero total | PASS |
| `test_stats_missing_log` | missing file returns 200 and p50/p95 = 0 | PASS |

### Full file (`pytest tests/test_server.py -v`)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.17, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/aditikaranjkar/Documents/GitHub/nlp-final-project
configfile: pytest.ini
plugins: anyio-4.15.1
collected 24 items

tests/test_server.py ............F...........                            [100%]

=================================== FAILURES ===================================
________________ test_ask_detected_language_in_response_and_log ________________

client = <starlette.testclient.TestClient object at 0x10d7995d0>
tmp_path = PosixPath('/private/var/folders/28/bxl21glx1wjfwfj24j_gjsgc0000gn/T/pytest-of-aditikaranjkar/pytest-13/test_ask_detected_language_in_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10d799490>

    def test_ask_detected_language_in_response_and_log(client, tmp_path, monkeypatch):
        """Response and qa_log.jsonl must contain detected_language, search_query, and passages."""
        import json
        from app import server
    
        log_file = tmp_path / "qa_log.jsonl"
        monkeypatch.setattr(server, "LOG_PATH", log_file)
        response = client.post("/ask", data={"persona": EXHIBIT, "text": "¿Cuándo y dónde naciste?"})
        assert response.status_code == 200
        body = response.json()
>       assert body.get("detected_language") == "es"
E       AssertionError: assert 'en' == 'es'
E         
E         - es
E         + en

tests/test_server.py:139: AssertionError
=============================== warnings summary ===============================
venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  /Users/aditikaranjkar/Documents/GitHub/nlp-final-project/venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_server.py::test_ask_detected_language_in_response_and_log
=================== 1 failed, 23 passed, 1 warning in 0.45s ====================
```

**Known unrelated failure:** `test_ask_detected_language_in_response_and_log` (`'en' == 'es'`).
It fails identically on the branch point with these changes stashed, so it is not caused by this PR.

## Manual checks (real log, 3 entries)

| Check | Result |
|---|---|
| `GET /stats` returns all five keys | PASS |
| `/stats.html` renders four sections with matching data | PASS |
| `scripts/report_stats.py` output matches `/stats` | PASS |
| Footer link opens `/stats.html` | TODO: fill in after clicking |

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
