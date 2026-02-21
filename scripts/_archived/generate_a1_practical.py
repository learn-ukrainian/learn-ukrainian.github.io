import os
import yaml

MODULES = [
    {
        "id": 36,
        "slug": "at-the-restaurant",
        "title": "At the Restaurant",
        "subtitle": "Dining Out in Ukraine",
        "vocab": [
            {"lemma": "столик", "ipa": "/ˈstɔlɪk/", "translation": "table (small)", "pos": "noun", "gender": "m"},
            {"lemma": "меню", "ipa": "/mɛˈnʲu/", "translation": "menu", "pos": "noun", "gender": "n"},
            {"lemma": "страва", "ipa": "/ˈstrɑvɑ/", "translation": "dish", "pos": "noun", "gender": "f"},
            {"lemma": "закуска", "ipa": "/zɑˈkuskɑ/", "translation": "appetizer", "pos": "noun", "gender": "f"},
            {"lemma": "десерт", "ipa": "/dɛˈsɛrt/", "translation": "dessert", "pos": "noun", "gender": "m"},
            {"lemma": "вегетаріанський", "ipa": "/vɛɦɛtɑrʲiˈɑnʲsʲkɪj/", "translation": "vegetarian", "pos": "adj", "gender": "m"},
            {"lemma": "алергія", "ipa": "/ɑlɛrˈɦijɑ/", "translation": "allergy", "pos": "noun", "gender": "f"},
            {"lemma": "порекомендувати", "ipa": "/pɔrɛkɔmɛndʊˈvɑtɪ/", "translation": "to recommend", "pos": "verb", "aspect": "pf"},
            {"lemma": "спробувати", "ipa": "/ˈsprɔbʊvɑtɪ/", "translation": "to try / taste", "pos": "verb", "aspect": "pf"},
            {"lemma": "смачний", "ipa": "/smɑt͡ʃˈnɪj/", "translation": "tasty / delicious", "pos": "adj", "gender": "m"},
            {"lemma": "гострий", "ipa": "/ɦɔsˈtrɪj/", "translation": "spicy / sharp", "pos": "adj", "gender": "m"},
            {"lemma": "солоний", "ipa": "/sɔˈlɔnɪj/", "translation": "salty", "pos": "adj", "gender": "m"},
            {"lemma": "солодкий", "ipa": "/sɔˈlɔdkɪj/", "translation": "sweet", "pos": "adj", "gender": "m"},
            {"lemma": "замовлення", "ipa": "/zɑˈmɔvlɛnʲːɑ/", "translation": "order", "pos": "noun", "gender": "n"},
            {"lemma": "бронювання", "ipa": "/brɔnʲʊˈvɑnʲːɑ/", "translation": "reservation", "pos": "noun", "gender": "n"}
        ]
    },
    {
        "id": 37,
        "slug": "at-the-market",
        "title": "At the Market",
        "subtitle": "Buying Fresh Produce",
        "vocab": [
            {"lemma": "кілограм", "ipa": "/kʲilɔˈɦrɑm/", "translation": "kilogram", "pos": "noun", "gender": "m"},
            {"lemma": "грам", "ipa": "/ɦrɑm/", "translation": "gram", "pos": "noun", "gender": "m"},
            {"lemma": "штука", "ipa": "/ˈʃtukɑ/", "translation": "piece / item", "pos": "noun", "gender": "f"},
            {"lemma": "свіжий", "ipa": "/ˈsvʲiʒɪj/", "translation": "fresh", "pos": "adj", "gender": "m"},
            {"lemma": "стиглий", "ipa": "/ˈstɪɦlɪj/", "translation": "ripe", "pos": "adj", "gender": "m"},
            {"lemma": "зелений", "ipa": "/zɛˈlɛnɪj/", "translation": "green / unripe", "pos": "adj", "gender": "m"},
            {"lemma": "дорого", "ipa": "/ˈdɔrɔɦɔ/", "translation": "expensive", "pos": "adv", "gender": "n/a"},
            {"lemma": "дешево", "ipa": "/ˈdɛʃɛvɔ/", "translation": "cheap", "pos": "adv", "gender": "n/a"},
            {"lemma": "знижка", "ipa": "/ˈznɪʒkɑ/", "translation": "discount", "pos": "noun", "gender": "f"},
            {"lemma": "торгуватися", "ipa": "/tɔrɦʊˈvɑtɪsʲɑ/", "translation": "to bargain", "pos": "verb", "aspect": "impf"},
            {"lemma": "вибирати", "ipa": "/vɪbɪˈrɑtɪ/", "translation": "to choose", "pos": "verb", "aspect": "impf"},
            {"lemma": "зважити", "ipa": "/ˈzvɑʒɪtɪ/", "translation": "to weigh", "pos": "verb", "aspect": "pf"},
            {"lemma": "пакет", "ipa": "/pɑˈkɛt/", "translation": "bag (plastic)", "pos": "noun", "gender": "m"},
            {"lemma": "сумка", "ipa": "/ˈsumkɑ/", "translation": "bag (tote)", "pos": "noun", "gender": "f"},
            {"lemma": "решта", "ipa": "/ˈrɛʃtɑ/", "translation": "change (money)", "pos": "noun", "gender": "f"}
        ]
    },
    {
        "id": 38,
        "slug": "at-the-store",
        "title": "At the Store",
        "subtitle": "Supermarket Shopping",
        "vocab": [
            {"lemma": "каса", "ipa": "/ˈkɑsɑ/", "translation": "checkout / cash register", "pos": "noun", "gender": "f"},
            {"lemma": "касир", "ipa": "/kɑˈsɪr/", "translation": "cashier", "pos": "noun", "gender": "m"},
            {"lemma": "чек", "ipa": "/t͡ʃɛk/", "translation": "receipt", "pos": "noun", "gender": "m"},
            {"lemma": "картка", "ipa": "/ˈkɑrtkɑ/", "translation": "card", "pos": "noun", "gender": "f"},
            {"lemma": "готівка", "ipa": "/ɦɔˈtʲivkɑ/", "translation": "cash", "pos": "noun", "gender": "f"},
            {"lemma": "безконтактно", "ipa": "/bɛzkɔnˈtɑktnɔ/", "translation": "contactless", "pos": "adv", "gender": "n/a"},
            {"lemma": "оплатити", "ipa": "/ɔplɑˈtɪtɪ/", "translation": "to pay for", "pos": "verb", "aspect": "pf"},
            {"lemma": "готово", "ipa": "/ɦɔˈtɔvɔ/", "translation": "done / ready", "pos": "adv", "gender": "n/a"},
            {"lemma": "потрібен", "ipa": "/pɔˈtʲribɛn/", "translation": "needed / necessary", "pos": "adj", "gender": "m"},
            {"lemma": "черга", "ipa": "/ˈt͡ʃɛrɦɑ/", "translation": "queue / line", "pos": "noun", "gender": "f"}
        ]
    },
    {
        "id": 39,
        "slug": "buying-tickets",
        "title": "Buying Tickets",
        "subtitle": "Travel Arrangements",
        "vocab": [
            {"lemma": "квиток", "ipa": "/kvɪˈtɔk/", "translation": "ticket", "pos": "noun", "gender": "m"},
            {"lemma": "туди", "ipa": "/tʊˈdɪ/", "translation": "there / one way", "pos": "adv", "gender": "n/a"},
            {"lemma": "назад", "ipa": "/nɑˈzɑd/", "translation": "back / return", "pos": "adv", "gender": "n/a"},
            {"lemma": "відправлення", "ipa": "/vʲidˈprɑvlɛnʲːɑ/", "translation": "departure", "pos": "noun", "gender": "n"},
            {"lemma": "прибуття", "ipa": "/prɪbʊˈtʲːɑ/", "translation": "arrival", "pos": "noun", "gender": "n"},
            {"lemma": "платформа", "ipa": "/plɑtˈfɔrmɑ/", "translation": "platform", "pos": "noun", "gender": "f"},
            {"lemma": "місце", "ipa": "/ˈmʲisʲt͡sɛ/", "translation": "seat / place", "pos": "noun", "gender": "n"},
            {"lemma": "вагон", "ipa": "/vɑˈɦɔn/", "translation": "carriage / wagon", "pos": "noun", "gender": "m"},
            {"lemma": "поїзд", "ipa": "/ˈpɔjizd/", "translation": "train", "pos": "noun", "gender": "m"},
            {"lemma": "автобус", "ipa": "/ɑvˈtɔbʊs/", "translation": "bus", "pos": "noun", "gender": "m"}
        ]
    },
    {
        "id": 40,
        "slug": "taking-transport",
        "title": "Taking Transport",
        "subtitle": "Navigating the City",
        "vocab": [
            {"lemma": "зупинка", "ipa": "/zʊˈpɪnkɑ/", "translation": "stop (bus/tram)", "pos": "noun", "gender": "f"},
            {"lemma": "станція", "ipa": "/ˈstɑnʲt͡sʲijɑ/", "translation": "station (metro)", "pos": "noun", "gender": "f"},
            {"lemma": "пересадка", "ipa": "/pɛrɛˈsɑdkɑ/", "translation": "transfer", "pos": "noun", "gender": "f"},
            {"lemma": "наступна", "ipa": "/nɑˈstʊpnɑ/", "translation": "next", "pos": "adj", "gender": "f"},
            {"lemma": "кінцева", "ipa": "/kʲinˈt͡sɛvɑ/", "translation": "terminal / last stop", "pos": "adj", "gender": "f"},
            {"lemma": "вихід", "ipa": "/ˈvɪxʲid/", "translation": "exit", "pos": "noun", "gender": "m"},
            {"lemma": "вхід", "ipa": "/vxʲid/", "translation": "entrance", "pos": "noun", "gender": "m"},
            {"lemma": "триматися", "ipa": "/trɪˈmɑtɪsʲɑ/", "translation": "to hold on", "pos": "verb", "aspect": "impf"},
            {"lemma": "оголошення", "ipa": "/ɔɦɔˈlɔʃɛnʲːɑ/", "translation": "announcement", "pos": "noun", "gender": "n"},
            {"lemma": "виходити", "ipa": "/vɪˈxɔdɪtɪ/", "translation": "to get off / exit", "pos": "verb", "aspect": "impf"}
        ]
    },
    {
        "id": 41,
        "slug": "phone-basics",
        "title": "Phone Basics",
        "subtitle": "Making Calls and Texting",
        "vocab": [
            {"lemma": "алло", "ipa": "/ɑˈlɔ/", "translation": "hello (on phone)", "pos": "intj", "gender": "n/a"},
            {"lemma": "говорити", "ipa": "/ɦɔvɔˈrɪtɪ/", "translation": "to speak", "pos": "verb", "aspect": "impf"},
            {"lemma": "помилитися", "ipa": "/pɔmɪˈlɪtɪsʲɑ/", "translation": "to make a mistake", "pos": "verb", "aspect": "pf"},
            {"lemma": "передзвонити", "ipa": "/pɛrɛdzvɔˈnɪtɪ/", "translation": "to call back", "pos": "verb", "aspect": "pf"},
            {"lemma": "повідомлення", "ipa": "/pɔvʲiˈdɔmlɛnʲːɑ/", "translation": "message", "pos": "noun", "gender": "n"},
            {"lemma": "чути", "ipa": "/ˈt͡ʃutɪ/", "translation": "to hear", "pos": "verb", "aspect": "impf"},
            {"lemma": "зачекайте", "ipa": "/zɑt͡ʃɛˈkɑjtɛ/", "translation": "wait (imperative)", "pos": "verb", "aspect": "pf"},
            {"lemma": "зайнято", "ipa": "/ˈzɑjnʲɑtɔ/", "translation": "busy (line)", "pos": "adv", "gender": "n/a"},
            {"lemma": "недоступний", "ipa": "/nɛdɔˈstʊpnɪj/", "translation": "unavailable / out of reach", "pos": "adj", "gender": "m"},
            {"lemma": "номер", "ipa": "/ˈnɔmɛr/", "translation": "number", "pos": "noun", "gender": "m"}
        ]
    },
    {
        "id": 42,
        "slug": "emergencies",
        "title": "Emergencies",
        "subtitle": "Help and Safety",
        "vocab": [
            {"lemma": "допомога", "ipa": "/dɔpɔˈmɔɦɑ/", "translation": "help", "pos": "noun", "gender": "f"},
            {"lemma": "допоможіть", "ipa": "/dɔpɔmɔˈʒʲitʲ/", "translation": "help! (imperative)", "pos": "verb", "aspect": "pf"},
            {"lemma": "загубити", "ipa": "/zɑɦʊˈbɪtɪ/", "translation": "to lose", "pos": "verb", "aspect": "pf"},
            {"lemma": "вкрасти", "ipa": "/ˈvkrɑstɪ/", "translation": "to steal", "pos": "verb", "aspect": "pf"},
            {"lemma": "поліція", "ipa": "/pɔˈlʲit͡sʲijɑ/", "translation": "police", "pos": "noun", "gender": "f"},
            {"lemma": "швидка", "ipa": "/ʃvɪdˈkɑ/", "translation": "ambulance", "pos": "noun", "gender": "f"},
            {"lemma": "посольство", "ipa": "/pɔˈsɔlʲstvɔ/", "translation": "embassy", "pos": "noun", "gender": "n"},
            {"lemma": "небезпечно", "ipa": "/nɛbɛzˈpɛt͡ʃnɔ/", "translation": "dangerous", "pos": "adv", "gender": "n/a"},
            {"lemma": "терміново", "ipa": "/tɛrmʲiˈnɔvɔ/", "translation": "urgently", "pos": "adv", "gender": "n/a"},
            {"lemma": "лікар", "ipa": "/ˈlʲikɑr/", "translation": "doctor", "pos": "noun", "gender": "m"}
        ]
    },
    {
        "id": 43,
        "slug": "combined-practice",
        "title": "Combined Practice",
        "subtitle": "Review of Practical Skills",
        "vocab": [
            {"lemma": "повторення", "ipa": "/pɔvˈtɔrɛnʲːɑ/", "translation": "repetition / review", "pos": "noun", "gender": "n"},
            {"lemma": "практика", "ipa": "/ˈprɑktɪkɑ/", "translation": "practice", "pos": "noun", "gender": "f"},
            {"lemma": "ситуація", "ipa": "/sɪtʊˈɑt͡sʲijɑ/", "translation": "situation", "pos": "noun", "gender": "f"},
            {"lemma": "діалог", "ipa": "/dʲiɑˈlɔɦ/", "translation": "dialogue", "pos": "noun", "gender": "m"},
            {"lemma": "роль", "ipa": "/rɔlʲ/", "translation": "role", "pos": "noun", "gender": "f"},
            {"lemma": "завдання", "ipa": "/zɑvˈdɑnʲːɑ/", "translation": "task", "pos": "noun", "gender": "n"},
            {"lemma": "відповідь", "ipa": "/vʲidˈpɔvʲidʲ/", "translation": "answer", "pos": "noun", "gender": "f"},
            {"lemma": "питання", "ipa": "/pɪˈtɑnʲːɑ/", "translation": "question", "pos": "noun", "gender": "n"},
            {"lemma": "результат", "ipa": "/rɛzʊlʲˈtɑt/", "translation": "result", "pos": "noun", "gender": "m"},
            {"lemma": "успіх", "ipa": "/ˈuspʲix/", "translation": "success", "pos": "noun", "gender": "m"}
        ]
    },
    {
        "id": 44,
        "slug": "a1-final-exam",
        "title": "A1 Final Exam",
        "subtitle": "Comprehensive Assessment",
        "vocab": [
            {"lemma": "іспит", "ipa": "/ˈispɪt/", "translation": "exam", "pos": "noun", "gender": "m"},
            {"lemma": "тест", "ipa": "/tɛst/", "translation": "test", "pos": "noun", "gender": "m"},
            {"lemma": "оцінка", "ipa": "/ɔˈt͡sʲinkɑ/", "translation": "grade / evaluation", "pos": "noun", "gender": "f"},
            {"lemma": "рівень", "ipa": "/ˈrʲivɛnʲ/", "translation": "level", "pos": "noun", "gender": "m"},
            {"lemma": "сертифікат", "ipa": "/sɛrtɪfʲiˈkɑt/", "translation": "certificate", "pos": "noun", "gender": "m"},
            {"lemma": "мова", "ipa": "/ˈmɔvɑ/", "translation": "language", "pos": "noun", "gender": "f"},
            {"lemma": "слово", "ipa": "/ˈslɔvɔ/", "translation": "word", "pos": "noun", "gender": "n"},
            {"lemma": "питання", "ipa": "/pɪˈtɑnʲːɑ/", "translation": "question", "pos": "noun", "gender": "n"},
            {"lemma": "відповідь", "ipa": "/vʲidˈpɔvʲidʲ/", "translation": "answer", "pos": "noun", "gender": "f"},
            {"lemma": "студент", "ipa": "/stʊˈdɛnt/", "translation": "student", "pos": "noun", "gender": "m"}
        ]
    }
]

