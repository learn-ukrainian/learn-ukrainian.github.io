#!/usr/bin/env python3
"""Batch fix + review loop: push all modules in a range to 9.0+ score.

For each module:
  1. Check if Phase 5 review exists → if not, run review first
  2. Check score → if >= 9.0, skip
  3. Assemble fix prompt from template → send to Gemini
  4. Extract fixed files → write to disk → run audit
  5. Assemble review prompt → send to Gemini
  6. Extract score → if >= 9.0, done; else retry fix (max 3)

Usage:
    .venv/bin/python scripts/batch_fix_review.py a1 --from 1 --to 20
    .venv/bin/python scripts/batch_fix_review.py a1 --from 6 --to 18 --dry-run
    .venv/bin/python scripts/batch_fix_review.py a1 --module 7
    .venv/bin/python scripts/batch_fix_review.py a1 --from 1 --to 20 --review-only
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.thresholds import STYLE_REVIEW_TARGET
from slug_utils import review_path as _review_path
from slug_utils import status_path as _status_path
from slug_utils import to_bare_slug

REPO = Path(__file__).parent.parent.parent
VENV_PYTHON = REPO / ".venv" / "bin" / "python"
MAX_RETRIES = 3
# Batch fix loop targets the style-reviewer PASS score (9.0).
PASS_THRESHOLD = STYLE_REVIEW_TARGET
SUSPICIOUS_JUMP = 3.5  # Flag if score jumps more than this in one fix
GEMINI_TIMEOUT = 600  # 10 minutes


# ─── Module Resolution ───────────────────────────────────────────────

def find_module_files(level: str, num: int) -> dict | None:
    """Find all files for a core-track module by number."""
    level_dir = REPO / f"curriculum/l2-uk-en/{level}"

    # Primary: resolve via manifest
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        from manifest_utils import get_module_by_number
        mod = get_module_by_number(level, num)
        if mod:
            slug = mod.slug
            content_path = level_dir / f"{slug}.md"
            if content_path.exists():
                return {
                    "num": num,
                    "slug": slug,
                    "full_stem": slug,
                    "content": content_path,
                    "activities": level_dir / f"activities/{slug}.yaml",
                    "vocabulary": level_dir / f"vocabulary/{slug}.yaml",
                    "meta": level_dir / f"meta/{slug}.yaml",
                    "plan": level_dir.parent / f"plans/{level}/{slug}.yaml",
                    "research": level_dir / f"research/{slug}-research.md",
                    "review": _review_path(level_dir, slug),
                    "status": _status_path(level_dir, slug),
                    "orchestration": level_dir / f"orchestration/{slug}",
                }
    except Exception:
        pass

    # Fallback: glob
    content_files = sorted(level_dir.glob(f"{num:02d}-*.md"))
    if not content_files:
        return None

    content_path = content_files[0]
    slug = to_bare_slug(content_path.stem)

    return {
        "num": num,
        "slug": slug,
        "full_stem": slug,
        "content": content_path,
        "activities": level_dir / f"activities/{slug}.yaml",
        "vocabulary": level_dir / f"vocabulary/{slug}.yaml",
        "meta": level_dir / f"meta/{slug}.yaml",
        "plan": level_dir.parent / f"plans/{level}/{slug}.yaml",
        "research": level_dir / f"research/{slug}-research.md",
        "review": _review_path(level_dir, slug),
        "status": _status_path(level_dir, slug),
        "orchestration": level_dir / f"orchestration/{slug}",
    }


def get_module_title(files: dict) -> str:
    """Get module title from content H1."""
    if files["content"].exists():
        for line in files["content"].read_text().split('\n'):
            if line.startswith('# '):
                return line[2:].strip()
    return files["slug"].replace("-", " ").title()


# ─── Audit Metrics ───────────────────────────────────────────────────

def get_audit_metrics(files: dict) -> dict:
    """Extract metrics from status JSON after audit."""
    status_path = files["status"]
    if not status_path.exists():
        return {}

    data = json.loads(status_path.read_text())
    gates = data.get("gates", {})

    # Parse word count from lesson gate message like "1135/1019 (raw: 1507)"
    lesson_msg = gates.get("lesson", {}).get("message", "")
    match = re.match(r"(\d+)/(\d+)", lesson_msg)
    audit_words = int(match.group(1)) if match else 0
    word_target = int(match.group(2)) if match else 0

    return {
        "audit_words": audit_words,
        "word_target": word_target,
        "word_percent": f"{(audit_words / word_target * 100):.0f}%" if word_target else "?",
        "activity_count": gates.get("activities", {}).get("message", "0/0").split("/")[0],
        "overall_status": data.get("overall", {}).get("status", "unknown"),
    }


def get_word_target(files: dict) -> int:
    """Get word_target from plan YAML."""
    if files["plan"].exists():
        for line in files["plan"].read_text().split('\n'):
            if line.startswith('word_target:'):
                try:
                    return int(line.split(':')[1].strip())
                except ValueError:
                    pass
    return 0


def count_items(path: Path, key: str = "items") -> int:
    """Count items in a YAML file."""
    if not path.exists():
        return 0
    text = path.read_text()
    # For vocabulary, count under 'items:'
    if key == "items":
        in_items = False
        count = 0
        for line in text.split('\n'):
            if line.strip() == "items:":
                in_items = True
                continue
            if in_items and line.startswith('  - '):
                count += 1
            elif in_items and not line.startswith('  ') and line.strip():
                break
        return count
    # For activities, count root-level list items
    count = 0
    for line in text.split('\n'):
        if line.startswith('- type:'):
            count += 1
    return count


def count_engagement(content_path: Path) -> int:
    """Count engagement boxes in content."""
    if not content_path.exists():
        return 0
    count = 0
    for line in content_path.read_text().split('\n'):
        if re.match(r'>\s*\[!', line) or re.match(r'>\s*💡|>\s*🔍|>\s*🎬|>\s*🌍', line):
            count += 1
    return count


# ─── Template Assembly ───────────────────────────────────────────────

def assemble_fix_prompt(files: dict, review_path: Path) -> Path:
    """Assemble fix prompt from template."""
    template = REPO / "claude_extensions/phases/gemini/phase-fix.md"
    dest = files["orchestration"] / "fix-prompt.md"
    files["orchestration"].mkdir(parents=True, exist_ok=True)

    text = template.read_text()
    replacements = {
        "{REVIEW_PATH}": str(review_path),
        "{CONTENT_PATH}": str(files["content"]),
        "{ACTIVITIES_PATH}": str(files["activities"]),
        "{VOCAB_PATH}": str(files["vocabulary"]),
        "{PLAN_PATH}": str(files["plan"]),
        "{RESEARCH_PATH}": str(files["research"]),
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    dest.write_text(text)
    return dest


def assemble_review_prompt(files: dict, level: str) -> Path:
    """Assemble review prompt from template."""
    template = REPO / "claude_extensions/phases/gemini/phase-5-review.md"
    dest = files["orchestration"] / "phase-5-review-prompt.md"
    files["orchestration"].mkdir(parents=True, exist_ok=True)

    text = template.read_text()

    # Get metrics
    metrics = get_audit_metrics(files)
    vocab_count = count_items(files["vocabulary"], "items")
    activity_count = count_items(files["activities"], "activities_root")
    engagement = count_engagement(files["content"])
    word_target = metrics.get("word_target", 0) or get_word_target(files)
    title = get_module_title(files)

    # Determine immersion target based on module number
    num = files["num"]
    if num <= 2:
        immersion_target = f"5-15% (M{num:02d})"
    elif num <= 10:
        immersion_target = f"10-25% (M{num:02d})"
    else:
        immersion_target = f"15-35% (M{num:02d})"

    replacements = {
        "{CONTENT_PATH}": str(files["content"]),
        "{ACTIVITIES_PATH}": str(files["activities"]),
        "{VOCAB_PATH}": str(files["vocabulary"]),
        "{PLAN_PATH}": str(files["plan"]),
        "{META_PATH}": str(files["meta"]),
        "{RESEARCH_PATH}": str(files["research"]),
        "{OUTPUT_PATH}": str(files["orchestration"] / "phase-5-re-review.md"),
        "{AUDIT_WORD_COUNT}": str(metrics.get("audit_words", "?")),
        "{WORD_TARGET}": str(word_target),
        "{WORD_PERCENT}": metrics.get("word_percent", "?"),
        "{ACTIVITY_COUNT}": str(activity_count),
        "{VOCAB_COUNT}": str(vocab_count),
        "{ENGAGEMENT_COUNT}": str(engagement),
        "{IMMERSION_PERCENT}": "?",  # Would need parsing from audit output
        "{IMMERSION_TARGET}": immersion_target,
        "{AUDIT_STATUS}": metrics.get("overall_status", "PASS").upper(),
        "{TOPIC_TITLE}": title,
        "{LEVEL}": level.upper(),
        "{MODULE_NUM}": f"{num:02d}",
        "{PREV_MODULE}": str(num - 1),
        "{TRACK}": level,
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    dest.write_text(text)
    return dest


# ─── Gemini Interaction ──────────────────────────────────────────────

def call_gemini(prompt_path: Path, task_id: str, model: str) -> Path:
    """Send prompt to Gemini, return path to output file."""
    output = Path(tempfile.mkstemp(suffix=".txt", prefix=f"gemini-{task_id}-")[1])

    prompt_content = prompt_path.read_text("utf-8")
    full_prompt = (
        f"{prompt_content}\n\nIMPORTANT: Put fixed files between delimiter lines like "
        f"===CONTENT_START=== and ===CONTENT_END=== on their own lines, NOT inside code blocks."
    )
    result = subprocess.run(
        [
            str(VENV_PYTHON), str(REPO / "scripts/ai_agent_bridge/__main__.py"),
            "ask-gemini",
            "-",  # read prompt from stdin
            "--task-id", task_id,
            "--stdout-only",
            "--model", model,
        ],
        capture_output=True, text=True, input=full_prompt,
        timeout=GEMINI_TIMEOUT, cwd=str(REPO),
    )

    output.write_text(result.stdout + result.stderr)
    return output


def call_gemini_review(prompt_path: Path, task_id: str, model: str) -> Path:
    """Send review prompt to Gemini with delimiter instructions."""
    output = Path(tempfile.mkstemp(suffix=".txt", prefix=f"gemini-{task_id}-")[1])

    prompt_content = prompt_path.read_text("utf-8")
    full_prompt = f"{prompt_content}\n\nWrap the ENTIRE review between ===REVIEW_START=== and ===REVIEW_END=== delimiters."
    result = subprocess.run(
        [
            str(VENV_PYTHON), str(REPO / "scripts/ai_agent_bridge/__main__.py"),
            "ask-gemini",
            "-",  # read prompt from stdin
            "--task-id", task_id,
            "--stdout-only",
            "--model", model,
        ],
        capture_output=True, text=True, input=full_prompt,
        timeout=GEMINI_TIMEOUT, cwd=str(REPO),
    )

    output.write_text(result.stdout + result.stderr)
    return output


# ─── Output Extraction ───────────────────────────────────────────────

def extract_section(output_path: Path, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiters, handling code block wrapping."""
    text = output_path.read_text()
    # Strip code block markers that Gemini sometimes wraps around delimiters
    # e.g., ```\n===CONTENT_START===\n...\n===CONTENT_END===\n```
    cleaned = re.sub(r'```\w*\n', '', text)
    cleaned = re.sub(r'\n```', '', cleaned)
    pattern = re.compile(
        rf'{re.escape(start_tag)}\s*\n(.*?)\n\s*{re.escape(end_tag)}',
        re.DOTALL
    )
    match = pattern.search(cleaned)
    if match:
        return match.group(1)
    # Fallback: try original text without cleaning
    match = pattern.search(text)
    return match.group(1) if match else None


