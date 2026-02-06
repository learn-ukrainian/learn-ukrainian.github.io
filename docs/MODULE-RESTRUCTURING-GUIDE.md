# Module Restructure Guide

**Purpose:** Guide agents on how to restructure module content when there's a mismatch between existing content and the plan outline.

## When to Use This Guide

Use this guide when:
1. Module audit fails with "Outline Compliance Errors"
2. Content sections don't match plan `content_outline`
3. Word count is below target because content is misorganized

## Key Principle: Plan Takes Precedence

**The plan file is the source of truth for module structure.**

```
Plan content_outline > Template suggested sections > Default structure
```

When a plan has `content_outline`, use those sections as headings. The template provides guidance for modules WITHOUT detailed plans.

## Restructure Workflow

### Step 1: Read the Plan

```bash
cat curriculum/l2-uk-en/plans/{level}/{slug}.yaml
```

Extract:
- `content_outline` - Required sections with word targets
- `word_target` - Total word count goal
- `vocabulary_hints` - Required vocabulary

### Step 2: Read Existing Content

Identify what content exists and map it to plan sections:

| Plan Section | Existing Content Location |
|--------------|--------------------------|
| Section A (400 words) | Found in "## Different Name" |
| Section B (600 words) | Spread across multiple sections |
| Section C (800 words) | Missing entirely |

### Step 3: Restructure (Don't Rewrite!)

**Preserve existing quality content.** Just reorganize under plan section names.

```markdown
## [Exact Plan Section Name]

[Move existing content here]
[Expand if below word target]
```

### Step 4: Fill Word Gaps

If a section is under target:
1. Add more detail from the plan's `points`
2. Add examples, quotes, context
3. Expand on existing ideas

**DO NOT:**
- Pad with filler
- Add content not relevant to the plan
- Introduce vocabulary not in the plan

### Step 5: Verify Structure

After restructuring, verify:
- [ ] All plan sections exist as `##` headings
- [ ] Section names match plan exactly
- [ ] Each section meets its word target (±10%)
- [ ] Total word count meets target (95%+)

## Example: Biography Module

**Plan says:**
```yaml
content_outline:
- section: Вступ — Королева театру
  words: 400
- section: Дитинство та юність (1854-1875)
  words: 600
- section: Зоряні роки
  words: 800
```

**Existing content has:**
```markdown
## Вступ
(155 words)

## Життєпис
### Ранні роки
(500 words about childhood)
### Кар'єра
(700 words about career)
```

**Restructure to:**
```markdown
## Вступ — Королева театру
[Expand existing Вступ to 400 words]

## Дитинство та юність (1854-1875)
[Move "Ранні роки" content here, expand to 600 words]

## Зоряні роки
[Move "Кар'єра" content here, expand to 800 words]
```

## Template vs Plan Conflict Resolution

When template requires sections that differ from plan:

1. **Use plan section names** - they're more specific
2. **Ensure plan sections COVER template topics** - the content should address what the template expects, even under different headings
3. **Template sections are guidance** - you can have more sections than template suggests

Example:
- Template wants: "Життєпис", "Внесок", "Підсумок"
- Plan has: "Дитинство", "Початок кар'єри", "Зоряні роки", "Спадщина"
- **Result:** Use plan sections. "Дитинство" + "Початок кар'єри" + "Зоряні роки" covers "Життєпис". "Спадщина" covers "Внесок" + "Підсумок".

## Common Mistakes to Avoid

❌ **Don't ask which approach to use** - Plan always wins when it has `content_outline`

❌ **Don't delete quality content** - Reorganize, don't remove

❌ **Don't add template sections alongside plan sections** - This creates duplicate coverage

❌ **Don't mix English and Ukrainian** - C1-BIO is 100% Ukrainian content

❌ **Don't invent new vocabulary** - Use only what's in the plan

## Quick Reference

```
1. Read plan → Get exact section names and word targets
2. Map existing content → What goes where?
3. Restructure headings → Use plan section names exactly
4. Fill gaps → Expand sections below word target
5. Audit → Verify structure matches plan
```
