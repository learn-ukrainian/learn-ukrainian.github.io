<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **33: Around the City** (A1, A1.5 [Places]).

**Word target: 1200 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: a1-033
level: A1
sequence: 33
slug: around-the-city
version: '1.3'
title: Around the City
subtitle: Де/куди + directions — navigating in Ukrainian
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Combine Де? (locative) and Куди? (accusative) in real navigation
- Give and follow simple directions
- Describe your neighborhood and daily routes
- Synthesize M28-M32 skills in connected urban communication
dialogue_situations:
- setting: Walking tour of Lviv old town — going from Площа Ринок (f, main square)
    to Оперний театр (m, Opera house) to Високий замок (m, High Castle). Де ми? На
    площі. Куди далі? В театр. Звідки прийшли? З замку.
  speakers:
  - Гід (guide)
  - Туристи
  motivation: Де/Куди/Звідки with площа(f), театр(m), замок(m), парк(m)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Asking for directions: — Вибачте, як дістатися до бібліотеки? —
    Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте
    на метро до центру. Combines directions + transport + city places.'
  - 'Dialogue 2 — Describing your route: — Як ти дістаєшся на роботу? — Спочатку йду
    на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п''ять
    хвилин. Робота в офісі на площі. Daily route using sequence words + transport
    + places.'
- section: Де і куди разом (Where and Where To Together)
  words: 300
  points:
  - 'Real navigation uses both cases together: Я зараз у парку (де? — locative). Я
    йду в магазин (куди? — accusative). Магазин на вулиці Шевченка (де? — locative).
    Потім їду на роботу (куди? — accusative). The constant switch between де? and
    куди? is natural Ukrainian.'
  - 'Preposition patterns (synthesis): | Situation | Question | Form | | Static |
    Де ти? | в/на + locative | | Direction | Куди йдеш? | в/на + accusative | | By
    transport | Як? Чим? | автобусом / на метро | | Distance | Далеко? | далеко /
    близько / пішки |'
- section: Мій район (My Neighborhood)
  words: 300
  points:
  - 'Describing where you live: Я живу на вулиці Франка. Біля мого дому є парк і магазин.
    Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму
    районі є кафе, ресторан і бібліотека.'
  - 'Useful phrases for city life: пішки (on foot), хвилина (minute) — П''ять хвилин
    пішки. далеко/близько від (far/near from — chunk). У центрі міста / на околиці
    (in the center / on the outskirts).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Urban communication toolkit: Asking: Де...? Як дістатися до...? Directions: прямо,
    направо, наліво. Location: в/на + locative, в/на + accusative. Transport: автобусом,
    на метро, пішки. Self-check: Describe your route from home to work/school.'
vocabulary_hints:
  required:
  - пішки (on foot)
  - хвилина (minute, f)
  - район (neighborhood, m)
  - центр (center, m)
  - вибачте (excuse me)
  recommended:
  - дістатися (to get to)
  - ідіть (go! — imperative, preview)
  - їдьте (go by transport! — imperative, preview)
  - поруч (nearby)
activity_hints:
- type: fill-in
  focus: Give directions using прямо, направо, наліво
  items: 6
  blanks:
  - Ідіть {прямо}, потім {направо}. Бібліотека на розі.
  - Вибачте, як дістатися до музею? — Ідіть {наліво}.
  - Аптека близько. Ідіть {прямо} п'ять хвилин.
  - Потім ідіть {направо}, школа там.
  - Йдіть {прямо}, а потім {наліво}.
  - Ресторан поруч. Ідіть {прямо} і {направо}.
- type: quiz
  focus: Де (locative) or Куди (accusative) in context
  items: 6
  questions:
  - Я зараз... (в парку / в парк)
  - Я йду... (в магазин / в магазині)
  - Магазин на... (вулиці / вулицю)
  - Потім їду на... (роботу / роботі)
  - Ми зараз у... (центрі / центр)
  - Вона йде в... (офіс / офісі)
- type: fill-in
  focus: Describe route with transport (автобусом, пішки, на метро)
  items: 6
  blanks:
  - Я їду в центр {на метро}.
  - Потім іду {пішки} п'ять хвилин.
  - Вона їде на роботу {автобусом}.
  - Школа далеко, треба їхати {на метро}.
  - Парк близько, ми йдемо {пішки}.
  - Ми їдемо в ресторан {автобусом}.
