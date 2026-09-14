<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-14T12:07:05Z sender=7d0d39bf-4b16-4747-a2c2-349b4db08dc2/task-151 priority=MESSAGE_PRIORITY_HIGH content=Task id "7d0d39bf-4b16-4747-a2c2-349b4db08dc2/task-151" finished with result:

The command exited with code 0.
Output:
молоко: молоко́ (index 2)
яблуко: я́блуко (index 0)
людина: люди́на (index 1)
вулиця: ву́лиця (index 0)
столиця: столи́ця (index 1)
каша: ка́ша (index 0)
пісня: пі́сня (index 0)
мама: ма́ма (index 0)
тато: та́то (index 0)
вода: вода́ (index 1)
рука: рука́ (index 1)
хата: ха́та (index 0)
книга: кни́га (index 0)
аптека: апте́ка (index 1)
університет: університе́т (index 4)
бібліотека: бібліоте́ка (index 3)
фотографія: фотогра́фія (index 3)
Київ: Ки́їв (index 0)
Одеса: Оде́са (index 1)
Харків: Ха́рків (index 0)
Дніпро: Дніпро́ (index 1)
Полтава: Полта́ва (index 1)
джерело: джерело́ (index 2)
сім'я: сім'я́ (index 1)
абетка: абе́тка (index 1)


Log: file:///home/ops/.gemini/antigravity-cli/brain/7d0d39bf-4b16-4747-a2c2-349b4db08dc2/.system_generated/tasks/task-151.log
</SYSTEM_MESSAGE>
<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-14T12:07:11Z sender=7d0d39bf-4b16-4747-a2c2-349b4db08dc2/task-153 priority=MESSAGE_PRIORITY_HIGH content=Task id "7d0d39bf-4b16-4747-a2c2-349b4db08dc2/task-153" finished with result:

The command exited with code 0.
Output:
Found 3 matches in textbooks:

1. **Большакова І. О., Пристінська М. С. — Українська мова та читання. 2 клас. Частина 1**
   `textbook:grade-2/bolshakova-ukr-2-1` · Grade 2 · Page 18
   > Скільки у слові голосних звуків, стільки й складів. Склад утворює тільки голосний звук або голосний звук разом з одним чи кількома приголосними звуками: о-сінь, лі-то, день. Склад, який закінчується голосним звуком, називають відкритим: ма-ма, во-да. Склад, який закінчується приголосним звуком, називають закритим: ліс, мир, сон.


2. **Большакова І. О., Пристінська М. С. — Українська мова та читання. 2 клас. Частина 1**
   `textbook:grade-2/bolshakova-ukr-2-1` · Grade 2 · Page 19
   > Склади бувають відкриті та закриті. Звуковий аналіз слова.


3. **Пономарьова К. І. — Українська мова та читання. 2 клас. Частина 1**
   `textbook:grade-2/ponomarova-ukr-2-1` · Grade 2 · Page 22
   > У слові стільки складів, скільки голосних звуків.


Log: file:///home/ops/.gemini/antigravity-cli/brain/7d0d39bf-4b16-4747-a2c2-349b4db08dc2/.system_generated/tasks/task-153.log
</SYSTEM_MESSAGE>
<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-14T12:09:09Z sender=7d0d39bf-4b16-4747-a2c2-349b4db08dc2/task-207 priority=MESSAGE_PRIORITY_HIGH content=Task id "7d0d39bf-4b16-4747-a2c2-349b4db08dc2/task-207" finished with result:

The command exited with code 0.
Output:
<truncated 864 lines>
+    for placement, i, a in originals:
+        p = prov.get((placement, i))
+        expected_id = a.get("id") if placement == "inline" else f"act-w{i+1}"
+        if not p:
+            block(f"provenance missing for original {placement}[{i}] ({expected_id})")
+            continue
+        if p.get("new_id") != expected_id:
+            block(f"original {placement}[{i}] must keep id {expected_id}; provenance says {p.get('new_id')}")
+        na = new_acts.get(expected_id)
+        if not na:
+            block(f"original {expected_id} not found in any lesson")
+            continue
+        n, _, act = na
+        if p.get("lesson") != n:
+            block(f"provenance says {expected_id} in lesson {p.get('lesson')} but it lives in lesson {n}")
+        if act.get("type") != a.get("type"):
+            block(f"{expected_id}: type {a.get('type')} became {act.get('type')}")
+        payload = {k: v for k, v in a.items() if k in LIST_FIELDS}
+        if not payload:
+            block(f"{expected_id}: original has no list payload to compare (checker config)")
+        elif not contains(payload, {k: act.get(k) for k in payload}):
+            block(f"{expected_id}: original items/answers/groups not preserved structurally")
+
+
+    # Exemptions cannot be invented for new writer activities.
+    original_ids = {a.get("id") for a in base_acts.get("inline", [])} | {
+        f"act-w{i + 1}" for i, _ in enumerate(base_acts.get("workbook", []))}
+    if not set(exempt) <= original_ids:
+        block("item exemptions may name only preserved original activities")
+    if len(provenance) != len(originals) or len(prov) != len(provenance):
+        block("provenance must cover every original exactly once")
+    # Allocation records first introduction once; a later lesson may use prior vocabulary.
+    for path in module_dir.glob("lesson-*/*"):
+        if path.name not in {"module.md", "activities.yaml", "vocabulary.yaml"}:
+            continue
+        for line in path.read_text().splitlines():
+            if NAME_RE.search(line) and not ATTR_RE.search(line):
+                block(f"unattributed reference-name hit in {path.name}")
+    for n, md in lesson_md_raw.items():
+        try:
+            from scripts.build.linear_pipeline import (
+                _advisory_immersion_pct,
+                _component_density_gate,
+                _l2_exposure_floor_gate,
+                _long_uk_ceiling_gate,
+            )
+            a1_plan = {**plan, "level": "a1"}
+            # The vocabulary tab is part of each lesson's learner-facing surface.
+            surface = md + "\n" + "\n".join(
+                f"- **{e['lemma']}** — {e['translation']}" for e in lesson_vocab[n])
+            immersion = {
+                "ratio_advisory": _advisory_immersion_pct(surface, a1_plan),
+                "l2_exposure_floor": _l2_exposure_floor_gate(surface, a1_plan),
+                "long_uk_ceiling": _long_uk_ceiling_gate(surface, a1_plan),
+                "component_density": _component_density_gate(surface, a1_plan),
+            }
+            report["facts"].setdefault("immersion", {})[n] = immersion
+            for name, result in immersion.items():
+                if not result["passed"]:
+                    block(f"lesson {n}: {name} failed: {result}")
+        except Exception as exc:
+            block(f"lesson {n}: immersion gate unavailable: {type(exc).__name__}")
+        page = (rendered or {}).get(str(n), (rendered or {}).get(f"{n}.mdx", ""))
+        if not page:
+            block(f"lesson {n}: render coverage missing")
+            continue
+        # Parse serialized props as well as Markdown: escaped strings must remain
+        # represented on the published surface (e.g. OddOneOut choices).
+        decoded = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), page)
+        decoded = decoded.replace('\\"', '"').replace("\\n", " ")
+        visible = norm_text(md_to_text(decoded))
+        literal_text = norm_text(strip_comments(decoded))
+        if len(re.findall(r"<TabItem\s", strip_comments(page))) != 4:
+            block(f"lesson {n}: render must have four learner tabs")
+        for para in paragraphs(md):
+            if len(para.split()) < 8:
+                continue
+            if para.lstrip().startswith(">") and "<DialogueBox" in page:
+                # DialogueBox serializes speaker and spoken text as separate props.
+                chunks = [re.sub(r"^>\s*", "", line) for line in para.splitlines() if line.strip()]
+                missing = False
+                for chunk in chunks:
+                    speaker, sep, spoken = chunk.partition(":")
+                    for value in (speaker, spoken) if sep else (chunk,):
+                        if md_to_text(value) not in literal_text:
+                            missing = True
+                if not missing:
+                    continue
+            if md_to_text(para) not in visible:
+                block(f"lesson {n}: render lacks lesson paragraph: {md_to_text(para)[:100]!r}")
+        for aid, (owner, _, act) in new_acts.items():
+            if owner != n:
+                continue
+            for value in leaves({k: v for k, v in act.items() if k in LIST_FIELDS or k in ("title", "instruction")}):
+                if isinstance(value, str) and len(value) >= 3 and norm_text(value) not in literal_text:
+                    block(f"lesson {n}: render lacks activity string from {aid}: {value!r}")
+        for entry in lesson_vocab[n]:
+            if norm_text(str(entry["lemma"])) not in visible:
+                block(f"lesson {n}: render lacks vocabulary lemma")
+        for resource in lesson_res[n]:
+            if norm_text(str(resource["title"])) not in visible:
+                block(f"lesson {n}: render lacks resource title")
+    landing = (rendered or {}).get("index", (rendered or {}).get("index.mdx", ""))
+    if not landing:
+        block("module landing render missing")
+    else:
+        landing_text = norm_text(strip_comments(landing).replace('\\"', '"'))
+        if len(re.findall(r"<TabItem\s", strip_comments(landing))) != 4:
+            block("module landing must have four learner tabs")
+        for lemma in base_lemmas:
+            if lemma not in landing_text.lower():
+                block("module landing lacks vocabulary union entry")
+        for n, entries in lesson_res.items():
+            if f"/{n}/" not in landing:
+                block(f"module landing lacks lesson {n} link")
+            for entry in entries:
+                if norm_text(str(entry["title"])) not in landing_text:
+                    block("module landing lacks resource union entry")
+        for aid, (_, placement, activity) in new_acts.items():
+            if placement == "workbook":
+                for value in leaves({k: v for k, v in activity.items()
+                                     if k in LIST_FIELDS or k in ("title", "instruction")}):
+                    if isinstance(value, str) and len(value) >= 3 and norm_text(value) not in landing_text:
+                        block(f"module landing lacks workbook union string from {aid}")
+    return {"passed": not report["blocking"], "diagnostics": report["blocking"], **report}
+
+
+def run_lesson_gates(module_dir: Path, source_dir: Path, plan: dict,
+                     rendered: dict[str, str] | None = None) -> dict:
+    """Fail closed on invalid artifacts as well as semantic gate failures."""
+    try:


Log: file:///home/ops/.gemini/antigravity-cli/brain/7d0d39bf-4b16-4747-a2c2-349b4db08dc2/.system_generated/tasks/task-207.log
</SYSTEM_MESSAGE>
```markdown file=module.md
# Читаємо українською

**ма — мо — му — ми. ма́ма. молоко́.** — syllables and first words.

Приві́т! In Module 1 you met Ukrainian letters and the word **склад**. Here
you turn that word into a reading tool. Printed Ukrainian comes first; English
support helps you check what your eyes already found.

For one listening pass before you read fast, open the public ULP <!-- source: ULP -->
[Ukrainian Alphabet guide](https://www.ukrainianlessons.com/ukrainian-alphabet/).
Use it only as listen-and-repeat support: do not download, transcribe, remix,
or reuse the audio. Listen for the vowel sound, point to the letter on this
page, then read the printed word.

Module 1 only previewed **склад**. This module teaches the counting rule:

**one vowel sound = one склад**

In print, count the letters that mark vowel sounds. Then split the word into
syllables and read it without guessing from another alphabet.

By the end, you can:

- count syllables by counting vowel sounds;
- read simple open syllables such as **ма**, **мо**, **му**, **ми**;
- keep the six simple vowel sounds clear;
- explain what **Я, Ю, Є, Ї** do at beginner level;
- read **ма́ма**, **молоко́**, **день**, **я́блуко**, **люди́на**, and
  **ву́лиця**;
- avoid the first reading traps: splitting **дж** and **дз**, ignoring **ь**,
  blurring **о**, and losing **й** in **ї**.

## Склади

**склад** — syllable.

Start every reading attempt with one Ukrainian question:

**Де голосні звуки?** — Where are the vowel sounds?

In Ukrainian, every syllable has a vowel sound. A single vowel can be a whole
syllable, and a consonant by itself cannot make a syllable.

| Слово́ | Letters that mark vowel sounds | Склади́ |
| --- | --- | --- |
| **день** | **е** | 1 |
| **ма́ма** | **а + а** | 2 |
| **молоко́** | **о + о + о** | 3 |
| **ву́лиця** | **у + и + я** | 3 |

Use a simple body check. Put a hand lightly under your chin and say the word
slowly. Each open vowel pulse makes the chin move. That movement is a
beginner check before you write or choose an answer.

Build from syllables instead of naming letters one by one:

| Letter path | Reading path |
| --- | --- |
| М + А | **ма** |
| М + О | **мо** |
| М + У | **му** |
| М + И | **ми** |

Then join syllables:

**ма + ма = ма́ма**

**мо + ло + ко = молоко́**

:::tip
**склад** — syllable. Find the vowel sound first. That is the anchor.
:::

<!-- INJECT_ACTIVITY: act-1 -->

Ukrainian children learn this rule from their very first school reader: «У слові стільки складів, скільки в ньому голосних звуків» (quoted from: Большакова, буквар 1 клас, p. 25). Each vowel forms the core of its own syllable beat.

<!-- INJECT_ACTIVITY: act-syllables-quiz -->

## Голосні лі́тери

**А О У Е И І** — six simple letters for vowel sounds.

The sounds are:

**[а] [о] [у] [е] [и] [і]**

Read them as clean sounds. In **молоко́**, every **о** stays **о**:

**мо-ло-ко́**

Say it slowly as three open beats, but keep the written word whole on the
page.

Now add the four other letters that mark vowel sounds:

**Я Ю Є Ї**

At beginner level, use this two-job rule:

| Лі́тера | At the start of a word or after a vowel/apostrophe | After a consonant |
| --- | --- | --- |
| **Я** | **[йа]** as in **я́блуко** | softens the consonant + **[а]** |
| **Ю** | **[йу]** | softens the consonant + **[у]** |
| **Є** | **[йе]** | softens the consonant + **[е]** |
| **Ї** | always **[йі]** | always **[йі]** |

**Ї** is not a softening letter. It is always two sounds: **[йі]**. In
**Украї́на**, read **ї** as **[йі]**.

Use three safe examples:

| Слово́ | English support | What to read |
| --- | --- | --- |
| **я́блуко** | apple | **я** starts the word: **[йа]** |
| **люди́на** | person | **ю** follows **л** and marks softness + **[у]** |
| **пі́сня** | song | **я** follows **н** and marks softness + **[а]** |

You do not need every phonetic detail yet. Look at the position of
**Я, Ю, Є, Ї**, then read the word slowly.

:::caution
Keep this beginner rule small: **Ї** is always **[йі]**. For **Я, Ю, Є**,
look at the position first, then read slowly.
:::

<!-- INJECT_ACTIVITY: act-2 -->

Pay special attention to the difference between **И** and **І**: **кит** (whale) has the open, retracted sound **[и]**, while **кіт** (cat) has the front vowel **[і]**. One vowel changes the entire meaning.

<!-- INJECT_ACTIVITY: act-vowels-fill -->

## Читаємо слова́

**ма́ма. та́то. вода́. ка́ша.**

Use this three-step reading routine:

1. Find the vowel sounds.
2. Split the word into syllables.
3. Read the syllables smoothly, not as separate letter names.

Try the routine with easy words:

| Слово́ | Split | English support |
| --- | --- | --- |
| **ма́ма** | 2 syllables | mother |
| **та́то** | 2 syllables | father |
| **вода́** | 2 syllables | water |
| **ка́ша** | 2 syllables | porridge |
| **ву́лиця** | 3 syllables | street |
| **столи́ця** | 3 syllables | capital |

Longer words use the same routine with more vowel sounds:

| Слово́ | Split | Beginner note |
| --- | --- | --- |
| **університе́т** | 5 syllables | read from left to right |
| **бібліоте́ка** | 5 syllables | **о** is its own vowel pulse |
| **фотогра́фія** | 5 syllables | final **я** gives the last vowel |

Names of Ukrainian cities are also good reading practice:

| Мі́сто | Split | Note |
| --- | --- | --- |
| **Ки́їв** | 2 syllables | **ї** is **[йі]** |
| **Львів** | 1 syllable | one vowel sound |
| **Оде́са** | 3 syllables | initial **О** can stand alone |
| **Дніпро́** | 2 syllables | consonant cluster, still two vowels |
| **Полта́ва** | 3 syllables | steady open syllables |

Three signs or combinations return in Module 3:

| Form | Beginner reading habit |
| --- | --- |
| **Ь** | no sound of its own; softens the previous consonant |
| **апо́строф** | keeps the next **я/ю/є/ї** separate with **й** |
| **ДЖ / ДЗ** | one joined sound, not two broken sounds |

Read **день** with soft **н**, not with an extra vowel after it. Read
**сім'я́** with a clear **й** before **я**. Read **джерело́** with joined
**дж**.

:::tip
If a word feels long, do not speed up. Find the letters for vowel sounds, make
small syllable beats, then smooth them into one word.
:::

<!-- INJECT_ACTIVITY: act-3 -->

Practice reading with a partner. Student A reads the syllables slowly; Student B checks the vowel count and meaning:

> Олена: Що тут написано? (What is written here?)
> Тарас: Тут слово «ма-ма». (Here is the word "ma-ma".)
> Олена: А тут? (And here?)
> Тарас: Тут «мо-ло-ко». Три склади! (Here is "mo-lo-ko". Three syllables!)
> Олена: Молодець! А це слово? (Well done! And this word?)
> Тарас: «Ву-ли-ця». Теж три склади! ("Vu-ly-tsia". Also three syllables!)

Support after the dialogue:

| Українська | English support |
| --- | --- |
| **Що тут написано?** | What is written here? |
| **Тут слово «ма-ма».** | Here is the word "ma-ma". |
| **А тут?** | And here? |
| **Тут «мо-ло-ко». Три склади!** | Here is "mo-lo-ko". Three syllables! |
| **Молодець! А це слово?** | Well done! And this word? |
| **«Ву-ли-ця». Теж три склади!** | "Vu-ly-tsia". Also three syllables! |

<!-- INJECT_ACTIVITY: act-words-match -->

Now you can comfortably find vowel sounds, identify open syllables, and read everyday Ukrainian words smoothly. In Lesson 2, you will learn to navigate reading traps and connect print to notebook handwriting.
```

