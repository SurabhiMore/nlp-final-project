# Test report

- Run: 2026-10-20 11:54 (UTC-04:00)
- Code tested: commit b68452f on branch feat/bm25-query-normalization, no uncommitted changes
- Command: python -m pytest --save-report
- Python 3.11.17 on Darwin
- Result: 108 passed, 1 not run in 2.4 s
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
| test_writes_json_and_markdown | test_compare_modes.py | passed | 0.00 |
| test_saved_answer_results_pair_cleanly | test_compare_modes.py | passed | 0.00 |
| test_interval_contains_the_observed_gap | test_compare_modes.py | passed | 0.00 |
| test_identical_modes_give_an_interval_centred_on_zero | test_compare_modes.py | passed | 0.00 |
| test_interval_allows_a_persona_win_even_with_none_observed | test_compare_modes.py | passed | 0.00 |
| test_interval_covers_the_true_gap_about_95_percent_of_the_time | test_compare_modes.py | passed | 0.05 |
| test_bad_results_files_give_clear_errors[missing-file] | test_compare_modes.py | passed | 0.00 |
| test_bad_results_files_give_clear_errors[not-json] | test_compare_modes.py | passed | 0.00 |
| test_bad_results_files_give_clear_errors[no-answers-key] | test_compare_modes.py | passed | 0.00 |
| test_bad_results_files_give_clear_errors[empty-answers] | test_compare_modes.py | passed | 0.00 |
| test_regressions_and_improvements_are_reported | test_compare_retrieval.py | passed | 0.00 |
| test_dropping_out_of_the_top_10_is_a_regression | test_compare_retrieval.py | passed | 0.00 |
| test_different_question_sets_are_refused | test_compare_retrieval.py | passed | 0.00 |
| test_question_file_passes_validation[t-rex] | test_datasets.py | passed | 0.16 |
| test_question_file_passes_validation[van-gogh] | test_datasets.py | passed | 0.45 |
| test_question_counts_and_id_conventions[van-gogh-vg-] | test_datasets.py | passed | 0.00 |
| test_question_counts_and_id_conventions[t-rex-tr-] | test_datasets.py | passed | 0.00 |
| test_question_ids_are_globally_unique | test_datasets.py | passed | 0.00 |
| test_answerable_questions_have_verified_supporting_chunks[t-rex] | test_datasets.py | passed | 0.16 |
| test_answerable_questions_have_verified_supporting_chunks[van-gogh] | test_datasets.py | passed | 0.45 |
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
| test_validation_detects_invalid_chunk_reference_in_check | test_datasets.py | passed | 0.02 |
| test_case_whitespace_and_punctuation_do_not_change_the_query[When did you live?] | test_retrieve.py | passed | 0.00 |
| test_case_whitespace_and_punctuation_do_not_change_the_query[WHEN DID YOU LIVE?] | test_retrieve.py | passed | 0.00 |
| test_case_whitespace_and_punctuation_do_not_change_the_query[  when   did you live  ] | test_retrieve.py | passed | 0.00 |
| test_case_whitespace_and_punctuation_do_not_change_the_query[When did you live?!?] | test_retrieve.py | passed | 0.00 |
| test_every_t_rex_spelling_becomes_the_same_terms[T. rex] | test_retrieve.py | passed | 0.00 |
| test_every_t_rex_spelling_becomes_the_same_terms[T-Rex] | test_retrieve.py | passed | 0.00 |
| test_every_t_rex_spelling_becomes_the_same_terms[t rex] | test_retrieve.py | passed | 0.00 |
| test_every_t_rex_spelling_becomes_the_same_terms[TRex] | test_retrieve.py | passed | 0.00 |
| test_every_t_rex_spelling_becomes_the_same_terms[trex] | test_retrieve.py | passed | 0.00 |
| test_every_t_rex_spelling_becomes_the_same_terms[T.Rex] | test_retrieve.py | passed | 0.00 |
| test_t_rex_rule_leaves_other_words_alone | test_retrieve.py | passed | 0.00 |
| test_possessive_leaves_no_stray_s[Who found Sue's skeleton?] | test_retrieve.py | passed | 0.00 |
| test_possessive_leaves_no_stray_s[Who found Sue\u2019s skeleton?] | test_retrieve.py | passed | 0.00 |
| test_curly_quotes_are_straightened | test_retrieve.py | passed | 0.00 |
| test_empty_and_stopword_only_questions | test_retrieve.py | passed | 0.01 |
| test_word_forms_meet[lived-live] | test_retrieve.py | passed | 0.00 |
| test_word_forms_meet[living-live] | test_retrieve.py | passed | 0.00 |
| test_word_forms_meet[named-name] | test_retrieve.py | passed | 0.00 |
| test_word_forms_meet[meaning-mean] | test_retrieve.py | passed | 0.00 |
| test_word_forms_meet[hunted-hunt] | test_retrieve.py | passed | 0.00 |
| test_word_forms_meet[paintings-painting] | test_retrieve.py | passed | 0.00 |
| test_word_forms_meet[stories-story] | test_retrieve.py | passed | 0.00 |
| test_short_or_special_words_are_not_mangled[tyrannosaurus] | test_retrieve.py | passed | 0.00 |
| test_short_or_special_words_are_not_mangled[class] | test_retrieve.py | passed | 0.00 |
| test_short_or_special_words_are_not_mangled[need] | test_retrieve.py | passed | 0.00 |
| test_short_or_special_words_are_not_mangled[king] | test_retrieve.py | passed | 0.00 |
| test_short_or_special_words_are_not_mangled[red] | test_retrieve.py | passed | 0.00 |
| test_short_or_special_words_are_not_mangled[bed] | test_retrieve.py | passed | 0.00 |
| test_return_structure_is_unchanged | test_retrieve.py | passed | 0.00 |
| test_question_is_not_modified | test_retrieve.py | passed | 0.00 |
| test_capitalization_variants_retrieve_the_same_passages | test_retrieve.py | passed | 0.00 |
| test_spelling_variants_retrieve_the_same_passages | test_retrieve.py | passed | 0.00 |
| test_word_form_fix_finds_the_name_meaning | test_retrieve.py | passed | 0.00 |
| test_ordinary_questions_still_work[t-rex-Who discovered the famous skeleton called Sue?-t-rex-wiki-0007] | test_retrieve.py | passed | 0.00 |
| test_ordinary_questions_still_work[van-gogh-In which town did you paint The Bedroom?-None] | test_retrieve.py | passed | 0.02 |
| test_terminology_variants_add_the_passage_word[How many fingers did you have?-digit] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[How many FINGERS did you have?-digit] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[Which horned dinosaurs did you eat?-ceratopsian] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[How strong was your bite?-forc] | test_retrieve.py | passed | 0.00 |
| test_ordinary_questions_are_not_expanded | test_retrieve.py | passed | 0.00 |
| test_map_only_applies_to_its_exhibit | test_retrieve.py | passed | 0.00 |
| test_every_mapped_word_is_in_the_t_rex_passages | test_retrieve.py | passed | 0.01 |
| test_terminology_map_finds_the_passage[How many fingers did you have on each hand?-t-rex-wiki-0000] | test_retrieve.py | passed | 0.00 |
| test_terminology_map_finds_the_passage[How strong was your bite?-t-rex-wiki-0001] | test_retrieve.py | passed | 0.00 |
| test_both_exhibits_load | test_smoke.py | passed | 0.00 |
| test_question_file_passes_the_check[t-rex] | test_smoke.py | passed | 0.16 |
| test_question_file_passes_the_check[van-gogh] | test_smoke.py | passed | 0.45 |
| test_search_returns_ranked_passages[t-rex] | test_smoke.py | passed | 0.00 |
| test_search_returns_ranked_passages[van-gogh] | test_smoke.py | passed | 0.00 |
| test_search_finds_the_passage_for_an_exact_wording_question | test_smoke.py | passed | 0.01 |
| test_health_reports_every_part_ready | test_smoke.py | passed | 0.00 |
| test_personas_lists_both_exhibits | test_smoke.py | passed | 0.00 |
| test_ask_by_text_returns_a_cited_answer | test_smoke.py | passed | 0.00 |
| test_ask_rejects_bad_requests[unknown-exhibit] | test_smoke.py | passed | 0.00 |
| test_ask_rejects_bad_requests[bad-mode] | test_smoke.py | passed | 0.00 |
| test_ask_rejects_bad_requests[empty-question] | test_smoke.py | passed | 0.00 |
| test_each_question_is_logged_without_audio | test_smoke.py | passed | 0.00 |
| test_roar_is_served_only_for_the_t_rex | test_smoke.py | passed | 0.01 |
| test_phone_page_is_served | test_smoke.py | passed | 0.00 |

Not run (left out by -m or -k):

- test_voice_round_trip (test_smoke.py)
