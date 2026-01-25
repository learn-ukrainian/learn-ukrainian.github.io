# Translation Input Batches

This folder contains 5 batches of Ukrainian words that need translation.

## Files

- `batch-aa` - Batch 1 (100 words) ✅ **DONE**
- `batch-ab` - Batch 2 (100 words) ⏳ **CURRENT**
- `batch-ac` - Batch 3 (100 words)
- `batch-ad` - Batch 4 (100 words)
- `batch-ae` - Batch 5 (45 words)

**Total: 445 words**

## Workflow for Each Batch

### 1. Copy words from batch file

Example for batch-ab:
```bash
cat data/translations/input/batch-ab
```

### 2. Create Gemini prompt

Use this template:

```
Translate these Ukrainian words to English. Return ONLY a JSON object with format:
{
  "ukrainian_word": "english_translation"
}

Rules:
- Provide the most common English translation
- For adjectives, translate as adjective (e.g., "новий" → "new")
- For verbs in infinitive, translate with "to" (e.g., "говорити" → "to speak")
- For nouns, provide the basic English equivalent
- For proper nouns (names, places), transliterate or provide English equivalent
- For diminutives, include "little" or "dear" in translation
- Skip words that are clearly fragments or corrupted (just omit from JSON)
- Return ONLY the JSON object, no other text

Words:

[PASTE WORDS FROM BATCH FILE HERE]

Return the JSON object now.
```

### 3. Save Gemini's response

Save the JSON response to:
- `data/translations/batch-aa-translations.json` (done ✅)
- `data/translations/batch-ab-translations.json` (current)
- `data/translations/batch-ac-translations.json`
- `data/translations/batch-ad-translations.json`
- `data/translations/batch-ae-translations.json`

### 4. Tell Claude when done

Just say "done" and Claude will:
1. Apply the translations to vocabulary YAMLs
2. Show how many were applied
3. Prepare the next batch

## Progress

- ✅ Batch 1 (batch-aa): 21 translations applied
- ⏳ Batch 2 (batch-ab): In progress
- ⬜ Batch 3 (batch-ac): Pending
- ⬜ Batch 4 (batch-ad): Pending
- ⬜ Batch 5 (batch-ae): Pending

## Note

Many words in these batches are fragments that Gemini will correctly skip.
Expected valid translations: ~100-150 words total across all batches.
