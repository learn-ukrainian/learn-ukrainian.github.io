# Dispatch brief — m20 italic-rule HARD REJECT prompt patch (#2095)

Same shape as merged PR #2094 (which took wiki obligation coverage from 22% → 100% in one rebuild). The writer prompt at `scripts/build/phases/linear-write.md:76-80` already lists italic-bad-form patterns as "forbidden" but the writer keeps emitting them anyway (m20 build #17 had `*Я дивюся*` at line 65 and `*Я користуювася*` at line 85 — both should use `<!-- bad -->...<!-- /bad -->` markers per the same prompt). Convert the warning into a HARD REJECT contract + pre-emit self-check, identical pattern to #2094.

## Verifiable claims this work produces

| Claim | Evidence (quote raw) |
|---|---|
| File `scripts/build/phases/linear-write.md` modified | `git diff main scripts/build/phases/linear-write.md` |
| HARD REJECT wording added near existing forbidden-pattern list | `grep -n 'HARD REJECT\|MUST wrap' scripts/build/phases/linear-write.md` |
| Pre-emit self-check `<bad_form_audit>` line added | `grep -n 'bad_form_audit' scripts/build/phases/linear-write.md` |
| Pre-commit hooks pass | `git push` output |
| PR opened | `gh pr view --json url` |

