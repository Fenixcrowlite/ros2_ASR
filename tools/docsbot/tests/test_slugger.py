from docsbot.planner.slugger import (
    parameter_filename,
    service_filename,
    slugify,
    stable_id,
    topic_filename,
)


def test_slugify_normalizes_symbols() -> None:
    assert slugify("/asr/text") == "asr-text"
    assert slugify("Recognize Once") == "recognize-once"


def test_stable_id_is_deterministic() -> None:
    assert stable_id("topic", "/asr/text") == stable_id("topic", "/asr/text")


def test_filename_helpers() -> None:
    assert topic_filename("/asr/text") == "asr-text.md"
    assert service_filename("/asr/recognize_once") == "asr-recognize_once.md"
    assert parameter_filename("backend.model") == "backend.model.md"
