## Linguistic Scan
1. Critical factual error in the first section: `Коли ми кажемо слово «немає», іменник після нього завжди змінює своє закінчення. Це правило працює для всіх слів.` This is false because indeclinable nouns do not change; the same module itself uses `немає метро`, and `метро` is indeclinable.
2. Critical factual error in the third section: `Якщо слово закінчується на голосний або м'який знак, ми додаємо «-їв».` This overgenerates wrong Genitive plural forms. Masculine nouns in `-ь` and `-о` often take other patterns, e.g. `учитель → учителів`, `день → днів`, `батько → батьків`, not blanket `-їв`.

## Exercise Check
Five `INJECT_ACTIVITY` markers are present, matching the five planned activities. They all come after the relevant teaching sections, and the types/foci map cleanly to the plan (`quiz`, `fill-in`, two `match-up`, `unjumble`). No inline DSL exercise blocks are present, so there is no answer logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three planned H2 sections are present and correctly ordered, but two planned items are missing from the prose: the quantity trigger `декілька` is absent, and the Zabолотний note on `немає vs не має` is not taught. Search checks on the provided text return `декілька` = 0 and `не має` = 0. |
| 2. Linguistic accuracy | 5/10 | Two statements teach wrong grammar: `Коли ми кажемо слово «немає», іменник після нього завжди змінює своє закінчення. Це правило працює для всіх слів.` and `Якщо слово закінчується на голосний або м'який знак, ми додаємо «-їв».` |
| 3. Pedagogical quality | 6/10 | The module has many examples and a clear section flow, but pedagogy is undermined by the two false generalizations above, which learners are likely to memorize as rules. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is well covered in context (`родовий відмінок`, `немає`, `багато`, `мало`, `кілька`, `скільки`, `закінчення`, `однина`, `множина` all appear), and recommended items such as `кількість`, `відсутність`, `гроші`, `час` also appear, but planned `декілька` is omitted. |
| 5. Exercise quality | 9/10 | Marker count matches the plan exactly, and placement is sensible: quiz after absence, fill-in after singular endings, and three quantity-related activities after the quantity section. No visible exercise logic errors can be checked because only markers are shown. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and generally substantive (`Let us practice...`, `Let us consolidate...`) without gamified fluff. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present, markdown is clean, and the pipeline word count is 2968, which is above the 2000 target. |
| 8. Cultural accuracy | 10/10 | No Russia-centric framing or cultural distortions appear; the module treats Ukrainian on its own terms. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues have named speakers and plausible situations (`new apartment`, `going to the cinema`), rather than robotic prompt-response exchanges. |

## Findings
[DIMENSION] [SEVERITY: critical]  
Location: First section — `Коли ми кажемо слово «немає», іменник після нього завжди змінює своє закінчення. Це правило працює для всіх слів.`  
Issue: This teaches a false rule. Indeclinable nouns do not change form after `немає`; the module itself later gives `немає метро`, where `метро` stays unchanged.  
Fix: Replace the absolute rule with a rule about declinable nouns, and explicitly contrast it with an indeclinable example such as `немає метро`.

[DIMENSION] [SEVERITY: critical]  
Location: Third section — `Якщо слово закінчується на голосний або м'який знак, ми додаємо «-їв». Наприклад, один трамвай стає багато трамваїв.`  
Issue: This is factually wrong as a general rule for Genitive plural. `-їв` is common for nouns in `-й`, but masculine nouns in `-ь` and `-о` often take other patterns (`учитель → учителів`, `день → днів`, `батько → батьків`).  
Fix: Narrow the rule to nouns in `-й` and add contrasting examples for `-ь` and `-о`.

[DIMENSION] [SEVERITY: major]  
Location: Third section — `Words such as **кілька** (a few, several) and **скільки** (how many, how much) trigger this change.`  
Issue: The plan explicitly includes `декілька` in the quantity set, but the prose never introduces it. Search check on the provided text: `декілька` = 0.  
Fix: Add `декілька` alongside `кілька` in the quantity-trigger sentence.

[DIMENSION] [SEVERITY: major]  
Location: First section, grammar box — `You will often hear Ukrainians use the short form **нема** instead of **немає** in everyday conversations. Both words mean exactly the same thing and both require the Genitive case.`  
Issue: The plan reference note explicitly calls out the key distinction `немає` vs `не має`, but the module never teaches it. Search checks on the provided text: `не має` = 0.  
Fix: Expand the grammar box to distinguish fused `немає/нема` from separate `не має` with personal forms of `мати`.

## Verdict: REVISE
The module cannot pass because it contains two critical grammar inaccuracies that would teach learners false rules, plus two clear plan-adherence misses (`декілька` and the `немає` vs `не має` distinction).

<fixes>
- find: |
    Родовий відмінок — це дуже важлива тема в українській граматиці. Коли ми кажемо слово «немає», іменник після нього завжди змінює своє закінчення. Це правило працює для всіх слів.
  replace: |
    Родовий відмінок — це дуже важлива тема в українській граматиці. Коли ми кажемо слово «немає», відмінюваний іменник після нього переходить у родовий відмінок. Але незмінювані слова не змінюють форми: ми кажемо «немає холодильника», але «немає метро».
- find: |
    :::info
    **Grammar box**
    You will often hear Ukrainians use the short form **нема** instead of **немає** in everyday conversations. Both words mean exactly the same thing and both require the Genitive case.
    :::
  replace: |
    :::info
    **Grammar box**
    You will often hear Ukrainians use the short form **нема** instead of **немає** in everyday conversations. Both words mean exactly the same thing and both require the Genitive case. Do not confuse **немає/нема** with **не має**: we write **немає/нема** together when it means “there is no / do not have,” but **не має** separately only with personal forms of the verb **мати**.
    :::
- find: |
    Words such as **кілька** (a few, several) and **скільки** (how many, how much) trigger this change.
  replace: |
    Words such as **кілька / декілька** (a few, several) and **скільки** (how many, how much) trigger this change.
- find: |
    Більшість іменників чоловічого роду отримують закінчення «-ів». Один брат — це називний відмінок, а кілька братів — це родовий відмінок. Якщо слово закінчується на голосний або м'який знак, ми додаємо «-їв». Наприклад, один трамвай стає багато трамваїв.
  replace: |
    Більшість іменників чоловічого роду отримують закінчення «-ів». Один брат — це називний відмінок, а кілька братів — це родовий відмінок. Іменники на «-й» часто мають закінчення «-їв»: наприклад, один трамвай стає багато трамваїв. Але слова на «-ь» і «-о» можуть мати інші форми: учитель → учителів, день → днів, батько → батьків.
</fixes>