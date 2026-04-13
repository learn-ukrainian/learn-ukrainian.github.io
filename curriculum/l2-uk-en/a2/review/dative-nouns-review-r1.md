## Linguistic Scan
No Russianisms, Surzhyk, calques, paronyms, or forbidden Russian characters found.

Factual grammar error:
- Feminine section: `In Ukrainian, the consonants **г**, **к**, and **х** cannot stand directly before the vowel **-і**.` This is too absolute and false. The alternation applies in the specific dative/locative patterns being taught, not everywhere in Ukrainian. VESUM confirms native words with `гі`, `кі`, `хі` such as `гільза`, `кіт`, `хімія`.

## Exercise Check
Markers found: `fill-in-dative-masculine`, `quiz-feminine-alternation`, `group-sort-dative-gender`, `match-up-verb-phrases`, `unjumble-dative-syntax`.

They match the 5 `activity_hints` types in the plan and appear after the relevant teaching sections. No inline DSL exercises are present here, so downstream distractor logic cannot be audited from this artifact alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Core content_outline points are covered, but search confirms 0 occurrences of `Заболотний`, `Глазова`, and `Кравцова` in the module text, and recommended terms `відміна`, `чергування`, `одержувач` are absent. |
| 2. Linguistic accuracy | 7/10 | Incorrect claim: `In Ukrainian, the consonants **г**, **к**, and **х** cannot stand directly before the vowel **-і**.` |
| 3. Pedagogical quality | 6/10 | The module opens with a long English theory block (`Welcome to the Dative case... In this section, we will focus entirely on masculine nouns.`) before the first Ukrainian example, which weakens PPP-style presentation. |
| 4. Vocabulary coverage | 8/10 | All required plan words appear in prose, but recommended vocabulary `відміна`, `чергування`, and `одержувач` is missing. |
| 5. Exercise quality | 9/10 | All 5 planned exercise types are represented by markers and placed after the relevant sections; no clustering problem. |
| 6. Engagement & tone | 5/10 | Repeated filler/generic enthusiasm: `Mastering them is a key step in speaking beautiful, authentic Ukrainian.` and `a fundamental, natural phonological law... beautifully.` |
| 7. Structural integrity | 10/10 | All four H2 sections are present and ordered correctly; pipeline word count is 2826, so the module is safely above target. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing; Ukrainian is presented on its own terms with locally appropriate examples. |
| 9. Dialogue & conversation quality | 9/10 | The post-office dialogue uses named speakers and directly matches the plan’s situation: `Студентові Петренку — підручник. Сестрі Олені — листівка. А дитині — іграшка.` |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `In Ukrainian, the consonants **г**, **к**, and **х** cannot stand directly before the vowel **-і**.`  
Issue: This teaches a false general rule. The alternation is relevant to the dative/locative forms being taught, not to all Ukrainian words before `і`.  
Fix: Rewrite the rule as a case-form alternation rule, not a universal phonotactic ban.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: whole module; search confirms no occurrences of `Заболотний`, `Глазова`, or `Кравцова`  
Issue: The plan’s reference base is not integrated into the prose at all.  
Fix: Add brief, natural reference mentions in the masculine, feminine, and case-contrast sections.

[PLAN ADHERENCE] [SEVERITY: minor]  
Location: whole module; search confirms 0 occurrences of `відміна`, `чергування`, `одержувач`  
Issue: Three recommended plan terms are never used, despite the lesson explicitly teaching those concepts.  
Fix: Introduce `відміна` in the masculine overview, `чергування` in the feminine alternation rule, and `одержувач` in the sentence-pattern section.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Welcome to the Dative case... In this section, we will focus entirely on masculine nouns.`  
Issue: The lesson starts with a long English-first explanation before showing Ukrainian patterning, which weakens presentation-by-example.  
Fix: Compress the opening into a shorter rule-focused introduction.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `Mastering them is a key step in speaking beautiful, authentic Ukrainian.` and `This is not a random exception or an annoying irregularity. It is a fundamental, natural phonological law of the Ukrainian language that makes the words flow much more smoothly and beautifully.`  
Issue: This is filler and generic language-praise rather than teaching.  
Fix: Replace with concrete, instructional phrasing.

## Verdict: REVISE
The module is structurally complete and mostly accurate, but it contains one critical grammar overstatement and several quality issues that need direct fixes. Because there are identified errors and dimensions below 9, this cannot pass as-is.

<fixes>
- find: "Welcome to the Dative case, or the **давальний відмінок** in Ukrainian. The name of this case comes from the verb meaning \"to give\". It answers the questions **кому?** (to whom?) and **чому?** (to what?). The primary function of the Dative case is to designate the recipient of an action. When you give something, show something, or explain something, the person receiving that action takes the Dative case. If you give a gift to a student, the student is the recipient and takes a specific ending. If you give it to a sister, she takes a different ending. In this section, we will focus entirely on masculine nouns."
  replace: "The **давальний відмінок** answers **кому?** (to whom?) and **чому?** (to what?) and usually marks the recipient of an action. In this section, we focus on masculine nouns and their main dative endings."

- find: "Let us focus on masculine nouns, which belong to the second declension."
  replace: "Let us focus on masculine nouns, which belong to the second declension, or **друга відміна**. As Заболотний notes, these nouns have parallel dative endings."

- find: "There is one crucial phonetic rule you must remember when forming the Dative case for feminine nouns. In Ukrainian, the consonants **г**, **к**, and **х** cannot stand directly before the vowel **-і**. When you add the **-і** ending to a stem that ends in one of these letters, the consonants undergo a mandatory, predictable shift."
  replace: "As Глазова explains, there is one crucial **чергування** pattern to remember when forming the Dative case for feminine nouns. In these dative forms, stems ending in **г**, **к**, or **х** usually alternate before the ending **-і**. When you add the **-і** ending to a stem that ends in one of these letters, the consonants often undergo a predictable shift."

- find: "**Consonant alternation rule** — Before the vowel **-і**, the sounds **г**, **к**, and **х** always change to **з**, **ц**, and **с**."
  replace: "**Consonant alternation rule** — In dative and locative forms like **книзі**, **руці**, and **мусі**, stems in **г**, **к**, and **х** alternate to **з**, **ц**, and **с** before **-і**."

- find: "The Dative case perfectly marks the recipient or the indirect object in your sentences, especially when using common verbs of giving and communicating."
  replace: "The Dative case perfectly marks the recipient, or **одержувача**, and the indirect object in your sentences, especially when using common verbs of giving and communicating."

- find: "It is crucial not to confuse the Dative case, which marks a destination or recipient, with the Genitive case, which indicates possession or absence."
  replace: "As Кравцова also emphasizes when distinguishing similar case endings, it is crucial not to confuse the Dative case, which marks a destination or recipient, with the Genitive case, which indicates possession or absence."

- find: "Mastering them is a key step in speaking beautiful, authentic Ukrainian."
  replace: "Mastering them helps you sound more natural in careful Ukrainian."

- find: "This is not a random exception or an annoying irregularity. It is a fundamental, natural phonological law of the Ukrainian language that makes the words flow much more smoothly and beautifully."
  replace: "This is a regular consonant alternation pattern that appears in several noun forms in Ukrainian."
</fixes>