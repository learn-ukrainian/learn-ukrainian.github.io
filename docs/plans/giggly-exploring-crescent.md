# Plan: Rewrite the-cyrillic-code-i (Bukvar Approach + Anna Ohoiko Videos)

## Context

The core l2-uk-en `the-cyrillic-code-i` module currently:
- Covers **18+ letters** using an English-centric "True Friends / False Friends / New Letters" framework
- Defines Ukrainian letters by similarity/difference to English — colonial framing
- Has zero pronunciation videos
- Uses only standard A1 activities (quiz, fill-in, match-up, etc.)

The l2-uk-direct track's `abetka-1` through `abetka-4` modules follow the Ukrainian bukvar approach and split the alphabet into 4 groups by frequency. The core A1 modules should mirror this split.

**4-module mapping (implement module i only now):**

| Core module | Direct module | Letters |
|------------|--------------|---------|
| **the-cyrillic-code-i** | **abetka-1** | **А М Л У Н С** (6) |
| the-cyrillic-code-ii | abetka-2 | К И Р Б В Д І (7) |
| the-cyrillic-code-iii | abetka-3 | П Т Г Ґ Е З Ж Ш Х (9) |
| the-cyrillic-code-iv | abetka-4 | Й Ч Щ Я Ю Є Ь Ї Ц Ф + ДЖ ДЗ + ' (11+) |

## Anna Ohoiko Key Words (Verified from Videos)

Every key word was verified by watching Anna's actual YouTube videos. The previous abetka-1.yaml had hallucinated key words.

| Letter | Video ID | Anna's key word | Emoji | Examples from video |
|--------|----------|----------------|-------|-------------------|
| А | `hvB3VpcR3ZE` | **ананас** | 🍍 | Африка, Аргентіна, аеропорт |
| М | `Ez95H4ibuJo` | **морква** | 🥕 | Мексика, Мінськ, мільйон |
| Л | `v6-3Xg52Buk` | **літак** | ✈️ | Латвія, Ліма, література |
| У | `VB1O6PmtYRU` | **Україна** | 🇺🇦 | Уругвай, Узбекистан, університет |
| Н | `vNUfiKHPYaU` | **ножиці** | ✂️ | Нова Зеландія, Нідерланди, ніс |
| С | `7UsFBgSL91E` | **сумка** | 👜 | Сатурн, Сідней, секрет |

Overview video: `https://www.youtube.com/watch?v=ksXIXj7CXwc`
Playlist: `https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV`

Also discovered: О = **огірок** 🥒 (from sidebar thumbnail) — missing from all abetka files, add to abetka-2 later with К И Р Б В Д І.

## Steps

### Step 1: Update config.py — Enable Pre-Literacy Activities for A1

**File:** `scripts/audit/config.py`

The A1 activity schema (`schemas/activities-a1.schema.json`) already defines `watch-and-repeat`, `classify`, `image-to-letter` (added when we created the direct track). But config.py doesn't know about them.

Changes:
1. Add to `LEVEL_CONFIG['A1']['priority_types']`: `'watch-and-repeat'`, `'classify'`, `'image-to-letter'`
2. Add to `ACTIVITY_COMPLEXITY`:
   ```python
   'watch-and-repeat': {
       'A1': {'min_items': 1},
   },
   'classify': {
       'A1': {'min_items': 1},
   },
   'image-to-letter': {
       'A1': {'min_items': 5},
   },
   ```

### Step 2: Rewrite meta content_outline

**File:** `curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml`

From 18+ letters with English-centric framing → 6 letters with Ukrainian bukvar approach.

