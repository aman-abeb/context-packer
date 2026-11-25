"""ContextPacker: offline BM25 ranking and token-budget packing of doc directories."""

from context_packer.packer import PackedFile, PackResult, pack, sentence_aligned_prefix
from context_packer.scanner import read_text, scan_directory
from context_packer.sentences import sentence_token_counts, split_sentences
from context_packer.tokens import count_tokens

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "PackedFile",
    "PackResult",
    "count_tokens",
    "pack",
    "read_text",
    "scan_directory",
    "sentence_aligned_prefix",
    "sentence_token_counts",
    "split_sentences",
]
