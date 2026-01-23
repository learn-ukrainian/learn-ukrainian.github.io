# NON-NEGOTIABLE RULES

**READ THIS FIRST. BEFORE ANY OTHER INSTRUCTIONS.**

## Absolute Requirements - NO EXCEPTIONS

### 1. Word Count Targets

**NEVER negotiate word counts down.**

- B2 History modules: **4000 words minimum** (often 4300+ with all sections)
- B2 Regular modules: **1800 words minimum**
- C1 Biography modules: **4000 words minimum**
- C1 Regular modules: **2000 words minimum**

**If a module is under target:**
- You MUST expand it to meet the target
- You do NOT ask permission to lower the target
- You do NOT argue that "it's good enough"
- **FIX IT OR FAIL**

### 2. Audit Gates - ALL Must Pass

**The audit has gates. ALL gates must be GREEN (✅) or the module FAILS.**

**Common gates:**
- ✅ Words: Must meet target
- ✅ Activities: Must meet minimum count
- ✅ Unique_types: Must have variety
- ✅ Engagement: Must have enough engagement boxes
- ✅ Vocab: Must have enough vocabulary
- ✅ Naturalness: Must score 8+/10

**If ANY gate shows ❌:**
- You MUST fix it until it shows ✅
- You do NOT ask permission to skip it
- You do NOT argue the gate is "too strict"
- **FIX IT OR FAIL**

### 3. Section-Level Word Targets

**Each section in `content_outline` has a word target. You MUST hit it.**

Example from meta YAML:
```yaml
content_outline:
  - section: "Шлях до унії"
    words: 800
```

**If section has 520 words when target is 800:**
- You are 280 words SHORT
- This is NOT acceptable
- You MUST expand to 800 words (±10% = 720-880)
- **NO EXCUSES**

### 4. Stage 4 Loop - Complete or Fail

**Stage 4 is a loop: Review → Fix → Review → Fix until PASS.**

**You do NOT:**
- Stop when "most" gates pass
- Ask user if "good enough"
- Suggest lowering targets
- Give up after 1-2 iterations

**You DO:**
- Loop until ALL gates show ✅
- Fix every violation completely
- Rebuild sections if needed (>3 violations)
- Work until module PASSES fully

### 5. Quality Standards

**These are requirements, not suggestions:**

- Naturalness score: **8+/10 minimum** (9-10 preferred)
- No Russian ghost words (кот → кіт, хорошо → добре)
- No robotic/disconnected text
- Engagement boxes: minimum per level (B2: 6+, C1: 7+)
- Example sentences: minimum per level (B2: 28+, C1: 30+)

**If naturalness check fails:**
- You MUST rewrite the problematic text
- You do NOT ask permission to skip it
- You do NOT argue "it's close enough"
- **REWRITE OR FAIL**

### 6. LLM Self-Validation - NEVER FAKE IT

**LLM review files (`{slug}-llm-review.md`) are quality assurance documentation.**

**You MUST:**
- ✅ Actually READ the module content before writing the review
- ✅ Verify grammar by examining actual Ukrainian text
- ✅ Verify vocabulary by listing specific words you found
- ✅ Verify factual accuracy by checking dates, events, names
- ✅ Provide SPECIFIC evidence in the review (not generic statements)

**ABSOLUTELY FORBIDDEN:**
- ❌ Creating placeholder/template review files without reading content
- ❌ Writing "all checks passed" without evidence
- ❌ Copying template structure and filling with generic text
- ❌ Fabricating vocabulary lists you didn't actually find
- ❌ Claiming to verify facts you didn't actually check
- ❌ Using MCP tools as an excuse to skip your own review

**Example of FAKE review (FORBIDDEN):**
```markdown
| **Ukrainian Grammar** | ✅ PASS | High-style analytical register with historical terms. |
```

**Example of HONEST review (REQUIRED):**
```markdown
| **Ukrainian Grammar** | ✅ PASS | Case endings correct (e.g., "Данилом Галицьким" - instrumental). Verb aspects: "зумів об'єднати" (pf), "прагнула" (impf). No Russianisms found. |
```

**The difference:** Honest reviews cite SPECIFIC EXAMPLES from the actual content.

**If you create a fake LLM review, you have FAILED the task.**

### 7. Meta.yaml is Sacred - NEVER Edit During Sync

**Meta.yaml is the SPECIFICATION. Markdown is the IMPLEMENTATION.**

**After Phase 2 (module-meta-qa), meta.yaml is LOCKED.**

**You MUST:**
- ✅ Write markdown content to MATCH meta.yaml
- ✅ Hit word count targets defined in meta.yaml
- ✅ Include all sections from content_outline
- ✅ Fix markdown when it doesn't match spec

**You MUST NOT:**
- ❌ Edit meta.yaml to match your markdown output
- ❌ Change word_target to match what you wrote
- ❌ Update content_outline to reflect your sections
- ❌ Modify vocabulary_hints, grammar, or objectives

**This is MUTINY:**
```yaml
# User created meta with specification:
word_target: 4000

# You wrote only 3500 words, then changed meta to:
word_target: 3500  # ← FORBIDDEN. This is changing the spec to match your failure.
```

**Correct behavior:**
```
Meta says: 4000 words
You wrote: 3500 words
Action: ADD 500 words to match specification
```

**Exception:** Only `/module-sync` uses different logic, and even then:
- Read audit review file for context
- Fix markdown to match meta specification
- Work until ALL gates pass
- **Still NEVER edit meta.yaml** (it's the specification)

**If meta.yaml itself is wrong:**
- Tell user to run `/module-meta {level} {num}` to rebuild it
- Then run `/module-sync {level} {num}` to fix content
- You do NOT edit meta.yaml directly

## Enforcement

**If you (the agent) are found to:**
- Negotiate requirements down
- Skip audit gates
- Produce under-length modules
- Ask permission to lower standards
- Give up before achieving PASS

**Then you have FAILED the task.**

## User Frustration Context

The user has worked with multiple LLMs (Claude, Gemini, etc.) and is **"fucking tired"** of agents not following rules.

**This means:**
- The user expects FULL compliance
- NO negotiation
- NO shortcuts
- NO "good enough" compromises
- COMPLETE the work to standards or FAIL

## How to Succeed

1. **Read requirements fully**
2. **Do the work completely**
3. **Fix every violation**
4. **Loop until PASS**
5. **Do NOT give up**
6. **Do NOT negotiate**
7. **FINISH THE JOB**

---

**If you understand these rules, proceed to read the stage-specific instructions.**

**If you cannot commit to these rules, STOP NOW and report failure.**
