# Rewrite A1 M1-M6 Plans + Fix A1/A2 Plan Issues

## Context

The A1 Cyrillic Code plans (M1-M4) were written without consulting Ukrainian textbooks. Result: garbage vocabulary (мул = "mule", луна = "echo"), fake phrases ("Нас сам"), letter groupings that don't match the code's decodability charsets, and section word budgets that sum to 2000 when the target is 1200.

Textbook research (Bolshakova 2018, Zaharijchuk NUS 2025) shows both bukvars introduce О as letter #1 or #2 because it unlocks high-frequency words (сом, сон, молоко, масло, слово). Our M1 omits О, leaving only ~5 useful words.

Additionally: M5 "Syllables and Transfer" has a confusing English title ("transfer" = переніс/hyphenation), and M6 "Stress and Intonation" is decent but needs section budget fixes.

**Separate issues found during A1 plan screening** need fixing in other plan files too.

---

## Part 1: Rewrite M1-M4 Plans (Letter Groupings from Textbooks)

### New Letter Groupings

Based on both bukvars + aligning with the **existing code charsets** in `_DECODABLE_CHARSETS`:

| Module | Letters (new) | Cumulative | Source |
|--------|--------------|------------|--------|
| **M1** | А О У М Л Н С | 7 | Bolshakova p.12-22: А О М Л У Н С. Zaharijchuk: О А У first. Adding О unlocks сом, сон, масло, молоко, слово |
| **M2** | К И І Р В Т Е | 14 | Matches `_DECODABLE_CHARSETS[2]` exactly. Bolshakova p.26-38. |
| **M3** | Б Д П З Г Х Ж Ш Ч | 23 | Matches `_DECODABLE_CHARSETS[3]` exactly (minus Ґ, which moves to M4 — too rare for its own slot). |
| **M4** | Й Щ Я Ю Є Ь Ї Ц Ф Ґ + ДЖ ДЗ + ' | 33 | All remaining letters, digraphs, apostrophe, soft sign |

**Key changes from current plans:**
- М1: +О (was АМЛУНС, now АОУМЛНС). Unlocks ~20 more words
- M2: Т and Е move here (were in M3 plan). Б and Д move to M3. **Matches code.**
- M3: +Ч (was in M4 plan), +Б +Д (were in M2 plan), -Ґ (moves to M4). **Matches code.**
- M4: +Ґ (was in M3 plan), -Ч (moves to M3)

### M1 New Vocabulary (textbook-sourced)

From Bolshakova p.21-22, words used with А О У М Л Н С:

| Word | Meaning | IPM | Source |
|------|---------|-----|--------|
| мама | mom | 46.4 | Both bukvars, universal |
| сом | catfish | 7.0 | Bolshakova p.22 |
| сон | dream/sleep | 65.7 | Bolshakova p.22 |
| оса | wasp | 2.7 | Bolshakova p.22 |
| сосна | pine tree | 5.3 | Bolshakova p.22 |
| насос | pump | 1.5 | Bolshakova p.22 |
| лама | llama | — | Bolshakova p.21 |
| масло | butter/oil | 14.2 | Bolshakova p.15 |
| слон | elephant | 5.8 | Bolshakova p.30 (preview) |
| нам | to us | common | Both bukvars |
| нас | us | common | Both bukvars |
| сам | self | common | Both bukvars |
| мало | little/few | common | Bolshakova p.14 |
| ананас | pineapple | — | Bolshakova p.22 |
| смола | resin | 3.4 | Bolshakova p.22 |

**Phrases possible with О**: "У нас — ананас." "У нас — сом." "А у вас?" (from Bolshakova p.22 — actual textbook phrases!)

### M1 Section Structure

