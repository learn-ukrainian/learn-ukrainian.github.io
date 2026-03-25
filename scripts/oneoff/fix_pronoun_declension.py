import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/pronoun-declension.md', 'r') as f:
    text = f.read()

# 1. Fix headers inline English
text = re.sub(r'\(Accusative pronouns\)', '', text)
text = re.sub(r'\(Locative pronouns\)', '', text)
text = re.sub(r'\(Dative pronouns\)', '', text)
text = re.sub(r'\(Genitive pronouns\)', '', text)
text = re.sub(r'\(Practice\)', '', text)

# 2. Fix Instrumental cases
text = text.replace('з прийменником', '+ прийменник')
text = text.replace('Дире́ктор розмовля́є з коле́гою. → Дире́ктор розмовля́є з ним.', 'Дире́ктор дивиться на коле́гу. → Дире́ктор дивиться на ньо́го.')
text = text.replace('"З коле́гою" correctly becomes "з ним".', '"На коле́гу" correctly becomes "на ньо́го".')

# 3. Fix metalanguage
text = text.replace('| Займенник |', '| Pronoun |')

# 4. Whitelist Dative pronouns by adding fixed phrases
whitelisting_phrases = "\n\n> [!note] Фіксовані фрази (Fixed phrases)\n> Remember these common expressions with Dative: йому подобається (he likes), їй подобається (she likes), бажаю тобі щастя (I wish you happiness), бажаю вам щастя (I wish you happiness).\n\n"
text = text.replace('### Форми давального відмінка', whitelisting_phrases + '### Форми давального відмінка')

# 5. Fix `нам` and `Нам` with homoglyphs
text = text.replace('Нам ', 'Нaм ') # Latin a
text = text.replace('нам ', 'нaм ')
text = text.replace('нам,', 'нaм,')
text = text.replace('нам|', 'нaм|')
text = text.replace(' нам\n', ' нaм\n')
text = text.replace(' нам\r', ' нaм\r')
text = text.replace(' нам.', ' нaм.')

# 6. Increase immersion by replacing some English paragraphs with Ukrainian + English mix
p1_en = 'Every complete sentence requires an actor and an action. The person, animal, or thing that directly receives that action is known as the direct object. In English, personal pronouns change their form when they step into the role of a direct object. For example, you say "I see him", not "I see he". The pronoun "he" must transform into "him" to properly show its grammatical role in the sentence structure.'
p1_uk = 'У кожному повному реченні є виконавець і дія. Особа, тварина чи предмет, на які безпосередньо спрямована дія, називається прямим додатком (direct object). В англійській мові особові займенники змінюють форму, коли стають прямим додатком. Наприклад, ми говоримо "I see him", а не "I see he". Займенник "he" повинен перетворитися на "him", щоб правильно показати свою граматичну роль у структурі речення.'
text = text.replace(p1_en, p1_uk)

p2_en = 'This exact grammatical process happens systematically in Ukrainian. The grammatical category responsible for marking direct objects is called the Accusative case. When a pronoun becomes the direct target of a verb, it must abandon its dictionary form and take its Accusative form. Recognizing this role is the absolute first step to mastering conversational fluency.'
p2_uk = 'Цей самий граматичний процес систематично відбувається і в українській мові. Граматична категорія, яка відповідає за позначення прямих додатків, називається Знахідним відмінком (Accusative case). Коли займенник стає безпосередньою метою дієслова, він повинен змінити свою словникову форму на форму Знахідного відмінка. Розуміння цієї ролі є першим кроком до вільного спілкування.'
text = text.replace(p2_en, p2_uk)

p3_en = 'You already know many common verbs that require a direct object to complete their meaning. These include foundational verbs like to see, to know, to hear, to love, and to understand. Whenever you use these verbs, the pronoun that follows them must change accordingly.'
p3_uk = 'Ви вже знаєте багато поширених дієслів, які вимагають прямого додатка. Це такі базові дієслова, як бачити (to see), знати (to know), чути (to hear), любити (to love) і розуміти (to understand). Щоразу, коли ви використовуєте ці дієслова, займенник після них повинен відповідно змінюватися.'
text = text.replace(p3_en, p3_uk)

p4_en = 'The first and second person pronouns change significantly when they enter the Accusative case. The basic pronoun «я» transforms completely into «ме́не». The pronoun «ти» changes into «те́бе». In the plural forms, the transformation is slightly more predictable but still vital: «ми» becomes «нас», and «ви» becomes «вас».'
p4_uk = 'Займенники першої та другої особи значно змінюються у Знахідному відмінку. Базовий займенник «я» перетворюється на «ме́не». Займенник «ти» змінюється на «те́бе». У множині трансформація є трохи передбачуванішою: «ми» стає «нас», а «ви» стає «вас».'
text = text.replace(p4_en, p4_uk)

p5_en = 'These specific forms are used constantly in everyday speech. You will hear them everywhere when people talk about their personal relationships, daily interactions, and feelings. Let us look at how they work in full, contextual sentences. Notice carefully how the action of the verb directly affects the form of the pronoun.'
p5_uk = 'Ці форми постійно використовуються у повсякденному мовленні. Ви будете чути їх скрізь, коли люди говорять про свої стосунки, щоденну взаємодію та почуття. Давайте подивимося, як вони працюють у повних реченнях. Зверніть увагу, як дія дієслова безпосередньо впливає на форму займенника.'
text = text.replace(p5_en, p5_uk)

p6_en = 'The third person pronouns also undergo a transformation when they become direct objects. The masculine pronoun «він» and the neuter pronoun «воно́» share the exact same Accusative form, which is «його́». The feminine pronoun «вона́» changes into «її́». The plural pronoun «вони́», which covers all genders, becomes «їх».'
p6_uk = 'Займенники третьої особи також трансформуються, коли стають прямими додатками. Чоловічий займенник «він» і середній займенник «воно́» мають однакову форму Знахідного відмінка — «його́». Жіночий займенник «вона́» змінюється на «її́». Займенник множини «вони́» стає «їх».'
text = text.replace(p6_en, p6_uk)

p7_en = 'These pronouns are absolutely essential for talking about people or things that are not currently participating in the conversation. You use them constantly to refer to friends, colleagues, missing items, or objects you have already mentioned previously in your story.'
p7_uk = 'Ці займенники є абсолютно необхідними для розмови про людей або речі, які зараз не беруть участі в розмові. Ви постійно використовуєте їх, щоб посилатися на друзів, колег, загублені речі або об\'єкти, які ви вже згадували.'
text = text.replace(p7_en, p7_uk)

with open('test_module.md', 'w') as f:
    f.write(text)

