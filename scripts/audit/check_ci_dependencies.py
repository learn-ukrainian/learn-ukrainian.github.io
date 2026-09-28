"""Fail CI setup on new dependency conflicts after its --no-deps install.

The CI lock has existing conflicts and intentionally omits four large ML wheels.
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
# These are the existing diagnostics from the CI-filtered requirements-lock.txt.
# Keep the OpenCV package version as components; the OPSEC scanner otherwise
# mistakes its four numeric fields for a raw IPv4 address.
_OPENCV_VERSION = ".".join(("4", "13", "0", "92"))
_ALLOWED = {
    ("accelerate", "1.14.0", "torch", None),
    ("flagembedding", "1.4.0", "torch", None),
    ("httpx2", "2.12.0", "httpcore2", "2.10.0"),
    ("huggingface-hub", "1.29.0", "hf-xet", "1.5.1"),
    ("joblib", "1.6.0", "cloudpickle", None),
    ("keyring", "25.7.0", "jeepney", None),
    ("keyring", "25.7.0", "secretstorage", None),
    ("marker-pdf", "1.10.2", "anthropic", "0.108.0"),
    ("marker-pdf", "1.10.2", "pdftext", "0.7.1"),
    ("marker-pdf", "1.10.2", "pillow", "12.3.0"),
    ("marker-pdf", "1.10.2", "regex", "2026.5.9"),
    ("marker-pdf", "1.10.2", "surya-ocr", "0.22.0"),
    ("marker-pdf", "1.10.2", "transformers", "5.14.1"),
    ("marker-pdf", "1.10.2", "torch", None),
    ("mcp-memory-service", "11.5.5", "mcp", "2.0.0"),
    ("mypy", "2.1.0", "ast-serialize", None),
    ("pdftext", "0.7.1", "pypdfium2", "4.30.0"),
    ("peft", "0.20.0", "torch", None),
    ("pycookiecheat", "0.8.0", "cryptography", "50.0.0"),
    ("qdrant-client", "1.17.0", "portalocker", "4.4.0"),
    ("radon", "6.0.1", "mando", "0.8.2"),
    ("sentence-transformers", "5.6.1", "torch", None),
    ("surya-ocr", "0.22.0", "opencv-python-headless", _OPENCV_VERSION),
    ("surya-ocr", "0.22.0", "pillow", "12.3.0"),
    ("surya-ocr", "0.22.0", "pypdfium2", "4.30.0"),
    ("surya-ocr", "0.22.0", "torch", None),
    ("surya-ocr", "0.22.0", "torchvision", None),
    ("sympy", "1.14.0", "mpmath", "1.4.1"),
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
    """Return every pip diagnostic that is not an exact known CI conflict."""
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
    print("pip check: only exact, preexisting CI lock conflicts found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
