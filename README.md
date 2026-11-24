# ContextPacker

<!-- builder:badges:start -->
[![CI](https://github.com/aman-abeb/context-packer/actions/workflows/ci.yml/badge.svg)](https://github.com/aman-abeb/context-packer/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white) ![License: MIT](https://img.shields.io/badge/license-MIT-green)
<!-- builder:badges:end -->


Offline CLI that ranks a directory of docs by BM25 relevance to a query and packs them into a strict LLM token budget — without cutting mid-sentence.

## Features

- Fully offline: local directory scan plus local token counting via tiktoken (`cl100k_base`)
- Pure-Python BM25 relevance ranking of every text file against the query
- Greedy whole-file packing under a hard token budget, with sentence-safe partial inclusion of the top file
- Plain-text ranked table with per-file token counts, total vs budget, and coverage %
- Optional JSON manifest export of the packed set (`--manifest manifest.json`)

## Quickstart

```bash
pip install -r requirements.txt
pip install -e .

# scaffold check: prints CLI help and exits 0
python -m context_packer

# full command: rank ./docs against a query and pack within a 4000-token budget
context-packer pack ./docs --query 'auth flow' --budget 4000
```

## Example

Running the entrypoint with no arguments prints the CLI help and exits 0:

```text
$ python -m context_packer
Usage: context-packer [OPTIONS] COMMAND ...

  ContextPacker: rank docs by BM25 relevance and pack them into an LLM
  token budget, fully offline.

Options:
  --help  Show this message and exit.
```

## How it works

- `context_packer/scanner.py` walks the target directory, skipping hidden files/directories and binary content, and returns the sorted list of text-file paths.
- `context_packer/tokens.py` counts tokens with tiktoken's `cl100k_base` encoding, cached once per process.
- `context_packer/__main__.py` is the click entrypoint, runnable as `python -m context_packer` or the `context-packer` console script.

## Running tests

```bash
pytest
```
