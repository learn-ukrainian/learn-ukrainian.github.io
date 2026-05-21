"""V7 run archive preservation helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline

ENV_KEY = "V7_RUN_ARCHIVE_CONTEXT"

_PASSTHROUGH_ARTIFACTS = (
    "writer_output.raw.md",
    "knowledge_packet.md",
    "wiki_manifest.json",
    "implementation_map.json",
    "writer_tool_calls.json",
    "module.md",
    "activities.yaml",
    "vocabulary.yaml",
    "resources.yaml",
    "python_qg.json",
    "wiki_coverage_gate.json",
    "wiki_coverage_review.json",
    "llm_qg.json",
)
_RENAMED_ARTIFACTS = {
    "writer_prompt.md": "v7-writer-prompt.md",
}
_ARTIFACT_GLOBS = (
    "python_qg_correction_r*.json",
    "wiki_coverage_correction_r*.json",
    "llm-qg-*-prompt.md",
    "llm-qg-*-response.raw.md",
    "wiki-coverage-review-prompt.md",
    "wiki-coverage-review-response.raw.md",
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def archive_dir_for(
    project_root: Path,
    *,
    level: str,
    slug: str,
    run_id: str,
) -> Path:
    return (
        project_root
        / "curriculum"
        / "l2-uk-en"
        / "_orchestration"
        / level.lower()
        / slug
        / "runs"
        / run_id
    )


def _latest_parent_run_id(project_root: Path, *, level: str, slug: str) -> str | None:
    runs_root = (
        project_root
        / "curriculum"
        / "l2-uk-en"
        / "_orchestration"
        / level.lower()
        / slug
        / "runs"
    )
    if not runs_root.exists():
        return None
    run_ids = sorted(path.name for path in runs_root.iterdir() if path.is_dir())
    return run_ids[-1] if run_ids else None


def parse_git_diff_stat(
    raw: str,
    *,
    run_id: str,
    parent_run_id: str | None,
    base_ref: str,
    head_ref: str,
) -> dict[str, Any]:
    lines = [line.rstrip() for line in raw.splitlines() if line.strip()]
    summary = lines[-1] if lines else ""
    path_lines = lines[:-1] if summary and "changed" in summary else lines

    files_changed = _summary_int(summary, r"(\d+)\s+files?\s+changed")
    insertions = _summary_int(summary, r"(\d+)\s+insertions?\(\+\)")
    deletions = _summary_int(summary, r"(\d+)\s+deletions?\(-\)")
    paths: list[dict[str, Any]] = []
    for line in path_lines:
        if "|" not in line:
            continue
        path_part, stat_part = line.rsplit("|", 1)
        path = path_part.strip()
        added = stat_part.count("+")
        removed = stat_part.count("-")
        status = "modified"
        if added and not removed:
            status = "added"
        elif removed and not added:
            status = "deleted"
        paths.append(
            {
                "path": path,
                "status": status,
                "insertions": added,
                "deletions": removed,
            }
        )

    return {
        "run_id": run_id,
        "parent_run_id": parent_run_id,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
        "paths": paths,
    }


def _summary_int(summary: str, pattern: str) -> int:
    match = re.search(pattern, summary)
    return int(match.group(1)) if match else 0


def _with_failed_frontmatter(mdx: str, *, failed_phase: str | None) -> str:
    phase = failed_phase or "unknown"
    if not mdx.startswith("---\n"):
        return f"---\nbuild_status: failed\nfailed_phase: {phase}\n---\n\n{mdx}"
    end = mdx.find("\n---", 4)
    if end == -1:
        return f"---\nbuild_status: failed\nfailed_phase: {phase}\n---\n\n{mdx}"
    frontmatter = mdx[4:end].splitlines()
    body = mdx[end + len("\n---") :]
    filtered = [
        line
        for line in frontmatter
        if not line.startswith("build_status:") and not line.startswith("failed_phase:")
    ]
    filtered.extend(["build_status: failed", f"failed_phase: {phase}"])
    return "---\n" + "\n".join(filtered).rstrip() + "\n---" + body


@dataclass(slots=True)
class RunArchive:
    project_root: Path
    worktree_path: Path
    archive_dir: Path
    level: str
    slug: str
    run_id: str
    parent_run_id: str | None
    base_ref: str

    @classmethod
    def start(
        cls,
        *,
        project_root: Path,
        worktree_path: Path,
        level: str,
        slug: str,
        run_id: str,
        writer: str,
        model: str,
        effort: str,
        prompt_sha: str | None,
        base_ref: str,
    ) -> RunArchive:
        project_root = project_root.resolve()
        worktree_path = worktree_path.resolve()
        level = level.lower()
        parent_run_id = _latest_parent_run_id(project_root, level=level, slug=slug)
        archive_dir = archive_dir_for(
            project_root,
            level=level,
            slug=slug,
            run_id=run_id,
        )
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive = cls(
            project_root=project_root,
            worktree_path=worktree_path,
            archive_dir=archive_dir,
            level=level,
            slug=slug,
            run_id=run_id,
            parent_run_id=parent_run_id,
            base_ref=base_ref,
        )
        archive._write_state(
            {
                "mode": "v7",
                "track": level,
                "slug": slug,
                "run_id": run_id,
                "parent_run_id": parent_run_id,
                "started_at": utc_now(),
                "finished_at": None,
                "status": "partial",
                "failed_phase": None,
                "failure_class": None,
                "agent": writer,
                "model": model,
                "effort": effort,
                "prompt_sha": prompt_sha,
                "phases": {},
            }
        )
        return archive

    @classmethod
    def from_env(cls) -> RunArchive | None:
        raw = os.environ.get(ENV_KEY)
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        archive_dir = Path(str(data["archive_dir"])).resolve()
        return cls(
            project_root=Path(str(data["project_root"])).resolve(),
            worktree_path=Path(str(data["worktree_path"])).resolve(),
            archive_dir=archive_dir,
            level=str(data["level"]).lower(),
            slug=str(data["slug"]),
            run_id=str(data["run_id"]),
            parent_run_id=data.get("parent_run_id"),
            base_ref=str(data.get("base_ref") or "HEAD"),
        )

    def env(self) -> dict[str, str]:
        return {
            ENV_KEY: json.dumps(
                {
                    "project_root": str(self.project_root),
                    "worktree_path": str(self.worktree_path),
                    "archive_dir": str(self.archive_dir),
                    "level": self.level,
                    "slug": self.slug,
                    "run_id": self.run_id,
                    "parent_run_id": self.parent_run_id,
                    "base_ref": self.base_ref,
                },
                ensure_ascii=False,
            )
        }

    @property
    def state_path(self) -> Path:
        return self.archive_dir / "state.json"

    def phase_started(self, phase: str) -> None:
        state = self._state()
        phases = state.setdefault("phases", {})
        phase_state = phases.setdefault(phase, {})
        phase_state.setdefault("started_at", utc_now())
        phase_state["status"] = "running"
        phase_state.setdefault("attempts", 0)
        phase_state.setdefault("artifacts", [])
        self._write_state(state)

    def phase_succeeded(
        self,
        phase: str,
        *,
        artifact_dir: Path | None = None,
        extra_paths: list[Path] | None = None,
        fields: dict[str, Any] | None = None,
    ) -> None:
        artifacts = self.copy_artifacts(artifact_dir, extra_paths=extra_paths)
        state = self._state()
        phases = state.setdefault("phases", {})
        phase_state = phases.setdefault(phase, {})
        phase_state.setdefault("started_at", utc_now())
        phase_state["finished_at"] = utc_now()
        phase_state["status"] = "complete"
        phase_state["attempts"] = self._phase_attempts(phase)
        phase_state["artifacts"] = sorted(set(phase_state.get("artifacts", []) + artifacts))
        if fields:
            phase_state["fields"] = _jsonable(fields)
        self._write_state(state)

    def phase_failed(
        self,
        phase: str,
        *,
        artifact_dir: Path | None = None,
        failure_class: str | None = None,
        reason: str | None = None,
    ) -> None:
        artifacts = self.copy_artifacts(artifact_dir)
        state = self._state()
        phases = state.setdefault("phases", {})
        phase_state = phases.setdefault(phase, {})
        phase_state.setdefault("started_at", utc_now())
        phase_state["finished_at"] = utc_now()
        phase_state["status"] = "failed"
        phase_state["attempts"] = self._phase_attempts(phase)
        phase_state["artifacts"] = sorted(set(phase_state.get("artifacts", []) + artifacts))
        if reason:
            phase_state["reason"] = reason[:1000]
        state["status"] = "failed"
        state["failed_phase"] = phase
        state["failure_class"] = failure_class
        self._write_state(state)

    def copy_artifacts(
        self,
        artifact_dir: Path | None,
        *,
        extra_paths: list[Path] | None = None,
    ) -> list[str]:
        copied: list[str] = []
        if artifact_dir is not None and artifact_dir.exists():
            for source_name, dest_name in _RENAMED_ARTIFACTS.items():
                copied.extend(self._copy_one(artifact_dir / source_name, dest_name))
            for name in (*_PASSTHROUGH_ARTIFACTS, f"{self.slug}.mdx"):
                copied.extend(self._copy_one(artifact_dir / name, name))
            for pattern in _ARTIFACT_GLOBS:
                for path in sorted(artifact_dir.glob(pattern)):
                    copied.extend(self._copy_one(path, path.name))
        for path in extra_paths or []:
            copied.extend(self._copy_one(path, path.name))
        return copied

    def write_failed_mdx(
        self,
        *,
        module_dir: Path | None,
        plan_path: Path | None,
        failed_phase: str | None,
    ) -> Path | None:
        if module_dir is None or plan_path is None:
            return None
        output_path = self.archive_dir / f"{self.slug}.mdx"
        try:
            mdx = linear_pipeline.assemble_mdx(module_dir, output_path, plan_path)
            output_path.write_text(
                _with_failed_frontmatter(mdx, failed_phase=failed_phase),
                encoding="utf-8",
            )
            return output_path
        except Exception as exc:
            state = self._state()
            state["failed_mdx_error"] = str(exc)[:1000]
            self._write_state(state)
            return None

    def terminal(
        self,
        *,
        status: str,
        failed_phase: str | None = None,
        failure_class: str | None = None,
        artifact_dir: Path | None = None,
        extra_paths: list[Path] | None = None,
    ) -> None:
        self.copy_artifacts(artifact_dir, extra_paths=extra_paths)
        state = self._state()
        prior_failed_phase = state.get("failed_phase")
        state["status"] = status
        state["finished_at"] = utc_now()
        if status != "complete":
            state["failed_phase"] = failed_phase or prior_failed_phase or self._active_phase(state)
            state["failure_class"] = failure_class or state.get("failure_class")
        self._write_state(state)

    def write_commit_diff_summary(self, *, worktree_path: Path | None = None) -> None:
        worktree = worktree_path or self.worktree_path
        raw = ""
        head_ref = "HEAD"
        try:
            diff = subprocess.run(
                ["git", "-C", str(worktree), "diff", "--stat", "--no-ext-diff", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if diff.returncode == 0:
                raw = diff.stdout
            head = subprocess.run(
                ["git", "-C", str(worktree), "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if head.returncode == 0 and head.stdout.strip():
                head_ref = head.stdout.strip()
        except OSError:
            raw = ""
        summary = parse_git_diff_stat(
            raw,
            run_id=self.run_id,
            parent_run_id=self.parent_run_id,
            base_ref=self.base_ref,
            head_ref=head_ref,
        )
        _write_json(self.archive_dir / "commit_diff_summary.json", summary)

    def _copy_one(self, source: Path, dest_name: str) -> list[str]:
        if not source.exists() or not source.is_file():
            return []
        dest = self.archive_dir / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        return [dest_name]

    def _state(self) -> dict[str, Any]:
        return _read_json(self.state_path)

    def _write_state(self, state: dict[str, Any]) -> None:
        _write_json(self.state_path, state)

    def _phase_attempts(self, phase: str) -> int:
        if phase == "python_qg":
            return len(list(self.archive_dir.glob("python_qg_correction_r*.json")))
        if phase == "wiki_coverage_gate":
            return len(list(self.archive_dir.glob("wiki_coverage_correction_r*.json")))
        return 1

    def _active_phase(self, state: dict[str, Any]) -> str | None:
        phases = state.get("phases")
        if not isinstance(phases, dict):
            return None
        for phase, phase_state in reversed(list(phases.items())):
            if isinstance(phase_state, dict) and phase_state.get("status") == "running":
                return str(phase)
        return None
