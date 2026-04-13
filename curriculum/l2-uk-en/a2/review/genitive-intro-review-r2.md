## Linguistic Scan
No Russianisms, Surzhyk, paronym misuse, or Russian-only characters (`ы`, `э`, `ё`, `ъ`) found.

Problems found:
- The module teaches a false universal rule about `немає`: `This rule works for all words.` and later `commands this grammatical change every single time.` This contradicts the module’s own Ukrainian explanation about indeclinables (`немає метро`).
- The Genitive plural section contains an incorrect rule in English: `If the word ends in a vowel or a soft sign, we add "-їв".`
- The feminine consonant-noun section contains a false rule: `simply add «-і» to the end of the word`, even though its own examples show stem changes (`ніч → ночі`, `сіль → солі`).
- The line `It is so fundamental that you will even see it in famous Ukrainian proverbs.` is not supportable for the example `У природи нема поганої погоди`; local idiom search for `поганої погоди` returned 0 hits, so it should not be taught as a proverb.

## Exercise Check
- Found 5 activity markers, matching the 5 `activity_hints` in the plan.
- Placement is correct: the `quiz` marker follows the absence section, the `fill-in` marker follows singular endings, and the three quantity/plural markers follow the quantity section.
- Marker focuses align semantically with the plan hints.
- No inline DSL exercise blocks are present.
- Exercise logic cannot be audited here because the generated YAML activity content is not included in the prompt.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The three planned sections are present and paced close to budget (`~660`, `~770`, `~770`), and the core objectives are covered with examples like `У мене є старший брат ... у нього немає брата` and `багато друзів, мало часу`; however, the plan references are not cited anywhere in the content (`ULP`, `Заболотний`, `§81` all return 0 hits in the provided text). |
| 2. Linguistic accuracy | 6/10 | Core Ukrainian forms are valid in VESUM (`стола`, `Києва`, `матері`, `ночі`, `грошей`), but the module contains false grammar claims: `This rule works for all words`, `commands this grammatical change every single time`, and `simply add «-і» to the end of the word`. |
| 3. Pedagogical quality | 6/10 | The module follows a PPP-like flow, but several explanations teach contradictory or overgeneralized rules, especially the universal statements about `немає` and the incorrect Genitive-plural rule `If the word ends in a vowel or a soft sign, we add "-їв"`. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears in prose: `родовий відмінок`, `немає`, `багато`, `мало`, `кілька`, `скільки`, `закінчення`, `однина`, `множина`; recommended `кількість` and `відсутність` also appear. |
| 5. Exercise quality | 9/10 | Marker inventory is complete and ordered correctly relative to the teaching sections. Actual answer logic cannot be checked because only injection markers are shown, not the generated YAML exercises. |
| 6. Engagement & tone | 9/10 | The voice is teacherly and clear, with concrete situations (apartment, cinema, classroom) and useful chunks like `немає часу` and `немає сенсу`. |
| 7. Structural integrity | 10/10 | Clean three-part structure, all section headings present, 5 activity markers present, no stray formatting damage, and pipeline word count is 2993, comfortably above the 2000 target. |
| 8. Cultural accuracy | 7/10 | The module avoids “Ukrainian via Russian” framing, but it labels `У природи нема поганої погоди` as something found in `famous Ukrainian proverbs`; that claim is unsupported by the local idiom search and should be softened. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues use named speakers and plausible situations; the opening apartment dialogue directly motivates `немає + Genitive`, and the cinema dialogue introduces `немає грошей` naturally. |

## Findings
- [2. Linguistic accuracy / 3. Pedagogical quality] [SEVERITY: critical]
Location: First section: `When we say the word "немає", the noun after it always changes its ending. This rule works for all words.` Also later: `The word «немає» is absolute and commands this grammatical change every single time.`
Issue: This contradicts the module’s own explanation about indeclinables (`немає метро`) and teaches a false universal rule.
Fix: Limit the statement to declinable nouns and explicitly preserve indeclinables as unchanged.

- [8. Cultural accuracy] [SEVERITY: critical]
Location: First section: `It is so fundamental that you will even see it in famous Ukrainian proverbs.` followed by `У природи нема поганої погоди.`
Issue: The content presents the example as a famous Ukrainian proverb, but that classification is unsupported; local idiom search for `поганої погоди` returned 0 hits.
Fix: Replace `famous Ukrainian proverbs` with a neutral label such as `fixed expressions and example sentences`, or swap the example.

