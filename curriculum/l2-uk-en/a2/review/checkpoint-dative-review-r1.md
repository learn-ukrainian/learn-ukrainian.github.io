## Linguistic Scan
- Factually wrong grammar claim in Part 3: `"You will frequently use the **давальний відмінок** *(dative case)* when writing short addresses, formal greetings in letters, or email salutations."` This teaches the wrong case for greetings. In Ukrainian letter/email salutations, the addressee is normally in the **кличний відмінок** *(vocative)*, e.g. textbook-style `"Шановна пані Ольго!"`, not dative.

## Exercise Check
Four markers are present and they match the four `activity_hints`:
`quiz-dative-recognition` after Part 1, `fill-in-dative-endings` and `match-up-dative-verbs` after Part 2, and `error-correction-dative` after the error-review section.

Placement is mostly correct:
- The quiz marker follows the recognition section.
- The fill-in and match-up markers follow the form-selection/government section they are meant to test.
- The error-correction marker follows the error-review section.

No inline DSL exercises are present, so exercise logic itself is not inspectable here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Most objectives are covered, but Part 1 was supposed to “distinguish dative from genitive, accusative, and locative”; the Part 1 prose explicitly contrasts only locative (`"A common challenge... with the locative case"`), while accusative appears later in Part 2 and the plan references (`Заболотний`, `Захарійчук`, `Кравцова`) never appear in the prose. |
| 2. Linguistic accuracy | 6/10 | Critical grammar-teaching error: `"formal greetings in letters, or email salutations"` are assigned to dative, but Ukrainian salutations use vocative. |
| 3. Pedagogical quality | 7/10 | Example density is good, but the salutation rule teaches a bad production habit, and the Part 1 recognition section does not fully deliver the promised genitive/accusative contrasts before the quiz marker. |
| 4. Vocabulary coverage | 10/10 | All required hints appear in prose: `давальний відмінок`, `допомагати`, `дякувати`, `подобатися`, `подарувати`, `надіслати`, `потрібно`, `холодно`; recommended `закінчення`, `чергування`, `узгодження` are also used contextually. |
| 5. Exercise quality | 9/10 | Marker count matches the four planned activities, and each marker comes after the relevant teaching block. No inline exercise content is available to audit for distractor logic. |
| 6. Engagement & tone | 9/10 | Concrete teacherly framing (`Secret Santa`, post office) keeps the review readable without heavy fluff. |
| 7. Structural integrity | 10/10 | All main planned H2 sections are present and ordered cleanly; markdown is clean; pipeline word count is 2009, above target. |
| 8. Cultural accuracy | 8/10 | The module is decentered and Ukrainian-focused, but the claim about dative in letter/email greetings misstates a real Ukrainian writing convention. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers and plausible situations rather than anonymous drill lines. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `"You will frequently use the **давальний відмінок** *(dative case)* when writing short addresses, formal greetings in letters, or email salutations."`  
Issue: This teaches the wrong case. Ukrainian greetings/salutations inside letters and emails use the vocative, not the dative.  
Fix: Rewrite the paragraph to distinguish dative recipient/dedication lines from vocative salutations.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Part 1, especially `"A common challenge for learners is confusing the **давальний відмінок** *(dative case)* with the locative case..."` and the three-example block below it.  
Issue: The plan requires Part 1 recognition of dative vs. genitive, accusative, and locative. Part 1 explicitly contrasts only locative; accusative is deferred to Part 2 and genitive is not illustrated there at all.  
Fix: Add one genitive and one accusative recognition example in Part 1 before `quiz-dative-recognition`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `"To consolidate your knowledge, review this summary comparison chart formatting the nominative, genitive, and dative endings for full phrases."`  
Issue: The plan lists three source references, but none are cited anywhere in the prose.  
Fix: Add a brief source sentence tying the review/chart to `Заболотний Grade 10, §157`, `Захарійчук Grade 4, §281`, and `Кравцова Grade 4, §135`.

## Verdict: REVISE
REVISE because there is one critical grammar-teaching error and two major plan-adherence gaps.

<fixes>
- find: |
    You will frequently use the **давальний відмінок** *(dative case)* when writing short addresses, formal greetings in letters, or email salutations. A full dative noun phrase—combining an adjective, a title, and a name—is the standard way to address someone in writing. Be explicitly careful not to use the genitive case for dedications or monuments, a mistake sometimes made through direct translation from other languages. A monument is always dedicated *to* someone.
  replace: |
    You will frequently use the **давальний відмінок** *(dative case)* in recipient lines on envelopes, written dedications, or labels showing who something is for. In actual greetings and salutations inside letters or emails, Ukrainian normally uses the **кличний відмінок** *(vocative case)* instead: **Шановний пане директоре!**, **Дорога Олено!** Be explicitly careful not to use the genitive case for dedications or monuments, a mistake sometimes made through direct translation from other languages. A monument is always dedicated *to* someone.
- find: |
    *   **Ми дали білочці горішки.** *(We gave the squirrel some nuts.)* — **кому?** *(to whom?)* — **давальний відмінок** *(dative case)*.
    *   **Руда шубка на білочці.** *(The red coat is on the squirrel.)* — **на кому?** *(on whom?)* — locative case.
    *   **Я допомагаю сестрі.** *(I help my sister.)* — **кому?** *(to whom?)* — **давальний відмінок** *(dative case)*.
  replace: |
    *   **Ми дали білочці горішки.** *(We gave the squirrel some nuts.)* — **кому?** *(to whom?)* — **давальний відмінок** *(dative case)*.
    *   **Руда шубка на білочці.** *(The red coat is on the squirrel.)* — **на кому?** *(on whom?)* — locative case.
    *   **Я допомагаю сестрі.** *(I help my sister.)* — **кому?** *(to whom?)* — **давальний відмінок** *(dative case)*.
    *   **Я не бачу сестри.** *(I do not see my sister.)* — **кого?** *(whom?)* — genitive after negation, not dative.
    *   **Я бачу сестру.** *(I see my sister.)* — **кого?** *(whom?)* — accusative direct object, not dative.
- find: |
    To consolidate your knowledge, review this summary comparison chart formatting the nominative, genitive, and dative endings for full phrases. Notice how the modifiers and nouns shift together.
  replace: |
    To consolidate your knowledge, review this summary comparison chart formatting the nominative, genitive, and dative endings for full phrases. Notice how the modifiers and nouns shift together. This review follows the core contrasts emphasized in Заболотний Grade 10, §157; Захарійчук Grade 4, §281; and Кравцова Grade 4, §135.
</fixes>