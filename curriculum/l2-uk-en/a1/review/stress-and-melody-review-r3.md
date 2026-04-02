Now I have all the data I need. Here is the full review.

---

## Linguistic Scan

**Verified correct:**
- замок stress pair (ЗА́МОК castle / ЗАМО́К lock) — confirmed by СУМ-11 ✓
- ніколи stress pair (НІ́КОЛИ "no time" / НІКО́ЛИ "never") — confirmed by СУМ-11 ✓
- 38 sounds — confirmed by Заболотний p.73 and Авраменко p.73 ✓
- Sentence type classification (розповідні, питальні, спонукальні + окличні as separate dimension) — confirmed by Авраменко p.19, Заболотний p.165, Litvinova p.206 ✓
- All VESUM "not found" entries are fragments from stress-marked words split by the tokenizer (e.g., "Інтона" from "Інтона́ція", "Заболо" from "Заболо́тний") — not real errors ✓

**Errors found:**

1. **Self-contradictory claim about українська stress.** The module states: "украї́нська (Ukrainian) is stressed on the ї — not on the third syllable as in Russian." The letter ї IS in the third syllable (у-кра-їн-ська). The sentence says stress is on ї but not on the third syllable — these contradict each other. Furthermore, Russian "украи́нский" also has stress on the equivalent third syllable ("ин"), so the Russian comparison is factually wrong on both counts.

2. **Misleading claim about Київ stress.** The module states: "When someone says *Киє́в* with stress on the second syllable, they are using the Russian pronunciation." Standard Russian "Ки́ев" has stress on the FIRST syllable (same position as Ukrainian Ки́їв). The real difference between Ukrainian and Russian forms is the vowel (ї vs е) and final consonant, not stress position. The form "Киє́в" (with є and second-syllable stress) is not standard in either language.

3. **[NEEDS VERIFICATION] Білоус Grade 2 textbook reference.** "a classic Ukrainian riddle from a Grade 2 textbook by Білоу́с" — Білоус is a real surname (VESUM confirms), but I cannot verify a Grade 2 textbook by this author in my textbook corpus. Standard Grade 2 authors are Вашуленко, Большакова, Захарійчук. This may be a fabricated citation by the writer (Gemini).

4. **[NEEDS VERIFICATION] Авраменко attribution for ніколи pair.** "One more powerful pair from Авраменко's Grade 5 textbook: ніколи." The stress pair itself is confirmed by СУМ-11, but the Заболотний наголос section (p.93) lists замок/бігом/сорок as stress pairs — not ніколи. I could not find ніколи in any Авраменко excerpt. Attribution may be fabricated.

No Russianisms, surzhyk, calques, or Russian characters detected. No incorrect gender/case found.

## Exercise Check

**Markers found (4 total):**
1. `<!-- INJECT_ACTIVITY: quiz-stress-syllable -->` — after Наголос section ✓ (matches plan hint: quiz, stress syllable, 8 items)
2. `<!-- INJECT_ACTIVITY: match-stress-pairs -->` — after Наголос section ✓ (matches plan hint: match-up, stress pairs, 4 items)
3. `<!-- INJECT_ACTIVITY: quiz-sentence-type -->` — after Інтонація section ✓ (matches plan hint: quiz, sentence type, 6 items)
4. `<!-- INJECT_ACTIVITY: fill-in-punctuation -->` — after Інтонація section ✓ (matches plan hint: fill-in, punctuation, 6 items)

