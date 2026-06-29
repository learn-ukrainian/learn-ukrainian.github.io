# BIO #4005 Base Prep — `oleksandr-bilash` (pilot) — 2026-06-29

**Issue:** #4005 `[bio][03-base]` · **Prompt gate:** #4006 (PASS WITH WARNINGS) · **Pilot:** #4004 · **Readiness gate:** #2535
**Scope:** base artifacts for `oleksandr-bilash` ONLY — the cautious first slice of #4005, not the 10-slug batch.
**Verdict:** **PASS WITH WARNINGS** after AGY/Gemini adversarial review — dossier + plan + wiki packet authored; deterministic checks green; two metadata/source blockers fixed; residual source/image warnings below.

## What was written (base-prep order: dossier → plan → wiki packet)

- `docs/research/bio/oleksandr-bilash.md` — 10-section research dossier.
- `curriculum/l2-uk-en/plans/bio/oleksandr-bilash.yaml` — BIO C1 plan (`module: bio-346`, `sequence: 346`).
- `wiki/figures/oleksandr-bilash.md` + `wiki/figures/oleksandr-bilash.sources.yaml` — wiki packet.
- `docs/audits/bio-4005-bilash-base-2026-06-29.md` — this note.
- `docs/audits/bio-4005-bilash-agy-review-2026-06-29.md` — adversarial review record.
- `docs/audits/bio-2337-2336-bilash-gate-2026-06-29.md` — Bilash-only gate decision after fixes.

No module source, activities, vocabulary, MDX, or `curriculum.yaml` edits — per the #2535 no-module-writing gate.

## Source coverage

- **Tier 1:** ЕСУ (`article-39952`), ВУЕ, *Митці України* довідник (1992, cited).
- **Tier 2:** ЦДАМЛМ archive page; НСКУ.
- **Tier 3:** uk.wikipedia «Білаш Олександр Іванович» + «Два кольори».
- **Tier 5 (corroboration / primary-voice only):** Україна молода feature; wz.lviv.ua Pavlychko interview (`https://wz.lviv.ua/far-and-near/125474-dmytro-pavlychko-pisniu-dva-kolory-kdb-vvazhalo-himnom-oun`).

## AGY/Gemini review integration

- **Resolved:** plan `aliases` now contain clean indexable forms only (`Білаш Олександр Іванович`, `Олександр Білаш`, `Oleksandr Bilash`); forbidden Russian-imperial forms remain documented in the dossier, not indexed as aliases.
- **Resolved:** the Pavlychko interview reference in the plan now points to the exact `Високий Замок` article URL and no longer carries a `VERIFY точність цитат` placeholder.
- **Challenged as false positive:** AGY flagged `connects_to` values such as `bio-137-dmytro-pavlychko` as fabricated because they are not filenames. Existing BIO plans use BIO identifiers in this style, and `dmytro-pavlychko`, `taras-shevchenko`, `volodymyr-ivasyuk` are sequences 137, 39, and 149 in `curriculum.yaml`; keep the identifiers unless a dedicated navigation validator says otherwise.
- **Carried warning:** CSAMM returns `403` to automated fetches; treat as a link-check warning, not dead-source proof.
- ≥3 Tier 1/2 ✓ · ≥2 primary-voice quotes ✓ (via T5 feature — flagged VERIFY) · oppression mechanism documented as **co-optation/surveillance** (KGB «Два кольори» episode), not physical repression.

## Framing decisions

- **SOV flag honoured:** not a "Soviet success story." Soviet honours and Soviet-theme works (`Павло Корчагін`, `Прапороносці`, `Дзвони Росії`) are in the record alongside the national song-canon; anti-hagiography annotations carried into the plan outline.
- **No invented martyrdom:** no arrest/exile/imprisonment exists; the KGB "розмова" survives only as Pavlychko's recollection — stated as such.
- **HIST-alignment:** light — music/song-canon figure, not state-building/UNR/dissident/wartime; aligned only to Soviet cultural-policy / russification context.

## Unresolved VERIFY items (carry into #2337/#2336 and module build)

1. **«Любіть Україну» (Sosiura) as a Bilash song** — attributed only by T5 sheet-music/song sites; absent from ЕСУ/ВУЕ/uk.wikipedia work lists. Do NOT assert as a Bilash work until a T1/T2 source confirms. Dossier covers the Sosiura poem + the song-setting flag instead.
2. **Primary-quote exact wording** — the three §4 quotes come via the *Україна молода* feature (T5); verify verbatim against Bilash's published collections (*Мелодія* 1977, *Мамине крило* 1999) before the module quotes them.
3. **Portrait** — no PD/CC portrait of Bilash exists (d. 2003). Plan uses `portrait_fallback` (Градизьк monument); its licence AND Ukrainian freedom-of-panorama status are unverified (`license: VERIFY`). Fallback to text-only if unresolved.
4. **Conservatory year** — *Україна молода* renders "1967"; ЕСУ/uk.wikipedia give **1957** (cited). Treated as a media error, not a real disagreement.

## Validation run

- `yaml.safe_load` over all `curriculum/l2-uk-en/plans/bio/*.yaml` → parses (incl. new plan).
- `scripts/audit/lint_bio_dossier_xref.py --paths docs/research/bio/oleksandr-bilash.md` → "No fabricated Existing cross-track plan paths found." (exit 0).
- `markdownlint-cli2` on changed markdown → 0 errors.
- `git diff --check` → clean.
- All §7 "Existing" cross-track paths confirmed with `test -e`.

## Not done (out of scope / deliberately)

- No staging, commit, push, or PR.
- No other +77 slug touched; no `curriculum.yaml` edit.
- The remaining first-batch dossiers (Chubynskyi, Shashkevych, Konyskyi, Vovk, Hnatiuk, Kolessa, Doroshenko, Narbut, Murashko) are NOT started — this slice is Bilash only.
