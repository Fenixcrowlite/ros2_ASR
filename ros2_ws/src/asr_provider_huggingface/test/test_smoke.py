import importlib


def test_import() -> None:
    importlib.import_module("asr_provider_huggingface")
