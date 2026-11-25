"""Tests for the sentence-safe greedy packer."""

from pathlib import Path

import pytest

from context_packer import PackedFile, PackResult, pack, sentence_aligned_prefix
from context_packer.tokens import count_tokens


def test_pack_empty_input() -> None:
    result = pack([], budget=100)
    assert isinstance(result, PackResult)
    assert result.files == ()
    assert result.budget == 100
    assert result.total_tokens == 0
    assert result.remaining_tokens == 100
    assert result.coverage == 0.0


def test_pack_negative_budget_raises() -> None:
    with pytest.raises(ValueError, match="budget"):
        pack([("a.txt", "hello")], budget=-1)


def test_pack_includes_whole_files_while_they_fit() -> None:
    files = [("a.txt", "alpha beta."), ("b.txt", "gamma delta."), ("c.txt", "epsilon zeta.")]
    a_tokens = count_tokens("alpha beta.")
    b_tokens = count_tokens("gamma delta.")
    result = pack(files, budget=a_tokens + b_tokens)
    assert [f.path for f in result.files] == ["a.txt", "b.txt"]
    assert all(isinstance(f, PackedFile) for f in result.files)
    assert all(not f.partial for f in result.files)
    assert [f.tokens for f in result.files] == [a_tokens, b_tokens]
    assert result.total_tokens == a_tokens + b_tokens
    assert result.coverage == 1.0
    assert result.remaining_tokens == 0
    # Whole-file inclusion keeps the full content.
    assert result.files[0].content == "alpha beta."


def test_pack_exact_fit_of_every_file() -> None:
    files = [("a.txt", "hello world"), ("b.txt", "foo bar")]
    budget = sum(count_tokens(content) for _, content in files)
    result = pack(files, budget)
    assert result.total_tokens == budget
    assert result.coverage == 1.0
    assert [f.partial for f in result.files] == [False, False]


def test_pack_partially_includes_first_overflowing_file_at_sentence_boundary() -> None:
    whole = "intro sentence."
    big = "first part here. second part here. third part here."
    whole_tokens = count_tokens(whole)
    first_sentence = "first part here."
    first_tokens = count_tokens(first_sentence)
    budget = whole_tokens + first_tokens
    result = pack([("whole.txt", whole), ("big.txt", big)], budget)
    assert [f.path for f in result.files] == ["whole.txt", "big.txt"]
    partial = result.files[1]
    assert partial.partial is True
    assert partial.content == first_sentence
    assert partial.tokens == first_tokens
    assert result.total_tokens == budget
    assert result.coverage == 1.0


def test_pack_stops_after_partial_inclusion() -> None:
    big = "one two three. four five six."
    budget = count_tokens("one two three.")
    result = pack([("big.txt", big), ("small.txt", "hi")], budget)
    assert [f.path for f in result.files] == ["big.txt"]
    assert result.files[0].partial is True
    assert result.files[0].content == "one two three."


def test_pack_stops_at_first_overflow_even_if_a_later_file_would_fit() -> None:
    big = "a very long sentence that cannot fit at all."
    result = pack([("big.txt", big), ("small.txt", "hi")], budget=2)
    assert result.files == ()
    assert result.total_tokens == 0


def test_pack_budget_smaller_than_one_sentence_packs_nothing() -> None:
    result = pack([("doc.txt", "hello world. this sentence is long.")], budget=1)
    assert result.files == ()
    assert result.total_tokens == 0
    assert result.coverage == 0.0
    assert result.remaining_tokens == 1


def test_pack_zero_budget_packs_nothing() -> None:
    result = pack([("a.txt", "hello world")], budget=0)
    assert result.files == ()
    assert result.total_tokens == 0
    assert result.coverage == 0.0


def test_pack_empty_file_is_included_with_zero_tokens() -> None:
    result = pack([("empty.txt", ""), ("a.txt", "hello world")], budget=2)
    assert [f.path for f in result.files] == ["empty.txt", "a.txt"]
    assert result.files[0].tokens == 0
    assert result.files[0].partial is False
    assert result.total_tokens == 2


def test_pack_accepts_any_iterable_of_pairs() -> None:
    files = ((f"f{i}.txt", "hello world") for i in range(3))
    result = pack(files, budget=4)  # two 2-token files fit, the third does not
    assert [f.path for f in result.files] == ["f0.txt", "f1.txt"]
    assert result.total_tokens == 4


def test_pack_normalizes_path_objects_to_strings(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    result = pack([(path, "hello world")], budget=10)
    assert result.files[0].path == str(path)


def test_pack_result_coverage_is_fraction_of_budget_used() -> None:
    result = pack([("a.txt", "hello world")], budget=10)  # "hello world" is 2 tokens
    assert result.total_tokens == 2
    assert result.coverage == pytest.approx(0.2)
    assert result.remaining_tokens == 8


def test_sentence_aligned_prefix_returns_longest_fitting_prefix() -> None:
    text = "one two. three four. five six."
    budget = count_tokens("one two. three four.")
    prefix, tokens = sentence_aligned_prefix(text, budget)
    assert prefix == "one two. three four."
    assert tokens == budget
    assert tokens == count_tokens(prefix)


def test_sentence_aligned_prefix_never_exceeds_budget_and_never_cuts_mid_sentence() -> None:
    text = "alpha beta. gamma delta! epsilon zeta?"
    full = count_tokens(text)
    for budget in range(0, full + 1):
        prefix, tokens = sentence_aligned_prefix(text, budget)
        assert tokens <= budget
        assert tokens == count_tokens(prefix)
        if prefix:
            assert prefix.endswith((".", "!", "?"))
            assert text.startswith(prefix)


def test_sentence_aligned_prefix_includes_everything_when_it_fits() -> None:
    text = "short one. short two."
    prefix, tokens = sentence_aligned_prefix(text, count_tokens(text))
    assert prefix == text
    assert tokens == count_tokens(text)


def test_sentence_aligned_prefix_zero_budget_returns_empty() -> None:
    assert sentence_aligned_prefix("hello world.", 0) == ("", 0)


def test_sentence_aligned_prefix_empty_text_returns_empty() -> None:
    assert sentence_aligned_prefix("", 10) == ("", 0)


def test_sentence_aligned_prefix_negative_budget_raises() -> None:
    with pytest.raises(ValueError, match="max_tokens"):
        sentence_aligned_prefix("hello world.", -1)
