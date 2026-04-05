<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 12: Милозвучність у складних контекстах (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- милозвучність (euphony, melodiousness)
- евфонія (euphony (technical term))
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- збіг (cluster, collision)
- прийменник (preposition)
- сполучник (conjunction)
- вживати (to use, to apply)
- складний (complex, compound)
- спрощення (simplification)
- уникати (to avoid)
- мелодійний (melodious)
- межа (boundary)
- правило (rule)

## Sections to research

- **У чи в? Складні випадки (U or V? Complex Cases)**: Review A1 basic rule: у after consonants, в after vowels. Now the exceptions and complex contexts.; At sentence/clause beginnings: В Україні зима холодна (sentence start allows в before vowels). After comma or dash — new phonetic context resets the rule.; With case forms: у школі, в університеті, у місті, в Одесі. The surrounding sounds determine the choice, not the preposition itself.
- **З, із чи зі? Правила перед збігами приголосних (Z, Iz, or Zi?)**: Base rule: з is default. Із before difficult initial clusters (із задоволенням, із сміхом). Зі before з-, с-, ш-, щ- and complex clusters (зі школи, зі мною, зі снігу).; With case forms and pronouns: з ним, з нею, з нами, зі мною (мн- cluster). З Києва, зі Львова (Льв- cluster).; Genitive context (current A2.2 focus): з родини, із сім'ї, зі школи. The genitive preposition context makes euphony practice natural.
- **І чи й? У складних реченнях (I or Y? In Complex Sentences)**: Review: й after vowels (мама й тато), і after consonants (брат і сестра). Now in multi-clause sentences.; After clause boundaries: comma resets the phonetic context. Він прийшов, і ми поїхали (і after comma, new clause). Вона заспівала, й усі заплакали (й because усі starts with vowel? No — after comma, default і is always safe).; With compound subjects and objects: хліб і масло, кава й молоко. Apply the rule to each pair individually.
- **Все разом: мелодійні речення (Putting It All Together)**: Building multi-clause sentences that sound natural: Ми поїхали у Львів із друзями й провели чудовий вихідний.; Reading aloud practice: euphony is about SOUND, not just rules. Read sentences aloud and feel when they flow vs. when they stumble.; Consolidation: all three rules (у/в, з/із/зі, і/й) serve the same principle — милозвучність. Ukrainian actively avoids consonant clusters and vowel collisions at word boundaries.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
