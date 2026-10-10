"""Report the importer-closure test selection for a pre-push range, in shadow (#10033).

The pre-push gate records this next to its blocking verdict.  It never executes
or deselects a test; an unresolved dependency falls back to every component, as
``components.affected`` already does.  Measurement compares the recorded
selection with full-suite CI failures before any blocking use is considered.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from scripts.ci import components


def shadow_selection(paths: Sequence[str]) -> dict[str, object]:
    manifest = components.load_manifest()
    affected = components.affected(paths, manifest)
    selected: set[str] = set()
    for component in affected["components"]:
        selected.update(components.test_files(component, manifest))
    return {
        "components": affected["components"],
        "fallback_reasons": affected["fallback_reasons"],
        "changed_paths": affected["changed_paths"],
        "selected_tests": sorted(selected),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paths", nargs="*", default=[], help="repository-relative changed paths")
    arguments = parser.parse_args(argv)
    print(json.dumps(shadow_selection(arguments.paths), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