- type: match-up
  focus: Match question to logical response for navigation
  items: 6
  pairs:
  - Вибачте, як дістатися до бібліотеки?: Ідіть прямо, потім направо.
  - Де музей?: Він у центрі.
  - Як ти дістаєшся на роботу?: Їду автобусом.
  - Школа далеко?: Ні, близько. П'ять хвилин пішки.
  - Куди ви йдете?: У магазин.
  - Де ти живеш?: На вулиці Франка.
connects_to:
- a1-034 (Where From?)
prerequisites:
- a1-032 (Transport)
grammar:
- 'Synthesis: Де? (locative) + Куди? (accusative) in real navigation'
- Direction + transport + location combined
- 'Imperative preview: ідіть, їдьте (formal commands)'
register: розмовний
references:
- title: Synthesis of M28-M32 skills
  notes: Applied communication — no new grammar, just integration.
- title: Большакова Grade 2, розділ «Моє місто»
  notes: Basic directions vocabulary (прямо, направо, наліво), neighborhood descriptions,
    asking/giving directions at A1 level.

</plan_content>

---

## Wiki Teaching Brief

Skim this for the key concepts, paradigms, and examples you must cover. Reference specific examples from the article that you plan to use in each paragraph.

<knowledge_packet>
# Knowledge Packet: Around the City
**Module:** around-the-city | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/around-the-city.md

# Педагогіка A1: Around The City



## Методичний підхід (Methodological Approach)

The core methodological approach for teaching "Around The City" at the A1 level is communicative and situational. The goal is not to exhaustively list vocabulary but to equip the learner with functional chunks to solve a real-world problem: getting lost and asking for directions. The approach should mirror how a native speaker would help a foreigner, simplifying language into clear, actionable steps.

Instruction should be built around a core dialogue pattern, as demonstrated in Ukrainian Lessons Podcast episodes (Source 22, Source 23). This involves:
1.  **Gaining attention politely:** Starting with `Вибачте, будь ласка...` (Source 23).
2.  **Asking the core question:** Using the simple construction `Де [назва місця]?` (e.g., `Де вокзал?`, `Де центр?`) (Source 23).
3.  **Understanding a simple response:** Processing basic directional adverbs (`прямо`, `праворуч`, `ліворуч`) and verbs (`ідіть`, `поверніть`) (Source 22).
4.  **Clarifying transport:** Differentiating between types of transport like `автобус` (bus) and `поїзд` (train), which dictates whether one needs an `автовокзал` or `залізничний вокзал` (Source 22).

Ukrainian elementary textbooks introduce related concepts through simple, repetitive structures. For example, exercises focus on using prepositions with locations (`Підійшли до річки`, `Сховався за деревом`) (Source 10) or listing related items to build semantic fields (`Яблука, груші, сливи... — це фрукти`) (Source 28). This method of grouping and association should be used for city vocabulary (e.g., `музей`, `церква`, `магазин` are all places in a city).

The learning process should be scaffolded, starting with recognizing place names, then forming a question, and finally understanding a multi-step answer. Role-playing dialogues is a highly effective activity at this stage (Source 12, Source 20).

## Послідовність введення (Introduction Sequence)

1.  **Core Question & Basic Locations:** Start with the most fundamental survival question: `Де...?` (Where is?). Pair it with the most essential, high-frequency A1-level locations.
    *   `Де центр?` (Where is the center?) (Source 23)
    *   `Де вокзал?` (Where is the station?) (Source 22)
    *   `Де метро?` (Where is the metro?) (Source 23)
    *   `Де туалет?` <!-- VERIFY -->
    This immediately gives the learner a functional tool.

2.  **Simple Positional Answers:** Introduce the simplest possible answers a person might point and give.
    *   `Тут` (Here)
    *   `Там` (There)
    *   `Он там` (Over there) (Source 23)

