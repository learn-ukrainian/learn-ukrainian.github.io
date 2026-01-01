# Podcast Curriculum Mapping Plan (Phase 3)

## Objective
Integrate the Ukrainian Lessons Podcast (ULP) library into the *Learn Ukrainian* curriculum by mapping specific episodes to relevant modules (A1-C1). This transforms the podcast from a standalone resource into a supplementary learning tool.

## Mapping Strategy

### 1. Direct Topic Mapping
Match podcast titles/summaries to Module themes.
- **Example:** ULP-001 "Informal Greetings" ↔ A1-M01 "Greetings"
- **Example:** ULP-022 "First Verb Conjugation" ↔ A1-M04 "Verbs Type 1"

### 2. Grammar Mapping
Match podcast grammar tags to module grammar focus.
- **Example:** Tag "Dative Case" ↔ A2-M21 "Dative Case Introduction"
- **Example:** Tag "Motion Verbs" ↔ B1-M17 "Motion Verbs"

### 3. Difficulty Alignment
Ensure the mapped episode does not exceed the learner's level significantly (i.e., don't map a B2 podcast to an A1 module unless it's specifically designed for beginners).

## Data Structure

The mapping will be stored in `docs/resources/podcasts/podcast_mapping.json`:

```json
[
  {
    "module_id": "a1-01-cyrillic-code-i",
    "recommended_episodes": ["ULP-001", "FMU-001"]
  },
  {
    "module_id": "a1-04-verbs-type-1",
    "recommended_episodes": ["ULP-022"]
  }
]
```

## Integration into Curriculum

### "Deep Dive" Section
Add a "Recommended Listening" or "Deep Dive" section at the end of `textbook.md` files.

> **🎧 Listen:**
> *   **[ULP-001] Informal Greetings** - Hear native pronunciation of the greetings we just learned.
> *   **[FMU-001] I don't speak Ukrainian well** - Useful phrases for your first conversations.

## Implementation Steps (Phase 3)

1.  **Tagging Audit:** Ensure all 200+ episodes have consistent tags (using `TAG_TAXONOMY.md`).
2.  **Draft Mapping:** Use an LLM to propose mappings based on Episode Summary vs. Module Curriculum Plan.
3.  **Validation:** Human review of the mappings.
4.  **Injection:** Script to insert the "Deep Dive" section into `textbook.md` files automatically.
