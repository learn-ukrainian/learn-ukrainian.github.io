黎thought
CRITICAL INSTRUCTION 1:
- 'cat' to create/append -> NOT APPLICABLE here (we are generating text, not running bash).
- 'grep' inside bash -> NOT APPLICABLE.
- 'ls', 'cat', 'grep', 'sed' -> NOT APPLICABLE.
We are tasked with generating text based on a prompt. No file system tools are needed.

CRITICAL INSTRUCTION 2:
- Tools available: `mcp_rag_verify_word`, `mcp_rag_verify_words`, `mcp_rag_verify_lemma`, `mcp_rag_query_pravopys`, `mcp_rag_search_style_guide`, `mcp_rag_search_definitions`, `mcp_rag_search_synonyms`, `mcp_rag_query_e2u`, `mcp_rag_translate_en_uk`.
- We already used `mcp_rag_verify_lemma` to check `кулька`. `кульками` is the correct instrumental plural.

Let's refine Dialogue 1 and 2 to fit the requested word count and style rules.

Dialogue 1 paragraph (P2 skeleton):
A 6-8 exchange dialogue focusing on Nominative, Genitive, and Accusative. Examples: "Хто прийде?" (Nom. subject), "У нас немає торта", "Буде багато гостей" (Gen. of absence and quantity), "Треба купити торт", "Час запрошувати друзів" (Acc. direct objects).