3.  **Essential Directional Commands:** Introduce the imperative verbs and adverbs for giving basic directions. Always teach the formal "ви" forms first (`-іть` ending) as they are safest for speaking to strangers.
    *   `Ідіть прямо` (Go straight) (Source 22)
    *   `Поверніть праворуч` (Turn right) (Source 22)
    *   `Поверніть ліворуч` (Turn left) (Source 22)

4.  **Key Nouns for Navigation:** Introduce nouns that act as landmarks in directions.
    *   `вулиця` (street) (Source 28)
    *   `перехрестя` (intersection) (Source 22)
    *   `церква` (church) (Source 2, Source 9)
    *   `магазин` (shop) (Source 28)

5.  **Combining into Short Instructions:** Practice combining the elements from steps 3 and 4.
    *   `Ідіть прямо по вулиці...` (Go straight on ... street) (Source 22).
    *   `На перехресті поверніть праворуч` (At the intersection, turn right) (Source 22).

6.  **Transportation Vocabulary:** Introduce basic modes of transport and the places associated with them. It is crucial to distinguish between `автовокзал` and `залізничний вокзал`.
    *   `автобус` (bus) → `автовокзал` (bus station) (Source 22)
    *   `поїзд` (train) → `залізничний вокзал` (railway station) (Source 22)
    *   `метро` (metro/subway) (Source 23)

