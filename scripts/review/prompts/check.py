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
import json
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

    # E3d: manifest["inputs"]["module_digest"]
    if "module_digest" in manifest and isinstance(manifest["module_digest"], dict):
        md = manifest["module_digest"]
        if "path" in md and "sha256" in md:
            p = (root / md["path"]).resolve()
            allowed[p] = str(md["sha256"])

    # E3d: manifest["inputs"]["diff"]
    if "diff_path" in manifest and "diff_sha256" in manifest:
        p = (root / manifest["diff_path"]).resolve()
        allowed[p] = str(manifest["diff_sha256"])

    # Authorized lock targets
    # E3d: manifest["inputs"]["pack"]
    if "pack_lock" in inputs and isinstance(inputs["pack_lock"], dict):
        lock_p = (root / inputs["pack_lock"]["path"]).resolve()
        if lock_p.is_file():
            lock_text = lock_p.read_text(encoding="ascii").strip()
            pack_sha = lock_text.split()[0] if lock_text else ""
            pack_p = Path(str(lock_p)[:-5]) if str(lock_p).endswith(".lock") else lock_p.with_suffix("")
            allowed[pack_p] = pack_sha

    # E3d: manifest["inputs"]["words"]
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
    # E3d: manifest["inputs"]["pack"]
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
    # E3d: manifest["inputs"]["words"]
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
    # E3d: manifest["inputs"]["module_digest"]
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


