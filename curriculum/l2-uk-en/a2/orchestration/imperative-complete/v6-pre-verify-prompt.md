<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 44: Хай він прочитає! (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- хай (let — particle for 3rd person imperative)
- нехай (let — formal variant)
- наказовий спосіб (imperative mood)
- побажання (wish, blessing)
- кличний відмінок (Vocative case)
- будь / будьте (be — imperative of бути)
- щасливий / щасливою (happy / happy — Instr.f.)
- здоровий / здоровими (healthy / healthy — Instr.pl.)
- ходімо (let's go)
- давайте (let's — suggestion particle)
- спокійний (calm)
- уважний (attentive)
- живи (live — imperative)
- здійснитися (to come true)
- мрія (dream)

## Sections to research

- **Хай і нехай: Наказ для третіх осіб (3rd Person Imperatives)**: Formation: хай/нехай + 3rd person present tense (imperfective) or perfective present form (future meaning). Хай він читає (Let him read). Нехай вона прочитає (Let her read it through).; Uses: permission (Хай іде, я не проти — Let him go, I don't mind), wish (Хай щастить! — Good luck!), indirect command (Нехай вони подзвонять — Have them call).; Хай vs. нехай: нехай is slightly more formal/literary, хай is everyday speech. Both are correct and interchangeable in meaning.
- **Читаймо! Ходімо! Перша особа множини (1st Person Plural Imperatives)**: Formation: verb stem + -мо. From the 2nd person singular imperative: читай → читаймо (let's read), ходи → ходімо (let's go), зробі → зробімо (let's do it), поїдь → поїдьмо (let's go by vehicle).; Alternative with давайте: давайте читати (let's read), давайте поїдемо (let's go). Давайте is softer, more of a suggestion.; Common -мо forms in daily life: Ходімо! (Let's go!), Починаймо! (Let's start!), Зробімо це! (Let's do it!), Поїдьмо! (Let's drive!), Поговорімо (Let's talk).
- **Кличний + наказовий + орудний: Побажання (Vocative + Imperative + Instrumental: Wishes)**: The powerful Ukrainian construction: Vocative (address) + Imperative (command/wish) + Instrumental (what to be/become). Оленко, будь щасливою! (Olenko, be happy!) — Vocative Оленко + imperative будь + Instrumental щасливою.; More examples: Друзі, будьте здоровими! (Friends, be healthy!). Мамо, будь спокійною! (Mom, be calm!). Діти, будьте уважними! (Children, be attentive!).; Blessings and toasts — a living Ukrainian tradition: Будьте здорові! Будь щаслива! Живи довго! These are not just grammar — they are culture.
- **Вид дієслова в наказовому способі (Aspect in Imperatives)**: Imperfective imperative = general instruction, repeated action, or politeness: Читай більше! (Read more — general advice). Пишіть щодня! (Write every day — habitual). Сідайте, будь ласка (Please sit down — polite invitation).; Perfective imperative = specific one-time command with expected result: Прочитай цю статтю! (Read this article — and finish it). Напиши мені! (Write to me — do it). Закрий двері! (Close the door — now).; Negative imperatives — typically imperfective: Не читай це! (Don't read this). Не відкривайте вікно! (Don't open the window). Using perfective in negation can sound harsh or warning-like: Не впади! (Don't fall! — careful!).

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
