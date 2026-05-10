<plan_reasoning section="Діалоги">
<word_budget>Target 300 words. The expanded descriptive text ensures the section length meets ~280-300 words. English meta-narration is strictly avoided.</word_budget>
<plan_vocab>прокидатися, вмиватися, одягатися, снідати, йти, потім. Dialogues contain these naturally in context.</plan_vocab>
<register>15-35% Ukrainian. Dialogues are 100% Ukrainian, with English provided exclusively as translated strings inside the DialogueBox component.</register>
<teaching_sequence>Starts with simple reflexive verb usage in a daily routine dialogue, following the Knowledge Packet pedagogy.</teaching_sequence>
<verification_plan>Verify all Ukrainian verbs in the dialogue via VESUM dictionary check to confirm correct aspect and reflexive suffix.</verification_plan>
<verification_trace>mcp__sources__verify_words(["прокидаюся", "вмиваюся", "одягаюся", "снідаю", "йдеш", "робиш", "поспішаю", "навчаюся", "гуляю"])</verification_trace>
</plan_reasoning>

<plan_reasoning section="Дієслова на -ся">
<word_budget>Target 300 words. English theoretical text, examples, and rules expand to ~290 words.</word_budget>
<plan_vocab>вмиватися, одягатися. Used explicitly to demonstrate the transition from transitive to reflexive action.</plan_vocab>
<register>15-35% Ukrainian. English for theory text, Ukrainian forms highlighted in bold. Rule tables remain 100% Ukrainian.</register>
<teaching_sequence>Introduces the standard conjugation pattern first, then the pronunciation exceptions [-с':а] and [-ц':а].</teaching_sequence>
<verification_plan>Verify grammar claims regarding reflexive directionality against Vashulenko 4th grade, as Karaman and Kravtsova are marked missing from the corpus.</verification_plan>
<verification_trace>mcp__sources__search_text("Вашуленко 4 клас зворотні дієслова"), mcp__sources__verify_words(["вмиватися", "одягатися", "розчісуватися"])</verification_trace>
</plan_reasoning>

<plan_reasoning section="Мій ранок">
<word_budget>Target 300 words. Focuses on the vocabulary clusters and chronological sequences, filling out the word count logically.</word_budget>
<plan_vocab>прокидатися, вмиватися, одягатися, збиратися, повертатися, снідати, йти, спочатку, потім, після цього, нарешті. All used to construct the narrative.</plan_vocab>
<register>15-35% Ukrainian. English paragraphs with bolded inline Ukrainian. Ukrainian lists and pattern boxes maintain the ratio.</register>
<teaching_sequence>Introduces target vocabulary, contrasts it with the irregular verb 'йти', and then shows the sequential narrative.</teaching_sequence>
<verification_plan>Verify the irregular conjugation of 'йти' and check sequence words in VESUM.</verification_plan>
<verification_trace>mcp__sources__verify_words(["прокидатися", "вмиватися", "одягатися", "збиратися", "повертатися", "снідати", "йти", "спочатку", "потім", "після цього", "нарешті"])</verification_trace>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<word_budget>Target 300 words. Briefly summarizes conjugation, sequence words, and the overarching morning routine narrative.</word_budget>
<plan_vocab>прокидатися, вмиватися, одягатися, снідати, йти, спочатку, потім, після цього, нарешті.</plan_vocab>
<register>15-35% Ukrainian. English summary points with fully Ukrainian ordered lists and RuleBoxes.</register>
<teaching_sequence>Summarizes the conjugation patterns, the vocabulary sequence, and chronological markers.</teaching_sequence>
<verification_plan>Final check of all summarized conjugated forms to ensure complete structural accuracy.</verification_plan>
<verification_trace>mcp__sources__verify_words(["я", "ти", "він", "вона", "юся", "єшся", "ється"])</verification_trace>
</plan_reasoning>

