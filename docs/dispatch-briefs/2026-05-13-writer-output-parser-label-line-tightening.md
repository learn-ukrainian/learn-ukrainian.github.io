# Codex dispatch brief — Writer-output parser preceding-label-line tightening (#1956)

> **Issue:** #1956 — `[v7_build] Writer-output parser refuses Card 1 writer's fence-info-string format`
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/parser-label-tightening-2026-05-13/`
> **Base:** `origin/main` (currently `d1a2d9b13d`)
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Every command that uses `.venv/`, `scripts/`, or files in MAIN checkout MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && ...` or absolute path. Inside the worktree, `.venv/` is gitignored — use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

P0 blocker for Phase 2 of the student-aware-immersion plan. The 2026-05-13 m20 (`a1/my-morning`) V7 build halted at writer-output parse with:

```
"reason": "Writer output has mismatched artifact label and fence name at line 96:
            label='activities.yaml' but fence info has 'module.md'"
```

The writer was correct. The parser is wrong. Tighten the parser's preceding-label-line detection so it does not false-positive on `<plan_reasoning>` CoT content. After this fix, m20 will be re-run; if green, Phase 2b unblocks.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Parser uses standalone-label-line detection (not word-boundary embed)" | `grep -n '_artifact_name_from_label_line\|pending_name' scripts/build/linear_pipeline.py` shows the new helper + the call-site swap at the `pending_name = name` line | quote grep output |
| "Existing mismatch-guard test still fires on legitimate label-vs-fence-info conflict" | `.venv/bin/pytest tests/build/test_linear_pipeline.py::test_parse_writer_output_rejects_label_vs_fence_name_mismatch -v` | quote test name + `passed` line |
| "Regression test: `<plan_reasoning>` CoT mentioning `activities.yaml` followed by `markdown file=module.md` fence parses successfully" | new test in `tests/build/test_linear_pipeline.py` (see fixture below) | quote new test name + `passed` line |
| "Real-world repro: the actual failed writer_output.raw.md from m20 build parses successfully" | new test loads/inlines the relevant prefix of `.worktrees/builds/a1-my-morning-20260513-122043/curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md` and asserts `parse_writer_output_strict_json` returns 4 artifacts | quote test name + `passed` line |
| "All `tests/build/test_linear_pipeline.py` tests pass" | `.venv/bin/pytest tests/build/test_linear_pipeline.py -v` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py` | quote final line |
| "PR opened" | `gh pr view <N> --json url` | quote URL |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## Bug analysis (already done by orchestrator — do not redo, implement)

### Evidence

The failed writer_output.raw.md is preserved at:

```
.worktrees/builds/a1-my-morning-20260513-122043/curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md
```

Lines 1–94 are four `<plan_reasoning section="...">` XML blocks (CoT/planning). Each contains an `<implementation_map>` listing obligation→artifact rows in pipe-delimited form, e.g. line 9:

```
- act-5 (match-up verb-pairs) | activities.yaml | INJECT_ACTIVITY end of §Діалоги | inline match-up вмивати↔вмиватися, ...
```

Lines 33, 58, 73, 83 contain similar `| activities.yaml |` mentions.

Line 96 begins the first artifact fence:

```
```markdown file=module.md
```

### Writer prompt mandates the fence-info-string form

`.worktrees/builds/a1-my-morning-20260513-122043/curriculum/l2-uk-en/a1/my-morning/writer_prompt.md` lines 1017–1023:

```
Return the visible `<plan_reasoning>` blocks first, then exactly these four fenced blocks in the order below, then the `<end_gate>` block. Do not add any other prose anywhere.

```markdown file=module.md
...
```

```json file=activities.yaml
```

No "preceding section header label" pattern appears anywhere in the writer prompt. The fence-info-string form is the ONLY shape the writer is told to emit. The writer in this build followed spec.

### Parser code path that misfires

`scripts/build/linear_pipeline.py:2357 parse_writer_output_strict_json`:

```python
# Line 2429 — for any non-fence line, scrape pending_name with WORD-BOUNDARY embed search
name = _artifact_name_from_text(line)
if name in WRITER_ARTIFACTS:
    pending_name = name
