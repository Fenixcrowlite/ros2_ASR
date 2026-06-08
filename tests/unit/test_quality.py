from asr_metrics.quality import EvaluationPolicy, cer, normalize_text, text_quality_support, wer


def test_wer_zero_on_exact_match() -> None:
    assert wer("hello world", "hello world") == 0.0


def test_wer_positive_on_mismatch() -> None:
    assert wer("hello world", "hello") > 0.0


def test_cer_zero_on_exact_match() -> None:
    assert cer("robot", "robot") == 0.0


def test_cer_positive_on_mismatch() -> None:
    assert cer("robot", "rbt") > 0.0


def test_quality_normalization_ignores_punctuation_and_case() -> None:
    assert normalize_text("Zero.") == "zero"
    assert wer("zero", "Zero.") == 0.0
    assert cer("one", "ONE!") == 0.0


def test_exact_match_requires_non_empty_normalized_reference() -> None:
    support = text_quality_support("!!!", "...")

    assert support.normalized_reference == ""
    assert support.normalized_hypothesis == ""
    assert support.reference_has_content is False
    assert support.hypothesis_has_content is False
    assert support.exact_match is False


def test_quality_policy_controls_whitespace_and_punctuation() -> None:
    policy = EvaluationPolicy(remove_punctuation=True, normalize_whitespace=True)

    assert normalize_text("  Hello,\tWORLD!  ", policy) == "hello world"
    assert wer("Hello, world!", "hello world") == 0.0
    assert cer("a b", "ab") == 0.0


def test_text_quality_support_exposes_raw_word_and_char_edit_counts() -> None:
    support = text_quality_support("alpha beta gamma", "alpha delta gamma zed")

    assert support.word_hits == 2
    assert support.word_substitutions == 1
    assert support.word_deletions == 0
    assert support.word_insertions == 1
    assert support.hits == support.word_hits
    assert support.substitutions == support.word_substitutions
    assert support.insertions == support.word_insertions
    assert support.word_edits == 2
    assert support.char_edits > 0


def test_ser_is_consistent_with_sample_accuracy() -> None:
    exact = text_quality_support("same text", "same text")
    mismatch = text_quality_support("same text", "different text")

    assert exact.sample_accuracy == 1.0
    assert exact.ser == 0.0
    assert mismatch.sample_accuracy == 0.0
    assert mismatch.ser == 1.0


def test_empty_reference_is_kept_and_hallucination_is_flagged() -> None:
    support = text_quality_support("", "unexpected speech")

    assert support.reference_word_count == 0
    assert support.hypothesis_has_content is True
    assert support.hallucination_on_silence == 1.0
    assert support.wer == 0.0


def test_wer_and_cer_can_exceed_one_for_insertions() -> None:
    support = text_quality_support("a", "a x x x x x")

    assert support.reference_word_count == 1
    assert support.reference_char_count == 1
    assert support.word_insertions == 5
    assert support.char_insertions == 5
    assert support.wer == 5.0
    assert support.cer == 5.0
