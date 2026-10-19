# Test report

- Run: 2026-10-19 14:26 (UTC-04:00)
- Code tested: commit 3554797 on branch eval/compare-modes, no uncommitted changes
- Command: python -m pytest -m "slow or not slow" --save-report
- Python 3.11.9 on Windows
- Result: 40 passed in 30.7 s
- All tests that ran passed.

| Test | File | Result | Time (s) |
|---|---|---|---|
| test_counts_the_four_outcomes | test_compare_modes.py | passed | 0.00 |
| test_pairs_by_question_id_not_row_order | test_compare_modes.py | passed | 0.00 |
| test_same_question_id_in_two_exhibits_stays_separate | test_compare_modes.py | passed | 0.00 |
| test_exact_mcnemar_p_values[0-0-1.0] | test_compare_modes.py | passed | 0.00 |
| test_exact_mcnemar_p_values[1-2-1.0] | test_compare_modes.py | passed | 0.00 |
| test_exact_mcnemar_p_values[0-6-0.03125] | test_compare_modes.py | passed | 0.00 |
| test_exact_mcnemar_p_values[2-8-0.109375] | test_compare_modes.py | passed | 0.00 |
| test_exact_mcnemar_p_values[5-5-1.0] | test_compare_modes.py | passed | 0.00 |
| test_no_discordant_pairs_does_not_crash | test_compare_modes.py | passed | 0.00 |
| test_small_sample_is_called_too_small | test_compare_modes.py | passed | 0.00 |
| test_clear_win_is_reported_with_its_p_value | test_compare_modes.py | passed | 0.00 |
| test_duplicate_result_is_rejected | test_compare_modes.py | passed | 0.00 |
| test_missing_mode_is_rejected | test_compare_modes.py | passed | 0.00 |
| test_failed_call_is_rejected | test_compare_modes.py | passed | 0.00 |
| test_writes_json_and_markdown | test_compare_modes.py | passed | 0.07 |
| test_saved_answer_results_pair_cleanly | test_compare_modes.py | passed | 0.00 |
| test_interval_contains_the_observed_gap | test_compare_modes.py | passed | 0.00 |
| test_identical_modes_give_an_interval_centred_on_zero | test_compare_modes.py | passed | 0.00 |
| test_interval_allows_a_persona_win_even_with_none_observed | test_compare_modes.py | passed | 0.00 |
| test_interval_covers_the_true_gap_about_95_percent_of_the_time | test_compare_modes.py | passed | 0.22 |
| test_bad_results_files_give_clear_errors[missing-file] | test_compare_modes.py | passed | 0.00 |
| test_bad_results_files_give_clear_errors[not-json] | test_compare_modes.py | passed | 0.01 |
| test_bad_results_files_give_clear_errors[no-answers-key] | test_compare_modes.py | passed | 0.01 |
| test_bad_results_files_give_clear_errors[empty-answers] | test_compare_modes.py | passed | 0.03 |
| test_both_exhibits_load | test_smoke.py | passed | 0.00 |
| test_question_file_passes_the_check[t-rex] | test_smoke.py | passed | 0.37 |
| test_question_file_passes_the_check[van-gogh] | test_smoke.py | passed | 1.22 |
| test_search_returns_ranked_passages[t-rex] | test_smoke.py | passed | 0.03 |
| test_search_returns_ranked_passages[van-gogh] | test_smoke.py | passed | 0.06 |
| test_search_finds_the_passage_for_an_exact_wording_question | test_smoke.py | passed | 0.03 |
| test_health_reports_every_part_ready | test_smoke.py | passed | 0.04 |
| test_personas_lists_both_exhibits | test_smoke.py | passed | 0.01 |
| test_ask_by_text_returns_a_cited_answer | test_smoke.py | passed | 0.02 |
| test_ask_rejects_bad_requests[unknown-exhibit] | test_smoke.py | passed | 0.01 |
| test_ask_rejects_bad_requests[bad-mode] | test_smoke.py | passed | 0.01 |
| test_ask_rejects_bad_requests[empty-question] | test_smoke.py | passed | 0.01 |
| test_each_question_is_logged_without_audio | test_smoke.py | passed | 0.04 |
| test_roar_is_served_only_for_the_t_rex | test_smoke.py | passed | 0.18 |
| test_phone_page_is_served | test_smoke.py | passed | 0.02 |
| test_voice_round_trip | test_smoke.py | passed | 26.90 |
