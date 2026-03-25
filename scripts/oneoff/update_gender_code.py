import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md', 'r') as f:
    content = f.read()

# Replace 1
content = content.replace("""**Examples:**
*   **дім** — house (ends in 'm' → Masculine)
*   **стіл** — table (ends in 'l' → Masculine)
*   **хліб** — bread (ends in 'b' → Masculine)
*   **брат** — brother (ends in 't' → Masculine)""", """**Examples:**
*   **дім** — house (ends in 'm' → Masculine)
*   **стіл** — table (ends in 'l' → Masculine)
*   **хліб** — bread (ends in 'b' → Masculine)
*   **брат** — brother (ends in 't' → Masculine)
*   **парк** — park (ends in 'k' → Masculine)
*   **банк** — bank (ends in 'k' → Masculine)
*   **чай** — tea (ends in 'й' → Masculine)""")

# Replace 2
content = content.replace("""> [!context]
> **Usage Note: "Мій"**
> When you possess a masculine object, you use the word **мій** (my).
> *   **мій брат** (my brother)
> *   **мій дім** (my house)
> *   **мій стіл** (my table)""", """> [!context]
> **Usage Note: "Мій"**
> When you possess a masculine object, you use the word **мій** (my).
> *   **мій брат** (my brother)
> *   **мій дім** (my house)
> *   **мій стіл** (my table)
> *   **мій парк** (my park)
> *   **мій банк** (my bank)
> *   **мій чай** (my tea)
> 
> **Приклади (Examples):**
> *   Це дім. Це мій дім. (This is a house. This is my house.)
> *   Це мій чай. Дякую! (This is my tea. Thank you!)""")

# Replace 3
content = content.replace("""**Examples:**
*   **ма́ма** — mom (ends in 'a' → Feminine)
*   **сестра́** — sister (ends in 'a' → Feminine)
*   **кни́га** — book (ends in 'a' → Feminine)
*   **кімна́та** — room (ends in 'a' → Feminine)
*   **земля́** — earth/land (ends in 'ya' → Feminine)""", """**Examples:**
*   **ма́ма** — mom (ends in 'a' → Feminine)
*   **сестра́** — sister (ends in 'a' → Feminine)
*   **кни́га** — book (ends in 'a' → Feminine)
*   **кімна́та** — room (ends in 'a' → Feminine)
*   **земля́** — earth/land (ends in 'ya' → Feminine)
*   **ка́ва** — coffee (ends in 'a' → Feminine)
*   **маши́на** — car (ends in 'a' → Feminine)""")

# Replace 4
content = content.replace("""> [!context]
> **Usage Note: "Моя"**
> To say "my" for feminine words, use **моя́**. Notice the rhyme: **Мам-а** → **Мо-я**.
> *   **моя мама** (my mom)
> *   **моя книга** (my book)
> *   **моя земля** (my land)""", """> [!context]
> **Usage Note: "Моя"**
> To say "my" for feminine words, use **моя́**. Notice the rhyme: **Мам-а** → **Мо-я**.
> *   **моя мама** (my mom)
> *   **моя книга** (my book)
> *   **моя земля** (my land)
> *   **моя кава** (my coffee)
> *   **моя кімната** (my room)
> 
> **Приклади (Examples):**
> *   Це машина. Це моя машина. (This is a car. This is my car.)
> *   Це моя кава. Будь ласка. (This is my coffee. Please.)""")

# Replace 5
content = content.replace("""**Examples:**
*   **вікно́** — window (ends in 'o' → Neuter)
*   **мі́сто** — city (ends in 'o' → Neuter)
*   **мо́ре** — sea (ends in 'e' → Neuter)
*   **се́рце** — heart (ends in 'e' → Neuter)""", """**Examples:**
*   **вікно́** — window (ends in 'o' → Neuter)
*   **мі́сто** — city (ends in 'o' → Neuter)
*   **мо́ре** — sea (ends in 'e' → Neuter)
*   **се́рце** — heart (ends in 'e' → Neuter)
*   **пи́во** — beer (ends in 'o' → Neuter)
*   **м'я́со** — meat (ends in 'o' → Neuter)""")

