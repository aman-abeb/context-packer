# ContextPacker

<!-- builder:badges:start -->
[![CI](https://github.com/aman-abeb/context-packer/actions/workflows/ci.yml/badge.svg)](https://github.com/aman-abeb/context-packer/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white) ![License: MIT](https://img.shields.io/badge/license-MIT-green)
<!-- builder:badges:end -->

Offline CLI that ranks a directory of docs by BM25 relevance to a query and packs them into a strict LLM token budget — without cutting mid-sentence.

## Features

- Fully offline: local directory scan plus local token counting via tiktoken (`cl100k_base`)
- Pure-Python Okapi BM25 relevance ranking of every text file against the query (deterministic tie-breaking by path)
- Greedy whole-file packing under a hard token budget, with sentence-safe partial inclusion of the top overflowing file — never mid-sentence
- Plain-text ranked table with per-file token counts, total vs budget, remaining tokens, and coverage %
- Optional JSON manifest export of the packed set (`--manifest manifest.json`)

## Quickstart

```bash
pip install -r requirements.txt
pip install -e .

# rank ./docs against a query and pack within a 4000-token budget
context-packer pack ./docs --query 'auth flow' --budget 4000

# equivalent module invocation, also writing a JSON manifest
python -m context_packer pack ./docs --query 'auth flow' --budget 4000 --manifest manifest.json
```

## Example

Given a `docs/` directory containing `auth.md`, `login.md`, and `recipe.md`:

```text
$ context-packer pack ./docs --query 'auth flow' --budget 4000 --manifest manifest.json
Packed 3 of 3 scanned files (0 partial) into a 4000-token budget.
rank  tokens  partial    score  path
------------------------------------
   1      38       no     8.42  auth.md
   2      21       no     0.00  login.md
   3      19       no     0.00  recipe.md
Total: 78/4000 tokens (coverage: 2.0%), 3922 remaining
Manifest written to manifest.json
```

With a tight budget, the top-ranked file is included only up to the last whole sentence that fits — never mid-sentence:

```text
$ context-packer pack ./docs --query 'auth flow' --budget 20
Packed 1 of 3 scanned files (1 partial) into a 20-token budget.
rank  tokens  partial    score  path
------------------------------------
   1      18      yes    8.42  auth.md
Total: 18/20 tokens (coverage: 90.0%), 2 remaining
```

`--manifest manifest.json` writes the packed set as JSON (sorted keys, two-space indent, trailing newline):

```json
{
  "budget": 4000,
  "coverage": 0.0195,
  "files": [
    {
      "partial": false,
      "path": "auth.md",
      "tokens": 38
    },
    {
      "partial": false,
      "path": "login.md",
      "tokens": 21
    },
    {
      "partial": false,
      "path": "recipe.md",
      "tokens": 19
    }
  ],
  "query": "auth flow",
  "remaining_tokens": 3922,
  "total_tokens": 78,
  "version": 1
}
```

Running the entrypoint with no arguments prints the CLI help and exits 0:

```text
$ python -m context_packer
Usage: context-packer [OPTIONS] COMMAND ...

  ContextPacker: rank docs by BM25 relevance and pack them into an LLM
  token budget, fully offline.

Options:
  --help  Show this message and exit.

Commands:
  pack  Pack a directory of docs into a token budget.
```

## How it works

- `context_packer/scanner.py` walks the target directory, skipping hidden files/directories and binary content, and returns the sorted list of text-file paths.
- `context_packer/tokens.py` counts tokens with tiktoken's `cl100k_base` encoding, cached once per process.
- `context_packer/scorer.py` ranks files with a pure-Python Okapi BM25 implementation (`k1=1.5`, `b=0.75`); score ties break by path so output is deterministic.
- `context_packer/sentences.py` splits text into abbreviation-aware sentences and counts tokens per sentence.
- `context_packer/packer.py` greedily packs whole files under the budget, then partial-includes the first overflowing file as the longest sentence-aligned prefix that fits.
- `context_packer/manifest.py` exports the packed set as a versioned JSON manifest (`build_manifest` / `write_manifest`).
- `context_packer/__main__.py` is the click entrypoint, runnable as `python -m context_packer` or the `context-packer` console script.

## Running tests

```bash
pytest
```
