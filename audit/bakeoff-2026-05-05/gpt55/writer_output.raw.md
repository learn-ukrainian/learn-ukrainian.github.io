<plan_reasoning section="Діалоги">
word_budget: 300 target, 270-330 allowed; planned 295 words, running total 295/1200.
plan_vocab: прокидатися — "Я прокидаюся о сьомій."; вмиватися — "Вмиваюся, одягаюся і снідаю."; одягатися — "Вмиваюся, одягаюся і снідаю."; снідати — "Вмиваюся, одягаюся і снідаю."; йти — "Коли ти йдеш на роботу?"; потім — "Що ти робиш потім?"
register: A1 target 15-35% Ukrainian; English glosses support short Ukrainian dialogue lines.
teaching_sequence: uses the plan’s two dialogue situations and wiki pedagogy sequence: introduce reflexive verbs in real morning context before rule abstraction.
verification: functions.exec_command local VESUM forms table verified прокидатися, вмиватися, одягатися, снідати, йти, потім and dialogue forms прокидаюся, прокидаєшся, вмиваюся, одягаюся, йдеш. Source grounding uses plan references plus wiki/pedagogy/a1/my-morning.sources.yaml. No literary quotes used, so quote-contiguity is not applicable. Heritage defense: no archaism/historism/dialectism introduced.
</plan_reasoning>
<plan_reasoning section="Дієслова на -ся">
word_budget: 300 target, 270-330 allowed; planned 305 words, running total 600/1200.
plan_vocab: вмиватися — "Я вмиваюся."; одягатися — "Ти одягаєшся."; прокидатися — "Він прокидається."; спочатку — "Спочатку: вмивати → вмиватися."
register: A1 target 15-35% Ukrainian; rule is in English, paradigm and pattern boxes are Ukrainian.
teaching_sequence: uses Karaman Grade 10 p.176 for reflexive -ся as action directed to self and postfixed to personal forms; uses pronunciation rule from the plan and corroborating textbook rows in sources.db.
verification: functions.exec_command local SQLite sources.db FTS found 10-klas-ukrmova-karaman-2018_s0315: "Дієслова із суфіксом -ся(-сь)..." and Захарійчук page rows with "дію, спрямовану на себе" plus [с′:а]/[ц′:а] forms. VESUM verified examples вмиватися, одягатися, прокидатися and forms вмиваюся, вмиваєшся, одягаєшся. No literary quotes. No heritage-risk forms used.
</plan_reasoning>
<plan_reasoning section="Мій ранок">
word_budget: 300 target, 270-330 allowed; planned 300 words, running total 900/1200.
plan_vocab: прокидатися — "Спочатку я прокидаюся."; вмиватися — "Потім я вмиваюся."; одягатися — "Після цього я одягаюся."; снідати — "Потім я снідаю."; йти — "Нарешті я йду."; спочатку/потім — those exact sequence sentences ground them.
register: A1 target 15-35% Ukrainian; English labels explain sequencing, Ukrainian model lines stay short.
teaching_sequence: uses the wiki словниковий мінімум and sequence guidance: high-frequency routine words before full personal narration; irregular йти kept as memorized forms.
verification: functions.exec_command VESUM verified lemmas збиратися, повертатися, навчатися, поспішати, снідати, йти, спочатку, потім, після, цього, нарешті, вранці, пізно and forms йду, йдеш, йде. Source grounding: local sources.db/wiki packet, no extra dictionary claims. No attributed quotes. No suspicious heritage forms retained.
</plan_reasoning>
<plan_reasoning section="Підсумок">
word_budget: 300 target, 270-330 allowed; planned 300 words, running total 1200/1200.
plan_vocab: прокидатися — "Я прокидаюся."; вмиватися — "Я вмиваюся."; одягатися — "Я одягаюся."; снідати — "Я снідаю."; йти — "Я йду."; нарешті — "Нарешті я йду на роботу."
register: A1 target 15-35% Ukrainian; summary uses English scaffolds with Ukrainian checklists, patterns, and self-test lines.
teaching_sequence: recycles PPP: presentation in dialogues, practice in -ся forms, production in a four-sentence morning story. Includes one natural forward link to later reflexive work.
verification: functions.exec_command VESUM check covered all listed Ukrainian example lemmas and key forms. Source grounding limited to plan references and local textbook/wiki rows; no unsupported style-guide or dictionary citation is added. Quote-contiguity: no literary quotation. Heritage defense: no archaism/historism/dialectism versus Russianism decision needed.
</plan_reasoning>

