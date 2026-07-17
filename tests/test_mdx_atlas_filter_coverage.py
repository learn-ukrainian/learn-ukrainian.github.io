"""Guards for MDX drift/parity + atlas path-filter coverage (#5354).

Sibling of ``tests/test_lesson_schema_filter_coverage.py`` (#5352): conditional
CI gates must trigger on every path the gated check actually consumes.
Otherwise drift/staleness accumulates silently on main and reds an unrelated
ci.yml-touching PR later (class: #3873 / #4888 / #4936 / #5351).

1. ``frontend`` must cover MDX generator entry + package (+ generator deps
   enumerated by ``check_mdx_source_parity``), else generator-only PRs skip
   ``mdx-generation-drift`` / ``mdx-source-parity``.
2. ``atlas`` must cover the manifest pointer (``hashFiles`` +
   ``load_manifest``) and the static practice asset paths read by
   ``check_static_practice_assets``, else pointer-only / asset-only edits
   skip ``atlas-freshness``.

Expectations are derived FROM the gate scripts / workflow expressions, so a
new input without a matching glob fails pytest.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

sys.path.insert(0, str(_REPO_ROOT))
from scripts.audit import check_mdx_source_parity as mdx_parity
from scripts.audit import check_static_practice_assets as practice_assets
from scripts.lexicon import manifest_io


def _filter_globs(name: str) -> list[str]:
    workflow = yaml.safe_load(_CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["changes"]["steps"]
    filter_step = next(s for s in steps if s.get("id") == "filter")
    filters = yaml.safe_load(filter_step["with"]["filters"])
    return filters[name]


def _covered(rel_path: str, globs: list[str]) -> bool:
    # fnmatch's ``*`` crosses ``/`` — intentionally permissive: we assert
    # representative concrete paths are matched (coverage), never exclusion.
    return any(fnmatch.fnmatch(rel_path, g) for g in globs)


def _assert_filter_covers(filter_name: str, inputs: list[Path], *, hint: str) -> None:
    globs = _filter_globs(filter_name)
    assert globs, f"{filter_name} filter missing from ci.yml"
    uncovered = [
        str(p.relative_to(_REPO_ROOT))
        for p in inputs
        if not _covered(str(p.relative_to(_REPO_ROOT)), globs)
    ]
    assert not uncovered, (
        f"{filter_name} path filter does not cover gate inputs {uncovered}; "
        f"{hint} Extend the {filter_name} globs in .github/workflows/ci.yml."
    )


def _mdx_generator_inputs() -> list[Path]:
    """Paths whose edits must fire the MDX drift/parity gates.

    Derived from ``check_mdx_source_parity`` (generator change detection) and
    ``check_mdx_generation_drift`` (subprocess to ``scripts/generate_mdx.py``).
    """
    package_files = sorted(mdx_parity.GENERATOR_PACKAGE.rglob("*.py"))
    assert package_files, "generate_mdx package empty or moved?"
    inputs = [
        mdx_parity.GENERATOR_ENTRYPOINT,
        package_files[0],  # representative proves scripts/generate_mdx/**
        *sorted(mdx_parity.GENERATOR_DEPENDENCIES),
    ]
    return inputs


def _atlas_freshness_inputs() -> list[Path]:
    """Paths consumed by atlas-freshness (workflow + static practice check).

    - ``lexicon-manifest.pointer.json``: ``hashFiles(...)`` cache key and
      ``manifest_io.load_manifest`` / ``_load_pointer``.
    - practice asset defaults from ``check_static_practice_assets``.
    """
    workflow_text = _CI_WORKFLOW.read_text(encoding="utf-8")
    # Confirm the workflow still hashes the pointer (regression if expression moves).
    assert "lexicon-manifest.pointer.json" in workflow_text, (
        "ci.yml no longer hashFiles the atlas pointer — update this test"
    )
    pointer = manifest_io.DEFAULT_POINTER
    assert pointer.is_relative_to(_REPO_ROOT)

    practice_dir = _REPO_ROOT / practice_assets.DEFAULT_PRACTICE_DIR
    # One representative file under public/lexicon proves the directory glob.
    practice_files = sorted(p for p in practice_dir.rglob("*.json") if p.is_file())[:1]
    assert practice_files, (
        f"no practice assets under {practice_assets.DEFAULT_PRACTICE_DIR} — path moved?"
    )

    return [
        pointer,
        _REPO_ROOT / practice_assets.DEFAULT_DAILY_POOL,
        _REPO_ROOT / practice_assets.DEFAULT_REVIEWED_SOURCES,
        practice_files[0],
    ]


def test_frontend_filter_covers_mdx_generator_inputs() -> None:
    _assert_filter_covers(
        "frontend",
        _mdx_generator_inputs(),
        hint=(
            "mdx-generation-drift / mdx-source-parity will not fire on "
            "generator-only changes."
        ),
    )


def test_atlas_filter_covers_freshness_inputs() -> None:
    _assert_filter_covers(
        "atlas",
        _atlas_freshness_inputs(),
        hint="atlas-freshness will not fire when those inputs change.",
    )


def test_atlas_freshness_hashfiles_includes_pointer() -> None:
    """Workflow expression must still key the cache on the pointer file."""
    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    # Match the dorny/actions expression used by atlas-freshness (and peers).
    pattern = re.compile(
        r"hashFiles\(\s*['\"]site/src/data/lexicon-manifest\.pointer\.json['\"]\s*\)"
    )
    assert pattern.search(text), (
        "ci.yml atlas cache key no longer hashFiles "
        "site/src/data/lexicon-manifest.pointer.json"
    )
