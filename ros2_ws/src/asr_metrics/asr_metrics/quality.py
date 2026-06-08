"""Text quality metrics (WER/CER) used in benchmark reports."""

from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass
from typing import Literal

UnicodeForm = Literal["NFC", "NFD", "NFKC", "NFKD"]


class MissingQualityReferenceError(ValueError):
    """Raised when quality metrics cannot be computed from an empty reference."""


@dataclass(frozen=True, slots=True)
class EvaluationPolicy:
    """Text normalization policy used by ASR quality metrics."""

    unicode_form: UnicodeForm = "NFKC"
    casefold: bool = True
    remove_punctuation: bool = True
    normalize_whitespace: bool = True
    cer_ignore_whitespace: bool = True
    language: str = "und"
    keep_empty_references: bool = True

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_EVALUATION_POLICY = EvaluationPolicy()


@dataclass(frozen=True, slots=True)
class EditCounts:
    """Raw alignment counts for one token sequence comparison."""

    hits: int = 0
    substitutions: int = 0
    deletions: int = 0
    insertions: int = 0

    @property
    def edits(self) -> int:
        return self.substitutions + self.deletions + self.insertions


def _align_counts(reference: list[str], hypothesis: list[str]) -> EditCounts:
    """Return Levenshtein alignment counts with deterministic tie-breaking."""
    if not reference:
        return EditCounts(insertions=len(hypothesis))
    if not hypothesis:
        return EditCounts(deletions=len(reference))

    dp = [[0] * (len(hypothesis) + 1) for _ in range(len(reference) + 1)]
    back: list[list[str]] = [[""] * (len(hypothesis) + 1) for _ in range(len(reference) + 1)]
    for i in range(len(reference) + 1):
        dp[i][0] = i
        back[i][0] = "delete" if i else ""
    for j in range(len(hypothesis) + 1):
        dp[0][j] = j
        back[0][j] = "insert" if j else ""
    for i, ref_item in enumerate(reference, start=1):
        for j, hyp_item in enumerate(hypothesis, start=1):
            if ref_item == hyp_item:
                dp[i][j] = dp[i - 1][j - 1]
                back[i][j] = "hit"
                continue
            candidates = (
                (dp[i - 1][j - 1] + 1, "substitute"),
                (dp[i - 1][j] + 1, "delete"),
                (dp[i][j - 1] + 1, "insert"),
            )
            dp[i][j], back[i][j] = min(candidates, key=lambda item: item[0])

    hits = substitutions = deletions = insertions = 0
    i = len(reference)
    j = len(hypothesis)
    while i > 0 or j > 0:
        op = back[i][j]
        if op == "hit":
            hits += 1
            i -= 1
            j -= 1
        elif op == "substitute":
            substitutions += 1
            i -= 1
            j -= 1
        elif op == "delete":
            deletions += 1
            i -= 1
        elif op == "insert":
            insertions += 1
            j -= 1
        else:
            break
    return EditCounts(
        hits=hits,
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
    )


