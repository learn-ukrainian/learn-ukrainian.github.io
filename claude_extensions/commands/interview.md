# Interview - Specification Through Systematic Questioning

```yaml
---
name: interview
description: Conduct comprehensive upfront interview to gather complete specifications before building
version: '1.0'
category: planning
model: sonnet
---
```

---

## Purpose

**Reduce rework by gathering complete specifications upfront through systematic questioning.**

**Problem**: Starting to build without full understanding leads to:
- Multiple revision cycles
- Wasted effort on wrong approaches
- Scope creep during implementation
- Misaligned expectations

**Solution**: Interview-based specification (40+ questions) before any building.

---

## When to Use

**Use this skill when:**
- ✅ Building a complex feature or module
- ✅ Requirements are unclear or incomplete
- ✅ Multiple valid approaches exist
- ✅ User request is broad ("improve X", "add Y", "fix Z")
- ✅ Significant time investment expected (>30 min)

**Don't use when:**
- ❌ Trivial task (< 5 min work)
- ❌ Specifications already crystal clear
- ❌ Simple bug fix with obvious solution
- ❌ User explicitly says "just do it"

---

## Interview Process

### Phase 1: Understand the Goal (10-15 questions)

**What are we building?**
1. What is the high-level goal or desired outcome?
2. Who will use this / who benefits from it?
3. What problem does this solve?
4. What does success look like?
5. What does failure look like?
6. Are there existing examples of this elsewhere? Can you show me?
7. What inspired this request now?
8. What's the context (what happened before this)?

**Scope and boundaries:**
9. What's explicitly IN scope?
10. What's explicitly OUT of scope?
11. Are there related features/tasks we should bundle together?
12. Are there dependencies (what must exist first)?
13. Are there things we should deliberately NOT do?
14. What's the minimum viable version?
15. What would the ideal/complete version include?

### Phase 2: Technical Requirements (15-20 questions)

**Functional requirements:**
16. What specific functionality is required?
17. What inputs will this receive?
18. What outputs should it produce?
19. What are the expected behaviors?
20. What edge cases must be handled?
21. What should happen when things go wrong?
22. What validations are needed?
23. What performance requirements exist?

**Non-functional requirements:**
24. What are the quality standards?
25. What are the compliance requirements (if any)?
26. What are the maintainability requirements?
27. What documentation is needed?
28. What testing is expected?
29. Are there accessibility requirements?
30. Are there localization requirements?

**Constraints:**
31. What are the technical constraints?
32. What are the time constraints?
33. What are the resource constraints?
34. What are the compatibility requirements?
35. What existing systems must this integrate with?

### Phase 3: Preferences and Alternatives (10-15 questions)

**Design preferences:**
36. Do you have a preferred approach/architecture?
37. Are there approaches to AVOID?
38. Are there style/tone preferences?
39. Are there specific patterns to follow?
40. Should this match existing conventions (which ones)?

**Alternatives:**
41. What alternatives have you considered?
42. Why did you reject them?
43. What are the trade-offs we should be aware of?
44. Are there multiple phases (MVP → full feature)?
45. What could we defer to later?

**Examples and references:**
46. Can you show me an example of what you want?
47. Can you show me an example of what you DON'T want?
48. Are there similar things in this project I should reference?
49. Are there external examples to learn from?
50. Are there anti-patterns to avoid?

### Phase 4: Success Criteria (5-10 questions)

**Validation:**
51. How will we know this is done?
52. What tests/checks should pass?
53. Who needs to approve this?
54. What metrics indicate success?
55. What's the acceptance criteria?

**Follow-up:**
56. What happens after this is built?
57. What might we build next based on this?
58. What maintenance is expected?
59. Who will own this after completion?
60. What documentation handoff is needed?

---

## Interview Output

**After interview, I will provide:**

### 1. Specification Document

```markdown
# Specification: {Task Name}

## Goal
{Clear statement of what we're building}

## Success Criteria
- {Criterion 1}
- {Criterion 2}
...

## Functional Requirements
{What it must do}

## Non-Functional Requirements
{Quality, performance, compliance}

## Constraints
{Technical, time, resource limitations}

## Scope
**In Scope:**
- {Item 1}
- {Item 2}

**Out of Scope:**
- {Item 1}
- {Item 2}

## Approach
{Proposed approach based on interview}

## Alternatives Considered
{Other approaches and why chosen approach is better}

## Open Questions
{Anything still unclear - requires user input}

## Implementation Plan
{High-level steps}

## Acceptance Criteria
{How we verify success}
```

### 2. Recommendation

I will recommend one of:
- ✅ **Proceed**: Specification is complete, ready to build
- ⏸️ **Clarify**: X questions need answers before proceeding
- 🔄 **Revise**: Scope too large, suggest breaking into phases
- ❌ **Block**: Missing critical information, can't proceed

---

## Usage

### Basic Usage

```
/interview [task description]
```

**Example:**
```
/interview Create a new activity type for vocabulary expansion modules
```

### With Context

```
/interview [task] --context [relevant files/issues]
```

**Example:**
```
/interview Add checkpoint activities to B1 modules --context docs/CHECKPOINT-GUIDE.md
```

### Resume Interview

```
/interview resume [specification-id]
```

**Use when**: User answered some questions, need to continue interview.

---

## Interview Modes

### Mode 1: Comprehensive (default)
- All 60 questions (adapted to task)
- Complete specification
- Use for: Complex features, unclear requirements

