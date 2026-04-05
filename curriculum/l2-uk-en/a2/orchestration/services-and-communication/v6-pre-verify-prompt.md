<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 22: На пошті (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- пошта (post office, mail)
- лист (letter)
- конверт (envelope)
- марка (stamp)
- посилка (parcel, package)
- адреса (address)
- надіслати (to send)
- отримати (to receive)
- відправити (to send, to dispatch)
- листоноша (mail carrier)
- бандероль (small parcel, book post)
- квитанція (receipt)
- одержувач (recipient)
- відправник (sender)
- індекс (postal code)

## Sections to research

- **На пошті: Базова лексика (At the Post Office: Essential Vocabulary)**: Post office vocabulary: пошта, відділення, лист, конверт, марка, посилка, бандероль, квитанція, адреса, індекс.; People: листоноша, одержувач, відправник.; Actions: надіслати/відправити (to send), отримати (to receive), заповнити (to fill out), підписати (to sign).
- **Надіслати листа: Діалоги на пошті (Sending a Letter: Dialogues at the Post Office)**: Dialogue 1: Sending a letter — asking for an envelope and stamps, giving the address, paying. Natural interaction with a postal worker.; Dialogue 2: Sending a parcel to a friend — explaining contents, filling out the form (кому — одержувач, від кого — відправник), asking about delivery time.; Dative in action: Я хочу надіслати листа другові. Дайте мені два конверти. Покажіть мені бланк. Напишіть адресу одержувачеві.
- **Просити, дякувати, допомагати: Давальний у сфері послуг (Requesting, Thanking, Helping: Dative in Services)**: Requesting help: Допоможіть мені заповнити бланк. Покажіть мені, як це зробити. Поясніть мені правила.; Thanking: Дякую вам за допомогу. Дякую листоноші.; Giving advice: Раджу вам надіслати бандероллю. Раджу тобі перевірити адресу.
- **Написати адресу: Давальний у листуванні (Writing an Address: Dative in Correspondence)**: Addressing letters and messages: Кому — дорогому другові Андрію, любій бабусі Олені, шановному професорові Петренку.; Full dative agreement in addresses: possessive + adjective + noun + name all in dative — моєму дорогому братові Михайлові.; Short message writing: Дорогій подрузі! Пишу тобі з Києва. Посилаю тобі маленький подарунок.

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
