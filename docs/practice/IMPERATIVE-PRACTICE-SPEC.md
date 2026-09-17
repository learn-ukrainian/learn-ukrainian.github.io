# Imperative Mood (Наказовий спосіб) Practice Mode — Engineering & Linguistic Specification

Status: Canonical implementation specification for Issue #8156 under Epic #4387
Area: `atlas-practice` (Stream: `atlas-practice`)
Parent Issue: #8156 · Parent Epic: #4387
Authority: Frozen consensus of designated advisors Fable (`claude-fable-5-1`) and Astra/Sol (`gpt-6-astra`)

---

## 1. Executive Summary & Objective

This specification defines the end-to-end design, data generation, linguistic contracts, user experience, and delivery plan for the **Imperative Mood (`наказовий спосіб`) Practice Mode** in the Word Atlas Practice Hub.

### The Problem
Practice Hub currently provides 12 drill modes, but **verb moods and conjugations are completely unrepresented**. The existing `paradigm` mode is strictly typed and built for nominal/pronominal case $\times$ number declensions. Imperatives are one of the most critical communicative structures in Ukrainian and one of the highest-frequency error zones for L2 learners (and ZNO/NMT examinees), subject to heavy interference from Russian calques (*«давайте робити»* ❌) and incorrect suffix/stress choices.

### The Goal
Deliver a first-class **`imperative`** practice mode that:
1. Drills Ukrainian synthetic imperatives across 3 grammatical slots: **2nd person singular (2sg)**, **1st person plural inclusive (1pl)**, and **2nd person plural (2pl)**.
2. Implements a deterministic **multi-key acceptance gate** recognizing all valid VESUM literary variants (§116 Правопис 2019: *-імо / -ім*, *-ся / -сь*).
3. Employs an explainable **misconception-driven distractor engine** (distinguishing wrong person, wrong mood, orthographic interference, and calque avoidance).
4. Delivers an accessible, responsive web interface designed by Kimi, with Ukrainian-first pedagogical chrome.
5. Clears the standard **$\ge 1,000$ unique lemmas bar** across CEFR levels A1–C1.

---

## 2. Team Role Map & Work Division

Per operator directive:
- **Kimi (Web Designer)**: Frontend UI/UX, responsive mode tile, card layout, accessible keyboard navigation, misconception feedback displays, and chrome localization in `site/src/`.
- **Astra / Codex (`gpt-6-astra`)**: Backend generator engine, VESUM 3-slot extraction, deterministic distractor generation, and shard compilation in `scripts/audit/generate_practice_deck.py`.
- **Claude (`claude-sonnet-5` / `claude-fable-5-1`)**: Linguistic auditing, verification contracts, tests in `tests/test_generate_practice_deck.py`, schema validation in `check_static_practice_assets.py`, and independent held-out review.
- **Gemini / AGY (Accountable Orchestrator)**: Architecture governance, ticket breakdown, PR coordination across worktrees, CI gate enforcement, cross-family review routing, squash merges, and merge closeout to `main`.

---

## 3. Linguistic Architecture & Morphological Rules

### A. The Three Synthetic Slots
Ukrainian synthetic imperatives exist only for:
1. **2nd person singular (`2sg` / `impr:s:2`)**: Addressing one person informally (*ти*).
2. **1st person plural inclusive cohortative (`1pl` / `impr:p:1`)**: Invitation to shared action (*ми разом*).
3. **2nd person plural polite / group (`2pl` / `impr:p:2`)**: Addressing multiple people or formal polite singular (*ви*).

*(Note: 3rd person analytic forms with `хай/нехай` + indicative are scheduled for contextual cloze in Phase 3).*

### B. Suffix Conditioning Rules
1. **The `-и` ending**:
   - Conditioned primarily by **end stress** on the imperative form (*роби́, скажи́, бери́, мовчи́, іди́, неси́, живи́*).
   - Also occurs after a stem ending in a consonant cluster with a sonorant (*прові́три, підкре́сли, заслі́пи*).
   - Occurs in *ви́-* prefixed perfectives of end-stressed verbs (*ви́неси, ви́бери, ви́пиши*).
