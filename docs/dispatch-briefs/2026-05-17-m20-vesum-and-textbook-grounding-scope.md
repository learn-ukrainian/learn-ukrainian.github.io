# Dispatch brief — m20: VESUM quiz `correctAnswer` + textbook_grounding punctuation tolerance (#2103)

## Two related gate-scope bugs surfaced by m20 build #18

Both touch `scripts/build/linear_pipeline.py`; one PR, two commits, two regression tests.

### Bug 1 — VESUM gate doesn't recognize quiz `correctAnswer` field

`_activity_vesum_text` at `linear_pipeline.py:5330` has:

```python
if key == "options" and "answer" in node:
    walk_answer_options(child, answer_values(node.get("answer")))
    continue
```

This intentionally skips wrong-distractor option values, walking ONLY the option matching `answer`. But m20 build #18 activities.yaml has quiz items that use `correctAnswer` (camelCase variant), not `answer`. The activity_schema gate accepts both spellings, but the VESUM walker only knows `answer`. When the writer emits `correctAnswer`, the conditional skip doesn't fire → walk falls through to "walk every option" → wrong distractors leak into VESUM scope.

m20 build #18 evidence (`.worktrees/builds/a1-my-morning-20260517-123835/curriculum/l2-uk-en/a1/my-morning/activities.yaml:221-234`):

```yaml
- question: Яка з форм правильна для «я» у дієсловах на -уватися?
  options:
  - користуюся
  - користуювася   # intentional distractor — VESUM caught it
  - користуєся     # intentional distractor — VESUM caught it
  correctAnswer: користуюся
- question: Яка з форм правильна для «я» у дієслові «дивитися»?
  options:
  - дивюся         # intentional distractor — VESUM caught it
  - дивлюся
  - дивиться
  correctAnswer: дивлюся
```

`vesum_verified.missing` = `["дивюся", "користуювася"]` — both legitimate quiz distractors.

**Fix:** accept either `answer` or `correctAnswer` (and merge values from both if both are present). One-line change at line 5330 plus an `answer_values` helper update if needed.

### Bug 2 — textbook_grounding matcher is punctuation-exact

m20 build #18 evidence (`.worktrees/builds/.../my-morning/python_qg.json`):

- plan reference title: `"Захарійчук Grade 1, p.24"` (NO comma after `Захарійчук`)
- module.md attribution emitted by writer: `*— Захарійчук, Grade 1, p.24*` (WITH comma)
- `textbook_grounding.matched = []` despite the attribution being right next to a long blockquote at module.md:104-106.

Find `_textbook_grounding_gate` or whatever function compares plan_references[i].title against module attribution strings. The comparison currently uses an exact-substring or strict equality. Make it punctuation-insensitive (lowercase + strip `[.,;:!?\-—–\s]` from both sides before comparing).

Conservative fix shape: normalize_for_match(s) = `re.sub(r"[^\wа-яіїєґА-ЯІЇЄҐ]+", "", s.lower())`. Compare normalized titles. Equivalent to "ignore punctuation and spacing."

Test the fix against both:
- `Захарійчук Grade 1, p.24` (plan ref, no comma in middle) matches `Захарійчук, Grade 1, p.24` (writer attribution, comma after surname)
- BUT `Захарійчук Grade 2, p.24` does NOT match `Захарійчук Grade 1, p.24` (substantive difference preserved)

## Worktree setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-gate-scope-fixes -b fix/m20-vesum-and-textbook-grounding-scope origin/main
cd .worktrees/m20-gate-scope-fixes
```

## Verification

```bash
# venv symlinked into worktree by delegate.py
.venv/bin/pytest tests/build/test_linear_pipeline.py -k "vesum or textbook" -v
git diff --stat main
git diff --name-only main
.venv/bin/python -m pre_commit run --files scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
```

Quote raw outputs in PR body.

## Regression tests

Add two tests to `tests/build/test_linear_pipeline.py`:

**Test 1** — VESUM quiz `correctAnswer`:
- Build a quiz-typed activity with `options: [<wrong-form>, <correct-form>]` and `correctAnswer: <correct-form>` (note: `correctAnswer`, NOT `answer`).
- Assert `_activity_vesum_text` output does NOT contain `<wrong-form>`.
- Counterpart: same activity with `answer` instead of `correctAnswer` — same expected output. Both spellings tolerated.

**Test 2** — textbook_grounding punctuation tolerance:
- Build a module text with attribution `*— Захарійчук, Grade 1, p.24*`.
- Build plan_references with `title: "Захарійчук Grade 1, p.24"` (no comma).
- Assert the gate matches.
- Counterpart: a different page (`Захарійчук Grade 1, p.52`) does NOT match the same attribution.

## Commit + PR

```bash
# venv symlinked into worktree by delegate.py
git add scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
git commit -m "fix(audit): VESUM accepts quiz correctAnswer + textbook_grounding ignores punctuation (#2103)

