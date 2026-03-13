"""Consultation result parser, template patcher, and approval queue.

Parses structured YAML from Gemini consultation output, applies
FIND/REPLACE patches to template copies, and queues cross-module
changes for human approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pipeline_lib import log

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TemplateChange:
    """A single FIND/REPLACE proposal for a template file."""
    find: str
    replace: str
    file: str
    rationale: str = ""


@dataclass
class ConsultationResult:
    """Parsed consultation output from Gemini."""
    root_cause: str
    proposed_changes: list[TemplateChange]
    scope: str          # "this_module" | "all_modules"
    action: str         # "rebuild" | "fix"
    confidence: str     # "high" | "medium" | "low"
    additional_notes: str = ""


# Required top-level keys in the consultation YAML
_REQUIRED_KEYS = {"root_cause", "proposed_changes", "scope", "action", "confidence"}
_VALID_SCOPES = {"this_module", "all_modules"}
_VALID_ACTIONS = {"rebuild", "fix"}
_VALID_CONFIDENCES = {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _clean_yaml_text(text: str) -> str:
    """Strip common LLM artifacts that break yaml.safe_load.

    Gemini often wraps YAML in markdown code fences or adds stray
    backticks. This pre-cleaning step handles those cases.
    """
    lines = text.strip().splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip markdown code fence markers
        if stripped.startswith("```"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def parse_consultation(text: str) -> ConsultationResult | None:
    """Parse consultation YAML text into a ConsultationResult.

    Returns None if the text is malformed or missing required fields.
    Applies LLM artifact cleaning before parsing.
    """
    if not text or not text.strip():
        log("  consultation-parse: empty text")
        return None

    cleaned = _clean_yaml_text(text)

    try:
        data = yaml.safe_load(cleaned)
    except yaml.YAMLError as e:
        log(f"  consultation-parse: YAML parse error: {e}")
        return None

    if not isinstance(data, dict):
        log(f"  consultation-parse: expected dict, got {type(data).__name__}")
        return None

    # Validate required fields
    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        log(f"  consultation-parse: missing required fields: {missing}")
        return None

    # Validate enum fields
    scope = str(data["scope"]).strip()
    if scope not in _VALID_SCOPES:
        log(f"  consultation-parse: invalid scope '{scope}', expected {_VALID_SCOPES}")
        return None

    action = str(data["action"]).strip()
    if action not in _VALID_ACTIONS:
        log(f"  consultation-parse: invalid action '{action}', expected {_VALID_ACTIONS}")
        return None

    confidence = str(data["confidence"]).strip()
    if confidence not in _VALID_CONFIDENCES:
        log(f"  consultation-parse: invalid confidence '{confidence}', expected {_VALID_CONFIDENCES}")
        return None

    # Parse proposed_changes
    raw_changes = data.get("proposed_changes")
    if not isinstance(raw_changes, list):
        log("  consultation-parse: proposed_changes must be a list")
        return None

    changes = []
    for i, change in enumerate(raw_changes):
        if not isinstance(change, dict):
            log(f"  consultation-parse: change #{i+1} is not a dict")
            return None
        find = str(change.get("find", "")).strip()
        replace = str(change.get("replace", "")).strip()
        file_name = str(change.get("file", "")).strip()
        if not find:
            log(f"  consultation-parse: change #{i+1} has empty 'find'")
            return None
        changes.append(TemplateChange(
            find=find,
            replace=replace,
            file=file_name,
            rationale=str(change.get("rationale", "")).strip(),
        ))

    return ConsultationResult(
        root_cause=str(data["root_cause"]).strip(),
        proposed_changes=changes,
        scope=scope,
        action=action,
        confidence=confidence,
        additional_notes=str(data.get("additional_notes", "")).strip(),
    )


# ---------------------------------------------------------------------------
# Template patching
# ---------------------------------------------------------------------------

def apply_template_patch(
    template_path: Path,
    changes: list[TemplateChange],
    output_path: Path,
) -> tuple[bool, int]:
    """Apply FIND/REPLACE changes to a template copy.

    Only applies changes whose `file` field matches the template filename.
    Uses exact match first, then whitespace-normalized fallback.
    Never modifies the original template — writes to output_path.

    Returns (success, num_applied). success is True even if 0 changes matched
    (that's not an error — the changes may target a different template).
    """
    if not template_path.exists():
        log(f"  consultation-patch: template not found: {template_path}")
        return False, 0

    template_name = template_path.name
    content = template_path.read_text("utf-8")
    applied = 0

    for i, change in enumerate(changes, 1):
        # Filter: only apply changes targeting this template
        if change.file and not _file_matches(change.file, template_name):
            continue

        find_text = change.find
        replace_text = change.replace

        if not find_text or find_text == replace_text:
            continue

        # Try exact match (replace first occurrence only)
        if find_text in content:
            content = content.replace(find_text, replace_text, 1)
            applied += 1
            log(f"  consultation-patch: change #{i} applied (exact match)")
            continue

        # Try whitespace-normalized fallback
        normalized_find = re.sub(r"\s+", " ", find_text).strip()
        normalized_content = re.sub(r"\s+", " ", content)
        norm_idx = normalized_content.find(normalized_find)

        if norm_idx >= 0:
            # Find the original span in the unnormalized content
            start, end = _find_normalized_span(content, normalized_find, norm_idx)
            if start is not None:
                content = content[:start] + replace_text + content[end:]
                applied += 1
                log(f"  consultation-patch: change #{i} applied (normalized match)")
                continue

        log(f"  consultation-patch: change #{i} skipped (no match in {template_name})")

    # Only write if changes were applied — a zero-change file would be
    # mistaken for a real patch by the "consultation-patched-*" detection.
    if applied > 0:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, "utf-8")

    return True, applied


def _file_matches(change_file: str, template_name: str) -> bool:
    """Check if a change's file field matches the template name.

    Accepts: exact name, path ending with name, or empty (matches all).
    """
    if not change_file:
        return True
    change_name = Path(change_file).name
    return change_name == template_name or template_name in change_file


def _find_normalized_span(
    content: str, normalized_find: str, idx: int,
) -> tuple[int | None, int | None]:
    """Find the original character span for a whitespace-normalized match.

    Maps from normalized string position back to original content positions.
    ``idx`` is the position of ``normalized_find`` in the already-normalized
    content (avoids re-normalizing).
    """
    # Map normalized index → original index
    # Walk through original content, tracking normalized position
    norm_pos = 0
    orig_start = None
    orig_end = None
    prev_was_space = False

    for orig_pos, ch in enumerate(content):
        if norm_pos == idx and orig_start is None:
            orig_start = orig_pos

        is_space = ch in (" ", "\t", "\n", "\r")
        if is_space:
            if not prev_was_space:
                norm_pos += 1
            prev_was_space = True
        else:
            norm_pos += 1
            prev_was_space = False

        if orig_start is not None and norm_pos >= idx + len(normalized_find):
            orig_end = orig_pos + 1
            break

    return orig_start, orig_end


# ---------------------------------------------------------------------------
# Approval queue
# ---------------------------------------------------------------------------

QUEUE_DIR = Path(__file__).resolve().parent.parent.parent / "claude_extensions" / "consultation-queue"


def queue_for_approval(
    result: ConsultationResult,
    slug: str,
    track: str,
    consultation_num: int,
    consultation_file: Path | None = None,
) -> Path:
    """Write a template change proposal to the approval queue.

    Returns the path to the queued file.
    """
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    timestamp = now.strftime("%Y%m%dT%H%M%S%f")
    queue_file = QUEUE_DIR / f"{timestamp}-{slug}.yaml"

    proposal = {
        "source_module": f"{track}/{slug}",
        "consultation_num": consultation_num,
        "confidence": result.confidence,
        "root_cause": result.root_cause,
        "proposed_changes": [
            {
                "find": c.find,
                "replace": c.replace,
                "file": c.file,
                "rationale": c.rationale,
            }
            for c in result.proposed_changes
        ],
        "additional_notes": result.additional_notes,
        "queued_at": now.isoformat(),
    }
    if consultation_file:
        proposal["source_file"] = str(consultation_file)

    queue_file.write_text(
        yaml.dump(proposal, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )
    return queue_file


# ---------------------------------------------------------------------------
# State tracking
# ---------------------------------------------------------------------------

def record_consultation(
    state: dict,
    num: int,
    result: ConsultationResult | None,
    outcome: str,
) -> None:
    """Record a consultation attempt in module state.

    outcome: "applied", "queued", "no_action", "no_match", "parse_failed"
    """
    consultations = state.setdefault("consultations", [])
    entry = {
        "num": num,
        "outcome": outcome,
        "ts": datetime.now(UTC).isoformat(),
    }
    if result:
        entry["scope"] = result.scope
        entry["action"] = result.action
        entry["confidence"] = result.confidence
        entry["changes_count"] = len(result.proposed_changes)
    consultations.append(entry)
