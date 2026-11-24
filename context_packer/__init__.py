"""ContextPacker: offline BM25 ranking and token-budget packing of doc directories."""

from context_packer.scanner import read_text, scan_directory
from context_packer.tokens import count_tokens

__version__ = "0.1.0"

__all__ = ["__version__", "count_tokens", "read_text", "scan_directory"]