- [2. Linguistic accuracy / 3. Pedagogical quality] [SEVERITY: critical]
Location: Genitive plural section, English explanation: `If the word ends in a vowel or a soft sign, we add "-їв".`
Issue: This is an incorrect rule and does not match the Ukrainian explanation immediately above, which says nouns in `-й` often take `-їв`, while nouns in `-ь` and `-о` can behave differently.
Fix: Rewrite the English sentence to match the Ukrainian explanation.

- [2. Linguistic accuracy / 3. Pedagogical quality] [SEVERITY: critical]
Location: Feminine consonant-noun section: `For all other nouns in this category, simply add «-і» to the end of the word.`
Issue: This is false even in the module’s own examples: `ніч → ночі` and `сіль → солі` are not formed by simply appending `-і`.
Fix: State that these nouns usually have Genitive singular `-і`, but some also change the stem.

- [1. Plan adherence] [SEVERITY: major]
Location: Whole module; explicit search in the provided content returned `ULP: 0`, `Заболотний: 0`, `§81: 0`.
Issue: The plan includes two references, but the module never cites either one, even where `немає` vs `не має` is explained.
Fix: Add a short source cue near the relevant explanations.

## Verdict: REVISE
Multiple critical findings teach wrong grammar or make unsupported cultural claims, so this cannot ship as-is even though the structure, vocabulary coverage, and activity placement are strong.

<fixes>
- find: "> *The Genitive case is a very important topic in Ukrainian grammar. When we say the word \"немає\", the noun after it always changes its ending. This rule works for all words.*"
  replace: "> *The Genitive case is a very important topic in Ukrainian grammar. With declinable nouns, the word \"немає\" normally requires the Genitive form. Indeclinable words like «метро» keep the same form.*"
- find: "The word «немає» is absolute and commands this grammatical change every single time."
  replace: "With declinable nouns, the word «немає» normally triggers this grammatical change."
- find: "It is so fundamental that you will even see it in famous Ukrainian proverbs."
  replace: "It is so fundamental that you will hear it in many fixed expressions and example sentences."
- find: "> *Most masculine nouns receive the \"-ів\" ending. One brother is the Nominative case, and a few brothers is the Genitive case. If the word ends in a vowel or a soft sign, we add \"-їв\". For example, one tram becomes many trams.*"
  replace: "> *Most masculine nouns receive the \"-ів\" ending. One brother is the Nominative case, and a few brothers is the Genitive case. If a noun ends in \"-й\", it often takes \"-їв\", while nouns in \"-ь\" or \"-о\" may follow other patterns. For example, one tram becomes many trams.*"
- find: "Notice that «мати» (mother) is an important exception. It takes the suffix «-ер-» before the ending, becoming «матері». For all other nouns in this category, simply add «-і» to the end of the word."
  replace: "Notice that «мати» (mother) is an important exception. It takes the suffix «-ер-» before the ending, becoming «матері». Other nouns in this category usually have the Genitive singular ending «-і», but some also change the stem: «ніч» → «ночі», «сіль» → «солі», «любов» → «любові»."
- find: "You will often hear Ukrainians use the short form **нема** instead of **немає** in everyday conversations. Both words mean exactly the same thing and both require the Genitive case. Do not confuse **немає/нема** with **не має**: we write **немає/нема** together when it means “there is no / do not have,” but **не має** separately only with personal forms of the verb **мати**."
  replace: "You will often hear Ukrainians use the short form **нема** instead of **немає** in everyday conversations. Both words mean exactly the same thing and both require the Genitive case. Do not confuse **немає/нема** with **не має**: we write **немає/нема** together when it means “there is no / do not have,” but **не має** separately only with personal forms of the verb **мати**. This is the same distinction highlighted in Заболотний Grade 6, §81."
- find: "We will explore quantities later, but first, let us practice the difference between having something and not having it."
  replace: "We will explore quantities later, but first, let us practice the difference between having something and not having it. For a broader overview of other genitive uses, see the Ukrainian Lessons article “10 Uses of Genitive Case.”"
</fixes>