# Replace 6
content = content.replace("""> [!context]
> **Usage Note: "Моє"**
> When you possess a neuter object, you use the word **моє́** (my). Listen to the sound — it matches the "roundness" of the neuter endings.
> *   **моє місто** (my city)
> *   **моє серце** (my heart)
> *   **моє море** (my sea)""", """> [!context]
> **Usage Note: "Моє"**
> When you possess a neuter object, you use the word **моє́** (my). Listen to the sound — it matches the "roundness" of the neuter endings.
> *   **моє місто** (my city)
> *   **моє серце** (my heart)
> *   **моє море** (my sea)
> *   **моє вікно** (my window)
> *   **моє пиво** (my beer)
> 
> **Приклади (Examples):**
> *   Це місто. Це моє місто. (This is a city. This is my city.)
> *   Це моє пиво. Дякую! (This is my beer. Thank you!)""")

# Replace 7
content = content.replace("""**Олена:** А це **твоя** сестра? (And is this your sister?)
**Андрій:** Так, це **моя** сестра. (Yes, this is my sister.)

**Бачите?** (See the pattern?)
*   **мама** (F) → **моя**
*   **тато** (M) → **мій** (Remember the dad rule!)
*   **брат** (M) → **мій**
*   **сестра** (F) → **моя**

## Культурний код та підсумок (Cultural Code and Summary)""", """**Олена:** А це **твоя** сестра? (And is this your sister?)
**Андрій:** Так, це **моя** сестра. (Yes, this is my sister.)

**Бачите?** (See the pattern?)
*   **мама** (F) → **моя**
*   **тато** (M) → **мій** (Remember the dad rule!)
*   **брат** (M) → **мій**
*   **сестра** (F) → **моя**

### Міні-діалог: Кафе (The Cafe)
Let's look at another situation. Pay attention to the gender of food and drinks.

**Олег:** Привіт! Це **моя** кава? (Hello! Is this my coffee?)
**Анна:** Ні, це **моя** кава. А це **твоє** пиво. (No, this is my coffee. And this is your beer.)
**Олег:** Добре, дякую. А де **мій** чай? (Okay, thank you. And where is my tea?)
**Анна:** Ось **твоя** вода і **мій** чай. Вибачте! (Here is your water and my tea. Sorry!)

**Бачите?** (See the pattern?)
*   **кава** (F), **вода** (F) → **моя**, **твоя**
*   **пиво** (N) → **моє**, **твоє**
*   **чай** (M) → **мій**, **твій**

## Культурний код та підсумок (Cultural Code and Summary)""")

# Replace 8
content = content.replace("""Відповіді (Answers): Masculine (consonant), Feminine (-а), Neuter (-о). When you know this, the code works!

## Практичні вправи (Practice Exercises)""", """Відповіді (Answers): Masculine (consonant), Feminine (-а), Neuter (-о). When you know this, the code works!

**Більше практики:** (More practice:)
- **кава** (coffee) → ___
- **чай** (tea) → ___
- **пиво** (beer) → ___

Відповіді (Answers): Feminine (-а), Masculine (consonant й), Neuter (-о).

## Практичні вправи (Practice Exercises)""")

# Replace 9 (Adding more Ukrainian phrases into explanations)
content = content.replace("""**The "Dad" Trap**
> Do not say "моє тато" just because it ends in "-о." Dad is always a "He."
> Correct: **мій тато** (my dad).""", """**The "Dad" Trap**
> Do not say "моє тато" just because it ends in "-о." Dad is always a "He."
> Правильно (Correct): **мій тато** (my dad).
> Наприклад (For example): Це мій тато. (This is my dad.)""")

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md', 'w') as f:
    f.write(content)

print("Updates applied")
