"""Sentence segmentation with per-sentence token counts.

The packer uses this to include a partial file only up to the last sentence
boundary that fits the remaining token budget, never cutting mid-sentence.
"""

from __future__ import annotations

import re

from context_packer.tokens import DEFAULT_ENCODING, count_tokens

#: A run of sentence-ending punctuation followed by whitespace or end of text.
_BOUNDARY = re.compile(r"([.!?]+)(?=\s|$)")

#: A trailing run of letters at the end of a string.
_WORD_TAIL = re.compile(r"([A-Za-z]+)\Z")

#: A trailing dotted token such as ``e.g``, ``i.e``, ``U.S`` or ``Ph.D``.
_DOTTED_TAIL = re.compile(r"([A-Za-z]+(?:\.[A-Za-z]+)+)\Z")

#: Common abbreviations whose trailing period does not end a sentence.
_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "approx",
        "co",
        "corp",
        "dept",
        "dr",
        "etc",
        "fig",
        "inc",
        "jr",
        "ltd",
        "mr",
        "mrs",
        "ms",
        "no",
        "prof",
        "sr",
        "st",
        "vs",
    }
)


def _ends_with_abbreviation(text: str, punct_start: int) -> bool:
    """Return True if the punctuation starting at ``punct_start`` is part of an abbreviation."""
    prefix = text[:punct_start]
    dotted = _DOTTED_TAIL.search(prefix)
    if dotted and all(len(part) <= 2 for part in dotted.group(1).split(".")):
        # Short dotted tokens: e.g., i.e., U.S., Ph.D., J. R.
        return True
    word = _WORD_TAIL.search(prefix)
    if word is None:
        return False
    token = word.group(1)
    if token.lower() in _ABBREVIATIONS:
        return True
    # A single uppercase letter is a personal initial, e.g. "J. R. R. Tolkien".
    return len(token) == 1 and token.isupper()


def split_sentences(text: str) -> list[str]:
    """Split ``text`` into sentences, keeping the ending punctuation on each one.

    A sentence boundary is a run of ``.``, ``!`` or ``?`` followed by whitespace
    or the end of the text. Boundaries that belong to common abbreviations
    (``Dr.``, ``e.g.``, ``U.S.``, single-letter initials) are not treated as
    sentence ends. Whitespace around each sentence is stripped.

    >>> split_sentences("Hello world. How are you?")
    ['Hello world.', 'How are you?']
    """
    if not text.strip():
        return []
    sentences: list[str] = []
    start = 0
    for match in _BOUNDARY.finditer(text):
        punct_end = match.end(1)
        if _ends_with_abbreviation(text, match.start(1)):
            continue
        sentence = text[start:punct_end].strip()
        if sentence:
            sentences.append(sentence)
        start = punct_end
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def sentence_token_counts(text: str, encoding: str = DEFAULT_ENCODING) -> list[tuple[str, int]]:
    """Return ``(sentence, token_count)`` pairs for each sentence in ``text``.

    Token counts use the same tiktoken encoding as the rest of the package, so
    the per-sentence costs can be summed against a token budget directly.
    """
    return [(sentence, count_tokens(sentence, encoding)) for sentence in split_sentences(text)]
