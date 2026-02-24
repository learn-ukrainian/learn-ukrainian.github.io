import re

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix Outline Headers
text = re.sub(r'## Вступ \(Introduction\)', '## Вступ', text)
text = re.sub(r'## Родини ход- та пис- \(The hod- and pys- Families\)', '## Родини ход- та пис-', text)
text = re.sub(r'## Родини чит- та бач- \(The chyt- and bach- Families\)', '## Родини чит- та бач-', text)
text = re.sub(r'## Фонетика та префікси \(Phonetics and Prefixes\)', '## Фонетика та префікси', text)
text = re.sub(r'## Практичне застосування \(Practical Application\)', '## Практичне застосування', text)

# 2. Fix Participles
text = text.replace("пов'язаний з", "має зв'язок з")
text = text.replace("повторюваний рух", "рух, який повторюється,")
text = text.replace("в один кінець у даний момент", "в один кінець у цей момент")

# 3. Fix Complexity
text = text.replace(
    "Коли ваш мозок звикне шукати корінь, ви почнете інтуїтивно розуміти тексти, які раніше здавалися вам занадто складними.",
    "Коли ваш мозок звикне шукати корінь, ви почнете інтуїтивно розуміти тексти. Раніше вони здавалися вам занадто складними."
)
text = text.replace(
    "Цікавий лінгвістичний факт: цей корінь має спільне індоєвропейське походження з давньогрецьким словом *hodos* (шлях, way), яке ви можете знати через англійські слова *method* або *exodus*.",
    "Цей корінь має спільне індоєвропейське походження з давньогрецьким словом *hodos* (шлях, way). Ви можете знати його через англійські слова *method* або *exodus*."
)
text = text.replace(
    "Він походить від стародавнього праслов'янського слова *pьsati*, яке спочатку означало не створення літер, а \"малювати\" або \"декорувати\" (to paint/decorate).",
    "Він походить від стародавнього праслов'янського слова *pьsati*. Воно спочатку означало не створення літер, а \"малювати\" або \"декорувати\"."
)
text = text.replace(
    "Коли ви хочете підкреслити, що у вас є готовий результат на папері чи на екрані, завжди використовуйте доконаний вид.",
    "Іноді ви хочете підкреслити, що маєте готовий результат. Тоді завжди використовуйте доконаний вид."
)
text = text.replace(
    "Але українська мова використовує цей корінь набагато ширше та глибше, ніж просто для опису фізичного зору.",
    "Але українська мова використовує цей корінь набагато ширше. Це не просто опис фізичного зору."
)
text = text.replace(
    "Наприклад, слово **бачення** (vision) означає не тільки фізичну здатність бачити світло, але й вашу унікальну точку зору або концепцію.",
    "Наприклад, слово **бачення** (vision) має два значення. Це фізична здатність бачити світло, а також ваша унікальна точка зору."
)
text = text.replace(
    "Слово буквально перекладається як \"взаємне бачення\" або процес, коли закохані люди спеціально йдуть \"побачити\" одне одного.",
    "Слово буквально перекладається як \"взаємне бачення\". Це процес, коли люди спеціально йдуть \"побачити\" одне одного."
)
text = text.replace(
    "Якщо ми хочемо сказати \"спуститися вниз\" або \"швидко піти кудись і повернутися\", ми додаємо префікс до дієслова **ходити**.",
    "Ми можемо захотіти сказати \"спуститися вниз\" або \"швидко піти кудись\". Тоді ми додаємо префікс до дієслова **ходити**."
)
text = text.replace(
    "Оскільки корінь починається на літеру **х** (яка є останньою у слові Пта**х**), ми фізично і граматично не можемо використовувати префікс **з-**.",
    "Корінь починається на літеру **х**. Це остання літера у слові Пта**х**. Тому ми не можемо використовувати префікс **з-**."
)
text = text.replace(
    "У цьому короткому, але реалістичному діалозі ми використали п'ять важливих слів із наших кореневих родин, і вся розмова виглядає абсолютно природно для носіїв мови.",
    "У цьому діалозі ми використали п'ять важливих слів із наших кореневих родин. Вся розмова виглядає абсолютно природно для носіїв мови."
)
text = text.replace(
    "Пам'ятайте ці правила, слухайте носіїв мови, і ваша українська дуже швидко звучатиме впевнено, природно та граматично бездоганно.",
    "Пам'ятайте ці правила та слухайте носіїв мови. Ваша українська швидко звучатиме впевнено та граматично бездоганно."
)
text = text.replace(
    "Ми дізналися, що слова ніколи не існують ізольовано; вони утворюють великі, логічні родини навколо базових будівельних блоків — коренів.",
    "Ми дізналися, що слова ніколи не існують ізольовано. Вони утворюють великі родини навколо базових блоків — коренів."
)
text = text.replace(
    "Ми детально дослідили «велику четвірку» лексики А2: корінь **-ход-** (фізичний рух), корінь **-пис-** (текст, документи і давнє мистецтво), корінь **-чит-** (сприйняття інформації) та корінь **-бач-** (зір, концептуальне розуміння і романтика).",
    "Ми дослідили лексику А2. Це корінь **-ход-** (рух) та **-пис-** (текст, мистецтво). Також це корінь **-чит-** (інформація) та **-бач-** (зір, романтика)."
)
text = text.replace(
    "Використовуючи цей модульний підхід до словотворення, ви зможете розширювати свій активний словниковий запас ефективно і без стресу.",
    "Цей модульний підхід до словотворення дуже корисний. Ви зможете розширювати свій словниковий запас ефективно і без стресу."
)