## Worktree setup (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-italic-rule -b fix/m20-writer-italic-bad-form-hard-reject origin/main
cd .worktrees/m20-italic-rule
```

## The patch — exact edits

Target: `scripts/build/phases/linear-write.md`

### Edit 1 — strengthen the existing "CONCRETE FORBIDDEN PATTERNS" section

Find this exact line in the file (currently around line 76):

```
**CONCRETE FORBIDDEN PATTERNS — close-the-class enumeration.** These are the exact patterns that failed m20 rebuilds #2–#6. The `<!-- bad -->` marker is the ONLY accepted form for a bad-form contrast. Any of the following will trip `vesum_verified`, `formatting_standards`, or `russianisms_clean`:
```

Replace with (note the `(#2094, #2095)` reference + the explicit HARD REJECT wording mirroring how #2094 hardened the implementation_map rule):

```
**CONCRETE FORBIDDEN PATTERNS — HARD REJECT, close-the-class enumeration (#2094, #2095).** These are the exact patterns that failed m20 rebuilds #2–#17. The `<!-- bad -->` marker is the ONLY accepted form for a bad-form contrast.

**Silent emission of any italic-wrapped bad form is a HARD REJECT — the rebuild is wasted and `vesum_verified` will fail.** Yesterday's m20 build #17 emitted `❌ *Я дивюся* → ✅ **Я дивлюся**` and `not the L2 trap form ❌ *Я користуювася*` — both patterns the writer KNEW the rule for (the same writer used `<!-- bad -->` markers correctly in the same module for завтрак / полотенце / одіватися). Inconsistent application of this rule is the same failure class as silent obligation omission, and it now carries the same HARD REJECT consequence.

Any of the following will trip `vesum_verified`, `formatting_standards`, or `russianisms_clean`:
```

### Edit 2 — add a pre-emit self-check after the forbidden-pattern enumeration

Find the line that closes the forbidden-pattern enumeration (search for the line ending the list of `- ❌` items — typically a paragraph or blank line follows the last `- ❌` bullet). Right after the LAST forbidden-pattern bullet (before the next ## or ### heading), add this self-check block:

```

### Pre-emit bad-form audit (mandatory — #2095)

Before emitting the four artifact fences (after the `<implementation_map_audit>` line from #2094), you MUST self-audit your draft for any italic-wrapped bad-form pattern:

1. Scan your draft `module.md` for any of: `❌ *X*`, `*X*, not *Y*`, `... not *Y*.`, `... not *Y*,`, or `say X, not Y`.
2. For EVERY match, the bad form `X` or `Y` MUST be wrapped in `<!-- bad -->X<!-- /bad -->` markers, NOT in `*italic*` and NOT bare prose. The Russianism, surzhyk, calque, or L2-trap form is the load-bearing case.
3. If your scan finds zero italic-bad-form patterns, you may proceed. If your scan finds any, STOP, replace them with `<!-- bad -->` markers, and re-scan.

Emit a single visible audit line BEFORE the artifact fences (after the `<implementation_map_audit>` line):

`<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>`

If this audit line is missing, or if `remaining > 0`, the writer has failed the protocol and the rebuild is wasted. Mechanical consistency on this rule unlocks all m20 ship velocity.
```

## Verification (do these, quote raw output in PR body)

```bash
# venv symlinked into worktree by delegate.py
# 1. HARD REJECT wording present
grep -n 'HARD REJECT\|silent emission' scripts/build/phases/linear-write.md

# 2. Pre-emit audit landed
grep -n 'bad_form_audit\|Pre-emit bad-form audit' scripts/build/phases/linear-write.md

# 3. Diff scope — single file, modest LOC
git diff --stat main
git diff --name-only main
# Expected: only `scripts/build/phases/linear-write.md`

# 4. Pre-commit hooks (venv symlinked into worktree by delegate.py)
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pre_commit run --files scripts/build/phases/linear-write.md
```

## Commit + PR

```bash
# venv symlinked into worktree by delegate.py
git add scripts/build/phases/linear-write.md
git commit -m "fix(writer): italic bad-form pattern is now HARD REJECT (#2095)

The writer prompt at scripts/build/phases/linear-write.md:76-80 already
lists italic-bad-form patterns as forbidden, but m20 build #17 emitted
two violations in a single module:

- module.md:65 — '❌ *Я дивюся* → ✅ **Я дивлюся**'
- module.md:85 — 'not the L2 trap form ❌ *Я користуювася*'

The same writer used <!-- bad --> markers correctly in the same module
for завтрак / полотенце / одіватися. Inconsistent application of the
rule — knows-the-rule, applies-partially.

This patch:

1. Converts the existing 'forbidden patterns' warning into a HARD REJECT
   contract — same shape that worked for #2094 (wiki obligation coverage
   went 22% → 100% in one rebuild after that rule became HARD REJECT).

2. Adds a pre-emit <bad_form_audit> self-check the writer must perform
   on its own draft. Mirrors the <implementation_map_audit> mechanism
   #2094 introduced; same enforcement shape.

Background: docs/dispatch-briefs/2026-05-17-m20-italic-rule-hard-reject.md.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Gemini <noreply@anthropic.com>"
git push -u origin fix/m20-writer-italic-bad-form-hard-reject
gh pr create --title "fix(writer): italic bad-form pattern is now HARD REJECT (#2095)" --body "$(cat <<'EOF'
## Summary

Path B follow-up to PR #2094 — same prompt-hardening shape, applied to the italic-bad-form rule that the writer knows but inconsistently applies.

m20 build #17 (post-PR #2094) showed:
- ✅ wiki obligation coverage 18/18 = 100% (PR #2094 worked)
- ❌ vesum_verified failed on `*Я дивюся*` and `*Я користуювася*` — italic-wrapped bad forms instead of `<!-- bad -->` markers, in violation of the existing rule at linear-write.md:76-80

The fix is the same shape that just succeeded for obligation coverage:
- Convert the warning into HARD REJECT wording
- Add a pre-emit `<bad_form_audit>` self-check line

## Test plan

- [x] Pre-commit hooks pass
- [ ] After merge: re-run m20 build, expect vesum_verified to pass (was failing on italic bad-form leaks into VESUM lookup)
- [ ] Remaining m20 gates: l2_exposure_floor + wiki_manifest.json proper-noun false positive are separate fixes

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## NO auto-merge — orchestrator merges after diff review

## Out of scope

- Do NOT touch any other file. Single file, single concern.
- Do NOT lower any threshold.
- Do NOT add tests (prompt-text-only change, no logic).
- Do NOT modify m20 module artifacts directly.

## Anti-fabrication reminders

- Quote raw output from grep/git diff/pre-commit in the PR body. Don't paraphrase.
- If the existing line text doesn't match exactly (perhaps shifted by another edit), STOP. Don't manually rewrite — escalate.
