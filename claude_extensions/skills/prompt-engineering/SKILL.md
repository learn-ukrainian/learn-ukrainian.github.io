---
name: prompt-engineering
description: Optimize AI-facing documentation using Anthropic's best practices. Use when creating or reviewing CLAUDE.md, AI context files, review prompts, or any documentation meant to be consumed by LLMs. Helps improve clarity, structure, examples, and specificity.
allowed-tools: Read, Glob, Grep, Edit, Write
---

# Prompt Engineering Skill

Optimize AI-facing documentation using Anthropic's best practices.

## When to Use

Use this skill when:
- Creating or reviewing `CLAUDE.md` or similar AI context files
- Writing review prompts for AI assistants
- Optimizing any documentation meant to be consumed by LLMs
- Improving AI assistant instructions

## Optimization Checklist

### 1. Structure & Clarity

- [ ] **Clear hierarchy**: Use headers (H1 > H2 > H3) to organize content
- [ ] **Scannable format**: Tables, bullet points, code blocks for quick parsing
- [ ] **Logical flow**: Most important information first (inverted pyramid)
- [ ] **Consistent formatting**: Same patterns throughout (tables, lists, code)
- [ ] **No ambiguity**: Every instruction has one clear interpretation

### 2. Context & Specificity

- [ ] **Project context**: What is this project? What does it do?
- [ ] **Directory structure**: Where are important files?
- [ ] **Terminology defined**: Project-specific terms explained
- [ ] **Explicit constraints**: What should NOT be done?
- [ ] **Success criteria**: What does "done well" look like?

### 3. Instructions & Tasks

- [ ] **Sequential steps**: Numbered lists for multi-step processes
- [ ] **Specific commands**: Exact commands to run, not vague descriptions
- [ ] **Edge cases covered**: What to do in unusual situations
- [ ] **Examples provided**: Show, don't just tell
- [ ] **Boundaries clear**: When to stop, when to ask for help

### 4. Examples (Multishot Patterns)

- [ ] **3-5 diverse examples**: Cover different scenarios
- [ ] **Realistic examples**: Mirror actual use cases
- [ ] **Edge cases included**: Show handling of unusual inputs
- [ ] **Tagged consistently**: Use `<example>` tags for clarity
- [ ] **Input + Output pairs**: Show what goes in and what comes out

### 5. XML Tag Usage

| Tag | Purpose | Example |
|-----|---------|---------|
| `<instructions>` | Main task instructions | Workflow steps |
| `<context>` | Background information | Project description |
| `<constraints>` | Boundaries and limits | What NOT to do |
| `<examples>` | Sample inputs/outputs | 3-5 diverse examples |
| `<format>` | Output format spec | JSON schema, table format |
| `<data>` | Input data to process | Files, content |

## Anti-Patterns to Fix

### Vague Instructions
```markdown
<!-- BAD -->
Make the code better.

<!-- GOOD -->
Refactor the function to:
1. Extract repeated logic into a helper function
2. Add TypeScript types to all parameters
3. Handle the edge case where input is empty array
```

### Missing Context
```markdown
<!-- BAD -->
Update the module.

<!-- GOOD -->
Update module-45.md (A2 level, Ukrainian grammar):
- Located at: curriculum/l2-uk-en/modules/module-45.md
- Format: See docs/MARKDOWN-FORMAT.md
- Requirements: 8+ activities, 22-30 vocab words
```

### Ambiguous Boundaries
```markdown
<!-- BAD -->
Add some examples.

<!-- GOOD -->
Add exactly 5 example sentences:
- Each 6-10 words (A2 level complexity)
- Include Ukrainian + English translation
- Cover different use cases of the grammar point
```

### No Examples
```markdown
<!-- BAD -->
Format the vocabulary table correctly.

<!-- GOOD -->
Format the vocabulary table like this:

| Slovo | Vymova | Pereklad | ChM | Prymitka |
|-------|--------|----------|-----|----------|
| **knyha** | /kniha/ | book | im. | zhin. rid |
```

## Optimization Process

1. **Analyze current document**
   - Identify vague/ambiguous sections
   - Find missing context or examples
   - Check structure and hierarchy

2. **Apply checklist**
   - Go through each section above
   - Mark items as done or needing work

3. **Rewrite problem areas**
   - Use templates as guides
   - Add examples where missing
   - Make instructions specific and sequential

4. **Test with fresh context**
   - Imagine reading the document with no prior knowledge
   - Could someone follow instructions exactly?
   - Are all edge cases covered?

5. **Iterate based on results**
   - If AI produces wrong output, fix the prompt
   - Add examples of the failure case
   - Clarify ambiguous instructions
