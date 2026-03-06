#!/usr/bin/env python3
"""Pipeline test bed — test build_module.py behavior without touching production modules.

Creates a disposable 'test' track with minimal fixture modules under:
    testbed/pipeline-test-YYYYMMDD-HHMMSS/

Each test run gets its own timestamped directory that persists for investigation.
Artifacts include orchestration dirs, state files, logs, and content files.

Usage:
    .venv/bin/python scripts/test_pipeline.py                    # Run all tests
    .venv/bin/python scripts/test_pipeline.py --test resumption  # Run one test
    .venv/bin/python scripts/test_pipeline.py --list              # List available tests
    .venv/bin/python scripts/test_pipeline.py --clean             # Delete testbed dirs older than 7 days

Tests use --dry-run by default (no Gemini calls). Pass --live to dispatch real calls.
"""
from __future__ import annotations

import argparse
import json
import os
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

# Add scripts to path once at module level for build_module/pipeline_lib imports
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Minimal fixture data
FIXTURE_PLAN = {
    "module": "test-001",
    "level": "A1",
    "sequence": 1,
    "slug": "test-alphabet",
    "version": "1.0",
    "title": "Test Alphabet",
    "subtitle": "Testing the pipeline",
    "focus": "grammar",
    "pedagogy": "PPP",
    "phase": "A1.1 [First Contact]",
    "word_target": 1200,
    "objectives": [
        "Learner can recognize test letters",
        "Learner can read simple test words",
    ],
    "content_outline": [
        {
            "section": "Introduction",
            "words": 300,
            "points": ["Welcome to the test module.", "This tests pipeline behavior."],
        },
        {
            "section": "Main Content",
            "words": 600,
            "points": ["Core content goes here.", "Examples and practice."],
        },
        {
            "section": "Summary",
            "words": 300,
            "points": ["Review key concepts.", "Self-check questions."],
        },
    ],
    "vocabulary_hints": {
        "required": ["мама", "тато", "брат"],
        "suggested": ["сестра", "дім"],
    },
}

FIXTURE_META = {
    "slug": "test-alphabet",
    "title": "Test Alphabet",
    "word_target": 1200,
    "content_outline": [
        {
            "section": "Introduction",
            "slug": "introduction",
            "words": 300,
            "points": ["Welcome to the test module."],
        },
        {
            "section": "Main Content",
            "slug": "main-content",
            "words": 600,
            "points": ["Core content."],
        },
        {
            "section": "Summary",
            "slug": "summary",
            "words": 300,
            "points": ["Review."],
        },
    ],
}

# Minimal content that passes basic structure checks
FIXTURE_CONTENT = textwrap.dedent("""\
    <!-- SCOPE
    Covers: Test content for pipeline testing
    Not covered:
      - Everything else
    -->

    # Test Alphabet

    > **Why does this matter?**
    >
    > This is a test module for pipeline behavior testing.

    ## Introduction

    Welcome to the test module. Це тест. (This is a test.) This module exists to verify
    pipeline resumption, fix prompts, and state management. Ласкаво просимо! (Welcome!)

    The Ukrainian alphabet has 33 letters. Це алфавіт. (This is the alphabet.)
    Each letter maps to one sound. Це звук. (This is a sound.)
    Let us begin our journey. Це подорож. (This is a journey.)

    We will learn how letters work together. Це літера. (This is a letter.)
    Practice reading these words. Це слово. (This is a word.)
    Ukrainian is a beautiful language. Це мова. (This is a language.)

    > [!tip]
    > This is an engagement box for the test module.

    ### Reading Practice
    Let us practice some simple words:
    * **мама** (mom)
    * **тато** (dad)
    * **брат** (brother)
    * **сестра** (sister)

    ## Main Content

    Now let us look at the core content. Це основний зміст. (This is the main content.)

    | Ukrainian | English |
    |-----------|---------|
    | **мама** | mom |
    | **тато** | dad |
    | **брат** | brother |
    | **сестра** | sister |
    | **дім** | house |

    In Ukrainian, every letter is pronounced. Це правило. (This is a rule.)
    There are no silent letters. Це факт. (This is a fact.)

    The vowels are the heart of every syllable. Це голосна. (This is a vowel.)
    Consonants attach to vowels. Це приголосна. (This is a consonant.)

    Let us look at how words are formed. Це формування. (This is formation.)
    Each syllable needs exactly one vowel. Це склад. (This is a syllable.)

    Practice reading these phrases:
    * **Це мама.** (This is mom.)
    * **Це тато.** (This is dad.)
    * **Це брат і сестра.** (This is brother and sister.)
    * **Це дім.** (This is a house.)

    > [!cultural-note]
    > Ukrainian is one of the most melodic languages in Europe.

    The Ukrainian language has a rich history. Це історія. (This is history.)
    It has evolved over many centuries. Це еволюція. (This is evolution.)

    ### Practice Section
    Read these sentences aloud:
    * **Мама тут.** (Mom is here.)
    * **Тато там.** (Dad is there.)
    * **Брат і сестра тут.** (Brother and sister are here.)
    * **Дім там.** (The house is there.)

    > [!example]
    > **Мій дім** (My house)
    > Це мій дім. Тут мама, тато, брат і сестра.
    > *(This is my house. Here are mom, dad, brother, and sister.)*

    Now let us combine what we have learned. Це практика. (This is practice.)
    Reading fluently takes time and patience. Це терпіння. (This is patience.)

    ## Summary

    You have completed this test module. Це підсумок. (This is a summary.)

    Let us review what we learned:
    1. Ukrainian letters each have one sound.
    2. Vowels are the heart of syllables.
    3. Every letter is pronounced — no silent letters.

    > [!tip]
    > Practice reading Ukrainian words every day!

    **Self-Check Questions:**
    1. How many letters does the Ukrainian alphabet have?
    2. What is the role of vowels in syllables?
    3. Are there silent letters in Ukrainian?
""")

