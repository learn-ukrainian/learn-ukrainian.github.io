# Codex dispatch — vesum_verified gate: MC distractor + pronunciation transcription awareness

**Trigger:** Re-eval of `audit/bakeoff-2026-05-12-night` claude-tools artifact against `_vesum_gate` (post-#1901 fix) flagged 6 forms as "missing from VESUM" — all 6 are pedagogically legitimate, not invented forms.
**File:** `scripts/build/linear_pipeline.py`
**Function:** `_vesum_gate` at line 3641, `_build_vesum_text` at line 3847, `_activity_vesum_text` at line 3868.
**Estimated effort:** 60-90 min (fix + regression tests + linting).

## The bug, with evidence

Six forms got flagged in re-eval of the night-bakeoff artifact:

| Form | Where it lives | Why it's legitimate |
|---|---|---|
| `вмиваєсся` | `module.md` line 70, prose: "the spelling **вмиваєшся** sounds like **вмиваєсся**" | Pronunciation transcription teaching the [с'а] rule from Кравцова G4 p.113. The lesson explicitly says it's a phonetic form. |
| `вмиваєцця` | `module.md` line 70, same prose: "**вмивається** sounds like **вмиваєцця**" | Pronunciation transcription for the [ц'а] rule. |
| `п'юся` | `activities.yaml` line 41: MC option, `text: "п'юся"` `correct: false`, question `Я ____ каву` (correct: `п'ю`) | Wrong-answer distractor testing whether students invent reflexive forms of non-reflexive verbs (`пити` is not reflexive). |
| `п'єшся` | `activities.yaml` line 43: same MC, distractor | Same. |
| `снідаюся` | `activities.yaml` line 73: MC distractor, question `Я ____ вранці` (correct: `снідаю`) | `снідати` is not reflexive — distractor tests `-ся` overgeneralization. |
| `снідаєшся` | `activities.yaml` line 75: same MC, distractor | Same. |

The gate's docstring at line 3651-3662 already excludes 3 false-positive classes (phonetic transcriptions, intentional misspellings in `error-correction` activities, sentence-initial capitalization). MC distractor exclusion is **not** in that list. Pronunciation transcriptions in bold-prose `**X** sounds like **Y**` pattern slip through because the existing `_strip_metalinguistic` strips backticks/brackets but not bold-prose-after-"sounds like".

## Two fixes needed

### Fix 1 — Exclude MC distractor option text (`correct: false`) from vesum verification

In `_activity_vesum_text` (line 3868), the function walks all string values of an activity. For activities containing `options` arrays of the shape `[{text, correct}]`, exclude the `text` field of options where `correct` is `False` (or falsy).

Implementation sketch:
```python
def _activity_vesum_text(activity: dict[str, Any]) -> str:
    if activity.get("type") == _ERROR_CORRECTION_TYPE:
        skip_subtree = _ERROR_CORRECTION_INTENTIONAL_FIELDS
    else:
        skip_subtree = frozenset()

    # NEW: walk options and skip text of wrong-answer distractors at any depth.
    # The activity schema uses {text, correct} pairs inside `options` lists.
    # A `correct: false` option is the activity author explicitly labeling the
    # form as a wrong answer (e.g., MC distractor testing -ся overgeneralization).
    # Such forms are intentionally non-standard; verifying them against VESUM
    # always fails and produces false-positive "invented form" reports.
    intentional_wrong_texts = _collect_intentional_wrong_option_texts(activity)

    def keep(_parent_key: str | None, value: str) -> str | None:
        if value in intentional_wrong_texts:
            return None
        return value

    return "\n".join(
        _walk_artifact_strings(activity, keep=keep, skip_subtree_keys=skip_subtree)
    )


def _collect_intentional_wrong_option_texts(activity: Any) -> frozenset[str]:
    """Return the set of MC option `text` values whose `correct` is falsy.

    Walks the activity tree because options can be nested under questions,
    items, or directly on the activity. The keep is per-option (not subtree)
    because we still want to verify the correct option's text.
    """
    collected: set[str] = set()
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            options = node.get("options")
            if isinstance(options, list):
                for opt in options:
                    if (isinstance(opt, dict)
                        and not opt.get("correct", False)
                        and isinstance(opt.get("text"), str)):
                        collected.add(opt["text"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(activity)
    return frozenset(collected)
```

If the schema also surfaces wrong-answer distractors under other keys (e.g., `distractors`, `wrong_answers`, `incorrect_options`), check the activity-schema docs / tests and include those too. **Do NOT invent schema patterns** — only add patterns you can confirm exist by grepping `tests/test_activity_*.py`, `scripts/audit/audit_activities.py`, or activity YAML samples under `curriculum/`.

### Fix 2 — Recognize pronunciation transcriptions in didactic prose

In `_strip_metalinguistic` (find via `grep -n "_strip_metalinguistic" scripts/build/linear_pipeline.py`), add a pattern that strips Ukrainian-bold-text that follows pronunciation cue phrases. Concretely:

```python
# Pronunciation transcription pattern: **СПЕЛЛІНГ** sounds like **ВИМОВА**
# (where ВИМОВА is a phonetic transcription, not a standard form).
# Strip the bold-text that follows English "sounds like" OR Ukrainian
# "звучить як" / "вимовляється як" / "вимова". The pattern is narrow on
# purpose — broader stripping would hide real misspellings.
_PRONUNCIATION_CUE_PATTERN = re.compile(
    r"(?:sounds?\s+like|звучить\s+як|вимовляється\s+як|вимова[:\s])\s*\*\*[^*]+\*\*",
    re.IGNORECASE,
)
```

Apply via `re.sub` in `_strip_metalinguistic`. Add a unit test that demonstrates `**вмиваєсся**` is stripped when preceded by "sounds like" but NOT stripped in isolation (so a real misspelling outside a transcription context still gets caught).

## Regression test

Add `tests/test_vesum_gate_distractor_and_phonetic.py`:

```python
"""Regression tests for the vesum_verified gate's false-positive classes.

Bug context: re-eval of audit/bakeoff-2026-05-12-night flagged 6 forms as
"missing from VESUM" — 4 were MC distractors labeled correct: false, 2 were
pronunciation transcriptions in didactic prose. Both classes are pedagogically
legitimate and must be excluded from VESUM verification.
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.build.linear_pipeline import _vesum_gate


def _stub_verify_words(words):
    # Whatever the test cases need — wire the test fixture.
    return {w: [] for w in words}


def test_mc_distractor_text_not_verified():
    """correct: false option text must NOT be checked against VESUM."""
    activity = {
        "type": "multiple-choice",
        "questions": [{
            "question": "Я ___ каву.",
            "options": [
                {"text": "п'ю", "correct": True},
                {"text": "п'юся", "correct": False},
                {"text": "п'єшся", "correct": False},
            ],
        }],
    }
    # Build minimal text/vocab/resources for the gate.
    # Call _vesum_gate with verify_words_fn that would FAIL the test
    # if п'юся / п'єшся were sent for verification.
    sent_for_verification: set[str] = set()
    def verify_fn(words):
        sent_for_verification.update(words)
        return {w: [{"lemma": w, "pos": "verb"}] for w in words}
    _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_fn,
    )
    assert "п'юся" not in sent_for_verification
    assert "п'єшся" not in sent_for_verification


def test_correct_option_text_still_verified():
    """correct: true option text MUST still be checked (regression guard)."""
    activity = {
        "type": "multiple-choice",
        "questions": [{
            "question": "Я ___ каву.",
            "options": [
                {"text": "п'ю", "correct": True},
                {"text": "п'юся", "correct": False},
            ],
        }],
    }
    sent_for_verification: set[str] = set()
    def verify_fn(words):
        sent_for_verification.update(words)
        return {w: [{"lemma": w, "pos": "verb"}] for w in words}
    _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_fn,
    )
    # The CORRECT option's text should be verified.
    assert "п'ю" in sent_for_verification


def test_pronunciation_transcription_stripped_in_prose():
    """A bold-text phonetic form following 'sounds like' must not hit VESUM."""
    module = (
        "The spelling **вмиваєшся** sounds like **вмиваєсся**, and "
        "**вмивається** sounds like **вмиваєцця**."
    )
    sent_for_verification: set[str] = set()
    def verify_fn(words):
        sent_for_verification.update(words)
        return {w: [{"lemma": w, "pos": "verb"}] for w in words}
    _vesum_gate(
        module_text=module,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_fn,
    )
    assert "вмиваєсся" not in sent_for_verification
    assert "вмиваєцця" not in sent_for_verification
    # Standard forms preceding the phonetic transcription MUST still be verified.
    assert "вмиваєшся" in sent_for_verification


def test_isolated_misspelling_still_caught():
    """A non-standard form NOT in a transcription context must still be flagged."""
    module = "She написала вмиваєсся without context — bug."
    flagged: set[str] = set()
    def verify_fn(words):
        # Empty result = "not in VESUM"
        return {w: [] for w in words}
    result = _vesum_gate(
        module_text=module,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_fn,
    )
    # вмиваєсся should appear in missing because it's an isolated misspelling
    assert "вмиваєсся" in result.get("missing", [])
```

Adapt the test harness to match `_vesum_gate`'s actual signature and return shape — the assertions above are illustrative. The non-negotiable contract is: distractor `text` values with `correct: false` are NEVER sent to `verify_words_fn`, and pronunciation transcriptions in `**X** sounds like **Y**` patterns have `Y` stripped before verification.

## Verifiable claims this dispatch will produce (per #M-4)

| Claim | Tool | Output |
|---|---|---|
| Pre-fix repro on bakeoff artifact | `PYTHONPATH=scripts .venv/bin/python` running `_vesum_gate` against the bakeoff module dir | Raw `missing=[вмиваєсся, вмиваєцця, п'юся, п'єшся, снідаюся, снідаєшся]` |
| Post-fix on same artifact | Same | Raw `missing=[]` or `missing=[<only-genuine-issues>]` |
| Regression test passes | `.venv/bin/python -m pytest tests/test_vesum_gate_distractor_and_phonetic.py -v` | `4 passed` summary line raw |
| Existing tests still pass | `.venv/bin/python -m pytest tests/test_vesum*.py tests/test_linear_pipeline*.py -v 2>&1 \| tail -20` | Raw summary |
| Ruff clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_vesum_gate_distractor_and_phonetic.py` | `All checks passed!` raw |

Quote raw output for each. "Tests pass" without quoted summary = hallucination per #M-4.

## Dispatch checklist

1. Worktree: `git worktree add .worktrees/dispatch/codex/vesum-gate-distractor-awareness -b codex/vesum-gate-distractor-awareness origin/main`
2. Implement Fix 1 + Fix 2 + regression tests.
3. Run pytest + ruff. Quote outputs.
4. Commit: `fix(vesum_gate): exclude MC distractor text + pronunciation transcriptions`
5. Push branch + open PR titled `fix(vesum_gate): MC distractor + pronunciation transcription awareness`.
6. PR body MUST include pre-fix repro + post-fix repro + pytest + ruff summaries with raw output.
7. **DO NOT auto-merge.** Orchestrator (Claude) merges after CI green.

## Out-of-scope

- ❌ Don't broaden phonetic-transcription detection beyond the cue-prefixed bold pattern — a wider strip would hide real misspellings.
- ❌ Don't touch other gates (`textbook_grounding`, `formatting_standards`, etc.).
- ❌ Don't touch the `writer_tool_call` telemetry (separate dispatch).
- ❌ Don't change the activity schema. The fix reads schema as-is.
