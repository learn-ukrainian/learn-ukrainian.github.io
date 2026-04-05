## Linguistic Scan
No linguistic errors found.

## Exercise Check
- Marker 1: `<!-- INJECT_ACTIVITY: quiz, Possession vs. Absence Drill (`Є` vs. `Немає`), 8 items -->` — Correctly placed after the first section on usage. Matches plan exactly.
- Marker 2: `<!-- INJECT_ACTIVITY: fill-in, Genitive Singular Formation, 8 items -->` — Correctly placed after singular endings instruction. Matches plan exactly.
- Marker 3: `<!-- INJECT_ACTIVITY: match-up, Genitive Plural Formation with Quantity Words, 8 items -->` — Correctly placed after the Genitive plural section. Matches plan exactly.
- Marker 4: `<!-- INJECT_ACTIVITY: match-up, Translate sentences with 'a lot of...' / 'I don't have...', 8 items -->` — Correctly placed after describing the world around us. Matches plan exactly.
- Marker 5: `<!-- INJECT_ACTIVITY: unjumble, Reorder words to form correct genitive phrases with немає and quantity expressions, 6 items -->` — Correctly placed after the final dialogue. Matches plan exactly.

All exercises logically test the preceding instructional content and match the plan's requirements.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module covers almost all plan points, but misses the explicitly required word "очей" from the exception list: "There is also a small group of nouns that take the ending -ей. The most common examples are гостей (of guests), коней (of horses), and plural-only words like грошей (of money)." |
| 2. Linguistic accuracy | 10/10 | All Ukrainian text, including case transformations and examples, is highly accurate with no Surzhyk or Russianisms detected. Case endings are correct. |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow, moving from situations (dialogues) to clear rules and patterns, ending with practice markers. The "Concrete vs. Abstract/Substance" logic is effectively explained. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary words from the plan are integrated naturally throughout the text and examples. |
| 5. Exercise quality | 10/10 | All five injected activity markers exactly match the type, focus, and item counts prescribed in the plan, and are placed logically after the taught concepts. |
| 6. Engagement & tone | 8/10 | Contains some filler meta-commentary that tells instead of showing ("Now, it is time to learn the Genitive case", "Let's look closer at the word «немає»", "Let's look at how the endings change"). |
| 7. Structural integrity | 6/10 | Clean markdown and correctly ordered sections, but the deterministic word count of 3437 significantly exceeds the target budget of 2000. |
| 8. Cultural accuracy | 10/10 | Names and situations are culturally appropriate and natural for Ukrainian contexts. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are multi-turn, natural, and highly contextual ("Ремонт у новій квартирі" is a great setting for practicing absent items). |

## Findings
[Plan adherence] [Minor]
Location: Section "Коли є багато або мало", paragraph "Чоловічий рід (Masculine Nouns)"
Issue: The text omitted the word "очей" from the `-ей` exception list, which was explicitly required by the plan ("гостей, коней, очей").
Fix: Add "**очей** *(of eyes)*" to the list of examples.

[Engagement & tone] [Minor]
Location: Section "Родовий відмінок: Коли чогось немає", paragraph 1
Issue: Meta-commentary filler that tells instead of shows ("You already know... Now, it is time to learn...").
Fix: Remove the unnecessary introductory sentences and directly state the case usage.

[Engagement & tone] [Minor]
Location: Section "Читаємо українською: Нова квартира", paragraph below dialogue
Issue: Generic meta-commentary filler ("Let's look closer at the word «немає».").
Fix: Replace with a direct declarative sentence ("The word «немає» has a specific grammatical role.").

[Engagement & tone] [Minor]
Location: Multiple sections ("Let's look at how the endings change...", "Let's start with masculine nouns...", "Let's look at some common feminine examples...")
Issue: Repetitive "Let's look at..." meta-commentary throughout the module.
Fix: Replace with more direct transitional sentences.

[Structural integrity] [Major]
Location: Entire module
Issue: The deterministic word count (3437 words) is significantly above the target budget (2000 words), exceeding the 10% variance limit.
Fix: Trim unnecessary meta-commentary ("This is one of the most debated parts...") to begin tightening the word count.

## Verdict: REVISE
The module is pedagogically strong and linguistically accurate, but requires minor revisions to fix meta-commentary, correctly include all plan-mandated exceptions ("очей"), and address the inflated word count.

<fixes>
- find: "You already know the Nominative case (Називний відмінок) for naming things and the Accusative case (Знахідний відмінок) for the direct object of an action. Now, it is time to learn the Genitive case (Родовий відмінок). This is one of the most frequently used cases in the Ukrainian language."
  replace: "The Genitive case (Родовий відмінок) is one of the most frequently used cases in the Ukrainian language."
- find: "Let's look closer at the word «немає»."
  replace: "The word «немає» has a specific grammatical role."
- find: "Let's look at how the endings change when we use the word «немає» *(there is no)* to express that something is missing."
  replace: "Here is how the endings change when we use the word «немає» *(there is no)* to express that something is missing."
- find: "There is also a small group of nouns that take the ending **-ей**. The most common examples are **гостей** *(of guests)*, **коней** *(of horses)*, and plural-only words like **грошей** *(of money)*."
  replace: "There is also a small group of nouns that take the ending **-ей**. The most common examples are **гостей** *(of guests)*, **коней** *(of horses)*, **очей** *(of eyes)*, and plural-only words like **грошей** *(of money)*."
- find: "Let's start with masculine nouns, which are generally the most straightforward."
  replace: "Masculine nouns are generally the most straightforward."
- find: "Let's look at some common feminine examples where the vowel simply disappears:"
  replace: "Here are some common feminine examples where the vowel simply disappears:"
- find: "This is one of the most debated parts of Ukrainian grammar even among native speakers! However, focusing on the \"Concrete vs. Abstract/Substance\" logic will guide you to the right answer most of the time."
  replace: "Focusing on the \"Concrete vs. Abstract/Substance\" logic will guide you to the right answer most of the time."
</fixes>
