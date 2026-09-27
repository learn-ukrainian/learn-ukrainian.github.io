# Translation Archive

This directory stores vocabulary translations in JSON format for version control and reproducibility.

## Files

- `a1-gemini-translations.json` - A1 vocabulary translated by Gemini
- `a2-gemini-translations.json` - A2 vocabulary translated by Gemini
- `b1-gemini-translations.json` - B1 vocabulary translated by Gemini
- `b1-manual-translations.json` - B1 manual translations (Issue #462 cleanup)

## Format

```json
{
  "українське_слово": "english translation",
  "іменник": "noun",
  "дієслово": "verb"
}
```

## Workflow

```
Translation Source → JSON Archive → apply_translations_batch.py → YAMLs → rebuild DB
                          ↓
                    (git commit)
```

This ensures:
- Translations are version-controlled
- Database can be quickly rebuilt from YAMLs
- Manual work is preserved separately from automated translations
- Easy to re-apply translations if YAMLs are regenerated

## Related Scripts

- `scripts/apply_translations_batch.py` - Applies JSON translations to YAML files
- `scripts/rebuild_vocab_from_yaml.py` - Rebuilds database from YAML files
- `scripts/regenerate_vocab_yamls.py` - Regenerates YAMLs from database (consistency check)