2. **Zero ending / `-ь`, `-й`**:
   - Vowel stems receive `-й` (*чита́й, співа́й, стій, ший, пий*).
   - Dental stems with soft consonant receive soft sign `-ь` (*сядь, стань, злазь, трать*).
   - **Orthographic Invariant (No Soft Sign on Labials or Post-alveolars)**:
     - Labials (*б, п, в, м, ф*) never take `-ь`: *сип, постав, знайом, економ*.
     - Post-alveolars (*ж, ч, ш, щ*) never take `-ь` in literary standard: *ріж, вибач, маж, стережи, плач*.
     *(Generating an erroneous `-ь` on these stems forms a licensed orthographic distractor).*

### C. 1st Person Plural (Cohortative) & Anti-Calque Gate
- Literary standard:
  - **`-мо`**: attaches directly to stems ending in a vowel (*чита́ймо*), a soft sign (*ста́ньмо, ся́дьмо, бу́дьмо*), or a hard consonant/labial/post-alveolar without soft sign (*рі́жмо, си́пмо, ві́рмо, пла́чмо*).
  - **`-імо`**: attaches to stems that take stressed *-и́* in the 2sg (*робі́мо, пиші́мо, ході́мо, несі́мо*).
- Literary shorter variant: **`-ім`** (*ході́м, робі́м, несі́м*). Both `-імо` and `-ім` are recognized in Правопис 2019 (§116).
- **Anti-Calque Rule**: In Ukrainian, *«давайте + дієслово»* (*«давайте робити»*) and *«пішли»* (in the sense of "let's go") are severe Russian calques/surzhyk. Ukrainian requires synthetic *робімо* / *ходімо*, or *ходімо робити* / *нумо робити*.

### D. Aspectual Contrast in the Imperative
- **Недоконаний вид (Imperfective)**: used for general instructions, repeated or ongoing actions, or polite invitations without focus on completion (*«Чита́йте уважно»*, *«Заходьте, сідайте»*).
- **Доконаний вид (Perfective)**: used for single, bounded actions where reaching the result/goal is critical (*«Прочита́йте цей параграф до кінця»*, *«Сядьте ось тут»*).
- Drills contrast aspectual pairs (*роби́ / зроби́*, *пиши́ / напиши́*, *відчиня́й / відчини́*) with communicative cue contexts to reinforce normative aspect choice.

---

## 4. Distractor Taxonomy & Misconception Codes

Every multiple-choice distractor must originate from a verified distractor family with a clear internal misconception code. Random strings are strictly forbidden.

| Family Code | Description | Generation Method | Example (Target: *робі́мо*) | Feedback Explanation |
|---|---|---|---|---|
| `WRONG_PERSON` | Valid imperative of another slot | Same lemma, different imperative slot | *роби́* (2sg) or *робі́ть* (2pl) | «Це форма 2-ї особи однини/множини, а потрібна 1-ша особа множини.» |
| `WRONG_MOOD` | Present indicative form | Same lemma, present indicative form | *ро́бимо* (pres.1pl) | «Це форма дійсного способу (що ми робимо зараз), а не заклик до дії.» |
| `ORTHO_SOFT_SIGN` | Erroneous soft sign on hard consonant | Suffix `-ь` added to labial/post-alveolar | *поставь* ❌ (target: *постав*) | «Губні та шиплячі в кінці слів в українській мові тверді: м'який знак не пишеться.» |
| `STEM_CLUSTER` | Missing vocalic ending `-и` | Dropped `-и` in stems with sonorant clusters | *провітр* ❌ (target: *провітри*) | «Після збігу приголосних із сонорним обов'язково пишеться закінчення -и.» |
| `CALQUE_AUX` | Russian auxiliary calque (sentence level only) | *Давайте* + infinitive/indicative | *давайте робити* ❌ | «В українській мові заклик до спільної дії передається синтетичною формою: робімо!» |

---

## 5. Data Engine & Shard Schema

### A. Shard File Format
Stored at `site/public/lexicon/practice-imperative.{level}.json` for levels `A1`, `A2`, `B1`, `B2`, `C1`.

