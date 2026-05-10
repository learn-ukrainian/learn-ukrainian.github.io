<plan_reasoning section="Діалоги">
<word_budget>Allocate about 300 words; running total target 300/1200 within 1200±5%.</word_budget>
<plan_vocab>прокидатися: «Я прокидаюся о сьомій.» вмиватися: «Вмиваюся.» одягатися: «Одягаюся.» снідати: «Снідаю.» йти: «Я йду о восьмій.» потім: «Що ти робиш потім?»</plan_vocab>
<register>A1.3 target 15-35% Ukrainian; English scaffolds are short, Ukrainian stays in dialogue lines and bullets.</register>
<teaching_sequence>Uses roommate dialogue situation and Knowledge Packet model: introduce reflexive forms naturally before rule explanation.</teaching_sequence>
<verification_plan>Local VESUM checks were run for core lemmas/forms. Textbook MCP tools are unavailable here; no retrieved textbook quote is claimed.</verification_plan>
<verification_trace>functions.exec_command(".venv/bin/python ... SELECT count(*) FROM forms ... data/vesum.db"). No mcp__sources__search_text signature emitted because that tool is unavailable in this runtime.</verification_trace>
</plan_reasoning>
<plan_reasoning section="Дієслова на -ся">
<word_budget>Allocate about 300 words; running total target 600/1200 within 1200±5%.</word_budget>
<plan_vocab>вмиватися: «Я вмиваюся.» одягатися: «Ти одягаєшся.» прокидатися: «Вона прокидається.» себе appears only as English scaffolded meaning, not vocabulary.</plan_vocab>
<register>A1.3 target 15-35% Ukrainian; grammar explanation in English, forms in tables and pattern boxes.</register>
<teaching_sequence>Uses Knowledge Packet facts on action directed to self, postfix placement, and -шся/-ться pronunciation. Plan references are marked corpus_missing.</teaching_sequence>
<verification_plan>VESUM checked target forms. Grammar claims are tied to supplied packet/plan comments, with corpus_missing comments instead of fabricated textbook excerpts.</verification_plan>
<verification_trace>functions.exec_command(".venv/bin/python ... SELECT lemma,tags,pos FROM forms ..."). No mcp__sources__search_text call available; textbook grounding remains unresolved.</verification_trace>
</plan_reasoning>
<plan_reasoning section="Мій ранок">
<word_budget>Allocate about 300 words; running total target 900/1200 within 1200±5%.</word_budget>
<plan_vocab>спочатку: «Спочатку я прокидаюся.» потім: «Потім вмиваюся.» після цього: «Після цього снідаю.» нарешті: «Нарешті йду.» йти: «Я йду.»</plan_vocab>
<register>A1.3 target 15-35% Ukrainian; sequence story uses short Ukrainian lines with English glosses.</register>
<teaching_sequence>Uses Knowledge Packet sequence model and minimal high-frequency morning vocabulary, avoiding overload.</teaching_sequence>
<verification_plan>Local VESUM checked routine verbs, adverbs, and йти forms. No heritage-risk claims used.</verification_plan>
<verification_trace>functions.exec_command(".venv/bin/python ... words='прокидатися ... йду' ... data/vesum.db"). No unavailable MCP calls cited.</verification_trace>
</plan_reasoning>
<plan_reasoning section="Підсумок">
<word_budget>Allocate about 300 words; running total target 1200/1200 within 1200±5%.</word_budget>
<plan_vocab>прокидатися, вмиватися, одягатися, снідати, йти appear in the chain «прокидатися → вмиватися → одягатися → снідати → йти».</plan_vocab>
<register>A1.3 target 15-35% Ukrainian; summary uses compact English checks plus Ukrainian forms.</register>
<teaching_sequence>Uses PPP wrap-up: rule, morning chain, sequence words, self-check prompt.</teaching_sequence>
<verification_plan>Rescan target vocabulary and source claims; unresolved corpus_missing textbook references stay in resources/comments.</verification_plan>
<verification_trace>functions.exec_command(".venv/bin/python ... missing [...]"). No mcp__sources__verify_words/search_text tools available; no fake tool results emitted.</verification_trace>
</plan_reasoning>

