# Activity Markdown Format Reference

This file demonstrates the markdown syntax for all 14 activity types used in curriculum modules.
Use this as a pattern when writing new modules. The `generate-mdx.ts` script converts this format to MDX.

> **Note:** Currently only 7 types have MDX parsers. See issue #103 for adding the remaining 7.

---

# Activities

## quiz: Multiple Choice Example
> Select the correct answer.

1. What does "привіт" mean?
   - [x] hello
   - [ ] goodbye
   - [ ] thank you
   - [ ] please
   > привіт (pryvit) = hello

2. Which is the feminine form of "this"?
   - [ ] цей
   - [x] ця
   - [ ] це
   - [ ] ці
   > Feminine → ця

3. How do you say "thank you"?
   - [ ] будь ласка
   - [x] дякую
   - [ ] привіт
   - [ ] вибачте
   > дякую (dyakuyu) = thank you

## match-up: Vocabulary Matching
> Match the Ukrainian words with their English meanings.

| Ukrainian | English |
|-----------|---------|
| книга | book |
| стіл | table |
| вікно | window |
| двері | door |
| кімната | room |
| будинок | building |

## fill-in: Complete the Sentence
> Fill in the blank with the correct word.

1. Я ___ книгу. (read)
   > [!answer] читаю
   > [!options] читаю | читаєш | читає | читають

2. Вона ___ українською. (speak)
   > [!answer] говорить
   > [!options] говорить | говорю | говоримо | говорять

3. Ми ___ в офісі. (work)
   > [!answer] працюємо
   > [!options] працюємо | працюю | працюєш | працюють

4. Ти ___ каву? (drink)
   > [!answer] п'єш
   > [!options] п'єш | п'ю | п'є | п'ють

## true-false: Grammar Rules
> Decide if each statement is true or false.

- [x] Ukrainian has 7 grammatical cases.
  > Correct! Nominative, Genitive, Dative, Accusative, Instrumental, Locative, Vocative.

- [ ] All Ukrainian nouns are masculine.
  > Incorrect! Ukrainian has three genders: masculine, feminine, and neuter.

- [x] Verb endings show who is doing the action.
  > Correct! That's why pronouns are often optional.

- [ ] Ukrainian uses the Latin alphabet.
  > Incorrect! Ukrainian uses the Cyrillic alphabet with 33 letters.

## anagram: Letter Unscramble (A1 Only)
> Arrange the letters to form the correct word.

1. к н и г а
   > [!answer] книга
   > (book)

2. с т і л
   > [!answer] стіл
   > (table)

3. в і к н о
   > [!answer] вікно
   > (window)

4. д в е р і
   > [!answer] двері
   > (door)

## unjumble: Word Order
> Put the words in the correct order.

1. книгу / читаю / Я
   > [!answer] Я читаю книгу.
   > (I read a book.) [3 words]

2. українською / Вона / говорить
   > [!answer] Вона говорить українською.
   > (She speaks Ukrainian.) [3 words]

3. в / Ми / офісі / працюємо
   > [!answer] Ми працюємо в офісі.
   > (We work in the office.) [4 words]

4. каву / Ти / п'єш / ранку / з
   > [!answer] Ти п'єш каву з ранку.
   > (You drink coffee in the morning.) [5 words]

## group-sort: Category Sorting
> Sort these items into the correct categories.

### Masculine Nouns
- стіл
- будинок
- хлопець
- телефон

### Feminine Nouns
- книга
- кімната
- дівчина
- машина

### Neuter Nouns
- вікно
- місто
- слово
- море

## error-correction: Find and Fix (A2+)
> Each sentence has ONE error. Find the incorrect word and correct it.

1. Я бачу студент у бібліотеці.
   > [!error] студент
   > [!answer] студента
   > [!options] студент | студента | студенту | студентом
   > [!explanation] Animate masculine accusative = genitive form

