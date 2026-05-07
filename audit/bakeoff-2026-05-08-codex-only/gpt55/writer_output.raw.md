<plan_reasoning section="Діалоги">
<word_budget>Target 300 words; planned section range 270-330; running total after section: about 300/1200.</word_budget>
<plan_vocab>прокидатися: “Я прокидаюся о сьомій.” вмиватися: “Вмиваюся, одягаюся і снідаю.” йти: “Я йду на роботу о восьмій.”</plan_vocab>
<register>A1 immersion target 15-35% Ukrainian: English scaffolds frame two short Ukrainian dialogues, with Ukrainian lines kept under 10 words.</register>
<teaching_sequence>Uses Knowledge Packet “Послідовність введення” for dialogue-before-rule staging and “Приклади з підручників” for authentic routine contexts.</teaching_sequence>
<verification_plan>Verify dialogue lemmas and forms through local VESUM helper; verify textbook grounding through local sources_db search_textbooks.</verification_plan>
<verification_trace>scripts/verification/vesum.py words(["прокидатися","прокидаюся","прокидаєшся","вмиватися","вмиваюся","одягатися","одягаюся","снідати","йти","йду","йдеш","потім","вранці","пізно"]); wiki.sources_db.search_textbooks({"прокидаєшся","займаєшся","одягаєшся"}, max_total=3)</verification_trace>
</plan_reasoning>

<plan_reasoning section="Дієслова на -ся">
<word_budget>Target 300 words; planned section range 270-330; running total after section: about 600/1200.</word_budget>
<plan_vocab>вмиватися: “Я вмиваюся.” одягатися: “Ти одягаєшся.” прокидатися: “Він прокидається.”</plan_vocab>
<register>A1 immersion target 15-35% Ukrainian: the rule is in compact English; paradigms and examples are Ukrainian.</register>
<teaching_sequence>Uses Knowledge Packet “Типові помилки L2” and textbook hits: Kravtsova Grade 4 p.113 for -шся/-ться pronunciation; Zakhariichuk Grade 4 p.162 for meaning and spelling/pronunciation contrast.</teaching_sequence>
<verification_plan>Verify forms in VESUM; search textbook corpus for pronunciation and meaning evidence; no fabricated Karaman quote because the packet marks it corpus_missing.</verification_plan>
<verification_trace>scripts/verification/vesum.py words(["вмиваєшся","вмивається","одягаєшся","одягається","прокидається"]); wiki.sources_db.search_textbooks({"Кравцова","шся","ться","вимова"}, max_total=5); wiki.sources_db.search_textbooks({"Написано","шся","вимовляй"}, max_total=3)</verification_trace>
</plan_reasoning>

<plan_reasoning section="Мій ранок">
<word_budget>Target 300 words; planned section range 270-330; running total after section: about 900/1200.</word_budget>
<plan_vocab>спочатку: “Спочатку я прокидаюся.” потім: “Потім я вмиваюся.” нарешті: “Нарешті я йду.”</plan_vocab>
<register>A1 immersion target 15-35% Ukrainian: English gives function labels; Ukrainian supplies short routine chains, tables, and pattern lines.</register>
<teaching_sequence>Uses Knowledge Packet “Словниковий мінімум” for high-frequency morning verbs and “Послідовність введення” for contrast between reflexive and non-reflexive verbs.</teaching_sequence>
<verification_plan>Verify sequence words, routine verbs, and йти forms through local VESUM; check style/definition/heritage for suspicious routine vocabulary.</verification_plan>
<verification_trace>scripts/verification/vesum.py words(["збиратися","повертатися","навчатися","поспішати","спочатку","потім","після","цього","нарешті","йти","йду","йдеш","йде"]); wiki.sources_db.search_style_guide("одягатися", limit=1); wiki.sources_db.search_definitions("сніданок", limit=1)</verification_trace>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<word_budget>Target 300 words; planned section range 270-330; final running total: about 1200/1200.</word_budget>
<plan_vocab>прокидатися, вмиватися, одягатися, снідати, йти: “Прокидаюся, вмиваюся, одягаюся, снідаю, йду.”</plan_vocab>
<register>A1 immersion target 15-35% Ukrainian: summary uses short English labels and Ukrainian self-check prompts.</register>
<teaching_sequence>Uses Knowledge Packet “Словниковий мінімум” and “Типові помилки L2”; final forward link points to a1-021 without adding new grammar.</teaching_sequence>
<verification_plan>Rescan all vocabulary and example forms against local VESUM; keep resource citations to retrieved or packet-declared sources only.</verification_plan>
<verification_trace>scripts/verification/vesum.py words(["ранок","рутина","кава","робота","субота","телефон","гуляти","лежати"]); wiki.sources_db.search_heritage("одягатися", limit=1); wiki.sources_db.search_heritage("рушник", limit=1)</verification_trace>
</plan_reasoning>