```yaml
content_outline:
- section: Вступ — Introduction
  words: 200
  points:
  - English scaffolding: Ukrainian has 33 letters, highly phonetic
  - Cultural hook: Cyrillic from students of Cyril & Methodius in First Bulgarian Empire
  - This module: 7 letters (3 vowels А О У + 4 consonants М Л Н С)
- section: Голосні — Vowels А, О, У
  words: 250
  points:
  - А — sounds like 'a' in 'father'. Key word: ананас. Anna Ohoiko video.
  - О — sounds like 'o' in 'more'. Key word: око. Video. Ukrainian О never reduces (unlike Russian).
  - У — sounds like 'oo' in 'moon'. Key word: Україна. Video.
  - Golden Rule: Ukrainian vowels stay pure in any position.
- section: Приголосні — Consonants М, Л, Н, С
  words: 250
  points:
  - М — like English M. Key word: мама. Video.
  - Л — looks like a tent (Λ). Key word: лимон (preview). Video.
  - Н — FALSE FRIEND: looks like H but sounds like N. Key word: нам. Video.
  - С — FALSE FRIEND: looks like C but always /s/. Key word: сом. Video.
- section: Склади і слова — Syllables and Words
  words: 300
  points:
  - Open syllables: МА МО МУ НА НО НУ ЛА ЛО ЛУ СА СО СУ
  - Closed syllables: АМ ОМ УМ АН ОН УН АС ОС УС АЛ ОЛ УЛ
  - Blending into words: ма+ма = мама, со+м = сом, со+сна = сосна
  - Word reading drill: мама, сом, сон, оса, масло, сосна, ананас, насос, лама, смола
- section: Підсумок — Summary
  words: 100
  points:
  - Progress: 7 of 33 letters (3 vowels + 4 consonants)
  - Self-check: Can you read мама? сом? масло? What sound does Н make?
  - Next: Cyrillic Code II adds 7 more letters
```

**word_target: 1200** (sum of sections: 1100, within ±10%)

### M2-M4 Plan Outlines

**M2** — "К И І Р В Т Е — Now You Can Read Words"
- 3 new vowels (И, І, Е) + 4 new consonants (К, Р, В, Т)
- Key vocab: кіт, вік, рис, сир, тато, місто, море, метро, ліс, вікно, літо, стіл, молоко, кіно, око, слово
- False friend: Р looks like P but is /r/. В looks like B but is /v/.
- Section structure: Intro → Vowels И,І,Е → Consonants К,Р,В,Т → Word drills → Reading practice → Summary
- word_target: 1200

**M3** — "Б Д П З Г Х Ж Ш Ч — Voiced and Voiceless Pairs"
- 9 new consonants, introduces voiced/voiceless concept
- Key vocab: хліб, парк, школа, будинок, газета, пошта, шапка, живот, чай (preview)
- Voiced/voiceless pairs: Б/П, Д/Т, Г/Х, З/С, Ж/Ш
- Section structure: Intro → Letters Б,Д,П → Letters З,Г,Х → Letters Ж,Ш,Ч → Voiced/voiceless drill → Summary
- word_target: 1200

**M4** — "The Full Alphabet — Й Щ Я Ю Є Ь Ї Ц Ф Ґ"
- Remaining 10 characters + digraphs ДЖ/ДЗ + apostrophe + soft sign
- Key vocab: чай, яблуко, їжа, день, сім'я, Львів, Європа, центр, щастя, м'яч, ґанок
- Iotated vowels: Я Ю Є Ї — dual function (beginning of syllable vs after consonant)
- Section structure: Intro → Affricates Ц,Щ,Ф → Iotated vowels Я,Ю,Є,Ї,Й → Soft sign & apostrophe → Digraphs ДЖ,ДЗ + Ґ → Full alphabet summary
- word_target: 1200

---

## Part 2: Rewrite M5-M6 Plans

### M5: "Syllables and Word Division" (was "Syllables and Transfer")

"Transfer" is a literal translation of "переніс" that means nothing in English. Rename to "Syllables and Word Division."

Current problems:
- Section budgets sum to 2000 vs target 1200
- "Наголос і склади" section overlaps with M6 (stress) — remove, that's M6's job

New structure:
```
- Що таке склад? (300w) — vowel = syllable core, counting syllables
- Типи складів (300w) — open vs closed, consonant clusters, maximal onset
- Правила переносу (400w) — word division rules for writing, cannot-split rules, дж/дз, ь, apostrophe
- Практика (200w) — drills
Total: 1200
```

### M6: "Stress and Intonation" — keep title, fix budgets

Current problems:
- Section budgets sum to 2000 vs target 1200

