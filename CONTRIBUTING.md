# Contributing to Learn Ukrainian

This guide is for **both humans and AI agents** contributing to the project.

## Project Overview

Learn Ukrainian is a language curriculum generator for Ukrainian language learning. The primary curriculum is `l2-uk-en` (Ukrainian for English speakers).

### Key Files

- `curriculum/l2-uk-en/modules/*.md` - Source module files
- `curriculum/l2-uk-en/*-CURRICULUM-PLAN.md` - Curriculum plans by level
- `scripts/generate.ts` - Generator script
- `output/` - Generated HTML and JSON (auto-generated, don't edit manually)

---

## For AI Agents

### Before You Start

1. **Read CLAUDE.md** - Contains project structure, naming conventions, and rules
2. **Read the relevant CURRICULUM-PLAN.md** - Understand what's planned vs implemented
3. **Check existing modules** - Use similar modules as templates for consistency

### Workflow for AI Agents

```
1. Create a feature branch: git checkout -b feature/description
2. Make changes to curriculum/l2-uk-en/modules/*.md
3. Run generator: npx ts-node scripts/generate.ts l2-uk-en
4. Commit with descriptive message
5. Push branch: git push -u origin feature/description
6. Create PR or request human review
```

### Module Creation Checklist

When creating new modules, verify:

- [ ] Frontmatter includes: module, title, subtitle, level, phase, duration, transliteration, tags, objectives
- [ ] Section structure: `# Зміст уроку | Lesson Content` with warm-up, presentation, practice, production
- [ ] Activities section with quiz and/or fill-in exercises
- [ ] Vocabulary table with IPA, English, and notes
- [ ] Summary section with key takeaways
- [ ] All Ukrainian text is grammatically correct
- [ ] Answer keys provided for all exercises

### Ukrainian Language Quality

**Critical checks:**
- Correct aspect pairs (imperfective/perfective)
- Proper case usage (especially instrumental for agents, accusative for objects)
- Natural word order
- Correct gender agreement
- Standard vocabulary forms (check dictionary if uncertain)

**Common errors to avoid:**
- Mixing adverbs and adjectives (e.g., "були тихо" should be "мовчали" or "були тиші")
- Non-standard vocabulary forms (e.g., "ревнощі" should be "ревність")
- Incorrect aspect in reported speech

### Commit Message Format

```
<type>: <short description>

<optional longer description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: <Agent Name> <email>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`

---

## For Human Contributors

### Getting Started

1. Fork the repository
2. Clone your fork
3. Install dependencies: `npm install`
4. Create a feature branch: `git checkout -b feature/your-feature`

### Running the Generator

```bash
# Generate all curricula
npx ts-node scripts/generate.ts

# Generate specific language pair
npx ts-node scripts/generate.ts l2-uk-en

# Generate specific module (for testing)
npx ts-node scripts/generate.ts l2-uk-en 101
```

### Pull Request Process

1. Ensure all modules follow the structure defined in CLAUDE.md
2. Run the generator to update output files
3. Test HTML output in browser
4. Submit PR with clear description of changes

---

## Multi-Agent Collaboration

This project supports collaboration between multiple AI agents and humans.

### Collaboration Model

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent A   │────▶│   Review    │────▶│   Merge     │
│  (Creator)  │     │  (Agent B)  │     │  (Human)    │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │
      ▼                   ▼
  feature/xxx         PR Comments
    branch            & Suggestions
```

### Branch Naming Convention

| Type | Format | Example |
|------|--------|---------|
| New modules | `feature/b1.3-modules` | `feature/b1.4-modules-126-140` |
| Bug fixes | `fix/module-118-typo` | `fix/aspect-errors` |
| Improvements | `improve/vocabulary-tables` | `improve/activity-consistency` |
| Reviews | `review/b1.3-accuracy` | `review/ukrainian-grammar` |

### Agent Review Protocol

When reviewing another agent's work:

1. **Create review branch** from their feature branch
2. **Document findings** in PR comments or commit messages
3. **Propose fixes** as commits (don't just comment)
4. **Categorize issues:**
   - 🔴 **Critical** - Must fix (grammar errors, incorrect information)
   - 🟡 **Recommended** - Should fix (style, consistency)
   - 🟢 **Suggestion** - Nice to have (enhancements)

### Accepting/Rejecting Changes

The primary agent (or human maintainer) reviews PRs:

```bash
# Review PR locally
gh pr checkout <PR-number>

# If accepting
gh pr merge <PR-number>

# If rejecting with feedback
gh pr comment <PR-number> --body "Reason for rejection..."
gh pr close <PR-number>
```

---

## Quality Standards

### Module Quality Checklist

| Aspect | Requirement |
|--------|-------------|
| **Structure** | All required sections present |
| **Ukrainian** | Grammatically correct, natural phrasing |
| **Pedagogy** | Clear progression, appropriate examples |
| **Vocabulary** | 30-45 words for V-modules, 15-20 for G-modules |
| **Activities** | Answer keys provided, variety of types |
| **Consistency** | Matches style of existing modules |

### Review Focus Areas

1. **Ukrainian Accuracy** - Grammar, spelling, natural usage
2. **Pedagogical Flow** - Logical progression, clear explanations
3. **Structural Consistency** - Follows module template
4. **Vocabulary Coverage** - Appropriate words, correct annotations
5. **Exercise Quality** - Clear instructions, correct answers

---

## Issue Management

### Creating Issues

Use GitHub Issues for:
- Bug reports (incorrect Ukrainian, broken exercises)
- Feature requests (new modules, improvements)
- Planning discussions (curriculum structure)

### Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something incorrect |
| `enhancement` | Improvement to existing |
| `new-content` | New modules/lessons |
| `review-needed` | Requires Ukrainian review |
| `ai-generated` | Created by AI agent |

---

## Communication

### For AI Agents

When handing off work or requesting review:

```markdown
## Handoff Summary

**What was done:**
- Created modules X-Y
- Fixed issues in module Z

**What needs review:**
- Ukrainian accuracy in modules X-Y
- Vocabulary completeness

**Known issues:**
- Module X vocabulary table needs expansion

**Next steps:**
- Implement modules A-B after this merges
```

### For Humans

- Open issues for questions or discussions
- Use PR comments for specific code feedback
- Tag relevant contributors in discussions

---

## Quick Reference

### Essential Commands

```bash
# Generate all
npx ts-node scripts/generate.ts l2-uk-en

# Check git status
git status

# Create feature branch
git checkout -b feature/description

# Commit changes
git add -A && git commit -m "feat: description"

# Push branch
git push -u origin feature/description

# Create PR
gh pr create --title "Title" --body "Description"
```

### File Locations

| Content | Path |
|---------|------|
| Module sources | `curriculum/l2-uk-en/modules/module-*.md` |
| Curriculum plans | `curriculum/l2-uk-en/*-CURRICULUM-PLAN.md` |
| Generated HTML | `output/html/l2-uk-en/` |
| Generated JSON | `output/json/l2-uk-en/` |
| Generator script | `scripts/generate.ts` |

---

## Questions?

- Check existing issues and PRs for similar discussions
- Read CLAUDE.md for project conventions
- Open an issue for clarification
