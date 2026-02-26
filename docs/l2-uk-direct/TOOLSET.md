# l2-uk-direct Toolset

> Last updated: 2026-02-26
> Status: Planning — most scripts not yet built

---

## 1. Schemas

### `schemas/vocabulary-direct.schema.json`
**Status**: Created ✓

L1-agnostic vocabulary entry. Key constraints:
- `pronunciation_video` required (replaces IPA)
- No `translation` field
- `examples` array: minimum 2, Ukrainian sentences only
- `question` enum: `ХТО?`, `ЩО?`, `ЩО РОБИТЬ?`, `ЯКИЙ?`, `ДЕ?`

```json
Required fields: word, pronunciation_video, category, examples
Optional fields: emoji, image_url, image_alt, context_video, question
```

### `schemas/activities-direct.schema.json`
**Status**: Created ✓

Activity types for direct method track:
- `watch_and_repeat` — pre-literacy ✓
- `classify` — pre-literacy ✓
- `image_to_letter` — pre-literacy ✓
- `true_false` — requires reading
- `build_sentence` — requires reading
- `match_sound` — requires reading
- `pattern_drill` — requires reading

---

## 2. Scripts (Needed)

### `scripts/validate_direct.py`
**Status**: Not built
**Purpose**: Validate module YAML files against schemas

```bash
.venv/bin/python scripts/validate_direct.py curriculum/l2-uk-direct/a1/abetka.yaml
```

**Checks**:
- Schema compliance (vocabulary entries, activity structure)
- Pre-literacy gate: warn if modules 1–2 contain reading-dependent activities
- Video URL format (must be YouTube)
- `image_url: null` count (for sourcing status)
- Ukrainian-only content in `examples` and activity items

### `scripts/source_images_direct.py`
**Status**: Not built
**Purpose**: Search Pixabay for images matching keyword, upload to Cloudinary

**Pipeline**:
1. Parse module YAML, find all entries where `image_url: null`
2. For each entry: use `key_word` or `word` to search Pixabay API
3. Display top 5 results for human approval
4. On approval: upload to Cloudinary, update `image_url` in YAML
5. Update `images_sourced` counter in `.status.json`

```bash
.venv/bin/python scripts/source_images_direct.py \
  curriculum/l2-uk-direct/a1/abetka.yaml \
  --cloudinary-folder l2-uk-direct/a1/abetka
```

**Dependencies**: `pixabay-python` or `requests`, `cloudinary` SDK, `PIXABAY_API_KEY`, `CLOUDINARY_*` env vars

### `scripts/status_direct.py`
**Status**: Not built
**Purpose**: Show status of all modules in l2-uk-direct track

```bash
.venv/bin/python scripts/status_direct.py
.venv/bin/python scripts/status_direct.py --level a1
```

**Output format**:
```
l2-uk-direct A1 Status
─────────────────────────────────────────
Module          Status    Images    Notes
abetka          draft     0/33      Needs Pixabay pass
sklad           missing   —         Not yet created
tse             missing   —         Not yet created
...
```

### `scripts/manifest_direct.py`
**Status**: Not built
**Purpose**: Validate manifest.yaml against actual files on disk

```bash
.venv/bin/python scripts/manifest_direct.py
```

**Checks**:
- Every module in manifest has a `.yaml` file
- Every `.yaml` file is in manifest (no orphans)
- `.status.json` exists for every module in manifest
- Module sequence is contiguous (no gaps in numbering)

---

## 3. Manifest System

### File: `curriculum/l2-uk-direct/manifest.yaml`
**Status**: Created ✓

Defines module ordering per level. Replaces numbered filename prefixes.

```yaml
track: l2-uk-direct
name: Українська мова — пряма метода
levels:
  a1:
    sequence:
      - abetka
      - sklad
      - naholos
      - tse
      - shcho-robyt
      - yakyi
      - ya-ty-vin
      - rechennia
      - zapytuyu
      - chysla
      - znavidminnyk-i
      - znavidminnyk-ii
      - mistse
      - misto
      - dim
      - chas
      - den
      - yizha
      - kupuvatysia
      - zdorovia
      - pryroda
      - sim-ya
      - sviatky
      - eufoniia
      - checkpoint-a1
```

---

## 4. Module Status Lifecycle

```
missing → draft → ready → published
```

| Status | Meaning | Gates |
|---|---|---|
| `missing` | File doesn't exist yet | — |
| `draft` | Content exists, not validated | Schema may fail |
| `ready` | Validated, images sourced | Schema passes, images_sourced = images_total |
| `published` | Live in the app | Manual promotion only |