7.  **The Concept of "Needing to Take":** Introduce the impersonal construction `треба їхати` (one needs to go/travel).
    *   `Треба їхати на метро.` (You need to go by metro.) (Source 23) This is a critical A1 structure that avoids complex verb conjugations.

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Вибачаюся` | `Вибачте` | `Вибачаюся` is a reflexive verb meaning "I apologize myself," which is a calque from Russian and considered unnatural and slightly self-centered in modern Ukrainian. The correct form for apologizing or getting someone's attention is the imperative `Вибачте` (Excuse me / Forgive me) (Source 26). |
| `Де є центр?` | `Де центр?` | English speakers often try to insert the verb "to be" (`є`) in simple "Where is X?" questions, directly translating from English. In Ukrainian, the verb "to be" is omitted in present tense location questions. The structure is simply `Де + [ іменник ]?` (Source 23). |
| `Іти до праворуч` | `Ідіть праворуч` or `Поверніть праворуч` | Learners may confuse adverbs of direction (`праворуч` - to the right) with nouns of place, incorrectly adding a preposition like `до` (to). The adverbs `праворуч`, `ліворуч`, and `прямо` do not require prepositions when used with verbs of motion (Source 22). |
| Asking for the "train station" and getting the "bus station" | `Залізничний вокзал` (for trains) vs. `Автовокзал` (for buses) | In English, "station" can be ambiguous. In Ukrainian, the distinction is critical. `Вокзал` by itself often implies the main railway station, but it's best to be specific. A speaker asking for a `поїзд` (train) needs the `залізничний вокзал`; someone asking for an `автобус` (bus) needs the `автовокзал` (Source 22). |
| Using informal `Іди` with a stranger | `Ідіть` | Learners might encounter the informal `ти` forms (`іди`, `поверни`) first. It is crucial to emphasize that when asking for directions from a stranger, the formal `ви` form (`ідіть`, `поверніть`) is mandatory for politeness and respect (Source 22). |
| `Це далеко?` (with rising intonation) | `Це далеко?` | This is a positive interference. Unlike English, which often uses auxiliary verbs for questions ("**Is it** far?"), Ukrainian can often form a yes/no question simply by applying a rising intonation to a declarative sentence (Source 23). This is an easy win for learners. |

## Деколонізаційні застереження (Decolonization Notes)

This topic is highly susceptible to colonial narratives, and it is imperative to address this from the beginning.

1.  **The "Empty Land" Myth:** The Russian imperial narrative often claims that southern and eastern Ukrainian cities were "founded" by Russian monarchs (like Catherine II) on empty, wild land. This is false. Content must explicitly state that these cities were often built upon or agglomerated from pre-existing Cossack settlements. The city of Dnipro, for instance, was established on the site of the Cossack sloboda `Половиця` (Source 9). The textbook should present this as the norm: a Ukrainian settlement was renamed and absorbed, its history erased.

2.  **Authentic Toponymy:** Ukrainian place names have deep historical and geographical roots. Village names often derive from geography (`Грядина` - from garden beds, Source 2), local crafts (`гончарі` - potters, Source 1), or ancient landmarks (`Добрий Дуб` - a sacred oak, Source 2). Presenting vocabulary like `куток` (a neighborhood or corner of a village) (Source 2) and `урочище` (a distinct natural landmark) (Source 2) grounds the learner in an authentic Ukrainian perception of space, rather than a generic, universal one.

3.  **No Russian Analogies:** Do not teach Ukrainian directions or locations by comparing them to Russian. For example, never say "вулиця is like Russian улица." Teach Ukrainian on its own terms. Phonetics, grammar, and vocabulary should be presented as a self-contained system. The presence of Cossack, Polish, and other historical layers (Source 3) should be highlighted to show Ukraine's history is European and distinct.

4.  **Transportation Hubs as Ukrainian Spaces:** While `вокзал` is an internationalism (from Vauxhall Gardens), its culture in Ukraine is distinctly Ukrainian. Train travel is a major part of Ukrainian life (Source 22). Frame `вокзали` not as generic transport hubs, but as vibrant centers of Ukrainian life, often with their own markets (`ринок`) and social dynamics (Source 22).

## Словниковий мінімум (Vocabulary Boundaries)

### Іменники (Nouns)
*   **Places (Місця):**
    *   `місто` (city) ★★★ (Source 9)
    *   `село` (village) ★★★ (Source 10)
    *   `центр` (center) ★★★ (Source 23)
    *   `вулиця` (street) ★★★ (Source 28)
    *   `площа` (square) ★★ (Source 28)
    *   `музей` (museum) ★★ (Source 15)
    *   `церква` (church) ★★ (Source 9)
    *   `магазин` (shop) ★★ (Source 28)
    *   `школа` (school) ★★ (Source 28)
    *   `бібліотека` (library) ★★ (Source 28)
    *   `пошта` (post office) ★★ (Source 28)
    *   `парк` (park) ★ (Source 9)
    *   `річка` (river) ★ (Source 10)
*   **Transport (Транспорт):**
    *   `вокзал` (station) ★★★ (Source 22)
    *   `залізничний вокзал` (railway station) ★★★ (Source 22)
    *   `автовокзал` (bus station) ★★★ (Source 22)
    *   `метро` (metro/subway) ★★★ (Source 23)
    *   `станція` (station, e.g., metro station) ★★★ (Source 23)
    *   `поїзд` (train) ★★ (Source 22)
    *   `автобус` (bus) ★★ (Source 22)
*   **Navigation Points (Орієнтири):**
    *   `перехрестя` (intersection) ★★★ (Source 22)
    *   `будинок` (building, house) ★★ (Source 10)
    *   `дорога` (road) ★ (Source 4)

### Дієслова (Verbs - Imperative Formal)
*   `ідіть` (go) ★★★ (Source 22)
*   `поверніть` (turn) ★★★ (Source 22)
*   `скажіть` (tell me/say) ★★★ (Source 23)
*   `вибачте` (excuse me) ★★★ (Source 23)
*   `дивіться / бачите` (look / you see) ★★ (Source 23)

### Прислівники (Adverbs)
*   `прямо` (straight) ★★★ (Source 22)
*   `праворуч` / `направо` (to the right) ★★★ (Source 22)
*   `ліворуч` / `наліво` (to the left) ★★★ (Source 22)
*   `тут` (here) ★★★ <!-- VERIFY -->
*   `там` / `он там` (there / over there) ★★★ (Source 23)
*   `далеко` (far) ★★ (Source 23)
*   `близько` (near) ★★ (Source 23)
*   `пішки` (on foot) ★ (Source 25)

### Ключові фрази (Key Phrases)
*   `Будь ласка` (Please / You're welcome) ★★★ (Source 23)
*   `Дякую` / `Дуже дякую` (Thank you / Thank you very much) ★★★ (Source 23)
*   `Де...?` (Where is...?) ★★★ (Source 23)
*   `Треба їхати на...` (You need to go by...) ★★ (Source 23)

## Приклади з підручників (Textbook Examples)

**1. Role-Play Dialogue (Situational Practice)**
*   **Task:** Based on the model from Ukrainian Lessons Podcast (Source 20, Source 22), create a dialogue. One learner is lost and asks for directions to the museum. The other gives simple, two-step directions.
*   **Student A (Lost Tourist):** `Вибачте, будь ласка. Скажіть, будь ласка, де музей?`
*   **Student B (Local):** `Ідіть прямо по цій вулиці, а потім поверніть праворуч. Музей буде там.`
*   **Student A:** `Дуже дякую!`
*   **Student B:** `Будь ласка.`

**2. Fill-in-the-Preposition (Grammar Focus)**
*   **Task:** Complete the sentences with the correct preposition from the box: `до`, `в/у`, `на`, `за`. (Inspired by Source 10).
    *   1. Ми підійшли ____ будинку. (We approached the house.)
    *   2. Голуби потрапили ____ пастку. (The doves got into the trap.) (Source 10)
    *   3. Ми сіли ____ метро. (We got on the metro.)
    *   4. Школа знаходиться ____ тим поворотом. (The school is behind that turn.)
*   **Answers:** 1. до, 2. в, 3. на, 4. за

**3. Location Identification on a Simple Map (Visual Comprehension)**
*   **Task:** Provide a simple, schematic map of a town center with 4-5 labeled buildings (e.g., `Школа`, `Вокзал`, `Церква`, `Магазин`). Ask the learner "Where is the X?" and have them respond using simple prepositions. (Adapted from the map task in Source 5).
*   **Question:** `Де школа?`
*   **Possible Answer:** `Школа біля церкви.` (The school is near the church.)
*   **Question:** `Де магазин?`
*   **Possible Answer:** `Магазин на вулиці Шевченка.` (The shop is on Shevchenko street.)

**4. Building Sentences (Syntax Practice)**
*   **Task:** Give the learner scrambled words and have them form a correct sentence giving a direction.
    *   1. `прямо / Ідіть / вулиці / по` -> `Ідіть прямо по вулиці.` (Source 22)
    *   2. `наліво / На / поверніть / перехресті` -> `На перехресті поверніть наліво.` (Source 22)
    *   3. `треба / на / Їхати / метро` -> `Треба їхати на метро.` (Source 23)

## Пов'язані статті (Related Articles)
- `pedagogy/a1/polite-expressions`
- `grammar/cases/prepositional`
- `grammar/verbs/imperative-mood`
- `vocabulary/a1/transport`

---

### Вікі: pedagogy/a1/people-around-me.md

# Педагогіка A1: People Around Me



## Методичний підхід (Methodological Approach)
The core of teaching "People Around Me" at the A1 level is to build from the self outwards: me (`я`), you (`ти`), my family (`моя сім'я`), my friends (`мої друзі`), and then their roles (professions). The approach should be communicative and pattern-based, mirroring how Ukrainian children learn about their social circle.

