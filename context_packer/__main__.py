"""Command-line entrypoint for ContextPacker.

Run with ``python -m context_packer``; with no arguments it prints the CLI
help and exits 0.
"""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """ContextPacker: rank docs by BM25 relevance and pack them into an LLM token budget, fully offline."""


def main() -> None:
    """Console-script entrypoint."""
    cli(prog_name="context-packer")


if __name__ == "__main__":
    main()
