"""Content-addressed reviewer prompt renderer (#8430 Part R2 item 1).

Renders reviewer prompts strictly from the inputs the review attempt manifest names
and hashes (plan review, lesson review, lesson re-review, or settle). The pinned
files are found the way the engine records them: any object carrying a ``path`` and
a ``sha256`` anywhere in the manifest is a pin (``scripts.build.fresh.manifest
.pinned_entries``), so ``inputs.*``, ``module_digest``, ``diff``,
``previous_attempt.*`` and ``upstream_lessons[*]`` are read alike. A file is read
only through a pin, only after its bytes match the pin's sha256, and no path is
derived from another path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from scripts.build.fresh.manifest import learner_state_sha256, pinned_entries
from scripts.review.receipts import REVIEW_TOOLS

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = Path(__file__).resolve().parent

#: Pins a first-class review needs, by manifest kind; a missing one is refused by name
#: rather than rendered as an empty section.
REQUIRED_PINS: dict[str, tuple[str, ...]] = {
    "lesson": (
        "inputs.plan",
        "inputs.pack",
        "inputs.pack_lock",
        "inputs.words",
        "inputs.words_lock",
        "inputs.learner_state",
        "inputs.lesson",
        "inputs.gate_report",
        "inputs.style_card",
        "module_digest",
    ),
    "plan": (
        "inputs.plan",
        "inputs.pack",
        "inputs.pack_lock",
        "inputs.words",
        "inputs.words_lock",
        "inputs.learner_state",
        "inputs.requirements",
        "inputs.arc",
        "inputs.arc_source",
        "inputs.decisions",
        "inputs.scope",
        "inputs.grammar",
        "inputs.validate_report",
        "inputs.pack_verify_report",
    ),
}


class RenderError(Exception):
    """Base error for prompt rendering failures."""


class InputHashMismatchError(RenderError):
    """An input file's sha256 does not match the manifest."""


class InputMissingError(RenderError):
    """An input file declared in the manifest does not exist."""


class UnauthorizedFileReadError(RenderError):
    """Attempted to read a file not declared in manifest inputs."""


class PackLockMismatchError(RenderError):
    """Pack file hash does not match its lock sidecar."""


class WordsLockMismatchError(RenderError):
    """Words file hash does not match its lock sidecar."""


class LearnerStateMismatchError(RenderError):
    """The materialized learner state does not hash to the identity the manifest records."""


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def dump_yaml(content: Any) -> str:
    """Readable YAML for parsed data: Ukrainian kept as written, nothing folded across lines."""
    return yaml.safe_dump(content, allow_unicode=True, sort_keys=False, width=1 << 30).strip()


def data_fence(content: Any, lang: str = "") -> str:
    """Insert data content safely wrapped in a fence delimiter that cannot occur in the content.

    Computes a backtick fence longer than the longest run of backticks in `content`,
    with a minimum length of 3 backticks.
    """
    if isinstance(content, str):
        text = content
    elif content is None:
        text = ""
    else:
        text = dump_yaml(content)

    runs = re.findall(r"`+", text)
    max_run = max((len(r) for r in runs), default=0)
    fence = "`" * max(3, max_run + 1)
    body = text if text.endswith("\n") else text + "\n"
    tag = lang.strip()
    return f"{fence}{tag}\n{body}{fence}"


