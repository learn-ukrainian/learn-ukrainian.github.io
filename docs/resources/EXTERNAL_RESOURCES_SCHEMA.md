# External Resources Schema

**Version:** 1.0
**Date:** 2026-01-02
**Status:** Draft (Issue #353)

---

## Purpose

Unified schema for ALL external learning resources across curriculum modules:
- Podcasts (ULP, FMU)
- YouTube videos
- Articles (ULP website, external)
- Books
- Websites
- Other media

**Goals:**
1. Single source of truth for external resources
2. Automated generation of `[!resources]` markdown sections
3. Validation and quality control
4. Easy updates without editing markdown

---

## File Location

**Primary file:** `docs/resources/external_resources.yaml`

**Structure:** Module-centric (resources grouped by module_id)

---

## Schema Definition

### Top-Level Structure

```yaml
# docs/resources/external_resources.yaml
version: "1.0"
generated_at: "2026-01-02"

resources:
  # Module ID as key
  a1-01-cyrillic-code-i:
    # Resource types
    youtube: []      # YouTube videos
    podcasts: []     # ULP/FMU episodes
    articles: []     # Web articles
    books: []        # Book references
    websites: []     # General websites

  a1-07-questions-and-negation:
    youtube: [...]
    articles: [...]
    podcasts: [...]
```

---

## Resource Types

### 1. YouTube Videos

```yaml
youtube:
  - title: "Negative sentences in Ukrainian"
    url: "https://www.youtube.com/watch?v=93NJlqXegFw"
    channel: "Speak Ukrainian"
    duration: "5:23"              # Optional
    relevance: high               # high | medium | low
    description: "..."            # Optional
    added_date: "2025-12-15"      # Optional
```

**Required fields:** `title`, `url`, `channel`, `relevance`
**Optional fields:** `duration`, `description`, `added_date`

### 2. Podcasts (ULP/FMU)

```yaml
podcasts:
  - episode_id: ULP-011           # Must match podcast_db.json
    title: "Ordering drinks in Ukrainian"
    url: "https://www.ukrainianlessons.com/lesson/11/"
    season: 1
    episode: 11
    relevance: high
    match_reason: "Level-aligned topic match: drinks"  # From mapping
```

**Required fields:** `episode_id`, `title`, `url`, `relevance`
**Optional fields:** `season`, `episode`, `match_reason`

**Note:** Episode data (summary, transcript) lives in `podcast_db.json`, referenced by `episode_id`

### 3. Articles (Web)

```yaml
articles:
  - title: "Питальні слова"
    url: "https://www.ukrainianlessons.com/question-words/"
    source: "Ukrainian Lessons"
    relevance: high
    description: "All question words with examples"
    language: uk                  # uk | en | mixed
```

**Required fields:** `title`, `url`, `source`, `relevance`
**Optional fields:** `description`, `language`

### 4. Books

```yaml
books:
  - title: "A Comprehensive Ukrainian Grammar"
    author: "S. Pugh, I. Press"
    isbn: "978-0631227304"        # Optional
    pages: "450-475"              # Optional (specific pages)
    relevance: medium
    description: "Advanced case usage"
```

**Required fields:** `title`, `author`, `relevance`
**Optional fields:** `isbn`, `pages`, `description`

### 5. Websites (General)

```yaml
websites:
  - title: "Useful Ukrainian Questions"
    url: "https://www.ukrainianlessons.com/useful-ukrainian-questions/"
    source: "Ukrainian Lessons"
    relevance: medium
    description: "Practical phrases for travelers"
```

**Required fields:** `title`, `url`, `source`, `relevance`
**Optional fields:** `description`

---

## Relevance Levels

| Level | Description | Usage |
|-------|-------------|-------|
| `high` | Directly teaches module content, essential | Core resources, exact topic match |
| `medium` | Supplements module, useful but not essential | Related content, review material |
| `low` | Tangentially related, optional enrichment | Challenge material, advanced exploration |

---

## Complete Example

```yaml
version: "1.0"
generated_at: "2026-01-02"

resources:
  a1-07-questions-and-negation:
    youtube:
      - title: "Negative sentences/Double negative in Ukrainian language"
        url: "https://www.youtube.com/watch?v=93NJlqXegFw"
        channel: "Speak Ukrainian"
        relevance: high

    articles:
      - title: "Питальні слова"
        url: "https://www.ukrainianlessons.com/question-words/"
        source: "Ukrainian Lessons"
        relevance: high
        description: "All question words with examples"

      - title: "Double Negation Rules"
        url: "https://www.ukrainianlessons.com/negation-in-ukrainian/"
        source: "Ukrainian Lessons"
        relevance: high
        description: "Master Ukrainian negative sentences"

      - title: "Short Ukrainian Questions"
        url: "https://www.ukrainianlessons.com/useful-ukrainian-questions/"
        source: "Ukrainian Lessons"
        relevance: medium
        description: "Practical phrases for travelers"

  a1-09-food-and-drinks:
    podcasts:
      - episode_id: ULP-011
        title: "Ordering drinks in Ukrainian"
        url: "https://www.ukrainianlessons.com/lesson/11/"
        season: 1
        episode: 11
        relevance: high
        match_reason: "Level-aligned topic match: drinks"

      - episode_id: ULP-012
        title: "Ordering food in Ukrainian"
        url: "https://www.ukrainianlessons.com/lesson/12/"
        season: 1
        episode: 12
        relevance: high
        match_reason: "Level-aligned topic match: food"

      - episode_id: FMU-012
        title: "Vocabulary booster! Beverages / Drinks in Ukrainian"
        url: "https://www.ukrainianlessons.com/fmu12/"
        relevance: high
        match_reason: "Level-aligned topic match: drinks"

    youtube:
      - title: "Ukrainian Food Vocabulary"
        url: "https://www.youtube.com/watch?v=EXAMPLE"
        channel: "Learn Ukrainian Fast"
        relevance: medium

  b2-75-volodymyr-i-khreshchennia:
    youtube:
      - title: "Хрещення Русі - Володимир Великий"
        url: "https://www.youtube.com/watch?v=EXAMPLE"
        channel: "Український Інститут"
        relevance: high
        description: "Documentary on Christianization of Kyivan Rus"

    articles:
      - title: "Volodymyr the Great"
        url: "https://en.wikipedia.org/wiki/Vladimir_the_Great"
        source: "Wikipedia"
        relevance: medium
        language: en

    books:
      - title: "Ukraine: A History"
        author: "Orest Subtelny"
        pages: "25-45"
        relevance: high
        description: "Chapter on Christianization"
```

---

## Validation Rules

### Required Validations
1. **No duplicate URLs** within same module
2. **All podcast episode_ids exist** in `podcast_db.json`
3. **All URLs are valid** (HTTP 200 response or flagged for review)
4. **Relevance is valid enum** (high | medium | low)
5. **Module IDs exist** in curriculum

### Warning Validations
1. **YouTube URL format** matches `youtube.com/watch?v=` or `youtu.be/`
2. **Missing descriptions** for high-relevance resources
3. **Too many resources** (>10 per type per module)

---

## Markdown Generation

**Input:** `docs/resources/external_resources.yaml`
**Output:** Updated `[!resources]` sections in module markdown files

**Generation template:**

```markdown
> [!resources] 🔗 External Resources
>
> **🎧 Podcasts:**
> - [ULP 1-11: Ordering drinks in Ukrainian](https://www.ukrainianlessons.com/lesson/11/) — Listening practice
> - [ULP 1-12: Ordering food in Ukrainian](https://www.ukrainianlessons.com/lesson/12/) — Restaurant conversation
>
> **📺 YouTube:**
> - [Negative sentences in Ukrainian](https://www.youtube.com/watch?v=93NJlqXegFw) — Speak Ukrainian
>
> **📖 Articles:**
> - [Питальні слова](https://www.ukrainianlessons.com/question-words/) — All question words with examples
> - [Double Negation Rules](https://www.ukrainianlessons.com/negation-in-ukrainian/) — Master negative sentences
```

**Sorting:**
1. Group by type (Podcasts → YouTube → Articles → Books → Websites)
2. Within type: high relevance first, then medium, then low
3. Within same relevance: alphabetical by title

---

## Migration from Existing Resources

### Phase 1: Extract
Parse existing `[!resources]` sections from 304 markdown files:
- Identify resource type (YouTube, article, etc.)
- Extract title, URL, source
- Infer relevance (all existing = high by default)
- Structure by module_id

### Phase 2: Merge ULP Mappings
Add podcast mappings from `ulp_mapping.yaml`:
- Convert to unified schema format
- Add `match_reason` from mapping
- Deduplicate if manually added

### Phase 3: Validate
Run validation script:
- Check URLs (flag broken links)
- Verify podcast episode_ids
- Check for duplicates

### Phase 4: Regenerate
Generate updated markdown sections:
- Replace existing `[!resources]`
- Use unified template
- Maintain sort order

---

## Scripts

### Extract: `scripts/extract_external_resources.py`
```bash
python scripts/extract_external_resources.py \
  --curriculum curriculum/l2-uk-en/ \
  --output docs/resources/external_resources.yaml
```

### Merge: `scripts/merge_podcast_mappings.py`
```bash
python scripts/merge_podcast_mappings.py \
  --existing docs/resources/external_resources.yaml \
  --podcasts docs/resources/podcasts/ulp_mapping.yaml \
  --output docs/resources/external_resources.yaml
```

### Validate: `scripts/validate_external_resources.py`
```bash
python scripts/validate_external_resources.py \
  docs/resources/external_resources.yaml
```

### Generate: `scripts/generate_resource_sections.py`
```bash
python scripts/generate_resource_sections.py \
  --input docs/resources/external_resources.yaml \
  --curriculum curriculum/l2-uk-en/ \
  --dry-run  # Preview changes
```

---

## Future Enhancements

1. **Automated URL checking** - Cron job to validate links monthly
2. **Resource ratings** - Track user feedback on resource quality
3. **Difficulty tagging** - Mark resources as easier/harder than module level
4. **Language learning paths** - Track which resources form coherent sequences
5. **Integration with Vibe app** - Export resources to JSON for mobile app

---

## Related Files

- `docs/resources/podcasts/podcast_db.json` - Podcast episode database
- `docs/resources/podcasts/ulp_mapping.yaml` - ULP → module mappings
- `docs/resources/podcasts/CURRICULUM_MAPPING.md` - Mapping strategy

---

**Status:** Draft schema for Issue #353
**Next:** Implement extraction script
