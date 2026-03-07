# Resource Request: Linguistic Planning

> **Your task: Read the plan and output a JSON resource request listing ALL Ukrainian words and phrases you will need to write this module.**

## Files to Read

| File | Purpose |
|------|---------|
| `{PLAN_PATH}` | Objectives, vocabulary_hints, content_outline |
| `{META_PATH}` | Section word allocations |
| `{QUICK_REF_PATH}` | Level constraints, immersion % |

Read ALL files before outputting.

## Module Constraints

{PEDAGOGICAL_CONSTRAINTS}

## What to Output

Based on the plan, estimate ALL Ukrainian words and phrases you will need. Think about:

1. **Vocabulary from the plan** — all vocabulary_hints words
2. **Grammar examples** — words needed to demonstrate the grammar point
3. **Immersion sentences** — Ukrainian words for example sentences
4. **Engagement boxes** — words for tips, warnings, cultural notes
5. **Common function words** — pronouns, conjunctions, prepositions you'll need

Output a JSON resource request between delimiters:

===RESOURCE_REQUEST_START===
```json
{
  "requested_vocabulary": {
    "nouns": ["word1", "word2", ...],
    "adjectives": ["word1", "word2", ...],
    "verbs": ["word1", "word2", ...],
    "adverbs": ["word1", "word2", ...],
    "pronouns": ["word1", "word2", ...],
    "prepositions": ["word1", "word2", ...],
    "conjunctions": ["word1", "word2", ...],
    "other": ["word1", "word2", ...]
  },
  "requested_phrases": [
    "Це великий будинок.",
    "Як тебе звати?"
  ],
  "topic_keywords": ["topic1", "topic2"]
}
```
===RESOURCE_REQUEST_END===

## Rules

- List ALL Ukrainian words you might use, not just the plan's vocabulary_hints
- Include common words (це, так, ні, він, вона, воно, вони, я, ти, ми)
- Include words for engagement callouts (tips, warnings)
- Better to over-request than under-request — the sandbox builder will filter
- You do NOT need to worry about grammar constraints — the pipeline will filter
- Output ONLY the JSON between delimiters, no other text
