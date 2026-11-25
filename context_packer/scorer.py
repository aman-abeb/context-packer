"""Pure-Python Okapi BM25 relevance ranking.

Documents and queries are tokenized into lowercase alphanumeric words and
ranked with the classic BM25 formula:

    score(D, Q) = sum_t IDF(t) * (f(t, D) * (k1 + 1)) / (f(t, D) + k1 * (1 - b + b * |D| / avgdl))

with ``IDF(t) = ln(1 + (N - n + 0.5) / (n + 0.5))``. Everything runs locally;
no network access or third-party scoring dependency is involved.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

#: BM25 term-frequency saturation parameter.
K1: float = 1.5

#: BM25 document-length normalization parameter.
B: float = 0.75

_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Return the lowercase alphanumeric word tokens of ``text``."""
    return _WORD.findall(text.lower())


@dataclass(frozen=True)
class RankedFile:
    """A document together with its BM25 score against the query."""

    path: str
    content: str
    score: float


def bm25_scores(
    query: str,
    documents: Iterable[str],
    k1: float = K1,
    b: float = B,
) -> list[float]:
    """Score each document against ``query`` with Okapi BM25.

    Args:
        query: The search query, tokenized the same way as the documents.
        documents: The document texts, in any order.
        k1: Term-frequency saturation parameter.
        b: Length-normalization parameter.

    Returns:
        One non-negative score per document, in the same order as
        ``documents``. Documents sharing no query terms score ``0.0``.
    """
    docs = list(documents)
    if not docs:
        return []
    query_terms = tokenize(query)
    term_freqs = [Counter(tokenize(doc)) for doc in docs]
    lengths = [sum(freqs.values()) for freqs in term_freqs]
    avg_length = sum(lengths) / len(lengths)
    n_docs = len(docs)

    query_set = set(query_terms)
    doc_freq = {term: 0 for term in query_set}
    for freqs in term_freqs:
        for term in query_set.intersection(freqs):
            doc_freq[term] += 1

    scores: list[float] = []
    for freqs, length in zip(term_freqs, lengths, strict=True):
        score = 0.0
        for term in query_terms:
            freq = freqs.get(term, 0)
            if freq == 0:
                continue
            n = doc_freq[term]
            idf = math.log(1.0 + (n_docs - n + 0.5) / (n + 0.5))
            norm = k1 * (1.0 - b + b * (length / avg_length if avg_length else 0.0))
            score += idf * (freq * (k1 + 1.0)) / (freq + norm)
        scores.append(score)
    return scores


def rank_files(
    query: str,
    files: Iterable[tuple[str | Path, str]],
    k1: float = K1,
    b: float = B,
) -> list[RankedFile]:
    """Rank ``(path, content)`` pairs by BM25 relevance to ``query``, best first.

    Ties (including all-zero scores) are broken by path, so the ranking is
    deterministic across runs.
    """
    items = [(str(path), content) for path, content in files]
    scores = bm25_scores(query, (content for _, content in items), k1=k1, b=b)
    ranked = [
        RankedFile(path=path, content=content, score=score)
        for (path, content), score in zip(items, scores, strict=True)
    ]
    ranked.sort(key=lambda item: (-item.score, item.path))
    return ranked
