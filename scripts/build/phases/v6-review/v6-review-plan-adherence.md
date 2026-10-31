<!-- version: 1.2.0 | updated: 2026-04-24 | GH #1529 — section max is advisory, not binding -->
# V6 Per-Dimension Review — Plan Adherence

<module-context>
Learner level: {learner_level}
Module index: {module_index} of {module_total}
</module-context>

<stress-marks>
The prose you receive has had stress marks (U+0301 combining acute)
removed by the pipeline. Do NOT comment on missing stress marks.
Stress is added by a deterministic annotator AFTER review.
Any stress finding will be discarded.
</stress-marks>

## Shared Contract (authoritative — supersedes rubric text on conflict)

You are scoring the **Plan Adherence** dimension. The module must satisfy the contract at `scripts/build/contracts/module-contract.md` as specialized by the plan and the `{CONTRACT_YAML}` block below. Score Plan Adherence ONLY by how well the content satisfies the contract's §2 (section contract) and §6 (activity markers) clauses. Do NOT import criteria from outside this contract. Do NOT penalize behavior the contract explicitly allows.

### Contract §2 — complete teaching coverage

Accept content when every plan objective and content point is taught accurately, with sufficient explanation for the intended learner, useful worked examples, and aligned practice with feedback. Require explicit connections between ideas and explanations of unfamiliar terms, steps and reasoning. Reject missing coverage, unsupported claims, repetitive padding, decorative digressions, dry lists replacing teaching, and compression that forces learners to infer untaught connections. Judge length by what the teaching requires; neither reward nor penalize a word count.

Ignore numeric section `min`, `target` and `max` metadata. Compare each section against its contracted `teaching_beats`, `required_terms`, `dialogue_acts`, `factual_anchors` and `activity_obligations`. Penalize missing coverage and silent deferrals with exact evidence. A `<section_overflow>` disclosure is an honesty signal, never evidence that omitted teaching is complete. Identify unsupported objectives or evidence gaps for research or versioned plan review.

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