def extract_score(review_text: str) -> float | None:
    """Extract overall score from review."""
    # Look for "Overall Score: X.X/10" or "Weighted Overall: X.X/10"
    patterns = [
        r'\*\*Overall Score:\*\*\s*(\d+\.?\d*)/10',
        r'Overall Score:\s*(\d+\.?\d*)/10',
        r'\*\*(\d+\.?\d*)/10\*\*\s*$',
        r'=\s*\*\*(\d+\.?\d*)/10\*\*',
    ]
    for pat in patterns:
        match = re.search(pat, review_text, re.MULTILINE)
        if match:
            return float(match.group(1))
    return None


def extract_status(review_text: str) -> str:
    """Extract PASS/FAIL from review."""
    match = re.search(r'\*\*Status:\*\*\s*(PASS|FAIL)', review_text)
    return match.group(1) if match else "UNKNOWN"


# ─── Audit ───────────────────────────────────────────────────────────

def run_audit(content_path: Path) -> bool:
    """Run audit_module.sh and return True if PASS."""
    try:
        result = subprocess.run(
            [str(REPO / "scripts/audit_module.sh"), str(content_path)],
            capture_output=True, text=True, timeout=120,
            cwd=str(REPO),
        )
        return "AUDIT PASSED" in result.stdout
    except Exception:
        return False