```

And `_artifact_name_from_text` at line 3762:

```python
def _artifact_name_from_text(text: str) -> str | None:
    for artifact in WRITER_ARTIFACTS:
        if re.search(rf"(?<![\w.-]){re.escape(artifact)}(?![\w.-])", text):
            return artifact
    return None
```

This function is also called at line 2376 to extract `info_name` from fence info strings (where `markdown file=module.md` needs `module.md` to be findable embedded). That call site is correct and must keep its current behavior.

The misfire is at the line 2429 call site: scanning every non-fence line of CoT prose for any artifact-name embed sets `pending_name = "activities.yaml"` from the implementation_map rows, then the fence-info mismatch guard at lines 2382–2387 raises when the actual fence emits `markdown file=module.md`.

### Why the existing test fixture isn't enough

`test_parse_writer_output_rejects_label_vs_fence_name_mismatch` (line 390) exercises a legitimate label/fence mismatch where `activities.yaml` is a STANDALONE LINE (test fixture line 404 of the test source):

```
activities.yaml
```

The fix must preserve that adversarial guard. It only needs to reject prose-mention matches (where the artifact name is embedded in a longer line with other content).

---

## Fix design

### Step 1: add `_artifact_name_from_label_line` helper

Add in `scripts/build/linear_pipeline.py` near `_artifact_name_from_text` (around line 3762). Module-level compiled regex above the function to keep the per-line scan cheap:

```python
_LABEL_LINE_RE = re.compile(
    r"^[\s>#\-*]*(?P<name>module\.md|activities\.yaml|vocabulary\.yaml|resources\.yaml)\s*:?\s*$"
)


def _artifact_name_from_label_line(line: str) -> str | None:
    """Return the artifact name if `line` is a standalone label line.

    Distinct from `_artifact_name_from_text`, which does a word-boundary
    embed search anywhere in the line (used at the fence-info-string call
    site, where `markdown file=module.md` requires finding `module.md`
    inside surrounding tokens). For the preceding-label call site we want
    the OPPOSITE semantics: only treat a line as a label if the artifact
    name is essentially the entire line content (optionally preceded by
    markdown decorations `#`, `-`, `*`, `>` and optionally followed by
    `:`).

    This avoids false positives where the artifact name appears as
    incidental prose — e.g. inside a `<plan_reasoning><implementation_map>`
    CoT block listing pipe-delimited rows like
    `- act-5 | activities.yaml | INJECT_ACTIVITY ...`.

    Failure mode it fixes: #1956 — the 2026-05-13 m20 build halted with
    `label='activities.yaml' but fence info has 'module.md'` after the
    parser scraped `activities.yaml` from a `<plan_reasoning>` block.
    The writer prompt mandates the fence-info-string form
    (`markdown file=module.md`) and never emits standalone label lines;
    the strict regex below rejects embedded matches without breaking
    `test_parse_writer_output_rejects_label_vs_fence_name_mismatch`,
    whose adversarial fixture uses a true standalone `activities.yaml`
    label line.
    """
    match = _LABEL_LINE_RE.match(line)
    return match.group("name") if match else None
```

Pin the artifact-name alternation to the canonical `WRITER_ARTIFACTS` tuple — do NOT hardcode if you can build the alternation at import time, e.g.:

```python
_LABEL_LINE_RE = re.compile(
    r"^[\s>#\-*]*(?P<name>"
    + "|".join(re.escape(name) for name in WRITER_ARTIFACTS)
    + r")\s*:?\s*$"
)
```

This keeps the helper in lock-step with the canonical tuple — if `WRITER_ARTIFACTS` ever grows or shrinks, the regex updates automatically.

### Step 2: swap the call site at line 2429

Change exactly one line in `parse_writer_output_strict_json`:

```python
        name = _artifact_name_from_text(line)