```json
{
  "schema": "atlas-practice-imperative",
  "schemaVersion": 1,
  "deckVersion": "atlas-practice-v1-c0c3f3242b5134b6",
  "level": "A2",
  "source": "vesum",
  "imperative": [
    {
      "id": "imp_robyty_1pl",
      "lemmaId": "робити",
      "srsKey": "робити::imperative::1pl",
      "lemma": "роби́ти",
      "lemmaPlain": "робити",
      "aspect": "imperf",
      "slot": "1pl",
      "slotLabelUa": "1-ша особа множини (заклик до дії)",
      "slotLabelEn": "1st person plural (let's...)",
      "target": "робі́мо",
      "targetPlain": "робімо",
      "acceptedAnswers": ["робі́мо", "робімо", "робі́м", "робім"],
      "options": [
        {"text": "робі́мо", "isCorrect": true, "code": "CORRECT"},
        {"text": "ро́бимо", "isCorrect": false, "code": "WRONG_MOOD", "explanationUk": "«ро́бимо» — це форма теперішнього часу дійсного способу (що ми робимо?), а не наказ чи заклик."},
        {"text": "робі́ть", "isCorrect": false, "code": "WRONG_PERSON", "explanationUk": "«робі́ть» — це форма 2-ї особи множини (ви робіть), а потрібна 1-ша особа множини (ми робімо)."},
        {"text": "роби́", "isCorrect": false, "code": "WRONG_PERSON", "explanationUk": "«роби́» — це форма 2-ї особи однини (ти роби), а потрібна 1-ша особа множини (ми робімо)."}
      ],
      "cueSentence": "Друзі, нумо працювати, ... все вчасно!",
      "cueSentenceEn": "Friends, let's work and do everything on time!",
      "cefr": "A2",
      "notes": "Наголос на закінченні: робі́мо."
    }
  ]
}
```

### B. Multi-Key Acceptance Gate
The client and verification engine must normalize responses (`stripStressMarks`, trim) and accept **any** surface present in `acceptedAnswers`. If the user types or selects `робім`, it is marked correct with an educational note: *«Форма "робім" є допустимим варіантом, але найуживанішою літературною нормою є "робімо".»*

---

## 6. Frontend & UI/UX Requirements (Kimi)

1. **Mode Chooser Tile**:
   - Add `imperative` to `PRACTICE_MODES` in [`site/src/lib/lexicon/srs.ts`](../../site/src/lib/lexicon/srs.ts).
   - Display tile title: **Наказовий спосіб** (`Imperative Mood`).
   - Short description on focus/hover: *«Тренування форм наказового способу: 2-га ос. однини, 1-ша та 2-га ос. множини»*.
2. **Interaction Stage**:
   - Prompt layout: Displays target verb lemma + target person/number slot.
   - Communicative cue sentence provided where applicable to anchor context.
   - 4-choice button options with 48px hit areas and numeric keyboard shortcuts (`1`, `2`, `3`, `4`).
   - Optional text input toggle for advanced recall (A2+).
3. **Feedback State**:
   - Never auto-advance without user confirmation.
   - Upon answer selection, freeze stage, reveal correct option in green, highlight selected distractor in red (if incorrect), and display the specific misconception explanation.
   - Pressing `Enter` advances to next card.

---

## 7. Quality Gates & Verification Standards

1. **Linguistic Verification**:
   - 100% of target forms must exist in `vesum.db` tagged with `impr:s:2`, `impr:p:1`, or `impr:p:2`.
   - Stress marks must come directly from the project stress oracle (`data/stress.db` or VESUM stress annotations); ambiguous stress items are excluded.
2. **Zero Distractor Collision**:
   - No option in `options` (distractors) may match any surface in `acceptedAnswers`.
3. **Scale Threshold**:
   - Generator must admit $\ge 1,000$ unique verb lemmas across all level shards (`practice/coverage_report.py`).
4. **Automated Audits**:
   - `scripts/audit/check_static_practice_assets.py` must hydrate and validate all `practice-imperative.*.json` shards.
   - Unit tests in `tests/test_generate_practice_deck.py` assert schema validity, multi-key handling, and distractor correctness.

---

## 8. Delivery Roadmap & Ticket Architecture

- **Umbrella Issue**: [#8156](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8156)
- **Sub-Issue 1 (#8157)**: `[4387][practice] Imperative Mode: SRS schema, types, and mode registration` (Owner: Claude / Gemini).
- **Sub-Issue 2 (#8158)**: `[4387][practice] Imperative Generator: VESUM 3-slot extraction, distractor engine & shard compilation` (Owner: Astra / Codex).
- **Sub-Issue 3 (#8159)**: `[4387][practice] Imperative UI: Kimi web design, responsive card interactions & feedback` (Owner: Kimi).
- **Sub-Issue 4 (#8160)**: `[4387][practice] Imperative Verification: Held-out linguistic tests, CI gates & release hydration` (Owner: Claude / Astra).
