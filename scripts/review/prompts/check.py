"""Check a rendered reviewer prompt against the review contract (#8430 Part R2 item 1).

The contract (``docs/epics/fresh-build-review-contracts.md``, principle 4 and "The review attempt
manifest (r4)") is about **which documents** a reviewer receives: never the writer's prompt,
reasoning or self-assessment, no earlier edition, no other module's content, and nothing that the
attempt manifest does not name and hash. So this checker proves deterministic facts about documents
and never scans the text of a pinned input for leaks:

1. **Manifest and pin eligibility** (``eligibility.pin_refusals``): the manifest matches its schema (every
   required input is pinned); every pinned file is an input the contract
   lists for this manifest kind, at this module's own path for the current build. A v1 or archive
   path, another module's file, a writer file or a superseded snapshot is refused by a named code
   before anything is read.
2. **Exact render**: every pin's sha256 is verified, then the prompt is rendered again from the
   manifest through the same ``render.py`` path. The prompt file must equal that render byte for byte
   (and its ``.sha256`` sidecar its hash), so no appended or altered text, no fence trick, and no read
   of an unpinned file can pass.
3. **Template lint**: what the *templates* say. The renderer serves only the fixed set of ``*.md.j2``
   files of the prompts directory (a template cannot ``include``, ``import`` or ``extend`` anything
   else, and the lint refuses those tags in any case), and records the sha256 of each template it
   used beside the pinned files it read. Every ``*.md.j2`` is linted, and so is a render of the
   template in use with every pinned datum replaced by a sentinel (template-produced text only). The
   lint refuses another module's slug, a v1 path, writer or earlier-edition wording, unresolved
   placeholders and an unclosed fence. Pinned data is never text-scanned: a rebuilt lesson legitimately
   shares text with its earlier edition, and lesson content may use an English word that is also a
   module slug; neither is a contract violation.

Beyond the pins the checker reads the module manifest (for the level's slugs) and the templates, and
lists them as ``verifier_reads``; they never reach the rendered prompt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jinja2
import yaml

from scripts.build.fresh.manifest import pinned_entries
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.prompts.render import RenderError, render, resolve_template_name

#: Jinja statements that make a template read another file; none is allowed in any template.
EXTERNAL_READ_NODES: tuple[type[jinja2.nodes.Node], ...] = (
    jinja2.nodes.Include,
    jinja2.nodes.Import,
    jinja2.nodes.FromImport,
    jinja2.nodes.Extends,
)

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

#: A first review's template must not talk of an earlier edition; a re-review's names its diff and findings.
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

#: One-word module slugs (across the level lists of ``curriculum.yaml``) that are also ordinary English words
#: the authored templates use as prose. They are the only slugs a template may contain; a test keeps this
#: set equal to the collisions the shipped templates really have. Pinned data is never scanned, so it
#: needs no such exemption.
TEMPLATE_PROSE_SLUGS: frozenset[str] = frozenset({"comparison", "euphony", "review", "surzhyk"})

#: A module locator: the level directory of a plan, evidence pack, scope sidecar or built page, then the slug.
MODULE_LOCATOR = re.compile(
    r"(?:lesson-plans|_scope|evidence|site/src/content/docs)/(?:[a-z0-9]+-)?[a-z0-9]+/(?P<slug>[A-Za-z0-9][A-Za-z0-9-]*)"
)
#: The module manifest the level-wide slug list comes from (a verifier read, never a reviewer input).
MODULE_MANIFEST = "curriculum/l2-uk-en/curriculum.yaml"
FENCE_OPEN = re.compile(r"^ {0,3}(?P<fence>`{3,})[^`]*$")
JINJA_TAG = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", re.DOTALL)


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


def _slug_pattern(slug: str) -> re.Pattern[str]:
    """The slug as a whole token: not part of a longer slug, identifier or hyphenated word."""
    return re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(slug)}(?![A-Za-z0-9_-])")


def _unclosed_fence(text: str) -> bool:
    """Whether a fenced block in ``text`` is never closed (a fence closes only at its own or a longer run)."""
    closing: str | None = None
    for line in text.splitlines():
        if closing is None:
            opening = FENCE_OPEN.match(line)
            if opening:
                closing = opening.group("fence")
        elif re.fullmatch(rf" {{0,3}}`{{{len(closing)},}}\s*", line):
            closing = None
    return closing is not None


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


def _lint_template_text(
    text: str, label: str, *, own_slug: Any, foreign_slugs: set[str], rereview: bool, rendered: bool, errors: list[str]
) -> None:
    """Lint text a template produced (or, unrendered, its literal text): never pinned data."""
    for pat in FORBIDDEN_V1_PATTERNS:
        match = pat.search(text)
        if match:
            errors.append(f"forbidden_v1_path: {label} contains a v1 path matching {pat.pattern!r}: {match.group(0)!r}")
    for pat in WRITER_LEAKAGE_PATTERNS:
        match = pat.search(text)
        if match:
            errors.append(f"writer_prompt_or_assessment: {label} contains forbidden writer text: {match.group(0)!r}")
    for pat in REREVIEW_FULL_EDITION_PATTERNS if rereview else EARLIER_EDITION_PATTERNS:
        match = pat.search(text)
        if match:
            errors.append(f"earlier_edition: {label} contains earlier edition text: {match.group(0)!r}")
    # A slug the level lists is another module's unless it is this one's; an ordinary word the templates
    # use as prose (TEMPLATE_PROSE_SLUGS) is only an identifier where it stands in a module locator.
    for locator in MODULE_LOCATOR.finditer(text):
        if locator.group("slug") != own_slug:
            errors.append(f"forbidden_module_slug: {label} has a locator into another module: {locator.group(0)!r}")
    for slug in sorted(foreign_slugs - {own_slug} - TEMPLATE_PROSE_SLUGS):
        if _slug_pattern(slug).search(text):
            errors.append(f"forbidden_module_slug: {label} names another module slug {slug!r}")
    if _unclosed_fence(text):
        errors.append(f"unbalanced_data_fence: {label} opens a fenced block it never closes")
    for marker in PLACEHOLDER_MARKERS:
        if marker in text:
            errors.append(f"unresolved_placeholder: {label} contains placeholder token {marker!r}")
    if rendered:
        if "{%" in text or "%}" in text:
            errors.append(f"unresolved_placeholder: {label} has an unrendered Jinja statement tag ({{% or %}})")
        if "{{" in text or "}}" in text:
            errors.append(f"unresolved_placeholder: {label} has an unrendered Jinja expression tag ({{{{ or }}}})")
        for line in text.splitlines():
            if ": None" in line and not line.strip().startswith("#"):
                errors.append(f"unresolved_placeholder: {label} rendered a variable as 'None': {line.strip()!r}")


def _template_paths(prompts_dir: Path) -> list[Path]:
    return sorted(prompts_dir.glob("*.md.j2"))


def _lint_templates(
    manifest_doc: dict[str, Any],
    used_text: str | None,
    used_name: str,
    prompts_dir: Path,
    root: Path,
    foreign_slugs: set[str],
    verifier_reads: list[str],
    errors: list[str],
) -> None:
    """Lint every template in the directory (literal text) and the render of the one in use (sentinel data)."""
    parser = jinja2.Environment()
    for path in _template_paths(prompts_dir):
        verifier_reads.append(path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix())
        source = path.read_text(encoding="utf-8")
        try:
            parsed = parser.parse(source)
        except jinja2.TemplateSyntaxError as err:
            errors.append(f"template_invalid: {path.name} does not parse ({err})")
            continue
        for node in parsed.find_all(EXTERNAL_READ_NODES):
            errors.append(
                f"template_external_read: {path.name} line {node.lineno} uses {type(node).__name__.lower()}, "
                "which would read a file no manifest pins"
            )
        _lint_template_text(
            JINJA_TAG.sub("", source),
            f"template {path.name}",
            own_slug=manifest_doc.get("slug"),
            foreign_slugs=foreign_slugs,
            rereview="rereview" in path.name,
            rendered=False,
            errors=errors,
        )
    if used_text is not None:
        _lint_template_text(
            used_text,
            f"the render of {used_name} without its pinned data",
            own_slug=manifest_doc.get("slug"),
            foreign_slugs=foreign_slugs,
            rereview="rereview" in used_name or bool(manifest_doc.get("previous_attempt")),
            rendered=True,
            errors=errors,
        )


def check_prompt(
    rendered_prompt: str,
    manifest_source: Path | str | dict[str, Any],
    template_name: str | None = None,
    *,
    repo_root: Path | None = None,
    files_read: list[Path | str] | None = None,
    recorded_sha256: str | None = None,
    template_sha256: dict[str, str] | None = None,
    prompts_dir: Path | None = None,
) -> RenderedPromptCheckResult:
    """Validate a rendered reviewer prompt: eligible pins, exact re-render, clean templates."""
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

    # 1. Pin eligibility: which documents may reach the reviewer (nothing is read yet)
    errors.extend(str(refusal) for refusal in pin_refusals(manifest_doc, root))
    if errors:
        return result()

    # 2. Every pin's hash is verified before any pinned content is used for anything else
    verified = _verify_manifest_inputs(manifest_doc, root, errors)
    if errors:
        return result()
    # 3. Exact render: the same render.py path, the same manifest, byte for byte
    used_text: str | None = None
    used_templates: dict[Path, str] = {}
    try:
        rendering = render(manifest_source, template_name, repo_root=root, prompts_dir=prompts_dir)
    except RenderError as err:
        errors.append(f"render_failed: {type(err).__name__}: {err}")
    else:
        used_text = rendering.template_text
        used_templates = rendering.template_sha256
        if rendered_prompt != rendering.prompt:
            first = next(
                (i for i, (a, b) in enumerate(zip(rendered_prompt, rendering.prompt, strict=False)) if a != b),
                min(len(rendered_prompt), len(rendering.prompt)),
            )
            errors.append(
                f"prompt_not_exact_render: the prompt ({prompt_sha256}) differs from the render of the manifest "
                f"({rendering.prompt_sha256}) at character {first}"
            )
        if recorded_sha256 is not None and recorded_sha256 != rendering.prompt_sha256:
            errors.append(
                f"prompt_sha256_mismatch: the sidecar records {recorded_sha256}, the render of the manifest is "
                f"{rendering.prompt_sha256}"
            )

    # The recorded reads are the verified pins and the templates the render used, each template with its sha256
    if files_read is not None:
        recorded_paths = {(root / f).resolve() for f in files_read}
        for fp in sorted(recorded_paths - set(verified) - set(used_templates)):
            errors.append(f"unauthorized_file_read: file {fp.as_posix()} was read but is not in manifest inputs")
        for fp in sorted(set(used_templates) - recorded_paths):
            errors.append(f"template_read_not_recorded: the render used template {fp.as_posix()}, the reads omit it")
    if template_sha256 is not None and {(root / k).resolve(): v for k, v in template_sha256.items()} != used_templates:
        errors.append(
            "template_sha256_mismatch: the recorded template hashes differ from the templates the render used"
        )

    # 4. Template lint: the level's other slugs come from the module manifest (a verifier read)
    foreign = _level_slugs(manifest_doc, root, verifier_reads, errors)
    used_name = resolve_template_name(manifest_doc, template_name)
    _lint_templates(
        manifest_doc,
        used_text,
        used_name,
        (prompts_dir or PROMPTS_DIR).resolve(),
        root,
        foreign,
        verifier_reads,
        errors,
    )
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
    args = parser.parse_args(argv)

    root = Path(args.repo_root) if args.repo_root else REPO_ROOT
    prompt_path = (
        (root / args.prompt_file).resolve() if not Path(args.prompt_file).is_absolute() else Path(args.prompt_file)
    )
    if not prompt_path.is_file():
        print(f"FAIL: Prompt file does not exist: {prompt_path}")
        return 1
    prompt_text = prompt_path.read_text(encoding="utf-8")

    # The CLI must read the files_read sidecar and the prompt's sha256 sidecar, and must not run without them
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
    sha_sidecar = prompt_path.with_name(f"{prompt_path.name}.sha256")
    if not sha_sidecar.is_file():
        print(f"FAIL: Missing required sha256 sidecar for {prompt_path.name}: CLI must not run without it")
        return 1
    recorded = sha_sidecar.read_text(encoding="ascii").strip()
    if recorded != compute_sha256(prompt_text.encode("utf-8")):
        print(f"FAIL: The sha256 sidecar {sha_sidecar.name} does not match the prompt file")
        return 1

    try:
        sidecar = json.loads(files_read_path.read_text(encoding="utf-8"))
        if (
            not isinstance(sidecar, dict)
            or not isinstance(sidecar.get("files_read"), list)
            or not isinstance(sidecar.get("template_sha256"), dict)
        ):
            print(
                f"FAIL: files_read sidecar {files_read_path} is not a JSON object with a files_read list "
                "and a template_sha256 map"
            )
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
        recorded_sha256=recorded,
        template_sha256=sidecar.get("template_sha256"),
        prompts_dir=Path(args.prompts_dir) if args.prompts_dir else None,
    )

    sidecar["verifier_reads"] = [path for path in result.verifier_reads if path not in sidecar["files_read"]]
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