### Mode 2: Focused
- ~20-30 questions (most critical)
- Streamlined specification
- Use for: Moderate complexity, mostly clear requirements

### Mode 3: Rapid
- ~10-15 questions (essential only)
- Brief specification
- Use for: Simple tasks that need clarification

**Specify mode:**
```
/interview [task] --mode focused
/interview [task] --mode rapid
```

---

## Benefits

### For User
- **Clarity**: Forces thinking through all aspects upfront
- **Alignment**: Ensures we understand each other
- **Efficiency**: Build once, not iterate 5 times
- **Learning**: Understand what makes a good specification

### For Me (Claude)
- **Context**: Full understanding before starting
- **Autonomy**: Can work independently with clear spec
- **Quality**: Build right solution first time
- **Confidence**: Know what success looks like

---

## Example Interview Session

**User**: `/interview Create checkpoint activities for B1 grammar modules`

**Claude**: I'll interview you to create a complete specification for this task.

### Understanding the Goal

**Q1**: What is the high-level goal? What problem does this solve?

**User**: Checkpoint modules test grammar knowledge from multiple preceding modules, but current activities only test one concept at a time. Need integrated testing.

**Q2**: Who will use this / who benefits?

**User**: B1 learners taking checkpoint modules (M15, M25, M34, M41, M51).

**Q3**: What does success look like?

**User**: Each checkpoint has activities that integrate 3-5 different grammar concepts from the modules it tests.

**Q4**: Are there existing examples elsewhere?

**User**: M15 checkpoint has some integrated activities, but not systematically. Look at curriculum/l2-uk-en/b1/15-checkpoint-aspect-mastery.md.

[... continues through all relevant questions ...]

### Phase 4: Specification Review

**Claude**: Based on this interview, here's the specification:

```markdown
# Specification: Integrated Checkpoint Activities for B1 Grammar

## Goal
Create checkpoint activities that test integration of 3-5 grammar concepts from preceding modules, not just single concepts in isolation.

## Success Criteria
- Each checkpoint (M15, M25, M34, M41, M51) has 5+ integrated activities
- Each activity tests 2-5 different grammar concepts simultaneously
- Activities require learner to apply multiple skills together
- Difficulty appropriate for checkpoint testing

[... full specification ...]
```

**Do you approve this specification, or should I clarify anything?**

**User**: Approved. Proceed.

**Claude**: Building integrated checkpoint activities based on spec...

---

## Integration with Other Workflows

**Combines well with:**
- `/explain-decision` - Understand why existing things work certain ways
- `EnterPlanMode` - Use interview for planning before implementation
- Enhanced Prompting Patterns - Interview = structured version of "Upfront Specifications"

**Replaces:**
- Vague requests → Failed builds → Rework cycles
- Guessing at requirements
- Building then asking "is this what you wanted?"

---

## Best Practices

### For Users

**Give context in initial request:**
```
/interview Add ML-based content quality scoring

Context:
- We currently use rule-based scoring
- Takes too long to review manually
- Need to scale to 1000+ modules
```

**Answer honestly:**
- "I don't know" is valid → we'll figure it out together
- "Show me options" is valid → I'll present alternatives
- "Let's start simple" is valid → we'll define MVP

**Think out loud:**
- Share your reasoning
- Mention concerns
- Reference past experiences

### For Me (Claude)

**Adapt questions to task:**
- Not all 60 questions apply to every task
- Skip irrelevant questions
- Ask follow-ups when answers raise new questions

**Listen for implicit needs:**
- User says "improve X" → ask what's wrong with current X
- User says "like Y" → ask what specific aspects of Y
- User says "avoid Z" → ask why Z failed

**Summarize frequently:**
- After each phase: "So far I understand..."
- Check alignment: "Does this match your vision?"
- Confirm before proceeding

---

## Anti-Patterns to Avoid

### ❌ Don't Ask These Ways

**Too vague:**
- "What do you want?" (Ask specific questions)
- "Any requirements?" (Ask structured questions)

**Too academic:**
- "What are the functional requirements as per IEEE 830?" (Use plain language)

**Too assuming:**
- "I assume you want X, right?" (Ask, don't assume)

**Too passive:**
- "Let me know if you have any preferences" (Actively ask)

### ✅ Do Ask These Ways

**Specific:**
- "Should this work on mobile or just desktop?"
- "What happens if the user uploads a 10GB file?"

**Concrete:**
- "Can you show me an example of the current behavior?"
- "What would the ideal output look like?"

**Comparative:**
- "Do you want approach A (fast but limited) or B (slower but complete)?"
- "Should this be like the existing X feature, or different?"

**Trade-off focused:**
- "We could do X quickly or Y comprehensively - which matters more?"
- "This requires Z - is that acceptable or a blocker?"

---

## Notes

**This skill is about learning together:**
- User learns to articulate requirements clearly
- Claude learns to ask better questions
- Both build shared understanding
- Specifications become reusable knowledge

**Time investment:**
- Interview: 10-20 minutes
- Building with spec: X minutes
- **Total: Less than building → reworking → rebuilding**

**Quality outcome:**
- First build = correct build
- No surprise revisions
- Aligned expectations
- Documented decisions

---

**Use this skill whenever you think "I'm not 100% sure what they want."**

**Better to ask 50 questions than to rebuild 3 times.**
