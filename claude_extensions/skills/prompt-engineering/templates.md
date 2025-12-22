# Prompt Engineering Templates

## Template: AI Context File (CLAUDE.md)

```markdown
# PROJECT.md - AI Context

## Overview
<context>
[1-2 sentence project description]
[Primary goal/purpose]
[Key technologies/frameworks]
</context>

## Directory Structure
<structure>
[Tree view of important directories]
[Note which files are source of truth]
</structure>

## Key Rules
<constraints>
[What must always be done]
[What must never be done]
[Project-specific conventions]
</constraints>

## Common Tasks
<instructions>
### Task 1: [Name]
1. Step one
2. Step two
3. Step three

### Task 2: [Name]
...
</instructions>

## Examples
<examples>
<example name="good-input">
[Input example]
</example>
<example name="good-output">
[Expected output]
</example>
</examples>
```

## Template: Review Prompt

```markdown
# Review Prompt: [Purpose]

## Task
<instructions>
Review the provided [content type] and:
1. [Specific check 1]
2. [Specific check 2]
3. [Specific check 3]
</instructions>

## Context
<context>
- Content type: [What is being reviewed]
- Quality standards: [Link to guidelines]
- Level: [Skill level, CEFR level, etc.]
</context>

## Constraints
<constraints>
- Do NOT [specific prohibition]
- Always [specific requirement]
- If unsure about [X], ask before proceeding
</constraints>

## Output Format
<format>
Return your review as:
1. **Summary**: 1-2 sentence overall assessment
2. **Issues**: Bulleted list of problems found
3. **Suggestions**: Specific improvements to make
4. **Fixed content**: Corrected version (if applicable)
</format>

## Examples
<examples>
[3-5 input/output pairs showing expected review behavior]
</examples>
```

## Template: Task Instruction

```markdown
# Task: [Name]

## Goal
<instructions>
[Clear statement of what needs to be accomplished]
</instructions>

## Input
<data>
[What you're working with - file paths, content, etc.]
</data>

## Steps
<instructions>
1. [First step with specific action]
2. [Second step with specific action]
3. [Third step with specific action]
</instructions>

## Output
<format>
[Exact format of expected output]
[Example of correct output]
</format>

## Constraints
<constraints>
- [What NOT to do]
- [Boundaries]
- [When to stop or ask]
</constraints>
```

## Resources

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Anthropic Prompt Library](https://docs.anthropic.com/en/prompt-library)
