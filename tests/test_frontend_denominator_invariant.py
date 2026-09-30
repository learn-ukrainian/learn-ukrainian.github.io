"""Keep paths read by the site inside the Frontend changed-path denominator."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from scripts.ci.frontend_change_scope import load_denominator, path_in_denominator

pytestmark = pytest.mark.repo_wide

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SITE_SOURCES = (SITE / "src", SITE / "tests")
SITE_CONFIGS = (
    SITE / "astro.config.mjs",
    SITE / "vitest.config.ts",
    SITE / "tsconfig.json",
    SITE / "src/content.config.ts",
)
SOURCE_SUFFIXES = {".astro", ".js", ".jsx", ".mjs", ".ts", ".tsx"}
RELATIVE_LITERAL = re.compile(r"(?P<quote>['\"])(?P<path>\.\./[^'\"]+)(?P=quote)")


def git_tree_paths(repo_root: Path) -> set[str]:
    """Paths at HEAD from the git object tree (sparse-checkout safe)."""
    raw = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD"], text=True, timeout=120, cwd=repo_root)
    return {line for line in raw.splitlines() if line}


def site_sources() -> list[Path]:
    return sorted(
        {path for directory in SITE_SOURCES for path in directory.rglob("*") if path.suffix in SOURCE_SUFFIXES}
        | set(SITE_CONFIGS)
    )


def external_site_paths() -> dict[str, list[str]]:
    """Resolve quoted relative imports and filesystem paths from site code/tests.

    Most paths are relative to the source file (imports, __dirname, import.meta.url).
    A process.cwd() expression in the site build/test is relative to site/.
    Only versioned targets enter a Git changed-path denominator; generated Atlas
    DBs and build trees cannot appear in the diff that this denominator checks.
    """
    found: dict[str, list[str]] = {}
    tracked = git_tree_paths(ROOT)
    for source in site_sources():
        lines = source.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            if line.lstrip().startswith(("//", "*")):
                continue
            # resolve(process.cwd(), "../...") is often formatted on three lines.
            expression = "\n".join(lines[max(0, line_number - 3):line_number])
            base = SITE if "process.cwd()" in expression and "resolve(" in expression else source.parent
            for match in RELATIVE_LITERAL.finditer(line):
                target = (base / match.group("path")).resolve()
                if not target.is_relative_to(ROOT) or target.is_relative_to(SITE) or target == ROOT:
                    continue
                repo_path = target.relative_to(ROOT).as_posix()
                if repo_path not in tracked and not any(path.startswith(repo_path + "/") for path in tracked):
                    continue
                found.setdefault(repo_path, []).append(f"{source.relative_to(ROOT)}:{line_number}")
    return found


def test_site_external_reads_are_in_frontend_denominator() -> None:
    paths = load_denominator()["paths"]
    external = external_site_paths()
    assert external, "site scan found no external paths; check the scanner"
    missing = {path: locations for path, locations in external.items() if not path_in_denominator(path, paths)}
    assert not missing, f"site reads outside Frontend denominator: {missing}"


def test_frontend_hydrate_script_dependencies_are_in_denominator() -> None:
    """The CI command chain also reads Python helpers and Atlas registry inputs."""
    paths = load_denominator()["paths"]
    dependencies = (
        "scripts/__init__.py",  # python -m scripts.atlas.atlas_db
        "scripts/storage/__init__.py",  # atlas_db imports scripts.storage.paths
        "scripts/storage/paths.py",  # atlas_db imports REGISTRY_ROOT
        "scripts/etymology/transliterate.py",  # generate_search_index loads this helper
        "scripts/audit/__init__.py",  # python -m scripts.audit.generate_daily_pool
        "scripts/audit/lexeme_filter.py",  # generate_search_index and daily_pool
        "scripts/audit/daily_cefr.py",  # generate_daily_pool imports it
        "registry/lexicon/synonym_pair_verdicts.yaml",  # atlas_db default input
        "registry/lexicon/curated_aliases.yaml",  # atlas_db default input
    )
    missing = [path for path in dependencies if not path_in_denominator(path, paths)]
    assert not missing, f"Frontend hydrate dependencies outside denominator: {missing}"
