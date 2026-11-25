"""ContextPacker: offline BM25 ranking and token-budget packing of doc directories."""

from context_packer.manifest import MANIFEST_VERSION, build_manifest, write_manifest
from context_packer.packer import PackedFile, PackResult, pack, sentence_aligned_prefix
from context_packer.scanner import read_text, scan_directory
from context_packer.scorer import K1, B, RankedFile, bm25_scores, rank_files, tokenize
from context_packer.sentences import sentence_token_counts, split_sentences
from context_packer.tokens import count_tokens

__version__ = "0.1.0"

__all__ = [
    "B",
    "K1",
    "MANIFEST_VERSION",
    "PackedFile",
    "PackResult",
    "RankedFile",
    "__version__",
    "bm25_scores",
    "build_manifest",
    "count_tokens",
    "pack",
    "rank_files",
    "read_text",
    "scan_directory",
    "sentence_aligned_prefix",
    "sentence_token_counts",
    "split_sentences",
    "tokenize",
    "write_manifest",
]
