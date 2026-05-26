# Bio Image Rights Policy

**Phase 0 F7 deliverable for epic #2309.** Closes #2316.

Companion to `docs/audits/bio-track-gap-audit-2026-05-26.md` (SSOT).

## Why this exists

This policy is permanent. The non-commercial project posture (CLAUDE.md, project policy 2026-04-19) tolerates some CC-NC licenses, but **commercial-friendly licenses are still preferred** for portability and for not creating future migration debt if upstream consumers (textbooks, OERs) want to remix.

## Acceptable image sources, by preference

### Preferred (commercial-friendly)
1. **Wikimedia Commons** with license:
   - `PD-old-70` / `PD-old-100` (author died ≥70 / 100 years ago)
   - `PD-Ukraine` (Ukrainian-specific PD-old)
   - `PD-Soviet` (works first published in USSR before 1996 by anonymous/state authors)
   - `PD-RusEmpire` (Russian Empire era works)
   - `CC0 / CC-BY / CC-BY-SA` (any version)
2. **Ukrainian National Archives (ЦДАМЛМ, ЦДКФФА ім. Г. С. Пшеничного)** — most pre-1991 holdings are PD or government-WIPO; verify before use.
3. **Музей-меморіальні квартири / Літературно-меморіальні музеї** — many UA writers' museums have CC-licensed photograph collections; check museum website T&Cs.
4. **Інститут літератури ім. Т. Г. Шевченка НАН України** archival photographs.

### Tolerated (CC-NC and similar non-commercial)
Per project's non-commercial posture (CLAUDE.md). Examples:
- `CC-BY-NC` from Ukrainian state media
- `CC-BY-NC-SA` from Український інститут / PEN Ukraine
- Print-only-permitted historical periodicals (rare for our use case)

**Do not use CC-BY-ND** (no-derivatives) — too restrictive for educational adaptation.

### Forbidden
- All-rights-reserved photos from commercial agencies (Getty, AP, AFP) unless we have specific license
- Russian-state-archive photographs (RGAKFD, RGALI) — both copyright risk AND #M-2 source-tier policy violations
- Photos from Russian Wikipedia where license tag is unclear or contested
- AI-generated portraits (per Educational Standards, AI portrait of a real person is not acceptable for biographical use)

## Image-attribution YAML field schema

Every `plans/bio/{slug}.yaml` MUST include:

```yaml
portrait:
  url: "https://commons.wikimedia.org/wiki/File:..."
  license: "PD-old-70"          # OR: CC0, CC-BY-4.0, CC-BY-SA-4.0, CC-BY-NC-4.0, etc.
  attribution: "Wikimedia Commons / ${photographer} (${year})"
  caption_uk: "Павло Тичина, 1929"   # caption shown to UA-track learners
  caption_en: "Pavlo Tychyna, 1929"  # caption shown to EN-track learners
  verified_on: "2026-05-26"      # YYYY-MM-DD when license tag last verified
```

If no acceptable portrait exists, omit the `portrait:` field entirely (the wiki article should still ship — see "Fallback strategy" below).

## Per-block availability sampling (planned for Phase 4 startup)

A separate workstream during Phase 4 wiki-compile startup will sample ~10 figures across blocks A–K and verify image availability. Pre-Phase-4 expectations:

