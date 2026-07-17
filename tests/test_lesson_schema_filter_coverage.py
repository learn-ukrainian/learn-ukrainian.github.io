"""Guards for the Lesson Schema Drift gate (#5351).

1. The CI ``lesson_schema`` path filter must cover every generator input,
   otherwise the drift gate never fires on the changes that stale the schema:
   drift accumulates silently on main and the gate reds unrelated
   ci.yml-touching PRs later (same filter-gap class as #3873 / #4888 / #4936).
2. The committed schema's input fingerprints must match a recomputation, so
   any scripts/tests-touching PR (which runs pytest) also surfaces staleness.
   (A components-only PR does not run pytest — the widened ``lesson_schema``
   filter + drift gate are the load-bearing guard for that path.)

Both tests derive their expectations FROM the generator module, so moving or
adding an input without updating the filter fails pytest.
"""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

sys.path.insert(0, str(_REPO_ROOT))
from scripts.build import generate_lesson_schema as gen


def _lesson_schema_globs() -> list[str]:
    workflow = yaml.safe_load(_CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["changes"]["steps"]
    filter_step = next(s for s in steps if s.get("id") == "filter")
    filters = yaml.safe_load(filter_step["with"]["filters"])
    return filters["lesson_schema"]


def _covered(rel_path: str, globs: list[str]) -> bool:
    # fnmatch's ``*`` crosses ``/`` — intentionally permissive: we assert
    # representative concrete paths are matched (coverage), never exclusion.
    return any(fnmatch.fnmatch(rel_path, g) for g in globs)


def _generator_inputs() -> list[Path]:
    inputs = [
        gen.CONFIG_TABLES_PATH,
        gen.LESSON_CONTRACT_PATH,
        gen.EXTRACTOR_PATH,
        gen.OUTPUT_PATH,
        Path(gen.__file__),
    ]
    # One representative component file per suffix proves the directory glob.
    components = sorted(gen.COMPONENTS_DIR.rglob("*.tsx"))[:1] + sorted(
        gen.COMPONENTS_DIR.rglob("*.astro")
    )[:1]
    assert components, "no components found — generator input dir moved?"
    return inputs + components


def test_lesson_schema_filter_covers_all_generator_inputs() -> None:
    globs = _lesson_schema_globs()
    assert globs, "lesson_schema filter missing from ci.yml"
    uncovered = [
        str(p.relative_to(_REPO_ROOT))
        for p in _generator_inputs()
        if not _covered(str(p.relative_to(_REPO_ROOT)), globs)
    ]
    assert not uncovered, (
        "lesson_schema path filter does not cover generator inputs "
        f"{uncovered}; the drift gate will not fire when they change. "
        "Extend the lesson_schema globs in .github/workflows/ci.yml."
    )


def test_committed_lesson_schema_fingerprints_are_fresh() -> None:
    """Recompute the generator's input hashes (pure Python — no node
    extraction) and compare with the committed ``generated_from`` block.
    Mismatch == the exact drift the CI gate reds on (#5351)."""
    committed = yaml.safe_load(gen.OUTPUT_PATH.read_text(encoding="utf-8"))
    generated_from = committed["generated_from"]
    expected = {
        "components_sha256": gen._hash_files(gen.discover_components(gen.COMPONENTS_DIR)),
        "config_tables_sha256": gen._hash_file(gen.CONFIG_TABLES_PATH),
        "lesson_contract_sha256": gen._hash_file(gen.LESSON_CONTRACT_PATH),
    }
    stale = {
        key: (generated_from.get(key), value)
        for key, value in expected.items()
        if generated_from.get(key) != value
    }
    assert not stale, (
        f"docs/lesson-schema.yaml is stale vs its inputs: {stale}. "
        "Run: .venv/bin/python scripts/build/generate_lesson_schema.py"
    )
