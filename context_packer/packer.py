"""Sentence-safe greedy packing of ranked files into a hard token budget.

The packer is the single source of truth for both the CLI table and the JSON
manifest: it consumes ranked ``(path, content)`` pairs, includes whole files
while they fit the remaining budget, and partial-includes the first
overflowing file as the longest sentence-aligned prefix that fits — never
cutting mid-sentence.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from context_packer.sentences import sentence_token_counts
from context_packer.tokens import DEFAULT_ENCODING, count_tokens


@dataclass(frozen=True)
class PackedFile:
    """One file included in a :class:`PackResult`.

    ``content`` is the text actually packed: the full text for whole-file
    inclusion, or the sentence-aligned prefix for partial inclusion.
    """

    path: str
    tokens: int
    partial: bool
    content: str


@dataclass(frozen=True)
class PackResult:
    """The outcome of packing ranked files into a token budget."""

    files: tuple[PackedFile, ...]
    budget: int
    total_tokens: int

    @property
    def remaining_tokens(self) -> int:
        """Tokens left unused under the budget (never negative)."""
        return max(0, self.budget - self.total_tokens)

    @property
    def coverage(self) -> float:
        """Fraction of the budget that was used, in ``[0.0, 1.0]``."""
        if self.budget <= 0:
            return 0.0
        return min(1.0, self.total_tokens / self.budget)


def sentence_aligned_prefix(
    text: str, max_tokens: int, encoding: str = DEFAULT_ENCODING
) -> tuple[str, int]:
    """Return the longest sentence-aligned prefix of ``text`` fitting ``max_tokens``.

    The prefix is built from whole sentences only, so it never ends
    mid-sentence. Returns ``(prefix, token_count)`` where ``token_count`` is
    the exact token count of the returned prefix under ``encoding``.

    Raises:
        ValueError: if ``max_tokens`` is negative.
    """
    if max_tokens < 0:
        raise ValueError(f"max_tokens must be non-negative, got {max_tokens}")
    prefix = ""
    for sentence, _sentence_tokens in sentence_token_counts(text, encoding):
        candidate = f"{prefix} {sentence}" if prefix else sentence
        if count_tokens(candidate, encoding) <= max_tokens:
            prefix = candidate
        else:
            break
    return prefix, count_tokens(prefix, encoding)


def pack(
    files: Iterable[tuple[str | Path, str]],
    budget: int,
    encoding: str = DEFAULT_ENCODING,
) -> PackResult:
    """Greedily pack ranked ``(path, content)`` pairs into ``budget`` tokens.

    Files are consumed in the given (ranked) order. Each file is included
    whole while it fits in the remaining budget. The first file that
    overflows is partially included as the longest sentence-aligned prefix
    that fits — never cutting mid-sentence — and packing then stops.

    Args:
        files: Ranked ``(path, content)`` pairs, best match first.
        budget: Hard token budget; must be non-negative.
        encoding: tiktoken encoding used for all token counts.

    Returns:
        A :class:`PackResult` with the packed files, the total token count,
        and the budget.

    Raises:
        ValueError: if ``budget`` is negative.
    """
    if budget < 0:
        raise ValueError(f"budget must be non-negative, got {budget}")
    packed: list[PackedFile] = []
    total = 0
    for path, content in files:
        remaining = budget - total
        file_tokens = count_tokens(content, encoding)
        if file_tokens <= remaining:
            packed.append(PackedFile(str(path), file_tokens, partial=False, content=content))
            total += file_tokens
            continue
        # First overflowing file: include the longest sentence-aligned prefix
        # that fits, then stop — later files are not considered.
        prefix, prefix_tokens = sentence_aligned_prefix(content, remaining, encoding)
        if prefix_tokens > 0:
            packed.append(PackedFile(str(path), prefix_tokens, partial=True, content=prefix))
            total += prefix_tokens
        break
    return PackResult(files=tuple(packed), budget=budget, total_tokens=total)