1.  **Start with Identification, Not Deep Grammar:** The initial focus is on simple identification using `Це...` (This is...). Example: `Це моя мама. Це мій тато.` (Source 37). This immediately and intuitively introduces noun gender through the possessive pronouns `мій/моя` without needing to explain the concept of gender itself.

2.  **Introduce Verbs through Natural Context:** Key verbs like `працювати` (to work) and `звати` (to be called) are introduced in simple sentences. The present tense of `бути` (to be) is typically omitted, which is a key feature of Ukrainian. Instead of `Моя мама є лікар`, the natural phrasing is `Моя мама — лікар` (My mom is a doctor) (Source 18).

3.  **Use Dialogues for Social Context:** Learning about people is inherently social. Short, simple dialogues are the primary vehicle for teaching greetings, introductions, and asking about others. For example, `— Хто це? — Це моя сестра Катя.` (— Who is this? — This is my sister Katia.) (Source 18). This format also naturally introduces question words (`хто?`, `де?`, `ким?`).

4.  **Teach Cases Communicatively, Not Theoretically:** At A1, learners don't need to memorize declension tables. Instead, cases are taught through functional "chunks."
    *   **Nominative (Називний):** For the subject. `Мама працює.` (Mom works.) (Source 37).
    *   **Accusative (Знахідний):** For the direct object. `Я бачу маму.` (I see Mom.) This is one of the first and most critical case distinctions for an L2 learner (Source 12, 20).
    *   **Vocative (Кличний):** For direct address. `Мамо, привіт!` (Mom, hello!). This case is vital for politeness and natural speech and should be introduced early (Source 13, 27). It's a major point of difference from Russian and a feature of authentic Ukrainian speech.

