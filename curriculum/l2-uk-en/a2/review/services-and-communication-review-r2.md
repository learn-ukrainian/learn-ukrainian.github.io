## Linguistic Scan
No linguistic errors found.

## Exercise Check
All 4 planned activity markers are present, and each one appears after the relevant teaching content:

- `fill-in-complete-post-office-dialogue-lines-with-correct-dative-forms` after the post-office dialogue section
- `group-sort-service-phrases` and `match-up-requests-responses` inside the service/dative section
- `quiz-dative-address-forms` after the address-writing section

The marker set matches the 4 `activity_hints` in the plan, and there are no inline DSL exercise blocks to audit here. Distribution is acceptable, though section 3 carries two markers while section 1 has none.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All 4 planned H2 sections are present, and the planned vocabulary appears in prose (`індекс`, `квитанція`, `одержувач`, `відправник`). However, none of the 3 plan references are cited anywhere in the module: `Заболотний` 0, `ULP` 0, `Кравцова` 0. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, or Russian-only letters found. Local verification confirms the suspicious forms used here are valid Ukrainian: `пакунок`, `бандероль`, `адрес`, `підказати`, `професорові`. |
| 3. Pedagogical quality | 8/10 | The module gives solid model phrases (`Допоможіть мені`, `Дякую листоноші`, `моєму дорогому братові Михайлові`), but one support gloss is not a translation of the Ukrainian paragraph it follows, which weakens learner trust in the bilingual scaffolding. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is used naturally across prose and dialogue (`пошта`, `лист`, `конверт`, `марка`, `посилка`, `адреса`, `надіслати`, `отримати`, `відправити`, `листоноша`), and the recommended set is also covered. |
| 5. Exercise quality | 9/10 | Marker count matches the plan exactly, IDs align with the planned activity types, and each marker comes after relevant teaching content. No visible logic errors can be assessed because the actual YAML exercises are not shown here. |
| 6. Engagement & tone | 9/10 | The tone is mostly teacherly and clear, with concrete postal situations and usable examples rather than gamified fluff. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, expected inject markers are intact, and the deterministic pipeline word count is 2881, safely above the 2000 target. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian as its own system, uses `Укрпошта` appropriately, and avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 7/10 | The dialogues use named speakers and multiple turns, but the first one is internally inconsistent: the customer asks for two envelopes, says `Я хочу надіслати листа`, then the clerk switches to `листи`, and the final instruction suddenly mentions `листівку`. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: module-wide; verified absence of `Заболотний`, `ULP`, and `Кравцова`  
Issue: The plan lists 3 references, but none of them are cited in the module prose.  
Fix: Integrate the references naturally into the relevant sections: add `ULP: At the Post Office` to the postal-vocabulary note, and add `Заболотний Grade 10, §157` plus `Кравцова Grade 4, §135` to the address/dative grammar note.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `> *On the envelope, there is always detailed information about the recipient. We write the person's name only in the Dative case...*`  
Issue: This English gloss does not translate the Ukrainian paragraph above it. The Ukrainian paragraph says “In this module, we practice the Dative case...” and explains addressee phrases; the gloss instead introduces different content.  
Fix: Replace the gloss with an accurate translation of the Ukrainian paragraph.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> — **Клієнт:** Добрий день! Дайте мені, будь ласка, два конверти і марки. Я хочу надіслати листа.` and `> — **Працівник пошти:** Двадцять п’ять гривень. Ви можете просто кинути листівку в поштову скриньку біля входу.`  
Issue: The first dialogue shifts between one letter, multiple letters, and a postcard, so the transactional logic feels stitched together instead of natural.  
Fix: Make the opening line plural (`два листи`) and replace `листівку` with `міжнародний лист` in the final clerk line.

## Verdict: REVISE
REVISE — there are fixable but real quality problems: missing plan-reference citations, one inaccurate bilingual gloss, and one internally inconsistent dialogue. These are targeted edits, not a full rebuild.

<fixes>
- find: |
    :::tip
    **Did you know?**
    In Ukrainian, **адреса** (address) is the physical location where you live or send mail. Be careful not to confuse it with the false friend *адрес*, which means a formal written greeting.
    :::
  replace: |
    :::tip
    **Did you know?**
    In Ukrainian, **адреса** (address) is the physical location where you live or send mail. Be careful not to confuse it with the false friend *адрес*, which means a formal written greeting. For more live postal-service phrases, compare **ULP: At the Post Office**.
    :::

- find: |
    > — **Клієнт:** Добрий день! Дайте мені, будь ласка, два конверти і марки. Я хочу надіслати листа. *(Good day! Please give me two envelopes and stamps. I want to send a letter.)*
  replace: |
    > — **Клієнт:** Добрий день! Дайте мені, будь ласка, два конверти і марки. Я хочу надіслати два листи. *(Good day! Please give me two envelopes and stamps. I want to send two letters.)*

- find: |
    > — **Працівник пошти:** Двадцять п’ять гривень. Ви можете просто кинути листівку в поштову скриньку біля входу. *(Twenty-five hryvnias. You can just drop the postcard in the postbox near the entrance.)*
  replace: |
    > — **Працівник пошти:** Двадцять п’ять гривень. Ви можете просто кинути міжнародний лист у поштову скриньку біля входу. *(Twenty-five hryvnias. You can just drop the international letter in the postbox near the entrance.)*

- find: |
    > *On the envelope, there is always detailed information about the recipient. We write the person's name only in the Dative case. For example, you are writing a long letter to dear friend Andriy. Or you want to send a warm gift to dear grandmother Olena. In official letters, we often write to respected professor Petrenko. When a person is to receive your letter, their name stands in the form of the Dative case.*
  replace: |
    > *In this module, we practice the Dative case in phrases that mark the addressee: **to whom?** You can write: "to dear friend Andriy", "to dear grandmother Olena", "to respected Professor Petrenko". In such phrases, the person's name and the words before it all stand in the Dative case. This clearly shows who the letter or gift is intended for.*

- find: |
    :::info
    **Grammar box** — When indicating the destination address on an envelope, always use **за адресою**. Avoid the incorrect phrase "по адресу", which is a direct calque from Russian. Correct Ukrainian requires the preposition **за** with the Instrumental case here.
    :::
  replace: |
    :::info
    **Grammar box** — When indicating the destination address on an envelope, always use **за адресою**. Avoid the incorrect phrase "по адресу", which is a direct calque from Russian. Correct Ukrainian requires the preposition **за** with the Instrumental case here. This matches the school-style treatment of formal address in **Заболотний Grade 10, §157**; the contrast between **на пошті** and forms like **листоноші** also aligns with **Кравцова Grade 4, §135**.
    :::
</fixes>