#!/usr/bin/env python3
"""Batch Phase 5 review: assemble prompts and send to Gemini for all modules in a level.

Usage:
    .venv/bin/python scripts/batch_review.py a1 --from 1 --to 44
    .venv/bin/python scripts/batch_review.py a1 --from 1 --to 13 --model gemini-3-pro-preview
    .venv/bin/python scripts/batch_review.py a1 --module 9  # single module
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Add shared utils to path
sys.path.append(str(Path(__file__).parent))
from utils.extraction import extract_delimited

REPO = Path(__file__).parent.parent
TEMPLATE_PATH = REPO / "claude_extensions/phases/gemini/phase-5-review.md"


def find_module_files(level: str, num: int) -> dict | None:
    """Find all files for a module by number. Returns dict of paths or None."""
    level_dir = REPO / f"curriculum/l2-uk-en/{level}"

    # Find content file by number prefix
    content_files = sorted(level_dir.glob(f"{num:02d}-*.md"))
    if not content_files:
        return None

    content_path = content_files[0]
    slug = content_path.stem[3:]  # Remove "01-" prefix
    full_stem = content_path.stem  # "01-the-cyrillic-code-i"

    # Activities/vocabulary/meta use full stem with number prefix
    # Plan uses slug without number prefix
    activities_path = level_dir / f"activities/{full_stem}.yaml"
    if not activities_path.exists():
        activities_path = level_dir / f"activities/{slug}.yaml"
    vocab_path = level_dir / f"vocabulary/{full_stem}.yaml"
    if not vocab_path.exists():
        vocab_path = level_dir / f"vocabulary/{slug}.yaml"
    meta_path = level_dir / f"meta/{full_stem}.yaml"
    if not meta_path.exists():
        meta_path = level_dir / f"meta/{slug}.yaml"
    plan_path = REPO / f"curriculum/l2-uk-en/plans/{level}/{slug}.yaml"
    research_path = level_dir / f"research/{slug}-research.md"
    status_path = level_dir / f"status/{slug}.json"

    return {
        "num": num,
        "slug": slug,
        "content": content_path,
        "activities": activities_path,
        "vocabulary": vocab_path,
        "meta": meta_path,
        "plan": plan_path,
        "research": research_path,
        "status": status_path,
    }


def get_audit_metrics(files: dict) -> dict:
    """Extract audit metrics from status JSON and files."""
    metrics = {
        "word_count": "?",
        "word_target": "?",
        "word_percent": "?",
        "activity_count": "?",
        "vocab_count": "?",
        "engagement_count": "?",
        "immersion_percent": "?",
        "immersion_target": "15-35%",
        "audit_status": "?",
    }

    # Try status JSON
    if files["status"].exists():
        try:
            status = json.loads(files["status"].read_text())
            metrics["word_count"] = status.get("word_count", "?")
            metrics["word_target"] = status.get("word_target", "?")
            if metrics["word_count"] != "?" and metrics["word_target"] != "?":
                try:
                    metrics["word_percent"] = round(int(metrics["word_count"]) / int(metrics["word_target"]) * 100)
                except (ValueError, ZeroDivisionError):
                    pass
            metrics["activity_count"] = status.get("activity_count", "?")
            metrics["audit_status"] = status.get("status", "?")
        except (json.JSONDecodeError, KeyError):
            pass

    # Count vocab items
    if files["vocabulary"].exists():
        try:
            content = files["vocabulary"].read_text()
            metrics["vocab_count"] = content.count("- ukrainian:")
            if metrics["vocab_count"] == 0:
                metrics["vocab_count"] = content.count("ukrainian:")
        except Exception:
            pass

    # Count engagement boxes in content
    if files["content"].exists():
        try:
            content = files["content"].read_text()
            metrics["engagement_count"] = len(re.findall(r'>\s*\[!', content))
            # Rough immersion: count Ukrainian vs total lines
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#') and not l.startswith('>')]
            if lines:
                uk_pattern = re.compile(r'[а-яіїєґА-ЯІЇЄҐ]')
                uk_lines = sum(1 for l in lines if uk_pattern.search(l))
                metrics["immersion_percent"] = round(uk_lines / len(lines) * 100)
        except Exception:
            pass

    return metrics


def get_topic_title(files: dict) -> str:
    """Extract topic title from content file H1."""
    if files["content"].exists():
        for line in files["content"].read_text().split('\n'):
            if line.startswith('# '):
                return line[2:].strip()
    return files["slug"].replace("-", " ").title()


def assemble_prompt(template: str, files: dict, metrics: dict, level: str, output_path: str) -> str:
    """Fill template placeholders."""
    title = get_topic_title(files)

    replacements = {
        "{CONTENT_PATH}": str(files["content"]),
        "{ACTIVITIES_PATH}": str(files["activities"]) if files["activities"].exists() else "(no activities file)",
        "{VOCAB_PATH}": str(files["vocabulary"]) if files["vocabulary"].exists() else "(no vocabulary file)",
        "{PLAN_PATH}": str(files["plan"]) if files["plan"].exists() else "(no plan file)",
        "{META_PATH}": str(files["meta"]) if files["meta"].exists() else "(no meta file)",
        "{RESEARCH_PATH}": str(files["research"]) if files["research"].exists() else "(no research file)",
        "{OUTPUT_PATH}": output_path,
        "{AUDIT_WORD_COUNT}": str(metrics["word_count"]),
        "{WORD_TARGET}": str(metrics["word_target"]),
        "{WORD_PERCENT}": str(metrics["word_percent"]),
        "{ACTIVITY_COUNT}": str(metrics["activity_count"]),
        "{VOCAB_COUNT}": str(metrics["vocab_count"]),
        "{ENGAGEMENT_COUNT}": str(metrics["engagement_count"]),
        "{IMMERSION_PERCENT}": str(metrics["immersion_percent"]),
        "{IMMERSION_TARGET}": metrics["immersion_target"],
        "{AUDIT_STATUS}": str(metrics["audit_status"]),
        "{TOPIC_TITLE}": title,
        "{LEVEL}": level.upper(),
        "{MODULE_NUM}": f"{files['num']:02d}",
        "{date}": "2026-02-08",
    }

    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt


def review_module(level: str, num: int, model: str, dry_run: bool = False) -> dict:
    """Run Phase 5 review for a single module. Returns result dict."""
    files = find_module_files(level, num)
    if not files:
        return {"num": num, "status": "SKIP", "reason": "no content file"}

    if not files["content"].exists():
        return {"num": num, "status": "SKIP", "reason": "content missing"}

    # Setup orchestration directory
    orch_dir = REPO / f"curriculum/l2-uk-en/{level}/orchestration/{files['slug']}"
    orch_dir.mkdir(parents=True, exist_ok=True)

    output_path = str(orch_dir / "phase-5-response.md")
    prompt_path = orch_dir / "phase-5-prompt.md"

    # Read template and assemble prompt
    template = TEMPLATE_PATH.read_text()
    metrics = get_audit_metrics(files)
    prompt = assemble_prompt(template, files, metrics, level, output_path)

    # Write assembled prompt
    prompt_path.write_text(prompt)

    if dry_run:
        return {"num": num, "slug": files["slug"], "status": "DRY_RUN", "prompt": str(prompt_path)}

    # Call bridge
    task_id = f"batch-review-{level}-{num:02d}"
    msg = f"Read and execute the instructions at {prompt_path}. Write your output to: {output_path}"

    try:
        # Create a temp file for the raw output to prevent context pollution
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=f"gemini-review-{task_id}-", delete=False) as tf:
            raw_output_log = Path(tf.name)

        with open(raw_output_log, "w") as f:
            subprocess.run(
                [
                    sys.executable, str(REPO / "scripts/ai_agent_bridge.py"),
                    "ask-gemini", msg,
                    "--task-id", task_id,
                    "--output-path", output_path,
                    "--model", model,
                    "--quiet",
                ],
                stdout=f, stderr=subprocess.STDOUT, timeout=600,
                cwd=str(REPO),
            )

        # Check if output was written
        if Path(output_path).exists():
            content = Path(output_path).read_text()
            # Extract score
            score_match = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', content)
            score = score_match.group(1) if score_match else "?"
            verdict_match = re.search(r'\*\*(PASS|FAIL)\*\*', content)
            verdict = verdict_match.group(1) if verdict_match else "?"
            return {
                "num": num, "slug": files["slug"], "status": "OK",
                "score": score, "verdict": verdict, "output": output_path,
            }
        else:
            return {"num": num, "slug": files["slug"], "status": "ERROR", "reason": "no output file written"}

    except subprocess.TimeoutExpired:
        return {"num": num, "slug": files["slug"], "status": "TIMEOUT"}
    except Exception as e:
        return {"num": num, "slug": files["slug"], "status": "ERROR", "reason": str(e)[:200]}


def main():
    parser = argparse.ArgumentParser(description="Batch Phase 5 review for a level")
    parser.add_argument("level", help="Level (e.g., a1, b1)")
    parser.add_argument("--from", dest="from_num", type=int, default=1, help="Start module number")
    parser.add_argument("--to", dest="to_num", type=int, default=None, help="End module number (inclusive)")
    parser.add_argument("--module", type=int, help="Single module number")
    parser.add_argument("--model", default="gemini-3-pro-preview", help="Gemini model")
    parser.add_argument("--dry-run", action="store_true", help="Assemble prompts but don't send to Gemini")
    args = parser.parse_args()

    if args.module:
        modules = [args.module]
    else:
        to_num = args.to_num or 99
        modules = list(range(args.from_num, to_num + 1))

    print(f"{'='*60}")
    print(f"Batch Phase 5 Review: {args.level.upper()} M{modules[0]:02d}-M{modules[-1]:02d}")
    print(f"Model: {args.model}")
    print(f"{'='*60}\n")

    results = []
    for num in modules:
        print(f"\n--- M{num:02d} ---")
        result = review_module(args.level, num, args.model, args.dry_run)
        results.append(result)

        if result["status"] == "SKIP":
            print(f"  SKIP: {result.get('reason', '')}")
        elif result["status"] == "OK":
            print(f"  {result['verdict']} ({result['score']}/10) → {result.get('output', '')}")
        elif result["status"] == "DRY_RUN":
            print(f"  Prompt: {result.get('prompt', '')}")
        else:
            print(f"  {result['status']}: {result.get('reason', '')}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'M#':<5} {'Slug':<35} {'Score':<8} {'Verdict'}")
    print(f"{'-'*5} {'-'*35} {'-'*8} {'-'*7}")
    for r in results:
        if r["status"] == "OK":
            print(f"M{r['num']:02d}  {r.get('slug', ''):<35} {r.get('score', '?'):<8} {r.get('verdict', '?')}")
        elif r["status"] == "SKIP":
            print(f"M{r['num']:02d}  {'—':<35} {'—':<8} SKIP")
        else:
            print(f"M{r['num']:02d}  {r.get('slug', ''):<35} {'—':<8} {r['status']}")


if __name__ == "__main__":
    main()