def _derive_foreign_slugs(
    manifest_doc: dict[str, Any],
    repo_root: Path,
    other_slugs: set[str] | list[str] | None = None,
) -> set[str]:
    """Derive foreign module slugs for the level via hashed reads from curriculum.yaml and the arc."""
    root = repo_root.resolve()
    current_slug = manifest_doc.get("slug")
    level = manifest_doc.get("level")
    slugs: set[str] = set(other_slugs or [])

    # 1. Hashed read of curriculum/l2-uk-en/curriculum.yaml for this level
    curriculum_path = root / "curriculum/l2-uk-en/curriculum.yaml"
    if not curriculum_path.is_file() and root != REPO_ROOT:
        curriculum_path = REPO_ROOT / "curriculum/l2-uk-en/curriculum.yaml"
    if curriculum_path.is_file():
        c_bytes = curriculum_path.read_bytes()
        _ = compute_sha256(c_bytes)
        try:
            c_doc = yaml.safe_load(c_bytes.decode("utf-8"))
            if isinstance(c_doc, dict):
                levels = c_doc.get("levels", {})
                level_keys = [level, f"{level}-v1"] if level else list(levels.keys())
                for lvl_key in level_keys:
                    lvl_val = levels.get(lvl_key)
                    if isinstance(lvl_val, dict) and "modules" in lvl_val:
                        for mod in lvl_val["modules"]:
                            if isinstance(mod, str):
                                slugs.add(mod)
        except Exception:
            pass

    # 2. Hashed read of arc
    inputs = manifest_doc.get("inputs", {})
    arc_path = None
    if "arc" in inputs and isinstance(inputs["arc"], dict) and "path" in inputs["arc"]:
        arc_path = (root / inputs["arc"]["path"]).resolve()
    elif level:
        cand = root / f"curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml"
        if cand.is_file():
            arc_path = cand
        elif root != REPO_ROOT and (REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml").is_file():
            arc_path = REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml"

    if arc_path and arc_path.is_file():
        a_bytes = arc_path.read_bytes()
        _ = compute_sha256(a_bytes)
        try:
            a_doc = yaml.safe_load(a_bytes.decode("utf-8"))
            if isinstance(a_doc, dict):
                for pos in a_doc.get("positions", []):
                    if isinstance(pos, dict) and pos.get("slug"):
                        slugs.add(str(pos["slug"]))
        except Exception:
            pass

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

    # 4. Foreign module detection (hashed reads)
    allowed_neighbour_slugs: set[str] = set()
    if manifest_doc.get("kind") == "plan":
        pos_num = manifest_doc.get("position")
        if pos_num is None and "plan" in manifest_doc.get("inputs", {}):
            plan_in = manifest_doc["inputs"]["plan"]
            if isinstance(plan_in, dict) and "path" in plan_in:
                try:
                    p_doc = yaml.safe_load((root / plan_in["path"]).read_text(encoding="utf-8"))
                    pos_num = p_doc.get("arc_ref", {}).get("position")
                except Exception:
                    pass
        if pos_num is not None:
            inputs = manifest_doc.get("inputs", {})
            arc_p = None
            if "arc" in inputs and isinstance(inputs["arc"], dict) and "path" in inputs["arc"]:
                arc_p = (root / inputs["arc"]["path"]).resolve()
            elif manifest_doc.get("level"):
                cand = root / f"curriculum/l2-uk-en/lesson-plans/{manifest_doc['level']}/_arc.yaml"
                if cand.is_file():
                    arc_p = cand
                elif (
                    root != REPO_ROOT
                    and (REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{manifest_doc['level']}/_arc.yaml").is_file()
                ):
                    arc_p = REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{manifest_doc['level']}/_arc.yaml"
            if arc_p and arc_p.is_file():
                try:
                    a_doc = yaml.safe_load(arc_p.read_text(encoding="utf-8"))
                    for pos in a_doc.get("positions", []):
                        if isinstance(pos, dict):
                            p_num = pos.get("position")
                            if p_num is not None and abs(int(p_num) - int(pos_num)) <= 1 and pos.get("slug"):
                                allowed_neighbour_slugs.add(str(pos["slug"]))
                except Exception:
                    pass

    foreign_slugs = _derive_foreign_slugs(manifest_doc, root, other_slugs)
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
    is_rereview = (
        "rereview" in t_name or bool(manifest_doc.get("previous_attempt")) or bool(manifest_doc.get("diff_sha256"))
    )

    earlier_files: list[Path] = []
    if earlier_editions:
        for item in earlier_editions:
            if isinstance(item, (str, Path)):
                p = (root / item).resolve() if not Path(item).is_absolute() else Path(item)
                if p.is_file():
                    earlier_files.append(p)
                else:
                    raw_text = str(item).strip()
                    if raw_text:
                        raw_sha = compute_sha256(raw_text.encode("utf-8"))
                        if raw_sha in rendered_prompt:
                            errors.append(
                                f"earlier_edition: prompt contains unmanifested earlier edition hash {raw_sha}"
                            )
                        if len(raw_text) >= 10 and raw_text in rendered_prompt:
                            errors.append("earlier_edition: prompt contains unmanifested earlier edition bytes")

    level = manifest_doc.get("level")
    current_slug = manifest_doc.get("slug")
    if level and current_slug:
        state_dir = root / f"curriculum/l2-uk-en/evidence/{level}/_state/{current_slug}"
        if state_dir.is_dir():
            for p in state_dir.glob("*"):
                if p.is_file() and any(k in p.name.lower() for k in ("prev", "old", "attempt", "draft", "edition")):
                    earlier_files.append(p)

    named_paths: set[Path] = set()
    inputs = manifest_doc.get("inputs", {})
    for k in ("diff", "previous_findings", "lesson", "plan"):
        if k in inputs and isinstance(inputs[k], dict) and "path" in inputs[k]:
            named_paths.add((root / inputs[k]["path"]).resolve())
    if "diff_path" in manifest_doc:
        named_paths.add((root / manifest_doc["diff_path"]).resolve())

    for ef in earlier_files:
        if ef.resolve() in named_paths or ef.name.endswith(".sha256"):
            continue
        try:
            ef_bytes = ef.read_bytes()
            if not ef_bytes:
                continue
            ef_sha = compute_sha256(ef_bytes)
            if ef_sha in rendered_prompt:
                errors.append(
                    f"earlier_edition: prompt contains unmanifested earlier edition hash {ef_sha} from {ef.name}"
                )
            ef_text = ef_bytes.decode("utf-8", errors="replace").strip()
            if len(ef_text) >= 10 and ef_text in rendered_prompt:
                errors.append(f"earlier_edition: prompt contains unmanifested earlier edition bytes from {ef.name}")
        except Exception:
            pass

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
