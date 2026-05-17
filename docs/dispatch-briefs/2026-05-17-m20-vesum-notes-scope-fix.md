# Dispatch brief — m20 vesum_verified scope: exclude resources notes (#2098)

## Root cause (verified via grep)

`scripts/build/linear_pipeline.py:5247` includes `entry.get("notes", "")` from every `resources.yaml` entry in the text fed to VESUM verification:

```
5247:            parts.append(_strip_metalinguistic(str(entry.get("notes", ""))))
```

m20 build #17 evidence: `resources.yaml` notes field contains the textbook attribution `"A1 reader 'Уранці Євген' (за Ларисою Ніцою) models..."`. The form `Ніцою` is the legitimately-inflected instrumental of the Ukrainian author surname Ніца, but VESUM doesn't index Ukrainian proper-noun inflections. Gate fails with `missing: ["Ніцою", ...]`.

The `notes` field is descriptive metadata about a resource (textbook attribution, sourcing context), not learner-facing curriculum content. It should NOT be in scope for `vesum_verified`. Other resource fields (title, lemma, usage) remain in scope — those are content the learner sees.

## Verifiable claims

| Claim | Evidence |
|---|---|
| Line 5247 `entry.get("notes", "")` removed from vesum scope | `git diff main scripts/build/linear_pipeline.py` |
| `title`, `lemma`, `usage` resource fields still scanned | The other 3 `parts.append` lines (5246, 5242, 5243) unchanged |
| Regression test added | `git diff main tests/build/test_linear_pipeline.py` |
| Tests pass | `.venv/bin/pytest tests/build/test_linear_pipeline.py -k vesum -v` raw output |
| Pre-commit hooks pass | `git push` output |
| PR opened | `gh pr view --json url` |

## Worktree setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-vesum-notes-scope -b fix/m20-vesum-skip-resource-notes origin/main
cd .worktrees/m20-vesum-notes-scope
```

## The patch

Target: `scripts/build/linear_pipeline.py`

Find the block around line 5236-5247 that assembles `parts` for VESUM verification. The exact line to remove (or comment) is:

```python
            parts.append(_strip_metalinguistic(str(entry.get("notes", ""))))
```

Replace with a comment explaining the exclusion:

```python
            # Resource `notes` field is descriptive metadata (textbook
            # attribution, sourcing context) — proper-noun inflections
            # like "за Ларисою Ніцою" trip VESUM with false positives.
            # The notes field is NOT learner-facing content. Skip from
            # VESUM scope. Keep title / lemma / usage in scope (#2098).
```

## Regression test

Add to `tests/build/test_linear_pipeline.py`:

A test demonstrating that:
1. A resources list with a `notes` field containing a fabricated/non-VESUM word does NOT trip the gate.
2. A resources list with a `title` field containing the same word DOES still trip the gate.

Test name suggestion: `test_vesum_gate_skips_resource_notes_field`.

## Verification

```bash
# venv symlinked into worktree by delegate.py
.venv/bin/pytest tests/build/test_linear_pipeline.py -k vesum -v
git diff --stat main
git diff --name-only main
# Expected: scripts/build/linear_pipeline.py + tests/build/test_linear_pipeline.py
.venv/bin/python -m pre_commit run --files scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
```

Quote raw output in PR body.

## Commit + PR

```bash
# venv symlinked into worktree by delegate.py
git add scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
git commit -m "fix(audit): vesum_verified excludes resources notes field (#2098)

m20 build #17 evidence: resources.yaml had textbook attribution
\"(за Ларисою Ніцою)\" in notes field. VESUM gate scanned it,
reported \"Ніцою\" as missing — but it's the legitimate instrumental
of a Ukrainian author surname (Лариса Ніца), and VESUM doesn't
index Ukrainian proper-noun inflections.

The notes field is descriptive metadata (textbook attribution,
sourcing context), not learner-facing curriculum content. Exclude
from vesum scope. Other resource fields (title, lemma, usage)
remain in scope — those are content the learner sees.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Gemini <noreply@anthropic.com>"
git push -u origin fix/m20-vesum-skip-resource-notes
gh pr create --title "fix(audit): vesum_verified excludes resources notes field (#2098)" --body "$(cat <<'EOF'
## Summary

vesum_verified gate at linear_pipeline.py:5247 included resources.yaml \`notes\` field in scope. The notes field is descriptive metadata (textbook attribution, sourcing context) and frequently contains inflected Ukrainian proper nouns (author surnames, place names) that VESUM doesn't index — guaranteed false-positive surface.

m20 build #17 example: \"за Ларисою Ніцою\" attribution trip. \"Ніцою\" is the legitimate instrumental of children's-author Лариса Ніца.

This patch excludes only the notes field. Other resource fields (title, lemma, usage) remain in scope.

## Test plan

- [x] Regression test: notes-field fabricated word doesn't trip gate
- [x] Regression test: title-field fabricated word DOES trip gate (scope preserved)
- [ ] After merge: m20 rebuild expected to clear the Ніцою false positive

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Out of scope

- Do NOT touch the other 3 `parts.append` lines.
- Do NOT modify `_strip_metalinguistic`.
- Do NOT change vesum gate logic for module text.

## Anti-fabrication

Quote raw pytest output, raw git diff, raw pre-commit output. NO auto-merge.
