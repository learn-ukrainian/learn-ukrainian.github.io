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

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]


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


# Processors that load a live ML model when invoked. Exercising them downloads
# the Stanza Ukrainian model, which is non-hermetic and flakes Stanza's md5
# check under parallel CI (`ValueError: md5 for .../uk/tokenize/iu.pt ...`).
# Their parametrizations are marked `slow` so the required pytest selection
# (`-m "not atlas_release and not slow"`) excludes them — keeping the required
# gate hermetic per the #2691 invariant — while every other processor's invariant
# check still runs. They continue to run in the slow/nightly path. See
# docs/bug-autopsies/stanza-model-md5-flake.md.
_MODEL_BACKED_PROCESSORS = {"pipeline.stress_annotator.annotate_stress"}


def _processor_fixture_params() -> list[pytest.param]:
    # Sort both axes so pytest-xdist test IDs are stable across workers;
    # sets/frozensets hash differently per-interpreter (#1461 lesson).
    params = []
    for processor_name in sorted(REGISTRY.keys()):
        marks = (pytest.mark.slow,) if processor_name in _MODEL_BACKED_PROCESSORS else ()
        for fixture in sorted(_ALL_FIXTURES, key=lambda f: f.id):
            params.append(
                pytest.param(
                    processor_name,
                    fixture,
                    id=f"{processor_name}[{fixture.id}]",
                    marks=marks,
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