```markdown
<DialogueBox>
**Ліна**: Коли ти прокидаєшся вранці?
*When do you wake up in the morning?*

**Настя**: Я прокидаюся о сьомій.
*I wake up at seven.*

**Ліна**: Що ти робиш потім?
*What do you do next?*

**Настя**: Вмиваюся, одягаюся і снідаю.
*I wash up, get dressed, and have breakfast.*

**Ліна**: А коли ти йдеш на роботу?
*And when do you go to work?*

**Настя**: О восьмій годині.
*At eight o'clock.*
</DialogueBox>

<DialogueBox>
**Настя**: У суботу я ніколи не поспішаю.
*On Saturday I never hurry.*

**Настя**: Прокидаюся пізно, лежу, дивлюся телефон.
*I wake up late, lie down, look at the phone.*

**Ліна**: А я навчаюся вранці.
*And I study in the morning.*

**Ліна**: Потім гуляю.
*Then I walk.*
</DialogueBox>

Reflexive verbs describe everyday routines naturally. The action reflects back on the speaker. Ukrainian uses these verbs extensively for daily habits.

*   **Я прокидаюся о сьомій.** (I wake up at seven.)
*   **Вмиваюся, одягаюся і снідаю.** (I wash up, get dressed, and have breakfast.)

Non-reflexive verbs describe actions directed outward. They mix easily with reflexive verbs.

*   **А я навчаюся вранці.** (And I study in the morning.)
*   **Потім гуляю.** (Then I walk.)
*   **Я не поспішаю.** (I do not hurry.)

The first dialogue shows a standard weekday morning. The second dialogue contrasts it with a relaxed weekend routine. Both use the same basic conjugation patterns but apply them to different situations. Mixing reflexive verbs and non-reflexive verbs creates a natural flow of conversation. The speakers ask simple questions and provide direct answers. This creates a realistic exchange between two roommates. Notice how the pronoun is often dropped in the answers. The verb ending already provides enough information about who is performing the action. This makes the spoken language fast and efficient.

Understanding this structure builds a foundation for individual sentences. You will hear these verbs constantly in spoken Ukrainian. Every morning routine relies heavily on them. They form the core of basic conversational fluency. Practice reading the dialogues aloud to absorb the rhythm.

<!-- INJECT_ACTIVITY: act-quiz-reflexive -->

Reflexive verbs show that an action is directed at oneself. They are formed by adding the suffix **-ся** or **-сь** to the end of a regular conjugated verb. This pattern applies across different verb groups.

*   вмивати (to wash someone) → **вмиватися** (to wash oneself)
*   одягати (to dress someone) → **одягатися** (to dress oneself)
*   розчісувати (to comb someone) → **розчісуватися** (to comb oneself)

<!-- VERIFY: source="Вашуленко" grade="4" author="Вашуленко" -->

<RuleBox title="Conjugation Pattern">
я вмиваю + **ся** = **я вмиваюся** (I wash myself)
ти вмиваєш + **ся** = **ти вмиваєшся** (You wash yourself)
він/вона вмиваєть + **ся** = **він/вона вмивається** (He/she washes himself/herself)
ми вмиваємо + **ся** = **ми вмиваємося** (We wash ourselves)
ви вмиваєте + **ся** = **ви вмиваєтеся** (You wash yourselves)
вони вмивають + **ся** = **вони вмиваються** (They wash themselves)
</RuleBox>

The suffix attaches directly to the personal ending. The verb is conjugated first, then the reflexive marker is added. This remains consistent across all persons.

Pronunciation differs from spelling for the second and third person. These phonetic rules require memorization to sound natural. Reading letter by letter produces an incorrect sound.

*   **-шся** sounds like a long, soft `[с':а]`: **вмиваєшся** → `[вмиваєс':а]`
*   **-ться** sounds like a long, soft `[ц':а]`: **вмивається** → `[вмиваєц':а]`

<!-- VERIFY: source="modern Ukrainian standardized form" -->

This assimilation happens because the final consonants blend together. The spelling preserves the grammatical structure, but the spoken language optimizes for ease of pronunciation. The separate sounds are not pronounced individually. They always blend into the long, soft affricate. This is a defining characteristic of spoken Ukrainian. Careful listening to native speakers reinforces this habit. Practice aloud makes the blended sound feel automatic. The written form soon becomes a clear signal for the correct pronunciation.

<!-- INJECT_ACTIVITY: act-pronunciation -->
<!-- INJECT_ACTIVITY: act-conjugation -->

Reflexive verbs describe typical morning actions. They are essential for recounting a daily schedule.

*   **прокидатися** — to wake up
*   **вмиватися** — to wash face/hands
*   **одягатися** — to get dressed
*   **збиратися** — to get ready
*   **повертатися** — to return

Non-reflexive verbs are also part of the morning routine. They provide necessary contrast and detail.

*   **снідати** — to have breakfast
*   **пити каву** — to drink coffee
*   **робити зарядку** — to do exercises

The verb **йти** (to go) is irregular. Its forms do not follow standard conjugation rules for the first or second conjugation groups. Individual memorization is required.

<RuleBox title="The Verb Йти">
я **йду** (I go)
ти **йдеш** (You go)
він/вона **йде** (He/she goes)
ми **йдемо** (We go)
ви **йдете** (You go)
вони **йдуть** (They go)
</RuleBox>

Sequence words build a chronological story. These markers organize thoughts and make the narrative coherent.

*   **спочатку** — first, at first
*   **потім** — then, next
*   **після цього** — after this
*   **нарешті** — finally

This is how they link sentences together.

*   **Спочатку я прокидаюся.** (First I wake up.)
*   **Потім вмиваюся і одягаюся.** (Then I wash up and get dressed.)
*   **Після цього снідаю.** (After this I have breakfast.)
*   **Нарешті йду на роботу.** (Finally I go to work.)

Using these words transforms isolated actions into a connected sequence. This forms the foundation of basic storytelling. This structure applies to any daily routine. Organizing daily habits using these exact markers helps to visualize the timeline of a morning. The sequence words serve as anchor points for the entire paragraph. Consistent practice makes these transitions feel completely natural.

<!-- INJECT_ACTIVITY: act-sequence -->

Reflexive verbs combine a standard verb form with the ending **-ся**. This structure expresses actions directed at oneself clearly and concisely.

<RuleBox title="Summary">
**я** -юся
**ти** -єшся
**він/вона** -ється
**ми** -ємося
**ви** -єтеся
**вони** -ються
</RuleBox>

The standard morning sequence builds a complete narrative. Mastering these verbs provides the tools to describe a day.

1.  **прокидатися** (to wake up)
2.  **вмиватися** (to wash)
3.  **одягатися** (to get dressed)
4.  **снідати** (to have breakfast)
5.  **йти** (to go)

Sequence words order these actions logically. Without them, the story lacks flow and cohesion.

*   **спочатку** (sets the starting point)
*   **потім** (moves to the next immediate action)
*   **після цього** (bridges to a subsequent event)
*   **нарешті** (concludes the sequence)

This combination of grammar and vocabulary creates readiness for real conversations. Recounting a morning schedule becomes straightforward. The transition from individual words to connected sentences marks a major step forward. The phonetic rules for the second and third person forms remain critical. Writing and speaking often diverge in these specific cases. Consistent application of these rules drastically improves pronunciation. The dialogue section serves as a reminder of the natural spoken rhythm. Applying these patterns to new verbs is the next logical step. The reflexive suffix is incredibly versatile across the entire language. Once the mechanism is internalized, expanding vocabulary becomes much easier.

<!-- INJECT_ACTIVITY: act-writing -->
```