```

→

```python
        name = _artifact_name_from_label_line(line)
```

Do NOT touch line 2376 — the fence-info-string call site needs the embed-search semantics.

### Step 3: regression tests

Add to `tests/build/test_linear_pipeline.py`:

**Test A — minimal CoT case:**

```python
def test_parse_writer_output_accepts_plan_reasoning_with_artifact_mentions() -> None:
    """Regression for #1956. `<plan_reasoning>` CoT blocks may list
    artifact names inside `<implementation_map>` table rows like
    `- act-5 | activities.yaml | INJECT_ACTIVITY ...`. These are
    prose mentions, not label headers. The parser must not scrape
    them as pending_name and false-positive against the actual
    fence-info-string label (`markdown file=module.md`).

    The 2026-05-13 m20 build of `a1/my-morning` halted with this
    exact pattern after Card 1 (writer-isolation) shipped — the
    writer-isolated `curriculum-writer` agent produced a clean
    output per spec, but the parser misread CoT mentions as labels.
    """
    output = '''<plan_reasoning section="Діалоги">
<implementation_map>
- act-5 (match-up verb-pairs) | activities.yaml | INJECT_ACTIVITY end of §Діалоги | inline match-up
- step-2 | module.md | §Діалоги paragraphs 2–3 | prose with я/ти reflexive forms
</implementation_map>
</plan_reasoning>

```markdown file=module.md
# Module body
Some prose.
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "section": "Діалоги",
    "title": "Match-up",
    "type": "match_up",
    "instruction": "Match these.",
    "items": [
      {"left": "вмивати", "right": "вмиватися"},
      {"left": "одягати", "right": "одягатися"}
    ]
  }
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176"}
]
```
'''
    artifacts = linear_pipeline.parse_writer_output_strict_json(output)
    assert set(artifacts) == {"module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"}
    assert "Module body" in artifacts["module.md"]
    assert yaml.safe_load(artifacts["activities.yaml"])[0]["id"] == "act-1"
```

**Test B — real-world artefact replay (preserves the actual failure case):**

Load the first 200 lines of the failed writer_output.raw.md, then append minimal placeholders for `activities.yaml`, `vocabulary.yaml`, `resources.yaml` so the parser has all four artifacts to find. This proves the actual prod failure path now parses. Use `pathlib.Path` to read from the failed build worktree if it exists; otherwise skip with a clear message:

```python
def test_parse_writer_output_handles_real_m20_plan_reasoning_prefix() -> None:
    """Replay the prefix of the actual 2026-05-13 m20 failed build
    that triggered #1956. The first ~95 lines are 4 `<plan_reasoning>`
    blocks with `<implementation_map>` rows mentioning `activities.yaml`.
    The 96th line begins the first fence (`markdown file=module.md`).

    Tier-1 replay: prove the parser no longer trips on this prefix.
    """
    raw_path = Path(
        ".worktrees/builds/a1-my-morning-20260513-122043/"
        "curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md"
    )
    if not raw_path.exists():
        pytest.skip(
            "Failed m20 build worktree not present — this is the "
            "real-world repro for #1956, optional in clean environments"
        )
    raw = raw_path.read_text(encoding="utf-8")
    # Trim to the first activities.yaml fence's start to exercise the
    # parser's preceding-label logic without depending on whatever
    # downstream JSON ordering/quirks the real artefact has. The
    # `<plan_reasoning>` prefix is what triggers #1956.
    # Build a minimal valid completion after the module.md fence.
    module_end = raw.find("\n```\n", raw.find("```markdown file=module.md"))
    if module_end == -1:
        pytest.skip("Real m20 artifact shape changed; refresh fixture")
    prefix = raw[: module_end + len("\n```\n")]
    completion = (
        '\n```json file=activities.yaml\n'
        '[{"id":"a","section":"x","title":"x","type":"match_up","instruction":"x",'
        '"items":[{"left":"x","right":"y"}]}]\n'
        '```\n\n'
        '```json file=vocabulary.yaml\n'
        '[{"lemma":"ранок","translation":"morning","pos":"noun","usage":"x"}]\n'
        '```\n\n'
        '```json file=resources.yaml\n'
        '[{"title":"x"}]\n'
        '```\n'
    )
    artifacts = linear_pipeline.parse_writer_output_strict_json(prefix + completion)
    assert set(artifacts) == {"module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"}
