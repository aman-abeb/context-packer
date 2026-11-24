"""Token counting backed by tiktoken encodings."""

from __future__ import annotations

from functools import cache

import tiktoken

#: Encoding used for all token counts (matches GPT-4 / GPT-3.5 tokenizers).
DEFAULT_ENCODING = "cl100k_base"


@cache
def get_encoding(name: str = DEFAULT_ENCODING) -> tiktoken.Encoding:
    """Return the cached tiktoken encoding for ``name``.

    The encoding is loaded once per process and reused for every call.
    """
    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding: str = DEFAULT_ENCODING) -> int:
    """Return the number of tokens ``text`` encodes to under ``encoding``.

    An empty string counts as zero tokens.
    """
    if not text:
        return 0
    return len(get_encoding(encoding).encode(text))
