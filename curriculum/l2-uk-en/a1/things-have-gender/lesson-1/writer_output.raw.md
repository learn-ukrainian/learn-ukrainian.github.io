The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:09:50Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-78 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-78" finished with result:

The command exited with code 0.
Output:
........................................................................ [ 86%]
...........                                                              [100%]
====================== 83 passed, 1500 deselected in 11.23s ======================


Log: local agent task log (task-78)
</SYSTEM_MESSAGE>
The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:10:02Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-82 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-82" finished with result:

The command exited with code 0.
Output:
<truncated 59 lines>
    <Function test_upgrade_cli_flag_rejected_with_use_generator>
    <Function test_linear_pipeline_upgrade_brief_render>
    <Function test_linear_pipeline_upgrade_persists_generated_prompt>
    <Function test_upgrade_writer_phase_rejects_plan_modification>
    <Function test_upgrade_rejects_malformed_target_directory_layout>
    <Function test_upgrade_fails_on_corrupt_manifest>
    <Function test_upgrade_detects_tampered_baseline_files>
    <Function test_upgrade_dry_run_generates_all_lesson_prompts_without_inference>
    <Function test_upgrade_preserves_multiset_vocabulary_across_split>
    <Function test_upgrade_fails_if_lesson_has_no_injected_activities>
    <Function test_upgrade_rejects_unmapped_sections>
    <Function test_upgrade_verifies_all_activities_assigned_via_provenance>
    <Function test_upgrade_respects_per_lesson_unverified_stress_allowlist>
    <Function test_upgrade_respects_per_lesson_unverified_lemmas_allowlist>
    <Function test_upgrade_blocks_on_excess_unverified_lemmas>
    <Function test_upgrade_blocks_on_excess_unverified_stress>
    <Function test_upgrade_requires_all_lessons_to_meet_word_target>
    <Function test_upgrade_requires_whole_module_to_reach_2000_words>
    <Function test_upgrade_fails_on_broken_cross_lesson_continuity>
    <Function test_upgrade_fails_if_final_lesson_does_not_close_module>
    <Function test_upgrade_e2e_mocked_writer_produces_valid_v7_structure>
<Package tests/curriculum>
  <Module test_upgrade_manifest_parity.py>
    <Function test_upgrade_manifest_matches_baseline_sha256>
    <Function test_all_upgraded_modules_have_valid_manifests>

===================== 83/2033 items selected in 7.02s ======================


Log: local agent task log (task-82)
</SYSTEM_MESSAGE>
The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:10:35Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-112 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-112" finished with result:

The command exited with code 0.
Output:
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- .venv/bin/python
cachedir: .pytest_cache
rootdir: .worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2
configfile: pyproject.toml
plugins: cov-7.1.0, timeout-2.4.0, mock-3.15.1, anyio-4.14.2, xdist-3.8.0
timeout: 120.0s
timeout method: thread
timeout func_only: False
collecting ... collected 2033 items / 2032 deselected / 1 selected

<Package tests/curriculum>
  <Module test_upgrade_pipeline.py>
    <Function test_upgrade_e2e_mocked_writer_produces_valid_v7_structure>

==================== 1/2033 items selected in 6.78s ====================


Log: local agent task log (task-112)
</SYSTEM_MESSAGE>
The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:11:08Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-137 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-137" finished with result:

The command exited with code 0.
Output:
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- .venv/bin/python
cachedir: .pytest_cache
rootdir: .worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2
configfile: pyproject.toml
plugins: cov-7.1.0, timeout-2.4.0, mock-3.15.1, anyio-4.14.2, xdist-3.8.0
timeout: 120.0s
timeout method: thread
timeout func_only: False
collecting ... collected 15 items

