"""Semantic Russicism detector — catches words that exist in Ukrainian
but carry a Russian meaning when paired with certain translations.

Used by preflight to auto-fix plans before content generation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Ensure scripts/ is on the path for pipeline_lib import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.core import log

# Word + Russian meaning → Ukrainian equivalent.
# These words ARE valid Ukrainian but mean something different than in Russian.
SEMANTIC_FALSE_FRIENDS: list[dict] = [
    # --- High-confidence entries (verified) ---
    {
        "word": "лук",
        "russian_meanings": ["onion", "цибуля", "onions"],
        "ukrainian_meaning": "bow (weapon)",
        "replacement": "цибуля",
        "replacement_translation": "onion",
    },
    {
        "word": "луна",
        "russian_meanings": ["moon", "місяць", "lunar"],
        "ukrainian_meaning": "echo (відлуння)",
        "replacement": "місяць",
        "replacement_translation": "moon",
    },
    {
        "word": "город",
        "russian_meanings": ["city", "місто", "town"],
        "ukrainian_meaning": "garden, vegetable patch",
        "replacement": "місто",
        "replacement_translation": "city",
    },
    {
        "word": "неділя",
        "russian_meanings": ["week", "тиждень"],
        "ukrainian_meaning": "Sunday",
        "replacement": "тиждень",
        "replacement_translation": "week",
    },
    # рушник removed: IS the standard Ukrainian word for towel (including generic use)
    # дурний removed: SUM defines it as "lacking intelligence" — "stupid" IS correct Ukrainian
    # --- Added from Gemini false-friends audit (2026-03-16) ---
    {
        "word": "річ",
        "russian_meanings": ["speech"],
        "ukrainian_meaning": "thing, item",
        "replacement": "промова",
        "replacement_translation": "speech",
    },
    {
        "word": "шар",
        "russian_meanings": ["ball", "sphere"],
        "ukrainian_meaning": "layer",
        "replacement": "куля",
        "replacement_translation": "ball",
    },
    {
        "word": "мешкати",
        "russian_meanings": ["to dawdle", "to delay", "dawdle", "delay"],
        "ukrainian_meaning": "to live, to dwell",
        "replacement": "баритися",
        "replacement_translation": "to delay",
    },
    # гадати removed: SUM meaning #3 IS ворожити; "to guess" = "I suppose" is valid Ukrainian
    {
        "word": "лічити",
        "russian_meanings": ["to treat", "to heal", "treatment"],
        "ukrainian_meaning": "to count",
        "replacement": "лікувати",
        "replacement_translation": "to treat (medically)",
    },
    {
        "word": "наглий",
        "russian_meanings": ["arrogant", "impudent", "insolent"],
        "ukrainian_meaning": "sudden, unexpected",
        "replacement": "зухвалий",
        "replacement_translation": "arrogant",
    },
    {
        "word": "лаяти",
        "russian_meanings": ["to bark", "bark", "barking"],
        "ukrainian_meaning": "to scold, to swear at",
        "replacement": "гавкати",
        "replacement_translation": "to bark",
    },
    {
        "word": "палиця",
        "russian_meanings": ["finger"],
        "ukrainian_meaning": "stick, cane",
        "replacement": "палець",
        "replacement_translation": "finger",
    },
    {
        "word": "сварка",
        "russian_meanings": ["welding"],
        "ukrainian_meaning": "quarrel, argument",
        "replacement": "зварювання",
        "replacement_translation": "welding",
    },
]


def scan_plan_for_russianisms(plan_path: Path) -> list[dict]:
    """Scan a plan's vocabulary_hints for semantic Russianisms (deterministic).

    Content_outline and research are scanned by LLM via scan_with_llm() — the LLM
    understands context and avoids false positives on warnings.

    Returns list of findings: [{word, meaning_found, fix, category, original_entry, ...}]
    """
    if not plan_path.exists():
        return []

    try:
        with open(plan_path) as f:
            plan = yaml.safe_load(f)
    except Exception:
        return []

    if not isinstance(plan, dict):
        return []

    findings = []

    # 1. Scan vocabulary_hints
    vocab = plan.get("vocabulary_hints", {})
    if isinstance(vocab, list):
        for item in vocab:
            if isinstance(item, str):
                _check_vocab_entry(item, "vocabulary_hints", findings)
    elif isinstance(vocab, dict):
        for category in ["required", "recommended", "sight_words"]:
            items = vocab.get(category, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, str):
                    continue
                _check_vocab_entry(item, f"vocabulary_hints.{category}", findings)

    # Content_outline scanning moved to scan_with_llm() — LLM understands context

    return findings


def scan_with_llm(
    plan_path: Path | None,
    research_path: Path | None,
    dispatch_fn,
    slug: str,
    model: str,
) -> list[dict]:
    """Use LLM to check plan content_outline and research for semantic false friends.

    The LLM understands context — it can distinguish between:
    - "лук (onion)" = MISUSE (translating with Russian meaning)
    - "неділя ≠ week" = CORRECT (warning about the false friend)

    Returns list of findings: [{word, meaning_found, ukrainian_meaning, source, context}]
    """
    # Build the false friends reference for the prompt
    ff_table = "\n".join(
        f"- {ff['word']}: Russian meaning = {', '.join(ff['russian_meanings'])}; "
        f"Ukrainian meaning = {ff['ukrainian_meaning']}"
        for ff in SEMANTIC_FALSE_FRIENDS
    )

    files_section = ""
    if plan_path and plan_path.exists():
        plan_text = plan_path.read_text("utf-8")
        # Only send content_outline, not the whole plan
        try:
            plan_data = yaml.safe_load(plan_text)
            outline = plan_data.get("content_outline", [])
            outline_text = yaml.dump(outline, allow_unicode=True, default_flow_style=False)
        except Exception:
            outline_text = plan_text[:3000]
        files_section += f"\n### Plan content_outline ({plan_path.name}):\n```yaml\n{outline_text}\n```\n"

    if research_path and research_path.exists():
        research_text = research_path.read_text("utf-8")
        # Truncate if too long
        if len(research_text) > 4000:
            research_text = research_text[:4000] + "\n...(truncated)"
        files_section += f"\n### Research ({research_path.name}):\n```markdown\n{research_text}\n```\n"

    if not files_section:
        return []

    prompt = (
        "Check these files for SEMANTIC FALSE FRIENDS — Ukrainian words paired "
        "with their RUSSIAN meaning instead of the correct Ukrainian meaning.\n\n"
        "False friends reference:\n" + ff_table + "\n\n"
        "IMPORTANT: Only flag cases where the word is being USED or DEFINED with "
        "the Russian meaning. Do NOT flag:\n"
        "- Warnings about the false friend (e.g., 'неділя ≠ week')\n"
        "- Discussions explaining the difference between meanings\n"
        "- Correct Ukrainian usage of the word\n\n"
        "Files to check:" + files_section + "\n\n"
        "Output format — ONLY if you find real misuses:\n"
        "===FINDINGS_START===\n"
        "- word: лук\n"
        "  meaning_found: onion\n"
        "  source: plan OR research\n"
        "  context: the exact text containing the misuse\n"
        "===FINDINGS_END===\n\n"
        "If NO misuses found, output:\n"
        "===FINDINGS_START===\nNONE\n===FINDINGS_END===\n"
    )

    ok, output = dispatch_fn(
        prompt,
        task_id=f"russicism-scan-{slug}",
        model=model, stdout_only=True, timeout=120,
    )
    if not ok:
        log("  pre-content: LLM russicism scan failed — skipping")
        return []

    # Parse findings
    import re as _re
    match = _re.search(r"===FINDINGS_START===\s*\n(.*?)\n\s*===FINDINGS_END===", output, _re.DOTALL)
    if not match:
        return []

    body = match.group(1).strip()
    if body == "NONE" or not body:
        return []

    # Parse YAML-like findings
    findings = []
    current: dict = {}
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("- word:"):
            if current:
                findings.append(current)
            current = {"word": line.split(":", 1)[1].strip()}
        elif line.startswith("meaning_found:") and current:
            current["meaning_found"] = line.split(":", 1)[1].strip()
        elif line.startswith("source:") and current:
            current["category"] = line.split(":", 1)[1].strip()
        elif line.startswith("context:") and current:
            current["original_entry"] = line.split(":", 1)[1].strip()
    if current and "word" in current:
        findings.append(current)

    # Enrich with dictionary data
    for f in findings:
        for ff in SEMANTIC_FALSE_FRIENDS:
            if ff["word"] == f.get("word"):
                f["ukrainian_meaning"] = ff["ukrainian_meaning"]
                f["replacement"] = ff["replacement"]
                f["replacement_translation"] = ff["replacement_translation"]
                break
        f.setdefault("ukrainian_meaning", "unknown")
        f.setdefault("replacement", None)
        f.setdefault("replacement_translation", None)
        f.setdefault("category", "llm-scan")
        f.setdefault("meaning_found", "unknown")
        f.setdefault("original_entry", "")

    return findings


def _check_vocab_entry(entry: str, category: str, findings: list[dict]) -> None:
    """Check a single vocabulary_hints entry for semantic Russianisms.

    Uses simple substring matching — vocabulary_hints have predictable format
    like 'лук (onion)'. For content_outline and research, use LLM-based
    checking via scan_with_llm() instead.
    """
    entry_lower = entry.lower()

    for ff in SEMANTIC_FALSE_FRIENDS:
        word = ff["word"]
        if not re.search(rf"\b{re.escape(word)}\b", entry_lower):
            continue

        for russian_meaning in ff["russian_meanings"]:
            if russian_meaning.lower() in entry_lower:
                findings.append({
                    "word": ff["word"],
                    "meaning_found": russian_meaning,
                    "ukrainian_meaning": ff["ukrainian_meaning"],
                    "replacement": ff["replacement"],
                    "replacement_translation": ff["replacement_translation"],
                    "category": category,
                    "original_entry": entry,
                })
                return


def fix_plan_russianisms(plan_path: Path, findings: list[dict]) -> int:
    """Auto-fix semantic Russianisms in a plan file.

    Returns number of fixes applied.
    """
    if not findings or not plan_path.exists():
        return 0

    content = plan_path.read_text("utf-8")
    fixes = 0

    for finding in findings:
        if not finding["replacement"]:
            log(f"  preflight-russicism: FLAG — '{finding['word']}' used as "
                f"'{finding['meaning_found']}' (Ukrainian meaning: {finding['ukrainian_meaning']}). "
                "Manual review needed.")
            continue

        old = finding["original_entry"]
        new = old
        category = finding.get("category", "")

        if category.startswith("content_outline") or category == "research":
            # In content_outline/research: the Ukrainian word is correct, the English
            # meaning is wrong. Do a direct text replacement in the file content —
            # find the word+meaning pattern and replace the meaning.
            # Use the simple pattern: word ... meaning (handles YAML wrapping)
            pattern = rf"(\b{re.escape(finding['word'])}\b[^)]*?){re.escape(finding['meaning_found'])}"
            replacement = rf"\g<1>{finding['ukrainian_meaning'].split(',')[0].strip()}"
            new_content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
            if new_content != content:
                content = new_content
                fixes += 1
                log(f"  preflight-russicism: FIXED — '{finding['word']}' meaning "
                    f"'{finding['meaning_found']}' → '{finding['ukrainian_meaning']}' "
                    f"in {category}")
            continue
        else:
            # In vocabulary_hints: replace the word AND the translation.
            new = re.sub(
                rf"\b{re.escape(finding['word'])}\b",
                finding["replacement"],
                new,
                count=1,
            )
            if finding["replacement_translation"] and finding["meaning_found"]:
                new = new.replace(
                    f"({finding['meaning_found']}",
                    f"({finding['replacement_translation']}",
                    1,
                )

        if old != new and old in content:
            content = content.replace(old, new, 1)
            fixes += 1
            log(f"  preflight-russicism: FIXED — '{finding['word']}' ({finding['meaning_found']}) "
                f"→ '{finding['replacement']}' ({finding['replacement_translation']})")

    if fixes > 0:
        plan_path.write_text(content, "utf-8")

    return fixes


def scan_and_fix_plan(plan_path: Path) -> tuple[list[dict], int]:
    """Scan a plan for semantic Russianisms and auto-fix what we can.

    Returns (findings, fixes_applied).
    """
    findings = scan_plan_for_russianisms(plan_path)
    if not findings:
        return [], 0
    fixes = fix_plan_russianisms(plan_path, findings)
    return findings, fixes
