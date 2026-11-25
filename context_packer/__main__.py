"""Command-line entrypoint for ContextPacker.

Run with ``python -m context_packer``; with no arguments it prints the CLI
help and exits 0.
"""

from __future__ import annotations

from pathlib import Path

import click

from context_packer import packer
from context_packer.manifest import build_manifest, write_manifest
from context_packer.packer import PackResult
from context_packer.scanner import read_text, scan_directory
from context_packer.scorer import rank_files
from context_packer.tokens import DEFAULT_ENCODING


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ContextPacker: rank docs by BM25 relevance and pack them into an LLM token budget, fully offline."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _print_report(result: PackResult, scores: dict[str, float], scanned: int) -> None:
    """Print the ranked table of packed files followed by the utilization line."""
    partial_count = sum(1 for packed in result.files if packed.partial)
    click.echo(
        f"Packed {len(result.files)} of {scanned} scanned files "
        f"({partial_count} partial) into a {result.budget}-token budget."
    )
    if result.files:
        header = f"{'rank':>4}  {'tokens':>6}  {'partial':>7}  {'score':>7}  path"
        click.echo(header)
        click.echo("-" * len(header))
        for rank, packed in enumerate(result.files, start=1):
            partial = "yes" if packed.partial else "no"
            score = scores.get(packed.path, 0.0)
            click.echo(f"{rank:>4}  {packed.tokens:>6}  {partial:>7}  {score:>7.2f}  {packed.path}")
    else:
        click.echo("No files fit the budget.")
    click.echo(
        f"Total: {result.total_tokens}/{result.budget} tokens "
        f"(coverage: {result.coverage * 100:.1f}%), {result.remaining_tokens} remaining"
    )


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--query", required=True, help="Query used to rank files by BM25 relevance.")
@click.option(
    "--budget",
    type=click.IntRange(min=0),
    default=4000,
    show_default=True,
    help="Hard token budget for the packed set.",
)
@click.option(
    "--manifest",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write a JSON manifest of the packed set to this path.",
)
@click.option(
    "--encoding",
    default=DEFAULT_ENCODING,
    show_default=True,
    help="tiktoken encoding used for all token counts.",
)
def pack(
    directory: Path,
    query: str,
    budget: int,
    manifest: Path | None,
    encoding: str,
) -> None:
    """Pack a directory of docs into a token budget.

    Ranks the text files in DIRECTORY by BM25 relevance to --query, then
    greedily packs them into --budget tokens without cutting mid-sentence.
    """
    paths = scan_directory(directory)
    documents = [(str(path.relative_to(directory)), read_text(path)) for path in paths]
    ranked = rank_files(query, documents)
    result = packer.pack(
        [(item.path, item.content) for item in ranked], budget=budget, encoding=encoding
    )
    scores = {item.path: item.score for item in ranked}
    _print_report(result, scores, scanned=len(paths))
    if manifest is not None:
        write_manifest(manifest, build_manifest(result, query))
        click.echo(f"Manifest written to {manifest}")


def main() -> None:
    """Console-script entrypoint."""
    cli(prog_name="context-packer")


if __name__ == "__main__":
    main()