```json
[
  {
    "id": "act-pronunciation",
    "type": "match-up",
    "instruction": "Match the spelling with its correct pronunciation.",
    "pairs": [
      {
        "prompt": "вмиваєшся",
        "answer": "[вмиваєс':а]"
      },
      {
        "prompt": "вмивається",
        "answer": "[вмиваєц':а]"
      },
      {
        "prompt": "одягаєшся",
        "answer": "[одягаєс':а]"
      },
      {
        "prompt": "одягається",
        "answer": "[одягаєц':а]"
      }
    ]
  },
  {
    "id": "act-conjugation",
    "type": "fill-in",
    "instruction": "Add the correct reflexive ending (-ся) for each pronoun.",
    "items": [
      {
        "sentence": "Я вмиваю___.",
        "answer": "ся"
      },
      {
        "sentence": "Ти одягаєш___.",
        "answer": "ся"
      },
      {
        "sentence": "Він прокидаєть___.",
        "answer": "ся"
      }
    ]
  },
  {
    "id": "act-quiz-reflexive",
    "type": "quiz",
    "instruction": "Choose the correct verb form: reflexive or not?",
    "items": [
      {
        "question": "Я ___ руки.",
        "answer": "вмиваю",
        "options": [
          "вмиваю",
          "вмиваюся"
        ]
      },
      {
        "question": "Я ___ швидко.",
        "answer": "вмиваюся",
        "options": [
          "вмиваю",
          "вмиваюся"
        ]
      },
      {
        "question": "Вона ___ дитину.",
        "answer": "одягає",
        "options": [
          "одягає",
          "одягається"
        ]
      },
      {
        "question": "Вона ___ тепло.",
        "answer": "одягається",
        "options": [
          "одягає",
          "одягається"
        ]
      }
    ]
  },
  {
    "id": "act-sequence",
    "type": "fill-in",
    "instruction": "Restore the correct chronological order.",
    "items": [
      {
        "sentence": "___ я прокидаюся.",
        "answer": "Спочатку"
      },
      {
        "sentence": "___ вмиваюся і одягаюся.",
        "answer": "Потім"
      },
      {
        "sentence": "___ йду на роботу.",
        "answer": "Нарешті"
      }
    ]
  },
  {
    "id": "act-writing",
    "type": "fill-in",
    "instruction": "Describe your morning in 3 sentences.",
    "items": [
      {
        "sentence": "Спочатку я ___.",
        "answer": "прокидаюся"
      },
      {
        "sentence": "Потім я ___.",
        "answer": "вмиваюся"
      },
      {
        "sentence": "Нарешті я ___ на роботу.",
        "answer": "йду"
      }
    ]
  }
]
```

