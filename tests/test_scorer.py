"""Tests for the pure-Python BM25 scorer."""

from pathlib import Path

from context_packer import bm25_scores, rank_files, tokenize
from context_packer.scorer import K1, B, RankedFile


def test_tokenize_lowercases_and_extracts_alphanumeric_words() -> None:
    assert tokenize("Auth flow! OAuth2 tokens.") == ["auth", "flow", "oauth2", "tokens"]


def test_tokenize_punctuation_only_is_empty() -> None:
    assert tokenize("") == []
    assert tokenize("!!! ... ---") == []


def test_bm25_scores_empty_document_list() -> None:
    assert bm25_scores("query", []) == []


def test_bm25_scores_empty_query_are_all_zero() -> None:
    assert bm25_scores("", ["some text", "more text"]) == [0.0, 0.0]
    assert bm25_scores("!!!", ["some text"]) == [0.0]


def test_bm25_matching_document_outranks_non_matching() -> None:
    docs = [
        "the auth flow redirects to the identity provider",
        "banana bread with flour and sugar",
    ]
    scores = bm25_scores("auth flow", docs)
    assert len(scores) == 2
    assert scores[0] > 0.0
    assert scores[1] == 0.0
    assert scores[0] > scores[1]


def test_bm25_scores_are_non_negative_floats_in_order() -> None:
    docs = ["alpha beta", "gamma delta", ""]
    scores = bm25_scores("alpha", docs)
    assert len(scores) == len(docs)
    assert all(isinstance(score, float) and score >= 0.0 for score in scores)
    assert scores[0] > 0.0
    assert scores[2] == 0.0


def test_bm25_more_term_occurrences_score_higher() -> None:
    scores = bm25_scores("auth", ["auth auth auth flow", "auth flow"])
    assert scores[0] > scores[1] > 0.0


def test_bm25_rarer_term_scores_higher_than_common_term() -> None:
    docs = ["common common rare", "common other"]
    rare = bm25_scores("rare", docs)
    common = bm25_scores("common", docs)
    assert rare[0] > common[0] > 0.0


def test_bm25_custom_k1_and_b() -> None:
    docs = ["alpha beta gamma", "alpha"]
    scores = bm25_scores("alpha", docs, k1=2.0, b=0.5)
    assert all(score > 0.0 for score in scores)


def test_default_parameters_are_the_classic_values() -> None:
    assert K1 == 1.5
    assert B == 0.75


def test_rank_files_orders_best_first() -> None:
    files = [
        ("b.md", "nothing relevant here"),
        ("c.md", "the auth flow of the login system"),
        ("a.md", "also nothing relevant"),
    ]
    ranked = rank_files("auth flow", files)
    assert [item.path for item in ranked] == ["c.md", "a.md", "b.md"]
    assert all(isinstance(item, RankedFile) for item in ranked)
    assert ranked[0].score > 0.0
    assert ranked[1].score == ranked[2].score == 0.0
    assert ranked[0].content == "the auth flow of the login system"


def test_rank_files_breaks_ties_by_path() -> None:
    ranked = rank_files("zzz", [("b.md", "text"), ("a.md", "text")])
    assert [item.path for item in ranked] == ["a.md", "b.md"]


def test_rank_files_empty_input() -> None:
    assert rank_files("anything", []) == []


def test_rank_files_accepts_path_objects(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    ranked = rank_files("hello", [(path, "hello world")])
    assert ranked[0].path == str(path)
    assert ranked[0].score > 0.0


def test_rank_files_is_deterministic() -> None:
    files = [("a.md", "auth flow"), ("b.md", "auth"), ("c.md", "flow auth")]
    first = rank_files("auth flow", files)
    second = rank_files("auth flow", files)
    assert [(item.path, item.score) for item in first] == [
        (item.path, item.score) for item in second
    ]
