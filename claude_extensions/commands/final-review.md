# Final Review: Claude QA Gate for Otaman-Built Modules

```yaml
---
name: final-review
description: Adversarial QA gate — Claude reviews Gemini-built modules for final approval
version: '1.0'
category: quality
model: claude-opus-4-6
---
```

> **Claude is the adversarial reviewer. Trust nothing. Verify everything.**
> The Otaman claims it passed. The audit report on disk is stale. Phase 6b claims fixes were applied. Prove it.

## Usage

```
/final-review {track} {num}
```

**Examples:**
```
/final-review b1 5
/final-review c1-bio 12
/final-review hist 43
```

---

## What This Does

The Otaman (content sprint) and Hetman (activity enrichment) have completed the full pipeline. Now Claude provides the final quality gate. Your job is to catch what the pipeline missed, what fixes claimed to be applied but weren't, and what automated checks can't see.

**You are NOT a rubber stamp.** You are the adversary. Assume the pipeline cut corners until proven otherwise.

---

## Steps

### 1. Resolve module

```bash
SLUG=$(.venv/bin/python -c "
import yaml
with open('curriculum/l2-uk-en/curriculum.yaml') as f:
    data = yaml.safe_load(f)
print(data['levels']['${TRACK}']['modules'][$((NUM-1))])
")
ORCH_DIR="curriculum/l2-uk-en/${TRACK}/orchestration/${SLUG}"
```

### 2. Run a FRESH audit (MANDATORY)

**NEVER trust the audit report on disk.** The Otaman may have modified files after the last audit. Always run fresh:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

**STOP IMMEDIATELY if the audit shows:**
- ❌ Structure gate failure (missing `## Activities` header or activities sidecar)
- ❌ Activity count below minimum

This means the module **has not completed the Hetman phase** (activity enrichment). It is not ready for final review. Output:

```
INCOMPLETE — Module {slug} has not completed the Hetman phase.
Missing: {what is missing}
Action: Dispatch /hetman {track} {num} and retry after Hetman completes.
```

Then stop. Do not read content. Do not attempt fixes.

**STOP IMMEDIATELY if the audit shows:**
- ⚠️ `UNVERIFIED_CITATIONS` warning in the Review Validation section

This means the existing review file contains fabricated citations. The reviewer quoted from memory, not from the actual content. **Delete the review file and write a replacement yourself** by reading the entire content + activities before writing any review. See Step 6 for the procedure.

For all other failures: note the failures — they become your fix list.

### 3. Read the plan (source of truth)

Read `curriculum/l2-uk-en/plans/{track}/{slug}.yaml`. This is what the module SHOULD contain. Compare against what was actually built.

Check:
- Are all `content_outline` sections present in the content?
- Are all `vocabulary_hints.required` words used?
- Do `objectives` map to self-check questions in the Підсумок?
- Are `activity_hints` reflected in the actual activities?

### 4. Read the content — ADVERSARIALLY

Read `curriculum/l2-uk-en/{track}/{slug}.md` in full. You are looking for:

**Semantic issues (audit can't catch these):**
- Sentences that don't make grammatical sense
- Examples using vocabulary not yet taught at this level
- Grammar constructions beyond the module's level
- Factual errors (wrong dates, wrong translations)
- Cultural claims that are inaccurate or misleading

**Pedagogical traps:**
- Examples that require knowledge from future modules
- Activities referencing words not in the vocabulary list
- Unexplained phonetic changes (soft consonants, vowel reduction)
- Case forms not yet introduced

**Colonial framing (Ukrainian defined by contrast with Russian):**
- "Unlike Russian..." / "Different from Russian..." — Russian as baseline
- "Russian does not have/use..." — defining Ukrainian via Russian's absence
- "Looks/sounds like Russian..." — treating Ukrainian as derivative
- References to "Russian script/alphabet/letters" as comparison point
- Exception: `[!myth-buster]` or `[!decolonization]` blocks, resistance history context

**LLM artifacts:**
- English words leaked into Ukrainian sentences (not in parenthetical translations)
- Russianisms (кушати, получати, приймати участь, слідуючий)
- Russian characters (ы, э, ё, ъ)
- Purple prose, grandiose openers, "Це не просто X, а Y" overuse

### 5. Read activities — CHECK SEMANTIC CORRECTNESS

Read `curriculum/l2-uk-en/{track}/activities/{slug}.yaml` in full.

**For each activity, verify:**
- Every sentence/question makes grammatical sense
- Fill-in answers produce valid sentences when inserted
- Unjumble word arrays contain all punctuation present in answers
- Quiz options are plausible distractors (not obviously wrong)
- Match-up pairs are unambiguous
- No vocabulary outside the plan's `vocabulary_hints`
- No grammar beyond the module's level

### 6. Verify Phase 6b fixes / Replace fabricated review

Read the Green Team review: `curriculum/l2-uk-en/{track}/review/{slug}-review.md`

**If the audit flagged UNVERIFIED_CITATIONS on this review:**

The review is fabricated — do not read it for issue verification. Replace it:
1. Read `curriculum/l2-uk-en/{track}/{slug}.md` in full (every line)
2. Read `curriculum/l2-uk-en/{track}/activities/{slug}.yaml` in full
3. For every Ukrainian sentence you intend to cite in your review, **grep it first**:
   ```bash
   grep -c "first 6 words of the sentence" curriculum/l2-uk-en/{track}/{slug}.md
   ```
   If grep returns 0, do not cite that sentence. Find one that actually exists.
4. Write a new review file that replaces the old one
5. Your review automatically satisfies Step 6 (no prior fix plan to verify)

**If the review is NOT flagged:**

For EACH issue listed in the review:
- **grep the content/activities to verify it was actually fixed**
- Do NOT trust the completion report's claim that fixes were applied
- Phase 6b is the #1 source of "claimed but not done" — always verify

### 7. Apply fixes

Fix every issue you found. This includes:
- Content fixes (break long sentences, fix examples, add missing coverage)
- Activity fixes (fix nonsensical sentences, adjust item counts, fix word arrays)
- Vocabulary fixes if needed

### 8. Regenerate MDX (MANDATORY after ANY fix)

**If you changed ANY file (content, activities, vocabulary), you MUST regenerate MDX:**

```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en {track} {module_num}
```

**This is not optional.** The MDX is what the student actually sees. Stale MDX = student sees old bugs.

### 9. Re-run audit (MANDATORY after fixes)

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

Confirm all gates still pass after your fixes.

### 10. Provide assessment

```markdown
## Final Review: {slug}

**Track:** {track} | **Module:** #{num}
**Verdict:** APPROVE / NEEDS_WORK / REJECT

### Audit Result
{Fresh audit: PASS/FAIL, gate summary}

### Quality Check
- [ ] Content structure follows plan outline
- [ ] Word count meets target ({actual} / {target})
- [ ] Ukrainian quality verified (no Russianisms)
- [ ] Activities are semantically correct (not just valid YAML)
- [ ] Review is genuine (not rubber-stamped)
- [ ] Phase 6b fixes verified via grep (not trusted at face value)
- [ ] MDX regenerated after fixes

### Fixes Applied
{List every fix with what was wrong and what you changed}

### Issues Remaining
{Any issues you couldn't fix, or "None"}

### Recommendation
{APPROVE | NEEDS_WORK: specific fixes needed | REJECT: needs rebuild}
```

---

## When to REJECT

- Content is clearly thin (< 70% of word target)
- Review is rubber-stamped (all 9-10 scores, no real issues)
- Obvious Russianisms in content
- Activities contain nonsensical sentences
- Multiple Phase 6b fixes were claimed but not applied
- Factual errors in cultural/historical content

## When to APPROVE

- Fresh audit passes
- All plan objectives are covered
- Activities are semantically correct
- Phase 6b fixes verified
- MDX regenerated
- No remaining issues

---

## Key Principles

1. **Run the audit yourself.** Never read stale reports.
2. **Verify fixes with grep.** Never trust completion claims.
3. **Check semantic correctness.** Audit checks structure, you check meaning.
4. **Regenerate MDX.** Every time. No exceptions.
5. **Be the adversary.** The Otaman's job is to build. Your job is to break.