5.  **Focus on Real-World Application:** Learners should immediately be able to apply what they've learned. Exercises should involve describing a family photo, writing a simple shopping list (`список покупок`) for family members, or creating a simple dialogue inviting a friend to a party (`запросити тебе в гості`) (Source 7, 5).

The goal is to build a functional scaffolding of language that allows learners to talk about their immediate social world. Abstract grammar rules come later; at A1, it's all about concrete, repeatable patterns (Source 2, 5).

## Послідовність введення (Introduction Sequence)

**Step 1 → Core Vocabulary: Immediate Family & Friends**
*   Introduce the core nouns: `мама, тато, брат, сестра, друг, подруга, сім'я` (family). These are high-frequency and immediately useful (Source 37).
*   Pair them with possessive pronouns to implicitly teach gender: `мій тато, мій брат, мій друг` vs. `моя мама, моя сестра, моя подруга`.

**Step 2 → Simple Identification & Naming**
*   Use the structure `Це + [person]`. Example: `Це моя сім'я на фотографії.` (This is my family in the photo) (Source 18).
*   Introduce naming with `Його/її звати...` (His/her name is...). Example: `Це мій брат. Його звати Денис.` (Source 18).

**Step 3 → Professions**
*   Introduce common professions using the structure `[Person] + [profession]`. Example: `Моя мама – лікар, а тато – викладач.` (My mom is a doctor, and dad is a university teacher) (Source 18).
*   Introduce gendered pairs where they are common: `вчитель / вчителька`, `студент / студентка` (Source 11).
*   Also, point out common professions that use the masculine form for both genders, like `дизайнер`, `програміст`, `менеджер` (Source 11, 18).

**Step 4 → Grammatical Roles: Subject vs. Object (Nominative vs. Accusative)**
*   Introduce the Nominative case (хто? що?) as the "doer" of the action. The initial vocabulary is already in this form. `Мама читає.` (Mom is reading.) (Source 37, 40).
*   Introduce the Accusative case (кого? що?) as the "receiver" of the action. Start with feminine nouns, as the change is obvious: `Я люблю мам**у**.` vs. `Я люблю сестр**у**.` (Source 12, 20).
*   Then, introduce the Accusative for masculine animate nouns, which is a major learning point: `Я бачу брат**а**.` (I see my brother.) Contrast this with inanimate nouns: `Я бачу стіл.` (I see the table.) (Source 13, 21). This distinction is fundamental.

**Step 5 → Direct Address (Vocative Case)**
*   Introduce the Vocative case for addressing people directly, as it is essential for natural communication.
*   Start with simple, common forms: `Мамо!`, `Тату!`, `Друже!`, `Оксано!` (Source 10, 13, 30).
*   Explain that this form is used instead of the Nominative when calling out to someone or getting their attention. `Оксанко, скажи лагідне, добре слово.` (Oksanka, say a kind, good word) (Source 34).

