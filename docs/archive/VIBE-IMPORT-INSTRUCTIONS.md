# Vibe Import Instructions

> ⚠️ **STALE / NEEDS REWORK**
> This import specification is currently outdated and requires significant rework to align with the new "Theory-First" approach and data structure. Do not rely on these instructions until updated.

## JSON Structure v2 - December 2025

The JSON output format has been updated to align with CO-VIBE-INTEGRATION.md spec.

**All modules need to be reimported.**

### Key Changes

1. **New metadata fields**:
   - `moduleType`: grammar, vocabulary, checkpoint, history, biography, idioms, skills, literature, culture, functional
   - `immersionLevel`: 0.0-1.0 (percentage of Ukrainian content)

2. **Simplified sections**:
   - Each section has `name`, `type`, and raw markdown `content`
   - Vibe should extract activities from content (see extraction patterns below)

3. **Raw markdown always included**:
   - `rawMarkdown` field contains full source for reference

### JSON Schema v2

```json
{
  "lesson": {
    "id": "lesson-uk-B2-168",
    "moduleId": "mod-uk-B2-168",
    "moduleNumber": 168,
    "moduleType": "history",
    "immersionLevel": 0.85,
    "title": "History: Kyivan Rus II",
    "titleUk": "Київська Русь II",
    "level": "B2",
    "phase": "B2.2",
    "objectives": ["..."],
    "tags": ["history", "kyivan-rus"],
    "sections": [
      {
        "id": "section-intro",
        "name": "Вступ",
        "nameEn": "Introduction",
        "type": "intro",
        "content": "raw markdown..."
      }
    ],
    "rawMarkdown": "full source..."
  },
  "activities": [...],
  "vocabulary": {...}
}
```

### Extraction Patterns (for Vibe)

Vibe should extract activities from section content:

| Pattern | Activity Type |
|---------|---------------|
| `> [!answer] text` | gap-fill answer |
| `## quiz: Title` | quiz questions |
| `## match-up: Title` | matching pairs |
| `## group-sort: Title` | categorization |
| `Розставте в порядку` + `**Відповідь:**` | ordering |
| `### Обговоріть` | discussion prompts |

### File Locations

```
output/json/l2-uk-en/
├── a1/module-01.json ... module-30.json
├── a2/module-31.json ... module-60.json
├── a2+/module-61.json ... module-80.json
├── b1/module-81.json ... module-140.json
└── b2/module-141.json ... module-190.json
```

### Module Types by Level

| Level | Common Types |
|-------|--------------|
| A1-A2 | grammar, vocabulary, checkpoint |
| B1 | grammar, vocabulary, checkpoint, functional |
| B2 | history, idioms, culture, grammar, vocabulary |
| C1 | literature, skills, biography |

### Questions?

See `vibe/docs/CO-VIBE-INTEGRATION.md` for the full integration spec.
