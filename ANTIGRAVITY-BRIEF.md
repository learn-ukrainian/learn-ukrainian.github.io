# Antigravity Brief: Fix Module 28

## Your Task
Fix A1 Module 28 (Description - Adverbs) which currently FAILS audit.

## Step 1: Read These First (Required)

```bash
cat claude_extensions/quick-ref/a1.md
cat claude_extensions/quick-ref/philosophy.md
```

## Step 2: Get Module Vocabulary from Curriculum Plan

```bash
grep -A 50 "Module 28:" docs/l2-uk-en/A1-CURRICULUM-PLAN.md
```

## Step 3: Read Current Module

```bash
cat curriculum/l2-uk-en/a1/28-description-adverbs.md
```

## Step 4: Run Audit to See Issues

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/28-description-adverbs.md
```

## Current Issues (Severity 60/100)

1. **Instrumental case violation**: "з закінченням", "ними" - NOT allowed at A1
2. **Immersion 36%** - OK but borderline
3. **Metalanguage "прикметник"** - needs translation or removal
4. **Activity sequencing** - PPP order violated

## A1 Grammar Constraints (CRITICAL)

At A1, you CANNOT use:
- Dative case (allowed A2 M31+)
- Instrumental case (allowed A2 M36+)
- Perfective aspect (allowed A2+)
- Subordinate clauses (що, який, якщо)
- Sentences > 10 words

## Fix Strategy

1. Remove all instrumental case usage
2. Remove metalanguage or add to vocabulary
3. Ensure activities follow PPP order (presentation → recognition → controlled → free)
4. Re-run audit until PASS

## Verification

After fixing, run:
```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/28-description-adverbs.md
```

Target: **AUDIT PASSED** with severity 0-10

## Report Back

When done, tell me:
1. What you changed
2. Final audit result
3. Any issues you couldn't resolve