```markdown file=module.md
# Мій ранок

## Діалоги

**Ранок** is a small story: wake up, wash, get dressed, eat, go. The Ukrainian forms below make that story sound like a real routine, not a list from a dictionary.

**Ліна і Настя вдома**

> Ліна: Коли ти прокидаєшся?  
> Настя: Я прокидаюся о сьомій.  
> Ліна: Що ти робиш потім?  
> Настя: Вмиваюся, одягаюся і снідаю.  
> Ліна: Коли ти йдеш на роботу?  
> Настя: О восьмій. А ти?  
> Ліна: Я йду о восьмій тридцять.

The words ending in **-ся** are the routine actions that happen to the speaker’s own body or state: **прокидаюся**, **вмиваюся**, **одягаюся**. The non-reflexive verbs stay plain: **снідаю**, **йду**.

**У суботу**

> Настя: У суботу я не поспішаю.  
> Ліна: Ти прокидаєшся пізно?  
> Настя: Так, прокидаюся пізно.  
> Ліна: А потім?  
> Настя: Лежу і дивлюся в телефон.  
> Ліна: А я навчаюся вранці.  
> Настя: Потім гуляєш?  
> Ліна: Так, потім гуляю.

Two morning patterns are visible here:

| Робочий день | Вихідний день |
|---|---|
| прокидаюся о сьомій | прокидаюся пізно |
| вмиваюся | лежу |
| одягаюся | дивлюся в телефон |
| снідаю | гуляю |
| йду на роботу | не поспішаю |

**Коли ти прокидаєшся?** asks about the other person’s morning. **Я прокидаюся** answers with the speaker’s own morning. The ending before **-ся** changes with the person: **я прокидаюся**, **ти прокидаєшся**.

<!-- INJECT_ACTIVITY: act-1 -->

## Дієслова на -ся

A verb with **-ся** usually points the action back toward the person doing it. **Вмивати** can mean washing someone or something; **вмиватися** means washing yourself. **Одягати** can mean dressing someone; **одягатися** means getting yourself dressed.

<!-- VERIFY: source="Zakhariichuk Grade 4" page="162" topic="дієслова на -ся; дія, спрямована на себе" -->
> Дієслова на -ся виражають дію, спрямовану на самого виконавця.

Pattern:

| Звичайне дієслово | Дієслово на -ся |
|---|---|
| вмивати | вмиватися |
| одягати | одягатися |
| збирати | збиратися |
| повертати | повертатися |

The present tense ending comes before **-ся**.

| Особа | Форма |
|---|---|
| я | вмиваюся |
| ти | вмиваєшся |
| він / вона | вмивається |
| я | одягаюся |
| ти | одягаєшся |
| він / вона | одягається |

So the form is not **я вмиваєшся** and not **він вмиваюся**. The person ending still does its normal work.

Pronunciation has its own rule. The spelling stays **-шся** and **-ться**, but the final sound is smoother.

<!-- VERIFY: source="Kravtsova Grade 4" page="113" topic="вимова -шся, -ться" -->
> -шся вимовляють як [с':а]. -ться вимовляють як [ц':а].

| Пишемо | Вимовляємо |
|---|---|
| вмиваєшся | [вмиваєс':а] |
| одягаєшся | [одягаєс':а] |
| вмивається | [вмиваєц':а] |
| одягається | [одягаєц':а] |

The plan reference to Karaman Grade 10 p.176 gives the same semantic rule for **-ся(-сь)**; the local packet marks the corpus excerpt as missing, so no verbatim Karaman quotation is used here.

<!-- INJECT_ACTIVITY: act-3 -->

## Мій ранок

A simple morning story needs two kinds of words: actions and sequence words. The actions say what happens. The sequence words put the actions in time.

| Дія | English gloss |
|---|---|
| прокидатися | to wake up |
| вмиватися | to wash up |
| одягатися | to get dressed |
| збиратися | to get ready |
| снідати | to have breakfast |
| йти | to go |

**Йти** is irregular and frequent. Learn these three forms as a small block.

| Особа | Форма |
|---|---|
| я | йду |
| ти | йдеш |
| він / вона | йде |

Sequence words:

| Українською | English gloss |
|---|---|
| спочатку | first |
| потім | then |
| після цього | after that |
| нарешті | finally |

Pattern:

| Крок | Речення |
|---|---|
| 1 | Спочатку я прокидаюся. |
| 2 | Потім я вмиваюся. |
| 3 | Після цього я одягаюся. |
| 4 | Нарешті я снідаю. |
| 5 | Я йду на роботу. |

The story can be shorter:

- Спочатку я прокидаюся. — First I wake up.
- Потім вмиваюся. — Then I wash up.
- Після цього одягаюся. — After that I get dressed.
- Нарешті снідаю. — Finally I have breakfast.
- Я йду на роботу. — I go to work.

A Ukrainian subject can drop out when it is clear. **Я вмиваюся** and **Вмиваюся** both work in a routine chain. The shorter form sounds natural after the first sentence because the speaker is still **я**.

Morning contrast:

| Зворотне | Незворотне |
|---|---|
| я прокидаюся | я снідаю |
| ти вмиваєшся | ти п’єш каву |
| вона одягається | вона йде |
| я збираюся | я працюю |

<!-- INJECT_ACTIVITY: act-6 -->

## Підсумок

**-ся** attaches to the end of the personal verb form.

| Base | я | ти | він / вона |
|---|---|---|---|
| вмиватися | вмиваюся | вмиваєшся | вмивається |
| одягатися | одягаюся | одягаєшся | одягається |
| прокидатися | прокидаюся | прокидаєшся | прокидається |

The morning chain:

| Порядок | Дія |
|---|---|
| 1 | прокидатися |
| 2 | вмиватися |
| 3 | одягатися |
| 4 | снідати |
| 5 | йти |

The sentence chain:

- Спочатку я прокидаюся.
- Потім я вмиваюся.
- Після цього я одягаюся.
- Нарешті я снідаю.
- Я йду на роботу.

The compact version:

> Спочатку я прокидаюся. Потім вмиваюся і одягаюся. Після цього снідаю. Нарешті йду на роботу.

Common traps:

| ❌ | ✅ |
|---|---|
| я прокидаєшся | я прокидаюся |
| ти вмиваюся | ти вмиваєшся |
| він одягаєшся | він одягається |
| я йдеш | я йду |

Self-check:

1. Write four sentences about your morning.
2. Use **спочатку**, **потім**, **після цього**, **нарешті**.
3. Use two verbs with **-ся**.
4. Use one form of **йти**.

Model:

> Спочатку я прокидаюся. Потім вмиваюся. Після цього снідаю. Нарешті йду на роботу.

A1-021 will check the larger action block, so this module keeps the chain small and accurate: **прокидаюся → вмиваюся → одягаюся → снідаю → йду**.

<!-- INJECT_ACTIVITY: act-9 -->
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "instruction": "Complete the morning dialogue with the correct word.",
    "items": [
      {
        "sentence": "Я ____ о сьомій.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "йду", "снідаю"]
      },
      {
        "sentence": "Потім я ____.",
        "answer": "вмиваюся",
        "options": ["вмиваюся", "пізно", "робота"]
      },
      {
        "sentence": "О восьмій я ____ на роботу.",
        "answer": "йду",
        "options": ["йду", "одягаюся", "лежу"]
      }
    ]
  },
  {
    "id": "act-2",
    "type": "quiz",
    "instruction": "Choose the natural answer.",
    "items": [
      {
        "question": "Коли ти прокидаєшся?",
        "options": ["Я прокидаюся о сьомій.", "Я йдеш о сьомій.", "Я робота о сьомій."],
        "answer": "Я прокидаюся о сьомій."
      },
      {
        "question": "Що ти робиш потім?",
        "options": ["Вмиваюся і снідаю.", "Пізно робота.", "О сьомій субота."],
        "answer": "Вмиваюся і снідаю."
      }
    ]
  },
  {
    "id": "act-3",
    "type": "fill-in",
    "instruction": "Add -ся in the right place.",
    "items": [
      {
        "sentence": "Я вмиваю__.",
        "answer": "ся",
        "options": ["ся", "ти", "він"]
      },
      {
        "sentence": "Ти одягаєш__.",
        "answer": "ся",
        "options": ["ся", "ю", "є"]
      },
      {
        "sentence": "Він прокидаєть__.",
        "answer": "ся",
        "options": ["ся", "еш", "ю"]
      }
    ]
  },
  {
    "id": "act-4",
    "type": "quiz",
    "instruction": "Choose the correct form.",
    "items": [
      {
        "question": "Я ____ руки.",
        "options": ["вмиваю", "вмиваюся", "вмиваєшся"],
        "answer": "вмиваю"
      },
      {
        "question": "Я ____ вранці.",
        "options": ["вмиваюся", "вмиваєшся", "вмивається"],
        "answer": "вмиваюся"
      },
      {
        "question": "Ти ____ пізно.",
        "options": ["прокидаюся", "прокидаєшся", "прокидається"],
        "answer": "прокидаєшся"
      }
    ]
  },
  {
    "id": "act-5",
    "type": "true-false",
    "instruction": "Mark each sentence true or false.",
    "items": [
      {
        "statement": "Я вмиваюся means I wash myself.",
        "answer": true
      },
      {
        "statement": "Ти вмиваюся is the correct ти form.",
        "answer": false
      },
      {
        "statement": "Він вмивається is the correct він form.",
        "answer": true
      }
    ]
  },
  {
    "id": "act-6",
    "type": "order",
    "instruction": "Put the morning routine in order.",
    "items": ["Я йду на роботу.", "Я прокидаюся.", "Я снідаю.", "Я вмиваюся.", "Я одягаюся."],
    "correct_order": [1, 3, 4, 2, 0]
  },
  {
    "id": "act-7",
    "type": "match-up",
    "instruction": "Match the Ukrainian word to the English gloss.",
    "pairs": [
      {
        "left": "спочатку",
        "right": "first"
      },
      {
        "left": "потім",
        "right": "then"
      },
      {
        "left": "після цього",
        "right": "after that"
      },
      {
        "left": "нарешті",
        "right": "finally"
      }
    ]
  },
  {
    "id": "act-8",
    "type": "group-sort",
    "instruction": "Sort the verbs.",
    "groups": [
      {
        "name": "Зворотні",
        "items": ["прокидатися", "вмиватися", "одягатися", "збиратися"]
      },
      {
        "name": "Незворотні",
        "items": ["снідати", "йти", "пити", "працювати"]
      }
    ]
  },
  {
    "id": "act-9",
    "type": "fill-in",
    "instruction": "Complete the routine with sequence words.",
    "items": [
      {
        "sentence": "____ я прокидаюся.",
        "answer": "Спочатку",
        "options": ["Спочатку", "Після цього", "Нарешті"]
      },
      {
        "sentence": "____ я вмиваюся.",
        "answer": "Потім",
        "options": ["Потім", "Я", "Робота"]
      },
      {
        "sentence": "____ я йду на роботу.",
        "answer": "Нарешті",
        "options": ["Нарешті", "Потім", "Субота"]
      }
    ]
  },
  {
    "id": "act-10",
    "type": "error-correction",
    "instruction": "Correct the morning sentence.",
    "items": [
      {
        "sentence": "Я прокидаєшся о сьомій.",
        "error": "прокидаєшся",
        "correction": "прокидаюся"
      },
      {
        "sentence": "Ти вмиваюся вранці.",
        "error": "вмиваюся",
        "correction": "вмиваєшся"
      },
      {
        "sentence": "Він йду на роботу.",
        "error": "йду",
        "correction": "йде"
      }
    ]
  }
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "прокидатися",
    "translation": "to wake up",
    "pos": "verb",
    "usage": "Я прокидаюся о сьомій."
  },
  {
    "lemma": "вмиватися",
    "translation": "to wash up",
    "pos": "verb",
    "usage": "Потім я вмиваюся."
  },
  {
    "lemma": "одягатися",
    "translation": "to get dressed",
    "pos": "verb",
    "usage": "Я одягаюся вранці."
  },
  {
    "lemma": "снідати",
    "translation": "to have breakfast",
    "pos": "verb",
    "usage": "Я снідаю вдома."
  },
  {
    "lemma": "йти",
    "translation": "to go",
    "pos": "verb",
    "usage": "Я йду на роботу."
  },
  {
    "lemma": "спочатку",
    "translation": "first, at first",
    "pos": "adverb",
    "usage": "Спочатку я прокидаюся."
  },
  {
    "lemma": "потім",
    "translation": "then, next",
    "pos": "adverb",
    "usage": "Потім я вмиваюся."
  },
  {
    "lemma": "збиратися",
    "translation": "to get ready",
    "pos": "verb",
    "usage": "Я збираюся вранці."
  },
  {
    "lemma": "повертатися",
    "translation": "to return",
    "pos": "verb",
    "usage": "Я повертаюся додому."
  },
  {
    "lemma": "навчатися",
    "translation": "to study, to learn",
    "pos": "verb",
    "usage": "Я навчаюся вранці."
  },
  {
    "lemma": "поспішати",
    "translation": "to hurry",
    "pos": "verb",
    "usage": "Я не поспішаю."
  },
  {
    "lemma": "після цього",
    "translation": "after that",
    "pos": "phrase",
    "usage": "Після цього я одягаюся."
  },
  {
    "lemma": "нарешті",
    "translation": "finally",
    "pos": "adverb",
    "usage": "Нарешті я снідаю."
  },
  {
    "lemma": "вранці",
    "translation": "in the morning",
    "pos": "adverb",
    "usage": "Я працюю вранці."
  },
  {
    "lemma": "пізно",
    "translation": "late",
    "pos": "adverb",
    "usage": "У суботу я прокидаюся пізно."
  },
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  },
  {
    "lemma": "рутина",
    "translation": "routine",
    "pos": "noun",
    "usage": "Це моя рутина."
  },
  {
    "lemma": "кава",
    "translation": "coffee",
    "pos": "noun",
    "usage": "Я п’ю каву."
  },
  {
    "lemma": "робота",
    "translation": "work",
    "pos": "noun",
    "usage": "Я йду на роботу."
  },
  {
    "lemma": "субота",
    "translation": "Saturday",
    "pos": "noun",
    "usage": "У суботу я не поспішаю."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Караман Grade 10, p.176",
    "notes": "Plan reference for reflexive verbs with -ся(-сь) marking an action directed back toward the doer. Local knowledge packet marks the corpus excerpt as missing, so the module does not include a verbatim quotation."
  },
  {
    "title": "Кравцова Grade 4, p.113",
    "notes": "Textbook corpus hit 4-klas-ukrayinska-mova-kravtsova-2021-1_s0111 grounds pronunciation of -шся as [с':а] and -ться as [ц':а]."
  },
  {
    "title": "Захарійчук Grade 4, p.162",
    "notes": "Textbook corpus hit 4-klas-ukrmova-zaharijchuk_s0162 grounds the meaning of verbs on -ся and the contrast between spelling and pronunciation."
  },
  {
    "title": "Педагогіка A1: Мій ранок",
    "notes": "Wiki packet source for A1 sequencing, L2 learner traps, and high-frequency morning-routine vocabulary."
  }
]
```