# ─── Main Fix+Review Loop ───────────────────────────────────────────

def _check_existing_reviews(files: dict, result: dict) -> tuple[str, float | None]:
    """Check for existing passing reviews. Returns (status, existing_score).
    Status is 'ALREADY_PASS' if passing, 'continue' otherwise."""
    review_path = files["orchestration"] / "phase-5-response.md"
    re_review_path = files["orchestration"] / "phase-5-re-review.md"

    if re_review_path.exists():
        text = re_review_path.read_text()
        score = extract_score(text)
        if score and score >= PASS_THRESHOLD:
            result["status"] = "ALREADY_PASS"
            result["score"] = score
            return "ALREADY_PASS", score

    existing_score = None
    if review_path.exists():
        text = review_path.read_text()
        existing_score = extract_score(text)
        status = extract_status(text)
        if existing_score and existing_score >= PASS_THRESHOLD and status == "PASS":
            result["status"] = "ALREADY_PASS"
            result["score"] = existing_score
            return "ALREADY_PASS", existing_score

    return "continue", existing_score


def _run_initial_review(files: dict, slug: str, level: str, model: str, result: dict) -> tuple[str, float | None]:
    """Run initial Phase 5 review. Returns (status, score)."""
    review_path = files["orchestration"] / "phase-5-response.md"

    print("    \u2192 No review found. Running Phase 5 review...")
    run_audit(files["content"])
    prompt = assemble_review_prompt(files, level)
    task_id = f"review-{slug}-initial"
    try:
        output = call_gemini_review(prompt, task_id, model)
        review_text = extract_section(output, "===REVIEW_START===", "===REVIEW_END===")
        if review_text:
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(review_text)
            existing_score = extract_score(review_text)
            print(f"    \u2192 Initial review: {existing_score}/10")

            if existing_score and existing_score >= PASS_THRESHOLD:
                files["review"].write_text(review_text)
                result["status"] = "PASS_ON_REVIEW"
                result["score"] = existing_score
                return "PASS_ON_REVIEW", existing_score
            output.unlink(missing_ok=True)
            return "continue", existing_score
        else:
            result["status"] = "ERROR"
            result["reason"] = "No delimited review in Gemini output"
            output.unlink(missing_ok=True)
            return "ERROR", None
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["phase"] = "initial_review"
        return "TIMEOUT", None
    except Exception as e:
        result["status"] = "ERROR"
        result["reason"] = str(e)[:200]
        return "ERROR", None


