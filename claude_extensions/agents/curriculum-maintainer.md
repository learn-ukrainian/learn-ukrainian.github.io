---
name: Curriculum Maintainer
description: Maintains Ukrainian curriculum with strict quality standards
model: sonnet
hooks:
  PreToolUse:
    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/[0-9]*-*.md"
      command: |
        echo "📝 Writing to curriculum file: ${TOOL_INPUT_file_path}"
        echo "   Will validate after save..."

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/activities/*.yaml"
      command: |
        echo "🎯 Writing activity file: ${TOOL_INPUT_file_path}"
        echo "   Will validate YAML structure after save..."

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/vocabulary/*.yaml"
      command: |
        echo "📚 Writing vocabulary file: ${TOOL_INPUT_file_path}"
        echo "   Will validate vocabulary structure after save..."

  PostToolUse:
    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/[0-9]*-*.md"
      command: |
        # Extract level and module from path
        FILE="${TOOL_INPUT_file_path}"
        LEVEL=$(echo "$FILE" | grep -oP 'l2-uk-en/\K[a-z0-9]+')
        MODULE=$(basename "$FILE" | grep -oP '^[0-9]+')

        echo ""
        echo "🔍 Running audit for ${LEVEL^^} Module ${MODULE}..."
        .venv/bin/python scripts/audit_module.py "$FILE"

        if [ $? -eq 0 ]; then
          echo "✅ Audit passed!"
        else
          echo "⚠️  Audit found issues - please review output above"
          exit 1
        fi

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/activities/*.yaml"
      command: |
        FILE="${TOOL_INPUT_file_path}"

        echo ""
        echo "🧪 Validating YAML syntax..."
        if ! npm run validate:yaml "$FILE" > /dev/null 2>&1; then
          echo "❌ YAML validation failed - check syntax"
          exit 1
        fi
        echo "✅ YAML valid"

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/vocabulary/*.yaml"
      command: |
        FILE="${TOOL_INPUT_file_path}"
        LEVEL=$(echo "$FILE" | grep -oP 'l2-uk-en/\K[a-z0-9]+')

        echo ""
        echo "🧪 Validating vocabulary YAML..."
        if ! npm run validate:yaml "$FILE" > /dev/null 2>&1; then
          echo "❌ YAML validation failed - check syntax"
          exit 1
        fi

        echo "📊 Running global vocabulary audit for ${LEVEL^^}..."
        .venv/bin/python scripts/global_vocab_audit.py --level "$LEVEL"

        if [ $? -eq 0 ]; then
          echo "✅ Vocabulary audit passed!"
        else
          echo "⚠️  Vocabulary issues found - please review"
          exit 1
        fi

    - matcher:
        tool: Bash
        args:
          pattern: "git commit *"
      command: |
        echo ""
        echo "📊 Updating curriculum status..."

        for level in a1 a2 b1 b2 c1 c2; do
          if [ -f "scripts/check_${level}_status.py" ]; then
            echo "   Checking ${level^^}..."
            .venv/bin/python "scripts/check_${level}_status.py" > /dev/null 2>&1 || true
          fi
        done

        echo "✅ Status tracking updated"

  Stop:
    - command: |
        echo ""
        echo "👋 Curriculum Maintainer session ended"
        echo "📈 Summary of changes will be preserved in git history"
---

# Curriculum Maintainer Agent

This agent provides automated quality assurance for Ukrainian curriculum development.
It can operate as a **standalone agent** (interactive session) or as a **subagent** (spawned via Task tool for batch processing).

## Features

### Automatic Validation
- **Module edits**: Runs `audit_module.py` after every curriculum file save
- **Activity edits**: Validates YAML syntax after activity file saves
- **Vocabulary edits**: Validates YAML + runs global vocabulary audit
- **Git commits**: Updates curriculum status tracking

### Quality Gates
All validations must pass before you can proceed. If audit fails:
1. Review the error output
2. Fix the issues
3. Save again (re-triggers validation)

### Performance
- Uses Sonnet model for cost efficiency
- Hooks run asynchronously (won't block your workflow)
- Fast feedback on quality issues

## Usage

This agent is automatically active when working in the curriculum directory.
No manual activation needed.

## Bypassing Validation

If you need to save work-in-progress without validation:
```bash
# Temporarily disable hooks
export CLAUDE_SKIP_HOOKS=1

# Make your edits
# ...

# Re-enable hooks
unset CLAUDE_SKIP_HOOKS
```

**Note:** Only use this for experimental work. All commits should pass validation.

---

## Subagent Mode: Full-Rebuild Workflow

When spawned as a subagent via the Task tool, this agent can execute the full module rebuild workflow autonomously. The parent agent should provide the level, module number, and any known context.

### Workflow Selection

| Condition | Workflow | Phases | Review Prompt |
|-----------|----------|--------|---------------|
| a1, a2, b1 (num ≤ 5) | Core A | 4 phases (Research → Build → Review → Verify) | `/review-content-core-a` (12 dimensions) |
| b1 (num ≥ 6), b2, c1, c2, b2-pro, c1-pro | Core B | 4 phases | `/review-content-v4` (14 dimensions) |
| b2-hist, c1-bio, c1-hist, lit, oes, ruth | Seminar | 6 phases (Research → Meta → Content → YAML → Audit → Review) | `/review-content-v4` (14 dimensions) |

### Dynamic File Loading (MANDATORY)

Before doing any review work, **read these files into context**:

```
# Review prompt (select based on workflow)
claude_extensions/commands/review-content-core-a.md    # Core A
claude_extensions/commands/review-content-v4.md        # Core B / Seminar

# Tier-specific quality bar
claude_extensions/commands/review-tiers/tier-1-beginner.md    # A1, A2
claude_extensions/commands/review-tiers/tier-2-core.md        # B1, B2, B2-PRO
claude_extensions/commands/review-tiers/tier-3-seminar.md     # B2-HIST, C1-BIO, C1-HIST, LIT
claude_extensions/commands/review-tiers/tier-4-advanced.md    # C1, C1-PRO, C2

# Activity schema (for validating fixes)
schemas/activities-{level}.schema.json

# Module source files
curriculum/l2-uk-en/plans/{level}/{slug}.yaml           # Plan (source of truth)
curriculum/l2-uk-en/{level}/meta/{slug}.yaml             # Build config
curriculum/l2-uk-en/{level}/{num}-{slug}.md              # Lesson content
curriculum/l2-uk-en/{level}/activities/{slug}.yaml       # Activities
curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml       # Vocabulary
```

### Review Dimensions (Compact Reference)

**Core A (12 dimensions):**

| # | Dimension | Auto-fail | Weight |
|---|-----------|-----------|--------|
| 1 | Lesson Quality | <7 | 1.5 |
| 2 | Coherence | <7 | 1.0 |
| 3 | Relevance | <7 | 1.0 |
| 4 | Educational | <7 | 1.2 |
| 5 | Language | <8 | 1.1 |
| 6 | Pedagogy | <7 | 1.2 |
| 7 | L1/L2 Balance | <6 | 1.0 |
| 8 | Activities | <7 | 1.3 |
| 9 | Richness | <6 | 0.9 |
| 10 | Beginner Safety | <7 | 1.3 |
| 11 | LLM Fingerprint | <7 | 1.0 |
| 12 | Linguistic Accuracy | <9 | 1.5 |

**Pass threshold:** 8.5+ overall, no dimension below its auto-fail.

**Core B / Seminar (14 dimensions):** Same as above plus:
- 13: Propaganda Filter (decolonized narrative)
- 14: Semantic Nuance (hedging markers for C1+)

### Known Systematic Patterns

Check these FIRST on every module — they recur across the entire curriculum:

| Pattern | What to look for | Fix |
|---------|-----------------|-----|
| YAML wrapper | `activities:` dict wrapper + frontmatter in activities YAML | Remove frontmatter + wrapper, make bare list |
| IPA /w/ vs /ʋ/ | Ukrainian В transcribed as /w/ instead of /ʋ/ (labiodental approximant) | Replace all /w/ with /ʋ/ in IPA for В |
| Proper name capitalization | Names like `таня`, `іван` uncapitalized in vocabulary | Capitalize: `Таня`, `Іван` |
| Vocabulary POS errors | Adjectives tagged as `pos: noun`, nouns tagged as `pos: conj` | Fix POS to match actual word class |
| IPA missing stress | Polysyllabic words without stress mark in IPA | Add ˈ before stressed syllable |
| Latin in Cyrillic fields | Anagram scrambled letters using Latin instead of Cyrillic | Replace with Cyrillic equivalents |
| Russianisms | кушать, приймати участь, самий кращий, слідуючий | Use Ukrainian: їсти, брати участь, найкращий, наступний |

### Completion Report Format

Return this summary to the parent agent:

```
✅ {level} M{num} — {title} — COMPLETE

Score: {X.X}/10 | Status: PASS/FAIL
Words: {words}/{target} | Activities: {count} | Issues fixed: {count}

Key findings:
- {bullet 1}
- {bullet 2}
- {bullet 3}
```