## Типові помилки L2 (Common L2 Errors)
Guidance for the writer on what pitfalls English-speaking learners will face and how to pre-emptively address them.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Андрій, де ти?` | `Андрі**ю**, де ти?` | English speakers lack the concept of a vocative case for direct address. They must learn that calling someone by name in Ukrainian requires changing the ending. This is a marker of fluency. (Source 14, 27). |
| `Я бачу **мій друг**.` | `Я бачу **мого друга**.` | Learners often fail to apply the Accusative case to masculine animate nouns, treating them like inanimate objects. The rule is: if it's a "who" (кого?), the ending changes. (Source 20, 21, 30). |
| `Вона **є** вчителька.` | `Вона — вчителька.` | English speakers overuse the verb "to be" (`є`) in present tense identity statements. In Ukrainian, it's typically omitted, and a dash (`—`) can be used in writing. (Source 18). |
| `Моя тато` | `**Мій** тато` | Noun gender is not intuitive for English speakers. They may incorrectly match feminine possessive pronouns (`моя`) with masculine nouns (`тато`). Constant reinforcement through patterns is necessary. (Source 41). |
| `Я хочу запросити **ви**.` | `Я хочу запросити **вас**.` | Learners often forget to decline personal pronouns. They must learn that pronouns change form when they are the object of a verb (Accusative case). (Source 7, 43). |
| `Я працюю як вчитель.` | `Я працюю вчителем.` | This is a direct translation of the English "I work *as* a teacher". In Ukrainian, this construction uses the Instrumental case (`ким?` - by whom?), not the word `як` (as/like). While Instrumental case is a B1 topic, this specific phrase chunk should be taught. <!-- VERIFY --> |

## Деколонізаційні застереження (Decolonization Notes)
**This is a mandatory section for all pedagogical briefs.** The goal is to teach Ukrainian on its own terms, free from the historical dominance of Russian-centric linguistics.

1.  **The Vocative Case is a Ukrainian Feature:** Emphasize that the robust Vocative case (`друже`, `пане`, `Олено`) is a vibrant, living part of modern Ukrainian, distinguishing it clearly from modern Russian, where the vocative is archaic or stylistically limited. It is not an optional or poetic form; it is standard grammar for direct address. (Source 10, 14, 27).

2.  **Gendered Nouns (Feminitives) are Standard:** Forms like `вчителька`, `письменниця`, `дизайнерка`, `засновниця` are not recent inventions or slang; they are a standard and evolving part of the Ukrainian language. The writer should use them consistently and naturally. (Source 4, 11). The use of these forms reflects a conscious break from the Soviet-era practice of using masculine forms as a universal default. (Source 6).

3.  **Teach Ukrainian Phonetics Directly:** Never use Russian as a phonetic reference point (e.g., "Ukrainian `и` is like Russian `ы`"). This builds an incorrect phonetic base. Ukrainian `и` and `і` are distinct sounds that must be learned from native audio examples. The historical pressure to Russify Ukrainian, including language, was a deliberate imperial policy (`Емський указ`), and consciously choosing to be a "свідома українка" (conscious Ukrainian) was an act of identity. (Source 6, 16).

4.  **Avoid "False Friends" with Russian:** The writer must be aware of words that exist in both languages but have different meanings or connotations. For example, `дружина` in Ukrainian primarily means "wife," whereas in Russian, it means "squad" or "retinue." While not directly related to this topic, the principle applies. Vocabulary should be sourced from Ukrainian explanatory dictionaries and usage guides (`СУМ-11`, Source 29).

## Словниковий мінімум (Vocabulary Boundaries)

#### Іменники (Nouns)
*   **Family & People (Сім'я та люди):**
    *   ★★★: `сім'я` (family), `мама` (mom), `тато` (dad), `батьки` (parents), `брат` (brother), `сестра` (sister), `друг` (male friend), `подруга` (female friend), `люди` (people). (Source 37, 17, 26).
    *   ★★: `дідусь` (grandfather), `бабуся` (grandmother), `чоловік` (husband), `дружина` (wife), `син` (son), `донька` (daughter), `хлопець` (boy/boyfriend), `дівчина` (girl/girlfriend). (Source 37, 41).
    *   ★: `тітка` (aunt), `дядько` (uncle), `колега` (colleague), `сусід` (neighbor). (Source 41, 8).
*   **Professions (Професії):**
    *   ★★★: `вчитель / вчителька` (teacher), `лікар` (doctor), `студент / студентка` (student). (Source 11, 18).
    *   ★★: `програміст` (programmer), `дизайнер` (designer), `менеджер` (manager), `продавець / продавчиня` (salesperson). (Source 11, 19).
    *   ★: `письменник / письменниця` (writer), `музикант` (musician), `водій` (driver), `пенсіонер / пенсіонерка` (pensioner). (Source 11, 18).

