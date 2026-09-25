"""Check rendered reviewer prompt for contract violations (#8430 Part R2 item 1).

Validates:
- Every pin the manifest names exists and hashes to its recorded sha256, before anything else
  is read for any other purpose (a failure returns at once)
- No v1 path references (curriculum/l2-uk-en/a1/, plans/)
- No other module's slug: the level's module list, the pinned arc, module locators in the
  prompt, and any slug the driver adds
- No writer prompt or writer self-assessment leakage
- No earlier edition of the lesson (except re-review's diff and previous findings), taken
  from the content-addressed lesson snapshots of the lesson's own history
- No unresolved Jinja placeholders in the template-produced text ({%, %}, {{, }}, TODO, : None)
- Every file read was a pin the manifest names and its sha256 matched

Pins are found the way the engine records them (``pinned_entries``): any object with a
``path`` and a ``sha256`` anywhere in the manifest. Each pinned file is read once, verified,
and that verified text serves every later check. The checker is a verifier, not a reviewer
input: beyond the pins it reads the module manifest and the lesson's content-addressed
snapshots, and lists them as ``verifier_reads`` (they never reach the rendered prompt).
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
from scripts.review.prompts.render import RenderError, resolve_template_name

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
    verifier_reads: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "prompt_sha256": self.prompt_sha256,
            "files_read": list(self.files_read),
            "verifier_reads": list(self.verifier_reads),
        }


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _collect_allowed_manifest_paths(manifest: dict[str, Any], repo_root: Path) -> dict[Path, str]:
    """Every pinned file, by resolved path, with the sha256 the manifest records."""
    root = repo_root.resolve()
    return {(root / entry["path"]).resolve(): str(entry["sha256"]) for _, entry in pinned_entries(manifest)}


def _verify_manifest_inputs(manifest: dict[str, Any], repo_root: Path, errors: list[str]) -> dict[Path, bytes]:
    """Read every pin once: it exists inside the repository and hashes to its recorded sha256.

    Returns the verified bytes by resolved path; each lock must also agree with its data pin.
    Nothing is read twice, so a changed file is read at most once before the check fails.
    """
    root = repo_root.resolve()
    pins = dict(pinned_entries(manifest))
    verified: dict[Path, bytes] = {}
    read: dict[Path, bytes] = {}

    for location, entry in pins.items():
        p = (root / entry["path"]).resolve()
        if not p.is_relative_to(root):
            errors.append(f"unauthorized_file_read: pin {location} escapes the repository: {entry['path']}")
        elif not p.is_file():
            errors.append(f"input_missing: {entry['path']} does not exist")
        else:
            if p not in read:
                read[p] = p.read_bytes()
            data = read[p]
            actual = compute_sha256(data)
            if actual != str(entry["sha256"]):
                errors.append(f"input_hash_mismatch: {entry['path']} expected {entry['sha256']}, actual {actual}")
            else:
                verified[p] = data

    for data_location, lock_location in (("inputs.pack", "inputs.pack_lock"), ("inputs.words", "inputs.words_lock")):
        if data_location not in pins or lock_location not in pins:
            continue
        lock_path = (root / pins[lock_location]["path"]).resolve()
        if lock_path in verified:
            words = verified[lock_path].decode("ascii", errors="replace").split()
            recorded = words[0] if words else ""
            if recorded != pins[data_location]["sha256"]:
                errors.append(
                    f"input_hash_mismatch: {pins[data_location]['path']} pinned at {pins[data_location]['sha256']}, "
                    f"its lock {pins[lock_location]['path']} records {recorded}"
                )
    return verified


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


#: The module manifest the level-wide slug list comes from (a verifier read, never a reviewer input).
MODULE_MANIFEST = "curriculum/l2-uk-en/curriculum.yaml"
#: Where every manifest write keeps the exact bytes of the lesson it records (``scripts.build.fresh.manifest``).
EVIDENCE_ROOT = "curriculum/l2-uk-en/evidence"
LESSON_SNAPSHOT = re.compile(r"lesson\.(?P<digest>[0-9a-f]{64})\.mdx\Z")
DIFF_BASE = re.compile(r"(?m)^--- a/\S*@(?P<prefix>[0-9a-f]{12})\s*$")
#: Shortest earlier-edition line treated as a passage (shorter lines are template and markup noise).
MIN_PASSAGE = 20
FENCE_OPEN = re.compile(r"^ {0,3}(?P<fence>`{3,})[^`]*$")


def _slug_pattern(slug: str) -> re.Pattern[str]:
    """The slug as a whole token: not part of a longer slug, identifier or hyphenated word."""
    return re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(slug)}(?![A-Za-z0-9_-])")


def _template_text(prompt: str, errors: list[str]) -> str:
    """The prompt without its fenced data blocks: what the template itself produced.

    The renderer fences every pinned file it inserts with a fence longer than any backtick run
    inside it, so a block closes only at its own fence. An unclosed fence would hide the rest of
    the prompt from every scan of template text, so it is an error.
    """
    kept: list[str] = []
    closing: str | None = None
    for line in prompt.splitlines():
        if closing is None:
            opening = FENCE_OPEN.match(line)
            if opening:
                closing = opening.group("fence")
            else:
                kept.append(line)
        elif re.fullmatch(rf" {{0,3}}`{{{len(closing)},}}\s*", line):
            closing = None
    if closing is not None:
        errors.append("unbalanced_data_fence: a fenced data block is never closed")
    return "\n".join(kept)


def _pinned_arc_positions(
    manifest_doc: dict[str, Any], root: Path, verified: dict[Path, bytes]
) -> list[dict[str, Any]]:
    """The positions of the pinned arc (``inputs.arc``), from its already verified bytes; empty when none is pinned."""
    entry = dict(pinned_entries(manifest_doc)).get("inputs.arc")
    data = verified.get((root / entry["path"]).resolve()) if entry else None
    if data is None:
        return []
    try:
        arc = yaml.safe_load(data.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError):
        return []
    positions = arc.get("positions", []) if isinstance(arc, dict) else []
    return [item for item in positions if isinstance(item, dict)]


def _level_slugs(manifest_doc: dict[str, Any], root: Path, verifier_reads: list[str], errors: list[str]) -> set[str]:
    """Every module slug of the manifest's level, from the module manifest (a verifier read)."""
    path = (root / MODULE_MANIFEST).resolve()
    if not path.is_file() or not path.is_relative_to(root):
        errors.append(f"module_manifest_unavailable: {MODULE_MANIFEST} is missing, so other modules' slugs are unknown")
        return set()
    verifier_reads.append(MODULE_MANIFEST)
    try:
        levels = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("levels") or {}
    except (OSError, yaml.YAMLError, AttributeError) as err:
        errors.append(f"module_manifest_unavailable: {MODULE_MANIFEST} cannot be read ({err})")
        return set()
    level = str(manifest_doc.get("level") or "")
    slugs = {
        str(module)
        for key, entry in levels.items()
        if isinstance(entry, dict) and level and level in (key, key.removesuffix("-v1"), entry.get("base_level"))
        for module in entry.get("modules") or []
        if isinstance(module, str)
    }
    if not slugs:
        errors.append(f"module_manifest_unavailable: {MODULE_MANIFEST} lists no modules for level {level!r}")
    return slugs


