<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 6: My Family (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- сім'я (family) — apostrophe word
- мама (mother)
- тато (father)
- брат (brother)
- сестра (sister)
- бабуся (grandmother)
- дідусь (grandfather)
- мій, моя, моє, мої (my — m/f/n/pl)
- твій, твоя, твоє (your — m/f/n, informal)
- у мене є (I have)
- у тебе є (you have, informal)
- батьки (parents)
- дядько (uncle)
- тітка (aunt)
- дочка (daughter)
- син (son)
- дружина (wife)
- чоловік (man / husband)
- його (his — doesn't change)
- її (her — doesn't change)
- один, одна (one — m/f)
- два, дві (two — m/f)
- чи (or — in questions)
- тільки (only)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Showing phone photos (Anna Ep6-7): — У тебе є брати чи сестри? — Так, у мене є два брати і одна сестра. — Ого! У мене тільки один брат. Як його звати? — Коля.; Dialogue 2 — Family in a photo (Anna Ep7): — Це моя сім'я на фотографії. Класно! Хто це? — Це моя мама Марина. Це мій тато Євген. Це моя сестра Катя і мої брати — Іван і Денис. — А це твоя бабуся? — Так, її звати Тетяна.; Dialogue 3 — Connected speech (Anna Ep10 review pattern): Привіт! Мене звати... Моя мама — вчителька. Мій тато — інженер. У мене є один брат. Combining all A1.1 skills.
- **Сім'я (Family Vocabulary)**: Anna Ep6: Two words for family: сім'я and родина (both used). Core: мама/мати, тато/батько, брат, сестра, син, дочка/донька. Extended: бабуся/баба, дідусь/дід, тітка, дядько. Note: Ukrainian has NO single word for 'grandparents' — always say бабуся і дідусь.
- **У мене є (I have)**: Anna Ep6 pattern: Ukrainian doesn't say 'I have' with a verb. Instead: 'At me there-is' — У мене є брат. For A1, teach only: у мене є, у тебе є (informal), у вас є (formal). Other forms (у нього, у неї, у нас, у них) use genitive pronouns which are A2 grammar — introduce them gradually through dialogues as memorized phrases, not as a paradigm table.; Questions with rising intonation: У тебе є сестра? ↗ Negative: Defer 'У мене немає' to A2 where genitive is taught. For A1, learners answer: Ні. / Ні, у мене тільки один брат. This avoids the pedagogical trap of немає + nominative (*немає брат).; Numbers preview (Anna Ep6): один/одна changes by gender: один брат, одна сестра. два/дві: два брати, дві сестри.
- **Мій, моя, моє (Possessive Pronouns)**: Anna Ep7: Possessives match the gender of the thing possessed. мій брат (m), моя сестра (f), моє місто (n), мої батьки (pl). твій/твоя/твоє/твої (your, informal). його (his — doesn't change), її (her — doesn't change). State Standard note: full paradigm (наш, ваш, їхній) is A2. At A1: мій/твій/його/її in nominative only.
- **Підсумок — Summary**: Self-check: Name 5 family members. Say 'I have a sister.' What's the difference between мій and моя? Introduce your family in 4-5 sentences.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