```

Place these in `tests/build/test_linear_pipeline.py` adjacent to `test_parse_writer_output_rejects_label_vs_fence_name_mismatch` so the related cases sit together. Import `pytest`, `pathlib.Path`, and any deps already in the test file.

### Step 4: leave the existing mismatch test untouched

`test_parse_writer_output_rejects_label_vs_fence_name_mismatch` (line 390) must continue to pass. Its fixture uses a true standalone-label line (`activities.yaml` alone on its line) which `_artifact_name_from_label_line` still recognizes via the strict regex. If your implementation accidentally regresses this test, the fix is wrong — revisit the regex.

---

## Execution steps (numbered, per dispatch-brief checklist)

All commands run in the worktree unless prefixed otherwise. The runtime auto-creates the worktree from `origin/main`; you start with a fresh branch `codex/parser-label-tightening-2026-05-13`.

1. **Inspect the failed writer output to confirm understanding before coding:**
   ```bash
   sed -n '1,20p;90,100p' /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260513-122043/curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md
   ```
   Confirm: lines 1–20 are `<plan_reasoning>` with `| activities.yaml |` rows; line 96 is ```` ```markdown file=module.md ````. If reality differs, **STOP and report** — the bug premise may have shifted.

2. **Implement the fix in `scripts/build/linear_pipeline.py`:**
   - Add the `_LABEL_LINE_RE` module-level compiled regex.
   - Add `_artifact_name_from_label_line` near `_artifact_name_from_text`.
   - Swap the single call site at line 2429.

3. **Add regression tests in `tests/build/test_linear_pipeline.py`:**
   - `test_parse_writer_output_accepts_plan_reasoning_with_artifact_mentions` — minimal CoT case.
   - `test_parse_writer_output_handles_real_m20_plan_reasoning_prefix` — real-world replay.

4. **Run the full linear_pipeline test suite to confirm zero regressions:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/build/test_linear_pipeline.py -v 2>&1 | tail -60
   ```
   Quote the full output's last 30 lines (must show both new tests passed AND the existing mismatch test still passes). Per #M-7 (HARD RULE): pytest locally before push, full failure on red.

5. **Run targeted broader pytest sanity-check on adjacent paths:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/build/ -v 2>&1 | tail -40
   ```
   Quote summary line.

6. **Lint:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py 2>&1 | tail -10
   ```
   Quote final line — should be `All checks passed!`.

7. **Commit (conventional message + #1956 closer):**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && git add -A && git commit -m "$(cat <<'EOF'
   fix(linear_pipeline): tighten preceding-label detection to standalone-label-lines (#1956)

   Parser was scraping any line for word-boundary embed matches of artifact
   names, including inside `<plan_reasoning>` CoT XML blocks whose
   `<implementation_map>` rows list pipe-delimited `obligation | artifact |
   ...`. This false-positived against the writer's fence-info-string label
   (`markdown file=module.md`) and halted m20's first end-to-end build
   under Card 1 writer-isolation with:

     "Writer output has mismatched artifact label and fence name at line
      96: label='activities.yaml' but fence info has 'module.md'"

   The writer prompt mandates the fence-info-string form exclusively (see
   writer_prompt.md lines 1017-1078) and never emits standalone label
   header lines. Tighten the preceding-label detection at the single call
   site (linear_pipeline.py:2429) to require the artifact name be the
   dominant content of a standalone line — preserves the legacy adversarial
   guard for true label-vs-fence-info mismatches (test
   `test_parse_writer_output_rejects_label_vs_fence_name_mismatch` stays
   green), rejects CoT prose mentions.

   Two new tests:
   - minimal `<plan_reasoning>` CoT case
   - real-world replay of the 2026-05-13 m20 failed writer_output.raw.md
     prefix (skips if the failed-build worktree has been cleaned)

   Closes #1956.

   X-Agent: codex/parser-label-tightening-2026-05-13

   Co-Authored-By: Codex GPT-5.5 <noreply@openai.com>
   EOF
   )"
   ```

