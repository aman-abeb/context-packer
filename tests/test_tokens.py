"""Tests for the tiktoken-based token counter."""

from context_packer.tokens import DEFAULT_ENCODING, count_tokens, get_encoding


def test_empty_string_is_zero_tokens() -> None:
    assert count_tokens("") == 0


def test_known_token_count() -> None:
    # cl100k_base encodes "hello world" as exactly two tokens.
    assert count_tokens("hello world") == 2


def test_counts_grow_with_text_length() -> None:
    short = count_tokens("auth")
    long = count_tokens("auth flow " * 100)
    assert long > short


def test_unicode_text_counts_positive() -> None:
    assert count_tokens("héllo wörld — ünïcode ✓") > 0


def test_encoding_is_cached_per_name() -> None:
    assert get_encoding(DEFAULT_ENCODING) is get_encoding(DEFAULT_ENCODING)


def test_custom_encoding_name() -> None:
    assert count_tokens("hello world", encoding="cl100k_base") == 2
