"""Plateau-triggered plan patching via Gemini.

This phase reads structured review outputs from the review loop, extracts the
recurring structural complaints, and asks Gemini for a minimal structured plan
patch. The patch is applied locally with the project's existing plan versioning
conventions: ``.bak`` backup, patch-version bump, and ``plan_fixes`` changelog.
"""

from __future__ import annotations

import copy
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from batch_gemini_config import PRO_MODEL
from gemini_output import extract_delimited
from tools.plan_autofix import _bump_version

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
PLAN_PATCH_TAG = "PLAN_PATCH"


@dataclass(frozen=True)
class PlanPatchResult:
    """Outcome of the plateau-triggered plan patch attempt."""

    applied: bool
    reason: str
    complaint_summary: str
    change_count: int = 0
    new_version: str | None = None
    changes: tuple[str, ...] = ()


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[\w-]*\n?", "", stripped)
        stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9а-яіїєґ]+", " ", text.lower())).strip()


def load_structured_review_rounds(orch_dir: Path) -> list[dict]:
    """Load structured review round YAML artifacts saved by v6_build."""
    rounds: list[dict] = []
    for path in sorted(orch_dir.glob("review-structured-r*.yaml")):
        try:
            data = yaml.safe_load(path.read_text("utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            rounds.append(data)
    return rounds


def extract_plateau_complaints(
    structured_rounds: list[dict],
    *,
    review_target_score: float = 9.0,
    max_items: int = 6,
) -> list[dict]:
    """Aggregate the recurring complaints that caused the review plateau."""
    complaints: dict[str, dict[str, Any]] = {}

    for fallback_round_num, round_data in enumerate(structured_rounds, start=1):
        round_num = int(round_data.get("round") or fallback_round_num)

        for finding in round_data.get("findings") or []:
            if not isinstance(finding, dict):
                continue
            issue = str(finding.get("issue") or "").strip()
            if not issue:
                continue
            dimension = str(finding.get("dimension") or "").strip()
            location = str(finding.get("location") or "").strip()
            fix = str(finding.get("fix") or "").strip()
            key = "finding|" + "|".join(
                _normalize_text(part) for part in (dimension, location, issue)
            )
            entry = complaints.setdefault(
                key,
                {
                    "source": "finding",
                    "dimension": dimension,
                    "location": location,
                    "issue": issue,
                    "fix": fix,
                    "summary": issue,
                    "rounds": [],
                },
            )
            entry["rounds"].append(round_num)

        for score in round_data.get("scores") or []:
            if not isinstance(score, dict):
                continue
            try:
                score_value = float(score.get("score") or 0)
            except (TypeError, ValueError):
                continue
            evidence = str(score.get("evidence") or "").strip()
            if score_value >= review_target_score or not evidence:
                continue
            dimension = str(score.get("name") or score.get("dimension") or "").strip()
            key = "score|" + "|".join(_normalize_text(part) for part in (dimension, evidence))
            entry = complaints.setdefault(
                key,
                {
                    "source": "score",
                    "dimension": dimension,
                    "location": "",
                    "issue": evidence,
                    "fix": "",
                    "summary": f"{dimension}: {evidence}" if dimension else evidence,
                    "rounds": [],
                },
            )
            entry["rounds"].append(round_num)

    ranked = list(complaints.values())
    recurrent = [entry for entry in ranked if len(set(entry["rounds"])) >= 2]
    chosen = recurrent or ranked
    chosen.sort(
        key=lambda entry: (
            -len(set(entry["rounds"])),
            0 if entry["source"] == "finding" else 1,
            entry["summary"],
        )
    )

    trimmed: list[dict] = []
    for entry in chosen[:max_items]:
        normalized = dict(entry)
        normalized["rounds"] = sorted(set(int(r) for r in entry["rounds"]))
        trimmed.append(normalized)
    return trimmed


def summarize_complaints(complaints: list[dict]) -> str:
    """Build a short human-readable plateau trigger summary."""
    if not complaints:
        return "No recurring structured review complaint was available."
    lead = complaints[0]
    rounds = ",".join(str(r) for r in lead.get("rounds") or [])
    suffix = ""
    if len(complaints) > 1:
        suffix = f" (+{len(complaints) - 1} related complaint(s))"
    return f"Rounds {rounds}: {lead.get('summary', '').strip()}{suffix}"


def build_plan_patch_prompt(
    *,
    level: str,
    slug: str,
    plan_text: str,
    complaints: list[dict],
    score_history: list[float],
    contract_violations: list[dict],
) -> str:
    """Build the Gemini prompt for a minimal structured plan patch."""
    complaint_lines = []
    for complaint in complaints:
        rounds = ", ".join(str(r) for r in complaint.get("rounds") or [])
        location = complaint.get("location") or "(not specified)"
        fix = complaint.get("fix") or "(none supplied)"
        complaint_lines.append(
            f"- Rounds {rounds} | {complaint.get('dimension') or 'Review issue'} | "
            f"Location: {location}\n"
            f"  Issue: {complaint.get('issue')}\n"
            f"  Suggested fix: {fix}"
        )

    contract_lines = []
    for violation in contract_violations[:8]:
        if not isinstance(violation, dict):
            continue
        contract_lines.append(
            f"- [{violation.get('type', 'CONTRACT')}] {violation.get('message', '')}"
        )

    return (
        "You are patching a curriculum plan after the content review loop plateaued.\n\n"
        "Task: propose the MINIMAL plan diff that removes an unreachable constraint or "
        "rephrases it so the writer can satisfy the recurring review complaint.\n\n"
        "Rules:\n"
        "- Do NOT change module identity, slug, level, sequence, or thresholds.\n"
        "- Do NOT add a new workflow or mention humans.\n"
        "- Prefer small edits to content_outline points, dialogue_situations, activity_hints focus, "
        "or other specific constraints already in the plan.\n"
        "- Keep the patch minimal and human-readable.\n"
        "- Output ONLY one YAML document between the required delimiters.\n"
        "- If the plan is already correct and the plateau is purely prose-level, return decision: noop.\n\n"
        f"Module: {level}/{slug}\n"
        f"Score history: {', '.join(f'{score:.1f}' for score in score_history)}\n\n"
        "Recurring complaints:\n"
        f"{chr(10).join(complaint_lines) if complaint_lines else '- (none)'}\n\n"
        "Current contract violations at plateau:\n"
        f"{chr(10).join(contract_lines) if contract_lines else '- (none)'}\n\n"
        "Current plan YAML:\n"
        "```yaml\n"
        f"{plan_text.strip()}\n"
        "```\n\n"
        "Allowed patch operations:\n"
        "- action: replace   path: nested.path[0].field   value: <scalar/list/dict>\n"
        "- action: append    path: nested.list            value: <item>\n"
        "- action: remove    path: nested.path[0].field\n\n"
        "Required output schema:\n"
        f"==={PLAN_PATCH_TAG}_START===\n"
        "decision: patch|noop\n"
        "complaint_summary: short sentence naming the recurring complaint\n"
        "rationale: one short paragraph\n"
        "changes:\n"
        "  - path: content_outline[1].points[0]\n"
        "    action: replace\n"
        "    value: Updated point text\n"
        "    reason: Why this plan edit removes the complaint\n"
        f"==={PLAN_PATCH_TAG}_END===\n"
    )


def _dispatch_gemini_plan_patch(prompt: str, *, task_id: str, model: str = PRO_MODEL) -> tuple[bool, str]:
    """Dispatch the plan-patch prompt through ai_agent_bridge/Gemini."""
    cmd = [
        str(VENV_PYTHON),
        str(SCRIPTS_DIR / "ai_agent_bridge" / "__main__.py"),
        "ask-gemini",
        "-",
        "--task-id",
        task_id,
        "--model",
        model,
        "--stdout-only",
        "--no-github",
    ]
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=1800,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        return False, ""

    if result.returncode != 0:
        return False, result.stdout + result.stderr
    return True, result.stdout


def parse_plan_patch_response(raw_output: str) -> dict | None:
    """Parse the structured Gemini plan-patch payload."""
    extracted = extract_delimited(raw_output, PLAN_PATCH_TAG)
    if extracted is None:
        extracted = raw_output
    cleaned = _strip_code_fence(extracted)
    if not cleaned:
        return None
    try:
        data = yaml.safe_load(cleaned)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _parse_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for chunk in path.split("."):
        if not chunk:
            raise ValueError(f"Invalid patch path: {path!r}")
        key_match = re.match(r"^[^\[]+", chunk)
        if key_match:
            tokens.append(key_match.group(0))
        for index_match in re.finditer(r"\[(\d+)\]", chunk):
            tokens.append(int(index_match.group(1)))
    return tokens


def _descend(target: Any, token: str | int) -> Any:
    if isinstance(token, int):
        if not isinstance(target, list):
            raise TypeError(f"Expected list before index [{token}]")
        return target[token]
    if not isinstance(target, dict):
        raise TypeError(f"Expected dict before key {token!r}")
    return target[token]


def _set_path(root: Any, path: str, *, action: str, value: Any = None) -> None:
    tokens = _parse_path(path)
    if not tokens:
        raise ValueError("Patch path cannot be empty")

    if action == "append":
        container = root
        for token in tokens:
            container = _descend(container, token)
        if not isinstance(container, list):
            raise TypeError(f"append requires a list target: {path}")
        container.append(value)
        return

    parent = root
    for token in tokens[:-1]:
        parent = _descend(parent, token)
    leaf = tokens[-1]

    if isinstance(leaf, int):
        if not isinstance(parent, list):
            raise TypeError(f"Expected list parent for index [{leaf}]")
        if action == "replace":
            parent[leaf] = value
        elif action == "remove":
            parent.pop(leaf)
        else:
            raise ValueError(f"Unsupported action: {action}")
        return

    if not isinstance(parent, dict):
        raise TypeError(f"Expected dict parent for key {leaf!r}")
    if action == "replace":
        parent[leaf] = value
    elif action == "remove":
        parent.pop(leaf, None)
    else:
        raise ValueError(f"Unsupported action: {action}")


def _change_summary(change: dict) -> str:
    action = str(change.get("action") or "replace")
    path = str(change.get("path") or "")
    reason = str(change.get("reason") or "").strip()
    summary = f"{action} {path}"
    if reason:
        summary += f" — {reason}"
    return summary


def apply_plan_patch_response(
    plan_path: Path,
    response: dict,
    *,
    complaint_summary: str,
) -> PlanPatchResult:
    """Apply the structured plan patch and persist versioned YAML."""
    if not plan_path.exists():
        return PlanPatchResult(
            applied=False,
            reason=f"Plan not found: {plan_path}",
            complaint_summary=complaint_summary,
        )

    decision = str(response.get("decision") or "noop").strip().lower()
    if decision != "patch":
        return PlanPatchResult(
            applied=False,
            reason="Gemini declined to patch the plan",
            complaint_summary=str(response.get("complaint_summary") or complaint_summary),
        )

    changes = response.get("changes")
    if not isinstance(changes, list) or not changes:
        return PlanPatchResult(
            applied=False,
            reason="Gemini returned no structured plan changes",
            complaint_summary=str(response.get("complaint_summary") or complaint_summary),
        )

    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    if not isinstance(plan, dict):
        return PlanPatchResult(
            applied=False,
            reason="Plan YAML root is not a mapping",
            complaint_summary=str(response.get("complaint_summary") or complaint_summary),
        )

    updated = copy.deepcopy(plan)
    summaries: list[str] = []
    for raw_change in changes:
        if not isinstance(raw_change, dict):
            return PlanPatchResult(
                applied=False,
                reason="Gemini returned a non-object change entry",
                complaint_summary=str(response.get("complaint_summary") or complaint_summary),
            )
        path = str(raw_change.get("path") or "").strip()
        action = str(raw_change.get("action") or "replace").strip().lower()
        if not path or action not in {"replace", "append", "remove"}:
            return PlanPatchResult(
                applied=False,
                reason=f"Unsupported structured change: {raw_change}",
                complaint_summary=str(response.get("complaint_summary") or complaint_summary),
            )
        try:
            _set_path(updated, path, action=action, value=raw_change.get("value"))
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            return PlanPatchResult(
                applied=False,
                reason=f"Could not apply change '{path}': {exc}",
                complaint_summary=str(response.get("complaint_summary") or complaint_summary),
            )
        summaries.append(_change_summary(raw_change))

    old_version = str(updated.get("version", "1.0"))
    new_version = _bump_version(old_version)
    updated["version"] = new_version

    fix_entry = {
        "version": new_version,
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "trigger": str(response.get("complaint_summary") or complaint_summary),
        "changes": summaries,
    }
    if "plan_fixes" not in updated or not isinstance(updated.get("plan_fixes"), list):
        updated["plan_fixes"] = []
    updated["plan_fixes"].append(fix_entry)

    backup_path = plan_path.with_suffix(".yaml.bak")
    shutil.copy2(plan_path, backup_path)
    plan_path.write_text(
        yaml.safe_dump(updated, allow_unicode=True, sort_keys=False),
        "utf-8",
    )

    return PlanPatchResult(
        applied=True,
        reason="patched",
        complaint_summary=str(response.get("complaint_summary") or complaint_summary),
        change_count=len(summaries),
        new_version=new_version,
        changes=tuple(summaries),
    )


def run_plan_patch(
    *,
    level: str,
    slug: str,
    plan_path: Path,
    orch_dir: Path,
    score_history: list[float],
    contract_violations: list[dict],
    round_window: int | None = None,
) -> PlanPatchResult:
    """Run the full plateau -> Gemini patch -> local apply flow."""
    structured_rounds = load_structured_review_rounds(orch_dir)
    if round_window:
        structured_rounds = structured_rounds[-round_window:]
    complaints = extract_plateau_complaints(structured_rounds)
    complaint_summary = summarize_complaints(complaints)
    if not complaints:
        return PlanPatchResult(
            applied=False,
            reason="No structured plateau complaints found",
            complaint_summary=complaint_summary,
        )

    plan_text = plan_path.read_text("utf-8")
    prompt = build_plan_patch_prompt(
        level=level,
        slug=slug,
        plan_text=plan_text,
        complaints=complaints,
        score_history=score_history,
        contract_violations=contract_violations,
    )
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "v6-plan-patch-prompt.md").write_text(prompt, "utf-8")

    ok, raw_output = _dispatch_gemini_plan_patch(
        prompt,
        task_id=f"plan-patch-{level}-{slug}",
    )
    (orch_dir / "v6-plan-patch-output.md").write_text(raw_output or "", "utf-8")
    if not ok:
        return PlanPatchResult(
            applied=False,
            reason="Gemini plan-patch dispatch failed",
            complaint_summary=complaint_summary,
        )

    response = parse_plan_patch_response(raw_output)
    if response is None:
        return PlanPatchResult(
            applied=False,
            reason="Gemini returned no parseable plan-patch payload",
            complaint_summary=complaint_summary,
        )

    parsed_path = orch_dir / "v6-plan-patch-response.yaml"
    parsed_path.write_text(
        yaml.safe_dump(response, allow_unicode=True, sort_keys=False),
        "utf-8",
    )
    return apply_plan_patch_response(
        plan_path,
        response,
        complaint_summary=complaint_summary,
    )
