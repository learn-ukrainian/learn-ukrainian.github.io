"""Pipeline v5 parsing, extraction, and formatting utilities.

Extracted from pipeline_v5.py — delimiter extraction, audit parsing,
metrics computation, prompt injection, D1 review parsing, LLM filler
scanning, calibration, and quality gate helpers.
"""

from __future__ import annotations

import contextlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from pipeline_lib import ModuleContext, log


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DScreenResult:
    """Result of deterministic screen — collects all pre-LLM findings."""
    metrics: dict[str, str]
    deterministic_issues: list[dict] = field(default_factory=list)
    audit_passed: bool = False
    audit_output: str = ""
    h2_sections: str = ""
    vesum_stats: dict = field(default_factory=dict)
    vesum_not_found: list[dict] = field(default_factory=list)


@dataclass
class D1Result:
    """Parsed result of D.1 Markdown review."""
    ok: bool
    issues: list[dict] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    verdict: str = ""
    raw_review: str = ""


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
    (r"\bце не просто\b.*?\bа й\b", False),
    (r"\bдавайте розглянемо\b", False),
    (r"\bдавайте дізнаємося\b", False),
    (r"\bцікаво,?\s+що\b", False),
    (r"\bварто зазначити,?\s+що\b", False),
    (r"\bдзеркало\s+культури\b", False),
    (r"\bархітектура\s+мови\b", False),
    (r"\bдвигун\s+прогресу\b", False),
]
_LLM_FILLER_COMPILED: list[tuple[re.Pattern, bool]] = [
    (re.compile(p, re.IGNORECASE), always) for p, always in _LLM_FILLER_DEFS
]


def _scan_llm_filler(content: str) -> list[dict]:
    """Scan content for LLM filler PATTERNS — repetition is the signal."""
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
                "fix": "Rephrase — this phrase appears repeatedly (LLM pattern)" if len(matches) >= 2
                       else "Rephrase — formulaic opener",
            })

    return issues


# ---------------------------------------------------------------------------
# Delimiter extraction
# ---------------------------------------------------------------------------

