"""Hugging Face provider adapters."""

from asr_provider_huggingface.api_provider import HuggingFaceAPIProvider
from asr_provider_huggingface.local_provider import HuggingFaceLocalProvider

__all__ = [
    "HuggingFaceLocalProvider",
    "HuggingFaceAPIProvider",
]
