import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-store.md', 'r') as f:
    text = f.read()

def replace_text(old, new):
    global text
    if old in text:
        text = text.replace(old, new)
    else:
        print("Could not find:", old[:50])

# Fix 1: Dative 'Вам' and long sentence in translation
old_1 = """**Фіна́л ва́ших заку́пів — це ка́са. Каси́р пра́цює ду́же шви́дко. Він ви́користовує коро́ткі фра́зи. Вам тре́ба слу́хати ува́жно.** (The final stage of any shopping trip takes place at the checkout. The cashier works very quickly. They use short phrases. You need to listen carefully.)"""
new_1 = """**Фінал ваших закупів — це каса. Касир працює дуже швидко. Він говорить короткі фрази. Ми слухаємо уважно.** (The end of shopping is the checkout. The cashier works very fast. He says short phrases. We listen carefully.)"""
replace_text(old_1, new_1)

# Fix 2: Complexity in translation of lesson overview
old_2 = """**У цьо́му уро́ці ми вивча́ємо пра́вила магази́ну. Ми вчи́мося шука́ти това́ри. Ми вчи́мося пита́ти про відді́ли. Тако́ж ми вчи́мося говори́ти на ка́сі.** (In this lesson, we will focus on the practical language you need to succeed in these environments. We will explore how to identify different store departments, how to ask for the location of specific items, and how to speak at the checkout.)"""
new_2 = """**У цьому уроці ми вивчаємо правила магазину. Ми вчимося шукати товари. Ми вчимося питати про відділи. Також ми говоримо на касі.** (In this lesson we study store rules. We learn to look for goods. We learn to ask about departments. Also we speak at the checkout.)"""
replace_text(old_2, new_2)

# Fix 3: Accents causing length issues
old_3 = """**Слова́ «ціна́», «ка́са» і «зни́жка» — це жіно́чий рід. Тому́ ми за́вжди ка́жемо «ця ціна́» чи «ця зни́жка». Це важли́во пам'ята́ти.** (The words "price", "checkout", and "discount" are feminine. Therefore we always say "this price" or "this discount". It is important to remember this.)"""
new_3 = """**Слова «ціна», «каса» і «знижка» — це жіночий рід. Тому ми завжди кажемо «ця ціна». Або ми кажемо «ця знижка». Це важливо знати.** (The words price, checkout, and discount are feminine. Therefore we always say this price. Or we say this discount. This is important to know.)"""
replace_text(old_3, new_3)

# Fix 4: Add more Ukrainian to reach 35% immersion
old_4 = """Imagine you have just walked through the sliding doors of a massive Ukrainian supermarket. The lighting is bright, and the aisles stretch out before you. Your first task is to secure a way to carry your groceries. Depending on the size of your shopping list, you will look for either a «ко́шик» (basket) or a «візо́к» (cart)."""
new_4 = """**Ви йдете в супермаркет. Це великий магазин. Тут дуже світло. Ви хочете купити продукти. Спочатку ви шукаєте кошик. Або ви берете великий візок.** (You go into the supermarket. It is a big store. It is very bright here. You want to buy groceries. First you look for a basket. Or you take a big cart.)"""
replace_text(old_4, new_4)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-store.md', 'w') as f:
    f.write(text)