2. Вона читав книгу вчора.
   > [!error] читав
   > [!answer] читала
   > [!options] читав | читала | читало | читали
   > [!explanation] Past tense agrees with subject gender (feminine = -ла)

3. Це моя книга, а це твоя.
   > [!error] none
   > [!answer] ✓
   > [!explanation] No error - keeps learners alert

## select: Multiple Correct Answers (A2+)
> Select ALL correct options.

1. Which are valid accusative forms for "книга"?
   - [x] книгу
   - [ ] книги
   - [ ] книзі
   - [ ] книгою
   > Only книгу is the accusative singular.

2. Which verbs are Class I conjugation?
   - [x] читати
   - [x] писати
   - [ ] говорити
   - [ ] любити
   > читати and писати end in -ати (Class I), говорити/любити are Class II (-ити)

## translate: Translation Choice (A2+)
> Choose the correct translation.

1. I love Ukraine.
   - [ ] Я люблю Українa.
   - [x] Я люблю Україну.
   - [ ] Я люблю України.
   - [ ] Я люблю Україні.
   > Accusative case needed: Україну

2. She reads a book.
   - [ ] Вона читає книга.
   - [ ] Вона читаю книгу.
   - [x] Вона читає книгу.
   - [ ] Вона читаєш книгу.
   > Third person singular: читає

## cloze: Passage Completion (A2+)
> Fill in the blanks with the correct words.

Мене [___:1] Олена. Я [___:2] з України. Я [___:3] українською і англійською.

1. звати | є | маю
   > [!answer] звати

2. є | живу | приїхала
   > [!answer] є

3. говорю | говорить | говорять
   > [!answer] говорю

## dialogue-reorder: Conversation Order (A2+)
> Put the dialogue in the correct order.

- А: Привіт! Як справи?
- B: Добре, дякую! А у тебе?
- А: Теж добре. Що будеш замовляти?
- B: Каву, будь ласка.
- А: Американо чи латте?
- B: Американо з молоком.

## mark-the-words: Word Identification (A2+)
> Click all the nouns in this sentence.

[Хлопець] читає [книгу] в [парку] біля [річки].

> 4 nouns: хлопець (boy), книгу (book), парку (park), річки (river)

## observe: Pattern Discovery (A2+)
> Study these examples and find the pattern.

> [!observe]
> Я **читаю** книгу.
> Ти **читаєш** книгу.
> Він **читає** книгу.
> Ми **читаємо** книгу.
> Ви **читаєте** книгу.
> Вони **читають** книгу.
>
> What pattern do you notice in the verb endings?

---

# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| книга | /ˈknɪɦɑ/ | book | noun | f | |
| стіл | /stil/ | table | noun | m | |
| вікно | /wʲikˈnɔ/ | window | noun | n | |
| читати | /t͡ʃɪˈtɑtɪ/ | to read | verb | - | читаю, читаєш |
| говорити | /ɦɔvɔˈrɪtɪ/ | to speak | verb | - | говорю, говориш |

---

# Summary

This reference file shows all 14 activity types:

1. **quiz** - Multiple choice (single answer)
2. **match-up** - Pair matching with table
3. **fill-in** - Gap fill with dropdown options
4. **true-false** - True/false statements
5. **anagram** - Letter unscrambling (A1 only)
6. **unjumble** - Word reordering
7. **group-sort** - Category sorting
8. **error-correction** - Find and fix mistakes (A2+)
9. **select** - Multiple correct answers (A2+)
10. **translate** - Translation choice (A2+)
11. **cloze** - Passage with multiple blanks (A2+)
12. **dialogue-reorder** - Conversation ordering (A2+)
13. **mark-the-words** - Word identification (A2+)
14. **observe** - Pattern discovery (A2+)

**Currently supported by generate-mdx.ts:** quiz, match-up, fill-in, true-false, anagram, unjumble, group-sort

**Needs MDX parser (see issue #103):** error-correction, select, translate, cloze, dialogue-reorder, mark-the-words, observe