def _template_source(
    manifest_doc: dict[str, Any],
    template_name: str | None,
    prompts_dir: Path | None,
    root: Path,
    verifier_reads: list[str],
    errors: list[str],
) -> str:
    """The unrendered template the prompt came from (a verifier read): its own words are authored, not leaked."""
    try:
        path = (prompts_dir or PROMPTS_DIR).resolve() / resolve_template_name(manifest_doc, template_name)
    except RenderError as err:
        errors.append(f"template_unavailable: {err}")
        return ""
    if not path.is_file():
        errors.append(f"template_unavailable: {path.as_posix()} does not exist")
        return ""
    verifier_reads.append(path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix())
    return path.read_text(encoding="utf-8")


def _earlier_editions(
    manifest_doc: dict[str, Any],
    root: Path,
    verified: dict[Path, bytes],
    verifier_reads: list[str],
    errors: list[str],
) -> list[tuple[str, bytes]]:
    """Every earlier edition of this lesson, from the content-addressed snapshots its manifest writes kept.

    The snapshots sit next to the manifest history, named by the sha256 of their bytes. The current
    lesson is not earlier, and a re-review's diff base is the one edition its pinned diff is
    allowed to quote, so both are left out. A snapshot whose bytes do not hash to its name is an error.
    """
    if manifest_doc.get("kind") != "lesson":
        return []
    pins = dict(pinned_entries(manifest_doc))
    lesson = pins.get("inputs.lesson")
    number, level, slug = manifest_doc.get("lesson"), manifest_doc.get("level"), manifest_doc.get("slug")
    if lesson is None or not (isinstance(number, int) and level and slug):
        return []
    skipped = {str(lesson["sha256"])}
    diff = pins.get("diff")
    if manifest_doc.get("previous_attempt") and diff is not None:
        diff_text = verified.get((root / diff["path"]).resolve(), b"").decode("utf-8", errors="replace")
        base = DIFF_BASE.search(diff_text)
        if base is None and diff_text.strip():
            errors.append(
                "earlier_edition: the pinned diff names no base lesson snapshot, so earlier editions are unknown"
            )
            return []
        skipped.add(base.group("prefix") if base else "")
    directory = root / EVIDENCE_ROOT / str(level) / "_state" / str(slug) / "manifests" / f"lesson-{number}"
    editions: list[tuple[str, bytes]] = []
    for snapshot in sorted(directory.glob("lesson.*.mdx")) if directory.is_dir() else []:
        named = LESSON_SNAPSHOT.match(snapshot.name)
        if named is None or any(named.group("digest").startswith(digest) for digest in skipped if digest):
            continue
        data = snapshot.read_bytes()
        verifier_reads.append(snapshot.relative_to(root).as_posix())
        if compute_sha256(data) != named.group("digest"):
            errors.append(f"input_hash_mismatch: lesson snapshot {snapshot.name} does not hash to its name")
        else:
            editions.append((snapshot.name, data))
    return editions