def _extract_delimiter(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiters. Anchors on LAST start tag."""
    s = text.rfind(start_tag)
    if s == -1:
        return None
    s += len(start_tag)
    e = text.find(end_tag, s)
    if e == -1:
        return None
    return text[s:e].strip()


def _extract_delimiter_tolerant(
    text: str, start_tag: str, end_tag: str, *, content_type: str = "yaml"
) -> str | None:
    """Extract delimited content, tolerating missing end tag."""
    exact = _extract_delimiter(text, start_tag, end_tag)
    if exact:
        return exact

    s = text.rfind(start_tag)
    if s == -1:
        return None

    s += len(start_tag)
    raw = text[s:]

    lines = raw.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("─") or stripped.startswith("✅") or stripped.startswith("✓"):
            break
        if stripped.startswith("===") and stripped.endswith("==="):
            break
        clean_lines.append(line)

    while clean_lines and not clean_lines[-1].strip():
        clean_lines.pop()

    candidate = "\n".join(clean_lines).strip()
    if not candidate:
        return None

    if content_type == "markdown":
        log(f"    Tolerant extraction (markdown): recovered {len(candidate)} chars (missing {end_tag})")
        return candidate

    import yaml
    try:
        parsed = yaml.safe_load(candidate)
        if parsed and isinstance(parsed, dict) and "items" in parsed:
            log(f"    Tolerant extraction: recovered {len(parsed['items'])} vocab items (missing {end_tag})")
            return candidate
    except yaml.YAMLError:
        last_good = -1
        for i, line in enumerate(clean_lines):
            if line.strip().startswith("- lemma:"):
                last_good = i
        if last_good > 0 and last_good > 1:
            for j in range(last_good, len(clean_lines)):
                ln = clean_lines[j].strip()
                if j > last_good and ln.startswith("- lemma:"):
                    break
            trimmed = "\n".join(clean_lines[:last_good]).strip()
            try:
                parsed = yaml.safe_load(trimmed)
                if parsed and isinstance(parsed, dict) and "items" in parsed:
                    log(f"    Tolerant extraction: recovered {len(parsed['items'])} vocab items (trimmed incomplete entry)")
                    return trimmed
            except yaml.YAMLError:
                pass

    return None


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def _compute_metrics_direct(ctx: ModuleContext) -> dict[str, str]:
    """Compute audit metrics WITHOUT running the audit subprocess."""
    import yaml
    from audit.cleaners import calculate_immersion, clean_for_immersion, clean_for_stats, extract_core_content

    metrics: dict[str, str] = {}
    content_path = ctx.paths.get("md")

    if content_path and content_path.exists():
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
    else:
        word_count = 0
        body = ""
        content = ""

    word_target = getattr(ctx, "word_target", 0) or 0
    word_pct = (word_count / word_target * 100) if word_target else 0
    metrics["COMPUTED_WORD_COUNT"] = str(word_count)
    metrics["COMPUTED_WORD_TARGET"] = str(word_target)
    metrics["COMPUTED_WORD_PERCENT"] = f"{word_pct:.1f}"

    act_path = ctx.paths.get("activities")
    act_count = 0
    if act_path and act_path.exists():
        try:
            act_data = yaml.safe_load(act_path.read_text("utf-8"))
            if isinstance(act_data, list):
                act_count = len(act_data)
        except Exception:
            pass
    metrics["COMPUTED_ACTIVITY_COUNT"] = str(act_count)

    vocab_path = ctx.paths.get("vocabulary")
    vocab_count = 0
    if vocab_path and vocab_path.exists():
        try:
            vocab_data = yaml.safe_load(vocab_path.read_text("utf-8"))
            if isinstance(vocab_data, list):
                vocab_count = len(vocab_data)
            elif isinstance(vocab_data, dict):
                vlist = vocab_data.get("vocabulary", vocab_data.get("items", []))
                if isinstance(vlist, list):
                    vocab_count = len(vlist)
        except Exception:
            pass
    metrics["COMPUTED_VOCAB_COUNT"] = str(vocab_count)

    engagement_pattern = re.compile(
        r'(>\s*[💡⚡🎬🎭📜⚔️🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑🎯🎮🎓🔍])|'
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
    metrics["COMPUTED_IMMERSION_TARGET"] = f"{min_imm}-{max_imm}%"

    if content_path and content_path.exists():
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
            level_code_rich = ctx.track.split("-")[0].lower() if "-" not in ctx.track else ctx.track.lower()
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


# ---------------------------------------------------------------------------
# H2 section extraction
# ---------------------------------------------------------------------------

def _extract_h2_sections(content_path: Path) -> str:
    """Extract all H2 headers from a content .md file as a numbered list."""
    if not content_path.exists():
        return "(content file not found)"
    text = content_path.read_text("utf-8")
    h2s = re.findall(r"^## (.+)$", text, re.MULTILINE)
    if not h2s:
        return "(no H2 sections found)"
    return "\n".join(f"{i}. {h}" for i, h in enumerate(h2s, 1))


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

        if stripped.startswith("❌") or stripped.startswith("🔴") or stripped.startswith("⚠️"):
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
        return "(No deterministic issues found — D.0 pre-screen clean)"
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
    lines = ["D.0 found these filler phrases — verify each one:"]
    for f in filler[:10]:
        lines.append(f"- \"{f.get('text', '')}\" at {f.get('location', '?')}")
    return "\n".join(lines)


def _format_vesum_verification(stats: dict, not_found: list[dict]) -> str:
    """Format VESUM word verification results for prompt injection."""
    if not stats:
        return "(VESUM word verification did not run — VESUM DB may be missing)"

    total = stats.get("total", 0)
    vesum = stats.get("vesum_hits", 0)
    coverage = (vesum / total * 100) if total else 0

    lines = [
        f"**Words checked:** {total} | **VESUM coverage:** {vesum}/{total} ({coverage:.1f}%)",
    ]

    if not not_found:
        lines.append("All words verified ✅ — no morphological issues detected.")
        return "\n".join(lines)

    not_found_words = [r for r in not_found if r["status"] == "❌"]
    partial_words = [r for r in not_found if r["status"] == "⚠️"]

    if not_found_words:
        lines.append("")
        lines.append(f"**❌ Not found in VESUM or textbooks ({len(not_found_words)}):**")
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
        lines.append(f"**⚠️ Found in textbooks only, not VESUM ({len(partial_words)}):**")
        for r in partial_words[:10]:
            lines.append(f"- `{r['original']}` (source: {r['source']})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt injection helpers
# ---------------------------------------------------------------------------

def _inject_metrics_into_prompt(prompt_text: str, metrics: dict[str, str]) -> str:
    """Replace {COMPUTED_*} placeholders in a prompt with computed values."""
    for key, val in metrics.items():
        prompt_text = prompt_text.replace("{" + key + "}", val)
    return prompt_text


def _inject_file_contents(prompt_text: str, ctx: ModuleContext) -> str:
    """Inject module file contents into prompt, replacing placeholders."""
    content_path = ctx.paths.get("md")
    act_path = ctx.paths.get("activities")
    vocab_path = ctx.paths.get("vocabulary")

    content_text = content_path.read_text("utf-8") if content_path and content_path.exists() else "(file not found)"
    act_text = act_path.read_text("utf-8") if act_path and act_path.exists() else "(file not found)"
    vocab_text = vocab_path.read_text("utf-8") if vocab_path and vocab_path.exists() else "(file not found)"

    prompt_text = prompt_text.replace("{CONTENT_FILE_CONTENT}", content_text)
    prompt_text = prompt_text.replace("{ACTIVITIES_FILE_CONTENT}", act_text)
    prompt_text = prompt_text.replace("{VOCAB_FILE_CONTENT}", vocab_text)
    return prompt_text


# ---------------------------------------------------------------------------
# D.1 review parsing
# ---------------------------------------------------------------------------

def _parse_d1_review(raw_output: str) -> D1Result:
    """Parse D.1 Markdown review from delimiters."""
    review_text = _extract_delimiter(raw_output, "===REVIEW_START===", "===REVIEW_END===")
    if not review_text:
        review_text = _extract_delimiter_tolerant(
            raw_output, "===REVIEW_START===", "===REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    score = 0.0
    score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        score = float(score_m.group(1))

    scores: dict[str, float] = {}
    if score > 0:
        scores["overall"] = score

    scores_section = re.search(
        r'## Scores\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if scores_section:
        dim_rows = re.findall(
            r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*([\d.]+)/10\s*\|',
            scores_section.group(1),
        )
        for dim_name, dim_score in dim_rows:
            key = dim_name.strip().lower().replace(" ", "_")
            with contextlib.suppress(ValueError):
                scores[key] = float(dim_score)

        weighted_m = re.search(
            r'\*\*Weighted Overall:\*\*.*?=\s*\*\*([\d.]+)/10\*\*',
            scores_section.group(1),
        )
        if weighted_m:
            with contextlib.suppress(ValueError):
                scores["weighted_overall"] = float(weighted_m.group(1))

    if not verdict and score > 0:
        verdict = "PASS" if score >= 9.0 else "FAIL"

    issues: list[dict] = []
    issues_section = re.search(
        r'## Critical Issues Found\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if issues_section:
        issue_blocks = re.findall(
            r'### Issue \d+:\s*(.+?)(?=### Issue|\Z)',
            issues_section.group(1),
            re.DOTALL,
        )
        for block in issue_blocks:
            issue: dict[str, str] = {"type": "REVIEW_ISSUE", "severity": "HIGH"}
            loc_m = re.search(r'\*\*Location\*\*:\s*(.+)', block)
            if loc_m:
                issue["location"] = loc_m.group(1).strip()
            prob_m = re.search(r'\*\*Problem\*\*:\s*(.+)', block)
            if prob_m:
                issue["text"] = prob_m.group(1).strip()
            fix_m = re.search(r'\*\*Fix\*\*:\s*(.+)', block)
            if fix_m:
                issue["fix"] = fix_m.group(1).strip()
            issues.append(issue)

    return D1Result(
        ok=True,
        issues=issues,
        scores=scores,
        verdict=verdict,
        raw_review=review_text,
    )


def _parse_factual_review(raw_output: str) -> D1Result:
    """Parse Gemini Fact Checker output."""
    review_text = _extract_delimiter(raw_output, "===FACTUAL_REVIEW_START===", "===FACTUAL_REVIEW_END===")
    if not review_text:
        review_text = _extract_delimiter_tolerant(
            raw_output, "===FACTUAL_REVIEW_START===", "===FACTUAL_REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    scores: dict[str, float] = {}
    score_m = re.search(r'\*\*Factual Alignment Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        scores["factual_accuracy"] = float(score_m.group(1))

    plan_m = re.search(r'\*\*Plan Adherence Score:\*\*\s*([\d.]+)/10', review_text)
    if plan_m:
        scores["plan_adherence"] = float(plan_m.group(1))

    plan_missing_m = re.search(r'(\d+)\s+missing', review_text[:500])
    plan_missing_count = int(plan_missing_m.group(1)) if plan_missing_m else 0

    disc_m = re.search(r'\*\*Discrepancies \[Tier 1\]:\*\*\s*(\d+)', review_text)
    discrepancy_count = int(disc_m.group(1)) if disc_m else 0

    re.search(r'\*\*Unverified:\*\*\s*(\d+)', review_text)

    issues: list[dict] = []

    missing_points = re.findall(
        r'- \[ \]\s+(?:Point \d+:\s*)?(.+?)(?:\s*—\s*MISSING)',
        review_text,
    )
    for pt_text in missing_points:
        issues.append({
            "type": "MISSING_PLAN_POINT",
            "severity": "MEDIUM",
            "text": pt_text.strip(),
        })

    disc_blocks = re.findall(
        r'### Discrepancy \d+:\s*(.+?)(?=### Discrepancy|\Z)',
        review_text,
        re.DOTALL,
    )
    for block in disc_blocks:
        issue: dict[str, str] = {"type": "FACTUAL_DISCREPANCY", "severity": "HIGH"}
        mod_m = re.search(r'\*\*Module says:\*\*\s*"(.+?)"', block)
        if mod_m:
            issue["text"] = mod_m.group(1).strip()
        ref_m = re.search(r'\*\*Reference says:\*\*\s*"(.+?)"', block)
        if ref_m:
            issue["reference"] = ref_m.group(1).strip()
        src_m = re.search(r'\*\*Source:\*\*\s*(.+)', block)
        if src_m:
            issue["source"] = src_m.group(1).strip()
        fix_m = re.search(r'\*\*Suggested fix:\*\*\s*(.+)', block)
        if fix_m:
            issue["fix"] = fix_m.group(1).strip()
        issues.append(issue)

    if not verdict:
        verdict = "FAIL" if discrepancy_count > 0 or plan_missing_count >= 3 else "PASS"

    return D1Result(
        ok=True,
        issues=issues,
        scores=scores,
        verdict=verdict,
        raw_review=review_text,
    )


# ---------------------------------------------------------------------------
# D.1 fix plan extraction
# ---------------------------------------------------------------------------

def _extract_fix_plan(review_text: str) -> str:
    """Extract only actionable sections from a review for the fix prompt."""
    sections: list[str] = []
    _PATTERNS = [
        r'(## Critical Issues Found\s*\n.*?)(?=\n## |\Z)',
        r'(## Ukrainian Language Issues\s*\n.*?)(?=\n## |\Z)',
        r'(## Fix Plan to Reach [^\n]+\n.*?)(?=\n## |\Z)',
    ]
    for pattern in _PATTERNS:
        m = re.search(pattern, review_text, re.DOTALL)
        if m:
            sections.append(m.group(1).strip())

    if not sections:
        return review_text
    return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Track calibration
# ---------------------------------------------------------------------------

_CALIBRATION_DIR = Path(__file__).resolve().parent.parent.parent / "claude_extensions" / "phases" / "calibration"


def _get_track_calibration(level: str, module_num: int) -> str:
    """Read the appropriate calibration file for a track/level + module number."""
    level_lower = level.lower()

    if level_lower == "b1" and module_num <= 5:
        cal_name = "b1-bridge.md"
    elif level_lower == "b1":
        cal_name = "b1-immersed.md"
    elif level_lower.startswith("lit"):
        cal_name = "lit.md"
    else:
        cal_name = f"{level_lower}.md"

    cal_path = _CALIBRATION_DIR / cal_name
    if cal_path.exists():
        return cal_path.read_text("utf-8")

    base = level_lower.split("-")[0]
    fallback = _CALIBRATION_DIR / f"{base}.md"
    if fallback.exists():
        return fallback.read_text("utf-8")

    return ""


def _get_russicism_table(level: str) -> str:
    """Extract the Russicism Lookup section from a calibration file."""
    cal_text = _get_track_calibration(level, 1)
    if not cal_text:
        return ""

    m = re.search(
        r'## Russicism Lookup.*?\n(.*?)(?=\n## |\Z)',
        cal_text,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# D.3 context builder
# ---------------------------------------------------------------------------

def _build_d3_context(d1_review: str, repair_cycle: int) -> str:
    """Build D.3 context injection with D.1 findings and D.2 repair info."""
    review_lines = d1_review.strip().split('\n')
    truncated = '\n'.join(review_lines[:80])
    if len(review_lines) > 80:
        truncated += f"\n\n... ({len(review_lines) - 80} more lines truncated)"

    return f"""## D.3 Re-Review Context (Repair Cycle {repair_cycle})

> **You are re-reviewing content that was already reviewed and repaired.**
> A previous D.1 review found issues. D.2 applied targeted FIND/REPLACE fixes.
> Your job: **verify the fixes landed correctly AND check for regressions** introduced by the repair.

### What D.1 Found (previous review summary)

<details>
<summary>D.1 Review (click to expand)</summary>

{truncated}

</details>

### Your D.3 Re-Review Focus

1. **Verify each D.1 issue was fixed** — check that the specific problems from D.1 no longer exist in the current content
2. **Check for D.2 regressions** — D.2 rewrites may have introduced new errors (broken sentences, orphaned references, formatting damage)
3. **Score the current state** — your scores reflect the content AS IT IS NOW, not the D.1 review's scores
4. **Do NOT auto-pass** — if D.2 fixes created new problems, flag them even though the originals are fixed

---"""


# ---------------------------------------------------------------------------
# Quick review quality gate
# ---------------------------------------------------------------------------

def _quick_review_quality_gate(review_text: str, content_path: Path) -> tuple[bool, str]:
    """Fast pre-save check: reject obviously shallow/fake reviews."""
    from audit.checks.review_gaming import _extract_h2_headers
    from audit.checks.review_validation import _extract_ukrainian_citations

    citations = _extract_ukrainian_citations(review_text)
    content_text = content_path.read_text("utf-8") if content_path.exists() else ""
    word_count = len(content_text.split())

    min_citations = max(2, word_count // 600) if word_count > 500 else 2
    if len(citations) < min_citations:
        return False, (
            f"Shallow review: {len(citations)} citation(s), need ≥{min_citations} "
            f"for {word_count}-word content"
        )

    if content_text:
        h2s = _extract_h2_headers(content_text)
        skip = {'словник', 'vocabulary', 'лексика', 'бібліографія', 'джерела',
                'література', 'використані джерела', 'самооцінювання',
                'self-assessment', 'самоперевірка'}
        h2s = [h for h in h2s if h.strip().lower() not in skip]

        if len(h2s) >= 3:
            review_lower = review_text.lower()
            mentioned = sum(
                1 for h in h2s
                if h.strip().lower() in review_lower
                or (len(h.split(':')[0].strip()) > 3
                    and h.split(':')[0].strip().lower() in review_lower)
            )
            coverage = mentioned / len(h2s)
            if coverage < 0.15:
                return False, (
                    f"Shallow review: covers {mentioned}/{len(h2s)} "
                    f"({coverage:.0%}) content sections"
                )

    if len(review_text.split()) < 150:
        return False, f"Shallow review: only {len(review_text.split())} words"

    return True, "OK"
