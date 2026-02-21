Confirmed: two instances of Latin "a" (U+0061) mixed into Cyrillic "брат". Now let me compile the full review.

---

## Deep Adversarial Review: the-accusative-ii-people (A1 #12)

### Issues Found

**Issue 1: Mixed Script — Latin "a" in Cyrillic word (CRITICAL)**
- **File**: the-accusative-ii-people.md, lines 68 and 155
- **Text**: `**братa**` — the final character is Latin "a" (U+0061), not Cyrillic "а" (U+0430)
- **Impact**: Search, copy-paste, and programmatic processing will break. A student copying this into a dictionary lookup will get no result.
- **Confirmed via hex analysis**: Line 68 `a=U+0061`, Line 155 `a=U+0061`. All other instances of "брата" in the file use correct Cyrillic.

**Issue 2: IPA Stress Error — дочка (MEDIUM)**
- **File**: vocabulary/the-accusative-ii-people.yaml, line 57
- **Text**: `ipa: '[dɔt͡ʃˈkɑ]'` — stress on second syllable
- **Correct**: `[ˈdɔt͡ʃkɑ]` — stress is on the first syllable (дóчка)
- **Impact**: Student learns wrong pronunciation for a high-frequency word.

**Issue 3: Misleading Hard Consonant Generalization (MEDIUM)**
- **File**: the-accusative-ii-people.md, line 74
- **Text**: `Notice the pattern? Hard consonant (**т, н, р**) adds **-а**.`
- **Problem**: Lists **р** as "hard consonant that adds -а", but the table 3 lines above shows **лікар → лікаря** (adds -я, not -а). The р in лікар is soft-stem. This directly contradicts what the student just read and will cause confusion.
- **Fix**: Remove р from the hard list and clarify.

**Issue 4: Redundant Description — Червона Рута (LOW)**
- **File**: the-accusative-ii-people.md, lines 410-411
- **Text**: "...about longing and love. The song is about love and longing..."
- **Problem**: Same idea restated in consecutive sentences. LLM artifact.

**Issue 5: Собака Grouped Under "Жіночий рід" in Activities (LOW-MEDIUM)**
- **File**: activities/the-accusative-ii-people.yaml, lines 389-396
- **Problem**: Собака appears in activity titled "Кого я люблю? (Жіночий рід)" (Feminine gender). In standard Ukrainian, собака is grammatically **masculine** (чоловічий рід), though it declines following the I declension pattern (-а ending) like feminine nouns. The accusative form собаку is correct, but grouping it under "Feminine" misleads about its gender. The explanation should note the gender discrepancy.

**Non-issues verified:**
- IPA in content file: `[ˈbɑt͡ʃɪtɪ]`, `[ˈznɑtɪ]`, `[lʲuˈbɪtɪ]`, `[t͡ʃɛˈkɑtɪ]` — all correct with proper tie bars on affricates
- Vocabulary IPA: uses `[ʋ]` for В (correct), `[ɦ]` for Г (correct), tie bars on `[t͡ʃ]` and `[t͡s]` — all good
- No Russianisms, no Russian characters (ы, э, ё, ъ)
- All unjumble word arrays match their answers
- All fill-in items produce grammatical sentences
- All case forms verified correct (лікаря, вчителя, кота, пса, маму, сестру, etc.)
- Plan compliance: all 5 content_outline sections present, all required vocabulary used
- Green Team review fixes (батько removed from Vowel Magic table, собака explanation in content fixed) — already applied
- Чекати + accusative: standard A1 simplification, pedagogically sound
- "Червона Рута" by Volodymyr Ivasyuk: factually correct
- Word target (2000): content is substantial, automated audit confirms PASS

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
| **брат** | я бачу **братa** | I see (my) brother |
---NEW---
| **брат** | я бачу **брата** | I see (my) brother |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
| **Masc.** | **Animate** | **брат** | я бачу **братa** | **+ а** |
---NEW---
| **Masc.** | **Animate** | **брат** | я бачу **брата** | **+ а** |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
Notice the pattern? Hard consonant (**т, н, р**) adds **-а**. Soft sign (**ь**) or soft consonant adds **-я**.
---NEW---
Notice the pattern? Hard consonant (**т, н**) adds **-а**. Soft sign (**ь**) or soft consonant (like **р** in лікар) adds **-я**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
Do you know the famous song "Червона Рута" (Red Rue) by Volodymyr Ivasyuk? It is one of Ukraine's most beloved songs, about longing and love.
The song is about love and longing — a perfect emotional connection to today's lesson about the people we love.
---NEW---
Do you know the famous song "Червона Рута" (Red Rue) by Volodymyr Ivasyuk? It is one of Ukraine's most beloved songs — about love and longing, a perfect emotional connection to today's lesson about the people we care about.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-accusative-ii-people.yaml
---OLD---
- ipa: '[dɔt͡ʃˈkɑ]'
  lemma: дочка
---NEW---
- ipa: '[ˈdɔt͡ʃkɑ]'
  lemma: дочка
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-accusative-ii-people.yaml
---OLD---
    explanation: Собака закінчується на -а, тому -а змінюється на -у.
---NEW---
    explanation: Собака — чоловічий рід, але закінчується на -а, тому відмінюється як -а → -у.
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===