New structure:
```
- Наголос (350w) — free/mobile stress, stress changes meaning (замок/замок)
- Типові наголоси (250w) — first/last/penultimate patterns
- Рухомий наголос (250w) — stress shifts in declension/conjugation (awareness only)
- Інтонація (250w) — declarative, interrogative, exclamatory
- Практика (100w) — drills
Total: 1200
```

---

## Part 3: Fix Other A1 Plan Issues

| File | Fix |
|------|-----|
| `plans/a1/buying-tickets.yaml` | `підстаканник` → `підсклянник` (Russianism, not in VESUM) |
| `plans/a1/the-genitive-i-absence.yaml` | `молоко` labeled "feminine" → "neuter" |
| `plans/a1/at-the-market.yaml` | Swap `здача`/`решта` priority — решта is 23x more frequent |
| `plans/a1/at-the-store.yaml` | Remove claim that `покупка` is Russian — it IS Ukrainian (in VESUM) |

---

## Part 4: Code Changes (align with new plans)

| File | Change |
|------|--------|
| `scripts/pipeline_lib.py` `_DECODABLE_CHARSETS[1]` | Add Оо: `"АаОоУуМмЛлНнСс"` (was `"АаМмЛлУуНнСс"`) |
| `scripts/pipeline_lib.py` `_DECODABLE_WORDS[1]` | New list from textbooks: мама, сом, сон, оса, масло, сосна, насос, лама, смола, ананас, нам, нас, сам, мало |
| `scripts/pipeline_lib.py` `PEDAGOGICAL_CONSTRAINTS["a1-m01"]` | Update letter list to include О |
| `scripts/audit/checks/rule_engine.py` `_DECODABILITY_SPECS` | Add Оо to module 1 charset |
| `scripts/pipeline_lib.py` `_DECODABLE_WORDS[2]` | Review against new M2 charset (Т,Е now in M2; Б,Д now in M3) |

---

## Part 5: Deferred — GH Issue for A2 + Remaining Levels

Create a GH issue to review A2, B1+, and seminar plan files in a future session. Not blocking this implementation.

---

## Files Modified

| File | What |
|------|------|
| `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-i.yaml` | Full rewrite |
| `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-ii.yaml` | Full rewrite |
| `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-iii.yaml` | Full rewrite |
| `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-iv.yaml` | Full rewrite |
| `curriculum/l2-uk-en/plans/a1/syllables-and-transfer.yaml` | Rewrite (rename + fix budgets) |
| `curriculum/l2-uk-en/plans/a1/stress-and-intonation.yaml` | Fix section budgets |
| `curriculum/l2-uk-en/plans/a1/buying-tickets.yaml` | підстаканник → підсклянник |
| `curriculum/l2-uk-en/plans/a1/the-genitive-i-absence.yaml` | молоко gender fix |
| `curriculum/l2-uk-en/plans/a1/at-the-market.yaml` | здача → решта priority |
| `curriculum/l2-uk-en/plans/a1/at-the-store.yaml` | Remove false покупка claim |
| `scripts/pipeline_lib.py` | M1 charset + word list + constraints |
| `scripts/audit/checks/rule_engine.py` | M1 charset |
| Meta + orchestration files for M1 | Propagate changes |

---

## Verification

```bash
# 1. Validate all plans parse correctly
.venv/bin/python scripts/validate_plans.py a1

# 2. Verify decodability charsets match plans
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from pipeline_lib import _DECODABLE_CHARSETS, _DECODABLE_WORDS, _charset_filter
for m in [1,2,3]:
    charset = _DECODABLE_CHARSETS[m]
    words = _DECODABLE_WORDS.get(m, [])
    filtered = _charset_filter(words, charset)
    print(f'M{m}: {len(filtered)} words pass charset ({len(words)} total)')
    if filtered != words:
        rejected = set(words) - set(filtered)
        print(f'  REJECTED: {rejected}')
"

# 3. VESUM-verify all M1 vocabulary
# (use mcp__rag__verify_word for each word in the new list)

# 4. Run existing tests
.venv/bin/python -m pytest tests/test_pipeline_v4.py tests/test_rule_engine.py -x -q

# 5. Rebuild M1 with new plan
.venv/bin/python scripts/build_module.py a1 1 --rebuild
```
