"""Discovery of text documents inside a directory tree."""

from __future__ import annotations

from pathlib import Path

#: File suffixes treated as plain text.
TEXT_SUFFIXES: frozenset[str] = frozenset(
    {
        ".c",
        ".cfg",
        ".clj",
        ".cpp",
        ".cs",
        ".css",
        ".csv",
        ".go",
        ".h",
        ".hpp",
        ".html",
        ".ini",
        ".java",
        ".js",
        ".json",
        ".jsonl",
        ".kt",
        ".lua",
        ".md",
        ".py",
        ".r",
        ".rb",
        ".rs",
        ".rst",
        ".sh",
        ".sql",
        ".swift",
        ".toml",
        ".ts",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)

#: File suffixes that are always considered binary, without sniffing.
BINARY_SUFFIXES: frozenset[str] = frozenset(
    {
        ".7z",
        ".avi",
        ".bin",
        ".bmp",
        ".bz2",
        ".class",
        ".dll",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".jar",
        ".jpeg",
        ".jpg",
        ".mkv",
        ".mov",
        ".mp3",
        ".mp4",
        ".o",
        ".pdf",
        ".png",
        ".pyc",
        ".so",
        ".tar",
        ".tiff",
        ".wav",
        ".webp",
        ".woff",
        ".woff2",
        ".xz",
        ".zip",
    }
)

#: Number of leading bytes inspected when sniffing for binary content.
_SNIFF_SIZE = 8192


def _is_hidden(relative: Path) -> bool:
    """Return True if any component of ``relative`` starts with a dot."""
    return any(part.startswith(".") for part in relative.parts)


def looks_binary(path: Path, sniff_size: int = _SNIFF_SIZE) -> bool:
    """Heuristically detect binary content by looking for NUL bytes."""
    with path.open("rb") as handle:
        chunk = handle.read(sniff_size)
    return b"\x00" in chunk


def read_text(path: str | Path) -> str:
    """Read a text file as UTF-8, replacing undecodable bytes."""
    return Path(path).read_text(encoding="utf-8", errors="replace")


def scan_directory(root: str | Path) -> list[Path]:
    """Return the sorted paths of all text files under ``root``.

    Hidden files and directories (names starting with ``.``), files with a
    known binary suffix, and files whose content sniffs as binary are
    excluded. Extensionless files are included when their content looks
    like text.

    Raises:
        NotADirectoryError: if ``root`` is not an existing directory.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        raise NotADirectoryError(f"not a directory: {root_path}")

    found: list[Path] = []
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root_path)
        if _is_hidden(relative):
            continue
        suffix = path.suffix.lower()
        if suffix in BINARY_SUFFIXES:
            continue
        if suffix and suffix not in TEXT_SUFFIXES:
            continue
        if looks_binary(path):
            continue
        found.append(path)
    return sorted(found)