All 4 plan activity_hints have corresponding markers. Markers are placed after the relevant teaching content, not clustered. Two markers after each major teaching section — well distributed. No issues.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present with correct ordering. All plan vocabulary (required + recommended) appears naturally in prose: наголос, замок pair, кава, вода, столиця, мука, ранок, метро, фотографія. Textbook references (Заболотний p.73, Авраменко p.19) cited. Section pacing proportional. **Deduction:** ULP reference (Season 1, Episode 5 — Pronunciation Trainer) from plan's `references` not cited anywhere in module. |
| 2. Linguistic accuracy | 8/10 | All stress pairs verified correct (СУМ-11). Intonation rules align with textbook pedagogy. Question word rule (falling intonation) correctly taught. **Deduction:** Self-contradictory claim "украї́нська is stressed on the ї — not on the third syllable as in Russian" (ї IS the third syllable; Russian stress is also third syllable). Misleading claim about Київ second-syllable stress being "Russian pronunciation" (Russian Ки́ев is also first-syllable stress). |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow: presents stress concept with textbook citation → demonstrates with 3 real stress pairs → provides 10 practice words with stress positions → culminates in reading aloud with 3-step method. Ukrainian examples appear every 50-80 words (never >100 words of English without Ukrainian). Grammar scope respected (phonetics focus, no morphology creep). The 3-step reading method (поділ на склади → знайди наголос → читай разом) mirrors Grade 1 textbook pedagogy. |
| 4. Vocabulary coverage | 10/10 | All 6 required vocab items from plan used naturally in prose (наголос in opening paragraph, замок pair in stress-meaning section, кава in intonation examples, вода in stress positions, столиця in reading practice as "Київ — столиця України"). All 4 recommended items present (мука pair, ранок, метро, фотографія). Additional contextual vocabulary (бібліотека, аптека) enriches reading practice. |
| 5. Exercise quality | 9/10 | All 4 markers present, correctly typed, and placed after relevant teaching. Each marker matches plan activity_hints in type and focus. Cannot evaluate exercise content (generated by separate YAML tool). Placement is pedagogically sound: stress exercises after stress teaching, intonation exercises after intonation teaching. |
| 6. Engagement & tone | 10/10 | Zero motivational openers or meta-commentary. Opens with action: "Say the word наголос out loud." Concrete cultural enrichment: Grade 2 riddle about замок, identity point about Київ stress. Practical tip: "every time you write a new word in your notes, mark its stress." Tapping rhythm tip in Reading Aloud is creative and embodied. No generic enthusiasm — every claim is grounded in specific examples. |
| 7. Structural integrity | 9/10 | All 4 H2 headings from plan present in correct order. Clean markdown, no stray tags or formatting artifacts. No duplicate summary sections. **Note:** Word count (1805) is 50% over target (1200). While ≥ target satisfies the hard requirement, significant overshoot may need trimming for A1 attention span. |
| 8. Cultural accuracy | 9/10 | Decolonized framing throughout — Ukrainian presented on its own terms, never "like Russian but..." Comparison to French/Czech for stress typology is appropriate (language science, not Slavic hierarchy). The identity paragraph about Київ/українська stress carries the right message. **Deduction:** The specific factual claims in that paragraph are wrong (see Linguistic Accuracy), which undermines the otherwise excellent decolonization approach. |
| 9. Dialogue & conversation quality | 9/10 | Кирилко and Соломійка dialogue: natural situation (friends near a metro station, one asks if it's the metro, then asks where the exit is). Named speakers, culturally appropriate names. Оленка/Тарас dialogue: greetings from Module 1 with intonation overlay. Both dialogues are short but appropriate for A1 phonetics module where dialogues serve as pronunciation practice, not conversation practice. |

## Findings

**[LINGUISTIC ACCURACY] [SEVERITY: critical]**
Location: Наголос section, final paragraph: "украї́нська (Ukrainian) is stressed on the **ї** — not on the third syllable as in Russian."
Issue: Self-contradictory. The letter ї is IN the third syllable (у-кра-їн-ська = syllable 3). The sentence says stress is on ї but NOT on the third syllable. Additionally, Russian "украи́нский" has stress on the equivalent position (third syllable, "ин"), making the Russian comparison factually wrong.
Fix: Remove the false Russian comparison, state the stress position constructively.

**[LINGUISTIC ACCURACY] [SEVERITY: critical]**
Location: Наголос section, final paragraph: "When someone says *Киє́в* with stress on the second syllable, they are using the Russian pronunciation."
Issue: Standard Russian "Ки́ев" also has first-syllable stress. The difference between Ukrainian Київ and Russian Киев is the vowel (ї vs е) and final consonant realization, not stress position. The form "Киє́в" with second-syllable stress is not standard in either language.
Fix: Reframe around the vowel difference (ї vs е), which IS the real Ukrainian-Russian distinction for this word.

**[PLAN ADHERENCE] [SEVERITY: minor]**
Location: Entire module
Issue: ULP reference (Season 1, Episode 5 — Pronunciation Trainer, ukrainianlessons.com/episode5/) from plan's `references` section is not cited or mentioned.
Fix: Not included in `<fixes>` — ULP links are typically added by the ENRICH step.

**[LINGUISTIC ACCURACY] [SEVERITY: minor] [NEEDS VERIFICATION]**
Location: Наголос section, paragraph 2: "a classic Ukrainian riddle from a Grade 2 textbook by Білоу́с"
Issue: Cannot verify a Grade 2 textbook authored by Білоус in the textbook corpus. Standard Grade 2 authors are Вашуленко, Большакова, Захарійчук. Attribution may be fabricated by Gemini.
Fix: Remove specific author/grade attribution, keep the riddle itself.

**[LINGUISTIC ACCURACY] [SEVERITY: minor] [NEEDS VERIFICATION]**
Location: Наголос section, paragraph 4: "One more powerful pair from Авраме́нко's Grade 5 textbook"
Issue: The ніколи stress pair is confirmed real (СУМ-11), but I cannot find it in any Авраменко Grade 5 excerpt. The Заболотний наголос section (p.93) uses замок/бігом/сорок as stress pair examples, not ніколи. Attribution may be fabricated.
Fix: Remove specific textbook attribution, keep the verified stress pair.

**[PEDAGOGICAL QUALITY] [SEVERITY: positive note]**
Location: Reading Aloud section, Оленка/Тарас dialogue: "Як спра́ви? ↘"
Note: The plan's content_outline incorrectly marks "Як справи?" as ↗ (yes/no question), but the module writer correctly used ↘ (falling — question word як signals the question), consistent with the intonation rules taught in the module. Good editorial judgment by the writer.

## Verdict: REVISE

Two critical findings: the українська and Київ stress claims in the identity paragraph contain factual errors that would teach wrong information to learners. Two minor unverifiable textbook attributions should also be cleaned up. All issues are localized to specific sentences and fixable with targeted find/replace. The module is otherwise excellent — strong pedagogy, verified linguistics, good exercises, natural dialogues.

<fixes>
- find: "Stress is also part of Ukrainian identity. The word **Ки́їв** (Kyiv) is stressed on the first syllable — this is the Ukrainian pronunciation. When someone says *Киє́в* with stress on the second syllable, they are using the Russian pronunciation. Similarly, **украї́нська** (Ukrainian) is stressed on the **ї** — not on the third syllable as in Russian. Getting stress right is not just grammar — it is an act of respect for the language and the people who speak it."
  replace: "Stress is also part of Ukrainian identity. The word **Ки́їв** (Kyiv) is stressed on the first syllable, with the uniquely Ukrainian letter **ї** — the Russian form uses a different vowel entirely. Always say and write the Ukrainian **Київ**. The word **украї́нська** (Ukrainian) is stressed on **ї** — the third syllable. Hear it: у-кра-ЇН-ська. Getting pronunciation right is not just grammar — it is an act of respect for the language and the people who speak it."
- find: "There is a classic Ukrainian riddle from a Grade 2 textbook by Білоу́с that captures this perfectly"
  replace: "There is a classic Ukrainian riddle that captures this perfectly"
- find: "One more powerful pair from Авраме́нко's Grade 5 textbook: **ні́коли**"
  replace: "One more powerful pair: **ні́коли**"
</fixes>