def _apply_fix_output(fix_output: Path, files: dict, attempt: int) -> tuple[list[str], int]:
    """Extract and write fixed files from Gemini output. Returns (files_changed, consecutive_no_changes_delta)."""
    content_text = extract_section(fix_output, "===CONTENT_START===", "===CONTENT_END===")
    activities_text = extract_section(fix_output, "===ACTIVITIES_START===", "===ACTIVITIES_END===")
    vocab_text = extract_section(fix_output, "===VOCABULARY_START===", "===VOCABULARY_END===")
    changes_text = extract_section(fix_output, "===CHANGES_START===", "===CHANGES_END===")

    files_changed = []
    if content_text and len(content_text.strip()) > 100:
        files["content"].write_text(content_text)
        files_changed.append("content")
    if activities_text and len(activities_text.strip()) > 50:
        files["activities"].write_text(activities_text)
        files_changed.append("activities")
    if vocab_text and len(vocab_text.strip()) > 50:
        files["vocabulary"].write_text(vocab_text)
        files_changed.append("vocabulary")

    if changes_text:
        (files["orchestration"] / f"fix-changes-v{attempt}.md").write_text(changes_text)

    if not files_changed:
        debug_path = files["orchestration"] / f"fix-debug-v{attempt}.txt"
        if fix_output.exists():
            raw = fix_output.read_text()
            debug_content = f"=== RAW OUTPUT ({len(raw)} chars) ===\n"
            debug_content += raw[:2000] + "\n...\n" + raw[-2000:] if len(raw) > 4000 else raw
            debug_path.write_text(debug_content)

    return files_changed, 0 if files_changed else 1


