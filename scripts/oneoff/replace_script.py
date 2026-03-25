import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-store.md', 'r') as f:
    text = f.read()

def replace_text(old, new):
    global text
    if old in text:
        text = text.replace(old, new)
    else:
        print("Could not find:", old[:50])

eng_1 = """Shopping for food is a fundamental human activity, but the environment in which we do it varies wildly across the globe. When you walk into a Ukrainian «суперма́ркет» (supermarket), you might be surprised by the sheer scale and aesthetic ambition of the space. While convenience stores exist, large retail chains dominate the urban landscape, offering everything from freshly baked artisan bread to imported delicacies."""

ukr_1 = """**Украї́нський суперма́ркет — це ду́же вели́кий магази́н. Тут є сві́жий хліб і смачни́й сир. Ви мо́жете купи́ти всі проду́кти. Украї́нці ду́же любля́ть ці магази́ни. Вони́ ма́ють гарни́й диза́йн.** (Shopping for food is a fundamental human activity. When you walk into a Ukrainian supermarket, you see a large and beautiful space. There is fresh bread and tasty cheese. Ukrainians love big stores.)"""

replace_text(eng_1, ukr_1)

eng_2 = """One of the most distinctive aspects of modern Ukrainian retail is the emphasis on design and thematic experience. Rather than building identical, sterile boxes, major chains often turn their stores into artistic installations. This transforms a mundane chore into an engaging visual journey."""

ukr_2 = """**Мере́жа «Сільпо́» ма́є темати́чні магази́ни. Ко́жен магази́н — це мисте́цтво. Оди́н магази́н ма́є те́му яма́йського куро́рту. І́нший магази́н ма́є те́му відеогри́. Це ро́бить проце́с купі́влі ду́же ціка́вим.** (The "Silpo" chain has thematic stores. Every store is art. One store has a Jamaican resort theme. Another store has a video game theme. This transforms a mundane chore into an engaging visual journey.)"""

replace_text(eng_2, ukr_2)

eng_3 = """Beyond the visuals, there is a distinct communicative rhythm to shopping in Ukraine. The interactions are fast, polite, and highly predictable. Foremost among these is the "Bag Ritual." When you reach the checkout line, or «ка́са», the cashier will almost always initiate the transaction with a single, highly specific question: «Паке́т потрі́бен?» (Do you need a bag?). Knowing how to respond to this instantly makes you part of the local flow."""

ukr_3 = """**На ка́сі є свої́ пра́вила. Це ду́же шви́дкий проце́с. Каси́р за́вжди запиту́є про паке́т. Він ка́же: «Паке́т потрі́бен?». Ви мо́жете сказа́ти: «Так, будь ла́ска» або́ «Ні, дя́кую». Це ду́же важли́вий ритуа́л.** (Beyond the visuals, there is a distinct communicative rhythm to shopping in Ukraine. The interactions are fast. When you reach the checkout line, the cashier will almost always ask: "Do you need a bag?". This is a very important ritual.)"""

replace_text(eng_3, ukr_3)

eng_4 = """In this lesson, we will focus on the practical language you need to succeed in these environments. We will explore how to identify different store departments, how to ask for the location of specific items, and how to navigate the rapid-fire questions at the checkout counter."""

ukr_4 = """**У цьо́му уро́ці ми вивча́ємо пра́вила магази́ну. Ми вчи́мося шука́ти това́ри. Ми вчи́мося пита́ти про відді́ли. Тако́ж ми вчи́мося говори́ти на ка́сі.** (In this lesson, we will focus on the practical language you need to succeed in these environments. We will explore how to identify different store departments, how to ask for the location of specific items, and how to speak at the checkout.)"""

replace_text(eng_4, ukr_4)

eng_5 = """To efficiently navigate a large store, you need to understand how it is organized. A specific section or department is called a «ві́дділ». Supermarkets are divided into logical zones, and knowing these names allows you to read overhead signs and follow directions."""

ukr_5 = """**Ко́жен магази́н ма́є відді́ли. Ві́дділ — це спеціа́льна зо́на. Тут є моло́чний ві́дділ. Там є м'ясни́й ві́дділ. Зна́ння цих слів допомага́є орієнтува́тися.** (Every store has departments. A department is a special zone. Here is the dairy department. There is the meat department. Knowing these words allows you to follow directions.)"""

replace_text(eng_5, ukr_5)

eng_6 = """If you find yourself lost among the aisles, you will need to ask store employees for assistance. There are two primary ways to ask for the location of an item, both of which are polite and natural."""

ukr_6 = """**Іноді́ ви не ба́чите това́р. Ви шука́єте смета́ну чи молоко́. Ви мо́жете запита́ти працівника́. Це ду́же про́сто і вві́чливо.** (If you find yourself lost among the aisles, you will need to ask store employees for assistance. You can ask an employee. It is very simple and polite.)"""

