from asr_metrics.quality import cer, wer


def test_wer_zero_on_exact_match() -> None:
    assert wer("hello world", "hello world") == 0.0


def test_wer_positive_on_mismatch() -> None:
    assert wer("hello world", "hello") > 0.0


def test_cer_zero_on_exact_match() -> None:
    assert cer("robot", "robot") == 0.0


def test_cer_positive_on_mismatch() -> None:
    assert cer("robot", "rbt") > 0.0
