## Linguistic Scan
- **Russianisms/Calques:** Found the calque **"близько від"**, which is a literal translation of the Russian "близко от". In Ukrainian, "близько" either takes the preposition "до" (близько до роботи) or takes the genitive directly. "Недалеко від" is also correct. 
- **Tool Note:** The 53 words marked as "NOT IN VESUM" in the verification output were flagged due to the presence of stress marks (combining acute accents) which split the tokens in the tool's regex (e.g., `Апте́ка` -> `Апте`, `ка`). The underlying words themselves are correct and valid.

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-directions -->` (matches plan: fill-in, directions) — Present.
- `<!-- INJECT_ACTIVITY: quiz-de-kudy -->` (matches plan: quiz, Де or Куди) — Present.
- `<!-- INJECT_ACTIVITY: fill-in-transport -->` (matches plan: fill-in, transport) — Present.
- `<!-- INJECT_ACTIVITY: match-navigation -->` (matches plan: match-up, navigation) — Present.
All exercises test the immediately preceding concepts correctly and match the `activity_hints` exactly.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The module is only ~600 words long, missing the 1200 target by 50%, despite the fake `Deterministic word count: 1287 words` tag. Furthermore, it completely ignored the specific `dialogue_situations` plan: "Walking tour of Lviv old town — going from Площа Ринок to Оперний театр to Високий замок... Звідки прийшли? З замку." |
| 2. Linguistic accuracy | 8/10 | Taught the Russian calque "близько від" instead of "близько до" or "недалеко від": "Парк близько від роботи." |
| 3. Pedagogical quality | 8/10 | Explicitly taught a calque as a grammatical rule to memorize: "The chunks далеко від and близько від are followed by genitive case." Also has a counting error: claims "The question type shifts six times" but only brackets 4 questions. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items (пішки, хвилина, район, центр, вибачте, дістатися, ідіть, їдьте, поруч) are integrated naturally. |
| 5. Exercise quality | 10/10 | All 4 injection markers match the plan perfectly and are placed well. |
| 6. Engagement & tone | 9/10 | Solid tone, though the commute description is a bit transactional/robotic. |
| 7. Structural integrity | 6/10 | Missed the target word count by a massive margin (~600 vs 1200) and included a false deterministic count at the end. |
| 8. Cultural accuracy | 9/10 | Good integration of Kyiv and Lviv locations (Хрещатик, Площа Ринок). |
| 9. Dialogue & conversation quality | 7/10 | Dialogues are very transactional. It missed the opportunity for the richer 3-way Lviv walking tour conversation requested in the plan. |

## Findings

[Plan adherence] [major]
Location: `Deterministic word count: 1287 words` and overall length
Issue: The module is only ~600 words long, missing the 1200 word target by 50%. The deterministic word count string at the bottom is falsely reporting 1287 words. Section budgets (300 words each) were completely ignored.
Fix: Add `insert_after` blocks to expand content, specifically including the missing Lviv walking tour.

[Linguistic accuracy] [critical]
Location: `- **далеко від** / **близько від** (far from / near) → Школа **далеко від** дому. Парк **близько від** робо́ти.` and `The chunks **далеко від** and **близько від** are followed by genitive case.`
Issue: "Близько від" is a literal calque of the Russian "близко от". In Ukrainian, "близько" takes "до" (близько до роботи) or directly takes the genitive (близько роботи). Teaching "близько від" as a fixed chunk is teaching a Russianism.
Fix: Change "близько від" to "близько до" in the examples and the explanatory note.

[Plan adherence] [major]
Location: `Three example outputs for different situations:`
Issue: The plan explicitly requested a dialogue setting: "Walking tour of Lviv old town — going from Площа Ринок to Оперний театр to Високий замок... Звідки прийшли? З замку." This was completely omitted, and the Lviv locations were just stuffed into a generic paragraph without the "Звідки?" mechanic.
Fix: Insert the missing Lviv dialogue at the end of the "My Neighborhood" section to fulfill the plan requirement and expand the word count.

[Pedagogical quality] [minor]
Location: `The question type shifts six times in this short passage — and that is completely natural.`
Issue: The passage only explicitly brackets and shifts between four `(де?)` and `(куди?)` questions. Saying it shifts six times is a counting error that might confuse learners trying to find the other two.
Fix: Change "six times" to "four times".

## Verdict: REVISE
The module contains a critical linguistic error (teaching a calque as a grammatical rule) and severely misses the word count target and planned Lviv dialogue. It requires targeted fixes to correct the Ukrainian and expand the content.

<fixes>
- find: "The question type shifts six times in this short passage"
  replace: "The question type shifts four times in this short passage"
- find: "- **далеко від** / **близько від** (far from / near) → Школа **далеко від** дому. Парк **близько від** робо́ти."
  replace: "- **далеко від** / **близько до** (far from / near to) → Школа **далеко від** дому. Парк **близько до** робо́ти."
- find: "The chunks **далеко від** and **близько від** are followed by genitive case. At this stage, memorize them as fixed phrases with common nouns: далеко від дому, близько від роботи, далеко від зупинки."
  replace: "The chunks **далеко від** and **близько до** are followed by genitive case. At this stage, memorize them as fixed phrases with common nouns: далеко від дому, близько до роботи, далеко від зупинки."
- insert_after: "The sentence frames stay identical — only the details change."
  content: |
    
    ### Екску́рсія (Walking Tour)
    
    You can also use these cases when walking around a city. Let's imagine a walking tour in the old town of Lviv. We start at the main square, go to the theater, and then up to the castle. We will also add **зві́дки?** (from where?), which takes the genitive case.
    
    > — **Гід:** Де ми за́раз? *(Where are we now?)*
    > — **Тури́сти:** На пло́щі Ри́нок. *(On Rynok Square.)*
    > — **Гід:** Пра́вильно. Куди́ йдемо́ да́лі? *(Correct. Where are we going next?)*
    > — **Туристи:** В О́перний теа́тр. *(To the Opera Theater.)*
    > — **Гід:** А зві́дки ми прийшли́? *(And where did we come from?)*
    > — **Туристи:** З Висо́кого за́мку. *(From the High Castle.)*
    
    Notice the three-part system:
    - **Де?** (Where at?) → **На пло́щі** (Locative)
    - **Куди?** (Where to?) → **В теа́тр** (Accusative)
    - **Зві́дки?** (From where?) → **З за́мку** (Genitive)
    
    This triangle of location (at, to, from) is the foundation of Ukrainian movement.
- insert_after: "The phrase **на розі** (at the corner) is a locative chunk — learn it as a fixed unit."
  content: |
    
    When listening to directions, pay attention to the order of actions. Ukrainians often use imperative verbs in a chain. For example, **ідіть прямо, а потім поверніть наліво** (go straight, and then turn left). If you are lost, simply asking **Де центр?** (Where is the center?) or **Де метро?** (Where is the metro?) is often enough to get a helpful point in the right direction.
- insert_after: "5. Where do you live? What is near your house? Say it in two sentences. — *(Free production using Я живу на... Біля мого дому є...)*"
  content: |
    
    6. How do you ask "Where did we come from?" — *Звідки ми прийшли?*
    
    ### Cultural Note on City Layouts
    When you ask for directions in a Ukrainian city, you might hear references to landmarks rather than street names. People often say things like **біля парку** (near the park), **за церквою** (behind the church), or **біля пам'ятника** (near the monument). Memorizing key city vocabulary like **площа** (square), **ринок** (market), and **зупинка** (stop) will help you navigate even if you don't catch the exact street name.
</fixes>