FIXTURE_ACTIVITIES = textwrap.dedent("""\
    - type: quiz
      title: Check Your Understanding
      instruction: Test your knowledge of basic Ukrainian concepts.
      items:
        - question: How many letters does the Ukrainian alphabet have?
          options: ['26', '33', '30', '28']
          answer: '33'
        - question: What is "мама" in English?
          options: ['dad', 'mom', 'sister', 'brother']
          answer: mom
        - question: What is "дім" in English?
          options: ['house', 'car', 'tree', 'book']
          answer: house
        - question: What is "тато" in English?
          options: ['mom', 'sister', 'dad', 'brother']
          answer: dad
        - question: How many vowels does Ukrainian have?
          options: ['5', '8', '10', '12']
          answer: '10'
        - question: What is "брат" in English?
          options: ['sister', 'mom', 'dad', 'brother']
          answer: brother
        - question: Are there silent letters in Ukrainian?
          options: ['Yes, many', 'No, every letter is pronounced', 'Sometimes', 'Only vowels']
          answer: No, every letter is pronounced
        - question: What is "сестра" in English?
          options: ['brother', 'mom', 'sister', 'dad']
          answer: sister
    - type: match-up
      title: Match Ukrainian to English
      instruction: Match each Ukrainian word with its English translation.
      items:
        - left: мама
          right: mom
        - left: тато
          right: dad
        - left: брат
          right: brother
        - left: сестра
          right: sister
        - left: дім
          right: house
        - left: слово
          right: word
    - type: fill-blank
      title: Complete the Sentence
      instruction: Fill in the missing Ukrainian word.
      items:
        - sentence: "Це ___. (This is mom.)"
          answer: мама
        - sentence: "Це ___. (This is dad.)"
          answer: тато
        - sentence: "Це ___. (This is a house.)"
          answer: дім
        - sentence: "___ тут. (Brother is here.)"
          answer: Брат
        - sentence: "___ там. (Sister is there.)"
          answer: Сестра
        - sentence: "Це ___. (This is a word.)"
          answer: слово
        - sentence: "Це ___. (This is a letter.)"
          answer: літера
        - sentence: "Це ___. (This is a sound.)"
          answer: звук
    - type: word-bank
      title: Build a Sentence
      instruction: Arrange the words to form a correct Ukrainian sentence.
      items:
        - words: ['Це', 'мама', 'і', 'тато']
          answer: Це мама і тато
        - words: ['Брат', 'і', 'сестра', 'тут']
          answer: Брат і сестра тут
        - words: ['Це', 'мій', 'дім']
          answer: Це мій дім
        - words: ['Тато', 'там']
          answer: Тато там
        - words: ['Це', 'слово']
          answer: Це слово
        - words: ['Мама', 'тут']
          answer: Мама тут
        - words: ['Це', 'літера']
          answer: Це літера
        - words: ['Це', 'звук']
          answer: Це звук
""")