Let's write it closely to the example sentences requested.
> — **Оксана:** Привіт, Андрію! У суботу буде **вечірка** (party) для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*
> — **Андрій:** Клас! А хто прийде? *(Cool! And who will come?)*
> — **Оксана:** Буде багато гостей. Нам час **запрошувати** (to invite) друзів. *(There will be many guests. It is time for us to invite friends.)*
> — **Андрій:** Я можу купити великий торт. *(I can buy a large cake.)*
> — **Оксана:** Це чудова ідея. У нас ще немає торта. *(That is a wonderful idea. We don't have a cake yet.)*
> — **Андрій:** А що ми будемо пити? *(And what will we drink?)*
> — **Оксана:** Я куплю сік і воду. *(I will buy juice and water.)*
> — **Андрій:** Добре, я все зрозумів. *(Good, I understood everything.)*

Wait, is P2 supposed to be just the dialogue, or an intro paragraph before it?
The skeleton says: "P2 (~150 words): Dialogue Part 1 (Planning the basics). A 6-8 exchange dialogue focusing on Nominative, Genitive, and Accusative. Examples: "Хто прийде?" (Nom. subject), "У нас немає торта", "Буде багато гостей" (Gen. of absence and quantity), "Треба купити торт", "Час запрошувати друзів" (Acc. direct objects)."
It's just the dialogue and maybe a tiny bit of text to pad the word count, but dialog turns take up words.
Let's see the word count for the dialogue alone: 8 exchanges, 16 lines (with English). About 90 words.
To reach 150 words, maybe I should make the dialogue longer, or add a short intro sentence before the dialogue block inside P2.
I will add an intro sentence to P2: "Here is the first part of their conversation, where they focus on the guest list and the food."

Let's expand Dialogue 1:
> — **Оксана:** Привіт, Андрію! У суботу буде **вечірка** (party) для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*
> — **Андрій:** Клас! А хто прийде? *(Cool! And who will come?)*
> — **Оксана:** Буде багато гостей. Нам час **запрошувати** (to invite) друзів. *(There will be many guests. It is time for us to invite friends.)*
> — **Андрій:** Я можу купити смачний торт на десерт. *(I can buy a delicious cake for dessert.)*
> — **Оксана:** Це чудова ідея. У нас ще немає торта, і я не вмію пекти. *(That is a wonderful idea. We don't have a cake yet, and I don't know how to bake.)*
> — **Андрій:** А що ми будемо пити? *(And what will we drink?)*
> — **Оксана:** Я куплю сік, лимонад і мінеральну воду. *(I will buy juice, lemonade, and mineral water.)*
> — **Андрій:** Добре. Тоді я також куплю піцу. *(Good. Then I will also buy pizza.)*
This is exactly 8 exchanges.

P3 Grammar breakdown (100 words):
In this first half of the dialogue, we see the Nominative, Genitive, and Accusative cases in action. The Nominative case introduces the main subjects of the sentence, such as when Andriy asks **хто** (who) will come to the celebration. The word **торт** (cake) changes its form depending on its grammatical role. When Andriy offers to buy it, it acts as a direct object and stays **торт** in the Accusative case because it is an inanimate object. However, when Oksana points out that they do not have one, the negative word **немає** (there is no) forces it into the Genitive case, making it **торта**.

Ми також бачимо знахідний відмінок для живих істот, коли Оксана каже запрошувати друзів. Оскільки друзі — це люди, форма знахідного відмінка множини збігається з формою родового відмінка.
> *We also see the Accusative case for living beings when Oksana says to invite friends. Because friends are people, the Accusative plural form matches the Genitive plural form.*

P4 Dialogue Part 2 (Details and gifts) (~150 words):
Need Dative, Instrumental, Locative, Vocative.
> — **Андрій:** Оксано, який **подарунок** (gift) купимо Олені? *(Oksana, what gift will we buy for Olena?)*
> — **Оксана:** Може, книгу? Треба написати друзям і запитати. *(Maybe a book? We need to write to the friends and ask.)*
> — **Андрій:** Добра ідея. А де ми зустрінемося? У кафе біля парку? *(Good idea. And where will we meet? In a cafe near the park?)*
> — **Оксана:** Так, ми підемо туди з друзями. *(Yes, we will go there with friends.)*
> — **Андрій:** Ми прикрасимо кімнату яскравими кульками! *(We will decorate the room with bright balloons!)*
> — **Оксана:** Андрію, це буде чудовий сюрприз. *(Andriy, this will be a wonderful surprise.)*
> — **Андрій:** Згоден. На вечірці буде дуже весело. *(I agree. It will be very fun at the party.)*
> — **Оксана:** Тоді я чекаю на тебе завтра. *(Then I am waiting for you tomorrow.)*
This hits Dat (Олені, друзям), Instr (з друзями, кульками), Loc (у кафе, на вечірці), Voc (Оксано, Андрію). Let's write an intro sentence for this one too. "Now let's look at the second part of their conversation, where they discuss the gift, the location, and the decorations."

P5 Grammar breakdown of Part 2 (~100 words):
The second part of the conversation brings in the four remaining cases. The Vocative case is used for direct address, which is why the names change to **Оксано** and **Андрію**. The Dative case shows the recipient of an action, such as buying a gift for Olena (**Олені**) or writing a message to the friends (**друзям**). We use the Instrumental case to show accompaniment, like going with friends (**з друзями**), or to indicate the instrument used to perform an action, like decorating with balloons (**кульками**). Finally, the Locative case is used to indicate the location of an event or meeting.

:::info
**Grammar box**
Remember that the Locative case is the only case that *never* appears without a preposition. You will always see it with words like **у/в** (in) or **на** (on/at), as seen in the phrases **у кафе** (in a cafe) and **на вечірці** (at the party).
:::

P6 Cultural note (~50 words):
:::tip
**Did you know?**
Ukrainian birthday traditions might differ from what you are used to. In some cultures, guests pool their money to pay for the birthday person's meal or drinks when they go out to celebrate. In Ukraine, the custom is the exact opposite. The birthday person, known as the іменинник (birthday boy) or іменинниця (birthday girl), is expected to **частувати** (treat) the guests to food and drinks. The guests bring gifts, but the host covers the cost of the celebration.
:::

Activity:
`<!-- INJECT_ACTIVITY: quiz, Identify which case a highlighted noun is in and explain why (verb or preposition trigger), 8 items -->`

Let me double check the exact case examples from the skeleton in Dialogue 2:
"Який подарунок купимо Олені?"
"Треба написати друзям"
"Підемо з друзями"
"Прикрасимо кімнату кулями" - wait, the prompt specifically says "кулями". Let's check "кулями". I verified "кулька" is "кульками". "куля" is "кулями". "Куля" can mean bullet, sphere, or balloon. So "кулями" is fine, but "кульками" is a diminutive, and very common for balloons. I will use "кульками" as it's better Ukrainian for balloons, or I can use "повітряними кулями". Actually, "кулями" is explicitly requested in the prompt: `(Instr. accompaniment and instrument), "Зустрінемося у кафе", "На вечірці буде весело" (Loc. location), "Оксано!", "Андрію!" (Voc. direct address).` I should stick to the requested phrases as closely as possible, or at least include the requested words. I will use `кулями` to be safe, or just "кульками" but ensure I hit the Instrumental case point. The prompt's examples are usually guidance, not strict verbatim requirements, but I will use `кулями` to strictly match the prompt's `(Instr. z друзями, прикрасити кулями)`. Actually, I can use "кульками" since it's the diminutive form of "куля" and means balloon more naturally. Let's see if "куля" -> "кулями" is better. "Прикрасити повітряними кулями" (decorate with balloons).
Let me check the translation of balloons. "повітряні кульки". "куля" is more of a sphere or bullet. Let's use `кульками`.

Let's review the required vocabulary checklist from the prompt:
- [x] вечірка (party)
- [x] подарунок (gift, present)
- [x] лікар (doctor)
- [x] пацієнт (patient)
- [x] здоров'я (health)
- [x] ліки (medicine)
- [x] подорож (trip, journey)
- [x] потяг (train)
- [x] визначне місце (landmark, sight)
- [x] запрошувати (to invite)

Wait, can I add any of the others naturally?
Лікар, пацієнт, здоров'я, ліки, подорож, потяг, визначне місце.
No, none of those fit naturally into a birthday party planning dialogue. They will be swept up in Dialogue 2 and 3.

Let's verify "Оксано" and "Андрію" with `mcp_rag_verify_lemma`.
Оксана -> Оксано. Андрій -> Андрію.
Let's verify the words just in case.
黎thought
CRITICAL INSTRUCTION 1:
- 'cat' to create/append -> NOT APPLICABLE here (we are generating text, not running bash).
- 'grep' inside bash -> NOT APPLICABLE.
- 'ls', 'cat', 'grep', 'sed' -> NOT APPLICABLE.
We are tasked with generating text based on a prompt. No file system tools are needed.

CRITICAL INSTRUCTION 2:
- Tools available: `mcp_rag_verify_word`, `mcp_rag_verify_words`, `mcp_rag_verify_lemma`, `mcp_rag_query_pravopys`, `mcp_rag_search_style_guide`, `mcp_rag_search_definitions`, `mcp_rag_search_synonyms`, `mcp_rag_query_e2u`, `mcp_rag_translate_en_uk`.
- We used `mcp_rag_verify_words` to check `Оксано` and `Андрію`. Both are found.

Let's do a final check of the text against all the constraints:
- Monolingual paragraphs (hard rule #1185): Yes, I'm ensuring English paragraphs are English and Ukrainian paragraphs are Ukrainian with English blockquotes beneath them. Dialogues are exempt from the monolingual rule.
- No stress marks.
- No Russian, Surzhyk, or calques.
- `вечірка`, `подарунок`, `запрошувати` are bolded and translated inline `**вечірка** (party)` in English paragraphs or left as is in the dialogue with full line translation in `*(*...*)*`. Wait, the requirement says "include it now (bold + English translation)" if it fits naturally. I will do this in the English intro text.
Wait! Required vocabulary checklist says: "(bold + English translation)". I did this in the English text: `**вечірка** (party)`. But in dialogue, it's bolded with English translation in the translation block? No, I'll put it in the intro paragraph just to be safe, like `**вечірка** (party)`.
Let's ensure the bolding + gloss `**term** (gloss)` is used appropriately but no more than 3 per paragraph to avoid the "inline-gloss salad" pattern.

Intro P1:
Planning a surprise **вечірка** (party) for a friend involves a lot of details and coordination. You have to decide who to invite, what kind of food to prepare, and where the celebration will take place. When native speakers like Оксана and Андрій discuss these plans, they naturally jump between all seven grammatical cases in a single conversation. Seeing all the cases working together is the best way to understand how Ukrainian sentences are built. Let's look at how they organize a celebration for their friend Олена.

Intro for Part 1 (inside P2):
This first part of their conversation focuses on the guest list and the food. It is time **запрошувати** (to invite) the guests and prepare the menu.

Dialogue Part 1:
> — **Оксана:** Привіт, Андрію! У суботу буде вечірка для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*
> — **Андрій:** Клас! А хто прийде? *(Cool! And who will come?)*
> — **Оксана:** Буде багато гостей. Нам час запрошувати друзів. *(There will be many guests. It is time for us to invite friends.)*
> — **Андрій:** Я можу купити великий торт. *(I can buy a large cake.)*
> — **Оксана:** Це чудова ідея. У нас ще немає торта. *(That is a wonderful idea. We don't have a cake yet.)*
> — **Андрій:** А що ми будемо пити? *(And what will we drink?)*
> — **Оксана:** Я куплю сік і воду. *(I will buy juice and water.)*
> — **Андрій:** Добре, я все зрозумів. *(Good, I understood everything.)*

Grammar Breakdown 1 (P3):
In this first half of the dialogue, we see the Nominative, Genitive, and Accusative cases in action. The Nominative case introduces the main subjects of the sentence, such as when Andriy asks **хто** (who) will come to the celebration. The word **торт** (cake) changes its form depending on its grammatical role. When Andriy offers to buy it, it acts as a direct object and stays **торт** in the Accusative case because it is an inanimate object. However, when Oksana points out that they do not have one, the negative word **немає** (there is no) forces it into the Genitive case, making it **торта**.

Ми також бачимо знахідний відмінок для живих істот, коли Оксана каже запрошувати друзів. Оскільки друзі — це люди, форма знахідного відмінка множини збігається з формою родового відмінка.
> *We also see the Accusative case for living beings when Oksana says to invite friends. Because friends are people, the Accusative plural form matches the Genitive plural form.*

Intro for Part 2 (inside P4):
Now let's look at the second part of their conversation, where they discuss the perfect **подарунок** (gift), the location, and the decorations.

Dialogue Part 2:
> — **Андрій:** Оксано, який подарунок купимо Олені? *(Oksana, what gift will we buy for Olena?)*
> — **Оксана:** Може, книгу? Треба написати друзям і запитати. *(Maybe a book? We need to write to the friends and ask.)*
> — **Андрій:** Добра ідея. А де ми зустрінемося? У кафе? *(Good idea. And where will we meet? In a cafe?)*
> — **Оксана:** Так, ми підемо туди з друзями. *(Yes, we will go there with friends.)*
> — **Андрій:** Ми прикрасимо кімнату яскравими кульками! *(We will decorate the room with bright balloons!)*
> — **Оксана:** Андрію, це буде чудовий сюрприз. *(Andriy, this will be a wonderful surprise.)*
> — **Андрій:** Згоден. На вечірці буде дуже весело. *(I agree. It will be very fun at the party.)*

Grammar Breakdown 2 (P5):
The second part of the conversation brings in the four remaining cases. The Vocative case is used for direct address, which is why the names change to **Оксано** and **Андрію**. The Dative case shows the recipient of an action, such as buying a gift for Olena (**Олені**) or writing a message to the friends (**друзям**). We use the Instrumental case to show accompaniment, like going with friends (**з друзями**), or to indicate the instrument used to perform an action, like decorating with balloons (**кульками**). Finally, the Locative case is used to indicate the location of an event or meeting.

:::info
**Grammar box**
Remember that the Locative case is the only case that *never* appears without a preposition. You will always see it with words like **у/в** (in) or **на** (on/at), as seen in the phrases **у кафе** (in a cafe) and **на вечірці** (at the party).
:::

Cultural Note (P6):
:::tip
**Did you know?**
Ukrainian birthday traditions might differ from what you are used to. In some cultures, guests pool their money to pay for the birthday person's meal or drinks when they go out to celebrate. In Ukraine, the custom is the exact opposite. The birthday person, known as the іменинник (birthday boy) or іменинниця (birthday girl), is expected to **частувати** (treat) the guests to food and drinks. The guests bring gifts, but the host covers the cost of the celebration.
:::

Activity:
`<!-- INJECT_ACTIVITY: quiz-case-identification -->` (Using the exact format from the skeleton: `<!-- INJECT_ACTIVITY: quiz-case-identification -->`) Wait, the skeleton says:
`<!-- INJECT_ACTIVITY: quiz-case-identification --> [quiz, Identify which case a highlighted noun is in and explain why (verb or preposition trigger), 8 items]`
I will output exactly this comment line at the end. Wait, the prompt says:
`<!-- INJECT_ACTIVITY: type, topic hint -->`
I will output `<!-- INJECT_ACTIVITY: quiz, Identify which case a highlighted noun is in and explain why (verb or preposition trigger), 8 items -->`.

Let's count the words again.
Intro 1: 68 words
Intro 2: 24 words
Dial 1: 85 words
Dial 2: 90 words
Breakdown 1: 153 words
Breakdown 2: 104 words
Box: 40 words
Tip: 80 words
Activity: 17 words
Total: ~660 words. This is right in the sweet spot for the 600-word target (aim for 660).

Wait, the prompt said:
`"Який подарунок купимо Олені?"`
`"Треба написати друзям"`
`"Підемо з друзями"`
`"Прикрасимо кімнату кулями"`
I used "кульками". Let me just use "кулями" to literally match the prompt's `кулями` example, or "кульками" to be more idiomatic. "Кулька" is much better for balloon, "куля" is bullet/sphere. "Прикрасити кулями" sounds like decorating with bullets or giant spheres. Since the prompt uses it as an example, but also says "zero Surzhyk", I'll stick to "кульками" but explain it acts as an instrument.

Let's double check Ukrainian sentences lengths.
"Кожен відмінок має свою функцію в реченні." (7 words)
"Називний відмінок показує головний предмет, родовий відмінок вказує на кількість або відсутність, а знахідний відмінок позначає об'єкт дії." (18 words) - Too long! Rule: "Max 15 words per Ukrainian sentence. Max 2 clauses per sentence."
Let's rewrite the Ukrainian paragraph in P3:
Ми також бачимо знахідний відмінок для живих істот. Оксана каже запрошувати друзів на свято. Оскільки друзі — це люди, ця форма збігається з формою родового відмінка.
> *We also see the Accusative case for living beings. Oksana says to invite friends to the holiday. Because friends are people, this form matches the Genitive case form.*

Sentences:
1. Ми також бачимо знахідний відмінок для живих істот. (8 words, 1 clause)
2. Оксана каже запрошувати друзів на свято. (6 words, 1 clause)
3. Оскільки друзі — це люди, ця форма збігається з формою родового відмінка. (12 words, 2 clauses)
This strictly adheres to the 15-word / 2-clause limit.

The prompt requires formatting for Dialogues:
> — **Оксана:** Привіт! *(Hi!)*
> — **Степан:** Добрий день! *(Good day!)*

Mine:
> — **Оксана:** Привіт, Андрію! У суботу буде вечірка для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*
Is this correct? Yes.

Let's check "частувати".
`mcp_rag_verify_lemma` on `частувати` -> verified, it exists. I know it means "to treat".

Check the forbidden words:
хорошо, конечно, спасибо, пожалуйста, ничего, сейчас, тоже, здесь, кот, кон.
None of these are in the text.
No ы, э, ё, ъ characters anywhere.

Let's check for inline glossing limits.
In Intro P1: `**вечірка** (party)` - 1 gloss.
In Intro for Part 1: `**запрошувати** (to invite)` - 1 gloss.
In Intro for Part 2: `**подарунок** (gift)` - 1 gloss.
In P6 Tip: `**частувати** (treat)` - 1 gloss.
None of these exceed 3 per paragraph.
The inline gloss limit rule is met.

Are there any mixed language sentences?
`Planning a surprise **вечірка** (party) for a friend involves a lot of details and coordination.`
This is an English sentence with an inline gloss. Rule says:
`Inline bolded vocabulary tooltips (up to 3 per paragraph): ✅ The word for cat is **кіт** (cat).`
So this is allowed and explicitly considered NOT a violation of the monolingual rule as long as it's limited to 3 per paragraph.

Let's review the required vocabulary once more.
вечірка - used.
подарунок - used.
запрошувати - used.
The rest (лікар, пацієнт, здоров'я, ліки, подорож, потяг, визначне місце) will naturally fit into the next two dialogues (Hospital, Travelling).

Let's re-verify the dialogue translation format:
`> — **Оксана:** Привіт! *(Hi!)*`
My output:
`> — **Оксана:** Привіт, Андрію! У суботу буде вечірка для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*`
This matches perfectly.

The formatting requires the section heading exactly as provided:
`## Діалог 1: Організовуємо день народження (~600 words)`

Check grammar box format:
```
:::info
**Grammar box**
Remember that the Locative case is the only case that *never* appears without a preposition. You will always see it with words like **у/в** (in) or **на** (on/at), as seen in the phrases **у кафе** (in a cafe) and **на вечірці** (at the party).
:::
```
This is correct.

Check Tip format:
```
:::tip
**Did you know?**
Ukrainian birthday traditions might differ from what you are used to. In some cultures, guests pool their money to pay for the birthday person's meal or drinks when they go out to celebrate. In Ukraine, the custom is the exact opposite. The birthday person, known as the іменинник (birthday boy) or іменинниця (birthday girl), is expected to **частувати** (treat) the guests to food and drinks. The guests bring gifts, but the host covers the cost of the celebration.
:::
```
This is correct.

And the exercise marker:
`<!-- INJECT_ACTIVITY: quiz, Identify which case a highlighted noun is in and explain why (verb or preposition trigger), 8 items -->`
This is exactly as requested in the instructions.

Final scan of the content against the plan references and knowledge packet:
Knowledge packet stresses Genitive and Accusative Animate matching, which I included. Locative and Instrumental are noted in the second part. The Vocative case is demonstrated.

I will assemble the final output block now.## Діалог 1: Організовуємо день народження (~600 words)

Planning a surprise **вечірка** (party) for a friend involves a lot of details and coordination. You have to decide who to invite, what kind of food to prepare, and where the celebration will take place. When native speakers like Оксана and Андрій discuss these plans, they naturally jump between all seven grammatical cases in a single conversation. Seeing all the cases working together is the best way to understand how Ukrainian sentences are built. Let's look at how they organize a celebration for their friend Олена.

This first part of their conversation focuses on the guest list and the food. It is time **запрошувати** (to invite) the guests and prepare the menu.

> — **Оксана:** Привіт, Андрію! У суботу буде вечірка для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*
> — **Андрій:** Клас! А хто прийде? *(Cool! And who will come?)*
> — **Оксана:** Буде багато гостей. Нам час запрошувати друзів. *(There will be many guests. It is time for us to invite friends.)*
> — **Андрій:** Я можу купити великий торт. *(I can buy a large cake.)*
> — **Оксана:** Це чудова ідея. У нас ще немає торта. *(That is a wonderful idea. We don't have a cake yet.)*
> — **Андрій:** А що ми будемо пити? *(And what will we drink?)*
> — **Оксана:** Я куплю сік і воду. *(I will buy juice and water.)*
> — **Андрій:** Добре, я все зрозумів. *(Good, I understood everything.)*

In this first half of the dialogue, we see the Nominative, Genitive, and Accusative cases in action. The Nominative case introduces the main subjects of the sentence, such as when Andriy asks **хто** (who) will come to the celebration. The word **торт** (cake) changes its form depending on its grammatical role. When Andriy offers to buy it, it acts as a direct object and stays **торт** in the Accusative case because it is an inanimate object. However, when Oksana points out that they do not have one, the negative word **немає** (there is no) forces it into the Genitive case, making it **торта**.

Ми також бачимо знахідний відмінок для живих істот. Оксана каже запрошувати друзів на свято. Оскільки друзі — це люди, ця форма збігається з формою родового відмінка.

> *We also see the Accusative case for living beings. Oksana says to invite friends to the holiday. Because friends are people, this form matches the Genitive case form.*

Now let's look at the second part of their conversation, where they discuss the perfect **подарунок** (gift), the location, and the decorations.

> — **Андрій:** Оксано, який подарунок купимо Олені? *(Oksana, what gift will we buy for Olena?)*
> — **Оксана:** Може, книгу? Треба написати друзям і запитати. *(Maybe a book? We need to write to the friends and ask.)*
> — **Андрій:** Добра ідея. А де ми зустрінемося? У кафе? *(Good idea. And where will we meet? In a cafe?)*
> — **Оксана:** Так, ми підемо туди з друзями. *(Yes, we will go there with friends.)*
> — **Андрій:** Ми прикрасимо кімнату яскравими кульками! *(We will decorate the room with bright balloons!)*
> — **Оксана:** Андрію, це буде чудовий сюрприз. *(Andriy, this will be a wonderful surprise.)*
> — **Андрій:** Згоден. На вечірці буде дуже весело. *(I agree. It will be very fun at the party.)*

The second part of the conversation brings in the four remaining cases. The Vocative case is used for direct address, which is why the names change to **Оксано** and **Андрію**. The Dative case shows the recipient of an action, such as buying a gift for Olena (**Олені**) or writing a message to the friends (**друзям**). We use the Instrumental case to show accompaniment, like going with friends (**з друзями**), or to indicate the instrument used to perform an action, like decorating with balloons (**кульками**). Finally, the Locative case is used to indicate the location of an event or meeting.

:::info
**Grammar box**
Remember that the Locative case is the only case that *never* appears without a preposition. You will always see it with words like **у/в** (in) or **на** (on/at), as seen in the phrases **у кафе** (in a cafe) and **на вечірці** (at the party).
:::

:::tip
**Did you know?**
Ukrainian birthday traditions might differ from what you are used to. In some cultures, guests pool their money to pay for the birthday person's meal or drinks when they go out to celebrate. In Ukraine, the custom is the exact opposite. The birthday person, known as the іменинник (birthday boy) or іменинниця (birthday girl), is expected to **частувати** (treat) the guests to food and drinks. The guests bring gifts, but the host covers the cost of the celebration.
:::

<!-- INJECT_ACTIVITY: quiz, Identify which case a highlighted noun is in and explain why (verb or preposition trigger), 8 items -->