<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Vocabulary Generation — Module Словник

You just wrote a Ukrainian language module. Now list ALL new vocabulary the module teaches.

## Your task

Read the module content below and produce a YAML vocabulary list.

## Rules

1. **Include every word the module teaches for the first time** — not just bold words, ANY word a learner needs to know from this module
2. **Use CONTEXTUAL translations** — if голосні means "vowels" in this module, write "vowels", not "loud"
3. **Include expressions** — multi-word phrases like "Як справи?" or "Рада тебе бачити!"
4. **Plan vocabulary comes first** — the plan's vocabulary_hints are the minimum. Add any extra words you introduced.
5. **Mark expressions** — set `expression: true` for multi-word phrases

## Output format

```yaml
vocabulary:
  - word: "мама"
    translation: "mother"
    expression: false
  - word: "Як справи?"
    translation: "How are you?"
    expression: true
```

Output ONLY the YAML block. No explanations.

## Plan vocabulary (baseline)

<plan_vocabulary>
{PLAN_VOCABULARY}
</plan_vocabulary>

## Module content

<module_content>
{MODULE_CONTENT}
</module_content>
