"""Check rendered reviewer prompt for contract violations (#8430 Part R2 item 1).

Validates:
- No v1 path references (curriculum/l2-uk-en/a1/, plans/)
- No other module's slug
- No writer prompt or writer self-assessment leakage
- No earlier edition of the lesson (except re-review's diff and previous findings)
- No unresolved Jinja placeholders ({%, %}, {{, }}, TODO, : None)
- Every file read was a pin the manifest names and its sha256 matched

Pins are found the way the engine records them (``pinned_entries``): any object with a
``path`` and a ``sha256`` anywhere in the manifest. The check reads only pinned files;
it derives no path from another path and reads no file the manifest does not name.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh.manifest import pinned_entries

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = Path(__file__).resolve().parent

FORBIDDEN_V1_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"curriculum/l2-uk-en/(?:[a-c][1-2]|[a-z0-9]+)-v1/"),
    re.compile(r"curriculum/l2-uk-en/[a-c][1-2]/"),
    re.compile(r"curriculum/l2-uk-en/plans\b"),
    re.compile(r"\b(?:[a-c][1-2]|[a-z][0-9])-v1/"),
    re.compile(r"(?:^|[\s/])-v1/"),
    re.compile(r"(?<!lesson-)plans/(?:[a-c][1-2]|[a-z0-9]+)/"),
    re.compile(r"(?<!lesson-)plans/"),
    re.compile(r"lesson-plans/[^/\s]+-v1(?:/|\b)"),
)

WRITER_LEAKAGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:lesson|recap|draft)?\s*writer prompt\b", re.IGNORECASE),
    re.compile(r"\bprompt for (?:the\s+)?(?:writer|author)\b", re.IGNORECASE),
    re.compile(r"\byou are (?:the|a)\s+(?:lesson\s+|recap\s+)?(?:writer|author)\b", re.IGNORECASE),
    re.compile(r"\bas (?:the|a)\s+(?:lesson\s+|recap\s+)?(?:writer|author)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:writer|author)(?:'s)?\s+(?:prompt|instruction|direction|guidance|notes?|reasoning|reflection|assessment|self-assessment|critique|evaluation)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:instructions?|directions?|guidance|notes?)\s+for\s+(?:the\s+)?(?:writer|author)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwriter\s+(?:direction|guidance|task|role|persona)\b", re.IGNORECASE),
    re.compile(r"\blesson-draft-v1\b"),
    re.compile(r"\bself[-_\s]*(?:assessment|evaluation|critique|check|reflection)\b", re.IGNORECASE),
    re.compile(r"\bwriter_assessment\b", re.IGNORECASE),
    re.compile(r"\bnotes?\s+to\s+(?:the\s+)?reviewer\b", re.IGNORECASE),
)

EARLIER_EDITION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bearlier edition\b", re.IGNORECASE),
    re.compile(r"\bprevious edition\b", re.IGNORECASE),
    re.compile(r"\bearlier draft\b", re.IGNORECASE),
    re.compile(r"\bprevious draft\b", re.IGNORECASE),
    re.compile(r"\bdiff from previous attempt\b", re.IGNORECASE),
    re.compile(r"\bprevious findings\b", re.IGNORECASE),
    re.compile(r"\bearlier\s+(?:full\s+)?lesson\s+bytes\b", re.IGNORECASE),
    re.compile(r"\bearlier\s+(?:full\s+)?edition\s+bytes\b", re.IGNORECASE),
    re.compile(r"\bprevious\s+(?:full\s+)?lesson\s+bytes\b", re.IGNORECASE),
)

REREVIEW_FULL_EDITION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bearlier edition of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bprevious edition of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bfull text of previous edition\b", re.IGNORECASE),
    re.compile(r"\bearlier draft of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bprevious draft of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bearlier\s+(?:full\s+)?lesson\s+bytes\b", re.IGNORECASE),
)

PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "<TODO>",
    "[TODO]",
    "TODO:",
    "<MISSING>",
    "__PLACEHOLDER__",
)


@dataclass(frozen=True)
class RenderedPromptCheckResult:
    passed: bool
    errors: list[str]
    prompt_sha256: str
    files_read: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "prompt_sha256": self.prompt_sha256,
            "files_read": list(self.files_read),
        }


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _collect_allowed_manifest_paths(manifest: dict[str, Any], repo_root: Path) -> dict[Path, str]:
    """Every pinned file, by resolved path, with the sha256 the manifest records."""
    root = repo_root.resolve()
    return {(root / entry["path"]).resolve(): str(entry["sha256"]) for _, entry in pinned_entries(manifest)}


def _lock_first_token(path: Path) -> str:
    text = path.read_text(encoding="ascii").strip()
    return text.split()[0] if text else ""


def _verify_manifest_inputs(manifest: dict[str, Any], repo_root: Path, errors: list[str]) -> None:
    """Every pin exists inside the repository and hashes to its recorded sha256; each lock agrees with its data pin."""
    root = repo_root.resolve()
    pins = dict(pinned_entries(manifest))

    for location, entry in pins.items():
        p = (root / entry["path"]).resolve()
        if not p.is_relative_to(root):
            errors.append(f"unauthorized_file_read: pin {location} escapes the repository: {entry['path']}")
        elif not p.is_file():
            errors.append(f"input_missing: {entry['path']} does not exist")
        else:
            actual = compute_sha256(p.read_bytes())
            if actual != str(entry["sha256"]):
                errors.append(f"input_hash_mismatch: {entry['path']} expected {entry['sha256']}, actual {actual}")

    for data, lock in (("inputs.pack", "inputs.pack_lock"), ("inputs.words", "inputs.words_lock")):
        if data not in pins or lock not in pins:
            continue
        lock_path = (root / pins[lock]["path"]).resolve()
        if lock_path.is_file() and lock_path.is_relative_to(root):
            recorded = _lock_first_token(lock_path)
            if recorded != pins[data]["sha256"]:
                errors.append(
                    f"input_hash_mismatch: {pins[data]['path']} pinned at {pins[data]['sha256']}, "
                    f"its lock {pins[lock]['path']} records {recorded}"
                )


TAXONOMY_EXEMPT_WORDS: frozenset[str] = frozenset(
    {"euphony", "register", "recap", "review", "comparison", "language", "grammar"}
)


def _is_taxonomy_boilerplate_line(line: str) -> bool:
    line_lower = line.lower()
    return any(
        marker in line_lower
        for marker in (
            "sub_dimension:",
            "register, euphony, stress",
            "russianism | surzhyk",
            "`register` and `euphony`",
            "register and euphony",
            "dimension:",
            "taxonomy:",
            "checks:",
            "review kind",
            "lesson review",
            "plan review",
        )
    )


#: A module locator: the level directory of a plan, evidence pack, scope sidecar or built page, then the slug.
MODULE_LOCATOR = re.compile(
    r"(?:lesson-plans|_scope|evidence|site/src/content/docs)/(?:[a-z0-9]+-)?[a-z0-9]+/(?P<slug>[A-Za-z0-9][A-Za-z0-9-]*)"
)


def _pinned_arc_positions(manifest_doc: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    """The positions of the pinned arc (``inputs.arc``); empty when the manifest pins none."""
    entry = dict(pinned_entries(manifest_doc)).get("inputs.arc")
    if entry is None:
        return []
    arc_path = (repo_root / entry["path"]).resolve()
    if not arc_path.is_file() or not arc_path.is_relative_to(repo_root):
        return []
    try:
        arc = yaml.safe_load(arc_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return []
    positions = arc.get("positions", []) if isinstance(arc, dict) else []
    return [item for item in positions if isinstance(item, dict)]


def _derive_foreign_slugs(
    manifest_doc: dict[str, Any],
    repo_root: Path,
    other_slugs: set[str] | list[str] | None = None,
    rendered_prompt: str = "",
) -> set[str]:
    """Foreign module slugs from what the manifest pins, the prompt's own module locators, and the caller.

    Three sources, none of them a file the manifest does not name: the positions of the pinned
    arc (plan reviews), any module locator in the rendered text whose slug is not this module's,
    and ``other_slugs`` supplied by the driver.
    """
    current_slug = manifest_doc.get("slug")
    slugs: set[str] = set(other_slugs or [])
    slugs.update(str(pos["slug"]) for pos in _pinned_arc_positions(manifest_doc, repo_root) if pos.get("slug"))
    slugs.update(match.group("slug") for match in MODULE_LOCATOR.finditer(rendered_prompt))
    if current_slug:
        slugs.discard(current_slug)
    return slugs


def check_prompt(
    rendered_prompt: str,
    manifest_source: Path | str | dict[str, Any],
    template_name: str | None = None,
    *,
    repo_root: Path | None = None,
    files_read: list[Path | str] | None = None,
    other_slugs: set[str] | list[str] | None = None,
    earlier_editions: list[Path | str] | None = None,
    prompts_dir: Path | None = None,
) -> RenderedPromptCheckResult:
    """Validate a rendered reviewer prompt against all contract requirements."""
    root = (repo_root or REPO_ROOT).resolve()
    errors: list[str] = []

    if isinstance(manifest_source, (str, Path)):
        mpath = (root / manifest_source).resolve() if not Path(manifest_source).is_absolute() else Path(manifest_source)
        manifest_doc = yaml.safe_load(mpath.read_text(encoding="utf-8"))
    elif isinstance(manifest_source, dict):
        manifest_doc = manifest_source
    else:
        manifest_doc = {}

    # 1. Verify manifest inputs and hashes
    _verify_manifest_inputs(manifest_doc, root, errors)

    # 2. Verify files read
    if files_read is not None:
        allowed = _collect_allowed_manifest_paths(manifest_doc, root)
        for f in files_read:
            fp = (root / f).resolve() if not Path(f).is_absolute() else Path(f)
            if fp not in allowed:
                errors.append(f"unauthorized_file_read: file {fp.as_posix()} was read but is not in manifest inputs")
            else:
                if not fp.is_file():
                    errors.append(f"input_missing: file {fp.as_posix()} was read but does not exist")
                else:
                    actual = compute_sha256(fp.read_bytes())
                    expected = allowed[fp]
                    if actual != expected:
                        errors.append(
                            f"input_hash_mismatch: file {fp.as_posix()} hash mismatch: expected {expected}, actual {actual}"
                        )

    # 3. Check for forbidden v1 paths
    for pat in FORBIDDEN_V1_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(
                f"forbidden_v1_path: prompt contains v1 path reference matching {pat.pattern!r}: {match.group(0)!r}"
            )

    # 4. Foreign module detection (the pinned arc, the prompt's own module locators, the driver's list)
    allowed_neighbour_slugs: set[str] = set()
    pos_num = manifest_doc.get("position")
    if manifest_doc.get("kind") == "plan" and pos_num is not None:
        for pos in _pinned_arc_positions(manifest_doc, root):
            p_num = pos.get("position")
            if isinstance(p_num, int) and abs(p_num - int(pos_num)) <= 1 and pos.get("slug"):
                allowed_neighbour_slugs.add(str(pos["slug"]))

    foreign_slugs = _derive_foreign_slugs(manifest_doc, root, other_slugs, rendered_prompt)
    prompt_lines = rendered_prompt.splitlines()

    for s in foreign_slugs:
        if not s:
            continue
        if manifest_doc.get("kind") == "plan" and s in allowed_neighbour_slugs:
            # Neighbour position references are permitted in plan review context
            continue
        if s in TAXONOMY_EXEMPT_WORDS:
            # Check if it appears outside taxonomy boilerplate lines
            violating_lines = [
                line
                for line in prompt_lines
                if re.search(rf"\b{re.escape(s)}\b", line) and not _is_taxonomy_boilerplate_line(line)
            ]
            if violating_lines:
                errors.append(f"forbidden_module_slug: found other module slug {s!r} in rendered prompt")
        else:
            if re.search(rf"\b{re.escape(s)}\b", rendered_prompt):
                errors.append(f"forbidden_module_slug: found other module slug {s!r} in rendered prompt")

    # 5. Check for writer prompt or self-assessment leakage
    for pat in WRITER_LEAKAGE_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(f"writer_prompt_or_assessment: prompt contains forbidden writer text: {match.group(0)!r}")

    # 6. Check for earlier edition of the lesson
    t_name = template_name or ""
    is_rereview = "rereview" in t_name or bool(manifest_doc.get("previous_attempt"))

    pinned_paths = _collect_allowed_manifest_paths(manifest_doc, root)
    pinned_texts = [
        path.read_text(encoding="utf-8", errors="replace")
        for path, digest in pinned_paths.items()
        if path.is_file() and compute_sha256(path.read_bytes()) == digest
    ]

    # Earlier editions come from the driver (the content-addressed snapshot of the lesson the previous attempt saw);
    # the check names no path of its own. Text that a pinned file also holds (the current lesson, the diff, the
    # previous findings) is manifested, so it is never a leak.
    for item in earlier_editions or []:
        candidate = (root / item).resolve() if not Path(item).is_absolute() else Path(item)
        if candidate.is_file():
            earlier_bytes = candidate.read_bytes()
            label = candidate.name
        else:
            earlier_bytes = str(item).encode("utf-8")
            label = "supplied text"
        earlier_text = earlier_bytes.decode("utf-8", errors="replace").strip()
        if not earlier_text or any(earlier_text in text for text in pinned_texts):
            continue
        earlier_sha = compute_sha256(earlier_bytes)
        if earlier_sha in rendered_prompt:
            errors.append(
                f"earlier_edition: prompt contains unmanifested earlier edition hash {earlier_sha} from {label}"
            )
        if len(earlier_text) >= 10 and earlier_text in rendered_prompt:
            errors.append(f"earlier_edition: prompt contains unmanifested earlier edition bytes from {label}")

    if is_rereview:
        for pat in REREVIEW_FULL_EDITION_PATTERNS:
            match = pat.search(rendered_prompt)
            if match:
                errors.append(
                    f"earlier_edition: prompt contains forbidden full earlier edition text: {match.group(0)!r}"
                )
    else:
        for pat in EARLIER_EDITION_PATTERNS:
            match = pat.search(rendered_prompt)
            if match:
                errors.append(
                    f"earlier_edition: prompt contains earlier edition or previous attempt text: {match.group(0)!r}"
                )

    # 7. Check for unresolved Jinja placeholders
    if "{%" in rendered_prompt or "%}" in rendered_prompt:
        errors.append("unresolved_placeholder: unrendered Jinja statement tag ({% or %}) found in prompt")

    if "{{" in rendered_prompt or "}}" in rendered_prompt:
        errors.append("unresolved_placeholder: unrendered Jinja expression tag ({{ or }}) found in prompt")

    for marker in PLACEHOLDER_MARKERS:
        if marker in rendered_prompt:
            errors.append(f"unresolved_placeholder: placeholder token {marker!r} found in prompt")

    for line in rendered_prompt.splitlines():
        if ": None" in line and not line.strip().startswith("#"):
            errors.append(f"unresolved_placeholder: template variable rendered as 'None': {line.strip()!r}")

    prompt_sha256 = compute_sha256(rendered_prompt.encode("utf-8"))
    files_read_str = [str(f) for f in (files_read or [])]

    return RenderedPromptCheckResult(
        passed=(len(errors) == 0),
        errors=errors,
        prompt_sha256=prompt_sha256,
        files_read=files_read_str,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check rendered reviewer prompt.")
    parser.add_argument("prompt_file", help="Path to rendered prompt markdown file")
    parser.add_argument("--manifest", "-m", required=True, help="Path to attempt manifest YAML")
    parser.add_argument("--template", "-t", default=None, help="Template name")
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    parser.add_argument("--prompts-dir", default=None, help="Prompts directory path (test only)")
    parser.add_argument(
        "--files-read",
        default=None,
        help="Path to files_read sidecar (default: <prompt_file>.files_read.json)",
    )
    parser.add_argument(
        "--earlier-edition",
        action="append",
        default=[],
        help="Path to an earlier edition of the lesson the prompt must not carry (repeatable)",
    )
    parser.add_argument(
        "--other-slug", action="append", default=[], help="Another module's slug the prompt must not name (repeatable)"
    )
    args = parser.parse_args(argv)

    root = Path(args.repo_root) if args.repo_root else REPO_ROOT
    prompt_path = (
        (root / args.prompt_file).resolve() if not Path(args.prompt_file).is_absolute() else Path(args.prompt_file)
    )
    if not prompt_path.is_file():
        print(f"FAIL: Prompt file does not exist: {prompt_path}")
        return 1
    prompt_text = prompt_path.read_text(encoding="utf-8")

    # The CLI must read the files_read sidecar and must not run without it
    files_read_path = None
    if args.files_read:
        files_read_path = (
            (root / args.files_read).resolve() if not Path(args.files_read).is_absolute() else Path(args.files_read)
        )
    else:
        for cand_name in (f"{prompt_path.name}.files_read.json", f"{prompt_path.name}.files_read"):
            cand = prompt_path.with_name(cand_name)
            if cand.is_file():
                files_read_path = cand
                break

    if files_read_path is None or not files_read_path.is_file():
        print(f"FAIL: Missing required files_read sidecar for {prompt_path.name}: CLI must not run without it")
        return 1

    try:
        files_read_content = json.loads(files_read_path.read_text(encoding="utf-8"))
        if not isinstance(files_read_content, list):
            print(f"FAIL: files_read sidecar {files_read_path} is not a JSON list")
            return 1
        files_read_list = [root / p for p in files_read_content]
    except Exception as exc:
        print(f"FAIL: Unable to read files_read sidecar {files_read_path}: {exc}")
        return 1

    result = check_prompt(
        prompt_text,
        manifest_source=args.manifest,
        template_name=args.template,
        repo_root=root,
        files_read=files_read_list,
        other_slugs=set(args.other_slug),
        earlier_editions=list(args.earlier_edition),
        prompts_dir=Path(args.prompts_dir) if args.prompts_dir else None,
    )

    if not result.passed:
        print("FAIL: Rendered prompt check failed with errors:")
        for err in result.errors:
            print(f"  - {err}")
        return 1

    print(f"PASS: Prompt check passed ({result.prompt_sha256})")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
