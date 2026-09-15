"""Anti-leak guard for baked host checkout / venv paths in the public tree.

Detector needles stay in dedicated tests and OPSEC scanners. Production
docs, scripts, curriculum (including `_archive`), and operator examples
must not bake a host checkout or interpreter path.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Reject-sample prefixes. Do not copy these into public files.
_BAKED_CHECKOUT_PREFIXES = (
    "/Users/krisztiankoos/projects/learn-ukrainian",
    "/Users/your-user/projects/learn-ukrainian",
    "/Users/REPLACE/projects/learn-ukrainian",
    "/Users/k/projects/learn-ukrainian",
    "/Users/me/projects/learn-ukrainian",
    "/Users/you/projects/learn-ukrainian",
)

_TEXT_SUFFIXES = {
    ".md",
    ".mdx",
    ".txt",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".html",
    ".htm",
    ".xml",
    ".plist",
    ".sh",
    ".toml",
    ".rst",
    ".css",
}

_PUBLIC_TREES = (
    Path("docs"),
    Path("scripts"),
    Path("curriculum"),
    Path("audit"),
    Path("archive"),
    Path("agents_extensions"),
    Path("batch_state"),
    Path("orchestration"),
    Path("plans"),
    Path("wiki"),
)

_SKIP_NAME_PARTS = (
    "dialect_historical",
    "v5_dialect_protection",
)


def _iter_public_files() -> list[Path]:
    files: list[Path] = []
    for rel in _PUBLIC_TREES:
        path = ROOT / rel
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for candidate in path.rglob("*"):
            if not candidate.is_file():
                continue
            name = str(candidate.relative_to(ROOT))
            if any(part in name for part in _SKIP_NAME_PARTS):
                continue
            if candidate.suffix.lower() not in _TEXT_SUFFIXES:
                continue
            files.append(candidate)
    return files


def test_public_tree_scan_includes_bio_research_dossiers() -> None:
    files = [str(path.relative_to(ROOT)) for path in _iter_public_files()]
    bio = [name for name in files if name.startswith("docs/research/bio/")]
    assert bio, "docs/research/bio/ must be scanned; do not skip that tree"


def test_public_tree_has_no_baked_host_checkout_or_venv() -> None:
    files = _iter_public_files()
    assert files, "expected public-tree files to scan"
    leaked: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(ROOT))
        for prefix in _BAKED_CHECKOUT_PREFIXES:
            if prefix in text:
                leaked.append(f"{rel} contains {prefix}")
    assert not leaked, "baked host run-root still present:\n" + "\n".join(leaked)
