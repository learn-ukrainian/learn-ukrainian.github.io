## Linguistic Scan
No Russianisms, Surzhyk, calques, or paronym errors found.

One factual phonetics error:
- In `Звуки і літери`, the sentence `There are no silent letters to trick you.` contradicts the same section’s earlier claim that `«ь» makes zero sound on its own.` That teaches an internally inconsistent rule.

## Exercise Check
6 markers are present, and their contracted type/order is intact: `quiz → match-up → fill-in → group-sort → letter-grid → watch-and-repeat`.

One placement issue:
- `<!-- INJECT_ACTIVITY: fill-in-greetings -->` appears before `## Привіт! (Hello!)`, so it tests greeting material before that section teaches it.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Contract beats are mostly covered, but section pacing drifts: `Приголосні звуки` counts 291 words and `Привіт!` counts 325 words from local count, both over the 275-word max. `fill-in-greetings` also appears before `## Привіт!`. |
| 2. Linguistic accuracy | 7/10 | No Russianisms/Surzhyk found, but `There are no silent letters to trick you.` conflicts with `«ь» makes zero sound on its own; it only changes the pronunciation of the consonant directly before it.` |
| 3. Pedagogical quality | 8/10 | Strong examples (`мА-мА`, `мО-лО-кО`, `П [п] + р [р] + и [и]...`), but `Remember that to state your name, you should never say **«Я звати»**...` spends scarce A1 space on meta-warning instead of practice. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is all present in prose: `звук`, `літера`, `голосний`, `приголосний`, `Привіт`, `Як справи`, `Добре`, `Чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 9/10 | All 6 markers exist and the type prefixes match the contract, but `<!-- INJECT_ACTIVITY: fill-in-greetings -->` is placed before the greeting section it should reinforce. |
| 6. Engagement & tone | 9/10 | The module is mostly concrete and teacherly, with textbook references and usable examples rather than empty hype. |
| 7. Structural integrity | 8/10 | All H2 sections are present and ordered, and total word count is above target, but formatting artifacts remain: `**'Звуки**'`, `**'Голосні**'`, `**'Приголосні**'`, `**'голосна** **літера'**`. |
| 8. Cultural accuracy | 10/10 | The classroom and peer-greeting scenarios are appropriate, and the module avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 7/10 | The teacher exchange is labeled, but the hallway dialogue falls back to anonymous em dashes: `— Привіт! Як тебе звати?` / `— Привіт! Мене звати Софія. А тебе?` / `— Мене звати Марко.` |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: `Звуки і літери` — `There are no silent letters to trick you.`  
Issue: This contradicts the same section’s earlier explanation that `«ь» makes zero sound on its own`. That is a factual phonetics error.  
Fix: Change the sentence to say Ukrainian spelling is highly phonetic, while explicitly preserving the exception that `ь` does not represent its own sound.

[1. Plan adherence] [SEVERITY: major]  
Location: `## Приголосні звуки (Consonant Sounds)`  
Issue: The section runs to 291 words, over the contract max of 275.  
Fix: Tighten the consonant tip box; keep the voicing check, but compress it.

[1. Plan adherence] [SEVERITY: major]  
Location: `## Привіт! (Hello!)` — especially `Remember that to state your name, you should never say **«Я звати»**...` through the gender explanation  
Issue: The section runs to 325 words, far over the 275-word max, and pacing suffers.  
Fix: Regenerate only this section to 225-275 words while preserving the required greeting chunks, gender contrast, and `Привіт` sound analysis.

[3. Pedagogical quality] [SEVERITY: major]  
Location: `Привіт! (Hello!)` — `Remember that to state your name, you should never say **«Я звати»**...`  
Issue: This spends beginner space on a meta warning instead of giving more modeled A1 dialogue practice.  
Fix: Remove that warning in the rewrite and replace it with direct modeled chunks using `Як тебе звати?` and `Мене звати...`.

[5. Exercise quality] [SEVERITY: major]  
Location: marker block after `Приголосні звуки` — `<!-- INJECT_ACTIVITY: fill-in-greetings -->`  
Issue: The greeting fill-in appears before the greeting section teaches that material.  
Fix: Move `fill-in-greetings` to after `## Привіт! (Hello!)`, immediately before `watch-and-repeat-videos`.