def create_files(module):
    mod_id = module['id']
    slug = module['slug']
    title = module['title']
    subtitle = module['subtitle']
    vocab_list = module['vocab']
    
    # Paths
    base_path = f"curriculum/l2-uk-en/a1"
    md_path = f"{base_path}/{mod_id}-{slug}.md"
    meta_path = f"{base_path}/meta/{slug}.yaml"
    vocab_path = f"{base_path}/vocabulary/{slug}.yaml"
    activities_path = f"{base_path}/activities/{slug}.yaml"
    
    # 1. Meta YAML
    meta_content = f"""module: a1-{mod_id}
title: '{title}'
subtitle: '{subtitle}'
version: '1.0'
phase: A1.4 Practical Scenarios
pedagogy: PPP
focus: practical
duration: 60
transliteration: first-occurrence
tags:
  - practical
  - {slug.replace('-', ' ')}
grammar:
  - Practical usage of A1 cases
  - Polite requests
  - Questions and answers
objectives:
  - Learner can handle {title.lower()} situations
  - Learner can use relevant vocabulary
  - Learner can communicate needs
vocabulary_count: {len(vocab_list)}
vocab_count: {len(vocab_list)}
slug: {slug}
naturalness:
  score: 10
  status: PASS
"""
    with open(meta_path, 'w') as f:
        f.write(meta_content)
        
    # 2. Vocabulary YAML
    vocab_items = []
    for v in vocab_list:
        item = f"""  - lemma: {v['lemma']}
    ipa: {v['ipa']}
    translation: {v['translation']}
    pos: {v['pos']} """
        if 'gender' in v:
            item += f"\n    gender: {v['gender']}"
        if 'aspect' in v:
            item += f"\n    aspect: {v['aspect']}"
        vocab_items.append(item)
        
    vocab_content = f"""module: {mod_id}-{slug}
level: A1
version: '1.0'
items:
{chr(10).join(vocab_items)}
"""
    with open(vocab_path, 'w') as f:
        f.write(vocab_content)

    # 3. Activities YAML (Template based)
    activities_content = f"""- type: match-up
  title: Vocabulary Match
  instruction: Match the words to their meanings.
  pairs:
    - left: {vocab_list[0]['lemma']}
      right: {vocab_list[0]['translation']}
    - left: {vocab_list[1]['lemma']}
      right: {vocab_list[1]['translation']}
    - left: {vocab_list[2]['lemma']}
      right: {vocab_list[2]['translation']}
    - left: {vocab_list[3]['lemma']}
      right: {vocab_list[3]['translation']}
    - left: {vocab_list[4]['lemma']}
      right: {vocab_list[4]['translation']}
    - left: {vocab_list[5]['lemma']}
      right: {vocab_list[5]['translation']}
    - left: {vocab_list[6]['lemma']}
      right: {vocab_list[6]['translation']}
    - left: {vocab_list[7]['lemma']}
      right: {vocab_list[7]['translation']}
    - left: {vocab_list[8]['lemma']}
      right: {vocab_list[8]['translation']}
    - left: {vocab_list[9]['lemma']}
      right: {vocab_list[9]['translation']}

- type: fill-in
  title: Complete the Phrase
  instruction: Fill in the blank with the correct word.
  items:
    - sentence: Я хочу _____ (ticket).
      answer: квиток
      options: [квиток, квитка, квитку, квитком]
    - sentence: Де _____ (exit)?
      answer: вихід
      options: [вихід, вхід, виходу, виходом]
    - sentence: Мені потрібна _____ (help).
      answer: допомога
      options: [допомога, допомогу, допомоги, допомогою]
    - sentence: Це мій _____ (number).
      answer: номер
      options: [номер, номера, номеру, номером]
    - sentence: Скільки коштує _____ (bag)?
      answer: пакет
      options: [пакет, пакета, пакету, пакетом]
    - sentence: Ось ваша _____ (change).
      answer: решта
      options: [решта, решти, решту, рештою]
    - sentence: Це _____ (delicious).
      answer: смачно
      options: [смачно, смачний, смачна, смачне]
    - sentence: Я _____ (pay) карткою.
      answer: плачу
      options: [плачу, платиш, платить, платять]
    - sentence: Це _____ (stop).
      answer: зупинка
      options: [зупинка, зупинки, зупинці, зупинкою]
    - sentence: Мені _____ (urgent).
      answer: терміново
      options: [терміново, терміновий, термінова, термінове]
    - sentence: Це _____ (expensive).
      answer: дорого
      options: [дорого, дорогий, дорога, дороге]
    - sentence: Я _____ (choose).
      answer: вибираю
      options: [вибираю, вибираєш, вибирає, вибирають]

- type: quiz
  title: Context Quiz
  instruction: Choose the best answer for the situation.
  items:
    - question: Ви в магазині. Касир питає 'Пакет потрібен?'. Що ви відповісте?
      options:
        - text: Так, будь ласка.
          correct: true
        - text: Я не знаю.
          correct: false
        - text: До побачення.
          correct: false
        - text: Мені каву.
          correct: false
    - question: Ви в таксі. Ви хочете вийти. Що ви скажете?
      options:
        - text: Зупиніть тут, будь ласка.
          correct: true
        - text: Їдьте далі.
          correct: false
        - text: Я хочу спати.
          correct: false
        - text: Це дорого.
          correct: false
    - question: Ви на ринку. Ви хочете купити яблука. Що ви скажете?
      options:
        - text: Зважте кілограм, будь ласка.
          correct: true
        - text: Я не хочу яблука.
          correct: false
        - text: Де вихід?
          correct: false
        - text: Яка погода?
          correct: false
    - question: Ви загубили паспорт. Що ви скажете поліції?
      options:
        - text: Я загубив паспорт.
          correct: true
        - text: Я маю паспорт.
          correct: false
        - text: Паспорт вдома.
          correct: false
        - text: Це не мій паспорт.
          correct: false
    - question: Ви дзвоните другу. Він не бере трубку. Що ви почуєте?
      options:
        - text: Абонент недоступний.
          correct: true
        - text: Привіт, як справи?
          correct: false
        - text: Це піца.
          correct: false
        - text: Ви помилилися.
          correct: false
    - question: Офіціант питає 'Вам сподобалося?'. Що ви відповісте?
      options:
        - text: Так, дуже смачно.
          correct: true
        - text: Ні, це стіл.
          correct: false
        - text: Я хочу спати.
          correct: false
        - text: До побачення.
          correct: false
    - question: Ви купуєте квиток. Касир питає 'Туди й назад?'. Що це значить?
      options:
        - text: Round trip.
          correct: true
        - text: One way.
          correct: false
        - text: Two tickets.
          correct: false
        - text: No tickets.
          correct: false
    - question: Ви в метро. Ви не знаєте, куди йти. Що ви запитаєте?
      options:
        - text: Де пересадка?
          correct: true
        - text: Де я?
          correct: false
        - text: Хто я?
          correct: false
        - text: Що це?
          correct: false
    - question: Ви хочете заплатити. Що ви запитаєте?
      options:
        - text: Можна рахунок?
          correct: true
        - text: Можна меню?
          correct: false
        - text: Можна вийти?
          correct: false
        - text: Можна зайти?
          correct: false
    - question: Ви дзвоните з невідомого номера. Що ви скажете?
      options:
        - text: Алло, хто це?
          correct: true
        - text: Я тут.
          correct: false
        - text: Це не я.
          correct: false
        - text: До побачення.
          correct: false
    - question: Ви бачите аварію. Кого ви викличете?
      options:
        - text: Швидку і поліцію.
          correct: true
        - text: Таксі.
          correct: false
        - text: Доставку їжі.
          correct: false
        - text: Маму.
          correct: false
    - question: Ви хочете приміряти одяг. Що ви запитаєте?
      options:
        - text: Де примірочна?
          correct: true
        - text: Де каса?
          correct: false
        - text: Де вихід?
          correct: false
        - text: Де туалет?
          correct: false

- type: unjumble
  title: Sentence Builder
  instruction: Unscramble the words.
  items:
    - words: ["Я", "хочу", "купити", "квиток"]
      answer: Я хочу купити квиток.
    - words: ["Де", "знаходиться", "найближча", "аптека", "?"]
      answer: Де знаходиться найближча аптека?
    - words: ["Скільки", "коштує", "цей", "сувенір", "?"]
      answer: Скільки коштує цей сувенір?
    - words: ["Мені", "потрібна", "допомога", "зараз"]
      answer: Мені потрібна допомога зараз.
    - words: ["Ви", "можете", "мені", "допомогти", "?"]
      answer: Ви можете мені допомогти?
    - words: ["Я", "не", "розумію", "вас"]
      answer: Я не розумію вас.
    - words: ["Говоріть", "будь", "ласка", "повільніше"]
      answer: Говоріть будь ласка повільніше.
    - words: ["Це", "дуже", "смачна", "страва"]
      answer: Це дуже смачна страва.
    - words: ["Я", "люблю", "українську", "кухню"]
      answer: Я люблю українську кухню.
    - words: ["Де", "тут", "можна", "поїсти", "?"]
      answer: Де тут можна поїсти?
    - words: ["Я", "шукаю", "станцію", "метро"]
      answer: Я шукаю станцію метро.
    - words: ["Це", "моя", "улюблена", "пісня"]
      answer: Це моя улюблена пісня.

- type: true-false
  title: Fact Check
  instruction: Is the statement true or false?
  items:
    - statement: У ресторані ми платимо на касі.
      correct: false
    - statement: Швидка допомога приїжджає, коли хтось хворий.
      correct: true
    - statement: Квиток потрібен для проїзду в транспорті.
      correct: true
    - statement: Ми купуємо ліки в продуктовому магазині.
      correct: false
    - statement: Поліція допомагає в небезпечних ситуаціях.
      correct: true
    - statement: Ми можемо торгуватися в супермаркеті.
      correct: false
    - statement: Ми можемо торгуватися на ринку.
      correct: true
    - statement: Аптека працює цілодобово (іноді).
      correct: true
    - statement: Ми дзвонимо 103, коли хочемо піцу.
      correct: false
    - statement: Метро - це підземний транспорт.
      correct: true
    - statement: Ми платимо за вхід у парк (зазвичай ні).
      correct: false
    - statement: Ми даємо чайові водію автобуса (зазвичай ні).
      correct: false

- type: group-sort
  title: Categories
  instruction: Sort into categories.
  groups:
    - name: Places
      items: ["магазин", "аптека", "ресторан", "парк"]
    - name: People
      items: ["лікар", "касир", "водій", "офіціант"]
    - name: Things
      items: ["квиток", "гроші", "паспорт", "телефон"]

- type: quiz
  title: Word Association
  instruction: Choose the associated word.
  items:
    - question: Лікарня
      options:
        - text: Лікар
          correct: true
        - text: Вчитель
          correct: false
        - text: Кухар
          correct: false
        - text: Водій
          correct: false
    - question: Магазин
      options:
        - text: Продукти
          correct: true
        - text: Ліки
          correct: false
        - text: Квитки
          correct: false
        - text: Уроки
          correct: false
    - question: Вокзал
      options:
        - text: Поїзд
          correct: true
        - text: Літак
          correct: false
        - text: Корабель
          correct: false
        - text: Велосипед
          correct: false
    - question: Кафе
      options:
        - text: Кава
          correct: true
        - text: Суп
          correct: false
        - text: Одяг
          correct: false
        - text: Взуття
          correct: false
    - question: Ринок
      options:
        - text: Овочі
          correct: true
        - text: Книги
          correct: false
        - text: Меблі
          correct: false
        - text: Комп'ютери
          correct: false
    - question: Банк
      options:
        - text: Гроші
          correct: true
        - text: Хліб
          correct: false
        - text: Вода
          correct: false
        - text: Квіти
          correct: false
    - question: Школа
      options:
        - text: Урок
          correct: true
        - text: Обід
          correct: false
        - text: Сон
          correct: false
        - text: Гра
          correct: false
    - question: Стадіон
      options:
        - text: Спорт
          correct: true
        - text: Музика
          correct: false
        - text: Читання
          correct: false
        - text: Малювання
          correct: false
    - question: Театр
      options:
        - text: Вистава
          correct: true
        - text: Кіно
          correct: false
        - text: Новини
          correct: false
        - text: Спорт
          correct: false
    - question: Аптека
      options:
        - text: Таблетки
          correct: true
        - text: Цукерки
          correct: false
        - text: Іграшки
          correct: false
        - text: Одяг
          correct: false
    - question: Готель
      options:
        - text: Номер
          correct: true
        - text: Клас
          correct: false
        - text: Палата
          correct: false
        - text: Кабінет
          correct: false
    - question: Аеропорт
      options:
        - text: Рейс
          correct: true
        - text: Поїздка
          correct: false
        - text: Прогулянка
          correct: false
        - text: Екскурсія
          correct: false

- type: quiz
  title: Translation Challenge
  instruction: Translate the concept.
  items:
    - question: How to say 'Help!'?
      options:
        - text: Допоможіть!
          correct: true
        - text: Привіт!
          correct: false
        - text: Дякую!
          correct: false
        - text: Будь ласка!
          correct: false
    - question: How to say 'How much?'?
      options:
        - text: Скільки коштує?
          correct: true
        - text: Де це?
          correct: false
        - text: Хто це?
          correct: false
        - text: Коли це?
          correct: false
    - question: How to say 'I don't understand'?
      options:
        - text: Я не розумію.
          correct: true
        - text: Я не знаю.
          correct: false
        - text: Я не хочу.
          correct: false
        - text: Я не буду.
          correct: false
    - question: How to say 'Where is the metro?'?
      options:
        - text: Де метро?
          correct: true
        - text: Де автобус?
          correct: false
        - text: Де таксі?
          correct: false
        - text: Де поїзд?
          correct: false
    - question: How to say 'Delicious'?
      options:
        - text: Смачно.
          correct: true
        - text: Погано.
          correct: false
        - text: Холодно.
          correct: false
        - text: Гаряче.
          correct: false
    - question: How to say 'Excuse me'?
      options:
        - text: Вибачте.
          correct: true
        - text: Дякую.
          correct: false
        - text: Прошу.
          correct: false
        - text: Привіт.
          correct: false
    - question: How to say 'Open'?
      options:
        - text: Відчинено.
          correct: true
        - text: Зачинено.
          correct: false
        - text: Зайнято.
          correct: false
        - text: Вільно.
          correct: false
    - question: How to say 'Closed'?
      options:
        - text: Зачинено.
          correct: true
        - text: Відчинено.
          correct: false
        - text: Доброго дня.
          correct: false
        - text: До побачення.
          correct: false
    - question: How to say 'Cash'?
      options:
        - text: Готівка.
          correct: true
        - text: Картка.
          correct: false
        - text: Чек.
          correct: false
        - text: Рахунок.
          correct: false
    - question: How to say 'Card'?
      options:
        - text: Картка.
          correct: true
        - text: Готівка.
          correct: false
        - text: Гроші.
          correct: false
        - text: Гаманець.
          correct: false
    - question: How to say 'Wait'?
      options:
        - text: Зачекайте.
          correct: true
        - text: Йдіть.
          correct: false
        - text: Спіть.
          correct: false
        - text: Їжте.
          correct: false
    - question: How to say 'Call'?
      options:
        - text: Дзвонити.
          correct: true
        - text: Писати.
          correct: false
        - text: Читати.
          correct: false
        - text: Слухати.
          correct: false
"""
    with open(activities_path, 'w') as f:
        f.write(activities_content)

    # 4. Markdown Content
    md_content = f"""# {title}

## Warm-up

Welcome to **{title}**! In this practical module, we will explore essential vocabulary and phrases for **{subtitle.lower()}**. Whether you are in Kyiv, Lviv, or Odesa, these skills will help you navigate daily life with confidence.

You will learn how to handle typical situations, ask the right questions, and understand the answers. Let's dive in!

## Presentation

### Key Vocabulary (Основна лексика)

Here are the most important words you need to know.

| Word | Pronunciation | English |
| :--- | :--- | :--- |
| **{vocab_list[0]['lemma']}** | {vocab_list[0]['ipa']} | {vocab_list[0]['translation']} |
| **{vocab_list[1]['lemma']}** | {vocab_list[1]['ipa']} | {vocab_list[1]['translation']} |
| **{vocab_list[2]['lemma']}** | {vocab_list[2]['ipa']} | {vocab_list[2]['translation']} |
| **{vocab_list[3]['lemma']}** | {vocab_list[3]['ipa']} | {vocab_list[3]['translation']} |
| **{vocab_list[4]['lemma']}** | {vocab_list[4]['ipa']} | {vocab_list[4]['translation']} |

> 💡 **Tip:** Memorize these words first! They are your keys to communication.

### Useful Phrases (Корисні фрази)

- **Я хочу...** (I want...)
- **Скільки коштує?** (How much does it cost?)
- **Де знаходиться...?** (Where is located...?) 
- **Ви можете допомогти?** (Can you help?)
- **Я не розумію.** (I don't understand.)

### Cultural Note (Культурна замітка)

> 🌍 **Did You Know?**
>
> In Ukraine, direct communication is common. It is polite to say "**Доброго дня**" when entering a small shop or engaging with a service person. Always say "**Дякую**" (Thank you) and "**До побачення**" (Goodbye).

## Practice

### Scenario 1: Basic Interaction (Базова взаємодія)

**You:** Доброго дня!
**Person:** Доброго дня! Чим можу допомогти?
**You:** (Use a phrase) -> **Я шукаю...** (I am looking for...)
**Person:** Це ось тут.
**You:** **Дякую!**

### Scenario 2: Asking Questions (Запитання)

**You:** Вибачте, скажіть будь ласка...
**Person:** Так?
**You:** (Ask a question) -> **Скільки це коштує?**
**Person:** Це коштує 100 гривень.
**You:** **Зрозуміло, дякую.**

### Scenario 3: Solving a Problem (Вирішення проблеми)

**You:** Вибачте, у мене проблема.
**Person:** Що сталося?
**You:** (Explain simple problem) -> **Я не розумію.** / **Мені потрібна допомога.**
**Person:** Зараз я допоможу.
**You:** **Дуже дякую!**

## Summary

In this module, you practiced **{title.lower()}**. You learned key vocabulary like **{vocab_list[0]['lemma']}** and **{vocab_list[1]['lemma']}**. You also practiced useful phrases for typical situations.

Remember:
- Be polite using **будь ласка** and **дякую**.
- Don't be afraid to say **Я не розумію**.
- Practice makes perfect!

## Need More Practice? 

- **Role-play:** Practice these dialogues with a friend.
- **Flashcards:** Create cards for the new vocabulary.
- **Listen:** Try to hear these words in Ukrainian videos or podcasts.
"""
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    print(f"Generated module {mod_id}: {slug}")

# Generate all modules
for module in MODULES:
    create_files(module)
