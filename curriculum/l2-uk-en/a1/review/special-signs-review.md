## Linguistic Scan
No linguistic errors found.

## Exercise Check
Seven markers are present, which matches the seven `activity_hints` in the plan. I also checked the content for the planned vocabulary and notation; the required/recommended words and `[–] / [=]` notation are present.

One exercise-placement issue: `<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->` sits under `## Вимова українських звуків` instead of immediately after `## Дзвінкі і глухі`, so that activity no longer tests the section that was just taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and ordered correctly, and the planned vocabulary appears in prose (`сім'я`, `день`, `сіль`, `м'ясо`, `п'ять`, `гарно`, `риба`, `батько`, `учитель`, `дев'ять`, `комп'ютер`, `м'який`). Deduction: plan references are flattened into generic lines like “Some Ukrainian primers mark...” and “Ukrainian schools use a classic mnemonic...” instead of citing the named sources from the plan. |
| 2. Linguistic accuracy | 10/10 | No Russian characters found; phonetic claims are consistent with the plan, including “The letter **Г** [ɦ] is a voiced fricative” and “**легко** ... [лехко].” |
| 3. Pedagogical quality | 7/10 | Strong examples and minimal pairs, but the apostrophe explanation opens with “exists to do the exact opposite” and “anti-soft-sign” / “wall,” which is catchy but less precise than the plan’s rule-focused framing. |
| 4. Vocabulary coverage | 10/10 | Required and recommended vocabulary is integrated naturally: “**день**,” “**сіль**,” “**м'ясо**,” “**п'ять**,” “**гарно**,” “**риба**,” plus “**батько**,” “**учитель**,” “**дев'ять**,” “**комп'ютер**,” “**м'який**.” |
| 5. Exercise quality | 7/10 | The marker inventory is complete, but `<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->` appears after `## Вимова українських звуків` instead of after `## Дзвінкі і глухі`, so the exercise is misplaced relative to the plan. |
| 6. Engagement & tone | 7/10 | The teacher voice is energetic, but lines like “We must focus intensely...” and “This gives Ukrainian its characteristic resonant sound” add pressure/flourish more than instruction. |
| 7. Structural integrity | 9/10 | Clean markdown, all five H2 headings present, no stray tags beyond expected inject markers, and the pipeline word count is 1676, which is above target. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-first and explicitly blocks a Russian form: “Ukrainian uses **тварина**... avoid the Russian cognate ‘тварь’.” |
| 9. Dialogue & conversation quality | 6/10 | Several exchanges are thin or mechanical, especially “Там звук? ... Ні, він тихий.” and “Це **дуб**? ... Ні, **дуб** тут.” They do not feel like natural classroom or real-life speech. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: “Some Ukrainian primers mark hard consonants as [–] and soft consonants as [=]...” and “Ukrainian schools use a classic mnemonic phrase...”  
Issue: The module uses generic source language instead of naming the plan’s cited references (`Захарійчук`, `Літвінова`).  
Fix: Name the referenced sources directly where their content is introduced.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: “the Ukrainian apostrophe (') exists to do the exact opposite. You can think of the apostrophe as the "anti-soft-sign" or a structural "wall" inside a word.”  
Issue: This framing is catchy but imprecise; it teaches metaphor before rule and overstates the relationship between apostrophe and soft sign.  
Fix: Replace the metaphor with the plan’s precise rule: the apostrophe keeps the consonant hard and signals a clear [й] onset before `я/ю/є/ї`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->` under `## Вимова українських звуків`  
Issue: The voiced/voiceless matching activity is attached to the wrong section.  
Fix: Move that marker to immediately after `<!-- INJECT_ACTIVITY: true-false-voicing -->` in the `Дзвінкі і глухі` section.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: “We must focus intensely on the unique Ukrainian vowel **И** [и].” and “This gives Ukrainian its characteristic resonant sound.”  
Issue: These lines lean into inflated emphasis instead of clear instruction.  
Fix: Use calmer, more specific teacher phrasing.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: “Там звук? ... Ні, він тихий.” and “Це **дуб**? ... Ні, **дуб** тут.”  
Issue: The dialogues are stilted and low-value; they do not model natural speech or help learners hear the target contrast efficiently.  
Fix: Rewrite them as short, natural exchanges that directly reinforce the target contrast.

## Verdict: REVISE
REVISE. There are no critical Ukrainian-form errors, but there are multiple major quality problems: missing named source citations from the plan, a misplaced exercise marker, overly metaphorical apostrophe teaching, and weak dialogue writing. Dimensions 1, 3, 5, 6, and 9 are below 9.

<fixes>
- find: |
    Some Ukrainian primers mark hard consonants as [–] and soft consonants as [=], which can help you see this contrast on the page.
  replace: |
    In **Захарійчук Grade 1**, hard consonants are marked as [–] and soft consonants as [=], which can help you see this contrast on the page.

- find: |
    To help students remember these letters, Ukrainian schools use a classic mnemonic phrase: «**ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи**».
  replace: |
    To help students remember these letters, **Літвінова Grade 5** uses the classic mnemonic phrase: «**ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи**».

- find: |
    There is a core spelling rule for the apostrophe in Ukrainian orthography.
  replace: |
    There is a core spelling rule for the apostrophe in Ukrainian orthography. **Захарійчук Grade 1** presents it this way.

- find: |
    If the soft sign exists to soften a consonant, the Ukrainian apostrophe (') exists to do the exact opposite. You can think of the apostrophe as the "anti-soft-sign" or a structural "wall" inside a word. Its main function is to keep the preceding consonant strictly hard and force the following iotated vowel (**я**, **ю**, **є**, **ї**) to split into two distinct sounds.
  replace: |
    The Ukrainian apostrophe (') is not the opposite of the soft sign. Its main function is to keep the preceding consonant hard and signal that the following iotated vowel (**я**, **ю**, **є**, **ї**) begins with a clear [й] sound.

- find: |
    English speakers often forget to pronounce the [й] sound after an apostrophe. Remember that the apostrophe acts as a wall: **м'ясо** is pronounced with a hard [м], followed by [йасо].
  replace: |
    English speakers often forget to pronounce the [й] sound after an apostrophe. Remember: **м'ясо** is pronounced with a hard [м] and a clear [йа] at the start of the next syllable.

- find: |
    > **Студент:** Що це? *(What is this?)*
    > **Вчитель:** Це **м'який знак**. *(This is a soft sign.)*
    > **Студент:** Там звук? *(Is there a sound?)*
    > **Вчитель:** Ні, він тихий. *(No, it is quiet.)*
  replace: |
    > **Студент:** Що це? *(What is this?)*
    > **Вчитель:** Це **м'який знак**. *(This is a soft sign.)*
    > **Студент:** Він читається? *(Is it pronounced?)*
    > **Вчитель:** Ні, окремого звука немає. Він тільки пом'якшує попередній приголосний. *(No, it has no separate sound. It only softens the preceding consonant.)*

- find: |
    > **Анна:** Це **дуб**? *(Is this an oak?)*
    > **Петро:** Так, старий **дуб**. *(Yes, an old oak.)*
    > **Анна:** Він там? *(Is it there?)*
    > **Петро:** Ні, **дуб** тут. *(No, the oak is here.)*
  replace: |
    > **Анна:** Це **коза** чи **коса**? *(Is that a goat or a braid?)*
    > **Петро:** Це **коза**. *(It is a goat.)*
    > **Анна:** А, тепер чую дзвінкий **з**. *(Ah, now I hear the voiced **z**.)*
    > **Петро:** Саме так. У слові **коза** цей звук дзвінкий. *(Exactly. In the word **коза**, that sound is voiced.)*

- find: |
    We must focus intensely on the unique Ukrainian vowel **И** [и].
  replace: |
    Now focus on the Ukrainian vowel **И** [и].

- find: |
    This gives Ukrainian its characteristic resonant sound.
  replace: |
    This is one of the pronunciation patterns learners notice early in Ukrainian.

- find: |
    <!-- INJECT_ACTIVITY: true-false-voicing -->
  replace: |
    <!-- INJECT_ACTIVITY: true-false-voicing -->
    <!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->

- find: |
    <!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->
    <!-- INJECT_ACTIVITY: quiz-g-vs-g -->
  replace: |
    <!-- INJECT_ACTIVITY: quiz-g-vs-g -->
</fixes>