def process_module(level: str, num: int, model: str, dry_run: bool = False,
                   review_only: bool = False) -> dict:
    """Process a single module through fix+review loop."""
    files = find_module_files(level, num)
    if not files:
        return {"num": num, "status": "SKIP", "reason": "no content file"}

    slug = files["slug"]
    title = get_module_title(files)
    result = {"num": num, "slug": slug, "title": title}

    review_path = files["orchestration"] / "phase-5-response.md"
    re_review_path = files["orchestration"] / "phase-5-re-review.md"

    # Check existing reviews
    check_status, existing_score = _check_existing_reviews(files, result)
    if check_status == "ALREADY_PASS":
        return result

    # Run initial review if needed
    if not review_path.exists():
        if dry_run:
            result["status"] = "DRY_RUN"
            result["action"] = "needs Phase 5 review first"
            return result
        review_status, existing_score = _run_initial_review(files, slug, level, model, result)
        if review_status != "continue":
            return result

    if review_only:
        result["status"] = "REVIEWED"
        result["score"] = existing_score
        return result

    if dry_run:
        result["status"] = "DRY_RUN"
        result["action"] = f"fix from {existing_score}/10"
        return result

    # Fix + Re-review loop
    return _fix_review_loop(files, slug, level, model, result, existing_score,
                            review_path, re_review_path)


def _run_fix_attempt(files, slug, model, attempt):
    """Run a single fix attempt. Returns (fix_output, error_result) or raises."""
    fix_prompt = assemble_fix_prompt(files, files.get("_current_review"))
    fix_task_id = f"fix-{slug}-v{attempt}"
    try:
        return call_gemini(fix_prompt, fix_task_id, model), None
    except subprocess.TimeoutExpired:
        return None, {"status": "TIMEOUT", "phase": f"fix_attempt_{attempt}"}
    except Exception as e:
        return None, {"status": "ERROR", "reason": str(e)[:200]}


def _run_re_review(files, slug, level, model, attempt):
    """Run re-review after fix. Returns (review_text, error_result)."""
    review_prompt = assemble_review_prompt(files, level)
    review_task_id = f"review-{slug}-v{attempt}"
    try:
        review_output = call_gemini_review(review_prompt, review_task_id, model)
    except subprocess.TimeoutExpired:
        return None, {"status": "TIMEOUT", "phase": f"review_attempt_{attempt}"}
    except Exception as e:
        return None, {"status": "ERROR", "reason": str(e)[:200]}

    review_text = extract_section(review_output, "===REVIEW_START===", "===REVIEW_END===")
    review_output.unlink(missing_ok=True)
    return review_text, None


