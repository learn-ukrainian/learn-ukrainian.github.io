"""Allow only CI's intentional missing ML wheels after uv pip check.

The CI lock is consistent, but the lean --no-deps install omits four ML wheels.
Keep this list exact by package name: a new diagnostic, a new requiring package
or a new missing dependency must fail here instead of failing later in many
pytest shards. Versions are not part of the key, so a routine bump of an
allowed package passes.
"""

from __future__ import annotations

import re
import subprocess
import sys

from packaging.utils import canonicalize_name

# (requiring package, missing dependency): the intentional omissions from the
# CI-filtered requirements-lock.txt. Only "which is not installed" diagnostics
# can match; a version conflict is never allowed.
_ALLOWED = {
    ("accelerate", "torch"),
    ("flagembedding", "torch"),
    ("peft", "torch"),
    ("sentence-transformers", "torch"),
    ("timm", "torch"),
    ("timm", "torchvision"),
    ("ukrainian-word-stress", "stanza"),
}

_MISSING = re.compile(r"^(\S+) \S+ requires (\S+), which is not installed\.$")


def _diagnostic_key(line: str) -> tuple[str, str] | None:
    if match := _MISSING.fullmatch(line):
        source, dependency = match.groups()
        return canonicalize_name(source), canonicalize_name(dependency)
    return None


def unexpected_diagnostics(output: str) -> list[str]:
    """Return every pip diagnostic that is not an exact filtered ML omission."""
    return [line for line in output.splitlines() if _diagnostic_key(line) not in _ALLOWED]


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(__doc__.strip())
        return 0
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
