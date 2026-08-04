# Paronym pair residual taxonomy (#6338)

Run date: 2026-08-04

Scope: `data/lexicon/paronym_pairs.yaml` against a locally hydrated
`data/atlas.db` (built from the `atlas-manifest` release, 17,387 approved
public articles) and a locally built VESUM shadow (`scripts/rag/build_vesum_shadow.py`,
brown-uk/dict_uk v6.8.0, ~7M forms — same source pinned by `scripts/config/vesum_source.lock.json`).
Reproduce with:

```
.venv/bin/python -m scripts.audit.paronym_residual_audit --vesum-db <db> --out <path>
```

## Before / after this change

| Metric | Before | After |
| --- | ---: | ---: |
| Pairs in `paronym_pairs.yaml` | 103 | 102 |
| Pairs with both legs in practice | 17 | 18 |
| Emitted `paronym` items | 34 | 36 |
| Residual pairs (≥1 leg missing) | 86 | 84 |

The 103→102 drop is a dedup, not a loss: `пам'ятка`/`пам'ятник` was authored
twice under two different apostrophe characters (curly `'` at the old line
323, straight `'` at line 1473 — only the straight form matches the Atlas
lemma spelling). The surviving entry keeps both citation sets.

## What actually blocked the 17→18 pairs that changed side

`пам'ятка`/`пам'ятник` is the one pair this change admits, and it was never a
missing-lexeme problem: both legs already had approved Atlas articles, CEFR
(A2/A1), and passed `is_practice_eligible`. The paronym emit loop resolved a
pair's `slugA`/`slugB` only through `slug_to_lex`/`lexemes_by_id`, which are
keyed by `lemmaId` — the hyphen-slugified `url_slug` (`пам'ятка` → `пам-ятка`).
`slugA`/`slugB` carry the lemma *spelling*, not the URL slug, so any
apostrophe-bearing pair could never resolve. `by_plain_lemma` (a
lemma-normalized map `_select_practice_lexemes` already returns and that the
homonym/synonym frame-selection code already consults) is the existing
fallback for exactly this; the paronym loop was the one relation-pair loop
not using it. Fixed in `scripts/audit/generate_practice_deck.py`.

Grepping all 102 pairs for non-plain-Cyrillic characters in `slugA`/`slugB`
found exactly 3 legs with apostrophes: `пам'ятка`, `пам'ятник` (now fixed),
and `об'єм` (pair 51 — genuinely absent from Atlas under any spelling, stays
residual). No other pair leg carries a character that could hit the same
lookup gap.

## Residual (84 pairs, 127 distinct blocked legs)

The two blocking reasons are mutually exclusive per leg but a pair can carry
one of each on its two legs:

| Blocking pattern | Pairs |
| --- | ---: |
| Only missing-from-Atlas leg(s) | 34 |
| Only ineligible (Atlas article exists, blocked below) leg(s) | 30 |
| Both | 20 |
| **Total residual** | **84** |

### 69 legs: no Atlas article at any spelling — out of scope (no invented lexemes)

These lemmas have no `article_payloads` row in `data/atlas.db` under any
apostrophe/casing variant checked. Admitting them would mean creating new
Atlas headwords, which is Atlas-intake work (#4387-adjacent), not a practice
admission — explicitly out of scope for this change ("do not invent
lexemes"):

`абрис, авторитарний, авторитетний, блискучий, будівельник, будівничий, взять,
виголошувати, вимисел, віла, віршований, геройський, героїчний, годувальниця,
годівниця, громадянський, гірницький, гірничий, дистанція, досвідчений,
дощовитий, змерзнути, знаменитий, знаменний, зумовлювати, контингент,
континент, корисливий, лепський, лікарський, музикальний, нервуватися,
об'єм, обумовлювати, орфей, пальне, передовий, писемність, письменність,
поверховий, постановка, присідати, проголошувати, програмний, програмований,
програмовий, прогресивний, пусто, путати, півтораста, регресивний,
свідоцтво, свідчення, сердешний, серцевий, сніговий, тактичний, тактовний,
туристичний, туристський, уповноваження, установка, хрещений, хутровий,
хутряний, чисельний, численний, іммігрант, інстанція`

### 58 legs: Atlas article exists but is `source_inventory_grow`, not yet CEFR-anchored

All 58 have an approved public Atlas article (`primary_source ==
"source_inventory_grow"`) but fail `is_practice_eligible` on
`practice_ineligibility_reason == "surface_not_admitted"` — and, checked
directly, every one of them *also* has no `course_usage` and no CEFR
(`missing_curriculum_anchor` would fire next even if the surface flag were
flipped). The only wired admission path for `source_inventory_grow` rows
(`--practice-seed` → `merge_practice_seed_entries`) requires the Atlas entry
to already carry a CEFR level and a source-backed example sentence with
provenance before it will flip `surface_admission.practice`; neither exists
here. Assigning a CEFR level is a curriculum decision (VESUM/PULS/course-fit
judgment), not a mechanical admission, so these stay in residual rather than
being force-admitted:

`абонент, адрес, багатир, барва, блудити, богатир, будівник, бювет, вдача,
виборний, виборчий, вислів, вклад, воєнний, відпуск, вілла, віршовий,
вітровий, гривна, густо, доля, домисел, дощовий, дружний, емігрант, ефектний,
задача, замерзнути, кампанія, кепський, корифей, кювет, лискучий, людний,
людяний, лічити, мимохідь, мимохіть, музичний, нотація, обрис, обсяг,
ожеледь, паливо, передній, плутати, поверхневий, привід, сопілка, спілка,
степінь, ступінь, талан, талант, трупа, удача, хресний, їда`

## Follow-up (not this change)

- CEFR-anchoring the 58 `source_inventory_grow` paronym legs (with a
  source-backed example per the existing `--practice-seed` contract) would be
  the highest-leverage next step — it alone gates ~30 pairs.
- The remaining 69 lemmas need Atlas intake before they can be practice
  candidates at all.
- Antonym/homonym pairs share the same `slug_to_lex`/`lexemes_by_id`-only
  resolution (`generate_practice_deck.py`, antonym ~4082, homonym ~4128) and
  likely have the same apostrophe-leg gap and a comparable
  Atlas/CEFR-anchoring residual. Out of scope here per #6338; noted for a
  follow-up ticket.