def _fix_review_loop(files, slug, level, model, result, existing_score,
                     review_path, re_review_path):
    """Run the fix+review loop until pass or max retries."""
    files["_current_review"] = review_path
    consecutive_no_changes = 0

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"    \u2192 Fix attempt {attempt}/{MAX_RETRIES}...")

        fix_output, err = _run_fix_attempt(files, slug, model, attempt)
        if err:
            result.update(err)
            return result

        files_changed, no_change_delta = _apply_fix_output(fix_output, files, attempt)

        if not files_changed:
            consecutive_no_changes += no_change_delta
            print("    \u2192 No files changed by fix (Gemini found nothing to fix)")
            if consecutive_no_changes >= 2:
                print("    \u2192 Breaking: fix produced no changes twice \u2014 needs manual intervention")
                result["status"] = "STUCK"
                result["score"] = existing_score
                result["reason"] = "Fix phase produces no changes but score < 9.0"
                return result
        else:
            consecutive_no_changes = 0
            print(f"    \u2192 Fixed: {', '.join(files_changed)}")

        fix_output.unlink(missing_ok=True)

        if not run_audit(files["content"]):
            print("    \u2192 Audit FAILED after fix. Retrying...")
            continue

        review_text, err = _run_re_review(files, slug, level, model, attempt)
        if err:
            result.update(err)
            return result
        if not review_text:
            print("    \u2192 No delimited review in output. Retrying...")
            continue

        new_score = extract_score(review_text)
        new_status = extract_status(review_text)
        print(f"    \u2192 Re-review: {new_score}/10 ({new_status})")

        if existing_score and new_score and (new_score - existing_score) > SUSPICIOUS_JUMP:
            print(f"    \u26a0\ufe0f  Suspicious jump: {existing_score} \u2192 {new_score} (+{new_score - existing_score:.1f})")

        re_review_path.write_text(review_text)
        files["review"].write_text(review_text)

        if new_score and new_score >= PASS_THRESHOLD:
            result["status"] = "FIXED"
            result["score_before"] = existing_score
            result["score_after"] = new_score
            result["attempts"] = attempt
            return result

        files["_current_review"] = re_review_path
        existing_score = new_score

    result["status"] = "FAIL_AFTER_RETRIES"
    result["score"] = existing_score
    result["attempts"] = MAX_RETRIES
    return result


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch fix + review to reach 9.0+")
    parser.add_argument("level", help="Level (e.g., a1, a2, b1)")
    parser.add_argument("--from", dest="from_num", type=int, default=1)
    parser.add_argument("--to", dest="to_num", type=int, default=20)
    parser.add_argument("--module", type=int, help="Process a single module")
    parser.add_argument("--model", default="gemini-3.1-pro-preview")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--review-only", action="store_true", help="Only run reviews, no fixes")
    args = parser.parse_args()

    # Enforce max 20 per batch
    if args.module:
        modules = [args.module]
    else:
        to_num = min(args.to_num, args.from_num + 19)  # Max 20 modules
        if to_num < args.to_num:
            print(f"⚠️  Capped batch at 20 modules: M{args.from_num:02d}-M{to_num:02d}")
        modules = list(range(args.from_num, to_num + 1))

    print(f"{'=' * 60}")
    print(f"Batch Fix+Review: {args.level.upper()} M{modules[0]:02d}-M{modules[-1]:02d}")
    print(f"Model: {args.model}")
    print(f"Target: {PASS_THRESHOLD}/10 | Max retries: {MAX_RETRIES}")
    if args.dry_run:
        print("MODE: DRY RUN (no changes)")
    if args.review_only:
        print("MODE: REVIEW ONLY (no fixes)")
    print(f"{'=' * 60}\n")

    results = []
    for num in modules:
        print(f"--- M{num:02d} ---")
        t0 = time.time()
        result = process_module(args.level, num, args.model, args.dry_run, args.review_only)
        elapsed = time.time() - t0
        result["elapsed_s"] = round(elapsed, 1)
        results.append(result)

        status = result["status"]
        if status == "ALREADY_PASS":
            print(f"  ✅ Already {result['score']}/10 — skipping")
        elif status == "PASS_ON_REVIEW":
            print(f"  ✅ Initial review: {result['score']}/10 — no fix needed")
        elif status == "FIXED":
            print(f"  ✅ {result.get('score_before', '?')} → {result['score_after']}/10 "
                  f"(attempt {result['attempts']}, {result['elapsed_s']}s)")
        elif status == "REVIEWED":
            print(f"  📋 Reviewed: {result.get('score', '?')}/10")
        elif status == "DRY_RUN":
            print(f"  🔍 Would: {result.get('action', '?')}")
        elif status == "SKIP":
            print(f"  ⏭️  Skip: {result.get('reason', '')}")
        elif status == "FAIL_AFTER_RETRIES":
            print(f"  ❌ Still {result.get('score', '?')}/10 after {MAX_RETRIES} attempts")
        else:
            print(f"  ❌ {status}: {result.get('reason', result.get('phase', ''))}")

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    passed = [r for r in results if r["status"] in ("ALREADY_PASS", "PASS_ON_REVIEW", "FIXED")]
    failed = [r for r in results if r["status"] in ("FAIL_AFTER_RETRIES", "ERROR", "TIMEOUT", "STUCK")]
    skipped = [r for r in results if r["status"] == "SKIP"]

    print(f"  ✅ Passed: {len(passed)}")
    for r in passed:
        score = r.get("score_after", r.get("score", "?"))
        print(f"     M{r['num']:02d} {r.get('slug', '')}: {score}/10")

    if failed:
        print(f"  ❌ Failed: {len(failed)}")
        for r in failed:
            print(f"     M{r['num']:02d} {r.get('slug', '')}: {r['status']} "
                  f"({r.get('reason', r.get('score', '?'))})")

    if skipped:
        print(f"  ⏭️  Skipped: {len(skipped)}")

    total_time = sum(r.get("elapsed_s", 0) for r in results)
    print(f"\n  Total time: {total_time:.0f}s ({total_time/60:.1f} min)")
    print(f"  Gemini calls: ~{len(passed) * 2 + len(failed) * MAX_RETRIES * 2}")


if __name__ == "__main__":
    main()