#### Займенники (Pronouns)
*   **Personal (Особові):**
    *   ★★★: `я, ти, він, вона, воно, ми, ви, вони`.
    *   ★★★ (Accusative forms): `мене, тебе, його, її, нас, вас, їх`. (Source 7, 43).
*   **Possessive (Присвійні):**
    *   ★★★: `мій, моя, моє, мої` (my); `твій, твоя, твоє, твої` (your). (Source 41).

#### Дієслова (Verbs)
*   ★★★: `бути` (to be, including its omission in the present), `звати` (to be called), `працювати` (to work), `жити` (to live), `мати` (to have), `бачити` (to see), `знати` (to know), `любити` (to love).

## Приклади з підручників (Textbook Examples)

**1. Activity: Matching Professions to Workplaces (Source 19)**
*   **Format:** A matching exercise. Two columns are presented, and the learner must draw a line connecting the person to their place of work.
*   **Prompt:** `Знайдіть пари за зразком.` (Find the pairs according to the example).
*   **Example:**
    | Хто? (Who?) | Де? (Where?) |
    | :--- | :--- |
    | лікар | школа |
    | вчитель | лікарня |
    | продавець | банк |
    | економіст | магазин |
*   **Goal:** Reinforces vocabulary for professions and places in a simple, visual way.

**2. Activity: Distinguishing Subject and Object (Nominative vs. Accusative) (Source 20)**
*   **Format:** Sentence comparison. The learner reads two very similar sentences where the subject and object are swapped.
*   **Prompt:** `Спишіть речення. Визначте, якими членами речення є виділені слова.` (Copy the sentences. Determine which part of the sentence the highlighted words are).
*   **Example:**
    *   `**Катерина** запросила **подругу**.` (Kateryna invited her friend.) -> Підмет: Катерина (Н.в.), Додаток: подругу (Зн.в.)
    *   `**Подруга** запросила **Катерину**.` (The friend invited Kateryna.) -> Підмет: Подруга (Н.в.), Додаток: Катерину (Зн.в.)
*   **Goal:** Forces the learner to focus on word endings to understand "who did what to whom," which is the core function of these cases.

**3. Activity: Forming the Vocative Case for Address (Source 14, 27)**
*   **Format:** A transformation drill. The learner is given a name or a title in the Nominative and must write it in the Vocative.
*   **Prompt:** `Утворіть звертання за допомогою сполук слів за зразком.` (Form an address using the word combinations, following the example).
*   **Example:**
    *   *Input:* `брат Сергій`, `пан професор`, `подруга Галя`
    *   *Output:* `брате Сергію`, `пане професоре`, `подруго Галю`
*   **Goal:** To practice forming the vocative case, which is essential for polite and correct direct address.

**4. Activity: Fill-in-the-blanks with Personal Pronouns (Source 36)**
*   **Format:** A short paragraph with blanks where the learner must insert the correct form of a personal pronoun.
*   **Prompt:** `Спиши, вставляючи замість крапок займенник **ти** у відповідних відмінкових формах.` (Copy, inserting the pronoun "you" in the correct case forms instead of the dots).
*   **Example:** "Чи є (у кого?) **в тебе** справжній друг? Так радісно жити, коли поруч (з ким?) **з тобою** добрі люди. Вони завжди готові прийти (кому?) **тобі** на допомогу."
*   **Goal:** To drill the declension of personal pronouns in different cases within a meaningful context.

## Пов'язані статті (Related Articles)
*   `pedagogy/a1/introduction-to-cases`
*   `pedagogy/a1/nominative-case`
*   `pedagogy/a1/accusative-case`
*   `pedagogy/a1/vocative-case`
*   `vocabulary/a1/professions-and-work`
*   `vocabulary/a1/family-and-friends`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type, focus]
...

## Підсумок (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~1200 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 1200+.** Aim for ~10% overshoot (1320 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercise injection markers in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place `<!-- INJECT_ACTIVITY: descriptive-id -->` AFTER the teaching content of that section, never before. Use a descriptive kebab-case id (e.g., `fill-in-genitive`, `quiz-aspect-choice`). If no `section:` is specified, place the marker after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section. Every plan `activity_hints` entry MUST have a corresponding `<!-- INJECT_ACTIVITY: id -->` marker in the skeleton.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
