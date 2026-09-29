"""Allow only CI's intentional missing ML wheels after uv pip check.

The CI lock is consistent, but the lean --no-deps install omits four ML wheels.
Keep this list exact: a new diagnostic, package version, or dependency version
must fail here instead of failing later in many pytest shards.
"""

from __future__ import annotations

import re
import subprocess
import sys

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

# (requiring package, its version, dependency, installed version or None)
# These are the intentional omissions from the CI-filtered requirements-lock.txt.
_ALLOWED = {
    ("accelerate", "1.14.0", "torch", None),
    ("flagembedding", "1.4.0", "torch", None),
    ("peft", "0.20.0", "torch", None),
    ("sentence-transformers", "5.6.1", "torch", None),
    ("timm", "1.0.27", "torch", None),
    ("timm", "1.0.27", "torchvision", None),
    ("ukrainian-word-stress", "2.1.0", "stanza", None),
}

_MISSING = re.compile(r"^(\S+) (\S+) requires (\S+), which is not installed\.$")
_CONFLICT = re.compile(
    r"^(\S+) (\S+) has requirement (.+), but you have (\S+) (\S+)\.$"
)


def _diagnostic_key(line: str) -> tuple[str, str, str, str | None] | None:
    if match := _MISSING.fullmatch(line):
        source, version, dependency = match.groups()
        return canonicalize_name(source), version, canonicalize_name(dependency), None
    if match := _CONFLICT.fullmatch(line):
        source, version, requirement, dependency, installed = match.groups()
        try:
            required_name = canonicalize_name(Requirement(requirement).name)
        except ValueError:
            return None
        if required_name != canonicalize_name(dependency):
            return None
        return canonicalize_name(source), version, required_name, installed
    return None


def unexpected_diagnostics(output: str) -> list[str]:
    """Return every pip diagnostic that is not an exact filtered ML omission."""
    return [line for line in output.splitlines() if _diagnostic_key(line) not in _ALLOWED]


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode == 0:
        print(result.stdout.strip())
        return 0
    unexpected = unexpected_diagnostics(result.stdout)
    if result.stderr.strip():
        unexpected.extend(result.stderr.splitlines())
    if unexpected or result.returncode != 1 or not result.stdout.strip():
        print("CI dependency check failed on new diagnostics:", file=sys.stderr)
        for line in unexpected:
            print(line, file=sys.stderr)
        return 1
    print("pip check: only exact, intentional CI ML omissions found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
