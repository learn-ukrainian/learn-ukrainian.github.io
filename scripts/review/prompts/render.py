"""Content-addressed reviewer prompt renderer (#8430 Part R2 item 1).

Renders reviewer prompts strictly from the inputs named and hashed by the review
attempt manifest (plan review, lesson review, lesson re-review, or settle).
Every file read is verified against its manifest sha256 before use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from scripts.review.receipts import REVIEW_TOOLS

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = Path(__file__).resolve().parent


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


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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
        text = yaml.safe_dump(content, allow_unicode=False, sort_keys=False)

    runs = re.findall(r"`+", text)
    max_run = max((len(r) for r in runs), default=0)
    fence = "`" * max(3, max_run + 1)
    body = text if text.endswith("\n") else text + "\n"
    tag = lang.strip()
    return f"{fence}{tag}\n{body}{fence}"


class ManifestReader:
    """Enforces that only manifest-declared files are read and verified."""

    def __init__(self, manifest: dict[str, Any], repo_root: Path):
        self.manifest = manifest
        self.repo_root = repo_root.resolve()
        self.allowed_paths: dict[Path, str] = {}
        self.files_read: list[Path] = []
        self._register_allowed_inputs()

    def _register_allowed_inputs(self) -> None:
        inputs = self.manifest.get("inputs", {})
        for _key, val in inputs.items():
            if isinstance(val, dict) and "path" in val and "sha256" in val:
                p = (self.repo_root / val["path"]).resolve()
                self.allowed_paths[p] = str(val["sha256"])
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and "path" in item and "sha256" in item:
                        p = (self.repo_root / item["path"]).resolve()
                        self.allowed_paths[p] = str(item["sha256"])

        # Top-level manifest files (module_digest, diff, previous_findings)
        # E3d: manifest["inputs"]["module_digest"]
        if "module_digest" in self.manifest and isinstance(self.manifest["module_digest"], dict):
            md = self.manifest["module_digest"]
            if "path" in md and "sha256" in md:
                p = (self.repo_root / md["path"]).resolve()
                self.allowed_paths[p] = str(md["sha256"])

        # E3d: manifest["inputs"]["diff"]
        if "diff_path" in self.manifest and "diff_sha256" in self.manifest:
            p = (self.repo_root / self.manifest["diff_path"]).resolve()
            self.allowed_paths[p] = str(self.manifest["diff_sha256"])

        # Pack and words locks authorize their corresponding unlocked data files
        # Verify the lock files first so we can register the unlocked targets
        if "pack_lock" in inputs and isinstance(inputs["pack_lock"], dict):
            # E3d: manifest["inputs"]["pack"]
            lock_rel = inputs["pack_lock"]["path"]
            lock_path = (self.repo_root / lock_rel).resolve()
            lock_bytes = self.read_bytes(lock_path)
            pack_sha = lock_bytes.decode("ascii").strip().split()[0]
            pack_path = Path(str(lock_path)[:-5]) if str(lock_path).endswith(".lock") else lock_path.with_suffix("")
            self.allowed_paths[pack_path] = pack_sha

        if "words_lock" in inputs and isinstance(inputs["words_lock"], dict):
            # E3d: manifest["inputs"]["words"]
            wlock_rel = inputs["words_lock"]["path"]
            wlock_path = (self.repo_root / wlock_rel).resolve()
            wlock_bytes = self.read_bytes(wlock_path)
            words_sha = wlock_bytes.decode("ascii").strip().split()[0]
            words_path = Path(str(wlock_path)[:-5]) if str(wlock_path).endswith(".lock") else wlock_path.with_suffix("")
            self.allowed_paths[words_path] = words_sha

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

    def read_yaml(self, target: Path | str) -> Any:
        return yaml.safe_load(self.read_text(target))

    def read_json(self, target: Path | str) -> Any:
        return json.loads(self.read_text(target))


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
        if manifest.get("previous_attempt") or manifest.get("diff_sha256"):
            return "lesson-rereview.md.j2"
        return "lesson-review.md.j2"
    if kind == "settle":
        return "settle.md.j2"

    raise RenderError(f"unable to infer template for manifest kind: {kind!r}")


def _build_context(manifest: dict[str, Any], manifest_sha256: str, reader: ManifestReader) -> dict[str, Any]:
    inputs = manifest.get("inputs", {})
    context: dict[str, Any] = {
        "manifest": manifest,
        "manifest_sha256": manifest_sha256,
        "review_tools": sorted(REVIEW_TOOLS),
    }

    # Load plan if present
    if "plan" in inputs:
        plan_doc = reader.read_yaml(inputs["plan"]["path"])
        context["plan"] = plan_doc
        context["plan_yaml"] = yaml.safe_dump(plan_doc, allow_unicode=False, sort_keys=False).strip()

        # For lesson review, extract lesson plan entry
        if "lesson" in manifest:
            lesson_n = int(manifest["lesson"])
            lessons = plan_doc.get("lessons", [])
            lesson_entry = next((item for item in lessons if item.get("n") == lesson_n), None)
            context["lesson_plan"] = lesson_entry
            context["lesson_plan_yaml"] = (
                yaml.safe_dump(lesson_entry, allow_unicode=False, sort_keys=False).strip()
                if lesson_entry is not None
                else ""
            )

    # Load decisions if present
    if "decisions" in inputs:
        decisions_doc = reader.read_yaml(inputs["decisions"]["path"])
        context["decisions"] = decisions_doc
        context["decisions_yaml"] = yaml.safe_dump(decisions_doc, allow_unicode=False, sort_keys=False).strip()

    # Load scope if present
    if "scope" in inputs:
        scope_doc = reader.read_yaml(inputs["scope"]["path"])
        context["scope"] = scope_doc
        context["scope_yaml"] = yaml.safe_dump(scope_doc, allow_unicode=False, sort_keys=False).strip()

    # Load arc if present
    if "arc" in inputs:
        arc_doc = reader.read_yaml(inputs["arc"]["path"])
        context["arc"] = arc_doc
        context["arc_yaml"] = yaml.safe_dump(arc_doc, allow_unicode=False, sort_keys=False).strip()

        # Contract 1: arc record of the position and its neighbours
        pos_num = manifest.get("position")
        if pos_num is None and "plan" in context and isinstance(context["plan"], dict):
            pos_num = context["plan"].get("arc_ref", {}).get("position")

        all_positions = arc_doc.get("positions", []) if isinstance(arc_doc, dict) else []
        if pos_num is not None:
            target_pos = int(pos_num)
            neighbour_positions = [
                p for p in all_positions if isinstance(p, dict) and abs(p.get("position", -999) - target_pos) <= 1
            ]
        else:
            neighbour_positions = all_positions

        context["arc_positions"] = neighbour_positions
        context["arc_positions_yaml"] = yaml.safe_dump(
            neighbour_positions, allow_unicode=False, sort_keys=False
        ).strip()

        # Arc system-or-chunk table
        soc_data = None
        if isinstance(arc_doc, dict):
            for k in ("system_or_chunk", "system_or_chunk_table", "chunks"):
                if k in arc_doc:
                    soc_data = arc_doc[k]
                    break
        if "system_or_chunk" in inputs:
            soc_data = reader.read_yaml(inputs["system_or_chunk"]["path"])
        elif "system_or_chunk" in manifest:
            soc_data = manifest["system_or_chunk"]

        if soc_data is not None:
            context["arc_system_or_chunk"] = soc_data
            context["arc_system_or_chunk_yaml"] = yaml.safe_dump(soc_data, allow_unicode=False, sort_keys=False).strip()
        else:
            context["arc_system_or_chunk"] = None
            context["arc_system_or_chunk_yaml"] = ""

    # Load requirements if present
    req_data = None
    if "requirements" in inputs:
        req_entry = inputs["requirements"]
        if isinstance(req_entry, dict) and "path" in req_entry:
            req_data = reader.read_yaml(req_entry["path"])
    elif "requirements" in manifest:
        req_data = manifest["requirements"]
    elif "plan" in context and isinstance(context["plan"], dict) and "requirements" in context["plan"]:
        req_data = context["plan"]["requirements"]
    elif "arc" in context and isinstance(context["arc"], dict) and "requirements" in context["arc"]:
        req_data = context["arc"]["requirements"]

    if req_data is not None:
        context["requirements"] = req_data
        context["requirements_yaml"] = (
            req_data.strip()
            if isinstance(req_data, str)
            else yaml.safe_dump(req_data, allow_unicode=False, sort_keys=False).strip()
        )
    else:
        context["requirements"] = None
        context["requirements_yaml"] = ""

    # Load grammar registry if present
    if "grammar" in inputs:
        grammar_doc = reader.read_yaml(inputs["grammar"]["path"])
        context["grammar"] = grammar_doc
        context["grammar_yaml"] = yaml.safe_dump(grammar_doc, allow_unicode=False, sort_keys=False).strip()

    # Load validate report if present
    if "validate_report" in inputs:
        val_doc = reader.read_json(inputs["validate_report"]["path"])
        context["validate_report"] = val_doc
        context["validate_report_json"] = json.dumps(val_doc, indent=2)
        context["validate_report_yaml"] = yaml.safe_dump(val_doc, allow_unicode=False, sort_keys=False).strip()

    # Load pack verify report if present
    if "pack_verify_report" in inputs:
        pv_doc = reader.read_json(inputs["pack_verify_report"]["path"])
        context["pack_verify_report"] = pv_doc
        context["pack_verify_report_json"] = json.dumps(pv_doc, indent=2)

    # Load pack records from pack locked by pack_lock
    # E3d: manifest["inputs"]["pack"]
    if "pack_lock" in inputs:
        lock_rel = inputs["pack_lock"]["path"]
        lock_path = (reader.repo_root / lock_rel).resolve()
        pack_path = Path(str(lock_path)[:-5]) if str(lock_path).endswith(".lock") else lock_path.with_suffix("")
        pack_doc = reader.read_yaml(pack_path)
        pack_records = pack_doc.get("records", []) if isinstance(pack_doc, dict) else pack_doc
        context["pack_records"] = pack_records
        context["pack_records_yaml"] = yaml.safe_dump(pack_records, allow_unicode=False, sort_keys=False).strip()

    # Load words from words locked by words_lock
    # E3d: manifest["inputs"]["words"]
    if "words_lock" in inputs:
        wlock_rel = inputs["words_lock"]["path"]
        wlock_path = (reader.repo_root / wlock_rel).resolve()
        words_path = Path(str(wlock_path)[:-5]) if str(wlock_path).endswith(".lock") else wlock_path.with_suffix("")
        words_doc = reader.read_yaml(words_path)
        words_list = words_doc.get("words", []) if isinstance(words_doc, dict) else words_doc
        context["words"] = words_list
        context["words_yaml"] = yaml.safe_dump(words_list, allow_unicode=False, sort_keys=False).strip()

    # Load lesson content if present
    if "lesson" in inputs:
        context["lesson_content"] = reader.read_text(inputs["lesson"]["path"])

    # Load activity data if present
    if "activity_data" in inputs:
        act_files = []
        for act in inputs["activity_data"]:
            if isinstance(act, dict) and "path" in act:
                act_files.append({"path": act["path"], "content": reader.read_text(act["path"])})
        context["activity_data_files"] = act_files

    # Load gate report if present
    if "gate_report" in inputs:
        gate_doc = reader.read_yaml(inputs["gate_report"]["path"])
        context["gate_report"] = gate_doc
        context["gate_report_yaml"] = yaml.safe_dump(gate_doc, allow_unicode=False, sort_keys=False).strip()

    # Load style card if present
    if "style_card" in inputs:
        context["style_card_content"] = reader.read_text(inputs["style_card"]["path"])

    # Load module digest if present
    # E3d: manifest["inputs"]["module_digest"]
    if "module_digest" in manifest and isinstance(manifest["module_digest"], dict):
        md = manifest["module_digest"]
        if "path" in md:
            digest_doc = reader.read_yaml(md["path"])
            context["module_digest"] = digest_doc
            context["module_digest_yaml"] = yaml.safe_dump(digest_doc, allow_unicode=False, sort_keys=False).strip()

    # Upstream lessons (for recap)
    # E3d: manifest["inputs"]["upstream_lessons"]
    context["upstream_lessons"] = manifest.get("upstream_lessons", [])

    # Learner state
    # E3d: manifest["inputs"]["learner_state"]
    l_state = manifest.get("learner_state", {})
    context["learner_state_sha256"] = l_state.get("sha256", "") if isinstance(l_state, dict) else ""

    # Re-review fields
    if "diff" in inputs:
        context["diff_content"] = reader.read_text(inputs["diff"]["path"])
        context["diff_sha256"] = str(inputs["diff"]["sha256"])
    elif manifest.get("diff_sha256"):
        context["diff_sha256"] = str(manifest["diff_sha256"])
        context["diff_content"] = ""

    if "previous_findings" in inputs:
        prev_doc = reader.read_yaml(inputs["previous_findings"]["path"])
        context["previous_findings"] = prev_doc
        context["previous_findings_yaml"] = yaml.safe_dump(prev_doc, allow_unicode=False, sort_keys=False).strip()

    context["previous_attempt_id"] = manifest.get("previous_attempt")

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
        files_read_sidecar.write_text(json.dumps(rel_files, indent=2) + "\n", encoding="utf-8")

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
