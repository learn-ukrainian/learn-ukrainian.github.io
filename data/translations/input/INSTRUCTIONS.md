# Tell Gemini This:

```
Read the file: data/translations/input/all-remaining-words.txt

Translate those Ukrainian words to English. Return ONLY a JSON object with format:
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

Save your response to: data/translations/all-translations.json
```

That's it. When done, tell Claude: "done"