```markdown file=module.md
## Діалоги

**-ся** marks many Ukrainian morning actions. The action turns back toward the person doing it: waking up, washing up, getting dressed, getting ready. English often uses “myself” or a plain verb; Ukrainian puts **-ся** at the end.

Ліна and Настя share a room and compare mornings.

**Робочий ранок**

> **Настя:** Ліно, коли ти прокидаєшся?  
> **Ліна:** Я прокидаюся о сьомій.  
> **Настя:** Що ти робиш потім?  
> **Ліна:** Вмиваюся, одягаюся і снідаю.  
> **Настя:** А коли ти йдеш на роботу?  
> **Ліна:** О восьмій.

Short answers sound natural here. A Ukrainian speaker does not need a full paragraph to describe a routine. One verb can carry one step.

- **Я прокидаюся.** — I wake up.
- **Вмиваюся.** — I wash up.
- **Одягаюся.** — I get dressed.
- **Снідаю.** — I have breakfast.
- **Я йду.** — I go.

**Ранок вихідного дня**

> **Ліна:** У суботу я не поспішаю.  
> **Ліна:** Прокидаюся пізно.  
> **Ліна:** Лежу, дивлюся телефон.  
> **Настя:** А я навчаюся вранці.  
> **Настя:** Потім гуляю.

The weekend dialogue mixes two kinds of verbs. **Прокидаюся** and **навчаюся** end in **-ся**. **Лежу**, **дивлюся**, **гуляю**, **снідаю**, and **йду** do not all follow one English pattern. Learn the Ukrainian verb as a Ukrainian verb.

<!-- INJECT_ACTIVITY: act-1 -->

## Дієслова на -ся

A reflexive verb is an ordinary verb form plus **-ся** at the end. The basic meaning is “the action is directed back to the subject.”  
<!-- VERIFY: source="Knowledge Packet pedagogy/a1/my-morning.md S9; plan reference Караман Grade 10, p.176 is corpus_missing=true" -->

Pattern:

| Звичайне дієслово | Зворотне дієслово |
|---|---|
| вмивати | вмиватися |
| одягати | одягатися |
| збирати | збиратися |
| повертати | повертатися |

The personal ending changes first. Then **-ся** stays at the end.

| Особа | Форма |
|---|---|
| я | вмиваюся |
| ти | вмиваєшся |
| він | вмивається |
| вона | вмивається |

Pattern box:

**вмивати → я вмиваю → я вмиваюся**  
**одягати → ти одягаєш → ти одягаєшся**  
**прокидатися → вона прокидається**

Spelling and pronunciation are not identical.  
<!-- VERIFY: source="Knowledge Packet pedagogy/a1/my-morning.md S1/S9; plan reference Кравцова Grade 4, p.113 is corpus_missing=true" -->

| Написання | Вимова |
|---|---|
| ти вмиваєшся | [вмиваєс':а] |
| він вмивається | [вмиваєц':а] |
| ти одягаєшся | [одягаєс':а] |
| вона одягається | [одягаєц':а] |

For A1, hold three forms firmly:

- **я вмиваюся** — I wash up.
- **ти вмиваєшся** — you wash up.
- **вона вмивається** — she washes up.

<!-- INJECT_ACTIVITY: act-2 -->
<!-- INJECT_ACTIVITY: act-3 -->

## Мій ранок

A basic morning story needs reflexive verbs, a few regular verbs, and sequence words. Keep each sentence short.

| Зворотні дієслова | Незворотні дієслова |
|---|---|
| прокидатися | снідати |
| вмиватися | пити каву |
| одягатися | йти |
| збиратися | гуляти |
| повертатися | лежати |

**Йти** is irregular. Its first three present forms are memorized, not built from the usual pattern.  
<!-- VERIFY: source="Plan grammar item; Knowledge Packet dictionary context verifies йти as VESUM verb" -->

| Особа | Форма |
|---|---|
| я | йду |
| ти | йдеш |
| він/вона | йде |

Sequence words make the routine into a small story.

| Слово | Meaning |
|---|---|
| спочатку | first |
| потім | then |
| після цього | after this |
| нарешті | finally |

A clean A1 morning:

- **Спочатку я прокидаюся.** — First I wake up.
- **Потім вмиваюся.** — Then I wash up.
- **Після цього снідаю.** — After this I have breakfast.
- **Нарешті йду на роботу.** — Finally I go to work.

A weekend version changes the pace:

- **У суботу я не поспішаю.** — On Saturday I do not hurry.
- **Прокидаюся пізно.** — I wake up late.
- **Потім п'ю каву.** — Then I drink coffee.
- **Нарешті гуляю.** — Finally I walk.

<!-- INJECT_ACTIVITY: act-4 -->
<!-- INJECT_ACTIVITY: act-5 -->

## Підсумок

The core rule is small: regular personal ending first, **-ся** last. The ending belongs to the whole verb form.

| Основа | Особова форма | З -ся |
|---|---|---|
| вмивати | я вмиваю | я вмиваюся |
| вмивати | ти вмиваєш | ти вмиваєшся |
| вмивати | вона вмиває | вона вмивається |

Morning chain:

**прокидатися → вмиватися → одягатися → снідати → йти**

Sequence chain:

**спочатку → потім → після цього → нарешті**

Three checks:

1. **-ся** sits at the end: **я вмиваюся**.
2. **-шся** sounds like [с':а]: **ти вмиваєшся**.
3. **-ться** sounds like [ц':а]: **вона вмивається**.

Good A1 answer:

- **Спочатку я прокидаюся.**
- **Потім вмиваюся.**
- **Після цього одягаюся.**
- **Нарешті йду.**

Self-check: write four short sentences about your morning. Use two sequence words and three morning verbs. Read the answer aloud once. Check the spelling of **-шся** and **-ться** after you speak it.

This module connects forward to **a1-021**, where these action patterns become part of the first review checkpoint.

<!-- VERIFY: source="Захарійчук Grade 4, p.162 plan reference is corpus_missing=true; no verbatim textbook quote retrieved in this runtime" -->

<!-- INJECT_ACTIVITY: act-10 -->
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "match-up",
    "instruction": "Match each Ukrainian line to its English meaning.",
    "pairs": [
      {
        "left": "Я прокидаюся о сьомій.",
        "right": "I wake up at seven."
      },
      {
        "left": "Вмиваюся.",
        "right": "I wash up."
      },
      {
        "left": "Одягаюся.",
        "right": "I get dressed."
      },
      {
        "left": "Снідаю.",
        "right": "I have breakfast."
      },
      {
        "left": "Я йду на роботу.",
        "right": "I go to work."
      }
    ]
  },
  {
    "id": "act-2",
    "type": "fill-in",
    "instruction": "Add the missing reflexive ending.",
    "items": [
      {
        "sentence": "Я вмиваю__.",
        "answer": "ся",
        "options": ["ся", "ти", "є"]
      },
      {
        "sentence": "Ти одягаєш__.",
        "answer": "ся",
        "options": ["ся", "сять", "є"]
      },
      {
        "sentence": "Він прокидаєть__.",
        "answer": "ся",
        "options": ["ся", "ти", "ють"]
      },
      {
        "sentence": "Вона збираєть__.",
        "answer": "ся",
        "options": ["ся", "сь", "те"]
      },
      {
        "sentence": "Я повертаю__.",
        "answer": "ся",
        "options": ["ся", "ш", "ть"]
      }
    ]
  },
  {
    "id": "act-3",
    "type": "quiz",
    "instruction": "Choose the form that fits the sentence.",
    "items": [
      {
        "question": "Я ____ о сьомій.",
        "options": [
          {
            "text": "прокидаюся",
            "correct": true
          },
          {
            "text": "прокидаєшся",
            "correct": false
          },
          {
            "text": "прокидається",
            "correct": false
          }
        ],
        "explanation": "Я takes прокидаюся."
      },
      {
        "question": "Ти швидко ____?",
        "options": [
          {
            "text": "вмиваюся",
            "correct": false
          },
          {
            "text": "вмиваєшся",
            "correct": true
          },
          {
            "text": "вмивається",
            "correct": false
          }
        ],
        "explanation": "Ти takes вмиваєшся."
      },
      {
        "question": "Вона ____ пізно.",
        "options": [
          {
            "text": "прокидаюся",
            "correct": false
          },
          {
            "text": "прокидаєшся",
            "correct": false
          },
          {
            "text": "прокидається",
            "correct": true
          }
        ],
        "explanation": "Вона takes прокидається."
      },
      {
        "question": "Я ____ на роботу.",
        "options": [
          {
            "text": "йду",
            "correct": true
          },
          {
            "text": "йдеш",
            "correct": false
          },
          {
            "text": "йде",
            "correct": false
          }
        ],
        "explanation": "Я takes йду."
      }
    ]
  },
  {
    "id": "act-4",
    "type": "order",
    "instruction": "Put the morning routine in a natural order.",
    "items": [
      "Спочатку я прокидаюся.",
      "Потім вмиваюся.",
      "Після цього одягаюся.",
      "Потім снідаю.",
      "Нарешті йду на роботу."
    ],
    "correct_order": [0, 1, 2, 3, 4]
  },
  {
    "id": "act-5",
    "type": "group-sort",
    "instruction": "Sort the verbs into reflexive and non-reflexive groups.",
    "groups": [
      {
        "name": "Зворотні",
        "items": ["прокидатися", "вмиватися", "одягатися", "збиратися", "повертатися"]
      },
      {
        "name": "Незворотні",
        "items": ["снідати", "йти", "пити", "гуляти", "лежати"]
      }
    ]
  },
  {
    "id": "act-6",
    "type": "true-false",
    "instruction": "Decide whether each statement is true.",
    "items": [
      {
        "statement": "Я вмиваюся means I wash up.",
        "correct": true,
        "explanation": "The action is directed back to the speaker."
      },
      {
        "statement": "Ти вмиваюся is the correct ти form.",
        "correct": false,
        "explanation": "The ти form is ти вмиваєшся."
      },
      {
        "statement": "Йти is irregular.",
        "correct": true,
        "explanation": "Use я йду, ти йдеш, він/вона йде."
      },
      {
        "statement": "Снідати normally takes -ся.",
        "correct": false,
        "explanation": "Снідати is not reflexive."
      }
    ]
  },
  {
    "id": "act-7",
    "type": "unjumble",
    "instruction": "Put the words in the right order.",
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
        "words": ["нарешті", "йду", "я"],
        "answer": "Нарешті я йду."
      }
    ]
  },
  {
    "id": "act-8",
    "type": "error-correction",
    "instruction": "Find the wrong form and choose the correction.",
    "items": [
      {
        "sentence": "Я прокидаєшся о сьомій.",
        "error": "прокидаєшся",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "прокидається", "прокидатися"],
        "explanation": "Я takes прокидаюся."
      },
      {
        "sentence": "Ти вмиваюся швидко.",
        "error": "вмиваюся",
        "answer": "вмиваєшся",
        "options": ["вмиваєшся", "вмивається", "вмиватися"],
        "explanation": "Ти takes вмиваєшся."
      },
      {
        "sentence": "Вона йду на роботу.",
        "error": "йду",
        "answer": "йде",
        "options": ["йде", "йдеш", "йти"],
        "explanation": "Вона takes йде."
      }
    ]
  },
  {
    "id": "act-9",
    "type": "translate",
    "instruction": "Choose the best Ukrainian translation.",
    "items": [
      {
        "source": "I wake up.",
        "options": [
          {
            "text": "Я прокидаюся.",
            "correct": true
          },
          {
            "text": "Ти прокидаєшся.",
            "correct": false
          },
          {
            "text": "Вона прокидається.",
            "correct": false
          }
        ],
        "explanation": "I = я."
      },
      {
        "source": "Then I have breakfast.",
        "options": [
          {
            "text": "Потім я снідаю.",
            "correct": true
          },
          {
            "text": "Спочатку я йду.",
            "correct": false
          },
          {
            "text": "Нарешті я лежу.",
            "correct": false
          }
        ],
        "explanation": "Then = потім."
      },
      {
        "source": "Finally I go.",
        "options": [
          {
            "text": "Нарешті я йду.",
            "correct": true
          },
          {
            "text": "Потім я вмиваюся.",
            "correct": false
          },
          {
            "text": "Спочатку я прокидаюся.",
            "correct": false
          }
        ],
        "explanation": "Finally = нарешті."
      }
    ]
  },
  {
    "id": "act-10",
    "type": "fill-in",
    "instruction": "Complete a three-sentence morning routine.",
    "items": [
      {
        "sentence": "Спочатку я ____.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "йду", "снідаю"]
      },
      {
        "sentence": "Потім я ____.",
        "answer": "вмиваюся",
        "options": ["вмиваюся", "гуляю", "лежу"]
      },
      {
        "sentence": "Нарешті я ____.",
        "answer": "йду",
        "options": ["йду", "одягаюся", "прокидаюся"]
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
    "lemma": "вставати",
    "translation": "to get up",
    "pos": "verb",
    "usage": "Я встаю рано."
  },
  {
    "lemma": "вмиватися",
    "translation": "to wash up",
    "pos": "verb",
    "usage": "Я вмиваюся."
  },
  {
    "lemma": "одягатися",
    "translation": "to get dressed",
    "pos": "verb",
    "usage": "Я одягаюся."
  },
  {
    "lemma": "збиратися",
    "translation": "to get ready",
    "pos": "verb",
    "usage": "Я збираюся."
  },
  {
    "lemma": "повертатися",
    "translation": "to return",
    "pos": "verb",
    "usage": "Я повертаюся."
  },
  {
    "lemma": "навчатися",
    "translation": "to study",
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
    "usage": "Я снідаю."
  },
  {
    "lemma": "йти",
    "translation": "to go",
    "pos": "verb",
    "usage": "Я йду на роботу."
  },
  {
    "lemma": "пити",
    "translation": "to drink",
    "pos": "verb",
    "usage": "Я п'ю каву."
  },
  {
    "lemma": "кава",
    "translation": "coffee",
    "pos": "noun",
    "usage": "Я п'ю каву."
  },
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок спокійний."
  },
  {
    "lemma": "робота",
    "translation": "work",
    "pos": "noun",
    "usage": "Я йду на роботу."
  },
  {
    "lemma": "спочатку",
    "translation": "first",
    "pos": "adverb",
    "usage": "Спочатку я прокидаюся."
  },
  {
    "lemma": "потім",
    "translation": "then",
    "pos": "adverb",
    "usage": "Потім я вмиваюся."
  },
  {
    "lemma": "після цього",
    "translation": "after this",
    "pos": "phrase",
    "usage": "Після цього я снідаю."
  },
  {
    "lemma": "нарешті",
    "translation": "finally",
    "pos": "adverb",
    "usage": "Нарешті я йду."
  },
  {
    "lemma": "вранці",
    "translation": "in the morning",
    "pos": "adverb",
    "usage": "Я навчаюся вранці."
  },
  {
    "lemma": "пізно",
    "translation": "late",
    "pos": "adverb",
    "usage": "Я прокидаюся пізно."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Караман Grade 10, p.176",
    "notes": "Plan reference: зворотні дієслова; суфікс -ся(-сь) означає дію, спрямовану на себе. Verbatim textbook excerpt unavailable in packet; corpus_missing=true."
  },
  {
    "title": "Кравцова Grade 4, p.113",
    "notes": "Plan reference: вимова -шся=[с'а], -ться=[ц'а]. Verbatim textbook excerpt unavailable in packet; corpus_missing=true."
  },
  {
    "title": "Захарійчук Grade 4, p.162",
    "notes": "Plan reference: дієслова на -ся; вправи з вимовою та правописом. Verbatim textbook excerpt unavailable in packet; corpus_missing=true."
  },
  {
    "title": "Knowledge Packet: pedagogy/a1/my-morning.md",
    "notes": "Compiled wiki context used for A1 sequencing, L2 error prevention, vocabulary minimum, and pronunciation warnings."
  }
]
```