```json file=activities.yaml
{
  "inline": [
    {
      "id": "act-1",
      "type": "count-syllables",
      "title": "Рахуй склади́",
      "instruction": "Рахуй голосні звуки. Кожен голосни́й звук дає один склад.",
      "maxCount": 5,
      "items": [
        {
          "word": "день",
          "correct": 1
        },
        {
          "word": "ма́ма",
          "correct": 2
        },
        {
          "word": "молоко́",
          "correct": 3
        },
        {
          "word": "ву́лиця",
          "correct": 3
        },
        {
          "word": "бібліоте́ка",
          "correct": 5
        },
        {
          "word": "Украї́на",
          "correct": 4
        }
      ]
    },
    {
      "id": "act-syllables-quiz",
      "type": "quiz",
      "title": "Скільки голосних — стільки складів",
      "instruction": "Визнач кількість складів у слові за кількістю голосних звуків.",
      "questions": [
        {
          "question": "Скільки складів у слові «ха-та»?",
          "options": [
            {
              "text": "1",
              "correct": false
            },
            {
              "text": "2",
              "correct": true
            },
            {
              "text": "3",
              "correct": false
            }
          ],
          "explanation": "У слові «хата» два голосні звуки [а], тому два склади."
        },
        {
          "question": "Скільки складів у слові «ру-ка»?",
          "options": [
            {
              "text": "2",
              "correct": true
            },
            {
              "text": "1",
              "correct": false
            },
            {
              "text": "3",
              "correct": false
            }
          ],
          "explanation": "У слові «рука» два голосні звуки [у, а] — два склади."
        },
        {
          "question": "Скільки складів у слові «во-да»?",
          "options": [
            {
              "text": "3",
              "correct": false
            },
            {
              "text": "2",
              "correct": true
            },
            {
              "text": "1",
              "correct": false
            }
          ],
          "explanation": "У слові «вода» два голосні звуки [о, а] — два склади."
        },
        {
          "question": "Скільки складів у слові «ка-ша»?",
          "options": [
            {
              "text": "2",
              "correct": true
            },
            {
              "text": "4",
              "correct": false
            },
            {
              "text": "1",
              "correct": false
            }
          ],
          "explanation": "У слові «каша» два голосні звуки [а, а] — два склади."
        },
        {
          "question": "Скільки складів у слові «банк»?",
          "options": [
            {
              "text": "2",
              "correct": false
            },
            {
              "text": "1",
              "correct": true
            },
            {
              "text": "3",
              "correct": false
            }
          ],
          "explanation": "У слові «банк» лише один голосний звук [а] — один склад."
        },
        {
          "question": "Скільки складів у слові «сон»?",
          "options": [
            {
              "text": "1",
              "correct": true
            },
            {
              "text": "2",
              "correct": false
            },
            {
              "text": "3",
              "correct": false
            }
          ],
          "explanation": "У слові «сон» один голосний звук [о] — один склад."
        }
      ]
    },
    {
      "id": "act-2",
      "type": "match-up",
      "title": "Роль літер у читанні",
      "instruction": "З'єднай лі́теру з її роллю в читанні.",
      "pairs": [
        {
          "left": "А",
          "right": "позначає [а]"
        },
        {
          "left": "О",
          "right": "позначає [о]"
        },
        {
          "left": "И",
          "right": "позначає [и]"
        },
        {
          "left": "І",
          "right": "позначає [і]"
        },
        {
          "left": "Я на початку слова",
          "right": "[йа]"
        },
        {
          "left": "Ї",
          "right": "завжди [йі]"
        }
      ]
    },
    {
      "id": "act-vowels-fill",
      "type": "fill-in",
      "title": "Впізнай голосну літеру",
      "instruction": "Встав правильну літеру у слово.",
      "items": [
        {
          "sentence": "Яблуко починається на літеру [Я].",
          "blanks": [
            "Я"
          ],
          "options": [
            "Я",
            "Ю",
            "Є"
          ],
          "explanation": "У слові яблуко початкова літера Я позначає [йа]."
        },
        {
          "sentence": "У слові Україна є особлива літера [Ї].",
          "blanks": [
            "Ї"
          ],
          "options": [
            "Ї",
            "І",
            "И"
          ],
          "explanation": "Літера Ї завжди позначає два звуки [йі]."
        },
        {
          "sentence": "У слові людина після л стоїть літера [ю].",
          "blanks": [
            "ю"
          ],
          "options": [
            "ю",
            "я",
            "є"
          ],
          "explanation": "Літера ю пом'якшує приголосний [л']."
        },
        {
          "sentence": "У слові пісня після н стоїть літера [я].",
          "blanks": [
            "я"
          ],
          "options": [
            "я",
            "а",
            "о"
          ],
          "explanation": "Літера я пом'якшує попередній звук [н']."
        },
        {
          "sentence": "У слові молоко всі три голосні — це літери [о].",
          "blanks": [
            "о"
          ],
          "options": [
            "о",
            "а",
            "у"
          ],
          "explanation": "Всі три склади у слові молоко мають голосний звук [о]."
        },
        {
          "sentence": "У слові каша голосні звуки позначає літера [а].",
          "blanks": [
            "а"
          ],
          "options": [
            "а",
            "о",
            "и"
          ],
          "explanation": "У слові каша дві голосні літери а."
        }
      ]
    },
    {
      "id": "act-3",
      "type": "divide-words",
      "title": "Поділи на склади́",
      "instruction": "Поділи кожне друковане слово на склади́.",
      "items": [
        {
          "word": "ма́ма",
          "answer": "ма ма"
        },
        {
          "word": "молоко́",
          "answer": "мо ло ко"
        },
        {
          "word": "ву́лиця",
          "answer": "ву ли ця"
        },
        {
          "word": "столи́ця",
          "answer": "сто ли ця"
        },
        {
          "word": "люди́на",
          "answer": "лю ди на"
        },
        {
          "word": "бібліоте́ка",
          "answer": "бі блі о те ка"
        }
      ]
    },
    {
      "id": "act-words-match",
      "type": "match-up",
      "title": "Слово та його значення",
      "instruction": "З'єднай прочитане українське слово з англійським перекладом.",
      "pairs": [
        {
          "left": "ма́ма",
          "right": "mother"
        },
        {
          "left": "та́то",
          "right": "father"
        },
        {
          "left": "вода́",
          "right": "water"
        },
        {
          "left": "ка́ша",
          "right": "porridge"
        },
        {
          "left": "ву́лиця",
          "right": "street"
        },
        {
          "left": "столи́ця",
          "right": "capital"
        }
      ]
    }
  ],
  "workbook": [
    {
      "id": "act-w1",
      "type": "group-sort",
      "title": "Один, два чи три склади́",
      "instruction": "Розподіли слова за кількістю складів.",
      "groups": [
        {
          "label": "Один склад",
          "items": [
            "день",
            "Львів"
          ]
        },
        {
          "label": "Два склади́",
          "items": [
            "ма́ма",
            "та́то",
            "Ки́їв"
          ]
        },
        {
          "label": "Три склади́",
          "items": [
            "молоко́",
            "ву́лиця",
            "столи́ця"
          ]
        }
      ]
    },
    {
      "id": "act-w2",
      "type": "odd-one-out",
      "title": "Зайве за кількістю складів",
      "instruction": "Обери слово, яке має іншу кількість складів.",
      "items": [
        {
          "words": [
            "ма́ма",
            "та́то",
            "вода́",
            "день"
          ],
          "answer": "день",
          "explanation": "День має один склад; інші слова мають два."
        },
        {
          "words": [
            "молоко́",
            "ву́лиця",
            "столи́ця",
            "Ки́їв"
          ],
          "answer": "Ки́їв",
          "explanation": "Ки́їв має два склади; інші слова мають три."
        },
        {
          "words": [
            "день",
            "Львів",
            "ма́ма",
            "так"
          ],
          "answer": "ма́ма",
          "explanation": "Ма́ма має два склади; інші слова мають один."
        },
        {
          "words": [
            "бібліоте́ка",
            "університе́т",
            "фотогра́фія",
            "ка́ша"
          ],
          "answer": "ка́ша",
          "explanation": "Ка́ша має два склади; інші слова мають п'ять."
        }
      ]
    },
    {
      "id": "act-w-count",
      "type": "count-syllables",
      "title": "Підрахунок складів у нових словах",
      "instruction": "Порахуй кількість складів у кожному слові.",
      "maxCount": 5,
      "items": [
        {
          "word": "та́то",
          "correct": 2
        },
        {
          "word": "вода́",
          "correct": 2
        },
        {
          "word": "ка́ша",
          "correct": 2
        },
        {
          "word": "люди́на",
          "correct": 3
        },
        {
          "word": "столи́ця",
          "correct": 3
        },
        {
          "word": "університе́т",
          "correct": 5
        }
      ]
    },
    {
      "id": "act-w-divide",
      "type": "divide-words",
      "title": "Розподіл слів на склади",
      "instruction": "Запиши слова, розділяючи склади пробілом.",
      "items": [
        {
          "word": "вода́",
          "answer": "во да"
        },
        {
          "word": "та́то",
          "answer": "та то"
        },
        {
          "word": "ка́ша",
          "answer": "ка ша"
        },
        {
          "word": "рука́",
          "answer": "ру ка"
        },
        {
          "word": "я́блуко",
          "answer": "яб лу ко"
        },
        {
          "word": "Полта́ва",
          "answer": "Пол та ва"
        }
      ]
    },
    {
      "id": "act-w-tf",
      "type": "true-false",
      "title": "Правила українського читання",
      "instruction": "Визнач, чи твердження є правильним.",
      "items": [
        {
          "statement": "У слові стільки складів, скільки в ньому голосних звуків.",
          "correct": true,
          "explanation": "Це головне правило складоподілу в українській мові."
        },
        {
          "statement": "Приголосний звук без голосного може утворити склад.",
          "correct": false,
          "explanation": "Склад утворюється лише навколо голосного звука."
        },
        {
          "statement": "Літера Ї завжди позначає два звуки [йі].",
          "correct": true,
          "explanation": "Літера Ї ніколи не пом'якшує приголосні й завжди дає [йі]."
        },
        {
          "statement": "В українській мові ненаголошений звук [о] читається як [а].",
          "correct": false,
          "explanation": "В українській мові [о] завжди звучить чітко як [о], наприклад, у слові молоко."
        },
        {
          "statement": "У слові «день» один склад.",
          "correct": true,
          "explanation": "У слові «день» один голосний звук [е], тому один склад."
        },
        {
          "statement": "У слові «яблуко» перший звук — це лише один звук [а].",
          "correct": false,
          "explanation": "На початку слова літера Я позначає два звуки: [й] та [а]."
        }
      ]
    },
    {
      "id": "act-w-match",
      "type": "match-up",
      "title": "Складові пари",
      "instruction": "З'єднай початок слова з його закінченням.",
      "pairs": [
        {
          "left": "мо-ло-",
          "right": "ко"
        },
        {
          "left": "ву-ли-",
          "right": "ця"
        },
        {
          "left": "сто-ли-",
          "right": "ця"
        },
        {
          "left": "лю-ди-",
          "right": "на"
        },
        {
          "left": "яб-лу-",
          "right": "ко"
        },
        {
          "left": "піс-",
          "right": "ня"
        }
      ]
    },
    {
      "id": "act-w-quiz",
      "type": "quiz",
      "title": "Перевірка читання слів",
      "instruction": "Обери правильний варіант відповіді.",
      "questions": [
        {
          "question": "Як правильно прочитати слово «молоко»?",
          "options": [
            {
              "text": "мо-ло-ко з чітким [о]",
              "correct": true
            },
            {
              "text": "ма-ла-ко через [а]",
              "correct": false
            },
            {
              "text": "м-л-к по літерах",
              "correct": false
            }
          ],
          "explanation": "Українське [о] завжди вимовляється чітко й виразно."
        },
        {
          "question": "Скільки складів у назві міста «Львів»?",
          "options": [
            {
              "text": "1 склад",
              "correct": true
            },
            {
              "text": "2 склади",
              "correct": false
            },
            {
              "text": "3 склади",
              "correct": false
            }
          ],
          "explanation": "У слові «Львів» лише один голосний звук [і], тому один склад."
        },
        {
          "question": "Скільки складів у назві міста «Київ»?",
          "options": [
            {
              "text": "2 склади",
              "correct": true
            },
            {
              "text": "1 склад",
              "correct": false
            },
            {
              "text": "3 склади",
              "correct": false
            }
          ],
          "explanation": "Голосні звуки [и] та [йі] утворюють два склади: Ки-їв."
        },
        {
          "question": "Яку роль виконує літера Я у слові «пісня»?",
          "options": [
            {
              "text": "пом'якшує попередній приголосний [н'] та позначає звук [а]",
              "correct": true
            },
            {
              "text": "позначає два звуки [йа]",
              "correct": false
            },
            {
              "text": "не позначає звука",
              "correct": false
            }
          ],
          "explanation": "Після приголосного літера Я позначає м'якість цього приголосного та звук [а]."
        },
        {
          "question": "Що означає слово «столиця»?",
          "options": [
            {
              "text": "capital city",
              "correct": true
            },
            {
              "text": "big street",
              "correct": false
            },
            {
              "text": "small village",
              "correct": false
            }
          ],
          "explanation": "Столиця — це головне місто держави (Київ — столиця України)."
        },
        {
          "question": "Як діти вчаться читати українські слова?",
          "options": [
            {
              "text": "по складах: склад за складом",
              "correct": true
            },
            {
              "text": "називаючи літери окремо",
              "correct": false
            },
            {
              "text": "вгадуючи з іншої мови",
              "correct": false
            }
          ],
          "explanation": "Підхід «знизу вгору»: звук -> склад -> слово."
        }
      ]
    }
  ]
}
```

