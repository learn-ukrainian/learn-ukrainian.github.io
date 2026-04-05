<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-intro.yaml` file for module **5: У мене немає...** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Possession vs. Absence Drill (`Є` vs. `Немає`)
  items: 8
  type: quiz
- focus: Genitive Singular Formation
  items: 8
  type: fill-in
- focus: Genitive Plural Formation with Quantity Words
  items: 8
  type: match-up
- focus: Translate sentences with 'a lot of...' / 'I don't have...'
  items: 8
  type: match-up
- focus: Reorder words to form correct genitive phrases with немає and quantity expressions
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кількість (quantity)
- відсутність (absence)
- гроші (money)
- час (time)
required:
- родовий відмінок (genitive case)
- немає ((there) is not, (I) don't have)
- багато (a lot, many, much)
- мало (a little, few)
- кілька (a few, several)
- скільки (how many, how much)
- закінчення (ending (grammar))
- однина (singular)
- множина (plural)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Родовий відмінок: Коли чогось немає (The Genitive Case: When Something Isn't There)

You already know the Nominative case (Називний відмінок) for naming things and the Accusative case (Знахідний відмінок) for the direct object of an action. Now, it is time to learn the Genitive case (Родовий відмінок). This is one of the most frequently used cases in the Ukrainian language. It is the case of origin, absence, and negation. It answers the core questions «Кого?» *(of whom?)* and «Чого?» *(of what?)*. Whenever we talk about things we *do not* have, or things that *are not* present in a certain place, we must switch from the Nominative to the Genitive case. 

### Приклади (Examples)
«Це мій брат.» *(This is my brother. — Nominative)*
«Я бачу брата.» *(I see a brother. — Accusative)*
«У мене немає брата.» *(I do not have a brother. — Genitive)*

The most common way to use the Genitive case is with the construction «у мене немає» *(I don't have)*. The linguistic logic in Ukrainian is quite different from English. In English, you say "I do not have a car," implying personal possession of a negative fact. In Ukrainian, you literally say "By me there is no car." 

The word «немає» means "there is no" or "is not present." It is an impersonal word, and whatever is "not there" must absolutely take the Genitive case. 

### Читаємо українською: Структура (Reading Practice: Structure)
«У мене є машина.» *(I have a car.)*
«У мене немає машини.» *(I don't have a car.)*
«У нього є новий телефон.» *(He has a new phone.)*
«У нього немає телефона.» *(He doesn't have a phone.)*
«У нас є вільний час.» *(We have free time.)*
«У нас немає часу.» *(We don't have time.)*
«У них є гроші.» *(They have money.)*
«У них немає грошей.» *(They don't have money.)*

It is very important to contrast presence with absence. When an object is present, we use the word «є» *(is/there is)* and the Nominative case. When an object is absent, we use the word «немає» and the Genitive case. The word «немає» always triggers this grammatical change. Notice how the endings change when we switch from «є» to «немає». We will learn the exact rules for these endings in the next section, but for now, focus on the pattern.

### Порівняння (Comparison)
«Тут є великий стіл.» *(There is a big table here. — Nominative)*
«Тут немає стола.» *(There is no table here. — Genitive)*
«У місті є гарний парк.» *(There is a beautiful park in the city. — Nominative)*
«У місті немає парку.» *(There is no park in the city. — Genitive)*
«У кімнаті є широке вікно.» *(There is a wide window in the room. — Nominative)*
«У кімнаті немає вікна.» *(There is no window in the room. — Genitive)*

### Читаємо українською: Нова квартира (Reading Practice: A New Apartment)
> — **Сусідка:** Добрий день! Я ваша нова сусідка. *(Good day! I am your new neighbor.)*
> — **Нова мешканка:** Добрий день! Дуже приємно. Заходьте, будь ласка. *(Good day! Nice to meet you. Come in, please.)*
> — **Сусідка:** О, у вас дуже світла і велика квартира. Але тут ще майже нічого немає! *(Oh, you have a very bright and big apartment. But there is almost nothing here yet!)*
> — **Нова мешканка:** Так, це правда. На кухні ще немає плити. *(Yes, that's true. There is no stove in the kitchen yet.)*
> — **Сусідка:** І великого холодильника теж немає? *(And there is no big fridge either?)*
> — **Нова мешканка:** Поки що немає холодильника, немає зручного стола... *(For now there is no fridge, there is no comfortable table...)*
> — **Сусідка:** А у ванній кімнаті? Там усе є? *(And in the bathroom? Is everything there?)*
> — **Нова мешканка:** Ні, у ванній ще немає дзеркала. *(No, there is no mirror in the bathroom yet.)*
> — **Сусідка:** Я бачу, що у вас є багато коробок, але дуже мало меблів. *(I see that you have a lot of boxes, but very little furniture.)*
> — **Нова мешканка:** Нічого страшного. Меблі обов'язково будуть завтра вранці. *(No worries. The furniture will definitely be here tomorrow morning.)*

Let's look closer at the word «немає». You might also see it written as two separate words: «не має». What is the exact difference? As noted in Ukrainian school textbooks, «немає» (written as one word) is an impersonal predicate meaning "there is no." It does not change, and it requires the Genitive case. However, «не має» (written as two words) is the normal verb «мати» *(to have)* with the negative particle «не». It means "he/she/it does not have" and is used with a specific subject.

:::tip
**Немає чи не має? (Nemaye or ne maye?)**
«Тут **немає** брата.» *(There is no brother here. — Impersonal absence)*
«Він **не має** брата.» *(He does not have a brother. — Personal possession)*
In everyday speech, Ukrainians strongly prefer the «у мене немає» structure over using the verb «мати».
«Анна не має часу.» *(Anna does not have time.)*
«У Анни немає часу.» *(Anna does not have time — much more natural and common.)*
:::

<!-- INJECT_ACTIVITY: quiz, Possession vs. Absence Drill (`Є` vs. `Немає`), 8 items -->


## Закінчення родового відмінка однини (Genitive Singular Endings)

In Ukrainian, the Genitive case is very "talkative." It changes the endings of nouns significantly to show absence, quantity, or possession. The exact ending depends on the noun's gender and the "hardness" or "softness" of its final consonant. Once you learn the patterns, forming the Genitive singular becomes highly predictable. Let's look at how the endings change when we use the word «немає» *(there is no)* to express that something is missing.

### Чоловічий рід (Masculine Gender)

Masculine nouns present a famous puzzle: they can take either the `-а/-я` ending or the `-у/-ю` ending. 

The `-а/-я` ending is used for concrete, tangible objects you can easily touch or count. It is also used for animate beings (people and animals) and specific measurements. For example, in our previous dialogue, «холодильник» *(a fridge)* is a concrete, countable object, so it becomes «холодильника» in the Genitive case.

«Тут є брат. — У мене немає брата.» *(There is a brother here. — I have no brother.)*
«Тут є син. — У нього немає сина.» *(There is a son here. — He has no son.)*
«Тут є стіл. — У кімнаті немає стола.» *(There is a table here. — There is no table in the room.)*
«Тут є телефон. — У мене немає телефона.» *(There is a phone here. — I have no phone.)*
«У мене є один долар. — У мене немає долара.» *(I have one dollar. — I don't have a dollar.)*
«Це мій кіт. — У хаті немає кота.» *(This is my cat. — There is no cat in the house.)*
«Тут є новий комп'ютер. — У школі немає комп'ютера.» *(There is a new computer here. — There is no computer in the school.)*

On the other hand, the `-у/-ю` ending is used for abstract concepts, substances (liquids, powders, gases), and large geographical locations like regions, cities, or institutions. This is one of the most debated parts of Ukrainian grammar even among native speakers! However, focusing on the "Concrete vs. Abstract/Substance" logic will guide you to the right answer most of the time. You cannot easily count "sugar" or "time" as individual items.

«Тут є цукор. — У чаї немає цукру.» *(There is sugar here. — There is no sugar in the tea.)*
«Тут є час. — На жаль, у мене немає часу.» *(There is time here. — Unfortunately, I don't have time.)*
«Тут є великий парк. — Біля дому немає парку.» *(There is a big park here. — There is no park near the house.)*
«Тут є університет. — У цьому місті немає університету.» *(There is a university here. — There is no university in this city.)*
«Він відчуває біль. — У пацієнта немає болю.» *(He feels pain. — The patient has no pain.)*
«Тут є теплий пісок. — На пляжі немає піску.» *(There is warm sand here. — There is no sand on the beach.)*
«Тут є смачний сік. — У склянці немає соку.» *(There is tasty juice here. — There is no juice in the glass.)*

:::tip **Що обрати? (What to choose?)**
If you can pick it up with your hands or count it exactly (one table, two phones), use **-а/-я**. If it is a feeling, a liquid, or a place you walk into (time, water, a park), use **-у/-ю**.
:::

### Жіночий рід (Feminine Gender)

Feminine nouns are much simpler and follow a beautiful phonetic harmony. Nouns with hard stems (usually ending in `-а` in the dictionary form) change their ending to `-и`. Nouns with soft stems (usually ending in `-я` or a soft consonant) change their ending to `-і`.

«Тут є мама. — Вдома немає мами.» *(There is a mom here. — Mom is not at home.)*
«Тут є школа. — У селі немає школи.» *(There is a school here. — There is no school in the village.)*
«Тут є цікава книга. — У бібліотеці немає книги.» *(There is an interesting book here. — There is no book in the library.)*
«Тут є нова плита. — На кухні ще немає плити.» *(There is a new stove here. — There is no stove in the kitchen yet.)*
«Тут є чорна земля. — Тут немає землі.» *(There is black land here. — There is no land here.)*
«Тут лунає пісня. — Сьогодні немає пісні.» *(A song sounds here. — There is no song today.)*
«Тут є широка вулиця. — У місті немає вулиці.» *(There is a wide street here. — There is no street in the city.)*
«Тут є Марія. — Сьогодні на уроці немає Марії.» *(Maria is here. — Maria is not at the lesson today.)*

### Середній рід (Neuter Gender)

Neuter nouns also follow a clear pattern based on their original vowel. Most neuter nouns that end in `-о` (hard stem) change to `-а`. Neuter nouns that end in `-е` (soft stem) change to `-я`. Notice how neuter endings in the Genitive singular look exactly like the Nominative endings for feminine nouns!

«Тут є велике вікно. — У кімнаті немає вікна.» *(There is a big window here. — There is no window in the room.)*
«Тут є чисте дзеркало. — У ванній немає дзеркала.» *(There is a clean mirror here. — There is no mirror in the bathroom.)*
«Тут є нове слово. — У тексті немає слова.» *(There is a new word here. — There is no word in the text.)*
«Тут є тепле море. — Біля міста немає моря.» *(There is a warm sea here. — There is no sea near the city.)*
«Тут світить сонце. — Сьогодні на небі немає сонця.» *(The sun shines here. — There is no sun in the sky today.)*
«Тут є зелене поле. — Біля лісу немає поля.» *(There is a green field here. — There is no field near the forest.)*

### Читаємо українською: Що є в офісі? (Reading Practice: What is in the office?)

> — **Менеджер:** Добрий день! Це наш новий офіс. *(Good day! This is our new office.)*
> — **Клієнт:** Добрий день. Тут дуже гарно. Але я бачу, що тут немає комп'ютера. *(Good day. It is very nice here. But I see that there is no computer here.)*
> — **Менеджер:** Так, комп'ютера ще немає. І принтера також немає. *(Yes, there is no computer yet. And there is no printer either.)*
> — **Клієнт:** А швидкий інтернет є? *(And is there fast internet?)*
> — **Менеджер:** На жаль, інтернету поки що немає. *(Unfortunately, there is no internet yet.)*
> — **Клієнт:** Я розумію. А кава у вас є? *(I understand. And do you have coffee?)*
> — **Менеджер:** Звісно! Кава є, але зараз немає цукру. *(Of course! There is coffee, but there is no sugar right now.)*
> — **Клієнт:** Нічого страшного, я п'ю без цукру. Але у вас немає чашки! *(No worries, I drink without sugar. But you don't have a cup!)*
> — **Менеджер:** Ой, вибачте... Чашки справді немає. *(Oh, sorry... There really is no cup.)*

<!-- INJECT_ACTIVITY: fill-in, Genitive Singular Formation -->


## Коли є багато або мало (When There Is a Lot or a Little)

When we want to talk about the quantity of something, we use specific quantity words. In Ukrainian, words that express quantity act like "Genitive magnets." If you have a lot of something, a little of something, or you are asking how many things there are, the noun that follows must change its form. Because we are usually talking about multiple items (a lot of books, a few friends), we use the Genitive Plural (**родовий відмінок множини**).

The most common quantity words you will use are **багато** *(a lot, many, much)*, **мало** *(a little, few)*, **кілька** or **декілька** *(a few, several)*, and the question word **скільки** *(how many, how much)*. Whenever you use these words followed by a noun, that noun must take the Genitive Plural form. This rule applies whether the quantity is large, small, or unknown.

«У мене є багато друзів.» *(I have a lot of friends.)*
«Тут живе мало людей.» *(Few people live here.)*
«На столі лежить кілька книг.» *(There are a few books lying on the table.)*
«Скільки студентів у класі?» *(How many students are in the class?)*
«У нас є декілька питань.» *(We have a few questions.)*

### Чоловічий рід (Masculine Nouns)

How do we form the Genitive Plural? It depends entirely on the gender of the noun. Let's start with masculine nouns, which are generally the most straightforward. For most masculine nouns that end in a hard consonant, the Genitive Plural ending is **-ів**. If the masculine noun ends in a soft sign or a vowel (like `-й`), the ending becomes **-їв**. This is the dominant and most common pattern you will hear in everyday conversation.

«Тут є багато столів.» *(There are a lot of tables here. [стіл → столів])*
«У мене немає братів.» *(I do not have brothers. [брат → братів])*
«У місті є кілька музеїв.» *(There are several museums in the city. [музей → музеїв])*
«Скільки доларів коштує цей квиток?» *(How many dollars does this ticket cost? [долар → доларів])*
«Я знаю багато хороших студентів.» *(I know many good students. [студент → студентів])*

There is also a small but important group of nouns that take the ending **-ей**. You will simply need to memorize these as special cases because they are used very frequently. The most common examples are **гостей** *(of guests)* and **грошей** *(of money)*.

«У нас сьогодні дуже багато гостей.» *(We have a lot of guests today.)*
«На жаль, у мене мало грошей.» *(Unfortunately, I have little money.)*

:::tip
The word **друг** *(friend)* is a special case. It changes its stem to **друзі** in the plural, and its Genitive Plural form takes the standard ending: **багато друзів** *(a lot of friends)*.
:::

### Жіночий та середній рід (Feminine and Neuter Nouns)

Feminine and neuter nouns share a very interesting and unique pattern in the Genitive Plural. Instead of adding letters to the end of the word, they usually lose their final vowel entirely. This is called the "zero ending" (**нульове закінчення**). You simply drop the **-а**, **-я**, **-о**, or **-е** from the end of the singular dictionary form. It feels like the word is being cut short abruptly.

Let's look at some common feminine examples where the vowel simply disappears:

«Тут на вулиці дуже багато машин.» *(There are a lot of cars here on the street. [машина → машин])*
«У мене зараз немає жодних проблем.» *(I have absolutely no problems right now. [проблема → проблем])*
«Я вивчаю кілька іноземних мов.» *(I am studying several foreign languages. [мова → мов])*
«Скільки шкіл є у вашому місті?» *(How many schools are in your city? [школа → шкіл])*

Neuter nouns follow the exact same zero-ending rule:

«В Україні є багато гарних міст.» *(There are many beautiful cities in Ukraine. [місто → міст])*
«У цьому тексті є кілька нових слів.» *(There are a few new words in this text. [слово → слів])*
«Ми бачимо багато сіл.» *(We see many villages. [село → сіл])*

### Рухомий голосний (The Fleeting Vowel)

When you drop the final vowel to create the zero ending for feminine and neuter nouns, you sometimes end up with a difficult combination of consonants at the very end of the word. Ukrainian pronunciation prefers a smooth, melodic flow, so it fixes this awkwardness by automatically inserting a "helper vowel" — usually **о** or **е** — between those final two consonants. This is called a "fleeting vowel" (**рухомий голосний**) because it appears in the Genitive Plural and disappears in other forms.

If the feminine word ends in **-ка**, it almost always inserts an **о**:

«Це дуже цікава книжка.» *(This is a very interesting book.)* -> «У мене є багато книжок.» *(I have a lot of books.)*
«Тут є одна маленька помилка.» *(There is one small mistake here.)* -> «У тексті є кілька помилок.» *(There are a few mistakes in the text.)*
«На столі стоїть чашка.» *(A cup stands on the table.)* -> «На столі є кілька чашок.» *(There are several cups on the table.)*

If the word ends in other tricky consonant clusters, it often inserts an **е** (or **є** if soft):

«Вона моя старша сестра.» *(She is my older sister.)* -> «У нього є кілька сестер.» *(He has several sisters.)*
«Скільки гривень коштує ця кава?» *(How many hryvnias does this coffee cost? [гривня → гривень])*
«У будинку кілька великих вікон.» *(There are several large windows in the house. [вікно → вікон])*

### Описуємо світ навколо нас (Describing the World Around Us)

Now you can combine everything you have learned in this module to create much richer and more complex descriptions. You can talk about what you possess, what you lack, and the exact quantities of things around you, all using the powerful Genitive case. Notice how the sentence structure allows you to contrast having an abundance of one thing with a complete lack of another.

«У мене багато друзів, але мало вільного часу.» *(I have a lot of friends, but little free time.)*
«У кімнаті немає великих вікон, але є багато картин.» *(There are no large windows in the room, but there are many paintings.)*
«Скільки грошей у тебе зараз є?» *(How much money do you have right now?)*
«У цьому місті є кілька гарних парків, але зовсім немає шкіл.» *(There are several beautiful parks in this city, but there are absolutely no schools.)*
«На столі лежить кілька нових книжок, але немає зошитів.» *(There are a few new books lying on the table, but there are no notebooks.)*

### Читаємо українською: Ремонт у новій квартирі (Reading Practice: Renovation in a New Apartment)

> — **Оксана:** Привіт, Максиме! Як твоя нова квартира? *(Hi, Maksym! How is your new apartment?)*
> — **Максим:** Привіт, Оксано! Квартира велика, але там ще мало меблів. *(Hi, Oksana! The apartment is big, but there is still little furniture there.)*
> — **Оксана:** У тебе вже є ліжко і шафа? *(Do you already have a bed and a wardrobe?)*
> — **Максим:** Так, ліжко є. Але у мене немає столів і немає стільців. *(Yes, I have a bed. But I have no tables and no chairs.)*
> — **Оксана:** А скільки кімнат у квартирі? *(And how many rooms are in the apartment?)*
> — **Максим:** Три кімнати. Там є багато вікон, тому дуже світло. *(Three rooms. There are many windows there, so it is very bright.)*
> — **Оксана:** Це чудово! А нова техніка є? *(That's wonderful! And are there new appliances?)*
> — **Максим:** На кухні є холодильник, але ще немає плити. *(There is a fridge in the kitchen, but no stove yet.)*
> — **Оксана:** У мене є кілька вільних стільців. Я можу тобі їх дати. *(I have a few spare chairs. I can give them to you.)*
> — **Максим:** Дуже дякую! Це допоможе, бо зараз у мене мало грошей. *(Thank you very much! That will help, because right now I have little money.)*

<!-- INJECT_ACTIVITY: match-up, Genitive Plural Formation with Quantity Words -->
<!-- INJECT_ACTIVITY: match-up, Translate sentences with 'a lot of...' / 'I don't have...' -->
<!-- INJECT_ACTIVITY: unjumble, Reorder words to form correct genitive phrases with немає and quantity expressions -->


## Підсумок (Summary)

Сьогодні ми вивчили дуже важливу функцію родового відмінка *(the Genitive case)*. You now know that this case is essential for two everyday situations: expressing absence and talking about quantities. When we want to say that someone does not have something, or something does not exist in a place, we use the magic word «немає» followed by the Genitive case. You have seen how «У мене є брат» *(I have a brother)* turns into «У мене немає брата» *(I don't have a brother)*.

We also learned that when you have a lot, a little, or an indefinite number of things, Ukrainian demands the Genitive plural. Words like «багато» *(a lot)*, «мало» *(a little)*, and «кілька» *(several)* are your triggers for this grammatical change. 

Remembering the endings takes practice. Masculine nouns split between **-а/-я** for concrete objects and **-у/-ю** for abstractions or substances. Feminine and neuter nouns often lose their endings completely in the plural, which can sometimes create a new fleeting vowel (like «вікно» becoming «вікон»). 

### Перевірте себе (Self-Check)

- Як ми кажемо "I don't have a book" українською? *(У мене немає книги.)*
- Яке закінчення мають маскулінітиви, що позначають конкретні предмети (наприклад, «стіл»)? *(-а: стола.)*
- Що відбувається з закінченням фемінітивів у множині після слова «багато»? *(Воно зазвичай зникає: «багато книг».)*
- Коли ми використовуємо закінчення -у/-ю для чоловічого роду? *(Для абстрактних понять та речовин: «мало часу», «немає цукру».)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-intro
level: a2

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

---

## Learner Level Context

**Level: A2 (Module 5/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
