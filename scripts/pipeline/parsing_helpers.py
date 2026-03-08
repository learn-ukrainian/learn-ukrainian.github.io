"""Helper functions for pipeline/parsing.py — metrics, formatting, scanning.

Contains LLM filler scanning, metrics computation, audit failure extraction,
and formatting helpers. Review parsing and calibration live in parsing_review.py.
All functions are imported back into parsing.py for backward compatibility.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline_lib import ModuleContext, log

# Re-export review/calibration/quality-gate functions for backward compat
from pipeline.parsing_review import (  # noqa: F401
    _build_d3_context,
    _CALIBRATION_DIR,
    _get_russicism_table,
    _get_track_calibration,
    _parse_d1_review,
    _parse_factual_review,
    _quick_review_quality_gate,
)


# ---------------------------------------------------------------------------
# LLM filler scanner
# ---------------------------------------------------------------------------

_LLM_FILLER_DEFS: list[tuple[str, bool]] = [
    (r"\bIt'?s worth noting that\b", False),
    (r"\bThis is particularly important because\b", False),
    (r"\binterestingly\b", False),
    (r"\bOne of the key aspects\b", False),
    (r"\bLet'?s explore\b", False),
    (r"\bLet'?s dive in\b", False),
    (r"\bLet'?s take a closer look\b", False),
    (r"\bIn this lesson,? we will\b", True),
    (r"\bIn this module,? we will\b", True),
    (r"\bIn this (?:lesson|module|section),? we (?:will|are going to) (?:explore|learn|discover)\b", True),
    (r"\bIt is important to note\b", False),
    (r"\bNumbers are everywhere\b", False),
    (r"\bLanguage is not just about\b", False),
    (r"\bAs we'?ve seen\b", False),
    (r"\bAs you can see\b", False),
    (r"\bIn conclusion\b", False),
    (r"\bTo summarize\b", False),
    (r"\bThis brings us to\b", False),
    (r"\b\u0446\u0435 \u043d\u0435 \u043f\u0440\u043e\u0441\u0442\u043e\b.*?\b\u0430 \u0439\b", False),
    (r"\b\u0434\u0430\u0432\u0430\u0439\u0442\u0435 \u0440\u043e\u0437\u0433\u043b\u044f\u043d\u0435\u043c\u043e\b", False),
    (r"\b\u0434\u0430\u0432\u0430\u0439\u0442\u0435 \u0434\u0456\u0437\u043d\u0430\u0454\u043c\u043e\u0441\u044f\b", False),
    (r"\b\u0446\u0456\u043a\u0430\u0432\u043e,?\s+\u0449\u043e\b", False),
    (r"\b\u0432\u0430\u0440\u0442\u043e \u0437\u0430\u0437\u043d\u0430\u0447\u0438\u0442\u0438,?\s+\u0449\u043e\b", False),
    (r"\b\u0434\u0437\u0435\u0440\u043a\u0430\u043b\u043e\s+\u043a\u0443\u043b\u044c\u0442\u0443\u0440\u0438\b", False),
    (r"\b\u0430\u0440\u0445\u0456\u0442\u0435\u043a\u0442\u0443\u0440\u0430\s+\u043c\u043e\u0432\u0438\b", False),
    (r"\b\u0434\u0432\u0438\u0433\u0443\u043d\s+\u043f\u0440\u043e\u0433\u0440\u0435\u0441\u0443\b", False),
]
_LLM_FILLER_COMPILED: list[tuple[re.Pattern, bool]] = [
    (re.compile(p, re.IGNORECASE), always) for p, always in _LLM_FILLER_DEFS
]


def _scan_llm_filler(content: str) -> list[dict]:
    """Scan content for LLM filler PATTERNS -- repetition is the signal."""
    issues: list[dict] = []

    lines = content.split("\n")
    narrative_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(">") or stripped.startswith("```") or stripped.startswith("---"):
            continue
        narrative_lines.append((i + 1, line))

    narrative_text = "\n".join(line for _, line in narrative_lines)

    for pattern, always in _LLM_FILLER_COMPILED:
        matches = list(pattern.finditer(narrative_text))
        if len(matches) < 2 and not always:
            continue
        for m in matches:
            char_pos = m.start()
            narrative_idx = narrative_text[:char_pos].count("\n")
            if narrative_idx < len(narrative_lines):
                line_num = narrative_lines[narrative_idx][0]
            else:
                line_num = narrative_lines[-1][0] if narrative_lines else 1
            count_note = f" ({len(matches)}x)" if len(matches) >= 2 else ""
            issues.append({
                "type": "LLM_FILLER",
                "severity": "MEDIUM",
                "location": f"~line {line_num}",
                "text": m.group()[:80] + count_note,
                "fix": "Rephrase -- this phrase appears repeatedly (LLM pattern)" if len(matches) >= 2
                       else "Rephrase -- formulaic opener",
            })

    return issues


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def _read_content_body(content_path: Path | None) -> tuple[str, str, int]:
    """Read content file, strip frontmatter, compute word count.

    Returns (content, body, word_count).
    """
    from audit.cleaners import clean_for_stats, extract_core_content

    if not content_path or not content_path.exists():
        return "", "", 0

    content = content_path.read_text("utf-8")
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]

    core = extract_core_content(body)
    core_lines = [ln for ln in core.split("\n") if not ln.strip().startswith("|")]
    core_cleaned = clean_for_stats("\n".join(core_lines))
    word_count = len(core_cleaned.split())
    return content, body, word_count


def _count_yaml_items(path: Path | None) -> int:
    """Count items in a YAML file (list at root or nested under vocabulary/items)."""
    import yaml

    if not path or not path.exists():
        return 0
    try:
        data = yaml.safe_load(path.read_text("utf-8"))
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            vlist = data.get("vocabulary", data.get("items", []))
            if isinstance(vlist, list):
                return len(vlist)
    except Exception:
        pass
    return 0


def _compute_immersion_target(ctx: ModuleContext) -> str:
    """Compute the immersion target range string for a module."""
    from audit.config import get_a1_immersion_range, get_a2_immersion_range, get_b1_immersion_range

    level = ctx.track.split("-")[0].upper() if "-" not in ctx.track else ctx.track.upper()
    level_code = level[:2] if len(level) >= 2 else level
    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    try:
        if level_code == "A1":
            min_imm, max_imm = get_a1_immersion_range(module_num)
        elif level_code == "A2":
            min_imm, max_imm = get_a2_immersion_range(module_num)
        elif level_code == "B1":
            min_imm, max_imm = get_b1_immersion_range(module_num)
        else:
            min_imm, max_imm = 85, 95
    except Exception:
        min_imm, max_imm = 80, 95
    return f"{min_imm}-{max_imm}%"


def _compute_richness_metrics(
    content: str, content_path: Path, act_path: Path | None, track: str,
) -> dict[str, str]:
    """Compute richness score metrics. Returns partial metrics dict."""
    import yaml

    metrics: dict[str, str] = {}
    try:
        from calculate_richness import calculate_richness_score
        act_types = []
        if act_path and act_path.exists():
            try:
                act_data_rich = yaml.safe_load(act_path.read_text("utf-8"))
                if isinstance(act_data_rich, list):
                    act_types = [a.get("type", "") for a in act_data_rich if isinstance(a, dict)]
            except Exception:
                pass
        level_code_rich = track.split("-")[0].lower() if "-" not in track else track.lower()
        richness = calculate_richness_score(content, level_code_rich, str(content_path), act_types)
        metrics["COMPUTED_RICHNESS_SCORE"] = str(richness.get("score", 0))
        metrics["COMPUTED_RICHNESS_THRESHOLD"] = str(richness.get("threshold", 95))
        raw_rich = richness.get("raw", {})
        targets = richness.get("targets", {})
        gaps = []
        for dim, target in targets.items():
            actual = raw_rich.get(dim, 0)
            if actual < target:
                gaps.append(f"{dim}: {actual}/{target}")
        metrics["COMPUTED_RICHNESS_GAPS"] = ", ".join(gaps) if gaps else "none"
    except Exception:
        metrics["COMPUTED_RICHNESS_SCORE"] = "?"
        metrics["COMPUTED_RICHNESS_THRESHOLD"] = "?"
        metrics["COMPUTED_RICHNESS_GAPS"] = "?"
    return metrics


def _compute_metrics_direct(ctx: ModuleContext) -> dict[str, str]:
    """Compute audit metrics WITHOUT running the audit subprocess."""
    from audit.cleaners import calculate_immersion, clean_for_immersion

    metrics: dict[str, str] = {}
    content_path = ctx.paths.get("md")
    content, body, word_count = _read_content_body(content_path)

    word_target = getattr(ctx, "word_target", 0) or 0
    word_pct = (word_count / word_target * 100) if word_target else 0
    metrics["COMPUTED_WORD_COUNT"] = str(word_count)
    metrics["COMPUTED_WORD_TARGET"] = str(word_target)
    metrics["COMPUTED_WORD_PERCENT"] = f"{word_pct:.1f}"

    act_path = ctx.paths.get("activities")
    metrics["COMPUTED_ACTIVITY_COUNT"] = str(_count_yaml_items(act_path))

    vocab_path = ctx.paths.get("vocabulary")
    metrics["COMPUTED_VOCAB_COUNT"] = str(_count_yaml_items(vocab_path))

    engagement_pattern = re.compile(
        r'(>\s*[\U0001f4a1\u26a1\U0001f3ac\U0001f3ad\U0001f4dc\u2694\ufe0f\U0001f517\U0001f30d\U0001f381\U0001f5e3\ufe0f\U0001f3e0\U0001f9ed\U0001f68c\U0001f687\U0001f39f\ufe0f\U0001f4f1\U0001f575\ufe0f\U0001f324\ufe0f\U0001f326\ufe0f\U0001f3b1\U0001f52e\U0001f1fa\U0001f1e6\U0001f550\ufe0f\u2753\U0001f6e0\ufe0f\U0001f482\U0001f96a\U0001f37a\U0001f6cd\ufe0f\U0001f3eb\U0001f3e5\U0001f48a\U0001f475\U0001f52c\U0001f3a8\U0001f504\U0001f4c5\U0001f343\u2744\ufe0f\U0001f682\u23f3\U0001f4da\U0001f372\U0001f963\U0001f957\U0001f959\U0001f95a\U0001f95b\U0001f9e9\u26a0\ufe0f\U0001f6d1\U0001f3af\U0001f3ae\U0001f393\U0001f50d])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection|fact|culture|military|perspective|biography)\])'
    )
    engagement_count = len(engagement_pattern.findall(content))
    metrics["COMPUTED_ENGAGEMENT_COUNT"] = str(engagement_count)

    if body:
        imm_text = clean_for_immersion(body)
        immersion_pct = calculate_immersion(imm_text)
    else:
        immersion_pct = 0.0
    metrics["COMPUTED_IMMERSION_PERCENT"] = f"{immersion_pct:.1f}"

    metrics["COMPUTED_IMMERSION_TARGET"] = _compute_immersion_target(ctx)

    if content_path and content_path.exists():
        metrics.update(_compute_richness_metrics(content, content_path, act_path, ctx.track))

    return metrics


# ---------------------------------------------------------------------------
# Audit failure extraction + formatting helpers
# ---------------------------------------------------------------------------

def _extract_audit_failures(audit_output: str) -> str:
    """Extract actionable failure lines from audit output."""
    lines = audit_output.strip().split("\n")
    failure_lines = []
    in_ped_section = False

    for line in lines:
        stripped = line.strip()

        if any(kw in stripped.upper() for kw in [
            "FAIL", "ERROR", "VIOLATION", "MISSING", "GATE",
            "ROBOTIC", "MONOTONY", "IMMERSION TOO", "SEVERITY",
        ]):
            failure_lines.append(stripped)
            continue

        if stripped.startswith("\u274c") or stripped.startswith("\U0001f534") or stripped.startswith("\u26a0\ufe0f"):
            failure_lines.append(stripped)
            continue

        if stripped.startswith("- **[") or stripped.startswith("- ["):
            failure_lines.append(stripped)
            continue

        if "IMMERSION" in stripped.upper() and ("LOW" in stripped.upper() or "HIGH" in stripped.upper()):
            failure_lines.append(stripped)
            continue

        if stripped.startswith("## PEDAGOGICAL") or stripped.startswith("## Low Density"):
            in_ped_section = True
            failure_lines.append(stripped)
            continue

        if in_ped_section:
            if stripped.startswith("## "):
                in_ped_section = False
            elif stripped:
                failure_lines.append(stripped)
                continue

    if not failure_lines:
        return "\n".join(lines[-40:])
    return "\n".join(failure_lines)


def _extract_gate_blockers(ctx: ModuleContext) -> str:
    """Read status JSON and extract blocking_issues as GATE BLOCKER lines."""
    try:
        status_path = ctx.paths.get("status")
        if not status_path or not status_path.exists():
            return ""
        data = json.loads(status_path.read_text("utf-8"))
        blockers = data.get("overall", {}).get("blocking_issues", [])
        if not blockers:
            return ""
        lines = ["", "--- STATUS JSON GATE BLOCKERS ---"]
        for b in blockers:
            lines.append(f"GATE BLOCKER: {b}")
        return "\n".join(lines)
    except Exception:
        return ""


def _extract_vesum_failures(ctx: ModuleContext) -> str:
    """Read screen-result.json and format VESUM not-found words."""
    try:
        f = ctx.orch_dir / "screen-result.json"
        if not f.exists():
            return ""
        data = json.loads(f.read_text("utf-8"))
        not_found = data.get("vesum_not_found", [])
        if not not_found:
            return ""
        lines = ["", "--- VESUM WORD VERIFICATION FAILURES ---"]
        lines.append("These words were NOT found in the VESUM morphological dictionary.")
        lines.append("Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.")
        for r in not_found[:20]:
            word = r.get("original", r.get("clean", "?"))
            source = r.get("source", "?")
            status = r.get("status", "?")
            lines.append(f"  {status} `{word}` (source: {source})")
        if len(not_found) > 20:
            lines.append(f"  ... and {len(not_found) - 20} more")
        return "\n".join(lines)
    except Exception:
        return ""


def _format_deterministic_issues(issues: list[dict]) -> str:
    """Format deterministic issues as text for prompt injection."""
    if not issues:
        return "(No deterministic issues found -- D.0 pre-screen clean)"
    lines = []
    for i, iss in enumerate(issues, 1):
        lines.append(f"{i}. **[{iss.get('type', 'UNKNOWN')}]** (severity: {iss.get('severity', '?')})")
        if iss.get("location"):
            lines.append(f"   Location: {iss['location']}")
        if iss.get("text"):
            lines.append(f"   Text: {iss['text'][:120]}")
        if iss.get("fix"):
            lines.append(f"   Fix: {iss['fix'][:120]}")
    return "\n".join(lines)


def _format_filler_phrases(issues: list[dict]) -> str:
    """Format LLM filler findings for prompt injection."""
    filler = [i for i in issues if i.get("type") == "LLM_FILLER"]
    if not filler:
        return "(No LLM filler phrases detected by D.0 scanner)"
    lines = ["D.0 found these filler phrases -- verify each one:"]
    for f in filler[:10]:
        lines.append(f'- "{f.get("text", "")}" at {f.get("location", "?")}')
    return "\n".join(lines)


def _format_vesum_verification(stats: dict, not_found: list[dict]) -> str:
    """Format VESUM word verification results for prompt injection."""
    if not stats:
        return "(VESUM word verification did not run -- VESUM DB may be missing)"

    total = stats.get("total", 0)
    vesum = stats.get("vesum_hits", 0)
    coverage = (vesum / total * 100) if total else 0

    lines = [
        f"**Words checked:** {total} | **VESUM coverage:** {vesum}/{total} ({coverage:.1f}%)",
    ]

    if not not_found:
        lines.append("All words verified \u2705 -- no morphological issues detected.")
        return "\n".join(lines)

    not_found_words = [r for r in not_found if r["status"] == "\u274c"]
    partial_words = [r for r in not_found if r["status"] == "\u26a0\ufe0f"]

    if not_found_words:
        lines.append("")
        lines.append(f"**\u274c Not found in VESUM or textbooks ({len(not_found_words)}):**")
        for r in not_found_words[:15]:
            lines.append(f"- `{r['original']}` (source: {r['source']})")
        if len(not_found_words) > 15:
            lines.append(f"- ... and {len(not_found_words) - 15} more")
        lines.append("")
        lines.append("**Action:** Check if these are valid Ukrainian word forms. "
                      "Proper nouns and vocative forms may be legitimate. "
                      "Hallucinated forms or Russianisms must be flagged.")

    if partial_words:
        lines.append("")
        lines.append(f"**\u26a0\ufe0f Found in textbooks only, not VESUM ({len(partial_words)}):**")
        for r in partial_words[:10]:
            lines.append(f"- `{r['original']}` (source: {r['source']})")

    return "\n".join(lines)
