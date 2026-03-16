#!/usr/bin/env python3
"""Quick-iterate content prompt tester.

Sends an already-assembled content prompt to Gemini, extracts the content block,
measures word count and immersion %, saves output. No pipeline, no fix loops.

Usage:
    # Use existing prompt from orchestration dir:
    %(prog)s a1 47

    # Use a custom prompt file:
    %(prog)s --prompt path/to/prompt.md

    # Just measure an existing output:
    %(prog)s --measure path/to/output.md
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))


def measure_immersion(text: str) -> dict:
    """Measure Ukrainian vs English word ratio."""
    # Strip markdown formatting
    clean = re.sub(r'[#*|>\-`~\[\](){}!]', ' ', text)
    clean = re.sub(r'\s+', ' ', clean).strip()

    uk_chars = set('абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ')
    en_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

    words = clean.split()
    uk_words = 0
    en_words = 0
    other = 0

    for w in words:
        letters = set(w)
        if letters & uk_chars:
            uk_words += 1
        elif letters & en_chars:
            en_words += 1
        else:
            other += 1

    total = uk_words + en_words
    pct = (uk_words / total * 100) if total else 0
    return {
        "total_words": len(words),
        "uk_words": uk_words,
        "en_words": en_words,
        "other": other,
        "immersion_pct": round(pct, 1),
    }


def count_containers(text: str) -> dict:
    """Count structural containers in the content."""
    lines = text.split('\n')
    tables = len(re.findall(r'^\|.*\|.*\|', text, re.MULTILINE))
    dialogues = sum(1 for l in lines if l.strip().startswith('> —'))
    bullets = sum(1 for l in lines if re.match(r'^- \*\*', l))
    callouts = len(re.findall(r'>\s*\[!', text))
    h2s = sum(1 for l in lines if l.startswith('## '))
    return {
        "h2_sections": h2s,
        "table_rows": tables,
        "dialogue_lines": dialogues,
        "bulleted_examples": bullets,
        "callout_boxes": callouts,
    }


def extract_content(raw: str) -> str:
    """Extract content between ===CONTENT_START=== and ===CONTENT_END=== tags."""
    # Try various delimiter patterns
    for start_tag, end_tag in [
        ("===CONTENT_START===", "===CONTENT_END==="),
        ("===TAG_START===", "===TAG_END==="),
        ("```markdown", "```"),
    ]:
        if start_tag in raw and end_tag in raw:
            idx_start = raw.index(start_tag) + len(start_tag)
            idx_end = raw.index(end_tag, idx_start)
            return raw[idx_start:idx_end].strip()

    # No delimiters — return everything (Gemini sometimes writes directly)
    return raw.strip()


def strip_activities_section(prompt: str) -> str:
    """Remove activities/vocabulary sections from prompt for content-only testing."""
    # Cut everything from "## 4. Create Activities" onward, but keep self-audit
    cut_markers = [
        "## 4. Create Activities",
        "## 4. Activities",
    ]
    for marker in cut_markers:
        if marker in prompt:
            idx = prompt.index(marker)
            # Keep the output format section (## 6) but simplify it
            prompt = prompt[:idx] + """## 4. Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Output ONE block:

```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
-->

# {Title}

> **{intro hook}**

## {Section 1}
...

---

# Підсумок

{Summary + 3-4 self-check questions}

===CONTENT_END===
```
"""
            break
    return prompt


def run_prompt(prompt_path: Path, output_dir: Path, content_only: bool = True) -> Path:
    """Send prompt to Gemini and save raw output."""
    from pipeline.core import dispatch_gemini_raw

    prompt_text = prompt_path.read_text("utf-8")
    if content_only:
        prompt_text = strip_activities_section(prompt_text)
        print("(content-only mode — activities/vocab stripped from prompt)")
    timestamp = time.strftime("%H%M%S")
    output_file = output_dir / f"test-output-{timestamp}.md"

    print(f"Sending prompt ({len(prompt_text.split())} words) to Gemini...")
    t0 = time.time()

    ok, raw = dispatch_gemini_raw(
        prompt_text,
        task_id=f"test-content-{timestamp}",
        model="gemini-3-flash-preview",
        stdout_only=True,
        timeout=600,
    )

    elapsed = time.time() - t0
    print(f"Gemini responded in {elapsed:.0f}s (ok={ok})")

    if not ok:
        print(f"FAILED: {raw[:500]}")
        return output_file

    content = extract_content(raw)
    output_file.write_text(content, "utf-8")
    print(f"Saved → {output_file}")
    return output_file


def report(text: str) -> None:
    """Print quality report for content."""
    imm = measure_immersion(text)
    cont = count_containers(text)

    print("\n" + "=" * 50)
    print("CONTENT QUALITY REPORT")
    print("=" * 50)
    print(f"Words:      {imm['total_words']}")
    print(f"Ukrainian:  {imm['uk_words']} ({imm['immersion_pct']}%)")
    print(f"English:    {imm['en_words']}")
    print("---")
    print(f"H2 sections:      {cont['h2_sections']}")
    print(f"Table rows:       {cont['table_rows']}")
    print(f"Dialogue lines:   {cont['dialogue_lines']}")
    print(f"Bulleted examples:{cont['bulleted_examples']}")
    print(f"Callout boxes:    {cont['callout_boxes']}")
    print("=" * 50)

    # Quality flags
    flags = []
    if imm['immersion_pct'] < 35:
        flags.append(f"IMMERSION TOO LOW: {imm['immersion_pct']}% (target 35-55%)")
    if imm['immersion_pct'] > 55:
        flags.append(f"IMMERSION HIGH: {imm['immersion_pct']}% (target 35-55%)")
    if cont['dialogue_lines'] < 10:
        flags.append(f"FEW DIALOGUES: {cont['dialogue_lines']} lines (want 10+)")
    if cont['callout_boxes'] < 3:
        flags.append(f"FEW CALLOUTS: {cont['callout_boxes']} (want 3+)")
    if cont['bulleted_examples'] > 15:
        flags.append(f"EXAMPLE SPAM: {cont['bulleted_examples']} bullets (too many)")

    if flags:
        print("\nFLAGS:")
        for f in flags:
            print(f"  ⚠ {f}")
    else:
        print("\n✅ All checks pass")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quick-iterate content prompt tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("track", nargs="?", help="Track (e.g. a1)")
    parser.add_argument("num", nargs="?", type=int, help="Module number")
    parser.add_argument("--prompt", type=Path, help="Custom prompt file")
    parser.add_argument("--measure", type=Path, help="Just measure an existing file")
    parser.add_argument("--full", action="store_true", help="Include activities/vocab (slower)")
    args = parser.parse_args()

    if args.measure:
        text = args.measure.read_text("utf-8")
        report(text)
        return 0

    if args.prompt:
        prompt_path = args.prompt
        output_dir = prompt_path.parent
    elif args.track and args.num:
        from batch_gemini_config import get_module_index
        idx = get_module_index(args.track)
        slug = idx["num_to_slug"].get(args.num)
        if not slug:
            print(f"ERROR: No module #{args.num} in {args.track}")
            return 1
        orch_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / args.track / "orchestration" / slug
        prompt_path = orch_dir / "phase-2-prompt.md"
        output_dir = orch_dir
        if not prompt_path.exists():
            print(f"ERROR: No assembled prompt at {prompt_path}")
            print("Run the pipeline first to generate the prompt, or use --prompt")
            return 1
    else:
        parser.print_help()
        return 1

    output_file = run_prompt(prompt_path, output_dir, content_only=not args.full)
    if output_file.exists():
        text = output_file.read_text("utf-8")
        report(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
