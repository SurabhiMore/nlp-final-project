# Test report

- Run: 2026-10-18 23:28 (UTC-04:00)
- Code tested: commit be16231 on branch test/pytest-setup, no uncommitted changes
- Command: python -m pytest -m "slow or not slow" --save-report
- Python 3.11.9 on Windows
- Result: 16 passed in 246.8 s
- All tests that ran passed.

| Test | File | Result | Time (s) |
|---|---|---|---|
| test_both_exhibits_load | test_smoke.py | passed | 0.00 |
| test_question_file_passes_the_check[t-rex] | test_smoke.py | passed | 0.38 |
| test_question_file_passes_the_check[van-gogh] | test_smoke.py | passed | 0.95 |
| test_search_returns_ranked_passages[t-rex] | test_smoke.py | passed | 0.02 |
| test_search_returns_ranked_passages[van-gogh] | test_smoke.py | passed | 0.05 |
| test_search_finds_the_passage_for_an_exact_wording_question | test_smoke.py | passed | 0.02 |
| test_health_reports_every_part_ready | test_smoke.py | passed | 0.02 |
| test_personas_lists_both_exhibits | test_smoke.py | passed | 0.01 |
| test_ask_by_text_returns_a_cited_answer | test_smoke.py | passed | 0.01 |
| test_ask_rejects_bad_requests[unknown-exhibit] | test_smoke.py | passed | 0.01 |
| test_ask_rejects_bad_requests[bad-mode] | test_smoke.py | passed | 0.01 |
| test_ask_rejects_bad_requests[empty-question] | test_smoke.py | passed | 0.02 |
| test_each_question_is_logged_without_audio | test_smoke.py | passed | 0.07 |
| test_roar_is_served_only_for_the_t_rex | test_smoke.py | passed | 0.14 |
| test_phone_page_is_served | test_smoke.py | passed | 0.01 |
| test_voice_round_trip | test_smoke.py | passed | 243.63 |
