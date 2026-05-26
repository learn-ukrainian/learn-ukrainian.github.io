# Bio Naming Canonical Policy

This policy governs new `curriculum/l2-uk-en/plans/bio/*.yaml` filenames,
`slug:` values, and alias metadata for the bio expansion epic (#2309).

## Scope

Use this policy for:

- Bio plan filenames in `curriculum/l2-uk-en/plans/bio/`
- `slug:` values inside bio plan YAML
- `connects_to:` references that point to bio modules
- Wiki/article slugs derived from bio plan slugs
- Alias lists that help writers and reviewers catch bad spellings

Existing legacy bio slugs are not renamed in this issue. New slugs must follow
this policy even where older files use a legacy spelling such as `-skyy`.

## Canonical Slug Format

Bio slugs use:

```text
firstname-surname.yaml
```

Rules:

- Lowercase ASCII only.
- Separate name parts with plain hyphens.
- Do not use apostrophes, curly apostrophes, quotation marks, or diacritics.
- Preserve public hyphenated names as slug segments:
  `nalepynska-boichuk`, `karpenko-karyi`, `fedun-poltava`.
- Omit Ukrainian soft sign and apostrophe inside words:
  `Ольга` -> `olha`, `Валер'ян` -> `valerian`.
- For figures known by a stable pen name, use the canonical public name in the
  slug and put legal names in `aliases:`.

Examples:

```text
Тарас Шевченко -> taras-shevchenko.yaml
Микола Хвильовий -> mykola-khvylovyi.yaml
Олександр Олесь -> oleksandr-oles.yaml
Валер'ян Поліщук -> valerian-polishchuk.yaml
Софія Налепинська-Бойчук -> sofiia-nalepynska-boichuk.yaml
```

## Transliteration Standard

Use the Ukrainian national romanization table approved by Cabinet of Ministers
Resolution No. 55 of 2010, and the BGN/PCGN-compatible form derived from it.
Do not use Russian-via-French or other imperial legacy spellings.

Primary reference:
<https://zakon.rada.gov.ua/go/55-2010-%D0%BF>

Project-critical letter rules:

| Ukrainian | Slug rule | Examples |
| --- | --- | --- |
| `г` | `h` | `Богдан` -> `bohdan` |
| `ґ` | `g` | `Ґалаґан` -> `galagan` |
| `и` | `y` | `Медвин` -> `medvyn` |
| `і` | `i` | `Іван` -> `ivan` |
| `ї` | `yi` at word start, `i` elsewhere | `Їжакевич` -> `yizhakevych`; `Мар'їне` -> `marine` |
| `й` | `y` at word start, `i` elsewhere | `Йосип` -> `yosyp`; `Олексій` -> `oleksii`; `Хвильовий` -> `khvylovyi` |
| `є` | `ye` at word start, `ie` elsewhere | `Євген` -> `yevhen`; `Асєєв` -> `asieiev` |
| `ю` | `yu` at word start, `iu` elsewhere | `Юрій` -> `yurii`; `Сосюра` -> `sosiura` |
| `я` | `ya` at word start, `ia` elsewhere | `Ярослав` -> `yaroslav`; `Надія` -> `nadiia` |
| `х` | `kh` | `Харків` -> `kharkiv` |
| `ш` | `sh` | `Шевченко` -> `shevchenko` |
| `щ` | `shch` | `Щербаківський` -> `shcherbakivskyi` |
| `зг` | `zgh`, not `zh` | `Згурський` -> `zghurskyi` |
| `ь`, apostrophe | omit | `Липківський` -> `lypkivskyi`; `Валер'ян` -> `valerian` |

Use `shevchenko`, not `chevtchenko`; `khvylovyi`, not `khvylovyy` or
`khvyliovyi`; `kyiv`, not `kiev`; `kharkiv`, not `kharkov`.

## Disambiguation

Start with `firstname-surname`. Add a disambiguator only when a collision or
high-confusion case remains after the canonical public name is applied.

Preferred order:

1. Use the full canonical given name if the other slug uses a short form or pen
   name: `oleksandr-oles.yaml` vs existing `oles-honchar.yaml`.
2. Use a stable second given name, monastic name, patronymic, or public
   compound name when it is part of the figure's usual identity.
3. Use birth year when two figures would otherwise have the same slug:
   `mykola-kulish-1892.yaml`.
4. For siblings or close family pairs, first names are enough if they clearly
   distinguish the figures. If not, add `-brother`, `-sister`, a patronymic, or
   a birth year.

Do not use vague disambiguators such as `writer`, `poet`, `famous`, `old`, or
`new`.

## Aliases

Every new bio plan should include an `aliases:` field when any alternate name,
pen name, Russian-imperial spelling, occupation-era spelling, legal name, or
commonly confused name is known.

Aliases are evidence for reviewers. They are not permission to use forbidden
forms in learner-facing body text.

Example:

```yaml
slug: taras-shevchenko
title: "Тарас Шевченко: ..."
aliases:
  - "Тарас Шевченко (canonical UA)"
  - "Taras Shevchenko (canonical EN)"
  - "Tarass Chevtchenko (FR-via-RU, FORBIDDEN in body text)"
  - "Тарас Григорович Шевченко (patronymic form; use only when context requires it)"
```

For pen names:

```yaml
slug: yurii-klen
aliases:
  - "Юрій Клен (canonical pen name)"
  - "Освальд Бургардт (legal name)"
  - "Oswald Burghardt (alternate English spelling)"
```

For callsigns:

```yaml
slug: iryna-tsybukh
aliases:
  - "Ірина Цибух (canonical UA)"
  - "Iryna Tsybukh (canonical EN)"
  - "Чека (callsign; allowed in context, not primary slug)"
```

## Forbidden Naming Patterns

Forbidden as primary slugs and forbidden in learner-facing body text unless the
text is explicitly discussing the bad spelling as an error:

- Russian-imperial or Russian-via-French transliterations:
  `Chevtchenko`, `Tarass Chevtchenko`, `Khmielnitski`, `Kharkov`,
  `Kiev`, `Lvov`, `Tchernigov`.
- Russianized first names when a Ukrainian form is canonical:
  `Sergey` for `Serhii`, `Nikolai` for `Mykola`, `Mikhail` for
  `Mykhailo`, `Vladimir` for `Volodymyr`.
- Russian patronymic forms copied from Russian-language sources when the
  Ukrainian form is not being explicitly analyzed.
- Suffixes from older local convention that conflict with the 2010 table for
  new files, especially `-skyy` where the canonical form is `-skyi`.

Historical quotations may preserve original spelling, but the surrounding
teacher voice must name the canonical Ukrainian form and flag the imperial form
as quoted or erroneous.

## Reviewer Checklist

- The filename and `slug:` match exactly.
- The slug is lowercase ASCII and hyphen-separated.
- Transliteration follows the 2010 table, including position-sensitive
  `ї`, `й`, `є`, `ю`, `я`.
- No exact slug collision exists in `curriculum/l2-uk-en/plans/bio/`.
- Family pairs, same-surname pairs, pen names, and callsigns are documented in
  `aliases:`.
- Russian-imperial spellings appear only in `aliases:` or explicit historical
  analysis, and are labelled as forbidden in body text where useful.
