**Audit PASSED.** All 17 pedagogy violations and 2 density issues are resolved. Here's a summary of what was fixed:

### Activities YAML (`the-instrumental-i-accompaniment.yaml`)

| Violation | Fix |
|---|---|
| **Quiz Q2-Q6, Q8, Q9**: prompts too short (4 words) | Expanded all prompts to 5-8 words with natural context |
| **Quiz Q8**: duplicate `explanation` key + broken Львовом item | Replaced with proper euphony item (зі знайомими — зн- cluster) |
| **Unjumble items 1-6**: 4-5 words (target 7-10) | Expanded all sentences to 7-8 words with prepositional phrases |
| **Match-up "Дії та люди"**: 8 pairs (target 10-12) | Added 4 pairs: Спілкуватися, Знайомитися, Обідати, Святкувати → 12 pairs |
| **Select**: 3 items (minimum 6) | Added 3 items testing plural Instrumental, preposition requirement, feminine endings → 6 items |
| **Cloze**: 10 blanks (minimum 12) | Extended passage with 2 new sentences + blanks (з Іваном, з родиною) → 12 blanks |
| **Schema violation**: duplicate key + select minItems | Both resolved by above fixes |

### Vocabulary YAML (`the-instrumental-i-accompaniment.yaml`)

| Violation | Fix |
|---|---|
| **Metalanguage terms** missing | Added іменник, прикметник, називний, орудний, займенник with translations and notes |

**Final status**: 7 gates pass, 0 fail, overall **PASS**.