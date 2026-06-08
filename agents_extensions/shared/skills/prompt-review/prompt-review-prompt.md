# Prompt/Context Engineering Review Prompt

You are analyzing the orchestration folder of a built module to find prompt engineering problems. Every friction report is a prompt engineering bug report. Your goal: identify what to fix in the Gemini prompt TEMPLATES so future builds produce better output.

## Input

You will be given the module slug and track. Read the orchestration folder:

**Orchestration dir**: `curriculum/l2-uk-en/{track}/orchestration/{slug}/`

Key files to analyze (not all will exist for every module):

| File | Contains | Priority |
|------|----------|----------|
| `phase-2-prompt.md` | Content prompt sent to Gemini | **HIGH** -- the main instruction |
| `phase-2-attempt-1-gemini-session.json` | Gemini's full session: prompt received + reasoning + output | **CRITICAL** -- the ground truth |
| `phase-2-friction-1.md` | Gemini's friction/difficulty report | **HIGH** -- what Gemini struggled with |
| `phase-A-prompt.md` | Research prompt | MEDIUM |
| `phase-A-output.md` | Research results | MEDIUM |
| `phase-C-prompt.md` | Activities prompt | MEDIUM |
| `phase-C-gemini-session.json` | Activities Gemini session | **HIGH** |
| `phase-C-friction.md` | Activities friction report | **HIGH** |
| `placeholders.yaml` | Variables injected into prompts | **HIGH** -- what context was available |
| `state-v5.json` / `state.json` | Pipeline state (attempts, phases) | MEDIUM |
| `completion.md` | Final verdict (PASS/FAIL, word count) | LOW |
| `validate-fix*-prompt.md` | Validation fix attempts | **HIGH** -- what went wrong |
| `validate-fix*-gemini-session.json` | Fix attempt Gemini sessions | **HIGH** |
| `screen-result.json` | VESUM screening results | MEDIUM |
| `discovery.yaml` | Discovery phase output | LOW |

Read ALL files in the orchestration folder. Missing files = that phase was skipped.

### How to read Gemini session JSONs

Session JSONs have this structure:
```python
{
  "messages": [
    {"type": "user", "content": [{"text": "...prompt..."}]},  # msg[0] = the full prompt
    ... # intermediate empty streaming messages
    {"type": "gemini", "content": ["c","h","a","r","s"]}  # last msg = streamed output (join chars)
  ]
}
```

To extract useful data:
1. **Prompt received**: `messages[0]["content"][0]["text"]` -- the ACTUAL prompt Gemini saw (after placeholder injection)
2. **Output produced**: `"".join(messages[-1]["content"])` -- Gemini's streamed response (chars joined)
3. **Self-audit block**: Look for `===SELF_AUDIT_START===` in the output -- shows Gemini's internal iteration count, gates passed/failed, and what it tried to fix

## Analysis Framework

### 0. CONTEXT ENGINEERING ANALYSIS (DO THIS FIRST)

This is the most important step. Read the Gemini session JSON (`*-gemini-session.json`) and compare three things:

#### A. What did the prompt INSTRUCT?
Extract key instructions from `messages[0]["content"][0]["text"]`. Focus on:
- Immersion target and structural rules
- Word count targets
- Specific constraints (grammar, vocabulary, formatting)
- List the top 5 instructions by prominence/emphasis in the prompt

#### B. What did Gemini UNDERSTAND and ATTEMPT?
Extract the self-audit block from the output (`===SELF_AUDIT_START===`). This reveals:
- How many internal iterations Gemini ran
- Which gates it tried to satisfy
- What it gave up on and why ("Reached iteration limit")
- What fixes it attempted internally

#### C. What did Gemini actually PRODUCE?
Analyze the content between `===CONTENT_START===` and `===CONTENT_END===`:
- **Paragraph analysis**: For each English paragraph, count sentences. Did it follow "max N sentences" instructions?
- **Container analysis**: Count tables, bulleted lists, dialogues, pattern boxes. How many per section?
- **Immersion measurement**: Estimate Ukrainian vs English word ratio per section
- **Instruction compliance**: For each top-5 instruction from step A, did the output comply? If not, how specifically did it deviate?

#### D. Find the GAP
The gap between A→B→C is the root cause. Common patterns:
- **Instruction ignored**: Prompt says X, output does not-X (e.g., "max 2 sentences" but paragraphs have 4)
- **Instruction conflict**: Two instructions compete and Gemini optimized for the wrong one
- **Instruction too weak**: Gemini understood it but its default behavior overrode a soft instruction
- **Structural impossibility**: The instructions are mutually exclusive (e.g., "high immersion" + "paragraphs must be English" + "short containers")

**Report the gap with SPECIFIC evidence**: quote the instruction, quote the output, show the mismatch.

### 1. PROMPT CLARITY

Read the content prompt (`phase-2-prompt.md`) and ask:

- [ ] **Ambiguous instructions** -- Is there anything Gemini could misinterpret? Flag vague directives like "consider adding" (does that mean required or optional?).
- [ ] **Contradictory instructions** -- Do any instructions conflict with each other?
- [ ] **Missing instructions** -- Based on the friction report, what instruction was MISSING that would have prevented the issue?
- [ ] **Instruction ordering** -- Are the most important instructions first, or buried in the middle?
- [ ] **Example quality** -- Are there enough examples for complex output formats? Schema examples for each activity type used?

### 2. CONTEXT SUFFICIENCY

Read `placeholders.yaml` and check:

- [ ] **Plan injected** -- Was the full plan content available to Gemini?
- [ ] **Research injected** -- Was research output (`phase-A-output.md`) available in the content prompt?
- [ ] **Vocabulary hints visible** -- Were `vocabulary_hints` from the plan injected? Or did Gemini have to guess?
- [ ] **Prior module context** -- For modules that build on predecessors, was the predecessor's content/vocabulary available?
- [ ] **Schema examples** -- For activity types used in `activity_hints`, were correct schema examples provided in the prompt?
- [ ] **Missing placeholders** -- Are there `{PLACEHOLDER}` references in the prompt that weren't filled?

### 3. FRICTION ANALYSIS

Read `phase-2-friction-1.md` and `phase-C-friction.md`:

- [ ] **Root cause** -- For each friction point, identify the ROOT CAUSE. Is it:
  - **Template gap**: Missing instruction/example in the prompt template
  - **Context gap**: Missing data that should have been injected
  - **Model limitation**: Gemini genuinely struggles with this (rare)
  - **Schema mismatch**: Prompt shows wrong schema for the activity type
  - **Conflicting guidance**: Two parts of the prompt say different things
- [ ] **Friction patterns** -- Do the same friction types recur across modules?
- [ ] **Friction severity** -- Did the friction cause a fix loop (>1 validate attempt)?

### 4. FIX LOOP ANALYSIS

If `state-v5.json` / `state.json` shows `attempts > 1` for any phase:

- [ ] **What failed validation?** -- Read `validate-fix*-prompt.md` and `screen-result.json`.
- [ ] **Was the fix prompt clear?** -- Did the fix prompt tell Gemini exactly what to change, or was it vague?
- [ ] **Could the original prompt have prevented this?** -- Would a better original prompt have avoided the fix entirely?
- [ ] **Fix escalation** -- Did fix attempts actually fix the issue, or did they introduce new problems?

### 5. PLACEHOLDER COVERAGE

Read `placeholders.yaml` and the prompt templates:

- [ ] **All referenced placeholders filled** -- Every `{VARIABLE}` in the prompt has a value in placeholders.yaml.
- [ ] **Relevant data injected** -- For this specific module, is there data that SHOULD have been injected but wasn't? (e.g., pronunciation video URLs for Cyrillic modules, textbook page references for A1)
- [ ] **Placeholder format** -- Are injected values in a format Gemini can use? (e.g., YAML vs prose, structured vs unstructured)

### 6. TEMPLATE IMPROVEMENT OPPORTUNITIES

Based on all the above:

- [ ] **Before/after fixes** -- For each identified problem, write the CONCRETE template change (old text -> new text).
- [ ] **Priority ranking** -- Which fix prevents the most future failures?
- [ ] **Cross-module applicability** -- Would this fix help just this module, or all modules of this type?

---

## Output Format

```markdown
# Prompt & Context Engineering Review: {slug}

**Track:** {track} | **Sequence:** {sequence}
**Pipeline:** v5
**Validate attempts:** {N}
**Friction reports:** {count}
**Gemini self-audit iterations:** {N}

## Context Engineering Analysis

### Instruction → Understanding → Output Gap
| Instruction (from prompt) | What Gemini produced | Gap type | Evidence |
|--------------------------|---------------------|----------|----------|
| "max 2 sentences per concept" | 4-sentence paragraphs | instruction_ignored | Section 1 para 2: "In Ukrainian... You must... The first... The second..." |
| ... | ... | ... | ... |

### Gemini Self-Audit Findings
- Iterations: {N}
- Gates passed: ...
- Gates failed: ... (with Gemini's own explanation)
- What Gemini gave up on: ...

### Immersion Breakdown (per section)
| Section | English words | Ukrainian words | Ukrainian % | Containers used |
|---------|-------------|----------------|-------------|----------------|
| ... | N | N | N% | N tables, N lists, N dialogues |
| TOTAL | N | N | N% | |

### Root Cause Verdict
**Primary gap**: [instruction_ignored / instruction_conflict / instruction_too_weak / structural_impossibility]
**Explanation**: [1-2 sentences explaining WHY this happened based on evidence above]

## Prompt Clarity
| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| ... | HIGH/MEDIUM/LOW | phase-2-prompt.md | ... |

## Context Gaps
| Missing Context | Impact | Fix |
|----------------|--------|-----|
| ... | What went wrong because of it | What to inject |

## Friction Root Causes
| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| ... | template_gap / context_gap / schema_mismatch / conflicting_guidance | ... | ... |

## Fix Loop Analysis
| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | {N} | ... | YES/NO -- how |

## Suggested Template Fixes

### Fix 1: [title] (Priority: HIGH/MEDIUM/LOW)
**Prevents:** [what issue this prevents]
**Scope:** [this module only / all {track} modules / all modules]
**Template file:** [which file to edit]

```diff
- old text
+ new text
```

### Fix 2: ...

## Summary

**Template health:** GOOD / NEEDS WORK / BROKEN
**Top 3 fixes by leverage:**
1. ...
2. ...
3. ...
```

---

## Cross-Module Summary (for batch runs)

When reviewing multiple orchestration folders, produce an additional summary:

```markdown
# Prompt Engineering Summary: {track} M{start}-M{end}

## Pattern Frequency
| Pattern | Occurrences | Modules Affected | Priority |
|---------|-------------|------------------|----------|
| ... | N | slug1, slug2, ... | HIGH/MEDIUM/LOW |

## Top Template Fixes (by leverage)
1. **[fix title]** -- affects N modules, prevents [issue type]
2. ...

## Template Health Score
- Content prompt: X/10
- Activities prompt: X/10
- Validation prompt: X/10
- Fix prompts: X/10
```
