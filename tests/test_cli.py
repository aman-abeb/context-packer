"""Tests for the click CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from context_packer.__main__ import cli
from context_packer.tokens import count_tokens

AUTH_MD = (
    "The auth flow starts at the login page. "
    "The auth flow redirects to the identity provider. "
    "Auth tokens are returned along the flow."
)
LOGIN_MD = "Login page. Enter your credentials. Sessions are stored server side."
RECIPE_MD = "Banana bread. Mix flour, sugar, and bananas. Bake for one hour."


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture()
def docs(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    _write(root / "auth.md", AUTH_MD)
    _write(root / "login.md", LOGIN_MD)
    _write(root / "recipe.md", RECIPE_MD)
    return root


def test_no_arguments_prints_help_and_exits_zero() -> None:
    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "pack" in result.output


def test_module_entrypoint_without_arguments_exits_zero() -> None:
    project_root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, "-m", "context_packer"],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=60,
    )
    assert proc.returncode == 0
    assert "Usage" in proc.stdout


def test_pack_prints_ranked_table_and_utilization_line(docs: Path) -> None:
    result = CliRunner().invoke(
        cli, ["pack", str(docs), "--query", "auth flow", "--budget", "4000"]
    )
    assert result.exit_code == 0, result.output
    assert "Packed 3 of 3 scanned files (0 partial)" in result.output
    assert "rank" in result.output and "tokens" in result.output and "path" in result.output
    rows = [line for line in result.output.splitlines() if line.rstrip().endswith(".md")]
    assert [row.split()[-1] for row in rows] == ["auth.md", "login.md", "recipe.md"]
    # Per-file token counts appear in the table.
    assert str(count_tokens(AUTH_MD)) in rows[0]
    total = count_tokens(AUTH_MD) + count_tokens(LOGIN_MD) + count_tokens(RECIPE_MD)
    assert f"Total: {total}/4000 tokens" in result.output
    assert "coverage:" in result.output
    assert f"{4000 - total} remaining" in result.output


def test_pack_ranks_best_bm25_match_first(docs: Path) -> None:
    result = CliRunner().invoke(
        cli, ["pack", str(docs), "--query", "auth flow", "--budget", "4000"]
    )
    assert result.exit_code == 0, result.output
    first_row = next(
        line for line in result.output.splitlines() if line.rstrip().endswith("auth.md")
    )
    assert first_row.split()[0] == "1"


def test_pack_partial_inclusion_is_sentence_safe(docs: Path, tmp_path: Path) -> None:
    first_sentence = "The auth flow starts at the login page."
    budget = count_tokens(first_sentence)
    manifest_path = tmp_path / "manifest.json"
    result = CliRunner().invoke(
        cli,
        [
            "pack",
            str(docs),
            "--query",
            "auth flow",
            "--budget",
            str(budget),
            "--manifest",
            str(manifest_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "(1 partial)" in result.output
    row = next(line for line in result.output.splitlines() if line.rstrip().endswith("auth.md"))
    assert "yes" in row
    assert str(budget) in row
    assert f"Total: {budget}/{budget} tokens (coverage: 100.0%)" in result.output
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["files"] == [{"path": "auth.md", "tokens": budget, "partial": True}]
    assert manifest["coverage"] == 1.0


def test_pack_manifest_option_writes_valid_manifest(docs: Path, tmp_path: Path) -> None:
    manifest_path = tmp_path / "nested" / "manifest.json"
    result = CliRunner().invoke(
        cli,
        [
            "pack",
            str(docs),
            "--query",
            "auth flow",
            "--budget",
            "4000",
            "--manifest",
            str(manifest_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Manifest written to" in result.output
    text = manifest_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    manifest = json.loads(text)
    assert set(manifest) == {
        "version",
        "query",
        "budget",
        "total_tokens",
        "remaining_tokens",
        "coverage",
        "files",
    }
    assert manifest["version"] == 1
    assert manifest["query"] == "auth flow"
    assert manifest["budget"] == 4000
    assert [entry["path"] for entry in manifest["files"]] == [
        "auth.md",
        "login.md",
        "recipe.md",
    ]
    assert all(set(entry) == {"path", "tokens", "partial"} for entry in manifest["files"])
    assert all(entry["partial"] is False for entry in manifest["files"])
    assert manifest["total_tokens"] == sum(entry["tokens"] for entry in manifest["files"])
    assert manifest["remaining_tokens"] == 4000 - manifest["total_tokens"]
    assert manifest["coverage"] == pytest.approx(manifest["total_tokens"] / 4000)


def test_pack_empty_directory_exits_zero(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    manifest_path = tmp_path / "manifest.json"
    result = CliRunner().invoke(
        cli,
        [
            "pack",
            str(empty),
            "--query",
            "auth",
            "--budget",
            "100",
            "--manifest",
            str(manifest_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Total: 0/100 tokens (coverage: 0.0%), 100 remaining" in result.output
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["files"] == []
    assert manifest["total_tokens"] == 0
    assert manifest["coverage"] == 0.0
    assert manifest["remaining_tokens"] == 100


def test_pack_zero_budget_packs_nothing(docs: Path) -> None:
    result = CliRunner().invoke(cli, ["pack", str(docs), "--query", "auth flow", "--budget", "0"])
    assert result.exit_code == 0, result.output
    assert "Total: 0/0 tokens (coverage: 0.0%), 0 remaining" in result.output


def test_pack_missing_directory_fails(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli,
        ["pack", str(tmp_path / "nope"), "--query", "x", "--budget", "10"],
    )
    assert result.exit_code != 0


def test_pack_negative_budget_is_rejected(docs: Path) -> None:
    result = CliRunner().invoke(cli, ["pack", str(docs), "--query", "x", "--budget", "-5"])
    assert result.exit_code != 0


def test_pack_requires_query_option(docs: Path) -> None:
    result = CliRunner().invoke(cli, ["pack", str(docs), "--budget", "100"])
    assert result.exit_code != 0
