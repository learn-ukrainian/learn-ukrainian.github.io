Now I have all the data I need. Let me compile the full review.

## Linguistic Scan

**Four separate checks:**

1. **Russianisms** — None found. All Ukrainian words verified against VESUM (84/84 confirmed).

2. **Surzhyk** — None found.

3. **Calques** — None found.

4. **Paronyms** — None found.

**Other checks:**
- No Russian characters (ы, э, ё, ъ) found.
- Gender/case: All forms correct.
- **CRITICAL phonetic claim error**: The module states "exactly 8 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**." This omits **Р**. The plan explicitly lists "9 pairs: Д/Д', Т/Т', З/З', С/С', Ц/Ц', Л/Л', Н/Н', **Р/Р'**, ДЗ/ДЗ'". Авраменко Grade 5 p.75 (RAG-verified) lists 9 м'які приголосні: [д'], [дз'], [т'], [з'], [с'], [ц'], [л'], [н'], **[р']** та [й]. Правопис §26 confirms Ь after Р before О in mid-word (трьох, ларьок). The module teaches a wrong count and a wrong rule.

- **Unpaired Ф omission**: The voiced/voiceless section lists сонорні but omits that **Ф** is an unpaired глухий. Авраменко Grade 5 p.77: "Глухий звук [ф] не має пари за дзвінкістю / глухістю." The module table has no row for Ф.

## Exercise Check

**Marker inventory** (7 markers found, 7 expected from plan):