[7. Structural integrity] [SEVERITY: minor]  
Location: `The textbook emphasizes **'Звуки**'...`, `vowels are called **'Голосні**'...`, `**'Приголосні**'...`, `Can you say **'голосна** **літера'**?`  
Issue: Stray apostrophes from contract-term leakage create visible formatting artifacts.  
Fix: Remove the stray apostrophes and format the Ukrainian terms normally.

[9. Dialogue & conversation quality] [SEVERITY: major]  
Location: `Привіт! (Hello!)` — `— Привіт! Як тебе звати? ...` / `— Мене звати Марко.` / `— Рада тебе бачити!`  
Issue: The hallway dialogue uses anonymous em dashes instead of named speakers, so it reads like a worksheet stub rather than a scene.  
Fix: Rewrite the exchange with named speakers such as `Марко:` and `Софія:`.

## Verdict: REVISE
REVISE. The module is close on coverage, but it contains one critical phonetics contradiction plus major section-pacing, marker-placement, and dialogue-format problems.

<fixes>
- find: |-
    The textbook emphasizes **'Звуки**' (sounds) as physical vibrations produced by your mouth.
  replace: |-
    The textbook emphasizes **звуки** (sounds) as physical vibrations produced by your mouth.
- find: |-
    What you see on the page is what you hear. There are no silent letters to trick you. Once you learn the specific sounds, reading becomes a direct and reliable translation of symbols into speech.
  replace: |-
    What you see on the page is usually what you hear. Ukrainian spelling is highly phonetic, but the soft sign «**ь**» does not represent its own sound. Once you learn the specific sound-letter patterns, reading becomes a direct and reliable translation of symbols into speech.
- find: |-
    In Ukrainian, vowels are called **'Голосні**' (vowels).
  replace: |-
    In Ukrainian, vowels are called **голосні** (vowels).
- find: |-
    In contrast to vowels, **'Приголосні**' (consonants) are produced with a mix of voice and noise, or noise alone.
  replace: |-
    In contrast to vowels, **приголосні** (consonants) are produced with a mix of voice and noise, or noise alone.
- find: |-
    :::tip
    You can feel the mechanics of consonants using a kinaesthetic voicing check. Place your hand firmly on your throat. When you pronounce a voiced consonant like [д], you will feel a strong vibration. When you pronounce a voiceless consonant like [т], you will only feel air.
    :::
  replace: |-
    :::tip
    Put your hand on your throat: [д] vibrates, [т] does not.
    :::
- find: |-
    <!-- INJECT_ACTIVITY: match-up-letters-sounds -->
    <!-- INJECT_ACTIVITY: fill-in-greetings -->
    <!-- INJECT_ACTIVITY: group-sort-sounds -->
    <!-- INJECT_ACTIVITY: letter-grid-alphabet -->
  replace: |-
    <!-- INJECT_ACTIVITY: match-up-letters-sounds -->
    <!-- INJECT_ACTIVITY: group-sort-sounds -->
    <!-- INJECT_ACTIVITY: letter-grid-alphabet -->
- find: |-
    <!-- INJECT_ACTIVITY: watch-and-repeat-videos -->
  replace: |-
    <!-- INJECT_ACTIVITY: fill-in-greetings -->
    <!-- INJECT_ACTIVITY: watch-and-repeat-videos -->
- find: |-
    Can you say **'голосна** **літера'**?
  replace: |-
    Can you say **голосна літера**?
</fixes>

<rewrite-block section="Привіт! (Hello!)">
Rewrite only this section. Keep the exact H2 heading. Cut it to 225-275 words. Use named speakers for both dialogues (`Вчитель`/`Учні`, `Марко`/`Софія`). Keep the required greeting vocabulary and chunks: `Привіт!`, `Добрий день!`, `Як справи?`, `Добре`, `Чудово`, `Нормально`, `А у тебе?`, `Рада/Радий тебе бачити!`. Keep the `звуковий аналіз` of `Привіт` with two `голосні` and four `приголосні`. Remove the meta warning about `«Я звати»` and avoid anonymous em-dash dialogue.
</rewrite-block>