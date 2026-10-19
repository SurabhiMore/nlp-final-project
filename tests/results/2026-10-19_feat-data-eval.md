# Test report

- Run: 2026-10-19 14:48 (UTC-04:00)
- Code tested: commit f7ebfe6 on branch feat/data-eval, no uncommitted changes
- Command: python -m pytest -m "slow or not slow" --save-report
- Python 3.12.15 on Darwin
- Result: 38 passed in 26.9 s
- All tests that ran passed.

| Test | File | Result | Time (s) |
|---|---|---|---|
| test_question_file_passes_validation[t-rex] | test_datasets.py | passed | 0.36 |
| test_question_file_passes_validation[van-gogh] | test_datasets.py | passed | 0.97 |
| test_question_counts_and_id_conventions[van-gogh-vg-] | test_datasets.py | passed | 0.00 |
| test_question_counts_and_id_conventions[t-rex-tr-] | test_datasets.py | passed | 0.00 |
| test_question_ids_are_globally_unique | test_datasets.py | passed | 0.00 |
| test_answerable_questions_have_verified_supporting_chunks[t-rex] | test_datasets.py | passed | 0.20 |
| test_answerable_questions_have_verified_supporting_chunks[van-gogh] | test_datasets.py | passed | 0.58 |
| test_unanswerable_traps_have_empty_evidence_and_facts[t-rex] | test_datasets.py | passed | 0.00 |
| test_unanswerable_traps_have_empty_evidence_and_facts[van-gogh] | test_datasets.py | passed | 0.00 |
| test_validation_detects_duplicate_ids | test_datasets.py | passed | 0.00 |
| test_validation_detects_malformed_json_lines | test_datasets.py | passed | 0.00 |
| test_validation_detects_non_dict_record | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[id] | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[question] | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[type] | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[answerable] | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[gold_answer] | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[key_facts] | test_datasets.py | passed | 0.00 |
| test_validation_detects_missing_required_fields[evidence] | test_datasets.py | passed | 0.00 |
| test_validation_detects_type_and_answerable_mismatch | test_datasets.py | passed | 0.00 |
| test_validation_detects_persona_mismatch | test_datasets.py | passed | 0.00 |
| test_validation_detects_invalid_chunk_reference_in_check | test_datasets.py | passed | 0.05 |
| test_both_exhibits_load | test_smoke.py | passed | 0.00 |
| test_question_file_passes_the_check[t-rex] | test_smoke.py | passed | 0.25 |
| test_question_file_passes_the_check[van-gogh] | test_smoke.py | passed | 0.64 |
| test_search_returns_ranked_passages[t-rex] | test_smoke.py | passed | 0.01 |
| test_search_returns_ranked_passages[van-gogh] | test_smoke.py | passed | 0.03 |
| test_search_finds_the_passage_for_an_exact_wording_question | test_smoke.py | passed | 0.02 |
| test_health_reports_every_part_ready | test_smoke.py | passed | 0.00 |
| test_personas_lists_both_exhibits | test_smoke.py | passed | 0.00 |
| test_ask_by_text_returns_a_cited_answer | test_smoke.py | passed | 0.00 |
| test_ask_rejects_bad_requests[unknown-exhibit] | test_smoke.py | passed | 0.00 |
| test_ask_rejects_bad_requests[bad-mode] | test_smoke.py | passed | 0.00 |
| test_ask_rejects_bad_requests[empty-question] | test_smoke.py | passed | 0.00 |
| test_each_question_is_logged_without_audio | test_smoke.py | passed | 0.00 |
| test_roar_is_served_only_for_the_t_rex | test_smoke.py | passed | 0.02 |
| test_phone_page_is_served | test_smoke.py | passed | 0.00 |
| test_voice_round_trip | test_smoke.py | passed | 22.48 |
