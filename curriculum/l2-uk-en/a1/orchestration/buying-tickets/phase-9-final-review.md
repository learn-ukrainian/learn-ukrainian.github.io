Confirmed: "черга" is never taught in the lesson content, while "вікно" appears in Dialogue 2 (line 229). Now let me compile the full adversarial review.

---

## Phase 9 Final QA Review — buying-tickets (a1-39)

### Issues Found

**Issue 1: Activity uses untaught vocabulary "черга"**
File: `activities/buying-tickets.yaml`, line 11
The group-sort activity includes "черга" (queue) in the "На вокзалі" group, but this word appears zero times in the lesson content. Students have never seen it. Replace with "вікно" — the cashier window at the station, which IS in Dialogue 2 (line 229: "Ви бачите вікно?").

**Issue 2: IPA inconsistency — автостанція missing tie bar on affricate**
File: `buying-tickets.md`, line 35
`[ɐu̯tɔˈstɑnʦ⁽ʲ⁾ijɐ]` uses the precomposed ʦ ligature. Project standard requires explicit tie bars on affricates (t͡s). Other affricates in the same file use tie bars correctly (e.g., line 278 `[prɔʋ⁽ʲ⁾idˈnɪt͡sʲɐ]`).

**Issue 3: IPA — місце missing tie bar (x2)**
File: `buying-tickets.md`, lines 173 and 174
`[ˈm⁽ʲ⁾isʲtse]` — the "ц" (tse) portion of місце lacks a tie bar. Should be `[ˈm⁽ʲ⁾isʲt͡se]` for consistency with project standard.

**Issue 4: IPA — відправлення uses dialectal [u̯] for в**
File: `buying-tickets.md`, line 183
`[ʋ⁽ʲ⁾idˈprɑu̯lʲɐnʲːɐ]` — the [u̯] for the "в" in "прав-" is a dialectal/fast-speech realization. Standard transcription: [ʋ]. Should be `[ʋ⁽ʲ⁾idˈprɑʋlʲɐnʲːɐ]`.

**Issue 5: Pedagogical inconsistency — intro uses "у Львів" then teaches "до Львова"**
File: `buying-tickets.md`, line 19
"Ви хочете поїхати у Львів?" uses the в/у + accusative pattern. The module later explicitly teaches "до + Genitive" as THE pattern for A1 and warns against "в" for tickets (lines 97–101). An A1 beginner seeing "у Львів" in paragraph 2 then being told to use "до Львова" will be confused. Fix to match the taught pattern.

**Issue 6: Genitive pattern description is inaccurate for Вінниця**
File: `buying-tickets.md`, line 87
States "Cities ending in **-а** change to **-и**" but then lists Вінниця (ends in **-я**, changes to **-і**). The rule as stated doesn't match the example. Needs to cover both -а→-и and -я→-і.

**Issue 7: Green Team review false positive (NOT an error in content)**
The Green Team review claims line 316 has "Ви молодец!" (Russicism). The actual file reads "Ви молодець!" — correct Ukrainian with soft sign. The review was working from a stale version. No fix needed.

### Non-blocking Notes

- **LLM fingerprint** (line 13–17): The "Чому це важливо?" opener is formulaic but not severe. The content quickly pivots to practical material. Minor.
- **"Дякую велике!"** (line 258): Informal but attested colloquial Ukrainian. Not an error.
- **Plan mentions "електронний квиток (QR-код)"** but content and meta omit it. Plan-meta divergence, not a content error. The meta (build source) doesn't require it.
- **Price "450 гривень" for Kyiv–Lviv купе** in dialogue: reasonable for a textbook example regardless of current real-world prices.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/buying-tickets.md
---OLD---
Це важливий урок. Ви хочете купити квиток? Ви хочете поїхати у Львів? Це прекрасно. Ви маєте знати слова. Слухайте і читайте.
---NEW---
Це важливий урок. Ви хочете купити квиток? Ви хочете поїхати до Львова? Це прекрасно. Ви маєте знати слова. Слухайте і читайте.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/buying-tickets.md
---OLD---
a **маршрутка** might stop at a smaller local **автостанція** [ɐu̯tɔˈstɑnʦ⁽ʲ⁾ijɐ] or even just a designated stop on the street.
---NEW---
a **маршрутка** might stop at a smaller local **автостанція** [ɐu̯tɔˈstɑnt͡s⁽ʲ⁾ijɐ] or even just a designated stop on the street.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/buying-tickets.md
---OLD---
*   Cities ending in **-а** change to **-и**:
    *   Полтава → **до Полтави**
    *   Вінниця → **до Вінниці**
    *   Одеса → **до Одеси**
---NEW---
*   Cities ending in **-а** change to **-и**; cities ending in **-я** change to **-і**:
    *   Полтава → **до Полтави**
    *   Одеса → **до Одеси**
    *   Вінниця → **до Вінниці**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/buying-tickets.md
---OLD---
*   **Нижнє місце** [ˈnɪʒnʲɛ ˈm⁽ʲ⁾isʲtse] is the "lower seat/bunk". It is usually preferred because you can sit on it during the day and don't have to climb.
*   **Верхнє місце** [ˈʋɛrxnʲɛ ˈm⁽ʲ⁾isʲtse] is the "upper seat/bunk". It is often cheaper, but requires some agility to access.
---NEW---
*   **Нижнє місце** [ˈnɪʒnʲɛ ˈm⁽ʲ⁾isʲt͡se] is the "lower seat/bunk". It is usually preferred because you can sit on it during the day and don't have to climb.
*   **Верхнє місце** [ˈʋɛrxnʲɛ ˈm⁽ʲ⁾isʲt͡se] is the "upper seat/bunk". It is often cheaper, but requires some agility to access.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/buying-tickets.md
---OLD---
1.  **Відправлення** [ʋ⁽ʲ⁾idˈprɑu̯lʲɐnʲːɐ] — Departure.
---NEW---
1.  **Відправлення** [ʋ⁽ʲ⁾idˈprɑʋlʲɐnʲːɐ] — Departure.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/buying-tickets.yaml
---OLD---
        - 'черга'
---NEW---
        - 'вікно'
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Summary:** Solid A1 practical module with excellent cultural depth (підстаканник tradition, купе vs плацкарт), well-scaffolded grammar (до + Genitive as chunks), and 4 realistic dialogues. Six issues found — all fixable: one untaught vocabulary item in an activity ("черга"), three IPA tie-bar inconsistencies, one pedagogical contradiction in the intro ("у Львів" vs taught "до Львова"), and one inaccurate genitive rule description. The Green Team's "молодец" Russicism finding was a false positive — the actual file has correct "молодець". After the fixes above, the module is clean.