```json file=vocabulary.yaml
[
  {
    "lemma": "склад",
    "translation": "syllable",
    "pos": "noun",
    "usage": "У сло́ві ма́ма два склади́."
  },
  {
    "lemma": "голосни́й звук",
    "translation": "vowel sound",
    "pos": "noun phrase",
    "usage": "А - голосни́й звук."
  },
  {
    "lemma": "при́голосний звук",
    "translation": "consonant sound",
    "pos": "noun phrase",
    "usage": "М - при́голосний звук."
  },
  {
    "lemma": "чита́ти",
    "translation": "to read",
    "pos": "verb",
    "usage": "Я чита́ю сло́во."
  },
  {
    "lemma": "писа́ти",
    "translation": "to write",
    "pos": "verb",
    "usage": "Я пишу́ лі́теру."
  },
  {
    "lemma": "ма́ма",
    "translation": "mother",
    "pos": "noun",
    "usage": "Ма́ма."
  },
  {
    "lemma": "та́то",
    "translation": "father",
    "pos": "noun",
    "usage": "Та́то."
  },
  {
    "lemma": "молоко́",
    "translation": "milk",
    "pos": "noun",
    "usage": "Молоко́."
  },
  {
    "lemma": "я́блуко",
    "translation": "apple",
    "pos": "noun",
    "usage": "Я́блуко."
  },
  {
    "lemma": "люди́на",
    "translation": "person",
    "pos": "noun",
    "usage": "Люди́на."
  },
  {
    "lemma": "ву́лиця",
    "translation": "street",
    "pos": "noun",
    "usage": "Ву́лиця."
  },
  {
    "lemma": "столи́ця",
    "translation": "capital",
    "pos": "noun",
    "usage": "Ки́їв - столи́ця Украї́ни."
  },
  {
    "lemma": "ка́ша",
    "translation": "porridge",
    "pos": "noun",
    "usage": "Ка́ша."
  },
  {
    "lemma": "пі́сня",
    "translation": "song",
    "pos": "noun",
    "usage": "Пі́сня."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Большакова, буквар 1 клас, p. 25",
    "role": "textbook",
    "source": "Большакова, буквар 1 клас, p. 25",
    "notes": "Plan reference: syllable rule; every syllable has a vowel sound."
  },
  {
    "title": "Большакова, буквар 1 клас, p. 29",
    "role": "textbook",
    "source": "Большакова, буквар 1 клас, p. 29",
    "notes": "Plan reference: sound analysis routine for Ukrainian words."
  },
  {
    "title": "Захарійчук 1 клас (НУШ 2025), p. 13-15",
    "role": "textbook",
    "source": "Захарійчук 1 клас (НУШ 2025), p. 13-15",
    "notes": "Plan reference: symbols for vowel, hard consonant, and soft consonant sounds."
  },
  {
    "title": "Кравцова, Українська мова 2 клас, p. 13",
    "role": "textbook",
    "source": "Кравцова, Українська мова 2 клас, p. 13",
    "notes": "Plan reference: hand-under-chin syllable counting check."
  },
  {
    "title": "Anna Ohoiko — Ukrainian alphabet overview",
    "role": "youtube",
    "url": "https://www.youtube.com/watch?v=ksXIXj7CXwc",
    "notes": "Supplemental listening support for the vowel reading pass."
  }
]
```