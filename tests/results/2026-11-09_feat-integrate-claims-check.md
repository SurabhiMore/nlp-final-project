# Test report

- Run: 2026-11-09 21:46 (UTC-05:00)
- Code tested: commit 2862b62 on branch feat/integrate-claims-check, with uncommitted changes
- Command: python -m pytest tests/test_server.py -k claims -v --save-report
- Python 3.11.14 on Darwin
- Result: 3 passed, 24 not run in 0.3 s
- All tests that ran passed.

| Test | File | Result | Time (s) |
|---|---|---|---|
| test_ask_response_has_unbacked_claims_key | test_server.py | passed | 0.03 |
| test_enable_claims_0_skips_check_and_returns_empty_list | test_server.py | passed | 0.00 |
| test_unbacked_claims_written_to_log | test_server.py | passed | 0.00 |

Not run (left out by -m or -k):

- test_ask_response_has_all_frontend_fields (test_server.py)
- test_ask_status_is_a_known_value (test_server.py)
- test_ask_citations_have_required_fields (test_server.py)
- test_citation_url_is_empty_string_or_valid_https (test_server.py)
- test_citation_snippet_is_string (test_server.py)
- test_updated_static_files_are_served (test_server.py)
- test_style_css_contains_state_tokens (test_server.py)
- test_main_js_references_data_state_attribute (test_server.py)
- test_main_js_has_loading_indicator_markup (test_server.py)
- test_ask_unknown_exhibit_returns_404 (test_server.py)
- test_ask_empty_question_returns_400 (test_server.py)
- test_ask_bad_mode_returns_400 (test_server.py)
- test_ask_detected_language_in_response_and_log (test_server.py)
- test_ask_skips_search_and_the_model_on_an_off_topic_question (test_server.py)
- test_ask_gives_a_blocked_question_the_normal_response (test_server.py)
- test_ask_gives_a_later_year_the_outside_time_line (test_server.py)
- test_ask_uses_the_plain_guide_line_in_neutral_mode (test_server.py)
- test_a_blocked_question_is_logged_as_the_classifier (test_server.py)
- test_ask_still_runs_the_pipeline_on_a_real_question (test_server.py)
- test_enable_classifier_0_restores_the_old_behaviour (test_server.py)
- test_ask_searches_with_translated_query_not_raw_non_english (test_server.py)
- test_stats_with_data (test_server.py)
- test_stats_empty_log (test_server.py)
- test_stats_missing_log (test_server.py)