| Block | Expected image availability |
|---|---|
| A — Розстріляне Відродження | **High** — most have known portraits; NKVD case files often included mugshots that are now PD in UA (`PD-Soviet` for 1937 NKVD records, see Wikimedia precedent for Куліш/Зеров/Курбас). |
| B — Imperial 19th c. | **High** — pre-1900 photographs / lithographs are uniformly `PD-old-100`. |
| C — Émigré tradition | **Medium-high** — DP-camp and postwar US photos may still be in copyright; rely on Wikimedia + museum holdings. |
| D — Survived/censored | **High** — Soviet-era state portraits of laureates are widely-distributed PD. |
| E — Шістдесятники / UHG | **Medium** — many are recent enough to have rights questions; UHG archive + Memorial archive coverage variable. |
| F — War-killed post-2014 | **Medium-low** — modern figures, most photos taken by photojournalists with reserved rights. PEN Ukraine memorial pages sometimes have CC-BY-NC. Service photos often `PD-UA-government`. **Sensitive: families' rights to grief-related images must be respected.** |
| G — OUN/UPA/UNR | **High** — most are historical figures (1900s–1950s), photos PD or in Wikimedia. **Sensitive: politically-charged framing per F2 #2311 applies to caption text.** |
| H — Scholars / scientists | **Medium** — academic-portrait genre; some via НАН України Wikimedia uploads. |
| I — Visual artists / composers | **High** — these figures often have well-documented portrait holdings. |
| J — Religious martyrs | **High** — UGCC + UAOC archives have extensive PD portrait collections; Vatican beatification documents include canonical portraits. |
| K — Crimean Tatar | **Medium** — Mejlis archives, Voice of Crimea, RFE/RL Tatar service. |

## Fallback strategy when no acceptable image exists

If no PD/CC-licensed portrait can be found for a figure, **do not block the bio**. Options:

1. **Text-only bio** — ship without portrait, use the figure's signature (often PD via primary-source documents) or a hand-drawn silhouette in the wiki article header.
2. **Era-context image** — use an image of the place / era / event the figure is associated with (e.g. Sandarmokh memorial photograph for executed figures whose own portrait isn't available).
3. **Manuscript / book-cover image** — use a CC-licensed scan of the figure's published work cover as the visual anchor.
4. **Document-image fallback** — for war-killed figures whose family hasn't released photographs, use a scan of a published article they wrote, or a quote graphically rendered.

Document the fallback choice in the YAML:

```yaml
portrait_fallback:
  type: "era-context"  # OR: book-cover, document-image, signature, text-only
  url: "..."
  license: "..."
  caption_uk: "..."
  caption_en: "..."
  reason: "no PD/CC portrait located after T1-T3 search 2026-XX-XX"
```

## Privacy / family-sensitivity policy (post-2014 war-killed)

For Block F figures (post-2014 war-killed/captured) who have surviving family:

- **Use photo published by family or by figure during their lifetime.** Don't use a captured-soldier photo released by Russian propaganda channels.
- **Prefer PEN Ukraine memorial / Ukrainian Institute photos** when available — these are typically released with family consent.
- **For figures killed in Russian captivity** (Рощина, Левін, Асєєв-released): verify the photo is the one the family/employer chose to circulate, not a captivity image.
- **Do not use images that would re-victimize** (post-mortem, captivity restraints, etc.) — even when technically licensable.

## Russian-imperial / Soviet-era propaganda imagery

When a figure's most-available portrait is a Soviet-laureate official portrait (e.g. Тичина in his 1950s state-position robes), consider:

- **Preferred:** use a pre-capitulation portrait if one exists at PD quality. For Тичина, this would be 1918–1932 era photographs, not 1953–1959 Голова Верховної Ради portraits.
- **If only Soviet-era portraits are available:** caption explicitly notes the era ("Павло Тичина в 1959 році, на посаді голови Верховної Ради УРСР"). The portrait choice itself becomes part of the bio's pedagogy.
- **For OUN/UPA figures (Block G):** prefer photographs the figure themselves circulated (Provid OUN portraits, UPA-era underground portraits) over Soviet-secret-service photographs from interrogation files.

## Action items during Phase 4 startup (post-this-policy)

These are NOT blocking for Phase 1 research. They become live when wiki-compile work begins:

1. Spot-check 10 figures (1 per block) for image availability — surface gaps early
2. Establish a Wikimedia Commons sub-category `Category:Учасники проекту learn-ukrainian` or similar if upload of new PD images is needed
3. Set up an image-attribution unit test in the audit pipeline (every `plans/bio/*.yaml` either has `portrait:` with valid license tag OR `portrait_fallback:` with reason)

## Closes

#2316. The next image-related work is the 10-figure spot-check, planned for Phase 4 startup.