```markdown file=module.md
## Діалоги

> Ліна: Коли ти прокидаєшся?
>
> Настя: Я прокидаюся о сьомій.
>
> Ліна: Що ти робиш потім?
>
> Настя: Вмиваюся, одягаюся і снідаю.
>
> Ліна: Коли ти йдеш на роботу?
>
> Настя: О восьмій.

A morning story in Ukrainian often begins with a time and then a chain of actions. The important forms here are **прокидаюся**, **вмиваюся**, **одягаюся**, and **йду**. Three of them end in **-ся**. They describe actions connected to the speaker’s own body or routine.

| Ukrainian | English gloss |
|---|---|
| Я прокидаюся о сьомій. | I wake up at seven. |
| Вмиваюся. | I wash up. |
| Одягаюся. | I get dressed. |
| Я йду на роботу. | I go to work. |

The second dialogue contrasts a workday morning with a weekend morning.

> Настя: У суботу я не поспішаю.
>
> Ліна: Що ти робиш?
>
> Настя: Прокидаюся пізно.
>
> Настя: Лежу і дивлюся телефон.
>
> Ліна: А я навчаюся вранці.
>
> Ліна: Потім гуляю.

Here **прокидаюся**, **дивлюся**, and **навчаюся** have **-ся**, but **лежу** and **гуляю** do not. Ukrainian does not add **-ся** to every morning verb. The ending belongs only to verbs whose dictionary form already has **-ся**: **прокидатися**, **вмиватися**, **одягатися**, **навчатися**.

| -ся verb | not -ся verb |
|---|---|
| прокидаюся | лежу |
| вмиваюся | снідаю |
| одягаюся | гуляю |
| навчаюся | йду |

<!-- INJECT_ACTIVITY: act-1 -->

## Дієслова на -ся

A **дієслово на -ся** is a verb with **-ся** or **-сь** at the end. Karaman Grade 10, p.176 explains this as a reflexive verb: the action turns back toward the subject. For A1, the working rule is simple: take the normal present-tense form and keep **-ся** at the end.

| base action | reflexive action |
|---|---|
| вмивати когось | вмиватися |
| одягати когось | одягатися |
| збирати когось | збиратися |

The personal ending changes before **-ся**.

| person | form |
|---|---|
| я | вмиваюся |
| ти | вмиваєшся |
| він | вмивається |
| вона | вмивається |

The pattern is the same with **одягатися**.

| person | form |
|---|---|
| я | одягаюся |
| ти | одягаєшся |
| він | одягається |
| вона | одягається |

The spelling and pronunciation are not identical. The written ending **-шся** is pronounced like a long soft **с**: **вмиваєшся → [вмиваєс':а]**. The written ending **-ться** is pronounced like a long soft **ц**: **вмивається → [вмиваєц':а]**. The spelling stays **-шся** and **-ться**.

| written | spoken guide |
|---|---|
| ти вмиваєшся | [вмиваєс':а] |
| ти одягаєшся | [одягаєс':а] |
| він вмивається | [вмиваєц':а] |
| вона одягається | [одягаєц':а] |

The English word "myself" can help once: **вмиваюся** means "I wash myself / I wash up." Ukrainian normally uses one verb, not a separate word for "myself."

<!-- INJECT_ACTIVITY: act-3 -->

## Мій ранок

**Мій ранок** needs a small set of high-frequency verbs. Some are reflexive; some are not. The contrast matters.

| routine step | verb |
|---|---|
| waking up | прокидатися |
| washing up | вмиватися |
| getting dressed | одягатися |
| getting ready | збиратися |
| breakfast | снідати |
| going | йти |

The verb **йти** is irregular and very common. Memorize the three A1 forms as a small block.

| person | form |
|---|---|
| я | йду |
| ти | йдеш |
| він / вона | йде |

Sequence words turn a list into a story.

| Ukrainian | English gloss |
|---|---|
| спочатку | first |
| потім | then |
| після цього | after this |
| нарешті | finally |

A basic morning story can stay short.

- **Спочатку я прокидаюся.** — First I wake up.
- **Потім я вмиваюся.** — Then I wash up.
- **Після цього я одягаюся.** — After this I get dressed.
- **Потім я снідаю.** — Then I have breakfast.
- **Нарешті я йду на роботу.** — Finally I go to work.

The same skeleton can change for a student.

- **Спочатку я прокидаюся.** — First I wake up.
- **Потім я навчаюся.** — Then I study.
- **Після цього я снідаю.** — After this I have breakfast.
- **Нарешті я гуляю.** — Finally I take a walk.

Keep the reflexive verbs reflexive: **я прокидаюся**, **я вмиваюся**, **я одягаюся**. Keep ordinary verbs ordinary: **я снідаю**, **я п’ю каву**, **я йду**. The goal is a plain chronological story, not a long paragraph.

<!-- INJECT_ACTIVITY: act-6 -->

## Підсумок

The core pattern:

| idea | Ukrainian |
|---|---|
| ordinary verb + -ся | зворотне дієслово |
| I wash up | я вмиваюся |
| you get dressed | ти одягаєшся |
| he wakes up | він прокидається |
| she wakes up | вона прокидається |

The form before **-ся** still agrees with the person.

| wrong | right |
|---|---|
| я прокидаєшся | я прокидаюся |
| ти прокидаюся | ти прокидаєшся |
| він вмиваюся | він вмивається |

Morning routine:

| order | sentence |
|---|---|
| 1 | Спочатку я прокидаюся. |
| 2 | Потім я вмиваюся. |
| 3 | Після цього я одягаюся. |
| 4 | Потім я снідаю. |
| 5 | Нарешті я йду. |

Self-check:

1. Use three **-ся** verbs: **прокидаюся**, **вмиваюся**, **одягаюся**.
2. Use one ordinary verb: **снідаю**, **п’ю**, or **йду**.
3. Use two sequence words: **спочатку**, **потім**, **після цього**, **нарешті**.
4. Keep each sentence short.

Model:

- **Спочатку я прокидаюся.**
- **Потім я вмиваюся.**
- **Після цього я одягаюся.**
- **Нарешті я йду на роботу.**

A later B1 lesson will return to **-ся** in longer Ukrainian prose, where the same ending helps express reflexive meaning, passive-like meaning, and natural style.

<!-- INJECT_ACTIVITY: act-10 -->
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "title": "Add -ся",
    "instruction": "Complete each form with the correct ending.",
    "items": [
      {
        "sentence": "Я вмиваю__.",
        "answer": "ся",
        "options": ["ся", "ти", "є"]
      },
      {
        "sentence": "Ти одягаєш__.",
        "answer": "ся",
        "options": ["ся", "ю", "є"]
      },
      {
        "sentence": "Він прокидаєть__.",
        "answer": "ся",
        "options": ["ся", "ти", "ю"]
      },
      {
        "sentence": "Вона збираєть__.",
        "answer": "ся",
        "options": ["ся", "єш", "ю"]
      },
      {
        "sentence": "Я прокидаю__ о сьомій.",
        "answer": "ся",
        "options": ["ся", "ти", "є"]
      },
      {
        "sentence": "Ти вмиваєш__ вранці.",
        "answer": "ся",
        "options": ["ся", "ю", "є"]
      },
      {
        "sentence": "Він одягаєть__ швидко.",
        "answer": "ся",
        "options": ["ся", "єш", "ти"]
      },
      {
        "sentence": "Я збираю__ на роботу.",
        "answer": "ся",
        "options": ["ся", "є", "ти"]
      },
      {
        "sentence": "Вона повертаєть__ додому.",
        "answer": "ся",
        "options": ["ся", "ю", "єш"]
      },
      {
        "sentence": "Ти навчаєш__ вранці.",
        "answer": "ся",
        "options": ["ся", "є", "ю"]
      }
    ]
  },
  {
    "id": "act-2",
    "type": "quiz",
    "title": "Reflexive or not",
    "instruction": "Choose the natural Ukrainian form.",
    "items": [
      {
        "question": "I wash up.",
        "options": [
          {
            "text": "Я вмиваюся.",
            "correct": true
          },
          {
            "text": "Я вмиваю.",
            "correct": false
          }
        ],
        "explanation": "Вмиватися is reflexive."
      },
      {
        "question": "I have breakfast.",
        "options": [
          {
            "text": "Я снідаюся.",
            "correct": false
          },
          {
            "text": "Я снідаю.",
            "correct": true
          }
        ],
        "explanation": "Снідати is not reflexive."
      },
      {
        "question": "You get dressed.",
        "options": [
          {
            "text": "Ти одягаєшся.",
            "correct": true
          },
          {
            "text": "Ти одягаєш.",
            "correct": false
          }
        ],
        "explanation": "Одягатися is reflexive."
      },
      {
        "question": "She wakes up.",
        "options": [
          {
            "text": "Вона прокидається.",
            "correct": true
          },
          {
            "text": "Вона прокидаєшся.",
            "correct": false
          }
        ],
        "explanation": "Вона takes -ється."
      },
      {
        "question": "I go.",
        "options": [
          {
            "text": "Я йдуся.",
            "correct": false
          },
          {
            "text": "Я йду.",
            "correct": true
          }
        ],
        "explanation": "Йти is not reflexive."
      },
      {
        "question": "I study.",
        "options": [
          {
            "text": "Я навчаюся.",
            "correct": true
          },
          {
            "text": "Я навчаєшся.",
            "correct": false
          }
        ],
        "explanation": "Я takes -юся."
      },
      {
        "question": "He gets ready.",
        "options": [
          {
            "text": "Він збирається.",
            "correct": true
          },
          {
            "text": "Він збираюся.",
            "correct": false
          }
        ],
        "explanation": "Він takes -ється."
      },
      {
        "question": "I drink coffee.",
        "options": [
          {
            "text": "Я п’ю каву.",
            "correct": true
          },
          {
            "text": "Я п’юся каву.",
            "correct": false
          }
        ],
        "explanation": "Пити is not reflexive here."
      }
    ]
  },
  {
    "id": "act-3",
    "type": "fill-in",
    "title": "Person endings",
    "instruction": "Choose the correct present-tense form.",
    "items": [
      {
        "sentence": "Я ____ о сьомій.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "прокидаєшся", "прокидається"]
      },
      {
        "sentence": "Ти ____ о восьмій.",
        "answer": "прокидаєшся",
        "options": ["прокидаюся", "прокидаєшся", "прокидається"]
      },
      {
        "sentence": "Вона ____ пізно.",
        "answer": "прокидається",
        "options": ["прокидаюся", "прокидаєшся", "прокидається"]
      },
      {
        "sentence": "Я ____ вранці.",
        "answer": "вмиваюся",
        "options": ["вмиваюся", "вмиваєшся", "вмивається"]
      },
      {
        "sentence": "Ти ____ швидко.",
        "answer": "одягаєшся",
        "options": ["одягаюся", "одягаєшся", "одягається"]
      },
      {
        "sentence": "Він ____ на роботу.",
        "answer": "збирається",
        "options": ["збираюся", "збираєшся", "збирається"]
      }
    ]
  },
  {
    "id": "act-4",
    "type": "match-up",
    "title": "Morning verbs",
    "instruction": "Match each Ukrainian verb with its English meaning.",
    "pairs": [
      {
        "left": "прокидатися",
        "right": "to wake up"
      },
      {
        "left": "вмиватися",
        "right": "to wash up"
      },
      {
        "left": "одягатися",
        "right": "to get dressed"
      },
      {
        "left": "снідати",
        "right": "to have breakfast"
      },
      {
        "left": "йти",
        "right": "to go"
      },
      {
        "left": "поспішати",
        "right": "to hurry"
      }
    ]
  },
  {
    "id": "act-5",
    "type": "true-false",
    "title": "Short checks",
    "instruction": "Decide whether each statement is true.",
    "items": [
      {
        "statement": "Я вмиваюся is a reflexive verb form.",
        "correct": true,
        "explanation": "The form ends in -ся."
      },
      {
        "statement": "Я снідаюся is the normal form for I have breakfast.",
        "correct": false,
        "explanation": "Use Я снідаю."
      },
      {
        "statement": "Ти одягаєшся uses the ти ending before -ся.",
        "correct": true,
        "explanation": "The ending is -єшся."
      },
      {
        "statement": "Він прокидаюся is correct.",
        "correct": false,
        "explanation": "Use Він прокидається."
      },
      {
        "statement": "Йти has the forms я йду, ти йдеш, він йде.",
        "correct": true,
        "explanation": "These forms are irregular and common."
      }
    ]
  },
  {
    "id": "act-6",
    "type": "order",
    "title": "Morning order",
    "instruction": "Put the morning routine in a natural order.",
    "items": [
      "Спочатку я прокидаюся.",
      "Потім я вмиваюся.",
      "Після цього я одягаюся.",
      "Потім я снідаю.",
      "Нарешті я йду на роботу."
    ],
    "correct_order": [0, 1, 2, 3, 4]
  },
  {
    "id": "act-7",
    "type": "group-sort",
    "title": "With -ся or without -ся",
    "instruction": "Sort the forms into two groups.",
    "groups": [
      {
        "name": "З -ся",
        "items": ["прокидаюся", "вмиваюся", "одягаюся", "навчаюся", "збираюся"]
      },
      {
        "name": "Без -ся",
        "items": ["снідаю", "йду", "п’ю", "лежу", "гуляю"]
      }
    ]
  },
  {
    "id": "act-8",
    "type": "unjumble",
    "title": "Build the sentence",
    "instruction": "Put the words in the correct order.",
    "items": [
      {
        "words": ["я", "спочатку", "прокидаюся"],
        "answer": "Спочатку я прокидаюся."
      },
      {
        "words": ["потім", "вмиваюся", "я"],
        "answer": "Потім я вмиваюся."
      },
      {
        "words": ["я", "після цього", "одягаюся"],
        "answer": "Після цього я одягаюся."
      },
      {
        "words": ["снідаю", "я", "потім"],
        "answer": "Потім я снідаю."
      },
      {
        "words": ["нарешті", "йду", "я"],
        "answer": "Нарешті я йду."
      }
    ]
  },
  {
    "id": "act-9",
    "type": "error-correction",
    "title": "Fix the morning forms",
    "instruction": "Choose the corrected sentence.",
    "items": [
      {
        "sentence": "Я прокидаєшся о сьомій.",
        "error": "прокидаєшся",
        "answer": "Я прокидаюся о сьомій.",
        "options": ["Я прокидаюся о сьомій.", "Я прокидається о сьомій.", "Я прокидаєшся о сьомій."],
        "explanation": "Я takes -юся."
      },
      {
        "sentence": "Він вмиваюся вранці.",
        "error": "вмиваюся",
        "answer": "Він вмивається вранці.",
        "options": ["Він вмивається вранці.", "Він вмиваєшся вранці.", "Він вмиваюся вранці."],
        "explanation": "Він takes -ється."
      },
      {
        "sentence": "Ти одягаюся швидко.",
        "error": "одягаюся",
        "answer": "Ти одягаєшся швидко.",
        "options": ["Ти одягаєшся швидко.", "Ти одягається швидко.", "Ти одягаюся швидко."],
        "explanation": "Ти takes -єшся."
      },
      {
        "sentence": "Я йдуся на роботу.",
        "error": "йдуся",
        "answer": "Я йду на роботу.",
        "options": ["Я йду на роботу.", "Я йдеш на роботу.", "Я йдеться на роботу."],
        "explanation": "Йти is not reflexive here."
      }
    ]
  },
  {
    "id": "act-10",
    "type": "fill-in",
    "title": "My morning",
    "instruction": "Complete the short morning story.",
    "items": [
      {
        "sentence": "Спочатку я ____.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "снідаю", "йду"]
      },
      {
        "sentence": "Потім я ____ і ____.",
        "answer": "вмиваюся, одягаюся",
        "options": ["вмиваюся, одягаюся", "йду, п’ю", "лежу, гуляю"]
      },
      {
        "sentence": "Нарешті я ____ на роботу.",
        "answer": "йду",
        "options": ["йду", "вмиваюся", "одягаюся"]
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
    "translation": "to wash up, to wash face or hands",
    "pos": "verb",
    "usage": "Я вмиваюся вранці."
  },
  {
    "lemma": "одягатися",
    "translation": "to get dressed",
    "pos": "verb",
    "usage": "Я одягаюся швидко."
  },
  {
    "lemma": "збиратися",
    "translation": "to get ready",
    "pos": "verb",
    "usage": "Я збираюся на роботу."
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
    "lemma": "снідати",
    "translation": "to have breakfast",
    "pos": "verb",
    "usage": "Потім я снідаю."
  },
  {
    "lemma": "йти",
    "translation": "to go",
    "pos": "verb",
    "usage": "Нарешті я йду на роботу."
  },
  {
    "lemma": "пити",
    "translation": "to drink",
    "pos": "verb",
    "usage": "Я п’ю каву."
  },
  {
    "lemma": "кава",
    "translation": "coffee",
    "pos": "noun",
    "usage": "Я п’ю каву."
  },
  {
    "lemma": "робота",
    "translation": "work, job",
    "pos": "noun",
    "usage": "Я йду на роботу."
  },
  {
    "lemma": "субота",
    "translation": "Saturday",
    "pos": "noun",
    "usage": "У суботу я не поспішаю."
  },
  {
    "lemma": "телефон",
    "translation": "phone",
    "pos": "noun",
    "usage": "Я дивлюся телефон."
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
    "usage": "Це моя ранкова рутина."
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
    "lemma": "після цього",
    "translation": "after this",
    "pos": "phrase",
    "usage": "Після цього я одягаюся."
  },
  {
    "lemma": "нарешті",
    "translation": "finally",
    "pos": "adverb",
    "usage": "Нарешті я йду."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Караман Grade 10, p.176",
    "notes": "Зворотні дієслова: суфікс -ся(-сь) означає зворотну дію; -ся(-сь) додається після інфінітивного суфікса або особового закінчення."
  },
  {
    "title": "Кравцова Grade 4, p.113",
    "notes": "Планова опора для правила вимови: -шся звучить як [с':а], -ться звучить як [ц':а]."
  },
  {
    "title": "Захарійчук Grade 4, p.162",
    "notes": "Дієслова на -ся: вправи з вимовою, правописом і дією, спрямованою на себе."
  },
  {
    "title": "wiki/pedagogy/a1/my-morning.md",
    "notes": "Compiled pedagogical packet for A1 morning routine: sequencing, L2 error prevention, high-frequency vocabulary, and decolonized vocabulary cautions."
  }
]
```

<end_gate>
actions: [rescanned_words, rescanned_sources]
removed_count: 0
summary: Rescanned planned lemmas and key example forms against the local VESUM forms table; rescanned source grounding against the supplied plan references, wiki source registry, and local sources.db textbook rows. No unverified literary quotes or heritage-risk forms were included.
</end_gate>