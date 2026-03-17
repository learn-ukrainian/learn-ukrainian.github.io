## Step 1: Section Coverage Checklist

Checking each plan `content_outline` section against the prompt's "REQUIRED H2 Sections and Points":

| Plan Section | Plan Words | Prompt Match | Location |
|---|---|---|---|
| Вступ — Introduction | ~100 | ✅ YES | `## Вступ — Introduction` (~100 words), all 2 bullet points present |
| Сонорні — Sonorant Consonants | ~200 | ✅ YES | `## Сонорні — Sonorant Consonants` (~200 words), all 3 bullet points present |
| Дзвінкі та глухі пари — Voiced and Voiceless Pairs | ~400 | ✅ YES | `## Дзвінкі та глухі пари — Voiced and Voiceless Pairs` (~400 words), all 8 bullet points present |
| Тверді та м'які — Hard and Soft Consonants | ~250 | ✅ YES | `## Тверді та м'які — Hard and Soft Consonants` (~250 words), all 4 bullet points present |
| Порівняння з англійською — English Comparison | ~150 | ✅ YES | `## Порівняння з англійською — English Comparison` (~150 words), both bullet points present |
| Читання — Reading Practice | ~150 | ✅ YES | `## Читання — Reading Practice` (~150 words), all 4 bullet points present |
| Підсумок — Summary | ~100 | ✅ YES | `## Підсумок — Summary` (~100 words), all 3 bullet points present |

All 7 plan sections are present with their exact headings and all bullet points carried through verbatim.

---

## Step 2: Word Target Check

- Plan `word_target`: **1200**
- Prompt Targets line: **"1200–1800 words"** (minimum 1200, ceiling 1800)
- Prompt section table total: **"1200+ (aim for ~1440)"**
- Audit gate: **Word target: 1200 / Word ceiling: ~1800**

✅ **MATCH** — minimum matches the plan exactly. The ceiling and aim are additive scaffolding, not contradictions.

---

## Step 3: Vocabulary Check

**Required items** (plan `vocabulary_hints.required`):

| Word | In Prompt? |
|---|---|
| хліб (bread) | ✅ YES — required list + content outline point |
| зуб (tooth) | ✅ YES — required list + content outline point |
| дім (house) | ✅ YES — required list + content outline point |
| вовк (wolf) | ✅ YES — required list + content outline point |
| жук (beetle) | ✅ YES — required list + content outline point |
| шапка (hat) | ✅ YES — required list + content outline point |
| гора (mountain) | ✅ YES — required list + content outline point |
| небо (sky) | ✅ YES — required list |
| рука (hand) | ✅ YES — required list + sonorant section point |
| бабуся (grandma) | ✅ YES — required list + content outline point |
| город (city) | ✅ YES — required list |

**Recommended items** (plan `vocabulary_hints.recommended`):

| Word | In Prompt? |
|---|---|
| павук (spider) | ✅ YES — recommended list + content outline point |
| ґанок (porch) | ✅ YES — recommended list + content outline point |
| сіль (salt) | ✅ YES — recommended list |
| люди (people) | ✅ YES — recommended list |
| суп (soup) | ✅ YES — recommended list + content outline point |
| вода (water) | ✅ YES — recommended list + sonorant section point |
| цибуля (onion) | ✅ YES — recommended list |
| люк (hatch) | ✅ YES — recommended list + hard/soft section point |

All 11 required and all 8 recommended vocabulary items are present.

---

## Step 4: Objective Check

| Plan Objective | Prompt Coverage |
|---|---|
| Learner masters sonorant consonants (Л М Н Р В) | ✅ Dedicated `## Сонорні` section with all 5 sonorants, individual letter points for Р and В |
| Learner understands voiced/voiceless pairs (Б/П Д/Т З/С Ж/Ш Г/Х Ґ/К) | ✅ `## Дзвінкі та глухі пари` covers all 7 pairs with examples |
| Learner knows the hard vs soft consonant distinction | ✅ `## Тверді та м'які` with minimal pair лук/люк and always-hard/always-soft rules |
| Learner can read words with all consonants | ✅ `## Читання — Reading Practice` with voiced/voiceless drills and minimal pairs |
| Key rule: no final devoicing (зуб = зу[б], not зу[п]) | ✅ Carried verbatim as CRITICAL RULE point in the voiced/voiceless section |

All objectives are addressed.

---

```yaml
prompt_preflight:
  status: PASS
  issues: []
```