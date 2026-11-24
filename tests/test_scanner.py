"""Tests for the directory scanner."""

from pathlib import Path

import pytest

from context_packer.scanner import looks_binary, read_text, scan_directory


def _write_text(path: Path, text: str = "hello") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_empty_directory_returns_empty_list(tmp_path: Path) -> None:
    assert scan_directory(tmp_path) == []


def test_finds_text_files_recursively_and_sorted(tmp_path: Path) -> None:
    a = _write_text(tmp_path / "a.md", "alpha")
    b = _write_text(tmp_path / "nested" / "b.txt", "beta")
    c = _write_text(tmp_path / "nested" / "deep" / "c.rst", "gamma")
    assert scan_directory(tmp_path) == sorted([a, b, c])


def test_skips_hidden_files_and_directories(tmp_path: Path) -> None:
    _write_text(tmp_path / ".hidden.md", "secret")
    _write_text(tmp_path / ".git" / "config.txt", "secret")
    visible = _write_text(tmp_path / "visible.md", "ok")
    assert scan_directory(tmp_path) == [visible]


def test_skips_known_binary_suffixes(tmp_path: Path) -> None:
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    (tmp_path / "archive.zip").write_bytes(b"PK\x03\x04" + b"\x00" * 32)
    notes = _write_text(tmp_path / "notes.md", "text")
    assert scan_directory(tmp_path) == [notes]


def test_skips_binary_content_even_with_text_suffix(tmp_path: Path) -> None:
    (tmp_path / "fake.txt").write_bytes(b"hello\x00world")
    assert scan_directory(tmp_path) == []


def test_includes_extensionless_text_files(tmp_path: Path) -> None:
    license_file = _write_text(tmp_path / "LICENSE", "MIT license text")
    assert scan_directory(tmp_path) == [license_file]


def test_skips_unknown_extensions(tmp_path: Path) -> None:
    _write_text(tmp_path / "data.weirdext", "mystery")
    assert scan_directory(tmp_path) == []


def test_missing_directory_raises_not_a_directory(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        scan_directory(tmp_path / "does-not-exist")


def test_file_instead_of_directory_raises(tmp_path: Path) -> None:
    file_path = _write_text(tmp_path / "single.md")
    with pytest.raises(NotADirectoryError):
        scan_directory(file_path)


def test_looks_binary_detects_nul_bytes(tmp_path: Path) -> None:
    binary = tmp_path / "blob.bin"
    binary.write_bytes(b"\x00\x01\x02")
    text = _write_text(tmp_path / "doc.md", "plain text")
    assert looks_binary(binary)
    assert not looks_binary(text)


def test_read_text_decodes_utf8(tmp_path: Path) -> None:
    path = _write_text(tmp_path / "doc.md", "héllo")
    assert read_text(path) == "héllo"
