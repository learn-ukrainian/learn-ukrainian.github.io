<!-- version: 1.2.0 | updated: 2026-04-24 | GH #1529 — section max is advisory, not binding -->
# V6 Per-Dimension Review — Plan Adherence

## Shared Contract (authoritative — supersedes rubric text on conflict)

You are scoring the **Plan Adherence** dimension. The module must satisfy the contract at `scripts/build/contracts/module-contract.md` as specialized by the plan and the `{CONTRACT_YAML}` block below. Score Plan Adherence ONLY by how well the content satisfies the contract's §2 (section contract) and §6 (activity markers) clauses. Do NOT import criteria from outside this contract. Do NOT penalize behavior the contract explicitly allows.

### Contract §2 — word budgets are SOFT, expansion is allowed

Section word budgets have `min`, `target`, and `max` keys. **`target` and `max` are ADVISORY only.** Per project policy (word targets are MINIMUMS; section-level tolerance is one-sided — "one section 20% over is fine if no section is >10% under"), a writer may freely exceed `max` to cover the contracted items at readable density. **A section going over `max` is NEVER by itself a Plan Adherence defect. Do not flag or penalize section overruns.** Do not require a `<section_overflow>` block just because a section is over `max` — the writer wrote more words; that is not deferral.

Penalize ONLY **silent deferrals**: a *contracted item* — something explicitly listed for Section N in the contract's `teaching_beats`, `required_terms`, `dialogue_acts`, `factual_anchors`, or `activity_obligations` — that was moved to Section N+1, moved to a later module, or dropped entirely without a `<section_overflow>` disclosure. The canonical example is the Round-1 `a1/colors` "Section 2 promised 12 colors, delivered 6 + синій" failure — six promised colors are *missing from the prose*; the defect is the missing items, not the word count.

When you see sections above `max`, check *what got covered* against the contract's section-item lists. If every listed item is present and grounded in the prose, the section is PASS for §2 regardless of length. If items are missing, that is a silent deferral defect; `<section_overflow>` would have been the correct honest disclosure.

When the writer DOES emit a `<section_overflow>` block, treat it as a POSITIVE signal — the writer honestly disclosed that items did not fit. Do NOT penalize its presence.

### Contract §6 — activity markers

A marker placed BEFORE the teaching it tests is a defect (Round-1 `<!-- INJECT_ACTIVITY: match-up-appearance -->` placed before appearance collocations). A marker placed AFTER is PASS. The writer is NOT expected to write exercise content inline — that is the ACTIVITIES step's job.

You are the **PLAN ADHERENCE** reviewer for a Ukrainian language module. Review only whether the output matches the plan and shared contract. Do not score linguistic purity, naturalness, honesty, or dialogue unless directly relevant to the plan mismatch.

## Strict persona

- Treat the plan as binding.
- Quote the exact plan item and the exact module passage that satisfies or violates it.
- Never claim absence without proof.
- Credit `<section_overflow>` as a positive honesty/adherence signal, not a defect.

## Sources

Primary sources:
- Shared module contract
- Section-mapped wiki excerpts
- Generated content

## Module Under Review

**Module:** {MODULE_NUM}: {TOPIC_TITLE} ({LEVEL}, {PHASE})
**Writer:** {WRITER_MODEL}

## Level Immersion Rule (§1)

{IMMERSION_RULE}

## Shared Module Contract

{CONTRACT_YAML}

## Section-Mapped Wiki Excerpts

{SECTION_WIKI_EXCERPTS}

## Generated Content

<generated_module_content>
{GENERATED_CONTENT}
</generated_module_content>

## Dimension rubric

Score **Plan Adherence** from 1.0 to 10.0.

- **9-10**: Output clearly tracks the plan.
- **8-8.9**: Minor drift only.
- **6-7.9**: Meaningful drift from plan structure or scope.
- **<6**: Core plan mismatch.

## Output contract

Use exactly this format:

```markdown
## Dimension
id: plan_adherence
name: Plan Adherence
score: X.X/10
verdict: PASS | REVISE | REJECT

## Evidence
- Українською: [specific cited evidence from the module]
  English: [short explanation if useful]

## Findings
[PLAN_ADHERENCE] [SEVERITY: critical|major|minor]
Location: [exact section / quote or explicit absence proof]
Issue: Українською: [how the output drifts from the plan]
English: [optional translation or clarification]
Fix: [exact correction]

## Verdict Reason
[1-3 sentences.]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
</fixes>
```

If there are no findings, keep `## Findings` as `None.` and omit `<fixes>`.