class ManifestReader:
    """Reads only files the manifest pins, each verified against its pinned sha256 before use."""

    def __init__(self, manifest: dict[str, Any], repo_root: Path):
        self.manifest = manifest
        self.repo_root = repo_root.resolve()
        self.pins: dict[str, dict[str, Any]] = dict(pinned_entries(manifest))
        self.allowed_paths: dict[Path, str] = {}
        self.files_read: list[Path] = []
        for location, entry in self.pins.items():
            path = (self.repo_root / entry["path"]).resolve()
            if not path.is_relative_to(self.repo_root):
                raise UnauthorizedFileReadError(f"pinned path escapes the repository ({location}): {entry['path']}")
            recorded = self.allowed_paths.setdefault(path, str(entry["sha256"]))
            if recorded != str(entry["sha256"]):
                raise RenderError(f"manifest pins {entry['path']} with two different hashes ({location})")

    def has(self, location: str) -> bool:
        return location in self.pins

    def pin(self, location: str) -> dict[str, Any]:
        if location not in self.pins:
            raise RenderError(f"manifest names no {location} input")
        return self.pins[location]

    def read_bytes(self, target: Path | str) -> bytes:
        p = (self.repo_root / target).resolve() if not isinstance(target, Path) or not target.is_absolute() else target
        if p not in self.allowed_paths:
            raise UnauthorizedFileReadError(f"file read not in manifest inputs: {p.as_posix()}")
        if not p.is_file():
            raise InputMissingError(f"input file missing: {p.as_posix()}")

        data = p.read_bytes()
        actual = compute_sha256(data)
        expected = self.allowed_paths[p]
        if actual != expected:
            raise InputHashMismatchError(
                f"input hash mismatch for {p.as_posix()}: expected {expected}, actual {actual}"
            )
        self.files_read.append(p)
        return data

    def read_text(self, target: Path | str) -> str:
        return self.read_bytes(target).decode("utf-8")

    def pin_text(self, location: str) -> str:
        return self.read_text(self.pin(location)["path"])

    def pin_yaml(self, location: str) -> Any:
        return yaml.safe_load(self.pin_text(location))

    def pin_json(self, location: str) -> Any:
        return json.loads(self.pin_text(location))

    def locked_text(self, data: str, lock: str, error: type[RenderError]) -> str:
        """A pinned data file whose lock (also pinned) records the same sha256 as the pin."""
        recorded = self.pin_text(lock).split()
        if not recorded or recorded[0] != self.pin(data)["sha256"]:
            raise error(f"{self.pin(data)['path']} disagrees with its lock {self.pin(lock)['path']}")
        return self.pin_text(data)


def resolve_template_name(manifest: dict[str, Any], template_name: str | None = None) -> str:
    """Accept any template in prompts dir; default based on manifest structure."""
    if template_name:
        name = template_name.strip()
        if not name.endswith(".j2"):
            name = f"{name}.md.j2" if not name.endswith(".md") else f"{name}.j2"
        return name

    kind = manifest.get("kind")
    if kind == "plan":
        return "plan-review.md.j2"
    if kind == "lesson":
        return "lesson-rereview.md.j2" if manifest.get("previous_attempt") else "lesson-review.md.j2"
    if kind == "settle":
        return "settle.md.j2"

    raise RenderError(f"unable to infer template for manifest kind: {kind!r}")


