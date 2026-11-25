"""Tests for the JSON manifest export."""

import json
from pathlib import Path

import pytest

from context_packer import MANIFEST_VERSION, build_manifest, pack, write_manifest
from context_packer.tokens import count_tokens


def test_build_manifest_has_required_keys_and_types() -> None:
    manifest = build_manifest(pack([], budget=10), "auth flow")
    assert set(manifest) == {
        "version",
        "query",
        "budget",
        "total_tokens",
        "remaining_tokens",
        "coverage",
        "files",
    }
    assert manifest["version"] == MANIFEST_VERSION
    assert isinstance(manifest["version"], int)
    assert manifest["query"] == "auth flow"
    assert isinstance(manifest["budget"], int)
    assert isinstance(manifest["total_tokens"], int)
    assert isinstance(manifest["remaining_tokens"], int)
    assert isinstance(manifest["coverage"], float)
    assert manifest["files"] == []


def test_build_manifest_empty_result_math() -> None:
    manifest = build_manifest(pack([], budget=10), "q")
    assert manifest["total_tokens"] == 0
    assert manifest["remaining_tokens"] == 10
    assert manifest["coverage"] == 0.0


def test_build_manifest_file_entries_match_packed_files() -> None:
    files = [("a.md", "alpha beta."), ("b.md", "gamma delta. epsilon zeta.")]
    result = pack(files, budget=100)
    manifest = build_manifest(result, "alpha")
    assert len(manifest["files"]) == len(result.files)
    for entry, packed in zip(manifest["files"], result.files, strict=True):
        assert set(entry) == {"path", "tokens", "partial"}
        assert entry["path"] == packed.path
        assert isinstance(entry["path"], str)
        assert entry["tokens"] == packed.tokens
        assert isinstance(entry["tokens"], int)
        assert entry["partial"] == packed.partial
        assert isinstance(entry["partial"], bool)


def test_build_manifest_utilization_math() -> None:
    result = pack([("a.md", "hello world")], budget=10)  # "hello world" is 2 tokens
    manifest = build_manifest(result, "hello")
    assert manifest["total_tokens"] == 2
    assert manifest["remaining_tokens"] == 8
    assert manifest["coverage"] == pytest.approx(0.2)


def test_build_manifest_coverage_is_capped_at_one() -> None:
    result = pack([("a.md", "hello world")], budget=2)
    assert build_manifest(result, "q")["coverage"] == 1.0


def test_build_manifest_marks_partial_files() -> None:
    big = "first sentence here. second sentence here."
    budget = count_tokens("first sentence here.")
    result = pack([("big.md", big)], budget=budget)
    manifest = build_manifest(result, "q")
    assert manifest["files"] == [{"path": "big.md", "tokens": budget, "partial": True}]


def test_manifest_is_json_serializable_and_round_trips() -> None:
    result = pack([("a.md", "hello world."), ("b.md", "bye now.")], budget=100)
    manifest = build_manifest(result, "hello")
    assert json.loads(json.dumps(manifest)) == manifest


def test_write_manifest_writes_sorted_json_with_trailing_newline(tmp_path: Path) -> None:
    result = pack([("a.md", "hello world.")], budget=100)
    manifest = build_manifest(result, "hello")
    path = tmp_path / "manifest.json"
    returned = write_manifest(path, manifest)
    assert returned == path
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == manifest
    assert list(json.loads(text)) == sorted(json.loads(text))


def test_write_manifest_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deep" / "manifest.json"
    write_manifest(path, build_manifest(pack([], budget=5), "q"))
    assert json.loads(path.read_text(encoding="utf-8"))["budget"] == 5