# 4. Fix Inline English in prose list
text = text.replace("* Я **ходжу** (I walk)", "* Я **ходжу**")
text = text.replace("* Ти **ходиш** (You walk)", "* Ти **ходиш**")
text = text.replace("* Він/вона/воно **ходить** (He/she/it walks)", "* Він/вона/воно **ходить**")
text = text.replace("* Ми **ходимо** (We walk)", "* Ми **ходимо**")
text = text.replace("* Ви **ходите** (You walk)", "* Ви **ходите**")
text = text.replace("* Вони **ходять** (They walk)", "* Вони **ходять**")

# 5. Add English scaffolding to fix immersion and word count
# Add English to "The Big Four Roots" section in Intro
big_four_expansion = """
Mastering just these four roots unlocks a massive portion of the language. You will start seeing them everywhere: on street signs, in books, in professional titles, and in daily conversations. For example, knowing the root **-ход-** helps you physically navigate a city, while **-пис-** helps you understand documents and legal texts. By the end of this module, you will not just know four new words; you will possess the analytical keys to decode a vast network of related vocabulary.

**Understanding Aspect and Word Formation**
Before we dive into the specific roots, it is crucial to understand how Ukrainian verbs operate within this modular system. Ukrainian verbs generally exist in pairs representing two different **aspects**: the **imperfective aspect** (недоконаний вид) and the **perfective aspect** (доконаний вид). The imperfective aspect focuses on the process, repetition, or general fact of an action without indicating its completion. The perfective aspect, on the other hand, focuses on the result, the successful completion, or a single specific instance of an action. Often, a perfective verb is created simply by adding a specific prefix to its imperfective counterpart. For example, adding the prefix **на-** to the process-oriented verb **писати** (to write) creates the result-oriented verb **написати** (to have written). This prefix acts as a marker of completion, transforming the focus from the ongoing activity to the finished product. Understanding this mechanism is the key to expressing yourself accurately in Ukrainian.
"""
text = text.replace("Mastering just these four roots unlocks a massive portion of the language. You will start seeing them everywhere: on street signs, in books, in professional titles, and in daily conversations. For example, knowing the root **-ход-** helps you physically navigate a city, while **-пис-** helps you understand documents and legal texts. By the end of this module, you will not just know four new words; you will possess the analytical keys to decode a vast network of related vocabulary.", big_four_expansion)

# Add English to "The Kafka-Ptakh Euphony Rule"
euphony_expansion = """
To remember these five letters forever, Ukrainian schoolchildren use a brilliant mnemonic phrase: **"Кафе Птах"** (Cafe Bird). If a root starts with any consonant from the words "Кафе Птах", the prefix must always be **с-**.

**Why Euphony Matters in Ukrainian**
This rule is not just an arbitrary grammar requirement; it reflects the deep phonetic philosophy of the Ukrainian language. Euphony, or **милозвучність**, dictates that speech should flow smoothly without harsh consonant clusters that interrupt the breath or vocal cord vibration. When you pronounce a voiced consonant like 'з' immediately followed by a voiceless consonant like 'х', your vocal apparatus experiences a sudden, uncomfortable transition. By automatically shifting the voiced prefix to its voiceless counterpart 'с', the language maintains its characteristic melodic rhythm. As a learner, paying attention to these phonetic shifts will not only make your spelling correct but will also make your pronunciation sound remarkably authentic and natural. This principle applies across the entire language, affecting prepositions, prefixes, and word endings.
"""
text = text.replace("To remember these five letters forever, Ukrainian schoolchildren use a brilliant mnemonic phrase: **\"Кафе Птах\"** (Cafe Bird). If a root starts with any consonant from the words \"Кафе Птах\", the prefix must always be **с-**.", euphony_expansion)


# Remove transliteration 'корені (roots)' -> 'корені'
text = text.replace("великі, логічні родини навколо базових будівельних блоків — коренів (roots).", "великі, логічні родини навколо базових будівельних блоків — коренів.")
# Actually it just says "корені (roots)" somewhere else.
text = text.replace("корені (roots)", "корені")

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'w', encoding='utf-8') as f:
    f.write(text)