ARC_SECTION = re.compile(r"(?ms)^## 3\..*?(?=^## |\Z)")
TABLE_SEPARATOR = re.compile(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?")


class ArcTableMissingError(RenderError):
    """The pinned arc source has no system-or-chunk table (its section 3)."""


def _arc_table(arc_source: str, path: str) -> str:
    """The system-or-chunk table of the arc source (the tables in its section 3), nothing else.

    Each arc document keeps that table under its ``## 3.`` heading. A source without the
    section, or a section without a table, is refused by name: the reviewer never receives
    another part of the document, so another module's content cannot arrive with it.
    """
    section = ARC_SECTION.search(arc_source)
    if section is None:
        raise ArcTableMissingError(f"the arc source {path} has no section 3 (system or chunk table)")
    tables: list[list[str]] = []
    current: list[str] = []
    for line in [*section.group(0).splitlines(), ""]:
        if line.lstrip().startswith("|"):
            current.append(line.strip())
        elif current:
            tables.append(current)
            current = []
    rendered = [
        "\n".join(rows)
        for rows in tables
        if len(rows) >= 3 and TABLE_SEPARATOR.fullmatch(rows[1].strip().replace(" ", ""))
    ]
    if not rendered:
        raise ArcTableMissingError(f"section 3 of the arc source {path} holds no table")
    return "\n\n".join(rendered)


def _neighbour_positions(arc: Any, position: Any) -> list[Any]:
    positions = arc.get("positions", []) if isinstance(arc, dict) else []
    if position is None:
        return positions
    return [
        item
        for item in positions
        if isinstance(item, dict)
        and isinstance(item.get("position"), int)
        and abs(item["position"] - int(position)) <= 1
    ]


def _learner_state_context(reader: ManifestReader, manifest: dict[str, Any]) -> dict[str, Any]:
    text = reader.pin_text("inputs.learner_state")
    document = yaml.safe_load(text)
    if not isinstance(document, dict) or "learner_state" not in document:
        raise RenderError(f"{reader.pin('inputs.learner_state')['path']} holds no learner_state")
    identity = learner_state_sha256(SimpleNamespace(to_dict=lambda: document["learner_state"]))
    recorded = (manifest.get("learner_state") or {}).get("sha256")
    if recorded != identity:
        raise LearnerStateMismatchError(
            f"learner state hashes to {identity}, the manifest records {recorded}: {reader.pin('inputs.learner_state')['path']}"
        )
    context = {
        "learner_state_sha256": identity,
        "learner_state_yaml": dump_yaml(document["learner_state"]),
    }
    if manifest.get("kind") == "lesson":
        if "immersion" not in document:
            raise RenderError(f"{reader.pin('inputs.learner_state')['path']} holds no immersion rule")
        context["immersion_yaml"] = dump_yaml(document["immersion"])
    return context


def _lesson_context(reader: ManifestReader, manifest: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    plan = reader.pin_yaml("inputs.plan")
    entry = next((row for row in plan.get("lessons", []) if row.get("n") == int(manifest["lesson"])), None)
    if entry is None:
        raise RenderError(f"the pinned plan has no lesson {manifest['lesson']}")
    context["lesson_plan_yaml"] = dump_yaml(entry)
    context["pack_text"] = reader.locked_text("inputs.pack", "inputs.pack_lock", PackLockMismatchError)
    context["words_text"] = reader.locked_text("inputs.words", "inputs.words_lock", WordsLockMismatchError)
    context.update(_learner_state_context(reader, manifest))
    context["lesson_content"] = reader.pin_text("inputs.lesson")
    context["activity_data_files"] = [
        {"path": item["path"], "content": reader.read_text(item["path"])}
        for item in manifest["inputs"].get("activity_data", [])
    ]
    context["gate_report_text"] = reader.pin_text("inputs.gate_report")
    context["style_card_content"] = reader.pin_text("inputs.style_card")
    context["module_digest_text"] = reader.pin_text("module_digest")
    if reader.has("inputs.decisions"):
        context["decisions_text"] = reader.pin_text("inputs.decisions")

    upstream = manifest.get("upstream_lessons") or []
    if manifest.get("recap"):
        if [row["n"] for row in upstream] != list(range(1, int(manifest["lesson"]))):
            raise RenderError("a recap manifest must pin the built lessons 1..N-1 as upstream_lessons")
        context["upstream_lessons"] = [
            {"n": row["n"], "path": row["path"], "content": reader.read_text(row["path"])} for row in upstream
        ]
    else:
        context["upstream_lessons"] = []

    context["previous_attempt_id"] = None
    if manifest.get("previous_attempt"):
        context["previous_attempt_id"] = manifest["previous_attempt"]["attempt_id"]
        context["diff_content"] = reader.pin_text("diff")
        previous = reader.pin_yaml("previous_attempt.review")
        context["previous_findings_yaml"] = dump_yaml(
            {"checks": previous.get("checks", {}), "findings": previous.get("findings", [])}
        )
    return context


def _plan_context(reader: ManifestReader, manifest: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {
        "plan_text": reader.pin_text("inputs.plan"),
        "pack_text": reader.locked_text("inputs.pack", "inputs.pack_lock", PackLockMismatchError),
        "words_text": reader.locked_text("inputs.words", "inputs.words_lock", WordsLockMismatchError),
        "requirements_text": reader.pin_text("inputs.requirements"),
        "arc_system_or_chunk_text": _arc_table(
            reader.pin_text("inputs.arc_source"), reader.pin("inputs.arc_source")["path"]
        ),
        "decisions_text": reader.pin_text("inputs.decisions"),
        "scope_text": reader.pin_text("inputs.scope"),
        "grammar_text": reader.pin_text("inputs.grammar"),
        "validate_report_text": reader.pin_text("inputs.validate_report"),
        "pack_verify_report_text": reader.pin_text("inputs.pack_verify_report"),
    }
    context.update(_learner_state_context(reader, manifest))
    arc = reader.pin_yaml("inputs.arc")
    context["arc_positions_yaml"] = dump_yaml(_neighbour_positions(arc, manifest.get("position")))
    return context


def _build_context(manifest: dict[str, Any], manifest_sha256: str, reader: ManifestReader) -> dict[str, Any]:
    kind = manifest.get("kind")
    missing = [location for location in REQUIRED_PINS.get(str(kind), ()) if not reader.has(location)]
    if missing:
        raise RenderError(f"manifest names no {', '.join(missing)} input")
    context: dict[str, Any] = {
        "manifest": manifest,
        "manifest_sha256": manifest_sha256,
        "review_tools": sorted(REVIEW_TOOLS),
    }
    if kind == "lesson":
        context.update(_lesson_context(reader, manifest))
    elif kind == "plan":
        context.update(_plan_context(reader, manifest))
    return context


def render_prompt(
    manifest_source: Path | str | dict[str, Any],
    template_name: str | None = None,
    *,
    repo_root: Path | None = None,
    output_path: Path | None = None,
    prompts_dir: Path | None = None,
) -> tuple[str, str, list[Path]]:
    """Render a reviewer prompt from manifest inputs and write prompt sha256 beside it.

    Returns:
        tuple[rendered_prompt, prompt_sha256, files_read]
    """
    root = (repo_root or REPO_ROOT).resolve()
    p_dir = (prompts_dir or PROMPTS_DIR).resolve()

    if isinstance(manifest_source, (str, Path)):
        mpath = (root / manifest_source).resolve() if not Path(manifest_source).is_absolute() else Path(manifest_source)
        manifest_bytes = mpath.read_bytes()
        manifest_sha256 = compute_sha256(manifest_bytes)
        manifest_doc = yaml.safe_load(manifest_bytes.decode("utf-8"))
    elif isinstance(manifest_source, dict):
        manifest_doc = manifest_source
        manifest_bytes = yaml.safe_dump(manifest_doc, allow_unicode=False, sort_keys=True).encode("utf-8")
        manifest_sha256 = manifest_doc.get("manifest_sha256") or compute_sha256(manifest_bytes)
    else:
        raise RenderError(f"invalid manifest source: {type(manifest_source)}")

    reader = ManifestReader(manifest_doc, repo_root=root)
    resolved_template = resolve_template_name(manifest_doc, template_name)

    env = Environment(
        loader=FileSystemLoader(str(p_dir)),
        undefined=StrictUndefined,
        autoescape=jinja2.select_autoescape(
            enabled_extensions=("html", "htm", "xml"), default_for_string=False, default=False
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["fence"] = data_fence
    env.globals["fence"] = data_fence
    env.filters["data_fence"] = data_fence
    env.globals["data_fence"] = data_fence

    try:
        tmpl = env.get_template(resolved_template)
    except jinja2.TemplateNotFound as exc:
        raise RenderError(f"template not found in {p_dir.as_posix()}: {resolved_template}") from exc

    context = _build_context(manifest_doc, manifest_sha256, reader)
    rendered = tmpl.render(**context)

    prompt_sha256 = compute_sha256(rendered.encode("utf-8"))

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        sidecar = out.with_name(f"{out.name}.sha256")
        sidecar.write_text(f"{prompt_sha256}\n", encoding="ascii")
        files_read_sidecar = out.with_name(f"{out.name}.files_read.json")
        rel_files: list[str] = []
        for f in reader.files_read:
            try:
                rel_files.append(f.relative_to(root).as_posix())
            except ValueError:
                rel_files.append(f.as_posix())
        read_record = {"files_read": rel_files, "verifier_reads": []}  # the checker records what verification read
        files_read_sidecar.write_text(json.dumps(read_record, indent=2) + "\n", encoding="utf-8")

    return rendered, prompt_sha256, list(reader.files_read)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render reviewer prompt from manifest inputs.")
    parser.add_argument("manifest", help="Path to attempt manifest YAML")
    parser.add_argument("--template", "-t", default=None, help="Template name (default inferred)")
    parser.add_argument("--output", "-o", default=None, help="Output prompt path")
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    args = parser.parse_args(argv)

    root = Path(args.repo_root) if args.repo_root else REPO_ROOT
    out = Path(args.output) if args.output else None

    rendered, prompt_sha256, _ = render_prompt(
        args.manifest,
        template_name=args.template,
        repo_root=root,
        output_path=out,
    )

    if out:
        print(f"Prompt written: {out} ({prompt_sha256})")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
