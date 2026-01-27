# Claude Code 2.1.1 Integration Plan for Learn Ukrainian

**Created:** January 9, 2026
**Status:** Planning Phase
**Priority:** High (workflow optimization)

---

## Executive Summary

Claude Code 2.1.1 introduces several features that can significantly improve curriculum development workflow, quality assurance automation, and collaboration efficiency for the Learn Ukrainian project.

**Key Benefits:**
- Reduce permission prompts by 90% (wildcard patterns)
- Automate quality validation (agent hooks)
- Enable parallel development (session teleportation)
- Streamline batch curriculum updates (improved plan mode)
- Background long-running tasks (dev servers, audits)
- Multilingual workflow (Ukrainian review mode)
- Custom slash commands for one-click validation
- Automated issue tracking for reviewers
- LSP integration for structural validation (see Issue #400)

---

## Feature Assessment Matrix

| Feature | Priority | Impact | Complexity | Status |
|---------|----------|--------|------------|--------|
| Wildcard Permissions | **HIGH** | High | Low | Recommended |
| Agent Lifecycle Hooks | **HIGH** | High | Medium | Recommended |
| Hot-Reload Skills | **MEDIUM** | Medium | Low | Recommended |
| Session Teleportation | **MEDIUM** | Medium | Low | Optional |
| Background Tasks | **MEDIUM** | Medium | Low | Recommended |
| Multilingual Mode | **MEDIUM** | Medium | Low | Recommended |
| Custom Slash Commands | **MEDIUM** | Medium | Low | Recommended |
| GitHub Issues Automation | **LOW** | Medium | Low | Optional |
| Vim Motions | **LOW** | Low | None | Available |
| LSP Integration | **HIGH** | High | Medium | See Issue #400 |
| MCP Integration | **MEDIUM** | High | High | Future Phase |
| Plan Mode Improvements | **HIGH** | High | None | Available |

---

## Phase 1: Immediate Wins (Week 1)

### 1.1 Wildcard Permissions Setup

**Rationale:** Eliminate 100+ repetitive permission prompts when working with curriculum scripts.

**Implementation:**

Create `.claude/settings.json`:

```json
{
  "permissions": {
    "bash": {
      "rules": [
        {
          "pattern": "npm *",
          "permission": "allow",
          "description": "Allow all npm commands"
        },
        {
          "pattern": ".venv/bin/python scripts/*",
          "permission": "allow",
          "description": "Allow curriculum validation scripts"
        },
        {
          "pattern": ".venv/bin/python -m pytest *",
          "permission": "allow",
          "description": "Allow test execution"
        },
        {
          "pattern": "cd docusaurus && *",
          "permission": "allow",
          "description": "Allow Docusaurus operations"
        },
        {
          "pattern": "git add curriculum/*",
          "permission": "allow",
          "description": "Stage curriculum changes"
        },
        {
          "pattern": "git commit -m *",
          "permission": "allow",
          "description": "Commit with messages"
        },
        {
          "pattern": "git push *",
          "permission": "ask",
          "description": "Require confirmation for push"
        },
        {
          "pattern": "gh * create *",
          "permission": "ask",
          "description": "Require confirmation for GitHub operations"
        }
      ]
    }
  },
  "respectGitignore": true
}
```

**Expected Impact:**
- Reduce permission prompts by ~90%
- Maintain security for destructive operations (push, force operations)

---

### 1.2 Background Task Support

**Rationale:** Keep dev server running while working on curriculum.

**Usage Pattern:**

```bash
# Start dev server in background
npm run start
[Ctrl+B]  # Background the dev server

# Continue curriculum work
> Generate 5 vocabulary exercises for B1 Module 52

# Dev server keeps running
# Access http://localhost:3000 to preview changes
```

**Expected Impact:**
- No need to stop/restart dev server
- Live preview while editing curriculum
- Better workflow for content review

---

### 1.3 Plan Mode Enhancements

**Rationale:** Leverage improved plan mode for batch curriculum operations (like the recent B1+ vocabulary cleanup).

**Usage:**

```bash
# For batch operations across multiple modules
claude /plan

> Update all C1 biography modules to include new vocabulary enrichment

# Claude creates detailed plan with all 74 affected files
# Use Shift+Tab to auto-accept edits mode
# Use feedback input to refine plan if needed
```

**Expected Impact:**
- Better planning for multi-module updates
- Reduced errors in batch operations
- Clearer visibility into scope of changes

---

### 1.4 Multilingual Mode for Ukrainian Review

**Rationale:** Enable Claude to respond in Ukrainian when reviewing Ukrainian curriculum content.

**Implementation:**

Create `.claude/settings.json` (or add to existing):

```json
{
  "language": "ukrainian",
  "respectGitignore": true,
  "agent": "curriculum-maintainer"
}
```

**Usage Pattern:**

```bash
# Claude reviews Ukrainian content and responds in Ukrainian
> Перевір цей модуль на граматичні помилки

[Claude responds in Ukrainian with detailed analysis]

# Toggle back to English when needed
> Switch to English

# Or use project settings:
# language: "auto" - detect from context
# language: "english" - force English
# language: "ukrainian" - force Ukrainian
```

**Expected Impact:**
- More natural review workflow for Ukrainian content
- Better context for linguistic corrections
- Authentic Ukrainian responses (not translations)
- Useful for A2+ immersed content where Ukrainian is primary language

---

### 1.5 Custom Slash Commands for Workflow

**Rationale:** Create reusable workflow commands for common curriculum operations.

**Implementation:**

Create `.claude/commands/curriculum-validate.md`:

```bash
#!/bin/bash
# /curriculum-validate - Validate all levels

echo "Running curriculum validation..."

levels=("a1" "a2" "b1" "b2" "c1" "c2")

for level in "${levels[@]}"; do
  if [ -f "scripts/check_${level}_status.py" ]; then
    echo "Validating $level..."
    .venv/bin/python scripts/check_${level}_status.py
  fi
done

echo "Running schema validation..."
npm run test:schema

echo "Checking Docusaurus build..."
cd docusaurus && npm run build
```

**Other useful commands:**

- `/curriculum-stats` - Generate statistics across all levels
- `/enrich-vocab` - Run vocabulary enrichment pipeline
- `/audit-level` - Deep audit of specific level
- `/sync-landing` - Update landing pages with current stats

**Usage:**

```bash
claude
> /curriculum-validate

[Runs validation across all levels]
[Reports pass/fail for each]
```

**Expected Impact:**
- One-command validation for all levels
- Consistent workflow across developers
- Easier onboarding for new contributors
- Faster feedback loops

---

## Phase 2: Quality Automation (Week 2)

### 2.1 Agent Lifecycle Hooks for Quality Assurance

**Rationale:** Automatically run validation after curriculum edits to catch errors early.

Create `.claude/agents/curriculum-maintainer.md`:

```yaml
---
name: Curriculum Maintainer
description: Maintains Ukrainian curriculum with strict quality standards
model: sonnet  # Use Sonnet for cost efficiency
hooks:
  PreToolUse:
    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/[0-9]*-*.md"
      command: |
        # Check if writing to curriculum markdown
        echo "📝 Writing to curriculum file: validating structure..."

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/activities/*-*.yaml"
      command: |
        # Check if writing to activity YAML
        echo "🎯 Writing activity file: will validate after save..."

  PostToolUse:
    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/[0-9]*-*.md"
      command: |
        # Extract level and module from path
        FILE="$TOOL_INPUT_file_path"
        LEVEL=$(echo "$FILE" | grep -oP 'l2-uk-en/\K[a-z0-9]+')
        MODULE=$(echo "$FILE" | grep -oP '/\K[0-9]+-')
        MODULE_NUM="${MODULE%-}"

        # Run audit
        echo "🔍 Running audit for ${LEVEL^^} Module ${MODULE_NUM}..."
        .venv/bin/python scripts/audit_module.py "$FILE"

        # Check if audit passed
        if [ $? -eq 0 ]; then
          echo "✅ Audit passed!"
        else
          echo "⚠️  Audit found issues - please review"
        fi

    - matcher:
        tool: Bash
        args:
          pattern: "git commit *"
      command: |
        # After commits, update status tracking
        echo "📊 Updating curriculum status..."
        for level in a1 a2 b1 b2 c1 c2; do
          if [ -f "scripts/check_${level}_status.py" ]; then
            .venv/bin/python "scripts/check_${level}_status.py" > /dev/null 2>&1 || true
          fi
        done
        echo "✅ Status updated"

  Stop:
    - command: |
        # Generate summary at end of session
        echo "📝 Session Summary"
        echo "=================="
        git diff --stat
        echo ""
        echo "Modules modified: $(git diff --name-only | grep -c curriculum/ || echo 0)"
        echo "Activities updated: $(git diff --name-only | grep -c activities/ || echo 0)"
---

Maintains Ukrainian language curriculum (A1-C2) with automatic quality validation.

**Responsibilities:**
- Validate curriculum markdown against MODULE-RICHNESS-GUIDELINES-v2.md
- Check activity YAML syntax and completeness
- Run audit scripts after content modifications
- Update status tracking after commits
- Generate session summaries

**Quality Standards:**
- Vocabulary: 15-30+ words per module (level-dependent)
- Activities: 4-8 per module with proper sequencing
- IPA pronunciation: Required for all vocabulary
- Integration: 80% in activities, 50% in lesson text
- Schema: Valid frontmatter and structure

**Common Tasks:**
- Create new modules from curriculum plans
- Enrich existing modules with activities
- Fix audit violations (grammar, vocabulary, activities)
- Update vocabulary enrichment (IPA, POS, gender)
- Validate schema compliance
```

**Expected Impact:**
- Automatic audit after every curriculum edit
- Catch errors immediately (before commit)
- No manual audit script execution
- Session summaries for documentation

---

### 2.2 Hot-Reload Skills for Workflow Tasks

**Rationale:** Create reusable skills for common curriculum tasks.

#### Skill 1: Module Generator

Create `.claude/skills/generate-module.md`:

```yaml
---
name: Generate Module
description: Generate a complete curriculum module from plan
allowed-tools:
  - Read
  - Write
  - Bash
context: fork  # Run in isolated context
agent: general-purpose
---

Generate a complete Ukrainian curriculum module following these steps:

1. **Read Curriculum Plan**
   - Extract module specification from docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md
   - Parse: title, focus, grammar scope, vocabulary targets, activities

2. **Read Templates**
   - Load appropriate template from docs/l2-uk-en/templates/
   - Grammar: {level}-grammar-module-template.md
   - Vocabulary: {level}-vocab-module-template.md
   - Cultural: {level}-cultural-module-template.md
   - History: {level}-history-module-template.md

3. **Create Module Markdown**
   - Structure: frontmatter, vocabulary, grammar, lesson text
   - Vocabulary table: 6-column format (Слово, Вимова, Переклад, ЧМ, Рід, Примітка)
   - Grammar explanations with examples
   - Engagement boxes (💡 Did You Know, 🎬 Pop Culture, 🌍 Real World)

4. **Create Activity YAML**
   - File: curriculum/l2-uk-en/{level}/activities/{number}-{slug}.yaml
   - Include 4-8 activities with proper sequencing:
     - Recognition: match-up, group-sort
     - Discrimination: quiz, true-false, select
     - Controlled: fill-in, cloze, error-correction
     - Production: unjumble, translate

5. **Create Vocabulary YAML**
   - File: curriculum/l2-uk-en/{level}/vocabulary/{number}-{slug}.yaml
   - Include all vocabulary from module
   - Leave IPA/POS/gender empty for enrichment

6. **Run Audit**
   - Execute: .venv/bin/python scripts/audit_module.py {file}
   - Fix any violations
   - Re-audit until PASS

7. **Generate Output**
   - Run: npm run pipeline l2-uk-en {level} {module_num}
   - Validate: MDX generation, HTML rendering

**Quality Checks:**
- Vocabulary count meets level targets
- Activity types match level requirements
- All Ukrainian text uses correct grammar (no Russianisms)
- IPA placeholders present for enrichment
- Schema validation passes
```

#### Skill 2: Vocabulary Enricher

Create `.claude/skills/enrich-vocabulary.md`:

```yaml
---
name: Enrich Vocabulary
description: Add IPA, POS, and grammatical metadata to vocabulary
allowed-tools:
  - Read
  - Write
  - Bash
---

Enrich vocabulary YAML files with linguistic metadata:

1. **Load Vocabulary File**
   - Read: curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
   - Parse items with missing IPA/POS/gender

2. **Enrich Metadata**
   - Run: .venv/bin/python scripts/enrich_yaml_vocab.py {file}
   - Script uses Wiktionary and Ukrainian dictionaries
   - Adds: IPA pronunciation, POS tags, gender, declension info

3. **Validate Results**
   - Check: all IPA fields populated
   - Verify: POS tags are valid
   - Confirm: gender for nouns, aspect for verbs

4. **Update Module**
   - Regenerate vocabulary table in markdown
   - Run audit to validate

**Sources Used:**
- Wiktionary Ukrainian entries
- Словник.UA (slovnyk.ua)
- Словарь Грінченка
- Антоненко-Давидович "Як ми говоримо" (Russianisms guide)
```

#### Skill 3: Batch Audit

Create `.claude/skills/batch-audit.md`:

```yaml
---
name: Batch Audit
description: Run audits across multiple modules or levels
allowed-tools:
  - Bash
  - Read
---

Run curriculum audits at scale:

**Usage:**
- `/batch-audit a2` - Audit all A2 modules
- `/batch-audit a2 1-10` - Audit A2 modules 1-10
- `/batch-audit all` - Audit all levels

**Process:**
1. Identify target modules
2. Run audit script for each
3. Collect violations by type
4. Generate summary report

**Output:**
- Count: total modules, passed, failed
- Violations: grouped by type (GRAMMAR, VOCAB, ACTIVITY, etc.)
- Recommendations: prioritized fix list
```

**Expected Impact:**
- Standardized module creation workflow
- Consistent quality across all modules
- Reusable skills that improve over time
- Hot-reload allows rapid iteration

---

## Phase 3: Collaboration & Review (Week 3)

### 3.1 Session Teleportation for Reviews

**Rationale:** Share work-in-progress with reviewers across devices.

**Workflow:**

```bash
# Developer creates modules
claude
> Generate C1 Module 110: Contemporary Biography

# Save session for review
claude --teleport c1-m110-review

# Reviewer accesses from browser or different machine
# Visit: https://claude.ai/code
# Or: claude --teleport c1-m110-review
```

**Use Cases:**
- Share curriculum development sessions with reviewers
- Resume work from different devices (desktop ↔ laptop)
- Collaborate on complex batch updates
- Document curriculum decisions

---

### 3.2 Named Sessions for Organization

**Rationale:** Better organization for parallel curriculum work.

**Pattern:**

```bash
# Create named sessions for different levels
claude --session-id c1-biographies
claude --session-id b2-history-fixes
claude --session-id a2-vocabulary-enrichment

# Resume by name
claude --resume c1-biographies
```

**Expected Impact:**
- Clearer organization of curriculum work
- Easy context switching between levels
- Better documentation of changes

---

### 3.3 GitHub Issues Automation for Reviewer Workflow

**Rationale:** Streamline issue creation when reviewers find problems in curriculum modules.

**Implementation:**

Create `.claude/skills/issue-tracker.md`:

```yaml
---
name: Issue Tracker
description: Generate GitHub issue templates for lesson reviews
allowed-tools:
  - Bash
---

When reviewer finds errors, generate structured issue:
- Title format: "[LEVEL-MODULE] Description"
- Labels: level-{a1|a2|b1|b2|c1|c2}, category-{grammar|vocab|activity}
- Reference: MODULE-RICHNESS-GUIDELINES-v2.md sections
- Checklist: vocabulary, activities, IPA, schema, immersion
```

**Usage:**

```bash
# Reviewer finds issues in B2 Module 75
> /issue-tracker

Title: [B2-M75] IPA pronunciation missing for 5 vocabulary words
Module: curriculum/l2-uk-en/b2/75-holodomor-collectivization.md
Issues:
  - Missing IPA for: колективізація, розкуркулення, репресії
  - Activity count: 6 (needs 8 for B2 history)
  - Vocabulary integration: 72% (needs 80%)

[Creates GitHub issue with proper labels and checklist]
```

**Auto-generated issue template:**

```markdown
## Module: B2-M75 Holodomor Collectivization

**File**: `curriculum/l2-uk-en/b2/75-holodomor-collectivization.md`

### Issues Found

- [ ] **IPA**: Missing pronunciation for 5 words
  - колективізація
  - розкуркулення
  - репресії
- [ ] **Activities**: Only 6/8 (B2 history requires 8+)
- [ ] **Integration**: Vocabulary 72% (needs 80%)

### References
- MODULE-RICHNESS-GUIDELINES-v2.md § Vocabulary Richness
- B2 History Module Template
- Issue #341 (6-column vocabulary standard)

### Checklist
- [ ] Fix IPA pronunciations
- [ ] Add 2 activities (prefer cloze/comprehension for history)
- [ ] Increase vocabulary integration in activities
- [ ] Re-run audit until PASS
- [ ] Run pipeline validation
```

**Expected Impact:**
- Consistent issue reporting format
- Faster reviewer-developer feedback loop
- Clear action items with references
- Better tracking of curriculum quality

---

## Phase 4: Advanced Integration (Future)

### 4.1 MCP Integration for Ukrainian NLP

**Rationale:** Integrate existing Ukrainian NLP tools (stanza, pymorphy2) as MCP servers.

**Proposed MCP Servers:**

1. **Ukrainian Grammar Validator**
   - Tool: `validate_grammar(text, level)`
   - Uses: stanza for POS tagging, pymorphy2 for morphology
   - Checks: Russianisms, calques, case agreement

2. **IPA Pronunciation Generator**
   - Tool: `generate_ipa(word)`
   - Uses: Wiktionary API + Ukrainian phonology rules
   - Returns: IPA string with stress markers

3. **YouTube Metadata Fetcher**
   - Tool: `get_video_metadata(url)`
   - Returns: title, description, duration, language
   - Validates: Ukrainian audio availability

**Implementation:** Create `.mcp.json` in project root:

```json
{
  "mcpServers": {
    "ukrainian-nlp": {
      "command": ".venv/bin/python",
      "args": ["scripts/mcp_servers/ukrainian_nlp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    },
    "youtube-metadata": {
      "command": "node",
      "args": ["scripts/mcp_servers/youtube_server.js"]
    }
  }
}
```

**Wildcard Permission:**

```json
{
  "permissions": {
    "mcp": {
      "mcp__ukrainian-nlp__*": "allow",
      "mcp__youtube-metadata__*": "allow"
    }
  }
}
```

---

## Implementation Roadmap

### Week 1: Foundation Setup

- [ ] Install Claude Code 2.1.1: `claude update`
- [ ] Create `.claude/settings.json` with wildcard permissions
- [ ] Configure multilingual mode (Ukrainian review)
- [ ] Create custom slash commands (/curriculum-validate, etc.)
- [ ] Test background task workflow with dev server
- [ ] Document plan mode usage for batch operations
- [ ] Review LSP integration plan (Issue #400)

### Week 2: Quality Automation

- [ ] Create curriculum-maintainer agent with hooks
- [ ] Create 3 core skills (generate, enrich, audit)
- [ ] Test agent hooks with A1 module edits
- [ ] Validate audit automation
- [ ] Test multilingual review with B2 modules
- [ ] Begin LSP schema creation (parallel with Issue #400)

### Week 3: Collaboration

- [ ] Set up session teleportation
- [ ] Create named sessions for each level
- [ ] Create GitHub issues automation skill
- [ ] Test issue-tracker workflow with reviewers
- [ ] Document review workflow
- [ ] Train team on new features

### Week 4: Testing & Documentation

- [ ] Test full workflow: create → audit → review → commit
- [ ] Validate custom slash commands across all levels
- [ ] Test multilingual mode with Ukrainian reviewers
- [ ] Update ARCHITECTURE.md with new workflow
- [ ] Update SCRIPTS.md with hook documentation
- [ ] Create training materials for team
- [ ] Finalize LSP integration (Issue #400)

---

## Success Metrics

**Efficiency Gains:**
- Permission prompts: Reduce from 100+ to <10 per session
- Audit time: Automatic (0 manual runs)
- Review cycle: 50% faster with teleportation
- Batch operations: 3x faster with plan mode

**Quality Improvements:**
- Audit pass rate: Target 95% first-run
- Vocabulary enrichment: 100% IPA coverage
- Schema compliance: 100% validation
- Russianisms: 0 tolerance via NLP validation

**Developer Experience:**
- Session setup: 30 seconds → 5 seconds
- Context switching: Seamless with named sessions
- Collaboration: Real-time with teleportation
- Documentation: Automatic session summaries

---

## Risk Assessment

**Low Risk:**
- Wildcard permissions (reviewed patterns)
- Background tasks (isolated processes)
- Named sessions (organizational only)

**Medium Risk:**
- Agent hooks (could slow workflow if misconfigured)
- Mitigation: Start with PostToolUse only, add PreToolUse gradually

**High Risk:**
- MCP integration (complex development)
- Mitigation: Phase 4 only, after core workflow established

---

## Next Steps

1. **Review this plan** with team
2. **Create GitHub issue** for Phase 1 implementation
3. **Test wildcard permissions** with A1 modules
4. **Iterate on agent hooks** based on feedback
5. **Document** learnings for future phases

---

## References

- Claude Code 2.1.1 Release Notes
- MODULE-RICHNESS-GUIDELINES-v2.md
- ARCHITECTURE.md
- docs/issues/395-resolution.md (vocabulary approach precedent)
