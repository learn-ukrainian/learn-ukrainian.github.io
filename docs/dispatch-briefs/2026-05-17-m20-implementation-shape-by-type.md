# Dispatch brief — writer prompt: per-obligation-type implementation shape (#2105)

## Root cause (m20 build #20)

PR #2094 forced the writer to LIST all 18 obligations in `<implementation_map>`. The writer does that mechanically. But the wiki_coverage gate at `scripts/audit/wiki_coverage_gate.py:276-320` verifies actual IMPLEMENTATION, not just listing — and the writer's implementation shape is wrong for ~half the obligation types.

Build #20 evidence (`wiki_coverage_gate.json`): **44.4% coverage = 8/18**.

Specific failure classes mapped to gate logic:

| Failure reason | Gate predicate (linear ref) | Writer's mistake |
|---|---|---|
| `contrast_pair_not_in_activity` (err-2…err-6, 5 fails) | `wiki_coverage_gate.py:288-289` requires artifact=`activities.yaml` for l2_error contrast_pair | Writer puts l2_error claims in module.md instead of activities.yaml |
| `missing_incorrect` (err-1) | `:282-283` requires the manifest's `incorrect` substring to appear in target_text | Writer didn't include the specific incorrect form verbatim |
| `ban_substance_missing` (ban-1,2,3) | `:316-318` requires the manifest's `rule` text to be substantively present | Writer didn't quote or paraphrase the ban rule with enough substance |
| `sequence_claim_missing` (step-4) | `:310-312` requires the step's `required_claim` content present | Writer didn't include step-4's content |

## Verifiable claims this work produces

| Claim | Evidence |
|---|---|
| File `scripts/build/phases/linear-write.md` modified | `git diff main scripts/build/phases/linear-write.md` |
| Per-obligation-type implementation rules added | `grep -n 'IMPLEMENTATION SHAPE\|MUST.*activities.yaml' scripts/build/phases/linear-write.md` |
| Pre-emit `<obligation_implementation_audit>` line added | `grep -n 'obligation_implementation_audit' scripts/build/phases/linear-write.md` |
| Pre-commit hooks pass | `git push` output |
| PR opened | `gh pr view --json url` |

## Worktree setup (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-impl-shape -b fix/m20-writer-implementation-shape-by-type origin/main
cd .worktrees/m20-impl-shape
```

## The patch — add a new section to `scripts/build/phases/linear-write.md`

Insert AFTER the existing `<implementation_map>` block (~line 28, after the existing #2094 block) and AFTER the `<bad_form_audit>` pre-emit section (#2095). Find the next ## or ### heading after both audit lines and insert before it.

Add the following section:

```markdown
### IMPLEMENTATION SHAPE by obligation type (mandatory — #2105)

Listing an obligation in `<implementation_map>` is necessary but NOT sufficient. The wiki_coverage_gate at `scripts/audit/wiki_coverage_gate.py:276-320` verifies actual implementation per obligation type. Mismatched implementation shape is a HARD REJECT — the gate will report `contrast_pair_not_in_activity`, `ban_substance_missing`, `sequence_claim_missing`, or `missing_incorrect_and_correct` and fail the build.

Implementation shape per obligation type:

**`l2_error` with `treatment: contrast_pair`** — MUST live in `activities.yaml` as an `error-correction` activity item. The item MUST contain BOTH the manifest's `incorrect` form and the `correct` form verbatim (substring-match — case-insensitive but punctuation-preserving). NOT in module.md prose. NOT as an inline contrast block. Concrete shape:

```yaml
- id: act-N
  type: error-correction
  items:
    - sentence: "<context sentence with the wrong form>"
      error: "<verbatim incorrect substring from manifest>"
      correction: "<verbatim correct substring from manifest>"
```

If the manifest's `incorrect` is `"Я прокидаєшся. / Він прокидаюся."` (slash-separated alternates), include BOTH alternates in either separate items or one item where the sentence covers both. The literal substring `Я прокидаєшся.` AND `Він прокидаюся.` MUST both appear in activities.yaml.

**`decolonization_ban`** — MUST quote the manifest's `rule` text substantively in module.md prose (NOT just a passing mention; the gate checks `_claim_markers_present` which requires multiple keyword markers from the rule text to appear). Concrete shape: in module.md, add a paragraph that paraphrases the rule's core constraint using its distinctive vocabulary. If the ban rule says "категорично заборонено використовувати російськомовні пояснення", your prose must contain those distinctive phrases (заборонено, російськомовні, пояснення) close together. Bare phrases like "we use Ukrainian only" are NOT substantive enough.

**`sequence_step`** — MUST include the step's `required_claim` content substantively in module.md prose. Same `_claim_markers_present` check as bans. Read each step's `required_claim` from the wiki manifest and ensure the distinctive vocabulary (verb names, technical terms like "епентетичний л", "суфікс -ва-", specific lexeme examples) appears in your prose for the matching section.

**`phonetic_rule`** — MUST include BOTH the `written` and `spoken` forms verbatim AND `_phonetic_examples_present` (specific example words). Already worked in build #20 — no change needed but the rule is restated here for completeness.

### Pre-emit implementation audit (mandatory — #2105)

AFTER the `<implementation_map_audit>` (#2094) and `<bad_form_audit>` (#2095) lines, add a third visible audit line by self-checking each obligation against its implementation shape:

For EACH obligation in your `<implementation_map>`:
1. If type=`l2_error` with treatment=`contrast_pair`: open `activities.yaml`, search for an `error-correction` item containing BOTH `incorrect` and `correct` substrings verbatim. If not found, FAIL this obligation.
2. If type=`decolonization_ban`: scan module.md prose for ≥3 distinctive substantive phrases from the manifest's `rule` text. If <3 found, FAIL this obligation.
3. If type=`sequence_step`: scan module.md prose for the distinctive vocabulary from `required_claim`. If thin or missing, FAIL this obligation.
4. If type=`phonetic_rule`: scan module.md for both `written` and `spoken` forms verbatim. If either missing, FAIL this obligation.

Emit a single visible audit line BEFORE the artifact fences:

`<obligation_implementation_audit>obligations_checked=N implemented=M failed_ids=[<list any IDs that failed self-check>]</obligation_implementation_audit>`

If `failed_ids` is non-empty, STOP. Go back and fix the failing obligation's implementation shape. Re-run the audit. Only when `failed_ids=[]` may you proceed to emit the four artifact fences.

If this audit line is missing, or if `implemented < obligations_checked`, the rebuild is wasted — the wiki_coverage gate will reach the same conclusion and HARD REJECT.
```

## Verification

```bash
# venv symlinked into worktree by delegate.py
grep -n 'IMPLEMENTATION SHAPE\|obligation_implementation_audit\|MUST.*activities.yaml' scripts/build/phases/linear-write.md
git diff --stat main
git diff --name-only main
.venv/bin/python -m pre_commit run --files scripts/build/phases/linear-write.md
```

Quote raw outputs in PR body.

## Commit + PR

Conventional commit + PR title referencing #2105. NO auto-merge.

## Out of scope

- Do NOT change `scripts/audit/wiki_coverage_gate.py` — gate logic is correct; prompt needs to match it.
- Do NOT touch `<implementation_map>` block (PR #2094 owns that).
- Do NOT touch `<bad_form_audit>` (PR #2095 owns that).
- Single file change only.

## Anti-fabrication

Quote raw grep/git diff/pre-commit outputs. NO menus or alternatives. If the existing line text doesn't match exactly, STOP and report what you found.