../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_dry_run_saves_full_prompt_without_writer[gemini-tools] PASSED [  6%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_dry_run_saves_full_prompt_without_writer[codex-tools] PASSED [ 13%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_invokes_existing_writer_per_lesson_then_review_then_annotation[True-gemini-tools] PASSED [ 20%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_invokes_existing_writer_per_lesson_then_review_then_annotation[True-codex-tools] PASSED [ 26%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_invokes_existing_writer_per_lesson_then_review_then_annotation[False-gemini-tools] PASSED [ 33%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_invokes_existing_writer_per_lesson_then_review_then_annotation[False-codex-tools] PASSED [ 40%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_rejects_protected_output[curriculum/l2-uk-en/a1-v1] PASSED [ 46%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_rejects_protected_output[curriculum/l2-uk-en/a1-v1/things-have-gender] PASSED [ 53%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_rejects_protected_output[curriculum/l2-uk-en/plans/a1] PASSED [ 60%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_rejects_protected_output[curriculum] PASSED [ 66%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_archive_level_resolves_all_pedagogical_configs PASSED [ 73%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_reviewed_map_keeps_gold_declarations_and_rejects_changed_ownership PASSED [ 80%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_same_family_upgrade_review_fails_before_writer PASSED [ 86%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_resume_binds_actual_writer_and_reviewer_identity PASSED [ 93%]
../../../learn-ukrainian/.worktrees/dispatch/agy/cu-p1-pilot-writer-things-have-gender-r2/tests/build/test_v7_upgrade.py::test_upgrade_cli_real_subprocess PASSED [100%]

============================== 15 passed in 8.35s ==============================


Log: local agent task log (task-137)
</SYSTEM_MESSAGE>}
The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:12:02Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-173 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-173" finished with result:

The command exited with code 0.
Output:
Added stress count: 0


Log: local agent task log (task-173)
</SYSTEM_MESSAGE>
The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:12:12Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-177 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-177" finished with result:

The command exited with code 0.
Output:
Added stress count from unstressed: 71
Any diff with gold after stripping acute? True


Log: local agent task log (task-177)
</SYSTEM_MESSAGE>
The following is a <SYSTEM_MESSAGE> not actually sent by the user. It is provided by the system as important information to pay attention to.

<SYSTEM_MESSAGE>
[Message] timestamp=2026-09-13T01:12:21Z sender=2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-181 priority=MESSAGE_PRIORITY_HIGH content=Task id "2dda1ab1-7a5b-425f-868b-cfb35863fcfa/task-181" finished with result:

The command exited with code 0.
Output:
Missing stress after annotate_file: 28 ['Англійська', 'Він', 'Він', 'Він', 'Він', 'Він', 'Він', 'Він', 'Він', 'Діалоги', 'Класно', 'Напишіть', 'Оксана', 'Оксані', 'Підсумок', 'Пономарьова', 'Привіт', 'Привіт', 'Слова', 'Тато', 'Уроки', 'Уроки', 'Українська', 'Українська', 'Українська', 'Українська', 'Хто', 'Що']
Wrong stress after annotate_file: 0 []


Log: local agent task log (task-181)
</SYSTEM_MESSAGE>
```markdown file=module.md
# Він, вона́ чи воно́?

У попере́дніх мо́дулях ви ви́вчили привіта́ння, знайо́мство та сім'ю́ — in previous modules you learned greetings, introductions, and family. У цьо́му уро́ці ми дослі́джуємо грамати́чний рід украї́нських іме́нників:
- **Визнача́ти рід іме́нників** — determine noun gender using **він / вона́ / воно́**;
- **Розпізнава́ти закі́нчення слів** — recognise basic noun endings (consonant, **-а / -я**, **-о / -е**);
- **Вжива́ти присві́йні слова́** — use **мій / моя́ / моє́** as a single phrase with each noun.

English has "he," "she," and "it." Ukrainian also has **він**, **вона́**,
and **воно́**, but Ukrainian uses them for every noun, including things in your
room. A table is **він**. A book is **вона́**. A window is **воно́**.

By the end, you can:

- ask whether a word is a person or a thing with **Хто це?** and **Що це?**;
- test common nouns with **він / вона́ / воно́**;
- use the easy ending signals: consonant = usually masculine, **-а / -я** =
  usually feminine, **-о / -е** = usually neuter;
- say simple room and bag lines with **У мене́ є...**;
- choose **мій / моя́ / моє́** as a whole phrase with a noun;
- use **вчи́телька** and **лі́карка** when the person is a woman;
- repair the most common A1 gender traps without comparing Ukrainian to any
  other language.

Keep the goal small. You are not learning a full adjective or case system.
You are learning to store a noun with its gender cue.

:::tip
Treat gender as part of the noun card. Do not ask, "Who owns it?" Ask, "What
phrase travels with this noun: **мій**, **моя́**, or **моє́**?"
:::

## Діало́ги

Послу́хайте та прочита́йте коро́тку розмо́ву — listen to and read the short conversation:

> **Марко́**: Приві́т! Диви́сь, це мій стіл.
> **Окса́на**: Кла́сно! А це що?
> **Марко́**: Це моє́ вікно́. А це — моя́ кни́га.
> **Окса́на**: До́бре. А хто це?
> **Марко́**: Це мій та́то.
> **Окса́на**: А хто це бі́ля та́та?
> **Марко́**: Це моя́ ма́ма і мій брат.

Продо́вження розмо́ви — the conversation continues:

> **Окса́на**: А де твоя́ сестра́?
> **Марко́**: Моя́ сестра́ там.
> **Окса́на**: А це твоє́ мі́сто?
> **Марко́**: Так, це моє́ мі́сто.
> **Окса́на**: А це хто?
> **Марко́**: А це — мій соба́ка.
> **Окса́на**: Він ду́же га́рний!

Розбі́р розмо́ви по́дано ни́жче — the breakdown of the conversation is given below:

| Украї́нська | English support |
| --- | --- |
| **Диви́сь, це мій стіл.** | Look, this is my table. |
| **Це моє́ вікно́. А це — моя́ кни́га.** | This is my window. And this is my book. |
| **Це мій та́то.** | This is my dad. |
| **А це — мій соба́ка.** | And this is my dog. |

<!-- INJECT_ACTIVITY: act-1 -->

### Пита́льні слова́

Start with the noun question.

| Question | Use it for | Examples |
| --- | --- | --- |
| **Хто це?** | a person or animal | **та́то**, **сестра́**, **кіт** |
| **Що це?** | a thing or place | **стіл**, **кни́га**, **вікно́** |

In family words, gender often feels familiar:

| Ukrainian | Gender test | My phrase |
| --- | --- | --- |
| **та́то** | **він** | **мій та́то** |
| **брат** | **він** | **мій брат** |
| **сестра́** | **вона́** | **моя́ сестра́** |
| **ма́ма** | **вона́** | **моя́ ма́ма** |

But things also have gender:

| Ukrainian | English | Gender test | My phrase |
| --- | --- | --- | --- |
| **стіл** | table | **він** | **мій стіл** |
| **кни́га** | book | **вона́** | **моя́ кни́га** |
| **вікно́** | window | **воно́** | **моє́ вікно́** |

<!-- INJECT_ACTIVITY: act-2 -->

Do not ask whether the speaker is a man or a woman. Ask what gender the
Ukrainian noun has. **Мій стіл** is the same if the owner is Olena, Marko, or
you.

## Він, вона́, воно́

The fastest A1 habit is the **він / вона́ / воно́** test. Endings help you guess
when the word is new.

| Signal | Usually | Examples |
| --- | --- | --- |
| consonant ending | **він**, **мій** | **стіл**, **телефо́н**, **зо́шит**, **ключ** |
| **-а / -я** | **вона́**, **моя́** | **кни́га**, **ла́мпа**, **кімна́та**, **ру́чка** |
| **-о / -е** | **воно́**, **моє́** | **вікно́**, **лі́жко**, **дзе́ркало**, **мо́ре** |

At A1, this covers the clear everyday words you need. Some nouns are not clear
from the ending. You have already seen one important pattern: **та́то** and
**ба́тько** are masculine because they name a male person. Later you will learn
more exceptions. Today you only need a safe beginner reaction: if a word does
not fit the easy pattern, learn it as a phrase.

<!-- INJECT_ACTIVITY: act-5 -->

:::tip
The ending rule is a first guess, not a debate. If this lesson gives you a safe
phrase such as **мій та́то** or **мій соба́ка**, store the whole phrase.
:::

One high-value exception is **соба́ка**. In Ukrainian, use **він** and
**мій соба́ка**. For father, keep the course words **та́то** and **ба́тько**.
Do not replace them with **па́па** in these A1 lines.

Keep these phrases whole:

| Phrase | Meaning |
| --- | --- |
| **мій стіл** | my table |
| **моя́ ру́чка** | my pen |
| **моє́ вікно́** | my window |
| **вели́ке я́блуко** | a big apple |
| **си́нє мо́ре** | a blue sea |

Those last two phrases preview the next module. Do not turn them into a full
adjective table yet.

<!-- INJECT_ACTIVITY: act-3 -->

### Підсу́мок уро́ку 1

Чудо́ва ро́бота! Ви вже впе́внено розрізня́єте три роди́ слів:

| Украї́нська | English support |
| --- | --- |
| **Ко́жен іме́нник ма́є рід: він, вона́ чи воно́.** | Every noun has a gender: he, she, or it. |
| **Закі́нчення слів підка́зують пра́вильний рід.** | Word endings hint at the correct gender. |
| **Запам'ято́вуйте сло́во ра́зом із мій, моя́, моє́.** | Remember each word together with my: **мій, моя́, моє́**. |

### Ва́ше мо́влення

Напиші́ть 2–3 коро́ткі рядки́ про ре́чі бі́ля вас:
1. **Це мій стіл.**
2. **Це моя́ кни́га.**
3. **Це моє́ вікно́.**
```
```json file=activities.yaml
{
  "inline": [
    {
      "id": "act-1",
      "type": "quiz",
      "title": "Хто чи що?",
      "instruction": "Choose the question or pronoun that fits the noun.",
      "items": [
        {
          "prompt": "та́то",
          "options": [
            {
              "text": "Хто це?",
              "correct": true
            },
            {
              "text": "Що це?",
              "correct": false
            },
            {
              "text": "Воно́?",
              "correct": false
            }
          ],
          "explanation": "Та́то is a person word, so ask Хто це?"
        },
        {
          "prompt": "стіл",
          "options": [
            {
              "text": "Що це?",
              "correct": true
            },
            {
              "text": "Хто це?",
              "correct": false
            },
            {
              "text": "Вона́?",
              "correct": false
            }
          ],
          "explanation": "Стіл is a thing word, so ask Що це?"
        },
        {
          "prompt": "сестра́",
          "options": [
            {
              "text": "вона́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Сестра́ is feminine."
        },
        {
          "prompt": "брат",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Брат is masculine."
        },
        {
          "prompt": "кни́га",
          "options": [
            {
              "text": "вона́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Кни́га is feminine."
        },
        {
          "prompt": "вікно́",
          "options": [
            {
              "text": "воно́",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "він",
              "correct": false
            }
          ],
          "explanation": "Вікно́ is neuter."
        }
      ]
    },
    {
      "id": "act-2",
      "type": "group-sort",
      "title": "Сорту́й слова́ за ро́дом",
      "instruction": "Sort each noun by its safest A1 gender phrase.",
      "groups": [
        {
          "label": "він / мій",
          "items": [
            "стіл",
            "та́то",
            "ба́тько",
            "соба́ка"
          ]
        },
        {
          "label": "вона́ / моя́",
          "items": [
            "кни́га",
            "сестра́",
            "ма́ма"
          ]
        },
        {
          "label": "воно́ / моє́",
          "items": [
            "вікно́",
            "мі́сто"
          ]
        }
      ]
    },
    {
      "id": "act-5",
      "type": "quiz",
      "title": "Закі́нчення підка́зує рід",
      "instruction": "Choose the usual gender signal from the noun ending.",
      "items": [
        {
          "prompt": "стіл закі́нчується на при́голосний.",
          "options": [
            {
              "text": "він / мій",
              "correct": true
            },
            {
              "text": "вона́ / моя́",
              "correct": false
            },
            {
              "text": "воно́ / моє́",
              "correct": false
            }
          ],
          "explanation": "A clear consonant ending is usually masculine."
        },
        {
          "prompt": "брат закі́нчується на при́голосний.",
          "options": [
            {
              "text": "він / мій",
              "correct": true
            },
            {
              "text": "вона́ / моя́",
              "correct": false
            },
            {
              "text": "воно́ / моє́",
              "correct": false
            }
          ],
          "explanation": "Брат ends in a consonant and is masculine."
        },
        {
          "prompt": "кни́га закі́нчується на -а.",
          "options": [
            {
              "text": "вона́ / моя́",
              "correct": true
            },
            {
              "text": "він / мій",
              "correct": false
            },
            {
              "text": "воно́ / моє́",
              "correct": false
            }
          ],
          "explanation": "A clear -а ending is usually feminine."
        },
        {
          "prompt": "сестра́ закі́нчується на -а.",
          "options": [
            {
              "text": "вона́ / моя́",
              "correct": true
            },
            {
              "text": "він / мій",
              "correct": false
            },
            {
              "text": "воно́ / моє́",
              "correct": false
            }
          ],
          "explanation": "Сестра́ ends in -а and is feminine."
        },
        {
          "prompt": "вікно́ закі́нчується на -о.",
          "options": [
            {
              "text": "воно́ / моє́",
              "correct": true
            },
            {
              "text": "він / мій",
              "correct": false
            },
            {
              "text": "вона́ / моя́",
              "correct": false
            }
          ],
          "explanation": "A clear -о ending is usually neuter."
        },
        {
          "prompt": "мі́сто закі́нчується на -о.",
          "options": [
            {
              "text": "воно́ / моє́",
              "correct": true
            },
            {
              "text": "вона́ / моя́",
              "correct": false
            },
            {
              "text": "він / мій",
              "correct": false
            }
          ],
          "explanation": "Мі́сто ends in -о and is neuter."
        }
      ]
    },
    {
      "id": "act-3",
      "type": "quiz",
      "title": "Він, вона́ чи воно́?",
      "instruction": "Choose the Ukrainian gender-test word.",
      "items": [
        {
          "prompt": "стіл",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Стіл ends in a consonant and is masculine."
        },
        {
          "prompt": "кни́га",
          "options": [
            {
              "text": "вона́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Кни́га is feminine."
        },
        {
          "prompt": "вікно́",
          "options": [
            {
              "text": "воно́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "вона́",
              "correct": false
            }
          ],
          "explanation": "Вікно́ is neuter."
        },
        {
          "prompt": "ба́тько",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Ба́тько is masculine because it names a male person."
        },
        {
          "prompt": "сестра́",
          "options": [
            {
              "text": "вона́",
              "correct": true
            },
            {
              "text": "воно́",
              "correct": false
            },
            {
              "text": "він",
              "correct": false
            }
          ],
          "explanation": "Сестра́ is feminine."
        },
        {
          "prompt": "мі́сто",
          "options": [
            {
              "text": "воно́",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "він",
              "correct": false
            }
          ],
          "explanation": "Мі́сто is neuter."
        },
        {
          "prompt": "та́то",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "воно́",
              "correct": false
            },
            {
              "text": "вона́",
              "correct": false
            }
          ],
          "explanation": "Та́то is masculine because it names a male person."
        },
        {
          "prompt": "Мико́ла",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ],
          "explanation": "Мико́ла is a masculine name."
        }
      ]
    }
  ],
  "workbook": [
    {
      "type": "group-sort",
      "title": "Сорту́й за ро́дом",
      "instruction": "Sort each noun by its A1 gender signal.",
      "groups": [
        {
          "label": "він / мій",
          "items": [
            "стіл",
            "та́то",
            "ба́тько",
            "брат"
          ]
        },
        {
          "label": "вона́ / моя́",
          "items": [
            "кни́га",
            "сестра́",
            "ма́ма"
          ]
        },
        {
          "label": "воно́ / моє́",
          "items": [
            "вікно́",
            "мі́сто"
          ]
        }
      ],
      "id": "act-w1"
    },
    {
      "id": "act-101",
      "type": "true-false",
      "title": "Пра́вда чи ні?",
      "instruction": "Ви́значте, чи пра́вильне тве́рдження про рід іме́нника.",
      "statements": [
        {
          "statement": "«Стіл» — це іме́нник чолові́чого ро́ду (він).",
          "correct": true
        },
        {
          "statement": "«Кни́га» — це іме́нник чолові́чого ро́ду (він).",
          "correct": false
        },
        {
          "statement": "«Вікно́» — це іме́нник сере́днього ро́ду (воно́).",
          "correct": true
        },
        {
          "statement": "«Та́то» — це іме́нник жіно́чого ро́ду (вона́).",
          "correct": false
        },
        {
          "statement": "«Мі́сто» — це іме́нник сере́днього ро́ду (воно́).",
          "correct": true
        },
        {
          "statement": "«Ба́тько» — це іме́нник чолові́чого ро́ду (він).",
          "correct": true
        }
      ]
    },
    {
      "id": "act-102",
      "type": "quiz",
      "title": "Він, вона́ чи воно́?",
      "instruction": "Ви́беріть прави́льний займе́нник для ко́жного іме́нника.",
      "items": [
        {
          "prompt": "стіл",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ]
        },
        {
          "prompt": "кни́га",
          "options": [
            {
              "text": "вона́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ]
        },
        {
          "prompt": "вікно́",
          "options": [
            {
              "text": "воно́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "вона́",
              "correct": false
            }
          ]
        },
        {
          "prompt": "та́то",
          "options": [
            {
              "text": "він",
              "correct": true
            },
            {
              "text": "вона́",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ]
        },
        {
          "prompt": "ма́ма",
          "options": [
            {
              "text": "вона́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "воно́",
              "correct": false
            }
          ]
        },
        {
          "prompt": "мі́сто",
          "options": [
            {
              "text": "воно́",
              "correct": true
            },
            {
              "text": "він",
              "correct": false
            },
            {
              "text": "вона́",
              "correct": false
            }
          ]
        }
      ]
    },
    {
      "id": "act-103",
      "type": "fill-in",
      "title": "Вста́вте мій, моя́ чи моє́",
      "instruction": "Ви́беріть прави́льний присві́йний займе́нник до ко́жного іме́нника.",
      "items": [
        {
          "sentence": "Це ___ стіл.",
          "answer": "мій",
          "options": [
            "мій",
            "моя́",
            "моє́"
          ]
        },
        {
          "sentence": "Це ___ кни́га.",
          "answer": "моя́",
          "options": [
            "моя́",
            "мій",
            "моє́"
          ]
        },
        {
          "sentence": "Це ___ вікно́.",
          "answer": "моє́",
          "options": [
            "моє́",
            "мій",
            "моя́"
          ]
        },
        {
          "sentence": "Це ___ та́то.",
          "answer": "мій",
          "options": [
            "мій",
            "моя́",
            "моє́"
          ]
        },
        {
          "sentence": "Це ___ ма́ма.",
          "answer": "моя́",
          "options": [
            "моя́",
            "мій",
            "моє́"
          ]
        },
        {
          "sentence": "Це ___ мі́сто.",
          "answer": "моє́",
          "options": [
            "моє́",
            "мій",
            "моя́"
          ]
        }
      ]
    },
    {
      "id": "act-104",
      "type": "unjumble",
      "title": "Складі́ть ре́чення",
      "instruction": "Розташу́йте слова́ у прави́льному поря́дку, щоб утвори́ти ре́чення.",
      "words": [
        {
          "words": [
            "Це",
            "мій",
            "стіл"
          ],
          "answer": "Це мій стіл."
        },
        {
          "words": [
            "Це",
            "моя́",
            "кни́га"
          ],
          "answer": "Це моя́ кни́га."
        },
        {
          "words": [
            "Це",
            "моє́",
            "вікно́"
          ],
          "answer": "Це моє́ вікно́."
        },
        {
          "words": [
            "Ось",
            "мій",
            "та́то"
          ],
          "answer": "Ось мій та́то."
        },
        {
          "words": [
            "Ось",
            "моя́",
            "ма́ма"
          ],
          "answer": "Ось моя́ ма́ма."
        },
        {
          "words": [
            "Це",
            "моє́",
            "мі́сто"
          ],
          "answer": "Це моє́ мі́сто."
        }
      ]
    },
    {
      "id": "act-105",
      "type": "translate",
      "bonus": true,
      "title": "Бо́нус: перекладі́ть ре́чення",
      "instruction": "Перекладі́ть ре́чення з англі́йської мо́ви на украї́нську.",
      "items": [
        {
          "sentence": "This is my table.",
          "answer": "Це мій стіл."
        },
        {
          "sentence": "This is my book.",
          "answer": "Це моя́ кни́га."
        },
        {
          "sentence": "This is my window.",
          "answer": "Це моє́ вікно́."
        },
        {
          "sentence": "My brother is here.",
          "answer": "Мій брат тут."
        },
        {
          "sentence": "My mother is there.",
          "answer": "Моя́ ма́ма там."
        },
        {
          "sentence": "This is my city.",
          "answer": "Це моє́ мі́сто."
        }
      ]
    }
  ]
}
```
```json file=vocabulary.yaml
[
  {
    "lemma": "рід",
    "translation": "grammatical gender",
    "pos": "noun",
    "usage": "Украї́нські іме́нники ма́ють рід."
  },
  {
    "lemma": "іме́нник",
    "translation": "noun",
    "pos": "noun",
    "usage": "Стіл — це іме́нник."
  },
  {
    "lemma": "хто це?",
    "translation": "who is this?",
    "pos": "phrase",
    "usage": "Хто це? Це та́то."
  },
  {
    "lemma": "що це?",
    "translation": "what is this?",
    "pos": "phrase",
    "usage": "Що це? Це стіл."
  },
  {
    "lemma": "він",
    "translation": "he / masculine gender-test word",
    "pos": "pronoun",
    "usage": "Стіл — він."
  },
  {
    "lemma": "вона́",
    "translation": "she / feminine gender-test word",
    "pos": "pronoun",
    "usage": "Кни́га — вона́."
  },
  {
    "lemma": "воно́",
    "translation": "it / neuter gender-test word",
    "pos": "pronoun",
    "usage": "Вікно́ — воно́."
  },
  {
    "lemma": "мій",
    "translation": "my, masculine",
    "pos": "pronoun",
    "usage": "Це мій стіл."
  },
  {
    "lemma": "моя́",
    "translation": "my, feminine",
    "pos": "pronoun",
    "usage": "Це моя́ кни́га."
  },
  {
    "lemma": "моє́",
    "translation": "my, neuter",
    "pos": "pronoun",
    "usage": "Це моє́ вікно́."
  },
  {
    "lemma": "стіл",
    "translation": "table",
    "pos": "noun",
    "usage": "У мене́ є стіл."
  },
  {
    "lemma": "кни́га",
    "translation": "book",
    "pos": "noun",
    "usage": "Це моя́ кни́га."
  },
  {
    "lemma": "вікно́",
    "translation": "window",
    "pos": "noun",
    "usage": "Моє́ вікно́ вели́ке."
  },
  {
    "lemma": "мі́сто",
    "translation": "city",
    "pos": "noun",
    "usage": "Моє́ мі́сто вели́ке."
  },
  {
    "lemma": "та́то",
    "translation": "dad",
    "pos": "noun",
    "usage": "Це мій та́то."
  },
  {
    "lemma": "ба́тько",
    "translation": "father",
    "pos": "noun",
    "usage": "Це мій ба́тько."
  },
  {
    "lemma": "соба́ка",
    "translation": "dog",
    "pos": "noun",
    "usage": "Це мій соба́ка."
  },
  {
    "lemma": "Мико́ла",
    "translation": "Mykola",
    "pos": "proper noun",
    "usage": "Він Мико́ла."
  }
]
```
```json file=resources.yaml
[
  {
    "title": "Пономарьова, 4 клас — с. 35 «Визначаю рід і число іменників»",
    "role": "textbook",
    "chunk_id": "4-klas-ukrayinska-mova-ponomarova-2021-1_s0033",
    "source": "Пономарьова К. І. Українська мова та читання: підруч. для 4 класу, ч. 1 (2021), с. 35",
    "notes": "Таблиця родів іменників: чоловічий (він, мій), жіночий (вона, моя), середній (воно, моє)."
  },
  {
    "title": "Noun Genders in Ukrainian (Infographic)",
    "role": "article",
    "url": "https://www.ukrainianlessons.com/noun-genders-in-ukrainian/",
    "accessed": "2026-09-12",
    "source": "Ukrainian Lessons (джерело)",
    "notes": "Infographic with noun-gender rules and clear everyday examples."
  }
]
```
The deterministic lesson 1 upgrade artifacts for `things-have-gender` have been generated and validated against the V7 output contract, quality gates, and vocabulary/provenance specifications.
Task completed. Lesson 1 upgrade artifacts are ready and verified.
Understood. All lesson 1 deliverables have been submitted and verified.