"""Check rendered reviewer prompt for contract violations (#8430 Part R2 item 1).

Validates:
- No v1 path references (curriculum/l2-uk-en/a1/, plans/)
- No other module's slug
- No writer prompt or writer self-assessment leakage
- No earlier edition of the lesson (except re-review's diff and previous findings)
- No unresolved Jinja placeholders ({%, %}, {{, }}, TODO, : None)
- Every file read was declared in manifest inputs and its sha256 matched
"""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

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
    re.compile(r"\blesson writer prompt\b", re.IGNORECASE),
    re.compile(r"\brecap writer prompt\b", re.IGNORECASE),
    re.compile(r"\bwriter prompt\b", re.IGNORECASE),
    re.compile(r"\byou are the lesson writer\b", re.IGNORECASE),
    re.compile(r"\blesson-draft-v1\b"),
    re.compile(r"\bself-assessment\b", re.IGNORECASE),
    re.compile(r"\bself_assessment\b", re.IGNORECASE),
    re.compile(r"\bself assessment\b", re.IGNORECASE),
    re.compile(r"\bwriter_assessment\b", re.IGNORECASE),
    re.compile(r"\bwriter's self-assessment\b", re.IGNORECASE),
    re.compile(r"\bnotes to the reviewer\b", re.IGNORECASE),
    re.compile(r"\bwriter notes\b", re.IGNORECASE),
    re.compile(r"\bwriter's notes\b", re.IGNORECASE),
)

EARLIER_EDITION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bearlier edition\b", re.IGNORECASE),
    re.compile(r"\bprevious edition\b", re.IGNORECASE),
    re.compile(r"\bearlier draft\b", re.IGNORECASE),
    re.compile(r"\bprevious draft\b", re.IGNORECASE),
    re.compile(r"\bdiff from previous attempt\b", re.IGNORECASE),
    re.compile(r"\bprevious findings\b", re.IGNORECASE),
)

REREVIEW_FULL_EDITION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bearlier edition of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bprevious edition of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bfull text of previous edition\b", re.IGNORECASE),
    re.compile(r"\bearlier draft of (?:the|this) lesson\b", re.IGNORECASE),
    re.compile(r"\bprevious draft of (?:the|this) lesson\b", re.IGNORECASE),
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
    root = repo_root.resolve()
    allowed: dict[Path, str] = {}
    inputs = manifest.get("inputs", {})

    for _key, val in inputs.items():
        if isinstance(val, dict) and "path" in val and "sha256" in val:
            p = (root / val["path"]).resolve()
            allowed[p] = str(val["sha256"])
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "path" in item and "sha256" in item:
                    p = (root / item["path"]).resolve()
                    allowed[p] = str(item["sha256"])

    if "module_digest" in manifest and isinstance(manifest["module_digest"], dict):
        md = manifest["module_digest"]
        if "path" in md and "sha256" in md:
            p = (root / md["path"]).resolve()
            allowed[p] = str(md["sha256"])

    if "diff_path" in manifest and "diff_sha256" in manifest:
        p = (root / manifest["diff_path"]).resolve()
        allowed[p] = str(manifest["diff_sha256"])

    # Authorized lock targets
    if "pack_lock" in inputs and isinstance(inputs["pack_lock"], dict):
        lock_p = (root / inputs["pack_lock"]["path"]).resolve()
        if lock_p.is_file():
            lock_text = lock_p.read_text(encoding="ascii").strip()
            pack_sha = lock_text.split()[0] if lock_text else ""
            pack_p = Path(str(lock_p)[:-5]) if str(lock_p).endswith(".lock") else lock_p.with_suffix("")
            allowed[pack_p] = pack_sha

    if "words_lock" in inputs and isinstance(inputs["words_lock"], dict):
        wlock_p = (root / inputs["words_lock"]["path"]).resolve()
        if wlock_p.is_file():
            wlock_text = wlock_p.read_text(encoding="ascii").strip()
            words_sha = wlock_text.split()[0] if wlock_text else ""
            words_p = Path(str(wlock_p)[:-5]) if str(wlock_p).endswith(".lock") else wlock_p.with_suffix("")
            allowed[words_p] = words_sha

    return allowed