### Status JSON Schema
```json
{
  "module": "string",
  "track": "l2-uk-direct",
  "level": "a1 | a2",
  "status": "draft | ready | published",
  "images_sourced": 0,
  "images_total": 0,
  "last_updated": "YYYY-MM-DD",
  "notes": "string"
}
```

---

## 5. Video Management

### Anna Ohоiko Alphabet Videos
All stored in `abetka.yaml` `pronunciation_video` fields. No separate index needed.

| Letter | Video ID | Full URL |
|---|---|---|
| А | hvB3VpcR3ZE | https://www.youtube.com/watch?v=hvB3VpcR3ZE |
| Б | V1hxBE_JbGg | |
| В | aFcvYfvQ2X4 | |
| Г | gVnclpSI0DU | |
| Ґ | gNjHqjTW9WQ | |
| Д | g4Bh-lqzd48 | |
| Е | KFlsroBW0dk | |
| Є | O0bwRyyBQSc | |
| Ж | dIrGVcqPwqM | |
| З | BhASNxitC1A | |
| И | W-1rCu0indE | |
| І | Z9TH0H4ShGo | |
| Ї | UcjdjQXhAY8 | |
| Й | aq0cjB90s3w | |
| К | J7sGEI4-xJo | |
| Л | v6-3Xg52Buk | |
| М | Ez95H4ibuJo | |
| Н | vNUfiKHPYaU | |
| О | gJFxRIPRZbI | |
| П | JksSjjxyW5Y | |
| Р | fMGsQ5KPQgg | |
| С | 7UsFBgSL91E | |
| Т | m-jcLR_gK0k | |
| У | VB1O6PmtYRU | |
| Ф | haHRsFFZRQI | |
| Х | vpr58zJSJKc | |
| Ц | u44eCjR2Oz8 | |
| Ч | UsJkbdsY2RA | |
| Ш | 1D-6MIw3OXY | |
| Щ | QmBLieIuf6Q | |
| Ь | cJlal8XKBxo | |
| Ю | 9JdIBYCTWGw | |
| Я | yhSAf41LX8I | |

Overview playlist: `https://www.youtube.com/watch?v=ksXIXj7CXwc`
Full playlist: `https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV`

### Video sourcing for other modules
- Context videos (`context_video` field): search YouTube for Ukrainian-language content showing the word in natural use
- No English narration in context videos
- No premium content — only freely available YouTube

---

## 6. Image Pipeline Detail

### Pixabay API
- Free tier: 100 requests/hour, 5000/day
- Search endpoint: `https://pixabay.com/api/?key={KEY}&q={QUERY}&lang=uk&image_type=photo`
- Use `lang=uk` to prioritize Ukrainian results
- Filter: `safesearch=true`, `per_page=5`

### Cloudinary
- Upload endpoint: `https://api.cloudinary.com/v1_1/{cloud}/image/upload`
- Transformation: resize to 800×600, auto format/quality
- Folder structure: `l2-uk-direct/{level}/{module}/{slug}.jpg`
- Naming: `{module}-{word}-{lang}.jpg` (e.g., `abetka-арбуз-uk.jpg`)

### Script workflow (pseudocode)
```python
for entry in module_yaml['letters']:  # or 'vocabulary'
    if entry['image_url'] is not None:
        continue
    results = pixabay_search(entry['key_word'] or entry['word'])
    show_results_to_human(results)
    chosen = get_human_choice()
    url = cloudinary_upload(chosen['largeImageURL'])
    entry['image_url'] = url

update_status_json(images_sourced=count_non_null_images())
write_yaml(module_yaml)
```

---

## 7. Content Validation Rules

These will be implemented in `scripts/validate_direct.py`:

### Pre-literacy gate
Modules 1 and 2 (`abetka`, `sklad`) may only contain:
- `watch_and_repeat`
- `classify` (with symbol-based categories: •/—, or image-based)
- `image_to_letter`

Blocked in modules 1–2: `true_false`, `build_sentence`, `match_sound`, `pattern_drill`

### Ukrainian-only gate
`examples` field entries and activity item texts must contain only Ukrainian characters, punctuation, and spaces. No Latin characters. No translations.

### Video URL gate
`pronunciation_video` and `context_video` must match:
```regex
https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}
```

### Grammar constraint gate
Activities in modules 1–10 must not contain accusative or locative forms (enforced by word list, not parser — optional/future).

---

## 8. Build Priority

| Priority | Script | Blocks |
|---|---|---|
| 1 | `validate_direct.py` | All content quality |
| 2 | `status_direct.py` | Progress visibility |
| 3 | `source_images_direct.py` | Images, publishability |
| 4 | `manifest_direct.py` | Structural integrity |

Build priority 1 and 2 before creating more than 3 modules.
