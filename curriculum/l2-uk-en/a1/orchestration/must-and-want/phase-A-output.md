===RESEARCH_START===

# Дослідження: Must and Want

## State Standard Reference
§1.1.2.2 (Діалогічне мовлення): "дуже прості вказівки про можливість отримати їжу, воду, першу допомогу тощо: Будь ласка, дайте воду / чай / каву / сік. Я хочу їсти / пити. Де їдальня / кафе / ресторан? Мені треба лікаря / ліки / швидку допомогу."
Alignment: This module directly fulfills the A1 communicative mandate to express desires (хочу) and basic necessities (треба/потрібен) in practical survival contexts (getting food, medical help).

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| треба | High (GRAC Corpus) | мені треба, треба йти, що треба |
| потрібно | Moderate (GRAC) | потрібно зробити, дуже потрібно |
| повинен | Mod-High (GRAC) | я повинен, ми повинні, він повинен був |
| хотіти | Very High (Top 50) | хочу їсти, хочу сказати, я б хотів |

## Cultural Hooks
1. **The Dative Mindset**: Ukrainian conceptually frames states of necessity not as something you "own" (like English "I have a need"), but as a state that happens *to* you (Мені треба - To me it is necessary). This emphasizes reception of a state over possession.
2. **Guest Etiquette**: A practical way to show intensity differences. Taking off shoes inside is an impersonal necessity ("Треба роззуватися" - it's just how the world works here), but bringing a gift or flowers is a stronger social duty ("Гість повинен принести...").

## Common Learner Errors
1. **Case mismatch with треба**: `Я треба` instead of `Мені треба` — applying English Nominative (Subject-Verb-Object) logic instead of the Ukrainian Dative experiencer pattern.
2. **Gender mismatch with повинен**: Female speakers defaulting to the masculine `повинен` instead of `повинна` (treating it as an invariable modal like the English "must").
3. **Case confusion after хотіти**: Using Nominative for the object (`Я хочу кава`) instead of Accusative (`Я хочу каву`).

## Cross-References
- Builds on: a1-45 (Can and Know How)
- Prepares for: a1-47 (Imperative and Requests)

## Notes for Content Writing
- **Decolonization**: Avoid using English as the universal benchmark. Frame the Dative experiencer pattern as a core, authentic feature of the Ukrainian language's worldview, not as a "weird exception" to the rules.
- **Scaffolding**: Adhere to the A1 immersion policy (10-50%). Since these grammar structures differ significantly from English, provide clear English scaffolding to explain the structural difference between `Мені треба` and `Я повинен` before giving Ukrainian examples.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Треба / Потрібно"
    words: 500
    points:
      - "Start with English scaffolding: Explicitly explain the 'It is necessary to...' concept in English, strictly following A1 scaffolding rules."
      - "Create an H3 to introduce the impersonal construction: Треба + infinitive (Треба працювати). Emphasize that 'треба' is invariable."
      - "Create an H3 for the Dative experiencer pattern. Provide a simple table mapping English 'I/You' to Ukrainian Dative pronouns (мені, тобі, йому, їй, нам, вам, їм) used with 'треба'."
      - "Introduce 'потрібно' as a slightly more formal, written synonym of 'треба'."
      - "Create an H3 for short adjectives: потрібен (m), потрібна (f), потрібне (n), потрібні (pl). Explain they agree with the *needed noun*, not the speaker (Мені потрібна допомога)."
  - section: "Повинен"
    words: 400
    points:
      - "Introduce personal obligation: Subject + повинен + infinitive. Contrast structurally with 'треба' (requires Nominative subject, not Dative)."
      - "Provide a clear H3 paradigm table for gender/number agreement: повинен (m), повинна (f), повинне (n), повинні (pl)."
      - "Address the common error: explicitly remind female learners to use 'я повинна', not 'я повинен'."
      - "Explain semantic nuance: 'повинен' implies strong personal duty or moral obligation. Contrast with the general necessity of 'треба'."
  - section: "Хотіти"
    words: 400
    points:
      - "Provide an H3 table for the full present tense conjugation of 'хотіти'. Highlight the irregular stem change (хот- → хоч-)."
      - "Explain the two common syntactic patterns with examples: хочу + infinitive (Я хочу спати) vs хочу + Accusative object (Я хочу воду)."
      - "Introduce the polite conditional variant: 'Я б хотів / Я б хотіла' (I would like). Provide a dialogue snippet in a café context."
  - section: "Порівняння"
    words: 400
    points:
      - "Provide a 3-way contrast summary table: треба (impersonal necessity) vs повинен (personal duty) vs хочу (personal desire)."
      - "Integrate the 'Guest Etiquette' cultural hook: taking off shoes ('треба' - impersonal rule) vs bringing a gift ('повинен' - social duty)."
      - "Show contextual contrast using the same subject: Я хочу працювати (desire) vs Мені треба працювати (financial need) vs Я повинен працювати (duty)."
  - section: "Практика"
    words: 300
    points:
      - "Include situation drills: Present 3 short scenarios (being sick, at a café, visiting a friend) and ask which modal fits best."
      - "Provide 2 short role-play mini-dialogues demonstrating these modals in everyday conversations."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Lightweight Research
**Friction Type**: BUG
**Raw Error**: `error: The argument '--threads <NUM>' requires 1 values, but 2 were provided` when using `grep_search`.
**Self-Correction**: Switched to `run_shell_command("rg -n '...'")` instead to bypass the bug with the custom search tool.
**Proposed Tooling Fix**: Fix the `--threads` argument injection bug in the `grep_search` and `search_file_content` tools within the agent's MCP/environment.
===FRICTION_END===