m20 build #18 surfaced two gate-scope bugs blocking ship despite the
writer obeying all new prompt rules (implementation_map_audit and
bad_form_audit both showed clean state).

1) VESUM quiz correctAnswer:
   _activity_vesum_text at linear_pipeline.py:5330 only checks for
   'answer' field when filtering wrong-distractor options. Quiz
   activities can use 'correctAnswer' (camelCase) which
   activity_schema accepts — but VESUM walker doesn't, so distractors
   leak. m20 build #18 vesum_verified.missing = ['дивюся',
   'користуювася'] — both legitimate distractors in an act-7 quiz
   with correctAnswer field. Fix: accept either spelling.

2) textbook_grounding punctuation:
   Plan ref title 'Захарійчук Grade 1, p.24' (no comma after surname)
   vs writer attribution '— Захарійчук, Grade 1, p.24' (comma). Exact
   match fails. Fix: punctuation-insensitive comparison via
   normalize_for_match() that strips non-alphanumeric chars and
   lowercases. Preserves substantive differences (page number,
   surname).

Two regression tests cover both fixes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Codex <noreply@anthropic.com>"
git push -u origin fix/m20-vesum-and-textbook-grounding-scope
gh pr create --title "fix(audit): VESUM accepts quiz correctAnswer + textbook_grounding ignores punctuation (#2103)" --body "$(cat <<'EOF'
## Summary

Two gate-scope bugs blocking m20 ship despite the writer obeying all new prompt rules from PR #2094 (implementation_map_audit) and PR #2095 (bad_form_audit). Build #18 evidence at \`.worktrees/builds/a1-my-morning-20260517-123835/curriculum/l2-uk-en/a1/my-morning/python_qg.json\`.

### Bug 1 — VESUM quiz \`correctAnswer\`

\`_activity_vesum_text\` at \`linear_pipeline.py:5330\` only checks for \`answer\` field. Quiz activities can use \`correctAnswer\` (camelCase variant the activity_schema gate accepts). When writer emits \`correctAnswer\`, wrong-distractor filter doesn't fire → distractors leak into VESUM scope. Build #18: \`vesum_verified.missing = [\"дивюся\", \"користуювася\"]\` — both legitimate quiz distractors.

### Bug 2 — textbook_grounding punctuation

Plan ref \`Захарійчук Grade 1, p.24\` vs writer attribution \`*— Захарійчук, Grade 1, p.24*\` — exact match fails on one extra comma. Punctuation-insensitive normalization fixes it without weakening real-mismatch detection (page numbers, surnames preserved).

## Test plan

- [x] Regression test 1: quiz with \`correctAnswer\` filters distractors
- [x] Regression test 1b: quiz with \`answer\` still works (backward-compat)
- [x] Regression test 2: punctuation-different attribution matches
- [x] Regression test 2b: substantively-different page does NOT match
- [ ] After merge: m20 rebuild expected to pass vesum_verified AND textbook_grounding

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Out of scope

- Do NOT change schema validation (it already accepts both `answer` and `correctAnswer`).
- Do NOT modify the writer prompt to canonicalize one spelling — that's a different concern.
- Do NOT bundle additional gate fixes into this PR.
- NO auto-merge.

## Anti-fabrication

Quote pytest output (`N passed in Ms`) raw. Quote `git diff --name-only main` to prove single-file scope. If the existing match function is shaped differently than expected, STOP and describe what you found before patching.