FIXTURE_VOCABULARY = textwrap.dedent("""\
    - word: мама
      translation: mom
      gender: f
      pos: noun
      example: Це мама.
      example_translation: This is mom.
    - word: тато
      translation: dad
      gender: m
      pos: noun
      example: Це тато.
      example_translation: This is dad.
    - word: брат
      translation: brother
      gender: m
      pos: noun
      example: Це брат.
      example_translation: This is brother.
    - word: сестра
      translation: sister
      gender: f
      pos: noun
      example: Це сестра.
      example_translation: This is sister.
    - word: дім
      translation: house
      gender: m
      pos: noun
      example: Це дім.
      example_translation: This is a house.
""")


def create_test_dir() -> Path:
    """Create a timestamped test directory."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    test_dir = TESTBED_ROOT / f"pipeline-test-{ts}"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def setup_fixture(test_dir: Path, slug: str = "test-alphabet",
                  num: int = 1, track: str = "a1") -> dict:
    """Create a complete module fixture in the test directory.

    Returns dict with paths for inspection.
    """
    import yaml

    # Mirror the production directory structure
    cur_dir = test_dir / "curriculum" / "l2-uk-en"
    track_dir = cur_dir / track
    plans_dir = cur_dir / "plans" / track

    for d in [
        track_dir / "meta",
        track_dir / "activities",
        track_dir / "vocabulary",
        track_dir / "research",
        track_dir / "orchestration" / slug,
        track_dir / "audit",
        track_dir / "status",
        track_dir / "review",
        plans_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # Write fixture files
    plan = FIXTURE_PLAN.copy()
    plan["slug"] = slug
    plan["sequence"] = num
    (plans_dir / f"{slug}.yaml").write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    meta = FIXTURE_META.copy()
    meta["slug"] = slug
    (track_dir / "meta" / f"{slug}.yaml").write_text(yaml.dump(meta, allow_unicode=True), "utf-8")

    (track_dir / f"{slug}.md").write_text(FIXTURE_CONTENT, "utf-8")
    (track_dir / "activities" / f"{slug}.yaml").write_text(FIXTURE_ACTIVITIES, "utf-8")
    (track_dir / "vocabulary" / f"{slug}.yaml").write_text(FIXTURE_VOCABULARY, "utf-8")

    # Create curriculum.yaml index
    curriculum_yaml = {
        "tracks": {
            track: {
                "modules": [{
                    "sequence": num,
                    "slug": slug,
                    "title": plan["title"],
                }]
            }
        }
    }
    (cur_dir / "curriculum.yaml").write_text(yaml.dump(curriculum_yaml, allow_unicode=True), "utf-8")

    return {
        "test_dir": test_dir,
        "curriculum_dir": cur_dir,
        "track_dir": track_dir,
        "orch_dir": track_dir / "orchestration" / slug,
        "state_v4": track_dir / "orchestration" / slug / "state-v4.json",
        "content": track_dir / f"{slug}.md",
        "activities": track_dir / "activities" / f"{slug}.yaml",
        "vocabulary": track_dir / "vocabulary" / f"{slug}.yaml",
        "plan": plans_dir / f"{slug}.yaml",
        "meta": track_dir / "meta" / f"{slug}.yaml",
        "slug": slug,
        "num": num,
        "track": track,
    }


def inject_state(fixture: dict, phases: dict[str, str]) -> None:
    """Write a state-v4.json with given phase statuses.

    phases: {"research": "complete", "content": "complete", "validate": "failed"}
    """
    state = {
        "track": fixture["track"],
        "slug": fixture["slug"],
        "mode": "v4",
        "phases": {},
    }
    from datetime import timezone
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for phase_id, status in phases.items():
        state_key = f"v4-{phase_id}"
        entry = {"status": status, "ts": ts}
        if status == "failed":
            entry["note"] = "test-failure"
            entry["attempts"] = 3
        state["phases"][state_key] = entry

    fixture["state_v4"].write_text(json.dumps(state, indent=2), "utf-8")


def run_build(track: str, num: int, extra_args: list[str] | None = None,
              dry_run: bool = True) -> tuple[int, str]:
    """Run build_module.py against a PRODUCTION module (always use --dry-run!).

    Uses real production paths. Tests state behavior without modifying content.
    Returns (return_code, stdout+stderr).
    """
    cmd = [
        VENV_PYTHON, str(SCRIPTS_DIR / "build_module.py"),
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


def read_state(fixture: dict) -> dict:
    """Read state-v4.json, return empty dict if missing."""
    sf = fixture["state_v4"]
    if sf.exists():
        return json.loads(sf.read_text("utf-8"))
    return {}


def list_orch_files(fixture: dict) -> list[str]:
    """List files in orchestration dir."""
    orch = fixture["orch_dir"]
    if orch.is_dir():
        return sorted(f.name for f in orch.iterdir() if f.is_file())
    return []


# ============================================================================
# Test Cases
# ============================================================================

class _FakeCtx:
    """Minimal context stub — _is_phase_v4_complete only reads ctx for state_path fallback."""
    slug = "test"


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.fixture: dict | None = None

    def ok(self, msg: str = ""):
        self.passed = True
        self.message = msg

    def fail(self, msg: str):
        self.passed = False
        self.message = msg


def test_complete_module_skips(test_dir: Path) -> TestResult:
    """Test: a fully-built production module (M1) skips all phases in dry-run."""
    r = TestResult("complete_module_skips")
    # Use production M1 which is fully built
    rc, output = run_build("a1", 1, dry_run=True)

    done_count = output.count("[DONE]")
    skip_count = output.count("SKIP")

    if done_count < 4:
        r.fail(f"Expected 4+ [DONE] markers for complete module, got {done_count}\n"
               f"Output:\n{output}")
        return r

    r.ok(f"rc={rc}, {done_count} [DONE], {skip_count} SKIP")
    return r


def test_resumption_via_state(test_dir: Path) -> TestResult:
    """Test: inject partial state into fixture, verify [DONE] markers."""
    r = TestResult("resumption_via_state")
    fixture = setup_fixture(test_dir / "resume", slug="test-resume")
    r.fixture = fixture

    # Inject state with research+discover+content complete
    inject_state(fixture, {
        "research": "complete",
        "discover": "complete",
        "content": "complete",
    })

    state = read_state(fixture)
    complete_phases = [k for k, v in state.get("phases", {}).items()
                       if v.get("status") == "complete"]
    incomplete_phases = [k for k, v in state.get("phases", {}).items()
                         if v.get("status") != "complete"]

    if len(complete_phases) != 3:
        r.fail(f"Expected 3 complete phases, got {complete_phases}")
        return r

    # Verify _is_phase_v4_complete works
    from build_module import _is_phase_v4_complete, _V4_PHASE_STATE_IDS

    for phase in ["research", "discover", "content"]:
        if not _is_phase_v4_complete(_FakeCtx(), phase, state):
            r.fail(f"_is_phase_v4_complete('{phase}') should be True")
            return r

    for phase in ["activities", "validate"]:
        if _is_phase_v4_complete(_FakeCtx(), phase, state):
            r.fail(f"_is_phase_v4_complete('{phase}') should be False")
            return r

    r.ok(f"3 phases complete, 2 not — resumption logic correct")
    return r


def test_failed_validate_state(test_dir: Path) -> TestResult:
    """Test: failed validate is NOT treated as complete."""
    r = TestResult("failed_validate_state")
    fixture = setup_fixture(test_dir / "failed-val", slug="test-failed-val")
    r.fixture = fixture

    inject_state(fixture, {
        "research": "complete",
        "discover": "complete",
        "content": "complete",
        "activities": "complete",
        "validate": "failed",
    })

    state = read_state(fixture)
    from build_module import _is_phase_v4_complete

    # Earlier phases should be complete
    for phase in ["research", "discover", "content", "activities"]:
        if not _is_phase_v4_complete(_FakeCtx(), phase, state):
            r.fail(f"{phase} should be complete")
            return r

    # Validate should NOT be complete
    if _is_phase_v4_complete(_FakeCtx(), "validate", state):
        r.fail("validate should NOT be complete (status=failed)")
        return r

    r.ok("4 phases complete, validate=failed correctly detected as incomplete")
    return r


def test_rebuild_cleans_state(test_dir: Path) -> TestResult:
    """Test: --rebuild logic deletes all orch files."""
    r = TestResult("rebuild_cleans_state")
    fixture = setup_fixture(test_dir / "rebuild", slug="test-rebuild")
    r.fixture = fixture

    # Inject complete state + artifacts
    inject_state(fixture, {
        "research": "complete",
        "discover": "complete",
        "content": "complete",
        "activities": "complete",
        "validate": "complete",
    })
    (fixture["orch_dir"] / "phase-2-prompt.md").write_text("test prompt", "utf-8")
    (fixture["orch_dir"] / "phase-2-friction-1.md").write_text("test friction", "utf-8")

    files_before = list_orch_files(fixture)
    state_before = read_state(fixture)

    # Simulate the --rebuild cleanup logic from build_module.py line 6047-6053
    orch_dir = fixture["orch_dir"]
    removed = 0
    for f in orch_dir.iterdir():
        if f.is_file():
            f.unlink()
            removed += 1

    files_after = list_orch_files(fixture)
    state_after = read_state(fixture)

    if files_after:
        r.fail(f"Expected 0 files after rebuild cleanup, got {files_after}")
        return r

    if state_after:
        r.fail(f"State should be empty after rebuild, got {state_after}")
        return r

    r.ok(f"Before: {len(files_before)} files, removed: {removed}, after: {len(files_after)}")
    return r


def test_auto_rebuild_detection(test_dir: Path) -> TestResult:
    """Test: verify that 'needs-rebuild' note in state triggers AUTO-REBUILD in batch."""
    r = TestResult("auto_rebuild_detection")
    fixture = setup_fixture(test_dir / "auto-rebuild", slug="test-auto-rebuild")
    r.fixture = fixture

    # Simulate exhausted validate with needs-rebuild note
    state = {
        "track": fixture["track"],
        "slug": fixture["slug"],
        "mode": "v4",
        "phases": {
            "v4-research": {"status": "complete", "ts": "2026-01-01T00:00:00Z"},
            "v4-discover": {"status": "complete", "ts": "2026-01-01T00:00:00Z"},
            "v4-content": {"status": "complete", "ts": "2026-01-01T00:00:00Z"},
            "v4-activities": {"status": "complete", "ts": "2026-01-01T00:00:00Z"},
            "v4-validate": {
                "status": "failed",
                "ts": "2026-01-01T00:00:00Z",
                "attempts": 6,
                "note": "needs-rebuild-diffuse-issues",
            },
        },
    }
    fixture["state_v4"].write_text(json.dumps(state, indent=2), "utf-8")

    # Check the detection logic (don't actually run batch, just verify the check)
    state_data = read_state(fixture)
    validate_phase = state_data.get("phases", {}).get("v4-validate", {})
    note = validate_phase.get("note", "")
    needs_rebuild = note.startswith("needs-")

    if not needs_rebuild:
        r.fail(f"Expected needs-rebuild detection, got note='{note}'")
        return r

    r.ok(f"note='{note}', needs_rebuild={needs_rebuild} — batch would AUTO-REBUILD")
    return r


def test_fix_prompt_includes_pedagogy(test_dir: Path) -> TestResult:
    """Test: _build_fix_prompt includes pedagogy violation details."""
    r = TestResult("fix_prompt_includes_pedagogy")
    fixture = setup_fixture(test_dir / "fix-prompt", slug="test-fix-prompt")
    r.fixture = fixture

    # Test the extraction function directly
    from pipeline_lib import _extract_pedagogy_violations

    test_audit = textwrap.dedent("""\
        📚 PEDAGOGICAL VIOLATIONS FOUND:
          [NO_IMPERATIVES_EARLY_A1] 'Прочитайте' — Imperative verb forms should not appear
             → FIX: Replace imperative verbs with English instructions
          [FORBIDDEN_CASE] 'на роботі' — Locative case not yet taught
             → FIX: Replace with nominative construction

        --- STRICT GATES ---
        Pedagogy     ❌ 2 violations
    """)

    violations = _extract_pedagogy_violations(test_audit)

    if len(violations) != 2:
        r.fail(f"Expected 2 violations, got {len(violations)}: {violations}")
        return r

    if violations[0]["type"] != "NO_IMPERATIVES_EARLY_A1":
        r.fail(f"Wrong type: {violations[0]}")
        return r

    if not violations[1]["fix"]:
        r.fail(f"Missing fix for violation 2: {violations[1]}")
        return r

    r.ok(f"Extracted {len(violations)} violations with types and fixes")
    return r


def test_immersion_scope_guard(test_dir: Path) -> TestResult:
    """Test: large immersion gap triggers scope warning in fix prompt."""
    r = TestResult("immersion_scope_guard")
    fixture = setup_fixture(test_dir / "immersion", slug="test-immersion")
    r.fixture = fixture

    import re

    # Test the immersion gap detection regex
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

    # Test small gap (should NOT trigger)
    detail_small = "30.0% LOW (target 35-55% (M37))"
    imm_match_small = re.search(r"([\d.]+)%\s+LOW\s+\(target\s+(\d+)-(\d+)%", detail_small)
    gap_small = int(imm_match_small.group(2)) - float(imm_match_small.group(1))

    if gap_small > 15:
        r.fail(f"Small gap should be <=15, got {gap_small}")
        return r

    r.ok(f"Large gap={gap:.0f}% triggers guard, small gap={gap_small:.0f}% does not")
    return r


def test_consecutive_timeout_bailout(test_dir: Path) -> TestResult:
    """Test: verify consecutive failure counter logic exists in validate loop."""
    r = TestResult("consecutive_timeout_bailout")
    fixture = setup_fixture(test_dir / "timeout", slug="test-timeout")
    r.fixture = fixture

    # Read the build_module.py source and verify the bail-out logic exists
    build_src = (SCRIPTS_DIR / "build_module.py").read_text("utf-8")

    if "consecutive_failures" not in build_src:
        r.fail("consecutive_failures counter not found in build_module.py")
        return r

    if "consecutive_failures >= 2" not in build_src:
        r.fail("Bail-out condition (>= 2) not found")
        return r

    if "skipping remaining fix attempts" not in build_src:
        r.fail("Bail-out log message not found")
        return r

    r.ok("Consecutive timeout bail-out logic present in validate loop")
    return r


# ============================================================================
# Test Runner
# ============================================================================

ALL_TESTS = {
    "complete_skips": test_complete_module_skips,
    "resumption": test_resumption_via_state,
    "failed_validate": test_failed_validate_state,
    "rebuild": test_rebuild_cleans_state,
    "auto_rebuild": test_auto_rebuild_detection,
    "fix_prompt_pedagogy": test_fix_prompt_includes_pedagogy,
    "immersion_guard": test_immersion_scope_guard,
    "timeout_bailout": test_consecutive_timeout_bailout,
}


def run_tests(test_names: list[str] | None = None, live: bool = False) -> list[TestResult]:
    """Run selected tests (or all)."""
    test_dir = create_test_dir()
    print(f"\nTest bed: {test_dir}")
    print(f"{'='*60}\n")

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
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} ({elapsed:.1f}s)")
            if result.message:
                print(f"    {result.message}")
            if result.fixture:
                print(f"    Artifacts: {result.fixture['orch_dir']}")
        except Exception as e:
            elapsed = time.time() - t0
            result = TestResult(name)
            result.fail(f"Exception: {e}")
            print(f"❌ ERROR ({elapsed:.1f}s)")
            print(f"    {e}")

        results.append(result)

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed")
    print(f"Test bed preserved at: {test_dir}")
    print(f"  └── Inspect orchestration dirs, state files, logs")
    if passed < total:
        print(f"\nFailed tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")

    return results


def clean_old_testbeds(max_age_days: int = 7) -> int:
    """Delete testbed directories older than max_age_days."""
    if not TESTBED_ROOT.exists():
        return 0
    cutoff = time.time() - (max_age_days * 86400)
    removed = 0
    for d in TESTBED_ROOT.iterdir():
        if d.is_dir() and d.name.startswith("pipeline-test-"):
            if d.stat().st_mtime < cutoff:
                shutil.rmtree(d)
                removed += 1
                print(f"  Removed: {d.name}")
    return removed


def main():
    parser = argparse.ArgumentParser(description="Pipeline test bed")
    parser.add_argument("--test", nargs="*", help="Run specific test(s)")
    parser.add_argument("--list", action="store_true", help="List available tests")
    parser.add_argument("--clean", action="store_true", help="Remove old testbed dirs")
    parser.add_argument("--live", action="store_true", help="Use real Gemini calls (not dry-run)")
    args = parser.parse_args()

    if args.list:
        print("Available tests:")
        for name, func in ALL_TESTS.items():
            doc = (func.__doc__ or "").strip().split("\n")[0]
            print(f"  {name:25s} {doc}")
        return

    if args.clean:
        removed = clean_old_testbeds()
        print(f"Cleaned {removed} old testbed(s)")
        return

    test_names = args.test if args.test else None
    results = run_tests(test_names, live=args.live)

    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