def _verify_manifest_inputs(manifest: dict[str, Any], repo_root: Path, errors: list[str]) -> None:
    root = repo_root.resolve()
    inputs = manifest.get("inputs", {})

    for _key, val in inputs.items():
        if isinstance(val, dict) and "path" in val and "sha256" in val:
            p = (root / val["path"]).resolve()
            if not p.is_file():
                errors.append(f"input_missing: {val['path']} does not exist")
                continue
            actual = compute_sha256(p.read_bytes())
            if actual != str(val["sha256"]):
                errors.append(f"input_hash_mismatch: {val['path']} expected {val['sha256']}, actual {actual}")
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "path" in item and "sha256" in item:
                    p = (root / item["path"]).resolve()
                    if not p.is_file():
                        errors.append(f"input_missing: {item['path']} does not exist")
                        continue
                    actual = compute_sha256(p.read_bytes())
                    if actual != str(item["sha256"]):
                        errors.append(f"input_hash_mismatch: {item['path']} expected {item['sha256']}, actual {actual}")

    # Check pack lock and pack file
    if "pack_lock" in inputs and isinstance(inputs["pack_lock"], dict):
        lock_p = (root / inputs["pack_lock"]["path"]).resolve()
        if lock_p.is_file():
            pack_p = Path(str(lock_p)[:-5]) if str(lock_p).endswith(".lock") else lock_p.with_suffix("")
            if not pack_p.is_file():
                errors.append(f"input_missing: locked pack file {pack_p.as_posix()} does not exist")
            else:
                expected_sha = lock_p.read_text(encoding="ascii").strip().split()[0]
                actual_sha = compute_sha256(pack_p.read_bytes())
                if actual_sha != expected_sha:
                    errors.append(
                        f"input_hash_mismatch: pack file {pack_p.as_posix()} hash mismatch with lock: "
                        f"recorded {expected_sha}, actual {actual_sha}"
                    )

    # Check words lock and words file
    if "words_lock" in inputs and isinstance(inputs["words_lock"], dict):
        wlock_p = (root / inputs["words_lock"]["path"]).resolve()
        if wlock_p.is_file():
            words_p = Path(str(wlock_p)[:-5]) if str(wlock_p).endswith(".lock") else wlock_p.with_suffix("")
            if not words_p.is_file():
                errors.append(f"input_missing: locked words file {words_p.as_posix()} does not exist")
            else:
                expected_w_sha = wlock_p.read_text(encoding="ascii").strip().split()[0]
                actual_w_sha = compute_sha256(words_p.read_bytes())
                if actual_w_sha != expected_w_sha:
                    errors.append(
                        f"input_hash_mismatch: words file {words_p.as_posix()} hash mismatch with lock: "
                        f"recorded {expected_w_sha}, actual {actual_w_sha}"
                    )

    # Check module_digest if present
    if "module_digest" in manifest and isinstance(manifest["module_digest"], dict):
        md = manifest["module_digest"]
        if "path" in md and "sha256" in md:
            mdp = (root / md["path"]).resolve()
            if not mdp.is_file():
                errors.append(f"input_missing: module digest {md['path']} does not exist")
            else:
                actual_md = compute_sha256(mdp.read_bytes())
                if actual_md != str(md["sha256"]):
                    errors.append(
                        f"input_hash_mismatch: module digest {md['path']} expected {md['sha256']}, actual {actual_md}"
                    )


def check_prompt(
    rendered_prompt: str,
    manifest_source: Path | str | dict[str, Any],
    template_name: str | None = None,
    *,
    repo_root: Path | None = None,
    files_read: list[Path | str] | None = None,
    other_slugs: set[str] | list[str] | None = None,
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

    # 3. Check for forbidden v1 paths
    for pat in FORBIDDEN_V1_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(
                f"forbidden_v1_path: prompt contains v1 path reference matching {pat.pattern!r}: {match.group(0)!r}"
            )

    # 4. Check for another module's slug
    current_slug = manifest_doc.get("slug")
    prohibited_slugs: set[str] = set(other_slugs or [])

    if not prohibited_slugs and current_slug:
        # Check arc input if present
        inputs = manifest_doc.get("inputs", {})
        if "arc" in inputs and isinstance(inputs["arc"], dict):
            arc_p = (root / inputs["arc"]["path"]).resolve()
            if arc_p.is_file():
                try:
                    arc_doc = yaml.safe_load(arc_p.read_text(encoding="utf-8"))
                    for pos in arc_doc.get("positions", []):
                        pos_slug = pos.get("slug")
                        if pos_slug and pos_slug != current_slug:
                            prohibited_slugs.add(pos_slug)
                except Exception:
                    pass

        # Also check level arc if available
        level = manifest_doc.get("level")
        if level and not prohibited_slugs:
            lvl_arc = root / f"curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml"
            if lvl_arc.is_file():
                try:
                    arc_doc = yaml.safe_load(lvl_arc.read_text(encoding="utf-8"))
                    for pos in arc_doc.get("positions", []):
                        pos_slug = pos.get("slug")
                        if pos_slug and pos_slug != current_slug:
                            prohibited_slugs.add(pos_slug)
                except Exception:
                    pass

    for s in prohibited_slugs:
        if s and re.search(rf"\b{re.escape(s)}\b", rendered_prompt):
            errors.append(f"forbidden_module_slug: found other module slug {s!r} in rendered prompt")

    # 5. Check for writer prompt or self-assessment leakage
    for pat in WRITER_LEAKAGE_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(f"writer_prompt_or_assessment: prompt contains forbidden writer text: {match.group(0)!r}")

    # 6. Check for earlier edition of the lesson
    t_name = template_name or ""
    is_rereview = (
        "rereview" in t_name or bool(manifest_doc.get("previous_attempt")) or bool(manifest_doc.get("diff_sha256"))
    )

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
    args = parser.parse_args(argv)

    root = Path(args.repo_root) if args.repo_root else REPO_ROOT
    prompt_path = (
        (root / args.prompt_file).resolve() if not Path(args.prompt_file).is_absolute() else Path(args.prompt_file)
    )
    prompt_text = prompt_path.read_text(encoding="utf-8")

    result = check_prompt(
        prompt_text,
        manifest_source=args.manifest,
        template_name=args.template,
        repo_root=root,
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