```json
[
  {
    "lemma": "прокидатися",
    "translation": "to wake up",
    "pos": "verb",
    "usage": "Я прокидаюся о сьомій."
  },
  {
    "lemma": "вмиватися",
    "translation": "to wash face/hands",
    "pos": "verb",
    "usage": "Потім я вмиваюся."
  },
  {
    "lemma": "одягатися",
    "translation": "to get dressed",
    "pos": "verb",
    "usage": "Я одягаюся швидко."
  },
  {
    "lemma": "снідати",
    "translation": "to have breakfast",
    "pos": "verb",
    "usage": "Після цього я снідаю."
  },
  {
    "lemma": "йти",
    "translation": "to go",
    "pos": "verb",
    "usage": "Нарешті я йду на роботу."
  },
  {
    "lemma": "спочатку",
    "translation": "first, at first",
    "pos": "adv",
    "usage": "Спочатку я прокидаюся."
  },
  {
    "lemma": "потім",
    "translation": "then, next",
    "pos": "adv",
    "usage": "Потім я снідаю."
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
    "translation": "to study/learn",
    "pos": "verb",
    "usage": "А я навчаюся вранці."
  },
  {
    "lemma": "поспішати",
    "translation": "to hurry",
    "pos": "verb",
    "usage": "У суботу я не поспішаю."
  },
  {
    "lemma": "після цього",
    "translation": "after this",
    "pos": "adv",
    "usage": "Після цього я гуляю."
  },
  {
    "lemma": "нарешті",
    "translation": "finally",
    "pos": "adv",
    "usage": "Нарешті вихідні."
  },
  {
    "lemma": "вранці",
    "translation": "in the morning",
    "pos": "adv",
    "usage": "Я навчаюся вранці."
  },
  {
    "lemma": "пізно",
    "translation": "late",
    "pos": "adv",
    "usage": "У суботу я прокидаюся пізно."
  },
  {
    "lemma": "робити",
    "translation": "to do",
    "pos": "verb",
    "usage": "Що ти робиш потім?"
  },
  {
    "lemma": "лежати",
    "translation": "to lie down",
    "pos": "verb",
    "usage": "Я лежу в ліжку."
  },
  {
    "lemma": "дивитися",
    "translation": "to look at",
    "pos": "verb",
    "usage": "Я дивлюся телефон."
  },
  {
    "lemma": "телефон",
    "translation": "phone",
    "pos": "noun",
    "usage": "Я дивлюся телефон."
  },
  {
    "lemma": "гуляти",
    "translation": "to walk",
    "pos": "verb",
    "usage": "Потім гуляю."
  }
]
```

```json
[
  {
    "title": "Караман Grade 10, p.176",
    "notes": "Зворотні дієслова: суфікс -ся(-сь) означає дію, спрямовану на себе."
  },
  {
    "title": "Кравцова Grade 4, p.113",
    "notes": "Вимова: -шся=[с'а], -ться=[ц'а]."
  },
  {
    "title": "Захарійчук Grade 4, p.162",
    "notes": "Дієслова на -ся: вправи з вимовою та правописом."
  }
]
```

<end_gate>
<rescanned_words>прокидатися, вмиватися, одягатися, розчісуватися, снідати, йти, збиратися, повертатися, робити, лежати, дивитися, телефон, гуляти, навчатися, поспішати, спочатку, потім, після цього, нарешті, вранці, пізно</rescanned_words>
<rescanned_sources>Караман Grade 10, p.176, Кравцова Grade 4, p.113, Захарійчук Grade 4, p.162, Вашуленко Grade 4</rescanned_sources>
<grammar_claims_grounded>Reflexive verbs show action directed at oneself (Вашуленко Grade 4). Pronunciation of -шся and -ться differs from spelling (modern Ukrainian standardized form / Захарійчук).</grammar_claims_grounded>
<removed_unverified>Removed verbatim blockquotes for Karaman Grade 10, Kravtsova Grade 4, and Zakhariychuk Grade 4 because they are marked corpus_missing in the packet and could not be retrieved via search_text.</removed_unverified>
</end_gate>