| Plan hint | Marker in content | Section placement | Status |
|-----------|-------------------|-------------------|--------|
| odd-one-out (М'який знак) | `<!-- INJECT_ACTIVITY: odd-one-out -->` | After М'який знак section ✓ | ✅ |
| fill-in (Апостроф) | `<!-- INJECT_ACTIVITY: fill-in-soft-or-apostrophe -->` | After Апостроф teaching ✓ | ✅ |
| error-correction (Апостроф) | `<!-- INJECT_ACTIVITY: error-correction-apostrophe -->` | After Апостроф teaching ✓ | ✅ |
| group-sort (Апостроф) | `<!-- INJECT_ACTIVITY: group-sort-soft-apostrophe -->` | After Апостроф teaching ✓ | ✅ |
| match-up (Дзвінкі і глухі) | `<!-- INJECT_ACTIVITY: match-voiced-voiceless -->` | After voiced/voiceless pairs ✓ | ✅ |
| true-false (Дзвінкі і глухі) | `<!-- INJECT_ACTIVITY: true-false-voicing -->` | After non-devoicing rule ✓ | ✅ |
| quiz (Вимова) | `<!-- INJECT_ACTIVITY: quiz-g-vs-gx -->` | After Г/Ґ teaching ✓ | ✅ |

All 7 markers present, correctly placed after their respective teaching sections, well-distributed across the module. No clustering issues.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | **Critical deviation**: Plan says "9 pairs: Д/Д', Т/Т', З/З', С/С', Ц/Ц', Л/Л', Н/Н', **Р/Р'**, ДЗ/ДЗ'" — module drops Р entirely, says "exactly 8 consonants." The Літвінова mnemonic correctly encodes 8 (without Р), but the plan explicitly notes 9 м'які pairs, and the module should cover Р+Ь before О per Правопис §26. Section word budgets are reasonable. All references cited (Авраменко, Большакова, Захарійчук, Літвінова, Кравцова). All required and recommended vocabulary present in prose. Self-check in Підсумок also says "8 consonants" — needs fixing too. |
| 2. Linguistic accuracy | 8/10 | The Р omission is a factual error about Ukrainian phonetics. Правопис §26 explicitly lists "після букв д, т, з, с, дз, ц, л, н та **р**" for Ь before О. Авраменко Grade 5 p.75 lists [р'] among м'які. All other phonetic claims verified correct: Г as fricative (confirmed глотковий/фарингальний in Караман Grade 10), Ґ as stop, non-devoicing rule, voiced/voiceless pairs match Большакова Grade 2 p.62 exactly, apostrophe rule matches Правопис §7 and Захарійчук. Minimal pairs all VESUM-verified. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: concept → explanation → examples → practice in every section. Three-way consonant distinction well-presented. Apostrophe section builds beautifully from contrastive pair (пісня vs м'ясо). "Hand on throat" test for voiced/voiceless is textbook pedagogy (Кравцова Grade 2). Minimal pairs for И/І are excellent (бик/бік, дим/дім). Г→Х→add voice explanation is sound. Each section has multiple Ukrainian examples before practice. |
| 4. Vocabulary coverage | 10/10 | All 7 required words used naturally: сім'я (apostrophe section), день (soft sign section), сіль (soft sign opening), м'ясо (apostrophe walkthrough), п'ять (apostrophe walkthrough), гарно (Г section), риба (Р section). All 5 recommended words present: батько, учитель (soft sign patterns), дев'ять, комп'ютер (apostrophe examples), м'який (apostrophe with note about no Ь). Additional contextual words: ім'я, здоров'я, пір'я in reading practice. |
| 5. Exercise quality | 9/10 | All 7 plan activity_hints have corresponding markers. Types match: odd-one-out, fill-in, error-correction, group-sort, match-up, true-false, quiz. Placement is pedagogically sound — each exercise immediately follows its teaching section. Spread is even across 4 major sections. Cannot evaluate answer logic since exercises are YAML-generated downstream, but marker placement and type matching are correct. |
| 6. Engagement & tone | 9/10 | No motivational openers, no "magic of" language, no gamification. Direct, teacher-like tone throughout: "Now meet a letter that breaks that rule" is engaging without being cheesy. The "Place your fingers lightly on your throat" instruction is experiential. Cultural identity woven in naturally ("Ґ is uniquely Ukrainian — an important part of Ukrainian phonetic identity"). One minor issue: "exceptions prove the rule" is a clichéd English idiom that may confuse non-native English speakers. |
| 7. Structural integrity | 10/10 | All 5 H2 headings from plan present in correct order. Clean markdown. No duplicate summaries, no meta-commentary, no stray tags. Word count 1407 exceeds 1200 target. :::tip, :::note, :::caution blocks used appropriately. |
| 8. Cultural accuracy | 10/10 | Fully decolonized — Ukrainian presented on its own terms. "И [...] exists on its own terms" — never compared to Russian И. "Ґ is uniquely Ukrainian" reinforced. The :::caution about not calling Г "soft" shows precise Ukrainian phonetic terminology. No "like Russian but..." anywhere. |
| 9. Dialogue & conversation quality | N/A → 9/10 | This is a phonetics module — dialogues are not expected and the plan includes none. The self-check Q&A format in Підсумок serves as interactive engagement. Scored based on the conversational tone of the prose, which reads like a teacher demonstrating rather than lecturing. |

## Findings

**[PLAN ADHERENCE / LINGUISTIC ACCURACY] [SEVERITY: critical]**
Location: М'який знак section, paragraph "**М'які приголосні** (truly soft consonants) — exactly 8 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**."
Issue: Plan says 9 pairs including Р/Р'. Правопис §26 lists "після букв д, т, з, с, дз, ц, л, н та **р**" for Ь before О in mid-word (трьох, ларьок). Авраменко Grade 5 p.75 lists [р'] among the 9 м'які. Module says 8 and omits Р entirely. Learners will believe Р can never be soft, which is factually wrong.
Fix: Change "8" to "9" and add Р to the list. Add a note that Р takes Ь only before О in mid-word. Update the mnemonic paragraph to clarify the mnemonic covers 8 of the 9, with Р as the additional one. Update the self-check answer in Підсумок accordingly.

**[PLAN ADHERENCE] [SEVERITY: critical]**
Location: Підсумок section, "**After which 8 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**."
Issue: Same Р omission propagated to the self-check. Must match the corrected count of 9.
Fix: Change to 9 consonants and add Р with note about before-О restriction.

**[LINGUISTIC ACCURACY] [SEVERITY: minor]**
Location: Дзвінкі і глухі section: "There is also a group called **сонорні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner."
Issue: The unpaired глухий **Ф** is not mentioned. Авраменко Grade 5 p.77: "Глухий звук [ф] не має пари за дзвінкістю / глухістю." For completeness, Ф should be noted as the lone unpaired voiceless consonant (all textbooks mention it).
Fix: Add a sentence about Ф after the сонорні sentence.

**[ENGAGEMENT & TONE] [SEVERITY: minor]**
Location: Дзвінкі і глухі section, non-devoicing caution box: "But exceptions prove the rule"
Issue: "Exceptions prove the rule" is a clichéd English idiom whose meaning is frequently debated. For A1 learners (many non-native English speakers), this is potentially confusing and adds no pedagogical value.
Fix: Replace with a clearer statement.

## Verdict: REVISE

Two critical findings (Р omission from soft consonants — factual phonetic error that would teach wrong Ukrainian) and two minor findings. The module is otherwise excellent — strong pedagogy, clean structure, accurate linguistics everywhere else. Fixes are targeted and minimal.

<fixes>
- find: "exactly 8 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. These are the consonants you will see **Ь** after in standard Ukrainian spelling."
  replace: "exactly 9 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. For most of these, **Ь** appears at the end of a word or syllable. For **Р**, **Ь** appears in the middle of a word before **О**: **трьох** (three, genitive), **сьогодні** — wait, that is С, not Р — **ларьок** (stall), **чотирьох** (four, genitive). These are the consonants you will see **Ь** after in standard Ukrainian spelling."
- find: "exactly 9 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. For most of these, **Ь** appears at the end of a word or syllable. For **Р**, **Ь** appears in the middle of a word before **О**: **трьох** (three, genitive), **сьогодні** — wait, that is С, not Р — **ларьок** (stall), **чотирьох** (four, genitive). These are the consonants you will see **Ь** after in standard Ukrainian spelling."
  replace: "exactly 9 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. For most of these, **Ь** appears at the end of a word or syllable. For **Р**, **Ь** appears in the middle of a word before **О**: **трьох** (three, genitive), **ларьок** (kiosk), **чотирьох** (four, genitive). These are the consonants you will see **Ь** after in standard Ukrainian spelling."
- find: "Літвінова (Grade 5) gives students a phrase to remember which consonants take **Ь**: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — the capital letters encode exactly the 8 consonants: **ДЗ**, **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**. If a consonant is not in this phrase, **Ь** does not follow it."
  replace: "Літвінова (Grade 5) gives students a phrase to remember which consonants take **Ь**: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — the capital letters encode 8 of the 9 consonants: **ДЗ**, **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**. The ninth — **Р** — takes **Ь** only before **О** in mid-word (трьох, ларьок). If a consonant is not in this list, **Ь** does not follow it."
- find: "There is also a group called **сонорні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner. They sit outside the paired system entirely."
  replace: "There is also a group called **сонорні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner. They sit outside the paired system entirely. On the other side, **Ф** is a voiceless consonant with no voiced partner — it too stands alone."
- find: "But exceptions prove the rule — Ukrainian voiced consonants stay voiced."
  replace: "But this is the rare exception — Ukrainian voiced consonants stay voiced."
- find: "**After which 8 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**. Mnemonic: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»**."
  replace: "**After which 9 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р** (before О), **ДЗ**. Mnemonic for 8 of them: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — plus **Р** before **О**."
</fixes>

**Post-fix note:** The first two find/replace entries above contain a self-correction artifact from my drafting. Here are the clean fixes:

<fixes>
- find: "exactly 8 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. These are the consonants you will see **Ь** after in standard Ukrainian spelling."
  replace: "exactly 9 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. For most of these, **Ь** appears at the end of a word or syllable. For **Р**, **Ь** appears in the middle of a word before **О**: **трьох** (three, genitive), **ларьок** (kiosk), **чотирьох** (four, genitive). These are the consonants you will see **Ь** after in standard Ukrainian spelling."
- find: "Літвінова (Grade 5) gives students a phrase to remember which consonants take **Ь**: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — the capital letters encode exactly the 8 consonants: **ДЗ**, **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**. If a consonant is not in this phrase, **Ь** does not follow it."
  replace: "Літвінова (Grade 5) gives students a phrase to remember which consonants take **Ь**: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — the capital letters encode 8 of the 9 consonants: **ДЗ**, **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**. The ninth — **Р** — takes **Ь** only before **О** in mid-word (трьох, ларьок). If a consonant is not in this list, **Ь** does not follow it."
- find: "There is also a group called **сонорні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner. They sit outside the paired system entirely."
  replace: "There is also a group called **сонорні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner. They sit outside the paired system entirely. On the other side, **Ф** is a voiceless consonant with no voiced partner — it too stands alone."
- find: "But exceptions prove the rule — Ukrainian voiced consonants stay voiced."
  replace: "But this is the rare exception — Ukrainian voiced consonants stay voiced."
- find: "**After which 8 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**. Mnemonic: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»**."
  replace: "**After which 9 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р** (before О), **ДЗ**. Mnemonic for 8 of them: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — plus **Р** before **О**."
</fixes>
