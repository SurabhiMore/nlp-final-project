# Test report

- Run: 2026-10-26 14:04 (UTC-04:00)
- Code tested: commit 9f0bd31 on branch feat/hybrid-search-and-install-fixes, with uncommitted changes
- Command: python -m pytest -v --save-report
- Python 3.11.14 on Darwin
- Result: 169 passed, 1 not run in 2.5 s
- All tests that ran passed.

| Test | File | Result | Time (s) |
|---|---|---|---|
| test_supported_answer_keeps_its_citation | test_answers.py | passed | 0.00 |
| test_honest_not_in_sources_is_kept_as_written | test_answers.py | passed | 0.00 |
| test_decline_that_answers_from_model_knowledge_is_replaced[rex-means-king] | test_answers.py | passed | 0.00 |
| test_decline_that_answers_from_model_knowledge_is_replaced[theo-art-dealer] | test_answers.py | passed | 0.00 |
| test_answer_with_no_citation_becomes_not_in_sources | test_answers.py | passed | 0.00 |
| test_off_topic_decline_is_kept_as_written | test_answers.py | passed | 0.00 |
| test_off_topic_decline_that_does_not_say_no_gets_a_clear_line | test_answers.py | passed | 0.00 |
| test_off_topic_answer_from_model_knowledge_is_not_shown | test_answers.py | passed | 0.00 |
| test_invalid_citation_is_removed_and_valid_one_kept | test_answers.py | passed | 0.00 |
| test_citing_a_real_passage_that_was_not_supplied_is_rejected | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[not-json] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[cut-off] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[empty-object] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[null-answer] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[answer-is-object] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[citations-is-number] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[citations-is-object] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[status-is-number] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[top-level-list] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[sound-is-number] | test_answers.py | passed | 0.00 |
| test_malformed_reply_never_crashes_and_never_shows_raw_output[whitespace] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[not-json] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[cut-off] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[empty-object] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[null-answer] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[answer-is-object] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[citations-is-number] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[citations-is-object] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[status-is-number] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[top-level-list] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[sound-is-number] | test_answers.py | passed | 0.00 |
| test_parse_reply_never_raises[whitespace] | test_answers.py | passed | 0.00 |
| test_json_wrapped_in_extra_text_is_still_read | test_answers.py | passed | 0.00 |
| test_introduction_without_citation_is_still_answered[Hello!] | test_answers.py | passed | 0.00 |
| test_introduction_without_citation_is_still_answered[Who are you?] | test_answers.py | passed | 0.00 |
| test_introduction_without_citation_is_still_answered[Are you real?] | test_answers.py | passed | 0.00 |
| test_roar_request_without_citation_keeps_the_sound | test_answers.py | passed | 0.00 |
| test_ask_returns_the_same_fields_when_the_model_reply_is_broken | test_answers.py | passed | 0.03 |
| test_frozen_passages_cover_both_exhibits | test_answers.py | passed | 0.00 |
| test_evaluation_scores_the_same_reply_before_and_after | test_answers.py | passed | 0.00 |
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
| test_question_file_passes_validation[t-rex] | test_datasets.py | passed | 0.18 |
| test_question_file_passes_validation[van-gogh] | test_datasets.py | passed | 0.47 |
| test_question_counts_and_id_conventions[van-gogh-vg-] | test_datasets.py | passed | 0.00 |
| test_question_counts_and_id_conventions[t-rex-tr-] | test_datasets.py | passed | 0.00 |
| test_question_ids_are_globally_unique | test_datasets.py | passed | 0.00 |
| test_answerable_questions_have_verified_supporting_chunks[t-rex] | test_datasets.py | passed | 0.18 |
| test_answerable_questions_have_verified_supporting_chunks[van-gogh] | test_datasets.py | passed | 0.47 |
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
| test_ordinary_questions_still_work[van-gogh-In which town did you paint The Bedroom?-None] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[How many fingers did you have?-digit] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[How many FINGERS did you have?-digit] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[Which horned dinosaurs did you eat?-ceratopsian] | test_retrieve.py | passed | 0.00 |
| test_terminology_variants_add_the_passage_word[How strong was your bite?-forc] | test_retrieve.py | passed | 0.00 |
| test_ordinary_questions_are_not_expanded | test_retrieve.py | passed | 0.00 |
| test_map_only_applies_to_its_exhibit | test_retrieve.py | passed | 0.00 |
| test_every_mapped_word_is_in_the_t_rex_passages | test_retrieve.py | passed | 0.01 |
| test_terminology_map_finds_the_passage[How many fingers did you have on each hand?-t-rex-wiki-0000] | test_retrieve.py | passed | 0.00 |
| test_terminology_map_finds_the_passage[How strong was your bite?-t-rex-wiki-0001] | test_retrieve.py | passed | 0.00 |
| test_rrf_combines_and_ranks_candidates | test_retrieve.py | passed | 0.00 |
| test_rrf_empty_rankings | test_retrieve.py | passed | 0.00 |
| test_search_mode_defaults_to_bm25 | test_retrieve.py | passed | 0.00 |
| test_search_mode_reads_env_var[bm25] | test_retrieve.py | passed | 0.00 |
| test_search_mode_reads_env_var[dense] | test_retrieve.py | passed | 0.00 |
| test_search_mode_reads_env_var[hybrid] | test_retrieve.py | passed | 0.00 |
| test_search_mode_falls_back_on_invalid_value | test_retrieve.py | passed | 0.00 |
| test_embedding_cache_rebuild_and_reload | test_retrieve.py | passed | 0.01 |
| test_retrieve_all_modes_return_compatible_structure | test_retrieve.py | passed | 0.00 |
| test_ask_response_has_all_frontend_fields | test_server.py | passed | 0.00 |
| test_ask_status_is_a_known_value | test_server.py | passed | 0.00 |
| test_ask_citations_have_required_fields | test_server.py | passed | 0.00 |
| test_citation_url_is_empty_string_or_valid_https | test_server.py | passed | 0.00 |
| test_citation_snippet_is_string | test_server.py | passed | 0.00 |
| test_updated_static_files_are_served | test_server.py | passed | 0.01 |
| test_style_css_contains_state_tokens | test_server.py | passed | 0.00 |
| test_main_js_references_data_state_attribute | test_server.py | passed | 0.00 |
| test_main_js_has_loading_indicator_markup | test_server.py | passed | 0.00 |
| test_ask_unknown_exhibit_returns_404 | test_server.py | passed | 0.00 |
| test_ask_empty_question_returns_400 | test_server.py | passed | 0.00 |
| test_ask_bad_mode_returns_400 | test_server.py | passed | 0.00 |
| test_both_exhibits_load | test_smoke.py | passed | 0.00 |
| test_question_file_passes_the_check[t-rex] | test_smoke.py | passed | 0.21 |
| test_question_file_passes_the_check[van-gogh] | test_smoke.py | passed | 0.47 |
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
| test_roar_is_served_only_for_the_t_rex | test_smoke.py | passed | 0.00 |
| test_phone_page_is_served | test_smoke.py | passed | 0.00 |

Not run (left out by -m or -k):

- test_voice_round_trip (test_smoke.py)
