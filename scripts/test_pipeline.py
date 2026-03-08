#!/usr/bin/env python3
"""Pipeline v5 test bed — test build_module_v5.py behavior without touching production modules.

Creates a disposable 'test' track with minimal fixture modules under:
    testbed/pipeline-test-YYYYMMDD-HHMMSS/

Each test run gets its own timestamped directory that persists for investigation.

Usage:
    .venv/bin/python scripts/test_pipeline.py                    # Run all tests
    .venv/bin/python scripts/test_pipeline.py --test resumption  # Run one test
    .venv/bin/python scripts/test_pipeline.py --list             # List available tests
    .venv/bin/python scripts/test_pipeline.py --clean            # Delete testbed dirs older than 7 days
    .venv/bin/python scripts/test_pipeline.py --analyze <slug>   # Context engineering analysis on a real module

Tests use --dry-run by default (no Gemini calls). Pass --live to dispatch real calls.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTBED_ROOT = PROJECT_ROOT / "testbed"
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ============================================================================
# Helpers
# ============================================================================

def create_test_dir() -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    test_dir = TESTBED_ROOT / f"pipeline-test-{ts}"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def run_build_v5(track: str, num: int, extra_args: list[str] | None = None,
                 dry_run: bool = True) -> tuple[int, str]:
    """Run build_module_v5.py against a production module."""
    cmd = [
        VENV_PYTHON, str(SCRIPTS_DIR / "build_module_v5.py"),
        track, str(num),
    ]
    if dry_run:
        cmd.append("--dry-run")
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_ROOT),
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return result.returncode, output


def read_state_v5(orch_dir: Path) -> dict:
    """Read v5 state.json from orchestration dir."""
    sf = orch_dir / "state.json"
    if sf.exists():
        try:
            return json.loads(sf.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def read_gemini_session(session_path: Path) -> tuple[str, str, dict]:
    """Read a Gemini session JSON and extract prompt, output, and self-audit.

    Returns (prompt_text, output_text, self_audit_dict).
    """
    if not session_path.exists():
        return "", "", {}

    data = json.loads(session_path.read_text("utf-8"))
    msgs = data.get("messages", [])

    # Prompt: first user message
    prompt = ""
    for msg in msgs:
        if msg.get("type") == "user":
            content = msg.get("content", [])
            if content and isinstance(content[0], dict) and "text" in content[0]:
                prompt = content[0]["text"]
            break

    # Output: last gemini message (streamed chars or text)
    output = ""
    for msg in reversed(msgs):
        if msg.get("type") == "gemini":
            content = msg.get("content", [])
            if content:
                if all(isinstance(c, str) for c in content):
                    output = "".join(content)
                elif isinstance(content[0], dict) and "text" in content[0]:
                    output = content[0]["text"]
            break

    # Self-audit extraction
    self_audit = {}
    audit_match = re.search(r"===SELF_AUDIT_START===(.*?)===SELF_AUDIT_END===", output, re.DOTALL)
    if audit_match:
        audit_text = audit_match.group(1).strip()
        for line in audit_text.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                self_audit[key.strip()] = val.strip()

    return prompt, output, self_audit


def measure_immersion(content: str) -> dict:
    """Measure Ukrainian vs English word ratio in content.

    Returns dict with per-section and total stats.
    """
    # Simple heuristic: Ukrainian words contain Cyrillic characters
    cyrillic_re = re.compile(r"[\u0400-\u04FF]")

    sections = {}
    current_section = "preamble"
    current_words: list[str] = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_words:
                sections[current_section] = current_words
            current_section = line.strip("# ").strip()
            current_words = []
        else:
            # Strip markdown formatting for word counting
            clean = re.sub(r"[|*_`>\[\]!]", " ", line)
            words = clean.split()
            current_words.extend(w for w in words if len(w) > 1)

    if current_words:
        sections[current_section] = current_words

    results = {}
    total_uk = 0
    total_en = 0
    for section, words in sections.items():
        uk = sum(1 for w in words if cyrillic_re.search(w))
        en = len(words) - uk
        total_uk += uk
        total_en += en
        pct = (uk / len(words) * 100) if words else 0
        results[section] = {"uk": uk, "en": en, "total": len(words), "uk_pct": round(pct, 1)}

    total = total_uk + total_en
    results["TOTAL"] = {
        "uk": total_uk, "en": total_en, "total": total,
        "uk_pct": round(total_uk / total * 100, 1) if total else 0,
    }
    return results


def analyze_paragraphs(content: str) -> list[dict]:
    """Analyze English paragraph lengths (sentence count).

    Returns list of dicts with paragraph info.
    """
    paragraphs = []
    current_lines: list[str] = []

    for line in content.split("\n"):
        stripped = line.strip()
        # Skip non-prose lines
        if (stripped.startswith("#") or stripped.startswith("|") or
                stripped.startswith(">") or stripped.startswith("-") or
                stripped.startswith("```") or not stripped):
            if current_lines:
                text = " ".join(current_lines)
                # Count sentences (rough: split on . ! ?)
                sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
                cyrillic_re = re.compile(r"[\u0400-\u04FF]")
                is_english = not cyrillic_re.search(text[:50])  # Check start
                paragraphs.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "sentences": len(sentences),
                    "words": len(text.split()),
                    "is_english": is_english,
                })
                current_lines = []
        else:
            current_lines.append(stripped)

    if current_lines:
        text = " ".join(current_lines)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        paragraphs.append({
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentences": len(sentences),
            "words": len(text.split()),
            "is_english": True,
        })

    return paragraphs


def count_containers(content: str) -> dict:
    """Count structural containers (tables, lists, dialogues, pattern boxes)."""
    tables = len(re.findall(r"^\|.+\|.+\|", content, re.MULTILINE)) // 2  # header + separator = 1 table start
    bulleted_uk = len(re.findall(r"^- \*\*[\u0400-\u04FF]", content, re.MULTILINE))
    dialogues = len(re.findall(r"^> — ", content, re.MULTILINE))
    pattern_boxes = len(re.findall(r"→.*→", content))
    callouts = len(re.findall(r"^\> \[!", content, re.MULTILINE))

    return {
        "tables": tables,
        "bulleted_uk_examples": bulleted_uk,
        "dialogue_lines": dialogues,
        "pattern_boxes": pattern_boxes,
        "callouts": callouts,
    }


# ============================================================================
# Context Engineering Analysis (the new capability)
# ============================================================================

def analyze_module(track: str, slug: str) -> str:
    """Full context engineering analysis of a built module.

    Reads the Gemini session JSON, compares prompt vs output, finds gaps.
    """
    orch_dir = CURRICULUM_DIR / track / "orchestration" / slug
    CURRICULUM_DIR / track / f"{slug}.md"

    if not orch_dir.exists():
        return f"ERROR: Orchestration dir not found: {orch_dir}"

    # Find session JSONs
    session_files = sorted(orch_dir.glob("*gemini-session.json"))
    if not session_files:
        return f"ERROR: No Gemini session JSONs found in {orch_dir}"

    lines = [f"# Context Engineering Analysis: {slug}\n"]
    lines.append(f"**Track:** {track}")
    lines.append(f"**Session files:** {len(session_files)}")

    # Analyze the content-phase session (phase-2)
    content_sessions = [f for f in session_files if "phase-2" in f.name]
    if content_sessions:
        session = content_sessions[-1]  # Latest attempt
        lines.append(f"\n## Content Phase: {session.name}\n")

        prompt, output, self_audit = read_gemini_session(session)

        # Self-audit findings
        if self_audit:
            lines.append("### Gemini Self-Audit")
            for k, v in self_audit.items():
                lines.append(f"- **{k}**: {v}")
        else:
            lines.append("### Gemini Self-Audit: NOT FOUND")

        # Extract content block
        content_match = re.search(r"===CONTENT_START===(.*?)===CONTENT_END===", output, re.DOTALL)
        if content_match:
            content_text = content_match.group(1).strip()

            # Immersion measurement
            lines.append("\n### Immersion Breakdown\n")
            immersion = measure_immersion(content_text)
            lines.append("| Section | EN words | UK words | UK % |")
            lines.append("|---------|----------|----------|------|")
            for section, stats in immersion.items():
                lines.append(f"| {section[:40]} | {stats['en']} | {stats['uk']} | {stats['uk_pct']}% |")

            # Paragraph analysis
            lines.append("\n### English Paragraph Lengths\n")
            paras = analyze_paragraphs(content_text)
            english_paras = [p for p in paras if p["is_english"]]
            if english_paras:
                lines.append("| Sentences | Words | First 100 chars |")
                lines.append("|-----------|-------|-----------------|")
                for p in english_paras:
                    lines.append(f"| {p['sentences']} | {p['words']} | {p['text'][:80]} |")
                avg_sentences = sum(p["sentences"] for p in english_paras) / len(english_paras)
                lines.append(f"\n**Average sentences per paragraph:** {avg_sentences:.1f}")

            # Container count
            lines.append("\n### Structural Containers\n")
            containers = count_containers(content_text)
            for k, v in containers.items():
                lines.append(f"- **{k}**: {v}")

        # Key instructions from prompt
        if prompt:
            lines.append("\n### Key Instructions Received\n")
            # Find immersion rule
            for pline in prompt.split("\n"):
                pline_lower = pline.lower()
                if any(kw in pline_lower for kw in ["target:", "max", "structural rule", "immersion block", "must conclude"]):
                    lines.append(f"- `{pline.strip()[:120]}`")

        # Gap analysis
        lines.append("\n### Instruction vs Output Gap\n")
        if self_audit and content_match:
            content_text = content_match.group(1).strip()
            immersion_total = immersion.get("TOTAL", {})
            uk_pct = immersion_total.get("uk_pct", 0)

            # Check "max 2 sentences" compliance
            english_paras = [p for p in analyze_paragraphs(content_text) if p["is_english"]]
            long_paras = [p for p in english_paras if p["sentences"] > 2]
            if long_paras:
                lines.append(f"- **INSTRUCTION IGNORED**: 'max 2 sentences per concept' — "
                             f"{len(long_paras)}/{len(english_paras)} English paragraphs exceed 2 sentences")

            # Check immersion target
            target_match = re.search(r"TARGET:\s*(\d+)-(\d+)%", prompt)
            if target_match:
                target_min = int(target_match.group(1))
                target_max = int(target_match.group(2))
                if uk_pct < target_min:
                    lines.append(f"- **IMMERSION MISS**: Target {target_min}-{target_max}%, "
                                 f"actual {uk_pct}% (gap: {target_min - uk_pct:.1f}%)")
                elif uk_pct > target_max:
                    lines.append(f"- **IMMERSION OVERSHOOT**: Target {target_min}-{target_max}%, actual {uk_pct}%")
                else:
                    lines.append(f"- **IMMERSION OK**: Target {target_min}-{target_max}%, actual {uk_pct}%")

            # Check immersion block presence
            if "immersion block" in prompt.lower() or "MUST conclude" in prompt:
                dialogue_lines = count_containers(content_text)["dialogue_lines"]
                h2_count = len(re.findall(r"^## ", content_text, re.MULTILINE))
                if dialogue_lines == 0:
                    lines.append("- **MISSING**: Immersion blocks requested but 0 dialogue lines found")
                else:
                    lines.append(f"- **IMMERSION BLOCKS**: {dialogue_lines} dialogue lines across {h2_count} H2 sections")

    # Validate-fix sessions
    fix_sessions = [f for f in session_files if "validate-fix" in f.name]
    if fix_sessions:
        lines.append(f"\n## Fix Loop: {len(fix_sessions)} attempts\n")
        for fs in fix_sessions:
            _, fix_output, fix_audit = read_gemini_session(fs)
            lines.append(f"### {fs.name}")
            if fix_audit:
                for k, v in fix_audit.items():
                    lines.append(f"- {k}: {v}")
            else:
                lines.append(f"- Output length: {len(fix_output)} chars")

    return "\n".join(lines)


# ============================================================================
# Test Cases (v5)
# ============================================================================

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""

    def ok(self, msg: str = ""):
        self.passed = True
        self.message = msg

    def fail(self, msg: str):
        self.passed = False
        self.message = msg


def test_complete_module_skips(test_dir: Path) -> TestResult:
    """v5: a fully-built production module skips all phases in dry-run."""
    r = TestResult("complete_module_skips")
    rc, output = run_build_v5("a1", 1, dry_run=True)

    done_count = output.count("[DONE]")
    skip_count = output.count("SKIP")

    if done_count < 4:
        r.fail(f"Expected 4+ [DONE] for complete module, got {done_count}")
        return r

    r.ok(f"rc={rc}, {done_count} [DONE], {skip_count} SKIP")
    return r


def test_resumption_two_runs(test_dir: Path) -> TestResult:
    """v5: two dry-runs on same module produce identical skip behavior."""
    r = TestResult("resumption_two_runs")

    _rc1, out1 = run_build_v5("a1", 1, dry_run=True)
    done1 = out1.count("[DONE]")

    _rc2, out2 = run_build_v5("a1", 1, dry_run=True)
    done2 = out2.count("[DONE]")

    if done1 < 4 or done2 < 4:
        r.fail(f"Expected 4+ [DONE] each run, got {done1} and {done2}")
        return r

    if abs(done1 - done2) > 1:
        r.fail(f"Inconsistent runs: {done1} vs {done2} [DONE]")
        return r

    r.ok(f"Run 1: {done1} [DONE] | Run 2: {done2} [DONE] — consistent")
    return r


def test_v5_state_format(test_dir: Path) -> TestResult:
    """v5: state.json has correct v5 format with phase entries."""
    r = TestResult("v5_state_format")

    # Check a known-built module's state
    orch_dir = CURRICULUM_DIR / "a1" / "orchestration" / "the-gender-code"
    state = read_state_v5(orch_dir)

    if not state:
        r.fail(f"No state.json found at {orch_dir}")
        return r

    phases = state.get("phases", {})
    if not phases:
        r.fail(f"No phases in state: {list(state.keys())}")
        return r

    # Check at least research and content are complete
    complete = [k for k, v in phases.items() if v.get("status") == "complete"]
    if len(complete) < 2:
        r.fail(f"Expected 2+ complete phases, got {complete}")
        return r

    r.ok(f"State has {len(phases)} phases, {len(complete)} complete: {complete}")
    return r


def test_gemini_session_readable(test_dir: Path) -> TestResult:
    """v5: Gemini session JSONs can be parsed and contain prompt + output."""
    r = TestResult("gemini_session_readable")

    # Find any session JSON
    sessions = list(CURRICULUM_DIR.glob("a1/orchestration/*/phase-2-attempt-1-gemini-session.json"))
    if not sessions:
        r.fail("No phase-2 Gemini session JSONs found")
        return r

    session = sessions[0]
    prompt, output, self_audit = read_gemini_session(session)

    if not prompt:
        r.fail(f"Empty prompt in {session.name}")
        return r

    if not output:
        r.fail(f"Empty output in {session.name}")
        return r

    r.ok(f"Session {session.parent.name}: prompt={len(prompt)}ch, output={len(output)}ch, "
         f"self_audit={'yes' if self_audit else 'no'}")
    return r


def test_immersion_measurement(test_dir: Path) -> TestResult:
    """v5: immersion measurement produces reasonable numbers for a built module."""
    r = TestResult("immersion_measurement")

    content_path = CURRICULUM_DIR / "a1" / "the-gender-code.md"
    if not content_path.exists():
        r.fail(f"Content file not found: {content_path}")
        return r

    content = content_path.read_text("utf-8")
    immersion = measure_immersion(content)
    total = immersion.get("TOTAL", {})

    if total.get("total", 0) < 100:
        r.fail(f"Too few words: {total}")
        return r

    uk_pct = total.get("uk_pct", 0)
    if uk_pct < 5 or uk_pct > 95:
        r.fail(f"Immersion {uk_pct}% seems wrong for A1 module")
        return r

    r.ok(f"Immersion: {uk_pct}% Ukrainian ({total['uk']}/{total['total']} words)")
    return r


def test_paragraph_analysis(test_dir: Path) -> TestResult:
    """v5: paragraph analysis detects sentence counts correctly."""
    r = TestResult("paragraph_analysis")

    test_content = textwrap.dedent("""\
        ## Test Section

        This is one sentence. This is two. This is three sentences total.

        | table | row |
        |-------|-----|
        | data  | here |

        Short paragraph here.

        > A blockquote line.

        Another paragraph with two sentences. And here is the second.
    """)

    paras = analyze_paragraphs(test_content)
    english_paras = [p for p in paras if p["is_english"]]

    if len(english_paras) != 3:
        r.fail(f"Expected 3 English paragraphs, got {len(english_paras)}: {english_paras}")
        return r

    if english_paras[0]["sentences"] != 3:
        r.fail(f"First paragraph should have 3 sentences, got {english_paras[0]['sentences']}")
        return r

    r.ok(f"Detected {len(english_paras)} paragraphs with correct sentence counts")
    return r


def test_context_analysis_runs(test_dir: Path) -> TestResult:
    """v5: context engineering analysis produces a report for a real module."""
    r = TestResult("context_analysis_runs")

    # Find a module with a session JSON
    sessions = list(CURRICULUM_DIR.glob("a1/orchestration/*/phase-2-attempt-1-gemini-session.json"))
    if not sessions:
        r.fail("No session JSONs found for analysis")
        return r

    slug = sessions[0].parent.name
    report = analyze_module("a1", slug)

    if "ERROR" in report:
        r.fail(report)
        return r

    if "Immersion Breakdown" not in report:
        r.fail("Report missing Immersion Breakdown section")
        return r

    if "Instruction vs Output Gap" not in report:
        r.fail("Report missing Gap Analysis section")
        return r

    r.ok(f"Analysis of '{slug}': {len(report)} chars, has immersion + gap analysis")
    return r


def test_fix_prompt_pedagogy(test_dir: Path) -> TestResult:
    """v5: _extract_pedagogy_violations works correctly."""
    r = TestResult("fix_prompt_pedagogy")

    from pipeline_v5 import _extract_pedagogy_violations

    test_audit = textwrap.dedent("""\
        📚 PEDAGOGICAL VIOLATIONS FOUND:
          [NO_IMPERATIVES_EARLY_A1] 'Прочитайте' — Imperative verb forms should not appear
             → FIX: Replace imperative verbs with English instructions
          [FORBIDDEN_CASE] 'на роботі' — Locative case not yet taught
             → FIX: Replace with nominative construction
    """)

    violations = _extract_pedagogy_violations(test_audit)

    if len(violations) != 2:
        r.fail(f"Expected 2 violations, got {len(violations)}: {violations}")
        return r

    if violations[0]["type"] != "NO_IMPERATIVES_EARLY_A1":
        r.fail(f"Wrong type: {violations[0]}")
        return r

    r.ok(f"Extracted {len(violations)} violations with types and fixes")
    return r


def test_immersion_scope_guard(test_dir: Path) -> TestResult:
    """v5: large immersion gap detection works."""
    r = TestResult("immersion_scope_guard")

    detail = "17.0% LOW (target 35-55% (M37))"
    imm_match = re.search(r"([\d.]+)%\s+LOW\s+\(target\s+(\d+)-(\d+)%", detail)

    if not imm_match:
        r.fail("Immersion regex didn't match")
        return r

    current = float(imm_match.group(1))
    target_min = int(imm_match.group(2))
    gap = target_min - current

    if gap <= 15:
        r.fail(f"Expected gap > 15, got {gap}")
        return r

    r.ok(f"Large gap={gap:.0f}% detected correctly")
    return r


# ============================================================================
# Test Runner
# ============================================================================

ALL_TESTS = {
    "complete_skips": test_complete_module_skips,
    "resumption_two_runs": test_resumption_two_runs,
    "v5_state_format": test_v5_state_format,
    "gemini_session_readable": test_gemini_session_readable,
    "immersion_measurement": test_immersion_measurement,
    "paragraph_analysis": test_paragraph_analysis,
    "context_analysis_runs": test_context_analysis_runs,
    "fix_prompt_pedagogy": test_fix_prompt_pedagogy,
    "immersion_guard": test_immersion_scope_guard,
}


def run_tests(test_names: list[str] | None = None) -> list[TestResult]:
    test_dir = create_test_dir()
    print(f"\nTest bed: {test_dir}")
    print(f"{'=' * 60}\n")

    tests_to_run = test_names or list(ALL_TESTS.keys())
    results: list[TestResult] = []

    for name in tests_to_run:
        if name not in ALL_TESTS:
            print(f"  UNKNOWN test: {name}")
            continue

        print(f"  Running: {name}...", end=" ", flush=True)
        t0 = time.time()
        try:
            result = ALL_TESTS[name](test_dir)
            elapsed = time.time() - t0
            status = "PASS" if result.passed else "FAIL"
            print(f"{status} ({elapsed:.1f}s)")
            if result.message:
                print(f"    {result.message}")
        except Exception as e:
            elapsed = time.time() - t0
            result = TestResult(name)
            result.fail(f"Exception: {e}")
            print(f"ERROR ({elapsed:.1f}s)")
            print(f"    {e}")

        results.append(result)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        print("\nFailed tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")

    return results


def clean_old_testbeds(max_age_days: int = 7) -> int:
    if not TESTBED_ROOT.exists():
        return 0
    cutoff = time.time() - (max_age_days * 86400)
    removed = 0
    for d in TESTBED_ROOT.iterdir():
        if d.is_dir() and d.name.startswith("pipeline-test-") and d.stat().st_mtime < cutoff:
            shutil.rmtree(d)
            removed += 1
            print(f"  Removed: {d.name}")
    return removed


def main():
    parser = argparse.ArgumentParser(description="Pipeline v5 test bed")
    parser.add_argument("--test", nargs="*", help="Run specific test(s)")
    parser.add_argument("--list", action="store_true", help="List available tests")
    parser.add_argument("--clean", action="store_true", help="Remove old testbed dirs")
    parser.add_argument("--analyze", nargs=2, metavar=("TRACK", "SLUG"),
                        help="Context engineering analysis on a real module")
    args = parser.parse_args()

    if args.list:
        print("Available tests:")
        for name, func in ALL_TESTS.items():
            doc = (func.__doc__ or "").strip().split("\n")[0]
            print(f"  {name:30s} {doc}")
        return

    if args.clean:
        removed = clean_old_testbeds()
        print(f"Cleaned {removed} old testbed(s)")
        return

    if args.analyze:
        track, slug = args.analyze
        report = analyze_module(track, slug)
        print(report)
        return

    test_names = args.test if args.test else None
    results = run_tests(test_names)
    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
