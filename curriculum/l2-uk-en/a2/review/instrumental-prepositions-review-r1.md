## Linguistic Scan
Errors found:
1. Calque/stylistic error: The verb "знаходиться" is repeatedly used to mean "розташований" (is located/situated), which is a common Russianism ("находится").
2. Table example error: "дверима" is used to illustrate the "-ями" (soft plural) Instrumental ending. However, "двері" is an exception that ends in "-има". 
3. Visual mismatch: "над музеєм" is used to illustrate the literal "-ем" ending, which can be visually confusing to an A2 learner since it is spelled with "-єм".

## Exercise Check
All exercise markers are present, correctly placed, and perfectly match the plan's `activity_hints`:
- `<!-- INJECT_ACTIVITY: match-up -->` follows "Просторові прийменники" section (Focus: Match prepositions).
- `<!-- INJECT_ACTIVITY: true-false -->` follows "Описуємо кімнату" section (Focus: Judge whether location descriptions match a room diagram).
- `<!-- INJECT_ACTIVITY: quiz -->` follows "Часове значення" section (Focus: Distinguish spatial vs. temporal meaning).
- `<!-- INJECT_ACTIVITY: fill-in -->` follows "Практика: Де? Коли?" section (Focus: Complete location sentences).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers all required sections ("Просторові прийменники", "Описуємо кімнату", "Часове значення", "Практика"). Integrates the planned museum dialogue flawlessly. Exceeds the target word count appropriately. |
| 2. Linguistic accuracy | 8/10 | General grammar is strong. However, uses the calque "знаходиться" multiple times instead of "розташований" or "є". The table incorrectly uses "дверима" to illustrate the "-ями" ending. |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of Location vs. Direction cases and spatial vs. temporal meanings. Minor deduction for introducing the vocabulary "кут" (Instrumental "кутом") but then practicing the diminutive locative "у кутку" in the text, and using "музеєм" (spelled with є) to illustrate the literal -ем ending rule. |
| 4. Vocabulary coverage | 10/10 | Integrates all required words (над, під, перед, за, між, стіл, будинок, ліжко, стіна, обід) naturally in prose. All recommended words are also seamlessly present. |
| 5. Exercise quality | 10/10 | All 4 exercise markers are accurately placed right after the corresponding concepts, meeting the exact count and focus from the plan's `activity_hints`. |
| 6. Engagement & tone | 10/10 | The writer adopts a warm, encouraging teacher persona ("Imagine you are visiting a beautiful museum", "Language is highly metaphorical"). Tone is constructive and avoids gamified clichés. |
| 7. Structural integrity | 10/10 | Uses clean Markdown, includes proper H2 headings that map to the outline, effectively utilizes callout blocks, and safely exceeds the minimum word count (2572 vs 2000). |
| 8. Cultural accuracy | 10/10 | Correctly identifies and warns learners against Russianisms like "по розкладу", actively teaching them to use the authentic Ukrainian phrasing ("за розкладом"). |
| 9. Dialogue & conversation quality | 10/10 | Multi-turn, natural dialogues. Roommates placing furniture or friends describing a neighborhood feel realistic and appropriately contextualize the grammar. |

## Findings
[DIMENSION] 2. Linguistic accuracy [SEVERITY: critical]
Location: Table under "Просторові прийменники: Де це?" -> "| **-ами** (тверда / hard)<br>**-ями** (м'яка / soft) | між вікн**ами**<br>над двер**има** |"
Issue: The table uses "над дверима" as an example of the "-ями" (soft plural) ending. "Двері" is pluralia tantum and its instrumental form is "дверима", which ends in "-има" (a historical exception), not "-ями". This teaches learners a false pattern.
Fix: Change the example to a true soft plural noun like "морями".

[DIMENSION] 3. Pedagogical quality [SEVERITY: major]
Location: Table under "Просторові прийменники: Де це?" -> "| **-ом** (тверда / hard)<br>**-ем** (м'яка / soft) | під стол**ом**<br>над музе**єм** |"
Issue: The table uses "над музеєм" to illustrate the soft masculine ending "-ем". While phonetically correct, the spelling is "-єм" (музей + ем = музеєм). This is visually confusing for A2 learners trying to map the literal "-ем" spelling rule directly.
Fix: Change "над музеєм" to "перед гаражем" to clearly show the literal "-ем" ending.

[DIMENSION] 2. Linguistic accuracy [SEVERITY: major]
Location: Multiple sentences including "А кафе знаходиться за музеєм.", "Що знаходиться під стелею?", "Магазин знаходиться за будинком.", "* Сад знаходиться за будинком"
Issue: The verb "знаходиться" is a common calque from Russian ("находится") when used to mean "is located" or "is situated". In a high-quality Ukrainian curriculum, it should be replaced with "розташований", "є", or omitted.
Fix: Replace with "розташоване", "є", or "розташований" depending on the noun's gender/context.

[DIMENSION] 3. Pedagogical quality [SEVERITY: minor]
Location: "А велика коричнева шафа стоїть у кутку."
Issue: The module introduces the vocabulary word "кут" and explicitly teaches its instrumental form "кутом". However, in the practice text, it uses "у кутку", which comes from the diminutive "куток". This is a slight pedagogical mismatch for the learner.
Fix: Change "у кутку" to "у куті" to align with the base word "кут" taught immediately above.

## Verdict: REVISE
The module is extremely strong in structure, tone, and pedagogy, and effectively warns learners against known grammatical Russianisms. However, it contains a critical factual error in a grammar table regarding the "-ями" ending, uses the stylistically poor calque "знаходиться" repeatedly, and has minor pedagogical mismatches in vocabulary presentation. These must be fixed via the find/replace block before publishing.

<fixes>
- find: "| **Множина** (Plural) | Орудний (Instr.) | **-ами** (тверда / hard)<br>**-ями** (м'яка / soft) | між вікн**ами**<br>над двер**има** |"
  replace: "| **Множина** (Plural) | Орудний (Instr.) | **-ами** (тверда / hard)<br>**-ями** (м'яка / soft) | між вікн**ами**<br>над мор**ями** |"
- find: "| **Чоловічий** (Masc.) | Орудний (Instr.) | **-ом** (тверда / hard)<br>**-ем** (м'яка / soft) | під стол**ом**<br>над музе**єм** |"
  replace: "| **Чоловічий** (Masc.) | Орудний (Instr.) | **-ом** (тверда / hard)<br>**-ем** (м'яка / soft) | під стол**ом**<br>перед гараж**ем** |"
- find: "> **Гід музею:** Лавка *(bench)* стоїть **під деревом** *(under the tree)* у саду. А кафе знаходиться **за музеєм** *(behind the museum)*."
  replace: "> **Гід музею:** Лавка *(bench)* стоїть **під деревом** *(under the tree)* у саду. А кафе розташоване **за музеєм** *(behind the museum)*."
- find: "Що знаходиться під стелею? **Під стелею** висить яскрава лампа."
  replace: "Що є під стелею? **Під стелею** висить яскрава лампа."
- find: "Магазин знаходиться **за будинком**. Це дуже зручно для нас."
  replace: "Магазин розташований **за будинком**. Це дуже зручно для нас."
- find: "*   Сад знаходиться **за будинком** *(behind the house — location, Instrumental)*."
  replace: "*   Сад розташований **за будинком** *(behind the house — location, Instrumental)*."
- find: "А велика коричнева шафа стоїть у кутку."
  replace: "А велика коричнева шафа стоїть у куті."
</fixes>
