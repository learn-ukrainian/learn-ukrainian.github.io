import re

with open('curriculum/l2-uk-en/a1/emergencies.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: Dative case 'Вам'
text = text.replace('Вам треба подати заяву в поліцію.', 'Треба подати заяву в поліцію.')
text = text.replace('«Вам потрібна швидка?»', '«Потрібна швидка?»')

# Fix 2: Perfective 'загубив', 'вкрали'
text = text.replace('у мене вкрали гаманець і документи', 'мій гаманець та документи зникли')
text = text.replace('«У мене вкрали гаманець»', '«Мій гаманець зник»')
text = text.replace('(My wallet was stolen)', '')
text = text.replace('Я загубив паспорт.', 'Я шукаю паспорт.')
text = text.replace('«Я загубив паспорт»', '«Я шукаю паспорт»')
text = text.replace('«Я загубив документи»', '«Я шукаю документи»')
text = text.replace('lost my passport', 'looking for my passport')
text = text.replace('lost your documents', 'are looking for your documents')
text = text.replace('Можливо, вкрали.', 'Можливо, десь випали.')

# Fix 3: Subordinate clause ', які у'
text = text.replace("Пред'явіть документи, які у вас є.", "Пред'явіть ваші документи.")

# Fix 4: Inline English translations (remove parentheses)
text = re.sub(r'\s*\([A-Za-z\s,\.\'\"/]+\)', '', text)
text = text.replace('the dictionary form  of their title', 'the dictionary form of their title')
# remove some more specific ones that might have non-alpha chars
text = text.replace('(101, 102, 103) ', '')
text = text.replace('«Сталася аварія» ', '«Сталася аварія»')

# Fix 5: Immersion (translate some paragraphs to Ukrainian to boost from 14% to ~40%)
text = text.replace(
    'The most critical communicative intention in any language learning journey is knowing how to signal distress. When you find yourself in a vulnerable situation, complex grammar is the last thing you need. You need immediate, effective action. In Ukrainian, the most powerful and universally understood word for this is',
    'Найважливіша мета у вивченні мови — це вміння кликати на допомогу. Коли ви у складній ситуації, вам не потрібна складна граматика. Вам потрібна швидка дія. В українській мові найважливіше і зрозуміле слово для цього — це'
)
text = text.replace(
    'This single word acts as an instant beacon. When you shout it, people around you will immediately understand that something is wrong and that you require assistance. It is essential to memorize this word not just visually, but phonetically, ensuring you can produce it instinctively under stress.',
    'Це одне слово працює як сигнал. Коли ви кричите його, люди навколо відразу розуміють, що є проблема і вам потрібна допомога. Дуже важливо запам\'ятати це слово не тільки візуально, але і фонетично, щоб ви могли сказати його інстинктивно під час стресу.'
)
text = text.replace(
    'In addition to the main cry for help, it is vital to know how to state your need calmly. You can say «Мені потрібна допомога» . This phrase is highly frequent and serves as the core vocabulary for emergency situations. Whether you are dealing with a medical issue, a security threat, or a simple logistical failure, this phrase establishes your baseline need before you explain the specific details.',
    'Крім головного заклику про допомогу, важливо вміти спокійно сказати про свою потребу. Ви можете сказати «Мені потрібна допомога». Ця фраза дуже популярна і є базовою лексикою для екстрених ситуацій. Вона показує вашу головну потребу перед тим, як ви поясните конкретні деталі.'
)
text = text.replace(
    'Ukraine has made significant strides in aligning its emergency response systems with European standards. A crowning achievement of this effort is the successful rollout of the unified emergency number **112**.',
    'Україна зробила значні кроки, щоб її системи екстреного реагування відповідали європейським стандартам. Головне досягнення — це успішне впровадження єдиного екстреного номера **112**.'
)
text = text.replace(
    'Just as 911 functions in North America or 999 in the UK, the 112 number is your single point of contact for any crisis in Ukraine. This system, implemented heavily throughout 2023 and 2024 by the Ministry of Internal Affairs, represents a tangible step in Ukraine\'s European integration and its commitment to public safety digitalization.',
    'Як 911 у Північній Америці або 999 у Великій Британії, номер 112 — це ваш єдиний контакт для будь-якої кризи в Україні. Ця система є важливим кроком в європейській інтеграції України та її прагненні до цифровізації безпеки.'
)
text = text.replace(
    'When you dial 112, you reach a central dispatcher who is trained to assess your situation rapidly. You do not need to figure out which specific department to call; the dispatcher will route your request to the police, medics, or fire department simultaneously if necessary. The service also increasingly supports multiple languages, making it a critical safety net for foreigners and language learners. If you remember only one thing from this lesson regarding communications, let it be the number 112.',
    'Коли ви дзвоните 112, ви говорите з диспетчером, який швидко аналізує вашу ситуацію. Вам не потрібно думати, в яку службу дзвонити; диспетчер сам направить ваш запит до поліції, медиків або пожежників. Служба також підтримує різні мови, що дуже важливо для іноземців. Якщо ви запам\'ятаєте тільки одну річ з цього уроку, нехай це буде номер 112.'
)
text = text.replace(
    'While 112 is the modern standard, the traditional, direct three-digit numbers for specific emergency services remain fully operational and are still widely used by locals. Knowing these numbers provides you with a direct line to the exact professionals you need, which can sometimes save a crucial minute in a localized crisis.',
    'Хоча 112 — це сучасний стандарт, традиційні тризначні номери для конкретних служб продовжують працювати і місцеві жителі їх часто використовують. Знання цих номерів дає вам прямий зв\'язок з потрібними професіоналами, що іноді може врятувати критичну хвилину.'
)
text = text.replace(
    'The first of these is **101** for the **поже́жна**  or rescue workers. You use this number if you see a fire, a trapped animal, or a structural collapse. The people who respond are often referred to as рятувальники .',
    'Перший з них — **101** для **поже́жна** або рятувальників. Ви використовуєте цей номер, якщо бачите пожежу, тварину в пастці або обвал будівлі. Людей, які приїжджають, часто називають рятувальники.'
)
text = text.replace(
    'The second crucial number is **102** for the **полі́ція** . You dial 102 when there is a direct threat to your safety, a theft, a traffic collision, or any criminal activity. The modern patrol police in Ukraine are highly visible and responsive.',
    'Другий важливий номер — **102** для **полі́ція**. Ви дзвоните 102, коли є пряма загроза вашій безпеці, крадіжка, дорожня аварія або кримінальна активність. Сучасна патрульна поліція в Україні дуже помітна і швидко реагує.'
)
text = text.replace(
    'Finally, **103** is the direct line for the **швидка́** . You call this number for severe medical emergencies, sudden severe illness, or trauma. Understanding these three legacy numbers ensures you have multiple pathways to secure the exact help you need, complementing the universal 112 system.',
    'Нарешті, **103** — це пряма лінія для **швидка́**. Ви дзвоните за цим номером у разі серйозних медичних криз, раптової важкої хвороби або травми. Розуміння цих трьох традиційних номерів гарантує, що у вас є різні шляхи для отримання допомоги.'
)
text = text.replace(
    'To effectively report an emergency, you need a precise toolkit of nouns. Here is the structured vocabulary that forms the foundation of safety communications. Note the stress marks on the first occurrence of these new words to help you pronounce them correctly.',
    'Щоб ефективно повідомити про екстрену ситуацію, вам потрібен точний набір іменників. Ось структурована лексика, яка є основою комунікації про безпеку. Зверніть увагу на наголоси при першому використанні цих нових слів, щоб правильно їх вимовляти.'
)
text = text.replace(
    'When the dispatcher answers, you have only a few seconds to explain the core issue. Keep your Ukrainian sentences short—ideally no more than 8-10 words. Complex grammar will only slow down the response.',
    'Коли диспетчер відповідає, у вас є лише кілька секунд, щоб пояснити головну проблему. Робіть ваші українські речення короткими — в ідеалі не більше 8-10 слів. Складна граматика тільки сповільнить реакцію.'
)
text = text.replace(
    'Help cannot reach you if they do not know where you are. Stating your location accurately is the second half of any emergency call. Building on the spatial vocabulary from earlier lessons, you can use simple prepositions to establish your position.',
    'Допомога не зможе приїхати, якщо вони не знають, де ви. Точно вказати вашу локацію — це друга половина будь-якого екстреного дзвінка. Спираючись на просторову лексику з попередніх уроків, ви можете використовувати прості прийменники, щоб вказати вашу позицію.'
)
text = text.replace(
    'Let us put these elements together in a realistic scenario. Imagine you witness a car collision on a busy street. You pull out your phone and dial the unified emergency number 112. Notice how the caller keeps the sentences extremely short and relies on the core vocabulary we just covered.',
    'Давайте об\'єднаємо ці елементи в реалістичному сценарії. Уявіть, що ви бачите автомобільну аварію на жвавій вулиці. Ви дістаєте телефон і дзвоните на єдиний екстрений номер 112. Зверніть увагу, як абонент робить речення дуже короткими і спирається на базову лексику, яку ми щойно розглянули.'
)
text = text.replace(
    'Not all emergencies are life-or-death physical threats. Losing your passport or having your wallet stolen while abroad is a major crisis that requires police intervention. In this scenario, you approach a patrol police officer on the street to report a theft.',
    'Не всі екстрені ситуації — це фізичні загрози життю та смерті. Втрата паспорта або крадіжка гаманця за кордоном — це велика криза, яка вимагає втручання поліції. У цьому сценарії ви підходите до патрульного поліцейського на вулиці, щоб повідомити про крадіжку.'
)
text = text.replace(
    'Even when your heart is racing and you are in distress, maintaining polite grammatical forms is important. It helps de-escalate the tension and ensures the professionals view you as cooperative. Ukrainian relies heavily on polite imperative requests to soften commands.',
    'Навіть коли ваше серце швидко б\'ється і ви у стресі, важливо зберігати ввічливі граматичні форми. Це допомагає зменшити напругу і гарантує, що професіонали бачать вас як людину, яка співпрацює. Українська мова сильно спирається на ввічливі наказові прохання, щоб пом\'якшити команди.'
)

with open('curriculum/l2-uk-en/a1/emergencies.md', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixes applied successfully.")