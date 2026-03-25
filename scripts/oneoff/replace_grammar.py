with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'r', encoding='utf-8') as f:
    text = f.read()

old_p1 = "When we talk about who we are right now, as our fundamental identity, we use the Nominative case, which is the dictionary form. This is what you learned in your first Ukrainian lessons. You simply say the pronoun and the noun, establishing a direct equation between the person and the title."
new_p1 = """> **📚 Граматика: Називний відмінок (Grammar: Nominative case)**
>
> Коли ми говоримо про нашу ідентичність, ми використовуємо називний відмінок. 
> (When we talk about our identity, we use the Nominative case.)
>
> Це словникова форма. Ви вчили це на перших уроках. 
> (This is the dictionary form. You learned this in your first lessons.)
>
> Ви просто кажете займенник і іменник.
> (You simply say the pronoun and the noun.)"""

old_p2 = "However, when we describe a role, a profession we work in, a past phase, or a future goal, we are talking about a function rather than a permanent identity. For this specific grammatical function, Ukrainian uses the Instrumental case. The language distinguishes between what you inherently are and what role you happen to occupy at a given time."
new_p2 = """> **📚 Граматика: Орудний відмінок (Grammar: Instrumental case)**
>
> Але коли ми описуємо роль або професію, ми говоримо про функцію. 
> (But when we describe a role or profession, we are talking about a function.)
>
> Для цієї граматичної функції українська мова використовує орудний відмінок. 
> (For this grammatical function, the Ukrainian language uses the Instrumental case.)
>
> Мова розрізняє вашу ідентичність і вашу роль.
> (The language distinguishes your identity and your role.)"""

text = text.replace(old_p1, new_p1)
text = text.replace(old_p2, new_p2)

with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'w', encoding='utf-8') as f:
    f.write(text)
