"""JSON manifest export of a packed result.

The manifest is the machine-readable counterpart of the CLI table: it records
the query, the budget, the token utilization, and the packed files (with a
``partial`` flag for sentence-truncated inclusions).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from context_packer.packer import PackResult

#: Schema version of the exported manifest.
MANIFEST_VERSION = 1


def build_manifest(result: PackResult, query: str) -> dict[str, Any]:
    """Build a JSON-serializable manifest describing ``result`` for ``query``.

    The returned dict has the keys ``version``, ``query``, ``budget``,
    ``total_tokens``, ``remaining_tokens``, ``coverage`` and ``files``, where
    ``files`` is a list of ``{"path", "tokens", "partial"}`` entries in packed
    (ranked) order.
    """
    return {
        "version": MANIFEST_VERSION,
        "query": query,
        "budget": result.budget,
        "total_tokens": result.total_tokens,
        "remaining_tokens": result.remaining_tokens,
        "coverage": result.coverage,
        "files": [
            {"path": packed.path, "tokens": packed.tokens, "partial": packed.partial}
            for packed in result.files
        ],
    }


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    """Write ``manifest`` to ``path`` as pretty-printed JSON.

    Keys are sorted, the output is indented with two spaces, and a trailing
    newline is appended. Parent directories are created as needed. Returns the
    path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
