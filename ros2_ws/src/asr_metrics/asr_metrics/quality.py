"""Text quality metrics (WER/CER) used in benchmark reports."""

from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass


class MissingQualityReferenceError(ValueError):
    """Raised when quality metrics cannot be computed from an empty reference."""


def _levenshtein(a: list[str], b: list[str]) -> int:
    """Classic edit-distance implementation."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        dp[i][0] = i
    for j in range(len(b) + 1):
        dp[0][j] = j
    for i, ai in enumerate(a, start=1):
        for j, bj in enumerate(b, start=1):
            cost = 0 if ai == bj else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[-1][-1]


def normalize_text(text: str) -> str:
    """Normalize text for ASR metrics by lowering case and dropping punctuation/symbol noise."""
    normalized_chars: list[str] = []
    for char in text.strip().lower():
        if char.isspace():
            normalized_chars.append(" ")
            continue
        category = unicodedata.category(char)
        if category.startswith(("L", "N")):
            normalized_chars.append(char)
            continue
        # Drop punctuation and symbols from both reference and hypothesis so
        # baseline WER/CER do not over-penalize formatting differences.
    return " ".join("".join(normalized_chars).split())


def has_quality_reference(reference: str) -> bool:
    """Return True when the reference still contains lexical content after normalization."""
    return bool(normalize_text(reference))


def require_quality_reference(reference: str, *, context: str = "Quality metrics") -> str:
    """Fail fast when the normalized reference is empty."""
    normalized_reference = normalize_text(reference)
    if normalized_reference:
        return normalized_reference
    raise MissingQualityReferenceError(
        f"{context} requires a non-empty reference transcript after normalization."
    )


@dataclass(frozen=True, slots=True)
class TextQualitySupport:
    """Support data required for logically-correct quality aggregation."""

    normalized_reference: str
    normalized_hypothesis: str
    reference_word_count: int
    reference_char_count: int
    word_edits: int
    char_edits: int
    exact_match: bool

    @property
    def wer(self) -> float:
        if self.reference_word_count <= 0:
            return 0.0
        return float(self.word_edits) / float(self.reference_word_count)

    @property
    def cer(self) -> float:
        if self.reference_char_count <= 0:
            return 0.0
        return float(self.char_edits) / float(self.reference_char_count)

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["wer"] = self.wer
        payload["cer"] = self.cer
        return payload


def text_quality_support(reference: str, hypothesis: str) -> TextQualitySupport:
    """Return normalized text and edit counters used by WER/CER/sample accuracy."""
    normalized_reference = normalize_text(reference)
    normalized_hypothesis = normalize_text(hypothesis)
    ref_words = normalized_reference.split()
    hyp_words = normalized_hypothesis.split()
    ref_chars = list(normalized_reference.replace(" ", ""))
    hyp_chars = list(normalized_hypothesis.replace(" ", ""))

    # Empty-reference rows are not expected in benchmark manifests, but when they
    # appear we keep the existing 0/1 behaviour by forcing a denominator of 1
    # only for non-empty hypotheses.
    reference_word_count = len(ref_words) or len(hyp_words)
    reference_char_count = len(ref_chars) or len(hyp_chars)

    return TextQualitySupport(
        normalized_reference=normalized_reference,
        normalized_hypothesis=normalized_hypothesis,
        reference_word_count=reference_word_count,
        reference_char_count=reference_char_count,
        word_edits=_levenshtein(ref_words, hyp_words),
        char_edits=_levenshtein(ref_chars, hyp_chars),
        exact_match=normalized_reference == normalized_hypothesis,
    )


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate."""
    return text_quality_support(reference, hypothesis).wer


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate with spaces removed after normalization."""
    return text_quality_support(reference, hypothesis).cer
