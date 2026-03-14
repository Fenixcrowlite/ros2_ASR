"""Text quality metrics (WER/CER) used in benchmark reports."""

from __future__ import annotations

import unicodedata


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


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate."""
    ref = normalize_text(reference).split()
    hyp = normalize_text(hypothesis).split()
    if not ref:
        return 0.0 if not hyp else 1.0
    return _levenshtein(ref, hyp) / float(len(ref))


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate."""
    ref = list(normalize_text(reference).replace(" ", ""))
    hyp = list(normalize_text(hypothesis).replace(" ", ""))
    if not ref:
        return 0.0 if not hyp else 1.0
    return _levenshtein(ref, hyp) / float(len(ref))