def _check_earlier_edition(
    label: str, earlier_bytes: bytes, pinned_texts: list[str], prompt: str, errors: list[str]
) -> None:
    """The overlap rule: earlier text a pinned file also holds (current lesson, diff, findings) is manifested.

    What only the earlier edition holds must not reach the prompt: not its bytes, its hash, or any
    passage (line) that no pinned file carries.
    """
    earlier_text = earlier_bytes.decode("utf-8", errors="replace").strip()
    if not earlier_text or any(earlier_text in text for text in pinned_texts):
        return
    earlier_sha = compute_sha256(earlier_bytes)
    if earlier_sha in prompt:
        errors.append(f"earlier_edition: prompt contains unmanifested earlier edition hash {earlier_sha} from {label}")
    if len(earlier_text) >= 10 and earlier_text in prompt:
        errors.append(f"earlier_edition: prompt contains unmanifested earlier edition bytes from {label}")
        return
    for line in earlier_text.splitlines():
        passage = line.strip()
        if len(passage) >= MIN_PASSAGE and passage in prompt and not any(passage in text for text in pinned_texts):
            errors.append(
                f"earlier_edition: prompt contains an unmanifested earlier edition passage from {label}: {passage!r}"
            )
            return


def _derive_foreign_slugs(
    manifest_doc: dict[str, Any],
    positions: list[dict[str, Any]],
    other_slugs: set[str] | list[str] | None = None,
    rendered_prompt: str = "",
    level_slugs: set[str] | None = None,
) -> set[str]:
    """Foreign module slugs from the pinned arc, the prompt's own module locators, the driver and the level's list.

    The module manifest lists every slug of the level, so any of them other than this module's own is foreign.
    """
    current_slug = manifest_doc.get("slug")
    slugs: set[str] = set(other_slugs or []) | set(level_slugs or [])
    slugs.update(str(pos["slug"]) for pos in positions if pos.get("slug"))
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
    verifier_reads: list[str] = []

    if isinstance(manifest_source, (str, Path)):
        mpath = (root / manifest_source).resolve() if not Path(manifest_source).is_absolute() else Path(manifest_source)
        manifest_doc = yaml.safe_load(mpath.read_text(encoding="utf-8"))
    elif isinstance(manifest_source, dict):
        manifest_doc = manifest_source
    else:
        manifest_doc = {}

    prompt_sha256 = compute_sha256(rendered_prompt.encode("utf-8"))
    files_read_str = [str(f) for f in (files_read or [])]

    def result() -> RenderedPromptCheckResult:
        return RenderedPromptCheckResult(
            passed=(len(errors) == 0),
            errors=errors,
            prompt_sha256=prompt_sha256,
            files_read=files_read_str,
            verifier_reads=verifier_reads,
        )

    # 1. Verify every pin's hash before any pinned content is used for anything else
    verified = _verify_manifest_inputs(manifest_doc, root, errors)
    if errors:
        return result()
    pinned_texts = [data.decode("utf-8", errors="replace") for data in verified.values()]

    # 2. Verify files read: each must be a pin, and every pin was verified above
    if files_read is not None:
        for f in files_read:
            fp = (root / f).resolve() if not Path(f).is_absolute() else Path(f)
            if fp not in verified:
                errors.append(f"unauthorized_file_read: file {fp.as_posix()} was read but is not in manifest inputs")

    # 3. Check for forbidden v1 paths
    for pat in FORBIDDEN_V1_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(
                f"forbidden_v1_path: prompt contains v1 path reference matching {pat.pattern!r}: {match.group(0)!r}"
            )

    # 4. Foreign module detection (the level's modules, the pinned arc, the prompt's module locators, the driver's list)
    template_text = _template_text(rendered_prompt, errors)
    positions = _pinned_arc_positions(manifest_doc, root, verified)
    allowed_neighbour_slugs: set[str] = set()
    pos_num = manifest_doc.get("position")
    if manifest_doc.get("kind") == "plan" and pos_num is not None:
        for pos in positions:
            p_num = pos.get("position")
            if isinstance(p_num, int) and abs(p_num - int(pos_num)) <= 1 and pos.get("slug"):
                allowed_neighbour_slugs.add(str(pos["slug"]))

    level_slugs = _level_slugs(manifest_doc, root, verifier_reads, errors)
    foreign_slugs = _derive_foreign_slugs(manifest_doc, positions, other_slugs, rendered_prompt, level_slugs)
    explicit_slugs = _derive_foreign_slugs(manifest_doc, positions, other_slugs, rendered_prompt)
    level_only = {slug for slug in foreign_slugs - explicit_slugs if "-" not in slug}
    template_source = (
        _template_source(manifest_doc, template_name, prompts_dir, root, verifier_reads, errors) if level_only else ""
    )

    for s in sorted(foreign_slugs):
        if not s or (manifest_doc.get("kind") == "plan" and s in allowed_neighbour_slugs):
            # Neighbour position references are permitted in plan review context
            continue
        pattern = _slug_pattern(s)
        # A single word can be ordinary prose, so a slug known only as a one-word entry of the level's list
        # is looked for in the template-produced text, and skipped when the template's own source uses the
        # word (authored prose such as "comparison"); every other slug (hyphenated, a module locator, the
        # pinned arc, the driver's) is an identifier wherever it stands.
        if s in level_only and pattern.search(template_source):
            continue
        searched = template_text if s in level_only else rendered_prompt
        if s in TAXONOMY_EXEMPT_WORDS:
            lines = searched.splitlines()
            found = any(pattern.search(line) and not _is_taxonomy_boilerplate_line(line) for line in lines)
        else:
            found = bool(pattern.search(searched))
        if found:
            errors.append(f"forbidden_module_slug: found other module slug {s!r} in rendered prompt")

    # 5. Check for writer prompt or self-assessment leakage
    for pat in WRITER_LEAKAGE_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(f"writer_prompt_or_assessment: prompt contains forbidden writer text: {match.group(0)!r}")

    # 6. Check for earlier edition of the lesson
    t_name = template_name or ""
    is_rereview = "rereview" in t_name or bool(manifest_doc.get("previous_attempt"))

    # Earlier editions come from the lesson's own pinned history (every snapshot but the current one and a
    # re-review's diff base) and, optionally, from the driver.
    supplied: list[tuple[str, bytes]] = []
    for item in earlier_editions or []:
        candidate = (root / item).resolve() if not Path(item).is_absolute() else Path(item)
        if candidate.is_file():
            supplied.append((candidate.name, candidate.read_bytes()))
        else:
            supplied.append(("supplied text", str(item).encode("utf-8")))
    for label, data in [*_earlier_editions(manifest_doc, root, verified, verifier_reads, errors), *supplied]:
        _check_earlier_edition(label, data, pinned_texts, rendered_prompt, errors)

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

    # 7. Check for unresolved Jinja placeholders (in what the template produced; fenced pinned data is literal)
    if "{%" in template_text or "%}" in template_text:
        errors.append("unresolved_placeholder: unrendered Jinja statement tag ({% or %}) found in prompt")

    if "{{" in template_text or "}}" in template_text:
        errors.append("unresolved_placeholder: unrendered Jinja expression tag ({{ or }}) found in prompt")

    for marker in PLACEHOLDER_MARKERS:
        if marker in rendered_prompt:
            errors.append(f"unresolved_placeholder: placeholder token {marker!r} found in prompt")

    for line in rendered_prompt.splitlines():
        if ": None" in line and not line.strip().startswith("#"):
            errors.append(f"unresolved_placeholder: template variable rendered as 'None': {line.strip()!r}")

    return result()


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
        sidecar = json.loads(files_read_path.read_text(encoding="utf-8"))
        if not isinstance(sidecar, dict) or not isinstance(sidecar.get("files_read"), list):
            print(f"FAIL: files_read sidecar {files_read_path} is not a JSON object with a files_read list")
            return 1
        files_read_list = [root / p for p in sidecar["files_read"]]
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

    sidecar["verifier_reads"] = result.verifier_reads
    files_read_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

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
