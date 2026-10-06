"""Deterministic build pins and the deliberately narrow public-safe projection."""

import re
from pathlib import Path

from .contract import canonical, digest
from .errors import require


def code_pins() -> dict:
    package = Path(__file__).parent
    files = {p.name: digest(p.read_bytes()) for p in sorted(package.glob("*.py"))}
    root = next(p for p in package.parents if (p / ".git").exists())
    git = root / ".git"
    if git.is_file():
        value = git.read_text().strip()
        require(value.startswith("gitdir: "), "code_identity")
        git = (root / value[8:]).resolve()
    head = (git / "HEAD").read_text().strip()
    if head.startswith("ref: "):
        ref = head[5:]
        common = git
        if (git / "commondir").exists():
            common = (git / (git / "commondir").read_text().strip()).resolve()
        if (common / ref).exists():
            head = (common / ref).read_text().strip()
        else:
            matches = [
                line.split()[0]
                for line in (common / "packed-refs").read_text().splitlines()
                if line.endswith(" " + ref)
            ]
            require(len(matches) == 1, "code_identity")
            head = matches[0]
    require(bool(re.fullmatch(r"[0-9a-f]{40}", head)), "code_identity")
    return {"code_sha": head, "parser_sha256": digest(canonical(files)), "files": files}


PRIVATE_FIELDS = frozenset({"hashes", "counts", "versions", "code_sha", "reason_code_tallies"})


def private_manifest(data: dict) -> dict:
    """Accept only this schema; do not recursively strip unknown fields."""
    require(set(data) == PRIVATE_FIELDS, "private_manifest_field")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", data["code_sha"])), "private_manifest_string")
    require(
        set(data["hashes"]) <= {"build", "register", "catalog", "parser", "candidates", "spec"},
        "private_manifest_field",
    )
    require(
        all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) for v in data["hashes"].values()),
        "private_manifest_string",
    )
    require(set(data["versions"]) <= {"record", "framework", "catalog"}, "private_manifest_field")
    require(
        all(
            isinstance(v, str) and re.fullmatch(r"(?:omd-review-record\.v1|[0-9]+(?:\.[0-9]+)*(?:-draft)?)", v)
            for v in data["versions"].values()
        ),
        "private_manifest_string",
    )
    require(
        all(
            re.fullmatch(r"C[1-79]\.(?:accepted|rejected|withheld|excluded|counted)", k) and type(v) is int and v >= 0
            for k, v in data["counts"].items()
        ),
        "private_manifest_field",
    )
    require(
        all(
            re.fullmatch(r"[a-z][a-z0-9_]{0,63}", k) and type(v) is int and v >= 0
            for k, v in data["reason_code_tallies"].items()
        ),
        "private_manifest_field",
    )
    require(not re.search(r"[\u0400-\u052f]", canonical(data).decode()), "private_manifest_cyrillic")
    return data