```yaml
slug: the-cyrillic-code-i
title: The Cyrillic Code I
word_target: 2000
pronunciation_videos:
  overview: "https://www.youtube.com/watch?v=ksXIXj7CXwc"
  playlist: "https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV"
  credit: "Anna Ohoiko — Ukrainian Lessons"
  letters:
    А: "https://www.youtube.com/watch?v=hvB3VpcR3ZE"
    М: "https://www.youtube.com/watch?v=Ez95H4ibuJo"
    Л: "https://www.youtube.com/watch?v=v6-3Xg52Buk"
    У: "https://www.youtube.com/watch?v=VB1O6PmtYRU"
    Н: "https://www.youtube.com/watch?v=vNUfiKHPYaU"
    С: "https://www.youtube.com/watch?v=7UsFBgSL91E"
content_outline:
  - section: Вступ
    words: 300
    points:
      - "A1 immersion 10-50%. English scaffolding explains the system, Ukrainian carries the content."
      - "The Ukrainian alphabet has 33 letters. It is phonetic — each letter maps to one sound. This module covers the first 6 letters."
      - "Introduce Anna Ohoiko (Ukrainian Lessons) as the pronunciation guide. Embed overview video link."
      - "Brief cultural hook: the alphabet descends from the script created by students of Saints Cyril and Methodius in the First Bulgarian Empire."
      - "Learning method: for each letter, watch Anna's video → repeat aloud → practice reading."
  - section: "Голосні — А, У"
    words: 400
    points:
      - "Explain: Ukrainian has 10 vowels (голосні). This module introduces 2. Vowels are 'voice only' — no obstruction."
      - "А — ананас 🍍. Anna Ohoiko video link. Examples from video: Африка, Аргентіна, аеропорт. Additional examples: ананас, акула, автобус."
      - "У — Україна 🇺🇦. Anna Ohoiko video link. Examples from video: Уругвай, Узбекистан, університет. Additional: улюблений, урок."
      - "Teaching point: Ukrainian vowels are stable — they keep their clear sound in any position, stressed or unstressed."
      - "English sidebar: А sounds like 'a' in 'father' (never reduced). У sounds like 'oo' in 'moon'."
  - section: "Приголосні — М, Л, Н, С"
    words: 500
    points:
      - "Explain: Ukrainian has 22 consonants (приголосні). This module introduces 4. Consonants use some obstruction of airflow."
      - "М — морква 🥕. Video link. Examples: Мексика, Мінськ, мільйон. Additional: мама, молоко, місто."
      - "Л — літак ✈️. Video link. Examples: Латвія, Ліма, література. Additional: лимон, луна, лампа."
      - "Н — ножиці ✂️. Video link. Examples: Нова Зеландія, Нідерланди, ніс. Additional: ніч, нуль, нам."
      - "С — сумка 👜. Video link. Examples: Сатурн, Сідней, секрет. Additional: сон, сіль, сам."
      - "English sidebar: Н looks like English H but is /n/. С looks like English C but is always /s/."
  - section: "Перші склади — First Syllables"
    words: 350
    points:
      - "Now combine the 6 letters into syllables (склади). Syllable = vowel or consonant+vowel."
      - "Open syllables: МА, МУ, НА, НУ, ЛА, ЛУ, СА, СУ."
      - "Closed syllables: АМ, УМ, АН, УН, АС, УС, АЛ, УЛ."
      - "Reading drill: read each syllable aloud, then combine into first words."
      - "First words from known letters: мама, нас, сам, сума, мул, нам, луна."
  - section: "Практика читання — Reading Practice"
    words: 300
    points:
      - "Progressive decoding: syllables → words → short phrases."
      - "Word practice: мама, сума, нас, сам, мул, луна, мус, нам."
      - "First phrases: Мама нам. Нас сам. Сума мала (preview — мала uses only known letters except for the repeated А)."
      - "Self-check: can you read мама? сума? луна?"
  - section: Підсумок
    words: 150
    points:
      - "Progress: 6 of 33 letters learned (2 голосні + 4 приголосні)."
      - "You can now read syllables and simple words."
      - "Next module: The Cyrillic Code II adds 7 more letters (К, И, Р, Б, В, Д, І)."
      - "Link to Anna Ohoiko playlist for independent practice of all 33 letters."
activity_hints:
  - type: watch-and-repeat
    focus: "Watch Anna's video for each of the 6 letters"
    items: 6
  - type: classify
    focus: "Sort А М Л У Н С into голосні vs приголосні"
    items: 6
  - type: image-to-letter
    focus: "See emoji (🍍🥕✈️🇺🇦✂️👜) — which letter does the word start with?"
    items: 6
  - type: match-up
    focus: "Match letter to key word (А↔ананас, М↔морква, etc.)"
    items: 6
  - type: group-sort
    focus: "Sort syllables into open (МА, НУ) vs closed (АМ, УН)"
    items: 12
```

**What changed from current outline:**
- **6 letters only** (А М Л У Н С) — matches abetka-1, not 18+
- **Ukrainian bukvar approach** — голосні/приголосні, not True Friends/False Friends
- **Anna Ohoiko videos** embedded per letter
- **Verified key words** from actual videos (ананас, морква, літак, Україна, ножиці, сумка)
- **Syllable practice** section — fundamental to bukvar method
- **Pre-literacy activity hints** (watch-and-repeat, classify, image-to-letter)
- **English is sidebar notes** ("Н looks like H but is /n/") — not the organizing principle

### Step 3: Fix abetka-1.yaml — Replace Hallucinated Key Words

**File:** `curriculum/l2-uk-direct/a1/abetka-1.yaml`

Replace all 6 hallucinated key words and emojis with Anna's verified ones:

| Letter | Old (hallucinated) | New (verified) |
|--------|-------------------|----------------|
| А | арбуз 🍉 | ананас 🍍 |
| М | мама 👩 | морква 🥕 |
| Л | лимон 🍋 | літак ✈️ |
| У | улитка 🐌 | Україна 🇺🇦 |
| Н | ніс 👃 | ножиці ✂️ |
| С | сонце ☀️ | сумка 👜 |

Also update the `image_to_letter` activity to use the new emojis (🍍🥕✈️🇺🇦✂️👜 instead of 🍉👩🍋🐌👃☀️).

### Step 4: Force Re-research

```bash
.venv/bin/python scripts/build_module_v3.py a1 the-cyrillic-code-i --research-only --force-research
```

### Step 5: Rebuild Content (user runs)

```bash
.venv/bin/python scripts/build_module_v3.py a1 the-cyrillic-code-i
```

### Step 6: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
```

## Files to Modify

1. **`scripts/audit/config.py`** — add watch-and-repeat, classify, image-to-letter to A1 config
2. **`curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml`** — complete rewrite of content_outline
3. **`curriculum/l2-uk-direct/a1/abetka-1.yaml`** — fix 6 hallucinated key words + emojis
4. **`curriculum/l2-uk-en/a1/research/the-cyrillic-code-i-research.md`** — regenerated by pipeline
5. **`curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`** — rebuilt by pipeline

## Verification

1. Meta YAML parses: `.venv/bin/python -c "import yaml; yaml.safe_load(open('curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml'))"`
2. config.py has 3 new types: `grep -c 'watch-and-repeat\|classify\|image-to-letter' scripts/audit/config.py`
3. abetka-1 key words correct: `grep 'key_word' curriculum/l2-uk-direct/a1/abetka-1.yaml` — should show ананас, морква, літак, Україна, ножиці, сумка
4. Research scores 9+: `.venv/bin/python scripts/assess_research.py curriculum/l2-uk-en/a1/research/the-cyrillic-code-i-research.md`
5. Content has 6 video links: `grep -c "youtube.com" curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`
6. Audit passes: `.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`