<end_gate>
<rescanned_words>прокидатися, вставати, вмиватися, одягатися, збиратися, повертатися, навчатися, поспішати, снідати, йти, пити, кава, ранок, робота, субота, телефон, спочатку, потім, після, цього, нарешті, вранці, пізно, прокидаюся, прокидаєшся, вмиваюся, вмиваєшся, вмивається, одягаюся, снідаю, йду, йдеш, йде, поспішаю, лежу, дивлюся, гуляю, п'ю, каву, сьомій, восьмій.</rescanned_words>
<rescanned_sources>Knowledge Packet pedagogy/a1/my-morning.md; Караман Grade 10 p.176 marked corpus_missing=true; Кравцова Grade 4 p.113 marked corpus_missing=true; Захарійчук Grade 4 p.162 marked corpus_missing=true.</rescanned_sources>
<grammar_claims_grounded>Зворотні дієслова express action directed back to subject: grounded in Knowledge Packet S9 and plan Караман note, unresolved corpus excerpt. -ся follows the personal form: grounded in plan and Knowledge Packet sequence. -шся=[с':а] and -ться=[ц':а]: grounded in Knowledge Packet S1/S9 and plan Кравцова note, unresolved corpus excerpt. Йти forms я йду, ти йдеш, він/вона йде: grounded in plan and VESUM local form checks.</grammar_claims_grounded>
<removed_unverified>Removed all invented verbatim textbook blockquotes because the supplied packet says all three plan-reference excerpts are corpus_missing and no mcp__sources__search_text tool is available. Removed будний after local VESUM check did not verify it; used робочий instead.</removed_unverified>
</end_gate>