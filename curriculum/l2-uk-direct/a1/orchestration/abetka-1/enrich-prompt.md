# l2-uk-direct Enrichment

You are enriching an existing Ukrainian language module for the **l2-uk-direct** track — an L1-agnostic course where Ukrainian is the sole medium of instruction. Your job is to **fill gaps and improve quality**, not rewrite from scratch.

## Module Context

- **Slug:** abetka-1
- **Level:** A1
- **Type:** script_foundation
- **Position in sequence:** 1/47
- **Available letters (decodability):** А Л М Н С У а л м н с у

## Current YAML

```yaml
module: abetka-1
track: l2-uk-direct
level: a1
type: script_foundation
title: Абетка — перші букви
subtitle: А М Л У Н С — перший голосний і перші приголосні
standard_ref: §4.1.1 — alphabet, §4.1.4 — vowels/consonants
textbook_ref: Bolshakova 2018 Part 1, pp.12-22
teaching_notes: На цьому етапі важливо зосередитися на розпізнаванні перших шести літер. Усі наведені речення (наприклад,
  «У нас ананас», «Мама сама») використовують виключно букви А, Л, М, Н, С, У, тому учні можуть і повинні читати їх самостійно.
  Зверніть увагу на артикуляцію звуків. Не використовуйте для самостійного читання слова з іншими літерами, навіть якщо вони
  є у ключових словах.
mascot_video: https://www.youtube.com/watch?v=MImM8y_htqY
mascot_credit: Черепаха Аха — Телекомпанія Малятко ТВ
playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
playlist_credit: Anna Ohoiko — Ukrainian Lessons
overview_video: https://www.youtube.com/watch?v=ksXIXj7CXwc
overview_credit: Anna Ohoiko — Ukrainian Letters and Sounds
letters:
- upper: А
  lower: а
  sound_type: vowel
  key_word: ананас
  emoji: 🍍
  image_url: null
  pronunciation_video: https://www.youtube.com/watch?v=hvB3VpcR3ZE
  sentence: У нас ананас.
- upper: М
  lower: м
  sound_type: consonant
  key_word: морква
  emoji: 🥕
  image_url: null
  pronunciation_video: https://www.youtube.com/watch?v=Ez95H4ibuJo
  sentence: Мама сама.
- upper: Л
  lower: л
  sound_type: consonant
  key_word: літак
  emoji: ✈️
  image_url: null
  pronunciation_video: https://www.youtube.com/watch?v=v6-3Xg52Buk
  sentence: Мала лама.
- upper: У
  lower: у
  sound_type: vowel
  key_word: Україна
  emoji: 🇺🇦
  image_url: null
  pronunciation_video: https://www.youtube.com/watch?v=VB1O6PmtYRU
  sentence: У нас мул.
- upper: Н
  lower: н
  sound_type: consonant
  key_word: ножиці
  emoji: ✂️
  image_url: null
  pronunciation_video: https://www.youtube.com/watch?v=vNUfiKHPYaU
  sentence: У нас лан.
- upper: С
  lower: с
  sound_type: consonant
  key_word: сумка
  emoji: 👜
  image_url: null
  pronunciation_video: https://www.youtube.com/watch?v=7UsFBgSL91E
  sentence: Сумна мама.
syllables:
- МА
- МУ
- НА
- НУ
- ЛА
- ЛУ
- СА
- СУ
- АМ
- УМ
- АН
- УН
- АС
- УС
activities:
- type: watch_and_repeat
  title: Слухай і повторюй
  items:
  - letter: А
    video: https://www.youtube.com/watch?v=hvB3VpcR3ZE
  - letter: М
    video: https://www.youtube.com/watch?v=Ez95H4ibuJo
  - letter: Л
    video: https://www.youtube.com/watch?v=v6-3Xg52Buk
  - letter: У
    video: https://www.youtube.com/watch?v=VB1O6PmtYRU
  - letter: Н
    video: https://www.youtube.com/watch?v=vNUfiKHPYaU
  - letter: С
    video: https://www.youtube.com/watch?v=7UsFBgSL91E
- type: classify
  title: Голосний чи приголосний?
  instruction: • = голосний (тільки голос), — = приголосний (шум)
  categories:
  - label: •
    symbol_hint: голосний
    items:
    - А
    - У
  - label: —
    symbol_hint: приголосний
    items:
    - М
    - Л
    - Н
    - С
- type: image_to_letter
  title: Яка перша буква?
  items:
  - emoji: 🍍
    answer: А
    distractors:
    - М
    - У
  - emoji: 🥕
    answer: М
    distractors:
    - Н
    - Л
  - emoji: ✈️
    answer: Л
    distractors:
    - М
    - Н
  - emoji: 🇺🇦
    answer: У
    distractors:
    - А
    - С
  - emoji: ✂️
    answer: Н
    distractors:
    - М
    - Л
  - emoji: 👜
    answer: С
    distractors:
    - Н
    - М
  - emoji: 🍋
    answer: Л
    distractors:
    - У
    - С
  - emoji: 🐒
    answer: М
    distractors:
    - А
    - Н
  - emoji: ☀️
    answer: С
    distractors:
    - Л
    - А
  - emoji: 🦈
    answer: А
    distractors:
    - У
    - М

```

## Enrichment Rules

### What to do

1. **Activities:** Ensure at least 3 activities. If fewer exist, add appropriate ones matching the module type. For `script_foundation` modules, use only: `watch_and_repeat`, `classify`, `image_to_letter`. For other types, choose from: `true_false`, `build_sentence`, `match_sound`, `pattern_drill`, `riddle`, `tongue_twister`, `reading`, `proverb_drill`.

2. **Vocabulary sentences:** Every vocabulary item should have a `sentence` field with a natural Ukrainian example. Add missing sentences.

3. **Teaching notes:** Add or expand `teaching_notes` with practical guidance for the instructor (in Ukrainian).

4. **Activity items:** Expand thin activities. `true_false` needs ≥ 5 items. `image_to_letter` needs ≥ 10 items. `pattern_drill` needs ≥ 5 items. `build_sentence` needs ≥ 5 sentences.

5. **Distractors:** All quiz-type activities must have plausible distractors, not obviously wrong answers.

### What NOT to do

1. **Do NOT change these fields:** `module`, `track`, `level`, `type`, `title`. They must remain exactly as they are.
2. **Do NOT remove** existing activities, vocabulary items, or sections. Only add or expand.
3. **Do NOT use English** anywhere in content. This is an L1-agnostic course. All text, instructions, explanations must be in Ukrainian only.
4. **Do NOT add Latin characters** in Ukrainian content. Watch for accidental English words.
5. **Decodability (script_foundation only):** If available letters are listed above, ALL Ukrainian text in activities and examples must use ONLY those letters. This is critical — learners cannot read letters they haven't been taught yet.

## Output Format

Return the complete enriched YAML. Do NOT wrap in markdown code fences. Output raw YAML only. Preserve the exact structure and field ordering of the original where possible.