def normalize_text(text: str, policy: EvaluationPolicy | None = None) -> str:
    """Normalize text for ASR metrics by lowering case and dropping punctuation/symbol noise."""
    active_policy = policy or DEFAULT_EVALUATION_POLICY
    normalized_text = unicodedata.normalize(active_policy.unicode_form, str(text))
    if active_policy.casefold:
        normalized_text = normalized_text.casefold()

    normalized_chars: list[str] = []
    for char in normalized_text.strip():
        if char.isspace():
            normalized_chars.append(" ")
            continue
        category = unicodedata.category(char)
        if category.startswith(("L", "N")) or not active_policy.remove_punctuation:
            normalized_chars.append(char)
            continue
        # Drop punctuation and symbols from both reference and hypothesis so
        # baseline WER/CER do not over-penalize formatting differences.
    output = "".join(normalized_chars)
    if active_policy.normalize_whitespace:
        output = " ".join(output.split())
    return output


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
    reference_has_content: bool
    hypothesis_has_content: bool
    reference_word_count: int
    reference_char_count: int
    word_edits: int
    char_edits: int
    hits: int
    substitutions: int
    deletions: int
    insertions: int
    word_hits: int
    word_substitutions: int
    word_deletions: int
    word_insertions: int
    char_hits: int
    char_substitutions: int
    char_deletions: int
    char_insertions: int
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

    @property
    def sample_accuracy(self) -> float:
        return 1.0 if self.exact_match else 0.0

    @property
    def ser(self) -> float:
        return 1.0 - self.sample_accuracy

    @property
    def mer(self) -> float:
        denominator = self.hits + self.substitutions + self.deletions + self.insertions
        if denominator <= 0:
            return 0.0
        return float(self.substitutions + self.deletions + self.insertions) / float(denominator)

    @property
    def wip(self) -> float:
        recall_denominator = self.hits + self.substitutions + self.deletions
        precision_denominator = self.hits + self.substitutions + self.insertions
        if recall_denominator <= 0 or precision_denominator <= 0:
            return 0.0
        return (float(self.hits) / float(recall_denominator)) * (
            float(self.hits) / float(precision_denominator)
        )

    @property
    def wil(self) -> float:
        return 1.0 - self.wip

    @property
    def hallucination_on_silence(self) -> float:
        return 1.0 if not self.reference_has_content and self.hypothesis_has_content else 0.0

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["wer"] = self.wer
        payload["cer"] = self.cer
        payload["sample_accuracy"] = self.sample_accuracy
        payload["ser"] = self.ser
        payload["mer"] = self.mer
        payload["wil"] = self.wil
        payload["wip"] = self.wip
        payload["hallucination_on_silence"] = self.hallucination_on_silence
        return payload


def text_quality_support(
    reference: str,
    hypothesis: str,
    policy: EvaluationPolicy | None = None,
) -> TextQualitySupport:
    """Return normalized text and edit counters used by WER/CER/sample accuracy."""
    active_policy = policy or DEFAULT_EVALUATION_POLICY
    normalized_reference = normalize_text(reference, active_policy)
    normalized_hypothesis = normalize_text(hypothesis, active_policy)
    ref_words = normalized_reference.split()
    hyp_words = normalized_hypothesis.split()
    if active_policy.cer_ignore_whitespace:
        ref_chars = list(normalized_reference.replace(" ", ""))
        hyp_chars = list(normalized_hypothesis.replace(" ", ""))
    else:
        ref_chars = list(normalized_reference)
        hyp_chars = list(normalized_hypothesis)

    reference_has_content = bool(normalized_reference)
    hypothesis_has_content = bool(normalized_hypothesis)
    reference_word_count = len(ref_words)
    reference_char_count = len(ref_chars)
    word_counts = _align_counts(ref_words, hyp_words)
    char_counts = _align_counts(ref_chars, hyp_chars)

    return TextQualitySupport(
        normalized_reference=normalized_reference,
        normalized_hypothesis=normalized_hypothesis,
        reference_has_content=reference_has_content,
        hypothesis_has_content=hypothesis_has_content,
        reference_word_count=reference_word_count,
        reference_char_count=reference_char_count,
        word_edits=word_counts.edits,
        char_edits=char_counts.edits,
        hits=word_counts.hits,
        substitutions=word_counts.substitutions,
        deletions=word_counts.deletions,
        insertions=word_counts.insertions,
        word_hits=word_counts.hits,
        word_substitutions=word_counts.substitutions,
        word_deletions=word_counts.deletions,
        word_insertions=word_counts.insertions,
        char_hits=char_counts.hits,
        char_substitutions=char_counts.substitutions,
        char_deletions=char_counts.deletions,
        char_insertions=char_counts.insertions,
        exact_match=reference_has_content and normalized_reference == normalized_hypothesis,
    )


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate."""
    return text_quality_support(reference, hypothesis).wer


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate with spaces removed after normalization."""
    return text_quality_support(reference, hypothesis).cer
