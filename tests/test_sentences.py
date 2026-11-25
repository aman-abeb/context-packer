"""Tests for sentence segmentation and per-sentence token counts."""

from context_packer.sentences import sentence_token_counts, split_sentences
from context_packer.tokens import count_tokens


def test_empty_and_whitespace_input() -> None:
    assert split_sentences("") == []
    assert split_sentences("   \n\t  ") == []


def test_single_sentence_without_punctuation() -> None:
    assert split_sentences("just a fragment") == ["just a fragment"]


def test_multi_sentence_paragraph() -> None:
    text = "The auth flow starts here. It redirects to the IdP. Tokens are returned."
    assert split_sentences(text) == [
        "The auth flow starts here.",
        "It redirects to the IdP.",
        "Tokens are returned.",
    ]


def test_question_and_exclamation_marks() -> None:
    assert split_sentences("Really? Yes! Done.") == ["Really?", "Yes!", "Done."]


def test_runs_of_punctuation_stay_together() -> None:
    assert split_sentences("Wait... what?! ok") == ["Wait...", "what?!", "ok"]


def test_newlines_are_boundaries() -> None:
    text = "First line.\nSecond line.\n\nThird line."
    assert split_sentences(text) == ["First line.", "Second line.", "Third line."]


def test_abbreviations_do_not_split() -> None:
    text = "Dr. Smith reviewed the PR. Mr. Jones approved it."
    assert split_sentences(text) == [
        "Dr. Smith reviewed the PR.",
        "Mr. Jones approved it.",
    ]


def test_dotted_abbreviations_do_not_split() -> None:
    assert split_sentences("Use e.g. retries. Also i.e. backoff.") == [
        "Use e.g. retries.",
        "Also i.e. backoff.",
    ]


def test_single_letter_initials_do_not_split() -> None:
    text = "J. R. R. Tolkien wrote it. It is long."
    assert split_sentences(text) == ["J. R. R. Tolkien wrote it.", "It is long."]


def test_decimal_numbers_do_not_split() -> None:
    assert split_sentences("Pi is 3.14 roughly. Yes.") == ["Pi is 3.14 roughly.", "Yes."]


def test_filename_period_still_splits() -> None:
    assert split_sentences("See file.txt. It helps.") == ["See file.txt.", "It helps."]


def test_sentences_preserve_punctuation_and_strip_whitespace() -> None:
    assert split_sentences("  Hello world.   Again?  ") == ["Hello world.", "Again?"]


def test_sentence_token_counts_are_exact() -> None:
    text = "hello world. bye now."
    assert sentence_token_counts(text) == [
        ("hello world.", count_tokens("hello world.")),
        ("bye now.", count_tokens("bye now.")),
    ]


def test_sentence_token_counts_known_value() -> None:
    # cl100k_base encodes "hello world" as exactly two tokens.
    assert sentence_token_counts("hello world") == [("hello world", 2)]


def test_sentence_token_counts_empty_input() -> None:
    assert sentence_token_counts("") == []
    assert sentence_token_counts("  \n ") == []


def test_sentence_token_counts_match_split_sentences() -> None:
    text = "One sentence here. Another one follows! And a third?"
    pairs = sentence_token_counts(text)
    assert [sentence for sentence, _ in pairs] == split_sentences(text)
    assert all(isinstance(n, int) and n > 0 for _, n in pairs)
