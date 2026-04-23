"""Post-processor mutation-class invariant — EPIC #1451 Phase 4-C.

Structural defense against the #1448 bug class: silent base-character
mutation of content after the reviewer has scored. Every registered
post-review mutator must stay within its declared mutation class on every
fixture in the golden corpus.

Failure modes caught:
1. Structural — a post-review mutator was added to the pipeline without
   registering its class (``test_no_unregistered_post_processors`` /
   ``test_every_registered_processor_has_a_resolver``).
2. Behavioral — a registered mutator performs an out-of-class mutation on
   any fixture (``test_post_processor_stays_in_class``).

See ``scripts/build/post_processors/__init__.py`` for the class taxonomy.
Fixtures live in ``tests/fixtures/post_processor_mutation_corpus.yaml`` —
the Cyrillic-roundtrip corpus (#1461) is also parametrized into this
test because the #1448 class is specifically Cyrillic mutation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build.post_processors import REGISTRY, Violation, verify_mutation
from build.post_processors._migrations import get_processor_callable


class Fixture(NamedTuple):
    id: str
    text: str
    notes: str


def _load_corpus(path: Path) -> list[Fixture]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        Fixture(id=case["id"], text=case["text"], notes=case.get("notes", ""))
        for case in raw["cases"]
    ]


_POST_PROCESSOR_CORPUS = _load_corpus(
    REPO_ROOT / "tests" / "fixtures" / "post_processor_mutation_corpus.yaml"
)
_CYRILLIC_ROUNDTRIP_CORPUS = _load_corpus(
    REPO_ROOT / "tests" / "fixtures" / "cyrillic_roundtrip_corpus.yaml"
)
_ALL_FIXTURES: list[Fixture] = _POST_PROCESSOR_CORPUS + [
    # Prefix Cyrillic corpus IDs so xdist-stable sort order keeps them
    # distinct from post-processor fixtures.
    Fixture(id=f"cyrillic.{f.id}", text=f.text, notes=f.notes)
    for f in _CYRILLIC_ROUNDTRIP_CORPUS
]


def _processor_fixture_params() -> list[pytest.param]:
    # Sort both axes so pytest-xdist test IDs are stable across workers;
    # sets/frozensets hash differently per-interpreter (#1461 lesson).
    params = []
    for processor_name in sorted(REGISTRY.keys()):
        for fixture in sorted(_ALL_FIXTURES, key=lambda f: f.id):
            params.append(
                pytest.param(
                    processor_name,
                    fixture,
                    id=f"{processor_name}[{fixture.id}]",
                )
            )
    return params


@pytest.mark.parametrize(("processor_name", "fixture"), _processor_fixture_params())
def test_post_processor_stays_in_class(
    processor_name: str, fixture: Fixture
) -> None:
    """Every post-review mutator stays within its declared class on every fixture."""
    invoke = get_processor_callable(processor_name)
    try:
        after = invoke(fixture.text)
    except Exception as exc:
        raise AssertionError(
            f"Processor {processor_name} crashed on fixture {fixture.id!r}: "
            f"{exc!r}\n  notes: {fixture.notes}"
        ) from exc

    violations: list[Violation] = verify_mutation(
        processor_name, fixture.text, after
    )
    if violations:
        lines = [
            f"Processor {processor_name} left its declared class on "
            f"fixture {fixture.id!r}.",
            f"  notes: {fixture.notes}",
            f"  input : {fixture.text!r}",
            f"  output: {after!r}",
        ]
        for v in violations:
            lines.append(f"  → {v.kind}: {v.note}")
            lines.append(f"    before: {v.before_fragment!r}")
            lines.append(f"    after : {v.after_fragment!r}")
        pytest.fail("\n".join(lines))


def test_every_registered_processor_has_a_resolver() -> None:
    """Structural: every name in REGISTRY must resolve to a callable.

    Prevents a dangling registration that names a processor with no
    corresponding ``get_processor_callable`` entry.
    """
    for processor_name in sorted(REGISTRY.keys()):
        invoke = get_processor_callable(processor_name)
        assert callable(invoke), (
            f"Processor {processor_name!r} is registered but has no callable "
            f"resolver — add an entry to ``_migrations.get_processor_callable``."
        )


# Known post-review mutators — any NEW function matching these markers must
# appear in REGISTRY. Extend this list whenever the pipeline grows a new
# post-review mutator; the test forces an explicit class declaration.
_EXPECTED_REGISTRATIONS = {
    "pipeline.stress_annotator.annotate_stress",
    "build.v6_build._post_process_content",
}


def test_registry_contains_all_known_post_review_mutators() -> None:
    """Structural: drift guard on the expected-registration set.

    If a post-review mutator is removed from the pipeline, remove it from
    ``_EXPECTED_REGISTRATIONS`` in this test AND from ``_migrations``.
    If a new post-review mutator is added, register it in
    ``_migrations.register_existing`` AND add it to this set.
    """
    missing = _EXPECTED_REGISTRATIONS - set(REGISTRY.keys())
    assert not missing, (
        f"Expected post-review mutators are not registered: {sorted(missing)!r}. "
        f"Add registrations in scripts/build/post_processors/_migrations.py."
    )


def test_no_unregistered_post_processor_files() -> None:
    """Structural: any module under ``scripts/build/post_processors/`` must
    either be the registry itself, a helper (prefixed with ``_``), or
    register its processor at import time.

    Catches the shape-error of "added a new processor file but forgot to
    register it".
    """
    pkg_dir = SCRIPTS_DIR / "build" / "post_processors"
    unregistered: list[str] = []
    for module_file in pkg_dir.glob("*.py"):
        if module_file.name == "__init__.py" or module_file.name.startswith("_"):
            continue
        text = module_file.read_text(encoding="utf-8")
        if "register_post_processor(" not in text:
            unregistered.append(module_file.name)
    assert not unregistered, (
        f"Post-processor module(s) do not call register_post_processor(): "
        f"{unregistered!r}"
    )