<end_gate>
<rescanned_words>прокидатися, прокидаюся, прокидаєшся, прокидається, вмиватися, вмиваюся, вмиваєшся, вмивається, одягатися, одягаюся, одягаєшся, одягається, снідати, снідаю, снідаєш, йти, йду, йдеш, йде, спочатку, потім, збиратися, збираюся, повертатися, повертаюся, навчатися, навчаюся, поспішати, поспішаю, після, цього, нарешті, вранці, пізно, ранок, рутина, кава, робота, субота, телефон, гуляти, лежати</rescanned_words>
<rescanned_sources>Кравцова Grade 4 p.113 via search_textbooks({"Кравцова","шся","ться","вимова"}); Захарійчук Grade 4 p.162 via search_textbooks({"Написано","шся","вимовляй"}) and search_textbooks({"Поставте","дієслова","ся","особи"}); Караман Grade 10 p.176 retained only as plan reference because corpus excerpt is missing in packet and no matching verbatim excerpt was retrieved.</rescanned_sources>
<grammar_claims_grounded>-ся marks an action directed toward the doer: Захарійчук Grade 4 p.162 and packet plan reference Караман Grade 10 p.176; personal ending precedes -ся: Knowledge Packet “Послідовність введення” plus VESUM forms; -шся=[с':а] and -ться=[ц':а]: Кравцова Grade 4 p.113 and Захарійчук Grade 4 p.162; йти forms я йду, ти йдеш, він/вона йде: VESUM verification.</grammar_claims_grounded>
<removed_unverified>No Karaman verbatim quote was included because the supplied packet marks that textbook excerpt corpus_missing and local search did not retrieve the specified page. No fabricated textbook quotation was added.</removed_unverified>
</end_gate>