8. **Push branch:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && git push -u origin codex/parser-label-tightening-2026-05-13
   ```

9. **Open PR (NO auto-merge):**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/parser-label-tightening-2026-05-13 && gh pr create --title "fix(linear_pipeline): writer-output parser preceding-label-line tightening (#1956)" --body "$(cat <<'EOF'
   ## Summary

   - Tightens `parse_writer_output_strict_json`'s preceding-label detection to require the artifact name be the dominant content of a standalone line (`_artifact_name_from_label_line` helper), not a word-boundary embed match anywhere in any line (`_artifact_name_from_text`).
   - The embed-search call site for fence-info-string extraction (line 2376) is untouched — it still needs to find `module.md` inside `markdown file=module.md`.
   - Adds two regression tests; preserves the existing adversarial mismatch test.

   ## Why

   The 2026-05-13 m20 (`a1/my-morning`) V7 build under Card 1 writer-isolation halted at writer-output parse because the parser scraped `activities.yaml` from `<plan_reasoning><implementation_map>` CoT rows like `- act-5 | activities.yaml | INJECT_ACTIVITY ...` and then saw the writer's fence-info-string label `markdown file=module.md` as a mismatch. The writer followed prompt spec; the parser was over-eager.

   Tier-1 verification of Card 1 had already shown the new `curriculum-writer` agent works as designed (`tool_calls_total=12, verify_words_calls=5, tool_theatre_violations=[]`). This PR unblocks Phase 2 of the student-aware immersion plan.

   ## Test plan

   - [x] `pytest tests/build/test_linear_pipeline.py -v` — all green, new + existing tests.
   - [x] `pytest tests/build/ -v` — full build-tests suite green.
   - [x] `ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py` — clean.
   - [ ] Follow-up: re-run m20 V7 build under Monitor (orchestrator handles post-merge).

   Closes #1956.

   🤖 Generated with [Codex CLI](https://github.com/openai/codex-cli)
   EOF
   )"
   ```

10. **Do NOT merge.** Orchestrator merges after CI green + spot-check review. Print the PR URL via `gh pr view --json url` so the orchestrator can pick it up.

---

## Acceptance criteria

A run is **DONE** when ALL of these hold:

- [ ] Branch `codex/parser-label-tightening-2026-05-13` pushed.
- [ ] PR opened (URL printed).
- [ ] `tests/build/test_linear_pipeline.py -v` shows ≥1 added test passing AND `test_parse_writer_output_rejects_label_vs_fence_name_mismatch` still passing.
- [ ] `ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py` clean.
- [ ] Conventional commit on the branch with `Closes #1956` in the body and X-Agent trailer.

## On halt

If you hit any of these, **STOP** and report in the final task output (don't improvise):

- The existing `test_parse_writer_output_rejects_label_vs_fence_name_mismatch` regresses → your regex is too loose or you're scraping pending_name from the wrong call site.
- The minimal `<plan_reasoning>` test fixture you authored doesn't parse → your regex is too strict, probably anchoring on something the writer doesn't emit.
- The failed m20 worktree at `.worktrees/builds/a1-my-morning-20260513-122043/` is gone → skip Test B with a clear message, run Test A only.
- Unrelated test failures appear (not in `test_linear_pipeline.py`) → flag in final report, don't try to fix.

Do not deviate from the 1-helper + 1-call-site-swap structure. The fix is intentionally minimal — broader parser refactors are out of scope.