replace_text(eng_6, ukr_6)

eng_7 = """The final stage of any shopping trip takes place at the «ка́са» (checkout). Because this environment processes hundreds of customers an hour, the language used here is highly compressed. The cashier will speak quickly and use fixed phrases."""

ukr_7 = """**Фіна́л ва́ших заку́пів — це ка́са. Каси́р пра́цює ду́же шви́дко. Він ви́користовує коро́ткі фра́зи. Вам тре́ба слу́хати ува́жно.** (The final stage of any shopping trip takes place at the checkout. The cashier works very quickly. They use short phrases. You need to listen carefully.)"""

replace_text(eng_7, ukr_7)

eng_8 = """The transaction generally opens with a question about bags. If you need one, they will provide a «паке́т». The interaction then moves immediately to the payment method."""

ukr_8 = """**Споча́тку каси́р пита́є про паке́т. Якщо́ ви ка́жете «так», він дає́ паке́т. По́тім він пита́є про опла́ту.** (The transaction generally opens with a question about bags. If you say "yes", they give you a bag. Then they ask about payment.)"""

replace_text(eng_8, ukr_8)

eng_9 = """One of the most persistent hurdles for learners is choosing the correct grammatical case when talking about stores. The decision hinges entirely on whether you are describing movement toward a destination or a static presence within a location."""

ukr_9 = """**Ви йдете́ в магази́н чи ви вже там? Це важли́ве пра́вило. Якщо́ це на́прямок, ми ка́жемо «в магази́н». Якщо́ це мі́сце, ми ка́жемо «у магази́ні».** (Are you going into the store or are you already there? This is an important rule. If it is a destination, we say "into the store". If it is a location, we say "in the store".)"""

replace_text(eng_9, ukr_9)

eng_10 = """Getting this distinction right is crucial. Using the location ending when describing movement sounds deeply unnatural to a native speaker. Always ask yourself: "Am I traveling there, or am I already inside?"""

ukr_10 = """**За́вжди пита́йте се́бе: «Я йду туди́ чи я вже там?». Це допомага́є уника́ти поми́лок. Украї́нці ду́же зве́ртають на це ува́гу.** (Always ask yourself: "Am I traveling there, or am I already inside?". This helps to avoid mistakes. Ukrainians pay a lot of attention to this.)"""

replace_text(eng_10, ukr_10)

eng_11 = """When discussing the concept of shopping itself, vocabulary precision matters. Due to a long history of linguistic interference and colonial pressure, a mixed speech pattern known as Surzhyk developed in parts of Ukraine. In Surzhyk, people often use the word «поку́пка» to describe a purchase or shopping trip."""

ukr_11 = """**Сло́во «поку́пка» — це су́ржик. Бага́то люде́й ка́жуть так на ву́лиці. Але́ це непра́вильно. Украї́нська мо́ва ма́є і́нші слова́.** (The word "pokupka" is Surzhyk. Many people say this on the street. But it is incorrect. The Ukrainian language has other words.)"""

replace_text(eng_11, ukr_11)

eng_12 = """While you will undoubtedly hear «поку́пка» on the street, it is considered non-standard. The authentic Ukrainian approach focuses on the process of acquiring goods."""

ukr_12 = """**Пра́вильно говори́ти «заку́пи» або́ «купі́вля». Це аутенти́чні украї́нські слова́. Вони́ звучать ду́же приро́дно.** (It is correct to say "zakupy" or "kupivlia". These are authentic Ukrainian words. They sound very natural.)"""

replace_text(eng_12, ukr_12)

eng_13 = """In a retail environment, you frequently need to point out specific items, ask about particular costs, or refer to a distinct checkout lane. To do this, you rely on demonstrative pronouns (words like "this" or "that")."""

ukr_13 = """**Ви ча́сто хо́чете показа́ти това́р. Або́ запита́ти про конкре́тну ціну́. Для цьо́го ми ви́користовуємо слова́ «цей», «ця», «це».** (You often want to show a product. Or ask about a specific price. For this we use the words "this" or "that".)"""

replace_text(eng_13, ukr_13)

eng_14 = """Because grammatical gender governs Ukrainian sentence structure, your pronoun must match the gender of the noun. For feminine nouns like «ціна́» (price), «ка́са» (checkout), and «зни́жка» (discount), you must strictly use the feminine demonstrative «ця» (this)."""

ukr_14 = """**Слова́ «ціна́», «ка́са» і «зни́жка» — це жіно́чий рід. Тому́ ми за́вжди ка́жемо «ця ціна́» чи «ця зни́жка». Це важли́во пам'ята́ти.** (The words "price", "checkout", and "discount" are feminine. Therefore we always say "this price" or "this discount". It is important to remember this.)"""

replace_text(eng_14, ukr_14)


with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-store.md', 'w') as f:
    f.write(text)
